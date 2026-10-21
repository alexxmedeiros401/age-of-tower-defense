"""Cloaker, HQ: the Medieval Age's infiltrator, the robot that walks unseen. A lean, stooping machine in a hooded cloak:
a deep cowl drawn forward over its head, only a narrow violet visor slit glowing in the shadow inside, its point down
its back; a short mantle over its shoulders cut in points, and a long cloak from its shoulders to its knees, open in
front, its hem ragged and edged in violet, fastened at its throat by a round clasp with a cyan cloaking gem; a slim armoured body under it, thin jointed arms, a long stiletto
blade in its right hand with a violet edge, a hooked claw for a left hand; thin greaves and long pointed sabatons.
Run: a quick, low prowl, the blade held forward, the cloak's panels swinging behind it (bones of their own). In game
it turns to a see-through cyan ghost while it is cloaked (game.gd's ghost materials). Faces -Y, Z up, model_scale 0.9.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, rot_from_axes, v3, norm, euler, F
from caveman import Inter, Shell
import robot_anim as ra
from mathutils import Vector

ROOT_NAME = "Cloaker"
GLB_NAME = "cloaker"
TEX_PREFIX = "cloaker"
WALK_STEP = 0.5
WALK_FRAMES = 20

SLATE = (0.24, 0.26, 0.3)
VIOLET = (0.5, 0.24, 0.8)
SEAM = (0.08, 0.08, 0.1)
DARK = (0.1, 0.1, 0.12)


def mirror(p):
    return (-p[0], p[1], p[2])


J = {
    "hip_L": (0.1, 0.03, 0.64), "knee_L": (0.12, -0.05, 0.37), "ankle_L": (0.12, 0.04, 0.1), "toe_L": (0.12, -0.12, 0.03),
    "shoulder_L": (0.21, 0.04, 1.13), "elbow_L": (0.29, 0.08, 0.88), "wrist_L": (0.31, -0.02, 0.66), "hand_L": (0.31, -0.05, 0.56),
}
for k in list(J):
    if k.endswith("_L"):
        J[k[:-2] + "_R"] = mirror(J[k])

CLOAK_TOP = {"L": (0.15, 0.12, 1.13), "B": (0.0, 0.17, 1.13), "R": (-0.15, 0.12, 1.13)}
CLOAK_LEN = 0.6
CAPE_C = (0.0, 0.03)                    # the cape's axis (x, y): it hangs round it in a cone
CAPE_SPAN = 1.5                         # its half-angle round from the back (rad): open in front, clear of the arms
CAPE_CUTS = (0.5, -0.5)                 # where it is cut into its three sections (angle from the back; + = its left)

BONES = [
    ("root", (0, 0.02, 0.64), (0, 0.02, 0.74), None),
    ("spine", (0, 0.03, 0.74), (0, 0.04, 1.16), "root"),
    ("head", (0, 0.0, 1.18), (0, -0.02, 1.4), "spine"),
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
for k, top in CLOAK_TOP.items():
    BONES.append(("cloak." + k, top, (top[0], top[1] + 0.06, top[2] - CLOAK_LEN), "spine"))

MATS = {
    "armor": ("armor", dict(name="RB_CloakerArmor", base=SLATE, metal=(0.5, 0.52, 0.56), labels=[(1, VIOLET, 0.35), (2, SEAM, 0.6),
                                                                                       (3, DARK, 0.5)], seams=[2], wear=0.4)),
    "cloak": ("gunmetal", dict(name="RB_CloakerCloak", base=(0.14, 0.15, 0.18), edge=(0.42, 0.44, 0.5),
                               labels=[(1, VIOLET, 0.35), (2, (0.06, 0.06, 0.07), 0.6)], seams=[2])),
    "frame": ("gunmetal", dict(name="RB_CloakerFrame", labels=[(1, VIOLET, 0.35), (2, (0.08, 0.08, 0.09), 0.6)], seams=[2])),
    "chrome": ("chrome", dict(name="RB_CloakerBlade")),
    "glow": ("glow", dict(name="RB_CloakerGlow", col=(0.75, 0.35, 1.0))),
}
GLOW = {"Visor": ((0.78, 0.4, 1.0), 1.5, 0.5), "Gem": ((0.3, 0.9, 1.0), 1.4, 0.5), "Edge": ((0.75, 0.35, 1.0), 1.2, 0.6)}

LOW_TARGETS = {"Torso": 420, "Pelvis": 160, "Hood": 600, "Mantle": 420, "Face": 120, "Visor": 30, "Clasp": 140, "Gem": 40,
               "CloakL": 300, "CloakB": 300, "CloakR": 300, "Blade": 160, "Edge": 40}
for s in "LR":
    LOW_TARGETS.update({"UpperArm" + s: 110, "Forearm" + s: 150, "Hand" + s: 170, "Thigh" + s: 110, "Shin" + s: 150,
                        "Foot" + s: 150})


def _cape_angle(P):
    return np.arctan2(P[:, 0] - F(CAPE_C[0]), P[:, 1] - F(CAPE_C[1]))          # 0 at its back, + round to its left


def cape_hem(a):
    """The cape's ragged hem: a sawtooth of points with a few deeper rents."""
    saw = np.abs(np.mod(a * F(7.0) + F(0.3), F(1.0)) - F(0.5)) * F(2.0)
    rent = np.clip(F(1.0) - np.abs(np.mod(a * F(2.3) + F(0.9), F(1.0)) - F(0.5)) * F(14.0), 0, 1)
    return F(0.5) + F(0.06) * saw + F(0.07) * rent


def cape_sd(P, lo_a, hi_a):
    """The cloak hanging from its shoulders in a widening cone round its back, open in front, cut to the section
    between angles lo_a and hi_a."""
    x, y, z = P[:, 0] - F(CAPE_C[0]), P[:, 1] - F(CAPE_C[1]), P[:, 2]
    r = np.sqrt(x * x + y * y)
    a = _cape_angle(P)
    t = np.clip((F(1.13) - z) / F(0.6), 0, 1)
    R = F(0.19) + F(0.2) * t + F(0.006) * np.sin(a * F(11) + z * F(6))              # (a few folds)
    shell = np.abs(r - R) - F(0.011)
    side = np.maximum(F(lo_a) - a, a - F(hi_a)) * R
    top = z - (F(1.15) + F(0.03) * np.cos(a))
    return np.maximum(np.maximum(shell, side), np.maximum(top, cape_hem(a) - z))


def parts(fine=False):
    vx = 0.0045 if fine else 0.008
    vs = 0.003 if fine else 0.006
    out = []
    # ---- the body: a slim chest and waist, stooping a little
    f = Field("Torso")
    f.add(Ellipsoid((0, 0.04, 1.0), (0.15, 0.11, 0.16)))
    f.add(Ellipsoid((0, 0.03, 0.82), (0.11, 0.085, 0.12)), k=0.05)
    f.add(RoundBox((0, -0.07, 0.98), (0.1, 0.03, 0.1), 0.03), k=0.03)                       # a breastplate ridge
    f.paint(RoundBox((0, -0.11, 0.98), (0.012, 0.05, 0.12)), 1)
    f.paint(RoundBox((0, 0.04, 0.9), (0.3, 0.3, 0.004)), 2)
    out.append(("Torso", f, vx, "spine", "armor"))
    f = Field("Pelvis")
    f.add(RoundBox((0, 0.03, 0.68), (0.12, 0.08, 0.06), 0.04))
    for sx in (-1, 1):
        f.add(Sphere((sx * 0.1, 0.03, 0.64), 0.05), k=0.015)
    out.append(("Pelvis", f, vx, "root", "frame"))
    # ---- the hood: a deep cowl drawn forward over the face, its opening turned down and in shadow, its point down
    # the back; the visor slit glows in the shadow
    f = Field("Hood")
    hc = v3((0, 0.0, 1.28))
    cowl = Ellipsoid(hc + v3((0, 0.02, 0.012)), (0.135, 0.16, 0.168))
    open_n = norm(v3((0, -1, -0.55)))
    open_p = hc + v3((0, -0.085, 0.0))
    f.add(Inter(Shell(cowl, 0.0, 0.024), Plane(open_p, open_n), 0.008))
    f.add(Inter(Ellipsoid(hc + v3((0, -0.02, 0.11)), (0.08, 0.13, 0.06)), Plane(open_p, open_n), 0.01), k=0.02)   # the peak over its brow
    f.add(RoundCone(hc + v3((0, 0.12, 0.05)), hc + v3((0, 0.2, -0.16)), 0.06, 0.012), k=0.04)          # its point down the back
    f.paint(Inter(Shell(cowl, 0.0, 0.04), Func(lambda P: np.abs((P - open_p.astype(F)) @ open_n.astype(F) + F(0.014)) - F(0.014),
                                                hc - 0.3, hc + 0.3), 0.0), 1)                     # a violet hem round its opening
    out.append(("Hood", f, vx, "head", "cloak"))
    f = Field("Mantle")                                     # the short cape over its shoulders, its hem cut in points
    mb = Ellipsoid((0, 0.04, 1.1), (0.27, 0.18, 0.15))
    def mantle_keep(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.04)))
        saw = np.abs(np.mod(a * F(9.0 / (2 * math.pi)) * F(1.0) + F(0.5), F(1.0)) - F(0.5)) * F(2.0)
        hem = F(0.99) + F(0.07) * saw
        return np.maximum(hem - P[:, 2], P[:, 2] - F(1.2))
    f.add(Inter(Shell(mb, 0.0, 0.02), Func(mantle_keep, (-0.5, -0.4, 0.8), (0.5, 0.4, 1.4)), 0.006))
    f.add(Ellipsoid((0, 0.03, 1.19), (0.13, 0.12, 0.06)), k=0.04)                                      # the hood's fold at its neck
    f.paint(Func(lambda P: P[:, 2] - (F(0.99) + F(0.07) * np.abs(np.mod(np.arctan2(P[:, 0], -(P[:, 1] - F(0.04))) * F(9.0 / (2 * math.pi)) + F(0.5), F(1.0)) - F(0.5)) * F(2.0) + F(0.025)),
                 (-0.5, -0.4, 0.8), (0.5, 0.4, 1.4)), 1)                                             # violet along its points
    out.append(("Mantle", f, vx, "spine", "cloak"))
    f = Field("Face")
    f.add(Ellipsoid(hc + v3((0, 0.01, -0.01)), (0.085, 0.1, 0.11)))
    f.add(RoundBox(hc + v3((0, -0.07, -0.05)), (0.05, 0.03, 0.05), 0.025), k=0.02)
    f.sub(RoundBox(hc + v3((0, -0.1, 0.005)), (0.06, 0.03, 0.009), 0.006), k=0.004)
    f.paint(RoundBox(hc + v3((0, -0.1, -0.06)), (0.2, 0.2, 0.004)), 2)
    out.append(("Face", f, vs, "head", "frame"))
    f = Field("Visor")
    f.add(RoundBox(hc + v3((0, -0.088, 0.005)), (0.055, 0.008, 0.008), 0.006))
    out.append(("Visor", f, vs, "head", "glow"))
    # ---- the clasp at its throat and the cloaking gem
    f = Field("Clasp")
    cc = v3((0, -0.1, 1.12))
    Rf = rot_from_axes(z_axis=(0, -1, 0.15))
    f.add(Cylinder(cc, 0.04, 0.012, rr=0.004, R=Rf))
    f.add(Torus(cc + v3((0, -0.006, 0)), 0.038, 0.007, R=Rf), k=0.003)
    for sx in (-1, 1):
        f.add(RoundCone(cc + v3((sx * 0.03, 0, 0.0)), v3((sx * 0.1, -0.12, 1.1)), 0.01, 0.008), k=0.006)   # its chains
    f.paint(Torus(cc + v3((0, -0.006, 0)), 0.038, 0.01, R=Rf), 1)
    out.append(("Clasp", f, vs, "spine", "frame"))
    f = Field("Gem")
    f.add(Ellipsoid(cc + v3((0, -0.014, 0)), (0.024, 0.012, 0.024), R=Rf))
    out.append(("Gem", f, vs, "spine", "glow"))
    # ---- the cloak: one draped cape cut into three sections (its left, its back, its right), each on its own bone
    lim = {"L": (CAPE_CUTS[0] - 0.03, CAPE_SPAN), "B": (CAPE_CUTS[1] - 0.03, CAPE_CUTS[0] + 0.03), "R": (-CAPE_SPAN, CAPE_CUTS[1] + 0.03)}
    for k in ("L", "B", "R"):
        lo_a, hi_a = lim[k]
        f = Field("Cloak" + k)
        f.add(Func(lambda P, lo_a=lo_a, hi_a=hi_a: cape_sd(P, lo_a, hi_a), (-0.5, -0.45, 0.38), (0.5, 0.5, 1.22)))
        f.paint(Func(lambda P: P[:, 2] - (cape_hem(_cape_angle(P)) + F(0.035)), (-0.5, -0.45, 0.38), (0.5, 0.5, 1.22)), 1)   # its violet hem
        f.paint(Func(lambda P: np.abs(P[:, 2] - F(0.8)) - F(0.004), (-0.5, -0.45, 0.38), (0.5, 0.5, 1.22)), 2)
        out.append(("Cloak" + k, f, vx, "cloak." + k, "cloak"))
    # ---- arms: thin, jointed; a stiletto in the right fist, a hooked claw for the left hand
    for s, sx in (("L", 1), ("R", -1)):
        sh, el, wr, hd = (v3(J[k + "_" + s]) for k in ("shoulder", "elbow", "wrist", "hand"))
        f = Field("UpperArm" + s)
        f.add(RoundCone(sh, el, 0.042, 0.034))
        f.add(Sphere(sh, 0.06), k=0.015)
        f.add(Sphere(el, 0.042), k=0.01)
        f.paint(RoundBox(sh + (el - sh) * 0.5, (0.1, 0.1, 0.004)), 2)
        out.append(("UpperArm" + s, f, vx, "upperarm." + s, "armor"))
        f = Field("Forearm" + s)
        f.add(RoundCone(el + (wr - el) * 0.08, wr, 0.04, 0.05))
        f.add(Ellipsoid(el + (wr - el) * 0.55 + v3((sx * 0.012, 0, 0)), (0.055, 0.055, 0.09)), k=0.03)
        f.paint(RoundBox(el + (wr - el) * 0.85, (0.12, 0.12, 0.012)), 1)
        out.append(("Forearm" + s, f, vx, "forearm." + s, "armor"))
        f = Field("Hand" + s)
        f.add(RoundBox(wr + v3((0, -0.01, -0.045)), (0.04, 0.035, 0.04), 0.02))
        if s == "R":                                                     # a fist round the stiletto's grip
            for dz in (-0.02, 0.0, 0.02):
                f.add(Sphere(wr + v3((0, -0.045, -0.06 + dz)), 0.018), k=0.008)
        else:                                                            # three hooked claws
            for dx in (-0.025, 0.0, 0.025):
                b = wr + v3((dx, -0.03, -0.08))
                f.add(RoundCone(b, b + v3((0, -0.03, -0.05)), 0.012, 0.008), k=0.006)
                f.add(RoundCone(b + v3((0, -0.03, -0.05)), b + v3((0, -0.01, -0.09)), 0.008, 0.003), k=0.004)
        out.append(("Hand" + s, f, vs, "hand." + s, "frame"))
        hp, kn, an, to = (v3(J[k + "_" + s]) for k in ("hip", "knee", "ankle", "toe"))
        f = Field("Thigh" + s)
        f.add(RoundCone(hp, kn, 0.05, 0.042))
        f.add(Sphere(kn, 0.045), k=0.01)
        out.append(("Thigh" + s, f, vx, "thigh." + s, "frame"))
        f = Field("Shin" + s)
        f.add(RoundCone(kn + (an - kn) * 0.1, an, 0.05, 0.036))
        f.add(Ellipsoid(kn + (an - kn) * 0.4 + v3((0, -0.02, 0)), (0.05, 0.045, 0.11)), k=0.02)
        f.add(Ellipsoid(kn + v3((0, -0.04, 0.0)), (0.045, 0.03, 0.05)), k=0.012)                    # the knee cop
        f.paint(RoundBox(kn + v3((0, -0.07, 0.0)), (0.08, 0.05, 0.012)), 1)
        out.append(("Shin" + s, f, vx, "shin." + s, "armor"))
        f = Field("Foot" + s)                                            # long pointed sabatons (poulaines)
        f.add(RoundBox(an + v3((0, -0.04, -0.06)), (0.05, 0.08, 0.03), 0.022))
        f.add(RoundCone(an + v3((0, -0.1, -0.065)), an + v3((0, -0.25, -0.06)), 0.035, 0.006), k=0.02)
        f.add(Sphere(an, 0.042), k=0.015)
        for i in range(3):
            f.paint(RoundBox(an + v3((0, -0.04 - 0.05 * i, -0.05)), (0.1, 0.004, 0.08)), 2)
        out.append(("Foot" + s, f, vx, "foot." + s, "armor"))
    # ---- the stiletto: a long thin blade from the right fist, its edge glowing violet
    wr = v3(J["wrist_R"])
    g0 = wr + v3((0, -0.05, -0.06))
    ax = norm(v3((0, -1.0, -0.1)))
    f = Field("Blade")
    f.add(RoundCone(g0 - ax * 0.05, g0 + ax * 0.03, 0.012, 0.012))
    f.add(RoundBox(g0 + ax * 0.04, (0.05, 0.012, 0.012), 0.006, R=rot_from_axes(z_axis=(0, 0, 1), y_axis=ax)), k=0.004)     # the cross guard
    f.add(RoundCone(g0 + ax * 0.05, g0 + ax * 0.36, 0.016, 0.002), k=0.004)
    f.add(Sphere(g0 - ax * 0.06, 0.016), k=0.004)
    out.append(("Blade", f, vs, "hand.R", "chrome"))
    f = Field("Edge")
    f.add(RoundCone(g0 + ax * 0.1, g0 + ax * 0.34, 0.006, 0.0015))
    out.append(("Edge", f, vs, "hand.R", "glow"))
    return out


def clips(arm):
    def extra(t, aims):
        w = 2 * math.pi * t
        # the cloak's panels stream back as it runs, flapping a little out of step
        aims["cloak.B"] = Vector((0.03 * math.sin(w), 0.5 + 0.1 * math.sin(2 * w + 0.6), -1.0)).normalized()
        for k, sx in (("L", 1), ("R", -1)):
            aims["cloak." + k] = Vector((sx * (0.06 + 0.03 * math.sin(w * 2 + sx)), 0.44 + 0.08 * math.sin(2 * w + 1.0 + sx * 0.5), -1.0)).normalized()
        # the stiletto held low and forward, the claw hand drawn back
        aims["upperarm.R"] = Vector((-0.25, -0.55, -0.8)).normalized()
        aims["forearm.R"] = Vector((-0.05, -0.95, -0.25)).normalized()
        aims["hand.R"] = Vector((0.0, -1.0, -0.15)).normalized()
        aims["head"] = Vector((0.0, -0.25, 1.0))
    ra.walk(arm, J, "Walk", frames=WALK_FRAMES, step=WALK_STEP, lift=0.1, bob=0.03, sway=0.025, arm_swing=0.35, lean=0.3,
            twist=0.18, heavy=0.0, extra=extra)
