"""Cadastro ("Como devo te chamar?" + perfil) e Configurações (tema, fonte, texto).

Os dois gravam em core.settings.Settings (config.json). Segue o DESIGN.md:
rótulos de seção em Mono, uma ação principal por diálogo.
"""

import unicodedata

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout)

from core import mascot
from core.settings import Settings
from ui.hub import Clickable, make_glyph
from ui.icons import svg_icon
from ui.style import set_prop
from ui.theme import FONTS, TEXT_SIZES, THEME_ALIASES, THEMES, Size, Space, glyph_for
from ui.tools import BY_ID, GROUPS, PROFILE_BY_ID, PROFILES, TOOLS, Profile

MODE_LABELS = {'simple': 'Simples', 'detailed': 'Detalhado (todas as ferramentas)'}
LAYOUT_LABELS = {'sidebar': 'Barra lateral', 'blocks': 'Blocos grandes'}


def apply_profile(settings: Settings, profile_id: str) -> None:
    """O perfil só sugere: os favoritos viram a sugestão do perfil novo apenas se a pessoa
    ainda não mexeu neles (vazios, ou iguais à sugestão do perfil anterior)."""
    old = PROFILE_BY_ID.get(settings.profile)
    new = PROFILE_BY_ID.get(profile_id)
    untouched = not settings.pinned or (old is not None and settings.pinned == list(old.favorites))
    settings.profile = profile_id
    if untouched and new is not None:
        settings.pinned = list(new.favorites)


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
                 else 'Você escolhe tudo')
        for label, text in (('Objetivo', profile.goal), ('Ideal para', profile.ideal),
                            ('Sugere', tools)):
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
        hint = QLabel('O perfil só sugere os primeiros favoritos: você põe e tira ferramentas quando '
                      'quiser. Fica salvo neste computador.')
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
        apply_profile(self.settings, self.choice)
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

        self.theme = combo([(t, t) for t in THEMES], THEME_ALIASES.get(settings.theme, settings.theme))
        self.font = combo([(f, f) for f in FONTS], settings.font)
        self.text_size = combo([(s, s) for s in TEXT_SIZES], settings.text_size)
        self.mascot = combo([(m, mascot.LABELS[m]) for m in mascot.MASCOTS], settings.mascot)
        for i, m in enumerate(mascot.MASCOTS):  # cada opção mostra o próprio mascote
            self.mascot.setItemIcon(i, QIcon(str(mascot.image_file(m))))
        self.mascot.setIconSize(QSize(28, 28))
        self.mode = combo(list(MODE_LABELS.items()), settings.mode)
        self.layout_box = combo(list(LAYOUT_LABELS.items()), settings.layout)
        self.recs = QCheckBox('Mostrar recomendações embaixo (barra lateral)')
        self.recs.setChecked(settings.recommendations != 'não')
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

        note = QLabel('Tema, fonte e tamanho do texto valem ao reabrir o app. O mascote muda na hora '
                      '(janela, barra de tarefas e atalhos).')
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
                              ('Tamanho do texto', self.text_size), ('Mascote', self.mascot)))
        layout.addWidget(note)
        layout.addSpacing(Space.XL)
        layout.addWidget(_section('Tela inicial'))
        layout.addLayout(form(('Abrir em', self.mode), ('Visual da tela simples', self.layout_box)))
        layout.addWidget(self.recs)
        layout.addSpacing(Space.XL)
        layout.addWidget(_section('Cadastro'))
        layout.addLayout(form(('Como devo te chamar?', self.name), ('Perfil', self.profile)))
        layout.addSpacing(Space.XL)
        layout.addWidget(where)
        layout.addSpacing(Space.SM)
        layout.addLayout(buttons)
        self.setMinimumWidth(480)
        self.appearance_changed = self.mascot_changed = False

    def accept(self):
        s = self.settings
        before = (s.theme, s.font, s.text_size)
        s.theme, s.font = self.theme.currentData(), self.font.currentData()
        s.text_size, s.mode = self.text_size.currentData(), self.mode.currentData()
        s.layout = self.layout_box.currentData()
        s.recommendations = 'sim' if self.recs.isChecked() else 'não'
        s.name = self.name.text().strip()
        apply_profile(s, self.profile.currentData())
        s.welcomed = 'sim'
        self.appearance_changed = (s.theme, s.font, s.text_size) != before
        new_mascot = self.mascot.currentData()
        self.mascot_changed = new_mascot != s.mascot
        s.mascot = new_mascot
        super().accept()


def _fold(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn')


class PinDialog(QDialog):
    """Perfil Personalizado: marcar os cards que ficam fixados na tela simples."""

    def __init__(self, parent, pinned: list[str]):
        super().__init__(parent)
        self.initial = list(pinned)
        self.setWindowTitle('Editar favoritos')
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
        save = QPushButton('Salvar favoritos')
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
        layout.addWidget(_section('Marque as ferramentas que ficam nos Favoritos'))
        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)
        layout.addSpacing(Space.SM)
        layout.addLayout(buttons)
        self.resize(620, 640)
        self._count()

    def _count(self, *_):
        self.counter.setText(f'{len(self.pinned())} FAVORITOS')

    def filter(self, text: str):
        terms = _fold(text).split()
        for tid, item in self.items.items():
            t = BY_ID[tid]
            hay = _fold(f'{t.title} {t.desc} {t.group}')
            item.setHidden(not all(term in hay for term in terms))

    def pinned(self) -> list[str]:
        """Mantém a ordem antiga e põe os novos no fim."""
        checked = [tid for tid, item in self.items.items() if item.checkState() == Qt.Checked]
        return [t for t in self.initial if t in checked] + [t for t in checked if t not in self.initial]

    @classmethod
    def ask(cls, parent, pinned: list[str]) -> list[str] | None:
        dialog = cls(parent, pinned)
        return dialog.pinned() if dialog.exec() == QDialog.Accepted else None
