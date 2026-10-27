"""Gera o fundo (BK*.asset) desfocado a partir da capa (GC*.asset) para jogos sem fundo no Aurora.

uso: python fundos.py <bk_modelo.asset> <pasta_gc> <saida> [previa_dir]
Cada capa <id>.asset vira <saida>/<id>.asset (RXEA, DXT5 1920x1080 linear, igual ao formato do Aurora).
"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
sys.path.insert(0, os.path.dirname(__file__))
from rxea import decode, encode_bc3, info

HDR = 0x800


def blurred_bg(cover_rgb):
    h, w, _ = cover_rgb.shape
    front = Image.fromarray(cover_rgb).crop((int(0.528 * w), int(0.002 * h), int(0.999 * w), int(0.996 * h)))
    big = front.resize((1920, int(1920 * front.height / front.width)), Image.LANCZOS)
    top = int(big.height * 0.29)                                  # meio da capa (mais arte, menos logotipo)
    top = min(top, big.height - 1080)
    bg = big.crop((0, top, 1920, top + 1080)).filter(ImageFilter.GaussianBlur(34))
    bg = ImageEnhance.Color(bg).enhance(0.85)
    return ImageEnhance.Brightness(bg).enhance(0.72)


def build(model, gc_dir, out_dir, prev=None):
    m = open(model, 'rb').read(); t = info(m)
    header = m[:HDR]; rows = (len(m) - HDR) // t['pitch']
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(gc_dir)):
        cover = decode(open(os.path.join(gc_dir, f), 'rb').read())
        bg = blurred_bg(cover)
        data = encode_bc3(np.asarray(bg), t['pitch'], rows)
        assert len(data) == len(m) - HDR
        open(os.path.join(out_dir, f), 'wb').write(header + data)
        if prev:
            os.makedirs(prev, exist_ok=True); bg.resize((480, 270)).save(os.path.join(prev, f + '.png'))
        n += 1
    return n


if __name__ == '__main__':
    print(build(*sys.argv[1:5]), 'fundos gerados')
