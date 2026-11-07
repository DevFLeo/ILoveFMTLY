"""Tela simples com barra lateral: seções, abas, seleção, abrir, fixar."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402

from core.settings import Settings  # noqa: E402
from core.workspace import Workspace  # noqa: E402
from ui import dialogs  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.side_home import HOME, SideHome  # noqa: E402
from ui.tools import CATEGORIES, CATEGORY_BY_ID  # noqa: E402


@pytest.fixture
def settings(tmp_path):
    return Settings.load(tmp_path / 'config.json')


@pytest.fixture
def window(qtbot, tmp_path, settings, monkeypatch):
    monkeypatch.setattr(dialogs, 'error', lambda *_: pytest.fail(f'erro inesperado: {_}'))
    monkeypatch.setattr(dialogs, 'info', lambda *_: None)
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False, settings=settings)
    qtbot.addWidget(w)
    w.show()
    return w


def test_sidebar_is_default(window):
    assert isinstance(window.home, SideHome)
    assert window.stack.currentWidget() is window.home and window.on_hub()
    assert set(window.home.nav_buttons) == {HOME} | {c.id for c in CATEGORIES}


def test_home_shows_only_favorites(window, settings):
    assert window.home.cards == [] and not window.home.empty.isHidden()  # sem favoritos ainda
    assert 'Editar favoritos' in window.home.empty.text()
    settings.pinned = ['merge', 'json-format']
    window.rebuild_home()
    assert [c.tool.id for c in window.home.cards] == ['merge', 'json-format']
    assert not window.home.edit_favs.isHidden()
    window.home.nav_buttons['pdf'].click()
    assert window.home.edit_favs.isHidden()


def test_section_tabs_and_search(window):
    home = window.home
    home.nav_buttons['csv'].click()
    assert {c.tool.id for c in home.cards} == set(CATEGORY_BY_ID['csv'].tools)
    tab = next(b for b in home.tab_group.buttons() if b.text() == 'CSV')
    tab.click()
    assert all(c.tool.group == 'CSV' for c in home.cards)
    home.search.setText('sql')
    assert [c.tool.id for c in home.cards] == ['csv-sql']
    home.search.setText('xyz-nada')
    assert home.cards == [] and not home.empty.isHidden() and home.detail.isHidden()


def test_click_selects_double_click_opens(qtbot):
    home = SideHome({}, 'Ana')  # sozinho: na janela, abrir chamaria o seletor de arquivos
    qtbot.addWidget(home)
    home.show()
    home.nav_buttons['pdf'].click()
    card = next(c for c in home.cards if c.tool.id == 'sign')
    qtbot.mouseClick(card, Qt.LeftButton)
    assert home.selected == 'sign' and home.d_title.text() == 'Assinar PDF'
    assert card.property('selected')
    opened = []
    home.tool_clicked.connect(opened.append)
    qtbot.mouseDClick(card, Qt.LeftButton)
    home.open_btn.click()
    assert opened == ['sign', 'sign']


def test_favorite_button_saves_and_shows_on_home(window, settings):
    window.home.nav_buttons['dev'].click()
    window.home.select('hash')
    window.home.pin_btn.click()
    assert Settings.load(settings.path).pinned == ['hash']
    home = window.home  # foi recriada, no mesmo lugar
    assert home.section == 'dev' and home.selected == 'hash'
    assert home.pin_btn.text() == 'Tirar dos favoritos'
    home.nav_buttons['home'].click()
    assert [c.tool.id for c in home.cards] == ['hash']
    home.select('hash')
    home.pin_btn.click()
    assert Settings.load(settings.path).pinned == []


def test_profile_only_suggests_favorites():
    from ui.profile_dialog import apply_profile
    s = Settings()
    apply_profile(s, 'estudante')                       # vazio: recebe a sugestão
    assert s.pinned[:2] == ['merge', 'compress']
    apply_profile(s, 'empresa')                         # não mexeu: troca pela nova sugestão
    assert s.pinned[0] == 'sign'
    s.pinned.append('hash')                             # mexeu: o perfil não apaga mais nada
    apply_profile(s, 'pessoal')
    assert s.pinned[-1] == 'hash' and s.profile == 'pessoal'


def test_layout_switch_in_settings(window, settings, monkeypatch):
    from ui.profile_dialog import SettingsDialog

    def fake_exec(dialog):
        dialog.layout_box.setCurrentIndex(dialog.layout_box.findData('blocks'))
        dialog.accept()
        return SettingsDialog.Accepted
    monkeypatch.setattr(SettingsDialog, 'exec', fake_exec)
    window.open_settings()
    assert not isinstance(window.home, SideHome)
    assert window.stack.currentWidget() is window.home
    assert Settings.load(settings.path).layout == 'blocks'
