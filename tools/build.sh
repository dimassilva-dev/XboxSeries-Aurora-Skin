#!/bin/zsh
# Gera a skin Xbox Series 2.0 (Home Xbox Series + menus baseados na Clean NXE + relógio) e os dois layouts.
# Precisa de Python 3 com Pillow e numpy (pip install pillow numpy).
# uso: cd XboxSeries-Aurora-Skin && zsh tools/build.sh
set -e
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
TMP=$(mktemp -d)
$PY tools/scripts/layout.py "tools/base/Liquid Glass.cfljson" "Aurora/Media/Layouts/Xbox Series.cfljson"
$PY tools/scripts/layout.py "tools/base/Liquid Glass.cfljson" "Aurora/Media/Layouts/Xbox Series - Fundo do Jogo.cfljson" jogo
# 1) Home, detalhes, abertura e relógio (a partir da Liquid Glass traduzida)
XBOX_CLOCK=1 $PY tools/scripts/xbox.py tools/base/LiquidGlass-ptbr.xzp "$TMP/home.xzp" tools/build-input/art tools/build-input/pecas
# 2) menus internos da Clean NXE com a identidade Xbox Series
$PY tools/scripts/merge_nxe.py tools/base/CleanNXE-2.0.1.xzp "$TMP/home.xzp" Aurora/Skins/XboxSeries.xzp
# 3) versões em inglês e espanhol (textos das telas, rótulos das imagens e nome da skin)
$PY tools/scripts/i18n.py Aurora/Skins/XboxSeries.xzp Aurora/Skins/XboxSeries-EN.xzp en
$PY tools/scripts/i18n.py Aurora/Skins/XboxSeries.xzp Aurora/Skins/XboxSeries-ES.xzp es
rm -rf "$TMP"
ls -l Aurora/Skins/
