"""Diálogos de Assinar PDF e Preencher formulário.

Mesma interface dos outros diálogos de ferramenta:
    Dialog.ask(parent, src, kind) -> dict de parâmetros, ou None se cancelado.
Erros de leitura (ex.: PDF sem campos) sobem como ValueError.
"""

from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QScrollArea, QSpinBox, QVBoxLayout,
                               QWidget)

from core import pdf_tools
from core.engines import mupdf
from ui.theme import INK, PAPER, Space

PAD_SIZE = (520, 200)
STROKE = 3.0   # px
CROP_PAD = 8   # px de folga ao recortar a assinatura


def _section(text: str) -> QLabel:
    label = QLabel(text.upper())
    label.setProperty('role', 'section')
    return label


def _png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.WriteOnly)
    image.save(buf, 'PNG')
    buf.close()
    return bytes(data)


def _buttons(primary_text: str, dialog: QDialog) -> tuple[QHBoxLayout, QPushButton]:
    cancel = QPushButton('Cancelar')
    cancel.setProperty('variant', 'ghost')
    cancel.clicked.connect(dialog.reject)
    primary = QPushButton(primary_text)
    primary.setProperty('variant', 'primary')
    primary.setDefault(True)
    primary.clicked.connect(dialog.accept)
    row = QHBoxLayout()
    row.addStretch(1)
    row.addWidget(cancel)
    row.addWidget(primary)
    return row, primary


class SignPad(QWidget):
    """Área para desenhar a assinatura com o mouse (ou mostrar uma imagem escolhida)."""

    changed = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName('signPad')
        self.setFixedSize(*PAD_SIZE)
        self.setCursor(Qt.CrossCursor)
        self.setAccessibleName('Área de assinatura')
        self.paths: list[QPainterPath] = []
        self.image: QImage | None = None

    def clear(self):
        self.paths, self.image = [], None
        self.update()
        self.changed.emit()

    def set_image(self, image: QImage):
        self.paths, self.image = [], image
        self.update()
        self.changed.emit()

    def is_empty(self) -> bool:
        return not self.paths and self.image is None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.image = None
            path = QPainterPath(event.position())
            path.lineTo(event.position() + QPointF(0.1, 0.1))  # um clique vira um ponto
            self.paths.append(path)
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.paths:
            self.paths[-1].lineTo(event.position())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.changed.emit()

    def _pen(self) -> QPen:
        return QPen(QColor(INK), STROKE, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(PAPER))
        if self.image is not None:
            size = self.image.size().scaled(self.size(), Qt.KeepAspectRatio)
            x, y = (self.width() - size.width()) / 2, (self.height() - size.height()) / 2
            p.drawImage(QRectF(x, y, size.width(), size.height()), self.image)
        p.setPen(self._pen())
        for path in self.paths:
            p.drawPath(path)
        p.end()

    def signature_png(self) -> bytes:
        """PNG com fundo transparente, recortado em volta do traço."""
        if self.image is not None:
            return _png_bytes(self.image)
        if not self.paths:
            return b''
        bounds = QRectF()
        for path in self.paths:
            bounds = bounds.united(path.boundingRect())
        bounds = bounds.adjusted(-CROP_PAD, -CROP_PAD, CROP_PAD, CROP_PAD)
        scale = 3  # nítido no PDF impresso
        img = QImage(int(bounds.width() * scale), int(bounds.height() * scale), QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(scale, scale)
        p.translate(-bounds.topLeft())
        p.setPen(self._pen())
        for path in self.paths:
            p.drawPath(path)
        p.end()
        return _png_bytes(img)


class SignDialog(QDialog):
    def __init__(self, parent, src: Path):
        super().__init__(parent)
        self.setWindowTitle('Assinar PDF')
        self.src = Path(src)
        pages = mupdf.page_count(self.src)

        self.pad = SignPad()
        clear = QPushButton('Limpar')
        clear.setProperty('variant', 'ghost')
        clear.clicked.connect(self.pad.clear)
        load = QPushButton('Usar imagem…')
        load.setProperty('variant', 'ghost')
        load.clicked.connect(self.load_image)
        pad_tools = QHBoxLayout()
        pad_tools.addWidget(QLabel('Desenhe com o mouse ou use uma imagem da sua assinatura.'))
        pad_tools.addStretch(1)
        pad_tools.addWidget(clear)
        pad_tools.addWidget(load)

        self.page = QSpinBox()
        self.page.setRange(0, pages)
        self.page.setSpecialValueText('Última')
        self.page.setValue(0)
        self.page.setSuffix(f' de {pages}')
        self.position = QComboBox()
        self.position.addItems(pdf_tools.SIGN_POSITIONS)
        self.width_pct = QSpinBox()
        self.width_pct.setRange(5, 90)
        self.width_pct.setValue(30)
        self.width_pct.setSuffix(' % da largura')
        form = QFormLayout()
        form.setHorizontalSpacing(Space.LG)
        form.setVerticalSpacing(Space.MD)
        form.addRow('Página', self.page)
        form.addRow('Posição', self.position)
        form.addRow('Tamanho', self.width_pct)

        buttons, self.primary = _buttons('Assinar', self)
        self.pad.changed.connect(lambda: self.primary.setEnabled(not self.pad.is_empty()))
        self.primary.setEnabled(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.XL, Space.XL, Space.XL, Space.XL)
        layout.setSpacing(Space.SM)
        layout.addWidget(_section('Assinatura'))
        layout.addWidget(self.pad, 0, Qt.AlignHCenter)
        layout.addLayout(pad_tools)
        layout.addSpacing(Space.XL)
        layout.addWidget(_section('Onde colocar'))
        layout.addLayout(form)
        layout.addSpacing(Space.LG)
        layout.addLayout(buttons)

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Imagem da assinatura', '',
                                              'Imagens (*.png *.jpg *.jpeg *.webp *.bmp)')
        if path:
            image = QImage(path)
            if not image.isNull():
                self.pad.set_image(image)

    def values(self) -> dict:
        return {'signature': self.pad.signature_png(), 'page': self.page.value(),
                'position': self.position.currentText(), 'width': self.width_pct.value()}

    @classmethod
    def ask(cls, parent, src: Path, _kind: str = 'sign') -> dict | None:
        dialog = cls(parent, src)
        return dialog.values() if dialog.exec() == QDialog.Accepted else None


class FormsDialog(QDialog):
    def __init__(self, parent, src: Path):
        super().__init__(parent)
        self.setWindowTitle('Preencher formulário')
        self.fields = pdf_tools.read_fields(src)  # ValueError se não houver campos
        self.inputs: dict[str, QWidget] = {}

        form = QFormLayout()
        form.setHorizontalSpacing(Space.LG)
        form.setVerticalSpacing(Space.MD)
        for f in self.fields:
            if f.kind == pdf_tools.CHECK:
                w = QCheckBox()
                w.setChecked(bool(f.value))
            elif f.kind in (pdf_tools.CHOICE, pdf_tools.RADIO):
                w = QComboBox()
                w.addItems(f.options)
                w.setEditable(f.kind == pdf_tools.CHOICE and not f.options)
                if f.value in f.options:
                    w.setCurrentText(f.value)
            else:
                w = QLineEdit(str(f.value))
            w.setAccessibleName(f.name)
            self.inputs[f.name] = w
            form.addRow(f.name, w)
        holder = QWidget()
        holder.setLayout(form)
        scroll = QScrollArea()
        scroll.setWidget(holder)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(min(420, 48 * len(self.fields) + 24))

        self.flatten = QCheckBox('Deixar fixo (ninguém consegue mais editar os campos)')
        count = QLabel(f'{len(self.fields)} CAMPOS')
        count.setProperty('role', 'mono')
        buttons, _ = _buttons('Preencher', self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.XL, Space.XL, Space.XL, Space.XL)
        layout.setSpacing(Space.SM)
        head = QHBoxLayout()
        head.addWidget(_section('Campos do formulário'))
        head.addStretch(1)
        head.addWidget(count)
        layout.addLayout(head)
        layout.addWidget(scroll)
        layout.addSpacing(Space.MD)
        layout.addWidget(self.flatten)
        layout.addSpacing(Space.LG)
        layout.addLayout(buttons)
        self.setMinimumWidth(520)

    def values(self) -> dict:
        out = {}
        for name, w in self.inputs.items():
            if isinstance(w, QCheckBox):
                out[name] = w.isChecked()
            elif isinstance(w, QComboBox):
                out[name] = w.currentText()
            else:
                out[name] = w.text()
        return {'values': out, 'flatten': self.flatten.isChecked()}

    @classmethod
    def ask(cls, parent, src: Path, _kind: str = 'forms') -> dict | None:
        dialog = cls(parent, src)
        return dialog.values() if dialog.exec() == QDialog.Accepted else None
