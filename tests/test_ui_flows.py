"""Fluxos completos da interface, com os diálogos substituídos por respostas fixas."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import pikepdf  # noqa: E402
import pymupdf  # noqa: E402
import pytest  # noqa: E402
import warnings  # noqa: E402

from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl  # noqa: E402
from PySide6.QtGui import QDragEnterEvent, QDropEvent  # noqa: E402
from PySide6.QtPrintSupport import QPrinter  # noqa: E402
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog  # noqa: E402

from core.engines import qpdf  # noqa: E402
from core.workspace import Workspace  # noqa: E402
from ui import dialogs  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch):
    errors = []
    monkeypatch.setattr(dialogs, 'error', lambda _p, title, msg: errors.append((title, msg)))
    monkeypatch.setattr(dialogs, 'info', lambda *_: None)
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=tmp_path / 'spool')
    w.errors = errors
    qtbot.addWidget(w)
    return w


def drop_files(widget, paths):
    """Simula o arrasto do Explorer: DragEnter (aceito) e depois Drop."""
    widget.window().show()
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(p)) for p in paths])
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        enter = QDragEnterEvent(QPoint(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(widget, enter)
    assert enter.isAccepted()
    drop = QDropEvent(QPointF(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(widget, drop)


def test_drop_files_on_grid(window, make_pdf, make_png):
    drop_files(window.grid.viewport(), [make_pdf(2), make_png()])
    assert len(window.doc) == 3


def test_drop_files_on_window(window, make_pdf):
    drop_files(window, [make_pdf(4)])
    assert len(window.doc) == 4


def test_merge_two_files(window, make_pdf):
    window.add_files([make_pdf(2, 'A'), make_pdf(3, 'B')])
    assert len(window.doc) == 5
    assert len({p.source for p in window.doc.pages}) == 2


def test_password_prompt(window, make_pdf, monkeypatch):
    src = make_pdf(2)
    qpdf.protect(src, 'certa')
    answers = iter(['errada', 'certa'])
    asked = []

    def fake_ask(_parent, name, retry):
        asked.append(retry)
        return next(answers)

    monkeypatch.setattr(dialogs, 'ask_password', fake_ask)
    assert window.add_files([src]) == 1
    assert asked == [False, True]
    assert len(window.doc) == 2


def test_password_cancel(window, make_pdf, monkeypatch):
    src = make_pdf(1)
    qpdf.protect(src, 'x')
    monkeypatch.setattr(dialogs, 'ask_password', lambda *_: None)
    assert window.add_files([src]) == 0
    assert len(window.doc) == 0


def test_garbage_file_shows_error(window, tmp_path):
    bad = tmp_path / 'ruim.pdf'
    bad.write_bytes(b'lixo')
    assert window.add_files([bad]) == 0
    assert window.errors and window.errors[0][0] == 'Não foi possível importar'


def test_export_with_options(window, qtbot, make_pdf, tmp_path, monkeypatch):
    out = tmp_path / 'final.pdf'
    window.add_files([make_pdf(3)])
    window.options.page_numbers.setChecked(True)
    window.options.watermark.setText('SIGILOSO')
    window.options.password.setText('abc')
    window.options.password2.setText('abc')
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(out), ''))
    window.export_dialog()
    qtbot.waitUntil(lambda: out.exists() and window.toolbar.isEnabled(), timeout=10000)
    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(out)
    with pymupdf.open(out) as pdf:
        assert pdf.authenticate('abc')
        assert '1 / 3' in pdf[0].get_text()
    assert not window.errors


def test_export_password_mismatch(window, make_pdf, monkeypatch):
    window.add_files([make_pdf(1)])
    window.options.password.setText('a')
    window.options.password2.setText('b')
    called = []
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: called.append(1) or ('', ''))
    window.export_dialog()
    assert not called
    assert window.errors[0][1] == 'As senhas não conferem.'


def test_extract_selected(window, qtbot, make_pdf, tmp_path, monkeypatch):
    out = tmp_path / 'sel.pdf'
    window.add_files([make_pdf(4)])
    window.grid.clearSelection()
    window.grid.item(1).setSelected(True)
    window.grid.item(3).setSelected(True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(out), ''))
    window.extract_dialog()
    qtbot.waitUntil(lambda: out.exists() and window.toolbar.isEnabled(), timeout=10000)
    with pymupdf.open(out) as pdf:
        assert pdf.page_count == 2
        assert 'Página 2' in pdf[0].get_text()
        assert 'Página 4' in pdf[1].get_text()


def test_split(window, qtbot, make_pdf, tmp_path, monkeypatch):
    out_dir = tmp_path / 'partes'
    out_dir.mkdir()
    window.add_files([make_pdf(5)])
    monkeypatch.setattr(QInputDialog, 'getText', lambda *a, **k: ('1-2, 3-5', True))
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *a, **k: str(out_dir))
    window.split_dialog()
    qtbot.waitUntil(lambda: len(list(out_dir.glob('*.pdf'))) == 2 and window.toolbar.isEnabled(),
                    timeout=10000)
    counts = sorted(pymupdf.open(p).page_count for p in out_dir.glob('*.pdf'))
    assert counts == [2, 3]


def test_split_invalid_range(window, make_pdf, monkeypatch):
    window.add_files([make_pdf(3)])
    monkeypatch.setattr(QInputDialog, 'getText', lambda *a, **k: ('5-2', True))
    window.split_dialog()
    assert window.errors[0][0] == 'Intervalo inválido'


def test_print_to_pdf_printer(window, make_pdf, tmp_path):
    """Impressão real pelo QPrinter, gravando num PDF em vez de papel."""
    window.add_files([make_pdf(3)])
    window.grid.clearSelection()
    window.grid.item(0).setSelected(True)
    window.rotate(90)
    target = tmp_path / 'impresso.pdf'
    qprinter = QPrinter(QPrinter.HighResolution)
    qprinter.setOutputFormat(QPrinter.PdfFormat)
    qprinter.setOutputFileName(str(target))
    window.print_to(qprinter)
    with pymupdf.open(target) as pdf:
        assert pdf.page_count == 3
    assert not window.errors
    assert not list(window.ws.path.glob('impressao*.pdf'))  # temporário apagado


def test_app_starts_offline():
    """Sobe o app.py de verdade e confirma que ele fica de pé."""
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    proc = subprocess.Popen([sys.executable, 'app.py'], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        time.sleep(3)
        assert proc.poll() is None, proc.stderr.read()
    finally:
        proc.kill()
        proc.wait()
