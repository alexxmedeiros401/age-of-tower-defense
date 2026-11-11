# propaxis.py GLB BONE [MINDIST]: PCA axis of the verts carried by BONE beyond MINDIST of its head (rest armature space),
# oriented from the bone head toward the far end with more extent; prints extents along it.
import bpy, sys, numpy as np
glb, bone = sys.argv[1], sys.argv[2]; md = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); B = arm.data.bones
Ai = np.array(arm.matrix_world.inverted())
pts = []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.find_armature() != arm: continue
    g = {x.index: x.name for x in o.vertex_groups}
    M = np.array(o.matrix_world)
    for v in o.data.vertices:
        if len(v.groups) and g[max(v.groups, key=lambda q: q.weight).group] == bone:
            p = M[:3, :3] @ np.array(v.co) + M[:3, 3]; pts.append(Ai[:3, :3] @ p + Ai[:3, 3])
pts = np.array(pts); h = np.array(B[bone].head_local)
far = pts[np.linalg.norm(pts - h, axis=1) > md]
c = far.mean(0); u, s, vt = np.linalg.svd(far - c); ax = vt[0]
t = (pts - h) @ ax
if abs(t.max()) < abs(t.min()): ax = -ax; t = -t
print('n', len(pts), 'head', h.round(3), 'axis', ax.round(3), 'extent along axis %.2f .. %.2f' % (t.min(), t.max()))
print('far end', (h + ax * t.max()).round(3), 'near end', (h + ax * t.min()).round(3))
