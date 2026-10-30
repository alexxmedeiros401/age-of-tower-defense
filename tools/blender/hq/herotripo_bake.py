"""Generic Tripo hero, step 6 (GitHub runner): high-poly pieces -> decimated game mesh, fresh UV atlas, baked maps.

    python3 herotripo_bake.py -- --hero ugo --in herotripo_in/ugo --out OUT [--test]

Inputs (--in): tripo.glb (the Tripo model, plain floats: herotripo_prep/decode.mjs), labels.npz (cut.py), patches.pkl
(patches.py), fit.json (fit.py: the Tripo -> game transform 'xf' and the fitted pose's landmarks); the config is
herotripo_cfg/<hero>.json. Everything is put in game units in the Tripo model's own pose (rigging comes after:
herotripo_rig.py). The body and each prop are decimated on their own (the body with a vertex-group bias that keeps the
head, most of all the face, and the hands denser; the head's share of the body's triangles is searched to cfg
head_share), joined with a `part` face layer (0 body, k the k-th prop), unwrapped with xatlas (each chart scaled by its
region's texel boost: the face cfg face_boost), and baked piece by piece from its own high-poly: base colour and
roughness-metal as emission, the normal map, ambient occlusion. Writes OUT/low.blend (mesh HeroLow, Tripo pose),
OUT/hero_{albedo,normal,orm}.png and OUT/look/*.png.
--test: a quick local check of the code path (the head only, 512 maps).
"""
import sys, os, time, json, pickle, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
sys.path.insert(0, os.path.join(HQ, "herotripo_prep"))
import numpy as np
import bpy, bmesh
from mathutils import Vector
import common as C

HID = C.arg("--hero")
CFG = C.load_cfg(HID)
IN = C.arg("--in", os.path.join(HQ, "herotripo_in", HID))
OUT = C.arg("--out", "out")
TEST = "--test" in sys.argv
TEX = 512 if TEST else int(C.arg("--tex", CFG["tex"]))
os.makedirs(OUT, exist_ok=True)
T0 = time.time()


def log(*a):
    print("[ht] %5.0fs" % (time.time() - T0), *a, flush=True)


PB, UV, I = C.read_glb(os.path.join(IN, "tripo.glb"), OUT)
q = np.round(PB.astype(np.float32).astype(np.float64) * 1e5).astype(np.int64)
_, inv = np.unique(q, axis=0, return_inverse=True)
inv = inv.ravel()
del q
Pw = np.zeros((inv.max() + 1, 3))
Pw[inv] = PB.astype(np.float32)
F = inv[I]
LZ = np.load(os.path.join(IN, "labels.npz"))
lab, NAMES = LZ["lab"].copy(), [str(x) for x in LZ["names"]]
assert len(lab) == len(F), (len(lab), len(F))
patches = pickle.load(open(os.path.join(IN, "patches.pkl"), "rb"))
FIT = json.load(open(os.path.join(IN, "fit.json")))
XF = FIT["xf"]
MK = FIT["posed"]                                   # fitted-pose landmarks (game units, Tripo pose)
PIECES = [k for k in range(len(NAMES)) if (lab == k).any()]
log("tripo", len(PB), "verts", len(F), "faces; pieces", {NAMES[k]: int((lab == k).sum()) for k in PIECES}, "xf", XF)
NECK_Z = 0.5 * (MK["neck"]["head"][2] + MK["neck"]["tail"][2])
HEAD_C = np.array(MK["head"]["head"]) * 0.6 + np.array(MK["head"]["tail"]) * 0.4
HANDS = [np.array(MK[h]["head"]) * 0.4 + np.array(MK[h]["tail"]) * 0.6 for h in ("hand.R", "hand.L") if h in MK]
FEET_Z = min(MK[f]["head"][2] for f in ("foot.R", "foot.L") if f in MK)
if TEST:
    keep = (lab == 0) & (C.to_game(Pw[F].mean(1), XF)[:, 2] < NECK_Z)
    lab[keep] = 255
    patches["body"] = []


def to_game(X):
    return C.to_game(X, XF)


def srgb_to_lin(a):
    return np.where(a <= 0.04045, a / 12.92, np.power((a + 0.055) / 1.055, 2.4))


# ------------------------------------------------------------------------------------------------ materials
def tripo_material():
    m = bpy.data.materials.new("TripoMat")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    def tex(role, cs):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(C.tex_path(OUT, role))
        n.image.colorspace_settings.name = cs
        return n
    tb, trm, tn = tex("base", "sRGB"), tex("rm", "Non-Color"), tex("normal", "Non-Color")
    tb.name, trm.name = "BASE", "RM"
    nt.links.new(tb.outputs["Color"], b.inputs["Base Color"])
    sc = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(trm.outputs["Color"], sc.inputs[0])
    nt.links.new(sc.outputs["Green"], b.inputs["Roughness"])
    nt.links.new(sc.outputs["Blue"], b.inputs["Metallic"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Emission Strength"].default_value = 1.0


def patch_material():
    m = bpy.data.materials.new("PatchMat")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    for nm in ("pcol", "prm"):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = nm
        a.name = nm.upper()
    nt.links.new(nt.nodes["PCOL"].outputs["Color"], b.inputs["Base Color"])
    b.inputs["Emission Strength"].default_value = 1.0


def emit_source(which):
    for mname, node in (("TripoMat", {"base": "BASE", "rm": "RM"}), ("PatchMat", {"base": "PCOL", "rm": "PRM"})):
        nt = bpy.data.materials[mname].node_tree
        b = nt.nodes["Principled BSDF"]
        for l in list(b.inputs["Emission Color"].links):
            nt.links.remove(l)
        nt.links.new(nt.nodes[node[which]].outputs["Color"], b.inputs["Emission Color"])


# ------------------------------------------------------------------------------------------------ high-poly pieces
def hi_piece(L, name):
    Fm = F[lab == L]
    used = np.unique(Fm)
    remap = np.full(Pw.shape[0], -1)
    remap[used] = np.arange(len(used))
    V, Fs = [Pw[used]], [remap[Fm]]
    corner_uv = [UV[I[lab == L]].reshape(-1, 2)]
    mat = [np.zeros(len(Fm), np.int32)]
    nv = len(used)
    pcol, prm = np.zeros((nv, 3)), np.zeros((nv, 3))
    pcols, prms = [pcol], [prm]
    for (Lr, Pin, tris, col, rmv) in patches.get(NAMES[L], []):
        n = len(Lr)
        if (remap[Lr] < 0).any():
            continue
        idx = np.r_[remap[Lr], nv + np.arange(len(Pin))]
        V.append(Pin)
        Fs.append(idx[tris])
        corner_uv.append(np.zeros((len(tris) * 3, 2), np.float32))
        mat.append(np.ones(len(tris), np.int32))
        pcol[remap[Lr]] = col[:n]
        prm[remap[Lr]] = rmv[:n]
        pcols.append(col[n:])
        prms.append(rmv[n:])
        nv += len(Pin)
    V = to_game(np.concatenate(V))
    Fc = np.concatenate(Fs)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(Fc.size)
    me.loops.foreach_set("vertex_index", Fc.astype(np.int32).ravel())
    me.polygons.add(len(Fc))
    me.polygons.foreach_set("loop_start", np.arange(0, Fc.size, 3, dtype=np.int32))
    me.update(calc_edges=True)
    uvl = me.uv_layers.new(name="UVMap")
    cu = np.concatenate(corner_uv).astype(np.float32).copy()
    cu[:, 1] = 1.0 - cu[:, 1]
    uvl.data.foreach_set("uv", cu.ravel())
    me.polygons.foreach_set("material_index", np.concatenate(mat))
    me.polygons.foreach_set("use_smooth", np.ones(len(Fc), bool))
    for nm, arr in (("pcol", srgb_to_lin(np.clip(np.concatenate(pcols), 0, 1))), ("prm", np.clip(np.concatenate(prms), 0, 1))):
        a = me.attributes.new(nm, "FLOAT_COLOR", "POINT")
        a.data.foreach_set("color", np.c_[arr, np.ones(len(arr))].astype(np.float32).ravel())
    me.materials.append(bpy.data.materials["TripoMat"])
    me.materials.append(bpy.data.materials["PatchMat"])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    log("hi", name, len(V), "verts", len(Fc), "faces")
    return ob


bpy.ops.wm.read_factory_settings(use_empty=True)
tripo_material()
patch_material()
HI = {k: hi_piece(k, "Hi_" + NAMES[k]) for k in PIECES}


# ------------------------------------------------------------------------------------------------ decimation
def head_bias(V, wh):
    """Decimation weights (lower = kept denser): the head (above the neck), most of all the face, and the hands."""
    w = np.ones(len(V))
    head = np.clip((V[:, 2] - NECK_Z) / 0.07, 0, 1)
    face = head * np.clip((-(V[:, 1] - HEAD_C[1]) + 0.02) / 0.1, 0, 1)
    w -= head * (1 - wh) * 0.7 + face * (1 - wh) * 0.3
    for h in HANDS:
        hands = np.clip((0.16 - np.linalg.norm(V - h, axis=1)) / 0.05, 0, 1)
        w -= hands * (1 - wh) * 0.3
    return np.clip(w, 0.02, 1.0)


def decimate(src, target, name, bias=None):
    tmp = src.copy()
    tmp.data = src.data.copy()
    bpy.context.scene.collection.objects.link(tmp)
    bm = bmesh.new()
    bm.from_mesh(tmp.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-7, edges=bm.edges)
    bm.to_mesh(tmp.data)
    bm.free()
    nf = len(tmp.data.polygons)
    m = tmp.modifiers.new("Dec", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = min(1.0, target / nf)
    m.use_collapse_triangulate = True
    if bias is not None:
        co = np.zeros(len(tmp.data.vertices) * 3)
        tmp.data.vertices.foreach_get("co", co)
        w = np.round(bias(co.reshape(-1, 3)), 3)
        g = tmp.vertex_groups.new(name="dec")
        for val in np.unique(w):
            g.add(np.nonzero(w == val)[0].tolist(), float(val), "REPLACE")
        m.vertex_group = "dec"
        m.vertex_group_factor = 1.0
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    old = tmp.data
    bpy.data.objects.remove(tmp)
    bpy.data.meshes.remove(old)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    for a in [a.name for a in me.attributes if a.name in ("pcol", "prm")]:
        me.attributes.remove(me.attributes[a])
    return ob


def prop_target(k):
    p = CFG["props"][k - 1]
    if "tris" in p:
        return int(p["tris"])
    share = (lab == k).sum() / len(lab)
    return int(np.clip(share * CFG["tris"] * 1.5, 250, 2500))


TARGETS = {k: prop_target(k) for k in PIECES if k > 0}
TARGETS[0] = (3000 if TEST else CFG["tris"]) - sum(TARGETS.values())
log("targets", {NAMES[k]: v for k, v in TARGETS.items()})
HEAD_SHARE = 1.0 if TEST else CFG["head_share"]
LOW = {}
lo_w, hi_w, wh = 0.0, 1.0, float(CFG.get("head_w", 0.969))
for it in range(6):
    ob = decimate(HI[0], TARGETS[0], "Body_low", lambda V: head_bias(V, wh))
    Cf = np.array([p.center for p in ob.data.polygons])
    share = (Cf[:, 2] > NECK_Z).mean()
    log("decimate body: head weight %.3f -> %d tris, head share %.3f" % (wh, len(Cf), share))
    if abs(share - HEAD_SHARE) < 0.02 or it == 5 or TEST:
        break
    bpy.data.objects.remove(ob)
    if share < HEAD_SHARE:
        hi_w = wh
    else:
        lo_w = wh
    wh = (lo_w + hi_w) / 2
LOW[0] = ob
for k in PIECES:
    if k > 0:
        LOW[k] = decimate(HI[k], TARGETS[k], "Low_" + NAMES[k])
for k, o in LOW.items():
    a = o.data.attributes.new("part", "INT", "FACE")
    a.data.foreach_set("value", np.full(len(o.data.polygons), k, np.int32))
    o.data.materials.clear()
    log("low", o.name, len(o.data.polygons))

import lowpoly as lp
import bake as bk
joined = lp.join([LOW[k] for k in sorted(LOW)], "HeroLow")
joined.data.validate(clean_customdata=False)
for l in list(joined.data.uv_layers):
    joined.data.uv_layers.remove(l)
joined.data.uv_layers.new(name="UVMap")
FB = float(CFG["face_boost"])


def uv_boost(c, part):
    if part == 0 and c[2] > NECK_Z:
        return FB if c[1] < HEAD_C[1] else 1.5
    if part == 0 and any(np.linalg.norm(c - h) < 0.14 for h in HANDS):
        return 1.15
    if part > 0:
        return float(CFG["props"][part - 1].get("uv_boost", 1.2))
    if part == 0 and c[2] < FEET_Z + 0.12:
        return 0.65
    return 1.0


def xatlas_unwrap(ob, boost, padding=4):
    """xatlas charts on the real shape, each scaled by its region's boost, then packed again (brute force)."""
    import xatlas
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    me = ob.data
    V = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    assert all(len(p.vertices) == 3 for p in me.polygons)
    Fi = np.zeros(len(me.polygons) * 3, np.int32)
    me.polygons.foreach_get("vertices", Fi)
    Fi = Fi.reshape(-1, 3)
    part = np.zeros(len(me.polygons), np.int32)
    me.attributes["part"].data.foreach_get("value", part)
    at = xatlas.Atlas()
    at.add_mesh(V, Fi)
    co = xatlas.ChartOptions()
    co.max_iterations = 2
    co.normal_deviation_weight = 0.5
    po = xatlas.PackOptions()
    po.padding = 2
    po.resolution = TEX
    at.generate(co, po)
    vmap, ind, uvs = at[0]
    n = len(uvs)
    e = np.r_[ind[:, [0, 1]], ind[:, [1, 2]]]
    _, isl = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    fisl = isl[ind[:, 0]]
    cen = V[Fi].mean(1)
    uvs = uvs.copy()
    for i in np.unique(fisl):
        fm = fisl == i
        sc_ = float(np.mean([boost(c, p) for c, p in zip(cen[fm], part[fm])]))
        vs = np.unique(ind[fm])
        c = uvs[vs].mean(0)
        uvs[vs] = c + (uvs[vs] - c) * sc_
    at2 = xatlas.Atlas()
    at2.add_uv_mesh(uvs.astype(np.float32), ind.astype(np.uint32))
    po = xatlas.PackOptions()
    po.padding = padding
    po.resolution = TEX
    po.bruteForce = True
    po.bilinear = True
    po.rotate_charts = True
    at2.generate(xatlas.ChartOptions(), po)
    vm2, ind2, uv2 = at2[0]
    uv = uv2[ind2].copy()
    e3 = np.linalg.norm(V[Fi].max(1) - V[Fi].min(1), axis=1)
    ext = (uv.max(1) - uv.min(1)).max(1)
    ratio = ext / np.maximum(e3, 1e-9)
    bad = ratio > np.median(ratio) * 8
    uv[bad] = uv[bad][:, :1]
    me.uv_layers.active.data.foreach_set("uv", uv.astype(np.float32).ravel())
    me.update()
    a3 = np.linalg.norm(np.cross(V[Fi[:, 1]] - V[Fi[:, 0]], V[Fi[:, 2]] - V[Fi[:, 0]]), axis=1) / 2
    a2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1]) - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
    def dens(m):
        return math.sqrt(a2[m].sum() / max(a3[m].sum(), 1e-9)) * TEX
    face = (part == 0) & (cen[:, 2] > NECK_Z) & (cen[:, 1] < HEAD_C[1])
    log("uv: %d charts, coverage %.3f, %d slivers zeroed; px/m face %.0f head %.0f body %.0f props %s" % (
        at.chart_count, a2.sum(), bad.sum(), dens(face), dens((part == 0) & (cen[:, 2] > NECK_Z)),
        dens((part == 0) & (cen[:, 2] < NECK_Z)), {NAMES[k]: round(dens(part == k)) for k in PIECES if k > 0}))


xatlas_unwrap(joined, uv_boost)
log("uv done; tris", len(joined.data.polygons))

# ------------------------------------------------------------------------------------------------ bakes
from scipy.ndimage import binary_dilation
sc = bpy.context.scene
sc.world = bpy.data.worlds.new("BakeWorld")
sc.world.light_settings.distance = 0.16
MARGIN = 10
maps = {k: np.zeros((TEX, TEX, 4), np.float32) for k in ("base", "rm", "NORMAL", "AO")}
covered = np.zeros((TEX, TEX), bool)
joined.hide_render = True
for k in PIECES:
    tmp = bk._group_object(joined, {k}, "BakeGroup_%d" % k)
    if len(tmp.data.polygons) == 0:
        bpy.data.objects.remove(tmp)
        continue
    m = bk.uv_mask(tmp, TEX)
    md = binary_dilation(m, iterations=MARGIN) & ~covered
    for kk, o in HI.items():
        o.hide_render = kk != k
    for key, kind in (("base", "EMIT"), ("rm", "EMIT"), ("NORMAL", "NORMAL"), ("AO", "AO")):
        if kind == "EMIT":
            emit_source(key)
        img = bk.new_image("g_%s_%d" % (key, k), TEX, non_color=True)
        bk.bake(tmp, [HI[k]], img, kind, samples=(32 if kind == "AO" else 4), margin=MARGIN, extrusion=0.015, maxdist=0.045)
        px = bk.pixels(img)
        maps[key][md] = px[md]
        maps[key][m] = px[m]
        bpy.data.images.remove(img)
        log("baked", key, NAMES[k])
    covered |= m
    bpy.data.objects.remove(tmp)
joined.hide_render = False
empty = ~binary_dilation(covered, iterations=MARGIN)
maps["NORMAL"][empty] = (0.5, 0.5, 1.0, 1.0)
maps["AO"][empty] = 1.0
maps["rm"][empty] = (1.0, 0.6, 0.0, 1.0)
AO_K = float(CFG.get("ao_k", 0.35))
ao = bk.blur(maps["AO"][..., :3], 1.0)[..., :1]
alb = maps["base"][..., :3] * (1 - AO_K + AO_K * ao)
pa = bk.save_png(alb, os.path.join(OUT, "hero_albedo.png"), srgb_encode=True)
pn = bk.save_png(maps["NORMAL"][..., :3], os.path.join(OUT, "hero_normal.png"))
orm = np.concatenate([ao, maps["rm"][..., 1:2], maps["rm"][..., 2:3]], axis=2)
po = bk.save_png(orm, os.path.join(OUT, "hero_orm.png"))
log("maps saved")

for o in list(HI.values()):
    bpy.data.objects.remove(o)
mat = bk.game_material("HeroMat", pa, pn, po)
joined.data.materials.clear()
joined.data.materials.append(mat)
for im in bpy.data.images:
    if im.filepath:
        im.filepath = "//" + os.path.basename(im.filepath)
json.dump(dict(names=NAMES, targets={NAMES[k]: v for k, v in TARGETS.items()}, xf=XF), open(os.path.join(OUT, "low.json"), "w"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "low.blend"))
log("saved low.blend", len(joined.data.polygons), "tris")

# ------------------------------------------------------------------------------------------------ quick look
sc.render.engine = "CYCLES"
sc.cycles.samples = 16
sc.cycles.use_denoising = True
sc.render.resolution_x = sc.render.resolution_y = 256 if TEST else 640
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.77, 0.8, 1)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
sc.collection.objects.link(sun)
os.makedirs(os.path.join(OUT, "look"), exist_ok=True)
Hc = HEAD_C
zc = float(np.mean([v.co.z for v in joined.data.vertices]))
for nm, tgt, az, el, ortho in (("front", (0, 0, 1.1), 0, 5, 2.6), ("q", (0, 0, 1.1), 40, 15, 2.6), ("back", (0, 0, 1.1), 180, 5, 2.6),
                               ("face", (Hc[0], Hc[1] - 0.1, Hc[2]), 0, 3, 0.6), ("face_q", (Hc[0], Hc[1] - 0.1, Hc[2]), -35, 5, 0.6)):
    if TEST and nm not in ("face", "face_q"):
        continue
    t = Vector(tgt)
    a, e = math.radians(az), math.radians(el)
    cam = bpy.data.objects.new("C_" + nm, bpy.data.cameras.new("C_" + nm))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = ortho
    cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 5
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, "look", nm + ".png")
    bpy.ops.render.render(write_still=True)
log("done")
