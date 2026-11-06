"""Motor PyMuPDF: renderização, montagem e alterações de conteúdo.

Responsável por tudo que precisa entender o conteúdo da página (desenhar,
escrever texto, recomprimir imagens). Operações estruturais (senha, reparo,
compressão sem perda, metadados) ficam em engines/qpdf.py.
"""

import os
from pathlib import Path

import pymupdf

from core.document import PageRef


class PasswordRequired(Exception):
    """O PDF tem senha e nenhuma foi informada."""


class WrongPassword(Exception):
    """A senha informada não abre o PDF."""


def open_pdf(path: Path, password: str | None = None) -> pymupdf.Document:
    doc = pymupdf.open(path)
    if doc.needs_pass:
        if not password:
            doc.close()
            raise PasswordRequired(str(path))
        if not doc.authenticate(password):
            doc.close()
            raise WrongPassword(str(path))
    return doc


def needs_password(path: Path) -> bool:
    with pymupdf.open(path) as doc:
        return bool(doc.needs_pass)


def page_count(path: Path, password: str | None = None) -> int:
    doc = open_pdf(path, password)
    try:
        return doc.page_count
    finally:
        doc.close()


def render(path: Path, index: int, zoom: float, rotation: int = 0,
           password: str | None = None) -> bytes:
    """PNG da página, já com a rotação original + `rotation` extra."""
    doc = open_pdf(path, password)
    try:
        matrix = pymupdf.Matrix(zoom, zoom).prerotate(rotation)
        return doc[index].get_pixmap(matrix=matrix, alpha=False).tobytes('png')
    finally:
        doc.close()


def image_to_pdf(img: Path, out: Path) -> Path:
    with pymupdf.open(img) as image_doc:
        pdf_bytes = image_doc.convert_to_pdf()
    with pymupdf.open('pdf', pdf_bytes) as pdf:
        pdf.save(out, garbage=3, deflate=True)
    return Path(out)


def build(pages: list[PageRef], out: Path,
          passwords: dict[Path, str] | None = None) -> Path:
    """Monta um PDF novo a partir da lista de PageRef."""
    passwords = passwords or {}
    sources: dict[Path, pymupdf.Document] = {}
    result = pymupdf.open()
    try:
        for ref in pages:
            src = sources.get(ref.source)
            if src is None:
                src = sources[ref.source] = open_pdf(ref.source, passwords.get(ref.source))
            original = src[ref.index].rotation
            result.insert_pdf(src, from_page=ref.index, to_page=ref.index)
            result[-1].set_rotation((original + ref.rotation) % 360)
        result.save(out, garbage=3, deflate=True)
    finally:
        result.close()
        for src in sources.values():
            src.close()
    return Path(out)


def _save_replace(doc: pymupdf.Document, path: Path) -> None:
    tmp = Path(str(path) + '.tmp')
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    os.replace(tmp, path)


def _insert_upright(page: pymupdf.Page, x: float, y: float, text: str, **kw) -> None:
    """Escreve texto que aparece na horizontal mesmo em página girada."""
    point = pymupdf.Point(x, y) * page.derotation_matrix
    page.insert_text(point, text, rotate=page.rotation, **kw)


def add_page_numbers(path: Path, fmt: str = '{n} / {total}', fontsize: float = 9) -> None:
    doc = pymupdf.open(path)
    total = doc.page_count
    for n, page in enumerate(doc, start=1):
        label = fmt.format(n=n, total=total)
        width = pymupdf.get_text_length(label, fontname='helv', fontsize=fontsize)
        rect = page.rect  # retângulo visível (já considera a rotação)
        _insert_upright(page, (rect.width - width) / 2, rect.height - 20, label,
                        fontsize=fontsize, fontname='helv', color=(0.25, 0.25, 0.25))
    _save_replace(doc, path)


def add_watermark(path: Path, text: str, opacity: float = 0.15) -> None:
    doc = pymupdf.open(path)
    for page in doc:
        box = page.mediabox
        fontsize = max(24.0, min(box.width, box.height) / 8)
        width = pymupdf.get_text_length(text, fontname='helv', fontsize=fontsize)
        center = pymupdf.Point(box.x0 + box.width / 2, box.y0 + box.height / 2)
        start = pymupdf.Point(center.x - width / 2, center.y + fontsize / 3)
        page.insert_text(start, text, fontsize=fontsize, fontname='helv',
                         color=(0.5, 0.5, 0.5), fill_opacity=opacity,
                         morph=(center, pymupdf.Matrix(-45)), overlay=True)
    _save_replace(doc, path)


def compress_images(path: Path, dpi: int = 150, quality: int = 70) -> None:
    """Compressão com perda: reduz resolução e qualidade das imagens."""
    doc = pymupdf.open(path)
    doc.rewrite_images(dpi_threshold=int(dpi * 1.3), dpi_target=dpi, quality=quality)
    _save_replace(doc, path)


def extract_text(path: Path, index: int) -> str:
    with pymupdf.open(path) as doc:
        return doc[index].get_text()
