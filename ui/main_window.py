"""Janela principal: hub de blocos + editor, ligados ao core."""

import importlib
from functools import partial
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QImage, QKeySequence, QMovie, QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (QFileDialog, QInputDialog, QLabel, QMainWindow,
                               QScrollArea, QSizePolicy, QSplitter, QStackedWidget,
                               QToolBar, QVBoxLayout, QWidget)

from core import importer, printer
from core.document import Document
from core import convert
from core.engines import mupdf, office, qpdf
from core.export import export, split
from core.history import History
from core.ranges import parse_ranges
from core.workspace import Workspace
from ui import dialogs
from ui.crop_dialog import CropDialog
from ui.hub import DropLayer, HubPage
from ui.icons import svg_icon
from ui.style import set_prop
from ui.options_panel import OptionsPanel
from ui.thumbnails import ThumbnailGrid
from ui.tools import BY_ID, OFFICE_LABEL, Tool, accepts_count, file_filter
from ui.theme import ASSETS, Size
from ui.viewer import Viewer
from ui.worker import run_in_thread

OPEN_FILTER = 'PDF e imagens (*.pdf *.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)'
THEME_GIF = ASSETS / 'tema.gif'

# Dica mostrada no topo do editor ao abrir cada bloco.
TOOL_HINTS = {
    'merge': 'Arraste as miniaturas para definir a ordem e clique em Exportar PDF.',
    'organize': 'Arraste para reordenar, gire (Ctrl+L / Ctrl+R) e exclua (Del). Depois, Exportar PDF.',
    'rotate': 'Todas as páginas estão selecionadas: use Girar ↺ / ↻ e depois Exportar PDF.',
    'extract': 'Selecione as páginas (Ctrl+clique) e clique em Extrair.',
    'split': 'Informe os intervalos; cada um vira um arquivo.',
    'compress': 'Compressão com redução de imagens selecionada. Clique em Exportar PDF.',
    'repair': 'Arquivo recuperado. Confira as páginas e clique em Exportar PDF.',
    'img2pdf': 'Cada imagem virou uma página. Organize e clique em Exportar PDF.',
    'word2pdf': 'Documento convertido pelo Word local. Ajuste e clique em Exportar PDF.',
    'numbers': 'Numeração marcada no painel à direita. Clique em Exportar PDF.',
    'watermark': "Digite o texto da marca d'água no painel à direita e clique em Exportar PDF.",
    'protect': 'Defina a senha no painel à direita e clique em Exportar PDF.',
    'unlock': 'Senha removida da cópia de trabalho. Exporte sem senha para salvar o PDF livre.',
    'metadata': 'Remoção de metadados marcada. Clique em Exportar PDF.',
    'crop': 'Margens recortadas. Confira e clique em Exportar PDF.',
    'grayscale': 'Páginas em tons de cinza. Confira e clique em Exportar PDF.',
    'excel2pdf': 'Planilha convertida pelo Excel local. Ajuste e clique em Exportar PDF.',
    'ppt2pdf': 'Apresentação convertida pelo PowerPoint local. Ajuste e clique em Exportar PDF.',
    'web2pdf': 'Documento convertido para PDF A4. Ajuste e clique em Exportar PDF.',
    'ebook2pdf': 'E-book convertido para PDF. Ajuste e clique em Exportar PDF.',
}


def resolve_fn(name: str):
    """'pdf_to_text' -> core.convert.pdf_to_text; 'docx_tools.clean' -> core.docx_tools.clean."""
    module, _, attr = name.rpartition('.')
    return getattr(importlib.import_module(f'core.{module}') if module else convert, attr)


class MainWindow(QMainWindow):
    def __init__(self, workspace: Workspace, spool_dir: Path | None = printer.SPOOL_DIR,
                 word_ok: bool | None = None):
        super().__init__()
        self.ws = workspace
        self.doc = Document()
        self.history = History(self.doc)
        if word_ok is None:
            self.apps = {key: office.is_available(app) for key, app in
                         (('word', office.WORD), ('excel', office.EXCEL),
                          ('powerpoint', office.POWERPOINT))}
        else:  # testes: liga/desliga todo o Office de uma vez
            self.apps = dict.fromkeys(('word', 'excel', 'powerpoint'), word_ok)
        self.setWindowTitle('ILoveFMTLY')
        self.resize(1280, 820)
        self.setAcceptDrops(True)

        # --- editor ---------------------------------------------------------
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

        self.hint_bar = QLabel()
        self.hint_bar.setObjectName('hintBar')
        self.hint_bar.setWordWrap(True)
        self.hint_bar.hide()
        self.editor = QWidget()
        editor_layout = QVBoxLayout(self.editor)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        editor_layout.addWidget(self.hint_bar)
        editor_layout.addWidget(split_view, 1)

        # --- hub + camada ---------------------------------------------------
        self.hub = HubPage(self.apps)
        self.hub.tool_clicked.connect(self.run_tool)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.hub)
        self.stack.addWidget(self.editor)
        self.setCentralWidget(self.stack)
        self.layer = DropLayer(self.stack, self.apps)
        self.layer.tool_chosen.connect(self.run_tool)

        # --- barra de status --------------------------------------------------
        self.status = QLabel()
        self.statusBar().addWidget(self.status)
        self.statusBar().addPermanentWidget(QLabel('🔒 Offline — nada sai desta máquina'))
        self.theme_gif = self._make_theme_gif()

        self._build_actions()
        self.grid.currentRowChanged.connect(self._show_current)
        self.grid.itemSelectionChanged.connect(self._update_state)
        self.grid.reorder_requested.connect(self.move_pages)
        self.grid.files_dropped.connect(self.add_files)

        self._spool_dir = spool_dir
        self._watcher = None
        if spool_dir is not None:
            self._watch_spool(spool_dir)
        self.show_hub()

    def _make_theme_gif(self) -> QLabel | None:
        if not THEME_GIF.exists():
            return None
        label = QLabel()
        label.setObjectName('themeGif')
        label.setFixedSize(Size.THEME_GIF, Size.THEME_GIF)
        movie = QMovie(str(THEME_GIF), parent=label)
        movie.setScaledSize(QSize(Size.THEME_GIF, Size.THEME_GIF))
        label.setMovie(movie)
        movie.start()
        self.statusBar().addPermanentWidget(label)  # último item: canto inferior direito
        return label

    # --- ações --------------------------------------------------------------
    def _action(self, text, slot, shortcut=None, icon=None, tip=None):
        act = QAction(text, self)
        act.triggered.connect(slot)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        if icon is not None:
            act.setIcon(svg_icon(icon))
        act.setToolTip(f'{tip or text} ({shortcut})' if shortcut else (tip or text))
        return act

    def _build_actions(self):
        self.act_home = self._action('Início', self.show_hub, 'Alt+Home', 'house',
                                     'Voltar para as ferramentas')
        self.act_import = self._action('Importar', self.import_dialog, 'Ctrl+O', 'file-plus',
                                       'Adicionar PDFs ou imagens ao documento')
        self.act_clear = self._action('Novo', self.clear_document, 'Ctrl+N', 'file',
                                      'Começar um documento vazio')
        self.act_rot_l = self._action('Girar', lambda: self.rotate(-90), 'Ctrl+L', 'rotate-ccw', 'Girar para a esquerda')
        self.act_rot_r = self._action('Girar', lambda: self.rotate(90), 'Ctrl+R', 'rotate-cw', 'Girar para a direita')
        self.act_delete = self._action('Excluir', self.delete_selected, 'Del', 'trash-2',
                                       'Excluir páginas selecionadas')
        self.act_undo = self._action('Desfazer', self.undo, 'Ctrl+Z', 'undo-2')
        self.act_redo = self._action('Refazer', self.redo, 'Ctrl+Y', 'redo-2')
        self.act_extract = self._action('Extrair', self.extract_dialog, 'Ctrl+E', 'file-output',
                                        'Salvar só as páginas selecionadas')
        self.act_split = self._action('Dividir', self.split_dialog, 'Ctrl+D', 'scissors',
                                      'Dividir em vários arquivos por intervalos')
        self.act_meta = self._action('Metadados', self.show_metadata, None, 'info',
                                     'Ver metadados dos arquivos de origem')
        self.act_print = self._action('Imprimir', self.print_dialog, 'Ctrl+P', 'printer')
        self.act_export = self._action('Exportar PDF', self.export_dialog, 'Ctrl+S', None,
                                       'Gravar o documento final')

        bar = QToolBar('Ferramentas')
        bar.setMovable(False)
        bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        spacer = QWidget()
        spacer.setObjectName('toolbarSpacer')
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        for act in (self.act_home, None, self.act_import, self.act_clear, None,
                    self.act_rot_l, self.act_rot_r, self.act_delete, None,
                    self.act_undo, self.act_redo, None,
                    self.act_extract, self.act_split, self.act_meta, 'spacer',
                    self.act_print, self.act_export):
            if act is None:
                bar.addSeparator()
            elif act == 'spacer':
                bar.addWidget(spacer)  # empurra Imprimir/Exportar para a direita
            else:
                bar.addAction(act)
        # ações de ícone óbvio ficam só com ícone (texto no tooltip) para caber a barra
        for act in (self.act_rot_l, self.act_rot_r, self.act_undo, self.act_redo):
            bar.widgetForAction(act).setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.addToolBar(bar)
        self.toolbar = bar
        export_btn = bar.widgetForAction(self.act_export)
        set_prop(export_btn, 'variant', 'primary')

    # --- navegação ------------------------------------------------------------
    def show_hub(self):
        self.layer.close_layer()
        self.stack.setCurrentWidget(self.hub)
        self.toolbar.hide()
        self.status.setText('Escolha uma ferramenta ou solte arquivos na tela.')

    def show_editor(self, hint: str = ''):
        self.stack.setCurrentWidget(self.editor)
        self.toolbar.show()
        self.hint_bar.setText(hint)
        self.hint_bar.setVisible(bool(hint))

    def on_hub(self) -> bool:
        return self.stack.currentWidget() is self.hub

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.layer.isVisible():
            self.layer.setGeometry(self.stack.rect())

    # --- blocos -------------------------------------------------------------
    def available(self, tool: Tool) -> bool:
        return not tool.soon and (tool.needs is None or self.apps.get(tool.needs, False))

    def run_tool(self, tool_id: str, files: list[Path] | None = None):
        tool = BY_ID[tool_id]
        if not self.available(tool):
            return
        self.layer.close_layer()
        if files is None:
            files = self._pick_files(tool)
            if not files:
                return
        files = [Path(f) for f in files]
        if not accepts_count(tool, len(files)):
            need = (f'exatamente {tool.min_files}' if tool.min_files == tool.max_files
                    else f'pelo menos {tool.min_files}')
            dialogs.error(self, tool.title, f'Esta ferramenta precisa de {need} arquivo(s).')
            return
        if tool.mode == 'editor':
            self._tool_in_editor(tool, files)
        elif tool.mode == 'dialog':
            self._tool_dialog(tool, files[0])
        else:
            self._tool_convert(tool, files)

    def _pick_files(self, tool: Tool) -> list[Path]:
        if tool.multi:
            chosen, _ = QFileDialog.getOpenFileNames(self, tool.title, '', file_filter(tool))
        else:
            one, _ = QFileDialog.getOpenFileName(self, tool.title, '', file_filter(tool))
            chosen = [one] if one else []
        return [Path(c) for c in chosen]

    def new_document(self):
        self.doc.restore(())
        self.history = History(self.doc)
        self.options.reset()
        self.refresh()

    def _tool_in_editor(self, tool: Tool, files: list[Path]):
        self.new_document()
        if not self.add_files(files):
            self.show_hub()
            return
        self.show_editor(TOOL_HINTS.get(tool.id, ''))
        preset = {
            'rotate': self.grid.selectAll,
            'compress': lambda: self.options.compress.setCurrentIndex(
                self.options.compress.findData('lossy')),
            'numbers': lambda: self.options.page_numbers.setChecked(True),
            'watermark': self.options.watermark.setFocus,
            'protect': self.options.password.setFocus,
            'metadata': lambda: self.options.strip_metadata.setChecked(True),
            'split': lambda: QTimer.singleShot(0, self.split_dialog),
        }.get(tool.id)
        if preset:
            preset()

    def _tool_dialog(self, tool: Tool, src: Path):
        """Recortar / borrar: diálogo próprio, depois o arquivo de destino."""
        try:
            values = CropDialog.ask(self, src, tool.dialog)
        except ValueError as exc:
            dialogs.error(self, tool.title, str(exc))
            return
        if values is None:
            return
        default = str(src.with_name(src.stem + tool.out_suffix + src.suffix.lower()))
        out, _ = QFileDialog.getSaveFileName(self, tool.title, default,
                                             f'{src.suffix[1:].upper()} (*{src.suffix.lower()})')
        if not out:
            return
        target = Path(out)
        if not target.suffix:
            target = target.with_suffix(src.suffix.lower())
        if target.resolve() == src.resolve():
            dialogs.error(self, tool.title, 'Escolha outro nome: o arquivo original não é sobrescrito.')
            return
        self._run(f'{tool.title}…', partial(resolve_fn(tool.fn), src, target, **values),
                  done_msg=lambda res: f'Arquivo salvo em:\n{res}')

    def _tool_convert(self, tool: Tool, files: list[Path]):
        """Ferramentas de conversão: parâmetros, destino e execução em segundo plano."""
        params = {}
        if tool.params:
            params = dialogs.ParamDialog.ask(self, tool.title, tool.params)
            if params is None:
                return
        sources = []
        for f in files:  # PDFs passam pelo workspace (senha, reparo); o original não é tocado
            if f.suffix.lower() == '.pdf':
                copy = self._import_with_password(f)
                if copy is None:
                    return
                sources.append(copy)
            else:
                sources.append(f)
        fn = resolve_fn(tool.fn)
        busy = (f'Convertendo com o {OFFICE_LABEL[tool.needs]}…' if tool.needs
                else f'{tool.title}…')

        if tool.mode == 'to_editor':
            def job():
                return [fn([src], self.ws.unique_path(orig.stem + '.pdf'), **params)[0]
                        for src, orig in zip(sources, files)]
            self._run(busy, job, on_done=lambda pdfs: self._tool_in_editor(tool, pdfs))
            return

        if tool.mode == 'file':
            default = files[0].stem + tool.out_suffix + tool.ext
            out, _ = QFileDialog.getSaveFileName(self, tool.title, default,
                                                 f'{tool.ext[1:].upper()} (*{tool.ext})')
            if not out:
                return
            target = Path(out)
            if target.suffix.lower() != tool.ext:
                target = target.with_name(target.name + tool.ext)
            if any(target.resolve() == Path(f).resolve() for f in files):
                dialogs.error(self, tool.title, 'Escolha outro nome: o arquivo original não é sobrescrito.')
                return
            self._run(busy, partial(fn, sources, target, **params),
                      done_msg=lambda res: f'Arquivo salvo em:\n{res[0]}')
            return

        folder = QFileDialog.getExistingDirectory(self, f'{tool.title}: pasta de destino')
        if folder:
            self._run(busy, partial(fn, sources, Path(folder), **params),
                      done_msg=lambda res: f'{len(res)} arquivo(s) salvos em:\n{folder}')

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
        if self.on_hub():
            return
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
    def _import_with_password(self, src: Path) -> Path | None:
        """Copia para o workspace pedindo a senha quando preciso. None se cancelado/erro."""
        password, retry = None, False
        while True:
            try:
                return importer.import_file(self.ws, src, password)
            except importer.PasswordRequired:
                pass
            except importer.WrongPassword:
                retry = True
            except (importer.UnsupportedFile, qpdf.PdfRepairError) as exc:
                dialogs.error(self, 'Não foi possível importar', str(exc))
                return None
            password = dialogs.ask_password(self, Path(src).name, retry)
            if password is None:
                return None

    def add_files(self, paths: list[Path]) -> int:
        """Importa arquivos para o documento aberto. Devolve quantos entraram."""
        imported = []
        for src in paths:
            src = Path(src)
            if src.is_dir():
                continue
            copy = self._import_with_password(src)
            if copy is not None:
                imported.append(copy)
        if imported:
            start = len(self.doc)
            self.history.record()
            for path in imported:
                self.doc.add_source(path, mupdf.page_count(path))
            if self.on_hub():
                self.show_editor()
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
        self.hub.setEnabled(not on)
        if on:
            self.status.setText(text)
            self.setCursor(Qt.WaitCursor)
        else:
            self.unsetCursor()
            self._update_state()

    def is_busy(self) -> bool:
        return not self.hub.isEnabled()

    def _run(self, text, fn, *args, done_msg=None, on_done=None):
        self._busy(True, text)

        def ok(result):
            self._busy(False)
            if on_done:
                on_done(result)
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
        if not n:
            return
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
        if not len(self.doc):
            return
        qprinter = QPrinter(QPrinter.HighResolution)
        if QPrintDialog(qprinter, self).exec() == QPrintDialog.Accepted:
            self.print_to(qprinter)

    def print_to(self, qprinter: QPrinter):
        opts = self._read_options(for_print=True)
        if opts is None or not len(self.doc):
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
            self.show_editor('Impressão recebida da impressora "ILoveFMTLY PDF".')
            self.raise_()
            self.activateWindow()

    # --- arrastar arquivos para qualquer ponto da janela ---------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
        paths = [p for p in paths if p.is_file()]
        if not paths:
            return
        event.acceptProposedAction()
        if self.on_hub():
            self.layer.show_for(paths)
        else:
            self.add_files(paths)
