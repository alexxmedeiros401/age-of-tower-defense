"""Knight base: a corner of the castle's training yard. A round floor of cobbles (rounded stones packed close, a few
darker, worn smooth where he stands) inside a kerb of curved granite blocks, on a grassy mound; behind him on his left a
pell, the thick oak post knights hack at, scarred with cuts, set in a stone; behind him on his right a weapon rack (two
posts and a rail) with a halberd and a flanged mace standing in it; behind him a banner hanging from a crossbar on a tall
pole, blue with a yellow cross, swallow-tailed, a yellow fringe; grass and wild flowers round about (distance fields +
direct low-poly geometry for the grass and flowers)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
from sunpriest_base import ring_func
from crossbowman_base import _bloom

GROUND_R = 1.32
GROUND_TOP = 0.1
TOP_Z = 0.22                       # the cobbles' tops = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
YARD_R = 0.8                       # the cobbled floor
KERB_R = 0.96
KERB_TOP = TOP_Z + 0.03
PELL_C = v3((0.62, 0.62, 0.0))     # the pell (behind him, on his left)
RACK_C = v3((-0.6, 0.6, 0.0))      # the weapon rack (behind him, on his right)
RACK_AX = norm(v3((1.0, -0.62, 0.0)))     # along its rail
POLE_C = v3((0.1, 0.92, 0.0))      # the banner's pole
POLE_H = 1.95


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 0.3) + F(0.02) * np.sin(a * 11 + 1.7) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.03) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _chip(P):
    return F(0.0035) * NOISE(P * F(9)) + F(0.0018) * NOISE(P * F(31))


def _hash2(ix, iy, s):
    h = np.sin(ix * F(127.1) + iy * F(311.7) + F(s)) * F(43758.5453)
    return h - np.floor(h)


CELL = 0.072


def cobble_height(P):
    """Packed cobbles: each cell of a jittered grid holds a rounded stone; returns (height above the bed, label mask)."""
    x, y = P[:, 0] / F(CELL), P[:, 1] / F(CELL)
    ix0, iy0 = np.floor(x), np.floor(y)
    best = np.full(len(P), F(9.0))
    hid = np.zeros(len(P), F)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx, cy = ix0 + F(dx), iy0 + F(dy)
            jx = _hash2(cx, cy, 1.3) * F(0.7) + F(0.15)
            jy = _hash2(cx, cy, 7.9) * F(0.7) + F(0.15)
            d = np.sqrt((x - cx - jx) ** 2 + (y - cy - jy) ** 2)
            use = d < best
            best = np.where(use, d, best)
            hid = np.where(use, _hash2(cx, cy, 3.1), hid)
    r = best * F(CELL)
    h = F(0.016) * np.sqrt(np.clip(F(1) - (r / F(0.04)) ** 2, 0, 1)) + F(0.003) * hid
    return h, hid


def cobbles_field():
    """Grey cobbles (granite, label 0; a few darker, 7), packed in a disc inside the kerb, their tops worn smooth where
    he stands (6)."""
    fd = Field("Cobbles")
    def fn(P):
        h, hid = cobble_height(P)
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        top = F(TOP_Z - 0.012) + h
        dz = np.maximum(P[:, 2] - top, F(GROUND_TOP - 0.05) - P[:, 2])
        return np.maximum(dz * F(0.8), r - F(YARD_R + 0.01))
    R = YARD_R + 0.05
    fd.add(Func(fn, (-R, -R, GROUND_TOP - 0.08), (R, R, TOP_Z + 0.03)), 0.0)
    fd.paint(Func(lambda P: F(0.82) - cobble_height(P)[1], (-R, -R, GROUND_TOP - 0.08), (R, R, TOP_Z + 0.03)), 7)
    fd.paint(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(0.3), F(TOP_Z - 0.004) - P[:, 2]),
                  (-R, -R, GROUND_TOP - 0.08), (R, R, TOP_Z + 0.03)), 6)
    return fd


def kerb_field():
    """Curved granite blocks round the yard (label 0; weathered dark low down, 7)."""
    fd = Field("Kerb")
    fd.add(ring_func(YARD_R, KERB_R, 14, 411, KERB_TOP, (KERB_TOP - GROUND_TOP + 0.06) / 2, jitter=0.7, chip=_chip), 0.0)
    fd.paint(Func(lambda P: (P[:, 2] - F(GROUND_TOP + 0.04)) + F(0.03) * NOISE(P * F(5)), (-1.1, -1.1, -0.1), (1.1, 1.1, 0.4)), 7)
    return fd


def _ground_at(c, sink=0.03):
    return v3((c[0], c[1], ground_height(c[0], c[1]) - sink))


def pell_stone():
    return _ground_at(PELL_C, 0.0)


def wood_field():
    """Oak (wood, label 0 / 11 upright grain): the pell, hacked with cuts; the weapon rack's posts and rail; the
    banner's pole and crossbar; the halberd's and the mace's hafts."""
    fd = Field("Wood")
    g = pell_stone()
    b0 = g + v3((0, 0, 0.08))
    top = b0 + v3((0.0, 0.0, 0.92))
    fd.add(RoundBox((b0 + top) / 2, (0.068, 0.068, 0.46), 0.012, R=euler(0, 0, 0.3),
                    disp=lambda P: F(0.0018) * NOISE(P * np.array([40, 40, 8], F)), disp_amp=0.003), 0.0, 11)
    rs = np.random.RandomState(17)
    for k in range(9):                                                            # cuts from his blows
        z = rs.uniform(0.35, 0.85)
        a = rs.uniform(-1.2, 1.2) + math.pi * 1.25
        d = v3((math.cos(a), math.sin(a), 0.0))
        c = b0 + v3((0, 0, z)) + d * 0.07
        tilt = rs.uniform(-0.6, 0.6)
        fd.sub(RoundBox(c, (0.05, 0.012, 0.003), 0.0, R=rot_from_axes(z_axis=norm(v3((-d[1], d[0], 0)) * math.sin(tilt) + v3((0, 0, math.cos(tilt)))),
                                                                     y_axis=d)), 0.002)
    # the weapon rack: two posts and a rail
    rg = _ground_at(RACK_C)
    side = norm(np.cross(RACK_AX, v3((0, 0, 1))))
    for s in (-1, 1):
        p0 = rg + RACK_AX * (s * 0.22)
        fd.add(Chain([p0, p0 + v3((0, 0, 0.62))], [0.024, 0.022], k=0.002), 0.0, 11)
    fd.add(Chain([rg + RACK_AX * -0.26 + v3((0, 0, 0.55)), rg + RACK_AX * 0.26 + v3((0, 0, 0.55))], [0.019, 0.019], k=0.002), 0.004)
    fd.add(Chain([rg + RACK_AX * -0.26 + v3((0, 0, 0.12)), rg + RACK_AX * 0.26 + v3((0, 0, 0.12))], [0.016, 0.016], k=0.002), 0.004)
    # the hafts: a halberd and a mace standing in the rack, leaning back against the rail
    for off, L, nm in ((-0.1, 1.55, "halberd"), (0.11, 0.62, "mace")):
        f0 = rg + RACK_AX * off + side * 0.05 + v3((0, 0, 0.03))
        lean = norm(v3((0, 0, 1)) - side * 0.12)
        fd.add(Chain([f0, f0 + lean * L], [0.016, 0.015], k=0.002), 0.004)
    # the banner's pole and crossbar
    pg = _ground_at(POLE_C, 0.02)
    fd.add(Chain([pg, pg + v3((0, 0, POLE_H))], [0.024, 0.019], k=0.002), 0.0, 11)
    ct = pg + v3((0, 0, POLE_H - 0.06))
    fd.add(Chain([ct + v3((-0.22, -0.02, 0)), ct + v3((0.22, -0.02, 0))], [0.013, 0.013], k=0.002), 0.004)
    return fd


def iron_field():
    """Forged iron: the halberd's head (an axe blade, a spike and a hook), the mace's flanged head, the pole's finial,
    nails in the pell."""
    fd = Field("Iron")
    rg = _ground_at(RACK_C)
    side = norm(np.cross(RACK_AX, v3((0, 0, 1))))
    lean = norm(v3((0, 0, 1)) - side * 0.12)
    # halberd
    f0 = rg + RACK_AX * -0.1 + side * 0.05 + v3((0, 0, 0.03))
    top = f0 + lean * 1.55
    fd.add(RoundCone(top, top + lean * 0.2, 0.014, 0.003), 0.003)                              # the spike
    blade_c = top - lean * 0.06 + RACK_AX * -0.07
    fd.add(RoundBox(blade_c, (0.07, 0.006, 0.08), 0.004, R=rot_from_axes(z_axis=lean, x_axis=RACK_AX)), 0.004)
    fd.add(RoundCone(top - lean * 0.06 + RACK_AX * 0.02, top - lean * 0.02 + RACK_AX * 0.1, 0.012, 0.004), 0.003)   # the hook
    fd.add(RoundCone(top - lean * 0.16, top + lean * 0.02, 0.019, 0.017), 0.003)               # its socket
    # the flanged mace
    m0 = rg + RACK_AX * 0.11 + side * 0.05 + v3((0, 0, 0.03))
    mh = m0 + lean * 0.66
    for k in range(7):
        a = 2 * math.pi * k / 7
        d = RACK_AX * math.cos(a) + side * math.sin(a)
        fd.add(RoundBox(mh + d * 0.03, (0.03, 0.005, 0.05), 0.004, R=rot_from_axes(z_axis=lean, x_axis=d)), 0.004)
    fd.add(Sphere(mh, 0.026), 0.006)
    fd.add(Sphere(mh + lean * 0.06, 0.013), 0.004)
    # the pole's finial
    pg = _ground_at(POLE_C, 0.02)
    tip = pg + v3((0, 0, POLE_H))
    fd.add(RoundCone(tip, tip + v3((0, 0, 0.1)), 0.02, 0.003), 0.003)
    fd.add(Sphere(tip + v3((0, 0, 0.012)), 0.022), 0.003)
    # nails in the pell
    g = pell_stone()
    for z in (0.5, 0.78):
        fd.add(Sphere(g + v3((0, 0, 0.08 + z)) + v3((-0.05, -0.05, 0.0)), 0.009), 0.002)
    return fd


def stone_field():
    """The pell's stone: a rough granite block it is set in."""
    fd = Field("Stone")
    g = pell_stone()
    fd.add(RoundBox(g + v3((0, 0, 0.04)), (0.14, 0.13, 0.07), 0.025, R=euler(0, 0, 0.3), disp=_chip, disp_amp=0.006), 0.0)
    return fd


def banner_field():
    """The banner: blue wool (label 0), a yellow cross (6), a yellow fringe along its tails (5), hanging from the
    crossbar in soft folds and ending in two tails."""
    fd = Field("Banner")
    pg = _ground_at(POLE_C, 0.02)
    ct = pg + v3((0, 0, POLE_H - 0.06))
    top = ct + v3((0.0, -0.05, -0.02))
    W, L = 0.2, 0.78
    def flag(P):
        q = P - top.astype(F)
        x, y, z = q[:, 0], q[:, 1], -q[:, 2]                               # z: down the banner
        fold = F(0.012) * np.sin(x * F(28) + F(0.4)) * (F(0.5) + z)
        d = np.maximum(np.maximum(np.abs(x) - F(W), np.maximum(-z, z - F(L))), np.abs(y - fold) - F(0.006))
        notch = (z - F(L - 0.14)) * F(0.6) - np.abs(x)                    # the swallow-tail: a V cut up its middle
        return np.maximum(d, notch)
    lo = top - v3((0.3, 0.1, L + 0.05))
    hi = top + v3((0.3, 0.1, 0.05))
    fd.add(Func(flag, lo, hi), 0.0)
    def cross(P):
        q = P - top.astype(F)
        x, z = q[:, 0], -q[:, 2]
        v = np.maximum(np.abs(x) - F(0.035), np.maximum(F(0.06) - z, z - F(L - 0.16)))
        h = np.maximum(np.abs(z - F(0.28)) - F(0.035), np.abs(x) - F(W - 0.04))
        return np.minimum(v, h)
    fd.paint(Func(cross, lo, hi), 6)
    fd.paint(Func(lambda P: F(L - 0.06) - (-(P[:, 2] - F(top[2]))), lo, hi), 5)
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < KERB_R + 0.05 + pad:
        return True
    for p, r in ((PELL_C, 0.2), (RACK_C, 0.35), (POLE_C, 0.08)):
        if math.hypot(c[0] - p[0], c[1] - p[1]) < r + pad:
            return True
    return False


def grass_geometry(seed=53):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 28 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(KERB_R + 0.04, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.13 for t in tufts):
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
            outv = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(outv * rs.uniform(0.15, 0.45) + v3((0, 0, 1)))
            L = rs.uniform(0.12, 0.22) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.042), outv * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=59):
    """Daisies (swatch 0) and buttercups (1) in the grass round the yard."""
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 8 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(KERB_R + 0.06, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.03) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.2 for s in spots):
            continue
        spots.append((c, 0 if len(spots) % 2 else 1))
    for c, col in spots:
        for k in range(rs.randint(3, 6)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.07)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.07, 0.13)
            d = norm(v3((math.cos(ang) * 0.35, math.sin(ang) * 0.35, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, col))
            tilt = norm(v3((rs.uniform(-0.4, 0.4), rs.uniform(-0.4, 0.4), 1.0)))
            _bloom(out, root + d * h, tilt, 0.026, col)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Cobbles", cobbles_field(), 0.0036), ("Kerb", kerb_field(), 0.0042),
            ("Wood", wood_field(), 0.0026), ("Iron", iron_field(), 0.0022), ("Stone", stone_field(), 0.0036),
            ("Banner", banner_field(), 0.0026)]


REGION_PARTS = ("Cobbles", "Kerb", "Wood", "Banner")
LOW_TARGETS = {"Ground": 1500, "Cobbles": 3400, "Kerb": 1200, "Wood": 1300, "Iron": 700, "Stone": 300, "Banner": 500}
_BLUE = (0.14, 0.27, 0.62)
_YELLOW = (0.9, 0.68, 0.16)
MAT_OVERRIDES = {"Cobbles": ("granite", {"name": "HQ_Cobbles", "base": (0.48, 0.47, 0.46), "feld": (0.6, 0.58, 0.56),
                                         "quartz": (0.55, 0.55, 0.56), "mica": (0.12, 0.12, 0.13)}),
                 "Kerb": ("granite", {"name": "HQ_YardKerb", "base": (0.52, 0.5, 0.48), "feld": (0.64, 0.6, 0.56),
                                      "quartz": (0.58, 0.57, 0.56), "mica": (0.12, 0.12, 0.13)}),
                 "Wood": ("siege", {"name": "HQ_YardWood", "wood": (0.5, 0.34, 0.2), "wood2": (0.36, 0.23, 0.13),
                                    "red": _YELLOW, "blue": _BLUE, "metal": "iron"}),
                 "Iron": ("iron", {"name": "HQ_YardIron"}),
                 "Stone": ("stone", {"name": "HQ_PellStone"}),
                 "Banner": ("wool", {"name": "HQ_YardBanner", "base": _BLUE, "border": _YELLOW, "stripe": _YELLOW})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035 and r > KERB_R + 0.02
    return n.z > 0.55 and on_ground
