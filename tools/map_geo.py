"""Map geometry shared by the ground renderers: the visible road (minus rift hops and tunnel interiors), lanes and
tunnels, measured on a pixel grid. Same rules as tools/gen_ground.py (which keeps its own frozen copy).

World coverage of a ground texture: x in [X0, X0+W], z in [Z0, Z0+H]; image row 0 = z = Z0 (the top of the screen).
"""
import json
import numpy as np

X0, Z0, W, H = -21.0, -13.0, 40.0, 26.0
TUN_MOUTH = 0.9


class Grid:
    def __init__(self, px):
        self.px = px
        self.w, self.h = int(W * px), int(H * px)
        xs = X0 + (np.arange(self.w) + 0.5) / px
        zs = Z0 + (np.arange(self.h) + 0.5) / px
        self.X, self.Z = np.meshgrid(xs, zs)

    def poly_dist(self, polylines, margin=3.0, signed=False):
        """Distance to the nearest polyline, distance along it, and (signed) the side of the road."""
        X, Z, PX = self.X, self.Z, self.px
        dd = np.full(X.shape, 1e9)
        along = np.zeros(X.shape)
        side = np.zeros(X.shape) if signed else None
        for pts in polylines:
            pts = np.array(pts, dtype=np.float64)
            cum = 0.0
            for i in range(1, len(pts)):
                a, b = pts[i - 1], pts[i]
                ab = b - a
                L = np.hypot(*ab)
                if L < 1e-9:
                    continue
                j0 = max(0, int((min(a[0], b[0]) - margin - X0) * PX))
                j1 = min(self.w, int((max(a[0], b[0]) + margin - X0) * PX) + 1)
                i0 = max(0, int((min(a[1], b[1]) - margin - Z0) * PX))
                i1 = min(self.h, int((max(a[1], b[1]) + margin - Z0) * PX) + 1)
                if j1 > j0 and i1 > i0:
                    Xs, Zs = X[i0:i1, j0:j1], Z[i0:i1, j0:j1]
                    t = np.clip(((Xs - a[0]) * ab[0] + (Zs - a[1]) * ab[1]) / (L * L), 0, 1)
                    px, pz = Xs - (a[0] + t * ab[0]), Zs - (a[1] + t * ab[1])
                    d = np.hypot(px, pz)
                    sub = dd[i0:i1, j0:j1]
                    closer = d < sub
                    sub[closer] = d[closer]
                    al = along[i0:i1, j0:j1]
                    al[closer] = (cum + t * L)[closer]
                    if signed:
                        sd_ = side[i0:i1, j0:j1]
                        sd_[closer] = ((ab[0] * pz - ab[1] * px) / L)[closer]
                cum += L
        return (dd, along, side) if signed else (dd, along)


def spec_cum(sp):
    pts, rf = sp["pts"], set(sp.get("rift", []))
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + (0.0 if i in rf else float(np.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))))
    return cum


def sub_polylines(sp, d0, d1):
    pts, rf, cum = sp["pts"], set(sp.get("rift", [])), spec_cum(sp)
    out, cur = [], []
    for i in range(1, len(pts)):
        if i in rf:
            if len(cur) > 1:
                out.append(cur)
            cur = []
            continue
        c0, c1 = cum[i - 1], cum[i]
        lo, hi = max(c0, d0), min(c1, d1)
        if hi <= lo or c1 - c0 < 1e-9:
            if c0 >= d1 and len(cur) > 1:
                out.append(cur)
                cur = []
            continue
        a, b = np.array(pts[i - 1], float), np.array(pts[i], float)
        pa = a + (b - a) * (lo - c0) / (c1 - c0)
        pb = a + (b - a) * (hi - c0) / (c1 - c0)
        if not cur or np.hypot(*(np.array(cur[-1]) - pa)) > 1e-6:
            if len(cur) > 1:
                out.append(cur)
            cur = [list(pa)]
        cur.append(list(pb))
    if len(cur) > 1:
        out.append(cur)
    return out


def visible_legs(sp):
    L_ = spec_cum(sp)[-1]
    gaps = sorted((spec_cum(sp)[z["a"]] + TUN_MOUTH, spec_cum(sp)[z["b"]] - TUN_MOUTH)
                  for z in sp.get("zones", []) if z["k"] == "tunnel")
    gaps = [g for g in gaps if g[1] > g[0]]
    out, d = [], 0.0
    for g0, g1 in gaps:
        out += sub_polylines(sp, d, g0)
        d = g1
    out += sub_polylines(sp, d, L_ + 1)
    return out


def load(map_id, root):
    m = json.load(open("%s/data/map_%s.json" % (root, map_id)))
    specs = [p if isinstance(p, dict) else {"pts": p} for p in (m["paths"] if "paths" in m else [m["path"]])]
    return m, specs


def zones(specs):
    zf = {"fast": [], "slow": [], "tunnel": []}
    for sp in specs:
        cum = spec_cum(sp)
        for z in sp.get("zones", []):
            d0, d1 = cum[z["a"]], cum[z["b"]]
            if z["k"] == "tunnel":
                if d1 - d0 > 2 * TUN_MOUTH:
                    zf["tunnel"] += sub_polylines(sp, d0 + TUN_MOUTH, d1 - TUN_MOUTH)
            else:
                zf[z["k"]] += sub_polylines(sp, d0, d1)
    return zf
