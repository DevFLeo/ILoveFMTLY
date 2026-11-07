import json

from core.settings import Settings


def test_missing_file_gives_defaults(tmp_path):
    s = Settings.load(tmp_path / 'config.json')
    assert s.mode == 'simple' and s.theme == 'Noite' and not s.registered


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / 'config.json'
    s = Settings.load(path)
    s.name, s.profile, s.mode, s.theme = 'Ana', 'instituicao', 'detailed', 'Claro'
    assert s.save() == path
    data = json.loads(path.read_text(encoding='utf-8'))
    assert data['name'] == 'Ana' and 'path' not in data
    again = Settings.load(path)
    assert again == s and again.registered


def test_corrupt_or_odd_file_falls_back(tmp_path):
    path = tmp_path / 'config.json'
    path.write_text('{nada', encoding='utf-8')
    assert Settings.load(path).mode == 'simple'
    path.write_text(json.dumps({'mode': 'xyz', 'name': 5, 'extra': 1}), encoding='utf-8')
    s = Settings.load(path)
    assert s.mode == 'simple' and s.name == ''


def test_no_path_never_writes(tmp_path):
    assert Settings().save() is None
