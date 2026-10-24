"""Arc Cannon base: the Resistance's barricaded firing step inside the robots' data center. A round raised step of steel
floor grating (bar grating in a gunmetal frame, worn bright where boots go, an amber Resistance slash sprayed across its
front, amber marker lamps round its rim: `Rim`) stands on a ring of the data center's own floor (dark raised-floor
tiles, some perforated, a cable trench). Nothing on the step stands proud of it: the cannon and its gunner turn over it.
On the floor round it: a low curved wall of sandbags across the front with two salvaged white robot armour plates set in
it (dented, sprayed with amber slashes); behind on his right a field battery bank (three charcoal battery boxes on a
skid, amber charge strips, fat terminals) with its cable to a socket in the step's rim; behind on his left a supply
crate with an ammo box on it; at the back the Resistance's banner: an amber scrap of cloth high on a salvaged pipe (out of
the cannon's sweep), its foot held in a heap of sandbags. Glowing parts ship as their own meshes (`Rim`, `Lights`)."""
import math
import numpy as np
from sdf import (Field, Sphere, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Ellipsoid, Chain, v3, norm, rot_from_axes,
                 smax, NOISE, F, euler)
from caveman import Inter, Shell, Lock
import arc_cannon as _a
from missile import stencil

GROUND_R = 1.38                # the floor ring's edge
GROUND_TOP = 0.07              # the floor's top
PLATE_R = 1.06                 # the step's edge
TOP_Z = 0.13                   # the step's top: where he and the pedestal stand
STAND = v3((-_a.YAW_PIVOT[0], -_a.YAW_PIVOT[1], TOP_Z))
FRAME_W = 0.07                 # the grating's frame (a ring at the step's edge)
LAMP_R = 1.035                 # the marker lamps' ring (in the frame's outer edge)
PROP_R = 1.22                  # the props' ring, on the floor
Z = v3((0.0, 0.0, 1.0))
WALL_A = (math.radians(-152.0), math.radians(-28.0))       # the sandbag wall's ends (across the front: -Y)
PLATE_AS = (math.radians(-118.0), math.radians(-62.0))     # the salvaged plates in it
BANK_A = math.radians(146.0)   # behind him on his right (-X)
CRATE_A = math.radians(46.0)   # behind him on his left (+X)
FLAG_A = math.radians(100.0)   # behind him (its cloth hangs out toward his right, facing the front)
SOCK_A = math.radians(124.0)   # the battery cable's socket in the step's rim
B = dict(BASE=0, BLACK=5, AMB=6, WHITE=7, ALT=8, GUN=9, STEEL=10, GLASS=11, RUBBER=12, HAZ=13)
BAG = (0.15, 0.085, 0.05)      # a sandbag's half length, depth, height


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


# ======================================================================================= the floor and the step
def ground_field():
    """The data center's floor: dark raised-floor tiles (0) with joints (5), every few a perforated vent tile (black dots),
    a cable trench across the back (black, a gunmetal lip 9), scuffs; rounded at its edge."""
    fd = Field("Ground")
    def disc(P):
        r = _rr(P)
        dx = r - F(GROUND_R)
        dz = np.maximum(P[:, 2] - F(GROUND_TOP), F(-0.12) - P[:, 2])
        q0, q1 = dx + F(0.03), dz + F(0.03)
        return np.minimum(np.maximum(q0, q1), F(0)) + np.sqrt(np.maximum(q0, 0) ** 2 + np.maximum(q1, 0) ** 2) - F(0.03)
    lo, hi = (-GROUND_R - 0.05, -GROUND_R - 0.05, -0.2), (GROUND_R + 0.05, GROUND_R + 0.05, 0.12)
    fd.add(Func(disc, lo, hi, disp=lambda P: F(0.0006) * NOISE(P * F(40)), disp_amp=0.001), 0.0)
    cell = 0.6
    def joints(P):
        c = F(cell)
        gx = np.abs(((P[:, 0] + F(10.2)) % c) - c / 2)
        gy = np.abs(((P[:, 1] + F(10.2)) % c) - c / 2)
        return np.maximum(np.minimum(gx, gy) - F(0.004), F(GROUND_TOP - 0.01) - P[:, 2])
    fd.sub(Func(joints, lo, hi), 0.002)
    # perforated vent tiles: a grid of black dots on a few tiles
    def vents(P):
        c = F(cell)
        ix = np.floor((P[:, 0] + F(10.2)) / c)
        iy = np.floor((P[:, 1] + F(10.2)) / c)
        pick = (np.mod(ix * F(3) + iy * F(5), F(4)) == 0)
        hx = np.abs(((P[:, 0] + F(10.2)) % F(0.04)) - F(0.02))
        hy = np.abs(((P[:, 1] + F(10.2)) % F(0.04)) - F(0.02))
        inner = np.maximum(np.abs(((P[:, 0] + F(10.2)) % c) - c / 2), np.abs(((P[:, 1] + F(10.2)) % c) - c / 2)) - F(cell / 2 - 0.05)
        d = np.sqrt(hx * hx + hy * hy) - F(0.008)
        return np.where(pick, np.maximum(np.maximum(d, inner), F(GROUND_TOP - 0.01) - P[:, 2]), F(1.0))
    fd.paint(Func(vents, lo, hi), B["BLACK"])
    # a cable trench across the back, behind the step
    def trench(P):
        return np.maximum(np.maximum(np.abs(P[:, 1] - F(1.17)) - F(0.05), np.abs(P[:, 0]) - F(0.7)), F(GROUND_TOP - 0.005) - P[:, 2])
    fd.paint(Func(trench, lo, hi), B["BLACK"])
    def lip(P):
        return np.maximum(np.maximum(np.abs(np.abs(P[:, 1] - F(1.17)) - F(0.055)) - F(0.008), np.abs(P[:, 0]) - F(0.7)), F(GROUND_TOP - 0.005) - P[:, 2])
    fd.paint(Func(lip, lo, hi), B["GUN"])
    return fd


def plate_field():
    """The firing step: steel bar grating (9) inside a gunmetal-black frame (0) with bolts (10); grooves between the bars
    (5); an amber (6) Resistance slash sprayed across its front; sockets for the marker lamps in the frame."""
    fd = Field("Plate")
    R = PLATE_R + 0.03
    def fn(P):
        r = _rr(P)
        d = np.maximum(P[:, 2] - F(TOP_Z), F(GROUND_TOP - 0.03) - P[:, 2])
        q0, q1 = r - F(PLATE_R) + F(0.02), d + F(0.02)
        return np.minimum(np.maximum(q0, q1), F(0)) + np.sqrt(np.maximum(q0, 0) ** 2 + np.maximum(q1, 0) ** 2) - F(0.02)
    lo, hi = (-R, -R, GROUND_TOP - 0.06), (R, R, TOP_Z + 0.03)
    fd.add(Func(fn, lo, hi, disp=lambda P: F(0.0005) * NOISE(P * F(50)), disp_amp=0.001), 0.0)
    inner = PLATE_R - FRAME_W
    # the grating inside the frame: bars along X, cross rods along Y (grooves between them)
    fd.paint(Func(lambda P: np.maximum(_rr(P) - F(inner), F(TOP_Z - 0.01) - P[:, 2]), lo, hi), B["GUN"])
    def bars(P):
        g = np.abs(((P[:, 1] + F(10.0)) % F(0.05)) - F(0.025)) - F(0.0055)
        return np.maximum(np.maximum(g, _rr(P) - F(inner - 0.012)), np.abs(P[:, 2] - F(TOP_Z)) - F(0.012))
    fd.sub(Func(bars, lo, hi), 0.0015)
    def rods(P):
        g = np.abs(((P[:, 0] + F(10.0)) % F(0.2)) - F(0.1)) - F(0.004)
        return np.maximum(np.maximum(g, _rr(P) - F(inner - 0.012)), np.abs(P[:, 2] - F(TOP_Z)) - F(0.006))
    fd.sub(Func(rods, lo, hi), 0.0015)
    fd.sub(Func(lambda P: np.maximum(np.abs(_rr(P) - F(inner)) - F(0.004), np.abs(P[:, 2] - F(TOP_Z)) - F(0.006)), lo, hi), 0.002)
    for k in range(16):
        a = math.radians(11.25 + 22.5 * k)
        fd.add(Cylinder(ring_pt(a, inner + 0.03, TOP_Z + 0.002), 0.011, 0.008, rr=0.003), 0.002, B["STEEL"])
    # sockets for the marker lamps (in the frame's outer edge)
    for k in range(12):
        a = math.radians(15.0 + 30.0 * k)
        fd.sub(Cylinder(ring_pt(a, LAMP_R, TOP_Z), 0.02, 0.02, rr=0.004), 0.003)
    # the amber Resistance slash sprayed across the grating's front (rough spray edges)
    def slash(P):
        a, b = np.array([-0.32, -0.62], F), np.array([0.3, -0.86], F)
        ab = b - a
        t = np.clip(((P[:, :2] - a) @ ab) / F(ab @ ab), 0, 1)
        q = P[:, :2] - (a + t[:, None] * ab)
        w = F(0.06) + F(0.03) * t + F(0.006) * NOISE(P * F(30))
        return np.maximum(np.sqrt((q * q).sum(1)) - w, F(TOP_Z - 0.012) - P[:, 2])
    fd.paint(Func(slash, lo, hi), B["AMB"])
    return fd


def rim_field():
    """The amber marker lamps round the step's rim (shipped glowing)."""
    fd = Field("Rim")
    for k in range(12):
        a = math.radians(15.0 + 30.0 * k)
        fd.add(Cylinder(ring_pt(a, LAMP_R, TOP_Z - 0.004), 0.016, 0.014, rr=0.006), 0.0)
    return fd


# ======================================================================================= the sandbag wall and its plates
def bag_specs():
    rs = np.random.RandomState(31)
    out = []
    a0, a1 = WALL_A
    for course, (rr, n) in enumerate(((PROP_R + 0.02, 11), (PROP_R + 0.025, 10))):
        for k in range(n):
            t = (k + 0.5 * course + 0.25) / float(n)
            a = a0 + (a1 - a0) * t
            if any(abs(a - pa) < math.radians(10.0) for pa in PLATE_AS) and course == 1:
                continue
            z = GROUND_TOP + BAG[2] * 0.9 + course * (2 * BAG[2] * 0.82) + rs.uniform(-0.004, 0.006)
            c = v3((math.cos(a) * (rr + rs.uniform(-0.012, 0.012)), math.sin(a) * (rr + rs.uniform(-0.012, 0.012)), z))
            yaw = a + math.pi / 2 + rs.uniform(-0.08, 0.08)
            h = (BAG[0] * rs.uniform(0.92, 1.04), BAG[1] * rs.uniform(0.92, 1.05), BAG[2] * rs.uniform(0.9, 1.05))
            out.append((c, yaw, h, int(rs.randint(1 << 20))))
    # the heap at the banner's foot
    o, t, R = frame_at(FLAG_A)
    for j, (dt, dr, zc, yw) in enumerate(((-0.13, 0.0, 0, 0.2), (0.13, 0.02, 0, -0.15), (0.0, -0.1, 0, 1.4), (0.0, 0.03, 1, 0.1))):
        c = o * (1.29 + dr) + t * dt + Z * (GROUND_TOP + BAG[2] * 0.9 + zc * (2 * BAG[2] * 0.82))
        out.append((c, FLAG_A + math.pi / 2 + yw, (BAG[0] * 0.92, BAG[1], BAG[2]), 4000 + j))
    return out


def sandbags_field():
    """Sandbags: canvas (0), each a little different, their tied ends (twine, 6), a stencilled mark on a few (5)."""
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


def salvage_plates_field():
    """Two white (7) robot armour plates set upright in the wall, their faces out: curved, a raised rim, a panel line
    (5), dents, a ragged torn edge, gunmetal (9) bolt stubs; each sprayed with the amber (6) Resistance slash."""
    fd = Field("Plates")
    for j, a in enumerate(PLATE_AS):
        o, t, R = frame_at(a)
        c = o * (PROP_R + 0.02) + Z * (GROUND_TOP + 0.24)
        tilt = euler(0.0, 0.0, 0.0)
        Rp = R @ euler(-0.16, 0.0, 0.0)                     # leaning back a little against the bags
        hw, hh = 0.19, 0.22
        def plate(P, c=c, Rp=Rp):
            q = (P - c.astype(F)) @ Rp.astype(F)
            bow = q[:, 1] - F(0.14) * (q[:, 0] / F(hw)) ** 2 * F(0.3)
            torn = F(0.02) * np.sin(q[:, 0] * F(40) + F(j * 2.0)) + F(0.012) * NOISE(q * F(20))
            ex = np.abs(q[:, 0]) - F(hw)
            ez = np.maximum(-q[:, 2] - F(hh), q[:, 2] - F(hh) + torn)
            ey = np.abs(bow) - F(0.018)
            r = F(0.012)
            w0, w1, w2 = ex + r, ez + r, ey + r
            m = np.stack([w0, w1, w2], 1)
            return np.sqrt((np.maximum(m, 0) ** 2).sum(1)) + np.minimum(m.max(1), 0) - r
        fd.add(Func(plate, c - 0.4, c + 0.4, disp=lambda P: F(0.0004) * NOISE(P * F(40)), disp_amp=0.001), 0.0, B["WHITE"])
        face = c - Rp @ v3((0, 0.02, 0))
        # a panel line, dents
        fd.sub(RoundBox(face + Rp @ v3((0.0, 0.0, -0.08)), (hw - 0.03, 0.006, 0.003), 0.002, R=Rp), 0.002)
        for (u, w) in ((-0.08, 0.06), (0.1, -0.12)):
            fd.sub(Sphere(face + Rp @ v3((u, -0.022, w)), 0.03), 0.008)
        for (u, w) in ((-hw + 0.03, -hh + 0.04), (hw - 0.03, -hh + 0.04), (-hw + 0.03, hh - 0.08), (hw - 0.03, hh - 0.08)):
            fd.add(Cylinder(face + Rp @ v3((u, -0.004, w)), 0.012, 0.012, rr=0.003, R=rot_from_axes(z_axis=Rp @ v3((0, 1, 0)))), 0.002, B["GUN"])
        def slash(P, face=face, Rp=Rp):
            q = (P - face.astype(F)) @ Rp.astype(F)
            d = np.abs(q[:, 0] * F(0.55) + q[:, 2] * F(0.83)) - F(0.045) - F(0.006) * NOISE(P * F(30))
            return np.maximum(d, q[:, 1] - F(0.0))
        fd.paint(Func(slash, c - 0.4, c + 0.4), B["AMB"])
        stencil(fd, "ARC-%d" % (j + 7), face + Rp @ v3((0.0, -0.022, -0.15)), Rp @ v3((-1, 0, 0)), Rp @ v3((0, 0, 1)), 0.026,
                B["BLACK"], depth=0.008)
    return fd


# ======================================================================================= the battery bank
BOX_HALF = (0.075, 0.1, 0.13)     # a battery box: along the ring, radial, height (half)


def bank_frame():
    o, t, R = frame_at(BANK_A)
    return o * (PROP_R + 0.03) + Z * GROUND_TOP, o, t, R


def bank_field():
    """The field battery bank: a gunmetal (9) skid, three charcoal (8) battery boxes side by side with black (5) lids,
    fat steel (10) terminals with amber (6) and black caps, carry handles, white stencils (7); the jumper cables between
    them (12)."""
    fd = Field("Bank")
    f0, o, t, R = bank_frame()
    hx, hy, hz = BOX_HALF
    fd.add(RoundBox(f0 + Z * 0.016, (3 * hx + 0.05, hy + 0.03, 0.016), 0.008, R=R), 0.0, B["GUN"])
    for s in (-1, 1):
        fd.add(RoundBox(f0 + Z * 0.016 + o * (s * (hy + 0.02)), (3 * hx + 0.06, 0.014, 0.024), 0.008, R=R), 0.004, B["GUN"])
    for k in (-1, 0, 1):
        c = f0 + t * (k * (2 * hx + 0.012)) + Z * (0.032 + hz)
        fd.add(RoundBox(c, (hx, hy, hz), 0.016, R=R), 0.006, B["ALT"])
        fd.add(RoundBox(c + Z * (hz - 0.004), (hx + 0.004, hy + 0.004, 0.016), 0.01, R=R), 0.004, B["BLACK"])
        for k2 in range(3):                                                    # ribs on the faces
            fd.add(RoundBox(c - o * hy + Z * (-0.08 + 0.05 * k2), (hx - 0.012, 0.006, 0.008), 0.004, R=R), 0.002, B["ALT"])
        for s, lab in ((-1, B["AMB"]), (1, B["BLACK"])):
            tp = c + Z * (hz + 0.012) + o * (s * 0.045)
            fd.add(Cylinder(tp + Z * 0.016, 0.017, 0.03, rr=0.005), 0.003, B["STEEL"])
            fd.add(Cylinder(tp + Z * 0.036, 0.021, 0.012, rr=0.005), 0.003, lab)
        fd.add(Torus(c + Z * (hz + 0.03), 0.04, 0.007, R=rot_from_axes(z_axis=o)), 0.002, B["BLACK"])
        stencil(fd, "PWR", c - o * (hy + 0.006) + Z * 0.04, -t, Z, 0.03, B["WHITE"], depth=0.01)
    for k in (-1, 0):                                                          # jumpers between the boxes
        a = f0 + t * (k * (2 * hx + 0.012) + 0.0) + Z * (0.032 + 2 * hz + 0.05) + o * 0.045
        b = f0 + t * ((k + 1) * (2 * hx + 0.012)) + Z * (0.032 + 2 * hz + 0.05) - o * 0.045
        m = (a + b) / 2 + Z * 0.05
        fd.add(Chain([a, m, b], [0.011] * 3, k=0.01), 0.004, B["RUBBER"])
    return fd


def cable_pts():
    """The bank's cable to the socket in the step's rim (along the floor)."""
    f0, o, t, R = bank_frame()
    hx, hy, hz = BOX_HALF
    a0 = f0 + t * -(2 * hx + 0.012) + Z * (0.032 + 2 * hz + 0.05) - o * 0.045
    so = ring_pt(SOCK_A, PLATE_R + 0.03, GROUND_TOP + 0.014)
    a1 = f0 + t * -(3 * hx + 0.05) - o * 0.03 + Z * 0.05
    mid = ring_pt(0.5 * (BANK_A + SOCK_A) - 0.04, PLATE_R + 0.06, GROUND_TOP + 0.014)
    return [a0, a0 - t * 0.06 + Z * 0.0, a1, mid, so]


def cables_field():
    """The bank's black rubber cable (12) along the floor; the socket in the step's rim (gunmetal 9, an amber collar 6)."""
    fd = Field("Cables")
    pts = cable_pts()
    fd.add(Chain(pts, [0.017] * len(pts), k=0.03), 0.0, B["RUBBER"])
    so = ring_pt(SOCK_A, PLATE_R + 0.012, GROUND_TOP + 0.022)
    o, t, R = frame_at(SOCK_A)
    fd.add(RoundBox(so, (0.05, 0.03, 0.032), 0.01, R=R), 0.006, B["GUN"])
    fd.add(Cylinder(so + o * 0.03, 0.024, 0.03, rr=0.006, R=rot_from_axes(z_axis=o)), 0.004, B["AMB"])
    return fd


# ======================================================================================= the crate
def crate_frame():
    o, t, R = frame_at(CRATE_A)
    return o * (PROP_R + 0.03) + Z * GROUND_TOP, o, t, R


def crate_field():
    """A supply crate: charcoal (8) panels with gunmetal (9) corner guards and edges, black (5) handles, an amber (6)
    stencilled slash and code; on it an ammo box (gunmetal-black 0, a black latch, a white stencil 7)."""
    fd = Field("Crate")
    f0, o, t, R = crate_frame()
    R2 = R @ euler(0, 0, 0.12)
    hx, hy, hz = 0.19, 0.14, 0.15
    c = f0 + Z * hz
    fd.add(RoundBox(c, (hx, hy, hz), 0.012, R=R2), 0.0, B["ALT"])
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(RoundBox(c + R2 @ v3((sx * (hx - 0.012), sy * (hy - 0.012), 0)), (0.022, 0.022, hz + 0.005), 0.006, R=R2), 0.003, B["GUN"])
    for sz in (-1, 1):
        fd.add(RoundBox(c + Z * (sz * (hz - 0.012)), (hx + 0.004, hy + 0.004, 0.012), 0.006, R=R2), 0.003, B["GUN"])
    for sx in (-1, 1):
        fd.add(RoundBox(c + R2 @ v3((sx * (hx + 0.012), 0.0, 0.05)), (0.008, 0.05, 0.012), 0.004, R=R2), 0.002, B["BLACK"])
    face = c - R2 @ v3((0, hy, 0))
    def sl(P, face=face):
        q = (P - face.astype(F)) @ R2.astype(F)
        d = np.abs(q[:, 0] * F(0.6) + q[:, 2] * F(0.8)) - F(0.03)
        return np.maximum(np.maximum(d, np.abs(q[:, 0]) - F(0.12)), q[:, 1] - F(0.0))
    fd.paint(Func(sl, c - 0.4, c + 0.4), B["AMB"])
    stencil(fd, "RES-04", face - R2 @ v3((0, 0.004, 0)) + Z * -0.09, -R2 @ v3((1, 0, 0)), Z, 0.026, B["AMB"], depth=0.01)
    # the ammo box on top, turned a little
    R3 = R @ euler(0, 0, -0.35)
    hb = (0.13, 0.07, 0.065)
    cb = c + Z * (hz + hb[2]) + R3 @ v3((0.02, 0.0, 0.0))
    fd.add(RoundBox(cb, hb, 0.01, R=R3), 0.004, B["BASE"])
    fd.add(RoundBox(cb + Z * (hb[2] - 0.004), (hb[0] + 0.004, hb[1] + 0.004, 0.01), 0.006, R=R3), 0.003, B["BASE"])
    fd.add(RoundBox(cb + R3 @ v3((0, -hb[1] - 0.006, 0.03)), (0.026, 0.008, 0.02), 0.004, R=R3), 0.002, B["BLACK"])
    fd.add(Torus(cb + Z * (hb[2] + 0.012), 0.035, 0.007, R=R3 @ rot_from_axes(z_axis=(0, 1, 0))), 0.002, B["BLACK"])
    stencil(fd, "CELLS", cb + R3 @ v3((0.0, -hb[1] - 0.004, -0.02)), R3 @ v3((-1, 0, 0)) * -1.0, Z, 0.022, B["WHITE"], depth=0.008)
    return fd


# ======================================================================================= the banner
def flag_frame():
    o, t, R = frame_at(FLAG_A)
    foot = o * 1.29 + Z * GROUND_TOP
    return foot, o, t, R


POLE_H = 1.95


def banner_field():
    """The banner: a salvaged steel pipe (9, a bent robot-arm strut clamped on as a crossbar 10) planted in the sandbag
    heap; hanging from it a ragged scrap of amber cloth (0) with a charcoal (5) slash, torn and frayed at its foot,
    fluttering out to the side."""
    fd = Field("Banner")
    foot, o, t, R = flag_frame()
    top = foot + Z * POLE_H
    fd.add(RoundCone(foot, top, 0.022, 0.018), 0.0, B["GUN"])
    fd.add(Sphere(top + Z * 0.012, 0.026), 0.006, B["GUN"])
    for zz in (0.5, 1.0):
        fd.add(Cylinder(foot + Z * zz, 0.028, 0.026, rr=0.006), 0.003, B["BLACK"])
    # the crossbar (a bent strut), out to the side (along -t: toward the camera's side)
    bar0, bar1 = top - Z * 0.06, top - Z * 0.06 + t * 0.4 - o * 0.04
    fd.add(RoundCone(bar0, bar1, 0.014, 0.012), 0.004, B["STEEL"])
    fd.add(Cylinder(bar0, 0.026, 0.04, rr=0.006), 0.003, B["BLACK"])
    return fd


def cloth_frame():
    foot, o, t, R = flag_frame()
    top = foot + Z * (POLE_H - 0.06)
    return top, o, t


def flagcloth_field():
    """The amber cloth (0): a ragged rectangle hanging from the crossbar, rippled, its foot torn into tongues; a charcoal
    (5) slash across it and frayed holes."""
    fd = Field("Flag")
    top, o, t, = cloth_frame()
    w, h = 0.42, 0.5
    def cloth(P):
        q = P - top.astype(F)
        u = q @ t.astype(F)                        # along the bar (0 .. w)
        v = -q[:, 2]                               # down from the bar (0 .. h)
        n = q @ (-o).astype(F)                     # off the cloth's plane
        wav = F(0.035) * np.sin(u * F(14) + v * F(4)) * (F(0.4) + v / F(h)) + F(0.012) * np.sin(v * F(11) + u * F(3))
        ragged = F(0.04) * np.abs(np.sin(u * F(26))) + F(0.02) * NOISE(q * F(9))
        inside = np.maximum(np.maximum(-u + F(0.01), u - F(w)), np.maximum(-v + F(0.004), v - F(h) + ragged * (F(0.3) + u / F(w))))
        return np.maximum(inside, np.abs(n - wav) - F(0.006))
    fd.add(Func(cloth, top - 0.8, top + 0.8), 0.0, 0)
    def mark(P):
        q = P - top.astype(F)
        u = q @ t.astype(F)
        v = -q[:, 2]
        return np.abs((u - F(w / 2)) * F(0.7) + (v - F(h * 0.45)) * F(0.7)) - F(0.045) + F(0.006) * NOISE(P * F(30))
    fd.paint(Func(mark, top - 0.8, top + 0.8), 5)
    for (u, v) in ((0.08, 0.38), (0.31, 0.2)):
        fd.sub(Sphere(top + t * u - Z * v, 0.022), 0.004)
    return fd


def lights_field():
    """The props' amber lights (shipped glowing): the battery boxes' charge strips."""
    fd = Field("Lights")
    f0, o, t, R = bank_frame()
    hx, hy, hz = BOX_HALF
    for k in (-1, 0, 1):
        c = f0 + t * (k * (2 * hx + 0.012)) + Z * (0.032 + hz)
        fd.add(RoundBox(c - o * (hy + 0.002) + Z * 0.085, (hx - 0.022, 0.006, 0.009), 0.004, R=R), 0.0)
    return fd


def fields():
    return [("Ground", ground_field(), 0.006), ("Plate", plate_field(), 0.0032), ("Rim", rim_field(), 0.002),
            ("Sandbags", sandbags_field(), 0.0036), ("Plates", salvage_plates_field(), 0.0026), ("Bank", bank_field(), 0.0026),
            ("Cables", cables_field(), 0.0024), ("Crate", crate_field(), 0.0026), ("Banner", banner_field(), 0.0024),
            ("Flag", flagcloth_field(), 0.0024), ("Lights", lights_field(), 0.0016)]


def grass_geometry(seed=0):
    """No grass in the data center."""
    return np.zeros((0, 3)), [], np.zeros((0, 2)), np.zeros((0,))


def flower_geometry(seed=0):
    return []


def is_grass_face(c, n):
    return False


REGION_PARTS = ("Ground", "Plate", "Sandbags", "Plates", "Bank", "Cables", "Crate", "Banner", "Flag")
LOW_TARGETS = {"Ground": 1300, "Plate": 3200, "Rim": 360, "Sandbags": 2800, "Plates": 1200, "Bank": 1700, "Cables": 360,
               "Crate": 1100, "Banner": 360, "Flag": 700, "Lights": 120}
KIT = dict(weave=0.0, black=(0.05, 0.05, 0.06), red=_a.AMBER_PAINT, white=_a.ROBOT_WHITE, gunmetal=_a.GUNMETAL,
           olive=_a.CHARCOAL, coyote=_a.AMBER_PAINT, rubber=(0.07, 0.07, 0.075))
MAT_OVERRIDES = {"Ground": ("modern_kit", dict(KIT, name="HQ_ArcFloor", base=(0.3, 0.31, 0.33), gloss=0.5, black=(0.12, 0.12, 0.13))),
                 "Plate": ("modern_kit", dict(KIT, name="HQ_ArcStep", base=_a.GUNBLACK, gloss=0.5, gunmetal=(0.36, 0.37, 0.4))),
                 "Sandbags": ("sacking", {"name": "HQ_ArcSandbags", "base": (0.46, 0.43, 0.36), "dark": (0.28, 0.26, 0.21),
                                          "stencil": (0.1, 0.1, 0.1)}),
                 "Plates": ("modern_kit", dict(KIT, name="HQ_ArcSalvagePlates", base=_a.ROBOT_WHITE, gloss=0.42)),
                 "Bank": ("modern_kit", dict(KIT, name="HQ_ArcProps", base=_a.GUNBLACK, gloss=0.55)),
                 "Cables": ("modern_kit", dict(KIT, name="HQ_ArcProps", base=_a.GUNBLACK, gloss=0.55)),
                 "Crate": ("modern_kit", dict(KIT, name="HQ_ArcProps", base=_a.GUNBLACK, gloss=0.55)),
                 "Banner": ("modern_kit", dict(KIT, name="HQ_ArcProps", base=_a.GUNBLACK, gloss=0.55)),
                 "Flag": ("modern_kit", dict(KIT, name="HQ_ArcFlag", base=(0.9, 0.55, 0.12), weave=1.0, black=(0.1, 0.1, 0.11)))}
GLOW = {"Rim": (_a.AMBER, 1.1, 0.5), "Lights": (_a.AMBER, 1.1, 0.5)}
FLAME_PIVOT = None
