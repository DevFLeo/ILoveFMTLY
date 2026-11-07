"""Janela das ferramentas de desenvolvedor (mode='dev').

Entrada à esquerda (texto, dois textos, um arquivo ou nada), parâmetros, saída à
direita. Roda sozinha enquanto você digita (com uma pequena pausa); textos muito
grandes esperam o botão Rodar. Saída em texto ou imagem (QR, código de barras),
com Copiar e Salvar.
"""

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt, QTimer
from PySide6.QtGui import QFontDatabase, QGuiApplication, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPlainTextEdit, QPushButton, QSpinBox, QSplitter,
                               QVBoxLayout, QWidget)
from PySide6.QtGui import QFont, QPainter

from ui.theme import Space, Type
from ui.tools import Tool

LIVE_LIMIT = 200_000   # caracteres: acima disso, só com o botão Rodar
DEBOUNCE_MS = 300
PREVIEW = 320          # px, prévia de imagem


def _section(text: str) -> QLabel:
    label = QLabel(text.upper())
    label.setProperty('role', 'section')
    return label


def _mono_editor(placeholder: str = '', read_only: bool = False) -> QPlainTextEdit:
    edit = QPlainTextEdit()
    edit.setPlaceholderText(placeholder)
    edit.setReadOnly(read_only)
    edit.setLineWrapMode(QPlainTextEdit.NoWrap)
    font = QFont(Type.MONO)
    font.setPointSize(Type.BODY)
    edit.setFont(font)
    return edit


def _resolve(name: str):
    from ui.main_window import resolve_fn  # import tardio: evita ciclo
    return resolve_fn(name)


class DevDialog(QDialog):
    def __init__(self, parent, tool: Tool, text: str = '', path: Path | None = None):
        super().__init__(parent)
        self.tool = tool
        self.fn = _resolve(tool.fn)
        self.result: str | bytes | None = None
        self.setWindowTitle(tool.title)
        self.timer = QTimer(self, singleShot=True, interval=DEBOUNCE_MS)
        self.timer.timeout.connect(self.run)

        # --- entrada ----------------------------------------------------------
        self.inputs: list[QPlainTextEdit] = []
        self.path_field: QLineEdit | None = None
        left = QVBoxLayout()
        left.setSpacing(Space.SM)
        kind = tool.dev_input
        if kind in ('text', 'two'):
            labels = tool.dev_labels if kind == 'two' else (tool.dev_labels[0],)
            for i, label in enumerate(labels):
                head = QHBoxLayout()
                head.addWidget(_section(label))
                head.addStretch(1)
                editor = _mono_editor('Cole aqui ou abra um arquivo…')
                open_btn = QPushButton('Abrir arquivo…')
                open_btn.setProperty('variant', 'ghost')
                open_btn.clicked.connect(lambda _=False, e=editor: self.open_into(e))
                head.addWidget(open_btn)
                editor.textChanged.connect(self.schedule)
                left.addLayout(head)
                left.addWidget(editor, 1)
                self.inputs.append(editor)
            if text and self.inputs:
                self.inputs[0].setPlainText(text)
        elif kind == 'file':
            left.addWidget(_section('Arquivo'))
            row = QHBoxLayout()
            self.path_field = QLineEdit(str(path or ''))
            self.path_field.setReadOnly(True)
            self.path_field.setPlaceholderText('Nenhum arquivo escolhido')
            pick = QPushButton('Escolher…')
            pick.clicked.connect(self.pick_file)
            row.addWidget(self.path_field, 1)
            row.addWidget(pick)
            left.addLayout(row)
            left.addStretch(1)

        # --- parâmetros ---------------------------------------------------------
        self.fields: dict[str, QWidget] = {}
        form = QFormLayout()
        form.setHorizontalSpacing(Space.LG)
        form.setVerticalSpacing(Space.MD)
        for p in tool.params:
            if p.options:
                field = QComboBox()
                field.addItems([str(o) for o in p.options])
                field.setCurrentText(str(p.default))
                field.currentIndexChanged.connect(self.schedule)
            elif isinstance(p.default, str):
                field = QLineEdit(p.default)
                field.setPlaceholderText(p.hint)
                field.textChanged.connect(self.schedule)
            else:
                field = QSpinBox()
                field.setRange(p.min, p.max)
                field.setValue(int(p.default))
                field.setSuffix(p.suffix)
                field.valueChanged.connect(self.schedule)
            field.setAccessibleName(p.label)
            self.fields[p.key] = field
            form.addRow(p.label, field)
        if tool.params:
            left.addSpacing(Space.SM)
            left.addWidget(_section('Opções'))
            left.addLayout(form)

        # --- saída --------------------------------------------------------------
        right = QVBoxLayout()
        right.setSpacing(Space.SM)
        out_head = QHBoxLayout()
        out_head.addWidget(_section(tool.dev_labels[-1] if kind != 'two' else 'Resultado'))
        out_head.addStretch(1)
        self.copy_btn = QPushButton('Copiar')
        self.copy_btn.setProperty('variant', 'ghost')
        self.copy_btn.clicked.connect(self.copy)
        self.save_btn = QPushButton('Salvar…')
        self.save_btn.setProperty('variant', 'ghost')
        self.save_btn.clicked.connect(self.save)
        out_head.addWidget(self.copy_btn)
        out_head.addWidget(self.save_btn)
        self.error = QLabel()
        self.error.setProperty('tone', 'error')
        self.error.setWordWrap(True)
        self.error.hide()
        self.output = _mono_editor(read_only=True)
        self.image = QLabel(alignment=Qt.AlignCenter)
        self.image.setMinimumSize(PREVIEW, PREVIEW)
        self.image.hide()
        right.addLayout(out_head)
        right.addWidget(self.error)
        right.addWidget(self.output, 1)
        right.addWidget(self.image, 1)

        # --- montagem -----------------------------------------------------------
        split = QSplitter(Qt.Horizontal)
        for box in (left, right):
            holder = QWidget()
            holder.setLayout(box)
            split.addWidget(holder)
        if kind == 'none':
            split.setSizes([360, 640])
        self.run_btn = QPushButton('Rodar')
        self.run_btn.setProperty('variant', 'primary')
        self.run_btn.setDefault(True)
        self.run_btn.clicked.connect(self.run)
        close = QPushButton('Fechar')
        close.setProperty('variant', 'ghost')
        close.clicked.connect(self.accept)
        desc = QLabel(tool.desc)
        desc.setProperty('tone', 'muted')
        bottom = QHBoxLayout()
        bottom.addWidget(desc, 1)
        bottom.addWidget(close)
        bottom.addWidget(self.run_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.XL, Space.XL, Space.XL, Space.XL)
        layout.setSpacing(Space.MD)
        layout.addWidget(split, 1)
        layout.addLayout(bottom)
        self.resize(1100, 680)
        self._update_buttons()
        if kind == 'none' or (kind == 'text' and text) or (kind == 'file' and path):
            QTimer.singleShot(0, self.run)

    # --- entrada -----------------------------------------------------------------
    def open_into(self, editor: QPlainTextEdit):
        exts = ' '.join(f'*{e}' for e in sorted(self.tool.accepts)) or '*.*'
        chosen, _ = QFileDialog.getOpenFileName(self, 'Abrir', '', f'Arquivos ({exts});;Todos (*.*)')
        if chosen:
            editor.setPlainText(Path(chosen).read_text(encoding='utf-8', errors='replace'))

    def pick_file(self):
        exts = ' '.join(f'*{e}' for e in sorted(self.tool.accepts)) or '*.*'
        chosen, _ = QFileDialog.getOpenFileName(self, 'Escolher arquivo', '', f'Arquivos ({exts});;Todos (*.*)')
        if chosen:
            self.path_field.setText(chosen)
            self.run()

    def schedule(self, *_):
        if sum(len(e.toPlainText()) for e in self.inputs) <= LIVE_LIMIT:
            self.timer.start()

    def values(self) -> dict:
        out = {}
        for key, f in self.fields.items():
            if isinstance(f, QComboBox):
                out[key] = f.currentText()
            elif isinstance(f, QLineEdit):
                out[key] = f.text()
            else:
                out[key] = f.value()
        return out

    # --- execução ----------------------------------------------------------------
    def run(self):
        kind = self.tool.dev_input
        try:
            if kind == 'text':
                text = self.inputs[0].toPlainText()
                if not text.strip():
                    return self._show('', None)
                result = self.fn(text, **self.values())
            elif kind == 'two':
                a, b = (e.toPlainText() for e in self.inputs)
                if not a.strip() or not b.strip():
                    return self._show('', None)
                result = self.fn(a, b, **self.values())
            elif kind == 'file':
                path = self.path_field.text()
                if not path:
                    return self._show('', None)
                result = self.fn(Path(path), **self.values())
            else:
                result = self.fn(**self.values())
        except (ValueError, TypeError, OSError) as exc:
            return self._show(None, str(exc))
        return self._show(result, None)

    def _show(self, result, error):
        self.result = result if error is None else None
        self.error.setText(error or '')
        self.error.setVisible(bool(error))
        if isinstance(result, bytes):
            self.output.hide()
            self.image.show()
            self.image.setPixmap(self._pixmap(result))
        else:
            self.image.hide()
            self.output.show()
            self.output.setPlainText(result or '')
        self._update_buttons()
        return result

    @staticmethod
    def _is_svg(data: bytes) -> bool:
        return data.lstrip()[:5] in (b'<?xml', b'<svg ') or b'<svg' in data[:200]

    def _pixmap(self, data: bytes) -> QPixmap:
        if self._is_svg(data):
            renderer = QSvgRenderer(QByteArray(data))
            pix = QPixmap(PREVIEW, PREVIEW)
            pix.fill(Qt.white)
            painter = QPainter(pix)
            renderer.render(painter)
            painter.end()
            return pix
        pix = QPixmap()
        pix.loadFromData(data)
        return pix.scaled(PREVIEW, PREVIEW, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _update_buttons(self):
        has = bool(self.result)
        self.save_btn.setEnabled(has)
        self.copy_btn.setEnabled(has and isinstance(self.result, str))

    # --- saída ---------------------------------------------------------------------
    def copy(self):
        if isinstance(self.result, str):
            QGuiApplication.clipboard().setText(self.result)

    def default_ext(self) -> str:
        if isinstance(self.result, bytes):
            return '.svg' if self._is_svg(self.result) else '.png'
        return self.tool.ext or '.txt'

    def save(self):
        if not self.result:
            return
        ext = self.default_ext()
        out, _ = QFileDialog.getSaveFileName(self, 'Salvar', f'resultado{ext}', f'{ext[1:].upper()} (*{ext})')
        if not out:
            return
        target = Path(out)
        if not target.suffix:
            target = target.with_suffix(ext)
        if isinstance(self.result, bytes):
            target.write_bytes(self.result)
        else:
            target.write_text(self.result, encoding='utf-8')
        self.saved_to = target
