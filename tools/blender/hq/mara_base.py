"""Mara's hero dais: a round dry-stone platform (three courses of rough laid blocks, joints offset course to course,
capped with irregular flagstones) on a grassy mound. A ring of amber stones set in the flagstones glows (the hero
ring); clusters of purple quartz grow from the ground round it and glow too. Behind her: a holed standing stone painted
with a spiral, a balanced cairn; pebbles, grass and flowers."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
from ugo_base import spiral
import base as _b

GROUND_R = 1.3
GROUND_TOP = 0.16
TOP_Z = 0.4                     # flagstone top = where Mara's feet stand
STAND = v3((0.0, 0.03, TOP_Z))
COURSES = [(0.9, 0.05, 0.17, 15, 0.0), (0.875, 0.165, 0.265, 14, 0.5), (0.85, 0.26, 0.345, 16, 0.2)]   # (outer r, z0, z1, n, phase)
CAP_R = 0.86
RING_R = 0.62
PAINT = 5
QUARTZ = [((0.9, -0.72), 9, 11, 1.35), ((-1.04, -0.38), 7, 13, 1.1), ((0.42, 1.04), 6, 17, 1.0), ((-0.4, -1.04), 4, 19, 0.8)]
HOLED = v3((-0.6, 0.98, 0.0))   # holed standing stone (behind her, left)
CAIRN = v3((0.98, 0.48, 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.05 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.035) * np.sin(a * 5 + 1.9) + F(0.02) * np.sin(a * 11 + 0.4) + F(0.02) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.05) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.09), 0), np.maximum(dz + F(0.09), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.09), dz + F(0.09)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.09)
    fd.add(Func(disc, (-1.5, -1.5, -0.25), (1.5, 1.5, 0.35),
                disp=lambda P: F(0.008) * NOISE(P * F(7)) + F(0.004) * NOISE(P * F(23)), disp_amp=0.014), 0.0)
    return fd


class Block(Prim):
    """A rough dry-stone block: a rounded box with chipped corners and a little noise."""

    def __init__(self, c, half, R, seed, chips=5, rr=0.012, noise=0.005):
        super().__init__(c, R, disp_amp=noise)
        rs = np.random.RandomState(seed)
        self.h = v3(half)
        self.rr = rr
        ns, os_ = [], []
        for i in range(chips):
            s = rs.choice([-1.0, 1.0], 3)
            n = norm(s + rs.normal(0, 0.25, 3))
            corner = s * self.h
            ns.append(n)
            os_.append(float(corner @ n) * rs.uniform(0.74, 0.9))
        self.n = np.array(ns, F)
        self.o = np.array(os_, F)
        self.noise = noise
        self.seed = seed
        e = float(np.linalg.norm(self.h)) + rr
        self.bounds_from_local((-e,) * 3, (e,) * 3)

    def sdf(self, P):
        q = self.local(P)
        d3 = np.abs(q) - (self.h.astype(F) - F(self.rr))
        d = np.sqrt((np.maximum(d3, 0) ** 2).sum(1)) + np.minimum(d3.max(1), 0) - F(self.rr)
        for n, o in zip(self.n, self.o):
            d = smax(d, q @ n - o, 0.006)
        if self.noise:
            d = d + F(self.noise) * (NOISE((P + self.seed * 3.7) * F(9)) + F(0.5) * NOISE((P + self.seed) * F(31)))
        return d


def course_blocks():
    """(centre, half extents, R, seed) for every laid block, course by course."""
    out = []
    rs = np.random.RandomState(31)
    for ci, (ro, z0, z1, n, ph) in enumerate(COURSES):
        a_prev = 0.0
        widths = rs.uniform(0.75, 1.25, n)
        widths = widths / widths.sum() * 2 * math.pi
        a = (ph + rs.uniform(-0.1, 0.1)) * 2 * math.pi / n
        for k in range(n):
            w = widths[k]
            ac = a + w / 2
            a += w
            hd = rs.uniform(0.09, 0.13)                                   # radial half-depth
            ht = (ro * math.tan(w / 2)) - rs.uniform(0.008, 0.014)         # tangential half-width (small joint)
            hz = (z1 - z0) / 2 - rs.uniform(0.003, 0.008)
            zc = (z0 + z1) / 2 + rs.uniform(-0.004, 0.004)
            rc = ro - hd + rs.uniform(-0.008, 0.01)
            c = v3((math.cos(ac) * rc, math.sin(ac) * rc, zc))
            tan = v3((-math.sin(ac), math.cos(ac), 0))
            rad = v3((math.cos(ac), math.sin(ac), 0))
            R = np.stack([tan, rad, v3((0, 0, 1))], axis=1) @ euler(rs.uniform(-0.05, 0.05), rs.uniform(-0.06, 0.06), rs.uniform(-0.03, 0.03))
            out.append((c, (ht, hd, hz), R, 400 + ci * 40 + k))
    return out


def _voronoi_cells(seed=7, n=15):
    rs = np.random.RandomState(seed)
    pts = []
    for _ in range(20000):
        if len(pts) == n:
            break
        p = rs.uniform(-CAP_R, CAP_R, 2)
        if np.linalg.norm(p) < CAP_R - 0.05 and all(np.linalg.norm(p - q) > 0.27 for q in pts):
            pts.append(p)
    return np.array(pts, F), rs.uniform(-0.007, 0.007, n).astype(F)


CELLS, CELL_DZ = _voronoi_cells()


def flagstones(P):
    """Irregular flagstones capping the platform: 2D Voronoi cells with open joints, each laid at its own height."""
    xy = P[:, :2]
    d = np.sqrt(((xy[:, None, :] - CELLS[None, :, :]) ** 2).sum(2))
    o = np.argsort(d, axis=1)[:, :2]
    d1 = np.take_along_axis(d, o[:, :1], 1)[:, 0]
    d2 = np.take_along_axis(d, o[:, 1:2], 1)[:, 0]
    edge = (d2 - d1) * F(0.5)
    r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
    a = np.arctan2(P[:, 1], P[:, 0])
    rim = r - (F(CAP_R) + F(0.012) * np.sin(a * 7 + 0.5) + F(0.008) * np.sin(a * 17))
    inside = np.maximum(rim, F(0.008) - edge)
    top = F(TOP_Z) + CELL_DZ[o[:, 0]]
    dz = np.maximum(P[:, 2] - top, F(TOP_Z - 0.065) - P[:, 2])
    rr = F(0.01)
    q = np.stack([np.maximum(inside + rr, 0), np.maximum(dz + rr, 0)], 1)
    return np.minimum(np.maximum(inside + rr, dz + rr), 0) + np.sqrt((q ** 2).sum(1)) - rr


def dais_field():
    fd = Field("Dais")
    # rubble core behind the facing blocks (shows dark in the joints)
    fd.add(Cylinder((0, 0, 0.18), COURSES[-1][0] - 0.06, 0.36), 0.0)
    for c, half, R, seed in course_blocks():
        fd.add(Block(c, half, R, seed), 0.0)
    fd.add(Func(flagstones, (-CAP_R - 0.05, -CAP_R - 0.05, TOP_Z - 0.09), (CAP_R + 0.05, CAP_R + 0.05, TOP_Z + 0.03),
                disp=lambda P: F(0.003) * NOISE(P * F(11)) + F(0.0015) * NOISE(P * F(37)), disp_amp=0.005), 0.0)
    # groove for the amber ring
    fd.sub(Torus((0, 0, TOP_Z + 0.004), RING_R, 0.034), 0.006)
    # ochre spirals painted on four of the flagstones round the ring, and dots on the facing blocks of the top course
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        c = v3((math.cos(a) * 0.74, math.sin(a) * 0.74, TOP_Z))
        fd.paint(Func(lambda P, c=c: _flat_spiral(P, c, 0.07), c - 0.12, c + 0.12), PAINT)
    for c, half, R, seed in course_blocks()[-COURSES[-1][3]:]:
        out = norm(v3((c[0], c[1], 0)))
        p = c + out * (half[1] + 0.004)
        fd.paint(Sphere(p, 0.016), PAINT)
    return fd


def _flat_spiral(P, c, r1, turns=2.2, w=0.009):
    x = P[:, 0] - F(c[0])
    y = P[:, 1] - F(c[1])
    rr = np.sqrt(x * x + y * y)
    th = np.arctan2(y, x)
    k = F(r1 / (turns * 2 * math.pi))
    m = np.clip(np.round((rr / k - th) / F(2 * math.pi)), 0, turns)
    d = np.abs(rr - k * (th + F(2 * math.pi) * m))
    d = np.where(rr > F(r1 + w), rr - F(r1), d)
    return np.maximum(d - F(w), np.abs(P[:, 2] - F(c[2])) - F(0.03))


def amber_field():
    fd = Field("Amber")
    for i in range(20):
        a = i * 2 * math.pi / 20 + 0.08
        c = v3((math.cos(a) * RING_R, math.sin(a) * RING_R, TOP_Z - 0.006))
        fd.add(Ellipsoid(c, (0.04, 0.044, 0.028), R=euler(0, 0, a)), 0.0)
    return fd


class Crystal(Prim):
    """Hexagonal quartz point: six side planes, six tip facets, a flat base far below."""

    def __init__(self, base, axis, length, r, tip, twist=0.0):
        z = norm(axis)
        R = rot_from_axes(z_axis=z) @ euler(0, 0, twist)
        super().__init__(base, R)
        self.L, self.r, self.tip = length, r, tip
        e = max(length, r) + 0.02
        self.bounds_from_local((-r - 0.02, -r - 0.02, -0.02), (r + 0.02, r + 0.02, length + 0.02))
        th = np.arange(6) * math.pi / 3
        self.side = np.stack([np.cos(th), np.sin(th), np.zeros(6)], 1).astype(F)
        tn = np.stack([np.cos(th) * tip, np.sin(th) * tip, np.full(6, r)], 1)
        self.tipn = (tn / np.linalg.norm(tn, axis=1, keepdims=True)).astype(F)

    def sdf(self, P):
        q = self.local(P)
        d = -q[:, 2]
        d = np.maximum(d, (q @ self.side.T).max(1) - F(self.r))
        qt = q - np.array([0, 0, self.L], F)
        d = np.maximum(d, (qt @ self.tipn.T).max(1))
        return d


def quartz_clusters():
    out = []
    for ci, ((x, y), n, seed, size) in enumerate(QUARTZ):
        rs = np.random.RandomState(seed)
        root = v3((x, y, ground_height(x, y) - 0.06))
        out_dir = norm(v3((x, y, 0)))
        for k in range(n):
            ang = rs.uniform(0, 2 * math.pi)
            tilt = 0.12 if k == 0 else rs.uniform(0.35, 0.85)
            d = norm(v3((math.cos(ang) * tilt, math.sin(ang) * tilt, 1.0)) + out_dir * 0.18)
            L = (0.34 if k == 0 else rs.uniform(0.12, 0.26)) * size
            r = (0.05 if k == 0 else rs.uniform(0.024, 0.04)) * (0.6 + 0.4 * size)
            off = v3((math.cos(ang), math.sin(ang), 0)) * (0.0 if k == 0 else rs.uniform(0.02, 0.06))
            out.append((root + off, d, L + 0.06, r, r * rs.uniform(1.4, 2.0), rs.uniform(0, 1)))
    return out


def quartz_field():
    fd = Field("Quartz")
    for base, d, L, r, tip, tw in quartz_clusters():
        fd.add(Crystal(base, d, L, r, tip, tw), 0.0)
    return fd


def holed_frame():
    base = HOLED + v3((0, 0, ground_height(HOLED[0], HOLED[1]) - 0.06))
    face = norm(v3((0.35, -1.0, 0.0)))                                   # its face turned to the camera
    R = rot_from_axes(z_axis=v3((0, 0, 1)), y_axis=face)
    return base, R, face


def rocks_field():
    fd = Field("Rocks")
    base, R, face = holed_frame()
    c = base + v3((0, 0, 0.5))
    # a thick standing disc (squashed along its face normal) with a round hole through it
    disc = Stone(c, 0.42, seed=23, cuts=14, squash=(0.95, 0.36, 1.15), soft=0.08, depth=(0.82, 0.95), R=R, noise=0.025)
    fd.add(disc, 0.0)
    hole_c = c + v3((0, 0, 0.08))
    fd.sub(RoundCone(hole_c - face * 0.3, hole_c + face * 0.3, 0.11, 0.11), 0.03)
    fd.paint(Func(lambda P: _spiral_face(P, hole_c, face, 0.25), hole_c - 0.4, hole_c + 0.4), PAINT)
    # cairn: flat river stones balanced in a stack, largest at the bottom
    z = ground_height(CAIRN[0], CAIRN[1]) - 0.02
    rs = np.random.RandomState(5)
    for i, (rr, hh) in enumerate(((0.17, 0.07), (0.14, 0.06), (0.115, 0.055), (0.09, 0.05), (0.065, 0.045), (0.045, 0.04))):
        cz = z + hh
        cc = CAIRN + v3((rs.uniform(-0.015, 0.015), rs.uniform(-0.015, 0.015), cz))
        fd.add(Stone(cc, rr, seed=70 + i, cuts=7, squash=(1.0, 0.86, hh / rr * 1.15), soft=0.3, depth=(0.84, 0.96),
                     R=euler(rs.uniform(-0.08, 0.08), rs.uniform(-0.08, 0.08), rs.uniform(0, 3)), noise=0.02), 0.004)
        z = cz + hh * 0.92
    # boulders round the foot of the mound and a few painted river stones
    for i, (c, r, s) in enumerate((((-1.0, 0.3, 0.17), 0.12, 41), ((1.12, -0.18, 0.16), 0.1, 43), ((0.12, 1.1, 0.16), 0.11, 45),
                                    ((-0.84, 0.78, 0.15), 0.08, 47))):
        fd.add(Stone(c, r, seed=s, cuts=10, squash=(1.0, 0.95, 0.75), soft=0.06, noise=0.02), 0.03)
    for i, (x, y, r, a) in enumerate(((-0.62, -0.98, 0.065, -1.2), (0.56, -1.04, 0.055, -1.9), (1.1, 0.12, 0.05, -0.3))):
        c = v3((x, y, ground_height(x, y) + r * 0.45))
        fd.add(Stone(c, r, seed=90 + i, cuts=6, squash=(1.0, 0.9, 0.6), soft=0.25, depth=(0.84, 0.96), noise=0.02), 0.0)
        top = c + v3((0, 0, r * 0.55))
        fd.paint(Func(lambda P, top=top, r=r: _flat_spiral(P, top, r * 0.6, turns=1.8, w=0.006), top - 0.1, top + 0.1), PAINT)
    return fd


def _spiral_face(P, c, nrm, r1, turns=2.6, w=0.014):
    n = norm(nrm)
    u = norm(np.cross(n, v3((0, 0, 1))))
    vv = np.cross(n, u)
    q = P - c.astype(F)
    x, y = q @ u.astype(F), q @ vv.astype(F)
    rr = np.sqrt(x * x + y * y)
    th = np.arctan2(y, x)
    r0 = 0.13                                                             # start outside the hole
    k = F((r1 - r0) / (turns * 2 * math.pi))
    m = np.clip(np.round(((rr - F(r0)) / k - th) / F(2 * math.pi)), 0, turns)
    d = np.abs(rr - (F(r0) + k * (th + F(2 * math.pi) * m)))
    d = np.where(rr > F(r1 + w), rr - F(r1), d)
    d = np.where(rr < F(r0 - w), F(r0) - rr, d)
    return np.maximum(d - F(w), np.abs(q @ n.astype(F)) - F(0.3))


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(13)
    n = 0
    tries = 0
    while n < 16 and tries < 4000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(COURSES[0][0] + 0.05, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0.0))
        if _blocked(p, 0.08):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.026, 0.046), seed=100 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def _blocked(c, pad=0.0):
    x, y = c[0], c[1]
    if math.hypot(x, y) < COURSES[0][0] + 0.03 + pad:
        return True
    for (qx, qy), n, seed, size in QUARTZ:
        if math.hypot(x - qx, y - qy) < 0.16 * size + 0.06 + pad:
            return True
    if math.hypot(x - HOLED[0], y - HOLED[1]) < 0.3 + pad:
        return True
    if math.hypot(x - CAIRN[0], y - CAIRN[1]) < 0.2 + pad:
        return True
    return False


# ---------------------------------------------------------------------------------------- direct geometry
def grass_geometry(seed=17):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 34 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(COURSES[0][0] + 0.04, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, -0.02):
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


def flower_geometry(seed=29):
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 9 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(COURSES[0][0] + 0.06, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.02):
            continue
        if any(np.linalg.norm(c[:2] - s[0][:2]) < 0.2 for s in spots):
            continue
        spots.append((c, (0, 2, 2, 1)[len(spots) % 4]))
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
    return [("Ground", ground_field(), 0.008), ("Dais", dais_field(), 0.0055), ("Amber", amber_field(), 0.003),
            ("Quartz", quartz_field(), 0.003), ("Rocks", rocks_field(), 0.006), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Dais", "Rocks")
LOW_TARGETS = {"Ground": 1300, "Dais": 3600, "Amber": 600, "Quartz": 700, "Rocks": 2400, "Pebbles": 380}
FLAME_PIVOT = None
MAT_OVERRIDES = {"Dais": ("stone", {"name": "HQ_DryStone", "moss": True, "paint": True}),
                 "Rocks": ("stone", {"name": "HQ_PaintedRock", "moss": True, "paint": True})}
GLOW = {"Amber": ((1.0, 0.45, 0.05), 1.0, 0.5), "Quartz": ((0.58, 0.26, 1.0), 1.05)}   # (brighter reads pastel in game)


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and 0.08 < c.z < 0.26 and COURSES[0][0] + 0.02 < r < GROUND_R + 0.05
