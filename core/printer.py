"""Impressora virtual: recolhe os PDFs que a impressora "ILoveFMTLY PDF" grava.

A impressora (instalada por scripts/setup_printer.ps1) usa o driver nativo
"Microsoft Print To PDF" com uma porta local que grava sempre o mesmo
arquivo dentro de SPOOL_DIR. O app move cada impressão para o workspace com
nome único, liberando a porta para a próxima.
"""

import os
import shutil
import time
from datetime import datetime
from pathlib import Path

from core.workspace import Workspace

SPOOL_DIR = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'ILoveFMTLY' / 'spool'
PRINTER_NAME = 'ILoveFMTLY PDF'


def ensure_spool(directory: Path = SPOOL_DIR) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _is_complete_pdf(path: Path, settle: float) -> bool:
    """O driver ainda pode estar gravando: exige tamanho estável e cabeçalho %PDF."""
    try:
        size = path.stat().st_size
        if size == 0:
            return False
        if settle:
            time.sleep(settle)
            if path.stat().st_size != size:
                return False
        with open(path, 'rb') as fh:
            if fh.read(4) != b'%PDF':
                return False
            fh.seek(max(0, size - 1024))
            return b'%%EOF' in fh.read()
    except OSError:  # arquivo ainda bloqueado pelo spooler
        return False


def collect(ws: Workspace, directory: Path = SPOOL_DIR, settle: float = 0.3) -> list[Path]:
    """Move as impressões completas para o workspace e devolve os novos caminhos."""
    directory = Path(directory)
    if not directory.is_dir():
        return []
    collected = []
    for item in sorted(directory.glob('*.pdf')):
        if not _is_complete_pdf(item, settle):
            continue
        stamp = datetime.now().strftime('%Y-%m-%d %H%M%S')
        target = ws.unique_path(f'Impressão {stamp}.pdf')
        try:
            shutil.move(str(item), target)
        except OSError:
            continue
        collected.append(target)
    return collected
