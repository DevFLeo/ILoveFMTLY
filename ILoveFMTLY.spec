# -*- mode: python ; coding: utf-8 -*-
"""Empacotamento do ILoveFMTLY em .exe com PyInstaller.

Use scripts/build_exe.ps1 em vez de chamar o PyInstaller direto.
Modo padrão: pasta dist/ILoveFMTLY/ com ILoveFMTLY.exe (abre rápido).
Com ILOVEFMTLY_ONEFILE=1: um único dist/ILoveFMTLY.exe (abre mais devagar,
pois extrai tudo numa pasta temporária a cada execução).
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH)
ONEFILE = os.environ.get('ILOVEFMTLY_ONEFILE') == '1'
ICON = str(ROOT / 'assets' / 'app.ico')

# Extensões do Markdown são carregadas pelo nome ('tables', 'fenced_code'),
# então o PyInstaller não as enxerga sozinho.
hidden = collect_submodules('markdown.extensions')
# Faker carrega os provedores e idiomas pelo nome.
hidden += collect_submodules('faker.providers')

# Peças grandes que o app não usa.
excluded = [
    'tkinter', 'pytest', 'pytestqt', '_pytest', 'unittest', 'pydoc_data',
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick',
    'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.QtQuick', 'PySide6.QtQml',
    'PySide6.QtMultimedia', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
    'PySide6.QtBluetooth', 'PySide6.QtNetworkAuth', 'PySide6.QtPositioning',
    'PySide6.QtLocation', 'PySide6.QtSerialPort', 'PySide6.QtWebSockets',
]

a = Analysis(
    [str(ROOT / 'app.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / 'assets'), 'assets'),
           (str(ROOT / 'scripts' / 'setup_printer.ps1'), 'scripts'),
           *collect_data_files('docx'), *collect_data_files('docxcompose'),
           *collect_data_files('faker'), *collect_data_files('zxcvbn'),
           *collect_data_files('jsonschema_specifications'), *collect_data_files('barcode')],
    hiddenimports=hidden,
    excludes=excluded,
    noarchive=False,
)
pyz = PYZ(a.pure)

common = dict(
    name='ILoveFMTLY',
    icon=ICON,
    console=False,       # app de janela, sem prompt preto
    upx=False,           # UPX costuma gerar falso positivo em antivírus
    debug=False,
    strip=False,
)

if ONEFILE:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], runtime_tmpdir=None, **common)
else:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, **common)
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='ILoveFMTLY')
