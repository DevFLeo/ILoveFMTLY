"""Aplica o mascote (janela, barra de tarefas, bandeja, atalhos) e avisa pela bandeja
quando uma tarefa demorada termina.

Melhorias sobre a primeira versão do aviso:
- só avisa se a pessoa não está olhando (janela minimizada ou sem foco): com a janela
  na frente, o diálogo "Pronto" já basta;
- o ícone da bandeja aparece só enquanto há aviso, e some depois;
- o texto do erro é cortado para caber no balão do Windows.
"""

import time

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QWidget

from core import mascot

SLOW_SECONDS = 10.0
BALLOON_MS = 8000
MAX_ERROR = 180


def apply_mascot(name: str, window: QWidget | None = None, tray: QSystemTrayIcon | None = None,
                 shortcuts: bool = True) -> QIcon:
    """Troca o ícone em tudo. `shortcuts=False` nos testes (não mexe no Windows)."""
    path = mascot.icon_file(name)
    if shortcuts:
        try:
            path = mascot.persistent_icon(name)
            mascot.update_shortcuts(path)
        except OSError:
            path = mascot.icon_file(name)  # sem LOCALAPPDATA gravável: vale só para a janela
    icon = QIcon(str(path))
    app = QApplication.instance()
    if app is not None:
        app.setWindowIcon(icon)
    if window is not None:
        window.setWindowIcon(icon)
    if tray is not None:
        tray.setIcon(icon)
    return icon


class TaskNotifier:
    """Mede tarefas e avisa na bandeja quando uma demorada termina longe dos olhos."""

    def __init__(self, window: QWidget, icon: QIcon):
        self.window = window
        self.tray = QSystemTrayIcon(icon, window)
        self.tray.setToolTip('ILoveFMTLY')
        self.tray.messageClicked.connect(self._bring_back)
        self.last: tuple[str, str] | None = None   # (título, texto) do último aviso, para testes

    def start(self) -> float:
        return time.monotonic()

    def _away(self) -> bool:
        return self.window.isMinimized() or not self.window.isActiveWindow()

    def finished(self, task: str, started: float, error: Exception | None = None,
                 limit: float = SLOW_SECONDS) -> bool:
        """Chame na thread da interface quando a tarefa acabar. Devolve se avisou."""
        took = time.monotonic() - started
        if took < limit or not self._away():
            return False
        if error is None:
            text = f'{task} terminou em {took:.0f} s.'
            kind = QSystemTrayIcon.MessageIcon.Information
        else:
            msg = str(error)
            text = f'{task} falhou: {msg[:MAX_ERROR]}{"…" if len(msg) > MAX_ERROR else ""}'
            kind = QSystemTrayIcon.MessageIcon.Warning
        self.last = ('ILoveFMTLY', text)
        if QSystemTrayIcon.isSystemTrayAvailable() and QSystemTrayIcon.supportsMessages():
            self.tray.show()
            self.tray.showMessage('ILoveFMTLY', text, kind, BALLOON_MS)
            QTimer.singleShot(BALLOON_MS + 2000, self.tray.hide)
        return True

    def _bring_back(self):
        self.window.showNormal()
        self.window.raise_()
        self.window.activateWindow()
