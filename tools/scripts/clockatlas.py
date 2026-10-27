"""Atlas do relógio: algarismos 0-9 e ':' em Inter Bold, branco, cobertura no alfa (DXT5 512x512).
Células de 48 x 72 px (9 por linha); o shader mostra cada célula em 24 x 36 px na tela."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
CELL_W, CELL_H, PER_ROW = 48, 72, 9
CHARS = '0123456789:'


def atlas(fontpath, size=76):
    img = Image.new('L', (512, 512), 0); d = ImageDraw.Draw(img)
    f = ImageFont.truetype(fontpath, size)
    cap = d.textbbox((0, 0), '0', font=f)                     # altura dos algarismos
    for i, ch in enumerate(CHARS):
        cx, cy = (i % PER_ROW) * CELL_W, (i // PER_ROW) * CELL_H
        l, t, r, b = d.textbbox((0, 0), ch, font=f)
        x = cx + (CELL_W - (r - l)) / 2 - l
        y = cy + (CELL_H - (cap[3] - cap[1])) / 2 - cap[1]
        d.text((x, y), ch, font=f, fill=255)
    return np.asarray(img).astype(np.float32)


if __name__ == '__main__':
    a = atlas(sys.argv[1]); Image.fromarray(a.astype(np.uint8)).save(sys.argv[2])
