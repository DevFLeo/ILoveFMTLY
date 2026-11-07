"""Vídeo para GIF: prévia, trilha com alças de início/fim, play, FPS, largura, formato.

Visual do DESIGN.md: trilha fina na cor de borda, trecho em vinho, alças accent,
linha de estado em Mono e uma única ação principal ("Gerar GIF").
"""

from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QSpinBox,
                               QVBoxLayout, QWidget)

from core import video
from ui.icons import svg_icon
from ui.theme import Color, Space

PREVIEW = (640, 360)
HANDLE_W, TRACK_H = 8, 4
DEFAULT_SECONDS = 5.0


class Timeline(QWidget):
    """Trilha do vídeo. Arraste as alças para o trecho; clique fora delas para mover a agulha."""
    range_changed = Signal(float, float)
    scrubbed = Signal(float)

    def __init__(self, duration: float):
        super().__init__()
        self.duration = max(duration, 0.01)
        self.start, self.end = 0.0, min(self.duration, DEFAULT_SECONDS)
        self.playhead = 0.0
        self._drag = None
        self.setFixedHeight(32)
        self.setMinimumWidth(PREVIEW[0])
        self.setCursor(Qt.PointingHandCursor)

    def _x(self, t: float) -> float:
        usable = self.width() - HANDLE_W
        return HANDLE_W / 2 + usable * t / self.duration

    def _t(self, x: float) -> float:
        usable = max(1, self.width() - HANDLE_W)
        return min(max((x - HANDLE_W / 2) / usable * self.duration, 0.0), self.duration)

    def set_range(self, start: float, end: float):
        start = min(max(start, 0.0), self.duration)
        end = min(max(end, 0.0), self.duration)
        if end - start < 0.1:
            return
        self.start, self.end = start, end
        self.playhead = min(max(self.playhead, start), end)
        self.update()
        self.range_changed.emit(start, end)

    def set_playhead(self, t: float):
        self.playhead = min(max(t, 0.0), self.duration)
        self.update()
        self.scrubbed.emit(self.playhead)

    def mousePressEvent(self, e):
        x = e.position().x()
        if abs(x - self._x(self.start)) <= HANDLE_W:
            self._drag = 'start'
        elif abs(x - self._x(self.end)) <= HANDLE_W:
            self._drag = 'end'
        else:
            self._drag = 'head'
            self.set_playhead(self._t(x))

    def mouseMoveEvent(self, e):
        t = self._t(e.position().x())
        if self._drag == 'start':
            self.set_range(min(t, self.end - 0.1), self.end)
            self.set_playhead(self.start)
        elif self._drag == 'end':
            self.set_range(self.start, max(t, self.start + 0.1))
            self.set_playhead(self.end)
        elif self._drag == 'head':
            self.set_playhead(t)

    def mouseReleaseEvent(self, e):
        self._drag = None

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        mid = self.height() / 2
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(Color.BORDER))
        p.drawRoundedRect(QRectF(HANDLE_W / 2, mid - TRACK_H / 2, self.width() - HANDLE_W, TRACK_H), 2, 2)
        a, b = self._x(self.start), self._x(self.end)
        p.setBrush(QColor(Color.WINE))
        p.drawRect(QRectF(a, mid - 8, b - a, 16))
        p.setBrush(QColor(Color.ACCENT))
        for x in (a, b):
            p.drawRoundedRect(QRectF(x - HANDLE_W / 2, mid - 12, HANDLE_W, 24), 2, 2)
        p.setPen(QPen(QColor(Color.TEXT), 2))
        h = self._x(self.playhead)
        p.drawLine(round(h), 2, round(h), self.height() - 2)
        p.end()


class VideoGifDialog(QDialog):
    def __init__(self, parent, path: Path):
        super().__init__(parent)
        self.path = Path(path)
        self.info = video.probe(self.path)       # VideoError sobe para quem abriu
        self.setWindowTitle(f'Vídeo para GIF · {self.path.name}')

        section = QLabel('VÍDEO PARA GIF')
        section.setProperty('role', 'section')
        self.preview = QLabel(alignment=Qt.AlignCenter)
        self.preview.setFixedSize(*PREVIEW)
        self.preview.setObjectName('videoPreview')
        self.timeline = Timeline(self.info.duration)

        self.play = QPushButton()
        self.play.setProperty('variant', 'ghost')
        self.play.setToolTip('Prévia do trecho (Espaço)')
        self.play.setCheckable(True)
        self.play.toggled.connect(self._toggle_play)
        self._set_play_icon(False)

        self.fps = QSpinBox()
        self.fps.setRange(1, 30)
        self.fps.setValue(10)
        self.fps.setSuffix(' fps')
        self.width_px = QSpinBox()
        self.width_px.setRange(0, max(16, self.info.width))
        self.width_px.setValue(min(480, self.info.width))
        self.width_px.setSuffix(' px')
        self.width_px.setSpecialValueText('original')
        self.fmt = QComboBox()
        self.fmt.addItems(list(video.FORMATS))

        controls = QHBoxLayout()
        controls.setSpacing(Space.MD)
        controls.addWidget(self.play)
        for label, field in (('Quadros por segundo', self.fps), ('Largura', self.width_px),
                             ('Formato', self.fmt)):
            controls.addSpacing(Space.SM)
            controls.addWidget(QLabel(label))
            controls.addWidget(field)
        controls.addStretch(1)

        self.status = QLabel()
        self.status.setProperty('role', 'mono')

        cancel = QPushButton('Cancelar', clicked=self.reject)
        cancel.setProperty('variant', 'ghost')
        self.ok = QPushButton('Gerar GIF', clicked=self.accept)
        self.ok.setObjectName('primary')
        self.ok.setProperty('variant', 'primary')
        self.ok.setDefault(True)
        buttons = QHBoxLayout()
        buttons.addWidget(self.status, 1)
        buttons.addWidget(cancel)
        buttons.addWidget(self.ok)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.XL, Space.XL, Space.XL, Space.XL)
        layout.setSpacing(Space.LG)
        layout.addWidget(section)
        layout.addWidget(self.preview, 0, Qt.AlignCenter)
        layout.addWidget(self.timeline)
        layout.addLayout(controls)
        layout.addSpacing(Space.SM)
        layout.addLayout(buttons)

        self._pending = None
        self._debounce = QTimer(self, singleShot=True, interval=80, timeout=self._render)
        self._ticker = QTimer(self, timeout=self._tick)
        self.timeline.range_changed.connect(lambda *_: self._update_status())
        self.timeline.scrubbed.connect(self._request_frame)
        for w in (self.fps, self.width_px):
            w.valueChanged.connect(self._update_status)
        self.fmt.currentTextChanged.connect(self._on_format)
        self._update_status()
        self._request_frame(0.0)

    # estado ------------------------------------------------------------------
    def _on_format(self, fmt: str):
        self.ok.setText(f'Gerar {fmt}')
        self._update_status()

    def _update_status(self):
        s, e = self.timeline.start, self.timeline.end
        est = video.estimate(self.info, s, e, self.fps.value(), self.width_px.value(),
                             self.fmt.currentText())
        too_long = e - s > video.MAX_SECONDS
        text = video.status_line(s, e, est)
        if too_long:
            text += f' · máx. {video.MAX_SECONDS} s'
        self.status.setText(text)
        self.status.setProperty('tone', 'error' if too_long else None)
        self.style().polish(self.status)
        self.ok.setEnabled(not too_long)

    # prévia ------------------------------------------------------------------
    def _request_frame(self, t: float):
        self._pending = t
        self._debounce.start()

    def _render(self):
        if self._pending is None:
            return
        try:
            img = video.frame_at(self.path, self._pending, max_width=PREVIEW[0])
        except video.VideoError:
            return
        img = img.convert('RGB')
        qimg = QImage(img.tobytes(), img.width, img.height, 3 * img.width, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg.copy()).scaled(*PREVIEW, Qt.KeepAspectRatio,
                                                    Qt.SmoothTransformation)
        self.preview.setPixmap(pix)

    def _set_play_icon(self, playing: bool):
        self.play.setIcon(svg_icon('pause' if playing else 'play'))
        self.play.setText('Pausar' if playing else 'Prévia')

    def _toggle_play(self, on: bool):
        self._set_play_icon(on)
        if on:
            if not self.timeline.start <= self.timeline.playhead < self.timeline.end:
                self.timeline.set_playhead(self.timeline.start)
            self._ticker.start(round(1000 / self.fps.value()))
        else:
            self._ticker.stop()

    def _tick(self):
        t = self.timeline.playhead + 1 / self.fps.value()
        if t >= self.timeline.end:
            t = self.timeline.start
        self.timeline.set_playhead(t)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space:
            self.play.toggle()
        else:
            super().keyPressEvent(e)

    def done(self, result):
        self._ticker.stop()
        super().done(result)

    # resultado ---------------------------------------------------------------
    def values(self) -> dict:
        return {'start': round(self.timeline.start, 2), 'end': round(self.timeline.end, 2),
                'fps': self.fps.value(), 'width': self.width_px.value(),
                'fmt': self.fmt.currentText()}

    @classmethod
    def ask(cls, parent, path: Path, mode: str = 'video') -> dict | None:
        dlg = cls(parent, path)
        return dlg.values() if dlg.exec() == QDialog.Accepted else None
