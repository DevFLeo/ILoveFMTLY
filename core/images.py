"""Fase 2: ferramentas de imagem (Pillow, sem rede).

Funções em lote seguem o padrão do app: (files, out, **params) -> list[Path],
gravando arquivos novos em `out`. `crop` e `blur_area` trabalham com uma
imagem e uma caixa (x0, y0, x1, y1) escolhida no diálogo de recorte.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageSequence

from core.convert import unique
from core.paths import assets

ROTATE_ACTIONS = {
    'Girar 90° à direita': Image.Transpose.ROTATE_270,
    'Girar 90° à esquerda': Image.Transpose.ROTATE_90,
    'Girar 180°': Image.Transpose.ROTATE_180,
    'Espelhar na horizontal': Image.Transpose.FLIP_LEFT_RIGHT,
    'Espelhar na vertical': Image.Transpose.FLIP_TOP_BOTTOM,
}
POSITIONS = ('Centro', 'Superior esquerdo', 'Superior direito', 'Inferior esquerdo',
             'Inferior direito', 'Lado a lado')
ANIM_FORMATS = {'GIF': '.gif', 'WebP': '.webp'}
_FONT = 'fonts/IBMPlexSans-SemiBold.ttf'


class ImageError(Exception):
    """Imagem inválida ou parâmetro fora do intervalo."""


def _open(path: Path) -> Image.Image:
    try:
        im = Image.open(path)
        im.load()
        return im
    except (OSError, Image.DecompressionBombError) as exc:
        raise ImageError(f'{Path(path).name}: não é uma imagem válida ({exc}).') from None


def _truthy(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ('sim', 'true', '1', 'yes')
    return bool(value)


def _is_animated(im: Image.Image) -> bool:
    return getattr(im, 'n_frames', 1) > 1


def _frames(im: Image.Image) -> tuple[list[Image.Image], list[int]]:
    frames, durations = [], []
    for frame in ImageSequence.Iterator(im):
        durations.append(int(frame.info.get('duration', im.info.get('duration', 100)) or 100))
        frames.append(frame.convert('RGBA'))
    return frames, durations


def _save_anim(frames, durations, target: Path, loop: int = 0) -> Path:
    first, rest = frames[0], frames[1:]
    if target.suffix.lower() == '.webp':
        first.save(target, save_all=True, append_images=rest, duration=durations, loop=loop,
                   quality=85, method=4)
    else:
        first.save(target, save_all=True, append_images=rest, duration=durations, loop=loop,
                   disposal=2, optimize=False)
    return target


def _save(im: Image.Image, target: Path, src_format: str | None) -> Path:
    """Grava sem metadados (EXIF, XMP, textos): só pixels, perfil de cor e transparência."""
    fmt = (src_format or target.suffix.lstrip('.')).upper().replace('JPG', 'JPEG')
    keep = {k: im.info[k] for k in ('icc_profile', 'transparency') if k in im.info}
    im = im.copy()
    im.info = {}
    kwargs = dict(keep)
    if fmt == 'JPEG':
        if im.mode not in ('RGB', 'L'):
            im = im.convert('RGB')
        kwargs.pop('transparency', None)
        kwargs.update(quality=95, subsampling=0)
    elif fmt == 'WEBP':
        kwargs.update(quality=95)
    im.save(target, format=fmt, **kwargs)
    return target


def _out(out: Path, src: Path, tag: str, ext: str | None = None) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    return unique(out / f'{Path(src).stem}{tag}{ext or Path(src).suffix.lower()}')


# --- girar / espelhar ----------------------------------------------------------
def rotate(files, out: Path, action: str = 'Girar 90° à direita') -> list[Path]:
    if action not in ROTATE_ACTIONS:
        raise ImageError(f'Ação desconhecida: {action}')
    op = ROTATE_ACTIONS[action]
    results = []
    for f in files:
        im = _open(f)
        target = _out(out, f, '_girada')
        if _is_animated(im):
            frames, durations = _frames(im)
            _save_anim([fr.transpose(op) for fr in frames], durations, target,
                       im.info.get('loop', 0))
        else:
            _save(ImageOps.exif_transpose(im).transpose(op), target, im.format)
        results.append(target)
    return results


# --- EXIF ----------------------------------------------------------------------
def strip_exif(files, out: Path) -> list[Path]:
    """Aplica a orientação EXIF e grava sem EXIF/GPS/XMP/textos."""
    results = []
    for f in files:
        im = _open(f)
        target = _out(out, f, '_sem_exif')
        if _is_animated(im):
            frames, durations = _frames(im)
            _save_anim(frames, durations, target, im.info.get('loop', 0))
        else:
            _save(ImageOps.exif_transpose(im), target, im.format)
        results.append(target)
    return results


# --- marca d'água --------------------------------------------------------------
def _font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(assets() / _FONT), size)
    except OSError:
        return ImageFont.load_default(size)


def _place(canvas: tuple[int, int], item: tuple[int, int], position: str, margin: int):
    W, H = canvas
    w, h = item
    x = {'esquerdo': margin, 'direito': W - w - margin}.get(position.split()[-1], (W - w) // 2)
    y = margin if position.startswith('Superior') else (
        H - h - margin if position.startswith('Inferior') else (H - h) // 2)
    return x, y


def _stamp(base: Image.Image, mark: Image.Image, position: str) -> Image.Image:
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    margin = max(4, min(base.size) // 40)
    if position == 'Lado a lado':
        step_x, step_y = mark.width * 2, mark.height * 3
        for y in range(margin, base.height, step_y):
            for x in range(margin + (y // step_y % 2) * mark.width, base.width, step_x):
                layer.alpha_composite(mark, (x, y))
    else:
        layer.alpha_composite(mark, _place(base.size, mark.size, position, margin))
    return Image.alpha_composite(base.convert('RGBA'), layer)


def _text_mark(text: str, width: int, opacity: int) -> Image.Image:
    size = max(12, width // max(8, len(text) + 2))
    font = _font(size)
    box = font.getbbox(text)
    mark = Image.new('RGBA', (box[2] - box[0] + 8, box[3] - box[1] + 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(mark)
    alpha = round(255 * opacity / 100)
    draw.text((4 - box[0], 4 - box[1]), text, font=font, fill=(255, 255, 255, alpha),
              stroke_width=max(1, size // 18), stroke_fill=(0, 0, 0, alpha))
    return mark


def _logo_mark(logo: Path, width: int, opacity: int) -> Image.Image:
    mark = _open(logo).convert('RGBA')
    target_w = max(16, width // 4)
    if mark.width > target_w:
        mark = mark.resize((target_w, round(mark.height * target_w / mark.width)), Image.LANCZOS)
    if opacity < 100:
        alpha = mark.getchannel('A').point(lambda a: round(a * opacity / 100))
        mark.putalpha(alpha)
    return mark


def watermark(files, out: Path, text: str = '', position: str = 'Centro', opacity: int = 50,
              logo: str = '') -> list[Path]:
    """Texto (Plex SemiBold, branco com contorno) e/ou logo sobre cada imagem."""
    text = (text or '').strip()
    if not text and not logo:
        raise ImageError("Informe o texto ou escolha um logo para a marca d'água.")
    if position not in POSITIONS:
        raise ImageError(f'Posição desconhecida: {position}')
    results = []
    for f in files:
        im = ImageOps.exif_transpose(_open(f))
        fmt = im.format or Image.open(f).format
        marked = im
        if logo:
            marked = _stamp(marked, _logo_mark(Path(logo), im.width, opacity), position)
        if text:
            marked = _stamp(marked, _text_mark(text, im.width, opacity), position)
        target = _out(out, f, '_marca')
        if fmt in ('JPEG', 'BMP'):
            marked = marked.convert('RGB')
        _save(marked, target, fmt)
        results.append(target)
    return results


# --- recortar / borrar ---------------------------------------------------------
def _box(im: Image.Image, box) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = (round(v) for v in box)
    x0, x1 = sorted((max(0, x0), min(im.width, x1)))
    y0, y1 = sorted((max(0, y0), min(im.height, y1)))
    if x1 - x0 < 1 or y1 - y0 < 1:
        raise ImageError('Selecione uma área dentro da imagem.')
    return x0, y0, x1, y1


def crop(src: Path, target: Path, box) -> Path:
    im = ImageOps.exif_transpose(_open(src))
    fmt = Image.open(src).format
    return _save(im.crop(_box(im, box)), Path(target), fmt)


def blur_area(src: Path, target: Path, box, block: int = 12) -> Path:
    """Pixela a área (mosaico): irreversível, ao contrário de um desfoque leve."""
    im = ImageOps.exif_transpose(_open(src))
    fmt = Image.open(src).format
    x0, y0, x1, y1 = _box(im, box)
    region = im.crop((x0, y0, x1, y1))
    small = region.resize((max(1, (x1 - x0) // block), max(1, (y1 - y0) // block)),
                          Image.BILINEAR)
    im = im.copy()
    im.paste(small.resize(region.size, Image.NEAREST), (x0, y0))
    return _save(im, Path(target), fmt)


# --- editar GIF ----------------------------------------------------------------
def edit_gif(files, out: Path, speed: int = 100, first: int = 1, last: int = 0, width: int = 0,
             reverse='Não', fmt: str = 'GIF') -> list[Path]:
    """Velocidade (%), trecho de quadros (1 = primeiro; último 0 = até o fim), largura,
    inverter e formato de saída (GIF ou WebP animado)."""
    if fmt not in ANIM_FORMATS:
        raise ImageError(f'Formato desconhecido: {fmt}')
    if not 10 <= int(speed) <= 1000:
        raise ImageError('A velocidade vai de 10 % a 1000 %.')
    results = []
    for f in files:
        im = _open(f)
        frames, durations = _frames(im)
        n = len(frames)
        a, b = int(first), (int(last) or n)
        if not 1 <= a <= b <= n:
            raise ImageError(f'{Path(f).name}: trecho de quadro {a} a {b}, mas o GIF tem {n}.')
        frames, durations = frames[a - 1:b], durations[a - 1:b]
        if _truthy(reverse):
            frames.reverse()
            durations.reverse()
        durations = [max(20, round(d * 100 / int(speed))) for d in durations]
        if width and int(width) != frames[0].width:
            w = int(width)
            h = max(1, round(frames[0].height * w / frames[0].width))
            frames = [fr.resize((w, h), Image.LANCZOS) for fr in frames]
        target = _out(out, f, '_editado', ANIM_FORMATS[fmt])
        _save_anim(frames, durations, target, im.info.get('loop', 0))
        results.append(target)
    return results
