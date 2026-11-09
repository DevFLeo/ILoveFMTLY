"""Ícones SVG e fontes embutidas (DESIGN.md)."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from pathlib import Path  # noqa: E402

from PySide6.QtGui import QFontInfo, QImage  # noqa: E402

from ui.icons import icon_path, svg_pixmap  # noqa: E402
from ui.style import load_fonts  # noqa: E402
from ui.theme import Color, Type  # noqa: E402
from ui.tools import TOOLS  # noqa: E402

UI = Path(__file__).resolve().parent.parent / 'ui'


def test_toda_ferramenta_tem_svg():
    faltando = [t.id for t in TOOLS if not icon_path(t.icon).is_file()]
    assert faltando == []


def test_toolbar_tem_icones(qtbot, tmp_path):
    from core.workspace import Workspace
    from ui.main_window import MainWindow
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False)
    qtbot.addWidget(w)
    sem_icone = [a.text() for a in w.toolbar.actions()
                 if a.text() and not a.isSeparator() and a is not w.act_export and a.icon().isNull()]
    assert sem_icone == []


def test_svg_pinta_na_cor_pedida(qapp):
    img: QImage = svg_pixmap('lock', Color.ACCENT, 24).toImage()
    cores = {img.pixelColor(x, y).name() for x in range(img.width()) for y in range(img.height())
             if img.pixelColor(x, y).alpha() == 255}
    assert Color.ACCENT.lower() in cores


def test_fontes_plex_carregam(qapp):
    familias = load_fonts()
    assert Type.SANS in familias and Type.MONO in familias


def test_app_usa_plex(qapp):
    from ui.style import apply_style
    apply_style(qapp)
    assert QFontInfo(qapp.font()).family() == Type.SANS
