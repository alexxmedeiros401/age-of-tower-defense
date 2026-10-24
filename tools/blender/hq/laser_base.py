"""Laser Turret base: a gun platform in the corps' research lab. A round graphite floor plate (bolted panels with seams
between them, vent grilles, a ring of yellow-and-black hazard striping near its edge and, in a groove round its rim, a
glowing violet light strip: `Rim`) stands on a ring of pale epoxy deck (tile joints, yellow floor markings). Nothing on
the plate stands proud of it: the turret and its gunner turn over it. On the deck round it, mostly behind the gunner: a
capacitor bank humming (a graphite cabinet, three gunmetal capacitors with glowing violet bands, cooling fins, a violet
status bar), cable runs from it to a socket in the plate's rim and to the terminal; a slim terminal on a post with its
keyboard and a violet holo-screen floating over it (`Holo`); an open hard case of spare power cells (their tops glowing);
a squat cooling unit with a fan grille. Glowing parts ship as their own meshes (`Rim`, `Lights`, `Holo`)."""
import math
import numpy as np
from sdf import (Field, Sphere, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Ellipsoid, Chain, v3, norm, rot_from_axes,
                 smax, NOISE, F, euler)
from caveman import Inter, Shell
import laser as _l
from missile import stencil

GROUND_R = 1.38                # the deck ring's edge
GROUND_TOP = 0.07              # the deck's top
PLATE_R = 1.06                 # the floor plate's edge
TOP_Z = 0.13                   # the plate's top: where he and the pedestal stand
STAND = v3((-_l.YAW_PIVOT[0], -_l.YAW_PIVOT[1], TOP_Z))
RIM_R, RIM_W = 1.015, 0.013    # the light strip's middle radius and half width (in a groove round the plate's rim)
HAZ_R = (0.9, 0.975)           # the hazard band
PROP_R = 1.22                  # the props' ring, on the deck
Z = v3((0.0, 0.0, 1.0))
BANK_A = math.radians(112.0)   # behind him, on his left (the camera's right)
TERM_A = math.radians(58.0)
CELLS_A = math.radians(158.0)
COOL_A = math.radians(16.0)
SOCK_A = math.radians(92.0)    # the cable's socket in the plate's rim
B = dict(BASE=0, BLACK=5, VIO=6, WHITE=7, ALT=8, GUN=9, STEEL=10, GLASS=11, RUBBER=12, HAZ=13)


def ring_pt(a, r, z=0.0):
    return v3((math.cos(a) * r, math.sin(a) * r, z))


def frame_at(a):
    """At angle a on the ring: outward o, tangent t (counter-clockwise), up; R with columns (t, o, up)."""
    o = v3((math.cos(a), math.sin(a), 0.0))
    t = v3((-math.sin(a), math.cos(a), 0.0))
    return o, t, np.stack([t, o, Z], axis=1)


def ground_height(x, y):
    r = math.hypot(x, y)
    return TOP_Z if r < PLATE_R else GROUND_TOP


def _rr(P):
    return np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)


# ======================================================================================= the deck and the plate
def ground_field():
    """The deck ring: pale epoxy (0) in square tiles (joints 5), rounded at its edge; yellow floor markings (13)."""
    fd = Field("Ground")
    def disc(P):
        r = _rr(P)
        dx = r - F(GROUND_R)
        dz = np.maximum(P[:, 2] - F(GROUND_TOP), F(-0.12) - P[:, 2])
        q0, q1 = dx + F(0.03), dz + F(0.03)
        return np.minimum(np.maximum(q0, q1), F(0)) + np.sqrt(np.maximum(q0, 0) ** 2 + np.maximum(q1, 0) ** 2) - F(0.03)
    lo, hi = (-GROUND_R - 0.05, -GROUND_R - 0.05, -0.2), (GROUND_R + 0.05, GROUND_R + 0.05, 0.12)
    fd.add(Func(disc, lo, hi, disp=lambda P: F(0.0006) * NOISE(P * F(40)), disp_amp=0.001), 0.0)
    def joints(P):
        cell = F(0.4)
        gx = np.abs(((P[:, 0] + F(10.2)) % cell) - cell / 2)
        gy = np.abs(((P[:, 1] + F(10.2)) % cell) - cell / 2)
        return np.maximum(np.minimum(gx, gy) - F(0.0035), F(GROUND_TOP - 0.01) - P[:, 2])
    fd.paint(Func(joints, lo, hi), B["BLACK"])
    # floor markings: a yellow line round the deck's outer edge, broken at the props
    def line(P):
        r = _rr(P)
        return np.maximum(np.abs(r - F(GROUND_R - 0.06)) - F(0.012), F(GROUND_TOP - 0.01) - P[:, 2])
    fd.paint(Func(line, lo, hi), B["HAZ"])
    for a0 in (math.radians(-30.0), math.radians(-90.0), math.radians(-150.0), math.radians(210.0)):
        o, t, R = frame_at(a0)
        c = o * (PROP_R + 0.02) + Z * GROUND_TOP
        for s in (-1, 1):
            fd.paint(RoundCone(c + t * (s * 0.02) - o * 0.07, c + t * (s * 0.09) + o * 0.02, 0.012, 0.012), B["HAZ"])
    return fd


def plate_field():
    """The floor plate: graphite (0) panels, seams (5), bolt heads (9), vent grilles (5), a ring of hazard striping (13 on
    5) near the edge, the groove round its rim the light strip lies in, a navy (8) ring round the middle."""
    fd = Field("Plate")
    R = PLATE_R + 0.03
    def fn(P):
        r = _rr(P)
        d = np.maximum(P[:, 2] - F(TOP_Z), F(GROUND_TOP - 0.03) - P[:, 2])
        q0, q1 = r - F(PLATE_R) + F(0.02), d + F(0.02)
        return np.minimum(np.maximum(q0, q1), F(0)) + np.sqrt(np.maximum(q0, 0) ** 2 + np.maximum(q1, 0) ** 2) - F(0.02)
    lo, hi = (-R, -R, GROUND_TOP - 0.06), (R, R, TOP_Z + 0.03)
    fd.add(Func(fn, lo, hi, disp=lambda P: F(0.0005) * NOISE(P * F(50)), disp_amp=0.001), 0.0)
    # the rim's groove (the light strip lies in it)
    fd.sub(Func(lambda P: np.maximum(np.abs(_rr(P) - F(RIM_R)) - F(RIM_W + 0.004), np.abs(P[:, 2] - F(TOP_Z)) - F(0.012)), lo, hi), 0.003)
    # seams: six radial ones and a ring
    for k in range(6):
        a = math.radians(30.0 + 60.0 * k)
        d = v3((math.cos(a), math.sin(a), 0.0))
        fd.sub(RoundCone(d * 0.56 + Z * TOP_Z, d * (HAZ_R[0] - 0.03) + Z * TOP_Z, 0.004, 0.004), 0.002)
    fd.sub(Func(lambda P: np.maximum(np.abs(_rr(P) - F(0.56)) - F(0.004), np.abs(P[:, 2] - F(TOP_Z)) - F(0.004)), lo, hi), 0.002)
    fd.paint(Func(lambda P: np.maximum(np.abs(_rr(P) - F(0.5)) - F(0.035), F(TOP_Z - 0.01) - P[:, 2]), lo, hi), B["ALT"])
    for k in range(12):
        a = math.radians(15.0 + 30.0 * k)
        for r in (0.6, HAZ_R[0] - 0.05):
            fd.add(Cylinder(ring_pt(a, r, TOP_Z + 0.002), 0.012, 0.008, rr=0.003), 0.002, B["GUN"])
    # vent grilles between the seams
    for k in range(6):
        a = math.radians(60.0 * k)
        o, t, Rm = frame_at(a)
        c = o * 0.74 + Z * TOP_Z
        fd.add(RoundBox(c, (0.09, 0.05, 0.004), 0.004, R=Rm), 0.002, B["GUN"])
        for j in range(4):
            fd.sub(RoundBox(c + t * (-0.06 + 0.04 * j), (0.008, 0.035, 0.008), 0.003, R=Rm), 0.002)
    # the hazard band: diagonal yellow-and-black stripes
    def band(P):
        r = _rr(P)
        return np.maximum(np.abs(r - F(0.5 * (HAZ_R[0] + HAZ_R[1]))) - F(0.5 * (HAZ_R[1] - HAZ_R[0])), F(TOP_Z - 0.01) - P[:, 2])
    fd.paint(Func(band, lo, hi), B["BLACK"])
    def stripes(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        r = _rr(P)
        u = a * F(0.94) + (r - F(HAZ_R[0])) * F(1.2)
        per = F(2 * math.pi / 64)
        s = np.abs(((u + F(20.0)) % per) - per / 2) - per / 4
        return np.maximum(band(P), s * F(0.9))
    fd.paint(Func(stripes, lo, hi), B["HAZ"])
    # the corps' mark painted in violet in front of the pedestal (a chevron)
    o = v3((0.0, -1.0, 0.0))
    c = o * 0.78 + Z * TOP_Z
    for s in (-1, 1):
        fd.paint(RoundCone(c + v3((s * 0.07, 0.03, 0)), c + v3((0, -0.03, 0)), 0.014, 0.014), B["VIO"])
    return fd


def rim_field():
    """The light strip in the rim's groove (shipped glowing violet)."""
    fd = Field("Rim")
    R = RIM_R + RIM_W + 0.02
    fd.add(Func(lambda P: np.maximum(np.abs(_rr(P) - F(RIM_R)) - F(RIM_W), np.abs(P[:, 2] - F(TOP_Z - 0.006)) - F(0.006)),
                (-R, -R, TOP_Z - 0.03), (R, R, TOP_Z + 0.02)), 0.0)
    return fd


# ======================================================================================= the props
BANK_HALF = (0.2, 0.105, 0.2)     # along the ring, radial, height (half)


def bank_c():
    o, t, R = frame_at(BANK_A)
    return o * (PROP_R + 0.02) + Z * (GROUND_TOP + BANK_HALF[2])


def bank_field():
    """The capacitor bank: a graphite (0) cabinet on black feet, navy (8) side panels with cooling fins (9), a black
    face with a slot for the status bar; three gunmetal (9) capacitors standing on its top, black (5) sleeves, bright
    terminals (10); a hazard sticker (13)."""
    fd = Field("Bank")
    o, t, R = frame_at(BANK_A)
    c = bank_c()
    hx, hy, hz = BANK_HALF
    fd.add(RoundBox(c, (hx, hy, hz), 0.02, R=R), 0.0, B["BASE"])
    for s in (-1, 1):
        fd.add(RoundBox(c + t * (s * (hx + 0.006)), (0.012, hy - 0.012, hz - 0.02), 0.006, R=R), 0.004, B["ALT"])
        for k in range(5):
            fd.add(RoundBox(c + t * (s * (hx + 0.018)) + Z * (-0.1 + 0.05 * k), (0.012, hy - 0.025, 0.006), 0.003, R=R), 0.002, B["GUN"])
        fd.add(RoundBox(c + t * (s * (hx - 0.03)) - Z * (hz + 0.012), (0.03, hy - 0.01, 0.012), 0.004, R=R), 0.004, B["BLACK"])
    face = c - o * hy
    fd.add(RoundBox(face, (hx - 0.03, 0.006, hz - 0.03), 0.006, R=R), 0.004, B["BLACK"])
    fd.sub(RoundBox(face - o * 0.004 + Z * 0.08, (0.11, 0.008, 0.014), 0.004, R=R), 0.002)
    fd.paint(RoundBox(face + Z * -0.06 + t * 0.1, (0.03, 0.02, 0.022), 0.004, R=R), B["HAZ"])
    stencil(fd, "CAP BANK", face - o * 0.006 + Z * 0.0, -t, Z, 0.028, B["WHITE"], depth=0.01)
    for k in (-1, 0, 1):
        cc = c + t * (k * 0.1) + Z * (hz + 0.07)
        fd.add(Cylinder(cc, 0.052, 0.14, rr=0.012), 0.006, B["GUN"])
        fd.add(Cylinder(cc - Z * 0.03, 0.055, 0.05, rr=0.006), 0.003, B["BLACK"])
        fd.add(Cylinder(cc + Z * 0.072, 0.03, 0.016, rr=0.005), 0.003, B["STEEL"])
        for s in (-1, 1):
            fd.add(Cylinder(cc + Z * 0.082 + t * (s * 0.016), 0.008, 0.02, rr=0.003), 0.002, B["STEEL"])
    return fd


def term_frame():
    o, t, R = frame_at(TERM_A)
    foot = o * (PROP_R + 0.03) + Z * GROUND_TOP
    return foot, o, t, R


def terminal_field():
    """The terminal: a graphite (0) post on a foot plate, a sloped console (navy 8 frame) with a black keyboard (5) and a
    violet key (6); the holo projector's gunmetal (9) lip along the console's back edge."""
    fd = Field("Terminal")
    foot, o, t, R = term_frame()
    fd.add(RoundBox(foot + Z * 0.012, (0.12, 0.1, 0.012), 0.008, R=R), 0.0, B["ALT"])
    fd.add(RoundBox(foot + Z * 0.27, (0.04, 0.035, 0.26), 0.014, R=R), 0.006, B["BASE"])
    # the console, sloping down toward the plate (he could reach it)
    Rc = R @ euler(-0.5, 0, 0)
    cc = foot + Z * 0.56 - o * 0.02
    fd.add(RoundBox(cc, (0.15, 0.1, 0.022), 0.012, R=Rc), 0.008, B["ALT"])
    fd.add(RoundBox(cc + Rc @ v3((0, -0.01, 0.02)), (0.12, 0.06, 0.006), 0.004, R=Rc), 0.003, B["BLACK"])
    for i in range(4):
        for j in range(2):
            fd.add(RoundBox(cc + Rc @ v3((-0.09 + 0.06 * i, -0.04 + 0.04 * j, 0.027)), (0.022, 0.014, 0.004), 0.003, R=Rc),
                   0.002, B["VIO"] if (i, j) == (3, 0) else B["BASE"])
    fd.add(RoundBox(cc + Rc @ v3((0, 0.09, 0.03)), (0.13, 0.014, 0.012), 0.006, R=Rc), 0.004, B["GUN"])
    return fd


def holo_frame():
    foot, o, t, R = term_frame()
    Rh = R @ euler(-1.35, 0, 0)          # nearly upright, tipped back a little, facing the plate's middle
    c = foot + Z * 0.8 + o * 0.03
    return c, Rh


def holo_field():
    """The holo-screen floating over the console (shipped glowing violet): a thin pane with a brighter frame."""
    fd = Field("Holo")
    c, Rh = holo_frame()
    fd.add(RoundBox(c, (0.14, 0.09, 0.003), 0.003, R=Rh), 0.0)
    return fd


def cells_frame():
    o, t, R = frame_at(CELLS_A)
    c = o * (PROP_R + 0.02) + Z * GROUND_TOP
    return c, o, t, R


CELL_SLOTS = [(-0.09, -0.04), (-0.03, 0.04), (0.03, -0.04), (0.09, 0.04)]
CELL_H = 0.24


def cells_field():
    """An open hard case (graphite 0, navy rim 8, black foam 5, its lid standing open behind it) of spare power cells: four
    black (5) cells with gunmetal caps (9) standing in the foam."""
    fd = Field("Cells")
    c, o, t, R = cells_frame()
    hx, hy, h = 0.17, 0.1, 0.12
    def box(P):
        q = (P - c.astype(F)) @ R.astype(F)
        outer = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx), np.abs(q[:, 1]) - F(hy)), np.maximum(-q[:, 2], q[:, 2] - F(h)))
        inner = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx - 0.014), np.abs(q[:, 1]) - F(hy - 0.014)), F(h - 0.05) - q[:, 2])
        return np.maximum(outer, -inner)
    lo, hi = c - 0.3, c + 0.3
    fd.add(Func(box, lo, hi), 0.0, B["BASE"])
    fd.add(Func(lambda P: np.maximum(box(P) - F(0.004), np.abs(P[:, 2] - F(c[2] + h - 0.008)) - F(0.008)), lo, hi), 0.004, B["ALT"])
    fd.add(RoundBox(c + Z * (h - 0.06), (hx - 0.016, hy - 0.016, 0.008), 0.004, R=R), 0.002, B["BLACK"])
    for sx in (-1, 1):
        fd.add(RoundBox(c + t * (sx * (hx + 0.006)) + Z * (h * 0.6), (0.006, 0.03, 0.012), 0.004, R=R), 0.002, B["GUN"])
    # the lid, open on its hinges along the outer edge, leaning back
    Rl = R @ euler(1.95, 0, 0)
    hinge = c + o * hy + Z * h
    lc = hinge + Rl @ v3((0.0, -hy, -0.012))
    fd.add(RoundBox(lc, (hx, hy, 0.014), 0.01, R=Rl), 0.004, B["BASE"])
    fd.add(RoundBox(lc + Rl @ v3((0, 0, -0.014)), (hx - 0.02, hy - 0.02, 0.006), 0.004, R=Rl), 0.003, B["BLACK"])
    stencil(fd, "PWR CELL", lc + Rl @ v3((0, 0, 0.015)), t, norm(Rl @ v3((0, -1, 0))), 0.026, B["WHITE"], depth=0.008)
    for (u, w) in CELL_SLOTS:
        p = c + t * u + o * w + Z * (h - 0.06)
        fd.add(Cylinder(p + Z * (CELL_H * 0.5 - 0.02), 0.024, CELL_H - 0.04, rr=0.006), 0.003, B["BLACK"])
        fd.add(Cylinder(p + Z * (CELL_H - 0.04), 0.026, 0.02, rr=0.005), 0.003, B["GUN"])
        fd.add(Cylinder(p + Z * 0.012, 0.026, 0.018, rr=0.005), 0.003, B["GUN"])
    return fd


def cool_frame():
    o, t, R = frame_at(COOL_A)
    return o * (PROP_R + 0.02) + Z * GROUND_TOP, o, t, R


def cooler_field():
    """A squat cooling unit: a graphite (0) box with navy corners (8), a round fan grille on its top (black 5, gunmetal
    blades 9), louvres on its faces, a short duct of black rubber (12) into the plate's side."""
    fd = Field("Cooler")
    f0, o, t, R = cool_frame()
    hx, hy, hz = 0.145, 0.11, 0.13
    c = f0 + Z * hz
    fd.add(RoundBox(c, (hx, hy, hz), 0.02, R=R), 0.0, B["BASE"])
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(RoundBox(c + t * (sx * hx) + o * (sy * hy), (0.018, 0.018, hz + 0.004), 0.008, R=R), 0.003, B["ALT"])
    top = c + Z * hz
    fd.sub(Cylinder(top, 0.075, 0.03, rr=0.004), 0.003)
    fd.add(Cylinder(top - Z * 0.02, 0.07, 0.01), 0.002, B["BLACK"])
    for k in range(5):
        a = 2 * math.pi * k / 5
        Rb = R @ euler(0, 0.35, a)
        fd.add(RoundBox(top - Z * 0.012 + R @ v3((math.cos(a) * 0.035, math.sin(a) * 0.035, 0)), (0.03, 0.012, 0.003), 0.002, R=Rb), 0.002, B["GUN"])
    fd.add(Cylinder(top - Z * 0.008, 0.016, 0.014, rr=0.004), 0.002, B["GUN"])
    for k in range(4):
        fd.add(RoundBox(top + R @ v3((0, 0, 0.002)) + t * 0.0, (0.078, 0.003, 0.004), 0.002, R=R @ euler(0, 0, k * math.pi / 4)), 0.001, B["GUN"])
    for k in range(4):
        fd.sub(RoundBox(c - o * hy + Z * (-0.06 + 0.035 * k), (0.09, 0.008, 0.006), 0.003, R=R), 0.002)
    # the duct into the plate
    a = c - o * hy + Z * (-0.04)
    fd.add(Chain([a, a - o * 0.06, a - o * 0.12 + Z * -0.02], [0.03, 0.03, 0.028], k=0.01), 0.006, B["RUBBER"])
    return fd


def lights_field():
    """The props' violet lights (shipped glowing): the capacitors' bands, the bank's status bar, the spare cells' tops, the
    terminal's status light."""
    fd = Field("Lights")
    o, t, R = frame_at(BANK_A)
    c = bank_c()
    for k in (-1, 0, 1):
        cc = c + t * (k * 0.1) + Z * (BANK_HALF[2] + 0.07)
        fd.add(Cylinder(cc + Z * 0.035, 0.0535, 0.012, rr=0.003), 0.0)
    face = c - o * BANK_HALF[1]
    fd.add(RoundBox(face - o * 0.002 + Z * 0.08, (0.105, 0.006, 0.01), 0.004, R=R), 0.0)
    cc, o2, t2, R2 = cells_frame()
    for (u, w) in CELL_SLOTS:
        p = cc + t2 * u + o2 * w + Z * (0.12 - 0.06)
        fd.add(Cylinder(p + Z * (CELL_H - 0.026), 0.016, 0.012, rr=0.004), 0.0)
    foot, o3, t3, R3 = term_frame()
    fd.add(Sphere(foot + Z * 0.45 - o3 * 0.036, 0.009), 0.0)
    return fd


def cable_pts():
    """The cables (three): bank -> the plate's socket, bank -> the terminal's foot, the cooler -> the plate's side."""
    ob, tb, Rb = frame_at(BANK_A)
    bc = bank_c()
    so = ring_pt(SOCK_A, PLATE_R + 0.02, GROUND_TOP + 0.012)
    a0 = bc - ob * (BANK_HALF[1] + 0.01) + tb * 0.1 - Z * (BANK_HALF[2] - 0.02)
    mid = ring_pt(0.5 * (BANK_A + SOCK_A) + 0.04, PLATE_R + 0.07, GROUND_TOP + 0.012)
    c1 = [a0, a0 - ob * 0.04 + Z * -0.02, mid, so]
    foot, o, t, R = term_frame()
    a1 = bc + tb * -(BANK_HALF[0] + 0.01) - Z * (BANK_HALF[2] - 0.03)
    m1 = ring_pt(0.5 * (BANK_A + TERM_A), PROP_R + 0.06, GROUND_TOP + 0.012)
    e1 = foot + t * 0.11 + Z * 0.012
    c2 = [a1, a1 + tb * -0.05 + Z * -0.02, m1, e1]
    return [c1, c2]


def cables_field():
    """Black rubber cables (12) along the deck; the socket in the plate's rim (gunmetal 9, a navy collar 8)."""
    fd = Field("Cables")
    for pts in cable_pts():
        fd.add(Chain(pts, [0.014] * len(pts), k=0.03), 0.0, B["RUBBER"])
    so = ring_pt(SOCK_A, PLATE_R + 0.01, GROUND_TOP + 0.02)
    o, t, R = frame_at(SOCK_A)
    fd.add(RoundBox(so, (0.05, 0.03, 0.03), 0.01, R=R), 0.006, B["GUN"])
    fd.add(Cylinder(so + o * 0.03, 0.022, 0.03, rr=0.006, R=rot_from_axes(z_axis=o)), 0.004, B["ALT"])
    return fd


def fields():
    return [("Ground", ground_field(), 0.006), ("Plate", plate_field(), 0.0034), ("Rim", rim_field(), 0.002),
            ("Bank", bank_field(), 0.0026), ("Terminal", terminal_field(), 0.0024), ("Holo", holo_field(), 0.002),
            ("Cells", cells_field(), 0.0024), ("Cooler", cooler_field(), 0.0024), ("Lights", lights_field(), 0.0016),
            ("Cables", cables_field(), 0.0024)]


def grass_geometry(seed=0):
    """No grass in the lab."""
    return np.zeros((0, 3)), [], np.zeros((0, 2)), np.zeros((0,))


def flower_geometry(seed=0):
    return []


def is_grass_face(c, n):
    return False


REGION_PARTS = ("Ground", "Plate", "Bank", "Terminal", "Cells", "Cooler", "Cables")
LOW_TARGETS = {"Ground": 1000, "Plate": 3600, "Rim": 420, "Bank": 1800, "Terminal": 1100, "Holo": 40, "Cells": 1600,
               "Cooler": 1100, "Lights": 420, "Cables": 500}
KIT = dict(weave=0.0, black=(0.05, 0.05, 0.06), red=_l.VIOLET, white=_l.WHITE, gunmetal=_l.GUNMETAL, olive=_l.NAVY,
           coyote=_l.HAZARD, rubber=(0.07, 0.07, 0.075))
MAT_OVERRIDES = {"Ground": ("modern_kit", dict(KIT, name="HQ_LzrDeck", base=(0.8, 0.81, 0.83), gloss=0.32, black=(0.5, 0.51, 0.54))),
                 "Plate": ("modern_kit", dict(KIT, name="HQ_LzrPlate", base=_l.GRAPHITE, gloss=0.45)),
                 "Bank": ("modern_kit", dict(KIT, name="HQ_LzrProps", base=_l.GRAPHITE, gloss=0.4)),
                 "Terminal": ("modern_kit", dict(KIT, name="HQ_LzrProps", base=_l.GRAPHITE, gloss=0.4)),
                 "Cells": ("modern_kit", dict(KIT, name="HQ_LzrProps", base=_l.GRAPHITE, gloss=0.4)),
                 "Cooler": ("modern_kit", dict(KIT, name="HQ_LzrProps", base=_l.GRAPHITE, gloss=0.4)),
                 "Cables": ("modern_kit", dict(KIT, name="HQ_LzrProps", base=_l.GRAPHITE, gloss=0.4))}
GLOW = {"Rim": (_l.VIOLET, 1.0, 0.5), "Lights": (_l.VIOLET, 1.1, 0.5), "Holo": ((0.78, 0.52, 1.0), 0.9, 0.6)}
FLAME_PIVOT = None
