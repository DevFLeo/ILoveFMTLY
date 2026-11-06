from pathlib import Path

import pytest

from core.document import Document
from core.history import History
from core.ranges import parse_ranges

A = Path('a.pdf')


def doc3():
    d = Document()
    d.add_source(A, 3)
    return d


def order(d):
    return [p.index for p in d.pages]


def test_move_to_end():
    d = doc3()
    d.move([0], 3)
    assert order(d) == [1, 2, 0]


def test_move_to_start():
    d = doc3()
    d.move([2], 0)
    assert order(d) == [2, 0, 1]


def test_move_multiple():
    d = doc3()
    d.move([0, 1], 3)
    assert order(d) == [2, 0, 1]


def test_rotate_normalizes():
    d = doc3()
    d.rotate([0], 90)
    d.rotate([0], 90)
    assert d.pages[0].rotation == 180
    d.rotate([1], 270)
    d.rotate([1], 90)
    assert d.pages[1].rotation == 0
    d.rotate([2], -90)
    assert d.pages[2].rotation == 270


def test_rotate_rejects_non_multiple():
    with pytest.raises(ValueError):
        doc3().rotate([0], 45)


def test_delete():
    d = doc3()
    d.delete([0, 2])
    assert order(d) == [1]


def test_undo_redo():
    d = doc3()
    h = History(d)
    h.record()
    d.delete([0])
    assert len(d) == 2
    assert h.undo()
    assert len(d) == 3
    assert h.redo()
    assert len(d) == 2
    assert not h.redo()


def test_parse_ranges_ok():
    assert parse_ranges('1-3, 5', 5) == [[0, 1, 2], [4]]


@pytest.mark.parametrize('text,n', [('5-2', 5), ('0', 3), ('9', 3), ('', 3), ('a', 3), ('1-x', 3)])
def test_parse_ranges_invalid(text, n):
    with pytest.raises(ValueError):
        parse_ranges(text, n)
