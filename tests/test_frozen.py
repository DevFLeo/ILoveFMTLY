"""O .exe (PyInstaller) acha os assets e o spec empacota o necessário."""

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_assets_no_projeto():
    import ui.theme as theme
    assert (theme.ASSETS / 'check.svg').is_file()
    assert (theme.ASSETS / 'app.ico').is_file()


def test_assets_no_exe(monkeypatch, tmp_path):
    import ui.theme as theme
    monkeypatch.setattr(sys, '_MEIPASS', str(tmp_path), raising=False)
    try:
        importlib.reload(theme)
        assert theme.ASSETS == tmp_path / 'assets'
    finally:
        monkeypatch.delattr(sys, '_MEIPASS')
        importlib.reload(theme)


def test_spec_inclui_assets_e_markdown():
    spec = (ROOT / 'ILoveFMTLY.spec').read_text(encoding='utf-8')
    assert "'assets'" in spec
    assert "collect_submodules('markdown.extensions')" in spec
    assert 'console=False' in spec
