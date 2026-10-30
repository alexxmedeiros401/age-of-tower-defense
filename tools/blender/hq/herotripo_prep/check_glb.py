"""Round-trip check of a rebuilt hero GLB against the shipped one (Blender, light).

    python3 check_glb.py -- NEW.glb OLD.glb

Imports both and compares: objects (name, type, parent), mesh data names, materials and their image names, bones,
actions and their frame ranges, and the bones' world positions over each clip (they must not move: the rig and the
clips are the old ones). Prints OK or every difference.
"""
import sys, os
import numpy as np
import bpy

a = sys.argv[sys.argv.index("--") + 1:]


def grab(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    d = {}
    d["objects"] = sorted((o.name, o.type, o.parent.name if o.parent else None) for o in bpy.data.objects)
    d["meshes"] = sorted(o.data.name for o in bpy.data.objects if o.type == "MESH")
    d["materials"] = sorted((m.name, tuple(sorted(n.image.name for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image)))
                            for m in bpy.data.materials if m.node_tree)
    arm = bpy.data.objects["CavemanRig"]
    d["bones"] = sorted(b.name for b in arm.data.bones)
    d["actions"] = sorted((x.name, tuple(round(v, 3) for v in x.frame_range)) for x in bpy.data.actions)
    pos = {}
    arm.animation_data_create()
    for x in bpy.data.actions:
        arm.animation_data.action = x
        try:
            arm.animation_data.action_slot = x.slots[0]
        except Exception:
            pass
        for f in np.linspace(x.frame_range[0], x.frame_range[1], 6):
            bpy.context.scene.frame_set(int(round(f)))
            for pb in arm.pose.bones:
                pos[(x.name, int(round(f)), pb.name)] = np.array(arm.matrix_world @ pb.head)
    d["tris"] = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == "MESH"}
    return d, pos


n, pn = grab(a[0])
o, po = grab(a[1])
bad = 0
for k in ("objects", "meshes", "materials", "bones", "actions"):
    if n[k] != o[k]:
        bad += 1
        print("DIFF", k, "\n  new only:", sorted(set(n[k]) - set(o[k])), "\n  old only:", sorted(set(o[k]) - set(n[k])))
dmax = max(np.abs(pn[k] - po[k]).max() for k in po if k in pn)
missing = [k for k in po if k not in pn]
print("bone positions over the clips: max difference %.2e, %d samples missing" % (dmax, len(missing)))
if dmax > 1e-4 or missing:
    bad += 1
print("triangles new", n["tris"], "\n          old", o["tris"])
print("OK" if not bad else "%d DIFFERENCES" % bad)
