# Changelog

Todas as mudanças importantes da skin Xbox Series ficam registradas aqui.

## [2.0.0] - 2026-10-26

### Adicionado
- Versões em **inglês** (`XboxSeries-EN.xzp`) e **espanhol** (`XboxSeries-ES.xzp`), com os textos das telas, os rótulos das imagens e o nome da skin traduzidos.
- **Relógio de 24 h** na tela inicial, em negrito, nos dois layouts. O `Main.lua` grava a hora de abertura e o shader das capas desenha HH:MM.
- **Telas internas da Clean NXE** (Jayshai) com a identidade Xbox Series: painéis pretos sólidos, foco em pílula clara com texto escuro, barras em verde-limão sólido, fonte Inter e textos 25% menores (títulos e listas do gerenciador de arquivos e do seletor de skins um pouco mais).
- Prévia da skin no seletor do Aurora com a tela inicial do projeto.
- Leitor/gravador de telas `.xur` (`xur5.py`) e `merge_nxe.py`; `tools/build.sh` gera a versão final.

### Mantido da 1.0
- Tela inicial, detalhes do jogo (lista "Ações"), abertura, fundo desfocado e layouts de capas.

## [1.0.0] - 2026-10-25

### Adicionado
- Primeira versão da skin **Xbox Series** (`XboxSeries.xzp`) para Aurora 0.7b, baseada na Liquid Glass 1.0.0.
- Layout de capas **Xbox Series** (`Xbox Series.cfljson`): capa selecionada maior à esquerda, com borda verde, e a fileira seguindo à direita.
- Tela inicial no estilo da dashboard de 2026: perfil com gamerscore no canto superior esquerdo, dicas de botão no centro, hora grande em negrito alinhada à direita e foco verde-limão.
- Moldura com degradês nas bordas, para a arte de cada jogo aparecer em tela cheia.
- Papel de parede padrão preto com brilho verde, usado quando o jogo não tem fundo.
- Tela de abertura (splash) com o logo do Xbox em verde sobre fundo preto. Ela usa uma imagem própria, separada do papel de parede da Home.
- Tela de detalhes do jogo redesenhada no estilo Xbox Series, com rótulos em pt-BR.
- 351 peças e ícones recoloridos (configurações, listas, botões, caixas de texto, gerenciador de arquivos, Visão Rápida, conquistas, atualizações, trainers, dispositivos): grafite, foco branco, verde Xbox e cantos de 4 px.
- Tradução completa para português do Brasil.

### Ajustado após o teste no console
- Fundo: capa do jogo ampliada e desfocada (pelo shader das capas), na Home e nos detalhes; layout alternativo "Xbox Series - Fundo do Jogo".
- Fundo padrão do Aurora trocado pelo escuro da skin (antes era o borrão colorido da Liquid Glass).
- Painéis e véus mais opacos e neutros; bordas de vidro quase invisíveis; textos 15% menores nas telas internas.
- Botão Detalhes sólido e mais largo; área da hora/status maior.

### Removido
- Capa "hero" grande na Home e cápsula inferior de botões da Liquid Glass.
