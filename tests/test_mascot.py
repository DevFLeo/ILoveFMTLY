import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import sys  # noqa: E402
import time  # noqa: E402

import pytest  # noqa: E402

from core import mascot  # noqa: E402
from core.settings import Settings  # noqa: E402


def test_every_mascot_has_files():
    for name in mascot.MASCOTS:
        assert mascot.icon_file(name).is_file() and mascot.image_file(name).is_file()
    assert mascot.valid('dragao') == 'folha'


def test_persistent_icon_copies_only_on_change(tmp_path):
    a = mascot.persistent_icon('raposa', tmp_path)
    first = a.stat().st_mtime_ns
    time.sleep(0.01)
    assert mascot.persistent_icon('raposa', tmp_path).stat().st_mtime_ns == first   # igual: não copia
    mascot.persistent_icon('coruja', tmp_path)
    assert a.read_bytes() == mascot.icon_file('coruja').read_bytes()


@pytest.mark.skipif(sys.platform != 'win32', reason='atalhos .lnk são do Windows')
def test_update_shortcuts(tmp_path):
    import pythoncom
    import win32com.client
    lnk = tmp_path / "Usuário d'Ana" / 'ILoveFMTLY.lnk'  # aspas e acento no caminho
    lnk.parent.mkdir()
    pythoncom.CoInitialize()
    sc = win32com.client.Dispatch('WScript.Shell').CreateShortcut(str(lnk))
    sc.TargetPath = sys.executable
    sc.Save()
    icon = mascot.persistent_icon('castor', tmp_path)
    assert mascot.update_shortcuts(icon, [lnk, tmp_path / 'nao-existe.lnk']) == 1
    again = win32com.client.Dispatch('WScript.Shell').CreateShortcut(str(lnk))
    assert again.IconLocation.lower() == f'{icon},0'.lower()
    assert mascot.update_shortcuts(icon, [lnk]) == 0  # já estava certo


def test_notifier_only_when_slow_and_away(qtbot):
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QWidget

    from ui.mascot_ui import TaskNotifier
    w = QWidget()
    qtbot.addWidget(w)
    n = TaskNotifier(w, QIcon(str(mascot.icon_file('folha'))))
    start = n.start()
    assert not n.finished('Comprimir PDF', start)            # rápido: não avisa
    assert n.finished('Comprimir PDF', start, limit=0)       # janela não está ativa: avisa
    assert n.last[1].startswith('Comprimir PDF terminou')
    n.finished('Exportar', start, RuntimeError('x' * 500), limit=0)
    assert n.last[1].endswith('…') and len(n.last[1]) < 220


def test_mascot_from_settings_dialog(qtbot, tmp_path, monkeypatch):
    from core.workspace import Workspace
    from ui import hub
    from ui.main_window import MainWindow
    from ui.profile_dialog import SettingsDialog
    s = Settings(layout='blocks')
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False, settings=s)
    qtbot.addWidget(w)

    def fake_exec(dialog):
        dialog.mascot.setCurrentIndex(dialog.mascot.findData('tartaruga'))
        dialog.accept()
        return SettingsDialog.Accepted
    monkeypatch.setattr(SettingsDialog, 'exec', fake_exec)
    w.open_settings()
    assert s.mascot == 'tartaruga'
    assert hub.LOGO['path'] == mascot.image_file('tartaruga')
    assert not w.windowIcon().isNull()
