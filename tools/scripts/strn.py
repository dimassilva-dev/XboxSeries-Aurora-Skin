import struct, sys, glob, os
def sections(d):
    b = 0; assert d[:4]==b'XUIB'
    cnt = struct.unpack('>H', d[b+0x12:b+0x14])[0]
    secs={}
    flags=struct.unpack('>I', d[b+8:b+12])[0]
    p=b+0x14+(0x28 if flags&1 else 0)
    for i in range(cnt):
        tag=d[p:p+4].decode(); off,size=struct.unpack('>II',d[p+4:p+12]); secs[tag]=(b+off,size); p+=12
    return b, secs
def strings(d):
    b,secs=sections(d); off,size=secs['STRN']; p=off; out=[]
    while p<off+size:
        n=struct.unpack('>H',d[p:p+2])[0]; out.append(d[p+2:p+2+2*n].decode('utf-16-be')); p+=2+2*n
    return out
if __name__=='__main__':
    for f in sorted(glob.glob(sys.argv[1]+'/*.xur')):
        d=open(f,'rb').read()
        b,secs=sections(d)
        print('###',os.path.basename(f), b, {k:v for k,v in secs.items()})
        for s in strings(d): print('  ',repr(s))
