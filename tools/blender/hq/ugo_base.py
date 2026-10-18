"""Ugo's hero dais: a grassy mound with a carved two-tier stone dais (ring of amber stones set in its top, red
ochre zigzags round its sides), two standing stones painted with spirals behind him, boulders, a pile of sling
stones and pebbles (distance fields) + grass blades and flowers (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b

TOP_Z = 0.4             # dais top = where Ugo's feet stand
STAND = v3((0.0, 0.03, TOP_Z))
GROUND_R = 1.3
GROUND_TOP = 0.16
TIER1 = (0.94, 0.27)    # lower tier radius, top
TIER2 = (0.76, TOP_Z)   # upper tier radius, top
RING_R = 0.6
PAINT = 5
MENHIRS = [((-0.68, 0.62), 0.98, 0.2, 3, 0.1), ((0.72, 0.55), 0.8, 0.19, 7, 0.14)]   # (xy, height, radius, seed, lean)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.035) * np.sin(a * 5 + 0.7) + F(0.02) * np.sin(a * 11 + 2.0) + F(0.02) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.05) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.09), 0), np.maximum(dz + F(0.09), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.09), dz + F(0.09)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.09)
    fd.add(Func(disc, (-1.5, -1.5, -0.25), (1.5, 1.5, 0.35),
                disp=lambda P: F(0.008) * NOISE(P * F(7)) + F(0.004) * NOISE(P * F(23)), disp_amp=0.014), 0.0)
    return fd


def _tier(r, z0, z1, rr, seed):
    """Round slab with chiselled facets on its rim and a softly bevelled top edge."""
    nf = 18
    rs = np.random.RandomState(seed)
    offs = rs.uniform(-0.012, 0.012, nf)
    def fn(P):
        rad = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        k = np.floor((a + np.pi) / (2 * np.pi) * nf).astype(np.int64) % nf
        ac = (k + 0.5) / nf * 2 * np.pi - np.pi
        facet = rad * np.cos(a - ac) - (F(r) + offs[k].astype(F))          # flat facets round the rim
        dz = np.maximum(P[:, 2] - F(z1), F(z0) - P[:, 2])
        q = np.stack([np.maximum(facet + F(rr), 0), np.maximum(dz + F(rr), 0)], 1)
        return np.minimum(np.maximum(facet + F(rr), dz + F(rr)), 0) + np.sqrt((q ** 2).sum(1)) - F(rr)
    e = r + 0.05
    return Func(fn, (-e, -e, z0 - 0.05), (e, e, z1 + 0.05), disp=lambda P: F(0.004) * NOISE(P * F(9)) + F(0.002) * NOISE(P * F(30)),
                disp_amp=0.007)


def zigzag(P, r, zc, amp, n, w):
    """Distance to a zigzag line painted round a cylinder of radius r at height zc."""
    a = np.arctan2(P[:, 1], P[:, 0])
    x = a * F(n / (2 * math.pi))
    tri = F(2) * np.abs(F(2) * (x - np.floor(x + F(0.5)))) - F(1)
    rad = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
    return np.maximum(np.abs(P[:, 2] - (F(zc) + F(amp) * tri)) - F(w), np.abs(rad - F(r)) - F(0.06))


def dais_field():
    fd = Field("Dais")
    fd.add(_tier(TIER1[0], 0.02, TIER1[1], 0.035, 3), 0.0)
    fd.add(_tier(TIER2[0], TIER1[1] - 0.04, TIER2[1], 0.03, 5), 0.015)
    # ring groove for the amber stones
    fd.sub(Torus((0, 0, TOP_Z + 0.006), RING_R, 0.036), 0.006)
    # cracks and chips
    rs = np.random.RandomState(14)
    for i in range(6):
        a0 = rs.uniform(0, 2 * math.pi)
        r0 = TIER1[0] if i % 2 else TIER2[0]
        z0 = (TIER1[1] if i % 2 else TIER2[1]) - 0.01
        p0 = v3((math.cos(a0) * r0, math.sin(a0) * r0, z0))
        pts = [p0]
        for j in range(3):
            pts.append(pts[-1] + v3((rs.uniform(-0.03, 0.03), rs.uniform(-0.03, 0.03), -0.035)))
        fd.sub(Chain(pts, [0.011, 0.009, 0.007, 0.003], k=0.004), 0.006)
    # red ochre zigzags painted round both tiers, little sun dots on the top
    fd.paint(Func(lambda P: zigzag(P, TIER1[0], (0.06 + TIER1[1]) / 2 + 0.01, 0.04, 22, 0.013), (-1.1, -1.1, 0.0), (1.1, 1.1, 0.4)), PAINT)
    fd.paint(Func(lambda P: zigzag(P, TIER2[0], (TIER1[1] + TIER2[1]) / 2 - 0.005, 0.03, 18, 0.011), (-0.9, -0.9, 0.2), (0.9, 0.9, 0.5)), PAINT)
    for i in range(10):
        a = i * 2 * math.pi / 10 + 0.31
        c = v3((math.cos(a) * 0.69, math.sin(a) * 0.69, TOP_Z))
        fd.paint(Func(lambda P, c=c: np.maximum(np.sqrt((P[:, 0] - F(c[0])) ** 2 + (P[:, 1] - F(c[1])) ** 2) - F(0.018), np.abs(P[:, 2] - F(TOP_Z)) - F(0.03)),
                      c - 0.05, c + 0.05), PAINT)
    return fd


def amber_field():
    fd = Field("Amber")
    for i in range(26):
        a = i * 2 * math.pi / 26
        c = v3((math.cos(a) * RING_R, math.sin(a) * RING_R, TOP_Z - 0.004))
        fd.add(Ellipsoid(c, (0.036, 0.04, 0.026), R=euler(0, 0, a)), 0.0)
    return fd


def menhir_axis(i):
    (x, y), h, r, seed, lean = MENHIRS[i]
    base = v3((x, y, GROUND_TOP - 0.05))
    top = base + norm(v3((math.copysign(lean, x), lean * 0.6, 1.0))) * h
    return base, top


def rocks_field():
    fd = Field("Rocks")
    for i, ((x, y), h, r, seed, lean) in enumerate(MENHIRS):
        base, top = menhir_axis(i)
        ax = norm(top - base)
        c = (base + top) / 2
        R = rot_from_axes(z_axis=ax, y_axis=(0, 1, 0)) @ euler(0, 0, -0.35 * math.copysign(1, x))
        st = Stone(c, h * 0.5, seed=seed, cuts=15, squash=(r * 2.1 / h, r * 1.45 / h, 1.0), soft=0.028, depth=(0.72, 0.92), R=R, noise=0.02)
        fd.add(st, 0.0)
    # boulders round the foot of the dais
    for i, (c, r, s) in enumerate((((-0.98, -0.28, 0.17), 0.15, 41), ((1.0, -0.12, 0.17), 0.13, 43), ((-0.2, 0.98, 0.17), 0.14, 45),
                                    ((0.3, 1.02, 0.16), 0.1, 47), ((-1.02, 0.42, 0.16), 0.11, 49), ((1.08, 0.36, 0.16), 0.09, 51))):
        fd.add(Stone(c, r, seed=s, cuts=10, squash=(1.0, 0.95, 0.75), soft=0.06, noise=0.02), 0.03)
    # painted spirals on the standing stones (front faces)
    for i in range(len(MENHIRS)):
        base, top = menhir_axis(i)
        c = lerp(base, top, 0.6)
        fd.paint(Func(lambda P, c=c: spiral(P, c), c - 0.3, c + 0.3), PAINT)
    return fd


def spiral(P, c, turns=2.4, r1=0.085, w=0.011):
    """Distance to an Archimedean spiral drawn in the x/z plane (seen from the front), projected along y."""
    x = P[:, 0] - F(c[0])
    z = P[:, 2] - F(c[2])
    r = np.sqrt(x * x + z * z)
    th = np.arctan2(z, x)
    k = F(r1 / (turns * 2 * math.pi))
    # nearest arm: r = k * (th + 2 pi n)
    n = np.round((r / k - th) / F(2 * math.pi))
    n = np.clip(n, 0, turns)
    rr = k * (th + F(2 * math.pi) * n)
    d = np.abs(r - rr)
    d = np.where(r > F(r1 + w), r - F(r1), d)
    depth = np.abs(P[:, 1] - F(c[1])) - F(0.35)
    return np.maximum(d - F(w), depth)


def ammo_field():
    fd = Field("AmmoStones")
    rs = np.random.RandomState(9)
    pile = v3((0.5, -0.62, TIER1[1]))
    for i, (dx, dy, dz, r) in enumerate(((0.0, 0.0, 0.05, 0.06), (0.09, 0.03, 0.045, 0.055), (0.045, 0.06, 0.04, 0.05),
                                          (0.04, 0.02, 0.12, 0.052), (-0.07, 0.05, 0.045, 0.05))):
        fd.add(Stone(pile + v3((dx, dy, dz)), r, seed=60 + i, noise=0.05, squash=(1, 1, 0.85)), 0.004)
    return fd


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(13)
    n = 0
    while n < 14:
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(1.0, 1.25)
        p = v3((math.cos(a) * r, math.sin(a) * r, GROUND_TOP + 0.03))
        if any(np.linalg.norm(p[:2] - np.array(m[0])) < 0.3 for m in MENHIRS):
            continue
        fd.add(Stone(p, rs.uniform(0.028, 0.05), seed=100 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


# ---------------------------------------------------------------------------------------- direct geometry
def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.05 * max(0.0, 1 - (r / GROUND_R) ** 2)


def grass_geometry(seed=17):
    """Grass tufts round the dais (between the boulders and standing stones)."""
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    avoid = [((0.0, 0.0), TIER1[0] + 0.04)] + [(m[0], m[2] + 0.12) for m in MENHIRS]
    tufts = []
    tries = 0
    while len(tufts) < 34 and tries < 6000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(TIER1[0] + 0.06, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - np.array(q)) < rr for q, rr in avoid):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.14 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(8, 13)
        big = 0.7 + 0.45 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.05)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.15, 0.45) + v3((0, 0, 1)))
            L = rs.uniform(0.13, 0.24) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.042), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=23):
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 8 and tries < 2000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(TIER1[0] + 0.08, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - np.array(m[0])) < 0.28 for m in MENHIRS):
            continue
        if any(np.linalg.norm(c[:2] - s[0][:2]) < 0.2 for s in spots):
            continue
        spots.append((c, rs.randint(0, 3)))
    for c, kind in spots:
        base = v3((c[0], c[1], ground_height(c[0], c[1]) - 0.01))
        h = rs.uniform(0.1, 0.15)
        top = base + v3((rs.uniform(-0.02, 0.02), rs.uniform(-0.02, 0.02), h))
        sv, sf, _ = _b.blade_mesh(base, top - base, h, 0.012, (0, 0, 0), segs=2)
        out.append((sv, sf, 0, kind))
        n = 5
        pr = 0.035
        tilt = norm(v3((rs.uniform(-0.3, 0.3), rs.uniform(-0.5, -0.1), 1.0)))
        R = rot_from_axes(z_axis=tilt)
        pv, pf = [], []
        for k in range(n):
            a = 2 * math.pi * k / n
            dirk = R @ v3((math.cos(a), math.sin(a), 0.12))
            sidek = R @ v3((-math.sin(a), math.cos(a), 0))
            b0 = len(pv)
            pv += [top + tilt * 0.004, top + dirk * pr * 0.55 + sidek * pr * 0.42, top + dirk * pr, top + dirk * pr * 0.55 - sidek * pr * 0.42]
            pf.append((b0, b0 + 1, b0 + 2, b0 + 3))
        out.append((pv, pf, 1, kind))
        cv = [top + R @ v3((math.cos(2 * math.pi * k / 6) * 0.012, math.sin(2 * math.pi * k / 6) * 0.012, 0.008)) for k in range(6)]
        cv.append(top + R @ v3((0, 0, 0.016)))
        out.append((cv, [(k, (k + 1) % 6, 6) for k in range(6)], 2, kind))
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Dais", dais_field(), 0.006), ("Amber", amber_field(), 0.003),
            ("Rocks", rocks_field(), 0.006), ("AmmoStones", ammo_field(), 0.004), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Dais", "Rocks")
LOW_TARGETS = {"Ground": 1300, "Dais": 2600, "Amber": 700, "Rocks": 2400, "AmmoStones": 420, "Pebbles": 380}
FLAME_PIVOT = None
MAT_OVERRIDES = {"Rocks": ("stone", {"name": "HQ_PaintedRock", "moss": True, "paint": True})}
GLOW = {"Amber": ((1.0, 0.64, 0.14), 1.4)}        # the hero ring: amber stones that glow in game


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and 0.08 < c.z < 0.26 and TIER1[0] + 0.03 < r < GROUND_R + 0.05
