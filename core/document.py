"""Modelo de páginas virtual.

O Document não é um PDF: é uma lista de referências a páginas de PDFs de
origem. Juntar, reordenar, girar e excluir só mexem nessa lista; o PDF real
só é gravado na exportação. Por isso as edições são instantâneas e o
desfazer é trivial.
"""

from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class PageRef:
    source: Path
    index: int
    rotation: int = 0  # rotação extra, somada à rotação original da página


class Document:
    def __init__(self):
        self.pages: list[PageRef] = []
        self.passwords: dict[Path, str] = {}

    def __len__(self) -> int:
        return len(self.pages)

    def add_source(self, path: Path, n_pages: int, password: str | None = None) -> None:
        path = Path(path)
        if password:
            self.passwords[path] = password
        self.pages.extend(PageRef(path, i) for i in range(n_pages))

    def move(self, src: list[int], dest: int) -> None:
        """Move as páginas `src` para antes da posição `dest` (posição na lista original)."""
        src = sorted(set(src))
        moving = [self.pages[i] for i in src]
        before = sum(1 for i in src if i < dest)
        rest = [p for i, p in enumerate(self.pages) if i not in set(src)]
        pos = max(0, min(len(rest), dest - before))
        self.pages = rest[:pos] + moving + rest[pos:]

    def rotate(self, idx: list[int], degrees: int) -> None:
        if degrees % 90:
            raise ValueError('Rotação deve ser múltipla de 90 graus')
        for i in set(idx):
            p = self.pages[i]
            self.pages[i] = replace(p, rotation=(p.rotation + degrees) % 360)

    def delete(self, idx: list[int]) -> None:
        drop = set(idx)
        self.pages = [p for i, p in enumerate(self.pages) if i not in drop]

    def subset(self, idx: list[int]) -> 'Document':
        sub = Document()
        sub.pages = [self.pages[i] for i in idx]
        sub.passwords = dict(self.passwords)
        return sub

    def snapshot(self) -> tuple[PageRef, ...]:
        return tuple(self.pages)

    def restore(self, snap: tuple[PageRef, ...]) -> None:
        self.pages = list(snap)
