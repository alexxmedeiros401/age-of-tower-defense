"""Step 2 (Blender python, for its BVH): mesh.npz + the baked albedo -> weights.npz.

  python3 rs_make_weights.py -- OUT/mesh.npz ALBEDO.png OUT/weights.npz
"""
import sys, os, hashlib
import numpy as np
import bpy  # noqa (mathutils)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rs_mesh, rs_skel, rs_heat, rs_weights

mesh_npz, albedo, out = sys.argv[sys.argv.index("--") + 1:][:3]
M = rs_mesh.Mesh(mesh_npz)
col = M.vertex_colors(albedo)
main = [b for b in rs_skel.bones() if b[4] == 'main']
segs = []
for name, parent, head, tail, kind in main:
    if name.startswith('clavicle'):
        # the collar bone's reach stops short of the shoulder joint, so the shoulder's ball goes with the arm
        segs.append((head + (tail - head) * 0.30, head + (tail - head) * 0.74))
    else:
        segs.append((head, tail))
body = np.where(M.vpart == 0)[0]
key = hashlib.md5(np.concatenate([np.concatenate(s) for s in segs]).tobytes() + M.V.tobytes()).hexdigest()[:12]
cache = os.path.join(os.path.dirname(os.path.abspath(out)), 'vis_%s.npz' % key)
if os.path.exists(cache):
    d = np.load(cache); dist, vis = d['dist'], d['vis']
else:
    dist, vis = rs_heat.visibility(M.V, M.vertex_normals(), M.F, segs, body)
    np.savez_compressed(cache, dist=dist, vis=vis)
names, W, info = rs_weights.compute(M, col, dist, vis)
np.savez_compressed(out, names=np.array(names), W=W, lab=info['lab'], verts=info['verts'], main_names=np.array(info['main_names']))
infl = (W > 0).sum(1)
print('weights: %d bones, influences per vertex %s' % (len(names), np.bincount(infl).tolist()))
print({n: round(float(t), 1) for n, t in zip(names, W.sum(0))})
