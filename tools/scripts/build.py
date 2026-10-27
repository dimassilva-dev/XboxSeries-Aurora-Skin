import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from xzp import parse
from strn import sections, strings
from classify import classify_bytes
from ptbr import T, SKIP

def rebuild_xur(name, d):
    b, secs = sections(d); st = strings(d)
    flags = classify_bytes(d)
    skip = SKIP.get(name, set()); changed = []
    new = []
    for i, s in enumerate(st, 1):
        isid, frame = flags[i]
        if s in T and s not in skip and not isid and not frame and T[s] != s:
            new.append(T[s]); changed.append((s, T[s]))
        else:
            new.append(s)
    if not changed: return d, []
    blob = b''.join(struct.pack('>H', len(s)) + s.encode('utf-16-be') for s in new)
    so, ssz = secs['STRN']; delta = len(blob) - ssz
    out = bytearray(d[:so] + blob + d[so+ssz:])
    fl = struct.unpack('>I', d[8:12])[0]
    p = 0x14 + (0x28 if fl & 1 else 0)
    cnt = struct.unpack('>H', d[0x12:0x14])[0]
    for k in range(cnt):
        tag = out[p:p+4]; off, size = struct.unpack('>II', out[p+4:p+12])
        if tag == b'STRN': out[p+8:p+12] = struct.pack('>I', len(blob))
        elif off > so: out[p+4:p+8] = struct.pack('>I', off + delta)
        p += 12
    out[0xe:0x12] = struct.pack('>I', len(out))
    return bytes(out), changed

def build(src, dst, meta_desc=None):
    d, ds, count, tend, ents = parse(src)
    blobs = []; report = {}
    for name, size, off in ents:
        data = d[ds+off:ds+off+size]
        if name.endswith('.xur'):
            data, ch = rebuild_xur(name, data)
            if ch: report[name] = ch
        elif name == 'skin.meta' and meta_desc:
            old = data.decode('ascii')
            import re
            data = re.sub(r'"description" : "[^"]*"', '"description" : "%s"' % meta_desc, old).encode('ascii')
        blobs.append((name, data))
    table = bytearray(); off = 0
    for name, data in blobs:
        table += struct.pack('>II', len(data), off) + bytes([len(name)]) + name.encode('utf-16-be')
        off += len(data)
    assert len(table) == tend - 0x16
    hdr = bytearray(d[:0x16])
    total = 0x16 + len(table) + off
    hdr[8:12] = struct.pack('>I', total)
    out = bytes(hdr) + bytes(table) + b''.join(x for _, x in blobs)
    assert len(out) == total
    open(dst, 'wb').write(out)
    return report

if __name__ == '__main__':
    rep = build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    n = 0
    for f, ch in rep.items():
        print('##', f, len(ch))
        for a, b in ch: print('   %r -> %r' % (a, b)); n += 1
    print('total', n)
