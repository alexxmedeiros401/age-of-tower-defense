"""Mesh every caveman part at production resolution and save char_hi.blend (+ clay renders)."""
import sys, time
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import bpy, numpy as np
import sdf, caveman as cm, preview as pv
bpy.ops.wm.read_factory_settings(use_empty=True)
T = time.time()
skin = cm.skin_field()
pelt = cm.pelt_field()
leather, bc, bagR = cm.leather_field(skin, pelt)
cord, bone = cm.necklace(skin, pelt)
sling, sstone = cm.sling_field()
COL = {"Skin": (0.86, 0.6, 0.45, 1), "Eyes": (0.95, 0.95, 0.92, 1), "Teeth": (0.95, 0.9, 0.75, 1), "Hair": (0.22, 0.14, 0.1, 1),
       "Beard": (0.25, 0.16, 0.11, 1), "Pelt": (0.85, 0.55, 0.22, 1), "Leather": (0.45, 0.27, 0.15, 1), "BagStones": (0.55, 0.55, 0.58, 1),
       "Cord": (0.5, 0.36, 0.2, 1), "Bone": (0.93, 0.88, 0.75, 1), "Sling": (0.45, 0.27, 0.15, 1), "SlingStone": (0.55, 0.55, 0.58, 1)}
fine = "--fine" in sys.argv
parts = [
    ("Skin", skin, 0.0032 if fine else 0.005),
    ("Eyes", cm.eyes_field(), 0.0015),
    ("Teeth", cm.teeth_field(), 0.0012),
    ("Hair", cm.hair_field(skin), 0.003 if fine else 0.0035),
    ("Beard", cm.beard_field(skin), 0.003 if fine else 0.0035),
    ("Pelt", pelt, 0.0035 if fine else 0.005),
    ("Leather", leather, 0.0025 if fine else 0.003),
    ("BagStones", cm.bag_stones(bc, bagR), 0.002),
    ("Cord", cord, 0.0015 if fine else 0.002),
    ("Bone", bone, 0.0015 if fine else 0.002),
    ("Sling", sling, 0.0015 if fine else 0.002),
    ("SlingStone", sstone, 0.002),
]
for name, f, vx in parts:
    V, Fc = f.mesh(vx)
    V, Fc = sdf.clean_islands(V, Fc)
    ob = sdf.to_blender(name, V, Fc)
    ob.color = COL[name]
    if name == "Skin":
        d, lab = skin.eval(V.astype(np.float32), labels=True)
        a = ob.data.attributes.new("region", "INT", "POINT")
        a.data.foreach_set("value", lab.astype(np.int32))
print("meshed in %.1fs" % (time.time() - T))
out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else ("char_hi.blend" if fine else "char_mid.blend")
bpy.ops.wm.save_as_mainfile(filepath=out)
if "--shots" in sys.argv:
    pv.setup()
    shots = []
    for i, (az, el) in enumerate(((0, 6), (35, 14), (95, 6), (160, 12))):
        shots.append(pv.shot("f_%d.png" % i, (0, 0, 1.05), 6.4, az, el, lens=50, res=(560, 760)))
    pv.sheet(shots, "full_clay.png")
    pv.shot("f_hero.png", (0, -0.05, 1.45), 4.2, 28, 12, lens=70, res=(900, 1100))
