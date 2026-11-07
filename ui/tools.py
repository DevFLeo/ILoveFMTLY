"""Catálogo das ferramentas mostradas como blocos no hub (dados puros).

Cada ferramenta tem um modo:
- editor:  abre os arquivos no editor de páginas com uma predefinição;
- to_editor: converte cada arquivo para PDF (core.convert.<fn>) e abre no editor;
- file:    converte e grava um arquivo escolhido pelo usuário (extensão `ext`);
- folder:  converte e grava vários arquivos numa pasta escolhida.
"""

from dataclasses import dataclass, field
from pathlib import Path

from core.convert import (EBOOK_EXTS, EXCEL_EXTS, IMAGE_FORMATS, POWERPOINT_EXTS,
                          RASTER_EXTS, WEB_EXTS)
from core.engines.word import WORD_INPUT_EXTS
from core.importer import IMAGE_EXTS

PDF = frozenset({'.pdf'})
IMAGES = frozenset(IMAGE_EXTS)
RASTER = frozenset(RASTER_EXTS)
WORD = frozenset(WORD_INPUT_EXTS)
EXCEL = frozenset(EXCEL_EXTS)
POWERPOINT = frozenset(POWERPOINT_EXTS)
WEB = frozenset(WEB_EXTS)
EBOOK = frozenset(EBOOK_EXTS)
GIF = frozenset({'.gif'})

GROUPS = ['Organizar', 'Otimizar', 'PDF para…', '…para PDF', 'Imagens', 'Editar',
          'Segurança', 'Em breve']

OFFICE_LABEL = {'word': 'Word', 'excel': 'Excel', 'powerpoint': 'PowerPoint'}


@dataclass(frozen=True)
class Param:
    key: str
    label: str
    default: object
    options: tuple = ()        # escolha entre opções (texto)
    min: int = 0               # números inteiros
    max: int = 0
    suffix: str = ''


@dataclass(frozen=True)
class Tool:
    id: str
    title: str
    desc: str
    group: str
    glyph: str
    accepts: frozenset = frozenset()
    max_files: int = 1         # 0 = sem limite
    min_files: int = 1
    soon: bool = False
    needs: str | None = None   # 'word' | 'excel' | 'powerpoint'
    mode: str = 'editor'       # editor | to_editor | file | folder
    fn: str = ''               # nome da função em core.convert
    ext: str = ''              # extensão de saída no modo file
    params: tuple = field(default_factory=tuple)

    @property
    def multi(self) -> bool:
        return self.max_files != 1


DPI = Param('dpi', 'Resolução', 150, min=36, max=600, suffix=' dpi')
FORMAT = Param('fmt', 'Formato', 'PNG', options=tuple(IMAGE_FORMATS))
QUALITY = Param('quality', 'Qualidade', 80, min=10, max=100, suffix=' %')
FRAME = Param('frame_ms', 'Tempo de cada quadro', 600, min=50, max=10000, suffix=' ms')

TOOLS: list[Tool] = [
    # Organizar
    Tool('merge', 'Juntar PDF', 'Combine vários PDFs e imagens na ordem que quiser.',
         'Organizar', '⊕', PDF | IMAGES, max_files=0),
    Tool('split', 'Dividir PDF', 'Separe intervalos de páginas em arquivos independentes.',
         'Organizar', '✂', PDF),
    Tool('organize', 'Organizar páginas', 'Reordene, gire e exclua páginas arrastando.',
         'Organizar', '▦', PDF | IMAGES, max_files=0),
    Tool('rotate', 'Girar PDF', 'Gire uma ou várias páginas de uma vez.', 'Organizar', '↻', PDF),
    Tool('extract', 'Extrair páginas', 'Salve só as páginas que escolher.', 'Organizar', '⇱', PDF),
    Tool('crop', 'Recortar margens', 'Corte o espaço em branco ao redor do conteúdo.',
         'Organizar', '⌗', PDF, mode='to_editor', fn='crop_margins',
         params=(Param('margin', 'Folga', 12, min=0, max=144, suffix=' pt'),)),

    # Otimizar
    Tool('compress', 'Comprimir PDF', 'Reduza o tamanho do arquivo reduzindo imagens.',
         'Otimizar', '⇲', PDF),
    Tool('repair', 'Reparar PDF', 'Recupere PDFs danificados ou corrompidos.', 'Otimizar', '✚', PDF),
    Tool('grayscale', 'Escala de cinza', 'Páginas em tons de cinza (viram imagem).',
         'Otimizar', '◐', PDF, mode='to_editor', fn='grayscale_pdf', params=(DPI,)),

    # PDF para…
    Tool('pdf2word', 'PDF para Word', 'Documento DOCX editável.', 'PDF para…', 'W', PDF,
         needs='word', mode='file', fn='pdf_to_word', ext='.docx'),
    Tool('pdf2excel', 'PDF para Excel', 'Cada tabela encontrada vira uma aba.', 'PDF para…', 'X',
         PDF, mode='file', fn='pdf_to_excel', ext='.xlsx'),
    Tool('pdf2ppt', 'PDF para PowerPoint', 'Uma página por slide.', 'PDF para…', 'P', PDF,
         needs='powerpoint', mode='file', fn='pdf_to_powerpoint', ext='.pptx', params=(DPI,)),
    Tool('pdf2img', 'PDF para imagem', 'PNG, JPG, WebP, TIFF... uma por página.', 'PDF para…', '▤',
         PDF, max_files=0, mode='folder', fn='pdf_to_images', params=(FORMAT, DPI)),
    Tool('pdf2gif', 'PDF para GIF', 'GIF animado: cada página vira um quadro.', 'PDF para…', '▶',
         PDF, mode='file', fn='pdf_to_gif', ext='.gif',
         params=(Param('dpi', 'Resolução', 72, min=24, max=200, suffix=' dpi'), FRAME)),
    Tool('pdf2txt', 'PDF para TXT', 'Só o texto, página por página.', 'PDF para…', 'T', PDF,
         mode='file', fn='pdf_to_text', ext='.txt'),
    Tool('pdf2html', 'PDF para HTML', 'Página web com o texto e as imagens.', 'PDF para…', '‹›',
         PDF, mode='file', fn='pdf_to_html', ext='.html'),
    Tool('pdf2svg', 'PDF para SVG', 'Vetores: uma imagem SVG por página.', 'PDF para…', '◇', PDF,
         mode='folder', fn='pdf_to_svg'),
    Tool('extractimg', 'Extrair imagens', 'Salve as imagens embutidas no PDF.', 'PDF para…', '⧉',
         PDF, mode='folder', fn='extract_images'),

    # …para PDF
    Tool('word2pdf', 'Word para PDF', 'DOCX, DOC, RTF, ODT e TXT em PDF.', '…para PDF', 'W', WORD,
         max_files=0, needs='word', mode='to_editor', fn='word_to_pdf'),
    Tool('excel2pdf', 'Excel para PDF', 'XLSX, XLS, ODS e CSV em PDF.', '…para PDF', 'X', EXCEL,
         max_files=0, needs='excel', mode='to_editor', fn='excel_to_pdf'),
    Tool('ppt2pdf', 'PowerPoint para PDF', 'PPTX, PPT e ODP em PDF.', '…para PDF', 'P', POWERPOINT,
         max_files=0, needs='powerpoint', mode='to_editor', fn='powerpoint_to_pdf'),
    Tool('img2pdf', 'Imagem para PDF', 'JPG, PNG, TIFF e outras imagens em PDF.', '…para PDF', '▣',
         IMAGES, max_files=0),
    Tool('web2pdf', 'HTML / Markdown para PDF', 'Páginas HTML, Markdown e TXT em PDF A4.',
         '…para PDF', '‹›', WEB, max_files=0, mode='to_editor', fn='web_to_pdf'),
    Tool('ebook2pdf', 'E-book para PDF', 'EPUB, MOBI, FB2, XPS, CBZ e SVG em PDF.', '…para PDF',
         '❏', EBOOK, max_files=0, mode='to_editor', fn='ebook_to_pdf'),

    # Imagens
    Tool('imgconvert', 'Converter imagem', 'PNG, JPG, WebP, BMP, TIFF, ICO e GIF.', 'Imagens', '⇄',
         RASTER, max_files=0, mode='folder', fn='convert_images', params=(FORMAT, QUALITY)),
    Tool('imgresize', 'Redimensionar imagem', 'Aumente ou reduza por porcentagem.', 'Imagens', '⤡',
         RASTER, max_files=0, mode='folder', fn='resize_images',
         params=(Param('percent', 'Tamanho', 50, min=1, max=1000, suffix=' %'),)),
    Tool('imgcompress', 'Comprimir imagem', 'Arquivos menores com pouca perda visível.', 'Imagens',
         '⇲', RASTER, max_files=0, mode='folder', fn='compress_images', params=(QUALITY,)),
    Tool('img2gif', 'Criar GIF', 'Várias imagens viram um GIF animado.', 'Imagens', '▶', RASTER,
         max_files=0, min_files=2, mode='file', fn='images_to_gif', ext='.gif',
         params=(FRAME, Param('width', 'Largura (0 = original)', 0, min=0, max=4000, suffix=' px'))),
    Tool('gif2frames', 'GIF para quadros', 'Cada quadro do GIF vira um PNG.', 'Imagens', '▥', GIF,
         mode='folder', fn='gif_to_frames'),

    # Editar
    Tool('numbers', 'Numerar páginas', 'Adicione números ao rodapé das páginas.', 'Editar', '#', PDF),
    Tool('watermark', "Marca d'água", 'Carimbe um texto em diagonal sobre as páginas.',
         'Editar', '≋', PDF),
    Tool('compare', 'Comparar PDF', 'Relatório com as diferenças de texto entre dois PDFs.',
         'Editar', '⇋', PDF, min_files=2, max_files=2, mode='file', fn='compare_pdfs', ext='.html'),

    # Segurança
    Tool('protect', 'Proteger PDF', 'Senha AES-256 para abrir o arquivo.', 'Segurança', '⚿', PDF),
    Tool('unlock', 'Desbloquear PDF', 'Remova a senha de um PDF (você precisa saber a senha).',
         'Segurança', '⚷', PDF),
    Tool('metadata', 'Remover metadados', 'Apague autor, software, datas e XMP.',
         'Segurança', '⌫', PDF),

    # Em breve
    Tool('sign', 'Assinar PDF', 'Assinatura desenhada ou em imagem.', 'Em breve', '✍', soon=True),
    Tool('redact', 'Tarja', 'Apague de verdade trechos sensíveis.', 'Em breve', '▬', soon=True),
    Tool('edit', 'Editar PDF', 'Texto, imagens e formas sobre as páginas.', 'Em breve', '✎', soon=True),
    Tool('forms', 'Formulários', 'Preencha campos de formulários PDF.', 'Em breve', '☑', soon=True),
    Tool('ocr', 'OCR', 'Torne PDFs escaneados pesquisáveis.', 'Em breve', '⌕', soon=True),
    Tool('pdfa', 'PDF/A', 'Formato para arquivamento de longo prazo.', 'Em breve', 'A', soon=True),
]

BY_ID = {t.id: t for t in TOOLS}


def accepts_count(tool: Tool, n: int) -> bool:
    return n >= tool.min_files and (tool.max_files == 0 or n <= tool.max_files)


def compatible(paths: list[Path]) -> list[Tool]:
    """Ferramentas prontas que aceitam TODOS os arquivos (e a quantidade) informados."""
    exts = {Path(p).suffix.lower() for p in paths}
    if not exts:
        return []
    return [t for t in TOOLS if not t.soon and exts <= t.accepts and accepts_count(t, len(paths))]


def file_filter(tool: Tool) -> str:
    patterns = ' '.join(f'*{e}' for e in sorted(tool.accepts))
    return f'Arquivos aceitos ({patterns})'
