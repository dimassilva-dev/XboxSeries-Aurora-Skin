import sys, json
from PIL import Image, ImageDraw, ImageFont
xs, art, layout, out = sys.argv[1:5]
F = lambda w, s: ImageFont.truetype(xs + '/Fonts\\Inter-%s.ttf' % w, s)
ref = Image.open('ref/xbox-home.jpg').convert('RGB')
bg = ref.crop((300, 90, 760, 330)).resize((1280, 720), Image.LANCZOS).convert('RGBA')   # "arte do jogo"
bg.alpha_composite(Image.open(art + '/HomeChrome.png'))
bg = bg.convert('RGB')
d = ImageDraw.Draw(bg, 'RGBA')
m = [x for x in json.load(open(layout))['modes'] if x['name'] == 'Normal'][0]['covers']
FW, FH = 0.6914, 0.9766
cols = [(196, 60, 40), (40, 90, 170), (90, 140, 60), (150, 120, 40), (110, 60, 150), (40, 140, 140), (170, 70, 110), (80, 80, 80), (200, 150, 60)]
def cover(cx, cy, sx, sy, col, focus=False):
    w, h = FW * sx * 100, FH * sy * 100
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    if focus:
        d.rounded_rectangle((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), radius=11, outline=(77, 204, 92), width=4)
    d.rounded_rectangle(box, radius=6, fill=col if focus else tuple(int(c * 0.86) for c in col))
c = m['position']['center']; s = m['scale']['center']
cover(c[0] * 100, -c[1] * 100, s[0], s[1], cols[0], True)
r = m['position']['right']; s = m['scale']['right']; st = m['spacer']['right'][0]
for k in range(9):
    x = (r[0] + k * st) * 100
    if x < 1281: cover(x, -r[1] * 100, s[0], s[1], cols[(k + 1) % len(cols)])
# barra superior
d.ellipse((68, 38, 112, 82), fill=(60, 120, 160)); d.ellipse((64, 34, 116, 86), outline=(255, 255, 255, 120), width=2)
d.text((126, 44), 'NewSasquatch', font=F('SemiBold', 18), fill='white')
d.text((126, 64), 'G', font=F('Bold', 11), fill=(220, 220, 220)); d.text((148, 64), '21.337', font=F('Medium', 13), fill=(220, 220, 220))
for x, w, lab, key in ((420, 77, 'Exibir', 'B'), (517, 100, 'Navegar', 'X'), (637, 99, 'Sistema', '⧉'), (756, 105, 'Ajustes', '≡')):
    d.ellipse((x, 46, x + 20, 66), fill=(255, 255, 255, 50)); d.text((x + 6, 48), key, font=F('Bold', 12), fill='white')
    d.text((x + 26, 47), lab, font=F('Light', 14), fill='white')
d.text((1046, 52), '16:55', font=F('Medium', 16), fill='white')
# rodapé
d.text((64, 574), 'Starfield', font=F('Bold', 30), fill='white')
d.rounded_rectangle((64, 640, 247, 688), radius=24, fill=(16, 124, 16)); d.text((100, 652), 'Iniciar', font=F('SemiBold', 18), fill='white')
d.rounded_rectangle((259, 640, 417, 688), radius=24, fill=(255, 255, 255, 40), outline=(255, 255, 255, 90))
d.ellipse((275, 652, 299, 676), fill=(230, 180, 30)); d.text((282, 654), 'Y', font=F('Bold', 15), fill='white'); d.text((308, 652), 'Detalhes', font=F('SemiBold', 18), fill='white')
d.text((440, 654), '1 de 120', font=F('SemiBold', 18), fill=(229, 229, 234))
bg.convert('RGB').save(out)
