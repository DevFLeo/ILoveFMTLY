import pikepdf
import pytest

from core.engines import qpdf


def test_protect_and_unprotect(make_pdf, tmp_path):
    a = make_pdf(2)
    qpdf.protect(a, 'segredo')
    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(a)
    with pikepdf.open(a, password='segredo') as pdf:
        assert pdf.encryption.R == 6
    out = qpdf.unprotect(a, 'segredo', tmp_path / 'livre.pdf')
    with pikepdf.open(out) as pdf:
        assert not pdf.is_encrypted
        assert len(pdf.pages) == 2


def test_protect_rejects_empty(make_pdf):
    with pytest.raises(ValueError):
        qpdf.protect(make_pdf(1), '')


def test_strip_metadata(make_pdf):
    a = make_pdf(1)
    with pikepdf.open(a, allow_overwriting_input=True) as pdf:
        pdf.docinfo['/Author'] = 'Fulano'
        with pdf.open_metadata() as meta:
            meta['dc:creator'] = ['Fulano']
        pdf.save(a)
    assert 'Author' in qpdf.read_metadata(a)
    qpdf.strip_metadata(a)
    meta = qpdf.read_metadata(a)
    assert 'Fulano' not in ' '.join(meta.values())


def test_optimize_keeps_pages(make_pdf):
    a = make_pdf(3)
    qpdf.optimize(a)
    with pikepdf.open(a) as pdf:
        assert len(pdf.pages) == 3
        assert pdf.is_linearized


def test_repair_garbage_raises(tmp_path):
    bad = tmp_path / 'bad.pdf'
    bad.write_bytes(b'isto nao e um pdf')
    with pytest.raises(qpdf.PdfRepairError):
        qpdf.repair(bad, tmp_path / 'out.pdf')


def test_repair_truncated(make_pdf, tmp_path):
    a = make_pdf(3)
    data = a.read_bytes()
    broken = tmp_path / 'broken.pdf'
    broken.write_bytes(data[: int(len(data) * 0.8)])
    try:
        out = qpdf.repair(broken, tmp_path / 'fixed.pdf')
    except qpdf.PdfRepairError:
        return
    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) >= 1
