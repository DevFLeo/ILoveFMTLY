"""Mascote do app: ícone da janela, da barra de tarefas, da bandeja e dos atalhos.

Melhorias sobre a primeira versão:
- o mascote escolhido fica no config.json (Settings.mascot) e volta ao abrir;
- o AppUserModelID é definido uma vez, antes da primeira janela (é ele que agrupa
  o app na barra de tarefas e mantém o ícone fixado);
- atalhos editados pelo pywin32 (sem montar comando de PowerShell com o caminho,
  que quebrava com aspas no nome do usuário), incluindo o atalho fixado na barra;
- o ícone é copiado para %LOCALAPPDATA% só quando muda (o _MEIPASS do onefile some
  ao fechar, e os atalhos precisam de um arquivo que fique);
- fora do Windows (ou nos testes) tudo isso vira no-op seguro.
"""

import filecmp
import os
import shutil
import sys
from pathlib import Path

from core.paths import assets

APP_ID = 'ILoveFMTLY.App'
DEFAULT = 'folha'
# nome -> (ícone .ico, imagem .png) relativos a assets/
MASCOTS = {
    'folha': ('app.ico', 'logo.png'),
    'raposa': ('mascotes/raposa.ico', 'mascotes/raposa.png'),
    'coruja': ('mascotes/coruja.ico', 'mascotes/coruja.png'),
    'tartaruga': ('mascotes/tartaruga.ico', 'mascotes/tartaruga.png'),
    'castor': ('mascotes/castor.ico', 'mascotes/castor.png'),
}
LABELS = {'folha': 'Folha', 'raposa': 'Raposa', 'coruja': 'Coruja', 'tartaruga': 'Tartaruga',
          'castor': 'Castor'}


def _data_dir() -> Path:
    return Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local') / 'ILoveFMTLY'


def shortcut_paths() -> list[Path]:
    """Atalhos do app que o Windows mostra: área de trabalho, menu Iniciar e barra de tarefas."""
    home, roaming = Path.home(), Path(os.environ.get('APPDATA') or Path.home() / 'AppData' / 'Roaming')
    return [home / 'Desktop' / 'ILoveFMTLY.lnk',
            roaming / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'ILoveFMTLY.lnk',
            roaming / 'Microsoft' / 'Internet Explorer' / 'Quick Launch' / 'User Pinned' / 'TaskBar'
            / 'ILoveFMTLY.lnk']


def valid(name: str) -> str:
    return name if name in MASCOTS else DEFAULT


def icon_file(name: str) -> Path:
    return assets() / MASCOTS[valid(name)][0]


def image_file(name: str) -> Path:
    return assets() / MASCOTS[valid(name)][1]


def set_app_id() -> None:
    """Chame uma vez, antes de criar a primeira janela."""
    if sys.platform == 'win32':
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except (AttributeError, OSError):
            pass


def persistent_icon(name: str, data_dir: Path | None = None) -> Path:
    """Cópia do .ico fora da pasta do programa, atualizada só quando muda."""
    src = icon_file(name)
    folder = data_dir or _data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / 'icone_atual.ico'
    if not dest.exists() or not filecmp.cmp(src, dest, shallow=False):
        tmp = dest.with_suffix('.tmp')
        shutil.copyfile(src, tmp)
        tmp.replace(dest)
    return dest


def update_shortcuts(icon: Path, paths: list[Path] | None = None) -> int:
    """Troca o ícone dos atalhos que existem. Devolve quantos foram trocados."""
    if sys.platform != 'win32':
        return 0
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return 0
    changed = 0
    # Sem CoUninitialize: na thread da interface o Qt já usa COM, e desligar quebraria quem chamou.
    pythoncom.CoInitialize()
    shell = win32com.client.Dispatch('WScript.Shell')
    for lnk in (p for p in (paths or shortcut_paths()) if p.exists()):
        try:
            sc = shell.CreateShortcut(str(lnk))
            if sc.IconLocation.lower() != f'{icon},0'.lower():
                sc.IconLocation = f'{icon},0'
                sc.Save()
                changed += 1
        except Exception:  # atalho só leitura ou corrompido: segue com os outros
            continue
    if changed:
        import ctypes
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)  # Explorer recarrega ícones
    return changed
