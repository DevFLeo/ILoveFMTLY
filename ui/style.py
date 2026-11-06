"""Tema visual (QSS) com a paleta do projeto.

bg #181A2F · surface #242E49 · border #37415C · accent #FDA481 ·
danger #B4182D · wine #54162B · texto #F3F4F8 / secundário #AEB4C8
"""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

BG, SURFACE, BORDER = '#181A2F', '#242E49', '#37415C'
ACCENT, DANGER, WINE = '#FDA481', '#B4182D', '#54162B'
TEXT, MUTED = '#F3F4F8', '#AEB4C8'

QSS = f"""
QMainWindow, QWidget {{ background: {BG}; color: {TEXT}; font-size: 10pt; }}
QToolTip {{ background: {SURFACE}; color: {TEXT}; border: 1px solid {BORDER}; padding: 4px; }}

/* barra de ferramentas */
QToolBar {{ background: {SURFACE}; border: none; border-bottom: 1px solid {BORDER};
           padding: 6px 10px; spacing: 4px; }}
QToolBar::separator {{ background: {BORDER}; width: 1px; margin: 4px 6px; }}
QToolButton {{ color: {TEXT}; padding: 6px 10px; border-radius: 8px; background: transparent; }}
QToolButton:hover {{ background: {BORDER}; }}
QToolButton:pressed {{ background: {WINE}; }}
QToolButton:disabled {{ color: #5d6684; }}
QToolButton#primary {{ background: {ACCENT}; color: {BG}; font-weight: 600; }}
QToolButton#primary:hover {{ background: #ffb898; }}
QToolButton#primary:disabled {{ background: {BORDER}; color: #7d859e; }}

/* hub */
QScrollArea#hub, QWidget#hubBody {{ background: {BG}; border: none; }}
QLabel#hubTitle {{ font-size: 20pt; font-weight: 600; color: {TEXT}; }}
QLabel#hubSubtitle {{ color: {MUTED}; font-size: 10.5pt; }}
QLabel#groupHeader {{ color: {ACCENT}; font-size: 9pt; font-weight: 700; letter-spacing: 2px; }}
QFrame#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; }}
QFrame#card:hover {{ border-color: {ACCENT}; background: #2a3554; }}
QFrame#card[disabled="true"] {{ background: #1e2238; border-color: #262c45; }}
QFrame#card[disabled="true"]:hover {{ border-color: #262c45; background: #1e2238; }}
QFrame#card QLabel {{ background: transparent; }}
QFrame#card[disabled="true"] QLabel#cardTitle {{ color: #6b7390; }}
QFrame#card[disabled="true"] QLabel#cardDesc {{ color: #565d78; }}
QLabel#glyph {{ border-radius: 9px; font-size: 16pt; font-weight: 700;
                font-family: "Segoe UI Symbol", "Segoe UI Emoji", "Segoe UI"; }}
QLabel#cardTitle {{ font-size: 11pt; font-weight: 600; color: {TEXT}; }}
QLabel#cardDesc {{ color: {MUTED}; font-size: 9pt; }}

/* camada de blocos compatíveis */
QFrame#dropLayer {{ background: rgba(24, 26, 47, 225); }}
QFrame#layerPanel {{ background: {BG}; border: 1px solid {ACCENT}; border-radius: 18px; }}
QFrame#layerPanel QWidget {{ background: transparent; }}
QFrame#layerPanel QFrame#card {{ background: {SURFACE}; }}
QLabel#fileChip {{ background: {WINE}; color: {ACCENT}; border-radius: 10px;
                   padding: 8px 14px; font-weight: 600; }}

/* editor */
QLabel#hintBar {{ background: {WINE}; color: {ACCENT}; padding: 8px 16px; font-weight: 500; }}
QListWidget#thumbnails {{ background: {BG}; border: none; outline: 0; color: {MUTED}; }}
QListWidget#thumbnails::item {{ color: {MUTED}; border-radius: 10px; padding: 6px; }}
QListWidget#thumbnails::item:hover {{ background: {SURFACE}; }}
QListWidget#thumbnails::item:selected {{ background: {DANGER}; color: {TEXT}; }}
QWidget#viewer, QScrollArea {{ background: #11132a; border: none; }}
QWidget#viewer QLabel#muted {{ background: transparent; }}
QLabel#page {{ background: transparent; }}
QLabel#muted {{ color: {MUTED}; font-size: 9pt; }}
QWidget#options {{ background: {BG}; }}

/* formulários */
QGroupBox {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px;
            margin-top: 16px; padding: 12px 10px 10px 10px; font-weight: 600; color: {ACCENT}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; }}
QGroupBox QLabel, QGroupBox QCheckBox {{ background: transparent; color: {TEXT}; font-weight: normal; }}
QGroupBox QLabel#muted {{ color: {MUTED}; }}
QLineEdit, QComboBox {{ background: {BG}; color: {TEXT}; border: 1px solid {BORDER};
                       border-radius: 8px; padding: 6px 8px; font-weight: normal;
                       selection-background-color: {DANGER}; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox QAbstractItemView {{ background: {SURFACE}; color: {TEXT};
                              selection-background-color: {DANGER}; border: 1px solid {BORDER}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {BORDER};
                       border-radius: 4px; background: {BG}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

QPushButton {{ background: {SURFACE}; color: {TEXT}; border: 1px solid {BORDER};
              border-radius: 8px; padding: 6px 12px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton#ghost {{ background: transparent; }}

QStatusBar {{ background: {SURFACE}; border-top: 1px solid {BORDER}; color: {MUTED}; }}
QStatusBar QLabel {{ background: transparent; color: {MUTED}; }}
QStatusBar::item {{ border: none; }}
QSplitter::handle {{ background: {BORDER}; width: 1px; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 4px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMessageBox, QDialog, QInputDialog {{ background: {BG}; }}
QTableWidget {{ background: {SURFACE}; gridline-color: {BORDER}; color: {TEXT}; }}
QHeaderView::section {{ background: {BG}; color: {ACCENT}; border: none; padding: 6px; }}
"""


def apply_style(app: QApplication) -> None:
    app.setStyle('Fusion')
    palette = QPalette()
    for role, color in ((QPalette.Window, BG), (QPalette.Base, BG), (QPalette.AlternateBase, SURFACE),
                        (QPalette.Text, TEXT), (QPalette.WindowText, TEXT), (QPalette.Button, SURFACE),
                        (QPalette.ButtonText, TEXT), (QPalette.Highlight, DANGER),
                        (QPalette.HighlightedText, TEXT), (QPalette.PlaceholderText, '#6b7390'),
                        (QPalette.ToolTipBase, SURFACE), (QPalette.ToolTipText, TEXT)):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(QSS)
