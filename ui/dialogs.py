"""Diálogos pequenos: senha, metadados, mensagens."""

from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
                               QHeaderView, QInputDialog, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout)

from ui.theme import Space


def ask_password(parent, filename: str, retry: bool) -> str | None:
    prompt = (f'Senha incorreta para "{filename}". Tente de novo:' if retry
              else f'"{filename}" é protegido por senha. Digite a senha:')
    text, ok = QInputDialog.getText(parent, 'PDF protegido', prompt, QLineEdit.Password)
    return text if ok else None


def error(parent, title: str, message: str) -> None:
    QMessageBox.critical(parent, title, message)


def info(parent, title: str, message: str) -> None:
    QMessageBox.information(parent, title, message)


class ParamDialog(QDialog):
    """Parâmetros de uma ferramenta. Segue o DESIGN.md: sem caixas, rótulo de seção
    em Mono, uma ação principal."""

    def __init__(self, parent, title: str, params):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.fields = {}
        section = QLabel(title.upper())
        section.setProperty('role', 'section')
        form = QFormLayout()
        form.setHorizontalSpacing(Space.LG)
        form.setVerticalSpacing(Space.MD)
        for p in params:
            if isinstance(p.default, str) and not p.options:
                field = QLineEdit(p.default)
                field.setPlaceholderText(p.hint)
            elif p.options:
                field = QComboBox()
                field.addItems(list(p.options))
                field.setCurrentText(str(p.default))
            else:
                field = QSpinBox()
                field.setRange(p.min, p.max)
                field.setValue(int(p.default))
                field.setSuffix(p.suffix)
            self.fields[p.key] = field
            form.addRow(p.label, field)
        cancel = QPushButton('Cancelar', clicked=self.reject)
        cancel.setProperty('variant', 'ghost')
        ok = QPushButton('Continuar', clicked=self.accept)
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
        layout.addLayout(form)
        layout.addSpacing(Space.SM)
        layout.addLayout(buttons)

    def values(self) -> dict:
        def read(f):
            if isinstance(f, QComboBox):
                return f.currentText()
            if isinstance(f, QLineEdit):
                return f.text()
            return f.value()
        return {k: read(f) for k, f in self.fields.items()}

    @classmethod
    def ask(cls, parent, title: str, params) -> dict | None:
        dlg = cls(parent, title, params)
        return dlg.values() if dlg.exec() == QDialog.Accepted else None


class MetadataDialog(QDialog):
    def __init__(self, parent, entries: list[tuple[str, str, str]]):
        super().__init__(parent)
        self.setWindowTitle('Metadados dos arquivos de origem')
        self.resize(640, 420)
        table = QTableWidget(len(entries), 3)
        table.setHorizontalHeaderLabels(['Arquivo', 'Campo', 'Valor'])
        for row, values in enumerate(entries):
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(value))
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        buttons = QDialogButtonBox(QDialogButtonBox.Close, rejected=self.reject)
        layout = QVBoxLayout(self)
        if not entries:
            table.setRowCount(1)
            table.setItem(0, 0, QTableWidgetItem('Nenhum metadado encontrado.'))
        layout.addWidget(table)
        layout.addWidget(buttons)
