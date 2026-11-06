"""Janela principal: liga a interface ao core (Document, History, export...)."""

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, Qt, QTimer
from PySide6.QtGui import QAction, QImage, QKeySequence, QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (QFileDialog, QInputDialog, QLabel, QMainWindow,
                               QScrollArea, QSplitter, QStyle, QToolBar)

from core import importer, printer
from core.document import Document
from core.engines import mupdf, qpdf
from core.export import export, split
from core.history import History
from core.ranges import parse_ranges
from core.workspace import Workspace
from ui import dialogs
from ui.options_panel import OptionsPanel
from ui.thumbnails import ThumbnailGrid
from ui.viewer import Viewer
from ui.worker import run_in_thread

OPEN_FILTER = 'PDF e imagens (*.pdf *.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)'


class MainWindow(QMainWindow):
    def __init__(self, workspace: Workspace, spool_dir: Path | None = printer.SPOOL_DIR):
        super().__init__()
        self.ws = workspace
        self.doc = Document()
        self.history = History(self.doc)
        self.setWindowTitle('ILoveFMTLY — PDF')
        self.resize(1280, 800)
        self.setAcceptDrops(True)

        self.grid = ThumbnailGrid()
        self.viewer = Viewer()
        self.options = OptionsPanel()
        options_scroll = QScrollArea()
        options_scroll.setWidget(self.options)
        options_scroll.setWidgetResizable(True)
        options_scroll.setMinimumWidth(320)
        options_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        split_view = QSplitter(Qt.Horizontal)
        split_view.addWidget(self.grid)
        split_view.addWidget(self.viewer)
        split_view.addWidget(options_scroll)
        split_view.setStretchFactor(0, 1)
        split_view.setStretchFactor(1, 1)
        split_view.setStretchFactor(2, 0)
        split_view.setSizes([440, 520, 320])
        self.setCentralWidget(split_view)

        self.status = QLabel()
        self.statusBar().addPermanentWidget(QLabel('🔒 Offline — nada sai desta máquina'))
        self.statusBar().addWidget(self.status)

        self._build_actions()
        self.grid.currentRowChanged.connect(self._show_current)
        self.grid.itemSelectionChanged.connect(self._update_state)
        self.grid.reorder_requested.connect(self.move_pages)
        self.grid.files_dropped.connect(self.add_files)

        self._spool_dir = spool_dir
        self._watcher = None
        if spool_dir is not None:
            self._watch_spool(spool_dir)
        self.refresh()

    # --- ações --------------------------------------------------------------
    def _action(self, text, slot, shortcut=None, icon=None, tip=None):
        act = QAction(text, self)
        act.triggered.connect(slot)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        if icon is not None:
            act.setIcon(self.style().standardIcon(icon))
        act.setToolTip(f'{tip or text} ({shortcut})' if shortcut else (tip or text))
        return act

    def _build_actions(self):
        sp = QStyle.StandardPixmap
        self.act_import = self._action('Importar', self.import_dialog, 'Ctrl+O', sp.SP_DialogOpenButton,
                                       'Adicionar PDFs ou imagens ao documento')
        self.act_clear = self._action('Novo', self.clear_document, 'Ctrl+N', sp.SP_FileIcon,
                                      'Começar um documento vazio')
        self.act_rot_l = self._action('Girar ↺', lambda: self.rotate(-90), 'Ctrl+L')
        self.act_rot_r = self._action('Girar ↻', lambda: self.rotate(90), 'Ctrl+R')
        self.act_delete = self._action('Excluir', self.delete_selected, 'Del', sp.SP_TrashIcon,
                                       'Excluir páginas selecionadas')
        self.act_undo = self._action('Desfazer', self.undo, 'Ctrl+Z', sp.SP_ArrowBack)
        self.act_redo = self._action('Refazer', self.redo, 'Ctrl+Y', sp.SP_ArrowForward)
        self.act_extract = self._action('Extrair', self.extract_dialog, 'Ctrl+E', None,
                                        'Salvar só as páginas selecionadas')
        self.act_split = self._action('Dividir', self.split_dialog, 'Ctrl+D', None,
                                      'Dividir em vários arquivos por intervalos')
        self.act_meta = self._action('Metadados', self.show_metadata, None, sp.SP_FileDialogInfoView,
                                     'Ver metadados dos arquivos de origem')
        self.act_print = self._action('Imprimir', self.print_dialog, 'Ctrl+P', None)
        self.act_export = self._action('Exportar PDF', self.export_dialog, 'Ctrl+S', sp.SP_DialogSaveButton,
                                       'Gravar o documento final')

        bar = QToolBar('Ferramentas')
        bar.setMovable(False)
        bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        for act in (self.act_import, self.act_clear, None, self.act_rot_l, self.act_rot_r,
                    self.act_delete, None, self.act_undo, self.act_redo, None,
                    self.act_extract, self.act_split, self.act_meta, None,
                    self.act_print, self.act_export):
            bar.addSeparator() if act is None else bar.addAction(act)
        self.addToolBar(bar)
        self.toolbar = bar

    # --- estado -------------------------------------------------------------
    def refresh(self, selected: list[int] | None = None):
        self.grid.set_pages(self.doc.pages, selected)
        if not self.doc.pages:
            self.viewer.show_page(None)
        self._update_state()

    def _update_state(self):
        n, sel = len(self.doc), len(self.grid.selected_rows())
        has_sel = sel > 0
        for act in (self.act_rot_l, self.act_rot_r, self.act_delete, self.act_extract):
            act.setEnabled(has_sel)
        for act in (self.act_split, self.act_print, self.act_export, self.act_meta, self.act_clear):
            act.setEnabled(n > 0)
        self.act_undo.setEnabled(self.history.can_undo())
        self.act_redo.setEnabled(self.history.can_redo())
        if n == 0:
            self.status.setText('Arraste PDFs ou imagens para cá, ou use Importar (Ctrl+O).')
        else:
            self.status.setText(f'{n} página(s)' + (f' · {sel} selecionada(s)' if sel else ''))

    def _show_current(self, row: int):
        if 0 <= row < len(self.doc):
            self.viewer.show_page(self.doc.pages[row], f'Página {row + 1} de {len(self.doc)}')

    def _change(self, fn, selected=None):
        self.history.record()
        fn()
        self.refresh(selected)

    # --- edição -------------------------------------------------------------
    def add_files(self, paths: list[Path]) -> int:
        """Importa arquivos (pedindo senha quando preciso). Devolve quantos entraram."""
        imported = []
        for src in paths:
            src = Path(src)
            if src.is_dir():
                continue
            password, retry = None, False
            while True:
                try:
                    copy = importer.import_file(self.ws, src, password)
                    imported.append(copy)
                    break
                except importer.PasswordRequired:
                    pass
                except importer.WrongPassword:
                    retry = True
                except (importer.UnsupportedFile, qpdf.PdfRepairError) as exc:
                    dialogs.error(self, 'Não foi possível importar', str(exc))
                    break
                password = dialogs.ask_password(self, src.name, retry)
                if password is None:
                    break
        if imported:
            start = len(self.doc)
            self.history.record()
            for path in imported:
                self.doc.add_source(path, mupdf.page_count(path))
            self.refresh([start])
        return len(imported)

    def import_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Importar', '', OPEN_FILTER)
        if files:
            self.add_files([Path(f) for f in files])

    def clear_document(self):
        self._change(lambda: self.doc.restore(()))

    def rotate(self, degrees: int):
        rows = self.grid.selected_rows()
        if rows:
            self._change(lambda: self.doc.rotate(rows, degrees), rows)

    def delete_selected(self):
        rows = self.grid.selected_rows()
        if rows:
            first = min(rows[0], len(self.doc) - len(rows) - 1)
            self._change(lambda: self.doc.delete(rows), [first] if first >= 0 else None)

    def move_pages(self, rows: list[int], dest: int):
        before = sum(1 for r in rows if r < dest)
        start = max(0, dest - before)
        self._change(lambda: self.doc.move(rows, dest), list(range(start, start + len(rows))))

    def undo(self):
        if self.history.undo():
            self.refresh()

    def redo(self):
        if self.history.redo():
            self.refresh()

    # --- saída --------------------------------------------------------------
    def _read_options(self, for_print=False):
        try:
            return self.options.options(for_print)
        except ValueError as exc:
            dialogs.error(self, 'Opções inválidas', str(exc))
            return None

    def _busy(self, on: bool, text: str = ''):
        self.toolbar.setEnabled(not on)
        if on:
            self.status.setText(text)
            self.setCursor(Qt.WaitCursor)
        else:
            self.unsetCursor()
            self._update_state()

    def _run(self, text, fn, *args, done_msg=None):
        self._busy(True, text)

        def ok(result):
            self._busy(False)
            if done_msg:
                dialogs.info(self, 'Pronto', done_msg(result))

        def fail(exc):
            self._busy(False)
            dialogs.error(self, 'Erro', str(exc))

        run_in_thread(fn, *args, on_done=ok, on_error=fail)

    def _snapshot_doc(self, rows=None) -> Document:
        return self.doc.subset(rows if rows is not None else list(range(len(self.doc))))

    def export_dialog(self):
        opts = self._read_options()
        if opts is None or not len(self.doc):
            return
        out, _ = QFileDialog.getSaveFileName(self, 'Exportar PDF', 'documento.pdf', 'PDF (*.pdf)')
        if out:
            self._run('Exportando…', export, self._snapshot_doc(), Path(out), opts,
                      done_msg=lambda p: f'Arquivo salvo em:\n{p}')

    def extract_dialog(self):
        rows = self.grid.selected_rows()
        opts = self._read_options()
        if not rows or opts is None:
            return
        out, _ = QFileDialog.getSaveFileName(self, 'Extrair páginas', 'paginas.pdf', 'PDF (*.pdf)')
        if out:
            self._run('Extraindo…', export, self._snapshot_doc(rows), Path(out), opts,
                      done_msg=lambda p: f'{len(rows)} página(s) salvas em:\n{p}')

    def split_dialog(self):
        n = len(self.doc)
        text, ok = QInputDialog.getText(
            self, 'Dividir', f'Intervalos separados por vírgula (1 a {n}).\n'
                             'Cada intervalo vira um arquivo. Ex.: 1-3, 4, 5-8', text=f'1-{n}')
        if not ok:
            return
        try:
            ranges = parse_ranges(text, n)
        except ValueError as exc:
            dialogs.error(self, 'Intervalo inválido', str(exc))
            return
        opts = self._read_options()
        if opts is None:
            return
        folder = QFileDialog.getExistingDirectory(self, 'Pasta de destino')
        if folder:
            self._run('Dividindo…', split, self._snapshot_doc(), ranges, Path(folder), 'documento', opts,
                      done_msg=lambda files: f'{len(files)} arquivo(s) criados em:\n{folder}')

    def show_metadata(self):
        entries = []
        for source in dict.fromkeys(p.source for p in self.doc.pages):
            try:
                for key, value in qpdf.read_metadata(source).items():
                    entries.append((source.name, key, value))
            except Exception as exc:  # metadado ilegível não impede o resto
                entries.append((source.name, 'erro', str(exc)))
        dialogs.MetadataDialog(self, entries).exec()

    def print_dialog(self):
        opts = self._read_options(for_print=True)
        if opts is None or not len(self.doc):
            return
        qprinter = QPrinter(QPrinter.HighResolution)
        if QPrintDialog(qprinter, self).exec() != QPrintDialog.Accepted:
            return
        tmp = self.ws.unique_path('impressao.pdf')
        self._busy(True, 'Preparando impressão…')
        try:
            export(self._snapshot_doc(), tmp, opts)
            self._paint(qprinter, tmp)
        except Exception as exc:
            dialogs.error(self, 'Erro ao imprimir', str(exc))
        finally:
            tmp.unlink(missing_ok=True)
            self._busy(False)

    @staticmethod
    def _paint(qprinter: QPrinter, pdf: Path):
        zoom = min(qprinter.resolution(), 300) / 72
        painter = QPainter(qprinter)
        try:
            total = mupdf.page_count(pdf)
            for i in range(total):
                if i:
                    qprinter.newPage()
                image = QImage.fromData(mupdf.render(pdf, i, zoom))
                area = painter.viewport()
                size = image.size().scaled(area.size(), Qt.KeepAspectRatio)
                painter.drawImage(area.x() + (area.width() - size.width()) // 2,
                                  area.y() + (area.height() - size.height()) // 2,
                                  image.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        finally:
            painter.end()

    # --- impressora virtual -------------------------------------------------
    def _watch_spool(self, spool_dir: Path):
        try:
            printer.ensure_spool(spool_dir)
        except OSError:
            return
        self._watcher = QFileSystemWatcher([str(spool_dir)], self)
        self._spool_timer = QTimer(self, singleShot=True, interval=800)
        self._spool_timer.timeout.connect(self.collect_spool)
        self._watcher.directoryChanged.connect(lambda _: self._spool_timer.start())
        QTimer.singleShot(0, self.collect_spool)  # impressões feitas com o app fechado

    def collect_spool(self):
        files = printer.collect(self.ws, self._spool_dir)
        if files:
            self.add_files(files)
            self.raise_()
            self.activateWindow()

    # --- arrastar arquivos para qualquer ponto da janela ---------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            event.acceptProposedAction()
            self.add_files(paths)
