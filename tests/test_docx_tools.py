"""Word B: ajustes em DOCX sem o Word."""

import zipfile
from pathlib import Path

import docx
import pytest
from docx.shared import Pt
from lxml import etree

from core import docx_tools
from core.docx_tools import DocxError

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def _run_xml(text, tag='w:t'):
    return (f'<w:r xmlns:w="{W}"><{tag} xml:space="preserve">{text}</{tag}></w:r>')


@pytest.fixture
def contrato(tmp_path) -> Path:
    """DOCX com autor, comentário, revisão pendente, tabela e cabeçalho."""
    d = docx.Document()
    d.core_properties.author = 'Maria Souza'
    d.core_properties.last_modified_by = 'João Lima'
    d.core_properties.title = 'Contrato de locação'
    d.sections[0].header.paragraphs[0].text = 'Contratante: Imobiliária Norte'
    p = d.add_paragraph('A Contratante pagará até o dia 5.')
    d.add_comment(p.runs, text='Conferir a data', author='João Lima')
    # revisão: "R$ 1.200" inserido, "R$ 1.000" apagado
    rev = d.add_paragraph('Valor: ')
    ins = etree.fromstring(f'<w:ins xmlns:w="{W}" w:id="90" w:author="João Lima">'
                           f'{_run_xml("R$ 1.200")}</w:ins>')
    dele = etree.fromstring(f'<w:del xmlns:w="{W}" w:id="91" w:author="João Lima">'
                            f'{_run_xml("R$ 1.000", "w:delText")}</w:del>')
    rev._p.append(ins)
    rev._p.append(dele)
    t = d.add_table(rows=1, cols=1)
    t.cell(0, 0).text = 'Assinatura da Contratante'
    out = tmp_path / 'contrato.docx'
    d.save(out)
    return out


def _parts(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def _all_text(path: Path) -> str:
    d = docx.Document(path)
    body = '\n'.join(p.text for p in d.paragraphs)
    cells = '\n'.join(c.text for row in d.tables for r in row.rows for c in r.cells)
    header = '\n'.join(p.text for p in d.sections[0].header.paragraphs)
    return '\n'.join((body, cells, header))


# --- limpar ------------------------------------------------------------------
def test_limpar_tira_autor_comentarios_e_aceita_revisoes(contrato, tmp_path):
    [out] = docx_tools.clean([contrato], tmp_path / 'saida')
    assert out.name == 'contrato_limpo.docx'
    parts = _parts(out)
    doc_xml = parts['word/document.xml'].decode('utf-8')
    assert 'commentRangeStart' not in doc_xml and 'commentReference' not in doc_xml
    assert not any(n.startswith('word/comments') for n in parts)
    assert b'comments' not in parts['[Content_Types].xml']
    assert 'w:ins ' not in doc_xml and 'w:del ' not in doc_xml and 'delText' not in doc_xml
    assert 'Valor: R$ 1.200' in _all_text(out)
    assert 'R$ 1.000' not in _all_text(out)
    props = docx.Document(out).core_properties
    assert props.author == '' and props.last_modified_by == ''
    assert 'Maria' not in parts['docProps/core.xml'].decode('utf-8')
    assert b'w:removePersonalInformation' in parts['word/settings.xml']
    assert b'w:rsid' not in parts['word/document.xml']


def test_limpar_nao_toca_no_original(contrato, tmp_path):
    antes = contrato.read_bytes()
    docx_tools.clean([contrato], tmp_path / 'saida')
    assert contrato.read_bytes() == antes


def test_limpar_resultado_abre_no_python_docx(contrato, tmp_path):
    [out] = docx_tools.clean([contrato], tmp_path / 'saida')
    assert 'A Contratante pagará' in _all_text(out)


# --- substituir --------------------------------------------------------------
def test_substituir_em_corpo_tabela_e_cabecalho(contrato, tmp_path):
    [out] = docx_tools.replace([contrato], tmp_path, find='Contratante', replace='Locatária',
                               match_case='Sim')
    assert out.name == 'contrato_substituido.docx'
    texto = _all_text(out)
    assert 'Contratante' not in texto
    assert texto.count('Locatária') == 3


def test_substituir_texto_partido_em_varios_runs(tmp_path):
    d = docx.Document()
    p = d.add_paragraph()
    a = p.add_run('Imobi')
    a.bold = True
    b = p.add_run('liária ')
    b.italic = True
    c = p.add_run('Norte')
    c.font.size = Pt(14)
    src = tmp_path / 'partido.docx'
    d.save(src)
    [out] = docx_tools.replace([src], tmp_path, find='Imobiliária Norte', replace='Casa Sul',
                               match_case='Sim')
    runs = docx.Document(out).paragraphs[0].runs
    assert ''.join(r.text for r in runs) == 'Casa Sul'
    assert runs[0].text == 'Casa Sul' and runs[0].bold  # herda o formato do 1º pedaço


def test_substituir_sem_diferenciar_maiusculas(tmp_path):
    d = docx.Document()
    d.add_paragraph('CPF do LOCADOR e cpf do locador.')
    src = tmp_path / 'c.docx'
    d.save(src)
    [out] = docx_tools.replace([src], tmp_path, find='locador', replace='Proprietário',
                               match_case='Não')
    assert docx.Document(out).paragraphs[0].text == 'CPF do Proprietário e cpf do Proprietário.'


def test_substituir_vazio_falha(contrato, tmp_path):
    with pytest.raises(DocxError):
        docx_tools.replace([contrato], tmp_path, find='', replace='x', match_case='Sim')


def test_contar_trocas(contrato):
    assert docx_tools.count_matches(contrato, 'contratante', match_case=False) == 3


# --- juntar ------------------------------------------------------------------
def test_juntar_na_ordem(tmp_path):
    fontes = []
    for nome in ('Capítulo 1 — Partes', 'Capítulo 2 — Prazo'):
        d = docx.Document()
        d.add_heading(nome, level=1)
        d.add_paragraph(f'Texto de {nome}.')
        f = tmp_path / f'{nome[:10]}.docx'
        d.save(f)
        fontes.append(f)
    [out] = docx_tools.merge(fontes, tmp_path / 'juntado.docx')
    texto = [p.text for p in docx.Document(out).paragraphs if p.text]
    assert texto.index('Capítulo 1 — Partes') < texto.index('Capítulo 2 — Prazo')


# --- exportar ----------------------------------------------------------------
@pytest.mark.parametrize('fmt, ext', [('TXT', '.txt'), ('Markdown', '.md'), ('HTML', '.html')])
def test_exportar_texto(contrato, tmp_path, fmt, ext):
    [out] = docx_tools.export_text([contrato], tmp_path, fmt=fmt)
    assert out.suffix == ext
    texto = out.read_text(encoding='utf-8')
    assert 'A Contratante pagará' in texto
    assert 'Assinatura da Contratante' in texto


def test_exportar_salva_imagens(tmp_path, make_png):
    d = docx.Document()
    d.add_paragraph('Planta do imóvel:')
    d.add_picture(str(make_png()))
    src = tmp_path / 'planta.docx'
    d.save(src)
    [out] = docx_tools.export_text([src], tmp_path / 'saida', fmt='HTML')
    pasta = out.parent / 'planta_imagens'
    imgs = list(pasta.iterdir())
    assert len(imgs) == 1
    assert f'planta_imagens/{imgs[0].name}' in out.read_text(encoding='utf-8')


# --- erros -------------------------------------------------------------------
def test_arquivo_invalido(tmp_path):
    ruim = tmp_path / 'ruim.docx'
    ruim.write_bytes(b'nao sou zip')
    with pytest.raises(DocxError, match='ruim.docx'):
        docx_tools.clean([ruim], tmp_path / 'saida')
    assert not (tmp_path / 'saida' / 'ruim_limpo.docx').exists()


def test_docx_com_senha(tmp_path):
    cifrado = tmp_path / 'senha.docx'
    cifrado.write_bytes(bytes.fromhex('D0CF11E0A1B11AE1') + b'\0' * 512)  # contêiner OLE
    with pytest.raises(DocxError, match='senha'):
        docx_tools.clean([cifrado], tmp_path / 'saida')
