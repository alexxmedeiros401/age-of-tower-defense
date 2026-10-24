"""THE CORE, HQ: the final boss, the robots' central intelligence walking out of its data center. A colossal six-legged
machine: on a broad hexagonal hull of white armour plates (a gunmetal belly, orange pinstripes, cyan conduits glowing
in grooves along its deck, rows of status lights on its back) sits its mind: a giant glowing cyan core sphere laced
with a gunmetal grid, one huge red eye in a bolted bezel in its front (a dark pupil in a red iris), held in a cage of
four curved white armour petals with orange edges rising from a hazard-banded cup to a cap at the top, where a crown of
antenna spires (orange bands, red tips) rises from a gunmetal collar. Two chrome gyroscope rings clamped with white
plates orbit the sphere outside the cage, each slowly turning in its own tilted plane. At its front, under the eye, an
armoured prow holds the deployment bay: a hazard-striped door hinged at its foot that drops into a ramp to the ground,
a cyan-lit bay behind it with a Sentinel standing ready inside (a scale model of robot_sentinel's, at the size the
game launches a summoned robot: 0.55 of the Sentinel in game), two orange launch lamps beside it. Torn-out data cables
trail from its back, their plugs dragging on the ground. Six heavy legs: gunmetal hip drums, white armoured thighs
with hazard bands and chrome pistons, knees held high under orange caps, long gunmetal shins with white plates and
cyan conduits, round foot pads with three claws.
Walk (48 frames): a ripple gait (on each side the legs swing one after another, rear to front, the sides half a loop
apart; four feet always planted), the hull swaying gently, the eye looking about, the rings turning slowly
(walk_speed 0.38 = WALK_STEP / (2/3 of the loop's 2 s): the feet stay planted at its speed). Emp (48): it braces, the
rings spin up, the core brightens and flickers, and at EMP_FIRE a pulse bursts from the core (a ring of light flung
out), the hull jolting; the rings spin down. Summon (48): it dips its prow, the bay door drops into a ramp, the bay and
lamps blaze, the eye looks down, and the Sentinel rides out of the bay and down the ramp, released at SUMMON_FRAME
(the game's Sentinel takes over there, at 0.55 scale); the door closes and a fresh one stands in the bay. Enrage (48):
the core flickers red and burns red, the rings spin up fast, it rears and shudders, then leans into a charge; its legs
march at the enraged speed (twice the walk). WalkRage (48, optional): the Walk with the core red and the rings
spinning fast (for the game to loop once it is enraged). Faces -Y, Z up; model_scale 1.0.
"""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Func, rot_from_axes, v3, norm, F,
                 smax)
from robot_stealth_jet import facet, mirror_pts, hazard, rel, smooth
import robot_anim as ra
from mathutils import Vector, Quaternion, Matrix
from rig import Poser, two_bone, bone_len

ROOT_NAME = "TheCore"
GLB_NAME = "the_core"
TEX_PREFIX = "the_core"
WALK_FRAMES = 48
DUTY = 2.0 / 3.0           # each foot is planted two thirds of the loop
WALK_STEP = 0.507          # walk_speed = WALK_STEP / (DUTY * 48 / 24) = 0.38
EMP_FRAMES = 48
EMP_FIRE = 24              # the pulse bursts from the core here
SUMMON_FRAMES = 48
SUMMON_FRAME = 22          # the Sentinel stands on the ramp here: released (the game's Sentinel takes over)
ENRAGE_FRAMES = 48
RAGE_FRAME = 13            # the core has turned red here (it flickers from frame 6)

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.22, 0.23, 0.26)
BLACK = (0.07, 0.07, 0.08)
DECKC = (0.56, 0.58, 0.61)
RED_GLOW = (1.0, 0.16, 0.08)
RAGE = (1.0, 0.1, 0.05)
CYAN = (0.3, 0.88, 1.0)
LAMP = (1.0, 0.55, 0.15)

X_AX = rot_from_axes(z_axis=(1, 0, 0))
Y_AX = rot_from_axes(z_axis=(0, 1, 0))

# ---- the core and its cage
CC = v3((0, 0.15, 2.5))                    # the core sphere's centre
CORE_R = 0.6
CAGE_R, CAGE_T = 0.7125, 0.0325            # the petals' mid radius and half thickness
EYE_D = norm(v3((0, -math.cos(math.radians(15)), math.sin(math.radians(15)))))
NA = norm(v3((0, -math.sin(math.radians(18)), math.cos(math.radians(18)))))          # ring A: front low
_tb = math.radians(48)
NB = norm(v3((math.sin(_tb) * 0.7071, math.sin(_tb) * 0.7071, math.cos(_tb))))      # ring B: low at the rear left
RA, RB, RING_T = 0.88, 1.0, 0.04
CROWN = v3((0, 0.15, CC[2] + CAGE_R + CAGE_T - 0.01))

# ---- the hull and the prow with its bay
DECK = 1.62
HULL = facet(mirror_pts([(0.5, -0.92, DECK), (0.86, -0.32, DECK), (0.86, 0.42, DECK), (0.52, 0.92, DECK),
                         (0.58, -1.0, 1.48), (0.98, -0.36, 1.48), (0.98, 0.46, 1.48), (0.6, 1.0, 1.48),
                         (0.58, -1.0, 1.08), (0.98, -0.36, 1.08), (0.98, 0.46, 1.08), (0.6, 1.0, 1.08),
                         (0.46, -0.9, 0.86), (0.8, -0.3, 0.86), (0.8, 0.4, 0.86), (0.48, 0.9, 0.86)]), k=0.014)
PROW = facet(mirror_pts([(0.45, -1.28, 0.86), (0.4, -1.28, 1.84), (0.32, -1.21, 1.92), (0.48, -0.45, 0.9),
                         (0.42, -0.45, 1.98), (0.34, -0.5, 2.04)]), k=0.012)
BAY_LO, BAY_HI = v3((-0.31, -1.4, 0.9)), v3((0.31, -0.57, 1.78))
HINGE = v3((0, -1.29, 0.9))
DOOR_H = BAY_HI[2] - BAY_LO[2]
DOOR_OPEN = math.radians(145)
M0 = v3((0, -0.92, 0.926))                   # the waiting Sentinel's feet (rest)
MINI = 0.55 * 0.9                          # its scale: the game's summoned Sentinel starts at 0.55 (model_scale 0.9)

# ---- the legs
LEGS = {}
for _n, _sx, _y0, _kn, _an in (("LF", 1, -0.62, (1.36, -0.95, 1.88), (1.3, -1.22, 0.24)),
                               ("LM", 1, 0.05, (1.55, 0.05, 1.9), (1.44, 0.05, 0.24)),
                               ("LH", 1, 0.72, (1.38, 1.02, 1.88), (1.3, 1.3, 0.24))):
    _hx = 0.98 if _n == "LM" else (0.82 if _n == "LF" else 0.84)
    for _s, _m in (("L", 1), ("R", -1)):
        LEGS[_s + _n[1]] = {"hip": v3((_m * _hx, _y0, 1.25)), "knee": v3((_m * _kn[0], _kn[1], _kn[2])),
                            "ankle": v3((_m * _an[0], _an[1], _an[2])), "sx": _m,
                            "sy": -1 if _n == "LF" else (1 if _n == "LH" else 0)}
# a ripple gait: on each side the legs swing rear, middle, front in turn; the right side half a loop after the left
PHASE = {"LF": 0.0, "LM": 1 / 3, "LH": 2 / 3, "RF": 0.5, "RM": 5 / 6, "RH": 1 / 6}

CABLES = {"1": -0.32, "2": 0.0, "3": 0.32}


def _cable_pts(x):
    return [v3((x, 1.0, 1.22)), v3((x * 1.05, 1.36, 1.1)), v3((x * 1.15, 1.6, 0.72)), v3((x * 1.25, 1.74, 0.32)),
            v3((x * 1.3, 1.82, 0.13))]


BONES = [
    ("root", (0, 0.0, 1.25), (0, 0.0, 1.5), None),
    ("core", tuple(CC), tuple(CC + EYE_D * 0.3), "root"),
    ("rage", tuple(CC), tuple(CC + v3((0, 0, 0.2))), "core"),
    ("pulse", tuple(CC), tuple(CC + v3((0, 0, 0.2))), "root"),
    ("ringA", tuple(CC), tuple(CC + NA * 0.3), "root"),
    ("ringB", tuple(CC), tuple(CC + NB * 0.3), "root"),
    ("crown", tuple(CROWN), tuple(CROWN + v3((0, 0, 0.2))), "root"),
    ("door", tuple(HINGE), tuple(HINGE + v3((0, 0, DOOR_H))), "root"),
    ("bay", (0, -0.6, 1.34), (0, -0.75, 1.34), "root"),
    ("deploy", tuple(M0), tuple(M0 + v3((0, 0, 0.3))), None),          # (parentless: it rides out of the bay)
]
for _s, _sx in (("L", 1), ("R", -1)):
    BONES.append(("lamp." + _s, (_sx * 0.36, -1.29, 1.7), (_sx * 0.36, -1.4, 1.7), "root"))
for _k, _x in CABLES.items():
    _p = _cable_pts(_x)
    BONES.append(("cable." + _k, tuple(_p[0]), tuple(_p[-1]), "root"))
for _n, _L in LEGS.items():
    BONES += [("thigh." + _n, tuple(_L["hip"]), tuple(_L["knee"]), "root"),
              ("shin." + _n, tuple(_L["knee"]), tuple(_L["ankle"]), "thigh." + _n),
              ("foot." + _n, tuple(_L["ankle"]), tuple(_L["ankle"] - v3((0, 0, 0.2))), "shin." + _n)]

MATS = {
    "armor": ("armor", dict(name="RB_CoreArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.42), (4, BLACK, 0.45),
                                                         (5, DECKC, 0.5)], seams=[2], wear=1.1, scale=2.0)),
    "frame": ("gunmetal", dict(name="RB_CoreFrame", base=(0.21, 0.22, 0.25), labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6),
                                                                                      (4, BLACK, 0.5)], seams=[2], scale=2.0)),
    "chrome": ("chrome", dict(name="RB_CoreChrome")),
    "socket": ("lens_socket", dict(name="RB_CoreSocket")),
    "cable": ("rubber", dict(name="RB_CoreCable")),
    "glow": ("glow", dict(name="RB_CoreGlow", col=CYAN)),
}
GLOW = {"Core": (CYAN, 1.5, 0.6), "Iris": (RED_GLOW, 1.7, 0.5), "Rage": (RAGE, 1.9, 0.55), "Pulse": (CYAN, 1.9, 0.7),
        "CrownTips": (RED_GLOW, 1.7, 0.5), "DeckGlow": (CYAN, 1.4, 0.55), "Leds": (CYAN, 1.5, 0.55), "BayGlow": (CYAN, 1.4, 0.6),
        "DeployGlow": (CYAN, 1.5, 0.6), "DeployEye": (RED_GLOW, 1.7, 0.5)}
LOW_TARGETS = {"Hull": 2400, "Belly": 260, "Turret": 520, "Cage": 2000, "Core": 520, "CoreGrid": 700, "Bezel": 380, "Iris": 120,
               "Pupil": 60, "Rage": 420, "Pulse": 300, "RingA": 420, "RingAPlates": 480, "RingB": 460, "RingBPlates": 380,
               "Crown": 700, "CrownTips": 70, "Conduits": 420, "DeckGlow": 120, "Leds": 120, "Door": 320, "BayGlow": 30,
               "Deploy": 1300, "DeployGlow": 90, "DeployEye": 30, "Sled": 100}
for _s in "LR":
    GLOW["Lamp" + _s] = (LAMP, 1.6, 0.5)
    LOW_TARGETS["Lamp" + _s] = 40
for _k in CABLES:
    LOW_TARGETS.update({"Cable" + _k: 200, "Plug" + _k: 120})
for _n in LEGS:
    GLOW["LegGlow" + _n] = (CYAN, 1.4, 0.55)
    LOW_TARGETS.update({"Hip" + _n: 150, "Thigh" + _n: 250, "Piston" + _n: 70, "Knee" + _n: 150, "KneeCap" + _n: 100,
                        "Shin" + _n: 190, "ShinPlate" + _n: 140, "LegGlow" + _n: 40, "Foot" + _n: 230})


# ------------------------------------------------------------------------------------------------ shapes
def _sph(P):
    q = P - CC.astype(F)
    r = np.sqrt((q * q).sum(1)) + F(1e-9)
    th = np.arccos(np.clip(q[:, 2] / r, -1, 1))
    ph = np.arctan2(q[:, 1], q[:, 0])
    return q, r, th, ph


TH_CUP, TH_CAP = math.radians(125), math.radians(24)


def _cage_regions(P):
    q, r, th, ph = _sph(P)
    daz = np.abs((ph % F(math.pi / 2)) - F(math.pi / 4))           # (angle to the nearest petal: 45 + 90k degrees)
    hw = F(0.16) + F(0.08) * np.cos(th) ** 2
    strip = F(CAGE_R) * np.sin(th) * daz - hw
    cup = F(CAGE_R) * (F(TH_CUP) - th)
    cap = F(CAGE_R) * (th - F(TH_CAP))
    return r, th, strip, cup, cap


def cage_sd(P):
    r, th, strip, cup, cap = _cage_regions(P)
    shell = np.abs(r - F(CAGE_R)) - F(CAGE_T)
    region = np.minimum(np.minimum(strip, cup), cap)
    return smax(shell, region, 0.012)


def _ring_frame(n):
    return rot_from_axes(z_axis=n)


def _sentinel_fields():
    """The Sentinel's parts (rest pose), scaled to MINI and stood at M0: one armour field (its frames and chrome as
    darker / lighter labels), its cyan glows and its red eye slit."""
    import robot_sentinel as sn
    lab = {"armor": 0, "frame": 3, "chrome": 5, "socket": 4}
    body, glow, eye = Field("Deploy"), Field("DeployGlow"), Field("DeployEye")
    s = F(MINI)
    T = M0.astype(F)
    for name, f, vx, bone, mk in sn.parts(False):
        lo, hi = f.bounds()
        fn = (lambda P, f=f: f.eval((P - T) / s) * s)
        pr = Func(fn, M0 + MINI * (lo - 0.03), M0 + MINI * (hi + 0.03))
        if name in sn.GLOW:
            (eye if name == "Eye" else glow).add(pr, k=0.0)
        else:
            body.add(pr, k=0.0, label=lab.get(mk, 0))
    return body, glow, eye


def parts(fine=False):
    vx = 0.008 if fine else 0.014
    vs = 0.0055 if fine else 0.01
    vm = 0.0035 if fine else 0.006            # (the little Sentinel in the bay)
    out = []
    # ---- the hull with the prow: white plates, the bay cut into the prow, deck conduit grooves, stripes, seams
    f = Field("Hull")
    f.add(HULL)
    f.add(PROW, k=0.03)
    f.sub(RoundBox((BAY_LO + BAY_HI) / 2, (BAY_HI - BAY_LO) / 2, 0.03), k=0.012)
    for sx in (-1, 1):
        f.sub(RoundCone((sx * 0.6, -0.38, DECK + 0.01), (sx * 0.6, 0.72, DECK + 0.01), 0.034), k=0.008)
    f.paint(Func(lambda P: P[:, 2] - F(1.0), (-1.2, -1.5, 0.7), (1.2, 1.2, 2.2)), 3)                     # the belly
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(1.015)) - F(0.005), (-1.2, -1.5, 0.7), (1.2, 1.2, 2.2)), 2)
    f.paint(Func(lambda P: np.maximum(F(DECK - 0.03) - P[:, 2], P[:, 1] - F(1.0)), (-1.2, -0.5, 1.4), (1.2, 1.2, 1.7)), 5)   # the deck
    for y in (-0.36, 0.46):
        f.paint(RoundBox((0, y, 1.3), (1.2, 0.004, 0.5)), 2)                                           # plate seams
    for sx in (-1, 1):
        f.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 2] - F(1.43)) - F(0.016), F(0.5) - P[:, 0] * F(sx)),
                     (-1.2, -1.5, 0.7), (1.2, 1.2, 2.2)), 1)                                           # orange pinstripes
        f.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 2] - F(1.12)) - F(0.008), F(0.5) - P[:, 0] * F(sx)),
                     (-1.2, -1.5, 0.7), (1.2, 1.2, 2.2)), 1)
    # the prow: the bay's inside dark, hazard stripes framing its mouth, an orange band over it
    f.paint(RoundBox((BAY_LO + BAY_HI) / 2, (BAY_HI - BAY_LO) / 2 + 0.012, 0.03), 4)
    hazard(f, (-0.5, -1.34, 0.84), (0.5, -1.18, 1.95), w=0.08, d=(1, 0, 1),
           band=lambda P: -np.maximum(np.abs(P[:, 0]) - F(0.325), np.maximum(F(0.885) - P[:, 2], P[:, 2] - F(1.795))))
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(1.9)) - F(0.02), P[:, 1] - F(-0.6)), (-0.6, -1.5, 1.7), (0.6, -0.4, 2.1)), 1)
    out.append(("Hull", f, vx, "root", "armor"))
    f = Field("Belly")
    f.add(RoundBox((0, 0.0, 0.85), (0.5, 0.82, 0.05), 0.03))
    for i in range(7):
        f.sub(RoundBox((0, -0.6 + 0.2 * i, 0.8), (0.34, 0.035, 0.03), 0.01), k=0.004)
    out.append(("Belly", f, vs, "root", "frame"))
    # ---- the turret ring on the deck and the pedestal under the cage's cup
    f = Field("Turret")
    f.add(Cylinder((0, CC[1], DECK + 0.04), 0.5, 0.09, rr=0.025))
    f.add(Torus((0, CC[1], DECK + 0.012), 0.51, 0.022), k=0.008)
    for i in range(16):
        a = i * math.pi / 8
        f.add(Sphere((0.44 * math.cos(a), CC[1] + 0.44 * math.sin(a), DECK + 0.088), 0.017), k=0.004)
    f.add(RoundCone((0, CC[1], DECK + 0.07), (0, CC[1], 1.86), 0.4, 0.33), k=0.03)
    f.paint(Torus((0, CC[1], DECK + 0.012), 0.51, 0.03), 1)
    out.append(("Turret", f, vs, "root", "frame"))
    # ---- the cage: four curved petals from a hazard-banded cup to the cap, orange edges
    lo, hi = CC - 0.8, CC + 0.8
    f = Field("Cage")
    f.add(Func(cage_sd, lo, hi))
    f.paint(Func(lambda P: (lambda r, th, st, cu, ca: np.maximum(np.maximum(np.abs(st + F(0.016)) - F(0.016), -cu), -ca))(*_cage_regions(P)),
                 lo, hi), 1)
    hazard(f, lo, hi, w=0.09, d=(1, 1, 0.3),
           band=lambda P: np.abs(_cage_regions(P)[1] - F(TH_CUP + 0.09)) * F(CAGE_R) - F(0.05))
    f.paint(Func(lambda P: np.maximum(np.abs(_cage_regions(P)[1] - F(math.radians(52))) * F(CAGE_R) - F(0.005),
                                      -_cage_regions(P)[3]), lo, hi), 2)
    f.paint(Func(lambda P: _cage_regions(P)[0] - F(CAGE_R), lo, hi), 3)                              # the inside dark
    out.append(("Cage", f, vx, "root", "armor"))
    # ---- the core: a glowing sphere laced with a gunmetal grid, the eye in front, the red shell (hidden until enraged)
    f = Field("Core")
    f.add(Sphere(CC, CORE_R))
    out.append(("Core", f, vs, "core", "glow"))
    f = Field("Rage")
    f.add(Sphere(CC, CORE_R + 0.017))
    out.append(("Rage", f, vs, "rage", "glow"))
    f = Field("CoreGrid")
    for th in (35, 60, 118, 145):
        a = math.radians(th)
        f.add(Torus(CC + v3((0, 0, (CORE_R + 0.02) * math.cos(a))), (CORE_R + 0.02) * math.sin(a), 0.011))
    for az in (0, 60, 120):
        a = math.radians(az)
        f.add(Torus(CC, CORE_R + 0.022, 0.011, R=rot_from_axes(z_axis=(-math.sin(a), math.cos(a), 0))))
    f.add(Torus(CC, CORE_R + 0.022, 0.012, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.0)
    f.sub(Sphere(CC + EYE_D * CORE_R, 0.25), k=0.01)
    f.add(Cylinder(CC + v3((0, 0, -CORE_R + 0.02)), 0.12, 0.08, rr=0.02), k=0.01)                 # the hub it turns on
    out.append(("CoreGrid", f, vs, "core", "frame"))
    Re = rot_from_axes(z_axis=EYE_D)
    f = Field("Bezel")
    ec = CC + EYE_D * (CORE_R + 0.012)
    f.add(Torus(ec, 0.215, 0.034, R=Re))
    for i in range(10):
        a = i * math.pi / 5 + math.pi / 10
        f.add(Sphere(ec + Re @ v3((math.cos(a) * 0.215, math.sin(a) * 0.215, 0.03)), 0.019), k=0.006)
    f.paint(Torus(ec + EYE_D * 0.015, 0.215, 0.028, R=Re), 1)
    out.append(("Bezel", f, vs, "core", "frame"))
    f = Field("Iris")
    f.add(Ellipsoid(CC + EYE_D * (CORE_R + 0.015), (0.19, 0.19, 0.045), R=Re))
    out.append(("Iris", f, vs, "core", "glow"))
    f = Field("Pupil")
    f.add(Ellipsoid(CC + EYE_D * (CORE_R + 0.056), (0.07, 0.07, 0.014), R=Re))
    out.append(("Pupil", f, vs * 0.8, "core", "socket"))
    f = Field("Pulse")                                      # the EMP's ring of light (hidden until it fires)
    f.add(Torus(CC, 0.72, 0.05))
    f.add(Ellipsoid(CC, (0.62, 0.62, 0.012)), k=0.04)
    out.append(("Pulse", f, vs, "pulse", "glow"))
    # ---- the gyroscope rings: chrome hoops clamped with white plates (8 on A, 6 on B), each in its own plane
    for nm, n, R, cnt in (("RingA", NA, RA, 8), ("RingB", NB, RB, 6)):
        Rr = _ring_frame(n)
        f = Field(nm)
        f.add(Torus(CC, R, RING_T, R=Rr))
        out.append((nm, f, vs, "ringA" if nm == "RingA" else "ringB", "chrome"))
        f = Field(nm + "Plates")
        for i in range(cnt):
            a = 2 * math.pi * i / cnt
            u = Rr @ v3((math.cos(a), math.sin(a), 0))
            tng = Rr @ v3((-math.sin(a), math.cos(a), 0))
            Rp = rot_from_axes(x_axis=u, y_axis=tng)
            f.add(RoundBox(CC + u * R, (0.07, 0.11, 0.065), 0.03, R=Rp))
            f.paint(RoundBox(CC + u * R, (0.2, 0.025, 0.2), R=Rp), 1)
            f.paint(RoundBox(CC + u * R + tng * 0.065, (0.2, 0.004, 0.2), R=Rp), 2)
            f.paint(RoundBox(CC + u * R - tng * 0.065, (0.2, 0.004, 0.2), R=Rp), 2)
        out.append((nm + "Plates", f, vs, "ringA" if nm == "RingA" else "ringB", "armor"))
    # ---- the crown: a gunmetal collar on the cap, six spires round a tall middle one, orange bands, red tips
    f = Field("Crown")
    g = Field("CrownTips")
    f.add(Cylinder(CROWN + v3((0, 0, 0.02)), 0.2, 0.1, rr=0.03))
    f.add(Torus(CROWN + v3((0, 0, -0.02)), 0.21, 0.025), k=0.01)
    tips = [(CROWN + v3((0, 0, 0.06)), CROWN + v3((0, 0, 0.36)), 0.05)]
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3
        d = v3((math.cos(a), math.sin(a), 0))
        ln = 0.26 if i % 2 == 0 else 0.18
        b = CROWN + d * 0.14 + v3((0, 0, 0.05))
        tips.append((b, b + norm(d * 0.33 + v3((0, 0, 1))) * ln, 0.032))
    for b, t, r in tips:
        f.add(RoundCone(b, t, r, r * 0.4), k=0.012)
        f.add(Cylinder(b + (t - b) * 0.45, r * 1.15, 0.03, rr=0.008, R=rot_from_axes(z_axis=t - b)), k=0.006)
        f.paint(Cylinder(b + (t - b) * 0.45, r * 1.4, 0.034, R=rot_from_axes(z_axis=t - b)), 1)
        g.add(Sphere(t + norm(t - b) * 0.012, r * 0.62))
    f.paint(Torus(CROWN + v3((0, 0, -0.02)), 0.21, 0.032), 1)
    out.append(("Crown", f, vs, "crown", "frame"))
    out.append(("CrownTips", g, vs, "crown", "glow"))
    # ---- conduits from the deck into the cup (thick ribbed hoses), the deck's glowing grooves, status lights at the back
    f = Field("Conduits")
    for sx in (-1, 1):
        for p0, p1, p2 in (((sx * 0.3, -0.42, DECK), (sx * 0.42, -0.4, 1.86), (sx * 0.3, -0.25, 2.0)),
                           ((sx * 0.62, 0.0, DECK), (sx * 0.7, 0.1, 1.84), (sx * 0.52, 0.12, 2.0))):
            p0, p1, p2 = v3(p0), v3(p1), v3(p2)
            pts = [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2 for t in np.linspace(0, 1, 7)]
            for a, b in zip(pts[:-1], pts[1:]):
                f.add(RoundCone(a, b, 0.045), k=0.01)
            for p in pts[1:-1]:
                f.add(Sphere(p, 0.055), k=0.006)
            f.add(Cylinder(p0 + v3((0, 0, 0.02)), 0.075, 0.05, rr=0.012), k=0.01)
    out.append(("Conduits", f, vs, "root", "cable"))
    f = Field("DeckGlow")
    for sx in (-1, 1):
        f.add(RoundCone((sx * 0.6, -0.38, DECK + 0.01), (sx * 0.6, 0.72, DECK + 0.01), 0.023))
    out.append(("DeckGlow", f, vs, "root", "glow"))
    f = Field("Leds")
    for row, z in enumerate((1.38, 1.44)):
        for i in range(7):
            x = -0.48 + 0.16 * i
            if abs(x) < 0.4 and row == 0:
                continue
            f.add(RoundBox((x, 0.995, z), (0.035, 0.012, 0.012), 0.008))
    out.append(("Leds", f, vs, "root", "glow"))
    # ---- the bay door (hinged at its foot: a ramp when open), the bay's glow, the launch lamps
    f = Field("Door")
    dc = HINGE + v3((0, -0.012, DOOR_H / 2))
    f.add(RoundBox(dc, (0.325, 0.022, DOOR_H / 2 + 0.005), 0.014))
    f.add(Cylinder(HINGE, 0.03, 0.68, rr=0.01, R=X_AX), k=0.006)
    hazard(f, dc - v3((0.4, 0.2, DOOR_H / 2 + 0.05)), dc + v3((0.4, 0.0, DOOR_H / 2 + 0.05)), w=0.08, d=(1, 0, 1),
           band=lambda P: np.maximum(P[:, 1] - F(dc[1] - 0.003),                          # a hazard border on its outer face
                                     -np.maximum(np.abs(P[:, 0]) - F(0.25), np.abs(P[:, 2] - F(dc[2])) - F(DOOR_H / 2 - 0.075))))
    for k in range(2):                                                                        # two orange chevrons
        zc = dc[2] - 0.06 + 0.17 * k
        f.paint(Func(lambda P, zc=zc: np.maximum(np.abs(P[:, 2] - F(zc) + np.abs(P[:, 0]) * F(0.6)) - F(0.035),
                                                 np.maximum(np.abs(P[:, 0]) - F(0.2), P[:, 1] - F(dc[1] - 0.003))), dc - 0.6, dc + 0.6), 1)
    f.paint(Func(lambda P: F(dc[1] + 0.008) - P[:, 1], dc - 0.6, dc + 0.6), 3)                               # its inner face
    for k in range(7):                                                                                        # ramp treads
        f.paint(Func(lambda P, k=k: np.maximum(np.abs(P[:, 2] - F(HINGE[2] + 0.1 + 0.11 * k)) - F(0.012), F(dc[1] + 0.01) - P[:, 1]),
                     dc - 0.6, dc + 0.6), 4)
    out.append(("Door", f, vs, "door", "armor"))
    f = Field("BayGlow")
    f.add(RoundBox((0, -0.585, 1.34), (0.3, 0.01, 0.38), 0.008))
    out.append(("BayGlow", f, vs, "bay", "glow"))
    for s, sx in (("L", 1), ("R", -1)):
        f = Field("Lamp" + s)
        f.add(Ellipsoid((sx * 0.355, -1.285, 1.7), (0.03, 0.03, 0.05)))
        out.append(("Lamp" + s, f, vs, "lamp." + s, "glow"))
    # ---- the Sentinel standing ready in the bay, on its launch sled
    body, glow, eye = _sentinel_fields()
    out.append(("Deploy", body, vm, "deploy", "armor"))
    out.append(("DeployGlow", glow, vm, "deploy", "glow"))
    out.append(("DeployEye", eye, vm, "deploy", "glow"))
    f = Field("Sled")
    f.add(RoundBox(M0 + v3((0, -0.02, -0.013)), (0.17, 0.2, 0.012), 0.008))
    f.paint(Func(lambda P: np.abs(P[:, 0]) - F(0.12), M0 - 0.5, M0 + 0.5), 1)
    out.append(("Sled", f, vs, "deploy", "frame"))
    # ---- the torn-out data cables trailing from its back, their plugs dragging
    for k, x in CABLES.items():
        pts = _cable_pts(x)
        f = Field("Cable" + k)
        for a, b in zip(pts[:-1], pts[1:]):
            f.add(RoundCone(a, b, 0.05), k=0.02)
        f.add(Cylinder(pts[0] + v3((0, 0.02, 0)), 0.075, 0.06, rr=0.015, R=Y_AX), k=0.01)     # its socket
        out.append(("Cable" + k, f, vs, "cable." + k, "cable"))
        f = Field("Plug" + k)
        d = norm(pts[-1] - pts[-2])
        f.add(Cylinder(pts[-1], 0.08, 0.16, rr=0.02, R=rot_from_axes(z_axis=d)))
        for sx in (-1, 1):
            f.add(RoundCone(pts[-1] + d * 0.08 + v3((sx * 0.03, 0, 0)), pts[-1] + d * 0.15 + v3((sx * 0.03, 0, 0)), 0.012), k=0.004)
        f.paint(Func(lambda P, c=pts[-1], d=d: np.abs((P - c.astype(F)) @ d.astype(F)) - F(0.02), pts[-1] - 0.3, pts[-1] + 0.3), 1)
        out.append(("Plug" + k, f, vs, "cable." + k, "frame"))
    # ---- the legs
    for n, L in LEGS.items():
        hp, kn, an, sx = L["hip"], L["knee"], L["ankle"], L["sx"]
        tax, sax = norm(kn - hp), norm(an - kn)
        Rt = rot_from_axes(z_axis=tax, x_axis=(sx, 0, 0))
        Rs = rot_from_axes(z_axis=sax, x_axis=(sx, 0, 0))
        f = Field("Hip" + n)
        f.add(Cylinder(hp - v3((sx * 0.06, 0, 0)), 0.19, 0.16, rr=0.035, R=X_AX))
        f.add(Sphere(hp, 0.15), k=0.02)
        f.paint(Torus(hp, 0.19, 0.026, R=X_AX), 1)
        out.append(("Hip" + n, f, vs, "root", "frame"))
        tl = float(np.linalg.norm(kn - hp))
        f = Field("Thigh" + n)
        f.add(RoundBox(hp + tax * (tl * 0.52), (0.14, 0.13, tl * 0.42), 0.06, R=Rt))
        f.add(RoundBox(hp + tax * (tl * 0.52) + v3((0, 0, 0.085)), (0.06, 0.05, tl * 0.36), 0.035, R=Rt), k=0.03)
        hazard(f, hp + tax * (tl * 0.72) - 0.35, hp + tax * (tl * 0.86) + 0.35, w=0.07, d=(1, 1, 1),
               band=lambda P, o=hp + tax * (tl * 0.79), ax=tax: np.abs((P - o.astype(F)) @ ax.astype(F)) - F(tl * 0.07))
        f.paint(Func(lambda P, o=hp + tax * (tl * 0.4), ax=tax: np.abs((P - o.astype(F)) @ ax.astype(F)) - F(0.005), hp - 1, hp + 1.5), 2)
        out.append(("Thigh" + n, f, vx, "thigh." + n, "armor"))
        f = Field("Piston" + n)
        f.add(RoundCone(hp + tax * 0.16 + v3((0, 0, -0.12)), hp + tax * (tl * 0.85) + v3((0, 0, -0.12)), 0.035))
        out.append(("Piston" + n, f, vs, "thigh." + n, "chrome"))
        f = Field("Knee" + n)
        f.add(Sphere(kn, 0.15))
        f.add(Cylinder(kn, 0.11, 0.36, rr=0.03, R=Y_AX), k=0.02)
        out.append(("Knee" + n, f, vs, "shin." + n, "frame"))
        f = Field("KneeCap" + n)
        f.add(Ellipsoid(kn + v3((sx * 0.02, 0, 0.08)), (0.17, 0.19, 0.1)))
        f.sub(Sphere(kn - v3((0, 0, 0.02)), 0.135), k=0.02)
        f.paint(Sphere(kn, 1.0), 1)
        f.paint(Func(lambda P, kn=kn: np.abs(P[:, 0] - F(kn[0])) - F(0.005), kn - 0.3, kn + 0.3), 2)
        out.append(("KneeCap" + n, f, vs, "shin." + n, "armor"))
        f = Field("Shin" + n)
        f.add(RoundCone(kn + sax * 0.1, an, 0.12, 0.09))
        f.add(Sphere(an, 0.13), k=0.02)
        f.paint(Func(lambda P, o=an, ax=sax: np.abs((P - o.astype(F)) @ ax.astype(F) + F(0.22)) - F(0.028), an - 0.5, an + 0.5), 1)
        out.append(("Shin" + n, f, vs, "shin." + n, "frame"))
        sl = float(np.linalg.norm(an - kn))
        f = Field("ShinPlate" + n)
        pc = kn + sax * (sl * 0.45) + v3((sx * 0.11, 0, 0))
        f.add(RoundBox(pc, (0.05, 0.15, sl * 0.3), 0.04, R=Rs))
        f.sub(RoundBox(pc + v3((sx * 0.045, 0, 0)), (0.022, 0.025, sl * 0.26), 0.01, R=Rs), k=0.006)
        f.paint(Func(lambda P, o=pc, ax=sax: np.abs(np.abs((P - o.astype(F)) @ ax.astype(F)) - F(sl * 0.27)) - F(0.014), pc - 1, pc + 1), 1)
        out.append(("ShinPlate" + n, f, vs, "shin." + n, "armor"))
        f = Field("LegGlow" + n)
        f.add(RoundBox(pc + v3((sx * 0.04, 0, 0)), (0.013, 0.017, sl * 0.25), 0.012, R=Rs))
        out.append(("LegGlow" + n, f, vs, "shin." + n, "glow"))
        f = Field("Foot" + n)
        f.add(Cylinder(an - v3((0, 0, 0.19)), 0.27, 0.14, rr=0.05))
        f.add(RoundCone(an - v3((0, 0, 0.12)), an - v3((0, 0, 0.02)), 0.17, 0.1), k=0.03)
        fwd = norm(v3((sx * 0.55, (L["sy"] if L["sy"] else 0.0) * 0.8 - (0.0 if L["sy"] else 0.0), 0)) + v3((sx * 0.3, 0, 0)))
        for a in (-0.75, 0.0, 0.75):
            ca, sa = math.cos(a), math.sin(a)
            d = norm(v3((fwd[0] * ca - fwd[1] * sa, fwd[0] * sa + fwd[1] * ca, 0)))
            f.add(RoundCone(an - v3((0, 0, 0.18)) + d * 0.2, an - v3((0, 0, 0.215)) + d * 0.36, 0.055, 0.024), k=0.025)
            f.paint(Sphere(an - v3((0, 0, 0.215)) + d * 0.36, 0.065), 1)
        f.paint(Func(lambda P, an=an: P[:, 2] - F(an[2] - 0.24), an - 0.7, an + 0.7), 4)
        out.append(("Foot" + n, f, vs, "foot." + n, "frame"))
    return out


# ------------------------------------------------------------------------------------------------ clips
V = lambda *a: Vector(a)
HIDE = 0.01


def _leg(arm, n, ankle, pitch=0.0):
    L = LEGS[n]
    la, lb = bone_len(arm, "thigh." + n), bone_len(arm, "shin." + n)
    pole = V(L["sx"] * 0.7, L["sy"] * 0.25, 1.0)
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


def gait(arm, t, step=WALK_STEP, lift=0.26):
    """The ripple gait at loop time t: each foot planted DUTY of the loop (sliding back under the body by `step`),
    swung forward the rest, lifted, its pad tipped up a little."""
    aims = {}
    for n, L in LEGS.items():
        ph = (t + PHASE[n]) % 1.0
        if ph < DUTY:
            y, z, p = -step / 2 + step * ph / DUTY, 0.0, 0.0
        else:
            k = (ph - DUTY) / (1 - DUTY)
            e = 0.5 - 0.5 * math.cos(math.pi * k)
            y = step / 2 - step * e
            z = lift * math.sin(math.pi * k) ** 1.4
            p = 0.25 * math.sin(math.pi * k) * (1.2 - k)
        aims.update(_leg(arm, n, Vector(L["ankle"]) + V(0, y, z), p))
    return aims


def _body(t):
    """The hull's gentle sway over its planted feet (toward the side with three feet down) and a dip at each swing."""
    w = 2 * math.pi * t
    sway = 0.03 * math.sin(w + 0.5)
    dip = -0.016 * (0.5 + 0.5 * math.cos(6 * w))
    return V(sway, 0.0, dip + 0.008), Quaternion(V(0, 1, 0), 0.02 * math.sin(w + 0.5)) @ Quaternion(V(1, 0, 0), 0.008 * math.sin(6 * w))


def _twist(a):
    return lambda P, base: (base.col[1].xyz.copy(), a)


def _look(arm, yaw, pitch=0.0):
    d = Quaternion(V(0, 0, 1), yaw) @ (Quaternion(V(1, 0, 0), pitch) @ Vector(EYE_D))
    return rel(arm, "core", d)


def _door(arm, ang):
    return rel(arm, "door", (0.0, -math.sin(ang), math.cos(ang)))


def _deploy(arm, off):
    """The little Sentinel moved by `off` (rest space), carried by the hull's pose."""
    rest = arm.data.bones["deploy"].matrix_local.copy()
    rr = arm.data.bones["root"].matrix_local.inverted()
    def fn(P, base):
        return ("world", P["root"] @ rr @ Matrix.Translation(Vector(off)) @ rest)
    return fn


def _ramp_point(s):
    """A point on the open ramp's surface, s along it from the hinge (rest space)."""
    a = DOOR_OPEN
    d = v3((0, -math.sin(a), math.cos(a)))
    up = v3((0, math.cos(a), math.sin(a)))
    return HINGE + d * s + up * 0.012


def _cables(arm, t, amp=1.0):
    out = {}
    for i, k in enumerate(CABLES):
        p = _cable_pts(CABLES[k])
        d = Vector(tuple(p[-1] - p[0]))
        sw = Quaternion(V(0, 0, 1), amp * 0.06 * math.sin(2 * math.pi * t + i * 1.3))
        out["cable." + k] = rel(arm, "cable." + k, sw @ d)
    return out


RATE_A = (2 * math.pi / 8) / WALK_FRAMES      # the rings' slow turn: one clamp spacing per loop (seamless)
RATE_B = -(2 * math.pi / 6) / WALK_FRAMES


def _pose(arm, P, f, tg, step=WALK_STEP, root_add=(0, 0, 0), pitch=0.0, roll=0.0, look=(0.0, 0.0), ring=(0.0, 0.0),
          door=0.0, deploy=(0, 0, 0), sc=None, crown=(0.0, 0.0), cable_amp=1.0):
    aims = gait(arm, tg, step)
    root_off, root_rot = _body(tg)
    root_off = root_off + V(*root_add)
    root_rot = Quaternion(V(1, 0, 0), pitch) @ Quaternion(V(0, 1, 0), roll) @ root_rot
    aims["core"] = _look(arm, *look)
    aims["ringA"] = _twist(ring[0])
    aims["ringB"] = _twist(ring[1])
    aims["door"] = _door(arm, door)
    aims["deploy"] = _deploy(arm, deploy)
    aims["crown"] = rel(arm, "crown", (crown[0], crown[1], 1.0))
    aims.update(_cables(arm, tg, cable_amp))
    scales = {"rage": HIDE, "pulse": HIDE}
    scales.update(sc or {})
    ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, scales=scales)
    P.key(ch, f)


def walk(arm, name="Walk", rage=False):
    """The ripple gait; the eye looks about, the rings turn slowly (fast and the core red: WalkRage), the cables drag."""
    P = Poser(arm)
    act = ra.new_action(arm, name)
    m = 8 if rage else 1                       # (8: ring A one full turn a loop, B 8/6 of a turn: still seamless)
    for f in range(WALK_FRAMES + 1):
        t = f / WALK_FRAMES
        w = 2 * math.pi * t
        look = (0.3 * math.sin(w + 0.8), -0.06 + 0.05 * math.sin(2 * w)) if not rage else \
            (0.12 * math.sin(2 * w + 0.8), -0.12 + 0.03 * math.sin(4 * w))
        sc = {"core": 1.0 + 0.02 * math.sin(4 * w), "bay": 1.0, "crown": 1.0}
        if rage:
            sc.update({"rage": 1.0, "core": 1.0 + 0.03 * math.sin(8 * w)})
        _pose(arm, P, f, t, look=look, ring=(m * RATE_A * f, m * RATE_B * f), sc=sc,
              crown=(0.012 * math.sin(w), 0.01 * math.sin(2 * w)) if not rage else (0.02 * math.sin(6 * w), 0.02 * math.sin(4 * w)))
    ra.finish_action(arm, act, WALK_FRAMES, True)


def _spin(rate_mult, frames):
    """Ring angles per frame for an angular speed multiplier rate_mult(f) (integrated)."""
    a, b, out = 0.0, 0.0, []
    for f in range(frames + 1):
        out.append((a, b))
        m = rate_mult(f)
        a += RATE_A * m
        b += RATE_B * m
    return out


def emp(arm):
    """It braces (sinking, the prow down a touch), the rings spin up (0-20), the core brightens and flickers and the eye
    narrows; at EMP_FIRE the pulse bursts from the core (its ring of light flung out over five frames), the core
    flashes, the hull jolts and the crown shivers; the rings spin down (28-46). The legs walk on."""
    P = Poser(arm)
    act = ra.new_action(arm, "Emp")
    spin = _spin(lambda f: 1.0 + 15.0 * smooth(2, 20, f) * (1.0 - smooth(28, 46, f)), EMP_FRAMES)
    for f in range(EMP_FRAMES + 1):
        t = f / EMP_FRAMES
        brace = smooth(4, 18, f) * (1.0 - smooth(30, 44, f))
        jolt = 0.0
        if f >= EMP_FIRE:
            u = f - EMP_FIRE
            jolt = math.exp(-u * 0.35) * math.cos(u * 1.4)
        charge = smooth(4, EMP_FIRE - 1, f) if f < EMP_FIRE else 0.0
        core = 1.0 + 0.06 * charge + 0.03 * charge * math.sin(f * 2.1)
        if f >= EMP_FIRE:
            core = 1.0 + 0.12 * math.exp(-(f - EMP_FIRE) * 0.4)
        pu = {0: 1.05, 1: 1.7, 2: 2.3, 3: 2.8, 4: 3.15, 5: 3.4}.get(f - EMP_FIRE, HIDE)
        sc = {"core": core, "pulse": pu, "crown": 1.0 + 0.04 * charge}
        _pose(arm, P, f, t, root_add=(0.0, 0.0, -0.06 * brace + 0.04 * jolt), pitch=0.02 * brace - 0.03 * jolt,
              look=(0.0, -0.1 * brace), ring=spin[f], sc=sc,
              crown=(0.03 * jolt + 0.01 * charge * math.sin(f * 2.7), 0.02 * jolt))
    ra.finish_action(arm, act, EMP_FRAMES, False)


def summon(arm):
    """It dips its prow and the bay door drops open into a ramp (2-12) while the bay and the launch lamps blaze and the
    eye turns down to watch; the Sentinel in the bay rides out on its sled (9-15) and down the ramp, standing on it at
    SUMMON_FRAME, where it is released (hidden: the game's Sentinel takes its place); the door closes (29-42) and a
    fresh Sentinel stands in the bay. The legs walk on."""
    P = Poser(arm)
    act = ra.new_action(arm, "Summon")
    lip = HINGE + v3((0, 0.03, 0)) - M0                        # the floor's lip: the sled's way out
    s_rel = 0.62                                               # how far down the ramp it rides
    down = _ramp_point(s_rel) - M0
    spin = _spin(lambda f: 1.0 + 3.0 * smooth(0, 10, f) * (1.0 - smooth(30, 44, f)), SUMMON_FRAMES)
    for f in range(SUMMON_FRAMES + 1):
        t = f / SUMMON_FRAMES
        k = smooth(0, 10, f) * (1.0 - smooth(30, 44, f))
        door = DOOR_OPEN * smooth(2, 12, f) * (1.0 - smooth(29, 42, f))
        if f <= 15:
            off = lip * smooth(9, 15, f)
        elif f <= SUMMON_FRAME:
            u = smooth(15, SUMMON_FRAME, f)
            off = lip + (down - lip) * u
        else:
            off = down if f < 42 else v3((0, 0, 0))          # (hidden, then a fresh one stands in the closed bay)
        hidden = SUMMON_FRAME < f < 43
        blaze = smooth(3, 10, f) * (1.0 - smooth(26, 36, f))
        flick = 0.15 * blaze * (1 if (f // 2) % 2 else -1)
        sc = {"deploy": HIDE if hidden else 1.0, "bay": 1.0 + 0.12 * blaze, "lamp.L": 1.0 + 0.6 * blaze + flick,
              "lamp.R": 1.0 + 0.6 * blaze - flick, "core": 1.0 + 0.04 * k, "crown": 1.0}
        _pose(arm, P, f, t, root_add=(0.0, 0.0, -0.05 * k), pitch=0.05 * k, look=(0.0, -0.32 * k),
              ring=spin[f], door=door, deploy=tuple(off), sc=sc)
    ra.finish_action(arm, act, SUMMON_FRAMES, False)


def enrage(arm):
    """It shudders and the core flickers red (6-12) and burns red from RAGE_FRAME, the eye swelling; the rings spin up
    to a blur and stay fast; it rears (10-20), shuddering, the crown quivering, then lowers its front and leans into the
    charge (28-44). Its legs march two loops of the ripple gait: the enraged speed (twice the walk)."""
    P = Poser(arm)
    act = ra.new_action(arm, "Enrage")
    spin = _spin(lambda f: 1.0 + 15.0 * smooth(4, 16, f) - 8.0 * smooth(30, 46, f), ENRAGE_FRAMES)
    for f in range(ENRAGE_FRAMES + 1):
        t = f / ENRAGE_FRAMES
        tg = (2 * t) % 1.0 if f < ENRAGE_FRAMES else 0.0
        shud = smooth(2, 6, f) * (1.0 - smooth(22, 30, f))
        jit = 0.014 * math.sin(f * 2.6) * shud
        rear = smooth(9, 16, f) * (1.0 - smooth(24, 32, f))
        charge = smooth(28, 42, f)
        if f < 6:
            rg = HIDE
        elif f < RAGE_FRAME:
            rg = 1.0 if f in (6, 7, 9, 11, 12) else HIDE                  # a stutter of red, then it holds
        else:
            rg = 1.0
        sc = {"rage": rg, "core": 1.0 + 0.05 * shud * (1 + math.sin(f * 1.9)), "crown": 1.0 + 0.06 * rear}
        _pose(arm, P, f, tg, root_add=(jit, 0.0, -0.05 * smooth(0, 8, f) * (1 - rear) + 0.06 * rear + jit * 0.5),
              pitch=-0.07 * rear + 0.05 * charge, roll=0.6 * jit, look=(0.0, 0.08 * rear - 0.14 * charge),
              ring=spin[f], sc=sc, crown=(0.04 * math.sin(f * 2.2) * (shud + rear), 0.03 * math.sin(f * 1.7) * shud),
              cable_amp=2.0)
    ra.finish_action(arm, act, ENRAGE_FRAMES, False)


def clips(arm):
    walk(arm)
    emp(arm)
    summon(arm)
    enrage(arm)
    walk(arm, "WalkRage", rage=True)
