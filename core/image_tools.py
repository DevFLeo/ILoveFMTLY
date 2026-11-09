"""Mais ferramentas de imagem (Pillow, tudo local).

Mesma forma das conversões: fn(files, out, **params) -> list[Path], onde `out`
é uma pasta (ou um arquivo, nas que juntam várias imagens numa só).
"""

import base64
import binascii
import json
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from core.convert import unique
from core.images import ImageError, _open, _save

EFFECTS = ('Preto e branco', 'Sépia', 'Inverter cores', 'Desfoque', 'Nitidez', 'Contorno',
           'Relevo', 'Pôster')
BORDER_COLORS = {'Branco': (255, 255, 255), 'Preto': (0, 0, 0), 'Cinza': (128, 128, 128),
                 'Transparente': None}
LAYOUTS = ('Lado a lado', 'Empilhadas', 'Grade')
B64_KINDS = ('Data URI (para HTML/CSS)', 'Base64 puro')
FAVICON_PNGS = (16, 32, 48, 64, 96, 128, 192, 256, 512)


def _target(out: Path, src: Path, tag: str, ext: str | None = None) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    return unique(out / f'{Path(src).stem}{tag}{ext or Path(src).suffix.lower()}')


def _still(path: Path) -> tuple[Image.Image, str | None]:
    """Primeiro quadro, já com a orientação do EXIF aplicada."""
    im = _open(path)
    return ImageOps.exif_transpose(im), im.format


def _clamp(value: int, lo: int, hi: int, label: str) -> int:
    value = int(value)
    if not lo <= value <= hi:
        raise ImageError(f'{label} deve ficar entre {lo} e {hi}.')
    return value


# --- ajustes e filtros ----------------------------------------------------------
def adjust(files, out: Path, brightness: int = 100, contrast: int = 100, saturation: int = 100,
           sharpness: int = 100) -> list[Path]:
    """Valores em %: 100 = sem mudança."""
    steps = [(ImageEnhance.Brightness, brightness, 'Brilho'), (ImageEnhance.Contrast, contrast, 'Contraste'),
             (ImageEnhance.Color, saturation, 'Saturação'), (ImageEnhance.Sharpness, sharpness, 'Nitidez')]
    results = []
    for f in files:
        im, fmt = _still(f)
        alpha = im.getchannel('A') if 'A' in im.getbands() else None
        work = im.convert('RGB')
        for enhancer, value, label in steps:
            value = _clamp(value, 0, 300, label)
            if value != 100:
                work = enhancer(work).enhance(value / 100)
        if alpha is not None:
            work.putalpha(alpha)
        results.append(_save(work, _target(out, f, '_ajustada'), fmt))
    return results


def _sepia(im: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(im)
    return ImageOps.colorize(gray, (40, 26, 13), (255, 240, 192))


def filter_images(files, out: Path, effect: str = 'Preto e branco', strength: int = 50) -> list[Path]:
    if effect not in EFFECTS:
        raise ImageError(f'Efeito desconhecido: {effect}')
    strength = _clamp(strength, 1, 100, 'Intensidade')
    results = []
    for f in files:
        im, fmt = _still(f)
        alpha = im.getchannel('A') if 'A' in im.getbands() else None
        rgb = im.convert('RGB')
        if effect == 'Preto e branco':
            res = ImageOps.grayscale(rgb).convert('RGB')
        elif effect == 'Sépia':
            res = _sepia(rgb)
        elif effect == 'Inverter cores':
            res = ImageOps.invert(rgb)
        elif effect == 'Desfoque':
            res = rgb.filter(ImageFilter.GaussianBlur(radius=strength / 10))
        elif effect == 'Nitidez':
            res = rgb.filter(ImageFilter.UnsharpMask(radius=2, percent=strength * 3, threshold=2))
        elif effect == 'Contorno':
            res = ImageOps.invert(ImageOps.grayscale(rgb).filter(ImageFilter.FIND_EDGES)).convert('RGB')
        elif effect == 'Relevo':
            res = rgb.filter(ImageFilter.EMBOSS)
        else:  # Pôster: menos cores
            res = ImageOps.posterize(rgb, max(1, 8 - round(strength / 15)))
        if alpha is not None:
            res.putalpha(alpha)
        results.append(_save(res, _target(out, f, '_filtro'), fmt))
    return results


# --- cantos e borda -------------------------------------------------------------
def frame(files, out: Path, radius: int = 24, border: int = 0, color: str = 'Branco') -> list[Path]:
    """Cantos arredondados (px) e borda (px). Sai em PNG para guardar a transparência."""
    if color not in BORDER_COLORS:
        raise ImageError(f'Cor desconhecida: {color}')
    radius, border = _clamp(radius, 0, 2000, 'Raio'), _clamp(border, 0, 500, 'Borda')
    fill = BORDER_COLORS[color]
    results = []
    for f in files:
        im, _ = _still(f)
        im = im.convert('RGBA')
        if border:
            canvas = Image.new('RGBA', (im.width + 2 * border, im.height + 2 * border),
                               (*fill, 255) if fill else (0, 0, 0, 0))
            canvas.paste(im, (border, border), im)
            im = canvas
        if radius:
            mask = Image.new('L', im.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1),
                                                   radius=min(radius, min(im.size) // 2), fill=255)
            im.putalpha(ImageChops.multiply(im.getchannel('A'), mask))
        results.append(_save(im, _target(out, f, '_moldura', '.png'), 'PNG'))
    return results


# --- fundo transparente -----------------------------------------------------------
def remove_background(files, out: Path, tolerance: int = 30) -> list[Path]:
    """Deixa transparente o fundo liso que encosta nas bordas (ex.: foto de produto,
    logo em fundo branco). Não usa IA: funciona para fundos de cor única."""
    tolerance = _clamp(tolerance, 0, 255, 'Tolerância')
    results = []
    for f in files:
        im, _ = _still(f)
        rgba = im.convert('RGBA')
        marker = (255, 0, 255, 0)
        work = rgba.convert('RGB')
        flood = work.copy()
        w, h = work.size
        for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
            if flood.getpixel(corner) != marker[:3]:
                ImageDraw.floodfill(flood, corner, marker[:3], thresh=tolerance)
        bg = Image.eval(ImageChops.difference(flood, Image.new('RGB', flood.size, marker[:3]))
                        .convert('L'), lambda v: 255 if v else 0)
        rgba.putalpha(ImageChops.multiply(rgba.getchannel('A'), bg))
        results.append(_save(rgba, _target(out, f, '_sem_fundo', '.png'), 'PNG'))
    return results


# --- comprimir até um tamanho -------------------------------------------------------
def compress_to_size(files, out: Path, target_kb: int = 200, fmt: str = 'JPG') -> list[Path]:
    """Procura a maior qualidade que cabe no tamanho; se não couber, reduz a imagem."""
    target_kb = _clamp(target_kb, 5, 100_000, 'Tamanho alvo')
    pil, ext = {'JPG': ('JPEG', '.jpg'), 'WebP': ('WEBP', '.webp')}[fmt]
    limit = target_kb * 1024
    results = []
    for f in files:
        im, _ = _still(f)
        im = im.convert('RGB')
        target = _target(out, f, f'_{target_kb}kb', ext)
        best = None
        for _ in range(6):  # até 6 reduções de tamanho
            lo, hi = 10, 95
            while lo <= hi:
                q = (lo + hi) // 2
                im.save(target, pil, quality=q, optimize=True)
                if target.stat().st_size <= limit:
                    best, lo = q, q + 1
                else:
                    hi = q - 1
            if best is not None:
                im.save(target, pil, quality=best, optimize=True)
                break
            im = im.resize((max(1, int(im.width * 0.8)), max(1, int(im.height * 0.8))), Image.LANCZOS)
        if best is None:
            target.unlink(missing_ok=True)
            raise ImageError(f'{Path(f).name}: não coube em {target_kb} KB nem reduzindo a imagem.')
        results.append(target)
    return results


# --- colagem ------------------------------------------------------------------------
def collage(files, out: Path, layout: str = 'Lado a lado', gap: int = 16,
            background: str = 'Branco') -> list[Path]:
    if layout not in LAYOUTS:
        raise ImageError(f'Arranjo desconhecido: {layout}')
    if len(files) < 2:
        raise ImageError('Escolha pelo menos duas imagens.')
    gap = _clamp(gap, 0, 500, 'Espaço')
    fill = BORDER_COLORS.get(background, (255, 255, 255))
    ims = [_still(f)[0].convert('RGBA') for f in files]
    if layout == 'Lado a lado':
        h = min(i.height for i in ims)
        ims = [i.resize((max(1, round(i.width * h / i.height)), h), Image.LANCZOS) for i in ims]
        cols, rows = len(ims), 1
    elif layout == 'Empilhadas':
        w = min(i.width for i in ims)
        ims = [i.resize((w, max(1, round(i.height * w / i.width))), Image.LANCZOS) for i in ims]
        cols, rows = 1, len(ims)
    else:
        cols = max(1, round(len(ims) ** 0.5 + 0.49))
        rows = -(-len(ims) // cols)
        side = min(min(i.size) for i in ims)
        ims = [ImageOps.fit(i, (side, side), Image.LANCZOS) for i in ims]
    widths = [max(ims[r * cols + c].width for r in range(rows) if r * cols + c < len(ims))
              for c in range(cols)]
    heights = [max(ims[r * cols + c].height for c in range(cols) if r * cols + c < len(ims))
               for r in range(rows)]
    canvas = Image.new('RGBA', (sum(widths) + gap * (cols + 1), sum(heights) + gap * (rows + 1)),
                       (*fill, 255) if fill else (0, 0, 0, 0))
    y = gap
    for r in range(rows):
        x = gap
        for c in range(cols):
            i = r * cols + c
            if i < len(ims):
                canvas.paste(ims[i], (x, y), ims[i])
            x += widths[c] + gap
        y += heights[r] + gap
    out = Path(out)
    return [_save(canvas, out, 'PNG')]


# --- paleta ---------------------------------------------------------------------------
def palette(files, out: Path, colors: int = 6) -> list[Path]:
    """Cores principais: uma faixa PNG e um TXT com os códigos hex."""
    colors = _clamp(colors, 2, 16, 'Cores')
    results = []
    for f in files:
        im, _ = _still(f)
        small = im.convert('RGB')
        small.thumbnail((200, 200))
        quant = small.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
        pal = quant.getpalette()[:colors * 3]
        counts = sorted(quant.getcolors(), reverse=True)
        hexes = []
        for _, idx in counts:
            r, g, b = pal[idx * 3:idx * 3 + 3]
            hexes.append(f'#{r:02X}{g:02X}{b:02X}')
        swatch = Image.new('RGB', (100 * len(hexes), 100))
        draw = ImageDraw.Draw(swatch)
        for i, hx in enumerate(hexes):
            draw.rectangle((i * 100, 0, i * 100 + 99, 99), fill=hx)
        png = _target(out, f, '_paleta', '.png')
        swatch.save(png)
        txt = png.with_suffix('.txt')
        txt.write_text('\n'.join(hexes) + '\n', encoding='utf-8')
        results += [png, txt]
    return results


# --- favicon --------------------------------------------------------------------------
def favicon(files, out: Path) -> list[Path]:
    """favicon.ico, PNGs 16 a 512, apple-touch-icon, site.webmanifest e o HTML para colar."""
    im, _ = _still(files[0])
    im = ImageOps.fit(im.convert('RGBA'), (512, 512), Image.LANCZOS)
    folder = Path(out)
    folder.mkdir(parents=True, exist_ok=True)
    made = []
    ico = folder / 'favicon.ico'
    im.save(ico, 'ICO', sizes=[(16, 16), (32, 32), (48, 48)])
    made.append(ico)
    for s in FAVICON_PNGS:
        p = folder / f'favicon-{s}x{s}.png'
        im.resize((s, s), Image.LANCZOS).save(p)
        made.append(p)
    apple = folder / 'apple-touch-icon.png'
    bg = Image.new('RGBA', (180, 180), (255, 255, 255, 255))
    bg.alpha_composite(im.resize((180, 180), Image.LANCZOS))
    bg.convert('RGB').save(apple)
    made.append(apple)
    manifest = folder / 'site.webmanifest'
    manifest.write_text(json.dumps({'name': '', 'short_name': '', 'icons': [
        {'src': '/favicon-192x192.png', 'sizes': '192x192', 'type': 'image/png'},
        {'src': '/favicon-512x512.png', 'sizes': '512x512', 'type': 'image/png'}],
        'display': 'standalone'}, indent=2), encoding='utf-8')
    made.append(manifest)
    snippet = folder / 'favicon.html'
    snippet.write_text(
        '<link rel="icon" href="/favicon.ico" sizes="any">\n'
        '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">\n'
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
        '<link rel="manifest" href="/site.webmanifest">\n', encoding='utf-8')
    made.append(snippet)
    return made


# --- Base64 ---------------------------------------------------------------------------
MIME = {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'GIF': 'image/gif', 'WEBP': 'image/webp',
        'BMP': 'image/bmp', 'ICO': 'image/x-icon', 'TIFF': 'image/tiff', 'AVIF': 'image/avif'}
EXT_BY_MIME = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/gif': '.gif', 'image/webp': '.webp',
               'image/bmp': '.bmp', 'image/x-icon': '.ico', 'image/tiff': '.tiff',
               'image/avif': '.avif', 'image/svg+xml': '.svg'}


def to_base64(files, out: Path, kind: str = B64_KINDS[0]) -> list[Path]:
    results = []
    for f in files:
        data = Path(f).read_bytes()
        _open(f)  # confere que é imagem
        text = base64.b64encode(data).decode('ascii')
        if kind == B64_KINDS[0]:
            fmt = Image.open(f).format or 'PNG'
            text = f'data:{MIME.get(fmt, "application/octet-stream")};base64,{text}'
        target = _target(out, f, '_base64', '.txt')
        target.write_text(text, encoding='ascii')
        results.append(target)
    return results


_DATA_URI = re.compile(r'data:([\w/+.-]+);base64,', re.I)


def from_base64(files, out: Path) -> list[Path]:
    """Lê um .txt com Base64 puro ou data URI e grava a imagem."""
    results = []
    for f in files:
        raw = Path(f).read_text(encoding='utf-8', errors='ignore').strip()
        mime = None
        m = _DATA_URI.search(raw)
        if m:
            mime, raw = m.group(1).lower(), raw[m.end():]
        raw = re.sub(r'\s+', '', raw)
        try:
            data = base64.b64decode(raw + '=' * (-len(raw) % 4), validate=False)
        except (binascii.Error, ValueError):
            raise ImageError(f'{Path(f).name}: o texto não é Base64 válido.') from None
        if mime == 'image/svg+xml':
            ext = '.svg'
        else:
            target = Path(out) / 'tmp.bin'
            Path(out).mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            try:
                fmt = Image.open(target).format
            except OSError:
                target.unlink(missing_ok=True)
                raise ImageError(f'{Path(f).name}: o Base64 não contém uma imagem.') from None
            target.unlink(missing_ok=True)
            ext = EXT_BY_MIME.get(MIME.get(fmt, ''), '.png')
        target = _target(out, f, '_imagem', ext)
        target.write_bytes(data)
        results.append(target)
    return results


# --- informações -------------------------------------------------------------------------
def info(files, out: Path) -> list[Path]:
    """Relatório TXT: formato, medidas, cores, DPI, quadros e EXIF (incluindo GPS)."""
    from PIL.ExifTags import GPSTAGS, TAGS
    lines = []
    for f in files:
        im = _open(f)
        p = Path(f)
        lines += [f'== {p.name}', f'Formato: {im.format}', f'Medidas: {im.width} × {im.height} px',
                  f'Modo de cor: {im.mode}', f'Tamanho do arquivo: {p.stat().st_size:,} bytes'.replace(',', '.')]
        if 'dpi' in im.info:
            lines.append(f'DPI: {round(im.info["dpi"][0])}')
        lines.append(f'Quadros: {getattr(im, "n_frames", 1)}')
        lines.append(f'Transparência: {"sim" if "A" in im.getbands() or "transparency" in im.info else "não"}')
        exif = im.getexif()
        if exif:
            lines.append('EXIF:')
            for tag, value in exif.items():
                lines.append(f'  {TAGS.get(tag, tag)}: {value}')
            gps = exif.get_ifd(0x8825)
            for tag, value in gps.items():
                lines.append(f'  GPS {GPSTAGS.get(tag, tag)}: {value}')
        else:
            lines.append('EXIF: nenhum')
        lines.append('')
    out = Path(out)
    out.write_text('\n'.join(lines), encoding='utf-8')
    return [out]
