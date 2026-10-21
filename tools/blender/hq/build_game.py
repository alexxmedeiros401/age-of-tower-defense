"""HQ model: high-poly sculpt -> rigged, animated, texture-baked game asset (GLB).

    python3 build_game.py -- --character caveman|ugo --char char_hi.blend --base base_hi.blend --out DIR
                             [--tex 2048] [--ao 40] [--stage char|base|export|all]
The character module (caveman.py, ugo.py) supplies parts, decimation targets, weight rules, UV boosts, its base
module and its animation module.
"""
import sys, os, time, math, importlib
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d

import character
CH = character.use(arg("--character", "caveman"))
import lowpoly as lp, rig, mats, prep, bake as bk, sdf
bs = importlib.import_module(CH.BASE_MODULE)
an = importlib.import_module(CH.ANIM_MODULE)

CHAR = arg("--char", "char_hi.blend")
BASE = arg("--base", "base_hi.blend")
OUT = arg("--out", "out")
TEX = int(arg("--tex", "2048"))
STAGE = arg("--stage", "all")
AO_SPP = int(arg("--ao", "32"))
os.makedirs(OUT, exist_ok=True)
PART_IDS = {n: i for i, n in enumerate(CH.PARTS)}


def log(*a):
    print("[game]", *a, flush=True)


def glow_material(name, col, strength, base=1.0):
    """Emissive material for Glow* meshes. `base` < 1 darkens the albedo under the glow, which keeps a saturated hue in
    game (a bright albedo plus emission washes out to white or pastel)."""
    gm = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    gm.use_nodes = True
    b = gm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = mats.lin(tuple(c * base for c in col))
    b.inputs["Roughness"].default_value = 0.25
    b.inputs["Emission Color"].default_value = mats.lin(col)
    b.inputs["Emission Strength"].default_value = strength
    return gm


def _shift_parts(ob, pids, off):
    """Move the vertices of the faces tagged with any of these part ids (the joined low-poly's 'part' face layer)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    lay = bm.faces.layers.int.get("part")
    vs = set()
    for f in bm.faces:
        if f[lay] in pids:
            vs.update(f.verts)
    for v in vs:
        v.co += off
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def char_stage():
    T = time.time()
    bpy.ops.wm.open_mainfile(filepath=CHAR)
    hi = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
    for o in hi.values():
        sdf.fix_winding(o)
    for o in hi.values():
        prep.region_masks(o)
    prep.paint_skin(hi["Skin"])
    if "Eyes" in hi:                                 # (a full helm hides the face: no eyes)
        prep.paint_eyes(hi["Eyes"], getattr(CH, "IRIS", None))
    if hasattr(CH, "paint_extra"):
        CH.paint_extra(hi)
    mats.assign_all(list(hi.values()), getattr(CH, "MAT_OVERRIDES", None))
    glow = getattr(CH, "GLOW", {})                   # parts shipped as their own glowing mesh (spirit orb...), not baked
    low = {}
    for nm, tgt in CH.LOW_TARGETS.items():
        if nm in hi and nm not in glow:
            low[nm] = lp.decimated_copy(hi[nm], tgt, nm + "_low")
    if "Eyes" in hi:
        low["Eyes"] = lp.eyes_low()
    for nm, o in low.items():
        lp.tag_part(o, PART_IDS[nm])
    log("lowpoly", {k: len(v.data.polygons) for k, v in low.items()}, "%.0fs" % (time.time() - T))
    arm = rig.build_armature()
    rig.sdf_weights(low["Skin"], CH.skin_field(), arm)
    rules = CH.weight_rules()
    glow_obs = []
    for nm, spec in glow.items():
        if nm not in hi:
            continue
        g = lp.decimated_copy(hi[nm], CH.LOW_TARGETS.get(nm, 500), "Glow" + nm)
        rig.rigid_weights(g, rules[nm][1])
        g.data.materials.clear()
        g.data.materials.append(glow_material("Glow" + nm, *spec))
        glow_obs.append(g)
    for nm, o in low.items():
        if nm == "Skin":
            continue
        r = rules.get(nm, ("transfer", None, None))
        if r[0] == "rigid":
            rig.rigid_weights(o, r[1])
        elif r[0] == "custom":
            r[1](o, low["Skin"], arm)
        else:
            rig.transfer_weights(low["Skin"], o, allowed=r[1], caps=r[2])
    for o in low.values():
        rig.limit_and_normalize(o)
    for o in low.values():
        for m in list(o.modifiers):
            o.modifiers.remove(m)
        o.parent = None
    order = [low["Skin"]] + [o for n, o in low.items() if n != "Skin"]
    cav = lp.join(order, "Character")
    cav.data.validate(clean_customdata=False)          # drop duplicate faces left by decimation (glTF warns otherwise)
    names = {v: k for k, v in PART_IDS.items()}
    lp.unwrap(cav, boost=lambda c, pid: CH.uv_boost(c, names.get(pid, "")), margin=0.0035)
    log("uv done %.0fs" % (time.time() - T))
    groups = [([PART_IDS[n]], [hi[n]]) for n in CH.PARTS if n in hi and n not in glow]
    # BAKE_APART = (parts, offset): a machine and its crew are baked apart (moved `offset` away for the bake), so the
    # crew's rest pose leaves no shadow on the machine and the machine none on the crew
    apart = getattr(CH, "BAKE_APART", None)
    if apart:
        _shift_parts(cav, {PART_IDS[n] for n in apart[0] if n in PART_IDS}, Vector(apart[1]))
        for n in apart[0]:
            if n in hi:
                hi[n].location += Vector(apart[1])
    maps = bk.bake_groups(cav, groups, TEX, ["DIFFUSE", "NORMAL", "ROUGHNESS", "AO"], ao_samples=AO_SPP, ao_dist=0.16,
                         ao_exclude=[hi[n] for n in CH.AO_EXCLUDE if n in hi])
    if apart:
        _shift_parts(cav, {PART_IDS[n] for n in apart[0] if n in PART_IDS}, -Vector(apart[1]))
        for n in apart[0]:
            if n in hi:
                hi[n].location -= Vector(apart[1])
    log("bakes %.0fs" % (time.time() - T))
    pa, pn, po = bk.save_maps(maps, OUT, CH.TEX_PREFIX, ao_strength=0.7)
    mat = bk.game_material(CH.MAT_NAME, pa, pn, po)
    cav.data.materials.clear()
    cav.data.materials.append(mat)
    cav.name = getattr(CH, "MESH_NAME", "Caveman")
    cav.data.name = cav.name
    for nm, (oname, origin) in getattr(CH, "SPLIT", {}).items():
        # parts that ship as their own unskinned mesh (e.g. stones orbiting a hero, spun in game): same atlas and UVs
        pid = PART_IDS[nm]
        so = bk._group_object(cav, {pid}, oname)
        so.data.name = oname
        bm = bmesh.new()
        bm.from_mesh(cav.data)
        lay = bm.faces.layers.int.get("part")
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] == pid], context="FACES")
        bm.to_mesh(cav.data)
        bm.free()
        so.vertex_groups.clear()
        so.data.transform(Matrix.Translation(-Vector(origin)))
        so.location = Vector(origin)
        log("split", nm, "->", oname, len(so.data.polygons), "faces")
    m = cav.modifiers.new("Armature", "ARMATURE")
    m.object = arm
    cav.parent = arm
    for g in glow_obs:
        for p in g.data.polygons:
            p.use_smooth = True
        gm = g.modifiers.new("Armature", "ARMATURE")
        gm.object = arm
        g.parent = arm
    an.make_all(arm)
    for o in hi.values():
        bpy.data.objects.remove(o)
    for me in [me for me in bpy.data.meshes if me.users == 0]:
        bpy.data.meshes.remove(me)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "char_game.blend"))
    log("char done %.0fs, tris %d" % (time.time() - T, len(cav.data.polygons)))


def base_stage():
    global G0, G1, S0
    if getattr(bs, "EXTRA_SWATCHES", None):
        G0, G1, S0 = 0.04, 0.54, 0.62                  # grass gradient 0.04-0.58, up to 7 swatches from 0.62
    else:
        G0, G1, S0 = 0.05, 0.6, 0.7                    # the layout the first bases were baked with
    T = time.time()
    bpy.ops.wm.open_mainfile(filepath=BASE)
    for o in list(bpy.context.scene.objects):
        if o.name in ("Grass", "Flowers"):
            bpy.data.objects.remove(o)
    hi = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
    for o in hi.values():
        sdf.fix_winding(o)
        prep.region_masks(o)
    mats.assign_all(list(hi.values()), getattr(bs, "MAT_OVERRIDES", None))
    low = []
    glow = getattr(bs, "GLOW", {})                  # parts kept as their own glowing mesh (not baked into the base)
    for nm, tgt in bs.LOW_TARGETS.items():
        if nm == "Flame" or nm not in hi or nm in glow:
            continue
        low.append(lp.decimated_copy(hi[nm], tgt, nm + "_low"))
    baseob = lp.join(low, "Base")
    baseob.data.validate(clean_customdata=False)          # duplicate faces from decimation (glTF warns otherwise)
    lp.unwrap(baseob, margin=0.003)
    uv = baseob.data.uv_layers.active.data
    co = np.zeros(len(uv) * 2, np.float32)
    uv.foreach_get("uv", co)
    co *= 0.94                                   # free column on the right for grass/flower swatches
    uv.foreach_set("uv", co)
    hi_list = [o for n, o in hi.items() if n != "Flame"]
    imgs = {}
    kw = dict(extrusion=0.02, maxdist=0.05)
    imgs["albedo"] = bk.bake(baseob, hi_list, bk.new_image("base_albedo", TEX), "DIFFUSE", samples=4, **kw)
    imgs["normal"] = bk.bake(baseob, hi_list, bk.new_image("base_normal", TEX, non_color=True), "NORMAL", samples=4, **kw)
    imgs["rough"] = bk.bake(baseob, hi_list, bk.new_image("base_rough", TEX, non_color=True), "ROUGHNESS", samples=2, **kw)
    imgs["ao"] = bk.bake(baseob, hi_list, bk.new_image("base_ao", TEX, non_color=True), "AO", samples=AO_SPP, **kw)
    log("base bakes %.0fs" % (time.time() - T))
    from mats import lin
    swatches = [(0.97, 0.96, 0.92), (1.0, 0.86, 0.3), (0.72, 0.56, 0.96), (1.0, 0.68, 0.14), (0.3, 0.5, 0.18)] + \
               list(getattr(bs, "EXTRA_SWATCHES", []))
    def paint(a):
        h, w, _ = a.shape
        x0 = int(w * 0.955)
        for y in range(int(h * G0), int(h * (G0 + G1))):
            t = (y - h * G0) / (h * G1)
            c0, c1 = np.array(lin((0.17, 0.34, 0.09))[:3]), np.array(lin((0.6, 0.78, 0.3))[:3])
            a[y, x0:w - 4] = c0 * (1 - t) + c1 * t
        for i, c in enumerate(swatches):
            y0 = int(h * (S0 + 0.055 * i))
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
    for p in baseob.data.polygons:
        if bs.is_grass_face(p.center, p.normal):
            p.material_index = 1
    V, Fc, UV, TUFT = bs.grass_geometry()
    me = bpy.data.meshes.new("GrassBlades")
    me.from_pydata([tuple(v) for v in V], [], Fc)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            t = UV[me.loops[li].vertex_index][1]
            uvl.data[li].uv = (0.975, G0 + G1 * t)
        poly.use_smooth = True
    blades = bpy.data.objects.new("GrassBlades", me)
    bpy.context.scene.collection.objects.link(blades)
    me.materials.append(grass_mat)
    allv, allf, alluv = [], [], []
    for v, f, kind, ck in bs.flower_geometry():
        b = len(allv)
        allv += [tuple(x) for x in v]
        allf += [tuple(b + i for i in q) for q in f]
        sw = {0: 4, 2: 3, 3: 5}.get(kind, ck)           # stem, centre, extra (e.g. cattail heads), else petal colour
        alluv += [(0.975, S0 + 0.055 * sw + 0.022)] * len(v)
    if allv:
        me2 = bpy.data.meshes.new("Flowers")
        me2.from_pydata(allv, [], allf)
        uvl2 = me2.uv_layers.new(name="UVMap")
        for poly in me2.polygons:
            for li in poly.loop_indices:
                uvl2.data[li].uv = alluv[me2.loops[li].vertex_index]
        flowers = bpy.data.objects.new("Flowers", me2)
        bpy.context.scene.collection.objects.link(flowers)
        me2.materials.append(mat)
    keep = {"Base", "GrassBlades", "Flowers"}
    for nm, spec in glow.items():
        if nm not in hi:
            continue
        g = lp.decimated_copy(hi[nm], bs.LOW_TARGETS.get(nm, 600), "Glow" + nm)
        g.data.materials.clear()
        g.data.materials.append(glow_material("Glow" + nm, *spec))
        for p in g.data.polygons:
            p.use_smooth = True
        keep.add(g.name)
    for i, ((bx, by), br) in enumerate(getattr(bs, "BUBBLES", [])):
        # tar bubbles: little domes with their origin on the tar, swollen and popped in game (Bubble*)
        bmb = bmesh.new()
        bmesh.ops.create_uvsphere(bmb, u_segments=12, v_segments=8, radius=br)
        for v in list(bmb.verts):
            if v.co.z < -1e-6:
                v.co.z = 0.0
        bmesh.ops.remove_doubles(bmb, verts=bmb.verts, dist=1e-5)
        meb = bpy.data.meshes.new("Bubble%d" % i)
        bmb.to_mesh(meb)
        bmb.free()
        ob = bpy.data.objects.new("Bubble%d" % i, meb)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = (bx, by, bs.TAR_Z)
        for p in meb.polygons:
            p.use_smooth = True
        tm = bpy.data.materials.get("TarBubble") or bpy.data.materials.new("TarBubble")
        tm.use_nodes = True
        pb = tm.node_tree.nodes["Principled BSDF"]
        pb.inputs["Base Color"].default_value = mats.lin((0.07, 0.06, 0.06))
        pb.inputs["Roughness"].default_value = 0.12
        meb.materials.append(tm)
        keep.add(ob.name)
    if "Flame" in hi and getattr(bs, "FLAME_PIVOT", None) is not None:
        fl = lp.decimated_copy(hi["Flame"], bs.LOW_TARGETS.get("Flame", 160), "FlickerTorch")
        pivot = bs.FLAME_PIVOT
        fl.data.transform(Matrix.Translation(-Vector(pivot)))
        fl.location = Vector(pivot)
        fl.data.materials.clear()
        fl.data.materials.append(bk.flame_material(color=getattr(bs, "FLAME_COLOR", (1.0, 0.62, 0.16)),
                                                  strength=getattr(bs, "FLAME_STRENGTH", 2.5)))
        keep.add("FlickerTorch")
    for o in list(hi.values()):
        bpy.data.objects.remove(o)
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and o.name not in keep:
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
    pivot = Vector(getattr(CH, "YAW_PIVOT", (0, 0, 0)))   # the tower turns about this point (character space)
    yaw.location = Vector(bs.STAND) + pivot
    for o in dst.objects:
        if o is None:
            continue
        sc.collection.objects.link(o)
        if o.type == "ARMATURE":
            o.parent = yaw
            o.location = -pivot
        elif o.name in [v[0] for v in getattr(CH, "SPLIT", {}).values()]:
            o.location = Vector(bs.STAND) + Vector(o.location)          # unskinned split parts sit where she stands
    root = bpy.data.objects.new(CH.ROOT_NAME, None)
    sc.collection.objects.link(root)
    for o in sc.objects:
        if o.parent is None and o is not root:
            o.parent = root
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, CH.GLB_NAME + "_hq.blend"))
    path = os.path.join(OUT, CH.GLB_NAME + ".glb")
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
