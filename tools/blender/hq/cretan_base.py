"""Cretan Archer base: a marksman's lookout among old marble. A round platform of white marble in two steps (curved blocks
round a centre slab, chipped, the top worn smooth where he kneels) on a grassy hillside mound with grey limestone rocks;
behind him on his left a broken fluted column (two drums standing on a foundation block, the third fallen beside it)
with a black-banded amphora at its foot; behind him on his right a coiled straw target on a wooden easel with three of his
arrows in it; wild thyme, grass and pebbles (distance fields + direct low-poly geometry for the grass and flowers)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
from sunpriest_base import ring_func

GROUND_R = 1.32
GROUND_TOP = 0.12
LOW_Z = 0.21                       # the lower step's top
TOP_Z = 0.3                        # the platform top = where he kneels
STAND = v3((0.0, 0.0, TOP_Z))
CENTRE_R = 0.2                     # the centre slab
UPPER_R = 0.54                     # the upper step's edge
LOWER_R = 0.74                     # the lower step's edge
COL_C = v3((-0.62, 0.76, 0.0))     # the broken column (behind him, on his left)
COL_R = 0.13
DRUM_H = 0.27
COL_TOP = 0.92                     # its broken top, above its foundation block (in the third drum)
FALLEN_C = v3((-1.0, 0.3, 0.0))    # the fallen drum
FALLEN_AX = norm(v3((0.62, 0.78, 0.0)))
POT_C = v3((-0.26, 1.02, 0.0))     # the amphora at the column's foot
TGT_C = v3((0.64, 0.84, 0.0))      # the target's easel (behind him, on his right)
TGT_Z = 0.7                        # the target's centre height
TGT_R = 0.25
TGT_N = norm(v3((-0.22, -1.0, 0.28)))     # its face: to the front, a little up, turned a little toward the platform
ROCKS = [(v3((1.02, -0.4, 0.0)), 0.17, 4), (v3((-1.04, -0.48, 0.0)), 0.13, 5), (v3((0.98, 0.12, 0.0)), 0.085, 6)]


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


def _fine(P):
    return F(0.0012) * NOISE(P * F(9)) + F(0.0006) * NOISE(P * F(31))


def _fluted(Q, r, n=20, depth=0.012):
    """Distance to an upright fluted shaft of radius r (local points, the axis along z); concave flutes."""
    rr = np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2)
    th = np.arctan2(Q[:, 1], Q[:, 0])
    return rr - F(r) + F(depth) * (F(0.5) - F(0.5) * np.cos(F(n) * th))


def column_top(P):
    """The broken top of the standing column: a jagged break, tilted."""
    q = P - COL_C.astype(F)
    return F(COL_TOP) + F(0.07) * q[:, 0] / F(COL_R) - F(0.05) * q[:, 1] / F(COL_R) + F(0.035) * NOISE(P * F(14))


def marble_field():
    """The platform (marble, label 0; the top worn smooth where he kneels, 6; weathered dark low on the outer step, 7),
    the column (two fluted drums on a foundation block, broken off), the fallen drum."""
    fd = Field("Marble")
    fd.add(Cylinder(v3((0, 0, (GROUND_TOP - 0.06 + LOW_Z) / 2)), 0.56, LOW_Z - GROUND_TOP + 0.06, rr=0.01), 0.0)   # core (hidden)
    fd.add(ring_func(0.5, LOWER_R, 18, 71, LOW_Z, (LOW_Z - GROUND_TOP + 0.06) / 2), 0.0)
    fd.add(ring_func(CENTRE_R, UPPER_R, 10, 72, TOP_Z, (TOP_Z - LOW_Z + 0.02) / 2, jitter=0.4, chip=_fine), 0.0)
    fd.add(Cylinder(v3((0, 0, TOP_Z - 0.09)), CENTRE_R - 0.0055, 0.18, rr=0.01, disp=_fine, disp_amp=0.003), 0.0)
    fd.paint(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(0.34), F(TOP_Z - 0.01) - P[:, 2]),
                  (-0.5, -0.5, TOP_Z - 0.05), (0.5, 0.5, TOP_Z + 0.05)), 6)
    fd.paint(Func(lambda P: np.maximum(F(0.62) - np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2), P[:, 2] - F(LOW_Z - 0.035)),
                  (-0.9, -0.9, GROUND_TOP - 0.1), (0.9, 0.9, LOW_Z)), 7)
    # the column: a square foundation block, two fluted drums (a joint between them), the jagged break
    g = ground_height(COL_C[0], COL_C[1])
    z0 = g + 0.09
    fd.add(RoundBox(COL_C + v3((0, 0, g + 0.03)), (0.19, 0.19, 0.065), 0.015, disp=_chip, disp_amp=0.006), 0.0)
    def shaft(P):
        q = P - COL_C.astype(F)
        q[:, 2] -= F(z0)
        rad = np.maximum(_fluted(q, COL_R * (1.0 - 0.05 * 0.5)), F(-0.01) - q[:, 2])
        return np.maximum(rad, P[:, 2] - column_top(P)) * F(0.92)
    fd.add(Func(shaft, COL_C + v3((-0.2, -0.2, z0 - 0.02)), COL_C + v3((0.2, 0.2, z0 + COL_TOP + 0.12)), disp=_chip, disp_amp=0.006), 0.01)
    for k in (1, 2):
        fd.sub(Torus(COL_C + v3((0, 0, z0 + DRUM_H * k)), COL_R + 0.004, 0.006), 0.003)
    fd.paint(Func(lambda P: (P[:, 2] - F(z0 + 0.16)) + F(0.05) * NOISE(P * F(5)), COL_C + v3((-0.25, -0.25, g - 0.05)),
                  COL_C + v3((0.25, 0.25, z0 + 0.3))), 7)
    # the fallen drum, lying on its side half sunk in the grass
    gf = ground_height(FALLEN_C[0], FALLEN_C[1])
    c = FALLEN_C + v3((0, 0, gf + COL_R * 0.72))
    R = rot_from_axes(z_axis=FALLEN_AX, x_axis=(0, 0, 1))
    def drum(P, c=c, R=R):
        q = (P - c.astype(F)) @ R.astype(F)
        return np.maximum(_fluted(q, COL_R), np.abs(q[:, 2]) - F(DRUM_H / 2)) * F(0.92)
    fd.add(Func(drum, c - 0.3, c + 0.3, disp=_chip, disp_amp=0.006), 0.0)
    fd.paint(Func(lambda P: F(gf + 0.06) - P[:, 2] + F(0.03) * NOISE(P * F(6)), c - 0.35, c + 0.35), 7)
    return fd


def pot_field():
    """An amphora of red clay at the column's foot: a swelling body on a small foot, a narrow neck with a rolled rim, two
    handles from neck to shoulder; black painted bands (label 5): the neck, a band round the shoulder, two thin lines
    round the belly."""
    fd = Field("Pot")
    c = POT_C + v3((0, 0, ground_height(POT_C[0], POT_C[1]) - 0.01))
    fd.add(Ellipsoid(c + v3((0, 0, 0.2)), (0.1, 0.1, 0.13)), 0.0)
    fd.add(RoundCone(c + v3((0, 0, 0.05)), c + v3((0, 0, 0.17)), 0.034, 0.09), 0.05)
    fd.add(Cylinder(c + v3((0, 0, 0.025)), 0.046, 0.04, rr=0.008), 0.012)
    fd.add(RoundCone(c + v3((0, 0, 0.29)), c + v3((0, 0, 0.38)), 0.044, 0.038), 0.02)
    fd.add(Torus(c + v3((0, 0, 0.385)), 0.042, 0.012), 0.006)
    fd.sub(Cylinder(c + v3((0, 0, 0.39)), 0.03, 0.05), 0.004)
    for sx in (-1, 1):
        pts = [c + v3((sx * 0.04, 0, 0.355)), c + v3((sx * 0.1, 0, 0.36)), c + v3((sx * 0.112, 0, 0.32)), c + v3((sx * 0.088, 0, 0.27))]
        fd.add(Chain(pts, [0.011, 0.011, 0.011, 0.011], k=0.006), 0.008)
    fd.paint(Func(lambda P: F(c[2] + 0.29) - P[:, 2], c - 0.3, c + 0.5), 5)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(c[2] + 0.235)) - F(0.022), c - 0.3, c + 0.5), 5)
    fd.paint(Func(lambda P: np.minimum(np.abs(P[:, 2] - F(c[2] + 0.15)), np.abs(P[:, 2] - F(c[2] + 0.12))) - F(0.006), c - 0.3, c + 0.5), 5)
    return fd


# ======================================================================================= the target and its easel
def _tgt_frame():
    N = TGT_N
    up = norm(v3((0, 0, 1)) - N * N[2])
    side = norm(np.cross(up, N))
    centre = TGT_C + v3((0, 0, ground_height(TGT_C[0], TGT_C[1]) + TGT_Z - GROUND_TOP))
    return centre, N, up, side


def target_field():
    """Coiled straw: rings of straw rope sewn into a thick disc, the coils standing proud of a backing; painted rings
    (label 5 red, 7 white, 6 the black centre); two rope loops (8) hanging it from the easel's top."""
    fd = Field("Target")
    C, N, up, side = _tgt_frame()
    R = rot_from_axes(z_axis=N, x_axis=side)
    fd.add(Cylinder(C - N * 0.03, TGT_R - 0.01, 0.05, rr=0.012, R=R), 0.0)
    rad = 0.026
    r = 0.022
    while r < TGT_R - 0.008:
        fd.add(Torus(C, r, 0.0145, R=R, disp=lambda P: F(0.0015) * NOISE(P * F(90)), disp_amp=0.002), 0.004)
        r += rad
    def ring(P):
        q = P - C.astype(F)
        h = q @ N.astype(F)
        return np.sqrt(np.maximum((q * q).sum(1) - h * h, 0))
    k = TGT_R / 0.2
    fd.paint(Func(lambda P: ring(P) - F(0.055 * k), C - 0.4, C + 0.4), 6)
    fd.paint(Func(lambda P: np.abs(ring(P) - F(0.08 * k)) - F(0.025 * k), C - 0.4, C + 0.4), 5)
    fd.paint(Func(lambda P: np.abs(ring(P) - F(0.13 * k)) - F(0.025 * k), C - 0.4, C + 0.4), 7)
    fd.paint(Func(lambda P: np.abs(ring(P) - F(0.18 * k)) - F(0.025 * k), C - 0.4, C + 0.4), 5)
    top = C + up * (TGT_R + 0.12) + N * 0.02
    for s in (-1, 1):
        a = C + side * (s * 0.1) + up * (TGT_R - 0.03) - N * 0.02
        fd.add(Chain([a, lerp(a, top, 0.5) + N * 0.012, top], [0.006, 0.006, 0.006], k=0.003), 0.003, 8)
    return fd


def easel_legs():
    C, N, up, side = _tgt_frame()
    top = C + up * (TGT_R + 0.12) - N * 0.02
    g = lambda p: v3((p[0], p[1], ground_height(p[0], p[1]) - 0.03))
    feet = [g(TGT_C + side * 0.22 + N * 0.06), g(TGT_C - side * 0.22 + N * 0.06), g(TGT_C - N * 0.4)]
    return top, feet


def wood_field():
    """The easel: three legs lashed at the top, a crossbar the target rests on."""
    fd = Field("Wood")
    C, N, up, side = _tgt_frame()
    top, feet = easel_legs()
    for k, f in enumerate(feet):
        d = norm(top - f)
        fd.add(Chain([f, top + d * 0.05], [0.019, 0.016], k=0.004, disp=lambda P: F(0.0015) * NOISE(P * F(40)), disp_amp=0.002), 0.004)
    zb = C - up * (TGT_R + 0.01) - N * 0.04
    pts = []
    for s in (-1, 1):
        f = feet[0] if s > 0 else feet[1]
        t = float((zb[2] - f[2]) / (top[2] - f[2]))
        pts.append(f + (top - f) * t)
    fd.add(Chain([pts[0] + (pts[0] - pts[1]) * 0.12, pts[1] + (pts[1] - pts[0]) * 0.12], [0.014, 0.014], k=0.003), 0.004)
    fd.add(Sphere(top, 0.03, disp=lambda P: F(0.002) * NOISE(P * F(60)), disp_amp=0.003), 0.01)        # the lashing
    return fd


def arrows_field():
    """Three of his arrows deep in the target near its middle: reed shafts (label 0), red and white fletching (8)."""
    fd = Field("Arrows")
    C, N, up, side = _tgt_frame()
    rs = np.random.RandomState(7)
    for (u, v) in ((0.018, 0.012), (-0.045, 0.03), (0.03, -0.06)):
        hit = C + side * u + up * v + N * 0.01
        ax = norm(-N + side * rs.uniform(-0.18, 0.18) + up * rs.uniform(-0.05, 0.22))      # its flight, into the straw
        L = 0.58
        nock = hit - ax * L
        fd.add(Chain([nock + ax * 0.01, hit + ax * 0.03], [0.0092, 0.0092], k=0.002), 0.0)
        fd.add(Cylinder(nock + ax * 0.012, 0.0117, 0.026, rr=0.003, R=rot_from_axes(z_axis=ax)), 0.002)
        upv = norm(np.cross(ax, side))
        sd = norm(np.cross(ax, upv))
        for j in range(3):
            ang = j * 2 * math.pi / 3 + 0.4 + rs.uniform(-0.3, 0.3)
            vd = sd * math.cos(ang) + upv * math.sin(ang)
            fc = nock + ax * 0.1 + vd * 0.017
            fd.add(Ellipsoid(fc, (0.0026, 0.019, 0.07), R=rot_from_axes(z_axis=ax, y_axis=vd)), 0.002, 8)
    return fd


def rocks_field():
    fd = Field("Rocks")
    for c, r, seed in ROCKS:
        p = c + v3((0, 0, ground_height(c[0], c[1]) - 0.25 * r))
        fd.add(Stone(p, r, seed=410 + seed, squash=(1.1, 0.95, 0.62), noise=0.08), 0.0)
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < LOWER_R + 0.06 + pad:
        return True
    if math.hypot(c[0] - COL_C[0], c[1] - COL_C[1]) < 0.28 + pad:
        return True
    if math.hypot(c[0] - POT_C[0], c[1] - POT_C[1]) < 0.15 + pad:
        return True
    q = np.array(c[:2]) - FALLEN_C[:2]
    along = float(q @ FALLEN_AX[:2])
    if abs(along) < DRUM_H / 2 + 0.06 + pad and abs(float(q @ np.array([-FALLEN_AX[1], FALLEN_AX[0]]))) < COL_R + 0.06 + pad:
        return True
    top, feet = easel_legs()
    for f in feet:
        if math.hypot(c[0] - f[0], c[1] - f[1]) < 0.08 + pad:
            return True
    for rc, r, s in ROCKS:
        if math.hypot(c[0] - rc[0], c[1] - rc[1]) < r * 1.15 + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(29)
    n = 0
    tries = 0
    while n < 16 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.8, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.024, 0.046), seed=520 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
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
        r = rs.uniform(0.8, GROUND_R - 0.08)
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
            L = rs.uniform(0.12, 0.22) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.042), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
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


def flower_geometry(seed=41):
    """Wild thyme: low clumps of wiry stems with little purple heads (swatch 2); a few yellow rock-roses (swatch 1)."""
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 7 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.82, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.04) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.22 for s in spots):
            continue
        spots.append((c, 2 if len(spots) % 3 else 1))
    for c, col in spots:
        n_stem = rs.randint(6, 10) if col == 2 else rs.randint(3, 5)
        for k in range(n_stem):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.08)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.06, 0.12) if col == 2 else rs.uniform(0.1, 0.16)
            d = norm(v3((math.cos(ang) * 0.45, math.sin(ang) * 0.45, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, col))
            nb = 2 if col == 2 else 1
            for j in range(nb):
                p = root + d * h * (1.0 - 0.25 * j) + v3((rs.uniform(-0.01, 0.01), rs.uniform(-0.01, 0.01), 0))
                tilt = norm(v3((rs.uniform(-0.5, 0.5), rs.uniform(-0.5, 0.5), 1.0)))
                _bloom(out, p, tilt, 0.02 if col == 2 else 0.034, col)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Marble", marble_field(), 0.0042), ("Pot", pot_field(), 0.0024),
            ("Wood", wood_field(), 0.0026), ("Target", target_field(), 0.0024), ("Arrows", arrows_field(), 0.0016),
            ("Rocks", rocks_field(), 0.004), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Marble", "Pot", "Target", "Arrows")
LOW_TARGETS = {"Ground": 1500, "Marble": 3800, "Pot": 700, "Wood": 500, "Target": 1000, "Arrows": 300, "Rocks": 700,
               "Pebbles": 400}
MAT_OVERRIDES = {"Marble": ("marble", {"name": "HQ_CretanMarble"}),
                 "Pot": ("terracotta", {"name": "HQ_Amphora", "base": (0.74, 0.38, 0.2), "paint": (0.09, 0.07, 0.06)}),
                 "Target": ("straw_target", {"name": "HQ_StrawTarget"}),
                 "Arrows": ("arrows", {"name": "HQ_TargetArrows"}),
                 "Rocks": ("stone", {"name": "HQ_CretanRock", "moss": False})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035 and r > LOWER_R + 0.02
    return n.z > 0.55 and on_ground
