"""Bronze Archer base: a mud-brick watchtower on a grassy mound by the river. Battered walls of sun-dried brick with a
band of blue glazed bricks and yellow rosettes, a low parapet with stepped merlons and whitewashed coping, a ladder up
the back, a jar of spare arrows and a bundle of reeds on the platform, a bronze brazier burning on the mound, papyrus
and pebbles round it (distance fields) + grass, flowers and papyrus (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b

GROUND_R = 1.38
GROUND_TOP = 0.18
TC = v3((0.0, 0.03, 0.0))          # tower centre
HB, HT = 0.6, 0.55                 # half size at the foot and at the top (battered walls)
TOP_Z = 0.82                       # the platform floor = where the archer's feet stand
STAND = v3((0.0, 0.0, TOP_Z))
PAR_H = 0.13                       # parapet height above the floor
PAR_T = 0.1                        # parapet thickness
BAND = (0.6, 0.7)                  # the glazed band (z)
JAR_C = v3((-0.33, 0.33, TOP_Z))
REEDS_C = v3((0.35, 0.35, TOP_Z))
BRAZ_C = v3((0.86, -0.72, 0.0))
LADDER_X = -0.27


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.05 * max(0.0, 1 - (r / GROUND_R) ** 2)


BRAZ_TOP = v3((BRAZ_C[0], BRAZ_C[1], ground_height(BRAZ_C[0], BRAZ_C[1]) + 0.32))
FLAME_TOP = BRAZ_TOP + v3((0, 0, 0.02))


def half_at(z):
    t = min(1.0, max(0.0, (z - 0.1) / (TOP_Z - 0.1)))
    return HB + (HT - HB) * t


def tower_sd(P, grow=0.0):
    """Signed distance to the battered tower block (from the mound to the floor)."""
    t = np.clip((P[:, 2] - F(0.1)) / F(TOP_Z - 0.1), 0, 1)
    h = F(HB) + F(HT - HB) * t + F(grow)
    qx = np.abs(P[:, 0] - F(TC[0])) - h + F(0.05)
    qy = np.abs(P[:, 1] - F(TC[1])) - h + F(0.05)
    d2 = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - F(0.05)
    return np.maximum(d2, np.maximum(F(-0.1) - P[:, 2], P[:, 2] - F(TOP_Z)))


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
    return fd


DOOR_W, DOOR_Z = 0.1, (0.26, 0.54)      # half width, sill and lintel of the doorway in the front wall


def front_y(z):
    return TC[1] - half_at(z)


def pilaster_sd(P):
    """Shallow buttresses: one at every corner and two on every face (they frame the doorway on the front)."""
    t = np.clip((P[:, 2] - F(0.1)) / F(TOP_Z - 0.1), 0, 1)
    h = F(HB) + F(HT - HB) * t
    ax = np.abs(P[:, 0] - F(TC[0]))
    ay = np.abs(P[:, 1] - F(TC[1]))
    corner = np.maximum(h - F(0.1) - ax, h - F(0.1) - ay)
    py = np.maximum(np.abs(ax - F(0.25)) - F(0.05), ax - ay)
    px = np.maximum(np.abs(ay - F(0.25)) - F(0.05), ay - ax)
    region = np.minimum(corner, np.minimum(py, px))
    zr = np.maximum(F(0.25) - P[:, 2], P[:, 2] - F(TOP_Z - 0.06))
    return np.maximum(np.maximum(tower_sd(P, 0.03), region), zr)


def door_cut(P, grow=0.0, depth=0.06):
    """The doorway's opening: a box sunk `depth` into the battered front wall (grow widens it, for the rebate)."""
    t = np.clip((P[:, 2] - F(0.1)) / F(TOP_Z - 0.1), 0, 1)
    face = F(TC[1]) - (F(HB) + F(HT - HB) * t)
    zc, zh = (DOOR_Z[0] + DOOR_Z[1]) / 2, (DOOR_Z[1] - DOOR_Z[0]) / 2
    return np.maximum(np.maximum(np.abs(P[:, 0] - F(TC[0])) - F(DOOR_W + grow), np.abs(P[:, 2] - F(zc + grow / 2)) - F(zh + grow / 2)),
                      np.maximum(P[:, 1] - (face + F(depth)), (face - F(0.3)) - P[:, 1]))


def brick_field():
    """The tower: battered mud-brick walls with buttresses, a plinth course, a doorway with a whitewashed rebated frame,
    the glazed band with rosettes, the parapet and stepped merlons."""
    fd = Field("Brick")
    wob = lambda P: F(0.006) * NOISE(P * F(6)) + F(0.003) * NOISE(P * F(19))
    fd.add(Func(lambda P: tower_sd(P), (-0.8, -0.8, -0.15), (0.8, 0.8, TOP_Z + 0.02), disp=wob, disp_amp=0.01), 0.0)
    fd.add(Func(pilaster_sd, (-0.8, -0.8, 0.2), (0.8, 0.8, TOP_Z), disp=wob, disp_amp=0.01), 0.006)
    # plinth course round the foot
    fd.add(Func(lambda P: np.maximum(tower_sd(P, 0.05), np.abs(P[:, 2] - F(0.2)) - F(0.06)), (-0.8, -0.8, 0.0), (0.8, 0.8, 0.4), disp=wob, disp_amp=0.01), 0.012)
    # a string course just under the parapet
    fd.add(Func(lambda P: np.maximum(tower_sd(P, 0.045), np.abs(P[:, 2] - F(TOP_Z - 0.03)) - F(0.035)), (-0.8, -0.8, 0.5), (0.8, 0.8, TOP_Z + 0.1)), 0.01)
    # the doorway: a rebate, then the opening itself
    fd.sub(Func(lambda P: door_cut(P, 0.035, 0.022), (-0.3, -0.8, 0.2), (0.3, -0.3, 0.65)), 0.004)
    fd.sub(Func(lambda P: door_cut(P), (-0.2, -0.8, 0.2), (0.2, -0.3, 0.6)), 0.004)
    # parapet: a low wall round the edge of the floor
    def ring(P, h_top):
        hx = np.abs(P[:, 0] - F(TC[0]))
        hy = np.abs(P[:, 1] - F(TC[1]))
        outer = np.maximum(hx, hy) - F(HT + 0.01)
        inner = F(HT - PAR_T) - np.maximum(hx, hy)
        return np.maximum(np.maximum(outer, inner), np.maximum(F(TOP_Z - 0.05) - P[:, 2], P[:, 2] - F(h_top)))
    fd.add(Func(lambda P: ring(P, TOP_Z + PAR_H), (-0.8, -0.8, TOP_Z - 0.1), (0.8, 0.8, TOP_Z + 0.4), disp=wob, disp_amp=0.01), 0.012)
    # stepped merlons: at every corner, and in the middle of the sides and the back
    spots = [(sx * (HT - PAR_T / 2), sy * (HT - PAR_T / 2)) for sx in (-1, 1) for sy in (-1, 1)]
    spots += [(-(HT - PAR_T / 2), 0.0), ((HT - PAR_T / 2), 0.0), (0.0, HT - PAR_T / 2)]
    for (mx, my) in spots:
        c = TC + v3((mx, my, 0))
        fd.add(RoundBox(c + v3((0, 0, TOP_Z + PAR_H + 0.05)), (0.075, 0.075, 0.05), 0.012), 0.008)
        fd.add(RoundBox(c + v3((0, 0, TOP_Z + PAR_H + 0.13)), (0.05, 0.05, 0.04), 0.01), 0.008)
    # the glazed band (5) with rosettes (6) on all four faces; whitewash (7) on the coping and round the doorway
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(sum(BAND) / 2)) - F((BAND[1] - BAND[0]) / 2), tower_sd(P, 0.07)),
                  (-0.8, -0.8, BAND[0] - 0.05), (0.8, 0.8, BAND[1] + 0.05)), 5)
    zc = sum(BAND) / 2
    for side in range(4):
        for u in (-0.4, -0.11, 0.0, 0.11, 0.4):
            h = half_at(zc) + 0.012
            p = {0: v3((u, -h, zc)), 1: v3((h, u, zc)), 2: v3((-u, h, zc)), 3: v3((-h, -u, zc))}[side] + TC
            fd.paint(Sphere(p, 0.032), 6)
    fd.paint(Func(lambda P: F(TOP_Z + PAR_H - 0.012) - P[:, 2], (-0.8, -0.8, TOP_Z), (0.8, 0.8, TOP_Z + 0.5)), 7)
    fd.paint(Func(lambda P: door_cut(P, 0.06, 0.08), (-0.3, -0.8, 0.2), (0.3, -0.3, 0.7)), 7)
    return fd


def door_field(fd):
    """A plank door set back in the doorway, with two battens across it."""
    zc = (DOOR_Z[0] + DOOR_Z[1]) / 2
    zh = (DOOR_Z[1] - DOOR_Z[0]) / 2
    y = front_y(zc) + 0.05
    def grooves(P):
        m = (P[:, 0] - F(TC[0] + 0.02)) / F(0.04)
        dist = np.abs(m - np.round(m)) * F(0.04)
        return F(0.0025) * np.clip(1 - dist / F(0.004), 0, 1) + F(0.0015) * NOISE(P * np.array([60, 60, 8], F))
    fd.add(RoundBox(v3((TC[0], y, zc)), (DOOR_W - 0.002, 0.014, zh + 0.01), 0.004, disp=grooves, disp_amp=0.003), 0.0)
    for z in (zc - 0.08, zc + 0.08):
        fd.add(RoundBox(v3((TC[0], y - 0.016, z)), (DOOR_W - 0.012, 0.007, 0.018), 0.004), 0.002)
    return fd


DOOR_STUDS = [(x, z) for z in ((DOOR_Z[0] + DOOR_Z[1]) / 2 - 0.08, (DOOR_Z[0] + DOOR_Z[1]) / 2 + 0.08) for x in (-0.065, -0.022, 0.022, 0.065)]


def wood_field():
    """The ladder up the back wall, and the brazier's pole."""
    fd = Field("Wood")
    bark = lambda P: F(0.003) * NOISE(P * np.array([40, 40, 8], F))
    y_out, z0 = TC[1] + HB + 0.32, ground_height(0.0, TC[1] + HB + 0.32) - 0.02
    y_in, z1 = TC[1] + HT + 0.03, TOP_Z + 0.26
    for dx in (-0.11, 0.11):
        a, b = v3((LADDER_X + dx, y_out, z0)), v3((LADDER_X + dx * 0.9, y_in, z1))
        fd.add(RoundCone(a, b, 0.022, 0.02, disp=bark, disp_amp=0.004), 0.0)
    for k in range(1, 6):
        t = k / 6.2
        a = lerp(v3((LADDER_X - 0.11, y_out, z0)), v3((LADDER_X - 0.099, y_in, z1)), t)
        b = lerp(v3((LADDER_X + 0.11, y_out, z0)), v3((LADDER_X + 0.099, y_in, z1)), t)
        fd.add(RoundCone(a, b, 0.014, 0.014, disp=bark, disp_amp=0.003), 0.006)
    door_field(fd)
    return fd


def bronze_field():
    """A bronze brazier on three legs, its bowl rimmed with a twisted band."""
    fd = Field("BronzeBits")
    g = ground_height(BRAZ_C[0], BRAZ_C[1])
    bowl_c = BRAZ_TOP + v3((0, 0, -0.05))
    fd.add(Inter(Shell(Ellipsoid(bowl_c, (0.13, 0.13, 0.08)), 0.0, 0.014), Plane(bowl_c + v3((0, 0, 0.035)), (0, 0, 1)), 0.004), 0.0)
    fd.add(Torus(bowl_c + v3((0, 0, 0.032)), 0.12, 0.012), 0.006)
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.3
        d = v3((math.cos(a), math.sin(a), 0))
        top = bowl_c + d * 0.08 + v3((0, 0, -0.04))
        foot = BRAZ_C + d * 0.17 + v3((0, 0, g - 0.01))
        fd.add(Chain([top, lerp(top, foot, 0.5) + d * 0.025, foot], [0.012, 0.011, 0.014], k=0.006), 0.008)
        fd.add(Sphere(foot + v3((0, 0, 0.008)), 0.022), 0.008)
    # studs on the door's battens, and a ring to pull it by
    zc = (DOOR_Z[0] + DOOR_Z[1]) / 2
    y = front_y(zc) + 0.05 - 0.024
    for (x, z) in DOOR_STUDS:
        fd.add(Sphere(v3((TC[0] + x, y, z)), 0.009), 0.0)
    fd.add(Torus(v3((TC[0] + 0.05, y - 0.006, zc - 0.005)), 0.022, 0.0045, R=rot_from_axes(z_axis=(0, 1, 0))), 0.0)
    fd.add(Sphere(v3((TC[0] + 0.05, y + 0.002, zc + 0.017)), 0.008), 0.003)
    return fd


def coals_field():
    """Glowing coals heaped in the brazier's bowl."""
    fd = Field("Coals")
    bowl_c = BRAZ_TOP + v3((0, 0, -0.05))
    rs = np.random.RandomState(31)
    fd.add(Inter(Ellipsoid(bowl_c, (0.115, 0.115, 0.07)), Plane(bowl_c + v3((0, 0, 0.0)), (0, 0, 1)), 0.0), 0.0)
    for k in range(9):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.0, 0.08)
        p = bowl_c + v3((math.cos(a) * r, math.sin(a) * r, 0.012 + 0.01 * (1 - r / 0.08)))
        fd.add(Stone(p, rs.uniform(0.022, 0.034), seed=200 + k, squash=(1, 1, 0.7), noise=0.08), 0.006)
    return fd


def jar_field():
    """A storage jar holding spare arrows (label 5 = black painted bands)."""
    fd = Field("Jar")
    c = JAR_C + v3((0, 0, 0.16))
    fd.add(Ellipsoid(c, (0.11, 0.11, 0.15)), 0.0)
    fd.add(RoundCone(c + v3((0, 0, 0.1)), c + v3((0, 0, 0.2)), 0.06, 0.05), 0.04)
    fd.add(Torus(c + v3((0, 0, 0.2)), 0.052, 0.014), 0.008)
    fd.sub(Cylinder(c + v3((0, 0, 0.22)), 0.04, 0.12), 0.006)
    fd.add(Cylinder(JAR_C + v3((0, 0, 0.03)), 0.06, 0.06, rr=0.015), 0.03)
    for k, z in enumerate((0.03, 0.08)):
        fd.paint(Func(lambda P, z=z: np.abs(P[:, 2] - F(c[2] + z)) - F(0.012), c - 0.3, c + 0.3), 5)
    return fd


def spare_field():
    """Spare arrows standing in the jar: reed shafts (label 0) and red and white fletching (8)."""
    fd = Field("Spare")
    c = JAR_C + v3((0, 0, 0.36))
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.2
        d = norm(v3((math.cos(a) * 0.18, math.sin(a) * 0.18, 1.0)))
        base = c + v3((math.cos(a), math.sin(a), 0)) * 0.012 - d * 0.1
        top = base + d * (0.36 + 0.03 * (k % 2))
        fd.add(Chain([base, top], [0.0065, 0.0065]), 0.0)
        side = norm(np.cross(d, v3((0, 0, 1)) if abs(d[2]) < 0.99 else v3((1, 0, 0))))
        up = np.cross(side, d)
        for j in range(3):
            ang = j * 2 * math.pi / 3
            vd = side * math.cos(ang) + up * math.sin(ang)
            fd.add(Ellipsoid(top - d * 0.06 + vd * 0.012, (0.002, 0.014, 0.05), R=rot_from_axes(z_axis=d, y_axis=vd)), 0.002, 8)
        fd.add(Cylinder(top + d * 0.004, 0.008, 0.016, rr=0.003, R=rot_from_axes(z_axis=d)), 0.002)
    return fd


def reeds_field():
    """A tied bundle of reeds leaning in the corner of the platform (label 5 = the bindings)."""
    fd = Field("Reeds")
    base = REEDS_C + v3((0, 0, 0.02))
    d = norm(v3((0.22, 0.22, 1.0)))
    rs = np.random.RandomState(4)
    for k in range(9):
        o = v3((rs.uniform(-0.035, 0.035), rs.uniform(-0.035, 0.035), 0))
        dd = norm(d + rs.normal(0, 0.03, 3))
        fd.add(Chain([base + o, base + o + dd * rs.uniform(0.42, 0.5)], [0.012, 0.009], k=0.004), 0.004)
    for z in (0.12, 0.3):
        fd.add(Torus(base + d * z, 0.045, 0.01, R=rot_from_axes(z_axis=d)), 0.004, 5)
    return fd


def flame_field():
    fd = Field("Flame")
    c = FLAME_TOP + v3((0, 0, 0.04))
    fd.add(Ellipsoid(c, (0.085, 0.085, 0.09)), 0.0)
    fd.add(RoundCone(c, c + v3((0.01, 0.0, 0.26)), 0.075, 0.005), 0.05)
    for a in (0.0, 2.1, 4.2):
        d = v3((math.cos(a), math.sin(a), 0))
        fd.add(RoundCone(c + d * 0.045, c + d * 0.06 + v3((0, 0, 0.17)), 0.04, 0.003), 0.03)
    return fd


FLAME_PIVOT = FLAME_TOP + np.array((0, 0, 0.0))
FLAME_COLOR = (1.0, 0.5, 0.12)          # an orange brazier fire (the default yellow washed out to white in game)
FLAME_STRENGTH = 1.5


def _blocked(c, pad=0.0):
    if abs(c[0] - TC[0]) < HB + 0.12 + pad and abs(c[1] - TC[1]) < HB + 0.12 + pad:
        return True
    if abs(c[0] - LADDER_X) < 0.25 + pad and TC[1] + HB < c[1] < TC[1] + HB + 0.45 + pad:
        return True
    if math.hypot(c[0] - BRAZ_C[0], c[1] - BRAZ_C[1]) < 0.28 + pad:
        return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(13)
    n = 0
    tries = 0
    while n < 16 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.75, 1.28)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.026, 0.05), seed=100 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=17):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.7, GROUND_R - 0.08)
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
            L = rs.uniform(0.13, 0.24) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.042), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


PAPYRUS = [(-0.95, -0.62, 0.3), (1.02, 0.42, 1.4), (-0.9, 0.74, 2.2)]


def flower_geometry(seed=23):
    """A few flowers (kinds 0-2: stem, petals, centre) and papyrus clumps: tall stems crowned with a burst of thin rays
    (kind 3, the papyrus green swatch)."""
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.8, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.05) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.2 for s in spots):
            continue
        spots.append((c, rs.randint(0, 3)))
    for c, kind in spots:
        base = v3((c[0], c[1], ground_height(c[0], c[1]) - 0.01))
        h = rs.uniform(0.1, 0.15)
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
            pv += [top + tilt * 0.004, top + dirk * 0.035 * 0.55 + sidek * 0.035 * 0.42, top + dirk * 0.035, top + dirk * 0.035 * 0.55 - sidek * 0.035 * 0.42]
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
            h = rs.uniform(0.44, 0.66)
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
    return [("Ground", ground_field(), 0.008), ("Brick", brick_field(), 0.006), ("Wood", wood_field(), 0.003),
            ("BronzeBits", bronze_field(), 0.003), ("Coals", coals_field(), 0.003), ("Jar", jar_field(), 0.003), ("Spare", spare_field(), 0.0018),
            ("Reeds", reeds_field(), 0.003), ("Flame", flame_field(), 0.004), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Brick", "Jar", "Spare", "Reeds")
LOW_TARGETS = {"Ground": 1400, "Brick": 3400, "Wood": 520, "BronzeBits": 700, "Coals": 200, "Jar": 520, "Spare": 420, "Reeds": 420,
               "Pebbles": 420, "Flame": 160}
MAT_OVERRIDES = {"Brick": ("mudbrick", {"name": "HQ_Mudbrick"}),
                 "BronzeBits": ("bronze", {"name": "HQ_BaseBronze"}),
                 "Coals": ("coals", {"name": "HQ_Coals"}),
                 "Jar": ("terracotta", {"name": "HQ_Jar"}),
                 "Spare": ("arrows", {"name": "HQ_SpareArrows"}),
                 "Reeds": ("reed", {"name": "HQ_ReedBundle"})}
EXTRA_SWATCHES = [(0.56, 0.7, 0.24)]          # kind 3: papyrus heads


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not (abs(c.x - TC[0]) < HB + 0.05 and abs(c.y - TC[1]) < HB + 0.05))
