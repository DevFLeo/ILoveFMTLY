"""Cadastro ("Como devo te chamar?" + perfil) e Configurações (tema, fonte, texto).

Os dois gravam em core.settings.Settings (config.json). Segue o DESIGN.md:
rótulos de seção em Mono, uma ação principal por diálogo.
"""

import unicodedata

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout)

from core.settings import Settings
from ui.hub import Clickable, make_glyph
from ui.icons import svg_icon
from ui.style import set_prop
from ui.theme import FONTS, TEXT_SIZES, THEMES, Size, Space, glyph_for
from ui.tools import BY_ID, GROUPS, PROFILES, TOOLS, Profile

MODE_LABELS = {'simple': 'Simples (blocos grandes)', 'detailed': 'Detalhado (todas as ferramentas)'}


def _section(text: str) -> QLabel:
    label = QLabel(text.upper())
    label.setProperty('role', 'section')
    return label


class ProfileCard(Clickable):
    """Cartão de perfil: faixa colorida, ícone redondo, título e o que o perfil traz."""

    def __init__(self, profile: Profile):
        super().__init__(profile.id)
        self.profile = profile
        self.setObjectName('profileCard')
        self.setAccessibleName(f'Perfil {profile.title}')
        bg, _ = glyph_for(profile.group)

        bar = QFrame()
        bar.setFixedHeight(Size.PROFILE_BAR)
        bar.setObjectName('profileBar')
        bar.setStyleSheet(f'background:{bg};')  # cor do perfil vem dos tokens
        glyph = make_glyph(profile.icon, profile.group, Size.HOME_GLYPH, Size.HOME_GLYPH_ICON,
                           'profileGlyph')
        title = QLabel(profile.title, alignment=Qt.AlignCenter)
        title.setObjectName('profileTitle')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.LG, Space.MD, Space.LG, Space.LG)
        layout.setSpacing(Space.SM)
        layout.addWidget(bar)
        layout.addSpacing(Space.SM)
        layout.addWidget(glyph, 0, Qt.AlignHCenter)
        layout.addWidget(title)
        tools = (', '.join(BY_ID[i].title for i in profile.favorites[:3]) if profile.favorites
                 else 'Os cards que você escolher')
        for label, text in (('Objetivo', profile.goal), ('Ideal para', profile.ideal),
                            ('Já vem com', tools)):
            layout.addSpacing(Space.XS)
            head = QLabel(label)
            head.setObjectName('profileLabel')
            body = QLabel(text)
            body.setObjectName('profileText')
            body.setWordWrap(True)
            layout.addWidget(head)
            layout.addWidget(body)
        layout.addStretch(1)

    def set_selected(self, on: bool):
        set_prop(self, 'selected', on)


class WelcomeDialog(QDialog):
    """Cadastro: nome e perfil. Aparece na primeira vez e pelas Configurações."""

    def __init__(self, parent, settings: Settings):
        super().__init__(parent)
        self.setWindowTitle('Bem-vindo ao ILoveFMTLY')
        self.settings = settings
        self.choice = settings.profile

        title = QLabel('Vamos deixar o app com a sua cara')
        title.setObjectName('hubTitle')
        hint = QLabel('Isso fica salvo neste computador. Dá para mudar depois em Configurações.')
        hint.setProperty('tone', 'muted')
        self.name = QLineEdit(settings.name, placeholderText='ex.: Ana')
        self.name.setMaxLength(40)
        self.name.setAccessibleName('Como devo te chamar?')

        grid = QGridLayout()
        grid.setSpacing(Space.LG)
        self.cards: list[ProfileCard] = []
        for i, profile in enumerate(PROFILES):
            card = ProfileCard(profile)
            card.clicked.connect(self.pick)
            grid.addWidget(card, 0, i)
            grid.setColumnStretch(i, 1)
            self.cards.append(card)

        self.later = QPushButton('Agora não')
        self.later.setProperty('variant', 'ghost')
        self.later.clicked.connect(self.reject)
        self.save_btn = QPushButton('Salvar')
        self.save_btn.setProperty('variant', 'primary')
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.accept)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.later)
        buttons.addWidget(self.save_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.XXL, Space.XXL, Space.XXL, Space.XL)
        layout.setSpacing(Space.SM)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addSpacing(Space.XL)
        layout.addWidget(_section('Como devo te chamar?'))
        layout.addWidget(self.name)
        layout.addSpacing(Space.XL)
        layout.addWidget(_section('Você usa o app como?'))
        layout.addLayout(grid)
        layout.addSpacing(Space.XL)
        layout.addLayout(buttons)
        self.pick(self.choice)
        self.resize(1180, 580)

    def pick(self, profile_id: str):
        self.choice = profile_id if any(p.id == profile_id for p in PROFILES) else ''
        for card in self.cards:
            card.set_selected(card.profile.id == self.choice)
        self.save_btn.setEnabled(bool(self.choice))
        self.save_btn.setToolTip('' if self.choice else 'Escolha um perfil.')

    def accept(self):
        if not self.choice:
            return
        self.settings.name = self.name.text().strip()
        self.settings.profile = self.choice
        self.settings.welcomed = 'sim'
        super().accept()

    def reject(self):
        self.settings.welcomed = 'sim'  # não pergunta de novo a cada abertura
        super().reject()


class SettingsDialog(QDialog):
    """Tema, fonte, tamanho do texto, tela inicial e cadastro."""

    def __init__(self, parent, settings: Settings):
        super().__init__(parent)
        self.setWindowTitle('Configurações')
        self.settings = settings

        def combo(options, current):
            box = QComboBox()
            for value, label in options:
                box.addItem(label, value)
            box.setCurrentIndex(max(0, box.findData(current)))
            return box

        self.theme = combo([(t, t) for t in THEMES], settings.theme)
        self.font = combo([(f, f) for f in FONTS], settings.font)
        self.text_size = combo([(s, s) for s in TEXT_SIZES], settings.text_size)
        self.mode = combo(list(MODE_LABELS.items()), settings.mode)
        self.name = QLineEdit(settings.name, placeholderText='ex.: Ana')
        self.name.setMaxLength(40)
        self.profile = combo([('', 'Nenhum')] + [(p.id, p.title) for p in PROFILES], settings.profile)

        def form(*rows):
            f = QFormLayout()
            f.setHorizontalSpacing(Space.LG)
            f.setVerticalSpacing(Space.MD)
            for label, widget in rows:
                f.addRow(label, widget)
            return f

        note = QLabel('Tema, fonte e tamanho do texto valem ao reabrir o app.')
        note.setProperty('tone', 'muted')
        where = QLabel(f'Salvo em: {settings.path}' if settings.path else 'Não salvo em arquivo.')
        where.setProperty('tone', 'muted')
        where.setWordWrap(True)
        where.setTextInteractionFlags(Qt.TextSelectableByMouse)

        cancel = QPushButton('Cancelar')
        cancel.setProperty('variant', 'ghost')
        cancel.clicked.connect(self.reject)
        save = QPushButton('Salvar')
        save.setProperty('variant', 'primary')
        save.setDefault(True)
        save.clicked.connect(self.accept)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(save)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.XXL, Space.XL, Space.XXL, Space.XL)
        layout.setSpacing(Space.SM)
        layout.addWidget(_section('Aparência'))
        layout.addLayout(form(('Tema', self.theme), ('Fonte', self.font),
                              ('Tamanho do texto', self.text_size)))
        layout.addWidget(note)
        layout.addSpacing(Space.XL)
        layout.addWidget(_section('Tela inicial'))
        layout.addLayout(form(('Abrir em', self.mode)))
        layout.addSpacing(Space.XL)
        layout.addWidget(_section('Cadastro'))
        layout.addLayout(form(('Como devo te chamar?', self.name), ('Perfil', self.profile)))
        layout.addSpacing(Space.XL)
        layout.addWidget(where)
        layout.addSpacing(Space.SM)
        layout.addLayout(buttons)
        self.setMinimumWidth(480)
        self.appearance_changed = False

    def accept(self):
        s = self.settings
        before = (s.theme, s.font, s.text_size)
        s.theme, s.font = self.theme.currentData(), self.font.currentData()
        s.text_size, s.mode = self.text_size.currentData(), self.mode.currentData()
        s.name, s.profile = self.name.text().strip(), self.profile.currentData()
        s.welcomed = 'sim'
        self.appearance_changed = (s.theme, s.font, s.text_size) != before
        super().accept()


def _fold(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn')


class PinDialog(QDialog):
    """Perfil Personalizado: marcar os cards que ficam fixados na tela simples."""

    def __init__(self, parent, pinned: list[str]):
        super().__init__(parent)
        self.setWindowTitle('Escolher cards fixados')
        self.search = QLineEdit(placeholderText='Buscar ferramenta…')
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.filter)
        self.list = QListWidget()
        self.list.setObjectName('pinList')
        self.items: dict[str, QListWidgetItem] = {}
        for group in GROUPS:
            tools = [t for t in TOOLS if t.group == group and not t.soon]
            if not tools:
                continue
            header = QListWidgetItem(group.upper())
            header.setFlags(Qt.NoItemFlags)
            header.setData(Qt.UserRole, '')
            self.list.addItem(header)
            for t in tools:
                item = QListWidgetItem(svg_icon(t.icon), f'{t.title}  ·  {t.desc}')
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked if t.id in pinned else Qt.Unchecked)
                item.setData(Qt.UserRole, t.id)
                self.list.addItem(item)
                self.items[t.id] = item
        self.list.itemChanged.connect(self._count)
        self.counter = QLabel()
        self.counter.setProperty('role', 'mono')

        cancel = QPushButton('Cancelar')
        cancel.setProperty('variant', 'ghost')
        cancel.clicked.connect(self.reject)
        save = QPushButton('Fixar cards')
        save.setProperty('variant', 'primary')
        save.setDefault(True)
        save.clicked.connect(self.accept)
        buttons = QHBoxLayout()
        buttons.addWidget(self.counter)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(save)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.XL, Space.XL, Space.XL, Space.XL)
        layout.setSpacing(Space.SM)
        layout.addWidget(_section('Marque os cards que ficam no topo da tela simples'))
        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)
        layout.addSpacing(Space.SM)
        layout.addLayout(buttons)
        self.resize(620, 640)
        self._count()

    def _count(self, *_):
        self.counter.setText(f'{len(self.pinned())} FIXADOS')

    def filter(self, text: str):
        terms = _fold(text).split()
        for tid, item in self.items.items():
            t = BY_ID[tid]
            hay = _fold(f'{t.title} {t.desc} {t.group}')
            item.setHidden(not all(term in hay for term in terms))

    def pinned(self) -> list[str]:
        return [tid for tid, item in self.items.items() if item.checkState() == Qt.Checked]

    @classmethod
    def ask(cls, parent, pinned: list[str]) -> list[str] | None:
        dialog = cls(parent, pinned)
        return dialog.pinned() if dialog.exec() == QDialog.Accepted else None
