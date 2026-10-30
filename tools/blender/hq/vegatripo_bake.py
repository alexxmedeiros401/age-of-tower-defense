"""Commander Vega from the Tripo model: high-poly pieces -> decimated game mesh with a fresh UV atlas and baked maps.

    python3 vegatripo_bake.py -- --in vegatripo_in --out OUT [--tex 2048] [--body 21300] [--gun 2200] [--switch 1000]

Inputs (vegatripo_in/): vega_tripo.glb (the Tripo model: one 1.9M-triangle mesh, base colour / roughness-metal / normal
maps), labels.npz (per Tripo face: 0 body, 1 the holstered pistol, 2 the killswitch, 3 dropped: the pistol's cable and
slivers; found by min-cuts along the creases where the props were fused to the coat), patches.pkl (fills for the holes
those cuts leave: harmonic membranes with colours interpolated from the hole's rim).
The Tripo mesh is scaled to the old Vega's height (S0, feet at DZ) and kept in its own A-pose: rigging and the rest pose
are done afterwards (vegatripo_rig.py). Each piece is decimated on its own (the body with a vertex-group bias that keeps
the head denser), joined with a `part` face layer (0 body, 1 pistol, 2 switch), unwrapped (lowpoly.unwrap, the face
boosted) and baked piece by piece from its own high-poly: base colour and roughness-metal as emission, the normal map,
ambient occlusion. Writes OUT/low.blend (mesh VegaLow, Tripo pose) and OUT/hero_{albedo,normal,orm}.png.
"""
import sys, os, time, json, struct, pickle, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import numpy as np
import bpy, bmesh
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d

IN = arg("--in", "vegatripo_in")
OUT = arg("--out", "out")
TEX = int(arg("--tex", "2048"))
TARGETS = {0: int(arg("--body", "21300")), 1: int(arg("--gun", "2200")), 2: int(arg("--switch", "1000"))}
HEAD_SHARE = float(arg("--head-share", "0.25"))      # the share of the body's triangles above the neck
TEST = "--test" in ARGS                               # (a quick local check of the code path: the head only, small maps)
S0, DZ = 2.057, -0.031                               # Tripo -> the old Vega's height, feet on the ground
os.makedirs(OUT, exist_ok=True)
T0 = time.time()


def log(*a):
    print("[vt] %5.0fs" % (time.time() - T0), *a, flush=True)


# ------------------------------------------------------------------------------------------------ the Tripo model
def read_glb(path):
    b = open(path, "rb").read()
    off, chunks = 12, []
    while off < len(b):
        cl, ct = struct.unpack("<II", b[off:off + 8])
        chunks.append(b[off + 8:off + 8 + cl])
        off += 8 + cl
    js, bin_ = json.loads(chunks[0]), chunks[1]
    CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}
    NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}
    def acc(i):
        a = js["accessors"][i]
        bv = js["bufferViews"][a["bufferView"]]
        o = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        arr = np.frombuffer(bin_, CT[a["componentType"]], a["count"] * NC[a["type"]], o)
        return arr.reshape(a["count"], -1)
    prim = js["meshes"][0]["primitives"][0]
    P = acc(prim["attributes"]["POSITION"]).astype(np.float64)
    UV = acc(prim["attributes"]["TEXCOORD_0"]).astype(np.float32)
    I = acc(prim["indices"]).reshape(-1, 3).astype(np.int64)
    for i, nm in enumerate(("tex_base.jpg", "tex_rm.jpg", "tex_normal.png")):
        bv = js["bufferViews"][js["images"][i]["bufferView"]]
        o = bv.get("byteOffset", 0)
        open(os.path.join(OUT, nm), "wb").write(bin_[o:o + bv["byteLength"]])
    return P, UV, I


P, UV, I = read_glb(os.path.join(IN, "vega_tripo.glb"))
PB = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1)                  # glTF Y-up -> Blender Z-up (facing -Y)
q = np.round(PB.astype(np.float32).astype(np.float64) * 1e5).astype(np.int64)
_, inv = np.unique(q, axis=0, return_inverse=True)
inv = inv.ravel()
Pw = np.zeros((inv.max() + 1, 3))
Pw[inv] = PB.astype(np.float32)
F = inv[I]
lab = np.load(os.path.join(IN, "labels.npz"))["lab"]
assert len(lab) == len(F), (len(lab), len(F))
patches = pickle.load(open(os.path.join(IN, "patches.pkl"), "rb"))
if TEST:
    lab = lab.copy()
    lab[(lab == 0) & (Pw[F].mean(1)[:, 2] < 0.8)] = 3
    patches["body"] = []
    TARGETS[0] = 3000
log("tripo", len(P), "verts", len(F), "faces; labels", np.bincount(lab).tolist())


def to_game(X):
    X = X * S0
    X[:, 2] += DZ
    return X


def srgb_to_lin(a):
    return np.where(a <= 0.04045, a / 12.92, np.power((a + 0.055) / 1.055, 2.4))


# ------------------------------------------------------------------------------------------------ materials
def tripo_material():
    m = bpy.data.materials.new("TripoMat")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    def tex(f, cs):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(os.path.join(OUT, f))
        n.image.colorspace_settings.name = cs
        return n
    tb = tex("tex_base.jpg", "sRGB")
    trm = tex("tex_rm.jpg", "Non-Color")
    tn = tex("tex_normal.png", "Non-Color")
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
    return m


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
    return m


def emit_source(which):
    """Point both materials' emission at the base colour ('base') or the roughness-metal map ('rm')."""
    for mname, node in (("TripoMat", {"base": "BASE", "rm": "RM"}), ("PatchMat", {"base": "PCOL", "rm": "PRM"})):
        nt = bpy.data.materials[mname].node_tree
        b = nt.nodes["Principled BSDF"]
        for l in list(b.inputs["Emission Color"].links):
            nt.links.remove(l)
        nt.links.new(nt.nodes[node[which]].outputs["Color"], b.inputs["Emission Color"])


# ------------------------------------------------------------------------------------------------ high-poly pieces
def hi_piece(L, key, name):
    Fm = F[lab == L]
    used = np.unique(Fm)
    remap = np.full(Pw.shape[0], -1)
    remap[used] = np.arange(len(used))
    V = [Pw[used]]
    Fs = [remap[Fm]]
    corner_uv = [UV[I[lab == L]].reshape(-1, 2)]
    mat = [np.zeros(len(Fm), np.int32)]
    nv = len(used)
    pcol = np.zeros((nv, 3))
    prm = np.zeros((nv, 3))
    pcols, prms = [pcol], [prm]
    for (Lr, Pin, tris, col, rmv) in patches[key]:
        n = len(Lr)
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
    c = np.concatenate(pcols)
    r = np.concatenate(prms)
    for nm, arr in (("pcol", srgb_to_lin(np.clip(c, 0, 1))), ("prm", np.clip(r, 0, 1))):
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
HI = {0: hi_piece(0, "body", "Body_hi"), 1: hi_piece(1, "gun", "Pistol_hi"), 2: hi_piece(2, "sw", "Switch_hi")}


# ------------------------------------------------------------------------------------------------ decimation
def head_bias(V, wh):
    """Decimation weights (lower = kept denser): the head (above the collar) and most of all the face."""
    w = np.ones(len(V))
    head = np.clip((V[:, 2] - 1.52) / 0.07, 0, 1)
    face = head * np.clip((-V[:, 1] + 0.02) / 0.1, 0, 1)
    w -= head * (1 - wh) * 0.7 + face * (1 - wh) * 0.3
    hands = np.clip((np.abs(V[:, 0]) - 0.64) / 0.05, 0, 1) * np.clip((1.02 - V[:, 2]) / 0.08, 0, 1)
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


def region_counts(ob):
    C = np.array([p.center for p in ob.data.polygons])
    return dict(total=len(C), head=int((C[:, 2] > 1.55).sum()), face=int(((C[:, 2] > 1.55) & (C[:, 1] < -0.04)).sum()),
                hands=int(((np.abs(C[:, 0]) > 0.66) & (C[:, 2] < 0.98)).sum()), boots=int((C[:, 2] < 0.3).sum()))


LOW = {}
lo_w, hi_w, wh = 0.0, 1.0, float(arg("--head-w", "0.969"))     # (0.969 gave a 0.26 share on the first build)
for it in range(5):                                   # search the head weight for the head's share of the triangles
    ob = decimate(HI[0], TARGETS[0], "Body_low", lambda V: head_bias(V, wh))
    rc = region_counts(ob)
    share = rc["head"] / rc["total"]
    log("decimate body: head weight %.3f ->" % wh, rc, "head share %.3f" % share)
    if abs(share - HEAD_SHARE) < 0.02 or it == 4:
        break
    bpy.data.objects.remove(ob)
    if share < HEAD_SHARE:
        hi_w = wh
    else:
        lo_w = wh
    wh = (lo_w + hi_w) / 2
LOW[0] = ob
LOW[1] = decimate(HI[1], TARGETS[1], "Pistol_low")
LOW[2] = decimate(HI[2], TARGETS[2], "Switch_low")
for k, o in LOW.items():
    a = o.data.attributes.new("part", "INT", "FACE")
    a.data.foreach_set("value", np.full(len(o.data.polygons), k, np.int32))
    o.data.materials.clear()
    log("low", o.name, len(o.data.polygons))

import lowpoly as lp
import bake as bk
joined = lp.join([LOW[0], LOW[1], LOW[2]], "VegaLow")
joined.data.validate(clean_customdata=False)
for l in list(joined.data.uv_layers):
    joined.data.uv_layers.remove(l)
joined.data.uv_layers.new(name="UVMap")


def uv_boost(c, part):
    """Texel density per region (relative): the face most, then the rest of the head; the boots least."""
    if part == 0 and c[2] > 1.52:
        return 2.2 if c[1] < 0.0 else 1.5
    if part == 0 and abs(c[0]) > 0.64 and c[2] < 1.0:
        return 1.15                                 # the fists
    if part in (1, 2):
        return 1.2
    if part == 0 and c[2] < 0.3:
        return 0.65                                 # the boots
    return 1.0


def xatlas_unwrap(ob, boost, padding=4):
    """Charts and their parametrisation by xatlas on the real shape (no collapsed islands, unlike smoothing first: the
    first build's coat back came out squashed to a sliver); every chart scaled by its region's boost, then packed again
    by xatlas (brute force) into the square."""
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
    # (a few sliver faces come back spread across the atlas: give them no area)
    e3 = np.linalg.norm(V[Fi].max(1) - V[Fi].min(1), axis=1)
    ext = (uv.max(1) - uv.min(1)).max(1)
    ratio = ext / np.maximum(e3, 1e-9)
    bad = ratio > np.median(ratio) * 8
    uv[bad] = uv[bad][:, :1]
    uvl = me.uv_layers.active
    uvl.data.foreach_set("uv", uv.astype(np.float32).ravel())
    me.update()
    a3 = np.linalg.norm(np.cross(V[Fi[:, 1]] - V[Fi[:, 0]], V[Fi[:, 2]] - V[Fi[:, 0]]), axis=1) / 2
    a2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1]) - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
    def dens(m):
        return math.sqrt(a2[m].sum() / max(a3[m].sum(), 1e-9)) * TEX
    face = (part == 0) & (cen[:, 2] > 1.52) & (cen[:, 1] < -0.02)
    log("uv: %d charts, coverage %.3f, %d slivers zeroed; px/m face %.0f head %.0f body %.0f boots %.0f pistol %.0f switch %.0f"
        % (at.chart_count, a2.sum(), bad.sum(), dens(face), dens((part == 0) & (cen[:, 2] > 1.52)),
           dens((part == 0) & (cen[:, 2] > 0.35) & (cen[:, 2] < 1.5)), dens((part == 0) & (cen[:, 2] < 0.3)), dens(part == 1), dens(part == 2)))


xatlas_unwrap(joined, uv_boost)
log("uv done; tris", len(joined.data.polygons))

# ------------------------------------------------------------------------------------------------ bakes
groups = [([0], [HI[0]]), ([1], [HI[1]]), ([2], [HI[2]])]
from scipy.ndimage import binary_dilation
sc = bpy.context.scene
sc.world = bpy.data.worlds.new("BakeWorld")
sc.world.light_settings.distance = 0.16
MARGIN = 10
maps = {k: np.zeros((TEX, TEX, 4), np.float32) for k in ("base", "rm", "NORMAL", "AO")}
covered = np.zeros((TEX, TEX), bool)
joined.hide_render = True
for gi, (pids, his) in enumerate(groups):
    tmp = bk._group_object(joined, set(pids), "BakeGroup_%d" % gi)
    m = bk.uv_mask(tmp, TEX)
    md = binary_dilation(m, iterations=MARGIN) & ~covered
    for o in HI.values():
        o.hide_render = o not in his
    for key, kind in (("base", "EMIT"), ("rm", "EMIT"), ("NORMAL", "NORMAL"), ("AO", "AO")):
        if kind == "EMIT":
            emit_source(key)
        img = bk.new_image("g_%s_%d" % (key, gi), TEX, non_color=True)
        bk.bake(tmp, his, img, kind, samples=(32 if kind == "AO" else 4), margin=MARGIN, extrusion=0.015, maxdist=0.045)
        px = bk.pixels(img)
        maps[key][md] = px[md]
        maps[key][m] = px[m]
        bpy.data.images.remove(img)
        log("baked", key, "group", gi)
    covered |= m
    bpy.data.objects.remove(tmp)
joined.hide_render = False
empty = ~binary_dilation(covered, iterations=MARGIN)
maps["NORMAL"][empty] = (0.5, 0.5, 1.0, 1.0)
maps["AO"][empty] = 1.0
maps["rm"][empty] = (1.0, 0.6, 0.0, 1.0)

AO_K = 0.35
ao = bk.blur(maps["AO"][..., :3], 1.0)[..., :1]
alb = maps["base"][..., :3] * (1 - AO_K + AO_K * ao)
pa = bk.save_png(alb, os.path.join(OUT, "hero_albedo.png"), srgb_encode=True)
pn = bk.save_png(maps["NORMAL"][..., :3], os.path.join(OUT, "hero_normal.png"))
orm = np.concatenate([ao, maps["rm"][..., 1:2], maps["rm"][..., 2:3]], axis=2)
po = bk.save_png(orm, os.path.join(OUT, "hero_orm.png"))
log("maps saved")

for o in list(HI.values()):
    bpy.data.objects.remove(o)
mat = bk.game_material("VegaMat", pa, pn, po)
joined.data.materials.clear()
joined.data.materials.append(mat)
for im in bpy.data.images:
    if im.filepath:
        im.filepath = "//" + os.path.basename(im.filepath)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "low.blend"))
log("saved low.blend", len(joined.data.polygons), "tris")

# ------------------------------------------------------------------------------------------------ quick look
sc.render.engine = "CYCLES"
sc.cycles.samples = 24
sc.cycles.use_denoising = True
sc.render.resolution_x = sc.render.resolution_y = 640
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
for nm, tgt, az, el, ortho in (("front", (0, 0, 1.0), 0, 5, 2.3), ("q", (0, 0, 1.0), 40, 15, 2.3), ("back", (0, 0, 1.0), 180, 5, 2.3),
                               ("face", (0, -0.1, 1.72), 0, 3, 0.55), ("face_q", (0, -0.1, 1.72), -35, 5, 0.55)):
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
