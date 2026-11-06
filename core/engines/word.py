"""Motor Word: conversões usando o Microsoft Word instalado (COM).

Tudo roda localmente, numa instância própria e invisível do Word:
- documento aberto só para leitura, sem entrar na lista de recentes;
- macros desativadas à força (documentos de terceiros podem conter macros);
- PDF gerado sem as propriedades do documento (autor, empresa...);
- tempo limite: se o Word travar (diálogo inesperado), a instância aberta
  por nós é encerrada e a conversão falha com WordTimeout.

Estas funções bloqueiam: chame-as fora da thread da interface.
"""

import contextlib
import threading
import winreg
from pathlib import Path

WORD_INPUT_EXTS = {'.docx', '.doc', '.docm', '.dotx', '.rtf', '.odt', '.txt'}

_WD_FORMAT_DOCX = 16
_WD_EXPORT_PDF = 17
_MSO_AUTOMATION_FORCE_DISABLE = 3
_lock = threading.Lock()  # uma conversão por vez: o Word não gosta de concorrência


class WordUnavailable(Exception):
    """Microsoft Word não está instalado."""


class WordTimeout(Exception):
    """O Word não respondeu dentro do tempo limite."""


class WordError(Exception):
    """O Word recusou o arquivo."""


def word_version() -> str | None:
    """'16.0' para o Office 2016/2019/2021/365; None sem Word."""
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r'Word.Application\CurVer') as key:
            prog_id = winreg.QueryValue(key, None)  # 'Word.Application.16'
    except OSError:
        return None
    return prog_id.rsplit('.', 1)[-1] + '.0'


def is_available() -> bool:
    return word_version() is not None


@contextlib.contextmanager
def _pdf_warning_disabled():
    """Desliga o aviso "o Word vai converter o PDF" só durante a conversão.

    O aviso é um diálogo modal que, com o Word invisível, trava a automação.
    O valor anterior do usuário é restaurado ao final.
    """
    path = rf'Software\Microsoft\Office\{word_version()}\Word\Options'
    name = 'DisableConvertPdfWarning'
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0,
                            winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            previous = winreg.QueryValueEx(key, name)
        except FileNotFoundError:
            previous = None
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, 1)
        try:
            yield
        finally:
            if previous is None:
                winreg.DeleteValue(key, name)
            else:
                winreg.SetValueEx(key, name, 0, previous[1], previous[0])


def _word_pids() -> set[int]:
    import win32api
    import win32con
    import win32process

    pids = set()
    for pid in win32process.EnumProcesses():
        try:
            handle = win32api.OpenProcess(
                win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        except Exception:  # processos de sistema sem acesso
            continue
        try:
            exe = win32process.GetModuleFileNameEx(handle, 0)
        except Exception:
            exe = ''
        finally:
            win32api.CloseHandle(handle)
        if exe.lower().endswith('winword.exe'):
            pids.add(pid)
    return pids


def _kill(pids: set[int]) -> None:
    import win32api
    import win32con

    for pid in pids:
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, pid)
            win32api.TerminateProcess(handle, 1)
            win32api.CloseHandle(handle)
        except Exception:
            pass


@contextlib.contextmanager
def _word(timeout: float):
    """Abre uma instância exclusiva do Word com tempo limite."""
    if not is_available():
        raise WordUnavailable('Esta função requer o Microsoft Word instalado.')
    import pythoncom
    import pywintypes
    import win32com.client

    with _lock:
        pythoncom.CoInitialize()
        before = _word_pids()
        app = None
        timed_out = threading.Event()
        ours: set[int] = set()

        def on_timeout():
            timed_out.set()
            _kill(ours)

        watchdog = threading.Timer(timeout, on_timeout)
        try:
            app = win32com.client.DispatchEx('Word.Application')
            ours.update(_word_pids() - before)
            watchdog.start()
            app.Visible = False
            app.DisplayAlerts = 0
            app.AutomationSecurity = _MSO_AUTOMATION_FORCE_DISABLE
            yield app
        except Exception as exc:
            # Depois de encerrarmos o Word, qualquer chamada COM falha de um
            # jeito diferente (com_error, AttributeError...): é tudo tempo limite.
            if timed_out.is_set():
                raise WordTimeout(f'O Word não respondeu em {timeout:g} s.') from None
            if isinstance(exc, pywintypes.com_error):
                raise WordError(_com_message(exc)) from None
            raise
        finally:
            watchdog.cancel()
            if app is not None and not timed_out.is_set():
                with contextlib.suppress(Exception):
                    app.Quit(0)
            app = None
            pythoncom.CoUninitialize()


def _com_message(exc) -> str:
    try:
        return exc.excepinfo[2] or str(exc)
    except Exception:
        return str(exc)


def to_pdf(src: Path, out: Path, timeout: float = 120) -> Path:
    """DOCX/DOC/RTF/ODT/TXT para PDF, sem as propriedades do documento."""
    src, out = Path(src).resolve(), Path(out).resolve()
    with _word(timeout) as app:
        doc = app.Documents.Open(str(src), ConfirmConversions=False, ReadOnly=True,
                                 AddToRecentFiles=False, Visible=False, NoEncodingDialog=True)
        try:
            doc.ExportAsFixedFormat(OutputFileName=str(out), ExportFormat=_WD_EXPORT_PDF,
                                    OpenAfterExport=False, OptimizeFor=0,
                                    IncludeDocProps=False, KeepIRM=True,
                                    DocStructureTags=True, BitmapMissingFonts=True)
        finally:
            doc.Close(0)
    if not out.exists():
        raise WordError(f'O Word não gerou {out.name}.')
    return out


def pdf_to_docx(src: Path, out: Path, timeout: float = 300) -> Path:
    """PDF para DOCX usando a conversão de PDF do próprio Word."""
    src, out = Path(src).resolve(), Path(out).resolve()
    with _pdf_warning_disabled(), _word(timeout) as app:
        doc = app.Documents.Open(str(src), ConfirmConversions=False, ReadOnly=True,
                                 AddToRecentFiles=False, Visible=False)
        try:
            doc.SaveAs2(str(out), FileFormat=_WD_FORMAT_DOCX, AddToRecentFiles=False)
        finally:
            doc.Close(0)
    if not out.exists():
        raise WordError(f'O Word não gerou {out.name}.')
    return out
