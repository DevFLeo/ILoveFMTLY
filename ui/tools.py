"""Catálogo das ferramentas mostradas como blocos no hub (dados puros).

Cada ferramenta tem um modo:
- editor:  abre os arquivos no editor de páginas com uma predefinição;
- to_editor: converte cada arquivo para PDF (core.convert.<fn>) e abre no editor;
- file:    converte e grava um arquivo escolhido pelo usuário (extensão `ext`);
- folder:  converte e grava vários arquivos numa pasta escolhida;
- dialog:  abre um diálogo próprio (recorte, borrar) e grava um arquivo escolhido.
"""

from dataclasses import dataclass, field
from pathlib import Path

from core.convert import (EBOOK_EXTS, EXCEL_EXTS, IMAGE_FORMATS, POWERPOINT_EXTS,
                          RASTER_EXTS, WEB_EXTS)
from core.docx_tools import EXPORT_FORMATS
from core.images import ANIM_FORMATS, POSITIONS, ROTATE_ACTIONS
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
ANIMATED = frozenset({'.gif', '.webp'})
DOCX = frozenset({'.docx', '.docm', '.dotx'})

GROUPS = ['Organizar', 'Otimizar', 'PDF para…', '…para PDF', 'Word', 'Imagens', 'Editar',
          'Segurança', 'Em breve']

OFFICE_LABEL = {'word': 'Word', 'excel': 'Excel', 'powerpoint': 'PowerPoint'}


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
    dialog: str = ''           # modo dialog: 'crop' | 'blur' (ui/crop_dialog.py)
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
         'Organizar', 'combine', PDF | IMAGES, max_files=0),
    Tool('split', 'Dividir PDF', 'Separe intervalos de páginas em arquivos independentes.',
         'Organizar', 'split', PDF),
    Tool('organize', 'Organizar páginas', 'Reordene, gire e exclua páginas arrastando.',
         'Organizar', 'layout-grid', PDF | IMAGES, max_files=0),
    Tool('rotate', 'Girar PDF', 'Gire uma ou várias páginas de uma vez.', 'Organizar', 'rotate-cw', PDF),
    Tool('extract', 'Extrair páginas', 'Salve só as páginas que escolher.', 'Organizar', 'file-output', PDF),
    Tool('crop', 'Recortar margens', 'Corte o espaço em branco ao redor do conteúdo.',
         'Organizar', 'crop', PDF, mode='to_editor', fn='crop_margins',
         params=(Param('margin', 'Folga', 12, min=0, max=144, suffix=' pt'),)),

    # Otimizar
    Tool('compress', 'Comprimir PDF', 'Reduza o tamanho do arquivo reduzindo imagens.',
         'Otimizar', 'shrink', PDF),
    Tool('repair', 'Reparar PDF', 'Recupere PDFs danificados ou corrompidos.', 'Otimizar', 'wrench', PDF),
    Tool('grayscale', 'Escala de cinza', 'Páginas em tons de cinza (viram imagem).',
         'Otimizar', 'contrast', PDF, mode='to_editor', fn='grayscale_pdf', params=(DPI,)),

    # PDF para…
    Tool('pdf2word', 'PDF para Word', 'Documento DOCX editável.', 'PDF para…', 'file-text', PDF,
         needs='word', mode='file', fn='pdf_to_word', ext='.docx'),
    Tool('pdf2excel', 'PDF para Excel', 'Cada tabela encontrada vira uma aba.', 'PDF para…', 'sheet',
         PDF, mode='file', fn='pdf_to_excel', ext='.xlsx'),
    Tool('pdf2ppt', 'PDF para PowerPoint', 'Uma página por slide.', 'PDF para…', 'presentation', PDF,
         needs='powerpoint', mode='file', fn='pdf_to_powerpoint', ext='.pptx', params=(DPI,)),
    Tool('pdf2img', 'PDF para imagem', 'PNG, JPG, WebP, TIFF... uma por página.', 'PDF para…', 'image',
         PDF, max_files=0, mode='folder', fn='pdf_to_images', params=(FORMAT, DPI)),
    Tool('pdf2gif', 'PDF para GIF', 'GIF animado: cada página vira um quadro.', 'PDF para…', 'film',
         PDF, mode='file', fn='pdf_to_gif', ext='.gif',
         params=(Param('dpi', 'Resolução', 72, min=24, max=200, suffix=' dpi'), FRAME)),
    Tool('pdf2txt', 'PDF para TXT', 'Só o texto, página por página.', 'PDF para…', 'type', PDF,
         mode='file', fn='pdf_to_text', ext='.txt'),
    Tool('pdf2html', 'PDF para HTML', 'Página web com o texto e as imagens.', 'PDF para…', 'code',
         PDF, mode='file', fn='pdf_to_html', ext='.html'),
    Tool('pdf2svg', 'PDF para SVG', 'Vetores: uma imagem SVG por página.', 'PDF para…', 'pen-tool', PDF,
         mode='folder', fn='pdf_to_svg'),
    Tool('extractimg', 'Extrair imagens', 'Salve as imagens embutidas no PDF.', 'PDF para…', 'images',
         PDF, mode='folder', fn='extract_images'),

    # …para PDF
    Tool('word2pdf', 'Word para PDF', 'DOCX, DOC, RTF, ODT e TXT em PDF.', '…para PDF', 'file-text', WORD,
         max_files=0, needs='word', mode='to_editor', fn='word_to_pdf'),
    Tool('excel2pdf', 'Excel para PDF', 'XLSX, XLS, ODS e CSV em PDF.', '…para PDF', 'sheet', EXCEL,
         max_files=0, needs='excel', mode='to_editor', fn='excel_to_pdf'),
    Tool('ppt2pdf', 'PowerPoint para PDF', 'PPTX, PPT e ODP em PDF.', '…para PDF', 'presentation', POWERPOINT,
         max_files=0, needs='powerpoint', mode='to_editor', fn='powerpoint_to_pdf'),
    Tool('img2pdf', 'Imagem para PDF', 'JPG, PNG, TIFF e outras imagens em PDF.', '…para PDF', 'file-image',
         IMAGES, max_files=0),
    Tool('web2pdf', 'HTML / Markdown para PDF', 'Páginas HTML, Markdown e TXT em PDF A4.',
         '…para PDF', 'file-code', WEB, max_files=0, mode='to_editor', fn='web_to_pdf'),
    Tool('ebook2pdf', 'E-book para PDF', 'EPUB, MOBI, FB2, XPS, CBZ e SVG em PDF.', '…para PDF',
         'book-open', EBOOK, max_files=0, mode='to_editor', fn='ebook_to_pdf'),

    # Word (sem Office)
    Tool('docxclean', 'Limpar DOCX', 'Tire autor, comentários e revisões antes de enviar.', 'Word',
         'brush-cleaning', DOCX, max_files=0, mode='folder', fn='docx_tools.clean'),
    Tool('docxreplace', 'Localizar e substituir', 'Troque um texto em um ou vários DOCX.', 'Word',
         'replace', DOCX, max_files=0, mode='folder', fn='docx_tools.replace',
         params=(Param('find', 'Localizar', '', hint='ex.: Contratante'),
                 Param('replace', 'Substituir por', '', hint='ex.: Locatária'),
                 Param('match_case', 'Diferenciar maiúsculas', 'Sim', options=('Sim', 'Não')))),
    Tool('docxmerge', 'Juntar DOCX', 'Vários DOCX viram um, na ordem escolhida.', 'Word', 'files',
         DOCX, max_files=0, min_files=2, mode='file', fn='docx_tools.merge', ext='.docx',
         out_suffix='_juntado'),
    Tool('docx2text', 'DOCX para TXT / Markdown / HTML', 'Texto puro ou web; imagens numa pasta.',
         'Word', 'file-type', DOCX, max_files=0, mode='folder', fn='docx_tools.export_text',
         params=(Param('fmt', 'Formato', 'Markdown', options=tuple(EXPORT_FORMATS)),)),

    # Imagens
    Tool('imgconvert', 'Converter imagem', 'PNG, JPG, WebP, BMP, TIFF, ICO e GIF.', 'Imagens', 'refresh-cw',
         RASTER, max_files=0, mode='folder', fn='convert_images', params=(FORMAT, QUALITY)),
    Tool('imgresize', 'Redimensionar imagem', 'Aumente ou reduza por porcentagem.', 'Imagens', 'scaling',
         RASTER, max_files=0, mode='folder', fn='resize_images',
         params=(Param('percent', 'Tamanho', 50, min=1, max=1000, suffix=' %'),)),
    Tool('imgcompress', 'Comprimir imagem', 'Arquivos menores com pouca perda visível.', 'Imagens',
         'minimize-2', RASTER, max_files=0, mode='folder', fn='compress_images', params=(QUALITY,)),
    Tool('img2gif', 'Criar GIF', 'Várias imagens viram um GIF animado.', 'Imagens', 'clapperboard', RASTER,
         max_files=0, min_files=2, mode='file', fn='images_to_gif', ext='.gif',
         params=(FRAME, Param('width', 'Largura (0 = original)', 0, min=0, max=4000, suffix=' px'))),
    Tool('imgcrop', 'Recortar imagem', 'Arraste a área; proporção livre, 1:1, 4:3 ou 16:9.',
         'Imagens', 'crop', IMAGES, mode='dialog', dialog='crop', fn='images.crop',
         out_suffix='_recortada'),
    Tool('imgrotate', 'Girar / espelhar imagem', '90°, 180° ou espelho; GIFs continuam animados.',
         'Imagens', 'flip-horizontal-2', RASTER, max_files=0, mode='folder', fn='images.rotate',
         params=(Param('action', 'Ação', 'Girar 90° à direita', options=tuple(ROTATE_ACTIONS)),)),
    Tool('imgexif', 'Remover EXIF / GPS', 'Tire câmera, local e data das fotos antes de enviar.',
         'Imagens', 'map-pin-off', RASTER, max_files=0, mode='folder', fn='images.strip_exif'),
    Tool('imgwatermark', "Marca d'água em imagem", 'Texto ou logo sobre várias imagens.', 'Imagens',
         'stamp', IMAGES, max_files=0, mode='folder', fn='images.watermark',
         params=(Param('text', 'Texto', '', hint='ex.: CONFIDENCIAL'),
                 Param('logo', 'Logo (opcional)', '',
                       file_filter='Imagens (*.png *.jpg *.jpeg *.webp *.bmp)'),
                 Param('position', 'Posição', 'Inferior direito', options=POSITIONS),
                 Param('opacity', 'Opacidade', 50, min=5, max=100, suffix=' %'))),
    Tool('imgblur', 'Borrar área', 'Pixele rostos, placas ou dados numa parte da imagem.',
         'Imagens', 'scan-face', IMAGES, mode='dialog', dialog='blur', fn='images.blur_area',
         out_suffix='_borrada'),
    Tool('gifedit', 'Editar GIF', 'Velocidade, trecho, largura, inverter; salva GIF ou WebP.',
         'Imagens', 'sliders-horizontal', ANIMATED, max_files=0, mode='folder',
         fn='images.edit_gif',
         params=(Param('speed', 'Velocidade', 100, min=10, max=1000, suffix=' %'),
                 Param('first', 'Do quadro', 1, min=1, max=100000),
                 Param('last', 'Até o quadro (0 = fim)', 0, min=0, max=100000),
                 Param('width', 'Largura (0 = original)', 0, min=0, max=4000, suffix=' px'),
                 Param('reverse', 'Inverter', 'Não', options=('Não', 'Sim')),
                 Param('fmt', 'Salvar como', 'GIF', options=tuple(ANIM_FORMATS)))),
    Tool('gif2frames', 'GIF para quadros', 'Cada quadro do GIF vira um PNG.', 'Imagens', 'layers', GIF,
         mode='folder', fn='gif_to_frames'),

    # Editar
    Tool('numbers', 'Numerar páginas', 'Adicione números ao rodapé das páginas.', 'Editar', 'list-ordered', PDF),
    Tool('watermark', "Marca d'água", 'Carimbe um texto em diagonal sobre as páginas.',
         'Editar', 'stamp', PDF),
    Tool('compare', 'Comparar PDF', 'Relatório com as diferenças de texto entre dois PDFs.',
         'Editar', 'git-compare-arrows', PDF, min_files=2, max_files=2, mode='file', fn='compare_pdfs',
         ext='.html', out_suffix='_comparacao'),

    # Segurança
    Tool('protect', 'Proteger PDF', 'Senha AES-256 para abrir o arquivo.', 'Segurança', 'lock', PDF),
    Tool('unlock', 'Desbloquear PDF', 'Remova a senha de um PDF (você precisa saber a senha).',
         'Segurança', 'lock-open', PDF),
    Tool('metadata', 'Remover metadados', 'Apague autor, software, datas e XMP.',
         'Segurança', 'eraser', PDF),

    # Em breve
    Tool('sign', 'Assinar PDF', 'Assinatura desenhada ou em imagem.', 'Em breve', 'signature', soon=True),
    Tool('redact', 'Tarja', 'Apague de verdade trechos sensíveis.', 'Em breve', 'eye-off', soon=True),
    Tool('edit', 'Editar PDF', 'Texto, imagens e formas sobre as páginas.', 'Em breve', 'square-pen', soon=True),
    Tool('forms', 'Formulários', 'Preencha campos de formulários PDF.', 'Em breve', 'text-cursor-input', soon=True),
    Tool('ocr', 'OCR', 'Torne PDFs escaneados pesquisáveis.', 'Em breve', 'scan-text', soon=True),
    Tool('pdfa', 'PDF/A', 'Formato para arquivamento de longo prazo.', 'Em breve', 'archive', soon=True),
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
