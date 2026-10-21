"""Trebuchet base: a siege platform before the castle. A round deck of heavy oak planks laid front to back, pinned with
trenails over three sleepers, inside a kerb of curved oak timbers jointed with iron dogs; nothing on the deck stands
proud of the planks (the whole engine sweeps it when the tower turns). Beyond the kerb, trodden earth and grass; at the
back two gabions (wicker baskets packed with earth, grass on top) that shield the crew; at the front on the left a
pyramid of spare stone balls; pebbles and a few flowers (distance fields + direct low-poly geometry for the grass and
the flowers)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
import trebuchet as _t
from torsion import stone_ball
from crossbowman_base import _bloom

GROUND_R = 1.42
GROUND_TOP = 0.1
FLOOR_R = 1.25                 # the deck's edge (the engine sweeps up to ~1.23 of it)
KERB_W = 0.1                   # the kerb's width outside the deck
TOP_Z = 0.16                   # the deck's top: where the frame and his feet rest
STAND = v3((-_t.YAW_PIVOT[0], -_t.YAW_PIVOT[1], TOP_Z))
PLANK_W = 0.16
PLANK_H = 0.032                # half thickness
SLEEPERS = (-0.62, 0.0, 0.62)  # y of the sleepers under the planks (the trenail rows)
GABIONS = (math.radians(62.0), math.radians(112.0))      # behind (+Y): angle from +X
BALLS_A = math.radians(218.0)                            # the spare balls: in front on the left (as he faces -Y)


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
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 1.9) + F(0.02) * np.sin(a * 11 + 0.6) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.03) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.7, -1.7, -0.25), (1.7, 1.7, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _grain(P):
    return F(0.0016) * NOISE(P * np.array([70, 6, 70], F)) + F(0.0008) * NOISE(P * F(140))


def deck_func(seed=11):
    """The planks: strips along Y sawn round to the deck's edge, gaps between them, each a little proud or sunk and
    tilted on its own, their ends butting at staggered joints over the sleepers."""
    rs = np.random.RandomState(seed)
    n = int(2 * FLOOR_R / PLANK_W) + 3
    dzs = rs.uniform(-0.004, 0.0025, (n, 2)).astype(F)
    tilt = rs.uniform(-0.004, 0.004, (n, 2)).astype(F)
    joint = np.where(np.arange(n) % 2 == 0, F(SLEEPERS[0]), F(SLEEPERS[2])).astype(F)
    gap = F(0.006)
    rr = F(0.007)
    def fn(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        u = (x + F(FLOOR_R + PLANK_W * 0.41)) / F(PLANK_W)
        k = np.clip(np.floor(u).astype(np.int64), 0, n - 1)
        du = (u - np.floor(u) - F(0.5)) * F(PLANK_W)
        d_u = np.abs(du) - (F(PLANK_W * 0.5) - gap)
        j = joint[k]
        seg = (y > j).astype(np.int64)
        d_j = gap - np.abs(y - j)                                  # the butt joint across the plank
        r = np.sqrt(x * x + y * y)
        d_r = r - F(FLOOR_R - 0.012)
        top = F(TOP_Z) + dzs[k, seg] + tilt[k, seg] * y
        d_z = np.abs(z - (top - F(PLANK_H))) - F(PLANK_H)
        q = np.stack([d_u + rr, d_r + rr, d_z + rr], 1)
        out = np.sqrt((np.maximum(q, 0) ** 2).sum(1))
        return np.maximum(out + np.minimum(q.max(1), 0) - rr, d_j)
    R = FLOOR_R + 0.02
    return Func(fn, (-R, -R, TOP_Z - 2 * PLANK_H - 0.02), (R, R, TOP_Z + 0.03), disp=_grain, disp_amp=0.003)


def deck_field():
    """The planks (oak, grain along Y: label 0) and their trenails (oak end grain, darker: label 11)."""
    fd = Field("Deck")
    fd.add(deck_func(), 0.0, 0)
    fd.add(Cylinder(v3((0, 0, TOP_Z - 2 * PLANK_H - 0.02)), FLOOR_R - 0.03, 0.06, rr=0.01), 0.0, 0)
    n = int(2 * FLOOR_R / PLANK_W) + 3
    for i in range(n):
        xc = -FLOOR_R - PLANK_W * 0.41 + (i + 0.5) * PLANK_W
        for ys in SLEEPERS:
            for dx in (-0.038, 0.038):
                p = v3((xc + dx, ys + (0.03 if ys != 0.0 and abs(ys) > 0.1 and i % 2 == (0 if ys < 0 else 1) else 0.0), TOP_Z))
                if math.hypot(p[0], p[1]) < FLOOR_R - 0.07:
                    fd.add(Cylinder(p + v3((0, 0, -0.004)), 0.011, 0.01, rr=0.003), 0.002, 11)
    return fd


def kerb_field():
    """A ring of curved oak timbers round the deck, a little proud of it, jointed with iron dogs (6)."""
    fd = Field("Kerb")
    r0, r1 = FLOOR_R - 0.01, FLOOR_R + KERB_W
    top = TOP_Z + 0.025
    def ring(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        seg = np.abs(((a + F(0.2)) / F(2 * math.pi / 10)) - np.round((a + F(0.2)) / F(2 * math.pi / 10))) * F(2 * math.pi / 10) * r
        dr = np.abs(r - F((r0 + r1) / 2)) - F((r1 - r0) / 2)
        dz = np.abs(P[:, 2] - F((top + GROUND_TOP - 0.04) / 2)) - F((top - GROUND_TOP + 0.04) / 2)
        dj = F(0.004) - seg
        q = np.stack([np.maximum(dr + F(0.008), 0), np.maximum(dz + F(0.008), 0)], 1)
        d = np.sqrt((q ** 2).sum(1)) + np.minimum(np.maximum(dr, dz) + F(0.008), 0) - F(0.008)
        return np.maximum(d, dj)
    R = r1 + 0.05
    grain = lambda P: F(0.0014) * NOISE(np.stack([np.arctan2(P[:, 1], P[:, 0]) * F(8), P[:, 2] * F(60), np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) * F(60)], 1))
    fd.add(Func(ring, (-R, -R, GROUND_TOP - 0.1), (R, R, top + 0.03), disp=grain, disp_amp=0.002), 0.0, 10)
    for k in range(10):
        a = 2 * math.pi * k / 10 - 0.2
        c = v3((math.cos(a) * (r0 + r1) / 2, math.sin(a) * (r0 + r1) / 2, top))
        t = v3((-math.sin(a), math.cos(a), 0.0))
        fd.add(RoundBox(c, (0.012, 0.05, 0.006), 0.003, R=rot_from_axes(z_axis=(0, 0, 1), y_axis=t)), 0.002, 6)
        for s in (-1, 1):
            fd.add(Sphere(c + t * (s * 0.042), 0.009), 0.002, 6)
    return fd


def gabion_field():
    """Two gabions: wicker baskets (stakes and woven withies) packed with earth."""
    fd = Field("Gabions")
    for i, a in enumerate(GABIONS):
        c = v3((math.cos(a) * 1.335, math.sin(a) * 1.335, 0.0))
        z0 = ground_height(c[0], c[1]) - 0.03
        h = 0.27 + 0.03 * i
        r = 0.075
        def weave(P, c=c):
            q = P - c.astype(F)
            ang = np.arctan2(q[:, 1], q[:, 0])
            return F(0.004) * np.sin(ang * F(9)) * np.sin(q[:, 2] * F(110)) + F(0.0012) * NOISE(P * F(60))
        fd.add(Inter(Shell(Cylinder(c + v3((0, 0, z0 + h / 2)), r, h, rr=0.01), 0.0, 0.016, disp=weave, disp_amp=0.006),
                     Func(lambda P, z0=z0, h=h: P[:, 2] - F(z0 + h - 0.006), c - 0.3, c + 0.6), 0.004), 0.0)
        for k in range(8):                                                        # the stakes, proud of the rim
            ak = 2 * math.pi * k / 8 + 0.2 * i
            p = c + v3((math.cos(ak) * r, math.sin(ak) * r, 0))
            fd.add(RoundCone(p + v3((0, 0, z0)), p + v3((0, 0, z0 + h + 0.035)), 0.009, 0.006), 0.003)
    return fd


def gabion_fill():
    fd = Field("Fill")
    for i, a in enumerate(GABIONS):
        c = v3((math.cos(a) * 1.335, math.sin(a) * 1.335, 0.0))
        z0 = ground_height(c[0], c[1]) - 0.03
        h = 0.27 + 0.03 * i
        fd.add(Ellipsoid(c + v3((0, 0, z0 + h - 0.015)), (0.07, 0.07, 0.035), disp=lambda P: F(0.004) * NOISE(P * F(20)), disp_amp=0.005), 0.0)
    return fd


def ball_centres():
    a = BALLS_A
    c = v3((math.cos(a) * 1.33, math.sin(a) * 1.33, 0.0))
    z = ground_height(c[0], c[1]) - 0.004
    R = _t.BALL_R
    t = v3((-math.sin(a), math.cos(a), 0.0))
    o = v3((math.cos(a), math.sin(a), 0.0))
    out = [c + t * (s * (R + 0.004)) + v3((0, 0, z + R)) for s in (-1, 1)]
    out.append(c - o * (R * 1.2) + v3((0, 0, z + R)))
    out.append(c - o * (R * 0.4) + v3((0, 0, z + R + R * 1.35)))
    return out


def balls_field():
    fd = Field("Balls")
    for i, p in enumerate(ball_centres()):
        fd.add(stone_ball(p, _t.BALL_R, 40 + i), 0.0)
    return fd


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(29)
    n = 0
    tries = 0
    avoid = list(GABIONS) + [BALLS_A]
    while n < 12 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        if min(abs((a - s + math.pi) % (2 * math.pi) - math.pi) for s in avoid) < 0.22:
            continue
        r = rs.uniform(FLOOR_R + KERB_W + 0.03, GROUND_R - 0.03)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.02, 0.032), seed=320 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def _free(c):
    for a in list(GABIONS) + [BALLS_A]:
        p = np.array((math.cos(a) * 1.335, math.sin(a) * 1.335))
        if np.linalg.norm(c[:2] - p) < 0.14:
            return False
    return True


def grass_geometry(seed=47):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(FLOOR_R + KERB_W + 0.02, GROUND_R - 0.04)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.12 for t in tufts) or not _free(c):
            continue
        tufts.append(c)
    for i, a in enumerate(GABIONS):                       # grass on the gabions' earth
        c = v3((math.cos(a) * 1.335, math.sin(a) * 1.335, 0.0))
        c[2] = ground_height(c[0], c[1]) - 0.03 + 0.27 + 0.03 * i + 0.012
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(7, 11)
        big = 0.6 + 0.35 * rs.rand()
        on_gab = ti >= len(tufts) - len(GABIONS)
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.035)
            root = c + off
            root[2] = (c[2] if on_gab else ground_height(root[0], root[1])) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.25, 0.55) + v3((0, 0, 1)))
            L = rs.uniform(0.09, 0.16) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.04), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=53):
    """Daisies (swatch 0: white petals) and buttercups (1: yellow) in the grass beyond the kerb."""
    rs = np.random.RandomState(seed)
    spots = []
    tries = 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(FLOOR_R + KERB_W + 0.03, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - s[0][:2]) < 0.25 for s in spots) or not _free(c):
            continue
        spots.append((c, 0 if len(spots) % 2 else 1))
    out = []
    for c, col in spots:
        for k in range(rs.randint(2, 5)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.05)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.07, 0.12)
            d = norm(v3((math.cos(ang) * 0.35, math.sin(ang) * 0.35, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, col))
            tilt = norm(v3((rs.uniform(-0.4, 0.4), rs.uniform(-0.4, 0.4), 1.0)))
            _bloom(out, root + d * h, tilt, 0.026, col)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Deck", deck_field(), 0.0042), ("Kerb", kerb_field(), 0.004),
            ("Gabions", gabion_field(), 0.003), ("Fill", gabion_fill(), 0.005), ("Balls", balls_field(), 0.004),
            ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Deck", "Kerb", "Gabions")
LOW_TARGETS = {"Ground": 1300, "Deck": 4600, "Kerb": 900, "Gabions": 1100, "Fill": 160, "Balls": 500, "Pebbles": 280}
MAT_OVERRIDES = {"Deck": ("siege", {"name": "HQ_TrebDeck", "wood": (0.52, 0.37, 0.23), "wood2": (0.37, 0.26, 0.15), "metal": "iron"}),
                 "Kerb": ("siege", {"name": "HQ_TrebKerb", "wood": (0.46, 0.32, 0.19), "wood2": (0.33, 0.22, 0.13), "metal": "iron"}),
                 "Gabions": ("basket", {}),
                 "Fill": ("ground", {"name": "HQ_GabionEarth"}),
                 "Balls": ("limestone", {"name": "HQ_SpareBalls"}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and FLOOR_R + KERB_W - 0.01 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
