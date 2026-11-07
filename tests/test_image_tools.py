import base64
import json

import pytest
from PIL import Image

from core import image_tools as it
from core.convert import convert_images
from core.images import ImageError


@pytest.fixture
def photo(tmp_path):
    p = tmp_path / 'foto.png'
    im = Image.new('RGB', (120, 80), (255, 255, 255))
    for x in range(40, 80):
        for y in range(20, 60):
            im.putpixel((x, y), (200, 30, 30))
    im.save(p)
    return p


def test_adjust_changes_pixels(photo, tmp_path):
    out = it.adjust([photo], tmp_path / 'o', brightness=50)[0]
    assert Image.open(out).getpixel((0, 0))[0] < 200


def test_adjust_rejects_out_of_range(photo, tmp_path):
    with pytest.raises(ImageError, match='Brilho'):
        it.adjust([photo], tmp_path / 'o', brightness=999)


@pytest.mark.parametrize('effect', it.EFFECTS)
def test_every_filter_runs(photo, tmp_path, effect):
    out = it.filter_images([photo], tmp_path / 'o', effect=effect)[0]
    assert Image.open(out).size == (120, 80)


def test_filter_bw_is_gray(photo, tmp_path):
    out = it.filter_images([photo], tmp_path / 'o', effect='Preto e branco')[0]
    r, g, b = Image.open(out).convert('RGB').getpixel((60, 40))
    assert r == g == b


def test_frame_rounds_corners_and_adds_border(photo, tmp_path):
    out = it.frame([photo], tmp_path / 'o', radius=20, border=10, color='Preto')[0]
    im = Image.open(out)
    assert out.suffix == '.png' and im.size == (140, 100)
    assert im.getpixel((0, 0))[3] == 0            # canto transparente
    assert im.getpixel((70, 2))[:3] == (0, 0, 0)  # borda preta


def test_remove_background_keeps_subject(photo, tmp_path):
    out = it.remove_background([photo], tmp_path / 'o')[0]
    im = Image.open(out)
    assert im.getpixel((0, 0))[3] == 0 and im.getpixel((60, 40))[3] == 255


def test_compress_to_size_fits(tmp_path):
    big = tmp_path / 'big.png'
    Image.effect_noise((800, 600), 80).convert('RGB').save(big)
    out = it.compress_to_size([big], tmp_path / 'o', target_kb=30)[0]
    assert out.stat().st_size <= 30 * 1024


@pytest.mark.parametrize('layout', it.LAYOUTS)
def test_collage(photo, tmp_path, layout):
    other = tmp_path / 'b.png'
    Image.new('RGB', (60, 60), (0, 0, 255)).save(other)
    out = it.collage([photo, other, photo], tmp_path / 'c.png', layout=layout, gap=4)[0]
    w, h = Image.open(out).size
    assert w > 0 and h > 0
    if layout == 'Lado a lado':
        assert w > h


def test_palette(photo, tmp_path):
    png, txt = it.palette([photo], tmp_path / 'o', colors=2)
    hexes = txt.read_text().split()
    assert '#FFFFFF' in hexes and len(hexes) == 2 and png.exists()


def test_favicon_set(photo, tmp_path):
    made = {p.name for p in it.favicon([photo], tmp_path / 'fav')}
    assert {'favicon.ico', 'favicon-32x32.png', 'favicon-512x512.png', 'apple-touch-icon.png',
            'site.webmanifest', 'favicon.html'} <= made
    json.loads((tmp_path / 'fav' / 'site.webmanifest').read_text())


def test_base64_roundtrip(photo, tmp_path):
    txt = it.to_base64([photo], tmp_path / 'b')[0]
    assert txt.read_text().startswith('data:image/png;base64,')
    back = it.from_base64([txt], tmp_path / 'img')[0]
    assert back.suffix == '.png' and back.read_bytes() == photo.read_bytes()
    raw = tmp_path / 'raw.txt'
    raw.write_text(base64.b64encode(photo.read_bytes()).decode())
    assert it.from_base64([raw], tmp_path / 'img')[0].suffix == '.png'


def test_base64_not_image(tmp_path):
    t = tmp_path / 'x.txt'
    t.write_text(base64.b64encode(b'ola mundo').decode())
    with pytest.raises(ImageError, match='não contém uma imagem'):
        it.from_base64([t], tmp_path / 'o')


def test_info_report(photo, tmp_path):
    out = it.info([photo], tmp_path / 'info.txt')[0]
    text = out.read_text(encoding='utf-8')
    assert '120 × 80 px' in text and 'PNG' in text


def test_convert_to_avif(photo, tmp_path):
    out = convert_images([photo], tmp_path, fmt='AVIF', quality=60)[0]
    assert out.suffix == '.avif' and Image.open(out).format == 'AVIF'
