"""Caminhos do app: a pasta do projeto ou, no .exe do PyInstaller, a pasta extraída."""

import sys
from pathlib import Path


def base_dir() -> Path:
    frozen = getattr(sys, '_MEIPASS', None)
    if frozen:
        return Path(frozen)
    return Path(__file__).resolve().parent.parent


def assets() -> Path:
    return base_dir() / 'assets'
