"""Commander Vega from the Tripo model, step 2: rig the baked low-poly onto the old Vega's skeleton and export the game file.

    python3 vegatripo_rig.py -- --old vega_hq.blend --low low.blend --fit pose_fit.json --out OUT

`--old` is the shipped Vega build (vega_final5's vega_hq.blend: base, glows, grass, Yaw, CavemanRig and the five clips).
`--low` is vegatripo_bake.py's output (VegaLow: the Tripo body, pistol and killswitch decimated and baked, still in the
Tripo model's own A-pose; the `part` face layer says which piece a face belongs to).
`--fit` is the pose of the old rig that matches the Tripo model (fit by least squares: the old Vega mesh, skinned, posed
onto the Tripo surface; limb twists left out), plus a small global offset.

The rig's rest pose is not touched (the clips depend on it). Instead the body is skinned in the Tripo pose (weights
transferred from the old Vega mesh posed with the fit: nearest surface with agreeing normals, interpolated over the
triangle, smoothed over the mesh), then brought into the rig's rest pose by inverting that skinning, and bound to
CavemanRig with the same weights. The pistol and the killswitch are moved rigidly onto their bones' rest frames (the
grip in the fist, the barrel along the old one, the switch's grip and button where the old ones were) and weighted 100%
to `pistol` / `switch`. New GlowChamber (the muzzle's core) and GlowButton (the thumb button, on `button`) replace the
old ones. Everything else in the scene is kept as it was; the maps replace hero_albedo/normal/orm in VegaMat.
Writes OUT/vega.glb and OUT/vega_hq.blend.
"""
import sys, os, json, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d

OLD, LOW, FIT, OUT = arg("--old"), arg("--low"), arg("--fit"), arg("--out", "out")
os.makedirs(OUT, exist_ok=True)
S0, DZ = 2.057, -0.031                     # (vegatripo_bake.py: Tripo units -> game units)


def log(*a):
    print("[rig]", *a, flush=True)


def tg(p):
    """Tripo-model point (Blender axes, Tripo units) -> game units (Tripo pose)."""
    p = np.array(p, float) * S0
    p[2] += DZ
    return p


def nrm(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


# -------------------------------------------------------------------------------------------- the props' landmarks
# (measured on the Tripo model's cut-out pieces, Tripo units)
GUN_MUZZLE = (-0.1619, -0.298, 0.5221)     # the muzzle face's middle
GUN_BARREL = nrm((0.0, -0.9972, 0.0747))   # the barrel's axis (it rises 4.3 degrees toward the muzzle)
GUN_GRIP = (-0.132, -0.040, 0.440)         # where the fist closes: the grip's middle just under the frame
GUN_SCALE = 0.85                           # (x S0: the old pistol's size, so the muzzle stays where it was)
GUN_CORE = ((-0.1631, -0.2915, 0.5226), 0.0125)    # the glowing core in the bore (centre, radius)
SW_GRIP = (0.1459, 0.1569, 0.40)           # the killswitch: the ribbed grip's middle on the rod's axis ...
SW_TOP = (0.1378, 0.1316, 0.538)           # ... and the top of its amber thumb button
SW_DOME = (0.027, 0.015)                   # the button's dome (radius, height)


def main():
    bpy.ops.wm.open_mainfile(filepath=OLD)
    for im in bpy.data.images:            # the base's maps: the build's blend points at the runner's paths
        if im.source == "FILE" and not im.packed_file and not im.name.startswith("hero_"):
            if not os.path.exists(bpy.path.abspath(im.filepath)):
                im.filepath = os.path.join(os.path.dirname(os.path.abspath(OLD)), os.path.basename(im.filepath))
            im.reload()
            if im.has_data or os.path.exists(bpy.path.abspath(im.filepath)):
                im.pack()
            log("image", im.name, tuple(im.size), "packed" if im.packed_file else "MISSING")
    sc = bpy.context.scene
    arm = bpy.data.objects["CavemanRig"]
    old = bpy.data.objects["Vega"]
    bones = {b.name: b for b in arm.data.bones}
    rest = {n: np.array(b.matrix_local) for n, b in bones.items()}

    # ---- the old mesh (rest pose, rig space) and its weights
    me = old.data
    V0 = np.array([v.co for v in me.vertices])
    gn = [g.name for g in old.vertex_groups]
    W0 = np.zeros((len(V0), len(gn)))
    for v in me.vertices:
        for g in v.groups:
            W0[v.index, g.group] = g.weight
    part0 = np.zeros(len(me.polygons), np.int32)
    me.attributes["part"].data.foreach_get("value", part0)
    me.calc_loop_triangles()
    tri0 = np.array([t.vertices[:] for t in me.loop_triangles])
    tp0 = np.array([t.polygon_index for t in me.loop_triangles])
    tri0 = tri0[~np.isin(part0[tp0], [14, 15, 16, 17])]          # the old pistol / switch are not body
    body_groups = [i for i, n in enumerate(gn) if n not in ("pistol", "switch")]

    # ---- the fitted pose: skinning matrices of the old rig posed onto the Tripo model
    fit = json.load(open(FIT))
    parent = {n: (b.parent.name if b.parent else None) for n, b in bones.items()}
    order = []
    def add(n):
        if n not in order:
            if parent[n]:
                add(parent[n])
            order.append(n)
    for n in bones:
        add(n)
    posed = {}
    for n in order:
        R = np.eye(4)
        if n in fit["rotvec"]:
            R[:3, :3] = Rot.from_rotvec(fit["rotvec"][n]).as_matrix()
        p = parent[n]
        posed[n] = rest[n] @ R if p is None else posed[p] @ np.linalg.inv(rest[p]) @ rest[n] @ R
    SK = {n: posed[n] @ np.linalg.inv(rest[n]) for n in order}
    tr = np.array(fit["translation"])

    def blend(W, names):
        M = np.zeros((len(W), 4, 4))
        for j, n in enumerate(names):
            w = W[:, j]
            if (w > 0).any():
                M += w[:, None, None] * SK[n][None]
        return M

    Vh = np.c_[V0, np.ones(len(V0))]
    Vp = np.einsum("nij,nj->ni", blend(W0, gn), Vh)[:, :3] + tr          # the old mesh in the Tripo pose

    # ---- the new low-poly (Tripo pose)
    with bpy.data.libraries.load(LOW) as (src, dst):
        dst.objects = ["VegaLow"]
    low = dst.objects[0]
    lm = low.data
    nv = len(lm.vertices)
    P = np.zeros(nv * 3)
    lm.vertices.foreach_get("co", P)
    P = P.reshape(-1, 3)
    fpart = np.zeros(len(lm.polygons), np.int32)
    lm.attributes["part"].data.foreach_get("value", fpart)
    vpart = np.zeros(nv, np.int32)
    for p in lm.polygons:
        vpart[list(p.vertices)] = fpart[p.index]
    log("low", nv, "verts", len(lm.polygons), "faces; parts", np.bincount(fpart).tolist())
    # vertex normals (area weighted) and adjacency
    lm.calc_loop_triangles()
    lt = np.array([t.vertices[:] for t in lm.loop_triangles])
    fn = np.cross(P[lt[:, 1]] - P[lt[:, 0]], P[lt[:, 2]] - P[lt[:, 0]])
    VN = np.zeros_like(P)
    for k in range(3):
        np.add.at(VN, lt[:, k], fn)
    VN /= np.maximum(np.linalg.norm(VN, axis=1), 1e-12)[:, None]

    # ---- weights for the body: nearest point of the posed old surface with an agreeing normal
    body = np.nonzero(vpart == 0)[0]
    A, B, C = Vp[tri0[:, 0]], Vp[tri0[:, 1]], Vp[tri0[:, 2]]
    tn = np.cross(B - A, C - A)
    area = np.linalg.norm(tn, axis=1) / 2
    tn /= np.maximum(2 * area, 1e-12)[:, None]
    rng = np.random.default_rng(1)
    ns = 600000
    ti = rng.choice(len(tri0), ns, p=area / area.sum())
    r1, r2 = rng.random(ns), rng.random(ns)
    flip = r1 + r2 > 1
    r1[flip], r2[flip] = 1 - r1[flip], 1 - r2[flip]
    bary = np.c_[1 - r1 - r2, r1, r2]
    S = A[ti] * bary[:, :1] + B[ti] * bary[:, 1:2] + C[ti] * bary[:, 2:]
    tree = cKDTree(S)
    d, nb = tree.query(P[body], k=24)
    ok = (tn[ti[nb]] * VN[body][:, None, :]).sum(2) > 0.25
    first = np.where(ok.any(1), ok.argmax(1), 0)
    pick = nb[np.arange(len(body)), first]
    log("weights: %.1f%% of body verts matched with agreeing normals, median dist %.4f" % (100 * ok.any(1).mean(), np.median(d[np.arange(len(body)), first])))
    WB = np.zeros((len(body), len(gn)))
    for k in range(3):
        WB += bary[pick][:, k:k + 1] * W0[tri0[ti[pick], k]]
    WB[:, [i for i in range(len(gn)) if i not in body_groups]] = 0
    # smooth over the low mesh (a few Laplacian passes), then at most four bones, normalised
    edges = set()
    for t in lt:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edges.add((min(a, b), max(a, b)))
    E = np.array(list(edges))
    bidx = np.full(nv, -1)
    bidx[body] = np.arange(len(body))
    E = E[(bidx[E[:, 0]] >= 0) & (bidx[E[:, 1]] >= 0)]
    ea, eb = bidx[E[:, 0]], bidx[E[:, 1]]
    deg = np.bincount(np.r_[ea, eb], minlength=len(body)).astype(float)
    for _ in range(4):
        acc = np.zeros_like(WB)
        np.add.at(acc, ea, WB[eb])
        np.add.at(acc, eb, WB[ea])
        WB = 0.5 * WB + 0.5 * acc / np.maximum(deg, 1)[:, None]
    head_i = gn.index("head")
    # the face and skull ride the head alone (no smearing of neck weights up the face)
    zb = P[body, 2]
    WB[zb > 1.74] = 0
    WB[zb > 1.74, head_i] = 1
    keep = np.argsort(-WB, axis=1)[:, :4]
    W4 = np.zeros_like(WB)
    rows = np.arange(len(body))[:, None]
    W4[rows, keep] = WB[rows, keep]
    W4[W4 < 0.01] = 0
    W4 /= W4.sum(1, keepdims=True)

    # ---- into the rest pose: invert the skinning of the fitted pose
    M = blend(W4, gn)
    Prest = P.copy()
    Prest[body] = np.einsum("nij,nj->ni", np.linalg.inv(M), np.c_[P[body] - tr, np.ones(len(body))])[:, :3]
    # the soles on the ground where the old ones were (the fit matched the boots' shafts, not their soles)
    dzfix = V0[:, 2].min() - Prest[body, 2].min()
    Prest[body, 2] += dzfix
    log("soles lifted by %.4f" % dzfix)
    log("body to rest: moved median %.4f max %.4f; feet min z %.4f" % (np.median(np.linalg.norm(Prest[body] - P[body], axis=1)),
                                                                      np.linalg.norm(Prest[body] - P[body], axis=1).max(), Prest[body, 2].min()))

    # ---- the props: rigid onto their bones' rest frames
    G0 = np.array(bones["pistol"].head_local)
    M0 = np.array(bones["pistol"].tail_local)
    Aax, Uax = np.array((0.0, -1.0, 0.0)), np.array((0.0, 0.0, 1.0))     # the old barrel's axis and up (vega.py GUN_A0/U0)
    b_t = GUN_BARREL
    u_t = nrm(np.cross(np.cross(b_t, (0, 0, 1)), b_t))
    Rt = np.stack([b_t, u_t, np.cross(b_t, u_t)], 1)
    Rr = np.stack([Aax, Uax, np.cross(Aax, Uax)], 1)
    Rg = Rr @ Rt.T
    sg = GUN_SCALE
    g_game = tg(GUN_GRIP)
    def gun_xf(X):
        return G0 + sg * (Rg @ (X - g_game).T).T
    gun = np.nonzero(vpart == 1)[0]
    Prest[gun] = gun_xf(P[gun])
    muz = gun_xf(tg(GUN_MUZZLE)[None])[0]
    log("pistol: grip at", G0.round(4), "muzzle (rest) at", muz.round(4), "old muzzle", M0.round(4), "offset", (muz - M0).round(4))

    Gs = np.array(bones["switch"].head_local)
    Ts = np.array(bones["switch"].tail_local)
    a_t = nrm(tg(SW_TOP) - tg(SW_GRIP))
    a_r = nrm(Ts - Gs)
    ss = np.linalg.norm(Ts - Gs) / np.linalg.norm(tg(SW_TOP) - tg(SW_GRIP))
    ax = np.cross(a_t, a_r)
    ang = math.atan2(np.linalg.norm(ax), a_t @ a_r)
    Rs = Rot.from_rotvec(nrm(ax) * ang).as_matrix() if np.linalg.norm(ax) > 1e-9 else np.eye(3)
    def sw_xf(X):
        return Gs + ss * (Rs @ (X - tg(SW_GRIP)).T).T
    sw = np.nonzero(vpart == 2)[0]
    Prest[sw] = sw_xf(P[sw])
    log("switch: scale %.3f (x S0), top at" % ss, sw_xf(tg(SW_TOP)[None])[0].round(4), "bone tail", Ts.round(4))

    lm.vertices.foreach_set("co", Prest.astype(np.float32).ravel())
    lm.update()

    # ---- replace the old Vega mesh's data, keep the object (name, parent, modifier)
    old_me = old.data
    old_me.name = "Vega_old"
    old.data = lm
    lm.name = "Vega"
    old.vertex_groups.clear()
    groups = {n: old.vertex_groups.new(name=n) for n in gn}
    for j in body_groups:
        w = W4[:, j]
        nz = np.nonzero(w > 0)[0]
        for i in nz:
            groups[gn[j]].add([int(body[i])], float(w[i]), "REPLACE")
    groups["pistol"].add(gun.tolist(), 1.0, "REPLACE")
    groups["switch"].add(sw.tolist(), 1.0, "REPLACE")
    bpy.data.meshes.remove(old_me)
    # the baked maps go into the old material's images (same names)
    mat = bpy.data.materials["VegaMat"]
    ldir = os.path.dirname(os.path.abspath(LOW))
    for nd in mat.node_tree.nodes:
        if nd.type == "TEX_IMAGE":
            nm = nd.image.name                     # hero_albedo.png ...
            nd.image.filepath = os.path.join(ldir, nm)
            nd.image.reload()
            nd.image.pack()
            log("image", nm, tuple(nd.image.size))
    lm.materials.clear()
    lm.materials.append(mat)
    for m in [m for m in bpy.data.materials if m.users == 0]:
        bpy.data.materials.remove(m)
    for im in [im for im in bpy.data.images if im.users == 0]:
        bpy.data.images.remove(im)

    # ---- the glows
    def rigid_glow(name, bm_fn, bone):
        ob = bpy.data.objects[name]
        gm = ob.data
        bm = bmesh.new()
        bm_fn(bm)
        me = bpy.data.meshes.new(name.replace("Glow", "") + "_new")
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        mats_ = list(gm.materials)
        old_name = gm.name
        ob.data = me
        for m_ in mats_:
            me.materials.append(m_)
        bpy.data.meshes.remove(gm)
        me.name = old_name                         # (the same mesh names in the GLB as before)
        ob.vertex_groups.clear()
        for n in gn + (["button"] if bone == "button" else []):
            if n not in [g.name for g in ob.vertex_groups]:
                ob.vertex_groups.new(name=n)
        ob.vertex_groups[bone].add(list(range(len(me.vertices))), 1.0, "REPLACE")
        log(name, len(me.polygons), "faces on", bone)

    core_c, core_r = GUN_CORE
    def chamber(bm):
        r = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=16, radius1=core_r * S0, radius2=core_r * S0, depth=0.012)
        # disc along the barrel, just in front of the core's face
        c = tg(core_c)
        Rz = Matrix(np.stack([np.cross(u_t, b_t), u_t, b_t], 1).tolist()).to_4x4()     # local z -> barrel axis
        bmesh.ops.transform(bm, matrix=Rz, verts=r["verts"])
        bmesh.ops.translate(bm, vec=Vector(c), verts=r["verts"])
        for v in bm.verts:
            v.co = Vector(gun_xf(np.array(v.co)[None])[0])
    rigid_glow("GlowChamber", chamber, "pistol")

    dr, dh = SW_DOME
    def button(bm):
        r = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0)
        top = tg(SW_TOP)
        a = a_t
        Ra = Rot.align_vectors([a], [[0, 0, 1]])[0].as_matrix()
        for v in r["verts"]:
            p = np.array(v.co) * np.array((dr * S0 * 1.04, dr * S0 * 1.04, dh * S0 * 1.1))
            p = top - a * dh * S0 * 0.95 + Ra @ p
            v.co = Vector(sw_xf(p[None])[0])
    rigid_glow("GlowButton", button, "button")

    # ---- save and export (build_game.py's export settings)
    for o in sc.objects:
        o.select_set(False)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "vega_hq.blend"))
    path = os.path.join(OUT, "vega.glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                              export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                              export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
    log("exported", path, os.path.getsize(path))
    tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == "MESH"}
    log("tris", tris)


main()
