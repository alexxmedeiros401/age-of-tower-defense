"""Halberdier base: a corner of the star fort's gate. A round floor of big flagstones laid in courses (each slab set a hair
high or low, the joints sunk and gritty) inside a kerb of curved pale stone blocks, on a grassy mound; behind him on his
right a weapon rack (two posts and two rails) with two more halberds and a pike leaning in it; behind him on his left a
crimson flag with a ragged gold saltire flying from a pole with an iron finial; on his left a barrel bound with iron
hoops and a little pyramid of iron shot beside it; tropical green at the edge: a young palm on his right, a clump of
ferns at the front on his left; grass (distance fields + direct low-poly geometry for the grass)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
from sunpriest_base import ring_func

GROUND_R = 1.32
GROUND_TOP = 0.1
TOP_Z = 0.22                       # the flagstones' tops = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
FLOOR_R = 0.8                      # the flagged floor (inside the kerb)
KERB_R = 0.97
KERB_TOP = TOP_Z + 0.035
RACK_C = v3((-0.5, 0.84, 0.0))     # the weapon rack (behind him, on his right)
RACK_AX = norm(v3((1.0, -0.52, 0.0)))       # along its rails
POLE_C = v3((0.44, 0.9, 0.0))      # the flag's pole (behind him, on his left)
POLE_H = 2.05
BARREL_C = v3((0.88, 0.32, 0.0))   # the barrel (on his left)
SHOT_C = v3((0.98, -0.02, 0.0))    # the iron shot beside it
PALM_C = v3((-1.04, 0.16, 0.0))    # the young palm (on his right)
FERN_C = v3((0.94, -0.5, 0.0))     # the ferns (at the front, on his left)


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 1.1) + F(0.02) * np.sin(a * 11 + 0.4) + F(0.015) * NOISE(P * F(3))
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


def _hash(a, b, s):
    h = np.sin(a * F(127.1) + b * F(311.7) + F(s)) * F(43758.5453)
    return h - np.floor(h)


ROW_H = 0.27                       # the courses' width (along y)


def slab(P):
    """The flag under each point: (distance to the nearest joint, the slab's own lift, a 0-1 hash of it). Courses run
    across him (along x), each course's slabs a different length, the joints staggered."""
    yy = P[:, 1] / F(ROW_H) + F(0.43)
    r = np.floor(yy)
    fy = yy - r
    L = F(0.34) + F(0.16) * _hash(r, F(3.0), 1.7)
    xx = P[:, 0] / L + _hash(r, F(7.0), 4.1)
    c = np.floor(xx)
    fx = xx - c
    dj = np.minimum(np.minimum(fx, F(1) - fx) * L, np.minimum(fy, F(1) - fy) * F(ROW_H))
    hid = _hash(r, c, 9.3)
    return dj, (hid - F(0.5)) * F(0.007), hid


def floor_field():
    """The flagstones (label 0; a lighter, browner stone for some of them, 7), worn soft at their edges, the joints sunk,
    cut round by the kerb."""
    fd = Field("Floor")
    def fn(P):
        dj, lift, hid = slab(P)
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        top = F(TOP_Z) + lift - F(0.013) * np.clip(F(1) - dj / F(0.013), 0, 1) ** 2 - F(0.004) * np.clip(F(1) - dj / F(0.05), 0, 1)
        dz = np.maximum(P[:, 2] - top, F(GROUND_TOP - 0.05) - P[:, 2])
        return np.maximum(dz * F(0.8), r - F(FLOOR_R + 0.01))
    R = FLOOR_R + 0.05
    fd.add(Func(fn, (-R, -R, GROUND_TOP - 0.08), (R, R, TOP_Z + 0.03), disp=_chip, disp_amp=0.005), 0.0)
    fd.paint(Func(lambda P: F(0.68) - slab(P)[2], (-R, -R, GROUND_TOP - 0.08), (R, R, TOP_Z + 0.03)), 7)
    return fd


def kerb_field():
    """Curved blocks of pale dressed stone round the floor (label 0)."""
    fd = Field("Kerb")
    fd.add(ring_func(FLOOR_R - 0.005, KERB_R, 14, 517, KERB_TOP, (KERB_TOP - GROUND_TOP + 0.06) / 2, jitter=0.7, chip=_chip), 0.0)
    return fd


def _ground_at(c, sink=0.03):
    return v3((c[0], c[1], ground_height(c[0], c[1]) - sink))


# ---------------------------------------------------------------------------------------------- the weapon rack
def rack_weapons():
    """(name, foot, lean direction, length) of the weapons standing in the rack: two halberds and a pike."""
    rg = _ground_at(RACK_C, 0.0)
    side = norm(np.cross(RACK_AX, v3((0, 0, 1))))               # toward the floor's middle
    out = []
    for name, off, L in (("halberd", -0.17, 1.72), ("pike", 0.0, 2.12), ("halberd", 0.17, 1.66)):
        f0 = rg + RACK_AX * off + side * 0.13 + v3((0, 0, 0.0))
        top = rg + RACK_AX * (off * 1.05) - side * 0.02 + v3((0, 0, 0.92))
        d = norm(top - f0)
        out.append((name, f0, d, L))
    return out


def _rack_post_feet():
    rg = _ground_at(RACK_C)
    return [rg + RACK_AX * (s * 0.28) for s in (-1, 1)]


def wood_field():
    """Timber (siege: grain along Z 11, along X 10, label 0 along Y): the rack (two posts, two rails), the hafts of the
    halberds and the pike, the flag's pole, the barrel's staves (11); iron (6): the weapons' heads, the barrel's hoops,
    the pole's finial."""
    fd = Field("Wood")
    side = norm(np.cross(RACK_AX, v3((0, 0, 1))))
    for p0 in _rack_post_feet():
        fd.add(RoundCone(p0, p0 + v3((0, 0, 1.0)), 0.026, 0.023), 0.0, 11)
        fd.add(Sphere(p0 + v3((0, 0, 1.0)), 0.028), 0.006, 11)
    rg = _ground_at(RACK_C)
    for z, r in ((0.96, 0.02), (0.36, 0.018)):
        fd.add(RoundCone(rg + RACK_AX * -0.33 + v3((0, 0, z)), rg + RACK_AX * 0.33 + v3((0, 0, z)), r, r), 0.004, 10)
    # the weapons: ash hafts, iron heads
    for name, f0, d, L in rack_weapons():
        fd.add(RoundCone(f0, f0 + d * (L - (0.3 if name == "halberd" else 0.22)), 0.017, 0.016), 0.004, 11)
        fd.add(RoundCone(f0, f0 + d * 0.05, 0.019, 0.018), 0.003, 6)
        hb = norm(np.cross(d, side)) if name == "halberd" else None
        if name == "halberd":
            _rack_halberd_head(fd, f0, d, L, side)
        else:
            tip = f0 + d * L
            sk = f0 + d * (L - 0.24)
            fd.add(RoundCone(sk, sk + d * 0.06, 0.02, 0.017), 0.003, 6)                     # the socket
            fd.add(Ellipsoid(sk + d * 0.14, (0.026, 0.008, 0.1), R=rot_from_axes(z_axis=d, y_axis=side)), 0.004, 6)   # leaf head
            fd.add(RoundCone(sk + d * 0.2, tip, 0.008, 0.002), 0.004, 6)
            for s in (-1, 1):                                                                 # langets
                fd.add(RoundBox(sk - d * 0.08 + side * s * 0.016, (0.004, 0.006, 0.08), 0.002, R=rot_from_axes(z_axis=d, x_axis=side)), 0.002, 6)
    # the flag's pole, an iron finial (a spearhead and a ball)
    pg = _ground_at(POLE_C, 0.02)
    fd.add(RoundCone(pg, pg + v3((0, 0, POLE_H)), 0.027, 0.02), 0.0, 11)
    tip = pg + v3((0, 0, POLE_H))
    fd.add(Sphere(tip + v3((0, 0, 0.015)), 0.026), 0.004, 6)
    fd.add(Ellipsoid(tip + v3((0, 0, 0.09)), (0.02, 0.008, 0.06)), 0.004, 6)
    fd.add(Torus(pg + v3((0, 0, 0.12)), 0.029, 0.006), 0.002, 6)
    # the barrel: bulging staves, iron hoops, a lid
    bg = _ground_at(BARREL_C, 0.0)
    H, R0, R1 = 0.5, 0.15, 0.185
    def barrel(P):
        q = P - bg.astype(F)
        z = q[:, 2]
        t = np.clip(z / F(H), 0, 1)
        r = F(R0) + (F(R1) - F(R0)) * np.sin(t * F(math.pi))
        a = np.arctan2(q[:, 1], q[:, 0])
        stave = F(0.0025) * np.abs(np.sin(a * F(11)))                       # the joints between the staves
        rho = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        return np.maximum(rho - r + stave, np.abs(z - F(H / 2)) - F(H / 2))
    fd.add(Func(barrel, bg - v3((0.25, 0.25, 0.02)), bg + v3((0.25, 0.25, H + 0.02))), 0.0, 11)
    fd.sub(Cylinder(bg + v3((0, 0, H)), R0 - 0.014, 0.024, rr=0.004), 0.003)                     # the lid set in
    for zf in (0.06, 0.22, 0.78, 0.94):
        z = H * zf
        rr = R0 + (R1 - R0) * math.sin(zf * math.pi) + 0.004
        fd.add(Torus(bg + v3((0, 0, z)), rr, 0.009), 0.003, 6)
    return fd


def _rack_halberd_head(fd, f0, d, L, side):
    """A plain halberd's head (iron): a socket, an axe blade, a back spike and a top spike."""
    top = f0 + d * L
    s0 = f0 + d * (L - 0.32)
    b = norm(np.cross(d, side))                                   # the blade's side (along the rails)
    fd.add(RoundCone(s0, s0 + d * 0.12, 0.022, 0.019), 0.003, 6)
    hc = s0 + d * 0.12
    fd.add(RoundBox(hc + b * 0.075, (0.07, 0.006, 0.075), 0.004, R=rot_from_axes(z_axis=d, x_axis=b)), 0.004, 6)
    fd.add(Ellipsoid(hc + b * 0.14 - d * 0.005, (0.012, 0.0055, 0.09), R=rot_from_axes(z_axis=d, x_axis=b)), 0.008, 6)  # the edge
    fd.add(RoundCone(hc - b * 0.02, hc - b * 0.11 - d * 0.03, 0.013, 0.003), 0.004, 6)
    fd.add(RoundCone(hc + d * 0.05, top, 0.012, 0.002), 0.004, 6)


# ---------------------------------------------------------------------------------------------- the flag
FLAG_W, FLAG_H = 0.58, 0.4


def flag_frame():
    pg = _ground_at(POLE_C, 0.02)
    top = pg + v3((0, 0, POLE_H - 0.07))
    out = norm(v3((0.62, 0.78, 0.0)))                      # it flies out behind, away from the floor
    return top, out


def flag_field():
    """The flag: crimson wool (label 0), a ragged gold saltire (6) from corner to corner, a gold fringe (5) along its
    fly; it flies out from the pole in two soft waves."""
    fd = Field("Flag")
    top, out = flag_frame()
    up = v3((0, 0, 1))
    nrm = np.cross(up, out)
    def coords(P):
        q = P - top.astype(F)
        u = q @ out.astype(F)                                # out along the fly
        v = -(q @ up.astype(F))                              # down
        w = q @ nrm.astype(F)
        wave = F(0.05) * np.sin(u * F(9.5) + F(0.6)) * np.clip(u / F(0.12), 0, 1) - F(0.06) * (u / F(FLAG_W)) ** 2 * F(0.0)
        droop = F(0.06) * (u / F(FLAG_W)) ** 2
        return u, v - droop, w - wave
    def flag(P):
        u, v, w = coords(P)
        return np.maximum(np.maximum(np.maximum(-u, u - F(FLAG_W)), np.maximum(-v, v - F(FLAG_H))), np.abs(w) - F(0.006))
    lo, hi = top - v3((0.7, 0.7, FLAG_H + 0.2)), top + v3((0.7, 0.7, 0.12))
    fd.add(Func(flag, lo, hi), 0.0)
    def saltire(P):
        u, v, w = coords(P)
        a = u / F(FLAG_W)
        b = v / F(FLAG_H)
        rag = F(0.012) * np.sign(np.sin(a * F(40)))                    # ragged (knotty) bars
        d1 = np.abs(b - a) * F(FLAG_H) - F(0.03) - rag
        d2 = np.abs(b - (F(1) - a)) * F(FLAG_H) - F(0.03) + rag
        return np.minimum(d1, d2)
    fd.paint(Func(saltire, lo, hi), 6)
    fd.paint(Func(lambda P: F(FLAG_W - 0.035) - coords(P)[0], lo, hi), 5)
    return fd


# ---------------------------------------------------------------------------------------------- iron shot
def shot_field():
    """A little pyramid of iron shot (four balls) on the grass."""
    fd = Field("Shot")
    g = _ground_at(SHOT_C, 0.0)
    r = 0.058
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        fd.add(Sphere(g + v3((math.cos(a) * r * 1.16, math.sin(a) * r * 1.16, r - 0.008)), r), 0.002)
    fd.add(Sphere(g + v3((0, 0, r - 0.008 + r * 1.63)), r), 0.002)
    return fd


# ---------------------------------------------------------------------------------------------- green
def _frond(fd, root, d, L, side_dir, seed, size=0.055, label=0):
    """A fern frond: an arching stem (label 7) with leaflets in pairs (label), shrinking toward its tip."""
    pts = []
    for k in range(7):
        u = k / 6
        p = root + d * (L * u) + v3((0, 0, 0.22 * L * math.sin(math.pi * u * 0.8) - 0.18 * L * u * u))
        pts.append(p)
    fd.add(Chain(pts, [0.006 - 0.004 * k / 6 for k in range(7)], k=0.003), 0.003, 7)
    for i in range(1, 14):
        u = i / 14
        s = u * 6
        j = min(int(s), 5)
        p = lerp(pts[j], pts[j + 1], s - j)
        t = norm(pts[j + 1] - pts[j])
        sd = norm(side_dir - t * float(side_dir @ t))
        sz = size * (1.0 - 0.75 * u) * (0.6 + 0.4 * math.sin(math.pi * min(1.0, u * 1.6)))
        for sg in (-1, 1):
            c = p + sd * (sg * sz * 0.95) + v3((0, 0, -0.008 * u))
            fd.add(Ellipsoid(c, (sz, 0.0035, sz * 0.32), R=rot_from_axes(x_axis=sd * sg + t * 0.35, y_axis=v3((0, 0, 1)))), 0.003, label)


def green_field():
    """Tropical green (leafy: green leaves 0, stems 7): a clump of ferns at the front on his left; the young palm's
    fronds on his right, arching out from its crown, each a midrib (7) with long narrow leaflets in pairs."""
    fd = Field("Green")
    rs = np.random.RandomState(29)
    c = FERN_C + v3((0, 0, ground_height(FERN_C[0], FERN_C[1]) - 0.01))
    for k in range(9):
        a = 2 * math.pi * k / 9 + rs.uniform(-0.2, 0.2)
        d = norm(v3((math.cos(a), math.sin(a), 0.9)))
        sd = norm(np.cross(v3((0, 0, 1)), d))
        _frond(fd, c + v3((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.0)), d, rs.uniform(0.28, 0.38), sd, 300 + k)
    # the palm's fronds
    crown = palm_crown()
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.35
        u = (k % 3) / 2.0
        el = math.radians(52 - 30 * u)
        dh = v3((math.cos(a), math.sin(a), 0.0))
        # (the fronds over the floor rise more steeply: they must clear his halberd)
        inward = max(0.0, float(dh @ norm(-PALM_C * v3((1, 1, 0)))))
        el += math.radians(22) * inward
        L = 0.62 - 0.1 * u
        pts = []
        for i in range(8):
            t = i / 7
            pts.append(crown + dh * (L * t * math.cos(el)) + v3((0, 0, L * t * math.sin(el) - 0.42 * L * t * t)))
        fd.add(Chain(pts, [0.009 - 0.006 * i / 7 for i in range(8)], k=0.004), 0.003, 7)
        sd = norm(np.cross(v3((0, 0, 1)), dh))
        for i in range(1, 16):
            t = i / 16
            s = t * 7
            j = min(int(s), 6)
            p = lerp(pts[j], pts[j + 1], s - j)
            tg = norm(pts[j + 1] - pts[j])
            ln = 0.15 * math.sin(math.pi * min(1.0, 0.15 + t * 0.95)) + 0.03
            for sg in (-1, 1):
                ld = norm(sd * sg * 0.8 + tg * 0.45 + v3((0, 0, -0.35)))
                fd.add(Ellipsoid(p + ld * ln * 0.5, (0.011, 0.003, ln * 0.5), R=rot_from_axes(z_axis=ld, y_axis=norm(np.cross(ld, tg)))), 0.003, 0)
    return fd


def palm_crown():
    g = _ground_at(PALM_C, 0.0)
    return g + v3((0.03, 0.01, 0.5))


def trunk_field():
    """The young palm's trunk (bark, label 0): short and thick, ringed with the scars of old fronds, flaring at its foot;
    the stubs of old fronds round its top."""
    fd = Field("Trunk")
    g = _ground_at(PALM_C, 0.04)
    top = palm_crown()
    rings = lambda P: F(0.006) * np.abs(np.sin((P[:, 2] - F(g[2])) * F(70))) + F(0.002) * NOISE(P * F(30))
    fd.add(RoundCone(g, top, 0.105, 0.075, disp=rings, disp_amp=0.008), 0.0)
    fd.add(Ellipsoid(g + v3((0, 0, 0.04)), (0.16, 0.16, 0.1)), 0.06)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.2
        b0 = top + v3((0.05 * math.cos(a), 0.05 * math.sin(a), -0.03))
        fd.add(RoundCone(b0, b0 + v3((0.1 * math.cos(a), 0.1 * math.sin(a), 0.03)), 0.03, 0.012), 0.012)
    return fd


# ---------------------------------------------------------------------------------------------- grass
def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < KERB_R + 0.05 + pad:
        return True
    for p, r in ((RACK_C, 0.42), (POLE_C, 0.08), (BARREL_C, 0.24), (SHOT_C, 0.15), (PALM_C, 0.22), (FERN_C, 0.24)):
        if math.hypot(c[0] - p[0], c[1] - p[1]) < r + pad:
            return True
    return False


def grass_geometry(seed=67):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 26 and tries < 8000:
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
        big = 0.75 + 0.45 * rs.rand()
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


def flower_geometry(seed=71):
    return []


def fields():
    return [("Ground", ground_field(), 0.008), ("Floor", floor_field(), 0.0036), ("Kerb", kerb_field(), 0.0042),
            ("Wood", wood_field(), 0.0024), ("Flag", flag_field(), 0.0024), ("Shot", shot_field(), 0.003),
            ("Green", green_field(), 0.0022), ("Trunk", trunk_field(), 0.003)]


REGION_PARTS = ("Floor", "Wood", "Flag", "Green")
LOW_TARGETS = {"Ground": 1500, "Floor": 2800, "Kerb": 1100, "Wood": 1700, "Flag": 500, "Shot": 300, "Green": 1900, "Trunk": 350}
CRIMSON = (0.55, 0.08, 0.08)
GOLD = (0.85, 0.62, 0.2)
MAT_OVERRIDES = {"Floor": ("flagstone", {"name": "HQ_FortFlags", "base": (0.5, 0.47, 0.43), "alt": (0.62, 0.56, 0.47)}),
                 "Kerb": ("limestone", {"name": "HQ_FortKerb"}),
                 "Wood": ("siege", {"name": "HQ_FortWood", "wood": (0.55, 0.38, 0.22), "wood2": (0.4, 0.26, 0.14),
                                    "red": CRIMSON, "blue": GOLD, "metal": "iron"}),
                 "Flag": ("wool", {"name": "HQ_FortFlag", "base": CRIMSON, "border": GOLD, "stripe": GOLD}),
                 "Shot": ("iron", {"name": "HQ_FortShot"}),
                 "Green": ("leafy", {"name": "HQ_FortGreen", "leaf": (0.17, 0.42, 0.13), "vein": (0.38, 0.62, 0.2),
                                     "twig": (0.32, 0.36, 0.14)}),
                 "Trunk": ("bark_wood", {"name": "HQ_PalmTrunk", "bark": (0.42, 0.32, 0.22), "wood": (0.72, 0.6, 0.44)})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035 and r > KERB_R + 0.02
    return n.z > 0.55 and on_ground
