"""Torsion Catapult base: a round paved emplacement on a grassy mound. Limestone flags laid in rings round a socket
stone in the middle (the cart turns about it), a rim of big dressed blocks, every other one painted red, flush with the
paving (the wheels roll over all of it), the wheels' tracks worn pale and smooth into the flags; grass, flowers and a few
pebbles beyond the rim. Nothing on the paving stands taller than a flag: the whole cart sweeps it when the tower turns."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
import torsion as _t

GROUND_R = 1.32
GROUND_TOP = 0.1
FLOOR_R = 1.2                  # the paving's outer edge
TOP_Z = 0.16                   # the paving's top: where the wheels and his feet rest
STAND = v3((-_t.YAW_PIVOT[0], -_t.YAW_PIVOT[1], TOP_Z))
# rings of flags: (inner radius, outer radius, number of flags); the last ring is the rim of big blocks
RINGS = [(0.17, 0.48, 8), (0.48, 0.76, 14), (0.76, 1.02, 20), (1.02, FLOOR_R, 24)]
SOCKET_R = 0.17


def wheel_tracks():
    """Distances from the base's middle of the four wheels (the tracks they wear as the cart turns)."""
    out = []
    for wy in _t.WY:
        for sx in (-1, 1):
            out.append(math.hypot(_t.MX + sx * _t.WX - _t.YAW_PIVOT[0], wy - _t.YAW_PIVOT[1]))
    return out


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


def _chip(P):
    return F(0.0035) * NOISE(P * F(9)) + F(0.0018) * NOISE(P * F(31))


def ring_func(r0, r1, n, seed, rim=False):
    """One ring of flags: n annular sectors between r0 and r1 with joints between them, each a little tilted and set at
    its own height."""
    rs = np.random.RandomState(seed)
    ph0 = rs.uniform(0, 2 * math.pi)
    hz = (0.034 if rim else 0.028)
    dzs = rs.uniform(-0.004, 0.003, n).astype(F)
    tilt = rs.uniform(-0.012, 0.012, (n, 2)).astype(F)
    gap = F(0.0055)
    rr = F(0.008)
    step = 2 * math.pi / n
    def fn(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.sqrt(x * x + y * y)
        a = np.arctan2(y, x)
        u = (a - F(ph0)) / F(step)
        k = np.floor(u).astype(np.int64) % n
        da = (u - np.floor(u) - F(0.5)) * F(step)
        d_a = np.abs(da) * r - (F(step * 0.5) * r - gap)
        d_r = np.maximum(F(r0) + gap - r, r - (F(r1) - gap))
        rm = F((r0 + r1) / 2)
        top = F(TOP_Z) + dzs[k] + tilt[k, 0] * (r - rm) + tilt[k, 1] * da * r
        d_z = np.abs(z - (top - F(hz))) - F(hz)
        q = np.stack([d_a + rr, d_r + rr, d_z + rr], 1)
        out = np.sqrt((np.maximum(q, 0) ** 2).sum(1))
        return out + np.minimum(q.max(1), 0) - rr
    R = r1 + 0.02
    return Func(fn, (-R, -R, TOP_Z - 2 * hz - 0.02), (R, R, TOP_Z + 0.03), disp=_chip, disp_amp=0.006)


def stone_field():
    """The paving (limestone, label 0), the red-painted rim blocks (5) and the wheels' polished tracks (6)."""
    fd = Field("Stone")
    fd.add(Cylinder(v3((0, 0, TOP_Z - 0.03)), SOCKET_R - 0.005, 0.06, rr=0.01, disp=_chip, disp_amp=0.006), 0.0)
    fd.sub(Cylinder(v3((0, 0, TOP_Z)), 0.05, 0.03, rr=0.008), 0.006)                     # the pivot's socket
    for i, (r0, r1, n) in enumerate(RINGS):
        fd.add(ring_func(r0, r1, n, 40 + i, rim=(i == len(RINGS) - 1)), 0.0)
    r0, r1, n = RINGS[-1]
    rs = np.random.RandomState(40 + len(RINGS) - 1)
    ph0 = rs.uniform(0, 2 * math.pi)
    def red(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        k = np.floor((a - F(ph0)) / F(2 * math.pi / n)).astype(np.int64) % n
        return np.where(k % 2 == 0, F(r0 + 0.004) - r, F(1.0))
    fd.paint(Func(red, (-1.5, -1.5, 0.0), (1.5, 1.5, 0.3)), 5)
    for rt in wheel_tracks():
        fd.paint(Func(lambda P, rt=rt: np.maximum(np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(rt)) - F(0.03),
                                                  F(TOP_Z - 0.012) - P[:, 2]), (-1.5, -1.5, 0.0), (1.5, 1.5, 0.3)), 6)
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
    return [("Ground", ground_field(), 0.008), ("Stone", stone_field(), 0.0042), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Stone",)
LOW_TARGETS = {"Ground": 1300, "Stone": 4200, "Pebbles": 300}
MAT_OVERRIDES = {"Stone": ("limestone", {"name": "HQ_Paving"}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and FLOOR_R - 0.01 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
