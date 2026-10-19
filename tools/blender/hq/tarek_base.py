"""Tarek's smithy: a round floor of worn dark flagstones ringed with fieldstones, soot-black round the forge; at his right
hand, a little in front of him, a bronze anvil on an oak stump bound with bronze, a red-hot bar lying on its face and a
pair of tongs leaning on the stump; behind him at his left a round clay forge with a bed of charcoal glowing through the
cracks, a crucible of molten bronze sitting in it and its fire (a flickering flame) fanned by two pot bellows through
clay pipes; at his left in front a stack of copper oxhide ingots; grass, flowers and pebbles (distance fields + direct
low-poly geometry).

The anvil's face is where he strikes in Forge Fury (anim_tarek.py turns him to face it; game.gd turns his yaw to it
and throws the sparks from ANVIL_FACE)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
from ugo import bez3
import base as _b

GROUND_R = 1.3
GROUND_TOP = 0.14
TOP_Z = 0.26                       # the floor's top = where his feet stand
STAND = v3((0.0, 0.0, TOP_Z))
OUTER_R = 0.92                     # the floor's edge (the fieldstone curb sits on it)


def dirz(deg):
    """Horizontal direction at `deg` counterclockwise from his front (-Y), seen from above."""
    a = math.radians(deg)
    return v3((math.sin(a), -math.cos(a), 0.0))


ANVIL_DEG = -45.0                                   # front-right of him
ANVIL_R = 0.72                                      # far enough for a full swing with his 0.4 hammer
ANVIL = dirz(ANVIL_DEG) * ANVIL_R                   # the stump's centre (floor plane)
STUMP_R = 0.15
STUMP_H = 0.34
ANVIL_TOP = STUMP_H + 0.27                          # the anvil's face above the floor
ANVIL_U = dirz(ANVIL_DEG + 90.0)                    # along the anvil, toward its horn (his left as he faces it)
ANVIL_V = dirz(ANVIL_DEG)                           # across it, away from him
ANVIL_FACE = ANVIL + v3((0, 0, TOP_Z + ANVIL_TOP))  # the middle of the face (base space)

FORGE = dirz(146.0) * 0.72                          # behind him at his left
FORGE_R = 0.24
FORGE_H = 0.25                                      # the clay wall's rim above the floor
COAL_Z = TOP_Z + 0.17                               # the charcoal bed's surface
BELLOWS = [dirz(170.0) * 1.1, dirz(124.0) * 1.08]  # two pot bellows behind the forge, on the ground
INGOTS = dirz(58.0) * 0.6                           # in front at his left
RACK = dirz(-150.0) * 0.8                           # the tool rack, behind him at his right
RACK_U = dirz(-150.0 + 90.0)                        # along its crossbar
RACK_W = 0.24                                       # half its width (post to post)
RACK_H = 0.92                                       # its posts above the floor
BASKET = dirz(100.0) * 0.93                         # a basket of charcoal by the forge, at his left


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.04 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 1.3) + F(0.02) * np.sin(a * 11 + 0.4) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.04) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    # soot and trampled earth round the forge and the bellows (label 5 = dark ground)
    fd.paint(Func(lambda P: np.sqrt((P[:, 0] - F(FORGE[0])) ** 2 + (P[:, 1] - F(FORGE[1])) ** 2) - F(0.5) + F(0.06) * NOISE(P * F(6)),
                  (-1.6, -1.6, -0.3), (1.6, 1.6, 0.4)), 5)
    return fd


# ======================================================================================= the flagstone floor
def _flag_seeds(n=21, seed=5):
    rs = np.random.RandomState(seed)
    pts = [v3((0.0, 0.0, 0.0))]                     # a big flag right under his feet
    tries = 0
    while len(pts) < n and tries < 20000:
        tries += 1
        r = OUTER_R * math.sqrt(rs.uniform(0.05, 1.0))
        a = rs.uniform(0, 2 * math.pi)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0.0))
        if all(np.linalg.norm(p[:2] - q[:2]) > 0.3 for q in pts):
            pts.append(p)
    return np.array(pts)[:, :2].astype(F)


SEEDS = _flag_seeds()
_rs = np.random.RandomState(17)
FLAG_DZ = _rs.uniform(-0.006, 0.004, len(SEEDS)).astype(F)
FLAG_TILT = _rs.uniform(-0.012, 0.012, (len(SEEDS), 2)).astype(F)
FLAG_ALT = (_rs.uniform(0, 1, len(SEEDS)) < 0.4)


def _voronoi(P):
    """Nearest seed index and the distance to that flag's edge (to the nearest bisector). Evaluated in batches: the
    pairwise arrays are (points x seeds), which for a whole meshing chunk would take gigabytes."""
    n = len(P)
    K = np.empty(n, np.int64)
    E = np.empty(n, F)
    B = 200000
    for a in range(0, n, B):
        xy = P[a:a + B, :2]
        d2 = ((xy[:, None, :] - SEEDS[None, :, :]) ** 2).sum(2)
        k = np.argmin(d2, axis=1)
        s1 = SEEDS[k]
        dk = d2[np.arange(len(k)), k]
        sep = np.sqrt(((SEEDS[None, :, :] - s1[:, None, :]) ** 2).sum(2))
        with np.errstate(divide="ignore", invalid="ignore"):
            e = (d2 - dk[:, None]) / (F(2) * sep)
        e[np.arange(len(k)), k] = F(1e3)
        K[a:a + B] = k
        E[a:a + B] = e.min(1)
    return K, E


def floor_field():
    """Flagstones (label 0; a lighter warm shade on some, 7), each laid a little proud or sunk and tilted, the joints
    between them filled with dark grit; round the edge a curb of fieldstones; soot near the forge (5) and hammer scale
    round the anvil (6)."""
    fd = Field("Floor")
    hz = (TOP_Z - GROUND_TOP + 0.06) / 2
    gap = F(0.008)
    rr = F(0.012)

    def flags(P):
        k, e = _voronoi(P)
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        d_xy = np.maximum(gap - e, r - F(OUTER_R - 0.035))
        s = SEEDS[k]
        t = F(TOP_Z) + FLAG_DZ[k] + FLAG_TILT[k, 0] * (P[:, 0] - s[:, 0]) + FLAG_TILT[k, 1] * (P[:, 1] - s[:, 1])
        d_z = np.abs(P[:, 2] - (t - F(hz))) - F(hz)
        q = np.stack([d_xy + rr, d_z + rr], 1)
        return np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - rr
    R = OUTER_R + 0.02
    chip = lambda P: F(0.003) * NOISE(P * F(9)) + F(0.0016) * NOISE(P * F(33))
    fd.add(Func(flags, (-R, -R, GROUND_TOP - 0.08), (R, R, TOP_Z + 0.03), disp=chip, disp_amp=0.006), 0.0)
    # a bed of grit under the flags (fills the joints a little below the tops)
    fd.add(Cylinder(v3((0, 0, (GROUND_TOP - 0.06 + TOP_Z - 0.022) / 2)), OUTER_R - 0.03, TOP_Z - 0.022 - GROUND_TOP + 0.06, rr=0.01), 0.0)
    # the fieldstone curb
    n = 26
    for i in range(n):
        a = 2 * math.pi * i / n + 0.07
        rad = 0.07 + 0.012 * math.sin(i * 2.7)
        c = v3((math.cos(a) * (OUTER_R + 0.005), math.sin(a) * (OUTER_R + 0.005), TOP_Z - 0.045))
        fd.add(Stone(c, rad, seed=300 + i, squash=(1.15, 1.0, 0.85), noise=0.05), 0.012)
    def alt(P):
        k, _ = _voronoi(P)
        return np.where(FLAG_ALT[k], F(-1.0), F(1.0))
    fd.paint(Func(alt, (-R, -R, GROUND_TOP), (R, R, TOP_Z + 0.05)), 7)
    fd.paint(Func(lambda P: np.sqrt((P[:, 0] - F(FORGE[0])) ** 2 + (P[:, 1] - F(FORGE[1])) ** 2) - F(0.42) + F(0.07) * NOISE(P * F(5)),
                  (-1.2, -1.2, -0.2), (1.2, 1.2, 0.6)), 5)
    fd.paint(Func(lambda P: np.sqrt((P[:, 0] - F(ANVIL[0])) ** 2 + (P[:, 1] - F(ANVIL[1])) ** 2) - F(0.3) + F(0.05) * NOISE(P * F(7)),
                  (-1.2, -1.2, -0.2), (1.2, 1.2, 0.6)), 6)
    return fd


# ======================================================================================= the anvil and its stump
def anvil_frame():
    """Origin on the stump's top, u along the anvil to its horn, v across (away from him), w up."""
    o = ANVIL + v3((0, 0, TOP_Z + STUMP_H))
    return o, ANVIL_U, ANVIL_V, v3((0, 0, 1))


def anvil_field():
    """A bronze anvil (label 0): splayed feet, a waist, a heavy body with a flat polished face, a square heel with a hardy
    hole and a horn tapering to a blunt point."""
    fd = Field("Anvil")
    o, U, Vv, W = anvil_frame()
    R = np.stack([U, Vv, W], axis=1)
    L = lambda u, v, w: o + U * u + Vv * v + W * w
    fd.add(RoundBox(L(0, 0, 0.032), (0.112, 0.088, 0.032), 0.012, R=R), 0.0)                     # the foot block
    for s in (-1, 1):                                                                                # arches between the feet
        fd.sub(Ellipsoid(L(0, s * 0.095, 0.0), (0.06, 0.03, 0.045), R=R), 0.01)
        fd.sub(Ellipsoid(L(s * 0.118, 0, 0.0), (0.03, 0.055, 0.045), R=R), 0.01)
    fd.add(RoundBox(L(0.0, 0, 0.115), (0.068, 0.046, 0.06), 0.02, R=R), 0.035)                      # the waist
    fd.add(RoundBox(L(-0.02, 0, 0.215), (0.165, 0.062, 0.052), 0.01, R=R), 0.03)                    # the body; face at w=0.267
    fd.add(RoundCone(L(0.13, 0, 0.212), L(0.37, 0, 0.204), 0.048, 0.007), 0.02)                      # the horn, below the face
    fd.sub(RoundBox(L(-0.142, 0, 0.27), (0.012, 0.012, 0.04), 0.002, R=R), 0.002)                    # the hardy hole
    fd.sub(Cylinder(L(-0.105, 0.0, 0.27), 0.007, 0.08, R=R), 0.002)                                  # the pritchel hole
    return fd


def stump_field():
    """An oak stump (label 11: grain upright) bound with two bronze bands (6), the anvil seated on it."""
    fd = Field("Stump")
    b = ANVIL + v3((0, 0, TOP_Z - 0.03))
    bark = lambda P: F(0.005) * NOISE(P * np.array([30, 30, 3], F)) + F(0.002) * NOISE(P * F(40))
    fd.add(Cylinder(b + v3((0, 0, (STUMP_H + 0.03) / 2)), STUMP_R, STUMP_H + 0.03, rr=0.02, disp=bark, disp_amp=0.007), 0.0, 11)
    for a in range(5):                                                                              # root flare
        d = dirz(a * 72 + 20)
        fd.add(RoundCone(b + d * 0.1 + v3((0, 0, 0.1)), b + d * 0.21 + v3((0, 0, 0.01)), 0.045, 0.02), 0.04, 11)
    for z in (0.08, STUMP_H - 0.06):
        fd.add(Torus(b + v3((0, 0, z + 0.03)), STUMP_R + 0.004, 0.011), 0.004, 6)
    fd.sub(Ellipsoid(ANVIL + v3((0, 0, TOP_Z + STUMP_H + 0.01)), (0.11, 0.11, 0.012)), 0.01)        # the seat
    return fd


def work_field():
    """The red-hot bar lying on the anvil's face (its own glowing mesh)."""
    fd = Field("Work")
    o, U, Vv, W = anvil_frame()
    c = o + U * 0.02 + W * 0.278
    R = np.stack([U, Vv, W], axis=1) @ euler(0, 0, 0.12)
    fd.add(RoundBox(c, (0.085, 0.014, 0.011), 0.007, R=R), 0.0)
    fd.add(RoundCone(c + (R @ v3((0.085, 0, 0))), c + (R @ v3((0.12, 0.004, -0.004))), 0.011, 0.004), 0.008)
    return fd


def tools_field():
    """Bronze tongs leaning on the stump (6 = bronze; their grips wrapped in leather, 9)."""
    fd = Field("Tools")
    side = dirz(ANVIL_DEG + 40.0)
    foot = ANVIL + side * 0.2 + v3((0, 0, TOP_Z + 0.004))
    top = ANVIL + side * (STUMP_R + 0.012) + v3((0, 0, TOP_Z + STUMP_H - 0.02))
    ax = norm(top - foot)
    across = norm(np.cross(ax, v3((0, 0, 1))))
    piv = lerp(foot, top, 0.72)
    for s in (-1, 1):
        a0 = foot + across * s * 0.03
        fd.add(RoundCone(a0, piv, 0.0075, 0.007), 0.002, 6)
        fd.add(RoundCone(foot + across * s * 0.03 + ax * 0.01, foot + across * s * 0.03 + ax * 0.12, 0.0095, 0.009), 0.002, 9)
        j0 = piv + ax * 0.004
        j1 = piv + ax * 0.09 + across * s * 0.012
        fd.add(RoundCone(j0, j1, 0.008, 0.006), 0.003, 6)
    fd.add(Cylinder(piv, 0.011, 0.02, R=rot_from_axes(z_axis=norm(np.cross(ax, across)))), 0.002, 6)
    return fd


# ======================================================================================= the forge, crucible, bellows
def forge_field():
    """A round clay hearth (label 0) with a thick rolled rim, blackened with soot above (5); the clay pipes from the
    bellows entering its back low down, and the bellows' round clay pots (0)."""
    fd = Field("Forge")
    b = FORGE + v3((0, 0, TOP_Z - 0.02))
    fd.add(Cylinder(b + v3((0, 0, (FORGE_H + 0.02) / 2)), FORGE_R, FORGE_H + 0.02, rr=0.04,
                    disp=lambda P: F(0.004) * NOISE(P * F(8)) + F(0.002) * NOISE(P * F(30)), disp_amp=0.006), 0.0)
    fd.add(Torus(b + v3((0, 0, FORGE_H + 0.01)), FORGE_R - 0.03, 0.04), 0.03)
    fd.sub(Cylinder(b + v3((0, 0, FORGE_H + 0.02)), FORGE_R - 0.075, 0.2, rr=0.03), 0.03)              # the hollow for the coals
    # a mouth at the front (toward him) where the glow shows
    m = norm(v3((-FORGE[0], -FORGE[1], 0)))
    fd.sub(Ellipsoid(b + m * (FORGE_R - 0.02) + v3((0, 0, FORGE_H * 0.62)), (0.09, 0.09, 0.07), R=rot_from_axes(z_axis=(0, 0, 1), y_axis=m)), 0.02)
    fd.paint(Func(lambda P: (b[2] + FORGE_H * 0.55) - P[:, 2] + F(0.03) * NOISE(P * F(9)), b - 0.5, b + 0.6), 5)
    # the tuyeres: clay pipes from each bellows, in low at the back
    for bp in BELLOWS:
        d = norm(v3((FORGE[0] - bp[0], FORGE[1] - bp[1], 0)))
        a = bp + d * 0.1 + v3((0, 0, ground_height(bp[0], bp[1]) + 0.1))
        e = FORGE - d * (FORGE_R - 0.03) + v3((0, 0, TOP_Z + 0.09))
        fd.add(RoundCone(a, e, 0.026, 0.03), 0.01)
        fd.add(Torus(e - d * 0.015, 0.032, 0.008, R=rot_from_axes(z_axis=d)), 0.008)
    for bp in BELLOWS:
        c = bp + v3((0, 0, ground_height(bp[0], bp[1]) + 0.075))
        fd.add(Ellipsoid(c, (0.115, 0.115, 0.085)), 0.0)
        fd.add(Cylinder(c + v3((0, 0, 0.075)), 0.09, 0.03, rr=0.01), 0.02)
    return fd


def coals_field():
    """The charcoal bed: lumps heaped in the hearth (baked: black with glowing cracks)."""
    fd = Field("Coals")
    rs = np.random.RandomState(61)
    for i in range(30):
        a = rs.uniform(0, 2 * math.pi)
        r = (FORGE_R - 0.09) * math.sqrt(rs.uniform(0, 1))
        c = FORGE + v3((math.cos(a) * r, math.sin(a) * r, COAL_Z - 0.008 + rs.uniform(-0.01, 0.012) - r * 0.08))
        fd.add(Stone(c, rs.uniform(0.026, 0.038), seed=700 + i, squash=(1.0, 1.0, 0.75), noise=0.08), 0.004)
    return fd


def embers_field():
    """The glow under the charcoal (its own glowing mesh): shows through the gaps between the lumps and in the mouth."""
    fd = Field("Embers")
    fd.add(Cylinder(FORGE + v3((0, 0, COAL_Z - 0.03)), FORGE_R - 0.08, 0.04, rr=0.018,
                    disp=lambda P: F(0.006) * NOISE(P * F(14)), disp_amp=0.008), 0.0)
    return fd


CRUCIBLE = FORGE + dirz(200.0) * 0.06 + v3((0, 0, COAL_Z + 0.02))


def crucible_field():
    """A small clay crucible (label 0) with a pouring lip, its outside burnt dark (5)."""
    fd = Field("Crucible")
    c = CRUCIBLE
    fd.add(RoundCone(c + v3((0, 0, -0.04)), c + v3((0, 0, 0.04)), 0.04, 0.055), 0.0)
    fd.sub(Cylinder(c + v3((0, 0, 0.05)), 0.042, 0.06, rr=0.01), 0.008)
    d = norm(v3((-FORGE[0], -FORGE[1], 0)))
    fd.add(Ellipsoid(c + d * 0.05 + v3((0, 0, 0.04)), (0.02, 0.02, 0.008), R=rot_from_axes(z_axis=(0, 0, 1), y_axis=d)), 0.008)
    fd.paint(Func(lambda P: P[:, 2] - F(c[2] + 0.02), c - 0.2, c + 0.2), 5)
    return fd


def melt_field():
    """The molten bronze in the crucible (its own glowing mesh)."""
    fd = Field("Melt")
    fd.add(Cylinder(CRUCIBLE + v3((0, 0, 0.026)), 0.043, 0.012, rr=0.005), 0.0)
    return fd


def bellows_field():
    """The pot bellows' slack leather skins tied round the pots' necks (9 = leather, 8 = cord), each worked by a stick
    standing up from its middle (11 = wood, grain upright). (The clay pots are in the Forge part.)"""
    fd = Field("Bellows")
    for i, bp in enumerate(BELLOWS):
        g = ground_height(bp[0], bp[1])
        c = bp + v3((0, 0, g + 0.075))
        skin = c + v3((0, 0, 0.1 + 0.012 * (i % 2)))
        fd.add(Ellipsoid(skin, (0.105, 0.105, 0.035), disp=lambda P: F(0.004) * NOISE(P * F(16)), disp_amp=0.005), 0.0, 9)
        fd.add(Torus(c + v3((0, 0, 0.085)), 0.094, 0.007), 0.003, 8)
        top = skin + v3((0.02 * (1 - 2 * i), 0.01, 0.34))
        fd.add(RoundCone(skin + v3((0, 0, 0.02)), top, 0.012, 0.01), 0.006, 11)
    return fd


# ======================================================================================= copper oxhide ingots
def _oxhide(c, ang, tilt=(0.0, 0.0), L=0.15, W=0.1, T=0.016):
    """One oxhide ingot: a thick slab with concave sides and its four corners drawn out like the legs of a hide."""
    R = euler(tilt[0], tilt[1], ang)
    u, v, w = R[:, 0], R[:, 1], R[:, 2]
    def fn(P, c=c, u=u, v=v, w=w):
        Q = P - c.astype(F)
        x = Q @ u.astype(F)
        y = Q @ v.astype(F)
        z = Q @ w.astype(F)
        # concave sides: the half-widths shrink toward the middle of each side
        hx = F(L) - F(0.022) * np.clip(F(1) - (y / F(W)) ** 2, 0, 1)
        hy = F(W) - F(0.018) * np.clip(F(1) - (x / F(L)) ** 2, 0, 1)
        dx = np.abs(x) - hx
        dy = np.abs(y) - hy
        dz = np.abs(z) - F(T)
        q = np.stack([dx, dy, dz], 1)
        rr = F(0.006)
        q2 = q + rr
        return np.sqrt((np.maximum(q2, 0) ** 2).sum(1)) + np.minimum(q2.max(1), 0) - rr
    e = max(L, W) + 0.03
    return Func(fn, c - e, c + e, disp=lambda P: F(0.0025) * NOISE(P * F(30)), disp_amp=0.003)


def ingots_field():
    """A stack of copper oxhide ingots (label 0) laid crosswise, one more lying beside it."""
    fd = Field("Ingots")
    g = TOP_Z
    rs = np.random.RandomState(83)
    base_ang = math.atan2(INGOTS[1], INGOTS[0])
    for i in range(5):
        c = INGOTS + v3((rs.uniform(-0.008, 0.008), rs.uniform(-0.008, 0.008), g + 0.017 + i * 0.034))
        fd.add(_oxhide(c, base_ang + (math.pi / 2 if i % 2 else 0.0) + rs.uniform(-0.08, 0.08), (rs.uniform(-0.02, 0.02), rs.uniform(-0.02, 0.02))), 0.0)
    d = dirz(58.0 - 75.0)
    c = INGOTS + d * 0.24 + v3((0, 0, g + 0.017))
    fd.add(_oxhide(c, math.atan2(d[1], d[0]) + 0.4, (0.03, -0.04)), 0.0)
    return fd


def rack_field():
    """A tool rack of adzed poles (11 = grain upright, 0 = along the bar), its crossbar lashed on with rope (8); hanging
    from its pegs a pair of long tongs and a spare hammer (6 = bronze, 9 = leather grips)."""
    fd = Field("Rack")
    grain = lambda P: F(0.002) * NOISE(P * np.array([40, 40, 6], F))
    U = RACK_U
    out = norm(v3((RACK[0], RACK[1], 0)))
    for sd in (-1, 1):
        b = RACK + U * (sd * RACK_W) + v3((0, 0, TOP_Z - 0.03))
        fd.add(RoundCone(b, b + v3((0, 0, RACK_H + 0.03)), 0.034, 0.03, disp=grain, disp_amp=0.003), 0.0, 11)
        fd.add(Sphere(b + v3((0, 0, RACK_H + 0.03)), 0.031), 0.012, 11)
        for j in range(3):
            fd.add(Torus(b + v3((0, 0, RACK_H - 0.12 + 0.016 * j)), 0.036, 0.007), 0.003, 8)
    bz = TOP_Z + RACK_H - 0.1
    a = RACK - U * (RACK_W + 0.06) + v3((0, 0, bz)) - out * 0.0
    e = RACK + U * (RACK_W + 0.06) + v3((0, 0, bz))
    fd.add(RoundCone(a, e, 0.026, 0.024, disp=lambda P: F(0.002) * NOISE(P * F(30)), disp_amp=0.003), 0.004, 0)
    pegs = [-0.13, 0.0, 0.13]
    for o in pegs:
        p0 = RACK + U * o + v3((0, 0, bz)) - out * 0.02
        fd.add(RoundCone(p0, p0 - out * 0.07 + v3((0, 0, 0.02)), 0.008, 0.007), 0.003, 0)
    # tongs hanging from the left peg (their rivet on it, the long arms down)
    t0 = RACK + U * pegs[0] + v3((0, 0, bz - 0.01)) - out * 0.07
    for sd in (-1, 1):
        top = t0 + U * (sd * 0.012)
        fd.add(RoundCone(top, top + v3((0, 0, -0.5)) + U * (sd * 0.03), 0.0075, 0.007), 0.002, 6)
        fd.add(RoundCone(top + v3((0, 0, -0.36)) + U * (sd * 0.022), top + v3((0, 0, -0.5)) + U * (sd * 0.03), 0.0098, 0.0092), 0.002, 9)
        fd.add(RoundCone(top, top + v3((0, 0, 0.07)) - U * (sd * 0.012), 0.0085, 0.006), 0.003, 6)
    fd.add(Cylinder(t0, 0.012, 0.03, R=rot_from_axes(z_axis=out)), 0.002, 6)
    # a spare hammer hanging by its head from the right-hand pegs
    hc = RACK + U * 0.13 + v3((0, 0, bz + 0.035)) - out * 0.06
    R = np.stack([out, U, v3((0, 0, 1))], axis=1)
    fd.add(RoundBox(hc, (0.032, 0.085, 0.03), 0.008, R=R), 0.0, 6)
    fd.add(RoundCone(hc, hc + v3((0, 0, -0.34)), 0.014, 0.012, disp=grain, disp_amp=0.002), 0.004, 11)
    fd.add(RoundCone(hc + v3((0, 0, -0.22)), hc + v3((0, 0, -0.33)), 0.0165, 0.0165), 0.003, 9)
    return fd


def basket_field():
    """A wicker basket (label 0) heaped with charcoal (the Charcoal part)."""
    fd = Field("Basket")
    g = ground_height(BASKET[0], BASKET[1])
    c = BASKET + v3((0, 0, g + 0.075))
    weave = lambda P: F(0.003) * np.sin(np.arctan2(P[:, 1] - F(c[1]), P[:, 0] - F(c[0])) * F(40)) * np.sin(P[:, 2] * F(160)) + F(0.001) * NOISE(P * F(60))
    fd.add(Inter(Shell(Cylinder(c, 0.11, 0.15, rr=0.03), 0.0, 0.012), Plane(c + v3((0, 0, 0.06)), (0, 0, 1)), 0.004), 0.0)
    fd.add(Cylinder(c + v3((0, 0, -0.062)), 0.1, 0.02, rr=0.008), 0.004)
    fd.add(Torus(c + v3((0, 0, 0.06)), 0.104, 0.013, disp=weave, disp_amp=0.004), 0.004)
    return fd


def charcoal_field():
    """The heap of charcoal in the basket: dull black lumps."""
    fd = Field("Charcoal")
    g = ground_height(BASKET[0], BASKET[1])
    c = BASKET + v3((0, 0, g + 0.11))
    rs = np.random.RandomState(91)
    for i in range(16):
        a = rs.uniform(0, 2 * math.pi)
        r = 0.08 * math.sqrt(rs.uniform(0, 1))
        p = c + v3((math.cos(a) * r, math.sin(a) * r, 0.03 * (1 - (r / 0.08) ** 2) + rs.uniform(-0.01, 0.01)))
        fd.add(Stone(p, rs.uniform(0.022, 0.032), seed=800 + i, squash=(1.0, 0.9, 0.8), noise=0.08), 0.004)
    return fd


# ======================================================================================= dressing
def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < OUTER_R + 0.07 + pad:
        return True
    if math.hypot(c[0] - BASKET[0], c[1] - BASKET[1]) < 0.15 + pad:
        return True
    for bp in BELLOWS:
        if math.hypot(c[0] - bp[0], c[1] - bp[1]) < 0.16 + pad:
            return True
    if math.hypot(c[0] - FORGE[0], c[1] - FORGE[1]) < FORGE_R + 0.06 + pad:
        return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(29)
    n = 0
    tries = 0
    while n < 14 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(OUTER_R + 0.07, GROUND_R - 0.05)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.0):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.022, 0.04), seed=520 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=57):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 22 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(OUTER_R + 0.08, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, -0.02):
            continue
        if math.hypot(c[0] - FORGE[0], c[1] - FORGE[1]) < 0.55:     # scorched round the forge
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


def flower_geometry(seed=59):
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
        if math.hypot(c[0] - FORGE[0], c[1] - FORGE[1]) < 0.6:
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
    return out


# ======================================================================================= the flame
FLAME_TOP = FORGE + v3((0, 0, COAL_Z - 0.01))


def flame_field():
    fd = Field("Flame")
    c = FLAME_TOP + v3((0.0, 0.0, 0.05))
    fd.add(Ellipsoid(c, (0.1, 0.1, 0.075)), 0.0)
    fd.add(RoundCone(c, c + v3((0.01, 0.0, 0.24)), 0.08, 0.005), 0.05)
    for a in (0.3, 2.4, 4.5):
        d = v3((math.cos(a), math.sin(a), 0))
        fd.add(RoundCone(c + d * 0.055, c + d * 0.07 + v3((0, 0, 0.15)), 0.042, 0.003), 0.03)
    return fd


def fields():
    return [("Ground", ground_field(), 0.008), ("Floor", floor_field(), 0.0052), ("Anvil", anvil_field(), 0.0024),
            ("Stump", stump_field(), 0.003), ("Work", work_field(), 0.002), ("Tools", tools_field(), 0.0018),
            ("Forge", forge_field(), 0.0034), ("Coals", coals_field(), 0.0026), ("Embers", embers_field(), 0.004),
            ("Crucible", crucible_field(), 0.002), ("Melt", melt_field(), 0.002), ("Bellows", bellows_field(), 0.003),
            ("Ingots", ingots_field(), 0.0022), ("Rack", rack_field(), 0.0024), ("Basket", basket_field(), 0.0022),
            ("Charcoal", charcoal_field(), 0.0024), ("Pebbles", pebbles_field(), 0.004), ("Flame", flame_field(), 0.004)]


REGION_PARTS = ("Ground", "Floor", "Stump", "Tools", "Forge", "Crucible", "Bellows", "Rack")
LOW_TARGETS = {"Ground": 1300, "Floor": 4200, "Anvil": 900, "Stump": 700, "Work": 80, "Tools": 260, "Forge": 1300,
               "Coals": 1100, "Embers": 200, "Crucible": 240, "Melt": 40, "Bellows": 900, "Ingots": 900, "Rack": 900,
               "Basket": 500, "Charcoal": 500, "Pebbles": 300,
               "Flame": 160}
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_SmithyGround", "dirt_label": 5}),
                 "Floor": ("flagstone", {"name": "HQ_Flagstone"}),
                 "Anvil": ("bronze", {"name": "HQ_Anvil", "base": (0.46, 0.29, 0.14), "hi": (0.98, 0.8, 0.52),
                                      "dark": (0.16, 0.09, 0.05), "patina": (0.26, 0.42, 0.36)}),
                 "Stump": ("siege", {"name": "HQ_Stump", "wood": (0.5, 0.33, 0.2), "wood2": (0.36, 0.22, 0.12)}),
                 "Tools": ("siege", {"name": "HQ_Tongs"}),
                 "Forge": ("terracotta", {"name": "HQ_ForgeClay", "base": (0.66, 0.4, 0.26), "paint": (0.1, 0.08, 0.07)}),
                 "Coals": ("coals", {"name": "HQ_Coals"}),
                 "Crucible": ("terracotta", {"name": "HQ_Crucible", "base": (0.7, 0.46, 0.3), "paint": (0.12, 0.09, 0.08)}),
                 "Bellows": ("siege", {"name": "HQ_Bellows", "wood": (0.66, 0.4, 0.25), "wood2": (0.56, 0.32, 0.2)}),
                 "Ingots": ("bronze", {"name": "HQ_Copper", "base": (0.62, 0.3, 0.17), "hi": (0.96, 0.62, 0.44),
                                       "dark": (0.28, 0.11, 0.06), "patina": (0.24, 0.52, 0.42)}),
                 "Rack": ("siege", {"name": "HQ_Rack", "wood": (0.56, 0.37, 0.22), "wood2": (0.42, 0.26, 0.14)}),
                 "Basket": ("basket", {}),
                 "Charcoal": ("charcoal", {"name": "HQ_Charcoal"}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
GLOW = {"Work": ((1.0, 0.42, 0.08), 1.1, 0.5), "Embers": ((1.0, 0.36, 0.06), 1.0, 0.5),
        "Melt": ((1.0, 0.72, 0.24), 1.2, 0.55)}
FLAME_PIVOT = FLAME_TOP + np.array((0, 0, 0.0))
FLAME_COLOR = (1.0, 0.5, 0.12)
FLAME_STRENGTH = 1.5


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and OUTER_R + 0.03 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.08) and math.hypot(c.x - FORGE[0], c.y - FORGE[1]) > 0.5)
