"""Tokens do design system do ILoveFMTLY.

Fonte única de cores, tipografia, raios e espaçamentos. O QSS (ui/style.py) e
os widgets leem daqui; nenhum outro arquivo deve conter hex ou medidas soltas.

Paleta base: #181A2F #242E49 #37415C #FDA481 #B4182D #54162B
"""

import sys
from pathlib import Path


class Color:
    # paleta
    BG = '#181A2F'          # fundo da janela
    SURFACE = '#242E49'     # cartões, barras, painéis
    BORDER = '#37415C'      # bordas, campos, hover neutro
    ACCENT = '#FDA481'      # destaque, foco, ação principal
    DANGER = '#B4182D'      # perigo e erro (nunca seleção)
    WINE = '#54162B'        # seleção, faixas, detalhes

    # derivados (variações da paleta, não cores novas)
    BG_SUNKEN = '#11132A'        # área de leitura do visualizador
    SURFACE_HOVER = '#2A3554'    # cartão sob o mouse
    SURFACE_DISABLED = '#1E2238' # cartão desativado
    BORDER_DISABLED = '#262C45'
    ACCENT_HOVER = '#FFB898'
    DANGER_BG = '#2A1324'        # fundo de campo com erro

    # texto
    TEXT = '#F3F4F8'
    TEXT_MUTED = '#AEB4C8'
    TEXT_DISABLED = '#6B7390'
    TEXT_ON_ACCENT = BG


class Type:
    CAPTION = 9    # pt: descrições, rótulos secundários
    BODY = 10      # pt: texto padrão
    BODY_LG = 11   # pt: títulos de cartão
    ICON = 16      # pt: glifos dos blocos
    TITLE = 20     # pt: título de tela
    ICON_FONT = '"Segoe UI Symbol", "Segoe UI Emoji", "Segoe UI"'


class Radius:
    SM = 4    # checkbox, scrollbar
    MD = 8    # botões, campos, glifo, miniaturas, chip
    LG = 12   # cartões, grupos
    XL = 16   # painel da camada


class Space:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32
    XXXL = 40


class Size:
    CARD_HEIGHT = 132
    GLYPH = 36
    ICON_BUTTON = 32
    TOOLBAR_ICON = 18
    THEME_GIF = 10   # px, GIF no canto inferior direito


# Glifo por grupo: (fundo, cor do símbolo)
GROUP_GLYPH = {
    'Organizar': (Color.ACCENT, Color.BG),
    'Otimizar': (Color.BORDER, Color.ACCENT),
    'PDF para…': (Color.DANGER, Color.TEXT),
    '…para PDF': (Color.WINE, Color.ACCENT),
    'Converter': (Color.DANGER, Color.TEXT),
    'Imagens': (Color.ACCENT, Color.WINE),
    'Editar': (Color.WINE, Color.ACCENT),
    'Segurança': (Color.ACCENT, Color.WINE),
    'Em breve': (Color.BORDER, Color.TEXT_MUTED),
}


def _base_dir() -> Path:
    """Raiz do app: a pasta do projeto ou, no .exe do PyInstaller, a pasta extraída."""
    frozen = getattr(sys, '_MEIPASS', None)
    if frozen:
        return Path(frozen)
    return Path(__file__).resolve().parent.parent


ASSETS = _base_dir() / 'assets'
