"""HQ Rock Slinger: high-poly sculpt -> rigged, animated, texture-baked game asset (GLB).

    python3 build_game.py -- --char char_hi.blend --base base_hi.blend --out DIR [--tex 2048] [--stage char|base|export|all]
"""
import sys, os, time, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import numpy as np
import bpy, bmesh
from mathutils import Vector
import caveman as cm, base as bs, lowpoly as lp, rig, anim, mats, prep, bake as bk

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d
CHAR = arg("--char", "/home/claude/work/hq/char_hi.blend")
BASE = arg("--base", "/home/claude/work/hq/base_hi.blend")
OUT = arg("--out", "/home/claude/work/hq/game")
TEX = int(arg("--tex", "2048"))
STAGE = arg("--stage", "all")
AO_SPP = int(arg("--ao", "32"))
os.makedirs(OUT, exist_ok=True)

PART_IDS = {n: i for i, n in enumerate(["Skin", "Eyes", "Teeth", "Hair", "Beard", "Pelt", "Leather", "BagStones", "Cord", "Bone", "Sling", "SlingStone"])}
TORSO = {"root", "spine", "chest", "neck"}


def log(*a):
    print("[game]", *a, flush=True)


def char_stage():
    T = time.time()
    bpy.ops.wm.open_mainfile(filepath=CHAR)
    hi = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
    import sdf
    for o in hi.values():
        sdf.fix_winding(o)
    prep.paint_skin(hi["Skin"])
    prep.paint_eyes(hi["Eyes"])
    mats.assign_all(list(hi.values()))
    low = {}
    for nm, tgt in lp.CHAR_TARGETS.items():
        low[nm] = lp.decimated_copy(hi[nm], tgt, nm + "_low")
    low["Eyes"] = lp.eyes_low()
    for nm, o in low.items():
        lp.tag_part(o, PART_IDS[nm])
    log("lowpoly", {k: len(v.data.polygons) for k, v in low.items()}, "%.0fs" % (time.time() - T))
    # rig + weights on the separate parts
    arm = rig.build_armature()
    rig.sdf_weights(low["Skin"], cm.skin_field(), arm)
    rig.transfer_weights(low["Skin"], low["Pelt"], allowed=TORSO | {"clavicle.L", "upperarm.L", "thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"},
                         caps={"thigh.R": 0.3, "thigh.L": 0.3, "upperarm.L": 0.85})
    rig.transfer_weights(low["Skin"], low["Leather"], allowed=TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "upperarm.R", "upperarm.L", "thigh.R"},
                         caps={"thigh.R": 0.3})
    rig.transfer_weights(low["Skin"], low["Cord"], allowed=TORSO | {"head"})
    rig.transfer_weights(low["Skin"], low["Bone"], allowed=TORSO | {"head"})
    rig.transfer_weights(low["Skin"], low["BagStones"], allowed=TORSO | {"thigh.R"}, caps={"thigh.R": 0.3})
    for nm in ("Hair", "Beard", "Eyes", "Teeth"):
        rig.rigid_weights(low[nm], "head")
    rig.rigid_weights(low["Sling"], "sling")
    rig.rigid_weights(low["SlingStone"], "stone")
    for o in low.values():
        rig.limit_and_normalize(o)
    for o in low.values():
        for m in list(o.modifiers):
            o.modifiers.remove(m)
        o.parent = None
    order = [low["Skin"]] + [o for n, o in low.items() if n != "Skin"]
    cav = lp.join(order, "Caveman")
    # UV atlas: more pixels for the face, eyes and hands
    hp = cm.hp
    face_z = hp((0, 0, 1.45))[2]
    def boost(c, part):
        if part == PART_IDS["Eyes"]:
            return 2.0
        if part in (PART_IDS["Cord"], PART_IDS["Sling"], PART_IDS["Bone"], PART_IDS["SlingStone"], PART_IDS["BagStones"]):
            return 0.6
        if part in (PART_IDS["Skin"], PART_IDS["Teeth"]) and c.z > face_z and c.y < 0.0:
            return 1.9
        if part == PART_IDS["Skin"] and (abs(c.x) > 0.62 and c.z < 1.0):
            return 1.35
        return 1.0
    lp.unwrap(cav, boost=boost, margin=0.0035)
    log("uv done %.0fs" % (time.time() - T))
    # bake (rest pose): each part only from its own sculpt; AO sees everything
    names = list(PART_IDS.keys())
    groups = [([PART_IDS[n]], [hi[n]]) for n in names if n in hi]
    maps = bk.bake_groups(cav, groups, TEX, ["DIFFUSE", "NORMAL", "ROUGHNESS", "AO"], ao_samples=AO_SPP, ao_dist=0.16,
                         ao_exclude=[hi[n] for n in ("Cord", "Bone", "Sling", "SlingStone", "BagStones", "Leather") if n in hi])
    log("bakes %.0fs" % (time.time() - T))
    pa, pn, po = bk.save_maps(maps, OUT, "caveman", ao_strength=0.7)
    mat = bk.game_material("CavemanMat", pa, pn, po)
    cav.data.materials.clear()
    cav.data.materials.append(mat)
    # skin it and animate
    m = cav.modifiers.new("Armature", "ARMATURE")
    m.object = arm
    cav.parent = arm
    anim.make_all(arm)
    for o in hi.values():
        bpy.data.objects.remove(o)
    for me in [me for me in bpy.data.meshes if me.users == 0]:
        bpy.data.meshes.remove(me)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "char_game.blend"))
    log("char done %.0fs, tris %d" % (time.time() - T, len(cav.data.polygons)))


def base_stage():
    T = time.time()
    bpy.ops.wm.open_mainfile(filepath=BASE)
    for o in list(bpy.context.scene.objects):
        if o.name in ("Grass", "Flowers"):
            bpy.data.objects.remove(o)
    hi = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
    import sdf
    for o in hi.values():
        sdf.fix_winding(o)
    mats.assign_all(list(hi.values()))
    low = []
    for nm, tgt in lp.BASE_TARGETS.items():
        if nm == "Flame":
            continue
        o = lp.decimated_copy(hi[nm], tgt, nm + "_low")
        low.append(o)
    baseob = lp.join(low, "Base")
    lp.unwrap(baseob, margin=0.003)
    # leave a free column on the right of the atlas for the grass/flower swatches
    uv = baseob.data.uv_layers.active.data
    co = np.zeros(len(uv) * 2, np.float32)
    uv.foreach_get("uv", co)
    co *= 0.94
    uv.foreach_set("uv", co)
    hi_list = [o for n, o in hi.items() if n != "Flame"]
    imgs = {}
    imgs["albedo"] = bk.bake(baseob, hi_list, bk.new_image("base_albedo", TEX), "DIFFUSE", samples=4, extrusion=0.02, maxdist=0.05)
    imgs["normal"] = bk.bake(baseob, hi_list, bk.new_image("base_normal", TEX, non_color=True), "NORMAL", samples=4, extrusion=0.02, maxdist=0.05)
    imgs["rough"] = bk.bake(baseob, hi_list, bk.new_image("base_rough", TEX, non_color=True), "ROUGHNESS", samples=2, extrusion=0.02, maxdist=0.05)
    imgs["ao"] = bk.bake(baseob, hi_list, bk.new_image("base_ao", TEX, non_color=True), "AO", samples=AO_SPP, extrusion=0.02, maxdist=0.05)
    log("base bakes %.0fs" % (time.time() - T))
    # swatches (linear colours) in the free column: grass gradient + flower colours
    from mats import lin
    def paint(a):
        h, w, _ = a.shape
        x0 = int(w * 0.955)
        for y in range(int(h * 0.05), int(h * 0.65)):
            t = (y - h * 0.05) / (h * 0.6)
            c0, c1 = np.array(lin((0.17, 0.34, 0.09))[:3]), np.array(lin((0.6, 0.78, 0.3))[:3])
            a[y, x0:w - 4] = c0 * (1 - t) + c1 * t
        for i, c in enumerate(((0.97, 0.96, 0.92), (1.0, 0.86, 0.3), (0.72, 0.56, 0.96), (1.0, 0.68, 0.14), (0.3, 0.5, 0.18))):
            y0 = int(h * (0.7 + 0.055 * i))
            a[y0:y0 + int(h * 0.045), x0:w - 4] = np.array(lin(c)[:3])
        return a
    pa, po = bk.compose(imgs["albedo"], imgs["ao"], imgs["rough"], OUT, "base", ao_strength=0.75, extra_paint=paint)
    nrm = bk.pixels(imgs["normal"])[..., :3]
    h, w, _ = nrm.shape
    nrm[:, int(w * 0.95):] = (0.5, 0.5, 1.0)
    pn = bk.save_png(nrm, os.path.join(OUT, "base_normal.png"))
    mat = bk.game_material("BaseMat", pa, pn, po)
    grass_mat = bk.game_material("Grass", pa, pn, po)
    baseob.data.materials.clear()
    baseob.data.materials.append(mat)
    baseob.data.materials.append(grass_mat)
    # grass-top faces of the ground use the "Grass" material (the game swaps it on snow/ash maps)
    part_ground = None
    for p in baseob.data.polygons:
        c = p.center
        r = math.hypot(c.x, c.y)
        if p.normal.z > 0.55 and c.z > 0.1 and c.z < 0.32 and r < bs.GROUND_R + 0.05 and not (r < 0.95 and c.z > 0.28):
            p.material_index = 1
    # grass blades + flowers: geometry with swatch UVs
    V, Fc, UV, TUFT = bs.grass_geometry()
    me = bpy.data.meshes.new("GrassBlades")
    me.from_pydata([tuple(v) for v in V], [], Fc)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            t = UV[vi][1]
            uvl.data[li].uv = (0.975, 0.05 + 0.6 * t)
        poly.use_smooth = True
    blades = bpy.data.objects.new("GrassBlades", me)
    bpy.context.scene.collection.objects.link(blades)
    me.materials.append(grass_mat)
    allv, allf, alluv = [], [], []
    for v, f, kind, ck in bs.flower_geometry():
        b = len(allv)
        allv += [tuple(x) for x in v]
        allf += [tuple(b + i for i in q) for q in f]
        sw = 4 if kind == 0 else (3 if kind == 2 else ck)
        alluv += [(0.975, 0.7 + 0.055 * sw + 0.02)] * len(v)
    me2 = bpy.data.meshes.new("Flowers")
    me2.from_pydata(allv, [], allf)
    uvl2 = me2.uv_layers.new(name="UVMap")
    for poly in me2.polygons:
        for li in poly.loop_indices:
            uvl2.data[li].uv = alluv[me2.loops[li].vertex_index]
    flowers = bpy.data.objects.new("Flowers", me2)
    bpy.context.scene.collection.objects.link(flowers)
    me2.materials.append(mat)
    # flame: own emissive object, origin at the torch head so flicker scales it upward
    fl = lp.decimated_copy(hi["Flame"], lp.BASE_TARGETS["Flame"], "FlickerTorch")
    pivot = bs.TORCH_TOP + np.array((0, 0, 0.02))
    fl.data.transform(__import__("mathutils").Matrix.Translation(-Vector(pivot)))
    fl.location = Vector(pivot)
    fl.data.materials.clear()
    fl.data.materials.append(bk.flame_material())
    for o in list(hi.values()):
        bpy.data.objects.remove(o)
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and o.name not in ("Base", "GrassBlades", "Flowers", "FlickerTorch"):
            bpy.data.objects.remove(o)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "base_game.blend"))
    log("base done %.0fs, tris %d" % (time.time() - T, sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type == "MESH")))


def export_stage():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "base_game.blend"))
    with bpy.data.libraries.load(os.path.join(OUT, "char_game.blend")) as (src, dst):
        dst.objects = [n for n in src.objects]
        dst.actions = [n for n in src.actions]
    sc = bpy.context.scene
    yaw = bpy.data.objects.new("Yaw", None)
    sc.collection.objects.link(yaw)
    yaw.location = Vector(bs.STAND)
    for o in dst.objects:
        if o is None:
            continue
        sc.collection.objects.link(o)
        if o.type == "ARMATURE":
            o.parent = yaw
            o.location = (0, 0, 0)
    root = bpy.data.objects.new("RockSlingerHQ", None)
    sc.collection.objects.link(root)
    for o in sc.objects:
        if o.parent is None and o is not root:
            o.parent = root
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "rock_slinger_hq.blend"))
    path = os.path.join(OUT, "rock_slinger.glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                              export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                              export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
    log("exported", path, os.path.getsize(path))


if STAGE in ("char", "all"):
    char_stage()
if STAGE in ("base", "all"):
    base_stage()
if STAGE in ("export", "all"):
    export_stage()
