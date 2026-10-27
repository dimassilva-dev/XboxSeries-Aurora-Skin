"""Gera o layout de capas Xbox Series a partir do Liquid Glass.
Com a câmera em z=-7.75 o shader posiciona as capas em pixels: x*100, -y*100."""
import json, sys
src, dst = sys.argv[1:3]
# 3o argumento "jogo": usa o fundo do próprio jogo (sem a capa desfocada)
GAME_BG = len(sys.argv) > 3 and sys.argv[3] == "jogo"
L = json.load(open(src))
FACE_H, FACE_W = 0.9766, 0.6914          # face da capa no mesh (PG_RECT)
BOTTOM = 536                              # base da fileira (px)
FOCUS_H, ROW_H = 230, 170                 # altura da capa selecionada / demais
GAP = 15
sf = FOCUS_H / (FACE_H * 100); sr = ROW_H / (FACE_H * 100)
ax = 1.79346 / 1.78169                    # proporção x/y original da escala
fw = FACE_W * sf * 100; rw = FACE_W * sr * 100
cx = 64 + fw / 2                          # borda esquerda da selecionada em x=64
rx = 64 + fw + GAP + rw / 2
step = rw + GAP
cy = -(BOTTOM - FOCUS_H / 2) / 100; ry = -(BOTTOM - ROW_H / 2) / 100
shift = {'Initial': -0.9, 'Refresh': -3.2}
L['info']['name'] = 'Xbox Series - Fundo do Jogo' if GAME_BG else 'Xbox Series'; L['info']['author'] = 'Xbox Series skin'
for m in L['modes']:
    # o passe de reflexo desenha a capa central desfocada em tela cheia (ver CoverflowShader.fx)
    # no "Fundo do Jogo" o passe também fica ligado, mas só desenha o relógio: a hora marcada com +30 avisa o shader
    m['mirror']['enabled'] = True
    if GAME_BG:
        m['light']['attenuation'] = [30.0, -1.0, 0.0]
    if m['name'] == 'Flipped':            # tela de detalhes do jogo: mantém
        continue
    c = m['covers']; dy = shift.get(m['name'], 0.0); z = c['position']['center'][2]
    c['scale']['center'] = [round(sf * ax, 5), round(sf, 5), 1.0]
    c['scale']['left'] = c['scale']['right'] = [round(sr * ax, 5), round(sr, 5), 1.0]
    c['position']['center'] = [round(cx / 100, 4), round(cy + dy, 4), z]
    c['position']['right'] = [round(rx / 100, 4), round(ry + dy, 4), z]
    c['position']['left'] = [-3.0, round(ry + dy, 4), z]      # capas anteriores ficam fora da tela
    c['spacer']['right'] = [round(step / 100, 4), 0.0, 0.0]
    c['spacer']['left'] = [-round(step / 100, 4), 0.0, 0.0]
L['properties']['columns'] = 19      # ~9 por lado; à direita cabem 8 visíveis
json.dump(L, open(dst, 'w'), indent=2)
print('focus', round(fw), 'x', FOCUS_H, 'center px', round(cx), BOTTOM - FOCUS_H / 2, '| row', round(rw), 'x', ROW_H, 'first', round(rx), 'step', round(step))
