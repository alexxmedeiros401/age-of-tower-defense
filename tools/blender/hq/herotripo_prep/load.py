"""Step 2 (numpy): the Tripo GLB -> tripo_np.npz, topo.npz, tex_{base,rm,normal}, xf.json in the work folder.

    python3 load.py -- --hero ugo

- welds the Tripo mesh (its vertices are split along UV seams) and builds the face graph (pairs of faces sharing an
  edge, edge lengths, face normals, centres, areas) that the cuts run on;
- finds which way the model faces (cfg "yaw": "auto"): the arm span is the wider horizontal extent at hand height,
  and the toes stick out in front of the ankles; then the yaw about +Z that turns him to face -Y (the rig's front);
- a first Tripo -> game transform (xf.json): scaled to the old body's height (soles to the top of the body), soles on
  the old soles, the hips' middle on the old hips' middle. The fit (fit.py) refines it.
Every later step works in game units (CavemanRig's armature space) through this transform.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import common as C


def auto_yaw(P):
    """Degrees about +Z that turn the model (Blender axes, Z up) to face -Y."""
    z = P[:, 2]
    z0, h = z.min(), z.max() - z.min()
    s = P[(z > z0 + 0.38 * h) & (z < z0 + 0.6 * h)]
    ext = s[:, :2].max(0) - s[:, :2].min(0)
    lat = int(np.argmax(ext))                       # the arm span's axis (0: x, 1: y)
    fa = 1 - lat                                    # the facing axis
    feet = P[z < z0 + 0.035 * h]
    ank = P[(z > z0 + 0.07 * h) & (z < z0 + 0.12 * h)]
    # each foot on its own (left / right of the middle): toes beyond the ankle along the facing axis
    mid = np.median(feet[:, lat])
    d = []
    for left in (True, False):
        fs = feet[(feet[:, lat] < mid) == left]
        an = ank[(ank[:, lat] < mid) == left]
        if len(fs) and len(an):
            d.append((np.percentile(fs[:, fa], 98) + np.percentile(fs[:, fa], 2)) / 2 - np.median(an[:, fa]))
    sign = np.sign(np.sum(d)) or 1.0
    front = np.zeros(3)
    front[fa] = sign
    # yaw that maps `front` onto -Y
    ang = np.degrees(np.arctan2(-1.0, 0.0) - np.arctan2(front[1], front[0]))
    ang = (ang + 360) % 360
    print("[load] arm span along %s (extent %s), toes toward %s%s (foot asymmetry %s) -> yaw %.0f" % (
        "xy"[lat], ext.round(3), "+-"[int(sign < 0)], "xy"[fa], np.round(d, 4), ang))
    return float(round(ang / 90.0) * 90.0 % 360)


def main():
    hid = C.arg("--hero")
    cfg = C.load_cfg(hid)
    W = C.work_dir(hid)
    PB, UV, I = C.read_glb(cfg["tripo"], W)
    q = np.round(PB.astype(np.float32).astype(np.float64) * 1e5).astype(np.int64)
    _, inv = np.unique(q, axis=0, return_inverse=True)
    inv = inv.ravel()
    np.savez(os.path.join(W, "tripo_np.npz"), PB=PB.astype(np.float32), UV=UV, I=I.astype(np.int32), inv=inv.astype(np.int32))
    n = inv.max() + 1
    Pw = np.zeros((n, 3))
    Pw[inv] = PB.astype(np.float32)
    F = inv[I]
    print("[load] %d verts (%d welded), %d faces, bbox %s %s" % (len(PB), n, len(F), Pw.min(0).round(3), Pw.max(0).round(3)))
    # ---- the face graph
    nf = len(F)
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    fe = np.tile(np.arange(nf), 3)
    e.sort(1)
    key = e[:, 0] * n + e[:, 1]
    order = np.argsort(key, kind="stable")
    ks = key[order]
    same = np.nonzero(ks[1:] == ks[:-1])[0]
    fa, fb = fe[order[same]], fe[order[same + 1]]
    ev = e[order[same]]
    _, cnt = np.unique(ks, return_counts=True)
    print("[load] edges %d, face pairs %d, non-manifold edges %d, boundary edges %d" % (len(cnt), len(fa), (cnt > 2).sum(), (cnt == 1).sum()))
    v0, v1, v2 = Pw[F[:, 0]], Pw[F[:, 1]], Pw[F[:, 2]]
    N = np.cross(v1 - v0, v2 - v0)
    A = np.linalg.norm(N, axis=1)
    N /= np.maximum(A, 1e-20)[:, None]
    Cc = (v0 + v1 + v2) / 3
    L = np.linalg.norm(Pw[ev[:, 0]] - Pw[ev[:, 1]], axis=1)
    # ---- facing, scale, offset
    yaw = auto_yaw(Pw) if cfg["yaw"] == "auto" else float(cfg["yaw"])
    o = np.load(os.path.join(W, "old.npz"))
    V, T, Tp = o["V"], o["T"], o["Tprop"]
    vb = np.unique(T[Tp < 0])
    Vb = V[vb]
    R = C.rotz(yaw)
    Q = Pw @ R.T
    h_old = Vb[:, 2].max() - Vb[:, 2].min()
    h_new = Q[:, 2].max() - Q[:, 2].min()
    s = float(cfg["scale"]) if cfg["scale"] != "auto" else h_old / h_new
    Q = Q * s
    def hips(X):
        z0, h = X[:, 2].min(), X[:, 2].max() - X[:, 2].min()
        sl = X[(X[:, 2] > z0 + 0.42 * h) & (X[:, 2] < z0 + 0.5 * h)]
        return np.r_[np.median(sl[:, :2], 0), z0]
    t = hips(Vb) - hips(Q)
    xf = dict(yaw=yaw, s=s, t=t.tolist())
    json.dump(xf, open(os.path.join(W, "xf.json"), "w"), indent=1)
    print("[load] xf: yaw %.0f, scale %.4f (old body %.3f tall, Tripo %.3f), offset %s" % (yaw, s, h_old, h_new, np.round(t, 4)))
    np.savez(os.path.join(W, "topo.npz"), Pw=Pw, F=F, fa=fa, fb=fb, L=L, N=N, C=Cc, A=A / 2)


main()
