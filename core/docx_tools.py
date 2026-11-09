"""Word B: ajustes em DOCX sem abrir o Word.

Tudo é feito direto no pacote ZIP/XML do DOCX (lxml) ou com bibliotecas puras
(python-docx, docxcompose, mammoth, markdownify). O original nunca é alterado:
cada função grava um arquivo novo e devolve a lista de caminhos gerados.
"""

import re
import zipfile
from pathlib import Path

from lxml import etree

from core.convert import unique

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
_XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'
_OLE_MAGIC = bytes.fromhex('D0CF11E0A1B11AE1')

# partes com texto do documento
_STORY = re.compile(r'^word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$')
# partes de comentários e autores, removidas na limpeza
_COMMENT_PARTS = re.compile(r'^word/(comments\w*|people)\.xml$')

_UNWRAP = ('ins', 'moveTo')                       # revisão aceita: fica o conteúdo
_DROP = ('del', 'moveFrom', 'rPrChange', 'pPrChange', 'sectPrChange', 'tblPrChange',
         'trPrChange', 'tcPrChange', 'tblGridChange', 'numberingChange', 'cellIns', 'cellDel',
         'moveFromRangeStart', 'moveFromRangeEnd', 'moveToRangeStart', 'moveToRangeEnd',
         'commentRangeStart', 'commentRangeEnd')

EXPORT_FORMATS = {'TXT': '.txt', 'Markdown': '.md', 'HTML': '.html'}


class DocxError(Exception):
    """DOCX inválido, protegido por senha ou parâmetro inválido."""


def _w(tag: str) -> str:
    return f'{{{W}}}{tag}'


# --- pacote ------------------------------------------------------------------
def _check(path: Path) -> None:
    path = Path(path)
    try:
        head = path.read_bytes()[:8]
    except OSError as exc:
        raise DocxError(f'{path.name}: não foi possível ler ({exc}).') from None
    if head == _OLE_MAGIC:
        raise DocxError(f'{path.name}: documento protegido por senha. Remova a senha no Word e tente de novo.')
    if not zipfile.is_zipfile(path):
        raise DocxError(f'{path.name}: não é um DOCX válido.')
    with zipfile.ZipFile(path) as z:
        if 'word/document.xml' not in z.namelist():
            raise DocxError(f'{path.name}: não é um DOCX válido (sem word/document.xml).')


def _read(path: Path) -> list[tuple[zipfile.ZipInfo, bytes]]:
    _check(path)
    with zipfile.ZipFile(path) as z:
        return [(info, z.read(info)) for info in z.infolist()]


def _write(entries: list[tuple[zipfile.ZipInfo, bytes]], out: Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + '.tmp')
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for info, data in entries:
            z.writestr(info, data)
    tmp.replace(out)
    return out


def _parse(data: bytes):
    return etree.fromstring(data, etree.XMLParser(remove_blank_text=False, resolve_entities=False))


def _dump(root) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)


# --- limpar ------------------------------------------------------------------
def _unwrap(el) -> None:
    parent = el.getparent()
    idx = parent.index(el)
    for child in reversed(list(el)):
        parent.insert(idx, child)
    parent.remove(el)


def _clean_story(root) -> None:
    for tag in _UNWRAP:
        for el in list(root.iter(_w(tag))):
            if el.getparent().tag == _w('rPr'):   # marca de parágrafo inserido
                el.getparent().remove(el)
            else:
                _unwrap(el)
    for tag in _DROP:
        for el in list(root.iter(_w(tag))):
            el.getparent().remove(el)
    for ref in list(root.iter(_w('commentReference'))):
        run = ref.getparent()
        if run.tag == _w('r'):
            run.getparent().remove(run)
        else:
            run.remove(ref)
    for el in root.iter():
        for attr in [a for a in el.attrib if a.startswith(f'{{{W}}}rsid')]:
            del el.attrib[attr]


# ordem dos primeiros filhos de w:settings no esquema (CT_Settings)
_SETTINGS_HEAD = ('writeProtection', 'view', 'zoom', 'removePersonalInformation',
                  'removeDateAndTime')


def _clean_settings(root) -> None:
    for el in list(root.iter(_w('rsids'))):
        el.getparent().remove(el)
    for tag in ('removePersonalInformation', 'removeDateAndTime'):
        if root.find(_w(tag)) is not None:
            continue
        before = _SETTINGS_HEAD[:_SETTINGS_HEAD.index(tag)]
        pos = 0
        for i, child in enumerate(root):
            if etree.QName(child).localname in before:
                pos = i + 1
        root.insert(pos, etree.Element(_w(tag)))


def _clean_core(root) -> None:
    for child in list(root):
        name = etree.QName(child).localname
        if name in ('creator', 'lastModifiedBy', 'lastPrinted', 'created', 'modified'):
            root.remove(child)
        elif name == 'revision':
            child.text = '1'


def _clean_app(root) -> None:
    for child in list(root):
        if etree.QName(child).localname in ('Company', 'Manager', 'HyperlinkBase', 'TotalTime'):
            root.remove(child)


def _drop_rels(root, removed: set[str], base: str) -> None:
    for rel in list(root):
        target = rel.get('Target', '')
        full = target.lstrip('/') if target.startswith('/') else f'{base}{target}'
        if full in removed:
            root.remove(rel)


def _drop_overrides(root, removed: set[str]) -> None:
    for ov in list(root):
        if ov.get('PartName', '').lstrip('/') in removed:
            root.remove(ov)


def clean_one(src: Path, out: Path) -> Path:
    entries = _read(src)
    removed = {i.filename for i, _ in entries
               if _COMMENT_PARTS.match(i.filename) or i.filename == 'docProps/custom.xml'}
    result = []
    for info, data in entries:
        name = info.filename
        if name in removed:
            continue
        if _STORY.match(name):
            root = _parse(data)
            _clean_story(root)
            data = _dump(root)
        elif name == 'word/settings.xml':
            root = _parse(data)
            _clean_settings(root)
            data = _dump(root)
        elif name == 'docProps/core.xml':
            root = _parse(data)
            _clean_core(root)
            data = _dump(root)
        elif name == 'docProps/app.xml':
            root = _parse(data)
            _clean_app(root)
            data = _dump(root)
        elif name == 'word/_rels/document.xml.rels':
            root = _parse(data)
            _drop_rels(root, removed, 'word/')
            data = _dump(root)
        elif name == '_rels/.rels':
            root = _parse(data)
            _drop_rels(root, removed, '')
            data = _dump(root)
        elif name == '[Content_Types].xml':
            root = _parse(data)
            _drop_overrides(root, removed)
            data = _dump(root)
        result.append((info, data))
    return _write(result, out)


def clean(files, out: Path) -> list[Path]:
    """Tira autor, comentários e revisões (aceitas) de cada DOCX; grava <nome>_limpo.docx."""
    out = Path(out)
    for f in files:          # valida tudo antes de gravar qualquer coisa
        _check(f)
    return [clean_one(f, unique(out / f'{Path(f).stem}_limpo.docx')) for f in files]


# --- localizar e substituir --------------------------------------------------
def _paragraph_texts(p) -> list:
    """Nós w:t do parágrafo, em ordem, sem os de parágrafos aninhados (caixas de texto)."""
    nodes = []
    for t in p.iter(_w('t')):
        owner = next(t.iterancestors(_w('p')), None)
        if owner is p:
            nodes.append(t)
    return nodes


def _pattern(find: str, match_case: bool) -> re.Pattern:
    if not find:
        raise DocxError('Informe o texto a localizar.')
    return re.compile(re.escape(find), 0 if match_case else re.IGNORECASE)


def _replace_in_paragraph(p, pattern: re.Pattern, replacement: str) -> int:
    nodes = _paragraph_texts(p)
    if not nodes:
        return 0
    texts = [t.text or '' for t in nodes]
    full = ''.join(texts)
    matches = list(pattern.finditer(full))
    for m in reversed(matches):
        start, end = m.start(), m.end()
        pos = 0
        first = True
        for i, t in enumerate(texts):
            a, b = pos, pos + len(t)
            pos = b
            if b <= start or a >= end:
                continue
            lo, hi = max(start, a) - a, min(end, b) - a
            if first:
                texts[i] = t[:lo] + replacement + t[hi:]
                first = False
            else:
                texts[i] = t[:lo] + t[hi:]
    for node, text in zip(nodes, texts):
        if node.text != text:
            node.text = text
            node.set(_XML_SPACE, 'preserve')
    return len(matches)


def _replace_story(root, pattern, replacement) -> int:
    return sum(_replace_in_paragraph(p, pattern, replacement) for p in list(root.iter(_w('p'))))


def _truthy(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ('sim', 'true', '1', 'yes')
    return bool(value)


def count_matches(path: Path, find: str, match_case: bool = True) -> int:
    pattern = _pattern(find, match_case)
    total = 0
    for info, data in _read(path):
        if _STORY.match(info.filename):
            root = _parse(data)
            for p in root.iter(_w('p')):
                total += len(pattern.findall(''.join(t.text or '' for t in _paragraph_texts(p))))
    return total


def replace(files, out: Path, find: str = '', replace: str = '', match_case='Sim') -> list[Path]:
    """Troca `find` por `replace` em corpo, tabelas, cabeçalhos, rodapés e notas."""
    pattern = _pattern(find, _truthy(match_case))
    out = Path(out)
    for f in files:
        _check(f)
    results = []
    for f in files:
        entries = []
        for info, data in _read(f):
            if _STORY.match(info.filename):
                root = _parse(data)
                if _replace_story(root, pattern, replace):
                    data = _dump(root)
            entries.append((info, data))
        results.append(_write(entries, unique(out / f'{Path(f).stem}_substituido.docx')))
    return results


# --- juntar ------------------------------------------------------------------
def merge(files, out: Path) -> list[Path]:
    """Junta os DOCX na ordem dada; estilos, numeração e imagens via docxcompose."""
    import docx
    from docxcompose.composer import Composer

    if len(files) < 2:
        raise DocxError('Escolha pelo menos dois DOCX para juntar.')
    for f in files:
        _check(f)
    composer = Composer(docx.Document(str(files[0])))
    for f in files[1:]:
        composer.append(docx.Document(str(f)))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    composer.save(str(out))
    return [out]


# --- exportar texto ----------------------------------------------------------
def _html(src: Path, img_dir: Path) -> str:
    import mammoth

    count = {'n': 0}

    def save_image(image):
        count['n'] += 1
        ext = (image.content_type or 'image/png').split('/')[-1].replace('jpeg', 'jpg')
        img_dir.mkdir(parents=True, exist_ok=True)
        target = img_dir / f'imagem{count["n"]:03}.{ext}'
        with image.open() as fh:
            target.write_bytes(fh.read())
        return {'src': f'{img_dir.name}/{target.name}'}

    with open(src, 'rb') as fh:
        result = mammoth.convert_to_html(fh, convert_image=mammoth.images.img_element(save_image))
    return result.value


def export_text(files, out: Path, fmt: str = 'TXT') -> list[Path]:
    """DOCX para TXT, Markdown ou HTML. Imagens (MD/HTML) vão para <nome>_imagens/."""
    import html as html_lib

    import mammoth

    if fmt not in EXPORT_FORMATS:
        raise DocxError(f'Formato desconhecido: {fmt}')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for f in files:
        _check(f)
    results = []
    for f in files:
        src = Path(f)
        target = unique(out / f'{src.stem}{EXPORT_FORMATS[fmt]}')
        if fmt == 'TXT':
            with open(src, 'rb') as fh:
                text = mammoth.extract_raw_text(fh).value
            target.write_text(text.strip() + '\n', encoding='utf-8')
        else:
            body = _html(src, out / f'{src.stem}_imagens')
            if fmt == 'HTML':
                title = html_lib.escape(src.stem)
                target.write_text(
                    f'<!DOCTYPE html>\n<html lang="pt-BR"><head><meta charset="utf-8">'
                    f'<title>{title}</title></head>\n<body>\n{body}\n</body></html>\n',
                    encoding='utf-8')
            else:
                from markdownify import markdownify
                target.write_text(markdownify(body, heading_style='ATX').strip() + '\n',
                                  encoding='utf-8')
        results.append(target)
    return results
