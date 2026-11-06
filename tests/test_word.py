"""Testes reais com o Microsoft Word (pulam quando ele não está instalado)."""

import winreg

import pymupdf
import pytest

from core.engines import word

pytestmark = pytest.mark.skipif(not word.is_available(), reason='Microsoft Word não instalado')


@pytest.fixture
def make_docx(tmp_path):
    def _make(text='Contrato sigiloso'):
        import pythoncom
        import win32com.client

        out = tmp_path / 'doc.docx'
        pythoncom.CoInitialize()
        app = win32com.client.DispatchEx('Word.Application')
        try:
            app.Visible = False
            doc = app.Documents.Add()
            doc.Content.Text = text
            doc.SaveAs2(str(out), FileFormat=16)
            doc.Close(0)
        finally:
            app.Quit(0)
            pythoncom.CoUninitialize()
        return out

    return _make


def _reg_value():
    path = rf'Software\Microsoft\Office\{word.word_version()}\Word\Options'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            return winreg.QueryValueEx(key, 'DisableConvertPdfWarning')
    except FileNotFoundError:
        return None


def test_docx_to_pdf_and_back(make_docx, tmp_path):
    before = _reg_value()
    pdf = word.to_pdf(make_docx('Contrato sigiloso 123'), tmp_path / 'doc.pdf')
    with pymupdf.open(pdf) as doc:
        assert 'Contrato sigiloso 123' in doc[0].get_text()
        assert not doc.metadata.get('author')  # propriedades não exportadas

    back = word.pdf_to_docx(pdf, tmp_path / 'volta.docx')
    assert back.exists() and back.stat().st_size > 0
    assert _reg_value() == before  # configuração do usuário restaurada
    assert not (word._word_pids())  # nenhuma instância do Word sobrou


def test_timeout_kills_only_our_word(make_docx, tmp_path):
    src = make_docx()
    with pytest.raises((word.WordTimeout, word.WordError)):
        word.to_pdf(src, tmp_path / 'x.pdf', timeout=0.01)
    assert not word._word_pids()


def test_missing_file_raises_word_error(tmp_path):
    with pytest.raises(word.WordError):
        word.to_pdf(tmp_path / 'nao_existe.docx', tmp_path / 'x.pdf')
