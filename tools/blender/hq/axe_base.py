"""Axe Warrior base: the wood-yard of a hill fort. A platform of logs laid in an eight-sided ring, three courses high, their
ends crossing at the corners, packed with earth and turf, on a grassy mound; behind him a curved panel of wattle
(withies woven between stakes); a big chopping stump with a hand axe bitten into it, a stack of split firewood, a few
chips; pebbles (distance fields) + grass and flowers (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b

GROUND_R = 1.32
GROUND_TOP = 0.16
PC = v3((0.0, 0.03, 0.0))          # platform centre
PR = 0.62                          # the log ring's radius (to the logs' middles)
LOG_R = 0.055
COURSES = 3
TOP_Z = 0.44                       # turf top = where his feet stand
STAND = v3((0.0, 0.03, TOP_Z))
STUMP_C = v3((0.86, -0.42, 0.0))
WOOD_C = v3((-0.86, -0.36, 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.05 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    """The grassy mound, and the turf inside the log ring."""
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.035) * np.sin(a * 5 + 0.7) + F(0.02) * np.sin(a * 11 + 1.4) + F(0.02) * NOISE(P * F(3))
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
        return np.maximum(r - F(PR - 0.02), np.maximum(P[:, 2] - top, F(TOP_Z - 0.08) - P[:, 2]))
    fd.add(Func(turf, PC + v3((-0.75, -0.75, 0.25)), PC + v3((0.75, 0.75, 0.52)),
                disp=lambda P: F(0.004) * NOISE(P * F(12)), disp_amp=0.006), 0.0)
    return fd


def _bark(seed):
    return lambda P: F(0.004) * NOISE(P * np.array([30, 30, 30], F) + F(seed)) + F(0.002) * NOISE(P * F(70) + F(seed))


def ring_corner(k, course):
    """Corner k of the eight-sided ring (each course turned half a side, so the logs' ends cross)."""
    a = 2 * math.pi * (k + 0.5 * (course % 2)) / 8 + math.pi / 8
    return PC + v3((math.cos(a), math.sin(a), 0)) * (PR / math.cos(math.pi / 8))


def logs_field():
    """The log ring (bark 0, the sawn ends 5), the chopping stump, the firewood stack (split faces 5) and the wattle
    panel (stakes 0, withies 7), the hand axe's haft (5) and head (6)."""
    fd = Field("Wood")
    rs = np.random.RandomState(9)
    fd.add(Cylinder(PC + v3((0, 0, (TOP_Z - 0.04) / 2)), PR - 0.04, TOP_Z - 0.04, rr=0.02), 0.0)          # the earth fill
    for course in range(COURSES):
        z = 0.12 + course * (2 * LOG_R - 0.012)
        for k in range(8):
            a = ring_corner(k, course)
            b = ring_corner(k + 1, course)
            d = norm(b - a)
            a2 = a - d * 0.07 + v3((0, 0, z))
            b2 = b + d * 0.07 + v3((0, 0, z))
            r = LOG_R * rs.uniform(0.92, 1.08)
            fd.add(RoundCone(a2, b2, r, r * 0.95, disp=_bark(rs.uniform(0, 50)), disp_amp=0.006), 0.004)
            for e in (a2, b2):                                                          # the sawn ends
                fd.paint(Inter(Sphere(e, r + 0.02), Plane(e - d * 0.012 * (1 if e is b2 else -1), -d if e is b2 else d), 0.0), 5)
    # the stump: a broad round of oak with roots spreading into the ground, a hand axe bitten into its top
    g = ground_height(STUMP_C[0], STUMP_C[1])
    top = STUMP_C + v3((0, 0, g + 0.3))
    fd.add(Cylinder(STUMP_C + v3((0, 0, g + 0.14)), 0.2, 0.32, rr=0.03, disp=_bark(3.0), disp_amp=0.008), 0.0)
    for j in range(5):
        aa = 2 * math.pi * j / 5 + 0.4
        o = v3((math.cos(aa), math.sin(aa), 0))
        fd.add(RoundCone(STUMP_C + o * 0.16 + v3((0, 0, g + 0.1)), STUMP_C + o * 0.32 + v3((0, 0, g - 0.02)), 0.07, 0.025,
                         disp=_bark(5.0 + j), disp_amp=0.006), 0.05)
    fd.paint(Func(lambda P: (top[2] - F(0.012)) - P[:, 2], top - 0.3, top + 0.1), 5)
    cut = norm(v3((0.6, -0.8, 0.0)))
    hb = top + v3((0.02, 0.0, -0.02))
    hd = norm(v3((-0.5, 0.45, 0.75)))                                                   # the haft, up out of the cut
    fd.add(RoundCone(hb + hd * 0.02, hb + hd * 0.42, 0.016, 0.014), 0.0, 5)
    side = norm(np.cross(hd, cut))
    fd.add(RoundBox(hb + hd * 0.0 + cut * 0.02, (0.006, 0.07, 0.045), 0.006, R=rot_from_axes(x_axis=side, z_axis=hd)), 0.004, 6)
    # firewood: split logs stacked in a little pile (bark on the round side, pale split faces)
    gw = ground_height(WOOD_C[0], WOOD_C[1])
    along = norm(v3((0.3, 1.0, 0.0)))
    across = norm(np.cross(v3((0, 0, 1)), along))
    for row, (n, zc) in enumerate(((4, 0.05), (3, 0.11), (2, 0.17))):
        for i in range(n):
            c = WOOD_C + across * ((i - (n - 1) / 2) * 0.1) + v3((0, 0, gw + zc - 0.02)) + along * rs.uniform(-0.03, 0.03)
            L = rs.uniform(0.17, 0.2)
            split = Inter(Cylinder(c, 0.05, 2 * L, rr=0.01, R=rot_from_axes(z_axis=along), disp=_bark(row * 7 + i), disp_amp=0.005),
                          Plane(c + v3((0, 0, 0.008)), v3((0, 0, 1))), 0.004)                 # (split along, the face up)
            fd.add(split, 0.004)
            fd.paint(Inter(Cylinder(c, 0.06, 2 * L + 0.02, R=rot_from_axes(z_axis=along)), Plane(c + v3((0, 0, 0.002)), v3((0, 0, -1))), 0.0), 5)
            for e in (c - along * L, c + along * L):
                fd.paint(Sphere(e, 0.055), 5)
    # the wattle panel behind him: stakes and withies woven between them, curving round the back of the ring
    stakes = []
    for k in range(5):
        aa = math.pi / 2 + (k - 2) * 0.27
        o = v3((math.cos(aa), math.sin(aa), 0))
        p = PC + o * (PR + 0.2)
        gz = ground_height(p[0], p[1])
        stakes.append((p, gz))
        fd.add(RoundCone(p + v3((0, 0, gz - 0.05)), p + v3((0, 0, gz + 0.84)), 0.024, 0.02, disp=_bark(20 + k), disp_amp=0.004), 0.0)
    for row in range(8):
        z = 0.12 + row * 0.085
        pts = []
        for k, (p, gz) in enumerate(stakes):
            aa = math.pi / 2 + (k - 2) * 0.27
            o = v3((math.cos(aa), math.sin(aa), 0))
            wob = 0.022 if (k + row) % 2 == 0 else -0.022
            pts.append(p + o * wob + v3((0, 0, gz + z)))
        ends = [pts[0] + norm(pts[0] - pts[1]) * 0.05, pts[-1] + norm(pts[-1] - pts[-2]) * 0.05]
        fd.add(Chain([ends[0]] + pts + [ends[1]], [0.013] * (len(pts) + 2), k=0.004), 0.004, 7)
    return fd


def chips_field():
    """Wood chips round the stump."""
    fd = Field("Chips")
    rs = np.random.RandomState(13)
    for i in range(9):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.26, 0.42)
        p = STUMP_C + v3((math.cos(a) * r, math.sin(a) * r, 0))
        p[2] = ground_height(p[0], p[1]) + 0.008
        fd.add(RoundBox(p, (rs.uniform(0.02, 0.035), rs.uniform(0.012, 0.02), 0.005), 0.003, R=euler(rs.uniform(-0.2, 0.2), rs.uniform(-0.2, 0.2), rs.uniform(0, 3))), 0.0)
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0] - PC[0], c[1] - PC[1]) < PR + 0.12 + pad:
        return True
    if math.hypot(c[0] - STUMP_C[0], c[1] - STUMP_C[1]) < 0.36 + pad:
        return True
    if math.hypot(c[0] - WOOD_C[0], c[1] - WOOD_C[1]) < 0.3 + pad:
        return True
    if c[1] > PC[1] + PR - 0.1 and abs(c[0]) < 0.75 + pad and c[1] < PC[1] + PR + 0.35 + pad:
        return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(21)
    n = 0
    tries = 0
    while n < 14 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.8, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.026, 0.05), seed=340 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=25):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 28 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.78, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c) or any(np.linalg.norm(c[:2] - t[:2]) < 0.14 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(8, 13)
        big = 0.7 + 0.45 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.05)
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.15, 0.45) + v3((0, 0, 1)))
            v, f, uv = _b.blade_mesh(root, d, rs.uniform(0.13, 0.24) * big, rs.uniform(0.03, 0.042),
                                     out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4, twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=33):
    """A few white and yellow meadow flowers."""
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
        spots.append((c, rs.randint(0, 2)))
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
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Wood", logs_field(), 0.0035), ("Chips", chips_field(), 0.002),
            ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Wood",)
LOW_TARGETS = {"Ground": 1500, "Wood": 5200, "Chips": 160, "Pebbles": 400}
MAT_OVERRIDES = {"Wood": ("bark_wood", {"name": "HQ_YardWood"}),
                 "Chips": ("bark_wood", {"name": "HQ_Chips", "bark": (0.72, 0.57, 0.38)})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035 and math.hypot(c.x - PC[0], c.y - PC[1]) > PR + 0.08
    on_turf = math.hypot(c.x - PC[0], c.y - PC[1]) < PR - 0.12 and abs(c.z - TOP_Z) < 0.03
    return n.z > 0.55 and (on_ground or on_turf)
