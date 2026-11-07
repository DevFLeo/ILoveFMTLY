"""Conversões com o Microsoft Word (COM). A mecânica comum está em office.py."""

import contextlib
import winreg
from pathlib import Path

from core.engines.office import (WORD, OfficeError, OfficeTimeout, OfficeUnavailable,
                                 session)

WORD_INPUT_EXTS = {'.docx', '.doc', '.docm', '.dotx', '.rtf', '.odt', '.txt'}

_WD_FORMAT_DOCX = 16
_WD_EXPORT_PDF = 17

# nomes antigos, mantidos para quem já importava daqui
WordUnavailable = OfficeUnavailable
WordTimeout = OfficeTimeout
WordError = OfficeError


def word_version() -> str | None:
    from core.engines.office import version
    return version(WORD)


def is_available() -> bool:
    return word_version() is not None


def _word_pids() -> set[int]:
    from core.engines.office import pids
    return pids(WORD)


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


def to_pdf(src: Path, out: Path, timeout: float = 120) -> Path:
    """DOCX/DOC/RTF/ODT/TXT para PDF, sem as propriedades do documento."""
    src, out = Path(src).resolve(), Path(out).resolve()
    with session(WORD, timeout) as app:
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
    with _pdf_warning_disabled(), session(WORD, timeout) as app:
        doc = app.Documents.Open(str(src), ConfirmConversions=False, ReadOnly=True,
                                 AddToRecentFiles=False, Visible=False)
        try:
            doc.SaveAs2(str(out), FileFormat=_WD_FORMAT_DOCX, AddToRecentFiles=False)
        finally:
            doc.Close(0)
    if not out.exists():
        raise WordError(f'O Word não gerou {out.name}.')
    return out
