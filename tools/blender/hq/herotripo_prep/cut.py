"""Step 3 (numpy): cut the props out of the fused Tripo mesh -> labels.npz (per Tripo face: 0 body, k the k-th prop of
the config (1-based), 255 dropped).

    python3 cut.py -- --hero ugo [--only sling]        (then: look.py -- --hero ugo --labels)

Each prop in cfg["props"] (in order) is a minimum cut on the face graph inside its "region" box (game units, Tripo
pose: read the coordinates off look.py's grids). Cutting is cheap across concave creases (where a prop was fused onto
the body, e.g. a fist round a grip) and dear across smooth surface, so the cut runs round the prop where it meets the
body. Keys:
  region:  [[x0,x1],[y0,y1],[z0,z1]]: everything the cut may give to the prop (the prop lies inside, with a margin);
  seeds:   shapes (boxes, {"ball": {"c": .., "r": ..}}, each with an optional "col": {"min": rgb, "max": rgb} test on
           the Tripo base colour) that surely belong to the prop;
  sinks:   shapes that surely do not (default: none). The region's skin (faces within `margin`, default 0.012, of the
           region box's faces) is always a sink, so the region must hold the whole prop with room to spare;
  within:  cut from another prop's faces instead of the body (e.g. the stone out of the sling's pouch); its skin is
           then not a sink;
  drop:    true: the piece is removed (patched over), not kept as a prop (e.g. a cable you don't want);
  keep:    "largest" (default: only the prop's largest connected piece, the rest goes back) or "all";
  concave_k: how much cheaper a concave crease is (default 8);
  mode:    "pieces": no cut; the prop is every loose piece of the mesh (not the body's main piece) that a seed touches
           (floating stones, a separate necklace ...); only "seeds" is used.
Small loose islands of the body (< 200 faces) are dropped.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import maximum_flow, breadth_first_order, connected_components
from PIL import Image
import common as C


def mincut(T, region, src, sink, concave_k=8.0, scale=1e6):
    fa, fb, L, N, Cc = T["fa"], T["fb"], T["L"], T["N"], T["C"]
    idx = np.full(len(region), -1)
    rf = np.nonzero(region)[0]
    idx[rf] = np.arange(len(rf))
    m = region[fa] & region[fb]
    a, b = idx[fa[m]], idx[fb[m]]
    na, nb = N[fa[m]], N[fb[m]]
    cosang = np.clip((na * nb).sum(1), -1, 1)
    concave = ((Cc[fb[m]] - Cc[fa[m]]) * na).sum(1) > 1e-9
    w = np.where(concave, concave_k * (1 - cosang), 0.1 * (1 - cosang))
    c = L[m] * np.exp(-w / max(w.mean(), 1e-12))
    ci = np.maximum((c * scale).astype(np.int64), 1)
    n = len(rf)
    S, K = n, n + 1
    big = 2 ** 30
    s_f = np.nonzero(src[rf])[0]
    k_f = np.nonzero(sink[rf] & ~src[rf])[0]
    rows = np.concatenate([a, b, np.full(len(s_f), S), k_f])
    cols = np.concatenate([b, a, s_f, np.full(len(k_f), K)])
    data = np.concatenate([ci, ci, np.full(len(s_f), big), np.full(len(k_f), big)])
    G = sp.csr_matrix((np.minimum(data, 2 ** 31 - 1).astype(np.int32), (rows, cols)), shape=(n + 2, n + 2))
    G.sum_duplicates()
    res = maximum_flow(G, S, K)
    R = (G - res.flow).tocsr()
    R.data = np.where(R.data > 0, 1, 0)
    R.eliminate_zeros()
    reach = breadth_first_order(R, S, directed=True, return_predecessors=False)
    reach = reach[reach < n]
    out = np.zeros(len(region), bool)
    out[rf[reach]] = True
    print("   cut: flow %.4f, %d seed / %d sink faces of %d -> %d" % (res.flow_value / scale, len(s_f), len(k_f), n, out.sum()))
    return out


def comps(T, mask):
    fa, fb = T["fa"], T["fb"]
    idx = np.nonzero(mask)[0]
    m = mask[fa] & mask[fb]
    ii = np.full(len(mask), -1)
    ii[idx] = np.arange(len(idx))
    G = sp.coo_matrix((np.ones(m.sum()), (ii[fa[m]], ii[fb[m]])), shape=(len(idx), len(idx)))
    n, l = connected_components(G, directed=False)
    return idx, l, n


def main():
    hid = C.arg("--hero")
    cfg = C.load_cfg(hid)
    W = C.work_dir(hid)
    xf = C.load_xf(W, fitted=False)
    T = dict(np.load(os.path.join(W, "topo.npz")))
    z = np.load(os.path.join(W, "tripo_np.npz"))
    T["C"] = C.to_game(T["C"], xf)                         # (game units; normals turned with the yaw)
    T["N"] = T["N"] @ C.rotz(xf["yaw"]).T
    T["L"] = T["L"] * xf["s"]
    tex = np.asarray(Image.open(C.tex_path(W, "base")).convert("RGB"))
    S = tex.shape[0]
    uvc = z["UV"][z["I"]].mean(1)
    col = tex[np.clip((uvc[:, 1] * S).astype(int), 0, S - 1), np.clip((uvc[:, 0] * S).astype(int), 0, S - 1)].astype(np.float32) / 255
    Cg = T["C"]
    nf = len(Cg)
    lab = np.zeros(nf, np.uint8)
    names = [p["name"] for p in cfg["props"]]
    for k, p in enumerate(cfg["props"], start=1):
        print("[cut] %s" % p["name"])
        if p.get("mode") == "pieces":            # loose pieces (floating stones ...): every connected piece a seed touches
            src = C.shapes(Cg, p.get("seeds"), col) & (lab == 0)
            idx, l, n = comps(T, lab == 0)
            hit = np.unique(l[np.isin(idx, np.nonzero(src)[0])])
            cnt = np.bincount(l)
            big = np.argmax(cnt)
            hit = hit[hit != big]
            cutm = np.zeros(nf, bool)
            cutm[idx[np.isin(l, hit)]] = True
            lab[cutm] = 255 if p.get("drop") else k
            print("   %d loose pieces (%s faces)" % (len(hit), cnt[hit].tolist()))
            continue
        region = C.box(Cg, p["region"])
        parent = 0
        if p.get("within"):
            parent = names.index(p["within"]) + 1
        region &= lab == parent
        src = region & C.shapes(Cg, p.get("seeds"), col)
        sink = region & C.shapes(Cg, p.get("sinks"), col)
        if not p.get("within"):
            mg = p.get("margin", 0.012)
            (x0, x1), (y0, y1), (z0, z1) = p["region"]
            inner = C.box(Cg, [[x0 + mg, x1 - mg], [y0 + mg, y1 - mg], [z0 + mg, z1 - mg]])
            sink |= region & ~inner
        sink &= ~src
        if src.sum() == 0:
            raise SystemExit("no seed faces for %s" % p["name"])
        cutm = mincut(T, region, src, sink, p.get("concave_k", 8.0))
        if p.get("keep", "largest") == "largest":
            idx, l, n = comps(T, cutm)
            cnt = np.bincount(l)
            cutm[idx[l != np.argmax(cnt)]] = False
            print("   %d pieces, kept the largest (%d faces; others %s)" % (n, cnt.max(), sorted(cnt)[-6:-1]))
        lab[cutm] = 255 if p.get("drop") else k
        P = Cg[cutm]
        print("   %s: %d faces, bbox %s .. %s" % (p["name"], cutm.sum(), P.min(0).round(3), P.max(0).round(3)))
    idx, l, n = comps(T, lab == 0)
    cnt = np.bincount(l)
    small = cnt[l] < 200
    lab[idx[small]] = 255
    print("[cut] body: %d pieces, the largest %d faces; %d faces in %d pieces under 200 faces dropped; kept pieces %s" % (
        n, cnt.max(), small.sum(), (cnt < 200).sum(), sorted(cnt[cnt >= 200])[::-1][:8]))
    np.savez_compressed(os.path.join(W, "labels.npz"), lab=lab, names=np.array(["body"] + names))
    print("[cut] counts", {nm: int((lab == i).sum()) for i, nm in enumerate(["body"] + names)}, "dropped", int((lab == 255).sum()))


main()
