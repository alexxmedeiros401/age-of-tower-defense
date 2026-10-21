"""Alchemist base: her yard, centred on her furnace (the tower turns about it). A round floor of worn flagstones, stained
green here and there where brews were spilled, its rim of curved slabs; beyond it trodden earth and grass. Round about,
clear of where she walks as the tower turns: her workbench on trestles (stone jars of salts, a glass retort and a
round flask, a mortar and pestle, an open book of receipts); a water butt with a ladle; a crate of bottles packed in
straw; pebbles, grass and a few flowers (distance fields + direct low-poly geometry for the grass and the flowers)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
import alchemist as _a
from sunpriest_base import ring_func
from crossbowman_base import _bloom

GROUND_R = 1.36
GROUND_TOP = 0.08
FLOOR_R = 0.98                 # the flagstones (she sweeps round to ~0.85 as the tower turns)
TOP_Z = 0.14                   # the floor's top = where she and the furnace stand
STAND = v3((-_a.YAW_PIVOT[0], -_a.YAW_PIVOT[1], TOP_Z))
BENCH_A = math.radians(128.0)  # angles from +X (+Y is behind her when the tower faces -Y)
BUTT_A = math.radians(52.0)
CRATE_A = math.radians(208.0)
RING_R = 1.16                  # where those stand


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
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 2.4) + F(0.02) * np.sin(a * 11 + 0.9) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.03) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _fine(P):
    return F(0.0014) * NOISE(P * F(30)) + F(0.0008) * NOISE(P * F(90))


def floor_field():
    """Flagstones (label 0; a browner stone for some, 7; green brew stains, 8): a centre slab under the furnace, two
    rings of curved slabs, and a rim ring a little proud."""
    fd = Field("Floor")
    hz = 0.05
    fd.add(Cylinder(v3((0, 0, TOP_Z - hz)), 0.31, 2 * hz, rr=0.008, disp=_fine, disp_amp=0.003), 0.0)
    fd.add(ring_func(0.31, 0.64, 9, 411, TOP_Z, hz, jitter=0.5, chip=_fine), 0.0)
    fd.add(ring_func(0.64, FLOOR_R - 0.12, 13, 419, TOP_Z, hz, jitter=0.6, chip=_fine), 0.0)
    fd.add(ring_func(FLOOR_R - 0.12, FLOOR_R, 16, 421, TOP_Z + 0.012, hz + 0.02, jitter=0.6, chip=_fine), 0.0)
    rs = np.random.RandomState(17)
    for k in range(6):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.35, 0.9)
        fd.paint(Sphere(v3((math.cos(a) * r, math.sin(a) * r, TOP_Z)), rs.uniform(0.12, 0.2)), 7)
    for k in range(7):                                                           # spilled brews
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.3, 0.8)
        c = v3((math.cos(a) * r, math.sin(a) * r, TOP_Z))
        fd.paint(Ellipsoid(c, (rs.uniform(0.05, 0.12), rs.uniform(0.04, 0.09), 0.05), R=euler(0, 0, rs.uniform(0, 3))), 8)
        for j in range(3):
            d = v3((rs.uniform(-1, 1), rs.uniform(-1, 1), 0)) * 0.1
            fd.paint(Sphere(c + d, rs.uniform(0.012, 0.025)), 8)
    return fd


def _on_ring(a, r=RING_R):
    c = v3((math.cos(a) * r, math.sin(a) * r, 0.0))
    c[2] = ground_height(c[0], c[1])
    t = v3((-math.sin(a), math.cos(a), 0.0))                  # along the ring
    o = v3((math.cos(a), math.sin(a), 0.0))                   # outward
    return c, t, o


BENCH_H = 0.5                  # the bench top's height above the ground
BENCH_L, BENCH_D = 0.3, 0.12   # its half length (along the ring) and half depth


def bench_field():
    """Oak (label 0 grain along it... the planks; 11 the trestles' legs): a plank top on two trestles, iron nails (6)."""
    fd = Field("Bench")
    c, t, o = _on_ring(BENCH_A)
    R = rot_from_axes(z_axis=(0, 0, 1), y_axis=o)
    top = c + v3((0, 0, BENCH_H))
    fd.add(RoundBox(top, (BENCH_L, BENCH_D, 0.018), 0.006, R=R, disp=_fine, disp_amp=0.002), 0.0, 10)
    for s in (-1, 1):
        f = c + t * (s * (BENCH_L - 0.07))
        for u in (-1, 1):
            a = f + o * (u * 0.1) + v3((0, 0, 0.0))
            b = f + o * (u * 0.03) + v3((0, 0, BENCH_H - 0.02))
            fd.add(RoundCone(a, b, 0.018, 0.016), 0.006, 11)
        fd.add(RoundBox(f + v3((0, 0, BENCH_H - 0.04)), (0.02, 0.09, 0.016), 0.005, R=R), 0.006, 10)
        fd.add(RoundBox(f + v3((0, 0, 0.16)), (0.014, 0.08, 0.012), 0.004, R=R), 0.006, 10)
    for k in range(4):
        fd.add(Sphere(top + t * (-0.25 + 0.17 * k) + o * 0.08 + v3((0, 0, 0.018)), 0.006), 0.002, 6)
    return fd


def bench_top():
    c, t, o = _on_ring(BENCH_A)
    return c + v3((0, 0, BENCH_H + 0.018)), t, o


def jars_field():
    """On the bench: three stoneware jars with wooden stoppers (label 0 the glaze... drawn as stone, see MAT), the mortar
    and its pestle."""
    fd = Field("Jars")
    T, t, o = bench_top()
    for i, (u, h, r) in enumerate(((-0.24, 0.13, 0.045), (-0.15, 0.1, 0.04), (0.2, 0.08, 0.055))):
        p = T + t * u + o * (0.04 * (i % 2))
        fd.add(RoundCone(p + v3((0, 0, 0.01)), p + v3((0, 0, h)), r, r * 0.75), 0.0)
        fd.add(Cylinder(p + v3((0, 0, h + 0.012)), r * 0.5, 0.03, rr=0.006), 0.004)
    m = T + t * 0.05 - o * 0.06
    fd.add(Inter(Shell(Sphere(m + v3((0, 0, 0.05)), 0.055), 0.0, 0.014), Func(lambda P, m=m: P[:, 2] - F(m[2] + 0.075), m - 0.2, m + 0.2), 0.004), 0.0)
    fd.add(Cylinder(m + v3((0, 0, 0.01)), 0.035, 0.02, rr=0.006), 0.004)
    fd.add(RoundCone(m + v3((0.0, 0.0, 0.04)), m + t * 0.05 + v3((0, 0, 0.14)), 0.016, 0.011), 0.004)
    return fd


def glass_field():
    """The glassware on the bench (glass 0, brews: green 5, violet 7): a retort with its long neck and a round flask."""
    fd = Field("Glass")
    T, t, o = bench_top()
    rc = T + t * (-0.03) + o * 0.04 + v3((0, 0, 0.062))
    fd.add(Sphere(rc, 0.06), 0.0)
    neck = [rc + v3((0, 0, 0.04)), rc + v3((0, 0, 0.09)) - t * 0.02, rc - t * 0.13 + v3((0, 0, 0.11)), rc - t * 0.25 + v3((0, 0, 0.05))]
    fd.add(Chain(neck, [0.018, 0.014, 0.011, 0.008], k=0.008), 0.008)
    fd.paint(Func(lambda P, rc=rc: P[:, 2] - F(rc[2] + 0.01), rc - 0.2, rc + 0.2), 5)
    fc = T + t * 0.13 + o * (-0.03) + v3((0, 0, 0.05))
    fd.add(Sphere(fc, 0.048), 0.0)
    fd.add(RoundCone(fc + v3((0, 0, 0.04)), fc + v3((0, 0, 0.1)), 0.016, 0.013), 0.006)
    fd.add(Torus(fc + v3((0, 0, 0.1)), 0.014, 0.004), 0.003)
    fd.paint(Func(lambda P, fc=fc: P[:, 2] - F(fc[2] + 0.015), fc - 0.2, fc + 0.2), 7)
    return fd


def book_field():
    """An open book of receipts (pages: parchment, label 0; its leather cover red, 5) on the bench."""
    fd = Field("Book")
    T, t, o = bench_top()
    c = T + t * 0.04 - o * 0.06 + v3((0, 0, 0.006))
    R = rot_from_axes(z_axis=(0, 0, 1), y_axis=o)
    fd.add(RoundBox(c, (0.11, 0.075, 0.004), 0.002, R=R), 0.0, 5)
    for s in (-1, 1):
        p = c + t * (s * 0.052) + v3((0, 0, 0.01 + 0.004))
        fd.add(RoundBox(p, (0.05, 0.068, 0.008), 0.004, R=rot_from_axes(z_axis=norm(v3((0, 0, 1)) - t * (s * 0.12)), y_axis=o)), 0.002)
    return fd


BUTT_R, BUTT_H = 0.15, 0.4


def butt_field():
    """A water butt of oak staves (grain upright, 11) with iron hoops (6), a wooden ladle hanging on its rim."""
    fd = Field("Butt")
    c, t, o = _on_ring(BUTT_A, RING_R + 0.02)
    def keg(P):
        q = P - c.astype(F)
        z = q[:, 2]
        k = (z - F(BUTT_H / 2)) / F(BUTT_H / 2)
        r = F(BUTT_R) * (F(1) + F(0.1) * (F(1) - k * k))
        rr = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        a = np.arctan2(q[:, 1], q[:, 0])
        stave = F(0.0025) * (F(1) - np.abs(np.cos(a * F(10))))
        return np.maximum(rr - r + stave, np.abs(z - F(BUTT_H / 2)) - F(BUTT_H / 2))
    fd.add(Func(keg, c - 0.3, c + v3((0.3, 0.3, 0.5))), 0.0, 11)
    fd.sub(Cylinder(c + v3((0, 0, BUTT_H)), BUTT_R * 0.9, 0.05), 0.004)
    fd.add(Cylinder(c + v3((0, 0, BUTT_H - 0.035)), BUTT_R * 0.92, 0.01), 0.004, 5)              # the water (dark)
    for zz in (0.05, BUTT_H / 2, BUTT_H - 0.04):
        kk = (zz - BUTT_H / 2) / (BUTT_H / 2)
        r = BUTT_R * (1 + 0.1 * (1 - kk * kk))
        fd.add(Torus(c + v3((0, 0, zz)), r + 0.002, 0.008), 0.002, 6)
    lp = c - o * (BUTT_R - 0.01) + v3((0, 0, BUTT_H + 0.01))
    fd.add(RoundCone(lp + o * 0.02, lp + o * 0.2 + v3((0, 0, 0.08)), 0.008, 0.007), 0.003)
    fd.add(Inter(Shell(Sphere(lp - o * 0.03 + v3((0, 0, -0.05)), 0.035), 0.0, 0.006), Func(lambda P, lp=lp: P[:, 2] - F(lp[2] - 0.04), lp - 0.2, lp + 0.2), 0.003), 0.003)
    return fd


def crate_field():
    """A crate of planks (10) with straw (label 12... drawn as pale wood: 0) and three bottles' necks (glass, in Glass2)."""
    fd = Field("Crate")
    c, t, o = _on_ring(CRATE_A, RING_R + 0.02)
    R = rot_from_axes(z_axis=(0, 0, 1), y_axis=o)
    h = 0.22
    cc = c + v3((0, 0, h / 2))
    fd.add(Inter(Shell(RoundBox(cc, (0.16, 0.13, h / 2), 0.008, R=R), 0.0, 0.016),
                 Func(lambda P: P[:, 2] - F(c[2] + h - 0.004), cc - 0.4, cc + 0.4), 0.003), 0.0, 10)
    fd.add(RoundBox(cc + v3((0, 0, -0.03)), (0.15, 0.12, h / 2 - 0.02), 0.01, R=R, disp=lambda P: F(0.008) * NOISE(P * F(30)), disp_amp=0.01), 0.004, 0)
    for s in (-1, 1):
        fd.add(RoundBox(cc + t * (s * 0.12), (0.012, 0.135, h / 2 + 0.004), 0.004, R=R), 0.004, 10)
    return fd


def bottles_field():
    fd = Field("Bottles")
    c, t, o = _on_ring(CRATE_A, RING_R + 0.02)
    for i, (u, w) in enumerate(((-0.07, -0.03), (0.0, 0.04), (0.07, -0.02))):
        p = c + t * u + o * w + v3((0, 0, 0.17))
        d = norm(v3((0, 0, 1)) + t * (0.15 * (i - 1)))
        fd.add(RoundCone(p, p + d * 0.1, 0.026, 0.012), 0.0)
        fd.add(RoundCone(p + d * 0.09, p + d * 0.12, 0.009, 0.0095), 0.003, 9)
        fd.paint(Func(lambda P, p=p, d=d: (P - p.astype(F)) @ d.astype(F) - F(0.07), p - 0.2, p + 0.2), (6, 8, 5)[i])
    return fd


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(37)
    n = 0
    tries = 0
    while n < 12 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        if min(abs((a - s + math.pi) % (2 * math.pi) - math.pi) for s in (BENCH_A, BUTT_A, CRATE_A)) < 0.32:
            continue
        r = rs.uniform(FLOOR_R + 0.04, GROUND_R - 0.04)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.02, 0.032), seed=340 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def _free(c, pad=0.0):
    for a, rad in ((BENCH_A, 0.36), (BUTT_A, 0.2), (CRATE_A, 0.22)):
        p = np.array((math.cos(a) * RING_R, math.sin(a) * RING_R))
        if np.linalg.norm(c[:2] - p) < rad + pad:
            return False
    return True


def grass_geometry(seed=59):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 28 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(FLOOR_R + 0.03, GROUND_R - 0.04)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.12 for t in tufts) or not _free(c, 0.02):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(7, 11)
        big = 0.6 + 0.35 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.035)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
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


def flower_geometry(seed=61):
    """Daisies (swatch 0: white petals) and buttercups (1: yellow) in the grass beyond the floor."""
    rs = np.random.RandomState(seed)
    spots = []
    tries = 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(FLOOR_R + 0.05, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - s[0][:2]) < 0.25 for s in spots) or not _free(c, 0.03):
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
    return [("Ground", ground_field(), 0.008), ("Floor", floor_field(), 0.0042), ("Bench", bench_field(), 0.003),
            ("Jars", jars_field(), 0.0024), ("Glass", glass_field(), 0.0018), ("Book", book_field(), 0.002),
            ("Butt", butt_field(), 0.0028), ("Crate", crate_field(), 0.003), ("Bottles", bottles_field(), 0.002),
            ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Floor", "Bench", "Butt", "Crate")
LOW_TARGETS = {"Ground": 1300, "Floor": 2400, "Bench": 700, "Jars": 600, "Glass": 500, "Book": 160, "Butt": 800, "Crate": 600,
               "Bottles": 300, "Pebbles": 280}
_OAK = {"wood": (0.5, 0.35, 0.21), "wood2": (0.37, 0.25, 0.14), "red": (0.08, 0.1, 0.12), "blue": (0.2, 0.32, 0.5), "metal": "iron"}
MAT_OVERRIDES = {"Floor": ("flagstone", {"name": "HQ_AlchemistFloor", "stain": (0.26, 0.5, 0.12)}),
                 "Bench": ("siege", dict(_OAK, name="HQ_AlchemistOak")),
                 "Butt": ("siege", dict(_OAK, name="HQ_AlchemistOak")),
                 "Crate": ("siege", dict(_OAK, name="HQ_AlchemistOak")),
                 "Jars": ("terracotta", {"name": "HQ_AlchemistJars", "base": (0.56, 0.42, 0.3)}),
                 "Glass": ("vials", {"name": "HQ_BaseGlass"}),
                 "Bottles": ("vials", {"name": "HQ_BaseGlass"}),
                 "Book": ("linen", {"name": "HQ_Book", "base": (0.9, 0.84, 0.68), "border": (0.55, 0.1, 0.07), "stripe": (0.55, 0.1, 0.07)}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and FLOOR_R - 0.01 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
