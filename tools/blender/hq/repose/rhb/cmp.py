# cmp.py ID CLIP AZ STEP [OUT]  : row old / row new from the rendered frames
import sys, glob, os
from PIL import Image, ImageDraw
id_, clip, az, step = sys.argv[1:5]; step = int(step)
F = f'/home/claude/work/repose/rhB_frames/{id_}'
out = sys.argv[5] if len(sys.argv) > 5 else f'/home/claude/work/repose/rhB_look/{id_}_{clip}_{az}.jpg'
fo = sorted(glob.glob(f'{F}/old/{clip}_az{az}_*.png'))[::step]
w, h = Image.open(fo[0]).size; sc = 0.6; w2, h2 = int(w * sc), int(h * sc)
im = Image.new('RGB', (w2 * len(fo), h2 * 2), 'white'); d = ImageDraw.Draw(im)
for i, f in enumerate(fo):
    for j, which in enumerate(('old', 'new')):
        p = f.replace('/old/', f'/{which}/')
        if os.path.exists(p): im.paste(Image.open(p).convert('RGB').resize((w2, h2)), (i * w2, j * h2))
    d.text((i * w2 + 3, 3), os.path.basename(f)[:-4].split('_')[-1], fill='black')
im.save(out, quality=82); print(out)
