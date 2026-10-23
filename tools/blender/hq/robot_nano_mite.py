"""Nano Mite, HQ: the Digital Age's smallest robot, three of which burst out of every Nano Swarm that is destroyed. A tiny
scuttling spider-bot: a white armoured bead of a body (a gunmetal belly under it, a hazard-orange stripe across its
back, a seam down its spine), a single big red eye in a dark socket at its front under a frowning brow, a cyan glow
seam running round its middle where the shell meets the belly, and six thin gunmetal legs (ball joints at the hips and
knees, the knees cocked high, the feet needle-pointed). Walk (12 frames): a fast scuttle, an alternating tripod gait
(three legs carry it while the other three swing), the body jittering, the eye flickering.
Faces -Y, Z up; model_scale 0.9.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Func, rot_from_axes, v3, norm, F
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser, two_bone, bone_len

ROOT_NAME = "NanoMite"
GLB_NAME = "nano_mite"
TEX_PREFIX = "nano_mite"
WALK_STEP = 0.28           # each foot's stride: the body moves 2 * WALK_STEP per loop (a tripod gait)
WALK_FRAMES = 12           # walk_speed = 2 * 0.28 * 0.9 * 24 / 12 = 1.008

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.22, 0.23, 0.26)
RED_GLOW = (1.0, 0.16, 0.08)
CYAN = (0.3, 0.88, 1.0)

C = v3((0, 0.01, 0.2))                     # the body's centre
BR = (0.12, 0.155, 0.1)                    # its half-sizes
SEAM_Z = 0.214                             # the glow seam (where the white shell meets the gunmetal belly)
EYE_C = v3((0, -0.137, 0.212))
EYE_R = 0.056
LEGS = {}
for i, (yh, yk, yf) in enumerate(((-0.07, -0.17, -0.27), (0.02, 0.02, 0.03), (0.1, 0.2, 0.31))):
    for s, sx in (("L", 1), ("R", -1)):
        n = "%s%d" % (s, i + 1)
        LEGS[n] = {"hip": v3((sx * 0.1, yh, 0.19)), "knee": v3((sx * 0.23, yk, 0.3)), "foot": v3((sx * 0.31, yf, 0.012)),
                   "sx": sx}
TRIPOD_A = ("L1", "R2", "L3")

BONES = [("root", tuple(C), tuple(C + v3((0, 0, 0.08))), None),
         ("eye", tuple(EYE_C + v3((0, 0.04, 0))), tuple(EYE_C + v3((0, -0.04, 0))), "root")]
for n, L in LEGS.items():
    BONES += [("thigh." + n, tuple(L["hip"]), tuple(L["knee"]), "root"),
              ("shin." + n, tuple(L["knee"]), tuple(L["foot"]), "thigh." + n)]

MATS = {
    "armor": ("armor", dict(name="RB_MiteArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.42)], seams=[2], scale=0.5)),
    "frame": ("gunmetal", dict(name="RB_MiteFrame", base=(0.22, 0.23, 0.27), labels=[(1, ORANGE, 0.35)], scale=0.5)),
    "socket": ("lens_socket", dict(name="RB_MiteSocket")),
    "glow": ("glow", dict(name="RB_MiteGlow", col=RED_GLOW)),
}
GLOW = {"Eye": (RED_GLOW, 1.6, 0.5), "Seam": (CYAN, 1.4, 0.55)}
LOW_TARGETS = {"Body": 520, "Brow": 70, "Socket": 90, "Eye": 60, "Seam": 110, "Hips": 130}
for _n in LEGS:
    LOW_TARGETS["Femur" + _n] = 44
    LOW_TARGETS["Tibia" + _n] = 50


def _ellipse_ring(c, a, b, z, r):
    """A tube of radius r round the ellipse (half-axes a, b) at height z about c (an approximate distance)."""
    c = v3(c)
    def fn(P):
        x = (P[:, 0] - F(c[0])) / F(a)
        y = (P[:, 1] - F(c[1])) / F(b)
        rr = np.sqrt(x * x + y * y)
        e = (rr - F(1.0)) * F(min(a, b))
        return np.sqrt(e * e + (P[:, 2] - F(z)) ** 2) - F(r)
    return Func(fn, c + v3((-a - r - 0.02, -b - r - 0.02, z - c[2] - r - 0.02)), c + v3((a + r + 0.02, b + r + 0.02, z - c[2] + r + 0.02)))


def _seam_axes():
    """The plan half-axes of the body's outline at the seam's height."""
    k = math.sqrt(max(0.0, 1.0 - ((SEAM_Z - C[2]) / BR[2]) ** 2))
    return BR[0] * k, BR[1] * k


def parts(fine=False):
    vx = 0.003 if fine else 0.0055
    vs = 0.0024 if fine else 0.0045
    out = []
    a, b = _seam_axes()
    # ---- the body: a white bead, a gunmetal belly, an orange stripe across its back, a groove for the glow seam
    f = Field("Body")
    f.add(Ellipsoid(C, BR))
    f.add(Ellipsoid(C + v3((0, -0.085, 0.004)), (0.1, 0.075, 0.085)), k=0.03)                    # its "face" (the eye's mount)
    f.sub(Sphere(EYE_C + v3((0, -0.01, 0)), EYE_R + 0.012), k=0.006)                             # the eye's socket
    f.sub(_ellipse_ring(C, a + 0.004, b + 0.004, SEAM_Z, 0.011), k=0.004)                         # the seam's groove
    f.paint(Func(lambda P: P[:, 2] - F(SEAM_Z), C - 0.3, C + 0.3), 3)
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 1] - F(0.045)) - F(0.03), F(SEAM_Z + 0.01) - P[:, 2]), C - 0.3, C + 0.3), 1)
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 0]) - F(0.003), F(SEAM_Z + 0.02) - P[:, 2]), C - 0.3, C + 0.3), 2)
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 1] - F(0.1)) - F(0.003), F(SEAM_Z + 0.01) - P[:, 2]), C - 0.3, C + 0.3), 2)
    out.append(("Body", f, vx, "root", "armor"))
    f = Field("Brow")                                                         # two small angled plates: a frown
    for sx in (-1, 1):
        f.add(RoundBox(EYE_C + v3((sx * 0.032, -0.012, 0.06)), (0.04, 0.022, 0.011), 0.009,
                       R=rot_from_axes(x_axis=(1, 0, sx * 0.45), y_axis=(0, -1, -0.5))), k=0.008)
    f.paint(Sphere(EYE_C, 1.0), 3)
    out.append(("Brow", f, vs, "root", "armor"))
    f = Field("Socket")
    f.add(Torus(EYE_C + v3((0, -0.004, 0)), EYE_R + 0.004, 0.011, R=rot_from_axes(z_axis=(0, -1, 0))))
    out.append(("Socket", f, vs, "root", "socket"))
    f = Field("Eye")
    f.add(Ellipsoid(EYE_C, (EYE_R, 0.03, EYE_R)))
    out.append(("Eye", f, vs, "eye", "glow"))
    f = Field("Seam")
    f.add(_ellipse_ring(C, a + 0.001, b + 0.001, SEAM_Z, 0.0085))
    out.append(("Seam", f, vs, "root", "glow"))
    # ---- the legs: ball joints at the hips (on the body), thin femurs and tibias, needle feet
    f = Field("Hips")
    for n, L in LEGS.items():
        f.add(Sphere(L["hip"], 0.03))
    out.append(("Hips", f, vs, "root", "frame"))
    for n, L in LEGS.items():
        f = Field("Femur" + n)
        f.add(RoundCone(L["hip"], L["knee"], 0.023, 0.018))
        out.append(("Femur" + n, f, vs, "thigh." + n, "frame"))
        f = Field("Tibia" + n)
        f.add(Sphere(L["knee"], 0.026))
        f.add(RoundCone(L["knee"], L["foot"], 0.018, 0.009), k=0.006)
        f.paint(Sphere(L["knee"], 0.028), 1)                                 # an orange knee
        out.append(("Tibia" + n, f, vs, "shin." + n, "frame"))
    return out


# ------------------------------------------------------------------------------------------------ clips
V = lambda *a: Vector(a)


def leg_aims(arm, n, foot, legs=None):
    L = (legs or LEGS)[n]
    la, lb = bone_len(arm, "thigh." + n), bone_len(arm, "shin." + n)
    pole = V(L["sx"] * 0.5, 0.0, 1.0)
    st = {}
    def thigh(P, base):
        hip = base.translation
        knee = two_bone(hip, foot, la, lb, pole)
        st["knee"] = knee
        return knee - hip
    def shin(P, base):
        return Vector(foot) - st["knee"]
    return {"thigh." + n: thigh, "shin." + n: shin}


def tripod_feet(t, step, lift, legs=None, group_a=TRIPOD_A):
    out = {}
    for n, L in (legs or LEGS).items():
        ph = (t + (0.0 if n in group_a else 0.5)) % 1.0
        f0 = Vector(L["foot"])
        if ph < 0.5:
            k = ph / 0.5
            y, z = -step / 2 + step * k, 0.0
        else:
            k = (ph - 0.5) / 0.5
            e = 0.5 - 0.5 * math.cos(math.pi * k)
            y = step / 2 - step * e
            z = lift * math.sin(math.pi * k) ** 1.3
        out[n] = f0 + V(0.0, y, z)
    return out


def walk(arm):
    """The scuttle: a fast tripod gait, the body jittering (dipping at each change of tripod, wagging), the eye
    flickering from side to side."""
    P = Poser(arm)
    act = ra.new_action(arm, "Walk")
    for f in range(WALK_FRAMES + 1):
        t = f / WALK_FRAMES
        w = 2 * math.pi * t
        aims = {}
        for n, foot in tripod_feet(t, WALK_STEP, 0.075).items():
            aims.update(leg_aims(arm, n, foot))
        root_off = V(0.008 * math.sin(w), 0.0, 0.012 * math.cos(2 * w) - 0.004)
        root_rot = Quaternion(V(0, 0, 1), 0.07 * math.sin(w)) @ Quaternion(V(0, 1, 0), 0.05 * math.sin(w + 0.6)) @ \
            Quaternion(V(1, 0, 0), -0.05 + 0.03 * math.sin(2 * w))
        look = 0.25 * math.sin(w + 1.0)
        aims["eye"] = V(math.sin(look), -math.cos(look), 0.0)
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, scales={"eye": 1.0 + 0.08 * math.sin(2 * w)})
        P.key(ch, f)
    ra.finish_action(arm, act, WALK_FRAMES, True)


def clips(arm):
    walk(arm)
