"""Wren's stand: a glade in the greenwood. A broad old oak stump sawn flat, where she stands: its rings on the cut top
(two drying cracks running out from the heart), thick ridged bark round it, its roots spreading out into the mossy
forest floor; round it a ring of twelve teal-glowing stones set in the moss (the hero ring, their own emissive mesh),
small flat stones round each. Behind her on her right a straw butt on a three-legged easel with three of her arrows in
the gold; behind her on her left a clump of ferns and red-capped toadstools; fallen oak leaves; pebbles (distance
fields) + grass and flowers (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
import kael_base as kb
import wren as _w

ground_height = kb.ground_height
ground_field = kb.ground_field
GROUND_TOP = kb.GROUND_TOP
GROUND_R = kb.GROUND_R
TOP_Z = 0.3                        # the stump's cut top = where she stands
STAND = v3((0.0, 0.0, TOP_Z))
STUMP_R = 0.6
RING_R = 0.93
N_GLOW = 12
TGT_C = v3((-0.78, 0.74, 0.0))     # the straw butt's easel (behind her, on her right)
TGT_Z = 0.62                       # its centre's height above the ground
TGT_R = 0.22
TGT_N = norm(v3((0.3, -1.0, 0.22)))      # its face: to the front, a little up, turned a little toward the stump
FERNS_C = v3((0.8, 0.66, 0.0))     # ferns and toadstools (behind her, on her left)
ROOTS = [(0.3, 0.96), (1.2, 0.9), (2.05, 1.0), (2.9, 0.92), (3.75, 0.98), (4.6, 0.9), (5.45, 0.95)]   # (angle, reach)


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


# ---------------------------------------------------------------------------------------------- the stump
def stump_radius(a, z):
    return (F(STUMP_R) + F(0.022) * np.sin(a * F(5) + F(0.7)) + F(0.014) * np.sin(a * F(9) + F(2.1))
            + F(0.1) * smoothstep(0.26, 0.08, z))


def stump_field():
    """Oak: ridged bark round it (label 0), the cut top (5: pale wood, its rings) with the bark's edge showing; two
    drying cracks from the heart; root buttresses spreading out and down into the moss."""
    fd = Field("Stump")
    def body(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.sqrt(x * x + y * y)
        a = np.arctan2(y, x)
        ridges = F(0.006) * np.abs(np.sin(a * F(38) + F(0.6) * NOISE(P * F(4)))) + F(0.004) * NOISE(P * F(14))
        dr = r - stump_radius(a, z) - ridges * smoothstep(TOP_Z - 0.004, TOP_Z - 0.03, z)
        dz = np.maximum(z - F(TOP_Z), F(-0.05) - z)
        rr = F(0.01)
        q0 = np.maximum(dr + rr, 0)
        q1 = np.maximum(dz + rr, 0)
        return np.minimum(np.maximum(dr + rr, dz + rr), 0) + np.sqrt(q0 * q0 + q1 * q1) - rr
    m = STUMP_R + 0.2
    fd.add(Func(body, (-m, -m, -0.1), (m, m, TOP_Z + 0.04), disp=lambda P: F(0.0015) * NOISE(P * F(40)), disp_amp=0.002), 0.0)
    for a, reach in ROOTS:                                               # root buttresses
        d = v3((math.cos(a), math.sin(a), 0.0))
        p0 = d * (STUMP_R - 0.06) + v3((0, 0, 0.17))
        p1 = d * (STUMP_R + 0.16) + v3((0, 0, 0.12))
        x2, y2 = (d * reach)[0], (d * reach)[1]
        p2 = v3((x2, y2, ground_height(x2, y2) - 0.03))
        fd.add(Chain([p0, p1, p2], [0.07, 0.055, 0.025], k=0.02, disp=lambda P: F(0.003) * NOISE(P * F(18)), disp_amp=0.004), 0.05)
    for a, L in ((0.8, 0.42), (3.4, 0.3)):                               # drying cracks out from the heart
        d = v3((math.cos(a), math.sin(a), 0.0))
        p0 = d * 0.06 + v3((0, 0, TOP_Z + 0.003))
        p1 = d * (0.06 + L) + v3((0, 0, TOP_Z + 0.003))
        fd.sub(RoundCone(p0, p1, 0.004, 0.0075), 0.003)
    def cut(P):                                                          # the sawn top, inside the bark's edge
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        return np.maximum(r - (stump_radius(a, TOP_Z) - F(0.035)), F(TOP_Z - 0.012) - P[:, 2])
    fd.paint(Func(cut, (-m, -m, TOP_Z - 0.05), (m, m, TOP_Z + 0.04)), 5)
    return fd


# ---------------------------------------------------------------------------------------------- the hero ring
def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + 0.26
    x, y = math.cos(a) * RING_R, math.sin(a) * RING_R
    return v3((x, y, ground_height(x, y) + 0.01))


def glowstones_field():
    fd = Field("Glowstones")
    for i in range(N_GLOW):
        a = i * 2 * math.pi / N_GLOW + 0.26
        fd.add(Ellipsoid(glow_pos(i), (0.04, 0.032, 0.026), R=euler(0, 0, a)), 0.0)
    return fd


def kerb_field():
    """Small flat stones round each glowing stone (in the moss)."""
    fd = Field("Kerb")
    rs = np.random.RandomState(83)
    for i in range(N_GLOW):
        c = glow_pos(i)
        for k in range(3):
            a = rs.uniform(0, 2 * math.pi)
            p = c + v3((math.cos(a) * 0.058, math.sin(a) * 0.058, -0.008))
            fd.add(Stone(p, rs.uniform(0.02, 0.028), seed=860 + i * 3 + k, squash=(1.2, 1.0, 0.45), noise=0.05), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the straw butt
def _tgt_frame():
    N = TGT_N
    up = norm(v3((0, 0, 1)) - N * N[2])
    side = norm(np.cross(up, N))
    centre = TGT_C + v3((0, 0, ground_height(TGT_C[0], TGT_C[1]) + TGT_Z))
    return centre, N, up, side


def target_field():
    """Coiled straw: rings of straw rope sewn into a thick disc; painted rings (label 5 red, 7 white, 6 the black
    centre... the gold: 9); two rope loops (8) hanging it from the easel's top."""
    fd = Field("Target")
    C, N, up, side = _tgt_frame()
    R = rot_from_axes(z_axis=N, x_axis=side)
    fd.add(Cylinder(C - N * 0.03, TGT_R - 0.01, 0.05, rr=0.012, R=R), 0.0)
    r = 0.022
    while r < TGT_R - 0.008:
        fd.add(Torus(C, r, 0.0145, R=R, disp=lambda P: F(0.0015) * NOISE(P * F(90)), disp_amp=0.002), 0.004)
        r += 0.026
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
    """The easel: three rough poles lashed at the top (bark, label 0; the lashing 7), a crossbar the butt rests on."""
    fd = Field("Wood")
    C, N, up, side = _tgt_frame()
    top, feet = easel_legs()
    for f in feet:
        d = norm(top - f)
        fd.add(Chain([f, top + d * 0.05], [0.019, 0.016], k=0.004, disp=lambda P: F(0.0015) * NOISE(P * F(40)), disp_amp=0.002), 0.004)
    zb = C - up * (TGT_R + 0.01) - N * 0.04
    pts = []
    for f in feet[:2]:
        t = float((zb[2] - f[2]) / (top[2] - f[2]))
        pts.append(f + (top - f) * t)
    fd.add(Chain([pts[0] + (pts[0] - pts[1]) * 0.12, pts[1] + (pts[1] - pts[0]) * 0.12], [0.014, 0.014], k=0.003), 0.004)
    fd.add(Sphere(top, 0.03, disp=lambda P: F(0.002) * NOISE(P * F(60)), disp_amp=0.003), 0.01, 7)
    return fd


def arrows_field():
    """Three of her arrows deep in the butt near its middle: ash (label 0), grey goose fletching (8), cresting (5, 9)."""
    fd = Field("Arrows")
    C, N, up, side = _tgt_frame()
    rs = np.random.RandomState(17)
    for (u, v) in ((0.012, 0.016), (-0.036, -0.02), (0.034, -0.044)):
        hit = C + side * u + up * v + N * 0.01
        ax = norm(-N + side * rs.uniform(-0.15, 0.15) + up * rs.uniform(-0.04, 0.18))      # its flight, into the straw
        L = 0.52
        nock = hit - ax * L
        upv = norm(np.cross(ax, side))
        _w._arrow(fd, nock, ax, upv, full=False)
        fd.add(Chain([nock + ax * 0.01, hit + ax * 0.03], [0.0078, 0.0078], k=0.002), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- ferns and toadstools
def _frond(fd, root, d, L, side_dir, seed):
    """A fern frond: an arching stem (label 7) with leaflets in pairs (0), shrinking toward its tip."""
    rs = np.random.RandomState(seed)
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
        size = 0.055 * (1.0 - 0.75 * u) * (0.6 + 0.4 * math.sin(math.pi * min(1.0, u * 1.6)))
        for sg in (-1, 1):
            c = p + sd * (sg * size * 0.95) + v3((0, 0, -0.008 * u))
            fd.add(Ellipsoid(c, (size, 0.0035, size * 0.32), R=rot_from_axes(x_axis=sd * sg + t * 0.35, y_axis=v3((0, 0, 1)))), 0.003, 0)


def ferns_field():
    fd = Field("Ferns")
    rs = np.random.RandomState(29)
    c = FERNS_C + v3((0, 0, ground_height(FERNS_C[0], FERNS_C[1]) - 0.01))
    for k in range(9):
        a = 2 * math.pi * k / 9 + rs.uniform(-0.2, 0.2)
        d = norm(v3((math.cos(a), math.sin(a), 0.9)))
        sd = norm(np.cross(v3((0, 0, 1)), d))
        _frond(fd, c + v3((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.0)), d, rs.uniform(0.28, 0.38), sd, 300 + k)
    return fd


TOADSTOOLS = [(v3((0.62, 0.5, 0.0)), 0.05, 0.09), (v3((0.56, 0.6, 0.0)), 0.035, 0.065), (v3((0.98, 0.5, 0.0)), 0.042, 0.075),
              (v3((-0.5, -0.86, 0.0)), 0.03, 0.055)]


def toadstools_field():
    """Fly agarics: red caps (label 0) flecked with white (5), white stems (5)."""
    fd = Field("Toadstools")
    rs = np.random.RandomState(31)
    for c, r, h in TOADSTOOLS:
        g = ground_height(c[0], c[1])
        base = c + v3((0, 0, g - 0.02))
        top = base + v3((rs.uniform(-0.01, 0.01), rs.uniform(-0.01, 0.01), h))
        fd.add(RoundCone(base, top, r * 0.32, r * 0.24), 0.01, 5)
        fd.add(Inter(Ellipsoid(top + v3((0, 0, r * 0.05)), (r, r, r * 0.62)), Plane(top - v3((0, 0, r * 0.02)), (0, 0, -1)), 0.006), 0.006, 0)
        for k in range(9):
            a = rs.uniform(0, 2 * math.pi)
            el = rs.uniform(0.25, 1.1)
            p = top + v3((math.cos(a) * r * math.cos(el) * 0.95, math.sin(a) * r * math.cos(el) * 0.95, r * 0.05 + r * 0.6 * math.sin(el)))
            fd.paint(Sphere(p, r * 0.13), 5)
    return fd


# ---------------------------------------------------------------------------------------------- leaves, pebbles
def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < STUMP_R + 0.14 + pad:
        return True
    if math.hypot(c[0] - TGT_C[0], c[1] - TGT_C[1]) < 0.3 + pad:
        return True
    if math.hypot(c[0] - FERNS_C[0], c[1] - FERNS_C[1]) < 0.2 + pad:
        return True
    for t, r, h in TOADSTOOLS:
        if math.hypot(c[0] - t[0], c[1] - t[1]) < r + 0.03 + pad:
            return True
    for i in range(N_GLOW):
        g = glow_pos(i)
        if math.hypot(c[0] - g[0], c[1] - g[1]) < 0.1 + pad:
            return True
    for a, reach in ROOTS:
        d = np.array((math.cos(a), math.sin(a)))
        q = np.array(c[:2])
        along = float(q @ d)
        if STUMP_R < along < reach + 0.02 and abs(float(q @ np.array((-d[1], d[0])))) < 0.06 + pad:
            return True
    return False


def leaves_field():
    """Fallen oak leaves on the moss: lobed, curled a little (green-gold 0, brown 6, yellow 7 in `leafy`)."""
    fd = Field("Leaves")
    rs = np.random.RandomState(47)
    n, tries = 0, 0
    while n < 16 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(STUMP_R + 0.16, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0.0))
        if _blocked(c, 0.0):
            continue
        c[2] = ground_height(c[0], c[1]) + 0.004
        ang = rs.uniform(0, 2 * math.pi)
        ax = v3((math.cos(ang), math.sin(ang), 0.0))
        sd = v3((-ax[1], ax[0], 0.0))
        L = rs.uniform(0.04, 0.06)
        lab = (0, 6, 7)[n % 3]
        for k, u in enumerate((-0.6, -0.2, 0.2, 0.6)):
            w = L * (0.5 if abs(u) > 0.5 else 0.62)
            for sg in (-1, 1):
                fd.add(Ellipsoid(c + ax * (u * L) + sd * (sg * w * 0.45) + v3((0, 0, 0.004 * abs(u))), (w * 0.42, w * 0.38, 0.0028),
                                 R=euler(0, 0, ang)), 0.004, lab)
        fd.add(RoundCone(c - ax * L * 1.05, c + ax * L * 0.9, 0.0035, 0.002), 0.002, lab)
        n += 1
    return fd


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(53)
    n, tries = 0, 0
    while n < 10 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(1.0, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.024, 0.044), seed=900 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=59):
    old = kb._blocked
    kb._blocked = _blocked
    try:
        return kb.grass_geometry(seed)
    finally:
        kb._blocked = old


def flower_geometry(seed=61):
    old = kb._blocked
    kb._blocked = _blocked
    try:
        return kb.flower_geometry(seed)
    finally:
        kb._blocked = old


def fields():
    return [("Ground", ground_field(), 0.008), ("Stump", stump_field(), 0.0042), ("Glowstones", glowstones_field(), 0.0025),
            ("Kerb", kerb_field(), 0.004), ("Target", target_field(), 0.0024), ("Wood", wood_field(), 0.0026),
            ("Arrows", arrows_field(), 0.0014), ("Ferns", ferns_field(), 0.0022), ("Toadstools", toadstools_field(), 0.002),
            ("Leaves", leaves_field(), 0.002), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Stump", "Target", "Wood", "Arrows", "Ferns", "Toadstools", "Leaves")
LOW_TARGETS = {"Ground": 1400, "Stump": 3600, "Glowstones": 400, "Kerb": 500, "Target": 1000, "Wood": 500, "Arrows": 300,
               "Ferns": 1400, "Toadstools": 400, "Leaves": 500, "Pebbles": 300}
MAT_OVERRIDES = {"Stump": ("bark_wood", {"name": "HQ_OakStump", "bark": (0.3, 0.24, 0.18), "wood": (0.78, 0.62, 0.42)}),
                 "Kerb": ("stone", {"name": "HQ_KerbStone", "scale": 0.3}),
                 "Target": ("straw_target", {"name": "HQ_StrawTarget"}),
                 "Wood": ("bark_wood", {"name": "HQ_EaselPoles", "bark": (0.38, 0.3, 0.22), "wood": (0.7, 0.6, 0.46)}),
                 "Arrows": ("arrows", {"name": "HQ_WrenTargetArrows", "shaft": ((0.8, 0.68, 0.48), (0.66, 0.54, 0.36)),
                                       "fletch": ((0.56, 0.56, 0.58), (0.95, 0.94, 0.9)), "crest": (0.16, 0.42, 0.14),
                                       "crest2": (0.72, 0.12, 0.08)}),
                 "Ferns": ("leafy", {"name": "HQ_Fern", "leaf": (0.2, 0.42, 0.12), "vein": (0.4, 0.6, 0.2), "twig": (0.3, 0.32, 0.12)}),
                 "Toadstools": ("terracotta", {"name": "HQ_Toadstool", "base": (0.78, 0.1, 0.05), "paint": (0.96, 0.94, 0.88)}),
                 "Leaves": ("leafy", {"name": "HQ_FallenLeaves", "leaf": (0.5, 0.42, 0.12), "vein": (0.66, 0.54, 0.2),
                                      "mist": (0.5, 0.26, 0.1), "twig": (0.78, 0.6, 0.16)}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
GLOW = {"Glowstones": ((0.3, 1.0, 0.78), 1.0, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and STUMP_R + 0.12 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.08))
