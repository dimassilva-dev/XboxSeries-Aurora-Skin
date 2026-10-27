"""Leitor/gravador completo de XUR v5 (XUIB) — formato conforme o XUIHelper (SGCSam).
Distribuído sob a GNU GPL 3.0, como o XUIHelper (veja licenses/GPL-3.0.txt).

Mantém os valores como referências às tabelas do próprio arquivo (STRN/VECT/QUAT/CUST), o que permite
regravar o arquivo byte a byte e copiar objetos entre arquivos remapeando as referências (relocate).
"""
import struct, os, glob, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CLASS_DIR = os.environ.get('XUR5_CLASSES', os.path.join(HERE, 'xur5classes'))

SIZES = {'bool': 1, 'integer': 4, 'unsigned': 4, 'float': 4, 'color': 4,
         'string': 2, 'vector': 4, 'quaternion': 4, 'custom': 4}
REF = {'string': 's', 'vector': 'v', 'quaternion': 'q', 'custom': 'c'}
COMPOUND = {'Fill': 'XuiFigureFill', 'Gradient': 'XuiFigureFillGradient', 'Stroke': 'XuiFigureStroke'}


class PropDef:
    def __init__(self, name, typ, flags):
        self.name, self.type, self.indexed = name, typ, 'indexed' in flags


def load_classes(d=CLASS_DIR):
    classes = {}
    for f in sorted(glob.glob(os.path.join(d, '*.xml'))):
        for c in ET.parse(f).getroot().iter('XUIClass'):
            classes[c.get('Name')] = (c.get('BaseClassName'),
                                      [PropDef(p.get('Name'), p.get('Type'), p.get('Flags') or '') for p in c.findall('PropDef')])
    return classes


CLASSES = load_classes()


def hierarchy(name):
    out = []
    while name and name != '(null)':
        if name not in CLASSES:
            raise KeyError('classe desconhecida: %s' % name)
        out.append(name); name = CLASSES[name][0]
    return out[::-1]                     # base primeiro


class R:
    def __init__(self, d, p=0): self.d, self.p = d, p
    def u8(self): v = self.d[self.p]; self.p += 1; return v
    def i16(self): v = struct.unpack('>h', self.d[self.p:self.p+2])[0]; self.p += 2; return v
    def i32(self): v = struct.unpack('>i', self.d[self.p:self.p+4])[0]; self.p += 4; return v
    def raw(self, n): v = self.d[self.p:self.p+n]; self.p += n; return v


# ---- valores: ('s'|'v'|'q'|'c', índice) para referências, ('b', bytes) para valores literais,
#      ('o', count, depth, masks, [valores]) para objetos compostos, ('x', n, [valores]) para indexados
def read_value(r, pd, indexed=True):
    if indexed and pd.indexed:
        n = r.u8()
        return ('x', n, [read_value(r, pd, False) for _ in range(n)])
    t = pd.type
    if t == 'object':
        cnt = r.i16(); depth = r.u8()
        cls = CLASSES[COMPOUND[pd.name]][1]
        nm = max((len(cls) + 7) // 8, 1)
        masks = r.raw(nm)
        vals = []
        for i, m in enumerate(masks[::-1]):
            for k, sub in enumerate(cls[i*8:i*8+8]):
                if m & (1 << k):
                    vals.append((sub, read_value(r, sub)))
        return ('o', cnt, depth, masks, vals)
    if t in REF:
        return (REF[t], r.i16() if t == 'string' else r.i32())
    return ('b', r.raw(SIZES[t]))


def write_value(out, v):
    k = v[0]
    if k == 'x':
        out.append(bytes([v[1]])); [write_value(out, x) for x in v[2]]
    elif k == 'o':
        out.append(struct.pack('>hB', v[1], v[2])); out.append(v[3]); [write_value(out, x) for _, x in v[4]]
    elif k == 's':
        out.append(struct.pack('>h', v[1]))
    elif k in 'vqc':
        out.append(struct.pack('>i', v[1]))
    else:
        out.append(v[1])


class Obj:
    def __init__(self):
        self.cls = 0; self.props = None; self.children = []; self.frames = None; self.timelines = None
        self.flags = 0

    def name(self, x):  return x.strings[self.cls]

    def prop(self, x, pname):
        if not self.props: return None
        for lvl in self.props[1]:
            for pd, v in lvl[2]:
                if pd.name == pname: return v
        return None

    def id(self, x):
        v = self.prop(x, 'Id'); return x.strings[v[1]] if v else None


def read_obj(r, x):
    o = Obj(); o.cls = r.i16(); o.flags = r.u8()
    cname = x.strings[o.cls]
    if o.flags & 1:
        cnt = r.i16(); levels = []
        for cn in hierarchy(cname):
            pb = r.u8()
            if pb == 0:
                levels.append((pb, b'', [])); continue
            masks = r.raw(pb & 7); vals = []
            pdefs = CLASSES[cn][1]
            for i, m in enumerate(masks[::-1]):
                if m >> len(pdefs[i*8:i*8+8]):
                    raise ValueError('propriedade sem definição em %s (máscara %02x)' % (cn, m))
                for k, pd in enumerate(pdefs[i*8:i*8+8]):
                    if m & (1 << k):
                        vals.append((pd, read_value(r, pd)))
            levels.append((pb, masks, vals))
        o.props = (cnt, levels)
    if o.flags & 2:
        n = r.i32(); o.children = [read_obj(r, x) for _ in range(n)]
    if o.flags & 4:
        o.frames = [(r.i16(), r.i32(), r.u8(), r.i16()) for _ in range(r.i32())]
        o.timelines = None
        if o.children:
            o.timelines = [read_timeline(r, x, o) for _ in range(r.i32())]
    return o


def find_child(o, x, ident):
    for c in o.children:
        if c.id(x) == ident: return c
    return None


def read_timeline(r, x, parent):
    el = r.i16(); target = find_child(parent, x, x.strings[el])
    assert target is not None, x.strings[el]
    hier = hierarchy(x.strings[target.cls])[::-1]       # derivada primeiro
    defs = []; pdlist = []
    for _ in range(r.i32()):
        pb = r.u8(); ci = r.u8(); path = [r.u8() for _ in range(pb & 0x7f)]
        idx = r.i32() if pb & 0x80 else None
        cls = CLASSES[hier[ci]][1]
        for j, pi in enumerate(path):
            pd = cls[pi]
            if j != len(path) - 1: cls = CLASSES[COMPOUND[pd.name]][1]
        defs.append((pb, ci, path, idx)); pdlist.append(pd)
    kfs = []
    for _ in range(r.i32()):
        head = r.raw(8)
        kfs.append((head, [read_value(r, pd, False) for pd in pdlist]))
    return (el, defs, kfs, pdlist)


def write_obj(out, o):
    out.append(struct.pack('>hB', o.cls, o.flags))
    if o.flags & 1:
        cnt, levels = o.props
        out.append(struct.pack('>h', cnt))
        for pb, masks, vals in levels:
            out.append(bytes([pb])); out.append(masks)
            for _, v in vals: write_value(out, v)
    if o.flags & 2:
        out.append(struct.pack('>i', len(o.children)))
        for c in o.children: write_obj(out, c)
    if o.flags & 4:
        out.append(struct.pack('>i', len(o.frames)))
        for f in o.frames: out.append(struct.pack('>hiBh', *f))
        if o.timelines is not None:
            out.append(struct.pack('>i', len(o.timelines)))
            for el, defs, kfs, _ in o.timelines:
                out.append(struct.pack('>hi', el, len(defs)))
                for pb, ci, path, idx in defs:
                    out.append(bytes([pb, ci] + path))
                    if idx is not None: out.append(struct.pack('>i', idx))
                out.append(struct.pack('>i', len(kfs)))
                for head, vals in kfs:
                    out.append(head); [write_value(out, v) for v in vals]


class Xur:
    def __init__(self, d):
        assert d[:4] == b'XUIB' and struct.unpack('>I', d[4:8])[0] == 5
        self.flags, self.tool = struct.unpack('>IH', d[8:14])
        nsec = struct.unpack('>H', d[0x12:0x14])[0]
        p = 0x14
        self.counts = None
        if self.flags & 1:
            self.counts = list(struct.unpack('>10i', d[p:p+40])); p += 40
        self.order = []; secs = {}
        for _ in range(nsec):
            tag = d[p:p+4].decode(); off, size = struct.unpack('>II', d[p+4:p+12]); p += 12
            self.order.append(tag); secs[tag] = d[off:off+size]
        self.secs = secs
        s = secs.get('STRN', b''); q = 0; self.strings = ['']
        while q < len(s):
            n = struct.unpack('>H', s[q:q+2])[0]; self.strings.append(s[q+2:q+2+2*n].decode('utf-16-be')); q += 2 + 2*n
        v = secs.get('VECT', b''); self.vects = [v[i:i+12] for i in range(0, len(v), 12)]
        qd = secs.get('QUAT', b''); self.quats = [qd[i:i+16] for i in range(0, len(qd), 16)]
        c = secs.get('CUST', b''); self.custs = []; q = 0         # (offset, bytes)
        while q < len(c):
            n = struct.unpack('>i', c[q:q+4])[0]; self.custs.append((q, c[q:q+4+n])); q += 4 + n
        self.root = read_obj(R(secs['DATA']), self)

    # ---- gravação
    def build(self):
        out = []; write_obj(out, self.root); data = b''.join(out)
        secs = {'STRN': b''.join(struct.pack('>H', len(s)) + s.encode('utf-16-be') for s in self.strings[1:]),
                'VECT': b''.join(self.vects), 'QUAT': b''.join(self.quats),
                'CUST': b''.join(b for _, b in self.custs), 'DATA': data}
        order = [t for t in self.order if t in secs and (secs[t] or t in self.order)]
        for t in ('STRN', 'VECT', 'QUAT', 'CUST'):
            if secs[t] and t not in order: order.insert(len(order) - 1, t)
        head = 0x14 + (40 if self.flags & 1 else 0) + 12 * len(order)
        table = b''; body = b''; off = head
        for t in order:
            table += t.encode() + struct.pack('>II', off, len(secs[t])); body += secs[t]; off += len(secs[t])
        counts = struct.pack('>10i', *self.recount()) if self.flags & 1 else b''
        total = head + len(body)
        return (b'XUIB' + struct.pack('>IIHIH', 5, self.flags, self.tool, total, len(order)) + counts + table + body)

    def recount(self):
        c = [0] * 10
        def nvals(v):                    # valores (indexado = n; composto = 1 + filhos)
            if v[0] == 'x': return v[1]
            if v[0] == 'o': return 1 + sum(nvals(x) for _, x in v[4])
            return 1
        def ncomp(v):
            return 1 + sum(ncomp(x) for _, x in v[4]) if v[0] == 'o' else 0
        def walk(o):
            c[0] += 1; c[2] += 1
            if o.props:
                for _, _, vals in o.props[1]:
                    for pd, v in vals:
                        c[1] += nvals(v); c[2] += ncomp(v)
            if o.children: c[9] += 1
            for ch in o.children: walk(ch)
            if o.frames: c[8] += len(o.frames)
            for el, defs, kfs, _ in (o.timelines or []):
                c[7] += 1; c[6] += len(kfs); c[5] += len(defs)
                c[4] += sum(len(path) for _, _, path, _ in defs)
                c[3] += len(kfs) * len(defs)
        walk(self.root)
        return c

    # ---- referências
    def str_index(self, s):
        try: return self.strings.index(s)
        except ValueError: self.strings.append(s); return len(self.strings) - 1

    def vect_index(self, b):
        try: return self.vects.index(b)
        except ValueError: self.vects.append(b); return len(self.vects) - 1

    def quat_index(self, b):
        try: return self.quats.index(b)
        except ValueError: self.quats.append(b); return len(self.quats) - 1

    def cust_offset(self, b):
        for off, x in self.custs:
            if x == b: return off
        off = sum(len(x) for _, x in self.custs); self.custs.append((off, b)); return off


def relocate(o, src, dst):
    """Copia o objeto o (de src) remapeando todas as referências para as tabelas de dst."""
    import copy
    o = copy.deepcopy(o)
    def val(v):
        k = v[0]
        if k == 's': return ('s', dst.str_index(src.strings[v[1]]))
        if k == 'v': return ('v', dst.vect_index(src.vects[v[1]]))
        if k == 'q': return ('q', dst.quat_index(src.quats[v[1]]))
        if k == 'c': return ('c', dst.cust_offset(dict(src.custs)[v[1]]))
        if k == 'x': return ('x', v[1], [val(x) for x in v[2]])
        if k == 'o': return ('o', v[1], v[2], v[3], [(pd, val(x)) for pd, x in v[4]])
        return v
    def walk(o):
        o.cls = dst.str_index(src.strings[o.cls])
        if o.props:
            o.props = (o.props[0], [(pb, m, [(pd, val(v)) for pd, v in vals]) for pb, m, vals in o.props[1]])
        for ch in o.children: walk(ch)
        if o.frames:
            o.frames = [(dst.str_index(src.strings[a]), b, c, dst.str_index(src.strings[d]) if d > 0 else d)
                        for a, b, c, d in o.frames]
        if o.timelines:
            o.timelines = [(dst.str_index(src.strings[el]), defs, [(h, [val(v) for v in vs]) for h, vs in kfs], pdl)
                           for el, defs, kfs, pdl in o.timelines]
    walk(o)
    return o


if __name__ == '__main__':
    bad = 0
    for f in sys.argv[1:]:
        d = open(f, 'rb').read()
        try:
            x = Xur(d); b = x.build()
            ok = b == d
            if not ok:
                k = next((i for i in range(min(len(b), len(d))) if b[i] != d[i]), None)
                print('DIFERENTE', os.path.basename(f), len(d), len(b), 'primeiro byte diferente', k)
                bad += 1
        except Exception as e:
            print('ERRO', os.path.basename(f), repr(e)); bad += 1
    print(len(sys.argv) - 1, 'arquivos,', bad, 'com problema')
