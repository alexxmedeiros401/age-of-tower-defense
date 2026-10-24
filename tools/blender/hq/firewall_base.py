"""Firewall base: a hacker's nest inside the data center. A round, raised platform of steel floor grates (gunmetal
plates of slotted grating, a seam between the plates, bolts, a black edge with an amber line painted round its top and
an amber light strip set into its side, `GlowRim`); he, his rig and his crates stand on it and sweep out to ~0.9 as the
tower turns. Round it, a lower ring of dark steel floor plates on a plinth (its side banded in amber and black), a cable
trench across it with cables in it. On the ring: behind him on his right a robot server rack pried open (white casing, its
door torn back on one hinge, blade servers pulled half out, dead dark lights, an amber chevron sprayed on its side, cables
spilling out of it over the floor); in front on his left a low wall of sandbags (two courses) with the amber banner scrap
on a bent pole stuck in it; behind him on his left an ammo can with a field radio on it (a whip antenna); in front on his
right an energy drink can and a crushed one; coils of cable behind him. (Distance fields; no grass: it is a data
center.)"""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Inter, Shell, Lock, lerp
import firewall as _c

GROUND_R = 1.3
FLOOR_TOP = 0.1                # the outer ring's top
PAD_R = 0.99                   # the raised platform (he, the rig and the crates sweep out to ~0.9 of it)
TOP_Z = 0.17                   # the platform's top = where he stands
STAND = v3((-_c.YAW_PIVOT[0], -_c.YAW_PIVOT[1], TOP_Z))
Z = v3((0.0, 0.0, 1.0))
PROP_R = 1.15                  # the props' ring
RACK_A = math.radians(138.0)   # the pried-open server rack: behind him, on his right (the camera's left)
BAGS_A = math.radians(-50.0)   # the sandbags: in front on his left
BANNER_A = math.radians(-18.0) # the banner's pole: at the sandbags' right end
RADIO_A = math.radians(58.0)   # the ammo can and radio: behind him on his left
CAN_A = math.radians(-140.0)   # the energy drink: in front on his right
COIL_A = math.radians(98.0)    # cable coils: behind him
TRENCH_A = math.radians(-100.0)  # the cable trench crosses the ring here (in front)
RIM_Z = TOP_Z - 0.034          # the light strip's height on the platform's edge
# labels (mats.modern_kit): 0 base (steel: gunmetal; the sandbags: canvas; the banner: amber cloth), 5 black, 6 red,
# 7 robot white, 8 charcoal, 9 gunmetal, 10 steel, 11 glass, 12 rubber, 13 amber
BASE, BLACK, RED, WHITE, CHAR, GUN, STEEL, GLASS, RUBBER, AMBER = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13


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


def _slots(P, plate=0.33, pitch=0.034, slot=(0.012, 0.05)):
    """< 0 in the grating's slots: rows of short slots in each plate, the rows turned 90 degrees from plate to plate."""
    ix = np.floor(P[:, 0] / F(plate))
    iy = np.floor(P[:, 1] / F(plate))
    flip = np.mod(ix + iy, 2) > 0.5
    u = np.where(flip, P[:, 1], P[:, 0])
    v = np.where(flip, P[:, 0], P[:, 1])
    su = np.abs(np.mod(u, F(pitch)) - F(pitch / 2)) - F(slot[0] / 2)
    sv = np.abs(np.mod(v, F(slot[1] + 0.016)) - F((slot[1] + 0.016) / 2)) - F(slot[1] / 2)
    # keep a solid frame round each plate
    fx = np.abs(np.mod(P[:, 0], F(plate)) - F(plate / 2))
    fy = np.abs(np.mod(P[:, 1], F(plate)) - F(plate / 2))
    frame = np.maximum(fx, fy) - F(plate / 2 - 0.022)
    return np.maximum(np.maximum(su, sv), frame)


def floor_field():
    """The outer ring on its plinth: dark steel floor plates (charcoal 8) with a tread of raised diamonds, seams between
    them, a black chamfered edge (5), its side banded in amber (13) and black; the cable trench across its front (a
    gunmetal channel 9)."""
    fd = Field("Floor")
    h = FLOOR_TOP + 0.1
    fd.add(Cylinder(v3((0, 0, FLOOR_TOP - h / 2)), GROUND_R, h, rr=0.025), 0.0, CHAR)
    lo, hi = (-1.4, -1.4, -0.05), (1.4, 1.4, 0.2)
    def joints(P):
        return np.maximum(np.maximum(_grid(P, 0.4, 0.0024, 0.07, 0.11), np.abs(P[:, 2] - F(FLOOR_TOP)) - F(0.006)), F(PAD_R - 0.02) - _rr(P))
    fd.sub(Func(joints, lo, hi), 0.0015)
    def tread(P):
        a = np.abs(np.mod(P[:, 0] + P[:, 1], F(0.06)) - F(0.03))
        b = np.abs(np.mod(P[:, 0] - P[:, 1], F(0.06)) - F(0.03))
        d = np.maximum(a, b) - F(0.008)
        return np.maximum(np.maximum(d, np.abs(P[:, 2] - F(FLOOR_TOP)) - F(0.0035)), np.maximum(F(PAD_R) - _rr(P), _rr(P) - F(GROUND_R - 0.04)))
    fd.add(Func(tread, lo, hi), 0.001, CHAR)
    side = lambda P: np.maximum(F(GROUND_R - 0.03) - _rr(P), P[:, 2] - F(FLOOR_TOP - 0.025))
    fd.paint(Func(side, lo, hi), BLACK)
    def stripes(P):
        a = np.arctan2(P[:, 1], P[:, 0]) * F(GROUND_R)
        st = np.abs(np.mod(a + P[:, 2] * F(1.0), F(0.12)) - F(0.06)) - F(0.03)
        return np.maximum(np.maximum(st, side(P)), np.maximum(F(-0.07) - P[:, 2], P[:, 2] - F(FLOOR_TOP - 0.035)))
    fd.paint(Func(stripes, lo, hi), AMBER)
    # the cable trench: a channel across the ring at the front
    o, al = ring_frame(TRENCH_A)
    def trench(P):
        q = P[:, :2] @ al[:2].astype(F)
        r = P[:, :2] @ o[:2].astype(F)
        return np.maximum(np.maximum(np.abs(q) - F(0.06), F(PAD_R - 0.03) - r), np.abs(P[:, 2] - F(FLOOR_TOP)) - F(0.03))
    fd.sub(Func(trench, lo, hi), 0.004)
    def lip(P):
        q = P[:, :2] @ al[:2].astype(F)
        r = P[:, :2] @ o[:2].astype(F)
        return np.maximum(np.maximum(np.abs(np.abs(q) - F(0.066)) - F(0.008), F(PAD_R - 0.03) - r), np.abs(P[:, 2] - F(FLOOR_TOP)) - F(0.02))
    fd.paint(Func(lip, lo, hi), GUN)
    return fd


def pad_field():
    """The raised platform: steel grating plates (gunmetal 0) with their slots, solid frames and bolts at their corners,
    an amber line painted round the top's edge (13), its side black (5) with a groove all round for the amber light
    strip."""
    fd = Field("Pad")
    h = TOP_Z - (FLOOR_TOP - 0.02)
    fd.add(Cylinder(v3((0, 0, FLOOR_TOP - h / 2 + 0.0)), PAD_R, h, rr=0.016,
                    disp=lambda P: F(0.0004) * NOISE(P * F(30)), disp_amp=0.0006), 0.0, BASE)
    lo, hi = (-1.05, -1.05, 0.0), (1.05, 1.05, 0.25)
    top = lambda P: np.abs(P[:, 2] - F(TOP_Z)) - F(0.008)
    fd.sub(Func(lambda P: np.maximum(np.maximum(_slots(P), top(P)), _rr(P) - F(PAD_R - 0.09)), lo, hi), 0.001)
    fd.sub(Func(lambda P: np.maximum(np.maximum(_grid(P, 0.33, 0.002, 0.0, 0.0), top(P)), _rr(P) - F(PAD_R - 0.09)), lo, hi), 0.0012)
    for i in range(-3, 4):
        for j in range(-3, 4):
            p = v3((0.33 * i, 0.33 * j, TOP_Z))
            if np.hypot(p[0], p[1]) < PAD_R - 0.12:
                fd.add(Sphere(p + v3((0, 0, -0.002)), 0.011), 0.002, STEEL)
    # the amber line round the top's edge, the black side
    edge = lambda P: np.maximum(np.abs(_rr(P) - F(PAD_R - 0.05)) - F(0.016), F(TOP_Z - 0.02) - P[:, 2])
    fd.paint(Func(edge, lo, hi), AMBER)
    fd.paint(Func(lambda P: np.maximum(F(PAD_R - 0.012) - _rr(P), P[:, 2] - F(TOP_Z - 0.012)), lo, hi), BLACK)
    fd.sub(Torus(v3((0, 0, RIM_Z)), PAD_R + 0.004, 0.011), 0.002)
    return fd


def rim_field():
    """The amber light strip round the platform's edge (shipped glowing)."""
    fd = Field("Rim")
    fd.add(Torus(v3((0, 0, RIM_Z)), PAD_R - 0.0015, 0.0075), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the props
def rack_into(fd):
    """A robot server rack, pried open: a white casing (7) on black feet, its door (white, a black window) torn back on
    its bottom hinge, inside four blade servers (black 5, steel handles 10), two pulled half out, their lights dead (dark
    glass 11); the door wrenched back past its side; an amber chevron sprayed on its side (13); a red tag (6)."""
    out, along = ring_frame(RACK_A)
    c = ring_pt(RACK_A, PROP_R + 0.015)
    g = FLOOR_TOP
    face = -out                                     # its front faces in (toward him and the camera's side)
    acr = norm(np.cross(Z, face))
    R = np.stack([acr, face, Z], axis=1)
    H, W, D = 0.36, 0.18, 0.12                      # half height, half width, half depth
    cc = c + Z * (g + 0.03 + H)
    dents = lambda P: F(0.0005) * NOISE(P * F(45)) - F(0.004) * np.clip(NOISE(P * F(8)) - F(0.4), 0, None)
    fd.add(RoundBox(cc, (W, D, H), 0.02, R=R, disp=dents, disp_amp=0.004), 0.0, WHITE)
    fd.sub(RoundBox(cc + face * 0.02, (W - 0.03, D, H - 0.03), 0.01, R=R), 0.004)          # its open front
    fd.add(RoundBox(cc - face * (D - 0.03), (W - 0.03, 0.01, H - 0.03), 0.006, R=R), 0.002, BLACK)   # the dark inside
    for e in (-1, 1):
        for e2 in (-1, 1):
            fd.add(Cylinder(c + acr * (e * (W - 0.03)) + face * (e2 * (D - 0.03)) + Z * (g + 0.015), 0.018, 0.03, rr=0.006), 0.003, BLACK)
    # blade servers in it, two pulled out
    for k in range(4):
        zz = g + 0.12 + 0.15 * k
        pull = (0.0, 0.04, 0.0, 0.065)[k]
        bc = cc + Z * (zz - (g + 0.03 + H)) + face * (pull - 0.01)
        fd.add(RoundBox(bc, (W - 0.045, D - 0.035, 0.05), 0.008, R=R), 0.004, BLACK)
        fd.add(RoundBox(bc + face * (D - 0.03), (W - 0.06, 0.006, 0.006), 0.003, R=R), 0.002, STEEL)
        for j in range(3):
            fd.add(Sphere(bc + face * (D - 0.034) + acr * (-0.1 + 0.03 * j) + Z * 0.025, 0.007), 0.001, GLASS)
    # the door: wrenched back on its hinge past the rack's side, hanging crooked from its one good hinge
    hinge = cc + face * (D + 0.004) + acr * (W + 0.004)
    ddir = norm(acr * 0.985 + face * 0.17)
    dz = norm(Z + ddir * 0.12)
    dn = norm(np.cross(dz, ddir))
    Rdoor = np.stack([ddir, dn, dz], axis=1)
    dcen = hinge + ddir * (W - 0.005) + Z * 0.012
    fd.add(RoundBox(dcen, (W - 0.01, 0.012, H - 0.02), 0.008, R=Rdoor, disp=dents, disp_amp=0.004), 0.004, WHITE)
    fd.add(RoundBox(dcen + dn * 0.012 + Z * 0.08, (W - 0.06, 0.004, H * 0.45), 0.003, R=Rdoor), 0.002, BLACK)
    for e in (-1, 1):
        fd.add(Cylinder(hinge + Z * (e * (H - 0.08)) , 0.012, 0.05, rr=0.004), 0.003, STEEL)
    # the chevron on its side (the side toward the camera)
    sn = acr if (acr @ v3((0, -1, 0))) > 0 else -acr
    sc = cc + sn * W + Z * 0.06
    sa = norm(np.cross(Z, sn))
    def chev(P):
        q = P - sc.astype(F)
        u, v = q @ sa.astype(F), q @ Z.astype(F)
        return np.maximum(_c.chevron(u, v, w=0.05, arm=0.12) + F(0.006) * NOISE(P * F(50)), np.abs(q @ sn.astype(F)) - F(0.03))
    fd.paint(Func(chev, sc - 0.3, sc + 0.3), AMBER)
    fd.paint(RoundBox(cc + sn * W + Z * (H - 0.07) + sa * 0.08, (0.03, 0.03, 0.02), 0.004, R=rot_from_axes(x_axis=sa, z_axis=Z)), RED)


def rack_cables_into(fd):
    """Cables spilling out of the rack and over the floor onto the platform's edge (black rubber 12, one red 6)."""
    out, along = ring_frame(RACK_A)
    c = ring_pt(RACK_A, PROP_R)
    g = FLOOR_TOP
    for k, (lab, da) in enumerate(((RUBBER, -0.08), (RED, 0.0), (RUBBER, 0.09))):
        p0 = c - out * 0.1 + along * (da * 0.6) + Z * (g + 0.25)
        pts = [p0, p0 - out * 0.08 - Z * 0.12, ring_pt(RACK_A + da, PAD_R + 0.12) + Z * (g + 0.012),
               ring_pt(RACK_A + da - 0.25, PAD_R + 0.04) + Z * (g + 0.012), ring_pt(RACK_A + da - 0.45, PAD_R + 0.08) + Z * (g + 0.012),
               ring_pt(RACK_A + da - 0.7, PAD_R + 0.15) + Z * (g + 0.012)]
        fd.add(Chain(pts, [0.013 if lab != RED else 0.01] * len(pts), k=0.012), 0.003, lab)


def bags_into(fd):
    """A low wall of sandbags (canvas 0), two courses on an arc at the ring's edge, tied ends (black 5)."""
    rs = np.random.RandomState(19)
    o0, _ = ring_frame(BAGS_A)
    for row, (n, r, z, span) in enumerate(((5, PROP_R + 0.02, 0.0, 0.72), (4, PROP_R + 0.03, 0.105, 0.56))):
        for k in range(n):
            a = BAGS_A + span * (k / (n - 1) - 0.5)
            out, along = ring_frame(a)
            p = ring_pt(a, r) + Z * (FLOOR_TOP + 0.058 + z)
            R = np.stack([along, out, Z], axis=1) @ euler(rs.uniform(-0.06, 0.06), rs.uniform(-0.05, 0.05), rs.uniform(-0.1, 0.1))
            lump = lambda P: F(0.006) * NOISE(P * F(14)) + F(0.002) * NOISE(P * F(40))
            fd.add(Ellipsoid(p, (0.125, 0.085, 0.062), R=R, disp=lump, disp_amp=0.008), 0.012, BASE)
            fd.add(Ellipsoid(p + R[:, 0] * 0.12, (0.024, 0.034, 0.026), R=R), 0.008, BASE)                # the tied end
            fd.add(Torus(p + R[:, 0] * 0.103, 0.028, 0.006, R=rot_from_axes(z_axis=R[:, 0])), 0.003, BLACK)


def banner_into(fd):
    """The banner's pole (gunmetal 9, bent a little, a steel cap 10) stuck in the sandbags, a lashing of black cord."""
    p = ring_pt(BANNER_A, PROP_R + 0.06) + Z * FLOOR_TOP
    fd.add(Chain(BANNER_POLE, [0.016, 0.015, 0.014, 0.013], k=0.006), 0.0, GUN)
    fd.add(Sphere(BANNER_POLE[-1] + Z * 0.012, 0.02), 0.004, STEEL)
    fd.add(Torus(BANNER_POLE[0] + Z * 0.05, 0.022, 0.006), 0.003, BLACK)


BANNER_POLE = [ring_pt(BANNER_A, PROP_R + 0.07) + Z * FLOOR_TOP, ring_pt(BANNER_A, PROP_R + 0.075) + Z * (FLOOR_TOP + 0.45),
               ring_pt(BANNER_A + 0.02, PROP_R + 0.09) + Z * (FLOOR_TOP + 0.8), ring_pt(BANNER_A + 0.04, PROP_R + 0.1) + Z * (FLOOR_TOP + 1.08)]


def banner_field():
    """The amber banner scrap (amber cloth 0 in the banner's material): a ragged strip hanging from the pole's top, its
    fly torn into tails, a black chevron painted on it (5), a darker scorched edge (8)."""
    fd = Field("Banner")
    top = BANNER_POLE[-1] - Z * 0.03
    out, along = ring_frame(BANNER_A)
    hang = norm(along * -1.0 + out * -0.35)                 # it hangs off the pole toward the camera's side
    n = norm(np.cross(hang, Z))
    W, H = 0.3, 0.46
    wave = lambda P: F(0.012) * np.sin(((P - top.astype(F)) @ hang.astype(F)) * F(22) + P[:, 2] * F(6)) + F(0.002) * NOISE(P * F(30))
    def cloth(P):
        q = P - top.astype(F)
        u = q @ hang.astype(F)
        v = -(q @ Z.astype(F))
        w = q @ n.astype(F)
        tails = F(0.05) * np.clip(np.sin(u * F(38)), 0, 1)               # its lower edge torn into tails
        rag = F(0.012) * NOISE(P * F(25))
        return np.maximum(np.maximum(np.abs(w - wave(P)) - F(0.006), np.maximum(-u, u - F(W) - rag)),
                          np.maximum(-v + F(0.0), v - F(H) + tails * smoothstep(0.05, 0.2, u) - rag))
    lo, hi = top - 0.45, top + 0.45
    fd.add(Func(cloth, lo, hi), 0.0, BASE)
    fd.add(Chain([top - hang * 0.0, top + hang * W], [0.012, 0.01], k=0.004), 0.006, BASE)          # its hem round the pole's arm
    cc = top + hang * (W * 0.5) - Z * 0.18
    def chev(P):
        q = P - cc.astype(F)
        return np.maximum(_c.chevron(q @ hang.astype(F), q @ Z.astype(F), w=0.044, arm=0.11), np.abs(q @ n.astype(F)) - F(0.04))
    fd.paint(Func(chev, cc - 0.3, cc + 0.3), BLACK)
    def scorch(P):
        q = P - top.astype(F)
        u = q @ hang.astype(F)
        return np.maximum(F(W - 0.035) - u + F(0.02) * NOISE(P * F(20)), np.abs(q @ n.astype(F)) - F(0.05))
    fd.paint(Func(scorch, lo, hi), CHAR)
    return fd


def radio_into(fd):
    """An ammo can (teal-grey 8 here: charcoal) with a field radio on it (black 5, a steel dial 10, an amber stripe 13),
    its whip antenna (black) and a coiled handset cord."""
    out, along = ring_frame(RADIO_A)
    c = ring_pt(RADIO_A, PROP_R + 0.0)
    g = FLOOR_TOP
    R = np.stack([along, out, Z], axis=1) @ euler(0, 0, 0.2)
    fd.add(RoundBox(c + Z * (g + 0.1), (0.13, 0.08, 0.1), 0.012, R=R), 0.0, CHAR)
    fd.add(RoundBox(c + Z * (g + 0.2), (0.135, 0.085, 0.012), 0.008, R=R), 0.003, CHAR)
    fd.add(Chain([c + R @ v3((-0.05, 0, 0.215)) + Z * g, c + R @ v3((0, 0, 0.245)) + Z * g, c + R @ v3((0.05, 0, 0.215)) + Z * g], [0.008] * 3, k=0.004), 0.003, BLACK)
    rc = c + Z * (g + 0.27) + R @ v3((0.0, 0.0, 0.0))
    fd.add(RoundBox(rc, (0.1, 0.06, 0.055), 0.012, R=R), 0.004, BLACK)
    face = -R[:, 1]
    fd.add(Cylinder(rc + face * 0.06 + R[:, 0] * 0.04, 0.02, 0.014, rr=0.004, R=rot_from_axes(z_axis=face)), 0.003, STEEL)
    fd.add(Cylinder(rc + face * 0.06 - R[:, 0] * 0.03 + Z * 0.015, 0.012, 0.012, rr=0.003, R=rot_from_axes(z_axis=face)), 0.003, STEEL)
    fd.paint(RoundBox(rc + face * 0.06 - Z * 0.03, (0.09, 0.02, 0.01), 0.003, R=R), AMBER)
    ant = rc + R[:, 0] * 0.08 + Z * 0.05
    fd.add(RoundCone(ant, ant + v3((0.02, 0.03, 0.42)), 0.007, 0.004), 0.003, BLACK)
    fd.add(Sphere(ant + v3((0.02, 0.03, 0.42)), 0.008), 0.002, BLACK)


def drinks_into(fd):
    """An energy drink can standing on the ring (teal-grey 8 with an amber band 13 and a black stripe 5, steel top 10),
    a crushed one lying beside it."""
    c = ring_pt(CAN_A, PROP_R + 0.02)
    g = FLOOR_TOP
    fd.add(Cylinder(c + Z * (g + 0.065), 0.034, 0.13, rr=0.01), 0.0, CHAR)
    fd.add(Cylinder(c + Z * (g + 0.128), 0.028, 0.008, rr=0.003), 0.002, STEEL)
    fd.paint(Cylinder(c + Z * (g + 0.07), 0.04, 0.05), AMBER)
    fd.paint(Cylinder(c + Z * (g + 0.07), 0.04, 0.012), BLACK)
    out, along = ring_frame(CAN_A)
    c2 = c + along * 0.1 - out * 0.03 + Z * (g + 0.024)
    R = rot_from_axes(z_axis=along) @ euler(0, 0, 0.4)
    crush = lambda P: F(0.006) * NOISE(P * F(30))
    fd.add(Cylinder(c2, 0.028, 0.07, rr=0.008, R=R @ np.diag([1.0, 0.7, 1.0]), disp=crush, disp_amp=0.008), 0.004, CHAR)
    fd.paint(Sphere(c2, 0.03), AMBER)


def coils_into(fd):
    """Coils of cable on the floor behind him (black rubber 12), and one amber-taped cable over to the platform."""
    for a, r0, n in ((COIL_A, 0.11, 3), (COIL_A + 0.32, 0.08, 2)):
        c = ring_pt(a, PROP_R + 0.02) + Z * (FLOOR_TOP + 0.012)
        for k in range(n):
            fd.add(Torus(c + Z * (0.02 * k), r0 - 0.008 * k, 0.012), 0.006, RUBBER)
    c = ring_pt(COIL_A, PROP_R + 0.02)
    pts = [c + Z * (FLOOR_TOP + 0.05), ring_pt(COIL_A - 0.1, PAD_R + 0.08) + Z * (FLOOR_TOP + 0.012),
           ring_pt(COIL_A - 0.25, PAD_R + 0.03) + Z * (FLOOR_TOP + 0.012)]
    fd.add(Chain(pts, [0.012] * 3, k=0.01), 0.004, RUBBER)
    fd.add(Torus(pts[1] + Z * 0.004, 0.02, 0.007, R=rot_from_axes(z_axis=norm(pts[2] - pts[0]))), 0.003, AMBER)
    # cables lying in the trench
    o, al = ring_frame(TRENCH_A)
    for k, (lab, off) in enumerate(((RUBBER, -0.025), (RUBBER, 0.0), (RED, 0.026))):
        pts = [ring_pt(TRENCH_A, PAD_R + 0.0) + al * off + Z * (FLOOR_TOP - 0.01),
               ring_pt(TRENCH_A, (PAD_R + GROUND_R) / 2) + al * (off * 1.1) + Z * (FLOOR_TOP - 0.016),
               ring_pt(TRENCH_A, GROUND_R - 0.01) + al * off + Z * (FLOOR_TOP - 0.012)]
        fd.add(Chain(pts, [0.011] * 3, k=0.008), 0.003, lab)


def _part(name, *fns):
    fd = Field(name)
    for fn in fns:
        fn(fd)
    return fd


def fields():
    """Each prop is its own part (small meshing grids); all are baked into the one atlas."""
    return [("Floor", floor_field(), 0.006), ("Pad", pad_field(), 0.0035), ("Rim", rim_field(), 0.003),
            ("Rack", _part("Rack", rack_into), 0.0024), ("Wires", _part("Wires", rack_cables_into, coils_into), 0.0028),
            ("Bags", _part("Bags", bags_into), 0.003), ("Pole", _part("Pole", banner_into), 0.0024),
            ("Banner", banner_field(), 0.0024), ("Radio", _part("Radio", radio_into), 0.0022),
            ("Drinks", _part("Drinks", drinks_into), 0.0018)]


def grass_geometry(seed=0):
    """No grass in a data center."""
    return np.zeros((0, 3)), [], np.zeros((0, 2)), np.zeros(0, int)


def flower_geometry(seed=0):
    return []


REGION_PARTS = ("Floor", "Pad", "Rack", "Wires", "Bags", "Pole", "Banner", "Radio", "Drinks")
LOW_TARGETS = {"Floor": 1800, "Pad": 3200, "Rim": 400, "Rack": 2200, "Wires": 1100, "Bags": 1800, "Pole": 200,
               "Banner": 500, "Radio": 900, "Drinks": 400}
STEEL_KIT = {"base": _c.GUNMETAL_C, "weave": 0.0, "black": (0.05, 0.05, 0.06), "red": (0.7, 0.12, 0.08),
             "white": _c.ROBOT_W, "olive": _c.CHARCOAL_C, "gunmetal": (0.2, 0.21, 0.23), "steel": (0.62, 0.64, 0.68),
             "glass": (0.04, 0.045, 0.05), "rubber": (0.08, 0.08, 0.09), "coyote": _c.AMBER_C, "gloss": 0.5}
KIT = dict(STEEL_KIT, olive=_c.TEAL_C)
CANVAS = dict(STEEL_KIT, base=(0.34, 0.36, 0.33), weave=1.0)
BANNER = dict(STEEL_KIT, base=_c.AMBER_C, weave=1.0, olive=(0.36, 0.2, 0.06))
MAT_OVERRIDES = {"Floor": ("modern_kit", dict(STEEL_KIT, name="HQ_FirewallFloor")),
                 "Pad": ("modern_kit", dict(STEEL_KIT, name="HQ_FirewallFloor")),
                 "Rack": ("modern_kit", dict(KIT, name="HQ_FirewallNestKit")),
                 "Wires": ("modern_kit", dict(KIT, name="HQ_FirewallNestKit")),
                 "Pole": ("modern_kit", dict(KIT, name="HQ_FirewallNestKit")),
                 "Radio": ("modern_kit", dict(KIT, name="HQ_FirewallNestKit")),
                 "Drinks": ("modern_kit", dict(KIT, name="HQ_FirewallNestKit")),
                 "Bags": ("modern_kit", dict(CANVAS, name="HQ_FirewallSandbags")),
                 "Banner": ("modern_kit", dict(BANNER, name="HQ_FirewallBanner")),
                 "Rim": ("glow_ball", {"name": "HQ_FirewallRim", "col": _c.GLOW_A, "strength": 0.9})}
GLOW = {"Rim": (_c.GLOW_A, 0.9, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
