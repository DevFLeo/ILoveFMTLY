"""JSON, XML, YAML, CSV e TOML: formatar, validar, converter, consultar, comparar."""

import csv
import difflib
import io
import json
import re
import tomllib
from html import escape

import jmespath
import jsonschema
import tomli_w
import xmltodict
import yaml
from jsonpath_ng.ext import parse as jsonpath_parse
from lxml import etree

INDENTS = ('2 espaços', '4 espaços', 'Tab')


def _indent(choice: str):
    return '\t' if choice == 'Tab' else int(choice.split()[0])


# --- leitura com erro amigável --------------------------------------------------
def load_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f'JSON inválido na linha {e.lineno}, coluna {e.colno}: {e.msg}') from None


def load_yaml(text: str):
    """Um documento vira o próprio valor; vários (---) viram uma lista."""
    try:
        docs = list(yaml.safe_load_all(text))
    except yaml.YAMLError as e:
        raise ValueError(f'YAML inválido: {e}') from None
    return docs[0] if len(docs) == 1 else docs


def load_toml(text: str):
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f'TOML inválido: {e}') from None


def load_xml(text: str):
    try:
        return xmltodict.parse(text)
    except Exception as e:  # xmltodict usa ExpatError
        raise ValueError(f'XML inválido: {e}') from None


def _xml_tree(text: str):
    try:
        return etree.fromstring(text.encode('utf-8'), etree.XMLParser(remove_blank_text=True))
    except etree.XMLSyntaxError as e:
        raise ValueError(f'XML inválido: {e}') from None


def load_csv(text: str, delimiter: str = 'Automático') -> list[dict]:
    text = text.strip('\ufeff')
    if not text.strip():
        raise ValueError('CSV vazio.')
    delim = _delim(text, delimiter)
    rows = list(csv.DictReader(io.StringIO(text), delimiter=delim))
    if not rows:
        raise ValueError('O CSV só tem cabeçalho.')
    return rows


DELIMS = ('Automático', 'Vírgula', 'Ponto e vírgula', 'Tab', 'Barra vertical')
_DELIM_CHAR = {'Vírgula': ',', 'Ponto e vírgula': ';', 'Tab': '\t', 'Barra vertical': '|'}


def _delim(text: str, choice: str) -> str:
    if choice in _DELIM_CHAR:
        return _DELIM_CHAR[choice]
    try:
        return csv.Sniffer().sniff(text[:4096], delimiters=',;\t|').delimiter
    except csv.Error:
        return ','


# --- escrita ---------------------------------------------------------------------
def dump_json(data, indent='2 espaços') -> str:
    return json.dumps(data, ensure_ascii=False, indent=_indent(indent), default=str)


class _NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def dump_yaml(data, flow: bool = False) -> str:
    return yaml.dump(data, Dumper=_NoAliasDumper, allow_unicode=True, sort_keys=False,
                     default_flow_style=flow, width=10_000 if flow else 80)


def dump_toml(data) -> str:
    if not isinstance(data, dict):
        data = {'dados': data}
    try:
        return tomli_w.dumps(_toml_safe(data))
    except TypeError as e:
        raise ValueError(f'Não dá para representar em TOML: {e}') from None


def _toml_safe(v):
    if isinstance(v, dict):
        return {str(k): _toml_safe(x) for k, x in v.items() if x is not None}
    if isinstance(v, list):
        return [_toml_safe(x) for x in v if x is not None]
    return v


def dump_xml(data, root: str = 'root') -> str:
    if not (isinstance(data, dict) and len(data) == 1 and not isinstance(next(iter(data.values())), list)):
        data = {root: {'item': data} if isinstance(data, list) else data}
    return xmltodict.unparse(_xml_safe(data), pretty=True, indent='  ')


def _xml_key(k) -> str:
    k = re.sub(r'[^\w.-]', '_', str(k))
    return k if re.match(r'[A-Za-z_]', k) else f'_{k}'


def _xml_safe(v):
    if isinstance(v, dict):
        return {(k if str(k).startswith(('@', '#')) else _xml_key(k)): _xml_safe(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_xml_safe(x) for x in v]
    if isinstance(v, bool):
        return 'true' if v else 'false'
    return '' if v is None else v


def _flat_row(obj, prefix='') -> dict:
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flat_row(v, f'{prefix}{k}.'))
    elif isinstance(obj, list):
        out[prefix[:-1]] = json.dumps(obj, ensure_ascii=False)
    else:
        out[prefix[:-1] or 'valor'] = obj
    return out


def _records(data) -> list:
    """Acha a lista de registros (para virar CSV/tabela)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                inner = _records(v)
                if len(inner) > 1 or (inner and isinstance(v, dict) and len(v) == 1):
                    return inner
        return [data]
    return [{'valor': data}]


def dump_csv(data, delimiter: str = 'Vírgula') -> str:
    rows = [_flat_row(r) if isinstance(r, dict) else {'valor': r} for r in _records(data)]
    cols = list(dict.fromkeys(k for r in rows for k in r))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, delimiter=_DELIM_CHAR.get(delimiter, ','), lineterminator='\n')
    w.writeheader()
    w.writerows({k: ('' if r.get(k) is None else r.get(k)) for k in cols} for r in rows)
    return buf.getvalue()


def html_table(data) -> str:
    rows = [_flat_row(r) if isinstance(r, dict) else {'valor': r} for r in _records(data)]
    cols = list(dict.fromkeys(k for r in rows for k in r))
    head = ''.join(f'<th>{escape(str(c))}</th>' for c in cols)
    body = '\n'.join('  <tr>' + ''.join(f'<td>{escape(str(r.get(c, "")))}</td>' for c in cols) + '</tr>'
                     for r in rows)
    return (f'<table>\n  <thead><tr>{head}</tr></thead>\n  <tbody>\n{body}\n  </tbody>\n</table>\n')


def _diff(a: str, b: str, what: str) -> str:
    lines = list(difflib.unified_diff(a.splitlines(), b.splitlines(), 'A', 'B', lineterm='', n=2))
    if not lines:
        return f'Os dois {what} são iguais.'
    return '\n'.join(lines)


def _query_jmespath(data, expression: str):
    try:
        return jmespath.search(expression, data)
    except jmespath.exceptions.JMESPathError as e:
        raise ValueError(f'Expressão JMESPath inválida: {e}') from None


# --- inferência de tipos (schema, TS, Go, Rust, Zod) -------------------------------
def _pascal(name: str) -> str:
    parts = re.split(r'[^0-9A-Za-z]+', str(name))
    out = ''.join(p[:1].upper() + p[1:] for p in parts if p)
    return out if out and not out[0].isdigit() else f'T{out}'


def _snake(name: str) -> str:
    s = re.sub(r'(?<!^)(?=[A-Z])', '_', re.sub(r'[^0-9A-Za-z]+', '_', str(name))).lower().strip('_')
    return s if s and not s[0].isdigit() else f'f_{s}'


def _merge_items(items: list):
    """Junta os objetos de uma lista num só (para inferir o tipo do item)."""
    dicts = [i for i in items if isinstance(i, dict)]
    if dicts and len(dicts) == len(items):
        merged = {}
        for d in dicts:
            for k, v in d.items():
                merged.setdefault(k, v)
        return merged
    return items[0] if items else None


def schema_of(v) -> dict:
    if isinstance(v, dict):
        return {'type': 'object', 'properties': {k: schema_of(x) for k, x in v.items()},
                'required': list(v)}
    if isinstance(v, list):
        return {'type': 'array', 'items': schema_of(_merge_items(v)) if v else {}}
    if isinstance(v, bool):
        return {'type': 'boolean'}
    if isinstance(v, int):
        return {'type': 'integer'}
    if isinstance(v, float):
        return {'type': 'number'}
    if v is None:
        return {'type': 'null'}
    return {'type': 'string'}


def _types(data, root: str, render) -> str:
    """Percorre os objetos e chama render(nome, campos) para cada tipo novo."""
    blocks: list[str] = []

    def walk(v, name):
        if isinstance(v, dict):
            fields = [(k, walk(x, _pascal(k))) for k, x in v.items()]
            blocks.append(render(name, fields))
            return ('obj', name)
        if isinstance(v, list):
            return ('list', walk(_merge_items(v), name[:-1] if name.endswith('s') else f'{name}Item')
                    if v else ('any', None))
        if isinstance(v, bool):
            return ('bool', None)
        if isinstance(v, int):
            return ('int', None)
        if isinstance(v, float):
            return ('float', None)
        if v is None:
            return ('null', None)
        return ('str', None)

    walk(data, root)
    return '\n\n'.join(blocks) + '\n'


# === JSON =====================================================================
def json_format(text, indent='2 espaços', sort='Não'):
    data = load_json(text)
    return json.dumps(data, ensure_ascii=False, indent=_indent(indent), sort_keys=sort == 'Sim')


def json_validate(text):
    data = load_json(text)
    if isinstance(data, dict):
        kind = f'objeto com {len(data)} chave(s)'
    elif isinstance(data, list):
        kind = f'lista com {len(data)} item(ns)'
    else:
        kind = type(data).__name__
    return f'✓ JSON válido: {kind}.'


def json_minify(text):
    return json.dumps(load_json(text), ensure_ascii=False, separators=(',', ':'))


def json_to_yaml(text):
    return dump_yaml(load_json(text))


def json_to_toml(text):
    return dump_toml(load_json(text))


def json_to_markdown(text):
    rows = [_flat_row(r) if isinstance(r, dict) else {'valor': r} for r in _records(load_json(text))]
    cols = list(dict.fromkeys(k for r in rows for k in r))
    cell = lambda v: str('' if v is None else v).replace('|', '\\|').replace('\n', ' ')  # noqa: E731
    lines = ['| ' + ' | '.join(cols) + ' |', '| ' + ' | '.join('---' for _ in cols) + ' |']
    lines += ['| ' + ' | '.join(cell(r.get(c)) for c in cols) + ' |' for r in rows]
    return '\n'.join(lines) + '\n'


def json_schema(text):
    schema = {'$schema': 'http://json-schema.org/draft-07/schema#', **schema_of(load_json(text))}
    return json.dumps(schema, ensure_ascii=False, indent=2)


def json_to_typescript(text, root='Root'):
    def ts(t):
        kind, ref = t
        if kind == 'list':
            return f'{ts(ref)}[]'
        return {'obj': ref, 'bool': 'boolean', 'int': 'number', 'float': 'number', 'null': 'null',
                'str': 'string', 'any': 'unknown'}[kind]

    def render(name, fields):
        body = '\n'.join(f'  {k if re.fullmatch(r"[A-Za-z_$][\w$]*", k) else json.dumps(k)}: {ts(t)};'
                         for k, t in fields)
        return f'export interface {name} {{\n{body}\n}}'
    return _types(load_json(text), _pascal(root), render)


def json_to_go(text, root='Root'):
    def go(t):
        kind, ref = t
        if kind == 'list':
            return f'[]{go(ref)}'
        return {'obj': ref, 'bool': 'bool', 'int': 'int64', 'float': 'float64', 'null': 'interface{}',
                'str': 'string', 'any': 'interface{}'}[kind]

    def render(name, fields):
        body = '\n'.join(f'\t{_pascal(k)} {go(t)} `json:"{k}"`' for k, t in fields)
        return f'type {name} struct {{\n{body}\n}}'
    return _types(load_json(text), _pascal(root), render)


def json_to_rust(text, root='Root'):
    def rs(t):
        kind, ref = t
        if kind == 'list':
            return f'Vec<{rs(ref)}>'
        return {'obj': ref, 'bool': 'bool', 'int': 'i64', 'float': 'f64', 'null': 'Option<serde_json::Value>',
                'str': 'String', 'any': 'serde_json::Value'}[kind]

    def render(name, fields):
        lines = []
        for k, t in fields:
            field = _snake(k)
            if field != k:
                lines.append(f'    #[serde(rename = "{k}")]')
            lines.append(f'    pub {field}: {rs(t)},')
        return '#[derive(Debug, Clone, Serialize, Deserialize)]\npub struct ' + name + ' {\n' + '\n'.join(lines) + '\n}'
    return 'use serde::{Deserialize, Serialize};\n\n' + _types(load_json(text), _pascal(root), render)


def json_to_zod(text, root='Root'):
    def zod(t):
        kind, ref = t
        if kind == 'list':
            return f'z.array({zod(ref)})'
        return {'obj': f'{ref}Schema', 'bool': 'z.boolean()', 'int': 'z.number().int()', 'float': 'z.number()',
                'null': 'z.null()', 'str': 'z.string()', 'any': 'z.unknown()'}[kind]

    def render(name, fields):
        body = '\n'.join(f'  {k if re.fullmatch(r"[A-Za-z_$][\w$]*", k) else json.dumps(k)}: {zod(t)},'
                         for k, t in fields)
        return f'export const {name}Schema = z.object({{\n{body}\n}});\nexport type {name} = z.infer<typeof {name}Schema>;'
    return "import { z } from 'zod';\n\n" + _types(load_json(text), _pascal(root), render)


FLATTEN_MODES = ('Achatar', 'Desachatar')


def json_flatten(text, mode='Achatar', separator='.'):
    data = load_json(text)
    sep = separator or '.'
    if mode == 'Achatar':
        out = {}

        def walk(v, path):
            if isinstance(v, dict) and v:
                for k, x in v.items():
                    walk(x, f'{path}{sep}{k}' if path else str(k))
            elif isinstance(v, list) and v:
                for i, x in enumerate(v):
                    walk(x, f'{path}{sep}{i}' if path else str(i))
            else:
                out[path] = v
        walk(data, '')
        return json.dumps(out, ensure_ascii=False, indent=2)
    if not isinstance(data, dict):
        raise ValueError('Para desachatar, cole um objeto com chaves "a.b.c".')
    root: dict = {}
    for key, value in data.items():
        parts = key.split(sep)
        node = root
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = value

    def lists(v):  # {"0": a, "1": b} vira [a, b]
        if isinstance(v, dict):
            v = {k: lists(x) for k, x in v.items()}
            if v and all(k.isdigit() for k in v) and sorted(map(int, v)) == list(range(len(v))):
                return [v[str(i)] for i in range(len(v))]
        return v
    return json.dumps(lists(root), ensure_ascii=False, indent=2)


def _ptr(path: list) -> str:
    return '/' + '/'.join(str(p).replace('~', '~0').replace('/', '~1') for p in path) if path else ''


def json_patch(a, b):
    """RFC 6902: operações que transformam A em B."""
    ops = []

    def walk(x, y, path):
        if type(x) is not type(y):
            ops.append({'op': 'replace', 'path': _ptr(path), 'value': y})
        elif isinstance(x, dict):
            for k in x:
                if k not in y:
                    ops.append({'op': 'remove', 'path': _ptr(path + [k])})
                else:
                    walk(x[k], y[k], path + [k])
            for k in y:
                if k not in x:
                    ops.append({'op': 'add', 'path': _ptr(path + [k]), 'value': y[k]})
        elif isinstance(x, list):
            common = min(len(x), len(y))
            for i in range(common):
                walk(x[i], y[i], path + [i])
            for i in range(len(x) - 1, common - 1, -1):
                ops.append({'op': 'remove', 'path': _ptr(path + [i])})
            for i in range(common, len(y)):
                ops.append({'op': 'add', 'path': _ptr(path + ['-']), 'value': y[i]})
        elif x != y:
            ops.append({'op': 'replace', 'path': _ptr(path), 'value': y})
    walk(load_json(a), load_json(b), [])
    return json.dumps(ops, ensure_ascii=False, indent=2)


def json_schema_validate(document, schema):
    data, sch = load_json(document), load_json(schema)
    try:
        validator = jsonschema.validators.validator_for(sch)(sch)
    except jsonschema.SchemaError as e:
        raise ValueError(f'Schema inválido: {e.message}') from None
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if not errors:
        return '✓ O documento segue o schema.'
    return f'✗ {len(errors)} erro(s):\n' + '\n'.join(
        f'- {"/".join(map(str, e.path)) or "(raiz)"}: {e.message}' for e in errors)


def json_path(text, expression='$..*'):
    try:
        matches = jsonpath_parse(expression).find(load_json(text))
    except Exception as e:  # lark/ply levantam tipos variados
        raise ValueError(f'Expressão JSONPath inválida: {e}') from None
    return json.dumps([m.value for m in matches], ensure_ascii=False, indent=2)


def json_jmespath(text, expression='@'):
    return json.dumps(_query_jmespath(load_json(text), expression), ensure_ascii=False, indent=2)


def json_diff(a, b):
    x, y = load_json(a), load_json(b)
    lines = []

    def walk(u, v, path):
        if isinstance(u, dict) and isinstance(v, dict):
            for k in u.keys() | v.keys():
                p = f'{path}.{k}'
                if k not in v:
                    lines.append(f'- {p}: {json.dumps(u[k], ensure_ascii=False)}')
                elif k not in u:
                    lines.append(f'+ {p}: {json.dumps(v[k], ensure_ascii=False)}')
                else:
                    walk(u[k], v[k], p)
        elif isinstance(u, list) and isinstance(v, list):
            for i in range(max(len(u), len(v))):
                p = f'{path}[{i}]'
                if i >= len(v):
                    lines.append(f'- {p}: {json.dumps(u[i], ensure_ascii=False)}')
                elif i >= len(u):
                    lines.append(f'+ {p}: {json.dumps(v[i], ensure_ascii=False)}')
                else:
                    walk(u[i], v[i], p)
        elif u != v:
            lines.append(f'~ {path}: {json.dumps(u, ensure_ascii=False)} → {json.dumps(v, ensure_ascii=False)}')
    walk(x, y, '$')
    if not lines:
        return 'Os dois JSON são iguais.'
    return f'{len(lines)} diferença(s)\n' + '\n'.join(sorted(lines, key=lambda s: s[2:]))


def ndjson_view(text):
    items, bad = [], []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError as e:
            bad.append(f'linha {n}: {e.msg}')
    head = f'{len(items)} registro(s)' + (f' · {len(bad)} linha(s) inválida(s): ' + '; '.join(bad) if bad else '')
    return head + '\n' + json.dumps(items, ensure_ascii=False, indent=2)


_PROTO_DEFAULT = {'string': '', 'bytes': '', 'bool': False, 'double': 0.0, 'float': 0.0}


def protobuf_to_json(text):
    """Gera um JSON de exemplo a partir das mensagens de um .proto."""
    clean = re.sub(r'//.*|/\*.*?\*/', '', text, flags=re.S)
    messages: dict[str, list] = {}
    enums: dict[str, str] = {}
    for m in re.finditer(r'enum\s+(\w+)\s*\{([^{}]*)\}', clean):
        first = re.search(r'(\w+)\s*=', m.group(2))
        enums[m.group(1)] = first.group(1) if first else ''
    clean_no_enum = re.sub(r'enum\s+\w+\s*\{[^{}]*\}', '', clean)
    # mensagens de dentro para fora (aninhadas primeiro)
    pattern = re.compile(r'message\s+(\w+)\s*\{([^{}]*)\}')
    order = []
    while True:
        m = pattern.search(clean_no_enum)
        if not m:
            break
        fields = re.findall(r'(repeated\s+|optional\s+)?(map<\s*\w+\s*,\s*\w+\s*>|[\w.]+)\s+(\w+)\s*=\s*\d+', m.group(2))
        messages[m.group(1)] = fields
        order.append(m.group(1))
        clean_no_enum = clean_no_enum[:m.start()] + clean_no_enum[m.end():]
    if not messages:
        raise ValueError('Nenhuma "message" encontrada no .proto.')

    def sample(name, depth=0):
        out = {}
        for label, typ, field in messages[name]:
            typ = typ.split('.')[-1]
            if typ.startswith('map<'):
                value = {}
            elif typ in messages and depth < 5:
                value = sample(typ, depth + 1)
            elif typ in enums:
                value = enums[typ]
            elif typ in _PROTO_DEFAULT:
                value = _PROTO_DEFAULT[typ]
            elif re.match(r'(s|u)?int|fixed|sfixed', typ):
                value = 0
            else:
                value = {}
            out[field] = [value] if label.strip() == 'repeated' else value
        return out
    nested = {t.split('.')[-1] for f in messages.values() for _, t, _ in f}
    top = [n for n in order if n not in nested] or order
    result = {n: sample(n) for n in reversed(top)} if len(top) > 1 else sample(top[-1])
    return json.dumps(result, ensure_ascii=False, indent=2)


def json_to_csv(text, delimiter='Vírgula'):
    return dump_csv(load_json(text), delimiter)


def json_to_xml(text, root='root'):
    return dump_xml(load_json(text), root or 'root')


# === XML ======================================================================
def xml_format(text, indent='2 espaços'):
    tree = _xml_tree(text)
    etree.indent(tree, space='\t' if indent == 'Tab' else ' ' * _indent(indent))
    return etree.tostring(tree, encoding='unicode')


def xml_validate(text):
    tree = _xml_tree(text)
    return f'✓ XML bem formado: raiz <{etree.QName(tree).localname}>, {sum(1 for _ in tree.iter())} elemento(s).'


def xml_to_json(text):
    return dump_json(load_xml(text))


def xml_to_json_schema(text):
    return json.dumps({'$schema': 'http://json-schema.org/draft-07/schema#', **schema_of(load_xml(text))},
                      ensure_ascii=False, indent=2)


def xml_to_yaml(text):
    return dump_yaml(load_xml(text))


def xml_to_csv(text, delimiter='Vírgula'):
    return dump_csv(load_xml(text), delimiter)


def xml_minify(text):
    return etree.tostring(_xml_tree(text), encoding='unicode')


def xml_xpath(text, expression='//*'):
    tree = _xml_tree(text)
    try:
        result = tree.xpath(expression)
    except etree.XPathError as e:
        raise ValueError(f'XPath inválido: {e}') from None
    if not isinstance(result, list):
        return str(result)
    out = [etree.tostring(r, encoding='unicode').strip() if isinstance(r, etree._Element) else str(r)
           for r in result]
    return f'{len(out)} resultado(s)\n' + '\n'.join(out)


def xml_diff(a, b):
    return _diff(xml_format(a), xml_format(b), 'XML')


def xsd_validate(document, schema):
    try:
        xsd = etree.XMLSchema(_xml_tree(schema))
    except etree.XMLSchemaParseError as e:
        raise ValueError(f'XSD inválido: {e}') from None
    doc = _xml_tree(document)
    if xsd.validate(doc):
        return '✓ O XML segue o XSD.'
    return f'✗ {len(xsd.error_log)} erro(s):\n' + '\n'.join(f'- linha {e.line}: {e.message}' for e in xsd.error_log)


# === YAML =====================================================================
def yaml_format(text):
    docs = list(_yaml_all(text))
    return '---\n'.join(dump_yaml(d) for d in docs)


def _yaml_all(text):
    try:
        return list(yaml.safe_load_all(text))
    except yaml.YAMLError as e:
        raise ValueError(f'YAML inválido: {e}') from None


def yaml_minify(text):
    return '---\n'.join(dump_yaml(d, flow=True) for d in _yaml_all(text))


def yaml_validate(text):
    docs = _yaml_all(text)
    return f'✓ YAML válido: {len(docs)} documento(s).'


def yaml_to_json(text):
    docs = _yaml_all(text)
    return dump_json(docs[0] if len(docs) == 1 else docs)


def yaml_to_xml(text, root='root'):
    return dump_xml(load_yaml(text), root or 'root')


def yaml_to_csv(text, delimiter='Vírgula'):
    return dump_csv(load_yaml(text), delimiter)


def yaml_to_toml(text):
    return dump_toml(load_yaml(text))


def yaml_diff(a, b):
    return _diff(yaml_format(a), yaml_format(b), 'YAML')


QUERY_LANGS = ('JMESPath', 'JSONPath')


def yaml_query(text, expression='@', language='JMESPath'):
    data = load_yaml(text)
    if language == 'JSONPath':
        return dump_yaml(json.loads(json_path(json.dumps(data, default=str), expression)))
    return dump_yaml(_query_jmespath(data, expression))


def yaml_resolve_anchors(text):
    return '---\n'.join(dump_yaml(d) for d in _yaml_all(text))


def yaml_split(text):
    docs = _yaml_all(text)
    return '\n'.join(f'# ===== documento {i} de {len(docs)} =====\n{dump_yaml(d)}' for i, d in enumerate(docs, 1))


# === CSV ======================================================================
def csv_to_json(text, delimiter='Automático'):
    return dump_json(load_csv(text, delimiter))


def csv_to_xml(text, delimiter='Automático'):
    return dump_xml({'rows': {'row': load_csv(text, delimiter)}})


def csv_to_yaml(text, delimiter='Automático'):
    return dump_yaml(load_csv(text, delimiter))


def csv_to_html(text, delimiter='Automático'):
    return html_table(load_csv(text, delimiter))


def csv_format(text, delimiter='Automático', output='Vírgula'):
    rows = list(csv.reader(io.StringIO(text.strip('\ufeff')), delimiter=_delim(text, delimiter)))
    buf = io.StringIO()
    csv.writer(buf, delimiter=_DELIM_CHAR.get(output, ','), lineterminator='\n').writerows(
        [c.strip() for c in r] for r in rows if any(c.strip() for c in r))
    return buf.getvalue()


def csv_validate(text, delimiter='Automático'):
    delim = _delim(text, delimiter)
    rows = list(csv.reader(io.StringIO(text.strip('\ufeff')), delimiter=delim))
    if not rows:
        raise ValueError('CSV vazio.')
    width = len(rows[0])
    bad = [(n, len(r)) for n, r in enumerate(rows, 1) if r and len(r) != width]
    shown = {',': 'vírgula', ';': 'ponto e vírgula', '\t': 'tab', '|': 'barra'}[delim]
    if not bad:
        return f'✓ CSV válido: {len(rows) - 1} linha(s), {width} coluna(s), separador {shown}.'
    return (f'✗ {len(bad)} linha(s) com número de colunas diferente do cabeçalho ({width}):\n'
            + '\n'.join(f'- linha {n}: {w} coluna(s)' for n, w in bad[:50]))


def _sql_value(v: str) -> str:
    if v == '':
        return 'NULL'
    if re.fullmatch(r'-?\d+(\.\d+)?', v):
        return v
    return "'" + v.replace("'", "''") + "'"


def csv_to_sql(text, table='tabela', delimiter='Automático'):
    rows = load_csv(text, delimiter)
    name = re.sub(r'\W', '_', table or 'tabela')
    cols = list(rows[0])
    col_sql = ', '.join(f'"{c}"' for c in cols)
    return '\n'.join(f'INSERT INTO {name} ({col_sql}) VALUES ({", ".join(_sql_value(r.get(c) or "") for c in cols)});'
                     for r in rows) + '\n'


def csv_diff(a, b, delimiter='Automático'):
    ra = [tuple(r.items()) for r in load_csv(a, delimiter)]
    rb = [tuple(r.items()) for r in load_csv(b, delimiter)]
    removed = [r for r in ra if r not in rb]
    added = [r for r in rb if r not in ra]
    if not removed and not added:
        return 'Os dois CSV têm as mesmas linhas.'
    fmt = lambda r: ', '.join(f'{k}={v}' for k, v in r)  # noqa: E731
    return '\n'.join([f'{len(removed)} removida(s), {len(added)} adicionada(s)']
                     + [f'- {fmt(r)}' for r in removed] + [f'+ {fmt(r)}' for r in added])


def csv_columns(text, columns='', delimiter='Automático'):
    """columns: "c, a, b:novo_nome" — ordem nova; as que não aparecem somem."""
    rows = load_csv(text, delimiter)
    spec = [c.strip() for c in columns.split(',') if c.strip()]
    if not spec:
        raise ValueError(f'Diga as colunas na ordem que quer. Disponíveis: {", ".join(rows[0])}')
    pairs = []
    for item in spec:
        old, _, new = item.partition(':')
        old = old.strip()
        if old not in rows[0]:
            raise ValueError(f'Coluna "{old}" não existe. Disponíveis: {", ".join(rows[0])}')
        pairs.append((old, new.strip() or old))
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=_delim(text, delimiter), lineterminator='\n')
    w.writerow([n for _, n in pairs])
    w.writerows([r[o] for o, _ in pairs] for r in rows)
    return buf.getvalue()


def csv_dedupe(text, keys='', delimiter='Automático'):
    rows = load_csv(text, delimiter)
    key_cols = [k.strip() for k in keys.split(',') if k.strip()] or list(rows[0])
    missing = [k for k in key_cols if k not in rows[0]]
    if missing:
        raise ValueError(f'Coluna(s) inexistente(s): {", ".join(missing)}')
    seen, kept = set(), []
    for r in rows:
        k = tuple(r[c] for c in key_cols)
        if k not in seen:
            seen.add(k)
            kept.append(r)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), delimiter=_delim(text, delimiter), lineterminator='\n')
    w.writeheader()
    w.writerows(kept)
    return f'{buf.getvalue()}'


# === TOML =====================================================================
def toml_format(text):
    return dump_toml(load_toml(text))


def toml_validate(text):
    data = load_toml(text)
    return f'✓ TOML válido: {len(data)} chave(s)/tabela(s) no topo.'


def toml_to_json(text):
    return dump_json(load_toml(text))


def toml_to_yaml(text):
    return dump_yaml(load_toml(text))


def toml_to_xml(text, root='root'):
    return dump_xml(load_toml(text), root or 'root')


def toml_to_html(text):
    def render(v):
        if isinstance(v, dict):
            rows = ''.join(f'<tr><th>{escape(str(k))}</th><td>{render(x)}</td></tr>' for k, x in v.items())
            return f'<table>{rows}</table>'
        if isinstance(v, list):
            return '<ul>' + ''.join(f'<li>{render(x)}</li>' for x in v) + '</ul>'
        return escape(str(v))
    return render(load_toml(text)) + '\n'


def toml_minify(text):
    lines = [ln for ln in dump_toml(load_toml(text)).splitlines() if ln.strip()]
    return '\n'.join(lines) + '\n'


def toml_diff(a, b):
    return _diff(toml_format(a), toml_format(b), 'TOML')
