"""Step 4 (numpy): fill the holes the cuts left -> patches.pkl ({piece name: [(loop, interior points, triangles,
colours, roughness-metal)]}, Tripo units and vertex indices of the welded mesh).

    python3 patches.py -- --hero ugo

Every boundary loop (10 edges or more) of every piece (the body and each prop) is closed by a membrane: the loop is
projected on its best plane, filled with a triangulated grid at the loop's edge length, and the inner points placed
harmonically in 3D (and so are their colours, from the texture on the rim). The body's patches take the rim's colours
(cfg body_patch "rim") or, as Vega's coat did, the median of the rim's darker half ("dark": no smear of a prop's colour
into the body).
"""
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from scipy.spatial import Delaunay, cKDTree
from matplotlib.path import Path
from PIL import Image
import common as C


def loops_of(F, nv, mask):
    """Boundary loops of the face set (vertex index lists, in the faces' half-edge order)."""
    Fm = F[mask]
    he = np.concatenate([Fm[:, [0, 1]], Fm[:, [1, 2]], Fm[:, [2, 0]]])
    key = he[:, 0] * nv + he[:, 1]
    rkey = he[:, 1] * nv + he[:, 0]
    bd = ~np.isin(rkey, key)
    b = he[bd]
    nxt = {}
    for a, c in b.tolist():
        nxt.setdefault(a, []).append(c)
    loops, used = [], set()
    for a, c in b.tolist():
        if (a, c) in used:
            continue
        loop = [a]
        cur = c
        used.add((a, c))
        while cur != a:
            loop.append(cur)
            cands = [x for x in nxt.get(cur, []) if (cur, x) not in used]
            if not cands:
                break
            x = cands[0]
            used.add((cur, x))
            cur = x
        loops.append(loop)
    return loops


def main():
    hid = C.arg("--hero")
    cfg = C.load_cfg(hid)
    W = C.work_dir(hid)
    T = np.load(os.path.join(W, "topo.npz"))
    F, Pw = T["F"], T["Pw"]
    z = np.load(os.path.join(W, "tripo_np.npz"))
    UV, I, inv = z["UV"], z["I"], z["inv"]
    L = np.load(os.path.join(W, "labels.npz"))
    lab, names = L["lab"], [str(x) for x in L["names"]]
    tb = np.asarray(Image.open(C.tex_path(W, "base")).convert("RGB")).astype(np.float32) / 255
    trm = np.asarray(Image.open(C.tex_path(W, "rm")).convert("RGB")).astype(np.float32) / 255
    S = tb.shape[0]

    def samp(tex, uv, r=3):
        x = np.clip((uv[:, 0] * (S - 1)).astype(int), r, S - 1 - r)
        y = np.clip((uv[:, 1] * (S - 1)).astype(int), r, S - 1 - r)
        acc = 0
        for dx in (-r, 0, r):
            for dy in (-r, 0, r):
                acc = acc + tex[y + dy, x + dx]
        return acc / 9

    def patch(loop, faces_mask, Lb, vuv):
        Lp = np.array(loop)
        P = Pw[Lp]
        n = len(Lp)
        c = P.mean(0)
        _, _, Vt = np.linalg.svd(P - c)
        Q = (P - c) @ Vt[:2].T
        poly = Path(Q)
        el = np.median(np.linalg.norm(np.roll(Q, -1, 0) - Q, axis=1))
        h = el * 1.6
        lo, hi = Q.min(0), Q.max(0)
        gx, gy = np.meshgrid(np.arange(lo[0] + h / 2, hi[0], h), np.arange(lo[1] + h / 2, hi[1], h * 0.866))
        gx = gx + (np.arange(gx.shape[0])[:, None] % 2) * h / 2
        G = np.c_[gx.ravel(), gy.ravel()]
        G = G[poly.contains_points(G)] if len(G) else G
        if len(G):
            d, _ = cKDTree(Q).query(G)
            G = G[d > h * 0.6]
        Q2 = np.r_[Q, G]
        tri = Delaunay(Q2).simplices
        tri = tri[poly.contains_points(Q2[tri].mean(1))]
        m = len(G)
        allP = np.zeros((n + m, 3))
        allP[:n] = P
        Lii = Lib = None
        if m:
            e = np.r_[tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]
            A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n + m, n + m))
            A = ((A + A.T) > 0).astype(float).tocsr()
            Lp_ = sp.diags(np.asarray(A.sum(1)).ravel()) - A
            Lii, Lib = Lp_[n:, n:].tocsc(), Lp_[n:, :n]
            for k in range(3):
                allP[n:, k] = spsolve(Lii, -Lib @ P[:, k])
        cb = samp(tb, vuv[Lp])
        rb = samp(trm, vuv[Lp])
        if Lb == 0 and cfg["body_patch"] == "dark":
            lum = cb.mean(1)
            dk = lum <= np.median(lum)
            cb = np.tile(np.median(cb[dk], 0), (n, 1))
            rb = np.tile(np.median(rb[dk], 0), (n, 1))
        col = np.zeros((n + m, 3))
        rmv = np.zeros((n + m, 3))
        col[:n], rmv[:n] = cb, rb
        if m:
            for k in range(3):
                col[n:, k] = spsolve(Lii, -Lib @ cb[:, k])
                rmv[n:, k] = spsolve(Lii, -Lib @ rb[:, k])
        # orientation: the patch must hold the mesh's loop half-edges reversed
        Fm = F[faces_mask]
        nvv = Pw.shape[0]
        hs = set((np.concatenate([Fm[:, [0, 1]], Fm[:, [1, 2]], Fm[:, [2, 0]]]) @ np.array([nvv, 1])).tolist())
        fwd = sum((int(Lp[i]) * nvv + int(Lp[(i + 1) % n])) in hs for i in range(n))
        pe = set()
        for t in tri:
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                if a < n and b < n:
                    pe.add((a, b))
        same = sum(((i, (i + 1) % n) in pe) for i in range(n))
        rev = sum((((i + 1) % n, i) in pe) for i in range(n))
        if (fwd >= n / 2 and same > rev) or (fwd < n / 2 and rev > same):
            tri = tri[:, ::-1]
        return Lp, allP[n:], tri, col, rmv

    out = {}
    for Lb, nm in enumerate(names):
        mask = lab == Lb
        if not mask.any():
            out[nm] = []
            continue
        vuv = np.zeros((Pw.shape[0], 2), np.float32)
        vuv[inv[I[mask].ravel()]] = UV[I[mask].ravel()]
        res = []
        for lp in loops_of(F, Pw.shape[0], mask):
            if len(lp) < 10:
                continue
            r = patch(lp, mask, Lb, vuv)
            res.append(r)
            print("[patch] %s: loop %d, %d inner points, %d tris, colour %s" % (nm, len(lp), len(r[1]), len(r[2]), (r[3].mean(0) * 255).round()))
        out[nm] = res
    pickle.dump(out, open(os.path.join(W, "patches.pkl"), "wb"))
    print("[patch] saved", {k: len(v) for k, v in out.items()})


main()
