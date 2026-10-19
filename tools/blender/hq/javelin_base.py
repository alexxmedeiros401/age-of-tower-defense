"""Javelin Thrower base: a lookout on a hill fort's rampart. A round platform of dry-stone walling (flat grey slabs laid
in courses without mortar, turf on top) on a grassy mound; behind him two sharpened palisade stakes lashed to a
crossbar with a sheaf of javelins leaning on it, and a round painted shield with a bronze boss leaning on the stones;
pebbles (distance fields) + grass, heather and gorse (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b

GROUND_R = 1.32
GROUND_TOP = 0.16
PC = v3((0.0, 0.03, 0.0))          # platform centre
PR = 0.6                           # platform radius
COURSES = [(0.08, 0.17), (0.17, 0.26), (0.26, 0.35), (0.35, 0.43)]
TOP_Z = 0.46                       # turf top = where his feet stand
STAND = v3((0.0, 0.03, TOP_Z))
STAKES = [v3((-0.3, 1.0, 0.0)), v3((0.24, 1.04, 0.0))]
Z_BAR = 0.78                       # the crossbar's height
SHIELD_C = v3((0.7, -0.3, 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.05 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    """The grassy mound, and the turf on top of the platform."""
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
    def turf(P):
        q = P - PC.astype(F)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        top = F(TOP_Z) + F(0.012) * np.clip(1 - (r / F(PR)) ** 2, 0, 1)
        return np.maximum(r - F(PR - 0.03), np.maximum(P[:, 2] - top, F(TOP_Z - 0.07) - P[:, 2]))
    fd.add(Func(turf, PC + v3((-0.7, -0.7, 0.2)), PC + v3((0.7, 0.7, 0.45)),
                disp=lambda P: F(0.004) * NOISE(P * F(12)), disp_amp=0.006), 0.0)
    return fd


def _chip(seed):
    return lambda P: F(0.005) * NOISE(P * F(9) + F(seed)) + F(0.0025) * NOISE(P * F(31) + F(seed * 2))


def platform_field():
    """Dry-stone walling: flat slabs of uneven length laid round the platform in three courses, the joints staggered and
    open (no mortar), a few wedged in on edge; a capping course of slabs round the turf."""
    fd = Field("Stone")
    rs = np.random.RandomState(7)
    fd.add(Cylinder(PC + v3((0, 0, (TOP_Z - 0.03) / 2)), PR - 0.07, TOP_Z - 0.03, rr=0.02), 0.0)      # the earth core
    for ci, (z0, z1) in enumerate(COURSES):
        a = rs.uniform(0, 0.3) + ci * 0.17
        while a < 2 * math.pi - 0.05:
            L = rs.uniform(0.17, 0.3)
            da = L / PR
            if a + da > 2 * math.pi:
                da = 2 * math.pi - a
                L = da * PR
            if L < 0.06:
                break
            mid = a + da / 2
            out = v3((math.cos(mid), math.sin(mid), 0))
            tan = v3((-math.sin(mid), math.cos(mid), 0))
            h = (z1 - z0) / 2 - 0.006 - rs.uniform(0, 0.01)
            c = PC + out * (PR - 0.06 + rs.uniform(-0.008, 0.008)) + v3((0, 0, (z0 + z1) / 2 + rs.uniform(-0.006, 0.006)))
            R = rot_from_axes(x_axis=tan, y_axis=out) @ euler(rs.uniform(-0.05, 0.05), rs.uniform(-0.04, 0.04), 0)
            fd.add(RoundBox(c, (L / 2 - 0.008, 0.07, h), 0.016, R=R, disp=_chip(rs.uniform(0, 50)), disp_amp=0.007), 0.004)
            a += da
    # the capping slabs round the turf, a little proud of it
    a = 0.1
    while a < 2 * math.pi - 0.1:
        L = rs.uniform(0.2, 0.28)
        da = L / (PR - 0.05)
        mid = a + da / 2
        out = v3((math.cos(mid), math.sin(mid), 0))
        tan = v3((-math.sin(mid), math.cos(mid), 0))
        c = PC + out * (PR - 0.07) + v3((0, 0, TOP_Z - 0.02))
        R = rot_from_axes(x_axis=tan, y_axis=out) @ euler(rs.uniform(-0.06, 0.06), rs.uniform(-0.05, 0.05), 0)
        fd.add(RoundBox(c, (L / 2 - 0.012, 0.075, 0.026), 0.014, R=R, disp=_chip(rs.uniform(0, 50)), disp_amp=0.006), 0.004)
        a += da
    # two steps at the front
    fd.add(RoundBox(PC + v3((0.0, -PR - 0.14, 0.15)), (0.24, 0.08, 0.05), 0.02, disp=_chip(3.0), disp_amp=0.007), 0.004)
    fd.add(RoundBox(PC + v3((0.0, -PR - 0.04, 0.28)), (0.22, 0.07, 0.05), 0.02, disp=_chip(5.0), disp_amp=0.007), 0.004)
    return fd


def stake_top(c):
    g = ground_height(c[0], c[1])
    return c + v3((0, 0, g + (1.05 if c[0] < 0 else 1.16)))


def crossbar():
    a = v3((STAKES[0][0] - 0.12, STAKES[0][1] - 0.05, Z_BAR + 0.02))
    b = v3((STAKES[1][0] + 0.12, STAKES[1][1] - 0.05, Z_BAR - 0.02))
    return a, b


def sheaf():
    """The javelins leaning on the crossbar: (butt, direction, length)."""
    a, b = crossbar()
    out = []
    for x in (-0.13, -0.03, 0.07):
        butt = v3((x - 0.02, 0.72, ground_height(x, 0.72)))
        u = (x - a[0]) / (b[0] - a[0])
        rest = lerp(a, b, u) + v3((0, -0.044, 0.0))
        out.append((butt, norm(rest - butt), 1.2))
    return out


def wood_field():
    """Two palisade stakes, sharpened, lashed to a crossbar (rope, label 8); the sheaf of javelins' ash shafts; the
    round shield (planks, 0) painted red (5) with a blue ring (7) round a bronze boss, a bronze rim (6)."""
    fd = Field("Wood")
    bark = lambda P: F(0.004) * NOISE(P * np.array([40, 40, 8], F))
    tops = []
    for c in STAKES:
        g = ground_height(c[0], c[1])
        top = stake_top(c)
        tops.append(top)
        fd.add(RoundCone(c + v3((0, 0, g - 0.05)), top - v3((0, 0, 0.12)), 0.055, 0.05, disp=bark, disp_amp=0.005), 0.0, 11)
        fd.add(RoundCone(top - v3((0, 0, 0.13)), top, 0.05, 0.004), 0.01, 11)                           # sharpened point
    a, b = crossbar()
    fd.add(RoundCone(a, b, 0.032, 0.03, disp=bark, disp_amp=0.004), 0.004, 10)
    for c in STAKES:
        p = v3((c[0], c[1] - 0.04, Z_BAR))
        for k in range(3):
            fd.add(Torus(p + v3((0, 0, (k - 1) * 0.022)), 0.058, 0.009, R=rot_from_axes(z_axis=(0.3, 0.2, 1))), 0.003, 8)
    for butt, d, L in sheaf():
        fd.add(Chain([butt, butt + d * (L - 0.2)], [0.012, 0.0125], k=0.0), 0.0, 11)
    # the shield, leaning on the stones at his left side
    g = ground_height(SHIELD_C[0], SHIELD_C[1])
    N = norm(v3((0.62, -0.55, 0.35)))
    U = norm(np.cross(N, v3((0, 0, 1))))
    U = norm(np.cross(U, N))
    if U[2] < 0:
        U = -U
    C = SHIELD_C + v3((0, 0, g + 0.25))
    Rr = rot_from_axes(z_axis=N, y_axis=U)
    fd.add(Cylinder(C, 0.25, 0.026, rr=0.01, R=Rr), 0.0)
    fd.add(Torus(C + N * 0.008, 0.245, 0.012, R=Rr), 0.004, 6)
    fd.add(Inter(Sphere(C + N * 0.0, 0.065), Plane(C + N * 0.012, -N), 0.004), 0.006, 6)
    fd.add(Torus(C + N * 0.016, 0.064, 0.008, R=Rr), 0.003, 6)
    def paint(P, lo, hi_):
        q = P - C.astype(F)
        h = q @ N.astype(F)
        rr = np.sqrt(np.maximum((q * q).sum(1) - h * h, 0))
        return np.maximum(np.maximum(F(lo) - rr, rr - F(hi_)), F(0.006) - h)
    fd.paint(Func(lambda P: paint(P, 0.0, 0.23), C - 0.35, C + 0.35), 5)
    fd.paint(Func(lambda P: paint(P, 0.13, 0.175), C - 0.35, C + 0.35), 7)
    return fd


def iron_field():
    """The leaf-shaped iron heads of the javelins in the sheaf."""
    fd = Field("BaseIron")
    for butt, d, L in sheaf():
        side = norm(np.cross(d, v3((0, 0, 1))))
        s0 = butt + d * (L - 0.21)
        fd.add(RoundCone(s0, s0 + d * 0.07, 0.015, 0.0105), 0.0)
        fd.add(Ellipsoid(butt + d * (L - 0.065), (0.025, 0.0055, 0.07), R=rot_from_axes(z_axis=d, x_axis=side)), 0.005)
        fd.add(Chain([s0 + d * 0.06, butt + d * (L - 0.004)], [0.0085, 0.0025], k=0.004), 0.005)
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0] - PC[0], c[1] - PC[1]) < PR + 0.1 + pad:
        return True
    if abs(c[0] - PC[0]) < 0.32 + pad and PC[1] - PR - 0.3 - pad < c[1] < PC[1] - PR:
        return True
    for s in STAKES:
        if math.hypot(c[0] - s[0], c[1] - s[1]) < 0.12 + pad:
            return True
    if math.hypot(c[0] - SHIELD_C[0], c[1] - SHIELD_C[1]) < 0.3 + pad:
        return True
    for butt, d, L in sheaf():
        if math.hypot(c[0] - butt[0], c[1] - butt[1]) < 0.08 + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(19)
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
        fd.add(Stone(p, rs.uniform(0.026, 0.05), seed=320 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=23):
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


def _bloom(out, top, tilt, size, kind_col):
    """A small five-petalled bloom (kind 1, colour swatch `kind_col`) with a centre (kind 2)."""
    R = rot_from_axes(z_axis=tilt)
    pv, pf = [], []
    for k in range(5):
        a = 2 * math.pi * k / 5
        dirk = R @ v3((math.cos(a), math.sin(a), 0.15))
        sidek = R @ v3((-math.sin(a), math.cos(a), 0))
        b0 = len(pv)
        pv += [top + tilt * 0.003, top + dirk * size * 0.55 + sidek * size * 0.42, top + dirk * size, top + dirk * size * 0.55 - sidek * size * 0.42]
        pf.append((b0, b0 + 1, b0 + 2, b0 + 3))
    out.append((pv, pf, 1, kind_col))
    cv = [top + R @ v3((math.cos(2 * math.pi * k / 6) * size * 0.3, math.sin(2 * math.pi * k / 6) * size * 0.3, 0.006)) for k in range(6)]
    cv.append(top + R @ v3((0, 0, 0.012)))
    out.append((cv, [(k, (k + 1) % 6, 6) for k in range(6)], 2, kind_col))


def flower_geometry(seed=31):
    """Heather: low clumps of stems spiked with purple bells (swatch 2); a few yellow gorse blooms (swatch 1)."""
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 7 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.78, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.04) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.22 for s in spots):
            continue
        spots.append((c, 2 if len(spots) % 3 else 1))
    for c, col in spots:
        n_stem = rs.randint(5, 9) if col == 2 else rs.randint(3, 5)
        for k in range(n_stem):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.07)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.09, 0.16)
            d = norm(v3((math.cos(ang) * 0.35, math.sin(ang) * 0.35, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.011, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, col))
            top = root + d * h
            nb = 3 if col == 2 else 1
            for j in range(nb):
                p = root + d * h * (1.0 - 0.22 * j) + v3((rs.uniform(-0.01, 0.01), rs.uniform(-0.01, 0.01), 0))
                tilt = norm(v3((rs.uniform(-0.5, 0.5), rs.uniform(-0.5, 0.5), 1.0)))
                _bloom(out, p, tilt, 0.022 if col == 2 else 0.032, col)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Stone", platform_field(), 0.0045), ("Wood", wood_field(), 0.003),
            ("BaseIron", iron_field(), 0.0022), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Wood",)
LOW_TARGETS = {"Ground": 1500, "Stone": 4200, "Wood": 1300, "BaseIron": 240, "Pebbles": 420}
MAT_OVERRIDES = {"Stone": ("stone", {"name": "HQ_DryStone", "moss": True}),
                 "Wood": ("siege", {"name": "HQ_FortWood", "wood": (0.5, 0.34, 0.2), "wood2": (0.36, 0.23, 0.12)}),
                 "BaseIron": ("iron", {"name": "HQ_BaseIron"})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035 and math.hypot(c.x - PC[0], c.y - PC[1]) > PR + 0.02
    on_turf = math.hypot(c.x - PC[0], c.y - PC[1]) < PR - 0.17 and abs(c.z - TOP_Z) < 0.03
    step = abs(c.x) < 0.3 and -0.86 < c.y < -0.5
    return n.z > 0.55 and (on_ground or on_turf) and not step
