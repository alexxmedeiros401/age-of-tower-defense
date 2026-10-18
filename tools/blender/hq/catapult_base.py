"""Boulder Catapult base: a low grassy mound worn to bare, trampled earth where the sled turns, its runners' ruts and
pebbles (distance fields) + grass and flowers round the rim (direct low-poly geometry). The whole catapult (sled,
machine and operator) turns about the middle of the base, so the base stays clear of anything taller than a pebble."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b

GROUND_R = 1.34
GROUND_TOP = 0.16
WORK_R = 1.1
DIRT = 6
PILE = v3((-0.96, 0.62, 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.025 * max(0.0, 1 - (r / GROUND_R) ** 2)


# the character origin (her feet on the platform) relative to the base centre, when the tower faces forward
import catapult as _cat
SLED_Z = ground_height(0, 0) + 0.005                       # where the runners rest
STAND = v3((-_cat.YAW_PIVOT[0], -_cat.YAW_PIVOT[1], SLED_Z - _cat.GROUND_Z))
TOP_Z = STAND[2]


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 0.7) + F(0.02) * np.sin(a * 11 + 2.0) + F(0.02) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.025) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.09), 0), np.maximum(dz + F(0.09), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.09), dz + F(0.09)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.09)
    fd.add(Func(disc, (-1.55, -1.55, -0.25), (1.55, 1.55, 0.35),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    # ruts: the runners' tracks, worn in arcs where the sled swings round
    for rr in (0.52, 0.86):
        def rut(P, rr=rr):
            r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
            a = np.arctan2(P[:, 1], P[:, 0])
            on = np.clip(np.cos(a * 1.0 - 1.4) * 2.0 - 0.6, 0, 1)        # deepest at the back, fading round the sides
            return np.maximum(np.abs(r - F(rr)) - F(0.03), np.abs(P[:, 2] - F(GROUND_TOP + 0.03)) - F(0.03 * 1.0)) + F(0.02) * (1 - on)
        fd.sub(Func(rut, (-1.2, -1.2, 0.0), (1.2, 1.2, 0.4)), 0.02)
    def work(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        return r - (F(WORK_R + 0.05) + F(0.035) * np.sin(a * 6 + 1.1) + F(0.025) * NOISE(P * F(6)))
    fd.paint(Func(work, (-1.4, -1.4, -0.3), (1.4, 1.4, 0.5)), DIRT)
    return fd


def rocks_field():
    fd = Field("Rocks")
    for c, r, s in (((1.14, -0.42, GROUND_TOP + 0.02), 0.12, 41), ((-1.1, -0.5, GROUND_TOP + 0.02), 0.1, 43), ((0.6, 1.08, GROUND_TOP + 0.02), 0.11, 45)):
        fd.add(Stone(c, r, seed=s, cuts=10, squash=(1.0, 0.95, 0.72), soft=0.06, noise=0.02), 0.0)
    # the stockpile: boulders heaped against a stake at the edge
    for i, (dx, dy, dz, r) in enumerate(((0.0, 0.0, 0.07, 0.11), (0.17, 0.05, 0.06, 0.1), (0.06, 0.16, 0.06, 0.1), (0.09, 0.07, 0.2, 0.095),
                                         (-0.12, 0.12, 0.05, 0.085))):
        fd.add(Stone(PILE + v3((dx, dy, GROUND_TOP + dz)), r, seed=60 + i, cuts=10, noise=0.03), 0.006)
    return fd


def wood_field():
    fd = Field("Wood")
    a = PILE + v3((-0.12, -0.1, GROUND_TOP - 0.05))
    fd.add(Chain([a, a + v3((0.01, 0.0, 0.25)), a + v3((0.02, 0.01, 0.5))], [0.035, 0.032, 0.028], k=0.01,
                 disp=lambda P: F(0.004) * NOISE(P * np.array([45, 45, 6], F)), disp_amp=0.005), 0.0)
    return fd


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(13)
    n = 0
    tries = 0
    while n < 18 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.2, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.022, 0.04), seed=100 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < WORK_R + 0.05 + pad:
        return True
    return False


def grass_geometry(seed=17):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(WORK_R + 0.08, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.0) and math.hypot(c[0], c[1]) < WORK_R + 0.05:
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.13 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(7, 11)
        big = 0.6 + 0.35 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.045)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.2, 0.5) + v3((0, 0, 1)))
            L = rs.uniform(0.11, 0.2) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.04), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
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
    while len(spots) < 7 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(WORK_R + 0.1, GROUND_R - 0.04)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - s[0][:2]) < 0.2 for s in spots):
            continue
        spots.append((c, rs.randint(0, 3)))
    for c, kind in spots:
        base = v3((c[0], c[1], ground_height(c[0], c[1]) - 0.01))
        h = rs.uniform(0.09, 0.13)
        top = base + v3((rs.uniform(-0.02, 0.02), rs.uniform(-0.02, 0.02), h))
        sv, sf, _ = _b.blade_mesh(base, top - base, h, 0.012, (0, 0, 0), segs=2)
        out.append((sv, sf, 0, kind))
        n = 5
        pr = 0.033
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
    # No rocks, stockpile or stake on this base: the whole sled turns with the tower and sweeps a circle as wide as the
    # base (its runner tips reach 1.34 from the pivot), so anything taller than a pebble would be ploughed through.
    return [("Ground", ground_field(), 0.008), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Ground",)
LOW_TARGETS = {"Ground": 1600, "Pebbles": 420}
FLAME_PIVOT = None
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_WorkGround", "dirt_label": DIRT}),
                 "Rocks": ("stone", {"name": "HQ_PileStone", "moss": True})}


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and r > WORK_R + 0.1 and r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
