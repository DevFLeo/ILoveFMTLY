# DESIGN.md — ILoveFMTLY

Regras visuais do app. Os valores vivem em `ui/theme.py`; o QSS em `ui/style.py`
lê de lá. `tests/test_design_system.py` e `tests/test_icons_fonts.py` cobram
estas regras.

## Direção: technical

Parece instrumento de bancada, não site. Dados aparecem crus e exatos: tempo
`00:12.40`, tamanho `≈ 3,1 MB`, medida `1920 × 1080`, contagem `41 trocas`.
Uma ação principal por tela. Nada decorativo que não informe algo.

## Fontes

Embutidas em `assets/fonts/` (OFL, ver `OFL.txt`) e registradas em
`ui/style.load_fonts()`. Funcionam offline e dentro do .exe.

| Uso | Família | Pesos |
|---|---|---|
| Texto, títulos, botões | IBM Plex Sans (`Type.SANS`) | 400, 600, 700 |
| Números, tempos, tamanhos, medidas, rótulos de seção | IBM Plex Mono (`Type.MONO`) | 400, 600 |

Escala (pt): 9 legenda · 10 corpo · 11 título de cartão · 20 título de tela.

Proibido: Inter, Roboto, Segoe UI ou qualquer fonte do sistema como fonte de texto.

## Cores

Só a paleta abaixo e os derivados já definidos em `Color`. Sem gradiente. Sem cor nova.

| Token | Cor | Uso |
|---|---|---|
| `BG` | `#181A2F` | fundo |
| `SURFACE` | `#242E49` | barras, cartões, painéis |
| `BORDER` | `#37415C` | só linha fina de campo editável e trilhas |
| `ACCENT` | `#FDA481` | ação principal, foco, alças (recorte, in/out) |
| `WINE` | `#54162B` | seleção, faixa marcada (trecho do vídeo) |
| `DANGER` | `#B4182D` | só erro e perigo |
| `TEXT` / `TEXT_MUTED` | `#F3F4F8` / `#AEB4C8` | texto principal / secundário |

Nenhum hex fora de `ui/theme.py` (teste `test_no_hex_outside_theme`).

## Hierarquia

Vem de tipo e espaço, não de caixas.

- Diálogos novos: sem `QGroupBox`, sem caixa dentro de caixa.
- Seção = rótulo `role="section"` (Mono, 9 pt, maiúsculas, espaçado) + 24 a 32 px de espaço.
- Borda só em campo editável.
- Valores técnicos usam `role="mono"`.
- Uma ação principal por diálogo, com `variant="primary"`; o resto é `ghost`.

Hub e editor antigos ainda usam cartões; mudam só se for pedido.

## Ícones

SVG da Lucide (ISC) em `assets/icons/`, desenhados com `ui/icons.svg_icon()` /
`svg_pixmap()`, que trocam `currentColor` pelo token pedido. Cada `Tool` declara
`icon` (nome do arquivo sem `.svg`). Não usar glifos Unicode como ícone.

Bloco do hub: quadrado de 36 px na cor de fundo do grupo (`GROUP_GLYPH`),
ícone de 20 px na cor de frente do grupo.

## Mascote

A folha com dobra vermelha, olhos, bochechas e um coração (o "I love").
`assets/logo.png` (1024 px) e `assets/app.ico` (16 a 256 px, ícone do .exe e da janela)
saem de `scripts/mascote.py`; para mudar o desenho, edite o script e rode de novo.
No hub aparece com 56 px (`Size.LOGO`) ao lado do título.

## Padrões dos diálogos novos

- **Recorte:** fora da área = `BG` a 70 %; borda `ACCENT` 2 px; alças 8 px.
  Proporções: livre, 1:1, 4:3, 16:9. Medida em Mono: `1280 × 720 px`.
- **Vídeo para GIF:** trilha fina `BORDER`, trecho em `WINE`, alças `ACCENT`.
  Linha de estado em Mono:
  `TRECHO 00:12.40 → 00:18.00 · 5,6 s · 56 quadros · ≈ 3,1 MB`.
  Ação única: **Gerar GIF**.

## Texto

Português do Brasil, verbo no imperativo nos botões ("Gerar GIF", "Substituir em 3 arquivos").
Conteúdo real nos exemplos e testes, nunca "Lorem ipsum".
