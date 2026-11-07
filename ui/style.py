"""Folha de estilo (QSS) gerada a partir dos tokens de ui/theme.py.

Convenções:
- objectName = papel do widget (card, cardTitle, hub, hubTitle...).
- Variantes e tons são propriedades dinâmicas, nunca objectName:
  variant="primary" | "ghost";  tone="muted" | "error";  state="error";
  disabled=true (cartões).
"""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

from ui.theme import ASSETS, Color as C, Radius as R, Space as S, Type as T

CHECK_SVG = (ASSETS / 'check.svg').as_posix()

QSS = f"""
QMainWindow, QWidget {{ background: {C.BG}; color: {C.TEXT}; font-size: {T.BODY}pt; }}
QToolTip {{ background: {C.SURFACE}; color: {C.TEXT}; border: 1px solid {C.BORDER}; padding: {S.XS}px; }}

/* ---- barra de ferramentas ---- */
QToolBar {{ background: {C.SURFACE}; border: none; border-bottom: 1px solid {C.BORDER};
           padding: {S.SM}px {S.MD}px; spacing: {S.XS}px; }}
QToolBar::separator {{ background: {C.BORDER}; width: 1px; margin: {S.XS}px {S.SM}px; }}
QWidget#toolbarSpacer {{ background: transparent; }}
QToolButton {{ color: {C.TEXT}; padding: {S.XS + 2}px {S.SM}px; border-radius: {R.MD}px;
              background: transparent; border: 1px solid transparent; }}
QToolButton:hover {{ background: {C.BORDER}; }}
QToolButton:pressed {{ background: {C.WINE}; }}
QToolButton:focus {{ border-color: {C.ACCENT}; }}
QToolButton:disabled {{ color: {C.TEXT_DISABLED}; }}
QToolButton[variant="primary"] {{ background: {C.ACCENT}; color: {C.TEXT_ON_ACCENT}; font-weight: 600; }}
QToolButton[variant="primary"]:hover {{ background: {C.ACCENT_HOVER}; }}
QToolButton[variant="primary"]:disabled {{ background: {C.BORDER}; color: {C.TEXT_DISABLED}; }}

/* ---- botões ---- */
QPushButton {{ background: {C.SURFACE}; color: {C.TEXT}; border: 1px solid {C.BORDER};
              border-radius: {R.MD}px; padding: {S.XS + 2}px {S.MD}px; }}
QPushButton:hover {{ border-color: {C.ACCENT}; }}
QPushButton:pressed {{ background: {C.WINE}; }}
QPushButton:focus {{ border-color: {C.ACCENT}; }}
QPushButton:disabled {{ color: {C.TEXT_DISABLED}; border-color: {C.BORDER_DISABLED}; }}
QPushButton[variant="ghost"] {{ background: transparent; }}
QPushButton[variant="primary"] {{ background: {C.ACCENT}; color: {C.TEXT_ON_ACCENT};
                                 border-color: {C.ACCENT}; font-weight: 600; }}
QPushButton[variant="primary"]:hover {{ background: {C.ACCENT_HOVER}; }}

/* ---- texto ---- */
QLabel[tone="muted"] {{ color: {C.TEXT_MUTED}; font-size: {T.CAPTION}pt; background: transparent; }}
QLabel[tone="error"] {{ color: {C.ACCENT}; font-size: {T.CAPTION}pt; font-weight: 600;
                       background: transparent; }}

/* ---- hub ---- */
QScrollArea#hub, QWidget#hubBody {{ background: {C.BG}; border: none; }}
QLabel#hubTitle {{ font-size: {T.TITLE}pt; font-weight: 600; }}
QLabel#hubSubtitle, QLabel#layerHint {{ color: {C.TEXT_MUTED}; font-size: {T.BODY}pt; }}
QLabel#groupHeader {{ color: {C.ACCENT}; font-size: {T.CAPTION}pt; font-weight: 700; letter-spacing: 2px; }}
QLineEdit#hubSearch {{ font-size: {T.BODY_LG}pt; padding: {S.MD}px {S.LG}px; border-radius: {R.LG}px;
                      background: {C.SURFACE}; }}

/* ---- cartão (bloco de ferramenta) ---- */
QFrame#card {{ background: {C.SURFACE}; border: 1px solid {C.BORDER}; border-radius: {R.LG}px; }}
QFrame#card:hover {{ border-color: {C.ACCENT}; background: {C.SURFACE_HOVER}; }}
QFrame#card:focus {{ border: 2px solid {C.ACCENT}; background: {C.SURFACE_HOVER}; }}
QFrame#card[pressed="true"] {{ background: {C.WINE}; }}
QFrame#card[disabled="true"], QFrame#card[disabled="true"]:hover {{
    background: {C.SURFACE_DISABLED}; border: 1px solid {C.BORDER_DISABLED}; }}
QFrame#card QLabel {{ background: transparent; }}
QLabel#cardTitle {{ font-size: {T.BODY_LG}pt; font-weight: 600; }}
QLabel#cardDesc {{ color: {C.TEXT_MUTED}; font-size: {T.CAPTION}pt; }}
QFrame#card[disabled="true"] QLabel#cardTitle {{ color: {C.TEXT_DISABLED}; }}
QFrame#card[disabled="true"] QLabel#cardDesc {{ color: {C.TEXT_DISABLED}; }}
QLabel#glyph {{ border-radius: {R.MD}px; font-size: {T.ICON}pt; font-weight: 700;
               font-family: {T.ICON_FONT}; }}

/* ---- camada de blocos compatíveis ---- */
QFrame#dropLayer {{ background: rgba(24, 26, 47, 225); }}
QFrame#layerPanel {{ background: {C.BG}; border: 1px solid {C.ACCENT}; border-radius: {R.XL}px; }}
QScrollArea#layerScroll {{ background: transparent; border: none; }}
QFrame#layerPanel QWidget {{ background: transparent; }}
QFrame#layerPanel QFrame#card {{ background: {C.SURFACE}; }}
QLabel#fileChip {{ background: {C.WINE}; color: {C.ACCENT}; border-radius: {R.MD}px;
                   padding: {S.SM}px {S.LG}px; font-weight: 600; }}

/* ---- editor ---- */
QLabel#hintBar {{ background: {C.WINE}; color: {C.ACCENT}; padding: {S.SM}px {S.LG}px; }}
QListWidget#thumbnails {{ background: {C.BG}; border: none; outline: 0; color: {C.TEXT_MUTED}; }}
QListWidget#thumbnails::item {{ color: {C.TEXT_MUTED}; border-radius: {R.MD}px; padding: {S.SM}px;
                                border: 2px solid transparent; }}
QListWidget#thumbnails::item:hover {{ background: {C.SURFACE}; }}
QListWidget#thumbnails::item:selected {{ background: {C.WINE}; color: {C.ACCENT};
                                         border: 2px solid {C.ACCENT}; }}
QWidget#viewer, QScrollArea {{ background: {C.BG_SUNKEN}; border: none; }}
QLabel#page {{ background: transparent; }}
QWidget#options {{ background: {C.BG}; }}

/* ---- formulários ---- */
QGroupBox {{ background: {C.SURFACE}; border: 1px solid {C.BORDER}; border-radius: {R.LG}px;
            margin-top: {S.LG}px; padding: {S.MD}px {S.SM}px {S.SM}px {S.SM}px;
            font-weight: 600; color: {C.ACCENT}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: {S.MD}px; padding: 0 {S.XS}px; }}
QGroupBox QLabel, QGroupBox QCheckBox {{ background: transparent; color: {C.TEXT}; font-weight: normal; }}
QLineEdit, QComboBox, QSpinBox {{ background: {C.BG}; color: {C.TEXT}; border: 1px solid {C.BORDER};
                       border-radius: {R.MD}px; padding: {S.XS + 2}px {S.SM}px; font-weight: normal;
                       selection-background-color: {C.WINE}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {C.ACCENT}; }}
QLineEdit:disabled, QComboBox:disabled {{ color: {C.TEXT_DISABLED}; border-color: {C.BORDER_DISABLED}; }}
QLineEdit[state="error"] {{ border: 1px solid {C.DANGER}; background: {C.DANGER_BG}; }}
QComboBox QAbstractItemView {{ background: {C.SURFACE}; color: {C.TEXT};
                              selection-background-color: {C.WINE}; border: 1px solid {C.BORDER}; }}
QCheckBox {{ spacing: {S.SM}px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {C.BORDER};
                       border-radius: {R.SM}px; background: {C.BG}; }}
QCheckBox::indicator:hover {{ border-color: {C.ACCENT}; }}
QCheckBox::indicator:checked {{ background: {C.ACCENT}; border-color: {C.ACCENT}; image: url({CHECK_SVG}); }}
QCheckBox:focus {{ color: {C.ACCENT}; }}

/* ---- estrutura ---- */
QStatusBar {{ background: {C.SURFACE}; border-top: 1px solid {C.BORDER}; color: {C.TEXT_MUTED}; }}
QStatusBar QLabel {{ background: transparent; color: {C.TEXT_MUTED}; }}
QStatusBar::item {{ border: none; }}
QSplitter::handle {{ background: {C.BORDER}; width: 1px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {C.BORDER}; border-radius: {R.SM}px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {C.ACCENT}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {C.BORDER}; border-radius: {R.SM}px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QMessageBox, QDialog, QInputDialog {{ background: {C.BG}; }}
QTableWidget {{ background: {C.SURFACE}; gridline-color: {C.BORDER}; color: {C.TEXT}; }}
QHeaderView::section {{ background: {C.BG}; color: {C.ACCENT}; border: none; padding: {S.SM}px; }}
"""


def set_prop(widget: QWidget, name: str, value) -> None:
    """Muda uma propriedade de estilo e força o Qt a reaplicar o QSS."""
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def apply_style(app: QApplication) -> None:
    app.setStyle('Fusion')
    palette = QPalette()
    for role, color in ((QPalette.Window, C.BG), (QPalette.Base, C.BG), (QPalette.AlternateBase, C.SURFACE),
                        (QPalette.Text, C.TEXT), (QPalette.WindowText, C.TEXT), (QPalette.Button, C.SURFACE),
                        (QPalette.ButtonText, C.TEXT), (QPalette.Highlight, C.WINE),
                        (QPalette.HighlightedText, C.ACCENT), (QPalette.PlaceholderText, C.TEXT_DISABLED),
                        (QPalette.ToolTipBase, C.SURFACE), (QPalette.ToolTipText, C.TEXT)):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(QSS)
