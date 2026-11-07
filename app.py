"""Ponto de entrada do ILoveFMTLY.

O bloqueio de rede vem antes de qualquer outra coisa: a partir daqui nenhum
código do app consegue abrir conexão.
"""

from core import offline

offline.enable()

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from core.workspace import Workspace  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.style import apply_style  # noqa: E402
from ui.theme import ASSETS  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName('ILoveFMTLY')
    app.setWindowIcon(QIcon(str(ASSETS / 'app.ico')))
    apply_style(app)
    workspace = Workspace()
    app.aboutToQuit.connect(workspace.cleanup)
    window = MainWindow(workspace)
    window.show()
    files = [Path(a) for a in sys.argv[1:] if Path(a).is_file()]
    if files:
        window.add_files(files)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
