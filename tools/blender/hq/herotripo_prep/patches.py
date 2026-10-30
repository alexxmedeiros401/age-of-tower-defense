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
    xf_s = C.load_xf(W, fitted=False)["s"]

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

    def bridge(l1, l2, faces_mask, vuv, rings_per_m=60.0):
        """A tube between two boundary loops of one piece (a staff cut in two where it went through a fist): rings
        lofted between the loops (each resampled by arc length; loop 2 reversed and turned to line up with loop 1),
        colours interpolated between the two rims."""
        L1, L2 = np.array(l1), np.array(l2)[::-1]
        P1, P2 = Pw[L1], Pw[L2]
        def arc(P):
            d = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
            return np.r_[0, np.cumsum(d)[:-1]] / d.sum()
        t1, t2 = arc(P1), arc(P2)
        def at(P, t, q):
            q = q % 1.0
            j = np.searchsorted(t, q, side="right") - 1
            k = (j + 1) % len(P)
            tn = np.where(k == 0, 1.0, t[k])
            f = (q - t[j]) / np.maximum(tn - t[j], 1e-12)
            return P[j] * (1 - f)[:, None] + P[k] * f[:, None]
        M = max(len(L1), len(L2))
        q = np.arange(M) / M
        best = None
        for off in np.linspace(0, 1, 90, endpoint=False):
            d = np.linalg.norm(at(P1, t1, q) - at(P2, t2, q + off) - (P1.mean(0) - P2.mean(0)), axis=1).sum()
            if best is None or d < best[0]:
                best = (d, off)
        off = best[1]
        t2s = (t2 - off) % 1.0                              # loop 2's own vertices, in loop 1's parameter
        length = np.linalg.norm(P1.mean(0) - P2.mean(0))
        K = max(2, int(round(length * xf_s * rings_per_m)))
        n1, n2 = len(L1), len(L2)
        nb = n1 + n2
        # rings: index lists into [L1, L2, inner...]; inner rings M points each at q
        ring_idx = [list(range(n1))]
        ring_par = [t1]
        inner = []
        for r in range(1, K):
            a = r / K
            X = at(P1, t1, q) * (1 - a) + at(P2, t2, q + off) * a
            ring_idx.append(list(range(nb + len(inner) * M, nb + (len(inner) + 1) * M)))
            ring_par.append(q)
            inner.append(X)
        ring_idx.append(list(range(n1, n1 + n2)))
        o2 = np.argsort(t2s)
        ring_idx[-1] = [n1 + i for i in o2]
        ring_par.append(np.sort(t2s))
        tris = []
        for ra, rb, pa, pb in zip(ring_idx[:-1], ring_idx[1:], ring_par[:-1], ring_par[1:]):
            i = j = 0
            na_, nb_ = len(ra), len(rb)
            while i < na_ or j < nb_:
                qa = pa[i % na_] + (i // na_)
                qb = pb[j % nb_] + (j // nb_)
                if j >= nb_ or (i < na_ and qa + (pa[(i + 1) % na_] + ((i + 1) // na_) - qa) / 2 <= qb + (pb[(j + 1) % nb_] + ((j + 1) // nb_) - qb) / 2):
                    tris.append((ra[i % na_], ra[(i + 1) % na_], rb[j % nb_]))
                    i += 1
                else:
                    tris.append((ra[i % na_], rb[(j + 1) % nb_], rb[j % nb_]))
                    j += 1
        tris = np.array(tris)
        Pin = np.concatenate(inner) if inner else np.zeros((0, 3))
        Lr = np.r_[L1, L2]
        cb1, rb1 = samp(tb, vuv[L1]), samp(trm, vuv[L1])
        cb2, rb2 = samp(tb, vuv[L2]), samp(trm, vuv[L2])
        col = [cb1, cb2]
        rmv = [rb1, rb2]
        c1, c2 = cb1.mean(0), cb2.mean(0)
        r1_, r2_ = rb1.mean(0), rb2.mean(0)
        for r in range(1, K):
            a = r / K
            col.append(np.tile(c1 * (1 - a) + c2 * a, (M, 1)))
            rmv.append(np.tile(r1_ * (1 - a) + r2_ * a, (M, 1)))
        col, rmv = np.concatenate(col), np.concatenate(rmv)
        # orientation: the tube must hold loop 1's mesh half-edges reversed
        Fm = F[faces_mask]
        nvv = Pw.shape[0]
        hs = set((np.concatenate([Fm[:, [0, 1]], Fm[:, [1, 2]], Fm[:, [2, 0]]]) @ np.array([nvv, 1])).tolist())
        gl = np.r_[Lr, -1 - np.arange(len(Pin))]
        pe = set()
        for t in tris:
            for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                if a_ < nb and b_ < nb:
                    pe.add((int(gl[a_]), int(gl[b_])))
        clash = sum(((int(a_) // nvv, int(a_) % nvv) in pe) for a_ in hs if (a_ // nvv) in set(L1.tolist()) and (a_ % nvv) in set(L1.tolist()))
        if clash > len(L1) / 2:
            tris = tris[:, ::-1]
        return Lr, Pin, tris, col, rmv

    out = {}
    for Lb, nm in enumerate(names):
        mask = lab == Lb
        if not mask.any():
            out[nm] = []
            continue
        vuv = np.zeros((Pw.shape[0], 2), np.float32)
        vuv[inv[I[mask].ravel()]] = UV[I[mask].ravel()]
        res = []
        lps = [lp for lp in loops_of(F, Pw.shape[0], mask) if len(lp) >= 10]
        pc = cfg["props"][Lb - 1] if Lb > 0 else {}
        if pc.get("bridge") and len(lps) >= 2:
            lps.sort(key=len, reverse=True)
            # the two loops facing each other across the gap: the nearest pair of loop centres
            cs = [Pw[np.array(l)].mean(0) for l in lps]
            pairs = sorted((np.linalg.norm(cs[i] - cs[j]), i, j) for i in range(len(lps)) for j in range(i + 1, len(lps)))
            _, i, j = pairs[0]
            r = bridge(lps[i], lps[j], mask, vuv)
            res.append(r)
            print("[patch] %s: bridged loops %d and %d (gap %.3f): %d inner points, %d tris" % (nm, len(lps[i]), len(lps[j]), pairs[0][0] * xf_s, len(r[1]), len(r[2])))
            lps = [l for k_, l in enumerate(lps) if k_ not in (i, j)]
        for lp in lps:
            r = patch(lp, mask, Lb, vuv)
            res.append(r)
            print("[patch] %s: loop %d, %d inner points, %d tris, colour %s" % (nm, len(lp), len(r[1]), len(r[2]), (r[3].mean(0) * 255).round()))
        out[nm] = res
    pickle.dump(out, open(os.path.join(W, "patches.pkl"), "wb"))
    print("[patch] saved", {k: len(v) for k, v in out.items()})


main()
