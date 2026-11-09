"""Regras do design system: tokens centralizados, teclado e estados."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import re  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402

from core.settings import Settings  # noqa: E402
from core.workspace import Workspace  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.theme import GROUP_GLYPH  # noqa: E402
from ui.tools import GROUPS, TOOLS  # noqa: E402

UI = Path(__file__).resolve().parent.parent / 'ui'
HEX = re.compile(r'#[0-9A-Fa-f]{6}\b')


def test_no_hex_outside_theme():
    offenders = {f.name: HEX.findall(f.read_text(encoding='utf-8'))
                 for f in UI.glob('*.py') if f.name != 'theme.py'}
    assert {k: v for k, v in offenders.items() if v} == {}


def test_every_group_has_glyph_colors():
    assert set(GROUPS) <= set(GROUP_GLYPH)
    assert {t.group for t in TOOLS} <= set(GROUPS)


@pytest.fixture
def window(qtbot, tmp_path):
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False,
                   settings=Settings(mode='detailed'))
    qtbot.addWidget(w)
    w.show()
    return w


def card(window, tool_id):
    return next(c for c in window.hub.cards if c.tool.id == tool_id)


@pytest.mark.parametrize('key', [Qt.Key_Return, Qt.Key_Space])
def test_card_keyboard_activation(window, qtbot, key):
    c = card(window, 'merge')
    assert c.focusPolicy() == Qt.StrongFocus
    got = []
    window.hub.tool_clicked.disconnect()
    window.hub.tool_clicked.connect(got.append)
    c.setFocus()
    qtbot.keyClick(c, key)
    assert got == ['merge']


def test_disabled_card_not_focusable(window):
    assert card(window, 'ocr').focusPolicy() == Qt.NoFocus
    assert card(window, 'word2pdf').focusPolicy() == Qt.NoFocus  # word_ok=False


def test_search_filters_and_ignores_accents(window):
    assert window.hub.filter('seguranca') >= 3          # sem cedilha nem til
    assert all(c.isHidden() or 'segur' in c.search_text for c in window.hub.cards)
    assert window.hub.filter('xyz-nada') == 0
    assert window.hub.empty.isVisible()
    assert window.hub.filter('') == len(TOOLS)


def test_password_mismatch_inline(window):
    opts = window.options
    opts.password.setText('abc')
    opts.password2.setText('abx')
    assert not opts.password_error.isHidden()
    assert opts.password2.property('state') == 'error'
    opts.password2.setText('abc')
    assert opts.password_error.isHidden()
    assert opts.password2.property('state') == ''
