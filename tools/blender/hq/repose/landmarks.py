# Landmarks for authoring keys (armature REST coords, the frame hero_arm.py keys are written in):
# shoulders, rest elbows / wrists, the head volume (head/neck-carried skin: hair, beard, helmet) and torso extents,
# then, per clip, the ORIGINAL wrist and elbow positions brought back to chest-relative rest coords, every STEP frames.
# usage: python3 landmarks.py GLB [CLIP,CLIP..|all] [STEP]
import bpy, sys
import numpy as np
from mathutils import Vector, Quaternion
glb = sys.argv[1]; clips = sys.argv[2] if len(sys.argv) > 2 else 'all'; step = int(sys.argv[3]) if len(sys.argv) > 3 else 3
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); P = arm.pose.bones; B = arm.data.bones
AW = arm.matrix_world
def v3(v): return '(%.2f, %.2f, %.2f)' % tuple(v)
for s in 'RL':
    print(s, 'shoulder', v3(B['upperarm.' + s].head_local), 'elbow', v3(B['forearm.' + s].head_local), 'wrist', v3(B['hand.' + s].head_local),
          'hand tip', v3(B['hand.' + s].tail_local), 'Lu %.3f Lf %.3f' % ((B['forearm.' + s].head_local - B['upperarm.' + s].head_local).length,
                                                              (B['hand.' + s].head_local - B['forearm.' + s].head_local).length))
print('head bone', v3(B['head'].head_local), v3(B['head'].tail_local), 'chest', v3(B['chest'].head_local))
def subtree(n):
    o = [n]
    for c in B[n].children: o += subtree(c.name)
    return o
HEAD = set(subtree('neck'))
for o in bpy.data.objects:
    if o.type != 'MESH' or o.find_armature() != arm: continue
    gname = {g.index: g.name for g in o.vertex_groups}
    co = np.array([v.co[:] for v in o.data.vertices]); M = np.array(o.matrix_world); Ai = np.array(AW.inverted())
    co = co @ M[:3, :3].T + M[:3, 3]; co = co @ Ai[:3, :3].T + Ai[:3, 3]
    dom = np.array([gname[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else '' for v in o.data.vertices])
    h = co[np.isin(dom, list(HEAD))]
    if len(h):
        print(o.name, 'HEAD volume x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (h[:, 0].min(), h[:, 0].max(), h[:, 1].min(), h[:, 1].max(), h[:, 2].min(), h[:, 2].max()))
        for zz in np.arange(h[:, 2].min(), h[:, 2].max(), 0.08):
            sl = h[(h[:, 2] >= zz) & (h[:, 2] < zz + 0.08)]
            if len(sl): print('   head z %.2f: x %.2f..%.2f y %.2f..%.2f' % (zz, sl[:, 0].min(), sl[:, 0].max(), sl[:, 1].min(), sl[:, 1].max()))
    t = co[np.isin(dom, ['chest', 'spine', 'root'])]
    if len(t):
        for zz in np.arange(t[:, 2].min(), t[:, 2].max(), 0.1):
            sl = t[(t[:, 2] >= zz) & (t[:, 2] < zz + 0.1)]
            if len(sl): print('   torso z %.2f: x %.2f..%.2f y %.2f..%.2f' % (zz, sl[:, 0].min(), sl[:, 0].max(), sl[:, 1].min(), sl[:, 1].max()))
cr = B['chest'].matrix_local
arm.animation_data_create()
for act in bpy.data.actions:
    if clips != 'all' and act.name not in clips.split(','): continue
    arm.animation_data.action = act
    f0, f1 = [int(round(x)) for x in act.frame_range]
    print('==', act.name, f0, f1)
    for f in sorted(set(list(range(f0, f1 + 1, step)) + [f1])):
        bpy.context.scene.frame_set(f)
        X = (P['chest'].matrix @ cr.inverted()).inverted()
        for spec_ in [x for x in __import__('os').environ.get('AXIS', '').split(';') if x]:
            bn, ax_ = spec_.split(':'); ax_ = Vector([float(t) for t in ax_.split(',')])
            axl = B[bn].matrix_local.to_3x3().inverted() @ ax_
            print('     axis %s %s' % (bn, v3((X.to_3x3() @ P[bn].matrix.to_3x3() @ axl).normalized())))
        ex = ' '.join('%s %s' % (b, v3(X @ P[b].head)) for b in __import__('os').environ.get('EXTRA', '').split(',') if b)
        print('  f%3d' % f, ' '.join('%s wrist %s elbow %s' % (s, v3(X @ P['hand.' + s].head), v3(X @ P['forearm.' + s].head)) for s in 'RL'), ex)
