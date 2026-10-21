"""Oracle base: the floor of the shrine at Delphi. A round marble floor in two steps (curved blocks round a centre slab,
the top polished where she stands), split by a jagged dark fissure (the chasm the vapours rise from) running across it;
on a grassy mound with grey rocks; behind it on one side the omphalos, the navel stone of the world (a domed stone on a
square plinth, wrapped in a carved net of knotted bands, red ribbons painted in the net's knots), on the other a laurel
bush in a stone planter; laurel leaves strewn on the floor's edge, grass, flowers and pebbles. Nothing on the floor
stands proud of it: the tower turns with the tripod sweeping over it."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
from sunpriest_base import ring_func
import cretan_base as _cb
import oracle as _o

GROUND_R = 1.34
GROUND_TOP = 0.12
LOW_Z = 0.2                        # the lower step's top
TOP_Z = 0.28                       # the floor's top: where she and the tripod stand
YAW_PIVOT = (0.25, -0.22, 0.0)     # (oracle.py's: between her and the tripod)
STAND = v3((-YAW_PIVOT[0], -YAW_PIVOT[1], TOP_Z))
CENTRE_R = 0.24
UPPER_R = 0.84                     # the upper step's edge (the tripod's feet sweep to ~0.62)
LOWER_R = 1.0
OMPHALOS_C = v3((-0.72, 0.86, 0.0))
OMPH_R = 0.2
LAUREL_C = v3((0.86, 0.72, 0.0))
FISSURE = [(-0.62, -0.42), (-0.4, -0.3), (-0.26, -0.33), (-0.08, -0.12), (0.06, -0.1), (0.2, 0.12), (0.34, 0.16),
           (0.5, 0.4), (0.64, 0.46)]
ROCKS = [(v3((1.08, -0.42, 0.0)), 0.15, 7), (v3((-1.1, -0.36, 0.0)), 0.12, 8), (v3((0.06, 1.16, 0.0)), 0.09, 9)]


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.04 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 1.7) + F(0.02) * np.sin(a * 11 + 0.4) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.04) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _fissure_d(P):
    """Distance (in plan) to the fissure's jagged line."""
    out = F(1.0) * np.ones(len(P), F)
    x, y = P[:, 0], P[:, 1]
    for (ax_, ay), (bx, by) in zip(FISSURE, FISSURE[1:]):
        abx, aby = bx - ax_, by - ay
        t = np.clip(((x - F(ax_)) * F(abx) + (y - F(ay)) * F(aby)) / F(abx * abx + aby * aby), 0, 1)
        dx = x - (F(ax_) + t * F(abx))
        dy = y - (F(ay) + t * F(aby))
        out = np.minimum(out, np.sqrt(dx * dx + dy * dy))
    return out


def marble_field():
    """The floor (marble, label 0; polished where she stands, 6; weathered dark low on the outer step and in the
    fissure, 7), the omphalos's plinth (0) and the planter (0)."""
    fd = Field("Marble")
    fd.add(Cylinder(v3((0, 0, (GROUND_TOP - 0.06 + LOW_Z) / 2)), 0.9, LOW_Z - GROUND_TOP + 0.06, rr=0.01), 0.0)   # core (hidden)
    fd.add(ring_func(0.8, LOWER_R, 26, 81, LOW_Z, (LOW_Z - GROUND_TOP + 0.06) / 2), 0.0)
    fd.add(ring_func(0.52, UPPER_R, 18, 82, TOP_Z, (TOP_Z - LOW_Z + 0.02) / 2, jitter=0.3, chip=_cb._fine), 0.0)
    fd.add(ring_func(CENTRE_R, 0.52, 10, 83, TOP_Z, (TOP_Z - LOW_Z + 0.02) / 2, jitter=0.3, chip=_cb._fine), 0.0)
    fd.add(Cylinder(v3((0, 0, TOP_Z - 0.09)), CENTRE_R - 0.0055, 0.18, rr=0.01, disp=_cb._fine, disp_amp=0.003), 0.0)
    # the fissure: a jagged crack across the floor, a little wider in the middle, dark inside
    def crack(P):
        w = F(0.016) + F(0.012) * np.exp(-((P[:, 0] - F(0.0)) / F(0.35)) ** 2) + F(0.005) * NOISE(P * F(20))
        return np.maximum(_fissure_d(P) - w, F(TOP_Z - 0.06) - P[:, 2])
    fd.sub(Func(crack, (-0.9, -0.9, TOP_Z - 0.1), (0.9, 0.9, TOP_Z + 0.05)), 0.006)
    fd.paint(Func(lambda P: np.maximum(_fissure_d(P) - F(0.05) - F(0.01) * NOISE(P * F(12)), F(TOP_Z - 0.2) - P[:, 2]),
                  (-0.9, -0.9, TOP_Z - 0.3), (0.9, 0.9, TOP_Z + 0.05)), 7)
    fd.paint(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(0.45), F(TOP_Z - 0.01) - P[:, 2]),
                  (-0.6, -0.6, TOP_Z - 0.05), (0.6, 0.6, TOP_Z + 0.05)), 6)
    fd.paint(Func(lambda P: np.maximum(F(0.88) - np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2), P[:, 2] - F(LOW_Z - 0.035)),
                  (-1.2, -1.2, GROUND_TOP - 0.1), (1.2, 1.2, LOW_Z)), 7)
    # the omphalos's plinth
    g = ground_height(OMPHALOS_C[0], OMPHALOS_C[1])
    fd.add(RoundBox(OMPHALOS_C + v3((0, 0, g + 0.04)), (0.25, 0.25, 0.075), 0.015, disp=_cb._chip, disp_amp=0.006), 0.0)
    # the laurel's planter: a low round stone tub
    g2 = ground_height(LAUREL_C[0], LAUREL_C[1])
    tub = Cylinder(LAUREL_C + v3((0, 0, g2 + 0.1)), 0.17, 0.2, rr=0.02)
    fd.add(Inter(Shell(tub, 0.0, 0.04, pad=0.05, disp=_cb._chip, disp_amp=0.004), Func(lambda P: P[:, 2] - F(g2 + 0.19), LAUREL_C - 0.4, LAUREL_C + 0.5), 0.006), 0.0)
    fd.add(Cylinder(LAUREL_C + v3((0, 0, g2 + 0.03)), 0.16, 0.06, rr=0.01), 0.01)
    return fd


def omphalos_field():
    """The navel stone: a smooth dome a little taller than wide, wrapped in a raised net of knotted bands (the agrenon);
    red ribbons painted where the bands cross (label 5)."""
    fd = Field("Omphalos")
    g = ground_height(OMPHALOS_C[0], OMPHALOS_C[1]) + 0.11
    c = OMPHALOS_C + v3((0, 0, g))
    dome = Ellipsoid(c, (OMPH_R, OMPH_R, OMPH_R * 1.35))
    fd.add(Inter(dome, Plane(c + v3((0, 0, -0.02)), (0, 0, -1)), 0.01), 0.0)
    def net(P):
        q = P - c.astype(F)
        th = np.arctan2(q[:, 1], q[:, 0])
        h = q[:, 2] / F(OMPH_R * 1.35)
        u = th * F(8 / (2 * math.pi)) + h * F(2.2)
        v = th * F(8 / (2 * math.pi)) - h * F(2.2)
        du = np.abs(u - np.round(u))
        dv = np.abs(v - np.round(v))
        return np.minimum(du, dv) * F(0.17) - F(0.008)
    def net_lim(P):
        return np.maximum(net(P), F(c[2] - 0.0) - P[:, 2])
    fd.add(Inter(Shell(dome, 0.006, 0.012, pad=0.04), Func(net_lim, c - 0.4, c + 0.5), 0.003), 0.003)
    def knots(P):
        q = P - c.astype(F)
        th = np.arctan2(q[:, 1], q[:, 0])
        h = q[:, 2] / F(OMPH_R * 1.35)
        u = th * F(8 / (2 * math.pi)) + h * F(2.2)
        v = th * F(8 / (2 * math.pi)) - h * F(2.2)
        du = np.abs(u - np.round(u))
        dv = np.abs(v - np.round(v))
        return np.maximum(np.maximum(du, dv) * F(0.17) - F(0.014), F(c[2] + 0.01) - P[:, 2])
    fd.paint(Func(knots, c - 0.4, c + 0.5), 5)
    return fd


def laurel_bush():
    """(centre, radius) of the leaf clumps of the laurel bush."""
    g2 = ground_height(LAUREL_C[0], LAUREL_C[1])
    rs = np.random.RandomState(13)
    out = []
    for k in range(9):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.0, 0.12)
        out.append((LAUREL_C + v3((math.cos(a) * r, math.sin(a) * r, g2 + 0.32 + rs.uniform(0.0, 0.3))), rs.uniform(0.09, 0.14)))
    return out


def bush_field():
    """The laurel bush: a few stems from the planter's soil (label 7) and clumps of glossy pointed leaves (0)."""
    fd = Field("Bush")
    g2 = ground_height(LAUREL_C[0], LAUREL_C[1])
    soil = LAUREL_C + v3((0, 0, g2 + 0.17))
    leaves = lambda P: F(0.012) * NOISE(P * F(26)) + F(0.006) * NOISE(P * F(60))
    for c, r in laurel_bush():
        fd.add(RoundCone(soil + (c - soil) * 0.05, c, 0.016, 0.008), 0.004, 7)
        fd.add(Ellipsoid(c, (r, r, r * 0.85), disp=leaves, disp_amp=0.016), 0.03, 0)
    fd.add(Cylinder(soil, 0.13, 0.02, rr=0.006), 0.0, 7)
    return fd


def leaves_geometry(seed=17):
    """Laurel leaves strewn on the floor's outer step (direct geometry: little flat pointed quads)."""
    rs = np.random.RandomState(seed)
    out = []
    for k in range(22):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(UPPER_R + 0.03, LOWER_R - 0.03)
        c = v3((math.cos(a) * r, math.sin(a) * r, LOW_Z + 0.004))
        d = v3((math.cos(rs.uniform(0, 6.3)), math.sin(rs.uniform(0, 6.3)), 0.0))
        s = v3((-d[1], d[0], 0.0))
        L, W = rs.uniform(0.04, 0.06), rs.uniform(0.012, 0.018)
        out.append([c - d * L, c + s * W, c + d * L, c - s * W])
    return out


def rocks_field():
    fd = Field("Rocks")
    for c, r, seed in ROCKS:
        p = c + v3((0, 0, ground_height(c[0], c[1]) - 0.25 * r))
        fd.add(Stone(p, r, seed=430 + seed, squash=(1.1, 0.95, 0.62), noise=0.08), 0.0)
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < LOWER_R + 0.05 + pad:
        return True
    if math.hypot(c[0] - OMPHALOS_C[0], c[1] - OMPHALOS_C[1]) < 0.36 + pad:
        return True
    if math.hypot(c[0] - LAUREL_C[0], c[1] - LAUREL_C[1]) < 0.24 + pad:
        return True
    for rc, r, s in ROCKS:
        if math.hypot(c[0] - rc[0], c[1] - rc[1]) < r * 1.15 + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(31)
    n = 0
    tries = 0
    while n < 12 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(LOWER_R + 0.05, 1.26)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.022, 0.04), seed=560 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=47):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 24 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(LOWER_R + 0.06, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.14 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(7, 12)
        big = 0.65 + 0.4 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.05)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.15, 0.45) + v3((0, 0, 1)))
            L = rs.uniform(0.11, 0.2) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.04), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=53):
    """Wild thyme and a few yellow rock-roses (as the Cretan's hillside)."""
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(LOWER_R + 0.06, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.04) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.22 for s in spots):
            continue
        spots.append((c, 2 if len(spots) % 3 else 1))
    for c, col in spots:
        n_stem = rs.randint(6, 10) if col == 2 else rs.randint(3, 5)
        for k in range(n_stem):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.08)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.06, 0.12) if col == 2 else rs.uniform(0.1, 0.16)
            d = norm(v3((math.cos(ang) * 0.45, math.sin(ang) * 0.45, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, col))
            nb = 2 if col == 2 else 1
            for j in range(nb):
                p = root + d * h * (1.0 - 0.25 * j) + v3((rs.uniform(-0.01, 0.01), rs.uniform(-0.01, 0.01), 0))
                tilt = norm(v3((rs.uniform(-0.5, 0.5), rs.uniform(-0.5, 0.5), 1.0)))
                _cb._bloom(out, p, tilt, 0.02 if col == 2 else 0.034, col)
    # the strewn laurel leaves (leaf-green swatch 0 quads, flat on the step)
    for q in leaves_geometry():
        out.append((q, [(0, 1, 2, 3)], 0, 0))
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Marble", marble_field(), 0.0042), ("Omphalos", omphalos_field(), 0.003),
            ("Bush", bush_field(), 0.004), ("Rocks", rocks_field(), 0.004), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Marble", "Omphalos", "Bush")
LOW_TARGETS = {"Ground": 1500, "Marble": 4600, "Omphalos": 900, "Bush": 1100, "Rocks": 600, "Pebbles": 300}
MAT_OVERRIDES = {"Marble": ("marble", {"name": "HQ_DelphiMarble"}),
                 "Omphalos": ("marble", {"name": "HQ_Omphalos", "base": (0.82, 0.8, 0.76), "warm": (0.8, 0.74, 0.64)}),
                 "Bush": ("leafy", {"name": "HQ_LaurelBush", "leaf": (0.15, 0.3, 0.11), "vein": (0.32, 0.46, 0.18)}),
                 "Rocks": ("stone", {"name": "HQ_DelphiRock", "moss": False})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035 and r > LOWER_R + 0.02
    return n.z > 0.55 and on_ground
