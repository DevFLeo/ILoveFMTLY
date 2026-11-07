"""Tela inicial: grade de blocos de ferramentas, busca e a camada de compatíveis.

Ao soltar arquivos no hub, a DropLayer sobe por cima mostrando só os blocos
que aceitam aqueles arquivos. Os blocos funcionam com teclado: Tab navega,
Enter ou Espaço abrem.
"""

import unicodedata
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from ui.style import set_prop
from ui.theme import GROUP_GLYPH, Size, Space
from ui.tools import GROUPS, OFFICE_LABEL, TOOLS, Tool, compatible

COLUMNS = 4


def _fold(text: str) -> str:
    """Minúsculas sem acento, para a busca ignorar "ç", "ã"..."""
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn')


class ToolCard(QFrame):
    clicked = Signal(str)

    def __init__(self, tool: Tool, enabled: bool, reason: str = ''):
        super().__init__()
        self.tool = tool
        self._enabled = enabled
        self.setObjectName('card')
        self.setProperty('disabled', not enabled)
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        self.setFocusPolicy(Qt.StrongFocus if enabled else Qt.NoFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(Size.CARD_HEIGHT)
        self.setAccessibleName(tool.title)
        self.setAccessibleDescription(reason or tool.desc)

        bg, fg = GROUP_GLYPH.get(tool.group, GROUP_GLYPH['Em breve'])
        glyph = QLabel(tool.glyph, alignment=Qt.AlignCenter)
        glyph.setObjectName('glyph')
        glyph.setFixedSize(Size.GLYPH, Size.GLYPH)
        glyph.setStyleSheet(f'background:{bg}; color:{fg};')  # cor por grupo vem dos tokens

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

    def activate(self):
        if self._enabled:
            self.clicked.emit(self.tool.id)

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


class HubPage(QScrollArea):
    tool_clicked = Signal(str)

    def __init__(self, apps: dict[str, bool]):
        super().__init__()
        self.setObjectName('hub')
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cards: list[ToolCard] = []
        self.sections: list[tuple[QLabel, CardGrid]] = []

        body = QWidget()
        body.setObjectName('hubBody')
        layout = QVBoxLayout(body)
        layout.setContentsMargins(Space.XXXL, Space.XXL, Space.XXXL, Space.XXL)
        layout.setSpacing(Space.SM)

        title = QLabel('Ferramentas para seus documentos')
        title.setObjectName('hubTitle')
        subtitle = QLabel('Tudo roda neste computador. Solte arquivos em qualquer lugar '
                          'desta tela para ver o que dá para fazer com eles.')
        subtitle.setObjectName('hubSubtitle')
        subtitle.setWordWrap(True)
        self.search = QLineEdit(placeholderText='Buscar ferramenta…  (ex.: gif, word, senha, comprimir)')
        self.search.setObjectName('hubSearch')
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.filter)
        self.empty = QLabel('Nenhuma ferramenta encontrada.')
        self.empty.setProperty('tone', 'muted')
        self.empty.hide()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(Space.MD)
        layout.addWidget(self.search)
        layout.addWidget(self.empty)

        for group in GROUPS:
            tools = [t for t in TOOLS if t.group == group]
            if not tools:
                continue
            header = QLabel(group.upper())
            header.setObjectName('groupHeader')
            grid = CardGrid(tools, apps, self.tool_clicked.emit)
            layout.addSpacing(Space.LG)
            layout.addWidget(header)
            layout.addWidget(grid)
            self.cards.extend(grid.cards)
            self.sections.append((header, grid))
        layout.addStretch(1)
        self.setWidget(body)

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
