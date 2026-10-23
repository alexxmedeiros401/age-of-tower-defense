"""Missile Launcher base: a launch pad on the airfield. The round plinth is a pad of poured concrete (slabs with sawn
expansion joints, a few of them a shade darker, stained and worn) with painted markings: a yellow ring near its edge with
azimuth ticks every thirty degrees and the bearings 0, 9, 18 and 27 at the cardinal points. Nothing on the pad stands proud
of it: the launcher turns over it. Round it, on the grass: a curved wall of HESCO baskets behind (wire-mesh cages lined
with tan geotextile, filled with earth), low sandbag courses in front and at the sides, and in the gaps the crew's things:
an olive generator on skids with its exhaust, panel and fuel cap, its black cable snaking along the wall's foot to a
junction box at the pad's edge; a stack of two spare-missile crates; a field radio antenna on a tripod. Weeds and a few
dandelions in the grass."""
import math
import numpy as np
from sdf import (Field, Sphere, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Ellipsoid, Chain, v3, norm, rot_from_axes,
                 smax, NOISE, F, euler)
from caveman import Stone, Inter, Shell
import base as _b
import missile as _m
from crossbowman_base import _bloom

GROUND_R = 1.45
TOP_Z = 0.1                    # the pad's top: where the launcher and his feet rest
FLOOR_R = 1.15                 # the pad's edge
STAND = v3((-_m.YAW_PIVOT[0], -_m.YAW_PIVOT[1], TOP_Z))
BANK_Z = 0.07                  # the ground round it
SLAB = 0.58                    # the slabs' size (the joints' spacing)
RING_R, RING_W = 1.05, 0.03    # the painted ring (its middle radius, its half width)
BAG = (0.17, 0.09, 0.05)       # a sandbag's half length, depth, height
BAG_R = (1.31, 1.3)
HESCO_R = 1.3                  # the baskets' middle radius
HESCO = (0.17, 0.12, 0.17)     # a basket's half width (along the wall), depth, height
HESCO_A = (math.radians(42.0), math.radians(134.0))      # the wall's ends (behind the pad: +Y)
GAPS = {"gen": math.radians(160.0), "crates": math.radians(8.0), "antenna": math.radians(28.0)}
GAP_W = {"gen": 0.24, "crates": 0.17, "antenna": 0.0}
KIT_L = dict(OLIVE=0, GREY=5, STEEL=7, BLACK=8, RED=12, WHITE=13)


def _angd(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def in_gap(a, extra=0.0):
    return any(_angd(a, g) < GAP_W[k] + extra for k, g in GAPS.items() if GAP_W[k] > 0)


def in_hesco(a, extra=0.0):
    return HESCO_A[0] - extra <= (a % (2 * math.pi)) <= HESCO_A[1] + extra


def ground_height(x, y):
    r = math.hypot(x, y)
    if r < FLOOR_R:
        return TOP_Z
    return BANK_Z + 0.02 * max(0.0, 1 - ((r - FLOOR_R) / (GROUND_R - FLOOR_R)))


def ground_field():
    """The ground round the pad (grass; label 5: trampled earth at the wall's foot and under the pad)."""
    fd = Field("Ground")
    RE = GROUND_R
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        top = F(BANK_Z) + F(0.02) * np.clip((F(GROUND_R) - r) / F(GROUND_R - FLOOR_R), 0, 1)
        dx = r - F(RE)
        dz = np.maximum(P[:, 2] - top, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.04), 0), np.maximum(dz + F(0.04), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.04), dz + F(0.04)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.04)
    fd.add(Func(disc, (-RE - 0.05, -RE - 0.05, -0.2), (RE + 0.05, RE + 0.05, 0.2),
                disp=lambda P: F(0.004) * NOISE(P * F(9)) + F(0.002) * NOISE(P * F(30)), disp_amp=0.006), 0.0)
    fd.paint(Func(lambda P: np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(FLOOR_R + 0.1), (-RE, -RE, -0.2), (RE, RE, 0.2)), 5)
    return fd


def _slab_cells(P):
    u = P[:, 0] / F(SLAB) + F(0.5)
    v = P[:, 1] / F(SLAB) + F(0.5)
    iu, iv = np.floor(u), np.floor(v)
    e = np.minimum(np.minimum(u - iu, F(1) - (u - iu)), np.minimum(v - iv, F(1) - (v - iv))) * F(SLAB)
    rnd = np.abs(np.sin(iu * F(12.9898) + iv * F(78.233)) * F(43758.5453)) % F(1.0)
    return e, rnd


def pad_field():
    """The pad: poured concrete slabs (label 0; some a shade darker and browner, 7), sawn joints between them, a rounded
    edge; oil stains (5); painted markings in yellow (8): a ring with ticks every thirty degrees and the bearings."""
    fd = Field("Pad")
    R = FLOOR_R + 0.03
    def fn(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        e, rnd = _slab_cells(P)
        top = F(TOP_Z) + (rnd - F(0.5)) * F(0.002) - F(0.004) * np.clip(F(1.0) - e / F(0.006), 0, 1)
        d = np.maximum(P[:, 2] - top, F(TOP_Z - 0.09) - P[:, 2])
        q0, q1 = r - F(FLOOR_R) + F(0.025), d + F(0.025)
        return np.minimum(np.maximum(q0, q1), F(0)) + np.sqrt(np.maximum(q0, 0) ** 2 + np.maximum(q1, 0) ** 2) - F(0.025)
    lo, hi = (-R, -R, TOP_Z - 0.12), (R, R, TOP_Z + 0.03)
    fd.add(Func(fn, lo, hi, disp=lambda P: F(0.0008) * NOISE(P * F(50)), disp_amp=0.001), 0.0)
    def alt(P):
        e, rnd = _slab_cells(P)
        return np.where((rnd > F(0.62)) & (rnd < F(0.8)), F(-1.0), F(1.0))
    fd.paint(Func(alt, lo, hi), 7)
    def stains(P):
        return F(0.55) - NOISE(P * np.array([2.6, 2.6, 2.6], F)) - F(0.35) * NOISE(P * F(9.0))
    fd.paint(Func(stains, lo, hi), 5)
    # the painted ring, its ticks and the bearings
    def ring(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.abs(r - F(RING_R)) - F(RING_W), np.abs(P[:, 2] - F(TOP_Z)) - F(0.02))
    fd.paint(Func(ring, lo, hi), 8)
    for k in range(12):
        a = 2 * math.pi * k / 12
        d = v3((math.cos(a), math.sin(a), 0.0))
        L = 0.12 if k % 3 == 0 else 0.07
        fd.paint(RoundCone(d * (RING_R - RING_W - L) + v3((0, 0, TOP_Z)), d * (RING_R - RING_W) + v3((0, 0, TOP_Z)), 0.012, 0.012), 8)
    for k, txt in enumerate(("0", "9", "18", "27")):
        a = math.pi / 2 - k * math.pi / 2                 # 0 at the back (+Y), clockwise seen from above
        d = v3((math.cos(a), math.sin(a), 0.0))
        side = v3((math.sin(a), -math.cos(a), 0.0))
        o = d * (RING_R - RING_W - 0.22) + v3((0, 0, TOP_Z))
        _m.stencil(fd, txt, o, side, d, 0.085, 8, depth=0.02, weight=0.12)
    return fd


def hesco_specs():
    """(centre, yaw) of each HESCO basket along the wall behind the pad."""
    n = 5
    out = []
    for k in range(n):
        a = HESCO_A[0] + (HESCO_A[1] - HESCO_A[0]) * (k + 0.5) / n
        out.append((v3((math.cos(a) * HESCO_R, math.sin(a) * HESCO_R, BANK_Z + HESCO[2] - 0.004)), a + math.pi / 2))
    return out


def hesco_field():
    """HESCO baskets: tan geotextile (0) bulging a little between the welded wire mesh (label 5: dark wire), the mesh's
    vertical posts at the corners and its coil hinges."""
    fd = Field("Hesco")
    hw, hd, hh = HESCO
    bulge = lambda P: F(0.004) * NOISE(P * F(6)) + F(0.0015) * NOISE(P * F(25))
    for c, yaw in hesco_specs():
        R = euler(0, 0, yaw)
        fd.add(RoundBox(c, (hw - 0.004, hd, hh), 0.016, R=R, disp=bulge, disp_amp=0.005), 0.006, 0)
        # the wire mesh: a grid of wires painted on its faces (long faces: along it and up; ends: across and up)
        def mesh_sd(P, c=c, R=R):
            q = (P - c.astype(F)) @ R.astype(F)
            cell = F(0.056)
            gu = np.abs(((q[:, 0] + F(10.0)) % cell) - cell / 2)
            gv = np.abs(((q[:, 1] + F(10.0)) % cell) - cell / 2)
            gz = np.abs(((q[:, 2] + F(10.0)) % cell) - cell / 2)
            near_long = np.abs(np.abs(q[:, 1]) - F(hd)) < F(0.02)
            g = np.where(near_long, np.minimum(gu, gz), np.minimum(gv, gz))
            box = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hw), np.abs(q[:, 1]) - F(hd)), np.abs(q[:, 2]) - F(hh))
            return np.maximum(g - F(0.0032), np.abs(box) - F(0.012))
        lo, hi = c - v3((0.3, 0.3, 0.3)), c + v3((0.3, 0.3, 0.3))
        fd.paint(Func(mesh_sd, lo, hi), 5)
        for su in (-1, 1):
            for sv in (-1, 1):
                p = c + R @ v3((su * (hw - 0.004), sv * (hd + 0.002), 0.0))
                fd.add(Cylinder(p, 0.006, 2 * hh, rr=0.002), 0.002, 5)
    return fd


def fill_field():
    """The earth filling each basket, heaped a little above its rim."""
    fd = Field("Fill")
    hw, hd, hh = HESCO
    for c, yaw in hesco_specs():
        R = euler(0, 0, yaw)
        fd.add(Ellipsoid(c + v3((0, 0, hh - 0.02)), (hw - 0.01, hd - 0.012, 0.045), R=R,
                         disp=lambda P: F(0.006) * NOISE(P * F(14)), disp_amp=0.006), 0.0)
    return fd


def bag_specs(seed=5):
    rs = np.random.RandomState(seed)
    out = []
    for course in range(2):
        rr = BAG_R[course]
        n = int(2 * math.pi * rr / (2 * BAG[0] + 0.012))
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * course) / n
            if in_gap(a, 0.02) or in_hesco(a, 0.12) or _angd(a, GAPS["antenna"]) < 0.1:
                continue
            z = BANK_Z + BAG[2] * 0.9 + course * (2 * BAG[2] * 0.82) + rs.uniform(-0.004, 0.006)
            c = v3((math.cos(a) * (rr + rs.uniform(-0.012, 0.012)), math.sin(a) * (rr + rs.uniform(-0.012, 0.012)), z))
            yaw = a + math.pi / 2 + rs.uniform(-0.08, 0.08)
            h = (BAG[0] * rs.uniform(0.92, 1.04), BAG[1] * rs.uniform(0.92, 1.05), BAG[2] * rs.uniform(0.9, 1.05))
            out.append((c, yaw, h, int(rs.randint(1 << 20))))
    return out


def sandbags_field():
    """Low sandbag courses: jute (0), each a little different, their tied ends (twine, 6), a stencilled mark on a few (5)."""
    fd = Field("Sandbags")
    lumpy = lambda P: F(0.004) * NOISE(P * F(12)) + F(0.0015) * NOISE(P * F(40))
    for c, yaw, h, sd in bag_specs():
        R = euler(0.03 * math.sin(sd), 0.04 * math.cos(sd), yaw)
        fd.add(RoundBox(c, h, h[2] * 0.95, R=R, disp=lumpy, disp_amp=0.006), 0.012, 0)
        e = c + R @ v3((h[0] + 0.012, 0.0, 0.0))
        fd.add(Ellipsoid(e, (0.022, 0.03, 0.022), R=R), 0.012, 0)
        fd.add(Torus(e - R @ v3((0.006, 0, 0)), 0.018, 0.0045, R=R @ rot_from_axes(z_axis=(1, 0, 0))), 0.002, 6)
        if sd % 5 == 0:
            fd.paint(Inter(Shell(Ellipsoid(c + v3((0, 0, h[2] * 0.4)), (0.06, 0.04, h[2] * 0.7), R=R), 0.0, 0.03),
                           Plane(c + v3((0, 0, h[2] * 0.5)), (0, 0, -1))), 5)
    return fd


def _gap_frame(name, r):
    a = GAPS[name]
    o = v3((math.cos(a), math.sin(a), 0.0))
    t = v3((-math.sin(a), math.cos(a), 0.0))
    return o * r, o, t, a


GEN_HALF = (0.12, 0.22, 0.13)        # the generator's half depth (radial), length (along the wall), height


def generator_field():
    """An olive generator set (0) on black skids (8): louvred sides, a black control panel with a white gauge (13), a red
    switch (12) and a grey socket (5), a grey exhaust pipe and muffler on top (5), a fuel cap, lifting eyes, a white
    stencil."""
    fd = Field("Generator")
    c0, o, t, a = _gap_frame("gen", 1.29)
    R = np.stack([o, t, v3((0, 0, 1))], axis=1)
    hx, hy, hz = GEN_HALF
    c = c0 + v3((0, 0, BANK_Z + 0.03 + hz))
    for s in (-1, 1):
        fd.add(RoundBox(c0 + v3((0, 0, BANK_Z + 0.016)) + t * (s * (hy - 0.04)), (hx + 0.03, 0.022, 0.018), 0.008, R=R), 0.0, 8)
    fd.add(RoundBox(c, (hx, hy, hz), 0.025, R=R), 0.008, 0)
    for k in range(5):                                                             # louvres on the long side facing in
        p = c - o * hx + t * (-0.12 + 0.06 * k) + v3((0, 0, 0.02))
        fd.sub(RoundBox(p, (0.006, 0.012, 0.07), 0.004, R=R), 0.003)
    pf = c + t * hy
    fd.add(RoundBox(pf, (hx - 0.03, 0.006, hz - 0.035), 0.006, R=R), 0.004, 8)
    fd.add(Cylinder(pf + t * 0.006 + v3((0, 0, 0.04)) + o * 0.03, 0.026, 0.008, rr=0.003, R=rot_from_axes(z_axis=t)), 0.002, 13)
    fd.add(RoundBox(pf + t * 0.01 - o * 0.05 + v3((0, 0, -0.02)), (0.012, 0.008, 0.018), 0.003, R=R), 0.002, 12)
    fd.add(Cylinder(pf + t * 0.008 + o * 0.04 + v3((0, 0, -0.05)), 0.018, 0.014, rr=0.004, R=rot_from_axes(z_axis=t)), 0.002, 5)
    top = c + v3((0, 0, hz))
    fd.add(RoundCone(top - t * 0.12 + v3((0, 0, -0.01)), top - t * 0.12 + v3((0, 0, 0.12)), 0.018, 0.018), 0.006, 5)
    fd.add(Cylinder(top - t * 0.12 + v3((0, 0, 0.13)) + o * 0.0, 0.034, 0.12, rr=0.012, R=rot_from_axes(z_axis=t)), 0.006, 5)
    fd.add(Cylinder(top + t * 0.1 + o * 0.06 + v3((0, 0, 0.01)), 0.022, 0.024, rr=0.006), 0.004, 8)
    for s in (-1, 1):
        fd.add(Torus(top + t * (s * 0.18) + v3((0, 0, 0.02)), 0.018, 0.005, R=rot_from_axes(z_axis=o)), 0.002, 5)
    _m.stencil(fd, "GEN 10KW", c - o * hx + v3((0, 0, -0.06)), -t, v3((0, 0, 1)), 0.03, 13)
    return fd


JB_A = GAPS["gen"] + 0.19          # the junction box's place at the pad's edge
JB_R = FLOOR_R + 0.06


def cable_pts():
    """The generator's cable: from its panel, looping on the ground, to the junction box at the pad's edge."""
    c0, o, t, a = _gap_frame("gen", 1.29)
    start = c0 + t * (GEN_HALF[1] + 0.012) + v3((0, 0, BANK_Z + 0.09))
    jo = v3((math.cos(JB_A), math.sin(JB_A), 0.0))
    end = jo * (JB_R + 0.07) + v3((0, 0, BANK_Z + 0.03))
    mid = (start + end) * 0.5 + o * 0.08
    mid[2] = BANK_Z + 0.014
    return [start, start + t * 0.04 + v3((0, 0, -0.06)), mid, end]


def cable_field():
    """The black rubber cable (8) and the junction box at the pad's edge (olive 0, a black lid, a red light 12)."""
    fd = Field("Cable")
    pts = cable_pts()
    fd.add(Chain(pts, [0.012] * len(pts), k=0.02), 0.0, 8)
    o = v3((math.cos(JB_A), math.sin(JB_A), 0.0))
    t = v3((-math.sin(JB_A), math.cos(JB_A), 0.0))
    R = np.stack([o, t, v3((0, 0, 1))], axis=1)
    jb = o * JB_R + v3((0, 0, BANK_Z + 0.06))
    fd.add(RoundBox(jb, (0.06, 0.08, 0.06), 0.012, R=R), 0.004, 0)
    fd.add(RoundBox(jb + v3((0, 0, 0.058)), (0.064, 0.084, 0.008), 0.006, R=R), 0.003, 8)
    fd.add(Sphere(jb - o * 0.06 + v3((0, 0, 0.02)), 0.01), 0.002, 12)

    return fd


def crates_field():
    """A stack of two olive missile crates (0) in the gap on the right: black corner guards and latches (8), white
    stencils (13)."""
    fd = Field("Crates")
    c0, o, t, a = _gap_frame("crates", 1.3)
    for k, (dz, yaw, L) in enumerate(((0.0, 0.0, 0.36), (0.13, 0.12, 0.34))):
        R = np.stack([o, t, v3((0, 0, 1))], axis=1) @ euler(0, 0, yaw)
        c = c0 + v3((0, 0, BANK_Z + 0.065 + dz))
        fd.add(RoundBox(c, (0.11, L, 0.062), 0.012, R=R), 0.0 if k == 0 else 0.004, 0)
        for su in (-1, 1):
            for sv in (-1, 1):
                fd.add(RoundBox(c + R @ v3((su * 0.11, sv * L, 0.0)), (0.016, 0.016, 0.066), 0.006, R=R), 0.003, 8)
        for sv in (-1, 1):
            fd.add(RoundBox(c + R @ v3((-0.112, sv * 0.18, 0.03)), (0.006, 0.018, 0.016), 0.004, R=R), 0.002, 8)
        _m.stencil(fd, "MSL 1X" if k == 0 else "LOT 07", c + R @ v3((-0.11, 0.0, -0.005)), R @ v3((0, -1, 0)), v3((0, 0, 1)), 0.03, 13)
    return fd


ANT_H = 1.05


def antenna_foot():
    c0, o, t, a = _gap_frame("antenna", 1.27)
    return c0 + v3((0, 0, BANK_Z))


def antenna_field():
    """A field antenna: a grey tripod (5) under a black mast (8), a small olive radio box at its foot (0), a black whip
    with a white tip (13); a black cable from the radio down to the ground."""
    fd = Field("Antenna")
    f0 = antenna_foot()
    hub = f0 + v3((0, 0, 0.32))
    for k in range(3):
        a = GAPS["antenna"] + 2 * math.pi * k / 3 + 0.4
        foot = f0 + v3((math.cos(a) * 0.16, math.sin(a) * 0.16, 0.0))
        fd.add(RoundCone(foot + v3((0, 0, 0.01)), hub, 0.011, 0.011), 0.004, 5)
        fd.add(Cylinder(foot + v3((0, 0, 0.006)), 0.02, 0.012, rr=0.004), 0.002, 8)
    fd.add(Cylinder(hub, 0.022, 0.05, rr=0.006), 0.004, 5)
    fd.add(RoundCone(hub, f0 + v3((0, 0, ANT_H * 0.72)), 0.014, 0.011), 0.004, 8)
    fd.add(RoundCone(f0 + v3((0, 0, ANT_H * 0.72)), f0 + v3((0, 0, ANT_H)), 0.006, 0.004), 0.003, 8)
    fd.add(Sphere(f0 + v3((0, 0, ANT_H + 0.004)), 0.012), 0.002, 13)
    for z in (0.5, 0.68):
        fd.add(Torus(f0 + v3((0, 0, z)), 0.016, 0.004), 0.002, 5)
    o = v3((math.cos(GAPS["antenna"]), math.sin(GAPS["antenna"]), 0.0))
    rb = f0 + o * 0.0 + v3((0, 0, 0.2))
    fd.add(RoundBox(rb + o * 0.04, (0.04, 0.05, 0.035), 0.01, R=rot_from_axes(x_axis=o, z_axis=(0, 0, 1))), 0.004, 0)
    return fd


def _avoid():
    return [(g, max(GAP_W[k], 0.06)) for k, g in GAPS.items()]


def grass_geometry(seed=47):
    """Weeds: tufts round the outside of the wall and in the gaps (never on the pad the launcher sweeps)."""
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(1.42, GROUND_R - 0.02) if not in_hesco(a, 0.05) else rs.uniform(1.52, GROUND_R - 0.01)
        if r > GROUND_R - 0.01:
            continue
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.12 for t in tufts) or any(_angd(a, g) < w + 0.05 for g, w in _avoid()):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(6, 10)
        big = 0.5 + 0.35 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.03)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.008
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
    """A few dandelions (swatch 1: yellow) in the grass outside the wall."""
    rs = np.random.RandomState(seed)
    out = []
    n = 0
    tries = 0
    while n < 6 and tries < 2000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        if any(_angd(a, g) < w + 0.1 for g, w in _avoid()) or in_hesco(a, 0.1):
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
    return [("Ground", ground_field(), 0.008), ("Pad", pad_field(), 0.0035), ("Hesco", hesco_field(), 0.0035),
            ("Fill", fill_field(), 0.004), ("Sandbags", sandbags_field(), 0.004), ("Generator", generator_field(), 0.0026),
            ("Cable", cable_field(), 0.0024), ("Crates", crates_field(), 0.0026), ("Antenna", antenna_field(), 0.002)]


REGION_PARTS = ("Ground", "Pad", "Hesco", "Fill", "Sandbags", "Generator", "Cable", "Crates", "Antenna")
LOW_TARGETS = {"Ground": 1000, "Pad": 2200, "Hesco": 2200, "Fill": 500, "Sandbags": 2800, "Generator": 1300, "Cable": 300,
               "Crates": 800, "Antenna": 500}
KIT = {"olive": _m.OLIVE_KIT, "grey": _m.GUNMETAL, "red": _m.RED, "white": (0.86, 0.85, 0.8)}
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_PadGround", "dirt_label": 5}),
                 "Pad": ("flagstone", {"name": "HQ_PadConcrete", "base": (0.6, 0.59, 0.56), "alt": (0.55, 0.52, 0.48),
                                       "stain": (0.9, 0.72, 0.16)}),
                 "Hesco": ("sacking", {"name": "HQ_Hesco", "base": (0.66, 0.58, 0.44), "dark": (0.44, 0.38, 0.28),
                                       "stencil": (0.16, 0.16, 0.15)}),
                 "Fill": ("ground", {"name": "HQ_HescoFill", "dirt_label": 0}),
                 "Sandbags": ("sacking", {"name": "HQ_PadSandbags"}),
                 "Generator": ("fieldgun", dict(KIT, name="HQ_PadKit")),
                 "Cable": ("fieldgun", dict(KIT, name="HQ_PadKit")),
                 "Crates": ("fieldgun", dict(KIT, name="HQ_PadKit")),
                 "Antenna": ("fieldgun", dict(KIT, name="HQ_PadKit"))}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and r > 1.4 and abs(c.z - ground_height(c.x, c.y)) < 0.03
