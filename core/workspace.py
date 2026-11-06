"""Pasta temporária da sessão.

Toda cópia de trabalho vive aqui, nunca ao lado do original. Ao fechar o app,
cleanup() apaga tudo.
"""

import shutil
import tempfile
from pathlib import Path


class Workspace:
    def __init__(self, root: Path | None = None):
        if root is None:
            self.path = Path(tempfile.mkdtemp(prefix='ilovefmtly_'))
        else:
            self.path = Path(root)
            self.path.mkdir(parents=True, exist_ok=True)

    def unique_path(self, name: str) -> Path:
        """Caminho livre dentro do workspace; homônimos ganham ' (2)', ' (3)'..."""
        candidate = self.path / name
        stem, suffix = candidate.stem, candidate.suffix
        n = 2
        while candidate.exists():
            candidate = self.path / f'{stem} ({n}){suffix}'
            n += 1
        return candidate

    def import_copy(self, src: Path) -> Path:
        dest = self.unique_path(Path(src).name)
        shutil.copy2(src, dest)
        return dest

    def cleanup(self) -> None:
        shutil.rmtree(self.path, ignore_errors=True)
