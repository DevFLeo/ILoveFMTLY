"""Fase 3: vídeo para GIF/WebP (core/video.py, PyAV)."""

from fractions import Fraction
from pathlib import Path

import av
import numpy as np
import pytest
from PIL import Image

from core import video
from core.video import VideoError

COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]   # 1 s de cada


@pytest.fixture(scope='module')
def clip(tmp_path_factory) -> Path:
    """MP4 320×180, 25 fps, 4 s: vermelho, verde, azul, amarelo (1 s cada)."""
    out = tmp_path_factory.mktemp('v') / 'demo.mp4'
    with av.open(str(out), 'w') as c:
        s = c.add_stream('mpeg4', rate=25)
        s.width, s.height, s.pix_fmt = 320, 180, 'yuv420p'
        s.time_base = Fraction(1, 25)
        for i in range(100):
            arr = np.zeros((180, 320, 3), dtype=np.uint8)
            arr[:] = COLORS[i // 25]
            frame = av.VideoFrame.from_ndarray(arr, format='rgb24')
            frame.pts = i
            for pkt in s.encode(frame):
                c.mux(pkt)
        for pkt in s.encode():
            c.mux(pkt)
    return out


@pytest.fixture(scope='module')
def moving(tmp_path_factory) -> Path:
    """MP4 160×90, 25 fps, 2 s, com uma barra branca andando (todo quadro muda)."""
    tmp_path = tmp_path_factory.mktemp('m')
    out_mp4 = tmp_path / 'mov.mp4'
    with av.open(str(out_mp4), 'w') as c:
        s = c.add_stream('mpeg4', rate=25)
        s.width, s.height, s.pix_fmt = 160, 90, 'yuv420p'
        for i in range(50):
            arr = np.zeros((90, 160, 3), dtype=np.uint8)
            arr[:, (i * 3) % 160:(i * 3) % 160 + 8] = 255     # barra andando
            f = av.VideoFrame.from_ndarray(arr, format='rgb24')
            f.pts = i
            for pkt in s.encode(f):
                c.mux(pkt)
        for pkt in s.encode():
            c.mux(pkt)
    return out_mp4


def near(c, ref, tol=60):
    return all(abs(a - b) <= tol for a, b in zip(c[:3], ref))


def test_probe(clip):
    info = video.probe(clip)
    assert (info.width, info.height) == (320, 180)
    assert abs(info.duration - 4.0) < 0.2
    assert abs(info.fps - 25) < 0.5


@pytest.mark.parametrize('t, cor', [(0.5, COLORS[0]), (1.5, COLORS[1]), (2.5, COLORS[2]),
                                    (3.5, COLORS[3])])
def test_frame_at(clip, t, cor):
    img = video.frame_at(clip, t, max_width=160)
    assert img.size == (160, 90)
    assert near(img.getpixel((80, 45)), cor)


def total_ms(im) -> int:
    total = 0
    for i in range(im.n_frames):
        im.seek(i)
        im.load()
        total += im.info['duration']
    return total


def test_gif_do_trecho(clip, tmp_path):
    out = video.to_animation(clip, tmp_path / 'a.gif', start=1.0, end=3.0, fps=10, width=160,
                             fmt='GIF')
    with Image.open(out) as im:
        assert im.size == (160, 90)
        # quadros iguais seguidos viram um só (com a soma das durações): conta o tempo
        assert 1900 <= total_ms(im) <= 2100
        im.seek(0)
        assert near(im.convert('RGB').getpixel((80, 45)), COLORS[1])
        im.seek(im.n_frames - 1)
        assert near(im.convert('RGB').getpixel((80, 45)), COLORS[2])


def test_gif_com_movimento_tem_um_quadro_por_passo(moving, tmp_path):
    out = video.to_animation(moving, tmp_path / 'm.gif', start=0, end=1.9, fps=10, width=0,
                             fmt='GIF')
    with Image.open(out) as im:
        assert 19 <= im.n_frames <= 20
        im.seek(1)
        assert im.info['duration'] == 100


def test_webp(moving, tmp_path):
    out = video.to_animation(moving, tmp_path / 'a.webp', start=0, end=1, fps=5, width=80,
                             fmt='WebP')
    with Image.open(out) as im:
        assert im.format == 'WEBP' and im.size == (80, 45)
        assert im.n_frames == 5 and total_ms(im) == 1000


def test_estimativa():
    info = video.VideoInfo(duration=60.0, fps=30.0, width=1920, height=1080)
    est = video.estimate(info, start=12.4, end=18.0, fps=10, width=480, fmt='GIF')
    assert est.frames == 56
    assert est.height == 270
    assert est.bytes > 0
    assert video.status_line(12.4, 18.0, est) == (
        f'TRECHO 00:12.40 → 00:18.00 · 5,6 s · 56 quadros · ≈ {video.human_size(est.bytes)}')


def test_human_size():
    assert video.human_size(3_100_000) == '3,1 MB'
    assert video.human_size(850_000) == '850 KB'


def test_trecho_invalido(clip, tmp_path):
    with pytest.raises(VideoError, match='trecho'):
        video.to_animation(clip, tmp_path / 'x.gif', start=3, end=2, fps=10, width=0, fmt='GIF')
    with pytest.raises(VideoError, match='30 s'):
        video.to_animation(clip, tmp_path / 'x.gif', start=0, end=40, fps=10, width=0, fmt='GIF')


def test_arquivo_que_nao_e_video(tmp_path):
    ruim = tmp_path / 'ruim.mp4'
    ruim.write_bytes(b'nada aqui')
    with pytest.raises(VideoError, match='ruim.mp4'):
        video.probe(ruim)
