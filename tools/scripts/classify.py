import sys, glob, os, re
sys.path.insert(0, os.path.dirname(__file__))
from strn import sections, strings
def classify(path):
    return classify_list(open(path,'rb').read())
def classify_bytes(d):
    return {i:(a,b) for i,s,a,b in classify_list(d)}
def classify_list(d):
    b,secs=sections(d); st=strings(d); o,sz=secs['DATA']; D=d[o:o+sz]
    names=set(st); res=[]
    for i,s in enumerate(st,1):
        pat=i.to_bytes(2,'big'); p=D.find(pat); isid=False
        while p!=-1:
            if p>=8 and D[p-1]&1 and D[p-8] in (1,3,5,7) and D[p-4:p-1]==b'\0\0\0'[:3] or (p>=8 and D[p-1]&1 and D[p-8] in (1,3,5,7) and D[p-4]==0):
                isid=True
            p=D.find(pat,p+1)
        frame = ('End'+s) in names or s.startswith('End') and s[3:] in names
        res.append((i,s,isid,frame))
    return res
if __name__=='__main__':
    skip=re.compile(r'^(Xui\w*|.*\.(png|dds|jpg|xur|fx)|Inter( \w+)?)$', re.I)
    for f in sorted(glob.glob(sys.argv[1]+'/*.xur')):
        print('###',os.path.basename(f))
        for i,s,isid,fr in classify(f):
            if skip.match(s) or '\\' in s: continue
            print('  %3d %s%s %r'%(i,'I' if isid else '.', 'F' if fr else '.', s))
