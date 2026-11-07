"""Tipos das ferramentas (Param, Tool). Separado de ui/tools.py para ui/dev_tools.py
poder usá-los sem import circular."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Param:
    key: str
    label: str
    default: object            # str sem options = campo de texto
    options: tuple = ()        # escolha entre opções (texto)
    min: int = 0               # números inteiros
    max: int = 0
    suffix: str = ''
    hint: str = ''             # texto de exemplo em campos de texto
    file_filter: str = ''      # campo de arquivo (texto + "Escolher…"), ex.: 'Imagens (*.png)'


@dataclass(frozen=True)
class Tool:
    id: str
    title: str
    desc: str
    group: str
    icon: str                  # nome do SVG em assets/icons (Lucide)
    accepts: frozenset = frozenset()
    max_files: int = 1         # 0 = sem limite
    min_files: int = 1
    soon: bool = False
    needs: str | None = None   # 'word' | 'excel' | 'powerpoint'
    mode: str = 'editor'       # editor | to_editor | file | folder | dialog
    fn: str = ''               # função em core.convert, ou 'modulo.funcao' em core/
    ext: str = ''              # extensão de saída no modo file
    out_suffix: str = ''       # sufixo do nome sugerido no modo file/dialog (ex.: '_juntado')
    dialog: str = ''           # modo dialog: 'crop' | 'blur' | 'video'
    params: tuple = field(default_factory=tuple)
    dev_input: str = 'text'    # modo dev: 'text' | 'two' | 'file' | 'none' (ver core/dev)
    dev_labels: tuple = ('Entrada', 'Saída')

    @property
    def multi(self) -> bool:
        return self.max_files != 1
