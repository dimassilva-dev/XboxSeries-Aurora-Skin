"""Arte das telas internas.

  recolor_xbox(img, name)  -> peça da Liquid Glass convertida para o estilo Xbox Series
  details_xbox(fontdir)    -> fundo da tela de detalhes (Xbox Series, pt-BR)
  details_lg_ptbr(img, fontdir) -> fundo de detalhes da Liquid Glass com os rótulos em pt-BR
"""
import colorsys, re
from PIL import Image, ImageDraw, ImageFont

SS = 4  # supersampling para bordas suaves


def font(fontdir, weight, size):
    return ImageFont.truetype(fontdir + '/Fonts\\Inter-%s.ttf' % weight, size)


# ------------------------------------------------------------------ cores
def _xbox_pixel(r, g, b, a):
    if a == 0:
        return (r, g, b, a)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if 0.5 <= h <= 0.72 and s >= 0.45 and v >= 0.8:
        # azul de destaque (iOS) -> verde Xbox
        h, s, v = 0.333, min(1.0, s * 0.9), v * 0.55
    elif 0.25 <= h <= 0.45 and s >= 0.4 and v >= 0.6:
        # verde-menta (iOS) -> verde Xbox #107C10
        h, s, v = 0.333, 0.87, 0.49
    elif s < 0.5:
        # neutros azulados -> grafite neutro
        s = 0.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (round(r * 255), round(g * 255), round(b * 255), a)


def recolor(img):
    img = img.convert('RGBA')
    img.putdata([_xbox_pixel(*p) for p in img.getdata()])
    return img


def _rounded(size, radius, fill, outline=None, width=1):
    w, h = size
    big = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=radius * SS,
                        fill=fill, outline=outline, width=width * SS if outline else 0)
    return big.resize((w, h), Image.LANCZOS)


def reshape(img, radius=4, rim=True):
    """Pílula/círculo esticável -> retângulo com cantos pequenos, mesma cor e borda."""
    w, h = img.size
    c = img.getpixel((w // 2, h // 2))
    top = img.getpixel((w // 2, 0))
    fill = c if c[3] > 0 else None
    outline = top if rim and (top[3] > 0 and (fill is None or abs(sum(top[:3]) - sum(c[:3])) > 40 or abs(top[3] - c[3]) > 30)) else None
    if fill is None and outline is None:
        return img
    return _rounded((w, h), radius, fill, outline, 1)


def is_pill(name, img):
    w, h = img.size
    base = name.split('\\')[-1]
    if base.startswith(('rr_', 'Round', 'CTA_')) and w == h and w >= 25:
        return True
    return 'Controls.Button' in base and h <= 40 and w > 3 * h


def solidify(img):
    """Painel escuro translúcido -> quase opaco; borda clara de vidro -> bem discreta."""
    w, h = img.size
    c = img.getpixel((w // 2, h // 2))
    a = img.getchannel('A')
    if c[3] == 0:
        edge = max(img.getpixel((w // 2, 0))[:3])
        if edge > 150:
            # contorno branco de vidro: some (os painéis Xbox não têm borda)
            return Image.merge('RGBA', (*img.split()[:3], a.point(lambda v: 0)))
        return img
    if min(c[:3]) > 230 and 20 <= c[3] <= 70:
        # vidro branco translúcido (painel claro, subfoco, itens de lista) -> grafite sólido
        g = 46 if c[3] <= 40 else 56
        solid = Image.new('RGBA', img.size, (g, g, g, 255))
        return Image.merge('RGBA', (*solid.split()[:3], a.point(lambda v: min(255, int(v * 240 / c[3])))))
    if max(c[:3]) < 80 and 90 <= c[3] <= 225:
        k = 242 / c[3]
        return Image.merge('RGBA', (*img.split()[:3], a.point(lambda v: min(255, int(v * k)))))
    return img


def recolor_xbox(img, name):
    out = solidify(recolor(img))
    if is_pill(name, img):
        # botões CTA (Iniciar/Detalhes) ficam chapados, sem o aro claro do vidro
        out = reshape(out, rim='CTA_' not in name)
    return out


# ------------------------------------------------------------------ rodapé de dicas
def _glyph(fontdir, letter, color, size=24):
    g = _rounded((size, size), size // 2, color)
    d = ImageDraw.Draw(g)
    f = font(fontdir, 'Bold', 13)
    tw = d.textlength(letter, font=f)
    d.text(((size - tw) / 2, 4), letter, font=f, fill=(255, 255, 255, 255))
    return g


def _dpad(color=(240, 240, 244, 255), size=20):
    g = Image.new('RGBA', (size * SS, size * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    t = 6 * SS; s = size * SS
    d.rounded_rectangle(((s - t) // 2, 0, (s + t) // 2, s - 1), radius=SS * 1.5, outline=color, width=int(1.6 * SS))
    d.rounded_rectangle((0, (s - t) // 2, s - 1, (s + t) // 2), radius=SS * 1.5, outline=color, width=int(1.6 * SS))
    d.rectangle(((s - t) // 2 + 2 * SS, (s - t) // 2 + 2 * SS, (s + t) // 2 - 2 * SS, (s + t) // 2 - 2 * SS), fill=(0, 0, 0, 0))
    return g.resize((size, size), Image.LANCZOS)


def _hints(canvas, fontdir, items, x0, x1, cy, align='center', text=(240, 240, 244, 255), gap=22):
    f = font(fontdir, 'SemiBold', 16)
    d = ImageDraw.Draw(canvas)
    widths = [g.size[0] + 8 + d.textlength(t, font=f) for g, t in items]
    total = sum(widths) + gap * (len(items) - 1)
    x = x0 + (x1 - x0 - total) / 2 if align == 'center' else x1 - total
    for (g, t), w in zip(items, widths):
        canvas.alpha_composite(g, (int(round(x)), int(cy - g.size[1] / 2)))
        d.text((x + g.size[0] + 8, cy - 11), t, font=f, fill=text)
        x += w + gap


def _label(canvas, fontdir, xy, text, color, size=11, weight='Bold', track=0.9):
    d = ImageDraw.Draw(canvas); f = font(fontdir, weight, size); x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=color); x += d.textlength(ch, font=f) + track


# ------------------------------------------------------------------ detalhes: Xbox Series
PT_LABELS = {'overview': 'VISÃO GERAL', 'actions': 'AÇÕES', 'rating': 'AVALIAÇÃO',
             'select': 'Selecionar', 'back': 'Voltar', 'more': 'Mais opções'}


def details_xbox(fontdir, labels=None):
    t = dict(PT_LABELS, **(labels or {}))
    W, H = 1280, 720
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # véu escuro sobre a arte do jogo: mais forte à direita (painel) e embaixo
    veil = Image.new('L', (W, H)); px = veil.load()
    for y in range(H):
        for x in range(W):
            a = 200 + 30 * max(0.0, (x - 300) / 980) + 25 * max(0.0, (y - 420) / 300)
            px[x, y] = min(248, int(a))
    img = Image.merge('RGBA', (*Image.new('RGB', (W, H), (8, 9, 9)).split(), veil))
    # janela da capa (a capa é desenhada por trás), cantos de 6 px como no shader
    hole = _rounded((242, 338), 6, (255, 255, 255, 255)).getchannel('A')
    a = img.getchannel('A'); a.paste(0, (64, 88), hole); img.putalpha(a)
    panel = (32, 32, 32, 252)
    for box in ((896, 88, 1216, 636), (340, 540, 580, 636), (596, 540, 872, 636)):
        x0, y0, x1, y1 = box
        img.alpha_composite(_rounded((x1 - x0, y1 - y0), 4, panel), (x0, y0))
    _label(img, fontdir, (924, 112), t['actions'], (170, 170, 170, 255))
    _label(img, fontdir, (364, 560), t['rating'], (170, 170, 170, 255))
    _label(img, fontdir, (340, 202), t['overview'], (158, 194, 79, 255))
    items = [(_glyph(fontdir, 'A', (16, 124, 16, 255)), t['select']),
             (_glyph(fontdir, 'B', (210, 52, 42, 255)), t['back']),
             (_dpad(), t['more'])]
    _hints(img, fontdir, items, 340, 1216, 678, align='right')
    return img


# ------------------------------------------------------------------ detalhes: Liquid Glass em pt-BR
def _clear(img, box, src_x):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        p = img.getpixel((src_x, y))
        for x in range(x0, x1):
            img.putpixel((x, y), p)


def details_lg_ptbr(img, fontdir):
    img = img.convert('RGBA').copy()
    blue = img.getpixel((345, 207)); blue = max((img.getpixel((x, y)) for x in range(340, 409) for y in range(203, 213)), key=lambda p: p[2])
    grey = max((img.getpixel((x, y)) for x in range(924, 983) for y in range(113, 122)), key=lambda p: sum(p[:3]))
    _clear(img, (336, 199, 416, 217), 424); _label(img, fontdir, (340, 202), 'VISÃO GERAL', blue)
    _clear(img, (920, 108, 992, 126), 1000); _label(img, fontdir, (924, 112), 'AÇÕES', grey)
    _clear(img, (360, 556, 416, 574), 424); _label(img, fontdir, (364, 560), 'AVALIAÇÃO', grey)
    a = img.crop((463, 664, 491, 692)); b = img.crop((577, 664, 605, 692)); dp = img.crop((681, 666, 705, 690))
    _clear(img, (458, 662, 826, 696), 455)
    _hints(img, fontdir, [(a, 'Selecionar'), (b, 'Voltar'), (dp, 'Mais opções')], 442, 838, 678, gap=16)
    return img
