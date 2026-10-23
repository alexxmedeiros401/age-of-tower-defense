"""Preview helper (art-jobs only): the coarse character (char_game.blend) posed in its coarse base (base_q.blend, with
its procedural materials), rendered from game-like cameras.
    python3 sniper_combo.py -- --char C --base B --module sniper_base --out D --poses "Attack@0,30@3;Idle@0,90@30" --cams "az,el,dist;..." """
import sys, os, math, importlib
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import bpy
from mathutils import Vector
ARGS = sys.argv[sys.argv.index("--") + 1:]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d
import look, mats, prep, sdf
bs = importlib.import_module(arg("--module"))
OUT = arg("--out")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=arg("--char"))
look.relink(arg("--char"))
sc = bpy.context.scene
with bpy.data.libraries.load(arg("--base")) as (src, dst):
    dst.objects = [n for n in src.objects]
objs = []
for o in dst.objects:
    if o is None or o.type != "MESH":
        continue
    sc.collection.objects.link(o)
    objs.append(o)
for o in objs:
    if o.name in ("Grass", "Flowers"):
        m = bpy.data.materials.new("G" + o.name)
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = mats.lin((0.3, 0.52, 0.16) if o.name == "Grass" else (1.0, 0.85, 0.2))
        o.data.materials.append(m)
        continue
    sdf.fix_winding(o)
    prep.region_masks(o)
mats.assign_all([o for o in objs if o.name not in ("Grass", "Flowers")], getattr(bs, "MAT_OVERRIDES", None))
for nm, (col, strength, base) in getattr(bs, "GLOW", {}).items():
    o = bpy.data.objects.get(nm)
    if o:
        gm = bpy.data.materials.new("Glow" + nm)
        gm.use_nodes = True
        b = gm.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = mats.lin(tuple(c * base for c in col))
        b.inputs["Emission Color"].default_value = mats.lin(col)
        b.inputs["Emission Strength"].default_value = strength
        o.data.materials.clear()
        o.data.materials.append(gm)
arm = next(o for o in sc.objects if o.type == "ARMATURE")
arm.location = Vector(bs.STAND)
look.setup(samples=int(arg("--spp", "24")), res=(int(arg("--res", "640")), int(arg("--res", "640"))), transparent=False)
cams = [tuple(float(x) for x in c.split(",")) for c in arg("--cams", "0,52,6.2").split(";")]
for pz in arg("--poses").split(";"):
    act, rng, st = pz.split("@")
    a0, a1 = (int(x) for x in rng.split(","))
    arm.animation_data.action = bpy.data.actions[act]
    for f in range(a0, a1 + 1, int(st)):
        sc.frame_set(f)
        for ci, (az, el, dist) in enumerate(cams):
            look.camera((0.0, -0.1, 0.75), dist, az, el, lens=50)
            sc.render.filepath = os.path.join(OUT, "c%d_%s_%03d.png" % (ci, act, f))
            bpy.ops.render.render(write_still=True)
