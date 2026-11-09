"""Cripto, geradores, QR / código de barras e SVG. Tudo local (sem consulta a vazamentos)."""

import base64
import binascii
import hashlib
import hmac as _hmac
import io
import json
import math
import os
import re
import secrets
import string
import struct
import time
import uuid
import zlib
from datetime import datetime, timezone
from pathlib import Path

# === Hash ======================================================================
HASHES = ('MD5', 'SHA-1', 'SHA-256', 'SHA-384', 'SHA-512', 'SHA3-256', 'BLAKE2b')
_HASHLIB = {'MD5': 'md5', 'SHA-1': 'sha1', 'SHA-256': 'sha256', 'SHA-384': 'sha384',
            'SHA-512': 'sha512', 'SHA3-256': 'sha3_256', 'BLAKE2b': 'blake2b'}


def hash_text(text):
    data = text.encode('utf-8')
    return '\n'.join(f'{name:<9} {hashlib.new(_HASHLIB[name], data).hexdigest()}' for name in HASHES)


def hmac_text(text, key='', algorithm='SHA-256'):
    if not key:
        raise ValueError('Informe a chave secreta.')
    mac = _hmac.new(key.encode('utf-8'), text.encode('utf-8'), _HASHLIB[algorithm])
    return f'{algorithm} hex:    {mac.hexdigest()}\n{algorithm} base64: {base64.b64encode(mac.digest()).decode()}'


def file_hash(path):
    p = Path(path)
    hs = {n: hashlib.new(_HASHLIB[n]) for n in ('MD5', 'SHA-1', 'SHA-256', 'SHA-512')}
    crc = 0
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            for h in hs.values():
                h.update(chunk)
            crc = zlib.crc32(chunk, crc)
    lines = [f'Arquivo: {p.name}', f'Tamanho: {p.stat().st_size:,} bytes'.replace(',', '.'),
             f'CRC32     {crc & 0xFFFFFFFF:08x}']
    lines += [f'{n:<9} {h.hexdigest()}' for n, h in hs.items()]
    return '\n'.join(lines)


# === Senhas ====================================================================
def password_strength(text):
    """zxcvbn offline: estimativa de tempo para quebrar. Não consulta vazamentos (o app é offline)."""
    from zxcvbn import zxcvbn
    if not text:
        raise ValueError('Digite a senha para avaliar.')
    r = zxcvbn(text[:200])
    labels = ('Muito fraca', 'Fraca', 'Razoável', 'Forte', 'Muito forte')
    pool = sum(n for cond, n in ((re.search('[a-z]', text), 26), (re.search('[A-Z]', text), 26),
                                 (re.search('[0-9]', text), 10), (re.search(r'[^A-Za-z0-9]', text), 33)) if cond)
    entropy = len(text) * math.log2(pool) if pool else 0
    lines = [f'Nota: {r["score"]}/4 · {labels[r["score"]]}', f'Entropia aproximada: {entropy:.0f} bits',
             f'Para quebrar (ataque offline rápido): {r["crack_times_display"]["offline_fast_hashing_1e10_per_second"]}',
             f'Para quebrar (site com limite de tentativas): {r["crack_times_display"]["online_throttling_100_per_hour"]}']
    fb = r['feedback']
    if fb.get('warning'):
        lines.append(f'Aviso: {fb["warning"]}')
    lines += [f'Dica: {s}' for s in fb.get('suggestions', [])]
    lines.append('Obs.: o app é offline e não consulta bases de senhas vazadas.')
    return '\n'.join(lines)


CHARSETS = ('Letras e números', 'Só letras', 'Só números', 'Hex', 'Letras, números e símbolos', 'Base64 URL')
_CHARS = {'Letras e números': string.ascii_letters + string.digits, 'Só letras': string.ascii_letters,
          'Só números': string.digits, 'Hex': '0123456789abcdef',
          'Letras, números e símbolos': string.ascii_letters + string.digits + '!@#$%&*()-_=+[]{};:,.?',
          'Base64 URL': string.ascii_letters + string.digits + '-_'}


def random_string(length=32, charset='Letras e números', count=1):
    length, count = int(length), int(count)
    if not 1 <= length <= 10_000 or not 1 <= count <= 1000:
        raise ValueError('Tamanho de 1 a 10.000 e quantidade de 1 a 1.000.')
    chars = _CHARS[charset]
    return '\n'.join(''.join(secrets.choice(chars) for _ in range(length)) for _ in range(count))


def password_generate(length=16, symbols='Sim', count=5, avoid_similar='Sim'):
    length, count = int(length), int(count)
    if not 6 <= length <= 256:
        raise ValueError('Tamanho de 6 a 256.')
    pools = [string.ascii_lowercase, string.ascii_uppercase, string.digits]
    if symbols == 'Sim':
        pools.append('!@#$%&*-_=+?')
    if avoid_similar == 'Sim':
        pools = [''.join(c for c in p if c not in 'Il1O0o') for p in pools]
    out = []
    for _ in range(count):
        pw = [secrets.choice(p) for p in pools]  # pelo menos um de cada tipo
        pw += [secrets.choice(''.join(pools)) for _ in range(length - len(pw))]
        secrets.SystemRandom().shuffle(pw)
        out.append(''.join(pw))
    return '\n'.join(out)


# === UUID / ULID ===============================================================
ID_KINDS = ('UUID v4', 'UUID v7', 'ULID')
_CROCKFORD = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'


def ulid() -> str:
    ms = int(time.time() * 1000)
    value = (ms << 80) | int.from_bytes(os.urandom(10), 'big')
    return ''.join(_CROCKFORD[(value >> (5 * i)) & 31] for i in reversed(range(26)))


def uuid7() -> str:
    ms = int(time.time() * 1000)
    rand = int.from_bytes(os.urandom(10), 'big')
    value = (ms & ((1 << 48) - 1)) << 80 | (0x7 << 76) | ((rand >> 62) & 0xFFF) << 64 | (0b10 << 62) | (rand & ((1 << 62) - 1))
    return str(uuid.UUID(int=value))


def make_ids(kind='UUID v4', count=10, uppercase='Não'):
    count = int(count)
    if not 1 <= count <= 100_000:
        raise ValueError('Quantidade de 1 a 100.000.')
    gen = {'UUID v4': lambda: str(uuid.uuid4()), 'UUID v7': uuid7, 'ULID': ulid}[kind]
    ids = [gen() for _ in range(count)]
    return '\n'.join(i.upper() if uppercase == 'Sim' else i for i in ids)


# === Chaves e certificados (cryptography) =========================================
KEY_TYPES = ('RSA 2048', 'RSA 3072', 'RSA 4096', 'EC P-256', 'EC P-384', 'Ed25519')


def keypair(kind='RSA 2048'):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
    if kind.startswith('RSA'):
        key = rsa.generate_private_key(public_exponent=65537, key_size=int(kind.split()[1]))
    elif kind == 'Ed25519':
        key = ed25519.Ed25519PrivateKey.generate()
    else:
        key = ec.generate_private_key(ec.SECP256R1() if kind.endswith('256') else ec.SECP384R1())
    priv = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption()).decode()
    pub = key.public_key().public_bytes(serialization.Encoding.PEM,
                                        serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return f'{pub}\n{priv}'


def cert_decode(text):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    data = text.strip().encode()
    try:
        cert = x509.load_pem_x509_certificate(data) if b'-----BEGIN' in data else \
            x509.load_der_x509_certificate(base64.b64decode(data))
    except (ValueError, binascii.Error):
        raise ValueError('Cole um certificado X.509 em PEM (-----BEGIN CERTIFICATE-----).') from None
    now = datetime.now(timezone.utc)
    lines = [f'Assunto: {cert.subject.rfc4514_string()}', f'Emissor: {cert.issuer.rfc4514_string()}',
             f'Série: {cert.serial_number:X}',
             f'Válido de: {cert.not_valid_before_utc:%d/%m/%Y %H:%M} UTC',
             f'Válido até: {cert.not_valid_after_utc:%d/%m/%Y %H:%M} UTC',
             'Situação: ' + ('EXPIRADO' if cert.not_valid_after_utc < now else
                             f'válido ({(cert.not_valid_after_utc - now).days} dias restantes)'),
             f'Algoritmo da assinatura: {cert.signature_algorithm_oid._name}',
             f'SHA-256: {cert.fingerprint(hashes.SHA256()).hex(":").upper()}']
    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        lines.append('Nomes alternativos: ' + ', '.join(str(n.value) for n in san.value))
    except x509.ExtensionNotFound:
        pass
    return '\n'.join(lines)


# === TOTP ==========================================================================
def totp(secret='', digits=6, period=30):
    raw = re.sub(r'\s', '', secret).upper()
    if not raw:
        raise ValueError('Cole o segredo em Base32 (o código que aparece junto do QR).')
    try:
        key = base64.b32decode(raw + '=' * (-len(raw) % 8))
    except (binascii.Error, ValueError):
        raise ValueError('Segredo inválido: precisa ser Base32 (letras A-Z e números 2-7).') from None
    digits, period = int(digits), int(period)
    now = time.time()

    def code(t):
        counter = struct.pack('>Q', int(t // period))
        h = _hmac.new(key, counter, hashlib.sha1).digest()
        o = h[-1] & 0x0F
        return str((struct.unpack('>I', h[o:o + 4])[0] & 0x7FFFFFFF) % 10 ** digits).zfill(digits)
    left = period - int(now % period)
    return (f'Código atual: {code(now)}  (vale mais {left} s)\n'
            f'Anterior: {code(now - period)} · Próximo: {code(now + period)}')


# === Geradores ======================================================================
FAKE_FIELDS = ('nome', 'email', 'telefone', 'cpf', 'cidade', 'estado', 'empresa', 'cargo', 'data',
               'endereco', 'cep', 'uuid')
FAKE_FORMATS = ('JSON', 'CSV')
FAKE_LOCALES = ('Português (Brasil)', 'Inglês (EUA)')


def fake_data(count=10, fields='nome, email, telefone, cidade', fmt='JSON', locale='Português (Brasil)'):
    from faker import Faker
    count = int(count)
    if not 1 <= count <= 10_000:
        raise ValueError('Quantidade de 1 a 10.000.')
    fk = Faker('pt_BR' if locale.startswith('Port') else 'en_US')
    makers = {'nome': fk.name, 'email': fk.email, 'telefone': fk.phone_number,
              'cpf': getattr(fk, 'cpf', fk.ssn), 'cidade': fk.city,
              'estado': getattr(fk, 'estado_sigla', fk.state), 'empresa': fk.company, 'cargo': fk.job,
              'data': lambda: fk.date_of_birth().isoformat(), 'endereco': fk.street_address,
              'cep': fk.postcode, 'uuid': lambda: str(uuid.uuid4())}
    chosen = [f.strip().lower() for f in fields.split(',') if f.strip()]
    unknown = [f for f in chosen if f not in makers]
    if unknown or not chosen:
        raise ValueError(f'Campos disponíveis: {", ".join(FAKE_FIELDS)}')
    rows = [{f: makers[f]() for f in chosen} for _ in range(count)]
    if fmt == 'CSV':
        import csv
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=chosen, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
        return buf.getvalue()
    return json.dumps(rows, ensure_ascii=False, indent=2)


GITIGNORE = {
    'Python': '__pycache__/\n*.py[cod]\n*.egg-info/\n.venv/\nvenv/\n.env\n.pytest_cache/\n.mypy_cache/\nbuild/\ndist/\n',
    'Node': 'node_modules/\nnpm-debug.log*\nyarn-error.log\n.pnpm-store/\ndist/\n.env\n.env.local\ncoverage/\n',
    'Java': '*.class\n*.jar\n*.war\ntarget/\n.gradle/\nbuild/\nout/\n',
    'Kotlin/Android': '*.iml\n.gradle/\nlocal.properties\n/build\n/captures\n.externalNativeBuild\n.cxx\n',
    'Go': '*.exe\n*.test\n*.out\nvendor/\ngo.work\n',
    'Rust': 'target/\nCargo.lock\n**/*.rs.bk\n',
    '.NET': 'bin/\nobj/\n*.user\n*.suo\n.vs/\n',
    'Windows': 'Thumbs.db\nDesktop.ini\n$RECYCLE.BIN/\n',
    'macOS': '.DS_Store\n.AppleDouble\n.LSOverride\n',
    'VS Code': '.vscode/*\n!.vscode/settings.json\n!.vscode/extensions.json\n',
    'JetBrains': '.idea/\n*.iws\n',
}


def gitignore(stacks='Python, Windows, VS Code'):
    chosen = [s.strip() for s in stacks.split(',') if s.strip()]
    lookup = {k.lower(): k for k in GITIGNORE}
    unknown = [s for s in chosen if s.lower() not in lookup]
    if unknown or not chosen:
        raise ValueError(f'Disponíveis: {", ".join(GITIGNORE)}')
    return '\n'.join(f'# --- {lookup[s.lower()]} ---\n{GITIGNORE[lookup[s.lower()]]}' for s in chosen)


def readme(name='Meu projeto', description='', install='', usage='', license_name='MIT'):
    return (f'# {name}\n\n{description or "Uma frase dizendo o que o projeto faz."}\n\n'
            f'## Instalação\n\n```bash\n{install or "pip install -r requirements.txt"}\n```\n\n'
            f'## Uso\n\n```bash\n{usage or "python app.py"}\n```\n\n'
            '## Como contribuir\n\n1. Faça um fork\n2. Crie um branch (`git checkout -b minha-mudanca`)\n'
            '3. Abra um pull request\n\n'
            f'## Licença\n\n{license_name}\n')


# === QR e código de barras ==========================================================
QR_FORMATS = ('PNG', 'SVG')
QR_LEVELS = ('M (15%)', 'L (7%)', 'Q (25%)', 'H (30%)')


def qr_generate(text, fmt='PNG', level='M (15%)', size=10):
    import qrcode
    from qrcode.image.svg import SvgPathImage
    if not text.strip():
        raise ValueError('Digite o texto ou link do QR.')
    correction = {'L': qrcode.constants.ERROR_CORRECT_L, 'M': qrcode.constants.ERROR_CORRECT_M,
                  'Q': qrcode.constants.ERROR_CORRECT_Q, 'H': qrcode.constants.ERROR_CORRECT_H}[level[0]]
    qr = qrcode.QRCode(error_correction=correction, box_size=int(size), border=4)
    qr.add_data(text)
    qr.make(fit=True)
    buf = io.BytesIO()
    if fmt == 'SVG':
        qr.make_image(image_factory=SvgPathImage).save(buf)
    else:
        qr.make_image(fill_color='black', back_color='white').save(buf, 'PNG')
    return buf.getvalue()


def qr_read(path):
    import zxingcpp
    from PIL import Image
    try:
        img = Image.open(path)
        img.load()
    except OSError:
        raise ValueError('Escolha uma imagem (PNG, JPG...) com o QR ou código de barras.') from None
    results = zxingcpp.read_barcodes(img)
    if not results:
        return 'Nenhum QR ou código de barras encontrado na imagem.'
    return '\n\n'.join(f'{r.format.name}:\n{r.text}' for r in results)


BARCODES = ('Code 128', 'EAN-13', 'EAN-8', 'UPC-A', 'ITF', 'Code 39', 'ISBN-13')
_BARCODE_NAMES = {'Code 128': 'code128', 'EAN-13': 'ean13', 'EAN-8': 'ean8', 'UPC-A': 'upca',
                  'ITF': 'itf', 'Code 39': 'code39', 'ISBN-13': 'isbn13'}


def barcode_generate(text, kind='Code 128', fmt='PNG'):
    import barcode
    from barcode.writer import ImageWriter, SVGWriter
    if not text.strip():
        raise ValueError('Digite o valor do código de barras.')
    try:
        code = barcode.get(_BARCODE_NAMES[kind], text.strip(),
                           writer=ImageWriter() if fmt == 'PNG' else SVGWriter())
    except (barcode.errors.BarcodeError, ValueError) as e:
        raise ValueError(f'Valor inválido para {kind}: {e}') from None
    buf = io.BytesIO()
    code.write(buf)
    return buf.getvalue()


# === SVG ============================================================================
def svg_optimize(text, precision=2):
    """Tira comentários, metadados, IDs não usados e espaços; arredonda números."""
    from lxml import etree
    try:
        root = etree.fromstring(text.encode('utf-8'), etree.XMLParser(remove_blank_text=True,
                                                                     remove_comments=True))
    except etree.XMLSyntaxError as e:
        raise ValueError(f'SVG inválido: {e}') from None
    before = len(text.encode('utf-8'))
    junk = ('metadata', 'title', 'desc')
    for el in list(root.iter()):
        if not isinstance(el.tag, str):
            continue
        tag = etree.QName(el).localname
        if tag in junk or etree.QName(el).namespace and 'sodipodi' in etree.QName(el).namespace:
            el.getparent().remove(el)
            continue
        for attr in list(el.attrib):
            ns = etree.QName(attr).namespace or ''
            if 'inkscape' in ns or 'sodipodi' in ns:
                del el.attrib[attr]
    used = set(re.findall(r'url\(#([^)]+)\)|href="#([^"]+)"', etree.tostring(root, encoding='unicode')))
    used = {a or b for a, b in used}
    for el in root.iter():
        if isinstance(el.tag, str) and el.get('id') and el.get('id') not in used:
            del el.attrib['id']
    p = int(precision)
    out = etree.tostring(root, encoding='unicode')
    out = re.sub(r'-?\d+\.\d+', lambda m: (f'{float(m.group()):.{p}f}'.rstrip('0').rstrip('.') or '0'), out)
    after = len(out.encode('utf-8'))
    return out + f'\n<!-- {before} → {after} bytes ({100 - after * 100 // max(before, 1)}% menor) -->'
