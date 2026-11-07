"""Automação local do Microsoft Office (Word, Excel, PowerPoint) via COM.

Regras para todos os aplicativos:
- instância própria e invisível, aberta e fechada a cada conversão;
- arquivo aberto só para leitura, sem entrar na lista de recentes;
- macros desativadas à força (AutomationSecurity = 3);
- PDFs gerados sem as propriedades do documento (autor, empresa...);
- tempo limite: se o aplicativo travar (diálogo inesperado), só a instância
  aberta pelo ILoveFMTLY é encerrada e a conversão falha com OfficeTimeout.

As funções bloqueiam: chame-as fora da thread da interface.
"""

import contextlib
import threading
import winreg
from dataclasses import dataclass
from pathlib import Path

_MSO_AUTOMATION_FORCE_DISABLE = 3


class OfficeUnavailable(Exception):
    """O aplicativo do Office necessário não está instalado."""


class OfficeTimeout(Exception):
    """O aplicativo não respondeu dentro do tempo limite."""


class OfficeError(Exception):
    """O aplicativo recusou o arquivo."""


@dataclass(frozen=True)
class App:
    prog_id: str
    exe: str
    label: str


WORD = App('Word.Application', 'winword.exe', 'Microsoft Word')
EXCEL = App('Excel.Application', 'excel.exe', 'Microsoft Excel')
POWERPOINT = App('PowerPoint.Application', 'powerpnt.exe', 'Microsoft PowerPoint')

_locks = {app.prog_id: threading.Lock() for app in (WORD, EXCEL, POWERPOINT)}


def version(app: App) -> str | None:
    """'16.0' para Office 2016/2019/2021/365; None se não instalado."""
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf'{app.prog_id}\CurVer') as key:
            prog = winreg.QueryValue(key, None)
    except OSError:
        return None
    return prog.rsplit('.', 1)[-1] + '.0'


def is_available(app: App) -> bool:
    return version(app) is not None


def pids(app: App) -> set[int]:
    import win32api
    import win32con
    import win32process

    found = set()
    for pid in win32process.EnumProcesses():
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        except Exception:  # processos de sistema sem acesso
            continue
        try:
            exe = win32process.GetModuleFileNameEx(handle, 0)
        except Exception:
            exe = ''
        finally:
            win32api.CloseHandle(handle)
        if exe.lower().endswith(app.exe):
            found.add(pid)
    return found


def _kill(targets: set[int]) -> None:
    import win32api
    import win32con

    for pid in targets:
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, pid)
            win32api.TerminateProcess(handle, 1)
            win32api.CloseHandle(handle)
        except Exception:
            pass


def _com_message(exc) -> str:
    try:
        return exc.excepinfo[2] or str(exc)
    except Exception:
        return str(exc)


@contextlib.contextmanager
def session(app: App, timeout: float):
    """Abre uma instância exclusiva do aplicativo, com tempo limite."""
    if not is_available(app):
        raise OfficeUnavailable(f'Esta função requer o {app.label} instalado.')
    import pythoncom
    import pywintypes
    import win32com.client

    with _locks[app.prog_id]:
        pythoncom.CoInitialize()
        before = pids(app)
        instance = None
        timed_out = threading.Event()
        ours: set[int] = set()

        def on_timeout():
            timed_out.set()
            _kill(ours)

        watchdog = threading.Timer(timeout, on_timeout)
        try:
            instance = win32com.client.DispatchEx(app.prog_id)
            ours.update(pids(app) - before)
            watchdog.start()
            if app is not POWERPOINT:  # o PowerPoint não aceita Visible = False
                instance.Visible = False
            instance.DisplayAlerts = 0 if app is not EXCEL else False
            instance.AutomationSecurity = _MSO_AUTOMATION_FORCE_DISABLE
            yield instance
        except Exception as exc:
            # Depois de encerrarmos o processo, qualquer chamada COM falha de
            # formas variadas (com_error, AttributeError...): é tempo limite.
            if timed_out.is_set():
                raise OfficeTimeout(f'O {app.label} não respondeu em {timeout:g} s.') from None
            if isinstance(exc, pywintypes.com_error):
                raise OfficeError(_com_message(exc)) from None
            raise
        finally:
            watchdog.cancel()
            if instance is not None and not timed_out.is_set():
                with contextlib.suppress(Exception):
                    instance.Quit()
            instance = None
            pythoncom.CoUninitialize()
            _wait_exit(app, ours)


def _wait_exit(app: App, ours: set[int], grace: float = 10.0) -> None:
    """O Excel às vezes demora a sair após Quit(); nenhuma instância nossa pode sobrar."""
    import time

    deadline = time.monotonic() + grace
    while ours & pids(app):
        if time.monotonic() > deadline:
            _kill(ours & pids(app))
            return
        time.sleep(0.2)


def _check(out: Path, app: App) -> Path:
    if not out.exists():
        raise OfficeError(f'O {app.label} não gerou {out.name}.')
    return out


def excel_to_pdf(src: Path, out: Path, timeout: float = 180) -> Path:
    src, out = Path(src).resolve(), Path(out).resolve()
    with session(EXCEL, timeout) as xl:
        wb = xl.Workbooks.Open(str(src), UpdateLinks=0, ReadOnly=True, AddToMru=False)
        try:
            wb.ExportAsFixedFormat(0, str(out), 0, False, False)  # xlTypePDF, sem propriedades
        finally:
            wb.Close(False)
    return _check(out, EXCEL)


def powerpoint_to_pdf(src: Path, out: Path, timeout: float = 180) -> Path:
    src, out = Path(src).resolve(), Path(out).resolve()
    with session(POWERPOINT, timeout) as pp:
        pres = pp.Presentations.Open(str(src), ReadOnly=True, Untitled=False, WithWindow=False)
        try:
            pres.SaveAs(str(out), 32)  # ppSaveAsPDF
        finally:
            pres.Close()
    return _check(out, POWERPOINT)


def images_to_powerpoint(images: list[Path], width_pt: float, height_pt: float,
                         out: Path, timeout: float = 300) -> Path:
    """Uma imagem por slide, ocupando o slide inteiro."""
    out = Path(out).resolve()
    with session(POWERPOINT, timeout) as pp:
        pres = pp.Presentations.Add(WithWindow=False)
        try:
            pres.PageSetup.SlideWidth = width_pt
            pres.PageSetup.SlideHeight = height_pt
            for n, img in enumerate(images, start=1):
                slide = pres.Slides.Add(n, 12)  # ppLayoutBlank
                slide.Shapes.AddPicture(str(Path(img).resolve()), False, True, 0, 0,
                                        width_pt, height_pt)
            pres.SaveAs(str(out), 24)  # ppSaveAsOpenXMLPresentation
        finally:
            pres.Close()
    return _check(out, POWERPOINT)
