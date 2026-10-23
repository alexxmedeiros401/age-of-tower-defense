"""Stealth Jet, HQ: the Modern Age's fast flyer, a robot stealth fighter that cloaks. A small, chunky jet of faceted
white armour plates (flat facets meeting at soft creases, panel lines between them) over a gunmetal underside: a
chiselled nose, the body widening along sharp chines, swept wings with clipped tips, square-cut intakes under the
chines; where the cockpit would be, a faceted armoured head with a black visor band wrapped round its front and a red
glowing visor slit in it, set in a frown (the robot's eye). Two canted tail fins (hazard-orange tips) on rudder
bones, small swept tailplanes, two square gunmetal engine nozzles at its tail with cyan glowing exhausts. Hazard-orange
chevrons near the wing tips and a hazard-striped patch on its spine behind the head.
Fly (48 frames): it weaves from side to side, banking into each turn and yawing toward it, bobbing a little, the
rudders working against the turn and the exhausts pulsing. In game it turns into a see-through cyan ghost while it is
cloaked (game.gd's ghost materials). Faces -Y, Z up; flies about 1.0 model units up (its body's centre); model_scale
0.9 (and "flying": the game lifts it 0.9 more).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, rot_from_axes, v3, norm, F
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser

ROOT_NAME = "StealthJet"
GLB_NAME = "stealth_jet"
TEX_PREFIX = "stealth_jet"
FLY_FRAMES = 48

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.22, 0.23, 0.26)
BLACK = (0.06, 0.06, 0.07)
RED_GLOW = (1.0, 0.16, 0.08)
CYAN = (0.3, 0.88, 1.0)

C = v3((0, 0, 1.0))                        # the body's centre (the chine plane is z = 1.0)
ZC = 1.0
NOZ_X = 0.078                              # the two engine nozzles (x = +-NOZ_X)
NOZ_Y = 0.555
NOZ_Z = 0.985
FIN_CANT = math.radians(27)
FIN_ROOT = {sx: v3((sx * 0.125, 0.0, 1.085)) for sx in (-1, 1)}      # (y set per point)


# ------------------------------------------------------------------------------------------------ shared helpers
def facet(pts, k=0.006, inset=0.0):
    """A faceted convex solid: the convex hull of `pts`, its creases softened (a soft max over its face planes: flat
    faces stay exact, edges round over about 2-3 k). inset > 0 shrinks it. Returns a Func."""
    from scipy.spatial import ConvexHull
    pts = np.asarray(pts, dtype=np.float64)
    eq = ConvexHull(pts).equations
    eq = np.unique(np.round(eq, 6), axis=0)
    n, d = eq[:, :3].astype(F), eq[:, 3].astype(F)
    kk = F(k)

    def fn(P):
        D = P.astype(F) @ n.T + d
        m = D.max(1)
        s = m + kk * np.log(np.exp((D - m[:, None]) / kk).sum(1))
        return s + F(inset)
    pad = 0.02
    return Func(fn, pts.min(0) - pad, pts.max(0) + pad)


def mirror_pts(pts):
    """Points of a part on the left (+x) and their mirror images (a symmetric hull)."""
    out = []
    for p in pts:
        out.append(tuple(p))
        if abs(p[0]) > 1e-9:
            out.append((-p[0], p[1], p[2]))
    return out


def hazard(f, lo, hi, w=0.05, band=None, d=(0, 1, 1), orange=1, black=4):
    """Diagonal hazard stripes (orange / black labels) over the box lo..hi (optionally only where band(P) < 0),
    running across the direction d."""
    lo, hi = v3(lo), v3(hi)
    dd = norm(d).astype(F)
    def box(P):
        return np.max(np.stack([lo.astype(F) - P, P - hi.astype(F)], 0), axis=(0, 2))
    def org(P):
        b = box(P)
        return b if band is None else np.maximum(b, band(P))
    def blk(P):
        s = (P @ dd) / F(w)
        fr = s - np.floor(s)
        return np.maximum(org(P), (np.abs(fr - F(0.25)) - F(0.25)) * F(w * 0.7))
    f.paint(Func(org, lo - 0.01, hi + 0.01), orange)
    f.paint(Func(blk, lo - 0.01, hi + 0.01), black)


def rel(arm, name, d):
    """An aim given in the bone's parent's rest frame: direction d (armature space, rest pose) carried by the parent."""
    R0i = arm.data.bones[name].matrix_local.to_3x3().inverted()
    d = Vector(d)
    return lambda P, base: (base.to_3x3() @ R0i) @ d


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / float(b - a)))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------------------------------------ the shapes
def _station(y, wt, zt, wc, zc, wb, zb):
    return [(wt, y, zt), (wc, y, zc), (wb, y, zb)]


BODY_PTS = mirror_pts([(0.0, -0.66, 1.0), (0.0, -0.655, 0.982), (0.012, -0.64, 0.995)] +
                      _station(-0.44, 0.05, 1.075, 0.12, ZC, 0.055, 0.94) +
                      _station(-0.16, 0.1, 1.115, 0.215, ZC, 0.12, 0.9) +
                      _station(0.22, 0.115, 1.11, 0.23, ZC, 0.135, 0.905) +
                      _station(0.53, 0.1, 1.075, 0.165, ZC, 0.115, 0.93))
BODY = facet(BODY_PTS, k=0.007)

HEAD_PTS = mirror_pts([(0.05, -0.43, 1.055), (0.105, -0.2, 1.085), (0.095, 0.06, 1.085),        # its foot (in the body)
                       (0.0, -0.455, 1.075),
                       (0.042, -0.37, 1.135), (0.072, -0.22, 1.195), (0.05, -0.02, 1.175),      # its upper facets
                       (0.0, -0.39, 1.14), (0.0, -0.24, 1.215), (0.0, 0.0, 1.18)])
HEAD = facet(HEAD_PTS, k=0.006)
HEAD_LO, HEAD_HI = np.min(HEAD_PTS, 0) - 0.03, np.max(HEAD_PTS, 0) + 0.03


def _visor_band(P):
    """Signed distance across the visor band: a band round the head's front, low in the middle and rising to the sides
    and back (a frown)."""
    zc = F(1.152) + F(0.42) * np.abs(P[:, 0]) + F(0.16) * (P[:, 1] + F(0.3))
    return (P[:, 2] - zc) * F(0.92)


def _visor_ends(P, grow):
    """The visor slit runs across the head's front slope only (|x| < 0.07, ahead of y = -0.25), rounded at its ends."""
    q = np.stack([np.maximum(np.abs(P[:, 0]) - F(0.062), 0), np.maximum(P[:, 1] - F(-0.25), 0)], 1)
    return np.sqrt((q * q).sum(1)) - F(0.008 + grow)


def _wing_pts(sx):
    """A swept wing with clipped tips: thin edges, a ridge along its mid-chord; a little anhedral."""
    plan = [(0.15, -0.27), (0.6, 0.14), (0.6, 0.25), (0.17, 0.38)]
    ridge = [(0.15, 0.04, 0.026), (0.6, 0.195, 0.011)]
    pts = []
    sag = lambda x: -0.035 * (x - 0.15) / 0.45
    for x, y in plan:
        for dz in (-0.005, 0.005):
            pts.append((sx * x, y, ZC + sag(x) + dz))
    for x, y, t in ridge:
        for dz in (-t, t):
            pts.append((sx * x, y, ZC + sag(x) + dz * (0.8 if dz < 0 else 1.0)))
    return pts


def _tail_pts(sx):
    plan = [(0.11, 0.33), (0.35, 0.5), (0.35, 0.6), (0.11, 0.64)]
    pts = []
    for x, y in plan:
        for dz in (-0.004, 0.004):
            pts.append((sx * x, y, 0.985 + dz))
    for x, y, t in ((0.11, 0.48, 0.018), (0.35, 0.55, 0.008)):
        for dz in (-t, t):
            pts.append((sx * x, y, 0.985 + dz))
    return pts


def _fin_axes(sx):
    up = v3((sx * math.sin(FIN_CANT), 0, math.cos(FIN_CANT)))
    side = v3((math.cos(FIN_CANT) * sx, 0, -math.sin(FIN_CANT)))   # (its outward normal)
    return up, side


def _fin_pts(sx):
    """A canted fin: a raked trapezoid in the plane through its root line, tilted outward by FIN_CANT."""
    up, side = _fin_axes(sx)
    o = v3((sx * 0.125, 0.0, 1.075))
    plan = [(0.17, 0.0), (0.5, 0.0), (0.53, 0.25), (0.39, 0.25)]          # (y, height along `up`)
    pts = []
    for y, h in plan:
        for t in (-0.004, 0.004):
            pts.append(tuple(o + v3((0, y, 0)) + up * h + side * t))
    for y, h, t in ((0.36, 0.0, 0.016), (0.46, 0.25, 0.007)):
        for s in (-t, t):
            pts.append(tuple(o + v3((0, y, 0)) + up * h + side * s))
    return pts


FIN_PIVOT = {sx: v3((sx * 0.125, 0.36, 1.075)) for sx in (-1, 1)}
FIN_TIP = {sx: FIN_PIVOT[sx] + _fin_axes(sx)[0] * 0.25 + v3((0, 0.1, 0)) for sx in (-1, 1)}

BONES = [
    ("root", tuple(C), tuple(C + v3((0, 0, 0.1))), None),
    ("fin.L", tuple(FIN_PIVOT[1]), tuple(FIN_TIP[1]), "root"),
    ("fin.R", tuple(FIN_PIVOT[-1]), tuple(FIN_TIP[-1]), "root"),
    ("exhaust.L", (NOZ_X, NOZ_Y + 0.02, NOZ_Z), (NOZ_X, NOZ_Y + 0.14, NOZ_Z), "root"),
    ("exhaust.R", (-NOZ_X, NOZ_Y + 0.02, NOZ_Z), (-NOZ_X, NOZ_Y + 0.14, NOZ_Z), "root"),
]

MATS = {
    "armor": ("armor", dict(name="RB_JetArmor", base=(0.93, 0.93, 0.91), labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.42),
                                                                                  (4, BLACK, 0.3)], seams=[2], wear=0.8, rough=0.28)),
    "frame": ("gunmetal", dict(name="RB_JetFrame", labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6), (4, BLACK, 0.5)], seams=[2])),
    "glow": ("glow", dict(name="RB_JetGlow", col=RED_GLOW)),
}
GLOW = {"Visor": (RED_GLOW, 1.5, 0.5), "ExhaustL": (CYAN, 1.4, 0.55), "ExhaustR": (CYAN, 1.4, 0.55)}

LOW_TARGETS = {"Body": 1100, "Head": 420, "Visor": 90, "WingL": 260, "WingR": 260, "Tails": 200, "FinL": 140, "FinR": 140,
               "Nozzles": 420, "ExhaustL": 70, "ExhaustR": 70}


def parts(fine=False):
    vx = 0.0035 if fine else 0.0065
    vs = 0.0028 if fine else 0.0055
    out = []
    under = Func(lambda P: P[:, 2] - F(ZC - 0.004), (-1, -1, 0.5), (1, 1, 1.5))        # the gunmetal underside
    # ---- the body: faceted white plates, the gunmetal underside, intakes, panel lines, a hazard patch on its spine
    f = Field("Body")
    f.add(BODY)
    for sx in (-1, 1):
        f.sub(RoundBox((sx * 0.175, -0.22, 0.958), (0.04, 0.1, 0.03), 0.008, R=rot_from_axes(z_axis=(sx * 0.35, 0, 1))), k=0.006)  # an intake
    f.paint(under, 3)
    for sx in (-1, 1):
        f.paint(RoundBox((sx * 0.17, -0.18, 0.958), (0.05, 0.11, 0.034), 0.008), 4)                 # its dark throat
        f.paint(RoundBox((sx * 0.08, 0.15, 1.12), (0.0025, 0.4, 0.05)), 2)                         # panel lines
    for y in (-0.47, 0.1, 0.36):
        f.paint(RoundBox((0, y, 1.08), (0.3, 0.0025, 0.06)), 2)
    f.paint(RoundBox((0, 0.23, 1.14), (0.004, 0.13, 0.04)), 2)                                    # (the spine's seam)
    for sx in (-1, 1):                                                                            # orange pinstripes
        f.paint(RoundBox((sx * 0.105, 0.3, 1.1), (0.008, 0.21, 0.04)), 1)
    hazard(f, (-0.075, 0.1, 1.08), (0.075, 0.3, 1.16), w=0.045, d=(1, 1, 0))
    f.paint(RoundBox((0, -0.6, 0.995), (0.2, 0.06, 0.1)), 1)                                     # an orange nose tip
    out.append(("Body", f, vx, "root", "armor"))
    # ---- the head: faceted armour where the cockpit would be, a black visor band, the red slit in a groove
    f = Field("Head")
    f.add(HEAD)
    band = lambda P: np.maximum(np.abs(_visor_band(P)) - F(0.03), _visor_ends(P, 0.018))
    groove = lambda P: np.maximum(np.maximum(np.abs(HEAD(P)) - F(0.011), np.abs(_visor_band(P)) - F(0.0085)), _visor_ends(P, 0.0))
    f.sub(Func(groove, HEAD_LO, HEAD_HI), k=0.003)
    f.paint(Func(band, HEAD_LO, HEAD_HI), 4)
    f.paint(RoundBox((0, -0.08, 1.2), (0.0025, 0.2, 0.05)), 2)
    out.append(("Head", f, vs, "root", "armor"))
    f = Field("Visor")
    f.add(Func(lambda P: np.maximum(np.maximum(np.abs(HEAD(P) + F(0.006)) - F(0.0055), np.abs(_visor_band(P)) - F(0.0075)),
                                    _visor_ends(P, -0.004)), HEAD_LO, HEAD_HI))
    out.append(("Visor", f, vs, "root", "glow"))
    # ---- the wings: white on top, gunmetal below, orange chevrons near the tips, panel lines
    for s, sx in (("L", 1), ("R", -1)):
        wp = _wing_pts(sx)
        f = Field("Wing" + s)
        f.add(facet(wp, k=0.004))
        f.paint(Func(lambda P: P[:, 2] - (F(ZC) - F(0.035) * (np.abs(P[:, 0]) - F(0.15)) / F(0.45)) + F(0.001),
                     (-1, -1, 0.8), (1, 1, 1.2)), 3)
        dch = norm(v3((sx * 0.9, -1.0, 0)))                                 # chevrons across the wing, near the tip
        for o, wd in ((0.47, 0.028), (0.4, 0.012)):
            c0 = v3((sx * o, 0.06 + (o - 0.15) * 0.35, ZC))
            f.paint(Func(lambda P, c0=c0, wd=wd: np.maximum(np.abs((P - c0.astype(F)) @ v3((sx * 1.0, 0.25, 0)).astype(F)) - F(wd),
                                                            F(ZC - 0.03) - P[:, 2]), (-1, -1, 0.8), (1, 1, 1.2)), 1)
        f.paint(Func(lambda P: np.maximum(np.abs(P[:, 0] * F(sx) - F(0.3)) - F(0.0025), F(ZC - 0.03) - P[:, 2]),
                     (-1, -1, 0.8), (1, 1, 1.2)), 2)
        out.append(("Wing" + s, f, vs, "root", "armor"))
    # ---- the tailplanes
    f = Field("Tails")
    for sx in (-1, 1):
        f.add(facet(_tail_pts(sx), k=0.003))
        f.paint(Sphere(v3((sx * 0.36, 0.56, 0.985)), 0.06), 1)
    f.paint(Func(lambda P: P[:, 2] - F(0.984), (-1, -1, 0.8), (1, 1, 1.2)), 3)
    out.append(("Tails", f, vs, "root", "armor"))
    # ---- the canted fins (on their rudder bones), orange tips
    for s, sx in (("L", 1), ("R", -1)):
        up, side = _fin_axes(sx)
        f = Field("Fin" + s)
        f.add(facet(_fin_pts(sx), k=0.003))
        o = v3((sx * 0.125, 0.0, 1.075))
        f.paint(Func(lambda P, o=o, up=up: F(0.19) - (P - o.astype(F)) @ up.astype(F), (-1, -1, 0.9), (1, 1, 1.5)), 1)
        f.paint(Func(lambda P, o=o, up=up: np.abs((P - o.astype(F)) @ up.astype(F) - F(0.165)) - F(0.004), (-1, -1, 0.9), (1, 1, 1.5)), 2)
        out.append(("Fin" + s, f, vs, "fin." + s, "armor"))
    # ---- the engine nozzles: two square gunmetal nozzles with a fairing between them, orange rings
    f = Field("Nozzles")
    for sx in (-1, 1):
        nc = v3((sx * NOZ_X, NOZ_Y, NOZ_Z))
        f.add(RoundBox(nc, (0.062, 0.055, 0.043), 0.016), k=0.012)
        f.sub(RoundBox(nc + v3((0, 0.05, 0)), (0.044, 0.05, 0.027), 0.008), k=0.006)
        f.paint(RoundBox(nc + v3((0, -0.03, 0)), (0.08, 0.012, 0.06)), 1)
    f.add(RoundBox(v3((0, NOZ_Y - 0.03, NOZ_Z)), (0.03, 0.04, 0.03), 0.012), k=0.01)
    out.append(("Nozzles", f, vs, "root", "frame"))
    for s, sx in (("L", 1), ("R", -1)):
        nc = v3((sx * NOZ_X, NOZ_Y, NOZ_Z))
        f = Field("Exhaust" + s)
        f.add(RoundBox(nc + v3((0, 0.035, 0)), (0.042, 0.03, 0.025), 0.01))
        f.add(RoundCone(nc + v3((0, 0.05, 0)), nc + v3((0, 0.12, 0)), 0.024, 0.008), k=0.02)   # a short glowing jet
        out.append(("Exhaust" + s, f, vs, "exhaust." + s, "glow"))
    return out


# ------------------------------------------------------------------------------------------------ clips
V = lambda *a: Vector(a)


def fly(arm):
    """The weave: a lateral S (one swing each way per loop, a little second harmonic so it isn't a pendulum), banking
    into each turn (roll follows the sideways acceleration), yawing toward its sideways motion, a light bob; the
    rudders work against the turn, the exhausts pulse."""
    P = Poser(arm)
    act = ra.new_action(arm, "Fly")
    A1, A2 = 0.11, 0.025
    for f in range(FLY_FRAMES + 1):
        t = f / FLY_FRAMES
        w = 2 * math.pi * t
        x = A1 * math.sin(w) + A2 * math.sin(2 * w + 1.0)
        vx = A1 * math.cos(w) + 2 * A2 * math.cos(2 * w + 1.0)                 # (per radian)
        ax = -A1 * math.sin(w) - 4 * A2 * math.sin(2 * w + 1.0)
        roll = 3.6 * ax                                                        # bank into the turn (about 0.45 rad max)
        yaw = 1.1 * vx
        z = 0.025 * math.sin(2 * w + 0.6)
        pitch = 0.04 * math.cos(2 * w + 0.6) + 0.02
        root_rot = Quaternion(V(0, 0, 1), yaw) @ Quaternion(V(0, 1, 0), roll) @ Quaternion(V(1, 0, 0), pitch)
        aims = {}
        for s in ("L", "R"):
            aims["fin." + s] = (lambda r: (lambda P, base: (base.col[1].xyz.copy(), r)))(0.25 * math.cos(w + 0.4))
        flick = 0.5 + 0.5 * math.sin(20 * w + 1.3)
        sc = {}
        for i, s in enumerate(("L", "R")):
            p = 0.5 + 0.5 * math.sin(8 * w + i * 1.7)
            sc["exhaust." + s] = (1.0 + 0.08 * p, 1.0 + 0.45 * p + 0.12 * flick, 1.0 + 0.08 * p)
        ch, _ = P.solve(aims, root_off=V(x, 0.0, z), root_rot=root_rot, scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, FLY_FRAMES, True)


def clips(arm):
    fly(arm)
