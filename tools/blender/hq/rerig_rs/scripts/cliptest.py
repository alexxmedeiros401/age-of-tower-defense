"""Bake a clip and render frames (review). usage: -- rs_rig.blend OUTDIR CLIP FRAMES(e.g. 0-24:2) [--az 315,200] [--elev 25] [--close size,cx,cy,cz] [--base] [--rx N --ry N]"""
import sys, os, numpy as np, importlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rig'))
import bpy
import rs_core, rs_apply, rs_render, rs_skel, rs_anim, rs_clips
argv = sys.argv[sys.argv.index("--") + 1:]
blend, out, clipname, frs = argv[:4]
def opt(name, dflt):
    return argv[argv.index(name) + 1] if name in argv else dflt
azs = [float(x) for x in opt('--az', '315,200').split(',')]
elev = float(opt('--elev', '25'))
size = 3.0; ctr = (0.0, 0.06, 1.95)
if '--close' in argv:
    v = [float(x) for x in opt('--close', '').split(',')]; size = v[0]; ctr = (v[1], v[2], v[3])
rx, ry = int(opt('--rx', '420')), int(opt('--ry', '520'))
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
arm = bpy.data.objects['CavemanRig']
K = rs_apply.Keyer(arm)
clip = rs_clips.CLIPS[clipname]()
poses = rs_anim.bake(clip)
if '-' in frs:
    r, *st = frs.split(':'); f0, f1 = [int(x) for x in r.split('-')]; step = int(st[0]) if st else 1
    frames = list(range(f0, f1 + 1, step))
else:
    frames = [int(x) for x in frs.split(',')]
cam = rs_render.setup(sc, rx, ry, nobase='--base' not in argv)
os.makedirs(out, exist_ok=True)
for f in range(len(poses)):
    c, P, info = poses[f]
    if info['over']: print('FRAME %d over-reach: %s' % (f, info['over']))
for f in frames:
    c, P, info = poses[f]
    K.set_pose(P)
    bpy.context.view_layer.update()
    print('F%02d R: sw %.0f tw %.0f el %.0f | L: sw %.0f tw %.0f el %.0f | knees %.0f/%.0f | grip %s pouch %s' % (f, info['swing.R'], info['twist.R'], info['elbow_deg.R'],
          info['swing.L'], info['twist.L'], info['elbow_deg.L'], info['knee_deg.L'], info['knee_deg.R'], np.round(info['grip'], 2), np.round(info['pouch'], 2)))
    for az in azs:
        rs_render.shoot(sc, cam, os.path.join(out, '%s_az%03d_%02d.png' % (clipname, int(az), f)), az, elev=elev, size=size, ctr=ctr)
