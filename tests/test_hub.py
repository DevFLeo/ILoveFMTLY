import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl  # noqa: E402
from PySide6.QtGui import QDragEnterEvent, QDropEvent  # noqa: E402
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog  # noqa: E402

from core.engines import word  # noqa: E402
from core.workspace import Workspace  # noqa: E402
from ui import dialogs  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.tools import TOOLS, compatible  # noqa: E402


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch):
    monkeypatch.setattr(dialogs, 'error', lambda *_: pytest.fail(f'erro inesperado: {_}'))
    monkeypatch.setattr(dialogs, 'info', lambda *_: None)
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=word.is_available())
    qtbot.addWidget(w)
    w.show()
    return w


def drop(widget, paths):
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(p)) for p in paths])
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        enter = QDragEnterEvent(QPoint(20, 20), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(widget, enter)
    QApplication.sendEvent(widget, QDropEvent(QPointF(20, 20), Qt.CopyAction, mime,
                                              Qt.LeftButton, Qt.NoModifier))


def ids(tools):
    return {t.id for t in tools}


def test_compatible_by_format():
    assert {'word2pdf'} == ids(compatible([Path('a.docx')]))
    pdf = ids(compatible([Path('a.pdf')]))
    assert {'merge', 'split', 'numbers', 'pdf2word', 'protect'} <= pdf
    assert 'word2pdf' not in pdf and 'sign' not in pdf  # "em breve" nunca aparece
    assert ids(compatible([Path('a.pdf'), Path('b.png')])) == {'merge', 'organize'}
    assert ids(compatible([Path('a.pdf'), Path('b.docx')])) == set()
    assert ids(compatible([Path('a.xyz')])) == set()


def test_hub_starts_with_all_cards(window):
    assert window.on_hub()
    assert not window.toolbar.isVisible()
    assert len(window.hub.cards) == len(TOOLS)
    soon = [c for c in window.hub.cards if c.tool.soon]
    assert soon and all(c.property('disabled') for c in soon)


def test_drop_on_hub_opens_layer(window, make_pdf):
    drop(window, [make_pdf(2)])
    assert window.layer.isVisible()
    assert 'numbers' in {c.tool.id for c in window.layer.cards}
    assert len(window.doc) == 0  # ainda não importou: só mostrou as opções


def test_drop_unknown_format_shows_message(window, tmp_path):
    f = tmp_path / 'x.xyz'
    f.write_text('x')
    drop(window, [f])
    assert window.layer.isVisible()
    assert window.layer.cards == []
    assert 'Nenhuma ferramenta' in window.layer.hint.text()


def test_layer_card_runs_tool(window, make_pdf):
    drop(window, [make_pdf(3)])
    card = next(c for c in window.layer.cards if c.tool.id == 'numbers')
    card.clicked.emit(card.tool.id)
    assert not window.layer.isVisible()
    assert not window.on_hub()
    assert window.toolbar.isVisible()
    assert len(window.doc) == 3
    assert window.options.page_numbers.isChecked()
    assert 'Numeração' in window.hint_bar.text()


def test_tools_start_fresh_document(window, make_pdf):
    window.run_tool('merge', [make_pdf(2), make_pdf(3)])
    assert len(window.doc) == 5
    window.show_hub()
    window.run_tool('protect', [make_pdf(1)])
    assert len(window.doc) == 1
    assert not window.history.can_undo() or len(window.doc) == 1


def test_rotate_tool_selects_all(window, make_pdf):
    window.run_tool('rotate', [make_pdf(3)])
    assert window.grid.selected_rows() == [0, 1, 2]


def test_compress_tool_preset(window, make_pdf):
    window.run_tool('compress', [make_pdf(1)])
    assert window.options.compress.currentData() == 'lossy'


def test_card_click_opens_file_picker(window, make_pdf, monkeypatch):
    pdf = make_pdf(2)
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **k: (str(pdf), ''))
    window.run_tool('extract')
    assert len(window.doc) == 2


def test_soon_card_does_nothing(window):
    window.run_tool('sign')
    assert window.on_hub()


def test_pdf2img(window, qtbot, make_pdf, tmp_path, monkeypatch):
    out = tmp_path / 'imgs'
    out.mkdir()
    monkeypatch.setattr(dialogs.ParamDialog, 'ask', classmethod(lambda cls, *a: {'fmt': 'PNG', 'dpi': 40}))
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *a, **k: str(out))
    window.run_tool('pdf2img', [make_pdf(3)])
    qtbot.waitUntil(lambda: len(list(out.glob('*.png'))) == 3 and not window.is_busy(), timeout=10000)


def test_split_tool_opens_dialog(window, qtbot, make_pdf, tmp_path, monkeypatch):
    out = tmp_path / 'partes'
    out.mkdir()
    monkeypatch.setattr(QInputDialog, 'getText', lambda *a, **k: ('1, 2', True))
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *a, **k: str(out))
    window.run_tool('split', [make_pdf(2)])
    qtbot.waitUntil(lambda: len(list(out.glob('*.pdf'))) == 2 and not window.is_busy(), timeout=10000)


def test_back_to_hub(window, make_pdf):
    window.run_tool('organize', [make_pdf(1)])
    window.act_home.trigger()
    assert window.on_hub()
    assert not window.toolbar.isVisible()


def test_word_disabled_without_word(qtbot, tmp_path):
    w = MainWindow(Workspace(tmp_path / 'ws2'), spool_dir=None, word_ok=False)
    qtbot.addWidget(w)
    card = next(c for c in w.hub.cards if c.tool.id == 'word2pdf')
    assert card.property('disabled')
    assert 'Requer Microsoft Office' in card.toolTip()
    w.run_tool('word2pdf', [tmp_path / 'a.docx'])
    assert w.on_hub()


@pytest.mark.skipif(not word.is_available(), reason='Microsoft Word não instalado')
def test_word2pdf_and_pdf2word(window, qtbot, tmp_path, make_pdf, monkeypatch):
    import pythoncom
    import win32com.client

    docx = tmp_path / 'contrato.docx'
    pythoncom.CoInitialize()
    app = win32com.client.DispatchEx('Word.Application')
    try:
        app.Visible = False
        d = app.Documents.Add()
        d.Content.Text = 'Contrato sigiloso'
        d.SaveAs2(str(docx), FileFormat=16)
        d.Close(0)
    finally:
        app.Quit(0)

    window.run_tool('word2pdf', [docx])
    qtbot.waitUntil(lambda: len(window.doc) >= 1 and not window.is_busy(), timeout=60000)
    assert not window.on_hub()

    out = tmp_path / 'volta.docx'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(out), ''))
    window.show_hub()
    window.run_tool('pdf2word', [make_pdf(1)])
    qtbot.waitUntil(lambda: out.exists() and not window.is_busy(), timeout=60000)


def test_param_cancel_does_nothing(window, make_pdf, monkeypatch):
    monkeypatch.setattr(dialogs.ParamDialog, 'ask', classmethod(lambda cls, *a: None))
    called = []
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: called.append(1) or ('', ''))
    window.run_tool('pdf2gif', [make_pdf(2)])
    assert not called and window.on_hub()


def test_file_mode_pdf2gif_adds_extension(window, qtbot, make_pdf, tmp_path, monkeypatch):
    target = tmp_path / 'animacao'  # usuário não digitou a extensão
    monkeypatch.setattr(dialogs.ParamDialog, 'ask',
                        classmethod(lambda cls, *a: {'dpi': 30, 'frame_ms': 200}))
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(target), ''))
    window.run_tool('pdf2gif', [make_pdf(3)])
    gif = tmp_path / 'animacao.gif'
    qtbot.waitUntil(lambda: gif.exists() and not window.is_busy(), timeout=10000)


def test_folder_mode_image_convert(window, qtbot, make_png, tmp_path, monkeypatch):
    out = tmp_path / 'conv'
    out.mkdir()
    monkeypatch.setattr(dialogs.ParamDialog, 'ask',
                        classmethod(lambda cls, *a: {'fmt': 'WebP', 'quality': 80}))
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *a, **k: str(out))
    window.run_tool('imgconvert', [make_png()])
    qtbot.waitUntil(lambda: bool(list(out.glob('*.webp'))) and not window.is_busy(), timeout=10000)


def test_to_editor_mode_markdown(window, qtbot, tmp_path):
    md = tmp_path / 'nota.md'
    md.write_text('# Nota\n\nTexto sigiloso.', encoding='utf-8')
    window.run_tool('web2pdf', [md])
    qtbot.waitUntil(lambda: len(window.doc) >= 1 and not window.is_busy(), timeout=10000)
    assert not window.on_hub()


def test_compare_needs_two_files(window, make_pdf, monkeypatch):
    errors = []
    monkeypatch.setattr(dialogs, 'error', lambda _p, title, msg: errors.append(msg))
    window.run_tool('compare', [make_pdf(1)])
    assert errors and 'exatamente 2' in errors[0]


def test_layer_for_gif_and_markdown():
    assert {'gif2frames', 'imgconvert', 'imgresize'} <= ids(compatible([Path('a.gif')]))
    assert 'web2pdf' in ids(compatible([Path('a.md')]))
    assert 'compare' in ids(compatible([Path('a.pdf'), Path('b.pdf')]))
    assert 'compare' not in ids(compatible([Path('a.pdf')]))
    assert 'img2gif' in ids(compatible([Path('a.png'), Path('b.jpg')]))
