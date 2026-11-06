"""Tela inicial: grade de blocos de ferramentas e a camada de compatíveis.

Ao soltar arquivos no hub, a DropLayer sobe por cima mostrando só os blocos
que aceitam aqueles arquivos.
"""

from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from ui.tools import GROUPS, TOOLS, Tool, compatible

COLUMNS = 4
GLYPH_COLORS = {  # cor do quadradinho do ícone por grupo (paleta do tema)
    'Organizar': ('#FDA481', '#181A2F'),
    'Otimizar': ('#37415C', '#FDA481'),
    'Converter': ('#B4182D', '#F3F4F8'),
    'Editar': ('#54162B', '#FDA481'),
    'Segurança': ('#FDA481', '#54162B'),
    'Em breve': ('#37415C', '#AEB4C8'),
}


class ToolCard(QFrame):
    clicked = Signal(str)

    def __init__(self, tool: Tool, enabled: bool, reason: str = ''):
        super().__init__()
        self.tool = tool
        self.setObjectName('card')
        self.setProperty('disabled', not enabled)
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(132)
        self._enabled = enabled

        bg, fg = GLYPH_COLORS.get(tool.group, GLYPH_COLORS['Em breve'])
        glyph = QLabel(tool.glyph, alignment=Qt.AlignCenter)
        glyph.setObjectName('glyph')
        glyph.setFixedSize(36, 36)
        glyph.setStyleSheet(f'background:{bg}; color:{fg};')

        title = QLabel(tool.title)
        title.setObjectName('cardTitle')
        desc = QLabel(reason or tool.desc)
        desc.setObjectName('cardDesc')
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(6)
        layout.addWidget(glyph)
        layout.addWidget(title)
        layout.addWidget(desc, 1)
        self.setToolTip(reason or tool.desc)

    def mouseReleaseEvent(self, event):
        if self._enabled and event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit(self.tool.id)
        super().mouseReleaseEvent(event)


def _availability(tool: Tool, word_ok: bool) -> tuple[bool, str]:
    if tool.soon:
        return False, ''
    if tool.needs_word and not word_ok:
        return False, 'Requer Microsoft Word instalado.'
    return True, ''


def _card_grid(tools: list[Tool], word_ok: bool, on_click: Callable[[str], None]) -> QWidget:
    box = QWidget()
    grid = QGridLayout(box)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(14)
    for i, tool in enumerate(tools):
        enabled, reason = _availability(tool, word_ok)
        card = ToolCard(tool, enabled, reason)
        card.clicked.connect(on_click)
        grid.addWidget(card, i // COLUMNS, i % COLUMNS)
    for col in range(COLUMNS):
        grid.setColumnStretch(col, 1)
    return box


class HubPage(QScrollArea):
    tool_clicked = Signal(str)

    def __init__(self, word_ok: bool):
        super().__init__()
        self.setObjectName('hub')
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cards: list[ToolCard] = []

        body = QWidget()
        body.setObjectName('hubBody')
        layout = QVBoxLayout(body)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(10)

        title = QLabel('Ferramentas para seus documentos')
        title.setObjectName('hubTitle')
        subtitle = QLabel('Tudo roda neste computador. Solte arquivos em qualquer lugar '
                          'desta tela para ver o que dá para fazer com eles.')
        subtitle.setObjectName('hubSubtitle')
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        for group in GROUPS:
            tools = [t for t in TOOLS if t.group == group]
            if not tools:
                continue
            header = QLabel(group.upper())
            header.setObjectName('groupHeader')
            layout.addSpacing(14)
            layout.addWidget(header)
            grid = _card_grid(tools, word_ok, self.tool_clicked.emit)
            self.cards.extend(grid.findChildren(ToolCard))
            layout.addWidget(grid)
        layout.addStretch(1)
        self.setWidget(body)


class DropLayer(QFrame):
    """Camada que sobe por cima do hub com os blocos compatíveis com os arquivos soltos."""

    tool_chosen = Signal(str, list)

    def __init__(self, parent: QWidget, word_ok: bool):
        super().__init__(parent)
        self.setObjectName('dropLayer')
        self.word_ok = word_ok
        self.files: list[Path] = []
        self.cards: list[ToolCard] = []

        self.panel = QFrame()
        self.panel.setObjectName('layerPanel')
        self.panel.setMaximumWidth(1100)
        self.file_label = QLabel()
        self.file_label.setObjectName('fileChip')
        self.hint = QLabel()
        self.hint.setObjectName('hubSubtitle')
        self.hint.setWordWrap(True)
        cancel = QPushButton('Cancelar', clicked=self.close_layer)
        cancel.setObjectName('ghost')

        top = QHBoxLayout()
        top.addWidget(self.file_label, 1)
        top.addWidget(cancel)

        self.grid_holder = QVBoxLayout()
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(28, 24, 28, 24)
        panel_layout.setSpacing(12)
        panel_layout.addLayout(top)
        panel_layout.addWidget(self.hint)
        panel_layout.addLayout(self.grid_holder)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.addStretch(1)
        outer.addWidget(self.panel, 0, Qt.AlignHCenter)
        outer.addStretch(2)
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
            grid = _card_grid(tools, self.word_ok, lambda tid: self.tool_chosen.emit(tid, self.files))
            self.cards = grid.findChildren(ToolCard)
            self.grid_holder.addWidget(grid)
        else:
            self.cards = []
            self.hint.setText('Nenhuma ferramenta para este formato (ou para esta combinação de arquivos).')

        self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()
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
        if not self.panel.geometry().contains(event.position().toPoint()):
            self.close_layer()
        super().mousePressEvent(event)
