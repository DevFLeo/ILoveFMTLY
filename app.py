"""Ponto de entrada do ILoveFMTLY.

O bloqueio de rede vem antes de qualquer outra coisa: a partir daqui nenhum
código do app consegue abrir conexão.
"""

from core import offline

offline.enable()

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from core import mascot  # noqa: E402
from core.settings import Settings  # noqa: E402
from core.workspace import Workspace  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.style import apply_style  # noqa: E402
from ui.theme import ASSETS, apply_appearance  # noqa: E402


def main() -> int:
    mascot.set_app_id()  # antes da primeira janela: agrupa e fixa o app na barra de tarefas
    app = QApplication(sys.argv)
    app.setApplicationName('ILoveFMTLY')
    app.setWindowIcon(QIcon(str(ASSETS / 'app.ico')))
    settings = Settings.load()
    apply_appearance(settings.theme, settings.font, settings.text_size)
    apply_style(app)
    workspace = Workspace()
    app.aboutToQuit.connect(workspace.cleanup)
    window = MainWindow(workspace, settings=settings)
    window.show()
    files = [Path(a) for a in sys.argv[1:] if Path(a).is_file()]
    if files:
        window.add_files(files)
    QTimer.singleShot(0, window.maybe_welcome)  # cadastro na primeira vez
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
