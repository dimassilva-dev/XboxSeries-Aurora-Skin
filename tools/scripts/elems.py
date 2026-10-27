import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from strn import sections, strings
def vects(d, secs):
    o, sz = secs['VECT']; return [struct.unpack('>3f', d[o+i:o+i+12]) for i in range(0, sz, 12)]
def elements(d):
    b, secs = sections(d); st = strings(d); o, sz = secs['DATA']; D = d[o:o+sz]; V = vects(d, secs)
    classes = {i for i, s in enumerate(st, 1) if s.startswith('Xui') and '_' not in s}
    res = []
    for p in range(len(D)-16):
        c = int.from_bytes(D[p:p+2], 'big')
        if c not in classes or D[p+2] not in (1, 3, 5, 7): continue
        if D[p+6] != 0 or D[p+7] != 0: continue
        mask = int.from_bytes(D[p+6:p+10], 'big')
        if mask == 0 or mask > 0xffff: continue
        q = p+10; e = {'off': o+p, 'cls': st[c-1], 'mask': mask}
        if mask & 1:
            i = int.from_bytes(D[q:q+2], 'big')
            if not (0 < i <= len(st)) or not st[i-1].replace('_','').replace('\\','').isalnum(): continue
            e['id'] = st[i-1]; q += 2
        if mask & 2: e['w'] = struct.unpack('>f', D[q:q+4])[0]; e['w_off'] = o+p+(q-p); q += 4
        if mask & 4: e['h'] = struct.unpack('>f', D[q:q+4])[0]; e['h_off'] = o+p+(q-p); q += 4
        if mask & 8:
            vi = int.from_bytes(D[q:q+4], 'big')
            if vi >= len(V): continue
            e['pos'] = V[vi]; e['vi'] = vi; e['vi_off'] = o+p+(q-p); q += 4
        if 'w' in e and not (0 <= e['w'] < 5000): continue
        res.append(e)
    return res
if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    for e in elements(d):
        print('%6d %-20s %-34s w=%-7s h=%-7s pos=%s vi=%s' % (e['off'], e['cls'], e.get('id','-'), round(e.get('w',-1),1), round(e.get('h',-1),1),
              tuple(round(x,1) for x in e['pos']) if 'pos' in e else '-', e.get('vi')))
