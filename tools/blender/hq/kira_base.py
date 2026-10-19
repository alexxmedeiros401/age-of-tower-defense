"""Kira's dais: a round duelling floor of dressed sandstone. A ring of curved blocks round a sunburst of wedge flags
painted red and pale by turns, a round centre stone; a ring of sixteen glowing sun-stones set in the blocks (the hero
ring, its own emissive mesh); behind her a wooden training post bound with rope and scarred by blade cuts, a round
bronze-faced shield and a spare khopesh resting against it; grass, flowers, papyrus and pebbles (distance fields +
direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
from ugo import bez3
import base as _b

GROUND_R = 1.3
GROUND_TOP = 0.14
TOP_Z = 0.32                       # the floor's top = where her feet stand
STAND = v3((0.0, 0.0, TOP_Z))
INNER_R = 0.6                      # the sunburst's edge
OUTER_R = 0.9                      # the floor's edge
RING_R = 0.75                      # the sun-stones
POST = v3((0.66, 0.84, 0.0))       # the training post (behind her, to her left)
SHIELD_C = v3((0.34, 1.0, 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.04 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 0.7) + F(0.02) * np.sin(a * 11 + 2.2) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.04) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _chip(P):
    return F(0.0035) * NOISE(P * F(9)) + F(0.0018) * NOISE(P * F(31))


def ring_func(r0, r1, n, seed, top, hz, ph0=None, jitter=1.0):
    rs = np.random.RandomState(seed)
    ph0 = rs.uniform(0, 2 * math.pi) if ph0 is None else ph0
    dzs = (rs.uniform(-0.004, 0.003, n) * jitter).astype(F)
    tilt = (rs.uniform(-0.01, 0.01, (n, 2)) * jitter).astype(F)
    gap = F(0.0055)
    rr = F(0.01)
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
        t = F(top) + dzs[k] + tilt[k, 0] * (r - rm) + tilt[k, 1] * da * r
        d_z = np.abs(z - (t - F(hz))) - F(hz)
        q = np.stack([d_a + rr, d_r + rr, d_z + rr], 1)
        out = np.sqrt((np.maximum(q, 0) ** 2).sum(1))
        return out + np.minimum(q.max(1), 0) - rr
    R = r1 + 0.02
    return Func(fn, (-R, -R, top - 2 * hz - 0.02), (R, R, top + 0.03), disp=_chip, disp_amp=0.006)


WEDGES = 16


def dais_field():
    """Sandstone (label 0): the ring of curved blocks, the sunburst of wedges (every other one red, label 5) and the
    centre stone; the sun-stones' sockets."""
    fd = Field("Dais")
    hz = (TOP_Z - GROUND_TOP + 0.08) / 2
    fd.add(Cylinder(v3((0, 0, (GROUND_TOP - 0.08 + TOP_Z - 0.03) / 2)), INNER_R + 0.02, TOP_Z - 0.03 - GROUND_TOP + 0.08, rr=0.01), 0.0)
    fd.add(ring_func(INNER_R, OUTER_R, 18, 71, TOP_Z, hz), 0.0)
    fd.add(ring_func(0.16, INNER_R, WEDGES, 72, TOP_Z - 0.002, 0.05, ph0=math.pi / 2 - math.pi / WEDGES, jitter=0.4), 0.0)
    fd.add(Cylinder(v3((0, 0, TOP_Z - 0.05)), 0.155, 0.1, rr=0.01, disp=_chip, disp_amp=0.004), 0.0)
    def red(P):
        a = np.arctan2(P[:, 1], P[:, 0]) - F(math.pi / 2 - math.pi / WEDGES)
        k = np.floor(a / F(2 * math.pi / WEDGES)).astype(np.int64) % WEDGES
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.where(k % 2 == 0, np.maximum(F(0.165) - r, r - F(INNER_R - 0.004)), F(1.0))
    fd.paint(Func(red, (-1, -1, TOP_Z - 0.2), (1, 1, TOP_Z + 0.05)), 5)
    for i in range(16):                                      # sockets the sun-stones sit in
        a = i * 2 * math.pi / 16 + 0.1
        c = v3((math.cos(a) * RING_R, math.sin(a) * RING_R, TOP_Z + 0.004))
        fd.sub(Ellipsoid(c, (0.042, 0.042, 0.02), R=euler(0, 0, a)), 0.004)
    return fd


def sunstones_field():
    fd = Field("Sunstones")
    for i in range(16):
        a = i * 2 * math.pi / 16 + 0.1
        c = v3((math.cos(a) * RING_R, math.sin(a) * RING_R, TOP_Z - 0.004))
        fd.add(Ellipsoid(c, (0.036, 0.036, 0.022), R=euler(0, 0, a)), 0.0)
    return fd


POST_H = 1.18


def wood_field():
    """The training post: a thick, adzed post (label 0) bound with rope (label 8) at two heights, nicked by blade cuts;
    a squat foot-block."""
    fd = Field("Wood")
    g = ground_height(POST[0], POST[1])
    grain = lambda P: F(0.003) * NOISE(P * np.array([40, 40, 6], F))
    b = POST + v3((0, 0, g - 0.04))
    fd.add(RoundCone(b, b + v3((0, 0, POST_H)), 0.07, 0.062, disp=grain, disp_amp=0.004), 0.0, 11)      # grain along Z
    fd.add(Sphere(b + v3((0, 0, POST_H)), 0.064), 0.03, 11)
    fd.add(RoundBox(b + v3((0, 0, 0.06)), (0.13, 0.13, 0.07), 0.02, R=euler(0, 0, 0.3), disp=grain, disp_amp=0.003), 0.03)
    rs = np.random.RandomState(9)
    for k in range(9):                                      # blade cuts
        z = rs.uniform(0.45, 1.05)
        a = rs.uniform(-1.2, 1.2) - math.pi / 2 - 0.6           # on the side toward the dais
        c = b + v3((math.cos(a) * 0.068, math.sin(a) * 0.068, z))
        fd.sub(RoundBox(c, (0.03, 0.006, 0.003), 0.002, R=euler(rs.uniform(-0.5, 0.5), 0, a + math.pi / 2)), 0.002)
    for z0 in (0.32, 0.86):
        for j in range(4):
            fd.add(Torus(b + v3((0, 0, z0 + j * 0.022)), 0.073 - 0.0004 * z0, 0.0095), 0.004, 8)
    return fd


def shield_field():
    """A round shield leaning on the post: a bronze face with a raised boss and rim (label 6), the leather back (0)."""
    fd = Field("Shield")
    g = ground_height(SHIELD_C[0], SHIELD_C[1])
    face = norm(v3((-0.3, -1.0, 0.55)))
    c = SHIELD_C + v3((0, 0, g + 0.3))
    R = rot_from_axes(z_axis=face, x_axis=norm(np.cross(v3((0, 0, 1)), face)))
    fd.add(Cylinder(c, 0.29, 0.03, rr=0.012, R=R), 0.0, 6)
    fd.add(Torus(c + face * 0.012, 0.28, 0.012, R=R), 0.006, 6)
    fd.add(Sphere(c + face * 0.01, 0.07), 0.02, 6)
    fd.add(Torus(c + face * 0.018, 0.16, 0.006, R=R), 0.004, 6)
    fd.paint(Func(lambda P: -((P - c.astype(F)) @ face.astype(F)) - F(0.004), c - 0.4, c + 0.4), 0)
    return fd


def blade_field():
    """A spare khopesh resting against the post (bronze, label 6; its grip wrapped in red cord, 5)."""
    fd = Field("Blade")
    g = ground_height(POST[0], POST[1])
    foot = POST + v3((-0.12, -0.13, g + 0.0))
    top = POST + v3((-0.05, -0.07, g + 0.62))
    ax = norm(top - foot)
    side = norm(np.cross(ax, v3((0, 0, 1))))
    ed = norm(np.cross(side, ax))
    fd.add(RoundCone(foot, foot + ax * 0.13, 0.015, 0.016), 0.0, 5)
    fd.add(Sphere(foot - ax * 0.01, 0.022), 0.006, 6)
    s0, s1 = foot + ax * 0.14, foot + ax * 0.33
    fd.add(RoundBox((s0 + s1) / 2, (0.016, 0.006, 0.1), 0.003, R=rot_from_axes(z_axis=ax, x_axis=ed)), 0.004, 6)
    pts = [bez3(s1, s1 + ax * 0.16, s1 + ax * 0.3 - ed * 0.06, s1 + ax * 0.27 - ed * 0.18, t) for t in np.linspace(0, 1, 12)]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        tng = norm(b - a)
        out = norm(np.cross(side, tng))
        w = 0.03 - 0.02 * (i / 11) ** 2
        fd.add(RoundBox((a + b) / 2 + out * 0.004, (w, 0.005, float(np.linalg.norm(b - a)) * 0.6 + 0.004), 0.002,
                        R=rot_from_axes(z_axis=tng, x_axis=out)), 0.004, 6)
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < OUTER_R + 0.07 + pad:
        return True
    if math.hypot(c[0] - POST[0], c[1] - POST[1]) < 0.22 + pad:
        return True
    if math.hypot(c[0] - SHIELD_C[0], c[1] - SHIELD_C[1]) < 0.3 + pad:
        return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(27)
    n = 0
    tries = 0
    while n < 14 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(OUTER_R + 0.06, GROUND_R - 0.05)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.0):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.022, 0.04), seed=500 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=51):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 24 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(OUTER_R + 0.07, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, -0.02):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.13 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(7, 12)
        big = 0.65 + 0.4 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.045)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.2, 0.5) + v3((0, 0, 1)))
            L = rs.uniform(0.11, 0.2) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.04), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


PAPYRUS = [(-1.06, 0.4, 0.9), (1.08, -0.38, 2.4)]


def flower_geometry(seed=53):
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(OUTER_R + 0.1, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.03) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.22 for s in spots):
            continue
        if any(math.hypot(c[0] - x, c[1] - y) < 0.2 for x, y, _ in PAPYRUS):
            continue
        spots.append((c, rs.randint(0, 3)))
    for c, kind in spots:
        base = v3((c[0], c[1], ground_height(c[0], c[1]) - 0.01))
        h = rs.uniform(0.1, 0.14)
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
            pv += [top + tilt * 0.004, top + dirk * 0.034 * 0.55 + sidek * 0.034 * 0.42, top + dirk * 0.034, top + dirk * 0.034 * 0.55 - sidek * 0.034 * 0.42]
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
            h = rs.uniform(0.4, 0.6)
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
    return [("Ground", ground_field(), 0.008), ("Dais", dais_field(), 0.0042), ("Sunstones", sunstones_field(), 0.0025),
            ("Wood", wood_field(), 0.003), ("Shield", shield_field(), 0.0026), ("Blade", blade_field(), 0.0018),
            ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Dais", "Wood", "Shield", "Blade")
LOW_TARGETS = {"Ground": 1300, "Dais": 3800, "Sunstones": 500, "Wood": 700, "Shield": 520, "Blade": 360, "Pebbles": 300}
MAT_OVERRIDES = {"Dais": ("limestone", {"name": "HQ_Sandstone"}),
                 "Wood": ("siege", {"name": "HQ_PostWood"}),
                 "Shield": ("leather_dyed", {"name": "HQ_ShieldFace"}),
                 "Blade": ("spear_shaft", {"name": "HQ_SpareKhopesh"}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
GLOW = {"Sunstones": ((1.0, 0.66, 0.16), 1.0, 0.5)}
EXTRA_SWATCHES = [(0.56, 0.7, 0.24)]          # kind 3: papyrus heads
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and OUTER_R + 0.02 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.08))
