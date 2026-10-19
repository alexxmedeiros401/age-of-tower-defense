"""Walker, HQ: the Stone Age's foot soldier. A stocky white-armoured biped: a domed helmet with a red visor slit and an
antenna, a barrel chest with a glowing red core in a ringed socket, orange-striped shoulder pads, a power pack with two
exhaust stacks on its back, gunmetal joints, armoured gauntlets and shins, chunky boots and three-clawed hands.
Rigid parts, each on one bone; faces -Y, Z up, 1.0 model unit ~ 0.9 world units in game (model_scale 0.9).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3
import robot_anim as ra
from mathutils import Vector

ROOT_NAME = "Walker"
GLB_NAME = "walker"
TEX_PREFIX = "walker"
WALK_STEP = 0.48           # one stride, model units: enemies.json walk_speed = 2 * WALK_STEP * model_scale per second

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)


def mirror(p):
    return (-p[0], p[1], p[2])


J = {
    "hip_L": (0.12, 0.01, 0.6), "knee_L": (0.14, -0.04, 0.35), "ankle_L": (0.14, 0.02, 0.1), "toe_L": (0.14, -0.13, 0.05),
    "shoulder_L": (0.29, 0.0, 0.97), "elbow_L": (0.35, 0.03, 0.76), "wrist_L": (0.37, -0.02, 0.57), "hand_L": (0.37, -0.05, 0.46),
    "ant_base": (0.075, 0.035, 1.345), "ant_tip": (0.105, 0.065, 1.57),
}
for k in list(J):
    if k.endswith("_L"):
        J[k[:-2] + "_R"] = mirror(J[k])

BONES = [
    ("root", (0, 0, 0.6), (0, 0, 0.7), None),
    ("spine", (0, 0, 0.7), (0, 0, 1.05), "root"),
    ("head", (0, 0, 1.06), (0, 0, 1.32), "spine"),
    ("antenna", J["ant_base"], J["ant_tip"], "head"),
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
    "armor": ("armor", dict(name="RB_WalkerArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, (0.12, 0.12, 0.13), 0.5)], seams=[2])),
    "frame": ("gunmetal", dict(name="RB_WalkerFrame", labels=[(1, ORANGE, 0.35), (2, (0.1, 0.1, 0.11), 0.6)], seams=[2])),
    "chrome": ("chrome", dict(name="RB_WalkerChrome")),
    "socket": ("lens_socket", dict(name="RB_WalkerSocket")),
    "glow": ("glow", dict(name="RB_WalkerGlow", col=(1.0, 0.25, 0.1))),
}
GLOW_RED = (1.0, 0.22, 0.08)
GLOW = {"Core": (GLOW_RED, 1.2, 0.5), "Visor": (GLOW_RED, 1.3, 0.5), "AntennaTip": (GLOW_RED, 1.2, 0.5)}

LOW_TARGETS = {
    "Abdomen": 150, "Torso": 520, "Back": 200, "Pelvis": 150, "Neck": 40, "CoreRing": 70, "Head": 380, "Ears": 70, "Antenna": 50,
    "Core": 70, "Visor": 50, "AntennaTip": 30,
}
for s in "LR":
    LOW_TARGETS.update({"Shoulder" + s: 130, "UpperArm" + s: 80, "Forearm" + s: 130, "Hand" + s: 140, "Thigh" + s: 90,
                        "Knee" + s: 50, "Shin" + s: 150, "Foot" + s: 150})

FACE_Y = rot_from_axes(z_axis=(0, -1, 0))       # local Z pointing forward (-Y)


def seam_ring_z(f, z, w=0.004, lab=2):
    f.paint(RoundBox((0, 0, z), (0.5, 0.5, w)), lab)


def parts(fine=False):
    vx = 0.0045 if fine else 0.008
    vs = 0.0035 if fine else 0.007
    out = []

    # ---- torso: barrel chest tapering to the waist, core socket in front, an orange band over the top
    f = Field("Torso")
    f.add(RoundBox((0, 0.01, 0.91), (0.2, 0.145, 0.13), 0.08))
    f.add(Ellipsoid((0, -0.01, 0.96), (0.225, 0.165, 0.115)), k=0.04)
    f.sub(Sphere((0, -0.175, 0.9), 0.085), k=0.012)                        # core socket
    f.sub(RoundBox((0, 0.18, 0.92), (0.15, 0.06, 0.11), 0.03), k=0.01)     # seat for the power pack
    f.paint(RoundBox((0, -0.02, 1.02), (0.3, 0.3, 0.025)), 1)              # orange band across the shoulders
    seam_ring_z(f, 0.79)
    f.paint(RoundBox((0, -0.2, 0.86), (0.004, 0.05, 0.2)), 2)              # centre seam under the core
    for sx in (-1, 1):
        f.paint(RoundBox((sx * 0.13, -0.13, 0.82), (0.03, 0.06, 0.018), 0.01), 3)   # vents low on the chest
    out.append(("Torso", f, vx, "spine", "armor"))
    f = Field("Abdomen")                                                    # segmented waist, gunmetal rings
    for i, (z, r) in enumerate(((0.715, 0.12), (0.755, 0.13), (0.795, 0.14))):
        f.add(Cylinder((0, 0.01, z), r, 0.034, rr=0.012), k=0.004)
    out.append(("Abdomen", f, vx, "spine", "frame"))

    f = Field("CoreRing")
    f.add(Torus((0, -0.158, 0.9), 0.082, 0.017, R=FACE_Y))
    for i in range(6):
        a = i * math.pi / 3
        f.add(Sphere((0.1 * math.cos(a), -0.15, 0.9 + 0.1 * math.sin(a)), 0.012), k=0.004)
    out.append(("CoreRing", f, vs, "spine", "frame"))
    f = Field("Core")
    f.add(Ellipsoid((0, -0.155, 0.9), (0.068, 0.04, 0.068)))
    out.append(("Core", f, vs, "spine", "glow"))

    # ---- power pack and exhaust stacks on the back
    f = Field("Back")
    f.add(RoundBox((0, 0.18, 0.92), (0.135, 0.06, 0.11), 0.035))
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.075, 0.215, 1.03), 0.032, 0.18, rr=0.008), k=0.01)
        f.sub(Cylinder((sx * 0.075, 0.215, 1.12), 0.021, 0.06), k=0.004)
    for i in range(4):
        f.paint(RoundBox((0, 0.245, 0.86 + i * 0.03), (0.09, 0.01, 0.006), 0.004), 2)   # cooling fins
    out.append(("Back", f, vx, "spine", "frame"))

    # ---- pelvis with ball hips
    f = Field("Pelvis")
    f.add(RoundBox((0, 0.01, 0.645), (0.15, 0.1, 0.055), 0.04))
    for sx in (-1, 1):
        f.add(Sphere((sx * 0.12, 0.01, 0.6), 0.06), k=0.015)
    seam_ring_z(f, 0.645, 0.003)
    out.append(("Pelvis", f, vx, "root", "frame"))
    f = Field("Neck")
    f.add(Cylinder((0, 0.0, 1.06), 0.052, 0.08, rr=0.01))
    for i in range(2):
        f.paint(RoundBox((0, 0, 1.045 + i * 0.03), (0.2, 0.2, 0.004)), 2)
    out.append(("Neck", f, vs, "spine", "frame"))

    # ---- head: domed helmet, jaw guard, visor slot, ear discs, antenna
    f = Field("Head")
    f.add(Ellipsoid((0, 0.005, 1.215), (0.168, 0.158, 0.148)))
    f.add(RoundBox((0, -0.03, 1.13), (0.128, 0.112, 0.05), 0.045), k=0.035)
    f.sub(RoundBox((0, -0.168, 1.215), (0.118, 0.055, 0.034), 0.025), k=0.008)    # visor slot
    f.paint(RoundBox((0, 0.0, 1.345), (0.034, 0.22, 0.07), 0.01), 1)             # orange crest stripe
    for z in (1.105, 1.122, 1.139):
        f.paint(RoundBox((0, -0.15, z), (0.065, 0.03, 0.0045)), 3)                # mouth grille lines
    out.append(("Head", f, vx, "head", "armor"))
    f = Field("Visor")
    f.add(RoundBox((0, -0.142, 1.215), (0.112, 0.026, 0.028), 0.02))
    out.append(("Visor", f, vs, "head", "glow"))
    f = Field("Ears")
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.168, 0.0, 1.205), 0.056, 0.048, rr=0.013, R=rot_from_axes(z_axis=(1, 0, 0))))
        f.add(Cylinder((sx * 0.192, 0.0, 1.205), 0.03, 0.03, rr=0.008, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.006)
        f.paint(Cylinder((sx * 0.17, 0.0, 1.205), 0.062, 0.03, R=rot_from_axes(z_axis=(1, 0, 0))), 1)
    out.append(("Ears", f, vs, "head", "frame"))
    f = Field("Antenna")
    f.add(Cylinder(J["ant_base"], 0.03, 0.025, rr=0.008))
    f.add(RoundCone(J["ant_base"], J["ant_tip"], 0.012, 0.008), k=0.006)
    out.append(("Antenna", f, vs, "antenna", "frame"))
    f = Field("AntennaTip")
    f.add(Sphere(J["ant_tip"], 0.026))
    out.append(("AntennaTip", f, vs, "antenna", "glow"))

    for s, sx in (("L", 1), ("R", -1)):
        sh, el, wr, hd = (v3(J[k + "_" + s]) for k in ("shoulder", "elbow", "wrist", "hand"))
        # shoulder pad: a rounded dome with an orange stripe
        f = Field("Shoulder" + s)
        f.add(Ellipsoid(sh + v3((sx * 0.03, 0, 0.03)), (0.125, 0.125, 0.09)))
        f.add(Torus(sh + v3((sx * 0.03, 0, -0.005)), 0.112, 0.016), k=0.01)
        f.sub(Ellipsoid(sh + v3((sx * 0.025, 0, -0.05)), (0.09, 0.09, 0.065)), k=0.01)
        f.paint(RoundBox(sh + v3((sx * 0.03, 0, 0.11)), (0.2, 0.03, 0.07)), 1)
        out.append(("Shoulder" + s, f, vx, "upperarm." + s, "armor"))
        f = Field("UpperArm" + s)
        f.add(RoundCone(sh, el, 0.042, 0.038))
        f.add(Sphere(el, 0.048), k=0.01)
        for i in range(3):
            f.paint(RoundBox(sh + (el - sh) * (0.35 + 0.15 * i), (0.08, 0.08, 0.004)), 2)
        out.append(("UpperArm" + s, f, vs, "upperarm." + s, "frame"))
        # gauntlet: a chunky armoured forearm, flat plate on the outside
        f = Field("Forearm" + s)
        f.add(RoundCone(el + (wr - el) * 0.12, wr, 0.06, 0.052))
        f.add(RoundBox(el + (wr - el) * 0.55 + v3((sx * 0.04, 0, 0)), (0.025, 0.05, 0.085), 0.018,
                       R=rot_from_axes(y_axis=(0, 1, 0), x_axis=(1, 0, 0))), k=0.02)
        f.paint(RoundBox(el + (wr - el) * 0.62, (0.2, 0.2, 0.004)), 2)
        out.append(("Forearm" + s, f, vx, "forearm." + s, "armor"))
        # hand: palm and three claws
        f = Field("Hand" + s)
        f.add(RoundBox(wr + v3((0, -0.01, -0.045)), (0.048, 0.04, 0.04), 0.02))
        for i, dx in enumerate((-0.032, 0.0, 0.032)):
            base = wr + v3((dx, -0.035, -0.075))
            tip = base + v3((dx * 0.3, -0.045, -0.07))
            f.add(RoundCone(base, tip, 0.017, 0.008), k=0.006)
        thumb = wr + v3((-sx * 0.048, -0.035, -0.04))
        f.add(RoundCone(thumb, thumb + v3((-sx * 0.022, -0.05, -0.04)), 0.016, 0.008), k=0.006)
        out.append(("Hand" + s, f, vs, "hand." + s, "frame"))
        hp, kn, an, to = (v3(J[k + "_" + s]) for k in ("hip", "knee", "ankle", "toe"))
        f = Field("Thigh" + s)
        f.add(RoundCone(hp, kn, 0.052, 0.045))
        f.add(RoundBox(hp + (kn - hp) * 0.5 + v3((0, -0.04, 0)), (0.055, 0.02, 0.08), 0.015,
                       R=rot_from_axes(y_axis=(0, -1, 0), z_axis=(kn - hp))), k=0.015)
        for i in range(2):
            f.paint(RoundBox(hp + (kn - hp) * (0.25 + 0.5 * i), (0.1, 0.1, 0.004)), 2)
        out.append(("Thigh" + s, f, vx, "thigh." + s, "frame"))
        f = Field("Knee" + s)
        f.add(Ellipsoid(kn + v3((0, -0.035, 0.005)), (0.05, 0.035, 0.05)))
        out.append(("Knee" + s, f, vs, "shin." + s, "chrome"))
        # shin guard: armoured, wider at the calf, a seam and an orange band at the top
        f = Field("Shin" + s)
        f.add(RoundCone(kn + (an - kn) * 0.12, an + (kn - an) * 0.1, 0.068, 0.054))
        f.add(Ellipsoid(kn + (an - kn) * 0.45 + v3((0, 0.012, 0)), (0.07, 0.07, 0.1)), k=0.03)
        f.paint(RoundBox(kn + (an - kn) * 0.18, (0.2, 0.2, 0.018)), 1)
        f.paint(RoundBox(kn + (an - kn) * 0.6, (0.2, 0.2, 0.004)), 2)
        out.append(("Shin" + s, f, vx, "shin." + s, "armor"))
        # boot: chunky sole, toe cap, ankle ball
        f = Field("Foot" + s)
        f.add(RoundBox(an + v3((0, -0.06, -0.06)), (0.082, 0.135, 0.045), 0.032))
        f.add(Ellipsoid(an + v3((0, -0.135, -0.05)), (0.08, 0.075, 0.05)), k=0.02)
        f.add(Sphere(an, 0.05), k=0.02)
        f.paint(RoundBox(an + v3((0, -0.055, -0.098)), (0.1, 0.2, 0.012)), 2)    # sole line
        out.append(("Foot" + s, f, vx, "foot." + s, "frame"))
    return out


def clips(arm):
    def extra(t, aims):
        # the antenna trails the bob
        aims["antenna"] = Vector((0.1 + 0.08 * math.sin(2 * math.pi * t * 2 - 1.2), 0.12 + 0.12 * math.sin(4 * math.pi * t - 1.4), 1.0))
    ra.walk(arm, J, "Walk", frames=24, step=WALK_STEP, lift=0.085, bob=0.022, sway=0.018, arm_swing=0.38, lean=0.1,
            twist=0.14, extra=extra)
