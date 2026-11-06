# ILoveFMTLY — Subprojeto 1: PDF v1 (design)

Data: 2026-11-06

## Objetivo

Aplicativo desktop nativo para Windows que ajusta documentos sensíveis sem nunca enviá-los a um servidor. Esta é a primeira entrega, focada em PDF (escopo A: operações de página), com arquitetura preparada para anotações (B) e edição de texto (C) no futuro.

Roadmap de subprojetos, nesta ordem: 1. PDF, 2. Word, 3. Excel, 4. CSV, 5. demais formatos, e depois o conjunto de ferramentas Dev (inspirado no fmtly.dev).

## Restrições globais

- Python 3.12 ou superior (desenvolvido em 3.14).
- Interface em PySide6 (Qt). Motor principal de PDF: PyMuPDF (`import pymupdf`). Motor estrutural: pikepdf (qpdf).
- Licença: PyMuPDF é AGPL. Uso pessoal sem restrição; distribuição exige código aberto AGPL ou licença comercial.
- Zero tráfego de rede: a aplicação bloqueia `socket` na inicialização e não tem telemetria nem verificação de atualizações.
- O arquivo original importado nunca é modificado.
- Arquivos de trabalho ficam em um workspace temporário próprio, apagado ao fechar a aplicação.
- `core/` não importa Qt; `ui/` só consome `core/`.
- Textos da interface em português do Brasil.

## Divisão de bibliotecas

| Tarefa | Biblioteca |
|---|---|
| Renderizar páginas, miniaturas, impressão | PyMuPDF |
| Montar documento (juntar, reordenar, girar, excluir, extrair) | PyMuPDF (`insert_pdf`) |
| Imagens para PDF | PyMuPDF |
| Numeração de páginas e marca d'água | PyMuPDF |
| Compressão com perda (reduzir imagens) | PyMuPDF (`rewrite_images`) |
| Reparo de PDF corrompido | pikepdf |
| Senha AES-256 com permissões, e remoção de senha | pikepdf |
| Compressão sem perda (object streams, recompressão flate) e linearização | pikepdf |
| Metadados (ver e limpar Info e XMP) | pikepdf |

## Arquitetura

```
app.py                 ponto de entrada
core/
  offline.py           bloqueio de rede
  workspace.py         pasta temporária da sessão
  document.py          modelo de páginas virtual (PageRef, Document)
  history.py           desfazer/refazer de estados do Document
  engines/mupdf.py     render, montagem, imagens, numeração, marca d'água, compressão com perda
  engines/qpdf.py      reparo, senha, compressão sem perda, linearização, metadados
  export.py            grava o Document em PDF aplicando opções de saída
  printer.py           pasta de spool da impressora virtual
ui/                    janela principal, miniaturas, visualizador, painéis de ferramentas
scripts/setup_printer.ps1   instala a impressora virtual (admin, uma vez)
tests/                 pytest
```

## Fluxo de dados (edição não destrutiva)

1. Importar: o arquivo é copiado para o workspace. Imagens são convertidas em PDF de uma página por imagem. PDFs que falham ao abrir passam pelo reparo do pikepdf; PDFs com senha pedem a senha.
2. O `Document` é uma lista de `PageRef(source, index, rotation)`. Juntar, reordenar, girar, excluir e extrair alteram só essa lista. Cada alteração empilha o estado anterior no histórico.
3. Exportar: PyMuPDF monta o PDF a partir dos `PageRef` e aplica numeração e marca d'água. Em seguida o pikepdf aplica compressão sem perda, linearização, limpeza de metadados e senha, conforme as opções escolhidas.
4. Dividir gera vários arquivos, um por intervalo de páginas.

Extensão futura: anotações (B) entram como uma lista opcional por `PageRef`; edição de texto (C) entra como uma operação que gera uma nova origem.

## Operações da v1

Importar (PDF e imagens), visualizar com zoom, juntar, dividir por intervalos, extrair páginas selecionadas, reordenar por arrastar, girar, excluir, comprimir (sem perda e com perda), numerar páginas, marca d'água de texto, proteger com senha, remover senha, reparar, imprimir, ver e limpar metadados, desfazer e refazer.

## Impressora virtual

O script `scripts/setup_printer.ps1` cria uma porta local que grava em `%LOCALAPPDATA%\ILoveFMTLY\spool\print.pdf` e uma impressora "ILoveFMTLY PDF" com o driver "Microsoft Print To PDF". Com a aplicação aberta, um `QFileSystemWatcher` detecta o arquivo, move-o para o workspace com nome único e o abre. Com a aplicação fechada, o arquivo é importado na próxima abertura.

## Erros

- PDF corrompido: tentar reparo; se falhar, mensagem clara e o arquivo não é importado.
- Senha incorreta: pedir de novo, com opção de cancelar.
- Operações longas rodam fora da thread da interface, com indicação de progresso.
- Intervalos de páginas inválidos (por exemplo "5-2" ou páginas fora do documento) geram erro de validação antes de qualquer gravação.

## Testes

pytest no `core/` com PDFs gerados em fixtures; smoke test da janela com pytest-qt; teste que garante que a aplicação não consegue abrir sockets após `offline.enable()`.

## Interface

Barra lateral com ferramentas, área central com grade de miniaturas (arrastar para reordenar) e visualizador com zoom, painel de opções da ferramenta e área de soltar arquivos. O refinamento visual será feito com o Claude Design depois da v1 funcional.
