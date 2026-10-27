import struct
def load(path):
    d=open(path,'rb').read(); n=struct.unpack('>H',d[4:6])[0]
    tabs={d[12+16*i:16+16*i].decode('latin1'):struct.unpack('>II',d[20+16*i:28+16*i]) for i in range(n)}
    o,l=tabs['cmap']; c=d[o:o+l]; nt=struct.unpack('>H',c[2:4])[0]; cmap={}
    for i in range(nt):
        pid,eid,off=struct.unpack('>HHI',c[4+8*i:12+8*i]); fmt=struct.unpack('>H',c[off:off+2])[0]
        if fmt==4 and not cmap:
            sc=struct.unpack('>H',c[off+6:off+8])[0]//2; e=off+14
            ends=struct.unpack('>%dH'%sc,c[e:e+2*sc]); starts=struct.unpack('>%dH'%sc,c[e+2*sc+2:e+4*sc+2])
            deltas=struct.unpack('>%dh'%sc,c[e+4*sc+2:e+6*sc+2]); ro=e+6*sc+2
            ranges=struct.unpack('>%dH'%sc,c[ro:ro+2*sc])
            for k,(s,en,dl,r) in enumerate(zip(starts,ends,deltas,ranges)):
                for cp in range(s,en+1):
                    if r==0: g=(cp+dl)&0xffff
                    else:
                        a=ro+2*k+r+2*(cp-s); g=struct.unpack('>H',c[a:a+2])[0]
                        if g: g=(g+dl)&0xffff
                    cmap[cp]=g
    hh=tabs['hhea'][0]; nm=struct.unpack('>H',d[hh+34:hh+36])[0]; ho=tabs['hmtx'][0]
    adv=[struct.unpack('>H',d[ho+4*i:ho+4*i+2])[0] for i in range(nm)]
    return lambda s: sum(adv[min(cmap.get(ord(ch),0),nm-1)] for ch in s if ch not in '\r\n')
