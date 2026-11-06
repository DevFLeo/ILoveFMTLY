"""Catálogo das ferramentas mostradas como blocos no hub (dados puros)."""

from dataclasses import dataclass
from pathlib import Path

from core.engines.word import WORD_INPUT_EXTS
from core.importer import IMAGE_EXTS

PDF = frozenset({'.pdf'})
IMAGES = frozenset(IMAGE_EXTS)
WORD = frozenset(WORD_INPUT_EXTS)

GROUPS = ['Organizar', 'Otimizar', 'Converter', 'Editar', 'Segurança', 'Em breve']


@dataclass(frozen=True)
class Tool:
    id: str
    title: str
    desc: str
    group: str
    glyph: str
    accepts: frozenset = frozenset()
    multi: bool = False        # aceita vários arquivos de uma vez
    soon: bool = False         # ainda não implementado (bloco apagado)
    needs_word: bool = False   # depende do Microsoft Word instalado


TOOLS: list[Tool] = [
    Tool('merge', 'Juntar PDF', 'Combine vários PDFs e imagens na ordem que quiser.',
         'Organizar', '⊕', PDF | IMAGES, multi=True),
    Tool('split', 'Dividir PDF', 'Separe intervalos de páginas em arquivos independentes.',
         'Organizar', '✂', PDF),
    Tool('organize', 'Organizar páginas', 'Reordene, gire e exclua páginas arrastando.',
         'Organizar', '▦', PDF | IMAGES, multi=True),
    Tool('rotate', 'Girar PDF', 'Gire uma ou várias páginas de uma vez.',
         'Organizar', '↻', PDF),
    Tool('extract', 'Extrair páginas', 'Salve só as páginas que escolher.',
         'Organizar', '⇱', PDF),

    Tool('compress', 'Comprimir PDF', 'Reduza o tamanho do arquivo reduzindo imagens.',
         'Otimizar', '⇲', PDF),
    Tool('repair', 'Reparar PDF', 'Recupere PDFs danificados ou corrompidos.',
         'Otimizar', '✚', PDF),

    Tool('word2pdf', 'Word para PDF', 'DOCX, DOC, RTF, ODT e TXT em PDF.',
         'Converter', 'W', WORD, multi=True, needs_word=True),
    Tool('pdf2word', 'PDF para Word', 'Converta um PDF em documento DOCX editável.',
         'Converter', 'W', PDF, needs_word=True),
    Tool('img2pdf', 'Imagem para PDF', 'JPG, PNG, TIFF e outras imagens em PDF.',
         'Converter', '▣', IMAGES, multi=True),
    Tool('pdf2img', 'PDF para imagem', 'Cada página vira uma imagem PNG ou JPG.',
         'Converter', '▤', PDF),

    Tool('numbers', 'Numerar páginas', 'Adicione números ao rodapé das páginas.',
         'Editar', '#', PDF),
    Tool('watermark', "Marca d'água", 'Carimbe um texto em diagonal sobre as páginas.',
         'Editar', '≋', PDF),

    Tool('protect', 'Proteger PDF', 'Senha AES-256 para abrir o arquivo.',
         'Segurança', '⚿', PDF),
    Tool('unlock', 'Desbloquear PDF', 'Remova a senha de um PDF (você precisa saber a senha).',
         'Segurança', '⚷', PDF),
    Tool('metadata', 'Remover metadados', 'Apague autor, software, datas e XMP.',
         'Segurança', '⌫', PDF),

    Tool('sign', 'Assinar PDF', 'Assinatura desenhada ou em imagem.', 'Em breve', '✍', soon=True),
    Tool('redact', 'Tarja', 'Apague de verdade trechos sensíveis.', 'Em breve', '▬', soon=True),
    Tool('edit', 'Editar PDF', 'Texto, imagens e formas sobre as páginas.', 'Em breve', '✎', soon=True),
    Tool('forms', 'Formulários', 'Preencha campos de formulários PDF.', 'Em breve', '☑', soon=True),
    Tool('ocr', 'OCR', 'Torne PDFs escaneados pesquisáveis.', 'Em breve', '⌕', soon=True),
    Tool('compare', 'Comparar PDF', 'Veja as diferenças entre duas versões.', 'Em breve', '⇄', soon=True),
    Tool('crop', 'Recortar PDF', 'Corte as margens das páginas.', 'Em breve', '⌗', soon=True),
    Tool('pdfa', 'PDF/A', 'Formato para arquivamento de longo prazo.', 'Em breve', 'A', soon=True),
]

BY_ID = {t.id: t for t in TOOLS}


def compatible(paths: list[Path]) -> list[Tool]:
    """Ferramentas prontas que aceitam TODOS os arquivos (e a quantidade) informados."""
    exts = {Path(p).suffix.lower() for p in paths}
    if not exts:
        return []
    return [t for t in TOOLS
            if not t.soon and exts <= t.accepts and (t.multi or len(paths) == 1)]


def file_filter(tool: Tool) -> str:
    patterns = ' '.join(f'*{e}' for e in sorted(tool.accepts))
    return f'Arquivos aceitos ({patterns})'
