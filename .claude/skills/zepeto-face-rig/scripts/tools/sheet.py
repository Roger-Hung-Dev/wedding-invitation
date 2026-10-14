import sys, glob, os
from PIL import Image, ImageDraw, ImageFont
d_=sys.argv[1]; cols=int(sys.argv[2]); f=ImageFont.truetype(r"C:\Windows\Fonts\msjh.ttc",16)
fs=sorted(glob.glob(os.path.join(d_,"*.png"))); names=open(os.path.join(d_,"frames.txt")).read().split("\n")
c=300; W=Image.new("RGB",(cols*c,((len(fs)+cols-1)//cols)*(c+22)),(30,30,30)); dr=ImageDraw.Draw(W)
for i,p in enumerate(fs):
    x,y=(i%cols)*c,(i//cols)*(c+22); W.paste(Image.open(p).convert("RGB").resize((c,c)),(x,y)); dr.text((x+4,y+c+2),names[i],fill=(230,230,230),font=f)
W.save(d_+".png")
