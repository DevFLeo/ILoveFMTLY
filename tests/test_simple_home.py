"""Tela simples, páginas de categoria, cadastro, configurações e temas."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import json  # noqa: E402

import pymupdf  # noqa: E402
import pytest  # noqa: E402
from PySide6.QtCore import QPointF, Qt  # noqa: E402
from PySide6.QtWidgets import QFileDialog  # noqa: E402

from core.settings import Settings  # noqa: E402
from core.workspace import Workspace  # noqa: E402
from ui import dialogs, theme  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.pdf_dialogs import FormsDialog, SignDialog  # noqa: E402
from ui.profile_dialog import SettingsDialog, WelcomeDialog  # noqa: E402
from ui.tools import BY_ID, CATEGORIES, PROFILES, TOOLS  # noqa: E402


@pytest.fixture
def settings(tmp_path):
    s = Settings.load(tmp_path / 'config.json')
    s.layout = 'blocks'  # estes testes cobrem a tela de blocos; a barra lateral está em test_side_home.py
    return s


@pytest.fixture
def window(qtbot, tmp_path, settings, monkeypatch):
    monkeypatch.setattr(dialogs, 'error', lambda *_: pytest.fail(f'erro inesperado: {_}'))
    monkeypatch.setattr(dialogs, 'info', lambda *_: None)
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False, settings=settings)
    qtbot.addWidget(w)
    w.show()
    return w


# --- categorias -------------------------------------------------------------
def test_every_ready_tool_is_in_a_category():
    covered = {i for c in CATEGORIES for i in c.tools}
    assert {t.id for t in TOOLS if not t.soon} <= covered
    assert all(i in BY_ID for i in covered)


def test_profiles_point_to_real_tools_and_categories():
    cats = {c.id for c in CATEGORIES}
    for p in PROFILES:
        assert all(i in BY_ID and not BY_ID[i].soon for i in p.favorites)
        assert set(p.categories) == cats


# --- tela simples -----------------------------------------------------------
def test_opens_on_simple_home(window):
    assert window.stack.currentWidget() is window.home
    assert window.on_hub()
    assert [c.key for c in window.home.home_cards] == [c.id for c in CATEGORIES]
    assert window.home.favorites.cards == []  # sem favoritos ainda, mas dá para editar


def test_category_shows_only_its_tools_and_goes_back(window, qtbot):
    pdf_card = next(c for c in window.home.home_cards if c.key == 'pdf')
    qtbot.mouseClick(pdf_card, Qt.LeftButton)
    page = window.category
    assert window.stack.currentWidget() is page and window.on_hub()
    ids = {c.tool.id for c in page.cards}
    assert 'merge' in ids and 'imgconvert' not in ids and 'video2gif' not in ids
    page.back_clicked.emit()
    assert window.stack.currentWidget() is window.home


def test_toggle_mode_is_saved(window, settings):
    window.home.toggle.click()
    assert window.stack.currentWidget() is window.hub
    assert json.loads(settings.path.read_text(encoding='utf-8'))['mode'] == 'detailed'
    window.hub.toggle.click()
    assert window.stack.currentWidget() is window.home
    assert Settings.load(settings.path).mode == 'simple'


def test_home_button_returns_to_chosen_mode(window, make_pdf):
    window.run_tool('organize', [make_pdf(1)])
    assert not window.on_hub()
    window.act_home.trigger()
    assert window.stack.currentWidget() is window.home


def test_profile_favorites_and_greeting(qtbot, tmp_path):
    s = Settings(name='Ana', profile='instituicao', layout='blocks', pinned=['sign', 'redact', 'forms'])
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False, settings=s)
    qtbot.addWidget(w)
    assert w.home.title.text() == 'Olá, Ana!'
    favs = [c.tool.id for c in w.home.favorites.cards]
    assert favs[:3] == ['sign', 'redact', 'forms']


# --- cadastro e configurações -----------------------------------------------
def test_welcome_saves_name_and_profile(window, settings, monkeypatch):
    def fake_exec(dialog):
        dialog.name.setText('  Bruno ')
        dialog.pick('empresa')
        dialog.accept()
        return WelcomeDialog.Accepted
    monkeypatch.setattr(WelcomeDialog, 'exec', fake_exec)
    window.maybe_welcome()
    saved = Settings.load(settings.path)
    assert (saved.name, saved.profile, saved.welcomed) == ('Bruno', 'empresa', 'sim')
    assert saved.pinned[:2] == ['sign', 'pdf2excel']  # sugestão do perfil
    assert window.home.title.text() == 'Olá, Bruno!'
    window.maybe_welcome()  # segunda vez: não pergunta (exec não seria chamado de novo)


def test_welcome_needs_profile(qtbot, settings):
    d = WelcomeDialog(None, settings)
    qtbot.addWidget(d)
    assert not d.save_btn.isEnabled()
    d.pick('estudante')
    assert d.save_btn.isEnabled()
    assert [c.property('selected') for c in d.cards].count(True) == 1


def test_welcome_later_does_not_ask_again(window, settings, monkeypatch):
    monkeypatch.setattr(WelcomeDialog, 'exec', lambda d: d.reject() or WelcomeDialog.Rejected)
    window.maybe_welcome()
    assert Settings.load(settings.path).welcomed == 'sim'
    assert not Settings.load(settings.path).registered


def test_settings_dialog_flags_appearance(qtbot, settings):
    d = SettingsDialog(None, settings)
    qtbot.addWidget(d)
    d.mode.setCurrentIndex(d.mode.findData('detailed'))
    d.accept()
    assert settings.mode == 'detailed' and not d.appearance_changed
    d = SettingsDialog(None, settings)
    qtbot.addWidget(d)
    d.theme.setCurrentIndex(d.theme.findData('Claro'))
    d.accept()
    assert settings.theme == 'Claro' and d.appearance_changed


# --- temas --------------------------------------------------------------------
def test_themes_complete():
    keys = set(theme.THEMES[theme.DEFAULT_THEME])
    assert all(set(t) == keys for t in theme.THEMES.values())


def test_apply_appearance_and_back():
    try:
        assert theme.apply_appearance('Claro', 'Arial', 'Grande') == ('Claro', 'Arial', 'Grande')
        assert theme.Color.BG == theme.THEMES['Claro']['BG']
        assert theme.Type.SANS == 'Arial' and theme.Type.BODY > 10
        assert theme.GROUP_GLYPH['Organizar'] == theme.tonal('pdf')  # grupo segue o tipo de arquivo
        assert theme.apply_appearance('xyz', 'Comic', 'Gigante') == ('Padrão escuro', 'IBM Plex Sans', 'Normal')
        assert theme.apply_appearance('Noite')[0] == 'Tema Claude'  # nome antigo
    finally:
        theme.apply_appearance()
    assert theme.Type.BODY == 10 and theme.Color.BG == theme.THEMES['Padrão escuro']['BG']


# --- assinar, formulário, tarja ----------------------------------------------
def test_sign_flow(window, qtbot, make_pdf, tmp_path, monkeypatch):
    out = tmp_path / 'assinado.pdf'
    real_values = {}

    def fake_ask(cls, parent, src, kind):
        d = cls(parent, src)
        qtbot.addWidget(d)
        pad = d.pad
        qtbot.mousePress(pad, Qt.LeftButton, pos=pad.rect().center() - pad.rect().center() / 2)
        pad.paths[-1].lineTo(QPointF(300, 120))
        qtbot.mouseRelease(pad, Qt.LeftButton)
        assert d.primary.isEnabled()
        real_values.update(d.values())
        return real_values
    monkeypatch.setattr(SignDialog, 'ask', classmethod(fake_ask))
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(out), ''))
    window.run_tool('sign', [make_pdf(2)])
    qtbot.waitUntil(lambda: out.exists() and not window.is_busy(), timeout=10000)
    assert real_values['signature'].startswith(b'\x89PNG')
    with pymupdf.open(out) as doc:
        assert len(doc[1].get_images()) == 1


def test_forms_flow(window, qtbot, tmp_path, monkeypatch):
    src = tmp_path / 'f.pdf'
    doc = pymupdf.open()
    page = doc.new_page()
    w = pymupdf.Widget()
    w.field_name, w.field_type, w.rect = 'nome', pymupdf.PDF_WIDGET_TYPE_TEXT, pymupdf.Rect(72, 72, 300, 92)
    page.add_widget(w)
    doc.save(src)
    doc.close()
    out = tmp_path / 'ok.pdf'

    def fake_ask(cls, parent, path, kind):
        d = cls(parent, path)
        qtbot.addWidget(d)
        d.inputs['nome'].setText('Carla')
        return d.values()
    monkeypatch.setattr(FormsDialog, 'ask', classmethod(fake_ask))
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(out), ''))
    window.run_tool('forms', [src])
    qtbot.waitUntil(lambda: out.exists() and not window.is_busy(), timeout=10000)
    with pymupdf.open(out) as d:
        assert next(d[0].widgets()).field_value == 'Carla'


def test_redact_flow(window, qtbot, make_pdf, tmp_path, monkeypatch):
    out = tmp_path / 'tarjado.pdf'
    monkeypatch.setattr(dialogs.ParamDialog, 'ask', classmethod(
        lambda cls, *a: {'terms': 'Página 1', 'docs': 'Não', 'contacts': 'Não'}))
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(out), ''))
    window.run_tool('redact', [make_pdf(2)])
    qtbot.waitUntil(lambda: out.exists() and not window.is_busy(), timeout=10000)
    with pymupdf.open(out) as d:
        assert 'Página 1' not in d[0].get_text() and 'Página 2' in d[1].get_text()


# --- perfil Personalizado ---------------------------------------------------
def test_edit_favorites_on_blocks(window, settings, monkeypatch):
    from ui.profile_dialog import PinDialog
    window.rebuild_home()
    assert window.home.pins_button is not None  # qualquer perfil (ou nenhum) edita
    assert window.home.favorites.cards == []
    monkeypatch.setattr(PinDialog, 'ask', classmethod(lambda cls, parent, pinned: ['sign', 'merge']))
    window.home.pins_button.click()
    assert [c.tool.id for c in window.home.favorites.cards] == ['sign', 'merge']
    assert Settings.load(settings.path).pinned == ['sign', 'merge']


def test_pin_dialog_checks_and_filters(qtbot):
    from ui.profile_dialog import PinDialog
    d = PinDialog(None, ['merge'])
    qtbot.addWidget(d)
    assert d.pinned() == ['merge']
    d.items['sign'].setCheckState(Qt.Checked)
    assert d.pinned() == ['merge', 'sign'] and d.counter.text() == '2 FAVORITOS'
    d.filter('assin')
    assert not d.items['sign'].isHidden() and d.items['merge'].isHidden()
    assert 'ocr' not in d.items  # "em breve" não pode ser fixado


def test_welcome_custom_asks_pins(window, settings, monkeypatch):
    from ui.profile_dialog import PinDialog

    def fake_exec(dialog):
        dialog.pick('personalizado')
        dialog.accept()
        return WelcomeDialog.Accepted
    monkeypatch.setattr(WelcomeDialog, 'exec', fake_exec)
    monkeypatch.setattr(PinDialog, 'ask', classmethod(lambda cls, parent, pinned: ['redact']))
    window.maybe_welcome()
    assert Settings.load(settings.path).pinned == ['redact']
    assert [c.tool.id for c in window.home.favorites.cards] == ['redact']


def test_every_theme_glyph_is_readable():
    """Relação de cores: todo ícone (grupo ou bloco) passa de 3:1 em todos os temas,
    e cada grupo usa a cor do tipo de arquivo."""
    try:
        for name in theme.THEMES:
            theme.apply_appearance(name)
            for group, (bg, fg) in theme.GROUP_GLYPH.items():
                assert theme.contrast(bg, fg) >= 3.0, (name, group)
            pdf_bg, _ = theme.GROUP_GLYPH['Organizar']
            assert pdf_bg == theme.mix(theme.Color.FILE_PDF, theme.Color.SURFACE, theme.TINT)
    finally:
        theme.apply_appearance()
