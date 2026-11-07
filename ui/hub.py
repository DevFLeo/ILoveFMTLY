"""Telas iniciais: tela simples (blocos grandes), página de categoria e hub detalhado.

- SimpleHome: um bloco grande por tipo de arquivo (PDF, Imagens...), as
  ferramentas favoritas do perfil e o botão "Trocar para detalhado".
- HubPage: grade de blocos com busca. Sem `tools`, mostra todas (modo
  detalhado); com `tools`, vira a página de uma categoria, com "Voltar".
- DropLayer: ao soltar arquivos, sobe por cima mostrando só os blocos que
  aceitam aqueles arquivos.

Os blocos funcionam com teclado: Tab navega, Enter ou Espaço abrem.
"""

import unicodedata
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from ui.icons import svg_icon, svg_pixmap
from ui.style import set_prop
from ui.theme import ASSETS, Size, Space, glyph_for
from ui.tools import (BY_ID, CATEGORIES, CATEGORY_BY_ID, CATEGORY_GROUP, GROUPS, OFFICE_LABEL,
                      PROFILE_BY_ID, TOOLS, Category, Tool, compatible)

COLUMNS = 4
HOME_COLUMNS = 3


def _fold(text: str) -> str:
    """Minúsculas sem acento, para a busca ignorar "ç", "ã"..."""
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn')


class Clickable(QFrame):
    """Bloco clicável por mouse e teclado. Emite `clicked(key)`."""

    clicked = Signal(str)

    def __init__(self, key: str, enabled: bool = True):
        super().__init__()
        self.key = key
        self._enabled = enabled
        self.setProperty('disabled', not enabled)
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        self.setFocusPolicy(Qt.StrongFocus if enabled else Qt.NoFocus)

    def activate(self):
        if self._enabled:
            self.clicked.emit(self.key)

    def mousePressEvent(self, event):
        if self._enabled and event.button() == Qt.LeftButton:
            set_prop(self, 'pressed', True)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        set_prop(self, 'pressed', False)
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.activate()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.activate()
        else:
            super().keyPressEvent(event)


def make_glyph(icon: str, group: str, box: int, size: int, name: str) -> QLabel:
    bg, fg = glyph_for(group)
    glyph = QLabel(alignment=Qt.AlignCenter)
    glyph.setObjectName(name)
    glyph.setFixedSize(box, box)
    glyph.setPixmap(svg_pixmap(icon, fg, size))
    glyph.setStyleSheet(f'background:{bg};')  # cor por grupo vem dos tokens
    return glyph


class ToolCard(Clickable):
    def __init__(self, tool: Tool, enabled: bool, reason: str = ''):
        super().__init__(tool.id, enabled)
        self.tool = tool
        self.setObjectName('card')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(Size.CARD_HEIGHT)
        self.setAccessibleName(tool.title)
        self.setAccessibleDescription(reason or tool.desc)

        glyph = make_glyph(tool.icon, tool.group, Size.GLYPH, Size.GLYPH_ICON, 'glyph')
        title = QLabel(tool.title)
        title.setObjectName('cardTitle')
        desc = QLabel(reason or tool.desc)
        desc.setObjectName('cardDesc')
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.LG, Space.MD, Space.LG, Space.MD)
        layout.setSpacing(Space.SM)
        layout.addWidget(glyph)
        layout.addWidget(title)
        layout.addWidget(desc, 1)
        self.setToolTip(reason or tool.desc)
        self.search_text = _fold(f'{tool.title} {tool.desc} {tool.group} {" ".join(tool.accepts)}')


class HomeCard(Clickable):
    """Bloco grande da tela simples: círculo com ícone, título, resumo e contagem."""

    def __init__(self, category: Category, count: int):
        super().__init__(category.id)
        self.category = category
        self.setObjectName('homeCard')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(Size.HOME_CARD_HEIGHT)
        self.setAccessibleName(category.title)
        self.setAccessibleDescription(category.desc)

        glyph = make_glyph(category.icon, CATEGORY_GROUP[category.id], Size.HOME_GLYPH,
                           Size.HOME_GLYPH_ICON, 'homeGlyph')
        title = QLabel(category.title)
        title.setObjectName('homeTitle')
        desc = QLabel(category.desc)
        desc.setObjectName('cardDesc')
        desc.setWordWrap(True)
        self.count = QLabel(f'{count} FERRAMENTAS')
        self.count.setObjectName('homeCount')

        texts = QVBoxLayout()
        texts.setSpacing(Space.XS)
        texts.addWidget(title)
        texts.addWidget(desc)
        texts.addStretch(1)
        texts.addWidget(self.count)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.XL, Space.XL, Space.XL, Space.XL)
        layout.setSpacing(Space.LG)
        layout.addWidget(glyph, 0, Qt.AlignTop)
        layout.addLayout(texts, 1)


def _availability(tool: Tool, apps: dict[str, bool]) -> tuple[bool, str]:
    if tool.soon:
        return False, ''
    if tool.needs and not apps.get(tool.needs, False):
        return False, f'Requer Microsoft Office instalado ({OFFICE_LABEL[tool.needs]}).'
    return True, ''


class CardGrid(QWidget):
    def __init__(self, tools: list[Tool], apps: dict[str, bool], on_click: Callable[[str], None]):
        super().__init__()
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(Space.MD)
        self.grid.setVerticalSpacing(Space.MD)
        for col in range(COLUMNS):
            self.grid.setColumnStretch(col, 1)
        self.cards: list[ToolCard] = []
        for tool in tools:
            enabled, reason = _availability(tool, apps)
            card = ToolCard(tool, enabled, reason)
            card.clicked.connect(on_click)
            self.cards.append(card)
        self.layout_cards(self.cards)

    def layout_cards(self, visible: list[ToolCard]) -> None:
        for card in self.cards:
            self.grid.removeWidget(card)
            card.hide()
        for i, card in enumerate(visible):
            self.grid.addWidget(card, i // COLUMNS, i % COLUMNS)
            card.show()


def _logo() -> QLabel:
    label = QLabel()
    label.setObjectName('hubLogo')
    label.setAccessibleName('ILoveFMTLY')
    logo = QPixmap(str(ASSETS / 'logo.png'))
    if not logo.isNull():
        dpr = label.devicePixelRatioF()
        logo = logo.scaled(round(Size.LOGO * dpr), round(Size.LOGO * dpr), Qt.KeepAspectRatio,
                           Qt.SmoothTransformation)
        logo.setDevicePixelRatio(dpr)
        label.setPixmap(logo)
    return label


def ghost_button(text: str, icon: str, slot, name: str = '') -> QPushButton:
    btn = QPushButton(svg_icon(icon), text)
    btn.setProperty('variant', 'ghost')
    btn.setCursor(Qt.PointingHandCursor)
    if name:
        btn.setObjectName(name)
    btn.clicked.connect(slot)
    return btn


class _Page(QScrollArea):
    """Base das telas iniciais: rolagem, margens e cabeçalho com mascote."""

    settings_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName('hub')
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName('hubBody')
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(Space.XXXL, Space.XXL, Space.XXXL, Space.XXL)
        self.body.setSpacing(Space.SM)
        self.setWidget(body)

    def _header(self, title: str, subtitle: str, actions: list[QWidget], logo: bool = True):
        self.title = QLabel(title)
        self.title.setObjectName('hubTitle')
        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName('hubSubtitle')
        self.subtitle.setWordWrap(True)
        head = QHBoxLayout()
        head.setSpacing(Space.LG)
        if logo:
            self.logo = _logo()
            head.addWidget(self.logo, 0, Qt.AlignTop)
        texts = QVBoxLayout()
        texts.setSpacing(Space.XS)
        texts.addWidget(self.title)
        texts.addWidget(self.subtitle)
        head.addLayout(texts, 1)
        for w in actions:
            head.addWidget(w, 0, Qt.AlignTop)
        self.body.addLayout(head)


class HubPage(_Page):
    """Grade de blocos com busca. Sem `tools`: todas as ferramentas (modo detalhado).
    Com `tools`: página de uma categoria, com botão "Voltar"."""

    tool_clicked = Signal(str)
    mode_clicked = Signal()
    back_clicked = Signal()

    def __init__(self, apps: dict[str, bool], tools: list[Tool] | None = None, title: str = '',
                 subtitle: str = ''):
        super().__init__()
        self.cards: list[ToolCard] = []
        self.sections: list[tuple[QLabel, CardGrid]] = []
        self.is_category = tools is not None
        tools = TOOLS if tools is None else tools

        if self.is_category:
            back = ghost_button('Voltar', 'arrow-left', self.back_clicked.emit, 'backButton')
            back.setShortcut('Alt+Left')
            back.setToolTip('Voltar para o início (Alt+←)')
            row = QHBoxLayout()
            row.addWidget(back)
            row.addStretch(1)
            self.body.addLayout(row)
            self.body.addSpacing(Space.SM)
            actions = []
        else:
            self.toggle = ghost_button('Trocar para simples', 'arrow-left-right',
                                       self.mode_clicked.emit, 'modeToggle')
            self.toggle.setToolTip('Voltar para os blocos grandes por tipo de arquivo.')
            actions = [self.toggle,
                       ghost_button('Configurações', 'settings', self.settings_clicked.emit)]
        self._header(title or 'Ferramentas para seus documentos',
                     subtitle or 'Tudo roda neste computador. Solte arquivos em qualquer lugar '
                                 'desta tela para ver o que dá para fazer com eles.',
                     actions, logo=not self.is_category)

        self.search = QLineEdit(placeholderText='Buscar ferramenta…  (ex.: gif, word, senha, comprimir)')
        self.search.setObjectName('hubSearch')
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.filter)
        self.empty = QLabel('Nenhuma ferramenta encontrada.')
        self.empty.setProperty('tone', 'muted')
        self.empty.hide()
        self.body.addSpacing(Space.MD)
        self.body.addWidget(self.search)
        self.body.addWidget(self.empty)

        for group in GROUPS:
            in_group = [t for t in tools if t.group == group]
            if not in_group:
                continue
            header = QLabel(group.upper())
            header.setObjectName('groupHeader')
            grid = CardGrid(in_group, apps, self.tool_clicked.emit)
            self.body.addSpacing(Space.LG)
            self.body.addWidget(header)
            self.body.addWidget(grid)
            self.cards.extend(grid.cards)
            self.sections.append((header, grid))
        self.body.addStretch(1)

    def filter(self, text: str) -> int:
        """Mostra só os blocos que casam com a busca. Devolve quantos ficaram."""
        terms = _fold(text).split()
        total = 0
        for header, grid in self.sections:
            visible = [c for c in grid.cards if all(t in c.search_text for t in terms)]
            grid.layout_cards(visible)
            header.setVisible(bool(visible))
            grid.setVisible(bool(visible))
            total += len(visible)
        self.empty.setVisible(total == 0)
        return total


def category_page(apps: dict[str, bool], category_id: str) -> HubPage:
    cat = CATEGORY_BY_ID[category_id]
    return HubPage(apps, [BY_ID[i] for i in cat.tools], cat.title,
                   f'{cat.desc} Escolha uma ferramenta ou solte arquivos aqui.')


class SimpleHome(_Page):
    """Tela simples: blocos grandes por tipo de arquivo + favoritas do perfil."""

    category_clicked = Signal(str)
    tool_clicked = Signal(str)
    mode_clicked = Signal()

    def __init__(self, apps: dict[str, bool], name: str = '', profile: str = ''):
        super().__init__()
        prof = PROFILE_BY_ID.get(profile)
        self._header(f'Olá, {name}!' if name else 'Olá!',
                     'O que você quer fazer hoje? Escolha um tipo de arquivo, '
                     'ou solte arquivos em qualquer lugar desta tela.',
                     [ghost_button('Configurações', 'settings', self.settings_clicked.emit)])

        self.favorites: CardGrid | None = None
        if prof:
            header = QLabel(f'SUAS FERRAMENTAS · {prof.title.upper()}')
            header.setObjectName('groupHeader')
            self.favorites = CardGrid([BY_ID[i] for i in prof.favorites if i in BY_ID], apps,
                                      self.tool_clicked.emit)
            self.body.addSpacing(Space.XL)
            self.body.addWidget(header)
            self.body.addWidget(self.favorites)

        order = list(prof.categories) if prof else []
        order += [c.id for c in CATEGORIES if c.id not in order]
        header = QLabel('O QUE VOCÊ QUER USAR?')
        header.setObjectName('groupHeader')
        grid_box = QWidget()
        grid = QGridLayout(grid_box)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(Space.LG)
        for col in range(HOME_COLUMNS):
            grid.setColumnStretch(col, 1)
        self.home_cards: list[HomeCard] = []
        for i, cid in enumerate(order):
            cat = CATEGORY_BY_ID[cid]
            card = HomeCard(cat, sum(1 for t in cat.tools if not BY_ID[t].soon))
            card.clicked.connect(self.category_clicked.emit)
            grid.addWidget(card, i // HOME_COLUMNS, i % HOME_COLUMNS)
            self.home_cards.append(card)
        self.body.addSpacing(Space.XL)
        self.body.addWidget(header)
        self.body.addWidget(grid_box)
        self.body.addStretch(1)

        self.toggle = ghost_button('Trocar para detalhado', 'arrow-left-right', self.mode_clicked.emit,
                                   'modeToggle')
        self.toggle.setToolTip('Ver todas as ferramentas numa tela só, com busca.')
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.toggle)
        row.addStretch(1)
        self.body.addSpacing(Space.XL)
        self.body.addLayout(row)


class DropLayer(QFrame):
    """Camada que sobe por cima do hub com os blocos compatíveis com os arquivos soltos."""

    tool_chosen = Signal(str, list)

    def __init__(self, parent: QWidget, apps: dict[str, bool]):
        super().__init__(parent)
        self.setObjectName('dropLayer')
        self.apps = apps
        self.files: list[Path] = []
        self.cards: list[ToolCard] = []

        self.panel = QFrame()
        self.panel.setObjectName('layerPanel')
        self.panel.setMaximumWidth(1100)
        self.file_label = QLabel()
        self.file_label.setObjectName('fileChip')
        self.hint = QLabel()
        self.hint.setObjectName('layerHint')
        self.hint.setWordWrap(True)
        cancel = QPushButton('Cancelar', clicked=self.close_layer)
        cancel.setProperty('variant', 'ghost')

        top = QHBoxLayout()
        top.addWidget(self.file_label, 1)
        top.addWidget(cancel)

        self.grid_holder = QVBoxLayout()
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(Space.XL, Space.XL, Space.XL, Space.XL)
        panel_layout.setSpacing(Space.MD)
        panel_layout.addLayout(top)
        panel_layout.addWidget(self.hint)
        panel_layout.addLayout(self.grid_holder)

        scroll = QScrollArea()
        scroll.setWidget(self.panel)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName('layerScroll')
        scroll.setMaximumWidth(1120)

        # centralizado por espaçadores (com alinhamento, o Qt encolhe a rolagem)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(Space.XXXL, Space.XXXL, Space.XXXL, Space.XXXL)
        outer.addStretch(1)
        outer.addWidget(scroll, 100)
        outer.addStretch(1)
        self.hide()

    def show_for(self, files: list[Path]) -> list[Tool]:
        self.files = [Path(f) for f in files]
        tools = compatible(self.files)
        names = ', '.join(f.name for f in self.files[:3])
        if len(self.files) > 3:
            names += f' e mais {len(self.files) - 3}'
        self.file_label.setText(f'📄  {names}')

        while self.grid_holder.count():
            item = self.grid_holder.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if tools:
            self.hint.setText('O que você quer fazer com este arquivo?' if len(self.files) == 1
                              else 'O que você quer fazer com estes arquivos?')
            grid = CardGrid(tools, self.apps, lambda tid: self.tool_chosen.emit(tid, self.files))
            self.cards = grid.cards
            self.grid_holder.addWidget(grid)
        else:
            self.cards = []
            self.hint.setText('Nenhuma ferramenta para este formato (ou para esta combinação de arquivos).')

        self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()
        focusable = [c for c in self.cards if c.focusPolicy() != Qt.NoFocus]
        (focusable[0] if focusable else self).setFocus()
        return tools

    def close_layer(self):
        self.hide()
        self.files = []

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_layer()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # clique fora do painel fecha a camada
        if not self.panel.geometry().contains(self.panel.parentWidget().mapFrom(self, event.position().toPoint())):
            self.close_layer()
        super().mousePressEvent(event)
