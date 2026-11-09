# ILoveFMTLY — Subprojeto 3: Word B, Imagens e Vídeo para GIF (design)

Data: 2026-11-06 · Base: `referencias.md` (Claude Doc) e `DESIGN.md`.

## Objetivo

Três fases, cada uma com testes e commit próprio, todas sem Office e sem rede:

1. **Word B** — ajustes em DOCX sem abrir o Word.
2. **Imagens** — recortar, girar/espelhar, remover EXIF/GPS, marca d'água, editar GIF, borrar área.
3. **Vídeo para GIF** — prévia com barra de trecho, FPS, largura, tamanho estimado; saída GIF ou WebP animado.

## Restrições globais

- `core/` sem Qt. Original nunca alterado: saída sempre em arquivo novo.
- Visual segue `DESIGN.md` (direção technical, Plex Sans/Mono, sem caixas nos diálogos novos).
- Bibliotecas novas (todas permissivas): `python-docx` (MIT), `docxcompose` (MIT), `mammoth` (BSD-2),
  `markdownify` (MIT), `av`/PyAV (BSD-3; inclui FFmpeg LGPL).
- `Tool.fn` aceita nome qualificado (`docx_tools.clean`) para funções fora de `core.convert`.
- `Param` ganha tipos texto (`default` str sem `options`) e sim/não (`default` bool).

## Fase 1 — Word B (`core/docx_tools.py`, grupo "Word")

| Bloco | Função | Modo | Saída |
|---|---|---|---|
| Limpar DOCX | `clean(files, out)` | folder | `<nome>_limpo.docx` |
| Localizar e substituir | `replace(files, out, find, replace, match_case)` | folder | `<nome>_substituido.docx` |
| Juntar DOCX | `merge(files, out)` | file | `.docx` |
| DOCX para TXT / Markdown / HTML | `export_text(files, out, fmt)` | folder | `<nome>.txt/.md/.html` + `<nome>_imagens/` |

- **Limpar**: aceita revisões (`w:ins`/`w:moveTo` desembrulhados; `w:del`/`w:moveFrom` e `*PrChange` removidos),
  remove comentários (marcas, referências e partes `comments*.xml`), zera autor/empresa/datas em `docProps`,
  remove `docProps/custom.xml`, remove `w:rsid*`, liga `w:removePersonalInformation`. Vale para corpo,
  cabeçalhos, rodapés e notas.
- **Substituir**: acha o texto mesmo dividido em várias `w:r` com formatos diferentes; o texto novo herda o
  formato do primeiro pedaço. Vale para corpo, tabelas, cabeçalhos, rodapés e notas.
- **Juntar**: `docxcompose` (estilos, numeração, imagens).
- **Exportar**: `mammoth` → HTML; `markdownify` → Markdown; TXT por parágrafos (`python-docx`).
- Erros: DOCX com senha (contêiner OLE) ou ZIP inválido → `DocxError` com mensagem clara; nada gravado.

## Fase 2 — Imagens (`core/images.py`)

| Bloco | Modo |
|---|---|
| Recortar | dialog (`ui/crop_dialog.py`): retângulo arrastável, proporção livre/1:1/4:3/16:9 |
| Girar / espelhar | folder, param `ação` |
| Remover EXIF/GPS | folder; aplica a orientação EXIF antes de remover |
| Marca d'água em imagem | folder; texto, posição, opacidade |
| Borrar área | dialog (reusa o recorte): pixelar o retângulo |
| Editar GIF | file; velocidade %, de/até quadro, largura, inverter, salvar como GIF ou WebP |

## Fase 3 — Vídeo para GIF (`core/video.py`, `ui/video_gif_dialog.py`)

- PyAV decodifica só o quadro pedido (prévia) e o trecho escolhido (exportação).
- Diálogo: prévia, trilha com alças in/out, play, FPS (padrão 10), largura (padrão 480), formato GIF/WebP.
- Linha de estado em Mono: `TRECHO 00:12.40 → 00:18.00 · 5,6 s · 56 quadros · ≈ 3,1 MB`.
- GIF com paleta adaptativa por quadro; vídeo sem codec suportado → aviso.

## Testes

- Arquivos de teste gerados no próprio teste (DOCX com `python-docx` + XML de revisão/comentário; imagens com
  Pillow; vídeo com PyAV).
- UI (pytest-qt): blocos novos no hub, camada de soltar arquivos, `ParamDialog` com texto e sim/não, diálogos
  novos seguindo `DESIGN.md` (sem `QGroupBox`, uma ação `primary`, valores em `role="mono"`).
