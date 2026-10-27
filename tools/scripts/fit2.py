import sys, os, glob, struct
sys.path.insert(0, os.path.dirname(__file__))
from strn import sections, strings
from width import load
from ptbr import T, SKIP
fonts={'Inter':'Regular','Inter Bold':'Bold','Inter SemiBold':'SemiBold','Inter Medium':'Medium','Inter Light':'Light'}
FW={k:load('extract/Fonts\\Inter-%s.ttf'%v) for k,v in fonts.items()}
def hdr(D,p):
    for q in range(p-1, max(0,p-60), -1):
        if D[q] in (1,3,5,7) and D[q+4]==0 and D[q+5]==0 and (D[q+7]&3)==3:
            w=struct.unpack('>f',D[q+10:q+14])[0]
            if 1<w<2000: return w
rows=[]
for f in sorted(glob.glob('extract/*.xur')):
    d=open(f,'rb').read(); b,secs=sections(d); st=strings(d); o,sz=secs['DATA']; D=d[o:o+sz]; fn=os.path.basename(f)
    for i,s in enumerate(st,1):
        if s not in T or T[s]==s or s in SKIP.get(fn,()): continue
        pat=i.to_bytes(2,'big'); p=D.find(pat)
        while p!=-1:
            kind=None
            try: ps=struct.unpack('>f',D[p+10:p+14])[0]
            except: ps=0
            if 5<ps<130 and D[p+14]==0:
                fi=int.from_bytes(D[p+14:p+16],'big'); fname=st[fi-1] if 0<fi<=len(st) else ''
                if fname in FW: kind=('text',ps,fname)
            elif D[p-1]==1 and D[p+2:p+4]==b'\x01\x01': kind=('btn',16,'Inter')
            if kind:
                ew=hdr(D,p)
                if ew:
                    w=FW[kind[2]]; en=w(s)*kind[1]/2048; pt=w(T[s])*kind[1]/2048
                    lines=max(s.count('\n'),1)
                    if '\n' in s: en=max(FW[kind[2]](x)*kind[1]/2048 for x in s.split('\n')); pt=max(FW[kind[2]](x)*kind[1]/2048 for x in T[s].split('\n'))
                    rows.append((pt/ew, fn, kind[0], round(kind[1]), s, T[s], ew, en, pt))
            p=D.find(pat,p+1)
seen=set()
for r in sorted(rows, reverse=True):
    if r[0] < float(sys.argv[1]): break
    k=(r[1],r[4])
    if k in seen: continue
    seen.add(k)
    print('%.2f %-30s %-4s %3d %-30r -> %-30r elem=%4.0f en=%4.0f pt=%4.0f'%r)
