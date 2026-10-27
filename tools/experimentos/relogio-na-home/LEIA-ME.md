# Relógio na tela inicial (experimental)

**Versão 3 (atual):** os algarismos são a própria **Inter Bold**, desenhada num atlas que fica no lugar das texturas
de estojo (`Textures\Coverflow.xpr`; o estojo nunca aparece nesta skin). O estojo da capa central vira um retângulo
no canto superior direito e o shader só copia os algarismos: uma leitura de textura por pixel, sem arcos nem `atan2`.
Veja `comparacao-fonte.png` (esquerda: protótipo; direita: simulação do shader com o atlas).

Histórico: v1 (arcos/atan2) travou o Aurora na abertura; v2 (traços retos) nunca foi testada.

## Como testar (tenha o XeXMenu à mão para desfazer)

1. Copie `XboxSeries-com-relogio.xzp` para `Aurora/Skins/XboxSeries.xzp`.
2. Copie `Main.lua` desta pasta para `Aurora/User/Scripts/Main.lua` (guarde o seu original; o deste console está em `Main.lua.original`).
3. No Aurora: Configurações → Segurança → Scripts → marque **"Executar Main.lua ao iniciar"**.
4. Use o layout **"Xbox Series"** ou **"Xbox Series - Fundo do Jogo"** (o relógio aparece nos dois) e reinicie o Aurora.

A hora vem do relógio do console: confira o fuso em Configurações do sistema → Console → Relógio.
Com layouts de capas de outras skins o estojo das capas mostraria o atlas; use os layouts Xbox Series.

## Se travar na abertura

Abra o XeXMenu (FTP `xbox`/`xbox`) e volte `Aurora/Skins/XboxSeries.xzp` para a versão normal
(`Aurora/Skins/XboxSeries.xzp` da raiz do projeto) e o `Main.lua` para o seu original.

## Gerar de novo

Precisa de Python com Pillow e numpy (`pip install pillow numpy`):
```
XBOX_CLOCK=1 python3 tools/scripts/xbox.py tools/base/LiquidGlass-ptbr.xzp saida.xzp tools/build-input/art tools/build-input/pecas
```
Atlas: `tools/scripts/clockatlas.py` (fonte `tools/build-input/Inter-Bold.ttf`). Shader e posições: bloco `ENABLE_CLOCK` em `tools/scripts/xbox.py`.
