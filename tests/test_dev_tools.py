"""Roda TODAS as ferramentas de desenvolvedor com entrada real e confere os resultados-chave."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import base64  # noqa: E402
import json  # noqa: E402

import pytest  # noqa: E402
import yaml  # noqa: E402
from PIL import Image  # noqa: E402

from core.dev import data as D  # noqa: E402
from core.dev import sec as S  # noqa: E402
from core.dev import text as X  # noqa: E402
from ui.dev_tools import DEV_TOOLS  # noqa: E402
from ui.main_window import resolve_fn  # noqa: E402

J = '{"nome": "Ana", "idade": 30, "tags": ["a", "b"], "end": {"cidade": "Recife"}}'
JL = '[{"nome": "Ana", "idade": 30}, {"nome": "Bia", "idade": 25}]'
XMLS = '<pessoas><pessoa id="1"><nome>Ana</nome></pessoa><pessoa id="2"><nome>Bia</nome></pessoa></pessoas>'
XSD = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="pessoas"><xs:complexType>'
       '<xs:sequence><xs:element name="pessoa" maxOccurs="unbounded"><xs:complexType><xs:sequence>'
       '<xs:element name="nome" type="xs:string"/></xs:sequence><xs:attribute name="id" type="xs:int"/>'
       '</xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>')
Y = 'base: &b\n  host: x\napp:\n  <<: *b\n  porta: 80\n---\noutro: 1\n'
YL = '- nome: Ana\n  idade: 30\n- nome: Bia\n  idade: 25\n'
C = 'nome;email;idade\nAna;a@x.com;30\nBia;b@x.com;25\nAna;a@x.com;30\n'
T = 'titulo = "App"\n[db]\nhost = "localhost"\nporta = 5432\n'
TXT = 'Olá mundo. O rato roeu a roupa do rei de Roma.\nlinha dois\nlinha dois\n'
PROTO = 'syntax = "proto3";\nmessage Pessoa { string nome = 1; int32 idade = 2; repeated Tel tels = 3; }\n' \
        'message Tel { string numero = 1; }'
JWT = (base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip('=') + '.' +
       base64.urlsafe_b64encode(b'{"sub":"1","exp":1}').decode().rstrip('=') + '.sig')
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><metadata>x</metadata><!-- c -->'
       '<rect id="r" x="1.123456" y="1" width="5" height="5"/></svg>')
CERT = None  # gerado no teste a partir de uma chave

TEXT_SAMPLES = {
    'JSON': J, 'XML': XMLS, 'YAML': Y, 'CSV': C, 'TOML': T, 'Texto': TXT, 'Codificar': 'Olá & mundo',
    'IA': 'Por favor, basicamente explique o que é um PDF.', 'Web': 'https://u@ex.com:8080/a/b?x=1&y=2#top',
    'Cripto': 'segredo123', 'QR e códigos': 'https://fmtly.dev', 'Imagens': SVG,
}
OVERRIDE = {
    'json-md': JL, 'json-csv': JL, 'ndjson': '{"a":1}\n{"a":2}\nruim\n', 'proto-json': PROTO,
    'yaml-csv': YL, 'jwt': JWT, 'punycode': 'café.com.br', 'hex': 'Olá', 'morse': 'SOS',
    'md-html': '# Oi\n\n| a | b |\n|---|---|\n| 1 | 2 |', 'barcode': '5901234123457',
}
PARAMS = {'json-flatten': {}, 'csv-columns': {'columns': 'email:contato, nome'}, 'hmac': {'key': 'k'},
          'totp': {'secret': 'JBSWY3DPEHPK3PXP'}, 'barcode': {'kind': 'EAN-13'}}
TWO = {'JSON': (J, J.replace('30', '31')), 'XML': (XMLS, XMLS.replace('Bia', 'Bea')),
       'YAML': (YL, YL.replace('25', '26')), 'CSV': (C, C.replace('Bia', 'Bea')),
       'TOML': (T, T.replace('5432', '5433')), 'Texto': ('a\nb', 'a\nc')}


def _defaults(tool):
    vals = {p.key: p.default for p in tool.params}
    vals.update(PARAMS.get(tool.id, {}))
    return vals


@pytest.fixture
def qr_png(tmp_path):
    p = tmp_path / 'qr.png'
    p.write_bytes(S.qr_generate('ILoveFMTLY'))
    return p


@pytest.mark.parametrize('tool', DEV_TOOLS, ids=[t.id for t in DEV_TOOLS])
def test_every_dev_tool_runs(tool, tmp_path, qr_png):
    fn = resolve_fn(tool.fn)
    kw = _defaults(tool)
    if tool.dev_input == 'none':
        out = fn(**kw)
    elif tool.dev_input == 'two':
        a, b = (J, XSD) if tool.id == 'xsd' else TWO.get(tool.group, (J, J))
        if tool.id == 'xsd':
            a = XMLS
        if tool.id == 'json-schema-check':
            a, b = J, D.json_schema(J)
        out = fn(a, b, **kw)
    elif tool.dev_input == 'file':
        out = fn(qr_png, **kw)
    elif tool.id == 'cert':
        pytest.skip('coberto em test_cert_decode')
    else:
        out = fn(OVERRIDE.get(tool.id, TEXT_SAMPLES[tool.group]), **kw)
    assert out, f'{tool.id} devolveu vazio'


# --- conferências de resultado ------------------------------------------------------
def test_json_roundtrips():
    assert json.loads(D.json_minify(J)) == json.loads(J)
    assert json.loads(D.yaml_to_json(D.json_to_yaml(J))) == json.loads(J)
    assert json.loads(D.toml_to_json(D.json_to_toml(J))) == json.loads(J)
    flat = D.json_flatten(J)
    assert json.loads(flat)['end.cidade'] == 'Recife'
    assert json.loads(D.json_flatten(flat, mode='Desachatar')) == json.loads(J)


def test_json_errors_are_friendly():
    with pytest.raises(ValueError, match='linha 1, coluna'):
        D.json_format('{"a": }')


def test_json_patch_and_diff():
    ops = json.loads(D.json_patch('{"a":1,"b":2}', '{"a":5,"c":3}'))
    assert {'op': 'replace', 'path': '/a', 'value': 5} in ops
    assert {'op': 'remove', 'path': '/b'} in ops and {'op': 'add', 'path': '/c', 'value': 3} in ops
    assert '~ $.a: 1 → 5' in D.json_diff('{"a":1}', '{"a":5}')


def test_type_generators():
    assert 'export interface Root' in D.json_to_typescript(J) and 'idade: number;' in D.json_to_typescript(J)
    assert 'Idade int64 `json:"idade"`' in D.json_to_go(J)
    assert 'pub idade: i64,' in D.json_to_rust(J)
    assert 'idade: z.number().int(),' in D.json_to_zod(J)
    assert json.loads(D.json_schema(J))['properties']['tags']['type'] == 'array'


def test_queries():
    assert json.loads(D.json_path(JL, '$[*].nome')) == ['Ana', 'Bia']
    assert json.loads(D.json_jmespath(JL, '[?idade > `26`].nome')) == ['Ana']
    assert '2 resultado(s)' in D.xml_xpath(XMLS, '//nome/text()')
    assert yaml.safe_load(D.yaml_query(YL, '[*].nome')) == ['Ana', 'Bia']


def test_schema_validators():
    assert D.json_schema_validate(J, D.json_schema(J)).startswith('✓')
    assert D.json_schema_validate('{"nome": 1}', D.json_schema(J)).startswith('✗')
    assert D.xsd_validate(XMLS, XSD).startswith('✓')
    assert D.xsd_validate('<pessoas><x/></pessoas>', XSD).startswith('✗')


def test_yaml_anchors_and_split():
    out = D.yaml_resolve_anchors(Y)
    assert '*b' not in out and '&b' not in out and 'host: x' in out
    assert 'documento 2 de 2' in D.yaml_split(Y)


def test_csv_tools():
    assert len(json.loads(D.csv_to_json(C))) == 3
    assert D.csv_dedupe(C).count('Ana') == 1
    assert D.csv_columns(C, 'email:contato, nome').splitlines()[0] == 'contato;nome'
    assert "INSERT INTO tabela" in D.csv_to_sql(C) and ', 30);' in D.csv_to_sql(C)
    assert D.csv_validate('a,b\n1\n').startswith('✗')
    assert '<td>Ana</td>' in D.csv_to_html(C)


def test_text_tools():
    assert X.case_convert('nome do cliente', 'camelCase') == 'nomeDoCliente'
    assert X.case_convert('nomeDoCliente', 'snake_case') == 'nome_do_cliente'
    assert X.dedupe_lines('a\nb\na') == 'a\nb'
    assert X.morse(X.morse('SOS'), 'Decodificar') == 'SOS'
    assert X.caesar(X.caesar('Olá', 3), 3, 'Decodificar') == 'Olá'
    assert X.base64_tool(X.base64_tool('ação'), 'Decodificar') == 'ação'
    assert X.hex_tool(X.hex_tool('ç'), 'Decodificar') == 'ç'
    assert X.punycode('café.com') == 'xn--caf-dma.com'
    assert '3 ocorrência(s)' in X.regex_test('a1 b2 c3', r'\w\d')
    assert 'EXPIRADO' in X.jwt_decode(JWT)
    assert 'Porta: 8080' in X.url_parse('https://ex.com:8080/a?x=1')
    assert X.html_entities('é<') == '&eacute;&lt;'


def test_security_tools():
    assert 'SHA-256   ' + '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08' in S.hash_text('test')
    assert len(S.make_ids('ULID', 3).split()) == 3 and len(S.ulid()) == 26
    assert S.uuid7()[14] == '7'
    pw = S.password_generate(20, 'Sim', 1)
    assert len(pw) == 20 and any(c.isdigit() for c in pw)
    assert 'Muito fraca' in S.password_strength('123456')
    assert 'BEGIN PUBLIC KEY' in S.keypair('EC P-256')
    assert S.totp('JBSWY3DPEHPK3PXP').startswith('Código atual: ')


def test_cert_decode():
    from datetime import datetime, timedelta, timezone

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'ilove.local')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(1).not_valid_before(now).not_valid_after(now + timedelta(days=10))
            .sign(key, hashes.SHA256()))
    pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    out = S.cert_decode(pem)
    assert 'CN=ilove.local' in out and 'válido' in out


def test_qr_roundtrip(tmp_path):
    png = tmp_path / 'q.png'
    png.write_bytes(S.qr_generate('https://fmtly.dev'))
    assert 'https://fmtly.dev' in S.qr_read(png)
    assert S.qr_generate('x', fmt='SVG').lstrip().startswith(b'<')


def test_barcode_png(tmp_path):
    data = S.barcode_generate('5901234123457', 'EAN-13')
    p = tmp_path / 'b.png'
    p.write_bytes(data)
    assert Image.open(p).width > 50


def test_fake_data_brazil():
    rows = json.loads(S.fake_data(5, 'nome, cpf, cidade'))
    assert len(rows) == 5 and set(rows[0]) == {'nome', 'cpf', 'cidade'}


def test_svg_optimize_shrinks():
    out = S.svg_optimize(SVG)
    assert '<metadata' not in out and 'id="r"' not in out and '1.12' in out and '% menor' in out


def test_file_hash(tmp_path):
    f = tmp_path / 'x.bin'
    f.write_bytes(b'test')
    assert 'CRC32     d87f7e0c' in S.file_hash(f)


# --- janela -----------------------------------------------------------------------
def test_dev_dialog_live_and_save(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    from ui.dev_dialog import DevDialog
    from ui.tools import BY_ID
    d = DevDialog(None, BY_ID['json-format'])
    qtbot.addWidget(d)
    d.inputs[0].setPlainText('{"b":1,"a":2}')
    qtbot.waitUntil(lambda: d.output.toPlainText().startswith('{\n'), timeout=3000)
    d.inputs[0].setPlainText('{ruim')
    qtbot.waitUntil(lambda: not d.error.isHidden(), timeout=3000)
    assert 'JSON inválido' in d.error.text() and not d.save_btn.isEnabled()
    d.inputs[0].setPlainText('[1]')
    qtbot.waitUntil(lambda: d.save_btn.isEnabled(), timeout=3000)
    target = tmp_path / 'saida'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **k: (str(target), ''))
    d.save()
    assert (tmp_path / 'saida.json').read_text(encoding='utf-8').startswith('[')


def test_dev_dialog_image_output(qtbot):
    from ui.dev_dialog import DevDialog
    from ui.tools import BY_ID
    d = DevDialog(None, BY_ID['qr-make'])
    qtbot.addWidget(d)
    d.inputs[0].setPlainText('oi')
    d.run()
    assert isinstance(d.result, bytes) and not d.image.isHidden() and d.default_ext() == '.png'


def test_dev_tool_from_hub(qtbot, tmp_path, monkeypatch):
    from core.workspace import Workspace
    from ui.dev_dialog import DevDialog
    from ui.main_window import MainWindow
    opened = []
    monkeypatch.setattr(DevDialog, 'exec', lambda self: opened.append(self) or 0)
    w = MainWindow(Workspace(tmp_path / 'ws'), spool_dir=None, word_ok=False)
    qtbot.addWidget(w)
    src = tmp_path / 'a.json'
    src.write_text('{"x": 1}', encoding='utf-8')
    w.run_tool('json-format', [src])
    assert opened and opened[0].inputs[0].toPlainText() == '{"x": 1}'
