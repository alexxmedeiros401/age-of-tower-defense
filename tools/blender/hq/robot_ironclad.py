"""Ironclad, HQ: the Iron Age's armoured heavy. A squat, broad walker clad in thick riveted steel plates: a deep box body
behind a huge riveted mantlet plate across its front (an orange band along its top, a seam where its two plates meet),
a small domed head sunk low behind the mantlet's rim with a narrow orange visor slit, great rounded pauldrons with rows
of rivets and orange stripes, short piston arms ending in heavy clamp hands, a riveted boiler drum on its back with two
glowing vents; short thick legs with knee plates and broad feet. Rigid parts on bones; faces -Y, Z up (model_scale 0.9).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3, norm, euler
import robot_anim as ra
from mathutils import Vector

ROOT_NAME = "Ironclad"
GLB_NAME = "ironclad"
TEX_PREFIX = "ironclad"
WALK_STEP = 0.38
WALK_FRAMES = 32

ORANGE = (1.0, 0.42, 0.1)
SEAM = (0.2, 0.2, 0.22)
BLACK = (0.08, 0.08, 0.09)
STEEL = (0.64, 0.66, 0.7)


def mirror(p):
    return (-p[0], p[1], p[2])


J = {
    "hip_L": (0.17, 0.02, 0.5), "knee_L": (0.2, -0.04, 0.3), "ankle_L": (0.2, 0.03, 0.1), "toe_L": (0.2, -0.15, 0.04),
    "shoulder_L": (0.44, 0.03, 0.97), "elbow_L": (0.52, 0.07, 0.73), "wrist_L": (0.54, -0.02, 0.5), "hand_L": (0.54, -0.05, 0.37),
}
for k in list(J):
    if k.endswith("_L"):
        J[k[:-2] + "_R"] = mirror(J[k])

BONES = [
    ("root", (0, 0, 0.5), (0, 0, 0.62), None),
    ("spine", (0, 0.02, 0.62), (0, 0.0, 1.1), "root"),
    ("head", (0, -0.1, 1.02), (0, -0.12, 1.2), "spine"),
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
    "armor": ("armor", dict(name="RB_IronArmor", base=STEEL, labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, BLACK, 0.45)], seams=[2],
                            wear=1.3)),
    "frame": ("gunmetal", dict(name="RB_IronFrame", labels=[(1, ORANGE, 0.35), (2, (0.1, 0.1, 0.11), 0.6)], seams=[2])),
    "chrome": ("chrome", dict(name="RB_IronChrome")),
    "glow": ("glow", dict(name="RB_IronGlow", col=(1.0, 0.45, 0.1))),
}
GLOW_O = (1.0, 0.45, 0.1)
GLOW = {"Visor": (GLOW_O, 1.3, 0.5), "Vents": ((1.0, 0.55, 0.15), 1.3, 0.5)}

LOW_TARGETS = {"Torso": 600, "Mantlet": 520, "Back": 360, "Vents": 40, "Pelvis": 180, "Abdomen": 140, "Head": 260, "Visor": 40}
for s in "LR":
    LOW_TARGETS.update({"Pauldron" + s: 300, "UpperArm" + s: 110, "Forearm" + s: 200, "Hand" + s: 200, "Thigh" + s: 120,
                        "Knee" + s: 70, "Shin" + s: 180, "Foot" + s: 170})
FACE_Y = rot_from_axes(z_axis=(0, -1, 0))


def rivets(f, pts, r=0.011):
    for p in pts:
        f.add(Sphere(p, r), k=0.004)


def parts(fine=False):
    vx = 0.0055 if fine else 0.009
    vs = 0.004 if fine else 0.008
    out = []
    # ---- the body: a deep box, the head sunk in a notch at its top front
    f = Field("Torso")
    f.add(RoundBox((0, 0.04, 0.85), (0.3, 0.2, 0.2), 0.08))
    f.add(Ellipsoid((0, 0.03, 0.98), (0.34, 0.24, 0.13)), k=0.05)
    f.sub(RoundBox((0, -0.12, 1.07), (0.14, 0.13, 0.08), 0.05), k=0.02)
    f.paint(RoundBox((0, 0.04, 0.68), (0.5, 0.4, 0.004)), 2)
    for sx in (-1, 1):
        f.paint(RoundBox((sx * 0.31, 0.04, 0.86), (0.02, 0.24, 0.13), 0.01), 1)
    out.append(("Torso", f, vx, "spine", "armor"))
    # ---- the mantlet: a great riveted plate across its front, leaning back a little
    f = Field("Mantlet")
    R = euler(-0.12, 0, 0)
    c = v3((0, -0.215, 0.84))
    f.add(RoundBox(c, (0.29, 0.032, 0.2), 0.024, R=R))
    f.add(RoundBox(c + R @ v3((0, -0.012, 0.19)), (0.3, 0.03, 0.026), 0.016, R=R), k=0.008)          # its rolled top rim
    fr = R @ v3((0, -1, 0))
    pts = []
    for i in range(9):
        x = -0.24 + 0.06 * i
        for zz in (-0.16, 0.135):
            pts.append(c + R @ v3((x, -0.034, zz)))
    for j in range(4):
        zz = -0.1 + 0.07 * j
        for x in (-0.255, 0.255):
            pts.append(c + R @ v3((x, -0.034, zz)))
    rivets(f, pts, 0.012)
    f.paint(RoundBox(c + R @ v3((0, -0.03, 0.185)), (0.32, 0.06, 0.03)), 1)
    f.paint(RoundBox(c + R @ v3((0, -0.03, -0.01)), (0.32, 0.06, 0.004)), 2)
    f.paint(RoundBox(c + R @ v3((0, -0.03, -0.2)), (0.32, 0.06, 0.02)), 3)
    out.append(("Mantlet", f, vx, "spine", "armor"))
    # ---- the boiler on its back, its two vents
    f = Field("Back")
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    f.add(Cylinder((0, 0.28, 0.9), 0.14, 0.4, rr=0.04, R=Rx))
    for x in (-0.15, 0.0, 0.15):
        f.add(Torus((x, 0.28, 0.9), 0.142, 0.01, R=Rx), k=0.004)
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.1, 0.3, 1.07), 0.045, 0.16, rr=0.01), k=0.015)
        f.add(Torus((sx * 0.1, 0.3, 1.15), 0.046, 0.012), k=0.004)
        f.sub(Cylinder((sx * 0.1, 0.3, 1.17), 0.032, 0.06), k=0.004)
    rivets(f, [v3((x, 0.28 + 0.14 * math.sin(a), 0.9 + 0.14 * math.cos(a))) for x in (-0.18, 0.18)
               for a in np.linspace(-1.2, 2.6, 7)], 0.009)
    out.append(("Back", f, vx, "spine", "frame"))
    f = Field("Vents")
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.1, 0.3, 1.145), 0.032, 0.012, rr=0.004))
    out.append(("Vents", f, vs, "spine", "glow"))
    f = Field("Pelvis")
    f.add(RoundBox((0, 0.03, 0.54), (0.22, 0.13, 0.07), 0.05))
    for sx in (-1, 1):
        f.add(Sphere((sx * 0.17, 0.02, 0.5), 0.07), k=0.015)
    out.append(("Pelvis", f, vx, "root", "frame"))
    f = Field("Abdomen")
    for z, r in ((0.61, 0.18), (0.65, 0.2)):
        f.add(Cylinder((0, 0.04, z), r, 0.04, rr=0.014), k=0.004)
    out.append(("Abdomen", f, vx, "root", "frame"))
    # ---- the head: a low dome behind the mantlet's rim, a narrow visor slit
    f = Field("Head")
    f.add(RoundBox((0, -0.11, 1.07), (0.1, 0.09, 0.065), 0.045))
    f.add(Ellipsoid((0, -0.1, 1.11), (0.105, 0.095, 0.065)), k=0.03)
    f.sub(RoundBox((0, -0.2, 1.075), (0.075, 0.03, 0.013), 0.008), k=0.004)
    f.add(RoundBox((0, -0.1, 1.17), (0.016, 0.1, 0.02), 0.008), k=0.01)                    # a crest ridge
    f.paint(RoundBox((0, -0.1, 1.17), (0.03, 0.2, 0.05)), 1)
    out.append(("Head", f, vs, "head", "armor"))
    f = Field("Visor")
    f.add(RoundBox((0, -0.188, 1.075), (0.07, 0.01, 0.011), 0.008))
    out.append(("Visor", f, vs, "head", "glow"))

    for s, sx in (("L", 1), ("R", -1)):
        sh, el, wr, hd = (v3(J[k + "_" + s]) for k in ("shoulder", "elbow", "wrist", "hand"))
        f = Field("Pauldron" + s)
        pc = sh + v3((sx * 0.03, 0.0, 0.07))
        f.add(Ellipsoid(pc, (0.19, 0.19, 0.14)))
        f.add(Torus(sh + v3((sx * 0.03, 0.0, 0.02)), 0.17, 0.024), k=0.015)
        f.sub(Ellipsoid(sh + v3((sx * 0.03, 0.0, -0.05)), (0.15, 0.15, 0.1)), k=0.01)
        rp = []
        for i in range(10):
            a = 2 * math.pi * i / 10
            rp.append(pc + v3((math.cos(a) * 0.165, math.sin(a) * 0.165, 0.035)))
        rivets(f, rp, 0.011)
        f.paint(RoundBox(pc + v3((0, 0, 0.12)), (0.3, 0.05, 0.08)), 1)
        f.paint(RoundBox(pc + v3((0, 0, 0.01)), (0.3, 0.3, 0.004)), 2)
        out.append(("Pauldron" + s, f, vx, "upperarm." + s, "armor"))
        f = Field("UpperArm" + s)
        f.add(RoundCone(sh, el, 0.066, 0.058))
        f.add(Sphere(el, 0.07), k=0.012)
        for i in range(3):
            f.paint(RoundBox(sh + (el - sh) * (0.35 + 0.15 * i), (0.12, 0.12, 0.005)), 2)
        out.append(("UpperArm" + s, f, vx, "upperarm." + s, "frame"))
        f = Field("Forearm" + s)
        f.add(RoundCone(el + (wr - el) * 0.1, wr, 0.085, 0.1))
        f.add(Ellipsoid(el + (wr - el) * 0.6 + v3((sx * 0.025, 0, 0)), (0.11, 0.11, 0.12)), k=0.04)
        rivets(f, [el + (wr - el) * 0.45 + v3((sx * 0.1, dy, 0)) for dy in (-0.05, 0.0, 0.05)], 0.01)
        f.paint(RoundBox(el + (wr - el) * 0.25, (0.3, 0.3, 0.02)), 1)
        f.paint(RoundBox(el + (wr - el) * 0.78, (0.3, 0.3, 0.005)), 2)
        out.append(("Forearm" + s, f, vx, "forearm." + s, "armor"))
        f = Field("Hand" + s)                                              # a heavy clamp: two fingers and a thumb
        f.add(RoundBox(wr + v3((0, -0.02, -0.07)), (0.085, 0.08, 0.06), 0.035))
        for dx in (-0.035, 0.035):
            base = wr + v3((dx, -0.06, -0.12))
            f.add(RoundCone(base, base + v3((0, -0.03, -0.08)), 0.03, 0.022), k=0.01)
            f.add(RoundCone(base + v3((0, -0.03, -0.08)), base + v3((0, 0.01, -0.12)), 0.022, 0.016), k=0.008)
        f.add(RoundCone(wr + v3((-sx * 0.07, -0.04, -0.08)), wr + v3((-sx * 0.08, -0.03, -0.17)), 0.026, 0.02), k=0.01)
        f.paint(RoundBox(wr + v3((0, -0.02, -0.03)), (0.2, 0.2, 0.005)), 2)
        out.append(("Hand" + s, f, vx, "hand." + s, "frame"))
        hp, kn, an, to = (v3(J[k + "_" + s]) for k in ("hip", "knee", "ankle", "toe"))
        f = Field("Thigh" + s)
        f.add(RoundCone(hp, kn, 0.075, 0.065))
        f.add(RoundBox(hp + (kn - hp) * 0.45 + v3((sx * 0.02, -0.05, 0)), (0.07, 0.025, 0.07), 0.02,
                       R=rot_from_axes(y_axis=(0, -1, 0), z_axis=(kn - hp))), k=0.02)
        out.append(("Thigh" + s, f, vx, "thigh." + s, "frame"))
        f = Field("Knee" + s)
        f.add(Ellipsoid(kn + v3((0, -0.055, 0.01)), (0.075, 0.045, 0.07)))
        rivets(f, [kn + v3((dx, -0.098, 0.01)) for dx in (-0.035, 0.035)], 0.009)
        f.paint(RoundBox(kn + v3((0, -0.1, 0.045)), (0.1, 0.06, 0.018)), 1)
        out.append(("Knee" + s, f, vs, "shin." + s, "armor"))
        f = Field("Shin" + s)
        f.add(RoundCone(kn + (an - kn) * 0.15, an + (kn - an) * 0.12, 0.095, 0.085))
        f.add(Ellipsoid(kn + (an - kn) * 0.5 + v3((0, -0.01, 0)), (0.1, 0.1, 0.1)), k=0.03)
        f.paint(RoundBox(kn + (an - kn) * 0.72, (0.3, 0.3, 0.005)), 2)
        out.append(("Shin" + s, f, vx, "shin." + s, "armor"))
        f = Field("Foot" + s)
        f.add(RoundBox(an + v3((0, -0.07, -0.062)), (0.115, 0.16, 0.048), 0.034))
        for dx in (-0.065, 0.0, 0.065):
            f.add(Ellipsoid(an + v3((dx, -0.2, -0.068)), (0.04, 0.05, 0.04)), k=0.015)
        f.add(Sphere(an, 0.066), k=0.02)
        f.paint(RoundBox(an + v3((0, -0.07, -0.105)), (0.14, 0.22, 0.012)), 2)
        out.append(("Foot" + s, f, vx, "foot." + s, "frame"))
    return out


def clips(arm):
    ra.walk(arm, J, "Walk", frames=WALK_FRAMES, step=WALK_STEP, lift=0.06, bob=0.03, sway=0.04, arm_swing=0.26, lean=0.12,
            twist=0.16, heavy=1.0)
