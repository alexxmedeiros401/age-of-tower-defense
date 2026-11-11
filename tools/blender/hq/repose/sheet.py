import sys,glob
from PIL import Image, ImageDraw
# sheet.py OUT AZ prefixA prefixB ...
out,az=sys.argv[1:3]; rows=sys.argv[3:]
cols=None; ims=[]
for p in rows:
    fs=sorted(glob.glob(f'{p}_*_az{az}.png'),key=lambda f:(f.split('_')[-3]!='Whirl',f))
    ims.append(fs)
n=max(len(r) for r in ims); w,h=Image.open(ims[0][0]).size
s=Image.new('RGB',(w*n,h*len(rows)),'white'); d=ImageDraw.Draw(s)
for j,r in enumerate(ims):
    for i,f in enumerate(r):
        s.paste(Image.open(f).convert('RGB'),(i*w,j*h)); d.text((i*w+4,j*h+4),f.split('/')[-1],fill='black')
s.save(out,quality=85)
