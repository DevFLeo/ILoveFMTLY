# ILoveFMTLY

Aplicativo desktop para Windows que ajusta documentos sensíveis **sem enviá-los a nenhum servidor**. Tudo roda na própria máquina: a aplicação bloqueia o acesso à rede ao iniciar e não tem telemetria nem verificação de atualizações.

Esta é a primeira entrega, focada em PDF. Próximos módulos, em ordem: Word, Excel, CSV, demais formatos e, por fim, as ferramentas de desenvolvedor (JSON, YAML, XML, encode, hash...).

## O que faz (PDF v1)

- **Importar** PDFs e imagens (PNG, JPG, BMP, TIFF, WebP), pelo botão ou arrastando arquivos para a janela. PDFs com senha pedem a senha; PDFs danificados passam por reparo automático.
- **Visualizar** com miniaturas e zoom (Ctrl + roda do mouse ou "Ajustar").
- **Juntar** (importe vários arquivos), **reordenar** arrastando miniaturas, **girar**, **excluir**, **desfazer/refazer**.
- **Extrair** as páginas selecionadas e **dividir** por intervalos (ex.: `1-3, 4, 5-8`).
- **Exportar** com numeração de páginas, marca d'água, compressão (sem perda ou reduzindo imagens), abertura rápida (linearização), remoção de metadados e senha AES-256.
- **Imprimir** e **ver metadados** dos arquivos de origem.
- **Impressora virtual** "ILoveFMTLY PDF": imprima de qualquer programa e o documento abre no app.

## Privacidade

- O arquivo original nunca é alterado. O app trabalha sobre cópias numa pasta temporária própria, apagada ao fechar.
- `core/offline.py` substitui as funções de rede do Python na inicialização; qualquer tentativa de conexão falha.
- A opção "Remover metadados" vem marcada por padrão.

## Rodando

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Também é possível abrir arquivos direto: `.venv\Scripts\python app.py contrato.pdf`.

## Impressora virtual

Execute uma vez, como administrador:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_printer.ps1
```

A impressora usa o driver nativo "Microsoft Print To PDF" e grava em `%LOCALAPPDATA%\ILoveFMTLY\spool\`. Com o app aberto, a impressão aparece na hora; com o app fechado, é importada na próxima abertura. Para remover: o mesmo comando com `-Remove`.

## Testes

```bash
.venv\Scripts\python -m pytest
```

## Arquitetura

- `core/` — regra de negócio, sem Qt. `document.py` guarda o documento como lista de referências a páginas (`PageRef`), por isso juntar, girar e reordenar são instantâneos e o desfazer é simples; o PDF real só é gravado na exportação.
- `core/engines/mupdf.py` — PyMuPDF: renderização, montagem, numeração, marca d'água, compressão de imagens.
- `core/engines/qpdf.py` — pikepdf (qpdf): reparo, senha, compressão sem perda, linearização, metadados.
- `ui/` — interface PySide6.

Spec e plano: `docs/superpowers/`.

## Licenças

PyMuPDF é distribuído sob AGPL-3.0. Para uso pessoal não há restrição; distribuir o aplicativo exige publicar o código sob AGPL ou obter licença comercial da Artifex. pikepdf (MPL-2.0) e PySide6 (LGPL-3.0) são permissivas para este uso.
