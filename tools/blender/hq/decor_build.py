"""HQ map kits: sculpt every prop of a Stone Age theme, bake them all into one texture atlas, export one GLB with one mesh
per prop (named as game.gd DECOR_V2 expects: Pine_A, Rock_C, Mammoth, Cave, ...), each at the origin, ground at y = 0.

    python3 decor_build.py -- --theme meadow|snow|volcano --out DIR [--stage sculpt|game|export|all] [--fine]
                              [--tex 2048] [--ao 24] [--only Pine_A,Rock_A] [--shots DIR]

Props are sculpted side by side (so their ambient occlusion doesn't mix), baked per part, then split and moved back to
the origin. Grass tufts and flower clumps are direct geometry coloured from a swatch strip on the right of the atlas.
Glowing parts (the volcano's lava) stay emissive (their own material slot, not baked).
"""
import sys, os, time, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d

import sdf, mats, prep
import lowpoly as lp
import bake as bk
import decor_props as DP
import decor_mats as DM

THEME = arg("--theme", "meadow")
OUT = arg("--out", "out_kit_" + THEME)
STAGE = arg("--stage", "all")
TEX = int(arg("--tex", "2048"))
AO_SPP = int(arg("--ao", "24"))
ONLY = arg("--only").split(",") if arg("--only") else None
DP.FINE[0] = "--fine" in ARGS
os.makedirs(OUT, exist_ok=True)
HI = os.path.join(OUT, "kit_hi.blend")
GAME = os.path.join(OUT, "kit_game.blend")
GLB = arg("--glb", {"meadow": "stone_decor", "snow": "stone_decor_snow", "volcano": "stone_decor_volcano",
                   "portal": "time_portal"}[THEME])
G0, G1, S0 = 0.05, 0.6, 0.7          # swatch strip: grass gradient rows, then flat colours (as in build_game.base_stage)
SWATCHES = [(0.97, 0.96, 0.92), (1.0, 0.86, 0.3), (0.72, 0.56, 0.96), (0.96, 0.52, 0.76), (0.3, 0.5, 0.18)]
GRASS = {"meadow": ((0.17, 0.34, 0.09), (0.6, 0.78, 0.3)), "snow": ((0.3, 0.27, 0.16), (0.62, 0.56, 0.36)),
         "volcano": ((0.16, 0.13, 0.1), (0.5, 0.42, 0.3))}.get(THEME, ((0.17, 0.34, 0.09), (0.6, 0.78, 0.3)))


def log(*a):
    print("[kit]", *a, flush=True)


def materials():
    th = THEME
    dark = mats.new("DK_Dark")
    dark.finish(dark.rgb((0.03, 0.025, 0.022)), 0.95)
    return {
        "needles": DM.needles("DK_Needles", th), "bark": DM.bark("DK_Bark", th), "charred": DM.bark("DK_Charred", th, charred=True),
        "leaves": DM.leaves("DK_Leaves"), "leaves_berry": DM.leaves("DK_LeavesBerry", berries=(0.85, 0.12, 0.15)),
        "rock": DM.rock("DK_Rock", th), "wood_end": DM.wood_end("DK_WoodEnd", th, charred=(th == "volcano")),
        "bone": DM.old_bone("DK_Bone", th), "hide": DM.hide("DK_Hide", th), "snow": DM.snowpack("DK_Snow"),
        "ice": DM.ice("DK_Ice"), "obsidian": DM.obsidian("DK_Obsidian"), "ochre": DM.ochre("DK_Ochre"),
        "turf": DM.turf("DK_Turf", th), "dark": dark.mat,
        "glow_lava": DM.glow("DK_GlowLava", (1.0, 0.45, 0.08), 2.2),
        "glow_cyan": DM.glow("DK_GlowCyan", (0.25, 0.85, 1.0), 2.2), "glow_magenta": DM.glow("DK_GlowMagenta", (1.0, 0.2, 0.85), 2.2),
        "portal_metal": __import__("robot_mats").gunmetal(name="DK_PortalMetal", base=(0.2, 0.22, 0.28), edge=(0.6, 0.66, 0.78),
                                                           labels=[(2, (0.1, 0.1, 0.12), 0.6)], seams=[2], scale=2.0),
        "portal_armor": __import__("robot_mats").armor(name="DK_PortalArmor", labels=[(1, (1.0, 0.47, 0.08), 0.35),
                                                       (2, (0.2, 0.2, 0.22), 0.6), (3, (0.08, 0.08, 0.09), 0.4)], seams=[2], scale=2.0),
    }
GLOW_KEYS = {"glow_lava": ((1.0, 0.45, 0.08), 1.6, 0.6), "glow_cyan": ((0.25, 0.85, 1.0), 1.3, 0.5),
             "glow_magenta": ((1.0, 0.2, 0.85), 1.3, 0.5)}      # (above ~1.5 glows wash out to pastel in game)


def kit():
    k = DP.KITS(THEME)
    return {n: v for n, v in k.items() if not ONLY or n in ONLY}


# ------------------------------------------------------------------------------------------------ sculpt
def sculpt_stage():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    T = time.time()
    x = 0.0
    for name, (fn, budget) in kit().items():
        parts = fn()
        meshes = []
        for part, f, vxs, mkey in parts:
            V, Fc = f.mesh(vxs)
            V, Fc = sdf.clean_islands(V, Fc, min_tris=30)
            meshes.append((part, V, Fc, mkey, f))
        lo = min(V[:, 0].min() for _, V, _, _, _ in meshes)
        hi = max(V[:, 0].max() for _, V, _, _, _ in meshes)
        off = x - lo
        x += (hi - lo) + 2.0
        tot = sum(len(Fc) for _, _, Fc, _, _ in meshes)
        for part, V, Fc, mkey, f in meshes:
            ob = sdf.to_blender("%s__%s" % (name, part), V + np.array([off, 0.0, 0.0]), Fc)
            ob["prop"] = name
            ob["part"] = part
            ob["mat"] = mkey
            ob["off"] = off
            ob["budget"] = max(40, int(budget * len(Fc) / max(tot, 1)))
            if any(op[0] == "paint" for op in f.ops):
                d, lab = f.eval(V.astype(np.float32), labels=True)
                a = ob.data.attributes.new("region", "INT", "POINT")
                a.data.foreach_set("value", lab.astype(np.int32))
                for L, dd in f.paint_dist(V.astype(np.float32)).items():
                    pa = ob.data.attributes.new("p%d" % L, "FLOAT", "POINT")
                    pa.data.foreach_set("value", np.clip(0.5 - dd / 0.006, -2.0, 3.0).astype(np.float32))
        log("sculpted", name, tot, "tris %.0fs" % (time.time() - T))
    bpy.ops.wm.save_as_mainfile(filepath=HI)
    if arg("--shots"):
        shots(arg("--shots"))


def shots(D):
    """Material preview of the high-poly kit: one wide shot of every prop in its row."""
    os.makedirs(D, exist_ok=True)
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    cache = materials()
    for o in objs:
        sdf.fix_winding(o)
        prep.region_masks(o)
        m = cache.get(o.get("mat"))
        if m is not None:
            o.data.materials.clear()
            o.data.materials.append(m)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 16
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Standard"
    wd = bpy.data.worlds.new("W")
    sc.world = wd
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.58, 0.68, 1)
    wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.2
    sun.rotation_euler = (math.radians(48), 0, math.radians(-30))
    sc.collection.objects.link(sun)
    lo = np.min([np.array(o.matrix_world @ Vector(c)) for o in objs for c in o.bound_box], 0)
    hi = np.max([np.array(o.matrix_world @ Vector(c)) for o in objs for c in o.bound_box], 0)
    W = hi[0] - lo[0]
    sc.render.resolution_x = 2400
    sc.render.resolution_y = min(1000, max(400, int(2400 * 6.0 / max(W, 1))))     # (a big frame costs GBs to render)
    cd = bpy.data.cameras.new("C")
    cd.type = "ORTHO"
    cd.ortho_scale = W * 1.04
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = Vector(((lo[0] + hi[0]) / 2, -30.0, 18.0))
    cam.rotation_euler = (Vector(((lo[0] + hi[0]) / 2, 0, 1.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(D, "kit_%s.png" % THEME)
    bpy.ops.render.render(write_still=True)
    if "--each" in ARGS:                       # plus a close-up of every prop from the game camera's angle
        from PIL import Image
        sc.render.resolution_x, sc.render.resolution_y = 640, 520
        sc.cycles.samples = 24
        props = {}
        for o in objs:
            props.setdefault(o.get("prop", o.name), []).append(o)
        tiles = []
        for name, obs in props.items():
            for o in objs:
                o.hide_render = o not in obs
            plo = np.min([np.array(o.matrix_world @ Vector(c)) for o in obs for c in o.bound_box], 0)
            phi = np.max([np.array(o.matrix_world @ Vector(c)) for o in obs for c in o.bound_box], 0)
            ctr = Vector(((plo + phi) / 2).tolist())
            r = float(np.linalg.norm(phi - plo)) / 2
            d = Vector((0.35, -0.75, 0.62)).normalized()
            cam.location = ctr + d * (r * 6)
            cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
            cd.ortho_scale = r * 2.1
            fp = os.path.join(D, "each_%s.png" % name)
            sc.render.filepath = fp
            bpy.ops.render.render(write_still=True)
            tiles.append((name, fp))
        for o in objs:
            o.hide_render = False
        cols = 4
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (640 * cols, 520 * rows), (120, 130, 145))
        for i, (name, fp) in enumerate(tiles):
            sheet.paste(Image.open(fp).convert("RGB"), ((i % cols) * 640, (i // cols) * 520))
        sheet.save(os.path.join(D, "each_%s.png" % THEME))
    log("shots ->", D)


# ------------------------------------------------------------------------------------------------ direct geometry
def tuft_geometry(rng, blades=9, r=0.12, h=0.19):
    V, F, UV = [], [], []
    for i in range(blades):
        a = 2 * math.pi * i / blades + rng.uniform(-0.3, 0.3)
        rr = r * rng.uniform(0.2, 0.8)
        hh = h * rng.uniform(0.6, 1.0)
        lean = rng.uniform(0.3, 0.7)
        bx, by = rr * 0.3 * math.cos(a), rr * 0.3 * math.sin(a)
        w = 0.018
        px, py = -math.sin(a) * w, math.cos(a) * w
        tip = (bx + math.cos(a) * hh * lean, by + math.sin(a) * hh * lean, hh)
        mid = (bx + math.cos(a) * hh * lean * 0.4 - px * 0.6, by + math.sin(a) * hh * lean * 0.4 - py * 0.6, hh * 0.55)
        mid2 = (bx + math.cos(a) * hh * lean * 0.4 + px * 0.6, by + math.sin(a) * hh * lean * 0.4 + py * 0.6, hh * 0.55)
        k = len(V)
        V += [(bx - px, by - py, -0.02), (bx + px, by + py, -0.02), mid2, mid, tip]
        UV += [0.0, 0.0, 0.55, 0.55, 1.0]
        F += [(k, k + 1, k + 2, k + 3), (k + 3, k + 2, k + 4)]
    return V, F, [(0.975, G0 + G1 * t) for t in UV]


def flowers_geometry(rng, n=6):
    V, F, UV = [], [], []
    for i in range(n):
        cx, cy = rng.uniform(-0.2, 0.2), rng.uniform(-0.17, 0.17)
        h = rng.uniform(0.1, 0.18)
        col = int(rng.integers(0, 4))
        # stem
        k = len(V)
        V += [(cx - 0.008, cy, 0.0), (cx + 0.008, cy, 0.0), (cx, cy, h)]
        F += [(k, k + 1, k + 2)]
        UV += [(0.975, S0 + 0.055 * 4 + 0.022)] * 3
        # petals: a flat star
        k = len(V)
        V.append((cx, cy, h + 0.004))
        UV.append((0.975, S0 + 0.055 * 1 + 0.022))        # yellow centre
        for j in range(10):
            a = 2 * math.pi * j / 10
            rr = 0.045 if j % 2 == 0 else 0.02
            V.append((cx + rr * math.cos(a), cy + rr * math.sin(a), h))
            UV.append((0.975, S0 + 0.055 * (0 if col == 1 else col) + 0.022) if col != 1 else (0.975, S0 + 0.055 * 3 + 0.022))
        for j in range(10):
            F.append((k, k + 1 + j, k + 1 + (j + 1) % 10))
    return V, F, UV


def mesh_from(name, V, F, UV, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = UV[me.loops[li].vertex_index]
        poly.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------------------------------------------ game
def game_stage():
    T = time.time()
    bpy.ops.wm.open_mainfile(filepath=HI)
    hi = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for o in hi:
        sdf.fix_winding(o)
        prep.region_masks(o)
    cache = materials()
    for o in hi:
        m = cache.get(o["mat"])
        o.data.materials.clear()
        o.data.materials.append(m)
    bake_hi = [o for o in hi if o["mat"] not in GLOW_KEYS]
    glow_hi = [o for o in hi if o["mat"] in GLOW_KEYS]
    pid = {o.name: i for i, o in enumerate(bake_hi)}
    props = sorted({o["prop"] for o in hi})
    prop_id = {p: i for i, p in enumerate(props)}
    low = []
    for o in bake_hi:
        lo_ob = lp.decimated_copy(o, int(o["budget"]), o.name + "_low")
        lp.tag_part(lo_ob, pid[o.name])
        a = lo_ob.data.attributes.new("prop", "INT", "FACE")
        a.data.foreach_set("value", np.full(len(lo_ob.data.polygons), prop_id[o["prop"]], np.int32))
        low.append(lo_ob)
    log("lowpoly", sum(len(o.data.polygons) for o in low), "tris %.0fs" % (time.time() - T))
    kitob = lp.join(low, "Kit")
    kitob.data.validate(clean_customdata=False)
    lp.unwrap(kitob, margin=0.003)
    uv = kitob.data.uv_layers.active.data
    co = np.zeros(len(uv) * 2, np.float32)
    uv.foreach_get("uv", co)
    co *= 0.94                                   # keep a free column on the right for the swatches
    uv.foreach_set("uv", co)
    log("uv %.0fs" % (time.time() - T))
    groups = [([pid[o.name]], [o]) for o in bake_hi]
    maps = bk.bake_groups(kitob, groups, TEX, ["DIFFUSE", "NORMAL", "ROUGHNESS", "AO"], ao_samples=AO_SPP, ao_dist=0.35,
                          extrusion=0.02, maxdist=0.06)
    log("bakes %.0fs" % (time.time() - T))
    from mats import lin
    def paint(a):
        h, w, _ = a.shape
        x0 = int(w * 0.955)
        c0, c1 = np.array(lin(GRASS[0])[:3]), np.array(lin(GRASS[1])[:3])
        for y in range(int(h * G0), int(h * (G0 + G1))):
            t = (y - h * G0) / (h * G1)
            a[y, x0:w - 4] = c0 * (1 - t) + c1 * t
        for i, c in enumerate(SWATCHES):
            y0 = int(h * (S0 + 0.055 * i))
            a[y0:y0 + int(h * 0.045), x0:w - 4] = np.array(lin(c)[:3])
        return a
    pa, pn, po = bk.save_maps(maps, OUT, GLB, ao_strength=0.75, extra_paint=paint, sat=1.08, val=1.02)
    nrm = np.asarray(__import__("PIL.Image", fromlist=["Image"]).open(pn)).copy()
    nrm[:, int(nrm.shape[1] * 0.95):] = (128, 128, 255)
    __import__("PIL.Image", fromlist=["Image"]).fromarray(nrm).save(pn)
    kmat = bk.game_material("KitMat", pa, pn, po)
    kitob.data.materials.clear()
    kitob.data.materials.append(kmat)
    # split per prop, back to the origin
    bm_all = kitob
    objs = {}
    for p in props:
        bm = bmesh.new()
        bm.from_mesh(bm_all.data)
        lay = bm.faces.layers.int.get("prop")
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] != prop_id[p]], context="FACES")
        if len(bm.faces) == 0:
            bm.free()
            continue
        me = bpy.data.meshes.new(p)
        bm.to_mesh(me)
        bm.free()
        off = next(o["off"] for o in hi if o["prop"] == p)
        me.transform(Matrix.Translation((-off, 0, 0)))
        ob = bpy.data.objects.new(p, me)
        bpy.context.scene.collection.objects.link(ob)
        me.materials.clear()
        me.materials.append(kmat)
        objs[p] = ob
    # glowing parts join their prop as a second, emissive surface
    for o in glow_hi:
        p = o["prop"]
        g = lp.decimated_copy(o, int(o["budget"]), o.name + "_glow")
        g.data.transform(Matrix.Translation((-o["off"], 0, 0)))
        col, strength, base = GLOW_KEYS[o["mat"]]
        gm = bpy.data.materials.get("Glow_" + o["mat"]) or bpy.data.materials.new("Glow_" + o["mat"])
        gm.use_nodes = True
        b = gm.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = mats.lin(tuple(c * base for c in col))
        b.inputs["Emission Color"].default_value = mats.lin(col)
        b.inputs["Emission Strength"].default_value = strength
        g.data.materials.clear()
        g.data.materials.append(gm)
        if p in objs:
            bpy.ops.object.select_all(action="DESELECT")
            objs[p].select_set(True)
            g.select_set(True)
            bpy.context.view_layer.objects.active = objs[p]
            bpy.ops.object.join()
        else:
            g.name = p
            objs[p] = g
    rng = np.random.default_rng(3)
    if THEME in ("meadow", "volcano"):
        V, F, UV = [], [], []
        for k in range(3):                          # a clump of three tufts
            v, f, u = tuft_geometry(rng)
            ox, oy = rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08)
            base = len(V)
            V += [(x + ox, y + oy, z) for x, y, z in v]
            F += [tuple(base + i for i in q) for q in f]
            UV += u
        objs["Tuft"] = mesh_from("Tuft", V, F, UV, kmat)
    if THEME == "meadow":
        V, F, UV = flowers_geometry(rng)
        objs["Flowers"] = mesh_from("Flowers", V, F, UV, kmat)
    bpy.data.objects.remove(bm_all)
    for o in hi:
        bpy.data.objects.remove(o)
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and o.name not in objs:
            bpy.data.objects.remove(o)
    for me in [me for me in bpy.data.meshes if me.users == 0]:
        bpy.data.meshes.remove(me)
    for ob in objs.values():
        ob.data.validate(clean_customdata=False)
    bpy.ops.wm.save_as_mainfile(filepath=GAME)
    log("game done %.0fs" % (time.time() - T), {k: len(v.data.polygons) for k, v in objs.items()})


def export_stage():
    bpy.ops.wm.open_mainfile(filepath=GAME)
    path = os.path.join(OUT, GLB + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_animations=False, export_tangents=True,
                              export_apply=False, export_yup=True, export_image_format="JPEG", export_jpeg_quality=92,
                              export_materials="EXPORT")
    log("exported", path, os.path.getsize(path))


if STAGE in ("sculpt", "all"):
    sculpt_stage()
if STAGE in ("game", "all"):
    game_stage()
if STAGE in ("export", "all"):
    export_stage()
if STAGE == "shots":
    bpy.ops.wm.open_mainfile(filepath=HI)
    shots(arg("--shots", os.path.join(OUT, "shots")))
