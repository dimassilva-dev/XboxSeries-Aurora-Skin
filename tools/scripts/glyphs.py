"""Ícones do controle no estilo Xbox Series (círculo grafite, aro claro, letra colorida).

uso: python glyphs.py <pasta_fontes> <saida>
Gera os mesmos nomes internos da skin (Images\\Visuals\\XuiGamepad\\..., DVDPanel, cta_*, pad_*).
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

SS = 8
# kit "Xbox buttons in components": A/B/X/Y chapados na cor do botão com letra escura;
# demais botões em cinza-claro com o símbolo escuro
FACE = {'A': (104, 162, 73), 'B': (198, 50, 46), 'X': (68, 152, 195), 'Y': (235, 213, 75)}
LIGHT = (216, 225, 243)
INK = (22, 22, 24, 255)
EDGE = (0, 0, 0, 150)


def font(fontdir, size):
    return ImageFont.truetype(os.path.join(fontdir, 'Fonts\\Inter-Bold.ttf'), size)


def shade(rgb, pressed):
    return tuple(int(v * 0.82) for v in rgb) + (255,) if pressed else tuple(rgb) + (255,)


def disc(size, rgb, pressed):
    s = size * SS
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    m = 1.0 * SS
    d.ellipse((m, m, s - m, s - m), fill=EDGE)
    m2 = m + 0.9 * SS * size / 32
    d.ellipse((m2, m2, s - m2, s - m2), fill=shade(rgb, pressed))
    return im, d


def letter(im, d, fontdir, ch, color=INK, scale=0.54):
    s = im.size[0]
    f = font(fontdir, int(s * scale))
    l, t, r, b = d.textbbox((0, 0), ch, font=f)
    d.text(((s - (r - l)) / 2 - l, (s - (b - t)) / 2 - t), ch, font=f, fill=color)


def finish(im, size, disabled):
    im = im.resize((size, size), Image.LANCZOS)
    if disabled:
        im.putalpha(im.getchannel('A').point(lambda v: int(v * 0.4)))
    return im


def face(fontdir, ch, size=32, pressed=False, disabled=False):
    im, d = disc(size, FACE[ch], pressed)
    letter(im, d, fontdir, ch)
    return finish(im, size, disabled)


def view_btn(size=32, pressed=False, disabled=False):
    im, d = disc(size, LIGHT, pressed); s = im.size[0]; u = s / 32; w = int(1.8 * u)
    d.rounded_rectangle((9.5 * u, 10.5 * u, 19.5 * u, 18 * u), radius=1.5 * u, outline=INK, width=w)
    d.rounded_rectangle((12.5 * u, 14 * u, 22.5 * u, 21.5 * u), radius=1.5 * u, fill=shade(LIGHT, pressed), outline=INK, width=w)
    return finish(im, size, disabled)


def menu_btn(size=32, pressed=False, disabled=False):
    im, d = disc(size, LIGHT, pressed); s = im.size[0]; u = s / 32
    for y in (11.5, 16, 20.5):
        d.rounded_rectangle((10 * u, (y - 1) * u, 22 * u, (y + 1) * u), radius=1 * u, fill=INK)
    return finish(im, size, disabled)


def thumb(fontdir, ch, size=32, pressed=False, disabled=False):
    im, d = disc(size, LIGHT, pressed); s = im.size[0]; u = s / 32
    d.ellipse((6 * u, 6 * u, 26 * u, 26 * u), outline=INK, width=int(1.6 * u))
    letter(im, d, fontdir, ch, scale=0.44)
    return finish(im, size, disabled)


def bumper(fontdir, side, size=32, pressed=False, disabled=False):
    s = size * SS; u = s / 32
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # formato do kit: topo arredondado, lado interno reto e inclinado
    if side == 'L':
        pts = [(4, 13), (9, 8.5), (29, 8.5), (27.5, 24), (3, 24)]
    else:
        pts = [(3, 8.5), (23, 8.5), (28, 13), (29, 24), (4.5, 24)]
    poly = [(x * u, y * u) for x, y in pts]
    d.polygon(poly, fill=EDGE)
    inner = [(x * u + (0.9 * u if x < 16 else -0.9 * u), y * u + (0.9 * u if y < 16 else -0.9 * u)) for x, y in pts]
    d.polygon(inner, fill=shade(LIGHT, pressed))
    f = font(fontdir, int(11 * u)); txt = side + 'B'
    l, t, r, b = d.textbbox((0, 0), txt, font=f)
    d.text(((s - (r - l)) / 2 - l, 16.3 * u - (b - t) / 2 - t), txt, font=f, fill=INK)
    return finish(im, size, disabled)


def dpad(direction, size=32, pressed=False, disabled=False):
    s = size * SS; u = s / 32
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    arm = 9.0
    a0, a1 = 16 - arm / 2, 16 + arm / 2
    col = shade(LIGHT, pressed)
    # contorno da cruz (como no kit) e o lado ativo preenchido
    cross = [(a0, 3), (a1, 3), (a1, a0), (29, a0), (29, a1), (a1, a1), (a1, 29), (a0, 29), (a0, a1), (3, a1), (3, a0), (a0, a0)]
    pts = [(x * u, y * u) for x, y in cross]
    d.line(pts + [pts[0]], fill=EDGE, width=int(3.6 * u), joint='curve')
    d.line(pts + [pts[0]], fill=col, width=int(1.8 * u), joint='curve')
    boxes = {'Up': (a0, 3, a1, 11), 'Down': (a0, 21, a1, 29), 'Left': (3, a0, 11, a1), 'Right': (21, a0, 29, a1)}
    for k in {'Up': ['Up'], 'Down': ['Down'], 'Left': ['Left'], 'Right': ['Right'],
              'Horizontal': ['Left', 'Right'], 'Vertical': ['Up', 'Down']}[direction]:
        x0, y0, x1, y1 = boxes[k]
        d.rectangle((x0 * u, y0 * u, x1 * u, y1 * u), fill=col)
    return finish(im, size, disabled)


def build(fontdir, out):
    os.makedirs(out, exist_ok=True)
    base = 'Images\\Visuals\\XuiGamepad\\Aurora.Skin.Controls.Controller.Buttons.'
    makers = {k: (lambda k: lambda **kw: face(fontdir, k, **kw))(k) for k in 'ABXY'}
    makers.update({'Back': view_btn, 'Start': menu_btn,
                   'Thumb.Left': lambda **kw: thumb(fontdir, 'L', **kw), 'Thumb.Right': lambda **kw: thumb(fontdir, 'R', **kw),
                   'Bumper.Left': lambda **kw: bumper(fontdir, 'L', **kw), 'Bumper.Right': lambda **kw: bumper(fontdir, 'R', **kw)})
    for dname in ('Up', 'Down', 'Left', 'Right', 'Horizontal', 'Vertical'):
        makers['Dpad.' + dname] = (lambda dn: lambda **kw: dpad(dn, **kw))(dname)
    n = 0
    for key, mk in makers.items():
        for state in ('Enabled', 'Disabled'):
            for fx in ('Blur', 'Press'):
                im = mk(pressed=(fx == 'Press'), disabled=(state == 'Disabled'))
                im.save(os.path.join(out, '%s%s.%s.%s.png' % (base, key, state, fx))); n += 1
    # ícones menores: botões Iniciar/Detalhes e painel de disco
    small = {
        'Images\\PolarGlass\\cta_A.png': lambda: face(fontdir, 'A', 24),
        'Images\\PolarGlass\\cta_Y.png': lambda: face(fontdir, 'Y', 24),
        'Images\\PolarGlass\\cta_Y_yellow.png': lambda: face(fontdir, 'Y', 24),
        'Images\\PolarGlass\\pad_A_20.png': lambda: face(fontdir, 'A', 20),
        'Images\\PolarGlass\\pad_Y_20.png': lambda: face(fontdir, 'Y', 20),
        'Images\\Icons\\DVDPanel\\Buttons\\Aurora.Skin.Scenes.Main.Panel.Buttons.X.Enabled.png': lambda: face(fontdir, 'X', 24),
        'Images\\Icons\\DVDPanel\\Buttons\\Aurora.Skin.Scenes.Main.Panel.Buttons.X.Holding.png': lambda: face(fontdir, 'X', 24, pressed=True),
        'Images\\Icons\\DVDPanel\\Buttons\\Aurora.Skin.Scenes.Main.Panel.Buttons.X.Disabled.png': lambda: face(fontdir, 'X', 24, disabled=True),
        'Images\\Icons\\DVDPanel\\Buttons\\Aurora.Skin.Scenes.Main.Panel.Buttons.Y.Enabled.png': lambda: face(fontdir, 'Y', 24),
        'Images\\Icons\\DVDPanel\\Buttons\\Aurora.Skin.Scenes.Main.Panel.Buttons.Y.Holding.png': lambda: face(fontdir, 'Y', 24, pressed=True),
        'Images\\Icons\\DVDPanel\\Buttons\\Aurora.Skin.Scenes.Main.Panel.Buttons.Y.Disabled.png': lambda: face(fontdir, 'Y', 24, disabled=True),
    }
    for name, mk in small.items():
        mk().save(os.path.join(out, name)); n += 1
    return n


if __name__ == '__main__':
    print(build(sys.argv[1], sys.argv[2]), 'ícones')
