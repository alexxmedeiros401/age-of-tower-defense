"""Theron's stand: the forecourt of Apollo's temple at Delphi. A round floor of white marble slabs in two rings round a
centre slab, a gold sun inlaid at its middle (a disc, twelve rays reaching out across the slabs, long and short by
turns); a marble kerb round it with twelve gold diamonds set in its top at the long rays' ends (the hero ring: they glow,
their own emissive mesh); on a low grassy mound. Behind him on his left the stump of a fluted Doric column (two drums on
a step, the upper one broken off), its fallen capital lying in the grass beside it; behind him on his right a marble
stele, pedimented, its face carved with rows of letters (the maxims of the god: know thyself, nothing in excess); at the
floor's edge before him on his right a round scroll box of leather, its lid off, the ends of the scrolls standing up in
it. Pebbles (distance fields) + grass and flowers (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
import kael_base as kb
from sunpriest_base import ring_func

ground_height = kb.ground_height
ground_field = kb.ground_field
GROUND_TOP = kb.GROUND_TOP
GROUND_R = kb.GROUND_R

TOP_Z = 0.3
STAND = v3((0.0, 0.0, TOP_Z))
CENTRE_R = 0.18
RING1_R = 0.4
DECK_R = 0.62
KERB_R = 0.76
KERB_TOP = TOP_Z - 0.01
RING_R = 0.69
N_GLOW = 12
RAY_A0 = math.pi / 12                  # the first long ray's angle (none points straight at the camera)
COLUMN_C = v3((0.76, 0.66, 0.0))
COLUMN_R = 0.16
CAPITAL_C = v3((1.05, 0.22, 0.0))
STELE_C = v3((-0.78, 0.66, 0.0))
STELE_FWD = norm(v3((0.38, -0.92, 0.0)))
CAPSA_C = v3((-0.74, -0.6, 0.0))


def _chip(P):
    return F(0.0018) * NOISE(P * F(11)) + F(0.001) * NOISE(P * F(37))


def ray_angle(i):
    return RAY_A0 + 2 * math.pi * i / 12


# ---------------------------------------------------------------------------------------------- the floor and the sun
def marble_field():
    """The floor's slabs and the kerb (marble, label 0); the floor polished in the middle (6), the kerb's outer face
    weathered (7)."""
    fd = Field("Marble")
    hz = (TOP_Z - GROUND_TOP + 0.06) / 2
    def centre(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        q = np.stack([np.maximum(r - F(CENTRE_R - 0.0055) + F(0.01), 0), np.maximum(np.abs(P[:, 2] - F(TOP_Z - hz)) - F(hz) + F(0.01), 0)], 1)
        inside = np.minimum(np.maximum(r - F(CENTRE_R - 0.0055) + F(0.01), np.abs(P[:, 2] - F(TOP_Z - hz)) - F(hz) + F(0.01)), 0)
        return np.sqrt((q * q).sum(1)) + inside - F(0.01)
    fd.add(Func(centre, (-CENTRE_R, -CENTRE_R, GROUND_TOP - 0.08), (CENTRE_R, CENTRE_R, TOP_Z + 0.01), disp=_chip, disp_amp=0.003), 0.0)
    fd.add(ring_func(CENTRE_R, RING1_R, 8, 411, TOP_Z, hz, jitter=0.35, chip=_chip), 0.0)
    fd.add(ring_func(RING1_R, DECK_R, 12, 419, TOP_Z, hz, jitter=0.35, chip=_chip), 0.0)
    hk = (KERB_TOP - GROUND_TOP + 0.08) / 2
    fd.add(ring_func(DECK_R, KERB_R, 12, 431, KERB_TOP, hk, jitter=0.6, chip=_chip), 0.0)
    fd.paint(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(0.3), F(TOP_Z - 0.01) - P[:, 2]),
                  (-0.5, -0.5, TOP_Z - 0.05), (0.5, 0.5, TOP_Z + 0.03)), 6)
    fd.paint(Func(lambda P: np.maximum(F(KERB_R - 0.01) - np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2), P[:, 2] - F(KERB_TOP - 0.03)),
                  (-1, -1, GROUND_TOP - 0.1), (1, 1, KERB_TOP)), 7)
    return fd


def gold_field():
    """The sun inlaid in the floor: a disc with a raised ring, twelve tapering rays (long and short by turns) a hair proud
    of the marble; the bronze settings of the kerb's diamonds."""
    fd = Field("Gold")
    z0 = TOP_Z + 0.0012
    fd.add(Cylinder(v3((0, 0, z0 - 0.003)), 0.1, 0.008, rr=0.002), 0.0)
    fd.add(Torus(v3((0, 0, z0 + 0.001)), 0.13, 0.006), 0.002)
    for i in range(12):
        a = ray_angle(i)
        d = v3((math.cos(a), math.sin(a), 0.0))
        side = v3((-math.sin(a), math.cos(a), 0.0))
        L = 0.46 if i % 2 == 0 else 0.3
        def ray(P, d=d, side=side, L=L):
            s = P[:, :2] @ d[:2].astype(F)
            t = P[:, :2] @ side[:2].astype(F)
            u = np.clip((s - F(0.14)) / F(L), 0, 1)
            w = F(0.034) * (F(1) - u) + F(0.002)
            return np.maximum(np.maximum(np.abs(t) - w, np.maximum(F(0.14) - s, s - F(0.14 + L))), np.abs(P[:, 2] - F(z0)) - F(0.003))
        fd.add(Func(ray, (-0.8, -0.8, z0 - 0.01), (0.8, 0.8, z0 + 0.01)), 0.002)
    for i in range(N_GLOW):
        c = glow_pos(i)
        a = ray_angle(2 * i if N_GLOW == 6 else i)
        fd.add(RoundBox(c + v3((0, 0, -0.004)), (0.04, 0.04, 0.008), 0.004, R=euler(0, 0, a + math.pi / 4)), 0.0)
    return fd


def glow_pos(i):
    a = ray_angle(i)
    return v3((math.cos(a) * RING_R, math.sin(a) * RING_R, KERB_TOP + 0.002))


def glowstones_field():
    """Twelve gold diamonds set in the kerb's top (domed facets: they glow)."""
    fd = Field("Glowstones")
    for i in range(N_GLOW):
        c = glow_pos(i)
        a = ray_angle(i)
        fd.add(RoundBox(c, (0.03, 0.03, 0.01), 0.006, R=euler(0, 0, a + math.pi / 4)), 0.0)
        fd.add(Ellipsoid(c + v3((0, 0, 0.004)), (0.024, 0.024, 0.01), R=euler(0, 0, a + math.pi / 4)), 0.004)
    return fd


# ---------------------------------------------------------------------------------------------- the column, the stele
def _flutes(c, R, n=20):
    def fn(P):
        a = np.arctan2(P[:, 1] - F(c[1]), P[:, 0] - F(c[0]))
        return F(0.008) * np.clip(np.cos(a * F(n)), 0, 1) ** 0.5
    return fn


def column_field():
    """Marble (label 0, weathered 7 low down, traces of red paint 5 in the flutes): a square step, two fluted drums
    standing on it, the upper one broken off in a jagged slant; the fallen capital in the grass beside it (the round
    echinus under its square abacus, chipped)."""
    fd = Field("Column")
    g = ground_height(COLUMN_C[0], COLUMN_C[1])
    fd.add(RoundBox(COLUMN_C + v3((0, 0, g + 0.02)), (0.24, 0.24, 0.06), 0.012, R=euler(0, 0, 0.3), disp=_chip, disp_amp=0.003), 0.0, 7)
    c = COLUMN_C
    fl = _flutes(c, COLUMN_R)
    z0 = g + 0.08
    h1, h2 = 0.3, 0.26
    def drum(P, za, zb, r0, r1, broken=False):
        r = np.sqrt((P[:, 0] - F(c[0])) ** 2 + (P[:, 1] - F(c[1])) ** 2)
        t = np.clip((P[:, 2] - F(za)) / F(zb - za), 0, 1)
        rad = F(r0) + (F(r1) - F(r0)) * t
        top = F(zb)
        if broken:
            top = F(zb) - F(0.09) * (P[:, 0] - F(c[0]) + F(0.16)) / F(0.32) + F(0.02) * NOISE(P * F(14))
        return np.maximum(r - rad + fl(P), np.maximum(F(za) - P[:, 2], P[:, 2] - top))
    fd.add(Func(lambda P: drum(P, z0, z0 + h1, COLUMN_R, COLUMN_R * 0.97), c + v3((-0.25, -0.25, z0 - 0.02)), c + v3((0.25, 0.25, z0 + h1 + 0.02)),
                disp=_chip, disp_amp=0.003), 0.004)
    fd.add(Func(lambda P: drum(P, z0 + h1 + 0.004, z0 + h1 + h2, COLUMN_R * 0.97, COLUMN_R * 0.95, True),
                c + v3((-0.25, -0.25, z0 + h1 - 0.02)), c + v3((0.25, 0.25, z0 + h1 + h2 + 0.06)), disp=_chip, disp_amp=0.004), 0.004)
    fd.paint(Func(lambda P: P[:, 2] - F(z0 + 0.12), c + v3((-0.3, -0.3, g - 0.1)), c + v3((0.3, 0.3, z0 + 0.2))), 7)
    # the fallen capital, tipped on its side in the grass
    gc = ground_height(CAPITAL_C[0], CAPITAL_C[1])
    R = euler(math.radians(78), 0, 0.9)
    cc = CAPITAL_C + v3((0, 0, gc + 0.13))
    fd.add(RoundBox(cc + R @ v3((0, 0, 0.07)), (0.21, 0.21, 0.04), 0.01, R=R, disp=_chip, disp_amp=0.004), 0.0)
    fd.add(Inter(Sphere(cc + R @ v3((0, 0, -0.1)), 0.2, disp=_chip, disp_amp=0.003),
                 Func(lambda P: np.abs(((P - cc.astype(F)) @ R.astype(F))[:, 2] + F(0.0)) - F(0.035), cc - 0.3, cc + 0.3), 0.01), 0.008)
    fd.add(RoundCone(cc + R @ v3((0, 0, -0.03)), cc + R @ v3((0, 0, -0.1)), 0.13, 0.13), 0.01)
    fd.sub(Sphere(cc + R @ v3((0.17, 0.1, 0.09)), 0.06), 0.01)                                  # a chipped corner
    return fd


def stele_frame():
    g = ground_height(STELE_C[0], STELE_C[1])
    side = norm(np.cross(v3((0, 0, 1)), STELE_FWD))
    return STELE_C + v3((0, 0, g)), STELE_FWD, side


def stele_field():
    """A marble slab on a plinth, a low pediment on top with acroteria; rows of carved letters across its face."""
    fd = Field("Stele")
    b, fwd, side = stele_frame()
    R = rot_from_axes(x_axis=side, y_axis=fwd, z_axis=(0, 0, 1))
    W = lambda x, y, z: b + side * x + fwd * y + v3((0, 0, z))
    fd.add(RoundBox(W(0, 0, 0.03), (0.2, 0.09, 0.07), 0.01, R=R, disp=_chip, disp_amp=0.003), 0.0, 7)
    fd.add(RoundBox(W(0, 0, 0.5), (0.155, 0.05, 0.42), 0.008, R=R, disp=_chip, disp_amp=0.003), 0.004)
    def pediment(P):
        q = (P - W(0, 0, 0.92).astype(F)) @ R.astype(F)
        tri = np.abs(q[:, 0]) * F(0.42) + q[:, 2] - F(0.07)
        return np.maximum(np.maximum(tri, F(-0.0) - q[:, 2]), np.abs(q[:, 1]) - F(0.055))
    fd.add(Func(pediment, W(0, 0, 0.92) - 0.25, W(0, 0, 0.92) + 0.25, disp=_chip, disp_amp=0.003), 0.006)
    fd.add(RoundBox(W(0, 0, 0.925), (0.175, 0.058, 0.014), 0.005, R=R), 0.004)
    for sx in (-1, 1):
        fd.add(Sphere(W(sx * 0.16, 0, 0.955), 0.024), 0.006)
    fd.add(Sphere(W(0, 0, 0.995), 0.026), 0.006)
    rs = np.random.RandomState(19)
    for row in range(9):                                                          # rows of carved letters
        z = 0.82 - row * 0.058
        x = -0.12
        while x < 0.12:
            w = rs.uniform(0.008, 0.016)
            kind = rs.randint(3)
            c = W(x + w, -0.052, z)
            if kind == 0:
                fd.sub(RoundBox(c, (0.003, 0.006, 0.016), 0.002, R=R), 0.0015)
            elif kind == 1:
                fd.sub(Torus(c, 0.01, 0.0028, R=rot_from_axes(z_axis=fwd)), 0.0015)
            else:
                fd.sub(RoundBox(c, (0.011, 0.006, 0.003), 0.002, R=R), 0.0015)
                fd.sub(RoundBox(c + v3((0, 0, 0.012)), (0.011, 0.006, 0.003), 0.002, R=R), 0.0015)
            x += 2 * w + 0.01 + (0.02 if rs.rand() < 0.15 else 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the scroll box
def capsa_field():
    """A round box of dark leather (label 9 in the siege material) bound with bronze bands (6), its lid lying beside it."""
    fd = Field("Capsa")
    g = ground_height(CAPSA_C[0], CAPSA_C[1])
    b = CAPSA_C + v3((0, 0, g - 0.01))
    fd.add(Cylinder(b + v3((0, 0, 0.09)), 0.075, 0.18, rr=0.008), 0.0, 9)
    fd.sub(Cylinder(b + v3((0, 0, 0.17)), 0.064, 0.1, rr=0.004), 0.004)
    for z in (0.03, 0.15):
        fd.add(Torus(b + v3((0, 0, z)), 0.076, 0.005), 0.002, 6)
    lid = b + v3((0.13, -0.05, 0.03))
    fd.add(Cylinder(lid, 0.08, 0.04, rr=0.008, R=euler(0.3, 0.2, 0)), 0.0, 9)
    fd.add(Torus(lid + v3((0, 0, 0.0)), 0.081, 0.005, R=euler(0.3, 0.2, 0)), 0.002, 6)
    return fd


def scrolls_field():
    """The scrolls standing in the box: papyrus rolls, their ends showing the spiral of the roll, a wooden knob on each
    rod."""
    fd = Field("Scrolls")
    g = ground_height(CAPSA_C[0], CAPSA_C[1])
    b = CAPSA_C + v3((0, 0, g - 0.01))
    for k, (dx, dy, h, tl) in enumerate(((-0.025, -0.02, 0.27, 0.12), (0.028, -0.012, 0.25, -0.1), (0.0, 0.03, 0.29, 0.05), (-0.03, 0.03, 0.23, -0.15))):
        ax = norm(v3((tl, tl * 0.5, 1.0)))
        c0 = b + v3((dx, dy, 0.04))
        top = c0 + ax * h
        fd.add(RoundCone(c0, top, 0.02, 0.02), 0.002)
        fd.sub(Torus(top, 0.011, 0.002, R=rot_from_axes(z_axis=ax)), 0.001)
        fd.add(RoundCone(top, top + ax * 0.03, 0.006, 0.006), 0.002, 9)
        fd.add(Sphere(top + ax * 0.034, 0.009), 0.002, 9)
    return fd


# ---------------------------------------------------------------------------------------------- scatter
def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < KERB_R + 0.08 + pad:
        return True
    if math.hypot(c[0] - COLUMN_C[0], c[1] - COLUMN_C[1]) < 0.36 + pad:
        return True
    if math.hypot(c[0] - CAPITAL_C[0], c[1] - CAPITAL_C[1]) < 0.26 + pad:
        return True
    if math.hypot(c[0] - STELE_C[0], c[1] - STELE_C[1]) < 0.24 + pad:
        return True
    if math.hypot(c[0] - CAPSA_C[0], c[1] - CAPSA_C[1]) < 0.22 + pad:
        return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(67)
    n = 0
    tries = 0
    while n < 12 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.9, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.024, 0.046), seed=860 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
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
    return [("Ground", ground_field(), 0.008), ("Marble", marble_field(), 0.0042), ("Gold", gold_field(), 0.0018),
            ("Glowstones", glowstones_field(), 0.0022), ("Column", column_field(), 0.0036), ("Stele", stele_field(), 0.0022),
            ("Capsa", capsa_field(), 0.0024), ("Scrolls", scrolls_field(), 0.0018), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Marble", "Column", "Capsa", "Scrolls")
LOW_TARGETS = {"Ground": 1400, "Marble": 4200, "Gold": 1400, "Glowstones": 300, "Column": 2200, "Stele": 1600, "Capsa": 500,
               "Scrolls": 500, "Pebbles": 340}
MAT_OVERRIDES = {"Marble": ("marble", {"name": "HQ_ForecourtMarble"}),
                 "Gold": ("gold", {"name": "HQ_SunGold"}),
                 "Column": ("marble", {"name": "HQ_ColumnMarble", "base": (0.9, 0.88, 0.83)}),
                 "Stele": ("marble", {"name": "HQ_SteleMarble", "base": (0.92, 0.9, 0.85)}),
                 "Capsa": ("siege", {"name": "HQ_Capsa", "wood": (0.5, 0.34, 0.2), "wood2": (0.36, 0.24, 0.13)}),
                 "Scrolls": ("siege", {"name": "HQ_Scrolls", "wood": (0.86, 0.78, 0.6), "wood2": (0.72, 0.62, 0.44)}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
GLOW = {"Glowstones": ((1.0, 0.8, 0.3), 1.0, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and KERB_R + 0.06 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.08))
