"""Fase 3: vídeo para GIF ou WebP animado (PyAV, FFmpeg embutido, sem rede).

- probe(): duração, FPS e tamanho.
- frame_at(): um quadro para a prévia (busca o quadro-chave e decodifica até t).
- to_animation(): decodifica só o trecho, amostra no FPS pedido e grava.
"""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

VIDEO_EXTS = {'.mp4', '.mov', '.m4v', '.mkv', '.webm', '.avi', '.wmv', '.mpg', '.mpeg', '.3gp'}
FORMATS = {'GIF': '.gif', 'WebP': '.webp'}
MAX_SECONDS = 30
# bytes por pixel por quadro, medidos em vídeos reais com paleta adaptativa (aproximação)
_BYTES_PER_PX = {'GIF': 0.45, 'WebP': 0.08}


class VideoError(Exception):
    """Vídeo ilegível, sem faixa de imagem ou trecho inválido."""


@dataclass(frozen=True)
class VideoInfo:
    duration: float
    fps: float
    width: int
    height: int


@dataclass(frozen=True)
class Estimate:
    frames: int
    width: int
    height: int
    bytes: int


def _open(path: Path):
    import av
    try:
        container = av.open(str(path))
    except Exception as exc:  # av.error.* variam por versão
        raise VideoError(f'{Path(path).name}: não foi possível abrir o vídeo ({exc}).') from None
    if not container.streams.video:
        container.close()
        raise VideoError(f'{Path(path).name}: o arquivo não tem imagem de vídeo.')
    stream = container.streams.video[0]
    stream.thread_type = 'AUTO'
    return container, stream


def probe(path: Path) -> VideoInfo:
    container, stream = _open(path)
    try:
        if stream.duration and stream.time_base:
            duration = float(stream.duration * stream.time_base)
        elif container.duration:
            duration = container.duration / 1_000_000
        else:
            duration = 0.0
        rate = stream.average_rate or stream.guessed_rate or 25
        return VideoInfo(duration, float(rate), stream.codec_context.width,
                         stream.codec_context.height)
    finally:
        container.close()


def _size(src_w: int, src_h: int, width: int) -> tuple[int, int]:
    if not width or width >= src_w:
        return src_w, src_h
    return int(width), max(1, round(src_h * width / src_w))


def _frames(path: Path, start: float, end: float | None = None):
    """Gera (tempo, PIL.Image RGB) de `start` até antes de `end` (se dado)."""
    container, stream = _open(path)
    try:
        tb = stream.time_base
        container.seek(int(start / tb) if tb else 0, stream=stream, backward=True, any_frame=False)
        for frame in container.decode(stream):
            if frame.pts is None:
                continue
            t = float(frame.pts * tb)
            if t < start - 1e-3:
                continue
            if end is not None and t >= end - 1e-6:   # fim exclusivo: [início, fim)
                break
            yield t, frame.to_image()
    finally:
        container.close()


def frame_at(path: Path, t: float, max_width: int = 0) -> Image.Image:
    for _, img in _frames(path, max(0.0, t)):
        size = _size(img.width, img.height, max_width)
        return img if size == img.size else img.resize(size, Image.BILINEAR)
    # depois do último quadro: devolve o último
    last = None
    for _, img in _frames(path, 0.0):
        last = img
    if last is None:
        raise VideoError(f'{Path(path).name}: nenhum quadro decodificado.')
    return last


def _check_range(start: float, end: float) -> None:
    if end <= start:
        raise VideoError('O fim do trecho precisa vir depois do início.')
    if end - start > MAX_SECONDS:
        raise VideoError(f'Escolha um trecho de até {MAX_SECONDS} s (GIF longo fica enorme).')


def to_animation(src: Path, target: Path, start: float = 0.0, end: float = 5.0, fps: int = 10,
                 width: int = 480, fmt: str = 'GIF') -> Path:
    if fmt not in FORMATS:
        raise VideoError(f'Formato desconhecido: {fmt}')
    if not 1 <= int(fps) <= 30:
        raise VideoError('Use de 1 a 30 quadros por segundo.')
    start, end = float(start), float(end)
    _check_range(start, end)
    step = 1.0 / int(fps)
    frames, next_t = [], start
    for t, img in _frames(src, start, end):
        if t + 1e-6 < next_t:
            continue
        size = _size(img.width, img.height, width)
        if size != img.size:
            img = img.resize(size, Image.LANCZOS)
        # paleta adaptativa por quadro: menos memória e GIF mais fiel
        frames.append(img.quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                                   dither=Image.Dither.FLOYDSTEINBERG) if fmt == 'GIF' else img)
        next_t += step
        while next_t <= t:
            next_t += step
    if not frames:
        raise VideoError(f'{Path(src).name}: nenhum quadro no trecho escolhido.')
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    duration = round(1000 / int(fps))
    if fmt == 'WebP':
        frames[0].save(target, save_all=True, append_images=frames[1:], duration=duration,
                       loop=0, quality=80, method=4)
    else:
        frames[0].save(target, save_all=True, append_images=frames[1:], duration=duration,
                       loop=0, optimize=False, disposal=1)
    return target


# --- estimativa e texto de estado ----------------------------------------------
def estimate(info: VideoInfo, start: float, end: float, fps: int, width: int, fmt: str) -> Estimate:
    w, h = _size(info.width, info.height, width)
    n = max(0, round((end - start) * fps))
    return Estimate(n, w, h, int(w * h * n * _BYTES_PER_PX.get(fmt, 0.45)))


def timecode(seconds: float) -> str:
    seconds = max(0.0, seconds)
    m, s = divmod(seconds, 60)
    return f'{int(m):02d}:{s:05.2f}'


def human_size(n: int) -> str:
    if n >= 1_000_000:
        return f'{n / 1_000_000:.1f} MB'.replace('.', ',')
    return f'{max(1, round(n / 1000))} KB'


def status_line(start: float, end: float, est: Estimate) -> str:
    length = f'{end - start:.1f}'.replace('.', ',')
    return (f'TRECHO {timecode(start)} → {timecode(end)} · {length} s · {est.frames} quadros'
            f' · ≈ {human_size(est.bytes)}')
