import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest  # noqa: E402

from core.workspace import Workspace  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402


@pytest.fixture
def window(qtbot, tmp_path):
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=tmp_path / 'spool')
    qtbot.addWidget(w)
    return w


def test_import_rotate_undo(window, make_pdf):
    assert window.add_files([make_pdf(3)]) == 1
    assert window.grid.count() == 3
    window.grid.item(0).setSelected(True)
    window.rotate(90)
    assert window.doc.pages[0].rotation == 90
    window.undo()
    assert window.doc.pages[0].rotation == 0
    window.redo()
    assert window.doc.pages[0].rotation == 90


def test_reorder_and_delete(window, make_pdf):
    window.add_files([make_pdf(3)])
    window.move_pages([0], 3)
    assert [p.index for p in window.doc.pages] == [1, 2, 0]
    window.grid.clearSelection()
    window.grid.item(0).setSelected(True)
    window.delete_selected()
    assert [p.index for p in window.doc.pages] == [2, 0]
    assert window.grid.count() == 2


def test_spool_is_collected(window, make_pdf, tmp_path):
    make_pdf(2).replace(tmp_path / 'spool' / 'print.pdf')
    window.collect_spool()
    assert len(window.doc) == 2
