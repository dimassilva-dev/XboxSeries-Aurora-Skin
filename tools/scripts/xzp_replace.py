"""Troca arquivos dentro de um .xzp. uso: python xzp_replace.py <in.xzp> <out.xzp> <nome_interno>=<arquivo> ..."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from xzp import parse

def replace(src, dst, repl):
    d, ds, count, tend, ents = parse(src)
    blobs = []
    for name, size, off in ents:
        data = open(repl.pop(name), 'rb').read() if name in repl else d[ds+off:ds+off+size]
        blobs.append((name, data))
    assert not repl, 'não encontrados: %s' % list(repl)
    table = bytearray(); off = 0
    for name, data in blobs:
        table += struct.pack('>II', len(data), off) + bytes([len(name)]) + name.encode('utf-16-be')
        off += len(data)
    hdr = bytearray(d[:0x16]); hdr[8:12] = struct.pack('>I', 0x16 + len(table) + off)
    open(dst, 'wb').write(bytes(hdr) + bytes(table) + b''.join(x for _, x in blobs))

if __name__ == '__main__':
    replace(sys.argv[1], sys.argv[2], dict(a.split('=', 1) for a in sys.argv[3:]))
