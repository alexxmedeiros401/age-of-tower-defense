"""Iron Colossus, HQ: the Iron Age boss. A towering walking furnace of riveted steel: a great barrel chest with a furnace
door at its heart (a grate glowing orange through its bars), huge rounded pauldrons rimmed with orange and studded with
rivets, a small domed head sunk low between them with a single red eye behind a slit, massive piston arms ending in
riveted fists, thick legs with knee plates; two tall smokestacks on its back with glowing mouths, and between them a
tesla coil (copper windings, a blue-glowing crown) that fires its EMP. Walk (a slow, heavy stomp), Summon (it rears up,
arms flung wide, and its furnace blazes while Ironclads march out) and Emp (it slams both fists into the ground: the
pulse). Faces -Y, Z up, model_scale 1.0.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3, norm, euler
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser

ROOT_NAME = "IronColossus"
GLB_NAME = "iron_colossus"
TEX_PREFIX = "iron_colossus"
WALK_STEP = 0.72
WALK_FRAMES = 48

ORANGE = (1.0, 0.42, 0.1)
SEAM = (0.2, 0.2, 0.22)
BLACK = (0.08, 0.08, 0.09)
STEEL = (0.62, 0.64, 0.68)
COPPER = (0.78, 0.42, 0.22)


def mirror(p):
    return (-p[0], p[1], p[2])


J = {
    "hip_L": (0.4, 0.02, 1.3), "knee_L": (0.47, -0.12, 0.78), "ankle_L": (0.47, 0.06, 0.24), "toe_L": (0.47, -0.32, 0.09),
    "shoulder_L": (0.98, 0.04, 2.32), "elbow_L": (1.14, 0.14, 1.78), "wrist_L": (1.18, -0.06, 1.28), "hand_L": (1.18, -0.12, 0.98),
}
for k in list(J):
    if k.endswith("_L"):
        J[k[:-2] + "_R"] = mirror(J[k])

BONES = [
    ("root", (0, 0, 1.3), (0, 0, 1.52), None),
    ("spine", (0, 0.02, 1.52), (0, 0.0, 2.55), "root"),
    ("head", (0, -0.26, 2.42), (0, -0.3, 2.8), "spine"),
    ("furnace", (0, -0.5, 2.0), (0, -0.7, 2.0), "spine"),
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
    "armor": ("armor", dict(name="RB_ColossusArmor", base=STEEL, labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, BLACK, 0.45)],
                            seams=[2], wear=1.4, scale=2.0)),
    "frame": ("gunmetal", dict(name="RB_ColossusFrame", base=(0.2, 0.21, 0.24), labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6),
                                                                                         (4, COPPER, 0.3)], seams=[2], scale=2.0)),
    "chrome": ("chrome", dict(name="RB_ColossusChrome")),
    "glow": ("glow", dict(name="RB_ColossusGlow", col=(1.0, 0.45, 0.1))),
}
GLOW = {"Furnace": ((1.0, 0.5, 0.12), 1.4, 0.5), "Eye": ((1.0, 0.18, 0.08), 1.4, 0.5), "StackGlow": ((1.0, 0.55, 0.15), 1.3, 0.5),
        "CoilTip": ((0.45, 0.8, 1.0), 1.4, 0.5)}

LOW_TARGETS = {"Torso": 1100, "Grate": 260, "Furnace": 80, "Back": 700, "StackGlow": 60, "Coil": 420, "CoilTip": 80, "Pelvis": 260,
               "Abdomen": 220, "Head": 420, "Eye": 40}
for s in "LR":
    LOW_TARGETS.update({"Pauldron" + s: 520, "UpperArm" + s: 200, "Forearm" + s: 360, "Fist" + s: 360, "Thigh" + s: 220,
                        "Knee" + s: 120, "Shin" + s: 320, "Foot" + s: 300})
FACE_Y = rot_from_axes(z_axis=(0, -1, 0))


def rivets(f, pts, r=0.022):
    for p in pts:
        f.add(Sphere(p, r), k=0.008)


def parts(fine=False):
    vx = 0.009 if fine else 0.015
    vs = 0.006 if fine else 0.011
    out = []
    # ---- the chest: a great riveted barrel, the furnace door at its heart
    f = Field("Torso")
    f.add(RoundBox((0, 0.06, 2.02), (0.64, 0.46, 0.48), 0.18))
    f.add(Ellipsoid((0, 0.04, 2.28), (0.76, 0.56, 0.32)), k=0.1)
    f.sub(RoundBox((0, -0.27, 2.43), (0.24, 0.26, 0.16), 0.08), k=0.04)                  # the head sits low in a notch
    f.sub(Cylinder((0, -0.46, 2.0), 0.27, 0.2, rr=0.04, R=FACE_Y), k=0.03)              # the furnace's mouth
    for z in (1.66, 2.36):
        f.paint(RoundBox((0, 0.04, z), (1.0, 0.8, 0.006)), 2)
    pts = []
    for i in range(11):
        a = -math.pi * 0.5 + math.pi * i / 10
        pts.append(v3((0.6 * math.sin(a), -0.38 * math.cos(a) * 1.05 + 0.04, 1.6)))
    rivets(f, [p for p in pts if p[1] < -0.05], 0.02)
    for sx in (-1, 1):
        f.paint(RoundBox((sx * 0.5, -0.36, 2.0), (0.06, 0.2, 0.36), 0.03), 1)
    out.append(("Torso", f, vx, "spine", "armor"))
    f = Field("Grate")                                                                   # the furnace door's ring and bars
    f.add(Torus((0, -0.47, 2.0), 0.28, 0.045, R=FACE_Y))
    for dx in (-0.16, -0.08, 0.0, 0.08, 0.16):
        h = math.sqrt(max(0.27 ** 2 - dx * dx, 0.0))
        f.add(RoundCone((dx, -0.48, 2.0 - h), (dx, -0.48, 2.0 + h), 0.018), k=0.006)
    rivets(f, [v3((0.32 * math.cos(a), -0.5, 2.0 + 0.32 * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)], 0.018)
    f.add(RoundBox((0.33, -0.48, 2.0), (0.04, 0.03, 0.09), 0.015), k=0.01)              # a hinge
    out.append(("Grate", f, vs, "spine", "frame"))
    f = Field("Furnace")                                                                 # the fire inside
    f.add(Ellipsoid((0, -0.42, 2.0), (0.25, 0.08, 0.25)))
    out.append(("Furnace", f, vs, "furnace", "glow"))
    # ---- the back: two smokestacks and the coil between them
    f = Field("Back")
    f.add(RoundBox((0, 0.5, 2.06), (0.44, 0.14, 0.36), 0.08))
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.3, 0.56, 2.62), 0.11, 1.02, rr=0.02), k=0.03)
        for z in (2.3, 2.62, 2.94):
            f.add(Torus((sx * 0.3, 0.56, z), 0.112, 0.016), k=0.006)
        f.add(Cylinder((sx * 0.3, 0.56, 3.14), 0.15, 0.08, rr=0.02), k=0.02)              # the flared cap
        f.sub(Cylinder((sx * 0.3, 0.56, 3.18), 0.1, 0.1), k=0.01)
    for i in range(6):
        f.paint(RoundBox((0, 0.645, 1.86 + i * 0.07), (0.36, 0.02, 0.012), 0.008), 2)
    out.append(("Back", f, vx, "spine", "frame"))
    f = Field("StackGlow")
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.3, 0.56, 3.15), 0.098, 0.02, rr=0.006))
    out.append(("StackGlow", f, vs, "spine", "glow"))
    f = Field("Coil")                                                                    # copper windings on an iron mast
    f.add(Cylinder((0, 0.6, 2.62), 0.05, 0.62, rr=0.01))
    for i in range(14):
        f.add(Torus((0, 0.6, 2.4 + i * 0.03), 0.075 - 0.001 * i, 0.012), k=0.002, label=4)
    f.add(Torus((0, 0.6, 2.95), 0.14, 0.022), k=0.008)
    for a in np.linspace(0, 2 * math.pi, 4, endpoint=False):                            # its struts
        f.add(RoundCone((0.02 * math.cos(a), 0.6 + 0.02 * math.sin(a), 2.88), (0.13 * math.cos(a), 0.6 + 0.13 * math.sin(a), 2.95), 0.012), k=0.004)
    out.append(("Coil", f, vs, "spine", "frame"))
    f = Field("CoilTip")
    f.add(Sphere((0, 0.6, 3.0), 0.085))
    out.append(("CoilTip", f, vs, "spine", "glow"))
    f = Field("Pelvis")
    f.add(RoundBox((0, 0.03, 1.36), (0.46, 0.28, 0.14), 0.1))
    for sx in (-1, 1):
        f.add(Sphere((sx * 0.4, 0.02, 1.3), 0.15), k=0.03)
    f.paint(RoundBox((0, -0.26, 1.36), (0.5, 0.06, 0.03)), 1)
    out.append(("Pelvis", f, vx, "root", "frame"))
    f = Field("Abdomen")
    for z, r in ((1.47, 0.38), (1.54, 0.4), (1.61, 0.42)):
        f.add(Cylinder((0, 0.05, z), r, 0.06, rr=0.02), k=0.006)
    out.append(("Abdomen", f, vx, "root", "frame"))
    # ---- the head: a low riveted dome, one red eye behind a slit
    f = Field("Head")
    f.add(RoundBox((0, -0.28, 2.5), (0.2, 0.18, 0.13), 0.09))
    f.add(Ellipsoid((0, -0.26, 2.58), (0.21, 0.19, 0.13)), k=0.05)
    f.sub(RoundBox((0, -0.47, 2.5), (0.12, 0.06, 0.03), 0.02), k=0.008)
    f.add(RoundBox((0, -0.26, 2.7), (0.03, 0.2, 0.035), 0.015), k=0.02)
    f.paint(RoundBox((0, -0.26, 2.7), (0.06, 0.4, 0.08)), 1)
    rivets(f, [v3((x, -0.46, 2.6)) for x in (-0.15, -0.075, 0.075, 0.15)], 0.014)
    out.append(("Head", f, vs, "head", "armor"))
    f = Field("Eye")
    f.add(Ellipsoid((0, -0.445, 2.5), (0.07, 0.03, 0.026)))
    out.append(("Eye", f, vs, "head", "glow"))

    for s, sx in (("L", 1), ("R", -1)):
        sh, el, wr, hd = (v3(J[k + "_" + s]) for k in ("shoulder", "elbow", "wrist", "hand"))
        f = Field("Pauldron" + s)
        pc = sh + v3((sx * 0.06, 0.0, 0.16))
        f.add(Ellipsoid(pc, (0.42, 0.42, 0.3)))
        f.add(Torus(sh + v3((sx * 0.06, 0.0, 0.05)), 0.38, 0.05), k=0.03)
        f.sub(Ellipsoid(sh + v3((sx * 0.06, 0.0, -0.1)), (0.33, 0.33, 0.22)), k=0.02)
        rivets(f, [pc + v3((math.cos(a) * 0.36, math.sin(a) * 0.36, 0.06)) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)], 0.022)
        f.paint(RoundBox(pc + v3((0, 0, 0.27)), (0.6, 0.09, 0.15)), 1)
        f.paint(RoundBox(pc + v3((0, 0, 0.02)), (0.6, 0.6, 0.007)), 2)
        out.append(("Pauldron" + s, f, vx, "upperarm." + s, "armor"))
        f = Field("UpperArm" + s)
        f.add(RoundCone(sh, el, 0.15, 0.13))
        f.add(Sphere(el, 0.15), k=0.02)
        for i in range(3):
            f.paint(RoundBox(sh + (el - sh) * (0.35 + 0.15 * i), (0.26, 0.26, 0.01)), 2)
        out.append(("UpperArm" + s, f, vx, "upperarm." + s, "frame"))
        f = Field("Forearm" + s)
        f.add(RoundCone(el + (wr - el) * 0.1, wr, 0.19, 0.22))
        f.add(Ellipsoid(el + (wr - el) * 0.6 + v3((sx * 0.05, 0, 0)), (0.24, 0.24, 0.26)), k=0.08)
        rivets(f, [el + (wr - el) * 0.45 + v3((sx * 0.22, dy, 0)) for dy in (-0.1, 0.0, 0.1)], 0.02)
        f.paint(RoundBox(el + (wr - el) * 0.25, (0.6, 0.6, 0.04)), 1)
        f.paint(RoundBox(el + (wr - el) * 0.8, (0.6, 0.6, 0.01)), 2)
        out.append(("Forearm" + s, f, vx, "forearm." + s, "armor"))
        f = Field("Fist" + s)                                                            # a great riveted fist
        f.add(RoundBox(wr + v3((0, -0.06, -0.2)), (0.2, 0.2, 0.18), 0.09))
        for dx in (-0.12, -0.04, 0.04, 0.12):
            f.add(Sphere(wr + v3((dx, -0.24, -0.25)), 0.065), k=0.025)
        f.add(RoundCone(wr + v3((-sx * 0.16, -0.14, -0.12)), wr + v3((-sx * 0.2, -0.24, -0.24)), 0.06, 0.05), k=0.02)
        rivets(f, [wr + v3((dx, -0.08, -0.03)) for dx in (-0.12, 0.0, 0.12)], 0.018)
        f.paint(RoundBox(wr + v3((0, -0.06, -0.06)), (0.4, 0.4, 0.01)), 2)
        out.append(("Fist" + s, f, vx, "hand." + s, "frame"))
        hp, kn, an, to = (v3(J[k + "_" + s]) for k in ("hip", "knee", "ankle", "toe"))
        f = Field("Thigh" + s)
        f.add(RoundCone(hp, kn, 0.17, 0.15))
        f.add(RoundBox(hp + (kn - hp) * 0.45 + v3((sx * 0.04, -0.11, 0)), (0.15, 0.05, 0.16), 0.04,
                       R=rot_from_axes(y_axis=(0, -1, 0), z_axis=(kn - hp))), k=0.04)
        out.append(("Thigh" + s, f, vx, "thigh." + s, "frame"))
        f = Field("Knee" + s)
        f.add(Ellipsoid(kn + v3((0, -0.12, 0.02)), (0.17, 0.1, 0.16)))
        rivets(f, [kn + v3((dx, -0.215, 0.02)) for dx in (-0.08, 0.08)], 0.018)
        f.paint(RoundBox(kn + v3((0, -0.22, 0.1)), (0.22, 0.12, 0.04)), 1)
        out.append(("Knee" + s, f, vs, "shin." + s, "armor"))
        f = Field("Shin" + s)
        f.add(RoundCone(kn + (an - kn) * 0.15, an + (kn - an) * 0.12, 0.21, 0.19))
        f.add(Ellipsoid(kn + (an - kn) * 0.5 + v3((0, -0.02, 0)), (0.22, 0.22, 0.24)), k=0.06)
        f.paint(RoundBox(kn + (an - kn) * 0.72, (0.6, 0.6, 0.01)), 2)
        out.append(("Shin" + s, f, vx, "shin." + s, "armor"))
        f = Field("Foot" + s)
        f.add(RoundBox(an + v3((0, -0.15, -0.13)), (0.25, 0.36, 0.1), 0.07))
        for dx in (-0.14, 0.0, 0.14):
            f.add(Ellipsoid(an + v3((dx, -0.44, -0.14)), (0.09, 0.11, 0.09)), k=0.03)
        f.add(Sphere(an, 0.15), k=0.04)
        f.paint(RoundBox(an + v3((0, -0.15, -0.22)), (0.3, 0.5, 0.025)), 2)
        out.append(("Foot" + s, f, vx, "foot." + s, "frame"))
    return out


def _legs(arm, R, t):
    """The walk's legs (it keeps marching through a one-shot, so its feet stay planted at the same pace)."""
    aims = {}
    for side, off in (("L", 0.0), ("R", 0.5)):
        ph = (t + off) % 1.0
        a0 = Vector(J["ankle_" + side])
        if ph < 0.5:
            kk = ph / 0.5
            y, z = -WALK_STEP / 2 + WALK_STEP * kk, 0.0
        else:
            kk = (ph - 0.5) / 0.5
            e = 0.5 - 0.5 * math.cos(math.pi * kk)
            y = WALK_STEP / 2 - WALK_STEP * e
            z = 0.12 * (math.sin(math.pi * kk) ** 2.5)
        aims.update(R.leg(arm, side, a0 + Vector((0, y, z)), Vector((0, -1, 0)), Vector((0, -1, 0.05))))
    return aims


def summon(arm, frames=WALK_FRAMES):
    """It rears up, arms flung wide, head thrown back, its furnace blazing (the fire swells) while Ironclads march out."""
    import robot_anim as R
    P = Poser(arm)
    act = R.new_action(arm, "Summon")
    for f in range(frames + 1):
        t = f / frames
        k = math.sin(math.pi * min(1.0, t / 0.85)) ** 0.7
        aims = _legs(arm, R, t)
        aims["spine"] = (Vector((0, 0.22 * k, 1.0)), 0.0)
        aims["head"] = Vector((0, -0.2 + 0.7 * k, 1.0))
        for side, sx in (("L", 1), ("R", -1)):
            up = Vector((sx * (0.4 + 0.6 * k), -0.15 - 0.2 * k, -1.0 + 1.5 * k)).normalized()
            fo = Vector((sx * (0.2 + 0.4 * k), -0.4, -1.0 + 1.7 * k)).normalized()
            aims["upperarm." + side] = up
            aims["forearm." + side] = fo
            aims["hand." + side] = fo
        aims["furnace"] = Vector((0, -1, 0))
        c = math.cos(4 * math.pi * t)
        ch, _ = P.solve(aims, root_off=Vector((0, 0, -0.05 * c + 0.05)), root_rot=Quaternion(Vector((1, 0, 0)), -0.04),
                        scales={"furnace": 1.0 + 0.4 * k})
        P.key(ch, f)
    R.finish_action(arm, act, frames, False)


EMP_HIT = 9            # its fists strike the ground (game.gd: the pulse is already out; the clip catches up)


def emp(arm, frames=36):
    """Both fists raised high (0-6) and slammed into the ground before it (EMP_HIT), a shudder, and it rises."""
    import robot_anim as R
    P = Poser(arm)
    act = R.new_action(arm, "Emp")
    for f in range(frames + 1):
        t = f / frames
        if f <= 6:
            k_up, k_dn = math.sin(0.5 * math.pi * f / 6.0), 0.0
        elif f <= EMP_HIT:
            k_up, k_dn = 1.0 - (f - 6) / float(EMP_HIT - 6), ((f - 6) / float(EMP_HIT - 6)) ** 2
        elif f <= 22:
            k_up, k_dn = 0.0, 1.0
        else:
            k_up, k_dn = 0.0, 1.0 - math.sin(0.5 * math.pi * (f - 22) / float(frames - 22))
        aims = _legs(arm, R, t * 0.75)
        bend = 0.45 * k_dn - 0.15 * k_up
        aims["spine"] = (Vector((0, -bend, 1.0)), 0.0)
        aims["head"] = Vector((0, -0.2 - 0.3 * k_dn + 0.4 * k_up, 1.0))
        shudder = 0.02 * math.sin(f * 2.2) if EMP_HIT <= f <= 18 else 0.0
        for side, sx in (("L", 1), ("R", -1)):
            up = Vector((sx * 0.3, -0.3 - 0.6 * k_dn - 0.1 * k_up, -1.0 + 2.0 * k_up + 0.3 * k_dn)).normalized()
            fo = Vector((sx * 0.1, -0.5 - 0.6 * k_dn, -1.0 + 2.2 * k_up - 0.4 * k_dn)).normalized()
            aims["upperarm." + side] = up
            aims["forearm." + side] = fo
            aims["hand." + side] = fo
        aims["furnace"] = Vector((0, -1, 0))
        ch, _ = P.solve(aims, root_off=Vector((0, -0.12 * k_dn, -0.22 * k_dn + 0.05 * k_up + shudder)),
                        root_rot=Quaternion(Vector((1, 0, 0)), -0.04 - 0.1 * k_dn), scales={"furnace": 1.0 + 0.25 * k_dn})
        P.key(ch, f)
    R.finish_action(arm, act, frames, False)


def clips(arm):
    ra.walk(arm, J, "Walk", frames=WALK_FRAMES, step=WALK_STEP, lift=0.12, bob=0.05, sway=0.06, arm_swing=0.2, lean=0.08,
            twist=0.12, heavy=1.6)
    summon(arm)
    emp(arm)
