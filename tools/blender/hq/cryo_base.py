"""Cryo Field base: a corner of the cleanroom lab. A round, raised platform of white epoxy floor plates (fine joints in a
square grid, an access hatch, a black line round its edge, hazard chevrons across its front) with a violet light strip
set into its edge all round (`GlowRim`); he, the projector and the pedestal stand on it and sweep out to ~0.9 as the
tower turns. Round it, a lower ring of graphite floor tiles on a plinth (its side banded in hazard stripes). On the ring:
behind him on his right a rack of coolant canisters (a black steel frame, three brushed-steel dewars with navy bands and
frosted caps, frost crusted on the floor round them), behind him on his left a lab terminal (a graphite pillar, a
keyboard ledge, a glowing pale-violet screen `GlowTerm`) whose cable runs over the floor under a hazard-striped cable
ramp to a junction box on the platform's edge, behind him a cooling unit (a fan grille on top, louvred sides), and at
the front right a puddle of spilled coolant frozen to a crust. (Distance fields; no grass: it is a lab.)"""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Inter, Shell, Lock, lerp
import cryo as _c

GROUND_R = 1.3
FLOOR_TOP = 0.1                # the outer ring's top
PAD_R = 0.99                   # the raised platform (he, the projector and the pedestal sweep out to ~0.9 of it)
TOP_Z = 0.17                   # the platform's top = where he stands
STAND = v3((-_c.YAW_PIVOT[0], -_c.YAW_PIVOT[1], TOP_Z))
Z = v3((0.0, 0.0, 1.0))
PROP_R = 1.15                  # the props' ring
RACK_A = math.radians(142.0)   # the coolant rack: behind him, on his right (the camera's left)
TERM_A = math.radians(48.0)    # the terminal: behind him on his left
COOL_A = math.radians(96.0)    # the cooling unit: behind him
JUNC_A = math.radians(70.0)    # the junction box on the platform's edge
PUDDLE_A = math.radians(-28.0) # the frozen puddle: front right
RIM_Z = TOP_Z - 0.032          # the light strip's height on the platform's edge
# labels (mats.modern_kit): 0 white epoxy, 5 black, 6 hazard yellow, 7 frost, 8 graphite, 9 gunmetal, 10 steel,
# 11 glass, 12 rubber, 13 violet
WHITE, BLACK, HAZ, FROST, GRAPH, GUN, STEEL, GLASS, RUBBER, VIOLET = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13


def ring_pt(a, r):
    return v3((math.cos(a) * r, math.sin(a) * r, 0.0))


def ring_frame(a):
    """At angle a on the ring: outward and along (counter-clockwise)."""
    return v3((math.cos(a), math.sin(a), 0.0)), v3((-math.sin(a), math.cos(a), 0.0))


def ground_height(x, y):
    return TOP_Z if math.hypot(x, y) < PAD_R else FLOOR_TOP


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def _rr(P):
    return np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)


def _grid(P, step, w, ox=0.0, oy=0.0):
    gx = np.abs(np.mod(P[:, 0] - F(ox), F(step)) - F(step / 2))
    gy = np.abs(np.mod(P[:, 1] - F(oy), F(step)) - F(step / 2))
    return F(step / 2) - np.maximum(gx, gy) - F(w)


def floor_field():
    """The outer ring on its plinth: graphite floor tiles (8) in a square grid, a black chamfered edge (5), its side
    banded with hazard stripes (yellow 6, black 5)."""
    fd = Field("Floor")
    h = FLOOR_TOP + 0.1
    fd.add(Cylinder(v3((0, 0, FLOOR_TOP - h / 2)), GROUND_R, h, rr=0.025), 0.0, GRAPH)
    lo, hi = (-1.4, -1.4, -0.05), (1.4, 1.4, 0.2)
    def joints(P):
        return np.maximum(np.maximum(_grid(P, 0.26, 0.0022, 0.03, 0.05), np.abs(P[:, 2] - F(FLOOR_TOP)) - F(0.006)), F(PAD_R - 0.02) - _rr(P))
    fd.sub(Func(joints, lo, hi), 0.0015)
    side = lambda P: np.maximum(F(GROUND_R - 0.03) - _rr(P), P[:, 2] - F(FLOOR_TOP - 0.025))
    fd.paint(Func(side, lo, hi), BLACK)
    def stripes(P):
        a = np.arctan2(P[:, 1], P[:, 0]) * F(GROUND_R)
        st = np.abs(np.mod(a + P[:, 2] * F(1.0), F(0.12)) - F(0.06)) - F(0.03)
        return np.maximum(np.maximum(st, side(P)), np.maximum(F(-0.07) - P[:, 2], P[:, 2] - F(FLOOR_TOP - 0.035)))
    fd.paint(Func(stripes, lo, hi), HAZ)
    return fd


def pad_field():
    """The raised platform: white epoxy plates (0) in a grid (fine joints), an access hatch under him (steel rim 10, four
    screws), a black line round its top's edge (5) with hazard chevrons across its front (6), its side black (5) with a
    groove all round for the violet light strip."""
    fd = Field("Pad")
    h = TOP_Z - (FLOOR_TOP - 0.02)
    fd.add(Cylinder(v3((0, 0, FLOOR_TOP - 0.02 + h / 2)), PAD_R, h, rr=0.018,
                    disp=lambda P: F(0.0004) * NOISE(P * F(30)), disp_amp=0.0006), 0.0, WHITE)
    lo, hi = (-1.05, -1.05, 0.0), (1.05, 1.05, 0.25)
    top = lambda P: np.abs(P[:, 2] - F(TOP_Z)) - F(0.006)
    fd.sub(Func(lambda P: np.maximum(np.maximum(_grid(P, 0.33, 0.0018, 0.165, 0.165), top(P)), _rr(P) - F(PAD_R - 0.1)), lo, hi), 0.0012)
    # the access hatch
    hc = v3((0.0, 0.33, TOP_Z))
    fd.sub(Torus(hc, 0.13, 0.004), 0.002)
    fd.paint(Inter(Cylinder(hc, 0.142, 0.03), Func(lambda P: F(0.122) - np.sqrt((P[:, 0] - F(hc[0])) ** 2 + (P[:, 1] - F(hc[1])) ** 2), hc - 0.2, hc + 0.2)), STEEL)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        fd.add(Sphere(hc + v3((math.cos(a), math.sin(a), 0)) * 0.132 + Z * 0.0, 0.008), 0.002, STEEL)
    # the black line round the top's edge and the side
    edge = lambda P: np.maximum(np.abs(_rr(P) - F(PAD_R - 0.065)) - F(0.016), F(TOP_Z - 0.02) - P[:, 2])
    fd.paint(Func(edge, lo, hi), BLACK)
    fd.paint(Func(lambda P: np.maximum(F(PAD_R - 0.012) - _rr(P), P[:, 2] - F(TOP_Z - 0.012)), lo, hi), BLACK)
    # hazard chevrons across its front, between the line and the edge
    def chev(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        u = a * F(PAD_R - 0.04) + (_rr(P) - F(PAD_R - 0.04)) * F(0.8)
        st = np.abs(np.mod(u, F(0.08)) - F(0.04)) - F(0.018)
        band = np.maximum(np.abs(_rr(P) - F(PAD_R - 0.03)) - F(0.018), F(TOP_Z - 0.02) - P[:, 2])
        front = np.abs(a + F(math.pi / 2)) - F(0.62)
        return np.maximum(np.maximum(st, front), band)
    fd.paint(Func(lambda P: np.maximum(np.abs(_rr(P) - F(PAD_R - 0.03)) - F(0.018),
                                       np.maximum(F(TOP_Z - 0.02) - P[:, 2], np.abs(np.arctan2(P[:, 1], P[:, 0]) + F(math.pi / 2)) - F(0.62))), lo, hi), HAZ)
    fd.paint(Func(chev, lo, hi), BLACK)
    # the groove for the light strip
    fd.sub(Torus(v3((0, 0, RIM_Z)), PAD_R + 0.004, 0.012), 0.002)
    return fd


def rim_field():
    """The violet light strip round the platform's edge (shipped glowing)."""
    fd = Field("Rim")
    fd.add(Torus(v3((0, 0, RIM_Z)), PAD_R - 0.0015, 0.0085), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the props
def rack_into(fd):
    """A rack of coolant canisters: a black steel frame (5: a base tray, two uprights, a top rail with clamps), three
    brushed-steel dewars (10) with navy bands (8), violet labels (13) and frosted caps (7)."""
    out, along = ring_frame(RACK_A)
    c = ring_pt(RACK_A, PROP_R + 0.01)
    g = FLOOR_TOP
    Rb = np.stack([along, out, Z], axis=1)
    fd.add(RoundBox(c + Z * (g + 0.02), (0.25, 0.1, 0.02), 0.008, R=Rb), 0.0, BLACK)
    for e in (-1, 1):
        p = c + along * (e * 0.235)
        fd.add(RoundBox(p + Z * (g + 0.24), (0.014, 0.05, 0.24), 0.006, R=Rb), 0.004, BLACK)
    fd.add(RoundBox(c + Z * (g + 0.44) + out * 0.01, (0.25, 0.016, 0.018), 0.006, R=Rb), 0.004, BLACK)
    rs = np.random.RandomState(31)
    for k, u in enumerate((-0.15, 0.0, 0.15)):
        p = c + along * u
        hgt = 0.36 + 0.03 * (k % 2)
        cc = p + Z * (g + 0.04 + hgt / 2)
        fd.add(Cylinder(cc, 0.062, hgt, rr=0.02), 0.004, STEEL)
        fd.add(Ellipsoid(p + Z * (g + 0.04 + hgt), (0.062, 0.062, 0.03)), 0.015, STEEL)
        for zz in (0.1, hgt - 0.07):
            fd.add(Torus(p + Z * (g + 0.04 + zz), 0.063, 0.008), 0.004, GRAPH)
        fd.paint(Inter(Shell(Cylinder(cc, 0.062, 0.3), 0.0, 0.01), Func(lambda P, p=p: np.maximum(
            np.abs(P[:, 2] - F(g + 0.04 + hgt * 0.5)) - F(0.04), F(0.0) - (P - p.astype(F)) @ (-out).astype(F)), p - 0.3, p + 0.4), 0.002), VIOLET)
        # the frosted cap and neck
        top = p + Z * (g + 0.04 + hgt + 0.02)
        fd.add(Cylinder(top + Z * 0.02, 0.026, 0.05, rr=0.008), 0.006, GUN)
        for j in range(5):
            a = rs.uniform(0, 2 * math.pi)
            d = v3((math.cos(a), math.sin(a), 0))
            fd.add(Ellipsoid(top + d * rs.uniform(0.02, 0.05) + Z * rs.uniform(-0.01, 0.04), (0.022, 0.018, 0.012),
                             R=rot_from_axes(z_axis=norm(Z + d)), disp=lambda P: F(0.003) * NOISE(P * F(55)), disp_amp=0.004), 0.01, FROST)
        # a clamp round it on the top rail
        fd.add(Torus(p + Z * (g + 0.44), 0.068, 0.009), 0.004, BLACK)
    # frost crusted on the floor round the tray
    for j in range(16):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.12, 0.28)
        q = c + v3((math.cos(a) * r, math.sin(a) * r * 0.7, 0))
        if np.hypot(q[0], q[1]) < PAD_R + 0.04 or np.hypot(q[0], q[1]) > GROUND_R - 0.06:
            continue
        fd.add(Ellipsoid(q + Z * (g + 0.004), (rs.uniform(0.03, 0.06), rs.uniform(0.025, 0.045), rs.uniform(0.008, 0.016)),
                         R=euler(0, 0, rs.uniform(0, 3)), disp=lambda P: F(0.003) * NOISE(P * F(45)), disp_amp=0.004), 0.016, FROST)


def terminal_into(fd):
    """A lab terminal: a graphite pillar (8) on a black foot (5), a keyboard ledge (black keys), the screen's black bezel
    tilted toward the field; its cable down its back (12)."""
    out, along = ring_frame(TERM_A)
    c = ring_pt(TERM_A, PROP_R + 0.02)
    g = FLOOR_TOP
    face = norm(-out + v3((0, -0.6, 0)))                      # the screen faces in and toward the camera
    fa = norm(np.cross(Z, face))
    R = np.stack([fa, face, Z], axis=1)
    fd.add(RoundBox(c + Z * (g + 0.015), (0.12, 0.1, 0.015), 0.008, R=R), 0.0, BLACK)
    fd.add(RoundBox(c + Z * (g + 0.3), (0.075, 0.055, 0.28), 0.02, R=R), 0.006, GRAPH)
    fd.paint(RoundBox(c + face * 0.056 + Z * (g + 0.3), (0.012, 0.01, 0.22), 0.004, R=R), VIOLET)
    # the keyboard ledge
    kc = c + face * 0.09 + Z * (g + 0.5)
    Rk = R @ euler(-0.35, 0, 0)
    fd.add(RoundBox(kc, (0.12, 0.07, 0.014), 0.008, R=Rk), 0.006, GRAPH)
    for i in range(4):
        for j in range(3):
            fd.add(RoundBox(kc + Rk @ v3((-0.075 + 0.05 * i, -0.03 + 0.03 * j, 0.014)), (0.018, 0.01, 0.005), 0.003, R=Rk), 0.002, BLACK)
    # the screen's housing
    sc = SCREEN_C()
    Rs = screen_frame()
    fd.add(RoundBox(sc - Rs[:, 2] * 0.02, (0.15, 0.1, 0.02), 0.014, R=Rs), 0.006, GRAPH)
    fd.add(RoundBox(sc - Rs[:, 2] * 0.004, (0.135, 0.085, 0.006), 0.004, R=Rs), 0.003, BLACK)
    fd.add(RoundCone(c + Z * (g + 0.55), sc - Rs[:, 2] * 0.03, 0.03, 0.025), 0.01, GRAPH)
    return c


def SCREEN_C():
    out, along = ring_frame(TERM_A)
    c = ring_pt(TERM_A, PROP_R + 0.02)
    return c + Z * (FLOOR_TOP + 0.7) - out * 0.01


def screen_frame():
    out, along = ring_frame(TERM_A)
    face = norm(-out + v3((0, -0.6, 0)) + Z * 0.5)
    fa = norm(np.cross(Z, face))
    up = norm(np.cross(face, fa))
    return np.stack([fa, up, face], axis=1)


def term_field():
    """The terminal's screen (shipped glowing pale violet)."""
    fd = Field("Term")
    Rs = screen_frame()
    fd.add(RoundBox(SCREEN_C() + Rs[:, 2] * 0.003, (0.125, 0.075, 0.004), 0.003, R=Rs), 0.0)
    return fd


def cooler_into(fd):
    """A cooling unit: a gunmetal box (9) with louvred sides, a round fan grille on top (black 5, steel rings 10), a
    navy stripe (8 is graphite here: a black stripe), feet."""
    out, along = ring_frame(COOL_A)
    c = ring_pt(COOL_A, PROP_R + 0.01)
    g = FLOOR_TOP
    Rb = np.stack([along, out, Z], axis=1)
    bc = c + Z * (g + 0.13)
    fd.add(RoundBox(bc, (0.15, 0.11, 0.12), 0.02, R=Rb), 0.0, GUN)
    for e in (-1, 1):
        for k in range(5):
            fd.sub(RoundBox(bc + along * (e * 0.152) + Z * (-0.06 + 0.03 * k), (0.008, 0.08, 0.007), 0.004, R=Rb), 0.002)
    tc = bc + Z * 0.12
    fd.add(Cylinder(tc + Z * 0.004, 0.095, 0.014, rr=0.006), 0.004, BLACK)
    for r in (0.03, 0.055, 0.08):
        fd.add(Torus(tc + Z * 0.013, r, 0.0045), 0.002, STEEL)
    for k in range(4):
        a = k * math.pi / 4
        d = v3((math.cos(a), math.sin(a), 0))
        fd.add(RoundCone(tc + Z * 0.013 - d * 0.085, tc + Z * 0.013 + d * 0.085, 0.003, 0.003), 0.002, STEEL)
    fd.add(Cylinder(tc + Z * 0.016, 0.018, 0.012, rr=0.004), 0.002, STEEL)
    fd.paint(RoundBox(bc - out * 0.11 + Z * 0.06, (0.12, 0.01, 0.012), 0.004, R=Rb), VIOLET)
    for e in (-1, 1):
        for e2 in (-1, 1):
            fd.add(Cylinder(c + along * (e * 0.12) + out * (e2 * 0.08) + Z * (g + 0.006), 0.018, 0.014, rr=0.004), 0.003, BLACK)


def junction_into(fd, term_c):
    """A junction box on the platform's edge (gunmetal 9, a hazard label 6), the terminal's cable to it over the floor
    under a hazard-striped cable ramp (yellow 6 and black 5)."""
    jo, ja = ring_frame(JUNC_A)
    jc = ring_pt(JUNC_A, PAD_R + 0.058)
    g = FLOOR_TOP
    Rj = np.stack([ja, jo, Z], axis=1)
    fd.add(RoundBox(jc + Z * (g + 0.05), (0.06, 0.04, 0.05), 0.01, R=Rj), 0.0, GUN)
    fd.paint(RoundBox(jc + jo * 0.04 + Z * (g + 0.055), (0.03, 0.01, 0.022), 0.004, R=Rj), HAZ)
    # the cable ramp from the terminal's foot to the box
    to, ta = ring_frame(TERM_A)
    a0 = TERM_A - 0.06
    pts = []
    for k in range(7):
        a = a0 + (JUNC_A + 0.05 - a0) * k / 6
        r = PROP_R - 0.06 - 0.05 * math.sin(math.pi * k / 6)
        pts.append(ring_pt(a, r) + Z * g)
    for p0, p1 in zip(pts[:-1], pts[1:]):
        d = norm(p1 - p0)
        Rr = rot_from_axes(y_axis=d, z_axis=Z)
        L = float(np.linalg.norm(p1 - p0)) / 2 + 0.01
        fd.add(RoundBox(lerp(p0, p1, 0.5) + Z * 0.008, (0.04, L, 0.012), 0.008, R=Rr), 0.006, HAZ)
    def ramp_stripes(P):
        u = (P[:, 0] + P[:, 1]) * F(1.0)
        st = np.abs(np.mod(u, F(0.07)) - F(0.035)) - F(0.016)
        near = F(1.0) * np.ones(len(P), F)
        for p0, p1 in zip(pts[:-1], pts[1:]):
            ab = (p1 - p0).astype(F)
            t = np.clip(((P - p0.astype(F)) @ ab) / F(ab @ ab), 0, 1)
            q = P - p0.astype(F) - t[:, None] * ab[None, :]
            near = np.minimum(near, np.sqrt((q[:, :2] ** 2).sum(1)) - F(0.05))
        return np.maximum(np.maximum(st, near), np.maximum(F(g + 0.01) - P[:, 2], P[:, 2] - F(g + 0.04)))
    fd.paint(Func(ramp_stripes, (-1.4, -1.4, 0.0), (1.4, 1.4, 0.3)), BLACK)


def puddle_into(fd):
    """Spilled coolant frozen to a crust on the floor at the front right (frost 7)."""
    rs = np.random.RandomState(13)
    c = ring_pt(PUDDLE_A, PROP_R + 0.03)
    for j in range(11):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.0, 0.08)
        q = c + v3((math.cos(a) * r * 1.6, math.sin(a) * r, 0))
        fd.add(Ellipsoid(q + Z * (FLOOR_TOP + 0.002), (rs.uniform(0.04, 0.07), rs.uniform(0.03, 0.05), rs.uniform(0.006, 0.012)),
                         R=euler(0, 0, rs.uniform(0, 3)), disp=lambda P: F(0.002) * NOISE(P * F(45)), disp_amp=0.003), 0.02, FROST)
    for j in range(4):                                       # a few shards standing up
        a = rs.uniform(0, 2 * math.pi)
        q = c + v3((math.cos(a), math.sin(a), 0)) * rs.uniform(0.02, 0.07)
        d = norm(v3((rs.uniform(-0.4, 0.4), rs.uniform(-0.4, 0.4), 1.0)))
        fd.add(RoundCone(q + Z * FLOOR_TOP, q + Z * FLOOR_TOP + d * rs.uniform(0.04, 0.07), 0.012, 0.003), 0.006, FROST)


def _part(name, *fns):
    fd = Field(name)
    for fn in fns:
        fn(fd)
    return fd


def fields():
    """Each prop is its own part (small meshing grids); all are baked into the one atlas."""
    return [("Floor", floor_field(), 0.006), ("Pad", pad_field(), 0.0045), ("Rim", rim_field(), 0.003),
            ("Rack", _part("Rack", rack_into), 0.0024), ("Terminal", _part("Terminal", terminal_into), 0.0024),
            ("Cable", _part("Cable", lambda fd: junction_into(fd, None)), 0.0028),
            ("Cooler", _part("Cooler", cooler_into), 0.0024), ("Puddle", _part("Puddle", puddle_into), 0.003),
            ("Term", term_field(), 0.003)]


def grass_geometry(seed=0):
    """No grass in a lab."""
    return np.zeros((0, 3)), [], np.zeros((0, 2)), np.zeros(0, int)


def flower_geometry(seed=0):
    return []


REGION_PARTS = ("Floor", "Pad", "Rack", "Terminal", "Cable", "Cooler", "Puddle")
LOW_TARGETS = {"Floor": 1600, "Pad": 2600, "Rim": 400, "Rack": 2600, "Terminal": 1500, "Cable": 700, "Cooler": 1300,
               "Puddle": 500, "Term": 30}
LAB = {"base": (0.88, 0.89, 0.9), "weave": 0.0, "black": (0.06, 0.06, 0.07), "red": (0.95, 0.74, 0.12),
       "white": (0.84, 0.92, 1.0), "olive": (0.22, 0.23, 0.27), "gunmetal": (0.26, 0.27, 0.3), "steel": (0.66, 0.68, 0.72),
       "glass": (0.05, 0.055, 0.08), "rubber": (0.08, 0.08, 0.09), "coyote": _c.VIOLET_C}
MAT_OVERRIDES = {"Floor": ("modern_kit", dict(LAB, name="HQ_CryoLabFloor")),
                 "Pad": ("modern_kit", dict(LAB, name="HQ_CryoLabFloor")),
                 "Rack": ("modern_kit", dict(LAB, name="HQ_CryoLabKit")),
                 "Terminal": ("modern_kit", dict(LAB, name="HQ_CryoLabKit")),
                 "Cable": ("modern_kit", dict(LAB, name="HQ_CryoLabKit")),
                 "Cooler": ("modern_kit", dict(LAB, name="HQ_CryoLabKit")),
                 "Puddle": ("modern_kit", dict(LAB, name="HQ_CryoLabKit")),
                 "Rim": ("glow_ball", {"name": "HQ_CryoRim", "col": _c.GLOW_V, "strength": 1.0}),
                 "Term": ("glow_ball", {"name": "HQ_CryoTerm", "col": (0.78, 0.64, 1.0), "strength": 0.8})}
GLOW = {"Rim": (_c.GLOW_V, 1.1, 0.5), "Term": ((0.78, 0.64, 1.0), 0.8, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
