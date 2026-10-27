"""Gera o código HLSL do relógio da Home a partir de clockfont.py (só traços retos, sem desvios por traço)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from clockfont import SEGS, DIGITS, HALF


def hlsl():
    m0 = {n: sum(1 << s for s in segs if s < 16) for n, segs in DIGITS.items()}
    m1 = {n: sum(1 << (s - 16) for s in segs if s >= 16) for n, segs in DIGITS.items()}
    def chain(m):
        return ' : '.join('n < %d.5f ? %d.0f' % (k, m[k]) for k in range(9)) + ' : %d.0f' % m[9]
    L = []
    L.append('// ---- relogio da Home (24 h): algarismos de tracos retos com cantos chanfrados')
    L.append('inline float PG_Seg( float2 p, float2 a, float2 b )')
    L.append('{')
    L.append('\tfloat2 pa = p - a, ba = b - a;')
    L.append('\tfloat h = saturate( dot( pa, ba ) / dot( ba, ba ) );')
    L.append('\treturn length( pa - ba * h );')
    L.append('}')
    L.append('')
    L.append('inline float PG_Bit( float m, float b ) { return fmod( floor( m / b ), 2.0f ); }')
    L.append('')
    L.append('// p: pixel relativo ao canto do algarismo (20 x 30 px); retorna cobertura 0..1')
    L.append('inline float PG_Digit( float2 p, float n )')
    L.append('{')
    L.append('\tfloat m0 = %s;' % chain(m0))
    L.append('\tfloat m1 = %s;' % chain(m1))
    L.append('\tfloat d = 1000.0f;')
    for k, (a, b) in enumerate(SEGS):
        m, bit = ('m0', 1 << k) if k < 16 else ('m1', 1 << (k - 16))
        L.append('\td = min( d, PG_Seg( p, float2( %.1ff, %.1ff ), float2( %.1ff, %.1ff ) ) + ( 1.0f - PG_Bit( %s, %d.0f ) ) * 1000.0f );'
                 % (a[0], a[1], b[0], b[1], m, bit))
    L.append('\treturn saturate( %.2ff - d );\t// traco de ~%.1f px com borda suave' % (0.5 + HALF, 2 * HALF))
    L.append('}')
    L.append('')
    L.append('// cobertura do relogio HH:MM no pixel px (tela 1280x720); 0 se a hora de inicio nao foi gravada')
    L.append('inline float PG_Clock( float2 px )')
    L.append('{')
    L.append('\tfloat3 a = g_fLightAttenuation;')
    L.append('\tbool ok = a.x >= 0.0f && a.x < 24.0f && a.y >= 0.0f && a.y < 60.0f && a.z >= 0.0f && a.z < 60.0f &&')
    L.append('\t          abs( a.x - floor( a.x + 0.5f ) ) < 0.01f && abs( a.y - floor( a.y + 0.5f ) ) < 0.01f;')
    L.append('\tconst float2 org = float2( 1118.0f, 41.0f );\t// termina em x=1216, centro em y=56')
    L.append('\tfloat2 q = px - org;')
    L.append('\tif( !ok || q.x < -4.0f || q.x > 102.0f || q.y < -4.0f || q.y > 34.0f ) return 0.0f;')
    L.append('\tfloat t = fmod( a.x * 3600.0f + a.y * 60.0f + a.z + g_fApplicationTime, 86400.0f );')
    L.append('\tfloat hh = floor( t / 3600.0f ), mm = floor( fmod( t, 3600.0f ) / 60.0f );')
    L.append('\t// um algarismo por pixel: escolhe a casa pela posicao x (0, 22 | dois-pontos 49 | 56, 78)')
    L.append('\tfloat x0 = q.x < 21.0f ? 0.0f : q.x < 44.0f ? 22.0f : q.x < 66.0f ? 56.0f : 78.0f;')
    L.append('\tfloat n = q.x < 21.0f ? floor( hh / 10.0f ) : q.x < 44.0f ? fmod( hh, 10.0f ) : q.x < 66.0f ? floor( mm / 10.0f ) : fmod( mm, 10.0f );')
    L.append('\tfloat c = ( q.x > 44.0f && q.x < 54.0f ) ? 0.0f : PG_Digit( q - float2( x0, 0.0f ), n );')
    L.append('\tc = max( c, saturate( 3.2f - length( q - float2( 49.0f, 10.5f ) ) ) );')
    L.append('\tc = max( c, saturate( 3.2f - length( q - float2( 49.0f, 22.5f ) ) ) );')
    L.append('\treturn c;')
    L.append('}')
    return '\n'.join(L) + '\n\n'


if __name__ == '__main__':
    print(hlsl())
