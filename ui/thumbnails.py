"""Grade de miniaturas: seleção múltipla, arrastar para reordenar, soltar arquivos."""

from pathlib import Path

from PySide6.QtCore import QItemSelectionModel, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QListView, QListWidget, QListWidgetItem

from core.document import PageRef
from core.engines import mupdf
from ui.theme import Space

THUMB_ZOOM = 0.3
THUMB_SIZE = QSize(150, 190)


class ThumbnailGrid(QListWidget):
    reorder_requested = Signal(list, int)   # linhas selecionadas, posição de destino
    files_dropped = Signal(list)            # list[Path]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cache: dict[PageRef, QPixmap] = {}
        self.setViewMode(QListView.IconMode)
        self.setFlow(QListView.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Snap)
        self.setIconSize(THUMB_SIZE)
        self.setGridSize(QSize(THUMB_SIZE.width() + 24, THUMB_SIZE.height() + 36))
        self.setSpacing(Space.SM)
        self.setUniformItemSizes(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setObjectName('thumbnails')

    # --- conteúdo -----------------------------------------------------------
    def pixmap_for(self, ref: PageRef) -> QPixmap:
        pix = self._cache.get(ref)
        if pix is None:
            pix = QPixmap()
            pix.loadFromData(mupdf.render(ref.source, ref.index, THUMB_ZOOM, ref.rotation))
            self._cache[ref] = pix
        return pix

    def set_pages(self, pages: list[PageRef], selected: list[int] | None = None) -> None:
        self.blockSignals(True)
        self.clear()
        for n, ref in enumerate(pages, start=1):
            pix = self.pixmap_for(ref)
            icon = QIcon(pix)
            icon.addPixmap(pix, QIcon.Selected)  # sem o tingimento azul do Qt
            item = QListWidgetItem(icon, str(n))
            item.setTextAlignment(Qt.AlignHCenter)
            item.setToolTip(f'{ref.source.name} — página {ref.index + 1}')
            self.addItem(item)
        self.blockSignals(False)
        for row in selected or []:
            if 0 <= row < self.count():
                self.item(row).setSelected(True)
        if selected:
            self.setCurrentRow(selected[0], QItemSelectionModel.NoUpdate)
        self.currentRowChanged.emit(self.currentRow())

    def selected_rows(self) -> list[int]:
        return sorted(i.row() for i in self.selectedIndexes())

    # --- arrastar e soltar --------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.source() is self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.source() is self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.source() is self:
            pos = event.position().toPoint()
            index = self.indexAt(pos)
            if index.isValid():
                dest = index.row()
                if pos.x() > self.visualRect(index).center().x():
                    dest += 1
            else:
                dest = self.count()
            rows = self.selected_rows()
            # o próprio Qt não move nada: o Document é a fonte da verdade
            event.setDropAction(Qt.IgnoreAction)
            event.accept()
            if rows:
                self.reorder_requested.emit(rows, dest)
        elif event.mimeData().hasUrls():
            paths = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
            event.acceptProposedAction()
            if paths:
                self.files_dropped.emit(paths)
        else:
            event.ignore()
