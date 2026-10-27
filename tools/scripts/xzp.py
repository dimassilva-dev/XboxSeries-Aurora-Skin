import struct, sys, os
def parse(path):
    d = open(path,'rb').read()
    assert d[:4]==b'XUIZ'
    data_start = struct.unpack('>I', d[0x10:0x14])[0] + 0x16
    count = struct.unpack('>H', d[0x14:0x16])[0]
    p = 0x16; ents=[]
    for _ in range(count):
        size, off = struct.unpack('>II', d[p:p+8]); n = d[p+8]
        name = d[p+9:p+9+2*n].decode('utf-16-be'); p += 9+2*n
        ents.append((name,size,off))
    return d, data_start, count, p, ents
if __name__=='__main__':
    d, ds, c, p, ents = parse(sys.argv[1])
    print('data_start',hex(ds),'count',c,'end_of_table',hex(p))
    out=sys.argv[2]
    for name,size,off in ents:
        fp=os.path.join(out,name); os.makedirs(os.path.dirname(fp) or out, exist_ok=True)
        open(fp,'wb').write(d[ds+off:ds+off+size])
    print(len(ents))
