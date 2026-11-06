import pymupdf

from core.document import PageRef
from core.engines import mupdf


def test_build_merges_and_rotates(make_pdf, tmp_path):
    a, b = make_pdf(2, 'A'), make_pdf(3, 'B')
    pages = [PageRef(a, 0, 90), PageRef(a, 1)] + [PageRef(b, i) for i in range(3)]
    out = mupdf.build(pages, tmp_path / 'out.pdf')
    with pymupdf.open(out) as doc:
        assert doc.page_count == 5
        assert doc[0].rotation == 90
        assert doc[1].rotation == 0
        assert 'A 1' in doc[0].get_text()
        assert 'B 3' in doc[4].get_text()


def test_build_reorders(make_pdf, tmp_path):
    a = make_pdf(3)
    out = mupdf.build([PageRef(a, 2), PageRef(a, 0)], tmp_path / 'out.pdf')
    with pymupdf.open(out) as doc:
        assert 'Página 3' in doc[0].get_text()
        assert 'Página 1' in doc[1].get_text()


def test_page_numbers(make_pdf):
    a = make_pdf(3)
    mupdf.add_page_numbers(a)
    assert '1 / 3' in mupdf.extract_text(a, 0)
    assert '3 / 3' in mupdf.extract_text(a, 2)


def test_page_numbers_on_rotated_page(make_pdf, tmp_path):
    a = make_pdf(1)
    out = mupdf.build([PageRef(a, 0, 90)], tmp_path / 'r.pdf')
    mupdf.add_page_numbers(out)
    assert '1 / 1' in mupdf.extract_text(out, 0)


def test_watermark(make_pdf):
    a = make_pdf(2)
    mupdf.add_watermark(a, 'CONFIDENCIAL')
    assert 'CONFIDENCIAL' in mupdf.extract_text(a, 1)


def test_image_to_pdf(make_png, tmp_path):
    out = mupdf.image_to_pdf(make_png(), tmp_path / 'img.pdf')
    assert mupdf.page_count(out) == 1


def test_render_png(make_pdf):
    data = mupdf.render(make_pdf(1), 0, 0.5)
    assert data.startswith(b'\x89PNG')


def test_export_images(make_pdf, tmp_path):
    out = tmp_path / 'imgs'
    out.mkdir()
    files = mupdf.export_images(make_pdf(3), out, 'doc')
    assert [f.name for f in files] == ['doc_p001.png', 'doc_p002.png', 'doc_p003.png']
    assert files[0].read_bytes().startswith(b'\x89PNG')
    jpgs = mupdf.export_images(make_pdf(1), out, 'doc', fmt='jpg')
    assert jpgs[0].read_bytes().startswith(b'\xff\xd8')


def test_compress_images_keeps_pages(make_pdf):
    a = make_pdf(2)
    mupdf.compress_images(a)
    assert mupdf.page_count(a) == 2
