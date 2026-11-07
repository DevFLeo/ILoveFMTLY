"""Fase 2: ferramentas de imagem (core/images.py)."""

from pathlib import Path

import pytest
from PIL import Image, ImageSequence

from core import images
from core.images import ImageError

GPS_TAG, ORIENTATION, MAKE = 0x8825, 0x0112, 0x010F


@pytest.fixture
def foto(tmp_path) -> Path:
    """JPEG 40×20 (lado esquerdo vermelho) com câmera, GPS e orientação 6 (girar 90°)."""
    img = Image.new('RGB', (40, 20), 'blue')
    img.paste('red', (0, 0, 20, 20))
    exif = Image.Exif()
    exif[MAKE] = 'Câmera Teste'
    exif[ORIENTATION] = 6
    exif[GPS_TAG] = {1: 'S', 2: (3.0, 7.0, 10.0)}
    out = tmp_path / 'praia.jpg'
    img.save(out, exif=exif, quality=95)
    return out


@pytest.fixture
def quadrado(tmp_path) -> Path:
    img = Image.new('RGB', (40, 20), 'white')
    img.paste('red', (0, 0, 10, 10))       # canto superior esquerdo
    out = tmp_path / 'quadro.png'
    img.save(out)
    return out


@pytest.fixture
def gif(tmp_path) -> Path:
    cores = ['red', 'green', 'blue', 'yellow', 'white']
    frames = [Image.new('RGB', (60, 30), c) for c in cores]
    out = tmp_path / 'anim.gif'
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=200, loop=0)
    return out


def px(path, xy):
    with Image.open(path) as im:
        return im.convert('RGB').getpixel(xy)


def near(c, ref, tol=40):
    return all(abs(a - b) <= tol for a, b in zip(c, ref))


# --- girar / espelhar ----------------------------------------------------------
@pytest.mark.parametrize('acao, tamanho, canto_vermelho', [
    ('Girar 90° à direita', (20, 40), (15, 2)),
    ('Girar 90° à esquerda', (20, 40), (2, 37)),
    ('Girar 180°', (40, 20), (37, 17)),
    ('Espelhar na horizontal', (40, 20), (37, 2)),
    ('Espelhar na vertical', (40, 20), (2, 17)),
])
def test_girar_espelhar(quadrado, tmp_path, acao, tamanho, canto_vermelho):
    [out] = images.rotate([quadrado], tmp_path / 'saida', action=acao)
    with Image.open(out) as im:
        assert im.size == tamanho
    assert near(px(out, canto_vermelho), (255, 0, 0))


def test_girar_gif_mantem_animacao(gif, tmp_path):
    [out] = images.rotate([gif], tmp_path / 'saida', action='Girar 90° à direita')
    with Image.open(out) as im:
        assert im.n_frames == 5 and im.size == (30, 60)


# --- EXIF ----------------------------------------------------------------------
def test_remover_exif_tira_gps_e_camera(foto, tmp_path):
    [out] = images.strip_exif([foto], tmp_path / 'saida')
    assert out.name == 'praia_sem_exif.jpg'
    with Image.open(out) as im:
        exif = im.getexif()
        assert GPS_TAG not in exif and MAKE not in exif and ORIENTATION not in exif
        assert im.size == (20, 40)        # orientação aplicada antes de remover
    assert near(px(out, (10, 2)), (255, 0, 0))


def test_remover_exif_png_tira_textos(tmp_path):
    from PIL.PngImagePlugin import PngInfo
    meta = PngInfo()
    meta.add_text('Author', 'Maria Souza')
    src = tmp_path / 'tela.png'
    Image.new('RGB', (10, 10), 'white').save(src, pnginfo=meta)
    [out] = images.strip_exif([src], tmp_path / 'saida')
    with Image.open(out) as im:
        assert 'Author' not in im.info


def test_nao_toca_no_original(foto, tmp_path):
    antes = foto.read_bytes()
    images.strip_exif([foto], tmp_path / 'saida')
    assert foto.read_bytes() == antes


# --- marca d'água --------------------------------------------------------------
def test_marca_dagua_texto(tmp_path):
    src = tmp_path / 'branco.png'
    Image.new('RGB', (400, 200), 'white').save(src)
    [out] = images.watermark([src], tmp_path / 'saida', text='CONFIDENCIAL',
                             position='Centro', opacity=60, logo='')
    with Image.open(out) as im:
        assert im.size == (400, 200)
        centro = im.convert('RGB').crop((100, 60, 300, 140))
        assert min(c[0] for c in centro.getdata()) < 220   # há tinta no centro
        canto = im.convert('RGB').crop((0, 0, 30, 30))
        assert set(canto.getdata()) == {(255, 255, 255)}


def test_marca_dagua_logo_no_canto(tmp_path):
    src = tmp_path / 'branco.png'
    Image.new('RGB', (400, 200), 'white').save(src)
    logo = tmp_path / 'logo.png'
    Image.new('RGBA', (100, 100), (255, 0, 0, 255)).save(logo)
    [out] = images.watermark([src], tmp_path / 'saida', text='', position='Inferior direito',
                             opacity=100, logo=str(logo))
    assert near(px(out, (390, 190)), (255, 0, 0))
    assert px(out, (10, 10)) == (255, 255, 255)


def test_marca_dagua_sem_texto_nem_logo(tmp_path, quadrado):
    with pytest.raises(ImageError):
        images.watermark([quadrado], tmp_path, text='', position='Centro', opacity=50, logo='')


# --- recortar / borrar ---------------------------------------------------------
def test_recortar(quadrado, tmp_path):
    out = images.crop(quadrado, tmp_path / 'r.png', (0, 0, 10, 10))
    with Image.open(out) as im:
        assert im.size == (10, 10)
    assert near(px(out, (5, 5)), (255, 0, 0))


def test_recortar_fora_da_imagem(quadrado, tmp_path):
    with pytest.raises(ImageError):
        images.crop(quadrado, tmp_path / 'r.png', (30, 10, 30, 15))


def test_borrar_area_pixela_so_o_retangulo(tmp_path):
    img = Image.new('RGB', (100, 50), 'white')
    for x in range(0, 50, 2):
        for y in range(50):
            img.putpixel((x, y), (0, 0, 0))   # listras finas na metade esquerda
    src = tmp_path / 'listras.png'
    img.save(src)
    out = images.blur_area(src, tmp_path / 'b.png', (0, 0, 50, 50), block=10)
    with Image.open(out) as im:
        rgb = im.convert('RGB')
        bloco = {rgb.getpixel((x, 5)) for x in range(0, 10)}
        assert len(bloco) == 1                        # listras viraram um bloco só
        assert rgb.getpixel((80, 10)) == (255, 255, 255)


# --- editar GIF ----------------------------------------------------------------
def frames_and_durations(path):
    with Image.open(path) as im:
        return [(f.convert('RGB').getpixel((1, 1)), f.info.get('duration'))
                for f in ImageSequence.Iterator(im)]


def test_gif_velocidade_trecho_e_inverter(gif, tmp_path):
    [out] = images.edit_gif([gif], tmp_path / 'saida', speed=200, first=2, last=4, width=0,
                            reverse='Sim', fmt='GIF')
    fr = frames_and_durations(out)
    assert len(fr) == 3
    assert [near(c, ref) for (c, _), ref in zip(fr, [(255, 255, 0), (0, 0, 255), (0, 128, 0)])] \
        == [True, True, True]
    assert all(d == 100 for _, d in fr)


def test_gif_largura_e_webp(gif, tmp_path):
    [out] = images.edit_gif([gif], tmp_path / 'saida', speed=100, first=1, last=0, width=30,
                            reverse='Não', fmt='WebP')
    assert out.suffix == '.webp'
    with Image.open(out) as im:
        assert im.n_frames == 5 and im.size == (30, 15)


def test_gif_trecho_invalido(gif, tmp_path):
    with pytest.raises(ImageError, match='quadro'):
        images.edit_gif([gif], tmp_path, speed=100, first=9, last=0, width=0, reverse='Não',
                        fmt='GIF')
