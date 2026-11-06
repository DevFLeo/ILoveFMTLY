"""Ícones desenhados a partir de glifos, no mesmo estilo dos blocos do hub."""

from functools import lru_cache

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

from ui.theme import Color, Size


@lru_cache(maxsize=None)
def glyph_icon(glyph: str, color: str = Color.ACCENT, size: int = Size.TOOLBAR_ICON) -> QIcon:
    icon = QIcon()
    for mode, tone in ((QIcon.Normal, color), (QIcon.Disabled, Color.TEXT_DISABLED)):
        scale = 2  # nítido em telas com escala
        pix = QPixmap(size * scale, size * scale)
        pix.setDevicePixelRatio(scale)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        font = QFont('Segoe UI Symbol')
        font.setPixelSize(int(size * 0.85))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(tone))
        painter.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, glyph)
        painter.end()
        icon.addPixmap(pix, mode)
    return icon
