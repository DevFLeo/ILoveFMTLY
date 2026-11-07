<img src="assets/logo.png" width="96" alt="Mascote do ILoveFMTLY">

# ILoveFMTLY

Aplicativo desktop para Windows que ajusta documentos sensíveis **sem enviá-los a nenhum servidor**. Tudo roda na própria máquina: a aplicação bloqueia o acesso à rede ao iniciar e não tem telemetria nem verificação de atualizações.

Próximos módulos, em ordem: ajustes em Word sem abrir o Word, visualizador de DOCX, Excel, CSV e, por fim, as ferramentas de desenvolvedor (JSON, YAML, XML, encode, hash...).

## Tela inicial: o canivete suíço

Na primeira vez, o app pergunta **como devo te chamar** e o **perfil** (Pessoal, Estudante, Instituição, Empresa). O perfil define as ferramentas que aparecem primeiro.

A tela inicial tem dois modos, com o botão **Trocar para detalhado / simples**:

- **Simples** (padrão): blocos grandes por tipo de arquivo (PDF, Word e Office, Imagens, Vídeo e GIF, Web e e-book). Clicar num bloco abre uma página só com as ferramentas daquele tipo.
- **Detalhado**: todas as ferramentas como blocos, por grupo, com busca.

Em **Configurações**: tema (Noite, Claro, Alto contraste), fonte, tamanho do texto, modo inicial e cadastro. Tudo fica num `config.json` pequeno, ao lado do `.exe` (ou na raiz do projeto, rodando pelo Python). Tema, fonte e tamanho valem ao reabrir o app.

Soltar arquivos em qualquer ponto dela abre uma camada com **só os blocos compatíveis** com aqueles arquivos. Todos os blocos funcionam pelo teclado (Tab, Enter, Espaço).

| Grupo | Ferramentas |
|---|---|
| Organizar | Juntar, Dividir, Organizar páginas, Girar, Extrair páginas, Recortar margens |
| Otimizar | Comprimir PDF, Reparar PDF, Escala de cinza |
| PDF para… | Word, Excel (tabelas), PowerPoint, imagem (PNG/JPG/WebP/TIFF...), GIF animado, TXT, HTML, SVG, Extrair imagens |
| …para PDF | Word, Excel, PowerPoint, imagem, HTML/Markdown/TXT, e-book (EPUB, MOBI, FB2, XPS, CBZ, SVG) |
| Word (sem Office) | Limpar DOCX (autor, comentários, revisões), Localizar e substituir, Juntar DOCX, DOCX para TXT/Markdown/HTML |
| Imagens | Converter formato, Redimensionar, Comprimir, Recortar, Girar/espelhar, Remover EXIF/GPS, Marca d'água (texto ou logo), Borrar área, Criar GIF, Editar GIF (velocidade, trecho, largura, inverter, WebP), Vídeo para GIF/WebP (prévia e trecho), GIF para quadros |
| Editar | Numerar páginas, Marca d'água, Comparar dois PDFs, Assinar PDF (desenho ou imagem), Preencher formulário |
| Segurança | Proteger, Desbloquear, Remover metadados, Tarja (termos, CPF/CNPJ, e-mails e telefones; apaga de verdade) |
| Em breve | Editar PDF, OCR, PDF/A |

As conversões de e para Word, Excel e PowerPoint usam o **Microsoft Office instalado**, numa instância invisível, só leitura, com macros desativadas e tempo limite. Sem o Office, esses blocos aparecem desativados. O resto não depende de nada além do próprio app.

## Editor de PDF

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

## Gerar o .exe

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

Roda os testes e empacota com PyInstaller. Resultado: `dist\ILoveFMTLY\ILoveFMTLY.exe`; copie a pasta `dist\ILoveFMTLY` inteira para onde quiser. O .exe não precisa de Python instalado. Opções: `-OneFile` gera um único `dist\ILoveFMTLY.exe` (abre mais devagar, pois extrai tudo a cada execução); `-SkipTests` pula os testes.

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
