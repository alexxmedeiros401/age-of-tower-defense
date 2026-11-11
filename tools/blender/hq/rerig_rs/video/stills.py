"""Before/after stills of one shot, from the slow-motion renders (B_old / B_new): python3 stills.py VIDEO_DIR OUT.png"""
import sys, os, json
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FONT_R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f_title = ImageFont.truetype(FONT, 24); f_col = ImageFont.truetype(FONT, 20); f_cap = ImageFont.truetype(FONT_R, 18); f_capb = ImageFont.truetype(FONT, 18)
BG = (24, 28, 24); FG = (240, 240, 232); DIM = (160, 168, 156); GOLD = (238, 190, 80)
CW, CH, CAP, HEAD = 360, 300, 34, 92
# (seconds after the game fires, what to look at)
MOMENTS = [(0.07, 'the rock has just left'), (0.20, 'follow-through'), (0.40, 'reload'), (0.62, 'wind-up'), (0.82, 'ready for the next shot')]
lo = json.load(open(os.path.join(src, 'B_old', 'log.json'))); ln = json.load(open(os.path.join(src, 'B_new', 'log.json')))
fire = lo['fires'][0]
im = Image.new('RGB', (2 * CW, HEAD + len(MOMENTS) * (CAP + CH)), BG)
d = ImageDraw.Draw(im)
d.text((14, 12), 'ROCK SLINGER  one shot, frame by frame', font=f_title, fill=FG)
for x, t, c in ((0, 'BEFORE', (96, 100, 96)), (CW, 'AFTER', (46, 125, 70))):
    w = d.textlength(t, font=f_col)
    d.rounded_rectangle([x + 12, 52, x + 12 + w + 20, 82], 6, fill=c); d.text((x + 22, 55), t, font=f_col, fill=(255, 255, 255))
for r, (dt, what) in enumerate(MOMENTS):
    y = HEAD + r * (CAP + CH)
    # the rendered frame nearest this moment
    i = min(range(len(lo['frames'])), key=lambda k: abs(lo['frames'][k]['t'] - (fire + dt)))
    assert abs(ln['frames'][i]['t'] - lo['frames'][i]['t']) < 1e-6
    a = '+%.2f s' % dt
    d.text((14, y + 7), a, font=f_capb, fill=GOLD)
    d.text((14 + d.textlength(a, font=f_capb) + 12, y + 7), what, font=f_cap, fill=DIM)
    for x, tag in ((0, 'B_old'), (CW, 'B_new')):
        cell = Image.open(os.path.join(src, tag, 'f_%05d.png' % i)).convert('RGB').resize((CW, CH), Image.LANCZOS)
        im.paste(cell, (x, y + CAP))
    d.line([CW, y + CAP, CW, y + CAP + CH], fill=BG, width=2)
im.save(out)
print('wrote', out, im.size)
