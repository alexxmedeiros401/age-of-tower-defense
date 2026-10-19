"""Shield Bot, HQ: the Bronze Age's shield wall. A broad, heavy biped in white armour with cobalt-blue stripes: a squat
domed helmet with a wide cyan visor and a jaw guard, a barrel chest round a hexagonal cyan generator core, a ring-shaped
shield emitter on its back, heavy shoulder pads, armoured gauntlets and shins, chunky boots. On its left forearm it
carries a tall gunmetal shield frame with emitter nodes round its rim and a panel of cyan energy across it (game.gd
makes the panel see-through and hides it while the robot's shield is down); its right fist swings as it marches.
Rigid parts, each on one bone; faces -Y, Z up; model_scale 0.9. The shield arm is modelled in the carrying pose (its
rest pose), and the Walk clip keeps it there, so the shield stays up in front as the legs march behind it.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3, norm
import robot_anim as ra
from mathutils import Vector

ROOT_NAME = "ShieldBot"
GLB_NAME = "shield_bot"
TEX_PREFIX = "shield_bot"
WALK_STEP = 0.46

BLUE = (0.12, 0.3, 0.74)
SEAM = (0.2, 0.2, 0.22)
CYAN = (0.3, 0.88, 1.0)


def mirror(p):
    return (-p[0], p[1], p[2])


J = {
    "hip_L": (0.14, 0.01, 0.62), "knee_L": (0.16, -0.05, 0.36), "ankle_L": (0.16, 0.02, 0.11), "toe_L": (0.16, -0.15, 0.05),
    "shoulder_R": (-0.33, 0.0, 1.0), "elbow_R": (-0.39, 0.03, 0.78), "wrist_R": (-0.41, -0.02, 0.58), "hand_R": (-0.41, -0.05, 0.47),
    # the shield arm, in its carrying pose: the forearm across the front, the shield before it
    "shoulder_L": (0.33, 0.0, 1.0), "elbow_L": (0.4, -0.08, 0.8), "wrist_L": (0.28, -0.3, 0.78), "hand_L": (0.24, -0.36, 0.78),
    "ant_base": (-0.08, 0.04, 1.36), "ant_tip": (-0.11, 0.09, 1.55),
}
for k in ("hip", "knee", "ankle", "toe"):
    J[k + "_R"] = mirror(J[k + "_L"])

SHIELD_C = v3((0.15, -0.43, 0.8))           # the shield panel's middle (rest pose)
SHIELD_HW, SHIELD_HH = 0.19, 0.29          # its half width and half height
SHIELD_R = rot_from_axes(z_axis=(0.12, -1.0, 0.0), y_axis=(0, 0, 1))     # facing forward, turned a touch outward

BONES = [
    ("root", (0, 0, 0.62), (0, 0, 0.72), None),
    ("spine", (0, 0, 0.72), (0, 0, 1.07), "root"),
    ("head", (0, 0, 1.08), (0, 0, 1.32), "spine"),
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
    "armor": ("armor", dict(name="RB_ShieldArmor", labels=[(1, BLUE, 0.35), (2, SEAM, 0.6), (3, (0.12, 0.12, 0.13), 0.5)], seams=[2])),
    "frame": ("gunmetal", dict(name="RB_ShieldFrame", labels=[(1, BLUE, 0.35), (2, (0.1, 0.1, 0.11), 0.6)], seams=[2])),
    "chrome": ("chrome", dict(name="RB_ShieldChrome")),
    "socket": ("lens_socket", dict(name="RB_ShieldSocket")),
    "glow": ("glow", dict(name="RB_ShieldGlow", col=CYAN)),
}
GLOW = {"Core": (CYAN, 1.2, 0.5), "Visor": (CYAN, 1.3, 0.5), "Emitter": (CYAN, 1.2, 0.5), "Nodes": (CYAN, 1.3, 0.5),
        "ShieldPanel": (CYAN, 0.9, 0.6), "AntennaTip": (CYAN, 1.2, 0.5)}

LOW_TARGETS = {
    "Abdomen": 160, "Torso": 620, "Back": 320, "Emitter": 80, "Pelvis": 180, "Neck": 40, "CoreRing": 110, "Core": 60,
    "Head": 420, "Visor": 60, "Ears": 80, "Antenna": 50, "AntennaTip": 30, "ShieldFrame": 520, "ShieldPanel": 60, "Nodes": 90,
}
for s in "LR":
    LOW_TARGETS.update({"Shoulder" + s: 160, "UpperArm" + s: 80, "Forearm" + s: 150, "Hand" + s: 140, "Thigh" + s: 110,
                        "Knee" + s: 50, "Shin" + s: 170, "Foot" + s: 160})

FACE_Y = rot_from_axes(z_axis=(0, -1, 0))


def seam_ring_z(f, z, w=0.004, lab=2):
    f.paint(RoundBox((0, 0, z), (0.6, 0.6, w)), lab)


def parts(fine=False):
    vx = 0.0045 if fine else 0.008
    vs = 0.0035 if fine else 0.007
    out = []

    # ---- torso: broad barrel chest, a hexagonal core socket, a blue band over the shoulders
    f = Field("Torso")
    f.add(RoundBox((0, 0.01, 0.92), (0.23, 0.16, 0.14), 0.09))
    f.add(Ellipsoid((0, -0.01, 0.98), (0.26, 0.18, 0.12)), k=0.04)
    f.sub(Sphere((0, -0.19, 0.9), 0.09), k=0.012)
    f.sub(RoundBox((0, 0.2, 0.93), (0.17, 0.06, 0.12), 0.03), k=0.01)
    f.paint(RoundBox((0, -0.02, 1.04), (0.32, 0.32, 0.027)), 1)
    seam_ring_z(f, 0.8)
    for sx in (-1, 1):
        f.paint(RoundBox((sx * 0.15, -0.15, 0.82), (0.035, 0.06, 0.016), 0.01), 3)
        f.paint(RoundBox((sx * 0.12, -0.2, 0.98), (0.004, 0.04, 0.08)), 2)
    out.append(("Torso", f, vx, "spine", "armor"))
    f = Field("Abdomen")
    for z, r in ((0.725, 0.135), (0.765, 0.145), (0.805, 0.155)):
        f.add(Cylinder((0, 0.01, z), r, 0.034, rr=0.012), k=0.004)
    out.append(("Abdomen", f, vx, "spine", "frame"))
    f = Field("CoreRing")
    f.add(Torus((0, -0.17, 0.9), 0.088, 0.018, R=FACE_Y))
    for i in range(6):
        a = i * math.pi / 3 + math.pi / 6
        f.add(Sphere((0.105 * math.cos(a), -0.16, 0.9 + 0.105 * math.sin(a)), 0.013), k=0.004)
    out.append(("CoreRing", f, vs, "spine", "frame"))
    f = Field("Core")
    for k in range(3):                                                       # a hexagonal glowing core
        a = k * math.pi / 3
        R = FACE_Y @ np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        f.add(RoundBox((0, -0.165, 0.9), (0.07, 0.04, 0.03), 0.012, R=R))
    out.append(("Core", f, vs, "spine", "glow"))

    # ---- the shield emitter on the back: a ring on a mount, glowing
    f = Field("Back")
    f.add(RoundBox((0, 0.2, 0.93), (0.15, 0.06, 0.12), 0.035))
    f.add(Torus((0, 0.27, 0.98), 0.11, 0.028, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.01)
    for sx in (-1, 1):
        f.add(RoundCone((sx * 0.1, 0.22, 0.86), (sx * 0.08, 0.26, 0.92), 0.02, 0.016), k=0.008)
    for i in range(3):
        f.paint(RoundBox((0, 0.262, 0.84 + i * 0.03), (0.1, 0.01, 0.006), 0.004), 2)
    out.append(("Back", f, vx, "spine", "frame"))
    f = Field("Emitter")
    f.add(Torus((0, 0.29, 0.98), 0.085, 0.012, R=rot_from_axes(z_axis=(0, 1, 0))))
    out.append(("Emitter", f, vs, "spine", "glow"))

    f = Field("Pelvis")
    f.add(RoundBox((0, 0.01, 0.66), (0.17, 0.11, 0.06), 0.045))
    for sx in (-1, 1):
        f.add(Sphere((sx * 0.14, 0.01, 0.62), 0.065), k=0.015)
    seam_ring_z(f, 0.66, 0.003)
    out.append(("Pelvis", f, vx, "root", "frame"))
    f = Field("Neck")
    f.add(Cylinder((0, 0.0, 1.08), 0.055, 0.08, rr=0.01))
    out.append(("Neck", f, vs, "spine", "frame"))

    # ---- head: a squat dome with a wide visor and a jaw guard, a blue crest stripe
    f = Field("Head")
    f.add(Ellipsoid((0, 0.005, 1.225), (0.18, 0.165, 0.135)))
    f.add(RoundBox((0, -0.035, 1.14), (0.14, 0.12, 0.055), 0.045), k=0.035)
    f.sub(RoundBox((0, -0.175, 1.215), (0.15, 0.055, 0.03), 0.022), k=0.008)       # the visor slot
    f.paint(RoundBox((0, 0.0, 1.345), (0.04, 0.24, 0.07), 0.01), 1)
    for z in (1.112, 1.13, 1.148):
        f.paint(RoundBox((0, -0.16, z), (0.07, 0.03, 0.0045)), 3)
    out.append(("Head", f, vx, "head", "armor"))
    f = Field("Visor")
    f.add(RoundBox((0, -0.15, 1.215), (0.142, 0.026, 0.024), 0.018))
    out.append(("Visor", f, vs, "head", "glow"))
    f = Field("Ears")
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.18, 0.0, 1.215), 0.05, 0.05, rr=0.013, R=rot_from_axes(z_axis=(1, 0, 0))))
        f.paint(Cylinder((sx * 0.18, 0.0, 1.215), 0.056, 0.03, R=rot_from_axes(z_axis=(1, 0, 0))), 1)
    out.append(("Ears", f, vs, "head", "frame"))
    f = Field("Antenna")
    f.add(Cylinder(J["ant_base"], 0.028, 0.025, rr=0.008))
    f.add(RoundCone(J["ant_base"], J["ant_tip"], 0.011, 0.008), k=0.006)
    out.append(("Antenna", f, vs, "antenna", "frame"))
    f = Field("AntennaTip")
    f.add(Sphere(J["ant_tip"], 0.024))
    out.append(("AntennaTip", f, vs, "antenna", "glow"))

    # ---- the shield: a tall gunmetal frame with a rim, cross braces behind, emitter nodes; a panel of energy across it
    f = Field("ShieldFrame")
    nrm = SHIELD_R[:, 2]
    def frame_box(c, half, rr=0.012):
        return RoundBox(c, half, rr, R=SHIELD_R)
    f.add(frame_box(SHIELD_C, (SHIELD_HW + 0.03, SHIELD_HH + 0.03, 0.02), 0.03))
    f.sub(frame_box(SHIELD_C - nrm * 0.0, (SHIELD_HW - 0.01, SHIELD_HH - 0.01, 0.05), 0.02), k=0.006)
    u, w = SHIELD_R[:, 0], SHIELD_R[:, 1]
    back = SHIELD_C + nrm * -0.03                               # (the braces sit behind the panel, toward the arm)
    for d in (u * SHIELD_HW + w * SHIELD_HH, u * SHIELD_HW - w * SHIELD_HH):
        f.add(RoundCone(back + d * 0.95, back - d * 0.95, 0.012, 0.012), k=0.008)
    f.add(Cylinder(back, 0.05, 0.03, rr=0.008, R=SHIELD_R), k=0.01)              # the hub where the braces cross
    hand = v3(J["hand_L"])
    f.add(RoundCone(back, hand + (back - hand) * 0.25, 0.022, 0.02), k=0.01)      # the grip post to the fist
    for sgn in (-1, 1):
        f.paint(frame_box(SHIELD_C + w * sgn * (SHIELD_HH + 0.012), (SHIELD_HW + 0.05, 0.012, 0.03)), 1)
    out.append(("ShieldFrame", f, vs, "hand.L", "frame"))
    f = Field("Nodes")
    for su in (-1, 0, 1):
        for sw in (-1, 1):
            p = SHIELD_C + u * su * (SHIELD_HW + 0.03) + w * sw * (SHIELD_HH + 0.03) + nrm * 0.02
            f.add(Sphere(p, 0.018))
    for sw in (-1, 1):
        f.add(Sphere(SHIELD_C + u * sw * (SHIELD_HW + 0.03) + nrm * 0.02, 0.018))
    out.append(("Nodes", f, vs, "hand.L", "glow"))
    f = Field("ShieldPanel")
    f.add(frame_box(SHIELD_C, (SHIELD_HW, SHIELD_HH, 0.006), 0.004))
    out.append(("ShieldPanel", f, vs, "hand.L", "glow"))

    for s, sx in (("L", 1), ("R", -1)):
        sh, el, wr, hd = (v3(J[k + "_" + s]) for k in ("shoulder", "elbow", "wrist", "hand"))
        f = Field("Shoulder" + s)
        f.add(Ellipsoid(sh + v3((sx * 0.03, 0, 0.035)), (0.14, 0.135, 0.1)))
        f.add(Torus(sh + v3((sx * 0.03, 0, -0.005)), 0.125, 0.018), k=0.01)
        f.sub(Ellipsoid(sh + v3((sx * 0.025, 0, -0.055)), (0.1, 0.1, 0.07)), k=0.01)
        f.paint(RoundBox(sh + v3((sx * 0.03, 0, 0.12)), (0.22, 0.032, 0.08)), 1)
        out.append(("Shoulder" + s, f, vx, "upperarm." + s, "armor"))
        f = Field("UpperArm" + s)
        f.add(RoundCone(sh, el, 0.046, 0.04))
        f.add(Sphere(el, 0.05), k=0.01)
        out.append(("UpperArm" + s, f, vs, "upperarm." + s, "frame"))
        f = Field("Forearm" + s)
        f.add(RoundCone(el + (wr - el) * 0.12, wr, 0.064, 0.055))
        f.add(RoundBox(el + (wr - el) * 0.55, (0.028, 0.055, 0.09), 0.018, R=rot_from_axes(z_axis=(wr - el), x_axis=(1, 0, 0))), k=0.02)
        f.paint(RoundBox(el + (wr - el) * 0.62, (0.2, 0.2, 0.004), R=rot_from_axes(z_axis=(wr - el))), 2)
        out.append(("Forearm" + s, f, vx, "forearm." + s, "armor"))
        f = Field("Hand" + s)
        ax = norm(hd - wr)
        f.add(RoundBox(wr + ax * 0.05, (0.05, 0.042, 0.045), 0.022, R=rot_from_axes(z_axis=ax)))
        side = norm(np.cross(ax, v3((0, 0, 1)))) if abs(ax[2]) < 0.9 else v3((1, 0, 0))
        for dx in (-0.032, 0.0, 0.032):
            base = wr + ax * 0.085 + side * dx
            f.add(RoundCone(base, base + ax * 0.06 + v3((0, 0, -0.02)), 0.017, 0.009), k=0.006)
        out.append(("Hand" + s, f, vs, "hand." + s, "frame"))
        hp, kn, an, to = (v3(J[k + "_" + s]) for k in ("hip", "knee", "ankle", "toe"))
        f = Field("Thigh" + s)
        f.add(RoundCone(hp, kn, 0.058, 0.05))
        f.add(RoundBox(hp + (kn - hp) * 0.5 + v3((0, -0.045, 0)), (0.06, 0.022, 0.085), 0.015,
                       R=rot_from_axes(y_axis=(0, -1, 0), z_axis=(kn - hp))), k=0.015)
        out.append(("Thigh" + s, f, vx, "thigh." + s, "frame"))
        f = Field("Knee" + s)
        f.add(Ellipsoid(kn + v3((0, -0.04, 0.005)), (0.055, 0.038, 0.055)))
        out.append(("Knee" + s, f, vs, "shin." + s, "chrome"))
        f = Field("Shin" + s)
        f.add(RoundCone(kn + (an - kn) * 0.12, an + (kn - an) * 0.1, 0.075, 0.06))
        f.add(Ellipsoid(kn + (an - kn) * 0.45 + v3((0, 0.012, 0)), (0.078, 0.076, 0.105)), k=0.03)
        f.paint(RoundBox(kn + (an - kn) * 0.18, (0.2, 0.2, 0.02)), 1)
        f.paint(RoundBox(kn + (an - kn) * 0.6, (0.2, 0.2, 0.004)), 2)
        out.append(("Shin" + s, f, vx, "shin." + s, "armor"))
        f = Field("Foot" + s)
        f.add(RoundBox(an + v3((0, -0.065, -0.062)), (0.09, 0.145, 0.048), 0.034))
        f.add(Ellipsoid(an + v3((0, -0.145, -0.052)), (0.086, 0.08, 0.052)), k=0.02)
        f.add(Sphere(an, 0.054), k=0.02)
        f.paint(RoundBox(an + v3((0, -0.06, -0.103)), (0.11, 0.21, 0.012)), 2)
        out.append(("Foot" + s, f, vx, "foot." + s, "frame"))
    return out


def clips(arm):
    sh, el, wr, hd = (Vector(J[k + "_L"]) for k in ("shoulder", "elbow", "wrist", "hand"))
    def extra(t, aims):
        # the shield arm holds its carrying pose (a small jolt at each footfall); the antenna trails the bob
        jolt = 0.04 * math.cos(4 * math.pi * t)
        aims["upperarm.L"] = (el - sh).normalized() + Vector((0, 0, jolt))
        aims["forearm.L"] = (wr - el).normalized() + Vector((0, 0, jolt * 0.5))
        aims["hand.L"] = (hd - wr).normalized()
        aims["antenna"] = Vector((-0.1 - 0.06 * math.sin(2 * math.pi * t - 1.2), 0.2 + 0.12 * math.sin(4 * math.pi * t - 1.4), 1.0))
    ra.walk(arm, J, "Walk", frames=24, step=WALK_STEP, lift=0.08, bob=0.024, sway=0.02, arm_swing=0.4, lean=0.08,
            twist=0.1, heavy=0.5, extra=extra)
