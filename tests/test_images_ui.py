"""Fase 2 na UI: blocos de imagem, diálogo de recorte/borrar e Param de arquivo."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from PIL import Image  # noqa: E402
from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtGui import QFontInfo  # noqa: E402
from PySide6.QtWidgets import QFileDialog, QGroupBox, QLabel, QLineEdit, QPushButton  # noqa: E402

from core.workspace import Workspace  # noqa: E402
from tests.test_hub import ids  # noqa: E402
from ui import dialogs  # noqa: E402
from ui.crop_dialog import CropDialog  # noqa: E402
from ui.main_window import MainWindow, resolve_fn  # noqa: E402
from ui.style import apply_style  # noqa: E402
from ui.theme import Type  # noqa: E402
from ui.tools import BY_ID, Param, compatible  # noqa: E402

NOVOS = {'imgcrop', 'imgblur', 'imgrotate', 'imgexif', 'imgwatermark', 'gifedit'}


@pytest.fixture
def foto(tmp_path) -> Path:
    img = Image.new('RGB', (400, 200), 'white')
    img.paste('red', (0, 0, 100, 100))
    out = tmp_path / 'praia.png'
    img.save(out)
    return out


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch, qapp):
    apply_style(qapp)
    erros = []
    monkeypatch.setattr(dialogs, 'error', lambda *a: erros.append(a))
    monkeypatch.setattr(dialogs, 'info', lambda *_: None)
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False)
    w.erros = erros
    qtbot.addWidget(w)
    w.show()
    return w


def test_blocos_novos(window):
    cards = {c.tool.id: c for c in window.hub.cards}
    assert NOVOS <= set(cards)
    for i in NOVOS:
        assert callable(resolve_fn(BY_ID[i].fn))


def test_compativeis_com_png_e_gif(foto, tmp_path):
    assert {'imgcrop', 'imgblur', 'imgrotate', 'imgexif', 'imgwatermark'} <= ids(compatible([foto]))
    gif = tmp_path / 'a.gif'
    Image.new('RGB', (4, 4)).save(gif)
    assert 'gifedit' in ids(compatible([gif]))
    assert 'gifedit' not in ids(compatible([foto]))


# --- diálogo de recorte ----------------------------------------------------------
@pytest.fixture
def crop(qtbot, foto, qapp):
    apply_style(qapp)
    dlg = CropDialog(None, foto, mode='crop')
    qtbot.addWidget(dlg)
    dlg.show()
    return dlg


def test_dialogo_segue_design(crop):
    assert crop.findChildren(QGroupBox) == []
    buttons = crop.findChildren(QPushButton)
    primary = [b for b in buttons if b.property('variant') == 'primary']
    assert len(primary) == 1 and primary[0].text() == 'Recortar'
    assert all(b.property('variant') == 'ghost' for b in buttons if b not in primary)
    mono = [lb for lb in crop.findChildren(QLabel) if lb.property('role') == 'mono']
    assert mono and QFontInfo(mono[0].font()).family() == Type.MONO
    section = [lb for lb in crop.findChildren(QLabel) if lb.property('role') == 'section']
    assert section and section[0].text() == 'RECORTAR'


def test_medida_em_mono(crop):
    crop.set_box((10, 20, 110, 70))
    assert crop.box() == (10, 20, 110, 70)
    assert '100 × 50 px' in crop.measure.text()


def test_proporcao_1_1(crop):
    crop.ratio.setCurrentText('1:1')
    crop.set_box((0, 0, 200, 100))
    x0, y0, x1, y1 = crop.box()
    assert x1 - x0 == y1 - y0


def test_arrastar_cria_selecao(crop, qtbot):
    crop.set_box((300, 150, 390, 190))       # começa fora da seleção atual: cria outra
    canvas = crop.canvas
    a = canvas.to_widget(50, 50)
    b = canvas.to_widget(150, 100)
    qtbot.mousePress(canvas, Qt.LeftButton, pos=QPoint(round(a.x()), round(a.y())))
    qtbot.mouseMove(canvas, QPoint(round(b.x()), round(b.y())))
    qtbot.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(round(b.x()), round(b.y())))
    x0, y0, x1, y1 = crop.box()
    assert abs(x0 - 50) <= 3 and abs(y0 - 50) <= 3 and abs(x1 - 150) <= 3 and abs(y1 - 100) <= 3


def test_arrastar_dentro_move(crop, qtbot):
    crop.set_box((100, 50, 200, 100))
    canvas = crop.canvas
    a, b = canvas.to_widget(150, 75), canvas.to_widget(250, 125)
    qtbot.mousePress(canvas, Qt.LeftButton, pos=QPoint(round(a.x()), round(a.y())))
    qtbot.mouseMove(canvas, QPoint(round(b.x()), round(b.y())))
    qtbot.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(round(b.x()), round(b.y())))
    x0, y0, x1, y1 = crop.box()
    assert (x1 - x0, y1 - y0) == (100, 50) and abs(x0 - 200) <= 3 and abs(y0 - 100) <= 3


def test_borrar_tem_tamanho_do_bloco(qtbot, foto):
    dlg = CropDialog(None, foto, mode='blur')
    qtbot.addWidget(dlg)
    assert dlg.findChild(QPushButton, 'primary').text() == 'Borrar'
    assert dlg.block.value() >= 4


# --- fluxo pelo hub --------------------------------------------------------------
def test_recortar_pelo_hub(window, qtbot, foto, tmp_path, monkeypatch):
    alvo = tmp_path / 'recorte.png'
    monkeypatch.setattr(CropDialog, 'ask', classmethod(lambda cls, *a, **k: {'box': (0, 0, 100, 100)}))
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(alvo), ''))
    window.run_tool('imgcrop', [foto])
    qtbot.waitUntil(lambda: alvo.exists() and not window.is_busy(), timeout=10000)
    with Image.open(alvo) as im:
        assert im.size == (100, 100)


def test_borrar_pelo_hub_sugere_nome(window, qtbot, foto, tmp_path, monkeypatch):
    sugestao = []
    monkeypatch.setattr(CropDialog, 'ask',
                        classmethod(lambda cls, *a, **k: {'box': (0, 0, 100, 100), 'block': 10}))

    def save(parent, title, default, flt):
        sugestao.append(default)
        return str(tmp_path / 'b.png'), ''
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', save)
    window.run_tool('imgblur', [foto])
    qtbot.waitUntil(lambda: (tmp_path / 'b.png').exists() and not window.is_busy(), timeout=10000)
    assert Path(sugestao[0]).name == 'praia_borrada.png'


def test_cancelar_recorte_nao_faz_nada(window, foto, monkeypatch):
    monkeypatch.setattr(CropDialog, 'ask', classmethod(lambda cls, *a, **k: None))
    chamado = []
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: chamado.append(1))
    window.run_tool('imgcrop', [foto])
    assert not chamado and not window.is_busy()


def test_exif_pelo_hub(window, qtbot, foto, tmp_path, monkeypatch):
    out = tmp_path / 'saida'
    out.mkdir()
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *a, **k: str(out))
    window.run_tool('imgexif', [foto])
    qtbot.waitUntil(lambda: (out / 'praia_sem_exif.png').exists() and not window.is_busy(),
                    timeout=10000)


# --- Param de arquivo ------------------------------------------------------------
def test_param_arquivo(qtbot, tmp_path, monkeypatch):
    logo = tmp_path / 'logo.png'
    params = (Param('logo', 'Logo (opcional)', '', file_filter='Imagens (*.png *.jpg)'),)
    dlg = dialogs.ParamDialog(None, "Marca d'água", params)
    qtbot.addWidget(dlg)
    assert isinstance(dlg.fields['logo'], QLineEdit)
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **k: (str(logo), ''))
    escolher = [b for b in dlg.findChildren(QPushButton) if b.text() == 'Escolher…']
    assert len(escolher) == 1 and escolher[0].property('variant') == 'ghost'
    escolher[0].click()
    assert dlg.values() == {'logo': str(logo)}
