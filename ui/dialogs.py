"""Diálogos pequenos: senha, metadados, mensagens."""

from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHeaderView, QInputDialog,
                               QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem,
                               QVBoxLayout)


def ask_password(parent, filename: str, retry: bool) -> str | None:
    prompt = (f'Senha incorreta para "{filename}". Tente de novo:' if retry
              else f'"{filename}" é protegido por senha. Digite a senha:')
    text, ok = QInputDialog.getText(parent, 'PDF protegido', prompt, QLineEdit.Password)
    return text if ok else None


def error(parent, title: str, message: str) -> None:
    QMessageBox.critical(parent, title, message)


def info(parent, title: str, message: str) -> None:
    QMessageBox.information(parent, title, message)


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
