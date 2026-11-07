"""Regras do DESIGN.md cobradas na UI de verdade (pytest-qt, tela offscreen)."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import re  # noqa: E402

import pytest  # noqa: E402
from PySide6.QtGui import QFontInfo  # noqa: E402
from PySide6.QtWidgets import QGroupBox, QLabel, QPushButton  # noqa: E402

from core.settings import Settings  # noqa: E402
from core.workspace import Workspace  # noqa: E402
from ui import dialogs  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.style import apply_style  # noqa: E402
from ui.theme import Size, Type  # noqa: E402
from ui.tools import TOOLS  # noqa: E402

TOOLS_WITH_PARAMS = [t for t in TOOLS if t.params and t.mode != 'dev']  # dev usa o DevDialog


@pytest.fixture
def styled(qapp):
    apply_style(qapp)
    return qapp


@pytest.fixture
def window(qtbot, tmp_path, styled):
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False,
                   settings=Settings(mode='detailed'))
    w.resize(1280, 820)
    qtbot.addWidget(w)
    w.show()
    return w


def family(widget) -> str:
    return QFontInfo(widget.font()).family()


# --- fontes ------------------------------------------------------------------
def test_textos_do_hub_em_plex_sans(window):
    labels = [lb for lb in window.hub.findChildren(QLabel)
              if lb.text() and lb.objectName() not in ('groupHeader', 'glyph')]
    assert labels
    assert {family(lb) for lb in labels} == {Type.SANS}


def test_rotulos_de_grupo_em_plex_mono(window):
    headers = [lb for lb in window.hub.findChildren(QLabel) if lb.objectName() == 'groupHeader']
    assert headers
    assert {family(lb) for lb in headers} == {Type.MONO}


def test_nenhuma_fonte_do_sistema(window):
    proibidas = {'Inter', 'Roboto', 'Segoe UI', 'Segoe UI Symbol', 'Arial', 'DejaVu Sans'}
    usadas = {family(w) for w in window.findChildren(QLabel) if w.text()}
    assert not usadas & proibidas


# --- ícones ------------------------------------------------------------------
def test_icones_sao_nomes_svg_nao_glifos():
    assert all(re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', t.icon) for t in TOOLS)


def test_bloco_tem_quadrado_36_e_icone_20(window):
    for card in window.hub.cards:
        glyph = card.findChild(QLabel, 'glyph')
        assert glyph.size().width() == Size.GLYPH == glyph.size().height()
        pix = glyph.pixmap()
        assert not pix.isNull()
        assert round(pix.width() / pix.devicePixelRatio()) == Size.GLYPH_ICON


# --- diálogos de parâmetros (usados pelos blocos novos) ----------------------
@pytest.mark.parametrize('tool', TOOLS_WITH_PARAMS, ids=[t.id for t in TOOLS_WITH_PARAMS])
def test_param_dialog_segue_design(qtbot, styled, tool):
    dlg = dialogs.ParamDialog(None, tool.title, tool.params)
    qtbot.addWidget(dlg)
    dlg.show()
    assert dlg.findChildren(QGroupBox) == []                     # sem caixas
    buttons = dlg.findChildren(QPushButton)
    primary = [b for b in buttons if b.property('variant') == 'primary']
    ghost = [b for b in buttons if b.property('variant') == 'ghost']
    assert len(primary) == 1 and len(ghost) == len(buttons) - 1  # uma ação principal
    assert primary[0].text() and primary[0].isDefault()
    assert family(primary[0]) == Type.SANS


def test_param_dialog_tem_rotulo_de_secao_mono(qtbot, styled):
    tool = next(t for t in TOOLS if t.id == 'docxreplace')
    dlg = dialogs.ParamDialog(None, tool.title, tool.params)
    qtbot.addWidget(dlg)
    dlg.show()
    sections = [lb for lb in dlg.findChildren(QLabel) if lb.property('role') == 'section']
    assert len(sections) == 1
    assert sections[0].text() == sections[0].text().upper()
    assert family(sections[0]) == Type.MONO


def test_campo_de_texto_tem_dica(qtbot, styled):
    tool = next(t for t in TOOLS if t.id == 'docxreplace')
    dlg = dialogs.ParamDialog(None, tool.title, tool.params)
    qtbot.addWidget(dlg)
    assert dlg.fields['find'].placeholderText()


# --- mascote -------------------------------------------------------------------
def test_mascote_no_hub_e_icone_do_exe(window):
    from ui.theme import ASSETS
    logo = window.hub.logo.pixmap()
    assert not logo.isNull()
    assert round(logo.width() / logo.devicePixelRatio()) == Size.LOGO
    from PIL import Image
    with Image.open(ASSETS / 'app.ico') as ico:
        assert {(16, 16), (32, 32), (256, 256)} <= set(ico.info['sizes'])
