import sys, os
from PIL import Image, ImageDraw
files=sys.argv[2:]; out=sys.argv[1]
cell=(300,200); cols=4; rows=(len(files)+cols-1)//cols
S=Image.new('RGB',(cols*cell[0],rows*cell[1]),(255,0,255))
d=ImageDraw.Draw(S)
for k,f in enumerate(files):
    im=Image.open(f).convert('RGBA'); w,h=im.size
    bg=Image.new('RGBA',im.size,(40,90,140,255)); bg.alpha_composite(im); im=bg
    im.thumbnail((cell[0]-10,cell[1]-30))
    x=(k%cols)*cell[0]; y=(k//cols)*cell[1]
    S.paste(im.convert('RGB'),(x+5,y+5))
    d.text((x+5,y+cell[1]-22),'%s %dx%d'%(os.path.basename(f).split('\\')[-1][:28],w,h),fill=(255,255,255))
S.save(out)
