"""Prime Walker, HQ: the Stone Age boss. A towering war mech: an armoured chest round a great red reactor behind a cage,
a horned helmet with a T-shaped visor and a crest of glowing spikes, wheel-like shoulder joints ringed with red lights
under striped pauldrons, piston arms with three-clawed hands, three exhaust stacks on its back, heavy legs with hydraulic
pistons and clawed feet. Walk (a slow, heavy stomp) and Summon (it rears up and raises its claws while walkers pour out).
Faces -Y, Z up, model_scale 1.0.
"""
import math
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser

ROOT_NAME = "PrimeWalker"
GLB_NAME = "prime_walker"
TEX_PREFIX = "prime_walker"
WALK_STEP = 0.7
WALK_FRAMES = 48

ORANGE = (1.0, 0.45, 0.08)
SEAM = (0.2, 0.2, 0.22)
BLACK = (0.08, 0.08, 0.09)
CRIMSON = (0.62, 0.08, 0.06)


def mirror(p):
    return (-p[0], p[1], p[2])


J = {
    "hip_L": (0.36, 0.02, 1.42), "knee_L": (0.42, -0.14, 0.84), "ankle_L": (0.42, 0.05, 0.24), "toe_L": (0.42, -0.3, 0.1),
    "shoulder_L": (0.74, 0.02, 2.28), "elbow_L": (0.86, 0.1, 1.72), "wrist_L": (0.9, -0.1, 1.22), "hand_L": (0.9, -0.16, 0.98),
}
for k in list(J):
    if k.endswith("_L"):
        J[k[:-2] + "_R"] = mirror(J[k])

BONES = [
    ("root", (0, 0, 1.42), (0, 0, 1.6), None),
    ("spine", (0, 0.02, 1.6), (0, 0.0, 2.5), "root"),
    ("head", (0, -0.08, 2.5), (0, -0.1, 2.85), "spine"),
    ("core", (0, -0.3, 2.02), (0, -0.5, 2.02), "spine"),
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
    "armor": ("armor", dict(name="RB_PrimeArmor", base=(0.9, 0.9, 0.87), labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, BLACK, 0.4), (4, CRIMSON, 0.35)],
                            seams=[2], wear=1.3, scale=2.0)),
    "frame": ("gunmetal", dict(name="RB_PrimeFrame", base=(0.2, 0.21, 0.25), labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6), (4, CRIMSON, 0.35)],
                               seams=[2], scale=2.0)),
    "chrome": ("chrome", dict(name="RB_PrimeChrome")),
    "socket": ("lens_socket", dict(name="RB_PrimeSocket")),
    "glow": ("glow", dict(name="RB_PrimeGlow", col=(1.0, 0.25, 0.1))),
}
GLOW_RED = (1.0, 0.2, 0.07)
GLOW = {"Core": (GLOW_RED, 1.25, 0.5), "Visor": (GLOW_RED, 1.35, 0.5), "Crest": (GLOW_RED, 1.2, 0.5),
        "ShoulderLights": (GLOW_RED, 1.3, 0.5), "Exhaust": ((1.0, 0.55, 0.15), 1.3, 0.5)}
LOW_TARGETS = {"Torso": 1400, "Cage": 300, "Core": 120, "Back": 500, "Exhaust": 60, "Pelvis": 360, "Abdomen": 260,
               "Head": 600, "Visor": 70, "Crest": 220, "Horns": 200, "ShoulderLights": 160}
for s in "LR":
    LOW_TARGETS.update({"Wheel" + s: 360, "Pauldron" + s: 420, "UpperArm" + s: 240, "Forearm" + s: 360, "Hand" + s: 380,
                        "Thigh" + s: 300, "Piston" + s: 120, "Knee" + s: 120, "Shin" + s: 380, "Foot" + s: 380})
FACE_Y = rot_from_axes(z_axis=(0, -1, 0))
AX_X = rot_from_axes(z_axis=(1, 0, 0))


def hazard(f, centre, half, n=6, angle=0.6, labs=(1, 3)):
    c = v3(centre)
    R = rot_from_axes(x_axis=(math.cos(angle), 0, math.sin(angle)), y_axis=(0, 1, 0))
    for i in range(n):
        off = ((i + 0.5) / n - 0.5) * 2 * half[0]
        f.paint(RoundBox(c + v3((off, 0, 0)), (half[0] / n, half[1], half[2] * 2.2), 0.0, R=R), labs[i % 2])


def parts(fine=False):
    vx = 0.008 if fine else 0.014
    vs = 0.006 if fine else 0.011
    out = []
    # ---- chest: broad and armoured, a reactor in a caged socket, crimson chevron, seams
    f = Field("Torso")
    f.add(RoundBox((0, 0.04, 2.05), (0.46, 0.32, 0.36), 0.2))
    f.add(Ellipsoid((0, -0.02, 2.25), (0.56, 0.38, 0.26)), k=0.1)
    f.add(RoundBox((0, 0.04, 1.72), (0.3, 0.24, 0.12), 0.1), k=0.1)
    f.sub(Sphere((0, -0.4, 2.02), 0.22), k=0.03)
    for sx in (-1, 1):
        f.paint(RoundBox((sx * 0.22, -0.36, 2.3), (0.2, 0.1, 0.035), 0.0, R=rot_from_axes(x_axis=(1, 0, -sx * 0.55), y_axis=(0, 1, 0))), 4)
        f.paint(RoundBox((sx * 0.34, -0.3, 1.9), (0.08, 0.1, 0.12), 0.03), 2)
    f.paint(RoundBox((0, 0.04, 1.8), (0.7, 0.6, 0.006)), 2)
    f.paint(RoundBox((0, 0.04, 2.47), (0.7, 0.6, 0.03)), 1)
    out.append(("Torso", f, vx, "spine", "armor"))
    f = Field("Cage")
    f.add(Torus((0, -0.37, 2.02), 0.215, 0.04, R=FACE_Y))
    for i in range(8):
        a = i * math.pi / 4
        f.add(Sphere((0.215 * math.cos(a), -0.41, 2.02 + 0.215 * math.sin(a)), 0.024), k=0.008)
    for dx in (-0.09, 0.0, 0.09):
        f.add(RoundCone((dx, -0.42, 1.83), (dx, -0.42, 2.21), 0.018), k=0.008)
    out.append(("Cage", f, vs, "spine", "frame"))
    f = Field("Core")
    f.add(Ellipsoid((0, -0.34, 2.02), (0.19, 0.1, 0.19)))
    out.append(("Core", f, vs, "core", "glow"))
    f = Field("Abdomen")
    for i, (z, r) in enumerate(((1.52, 0.27), (1.6, 0.3))):
        f.add(Cylinder((0, 0.04, z), r, 0.07, rr=0.025), k=0.006)
    out.append(("Abdomen", f, vx, "root", "frame"))
    f = Field("Back")
    f.add(RoundBox((0, 0.4, 2.1), (0.34, 0.12, 0.26), 0.08))
    for dx, h in ((-0.2, 0.5), (0.0, 0.62), (0.2, 0.5)):
        f.add(Cylinder((dx, 0.46, 2.36 + h * 0.3), 0.075, h, rr=0.02), k=0.02)
        f.add(Torus((dx, 0.46, 2.36 + h * 0.8), 0.075, 0.02), k=0.006)
        f.sub(Cylinder((dx, 0.46, 2.36 + h * 0.85), 0.052, 0.1), k=0.006)
    for i in range(6):
        f.paint(RoundBox((0, 0.53, 1.95 + i * 0.05), (0.26, 0.015, 0.01), 0.005), 2)
    out.append(("Back", f, vx, "spine", "frame"))
    f = Field("Exhaust")
    for dx, h in ((-0.2, 0.5), (0.0, 0.62), (0.2, 0.5)):
        f.add(Cylinder((dx, 0.46, 2.36 + h * 0.8 - 0.005), 0.052, 0.016, rr=0.005))
    out.append(("Exhaust", f, vs, "spine", "glow"))
    f = Field("Pelvis")
    f.add(RoundBox((0, 0.04, 1.42), (0.4, 0.26, 0.13), 0.08))
    for sx in (-1, 1):
        f.add(Sphere((sx * 0.36, 0.02, 1.42), 0.14), k=0.02)
    hazard(f, (0, -0.2, 1.42), (0.38, 0.1, 0.07), n=10)
    out.append(("Pelvis", f, vx, "root", "frame"))
    # ---- head: horned helm, T visor, crest of glowing spikes
    f = Field("Head")
    f.add(RoundBox((0, -0.08, 2.67), (0.235, 0.22, 0.185), 0.11))
    f.add(RoundBox((0, -0.26, 2.6), (0.17, 0.07, 0.11), 0.055), k=0.045)          # jaw guard
    f.sub(RoundBox((0, -0.33, 2.69), (0.17, 0.07, 0.035), 0.022), k=0.01)         # visor bar
    f.sub(RoundBox((0, -0.33, 2.6), (0.04, 0.07, 0.08), 0.022), k=0.01)           # visor stem
    f.paint(RoundBox((0, -0.1, 2.83), (0.08, 0.3, 0.05)), 4)
    out.append(("Head", f, vs, "head", "armor"))
    f = Field("Visor")
    f.add(RoundBox((0, -0.298, 2.69), (0.16, 0.032, 0.03), 0.022))
    f.add(RoundBox((0, -0.298, 2.61), (0.032, 0.032, 0.07), 0.022), k=0.01)
    out.append(("Visor", f, vs, "head", "glow"))
    f = Field("Horns")
    for sx in (-1, 1):
        f.add(RoundCone((sx * 0.21, -0.1, 2.74), (sx * 0.42, -0.22, 2.98), 0.07, 0.02))
        f.add(Sphere((sx * 0.22, -0.1, 2.73), 0.085), k=0.02)
    out.append(("Horns", f, vs, "head", "frame"))
    f = Field("Crest")
    for i, (y, h) in enumerate(((-0.2, 0.16), (-0.1, 0.24), (0.0, 0.28), (0.1, 0.24), (0.19, 0.16))):
        f.add(RoundCone((0, -0.08 + y, 2.83), (0, -0.04 + y * 1.2, 2.83 + h), 0.045, 0.006), k=0.01)
    out.append(("Crest", f, vs, "head", "glow"))
    f_lights = Field("ShoulderLights")
    for s, sx in (("L", 1), ("R", -1)):
        sh, el, wr, hd = (v3(J[k + "_" + s]) for k in ("shoulder", "elbow", "wrist", "hand"))
        f = Field("Wheel" + s)                                             # wheel-like shoulder joint
        wc = sh + v3((-sx * 0.04, 0, 0.0))
        f.add(Cylinder(wc, 0.26, 0.2, rr=0.05, R=AX_X))
        f.sub(Cylinder(wc + v3((sx * 0.1, 0, 0)), 0.17, 0.06, rr=0.02, R=AX_X), k=0.01)
        f.add(Cylinder(wc + v3((sx * 0.08, 0, 0)), 0.09, 0.06, rr=0.02, R=AX_X), k=0.01)
        for i in range(8):
            a = i * math.pi / 4
            f_lights.add(Sphere(wc + v3((sx * 0.1, 0.215 * math.cos(a), 0.215 * math.sin(a))), 0.028))
        out.append(("Wheel" + s, f, vx, "spine", "frame"))
        f = Field("Pauldron" + s)
        f.add(Ellipsoid(sh + v3((sx * 0.05, 0.0, 0.2)), (0.32, 0.3, 0.18)))
        f.add(Torus(sh + v3((sx * 0.05, 0.0, 0.12)), 0.28, 0.035), k=0.02)
        f.sub(Ellipsoid(sh + v3((sx * 0.05, 0.0, 0.04)), (0.25, 0.24, 0.14)), k=0.015)
        hazard(f, sh + v3((sx * 0.05, 0.0, 0.36)), (0.32, 0.4, 0.05), n=8, angle=0.0)
        f.paint(RoundBox(sh + v3((sx * 0.05, 0, 0.22)), (0.5, 0.5, 0.008)), 2)
        out.append(("Pauldron" + s, f, vx, "upperarm." + s, "armor"))
        f = Field("UpperArm" + s)
        f.add(RoundCone(sh + (el - sh) * 0.15, el, 0.1, 0.085))
        f.add(Sphere(el, 0.12), k=0.02)
        f.add(RoundCone(sh + (el - sh) * 0.25 + v3((0, -0.09, 0)), sh + (el - sh) * 0.85 + v3((0, -0.09, 0)), 0.03), k=0.01)
        out.append(("UpperArm" + s, f, vx, "upperarm." + s, "frame"))
        f = Field("Forearm" + s)
        f.add(RoundCone(el + (wr - el) * 0.1, wr, 0.15, 0.13))
        f.add(Ellipsoid(el + (wr - el) * 0.5 + v3((sx * 0.05, 0, 0)), (0.17, 0.16, 0.22)), k=0.05)
        f.paint(RoundBox(el + (wr - el) * 0.22, (0.4, 0.4, 0.035)), 4)
        f.paint(RoundBox(el + (wr - el) * 0.78, (0.4, 0.4, 0.008)), 2)
        out.append(("Forearm" + s, f, vx, "forearm." + s, "armor"))
        f = Field("Hand" + s)                                              # three great claws
        f.add(RoundBox(wr + v3((0, -0.03, -0.1)), (0.12, 0.1, 0.1), 0.06))
        for i, a in enumerate((-0.6, 0.0, 0.6)):
            base = wr + v3((0.09 * math.sin(a), -0.08, -0.17))
            mid = base + v3((0.05 * math.sin(a), -0.08, -0.12))
            tip = mid + v3((0.02 * math.sin(a), 0.02, -0.14))
            f.add(RoundCone(base, mid, 0.04, 0.03), k=0.012)
            f.add(RoundCone(mid, tip, 0.03, 0.008), k=0.01)
        out.append(("Hand" + s, f, vs, "hand." + s, "frame"))
        hp, kn, an, to = (v3(J[k + "_" + s]) for k in ("hip", "knee", "ankle", "toe"))
        f = Field("Thigh" + s)
        f.add(RoundCone(hp, kn, 0.15, 0.12))
        f.add(RoundBox(hp + (kn - hp) * 0.45 + v3((sx * 0.04, -0.08, 0)), (0.13, 0.04, 0.2), 0.04,
                       R=rot_from_axes(y_axis=(0, -1, 0), z_axis=(kn - hp))), k=0.03)
        f.paint(RoundBox(hp + (kn - hp) * 0.45 + v3((0, -0.14, 0)), (0.2, 0.06, 0.03), 0.0,
                         R=rot_from_axes(y_axis=(0, -1, 0), z_axis=(kn - hp))), 1)
        out.append(("Thigh" + s, f, vx, "thigh." + s, "frame"))
        f = Field("Knee" + s)
        f.add(Ellipsoid(kn + v3((0, -0.1, 0.02)), (0.14, 0.09, 0.13)))
        f.add(RoundCone(kn + v3((0, -0.12, 0.08)), kn + v3((0, -0.2, 0.2)), 0.04, 0.01), k=0.02)   # knee spike
        out.append(("Knee" + s, f, vs, "shin." + s, "armor"))
        f = Field("Shin" + s)
        f.add(RoundCone(kn + (an - kn) * 0.12, an + (kn - an) * 0.12, 0.17, 0.14))
        f.add(Ellipsoid(kn + (an - kn) * 0.45 + v3((0, 0.02, 0)), (0.18, 0.17, 0.25)), k=0.05)
        hazard(f, kn + (an - kn) * 0.2 + v3((0, -0.12, 0)), (0.17, 0.12, 0.05), n=6, angle=0.0)
        f.paint(RoundBox(kn + (an - kn) * 0.68, (0.4, 0.4, 0.008)), 2)
        out.append(("Shin" + s, f, vx, "shin." + s, "armor"))
        f = Field("Piston" + s)                                            # hydraulic ram down the back of the shin
        f.add(RoundCone(kn + v3((0, 0.17, -0.02)), an + v3((0, 0.17, 0.12)), 0.035), k=0.01)
        out.append(("Piston" + s, f, vs, "shin." + s, "chrome"))
        f = Field("Foot" + s)
        f.add(RoundBox(an + v3((0, -0.1, -0.13)), (0.2, 0.28, 0.1), 0.07))
        for dx in (-0.12, 0.0, 0.12):
            f.add(RoundCone(an + v3((dx, -0.3, -0.15)), an + v3((dx * 1.2, -0.48, -0.2)), 0.07, 0.025), k=0.03)
        f.add(RoundCone(an + v3((0, 0.12, -0.15)), an + v3((0, 0.28, -0.2)), 0.06, 0.02), k=0.03)
        f.add(Sphere(an, 0.13), k=0.03)
        out.append(("Foot" + s, f, vx, "foot." + s, "frame"))
    out.append(("ShoulderLights", f_lights, vs, "spine", "glow"))
    return out


def clips(arm):
    ra.walk(arm, J, "Walk", frames=WALK_FRAMES, step=WALK_STEP, lift=0.12, bob=0.05, sway=0.06, arm_swing=0.22, lean=0.08,
            twist=0.12, heavy=1.5)
    summon(arm)


def summon(arm, frames=WALK_FRAMES):
    """The walk's legs (it keeps marching, so its feet stay planted at the same pace) with the upper body rearing up:
    claws raised high, head thrown back, the reactor swelling."""
    import robot_anim as R
    P = Poser(arm)
    act = R.new_action(arm, "Summon")
    for f in range(frames + 1):
        t = f / frames
        k = math.sin(math.pi * min(1.0, t / 0.85)) ** 0.7          # rear up and come back down
        aims = {}
        # legs exactly as in the walk
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
        aims["spine"] = (Vector((0, 0.25 * k, 1.0)), 0.0)
        aims["head"] = Vector((0, -0.2 + 0.8 * k, 1.0))
        for side, sx in (("L", 1), ("R", -1)):
            up = Vector((sx * (0.3 + 0.5 * k), -0.2 - 0.3 * k, -1.0 + 1.9 * k)).normalized()
            fo = Vector((sx * 0.25 * k, -0.3 - 0.2 * k, -1.0 + 2.1 * k)).normalized()
            aims["upperarm." + side] = up
            aims["forearm." + side] = fo
            aims["hand." + side] = fo
        aims["core"] = Vector((0, -1, 0))
        c = math.cos(4 * math.pi * t)
        ch, _ = P.solve(aims, root_off=Vector((0, 0, -0.05 * c + 0.05)), root_rot=Quaternion(Vector((1, 0, 0)), -0.04),
                        scales={"core": 1.0 + 0.35 * k})
        P.key(ch, f)
    R.finish_action(arm, act, frames, False)
