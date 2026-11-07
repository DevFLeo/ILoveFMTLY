"""Ferramentas de desenvolvedor (inspiradas no fmtly.dev, licença MIT), registradas como Tool.

Todas usam mode='dev': abrem o DevDialog (ui/dev_dialog.py), com entrada de texto
(ou dois textos, ou um arquivo, ou nada) e saída de texto ou imagem.
Funções em core/dev/: data.py, text.py, sec.py.
"""

from core.dev import data as D
from core.dev import sec as S
from core.dev import text as X
from ui.tool_base import Param, Tool

JSON = frozenset({'.json'})
XML = frozenset({'.xml', '.svg', '.xsd'})
YAML = frozenset({'.yaml', '.yml'})
CSV = frozenset({'.csv', '.tsv'})
TOML = frozenset({'.toml'})
TXT = frozenset({'.txt', '.md', '.log'})
IMG = frozenset({'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif', '.tif', '.tiff'})

INDENT = Param('indent', 'Recuo', '2 espaços', options=D.INDENTS)
DIRECTION = Param('direction', 'Sentido', 'Codificar', options=X.DIRECTIONS)
DELIM = Param('delimiter', 'Separador', 'Automático', options=D.DELIMS)
OUT_DELIM = Param('delimiter', 'Separador da saída', 'Vírgula', options=D.DELIMS[1:])
ROOT = Param('root', 'Nome do tipo raiz', 'Root')
XML_ROOT = Param('root', 'Elemento raiz', 'root')


def dev(id, title, desc, group, icon, fn, params=(), inputs='text', accepts=frozenset(), ext='.txt',
        labels=('Entrada', 'Saída')):
    return Tool(id, title, desc, group, icon, accepts, max_files=1, mode='dev', fn=fn, ext=ext,
                params=tuple(params), dev_input=inputs, dev_labels=labels)


TWO = ('A (original)', 'B (novo)')

DEV_TOOLS: list[Tool] = [
    # --- JSON (21) ------------------------------------------------------------
    dev('json-format', 'Formatar JSON', 'Indente e organize, com opção de ordenar chaves.', 'JSON', 'braces',
        'dev.data.json_format', (INDENT, Param('sort', 'Ordenar chaves', 'Não', options=('Não', 'Sim'))),
        accepts=JSON, ext='.json'),
    dev('json-validate', 'Validar JSON', 'Diz se é válido e onde está o erro.', 'JSON', 'shield-check',
        'dev.data.json_validate', accepts=JSON),
    dev('json-minify', 'Minificar JSON', 'Tudo numa linha, sem espaços.', 'JSON', 'minimize',
        'dev.data.json_minify', accepts=JSON, ext='.json'),
    dev('json-yaml', 'JSON para YAML', 'Converte mantendo a ordem das chaves.', 'JSON', 'arrow-right-left',
        'dev.data.json_to_yaml', accepts=JSON, ext='.yaml'),
    dev('json-toml', 'JSON para TOML', 'Objeto JSON vira arquivo TOML.', 'JSON', 'arrow-right-left',
        'dev.data.json_to_toml', accepts=JSON, ext='.toml'),
    dev('json-md', 'JSON para tabela Markdown', 'Lista de objetos vira tabela .md.', 'JSON', 'table',
        'dev.data.json_to_markdown', accepts=JSON, ext='.md'),
    dev('json-schema', 'Gerar JSON Schema', 'Schema draft-07 a partir de um exemplo.', 'JSON', 'file-code',
        'dev.data.json_schema', accepts=JSON, ext='.json'),
    dev('json-go', 'JSON para Go', 'Structs com tags json.', 'JSON', 'code', 'dev.data.json_to_go', (ROOT,),
        accepts=JSON, ext='.go'),
    dev('json-ts', 'JSON para TypeScript', 'Interfaces TypeScript.', 'JSON', 'code', 'dev.data.json_to_typescript',
        (ROOT,), accepts=JSON, ext='.ts'),
    dev('json-rust', 'JSON para Rust', 'Structs com Serde.', 'JSON', 'code', 'dev.data.json_to_rust', (ROOT,),
        accepts=JSON, ext='.rs'),
    dev('json-zod', 'JSON para Zod', 'Schema Zod + tipo inferido.', 'JSON', 'code', 'dev.data.json_to_zod',
        (ROOT,), accepts=JSON, ext='.ts'),
    dev('json-flatten', 'Achatar / desachatar JSON', 'Aninhado vira "a.b.c" e volta.', 'JSON', 'layers',
        'dev.data.json_flatten', (Param('mode', 'Modo', 'Achatar', options=D.FLATTEN_MODES),
                                  Param('separator', 'Separador', '.')), accepts=JSON, ext='.json'),
    dev('json-patch', 'Gerar JSON Patch', 'RFC 6902: o que muda de A para B.', 'JSON', 'git-compare-arrows',
        'dev.data.json_patch', inputs='two', ext='.json', labels=TWO),
    dev('json-schema-check', 'Validar com JSON Schema', 'Confere um JSON contra um schema.', 'JSON',
        'shield-check', 'dev.data.json_schema_validate', inputs='two', labels=('Documento JSON', 'Schema')),
    dev('jsonpath', 'Consulta JSONPath', 'Ex.: $.itens[*].nome', 'JSON', 'filter', 'dev.data.json_path',
        (Param('expression', 'Expressão', '$..*', hint='ex.: $.itens[?(@.preco > 10)].nome'),),
        accepts=JSON, ext='.json'),
    dev('jmespath', 'Consulta JMESPath', 'Ex.: itens[?preco > `10`].nome', 'JSON', 'filter',
        'dev.data.json_jmespath', (Param('expression', 'Expressão', '@', hint='ex.: itens[*].nome'),),
        accepts=JSON, ext='.json'),
    dev('json-diff', 'Comparar JSON', 'Diferenças por caminho ($.a.b).', 'JSON', 'git-compare-arrows',
        'dev.data.json_diff', inputs='two', labels=TWO),
    dev('ndjson', 'Ver NDJSON', 'Uma linha por registro; mostra linhas com erro.', 'JSON', 'list-ordered',
        'dev.data.ndjson_view', accepts=frozenset({'.ndjson', '.jsonl'}), ext='.json'),
    dev('proto-json', 'Protobuf para JSON', 'JSON de exemplo a partir de um .proto.', 'JSON', 'braces',
        'dev.data.protobuf_to_json', accepts=frozenset({'.proto'}), ext='.json'),
    dev('json-csv', 'JSON para CSV', 'Lista de objetos vira planilha.', 'JSON', 'sheet', 'dev.data.json_to_csv',
        (OUT_DELIM,), accepts=JSON, ext='.csv'),
    dev('json-xml', 'JSON para XML', 'Objeto vira documento XML.', 'JSON', 'arrow-right-left',
        'dev.data.json_to_xml', (XML_ROOT,), accepts=JSON, ext='.xml'),

    # --- XML (10) ---------------------------------------------------------------
    dev('xml-format', 'Formatar XML', 'Indenta e organiza.', 'XML', 'file-code', 'dev.data.xml_format', (INDENT,),
        accepts=XML, ext='.xml'),
    dev('xml-validate', 'Validar XML', 'Confere se é bem formado.', 'XML', 'shield-check', 'dev.data.xml_validate',
        accepts=XML),
    dev('xml-json', 'XML para JSON', 'Atributos viram "@nome".', 'XML', 'arrow-right-left', 'dev.data.xml_to_json',
        accepts=XML, ext='.json'),
    dev('xml-schema', 'XML para JSON Schema', 'Infere o schema da estrutura.', 'XML', 'file-code',
        'dev.data.xml_to_json_schema', accepts=XML, ext='.json'),
    dev('xml-yaml', 'XML para YAML', 'Converte para YAML.', 'XML', 'arrow-right-left', 'dev.data.xml_to_yaml',
        accepts=XML, ext='.yaml'),
    dev('xml-csv', 'XML para CSV', 'Registros repetidos viram linhas.', 'XML', 'sheet', 'dev.data.xml_to_csv',
        (OUT_DELIM,), accepts=XML, ext='.csv'),
    dev('xml-minify', 'Minificar XML', 'Sem espaços entre as tags.', 'XML', 'minimize', 'dev.data.xml_minify',
        accepts=XML, ext='.xml'),
    dev('xpath', 'Consulta XPath', 'Ex.: //livro[@ano>2000]/titulo', 'XML', 'filter', 'dev.data.xml_xpath',
        (Param('expression', 'Expressão', '//*', hint='ex.: //item/@id'),), accepts=XML),
    dev('xml-diff', 'Comparar XML', 'Diferenças linha a linha, já formatado.', 'XML', 'git-compare-arrows',
        'dev.data.xml_diff', inputs='two', labels=TWO),
    dev('xsd', 'Validar com XSD', 'Confere um XML contra um XSD.', 'XML', 'shield-check', 'dev.data.xsd_validate',
        inputs='two', labels=('Documento XML', 'Schema XSD')),

    # --- YAML (11) --------------------------------------------------------------
    dev('yaml-format', 'Formatar YAML', 'Recuo uniforme, vários documentos.', 'YAML', 'file-code',
        'dev.data.yaml_format', accepts=YAML, ext='.yaml'),
    dev('yaml-minify', 'Minificar YAML', 'Estilo compacto { } e [ ].', 'YAML', 'minimize', 'dev.data.yaml_minify',
        accepts=YAML, ext='.yaml'),
    dev('yaml-validate', 'Validar YAML', 'Diz se é válido e onde está o erro.', 'YAML', 'shield-check',
        'dev.data.yaml_validate', accepts=YAML),
    dev('yaml-json', 'YAML para JSON', 'Converte para JSON.', 'YAML', 'arrow-right-left', 'dev.data.yaml_to_json',
        accepts=YAML, ext='.json'),
    dev('yaml-xml', 'YAML para XML', 'Converte para XML.', 'YAML', 'arrow-right-left', 'dev.data.yaml_to_xml',
        (XML_ROOT,), accepts=YAML, ext='.xml'),
    dev('yaml-csv', 'YAML para CSV', 'Lista vira planilha.', 'YAML', 'sheet', 'dev.data.yaml_to_csv', (OUT_DELIM,),
        accepts=YAML, ext='.csv'),
    dev('yaml-toml', 'YAML para TOML', 'Converte para TOML.', 'YAML', 'arrow-right-left', 'dev.data.yaml_to_toml',
        accepts=YAML, ext='.toml'),
    dev('yaml-diff', 'Comparar YAML', 'Diferenças lado a lado.', 'YAML', 'git-compare-arrows', 'dev.data.yaml_diff',
        inputs='two', labels=TWO),
    dev('yaml-query', 'Consultar YAML', 'JMESPath ou JSONPath.', 'YAML', 'filter', 'dev.data.yaml_query',
        (Param('expression', 'Expressão', '@'), Param('language', 'Linguagem', 'JMESPath', options=D.QUERY_LANGS)),
        accepts=YAML, ext='.yaml'),
    dev('yaml-anchors', 'Expandir âncoras YAML', 'Troca &âncoras e *apelidos pelo valor.', 'YAML', 'link',
        'dev.data.yaml_resolve_anchors', accepts=YAML, ext='.yaml'),
    dev('yaml-split', 'Separar documentos YAML', 'Arquivo com --- vira partes numeradas.', 'YAML', 'split',
        'dev.data.yaml_split', accepts=YAML, ext='.yaml'),

    # --- CSV (10) ---------------------------------------------------------------
    dev('csv-json', 'CSV para JSON', 'Cada linha vira um objeto.', 'CSV', 'arrow-right-left', 'dev.data.csv_to_json',
        (DELIM,), accepts=CSV, ext='.json'),
    dev('csv-xml', 'CSV para XML', 'Cada linha vira <row>.', 'CSV', 'arrow-right-left', 'dev.data.csv_to_xml',
        (DELIM,), accepts=CSV, ext='.xml'),
    dev('csv-yaml', 'CSV para YAML', 'Lista de registros YAML.', 'CSV', 'arrow-right-left', 'dev.data.csv_to_yaml',
        (DELIM,), accepts=CSV, ext='.yaml'),
    dev('csv-html', 'CSV para tabela HTML', '<table> pronta para colar.', 'CSV', 'table', 'dev.data.csv_to_html',
        (DELIM,), accepts=CSV, ext='.html'),
    dev('csv-format', 'Formatar CSV', 'Troca o separador e limpa espaços.', 'CSV', 'sheet', 'dev.data.csv_format',
        (DELIM, Param('output', 'Separador da saída', 'Vírgula', options=D.DELIMS[1:])), accepts=CSV, ext='.csv'),
    dev('csv-validate', 'Validar CSV', 'Acha linhas com colunas a mais ou a menos.', 'CSV', 'shield-check',
        'dev.data.csv_validate', (DELIM,), accepts=CSV),
    dev('csv-sql', 'CSV para SQL', 'Comandos INSERT INTO.', 'CSV', 'code', 'dev.data.csv_to_sql',
        (Param('table', 'Tabela', 'tabela'), DELIM), accepts=CSV, ext='.sql'),
    dev('csv-diff', 'Comparar CSV', 'Linhas que entraram e saíram.', 'CSV', 'git-compare-arrows',
        'dev.data.csv_diff', (DELIM,), inputs='two', labels=TWO),
    dev('csv-columns', 'Reordenar colunas CSV', 'Escolha, renomeie (antigo:novo) e tire colunas.', 'CSV',
        'arrow-right-left', 'dev.data.csv_columns',
        (Param('columns', 'Colunas na ordem', '', hint='ex.: nome, email:contato, idade'), DELIM),
        accepts=CSV, ext='.csv'),
    dev('csv-dedupe', 'Remover duplicadas CSV', 'Por linha inteira ou por colunas-chave.', 'CSV', 'filter',
        'dev.data.csv_dedupe', (Param('keys', 'Colunas-chave (vazio = linha toda)', '', hint='ex.: email'), DELIM),
        accepts=CSV, ext='.csv'),

    # --- TOML (8) ---------------------------------------------------------------
    dev('toml-format', 'Formatar TOML', 'Reescreve com estilo padrão.', 'TOML', 'file-code', 'dev.data.toml_format',
        accepts=TOML, ext='.toml'),
    dev('toml-validate', 'Validar TOML', 'Diz se é válido e onde está o erro.', 'TOML', 'shield-check',
        'dev.data.toml_validate', accepts=TOML),
    dev('toml-json', 'TOML para JSON', 'Converte para JSON.', 'TOML', 'arrow-right-left', 'dev.data.toml_to_json',
        accepts=TOML, ext='.json'),
    dev('toml-yaml', 'TOML para YAML', 'Converte para YAML.', 'TOML', 'arrow-right-left', 'dev.data.toml_to_yaml',
        accepts=TOML, ext='.yaml'),
    dev('toml-xml', 'TOML para XML', 'Converte para XML.', 'TOML', 'arrow-right-left', 'dev.data.toml_to_xml',
        (XML_ROOT,), accepts=TOML, ext='.xml'),
    dev('toml-html', 'TOML para tabela HTML', 'Tabelas aninhadas em HTML.', 'TOML', 'table', 'dev.data.toml_to_html',
        accepts=TOML, ext='.html'),
    dev('toml-minify', 'Minificar TOML', 'Sem comentários nem linhas vazias.', 'TOML', 'minimize',
        'dev.data.toml_minify', accepts=TOML, ext='.toml'),
    dev('toml-diff', 'Comparar TOML', 'Diferenças lado a lado.', 'TOML', 'git-compare-arrows', 'dev.data.toml_diff',
        inputs='two', labels=TWO),

    # --- Texto (13) -------------------------------------------------------------
    dev('word-count', 'Contar palavras', 'Palavras, caracteres, frases e tempo de leitura.', 'Texto', 'type',
        'dev.text.word_count', accepts=TXT),
    dev('lorem', 'Lorem ipsum', 'Texto de exemplo em parágrafos, frases ou palavras.', 'Texto', 'file-text',
        'dev.text.lorem', (Param('amount', 'Quantidade', 3, min=1, max=500),
                           Param('unit', 'Em', 'Parágrafos', options=X.LOREM_UNITS)), inputs='none'),
    dev('md-html', 'Markdown para HTML', 'Com tabelas e blocos de código.', 'Texto', 'code',
        'dev.text.markdown_to_html', accepts=frozenset({'.md', '.markdown'}), ext='.html'),
    dev('case', 'Maiúsculas e minúsculas', 'camelCase, snake_case, Título...', 'Texto', 'type',
        'dev.text.case_convert', (Param('case', 'Para', 'MAIÚSCULAS', options=X.CASES),), accepts=TXT),
    dev('reverse', 'Inverter texto', 'Por caractere, palavra ou linha.', 'Texto', 'arrow-right-left',
        'dev.text.reverse', (Param('mode', 'Inverter', 'Caracteres', options=X.REVERSE_MODES),), accepts=TXT),
    dev('dedupe-lines', 'Remover linhas repetidas', 'Mantém a primeira de cada.', 'Texto', 'filter',
        'dev.text.dedupe_lines', (Param('ignore_case', 'Ignorar maiúsculas', 'Não', options=('Não', 'Sim')),),
        accepts=TXT),
    dev('sort-lines', 'Ordenar linhas', 'A-Z, tamanho, números ou embaralhar.', 'Texto', 'list-ordered',
        'dev.text.sort_lines', (Param('order', 'Ordem', 'A → Z', options=X.SORTS),), accepts=TXT),
    dev('text-diff', 'Comparar textos', 'Diferenças linha a linha.', 'Texto', 'git-compare-arrows',
        'dev.text.text_diff', inputs='two', labels=TWO),
    dev('regex', 'Testar regex', 'Ocorrências, grupos e substituição.', 'Texto', 'scan-text', 'dev.text.regex_test',
        (Param('pattern', 'Regex', r'\w+'), Param('flags', 'Flags (i m s x)', 'i'),
         Param('replace', 'Substituir por (opcional)', '')), accepts=TXT),
    dev('readability', 'Legibilidade', 'Índice Flesch para português.', 'Texto', 'book-open',
        'dev.text.readability', accepts=TXT),
    dev('escape', 'Escapar texto', 'JSON, HTML, URL, SQL, regex, CSV.', 'Texto', 'code', 'dev.text.escape_text',
        (Param('kind', 'Para', X.ESCAPES[0], options=X.ESCAPES), DIRECTION), accepts=TXT),
    dev('morse', 'Código Morse', 'Texto ↔ Morse.', 'Texto', 'binary', 'dev.text.morse', (DIRECTION,)),
    dev('whitespace', 'Limpar espaços', 'Espaços duplos, tabs e linhas vazias.', 'Texto', 'brush-cleaning',
        'dev.text.whitespace_clean', (Param('tabs', 'Trocar tabs por espaços', 'Sim', options=('Sim', 'Não')),),
        accepts=TXT),

    # --- Codificar (8) ----------------------------------------------------------
    dev('base64', 'Base64', 'Codifique e decodifique, padrão ou URL-safe.', 'Codificar', 'binary',
        'dev.text.base64_tool', (DIRECTION, Param('variant', 'Variante', 'Padrão', options=X.B64_VARIANTS))),
    dev('url-encode', 'Codificar URL', 'Percent-encoding, componente ou URL inteira.', 'Codificar', 'link',
        'dev.text.url_tool', (DIRECTION, Param('mode', 'Modo', 'Componente', options=X.URL_MODES))),
    dev('html-entities', 'Entidades HTML', '&amp; &#233; &#xE9; e volta.', 'Codificar', 'code',
        'dev.text.html_entities', (DIRECTION, Param('mode', 'Tipo', 'Nomeadas', options=X.ENTITY_MODES))),
    dev('unicode', 'Inspecionar Unicode', 'Código, bytes UTF-8, categoria e nome.', 'Codificar', 'type',
        'dev.text.unicode_inspect'),
    dev('hex', 'Hex ↔ texto', 'UTF-8 em hexadecimal e volta.', 'Codificar', 'hash', 'dev.text.hex_tool', (DIRECTION,)),
    dev('caesar', 'ROT13 / César', 'Desloca as letras; 13 = ROT13.', 'Codificar', 'shuffle', 'dev.text.caesar',
        (Param('shift', 'Deslocamento', 13, min=1, max=25), DIRECTION)),
    dev('punycode', 'Punycode', 'Domínios com acento ↔ xn--.', 'Codificar', 'globe', 'dev.text.punycode',
        (DIRECTION,)),
    dev('jwt', 'Ler JWT', 'Cabeçalho, dados, validade e algoritmo.', 'Codificar', 'key-round', 'dev.text.jwt_decode'),

    # --- QR e códigos (3) -------------------------------------------------------
    dev('qr-make', 'Gerar QR Code', 'Link ou texto vira QR em PNG ou SVG.', 'QR e códigos', 'qr-code',
        'dev.sec.qr_generate', (Param('fmt', 'Formato', 'PNG', options=S.QR_FORMATS),
                                Param('level', 'Correção de erro', 'M (15%)', options=S.QR_LEVELS),
                                Param('size', 'Tamanho do módulo', 10, min=2, max=40, suffix=' px')),
        ext='.png'),
    dev('qr-read', 'Ler QR Code', 'Lê QR e códigos de barras de uma imagem.', 'QR e códigos', 'scan-text',
        'dev.sec.qr_read', inputs='file', accepts=IMG),
    dev('barcode', 'Gerar código de barras', 'Code 128, EAN-13, UPC-A, ITF...', 'QR e códigos', 'barcode',
        'dev.sec.barcode_generate', (Param('kind', 'Tipo', 'Code 128', options=S.BARCODES),
                                     Param('fmt', 'Formato', 'PNG', options=S.QR_FORMATS)), ext='.png'),

    # --- Cripto (9) -------------------------------------------------------------
    dev('hash', 'Gerar hash', 'MD5, SHA-1, SHA-256, SHA-512, SHA3, BLAKE2.', 'Cripto', 'hash', 'dev.sec.hash_text'),
    dev('hmac', 'Gerar HMAC', 'Assinatura com chave secreta.', 'Cripto', 'key-round', 'dev.sec.hmac_text',
        (Param('key', 'Chave secreta', ''), Param('algorithm', 'Algoritmo', 'SHA-256', options=S.HASHES))),
    dev('file-hash', 'Hash de arquivo', 'MD5, SHA-256, CRC32 de qualquer arquivo.', 'Cripto', 'shield-check',
        'dev.sec.file_hash', inputs='file'),
    dev('pw-strength', 'Força da senha', 'Nota, entropia e tempo para quebrar.', 'Cripto', 'lock',
        'dev.sec.password_strength'),
    dev('random-string', 'Texto aleatório', 'Tokens e chaves com gerador seguro.', 'Cripto', 'shuffle',
        'dev.sec.random_string', (Param('length', 'Tamanho', 32, min=1, max=10000),
                                  Param('charset', 'Caracteres', S.CHARSETS[0], options=S.CHARSETS),
                                  Param('count', 'Quantidade', 1, min=1, max=1000)), inputs='none'),
    dev('uuid', 'UUID / ULID', 'UUID v4, v7 ou ULID.', 'Cripto', 'hash', 'dev.sec.make_ids',
        (Param('kind', 'Tipo', 'UUID v4', options=S.ID_KINDS), Param('count', 'Quantidade', 1, min=1, max=1000),
         Param('uppercase', 'Maiúsculas', 'Não', options=('Não', 'Sim'))), inputs='none'),
    dev('keypair', 'Par de chaves RSA / EC', 'Chave pública e privada em PEM.', 'Cripto', 'key-round',
        'dev.sec.keypair', (Param('kind', 'Tipo', S.KEY_TYPES[0], options=S.KEY_TYPES),), inputs='none',
        ext='.pem'),
    dev('cert', 'Ler certificado', 'X.509: dono, emissor, validade, SHA-256.', 'Cripto', 'shield-check',
        'dev.sec.cert_decode', accepts=frozenset({'.pem', '.crt', '.cer'})),
    dev('totp', 'Código TOTP (2FA)', 'O código de 6 dígitos a partir do segredo.', 'Cripto', 'clock',
        'dev.sec.totp', (Param('secret', 'Segredo Base32', ''), Param('digits', 'Dígitos', 6, min=6, max=8),
                         Param('period', 'Período', 30, min=15, max=120, suffix=' s')), inputs='none'),

    # --- IA (3) -----------------------------------------------------------------
    dev('tokens', 'Contar tokens', 'Estimativa de tokens e custo por modelo.', 'IA', 'bot', 'dev.text.token_count',
        accepts=TXT),
    dev('prompt-opt', 'Enxugar prompt', 'Tira enrolação e mostra a economia.', 'IA', 'sparkles',
        'dev.text.prompt_optimize', accepts=TXT),
    dev('system-prompt', 'Montar system prompt', 'Papel, objetivo, tom, regras e formato.', 'IA', 'bot',
        'dev.text.system_prompt', (Param('role', 'Você é', 'um assistente de suporte'),
                                   Param('goal', 'Objetivo', ''), Param('tone', 'Tom', 'Direto e cordial'),
                                   Param('rules', 'Regras (separe com ;)', ''),
                                   Param('output_format', 'Formato da resposta', ''),
                                   Param('examples', 'Exemplos', '')), inputs='none', ext='.md'),

    # --- Geradores (5) ----------------------------------------------------------
    dev('fake-data', 'Dados falsos', 'Nomes, e-mails, CPF... para testes.', 'Geradores', 'shuffle',
        'dev.sec.fake_data', (Param('count', 'Quantidade', 10, min=1, max=10000),
                              Param('fields', 'Campos', 'nome, email, telefone, cidade',
                                    hint=', '.join(S.FAKE_FIELDS)),
                              Param('fmt', 'Formato', 'JSON', options=S.FAKE_FORMATS),
                              Param('locale', 'Idioma', S.FAKE_LOCALES[0], options=S.FAKE_LOCALES)),
        inputs='none', ext='.json'),
    dev('uuid-batch', 'UUIDs em lote', 'Milhares de UUID v4 ou v7.', 'Geradores', 'list-ordered',
        'dev.sec.make_ids', (Param('kind', 'Tipo', 'UUID v4', options=S.ID_KINDS),
                             Param('count', 'Quantidade', 1000, min=1, max=100000),
                             Param('uppercase', 'Maiúsculas', 'Não', options=('Não', 'Sim'))), inputs='none'),
    dev('password', 'Gerar senhas', 'Fortes, com ou sem símbolos.', 'Geradores', 'lock', 'dev.sec.password_generate',
        (Param('length', 'Tamanho', 16, min=6, max=256), Param('symbols', 'Símbolos', 'Sim', options=('Sim', 'Não')),
         Param('count', 'Quantidade', 5, min=1, max=1000),
         Param('avoid_similar', 'Evitar parecidos (l, 1, O, 0)', 'Sim', options=('Sim', 'Não'))), inputs='none'),
    dev('gitignore', 'Montar .gitignore', 'Junte regras de várias tecnologias.', 'Geradores', 'file-code',
        'dev.sec.gitignore', (Param('stacks', 'Tecnologias', 'Python, Windows, VS Code',
                                    hint=', '.join(S.GITIGNORE)),), inputs='none', ext='.gitignore'),
    dev('readme', 'Modelo de README', 'Esqueleto de README.md.', 'Geradores', 'file-text', 'dev.sec.readme',
        (Param('name', 'Nome do projeto', 'Meu projeto'), Param('description', 'Descrição', ''),
         Param('install', 'Como instalar', ''), Param('usage', 'Como usar', ''),
         Param('license_name', 'Licença', 'MIT')), inputs='none', ext='.md'),

    # --- Web (1) e SVG ------------------------------------------------------------
    dev('url-parse', 'Ler URL', 'Protocolo, host, porta, caminho e parâmetros.', 'Web', 'globe',
        'dev.text.url_parse'),
    dev('svg-opt', 'Otimizar SVG', 'Tira metadados, comentários e casas decimais.', 'Imagens', 'minimize',
        'dev.sec.svg_optimize', (Param('precision', 'Casas decimais', 2, min=0, max=6),),
        accepts=frozenset({'.svg'}), ext='.svg'),
]

DEV_GROUPS = ['JSON', 'XML', 'YAML', 'CSV', 'TOML', 'Texto', 'Codificar', 'Cripto', 'QR e códigos', 'IA',
              'Geradores', 'Web']
