"""Vídeo para GIF na UI: diálogo no padrão DESIGN.md, trilha, estado em Mono, fluxo."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from fractions import Fraction  # noqa: E402
from pathlib import Path  # noqa: E402

import av  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402
from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtGui import QFontInfo  # noqa: E402
from PySide6.QtWidgets import QFileDialog, QGroupBox, QLabel, QPushButton  # noqa: E402

from core.workspace import Workspace  # noqa: E402
from tests.test_hub import ids  # noqa: E402
from ui import dialogs  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.style import apply_style  # noqa: E402
from ui.theme import Type  # noqa: E402
from ui.tools import compatible  # noqa: E402
from ui.video_gif_dialog import VideoGifDialog  # noqa: E402


@pytest.fixture(scope='module')
def clip(tmp_path_factory) -> Path:
    """MP4 320×180, 25 fps, 8 s, barra andando."""
    out = tmp_path_factory.mktemp('vui') / 'aula.mp4'
    with av.open(str(out), 'w') as c:
        s = c.add_stream('mpeg4', rate=25)
        s.width, s.height, s.pix_fmt = 320, 180, 'yuv420p'
        s.time_base = Fraction(1, 25)
        for i in range(200):
            arr = np.full((180, 320, 3), 40, dtype=np.uint8)
            arr[:, (i * 2) % 320:(i * 2) % 320 + 10] = (253, 164, 129)
            f = av.VideoFrame.from_ndarray(arr, format='rgb24')
            f.pts = i
            for pkt in s.encode(f):
                c.mux(pkt)
        for pkt in s.encode():
            c.mux(pkt)
    return out


@pytest.fixture
def dlg(qtbot, clip, qapp):
    apply_style(qapp)
    d = VideoGifDialog(None, clip)
    qtbot.addWidget(d)
    d.show()
    return d


def test_compativel_com_mp4(clip):
    assert 'video2gif' in ids(compatible([clip]))


def test_dialogo_segue_design(dlg):
    assert dlg.findChildren(QGroupBox) == []
    buttons = dlg.findChildren(QPushButton)
    primary = [b for b in buttons if b.property('variant') == 'primary']
    assert [b.text() for b in primary] == ['Gerar GIF']
    assert all(b.property('variant') == 'ghost' for b in buttons if b not in primary)
    assert dlg.status.property('role') == 'mono'
    assert QFontInfo(dlg.status.font()).family() == Type.MONO
    section = [lb for lb in dlg.findChildren(QLabel) if lb.property('role') == 'section']
    assert [s.text() for s in section] == ['VÍDEO PARA GIF']


def test_trecho_inicial_e_estado(dlg):
    assert (dlg.timeline.start, dlg.timeline.end) == (0.0, 5.0)
    assert dlg.status.text().startswith('TRECHO 00:00.00 → 00:05.00 · 5,0 s · 50 quadros · ≈ ')


def test_mudar_trecho_atualiza_estado(dlg):
    dlg.timeline.set_range(1.2, 3.0)
    dlg.fps.setValue(15)
    assert 'TRECHO 00:01.20 → 00:03.00 · 1,8 s · 27 quadros' in dlg.status.text()
    assert dlg.values() == {'start': 1.2, 'end': 3.0, 'fps': 15, 'width': 320, 'fmt': 'GIF'}


def test_formato_muda_botao(dlg):
    dlg.fmt.setCurrentText('WebP')
    assert dlg.ok.text() == 'Gerar WebP'
    assert dlg.values()['fmt'] == 'WebP'


def test_arrastar_alca_do_fim(dlg, qtbot):
    tl = dlg.timeline
    x_end = round(tl._x(tl.end))
    y = tl.height() // 2
    alvo = round(tl._x(2.0))
    qtbot.mousePress(tl, Qt.LeftButton, pos=QPoint(x_end, y))
    qtbot.mouseMove(tl, QPoint(alvo, y))
    qtbot.mouseRelease(tl, Qt.LeftButton, pos=QPoint(alvo, y))
    assert abs(tl.end - 2.0) < 0.1 and tl.start == 0.0


def test_previa_aparece(dlg, qtbot):
    qtbot.waitUntil(lambda: dlg.preview.pixmap() is not None and not dlg.preview.pixmap().isNull(),
                    timeout=5000)


def test_play_anda_a_agulha(dlg, qtbot):
    dlg.play.setChecked(True)
    qtbot.waitUntil(lambda: dlg.timeline.playhead > 0.2, timeout=5000)
    dlg.play.setChecked(False)
    assert dlg.play.text() == 'Prévia'


def test_video_invalido_mostra_erro(qtbot, tmp_path, monkeypatch, qapp):
    erros = []
    monkeypatch.setattr(dialogs, 'error', lambda *a: erros.append(a))
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False)
    qtbot.addWidget(w)
    ruim = tmp_path / 'ruim.mp4'
    ruim.write_bytes(b'nada')
    w.run_tool('video2gif', [ruim])
    assert erros and 'ruim.mp4' in erros[0][2]


def test_fluxo_pelo_hub(qtbot, clip, tmp_path, monkeypatch, qapp):
    monkeypatch.setattr(dialogs, 'info', lambda *_: None)
    monkeypatch.setattr(dialogs, 'error', lambda *a: pytest.fail(str(a)))
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False)
    qtbot.addWidget(w)
    monkeypatch.setattr(VideoGifDialog, 'ask', classmethod(
        lambda cls, *a, **k: {'start': 1.0, 'end': 2.0, 'fps': 10, 'width': 160, 'fmt': 'GIF'}))
    sugestao = []

    def save(parent, title, default, flt):
        sugestao.append(Path(default).name)
        return str(tmp_path / 'trecho'), ''
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', save)
    w.run_tool('video2gif', [clip])
    alvo = tmp_path / 'trecho.gif'
    qtbot.waitUntil(lambda: alvo.exists() and not w.is_busy(), timeout=15000)
    assert sugestao == ['aula.gif']
    with Image.open(alvo) as im:
        assert im.size == (160, 90) and im.n_frames == 10
