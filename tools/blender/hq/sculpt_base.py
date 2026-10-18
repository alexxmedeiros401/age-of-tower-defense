import sys, time
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import bpy, numpy as np
import sdf, base as bs, preview as pv
bpy.ops.wm.read_factory_settings(use_empty=True)
COL = {"Ground": (0.36, 0.55, 0.22, 1), "Rocks": (0.55, 0.55, 0.58, 1), "Tusks": (0.93, 0.88, 0.75, 1), "BaseLeather": (0.45, 0.27, 0.15, 1),
       "Basket": (0.7, 0.55, 0.3, 1), "AmmoStones": (0.6, 0.6, 0.62, 1), "Wood": (0.42, 0.28, 0.16, 1), "Flame": (1.0, 0.6, 0.1, 1),
       "Pebbles": (0.6, 0.6, 0.62, 1), "Grass": (0.4, 0.65, 0.25, 1), "Flowers": (0.95, 0.9, 0.5, 1)}
fine = "--fine" in sys.argv
T = time.time()
for name, f, vx in bs.fields():
    V, Fc = f.mesh(vx * (0.75 if fine else 1.0))
    V, Fc = sdf.clean_islands(V, Fc, min_tris=30)
    ob = sdf.to_blender(name, V, Fc)
    ob.color = COL[name]
V, Fc, UV, TUFT = bs.grass_geometry()
me = bpy.data.meshes.new("Grass")
me.from_pydata([tuple(v) for v in V], [], Fc)
ob = bpy.data.objects.new("Grass", me); bpy.context.scene.collection.objects.link(ob); ob.color = COL["Grass"]
allv, allf = [], []
for v, f, kind, ck in bs.flower_geometry():
    b = len(allv); allv += [tuple(x) for x in v]; allf += [tuple(b + i for i in q) for q in f]
me = bpy.data.meshes.new("Flowers"); me.from_pydata(allv, [], allf)
ob = bpy.data.objects.new("Flowers", me); bpy.context.scene.collection.objects.link(ob); ob.color = COL["Flowers"]
print("base meshed in %.1fs" % (time.time() - T))
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else ("base_hi.blend" if fine else "base_mid.blend"))
if "--shots" in sys.argv:
    # stand-in for the caveman so the composition can be judged
    bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=2.0, location=(0, 0.06, bs.TOP_Z + 1.0))
    bpy.context.object.color = (0.86, 0.6, 0.45, 1)
    pv.setup()
    sh = [pv.shot("b_%d.png" % i, (0, 0, 0.9), 9.0, az, el, lens=50, res=(640, 640)) for i, (az, el) in enumerate(((0, 18), (35, 30), (120, 25)))]
    sh.append(pv.shot("b_top.png", (0, 0, 0.5), 9.5, 0, 68, lens=50, res=(640, 640)))
    pv.sheet(sh, "base_sheet.png")
