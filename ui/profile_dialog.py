"""Cadastro ("Como devo te chamar?" + perfil) e Configurações (tema, fonte, texto).

Os dois gravam em core.settings.Settings (config.json). Segue o DESIGN.md:
rótulos de seção em Mono, uma ação principal por diálogo.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QVBoxLayout)

from core.settings import Settings
from ui.hub import Clickable, make_glyph
from ui.style import set_prop
from ui.theme import FONTS, TEXT_SIZES, THEMES, Size, Space, glyph_for
from ui.tools import BY_ID, PROFILES, Profile

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
        tools = ', '.join(BY_ID[i].title for i in profile.favorites[:3])
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
        self.resize(980, 560)

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
