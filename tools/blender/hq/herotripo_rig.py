"""Generic Tripo hero, step 7 (local, light): rig the baked low-poly onto the old hero's skeleton and export the game file.

    python3 herotripo_rig.py -- --hero ugo --low BAKE_OUT/low.blend --out OUT [--work PREP]

Reads the old scene (cfg "old": the <id>_hq.blend or the shipped GLB), the bake's low.blend (HeroLow: the Tripo body and
props decimated and baked, in the Tripo model's own pose, game units; `part` face layer: 0 body, k the k-th prop) and
the prep folder's old.npz / old.json / fit.json.

The rig's rest pose and the clips are not touched. The body is skinned in the fitted pose (weights transferred from the
old mesh posed with the fit: nearest surface point with an agreeing normal, interpolated over its triangle, smoothed
over the new mesh; the skull rides the head bone alone above cfg head_rigid_above), then brought into the rest pose by
inverting that skinning, and bound with the same weights. Armour pieces (cfg "armour") are re-weighted rigidly to the
bones they ride. Props are moved onto their bones' rest frames (cfg "place", see README.md) and weighted 100% to their
bone. The old mesh object keeps its name, parent and modifier (its data is replaced, mesh data name kept); the bake's
maps replace the material's hero_albedo / hero_normal / hero_orm images (same image names). Everything else in the old
scene is kept as it was. Writes OUT/<id>.glb (build_game.py's export settings) and OUT/<id>_hq.blend (maps packed).
"""
import sys, os, json, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
sys.path.insert(0, os.path.join(HQ, "herotripo_prep"))
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
import scipy.sparse as sp
import common as C

HID = C.arg("--hero")
CFG = C.load_cfg(HID)
WK = C.work_dir(HID)
LOW = C.arg("--low")
OUT = C.arg("--out", "out")
os.makedirs(OUT, exist_ok=True)
INFO = json.load(open(os.path.join(WK, "old.json")))
FIT = json.load(open(os.path.join(WK, "fit.json")))
XF0 = json.load(open(os.path.join(WK, "xf.json")))
XF = FIT["xf"]
REPORT = {}


def log(*a):
    print("[rig]", *a, flush=True)


def load_to_final(p):
    """A point read off look.py's grid (the load step's frame) -> the fitted game frame (Tripo pose)."""
    return C.to_game(C.from_game(np.atleast_2d(np.array(p, float)), XF0), XF)


def nrm(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def rot_between(a, b):
    a, b = nrm(a), nrm(b)
    ax = np.cross(a, b)
    s = np.linalg.norm(ax)
    if s < 1e-9:
        return np.eye(3) if a @ b > 0 else Rot.from_rotvec(nrm(np.cross(a, [1, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1, 0])) * math.pi).as_matrix()
    return Rot.from_rotvec(ax / s * math.atan2(s, a @ b)).as_matrix()


def adjacency(lt, nv, sel):
    """Edges of the triangles among the vertices `sel` (indices into 0..nv): returns (ea, eb) in sel's numbering."""
    idx = np.full(nv, -1)
    idx[sel] = np.arange(len(sel))
    E = np.r_[lt[:, [0, 1]], lt[:, [1, 2]], lt[:, [2, 0]]]
    E.sort(1)
    E = np.unique(E, axis=0)
    E = E[(idx[E[:, 0]] >= 0) & (idx[E[:, 1]] >= 0)]
    return idx[E[:, 0]], idx[E[:, 1]]


def target_point(t, bones):
    if isinstance(t, str) and t.startswith("bone:"):
        nm, end = t[5:].rsplit(".", 1)
        b = bones[nm]
        return np.array(b.head_local if end == "head" else b.tail_local)
    return np.array(t, float)


def top4(W):
    keep = np.argsort(-W, axis=1)[:, :4]
    W4 = np.zeros_like(W)
    rows = np.arange(len(W))[:, None]
    W4[rows, keep] = W[rows, keep]
    W4[W4 < 0.01] = 0
    z_ = W4.sum(1) == 0                     # (every weight under 0.01, e.g. a refilled island: its largest bone takes it all)
    if z_.any():
        W4[np.nonzero(z_)[0], keep[z_, 0]] = 1.0
        log("weights: %d verts had only weights under 0.01 -> their largest bone" % z_.sum())
    W4 /= np.maximum(W4.sum(1, keepdims=True), 1e-12)
    return W4


def armour_weights(spec, P, body, W4, gn, posed, ea, eb, col):
    """One armour piece rides `bones` rigidly: selected by shapes (load frame, Tripo pose; optional colour tests on the
    baked albedo), grown by `grow` rings, weighted to spec["bones"] (fixed shares) with an optional fade from a second
    bone along the first bone's axis ("fade": {"bone": b, "share": s, "len": L}: share s at the first bone's head, 0
    at L down it); then `seam_rings` rings of the coat round it smoothed; optionally shrunk toward the first bone's
    head (`scale`) and lowered (`drop`)."""
    nb = len(body)
    A = sp.coo_matrix((np.ones(len(ea)), (ea, eb)), shape=(nb, nb))
    A = (A + A.T).tocsr()
    Pl = C.to_game(C.from_game(P[body], XF), XF0)          # (the config's frame)
    m = C.shapes(Pl, spec["select"], col)
    for _ in range(int(spec.get("grow", 0))):
        m = m | (A @ m.astype(float) > 0)
    if "within" in spec:
        m &= C.shapes(Pl, spec["within"], col)
    bones = spec["bones"]
    b0 = list(bones)[0]
    W = W4.copy()
    W[m] = 0
    for b, s in bones.items():
        W[m, gn.index(b)] = s
    fd = spec.get("fade")
    if fd:
        h = posed[b0][:3, 3]
        d = posed[b0][:3, 1]
        t = np.clip(((P[body] - h) @ d) / fd["len"], 0, 1)
        sh = fd["share"] * (1 - t * t * (3 - 2 * t))
        W[m, gn.index(fd["bone"])] = sh[m]
        W[m] *= (1.0 / np.maximum(W[m].sum(1, keepdims=True), 1e-9))
    band = m.copy()
    for _ in range(int(spec.get("seam_rings", 3))):
        band = band | (A @ band.astype(float) > 0)
    band &= ~m
    deg = np.asarray(A.sum(1)).ravel()
    for _ in range(6):
        Wn = (A @ W) / np.maximum(deg, 1)[:, None]
        W[band] = 0.5 * W[band] + 0.5 * Wn[band]
    sc, dr = float(spec.get("scale", 1.0)), float(spec.get("drop", 0.0))
    if sc != 1.0 or dr != 0.0:
        f = m.astype(float)
        ring = m.copy()
        for k in range(1, 4):
            nxt = ring | (A @ ring.astype(float) > 0)
            f[nxt & ~ring] = 1.0 - k / 4.0
            ring = nxt
        h = posed[b0][:3, 3]
        Pb = P[body]
        P[body] = Pb + f[:, None] * ((h + (Pb - h) * sc) - Pb) - f[:, None] * np.array((0.0, 0.0, dr))
    log("armour %s: %d verts rigid to %s, %d seam verts smoothed%s" % (spec["name"], m.sum(), bones, band.sum(),
        ", scaled %.2f, dropped %.3f" % (sc, dr) if (sc != 1.0 or dr != 0.0) else ""))
    REPORT.setdefault("armour", {})[spec["name"]] = int(m.sum())
    return top4(W)


def main():
    import old as oldmod
    arm = oldmod.open_old(CFG["old"])
    old_dir = os.path.dirname(os.path.abspath(CFG["old"]))
    for im in bpy.data.images:            # (a build's blend points at the runner's paths: look beside the blend)
        if im.source == "FILE" and not im.packed_file:
            if not os.path.exists(bpy.path.abspath(im.filepath)):
                im.filepath = os.path.join(old_dir, os.path.basename(im.filepath))
            if os.path.exists(bpy.path.abspath(im.filepath)):
                im.reload()
                im.pack()
            log("image", im.name, tuple(im.size), "packed" if im.packed_file else "MISSING")
    sc = bpy.context.scene
    old = bpy.data.objects[INFO["mesh"]]
    bones = {b.name: b for b in arm.data.bones}
    rest = {n: np.array(b.matrix_local) for n, b in bones.items()}
    to_arm = np.array(arm.matrix_world.inverted() @ old.matrix_world)
    assert np.allclose(to_arm, np.eye(4), atol=1e-5), "the old mesh is not in armature space: %s" % to_arm

    o = np.load(os.path.join(WK, "old.npz"))
    V0, W0, gn, T0, Tp = o["V"], o["W"].astype(float), [str(x) for x in o["gn"]], o["T"], o["Tprop"]
    tri0 = T0[Tp == -1]
    props_bones = set(INFO["prop_bones"])
    body_groups = [i for i, n in enumerate(gn) if n not in props_bones]

    # ---- the fitted pose
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
        if n in FIT["rotvec"]:
            R[:3, :3] = Rot.from_rotvec(FIT["rotvec"][n]).as_matrix()
        p = parent[n]
        posed[n] = rest[n] @ R if p is None else posed[p] @ np.linalg.inv(rest[p]) @ rest[n] @ R
    SK = {n: posed[n] @ np.linalg.inv(rest[n]) for n in order}

    def blend(W, names):
        M = np.zeros((len(W), 4, 4))
        for j, n in enumerate(names):
            w = W[:, j]
            if (w > 0).any() and n in SK:
                M += w[:, None, None] * SK[n][None]
        return M

    Vp = np.einsum("nij,nj->ni", blend(W0, gn), np.c_[V0, np.ones(len(V0))])[:, :3]     # the old mesh, fitted pose

    # ---- the new low-poly (Tripo pose, fitted game frame)
    with bpy.data.libraries.load(LOW) as (src, dst):
        dst.objects = ["HeroLow"]
    low = dst.objects[0]
    lm = low.data
    nv = len(lm.vertices)
    P = np.zeros(nv * 3)
    lm.vertices.foreach_get("co", P)
    P = P.reshape(-1, 3)
    fpart = np.zeros(len(lm.polygons), np.int32)
    lm.attributes["part"].data.foreach_get("value", fpart)
    lm.calc_loop_triangles()
    lt = np.array([t.vertices[:] for t in lm.loop_triangles])
    ltp = fpart[np.array([t.polygon_index for t in lm.loop_triangles])]
    vpart = np.zeros(nv, np.int32)
    for k in range(3):
        vpart[lt[:, k]] = ltp
    log("low", nv, "verts", len(lm.polygons), "faces; parts", np.bincount(fpart).tolist())
    fn = np.cross(P[lt[:, 1]] - P[lt[:, 0]], P[lt[:, 2]] - P[lt[:, 0]])
    VN = np.zeros_like(P)
    for k in range(3):
        np.add.at(VN, lt[:, k], fn)
    VN /= np.maximum(np.linalg.norm(VN, axis=1), 1e-12)[:, None]
    # per-vertex baked albedo (armour colour tests)
    from PIL import Image
    ldir = os.path.dirname(os.path.abspath(LOW))
    uv = np.zeros(len(lm.loops) * 2)
    lm.uv_layers.active.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    lv = np.zeros(len(lm.loops), np.int64)
    lm.loops.foreach_get("vertex_index", lv)
    alb = np.asarray(Image.open(os.path.join(ldir, "hero_albedo.png")).convert("RGB")).astype(float) / 255
    S_ = alb.shape[0]
    cc = alb[np.clip(((1 - uv[:, 1]) * S_).astype(int), 0, S_ - 1), np.clip((uv[:, 0] * S_).astype(int), 0, S_ - 1)]
    vcol = np.zeros((nv, 3))
    cnt = np.zeros(nv)
    np.add.at(vcol, lv, cc)
    np.add.at(cnt, lv, 1)
    vcol /= np.maximum(cnt, 1)[:, None]

    # ---- body weights: nearest point of the posed old surface with an agreeing normal
    body = np.nonzero(vpart == 0)[0]
    A_, B_, C_ = Vp[tri0[:, 0]], Vp[tri0[:, 1]], Vp[tri0[:, 2]]
    tn = np.cross(B_ - A_, C_ - A_)
    area = np.linalg.norm(tn, axis=1) / 2
    tn /= np.maximum(2 * area, 1e-12)[:, None]
    rng = np.random.default_rng(1)
    ns = 600000
    ti = rng.choice(len(tri0), ns, p=area / area.sum())
    r1, r2 = rng.random(ns), rng.random(ns)
    flip = r1 + r2 > 1
    r1[flip], r2[flip] = 1 - r1[flip], 1 - r2[flip]
    bary = np.c_[1 - r1 - r2, r1, r2]
    Sm = A_[ti] * bary[:, :1] + B_[ti] * bary[:, 1:2] + C_[ti] * bary[:, 2:]
    d, nb = cKDTree(Sm).query(P[body], k=24)
    ok = (tn[ti[nb]] * VN[body][:, None, :]).sum(2) > 0.25
    # limb capsules (fitted pose): a sample whose main bone is an arm or leg bone only counts when the vertex lies
    # within that limb's reach (Mara's belt ends hang beside her left hand: they took the hand and trailed after it)
    LIMBS = [b_ for b_ in ("upperarm.R", "forearm.R", "hand.R", "upperarm.L", "forearm.L", "hand.L", "thigh.R", "shin.R",
                           "foot.R", "thigh.L", "shin.L", "foot.L") if b_ in gn and b_ in posed]
    def seg_dist(X, b_):
        h = posed[b_][:3, 3]
        L_ = np.linalg.norm(np.array(INFO["bones"][b_]["tail"]) - np.array(INFO["bones"][b_]["head"]))
        t_ = np.clip((X - h) @ posed[b_][:3, 1], 0, L_)
        return np.linalg.norm(X - (h + t_[:, None] * posed[b_][:3, 1]), axis=1)
    dom0 = np.argmax(W0, axis=1)
    inbody = np.zeros(len(W0), bool)
    inbody[np.unique(tri0)] = True
    cap = {}
    for b_ in LIMBS:
        j_ = gn.index(b_)
        m_ = (dom0 == j_) & inbody
        if m_.sum() > 10:
            cap[b_] = np.percentile(seg_dist(Vp[m_], b_), 95) * float(CFG.get("limb_reach", 1.3)) + 0.02
    sdom = dom0[tri0[ti, 0]]                       # main bone of each sample
    for b_, r_ in cap.items():
        j_ = gn.index(b_)
        far = seg_dist(P[body], b_) > r_
        ok &= ~((sdom[nb] == j_) & far[:, None])
    log("limb reach (m): %s" % {b_: round(float(r_), 3) for b_, r_ in cap.items()})
    first = np.where(ok.any(1), ok.argmax(1), 0)
    pick = nb[np.arange(len(body)), first]
    log("weights: %.1f%% of body verts matched with agreeing normals, median dist %.4f" % (
        100 * ok.any(1).mean(), np.median(d[np.arange(len(body)), first])))
    WB = np.zeros((len(body), len(gn)))
    for k in range(3):
        WB += bary[pick][:, k:k + 1] * W0[tri0[ti[pick], k]]
    WB[:, [i for i in range(len(gn)) if i not in body_groups]] = 0
    ea, eb = adjacency(lt, nv, body)
    deg = np.bincount(np.r_[ea, eb], minlength=len(body)).astype(float)
    for _ in range(int(CFG.get("weight_smooth", 4))):
        acc = np.zeros_like(WB)
        np.add.at(acc, ea, WB[eb])
        np.add.at(acc, eb, WB[ea])
        WB = 0.5 * WB + 0.5 * acc / np.maximum(deg, 1)[:, None]
    # limb weights must be connected to their limb: islands of an arm/leg bone's weight not touching its core are cleared
    # and refilled from their neighbours
    lost = np.zeros(len(body), bool)
    banned = np.zeros(WB.shape, bool)
    for b_, r_ in cap.items():
        j_ = gn.index(b_)
        m_ = WB[:, j_] > 0.05
        if not m_.any():
            continue
        idx_ = np.nonzero(m_)[0]
        ii = np.full(len(body), -1)
        ii[idx_] = np.arange(len(idx_))
        sel = m_[ea] & m_[eb]
        from scipy.sparse.csgraph import connected_components
        nc, cl = connected_components(sp.coo_matrix((np.ones(sel.sum()), (ii[ea[sel]], ii[eb[sel]])), shape=(len(idx_), len(idx_))), directed=False)
        core = seg_dist(P[body][idx_], b_) < r_ * 0.6
        good = np.isin(cl, np.unique(cl[core]))
        # ... and within reach along the surface (a hand fused to a skirt must not reach the belt's ends through it)
        from scipy.sparse.csgraph import dijkstra
        el = np.linalg.norm(P[body][ea[sel]] - P[body][eb[sel]], axis=1)
        G_ = sp.coo_matrix((el, (ii[ea[sel]], ii[eb[sel]])), shape=(len(idx_), len(idx_))).tocsr()
        if core.any() and not b_.startswith(("thigh", "shin", "foot")):
            gd = dijkstra(G_, directed=False, indices=np.nonzero(core)[0], min_only=True)
            good &= gd < r_ * float(CFG.get("limb_reach_surface", 1.0))
        bad_ = idx_[~good]
        if len(bad_):
            WB[bad_, j_] = 0
            lost[bad_] = True
            banned[bad_, j_] = True
            log("weights: %d verts of %s cut off from the limb, cleared" % (len(bad_), b_))
    lost &= WB.sum(1) < 0.999
    for _ in range(300):
        if not lost.any():
            break
        acc = np.zeros_like(WB)
        np.add.at(acc, ea, WB[eb])
        np.add.at(acc, eb, WB[ea])
        avg = acc / np.maximum(deg, 1)[:, None]
        avg[banned] = 0                          # (the cleared bone stays cleared)
        WB[lost] = avg[lost]
    zero = WB.sum(1) < 1e-6
    if zero.any() and CFG.get("orphans", "root") == "nearest":     # (htA config: they take their nearest weighted vertex's weights)
        okv = np.nonzero(~zero)[0]
        _, nn_ = cKDTree(P[body][okv]).query(P[body][zero])
        WB[zero] = WB[okv[nn_]]
        log("weights: %d verts with nothing left -> their nearest weighted vertex's" % zero.sum())
    elif zero.any() and CFG.get("orphan_nearest", False):
        # (htB config orphan_nearest) the nearest fitted bone segment that was not banned for it, instead of root: a few
        # cleared hand/forearm verts left on root stayed behind as long spikes when the arm moved (Big Jim)
        cand = [b_ for b_ in gn if b_ in posed and gn.index(b_) in body_groups]
        Dz = np.stack([seg_dist(P[body][zero], b_) for b_ in cand], 1)
        Dz[banned[zero][:, [gn.index(b_) for b_ in cand]]] = 1e9
        WB[np.nonzero(zero)[0], [gn.index(cand[k]) for k in Dz.argmin(1)]] = 1.0
        log("weights: %d verts with nothing left -> their nearest bone" % zero.sum())
    elif zero.any():
        WB[zero, gn.index("root")] = 1.0
        log("weights: %d verts with nothing left -> root" % zero.sum())
    # limbs: the transferred weights decide how much a vertex belongs to an arm or a leg; how that share splits between
    # its bones (upper, lower, hand/foot) is redone from the fitted bones' segments (inverse 4th power of the distance),
    # so a limb whose old and Tripo shapes differ still bends at its joints (Mara's right forearm took half its weight
    # from the hand and the upper arm, and her bracer crumpled)
    # limb_own (config, off by default): the arm or leg surface claims its own vertices. A vertex within "r" of the
    # limb's fitted bone segments (and inside "select", outside "not": shapes in the load frame, colour tests on the
    # baked albedo) loses its trunk / other weights to the limb, fading in over the first "fade" (share of the first
    # bone's length) from the limb's root. Kael's sleeve bands and bracer had taken the old cape's chest weight (the
    # old cape hung where the Tripo arm is) and stretched into sheets when he raised his arm.
    for lo in CFG.get("limb_own", []):
        cb = lo["bones"]
        ci = [gn.index(c) for c in cb]
        Pb_ = P[body]
        Dm = np.stack([seg_dist(Pb_, c) for c in cb], 1)
        m_ = Dm.min(1) < float(lo.get("r", 0.12))
        if lo.get("select") or lo.get("not"):
            Pl_ = C.to_game(C.from_game(Pb_, XF), XF0)
            if lo.get("select"):
                m_ &= C.shapes(Pl_, lo["select"], vcol[body])
            if lo.get("not"):
                m_ &= ~C.shapes(Pl_, lo["not"], vcol[body])
        h0, h1 = posed[cb[0]][:3, 3], None
        L0 = np.linalg.norm(np.array(INFO["bones"][cb[0]]["tail"]) - np.array(INFO["bones"][cb[0]]["head"]))
        ax0 = posed[cb[0]][:3, 1]
        tt = np.clip(((Pb_ - h0) @ ax0) / (L0 * float(lo.get("fade", 0.3))), 0, 1)
        iv = 1.0 / np.maximum(Dm, 0.01) ** 4
        Wl = np.zeros_like(WB)
        Wl[:, ci] = iv / iv.sum(1, keepdims=True)
        f = (tt * tt * (3 - 2 * tt))[:, None]
        WB[m_] = f[m_] * Wl[m_] + (1 - f[m_]) * WB[m_]
        log("weights: limb_own %s: %d verts claimed" % ("/".join(cb), m_.sum()))
    if CFG.get("limb_regeom", True):
        for side in ("R", "L"):
            for chain in (("upperarm", "forearm", "hand"), ("thigh", "shin", "foot")):
                cb = [c + "." + side for c in chain]
                if not all(c in gn and c in posed for c in cb):
                    continue
                ci = [gn.index(c) for c in cb]
                Sc = WB[:, ci].sum(1)
                m_ = Sc > 0.02
                Dm = np.stack([seg_dist(P[body][m_], c) for c in cb], 1)
                iv = 1.0 / np.maximum(Dm, 0.01) ** 4
                WB[np.ix_(np.nonzero(m_)[0], ci)] = Sc[m_, None] * iv / iv.sum(1, keepdims=True)
        log("weights: limb shares redistributed along the fitted bones")
    hb = posed["head"]
    hlen = np.linalg.norm(np.array(INFO["bones"]["head"]["tail"]) - np.array(INFO["bones"]["head"]["head"]))
    zr = CFG["head_rigid_above"]
    zr = (hb[:3, 3] + hb[:3, 1] * hlen * 0.3)[2] if zr is None else float(zr)
    hi_ = gn.index("head")
    up = P[body, 2] > zr
    WB[up] = 0
    WB[up, hi_] = 1
    log("head rigid above z %.3f (Tripo pose): %d verts" % (zr, up.sum()))
    W4 = top4(WB)
    for spec in CFG["armour"]:
        W4 = armour_weights(spec, P, body, W4, gn, posed, ea, eb, vcol[body])

    if "--debug" in sys.argv:
        np.savez(os.path.join(OUT, "rig_debug.npz"), P=P, body=body, W4=W4, gn=np.array(gn), lt=lt, vcol=vcol)
    # ---- into the rest pose: invert the skinning of the fitted pose
    M = blend(W4, gn)
    bad = ~np.isfinite(M).all((1, 2)) | (np.abs(np.linalg.det(M[:, :3, :3])) < 1e-6)
    if bad.any():
        # (a vertex whose weights blend to a degenerate matrix, e.g. all its weight was on a prop bone: it takes the
        # weights of the nearest good vertex; Kael's fist round his javelin)
        good = np.nonzero(~bad)[0]
        _, nn = cKDTree(P[body][good]).query(P[body][bad])
        log("weights: %d verts blend to a singular matrix (weight sums %s); they take their nearest good neighbour's" % (
            bad.sum(), np.unique(W4[bad].sum(1).round(3))[:8]))
        W4[bad] = W4[good[nn]]
        M = blend(W4, gn)
    Prest = P.copy()
    Prest[body] = np.einsum("nij,nj->ni", np.linalg.inv(M), np.c_[P[body], np.ones(len(body))])[:, :3]
    sole_old = V0[np.unique(tri0), 2].min()
    dz = sole_old - Prest[body, 2].min()
    Prest[body, 2] += dz
    log("soles moved by %.4f to the old soles (z %.4f)" % (dz, sole_old))
    mv = np.linalg.norm(Prest[body] - P[body], axis=1)
    log("body to rest: moved median %.4f max %.4f" % (np.median(mv), mv.max()))

    # ---- the props
    xfs = {}
    prop_verts = {}
    prop_multi = {}
    obj_props = {}
    for k, p in enumerate(CFG["props"], start=1):
        if p.get("drop"):
            continue
        vs = np.nonzero(vpart == k)[0]
        if len(vs) == 0:
            log("prop %s: no vertices in the low mesh, skipped" % p["name"])
            continue
        bone = p.get("bone") or (p["name"] if p["name"] in SK else "root")
        pl0 = p.get("place", "fit")
        S_b = SK[pl0.get("frame", bone) if isinstance(pl0, dict) else bone]   # (place.frame: the bone whose fitted
        # pose the prop is read in, e.g. a pistol on its own root-level bone but held in hand.R: "frame": "hand.R")
        Sinv = np.linalg.inv(S_b)
        def fit_xf(X, Sinv=Sinv):
            return (np.c_[X, np.ones(len(X))] @ Sinv.T)[:, :3]
        pl = p.get("place", "fit")
        if isinstance(pl, str):
            pl = {"mode": pl}
        mode = pl.get("mode", "fit")
        if "like" in pl:
            f = xfs[pl["like"]]
        elif mode == "fit":
            f = fit_xf
        elif mode == "points":
            Aa, Bb = fit_xf(load_to_final(pl["from"][0]))[0], fit_xf(load_to_final(pl["from"][1]))[0]
            a, b = target_point(pl["to"][0], bones), target_point(pl["to"][1], bones)
            R = rot_between(Bb - Aa, b - a)
            s = pl.get("scale", "match")
            s = np.linalg.norm(b - a) / np.linalg.norm(Bb - Aa) if s == "match" else (1.0 if s == "keep" else float(s))
            a_hand = a.copy()                     # where the fist goes (hand_follow): the first target, even when
            if pl.get("anchor", 0) == 1:          # the second landmark lands exactly; the first slides along the line
                a = b - nrm(b - a) * s * np.linalg.norm(Bb - Aa)   # the prop slides through the fist (anchor 1)
            if pl.get("spin"):
                R = Rot.from_rotvec(nrm(b - a) * math.radians(pl["spin"])).as_matrix() @ R
            off = np.array(pl.get("offset", [0, 0, 0]), float)
            d_ = nrm(b - a)
            Lp = s * np.linalg.norm(Bb - Aa)                 # A->B after scaling ...
            Lt = np.linalg.norm(b - a)                       # ... and where B must land
            st = pl.get("stretch")                           # [t0, t1]: that stretch of A->B (0 at A, 1 at B) is
            k_st = 1.0                                       # lengthened so B lands on b while A stays on a
            if st:
                t0, t1 = st
                k_st = (Lt - Lp * (1 - (t1 - t0))) / (Lp * (t1 - t0))
            sh = pl.get("shorten")                           # [t0, t1, k]: that stretch of the line (0 at A, 1 at B; may
                                                             # be < 0, behind A) scaled by k toward A, what lies beyond
                                                             # it (away from A) follows (Aldric's hilt behind his fist)
            def f(X, Aa=Aa, a=a, R=R, s=s, off=off, fit_xf=fit_xf, st=st, k_st=k_st, d_=d_, Lp=Lp, sh=sh):
                Y = s * (fit_xf(X) - Aa) @ R.T
                if st:
                    u = Y @ d_
                    t0, t1 = st[0] * Lp, st[1] * Lp
                    du = np.where(u < t0, 0.0, np.where(u > t1, (k_st - 1) * (t1 - t0), (k_st - 1) * (u - t0)))
                    Y = Y + du[:, None] * d_
                if sh:
                    u = Y @ d_
                    t0, t1, k = sh[0] * Lp, sh[1] * Lp, float(sh[2])
                    if t1 <= 0:                              # behind A: the near end is t1
                        du = np.where(u > t1, 0.0, np.where(u < t0, (1 - k) * (t1 - t0), (1 - k) * (t1 - u)))
                    else:                                    # in front of A: the near end is t0
                        du = np.where(u < t0, 0.0, np.where(u > t1, -(1 - k) * (t1 - t0), -(1 - k) * (u - t0)))
                    Y = Y + du[:, None] * d_
                return a + off + Y
            log("prop %s: %s -> %s, scale %.3f, turned %.1f deg%s" % (p["name"], np.round(Aa, 3), np.round(a, 3), s,
                np.degrees(np.linalg.norm(Rot.from_matrix(R).as_rotvec())), ", stretched x%.2f over %s" % (k_st, st) if st else ""))
            if pl.get("hand_follow"):
                # the fist turns with the prop (about the grip) so the prop still goes through it. The turn is spread
                # up the forearm like a twist: a vertex turns by the angle times k, k = its hand weight plus its
                # forearm weight times its place along the forearm (0 at the elbow, 1 at the wrist), smoothstepped;
                # the turn is interpolated as a rotation (a linear blend of positions tore the bracer at the wrist)
                hb_ = pl.get("hand", bone)
                fb_ = INFO["bones"][hb_]["parent"]
                wh = W4[:, gn.index(hb_)]
                wf = W4[:, gn.index(fb_)] if fb_ in gn else np.zeros_like(wh)
                e0, e1 = np.array(bones[fb_].head_local), np.array(bones[fb_].tail_local)
                tt = np.clip(((Prest[body] - e0) @ (e1 - e0)) / ((e1 - e0) @ (e1 - e0)), 0, 1)
                tt = tt * tt * (3 - 2 * tt)
                kk = np.clip(wh + wf * tt, 0, 1)
                rv = Rot.from_matrix(R).as_rotvec()
                Xb = Prest[body]
                mv_ = kk > 1e-4
                Rk = Rot.from_rotvec(kk[mv_, None] * rv[None]).as_matrix()
                Xn = Xb.copy()
                Xn[mv_] = Aa + np.einsum("nij,nj->ni", Rk, Xb[mv_] - Aa) + kk[mv_, None] * (a_hand + off - Aa)
                Prest[body] = Xn
                ax_ = nrm(rv)
                fdir = nrm(e1 - e0)
                REPORT.setdefault("hand_follow", {})[p["name"]] = dict(hand=hb_, verts=int(mv_.sum()), deg=round(float(np.degrees(np.linalg.norm(rv))), 1),
                                                                      twist_share=round(float(abs(ax_ @ fdir)), 2))
                log("prop %s: %d body verts on %s/%s turned with it (axis . forearm = %.2f: 1 is a pure twist)" % (p["name"], mv_.sum(), hb_, fb_, ax_ @ fdir))
        else:
            raise ValueError(mode)
        xfs[p["name"]] = f
        Prest[vs] = f(P[vs])
        if p.get("object"):
            obj_props[p["name"]] = (vs, p["object"])
        else:
            prop_verts[p["name"]] = (vs, bone)
            if p.get("bones"):
                # several bones (Wren's bow: grip, inner and outer limbs, string halves): each vertex to the nearest
                # bone's rest segment, blended over `bone_blend` (m) between the two nearest
                bl_ = list(p["bones"])
                Xr_ = Prest[vs]
                Dd = np.stack([np.linalg.norm(Xr_ - (np.array(bones[b_].head_local) + np.clip(
                    ((Xr_ - np.array(bones[b_].head_local)) @ (np.array(bones[b_].tail_local) - np.array(bones[b_].head_local)))
                    / max(np.sum((np.array(bones[b_].tail_local) - np.array(bones[b_].head_local)) ** 2), 1e-12), 0, 1)[:, None]
                    * (np.array(bones[b_].tail_local) - np.array(bones[b_].head_local))), axis=1) for b_ in bl_], 1)
                bb = float(p.get("bone_blend", 0.0))
                if bb > 0:
                    Wm = np.clip(1 - (Dd - Dd.min(1, keepdims=True)) / bb, 0, 1)
                    o2 = np.argsort(-Wm, axis=1)[:, 2:]
                    np.put_along_axis(Wm, o2, 0.0, axis=1)
                else:
                    Wm = np.zeros_like(Dd)
                    Wm[np.arange(len(Dd)), Dd.argmin(1)] = 1.0
                for ov in p.get("bone_override", []):        # rest-frame shapes that ride one bone outright (Wren's
                    m_ = C.shapes(Xr_, ov["shapes"])            # grip between the two limbs' heads: hand.L)
                    if ov["bone"] not in bl_:
                        bl_.append(ov["bone"])
                        Wm = np.c_[Wm, np.zeros(len(Wm))]
                    Wm[m_] = 0
                    Wm[m_, bl_.index(ov["bone"])] = 1.0
                Wm /= Wm.sum(1, keepdims=True)
                ns_ = int(p.get("bone_smooth", 0))           # Laplacian passes over the prop's own edges (no hard
                if ns_:                                      # step where an override meets the limbs)
                    pa_, pb_ = adjacency(lt, nv, vs)
                    dg_ = np.bincount(np.r_[pa_, pb_], minlength=len(vs)).astype(float)
                    for _ in range(ns_):
                        ac_ = np.zeros_like(Wm)
                        np.add.at(ac_, pa_, Wm[pb_])
                        np.add.at(ac_, pb_, Wm[pa_])
                        Wm = 0.5 * Wm + 0.5 * ac_ / np.maximum(dg_, 1)[:, None]
                    o2 = np.argsort(-Wm, axis=1)[:, 3:]
                    np.put_along_axis(Wm, o2, 0.0, axis=1)
                    Wm[Wm < 0.01] = 0
                    Wm /= Wm.sum(1, keepdims=True)
                prop_multi[p["name"]] = (bl_, Wm)
                log("prop %s: split over %s: %s verts" % (p["name"], bl_, (Wm > 0.5).sum(0).tolist()))
        Xr = Prest[vs]
        REPORT.setdefault("props", {})[p["name"]] = dict(bone=bone, verts=int(len(vs)), bbox=[Xr.min(0).round(3).tolist(), Xr.max(0).round(3).tolist()])
        log("prop %s on %s (%s): %d verts, rest bbox %s .. %s" % (p["name"], bone, mode if "like" not in pl else "like " + pl["like"],
            len(vs), Xr.min(0).round(3), Xr.max(0).round(3)))

    lm.vertices.foreach_set("co", Prest.astype(np.float32).ravel())
    lm.update()
    # props that replace another object's mesh (e.g. stones that orbit her: SpinSlowStones, turned in game): split off,
    # moved into that object's space (they keep the new atlas' UVs and the hero material)
    for nm, (vs, oname) in obj_props.items():
        tgt = bpy.data.objects[oname]
        bm_ = bmesh.new()
        bm_.from_mesh(lm)
        bm_.verts.ensure_lookup_table()
        keep = set(vs.tolist())
        bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.index not in keep], context="VERTS")
        M_ = tgt.matrix_world.inverted() @ arm.matrix_world
        for v in bm_.verts:
            v.co = M_ @ v.co
        nme = bpy.data.meshes.new(tgt.data.name + "_new")
        bm_.to_mesh(nme)
        bm_.free()
        if CFG["props"][[q["name"] for q in CFG["props"]].index(nm)].get("old_places"):
            # each loose piece goes where an old piece was (matched by angle round the object's Z axis): the Tripo
            # shapes on the old layout (Mara's stones orbit at the old radius and height, clear of her head and staff)
            def pieces(me):
                co = np.array([v.co for v in me.vertices])
                ed = np.array([e.vertices[:] for e in me.edges])
                A = sp.coo_matrix((np.ones(len(ed)), (ed[:, 0], ed[:, 1])), shape=(len(co), len(co)))
                from scipy.sparse.csgraph import connected_components
                n_, l_ = connected_components(A, directed=False)
                return co, l_, [co[l_ == i].mean(0) for i in range(n_)]
            co_n, l_n, c_n = pieces(nme)
            _, _, c_o = pieces(tgt.data)
            if len(c_n) == len(c_o):
                ang = lambda c: math.atan2(c[1], c[0])
                on = sorted(range(len(c_n)), key=lambda i: ang(c_n[i]))
                oo = sorted(range(len(c_o)), key=lambda i: ang(c_o[i]))
                # the rotation of the order that moves the pieces least
                best = min(range(len(on)), key=lambda r: sum(np.linalg.norm(c_n[on[i]] - c_o[oo[(i + r) % len(oo)]]) for i in range(len(on))))
                for i in range(len(on)):
                    a_, b_ = on[i], oo[(i + best) % len(oo)]
                    co_n[l_n == a_] += c_o[b_] - c_n[a_]
                nme.vertices.foreach_set("co", co_n.astype(np.float32).ravel())
                nme.update()
                log("prop %s: %d pieces moved onto the old pieces' places" % (nm, len(c_n)))
                REPORT.setdefault("old_places", {})[nm] = [np.round(c, 3).tolist() for c in c_o]
            else:
                log("prop %s: %d pieces, the old object has %d: left where the fit put them" % (nm, len(c_n), len(c_o)))
        if "part" in nme.attributes:
            nme.attributes.remove(nme.attributes["part"])
        oldd = tgt.data
        dn = oldd.name
        for m_ in oldd.materials:
            nme.materials.append(m_)
        nme.polygons.foreach_set("material_index", np.zeros(len(nme.polygons), np.int32))
        tgt.data = nme
        bpy.data.meshes.remove(oldd)
        nme.name = dn
        log("prop %s -> object %s (%d verts, %d faces)" % (nm, oname, len(nme.vertices), len(nme.polygons)))
        bm_ = bmesh.new()
        bm_.from_mesh(lm)
        bm_.verts.ensure_lookup_table()
        bmesh.ops.delete(bm_, geom=[bm_.verts[i] for i in vs.tolist()], context="VERTS")
        bm_.to_mesh(lm)
        bm_.free()
    if obj_props:
        nv2 = len(lm.vertices)
        keepm = np.ones(nv, bool)
        for vs, _ in obj_props.values():
            keepm[vs] = False
        newidx = np.cumsum(keepm) - 1
        body = newidx[body[keepm[body]]]
        prop_verts = {k: (newidx[v], b) for k, (v, b) in prop_verts.items()}
        assert nv2 == keepm.sum()

    # ---- forearm twist bones (cfg "twist_bones", opt-in): the old clips turn the hands far round the forearm (Aldric's
    # right hand 100-180 deg in every clip); a realistic wrist (a gauntlet on a vambrace) tears where the two meet. A
    # bone forearm_twist.<side> (child of the forearm, from `twist_at` of its length to the wrist, same axis) is added
    # and every action gets its rotation: `twist_share` of the hand's twist about the forearm axis (swing-twist per
    # frame, unwrapped across frames); the forearm's weight is split toward it along the forearm (0 at `twist_from`,
    # all of it at `twist_to`, fractions of the forearm from the elbow).
    tw_cfg = CFG.get("twist_bones")
    if tw_cfg:
        sides = tw_cfg if isinstance(tw_cfg, list) else ["R", "L"]
        t_at, t_sh = float(CFG.get("twist_at", 0.6)), float(CFG.get("twist_share", 0.5))
        t_from, t_to = float(CFG.get("twist_from", 0.3)), float(CFG.get("twist_to", 0.85))
        co_ = np.zeros(len(lm.vertices) * 3)
        lm.vertices.foreach_get("co", co_)
        Pb_ = co_.reshape(-1, 3)[body]
        for side in sides:
            fa_n, h_n, t_n = "forearm." + side, "hand." + side, "forearm_twist." + side
            if fa_n not in gn or h_n not in bones:
                continue
            # the bone
            bpy.context.view_layer.objects.active = arm
            for o_ in sc.objects:
                o_.select_set(o_ == arm)
            bpy.ops.object.mode_set(mode="EDIT")
            eb = arm.data.edit_bones
            fe = eb[fa_n]
            nb_ = eb.new(t_n)
            nb_.head = fe.head + (fe.tail - fe.head) * t_at
            nb_.tail = fe.tail.copy()
            nb_.roll = fe.roll
            nb_.parent = fe
            nb_.use_connect = False
            nb_.use_deform = True
            bpy.ops.object.mode_set(mode="OBJECT")
            bones = {b.name: b for b in arm.data.bones}
            # its rotation in every action
            Fr = np.array(arm.data.bones[fa_n].matrix_local)[:3, :3]
            Hr = np.array(arm.data.bones[h_n].matrix_local)[:3, :3]
            ax = Hr.T @ Fr[:, 1]                                  # the forearm's axis in the hand's rest frame
            pb_h, pb_t = arm.pose.bones[h_n], arm.pose.bones[t_n]
            pb_t.rotation_mode = "QUATERNION"
            arm.animation_data_create()
            worst = []
            for act in bpy.data.actions:
                arm.animation_data.action = act
                try:
                    arm.animation_data.action_slot = act.slots[0]
                except Exception:
                    pass
                f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
                ths, sws = [], []
                for fr in range(f0, f1 + 1):
                    sc.frame_set(fr)
                    q = pb_h.matrix_basis.to_quaternion()
                    w, v = q.w, np.array([q.x, q.y, q.z])
                    th = 2 * math.atan2(v @ ax, w)               # the hand's twist about the forearm axis (mod 2 pi)
                    ths.append(math.atan2(math.sin(th), math.cos(th)))
                    sws.append(math.degrees(math.acos(max(-1.0, min(1.0, float((Hr @ np.array(q.to_matrix()) @ Hr.T @ Fr[:, 1]) @ Fr[:, 1]))))))
                # each frame's twist taken within half a turn of the clip's circular mean (no flips, no winding:
                # a clip that ends where it starts gets a twist bone that does too)
                ths = np.array(ths)
                m_ = math.atan2(np.sin(ths).mean(), np.cos(ths).mean())
                ths = m_ + np.arctan2(np.sin(ths - m_), np.cos(ths - m_))
                for k_, fr in enumerate(range(f0, f1 + 1)):
                    h_ = ths[k_] * t_sh / 2
                    pb_t.rotation_quaternion = (math.cos(h_), 0.0, math.sin(h_), 0.0)
                    pb_t.keyframe_insert("rotation_quaternion", frame=fr)
                    worst.append((round(abs(math.degrees(ths[k_]))), round(sws[k_]), act.name, fr))
            worst.sort(reverse=True)
            REPORT.setdefault("twist_bones", {})[t_n] = dict(max_twist=worst[0][0], worst=[list(x) for x in worst[:3]])
            log("twist bone %s: hand twist about the forearm up to %d deg (%s %d), %.0f%% of it on the twist bone" % (
                t_n, worst[0][0], worst[0][2], worst[0][3], t_sh * 100))
            # the weights: the forearm's share moves to the twist bone toward the wrist
            gn.append(t_n)
            body_groups.append(len(gn) - 1)
            W4 = np.c_[W4, np.zeros(len(W4))]
            jf, jt = gn.index(fa_n), len(gn) - 1
            e0, e1 = np.array(bones[fa_n].head_local), np.array(bones[fa_n].tail_local)
            tt = np.clip(((Pb_ - e0) @ (e1 - e0)) / ((e1 - e0) @ (e1 - e0)), 0, 1)
            s_ = np.clip((tt - t_from) / max(t_to - t_from, 1e-6), 0, 1)
            s_ = s_ * s_ * (3 - 2 * s_)
            mv_ = W4[:, jf] * s_
            W4[:, jt] = mv_
            W4[:, jf] -= mv_
            log("twist bone %s: %d verts share the forearm's weight with it" % (t_n, (mv_ > 0.01).sum()))
        W4 = top4(W4)
        arm.animation_data.action = None

    # ---- replace the old mesh's data; keep the object, its mesh data name and modifier
    old_me = old.data
    keep_name = old_me.name
    old_me.name = keep_name + "_old"
    old.data = lm
    lm.name = keep_name
    old.vertex_groups.clear()
    groups = {n: old.vertex_groups.new(name=n) for n in gn}
    for j in body_groups:
        w = W4[:, j]
        nz = np.nonzero(w > 0)[0]
        g = groups[gn[j]]
        for val in np.unique(np.round(w[nz], 4)):
            sel = nz[np.round(w[nz], 4) == val]
            g.add(body[sel].tolist(), float(val), "REPLACE")
    for nm, (vs, bone) in prop_verts.items():
        if nm in prop_multi:
            bl_, Wm = prop_multi[nm]
            for j_, b_ in enumerate(bl_):
                if b_ not in groups:
                    groups[b_] = old.vertex_groups.new(name=b_)
                for val in np.unique(np.round(Wm[:, j_], 4)):
                    if val <= 0:
                        continue
                    sel = vs[np.round(Wm[:, j_], 4) == val]
                    groups[b_].add(sel.tolist(), float(val), "REPLACE")
            continue
        if bone not in groups:
            groups[bone] = old.vertex_groups.new(name=bone)
        groups[bone].add(vs.tolist(), 1.0, "REPLACE")
    bpy.data.meshes.remove(old_me)
    # detach (config, off by default): where the Tripo surface fuses a limb to something beside it (Kael's forearm lay
    # on his cape), the faces between them stretch into sheets when the limb moves. Inside "within" (rest armature
    # space), every vertex is the limb's (its share on "bones" >= 0.5) or the body's; the edges between the two are
    # split, the limb side keeps only its limb weights and the body side loses them.
    for dt in CFG.get("detach", []):
        gi_ = [old.vertex_groups[b].index for b in dt["bones"]]
        bm_ = bmesh.new()
        bm_.from_mesh(lm)
        dl_ = bm_.verts.layers.deform.active
        bm_.verts.ensure_lookup_table()
        Xr = np.array([v.co for v in bm_.verts])
        inr = C.shapes(Xr, dt["within"])
        share = np.array([sum(v[dl_].get(g_, 0.0) for g_ in gi_) for v in bm_.verts])
        limb = share >= float(dt.get("split", 0.5))
        if dt.get("parts_only_body", True):
            isb = np.zeros(len(Xr), bool)
            isb[body] = True
            inr &= isb
        cut = [e for e in bm_.edges if inr[e.verts[0].index] and inr[e.verts[1].index]
               and limb[e.verts[0].index] != limb[e.verts[1].index]]
        for v in bm_.verts:
            i = v.index
            if not inr[i] or share[i] <= 0 or share[i] >= 1:
                continue
            d = v[dl_]
            if limb[i]:
                for k_ in list(d.keys()):
                    if k_ not in gi_:
                        del d[k_]
                    else:
                        d[k_] = d[k_] / share[i]
            else:
                rest_ = 1.0 - share[i]
                for k_ in list(d.keys()):
                    if k_ in gi_:
                        del d[k_]
                    else:
                        d[k_] = d[k_] / rest_
        nv0 = len(bm_.verts)
        bmesh.ops.split_edges(bm_, edges=cut)
        bm_.to_mesh(lm)
        bm_.free()
        log("detach %s: %d edges split, %d verts added, %d verts in the region (%d the limb's)" % (
            "/".join(dt["bones"]), len(cut), len(lm.vertices) - nv0, inr.sum(), (inr & limb).sum()))
    mat = bpy.data.materials[INFO["material"]]
    for nd in mat.node_tree.nodes:
        if nd.type == "TEX_IMAGE" and nd.image is not None:
            nm = nd.image.name.lower()
            role = "albedo" if "albedo" in nm else ("normal" if "normal" in nm else ("orm" if "orm" in nm else None))
            if role is None:
                continue
            nd.image.source = "FILE"
            nd.image.filepath = os.path.join(ldir, "hero_%s.png" % role)
            if nd.image.packed_file:
                nd.image.unpack(method="REMOVE")
            nd.image.reload()
            nd.image.pack()
            log("image", nd.image.name, "<- hero_%s.png" % role, tuple(nd.image.size))
    lm.materials.clear()
    lm.materials.append(mat)
    for m in [m for m in bpy.data.materials if m.users == 0]:
        bpy.data.materials.remove(m)
    for im in [im for im in bpy.data.images if im.users == 0]:
        bpy.data.images.remove(im)

    # ---- glows on prop bones: kept as they were unless the config says otherwise
    for gname, g in CFG["glows"].items():
        ob = bpy.data.objects.get(gname)
        if ob is None:
            continue
        if "fit_to" in g or "at" in g:          # centred on a prop's piece (rest) or a bone point; radius given or the piece's
            if "fit_to" in g:
                vs, _ = prop_verts[g["fit_to"]]
                X = np.array([lm.vertices[i].co for i in vs.tolist()])
                cen = (X.max(0) + X.min(0)) / 2
            if "at" in g:
                cen = target_point(g["at"], bones)
            rad = float(g["radius"]) if "radius" in g else np.median(np.linalg.norm(X - cen, axis=1))
            rad *= float(g.get("pad", 1.0))
            me = ob.data
            co = np.zeros(len(me.vertices) * 3)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            c0 = (co.max(0) + co.min(0)) / 2
            r0 = np.median(np.linalg.norm(co - c0, axis=1))
            co = cen + (co - c0) * (rad / r0)
            me.vertices.foreach_set("co", co.astype(np.float32).ravel())
            me.update()
            log("glow %s: centred at %s, radius %.4f -> %.4f" % (gname, np.round(cen, 4), r0, rad))
            REPORT.setdefault("glows", {})[gname] = dict(centre=np.round(cen, 4).tolist(), radius=round(float(rad), 4), old_centre=np.round(c0, 4).tolist(), old_radius=round(float(r0), 4))
        if "box" in g:                          # stretched (per axis) so its bounding box is this rest-pose box
            bx = np.array(g["box"], float)          # [[x0, x1], [y0, y1], [z0, z1]] (armature space, rest)
            me = ob.data
            co = np.zeros(len(me.vertices) * 3)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            lo, hi = co.min(0), co.max(0)
            co = bx[:, 0] + (co - lo) / np.maximum(hi - lo, 1e-9) * (bx[:, 1] - bx[:, 0])
            me.vertices.foreach_set("co", co.astype(np.float32).ravel())
            me.update()
            log("glow %s: box %s .. %s -> %s" % (gname, np.round(lo, 3), np.round(hi, 3), bx.round(3).tolist()))
            REPORT.setdefault("glows", {})[gname] = dict(box=bx.round(4).tolist(), old_box=[lo.round(4).tolist(), hi.round(4).tolist()])
        if g.get("hide"):
            ob.hide_render = True
        if "offset" in g or "scale" in g:
            me = ob.data
            co = np.zeros(len(me.vertices) * 3)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            c = co.mean(0)
            co = c + (co - c) * float(g.get("scale", 1.0)) + np.array(g.get("offset", [0, 0, 0]))
            me.vertices.foreach_set("co", co.astype(np.float32).ravel())
            me.update()
            log("glow %s: scaled %.2f, moved %s" % (gname, g.get("scale", 1.0), g.get("offset", [0, 0, 0])))

    # ---- save and export
    for ob in sc.objects:
        ob.select_set(False)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "%s_hq.blend" % HID))
    path = os.path.join(OUT, "%s.glb" % HID)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                              export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                              export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
    tris = {ob.name: sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in sc.objects if ob.type == "MESH"}
    # weights check
    nz = np.array([len([g for g in v.groups if g.weight > 0]) for v in lm.vertices])
    ws = np.array([sum(g.weight for g in v.groups) for v in lm.vertices])
    REPORT.update(dict(glb=path, glb_bytes=os.path.getsize(path), tris=tris, char_tris=tris[INFO["mesh"]],
                       max_influences=int(nz.max()), weight_sum=[float(ws.min()), float(ws.max())], soles_dz=float(dz)))
    json.dump(REPORT, open(os.path.join(OUT, "rig_report.json"), "w"), indent=1)
    log("exported", path, os.path.getsize(path), "bytes; tris", tris, "; influences <= %d, weight sums %.4f..%.4f" % (nz.max(), ws.min(), ws.max()))


main()
