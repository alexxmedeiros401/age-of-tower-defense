"""Step 3 (Blender): the rigged scene. The shipped unit's base, torch, grass and node tree are kept as they are; its
character mesh and armature are replaced by the re-rigged ones (same names: CavemanRig / Caveman under Yaw, CavemanMat).

  python3 rs_build.py -- SHIPPED.glb OUT/mesh.npz OUT/weights.npz OUT/rs_rig.blend
"""
import sys, os
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rs_skel


def build(shipped, mesh_npz, weights_npz):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=shipped)
    sc = bpy.context.scene
    sc.render.fps = 24
    old_arm = bpy.data.objects['CavemanRig']; old_mesh = bpy.data.objects['Caveman']
    yaw = old_arm.parent
    mat = old_mesh.data.materials[0]
    coll = old_arm.users_collection[0]
    for o in [old_mesh, old_arm] + [o for o in bpy.data.objects if o.name.startswith('Icosphere')]:
        bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    for blk in (bpy.data.meshes, bpy.data.armatures):
        for d in list(blk):
            if d.users == 0: blk.remove(d)
    # ---- armature
    ad = bpy.data.armatures.new('CavemanRig')
    arm = bpy.data.objects.new('CavemanRig', ad)
    coll.objects.link(arm)
    arm.parent = yaw
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for name, parent, head, tail, kind in rs_skel.bones():
        eb = ad.edit_bones.new(name)
        eb.head = Vector(head); eb.tail = Vector(tail)
        y = (eb.tail - eb.head).normalized()
        ref = Vector((0, -1, 0)) if abs(y.y) < 0.85 else Vector((0, 0, 1))
        eb.align_roll(ref)
        eb.use_connect = False
        if parent: eb.parent = ad.edit_bones[parent]
        eb.use_deform = True
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    # ---- mesh
    d = np.load(mesh_npz); w = np.load(weights_npz, allow_pickle=True)
    V = d['V'] + rs_skel.SHIFT; F = d['F']; uv = d['uv']
    me = bpy.data.meshes.new('Caveman')
    me.from_pydata([tuple(v) for v in V], [], [tuple(int(i) for i in f) for f in F])
    me.update()
    uvl = me.uv_layers.new(name='UVMap')
    uvl.data.foreach_set('uv', uv.reshape(-1).astype(np.float32))
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.materials.append(mat)
    ob = bpy.data.objects.new('Caveman', me)
    coll.objects.link(ob)
    ob.parent = arm
    names = [str(n) for n in w['names']]; W = w['W']
    assert W.shape[0] == len(V), (W.shape, len(V))
    for j, nme in enumerate(names):
        vg = ob.vertex_groups.new(name=nme)
        idx = np.where(W[:, j] > 0)[0]
        for i in idx:
            vg.add([int(i)], float(W[i, j]), 'REPLACE')
    md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = arm
    me.update()
    return arm, ob


def rest_table(arm):
    names = [b.name for b in arm.data.bones]
    return dict(names=np.array(names), parents=np.array([b.parent.name if b.parent else '' for b in arm.data.bones]),
                rest=np.array([np.array(b.matrix_local) for b in arm.data.bones]))


if __name__ == '__main__':
    shipped, mesh_npz, weights_npz, out = sys.argv[sys.argv.index("--") + 1:][:4]
    arm, ob = build(shipped, mesh_npz, weights_npz)
    np.savez_compressed(os.path.join(os.path.dirname(out), 'rest.npz'), **rest_table(arm))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
    print('built', out, 'bones', len(arm.data.bones), 'verts', len(ob.data.vertices), 'tris', len(ob.data.polygons))
