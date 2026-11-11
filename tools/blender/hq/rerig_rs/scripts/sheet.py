"""Contact sheet: python3 sheet.py OUT.jpg COLS [--label] FILES... (labels = file stems)"""
import sys, os
from PIL import Image, ImageDraw
out = sys.argv[1]; cols = int(sys.argv[2]); files = sys.argv[3:]
scale = 1.0
if files and files[0].startswith('--scale='):
    scale = float(files[0].split('=')[1]); files = files[1:]
ims = [Image.open(f).convert('RGB') for f in files]
if scale != 1.0:
    ims = [im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS) for im in ims]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * h), 'white')
d = ImageDraw.Draw(sheet)
for i, (im, f) in enumerate(zip(ims, files)):
    x, y = (i % cols) * w, (i // cols) * h
    sheet.paste(im, (x, y))
    lab = os.path.splitext(os.path.basename(f))[0]
    d.rectangle([x, y, x + 7 * len(lab) + 6, y + 13], fill='white')
    d.text((x + 3, y + 1), lab, fill='black')
sheet.save(out, quality=88)
print(out, sheet.size)
