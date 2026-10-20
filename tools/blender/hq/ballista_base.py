"""Ballista base: a round timber deck on a grassy mound. Oak planks laid side by side across it (each a little warped and
set at its own height, dark gaps between them, iron nails at their ends), framed by a ring of curved rim timbers pegged
flush with the planks; grass, flowers and a few pebbles beyond the rim. Nothing on the deck stands taller than a plank:
the whole ballista sweeps it when the tower turns."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
import ballista as _t

GROUND_R = 1.32
GROUND_TOP = 0.1
FLOOR_R = 1.2                  # the deck's outer edge
TOP_Z = 0.16                   # the deck's top: where the stand's feet and his rest
STAND = v3((-_t.YAW_PIVOT[0], -_t.YAW_PIVOT[1], TOP_Z))
RIM_W = 0.11                   # the rim timbers' width
PLANK_W = 0.15


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
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 0.3) + F(0.02) * np.sin(a * 11 + 1.2) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.03) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _grain(P):
    return F(0.0018) * NOISE(P * np.array([4, 40, 40], F)) + F(0.0012) * NOISE(P * F(30))


def planks_func(seed=41):
    """The planks: boards running along x, PLANK_W wide, each with its own height and a slight warp, gaps between
    them; inside the rim."""
    rs = np.random.RandomState(seed)
    n = int(2 * FLOOR_R / PLANK_W) + 2
    dzs = rs.uniform(-0.004, 0.003, n).astype(F)
    warp = rs.uniform(-0.006, 0.006, n).astype(F)
    gap = F(0.006)
    rr = F(0.008)
    hz = F(0.03)
    y0 = -FLOOR_R - 0.04
    def fn(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        u = (y - F(y0)) / F(PLANK_W)
        k = np.clip(np.floor(u).astype(np.int64), 0, n - 1)
        dy = (u - np.floor(u) - F(0.5)) * F(PLANK_W)
        d_y = np.abs(dy) - (F(PLANK_W * 0.5) - gap)
        r = np.sqrt(x * x + y * y)
        d_r = r - F(FLOOR_R - RIM_W + 0.004)
        top = F(TOP_Z) + dzs[k] + warp[k] * (x / F(FLOOR_R)) ** 2
        d_z = np.abs(z - (top - hz)) - hz
        q = np.stack([d_y + rr, d_r + rr, d_z + rr], 1)
        out = np.sqrt((np.maximum(q, 0) ** 2).sum(1))
        return out + np.minimum(q.max(1), 0) - rr
    R = FLOOR_R + 0.02
    return Func(fn, (-R, -R, TOP_Z - 0.08), (R, R, TOP_Z + 0.03), disp=_grain, disp_amp=0.004)


def rim_func(n=12, seed=43):
    """The rim: n curved timbers round the deck, pegged, butted end to end."""
    rs = np.random.RandomState(seed)
    ph0 = rs.uniform(0, 2 * math.pi)
    dzs = rs.uniform(-0.003, 0.004, n).astype(F)
    step = 2 * math.pi / n
    gap = F(0.006)
    rr = F(0.012)
    r0, r1 = FLOOR_R - RIM_W, FLOOR_R
    def fn(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.sqrt(x * x + y * y)
        a = np.arctan2(y, x)
        u = (a - F(ph0)) / F(step)
        k = np.floor(u).astype(np.int64) % n
        da = (u - np.floor(u) - F(0.5)) * F(step)
        d_a = np.abs(da) * r - (F(step * 0.5) * r - gap)
        d_r = np.maximum(F(r0) - r, r - F(r1))
        top = F(TOP_Z + 0.004) + dzs[k]
        d_z = np.abs(z - (top - F(0.045))) - F(0.045)
        q = np.stack([d_a + rr, d_r + rr, d_z + rr], 1)
        out = np.sqrt((np.maximum(q, 0) ** 2).sum(1))
        return out + np.minimum(q.max(1), 0) - rr
    R = r1 + 0.02
    return Func(fn, (-R, -R, TOP_Z - 0.12), (R, R, TOP_Z + 0.03), disp=_grain, disp_amp=0.004), ph0, step


def deck_field():
    """Planks (oak, grain along x: label 10), the rim timbers (grain along them: label 0), iron nail heads (6) at the
    planks' ends, oak pegs in the rim."""
    fd = Field("Deck")
    fd.add(Cylinder(v3((0, 0, TOP_Z - 0.07)), FLOOR_R - RIM_W + 0.01, 0.07, rr=0.01), 0.0, 10)        # (the bed under the planks)
    fd.add(planks_func(), 0.004, 10)
    rim, ph0, step = rim_func()
    fd.add(rim, 0.004, 0)
    for k in range(12):                                             # pegs: two in each rim timber
        for f in (0.28, 0.72):
            a = ph0 + (k + f) * step
            p = v3((math.cos(a) * (FLOOR_R - RIM_W / 2), math.sin(a) * (FLOOR_R - RIM_W / 2), TOP_Z + 0.002))
            fd.add(Cylinder(p, 0.014, 0.012, rr=0.004), 0.002, 11)
    n = int(2 * FLOOR_R / PLANK_W) + 2
    y0 = -FLOOR_R - 0.04
    for k in range(n):                                              # nails near both ends of every plank
        y = y0 + (k + 0.5) * PLANK_W
        if abs(y) > FLOOR_R - RIM_W - 0.04:
            continue
        xe = math.sqrt(max((FLOOR_R - RIM_W - 0.05) ** 2 - y * y, 0.0))
        for xs in (-xe, xe):
            for dy in (-0.035, 0.035):
                fd.add(Sphere(v3((xs, y + dy, TOP_Z + 0.002)), 0.008), 0.002, 6)
    return fd


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(19)
    n = 0
    tries = 0
    while n < 14 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(FLOOR_R + 0.03, GROUND_R - 0.04)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.022, 0.038), seed=200 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=31):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 26 and tries < 8000:
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


def flower_geometry(seed=37):
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
    return [("Ground", ground_field(), 0.008), ("Deck", deck_field(), 0.0042), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Deck",)
LOW_TARGETS = {"Ground": 1300, "Deck": 4200, "Pebbles": 300}
MAT_OVERRIDES = {"Deck": ("siege", {"name": "HQ_BalDeck", "wood": (0.5, 0.36, 0.22), "wood2": (0.36, 0.25, 0.15), "metal": "iron"}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and FLOOR_R - 0.01 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
