"""Exportação: transforma o Document em arquivo(s) PDF.

Ordem fixa: montar (mupdf), numerar, marca d'água, compressão com perda,
otimizar e linearizar (qpdf), limpar metadados e, por último, a senha — a
criptografia precisa ser a última etapa, senão as anteriores não conseguem
abrir o arquivo.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from core.document import Document
from core.engines import mupdf, qpdf

Compression = Literal['none', 'lossless', 'lossy']


@dataclass
class ExportOptions:
    page_numbers: bool = False
    watermark: str | None = None
    compress: Compression = 'lossless'
    linearize: bool = True
    strip_metadata: bool = False
    password: str | None = None


def export(doc: Document, out: Path, opts: ExportOptions | None = None) -> Path:
    opts = opts or ExportOptions()
    if len(doc) == 0:
        raise ValueError('Documento sem páginas')
    out = Path(out)
    partial = out.with_name(out.name + '.partial')
    try:
        mupdf.build(doc.pages, partial, doc.passwords)
        if opts.page_numbers:
            mupdf.add_page_numbers(partial)
        if opts.watermark:
            mupdf.add_watermark(partial, opts.watermark)
        if opts.compress == 'lossy':
            mupdf.compress_images(partial)
        if opts.compress != 'none' or opts.linearize:
            qpdf.optimize(partial, linearize=opts.linearize)
        if opts.strip_metadata:
            qpdf.strip_metadata(partial)
        if opts.password:
            qpdf.protect(partial, opts.password)
        os.replace(partial, out)
    finally:
        if partial.exists():
            partial.unlink()
    return out


def split(doc: Document, ranges: list[list[int]], out_dir: Path, stem: str,
          opts: ExportOptions | None = None) -> list[Path]:
    """Um arquivo por grupo de páginas: {stem}_parte1.pdf, {stem}_parte2.pdf..."""
    out_dir = Path(out_dir)
    results = []
    for n, group in enumerate(ranges, start=1):
        target = out_dir / f'{stem}_parte{n}.pdf'
        k = 2
        while target.exists():
            target = out_dir / f'{stem}_parte{n} ({k}).pdf'
            k += 1
        results.append(export(doc.subset(group), target, opts))
    return results
