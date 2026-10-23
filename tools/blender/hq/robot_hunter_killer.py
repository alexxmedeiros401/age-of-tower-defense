"""HUNTER-KILLER, HQ: the Modern Age boss, a heavy robot gunship drone that hunts unseen (it cloaks) and launches
Stealth Jets from its back. An angular stealth hull of faceted white armour plates over a gunmetal belly, an arrowhead
in plan: at its blunt nose a faceted armoured head holding one big red sensor eye in a bolted gunmetal bezel under a
frowning brow, two small red eyes below it; under the head a pair of six-barrelled rotary cannons on ball mounts; on
its back a launch bay (two hazard-striped doors hinged at their outer edges over a dark bay with two launch rails and
orange launch lights at its corners) from which its Stealth Jets launch; behind it two canted tail fins (orange tips)
and two square engine nozzles with cyan exhausts. Stub wings carry, on top, a missile pod each (six tubes, orange-tipped
missiles) and at their tips two big ducted fans on tilt pivots: white ducts with orange rims and hazard bands, gunmetal
stators and a chrome hub, the rotor blades spinning inside. Hazard stripes on its nose and spine, orange pinstripes.
Fly (72 frames, it hovers on its own, no "flying"): it cruises nose-down, bobbing and rolling heavily, its fans
tilted forward and wobbling, rotors spinning, the eye scanning, the rotary cannons idling round, the exhausts pulsing.
Summon (48 frames): it flares (nose up, fans tilted back, rising a little), the bay doors swing open, the launch lights
blaze and its two Stealth Jets launch from the bay at SUMMON_FRAME; the doors close and it settles. In game it turns
into a see-through cyan ghost while it is cloaked. Faces -Y, Z up; hovers about 2.0 model units up (the hull's centre);
model_scale 1.0.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Func, rot_from_axes, v3, norm, F
from robot_stealth_jet import facet, mirror_pts, hazard, rel, smooth
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser

ROOT_NAME = "HunterKiller"
GLB_NAME = "hunter_killer"
TEX_PREFIX = "hunter_killer"
FLY_FRAMES = 72
SUMMON_FRAMES = 48
SUMMON_FRAME = 16          # the doors are open, the lights blaze: the Stealth Jets launch from the bay here

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.22, 0.23, 0.26)
BLACK = (0.07, 0.07, 0.08)
RED_GLOW = (1.0, 0.16, 0.08)
CYAN = (0.3, 0.88, 1.0)
LAMP = (1.0, 0.55, 0.15)

ZC = 2.0                                   # the hull's chine plane (its centre height)
C = v3((0, 0, ZC))
EYE_D = norm(v3((0, -1, -0.06)))           # the big eye looks straight ahead (a touch down)
EYE_C = v3((0, -1.4, 1.99))                # its lens's centre
EYE_R = 0.17
GUN = {sx: v3((sx * 0.25, -1.02, 1.7)) for sx in (-1, 1)}        # the rotary cannons' mounts (they point -Y)
GUN_L = 0.5
BAY = v3((0, 0.36, 2.3))                   # the launch bay's opening (centre, on the back)
BAY_HALF = (0.27, 0.36)
BAY_FLOOR = 2.12
DOOR_OPEN = math.radians(115)
FAN = {sx: v3((sx * 1.17, 0.12, 2.04)) for sx in (-1, 1)}       # the ducted fans' centres
DUCT_R = 0.32                              # inner radius
DUCT_O = 0.41                              # outer
DUCT_H = 0.26
PIVOT_X = 0.66                             # the fans' tilt shafts run from the wing tips (x = +-PIVOT_X ... ) out
NOZ = {sx: v3((sx * 0.17, 1.2, 2.02)) for sx in (-1, 1)}
POD = {sx: v3((sx * 0.655, -0.06, 2.1)) for sx in (-1, 1)}      # the missile pods on the wings


def _station(y, wt, zt, wc, zc, wb, zb):
    return [(wt, y, zt), (wc, y, zc), (wb, y, zb)]


HULL_PTS = mirror_pts(_station(-1.16, 0.13, 2.12, 0.2, ZC, 0.12, 1.86) +
                      _station(-0.6, 0.27, 2.27, 0.44, ZC, 0.27, 1.76) +
                      _station(0.3, 0.38, 2.3, 0.66, ZC, 0.38, 1.72) +
                      _station(0.8, 0.36, 2.28, 0.64, ZC, 0.34, 1.75) +
                      _station(1.2, 0.2, 2.18, 0.34, 2.02, 0.2, 1.88) +
                      [(0.0, -1.0, 2.24), (0.0, -0.4, 2.36), (0.0, 0.9, 2.33)])          # (a low ridge down its spine)
HULL = facet(HULL_PTS, k=0.012)

HEAD_PTS = mirror_pts([(0.24, -1.38, 2.18), (0.28, -1.38, 1.98), (0.22, -1.34, 1.8),          # its front face (the eye)
                       (0.3, -1.1, 2.22), (0.34, -1.1, 1.98), (0.26, -1.05, 1.77), (0.22, -0.9, 2.27),
                       (0.0, -1.0, 2.31), (0.0, -1.37, 2.23), (0.0, -1.3, 1.75)])
HEAD = facet(HEAD_PTS, k=0.01)


def _wing_pts(sx):
    pts = []
    for x, y in ((0.5, -0.42), (PIVOT_X + 0.08, -0.16), (PIVOT_X + 0.08, 0.36), (0.5, 0.48)):
        for dz in (-0.02, 0.02):
            pts.append((sx * x, y, ZC + dz))
    for x, y, t in ((0.5, 0.02, 0.07), (PIVOT_X + 0.08, 0.1, 0.05)):
        for dz in (-t, t):
            pts.append((sx * x, y, ZC + dz))
    return pts


def _fin_pts(sx, cant=math.radians(30)):
    up = v3((sx * math.sin(cant), 0, math.cos(cant)))
    side = v3((math.cos(cant) * sx, 0, -math.sin(cant)))
    o = v3((sx * 0.27, 0.0, 2.24))
    pts = []
    for y, h in ((0.62, 0.0), (1.18, 0.0), (1.25, 0.42), (1.02, 0.42)):
        for t in (-0.008, 0.008):
            pts.append(tuple(o + v3((0, y, 0)) + up * h + side * t))
    for y, h, t in ((0.92, 0.0, 0.035), (1.14, 0.42, 0.014)):
        for s in (-t, t):
            pts.append(tuple(o + v3((0, y, 0)) + up * h + side * s))
    return pts, o, up


LAMPS = [v3((sx * (BAY_HALF[0] + 0.07), BAY[1] + sy * (BAY_HALF[1] + 0.04), 2.305)) for sx in (1, -1) for sy in (-1, 1)]
X_AX = rot_from_axes(z_axis=(1, 0, 0))
Y_AX = rot_from_axes(z_axis=(0, 1, 0))

BONES = [
    ("root", tuple(C), tuple(C + v3((0, 0, 0.2))), None),
    ("eye", tuple(EYE_C - EYE_D * 0.12), tuple(EYE_C + EYE_D * 0.08), "root"),
    ("bay", (BAY[0], BAY[1], BAY_FLOOR), (BAY[0], BAY[1], BAY_FLOOR + 0.25), "root"),
    ("hatch.L", (BAY_HALF[0], BAY[1], BAY[2] + 0.02), (0.02, BAY[1], BAY[2] + 0.02), "root"),
    ("hatch.R", (-BAY_HALF[0], BAY[1], BAY[2] + 0.02), (-0.02, BAY[1], BAY[2] + 0.02), "root"),
]
for i, lp in enumerate(LAMPS):
    BONES.append(("lamp.%d" % i, tuple(lp - v3((0, 0, 0.02))), tuple(lp + v3((0, 0, 0.06))), "root"))
for s, sx in (("L", 1), ("R", -1)):
    BONES += [
        ("fan." + s, (sx * PIVOT_X, FAN[sx][1], FAN[sx][2]), tuple(FAN[sx]), "root"),
        ("rotor." + s, tuple(FAN[sx]), tuple(FAN[sx] + v3((0, 0, 0.2))), "fan." + s),
        ("gun." + s, tuple(GUN[sx]), tuple(GUN[sx] + v3((0, -0.25, 0))), "root"),
        ("exhaust." + s, tuple(NOZ[sx] + v3((0, 0.04, 0))), tuple(NOZ[sx] + v3((0, 0.24, 0))), "root"),
    ]

MATS = {
    "armor": ("armor", dict(name="RB_HKArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.42), (4, BLACK, 0.45)],
                            seams=[2], wear=1.1, scale=2.0)),
    "frame": ("gunmetal", dict(name="RB_HKFrame", base=(0.21, 0.22, 0.25), labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6),
                                                                                    (4, BLACK, 0.5)], seams=[2], scale=2.0)),
    "chrome": ("chrome", dict(name="RB_HKChrome")),
    "rubber": ("rubber", dict(name="RB_HKBlade", base=(0.13, 0.13, 0.15))),
    "glow": ("glow", dict(name="RB_HKGlow", col=RED_GLOW)),
}
GLOW = {"Eye": (RED_GLOW, 1.6, 0.5), "SmallEyes": (RED_GLOW, 1.5, 0.5), "ExhaustL": (CYAN, 1.4, 0.55), "ExhaustR": (CYAN, 1.4, 0.55)}
for _i in range(4):
    GLOW["Lamp%d" % _i] = (LAMP, 1.4, 0.5)

LOW_TARGETS = {"Hull": 2600, "Head": 700, "Brow": 200, "Bezel": 420, "Eye": 140, "Pupil": 50, "SmallEyes": 60, "Bay": 520,
               "DoorL": 240, "DoorR": 240, "Lamp0": 24, "Lamp1": 24, "Lamp2": 24, "Lamp3": 24, "Fins": 360, "Nozzles": 420, "ExhaustL": 70, "ExhaustR": 70,
               "Belly": 360}
for s in "LR":
    LOW_TARGETS.update({"Wing" + s: 260, "Pod" + s: 520, "Duct" + s: 900, "Stator" + s: 420, "Blades" + s: 300,
                        "Gun" + s: 560, "Mount" + s: 220})

UNDER = Func(lambda P: P[:, 2] - F(ZC - 0.006), (-3, -3, 1), (3, 3, 3))


def parts(fine=False):
    vx = 0.0075 if fine else 0.013
    vs = 0.005 if fine else 0.009
    out = []
    # ---- the hull: faceted white plates, a gunmetal belly, the launch bay cut into its back, panel lines, stripes
    f = Field("Hull")
    f.add(HULL)
    f.sub(RoundBox(v3((BAY[0], BAY[1], (BAY[2] + BAY_FLOOR) / 2 + 0.05)), (BAY_HALF[0], BAY_HALF[1], (BAY[2] - BAY_FLOOR) / 2 + 0.1),
                   0.03), k=0.012)
    f.paint(UNDER, 3)
    for y in (-0.62, -0.12, 0.92):
        f.paint(RoundBox((0, y, 2.25), (0.7, 0.004, 0.12)), 2)
    for sx in (-1, 1):
        f.paint(RoundBox((sx * 0.38, 0.1, 2.25), (0.004, 0.8, 0.12)), 2)
        f.paint(RoundBox((sx * 0.33, 0.36, 2.25), (0.012, 0.42, 0.12)), 1)                         # pinstripes by the bay
        f.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 2] - F(2.04)) - F(0.018), F(-0.5) - P[:, 1] + F(0) * P[:, 0]),
                     (-1, -1.3, 1.9), (1, 1.3, 2.1)), 1)                                        # an orange chine stripe
    hazard(f, (-0.3, -0.92, 2.15), (0.3, -0.7, 2.4), w=0.07, d=(1, 1, 0))                          # on its brow, behind the head
    f.paint(RoundBox(v3((0, BAY[1], 2.2)), (BAY_HALF[0] + 0.015, BAY_HALF[1] + 0.015, 0.2), 0.03), 4)   # the bay's inside
    out.append(("Hull", f, vx, "root", "armor"))
    # ---- the belly: a gunmetal keel plate with vents
    f = Field("Belly")
    f.add(RoundBox((0, 0.1, 1.73), (0.28, 0.6, 0.03), 0.02))
    for i in range(5):
        f.sub(RoundBox((0, -0.25 + 0.15 * i, 1.7), (0.2, 0.025, 0.02), 0.01), k=0.004)
    out.append(("Belly", f, vs, "root", "frame"))
    # ---- the head at its nose: faceted armour round the big eye's socket, a hazard band
    f = Field("Head")
    f.add(HEAD)
    f.sub(Sphere(EYE_C - EYE_D * 0.02, EYE_R + 0.035), k=0.015)
    f.paint(UNDER, 3)
    f.paint(Func(lambda P: np.abs(P[:, 1] - F(-1.05)) - F(0.025), (-1, -1.5, 1.7), (1, -0.8, 2.4)), 1)
    out.append(("Head", f, vx, "root", "armor"))
    f = Field("Brow")                                         # two angled plates over the eye: a frown
    for sx in (-1, 1):
        f.add(RoundBox(EYE_C + v3((sx * 0.1, -0.04, 0.2)), (0.12, 0.07, 0.03), 0.025,
                       R=rot_from_axes(x_axis=(1, 0, sx * 0.4), y_axis=(0, -1, -0.5))), k=0.02)
    f.paint(Func(lambda P: F(-1.36) - P[:, 1], (-1, -1.6, 1.9), (1, -1.0, 2.4)), 1)
    out.append(("Brow", f, vs, "root", "armor"))
    Re = rot_from_axes(z_axis=EYE_D)
    f = Field("Bezel")
    f.add(Torus(EYE_C - EYE_D * 0.01, EYE_R + 0.01, 0.035, R=Re))
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        f.add(Sphere(EYE_C + Re @ v3((math.cos(a) * (EYE_R + 0.012), math.sin(a) * (EYE_R + 0.012), 0.03)), 0.017), k=0.006)
    out.append(("Bezel", f, vs, "root", "frame"))
    f = Field("Eye")
    f.add(Ellipsoid(EYE_C - EYE_D * 0.01, (EYE_R, EYE_R, 0.07), R=Re))
    out.append(("Eye", f, vs, "eye", "glow"))
    f = Field("Pupil")
    f.add(Ellipsoid(EYE_C + EYE_D * 0.055, (0.06, 0.06, 0.014), R=Re))
    out.append(("Pupil", f, vs * 0.8, "eye", "rubber"))
    f = Field("SmallEyes")
    for sx in (-1, 1):
        f.add(Sphere(v3((sx * 0.2, -1.35, 1.84)), 0.034))
    out.append(("SmallEyes", f, vs, "root", "glow"))
    # ---- the launch bay: its floor and walls (dark), two launch rails; the doors; launch lights at its corners
    f = Field("Bay")
    f.add(RoundBox(v3((0, BAY[1], BAY_FLOOR - 0.02)), (BAY_HALF[0] + 0.02, BAY_HALF[1] + 0.02, 0.03), 0.01))
    for sx in (-1, 1):
        f.add(RoundBox(v3((sx * 0.13, BAY[1], BAY_FLOOR + 0.03)), (0.025, BAY_HALF[1] - 0.03, 0.025), 0.008), k=0.006)
        f.add(RoundBox(v3((sx * 0.13, BAY[1] - BAY_HALF[1] + 0.06, BAY_FLOOR + 0.06)), (0.04, 0.03, 0.035), 0.01), k=0.006)
        f.paint(RoundBox(v3((sx * 0.13, BAY[1], BAY_FLOOR + 0.05)), (0.03, 0.06, 0.03)), 1)
    out.append(("Bay", f, vs, "bay", "frame"))
    for s, sx in (("L", 1), ("R", -1)):
        f = Field("Door" + s)
        c = v3((sx * BAY_HALF[0] / 2, BAY[1], BAY[2] + 0.02))
        f.add(RoundBox(c, (BAY_HALF[0] / 2, BAY_HALF[1] + 0.014, 0.024), 0.012))
        f.add(Cylinder(v3((sx * (BAY_HALF[0] + 0.006), BAY[1], BAY[2] + 0.02)), 0.028, BAY_HALF[1] * 2 + 0.02, rr=0.008, R=Y_AX), k=0.006)
        hazard(f, c - v3((BAY_HALF[0] / 2 - 0.015, BAY_HALF[1] - 0.015, 0.0)), c + v3((BAY_HALF[0] / 2 - 0.015, BAY_HALF[1] - 0.015, 0.06)),
               w=0.09, d=(1, 1, 0))
        out.append(("Door" + s, f, vs, "hatch." + s, "armor"))
    for i, lp in enumerate(LAMPS):
        f = Field("Lamp%d" % i)
        f.add(Sphere(lp, 0.028))
        out.append(("Lamp%d" % i, f, vs, "lamp.%d" % i, "glow"))
    # ---- the tail fins (canted, orange tips) and the engine nozzles
    f = Field("Fins")
    for sx in (-1, 1):
        pts, o, up = _fin_pts(sx)
        f.add(facet(pts, k=0.005))
        f.paint(Func(lambda P, o=o, up=up: F(0.33) - (P - o.astype(F)) @ up.astype(F), (-2, -1, 1.5), (2, 2, 3)), 1)
        f.paint(Func(lambda P, o=o, up=up: np.abs((P - o.astype(F)) @ up.astype(F) - F(0.3)) - F(0.006), (-2, -1, 1.5), (2, 2, 3)), 2)
    out.append(("Fins", f, vs, "root", "armor"))
    f = Field("Nozzles")
    for sx in (-1, 1):
        n = NOZ[sx]
        f.add(RoundBox(n, (0.12, 0.08, 0.08), 0.025), k=0.02)
        f.sub(RoundBox(n + v3((0, 0.07, 0)), (0.09, 0.08, 0.055), 0.015), k=0.008)
        f.paint(RoundBox(n + v3((0, -0.045, 0)), (0.15, 0.018, 0.1)), 1)
    out.append(("Nozzles", f, vs, "root", "frame"))
    for s, sx in (("L", 1), ("R", -1)):
        n = NOZ[sx]
        f = Field("Exhaust" + s)
        f.add(RoundBox(n + v3((0, 0.045, 0)), (0.088, 0.035, 0.052), 0.015))
        f.add(RoundCone(n + v3((0, 0.07, 0)), n + v3((0, 0.2, 0)), 0.05, 0.015), k=0.03)
        out.append(("Exhaust" + s, f, vs, "exhaust." + s, "glow"))
    # ---- per side: a stub wing, a missile pod on it, the ducted fan on its tilt shaft, a rotary cannon under the head
    for s, sx in (("L", 1), ("R", -1)):
        f = Field("Wing" + s)
        f.add(facet(_wing_pts(sx), k=0.008))
        f.paint(UNDER, 3)
        f.paint(Func(lambda P: np.abs(P[:, 0] * F(sx) - F(0.58)) - F(0.004), (-2, -1, 1.8), (2, 1, 2.2)), 2)
        out.append(("Wing" + s, f, vs, "root", "armor"))
        # the missile pod: an angular box, six tubes in its face, orange-tipped missile noses in them
        p = POD[sx]
        f = Field("Pod" + s)
        f.add(facet([tuple(p + v3((dx, dy, dz))) for dx in (-0.085, 0.085) for dy, dz in
                                       ((-0.22, 0.0), (-0.22, 0.13), (0.2, 0.0), (0.2, 0.12), (-0.26, 0.04), (-0.26, 0.11))], k=0.008))
        f.add(RoundBox(p + v3((0, 0.0, -0.025)), (0.06, 0.15, 0.04), 0.015), k=0.01)            # its pylon
        for i in range(3):
            for j in range(2):
                q = p + v3(((i - 1) * 0.052, -0.26, 0.04 + 0.055 * j + 0.012))
                f.sub(Cylinder(q, 0.022, 0.06, R=Y_AX), k=0.004)
                f.add(RoundCone(q + v3((0, 0.02, 0)), q + v3((0, -0.012, 0)), 0.017, 0.006), label=1)
        f.paint(RoundBox(p + v3((0, 0.12, 0.13)), (0.12, 0.03, 0.03)), 1)
        out.append(("Pod" + s, f, vs, "root", "frame"))
        # the ducted fan: the duct (white, orange rim, a hazard band round it), the tilt shaft and its collar
        fc = FAN[sx]
        f = Field("Duct" + s)
        f.add(Cylinder(fc, DUCT_O, DUCT_H, rr=0.04))
        f.sub(Cylinder(fc, DUCT_R, DUCT_H + 0.2), k=0.02)
        f.add(Torus(fc + v3((0, 0, DUCT_H / 2 - 0.01)), DUCT_R + 0.035, 0.035), k=0.02)          # the intake lip
        f.add(Cylinder(v3((sx * (PIVOT_X + 0.12), fc[1], fc[2])), 0.075, 0.24, rr=0.02, R=X_AX), k=0.03)   # the tilt shaft
        f.paint(Func(lambda P, fc=fc: P[:, 2] - F(fc[2] - DUCT_H / 2 + 0.03), fc - 0.6, fc + 0.6), 3)        # its underside
        f.paint(Torus(fc + v3((0, 0, DUCT_H / 2 - 0.0)), DUCT_R + 0.04, 0.03), 1)
        hazard(f, fc - v3((0.5, 0.5, 0.05)), fc + v3((0.5, 0.5, 0.0)), w=0.09, d=(0, 0, 1),
               band=lambda P, fc=fc: np.sqrt((P[:, 0] - F(fc[0])) ** 2 + (P[:, 1] - F(fc[1])) ** 2) - F(DUCT_O - 0.01))
        f.paint(Func(lambda P, fc=fc: np.maximum(np.abs(P[:, 2] - F(fc[2] + 0.06)) - F(0.004),
                                                 F(DUCT_O - 0.01) - np.sqrt((P[:, 0] - F(fc[0])) ** 2 + (P[:, 1] - F(fc[1])) ** 2)),
                     fc - 0.6, fc + 0.6), 2)
        out.append(("Duct" + s, f, vx, "fan." + s, "armor"))
        # the stators: four struts from the duct wall to the motor housing, a chrome hub cap
        f = Field("Stator" + s)
        f.add(Cylinder(fc + v3((0, 0, -0.04)), 0.1, 0.16, rr=0.03))
        for i in range(4):
            a = i * math.pi / 2 + math.pi / 4
            d = v3((math.cos(a), math.sin(a), 0))
            f.add(RoundBox(fc + d * (DUCT_R / 2 + 0.05) + v3((0, 0, -0.07)), (DUCT_R / 2, 0.018, 0.035), 0.01,
                           R=rot_from_axes(x_axis=d, z_axis=(0, 0, 1))), k=0.01)
        f.paint(Cylinder(fc + v3((0, 0, -0.04)), 0.11, 0.03), 1)
        out.append(("Stator" + s, f, vs, "fan." + s, "frame"))
        f = Field("Blades" + s)
        f.add(Cylinder(fc + v3((0, 0, 0.05)), 0.075, 0.06, rr=0.025))
        for i in range(5):
            a = i * 2 * math.pi / 5
            d = v3((math.cos(a), math.sin(a), 0))
            f.add(RoundBox(fc + d * 0.2 + v3((0, 0, 0.05)), (0.13, 0.04, 0.007), 0.007,
                           R=rot_from_axes(x_axis=d, z_axis=(0, 0, 1)) @ np.array(
                               [[1, 0, 0], [0, math.cos(0.4 * sx), -math.sin(0.4 * sx)], [0, math.sin(0.4 * sx), math.cos(0.4 * sx)]])), k=0.008)
        out.append(("Blades" + s, f, vs, "rotor." + s, "rubber"))
        # the rotary cannon: a ball mount under the head, a housing, six barrels round a spindle, clamps
        g = GUN[sx]
        f = Field("Mount" + s)
        f.add(Sphere(g + v3((0, 0.06, 0)), 0.1))
        f.add(RoundCone(g + v3((0, 0.08, 0.0)), g + v3((-sx * 0.05, 0.12, 0.15)), 0.06, 0.05), k=0.03)
        f.paint(Torus(g + v3((0, 0.06, 0)), 0.1, 0.02, R=Y_AX), 1)
        out.append(("Mount" + s, f, vs, "root", "frame"))
        f = Field("Gun" + s)
        f.add(Cylinder(g + v3((0, -0.06, 0)), 0.085, 0.14, rr=0.025, R=Y_AX))
        f.add(Cylinder(g + v3((0, -GUN_L / 2 - 0.02, 0)), 0.02, GUN_L - 0.04, R=Y_AX), k=0.004)
        for i in range(6):
            a = i * math.pi / 3
            o = v3((math.cos(a) * 0.05, 0, math.sin(a) * 0.05))
            f.add(Cylinder(g + o + v3((0, -GUN_L / 2 - 0.04, 0)), 0.019, GUN_L - 0.06, rr=0.005, R=Y_AX), k=0.003)
        for y in (-0.3, -GUN_L + 0.03):
            f.add(Cylinder(g + v3((0, y, 0)), 0.078, 0.03, rr=0.01, R=Y_AX), k=0.006)
        f.paint(Cylinder(g + v3((0, -0.3, 0)), 0.09, 0.034, R=Y_AX), 1)
        out.append(("Gun" + s, f, vs, "gun." + s, "frame"))
    return out


# ------------------------------------------------------------------------------------------------ clips
V = lambda *a: Vector(a)


def _spin(ang):
    return lambda P, base: ("rot", Quaternion(base.col[1].xyz.normalized(), ang))


def _tilt(sx, a):
    """The fan's tilt about its shaft (a > 0: the duct's top tips forward, toward -Y)."""
    return lambda P, base: ("rot", Quaternion(base.col[1].xyz.normalized(), sx * a))


def _door_aims(arm, ang):
    return {"hatch.L": rel(arm, "hatch.L", (-math.cos(ang), 0.0, math.sin(ang))),
            "hatch.R": rel(arm, "hatch.R", (math.cos(ang), 0.0, math.sin(ang)))}


def _eye(arm, look, dip=0.0):
    d0 = Vector(EYE_D)
    d = Quaternion(V(0, 0, 1), look) @ (Quaternion(V(1, 0, 0), -dip) @ d0)
    return rel(arm, "eye", d)


def fly(arm):
    P = Poser(arm)
    act = ra.new_action(arm, "Fly")
    for f in range(FLY_FRAMES + 1):
        t = f / FLY_FRAMES
        w = 2 * math.pi * t
        root_off = V(0.04 * math.sin(w + 0.7), 0.0, 0.07 * math.sin(w) + 0.02 * math.sin(3 * w))
        root_rot = Quaternion(V(0, 0, 1), 0.035 * math.sin(w + 1.4)) @ Quaternion(V(0, 1, 0), 0.05 * math.sin(w + 0.3)) @ \
            Quaternion(V(1, 0, 0), 0.06 + 0.025 * math.sin(w + 1.6))
        aims = {"eye": _eye(arm, 0.3 * math.sin(2 * w) + 0.08 * math.sin(6 * w), 0.05 * math.sin(4 * w))}
        for s, sx in (("L", 1), ("R", -1)):
            aims["fan." + s] = _tilt(sx, 0.2 + 0.05 * math.sin(w + (0.0 if sx > 0 else 1.2)))
            aims["rotor." + s] = _spin(sx * 2 * math.pi * 9 * t)
            aims["gun." + s] = _spin(sx * 2 * math.pi * 2 * t)
        sc = {}
        for i, s in enumerate(("L", "R")):
            p = 0.5 + 0.5 * math.sin(6 * w + i * 2.1)
            sc["exhaust." + s] = (1.0 + 0.06 * p, 1.0 + 0.35 * p, 1.0 + 0.06 * p)
        for i in range(4):
            sc["lamp.%d" % i] = 0.9 + 0.2 * (0.5 + 0.5 * math.sin(w * 3 + i * math.pi / 2))
        aims.update(_door_aims(arm, 0.0))
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, FLY_FRAMES, True)


def summon(arm):
    """It flares to a halt (nose up, fans tilted back, rising), the doors swing open, the launch lights blaze and the
    Stealth Jets launch at SUMMON_FRAME; the doors close and it noses down into its cruise again."""
    P = Poser(arm)
    act = ra.new_action(arm, "Summon")
    for f in range(SUMMON_FRAMES + 1):
        t = f / SUMMON_FRAMES
        w = 2 * math.pi * t
        k = smooth(0, 12, f) * (1.0 - smooth(28, 46, f))
        door = DOOR_OPEN * smooth(2, 12, f) * (1.0 - smooth(30, 42, f))
        kick = 0.0
        if f >= SUMMON_FRAME:
            u = f - SUMMON_FRAME
            kick = 0.05 * math.exp(-u * 0.35) * math.cos(u * 1.2)
        cruise = 1.0 - k
        root_off = V(0.0, 0.06 * k, 0.12 * k - kick + 0.03 * math.sin(w) * cruise)
        root_rot = Quaternion(V(1, 0, 0), 0.06 * cruise - 0.14 * k + kick * 0.6)
        lights = 1.0 + 0.7 * smooth(4, 12, f) * (1.0 - smooth(24, 34, f)) + 0.4 * math.exp(-abs(f - SUMMON_FRAME) * 0.4)
        aims = {"eye": _eye(arm, 0.0, -0.1 * k)}
        for s, sx in (("L", 1), ("R", -1)):
            aims["fan." + s] = _tilt(sx, 0.2 * cruise - 0.3 * k)
            aims["rotor." + s] = _spin(sx * 2 * math.pi * 7 * t)
            aims["gun." + s] = _spin(sx * 2 * math.pi * 1.33 * t)
        aims.update(_door_aims(arm, door))
        sc = {"eye": 1.0 + 0.12 * k}
        for i in range(4):
            sc["lamp.%d" % i] = lights
        for i, s in enumerate(("L", "R")):
            p = 0.5 + 0.5 * math.sin(6 * w + i * 2.1)
            sc["exhaust." + s] = (1.0 + 0.06 * p, 1.0 + 0.35 * p + 0.3 * k, 1.0 + 0.06 * p)
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, SUMMON_FRAMES, False)


def clips(arm):
    fly(arm)
    summon(arm)
