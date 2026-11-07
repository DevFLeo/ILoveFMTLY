"""Texto, codificar/decodificar, URL e IA (estimativas locais)."""

import base64
import binascii
import difflib
import html
import html.entities
import json
import random
import re
import unicodedata
import urllib.parse
from datetime import datetime, timezone

import markdown as md

# === Texto =====================================================================
def word_count(text):
    words = re.findall(r'\b\w+\b', text)
    sentences = [s for s in re.split(r'[.!?]+(?:\s|$)', text) if s.strip()]
    paragraphs = [p for p in re.split(r'\n\s*\n', text) if p.strip()]
    minutes = len(words) / 200
    return '\n'.join([
        f'Palavras: {len(words)}', f'Caracteres: {len(text)}',
        f'Caracteres sem espaço: {len(re.sub(r"\s", "", text))}', f'Frases: {len(sentences)}',
        f'Parágrafos: {len(paragraphs)}', f'Linhas: {len(text.splitlines())}',
        f'Tempo de leitura: ~{max(1, round(minutes))} min' if words else 'Tempo de leitura: 0 min'])


_LOREM = ('lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut '
          'labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco '
          'laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in '
          'voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat '
          'non proident sunt in culpa qui officia deserunt mollit anim id est laborum').split()
LOREM_UNITS = ('Parágrafos', 'Frases', 'Palavras')


def lorem(amount=3, unit='Parágrafos'):
    rng = random.Random(amount)

    def sentence():
        words = [rng.choice(_LOREM) for _ in range(rng.randint(8, 16))]
        return ' '.join(words).capitalize() + '.'
    if unit == 'Palavras':
        return ' '.join((_LOREM * (amount // len(_LOREM) + 1))[:amount]).capitalize()
    if unit == 'Frases':
        return ' '.join(sentence() for _ in range(amount))
    paras = [' '.join(sentence() for _ in range(rng.randint(4, 7))) for _ in range(amount)]
    paras[0] = 'Lorem ipsum dolor sit amet, ' + paras[0][0].lower() + paras[0][1:]
    return '\n\n'.join(paras)


def markdown_to_html(text):
    return md.markdown(text, extensions=['tables', 'fenced_code'])


CASES = ('MAIÚSCULAS', 'minúsculas', 'Título', 'Frase', 'camelCase', 'PascalCase', 'snake_case',
         'kebab-case', 'CONSTANTE')


def case_convert(text, case='MAIÚSCULAS'):
    words = re.findall(r'[A-Za-zÀ-ÿ0-9]+', re.sub(r'(?<=[a-zà-ÿ0-9])(?=[A-Z])', ' ', text))
    if case == 'MAIÚSCULAS':
        return text.upper()
    if case == 'minúsculas':
        return text.lower()
    if case == 'Título':
        return text.title()
    if case == 'Frase':
        return re.sub(r'(^\s*|[.!?]\s+)(\w)', lambda m: m.group(1) + m.group(2).upper(), text.lower())
    lower = [w.lower() for w in words]
    if case == 'camelCase':
        return lower[0] + ''.join(w.capitalize() for w in lower[1:]) if lower else ''
    if case == 'PascalCase':
        return ''.join(w.capitalize() for w in lower)
    if case == 'snake_case':
        return '_'.join(lower)
    if case == 'kebab-case':
        return '-'.join(lower)
    return '_'.join(w.upper() for w in words)


REVERSE_MODES = ('Caracteres', 'Palavras', 'Linhas')


def reverse(text, mode='Caracteres'):
    if mode == 'Palavras':
        return ' '.join(reversed(text.split()))
    if mode == 'Linhas':
        return '\n'.join(reversed(text.splitlines()))
    return text[::-1]


def dedupe_lines(text, ignore_case='Não'):
    seen, out = set(), []
    for line in text.splitlines():
        key = line.lower() if ignore_case == 'Sim' else line
        if key not in seen:
            seen.add(key)
            out.append(line)
    return '\n'.join(out)


SORTS = ('A → Z', 'Z → A', 'Mais curta primeiro', 'Mais longa primeiro', 'Números', 'Embaralhar')


def sort_lines(text, order='A → Z'):
    lines = text.splitlines()
    if order == 'Z → A':
        return '\n'.join(sorted(lines, key=str.lower, reverse=True))
    if order == 'Mais curta primeiro':
        return '\n'.join(sorted(lines, key=len))
    if order == 'Mais longa primeiro':
        return '\n'.join(sorted(lines, key=len, reverse=True))
    if order == 'Números':
        def num(s):
            m = re.search(r'-?\d+(?:[.,]\d+)?', s)
            return float(m.group().replace(',', '.')) if m else float('inf')
        return '\n'.join(sorted(lines, key=num))
    if order == 'Embaralhar':
        random.shuffle(lines)
        return '\n'.join(lines)
    return '\n'.join(sorted(lines, key=str.lower))


def text_diff(a, b):
    lines = list(difflib.unified_diff(a.splitlines(), b.splitlines(), 'A', 'B', lineterm='', n=2))
    return '\n'.join(lines) if lines else 'Os dois textos são iguais.'


def regex_test(text, pattern='\\w+', flags='i', replace=''):
    f = 0
    for ch, flag in (('i', re.I), ('m', re.M), ('s', re.S), ('x', re.X)):
        if ch in (flags or ''):
            f |= flag
    try:
        rx = re.compile(pattern, f)
    except re.error as e:
        raise ValueError(f'Regex inválida: {e}') from None
    matches = list(rx.finditer(text))
    lines = [f'{len(matches)} ocorrência(s)']
    for i, m in enumerate(matches[:500], 1):
        groups = ' · '.join(f'grupo {n}: {g!r}' for n, g in enumerate(m.groups(), 1))
        lines.append(f'{i}. [{m.start()}-{m.end()}] {m.group()!r}' + (f'  ({groups})' if groups else ''))
    if replace:
        lines += ['', '--- com substituição ---', rx.sub(replace, text)]
    return '\n'.join(lines)


def _syllables(word: str) -> int:
    groups = re.findall(r'[aeiouáéíóúâêôãõàüy]+', word.lower())
    return max(1, len(groups))


def readability(text):
    """Índice Flesch adaptado ao português (Martins et al., 1996)."""
    words = re.findall(r'[A-Za-zÀ-ÿ]+', text)
    sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
    if not words or not sentences:
        raise ValueError('Cole um texto com pelo menos uma frase.')
    syl = sum(_syllables(w) for w in words)
    asl, asw = len(words) / len(sentences), syl / len(words)
    score = 248.835 - 1.015 * asl - 84.6 * asw
    level = ('Muito fácil' if score >= 75 else 'Fácil' if score >= 50 else 'Difícil' if score >= 25
             else 'Muito difícil')
    return '\n'.join([f'Índice Flesch (pt-BR): {score:.1f} · {level}',
                      f'Palavras por frase: {asl:.1f}', f'Sílabas por palavra: {asw:.2f}',
                      f'Palavras longas (3+ sílabas): {sum(_syllables(w) >= 3 for w in words)}'])


ESCAPES = ('JSON / JavaScript', 'HTML', 'URL', 'SQL', 'Regex', 'CSV')
DIRECTIONS = ('Codificar', 'Decodificar')


def escape_text(text, kind='JSON / JavaScript', direction='Codificar'):
    enc = direction == 'Codificar'
    if kind == 'JSON / JavaScript':
        if enc:
            return json.dumps(text, ensure_ascii=False)[1:-1]
        try:
            return json.loads(f'"{text}"')
        except json.JSONDecodeError as e:
            raise ValueError(f'Sequência de escape inválida: {e.msg}') from None
    if kind == 'HTML':
        return html.escape(text) if enc else html.unescape(text)
    if kind == 'URL':
        return urllib.parse.quote(text) if enc else urllib.parse.unquote(text)
    if kind == 'SQL':
        return text.replace("'", "''") if enc else text.replace("''", "'")
    if kind == 'Regex':
        return re.escape(text) if enc else re.sub(r'\\(.)', r'\1', text)
    if enc:
        return '"' + text.replace('"', '""') + '"'
    return text[1:-1].replace('""', '"') if text.startswith('"') and text.endswith('"') else text


_MORSE = {'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
          'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
          'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
          'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
          '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--',
          '?': '..--..', '!': '-.-.--', '/': '-..-.', '@': '.--.-.', '-': '-....-', '(': '-.--.', ')': '-.--.-'}
_FROM_MORSE = {v: k for k, v in _MORSE.items()}


def morse(text, direction='Codificar'):
    if direction == 'Codificar':
        plain = unicodedata.normalize('NFD', text.upper())
        plain = ''.join(c for c in plain if unicodedata.category(c) != 'Mn')
        return ' / '.join(' '.join(_MORSE[c] for c in w if c in _MORSE) for w in plain.split())
    words = re.split(r'\s*/\s*|\s{3,}', text.strip())
    return ' '.join(''.join(_FROM_MORSE.get(code, '?') for code in w.split()) for w in words)


def whitespace_clean(text, tabs='Sim'):
    lines = [re.sub(r'[  ]+', ' ', (ln.replace('\t', '    ') if tabs == 'Sim' else ln)).strip()
             for ln in text.splitlines()]
    out = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines))
    return out.strip() + '\n'


# === Codificar / decodificar ======================================================
B64_VARIANTS = ('Padrão', 'URL-safe')


def base64_tool(text, direction='Codificar', variant='Padrão'):
    if direction == 'Codificar':
        data = text.encode('utf-8')
        return (base64.urlsafe_b64encode(data) if variant == 'URL-safe' else base64.b64encode(data)).decode()
    raw = re.sub(r'\s+', '', text)
    raw += '=' * (-len(raw) % 4)
    try:
        data = base64.urlsafe_b64decode(raw) if ('-' in raw or '_' in raw) else base64.b64decode(raw)
    except (binascii.Error, ValueError):
        raise ValueError('Não é Base64 válido.') from None
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return f'(binário, {len(data)} bytes) {data.hex(" ")}'


URL_MODES = ('Componente', 'URL inteira')


def url_tool(text, direction='Codificar', mode='Componente'):
    if direction == 'Decodificar':
        return urllib.parse.unquote_plus(text) if mode == 'Componente' else urllib.parse.unquote(text)
    safe = '' if mode == 'Componente' else ":/?#[]@!$&'()*+,;=%"
    return urllib.parse.quote(text, safe=safe)


ENTITY_MODES = ('Nomeadas', 'Decimais', 'Hexadecimais')


def html_entities(text, direction='Codificar', mode='Nomeadas'):
    if direction == 'Decodificar':
        return html.unescape(text)
    out = []
    for ch in text:
        code = ord(ch)
        if ch in '<>&"\'' or code > 126:
            if mode == 'Nomeadas':
                name = html.entities.codepoint2name.get(code)
                out.append(f'&{name};' if name else f'&#{code};')
            elif mode == 'Decimais':
                out.append(f'&#{code};')
            else:
                out.append(f'&#x{code:X};')
        else:
            out.append(ch)
    return ''.join(out)


def unicode_inspect(text):
    rows = ['CARACTERE  CÓDIGO     UTF-8          CATEGORIA  LARGURA  NOME']
    for ch in text[:2000]:
        if ch == '\n':
            continue
        rows.append(f'{ch!s:<10} U+{ord(ch):04X}{"":<3} {ch.encode("utf-8").hex(" ").upper():<14} '
                    f'{unicodedata.category(ch):<10} {unicodedata.east_asian_width(ch):<8} '
                    f'{unicodedata.name(ch, "(sem nome)")}')
    return '\n'.join(rows)


def hex_tool(text, direction='Codificar'):
    if direction == 'Codificar':
        return text.encode('utf-8').hex(' ').upper()
    raw = re.sub(r'[^0-9A-Fa-f]', '', re.sub(r'0x', '', text))
    try:
        return bytes.fromhex(raw).decode('utf-8', errors='replace')
    except ValueError:
        raise ValueError('Hex inválido (número ímpar de dígitos?).') from None


def caesar(text, shift=13, direction='Codificar'):
    k = int(shift) % 26 * (1 if direction == 'Codificar' else -1)

    def rot(c):
        for base in ('a', 'A'):
            start = ord(base)
            if start <= ord(c) < start + 26:
                return chr((ord(c) - start + k) % 26 + start)
        return c
    return ''.join(rot(c) for c in text)


def punycode(text, direction='Codificar'):
    out = []
    for item in text.split():
        local, at, domain = item.rpartition('@') if '@' in item else ('', '', item)
        try:
            if direction == 'Codificar':
                conv = domain.encode('idna').decode('ascii')
            else:
                conv = domain.encode('ascii').decode('idna')
        except (UnicodeError, ValueError) as e:
            raise ValueError(f'Domínio inválido "{domain}": {e}') from None
        out.append(f'{local}{at}{conv}')
    return '\n'.join(out)


def jwt_decode(text):
    parts = text.strip().split('.')
    if len(parts) < 2:
        raise ValueError('Um JWT tem 3 partes separadas por ponto.')

    def part(p):
        try:
            return json.loads(base64.urlsafe_b64decode(p + '=' * (-len(p) % 4)))
        except (ValueError, binascii.Error):
            raise ValueError('Parte do JWT não é JSON em Base64URL.') from None
    header, payload = part(parts[0]), part(parts[1])
    lines = ['CABEÇALHO', json.dumps(header, ensure_ascii=False, indent=2), '', 'DADOS (payload)',
             json.dumps(payload, ensure_ascii=False, indent=2), '']
    now = datetime.now(timezone.utc).timestamp()
    for claim, label in (('iat', 'Emitido em'), ('nbf', 'Válido a partir de'), ('exp', 'Expira em')):
        if isinstance(payload.get(claim), (int, float)):
            when = datetime.fromtimestamp(payload[claim], timezone.utc).strftime('%d/%m/%Y %H:%M:%S UTC')
            lines.append(f'{label}: {when}')
    if isinstance(payload.get('exp'), (int, float)):
        lines.append('Situação: EXPIRADO' if payload['exp'] < now else 'Situação: dentro da validade')
    lines.append(f'Algoritmo: {header.get("alg", "?")} · assinatura não verificada (precisa da chave)')
    return '\n'.join(lines)


# === Web ===========================================================================
def url_parse(text):
    u = urllib.parse.urlsplit(text.strip())
    if not u.scheme and not u.netloc:
        raise ValueError('Cole uma URL completa, ex.: https://exemplo.com/caminho?a=1')
    lines = [f'Protocolo: {u.scheme}', f'Usuário: {u.username or "-"}', f'Host: {u.hostname or "-"}',
             f'Porta: {u.port or "(padrão)"}', f'Caminho: {u.path or "/"}', f'Fragmento: {u.fragment or "-"}']
    params = urllib.parse.parse_qsl(u.query, keep_blank_values=True)
    lines.append(f'Parâmetros ({len(params)}):')
    lines += [f'  {k} = {v}' for k, v in params]
    return '\n'.join(lines)


# === IA (estimativas locais, sem rede) ================================================
# Preço por 1 milhão de tokens de entrada (USD). Valores de referência; confira no site do fornecedor.
MODELS = {
    'Claude (família Opus)': 15.0, 'Claude (família Sonnet)': 3.0, 'Claude (família Haiku)': 0.8,
    'GPT (modelo grande)': 2.5, 'GPT (modelo mini)': 0.15, 'Gemini (Pro)': 1.25, 'Llama (aberto)': 0.0,
}


def estimate_tokens(text: str) -> int:
    """Estimativa: média entre ~4 caracteres por token e ~0,75 palavra por token."""
    by_chars = len(text) / 4
    by_words = len(re.findall(r'\S+', text)) / 0.75
    return round((by_chars + by_words) / 2)


def token_count(text):
    n = estimate_tokens(text)
    lines = [f'≈ {n} tokens (estimativa offline; cada modelo conta um pouco diferente)',
             f'Caracteres: {len(text)} · Palavras: {len(re.findall(r"\S+", text))}', '',
             'Custo estimado de entrada:']
    lines += [f'  {name}: US$ {n * price / 1_000_000:.6f}' for name, price in MODELS.items()]
    return '\n'.join(lines)


_FILLER = [r'\bpor favor,?\s*', r'\b(eu )?gostaria (muito )?que (você )?', r'\bseria (muito )?bom se\s*',
           r'\bbasicamente,?\s*', r'\bna verdade,?\s*', r'\bé importante (notar|lembrar) que\s*',
           r'\bplease,?\s*', r'\bi would like you to\s*', r'\bbasically,?\s*', r'\bactually,?\s*',
           r'\bkind of\s*', r'\bjust\s+']


def prompt_optimize(text):
    out = text
    for rx in _FILLER:
        out = re.sub(rx, '', out, flags=re.I)
    out = whitespace_clean(out)
    out = '\n'.join(dict.fromkeys(out.splitlines())) if out.count('\n') > 3 else out
    before, after = estimate_tokens(text), estimate_tokens(out)
    return f'{out.strip()}\n\n--- ≈ {before} → {after} tokens ({before - after} a menos)'


def system_prompt(role='Assistente', goal='', tone='Direto e cordial', rules='', output_format='', examples=''):
    parts = [f'Você é {role}.']
    if goal:
        parts.append(f'\n## Objetivo\n{goal}')
    parts.append(f'\n## Tom\n{tone}')
    if rules:
        parts.append('\n## Regras\n' + '\n'.join(f'- {r.strip()}' for r in rules.split(';') if r.strip()))
    if output_format:
        parts.append(f'\n## Formato da resposta\n{output_format}')
    if examples:
        parts.append(f'\n## Exemplos\n{examples}')
    return '\n'.join(parts) + '\n'
