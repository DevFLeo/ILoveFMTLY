"""Tarja, assinatura e formulários em PDF (PyMuPDF, tudo local).

- redact: apaga de verdade (texto e imagem sob a tarja somem do arquivo);
- sign_pdf: carimba uma assinatura (PNG desenhado ou imagem) numa página;
- read_fields / fill_form: lê e preenche campos de formulário (AcroForm).
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

# --- tarja ------------------------------------------------------------------
PATTERNS = {
    'docs': (r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',               # CPF
             r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b'),       # CNPJ
    'contacts': (r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+',              # e-mail
                 r'\(?\b\d{2}\)?[\s-]?9?\d{4}-?\d{4}\b'),        # telefone
}


def _split_terms(terms: str) -> list[str]:
    return [t.strip() for t in re.split(r'[;\n]', terms or '') if t.strip()]


def redact(files, out: Path, terms: str = '', docs: str = 'Não', contacts: str = 'Não') -> list[Path]:
    """Tarja preta sobre os termos (separados por ";") e, se pedido, sobre CPF/CNPJ
    e e-mails/telefones. O conteúdo coberto é removido, não só escondido."""
    words = _split_terms(terms)
    regexes = [re.compile(p) for key, on in (('docs', docs), ('contacts', contacts))
               if on == 'Sim' for p in PATTERNS[key]]
    if not words and not regexes:
        raise ValueError('Diga o que tarjar: digite um termo ou marque CPF/CNPJ ou e-mails/telefones.')
    total = 0
    with pymupdf.open(files[0]) as doc:
        for page in doc:
            found = set(words)
            if regexes:
                text = page.get_text()
                found.update(m.group(0) for rx in regexes for m in rx.finditer(text))
            for needle in found:
                for rect in page.search_for(needle):
                    page.add_redact_annot(rect, fill=(0, 0, 0))
                    total += 1
            page.apply_redactions()
        if not total:
            raise ValueError('Nada encontrado para tarjar neste PDF.')
        doc.save(out, garbage=4, deflate=True)
    return [Path(out)]


# --- assinatura -------------------------------------------------------------
SIGN_POSITIONS = ('Inferior direito', 'Inferior esquerdo', 'Inferior centro',
                  'Superior direito', 'Superior esquerdo')
MARGIN = 36  # pt


def signature_rect(page_rect: pymupdf.Rect, img_w: int, img_h: int, position: str,
                   width_pct: int) -> pymupdf.Rect:
    if position not in SIGN_POSITIONS:
        raise ValueError(f'Posição desconhecida: {position}')
    w = page_rect.width * max(5, min(width_pct, 90)) / 100
    h = w * img_h / max(img_w, 1)
    vert, horiz = position.split(' ')
    x0 = {'esquerdo': MARGIN, 'direito': page_rect.width - MARGIN - w,
          'centro': (page_rect.width - w) / 2}[horiz]
    y0 = MARGIN if vert == 'Superior' else page_rect.height - MARGIN - h
    return pymupdf.Rect(x0, y0, x0 + w, y0 + h)


def sign_pdf(src: Path, target: Path, signature: bytes, page: int = 0,
             position: str = 'Inferior direito', width: int = 30) -> Path:
    """page: 1 = primeira, 0 = última. width: % da largura da página."""
    if not signature:
        raise ValueError('Desenhe a assinatura ou escolha uma imagem.')
    pix = pymupdf.Pixmap(signature)
    with pymupdf.open(src) as doc:
        index = len(doc) - 1 if page == 0 else page - 1
        if not 0 <= index < len(doc):
            raise ValueError(f'O PDF tem {len(doc)} página(s); a página {page} não existe.')
        p = doc[index]
        rect = signature_rect(p.rect, pix.width, pix.height, position, width)
        p.insert_image(rect * p.derotation_matrix, stream=signature, keep_proportion=True,
                       rotate=-p.rotation % 360)
        doc.save(target, garbage=3, deflate=True)
    return Path(target)


# --- formulários ------------------------------------------------------------
TEXT, CHECK, CHOICE, RADIO = 'text', 'check', 'choice', 'radio'


@dataclass
class FormField:
    name: str
    kind: str                      # text | check | choice | radio
    value: str | bool = ''
    options: list[str] = field(default_factory=list)


def _kind(widget) -> str | None:
    return {pymupdf.PDF_WIDGET_TYPE_TEXT: TEXT,
            pymupdf.PDF_WIDGET_TYPE_CHECKBOX: CHECK,
            pymupdf.PDF_WIDGET_TYPE_COMBOBOX: CHOICE,
            pymupdf.PDF_WIDGET_TYPE_LISTBOX: CHOICE,
            pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON: RADIO}.get(widget.field_type)


def _is_on(widget) -> bool:
    return widget.field_value not in (False, None, '', 'Off')


def read_fields(src: Path) -> list[FormField]:
    """Campos preenchíveis, na ordem em que aparecem. Rádios do mesmo nome viram um campo."""
    fields_: dict[str, FormField] = {}
    with pymupdf.open(src) as doc:
        for page in doc:
            for w in page.widgets():
                kind = _kind(w)
                if kind is None or not w.field_name:
                    continue
                f = fields_.get(w.field_name)
                if kind == RADIO:
                    f = f or fields_.setdefault(w.field_name, FormField(w.field_name, RADIO, ''))
                    state = str(w.on_state())
                    if state not in f.options:
                        f.options.append(state)
                    if _is_on(w):
                        f.value = state
                elif f is None:
                    value = _is_on(w) if kind == CHECK else str(w.field_value or '')
                    fields_[w.field_name] = FormField(w.field_name, kind, value,
                                                      list(w.choice_values or []))
    if not fields_:
        raise ValueError('Este PDF não tem campos de formulário para preencher.')
    return list(fields_.values())


def fill_form(src: Path, target: Path, values: dict, flatten: bool = False) -> Path:
    """Preenche os campos pelo nome. flatten=True deixa o resultado não editável."""
    with pymupdf.open(src) as doc:
        for page in doc:
            for w in page.widgets():
                if w.field_name not in values:
                    continue
                value, kind = values[w.field_name], _kind(w)
                if kind == CHECK:
                    w.field_value = w.on_state() if value else 'Off'
                elif kind == RADIO:
                    w.field_value = w.on_state() if str(w.on_state()) == value else 'Off'
                elif kind in (TEXT, CHOICE):
                    w.field_value = str(value)
                else:
                    continue
                w.update()
        if flatten:
            doc.bake()
        doc.save(target, garbage=3, deflate=True)
    return Path(target)
