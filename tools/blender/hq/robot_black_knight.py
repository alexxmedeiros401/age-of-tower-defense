"""Black Knight Mech, HQ: the Medieval Age boss. A towering knight of black steel trimmed in gold: a barrel breastplate
with a glowing red cross-shaped core at its heart, a gold-edged gorget, a tall great helm (a sugarloaf crown banded in
gold, a narrow red visor slit across its face and a gold cross over it, breaths pierced below) under a crimson plume
sweeping back; great layered pauldrons with gold edges and short gold spikes; plated arms with fanned elbow cops; a
skirt of faulds and tassets over the thighs; fanned knee cops, greaves and broad sabatons. In its right fist a huge
greatsword (a gold cross guard and pommel, a red rune glowing down its fuller); on its left arm a black kite shield
with a gold border and a red robot skull.
Walk (a slow, heavy stomp, the sword held out low before it, the shield across its body) and Summon (it raises the
sword high overhead, its head thrown back and its core blazing, while Cloakers shimmer into being). Its energy shield
is game.gd's bubble. Faces -Y, Z up, model_scale 1.0.
"""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, rot_from_axes, v3, norm,
                 euler, F)
from caveman import Inter, Shell
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser

ROOT_NAME = "BlackKnight"
GLB_NAME = "black_knight"
TEX_PREFIX = "black_knight"
WALK_STEP = 0.6
WALK_FRAMES = 48

BLACK = (0.13, 0.13, 0.15)
GOLD = (0.92, 0.7, 0.26)
RED = (0.62, 0.07, 0.05)
SEAM = (0.05, 0.05, 0.06)


def mirror(p):
    return (-p[0], p[1], p[2])


J = {
    "hip_L": (0.36, 0.02, 1.32), "knee_L": (0.42, -0.1, 0.78), "ankle_L": (0.42, 0.06, 0.22), "toe_L": (0.42, -0.32, 0.08),
    "shoulder_L": (0.82, 0.04, 2.42), "elbow_L": (0.98, 0.12, 1.9), "wrist_L": (1.02, -0.08, 1.44), "hand_L": (1.02, -0.14, 1.16),
}
for k in list(J):
    if k.endswith("_L"):
        J[k[:-2] + "_R"] = mirror(J[k])

HEAD_C = v3((0, -0.04, 2.84))
CORE_C = v3((0, -0.43, 2.12))

BONES = [
    ("root", (0, 0, 1.32), (0, 0, 1.52), None),
    ("spine", (0, 0.02, 1.52), (0, 0.0, 2.55), "root"),
    ("head", (0, -0.04, 2.6), (0, -0.06, 3.0), "spine"),
    ("core", tuple(CORE_C), tuple(CORE_C + v3((0, -0.2, 0))), "spine"),
]
for s in ("L", "R"):
    BONES += [
        ("upperarm." + s, J["shoulder_" + s], J["elbow_" + s], "spine"),
        ("forearm." + s, J["elbow_" + s], J["wrist_" + s], "upperarm." + s),
        ("hand." + s, J["wrist_" + s], J["hand_" + s], "forearm." + s),
        ("thigh." + s, J["hip_" + s], J["knee_" + s], "root"),
        ("shin." + s, J["knee_" + s], J["ankle_" + s], "thigh." + s),
        ("foot." + s, J["ankle_" + s], J["toe_" + s], "shin." + s),
    ]

MATS = {
    "armor": ("armor", dict(name="RB_KnightArmor", base=BLACK, metal=(0.52, 0.54, 0.58), grime=(0.05, 0.05, 0.06),
                            labels=[(1, GOLD, 0.3), (2, SEAM, 0.6), (3, RED, 0.45)], seams=[2], wear=0.9, scale=2.0, rough=0.3)),
    "frame": ("gunmetal", dict(name="RB_KnightFrame", base=(0.16, 0.16, 0.18), labels=[(1, GOLD, 0.3), (2, (0.06, 0.06, 0.07), 0.6)],
                               seams=[2], scale=2.0)),
    "chrome": ("chrome", dict(name="RB_KnightBlade", base=(0.78, 0.8, 0.86))),
    "red": ("armor", dict(name="RB_KnightPlume", base=RED, metal=(0.72, 0.3, 0.24), grime=(0.2, 0.03, 0.02),
                          labels=[(1, GOLD, 0.3)], wear=0.25, rough=0.6, scale=2.0)),
    "glow": ("glow", dict(name="RB_KnightGlow", col=(1.0, 0.18, 0.1))),
}
GLOW = {"Visor": ((1.0, 0.2, 0.1), 1.6, 0.5), "Core": ((1.0, 0.22, 0.1), 1.6, 0.5), "Rune": ((1.0, 0.25, 0.12), 1.3, 0.6)}

LOW_TARGETS = {"Chest": 1400, "Core": 120, "Gorget": 300, "Faulds": 600, "Helm": 1000, "Visor": 40, "Plume": 500,
               "Sword": 700, "Rune": 60, "Shield": 900}
for s in "LR":
    LOW_TARGETS.update({"Pauldron" + s: 700, "UpperArm" + s: 200, "Elbow" + s: 220, "Forearm" + s: 300, "Gauntlet" + s: 400,
                        "Tasset" + s: 260, "Thigh" + s: 220, "Knee" + s: 240, "Greave" + s: 320, "Sabaton" + s: 300})

# the greatsword in the right fist (rest pose): its grip's middle, its axis (out from the fist), its flat's normal
SWORD_G = v3(J["wrist_R"]) + v3((0.0, -0.06, -0.2))
SWORD_AX = norm(v3((0.0, -1.0, -0.32)))
SWORD_FLAT = v3((1.0, 0.0, 0.0))
BLADE_L = 1.75
# the kite shield on the left forearm (rest pose): its centre, its face's normal (outward-forward), its up
SH_C = v3(J["elbow_L"]) + (v3(J["wrist_L"]) - v3(J["elbow_L"])) * 0.55 + v3((0.13, -0.06, 0.0))
SH_N = norm(v3((0.55, -0.83, 0.0)))
SH_UP = norm(v3((0.0, 0.0, 1.0)) - SH_N * 0.0)
SH_W, SH_H = 0.42, 0.72


def rivets(f, pts, r=0.016):
    for p in pts:
        f.add(Sphere(p, r), k=0.006)


def _kite_2d(u, v):
    """Kite shield outline, signed distance in the shield's plane (u across, v up; centre at 0): a rounded top
    narrowing to a point at the bottom."""
    top = v - F(SH_H * 0.55)
    w = F(SH_W) * np.clip((v + F(SH_H)) / F(SH_H * 1.25), 0, 1) ** F(0.75)
    side = np.abs(u) - w
    bottom = -(v + F(SH_H))
    return np.maximum(np.maximum(side, top), bottom)


def _skull_2d(u, v):
    """A robot skull (the device): a round dome, a squared jaw, two eye holes and a nose slot cut out of it."""
    dome = np.sqrt(u * u + (v - F(0.06)) ** 2) - F(0.15)
    jaw = np.maximum(np.abs(u) - F(0.1), np.abs(v + F(0.1)) - F(0.07))
    d = np.minimum(dome, jaw)
    eyes = np.minimum(np.sqrt((u - F(0.06)) ** 2 + (v - F(0.04)) ** 2), np.sqrt((u + F(0.06)) ** 2 + (v - F(0.04)) ** 2)) - F(0.042)
    nose = np.maximum(np.abs(u) - F(0.014), np.abs(v + F(0.04)) - F(0.025))
    teeth = np.where(v < F(-0.1), np.abs(np.mod(u + F(0.02), F(0.04)) - F(0.02)) - F(0.006), F(1.0))
    return np.maximum(d, -np.minimum(np.minimum(eyes, nose), teeth))


def parts(fine=False):
    vx = 0.008 if fine else 0.014
    vs = 0.005 if fine else 0.009
    out = []
    # ---- the breastplate: a barrel chest, a ridge down its middle, the plackart over its belly, a backplate
    f = Field("Chest")
    f.add(Ellipsoid((0, 0.0, 2.12), (0.6, 0.42, 0.5)))
    f.add(Ellipsoid((0, 0.04, 1.68), (0.42, 0.32, 0.28)), k=0.12)
    f.add(RoundBox((0, -0.36, 2.06), (0.05, 0.06, 0.38), 0.04, R=euler(-0.08, 0, 0)), k=0.06)            # the ridge
    f.sub(RoundBox(CORE_C + v3((0, -0.04, 0)), (0.13, 0.08, 0.13), 0.02), k=0.02)                    # the core's recess
    pts = []
    for a in np.linspace(-1.1, 1.1, 9):
        pts.append(v3((math.sin(a) * 0.5, -math.cos(a) * 0.36, 1.86)))
    rivets(f, pts, 0.016)
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(1.86)) - F(0.03), (-0.8, -0.6, 1.3), (0.8, 0.6, 2.7)), 1)       # gold band
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(1.55)) - F(0.004), (-0.8, -0.6, 1.3), (0.8, 0.6, 2.7)), 2)
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 0]) - F(0.05), P[:, 1] + F(0.3)), (-0.8, -0.6, 1.3), (0.8, 0.6, 2.7)), 1)  # gold ridge
    out.append(("Chest", f, vx, "spine", "armor"))
    f = Field("Core")                                        # the red cross-shaped core behind its grille
    f.add(RoundBox(CORE_C + v3((0, -0.04, 0)), (0.035, 0.03, 0.11), 0.012))
    f.add(RoundBox(CORE_C + v3((0, -0.04, 0.03)), (0.1, 0.03, 0.032), 0.012), k=0.006)
    out.append(("Core", f, vs, "core", "glow"))
    f = Field("Gorget")
    f.add(Torus((0, -0.02, 2.56), 0.27, 0.07, R=euler(0.12, 0, 0)))
    f.add(Torus((0, -0.02, 2.63), 0.24, 0.05, R=euler(0.12, 0, 0)), k=0.02)
    f.paint(Torus((0, -0.02, 2.66), 0.24, 0.06, R=euler(0.12, 0, 0)), 1)
    out.append(("Gorget", f, vx, "spine", "armor"))
    # ---- faulds: three bands round its waist, gold-edged
    f = Field("Faulds")
    for i, (z, r) in enumerate(((1.5, 0.46), (1.42, 0.49), (1.34, 0.52))):
        f.add(Inter(Shell(Ellipsoid((0, 0.03, z), (r, r * 0.78, 0.12)), 0.0, 0.03),
                    Func(lambda P, z=z: np.abs(P[:, 2] - F(z)) - F(0.05), (-0.7, -0.6, z - 0.2), (0.7, 0.6, z + 0.2)), 0.008), k=0.006)
        f.paint(Func(lambda P, z=z: np.abs(P[:, 2] - F(z - 0.04)) - F(0.012), (-0.7, -0.6, z - 0.2), (0.7, 0.6, z + 0.2)), 1)
    out.append(("Faulds", f, vx, "root", "armor"))
    # ---- the great helm: a sugarloaf crown, the visor slit, a gold cross over the face, breaths; the plume
    f = Field("Helm")
    hc = HEAD_C
    f.add(RoundCone(hc + v3((0, 0, -0.18)), hc + v3((0, 0, 0.12)), 0.25, 0.24))
    f.add(Ellipsoid(hc + v3((0, 0.0, 0.14)), (0.24, 0.24, 0.16)), k=0.04)
    f.add(RoundBox(hc + v3((0, -0.21, -0.02)), (0.02, 0.06, 0.2), 0.015), k=0.02)                   # the face's keel
    f.sub(RoundBox(hc + v3((0, -0.26, 0.04)), (0.17, 0.06, 0.018), 0.01), k=0.006)                  # the visor slit
    for i in range(3):
        for sx in (-1, 1):
            f.sub(RoundBox(hc + v3((sx * (0.07 + 0.05 * i), -0.25, -0.1)), (0.008, 0.05, 0.03), 0.005), k=0.003)   # breaths
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(hc[2] + 0.13)) - F(0.025), hc - 0.5, hc + 0.5), 1)    # the crown's gold band
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 0]) - F(0.03), P[:, 1] - F(hc[1] - 0.15)), hc - 0.5, hc + 0.5), 1)  # cross: upright
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(hc[2] + 0.075)) - F(0.025), np.maximum(P[:, 1] - F(hc[1] - 0.15), np.abs(P[:, 0]) - F(0.19))),
                 hc - 0.5, hc + 0.5), 1)                                                            # cross: its arm over the slit
    out.append(("Helm", f, vx, "head", "armor"))
    f = Field("Visor")
    f.add(RoundBox(hc + v3((0, -0.235, 0.04)), (0.165, 0.012, 0.014), 0.008))
    out.append(("Visor", f, vs, "head", "glow"))
    f = Field("Plume")                                      # a crimson plume from a gold socket on the crown, sweeping back
    sock = hc + v3((0, 0.02, 0.29))
    f.add(Cylinder(sock, 0.05, 0.05, rr=0.012))
    pts = [sock + v3((0, 0.0, 0.03)), sock + v3((0, 0.12, 0.12)), sock + v3((0, 0.32, 0.1)), sock + v3((0, 0.48, -0.04)), sock + v3((0, 0.56, -0.2))]
    rads = [0.06, 0.09, 0.1, 0.08, 0.04]
    for i in range(len(pts) - 1):
        f.add(RoundCone(pts[i], pts[i + 1], rads[i], rads[i + 1], disp=lambda P: F(0.008) * np.sin(P[:, 0] * F(90)), disp_amp=0.008), k=0.03)
    f.paint(Cylinder(sock, 0.07, 0.07), 1)
    out.append(("Plume", f, vx, "head", "red"))
    # ---- the greatsword in its right fist
    g0, ax, fl = SWORD_G, SWORD_AX, SWORD_FLAT
    edge = norm(np.cross(ax, fl))
    f = Field("Sword")
    f.add(RoundCone(g0 - ax * 0.24, g0 + ax * 0.12, 0.045, 0.045))                               # the grip
    f.add(Sphere(g0 - ax * 0.28, 0.07), k=0.01)                                                   # the pommel
    f.add(RoundCone(g0 + ax * 0.15 - fl * 0.34, g0 + ax * 0.15 + fl * 0.34, 0.035, 0.035), k=0.02)  # the cross guard
    for s in (-1, 1):
        f.add(Sphere(g0 + ax * 0.15 + fl * (s * 0.36), 0.05), k=0.01)
    b0 = g0 + ax * 0.2
    R = rot_from_axes(z_axis=ax, x_axis=fl)
    def blade(P):
        q = P - b0.astype(F)
        u = q @ ax.astype(F)
        x = q @ fl.astype(F)
        y = q @ edge.astype(F)
        t = np.clip(u / F(BLADE_L), 0, 1)
        hw = F(0.085) * (F(1.0) - t ** F(3.0)) + F(0.004)
        th = F(0.03) * (F(1.0) - F(0.8) * np.abs(x) / F(0.09))
        return np.maximum(np.maximum(np.abs(x) - hw, np.abs(y) - th), np.maximum(-u, u - F(BLADE_L)))
    f.add(Func(blade, np.minimum(b0, b0 + ax * BLADE_L) - 0.15, np.maximum(b0, b0 + ax * BLADE_L) + 0.15), k=0.006)
    f.paint(Func(lambda P: np.maximum(np.abs((P - g0.astype(F)) @ ax.astype(F) + F(0.06)) - F(0.2), F(0.0)) - F(0.06) + F(0.0) * P[:, 0],
                 g0 - 0.5, g0 + 0.5), 1)                                                          # (gold hilt)
    out.append(("Sword", f, vs, "hand.R", "chrome"))
    f = Field("Rune")
    f.add(RoundCone(b0 + ax * 0.12 - edge * 0.032, b0 + ax * (BLADE_L * 0.72) - edge * 0.032, 0.012, 0.006))
    f.add(RoundCone(b0 + ax * 0.12 + edge * 0.032, b0 + ax * (BLADE_L * 0.72) + edge * 0.032, 0.012, 0.006))
    out.append(("Rune", f, vs, "hand.R", "glow"))
    # ---- the kite shield on its left forearm
    n, up = SH_N, norm(SH_UP - SH_N * float(SH_UP @ SH_N))
    acr = norm(np.cross(up, n))
    c = SH_C + n * 0.08
    def shield(P):
        q = P - c.astype(F)
        u = q @ acr.astype(F)
        v = q @ up.astype(F)
        w = q @ n.astype(F) + F(0.12) * (u / F(SH_W)) ** 2                          # a curved face
        return np.maximum(_kite_2d(u, v), np.abs(w) - F(0.03))
    lo, hi = c - 0.55, c + 0.55
    f = Field("Shield")
    f.add(Func(shield, lo, hi), k=0.0)
    def border(P):
        q = P - c.astype(F)
        u = q @ acr.astype(F)
        v = q @ up.astype(F)
        return np.abs(_kite_2d(u, v) + F(0.035)) - F(0.03)
    f.paint(Func(border, lo, hi), 1)
    def skull(P):
        q = P - c.astype(F)
        u = q @ acr.astype(F)
        v = q @ up.astype(F)
        return np.maximum(_skull_2d(u * F(0.95), v - F(0.1)), -(q @ n.astype(F) + F(0.12) * (u / F(SH_W)) ** 2))
    f.paint(Func(skull, lo, hi), 3)
    out.append(("Shield", f, vs, "forearm.L", "armor"))

    for s, sx in (("L", 1), ("R", -1)):
        sh, el, wr, hd = (v3(J[k + "_" + s]) for k in ("shoulder", "elbow", "wrist", "hand"))
        f = Field("Pauldron" + s)                           # three lames, gold-edged, short gold spikes
        for i in range(3):
            pc = sh + v3((sx * (0.04 + 0.03 * i), 0.0, 0.14 - 0.11 * i))
            f.add(Inter(Shell(Ellipsoid(pc, (0.32 - 0.02 * i, 0.3, 0.2)), 0.0, 0.04),
                        Func(lambda P, pc=pc: F(pc[2] - 0.06) - P[:, 2], pc - 0.6, pc + 0.6), 0.01), k=0.008)
            f.paint(Func(lambda P, pc=pc: np.abs(P[:, 2] - F(pc[2] - 0.055)) - F(0.018), pc - 0.6, pc + 0.6), 1)
        top = sh + v3((sx * 0.06, 0.0, 0.3))
        for a in (-0.5, 0.0, 0.5):
            base = top + v3((sx * 0.08 * math.cos(a), 0.18 * math.sin(a), -0.04))
            f.add(RoundCone(base, base + v3((sx * 0.06, 0.02 * math.sin(a), 0.16)), 0.035, 0.006), k=0.012)
            f.paint(Sphere(base + v3((sx * 0.04, 0, 0.1)), 0.09), 1)
        out.append(("Pauldron" + s, f, vx, "upperarm." + s, "armor"))
        f = Field("UpperArm" + s)
        f.add(RoundCone(sh, el, 0.13, 0.11))
        f.paint(RoundBox(sh + (el - sh) * 0.6, (0.3, 0.3, 0.008)), 2)
        out.append(("UpperArm" + s, f, vx, "upperarm." + s, "frame"))
        f = Field("Elbow" + s)                              # the couter, its fan on the outside
        f.add(Sphere(el, 0.13))
        f.add(Ellipsoid(el + v3((sx * 0.1, 0.04, 0.0)), (0.04, 0.16, 0.16)), k=0.03)
        f.paint(Ellipsoid(el + v3((sx * 0.13, 0.04, 0.0)), (0.04, 0.19, 0.19)), 1)
        out.append(("Elbow" + s, f, vx, "forearm." + s, "armor"))
        f = Field("Forearm" + s)
        f.add(RoundCone(el + (wr - el) * 0.15, wr, 0.12, 0.13))
        f.add(Ellipsoid(el + (wr - el) * 0.55, (0.15, 0.15, 0.2)), k=0.05)
        f.paint(RoundBox(wr + (el - wr) * 0.06, (0.3, 0.3, 0.03)), 1)
        out.append(("Forearm" + s, f, vx, "forearm." + s, "armor"))
        f = Field("Gauntlet" + s)                           # a plated fist (round the sword's grip on the right)
        f.add(RoundBox(wr + v3((0, -0.03, -0.12)), (0.11, 0.1, 0.1), 0.05))
        for i in range(4):
            f.add(RoundBox(wr + v3((sx * (0.06 - 0.04 * i), -0.11, -0.2)), (0.022, 0.05, 0.05), 0.02), k=0.02)
        f.add(Ellipsoid(wr + v3((0, -0.02, -0.02)), (0.15, 0.14, 0.08)), k=0.03)              # the cuff
        f.paint(Ellipsoid(wr + v3((0, -0.02, -0.02)), (0.17, 0.16, 0.05)), 1)
        out.append(("Gauntlet" + s, f, vx, "hand." + s, "armor"))
        hp, kn, an, to = (v3(J[k + "_" + s]) for k in ("hip", "knee", "ankle", "toe"))
        f = Field("Tasset" + s)                             # plates hanging over the front of the thigh
        for i in range(3):
            c0 = hp + (kn - hp) * (0.08 + 0.17 * i) + v3((sx * 0.02, -0.16, 0.0))
            f.add(RoundBox(c0, (0.17, 0.035, 0.08), 0.03, R=euler(-0.25, 0, sx * 0.1)), k=0.01)
            f.paint(RoundBox(c0 + v3((0, 0, -0.07)), (0.2, 0.06, 0.012), R=euler(-0.25, 0, sx * 0.1)), 1)
        out.append(("Tasset" + s, f, vx, "thigh." + s, "armor"))
        f = Field("Thigh" + s)
        f.add(RoundCone(hp, kn, 0.17, 0.14))
        out.append(("Thigh" + s, f, vx, "thigh." + s, "frame"))
        f = Field("Knee" + s)                               # the poleyn, its fan on the outside
        f.add(Ellipsoid(kn + v3((0, -0.1, 0.02)), (0.15, 0.09, 0.14)))
        f.add(Ellipsoid(kn + v3((sx * 0.12, -0.04, 0.02)), (0.035, 0.12, 0.13)), k=0.03)
        rivets(f, [kn + v3((dx, -0.19, 0.03)) for dx in (-0.06, 0.06)], 0.016)
        f.paint(Ellipsoid(kn + v3((sx * 0.14, -0.04, 0.02)), (0.03, 0.15, 0.16)), 1)
        out.append(("Knee" + s, f, vx, "shin." + s, "armor"))
        f = Field("Greave" + s)
        f.add(RoundCone(kn + (an - kn) * 0.12, an + (kn - an) * 0.08, 0.16, 0.13))
        f.add(Ellipsoid(kn + (an - kn) * 0.42 + v3((0, -0.03, 0)), (0.17, 0.16, 0.2)), k=0.06)
        f.add(RoundBox(kn + (an - kn) * 0.45 + v3((0, -0.15, 0)), (0.02, 0.04, 0.22), 0.015), k=0.03)     # its ridge
        f.paint(RoundBox(an + (kn - an) * 0.1, (0.3, 0.3, 0.02)), 1)
        out.append(("Greave" + s, f, vx, "shin." + s, "armor"))
        f = Field("Sabaton" + s)
        f.add(RoundBox(an + v3((0, -0.1, -0.12)), (0.17, 0.25, 0.08), 0.06))
        for i in range(3):
            f.add(RoundBox(an + v3((0, -0.14 - 0.08 * i, -0.08 + 0.01 * i)), (0.16, 0.05, 0.075), 0.04), k=0.015)
            f.paint(RoundBox(an + v3((0, -0.1 - 0.08 * i, -0.06)), (0.3, 0.008, 0.2)), 2)
        f.add(Sphere(an, 0.13), k=0.04)
        f.paint(RoundBox(an + v3((0, -0.1, -0.2)), (0.3, 0.4, 0.02)), 2)
        out.append(("Sabaton" + s, f, vx, "foot." + s, "armor"))
    return out


# ---------------------------------------------------------------------------------------------------------- clips
SWORD_HOLD = {"upperarm.R": Vector((-0.2, -0.32, -1.0)), "forearm.R": Vector((-0.04, -0.9, -0.42)), "hand.R": Vector((0.0, -0.95, -0.3))}
SHIELD_HOLD = {"upperarm.L": Vector((0.3, -0.25, -1.0)), "forearm.L": Vector((-0.35, -0.9, 0.1)), "hand.L": Vector((-0.35, -0.9, 0.0))}


def _legs(arm, t, step=WALK_STEP):
    """Both feet planted (a stance), a little apart, the knees soft."""
    aims = {}
    for side in ("L", "R"):
        a0 = Vector(J["ankle_" + side]) + Vector((0, 0.05 if side == "R" else -0.05, 0))
        aims.update(ra.leg(arm, side, a0, Vector((0, -1, 0)), Vector((0, -1, 0.05))))
    return aims


def summon(arm, frames=WALK_FRAMES):
    """It raises the greatsword high overhead (point to the sky), its head thrown back, the shield out to its side, its
    core blazing; holds; and brings the sword back down before it."""
    P = Poser(arm)
    act = ra.new_action(arm, "Summon")
    for f in range(frames + 1):
        t = f / frames
        k = math.sin(math.pi * min(1.0, t / 0.9)) ** 0.6
        aims = _legs(arm, t)
        aims["spine"] = (Vector((0, 0.16 * k, 1.0)), 0.0)
        aims["head"] = Vector((0, -0.25 + 0.75 * k, 1.0))
        up_r = SWORD_HOLD["upperarm.R"].lerp(Vector((-0.25, -0.15, 1.0)), k).normalized()
        fo_r = SWORD_HOLD["forearm.R"].lerp(Vector((0.05, 0.0, 1.0)), k).normalized()
        aims["upperarm.R"] = up_r
        aims["forearm.R"] = fo_r
        aims["hand.R"] = SWORD_HOLD["hand.R"].lerp(Vector((0.0, 0.25, 1.0)), k).normalized()
        aims["upperarm.L"] = SHIELD_HOLD["upperarm.L"].lerp(Vector((0.9, -0.2, -0.35)), k).normalized()
        aims["forearm.L"] = SHIELD_HOLD["forearm.L"].lerp(Vector((0.6, -0.6, 0.1)), k).normalized()
        aims["hand.L"] = SHIELD_HOLD["hand.L"].lerp(Vector((0.6, -0.6, 0.0)), k).normalized()
        aims["core"] = Vector((0, -1, 0))
        c = math.cos(4 * math.pi * t)
        ch, _ = P.solve(aims, root_off=Vector((0, 0, -0.04 * c + 0.04)), root_rot=Quaternion(Vector((1, 0, 0)), -0.03),
                        scales={"core": 1.0 + 0.45 * k})
        P.key(ch, f)
    ra.finish_action(arm, act, frames, False)


def clips(arm):
    def extra(t, aims):
        aims.update({k: v.normalized() for k, v in SWORD_HOLD.items()})
        sw = 0.04 * math.sin(2 * math.pi * t)
        aims["upperarm.L"] = (SHIELD_HOLD["upperarm.L"] + Vector((0, sw, 0))).normalized()
        aims["forearm.L"] = SHIELD_HOLD["forearm.L"].normalized()
        aims["hand.L"] = SHIELD_HOLD["hand.L"].normalized()
        aims["core"] = Vector((0, -1, 0))
    ra.walk(arm, J, "Walk", frames=WALK_FRAMES, step=WALK_STEP, lift=0.12, bob=0.05, sway=0.06, arm_swing=0.12, lean=0.06,
            twist=0.1, heavy=1.6, extra=extra)
    summon(arm)
