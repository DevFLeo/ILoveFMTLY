"""Tokens do design system do ILoveFMTLY.

Fonte única de cores, tipografia, raios e espaçamentos. O QSS (ui/style.py) e
os widgets leem daqui; nenhum outro arquivo deve conter hex ou medidas soltas.

Temas: cada tema em THEMES define todos os tokens de cor. Para criar ou mudar
um tema, edite só o dicionário dele. apply_appearance() aplica tema, fonte e
tamanho do texto antes de a janela ser criada (a troca vale ao reabrir o app).
"""

from core.paths import assets

# Cada tema tem exatamente estas chaves (teste test_themes_complete).
THEMES: dict[str, dict[str, str]] = {
    'Noite': {
        # paleta base: #181A2F #242E49 #37415C #FDA481 #B4182D #54162B
        'BG': '#181A2F',               # fundo da janela
        'SURFACE': '#242E49',          # cartões, barras, painéis
        'BORDER': '#37415C',           # bordas, campos, hover neutro
        'ACCENT': '#FDA481',           # destaque, foco, ação principal
        'DANGER': '#B4182D',           # perigo e erro (nunca seleção)
        'WINE': '#54162B',             # seleção, faixas, detalhes
        'BG_SUNKEN': '#11132A',        # área de leitura do visualizador
        'SURFACE_HOVER': '#2A3554',    # cartão sob o mouse
        'SURFACE_DISABLED': '#1E2238',  # cartão desativado
        'BORDER_DISABLED': '#262C45',
        'ACCENT_HOVER': '#FFB898',
        'DANGER_BG': '#2A1324',        # fundo de campo com erro
        'TEXT': '#F3F4F8',
        'TEXT_MUTED': '#AEB4C8',
        'TEXT_DISABLED': '#6B7390',
        'TEXT_ON_ACCENT': '#181A2F',
        'TEXT_ON_DANGER': '#F3F4F8',
    },
    'Claro': {
        'BG': '#F6F3EF',
        'SURFACE': '#FFFFFF',
        'BORDER': '#D9D3CC',
        'ACCENT': '#C8553D',
        'DANGER': '#B4182D',
        'WINE': '#F3D9CF',
        'BG_SUNKEN': '#ECE7E1',
        'SURFACE_HOVER': '#FBF4EF',
        'SURFACE_DISABLED': '#F0ECE8',
        'BORDER_DISABLED': '#E6E1DB',
        'ACCENT_HOVER': '#D96A52',
        'DANGER_BG': '#FBE3E6',
        'TEXT': '#1D2033',
        'TEXT_MUTED': '#5B6178',
        'TEXT_DISABLED': '#A3A7B6',
        'TEXT_ON_ACCENT': '#FFFFFF',
        'TEXT_ON_DANGER': '#FFFFFF',
    },
    'Alto contraste': {
        'BG': '#000000',
        'SURFACE': '#121212',
        'BORDER': '#6E6E6E',
        'ACCENT': '#FFD400',
        'DANGER': '#FF4D4D',
        'WINE': '#3A2E00',
        'BG_SUNKEN': '#000000',
        'SURFACE_HOVER': '#1F1F1F',
        'SURFACE_DISABLED': '#0A0A0A',
        'BORDER_DISABLED': '#3A3A3A',
        'ACCENT_HOVER': '#FFE45C',
        'DANGER_BG': '#2A0000',
        'TEXT': '#FFFFFF',
        'TEXT_MUTED': '#D9D9D9',
        'TEXT_DISABLED': '#8C8C8C',
        'TEXT_ON_ACCENT': '#000000',
        'TEXT_ON_DANGER': '#000000',
    },
}
DEFAULT_THEME = 'Noite'

# Assinatura: tinta e papel fixos (vão para o PDF, não mudam com o tema).
INK = '#1A2A6C'
PAPER = '#FFFFFF'

# Fator sobre a escala de texto (Type) e as alturas que dependem dela.
TEXT_SIZES = {'Pequeno': 0.9, 'Normal': 1.0, 'Grande': 1.15, 'Muito grande': 1.3}

# Fontes oferecidas nas Configurações. As IBM Plex vêm embutidas; as outras
# são do Windows (se faltarem, o Qt usa uma parecida).
FONTS = ('IBM Plex Sans', 'IBM Plex Mono', 'Segoe UI', 'Arial', 'Verdana', 'Georgia')


class Color:
    """Cores do tema ativo. Os valores vêm de THEMES (padrão: Noite)."""
    BG = SURFACE = BORDER = ACCENT = DANGER = WINE = ''
    BG_SUNKEN = SURFACE_HOVER = SURFACE_DISABLED = BORDER_DISABLED = ''
    ACCENT_HOVER = DANGER_BG = ''
    TEXT = TEXT_MUTED = TEXT_DISABLED = TEXT_ON_ACCENT = TEXT_ON_DANGER = ''


class Type:
    CAPTION = 9    # pt: descrições, rótulos secundários
    BODY = 10      # pt: texto padrão
    BODY_LG = 11   # pt: títulos de cartão
    HEADING = 15   # pt: títulos dos blocos grandes (tela simples)
    TITLE = 20     # pt: título de tela
    SANS = 'IBM Plex Sans'   # texto, títulos, botões (assets/fonts, OFL)
    MONO = 'IBM Plex Mono'   # números, tempos, tamanhos, rótulos em maiúsculas


class Radius:
    XS = 3    # scrollbar (6 px de largura: pílula), trilho do recorte de vídeo
    SM = 5    # checkbox
    MD = 12   # botões, campos, glifo, miniaturas, chip
    LG = 18   # cartões, grupos, busca
    XL = 24   # painel da camada, blocos grandes


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
    GLYPH_ICON = 20  # ícone SVG dentro do quadrado do bloco
    HOME_CARD_HEIGHT = 168   # bloco grande da tela simples
    HOME_GLYPH = 56          # círculo do ícone no bloco grande
    HOME_GLYPH_ICON = 28
    PROFILE_BAR = 4          # faixa colorida no topo do cartão de perfil
    ICON_BUTTON = 32
    TOOLBAR_ICON = 18
    LOGO = 56        # px, mascote no topo do hub
    THEME_GIF = 10   # px, GIF no canto inferior direito


_BASE_TYPE = {k: getattr(Type, k) for k in ('CAPTION', 'BODY', 'BODY_LG', 'HEADING', 'TITLE')}
_BASE_SIZE = {k: getattr(Size, k) for k in ('CARD_HEIGHT', 'HOME_CARD_HEIGHT')}

# Glifo por grupo: (fundo, cor do símbolo). Preenchido por apply_appearance().
GROUP_GLYPH: dict[str, tuple[str, str]] = {}


def _group_glyph() -> dict[str, tuple[str, str]]:
    C = Color
    return {
        'Organizar': (C.ACCENT, C.BG),
        'Otimizar': (C.BORDER, C.ACCENT),
        'PDF para…': (C.DANGER, C.TEXT_ON_DANGER),
        '…para PDF': (C.WINE, C.ACCENT),
        'Converter': (C.DANGER, C.TEXT_ON_DANGER),
        'Word': (C.SURFACE_HOVER, C.ACCENT),
        'Imagens': (C.ACCENT, C.WINE),
        'Editar': (C.WINE, C.ACCENT),
        'Segurança': (C.ACCENT, C.WINE),
        'Em breve': (C.BORDER, C.TEXT_MUTED),
    }


def glyph_for(group: str) -> tuple[str, str]:
    return GROUP_GLYPH.get(group, GROUP_GLYPH['Em breve'])


def apply_appearance(theme: str = DEFAULT_THEME, font: str = Type.SANS,
                     text_size: str = 'Normal') -> tuple[str, str, str]:
    """Aplica tema, fonte e tamanho do texto aos tokens. Valores desconhecidos
    viram o padrão. Devolve o que foi de fato aplicado."""
    theme = theme if theme in THEMES else DEFAULT_THEME
    for key, value in THEMES[theme].items():
        setattr(Color, key, value)
    font = font if font in FONTS else FONTS[0]
    Type.SANS = font
    text_size = text_size if text_size in TEXT_SIZES else 'Normal'
    factor = TEXT_SIZES[text_size]
    for key, value in _BASE_TYPE.items():
        setattr(Type, key, max(7, round(value * factor)))
    for key, value in _BASE_SIZE.items():
        setattr(Size, key, round(value * max(1.0, factor)))
    GROUP_GLYPH.clear()
    GROUP_GLYPH.update(_group_glyph())
    return theme, font, text_size


apply_appearance()

ASSETS = assets()  # pasta do projeto ou, no .exe, a pasta extraída (core/paths.py)
