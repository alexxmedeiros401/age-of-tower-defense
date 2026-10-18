"""Measure how much ground every tower and hero model covers and write data/footprints.json.

    python3 tools/blender/footprints.py            (from the repo root; bpy as a Python module)

A unit's footprint is the radius of the base its model stands on, in world units at its in-game model_scale: the
99.5th percentile of the horizontal distance from the model's origin of all geometry in its lower part (below 0.45 model
units: the base, the sled of a catapult, the feet of a character), rounded up to the next 0.05. The sim keeps units at
least the sum of their footprints apart, so their bases never clip into each other. A footprint is never smaller than
the unit's placement radius (towers.json `radius`, or the sim's HERO_RADIUS for heroes). Re-run this after changing a
model or a model_scale.
"""
import json, math, os, sys
import numpy as np
import bpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
HERO_RADIUS = 0.6          # sim/sim.gd HERO_RADIUS
LOW = 0.45                 # model units: what counts as the base


def measure(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        M = np.array(o.matrix_world)
        pts.append(co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3])
        ev.to_mesh_clear()
    P = np.concatenate(pts)
    low = P[P[:, 2] < LOW]
    if len(low) == 0:
        low = P
    return float(np.percentile(np.sqrt(low[:, 0] ** 2 + low[:, 1] ** 2), 99.5))


def main():
    towers = json.load(open(os.path.join(ROOT, "data", "towers.json")))
    heroes = json.load(open(os.path.join(ROOT, "data", "heroes.json")))["heroes"]
    out = {"towers": {}, "heroes": {}}
    for kind, defs, folder, default_r, default_scale in (("towers", towers, "towers", None, 0.56), ("heroes", heroes, "heroes", HERO_RADIUS, 0.55)):
        for uid, d in defs.items():
            path = os.path.join(ROOT, "assets", folder, uid + ".glb")
            if not os.path.exists(path):
                print("no model for", uid)
                continue
            r = measure(path) * float(d.get("model_scale", default_scale))
            fp = max(float(d.get("radius", default_r)), math.ceil((r - 0.005) / 0.05) * 0.05)   # up to the next 0.05
            out[kind][uid] = round(fp, 2)
            print("%-7s %-18s %.3f -> %.2f" % (kind, uid, r, fp), flush=True)
    with open(os.path.join(ROOT, "data", "footprints.json"), "w") as f:
        f.write("{\n \"_about\": \"Ground covered by each unit's model (world units). Written by tools/blender/footprints.py; "
                "the sim keeps units at least the sum of their footprints apart.\",\n")
        for i, kind in enumerate(("towers", "heroes")):
            items = ", ".join('"%s": %s' % (k, v) for k, v in out[kind].items())
            f.write(' "%s": {%s}%s\n' % (kind, items, "," if i == 0 else ""))
        f.write("}\n")
    print("wrote data/footprints.json")


main()
