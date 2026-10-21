"""Onager base: a round deck of heavy oak planks on the turf rampart of a Roman camp. The planks run across (along X),
sawn round to the deck's edge, two rows of iron nails over the sleepers under them, an iron band round the deck's rim;
the deck's top is where the frame and his feet rest, and nothing on it stands proud of the planks (the whole frame sweeps
it when the tower turns). Beyond the rim the rampart's grass, a few pebbles and flowers, and two pairs of pointed stakes
(pila muralia) crossed and lashed together at the back."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
import onager as _o
import torsion_base as _tb

GROUND_R = 1.34
GROUND_TOP = 0.1
FLOOR_R = 1.2                  # the deck's edge
TOP_Z = 0.16                   # the deck's top: where the frame and his feet rest
STAND = v3((-_o.YAW_PIVOT[0], -_o.YAW_PIVOT[1], TOP_Z))
PLANK_W = 0.15
PLANK_H = 0.032                # half thickness
SLEEPERS = (-0.55, 0.0, 0.55)  # x of the sleepers under the planks (the nail rows)
STAKES = (math.radians(58.0), math.radians(122.0))     # where the crossed stakes stand on the rim (angle from +X)


def ground_height(x, y):
    r = math.hypot(x, y)
    if r < FLOOR_R:
        return TOP_Z
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 0.8) + F(0.02) * np.sin(a * 11 + 0.2) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.03) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _grain(P):
    return F(0.0016) * NOISE(P * np.array([6, 70, 70], F)) + F(0.0008) * NOISE(P * F(140))


def deck_func(seed=7):
    """The planks: strips along X sawn round to the deck's edge, gaps between them, each a little proud or sunk and
    tilted on its own."""
    rs = np.random.RandomState(seed)
    n = int(2 * FLOOR_R / PLANK_W) + 3
    dzs = rs.uniform(-0.004, 0.0025, n).astype(F)
    tilt = rs.uniform(-0.004, 0.004, n).astype(F)
    gap = F(0.006)
    rr = F(0.007)
    def fn(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        u = (y + F(FLOOR_R + PLANK_W * 0.37)) / F(PLANK_W)
        k = np.clip(np.floor(u).astype(np.int64), 0, n - 1)
        dv = (u - np.floor(u) - F(0.5)) * F(PLANK_W)
        d_v = np.abs(dv) - (F(PLANK_W * 0.5) - gap)
        r = np.sqrt(x * x + y * y)
        d_r = r - F(FLOOR_R - 0.012)
        top = F(TOP_Z) + dzs[k] + tilt[k] * x
        d_z = np.abs(z - (top - F(PLANK_H))) - F(PLANK_H)
        q = np.stack([d_v + rr, d_r + rr, d_z + rr], 1)
        out = np.sqrt((np.maximum(q, 0) ** 2).sum(1))
        return out + np.minimum(q.max(1), 0) - rr
    R = FLOOR_R + 0.02
    return Func(fn, (-R, -R, TOP_Z - 2 * PLANK_H - 0.02), (R, R, TOP_Z + 0.03), disp=_grain, disp_amp=0.003)


def deck_field():
    """The planks (oak, grain along X: label 10), the iron nails and the iron band round the rim (6)."""
    fd = Field("Deck")
    fd.add(deck_func(), 0.0, 10)
    # a slab under it all (so no daylight shows through the gaps)
    fd.add(Cylinder(v3((0, 0, TOP_Z - 2 * PLANK_H - 0.02)), FLOOR_R - 0.03, 0.06, rr=0.01), 0.0, 10)
    # the band round the rim
    def band(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.abs(r - F(FLOOR_R - 0.004)) - F(0.008), np.abs(P[:, 2] - F(TOP_Z - 0.03)) - F(0.022))
    fd.add(Func(band, (-1.4, -1.4, TOP_Z - 0.1), (1.4, 1.4, TOP_Z + 0.02)), 0.003, 6)
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        fd.add(Sphere(v3((math.cos(a) * (FLOOR_R + 0.006), math.sin(a) * (FLOOR_R + 0.006), TOP_Z - 0.03)), 0.012), 0.003, 6)
    # nails: two to each plank over each sleeper
    n = int(2 * FLOOR_R / PLANK_W) + 3
    for i in range(n):
        yc = -FLOOR_R - PLANK_W * 0.37 + (i + 0.5) * PLANK_W
        for xs in SLEEPERS:
            for dy in (-0.035, 0.035):
                p = v3((xs, yc + dy, TOP_Z))
                if math.hypot(p[0], p[1]) < FLOOR_R - 0.06:
                    fd.add(Ellipsoid(p + v3((0, 0, -0.001)), (0.011, 0.011, 0.005)), 0.002, 6)
    return fd


def stake_field():
    """Two pairs of pila muralia: pointed oak stakes with a narrow waist, crossed in an X and lashed (rope: label 8),
    standing in the turf just beyond the rim."""
    fd = Field("Stakes")
    for i, a in enumerate(STAKES):
        c = v3((math.cos(a) * 1.27, math.sin(a) * 1.27, 0.0))
        c[2] = ground_height(c[0], c[1]) - 0.02
        t = v3((-math.sin(a), math.cos(a), 0.0))              # along the rim
        for s in (-1, 1):
            d = norm(t * (s * 0.42) + v3((0, 0, 1.0)))
            a0 = c - d * 0.06
            a1 = c + d * 0.44
            fd.add(RoundCone(a0, lerp(a0, a1, 0.46), 0.022, 0.016, disp=_grain, disp_amp=0.002), 0.0, 0)
            fd.add(RoundCone(lerp(a0, a1, 0.46), a1 - d * 0.06, 0.016, 0.02, disp=_grain, disp_amp=0.002), 0.008, 0)
            fd.add(RoundCone(a1 - d * 0.06, a1, 0.02, 0.003), 0.006, 0)
        x = c + v3((0, 0, 0.44 * 0.46 / math.sqrt(1 + 0.42 ** 2) + 0.01))
        fd.add(Torus(x, 0.026, 0.008, R=rot_from_axes(z_axis=t)), 0.004, 8)
        fd.add(Torus(x, 0.026, 0.008, R=rot_from_axes(z_axis=v3((0, 0, 1)))), 0.004, 8)
    return fd


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(23)
    n = 0
    tries = 0
    while n < 12 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        if min(abs(a - s) for s in STAKES) < 0.2:
            continue
        r = rs.uniform(FLOOR_R + 0.03, GROUND_R - 0.04)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.022, 0.036), seed=300 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=41):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 28 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(FLOOR_R + 0.04, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.13 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(7, 11)
        big = 0.6 + 0.35 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.04)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.25, 0.55) + v3((0, 0, 1)))
            L = rs.uniform(0.1, 0.18) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.04), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=43):
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(FLOOR_R + 0.04, GROUND_R - 0.04)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - s[0][:2]) < 0.25 for s in spots):
            continue
        spots.append((c, rs.randint(0, 3)))
    for c, kind in spots:
        base = v3((c[0], c[1], ground_height(c[0], c[1]) - 0.01))
        h = rs.uniform(0.09, 0.13)
        top = base + v3((rs.uniform(-0.02, 0.02), rs.uniform(-0.02, 0.02), h))
        sv, sf, _ = _b.blade_mesh(base, top - base, h, 0.012, (0, 0, 0), segs=2)
        out.append((sv, sf, 0, kind))
        tilt = norm(v3((rs.uniform(-0.3, 0.3), rs.uniform(-0.5, -0.1), 1.0)))
        R = rot_from_axes(z_axis=tilt)
        pv, pf = [], []
        for k in range(5):
            a = 2 * math.pi * k / 5
            dirk = R @ v3((math.cos(a), math.sin(a), 0.12))
            sidek = R @ v3((-math.sin(a), math.cos(a), 0))
            b0 = len(pv)
            pv += [top + tilt * 0.004, top + dirk * 0.033 * 0.55 + sidek * 0.033 * 0.42, top + dirk * 0.033, top + dirk * 0.033 * 0.55 - sidek * 0.033 * 0.42]
            pf.append((b0, b0 + 1, b0 + 2, b0 + 3))
        out.append((pv, pf, 1, kind))
        cv = [top + R @ v3((math.cos(2 * math.pi * k / 6) * 0.012, math.sin(2 * math.pi * k / 6) * 0.012, 0.008)) for k in range(6)]
        cv.append(top + R @ v3((0, 0, 0.016)))
        out.append((cv, [(k, (k + 1) % 6, 6) for k in range(6)], 2, kind))
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Deck", deck_field(), 0.0042), ("Stakes", stake_field(), 0.003),
            ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Deck", "Stakes")
LOW_TARGETS = {"Ground": 1300, "Deck": 4400, "Stakes": 700, "Pebbles": 280}
MAT_OVERRIDES = {"Deck": ("siege", {"name": "HQ_OakDeck", "wood": (0.5, 0.36, 0.22), "wood2": (0.36, 0.25, 0.15), "metal": "iron"}),
                 "Stakes": ("siege", {"name": "HQ_Stakes", "wood": (0.58, 0.42, 0.26), "wood2": (0.42, 0.29, 0.17), "metal": "iron"}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and FLOOR_R - 0.01 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
