"""Brute Bot, HQ: a hunched heavy. A massive barrel chest with a red core behind a grille, huge hazard-striped shoulder
pauldrons, a small angry head sunk low between them, piston upper arms, great armoured forearms ending in knuckled fists,
short thick legs, and two exhaust stacks glowing on its back. Rigid parts on bones; faces -Y, Z up (model_scale 0.9).
"""
import math
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3
import robot_anim as ra
from mathutils import Vector

ROOT_NAME = "Brute"
GLB_NAME = "brute"
TEX_PREFIX = "brute"
WALK_STEP = 0.42
WALK_FRAMES = 32

ORANGE = (1.0, 0.47, 0.08)
SEAM = (0.2, 0.2, 0.22)
BLACK = (0.08, 0.08, 0.09)


def mirror(p):
    return (-p[0], p[1], p[2])


J = {
    "hip_L": (0.17, 0.03, 0.56), "knee_L": (0.21, -0.04, 0.33), "ankle_L": (0.21, 0.03, 0.11), "toe_L": (0.21, -0.15, 0.05),
    "shoulder_L": (0.45, 0.02, 1.06), "elbow_L": (0.53, 0.06, 0.8), "wrist_L": (0.56, -0.04, 0.52), "hand_L": (0.56, -0.07, 0.38),
}
for k in list(J):
    if k.endswith("_L"):
        J[k[:-2] + "_R"] = mirror(J[k])

BONES = [
    ("root", (0, 0, 0.56), (0, 0, 0.68), None),
    ("spine", (0, 0.02, 0.68), (0, 0.0, 1.18), "root"),
    ("head", (0, -0.17, 1.08), (0, -0.2, 1.26), "spine"),
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
    "armor": ("armor", dict(name="RB_BruteArmor", base=(0.9, 0.9, 0.87), labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, BLACK, 0.4)], seams=[2], wear=1.2)),
    "frame": ("gunmetal", dict(name="RB_BruteFrame", labels=[(1, ORANGE, 0.35), (2, (0.1, 0.1, 0.11), 0.6)], seams=[2])),
    "chrome": ("chrome", dict(name="RB_BruteChrome")),
    "socket": ("lens_socket", dict(name="RB_BruteSocket")),
    "glow": ("glow", dict(name="RB_BruteGlow", col=(1.0, 0.25, 0.1))),
}
GLOW_RED = (1.0, 0.22, 0.08)
GLOW = {"Core": (GLOW_RED, 1.2, 0.5), "Visor": (GLOW_RED, 1.3, 0.5), "Exhaust": ((1.0, 0.55, 0.15), 1.3, 0.5)}

LOW_TARGETS = {"Torso": 700, "Grille": 160, "Back": 260, "Pelvis": 180, "Head": 300, "Core": 60, "Visor": 50,
               "Exhaust": 40, "Abdomen": 160}
for s in "LR":
    LOW_TARGETS.update({"Pauldron" + s: 260, "UpperArm" + s: 140, "Forearm" + s: 220, "Fist" + s: 240, "Thigh" + s: 130,
                        "Knee" + s: 50, "Shin" + s: 180, "Foot" + s: 170})
FACE_Y = rot_from_axes(z_axis=(0, -1, 0))


def hazard(f, centre, half, axis_x, n=6, lab_a=1, lab_b=3, angle=0.6):
    """Diagonal hazard stripes over a box region: alternating orange (lab_a) and black (lab_b)."""
    c = v3(centre)
    for i in range(n):
        t = (i + 0.5) / n
        off = (t - 0.5) * 2 * half[0]
        R = rot_from_axes(x_axis=(math.cos(angle), 0, math.sin(angle)), y_axis=(0, 1, 0)) if axis_x else None
        f.paint(RoundBox(c + v3((off, 0, 0)), (half[0] / n, half[1], half[2] * 2.0), 0.0, R=R), lab_a if i % 2 == 0 else lab_b)


def parts(fine=False):
    vx = 0.0055 if fine else 0.009
    vs = 0.004 if fine else 0.008
    out = []
    # ---- chest: massive, hunched forward; core behind a grille; hazard band low on the belly
    f = Field("Torso")
    f.add(RoundBox((0, 0.03, 0.93), (0.29, 0.21, 0.2), 0.13))
    f.add(Ellipsoid((0, -0.02, 1.06), (0.34, 0.25, 0.17)), k=0.06)
    f.sub(Sphere((0, -0.27, 0.92), 0.12), k=0.015)                         # core recess
    f.sub(RoundBox((0, -0.13, 1.12), (0.13, 0.12, 0.09), 0.05), k=0.02)    # the head sits low in a notch
    f.paint(RoundBox((0, -0.05, 0.765), (0.5, 0.4, 0.03)), 1)              # orange belly band
    f.paint(RoundBox((0, -0.05, 0.725), (0.5, 0.4, 0.004)), 2)
    f.paint(RoundBox((0, -0.3, 1.0), (0.004, 0.06, 0.2)), 2)
    for sx in (-1, 1):
        f.paint(RoundBox((sx * 0.2, -0.22, 0.9), (0.05, 0.05, 0.1), 0.02), 2)
    out.append(("Torso", f, vx, "spine", "armor"))
    f = Field("Grille")                                                    # bars over the core
    f.add(Torus((0, -0.245, 0.92), 0.115, 0.022, R=FACE_Y))
    for dz in (-0.05, 0.0, 0.05):
        f.add(RoundCone((-0.1, -0.265, 0.92 + dz), (0.1, -0.265, 0.92 + dz), 0.012), k=0.004)
    out.append(("Grille", f, vs, "spine", "frame"))
    f = Field("Core")
    f.add(Ellipsoid((0, -0.22, 0.92), (0.1, 0.05, 0.1)))
    out.append(("Core", f, vs, "spine", "glow"))
    f = Field("Abdomen")
    for i, (z, r) in enumerate(((0.66, 0.17), (0.705, 0.19))):
        f.add(Cylinder((0, 0.03, z), r, 0.04, rr=0.014), k=0.004)
    out.append(("Abdomen", f, vx, "root", "frame"))
    f = Field("Back")                                                      # reactor block and two stacks
    f.add(RoundBox((0, 0.26, 1.0), (0.2, 0.08, 0.15), 0.05))
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.11, 0.3, 1.2), 0.05, 0.28, rr=0.012), k=0.012)
        f.add(Torus((sx * 0.11, 0.3, 1.33), 0.05, 0.012), k=0.004)
        f.sub(Cylinder((sx * 0.11, 0.3, 1.36), 0.034, 0.06), k=0.004)
    for i in range(5):
        f.paint(RoundBox((0, 0.345, 0.92 + i * 0.035), (0.15, 0.012, 0.007), 0.004), 2)
    out.append(("Back", f, vx, "spine", "frame"))
    f = Field("Exhaust")
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.11, 0.3, 1.322), 0.034, 0.012, rr=0.004))
    out.append(("Exhaust", f, vs, "spine", "glow"))
    f = Field("Pelvis")
    f.add(RoundBox((0, 0.03, 0.58), (0.21, 0.13, 0.07), 0.05))
    for sx in (-1, 1):
        f.add(Sphere((sx * 0.17, 0.03, 0.56), 0.075), k=0.015)
    out.append(("Pelvis", f, vx, "root", "frame"))
    # ---- head: small, angry, low between the shoulders
    f = Field("Head")
    f.add(RoundBox((0, -0.2, 1.15), (0.105, 0.095, 0.08), 0.05))
    f.add(RoundBox((0, -0.24, 1.2), (0.11, 0.05, 0.03), 0.02, R=rot_from_axes(x_axis=(1, 0, 0), y_axis=(0, -1, -0.5))), k=0.02)   # brow
    f.sub(RoundBox((0, -0.3, 1.15), (0.08, 0.04, 0.018), 0.012, R=rot_from_axes(x_axis=(1, 0, 0.0), y_axis=(0, -1, 0))), k=0.006)
    for z in (1.09, 1.105):
        f.paint(RoundBox((0, -0.29, z), (0.05, 0.03, 0.004)), 3)
    f.paint(RoundBox((0, -0.2, 1.24), (0.025, 0.2, 0.05)), 1)
    out.append(("Head", f, vs, "head", "armor"))
    f = Field("Visor")
    f.add(RoundBox((0, -0.282, 1.15), (0.075, 0.016, 0.015), 0.012))
    out.append(("Visor", f, vs, "head", "glow"))

    for s, sx in (("L", 1), ("R", -1)):
        sh, el, wr, hd = (v3(J[k + "_" + s]) for k in ("shoulder", "elbow", "wrist", "hand"))
        f = Field("Pauldron" + s)                                          # huge striped shoulder armour
        f.add(Ellipsoid(sh + v3((sx * 0.02, 0.0, 0.08)), (0.2, 0.2, 0.15)))
        f.add(Torus(sh + v3((sx * 0.02, 0.0, 0.03)), 0.18, 0.025), k=0.015)
        f.sub(Ellipsoid(sh + v3((sx * 0.02, 0.0, -0.04)), (0.15, 0.15, 0.11)), k=0.01)
        hazard(f, sh + v3((sx * 0.02, 0.0, 0.2)), (0.22, 0.3, 0.04), True, n=7, angle=0.0)
        f.paint(RoundBox(sh + v3((sx * 0.02, 0, 0.1)), (0.3, 0.3, 0.004)), 2)
        out.append(("Pauldron" + s, f, vx, "upperarm." + s, "armor"))
        f = Field("UpperArm" + s)
        f.add(RoundCone(sh, el, 0.07, 0.06))
        f.add(Sphere(el, 0.075), k=0.012)
        for i in range(3):
            f.paint(RoundBox(sh + (el - sh) * (0.35 + 0.15 * i), (0.12, 0.12, 0.005)), 2)
        out.append(("UpperArm" + s, f, vx, "upperarm." + s, "frame"))
        f = Field("Forearm" + s)                                           # great armoured forearm
        f.add(RoundCone(el + (wr - el) * 0.1, wr, 0.1, 0.12))
        f.add(Ellipsoid(el + (wr - el) * 0.6 + v3((sx * 0.03, 0, 0)), (0.12, 0.12, 0.13)), k=0.04)
        f.paint(RoundBox(el + (wr - el) * 0.25, (0.3, 0.3, 0.022)), 1)
        f.paint(RoundBox(el + (wr - el) * 0.75, (0.3, 0.3, 0.005)), 2)
        out.append(("Forearm" + s, f, vx, "forearm." + s, "armor"))
        f = Field("Fist" + s)                                              # knuckled fist
        f.add(RoundBox(wr + v3((0, -0.03, -0.1)), (0.1, 0.1, 0.09), 0.05))
        for i, dx in enumerate((-0.06, -0.02, 0.02, 0.06)):
            f.add(Sphere(wr + v3((dx, -0.12, -0.12)), 0.032), k=0.012)
        f.add(RoundCone(wr + v3((-sx * 0.08, -0.07, -0.06)), wr + v3((-sx * 0.1, -0.12, -0.12)), 0.03, 0.025), k=0.01)
        f.paint(RoundBox(wr + v3((0, -0.03, -0.035)), (0.2, 0.2, 0.005)), 2)
        out.append(("Fist" + s, f, vx, "hand." + s, "frame"))
        hp, kn, an, to = (v3(J[k + "_" + s]) for k in ("hip", "knee", "ankle", "toe"))
        f = Field("Thigh" + s)
        f.add(RoundCone(hp, kn, 0.075, 0.065))
        f.add(RoundBox(hp + (kn - hp) * 0.45 + v3((sx * 0.02, -0.05, 0)), (0.07, 0.025, 0.08), 0.02,
                       R=rot_from_axes(y_axis=(0, -1, 0), z_axis=(kn - hp))), k=0.02)
        out.append(("Thigh" + s, f, vx, "thigh." + s, "frame"))
        f = Field("Knee" + s)
        f.add(Ellipsoid(kn + v3((0, -0.05, 0.01)), (0.07, 0.045, 0.065)))
        hazard(f, kn + v3((0, -0.08, 0.01)), (0.08, 0.1, 0.06), True, n=4, angle=0.0)
        out.append(("Knee" + s, f, vs, "shin." + s, "armor"))
        f = Field("Shin" + s)
        f.add(RoundCone(kn + (an - kn) * 0.15, an + (kn - an) * 0.12, 0.095, 0.08))
        f.add(Ellipsoid(kn + (an - kn) * 0.5 + v3((0, 0.01, 0)), (0.1, 0.1, 0.11)), k=0.03)
        f.paint(RoundBox(kn + (an - kn) * 0.7, (0.3, 0.3, 0.005)), 2)
        out.append(("Shin" + s, f, vx, "shin." + s, "armor"))
        f = Field("Foot" + s)
        f.add(RoundBox(an + v3((0, -0.07, -0.065)), (0.11, 0.16, 0.05), 0.035))
        for dx in (-0.06, 0.0, 0.06):
            f.add(Ellipsoid(an + v3((dx, -0.2, -0.07)), (0.04, 0.05, 0.04)), k=0.015)
        f.add(Sphere(an, 0.065), k=0.02)
        out.append(("Foot" + s, f, vx, "foot." + s, "frame"))
    return out


def clips(arm):
    ra.walk(arm, J, "Walk", frames=WALK_FRAMES, step=WALK_STEP, lift=0.07, bob=0.03, sway=0.04, arm_swing=0.32, lean=0.18,
            twist=0.2, heavy=1.0)
