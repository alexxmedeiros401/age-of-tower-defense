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


# -------------------------------------------------------------------------------------------- the right pauldron
PAD_UPPER, PAD_CLAV = "upperarm.R", "clavicle.R"
PAD_SCALE, PAD_DROP = 0.86, 0.015
PAD_CLAV_SHARE, PAD_SEAM_RINGS = 0.35, 3


def pauldron_weights(lm, P, body, W4, gn, posed, tr, ea, eb, ldir):
    """The salvaged white pauldron (dome, lames, its chevron and rivets) rides the right upper arm rigidly: found by its
    baked colour (white plates, the amber chevron, flooded over the light-grey rivets and rims, then two rings more to
    take its dark underside), weighted to the upper arm with a share of the clavicle at its inner edge (35% at the
    shoulder joint, none 0.2 m down the arm), and only the seam into the coat smoothed. The transferred weights left it
    on the chest and clavicle: it rose to his ear whenever the arm hung down (the old Vega's pauldron did the same)."""
    from PIL import Image
    import scipy.sparse as sp
    nv = len(P)
    uv = np.zeros(len(lm.loops) * 2)
    lm.uv_layers.active.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    lv = np.zeros(len(lm.loops), np.int64)
    lm.loops.foreach_get("vertex_index", lv)
    alb = np.asarray(Image.open(os.path.join(ldir, "hero_albedo.png")).convert("RGB")).astype(float) / 255
    S = alb.shape[0]
    c = alb[np.clip(((1 - uv[:, 1]) * S).astype(int), 0, S - 1), np.clip((uv[:, 0] * S).astype(int), 0, S - 1)]
    col = np.zeros((nv, 3))
    cnt = np.zeros(nv)
    np.add.at(col, lv, c)
    np.add.at(cnt, lv, 1)
    col = (col / np.maximum(cnt, 1)[:, None])[body]
    Pb = P[body]
    lum = col.mean(1)
    sat = col.max(1) - col.min(1)
    nb = len(body)
    A = sp.coo_matrix((np.ones(len(ea)), (ea, eb)), shape=(nb, nb))
    A = (A + A.T).tocsr()
    box = (Pb[:, 0] < -0.25) & (Pb[:, 2] > 1.1)
    m = box & (lum > 0.5) & (sat < 0.15)
    ok = box & ((lum > 0.33) | ((col[:, 0] > 0.55) & (col[:, 2] < 0.35)))
    for _ in range(40):
        m2 = m | ((A @ m.astype(float) > 0) & ok)
        if (m2 == m).all():
            break
        m = m2
    # rivets and rim bits the flood missed (light grey, within 2.5 cm of the plate)
    from scipy.spatial import cKDTree
    dd, _ = cKDTree(Pb[m]).query(Pb, k=1)
    stray = box & ~m & (dd < 0.025) & (lum > 0.3)
    m = m | stray
    for _ in range(40):                        # (and whatever hangs off them only through the pad)
        m2 = m | ((A @ m.astype(float) > 0) & ok)
        if (m2 == m).all():
            break
        m = m2
    # small islands of non-pad vertices in the shoulder box (rivets ringed by plate): the pad's too
    from scipy.sparse.csgraph import connected_components
    rest_ = np.nonzero(box & ~m)[0]
    ri = np.full(nb, -1)
    ri[rest_] = np.arange(len(rest_))
    sel = (ri[ea] >= 0) & (ri[eb] >= 0)
    nc, cl = connected_components(sp.coo_matrix((np.ones(sel.sum()), (ri[ea[sel]], ri[eb[sel]])), shape=(len(rest_), len(rest_))), directed=False)
    sizes = np.bincount(cl, minlength=nc)
    small = rest_[sizes[cl] < 40]
    m[small] = True
    for _ in range(2):                          # grey rivets on the rim (darker than the plate, lighter than the coat)
        m = m | ((A @ m.astype(float) > 0) & box & (lum > 0.27))
    log("pauldron: %d stray rivet/rim verts added, %d in small islands" % (stray.sum(), len(small)))
    # what lies under the shell (the coat's shoulder: seen from the shoulder joint, behind a plate vertex in the same
    # direction) moves and bends with it, so the two never cross; the seam to the coat is then outside the plate's rim
    h = posed[PAD_UPPER][:3, 3] + tr
    rv = Pb - h
    rr = np.linalg.norm(rv, axis=1)
    ud = rv / np.maximum(rr, 1e-9)[:, None]
    tree = cKDTree(ud[m])
    cand = box & ~m & (rr < 0.32)
    ang, j = tree.query(ud[cand], k=6)
    rp = rr[m][j]
    cov = ((ang < 0.10) & (rp > rr[cand][:, None] - 0.004)).any(1)
    under = np.zeros(nb, bool)
    under[np.nonzero(cand)[0][cov]] = True
    m = m | under
    mg = m
    log("pauldron: %d verts under the shell ride with it" % under.sum())
    # along the (fitted) upper arm from the shoulder joint
    h = posed[PAD_UPPER][:3, 3] + tr
    d = posed[PAD_UPPER][:3, 1]
    t = (Pb - h) @ d
    k = np.clip(t / 0.2, 0, 1)
    clav = PAD_CLAV_SHARE * (1 - k * k * (3 - 2 * k))
    iu, ic = gn.index(PAD_UPPER), gn.index(PAD_CLAV)
    W = W4.copy()
    W[m] = 0
    W[m, iu] = 1 - clav[m]
    W[m, ic] = clav[m]
    # smooth the seam: three rings outside the pad, the pad itself held
    band = m.copy()
    for _ in range(PAD_SEAM_RINGS):
        band = band | (A @ band.astype(float) > 0)
    band &= ~m
    deg = np.asarray(A.sum(1)).ravel()
    for _ in range(6):
        Wn = (A @ W) / np.maximum(deg, 1)[:, None]
        W[band] = 0.5 * W[band] + 0.5 * Wn[band]
    keep = np.argsort(-W, axis=1)[:, :4]
    W4n = np.zeros_like(W)
    rows = np.arange(nb)[:, None]
    W4n[rows, keep] = W[rows, keep]
    W4n[W4n < 0.01] = 0
    W4n /= W4n.sum(1, keepdims=True)
    log("pauldron: %d verts rigid to %s (clavicle share up to %.2f), %d seam verts smoothed" % (m.sum(), PAD_UPPER, PAD_CLAV_SHARE, band.sum()))
    # seat it lower: shrink it toward the shoulder joint and drop it a little (it stood 24 cm above the joint, its top at
    # his ear, and the Ability's shrug and crouch put it beside his face); the seam band follows by its ring distance
    f = mg.astype(float)
    ring = mg.copy()
    for k in range(1, 4):
        nxt = ring | (A @ ring.astype(float) > 0)
        f[nxt & ~ring] = 1.0 - k / 4.0
        ring = nxt
    Pn = Pb + (f[:, None] * ((h + (Pb - h) * PAD_SCALE) - Pb)) - f[:, None] * np.array((0.0, 0.0, PAD_DROP))
    P[body] = Pn
    log("pauldron: scaled %.2f about the shoulder joint, dropped %.3f m" % (PAD_SCALE, PAD_DROP))
    return W4n


# -------------------------------------------------------------------------------------------- the pistol's grip
GRIP_TOP = 0.905         # (rest frame of the gun, rig space) where the grip meets the frame ...
GRIP_END = 0.835         # ... and where it now ends: the fist's bottom (measured over Idle, Combat, Attack, Cheer: 0.825-0.83)
GRIP_TILT = 14.0         # degrees: the foot swung back toward his wrist, a handgun's rake


def shorten_grip(X):
    """The Tripo grip hung 12 cm out of the bottom of the fist: squash it along its length below the frame so it ends
    at the fist's bottom, and rake it back. Only the grip (below GRIP_TOP) moves; the frame, barrel and muzzle stay."""
    X = X.copy()
    g = X[:, 2] < GRIP_TOP
    lo = X[g, 2].min()
    k = (GRIP_TOP - GRIP_END) / (GRIP_TOP - lo)
    depth = GRIP_TOP - X[g, 2]
    X[g, 2] = GRIP_TOP - depth * k
    hy = np.median(X[g & (X[:, 2] > GRIP_TOP - 0.02), 1]) if (g & (X[:, 2] > GRIP_TOP - 0.02)).any() else X[g, 1].mean()
    # slimmer front to back (it was 10 cm deep, more than the fist), fading in below the frame
    yc = X[g, 1].mean()
    th = np.clip(depth * k / 0.025, 0, 1)
    X[g, 1] = yc + (X[g, 1] - yc) * (1 - 0.25 * th)
    a = math.radians(GRIP_TILT) * np.clip(depth * k / 0.03, 0, 1)
    dy, dz = X[g, 1] - hy, X[g, 2] - GRIP_TOP
    X[g, 1] = hy + dy * np.cos(a) - dz * np.sin(a)          # (the foot, dz < 0, moves to +y: back toward the wrist)
    X[g, 2] = GRIP_TOP + dy * np.sin(a) + dz * np.cos(a)
    log("grip: %d verts, %.3f m long -> %.3f m, raked back %.0f deg" % (g.sum(), GRIP_TOP - lo, GRIP_TOP - GRIP_END, GRIP_TILT))
    return X


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
    W4 = pauldron_weights(lm, P, body, W4, gn, posed, tr, ea, eb, os.path.dirname(os.path.abspath(LOW)))

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
    Prest[gun] = shorten_grip(gun_xf(P[gun]))
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
