from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from core import convert
from core.engines import office


@pytest.fixture
def out_dir(tmp_path):
    d = tmp_path / 'saida'
    d.mkdir()
    return d


@pytest.fixture
def make_img(tmp_path):
    counter = {'n': 0}

    def _make(fmt='PNG', size=(80, 60), color=(200, 40, 40)):
        counter['n'] += 1
        path = tmp_path / f'img{counter["n"]}.{fmt.lower().replace("jpeg", "jpg")}'
        Image.new('RGB', size, color).save(path, fmt)
        return path

    return _make


@pytest.fixture
def pdf_with_table(tmp_path):
    path = tmp_path / 'tabela.pdf'
    doc = pymupdf.open()
    page = doc.new_page()
    x0, y0, w, h = 72, 100, 120, 24
    rows = [['Nome', 'Valor'], ['Ana', '10'], ['Bia', '20']]
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            rect = pymupdf.Rect(x0 + c * w, y0 + r * h, x0 + (c + 1) * w, y0 + (r + 1) * h)
            page.draw_rect(rect, color=(0, 0, 0), width=0.8)
            page.insert_text((rect.x0 + 4, rect.y1 - 7), text, fontsize=10)
    doc.save(path)
    return path


@pytest.mark.parametrize('fmt,magic', [('PNG', b'\x89PNG'), ('JPG', b'\xff\xd8'),
                                       ('WebP', b'RIFF'), ('TIFF', b'II')])
def test_pdf_to_images_formats(make_pdf, out_dir, fmt, magic):
    files = convert.pdf_to_images([make_pdf(2)], out_dir, fmt=fmt, dpi=50)
    assert len(files) == 2
    assert files[0].read_bytes().startswith(magic)


def test_pdf_to_gif(make_pdf, tmp_path):
    out = tmp_path / 'a.gif'
    convert.pdf_to_gif([make_pdf(3)], out, dpi=30, frame_ms=300)
    with Image.open(out) as gif:
        assert gif.n_frames == 3


def test_pdf_to_text_and_html(make_pdf, tmp_path):
    pdf = make_pdf(2, 'Sigilo')
    convert.pdf_to_text([pdf], tmp_path / 'a.txt')
    assert 'Sigilo 2' in (tmp_path / 'a.txt').read_text(encoding='utf-8')
    convert.pdf_to_html([pdf], tmp_path / 'a.html')
    assert 'Sigilo 1' in (tmp_path / 'a.html').read_text(encoding='utf-8')


def test_pdf_to_svg(make_pdf, out_dir):
    files = convert.pdf_to_svg([make_pdf(2)], out_dir)
    assert len(files) == 2 and '<svg' in files[0].read_text(encoding='utf-8')


def test_extract_images(make_img, tmp_path, out_dir):
    pdf = tmp_path / 'com_img.pdf'
    doc = pymupdf.open()
    doc.new_page().insert_image(pymupdf.Rect(50, 50, 250, 200), filename=str(make_img()))
    doc.save(pdf)
    files = convert.extract_images([pdf], out_dir)
    assert len(files) == 1


def test_extract_images_none(make_pdf, out_dir):
    with pytest.raises(ValueError, match='Nenhuma imagem'):
        convert.extract_images([make_pdf(1)], out_dir)


def test_pdf_to_excel(pdf_with_table, tmp_path):
    from openpyxl import load_workbook
    out = tmp_path / 't.xlsx'
    convert.pdf_to_excel([pdf_with_table], out)
    ws = load_workbook(out).active
    values = [[c.value for c in row] for row in ws.iter_rows()]
    assert ['Nome', 'Valor'] in values and ['Bia', '20'] in values


def test_pdf_to_excel_without_tables(make_pdf, tmp_path):
    with pytest.raises(ValueError, match='Nenhuma tabela'):
        convert.pdf_to_excel([make_pdf(1)], tmp_path / 't.xlsx')


def test_compare(make_pdf, tmp_path):
    a, b = make_pdf(2, 'Igual'), make_pdf(2, 'Diferente')
    out = tmp_path / 'cmp.html'
    convert.compare_pdfs([a, b], out)
    assert '2 página(s) com diferenças' in out.read_text(encoding='utf-8')
    convert.compare_pdfs([a, a], out)
    assert 'Nenhuma diferença' in out.read_text(encoding='utf-8')
    with pytest.raises(ValueError):
        convert.compare_pdfs([a], out)


def test_grayscale(make_pdf, tmp_path):
    out = tmp_path / 'g.pdf'
    convert.grayscale_pdf([make_pdf(2)], out, dpi=40)
    with pymupdf.open(out) as doc:
        assert doc.page_count == 2


def test_crop_margins(make_pdf, tmp_path):
    out = tmp_path / 'c.pdf'
    convert.crop_margins([make_pdf(1)], out)
    with pymupdf.open(out) as doc:
        assert doc[0].cropbox.width < doc[0].mediabox.width


@pytest.mark.parametrize('name,content,expected', [
    ('a.md', '# Título\n\n| a | b |\n|---|---|\n| 1 | 2 |\n', 'Título'),
    ('a.html', '<h1>Olá</h1><p>mundo</p>', 'Olá'),
    ('a.txt', 'linha <com> sinais & etc', 'linha <com> sinais & etc'),
])
def test_web_to_pdf(tmp_path, name, content, expected):
    src = tmp_path / name
    src.write_text(content, encoding='utf-8')
    out = tmp_path / 'web.pdf'
    convert.web_to_pdf([src], out)
    with pymupdf.open(out) as doc:
        assert expected in doc[0].get_text()


def test_svg_to_pdf(tmp_path):
    svg = tmp_path / 'a.svg'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">'
                   '<rect width="100" height="50" fill="red"/></svg>', encoding='utf-8')
    out = tmp_path / 's.pdf'
    convert.ebook_to_pdf([svg], out)
    with pymupdf.open(out) as doc:
        assert doc.page_count == 1


@pytest.mark.parametrize('fmt', list(convert.IMAGE_FORMATS))
def test_convert_images(make_img, out_dir, fmt):
    files = convert.convert_images([make_img()], out_dir, fmt=fmt)
    with Image.open(files[0]) as img:
        assert img.format == convert.IMAGE_FORMATS[fmt][1]


def test_resize_and_compress(make_img, out_dir):
    src = make_img('JPEG', size=(400, 200))
    resized = convert.resize_images([src], out_dir, percent=25)[0]
    with Image.open(resized) as img:
        assert img.size == (100, 50)
    with pytest.raises(ValueError):
        convert.resize_images([src], out_dir, percent=0)
    small = convert.compress_images([make_img('PNG', size=(300, 300))], out_dir)[0]
    assert small.exists()


def test_gif_roundtrip(make_img, tmp_path, out_dir):
    gif = tmp_path / 'anim.gif'
    convert.images_to_gif([make_img(color=(255, 0, 0)), make_img(color=(0, 255, 0), size=(40, 40))],
                          gif, frame_ms=200)
    frames = convert.gif_to_frames([gif], out_dir)
    assert len(frames) == 2


def test_unique_never_overwrites(tmp_path):
    (tmp_path / 'a.png').write_bytes(b'x')
    assert convert.unique(tmp_path / 'a.png').name == 'a (2).png'


office_marks = {
    'excel': pytest.mark.skipif(not office.is_available(office.EXCEL), reason='sem Excel'),
    'ppt': pytest.mark.skipif(not office.is_available(office.POWERPOINT), reason='sem PowerPoint'),
}


@office_marks['excel']
def test_excel_to_pdf(tmp_path):
    csv = tmp_path / 'dados.csv'
    csv.write_text('Nome;Valor\nAna;10\n', encoding='utf-8')
    out = tmp_path / 'x.pdf'
    convert.excel_to_pdf([csv], out)
    with pymupdf.open(out) as doc:
        assert 'Ana' in doc[0].get_text()
    assert not office.pids(office.EXCEL)


@office_marks['ppt']
def test_pdf_to_powerpoint_and_back(make_pdf, tmp_path):
    pptx = tmp_path / 'p.pptx'
    convert.pdf_to_powerpoint([make_pdf(2)], pptx, dpi=40)
    assert pptx.exists()
    out = tmp_path / 'p.pdf'
    convert.powerpoint_to_pdf([pptx], out)
    with pymupdf.open(out) as doc:
        assert doc.page_count == 2
    assert not office.pids(office.POWERPOINT)
