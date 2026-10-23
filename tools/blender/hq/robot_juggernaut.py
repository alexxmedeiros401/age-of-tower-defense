"""Steam Juggernaut, HQ: the Industrial Age boss, a locomotive that walks. A long boiler in white armour (gunmetal
riveted bands, an orange stripe down each flank) on a gunmetal running board, the smokebox at its front with a huge
red-glowing eye in its door under a frowning armoured brow, a tall funnel with a flared crown (its mouth glows), a
chrome steam dome, a steam whistle before the cab, and between the funnel and the dome its shield emitter: a copper-
wound mast with a turning finned collar and a cyan-glowing orb (its energy shield). At the back the cab: white armour
with red-glowing window slits and a round furnace window glowing in each side, a gunmetal roof, a hazard-striped
skirt. At the front a buffer beam in hazard stripes with two chrome buffers over a cowcatcher ram of gunmetal bars.
It walks on four heavy legs, each with a spoked locomotive wheel at its knee; a steam cylinder on the running board
works each thigh (the piston pumps as the leg swings), and a side rod couples each side's front and rear knee wheels,
like a locomotive's coupling rods.
Walk: a pace (the two legs of a side swing together, so the side rods stay level and pump back and forth), the body
swaying and rolling over the planted side, the funnel's ember flaring at each footfall, the emitter's collar turning.
Enrage (one-shot, played on its enrage): it crouches, then its whistle shrieks (WHISTLE_FRAME: the game's steam blast
and sound go here) while it shudders, its eye and furnace blaze and the funnel flares; then it lowers its head and
charges. Its legs keep marching at the enraged speed (ENRAGE_STEP) so its feet don't slide. Its energy shield is
game.gd's bubble (the emitter's orb is its source). Faces -Y, Z up, model_scale 1.0.
"""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, rot_from_axes, v3, norm,
                 F, smax)
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser

ROOT_NAME = "Juggernaut"
GLB_NAME = "juggernaut"
TEX_PREFIX = "juggernaut"
WALK_STEP = 0.5            # each foot's stride: the body moves 2 * WALK_STEP per loop of WALK_FRAMES
WALK_FRAMES = 48           # (2 s at 24 fps): walk_speed = 2 * 0.5 * 1.0 * 24 / 48 = 0.5
WALK_SPEED = 2 * WALK_STEP * 24 / WALK_FRAMES
ENRAGE_FRAMES = 48
ENRAGE_STEP = 0.495        # the Enrage's stride: two pace cycles in its 2 s = 0.99 per second = speed 0.45 * 2.2
WHISTLE_FRAME = 10         # the whistle blasts (the steam jet / sound start here; it blows on to about frame 34)

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.22, 0.23, 0.26)
BLACK = (0.07, 0.07, 0.08)
DECKC = (0.56, 0.58, 0.61)
COPPER = (0.78, 0.42, 0.22)
RED_GLOW = (1.0, 0.2, 0.08)
FIRE = (1.0, 0.38, 0.1)
EMBER = (1.0, 0.55, 0.15)
CYAN = (0.3, 0.88, 1.0)

LEGS = {}
for fr, y in (("F", -0.72), ("R", 0.82)):
    for s, sx in (("L", 1.0), ("R", -1.0)):
        LEGS[fr + s] = {"sx": sx, "y": y,
                        "hip": v3((sx * 0.84, y, 1.45)), "knee": v3((sx * 0.88, y - 0.22, 0.86)),
                        "ankle": v3((sx * 0.88, y + 0.05, 0.3)), "toe": v3((sx * 0.88, y - 0.3, 0.3))}
PHASE = {"FL": 0.0, "RL": 0.0, "FR": 0.5, "RR": 0.5}      # a pace: a side's two legs swing together

BZ = 2.12                                  # the boiler's axis height
BR = 0.5                                   # its radius
BY = (-1.2, 0.62)                          # its length (the smokebox in front, the cab behind)
SMOKE_Y = (-1.44, -1.2)
EYE_C = v3((0.0, -1.47, BZ - 0.02))        # the eye in the smokebox door
EYE_R = 0.22
FUN_Y = -1.3
FUN_TOP = 3.45
FUN_MOUTH = v3((0.0, FUN_Y, FUN_TOP + 0.01))
DOME_Y = -0.5
EMIT = v3((0.0, -0.02, BZ + BR - 0.04))    # the emitter's foot on the boiler
ORB = EMIT + v3((0.0, 0.0, 0.56))          # its orb
WHISTLE = v3((0.2, 0.4, 2.9))              # the whistle's mouth
CAB_Y = (0.62, 1.32)
CAB_Z = (1.66, 2.88)
RB_Z = (1.48, 1.68)                        # the running board
RB_Y = (-1.46, 1.36)
KNEE_X = 0.2                               # the knee wheel's pin (side rods), outside the knee
PIST_A = {k: v3((L["sx"] * 0.84, (-1.3 if k[0] == "F" else 1.34), 1.6)) for k, L in LEGS.items()}   # cylinders' pivots
PIST_T = 0.36                              # the piston rod's eye on the thigh (fraction from hip to knee)
CYL_LEN, PROD_LEN = 0.34, 0.42


def thigh_eye(k, hip=None, knee=None):
    L = LEGS[k]
    hip = L["hip"] if hip is None else hip
    knee = L["knee"] if knee is None else knee
    return hip + (knee - hip) * PIST_T


def knee_pin(k):
    L = LEGS[k]
    return L["knee"] + v3((L["sx"] * KNEE_X, 0, 0))


BONES = [
    ("root", (0, 0, 1.5), (0, 0, 1.75), None),
    ("eye", tuple(EYE_C), tuple(EYE_C + v3((0, -0.2, 0))), "root"),
    ("ember", tuple(FUN_MOUTH - v3((0, 0, 0.04))), tuple(FUN_MOUTH + v3((0, 0, 0.15))), "root"),
    ("emitter", tuple(EMIT), tuple(EMIT + v3((0, 0, 0.3))), "root"),
    ("orb", tuple(ORB), tuple(ORB + v3((0, 0, 0.15))), "emitter"),
    ("whistle", tuple(WHISTLE), tuple(WHISTLE + v3((0, 0, 0.15))), "root"),
    ("furnace", (0, 0.97, 2.05), (0, 0.97, 2.25), "root"),
]
for k, L in LEGS.items():
    BONES += [
        ("thigh." + k, tuple(L["hip"]), tuple(L["knee"]), "root"),
        ("shin." + k, tuple(L["knee"]), tuple(L["ankle"]), "thigh." + k),
        ("foot." + k, tuple(L["ankle"]), tuple(L["toe"]), "shin." + k),
        ("cyl." + k, tuple(PIST_A[k]), tuple(PIST_A[k] + norm(thigh_eye(k) - PIST_A[k]) * CYL_LEN), "root"),
        ("prod." + k, tuple(thigh_eye(k)), tuple(thigh_eye(k) + norm(PIST_A[k] - thigh_eye(k)) * PROD_LEN), "thigh." + k),
    ]
for s in ("L", "R"):
    BONES.append(("rod." + s, tuple(knee_pin("F" + s)), tuple(knee_pin("R" + s)), "thigh.F" + s))
ROD_LEN = float(np.linalg.norm(knee_pin("FL") - knee_pin("RL")))

MATS = {
    "armor": ("armor", dict(name="RB_JuggArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.42), (4, BLACK, 0.45),
                                                         (5, DECKC, 0.5)], seams=[2], wear=1.2, scale=2.0)),
    "frame": ("gunmetal", dict(name="RB_JuggFrame", base=(0.21, 0.22, 0.25), labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6),
                                                                                      (4, COPPER, 0.3), (5, BLACK, 0.5)],
                               seams=[2], scale=2.0)),
    "chrome": ("chrome", dict(name="RB_JuggChrome")),
    "glow": ("glow", dict(name="RB_JuggGlow", col=RED_GLOW)),
}
GLOW = {"Eye": (RED_GLOW, 1.5, 0.5), "Windows": (RED_GLOW, 1.4, 0.5), "Furnace": (FIRE, 1.4, 0.5), "Ember": (EMBER, 1.3, 0.5),
        "Orb": (CYAN, 1.3, 0.55), "Coils": (CYAN, 1.2, 0.55)}

LOW_TARGETS = {"Boiler": 1100, "Bands": 420, "Smokebox": 380, "Brow": 240, "Bezel": 220, "Eye": 110, "Funnel": 400, "Ember": 50,
               "Dome": 180, "Whistle": 120, "Mast": 320, "Collar": 200, "Orb": 100, "Coils": 110, "Cab": 900, "Windows": 90,
               "Furnace": 90, "Board": 700, "Beam": 300, "Cowcatcher": 520}
for k in LEGS:
    LOW_TARGETS.update({"Thigh" + k: 130, "ThighPlate" + k: 200, "Knee" + k: 280, "Shin" + k: 300, "Foot" + k: 240, "Spat" + k: 120,
                        "Cyl" + k: 150, "Prod" + k: 60})
for s in "LR":
    LOW_TARGETS["Rod" + s] = 180
X_AX = rot_from_axes(z_axis=(1, 0, 0))
Y_AX = rot_from_axes(z_axis=(0, 1, 0))


def _hazard(f, lo, hi, w=0.08, band=None, d=(0, 1, 1)):
    """Diagonal hazard stripes (orange 1 / black 4) over the box lo..hi (optionally only where band(P) < 0)."""
    lo, hi = v3(lo), v3(hi)
    dd = norm(d).astype(F)
    def box(P):
        return np.max(np.stack([lo.astype(F) - P, P - hi.astype(F)], 0), axis=(0, 2))
    def orange(P):
        b = box(P)
        return b if band is None else np.maximum(b, band(P))
    def black(P):
        s = (P @ dd) / F(w)
        fr = s - np.floor(s)
        return np.maximum(orange(P), (np.abs(fr - F(0.25)) - F(0.25)) * F(w * 0.7))
    f.paint(Func(orange, lo - 0.01, hi + 0.01), 1)
    f.paint(Func(black, lo - 0.01, hi + 0.01), 4)


def _axial_band(c, ax, half):
    c, ax = v3(c), norm(ax)
    return Func(lambda P: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(half), c - 0.6, c + 0.6)


def rivet_ring(f, c, r, n, axis="y", rr=0.016):
    for i in range(n):
        a = i * 2 * math.pi / n
        if axis == "y":
            p = c + v3((math.cos(a) * r, 0, math.sin(a) * r))
        else:
            p = c + v3((0, math.cos(a) * r, math.sin(a) * r))
        f.add(Sphere(p, rr), k=0.005)


def parts(fine=False):
    vx = 0.008 if fine else 0.014
    vs = 0.0055 if fine else 0.01
    out = []
    by0, by1 = BY
    # ================================================================================================ the body
    # ---- the boiler: a long white-jacketed drum, an orange stripe down each flank, plate seams
    f = Field("Boiler")
    f.add(Cylinder((0, (by0 + by1) / 2, BZ), BR, by1 - by0, rr=0.04, R=Y_AX))
    for sx in (-1, 1):
        f.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 2] - F(BZ + 0.02)) - F(0.035), F(-sx) * P[:, 0]),
                     (-0.6, by0, BZ - 0.2), (0.6, by1, BZ + 0.2)), 1)
        f.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 2] - F(BZ - 0.035)) - F(0.004), F(-sx) * P[:, 0]),
                     (-0.6, by0, BZ - 0.2), (0.6, by1, BZ + 0.2)), 2)
    for y in (-0.72, -0.18, 0.3):
        f.paint(RoundBox((0, y, BZ), (0.7, 0.004, 0.7)), 2)
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 0]) - F(0.005), F(BZ + 0.3) - P[:, 2]), (-0.6, by0, BZ), (0.6, by1, BZ + 0.6)), 2)
    out.append(("Boiler", f, vx, "root", "armor"))
    f = Field("Bands")
    for y in (by0 + 0.06, -0.45, 0.06, by1 - 0.06):
        f.add(Torus((0, y, BZ), BR + 0.004, 0.026, R=Y_AX))
        rivet_ring(f, v3((0, y, BZ)), BR + 0.024, 18)
    out.append(("Bands", f, vs, "root", "frame"))
    # ---- the smokebox at its front: gunmetal, its door with the eye's bezel, a frowning white brow over the eye
    f = Field("Smokebox")
    sy0, sy1 = SMOKE_Y
    f.add(Cylinder((0, (sy0 + sy1) / 2, BZ), BR + 0.03, sy1 - sy0, rr=0.04, R=Y_AX))
    f.add(Torus((0, sy0 + 0.02, BZ), BR - 0.02, 0.03, R=Y_AX), k=0.01)
    f.add(Ellipsoid((0, sy0, BZ), (BR - 0.06, 0.06, BR - 0.06)), k=0.03)
    rivet_ring(f, v3((0, sy0 - 0.005, BZ)), BR - 0.08, 16, rr=0.018)
    for zz in (BZ - 0.33, BZ - 0.38):                                                      # hinge straps under the eye
        f.add(RoundBox((0, sy0 - 0.03, zz), (0.2, 0.02, 0.018), 0.01), k=0.006)
    f.paint(Torus((0, sy1 - 0.03, BZ), BR + 0.03, 0.03, R=Y_AX), 1)
    out.append(("Smokebox", f, vx, "root", "frame"))
    f = Field("Bezel")
    f.add(Torus(EYE_C, EYE_R + 0.025, 0.035, R=Y_AX))
    for i in range(10):
        a = i * 2 * math.pi / 10 + 0.3
        f.add(Sphere(EYE_C + v3((math.cos(a) * (EYE_R + 0.025), -0.03, math.sin(a) * (EYE_R + 0.025))), 0.018), k=0.005)
    f.paint(Torus(EYE_C + v3((0, -0.02, 0)), EYE_R + 0.025, 0.02, R=Y_AX), 1)
    out.append(("Bezel", f, vs, "root", "frame"))
    f = Field("Eye")
    f.add(Ellipsoid(EYE_C + v3((0, 0.01, 0)), (EYE_R, 0.06, EYE_R)))
    out.append(("Eye", f, vs, "eye", "glow"))
    f = Field("Brow")
    for sx in (-1, 1):
        f.add(RoundBox(EYE_C + v3((sx * 0.15, -0.06, EYE_R + 0.06)), (0.2, 0.06, 0.045), 0.03,
                       R=rot_from_axes(x_axis=(1, 0, -sx * 0.4), y_axis=(0, 1, 0))), k=0.03)
    _hazard(f, EYE_C + v3((-0.45, -0.2, EYE_R - 0.05)), EYE_C + v3((0.45, -0.07, EYE_R + 0.2)), w=0.075, d=(1, 0, 1))
    out.append(("Brow", f, vs, "root", "armor"))
    # ---- the funnel: a tall stack with a flared crown, banded; its mouth glows
    f = Field("Funnel")
    fz0 = BZ + BR - 0.05
    f.add(Cylinder((0, FUN_Y, (fz0 + FUN_TOP - 0.15) / 2), 0.15, FUN_TOP - 0.15 - fz0, rr=0.02))
    f.add(Cylinder((0, FUN_Y, fz0 + 0.1), 0.22, 0.07, rr=0.025), k=0.04)                   # its foot
    f.add(RoundCone((0, FUN_Y, FUN_TOP - 0.25), (0, FUN_Y, FUN_TOP - 0.03), 0.155, 0.25), k=0.03)   # the crown
    f.add(Torus((0, FUN_Y, FUN_TOP - 0.025), 0.24, 0.03), k=0.01)
    f.sub(Cylinder((0, FUN_Y, FUN_TOP + 0.05), 0.2, 0.2), k=0.01)                         # its mouth
    f.add(Torus((0, FUN_Y, FUN_TOP - 0.35), 0.152, 0.02), k=0.006)
    f.paint(Cylinder((0, FUN_Y, fz0 + 0.38), 0.3, 0.07), 1)
    f.paint(Cylinder((0, FUN_Y, FUN_TOP - 0.03), 0.32, 0.06), 4)
    out.append(("Funnel", f, vs, "root", "frame"))
    f = Field("Ember")
    f.add(Cylinder((0, FUN_Y, FUN_TOP - 0.1), 0.2, 0.025, rr=0.008))
    out.append(("Ember", f, vs, "ember", "glow"))
    # ---- the steam dome (chrome) and the whistle (chrome, before the cab)
    f = Field("Dome")
    dz = BZ + BR - 0.05
    f.add(Cylinder((0, DOME_Y, dz + 0.08), 0.2, 0.16, rr=0.04))
    f.add(Ellipsoid((0, DOME_Y, dz + 0.16), (0.2, 0.2, 0.15)), k=0.04)
    f.add(Cylinder((0, DOME_Y, dz + 0.02), 0.26, 0.05, rr=0.02), k=0.04)
    out.append(("Dome", f, vs, "root", "chrome"))
    f = Field("Whistle")
    wb = v3((WHISTLE[0], WHISTLE[1], BZ + math.sqrt(BR * BR - WHISTLE[0] ** 2) - 0.03))
    f.add(Cylinder(wb + v3((0, 0, 0.03)), 0.045, 0.06, rr=0.01))
    f.add(RoundCone(wb, WHISTLE - v3((0, 0, 0.14)), 0.022, 0.022), k=0.008)
    f.add(Cylinder(WHISTLE - v3((0, 0, 0.08)), 0.045, 0.14, rr=0.012), k=0.01)             # the bell
    f.add(Torus(WHISTLE - v3((0, 0, 0.012)), 0.04, 0.009), k=0.004)
    f.sub(Cylinder(WHISTLE + v3((0, 0, 0.02)), 0.03, 0.06), k=0.004)
    f.add(RoundCone(WHISTLE - v3((0, 0, 0.12)), WHISTLE - v3((-0.09, 0, 0.1)), 0.008, 0.007), k=0.004)   # its lever
    out.append(("Whistle", f, vs * 0.8, "root", "chrome"))
    # ---- the shield emitter: a mast on a pedestal, copper windings, a turning finned collar, the cyan orb and coils
    f = Field("Mast")
    f.add(Cylinder(EMIT + v3((0, 0, 0.04)), 0.2, 0.1, rr=0.03))
    f.add(Cylinder(EMIT + v3((0, 0, 0.27)), 0.06, 0.4, rr=0.015), k=0.02)
    for i in range(5):
        f.add(Torus(EMIT + v3((0, 0, 0.14 + 0.04 * i)), 0.09, 0.02), k=0.003, label=4)
    f.add(Cylinder(EMIT + v3((0, 0, 0.415)), 0.1, 0.04, rr=0.015), k=0.01)                  # the cup under the orb
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        u = v3((math.cos(a), math.sin(a), 0))
        f.add(RoundCone(EMIT + v3((0, 0, 0.42)) + u * 0.08, ORB + u * 0.16 + v3((0, 0, 0.04)), 0.017, 0.011), k=0.005)   # prongs
    f.paint(Cylinder(EMIT + v3((0, 0, 0.06)), 0.25, 0.04), 1)
    out.append(("Mast", f, vs, "root", "frame"))
    f = Field("Collar")
    f.add(Cylinder(EMIT + v3((0, 0, 0.36)), 0.085, 0.05, rr=0.012))
    for i in range(3):
        a = i * 2 * math.pi / 3
        u = v3((math.cos(a), math.sin(a), 0))
        f.add(RoundBox(EMIT + v3((0, 0, 0.36)) + u * 0.14, (0.075, 0.014, 0.045), 0.01,
                       R=rot_from_axes(x_axis=u, z_axis=(0, 0, 1))), k=0.008)
        f.paint(Sphere(EMIT + v3((0, 0, 0.36)) + u * 0.19, 0.04), 1)
    out.append(("Collar", f, vs, "emitter", "frame"))
    f = Field("Orb")
    f.add(Sphere(ORB, 0.15))
    out.append(("Orb", f, vs, "orb", "glow"))
    f = Field("Coils")
    for i, (z, r) in enumerate(((0.2, 0.125), (0.28, 0.125))):
        f.add(Torus(EMIT + v3((0, 0, z)), r, 0.016))
    out.append(("Coils", f, vs, "emitter", "glow"))
    # ---- the cab: white armour, a gunmetal roof, window slits and furnace windows (glowing), a hazard-striped skirt
    f = Field("Cab")
    cy0, cy1 = CAB_Y
    cz0, cz1 = CAB_Z
    cc = v3((0, (cy0 + cy1) / 2, (cz0 + cz1) / 2))
    f.add(RoundBox(cc, (0.64, (cy1 - cy0) / 2, (cz1 - cz0) / 2), 0.06))
    f.add(RoundBox(v3((0, cc[1] + 0.02, cz1 + 0.05)), (0.71, (cy1 - cy0) / 2 + 0.08, 0.05), 0.04), k=0.02, label=3)   # the roof
    f.add(Ellipsoid(v3((0, cc[1], cz1 + 0.08)), (0.6, (cy1 - cy0) / 2 + 0.02, 0.1)), k=0.04, label=3)
    for sx in (-1, 1):
        f.sub(RoundBox(v3((sx * 0.43, cy0, 2.62)), (0.13, 0.05, 0.08), 0.03), k=0.01)        # front windows (beside the boiler)
        f.sub(RoundBox(v3((sx * 0.64, cc[1], 2.6)), (0.05, 0.25, 0.075), 0.03), k=0.01)      # side windows
        f.sub(Cylinder(v3((sx * 0.64, cc[1], 2.05)), 0.13, 0.08, R=X_AX), k=0.01)            # furnace windows
        f.add(Torus(v3((sx * 0.645, cc[1], 2.05)), 0.14, 0.022, R=X_AX), k=0.006, label=3)
        for i in range(3):
            f.add(RoundBox(v3((sx * 0.62, cc[1], 2.0 + 0.05 * i)), (0.012, 0.12, 0.008), 0.004), k=0.003, label=3)   # its grate bars
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(cz1 - 0.12)) - F(0.03), cc - 1, cc + 1), 1)                 # an orange band
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(2.3)) - F(0.004), cc - 1, cc + 1), 2)
    _hazard(f, v3((-0.75, cy0 - 0.1, cz0 - 0.05)), v3((0.75, cy1 + 0.1, cz0 + 0.17)), w=0.09, d=(0, 1, 1))
    for sx in (-1, 1):
        f.paint(RoundBox(v3((sx * 0.64, cc[1], 2.3)), (0.04, 0.004, 0.65)), 2)
    out.append(("Cab", f, vx, "root", "armor"))
    f = Field("Windows")
    for sx in (-1, 1):
        f.add(RoundBox(v3((sx * 0.43, cy0 + 0.035, 2.62)), (0.12, 0.012, 0.07), 0.025))
        f.add(RoundBox(v3((sx * 0.6, cc[1], 2.6)), (0.012, 0.24, 0.066), 0.025))
    out.append(("Windows", f, vs, "root", "glow"))
    f = Field("Furnace")
    for sx in (-1, 1):
        f.add(Ellipsoid(v3((sx * 0.61, cc[1], 2.05)), (0.014, 0.125, 0.125)))
    out.append(("Furnace", f, vs, "furnace", "glow"))
    # ---- the running board: a gunmetal frame under it all, orange-edged, the hip housings, the cylinders' brackets
    f = Field("Board")
    f.add(RoundBox((0, (RB_Y[0] + RB_Y[1]) / 2, (RB_Z[0] + RB_Z[1]) / 2), (0.64, (RB_Y[1] - RB_Y[0]) / 2, (RB_Z[1] - RB_Z[0]) / 2), 0.04))
    f.add(RoundBox((0, 0.05, 1.36), (0.4, 1.1, 0.14), 0.06), k=0.04)                       # the belly frame
    for k, L in LEGS.items():
        hp = L["hip"]
        f.add(Cylinder(hp - v3((L["sx"] * 0.14, 0, 0)), 0.2, 0.18, rr=0.04, R=X_AX), k=0.03)
        f.add(Sphere(hp, 0.16), k=0.02)
        f.paint(Torus(hp - v3((L["sx"] * 0.07, 0, 0)), 0.2, 0.03, R=X_AX), 1)
        a = PIST_A[k]
        f.add(RoundBox(a + v3((-L["sx"] * 0.1, 0, 0.02)), (0.12, 0.07, 0.06), 0.03), k=0.03)   # the cylinder's trunnion bracket
        f.add(Cylinder(a, 0.05, 0.16, rr=0.012, R=X_AX), k=0.01)
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(RB_Z[1] - 0.04)) - F(0.025), (-1, -2, 1), (1, 2, 2)), 1)
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(RB_Z[0] + 0.05)) - F(0.004), (-1, -2, 1), (1, 2, 2)), 2)
    out.append(("Board", f, vx, "root", "frame"))
    # ---- the buffer beam (hazard stripes, two chrome-faced buffers) and the cowcatcher ram of bars below it
    f = Field("Beam")
    f.add(RoundBox((0, RB_Y[0] - 0.02, 1.48), (0.62, 0.07, 0.15), 0.035))
    _hazard(f, (-0.7, RB_Y[0] - 0.2, 1.3), (0.7, RB_Y[0] - 0.05, 1.66), w=0.1, d=(1, 0, 1))
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.42, RB_Y[0] - 0.14, 1.5), 0.055, 0.16, rr=0.015, R=Y_AX), k=0.01)
        f.add(Cylinder((sx * 0.42, RB_Y[0] - 0.235, 1.5), 0.1, 0.035, rr=0.014, R=Y_AX), k=0.01, label=5)
    out.append(("Beam", f, vs, "root", "armor"))
    f = Field("Cowcatcher")
    tip = v3((0, -2.3, 0.2))
    top_l, top_r = v3((0.56, RB_Y[0] - 0.08, 1.32)), v3((-0.56, RB_Y[0] - 0.08, 1.32))
    bot_l, bot_r = v3((0.55, -1.74, 0.2)), v3((-0.55, -1.74, 0.2))
    for i in range(9):
        u = i / 8.0
        top = top_r + (top_l - top_r) * u
        bot = (bot_r + (tip - bot_r) * (u * 2)) if u <= 0.5 else (tip + (bot_l - tip) * ((u - 0.5) * 2))
        f.add(RoundBox((top + bot) / 2, (0.03, 0.024, float(np.linalg.norm(top - bot)) / 2), 0.012,
                       R=rot_from_axes(z_axis=norm(top - bot), x_axis=norm(np.cross(norm(top - bot), (0, 0, 1)) + 1e-6))), k=0.01)
    f.add(RoundCone(top_r + v3((0, 0, 0.0)), top_l, 0.04, 0.04), k=0.015)                  # the top rail
    f.add(RoundCone(bot_r, tip, 0.035, 0.035), k=0.015)                                     # the bottom rails
    f.add(RoundCone(tip, bot_l, 0.035, 0.035), k=0.015)
    f.add(RoundCone(v3((0, RB_Y[0] - 0.06, 1.3)), tip + v3((0, 0.02, 0.06)), 0.07, 0.05), k=0.03)   # the ram's spine
    f.add(Sphere(tip + v3((0, 0.0, 0.03)), 0.07), k=0.02)
    f.paint(Sphere(tip + v3((0, 0.0, 0.03)), 0.12), 1)
    f.paint(RoundCone(top_r, top_l, 0.06, 0.06), 1)
    out.append(("Cowcatcher", f, vs, "root", "frame"))

    # ================================================================================================ the legs
    for k, L in LEGS.items():
        sx = L["sx"]
        hp, kn, an = L["hip"], L["knee"], L["ankle"]
        tax, sax = norm(kn - hp), norm(an - kn)
        Rt = rot_from_axes(z_axis=tax, y_axis=(0, -1, 0))
        Rs = rot_from_axes(z_axis=sax, y_axis=(0, -1, 0))
        f = Field("Thigh" + k)
        f.add(RoundCone(hp, kn, 0.17, 0.14))
        te = thigh_eye(k)
        f.add(Cylinder(te + v3((sx * 0.0, 0, 0)), 0.045, 0.26, rr=0.012, R=X_AX), k=0.02)    # the piston rod's eye pin
        out.append(("Thigh" + k, f, vx, "thigh." + k, "frame"))
        f = Field("ThighPlate" + k)                                                         # armour over its outside
        tc = hp + (kn - hp) * 0.58
        f.add(RoundBox(tc + Rt @ v3((sx * 0.08, 0.03, 0.0)), (0.12, 0.17, 0.21), 0.07, R=Rt))
        f.paint(_axial_band(hp + (kn - hp) * 0.42, tax, 0.03), 1)
        f.paint(_axial_band(hp + (kn - hp) * 0.75, tax, 0.004), 2)
        out.append(("ThighPlate" + k, f, vx, "thigh." + k, "armor"))
        f = Field("Knee" + k)                                                               # a locomotive wheel at the knee
        kw = kn + v3((sx * 0.12, 0, 0))
        f.add(Cylinder(kn, 0.11, 0.3, rr=0.03, R=X_AX))                                    # the axle
        f.add(Cylinder(kw, 0.26, 0.05, rr=0.015, R=X_AX), k=0.01)                          # the web
        f.add(Torus(kw + v3((sx * 0.012, 0, 0)), 0.245, 0.038, R=X_AX), k=0.01)              # the tyre
        for i in range(10):
            a = i * 2 * math.pi / 10
            d = v3((0, math.cos(a), math.sin(a)))
            f.add(RoundCone(kw + v3((sx * 0.03, 0, 0)) + d * 0.06, kw + v3((sx * 0.025, 0, 0)) + d * 0.22, 0.019, 0.015), k=0.006)
        f.add(Cylinder(kw + v3((sx * 0.035, 0, 0)), 0.07, 0.05, rr=0.015, R=X_AX), k=0.01)    # the hub
        f.add(RoundBox(kw + v3((sx * 0.06, 0, 0)), (0.025, 0.05, 0.1), 0.015, R=rot_from_axes(x_axis=(1, 0, 0), z_axis=(0, 0.6, 1))), k=0.01)   # the crank boss
        f.add(Cylinder(kn + v3((sx * (KNEE_X - 0.02), 0, 0)), 0.03, 0.08, rr=0.008, R=X_AX), k=0.006)   # the side rod's pin
        f.paint(Torus(kw + v3((sx * 0.012, 0, 0)), 0.245, 0.043, R=X_AX), 5)
        f.paint(Cylinder(kw + v3((sx * 0.06, 0, 0)), 0.05, 0.03, R=X_AX), 1)
        out.append(("Knee" + k, f, vs, "shin." + k, "frame"))
        f = Field("Shin" + k)                                                               # a boxy armoured shin, a ridge
        sc = kn + (an - kn) * 0.55
        f.add(RoundBox(sc + Rs @ v3((0, 0.0, 0)), (0.19, 0.17, 0.25), 0.07, R=Rs))
        f.add(RoundBox(sc + Rs @ v3((0, 0.18, 0.0)), (0.035, 0.035, 0.2), 0.02, R=Rs), k=0.03)
        f.add(RoundCone(kn, sc, 0.13, 0.13), k=0.03)
        f.paint(_axial_band(kn + (an - kn) * 0.82, sax, 0.03), 1)
        f.paint(_axial_band(kn + (an - kn) * 0.38, sax, 0.004), 2)
        if k[0] == "F":
            _hazard(f, sc - v3((0.25, 0.3, 0.12)), sc + v3((0.25, -0.08, 0.12)), w=0.07, d=(1, 0, 1))
        out.append(("Shin" + k, f, vx, "shin." + k, "armor"))
        f = Field("Foot" + k)                                                               # a broad iron foot, three toes
        f.add(RoundBox(an + v3((0, -0.08, -0.19)), (0.27, 0.35, 0.09), 0.07))
        for dx in (-0.15, 0.0, 0.15):
            f.add(Ellipsoid(an + v3((dx, -0.42, -0.18)), (0.085, 0.11, 0.085)), k=0.03)
            f.paint(Ellipsoid(an + v3((dx, -0.49, -0.17)), (0.1, 0.08, 0.1)), 1)
        f.add(RoundBox(an + v3((0, 0.24, -0.2)), (0.15, 0.09, 0.08), 0.05), k=0.04)
        f.add(Sphere(an, 0.12), k=0.04)
        f.paint(Func(lambda P, z=an[2] - 0.255: P[:, 2] - F(z), an - 0.6, an + 0.6), 5)
        out.append(("Foot" + k, f, vx, "foot." + k, "frame"))
        f = Field("Spat" + k)
        f.add(Ellipsoid(an + v3((0, -0.15, -0.08)), (0.23, 0.28, 0.1)))
        f.sub(Sphere(an + v3((0, 0.02, 0.0)), 0.15), k=0.03)
        f.paint(RoundBox(an + v3((0, -0.15, -0.08)), (0.004, 0.4, 0.3)), 2)
        out.append(("Spat" + k, f, vs, "foot." + k, "armor"))
        # ---- the thigh's steam cylinder (on the running board) and its piston rod (on the thigh)
        a = PIST_A[k]
        d = norm(te - a)
        Rc = rot_from_axes(z_axis=d, x_axis=(1, 0, 0))
        f = Field("Cyl" + k)
        f.add(Cylinder(a + d * (CYL_LEN / 2), 0.07, CYL_LEN, rr=0.018, R=Rc))
        f.add(Torus(a + d * (CYL_LEN - 0.02), 0.07, 0.014, R=Rc), k=0.005)
        f.add(Torus(a + d * 0.03, 0.07, 0.014, R=Rc), k=0.005)
        f.add(Cylinder(a, 0.05, 0.2, rr=0.012, R=X_AX), k=0.012)                             # its trunnion
        f.paint(Cylinder(a + d * (CYL_LEN / 2), 0.09, 0.05, R=Rc), 1)
        out.append(("Cyl" + k, f, vs, "cyl." + k, "frame"))
        f = Field("Prod" + k)
        f.add(RoundCone(te, te + (a - te) / float(np.linalg.norm(a - te)) * PROD_LEN, 0.024, 0.024))
        f.add(Cylinder(te, 0.04, 0.07, rr=0.01, R=X_AX), k=0.008)
        out.append(("Prod" + k, f, vs, "prod." + k, "chrome"))
    # ---- the side rods coupling each side's knee wheels
    for s in ("L", "R"):
        sx = 1.0 if s == "L" else -1.0
        p0, p1 = knee_pin("F" + s) + v3((sx * 0.03, 0, 0)), knee_pin("R" + s) + v3((sx * 0.03, 0, 0))
        f = Field("Rod" + s)
        mid = (p0 + p1) / 2
        f.add(RoundBox(mid, (0.02, ROD_LEN / 2 - 0.02, 0.035), 0.012))
        for p in (p0, p1):
            f.add(Cylinder(p, 0.06, 0.045, rr=0.014, R=X_AX), k=0.02)
        f.add(RoundBox(mid, (0.028, 0.06, 0.05), 0.012), k=0.02)
        f.paint(RoundBox(mid, (0.1, 0.07, 0.1)), 1)
        out.append(("Rod" + s, f, vs, "rod." + s, "chrome"))
    return out


# ------------------------------------------------------------------------------------------------ clips
V = lambda *a: Vector(a)


def _smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / float(b - a)))
    return t * t * (3 - 2 * t)


def _toe(pitch):
    return Quaternion(V(1, 0, 0), -pitch) @ V(0, -1, 0)


def _pace(arm, t, step, lift=0.13):
    """All four legs at loop time t: a pace, each side's two legs together; a planted foot slides back under the body
    for half the loop, then swings forward lifted, its toe a little up before it lands."""
    aims = {}
    for k, L in LEGS.items():
        ph = (t + PHASE[k]) % 1.0
        if ph < 0.5:
            y, z, pitch = -step / 2 + step * ph / 0.5, 0.0, 0.0
        else:
            q = (ph - 0.5) / 0.5
            e = 0.5 - 0.5 * math.cos(math.pi * q)
            y = step / 2 - step * e
            z = lift * math.sin(math.pi * q) ** 1.6
            pitch = 0.18 * math.sin(math.pi * q) ** 2 * q
        aims.update(ra.leg(arm, k, Vector(tuple(L["ankle"])) + V(0, y, z), _toe(pitch), V(0, -1, 0.05)))
    return aims


def _spin_z(a):
    return lambda P, base: (base.col[1].xyz.copy(), a)


def _mechanics(arm, P, rest):
    """Second-pass aims from the solved pose P: each cylinder at its piston's eye, each piston rod at its cylinder's
    pivot, each side rod from its front knee pin to its rear knee pin (stretched to fit exactly)."""
    aims, sc = {}, {}
    def world(bone, p):
        return P[bone] @ (rest[bone].inverted() @ Vector(tuple(p)))
    for k in LEGS:
        a = world("root", PIST_A[k])
        e = world("thigh." + k, thigh_eye(k))
        aims["cyl." + k] = e - a
        aims["prod." + k] = a - e
    for s in ("L", "R"):
        p0 = world("thigh.F" + s, knee_pin("F" + s))
        p1 = world("thigh.R" + s, knee_pin("R" + s))
        aims["rod." + s] = p1 - p0
        sc["rod." + s] = (1.0, (p1 - p0).length / ROD_LEN, 1.0)
    return aims, sc


def _solve2(P_, arm, aims, root_off, root_rot, scales):
    rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
    _, Pm = P_.solve(aims, root_off=root_off, root_rot=root_rot, scales=scales)
    a2, s2 = _mechanics(arm, Pm, rest)
    aims = dict(aims)
    aims.update(a2)
    sc = dict(scales)
    sc.update(s2)
    ch, _ = P_.solve(aims, root_off=root_off, root_rot=root_rot, scales=sc)
    return ch


def walk(arm):
    """The pace: a ponderous sway from side to side over the planted legs, a dip at each footfall, the side rods and
    pistons pumping, the funnel flaring at each footfall, the emitter's collar turning (a third of a turn per loop)."""
    P = Poser(arm)
    act = ra.new_action(arm, "Walk")
    for f in range(WALK_FRAMES + 1):
        t = f / WALK_FRAMES
        w = 2 * math.pi * t
        aims = _pace(arm, t, WALK_STEP)
        c = math.cos(2 * w)
        bob = 0.03
        dip = -bob * c - 1.4 * bob * max(0.0, c) ** 4
        root_off = V(0.07 * math.sin(w), 0.0, dip + bob)
        root_rot = Quaternion(V(0, 1, 0), 0.035 * math.sin(w - 0.4)) @ Quaternion(V(0, 0, 1), 0.025 * math.sin(w)) @ \
            Quaternion(V(1, 0, 0), 0.012 * math.sin(2 * w - 0.5))
        aims["emitter"] = _spin_z(2 * math.pi / 3 * t)
        puff = max(0.0, c) ** 8
        sc = {"ember": (1.0, 1.0 + 0.9 * puff, 1.0), "eye": 1.0 + 0.03 * math.sin(2 * w),
              "orb": 1.0 + 0.06 * math.sin(4 * w), "furnace": 1.0}
        P.key(_solve2(P, arm, aims, root_off, root_rot, sc), f)
    ra.finish_action(arm, act, WALK_FRAMES, True)


def enrage(arm):
    """It crouches (0-9), its whistle shrieks (WHISTLE_FRAME) as it rears a little and shudders, the eye, the furnace
    and the funnel blazing (10-32); then it drops its head and leans into the charge (32-48). Its legs pace on at the
    enraged speed (two cycles of ENRAGE_STEP)."""
    P = Poser(arm)
    act = ra.new_action(arm, "Enrage")
    for f in range(ENRAGE_FRAMES + 1):
        t = f / ENRAGE_FRAMES
        u = (2 * t) % 1.0 if f < ENRAGE_FRAMES else 0.0
        aims = _pace(arm, u, ENRAGE_STEP, lift=0.15)
        w = 2 * math.pi * u
        crouch = _smooth(0, 9, f) * (1.0 - _smooth(9, 13, f))
        rear = _smooth(9, 14, f) * (1.0 - _smooth(28, 36, f))
        charge = _smooth(30, 42, f)
        blast = _smooth(WHISTLE_FRAME - 1, WHISTLE_FRAME + 1, f) * (1.0 - _smooth(30, 36, f))
        shud = 0.012 * math.sin(f * 2.4) * blast
        c = math.cos(2 * w)
        root_off = V(0.05 * math.sin(w) + shud, 0.0, -0.025 * c + 0.025 - 0.09 * crouch + 0.03 * rear + shud * 0.6)
        root_rot = Quaternion(V(1, 0, 0), 0.05 * crouch * -1.0 + 0.045 * rear - 0.04 * charge) @ \
            Quaternion(V(0, 1, 0), 0.03 * math.sin(w - 0.4) + 0.5 * shud)
        aims["emitter"] = _spin_z(2 * math.pi / 3 * t * 2)
        flare = blast
        sc = {"ember": (1.0, 1.0 + 2.0 * flare, 1.0), "eye": 1.0 + 0.16 * flare + 0.06 * charge,
              "orb": 1.0 + 0.15 * flare, "furnace": (1.0, 1.0 + 0.25 * flare, 1.0 + 0.25 * flare)}
        P.key(_solve2(P, arm, aims, root_off, root_rot, sc), f)
    ra.finish_action(arm, act, ENRAGE_FRAMES, False)


def clips(arm):
    walk(arm)
    enrage(arm)
