"""Step 1 (Blender, light): the old hero's scene -> old.npz / old.json in the work folder.

    python3 old.py -- --hero ugo

Reads the old scene (a <id>_hq.blend, or the shipped assets/heroes/<id>.glb: Blender's glTF import keeps the armature,
the skin and the actions). Writes, all in CavemanRig's armature space (rest pose):
  old.npz: V (old mesh vertices), W (weights, one column per vertex group gn), T (triangles), Tprop (per triangle: the
           prop bone it rides, -1 for the body), bn/bm (bone names, rest matrices), bp (parent index, -1 for none)
  old.json: names (mesh, material, armature, the glows and other meshes on the rig), prop bones, the bones' heads and
           tails, the actions and their frame ranges.
A triangle belongs to a prop when its three vertices put more than half their weight on a prop bone. Prop bones are
the bones that are not part of the shared biped set (BIPED below) and that the clips do not use as deforming body
bones (cape.*, tail.*, hair.* ... stay body bones: list them in the config's "body_bones" if they are not in BIPED).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Matrix
import common as C

BIPED = {"root", "spine", "chest", "neck", "head", "clavicle.R", "upperarm.R", "forearm.R", "hand.R", "clavicle.L",
         "upperarm.L", "forearm.L", "hand.L", "thigh.R", "shin.R", "foot.R", "thigh.L", "shin.L", "foot.L"}
SOFT_PREFIX = ("cape", "tail", "hair", "skirt", "coat", "braid", "ear", "jaw", "scarf", "tabard", "cloak", "belt")


def open_old(path):
    if path.endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=path)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=path)
        # (the glTF importer adds a bone-shape Icosphere and names actions per object: strip that)
        ico = bpy.data.objects.get("Icosphere")
        if ico is not None and ico.parent is None and not ico.data.materials:
            bpy.data.objects.remove(ico)
    return bpy.data.objects["CavemanRig"]


def main():
    hid = C.arg("--hero")
    cfg = C.load_cfg(hid)
    W_DIR = C.work_dir(hid)
    arm = open_old(cfg["old"])
    rigged = [o for o in bpy.data.objects if o.type == "MESH" and o.parent == arm]
    if cfg["mesh"]:
        ob = bpy.data.objects[cfg["mesh"]]
    else:
        skinned = [o for o in rigged if any(m.type == "ARMATURE" for m in o.modifiers) and len(o.vertex_groups) > 3]
        ob = max(skinned, key=lambda o: len(o.data.polygons))
    mat = cfg["material"] or ob.data.materials[0].name
    to_arm = arm.matrix_world.inverted() @ ob.matrix_world
    me = ob.data
    V = np.array([to_arm @ v.co for v in me.vertices])
    gn = [g.name for g in ob.vertex_groups]
    W = np.zeros((len(V), len(gn)), np.float32)
    for v in me.vertices:
        for g in v.groups:
            W[v.index, g.group] = g.weight
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    me.calc_loop_triangles()
    T = np.array([t.vertices[:] for t in me.loop_triangles], np.int64)
    bones = list(arm.data.bones)
    bn = [b.name for b in bones]
    body_extra = set(cfg.get("body_bones", []))
    prop_bones = cfg.get("prop_bones") or [b for b in bn if b not in BIPED and b not in body_extra
                                           and not b.lower().startswith(SOFT_PREFIX)]
    Tprop = np.full(len(T), -1, np.int64)
    for j, pb in enumerate(prop_bones):
        if pb not in gn:
            continue
        w = W[:, gn.index(pb)]
        Tprop[(w[T] > 0.5).all(1)] = j
    rest = np.array([np.array(b.matrix_local) for b in bones])
    bp = np.array([bn.index(b.parent.name) if b.parent else -1 for b in bones])
    np.savez(os.path.join(W_DIR, "old.npz"), V=V, W=W, gn=np.array(gn), T=T, Tprop=Tprop, bn=np.array(bn), bm=rest, bp=bp)
    acts = {}
    for a in bpy.data.actions:
        acts[a.name] = [float(a.frame_range[0]), float(a.frame_range[1])]
    others = {o.name: dict(type=o.type, parent=o.parent.name if o.parent else None,
                           groups=[g.name for g in o.vertex_groups] if o.type == "MESH" else [],
                           tris=sum(len(p.vertices) - 2 for p in o.data.polygons) if o.type == "MESH" else 0)
              for o in bpy.data.objects}
    info = dict(mesh=ob.name, mesh_data=me.name, material=mat, armature=arm.name, prop_bones=prop_bones,
                bones={b.name: dict(head=list(b.head_local), tail=list(b.tail_local), parent=b.parent.name if b.parent else None)
                       for b in bones},
                actions=acts, objects=others, scene_fps=bpy.context.scene.render.fps,
                yaw_node=arm.parent.name if arm.parent else None,
                arm_world=[list(r) for r in arm.matrix_world])
    json.dump(info, open(os.path.join(W_DIR, "old.json"), "w"), indent=1)
    body = Tprop < 0
    vb = np.unique(T[body])
    print("[old] %s: mesh %s (%d verts, %d tris; %d prop tris on %s), material %s" % (
        hid, ob.name, len(V), len(T), (~body).sum(), {p: int((Tprop == j).sum()) for j, p in enumerate(prop_bones)}, mat))
    print("[old] body z %.3f..%.3f, actions %s" % (V[vb, 2].min(), V[vb, 2].max(), acts))


main()
