import pikepdf
import pymupdf
import pytest

from core import importer
from core.document import Document
from core.engines import mupdf, qpdf
from core.export import ExportOptions, export, split
from core.workspace import Workspace


@pytest.fixture
def ws(tmp_path):
    return Workspace(tmp_path / 'ws')


def doc_from(path):
    d = Document()
    d.add_source(path, mupdf.page_count(path))
    return d


def test_export_all_options(make_pdf, tmp_path):
    d = doc_from(make_pdf(3))
    opts = ExportOptions(page_numbers=True, watermark='SIGILOSO', compress='lossy',
                         strip_metadata=True, password='abc')
    out = export(d, tmp_path / 'final.pdf', opts)
    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(out)
    with pymupdf.open(out) as pdf:
        assert pdf.authenticate('abc')
        text = pdf[0].get_text()
    assert '1 / 3' in text
    assert 'SIGILOSO' in text
    assert not out.with_name(out.name + '.partial').exists()


def test_export_empty_raises(tmp_path):
    with pytest.raises(ValueError, match='Documento sem páginas'):
        export(Document(), tmp_path / 'x.pdf')


def test_split(make_pdf, tmp_path):
    d = doc_from(make_pdf(3))
    files = split(d, [[0, 1], [2]], tmp_path, 'doc')
    assert [f.name for f in files] == ['doc_parte1.pdf', 'doc_parte2.pdf']
    assert [mupdf.page_count(f) for f in files] == [2, 1]


def test_split_does_not_overwrite(make_pdf, tmp_path):
    d = doc_from(make_pdf(1))
    (tmp_path / 'doc_parte1.pdf').write_bytes(b'antigo')
    files = split(d, [[0]], tmp_path, 'doc')
    assert files[0].name == 'doc_parte1 (2).pdf'
    assert (tmp_path / 'doc_parte1.pdf').read_bytes() == b'antigo'


def test_import_pdf_keeps_original(make_pdf, ws):
    src = make_pdf(2)
    before = src.read_bytes()
    copy = importer.import_file(ws, src)
    assert copy.parent == ws.path
    assert src.read_bytes() == before


def test_import_image(make_png, ws):
    out = importer.import_file(ws, make_png())
    assert mupdf.page_count(out) == 1


def test_import_password(make_pdf, ws):
    src = make_pdf(2)
    qpdf.protect(src, 'pw')
    with pytest.raises(importer.PasswordRequired):
        importer.import_file(ws, src)
    with pytest.raises(importer.WrongPassword):
        importer.import_file(ws, src, 'errada')
    clear = importer.import_file(ws, src, 'pw')
    assert not mupdf.needs_password(clear)
    assert mupdf.page_count(clear) == 2


def test_import_garbage_raises(tmp_path, ws):
    bad = tmp_path / 'bad.pdf'
    bad.write_bytes(b'lixo')
    with pytest.raises(qpdf.PdfRepairError):
        importer.import_file(ws, bad)
    assert list(ws.path.iterdir()) == []


def test_import_unsupported(tmp_path, ws):
    f = tmp_path / 'x.docx'
    f.write_bytes(b'x')
    with pytest.raises(importer.UnsupportedFile):
        importer.import_file(ws, f)
