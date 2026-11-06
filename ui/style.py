"""Tema visual (QSS). Será refinado com o Claude Design."""

from PySide6.QtWidgets import QApplication

QSS = """
QMainWindow, QWidget { background: #f6f7f9; color: #1d2330; font-size: 10pt; }
QToolBar { background: #ffffff; border: none; border-bottom: 1px solid #e3e6ec;
           padding: 4px 8px; spacing: 4px; }
QToolButton { padding: 6px 10px; border-radius: 6px; }
QToolButton:hover { background: #eef1f6; }
QToolButton:disabled { color: #a8afbd; }
QListWidget#thumbnails { background: #eceff4; border: none; }
QListWidget#thumbnails::item { color: #5b6475; border-radius: 8px; padding: 6px; }
QListWidget#thumbnails::item:selected { background: #d6e4ff; color: #1d4ed8; }
QScrollArea { border: none; background: #e5e8ee; }
QLabel#page { background: transparent; }
QLabel#muted { color: #6b7385; font-size: 9pt; }
QGroupBox { background: #ffffff; border: 1px solid #e3e6ec; border-radius: 8px;
            margin-top: 14px; padding: 10px 8px 8px 8px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QLineEdit, QComboBox { background: #ffffff; border: 1px solid #d3d8e2; border-radius: 6px;
                       padding: 5px 8px; font-weight: normal; }
QLineEdit:focus, QComboBox:focus { border-color: #2563eb; }
QGroupBox QLabel, QGroupBox QCheckBox { background: transparent; }
QCheckBox { font-weight: normal; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #b8c0cf;
                       border-radius: 4px; background: #ffffff; }
QCheckBox::indicator:checked { background: #2563eb; border-color: #2563eb; }
QListWidget#thumbnails { outline: 0; }
QPushButton#ghost { background: #ffffff; border: 1px solid #d3d8e2; border-radius: 6px; padding: 3px; }
QPushButton#ghost:hover { background: #eef1f6; }
QStatusBar { background: #ffffff; border-top: 1px solid #e3e6ec; color: #4b5363; }
QSplitter::handle { background: #e3e6ec; width: 1px; }
"""


def apply_style(app: QApplication) -> None:
    app.setStyle('Fusion')
    app.setStyleSheet(QSS)
