"""Tela simples com barra lateral (layout "sidebar").

Barra lateral na cor de destaque: Favoritos (o início) e um ícone por tipo de
arquivo. No topo, a saudação e a busca; abas com os grupos do tipo escolhido; ao
centro, a grade num painel; à direita, o detalhe da ferramenta com "Abrir
ferramenta" e "Favoritar". O início mostra só os favoritos (Settings.pinned),
que a pessoa edita à vontade; o perfil só sugere os primeiros.

Um clique seleciona, duplo clique (ou Enter no botão) abre.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from ui.hub import ToolCard, _availability, _fold, add_easter_egg, ghost_button, make_glyph
from ui.icons import svg_icon
from ui.style import set_prop
from ui.theme import Color, Size, Space
from ui.tools import BY_ID, CATEGORIES, CATEGORY_BY_ID, CATEGORY_GROUP, GROUPS, PROFILE_BY_ID, Tool

GRID_COLUMNS = 3
NAV_BUTTON = 44   # px
DETAIL_WIDTH = 270
HOME = 'home'


def _file_group(tool: Tool) -> str:
    """Cor do círculo grande do detalhe: a do tipo de arquivo da primeira categoria."""
    for cat in CATEGORIES:
        if tool.id in cat.tools:
            return CATEGORY_GROUP[cat.id]
    return tool.group


class SideHome(QWidget):
    tool_clicked = Signal(str)      # abrir a ferramenta
    category_clicked = Signal(str)  # compatibilidade com a tela de blocos (não usado aqui)
    mode_clicked = Signal()
    settings_clicked = Signal()
    pins_clicked = Signal()
    pin_toggled = Signal(str)

    def __init__(self, apps: dict[str, bool], name: str = '', profile: str = '',
                 pinned: list[str] | None = None):
        super().__init__()
        self.setObjectName('sideHome')
        self.apps = apps
        self.pinned = list(pinned or [])
        prof = PROFILE_BY_ID.get(profile)
        self.section = HOME
        self.group = ''
        self.selected: str | None = None
        self.cards: list[ToolCard] = []

        # --- barra lateral --------------------------------------------------
        self.nav = QFrame()
        self.nav.setObjectName('sideNav')
        nav = QVBoxLayout(self.nav)
        nav.setContentsMargins(Space.MD, Space.LG, Space.MD, Space.LG)
        nav.setSpacing(Space.SM)
        self.nav_group = QButtonGroup(self)
        self.nav_buttons: dict[str, QPushButton] = {}
        order = [(HOME, 'Favoritos', 'star')] + [(c.id, c.title, c.icon) for c in CATEGORIES]
        if prof:  # perfil decide a ordem dos tipos
            rank = {cid: i for i, cid in enumerate(prof.categories)}
            order = order[:1] + sorted(order[1:], key=lambda o: rank.get(o[0], 99))
        for key, label, icon in order:
            btn = QPushButton(svg_icon(icon, Color.TEXT_ON_ACCENT, 22), '')
            btn.setObjectName('navButton')
            btn.setCheckable(True)
            btn.setFixedSize(NAV_BUTTON, NAV_BUTTON)
            btn.setToolTip(label)
            btn.setAccessibleName(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self.show_section(k))
            self.nav_group.addButton(btn)
            self.nav_buttons[key] = btn
            nav.addWidget(btn, 0, Qt.AlignHCenter)
        nav.addStretch(1)
        gear = QPushButton(svg_icon('settings', Color.TEXT_ON_ACCENT, 22), '')
        gear.setObjectName('navButton')
        gear.setFixedSize(NAV_BUTTON, NAV_BUTTON)
        gear.setToolTip('Configurações')
        gear.setAccessibleName('Configurações')
        gear.setCursor(Qt.PointingHandCursor)
        gear.clicked.connect(self.settings_clicked.emit)
        nav.addWidget(gear, 0, Qt.AlignHCenter)

        # --- topo -------------------------------------------------------------
        self.title = QLabel(f'Olá, {name}!' if name else 'Olá!')
        self.title.setObjectName('hubTitle')
        hint = QLabel('Tudo roda neste computador. Solte arquivos em qualquer lugar.')
        hint.setObjectName('hubSubtitle')
        self.search = QLineEdit(placeholderText='Buscar ferramenta…')
        self.search.setObjectName('sideSearch')
        self.search.setClearButtonEnabled(True)
        add_easter_egg(self.search)
        self.search.setFixedWidth(280)
        self.search.textChanged.connect(lambda _: self.refresh())
        self.toggle = ghost_button('Trocar para detalhado', 'arrow-left-right', self.mode_clicked.emit,
                                   'modeToggle')
        top = QHBoxLayout()
        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(self.title)
        texts.addWidget(hint)
        top.addLayout(texts, 1)
        top.addWidget(self.search, 0, Qt.AlignVCenter)
        top.addWidget(self.toggle, 0, Qt.AlignVCenter)

        self.tabs_row = QHBoxLayout()
        self.tabs_row.setSpacing(Space.XL)
        self.tab_group = QButtonGroup(self)
        tabs_box = QWidget()
        tabs_box.setLayout(self.tabs_row)

        # --- painel central ------------------------------------------------------
        self.panel = QFrame()
        self.panel.setObjectName('sidePanel')
        self.panel_title = QLabel()
        self.panel_title.setObjectName('panelTitle')
        self.panel_count = QLabel()
        self.panel_count.setObjectName('homeCount')
        self.grid_box = QWidget()
        self.grid_box.setObjectName('sideGrid')
        self.grid = QGridLayout(self.grid_box)
        self.grid.setContentsMargins(0, 0, Space.SM, 0)
        self.grid.setSpacing(Space.MD)
        for col in range(GRID_COLUMNS):
            self.grid.setColumnStretch(col, 1)
        scroll = QScrollArea()
        scroll.setObjectName('sideScroll')
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self.grid_box)
        self.empty = QLabel('Nenhuma ferramenta encontrada.')
        self.empty.setProperty('tone', 'muted')
        self.empty.setWordWrap(True)
        self.edit_favs = ghost_button('Editar favoritos', 'square-pen', self.pins_clicked.emit, 'pinsButton')
        self.edit_favs.setToolTip('Escolha quais ferramentas ficam nos Favoritos.')
        head = QHBoxLayout()
        head.addWidget(self.panel_title)
        head.addWidget(self.panel_count, 0, Qt.AlignBottom)
        head.addStretch(1)
        head.addWidget(self.edit_favs)
        panel = QVBoxLayout(self.panel)
        panel.setContentsMargins(Space.XL, Space.XL, Space.LG, Space.XL)
        panel.setSpacing(Space.MD)
        panel.addLayout(head)
        panel.addWidget(self.empty)
        panel.addWidget(scroll, 1)

        # --- detalhe -----------------------------------------------------------------
        self.detail = QFrame()
        self.detail.setObjectName('sideDetail')
        self.detail.setFixedWidth(DETAIL_WIDTH)
        self.preview = QFrame()
        self.preview.setObjectName('sidePreview')
        self.preview.setFixedHeight(170)
        self.preview_layout = QVBoxLayout(self.preview)
        self.preview_layout.setAlignment(Qt.AlignCenter)
        self.d_title = QLabel()
        self.d_title.setObjectName('detailTitle')
        self.d_title.setWordWrap(True)
        self.d_group = QLabel()
        self.d_group.setObjectName('homeCount')
        self.d_desc = QLabel()
        self.d_desc.setObjectName('cardDesc')
        self.d_desc.setWordWrap(True)
        self.d_accepts = QLabel()
        self.d_accepts.setObjectName('cardDesc')
        self.d_accepts.setWordWrap(True)
        self.open_btn = QPushButton('Abrir ferramenta')
        self.open_btn.setObjectName('openTool')
        self.open_btn.setProperty('variant', 'primary')
        self.open_btn.setCursor(Qt.PointingHandCursor)
        self.open_btn.clicked.connect(self.open_selected)
        self.pin_btn = QPushButton()
        self.pin_btn.setProperty('variant', 'ghost')
        self.pin_btn.setCursor(Qt.PointingHandCursor)
        self.pin_btn.clicked.connect(self.toggle_pin)
        detail = QVBoxLayout(self.detail)
        detail.setContentsMargins(0, 0, 0, 0)
        detail.setSpacing(Space.SM)
        detail.addWidget(self.preview)
        detail.addSpacing(Space.SM)
        detail.addWidget(self.d_title)
        detail.addWidget(self.d_group)
        detail.addWidget(self.d_desc)
        detail.addWidget(self.d_accepts)
        detail.addStretch(1)
        detail.addWidget(self.pin_btn)
        detail.addWidget(self.open_btn)

        middle = QHBoxLayout()
        middle.setSpacing(Space.XL)
        middle.addWidget(self.panel, 1)
        middle.addWidget(self.detail)

        # --- montagem --------------------------------------------------------------------
        content = QVBoxLayout()
        content.setSpacing(Space.LG)
        content.addLayout(top)
        content.addWidget(tabs_box)
        content.addLayout(middle, 1)
        root = QHBoxLayout(self)
        root.setContentsMargins(Space.XL, Space.XL, Space.XXL, Space.XL)
        root.setSpacing(Space.XXL)
        root.addWidget(self.nav)
        root.addLayout(content, 1)
        self.show_section(HOME)

    # --- navegação ------------------------------------------------------------------------
    def section_tools(self) -> list[Tool]:
        if self.section == HOME:  # só os favoritos, na ordem em que foram escolhidos
            return [BY_ID[i] for i in self.pinned if i in BY_ID and not BY_ID[i].soon]
        return [BY_ID[i] for i in CATEGORY_BY_ID[self.section].tools]

    def show_section(self, key: str):
        self.section = key
        self.group = ''
        self.nav_buttons[key].setChecked(True)
        title = 'Seus favoritos' if key == HOME else CATEGORY_BY_ID[key].title
        self.panel_title.setText(title)
        self.edit_favs.setVisible(key == HOME)
        self._build_tabs()
        self.refresh()

    def _build_tabs(self):
        for btn in self.tab_group.buttons():
            self.tab_group.removeButton(btn)
            btn.hide()  # some na hora; deleteLater só apaga depois
            btn.deleteLater()
        while self.tabs_row.count():
            self.tabs_row.takeAt(0)
        present = {t.group for t in self.section_tools()}
        # em Início são grupos demais para uma linha: lá vale a busca
        names = [''] if self.section == HOME else [''] + [g for g in GROUPS if g in present]
        for g in names:
            btn = QPushButton(g or 'Todas')
            btn.setObjectName('sideTab')
            btn.setCheckable(True)
            btn.setChecked(g == self.group)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, grp=g: self.pick_group(grp))
            self.tab_group.addButton(btn)
            self.tabs_row.addWidget(btn)
        self.tabs_row.addStretch(1)

    def pick_group(self, group: str):
        self.group = group
        self.refresh()

    def visible_tools(self) -> list[Tool]:
        tools = self.section_tools()
        if self.group:
            tools = [t for t in tools if t.group == self.group]
        terms = _fold(self.search.text()).split()
        if terms:
            tools = [t for t in tools if all(term in _fold(f'{t.title} {t.desc} {t.group}') for term in terms)]
        return tools

    def refresh(self):
        for card in self.cards:
            self.grid.removeWidget(card)
            card.hide()
            card.deleteLater()
        self.cards = []
        tools = self.visible_tools()
        for i, tool in enumerate(tools):
            enabled, reason = _availability(tool, self.apps)
            card = ToolCard(tool, enabled, reason)
            card.clicked.connect(self.select)
            card.double_clicked.connect(self.tool_clicked.emit)
            self.grid.addWidget(card, i // GRID_COLUMNS, i % GRID_COLUMNS)
            self.cards.append(card)
        rows = -(-len(tools) // GRID_COLUMNS)
        # o QScrollArea não cresce sozinho com a grade: fixa a altura mínima dela
        self.grid_box.setMinimumHeight(rows * Size.CARD_HEIGHT + max(0, rows - 1) * self.grid.verticalSpacing())
        self.panel_count.setText(f'{len(tools)} FERRAMENTAS')
        if self.section == HOME and not self.pinned:
            self.empty.setText('Nenhum favorito ainda. Clique em "Editar favoritos" ou escolha um tipo de '
                               'arquivo na barra ao lado e use "Favoritar" na ferramenta.')
        else:
            self.empty.setText('Nenhuma ferramenta encontrada.')
        self.empty.setVisible(not tools)
        ready = [t for t in tools if _availability(t, self.apps)[0]]
        if self.selected not in {t.id for t in tools}:
            self.selected = ready[0].id if ready else None
        self.select(self.selected)

    # --- detalhe -----------------------------------------------------------------------------
    def select(self, tool_id: str | None):
        self.selected = tool_id
        for card in self.cards:
            set_prop(card, 'selected', card.tool.id == tool_id)
        tool = BY_ID.get(tool_id) if tool_id else None
        self.detail.setVisible(tool is not None)
        if tool is None:
            return
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        glyph = make_glyph(tool.icon, _file_group(tool), Size.HOME_GLYPH + 16, Size.HOME_GLYPH_ICON + 8,
                           'detailGlyph')
        self.preview_layout.addWidget(glyph, 0, Qt.AlignCenter)
        self.d_title.setText(tool.title)
        self.d_group.setText(tool.group.upper())
        self.d_desc.setText(tool.desc)
        exts = ', '.join(sorted(e.lstrip('.').upper() for e in tool.accepts)) or 'texto digitado'
        self.d_accepts.setText(f'Aceita: {exts}')
        self.pin_btn.setText('Tirar dos favoritos' if tool.id in self.pinned else 'Favoritar')

    def open_selected(self):
        if self.selected:
            self.tool_clicked.emit(self.selected)

    def toggle_pin(self):
        if self.selected:
            self.pin_toggled.emit(self.selected)
