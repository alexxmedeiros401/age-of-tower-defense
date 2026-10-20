"""Druid base: a grove's stone circle. A grassy mound with a low turf hummock where he stands, ringed by a kerb of mossy
stones; behind and round him five standing stones of grey granite, leaning a little, lichened and mossy; an old oak
stump at his left with roots writhing over the ground and a sprig of mistletoe on it; a low altar stone at his right
front (a slab on two stones); ferns, grass, foxgloves and white wood anemones; pebbles (distance fields + direct
low-poly geometry for the grass, ferns and flowers)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b

GROUND_R = 1.32
GROUND_TOP = 0.14
PC = v3((0.0, 0.04, 0.0))          # the hummock's centre
PR = 0.5                           # its radius
TOP_Z = 0.3                        # turf top = where his feet stand
STAND = v3((0.0, 0.04, TOP_Z))
# the standing stones: (angle from +X in degrees, radius, height, half width, lean (rad))
MEGALITHS = [(12, 1.02, 0.5, 0.11, 0.08), (52, 1.04, 0.66, 0.13, -0.05), (95, 1.06, 0.78, 0.15, 0.04), (138, 1.03, 0.6, 0.12, -0.07),
             (172, 1.0, 0.46, 0.1, 0.06)]
STUMP = v3((0.72, -0.42, 0.0))
ALTAR = v3((-0.68, -0.58, 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.05 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    """The grassy mound, and the turf hummock he stands on."""
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.035) * np.sin(a * 5 + 0.9) + F(0.02) * np.sin(a * 11 + 2.4) + F(0.02) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.05) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.09), 0), np.maximum(dz + F(0.09), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.09), dz + F(0.09)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.09)
    fd.add(Func(disc, (-1.5, -1.5, -0.25), (1.5, 1.5, 0.35),
                disp=lambda P: F(0.008) * NOISE(P * F(7)) + F(0.004) * NOISE(P * F(23)), disp_amp=0.014), 0.0)
    def hummock(P):
        q = P - PC.astype(F)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        top = F(TOP_Z) + F(0.015) * np.clip(1 - (r / F(PR)) ** 2, 0, 1) - F(0.06) * smoothstep(PR - 0.12, PR + 0.08, r)
        return np.maximum(r - F(PR + 0.06), np.maximum(P[:, 2] - top, F(0.05) - P[:, 2]))
    fd.add(Func(hummock, PC + v3((-0.7, -0.7, 0.0)), PC + v3((0.7, 0.7, 0.36)),
                disp=lambda P: F(0.005) * NOISE(P * F(10)), disp_amp=0.007), 0.05)
    return fd


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def _chip(seed):
    return lambda P: F(0.006) * NOISE(P * F(8) + F(seed)) + F(0.003) * NOISE(P * F(27) + F(seed * 2))


def megalith_frame(a_deg, rad, h, w, lean):
    a = math.radians(a_deg)
    out = v3((math.cos(a), math.sin(a), 0.0))
    tan = v3((-math.sin(a), math.cos(a), 0.0))
    foot = PC + out * rad
    up = norm(v3((0, 0, 1)) + out * lean)
    return foot, out, tan, up


def stone_field():
    """The standing stones (rough-hewn slabs, their tops rounded and worn), the kerb of rounded stones round his hummock,
    the altar (a slab on two stones) and stepping stones in front."""
    fd = Field("Stone")
    rs = np.random.RandomState(13)
    for i, (a_deg, rad, h, w, lean) in enumerate(MEGALITHS):
        foot, out, tan, up = megalith_frame(a_deg, rad, h, w, lean)
        g = ground_height(foot[0], foot[1])
        c = foot + v3((0, 0, g - 0.04)) + up * (h / 2)
        R = rot_from_axes(x_axis=tan, z_axis=up)
        t = w * rs.uniform(0.55, 0.7)
        def slab(P, c=c, R=R, h=h, w=w, t=t, i=i):
            q = (P - c.astype(F)) @ R.astype(F)
            u = q[:, 2] / F(h / 2)
            ww = F(w) * (F(1.0) - F(0.22) * np.clip(u, 0, 1) ** 2) * (F(1.0) + F(0.06) * np.sin(u * F(3) + F(i)))
            tt = F(t) * (F(1.0) - F(0.25) * np.clip(u, 0, 1) ** 2)
            dx = np.abs(q[:, 0]) - ww
            dy = np.abs(q[:, 1]) - tt
            dz = np.abs(q[:, 2]) - F(h / 2)
            k = F(0.035)
            o = np.sqrt(np.maximum(dx + k, 0) ** 2 + np.maximum(dy + k, 0) ** 2 + np.maximum(dz + k, 0) ** 2)
            return o + np.minimum(np.maximum(np.maximum(dx, dy), dz) + k, 0) - k
        fd.add(Func(slab, c - h, c + h, disp=_chip(17 + i * 5), disp_amp=0.012), 0.0)
    # the kerb round his hummock
    n = 13
    for k in range(n):
        a = 2 * math.pi * k / n + 0.2
        p = PC + v3((math.cos(a), math.sin(a), 0)) * (PR + 0.03)
        p[2] = 0.13 + rs.uniform(-0.01, 0.015)
        fd.add(Stone(p, rs.uniform(0.07, 0.09), seed=200 + k, squash=(1.2, 0.9, 0.75), noise=0.05), 0.012)
    # the altar: a low slab on two stones
    g = ground_height(ALTAR[0], ALTAR[1])
    Ra = euler(0, 0, 0.5)
    for sx in (-1, 1):
        fd.add(Stone(ALTAR + Ra @ v3((sx * 0.13, 0, g + 0.06)), 0.075, seed=260 + sx, squash=(0.8, 1.0, 1.0), noise=0.05), 0.01)
    fd.add(RoundBox(ALTAR + v3((0, 0, g + 0.15)), (0.22, 0.13, 0.03), 0.02, R=Ra @ euler(0.03, -0.04, 0), disp=_chip(3), disp_amp=0.008), 0.006)
    # stepping stones in front
    for k, (x, y) in enumerate(((0.05, -0.7), (-0.1, -0.92))):
        fd.add(Stone(v3((x, y, ground_height(x, y) - 0.005)), 0.1, seed=280 + k, squash=(1.3, 1.0, 0.35), noise=0.04), 0.0)
    return fd


def wood_field():
    """The old oak stump (bark, label 0; its cut top weathered grey, 5) with roots writhing over the ground; a sprig of
    mistletoe on it (6 leaves, berries in the Leaf part)."""
    fd = Field("Wood")
    bark = lambda P: F(0.004) * NOISE(P * np.array([30, 30, 8], F)) + F(0.002) * NOISE(P * F(90))
    g = ground_height(STUMP[0], STUMP[1])
    top = STUMP + v3((0, 0, g + 0.34))
    fd.add(RoundCone(STUMP + v3((0, 0, g - 0.04)), top, 0.17, 0.13, disp=bark, disp_amp=0.006), 0.0)
    fd.add(Inter(Cylinder(top - v3((0, 0, 0.02)), 0.135, 0.06, rr=0.02, R=euler(0.08, -0.06, 0)),
                 Plane(top + v3((0, 0, 0.0)), (0.08, -0.06, 1.0)), 0.01), 0.01)
    fd.paint(Func(lambda P: np.maximum(F(top[2] - 0.035) - P[:, 2], np.sqrt((P[:, 0] - F(top[0])) ** 2 + (P[:, 1] - F(top[1])) ** 2) - F(0.13)),
                  top - 0.3, top + 0.3), 5)
    rs = np.random.RandomState(29)
    for k in range(6):
        a = 2 * math.pi * k / 6 + rs.uniform(-0.3, 0.3)
        d = v3((math.cos(a), math.sin(a), 0))
        pts = []
        for j in range(5):
            t = j / 4
            r = 0.1 + 0.32 * t * rs.uniform(0.8, 1.2)
            p = STUMP + d * r + v3((-d[1], d[0], 0)) * (0.05 * math.sin(t * 3 + k))
            p[2] = ground_height(p[0], p[1]) + 0.12 * (1 - t) ** 1.5 + 0.01
            pts.append(p)
        rad = [0.06 * (1 - 0.75 * j / 4) for j in range(5)]
        fd.add(Chain(pts, rad, k=0.02, disp=bark, disp_amp=0.004), 0.03)
    return fd


def leaf_field():
    """Mistletoe on the stump (narrow leaves, label 6; white berries, 5) and ivy on two of the standing stones (0)."""
    fd = Field("Leaf")
    g = ground_height(STUMP[0], STUMP[1])
    c = STUMP + v3((0.04, -0.06, g + 0.36))
    rs = np.random.RandomState(31)
    for k in range(5):
        d = norm(v3((math.cos(k * 1.3), math.sin(k * 1.3), 0.7)))
        tip = c + d * 0.07
        fd.add(Chain([c, tip], [0.005, 0.004], k=0.0), 0.002, 7)
        for sd in (-1, 1):
            ld = norm(d + norm(np.cross(d, v3((0, 0, 1)))) * sd * 0.9)
            fd.add(Ellipsoid(tip + ld * 0.024, (0.026, 0.01, 0.0035), R=rot_from_axes(x_axis=ld, z_axis=v3((0, 0, 1)))), 0.002, 6)
        for j in range(3):
            fd.add(Sphere(tip + v3(rs.uniform(-0.01, 0.01, 3)), 0.009), 0.002, 5)
    # ivy climbing two of the stones
    for i in (1, 3):
        a_deg, rad, h, w, lean = MEGALITHS[i]
        foot, out, tan, up = megalith_frame(a_deg, rad, h, w, lean)
        gz = ground_height(foot[0], foot[1])
        for k in range(9):
            t = k / 8
            p = foot + v3((0, 0, gz)) + up * (h * 0.75 * t) - out * (w * 0.62) + tan * (w * 0.5 * math.sin(t * 5 + i))
            n = -out
            fd.add(Ellipsoid(p, (0.03, 0.022, 0.005), R=rot_from_axes(z_axis=n, x_axis=norm(tan + up * 0.5))), 0.004, 0)
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0] - PC[0], c[1] - PC[1]) < PR + 0.12 + pad:
        return True
    for (a_deg, rad, h, w, lean) in MEGALITHS:
        foot, out, tan, up = megalith_frame(a_deg, rad, h, w, lean)
        if math.hypot(c[0] - foot[0], c[1] - foot[1]) < w + 0.1 + pad:
            return True
    if math.hypot(c[0] - STUMP[0], c[1] - STUMP[1]) < 0.45 + pad:
        return True
    if math.hypot(c[0] - ALTAR[0], c[1] - ALTAR[1]) < 0.3 + pad:
        return True
    for x, y in ((0.05, -0.7), (-0.1, -0.92)):
        if math.hypot(c[0] - x, c[1] - y) < 0.14 + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(41)
    n = 0
    tries = 0
    while n < 14 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.7, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.024, 0.045), seed=340 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=37):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.66, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.14 for t in tufts):
            continue
        tufts.append(c)
    # tufts at the foot of each standing stone
    for (a_deg, rad, h, w, lean) in MEGALITHS:
        foot, out, tan, up = megalith_frame(a_deg, rad, h, w, lean)
        for s in (-1, 1):
            tufts.append(foot + tan * s * (w + 0.06) - out * 0.04)
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


def _bloom(out, top, tilt, size, kind_col, petals=5):
    R = rot_from_axes(z_axis=tilt)
    pv, pf = [], []
    for k in range(petals):
        a = 2 * math.pi * k / petals
        dirk = R @ v3((math.cos(a), math.sin(a), 0.15))
        sidek = R @ v3((-math.sin(a), math.cos(a), 0))
        b0 = len(pv)
        pv += [top + tilt * 0.003, top + dirk * size * 0.55 + sidek * size * 0.42, top + dirk * size, top + dirk * size * 0.55 - sidek * size * 0.42]
        pf.append((b0, b0 + 1, b0 + 2, b0 + 3))
    out.append((pv, pf, 1, kind_col))
    cv = [top + R @ v3((math.cos(2 * math.pi * k / 6) * size * 0.3, math.sin(2 * math.pi * k / 6) * size * 0.3, 0.006)) for k in range(6)]
    cv.append(top + R @ v3((0, 0, 0.012)))
    out.append((cv, [(k, (k + 1) % 6, 6) for k in range(6)], 2, kind_col))


def _frond(out, root, d, L, rs):
    """A fern frond: a curving midrib (stem swatch) with paired leaflets along it, shortening to the tip."""
    side = norm(np.cross(d, v3((0, 0, 1))))
    pts = []
    for j in range(7):
        t = j / 6
        pts.append(root + d * (L * t) + v3((0, 0, 0.12 * L * math.sin(t * 2.4))) - v3((0, 0, 0.35 * L * t * t)))
    for j in range(6):
        a, b = pts[j], pts[j + 1]
        sv, sf, _ = _b.blade_mesh(a, norm(b - a), float(np.linalg.norm(b - a)), 0.008, v3((0, 0, 0)), segs=1)
        out.append((sv, sf, 0, 4))
        ln = 0.06 * L / 0.25 * (1 - j / 7)
        for sd in (-1, 1):
            tip = a + side * sd * ln + v3((0, 0, -0.01))
            out.append(([a, a + (b - a) * 0.5 + side * sd * ln * 0.5 + v3((0, 0, 0.004)), tip, a + (b - a) * 0.15],
                        [(0, 1, 2, 3)], 0, 4))


def flower_geometry(seed=43):
    """Ferns round the stones (stem swatch), foxgloves (purple bells up a stem, swatch 2), white wood anemones (0)."""
    rs = np.random.RandomState(seed)
    out = []
    # ferns at the feet of the stones and the stump
    spots = []
    for (a_deg, rad, h, w, lean) in MEGALITHS[1:4]:
        foot, o, tan, up = megalith_frame(a_deg, rad, h, w, lean)
        spots.append(foot - o * 0.16 + tan * 0.1)
    spots.append(STUMP + v3((-0.3, 0.22, 0)))
    for c in spots:
        c = v3(c)
        for k in range(rs.randint(5, 8)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c.copy()
            root[2] = ground_height(c[0], c[1]) + 0.01
            d = norm(v3((math.cos(ang), math.sin(ang), rs.uniform(0.8, 1.4))))
            _frond(out, root, d, rs.uniform(0.2, 0.3), rs)
    # foxgloves and anemones
    fl = []
    tries = 0
    while len(fl) < 7 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.72, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.04) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.2 for s in fl):
            continue
        fl.append((c, 2 if len(fl) % 3 == 0 else 0))
    for c, col in fl:
        if col == 2:                                     # a foxglove: a tall stem hung with bells
            root = c.copy()
            root[2] = ground_height(c[0], c[1]) - 0.01
            h = rs.uniform(0.24, 0.32)
            d = norm(v3((rs.uniform(-0.1, 0.1), rs.uniform(-0.1, 0.1), 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.014, v3((0, 0, 0)), segs=3)
            out.append((sv, sf, 0, col))
            for j in range(6):
                p = root + d * h * (0.45 + 0.09 * j)
                a = j * 2.2
                tilt = norm(v3((math.cos(a), math.sin(a), -0.3)))
                _bloom(out, p + tilt * 0.012, tilt, 0.02, col, petals=4)
        else:                                            # wood anemones: low white stars
            for k in range(rs.randint(3, 5)):
                ang = rs.uniform(0, 2 * math.pi)
                root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.06)
                root[2] = ground_height(root[0], root[1]) - 0.01
                h = rs.uniform(0.06, 0.1)
                d = norm(v3((math.cos(ang) * 0.3, math.sin(ang) * 0.3, 1.0)))
                sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
                out.append((sv, sf, 0, col))
                _bloom(out, root + d * h, norm(v3((rs.uniform(-0.3, 0.3), rs.uniform(-0.3, 0.3), 1.0))), 0.026, col, petals=6)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Stone", stone_field(), 0.0045), ("Wood", wood_field(), 0.004),
            ("Leaf", leaf_field(), 0.0025), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Wood", "Leaf")
LOW_TARGETS = {"Ground": 1500, "Stone": 4400, "Wood": 1500, "Leaf": 700, "Pebbles": 380}
MAT_OVERRIDES = {"Stone": ("stone", {"name": "HQ_StandingStones", "moss": True}),
                 "Wood": ("bark_wood", {"name": "HQ_OakStump", "bark": (0.3, 0.22, 0.14), "wood": (0.62, 0.58, 0.5)}),
                 "Leaf": ("leafy", {"name": "HQ_BaseLeafy", "leaf": (0.16, 0.32, 0.1)})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035 and math.hypot(c.x - PC[0], c.y - PC[1]) > PR + 0.1
    on_turf = math.hypot(c.x - PC[0], c.y - PC[1]) < PR - 0.12 and abs(c.z - TOP_Z) < 0.03
    return n.z > 0.55 and (on_ground or on_turf)
