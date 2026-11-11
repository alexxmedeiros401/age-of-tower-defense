# before/after video: shipped (left) vs re-authored (right); the 315 view then the 200 view (elev 35); per view the
# combat loop then the attack, twice (heroes: also Ability, Cheer).
# usage: python3 beforeafter.py OLD.glb NEW.glb OUT.mp4 [CLIP ...]   (default clips: Combat Attack)
import sys, os, subprocess, tempfile, glob
from PIL import Image, ImageDraw
old, new, out = sys.argv[1:4]
clips = sys.argv[4:] or ['Combat', 'Attack']
HERE = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp(prefix='ba_')
import bpy
def ranges(glb):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    return {a.name: [int(round(x)) for x in a.frame_range] for a in bpy.data.actions}
R = ranges(new)
spec = ';'.join('%s:%s' % (c, ','.join(str(f) for f in range(R[c][0], R[c][1] + 1))) for c in clips if c in R)
env = dict(os.environ, RX='320', RY='400')
for tag, g in (('old', old), ('new', new)):
    subprocess.run([sys.executable, os.path.join(HERE, 'shots.py'), g, os.path.join(tmp, tag), spec, '315,200', '35'],
                   env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
seq = []
for az in (315, 200):
    for rep in range(2):
        for c in clips:
            if c not in R: continue
            for f in range(R[c][0], R[c][1] + 1):
                seq.append((az, c, f))
for k, (az, c, f) in enumerate(seq):
    a = Image.open(os.path.join(tmp, 'old_%s_%02d_az%d.png' % (c, f, az))).convert('RGB')
    b = Image.open(os.path.join(tmp, 'new_%s_%02d_az%d.png' % (c, f, az))).convert('RGB')
    im = Image.new('RGB', (a.width * 2, a.height), 'white'); im.paste(a, (0, 0)); im.paste(b, (a.width, 0))
    d = ImageDraw.Draw(im)
    d.text((8, 8), 'shipped', fill='black'); d.text((a.width + 8, 8), 'new', fill='black')
    d.text((8, a.height - 18), '%s  f%02d  az%d' % (c, f, az), fill='black')
    im.save(os.path.join(tmp, 'v_%05d.png' % k))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(tmp, 'v_%05d.png'),
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23', out], check=True)
print('wrote', out, len(seq), 'frames')
