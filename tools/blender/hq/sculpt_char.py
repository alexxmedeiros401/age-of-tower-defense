"""Mesh every high-poly part of a character and save a .blend (+ optional clay renders).

    python3 sculpt_char.py --character caveman|ugo [--fine] --out char_hi.blend [--shots DIR]
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import character
A = sys.argv
CH = character.use(A[A.index("--character") + 1] if "--character" in A else "caveman")
import sdf, preview as pv

COL = {"Skin": (0.86, 0.6, 0.45, 1), "Eyes": (0.95, 0.95, 0.92, 1), "Teeth": (0.95, 0.9, 0.75, 1), "Hair": (0.22, 0.14, 0.1, 1),
       "Beard": (0.25, 0.16, 0.11, 1), "Pelt": (0.85, 0.55, 0.22, 1), "Leather": (0.45, 0.27, 0.15, 1), "BagStones": (0.55, 0.55, 0.58, 1),
       "Cord": (0.5, 0.36, 0.2, 1), "Bone": (0.93, 0.88, 0.75, 1), "Sling": (0.45, 0.27, 0.15, 1), "SlingStone": (0.55, 0.55, 0.58, 1),
       "Hood": (0.85, 0.6, 0.25, 1), "Cape": (0.82, 0.56, 0.22, 1), "Fangs": (0.95, 0.92, 0.82, 1), "Cloth": (0.75, 0.15, 0.1, 1),
       "Feather": (0.95, 0.93, 0.88, 1)}
fine = "--fine" in A
only = A[A.index("--only") + 1].split(",") if "--only" in A else None
out = A[A.index("--out") + 1] if "--out" in A else "char_hi.blend"
bpy.ops.wm.read_factory_settings(use_empty=True)
T = time.time()
parts = CH.sculpt_parts(fine)
for name, f, vx in parts:
    if only and name not in only:
        continue
    V, Fc = f.mesh(vx)
    V, Fc = sdf.clean_islands(V, Fc)
    ob = sdf.to_blender(name, V, Fc)
    ob.color = COL.get(name, (0.7, 0.7, 0.7, 1))
    if name in getattr(CH, "REGION_PARTS", ("Skin",)):
        d, lab = f.eval(V.astype(np.float32), labels=True)
        a = ob.data.attributes.new("region", "INT", "POINT")
        a.data.foreach_set("value", lab.astype(np.int32))
        for L, dd in f.paint_dist(V.astype(np.float32)).items():
            pa = ob.data.attributes.new("p%d" % L, "FLOAT", "POINT")
            pa.data.foreach_set("value", np.clip(0.5 - dd / 0.006, -2.0, 3.0).astype(np.float32))
print("meshed in %.1fs" % (time.time() - T))
bpy.ops.wm.save_as_mainfile(filepath=out)
if "--shots" in A:
    D = A[A.index("--shots") + 1]
    os.makedirs(D, exist_ok=True)
    pv.setup()
    shots = []
    for i, (az, el) in enumerate(((0, 6), (35, 14), (95, 6), (160, 12))):
        shots.append(pv.shot(os.path.join(D, "f_%d.png" % i), (0, 0, 1.1), 6.6, az, el, lens=50, res=(560, 760)))
    pv.sheet(shots, os.path.join(D, "full_clay.png"))
    hz = CH.hp((0, 0, 1.7))[2]
    h = [pv.shot(os.path.join(D, "h_%d.png" % i), (0, -0.03, hz), 2.6, az, el, lens=85, res=(560, 560)) for i, (az, el) in enumerate(((0, 4), (32, 10), (80, 6), (150, 15)))]
    pv.sheet(h, os.path.join(D, "head_clay.png"))
