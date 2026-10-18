"""Club Warrior base: a trampled earth arena on a grassy mound, ringed at the back by a little henge (a trilithon and
standing stones, mossy), a mammoth's skull with its tusks as a trophy, a pile of gnawed bones, a cracked crater where
his club comes down, boulders and pebbles (distance fields) + grass blades and flowers (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
from ugo import bez3

GROUND_R = 1.3
GROUND_TOP = 0.16
ARENA_R = 0.74
DIRT = 6


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.05 * max(0.0, 1 - (r / GROUND_R) ** 2)


TOP_Z = ground_height(0.0, 0.03)
STAND = v3((0.0, 0.03, TOP_Z))
CRATER = v3((0.02, -0.52, ground_height(0.02, -0.52)))
# standing stones: (angle deg, radius, height, width, depth, seed, lean)
HENGE = [(77.0, 1.0, 1.3, 0.38, 0.28, 3, 0.0), (103.0, 1.0, 1.34, 0.38, 0.29, 5, 0.0),
         (36.0, 1.02, 0.92, 0.36, 0.26, 7, 0.06), (144.0, 1.02, 1.06, 0.38, 0.27, 9, -0.04), (171.0, 1.05, 0.62, 0.34, 0.26, 11, -0.22)]
SKULL_C = v3((0.8, -0.5, GROUND_TOP + 0.02))
SKULL_FWD = norm(v3((0.55, -1.0, 0.0)))
BONES_C = v3((-0.84, -0.42, GROUND_TOP + 0.03))


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.035) * np.sin(a * 5 + 0.7) + F(0.02) * np.sin(a * 11 + 2.0) + F(0.02) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.05) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.09), 0), np.maximum(dz + F(0.09), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.09), dz + F(0.09)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.09)
    fd.add(Func(disc, (-1.5, -1.5, -0.25), (1.5, 1.5, 0.35),
                disp=lambda P: F(0.008) * NOISE(P * F(7)) + F(0.004) * NOISE(P * F(23)), disp_amp=0.014), 0.0)
    # the crater his club has pounded: a shallow dish with cracks running out of it
    fd.sub(Ellipsoid(CRATER + v3((0, 0, 0.035)), (0.2, 0.16, 0.06)), 0.03)
    rs = np.random.RandomState(4)
    for i in range(7):
        a = i * 2 * math.pi / 7 + rs.uniform(-0.3, 0.3)
        d = v3((math.cos(a), math.sin(a) * 0.85, 0))
        pts = [CRATER + d * 0.12 + v3((0, 0, 0.012))]
        for j in range(3):
            d = norm(d + v3((rs.uniform(-0.4, 0.4), rs.uniform(-0.4, 0.4), 0)))
            q = pts[-1] + d * rs.uniform(0.07, 0.11)
            q[2] = ground_height(q[0], q[1]) + 0.004
            pts.append(q)
        fd.sub(Chain(pts, [0.016, 0.012, 0.008, 0.003], k=0.004), 0.006)
    # the arena: bare trampled earth (painted), a little irregular
    def arena(P):
        r = np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F(0.0)) ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        return r - (F(ARENA_R + 0.06) + F(0.03) * np.sin(a * 6 + 1.1) + F(0.025) * NOISE(P * F(6)))
    fd.paint(Func(arena, (-1.2, -1.2, -0.3), (1.2, 1.2, 0.5)), DIRT)
    return fd


def henge_axis(i):
    ang, rad, h, w, dpt, seed, lean = HENGE[i]
    a = math.radians(ang)
    out = v3((math.cos(a), math.sin(a), 0))
    base = out * rad + v3((0, 0, GROUND_TOP - 0.08))
    top = base + norm(out * lean + v3((0, 0, 1.0))) * h
    return base, top, out


def rocks_field():
    """The henge (a trilithon and three standing stones, one broken and leaning) and boulders."""
    fd = Field("Rocks")
    for i, (ang, rad, h, w, dpt, seed, lean) in enumerate(HENGE):
        base, top, out = henge_axis(i)
        ax = norm(top - base)
        c = (base + top) / 2
        R = rot_from_axes(z_axis=ax, y_axis=out)
        st = Stone(c, h * 0.5, seed=seed, cuts=16, squash=(w / h, dpt / h, 1.0), soft=0.022, depth=(0.8, 0.95), R=R, noise=0.016)
        fd.add(st, 0.0)
    # the lintel across the trilithon (tenon bumps on the uprights hold it)
    b0, t0, _ = henge_axis(0)
    b1, t1, _ = henge_axis(1)
    lc = (t0 + t1) / 2 + v3((0, 0.0, 0.06))
    lax = norm(t0 - t1)
    R = np.stack([lax, np.cross(v3((0, 0, 1)), lax), v3((0, 0, 1))], axis=1)
    fd.add(Stone(lc, 0.47, seed=13, cuts=14, squash=(1.0, 0.3, 0.22), soft=0.03, depth=(0.84, 0.96), R=R, noise=0.012), 0.0)
    # boulders on the rim
    for c, r, s in (((1.05, -0.02, GROUND_TOP + 0.03), 0.15, 41), ((-1.04, -0.12, GROUND_TOP + 0.03), 0.13, 43), ((0.55, 0.92, GROUND_TOP + 0.02), 0.11, 45),
                    ((-0.5, 0.95, GROUND_TOP + 0.02), 0.12, 47)):
        fd.add(Stone(c, r, seed=s, cuts=10, squash=(1.0, 0.95, 0.75), soft=0.06, noise=0.02), 0.03)
    # chunks knocked out of the crater
    rs = np.random.RandomState(8)
    for i in range(5):
        a = rs.uniform(0, 2 * math.pi)
        q = CRATER + v3((math.cos(a) * rs.uniform(0.2, 0.3), math.sin(a) * rs.uniform(0.17, 0.25), 0))
        q[2] = ground_height(q[0], q[1]) + 0.01
        fd.add(Stone(q, rs.uniform(0.028, 0.045), seed=70 + i, cuts=7, squash=(1, 0.9, 0.6), soft=0.1, noise=0.03), 0.0)
    return fd


def skull_frame():
    f = SKULL_FWD
    up = v3((0, 0, 1))
    side = norm(np.cross(up, f))
    return f, up, side


def bone_field():
    """A mammoth's skull lying at the front right (tall domed cranium, the trunk opening, eye sockets, tusk sockets) and
    a pile of gnawed long bones at the front left."""
    fd = Field("Bone")
    f, up, side = skull_frame()
    c = SKULL_C
    L = lambda x, y, z: c + side * x + f * y + up * z          # y>0 = toward the skull's face
    R = np.stack([side, f, up], axis=1)
    pit = lambda P: F(0.003) * NOISE(P * F(35))
    fd.add(Ellipsoid(L(0, -0.02, 0.17), (0.15, 0.13, 0.16), R=R, disp=pit, disp_amp=0.004), 0.0)          # domed cranium
    fd.add(RoundBox(L(0, 0.08, 0.09), (0.12, 0.08, 0.085), 0.05, R=R, disp=pit, disp_amp=0.004), 0.05)     # face
    for sx in (-1, 1):
        fd.add(RoundCone(L(sx * 0.07, 0.09, 0.08), L(sx * 0.085, 0.2, 0.025), 0.06, 0.066), 0.04)         # tusk sockets
        fd.sub(Sphere(L(sx * 0.122, 0.05, 0.16), 0.032), 0.01)                                               # eye sockets
        fd.add(Torus(L(sx * 0.122, 0.05, 0.16), 0.034, 0.009, R=rot_from_axes(z_axis=side * sx)), 0.008)
    fd.sub(Ellipsoid(L(0, 0.15, 0.15), (0.055, 0.04, 0.035), R=R), 0.01)                                     # trunk opening
    for sx in (-1, 1):
        fd.sub(Ellipsoid(L(sx * 0.085, 0.24, 0.028), (0.045, 0.02, 0.045), R=R @ euler(0.5, 0, 0)), 0.006)  # socket mouths
    fd.add(Ellipsoid(L(0, -0.12, 0.05), (0.13, 0.08, 0.07), R=R), 0.05)                                    # back of the skull
    # the bone pile
    rs = np.random.RandomState(21)
    b = BONES_C
    for i, (a, L0) in enumerate(((0.3, 0.34), (1.9, 0.3), (1.1, 0.26))):
        d = v3((math.cos(a), math.sin(a), 0.08 * (i - 1)))
        p0 = b - d * L0 / 2 + v3((rs.uniform(-0.04, 0.04), rs.uniform(-0.04, 0.04), 0.02 + 0.03 * i))
        p1 = p0 + d * L0
        fd.add(RoundCone(p0, p1, 0.022, 0.02), 0.0)
        for q in (p0, p1):
            sd = norm(np.cross(d, v3((0, 0, 1))))
            fd.add(Sphere(q + sd * 0.016, 0.03), 0.012)
            fd.add(Sphere(q - sd * 0.016, 0.028), 0.012)
    # a curved rib
    rib = [b + v3((0.12, -0.12, 0.02)), b + v3((0.2, -0.02, 0.09)), b + v3((0.2, 0.1, 0.1)), b + v3((0.13, 0.17, 0.03))]
    fd.add(Chain(rib, [0.016, 0.015, 0.013, 0.01], k=0.01), 0.0)
    return fd


def tusks_field():
    fd = Field("Tusks")
    f, up, side = skull_frame()
    c = SKULL_C
    L = lambda x, y, z: c + side * x + f * y + up * z
    for sx in (-1, 1):
        p0 = L(sx * 0.085, 0.17, 0.04)
        p1 = L(sx * 0.11, 0.42, -0.04)
        p2 = L(sx * 0.3, 0.55, 0.12)
        p3 = L(sx * 0.18, 0.5, 0.36)
        ts = np.linspace(0, 1, 18)
        pts = [bez3(p0, p1, p2, p3, t) for t in ts]
        pts = [np.array((p[0], p[1], max(p[2], GROUND_TOP + 0.06 * (1 - t) + 0.035))) for p, t in zip(pts, ts)]
        rad = [0.05 * (1 - t) ** 0.8 + 0.008 for t in ts]
        fd.add(Chain(pts, rad, k=0.01, disp=lambda P: F(0.002) * NOISE(P * np.array([40, 40, 8], F)), disp_amp=0.003), 0.0)
    return fd


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(13)
    n = 0
    tries = 0
    while n < 16 and tries < 500:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.3, 1.2)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if np.linalg.norm(p[:2] - SKULL_C[:2]) < 0.35 or np.linalg.norm(p[:2] - BONES_C[:2]) < 0.25 or np.linalg.norm(p[:2] - STAND[:2]) < 0.3:
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.025, 0.045), seed=100 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


# ---------------------------------------------------------------------------------------- direct geometry
def _avoid():
    av = [((0.0, 0.0), ARENA_R + 0.06), (tuple(SKULL_C[:2] + SKULL_FWD[:2] * 0.2), 0.42), (tuple(BONES_C[:2]), 0.26)]
    for i in range(len(HENGE)):
        b, t, o = henge_axis(i)
        av.append((tuple(b[:2]), 0.26))
    av += [((1.05, -0.02), 0.2), ((-1.04, -0.12), 0.18)]
    return av


def grass_geometry(seed=17):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    avoid = _avoid()
    tufts = []
    tries = 0
    while len(tufts) < 34 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(ARENA_R + 0.08, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - np.array(q)) < rr for q, rr in avoid[1:]):
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


def flower_geometry(seed=23):
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    avoid = _avoid()
    while len(spots) < 8 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(ARENA_R + 0.1, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - np.array(q)) < rr for q, rr in avoid[1:]):
            continue
        if any(np.linalg.norm(c[:2] - s[0][:2]) < 0.2 for s in spots):
            continue
        spots.append((c, rs.randint(0, 3)))
    for c, kind in spots:
        base = v3((c[0], c[1], ground_height(c[0], c[1]) - 0.01))
        h = rs.uniform(0.1, 0.15)
        top = base + v3((rs.uniform(-0.02, 0.02), rs.uniform(-0.02, 0.02), h))
        sv, sf, _ = _b.blade_mesh(base, top - base, h, 0.012, (0, 0, 0), segs=2)
        out.append((sv, sf, 0, kind))
        n = 5
        pr = 0.035
        tilt = norm(v3((rs.uniform(-0.3, 0.3), rs.uniform(-0.5, -0.1), 1.0)))
        R = rot_from_axes(z_axis=tilt)
        pv, pf = [], []
        for k in range(n):
            a = 2 * math.pi * k / n
            dirk = R @ v3((math.cos(a), math.sin(a), 0.12))
            sidek = R @ v3((-math.sin(a), math.cos(a), 0))
            b0 = len(pv)
            pv += [top + tilt * 0.004, top + dirk * pr * 0.55 + sidek * pr * 0.42, top + dirk * pr, top + dirk * pr * 0.55 - sidek * pr * 0.42]
            pf.append((b0, b0 + 1, b0 + 2, b0 + 3))
        out.append((pv, pf, 1, kind))
        cv = [top + R @ v3((math.cos(2 * math.pi * k / 6) * 0.012, math.sin(2 * math.pi * k / 6) * 0.012, 0.008)) for k in range(6)]
        cv.append(top + R @ v3((0, 0, 0.016)))
        out.append((cv, [(k, (k + 1) % 6, 6) for k in range(6)], 2, kind))
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Rocks", rocks_field(), 0.006), ("Bone", bone_field(), 0.004),
            ("Tusks", tusks_field(), 0.004), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Ground",)
LOW_TARGETS = {"Ground": 1500, "Rocks": 2900, "Bone": 1100, "Tusks": 700, "Pebbles": 420}
FLAME_PIVOT = None
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_ArenaGround", "dirt_label": DIRT}),
                 "Rocks": ("stone", {"name": "HQ_HengeStone", "moss": True}),
                 "Tusks": ("bone", {"name": "HQ_Tusk", "banded": True})}


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and r > ARENA_R + 0.08 and r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
