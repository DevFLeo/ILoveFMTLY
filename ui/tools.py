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
from core.image_tools import B64_KINDS, BORDER_COLORS, EFFECTS, LAYOUTS
from core.images import ANIM_FORMATS, POSITIONS, ROTATE_ACTIONS
from core.video import VIDEO_EXTS
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
VIDEO = frozenset(VIDEO_EXTS)
DOCX = frozenset({'.docx', '.docm', '.dotx'})

GROUPS = ['Organizar', 'Otimizar', 'PDF para…', '…para PDF', 'Word', 'Imagens', 'Editar',
          'Segurança', 'JSON', 'XML', 'YAML', 'CSV', 'TOML', 'Texto', 'Codificar', 'Cripto',
          'QR e códigos', 'IA', 'Geradores', 'Web', 'Em breve']

OFFICE_LABEL = {'word': 'Word', 'excel': 'Excel', 'powerpoint': 'PowerPoint'}


from ui.tool_base import Param, Tool  # noqa: E402,F401  (reexportados)


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
    Tool('video2gif', 'Vídeo para GIF', 'Escolha o trecho com prévia; salva GIF ou WebP animado.',
         'Imagens', 'video', VIDEO, mode='dialog', dialog='video', fn='video.to_animation'),
    Tool('imgadjust', 'Ajustar cores', 'Brilho, contraste, saturação e nitidez.', 'Imagens', 'sun',
         RASTER, max_files=0, mode='folder', fn='image_tools.adjust',
         params=(Param('brightness', 'Brilho', 100, min=0, max=300, suffix=' %'),
                 Param('contrast', 'Contraste', 100, min=0, max=300, suffix=' %'),
                 Param('saturation', 'Saturação', 100, min=0, max=300, suffix=' %'),
                 Param('sharpness', 'Nitidez', 100, min=0, max=300, suffix=' %'))),
    Tool('imgfilter', 'Filtros', 'Preto e branco, sépia, desfoque, contorno, pôster…', 'Imagens',
         'wand-sparkles', RASTER, max_files=0, mode='folder', fn='image_tools.filter_images',
         params=(Param('effect', 'Efeito', EFFECTS[0], options=EFFECTS),
                 Param('strength', 'Intensidade', 50, min=1, max=100, suffix=' %'))),
    Tool('imgframe', 'Cantos redondos e borda', 'Arredonde os cantos e ponha uma moldura.',
         'Imagens', 'rounded-frame', RASTER, max_files=0, mode='folder', fn='image_tools.frame',
         params=(Param('radius', 'Raio dos cantos', 24, min=0, max=2000, suffix=' px'),
                 Param('border', 'Borda', 0, min=0, max=500, suffix=' px'),
                 Param('color', 'Cor da borda', 'Branco', options=tuple(BORDER_COLORS)))),
    Tool('imgnobg', 'Fundo transparente', 'Tira fundos lisos (ex.: branco) e salva PNG.', 'Imagens',
         'eraser', RASTER, max_files=0, mode='folder', fn='image_tools.remove_background',
         params=(Param('tolerance', 'Tolerância', 30, min=0, max=255),)),
    Tool('imgtarget', 'Comprimir até um tamanho', 'Diga o tamanho máximo em KB; o app acha a qualidade.',
         'Imagens', 'gauge', RASTER, max_files=0, mode='folder', fn='image_tools.compress_to_size',
         params=(Param('target_kb', 'Tamanho máximo', 200, min=5, max=100000, suffix=' KB'),
                 Param('fmt', 'Formato', 'JPG', options=('JPG', 'WebP')))),
    Tool('imgcollage', 'Colagem', 'Junte várias imagens lado a lado, empilhadas ou em grade.',
         'Imagens', 'grid-2x2', RASTER, max_files=0, min_files=2, mode='file', fn='image_tools.collage',
         ext='.png', out_suffix='_colagem',
         params=(Param('layout', 'Arranjo', LAYOUTS[0], options=LAYOUTS),
                 Param('gap', 'Espaço entre elas', 16, min=0, max=500, suffix=' px'),
                 Param('background', 'Fundo', 'Branco', options=tuple(BORDER_COLORS)))),
    Tool('imgpalette', 'Paleta de cores', 'As cores principais da imagem, com os códigos hex.',
         'Imagens', 'palette', RASTER, max_files=0, mode='folder', fn='image_tools.palette',
         params=(Param('colors', 'Quantas cores', 6, min=2, max=16),)),
    Tool('favicon', 'Gerar favicon', 'ICO, PNGs de 16 a 512, ícone da Apple e manifest.', 'Imagens',
         'app-window', RASTER, mode='folder', fn='image_tools.favicon'),
    Tool('img2b64', 'Imagem para Base64', 'Texto Base64 ou data URI para HTML e CSS.', 'Imagens',
         'binary', RASTER, max_files=0, mode='folder', fn='image_tools.to_base64',
         params=(Param('kind', 'Formato', B64_KINDS[0], options=B64_KINDS),)),
    Tool('b642img', 'Base64 para imagem', 'Cole o Base64 num .txt e vire imagem de novo.', 'Imagens',
         'file-image', frozenset({'.txt'}), max_files=0, mode='folder', fn='image_tools.from_base64'),
    Tool('imginfo', 'Informações da imagem', 'Medidas, cores, DPI, EXIF e GPS num relatório.', 'Imagens',
         'info', RASTER, max_files=0, mode='file', fn='image_tools.info', ext='.txt',
         out_suffix='_info'),
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

    # Assinar, tarjar, formulários
    Tool('sign', 'Assinar PDF', 'Desenhe a assinatura ou use uma imagem e carimbe na página.',
         'Editar', 'signature', PDF, mode='dialog', dialog='sign', fn='pdf_tools.sign_pdf',
         out_suffix='_assinado'),
    Tool('forms', 'Preencher formulário', 'Preencha os campos de um formulário PDF.',
         'Editar', 'text-cursor-input', PDF, mode='dialog', dialog='forms', fn='pdf_tools.fill_form',
         out_suffix='_preenchido'),
    Tool('redact', 'Tarja', 'Apague de verdade nomes, CPF, e-mails e outros trechos.',
         'Segurança', 'eye-off', PDF, mode='file', fn='pdf_tools.redact', ext='.pdf',
         out_suffix='_tarjado',
         params=(Param('terms', 'Termos (separe com ;)', '', hint='ex.: Maria Souza; 1000,00'),
                 Param('docs', 'Também CPF e CNPJ', 'Não', options=('Não', 'Sim')),
                 Param('contacts', 'Também e-mails e telefones', 'Não', options=('Não', 'Sim')))),

    # Em breve
    Tool('edit', 'Editar PDF', 'Texto, imagens e formas sobre as páginas.', 'Em breve', 'square-pen',
         PDF, soon=True),
    Tool('ocr', 'OCR', 'Torne PDFs escaneados pesquisáveis.', 'Em breve', 'scan-text', PDF, soon=True),
    Tool('pdfa', 'PDF/A', 'Formato para arquivamento de longo prazo.', 'Em breve', 'archive', PDF,
         soon=True),
]

# Ferramentas de desenvolvedor (fmtly.dev): ui/dev_tools.py usa Tool/Param, já definidos acima.
from ui.dev_tools import DEV_TOOLS  # noqa: E402

TOOLS[-3:-3] = DEV_TOOLS  # antes dos "em breve"
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


# --- tela simples: blocos grandes por tipo de arquivo ------------------------
@dataclass(frozen=True)
class Category:
    id: str
    title: str
    desc: str
    icon: str
    tools: tuple[str, ...]     # ids, na ordem em que aparecem


def _ids(pred) -> tuple[str, ...]:
    return tuple(t.id for t in TOOLS if pred(t))


CATEGORIES: list[Category] = [
    Category('pdf', 'PDF', 'Juntar, dividir, comprimir, assinar, proteger…', 'file',
             _ids(lambda t: '.pdf' in t.accepts and t.id not in ('pdf2gif',))),
    Category('office', 'Word e Office', 'Word, Excel e PowerPoint de e para PDF.', 'file-text',
             _ids(lambda t: t.mode != 'dev' and t.id != 'web2pdf' and (
                 t.group == 'Word' or t.accepts & (WORD | EXCEL | POWERPOINT)
                 or t.id in ('pdf2word', 'pdf2excel', 'pdf2ppt')))),
    Category('csv', 'CSV e planilhas', 'CSV para JSON, SQL, HTML; validar, limpar e comparar.', 'sheet',
             _ids(lambda t: t.group == 'CSV' or t.id in ('pdf2excel', 'excel2pdf', 'json-csv', 'xml-csv',
                                                          'yaml-csv'))),
    Category('images', 'Imagens', 'Converter, recortar, comprimir, borrar…', 'image',
             _ids(lambda t: (t.group == 'Imagens' and t.id not in ('video2gif', 'gifedit', 'gif2frames'))
                  or t.id in ('img2pdf', 'pdf2img'))),
    Category('video', 'Vídeo e GIF', 'Vídeo para GIF, editar e criar GIFs.', 'clapperboard',
             ('video2gif', 'gifedit', 'img2gif', 'gif2frames', 'pdf2gif')),
    Category('web', 'Web e e-book', 'HTML, Markdown, EPUB e outros para PDF.', 'book-open',
             ('web2pdf', 'ebook2pdf', 'pdf2html', 'docx2text', 'md-html', 'url-parse')),
    Category('data', 'JSON, XML, YAML e TOML', 'Formatar, validar, converter, consultar e gerar tipos.',
             'braces', _ids(lambda t: t.group in ('JSON', 'XML', 'YAML', 'TOML'))),
    Category('text', 'Texto e código', 'Contar, comparar, regex, Base64, URL, JWT, Unicode…', 'type',
             _ids(lambda t: t.group in ('Texto', 'Codificar', 'Web', 'IA'))),
    Category('dev', 'Cripto, QR e geradores', 'Hash, senhas, UUID, chaves, QR, código de barras…',
             'key-round', _ids(lambda t: t.group in ('Cripto', 'QR e códigos', 'Geradores'))),
]
CATEGORY_BY_ID = {c.id: c for c in CATEGORIES}

# Cor do glifo de cada bloco grande, pelo tipo de arquivo (ui/theme.GROUP_GLYPH):
# PDF vermelho, Word azul, CSV/Excel verde, ferramentas de dev cinza, imagem e o resto branco.
CATEGORY_GROUP = {'pdf': 'file:pdf', 'office': 'file:word', 'csv': 'file:excel', 'images': 'file:image',
                  'video': 'file:image', 'web': 'file:image', 'data': 'file:dev', 'text': 'file:dev',
                  'dev': 'file:dev'}


# --- cadastro: perfis ----------------------------------------------------------
@dataclass(frozen=True)
class Profile:
    id: str
    title: str
    icon: str
    goal: str                       # "Objetivo"
    ideal: str                      # "Ideal para"
    favorites: tuple[str, ...]      # ferramentas que aparecem primeiro
    categories: tuple[str, ...]     # ordem dos blocos grandes
    group: str                      # cor (via GROUP_GLYPH)


PROFILES: list[Profile] = [
    Profile('pessoal', 'Pessoal', 'user', 'Resolver o dia a dia rápido',
            'Fotos, documentos pessoais e GIFs',
            ('img2pdf', 'merge', 'compress', 'imgcompress', 'video2gif', 'pdf2img'),
            ('pdf', 'images', 'video', 'office', 'csv', 'web', 'data', 'text', 'dev'), 'Organizar'),
    Profile('estudante', 'Estudante', 'graduation-cap', 'Entregar trabalhos sem sufoco',
            'Escola, faculdade e concursos',
            ('merge', 'compress', 'word2pdf', 'pdf2word', 'numbers', 'web2pdf'),
            ('pdf', 'office', 'web', 'images', 'csv', 'video', 'text', 'data', 'dev'), '…para PDF'),
    Profile('instituicao', 'Instituição', 'building-2', 'Documentos oficiais e seguros',
            'Escolas, órgãos públicos e ONGs',
            ('sign', 'redact', 'forms', 'protect', 'numbers', 'watermark'),
            ('pdf', 'office', 'csv', 'images', 'web', 'video', 'text', 'data', 'dev'), 'PDF para…'),
    Profile('empresa', 'Empresa', 'briefcase', 'Agilizar o trabalho do escritório',
            'Contratos, planilhas e relatórios',
            ('sign', 'pdf2excel', 'protect', 'compress', 'docxreplace', 'compare'),
            ('pdf', 'office', 'csv', 'data', 'images', 'web', 'text', 'dev', 'video'), 'Otimizar'),
    Profile('personalizado', 'Personalizado', 'sliders-horizontal', 'Do seu jeito',
            'Quem quer escolher os próprios atalhos', (),
            ('pdf', 'office', 'csv', 'images', 'video', 'web', 'data', 'text', 'dev'), 'Editar'),
]
PROFILE_BY_ID = {p.id: p for p in PROFILES}
CUSTOM = 'personalizado'  # perfil em que a pessoa escolhe os cards fixados (Settings.pinned)
