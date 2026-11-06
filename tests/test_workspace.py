from core.workspace import Workspace


def test_unique_path_adds_suffix(tmp_path):
    ws = Workspace(tmp_path / 'ws')
    (ws.path / 'a.pdf').write_bytes(b'x')
    assert ws.unique_path('a.pdf').name == 'a (2).pdf'
    (ws.path / 'a (2).pdf').write_bytes(b'x')
    assert ws.unique_path('a.pdf').name == 'a (3).pdf'


def test_import_copy_keeps_original(tmp_path):
    src = tmp_path / 'orig.pdf'
    src.write_bytes(b'%PDF-1.7')
    ws = Workspace(tmp_path / 'ws')
    copy = ws.import_copy(src)
    assert copy.parent == ws.path
    assert copy.read_bytes() == b'%PDF-1.7'
    assert src.exists()


def test_cleanup_removes_folder():
    ws = Workspace()
    (ws.path / 'x.txt').write_text('x')
    ws.cleanup()
    assert not ws.path.exists()
