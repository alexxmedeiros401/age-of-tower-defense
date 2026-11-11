# Before/after video: shipped left, new right. usage:
# python3 video.py OLD_FRAMES NEW_FRAMES OUT.mp4 "seq"   seq = "az315:Combat,Attack,Combat,Attack;az200:Combat,Attack;az315:Ability,Cheer"
import sys, os, glob, subprocess, tempfile, shutil
from PIL import Image, ImageDraw
old, new, out, seq = sys.argv[1:5]
tmp = tempfile.mkdtemp()
k = 0
for part in seq.split(';'):
    az, clips = part.split(':')
    for clip in clips.split(','):
        fo = sorted(glob.glob(f'{old}/{clip}_{az}_*.png'))
        for fpath in fo:
            fn = os.path.basename(fpath)
            a = Image.open(fpath).convert('RGB'); b = Image.open(f'{new}/{fn}').convert('RGB')
            w, h = a.size
            im = Image.new('RGB', (w * 2 + 4, h), 'black'); im.paste(a, (0, 0)); im.paste(b, (w + 4, 0))
            d = ImageDraw.Draw(im)
            fr = fn.rsplit('_', 1)[1][:3]
            d.text((6, 6), f'shipped  {clip} {az} f{fr}', fill='black'); d.text((w + 10, 6), f'new  {clip} {az} f{fr}', fill='black')
            im.save(f'{tmp}/{k:05d}.png'); k += 1
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', f'{tmp}/%05d.png', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', out], check=True)
shutil.rmtree(tmp)
print('wrote', out, k, 'frames')
