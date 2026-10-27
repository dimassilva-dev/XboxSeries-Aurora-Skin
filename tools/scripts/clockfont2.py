"""Relógio da Home, fonte v3: algarismos no estilo Inter Bold feitos de anéis elípticos e traços retos.

Cada algarismo ocupa uma caixa de 20 x 30 px (espaço 1280 x 720). Primitivas:
  ('s', ax, ay, bx, by)                      traço reto
  ('e', cx, cy, rx, ry, cuts)                anel elíptico; cuts = semiplanos onde o anel FICA (n·p <= c)
O mesmo desenho gera a prévia (numpy) e o HLSL (um ramo por algarismo, só length/abs/min/max, sem atan2).
"""
T = 2.75            # meia espessura do traço (traço de ~5,5 px)

import math


def _pt(cx, cy, rx, ry, ang):
    """Ponto da elipse no ângulo ang (graus; 0 = direita, 90 = baixo, 270 = cima)."""
    t = math.radians(ang)
    return (round(cx + rx * math.cos(t), 3), round(cy + ry * math.sin(t), 3))


def arc(cx, cy, rx, ry, a0, a1):
    """Arco de a0 até a1 no sentido horário da tela (ângulo crescente), pontas retas."""
    span = (a1 - a0) % 360 or 360
    def dirv(ang):
        x, y = _pt(0, 0, rx, ry, ang); k = math.hypot(x, y); return (x / k, y / k)
    def wedge(u_ang, v_ang):            # semiplanos cuja interseção é a cunha de u até v (horário)
        u = dirv(u_ang); v = dirv(v_ang)
        n1 = (u[1], -u[0]); n2 = (-v[1], v[0])
        return [(n1[0], n1[1], n1[0] * cx + n1[1] * cy), (n2[0], n2[1], n2[0] * cx + n2[1] * cy)]
    if span >= 360:
        return ('e', cx, cy, rx, ry, [])
    if span <= 180:
        return ('e', cx, cy, rx, ry, wedge(a0, a1))               # mantém a cunha
    return ('e', cx, cy, rx, ry, [('remove', wedge(a1, a0))])     # apaga a cunha que sobra


def _seg(a, b):
    return ('s', a[0], a[1], b[0], b[1])


# arcos e traços encaixados: cada traço começa no ponto onde o arco termina
_2a = (10.0, 9.2, 7.0, 6.6); _2end = _pt(*_2a, 35)
_3t = (10.0, 8.4, 6.6, 6.0); _3b = (10.0, 20.8, 7.4, 6.6)
_5b = (10.4, 19.6, 7.2, 7.2); _5start = _pt(*_5b, 212)
_6b = (10.0, 20.0, 7.4, 7.2); _6join = _pt(*_6b, 200)
_9t = (10.0, 10.0, 7.4, 7.2); _9join = _pt(*_9t, 20)

DIGITS = {
    0: [('e', 10, 15, 7.4, 12.4, [])],
    1: [('s', 12.2, 2.6, 12.2, 27.4), ('s', 12.2, 2.6, 5.8, 7.0)],
    2: [arc(*_2a, 190, 35), _seg(_2end, (3.0, 27.4)), ('s', 3.0, 27.4, 17.4, 27.4)],
    3: [arc(*_3t, 205, 105), arc(*_3b, 255, 155), _seg(_pt(*_3t, 105), _pt(*_3b, 255))],
    4: [('s', 14.0, 2.6, 2.6, 20.6), ('s', 2.6, 20.6, 18.2, 20.6), ('s', 14.0, 2.6, 14.0, 27.4)],
    5: [('s', 16.8, 2.6, 5.2, 2.6), _seg((5.2, 2.6), _5start), arc(*_5b, 212, 150)],
    6: [('e',) + _6b + ([],), _seg((13.8, 2.6), _6join)],
    7: [('s', 2.6, 2.6, 17.4, 2.6), ('s', 17.4, 2.6, 7.6, 27.4)],
    8: [('e', 10, 8.4, 6.4, 5.8, []), ('e', 10, 20.8, 7.4, 6.6, [])],
    9: [('e',) + _9t + ([],), _seg(_9join, (6.4, 27.4))],
}


# ---------------------------------------------------------------- prévia em numpy
def _np():
    import numpy as np
    return np


def dist(p, prim):
    np = _np()
    if prim[0] == 's':
        _, ax, ay, bx, by = prim
        a = np.array([ax, ay]); b = np.array([bx, by])
        pa = p - a; ba = b - a
        h = np.clip((pa * ba).sum(-1) / (ba * ba).sum(), 0, 1)
        return np.linalg.norm(pa - ba * h[..., None], axis=-1)
    _, cx, cy, rx, ry, cuts = prim
    pc = p - np.array([cx, cy])
    k0 = np.linalg.norm(pc / np.array([rx, ry]), axis=-1)
    k1 = np.linalg.norm(pc / np.array([rx * rx, ry * ry]), axis=-1)
    g = np.where(k0 < 0.05, min(rx, ry), k0 / np.maximum(k1, 1e-4))   # no centro a fórmula zera
    d = np.abs((k0 - 1.0) * g)
    for cut in cuts:
        if cut[0] == 'remove':
            inside = np.max([(p[..., 0] * nx + p[..., 1] * ny - c) / np.hypot(nx, ny) for nx, ny, c in cut[1]], axis=0)
            d = np.maximum(d, T - inside)        # dentro da região: some; borda reta
            continue
        nx, ny, c = cut
        d = np.maximum(d, (p[..., 0] * nx + p[..., 1] * ny - c) / np.hypot(nx, ny) + T)   # corte reto, sem sobra do traço
    return d


def digit(p, n):
    np = _np()
    d = np.full(p.shape[:-1], 1e3)
    for prim in DIGITS[n]:
        d = np.minimum(d, dist(p, prim))
    return np.clip(T + 0.5 - d, 0, 1)


# ---------------------------------------------------------------- HLSL
def _f(v):
    return '%.4gf' % v if '.' in '%.4g' % v or 'e' in '%.4g' % v else '%.1ff' % v


def _prim_hlsl(prim):
    if prim[0] == 's':
        _, ax, ay, bx, by = prim
        return 'PG_Seg( p, float2( %s, %s ), float2( %s, %s ) )' % (_f(ax), _f(ay), _f(bx), _f(by))
    _, cx, cy, rx, ry, cuts = prim
    e = 'PG_Ring( p, float2( %s, %s ), float2( %s, %s ) )' % (_f(cx), _f(cy), _f(rx), _f(ry))
    for cut in cuts:
        if cut[0] == 'remove':
            planes = []
            for nx, ny, c in cut[1]:
                k = (nx * nx + ny * ny) ** 0.5
                planes.append('( dot( p, float2( %s, %s ) ) %s %s )' % (_f(nx / k), _f(ny / k), '-' if c >= 0 else '+', _f(abs(c / k))))
            inside = planes[0]
            for pl in planes[1:]:
                inside = 'max( %s, %s )' % (inside, pl)
            e = 'max( %s, %s - %s )' % (e, _f(T), inside)
            continue
        nx, ny, c = cut
        k = (nx * nx + ny * ny) ** 0.5
        off = c / k - T
        e = 'max( %s, dot( p, float2( %s, %s ) ) %s %s )' % (e, _f(nx / k), _f(ny / k), '-' if off >= 0 else '+', _f(abs(off)))
    return e


def hlsl(org=(1118.0, 41.0)):
    L = ['// ---- relogio da Home (24 h): algarismos estilo Inter Bold (aneis elipticos + tracos retos)',
         'inline float PG_Seg( float2 p, float2 a, float2 b )',
         '{',
         '\tfloat2 pa = p - a, ba = b - a;',
         '\tfloat h = saturate( dot( pa, ba ) / dot( ba, ba ) );',
         '\treturn length( pa - ba * h );',
         '}',
         '',
         'inline float PG_Ring( float2 p, float2 c, float2 r )',
         '{',
         '\tfloat2 pc = p - c;',
         '\tfloat k0 = length( pc / r );',
         '\tfloat k1 = length( pc / ( r * r ) );',
         '\tfloat g = k0 < 0.05f ? min( r.x, r.y ) : k0 / max( k1, 0.0001f );',
         '\treturn abs( ( k0 - 1.0f ) * g );',
         '}',
         '',
         '// p: pixel relativo ao canto do algarismo (20 x 30 px); retorna cobertura 0..1',
         'float PG_Digit( float2 p, float n )',
         '{',
         '\tfloat d = 1000.0f;']
    # sem if/else: calcula todas as primitivas e desliga as dos outros algarismos (como a v2, que apareceu no console)
    for k in range(10):
        L.append('\tfloat o%d = step( 0.5f, abs( n - %d.0f ) ) * 1000.0f;\t// 0 se o algarismo e %d' % (k, k, k))
    for k in range(10):
        for prim in DIGITS[k]:
            L.append('\td = min( d, %s + o%d );' % (_prim_hlsl(prim), k))
    L += ['\treturn saturate( %s - d );' % _f(T + 0.5),
          '}',
          '',
          '// cobertura do relogio HH:MM no pixel px (tela 1280x720); 0 se a hora de inicio nao foi gravada',
          'float PG_Clock( float2 px )',
          '{',
          '\tfloat3 a = g_fLightAttenuation;',
          '\ta.x = a.x > 29.5f ? a.x - 30.0f : a.x;\t// +30: layout sem desfoque (so o relogio)',
          '\tbool ok = a.x >= 0.0f && a.x < 24.0f && a.y >= 0.0f && a.y < 60.0f && a.z >= 0.0f && a.z < 60.0f &&',
          '\t          abs( a.x - floor( a.x + 0.5f ) ) < 0.01f && abs( a.y - floor( a.y + 0.5f ) ) < 0.01f;',
          '\tconst float2 org = float2( %s, %s );' % (_f(org[0]), _f(org[1])),
          '\tfloat2 q = px - org;',
          '\tif( !ok || q.x < -4.0f || q.x > 102.0f || q.y < -4.0f || q.y > 34.0f ) return 0.0f;',
          '\tfloat t = fmod( a.x * 3600.0f + a.y * 60.0f + a.z + g_fApplicationTime, 86400.0f );',
          '\tfloat hh = floor( t / 3600.0f ), mm = floor( fmod( t, 3600.0f ) / 60.0f );',
          '\t// um algarismo por pixel: casa pela posicao x (0-20, 22-42 | dois-pontos 49 | 56-76, 78-98)',
          '\tfloat x0 = q.x < 21.0f ? 0.0f : q.x < 44.0f ? 22.0f : q.x < 77.0f ? 56.0f : 78.0f;',
          '\tfloat n = q.x < 21.0f ? floor( hh / 10.0f ) : q.x < 44.0f ? fmod( hh, 10.0f ) : q.x < 77.0f ? floor( mm / 10.0f ) : fmod( mm, 10.0f );',
          '\tfloat c = ( q.x > 44.0f && q.x < 54.0f ) ? 0.0f : PG_Digit( q - float2( x0, 0.0f ), n );',
          '\tc = max( c, saturate( 3.4f - length( q - float2( 49.0f, 10.5f ) ) ) );',
          '\tc = max( c, saturate( 3.4f - length( q - float2( 49.0f, 22.5f ) ) ) );',
          '\treturn c;',
          '}',
          '']
    return '\n'.join(L)


def preview(path, font=None):
    """Prévia: protótipo (Inter Bold) x shader, várias horas."""
    np = _np()
    from PIL import Image, ImageDraw, ImageFont
    def clock(text):
        W, H = 110, 40
        ys, xs = np.mgrid[0:H, 0:W].astype(float) + 0.5
        q = np.stack([xs - 4, ys - 5], -1); c = np.zeros((H, W))
        for x0, ch in zip((0, 22, 56, 78), text.replace(':', '')):
            c = np.maximum(c, digit(q - np.array([x0, 0]), int(ch)))
        for y in (10.5, 22.5):
            c = np.maximum(c, np.clip(3.4 - np.linalg.norm(q - np.array([49, y]), axis=-1), 0, 1))
        return c
    times = ('21:47', '09:30', '16:58', '03:12')
    bg = Image.new('RGB', (520, 70 + 58 * len(times)), (18, 22, 26)); d = ImageDraw.Draw(bg)
    if font:
        f = ImageFont.truetype(font, 44)
        d.text((20, 10), 'protótipo (Inter Bold)', fill=(150, 150, 150)); d.text((280, 10), 'shader (fonte nova)', fill=(150, 150, 150))
    for i, t in enumerate(times):
        if font: d.text((20, 32 + i * 58), t, font=f, fill=(245, 245, 245))
        c = clock(t)
        bg.paste(Image.new('RGB', (110, 40), (245, 245, 245)), (280, 34 + i * 58), Image.fromarray((c * 255).astype(np.uint8)))
    bg.resize((bg.size[0] * 2, bg.size[1] * 2), Image.LANCZOS).save(path)


if __name__ == '__main__':
    import sys
    preview(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
