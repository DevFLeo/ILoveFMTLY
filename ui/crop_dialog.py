"""Diálogo de recorte e de borrar área.

Mostra a imagem com um retângulo arrastável (criar, mover, redimensionar pelas
alças). Visual do DESIGN.md: fora da área fica o fundo a 70 %, borda accent de
2 px, alças de 8 px, medida em Mono e uma ação principal.
"""

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImageReader, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QSpinBox,
                               QVBoxLayout, QWidget)

from ui.theme import Color, Space

RATIOS = {'Livre': None, '1:1': 1.0, '4:3': 4 / 3, '16:9': 16 / 9, '3:4': 3 / 4, '9:16': 9 / 16}
HANDLE = 8          # px
DIM_ALPHA = 178     # 70 %
MAX_VIEW = (860, 540)
MIN_SIDE = 4        # px da imagem


class CropCanvas(QWidget):
    changed = Signal()

    def __init__(self, image):
        super().__init__()
        self.image = image
        w, h = image.width(), image.height()
        self.scale = min(1.0, MAX_VIEW[0] / w, MAX_VIEW[1] / h)
        self.setFixedSize(max(1, round(w * self.scale)), max(1, round(h * self.scale)))
        self.ratio: float | None = None
        self.sel = QRectF(w * 0.1, h * 0.1, w * 0.8, h * 0.8)
        self._drag = None          # ('new'|'move'|corner, ponto inicial, seleção inicial)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

    # coordenadas -------------------------------------------------------------
    def to_widget(self, x: float, y: float) -> QPointF:
        return QPointF(x * self.scale, y * self.scale)

    def to_image(self, p: QPointF) -> QPointF:
        return QPointF(min(max(p.x() / self.scale, 0), self.image.width()),
                       min(max(p.y() / self.scale, 0), self.image.height()))

    def view_rect(self) -> QRectF:
        s = self.scale
        return QRectF(self.sel.x() * s, self.sel.y() * s, self.sel.width() * s, self.sel.height() * s)

    def _corners(self) -> dict[str, QPointF]:
        r = self.view_rect()
        return {'tl': r.topLeft(), 'tr': r.topRight(), 'bl': r.bottomLeft(), 'br': r.bottomRight()}

    # regras ------------------------------------------------------------------
    def set_ratio(self, ratio: float | None):
        self.ratio = ratio
        self.set_selection(self.sel)

    def set_selection(self, rect: QRectF, anchor: str = 'tl'):
        """Normaliza, aplica a proporção e mantém dentro da imagem."""
        r = rect.normalized()
        W, H = self.image.width(), self.image.height()
        r = r.intersected(QRectF(0, 0, W, H))
        if self.ratio:
            w, h = r.width(), r.height()
            if w / max(h, 1e-6) > self.ratio:
                w = h * self.ratio
            else:
                h = w / self.ratio
            if anchor in ('br', 'move'):
                r = QRectF(r.left(), r.top(), w, h)
            elif anchor == 'tr':
                r = QRectF(r.left(), r.bottom() - h, w, h)
            elif anchor == 'bl':
                r = QRectF(r.right() - w, r.top(), w, h)
            else:
                r = QRectF(r.left(), r.top(), w, h)
        if r.width() >= MIN_SIDE and r.height() >= MIN_SIDE:
            self.sel = r
        self.changed.emit()
        self.update()

    # mouse -------------------------------------------------------------------
    def _hit(self, pos: QPointF) -> str:
        for name, c in self._corners().items():
            if abs(pos.x() - c.x()) <= HANDLE and abs(pos.y() - c.y()) <= HANDLE:
                return name
        return 'move' if self.view_rect().contains(pos) else 'new'

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        pos = e.position()
        self._drag = (self._hit(pos), self.to_image(pos), QRectF(self.sel))

    def mouseMoveEvent(self, e):
        pos = e.position()
        if not self._drag:
            hit = self._hit(pos)
            self.setCursor({'move': Qt.SizeAllCursor, 'tl': Qt.SizeFDiagCursor,
                            'br': Qt.SizeFDiagCursor, 'tr': Qt.SizeBDiagCursor,
                            'bl': Qt.SizeBDiagCursor}.get(hit, Qt.CrossCursor))
            return
        kind, start, orig = self._drag
        p = self.to_image(pos)
        if kind == 'new':
            self.set_selection(QRectF(start, p), 'br' if p.x() >= start.x() else 'bl')
        elif kind == 'move':
            d = p - start
            r = orig.translated(d)
            W, H = self.image.width(), self.image.height()
            r.moveLeft(min(max(r.left(), 0), W - r.width()))
            r.moveTop(min(max(r.top(), 0), H - r.height()))
            self.sel = r
            self.changed.emit()
            self.update()
        else:
            opposite = {'tl': orig.bottomRight(), 'br': orig.topLeft(),
                        'tr': orig.bottomLeft(), 'bl': orig.topRight()}[kind]
            self.set_selection(QRectF(opposite, p), kind)

    def mouseReleaseEvent(self, e):
        self._drag = None

    # desenho -----------------------------------------------------------------
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawImage(self.rect(), self.image)
        r = self.view_rect()
        outside = QPainterPath()
        outside.addRect(QRectF(self.rect()))
        inner = QPainterPath()
        inner.addRect(r)
        dim = QColor(Color.BG)
        dim.setAlpha(DIM_ALPHA)
        p.fillPath(outside.subtracted(inner), dim)
        p.setPen(QPen(QColor(Color.ACCENT), 2))
        p.drawRect(r)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(Color.ACCENT))
        for c in self._corners().values():
            p.drawRect(QRectF(c.x() - HANDLE / 2, c.y() - HANDLE / 2, HANDLE, HANDLE))
        p.end()


class CropDialog(QDialog):
    """mode='crop' (recortar, com proporção) ou 'blur' (pixelar a área, com tamanho do bloco)."""

    def __init__(self, parent, path: Path, mode: str = 'crop'):
        super().__init__(parent)
        self.mode = mode
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)       # mesma orientação que o core (EXIF)
        image = reader.read()
        if image.isNull():
            raise ValueError(f'{Path(path).name}: não foi possível abrir a imagem.')
        title = 'Recortar' if mode == 'crop' else 'Borrar área'
        self.setWindowTitle(f'{title} · {Path(path).name}')

        section = QLabel(title.upper())
        section.setProperty('role', 'section')
        self.canvas = CropCanvas(image)
        self.measure = QLabel()
        self.measure.setProperty('role', 'mono')

        controls = QHBoxLayout()
        controls.setSpacing(Space.MD)
        if mode == 'crop':
            controls.addWidget(QLabel('Proporção'))
            self.ratio = QComboBox()
            self.ratio.addItems(list(RATIOS))
            self.ratio.currentTextChanged.connect(lambda t: self.canvas.set_ratio(RATIOS[t]))
            controls.addWidget(self.ratio)
        else:
            controls.addWidget(QLabel('Tamanho do bloco'))
            self.block = QSpinBox()
            self.block.setRange(4, 80)
            self.block.setValue(max(8, min(image.width(), image.height()) // 40))
            self.block.setSuffix(' px')
            controls.addWidget(self.block)
            w, h = image.width(), image.height()
            self.canvas.set_selection(QRectF(w * 0.35, h * 0.3, w * 0.3, h * 0.4))
        controls.addStretch(1)
        controls.addWidget(self.measure)

        cancel = QPushButton('Cancelar', clicked=self.reject)
        cancel.setProperty('variant', 'ghost')
        ok = QPushButton('Recortar' if mode == 'crop' else 'Borrar', clicked=self.accept)
        ok.setObjectName('primary')
        ok.setProperty('variant', 'primary')
        ok.setDefault(True)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.XL, Space.XL, Space.XL, Space.XL)
        layout.setSpacing(Space.LG)
        layout.addWidget(section)
        layout.addWidget(self.canvas, 0, Qt.AlignCenter)
        layout.addLayout(controls)
        layout.addLayout(buttons)

        self.canvas.changed.connect(self._update_measure)
        self._update_measure()

    def box(self) -> tuple[int, int, int, int]:
        r = self.canvas.sel
        return round(r.left()), round(r.top()), round(r.right()), round(r.bottom())

    def set_box(self, box):
        x0, y0, x1, y1 = box
        self.canvas.set_selection(QRectF(x0, y0, x1 - x0, y1 - y0))

    def _update_measure(self):
        x0, y0, x1, y1 = self.box()
        self.measure.setText(f'x {x0} · y {y0} · {x1 - x0} × {y1 - y0} px')

    def values(self) -> dict:
        data = {'box': self.box()}
        if self.mode == 'blur':
            data['block'] = self.block.value()
        return data

    @classmethod
    def ask(cls, parent, path: Path, mode: str = 'crop') -> dict | None:
        dlg = cls(parent, path, mode)
        return dlg.values() if dlg.exec() == QDialog.Accepted else None
