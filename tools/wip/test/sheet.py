"""sheet.py OUT 'GLOB' [cols] [crop x0,y0,x1,y1] [every] -> a numbered contact sheet"""
import sys, glob
from PIL import Image, ImageDraw
out, pat = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
crop = [int(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
every = int(sys.argv[5]) if len(sys.argv) > 5 else 1
fs = sorted(glob.glob(pat))[::every]
ims = []
for f in fs:
    im = Image.open(f).convert("RGB")
    if crop:
        im = im.crop(crop)
    ims.append(im)
w, h = ims[0].size
s = min(1.0, 2400 / (cols * w))
tw, th = int(w * s), int(h * s)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
dr = ImageDraw.Draw(sheet)
for i, im in enumerate(ims):
    x, y = (i % cols) * tw, (i // cols) * th
    sheet.paste(im.resize((tw, th)), (x, y))
    dr.text((x + 4, y + 2), str(i * every), fill=(255, 255, 0))
sheet.save(out)
print(out, sheet.size, len(ims))
