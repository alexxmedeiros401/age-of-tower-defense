"""Dump a unit GLB to npz: character mesh rest verts (armature space), tris, weights, bones, base mesh verts (world), node transforms.
usage: -- GLB out.npz"""
import sys, bpy, numpy as np
src, out = sys.argv[sys.argv.index("--") + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
ch = [o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature() == arm][0]
me = ch.data
V = np.array([v.co[:] for v in me.vertices]); F = np.array([p.vertices[:] for p in me.polygons])
names = [g.name for g in ch.vertex_groups]
W = np.zeros((len(V), len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
base = bpy.data.objects.get('Base')
BV = np.array([(base.matrix_world @ v.co)[:] for v in base.data.vertices]); BF = np.array([p.vertices[:] for p in base.data.polygons], dtype=object)
bones = {b.name: (np.array(b.head_local[:]), np.array(b.tail_local[:]), np.array(b.matrix_local), b.parent.name if b.parent else '') for b in arm.data.bones}
np.savez_compressed(out, V=V, F=F, W=W, names=np.array(names), BV=BV, arm_world=np.array(arm.matrix_world), ch_world=np.array(ch.matrix_world),
                    bone_names=np.array(list(bones)), bone_head=np.array([bones[b][0] for b in bones]), bone_tail=np.array([bones[b][1] for b in bones]),
                    bone_mat=np.array([bones[b][2] for b in bones]), bone_parent=np.array([bones[b][3] for b in bones]))
print('arm world', np.array(arm.matrix_world).round(3).tolist())
print('char verts', V.shape, 'bbox', V.min(0).round(3), V.max(0).round(3))
print('base verts', BV.shape, 'bbox', BV.min(0).round(3), BV.max(0).round(3))
infl = (W > 0).sum(1); print('influences max', infl.max(), 'hist', np.bincount(infl))
