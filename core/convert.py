"""Conversões do canivete suíço.

Todas as funções públicas têm a mesma forma:

    fn(files: list[Path], out: Path, **params) -> list[Path]

`out` é um arquivo ou uma pasta, conforme a ferramenta (veja ui/tools.py).
Tudo roda localmente: PyMuPDF, Pillow, openpyxl, markdown e, quando
indicado, o Office instalado.
"""

import difflib
import html
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps, ImageSequence

from core.engines import office

EBOOK_EXTS = {'.epub', '.mobi', '.fb2', '.xps', '.oxps', '.cbz', '.svg'}
EXCEL_EXTS = {'.xlsx', '.xls', '.xlsm', '.ods', '.csv'}
POWERPOINT_EXTS = {'.pptx', '.ppt', '.pps', '.ppsx', '.odp'}
WEB_EXTS = {'.html', '.htm', '.md', '.markdown', '.txt'}
RASTER_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp', '.gif', '.ico', '.avif'}

IMAGE_FORMATS = {  # nome na interface: (extensão, formato do Pillow)
    'PNG': ('png', 'PNG'), 'JPG': ('jpg', 'JPEG'), 'WebP': ('webp', 'WEBP'),
    'BMP': ('bmp', 'BMP'), 'TIFF': ('tiff', 'TIFF'), 'ICO': ('ico', 'ICO'), 'GIF': ('gif', 'GIF'),
    'AVIF': ('avif', 'AVIF'),
}


# --- utilitários ------------------------------------------------------------
def unique(path: Path) -> Path:
    path = Path(path)
    stem, suffix, n = path.stem, path.suffix, 2
    while path.exists():
        path = path.with_name(f'{stem} ({n}){suffix}')
        n += 1
    return path


def _page_images(pdf: Path, dpi: int) -> list[Image.Image]:
    zoom = dpi / 72
    with pymupdf.open(pdf) as doc:
        return [doc[i].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False).pil_image()
                for i in range(doc.page_count)]


def _save_image(img: Image.Image, target: Path, pil_format: str, quality: int = 90) -> Path:
    if pil_format in ('JPEG', 'BMP') and img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
    if pil_format == 'ICO':
        img.save(target, 'ICO', sizes=[(s, s) for s in (16, 32, 48, 64, 128, 256)
                                       if s <= max(img.size)] or [(16, 16)])
    elif pil_format in ('JPEG', 'WEBP', 'AVIF'):
        img.save(target, pil_format, quality=quality, optimize=True)
    else:
        img.save(target, pil_format)
    return target


# --- PDF para ... -----------------------------------------------------------
def pdf_to_images(files, out: Path, fmt: str = 'PNG', dpi: int = 150) -> list[Path]:
    ext, pil_format = IMAGE_FORMATS[fmt]
    results = []
    for pdf in files:
        for n, img in enumerate(_page_images(pdf, dpi), start=1):
            results.append(_save_image(img, unique(Path(out) / f'{Path(pdf).stem}_p{n:03}.{ext}'),
                                       pil_format))
    return results


def pdf_to_gif(files, out: Path, dpi: int = 72, frame_ms: int = 800) -> list[Path]:
    frames = _page_images(files[0], dpi)
    base = frames[0].size
    frames = [f if f.size == base else ImageOps.pad(f, base, color='white') for f in frames]
    frames[0].save(out, 'GIF', save_all=True, append_images=frames[1:],
                   duration=frame_ms, loop=0, optimize=True)
    return [Path(out)]


def pdf_to_text(files, out: Path) -> list[Path]:
    with pymupdf.open(files[0]) as doc:
        parts = [f'--- Página {i + 1} ---\n{page.get_text()}' for i, page in enumerate(doc)]
    Path(out).write_text('\n'.join(parts), encoding='utf-8')
    return [Path(out)]


def pdf_to_html(files, out: Path) -> list[Path]:
    with pymupdf.open(files[0]) as doc:
        pages = [f'<section class="page">{page.get_text("xhtml")}</section>' for page in doc]
    title = html.escape(Path(files[0]).stem)
    Path(out).write_text(
        f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{title}</title>'
        '<style>body{font-family:sans-serif;max-width:900px;margin:auto;padding:24px}'
        '.page{border-bottom:1px solid #ccc;padding:16px 0}img{max-width:100%}</style>'
        f'</head><body>{"".join(pages)}</body></html>', encoding='utf-8')
    return [Path(out)]


def pdf_to_svg(files, out: Path) -> list[Path]:
    results = []
    with pymupdf.open(files[0]) as doc:
        for n, page in enumerate(doc, start=1):
            target = unique(Path(out) / f'{Path(files[0]).stem}_p{n:03}.svg')
            target.write_text(page.get_svg_image(text_as_path=False), encoding='utf-8')
            results.append(target)
    return results


def extract_images(files, out: Path, min_side: int = 32) -> list[Path]:
    """Imagens embutidas no PDF, no formato original. Ignora ícones minúsculos."""
    results, seen = [], set()
    with pymupdf.open(files[0]) as doc:
        for page in doc:
            for info in page.get_images(full=True):
                xref = info[0]
                if xref in seen:
                    continue
                seen.add(xref)
                data = doc.extract_image(xref)
                if not data or min(data['width'], data['height']) < min_side:
                    continue
                target = unique(Path(out) / f'{Path(files[0]).stem}_img{len(results) + 1:03}.{data["ext"]}')
                target.write_bytes(data['image'])
                results.append(target)
    if not results:
        raise ValueError('Nenhuma imagem encontrada neste PDF.')
    return results


def pdf_to_excel(files, out: Path) -> list[Path]:
    """Cada tabela detectada vira uma aba da planilha."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    wb.remove(wb.active)
    with pymupdf.open(files[0]) as doc:
        for p, page in enumerate(doc, start=1):
            for t, table in enumerate(page.find_tables().tables, start=1):
                ws = wb.create_sheet(f'Pág {p} - Tab {t}'[:31])
                for row in table.extract():
                    ws.append(['' if c is None else str(c) for c in row])
                for cell in ws[1]:
                    cell.font = Font(bold=True)
    if not wb.sheetnames:
        raise ValueError('Nenhuma tabela encontrada neste PDF.')
    wb.save(out)
    return [Path(out)]


def pdf_to_powerpoint(files, out: Path, dpi: int = 150) -> list[Path]:
    """Uma página por slide (como imagem), via PowerPoint local."""
    import tempfile

    with pymupdf.open(files[0]) as doc:
        width, height = doc[0].rect.width, doc[0].rect.height
    with tempfile.TemporaryDirectory(prefix='ilovefmtly_ppt_') as tmp:
        images = pdf_to_images(files[:1], Path(tmp), 'PNG', dpi)
        office.images_to_powerpoint(images, width, height, Path(out))
    return [Path(out)]


def compare_pdfs(files, out: Path) -> list[Path]:
    """Relatório HTML lado a lado com as diferenças de texto, página a página."""
    if len(files) != 2:
        raise ValueError('Escolha exatamente dois PDFs para comparar.')
    texts = []
    for pdf in files:
        with pymupdf.open(pdf) as doc:
            texts.append([page.get_text().splitlines() for page in doc])
    a_name, b_name = Path(files[0]).name, Path(files[1]).name
    differ = difflib.HtmlDiff(wrapcolumn=70)
    sections, changed = [], 0
    for n in range(max(len(texts[0]), len(texts[1]))):
        a = texts[0][n] if n < len(texts[0]) else []
        b = texts[1][n] if n < len(texts[1]) else []
        if a == b:
            continue
        changed += 1
        sections.append(f'<h2>Página {n + 1}</h2>' + differ.make_table(a, b, a_name, b_name, context=True))
    summary = (f'{changed} página(s) com diferenças.' if changed
               else 'Nenhuma diferença de texto encontrada.')
    Path(out).write_text(
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Comparação</title>'
        '<style>body{font-family:sans-serif;padding:16px}table.diff{font-family:monospace;'
        'border-collapse:collapse;width:100%}td{padding:2px 6px}.diff_add{background:#cfc}'
        '.diff_chg{background:#ffa}.diff_sub{background:#fcc}</style></head><body>'
        f'<h1>{html.escape(a_name)} × {html.escape(b_name)}</h1><p>{summary}</p>'
        f'{"".join(sections)}</body></html>', encoding='utf-8')
    return [Path(out)]


# --- PDF para PDF -------------------------------------------------------------
def grayscale_pdf(files, out: Path, dpi: int = 150) -> list[Path]:
    """Páginas em tons de cinza. As páginas viram imagem (o texto deixa de ser selecionável)."""
    result = pymupdf.open()
    zoom = dpi / 72
    with pymupdf.open(files[0]) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csGRAY)
            new = result.new_page(width=page.rect.width, height=page.rect.height)
            new.insert_image(new.rect, pixmap=pix)
    result.save(out, garbage=3, deflate=True)
    result.close()
    return [Path(out)]


def crop_margins(files, out: Path, margin: int = 12) -> list[Path]:
    """Corta as margens em branco de cada página, deixando `margin` pontos de folga."""
    with pymupdf.open(files[0]) as doc:
        for page in doc:
            boxes = [pymupdf.Rect(b[1]) for b in page.get_bboxlog() if not pymupdf.Rect(b[1]).is_empty]
            if not boxes:
                continue
            content = boxes[0]
            for box in boxes[1:]:
                content |= box
            area = (content + (-margin, -margin, margin, margin)) & page.mediabox
            if not area.is_empty:
                page.set_cropbox(area * page.derotation_matrix if page.rotation else area)
        doc.save(out, garbage=3, deflate=True)
    return [Path(out)]


# --- ... para PDF -------------------------------------------------------------
def word_to_pdf(files, out: Path) -> list[Path]:
    from core.engines import word
    return [word.to_pdf(files[0], out)]


def pdf_to_word(files, out: Path) -> list[Path]:
    from core.engines import word
    return [word.pdf_to_docx(files[0], out)]


def excel_to_pdf(files, out: Path) -> list[Path]:
    return [office.excel_to_pdf(files[0], out)]


def powerpoint_to_pdf(files, out: Path) -> list[Path]:
    return [office.powerpoint_to_pdf(files[0], out)]


def ebook_to_pdf(files, out: Path) -> list[Path]:
    """EPUB, MOBI, FB2, XPS, CBZ e SVG para PDF."""
    with pymupdf.open(files[0]) as doc:
        if doc.is_reflowable:
            doc.layout(rect=pymupdf.paper_rect('a4'), fontsize=11)
        pdf_bytes = doc.convert_to_pdf()
    with pymupdf.open('pdf', pdf_bytes) as pdf:
        pdf.save(out, garbage=3, deflate=True)
    return [Path(out)]


_WEB_CSS = """
body { font-family: sans-serif; font-size: 11pt; line-height: 1.45; color: #111; }
h1 { font-size: 20pt; } h2 { font-size: 16pt; } h3 { font-size: 13pt; }
pre, code { font-family: monospace; font-size: 9.5pt; background: #f2f2f2; }
table { border-collapse: collapse; } td, th { border: 1px solid #999; padding: 3px 6px; }
"""


def web_to_pdf(files, out: Path) -> list[Path]:
    """HTML, Markdown ou TXT para PDF A4 (imagens locais relativas são incluídas)."""
    src = Path(files[0])
    text = src.read_text(encoding='utf-8', errors='replace')
    ext = src.suffix.lower()
    if ext in ('.md', '.markdown'):
        import markdown
        body = markdown.markdown(text, extensions=['tables', 'fenced_code'])
    elif ext == '.txt':
        body = f'<pre style="white-space: pre-wrap">{html.escape(text)}</pre>'
    else:
        body = text
    story = pymupdf.Story(html=body, user_css=_WEB_CSS, archive=str(src.parent))
    writer = pymupdf.DocumentWriter(str(out))
    mediabox = pymupdf.paper_rect('a4')
    where = mediabox + (50, 50, -50, -50)
    more = True
    while more:
        device = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
    writer.close()
    return [Path(out)]


# --- imagens ------------------------------------------------------------------
def convert_images(files, out: Path, fmt: str = 'PNG', quality: int = 90) -> list[Path]:
    ext, pil_format = IMAGE_FORMATS[fmt]
    results = []
    for src in files:
        with Image.open(src) as img:
            img.load()
            target = unique(Path(out) / f'{Path(src).stem}.{ext}')
            results.append(_save_image(img, target, pil_format, quality))
    return results


def resize_images(files, out: Path, percent: int = 50) -> list[Path]:
    if not 1 <= percent <= 1000:
        raise ValueError('Use uma porcentagem entre 1 e 1000.')
    results = []
    for src in files:
        with Image.open(src) as img:
            size = (max(1, img.width * percent // 100), max(1, img.height * percent // 100))
            resized = img.resize(size, Image.LANCZOS)
            fmt = (img.format or 'PNG').upper()
            target = unique(Path(out) / f'{Path(src).stem}_{percent}pct{Path(src).suffix.lower()}')
            results.append(_save_image(resized, target, fmt if fmt != 'MPO' else 'JPEG'))
    return results


def compress_images(files, out: Path, quality: int = 70) -> list[Path]:
    """JPG e WebP com qualidade reduzida; PNG com paleta otimizada."""
    results = []
    for src in files:
        with Image.open(src) as img:
            img.load()
            fmt = (img.format or 'PNG').upper()
            target = unique(Path(out) / f'{Path(src).stem}_comprimido{Path(src).suffix.lower()}')
            if fmt == 'PNG':
                reduced = img.convert('RGBA').quantize(colors=256, method=Image.Quantize.FASTOCTREE)
                reduced.save(target, 'PNG', optimize=True)
            elif fmt in ('JPEG', 'MPO', 'WEBP'):
                _save_image(img, target, 'WEBP' if fmt == 'WEBP' else 'JPEG', quality)
            else:
                _save_image(img.convert('RGB'), target.with_suffix('.jpg'), 'JPEG', quality)
                target = target.with_suffix('.jpg')
            results.append(target)
    return results


def images_to_gif(files, out: Path, frame_ms: int = 500, width: int = 0) -> list[Path]:
    """Imagens em sequência viram um GIF animado (no tamanho da primeira, ou `width`)."""
    frames = []
    for src in files:
        with Image.open(src) as img:
            frames.append(img.convert('RGBA'))
    base = frames[0].size
    if width:
        base = (width, max(1, base[1] * width // base[0]))
    frames = [ImageOps.pad(f, base, color=(255, 255, 255, 0)) for f in frames]
    frames[0].save(out, 'GIF', save_all=True, append_images=frames[1:],
                   duration=frame_ms, loop=0, disposal=2, optimize=True)
    return [Path(out)]


def gif_to_frames(files, out: Path) -> list[Path]:
    results = []
    with Image.open(files[0]) as gif:
        for n, frame in enumerate(ImageSequence.Iterator(gif), start=1):
            target = unique(Path(out) / f'{Path(files[0]).stem}_q{n:03}.png')
            frame.convert('RGBA').save(target, 'PNG')
            results.append(target)
    return results
