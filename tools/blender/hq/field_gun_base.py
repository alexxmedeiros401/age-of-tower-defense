"""Field Gun base: a gun pit in the railway yard. The round plinth is a floor of packed earth (trampled, dusty) inside a
parapet of sandbags laid in two staggered courses; part of the floor is cobbled, the cobbles sunk in the earth with gaps
where some are missing, and three old railway sleepers are bedded flush in it as a platform for the wheels and trail
(their iron spikes and tie plates still in them). Nothing on the floor stands proud of it: the gun turns over it. Four
gaps in the parapet hold the gunners' things: a heap of spent brass cases, an open box of fixed rounds standing nose up,
a range marker (a pole painted in red and white bands with a numbered board) and a red signal flag on a pole wedged
with a sandbag. Weeds grow along the parapet's foot and round the outside (distance fields + direct low-poly geometry
for the weeds and a few dandelions)."""
import math
import numpy as np
from sdf import (Field, Sphere, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Ellipsoid, v3, norm, rot_from_axes,
                 smax, NOISE, F, euler)
from caveman import Stone, Inter, Shell
import base as _b
import field_gun as _g
from crossbowman_base import _bloom

GROUND_R = 1.45
TOP_Z = 0.1                    # the pit's floor: where the gun and his feet rest
FLOOR_R = 1.19                 # the floor's edge (the parapet's inner foot)
STAND = v3((-_g.YAW_PIVOT[0], -_g.YAW_PIVOT[1], TOP_Z))
BANK_Z = 0.07                  # the ground outside the parapet
BAG = (0.17, 0.09, 0.052)     # a sandbag's half length, depth, height
BAG_R = (1.31, 1.3, 1.29)      # the courses' middle radii
GAPS = {"heap": math.radians(158.0), "box": math.radians(18.0), "marker": math.radians(62.0), "flag": math.radians(112.0)}
GAP_W = {"heap": 0.2, "box": 0.18, "marker": 0.0, "flag": 0.0}      # (half widths, radians: the pole props stand in the bags)
SLEEPERS = (-0.56, 0.0, 0.56)  # y of the sleepers (they lie along X)
SLP = (0.11, 0.05)             # their half width and half height


def _angd(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def in_gap(a, extra=0.0):
    return any(_angd(a, g) < GAP_W[k] + extra for k, g in GAPS.items() if GAP_W[k] > 0)


def ground_height(x, y):
    r = math.hypot(x, y)
    if r < FLOOR_R:
        return TOP_Z
    return BANK_Z + 0.02 * max(0.0, 1 - ((r - FLOOR_R) / (GROUND_R - FLOOR_R)))


def ground_field():
    """The ground under the pit's floor and round it (grass outside the parapet; label 5: trampled earth under it)."""
    fd = Field("Ground")
    RE = GROUND_R
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        top = F(BANK_Z) + F(0.02) * np.clip((F(GROUND_R) - r) / F(GROUND_R - FLOOR_R), 0, 1)     # (the setts lie on it)
        dx = r - F(RE)
        dz = np.maximum(P[:, 2] - top, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.04), 0), np.maximum(dz + F(0.04), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.04), dz + F(0.04)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.04)
    fd.add(Func(disc, (-RE - 0.05, -RE - 0.05, -0.2), (RE + 0.05, RE + 0.05, 0.2),
                disp=lambda P: F(0.004) * NOISE(P * F(9)) + F(0.002) * NOISE(P * F(30)), disp_amp=0.006), 0.0)
    fd.paint(Func(lambda P: np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(FLOOR_R + 0.02), (-RE, -RE, -0.2), (RE, RE, 0.2)), 5)
    return fd


def sleeper_box(y):
    hl = math.sqrt(max(0.0, (FLOOR_R - 0.06) ** 2 - (abs(y) + SLP[0]) ** 2))
    return v3((0.0, y, TOP_Z + 0.012 - SLP[1])), (hl, SLP[0], SLP[1])


def sleepers_field():
    """Three old railway sleepers (creosoted timber, grain along X: label 10), split and weathered, bedded flush in the
    floor; iron tie plates and spikes (6) where the rails were."""
    fd = Field("Sleepers")
    grain = lambda P: F(0.0025) * NOISE(P * np.array([4, 60, 60], F)) + F(0.001) * NOISE(P * F(90))
    for i, y in enumerate(SLEEPERS):
        c, h = sleeper_box(y)
        R = euler(0, 0, (-0.02, 0.015, -0.01)[i])
        fd.add(RoundBox(c, h, 0.012, R=R, disp=grain, disp_amp=0.003), 0.0, 10)
        fd.sub(RoundBox(c + v3((h[0] * 0.3, 0.02, SLP[1])), (h[0] * 0.35, 0.004, 0.012), 0.003, R=R), 0.002)     # a split
        for x in (-0.38, 0.38):
            if abs(x) > h[0] - 0.12:
                continue
            p = c + R @ v3((x, 0.0, SLP[1] + 0.004))
            fd.add(RoundBox(p, (0.06, 0.09, 0.006), 0.003, R=R), 0.002, 6)
            for sy in (-1, 1):
                fd.add(Cylinder(p + R @ v3((0.03 * sy, 0.065 * sy, 0.008)), 0.011, 0.012, rr=0.003), 0.002, 6)
    return fd


SETT = (0.105, 0.082)          # a granite sett's length (along X) and width: laid in courses along X, joints staggered
SETT_ROWS = 40


def _sett_cells(P):
    """Each point's sett: (row, column, distance to the sett's edge (>0 inside), per-sett random)."""
    v = P[:, 1] / F(SETT[1]) + F(SETT_ROWS / 2)
    row = np.floor(v)
    u = P[:, 0] / F(SETT[0]) + F(0.5) * (row % 2) + F(0.37) * np.sin(row * F(2.3))
    col = np.floor(u)
    du = (F(0.5) - np.abs(u - col - F(0.5))) * F(SETT[0])
    dv = (F(0.5) - np.abs(v - row - F(0.5))) * F(SETT[1])
    rnd = np.abs(np.sin(row * F(12.9898) + col * F(78.233)) * F(43758.5453)) % F(1.0)
    return row, col, np.minimum(du, dv), rnd


def floor_field():
    """The pit's floor: granite setts in staggered courses, each domed a little and a little proud or sunk on its own,
    gritty joints between them (label 7: some setts of a browner stone; 6: dark grit and earth where setts are missing,
    near the parapet)."""
    fd = Field("Floor")
    def fn(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        row, col, e, rnd = _sett_cells(P)
        dome = F(0.006) * np.clip(e / F(0.022), 0, 1) ** F(0.6) - F(0.006)
        lost = (rnd > F(0.93)) | ((r > F(FLOOR_R - 0.16)) & (rnd > F(0.72)))
        top = F(TOP_Z) + dome + (rnd - F(0.5)) * F(0.004) - np.where(lost, F(0.012), F(0.0))
        d = np.maximum(P[:, 2] - top, F(TOP_Z - 0.06) - P[:, 2])
        return np.maximum(d * F(0.7), r - F(FLOOR_R + 0.02))
    R = FLOOR_R + 0.04
    fd.add(Func(fn, (-R, -R, TOP_Z - 0.08), (R, R, TOP_Z + 0.02), disp=lambda P: F(0.0012) * NOISE(P * F(60)), disp_amp=0.0015), 0.0)
    def paint(P, which):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        row, col, e, rnd = _sett_cells(P)
        lost = (rnd > F(0.93)) | ((r > F(FLOOR_R - 0.16)) & (rnd > F(0.72)))
        if which == 6:
            return np.where(lost, F(-1.0), F(1.0))
        return np.where((rnd > F(0.55)) & (rnd < F(0.75)) & ~lost, F(-1.0), F(1.0))
    fd.paint(Func(lambda P: paint(P, 7), (-R, -R, TOP_Z - 0.08), (R, R, TOP_Z + 0.02)), 7)
    fd.paint(Func(lambda P: paint(P, 6), (-R, -R, TOP_Z - 0.08), (R, R, TOP_Z + 0.02)), 6)
    return fd


def bag_specs(seed=3):
    """(centre, yaw, half extents, seed) of every sandbag: two staggered courses round the pit, the gaps left open."""
    rs = np.random.RandomState(seed)
    out = []
    for course in range(3):
        rr = BAG_R[course]
        n = int(2 * math.pi * rr / (2 * BAG[0] + 0.012))
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * course) / n
            if in_gap(a, 0.02) or (course == 2 and (math.sin(a * 3.0 + 0.7) < -0.2)):
                continue                                                # (the third course only in stretches)
            z = BANK_Z + BAG[2] * 0.9 + course * (2 * BAG[2] * 0.82) + rs.uniform(-0.004, 0.006)
            c = v3((math.cos(a) * (rr + rs.uniform(-0.012, 0.012)), math.sin(a) * (rr + rs.uniform(-0.012, 0.012)), z))
            yaw = a + math.pi / 2 + rs.uniform(-0.08, 0.08)
            h = (BAG[0] * rs.uniform(0.92, 1.04), BAG[1] * rs.uniform(0.92, 1.05), BAG[2] * rs.uniform(0.9, 1.05))
            out.append((c, yaw, h, int(rs.randint(1 << 20))))
    return out


def sandbags_field():
    """The parapet: plump jute sandbags (0), each a little different, their tied ends pinched (twine, 6), a stencilled
    mark on a few (5)."""
    fd = Field("Sandbags")
    lumpy = lambda P: F(0.004) * NOISE(P * F(12)) + F(0.0015) * NOISE(P * F(40))
    for c, yaw, h, sd in bag_specs():
        R = euler(0.03 * math.sin(sd), 0.04 * math.cos(sd), yaw)
        fd.add(RoundBox(c, h, h[2] * 0.95, R=R, disp=lumpy, disp_amp=0.006), 0.012, 0)
        e = c + R @ v3((h[0] + 0.012, 0.0, 0.0))                       # the tied end
        fd.add(Ellipsoid(e, (0.022, 0.03, 0.022), R=R), 0.012, 0)
        fd.add(Torus(e - R @ v3((0.006, 0, 0)), 0.018, 0.0045, R=R @ rot_from_axes(z_axis=(1, 0, 0))), 0.002, 6)
        if sd % 5 == 0:
            fd.paint(Inter(Shell(Ellipsoid(c + v3((0, 0, h[2] * 0.4)), (0.06, 0.04, h[2] * 0.7), R=R), 0.0, 0.03),
                           Plane(c + v3((0, 0, h[2] * 0.5)), (0, 0, -1))), 5)
    return fd


def _gap_c(name, r=1.3):
    a = GAPS[name]
    return v3((math.cos(a) * r, math.sin(a) * r, 0.0)), a


def brass_field():
    """A heap of spent brass cases (6) in a gap of the parapet, dark inside their mouths (8): some standing, most lying
    tumbled against each other."""
    fd = Field("Brass")
    c0, a0 = _gap_c("heap", 1.31)
    rs = np.random.RandomState(11)
    t = v3((-math.sin(a0), math.cos(a0), 0.0))
    o = v3((math.cos(a0), math.sin(a0), 0.0))
    L, Rc = _g.CASE_L, _g.CASE_R
    def case(base, ax, k):
        ax = norm(ax)
        Rr = rot_from_axes(z_axis=ax)
        fd.add(Cylinder(base + ax * 0.006, _g.RIM_R, 0.012, rr=0.003, R=Rr), k, 6)
        fd.add(Cylinder(base + ax * (L * 0.5), Rc, L - 0.01, rr=0.004, R=Rr), 0.004, 6)
        fd.sub(Cylinder(base + ax * L, Rc - 0.007, 0.06, R=Rr), 0.003)
    lying = [(-0.12, -0.05, 0.3), (-0.02, -0.08, -0.4), (0.09, -0.04, 0.9), (0.17, 0.06, 2.4), (-0.12, 0.07, 1.7),
             (0.02, 0.05, 2.9), (-0.2, 0.0, 1.1), (0.22, -0.06, 0.2), (0.08, 0.1, 2.0)]
    for k, (u, v, yaw) in enumerate(lying):
        b = c0 + t * u + o * v + v3((0, 0, BANK_Z + Rc + 0.002))
        ax = v3((math.cos(yaw + a0), math.sin(yaw + a0), 0.0))
        case(b - ax * (L * 0.5), ax, 0.0)
    for k, (u, v) in enumerate(((-0.06, 0.0), (0.04, 0.02), (0.13, 0.0))):         # lying on top of the others
        b = c0 + t * u + o * v + v3((0, 0, BANK_Z + 3 * Rc - 0.004))
        ax = v3((math.cos(a0 + 1.2 * k + 0.4), math.sin(a0 + 1.2 * k + 0.4), 0.05))
        case(b - ax * (L * 0.5), ax, 0.0)
    for k, (u, v) in enumerate(((0.0, 0.12), (0.1, 0.14), (-0.11, 0.15), (0.2, 0.12), (-0.21, 0.12))):   # standing at the back
        b = c0 + t * u + o * v + v3((0, 0, BANK_Z - 0.004))
        case(b, v3((0.04 * ((k % 3) - 1), 0.03, 1.0)), 0.0)
    return fd


MARKER_H = 0.95
FLAG_H = 1.35


def marker_foot():
    c, a = _gap_c("marker", 1.3)
    return c + v3((0, 0, BANK_Z + 0.12))


def flag_foot():
    c, a = _gap_c("flag", 1.31)
    return c + v3((0, 0, BANK_Z + 0.12))


def ammo_field():
    """The open box of rounds standing nose up: wood (9) with iron corners (8), the rounds' brass cases (6), grey shells
    (5) with copper bands (11) and brass fuses."""
    fd = Field("Ammo")
    # the box of rounds, standing nose up
    c, a = _gap_c("box", 1.3)
    R = euler(0, 0, a + math.pi / 2 + 0.1)
    hx, hy, h = 0.2, 0.135, 0.15
    z0 = BANK_Z - 0.004
    def box(P):
        q = (P - c.astype(F) - F(np.array([0, 0, z0]))) @ R.astype(F)
        outer = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx), np.abs(q[:, 1]) - F(hy)), np.maximum(-q[:, 2], q[:, 2] - F(h)))
        inner = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx - 0.016), np.abs(q[:, 1]) - F(hy - 0.016)), F(0.03) - q[:, 2])
        return np.maximum(outer, -inner)
    cz = c + v3((0, 0, z0))
    fd.add(Func(box, cz - 0.3, cz + 0.3, disp=lambda P: F(0.0008) * NOISE(P * np.array([30, 30, 6], F)), disp_amp=0.0012), 0.0, 9)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(RoundBox(cz + R @ v3((sx * hx, sy * hy, h - 0.02)), (0.008, 0.008, 0.02), 0.003, R=R), 0.002, 8)
    for i in range(4):
        for j in range(2):
            if i == 3 and j == 1:
                continue                                          # (one gone)
            b = cz + R @ v3((-0.15 + 0.1 * i, -0.06 + 0.12 * j, 0.03))
            _g.round_into(fd, b, v3((0.02 * (i - 1), 0.015 * (j - 0.5), 1.0)), k=0.002)
    return fd


def marker_field():
    """The range marker: a pole painted in red (12) and white (13) bands, a white board with a red number."""
    fd = Field("Marker")
    f0 = marker_foot()
    f1 = f0 + v3((0, 0, MARKER_H))
    nb = 7
    for k in range(nb):
        a0 = f0 + (f1 - f0) * (k / nb)
        a1 = f0 + (f1 - f0) * ((k + 1) / nb)
        fd.add(RoundCone(a0, a1, 0.017, 0.017), 0.002 if k else 0.0, 12 if k % 2 == 0 else 13)
    fd.add(RoundCone(f1, f1 + v3((0, 0, 0.03)), 0.017, 0.006), 0.003, 12)
    ma = GAPS["marker"]
    side = v3((-math.sin(ma), math.cos(ma), 0.0))
    out = v3((math.cos(ma), math.sin(ma), 0.0))
    bc = f1 + v3((0, 0, -0.1)) - out * 0.022
    Rb = rot_from_axes(z_axis=-out, x_axis=side)
    fd.add(RoundBox(bc, (0.13, 0.09, 0.009), 0.004, R=Rb), 0.003, 13)
    # its number ("4"), painted red on the board's inner face
    s = 0.055
    for p0, p1 in (((-0.3, 0.9), (-0.3, -0.05)), ((-0.3, -0.05), (0.45, -0.05)), ((0.2, 0.75), (0.2, -0.8))):
        q0 = bc + side * (p0[0] * s) + v3((0, 0, p0[1] * s)) - out * 0.009
        q1 = bc + side * (p1[0] * s) + v3((0, 0, p1[1] * s)) - out * 0.009
        fd.paint(RoundCone(q0, q1, 0.011, 0.011), 12)
    return fd


def pole_field():
    """The flagpole: wood (9), an iron knob and spike (8), the flag's iron ties."""
    fd = Field("Pole")
    g0 = flag_foot()
    g1 = g0 + v3((0, 0, FLAG_H))
    fd.add(RoundCone(g0 - v3((0, 0, 0.1)), g1, 0.015, 0.012), 0.0, 9)
    fd.add(Sphere(g1 + v3((0, 0, 0.01)), 0.017), 0.003, 8)
    fd.add(RoundCone(g1 + v3((0, 0, 0.02)), g1 + v3((0, 0, 0.07)), 0.008, 0.0015), 0.002, 8)
    for z in (0.93, 0.73):
        fd.add(Torus(g0 + v3((0, 0, FLAG_H * z)), 0.016, 0.003), 0.001, 8)
    return fd


FLAG_L, FLAG_HT = 0.42, 0.28


def _flag_coords(P):
    f1 = flag_foot() + v3((0, 0, FLAG_H - 0.04))
    a = GAPS["flag"] + 0.45
    w = v3((math.cos(a), math.sin(a), 0.0))
    n = norm(np.cross(w, v3((0, 0, 1))))
    q = P - f1.astype(F)
    return q @ w.astype(F) - F(0.015), -q[:, 2], q @ n.astype(F)


def flag_field():
    """The red signal flag (linen, 0), its hem darker (5), rippling, the fly end sagging a little."""
    fd = Field("Flag")
    L, H = FLAG_L, FLAG_HT
    def fn(P):
        u, v, s = _flag_coords(P)
        un = np.clip(u / F(L), 0, 1)
        vv = v - F(0.03) * un * un
        s0 = F(0.032) * np.sin(u * F(16.0) - F(0.4)) * un + F(0.006) * np.sin(v * F(23.0) + u * F(9.0))
        d_sheet = (np.abs(s - s0) - F(0.005)) * F(0.8)
        d_box = np.maximum(np.maximum(-u, u - F(L)), np.maximum(-vv, vv - F(H)))
        return np.maximum(d_sheet, d_box)
    c = flag_foot() + v3((0, 0, FLAG_H - 0.04))
    lo, hi = c + v3((-0.5, -0.5, -0.32)), c + v3((0.5, 0.5, 0.06))
    fd.add(Func(fn, lo, hi), 0.0, 0)
    def hem(P):
        u, v, s = _flag_coords(P)
        un = np.clip(u / F(L), 0, 1)
        vv = v - F(0.03) * un * un
        return F(0.016) - np.minimum(np.minimum(u, F(L) - u), np.minimum(vv, F(H) - vv))
    fd.paint(Func(lambda P: -hem(P), lo, hi), 5)
    return fd


def wedge_field():
    """A sandbag laid against the flagpole's foot (the same jute as the parapet)."""
    fd = Field("Wedge")
    g0 = flag_foot()
    a = GAPS["flag"]
    o = v3((math.cos(a), math.sin(a), 0.0))
    for k, (d, yaw) in enumerate(((0.08, 0.3), (-0.09, -0.4))):
        c = g0 + o * d + v3((0, 0, -0.06))
        R = euler(0.1 * (k - 0.5), 0, a + yaw)
        fd.add(RoundBox(c, (0.12, 0.07, 0.045), 0.042, R=R, disp=lambda P: F(0.004) * NOISE(P * F(12)), disp_amp=0.005), 0.012)
    return fd


def _avoid():
    return [(g, max(GAP_W[k], 0.06)) for k, g in GAPS.items()]


def grass_geometry(seed=47):
    """Weeds: tufts along the parapet's inner foot (never out on the floor the gun sweeps) and round the outside."""
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        inner = rs.rand() < 0.45
        r = rs.uniform(FLOOR_R - 0.05, FLOOR_R + 0.01) if inner else rs.uniform(1.4, GROUND_R - 0.02)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.12 for t in tufts) or any(_angd(a, g) < w + 0.05 for g, w in _avoid()):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(6, 10)
        big = 0.5 + 0.35 * rs.rand()
        inner = math.hypot(c[0], c[1]) < FLOOR_R + 0.05
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.03)
            root = c + off
            root[2] = (TOP_Z if inner else ground_height(root[0], root[1])) - 0.008
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.25, 0.55) + v3((0, 0, 1)))
            L = rs.uniform(0.08, 0.14) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.026, 0.036), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=53):
    """A few dandelions (swatch 1: yellow) among the weeds outside the parapet."""
    rs = np.random.RandomState(seed)
    out = []
    n = 0
    tries = 0
    while n < 6 and tries < 2000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        if any(_angd(a, g) < w + 0.1 for g, w in _avoid()):
            continue
        r = rs.uniform(1.41, GROUND_R - 0.02)
        root = v3((math.cos(a) * r, math.sin(a) * r, 0))
        root[2] = ground_height(root[0], root[1]) - 0.005
        hgt = rs.uniform(0.07, 0.11)
        d = norm(v3((math.cos(a) * 0.3, math.sin(a) * 0.3, 1.0)))
        sv, sf, _ = _b.blade_mesh(root, d, hgt, 0.01, v3((math.cos(a), math.sin(a), 0)) * 0.1, segs=2)
        out.append((sv, sf, 0, 4))
        _bloom(out, root + d * hgt, norm(v3((math.cos(a) * 0.4, math.sin(a) * 0.4, 1.0))), 0.026, 1)
        n += 1
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Sleepers", sleepers_field(), 0.004), ("Floor", floor_field(), 0.0035),
            ("Sandbags", sandbags_field(), 0.004), ("Brass", brass_field(), 0.0024), ("Ammo", ammo_field(), 0.0024),
            ("Marker", marker_field(), 0.0024), ("Pole", pole_field(), 0.0024), ("Flag", flag_field(), 0.0025),
            ("Wedge", wedge_field(), 0.004)]


REGION_PARTS = ("Ground", "Floor", "Sleepers", "Sandbags", "Brass", "Ammo", "Marker", "Pole", "Flag")
LOW_TARGETS = {"Ground": 1000, "Sleepers": 1000, "Floor": 2600, "Sandbags": 4200, "Brass": 900, "Ammo": 1500, "Marker": 500,
               "Pole": 260, "Flag": 400, "Wedge": 300}
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_PitGround", "dirt_label": 5}),
                 "Sleepers": ("siege", {"name": "HQ_Sleepers", "wood": (0.34, 0.24, 0.16), "wood2": (0.2, 0.13, 0.08), "metal": "iron"}),
                 "Floor": ("flagstone", {"name": "HQ_Setts", "base": (0.44, 0.43, 0.42), "alt": (0.52, 0.45, 0.38)}),
                 "Sandbags": ("sacking", {"name": "HQ_Sandbags"}),
                 "Wedge": ("sacking", {"name": "HQ_Sandbags"}),
                 "Brass": ("fieldgun", {"name": "HQ_PitBrass"}),
                 "Ammo": ("fieldgun", {"name": "HQ_PitProps", "wood": (0.62, 0.48, 0.3)}),
                 "Marker": ("fieldgun", {"name": "HQ_PitProps", "wood": (0.62, 0.48, 0.3)}),
                 "Pole": ("fieldgun", {"name": "HQ_PitProps", "wood": (0.62, 0.48, 0.3)}),
                 "Flag": ("linen", {"name": "HQ_SignalFlag", "base": (0.78, 0.09, 0.06), "border": (0.5, 0.05, 0.04),
                                    "stripe": (0.5, 0.05, 0.04)})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and r > 1.4 and abs(c.z - ground_height(c.x, c.y)) < 0.03
