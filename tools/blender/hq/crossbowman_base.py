"""Crossbowman base: the top of a round tower. A floor of grey flagstones (rings of curved slabs round a centre slab,
worn smooth where he stands) inside a stone parapet of curved blocks, crenellated: merlons round it, the ones at the
back pierced with cross-shaped arrow loops; a big pavise propped against the parapet behind him on his left (a tall
wooden shield, a ridge down its middle, blue with a yellow cross, iron studs round its edge); a small barrel of spare
bolts behind him on his right; a blue swallow-tailed pennant on a pole lashed to the back merlon; the tower's drum below
the parapet in courses of blocks rising from a grassy mound, grass and wild flowers round its foot (distance fields +
direct low-poly geometry for the grass and flowers)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
from sunpriest_base import ring_func

GROUND_R = 1.32
GROUND_TOP = 0.08
DRUM_R = 1.04                      # the tower's outer face
WALL_IN = 0.84                     # the parapet's inner face
FLOOR_Z = 0.3                      # the floor = where he stands
TOP_Z = FLOOR_Z
STAND = v3((0.0, 0.0, FLOOR_Z))
COURSE = 0.12
WALL_TOP = FLOOR_Z + 2 * COURSE    # the parapet's walk (between the merlons)
MERLON_H = 0.24
N_MERLON = 8
PAV_C = v3((0.5, 0.56, FLOOR_Z))   # the pavise's foot (behind him, on his left)
PAV_N = norm(v3((-0.42, -1.0, 0.36)))     # its face: toward the middle, tipped back against the parapet
PAV_W, PAV_H = 0.27, 0.5           # half width, half height
BAR_C = v3((-0.5, 0.5, FLOOR_Z))   # the barrel of bolts (behind him, on his right)
BAR_R, BAR_H = 0.13, 0.3
POLE_C = v3((0.0, 0.95, 0.0))      # the pennant's pole, lashed to the back merlon


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 1.3) + F(0.02) * np.sin(a * 11 + 0.4) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.03) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _chip(P):
    return F(0.004) * NOISE(P * F(9)) + F(0.002) * NOISE(P * F(31))


def _fine(P):
    return F(0.0014) * NOISE(P * F(9)) + F(0.0007) * NOISE(P * F(31))


def merlon_angle(k):
    return 2 * math.pi * (k + 0.5) / N_MERLON + math.pi / 2           # (one straight behind him, at +Y)


def merlon_func(k, half_deg=13.5):
    a0 = merlon_angle(k)
    half = math.radians(half_deg)
    def fn(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        da = np.mod(a - F(a0) + F(math.pi), F(2 * math.pi)) - F(math.pi)
        d_a = np.abs(da) * r - F(half) * r
        d_r = np.maximum(F(WALL_IN + 0.005) - r, r - F(DRUM_R - 0.005))
        d_z = np.abs(P[:, 2] - F(WALL_TOP + MERLON_H / 2)) - F(MERLON_H / 2)
        q = np.stack([d_a + F(0.012), d_r + F(0.012), d_z + F(0.012)], 1)
        return np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - F(0.012)
    R = DRUM_R + 0.05
    return Func(fn, (-R, -R, WALL_TOP - 0.02), (R, R, WALL_TOP + MERLON_H + 0.03), disp=_chip, disp_amp=0.006)


def masonry_field():
    """Grey stone (label 0; weathered dark and green low down, 7): the drum in two courses below the floor, the parapet
    in two courses above it, eight merlons, cross-shaped arrow loops through the three at the back."""
    fd = Field("Masonry")
    hz = COURSE / 2
    for j, z in enumerate((FLOOR_Z - COURSE, FLOOR_Z, FLOOR_Z + COURSE, WALL_TOP)):
        r0 = 0.6 if z <= FLOOR_Z else WALL_IN
        fd.add(ring_func(r0, DRUM_R, 16, 301 + j, z, hz, jitter=0.6, chip=_chip), 0.0)
    fd.add(Cylinder(v3((0, 0, (GROUND_TOP - 0.1 + FLOOR_Z - 2 * COURSE) / 2)), DRUM_R - 0.01, FLOOR_Z - 2 * COURSE - GROUND_TOP + 0.1,
                    rr=0.01, disp=_chip, disp_amp=0.006), 0.0)
    for k in range(N_MERLON):
        fd.add(merlon_func(k), 0.004)
    for k in range(N_MERLON):
        a = merlon_angle(k)
        if math.sin(a) < 0.3:                                        # (loops only in the merlons behind him)
            continue
        d = v3((math.cos(a), math.sin(a), 0.0))
        c = d * ((WALL_IN + DRUM_R) / 2) + v3((0, 0, WALL_TOP + MERLON_H * 0.55))
        R = rot_from_axes(z_axis=(0, 0, 1), y_axis=d)
        fd.sub(RoundBox(c, (0.014, 0.2, 0.08), 0.004, R=R), 0.004)
        fd.sub(RoundBox(c + v3((0, 0, 0.02)), (0.045, 0.2, 0.012), 0.004, R=R), 0.004)
    fd.paint(Func(lambda P: (P[:, 2] - F(FLOOR_Z - 0.12)) + F(0.05) * NOISE(P * F(4)), (-1.2, -1.2, -0.2), (1.2, 1.2, 0.4)), 7)
    return fd


def floor_field():
    """Flagstones (label 0; a browner stone for some, 7; worn smooth where he stands, 6 is the soot... none): a centre
    slab, two rings of curved slabs out to the parapet."""
    fd = Field("Floor")
    hz = 0.05
    fd.add(Cylinder(v3((0, 0, FLOOR_Z - hz)), 0.245, 2 * hz, rr=0.008, disp=_fine, disp_amp=0.003), 0.0)
    fd.add(ring_func(0.25, 0.55, 8, 331, FLOOR_Z, hz, jitter=0.5, chip=_fine), 0.0)
    fd.add(ring_func(0.55, WALL_IN + 0.02, 13, 337, FLOOR_Z, hz, jitter=0.6, chip=_fine), 0.0)
    rs = np.random.RandomState(9)
    for k in range(5):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.3, 0.8)
        fd.paint(Sphere(v3((math.cos(a) * r, math.sin(a) * r, FLOOR_Z)), rs.uniform(0.12, 0.2)), 7)
    return fd


def _pav_frame():
    N = PAV_N
    up = norm(v3((0, 0, 1)) - N * N[2])
    side = norm(np.cross(up, N))
    c = PAV_C + up * PAV_H + N * 0.0 + v3((0, 0, 0.01))
    return c, N, up, side


def pavise_field():
    """The pavise: a tall board of planks (wood, label 0) with a raised ridge down its middle, its face painted blue (7)
    with a yellow cross (5), iron studs round its edge (6); two props behind it."""
    fd = Field("Pavise")
    c, N, up, side = _pav_frame()
    def board(P):
        q = P - c.astype(F)
        u = q @ side.astype(F)
        v = q @ up.astype(F)
        h = q @ N.astype(F)
        bulge = F(0.04) * (F(1) - (u / F(PAV_W)) ** 2)                 # curved across: its middle stands proud
        ridge = F(0.022) * np.exp(-(u / F(0.035)) ** 2)
        hh = h - bulge - ridge
        width = F(PAV_W) - F(0.04) * smoothstep(0.2, 0.5, (v / F(PAV_H)))   # narrowing a little to its top
        qx = np.abs(u) - width
        qy = np.abs(v) - F(PAV_H)
        qz = np.abs(hh) - F(0.014)
        qq = np.stack([qx, qy, qz], 1) + F(0.01)
        return np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0) - F(0.01)
    fd.add(Func(board, c - 0.7, c + 0.7, disp=lambda P: F(0.001) * NOISE(P * F(40)), disp_amp=0.002), 0.0)
    def front(P):
        q = P - c.astype(F)
        u = q @ side.astype(F)
        bulge = F(0.04) * (F(1) - (u / F(PAV_W)) ** 2) + F(0.022) * np.exp(-(u / F(0.035)) ** 2)
        return bulge + F(0.004) - q @ N.astype(F)
    def cross(P):
        q = P - c.astype(F)
        u = q @ side.astype(F)
        v = q @ up.astype(F)
        bar = np.minimum(np.maximum(np.abs(u) - F(0.045), np.abs(v - F(0.08)) - F(0.36)),
                         np.maximum(np.abs(u) - F(0.2), np.abs(v - F(0.17)) - F(0.045)))
        return np.maximum(bar, front(P))
    fd.paint(Func(lambda P: front(P), c - 0.7, c + 0.7), 7)
    fd.paint(Func(cross, c - 0.7, c + 0.7), 5)
    for k in range(14):
        t = k / 14.0
        per = 2 * (2 * PAV_W + 2 * PAV_H)
        s = t * per
        if s < 2 * PAV_W:
            u, v = -PAV_W + s, PAV_H
        elif s < 2 * PAV_W + 2 * PAV_H:
            u, v = PAV_W, PAV_H - (s - 2 * PAV_W)
        elif s < 4 * PAV_W + 2 * PAV_H:
            u, v = PAV_W - (s - 2 * PAV_W - 2 * PAV_H), -PAV_H
        else:
            u, v = -PAV_W, -PAV_H + (s - 4 * PAV_W - 2 * PAV_H)
        u *= 0.85
        v *= 0.9
        bulge = 0.04 * (1 - (u / PAV_W) ** 2)
        fd.add(Sphere(c + side * u + up * v + N * (bulge + 0.016), 0.012), 0.003, 6)
    # two props behind it, down to the floor
    back = c - N * 0.02
    for sgn in (-1, 1):
        a = back + side * (sgn * 0.16) + up * 0.2
        b = v3((a[0], a[1], FLOOR_Z)) - N * 0.25
        b[2] = FLOOR_Z + 0.01
        fd.add(Chain([a, b], [0.016, 0.016], k=0.003), 0.004)
    return fd


def barrel_field():
    """A small keg of oak staves (wood, label 11: the grain upright) bound with three iron hoops (6), full of spare bolts:
    their shafts (0) and vanes dyed yellow (5) and blue (7) sticking out of its open top."""
    fd = Field("Barrel")
    c = BAR_C
    def keg(P):
        q = P - c.astype(F)
        z = q[:, 2]
        k = (z - F(BAR_H / 2)) / F(BAR_H / 2)
        r = F(BAR_R) * (F(1) + F(0.13) * (F(1) - k * k))
        rr = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        a = np.arctan2(q[:, 1], q[:, 0])
        stave = F(0.0025) * (F(1) - np.abs(np.cos(a * F(9))))
        side = rr - r + stave
        return np.maximum(side, np.abs(z - F(BAR_H / 2)) - F(BAR_H / 2))
    fd.add(Func(keg, c - 0.3, c + v3((0.3, 0.3, 0.4))), 0.0, 11)
    fd.sub(Cylinder(c + v3((0, 0, BAR_H)), BAR_R * 0.92, 0.06), 0.004)
    for zz in (0.05, BAR_H / 2, BAR_H - 0.045):
        kk = (zz - BAR_H / 2) / (BAR_H / 2)
        r = BAR_R * (1 + 0.13 * (1 - kk * kk))
        fd.add(Torus(c + v3((0, 0, zz)), r + 0.002, 0.008), 0.002, 6)
    rs = np.random.RandomState(13)
    for i in range(9):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.0, BAR_R * 0.7)
        base = c + v3((math.cos(a) * r, math.sin(a) * r, BAR_H - 0.12))
        d = norm(v3((rs.uniform(-0.15, 0.15), rs.uniform(-0.15, 0.15), 1.0)))
        top = base + d * rs.uniform(0.2, 0.26)
        fd.add(RoundCone(base, top, 0.0065, 0.006), 0.002)
        vn = norm(np.cross(d, v3((1, 0, 0))))
        lab = 5 if i % 2 else 7
        for sg in (-1, 1):
            fd.add(RoundBox(top - d * 0.035 + vn * sg * 0.012, (0.0012, 0.012, 0.03), 0.001, R=rot_from_axes(z_axis=d, y_axis=vn * sg)), 0.002, lab)
    return fd


def pole_field():
    """The pennant's pole (wood, label 0), lashed to the back merlon with rope (8), an iron cap (6)."""
    fd = Field("Pole")
    a = merlon_angle(1)                                                # the merlon straight behind him
    d = v3((math.cos(a), math.sin(a), 0.0))
    base = d * (DRUM_R + 0.035) + v3((0, 0, FLOOR_Z - 0.05))
    top = base + v3((0, 0, 1.55))
    fd.add(Chain([base, top], [0.022, 0.018], k=0.002, disp=lambda P: F(0.0012) * NOISE(P * F(50)), disp_amp=0.002), 0.0)
    fd.add(Sphere(top + v3((0, 0, 0.012)), 0.026), 0.004, 6)
    for zz in (WALL_TOP + 0.06, WALL_TOP + 0.17):
        fd.add(Torus(base + v3((0, 0, zz - base[2])), 0.026, 0.0055), 0.002, 8)
    return fd


def pole_top():
    a = merlon_angle(1)
    d = v3((math.cos(a), math.sin(a), 0.0))
    return d * (DRUM_R + 0.035) + v3((0, 0, FLOOR_Z - 0.05 + 1.55))


def pennant_field():
    """A long swallow-tailed pennant of blue wool (label 0) with a yellow border (5), streaming out to his right in waves."""
    fd = Field("Pennant")
    top = pole_top()
    L = 0.85
    out = norm(v3((-1.0, -0.15, 0.0)))
    def flag(P):
        q = P - top.astype(F)
        s = q @ out.astype(F)
        z = q[:, 2] + F(0.06)
        k = np.clip(s / F(L), 0, 1)
        wave = F(0.05) * np.sin(s * F(9) + F(0.5)) * k + F(0.012) * np.sin(s * F(23))
        side = norm(np.cross(out, v3((0, 0, 1))))
        h = q @ side.astype(F) - wave
        half = F(0.11) * (F(1) - F(0.55) * k)                            # tapering
        droop = F(0.12) * k * k
        zc = -droop
        fork = np.where(k > F(0.72), F(0.04) * (k - F(0.72)) / F(0.28) - np.abs(z - zc) * F(0.0), F(-1.0))
        notch = np.where(k > F(0.72), (F(0.6) * half * (k - F(0.72)) / F(0.28)) - np.abs(z - zc), F(-1.0))
        dz = np.abs(z - zc) - half
        d = np.maximum(np.maximum(dz, np.maximum(-s, s - F(L))), np.abs(h) - F(0.007))
        return np.maximum(d, notch)
    lo = top - v3((1.1, 0.4, 0.5))
    hi = top + v3((0.2, 0.4, 0.2))
    fd.add(Func(flag, lo, hi), 0.0)
    def border(P):
        q = P - top.astype(F)
        s = q @ out.astype(F)
        k = np.clip(s / F(L), 0, 1)
        half = F(0.11) * (F(1) - F(0.55) * k)
        zc = -F(0.12) * k * k
        z = q[:, 2] + F(0.06)
        return np.minimum(F(0.02) - (half - np.abs(z - zc)), s - F(0.03))
    fd.paint(Func(border, lo, hi), 5)
    return fd


def _blocked(c, pad=0.0):
    return math.hypot(c[0], c[1]) < DRUM_R + 0.06 + pad


def grass_geometry(seed=43):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(DRUM_R + 0.06, GROUND_R - 0.08)
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


def _bloom(out, top, tilt, size, kind_col):
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


def flower_geometry(seed=47):
    """Daisies (swatch 0: white petals) and buttercups (1: yellow) in the grass round the tower's foot."""
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 8 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(DRUM_R + 0.08, GROUND_R - 0.06)
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


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(31)
    n = 0
    tries = 0
    while n < 12 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(DRUM_R + 0.05, 1.26)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, -0.03):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.026, 0.05), seed=560 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def fields():
    return [("Ground", ground_field(), 0.008), ("Masonry", masonry_field(), 0.0045), ("Floor", floor_field(), 0.0042),
            ("Pavise", pavise_field(), 0.0026), ("Barrel", barrel_field(), 0.0024), ("Pole", pole_field(), 0.0026),
            ("Pennant", pennant_field(), 0.0026), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Masonry", "Floor", "Pavise", "Barrel", "Pole", "Pennant")
LOW_TARGETS = {"Ground": 1500, "Masonry": 4200, "Floor": 1600, "Pavise": 900, "Barrel": 700, "Pole": 260, "Pennant": 420,
               "Pebbles": 400}
_BLUE = (0.14, 0.27, 0.62)
_YELLOW = (0.88, 0.66, 0.16)
MAT_OVERRIDES = {"Masonry": ("stone", {"name": "HQ_TowerStone", "moss": True}),
                 "Floor": ("flagstone", {"name": "HQ_TowerFloor"}),
                 "Pavise": ("siege", {"name": "HQ_Pavise", "wood": (0.5, 0.34, 0.2), "wood2": (0.38, 0.25, 0.14), "red": _YELLOW,
                                      "blue": _BLUE, "metal": "iron"}),
                 "Barrel": ("siege", {"name": "HQ_Pavise", "wood": (0.5, 0.34, 0.2), "wood2": (0.38, 0.25, 0.14), "red": _YELLOW,
                                      "blue": _BLUE, "metal": "iron"}),
                 "Pole": ("siege", {"name": "HQ_Pavise", "wood": (0.5, 0.34, 0.2), "wood2": (0.38, 0.25, 0.14), "red": _YELLOW,
                                    "blue": _BLUE, "metal": "iron"}),
                 "Pennant": ("wool", {"name": "HQ_Pennant", "base": _BLUE, "border": _YELLOW, "stripe": _YELLOW}),
                 "Pebbles": ("stone", {"name": "HQ_TowerPebbles"})}
FLAME_PIVOT = None


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035 and r > DRUM_R + 0.02
    return n.z > 0.55 and on_ground
