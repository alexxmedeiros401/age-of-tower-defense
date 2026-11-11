"""Step 1 (Blender): the bake's low.blend -> mesh.npz (LOW space). The sling's straps get edge loops across the chain,
so they can bend along it (they were long single triangles); nothing else changes (flat cuts, UVs interpolated).

  python3 rs_prep.py -- LOW.blend OUT/mesh.npz
"""
import sys, os
import bpy, bmesh
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rs_skel

src, out = sys.argv[sys.argv.index("--") + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects['HeroLow']; me = ob.data
n0 = len(me.polygons)
bm = bmesh.new(); bm.from_mesh(me)
part = bm.faces.layers.int.get('part')
assert part is not None
nodes = [n - rs_skel.SHIFT for n in rs_skel.sling_nodes()]      # LOW space
a, b = nodes[0], nodes[-1]
axis = (b - a) / np.linalg.norm(b - a); L = np.linalg.norm(b - a)
S = rs_skel.SLING_SEGS
cuts = [k / (2.0 * S) for k in range(1, 2 * S)]                 # at every node and every segment's middle
cuts = [t for t in cuts if t < 0.80]                            # the straps end at the cup's rim
for t in cuts:
    co = a + axis * (L * t)
    faces = [f for f in bm.faces if f[part] == 1]
    geom = faces + list({e for f in faces for e in f.edges}) + list({v for f in faces for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=Vector(co), plane_no=Vector(axis), clear_inner=False, clear_outer=False)
ng = [f for f in bm.faces if len(f.verts) > 3]
bmesh.ops.triangulate(bm, faces=ng)
bm.to_mesh(me); bm.free()
me.update()
V = np.array([v.co[:] for v in me.vertices], dtype=np.float64)
F = np.array([p.vertices[:] for p in me.polygons], dtype=np.int32)
pa = np.array([d.value for d in me.attributes['part'].data], dtype=np.int32)
uv = np.array([d.uv[:] for d in me.uv_layers['UVMap'].data], dtype=np.float64).reshape(len(F), 3, 2)
np.savez_compressed(out, V=V, F=F, part=pa, uv=uv)
print('faces %d -> %d, verts %d; sling faces %d, stone %d' % (n0, len(F), len(V), int((pa == 1).sum()), int((pa == 2).sum())))
