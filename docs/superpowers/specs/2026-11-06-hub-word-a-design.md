# ILoveFMTLY — Subprojeto 2: hub de blocos + Word nível A (design)

Data: 2026-11-06

## Objetivo

1. Tela inicial em grade de blocos de ferramentas, agrupados por categoria, com visual próprio na paleta escolhida pelo usuário.
2. Ao soltar um arquivo no hub, uma camada sobe por cima mostrando só os blocos compatíveis com aquele formato.
3. Word nível A: Word para PDF e PDF para Word, usando o Microsoft Word instalado via COM, totalmente local.
4. Novo bloco PDF para imagem.

Os níveis B (ajustes no DOCX sem o Word) e C (visualizar e editar DOCX no app) ficam para entregas seguintes.

## Restrições globais

- Sem rede: continua valendo o bloqueio de `core/offline.py`.
- Word via COM com `pywin32`: instância própria e invisível; documento aberto como somente leitura e fora da lista de recentes; macros desativadas (`AutomationSecurity = 3`); PDF exportado sem propriedades do documento (`IncludeDocProps=False`); tempo limite que encerra apenas a instância aberta pelo app.
- O aviso modal do Word ao abrir PDF (`DisableConvertPdfWarning`) é desligado só durante a conversão e o valor anterior do usuário é restaurado.
- Sem Word instalado, os blocos de Word aparecem desativados com o texto "Requer Microsoft Word".
- Ferramentas que dependem de internet ou IA na nuvem não entram no hub (resumo por IA, tradução, HTML por URL, digitalização pelo celular).

## Paleta

| Token | Cor | Uso |
|---|---|---|
| bg | `#181A2F` | fundo da janela |
| surface | `#242E49` | cartões, barras, painéis |
| border | `#37415C` | bordas, hover, campos |
| accent | `#FDA481` | destaque, foco, botão principal |
| danger | `#B4182D` | seleção, perigo |
| wine | `#54162B` | detalhes, ícones secundários |

Texto principal `#F3F4F8`, texto secundário `#AEB4C8`.

## Blocos

| Grupo | Blocos (prontos) | Aceita |
|---|---|---|
| Organizar | Juntar PDF, Dividir PDF, Organizar páginas, Girar PDF, Extrair páginas | PDF (Juntar e Organizar aceitam imagens) |
| Otimizar | Comprimir PDF, Reparar PDF | PDF |
| Converter | Word para PDF, PDF para Word, Imagem para PDF, PDF para imagem | conforme o bloco |
| Editar | Numerar páginas, Marca d'água | PDF |
| Segurança | Proteger PDF, Desbloquear PDF, Remover metadados | PDF |
| Em breve | Assinar, Tarja, Editar PDF, Formulários, OCR, Comparar, Recortar, PDF/A | desativados |

Ao abrir um bloco de PDF, o editor existente é aberto com o arquivo carregado e a opção correspondente já preparada (por exemplo, Numerar páginas já marca a numeração; Proteger PDF foca o campo de senha; Dividir abre o diálogo de intervalos).

## GIF de tema

Arquivo opcional `assets/tema.gif`, exibido com 10×10 px no canto inferior direito (última posição da barra de status). Sem o arquivo, nada aparece.

## Testes

Motor Word com testes reais marcados para pular quando o Word não está instalado, incluindo o tempo limite. Hub testado com pytest-qt: grade de blocos, camada de compatíveis ao soltar arquivo, abertura de cada tipo de bloco.
