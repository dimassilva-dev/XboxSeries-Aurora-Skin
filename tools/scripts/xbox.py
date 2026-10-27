"""Gera a skin Xbox Series a partir da Liquid Glass traduzida.

uso: python xbox.py <base.xzp> <saida.xzp> <arte_dir> [pecas_dir]

pecas_dir: imagens recoloridas (art2.recolor_xbox) com o mesmo nome interno do pacote.
"""
import sys, os, struct, re, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
from xzp import parse
from strn import sections, strings
from elems import elements

# ---------------------------------------------------------------- Aurora_Main
TOOLBAR_DX = 64 - 502          # perfil vai do centro para o canto superior esquerdo
TOOLBAR_VECTS = [21, 22, 23, 34, 35, 36, 37, 38, 39, 41]

# indice do vetor -> nova posicao (x, y). Os pares "fora da tela" das animacoes
# acompanham a posicao de repouso.
MAIN_VECTS = {
    # dicas de botao: da capsula de baixo para o centro da barra superior
    15: (420, 40), 60: (420, -78),     # Exibir
    16: (517, 40), 61: (517, -78),     # Navegar
    18: (637, 40), 63: (637, -78),     # Sistema
    19: (756, 40), 64: (756, -78),     # Ajustes
    # titulo do jogo logo abaixo da fileira de capas
    5: (64, 550), 55: (64, 550), 56: (64, 668), 57: (64, 668),
    # contador "1 de 120" ao lado dos botoes
    7: (462, 634), 58: (462, 752),
    # Iniciar / Detalhes no rodape
    14: (64, 616), 59: (64, 734),
    17: (259, 616), 62: (259, 734),
    # hora grande no canto superior direito (dashboard 2026); o gamerscore fica sob a gamertag
    20: (856, 41),
    # perfil: gamertag um pouco acima, G e pontos mais abaixo e com mais respiro entre o G e o número
    21: (126, 33.0), 34: (126, 33.0), 35: (206, 33.0),
    39: (126, 68.0), 41: (148, 65.3),      # G (centro y=76) e pontos com o mesmo centro, 6 px de espaço
}

# id do elemento -> {largura, altura, tamanho da fonte (antigo -> novo)}
MAIN_SIZES = {
    # textos da Home têm escala 0.5: caixa do título alta o bastante para não cortar as letras
    'GameTitleInfo': dict(w=2200.0, h=104.0, pt=(104.0, 30.0)),
    'GameListCounterInfo': dict(w=600.0, h=96.0, pt=(30.0, 30.0)),
    # hora/status termina na margem direita (x=1216), sem LB/RB em volta
    # estilo XUI: 0x400 centro, 0x200 direita, 0x10 centro vertical, 0x4000 reticências (0x8 é sublinhado)
    # textos da Home têm escala 0.5: a largura efetiva é metade de w (720 -> 360 px, de 856 a 1216)
    'StatusInfo': dict(w=720.0, h=60.0, pt=(30.0, 36.0), font='Inter SemiBold', style=0x4210),
    'DetailsButton': dict(w=183.0, h=48.0),
    'textCredScoreAndAchievementsEarned': dict(w=600.0, h=43.0, pt=(26.0, 30.0)),
}


def patch_main(d, vect_map=None, sizes=None, toolbar=True):
    vect_map = MAIN_VECTS if vect_map is None else vect_map
    sizes = MAIN_SIZES if sizes is None else sizes
    d = bytearray(d)
    b, secs = sections(bytes(d))
    vo, vsz = secs['VECT']
    def setv(i, x, y):
        assert i * 12 < vsz
        z = struct.unpack('>f', d[vo+i*12+8:vo+i*12+12])[0]
        d[vo+i*12:vo+i*12+12] = struct.pack('>3f', x, y, z)
    def getv(i):
        return struct.unpack('>3f', d[vo+i*12:vo+i*12+12])
    for i in (TOOLBAR_VECTS if toolbar else []):
        x, y, _ = getv(i)
        assert x >= 500, (i, x)
        setv(i, x + TOOLBAR_DX, y)
    for i, (x, y) in vect_map.items():
        setv(i, x, y)
    for e in elements(bytes(d)):
        cfg = sizes.get(e.get('id'))
        if not cfg:
            continue
        d[e['w_off']:e['w_off']+4] = struct.pack('>f', cfg['w'])
        d[e['h_off']:e['h_off']+4] = struct.pack('>f', cfg['h'])
        if 'pt' not in cfg:
            continue
        old, new = cfg['pt']
        k = bytes(d).find(struct.pack('>f', old), e['h_off'] + 4, e['h_off'] + 48)  # depois da altura
        assert k != -1, e['id']
        d[k:k+4] = struct.pack('>f', new)
        if 'font' in cfg:
            # o indice da fonte (u16) vem logo depois do tamanho
            fi = strings(bytes(d)).index(cfg['font']) + 1
            d[k+4:k+6] = struct.pack('>H', fi)
        if 'style' in cfg:
            d[k+6:k+10] = struct.pack('>I', cfg['style'])
        if 'color' in cfg:
            d[k-8:k-4] = struct.pack('>I', cfg['color'])   # cor ARGB vem antes da sombra e do tamanho
    return bytes(d)


# ---------------------------------------------------------------- todas as telas
# cores da Liquid Glass (azul-marinho) que viram grafite/cinza neutro
COLOR_SWAPS = {
    bytes.fromhex('ff0a0b14'): bytes.fromhex('ff0b0b0b'),   # preenchimento dos véus (Overlay)
    bytes.fromhex('cc23242f'): bytes.fromhex('cc232323'),   # barras do Sistema
    bytes.fromhex('ffa7a9b8'): bytes.fromhex('ffaaaaaa'),   # texto secundário
}
# véu (Overlay) com 65% de opacidade -> 88%, para o fundo não brigar com o texto
OVERLAY_OLD = struct.pack('>f', 0.65) + bytes.fromhex('190f00010102ff0f0f80')
OVERLAY_NEW = struct.pack('>f', 0.88) + bytes.fromhex('190f00010102ff0f0f80')
FONT_SCALE = 0.78            # textos do Aurora em pt-BR são mais longos que os em inglês
FONT_SCALE_SKIP = {'Aurora_Main.xur', 'Aurora_Loading.xur'}


def patch_screen(name, d):
    b, secs = sections(d)
    o, sz = secs['DATA']
    D = bytearray(d[o:o+sz])
    for old, new in COLOR_SWAPS.items():
        D = D.replace(old, new)
    D = D.replace(OVERLAY_OLD, OVERLAY_NEW)
    if name not in FONT_SCALE_SKIP:
        st = strings(d)
        fonts = {i + 1 for i, x in enumerate(st) if x.startswith('Inter')}
        k = 0
        while k < len(D) - 10:
            pt = struct.unpack('>f', D[k:k+4])[0]
            fi = int.from_bytes(D[k+4:k+6], 'big')
            if fi in fonts and 8.0 <= pt <= 80.0 and pt == round(pt * 2) / 2 and D[k+6] == 0 and D[k+7] == 0:
                D[k:k+4] = struct.pack('>f', round(pt * FONT_SCALE * 2) / 2)
                k += 6
            else:
                k += 1
    return d[:o] + bytes(D) + d[o+sz:]


def add_vect(d, xyz):
    b, secs = sections(d)
    vo, vsz = secs['VECT']
    idx = vsz // 12
    out = bytearray(d[:vo+vsz] + struct.pack('>3f', *xyz) + d[vo+vsz:])
    fl = struct.unpack('>I', d[8:12])[0]
    p = 0x14 + (0x28 if fl & 1 else 0)
    for _ in range(struct.unpack('>H', d[0x12:0x14])[0]):
        tag = out[p:p+4]; off = struct.unpack('>I', out[p+4:p+8])[0]
        if tag == b'VECT': out[p+8:p+12] = struct.pack('>I', vsz + 12)
        elif off > vo: out[p+4:p+8] = struct.pack('>I', off + 12)
        p += 12
    out[0xe:0x12] = struct.pack('>I', len(out))
    return bytes(out), idx


# ---------------------------------------------------------------- modelos de botão (Aurora_Skin)
# Iniciar (A) e Detalhes (Y): ícone + texto logo depois, alinhados pelo centro vertical do botão
CTA_GLYPH_VECT = (204, (16.0, 12.0))    # ícone 24 px -> centro em y=24
CTA_TEXT_VECT = (205, (48.0, 11.5))     # texto 8 px depois do ícone


def patch_skin_templates(d):
    d = bytearray(d)
    b, secs = sections(bytes(d))
    vo, _ = secs['VECT']
    for i, (x, y) in (CTA_GLYPH_VECT, CTA_TEXT_VECT):
        z = struct.unpack('>f', d[vo+i*12+8:vo+i*12+12])[0]
        d[vo+i*12:vo+i*12+12] = struct.pack('>3f', x, y, z)
    els = sorted(elements(bytes(d)), key=lambda e: e['off'])
    for k, e in enumerate(els):
        if e.get('id') in ('PG_CTA_A', 'PG_CTA_Y'):
            t = [x for x in els[k+1:k+5] if x.get('id') == 'txtMain'][0]
            d[t['w_off']:t['w_off']+4] = struct.pack('>f', 250.0)        # escala 0.5 -> 125 px
            k2 = bytes(d).find(struct.pack('>f', 25.0), t['h_off'], t['h_off'] + 48)
            assert k2 != -1
            d[k2:k2+4] = struct.pack('>f', 34.0)                         # texto maior (escala 0.5 -> ~17 px)
    return bytes(d)


# ---------------------------------------------------------------- abertura (splash)
# a abertura usa uma imagem própria; o logo do Aurora some (a arte já traz o logo)
SPLASH_FILES = {
    'Images\\XboxSeries\\Splash.png': 'Splash.png',
    'Images\\XboxSeries\\Empty.png': 'Empty.png',
}
# texto de carregamento centralizado sob o logo, leve e cinza claro
LOADING_VECTS = {1: (0, 2000)}   # texto de status fora da tela (a frase fixa está na imagem)
LOADING_SIZES = {
    'LoadingStatusText': dict(w=2560.0, h=60.0, pt=(30.0, 40.0), font='Inter Light', style=0x4410, color=0xFFBDBDBD),
}
LOADING_STRINGS = {
    'Images\\PolarGlass\\Ground.png': 'Images\\XboxSeries\\Splash.png',
    'Images\\Aurora.Skin.Scenes.Settings.About.Aurora.Logo.png': 'Images\\XboxSeries\\Empty.png',
    'Images\\Aurora.Skin.Scenes.Splash.Logo.Alternate.png': 'Images\\XboxSeries\\Empty.png',
}


def replace_strings(d, mapping, append=()):
    b, secs = sections(d)
    st = strings(d)
    missing = set(mapping) - set(st)
    assert not missing, missing
    new = [mapping.get(x, x) for x in st] + [x for x in append if x not in st]
    blob = b''.join(struct.pack('>H', len(x)) + x.encode('utf-16-be') for x in new)
    so, ssz = secs['STRN']; delta = len(blob) - ssz
    out = bytearray(d[:so] + blob + d[so+ssz:])
    fl = struct.unpack('>I', d[8:12])[0]
    p = 0x14 + (0x28 if fl & 1 else 0)
    for _ in range(struct.unpack('>H', d[0x12:0x14])[0]):
        tag = out[p:p+4]; off = struct.unpack('>I', out[p+4:p+8])[0]
        if tag == b'STRN': out[p+8:p+12] = struct.pack('>I', len(blob))
        elif off > so: out[p+4:p+8] = struct.pack('>I', off + delta)
        p += 12
    out[0xe:0x12] = struct.pack('>I', len(out))
    return bytes(out)


# ---------------------------------------------------------------- shader
# Relógio na Home (experimental): XBOX_CLOCK=1 no ambiente. Precisa do Main.lua de tools/experimentos/relogio-na-home.
ENABLE_CLOCK = os.environ.get('XBOX_CLOCK') == '1'

SHADER_EDITS = [
    (r'static const float3 PG_ACCENT [^\n]*',
     'static const float3 PG_ACCENT     = float3( 0.619608f, 0.760784f, 0.309804f );\t// focus ring: Xbox 2026 lime #9EC24F'),
    (r'dpx \+ 14\.0f;[^\n]*', 'dpx + 6.0f;\t\t// 6px Xbox-style corners'),
    (r'max\( qd, 0\.0f \) \) - 14\.0f;', 'max( qd, 0.0f ) ) - 6.0f;'),
    (r'saturate\( 2\.0f - abs\( d - 4\.5f \) \)', 'saturate( 2.5f - abs( d - 3.5f ) )'),
    # mip linear: deixa o desfoque do fundo mais suave quando a capa tem mipmaps
    (r'\tMaxAnisotropy = 16;\n', '\tMaxAnisotropy = 16;\n\tMipFilter = Linear;\n'),
    # passe de reflexo: em vez da capa "hero", a capa central em tela cheia e desfocada como fundo
    (r'\tif\( isMirror > 0\.5f \)\n\t\{\n.*?\n\t\}\n',
     '\tfloat bg = 0.0f;\n'
     '\tif( isMirror > 0.5f )\n'
     '\t{\n'
     '\t\t// Xbox Series: capa central ampliada em tela cheia (fundo desfocado), na Home e nos detalhes\n'
     '\t\tfloat2 tq = ( local - PG_RECT_MIN ) / ( PG_RECT_MAX - PG_RECT_MIN );\n'
     '\t\tpx  = float2( -16.0f + 1312.0f * tq.x, 736.0f - 752.0f * tq.y );\n'
     '\t\tvis = center;\n'
     '\t\tbg  = 1.0f;\n'
     '\t}\n'),
    (r'\tOutput\.PolarGlass = float4\( ppu\.x, center \* home, vis, [^\n]*?\);\n',
     lambda m: m.group(0) +
     '\tif( bg > 0.5f && vis > 0.001f )\n'
     '\t{\n'
     '\t\tOutput.PolarGlass = float4( 1.0f, -1.0f, vis, 1.0f );\t// y < 0: fundo desfocado\n'
     '\t\tOutput.Position.z = 0.995f;\t\t\t\t\t\t\t\t\t// atrás das capas\n'
     '\t}\n'),
    (r'(float4 PG_Shade\( VERTEX_TO_PIXEL Input \)\n\{\n\tclip\( [^\n]*?\);\n)',
     lambda m: m.group(1) +
     '\tif( Input.PolarGlass.y < -0.5f )\n'
     '\t{\n'
     '\t\t// fundo: frente da capa recortada em 16:9, desfocada e escurecida\n'
     '\t\tfloat2 tq = saturate( ( Input.PositionL.xy - PG_RECT_MIN ) / ( PG_RECT_MAX - PG_RECT_MIN ) );\n'
     '\t\tfloat2 uv = float2( 0.528f + tq.x * 0.471f, 0.71f - tq.y * 0.42f );\n'
     '\t\tconst float2 r = float2( 0.0044f, 0.0070f );\t// ~12 px\n'
     '\t\tfloat3 soft = ( PG_Tap( uv ) * 2.0f + PG_Tap( uv + float2( r.x, 0.0f ) ) + PG_Tap( uv - float2( r.x, 0.0f ) )\n'
     '\t\t             + PG_Tap( uv + float2( 0.0f, r.y ) ) + PG_Tap( uv - float2( 0.0f, r.y ) ) ) / 6.0f;\n'
     '\t\tfloat3 c = lerp( soft, PG_Blur( tq ), 0.90f );\t// desfoque a 90%\n'
     '\t\tfloat2 e = tq - 0.5f;\n'
     '\t\tfloat vig = ( 1.0f - 0.7f * dot( e, e ) ) * ( 0.55f + 0.45f * sin( 3.14159f * tq.y ) );\n'
     '\t\tc = lerp( dot( c, float3( 0.30f, 0.59f, 0.11f ) ).xxx, c, 0.75f );\n'
     '\t\treturn float4( c * 0.52f * vig, Input.PolarGlass.z );\n'
     '\t}\n'),
    # desfoque: 13 amostras em dois anéis, presas à frente da capa
    (r'(//-+\n// Polar Glass helpers\n//-+\n)',
     lambda m: m.group(1) +
     'inline float3 PG_Tap( float2 uv )\n'
     '{\n'
     '\tuv = clamp( uv, float2( 0.532f, 0.006f ), float2( 0.995f, 0.994f ) );\n'
     '\treturn tex2Dlod( TextureSampler, float4( uv, 0.0f, 0.0f ) ).rgb;\n'
     '}\n\n'
     '// desfoque total: a capa ampliada vira uma mistura suave das cores de uma grade 4x4.\n'
     '// As 16 leituras sao iguais para todos os pixels (cache), entao o custo e minimo.\n'
     'inline float PG_W( float t, float k ) { float d = t * 3.0f - k; return exp( -1.6f * d * d ); }\n\n'
     'inline float3 PG_Blur( float2 tq )\n'
     '{\n'
     '\tfloat3 c00, c10, c20, c30, c01, c11, c21, c31, c02, c12, c22, c32, c03, c13, c23, c33;\n'
     '\tc00 = PG_Tap( float2( 0.5869f, 0.1850f ) );\n'
     '\tc10 = PG_Tap( float2( 0.7046f, 0.1850f ) );\n'
     '\tc20 = PG_Tap( float2( 0.8224f, 0.1850f ) );\n'
     '\tc30 = PG_Tap( float2( 0.9401f, 0.1850f ) );\n'
     '\tc01 = PG_Tap( float2( 0.5869f, 0.3950f ) );\n'
     '\tc11 = PG_Tap( float2( 0.7046f, 0.3950f ) );\n'
     '\tc21 = PG_Tap( float2( 0.8224f, 0.3950f ) );\n'
     '\tc31 = PG_Tap( float2( 0.9401f, 0.3950f ) );\n'
     '\tc02 = PG_Tap( float2( 0.5869f, 0.6050f ) );\n'
     '\tc12 = PG_Tap( float2( 0.7046f, 0.6050f ) );\n'
     '\tc22 = PG_Tap( float2( 0.8224f, 0.6050f ) );\n'
     '\tc32 = PG_Tap( float2( 0.9401f, 0.6050f ) );\n'
     '\tc03 = PG_Tap( float2( 0.5869f, 0.8150f ) );\n'
     '\tc13 = PG_Tap( float2( 0.7046f, 0.8150f ) );\n'
     '\tc23 = PG_Tap( float2( 0.8224f, 0.8150f ) );\n'
     '\tc33 = PG_Tap( float2( 0.9401f, 0.8150f ) );\n'
     '\tfloat4 wx = float4( PG_W( tq.x, 0 ), PG_W( tq.x, 1 ), PG_W( tq.x, 2 ), PG_W( tq.x, 3 ) );\n'
     '\tfloat4 wy = float4( PG_W( 1.0f - tq.y, 0 ), PG_W( 1.0f - tq.y, 1 ), PG_W( 1.0f - tq.y, 2 ), PG_W( 1.0f - tq.y, 3 ) );\n'
     '\twx /= dot( wx, 1.0f ); wy /= dot( wy, 1.0f );\n'
     '\tfloat3 r0 = c00 * wx.x + c10 * wx.y + c20 * wx.z + c30 * wx.w;\n'
     '\tfloat3 r1 = c01 * wx.x + c11 * wx.y + c21 * wx.z + c31 * wx.w;\n'
     '\tfloat3 r2 = c02 * wx.x + c12 * wx.y + c22 * wx.z + c32 * wx.w;\n'
     '\tfloat3 r3 = c03 * wx.x + c13 * wx.y + c23 * wx.z + c33 * wx.w;\n'
     '\treturn r0 * wy.x + r1 * wy.y + r2 * wy.z + r3 * wy.w;\n'
     '}\n\n'),
    # entrada do pixel shader sem POSITION (exigência do perfil 3.0)
    (r'(struct VERTEX_TO_PIXEL\n\{.*?\n\};\n)',
     lambda m: m.group(1) + '\n'
     'struct PIXEL_IN\n'
     '{\n'
     '\tfloat4 Lights\t\t: COLOR0;\n'
     '\tfloat2 TexCoords\t: TEXCOORD0;\n'
     '\tfloat3 PositionL\t: TEXCOORD1;\n'
     '\tfloat3 PositionW\t: TEXCOORD2;\n'
     '\tfloat4 PolarGlass\t: TEXCOORD3;\n'
     '};\n'),
    (r'float4 PG_Shade\( VERTEX_TO_PIXEL Input \)', 'float4 PG_Shade( PIXEL_IN Input )'),
    (r'float4 CoverflowNormal_PS\( VERTEX_TO_PIXEL Input \)', 'float4 CoverflowNormal_PS( PIXEL_IN Input )'),
    (r'float4 CoverflowMirror_PS\( VERTEX_TO_PIXEL Input \)', 'float4 CoverflowMirror_PS( PIXEL_IN Input )'),
    # perfil 3.0: o desfoque passa do limite de instruções do 2.0
    (r'compile vs_2_0 CoverflowNormal_VS\(\)', 'compile vs_3_0 CoverflowNormal_VS()'),
    (r'compile ps_2_0 CoverflowNormal_PS\(\)', 'compile ps_3_0 CoverflowNormal_PS()'),
    (r'compile vs_2_0 CoverflowMirror_VS\(\)', 'compile vs_3_0 CoverflowMirror_VS()'),
    (r'compile ps_2_0 CoverflowMirror_PS\(\)', 'compile ps_3_0 CoverflowMirror_PS()'),
]


if ENABLE_CLOCK:
    # relógio: algarismos estilo Inter Bold (clockfont2.py) desenhados no passe do fundo desfocado,
    # o mesmo caminho do relógio que já apareceu no console (o v3, pela peça do estojo, não chegou à tela)
    from clockfont2 import hlsl as _clock_hlsl
    SHADER_EDITS += [
        (r'(inline float PG_ObjZ\(\)\n)', lambda m: _clock_hlsl() + m.group(1)),
        (r'Output\.PolarGlass = float4\( 1\.0f, -1\.0f, vis, 1\.0f \);',
         'Output.PolarGlass = float4( 1.0f, -1.0f, vis, home );'),
        # layout "Fundo do Jogo" (hora +30): o fundo do Aurora fica visível e o passe desenha só o relógio
        (r'(\t\t// fundo: frente da capa recortada em 16:9, desfocada e escurecida\n)',
         lambda m: m.group(1) +
         '\t\tif( g_fLightAttenuation.x > 29.5f )\n'
         '\t\t{\n'
         '\t\t\tfloat2 tk = ( Input.PositionL.xy - PG_RECT_MIN ) / ( PG_RECT_MAX - PG_RECT_MIN );\n'
         '\t\t\tfloat clk = Input.PolarGlass.w > 0.5f ? PG_Clock( float2( -16.0f + 1312.0f * tk.x, 736.0f - 752.0f * tk.y ) ) : 0.0f;\n'
         '\t\t\tclip( clk - 0.01f );\n'
         '\t\t\treturn float4( 0.96f, 0.96f, 0.96f, clk * Input.PolarGlass.z );\n'
         '\t\t}\n'),
        (r'\treturn float4\( c \* 0\.52f \* vig, Input\.PolarGlass\.z \);',
         '\tc *= 0.52f * vig;\n'
         '\t\tif( Input.PolarGlass.w > 0.5f )\n'
         '\t\t{\n'
         '\t\t\tfloat2 tr = ( Input.PositionL.xy - PG_RECT_MIN ) / ( PG_RECT_MAX - PG_RECT_MIN );\n'
         '\t\t\tfloat2 px = float2( -16.0f + 1312.0f * tr.x, 736.0f - 752.0f * tr.y );\n'
         '\t\t\tc = lerp( c, float3( 0.96f, 0.96f, 0.96f ), PG_Clock( px ) );\n'
         '\t\t}\n'
         '\t\treturn float4( c, Input.PolarGlass.z );'),
    ]
    # status do Aurora abaixo do relógio e indicador de disco mais abaixo
    MAIN_SIZES['StatusInfo'] = dict(w=720.0, h=60.0, pt=(30.0, 28.0), font='Inter SemiBold', style=0x4210)
    MAIN_VECTS.update({20: (856, 76), 8: (1116, 112), 66: (1116, 230)})


def patch_xpr_atlas(d):
    """Grava o atlas do relógio (Inter Bold) no lugar das 6 texturas de estojo (DXT5 512x512, lineares)."""
    import numpy as np
    from clockatlas import atlas
    from rxea import encode_bc3_alpha
    here = os.path.dirname(os.path.abspath(__file__))
    font = os.path.join(here, '..', 'build-input', 'Inter-Bold.ttf')
    if not os.path.exists(font):
        font = os.environ['XBOX_CLOCK_FONT']
    blk = encode_bc3_alpha(np.full((512, 512, 3), 255, np.uint8), atlas(font), 512, 512)
    d = bytearray(d)
    hdr = struct.unpack('>I', d[4:8])[0]; count = struct.unpack('>I', d[12:16])[0]
    for k in range(count):
        off = struct.unpack('>I', d[16+k*16+4:16+k*16+8])[0]
        name_off = struct.unpack('>I', d[16+k*16+12:16+k*16+16])[0]
        name = bytes(d[12+name_off:12+name_off+20]).split(b'\0')[0].decode()
        if not name.endswith('Case'):
            continue
        fc = struct.unpack('>6I', d[12+off+28:12+off+52])
        w = (fc[2] & 0x1fff) + 1; h = ((fc[2] >> 13) & 0x1fff) + 1; fmt = fc[1] & 0x3f
        assert (w, h, fmt) == (512, 512, 20), (name, w, h, fmt)
        base = (fc[1] >> 12) << 12
        start = 12 + hdr + base
        d[start:start+len(blk)] = blk
    return bytes(d)


def patch_shader(d):
    s = d.decode('ascii').replace('\r\n', '\n')
    for pat, new in SHADER_EDITS:
        s, n = re.subn(pat, new if callable(new) else (lambda m, new=new: new), s, flags=re.S)
        assert n == 1, pat
    s = s.replace('//  Author:         Phoenix (Default skin) - Polar Glass additions',
                  '//  Author:         Phoenix (Default skin) - Polar Glass additions - Xbox Series')
    # o compilador de shader do console espera ASCII: tira acentos dos comentarios
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return s.replace('\n', '\r\n').encode('ascii')


# ---------------------------------------------------------------- meta
def patch_meta(d):
    s = d.decode('ascii')
    s = re.sub(r'"skinname" : "[^"]*"', '"skinname" : "Xbox Series"', s)
    s = re.sub(r'"author" : "[^"]*"', '"author" : "Xbox Series"', s)
    s = re.sub(r'"description" : "[^"]*"',
               '"description" : "Inspirada na Home do Xbox Series: arte do jogo em tela cheia e capas com foco verde. Use com o layout de capas Xbox Series."', s)
    s = re.sub(r'"creationdate" : "[^"]*"', '"creationdate" : "2026-10-25"', s)
    return s.encode('ascii')


def build(src, dst, art, pieces=None):
    d, ds, count, tend, ents = parse(src)
    art_files = {
        'Images\\PolarGlass\\HomeChrome.png': 'HomeChrome.png',
        'Images\\PolarGlass\\Ground.png': 'Ground.png',
        'Images\\PolarGlass\\DetailsBackdrop.png': 'DetailsBackdrop.png',
        'Images\\Background\\Aurora.Background.jpg': 'DefaultBackground.jpg',
    }
    piece_files = set(os.listdir(pieces)) if pieces else set()
    blobs = []
    for name, size, off in ents:
        data = d[ds+off:ds+off+size]
        if name.endswith('.xur'):
            data = patch_screen(name, data)
        if name == 'Aurora_Skin.xur':
            data = patch_skin_templates(data)
        if name == 'Aurora_Main.xur':
            data = patch_main(data)
        elif name == 'Aurora_Loading.xur':
            data = replace_strings(data, LOADING_STRINGS, append=['Inter Light'])
            data = patch_main(data, LOADING_VECTS, LOADING_SIZES, toolbar=False)
        elif name == 'Shaders\\CoverflowShader.fx':
            data = patch_shader(data)
        elif name == 'skin.meta':
            data = patch_meta(data)
        elif False and name == 'Textures\\Coverflow.xpr':   # atlas do v3 desligado
            data = patch_xpr_atlas(data)
        elif name in art_files:
            data = open(os.path.join(art, art_files[name]), 'rb').read()
        elif name in piece_files:
            data = open(os.path.join(pieces, name), 'rb').read()
        blobs.append((name, data))
    for name, f in SPLASH_FILES.items():
        blobs.append((name, open(os.path.join(art, f), 'rb').read()))
    table = bytearray(); off = 0
    for name, data in blobs:
        table += struct.pack('>II', len(data), off) + bytes([len(name)]) + name.encode('utf-16-be')
        off += len(data)
    hdr = bytearray(d[:0x16])
    hdr[0x10:0x14] = struct.pack('>I', len(table))   # tamanho da tabela de arquivos
    hdr[0x14:0x16] = struct.pack('>H', len(blobs))
    total = 0x16 + len(table) + off
    hdr[8:12] = struct.pack('>I', total)
    open(dst, 'wb').write(bytes(hdr) + bytes(table) + b''.join(x for _, x in blobs))


if __name__ == '__main__':
    build(*sys.argv[1:5])
