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
    'Padrão escuro': {
        'BG': '#0C0C16',
        'SURFACE': '#16162A',
        'BORDER': '#2C2C4A',
        'ACCENT': '#6666FF',
        'ACCENT_TEXT': '#B8BAFF',
        'DANGER': '#E5484D',
        'WINE': '#24245A',
        'BG_SUNKEN': '#08080F',
        'SURFACE_HOVER': '#1E1E3A',
        'SURFACE_DISABLED': '#121222',
        'BORDER_DISABLED': '#1C1C30',
        'ACCENT_HOVER': '#8080FF',
        'DANGER_BG': '#2A1220',
        'TEXT': '#EEF0FF',
        'TEXT_MUTED': '#A9ABD6',
        'TEXT_DISABLED': '#5C5E85',
        'TEXT_ON_ACCENT': '#FFFFFF',
        'TEXT_ON_DANGER': '#FFFFFF',
        'FILE_PDF': '#E5484D',
        'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#C9E8FF',
        'ON_FILE_WORD': '#0C0C16',
        'FILE_EXCEL': '#B9F0D7',
        'ON_FILE_EXCEL': '#0C0C16',
        'FILE_DEV': '#8A8CB8',
        'ON_FILE_DEV': '#0C0C16',
        'FILE_IMAGE': '#EEF0FF',
        'ON_FILE_IMAGE': '#0C0C16',
    },
    'Padrão claro': {
        'BG': '#F4F5FF',
        'SURFACE': '#FFFFFF',
        'BORDER': '#D6D8F5',
        'ACCENT': '#6666FF',
        'ACCENT_TEXT': '#4A4AE0',
        'DANGER': '#C62828',
        'WINE': '#E3E4FF',
        'BG_SUNKEN': '#E9EBFA',
        'SURFACE_HOVER': '#F0F1FF',
        'SURFACE_DISABLED': '#ECEDF7',
        'BORDER_DISABLED': '#E3E4F2',
        'ACCENT_HOVER': '#7A7AFF',
        'DANGER_BG': '#FDE4E4',
        'TEXT': '#0C0C16',
        'TEXT_MUTED': '#4E5070',
        'TEXT_DISABLED': '#A3A5C2',
        'TEXT_ON_ACCENT': '#FFFFFF',
        'TEXT_ON_DANGER': '#FFFFFF',
        'FILE_PDF': '#C62828',
        'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#4A9BD9',
        'ON_FILE_WORD': '#FFFFFF',
        'FILE_EXCEL': '#2E9E6E',
        'ON_FILE_EXCEL': '#FFFFFF',
        'FILE_DEV': '#6B6E99',
        'ON_FILE_DEV': '#FFFFFF',
        'FILE_IMAGE': '#DCDEF5',
        'ON_FILE_IMAGE': '#0C0C16',
    },
    'Tema Claude': {
        'BG': '#1E1A2B',
        'SURFACE': '#2B2438',
        'BORDER': '#453A55',
        'ACCENT': '#E0875F',
        'ACCENT_TEXT': '#F2A27C',
        'DANGER': '#D6455D',
        'WINE': '#4A2233',
        'BG_SUNKEN': '#17141F',
        'SURFACE_HOVER': '#332B42',
        'SURFACE_DISABLED': '#241F30',
        'BORDER_DISABLED': '#2E2738',
        'ACCENT_HOVER': '#F0A07A',
        'DANGER_BG': '#33161F',
        'TEXT': '#F5EEE6',
        'TEXT_MUTED': '#BFB2B8',
        'TEXT_DISABLED': '#76687E',
        'TEXT_ON_ACCENT': '#1E1A2B',
        'TEXT_ON_DANGER': '#F5EEE6',
        'FILE_PDF': '#D6455D',
        'ON_FILE_PDF': '#F5EEE6',
        'FILE_WORD': '#6FB0DA',
        'ON_FILE_WORD': '#1E1A2B',
        'FILE_EXCEL': '#3DA874',
        'ON_FILE_EXCEL': '#1E1A2B',
        'FILE_DEV': '#988CA6',
        'ON_FILE_DEV': '#1E1A2B',
        'FILE_IMAGE': '#F5EEE6',
        'ON_FILE_IMAGE': '#1E1A2B',
    },
    'Umbra & Dreamless Sleep': {
        'BG': '#101011',
        'SURFACE': '#201F20',
        'BORDER': '#565257',
        'ACCENT': '#E5AD14',
        'ACCENT_TEXT': '#E5AD14',
        'DANGER': '#C0392B',
        'WINE': '#3A2A08',
        'BG_SUNKEN': '#0A0A0B',
        'SURFACE_HOVER': '#2A292A',
        'SURFACE_DISABLED': '#18181A',
        'BORDER_DISABLED': '#2E2C2F',
        'ACCENT_HOVER': '#F0BE3A',
        'DANGER_BG': '#2A1210',
        'TEXT': '#F2F0EE',
        'TEXT_MUTED': '#A39DA0',
        'TEXT_DISABLED': '#565257',
        'TEXT_ON_ACCENT': '#101011',
        'TEXT_ON_DANGER': '#FFFFFF',
        'FILE_PDF': '#D9534F',
        'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#8FB3D9',
        'ON_FILE_WORD': '#101011',
        'FILE_EXCEL': '#7FBF8E',
        'ON_FILE_EXCEL': '#101011',
        'FILE_DEV': '#807A7D',
        'ON_FILE_DEV': '#101011',
        'FILE_IMAGE': '#F2F0EE',
        'ON_FILE_IMAGE': '#101011',
    },
    'Soft Spectrum': {
        'BG': '#171213',
        'SURFACE': '#242323',
        'BORDER': '#3D3837',
        'ACCENT': '#A11A17',
        'ACCENT_TEXT': '#E0605C',
        'DANGER': '#FF8A80',
        'WINE': '#3A1514',
        'BG_SUNKEN': '#100C0D',
        'SURFACE_HOVER': '#2E2C2C',
        'SURFACE_DISABLED': '#1D1A1A',
        'BORDER_DISABLED': '#2C2828',
        'ACCENT_HOVER': '#B8241F',
        'DANGER_BG': '#2A1212',
        'TEXT': '#D2CEC7',
        'TEXT_MUTED': '#A29D96',
        'TEXT_DISABLED': '#5E5856',
        'TEXT_ON_ACCENT': '#F4F1EC',
        'TEXT_ON_DANGER': '#171213',
        'FILE_PDF': '#A11A17',
        'ON_FILE_PDF': '#F4F1EC',
        'FILE_WORD': '#8AA9C2',
        'ON_FILE_WORD': '#171213',
        'FILE_EXCEL': '#8DB89A',
        'ON_FILE_EXCEL': '#171213',
        'FILE_DEV': '#8A8480',
        'ON_FILE_DEV': '#171213',
        'FILE_IMAGE': '#D2CEC7',
        'ON_FILE_IMAGE': '#171213',
    },
    'Soft Ambar': {
        'BG': '#1A0D06',
        'SURFACE': '#2A160C',
        'BORDER': '#7A2E0B',
        'ACCENT': '#FFB45C',
        'ACCENT_TEXT': '#FFB45C',
        'DANGER': '#F2552C',
        'WINE': '#4A2410',
        'BG_SUNKEN': '#120804',
        'SURFACE_HOVER': '#361D10',
        'SURFACE_DISABLED': '#22120A',
        'BORDER_DISABLED': '#3D1E0E',
        'ACCENT_HOVER': '#FFD9A3',
        'DANGER_BG': '#3A140A',
        'TEXT': '#FFD9A3',
        'TEXT_MUTED': '#D9A877',
        'TEXT_DISABLED': '#7A5A40',
        'TEXT_ON_ACCENT': '#1A0D06',
        'TEXT_ON_DANGER': '#1A0D06',
        'FILE_PDF': '#D9412B',
        'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#9DB8D9',
        'ON_FILE_WORD': '#1A0D06',
        'FILE_EXCEL': '#A8C98A',
        'ON_FILE_EXCEL': '#1A0D06',
        'FILE_DEV': '#B08A6A',
        'ON_FILE_DEV': '#1A0D06',
        'FILE_IMAGE': '#FFD9A3',
        'ON_FILE_IMAGE': '#1A0D06',
    },
    'Claro': {
        'BG': '#F6F3EF',
        'SURFACE': '#FFFFFF',
        'BORDER': '#D9D3CC',
        'ACCENT': '#C8553D',
        'ACCENT_TEXT': '#C8553D',   # destaque usado como texto/ícone
        'DANGER': '#B4183D',
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
        'FILE_PDF': '#C62828', 'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#3A8FC8', 'ON_FILE_WORD': '#FFFFFF',
        'FILE_EXCEL': '#1E8A4F', 'ON_FILE_EXCEL': '#FFFFFF',
        'FILE_DEV': '#6B7280', 'ON_FILE_DEV': '#FFFFFF',
        'FILE_IMAGE': '#E2DBD3', 'ON_FILE_IMAGE': '#1D2033',
    },
    'Alto contraste': {
        'BG': '#000000',
        'SURFACE': '#121212',
        'BORDER': '#6E6E6E',
        'ACCENT': '#FFD400',
        'ACCENT_TEXT': '#FFD400',   # destaque usado como texto/ícone
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
        'FILE_PDF': '#FF4D4D', 'ON_FILE_PDF': '#000000',
        'FILE_WORD': '#66CCFF', 'ON_FILE_WORD': '#000000',
        'FILE_EXCEL': '#33DD77', 'ON_FILE_EXCEL': '#000000',
        'FILE_DEV': '#BBBBBB', 'ON_FILE_DEV': '#000000',
        'FILE_IMAGE': '#FFFFFF', 'ON_FILE_IMAGE': '#000000',
    },
    'Amarelo': {
        'BG': '#F5F5F5',
        'SURFACE': '#FFFFFF',
        'BORDER': '#D9D9D9',
        'ACCENT': '#FFD24D',
        'ACCENT_TEXT': '#7A5C00',
        'DANGER': '#C62828',
        'WINE': '#FFF1C2',
        'BG_SUNKEN': '#EBEBEB',
        'SURFACE_HOVER': '#FFFBEA',
        'SURFACE_DISABLED': '#F0F0F0',
        'BORDER_DISABLED': '#E6E6E6',
        'ACCENT_HOVER': '#FFDC6E',
        'DANGER_BG': '#FDE4E4',
        'TEXT': '#2B2B2B',
        'TEXT_MUTED': '#6B6B6B',
        'TEXT_DISABLED': '#ABABAB',
        'TEXT_ON_ACCENT': '#4D3A00',
        'TEXT_ON_DANGER': '#FFFFFF',
        'FILE_PDF': '#C62828', 'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#3A8FC8', 'ON_FILE_WORD': '#FFFFFF',
        'FILE_EXCEL': '#1E8A4F', 'ON_FILE_EXCEL': '#FFFFFF',
        'FILE_DEV': '#6B7280', 'ON_FILE_DEV': '#FFFFFF',
        'FILE_IMAGE': '#E4E4E4', 'ON_FILE_IMAGE': '#2B2B2B',
    },
    'SAGA (Unisapiens)': {
        'BG': '#F4F6F9',
        'SURFACE': '#FFFFFF',
        'BORDER': '#D5DCE6',
        'ACCENT': '#F39200',
        'ACCENT_TEXT': '#B45309',
        'DANGER': '#C62828',
        'WINE': '#FFF3E0',
        'BG_SUNKEN': '#E8ECF2',
        'SURFACE_HOVER': '#FFFBF5',
        'SURFACE_DISABLED': '#EEF1F5',
        'BORDER_DISABLED': '#E2E7EE',
        'ACCENT_HOVER': '#C2410C',
        'DANGER_BG': '#FDE4E4',
        'TEXT': '#1A2332',
        'TEXT_MUTED': '#526075',
        'TEXT_DISABLED': '#9BA6B8',
        'TEXT_ON_ACCENT': '#1A2332',
        'TEXT_ON_DANGER': '#FFFFFF',
        'FILE_PDF': '#C62828', 'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#2563EB', 'ON_FILE_WORD': '#FFFFFF',
        'FILE_EXCEL': '#15803D', 'ON_FILE_EXCEL': '#FFFFFF',
        'FILE_DEV': '#475569', 'ON_FILE_DEV': '#FFFFFF',
        'FILE_IMAGE': '#E2E8F0', 'ON_FILE_IMAGE': '#1A2332',
    },
    'Rosa': {
        'BG': '#FFF5F8',
        'SURFACE': '#FFFFFF',
        'BORDER': '#F3D1DC',
        'ACCENT': '#E11D74',
        'ACCENT_TEXT': '#BE185D',
        'DANGER': '#C62828',
        'WINE': '#FCE7F1',
        'BG_SUNKEN': '#F8E8EE',
        'SURFACE_HOVER': '#FFF0F5',
        'SURFACE_DISABLED': '#F7EDF0',
        'BORDER_DISABLED': '#EEDCE2',
        'ACCENT_HOVER': '#F43F8A',
        'DANGER_BG': '#FDE4E4',
        'TEXT': '#2D121E',
        'TEXT_MUTED': '#7A4B60',
        'TEXT_DISABLED': '#B895A4',
        'TEXT_ON_ACCENT': '#FFFFFF',
        'TEXT_ON_DANGER': '#FFFFFF',
        'FILE_PDF': '#C62828', 'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#2563EB', 'ON_FILE_WORD': '#FFFFFF',
        'FILE_EXCEL': '#15803D', 'ON_FILE_EXCEL': '#FFFFFF',
        'FILE_DEV': '#6B5B7B', 'ON_FILE_DEV': '#FFFFFF',
        'FILE_IMAGE': '#F5DCE6', 'ON_FILE_IMAGE': '#2D121E',
    },
    'Verde': {
        'BG': '#0D1912',
        'SURFACE': '#15281E',
        'BORDER': '#284A37',
        'ACCENT': '#2ECC71',
        'ACCENT_TEXT': '#6EE7A0',
        'DANGER': '#E5484D',
        'WINE': '#1E4631',
        'BG_SUNKEN': '#09120D',
        'SURFACE_HOVER': '#1D3628',
        'SURFACE_DISABLED': '#112018',
        'BORDER_DISABLED': '#1F382A',
        'ACCENT_HOVER': '#48D683',
        'DANGER_BG': '#2A1215',
        'TEXT': '#EAF7EF',
        'TEXT_MUTED': '#9CC2AC',
        'TEXT_DISABLED': '#527360',
        'TEXT_ON_ACCENT': '#0D1912',
        'TEXT_ON_DANGER': '#FFFFFF',
        'FILE_PDF': '#E5484D', 'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#7CC4FA', 'ON_FILE_WORD': '#0D1912',
        'FILE_EXCEL': '#5CE6A0', 'ON_FILE_EXCEL': '#0D1912',
        'FILE_DEV': '#8CA899', 'ON_FILE_DEV': '#0D1912',
        'FILE_IMAGE': '#EAF7EF', 'ON_FILE_IMAGE': '#0D1912',
    },
    'Azul': {
        'BG': '#0B1528',
        'SURFACE': '#132340',
        'BORDER': '#264173',
        'ACCENT': '#38BDF8',
        'ACCENT_TEXT': '#7DD3FC',
        'DANGER': '#EF4444',
        'WINE': '#1D3866',
        'BG_SUNKEN': '#070E1B',
        'SURFACE_HOVER': '#1B3057',
        'SURFACE_DISABLED': '#0F1C33',
        'BORDER_DISABLED': '#1D3159',
        'ACCENT_HOVER': '#67CEFA',
        'DANGER_BG': '#2C1219',
        'TEXT': '#F0F7FF',
        'TEXT_MUTED': '#9CB6D9',
        'TEXT_DISABLED': '#526B8F',
        'TEXT_ON_ACCENT': '#0B1528',
        'TEXT_ON_DANGER': '#FFFFFF',
        'FILE_PDF': '#EF4444', 'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#7DD3FC', 'ON_FILE_WORD': '#0B1528',
        'FILE_EXCEL': '#6EE7B7', 'ON_FILE_EXCEL': '#0B1528',
        'FILE_DEV': '#94A3B8', 'ON_FILE_DEV': '#0B1528',
        'FILE_IMAGE': '#F0F7FF', 'ON_FILE_IMAGE': '#0B1528',
    },
    'Roxo': {
        'BG': '#140E24',
        'SURFACE': '#21173B',
        'BORDER': '#3D2B6B',
        'ACCENT': '#A855F7',
        'ACCENT_TEXT': '#D8B4FE',
        'DANGER': '#F43F5E',
        'WINE': '#361E5C',
        'BG_SUNKEN': '#0D0918',
        'SURFACE_HOVER': '#2C1F4D',
        'SURFACE_DISABLED': '#1A122E',
        'BORDER_DISABLED': '#2D204F',
        'ACCENT_HOVER': '#C084FC',
        'DANGER_BG': '#2E1122',
        'TEXT': '#F5F0FF',
        'TEXT_MUTED': '#B5A3D4',
        'TEXT_DISABLED': '#685687',
        'TEXT_ON_ACCENT': '#FFFFFF',
        'TEXT_ON_DANGER': '#FFFFFF',
        'FILE_PDF': '#F43F5E', 'ON_FILE_PDF': '#FFFFFF',
        'FILE_WORD': '#7DD3FC', 'ON_FILE_WORD': '#140E24',
        'FILE_EXCEL': '#6EE7B7', 'ON_FILE_EXCEL': '#140E24',
        'FILE_DEV': '#A799B7', 'ON_FILE_DEV': '#140E24',
        'FILE_IMAGE': '#F5F0FF', 'ON_FILE_IMAGE': '#140E24',
    },
}
DEFAULT_THEME = 'Padrão escuro'
# nomes antigos que podem estar num config.json salvo
THEME_ALIASES = {
    'Noite': 'Tema Claude',
    'SAGA': 'SAGA (Unisapiens)',
    'Unisapiens': 'SAGA (Unisapiens)',
    'Laranja': 'SAGA (Unisapiens)',
}

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
    BG = SURFACE = BORDER = ACCENT = ACCENT_TEXT = DANGER = WINE = ''
    BG_SUNKEN = SURFACE_HOVER = SURFACE_DISABLED = BORDER_DISABLED = ''
    ACCENT_HOVER = DANGER_BG = ''
    TEXT = TEXT_MUTED = TEXT_DISABLED = TEXT_ON_ACCENT = TEXT_ON_DANGER = ''
    FILE_PDF = FILE_WORD = FILE_EXCEL = FILE_DEV = FILE_IMAGE = ''
    ON_FILE_PDF = ON_FILE_WORD = ON_FILE_EXCEL = ON_FILE_DEV = ON_FILE_IMAGE = ''


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


# --- relação de cores ------------------------------------------------------------
# Cada grupo herda a cor do TIPO de arquivo (a mesma do bloco grande da categoria):
# o ícone da ferramenta é uma tinta clara dessa cor com o símbolo na cor cheia.
# Assim PDF fica vermelho do bloco ao card, Word azul, CSV verde, dev cinza.
KIND_OF_GROUP = {
    'Organizar': 'pdf', 'Otimizar': 'pdf', 'PDF para…': 'pdf', '…para PDF': 'pdf', 'Converter': 'pdf',
    'Editar': 'pdf', 'Segurança': 'pdf', 'Word': 'word', 'CSV': 'excel', 'Imagens': 'image',
    **{g: 'dev' for g in ('JSON', 'XML', 'YAML', 'TOML', 'Texto', 'Codificar', 'Cripto', 'QR e códigos',
                          'IA', 'Geradores', 'Web')},
}
TINT = 0.22          # quanto da cor do tipo entra no fundo do ícone
MIN_CONTRAST = 3.0   # WCAG para ícones e texto grande


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a: str, b: str, amount: float) -> str:
    """`amount` de `a` sobre `b` (0 = b, 1 = a)."""
    ra, rb = _rgb(a), _rgb(b)
    return '#' + ''.join(f'{round(x * amount + y * (1 - amount)):02X}' for x, y in zip(ra, rb))


def _lum(h: str) -> float:
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def readable(fg: str, bg: str, toward: str, minimum: float = MIN_CONTRAST) -> str:
    """Aproxima `fg` de `toward` até ter contraste `minimum` sobre `bg`."""
    for step in range(11):
        cand = mix(toward, fg, step / 10)
        if contrast(cand, bg) >= minimum:
            return cand
    return toward


def tonal(kind: str) -> tuple[str, str]:
    """(fundo, símbolo) do ícone de uma ferramenta do tipo `kind`."""
    C = Color
    base = getattr(C, f'FILE_{kind.upper()}')
    bg = mix(base, C.SURFACE, TINT)
    return bg, readable(base, bg, C.TEXT)


def _group_glyph() -> dict[str, tuple[str, str]]:
    C = Color
    glyph = {g: tonal(k) for g, k in KIND_OF_GROUP.items()}
    glyph['Em breve'] = (C.SURFACE_DISABLED, readable(C.TEXT_MUTED, C.SURFACE_DISABLED, C.TEXT))
    # blocos grandes: a cor cheia do tipo, símbolo legível por cima
    for kind in ('pdf', 'word', 'excel', 'dev', 'image'):
        bg = getattr(C, f'FILE_{kind.upper()}')
        fg = getattr(C, f'ON_FILE_{kind.upper()}')
        dark = _lum(bg) > 0.3
        glyph[f'file:{kind}'] = (bg, readable(fg, bg, '#000000' if dark else '#FFFFFF'))
    return glyph


def needs_outline(bg: str) -> bool:
    """Fundo que some no card (ex.: branco das imagens em tema claro) ganha contorno."""
    return contrast(bg, Color.SURFACE) < 1.5


def glyph_for(group: str) -> tuple[str, str]:
    return GROUP_GLYPH.get(group, GROUP_GLYPH['Em breve'])


def apply_appearance(theme: str = DEFAULT_THEME, font: str = Type.SANS,
                     text_size: str = 'Normal') -> tuple[str, str, str]:
    """Aplica tema, fonte e tamanho do texto aos tokens. Valores desconhecidos
    viram o padrão. Devolve o que foi de fato aplicado."""
    theme = THEME_ALIASES.get(theme, theme)
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
