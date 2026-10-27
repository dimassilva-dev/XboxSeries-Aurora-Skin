import sys, math
from PIL import Image, ImageFilter
out = sys.argv[1]; fontdir = sys.argv[2]
W, H = 1280, 720

def vgrad(h, a0, a1, ease=1.6):
    return [int(round(a0 + (a1 - a0) * (t / max(h-1, 1)) ** ease)) for t in range(h)]

# ---------------- HomeChrome: só sombra/escurecimento, o centro fica livre para a arte do jogo
A = Image.new('L', (W, H), 0); px = A.load()
top = vgrad(170, 150, 0, 0.8)          # faixa superior para a barra de perfil/ícones/hora
for y in range(H):
    t = top[y] if y < 170 else 0
    if y >= 260:                         # escurece de baixo para cima atrás das capas e do título
        u = (y - 260) / (H - 260)
        bt = int(235 * (u ** 1.35))
    else:
        bt = 0
    for x in range(W):
        lv = int(70 * max(0.0, 1 - x / 620) ** 1.5) if y > 200 else 0   # vinheta à esquerda p/ legibilidade
        a = 255 - (255 - t) * (255 - bt) * (255 - lv) // (255 * 255)
        px[x, y] = a
rgb = Image.new('RGB', (W, H), (3, 6, 8))
chrome = Image.merge('RGBA', (*rgb.split(), A))

chrome.save(out + '/HomeChrome.png')

# ---------------- Ground: fundo reserva estilo Xbox (preto com brilho verde)
g = Image.new('RGB', (W, H), (4, 7, 6)); gp = g.load()
for y in range(H):
    for x in range(W):
        dx = (x - 860) / 900; dy = (y - 140) / 520
        r = math.sqrt(dx * dx + dy * dy)
        k = max(0.0, 1 - r) ** 2.2
        dx2 = (x - 180) / 700; dy2 = (y - 760) / 420
        k2 = max(0.0, 1 - math.sqrt(dx2 * dx2 + dy2 * dy2)) ** 2.5
        gp[x, y] = (int(4 + 10 * k + 4 * k2), int(7 + 70 * k + 22 * k2), int(6 + 22 * k + 8 * k2))
g = g.filter(ImageFilter.GaussianBlur(2))
g.save(out + '/Ground.png')
