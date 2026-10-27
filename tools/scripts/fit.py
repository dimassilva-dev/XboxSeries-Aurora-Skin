import sys, os, glob, struct
sys.path.insert(0, os.path.dirname(__file__))
from strn import sections, strings
from width import load
from ptbr import T, SKIP
W = load('extract/Fonts\\Inter-Regular.ttf')
UPM = 2048
def elem_widths(D, p):
    # nearest preceding element header: [flags][u16 count][len][mask u32 with Id+Width][id u16][W f32]
    for q in range(p-1, max(0,p-200), -1):
        if D[q] in (1,3,5,7) and D[q+3] >= 6 and D[q+4]==0 and D[q+5]==0 and (D[q+7] & 3)==3:
            w = struct.unpack('>f', D[q+10:q+14])[0]
            if 1 < w < 1300: return w
    return None
rows=[]
for f in sorted(glob.glob('extract/*.xur')):
    d=open(f,'rb').read(); b,secs=sections(d); st=strings(d); o,sz=secs['DATA']; D=d[o:o+sz]
    fn=os.path.basename(f)
    for i,s in enumerate(st,1):
        if s not in T or T[s]==s or s in SKIP.get(fn,()): continue
        pat=i.to_bytes(2,'big'); p=D.find(pat); ws=set()
        while p!=-1:
            w=elem_widths(D,p)
            if w: ws.add(w)
            p=D.find(pat,p+1)
        if not ws: continue
        ew=min(ws)
        # largura em px a 16px de corpo (estimativa)
        en=W(s)*16/UPM; pt=W(T[s])*16/UPM
        rows.append((pt/ew, fn, s, T[s], ew, en, pt))
for r in sorted(rows, reverse=True)[:int(sys.argv[1]) if len(sys.argv)>1 else 40]:
    print('%.2f %-28s %-28r -> %-34r elem=%4.0f en=%4.0f pt=%4.0f'%r)
