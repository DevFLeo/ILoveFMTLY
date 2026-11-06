"""Importação: traz um arquivo para o workspace pronto para editar.

O original nunca é tocado. Imagens viram PDF de uma página; PDFs com senha
são decifrados (com a senha do usuário) para a cópia de trabalho; PDFs
danificados passam pelo reparo do qpdf.
"""

from pathlib import Path

import pikepdf
import pymupdf

from core.engines import mupdf, qpdf
from core.engines.mupdf import PasswordRequired, WrongPassword
from core.workspace import Workspace

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp'}
SUPPORTED_EXTS = IMAGE_EXTS | {'.pdf'}

__all__ = ['import_file', 'PasswordRequired', 'WrongPassword', 'IMAGE_EXTS',
           'SUPPORTED_EXTS', 'UnsupportedFile']


class UnsupportedFile(ValueError):
    """Extensão que o app ainda não sabe importar."""


def import_file(ws: Workspace, src: Path, password: str | None = None) -> Path:
    src = Path(src)
    ext = src.suffix.lower()
    if ext in IMAGE_EXTS:
        return mupdf.image_to_pdf(src, ws.unique_path(src.stem + '.pdf'))
    if ext != '.pdf':
        raise UnsupportedFile(f'Formato não suportado: {src.name}')

    copy = ws.import_copy(src)
    try:
        encrypted = mupdf.needs_password(copy)
        readable = True
    except (pymupdf.FileDataError, RuntimeError):
        encrypted, readable = False, False

    if encrypted:
        if not password:
            copy.unlink()
            raise PasswordRequired(src.name)
        clear = ws.unique_path(src.stem + ' (sem senha).pdf')
        try:
            qpdf.unprotect(copy, password, clear)
        except pikepdf.PasswordError:
            copy.unlink()
            raise WrongPassword(src.name) from None
        copy.unlink()
        return clear

    if not readable or mupdf.page_count(copy) == 0:
        fixed = ws.unique_path(src.stem + ' (reparado).pdf')
        try:
            qpdf.repair(copy, fixed)
        finally:
            copy.unlink()
        return fixed

    return copy
