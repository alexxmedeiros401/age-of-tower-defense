# sh.py ID CLIP AZ f,f,f OUT
import sys
from PIL import Image, ImageDraw
id_,clip,az,frs,out=sys.argv[1:6]
F=f'/home/claude/work/repose/rhB_frames/{id_}'
frames=[int(x) for x in frs.split(',')]
w,h=Image.open(f'{F}/old/{clip}_az{az}_{frames[0]:03d}.png').size
im=Image.new('RGB',(w*len(frames),h*2),'white'); d=ImageDraw.Draw(im)
for i,f in enumerate(frames):
    for j,wh in enumerate(('old','new')):
        im.paste(Image.open(f'{F}/{wh}/{clip}_az{az}_{f:03d}.png').convert('RGB'),(i*w,j*h))
    d.text((i*w+4,4),f'{clip} {f} az{az}',fill='black')
im.save(out,quality=85)
