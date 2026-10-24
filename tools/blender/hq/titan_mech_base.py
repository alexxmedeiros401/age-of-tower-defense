"""The Titan Mech's base: the Resistance's salvage bay, cut into the robots' own data-center floor. A round deck of
steel floor grates (four panels, their bars running alternately across and along, dark below them), a solid steel ring
round them painted with charcoal-and-amber chevrons, a gunmetal kerb; round the kerb an apron of the data center's
raised-floor tiles (pale grey, seams, perforated vents, oil stains). On the apron: before it on both sides a low wall of
sandbags in two arcs, a white robot plate sprayed with an amber slash leaning on them; on its left a wrecked robot's
head lying on its side (its dead eye dark) and a severed robot forearm; behind it on its left a tripod chain hoist of
steel poles (a chain block at its top, the chain down to a hook with a salvaged robot hand hanging from it); behind it
on its right a squat generator (gunmetal, louvres, an exhaust, amber status lamps: `GlowRim`) and two thick cables
from it over the kerb and across the grates to a junction box behind its feet; beside the generator a pole with the
Resistance's amber banner (a charcoal double chevron on it, a ragged foot).

Everything on the deck lies flush or low (the cables, 6 cm; the junction box, 9 cm, behind its heels). Every prop on
the apron is low (under 0.5 m) within r = 1.2 (the fists sweep out to r ~1.15 as the tower turns, the hanging fists down
to z ~0.4); the tall ones (the hoist's legs and its hanging hand, the banner and its pole) stand beyond r = 1.2."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Inter, Shell, Lock, lerp
import base as _b

GROUND_R = 1.34
GROUND_TOP = 0.12
TOP_Z = 0.2                        # the deck's top = where it stands
STAND = v3((0.0, 0.0, TOP_Z))
DECK_R = 1.0
RING = (0.84, 0.97)                # the solid steel ring round the grates
KERB = (0.995, 1.065)
KERB_TOP = TOP_Z + 0.02
Z = v3((0.0, 0.0, 1.0))
# modern_kit labels
BASE, BLACK, RED, WHITE, TEAL, GUN, STEEL, GLASS, RUBBER, AMBER, BRASS = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
# android labels (the robot wreckage)
A_GRAPH, A_CHAR, A_PANEL, A_STEEL, A_GLASS, A_WHITE, A_ORANGE, A_RUBBER, A_AMBER = 5, 6, 7, 10, 11, 13, 14, 15, 16
# field_concrete labels (the apron): 6 black (the tiles' seams), 7 oil
SEAM, OIL = 6, 7

GEN_A, BANNER_A, HOIST_A = 122.0, 152.0, 54.0          # degrees round from its left (90 = behind it)
HEAD_A, ARM_A, PLATE_A = 338.0, 16.0, 292.0
BAGS = ((216.0, 256.0), (284.0, 324.0))
BAG = (0.15, 0.085, 0.05)
BAG_R = 1.17
JUNC = v3((-0.2, 0.62, TOP_Z))


def _polar(deg, r, z=GROUND_TOP):
    return v3((r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)), z))


def _frame(deg, r, z=GROUND_TOP):
    """A prop's frame on the apron: its foot centre, t (along the ring, counter-clockwise), n (out from the middle)."""
    c = _polar(deg, r, z)
    n = v3((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0.0))
    t = v3((-n[1], n[0], 0.0))
    return c, t, n


def ground_height(x, y):
    return TOP_Z if math.hypot(x, y) < DECK_R else GROUND_TOP


def _stroke(a, b, w, n, depth, rag=0.005):
    a, b, n = v3(a).astype(F), v3(b).astype(F), norm(v3(n)).astype(F)
    ab = b - a
    L2 = max(float(ab @ ab), 1e-12)

    def fn(P):
        t = np.clip(((P - a) @ ab) / F(L2), 0, 1)
        q = P - (a + t[:, None] * ab)
        dn = q @ n
        inplane = np.sqrt(np.maximum((q * q).sum(1) - dn * dn, 0))
        return np.maximum(inplane - F(w), np.abs(dn) - F(depth)) + F(rag) * NOISE(P * F(55))
    pad = depth + w + rag + 0.01
    return Func(fn, np.minimum(a, b) - pad, np.maximum(a, b) + pad)


# ---------------------------------------------------------------------------------------------- the apron (raised floor)
def ground_field():
    """The data center's raised-floor tiles (field_concrete, pale grey): square tiles 0.3 apart with dark seams (6), a few
    perforated vent tiles, oil stains (7), chips out of the edge."""
    fd = Field("Ground")

    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.01) * np.sin(a * 6 + 0.4) + F(0.006) * NOISE(P * F(3))
        dx = r - R
        dz = np.maximum(P[:, 2] - F(GROUND_TOP), F(-0.14) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.03), 0), np.maximum(dz + F(0.03), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.03), dz + F(0.03)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.03)
    fd.add(Func(disc, (-1.5, -1.5, -0.2), (1.5, 1.5, 0.2), disp=lambda P: F(0.0012) * NOISE(P * F(9)), disp_amp=0.002), 0.0)
    lo, hi = (-1.5, -1.5, -0.2), (1.5, 1.5, 0.2)
    g = 0.3

    def seams(P):
        dx = np.abs(P[:, 0] / F(g) - np.round(P[:, 0] / F(g) - 0.5) - 0.5) * F(g)
        dy = np.abs(P[:, 1] / F(g) - np.round(P[:, 1] / F(g) - 0.5) - 0.5) * F(g)
        return np.maximum(np.minimum(dx, dy) - F(0.004), np.abs(P[:, 2] - F(GROUND_TOP)) - F(0.006))
    fd.sub(Func(seams, lo, hi), 0.002)
    fd.paint(Func(lambda P: np.minimum(np.abs(P[:, 0] / F(g) - np.round(P[:, 0] / F(g) - 0.5) - 0.5),
                                       np.abs(P[:, 1] / F(g) - np.round(P[:, 1] / F(g) - 0.5) - 0.5)) * F(g) - F(0.007), lo, hi), SEAM)
    # vent tiles: rows of small holes
    for cx, cy in ((-1.05, -0.45), (1.05, -0.45), (0.45, -1.05), (-0.75, 0.75)):
        for i in range(5):
            for j in range(5):
                x, y = cx + (i - 2) * 0.05, cy + (j - 2) * 0.05
                if math.hypot(x, y) < GROUND_R - 0.06:
                    fd.sub(Cylinder(v3((x, y, GROUND_TOP)), 0.012, 0.03, rr=0.004), 0.003)
    rs = np.random.RandomState(14)
    for k in range(8):
        a = rs.uniform(0, 2 * math.pi)
        fd.sub(Sphere(_polar(math.degrees(a), GROUND_R + 0.02, GROUND_TOP + 0.01), rs.uniform(0.03, 0.05)), 0.01)
    for deg, r, s in ((GEN_A + 8, 1.17, 0.13), (HOIST_A, 1.2, 0.08), (250.0, 1.22, 0.06), (20.0, 1.25, 0.07)):
        c = _polar(deg, r)
        fd.paint(Func(lambda P, c=c, s=s: np.sqrt(((P[:, :2] - c[:2].astype(F)) ** 2).sum(1)) - F(s) + F(0.025) * NOISE(P * F(12)), lo, hi), OIL)
    return fd


# ---------------------------------------------------------------------------------------------- the deck (floor grates)
def _grate_holes(P):
    """< 0 inside the grates' holes: four panels (x, y quadrants), bars across in two and along in the others."""
    x, y = P[:, 0], P[:, 1]
    flip = (x * y) > 0
    a = np.where(flip, x, y)
    b = np.where(flip, y, x)
    pa, pb = F(0.055), F(0.2)
    da = np.abs(a / pa - np.floor(a / pa) - 0.5) * pa            # distance across a hole's long side
    db = np.abs(b / pb - np.floor(b / pb) - 0.5) * pb
    hole = np.maximum(da - F(0.0195), db - F(0.088))
    edge = F(0.035) - np.minimum(np.abs(x), np.abs(y))           # solid bands along the panels' seams
    rim = np.sqrt(x * x + y * y) - F(RING[0] - 0.01)
    return np.maximum(np.maximum(hole, edge), np.maximum(rim, F(TOP_Z - 0.024) - P[:, 2]))


def deck_field():
    """The steel deck (modern_kit 0 = steel grey): four grate panels, a solid ring round them with bolts and chevrons
    sprayed in charcoal (5) and amber (13), scuffs worn bright (10), a big amber arrow sprayed across the grates toward
    the robots, black scorch marks."""
    fd = Field("Deck")
    tex = lambda P: F(0.0005) * NOISE(P * F(40))
    fd.add(Cylinder(v3((0, 0, (TOP_Z + GROUND_TOP - 0.06) / 2)), DECK_R + 0.002, TOP_Z - GROUND_TOP + 0.06, rr=0.008, disp=tex, disp_amp=0.001), 0.0, BASE)
    lo, hi = (-1.1, -1.1, GROUND_TOP - 0.1), (1.1, 1.1, TOP_Z + 0.03)
    fd.sub(Func(_grate_holes, lo, hi), 0.002)
    fd.paint(Func(lambda P: _grate_holes(P + np.array([0, 0, 0.012], F)) - F(0.002), lo, hi), BLACK)       # dark down the holes
    # the ring: seams, bolts
    fd.sub(Func(lambda P: np.maximum(np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(RING[0])) - F(0.004), np.abs(P[:, 2] - F(TOP_Z)) - F(0.006)), lo, hi), 0.002)
    for k in range(20):
        a = 2 * math.pi * (k + 0.5) / 20
        for r in (RING[0] + 0.025, RING[1] - 0.012):
            fd.add(Cylinder(v3((math.cos(a) * r, math.sin(a) * r, TOP_Z + 0.002)), 0.011, 0.008, rr=0.003), 0.002, STEEL)
    # chevrons round the ring (amber and charcoal), sprayed over the robots' floor
    def chev(P, odd):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        s = a * F(RING[1]) / F(0.08) + (r - F(RING[0])) / F(0.08)
        ph = np.abs(s - np.floor(s) - F(0.5))
        inband = np.maximum(F(RING[0] + 0.045) - r, r - F(RING[1] - 0.03))
        stripe = (F(0.25) - ph) * F(0.08) if odd else (ph - F(0.25)) * F(0.08)
        return np.maximum(inband, -stripe) + F(0.003) * NOISE(P * F(50))
    fd.paint(Func(lambda P: chev(P, False), lo, hi), AMBER)
    fd.paint(Func(lambda P: chev(P, True), lo, hi), BLACK)
    # a big amber arrow sprayed across the grates before it (pointing at the robots)
    fd.paint(_stroke((0, -0.42, TOP_Z), (0, -0.78, TOP_Z), 0.035, Z, 0.04), AMBER)
    for sx in (-1, 1):
        fd.paint(_stroke((0, -0.8, TOP_Z), (sx * 0.16, -0.62, TOP_Z), 0.035, Z, 0.04), AMBER)
    # scuffs where its feet turn, scorch marks
    for sx in (-1, 1):
        c = v3((sx * 0.36, 0.0, TOP_Z))
        fd.paint(Func(lambda P, c=c: np.abs(np.sqrt(((P[:, :2] - c[:2].astype(F)) ** 2).sum(1)) - F(0.32)) - F(0.014) + F(0.012) * NOISE(P * F(25)),
                      c - 0.4, c + 0.4), STEEL)
    for c, s in (((0.55, 0.42), 0.11), ((-0.6, 0.3), 0.09), ((0.62, -0.38), 0.07)):
        cc = v3((c[0], c[1], TOP_Z))
        fd.paint(Func(lambda P, cc=cc, s=s: np.sqrt(((P[:, :2] - cc[:2].astype(F)) ** 2).sum(1)) - F(s) + F(0.03) * NOISE(P * F(14)),
                      cc - 0.3, cc + 0.3), BLACK)
    return fd


def kerb_field():
    """The gunmetal kerb round the deck (9), bolts (10), amber dashes sprayed on its top (13)."""
    fd = Field("Kerb")
    hz = (KERB_TOP - GROUND_TOP + 0.04) / 2

    def ring(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        dr = np.abs(r - F((KERB[0] + KERB[1]) / 2)) - F((KERB[1] - KERB[0]) / 2)
        dz = np.abs(P[:, 2] - F(KERB_TOP - hz)) - F(hz)
        q = np.stack([np.maximum(dr + F(0.012), 0), np.maximum(dz + F(0.012), 0)], 1)
        return np.minimum(np.maximum(dr, dz) + F(0.012), 0) + np.sqrt((q ** 2).sum(1)) - F(0.012)
    fd.add(Func(ring, (-1.15, -1.15, GROUND_TOP - 0.06), (1.15, 1.15, KERB_TOP + 0.01), disp=lambda P: F(0.0006) * NOISE(P * F(30)), disp_amp=0.001), 0.0, GUN)
    for k in range(24):
        a = 2 * math.pi * (k + 0.5) / 24
        fd.add(Cylinder(v3((math.cos(a) * (KERB[1] - 0.014), math.sin(a) * (KERB[1] - 0.014), KERB_TOP)), 0.008, 0.008, rr=0.003), 0.002, STEEL)
    for k in range(12):
        a = 2 * math.pi * k / 12
        fd.paint(Func(lambda P, a=a: np.maximum(np.abs(np.arctan2(P[:, 1], P[:, 0]) - F(a if a <= math.pi else a - 2 * math.pi)) - F(0.08), F(KERB_TOP - 0.006) - P[:, 2])
                      + F(0.002) * NOISE(P * F(60)), (-1.15, -1.15, KERB_TOP - 0.02), (1.15, 1.15, KERB_TOP + 0.02)), AMBER)
    return fd


# ---------------------------------------------------------------------------------------------- the generator and its cables
def gen_frame():
    return _frame(GEN_A, 1.16)


def generator_field():
    """A squat generator on skids (gunmetal 9, charcoal panels 0): louvred sides, an exhaust stack, a black control
    panel with amber status lamps (GlowRim), a white stencil (7), the robots' cyan-grey cells rewired: two cable sockets."""
    fd = Field("Generator")
    c, t, n = gen_frame()
    R = np.stack([t, n, Z], axis=1)
    for e in (-1, 1):
        fd.add(RoundBox(c + n * (e * 0.09) + Z * 0.016, (0.2, 0.022, 0.016), 0.006, R=R), 0.0, BLACK)
    bc = c + Z * 0.17
    fd.add(RoundBox(bc, (0.19, 0.13, 0.135), 0.024, R=R, disp=lambda P: F(0.0006) * NOISE(P * F(40)), disp_amp=0.001), 0.006, GUN)
    fd.add(RoundBox(bc + Z * 0.14, (0.17, 0.11, 0.012), 0.01, R=R), 0.004, BASE)
    for e in (-1, 1):
        for k in range(6):
            fd.sub(RoundBox(bc + n * (e * 0.132) + t * (-0.12 + 0.048 * k) + Z * 0.01, (0.008, 0.012, 0.075), 0.004, R=R), 0.003)
    # the control panel on the end toward the deck's front (its -t end), facing the camera's side
    pe = bc - n * 0.132
    fd.add(RoundBox(pe + Z * 0.02 - n * 0.004, (0.1, 0.008, 0.07), 0.006, R=R), 0.003, BLACK)
    fd.paint(RoundBox(pe + Z * 0.08 - n * 0.01 + t * 0.06, (0.05, 0.02, 0.012), 0.004, R=R), WHITE)
    ex = bc + Z * 0.15 + t * 0.11 + n * 0.04
    fd.add(Cylinder(ex + Z * 0.09, 0.024, 0.18, rr=0.006), 0.004, GUN)
    fd.add(Cylinder(ex + Z * 0.19, 0.03, 0.03, rr=0.006), 0.003, BLACK)
    for e in (-1, 1):
        fd.add(Cylinder(bc - t * 0.192 + Z * (-0.06) + n * (e * 0.05), 0.024, 0.03, rr=0.006, R=rot_from_axes(z_axis=-t)), 0.004, BLACK)
    fd.paint(Func(lambda P: np.maximum(np.abs(((P - bc.astype(F)) @ t.astype(F)) - (P[:, 2] - F(bc[2])) * F(0.8)) - F(0.02), np.abs((P - bc.astype(F)) @ n.astype(F)) - F(0.2))
                  + F(0.003) * NOISE(P * F(50)), bc - 0.3, bc + 0.3), AMBER)
    return fd


def cable_pts(e):
    """A cable's centre line: out of the generator's socket, down to the apron, over the kerb, across the grates."""
    c, t, n = gen_frame()
    s = c + Z * 0.11 - t * 0.21 + n * (e * 0.05)
    cr = 0.026
    j = JUNC + v3((e * 0.05 + 0.0, 0.07, 0.0))
    return [s, s - t * 0.07 + Z * (-0.06), _polar(GEN_A - 12 - e * 3, 1.09, GROUND_TOP + cr),
            _polar(GEN_A - 15 - e * 3, KERB[1] + 0.01, KERB_TOP + cr), _polar(GEN_A - 17 - e * 3, KERB[0] - 0.03, TOP_Z + cr),
            lerp(_polar(GEN_A - 18 - e * 3, KERB[0] - 0.03, TOP_Z + cr), j + Z * cr, 0.5) + v3((e * 0.03, 0.0, 0.0)), j + Z * cr]


def cable_field():
    """Two thick cables (rubber 12), taped every so often (8 teal), and the junction box they run to (gunmetal 9, an
    amber lamp: GlowRim, a hazard mark sprayed amber 13)."""
    fd = Field("Cable")
    for e in (-1, 1):
        pts = cable_pts(e)
        fd.add(Chain(pts, [0.026] * len(pts), k=0.04), 0.0, RUBBER)
        for i in (2, 4):
            d = norm(pts[i + 1] - pts[i])
            fd.add(Torus(lerp(pts[i], pts[i + 1], 0.5), 0.027, 0.008, R=rot_from_axes(z_axis=d)), 0.003, TEAL)
    fd.add(RoundBox(JUNC + Z * 0.04 + v3((0, 0.1, 0)), (0.12, 0.06, 0.045), 0.012), 0.004, GUN)
    fd.add(RoundBox(JUNC + Z * 0.088 + v3((0, 0.1, 0)), (0.124, 0.064, 0.006), 0.004), 0.003, BASE)
    fd.paint(_stroke(JUNC + v3((-0.08, 0.04, 0.05)), JUNC + v3((0.08, 0.04, 0.05)), 0.012, (0, -1, 0), 0.02), AMBER)
    return fd


# ---------------------------------------------------------------------------------------------- sandbags, the robot plate
def bag_specs(seed=7):
    rs = np.random.RandomState(seed)
    out = []
    for a0, a1 in BAGS:
        for course in range(2):
            rr = BAG_R - 0.01 * course
            span = math.radians(a1 - a0) - (0.08 if course else 0.0)
            n = max(1, int(span * rr / (2 * BAG[0] + 0.01)))
            for k in range(n):
                a = math.radians(a0) + (0.04 if course else 0.0) + span * (k + 0.5) / n
                z = GROUND_TOP + BAG[2] * 0.85 + course * (2 * BAG[2] * 0.8) + rs.uniform(-0.004, 0.006)
                c = v3((math.cos(a) * (rr + rs.uniform(-0.01, 0.01)), math.sin(a) * (rr + rs.uniform(-0.01, 0.01)), z))
                yaw = a + math.pi / 2 + rs.uniform(-0.08, 0.08)
                h = (BAG[0] * rs.uniform(0.92, 1.04), BAG[1] * rs.uniform(0.92, 1.05), BAG[2] * rs.uniform(0.9, 1.05))
                out.append((c, yaw, h, int(rs.randint(1 << 20))))
    return out


def sandbags_field():
    """Plump sandbags (sacking 0), their tied ends pinched (twine 6), a stencilled mark on a few (5)."""
    fd = Field("Sandbags")
    lumpy = lambda P: F(0.004) * NOISE(P * F(12)) + F(0.0015) * NOISE(P * F(40))
    for c, yaw, h, sd in bag_specs():
        R = euler(0.03 * math.sin(sd), 0.04 * math.cos(sd), yaw)
        fd.add(RoundBox(c, h, h[2] * 0.95, R=R, disp=lumpy, disp_amp=0.006), 0.012, 0)
        e = c + R @ v3((h[0] + 0.012, 0.0, 0.0))
        fd.add(Ellipsoid(e, (0.022, 0.028, 0.022), R=R), 0.012, 0)
        fd.add(Torus(e - R @ v3((0.006, 0, 0)), 0.017, 0.0045, R=R @ rot_from_axes(z_axis=(1, 0, 0))), 0.002, 6)
        if sd % 4 == 0:
            fd.paint(Inter(Shell(Ellipsoid(c + v3((0, 0, h[2] * 0.4)), (0.055, 0.04, h[2] * 0.7), R=R), 0.0, 0.03),
                           Plane(c + v3((0, 0, h[2] * 0.5)), (0, 0, -1))), 5)
    return fd


# ---------------------------------------------------------------------------------------------- the robot wreckage
def wreck_field():
    """Robot wreckage (android: white 13, hazard orange 14, graphite 5, panel lines 7, dark glass 11, steel 10, amber
    paint 16): a robot's head lying on its side (its eye dark, a crack, an amber X sprayed on it), a severed forearm and
    fist, a white plate leaning on the sandbags with an amber slash; a salvaged robot hand on the hoist's hook (Hoist)."""
    fd = Field("Wreck")
    # the head, lying on its side, turned to face the camera's way
    c, t, n = _frame(HEAD_A, 1.12)
    hc = c + Z * 0.115
    R = np.stack([t, n, Z], 1) @ euler(0.0, 1.35, -0.5)
    fd.add(RoundBox(hc, (0.13, 0.12, 0.09), 0.06, R=R, disp=lambda P: F(0.0008) * NOISE(P * F(24)), disp_amp=0.001), 0.0, A_WHITE)
    fd.add(RoundBox(hc + R @ v3((0, -0.11, 0.05)), (0.14, 0.03, 0.022), 0.018, R=R @ euler(-0.35, 0, 0)), 0.012, A_WHITE)
    fd.add(RoundBox(hc + R @ v3((0, -0.08, -0.065)), (0.1, 0.05, 0.035), 0.025, R=R), 0.015, A_GRAPH)
    fd.paint(RoundBox(hc + R @ v3((0, 0, 0.1)), (0.026, 0.3, 0.08), 0.0, R=R), A_ORANGE)
    ec = hc + R @ v3((0, -0.125, 0.0))
    fd.sub(Cylinder(ec, 0.05, 0.07, rr=0.008, R=R @ rot_from_axes(z_axis=(0, 1, 0))), 0.006)
    fd.add(Sphere(ec + R @ v3((0, 0.03, 0)), 0.045), 0.0, A_GLASS)
    fd.sub(Sphere(hc + R @ v3((0.13, 0.04, 0.05)), 0.05), 0.012)                                 # smashed in on one side
    fd.paint(_stroke(hc + R @ v3((-0.08, 0.0, 0.12)), hc + R @ v3((0.06, 0.0, 0.14)), 0.016, R @ v3((0, 0, 1)), 0.06), A_AMBER)
    # the severed forearm and fist
    c, t, n = _frame(ARM_A, 1.16)
    a = c + Z * 0.075 - t * 0.17
    b = c + Z * 0.075 + t * 0.06
    fd.add(seg_tube(a, b, 0.07), 0.0, A_WHITE)
    fd.paint(Func(lambda P: np.abs((P - lerp(a, b, 0.75).astype(F)) @ norm(b - a).astype(F)) - F(0.018), a - 0.2, b + 0.2), A_ORANGE)
    fd.add(RoundBox(b + norm(b - a) * 0.08 + Z * 0.0, (0.07, 0.065, 0.065), 0.035, R=np.stack([t, n, Z], 1)), 0.015, A_GRAPH)
    for k in range(4):
        fd.add(Sphere(b + norm(b - a) * 0.15 + n * (-0.045 + 0.03 * k) + Z * 0.01, 0.024), 0.008, A_GRAPH)
    fd.add(RoundCone(a, a - norm(b - a) * 0.05, 0.045), 0.01, A_STEEL)                          # the torn-off joint
    for k in range(3):
        d = norm(-norm(b - a) + n * (0.5 * (k - 1)) + Z * 0.3)
        fd.add(Chain([a, a + d * 0.06, a + d * 0.11 + Z * (-0.03)], [0.009, 0.008, 0.007], k=0.005), 0.004, A_RUBBER)
    # the white plate leaning on the sandbags, an amber slash on it
    c, t, n = _frame(PLATE_A, 1.07)
    lean = norm(Z * 0.9 + n * 0.45)
    Rp = np.stack([t, np.cross(lean, t), lean], 1)
    pc = c + Z * 0.16 - n * 0.0
    fd.add(RoundBox(pc, (0.15, 0.018, 0.13), 0.016, R=Rp, disp=lambda P: F(0.0008) * NOISE(P * F(24)), disp_amp=0.001), 0.0, A_WHITE)
    face = -np.cross(lean, t)
    fd.paint(RoundBox(pc + lean * 0.1, (0.2, 0.05, 0.02), 0.0, R=Rp), A_ORANGE)
    fd.paint(_stroke(pc - t * 0.1 - lean * 0.08 + face * 0.02, pc + t * 0.1 + lean * 0.06 + face * 0.02, 0.022, face, 0.03), A_AMBER)
    fd.sub(Sphere(pc + t * 0.07 - lean * 0.06 + face * 0.04, 0.035), 0.01)
    return fd


def seg_tube(a, b, r):
    return RoundCone(a, b, r, r * 1.08)


# ---------------------------------------------------------------------------------------------- the tripod hoist
HOIST_R = 1.26
HOIST_TOP = 1.86


def hoist_apex():
    return _polar(HOIST_A, HOIST_R, HOIST_TOP)


def hoist_field():
    """A tripod of steel poles (gunmetal 9) splayed beyond the kerb, lashed at the top (teal webbing 8); a chain block
    (gunmetal, an amber hand-chain wheel 13) hanging from it, the chain (steel 10) down to a hook with a salvaged robot
    hand hanging from it (white 7 and black 5 under modern_kit; a hazard-orange band painted 6? no: amber 13)."""
    fd = Field("Hoist")
    apex = hoist_apex()
    c, t, n = _frame(HOIST_A, HOIST_R)
    feet = [c + n * 0.08 + t * 0.26, c + n * 0.08 - t * 0.26, c - n * 0.17]
    feet = [f for f in feet]
    for f in feet:
        if math.hypot(f[0], f[1]) < 1.2:
            f[:2] = f[:2] * (1.2 / math.hypot(f[0], f[1]))
    for f in feet:
        d = norm(apex - f)
        fd.add(RoundCone(f + Z * 0.01, apex + d * 0.05, 0.032, 0.026), 0.0, GUN)
        fd.add(Cylinder(f + Z * 0.012, 0.036, 0.024, rr=0.006), 0.004, BLACK)
    fd.add(Sphere(apex, 0.055), 0.02, GUN)
    fd.add(Torus(apex - Z * 0.03, 0.04, 0.012), 0.004, TEAL)
    # the chain block
    blk = apex - Z * 0.15
    fd.add(RoundCone(apex, blk, 0.012), 0.004, STEEL)
    fd.add(RoundBox(blk - Z * 0.03, (0.05, 0.035, 0.06), 0.015, R=np.stack([t, n, Z], 1)), 0.006, GUN)
    fd.add(Cylinder(blk - Z * 0.02 + n * 0.045, 0.055, 0.014, rr=0.005, R=rot_from_axes(z_axis=n)), 0.003, AMBER)
    # the chain (links) and the hook
    top, bot = blk - Z * 0.1, blk - Z * 0.52
    nl = 13
    for k in range(nl):
        p = lerp(top, bot, k / (nl - 1))
        ax = n if k % 2 else t
        fd.add(Torus(p, 0.017, 0.0055, R=rot_from_axes(z_axis=ax, x_axis=Z)), 0.0, STEEL)
    hk = bot - Z * 0.03
    fd.add(Chain([hk, hk - Z * 0.05, hk - Z * 0.08 + n * 0.03, hk - Z * 0.06 + n * 0.055], [0.012, 0.012, 0.011, 0.008], k=0.006), 0.004, GUN)
    # the salvaged robot hand hanging by its wrist from the hook (fingers down)
    wr = hk - Z * 0.09 + n * 0.02
    Rh = np.stack([t, n, Z], 1)
    fd.add(Cylinder(wr - Z * 0.02, 0.04, 0.04, rr=0.01), 0.006, GUN)
    fd.add(RoundBox(wr - Z * 0.09, (0.07, 0.04, 0.06), 0.03, R=Rh), 0.01, WHITE)
    for k in range(4):
        x = -0.045 + 0.03 * k
        fd.add(Chain([wr - Z * 0.13 + t * x, wr - Z * 0.19 + t * x - n * 0.01, wr - Z * 0.22 + t * x - n * 0.03], [0.015, 0.014, 0.012], k=0.006), 0.006, BLACK)
    fd.add(Chain([wr - Z * 0.08 + t * 0.07, wr - Z * 0.14 + t * 0.09 - n * 0.02], [0.016, 0.013], k=0.006), 0.006, BLACK)
    fd.paint(RoundBox(wr - Z * 0.06, (0.1, 0.07, 0.012), 0.0, R=Rh), AMBER)
    return fd


# ---------------------------------------------------------------------------------------------- the banner
BANNER_R = 1.27


def banner_frame():
    return _frame(BANNER_A, BANNER_R)


def banner_field():
    """The Resistance's banner (modern_kit with a weave: amber cloth 0) on a steel pole (gunmetal 9) with a crossbar: a
    charcoal double chevron on it (5), a ragged foot; the pole stands in a small stand of sandbag-weighted steel feet."""
    fd = Field("Banner")
    c, t, n = banner_frame()
    top = c + Z * 1.9
    fd.add(RoundCone(c + Z * 0.02, top, 0.026, 0.02), 0.0, GUN)
    fd.add(Sphere(top + Z * 0.02, 0.028), 0.006, GUN)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        e = t * math.cos(a) + n * math.sin(a)
        fd.add(RoundCone(c + Z * 0.2, c + e * 0.14 + Z * 0.012, 0.012), 0.004, GUN)
    bar = top - Z * 0.08
    fd.add(RoundCone(bar - t * 0.28, bar + t * 0.28, 0.016), 0.004, GUN)
    # the cloth: hanging from the crossbar, gently rippled, its foot cut ragged
    def cloth(P):
        q = P - bar.astype(F)
        u = q @ t.astype(F)
        w = q[:, 2]
        # its folds: the sheet itself rippled (a wave across it, deeper toward its foot)
        v = q @ n.astype(F) - (F(0.014) * np.sin(u * F(14) + F(0.6)) * (F(0.4) - w)) - F(0.002) * NOISE(P * F(20))
        foot = F(-0.8) + F(0.035) * np.sin(u * F(38)) + F(0.03) * NOISE(P * F(14))
        return np.maximum(np.maximum(np.abs(u) - F(0.25), np.abs(v) - F(0.01)), np.maximum(w - F(-0.02), foot - w))
    fd.add(Func(cloth, bar - 1.0, bar + 0.3), 0.004, BASE)
    # the double chevron (on both faces)
    for k, dz in enumerate((-0.28, -0.46)):
        m = bar + Z * dz
        for s in (-1, 1):
            a = m + t * (s * 0.2) + Z * 0.13
            b = m - Z * 0.02
            fd.paint(_stroke(a, b, 0.036, n, 0.06, rag=0.004), BLACK)
    return fd


def rim_glow_field():
    """The generator's amber status lamps and the junction box's lamp (their own glowing mesh)."""
    fd = Field("Rim")
    c, t, n = gen_frame()
    bc = c + Z * 0.17
    for k in range(3):
        fd.add(Sphere(bc - n * 0.142 + Z * (0.02 + 0.03 * k) - t * 0.06, 0.011), 0.0)
    fd.add(RoundBox(bc - n * 0.141 + Z * 0.04 + t * 0.03, (0.04, 0.004, 0.025), 0.004, R=np.stack([t, n, Z], 1)), 0.0)
    fd.add(Sphere(JUNC + Z * 0.1 + v3((0.07, 0.1, 0)), 0.014), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- no grass in the data center
def grass_geometry(seed=71):
    return np.zeros((0, 3)), [], np.zeros((0, 2)), np.zeros(0)


def flower_geometry(seed=0):
    return []


def fields():
    return [("Ground", ground_field(), 0.008), ("Deck", deck_field(), 0.0042), ("Kerb", kerb_field(), 0.004),
            ("Generator", generator_field(), 0.003), ("Cable", cable_field(), 0.003), ("Sandbags", sandbags_field(), 0.004),
            ("Wreck", wreck_field(), 0.003), ("Hoist", hoist_field(), 0.0026), ("Banner", banner_field(), 0.003),
            ("Rim", rim_glow_field(), 0.003)]


REGION_PARTS = ("Ground", "Deck", "Kerb", "Generator", "Cable", "Sandbags", "Wreck", "Hoist", "Banner")
LOW_TARGETS = {"Ground": 1000, "Deck": 3600, "Kerb": 900, "Generator": 1100, "Cable": 800, "Sandbags": 1800,
               "Wreck": 1700, "Hoist": 1500, "Banner": 700, "Rim": 160}
_KIT = dict(weave=0.0, base=(0.13, 0.13, 0.15), black=(0.05, 0.05, 0.058), red=(0.72, 0.07, 0.05), white=(0.88, 0.88, 0.86),
            olive=(0.2, 0.27, 0.28), gunmetal=(0.26, 0.27, 0.3), steel=(0.64, 0.66, 0.7), glass=(0.05, 0.06, 0.09),
            rubber=(0.07, 0.07, 0.075), coyote=(0.95, 0.6, 0.15))
_PLATES = dict(suit=(0.1, 0.1, 0.11), graphite=(0.22, 0.23, 0.25), navy=(0.13, 0.13, 0.15), violet=(0.92, 0.56, 0.14),
               tape=(0.2, 0.27, 0.28), steel=(0.56, 0.58, 0.62), glass=(0.03, 0.035, 0.045), white=(0.88, 0.88, 0.85),
               orange=(1.0, 0.45, 0.1), rubber=(0.085, 0.085, 0.09), yellow=(0.98, 0.6, 0.13), wear=1.5)
MAT_OVERRIDES = {"Ground": ("field_concrete", {"name": "HQ_BayTiles", "base": (0.5, 0.51, 0.53), "dark": (0.36, 0.37, 0.39),
                                                "paint2": (0.16, 0.16, 0.17), "stain": (0.17, 0.16, 0.16)}),
                 "Deck": ("modern_kit", dict(_KIT, name="HQ_BayGrates", base=(0.34, 0.35, 0.38))),
                 "Kerb": ("modern_kit", dict(_KIT, name="HQ_BayKit")),
                 "Generator": ("modern_kit", dict(_KIT, name="HQ_BayKit")),
                 "Cable": ("modern_kit", dict(_KIT, name="HQ_BayKit")),
                 "Hoist": ("modern_kit", dict(_KIT, name="HQ_BayKit")),
                 "Sandbags": ("sacking", {"name": "HQ_BaySandbags", "base": (0.5, 0.47, 0.4), "dark": (0.33, 0.3, 0.25)}),
                 "Wreck": ("android", dict(_PLATES, name="HQ_BayWreck")),
                 "Banner": ("modern_kit", dict(_KIT, name="HQ_BayBanner", weave=1.0, base=(0.95, 0.6, 0.15))),
                 "Rim": ("glow_ball", {"name": "HQ_BayGlow", "col": (1.0, 0.62, 0.15)})}
GLOW = {"Rim": ((1.0, 0.62, 0.15), 1.25, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
