"""Painel com as opções aplicadas na exportação, na divisão e na impressão."""

from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGroupBox,
                               QLabel, QLineEdit, QVBoxLayout, QWidget)

from core.export import ExportOptions
from ui.style import set_prop

COMPRESSION = [('Sem perda (recomendado)', 'lossless'),
               ('Reduzir imagens (com perda)', 'lossy'),
               ('Nenhuma', 'none')]


class OptionsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('options')

        content = QGroupBox('Conteúdo')
        self.page_numbers = QCheckBox('Numerar páginas')
        self.watermark = QLineEdit(placeholderText="Texto da marca d'água")
        form = QFormLayout(content)
        form.addRow(self.page_numbers)
        form.addRow("Marca d'água", self.watermark)

        size = QGroupBox('Tamanho')
        self.compress = QComboBox()
        for label, value in COMPRESSION:
            self.compress.addItem(label, value)
        self.linearize = QCheckBox('Abertura rápida (linearizar)')
        self.linearize.setChecked(True)
        form = QFormLayout(size)
        form.addRow('Compressão', self.compress)
        form.addRow(self.linearize)

        privacy = QGroupBox('Privacidade')
        self.strip_metadata = QCheckBox('Remover metadados')
        self.strip_metadata.setToolTip('Apaga autor, software, datas e XMP do arquivo final')
        self.strip_metadata.setChecked(True)
        self.password = QLineEdit(placeholderText='Deixe vazio para não proteger')
        self.password.setEchoMode(QLineEdit.Password)
        self.password2 = QLineEdit(placeholderText='Repita a senha')
        self.password2.setEchoMode(QLineEdit.Password)
        form = QFormLayout(privacy)
        form.addRow(self.strip_metadata)
        form.addRow('Senha', self.password)
        form.addRow('Confirmar', self.password2)
        self.password_error = QLabel('As senhas não conferem.')
        self.password_error.setProperty('tone', 'error')
        self.password_error.hide()
        form.addRow(self.password_error)
        hint = QLabel('AES-256. Sem a senha, ninguém abre o arquivo — nem o ILoveFMTLY.')
        hint.setWordWrap(True)
        hint.setProperty('tone', 'muted')
        form.addRow(hint)
        self.password.textChanged.connect(self._check_passwords)
        self.password2.textChanged.connect(self._check_passwords)

        layout = QVBoxLayout(self)
        layout.addWidget(content)
        layout.addWidget(size)
        layout.addWidget(privacy)
        layout.addStretch(1)

    def _check_passwords(self) -> bool:
        """Erro inline enquanto a confirmação não bate. Devolve True se ok."""
        pw, pw2 = self.password.text(), self.password2.text()
        mismatch = bool(pw2) and pw != pw2
        set_prop(self.password2, 'state', 'error' if mismatch else '')
        self.password_error.setVisible(mismatch)
        return not mismatch

    def reset(self) -> None:
        """Volta aos padrões (usado ao abrir uma ferramenta pelo hub)."""
        self.page_numbers.setChecked(False)
        self.watermark.clear()
        self.compress.setCurrentIndex(0)
        self.linearize.setChecked(True)
        self.strip_metadata.setChecked(True)
        self.password.clear()
        self.password2.clear()

    def options(self, for_print: bool = False) -> ExportOptions:
        """Lê o painel. Levanta ValueError se as senhas não conferem."""
        pw, pw2 = self.password.text(), self.password2.text()
        if pw != pw2:
            set_prop(self.password2, 'state', 'error')
            self.password_error.show()
            self.password2.setFocus()
            raise ValueError('As senhas não conferem.')
        opts = ExportOptions(
            page_numbers=self.page_numbers.isChecked(),
            watermark=self.watermark.text().strip() or None,
            compress=self.compress.currentData(),
            linearize=self.linearize.isChecked(),
            strip_metadata=self.strip_metadata.isChecked(),
            password=pw or None,
        )
        if for_print:  # impressão só precisa do conteúdo visível
            opts.password, opts.compress, opts.linearize = None, 'none', False
        return opts
