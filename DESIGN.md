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

Padrão: IBM Plex Sans. A pessoa pode trocar a fonte do texto em Configurações
(`FONTS` em `ui/theme.py`: Plex Sans, Plex Mono, Segoe UI, Arial, Verdana, Georgia);
o código nunca escolhe outra fonte por conta própria.

Tamanho do texto (Configurações): Pequeno 0,9 · Normal 1 · Grande 1,15 · Muito grande 1,3
sobre a escala acima (`TEXT_SIZES`). As alturas dos blocos crescem junto.

## Cores

Cada tema em `THEMES` (`ui/theme.py`) define todos os tokens de `Color`; trocar ou
criar tema é editar só esse dicionário (`test_themes_complete` cobra as chaves).
Temas: **Padrão escuro** e **Padrão claro** (padrão; Medium Slate Blue `#6666FF`, Periwinkle,
Columbia Blue, Rich Black `#0C0C16`, Celadon), **Tema Claude** (o antigo Noite, em tons de
entardecer; a tabela abaixo é a paleta original dele), **Umbra & Dreamless Sleep**, **Soft Spectrum**,
**Soft Ambar**, **Claro**, **Alto contraste** e **Amarelo**. `THEME_ALIASES` leva nomes antigos
salvos ("Noite") ao tema novo.

Easter egg: o bichinho do Claude (pixel art, `assets/icons/clawd.svg`) fica dentro da busca;
clicar nele troca a dica. Tema, fonte e
tamanho valem ao reabrir o app (`apply_appearance()` roda antes da janela existir).
Sem gradiente. Sem cor fora do tema. Exceção: `INK`/`PAPER` da assinatura, que vão para
o PDF e não mudam com o tema.

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

## Raios

`Radius`: XS 3 (scrollbar, trilho) · SM 5 (checkbox) · MD 12 (botões, campos, glifo) ·
LG 18 (cartões, busca) · XL 24 (painel da camada, blocos grandes). Nada de raio solto no código.

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

Mascotes extras (Configurações › Mascote): raposa, coruja, tartaruga e castor, no mesmo estilo
(quadrado `BG` com borda `BORDER`, figura chapada, coração `DANGER`), gerados por `scripts/mascotes.py`
em `assets/mascotes/`. Trocar o mascote muda na hora o ícone da janela, da barra de tarefas, da bandeja,
dos atalhos (área de trabalho, menu Iniciar, fixado na barra) e o logo do topo (`core/mascot.py`).

## Cor por tipo de arquivo

Tokens `FILE_*` / `ON_FILE_*` em cada tema: PDF vermelho, Word azul ciano suave, CSV/Excel verde,
dev (fmtly) cinza visível, imagem e o resto branco. Usados nos blocos grandes (`CATEGORY_GROUP`)
e nos grupos Word, Imagens, CSV e de dev (`GROUP_GLYPH`).

### Relação de cores (tonal)

Cada grupo de ferramenta herda a cor do seu tipo de arquivo (`KIND_OF_GROUP`): o ícone do card é
uma tinta (`TINT` = 22 % da cor do tipo sobre `SURFACE`) com o símbolo na cor cheia, ajustado por
`readable()` até 3:1. O bloco grande da categoria usa a cor cheia. Resultado: PDF é vermelho do bloco
ao card, Word azul, CSV verde, dev cinza, imagem branca. Fundo que some no card (contraste < 1,5,
ex.: branco em tema claro) ganha contorno `BORDER`. `test_every_theme_glyph_is_readable` cobra o
mínimo de 3:1 em todos os temas. Perigo (`DANGER`) fica afastado do destaque em matiz ou em brilho.

## Telas iniciais

- **Simples** (padrão): saudação "Olá, {nome}!", favoritas do perfil (`SUAS FERRAMENTAS`)
  e um bloco grande por tipo de arquivo (`CATEGORIES` em `ui/tools.py`): círculo de
  56 px com ícone de 28 px, título 15 pt, contagem em Mono. Clicar abre a página da
  categoria (só aquelas ferramentas, com busca e "Voltar").
- **Simples com barra lateral** (padrão, `layout="sidebar"`): barra lateral na cor `ACCENT` (raio XL)
  com um ícone por tipo de arquivo; abas dos grupos com sublinhado `ACCENT` de 3 px; grade em painel
  `SURFACE`; à direita, o detalhe (círculo na cor do tipo, título 15 pt, **Abrir ferramenta** e
  Favoritar). O início mostra só os favoritos; embaixo, as RECOMENDAÇÕES (sugestões do perfil que
  ainda não são favoritas; desliga em Configurações). Um clique seleciona, duplo clique abre.
- **Detalhado**: todas as ferramentas por grupo, com busca.
- O botão "Trocar para detalhado / simples" grava a escolha no `config.json`.

## Cadastro

"Como devo te chamar?" + um cartão por perfil (`PROFILES`): faixa de 4 px na cor do
perfil, círculo com ícone, título, *Objetivo*, *Ideal para*, *Já vem com*. Selecionado =
borda `ACCENT` 2 px. Aparece na primeira vez; depois, em Configurações.

## Padrões dos diálogos novos

- **Recorte:** fora da área = `BG` a 70 %; borda `ACCENT` 2 px; alças 8 px.
  Proporções: livre, 1:1, 4:3, 16:9. Medida em Mono: `1280 × 720 px`.
- **Vídeo para GIF:** trilha fina `BORDER`, trecho em `WINE`, alças `ACCENT`.
  Linha de estado em Mono:
  `TRECHO 00:12.40 → 00:18.00 · 5,6 s · 56 quadros · ≈ 3,1 MB`.
  Ação única: **Gerar GIF**.
- **Assinar PDF:** área de desenho em `PAPER` com traço `INK` de 3 px; página
  (0 = última), posição e tamanho em % da largura. Ação única: **Assinar**.
- **Preencher formulário:** um campo por linha, contagem em Mono, opção "Deixar fixo".
  Ação única: **Preencher**.

- **Ferramentas de dev:** entrada à esquerda em Mono, opções abaixo, saída à direita;
  roda sozinha ao digitar (300 ms), erro em `tone="error"` acima da saída. Ações: Copiar, Salvar, **Rodar**.

## Texto

Português do Brasil, verbo no imperativo nos botões ("Gerar GIF", "Substituir em 3 arquivos").
Conteúdo real nos exemplos e testes, nunca "Lorem ipsum".
