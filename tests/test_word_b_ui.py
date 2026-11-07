"""Word B no hub: blocos, camada de compatíveis, parâmetros de texto e execução."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from pathlib import Path  # noqa: E402

import docx  # noqa: E402
import pytest  # noqa: E402
from PySide6.QtWidgets import QComboBox, QFileDialog, QLineEdit  # noqa: E402

from core.workspace import Workspace  # noqa: E402
from tests.test_hub import drop, ids  # noqa: E402
from ui import dialogs  # noqa: E402
from ui.main_window import MainWindow, resolve_fn  # noqa: E402
from ui.tools import BY_ID, GROUPS, Param, compatible  # noqa: E402

WORD_B = {'docxclean', 'docxreplace', 'docxmerge', 'docx2text'}


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch):
    erros = []
    monkeypatch.setattr(dialogs, 'error', lambda *a: erros.append(a))
    monkeypatch.setattr(dialogs, 'info', lambda *_: None)
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False)
    w.erros = erros
    qtbot.addWidget(w)
    w.show()
    return w


@pytest.fixture
def make_docx(tmp_path):
    n = {'i': 0}

    def _make(texto='A Contratante pagará até o dia 5.') -> Path:
        n['i'] += 1
        d = docx.Document()
        d.core_properties.author = 'Maria Souza'
        d.add_paragraph(texto)
        f = tmp_path / f'contrato{n["i"]}.docx'
        d.save(f)
        return f
    return _make


def test_grupo_word_no_hub(window):
    assert 'Word' in GROUPS
    cards = {c.tool.id: c for c in window.hub.cards}
    assert WORD_B <= set(cards)
    assert all(not cards[i].property('disabled') for i in WORD_B)  # não precisam do Office


def test_compativeis_com_docx(make_docx):
    um = ids(compatible([make_docx()]))
    assert {'docxclean', 'docxreplace', 'docx2text'} <= um and 'docxmerge' not in um
    assert 'docxmerge' in ids(compatible([make_docx(), make_docx()]))


def test_soltar_docx_mostra_blocos_word(window, make_docx):
    drop(window.hub, [make_docx()])
    assert window.layer.isVisible()
    assert {'docxclean', 'docxreplace'} <= {c.tool.id for c in window.layer.cards}


def test_fn_qualificada():
    from core import docx_tools
    assert resolve_fn('docx_tools.clean') is docx_tools.clean
    for i in WORD_B:
        assert callable(resolve_fn(BY_ID[i].fn))


def test_param_texto_e_opcoes(qtbot):
    params = (Param('find', 'Localizar', ''), Param('match_case', 'Diferenciar maiúsculas', 'Sim',
                                                     options=('Sim', 'Não')))
    dlg = dialogs.ParamDialog(None, 'Localizar e substituir', params)
    qtbot.addWidget(dlg)
    assert isinstance(dlg.fields['find'], QLineEdit)
    assert isinstance(dlg.fields['match_case'], QComboBox)
    dlg.fields['find'].setText('Contratante')
    assert dlg.values() == {'find': 'Contratante', 'match_case': 'Sim'}


def test_limpar_pelo_hub(window, qtbot, make_docx, tmp_path, monkeypatch):
    src = make_docx()
    out = tmp_path / 'saida'
    out.mkdir()
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *a, **k: str(out))
    window.run_tool('docxclean', [src])
    alvo = out / 'contrato1_limpo.docx'
    qtbot.waitUntil(lambda: alvo.exists() and not window.is_busy(), timeout=10000)
    assert docx.Document(alvo).core_properties.author == ''


def test_substituir_pelo_hub(window, qtbot, make_docx, tmp_path, monkeypatch):
    src = make_docx()
    out = tmp_path / 'saida'
    out.mkdir()
    monkeypatch.setattr(dialogs.ParamDialog, 'ask', classmethod(
        lambda cls, *a: {'find': 'Contratante', 'replace': 'Locatária', 'match_case': 'Sim'}))
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *a, **k: str(out))
    window.run_tool('docxreplace', [src])
    alvo = out / 'contrato1_substituido.docx'
    qtbot.waitUntil(lambda: alvo.exists() and not window.is_busy(), timeout=10000)
    assert docx.Document(alvo).paragraphs[0].text == 'A Locatária pagará até o dia 5.'


def test_substituir_sem_texto_mostra_erro(window, qtbot, make_docx, tmp_path, monkeypatch):
    monkeypatch.setattr(dialogs.ParamDialog, 'ask', classmethod(
        lambda cls, *a: {'find': '', 'replace': 'x', 'match_case': 'Sim'}))
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *a, **k: str(tmp_path))
    window.run_tool('docxreplace', [make_docx()])
    qtbot.waitUntil(lambda: bool(window.erros) and not window.is_busy(), timeout=10000)
    assert 'localizar' in window.erros[0][2].lower()


def test_juntar_nao_sobrescreve_original(window, qtbot, make_docx, monkeypatch):
    a, b = make_docx('Parte 1'), make_docx('Parte 2')
    antes = a.read_bytes()
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a_, **k: (str(a), ''))
    window.run_tool('docxmerge', [a, b])
    assert window.erros and 'original' in window.erros[0][2]
    assert a.read_bytes() == antes


def test_juntar_nome_padrao(window, qtbot, make_docx, tmp_path, monkeypatch):
    a, b = make_docx('Parte 1'), make_docx('Parte 2')
    sugestao = []

    def save(parent, title, default, flt):
        sugestao.append(default)
        return str(tmp_path / 'juntado.docx'), ''
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', save)
    window.run_tool('docxmerge', [a, b])
    qtbot.waitUntil(lambda: (tmp_path / 'juntado.docx').exists() and not window.is_busy(),
                    timeout=10000)
    assert sugestao == ['contrato1_juntado.docx']
    texto = [p.text for p in docx.Document(tmp_path / 'juntado.docx').paragraphs]
    assert texto.index('Parte 1') < texto.index('Parte 2')
