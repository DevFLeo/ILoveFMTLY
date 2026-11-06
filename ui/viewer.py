"""Visualizador de página com zoom (Ctrl + roda do mouse, ou botões).

Abre em "Ajustar à largura"; usar + ou − passa para zoom fixo.
"""

from bisect import bisect_left

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from core.document import PageRef
from core.engines import mupdf

ZOOM_STEPS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
MARGIN = 32


class _Scroll(QScrollArea):
    def __init__(self, viewer):
        super().__init__()
        self._viewer = viewer

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self._viewer.zoom_by(1 if event.angleDelta().y() > 0 else -1)
            event.accept()
        else:
            super().wheelEvent(event)


class Viewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('viewer')
        self._ref: PageRef | None = None
        self._fit = True
        self._zoom = 1.0

        self.page_label = QLabel(alignment=Qt.AlignCenter)
        self.page_label.setObjectName('page')
        self.scroll = _Scroll(self)
        self.scroll.setWidget(self.page_label)
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignCenter)

        self.info = QLabel('Nenhuma página selecionada')
        self.info.setObjectName('muted')
        minus = QPushButton('−', clicked=lambda: self.zoom_by(-1))
        plus = QPushButton('+', clicked=lambda: self.zoom_by(1))
        fit = QPushButton('Ajustar', clicked=self.fit_width)
        for b in (minus, plus):
            b.setFixedWidth(32)
        for b in (minus, plus, fit):
            b.setObjectName('ghost')
        self.zoom_label = QLabel()
        self.zoom_label.setMinimumWidth(44)
        self.zoom_label.setAlignment(Qt.AlignCenter)

        bar = QHBoxLayout()
        bar.setContentsMargins(8, 6, 8, 6)
        bar.addWidget(self.info, 1)
        bar.addWidget(fit)
        bar.addWidget(minus)
        bar.addWidget(self.zoom_label)
        bar.addWidget(plus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(bar)
        layout.addWidget(self.scroll, 1)

        self._resize_timer = QTimer(self, singleShot=True, interval=120)
        self._resize_timer.timeout.connect(self._render)

    @property
    def zoom(self) -> float:
        if self._fit and self._ref is not None:
            width, _ = mupdf.page_size(self._ref.source, self._ref.index, self._ref.rotation)
            available = self.scroll.viewport().width() - MARGIN
            return max(0.1, available / width)
        return self._zoom

    def fit_width(self) -> None:
        self._fit = True
        self._render()

    def zoom_by(self, step: int) -> None:
        current = self.zoom
        if step > 0:
            i = bisect_left(ZOOM_STEPS, current + 0.01)
        else:
            i = bisect_left(ZOOM_STEPS, current - 0.01) - 1
        self._zoom = ZOOM_STEPS[max(0, min(len(ZOOM_STEPS) - 1, i))]
        self._fit = False
        self._render()

    def show_page(self, ref: PageRef | None, position: str = '') -> None:
        self._ref = ref
        self.info.setText(f'{position}  ·  {ref.source.name}, pág. {ref.index + 1}'
                          if ref else 'Nenhuma página selecionada')
        self._render()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fit:
            self._resize_timer.start()

    def _render(self):
        if self._ref is None:
            self.page_label.clear()
            self.zoom_label.setText('')
            return
        zoom = self.zoom
        self.zoom_label.setText(f'{round(zoom * 100)}%')
        ratio = self.devicePixelRatioF()
        pix = QPixmap()
        pix.loadFromData(mupdf.render(self._ref.source, self._ref.index,
                                      zoom * ratio, self._ref.rotation))
        pix.setDevicePixelRatio(ratio)
        self.page_label.setPixmap(pix)
