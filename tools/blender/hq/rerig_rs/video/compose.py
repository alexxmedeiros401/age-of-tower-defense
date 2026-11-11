"""Before/after film of the full attack: stacks the BEFORE and AFTER renders of rs_fight.py (same game timeline) with
titles and the game's clip state, and encodes H.264 for a phone (720 x 1280, 30 fps).

  python3 compose.py VIDEO_DIR OUT.mp4        (VIDEO_DIR holds A_old, A_new, B_old, ... with f_%05d.png and log.json)
"""
import sys, os, json, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
W, PH, BAR = 720, 600, 40
H = BAR + PH + PH + BAR
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f_title = ImageFont.truetype(FONT, 22); f_chip = ImageFont.truetype(FONT, 20); f_small = ImageFont.truetype(FONT_R, 18)
f_state = ImageFont.truetype(FONT, 18)
BG = (24, 28, 24); FG = (240, 240, 232); DIM = (150, 158, 146); RED = (232, 86, 60); GOLD = (238, 190, 80)
SEGS = [('A', 'FULL ATTACK', 'game speed'), ('B', 'FIRST TWO SHOTS', 'slow motion x4'), ('C', 'FROM BEHIND', 'slow motion x4'),
        ('D', 'GAME CAMERA ANGLE', 'game speed')]
HOLD = 12            # frames the first picture of a part is held


def chip(d, xy, text, fill):
    x, y = xy
    w = d.textlength(text, font=f_chip)
    d.rounded_rectangle([x, y, x + w + 20, y + 30], 6, fill=fill)
    d.text((x + 10, y + 3), text, font=f_chip, fill=(255, 255, 255))


def state_text(fr):
    """What the game's animation player is doing on this frame."""
    clip = fr['clip']
    names = {'Idle': 'Idle', 'Whirl': 'Whirl (combat loop)', 'Throw': 'Throw (attack clip)'}
    s = names.get(clip, clip)
    if fr['blends']:
        s += '  <  ' + ' + '.join(names.get(b[0], b[0]).split(' (')[0] for b in fr['blends'])
    return s


tmp = os.path.join(src, '_frames')
shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
n = 0
for tag, title, sub in SEGS:
    lo = json.load(open(os.path.join(src, tag + '_old', 'log.json')))
    ln = json.load(open(os.path.join(src, tag + '_new', 'log.json')))
    assert len(lo['frames']) == len(ln['frames']), (tag, len(lo['frames']), len(ln['frames']))
    fires = lo['fires']
    frames = list(range(len(lo['frames'])))
    seq = [0] * HOLD + frames
    for i in seq:
        fo, fn = lo['frames'][i], ln['frames'][i]
        im = Image.new('RGB', (W, H), BG)
        a = Image.open(os.path.join(src, tag + '_old', 'f_%05d.png' % i)).convert('RGB')
        b = Image.open(os.path.join(src, tag + '_new', 'f_%05d.png' % i)).convert('RGB')
        im.paste(a, (0, BAR)); im.paste(b, (0, BAR + PH))
        d = ImageDraw.Draw(im)
        d.line([0, BAR + PH, W, BAR + PH], fill=BG, width=3)
        # top bar: the part's title
        d.text((14, 8), title, font=f_title, fill=FG)
        tw = d.textlength(sub, font=f_small)
        d.text((W - 14 - tw, 11), sub, font=f_small, fill=GOLD if 'slow' in sub else DIM)
        # panel labels
        chip(d, (12, BAR + 10), 'BEFORE', (96, 100, 96))
        chip(d, (12, BAR + PH + 10), 'AFTER', (46, 125, 70))
        # what each animation player is doing
        for y, fr in ((BAR + 14, fo), (BAR + PH + 14, fn)):
            st = state_text(fr)
            d.text((W - 14 - d.textlength(st, font=f_small), y), st, font=f_small, fill=(52, 66, 50))
        # bottom bar: the shot counter; it flashes when the game fires (and spawns its rock)
        t = fo['t']
        shot = sum(1 for x in fires if x <= t + 1e-6)
        age = fo['fire_age']
        flash = 0.0 <= age < 0.12
        d.ellipse([14, BAR + 2 * PH + 11, 32, BAR + 2 * PH + 29], fill=RED if flash else (70, 76, 70))
        d.text((42, BAR + 2 * PH + 9), ('GAME FIRES  shot %d' % shot) if flash else ('shot %d of %d' % (shot, len(fires)) if shot else 'target not in range yet'),
               font=f_state, fill=RED if flash else DIM)
        ts = 't = %.2f s' % t
        d.text((W - 14 - d.textlength(ts, font=f_small), BAR + 2 * PH + 10), ts, font=f_small, fill=DIM)
        im.save(os.path.join(tmp, 'c_%05d.png' % n)); n += 1
# hold the last picture half a second
last = Image.open(os.path.join(tmp, 'c_%05d.png' % (n - 1)))
for k in range(15):
    last.save(os.path.join(tmp, 'c_%05d.png' % n)); n += 1
print('composed', n, 'frames, %.1f s' % (n / 30.0))
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', os.path.join(tmp, 'c_%05d.png'), '-c:v', 'libx264', '-preset', 'slow', '-crf', '19',
       '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.0', '-movflags', '+faststart', '-r', '30', out]
subprocess.run(cmd, check=True)
print('wrote', out, os.path.getsize(out), 'bytes')
