"""Xbox Series + menus da Clean NXE.

A Clean NXE (Jayshai) é a base: todas as telas internas, peças e fontes Segoe dela.
Da Xbox Series vêm a tela inicial (com detalhes), a abertura, o shader/texturas das capas,
os modelos visuais da Home e as imagens que eles usam, as fontes Inter e as configurações de capas.

uso: python merge_nxe.py <CleanNXE.xzp> <XboxSeries.xzp> <saida.xzp>
"""
import os, re, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xzp import parse
import xur5

# cenas e arquivos que são nossos
OUR_FILES = ['Aurora_Main.xur', 'Aurora_Loading.xur', 'Shaders\\CoverflowShader.fx', 'skin.meta']
# modelos visuais da Home (os genéricos XuiButton/XuiImage/XuiScene/XuiNone ficam os da NXE)
OUR_VISUALS = ['Notification', 'PG_CTA_A', 'PG_CTA_Y', 'XuiDiscIndicator',
               'XuiControl_DiscIcon', 'XuiControl_DiscPanelX', 'XuiControl_DiscPanelY', 'XuiControl_NoDisc',
               'XuiControl_ReadingDisc', 'XuiControl_Grey', 'XuiControl_White',
               'XuiControl_ProfileAvatar', 'XuiControl_ProfilePicture',
               # barras em verde sólido (as da NXE são degradês em várias peças)
               'XuiProgressBar', 'XuiProgressBar_White', 'XuiSlider', 'XuiSlider_CustomCounter', 'XuiLoading',
               'XuiTempBar_Blue', 'XuiTempBar_Green', 'XuiTempBar_Yellow', 'XuiTempBar_Red',
               # listas que na NXE saem com texto enorme no console; as da Liquid Glass têm o tamanho certo
               'XuiButton_FileManager_List', 'XuiButton_Skin',
               # botão genérico e texto rolante seguem a convenção do Aurora (texto txtMain, escala 0,5): sem eles o
               # item com foco de texto longo ("Gerenciador de arquivos") sai gigante
               'XuiButton', 'XuiHorizontalTextScroller']
# prefixos de imagens que levamos inteiros (ícones do controle valem para a skin toda)
OUR_PREFIXES = ['Images\\PolarGlass\\', 'Images\\XboxSeries\\', 'Images\\Visuals\\XuiGamepad\\',
                'Images\\Icons\\DVDPanel\\', 'Images\\Icons\\Notification\\', 'Images\\Icons\\ProfilePanel\\',
                'Images\\Visuals\\XuiDiscIndicator\\', 'Fonts\\Inter', 'Textures\\', 'Images\\Background\\']


# textos que só aparecem nas telas da Clean NXE (o resto vem de ptbr.T)
EXTRA_PT = {
    'Avatar as Profile Picture': 'Avatar como foto do perfil', 'Cheats': 'Trapaças', 'Move': 'Mover',
    'Letterbox on 4:3 Screen': 'Faixas pretas em tela 4:3', 'NXE Stage & Rings': 'Palco e anéis NXE',
    'Profile & Disc Panel': 'Painel de perfil e disco', 'Run Main.lua on Boot': 'Executar Main.lua ao iniciar',
    'Start': 'Iniciar', 'Warning': 'Aviso', 'Unity Marketplace': 'Unity Marketplace',
}


def translate(b):
    """Traduz só as propriedades Text (inclusive nos quadros-chave); IDs que usam a mesma string não mudam."""
    from ptbr import T
    table = dict(T); table.update(EXTRA_PT)
    x = xur5.Xur(b); n = [0]
    def tr(v):
        s = x.strings[v[1]]
        if s in table and table[s] != s:
            n[0] += 1; return ('s', x.str_index(table[s]))
        return v
    def walk(o):
        if o.props:
            o.props = (o.props[0], [(pb, m, [(pd, tr(v) if pd.name == 'Text' and v[0] == 's' else v) for pd, v in vals])
                                    for pb, m, vals in o.props[1]])
        for c in o.children: walk(c)
        if o.timelines:
            o.timelines = [(el, defs, [(h, [tr(v) if pd.name == 'Text' and v[0] == 's' else v for pd, v in zip(pdl, vs)])
                                       for h, vs in kfs], pdl) for el, defs, kfs, pdl in o.timelines]
    walk(x.root)
    return (x.build(), n[0]) if n[0] else (b, 0)


LIME = (0x9e, 0xc2, 0x4f)


def lime_like(r, g, b):
    """Verde/turquesa da NXE -> limão #9EC24F, mantendo o brilho relativo."""
    import colorsys
    h, sat, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if sat < 0.3 or not (60 / 360 <= h <= 175 / 360):
        return None
    lh, ls, lv = colorsys.rgb_to_hsv(*(c / 255 for c in LIME))
    nv = max(0.25, min(1.0, lv * v / 0.75))
    return tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(lh, ls, nv))


SOLID_LIME = bytes([0xff, *LIME])
NXE_TEXT_SCALE = 0.75     # Inter é mais larga que a Segoe da NXE; textos em pt-BR também são mais longos
# reduções extras (multiplicam a geral): títulos e as listas do gerenciador de arquivos e do seletor de skins
NXE_TEXT_EXTRA = {'XuiLabel_Heading_': 0.85, 'XuiButton_FileManager_List': 0.9, 'XuiButton_Skin': 0.9,
                  'XuiButton_ScanPath': 0.85}


def scale_text(b, skip=()):
    """Reduz o tamanho (PointSize) dos textos das telas/modelos da NXE."""
    import struct as st
    x = xur5.Xur(b); n = [0]
    def ps(pd, v, f):
        if pd.name == 'PointSize' and v[0] == 'b':
            n[0] += 1
            return ('b', st.pack('>f', round(st.unpack('>f', v[1])[0] * f * 2) / 2))
        return v
    def walk(o, f):
        if o.props:
            o.props = (o.props[0], [(pb, m, [(pd, ps(pd, v, f)) for pd, v in vals]) for pb, m, vals in o.props[1]])
        for c in o.children: walk(c, f)
        if o.timelines:
            o.timelines = [(el, defs, [(h, [ps(pd, v, f) for pd, v in zip(pdl, vs)]) for h, vs in kfs], pdl)
                           for el, defs, kfs, pdl in o.timelines]
    for c in x.root.children if skip else [x.root]:
        name = c.id(x) or ''
        if name in skip: continue
        extra = next((k for pre, k in NXE_TEXT_EXTRA.items() if name.startswith(pre)), 1.0)
        walk(c, NXE_TEXT_SCALE * extra)
    return (x.build(), n[0]) if n[0] else (b, 0)


def green_gradient(fill):
    for p, v in fill[4]:
        if p.name == 'Gradient' and v[0] == 'o':
            for p2, v2 in v[4]:
                if p2.name == 'StopColor' and v2[0] == 'x':
                    if any(s[0] == 'b' and s[1][0] > 0x40 and lime_like(*s[1][1:]) for s in v2[2]):
                        return True
    return False


def solid_lime_fill(fill):
    """Degradê verde da NXE -> verde-limão sólido (como as barras de temperatura)."""
    def walk(p, v):
        if v[0] == 'o':
            return ('o', v[1], v[2], v[3], [(p2, walk(p2, v2)) for p2, v2 in v[4]])
        if v[0] == 'x' and p.name == 'StopColor':
            return ('x', v[1], [('b', SOLID_LIME) for _ in v[2]])
        if p.name == 'FillColor':
            return ('b', SOLID_LIME)
        return v
    return walk(None, fill)


def recolor_xur(b, skip=()):
    x = xur5.Xur(b); n = [0]
    def col(pd, v):
        if v[0] == 'b' and pd.type == 'color':
            a, r, g, bb = v[1]
            m = lime_like(r, g, bb)
            if m: n[0] += 1; return ('b', bytes([a, *m]))
        elif v[0] == 'o':
            if pd.name == 'Fill' and green_gradient(v):
                n[0] += 1; return solid_lime_fill(v)
            return ('o', v[1], v[2], v[3], [(p2, col(p2, v2)) for p2, v2 in v[4]])
        elif v[0] == 'x':
            return ('x', v[1], [col(pd, v2) for v2 in v[2]])
        return v
    def walk(o):
        if o.props:
            o.props = (o.props[0], [(pb, m, [(pd, col(pd, v)) for pd, v in vals]) for pb, m, vals in o.props[1]])
        for c in o.children: walk(c)
        if o.timelines:
            o.timelines = [(el, defs, [(h, [col(pd, v) for pd, v in zip(pdl, vs)]) for h, vs in kfs], pdl)
                           for el, defs, kfs, pdl in o.timelines]
    for c in x.root.children if skip else [x.root]:
        if c.id(x) not in skip: walk(c)
    return x.build() if n[0] else b


def recolor_image(b, name):
    import io, numpy as np
    from PIL import Image
    im = Image.open(io.BytesIO(b)); fmt = im.format; mode = im.mode
    a = np.asarray(im.convert('RGBA')).astype(np.float32) / 255
    rgb = a[..., :3]; mx = rgb.max(-1); mn = rgb.min(-1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, bb = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - bb) / d) % 6, np.where(mx == g, (bb - r) / d + 2, (r - g) / d + 4)) * 60
    blue = (hue >= 180) & (hue <= 265) & (sat > 0.15)
    green = (hue >= 60) & (hue <= 175) & (sat > 0.3)
    out = rgb.copy()
    gray = (0.30 * r + 0.59 * g + 0.11 * bb)[..., None]
    out[blue] = np.repeat(gray[blue] * 0.55, 3, -1) + np.array([0.0, 0.0, 0.004])   # grafite
    lime = np.array(LIME) / 255
    out[green] = np.clip(lime[None] * (mx[green] / 0.76)[:, None], 0, 1)
    if not (blue.any() or green.any()):
        return b
    a[..., :3] = out
    res = Image.fromarray((a * 255 + 0.5).astype(np.uint8), 'RGBA')
    buf = io.BytesIO()
    if fmt == 'JPEG':
        res.convert('RGB').save(buf, 'JPEG', quality=92)
    else:
        (res if 'A' in mode or mode == 'P' else res.convert('RGB')).save(buf, 'PNG', optimize=True)
    return buf.getvalue()


PANEL_BLACK = (11, 11, 11)


def solid_panel(b):
    import io, numpy as np
    from PIL import Image
    a = np.asarray(Image.open(io.BytesIO(b)).convert('RGBA')).copy()
    alpha = a[..., 3]
    a[..., :3] = PANEL_BLACK
    a[..., 3] = np.where(alpha > 128, 255, alpha)          # miolo opaco, borda arredondada preservada
    buf = io.BytesIO(); Image.fromarray(a, 'RGBA').save(buf, 'PNG', optimize=True); return buf.getvalue()


def clear_png(b):
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(b)); buf = io.BytesIO()
    Image.new('RGBA', im.size, (0, 0, 0, 0)).save(buf, 'PNG'); return buf.getvalue()


def resize_jpg(b, size):
    import io
    from PIL import Image
    buf = io.BytesIO(); Image.open(io.BytesIO(b)).convert('RGB').resize(size, Image.LANCZOS).save(buf, 'JPEG', quality=92)
    return buf.getvalue()


def png_size(b):
    return struct.unpack('>II', b[16:24]) if b[:8] == b'\x89PNG\r\n\x1a\n' else None


def entries(path):
    d, ds, _, _, ents = parse(path)
    return {n: d[ds+o:ds+o+s] for n, s, o in ents}, [n for n, _, _ in ents], d[:0x16]


def gamepad_visuals(x):
    return [c.id(x) for c in x.root.children if (c.id(x) or '').startswith('XuiGamepad')]


def visuals_used(b):
    x = xur5.Xur(b); u = set()
    def walk(o):
        u.add(x.strings[o.cls]); v = o.prop(x, 'Visual')
        if v: u.add(x.strings[v[1]])
        for c in o.children: walk(c)
    walk(x.root)
    return u


def details_visuals(nxe, ours):
    """Modelos que nossas telas de detalhes usam e que nenhuma outra tela da NXE usa (podem ser trocados sem efeito colateral)."""
    ours_skin = {c.id(x) for x in [xur5.Xur(ours['Aurora_Skin.xur'])] for c in x.root.children}
    need = set()
    for n, b in ours.items():
        if n.startswith('Game_Options') and n.endswith('.xur'):
            need |= visuals_used(b) & ours_skin
    others = set()
    for n, b in nxe.items():
        if n.endswith('.xur') and '\\' not in n and not n.startswith('Game_Options') and n != 'Aurora_Skin.xur':
            others |= visuals_used(b)
    nxe_skin = {c.id(x) for x in [xur5.Xur(nxe['Aurora_Skin.xur'])] for c in x.root.children}
    return sorted(v for v in need if (v not in others or v not in nxe_skin) and not v.startswith('XuiGamepad'))


FOCUS_TEXT = bytes.fromhex('ff111114')      # texto sobre a pílula clara (igual aos detalhes)
NEUTRAL_TEXT = bytes.fromhex('ff8a8c99')    # textos sem animação de cor: legíveis com e sem foco


def prop_count(levels):
    return sum(len(vals) for _, _, vals in levels)


def focus_ranges(x, v):
    fr = {x.strings[a]: b for a, b, c, d in (v.frames or [])}
    out = []
    for name, start in fr.items():
        if ('Focus' in name or name == 'Press') and not name.startswith(('End', 'Kill')) and name != 'FocusLoop':
            end = fr.get('End' + name)
            if end is not None: out.append((start, end))
    return out


def restyle_buttons(dst, src):
    """Botões da NXE com o foco dos detalhes da Xbox Series: pílula clara (Round10_Accent) e texto escuro."""
    rail = [c for c in src.root.children if c.id(src) == 'PG_Rail_GameLaunch'][0]
    pill_src = [c for c in rail.children if c.id(src) == 'bgFocus'][0]
    done = []
    for v in dst.root.children:
        gb = [c for c in v.children if (c.id(dst) or '').startswith('greenBox')]
        if not gb or (v.id(dst) or '') in OUR_VISUALS:
            continue
        g = gb[0]; gid = g.id(dst)
        tls = v.timelines or []
        ok = all(all(ci == len(xur5.hierarchy(dst.strings[g.cls])) - 1 for _, ci, _, _ in defs)
                 for el, defs, _, _ in tls if dst.strings[el] == gid)
        if not ok:
            continue
        pill = xur5.relocate(pill_src, src, dst)
        # nível XuiElement: Id/âncora/opacidade do greenBox, mas na área real do botão (sem a margem do brilho)
        import struct as st
        W = st.unpack('>f', g.prop(dst, 'Width')[1])[0]; H = st.unpack('>f', g.prop(dst, 'Height')[1])[0]
        px, py, pz = st.unpack('>3f', dst.vects[g.prop(dst, 'Position')[1]])
        pb, masks, vals = g.props[1][0]
        new = []
        for pd, val in vals:
            if pd.name == 'Width': val = ('b', st.pack('>f', W + 2 * px))
            elif pd.name == 'Height': val = ('b', st.pack('>f', H + 2 * py))
            elif pd.name == 'Position': val = ('v', dst.vect_index(st.pack('>3f', 0.0, 0.0, pz)))
            new.append((pd, val))
        levels = [(pb, masks, new)] + pill.props[1][1:]
        pill.props = (prop_count(levels), levels)
        # tira os brilhos da NXE
        drop = {c.id(dst) for c in v.children if (c.id(dst) or '').startswith(('Highlight', 'highlightBox', 'Shine'))}
        v.children = [pill if c is g else c for c in v.children if c.id(dst) not in drop]
        ranges = focus_ranges(dst, v)
        texts = {c.id(dst): c for c in v.children if dst.strings[c.cls] in ('XuiTextPresenter', 'XuiText', 'XuiMarqueePresenter')}
        new_tls, animated = [], set()
        for el, defs, kfs, pdl in tls:
            name = dst.strings[el]
            if name in drop:
                continue
            if name in texts and any(pd.name == 'TextColor' for pd in pdl):
                animated.add(name)
                kfs2 = []
                for head, vs in kfs:
                    fno = int.from_bytes(head[:4], 'big', signed=True)
                    if any(a <= fno <= b for a, b in ranges):
                        vs = [('b', FOCUS_TEXT) if pd.name == 'TextColor' else
                              ('b', bytes(4)) if pd.name == 'DropShadowColor' else vv for pd, vv in zip(pdl, vs)]
                    kfs2.append((head, vs))
                kfs = kfs2
            new_tls.append((el, defs, kfs, pdl))
        v.timelines = new_tls
        for name, t in texts.items():
            if name not in animated and t.props:
                t.props = (t.props[0], [(pb2, m2, [(pd, ('b', NEUTRAL_TEXT) if pd.name == 'TextColor' else vv) for pd, vv in vals2])
                                        for pb2, m2, vals2 in t.props[1]])
        done.append(v.id(dst))
    return done


def fix_text_scroller(dst):
    """Texto rolante do item com foco: no console a escala 0,5 da NXE é ignorada e o texto sai gigante.
    Deixa os textos em escala 1, do tamanho dos botões (13,5) e na caixa real (400 x 28)."""
    import struct as st
    v = [c for c in dst.root.children if c.id(dst) == 'XuiHorizontalTextScroller']
    if not v:
        return 0
    n = 0
    for c in v[0].children:
        if c.id(dst) not in ('MainText', 'SubText', 'Main', 'Sub'):
            continue
        new_levels = []
        for pb, m, vals in c.props[1]:
            out = []
            for pd, val in vals:
                if pd.name == 'Width': val = ('b', st.pack('>f', 400.0))
                elif pd.name == 'Height': val = ('b', st.pack('>f', 28.0))
                elif pd.name == 'Scale': val = ('v', dst.vect_index(st.pack('>3f', 1.0, 1.0, 1.0)))
                elif pd.name == 'PointSize': val = ('b', st.pack('>f', 13.5))
                out.append((pd, val))
            new_levels.append((pb, m, out))
        c.props = (c.props[0], new_levels); n += 1
    return n


FIXED_BUTTONS = {'XuiButton', 'XuiButton_SettingsCategory', 'XuiButton_SettingsCategory_Static',
                 'XuiButton_TextField', 'XuiButton_BasicString'}


def lg_list_items(nxe_b, ours_b):
    """Itens de lista que o Aurora preenche sozinho (com presenters). Os da NXE saem com texto gigante no console;
    os da Liquid Glass (nossa 1.0) têm o tamanho certo, então usamos esses quando existem."""
    n = xur5.Xur(nxe_b); o = xur5.Xur(ours_b)
    ov = {c.id(o) for c in o.root.children}
    out = []
    for v in n.root.children:
        name = v.id(n) or ''
        if not name.startswith(('XuiButton_', 'XuiCheckbox_')) or name in FIXED_BUTTONS or name not in ov:
            continue
        if any(n.strings[c.cls] in ('XuiTextPresenter', 'XuiMarqueePresenter', 'XuiImagePresenter') for c in v.children):
            out.append(name)
    return out


def merge_skin(nxe_b, ours_b, extra=()):
    dst = xur5.Xur(nxe_b); src = xur5.Xur(ours_b)
    srcv = {c.id(src): c for c in src.root.children}
    want = OUR_VISUALS + gamepad_visuals(src) + [v for v in extra if v not in OUR_VISUALS]
    idx = {c.id(dst): i for i, c in enumerate(dst.root.children)}
    added, replaced = [], []
    for name in want:
        if name not in srcv:
            continue
        obj = xur5.relocate(srcv[name], src, dst)
        if name in idx:
            dst.root.children[idx[name]] = obj; replaced.append(name)
        else:
            dst.root.children.append(obj); added.append(name)
    styled = restyle_buttons(dst, src)
    print('botões com o foco dos detalhes:', len(styled))
    out = dst.build()
    xur5.Xur(out)                                    # relê para garantir que ficou válido
    return out, added, replaced


def merge_skin_xml(nxe_x, ours_x):
    n = nxe_x.decode('utf-8-sig'); o = ours_x.decode('utf-8-sig')
    # fontes: as da NXE (Segoe, padrão) + as Inter da Xbox Series
    inter = ['\t\t\t' + l + '\n' for l in re.findall(r'<font name="Inter[^\n]*?/>', o)]
    inter = [l.replace('default="true"', 'default="false"') for l in inter]
    n = re.sub(r'[ \t]*</fonts>', lambda m: ''.join(inter) + m.group(0), n, count=1)
    # nomes Segoe da NXE apontando para os arquivos Inter (identidade da Xbox Series)
    for seg, inter in (('segoeui_r.ttf', 'Inter-Regular.ttf'), ('segoeuib_r.ttf', 'Inter-Bold.ttf'),
                       ('seguibl_r.ttf', 'Inter-Bold.ttf'), ('seguisb_r.ttf', 'Inter-SemiBold.ttf')):
        n = n.replace('file="Fonts/%s"' % seg, 'file="Fonts/%s"' % inter)
    # sem contadores de FPS/CPU/memória na tela
    for tag in ('name', 'fps', 'cpu', 'mem'):
        n = re.sub(r'<%s>[^<]*</%s>' % (tag, tag), '<%s>FALSE</%s>' % (tag, tag), n, count=1)
    # capas: a seção da Xbox Series (shader, texturas e layouts)
    cf = re.search(r'<CoverFlow>.*?</CoverFlow>', o, re.S).group(0)
    n = re.sub(r'<CoverFlow>.*?</CoverFlow>', lambda m: cf, n, count=1, flags=re.S)
    # fundo: permite o fundo do jogo
    bg = re.search(r'[ \t]*<Background>.*?</Background>\r?\n', o, re.S)
    if bg and '<Background>' not in n:                # dentro de <settings>, logo após a lista de módulos
        k = n.index('</ModuleList>') + len('</ModuleList>')
        k = n.index('\n', k) + 1
        n = n[:k] + bg.group(0) + n[k:]
    return n.encode('utf-8')


def build(nxe_path, ours_path, dst):
    nxe, nxe_order, hdr = entries(nxe_path)
    ours, ours_order, _ = entries(ours_path)
    files = dict(nxe); order = list(nxe_order)

    def put(name, data):
        if name not in files: order.append(name)
        files[name] = data

    for v in lg_list_items(nxe['Aurora_Skin.xur'], ours['Aurora_Skin.xur']):
        if v not in OUR_VISUALS: OUR_VISUALS.append(v)
    for name in OUR_FILES + [n for n in ours_order if n.startswith('Game_Options') and n.endswith('.xur')]:
        put(name, ours[name])
    for name in ours_order:
        if any(name.startswith(p) for p in OUR_PREFIXES):
            put(name, ours[name])
        elif name.startswith('Images\\') and name in nxe and len(ours[name]) > 0 and png_size(ours[name]) == png_size(nxe[name]):
            put(name, ours[name])             # peças recoloridas da Xbox Series com o mesmo tamanho da NXE
    meta = ours['skin.meta'].decode('utf-8', 'replace').rstrip('\x00')
    meta = re.sub(r'"description" : "[^"]*"', '"description" : "A Home do Xbox Series no Xbox 360: arte do jogo em tela cheia, capas com foco verde e relógio. Criada por Dimas Silva."', meta)
    meta = re.sub(r'"author" : "[^"]*"', '"author" : "Dimas Silva"', meta)
    meta = re.sub(r'"revision" : \d+', '"revision" : 2', meta)
    put('skin.meta', meta.encode('utf-8'))
    preview = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build-input', 'art', 'Preview.dds')
    if not os.path.exists(preview):
        preview = os.environ.get('XBOX_PREVIEW', '')
    if preview and os.path.exists(preview):
        for n in [n for n in order if n.lower() == 'preview.dds']:
            put(n, open(preview, 'rb').read())
    det = details_visuals(nxe, ours)
    skin, added, replaced = merge_skin(nxe['Aurora_Skin.xur'], ours['Aurora_Skin.xur'], det)
    skin = recolor_xur(skin, skip=set(OUR_VISUALS) | set(det))
    skin, k = scale_text(skin, skip=set(OUR_VISUALS) | set(det) | set(gamepad_visuals(xur5.Xur(ours['Aurora_Skin.xur']))) | {'PG_CTA_A', 'PG_CTA_Y', 'XuiHorizontalTextScroller'})
    print('textos reduzidos nos modelos da NXE:', k)
    put('Aurora_Skin.xur', skin)
    put('skin.xml', merge_skin_xml(nxe['skin.xml'], ours['skin.xml']))
    total = 0
    for name in order:
        if name.endswith('.xur') and name not in OUR_FILES and '\\' not in name and not name.startswith('Game_Options'):
            files[name], k = translate(files[name]); total += k
            if name != 'Aurora_Skin.xur':
                files[name] = recolor_xur(files[name])
                files[name], _ = scale_text(files[name])
    # imagens que continuam da NXE: azul vira grafite, verde vira o limão da Xbox Series
    from_ours = {n for n in order if n in ours and files[n] == ours[n]}
    nimg = 0
    for name in order:
        if name.startswith('Images\\') and name not in from_ours and name.lower().endswith(('.png', '.jpg')):
            files[name] = recolor_image(files[name], name); nimg += 1
    if 'Images\\Background\\Startup.Background.JPG' in files:
        files['Images\\Background\\Startup.Background.JPG'] = resize_jpg(ours['Images\\Background\\Aurora.Background.jpg'], (1280, 720))
    print('imagens da NXE recoloridas:', nimg)
    # painel dos menus internos: preto sólido como nos detalhes; sem o reflexo brilhante
    for name in ('Images\\Visuals\\BackgroundPanel.png', 'Images\\Visuals\\BackgroundPanelAlt.png'):
        if name in files: files[name] = solid_panel(nxe[name])
    if 'Images\\Visuals\\PanelReflect.png' in files:
        files['Images\\Visuals\\PanelReflect.png'] = clear_png(nxe['Images\\Visuals\\PanelReflect.png'])
    print('textos traduzidos:', total)
    # textura de capas: a NXE chama de CoverFlow.xpr; a nossa seção do skin.xml aponta o nome certo
    blobs = [(n, files[n]) for n in order]
    table = bytearray(); off = 0
    for name, data in blobs:
        table += struct.pack('>II', len(data), off) + bytes([len(name)]) + name.encode('utf-16-be')
        off += len(data)
    h = bytearray(hdr)
    h[0x10:0x14] = struct.pack('>I', len(table)); h[0x14:0x16] = struct.pack('>H', len(blobs))
    h[8:12] = struct.pack('>I', 0x16 + len(table) + off)
    open(dst, 'wb').write(bytes(h) + bytes(table) + b''.join(x for _, x in blobs))
    return added, replaced, len(blobs)


if __name__ == '__main__':
    a, r, n = build(*sys.argv[1:4])
    print('modelos adicionados:', a); print('modelos trocados:', r); print(n, 'arquivos')
