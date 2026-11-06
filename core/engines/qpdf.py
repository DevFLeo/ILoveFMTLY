"""Motor pikepdf (qpdf): operações estruturais.

Reparo, senha, compressão sem perda, linearização e metadados. Aqui o qpdf é
mais robusto que o PyMuPDF e não toca no conteúdo das páginas.
"""

import os
from pathlib import Path

import pikepdf


class PdfRepairError(Exception):
    """O PDF está danificado demais para ser recuperado."""


def _save_replace(pdf: pikepdf.Pdf, path: Path, **kw) -> None:
    tmp = Path(str(path) + '.tmp')
    pdf.save(tmp, **kw)
    pdf.close()
    os.replace(tmp, path)


def repair(src: Path, out: Path) -> Path:
    try:
        with pikepdf.open(src) as pdf:
            if len(pdf.pages) == 0:
                raise PdfRepairError(f'{Path(src).name}: nenhuma página recuperável')
            pdf.save(out)
    except pikepdf.PasswordError:
        raise
    except (pikepdf.PdfError, OSError, ValueError) as exc:
        raise PdfRepairError(f'{Path(src).name}: {exc}') from exc
    return Path(out)


def optimize(path: Path, linearize: bool = True) -> None:
    """Compressão sem perda: object streams + recompressão flate."""
    pdf = pikepdf.open(path)
    pdf.remove_unreferenced_resources()
    _save_replace(pdf, path, compress_streams=True,
                  object_stream_mode=pikepdf.ObjectStreamMode.generate,
                  recompress_flate=True, linearize=linearize)


def protect(path: Path, user_pw: str, owner_pw: str | None = None,
            allow_print: bool = True, allow_copy: bool = False) -> None:
    """Senha AES-256 (R=6)."""
    if not user_pw:
        raise ValueError('Senha vazia')
    permissions = pikepdf.Permissions(
        print_lowres=allow_print, print_highres=allow_print,
        extract=allow_copy, accessibility=True,
        modify_annotation=False, modify_assembly=False,
        modify_form=False, modify_other=False,
    )
    encryption = pikepdf.Encryption(user=user_pw, owner=owner_pw or user_pw,
                                    R=6, allow=permissions)
    pdf = pikepdf.open(path)
    _save_replace(pdf, path, encryption=encryption)


def unprotect(path: Path, password: str, out: Path) -> Path:
    with pikepdf.open(path, password=password) as pdf:
        pdf.save(out, encryption=False)
    return Path(out)


def is_encrypted(path: Path) -> bool:
    try:
        with pikepdf.open(path) as pdf:
            return pdf.is_encrypted
    except pikepdf.PasswordError:
        return True


def read_metadata(path: Path, password: str | None = None) -> dict[str, str]:
    """Campos do /Info e do XMP, como texto."""
    result: dict[str, str] = {}
    with pikepdf.open(path, password=password or '') as pdf:
        for key, value in pdf.docinfo.items():
            result[str(key).lstrip('/')] = str(value)
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            for key, value in meta.items():
                result.setdefault(f'XMP {key}', str(value))
    return result


def strip_metadata(path: Path) -> None:
    """Remove /Info e o XMP do catálogo (autor, software, datas...)."""
    pdf = pikepdf.open(path)
    if '/Info' in pdf.trailer:
        del pdf.trailer['/Info']
    if '/Metadata' in pdf.Root:
        del pdf.Root['/Metadata']
    _save_replace(pdf, path, fix_metadata_version=False)
