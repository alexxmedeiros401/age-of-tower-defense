"""ORBITAL UPLINK, HQ: the Digital Age boss, a walking satellite ground station. A heavy four-legged walker: a broad
armoured hull of faceted white plates over a gunmetal belly, cyan energy conduits glowing in grooves along its flanks
and its deck, orange pinstripes and hazard stripes; at its front a faceted armoured head holding one big red sensor eye
in a bolted gunmetal bezel under a frowning brow (two small red eyes under it). On its back, on a turret ring, a
pedestal carries a big satellite dish on an elevation axle: a white parabolic bowl with panel rings and an orange rim,
gunmetal ribs behind it, three struts holding the feed at its focus where a cyan emitter glows (its EMP and its uplink).
Behind the dish rises an antenna mast banded in orange and white, with dipoles and a red beacon at its tip. In each
flank, between the legs, a hatch (a hazard-striped door hinged at its foot that drops open into a ramp, a dark bay
behind it lit cyan) from which its Nano Swarms pour out. Four splayed legs: gunmetal hip drums, white armoured thighs
with hazard bands and chrome pistons, big knees with orange caps held high, long gunmetal shins with white shin plates
and cyan conduits, round foot pads with three claws.
Walk (48 frames): a slow four-beat walk (one leg at a time: left hind, left fore, right hind, right fore), the hull
swaying over its planted feet, the dish turning slowly to scan, the mast swaying. Emp (48 frames): the dish swings to
and fro seeking, locks forward and tilts down at the enemy, its emitter charging, and fires at EMP_FIRE (a ring of
light bursts from its feed, the dish kicks back, the hull jolts). Summon (48 frames): it crouches, the dish turns up
to the sky, both hatches drop open, their bays flare and a knot of nano mites rolls out onto each ramp, released at
SUMMON_FRAME (the game's Nano Swarms take over from there); the hatches close and it rises. In every clip its feet keep
to the ground at its real speed (a stride of WALK_STEP per loop: walk_speed 0.42 = enemies.json speed).
Faces -Y, Z up; model_scale 1.0.
"""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Func, rot_from_axes, v3, norm, F,
                 smax)
from robot_stealth_jet import facet, mirror_pts, hazard, rel, smooth
import robot_nano_swarm as ns
import robot_anim as ra
from mathutils import Vector, Quaternion, Matrix
from rig import Poser, two_bone, bone_len

ROOT_NAME = "OrbitalUplink"
GLB_NAME = "orbital_uplink"
TEX_PREFIX = "orbital_uplink"
WALK_STEP = 0.84           # each foot's stride; a four-beat walk moves the body one stride per loop
WALK_FRAMES = 48           # walk_speed = 0.84 * 1.0 * 24 / 48 = 0.42 (= its speed: the clips play at 1x)
EMP_FRAMES = 48
EMP_FIRE = 22              # the dish fires its pulse here (the emitter flashes, the ring bursts from the feed)
SUMMON_FRAMES = 48
SUMMON_FRAME = 18          # the knots of mites reach the hatches' ramp lips here: the Nano Swarms are released

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.22, 0.23, 0.26)
BLACK = (0.07, 0.07, 0.08)
DECKC = (0.56, 0.58, 0.61)
RED_GLOW = (1.0, 0.16, 0.08)
CYAN = (0.3, 0.88, 1.0)

X_AX = rot_from_axes(z_axis=(1, 0, 0))
Y_AX = rot_from_axes(z_axis=(0, 1, 0))

# ---- the hull
DECK = 1.92
HULL_PTS = mirror_pts([(0.4, -0.82, 1.86), (0.56, -0.82, 1.66), (0.56, -0.82, 1.43), (0.38, -0.82, 1.24),
                       (0.5, -0.5, DECK), (0.64, -0.5, 1.7), (0.64, -0.5, 1.4), (0.46, -0.5, 1.2),
                       (0.5, 0.55, DECK), (0.64, 0.55, 1.7), (0.64, 0.55, 1.4), (0.46, 0.55, 1.2),
                       (0.42, 0.95, 1.88), (0.56, 0.95, 1.68), (0.56, 0.95, 1.44), (0.38, 0.95, 1.26)])
HULL = facet(HULL_PTS, k=0.014)
EYE_D = norm(v3((0, -0.906, 0.423)))     # the head's front is raked back: the eye looks ahead and up at the camera
EYE_U = norm(np.cross(EYE_D, v3((1, 0, 0))))
EYE_C = v3((0, -1.155, 1.6))


def _face_y(z):
    """The raked front face's y at height z."""
    return -1.15 + (z - 1.6) * 0.423 / 0.906


HEAD_PTS = mirror_pts([(0.36, -0.76, 1.86), (0.44, -0.76, 1.6), (0.34, -0.76, 1.3),
                       (0.3, _face_y(1.83), 1.83), (0.37, _face_y(1.58), 1.58), (0.3, _face_y(1.36) + 0.04, 1.34),
                       (0.0, _face_y(1.86), 1.86), (0.0, _face_y(1.32) + 0.04, 1.3)])
HEAD = facet(HEAD_PTS, k=0.012)
EYE_R = 0.17

# ---- the dish on its pedestal
TURRET = v3((0, 0.12, DECK))
PIV = v3((0, 0.12, 2.36))                  # the elevation axle (along x)
TILT0 = math.radians(33)                   # the dish's axis leans this far forward from upright
A0 = v3((0, -math.sin(TILT0), math.cos(TILT0)))
RD = rot_from_axes(z_axis=A0)              # the dish's frame (x across, z out of its bowl)
V0 = PIV + A0 * 0.17                       # the bowl's vertex
FOCAL = 0.42
DISH_R = 0.66
DISH_T = 0.03
RIM_H = DISH_R ** 2 / (4 * FOCAL)
FOC = V0 + A0 * FOCAL                      # the feed (the emitter) at the focus

# ---- the mast
MAST0 = v3((0.4, 0.8, DECK))
MAST1 = MAST0 + v3((0, 0, 0.83))
MAST2 = MAST0 + v3((0, 0, 1.5))

# ---- the hatches (one in each flank), the bays behind them
HATCH_Z0, HATCH_Z1 = 1.43, 1.69
HATCH_HY = 0.25
HINGE_X = 0.655
DOOR_OPEN = math.radians(104)

# ---- the legs
LEGS = {}
for _n, _sx, _sy in (("LF", 1, -1), ("RF", -1, -1), ("LH", 1, 1), ("RH", -1, 1)):
    _y0 = -0.58 if _sy < 0 else 0.64
    LEGS[_n] = {"hip": v3((_sx * 0.56, _y0, 1.42)), "knee": v3((_sx * 1.08, _y0 + _sy * 0.2, 2.02)),
                "ankle": v3((_sx * 1.3, _y0 + _sy * 0.37, 0.26)), "sx": _sx, "sy": _sy}
PHASE = {"RF": 0.0, "RH": 0.25, "LF": 0.5, "LH": 0.75}   # each foot swings while (t + PHASE) % 1 >= 0.75: LH, LF, RH, RF

BONES = [
    ("root", (0, 0.05, 1.55), (0, 0.05, 1.8), None),
    ("eye", tuple(EYE_C - EYE_D * 0.1), tuple(EYE_C + EYE_D * 0.06), "root"),
    ("turret", tuple(TURRET), tuple(TURRET + v3((0, 0, 0.3))), "root"),
    ("dish", tuple(PIV), tuple(V0), "turret"),
    ("emitter", tuple(FOC - A0 * 0.05), tuple(FOC + A0 * 0.1), "dish"),
    ("pulse", tuple(FOC + A0 * 0.02), tuple(FOC + A0 * 0.2), "dish"),
    ("mast", tuple(MAST0), tuple(MAST1), "root"),
    ("mast2", tuple(MAST1), tuple(MAST2), "mast"),
    ("beacon", tuple(MAST2), tuple(MAST2 + v3((0, 0, 0.12))), "mast2"),
]
for _s, _sx in (("L", 1), ("R", -1)):
    BONES += [
        ("hatch." + _s, (_sx * HINGE_X, 0.0, HATCH_Z0), (_sx * HINGE_X, 0.0, HATCH_Z1), "root"),
        ("bay." + _s, (_sx * 0.445, 0.0, 1.555), (_sx * 0.6, 0.0, 1.555), "root"),
        ("spill." + _s, (_sx * 0.56, 0.0, 1.56), (_sx * 0.56, 0.0, 1.7), None),          # (parentless: it moves)
    ]
for _n, _L in LEGS.items():
    BONES += [("thigh." + _n, tuple(_L["hip"]), tuple(_L["knee"]), "root"),
              ("shin." + _n, tuple(_L["knee"]), tuple(_L["ankle"]), "thigh." + _n),
              ("foot." + _n, tuple(_L["ankle"]), tuple(_L["ankle"] - v3((0, 0, 0.2))), "shin." + _n)]

MATS = {
    "armor": ("armor", dict(name="RB_UplinkArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.42), (4, BLACK, 0.45),
                                                           (5, DECKC, 0.5)], seams=[2], wear=1.1, scale=2.0)),
    "frame": ("gunmetal", dict(name="RB_UplinkFrame", base=(0.21, 0.22, 0.25), labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6),
                                                                                        (4, BLACK, 0.5)], seams=[2], scale=2.0)),
    "chrome": ("chrome", dict(name="RB_UplinkChrome")),
    "socket": ("lens_socket", dict(name="RB_UplinkSocket")),
    "glow": ("glow", dict(name="RB_UplinkGlow", col=CYAN)),
}
GLOW = {"Eye": (RED_GLOW, 1.6, 0.5), "SmallEyes": (RED_GLOW, 1.5, 0.5), "Beacon": (RED_GLOW, 1.6, 0.5),
        "Conduits": (CYAN, 1.4, 0.55), "Emitter": (CYAN, 1.6, 0.6), "Pulse": (CYAN, 1.8, 0.7)}
LOW_TARGETS = {"Hull": 2400, "Belly": 300, "Head": 700, "Brow": 160, "Bezel": 360, "Eye": 120, "Pupil": 50, "SmallEyes": 60,
               "Turret": 520, "Dish": 1300, "DishBack": 650, "Feed": 360, "Emitter": 90, "Pulse": 140, "Mast": 450, "Mast2": 280,
               "Beacon": 40, "Conduits": 420, "Rack": 260}
for _s in "LR":
    GLOW["BayGlow" + _s] = (CYAN, 1.3, 0.55)
    GLOW["SpillEyes" + _s] = (RED_GLOW, 1.6, 0.5)
    LOW_TARGETS.update({"Door" + _s: 220, "BayGlow" + _s: 30, "Spill" + _s: 380, "SpillEyes" + _s: 40})
for _n in LEGS:
    GLOW["LegGlow" + _n] = (CYAN, 1.4, 0.55)
    LOW_TARGETS.update({"Hip" + _n: 220, "Thigh" + _n: 330, "Piston" + _n: 110, "Knee" + _n: 230, "KneeCap" + _n: 140,
                        "Shin" + _n: 230, "ShinPlate" + _n: 200, "LegGlow" + _n: 50, "Foot" + _n: 330})


# ------------------------------------------------------------------------------------------------ shapes
def _dish_local(P):
    return (P - V0.astype(F)) @ RD.astype(F)


def _dish_d(q):
    """Signed distance (approx.) to the bowl's paraboloid, + in front (the concave side), and the radius r."""
    r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
    s = r * r / F(4 * FOCAL)
    return (q[:, 2] - s) / np.sqrt(F(1) + (r / F(2 * FOCAL)) ** 2), r


def dish_sd(P):
    d, r = _dish_d(_dish_local(P))
    return smax(np.abs(d) - F(DISH_T / 2), r - F(DISH_R), 0.008)


def ribs_sd(P):
    q = _dish_local(P)
    d, r = _dish_d(q)
    phi = np.arctan2(q[:, 1], q[:, 0])
    k = np.round(phi / F(math.pi / 4)) * F(math.pi / 4)
    slab = r * np.abs(np.sin(phi - k)) - F(0.017)
    h = F(0.08) - F(0.05) * np.clip(r / F(DISH_R), 0, 1)
    depth = np.abs(d + h / 2) - h / 2
    return np.maximum(np.maximum(slab, depth), np.maximum(r - F(DISH_R - 0.03), F(0.09) - r))


def _hull_band(P, z):
    """Within the hull's flank band near height z (for painted flank stripes)."""
    return np.abs(P[:, 2] - F(z))


def _ramp_lip(sx):
    """The open ramp's far edge (rest space)."""
    a = DOOR_OPEN
    return v3((sx * (HINGE_X + (HATCH_Z1 - HATCH_Z0) * math.sin(a)), 0.0, HATCH_Z0 + (HATCH_Z1 - HATCH_Z0) * math.cos(a)))


SPILL_OUT = {sx: v3((sx * 0.9, 0.0, 1.535)) - v3((sx * 0.56, 0.0, 1.56)) for sx in (-1, 1)}   # the knot's way out


def _spill_mites(sx):
    """A knot of eight small mites (the Nano Swarm's mites, smaller) round the spill bone's head."""
    c0 = v3((sx * 0.56, 0.0, 1.56))
    rng = np.random.default_rng(11 if sx > 0 else 12)
    out = []
    ga = math.pi * (3 - 5 ** 0.5)
    n = 9
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        u = norm(v3((r * math.cos(ga * i), r * math.sin(ga * i), z)) + rng.normal(0, 0.08, 3))
        t0 = norm(np.cross(u, v3((0, 0, 1))) if abs(u[2]) < 0.95 else np.cross(u, v3((1, 0, 0))))
        a = float(rng.uniform(0, 2 * math.pi))
        fwd = norm(t0 * math.cos(a) + np.cross(u, t0) * math.sin(a))
        out.append((c0 + u * 0.085, u, fwd, 0.62))
    return out


def parts(fine=False):
    vx = 0.008 if fine else 0.014
    vs = 0.0055 if fine else 0.01
    vt = 0.0034 if fine else 0.0062            # (the spilling mites)
    out = []
    # ---- the hull: faceted white plates, the bays cut into its flanks, conduit grooves, panel lines and stripes
    f = Field("Hull")
    f.add(HULL)
    for sx in (-1, 1):
        f.sub(RoundBox((sx * 0.62, 0.0, (HATCH_Z0 + HATCH_Z1) / 2), (0.19, HATCH_HY, (HATCH_Z1 - HATCH_Z0) / 2), 0.025), k=0.01)
        f.sub(RoundCone((sx * 0.585, -0.5, 1.8), (sx * 0.585, 0.56, 1.8), 0.032), k=0.008)          # the flank conduit's groove
        f.sub(RoundCone((sx * 0.17, -0.06, DECK + 0.01), (sx * 0.17, -0.72, DECK + 0.01), 0.03), k=0.008)   # the deck's
    f.paint(Func(lambda P: P[:, 2] - F(1.3), (-1, -1.3, 1.0), (1, 1.3, 2.1)), 3)                         # the belly
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(1.315)) - F(0.004), (-1, -1.3, 1.0), (1, 1.3, 2.1)), 2)
    f.paint(Func(lambda P: np.maximum(F(DECK - 0.03) - P[:, 2], np.abs(P[:, 0]) - F(0.42)), (-1, -1.3, 1.0), (1, 1.3, 2.1)), 5)  # the deck
    for y in (-0.38, 0.4, 0.78):
        f.paint(RoundBox((0, y, 1.6), (0.8, 0.004, 0.42)), 2)                                    # plate seams
    for sx in (-1, 1):
        f.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 2] - F(1.725)) - F(0.016), F(0.5) - P[:, 0] * F(sx)),
                     (-1, -1.3, 1.0), (1, 1.3, 2.1)), 1)                                       # an orange pinstripe
        f.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 2] - F(1.38)) - F(0.008), F(0.5) - P[:, 0] * F(sx)),
                     (-1, -1.3, 1.0), (1, 1.3, 2.1)), 1)
        # hazard stripes framing the hatch, the bay's inside dark
        hazard(f, (sx * 0.5 - 0.3, -HATCH_HY - 0.07, HATCH_Z0 - 0.05), (sx * 0.5 + 0.3, HATCH_HY + 0.07, HATCH_Z1 + 0.05), w=0.07, d=(0, 1, 1),
               band=lambda P: -np.maximum(np.abs(P[:, 1]) - F(HATCH_HY + 0.01), np.maximum(F(HATCH_Z0 - 0.01) - P[:, 2], P[:, 2] - F(HATCH_Z1 + 0.01))))
        f.paint(RoundBox((sx * 0.55, 0.0, (HATCH_Z0 + HATCH_Z1) / 2), (0.16, HATCH_HY + 0.005, (HATCH_Z1 - HATCH_Z0) / 2 + 0.005), 0.02), 4)
    hazard(f, (-0.5, -0.8, DECK - 0.06), (0.5, -0.62, DECK + 0.05), w=0.08, d=(1, 1, 0))             # across the deck's front
    out.append(("Hull", f, vx, "root", "armor"))
    # ---- the belly: a gunmetal keel with vents, the hips' frame
    f = Field("Belly")
    f.add(RoundBox((0, 0.03, 1.2), (0.36, 0.72, 0.05), 0.03))
    for i in range(6):
        f.sub(RoundBox((0, -0.45 + 0.18 * i, 1.15), (0.24, 0.03, 0.03), 0.01), k=0.004)
    out.append(("Belly", f, vs, "root", "frame"))
    # ---- the head at its front: faceted armour round the big eye, a hazard chin, brows, two small eyes
    f = Field("Head")
    f.add(HEAD)
    f.sub(Sphere(EYE_C - EYE_D * 0.025, EYE_R + 0.035), k=0.015)
    f.paint(Func(lambda P: P[:, 2] - F(1.3), (-1, -1.4, 1.1), (1, -0.6, 2.0)), 3)
    hazard(f, (-0.5, -1.3, 1.29), (0.5, -0.9, 1.4), w=0.07, d=(1, 0, 1))
    f.paint(Func(lambda P: np.abs(P[:, 1] - F(-0.95)) - F(0.022), (-1, -1.4, 1.1), (1, -0.6, 2.0)), 1)
    out.append(("Head", f, vx, "root", "armor"))
    f = Field("Brow")                                         # two angled plates over the eye: a frown
    for sx in (-1, 1):
        xa = v3((1, 0, 0)) + EYE_U * (sx * 0.42)
        f.add(RoundBox(EYE_C + v3((sx * 0.1, 0, 0)) + EYE_U * 0.215 + EYE_D * 0.035, (0.115, 0.06, 0.028), 0.022,
                       R=rot_from_axes(x_axis=xa, y_axis=EYE_D - EYE_U * 0.5)), k=0.02)
    f.paint(Sphere(EYE_C, 1.0), 3)
    f.paint(Func(lambda P: (P - EYE_C.astype(F)) @ (-EYE_D).astype(F) + F(0.065), EYE_C - 0.5, EYE_C + 0.5), 1)
    out.append(("Brow", f, vs, "root", "armor"))
    Re = rot_from_axes(z_axis=EYE_D)
    f = Field("Bezel")
    f.add(Torus(EYE_C - EYE_D * 0.005, EYE_R + 0.012, 0.034, R=Re))
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        f.add(Sphere(EYE_C + Re @ v3((math.cos(a) * (EYE_R + 0.012), math.sin(a) * (EYE_R + 0.012), 0.03)), 0.016), k=0.006)
    out.append(("Bezel", f, vs, "root", "frame"))
    f = Field("Eye")
    f.add(Ellipsoid(EYE_C - EYE_D * 0.01, (EYE_R, EYE_R, 0.065), R=Re))
    out.append(("Eye", f, vs, "eye", "glow"))
    f = Field("Pupil")
    f.add(Ellipsoid(EYE_C + EYE_D * 0.052, (0.055, 0.055, 0.013), R=Re))
    out.append(("Pupil", f, vs * 0.8, "eye", "socket"))
    f = Field("SmallEyes")
    for sx in (-1, 1):
        f.add(Sphere(EYE_C - EYE_U * 0.19 + v3((sx * 0.22, 0, 0)) - EYE_D * 0.005, 0.032))
    out.append(("SmallEyes", f, vs, "root", "glow"))
    # ---- the turret on the deck and the pedestal with its axle housing
    f = Field("Turret")
    f.add(Cylinder(TURRET + v3((0, 0, 0.045)), 0.31, 0.09, rr=0.025))
    f.add(Torus(TURRET + v3((0, 0, 0.012)), 0.32, 0.022), k=0.008)
    for i in range(12):
        a = i * math.pi / 6
        f.add(Sphere(TURRET + v3((0.27 * math.cos(a), 0.27 * math.sin(a), 0.093)), 0.016), k=0.004)
    f.add(RoundCone(TURRET + v3((0, 0, 0.08)), PIV - v3((0, 0, 0.06)), 0.15, 0.1), k=0.03)            # the pedestal
    f.add(Cylinder(PIV, 0.075, 0.27, rr=0.015, R=X_AX), k=0.02)                                      # the axle housing
    f.paint(Torus(TURRET + v3((0, 0, 0.012)), 0.32, 0.03), 1)
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(2.2)) - F(0.02), PIV - 0.5, PIV + 0.5), 1)
    out.append(("Turret", f, vs, "turret", "frame"))
    # ---- the dish: the bowl (white, panel rings, an orange rim, gunmetal back), the rim's lip
    lo, hi = V0 - 0.8, V0 + 0.8
    f = Field("Dish")
    f.add(Func(dish_sd, lo, hi))
    f.add(Torus(V0 + A0 * RIM_H, DISH_R - 0.012, 0.028, R=RD), k=0.012)
    f.paint(Func(lambda P: _dish_d(_dish_local(P))[0], lo, hi), 3)                                    # the back
    for rr in (0.24, 0.45):
        f.paint(Func(lambda P, rr=rr: np.maximum(np.abs(_dish_d(_dish_local(P))[1] - F(rr)) - F(0.005),
                                                 -_dish_d(_dish_local(P))[0]), lo, hi), 2)
    f.paint(Func(lambda P: np.maximum(np.abs(np.arctan2(_dish_local(P)[:, 1], _dish_local(P)[:, 0]) % F(math.pi / 3) - F(math.pi / 6)) * _dish_d(_dish_local(P))[1] - F(0.004),
                                      np.maximum(F(0.245) - _dish_d(_dish_local(P))[1], -_dish_d(_dish_local(P))[0])), lo, hi), 2)
    f.paint(Func(lambda P: F(DISH_R - 0.07) - _dish_d(_dish_local(P))[1], lo, hi), 1)                  # the orange rim
    out.append(("Dish", f, vx, "dish", "armor"))
    # its back: the ribs, the hub on the axle with its two cheek plates
    f = Field("DishBack")
    f.add(Func(ribs_sd, lo, hi))
    f.add(Cylinder((PIV + V0) / 2 - A0 * 0.02, 0.13, 0.2, rr=0.03, R=RD), k=0.03)
    f.add(Torus(V0 - A0 * 0.04, 0.16, 0.03, R=RD), k=0.02)
    for sx in (-1, 1):
        f.add(RoundBox(PIV + v3((sx * 0.165, 0, 0)), (0.03, 0.13, 0.13), 0.025, R=RD), k=0.02)
        f.add(Cylinder(PIV + v3((sx * 0.19, 0, 0)), 0.055, 0.04, rr=0.012, R=X_AX), k=0.008)
    f.paint(Torus(V0 - A0 * 0.04, 0.16, 0.035, R=RD), 1)
    out.append(("DishBack", f, vs, "dish", "frame"))
    # the feed: three struts from the rim to the housing at the focus
    f = Field("Feed")
    fh = FOC - A0 * 0.06
    f.add(Cylinder(fh, 0.075, 0.1, rr=0.02, R=RD))
    f.add(RoundCone(fh - A0 * 0.05, fh - A0 * 0.13, 0.05, 0.02), k=0.02)
    for i in range(3):
        a = math.pi / 2 + i * 2 * math.pi / 3
        rp = V0 + RD @ v3((math.cos(a) * (DISH_R - 0.04), math.sin(a) * (DISH_R - 0.04), (DISH_R - 0.04) ** 2 / (4 * FOCAL)))
        f.add(RoundCone(rp, fh + RD @ v3((math.cos(a) * 0.05, math.sin(a) * 0.05, 0)), 0.018, 0.015), k=0.01)
    f.add(Torus(FOC - A0 * 0.012, 0.072, 0.016, R=RD), k=0.008)
    f.paint(Torus(FOC - A0 * 0.012, 0.075, 0.02, R=RD), 1)
    out.append(("Feed", f, vs, "dish", "frame"))
    f = Field("Emitter")
    f.add(Ellipsoid(FOC + A0 * 0.0, (0.058, 0.058, 0.04), R=RD))
    out.append(("Emitter", f, vs, "emitter", "glow"))
    f = Field("Pulse")                                    # the pulse's ring of light (hidden until the EMP fires)
    pc = FOC + A0 * 0.06
    f.add(Torus(pc, 0.2, 0.03, R=RD))
    f.add(Ellipsoid(pc, (0.13, 0.13, 0.018), R=RD), k=0.03)
    out.append(("Pulse", f, vs, "pulse", "glow"))
    # ---- the mast: a banded pole in two sections, dipoles, the beacon at its tip
    f = Field("Mast")
    f.add(RoundBox(MAST0 + v3((0, 0, 0.05)), (0.11, 0.11, 0.07), 0.03))
    f.add(RoundCone(MAST0 + v3((0, 0, 0.1)), MAST1, 0.048, 0.036), k=0.015)
    f.add(Cylinder(MAST1, 0.048, 0.04, rr=0.01), k=0.006)
    for z, half in ((0.42, 0.16), (0.66, 0.11)):
        c = MAST0 + v3((0, 0, z))
        f.add(Cylinder(c, 0.012, half * 2, rr=0.006, R=X_AX), k=0.006)
        for sx in (-1, 1):
            f.add(Sphere(c + v3((sx * half, 0, 0)), 0.02), k=0.004)
    for i, (z0, z1) in enumerate(((0.16, 0.26), (0.38, 0.48), (0.6, 0.7))):
        f.paint(Func(lambda P, z0=z0, z1=z1: np.maximum(F(MAST0[2] + z0) - P[:, 2], P[:, 2] - F(MAST0[2] + z1)), MAST0 - 1, MAST0 + 2), 1)
    f.paint(RoundBox(MAST0 + v3((0, 0, 0.05)), (0.2, 0.2, 0.08)), 3)
    out.append(("Mast", f, vs, "mast", "armor"))
    f = Field("Mast2")
    f.add(RoundCone(MAST1, MAST2, 0.032, 0.02))
    for z, half in ((0.25, 0.12), (0.5, 0.08)):
        c = MAST1 + v3((0, 0, z))
        f.add(Cylinder(c, 0.01, half * 2, rr=0.005, R=Y_AX), k=0.005)
        for sy in (-1, 1):
            f.add(Sphere(c + v3((0, sy * half, 0)), 0.017), k=0.004)
    f.add(Cylinder(MAST2 + v3((0, 0, 0.0)), 0.034, 0.05, rr=0.01), k=0.006)
    for z0, z1 in ((0.08, 0.18), (0.32, 0.42), (0.56, 0.66)):
        f.paint(Func(lambda P, z0=z0, z1=z1: np.maximum(F(MAST1[2] + z0) - P[:, 2], P[:, 2] - F(MAST1[2] + z1)), MAST1 - 1, MAST1 + 1), 1)
    out.append(("Mast2", f, vs, "mast2", "armor"))
    f = Field("Beacon")
    f.add(Sphere(MAST2 + v3((0, 0, 0.055)), 0.042))
    out.append(("Beacon", f, vs, "beacon", "glow"))
    # ---- an equipment rack on the rear deck, opposite the mast: a gunmetal cabinet with cooling fins
    f = Field("Rack")
    rc = v3((-0.27, 0.74, DECK + 0.11))
    f.add(RoundBox(rc, (0.15, 0.13, 0.11), 0.025))
    for i in range(5):
        f.add(RoundBox(rc + v3((-0.15, -0.09 + 0.045 * i, 0.0)), (0.025, 0.008, 0.08), 0.006), k=0.004)
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(rc[2] + 0.07)) - F(0.015), rc - 0.3, rc + 0.3), 1)
    f.paint(RoundBox(rc + v3((0, -0.13, -0.02)), (0.1, 0.01, 0.05), 0.01), 4)
    out.append(("Rack", f, vs, "root", "frame"))
    # ---- the conduits glowing in their grooves (flanks and deck)
    f = Field("Conduits")
    for sx in (-1, 1):
        f.add(RoundCone((sx * 0.585, -0.5, 1.8), (sx * 0.585, 0.56, 1.8), 0.021))
        f.add(RoundCone((sx * 0.17, -0.06, DECK + 0.01), (sx * 0.17, -0.72, DECK + 0.01), 0.02))
    out.append(("Conduits", f, vs, "root", "glow"))
    # ---- the hatches: doors (hinged at their feet), the bays' glow panels, the knots of mites waiting inside
    for s, sx in (("L", 1), ("R", -1)):
        hz = (HATCH_Z0 + HATCH_Z1) / 2
        f = Field("Door" + s)
        c = v3((sx * HINGE_X, 0.0, hz))
        f.add(RoundBox(c, (0.022, HATCH_HY + 0.012, (HATCH_Z1 - HATCH_Z0) / 2 + 0.008), 0.012))
        f.add(Cylinder(v3((sx * HINGE_X, 0.0, HATCH_Z0)), 0.026, HATCH_HY * 2 + 0.02, rr=0.008, R=Y_AX), k=0.006)   # its hinge
        hazard(f, c - v3((0.05, HATCH_HY, 0.125)), c + v3((0.05, HATCH_HY, 0.125)), w=0.075, d=(0, 1, 1),
               band=lambda P, sx=sx: F(HINGE_X + 0.012) - P[:, 0] * F(sx))
        f.paint(Func(lambda P, sx=sx: P[:, 0] * F(sx) - F(HINGE_X - 0.008), c - 0.4, c + 0.4), 3)     # its inner face (the ramp)
        for k in range(4):
            f.paint(Func(lambda P, sx=sx, k=k: np.maximum(np.abs(P[:, 2] - F(HATCH_Z0 + 0.05 + 0.055 * k)) - F(0.008),
                                                          P[:, 0] * F(sx) - F(HINGE_X - 0.008)), c - 0.4, c + 0.4), 4)
        out.append(("Door" + s, f, vs, "hatch." + s, "armor"))
        f = Field("BayGlow" + s)
        f.add(RoundBox(v3((sx * 0.44, 0.0, hz)), (0.012, HATCH_HY - 0.05, (HATCH_Z1 - HATCH_Z0) / 2 - 0.04), 0.01))
        out.append(("BayGlow" + s, f, vs, "bay." + s, "glow"))
        f = Field("Spill" + s)
        ge = Field("SpillEyes" + s)
        f.add(Sphere(v3((sx * 0.56, 0.0, 1.56)), 0.07))
        for c, u, fwd, sz in _spill_mites(sx):
            ns.mite(f, c, u, fwd, sz)
            ns.eye(ge, c, u, fwd, sz)
        out.append(("Spill" + s, f, vt, "spill." + s, "armor"))
        out.append(("SpillEyes" + s, ge, vt, "spill." + s, "glow"))
    # ---- the legs
    for n, L in LEGS.items():
        hp, kn, an, sx = L["hip"], L["knee"], L["ankle"], L["sx"]
        tax, sax = norm(kn - hp), norm(an - kn)
        Rt = rot_from_axes(z_axis=tax, x_axis=(sx, 0, 0))
        Rs = rot_from_axes(z_axis=sax, x_axis=(sx, 0, 0))
        f = Field("Hip" + n)                                         # the hip drum on the hull's corner
        f.add(Cylinder(hp - v3((sx * 0.06, 0, 0)), 0.17, 0.15, rr=0.03, R=X_AX))
        f.add(Sphere(hp, 0.13), k=0.02)
        f.paint(Torus(hp - v3((sx * 0.0, 0, 0)), 0.17, 0.025, R=X_AX), 1)
        out.append(("Hip" + n, f, vs, "root", "frame"))
        f = Field("Thigh" + n)                                       # a white armoured thigh, hazard band at the knee end
        tl = float(np.linalg.norm(kn - hp))
        f.add(RoundBox(hp + tax * (tl * 0.52) + Rt @ v3((0, 0, 0)), (0.12, 0.11, tl * 0.42), 0.05, R=Rt))
        f.add(RoundBox(hp + tax * (tl * 0.52) + Rt @ v3((0.0, 0.0, 0.0)) + v3((0, 0, 0.07)), (0.05, 0.04, tl * 0.36), 0.03, R=Rt), k=0.03)
        hazard(f, hp + tax * (tl * 0.72) - 0.3, hp + tax * (tl * 0.86) + 0.3, w=0.06, d=(1, 1, 1),
               band=lambda P, o=hp + tax * (tl * 0.79), ax=tax: np.abs((P - o.astype(F)) @ ax.astype(F)) - F(tl * 0.07))
        f.paint(Func(lambda P, o=hp + tax * (tl * 0.4), ax=tax: np.abs((P - o.astype(F)) @ ax.astype(F)) - F(0.004), hp - 1, hp + 1.5), 2)
        out.append(("Thigh" + n, f, vx, "thigh." + n, "armor"))
        f = Field("Piston" + n)                                      # a chrome piston under the thigh
        f.add(RoundCone(hp + tax * 0.15 + v3((0, 0, -0.1)), hp + tax * (tl * 0.85) + v3((0, 0, -0.1)), 0.03))
        out.append(("Piston" + n, f, vs, "thigh." + n, "chrome"))
        f = Field("Knee" + n)                                        # the knee: a big ball on an axle
        f.add(Sphere(kn, 0.13))
        f.add(Cylinder(kn, 0.1, 0.32, rr=0.03, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.02)
        out.append(("Knee" + n, f, vs, "shin." + n, "frame"))
        f = Field("KneeCap" + n)                                     # an orange cap over it (it reads from above)
        f.add(Ellipsoid(kn + v3((sx * 0.02, 0, 0.07)), (0.15, 0.17, 0.09)))
        f.sub(Sphere(kn - v3((0, 0, 0.02)), 0.12), k=0.02)
        f.paint(Sphere(kn, 1.0), 1)
        f.paint(Func(lambda P, kn=kn: np.abs(P[:, 0] - F(kn[0])) - F(0.004), kn - 0.3, kn + 0.3), 2)
        out.append(("KneeCap" + n, f, vs, "shin." + n, "armor"))
        f = Field("Shin" + n)                                        # a long gunmetal strut down to the ankle ball
        f.add(RoundCone(kn + sax * 0.1, an, 0.105, 0.08))
        f.add(Sphere(an, 0.115), k=0.02)
        f.paint(Func(lambda P, o=an, ax=sax: np.abs((P - o.astype(F)) @ ax.astype(F) + F(0.2)) - F(0.025), an - 0.5, an + 0.5), 1)
        out.append(("Shin" + n, f, vs, "shin." + n, "frame"))
        sl = float(np.linalg.norm(an - kn))
        f = Field("ShinPlate" + n)                                   # a white plate down its outer face
        pc = kn + sax * (sl * 0.45) + v3((sx * 0.095, 0, 0))
        f.add(RoundBox(pc, (0.045, 0.13, sl * 0.3), 0.035, R=Rs))
        f.sub(RoundBox(pc + v3((sx * 0.04, 0, 0)), (0.02, 0.022, sl * 0.26), 0.01, R=Rs), k=0.006)    # the conduit's channel
        f.paint(Func(lambda P, o=pc, ax=sax: np.abs(np.abs((P - o.astype(F)) @ ax.astype(F)) - F(sl * 0.27)) - F(0.012), pc - 1, pc + 1), 1)
        out.append(("ShinPlate" + n, f, vs, "shin." + n, "armor"))
        f = Field("LegGlow" + n)
        f.add(RoundBox(pc + v3((sx * 0.035, 0, 0)), (0.012, 0.015, sl * 0.25), 0.011, R=Rs))
        out.append(("LegGlow" + n, f, vs, "shin." + n, "glow"))
        f = Field("Foot" + n)                                        # a round pad with three claws
        f.add(Cylinder(an - v3((0, 0, 0.19)), 0.25, 0.13, rr=0.045))
        f.add(RoundCone(an - v3((0, 0, 0.12)), an - v3((0, 0, 0.02)), 0.15, 0.09), k=0.03)
        for a in (-0.7, 0.0, 0.7):
            d = norm(v3((math.sin(a) * sx * 0.6 + sx * 0.5, L["sy"] * math.cos(a) * 0.8, 0)))
            f.add(RoundCone(an - v3((0, 0, 0.18)) + d * 0.18, an - v3((0, 0, 0.21)) + d * 0.33, 0.05, 0.022), k=0.025)
            f.paint(Sphere(an - v3((0, 0, 0.21)) + d * 0.33, 0.06), 1)
        f.paint(Func(lambda P, an=an: P[:, 2] - F(an[2] - 0.235), an - 0.6, an + 0.6), 4)
        out.append(("Foot" + n, f, vs, "foot." + n, "frame"))
    return out


# ------------------------------------------------------------------------------------------------ clips
V = lambda *a: Vector(a)


def _leg(arm, n, ankle, pitch=0.0):
    L = LEGS[n]
    la, lb = bone_len(arm, "thigh." + n), bone_len(arm, "shin." + n)
    pole = V(L["sx"] * 0.7, 0.0, 1.0)
    st = {}
    def thigh(P, base):
        hip = base.translation
        knee = two_bone(hip, ankle, la, lb, pole)
        st["knee"] = knee
        return knee - hip
    def shin(P, base):
        return Vector(ankle) - st["knee"]
    down = Quaternion(V(1, 0, 0), -pitch) @ V(0, 0, -1)
    fwd = Quaternion(V(1, 0, 0), -pitch) @ V(0, -1, 0)
    return {"thigh." + n: thigh, "shin." + n: shin, "foot." + n: ("frame", V(0, 0, -1), down, V(0, -1, 0), fwd)}


def gait(arm, t, step=WALK_STEP, lift=0.24):
    """The four-beat walk at loop time t: each foot planted three quarters of the loop (sliding back under the body)
    and swung forward the last quarter, lifted, its pad tipped up a little."""
    aims = {}
    for n, L in LEGS.items():
        ph = (t + PHASE[n]) % 1.0
        if ph < 0.75:
            y, z, p = -step / 2 + step * ph / 0.75, 0.0, 0.0
        else:
            k = (ph - 0.75) / 0.25
            e = 0.5 - 0.5 * math.cos(math.pi * k)
            y = step / 2 - step * e
            z = lift * math.sin(math.pi * k) ** 1.4
            p = 0.25 * math.sin(math.pi * k) * (1.2 - k)
        aims.update(_leg(arm, n, Vector(L["ankle"]) + V(0, y, z), p))
    return aims


def _body(t):
    """The hull's sway over its planted feet and its dip at each footfall (four a loop)."""
    w = 2 * math.pi * t
    sway = -0.04 * math.sin(w)                       # away from the side whose legs are swinging (left: t in 0..0.5)
    dip = -0.022 * (0.5 + 0.5 * math.cos(4 * w))
    return V(sway, 0.0, dip + 0.011), Quaternion(V(0, 1, 0), 0.025 * math.sin(w)) @ Quaternion(V(1, 0, 0), 0.012 * math.sin(2 * w))


def _yaw(a):
    return lambda P, base: (base.col[1].xyz.copy(), a)


def _dish(arm, tilt):
    """The dish's axis leaning `tilt` (rad) forward from upright, in the turret's frame."""
    return rel(arm, "dish", (0.0, -math.sin(tilt), math.cos(tilt)))


def _spill(arm, sx, off, roll):
    """The knot of mites moved by `off` (rest space, carried by the hull's pose) and rolled about its own centre."""
    name = "spill." + ("L" if sx > 0 else "R")
    rest = arm.data.bones[name].matrix_local.copy()
    rr = arm.data.bones["root"].matrix_local.inverted()
    def fn(P, base):
        T = P["root"] @ rr
        M = Matrix.Translation(Vector(off)) @ Matrix.Translation(rest.translation) @ \
            Quaternion(V(0, 1, 0), -sx * roll).to_matrix().to_4x4() @ Matrix.Translation(-rest.translation) @ rest
        return ("world", T @ M)
    return fn


def _hatches(arm, ang):
    return {"hatch.L": rel(arm, "hatch.L", (math.sin(ang), 0.0, math.cos(ang))),
            "hatch.R": rel(arm, "hatch.R", (-math.sin(ang), 0.0, math.cos(ang)))}


HIDE = 0.01


def walk(arm):
    """The slow four-beat walk: the hull sways over its planted feet, the turret turns the dish slowly to scan, the mast
    sways, the eye looks about, the beacon blinks."""
    P = Poser(arm)
    act = ra.new_action(arm, "Walk")
    for f in range(WALK_FRAMES + 1):
        t = f / WALK_FRAMES
        w = 2 * math.pi * t
        aims = gait(arm, t)
        root_off, root_rot = _body(t)
        aims["turret"] = _yaw(0.16 * math.sin(w))
        aims["dish"] = _dish(arm, TILT0 + 0.04 * math.sin(2 * w + 0.5))
        aims["mast"] = rel(arm, "mast", (0.03 * math.sin(w - 0.6), 0.015 * math.sin(2 * w - 0.6), 1.0))
        aims["mast2"] = rel(arm, "mast2", (0.07 * math.sin(w - 1.2), 0.03 * math.sin(2 * w - 1.2), 1.0))
        look = 0.28 * math.sin(w + 0.8)
        aims["eye"] = rel(arm, "eye", Quaternion(V(0, 0, 1), look) @ Vector(EYE_D))
        aims.update(_hatches(arm, 0.0))
        for sx in (-1, 1):
            aims["spill." + ("L" if sx > 0 else "R")] = _spill(arm, sx, (0, 0, 0), 0.0)
        blink = 1.0 if (f // 6) % 4 else 1.25
        sc = {"pulse": HIDE, "spill.L": HIDE, "spill.R": HIDE, "beacon": blink, "emitter": 1.0 + 0.08 * math.sin(4 * w)}
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, WALK_FRAMES, True)


def emp(arm):
    """The dish swings to and fro seeking (0-18), locks forward and tilts down at the enemy while the emitter charges
    (flickering brighter), and at EMP_FIRE the pulse fires: the ring of light bursts out of the feed and spreads, the
    emitter flashes, the dish kicks back and the hull jolts; then the dish settles back (28-46). The legs walk on."""
    P = Poser(arm)
    act = ra.new_action(arm, "Emp")
    for f in range(EMP_FRAMES + 1):
        t = f / EMP_FRAMES
        w = 2 * math.pi * t
        aims = gait(arm, t)
        root_off, root_rot = _body(t)
        brace = smooth(10, 20, f) * (1.0 - smooth(30, 44, f))
        jolt = kick = 0.0
        if f >= EMP_FIRE:
            u = f - EMP_FIRE
            jolt = 0.05 * math.exp(-u * 0.4) * math.cos(u * 1.3)
            kick = 0.22 * math.exp(-u * 0.32)
        root_off = root_off + V(0.0, jolt * 0.8, -0.05 * brace)
        root_rot = Quaternion(V(1, 0, 0), -0.04 * jolt / 0.05) @ root_rot
        # the swing: left, right, then locked forward
        u = smooth(0, 18, f)
        yaw = -0.45 * math.sin(2 * math.pi * u) * math.sqrt(1.0 - u)       # the swing: left, back to the right, locked
        aims["turret"] = _yaw(yaw)
        tilt = TILT0 + 0.42 * smooth(6, 19, f) * (1.0 - smooth(30, 46, f)) - kick
        aims["dish"] = _dish(arm, tilt)
        aims["mast"] = rel(arm, "mast", (0.03 * math.sin(w - 0.6) - 0.0, 0.02 * jolt / 0.05, 1.0))
        aims["mast2"] = rel(arm, "mast2", (0.07 * math.sin(w - 1.2), 0.06 * jolt / 0.05, 1.0))
        aims["eye"] = rel(arm, "eye", Vector(EYE_D))
        aims.update(_hatches(arm, 0.0))
        for sx in (-1, 1):
            aims["spill." + ("L" if sx > 0 else "R")] = _spill(arm, sx, (0, 0, 0), 0.0)
        if f < EMP_FIRE:
            em = 1.0 + 0.8 * smooth(4, EMP_FIRE - 1, f) + 0.15 * smooth(8, 20, f) * math.sin(f * 2.3)
        else:
            em = 1.0 + 1.6 * math.exp(-(f - EMP_FIRE) * 0.35)
        pu = {0: 0.45, 1: 0.95, 2: 1.45, 3: 1.85, 4: 2.15, 5: 2.35}.get(f - EMP_FIRE, HIDE)
        sc = {"pulse": pu, "spill.L": HIDE, "spill.R": HIDE, "emitter": em, "eye": 1.0 + 0.12 * brace,
              "beacon": 1.0 + 0.3 * smooth(4, 20, f) * (1.0 - smooth(24, 34, f))}
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, EMP_FRAMES, False)


def summon(arm):
    """It crouches and turns its dish up to the sky (the emitter glowing: the order comes down the uplink), both hatches
    drop open into ramps (2-11), the bays flare and a knot of mites grows in each bay and rolls out onto the ramp,
    reaching its lip at SUMMON_FRAME where it is released (the game's Nano Swarm takes its place); the hatches close
    (31-43) and it rises. The legs walk on."""
    P = Poser(arm)
    act = ra.new_action(arm, "Summon")
    for f in range(SUMMON_FRAMES + 1):
        t = f / SUMMON_FRAMES
        w = 2 * math.pi * t
        aims = gait(arm, t)
        root_off, root_rot = _body(t)
        k = smooth(0, 10, f) * (1.0 - smooth(30, 44, f))
        root_off = root_off + V(0.0, 0.0, -0.07 * k)
        aims["turret"] = _yaw(0.0)
        aims["dish"] = _dish(arm, TILT0 - 0.36 * k)
        aims["mast"] = rel(arm, "mast", (0.03 * math.sin(w - 0.6), 0.015 * math.sin(2 * w - 0.6), 1.0))
        aims["mast2"] = rel(arm, "mast2", (0.07 * math.sin(w - 1.2), 0.03 * math.sin(2 * w - 1.2), 1.0))
        aims["eye"] = rel(arm, "eye", Vector(EYE_D))
        door = DOOR_OPEN * smooth(2, 11, f) * (1.0 - smooth(31, 43, f))
        aims.update(_hatches(arm, door))
        grow = smooth(5, 10, f)
        go = smooth(10, SUMMON_FRAME, f)
        gone = f > SUMMON_FRAME + 1
        sc = {"pulse": HIDE, "emitter": 1.0 + 0.5 * k + 0.1 * math.sin(f * 1.7) * k, "eye": 1.0 + 0.1 * k,
              "beacon": 1.0 + 0.3 * k}
        for sx in (-1, 1):
            s = "L" if sx > 0 else "R"
            off = SPILL_OUT[sx] * go + v3((0, 0, 0.03 * math.sin(math.pi * go)))
            aims["spill." + s] = _spill(arm, sx, tuple(off), 2.6 * go)
            sz = HIDE if (gone or f < 5) else max(HIDE, grow * (1.0 if f <= SUMMON_FRAME else 0.45))
            sc["spill." + s] = sz
            sc["bay." + s] = 1.0 + 0.5 * smooth(5, 12, f) * (1.0 - smooth(24, 36, f))
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, SUMMON_FRAMES, False)


def clips(arm):
    walk(arm)
    summon(arm)
    emp(arm)
