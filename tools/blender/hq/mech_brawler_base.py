"""The Mech Brawler's base: its bay on the corps' hangar floor. A round deck of dark steel floor plates (seams, bolt
heads at their corners, worn bright scuffs and dents where its fists slam down before it, black scorch marks), a band of
yellow-and-black hazard chevrons round it, a gunmetal kerb with a glowing violet strip in its top (its own emissive
mesh, `GlowRim`, with the charging post's status lamps); round the kerb an apron of dark poured concrete with oil
stains and a few dry weeds at its edge. On the apron, behind it, the charging post (a squat gunmetal pylon, hazard
band, a status panel) with the thick black umbilical cable running out of it over the kerb and across the deck to its
plug; behind it on its left a tool cart (two trays, a drawer unit, a big wrench, a driver, a spare cell); behind it on
its right a spare knuckle guard for its fists on a low A-frame rack; before it on its right a black hard case with yellow
latches.

Everything on the deck lies flush (the cable is the only thing proud of the plates, 6 cm); every prop stands on the
apron beyond r = 1.04: the fists sweep out to r ~ 1.0 as the tower turns, and the slam drives them into the deck
0.85-1.0 out."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Inter, Shell, Lock, lerp
import base as _b

GROUND_R = 1.32
GROUND_TOP = 0.12
TOP_Z = 0.2                        # the deck's top = where it stands
STAND = v3((0.0, 0.0, TOP_Z))
DECK_R = 1.0
BAND = (0.84, 0.96)                # the hazard band
KERB = (0.995, 1.06)
KERB_TOP = TOP_Z + 0.018
STRIP_R = 1.027
# modern_kit labels
BASE, BLACK, VIOLET, WHITE, NAVY, GUN, STEEL, GLASS, RUBBER, HAZARD = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13
OIL = 7                            # field_concrete: oil stains


def _polar(deg, r, z=GROUND_TOP):
    return v3((r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)), z))


POST_A, CART_A, RACK_A, CASE_A = 92.0, 30.0, 152.0, 218.0      # degrees round from its left (90 = behind it)
PROP_R = 1.15


def ground_height(x, y):
    return GROUND_TOP


def _frame(deg, r):
    """A prop's frame on the apron: its foot centre, t (along the ring, counter-clockwise), n (out from the middle)."""
    c = _polar(deg, r)
    n = v3((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0.0))
    t = v3((-n[1], n[0], 0.0))
    return c, t, n


def ground_field():
    """The apron of dark poured concrete (field_concrete): oil stains (7), a seam ring."""
    fd = Field("Ground")

    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.012) * np.sin(a * 7 + 0.4) + F(0.008) * NOISE(P * F(3))
        dx = r - R
        dz = np.maximum(P[:, 2] - F(GROUND_TOP), F(-0.14) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.05), 0), np.maximum(dz + F(0.05), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.05), dz + F(0.05)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.05)
    fd.add(Func(disc, (-1.5, -1.5, -0.2), (1.5, 1.5, 0.2), disp=lambda P: F(0.002) * NOISE(P * F(9)), disp_amp=0.003), 0.0)
    # chips out of its edge
    rs = np.random.RandomState(12)
    for k in range(9):
        a = rs.uniform(0, 2 * math.pi)
        fd.sub(Sphere(_polar(math.degrees(a), GROUND_R + 0.02, GROUND_TOP + 0.01), rs.uniform(0.03, 0.05)), 0.01)
    # oil stains round the props and under the cart
    lo, hi = (-1.5, -1.5, -0.2), (1.5, 1.5, 0.2)
    for deg, r, s in ((CART_A + 6, 1.16, 0.12), (POST_A - 14, 1.2, 0.08), (250.0, 1.2, 0.07), (330.0, 1.17, 0.09)):
        c = _polar(deg, r)
        fd.paint(Func(lambda P, c=c, s=s: np.sqrt(((P[:, :2] - c[:2].astype(F)) ** 2).sum(1)) - F(s) + F(0.025) * NOISE(P * F(12)), lo, hi), OIL)
    return fd


def _seam_d(P):
    """Distance to the deck plates' seams: a square grid 0.33 apart, two rings."""
    x, y = P[:, 0], P[:, 1]
    g = F(0.33)
    dx = np.abs(x / g - np.round(x / g)) * g
    dy = np.abs(y / g - np.round(y / g)) * g
    r = np.sqrt(x * x + y * y)
    inner = np.where(r < F(BAND[0]), np.minimum(dx, dy), F(1.0))
    rings = np.minimum(np.abs(r - F(BAND[0])), np.abs(r - F(BAND[1])))
    return np.minimum(inner, rings)


def deck_field():
    """The steel deck (modern_kit: 0 deck grey), seams and bolt heads, the hazard chevrons (13 yellow, 5 black), scuffs
    worn bright (10) and dents before it, black scorch marks (5), a white bay number (7)."""
    fd = Field("Deck")
    tex = lambda P: F(0.0006) * NOISE(P * F(40))
    fd.add(Cylinder(v3((0, 0, (TOP_Z + GROUND_TOP - 0.06) / 2)), DECK_R + 0.002, TOP_Z - GROUND_TOP + 0.06, rr=0.008, disp=tex, disp_amp=0.001), 0.0, BASE)
    lo, hi = (-1.1, -1.1, GROUND_TOP - 0.1), (1.1, 1.1, TOP_Z + 0.03)
    fd.sub(Func(lambda P: np.maximum(_seam_d(P) - F(0.0045), np.abs(P[:, 2] - F(TOP_Z)) - F(0.006)), lo, hi), 0.002)
    # bolt heads at the plates' corners
    g = 0.33
    for i in range(-3, 4):
        for j in range(-3, 4):
            for ox, oy in ((0.035, 0.035), (-0.035, 0.035), (0.035, -0.035), (-0.035, -0.035)):
                x, y = i * g + ox, j * g + oy
                if math.hypot(x, y) < BAND[0] - 0.03 and abs(x) > 0.42 or (math.hypot(x, y) < BAND[0] - 0.03 and abs(y) > 0.42):
                    fd.add(Cylinder(v3((x, y, TOP_Z + 0.002)), 0.011, 0.008, rr=0.003), 0.002, STEEL)
    # the hazard chevrons: diagonal yellow and black stripes round the band
    def chev(P, odd):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        s = a * F(BAND[1]) / F(0.07) + (r - F(BAND[0])) / F(0.07) * F(1.0)
        ph = np.abs(s - np.floor(s) - F(0.5))
        inband = np.maximum(F(BAND[0] + 0.012) - r, r - F(BAND[1] - 0.012))
        stripe = (F(0.25) - ph) * F(0.07) if odd else (ph - F(0.25)) * F(0.07)
        return np.maximum(inband, -stripe)
    fd.paint(Func(lambda P: chev(P, False), lo, hi), HAZARD)
    fd.paint(Func(lambda P: chev(P, True), lo, hi), BLACK)
    # where its fists slam down before it: dents, and scuffs worn bright round them
    for sx in (-1, 1):
        c = v3((sx * 0.3, -0.88, TOP_Z))
        fd.sub(Ellipsoid(c + v3((0, 0, 0.012)), (0.11, 0.075, 0.018)), 0.006)
        fd.paint(Func(lambda P, c=c: np.abs(np.sqrt(((P[:, :2] - c[:2].astype(F)) ** 2).sum(1)) - F(0.12)) - F(0.025) + F(0.02) * NOISE(P * F(30)),
                      c - 0.3, c + 0.3), STEEL)
    # scuffs where its feet turn, scorch marks
    for sx in (-1, 1):
        c = v3((sx * 0.3, 0.0, TOP_Z))
        fd.paint(Func(lambda P, c=c: np.abs(np.sqrt(((P[:, :2] - c[:2].astype(F)) ** 2).sum(1)) - F(0.3)) - F(0.012) + F(0.012) * NOISE(P * F(25)),
                      c - 0.4, c + 0.4), STEEL)
    for c, s in (((0.55, 0.42), 0.11), ((-0.6, 0.3), 0.08), ((-0.15, 0.62), 0.07), ((0.62, -0.38), 0.06)):
        cc = v3((c[0], c[1], TOP_Z))
        fd.paint(Func(lambda P, cc=cc, s=s: np.sqrt(((P[:, :2] - cc[:2].astype(F)) ** 2).sum(1)) - F(s) + F(0.03) * NOISE(P * F(14)),
                      cc - 0.3, cc + 0.3), BLACK)
    # the bay number behind it ("07": blocks)
    c = v3((0.0, 0.66, TOP_Z))
    fd.paint(Torus(c + v3((-0.05, 0, 0)), 0.04, 0.011), WHITE)
    fd.paint(Chain([c + v3((0.02, 0.045, 0)), c + v3((0.085, 0.045, 0)), c + v3((0.035, -0.045, 0))], [0.011] * 3), WHITE)
    return fd


def kerb_field():
    """The gunmetal kerb round the deck (modern_kit 9), the channel in its top for the light strip, bolts."""
    fd = Field("Kerb")
    hz = (KERB_TOP - GROUND_TOP + 0.04) / 2

    def ring(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        dr = np.abs(r - F((KERB[0] + KERB[1]) / 2)) - F((KERB[1] - KERB[0]) / 2)
        dz = np.abs(P[:, 2] - F(KERB_TOP - hz)) - F(hz)
        q = np.stack([np.maximum(dr + F(0.012), 0), np.maximum(dz + F(0.012), 0)], 1)
        return np.minimum(np.maximum(dr, dz) + F(0.012), 0) + np.sqrt((q ** 2).sum(1)) - F(0.012)
    fd.add(Func(ring, (-1.15, -1.15, GROUND_TOP - 0.06), (1.15, 1.15, KERB_TOP + 0.01)), 0.0, GUN)
    fd.sub(Torus(v3((0, 0, KERB_TOP + 0.002)), STRIP_R, 0.016), 0.004)
    for k in range(24):
        a = 2 * math.pi * (k + 0.5) / 24
        fd.add(Cylinder(v3((math.cos(a) * (KERB[1] - 0.012), math.sin(a) * (KERB[1] - 0.012), KERB_TOP)), 0.008, 0.008, rr=0.003), 0.002, STEEL)
    return fd


# ---------------------------------------------------------------------------------------------- the charging post, the cable
def post_frame():
    return _frame(POST_A, PROP_R + 0.02)


def post_field():
    """A squat gunmetal pylon (9) with a hazard band (13 / 5), a black status panel, its cable socket; a white stencil."""
    fd = Field("Post")
    c, t, n = post_frame()
    R = np.stack([t, n, v3((0, 0, 1))], axis=1)
    up = v3((0, 0, 1))
    fd.add(RoundBox(c + up * 0.02, (0.13, 0.1, 0.02), 0.012, R=R), 0.0, GUN)
    fd.add(RoundBox(c + up * 0.28, (0.1, 0.08, 0.26), 0.03, R=R), 0.01, GUN)
    fd.add(RoundBox(c + up * 0.54, (0.11, 0.09, 0.022), 0.012, R=R), 0.008, GUN)
    fd.add(RoundBox(c + up * 0.38 - n * 0.079, (0.065, 0.012, 0.07), 0.01, R=R), 0.004, BLACK)
    for k in range(6):
        z = 0.08 + 0.022 * k
        fd.paint(Func(lambda P, z=z, k=k: np.maximum(np.abs(P[:, 2] - F(c[2] + z)) - F(0.0105), F(-1.0)), c - 0.3, c + 0.3), HAZARD if k % 2 == 0 else BLACK)
    fd.add(Cylinder(c + up * 0.12 - n * 0.078, 0.036, 0.03, rr=0.008, R=rot_from_axes(z_axis=-n)), 0.004, BLACK)
    fd.paint(RoundBox(c + up * 0.49 - n * 0.095, (0.05, 0.02, 0.012), 0.002, R=R), WHITE)
    return fd


def cable_pts():
    """The umbilical's centre line: out of the post's socket, down to the apron, over the kerb, across the deck."""
    c, t, n = post_frame()
    s = c + v3((0, 0, 0.12)) - n * 0.11
    cr = 0.028
    pts = [s, s - n * 0.05 + v3((0, 0, -0.06)), _polar(POST_A - 4, 1.07, GROUND_TOP + cr),
           _polar(POST_A - 9, KERB[1] + 0.01, KERB_TOP + cr), _polar(POST_A - 12, KERB[0] - 0.02, TOP_Z + cr),
           _polar(POST_A - 22, 0.9, TOP_Z + cr), _polar(POST_A - 38, 0.82, TOP_Z + cr), _polar(POST_A - 50, 0.72, TOP_Z + cr),
           _polar(POST_A - 47, 0.6, TOP_Z + cr)]
    return pts


def cable_field():
    """The thick black umbilical (rubber 12), banded every so often (5), its plug (gunmetal 9) with a violet ring (6)."""
    fd = Field("Cable")
    pts = cable_pts()
    fd.add(Chain(pts, [0.028] * len(pts), k=0.04), 0.0, RUBBER)
    for i in (3, 5, 7):
        d = norm(pts[i + 1] - pts[i])
        fd.add(Torus(lerp(pts[i], pts[i + 1], 0.5), 0.029, 0.007, R=rot_from_axes(z_axis=d)), 0.003, BLACK)
    end = pts[-1]
    d = norm(pts[-1] - pts[-2])
    R = rot_from_axes(z_axis=d)
    fd.add(Cylinder(end + d * 0.05, 0.042, 0.1, rr=0.012, R=R), 0.006, GUN)
    fd.add(Cylinder(end + d * 0.11, 0.032, 0.03, rr=0.006, R=R), 0.004, BLACK)
    fd.paint(Torus(end + d * 0.065, 0.043, 0.008, R=R), VIOLET)
    for k in range(3):
        a = 2 * math.pi * k / 3
        e = R @ v3((math.cos(a), math.sin(a), 0.0))
        fd.add(RoundCone(end + d * 0.12 + e * 0.015, end + d * 0.145 + e * 0.015, 0.005), 0.002, STEEL)
    return fd


# ---------------------------------------------------------------------------------------------- the tool cart
def cart_field():
    """A tool cart: a gunmetal frame (9) on black casters, two trays (black 5), a drawer unit (navy 8, steel pulls), a
    big wrench and a driver (steel 10, a black grip), a spare power cell (graphite 0, a violet band 6) on the top tray."""
    fd = Field("Cart")
    c, t, n = _frame(CART_A, PROP_R)
    up = v3((0, 0, 1))
    R = np.stack([t, n, up], axis=1)
    hw, hd = 0.15, 0.09
    for st in (-1, 1):
        for sn in (-1, 1):
            p = c + t * st * hw + n * sn * hd
            fd.add(RoundCone(p + up * 0.05, p + up * 0.55, 0.014), 0.0, GUN)
            fd.add(Sphere(p + up * 0.022, 0.022), 0.004, BLACK)
    for z in (0.14, 0.53):
        fd.add(RoundBox(c + up * z, (hw + 0.012, hd + 0.012, 0.012), 0.008, R=R), 0.004, BLACK)
        fd.sub(RoundBox(c + up * (z + 0.012), (hw - 0.004, hd - 0.004, 0.008), 0.004, R=R), 0.003)
    fd.add(RoundBox(c + up * 0.335 + t * 0.03, (0.11, hd - 0.005, 0.17), 0.012, R=R), 0.004, NAVY)
    for z in (0.24, 0.35, 0.46):
        fd.sub(RoundBox(c + up * z + t * 0.03 - n * hd, (0.1, 0.006, 0.002), 0.001, R=R), 0.001)
        fd.add(RoundCone(c + up * (z - 0.02) + t * 0.0 - n * (hd + 0.008), c + up * (z - 0.02) + t * 0.06 - n * (hd + 0.008), 0.006), 0.002, STEEL)
    # on the top tray: a wrench, a driver, a spare cell
    top = c + up * 0.555
    a, b = top - t * 0.11 - n * 0.03, top + t * 0.04 - n * 0.05
    fd.add(RoundCone(a, b, 0.012), 0.0, STEEL)
    for e, s in ((a, 1), (b, -1)):
        fd.add(Inter(Cylinder(e, 0.03, 0.016, rr=0.004), Sphere(e - norm(b - a) * s * 0.02, 0.05), 0.002), 0.004, STEEL)
    fd.add(RoundCone(top + t * 0.03 + n * 0.05, top + t * 0.1 + n * 0.035, 0.014, 0.012), 0.0, BLACK)
    fd.add(RoundCone(top + t * 0.1 + n * 0.035, top + t * 0.15 + n * 0.025, 0.005, 0.003), 0.0, STEEL)
    cc = top + t * 0.1 - n * 0.02 + up * 0.03
    fd.add(Cylinder(cc, 0.03, 0.07, rr=0.01, R=rot_from_axes(z_axis=t)), 0.0, BASE)
    fd.paint(Torus(cc, 0.031, 0.007, R=rot_from_axes(z_axis=t)), VIOLET)
    return fd


# ---------------------------------------------------------------------------------------------- the rack, the spare fist plate
def rack_field():
    """A low A-frame rack (gunmetal 9) on a black base plate, and on it a spare knuckle guard: a graphite bar (0) with a
    navy back (8), its four sockets empty (violet-lined 6), a white rim line (7)."""
    fd = Field("Rack")
    c, t, n = _frame(RACK_A, PROP_R)
    up = v3((0, 0, 1))
    R = np.stack([t, n, up], axis=1)
    fd.add(RoundBox(c + up * 0.012, (0.16, 0.08, 0.012), 0.008, R=R), 0.0, BLACK)
    for st in (-1, 1):
        p = c + t * st * 0.12
        fd.add(RoundCone(p + n * 0.06 + up * 0.02, p + up * 0.4, 0.015), 0.004, GUN)
        fd.add(RoundCone(p - n * 0.06 + up * 0.02, p + up * 0.4, 0.015), 0.004, GUN)
        fd.add(RoundCone(p + up * 0.4, p + up * 0.4 - n * 0.04 + up * 0.03, 0.013), 0.004, GUN)
    fd.add(RoundCone(c - t * 0.13 + up * 0.4, c + t * 0.13 + up * 0.4, 0.014), 0.004, GUN)
    # the plate, leaning on the frame's front (toward the deck)
    lean = norm(up * 0.92 + n * 0.4)
    Rp = np.stack([t, np.cross(lean, t), lean], axis=1)
    pc = c - n * 0.06 + up * 0.22
    fd.add(RoundBox(pc, (0.24, 0.05, 0.11), 0.035, R=Rp), 0.0, BASE)
    fd.add(RoundBox(pc + Rp @ v3((0, 0.045, 0)), (0.2, 0.025, 0.085), 0.018, R=Rp), 0.01, NAVY)
    face = -np.cross(lean, t)
    for k, v in enumerate((0.165, 0.055, -0.055, -0.165)):
        q = pc + t * v * 1.0 + face * 0.045
        fd.sub(RoundBox(q, (0.042, 0.022, 0.062), 0.014, R=Rp), 0.004)
        fd.paint(RoundBox(q - face * 0.012, (0.036, 0.034, 0.056), 0.012, R=Rp), VIOLET)
    fd.paint(RoundBox(pc + Rp @ v3((0, -0.04, -0.095)), (0.26, 0.06, 0.007), 0.0, R=Rp), WHITE)
    return fd


def case_field():
    """A black hard case (5) lying on the apron, yellow latches (13), a steel handle, a white label (7)."""
    fd = Field("Case")
    c, t, n = _frame(CASE_A, PROP_R + 0.01)
    up = v3((0, 0, 1))
    Rz = euler(0, 0, math.radians(CASE_A + 90 + 12))
    fd.add(RoundBox(c + up * 0.065, (0.17, 0.1, 0.065), 0.025, R=Rz), 0.0, BLACK)
    fd.add(RoundBox(c + up * 0.07, (0.175, 0.105, 0.008), 0.006, R=Rz), 0.004, BLACK)
    for s in (-1, 1):
        fd.add(RoundBox(c + up * 0.07 + Rz @ v3((s * 0.09, -0.104, 0.0)), (0.018, 0.008, 0.022), 0.005, R=Rz), 0.003, HAZARD)
    fd.add(RoundCone(c + up * 0.135 + Rz @ v3((-0.05, 0, 0)), c + up * 0.135 + Rz @ v3((0.05, 0, 0)), 0.01), 0.004, STEEL)
    fd.paint(RoundBox(c + up * 0.13 + Rz @ v3((0.09, 0.04, 0)), (0.04, 0.025, 0.01), 0.004, R=Rz), WHITE)
    return fd


def rim_glow_field():
    """The violet light strip in the kerb's top, the charging post's status lamps (their own glowing mesh)."""
    fd = Field("Rim")
    fd.add(Torus(v3((0, 0, KERB_TOP - 0.004)), STRIP_R, 0.012), 0.0)
    c, t, n = post_frame()
    up = v3((0, 0, 1))
    for k in range(3):
        fd.add(Sphere(c + up * (0.34 + 0.03 * k) - n * 0.092 + t * 0.035, 0.01), 0.0)
    fd.add(RoundBox(c + up * 0.39 - n * 0.079 - t * 0.012, (0.04, 0.004, 0.05), 0.004, R=np.stack([t, n, up], axis=1)), 0.0)
    fd.add(RoundBox(c + up * 0.565, (0.06, 0.05, 0.006), 0.004, R=np.stack([t, n, up], axis=1)), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- dry weeds at the apron's edge
def grass_geometry(seed=71):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 9 and tries < 4000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        if abs(math.degrees(a) % 360 - POST_A) < 20 or abs(math.degrees(a) % 360 - CART_A) < 18:
            continue
        r = rs.uniform(GROUND_R - 0.09, GROUND_R - 0.03)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.3 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        for b in range(rs.randint(5, 8)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.03)
            root[2] = GROUND_TOP - 0.005
            outv = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(outv * rs.uniform(0.3, 0.6) + v3((0, 0, 1)))
            v, f, uv = _b.blade_mesh(root, d, rs.uniform(0.05, 0.1), rs.uniform(0.02, 0.03), outv * 0.6 + v3((0, 0, -0.2)), segs=3,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=0):
    return []


def fields():
    return [("Ground", ground_field(), 0.008), ("Deck", deck_field(), 0.0045), ("Kerb", kerb_field(), 0.004),
            ("Post", post_field(), 0.003), ("Cable", cable_field(), 0.003), ("Cart", cart_field(), 0.0026),
            ("Rack", rack_field(), 0.0028), ("Case", case_field(), 0.003), ("Rim", rim_glow_field(), 0.003)]


REGION_PARTS = ("Ground", "Deck", "Kerb", "Post", "Cable", "Cart", "Rack", "Case")
LOW_TARGETS = {"Ground": 900, "Deck": 3600, "Kerb": 1100, "Post": 900, "Cable": 900, "Cart": 1700, "Rack": 1300,
               "Case": 500, "Rim": 400}
_KIT = dict(weave=0.0, black=(0.05, 0.05, 0.058), red=(0.62, 0.2, 0.74), white=(0.9, 0.9, 0.92), olive=(0.12, 0.16, 0.3),
            gunmetal=(0.24, 0.25, 0.28), steel=(0.66, 0.68, 0.72), glass=(0.05, 0.06, 0.09), rubber=(0.07, 0.07, 0.075),
            coyote=(0.92, 0.72, 0.14))
MAT_OVERRIDES = {"Ground": ("field_concrete", {"name": "HQ_BayApron", "base": (0.4, 0.4, 0.41), "dark": (0.3, 0.3, 0.31),
                                                "stain": (0.16, 0.15, 0.15)}),
                 "Deck": ("modern_kit", dict(_KIT, name="HQ_BayDeck", base=(0.31, 0.32, 0.35))),
                 "Kerb": ("modern_kit", dict(_KIT, name="HQ_BayKit", base=(0.16, 0.17, 0.2))),
                 "Post": ("modern_kit", dict(_KIT, name="HQ_BayKit", base=(0.16, 0.17, 0.2))),
                 "Cable": ("modern_kit", dict(_KIT, name="HQ_BayKit", base=(0.16, 0.17, 0.2))),
                 "Cart": ("modern_kit", dict(_KIT, name="HQ_BayKit", base=(0.16, 0.17, 0.2))),
                 "Rack": ("modern_kit", dict(_KIT, name="HQ_BayKit", base=(0.16, 0.17, 0.2))),
                 "Case": ("modern_kit", dict(_KIT, name="HQ_BayKit", base=(0.16, 0.17, 0.2))),
                 "Rim": ("glow_ball", {"name": "HQ_BayGlow", "col": (0.85, 0.25, 0.95)})}
GLOW = {"Rim": ((0.85, 0.25, 0.95), 1.25, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
