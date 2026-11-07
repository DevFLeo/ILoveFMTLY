"""Preferências e cadastro do usuário, salvos num config.json pequeno.

Onde fica o arquivo:
- rodando pelo Python: na raiz do projeto;
- no .exe: ao lado do ILoveFMTLY.exe (a pasta extraída do PyInstaller é
  temporária e não serve). Se essa pasta não aceitar escrita (ex.: Arquivos de
  Programas), cai para %APPDATA%\\ILoveFMTLY.

Arquivo ausente, corrompido ou com valor estranho nunca impede o app de abrir:
o que não der para ler vira o valor padrão.
"""

import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

FILENAME = 'config.json'
MODES = ('simple', 'detailed')


def _home_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _fallback_dir() -> Path:
    return Path(os.environ.get('APPDATA') or Path.home()) / 'ILoveFMTLY'


def default_path() -> Path:
    """config.json que já existe (pasta do app primeiro) ou o lugar onde criar."""
    main = _home_dir() / FILENAME
    backup = _fallback_dir() / FILENAME
    if not main.exists() and backup.exists():
        return backup
    return main


@dataclass
class Settings:
    name: str = ''              # "Como devo te chamar?"
    profile: str = ''           # id do perfil (ui/tools.PROFILES); vazio = sem cadastro
    mode: str = 'simple'        # tela inicial: 'simple' (blocos grandes) | 'detailed'
    theme: str = 'Noite'        # nome em ui/theme.THEMES
    font: str = 'IBM Plex Sans'
    text_size: str = 'Normal'   # nome em ui/theme.TEXT_SIZES
    welcomed: str = ''          # 'sim' depois que o cadastro já foi mostrado uma vez
    path: Path | None = field(default=None, repr=False, compare=False)

    @property
    def registered(self) -> bool:
        return bool(self.profile)

    @classmethod
    def load(cls, path: Path | None = None) -> 'Settings':
        path = Path(path) if path else default_path()
        settings = cls(path=path)
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return settings
        if not isinstance(data, dict):
            return settings
        for f in fields(cls):
            value = data.get(f.name)
            if f.name != 'path' and isinstance(value, str):
                setattr(settings, f.name, value.strip())
        if settings.mode not in MODES:
            settings.mode = 'simple'
        return settings

    def to_dict(self) -> dict:
        data = asdict(self)
        data.pop('path')
        return data

    def save(self) -> Path | None:
        """Grava o JSON. Sem caminho (testes), não grava nada."""
        if self.path is None:
            return None
        text = json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + '\n'
        try:
            return self._write(self.path, text)
        except OSError:
            self.path = _fallback_dir() / FILENAME
            return self._write(self.path, text)

    @staticmethod
    def _write(path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.tmp')
        tmp.write_text(text, encoding='utf-8')
        tmp.replace(path)  # troca atômica: nunca fica um JSON pela metade
        return path
