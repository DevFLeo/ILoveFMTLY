"""Desfazer/refazer sobre snapshots do Document."""

from core.document import Document


class History:
    def __init__(self, doc: Document, limit: int = 200):
        self.doc = doc
        self.limit = limit
        self._undo: list = []
        self._redo: list = []

    def record(self) -> None:
        """Chamar ANTES de cada alteração no documento."""
        self._undo.append(self.doc.snapshot())
        if len(self._undo) > self.limit:
            self._undo.pop(0)
        self._redo.clear()

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self) -> bool:
        if not self._undo:
            return False
        self._redo.append(self.doc.snapshot())
        self.doc.restore(self._undo.pop())
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(self.doc.snapshot())
        self.doc.restore(self._redo.pop())
        return True
