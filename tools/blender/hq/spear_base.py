"""Spear Guard base: a guard post at a city gate. A square platform of dressed limestone blocks (two courses, a step at
the front, flagstones on top) on a grassy mound; behind him a pair of plastered "horns of consecration" with a red
band; a wooden rack with two spare spears, a tall storage jar bound with painted bands, papyrus, pebbles (distance
fields) + grass, flowers and papyrus heads (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b

GROUND_R = 1.32
GROUND_TOP = 0.16
PC = v3((0.0, 0.04, 0.0))          # platform centre
PH = 0.6                           # platform half size
COURSES = [(0.04, 0.205), (0.205, 0.365)]
TOP_Z = 0.4                        # flagstone top = where his feet stand
STAND = v3((0.0, 0.03, TOP_Z))
HORNS_C = v3((0.0, 0.44, TOP_Z))
RACK_C = v3((-0.86, 0.42, 0.0))
JAR_C = v3((0.88, -0.5, 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.05 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.035) * np.sin(a * 5 + 1.7) + F(0.02) * np.sin(a * 11 + 0.4) + F(0.02) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.05) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.09), 0), np.maximum(dz + F(0.09), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.09), dz + F(0.09)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.09)
    fd.add(Func(disc, (-1.5, -1.5, -0.25), (1.5, 1.5, 0.35),
                disp=lambda P: F(0.008) * NOISE(P * F(7)) + F(0.004) * NOISE(P * F(23)), disp_amp=0.014), 0.0)
    return fd


def _chip(seed):
    return lambda P: F(0.004) * NOISE(P * F(9) + F(seed)) + F(0.002) * NOISE(P * F(31) + F(seed * 2))


def platform_field():
    """Dressed limestone: two courses of blocks round a core, joints staggered, a step at the front, flagstones."""
    fd = Field("Stone")
    rs = np.random.RandomState(5)
    fd.add(RoundBox(PC + v3((0, 0, 0.19)), (PH - 0.02, PH - 0.02, 0.19), 0.02), 0.0)            # core
    for ci, (z0, z1) in enumerate(COURSES):
        zc, hz = (z0 + z1) / 2, (z1 - z0) / 2 - 0.004
        inset = 0.012 * ci
        for side in range(4):
            # walk along the side laying blocks of varied length
            u = -PH + inset + (0.12 if ci % 2 else 0.0)
            first = True
            while u < PH - inset - 0.04:
                L = rs.uniform(0.2, 0.32) if not first or ci % 2 == 0 else 0.12
                first = False
                L = min(L, PH - inset - u)
                c_u = u + L / 2
                half = (L / 2 - 0.006, 0.075, hz)
                o = PH - inset - 0.075
                c = {0: v3((c_u, -o, zc)), 1: v3((o, c_u, zc)), 2: v3((-c_u, o, zc)), 3: v3((-o, -c_u, zc))}[side] + PC
                R = euler(0, 0, side * math.pi / 2)
                fd.add(RoundBox(c, half, 0.014, R=R, disp=_chip(rs.uniform(0, 50)), disp_amp=0.006), 0.004)
                u += L
    # two steps in front
    fd.add(RoundBox(PC + v3((0.0, -PH - 0.1, 0.14)), (0.3, 0.11, 0.135), 0.016, disp=_chip(7.0), disp_amp=0.006), 0.004)
    fd.add(RoundBox(PC + v3((0.0, -PH - 0.27, 0.09)), (0.32, 0.09, 0.08), 0.016, disp=_chip(9.0), disp_amp=0.006), 0.004)
    # flagstones on top
    n = 4
    s = 2 * PH / n
    for i in range(n):
        for j in range(n):
            c = PC + v3((-PH + s * (i + 0.5) + rs.uniform(-0.01, 0.01), -PH + s * (j + 0.5) + rs.uniform(-0.01, 0.01),
                         TOP_Z - 0.025 + rs.uniform(-0.004, 0.004)))
            fd.add(RoundBox(c, (s / 2 - 0.008, s / 2 - 0.008, 0.026), 0.012, R=euler(0, 0, rs.uniform(-0.03, 0.03)),
                            disp=_chip(rs.uniform(0, 50)), disp_amp=0.005), 0.002)
    return fd


def horns_field():
    """Horns of consecration: a plastered block with two great horns curving up, a red painted band (label 5)."""
    fd = Field("Plaster")
    c = HORNS_C
    fd.add(RoundBox(c + v3((0, 0, 0.07)), (0.37, 0.1, 0.07), 0.022), 0.0)
    for sx in (-1, 1):
        base = c + v3((sx * 0.27, 0, 0.12))
        pts = [base, base + v3((sx * 0.03, 0.0, 0.16)), base + v3((sx * 0.09, 0.0, 0.34)), base + v3((sx * 0.17, 0.0, 0.47))]
        fd.add(Chain(pts, [0.088, 0.07, 0.046, 0.013], k=0.024), 0.035)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(c[2] + 0.08)) - F(0.026), c - 0.5, c + 0.6), 5)
    return fd


def wood_field():
    """A spear rack: two posts and two crossbars, the spare spears leaning in it."""
    fd = Field("Wood")
    bark = lambda P: F(0.003) * NOISE(P * np.array([40, 40, 8], F))
    g = ground_height(RACK_C[0], RACK_C[1])
    ax = norm(v3((0.35, -1.0, 0.0)))                  # the rack runs along this
    for s in (-0.2, 0.2):
        b = RACK_C + ax * s + v3((0, 0, g - 0.03))
        fd.add(RoundCone(b, b + v3((0, 0, 0.62)), 0.024, 0.021, disp=bark, disp_amp=0.004), 0.0)
    for z in (0.3, 0.56):
        a = RACK_C - ax * 0.24 + v3((0, 0, g + z))
        b = RACK_C + ax * 0.24 + v3((0, 0, g + z))
        fd.add(RoundCone(a, b, 0.016, 0.016, disp=bark, disp_amp=0.003), 0.006)
    for k, s in enumerate((-0.08, 0.1)):
        foot_p = RACK_C + ax * s + v3((0.14, 0.05, g + 0.0))
        top = RACK_C + ax * (s * 1.1) + v3((-0.06, -0.02, g + 1.25))
        fd.add(RoundCone(foot_p, top, 0.015, 0.014, disp=bark, disp_amp=0.002), 0.0)
    return fd


def spear_tops():
    g = ground_height(RACK_C[0], RACK_C[1])
    ax = norm(v3((0.35, -1.0, 0.0)))
    out = []
    for k, s in enumerate((-0.08, 0.1)):
        foot_p = RACK_C + ax * s + v3((0.14, 0.05, g + 0.0))
        top = RACK_C + ax * (s * 1.1) + v3((-0.06, -0.02, g + 1.25))
        out.append((foot_p, top))
    return out


def bronze_field():
    """The spare spears' leaf-shaped heads."""
    fd = Field("BronzeBits")
    for foot_p, top in spear_tops():
        d = norm(top - foot_p)
        side = norm(np.cross(d, v3((0, 0, 1))))
        fd.add(RoundCone(top - d * 0.02, top + d * 0.05, 0.019, 0.017), 0.0)
        fd.add(Ellipsoid(top + d * 0.15, (0.032, 0.007, 0.1), R=rot_from_axes(z_axis=d, x_axis=side)), 0.006)
        fd.add(Chain([top + d * 0.04, top + d * 0.26], [0.009, 0.003], k=0.004), 0.005)
    return fd


def jar_field():
    """A tall storage jar (label 5 = dark painted bands and a wavy line)."""
    fd = Field("Jar")
    g = ground_height(JAR_C[0], JAR_C[1])
    c = JAR_C + v3((0, 0, g + 0.24))
    fd.add(Ellipsoid(c, (0.15, 0.15, 0.22)), 0.0)
    fd.add(RoundCone(c + v3((0, 0, 0.14)), c + v3((0, 0, 0.27)), 0.09, 0.07), 0.05)
    fd.add(Torus(c + v3((0, 0, 0.27)), 0.072, 0.016), 0.01)
    fd.sub(Cylinder(c + v3((0, 0, 0.3)), 0.058, 0.1), 0.006)
    fd.add(Cylinder(JAR_C + v3((0, 0, g + 0.02)), 0.08, 0.06, rr=0.015), 0.04)
    for sx in (-1, 1):
        fd.add(Torus(c + v3((sx * 0.13, 0, 0.12)), 0.03, 0.01, R=rot_from_axes(z_axis=(1, 0, 0))), 0.006)
    for z in (-0.06, 0.07):
        fd.paint(Func(lambda P, z=z: np.abs(P[:, 2] - F(c[2] + z)) - F(0.013), c - 0.4, c + 0.4), 5)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(c[2]) - F(0.022) * np.sin(np.arctan2(P[:, 1] - F(c[1]), P[:, 0] - F(c[0])) * F(8))) - F(0.007),
                  c - 0.4, c + 0.4), 5)
    return fd


def _blocked(c, pad=0.0):
    if abs(c[0] - PC[0]) < PH + 0.12 + pad and abs(c[1] - PC[1]) < PH + 0.12 + pad:
        return True
    if abs(c[0] - PC[0]) < 0.44 + pad and PC[1] - PH - 0.42 - pad < c[1] < PC[1] - PH:
        return True
    if math.hypot(c[0] - RACK_C[0], c[1] - RACK_C[1]) < 0.34 + pad:
        return True
    if math.hypot(c[0] - JAR_C[0], c[1] - JAR_C[1]) < 0.24 + pad:
        return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(17)
    n = 0
    tries = 0
    while n < 16 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.75, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.026, 0.05), seed=300 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=21):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.72, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c):
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


PAPYRUS = [(1.0, 0.5, 0.9), (-0.98, -0.5, 2.6)]


def flower_geometry(seed=29):
    """A few flowers (kinds 0-2) and papyrus clumps crowned with bursts of thin rays (kind 3, the papyrus swatch)."""
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.8, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.05) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.2 for s in spots):
            continue
        spots.append((c, rs.randint(0, 3)))
    for c, kind in spots:
        base = v3((c[0], c[1], ground_height(c[0], c[1]) - 0.01))
        h = rs.uniform(0.1, 0.15)
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
            pv += [top + tilt * 0.004, top + dirk * 0.035 * 0.55 + sidek * 0.035 * 0.42, top + dirk * 0.035, top + dirk * 0.035 * 0.55 - sidek * 0.035 * 0.42]
            pf.append((b0, b0 + 1, b0 + 2, b0 + 3))
        out.append((pv, pf, 1, kind))
        cv = [top + R @ v3((math.cos(2 * math.pi * k / 6) * 0.012, math.sin(2 * math.pi * k / 6) * 0.012, 0.008)) for k in range(6)]
        cv.append(top + R @ v3((0, 0, 0.016)))
        out.append((cv, [(k, (k + 1) % 6, 6) for k in range(6)], 2, kind))
    for (x, y, a0) in PAPYRUS:
        for k in range(6):
            ang = a0 + k * 1.05
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.06)
            root = v3((x, y, 0)) + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.42, 0.62)
            d = norm(v3((math.cos(ang) * 0.14, math.sin(ang) * 0.14, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.016, v3((math.cos(ang), math.sin(ang), 0)) * 0.08, segs=4)
            out.append((sv, sf, 0, 0))
            top = root + d * h
            for j in range(11):
                aj = 2 * math.pi * j / 11 + k
                rd = norm(v3((math.cos(aj), math.sin(aj), 0)) * 0.9 + d * 0.5)
                rv, rf, _ = _b.blade_mesh(top, rd, rs.uniform(0.08, 0.11), 0.01, v3((0, 0, -0.35)), segs=2)
                out.append((rv, rf, 3, 3))
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Stone", platform_field(), 0.0045), ("Plaster", horns_field(), 0.004),
            ("Wood", wood_field(), 0.003), ("BronzeBits", bronze_field(), 0.0025), ("Jar", jar_field(), 0.003),
            ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Plaster", "Jar")
LOW_TARGETS = {"Ground": 1400, "Stone": 3600, "Plaster": 700, "Wood": 520, "BronzeBits": 260, "Jar": 600, "Pebbles": 420}
MAT_OVERRIDES = {"Stone": ("limestone", {"name": "HQ_Limestone"}),
                 "Plaster": ("plaster", {"name": "HQ_Plaster"}),
                 "BronzeBits": ("bronze", {"name": "HQ_BaseBronze"}),
                 "Jar": ("terracotta", {"name": "HQ_Pithos"})}
EXTRA_SWATCHES = [(0.56, 0.7, 0.24)]          # kind 3: papyrus heads
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not (abs(c.x - PC[0]) < PH + 0.05 and abs(c.y - PC[1]) < PH + 0.05))
