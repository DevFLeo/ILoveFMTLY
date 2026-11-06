import sys
from pathlib import Path

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def make_pdf(tmp_path):
    counter = {'n': 0}

    def _make(n_pages: int, text: str = 'Página') -> Path:
        counter['n'] += 1
        out = tmp_path / f'doc{counter["n"]}.pdf'
        doc = pymupdf.open()
        for i in range(n_pages):
            page = doc.new_page()
            page.insert_text((72, 72), f'{text} {i + 1}')
        doc.save(out)
        doc.close()
        return out

    return _make


@pytest.fixture
def make_png(tmp_path):
    def _make() -> Path:
        out = tmp_path / 'img.png'
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 40, 30), False)
        pix.clear_with(200)
        pix.save(out)
        return out

    return _make
