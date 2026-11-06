from core import printer
from core.workspace import Workspace


def test_collect_moves_complete_pdfs(make_pdf, tmp_path):
    spool = printer.ensure_spool(tmp_path / 'spool')
    ws = Workspace(tmp_path / 'ws')
    make_pdf(1).replace(spool / 'print.pdf')
    make_pdf(1).replace(spool / 'outro.pdf')
    (spool / 'incompleto.pdf').write_bytes(b'%PDF-1.7 ainda gravando')
    (spool / 'lixo.pdf').write_bytes(b'nada')

    got = printer.collect(ws, spool, settle=0)

    assert len(got) == 2
    assert len({p.name for p in got}) == 2  # mesmo segundo, nomes únicos
    assert all(p.name.startswith('Impressão ') for p in got)
    assert sorted(p.name for p in spool.iterdir()) == ['incompleto.pdf', 'lixo.pdf']


def test_collect_missing_dir(tmp_path):
    assert printer.collect(Workspace(tmp_path / 'ws'), tmp_path / 'nao-existe') == []
