"""Diálogos pequenos: senha, metadados, mensagens."""

from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                               QHeaderView, QInputDialog, QLineEdit, QMessageBox,
                               QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout)


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
    """Formulário pequeno com os parâmetros de uma ferramenta (formato, DPI...)."""

    def __init__(self, parent, title: str, params):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.fields = {}
        form = QFormLayout()
        for p in params:
            if p.options:
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
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                                   accepted=self.accept, rejected=self.reject)
        buttons.button(QDialogButtonBox.Ok).setText('Continuar')
        buttons.button(QDialogButtonBox.Cancel).setText('Cancelar')
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {k: (f.currentText() if isinstance(f, QComboBox) else f.value())
                for k, f in self.fields.items()}

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
