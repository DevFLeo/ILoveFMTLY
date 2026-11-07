"""Ícones SVG (Lucide, licença ISC) em assets/icons, pintados com as cores do tema.

Os SVGs usam stroke="currentColor"; aqui a cor é trocada antes de desenhar,
então qualquer token de ui/theme.py serve.
"""

from functools import lru_cache

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from ui.theme import ASSETS, Color, Size

ICONS = ASSETS / 'icons'
_SCALE = 2  # nítido em telas com escala


def icon_path(name: str):
    return ICONS / f'{name}.svg'


@lru_cache(maxsize=None)
def _svg(name: str, color: str) -> bytes:
    data = icon_path(name).read_text(encoding='utf-8')
    return data.replace('currentColor', color).encode('utf-8')


def svg_pixmap(name: str, color: str | None = None, size: int = Size.TOOLBAR_ICON) -> QPixmap:
    color = color or Color.ACCENT  # resolvido na hora: o tema pode mudar antes da janela
    pix = QPixmap(size * _SCALE, size * _SCALE)
    pix.setDevicePixelRatio(_SCALE)
    pix.fill(Qt.transparent)
    renderer = QSvgRenderer(QByteArray(_svg(name, color)))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return pix


def svg_icon(name: str, color: str | None = None, size: int = Size.TOOLBAR_ICON) -> QIcon:
    return _svg_icon(name, color or Color.ACCENT, Color.TEXT_DISABLED, size)


@lru_cache(maxsize=None)
def _svg_icon(name: str, color: str, disabled: str, size: int) -> QIcon:
    icon = QIcon()
    icon.addPixmap(svg_pixmap(name, color, size), QIcon.Normal)
    icon.addPixmap(svg_pixmap(name, disabled, size), QIcon.Disabled)
    return icon
