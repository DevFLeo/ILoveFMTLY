import io

import pymupdf
import pytest
from PIL import Image

from core import pdf_tools


def _pdf(tmp_path, lines, name='in.pdf'):
    out = tmp_path / name
    doc = pymupdf.open()
    page = doc.new_page()
    for i, line in enumerate(lines):
        page.insert_text((72, 72 + 20 * i), line)
    doc.save(out)
    doc.close()
    return out


def _text(path):
    with pymupdf.open(path) as doc:
        return ''.join(p.get_text() for p in doc)


# --- tarja ------------------------------------------------------------------
def test_redact_removes_terms_for_real(tmp_path):
    src = _pdf(tmp_path, ['Contrato de Maria Souza', 'Valor: 1000'])
    out = tmp_path / 'out.pdf'
    pdf_tools.redact([src], out, terms='Maria Souza; 1000')
    text = _text(out)
    assert 'Maria' not in text and '1000' not in text and 'Contrato' in text


def test_redact_patterns(tmp_path):
    src = _pdf(tmp_path, ['CPF 123.456.789-09', 'mail ana@exemplo.com.br', 'fone (11) 98765-4321'])
    out = tmp_path / 'out.pdf'
    pdf_tools.redact([src], out, docs='Sim', contacts='Sim')
    text = _text(out)
    assert '123.456' not in text and 'ana@' not in text and '98765' not in text


def test_redact_nothing_found_or_asked(tmp_path):
    src = _pdf(tmp_path, ['nada aqui'])
    with pytest.raises(ValueError, match='Nada encontrado'):
        pdf_tools.redact([src], tmp_path / 'o.pdf', terms='xyz')
    with pytest.raises(ValueError, match='Diga o que tarjar'):
        pdf_tools.redact([src], tmp_path / 'o.pdf')


# --- assinatura -------------------------------------------------------------
def _png(w=200, h=80) -> bytes:
    buf = io.BytesIO()
    Image.new('RGBA', (w, h), (0, 0, 0, 255)).save(buf, 'PNG')
    return buf.getvalue()


def test_sign_last_page_bottom_right(tmp_path, make_pdf):
    src = make_pdf(3)
    out = tmp_path / 'assinado.pdf'
    pdf_tools.sign_pdf(src, out, _png(), page=0, position='Inferior direito', width=30)
    with pymupdf.open(out) as doc:
        assert [len(p.get_images()) for p in doc] == [0, 0, 1]
        rect = doc[2].get_image_rects(doc[2].get_images()[0][0])[0]
        page = doc[2].rect
        assert rect.x1 == pytest.approx(page.width - pdf_tools.MARGIN, abs=1)
        assert rect.y1 == pytest.approx(page.height - pdf_tools.MARGIN, abs=1)
        assert rect.width == pytest.approx(page.width * 0.3, abs=1)


def test_sign_bad_page(tmp_path, make_pdf):
    with pytest.raises(ValueError, match='não existe'):
        pdf_tools.sign_pdf(make_pdf(1), tmp_path / 'o.pdf', _png(), page=5)


# --- formulários ------------------------------------------------------------
def _form(tmp_path):
    out = tmp_path / 'form.pdf'
    doc = pymupdf.open()
    page = doc.new_page()
    specs = [('nome', pymupdf.PDF_WIDGET_TYPE_TEXT, (72, 72, 300, 92)),
             ('aceito', pymupdf.PDF_WIDGET_TYPE_CHECKBOX, (72, 110, 90, 128)),
             ('cidade', pymupdf.PDF_WIDGET_TYPE_COMBOBOX, (72, 140, 300, 160))]
    for name, kind, rect in specs:
        w = pymupdf.Widget()
        w.field_name, w.field_type, w.rect = name, kind, pymupdf.Rect(rect)
        if kind == pymupdf.PDF_WIDGET_TYPE_COMBOBOX:
            w.choice_values = ['Recife', 'Natal']
            w.field_value = 'Recife'
        page.add_widget(w)
    doc.save(out)
    doc.close()
    return out


def test_read_and_fill_form(tmp_path):
    src = _form(tmp_path)
    fields = {f.name: f for f in pdf_tools.read_fields(src)}
    assert fields['nome'].kind == 'text'
    assert fields['aceito'].kind == 'check' and fields['aceito'].value is False
    assert fields['cidade'].options == ['Recife', 'Natal']
    out = tmp_path / 'preenchido.pdf'
    pdf_tools.fill_form(src, out, {'nome': 'Ana Lima', 'aceito': True, 'cidade': 'Natal'})
    filled = {f.name: f.value for f in pdf_tools.read_fields(out)}
    assert filled == {'nome': 'Ana Lima', 'aceito': True, 'cidade': 'Natal'}


def test_flatten_removes_fields(tmp_path):
    src = _form(tmp_path)
    out = tmp_path / 'fixo.pdf'
    pdf_tools.fill_form(src, out, {'nome': 'Ana Lima'}, flatten=True)
    assert 'Ana Lima' in _text(out)
    with pytest.raises(ValueError, match='não tem campos'):
        pdf_tools.read_fields(out)


def test_pdf_without_fields(make_pdf):
    with pytest.raises(ValueError, match='não tem campos'):
        pdf_tools.read_fields(make_pdf(1))
