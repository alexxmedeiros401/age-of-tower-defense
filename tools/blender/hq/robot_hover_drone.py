"""Hover Drone, HQ: the Classical Age's swarming flyer, a drone of the Hydra's hive. A sleek white wasp of a machine: a
rounded head pod with one big glowing amber eye in a gold bezel, a hoplite's red tufted crest along its top, a red Greek-key band round the
pod, two gold feeler antennae; a gunmetal thorax with two pairs of long blade wings on gold hinges (they buzz in a
blur); a ribbed tail pod banded red and gold, ending in a gold sting with an amber thruster glowing at its tip; three
pairs of little folded legs under it. It darts: bobbing, rolling and pitching, its tail swaying and its eye scanning.
Faces -Y, Z up; hovers about 0.85 model units up; model_scale 0.9.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3, norm, Func, F, NOISE
import robot_anim as ra
from mathutils import Vector, Quaternion

ROOT_NAME = "HoverDrone"
GLB_NAME = "hover_drone"
TEX_PREFIX = "hover_drone"

RED = (0.78, 0.12, 0.08)
GOLD = (0.95, 0.72, 0.28)
SEAM = (0.2, 0.2, 0.22)
AMBER = (1.0, 0.62, 0.16)
C = v3((0, 0, 0.86))                     # thorax centre
HEAD_C = C + v3((0, -0.2, 0.02))
TAIL_A = C + v3((0, 0.1, 0.0))           # the tail pod's front ring
TAIL_B = C + v3((0, 0.44, -0.08))        # its back end
STING = TAIL_B + v3((0, 0.1, -0.03))
WINGS = {"L1": (v3((0.07, -0.04, 0.07)), 0.0), "L2": (v3((0.07, 0.06, 0.06)), 1.0),
         "R1": (v3((-0.07, -0.04, 0.07)), 0.0), "R2": (v3((-0.07, 0.06, 0.06)), 1.0)}
WING_L = (0.4, 0.33)                     # the front and back wings' lengths

BONES = [
    ("root", tuple(C), tuple(C + v3((0, 0, 0.1))), None),
    ("eye", tuple(HEAD_C + v3((0, -0.12, 0.0))), tuple(HEAD_C + v3((0, -0.24, 0.0))), "root"),
    ("tail", tuple(TAIL_A), tuple(TAIL_B), "root"),
    ("ant.L", tuple(HEAD_C + v3((0.05, -0.06, 0.1))), tuple(HEAD_C + v3((0.12, -0.2, 0.2))), "root"),
    ("ant.R", tuple(HEAD_C + v3((-0.05, -0.06, 0.1))), tuple(HEAD_C + v3((-0.12, -0.2, 0.2))), "root"),
]
for k, (p, _) in WINGS.items():
    sx = 1 if k[0] == "L" else -1
    L = WING_L[0] if k[1] == "1" else WING_L[1]
    BONES.append(("wing." + k, tuple(C + p), tuple(C + p + v3((sx * L, 0.08 if k[1] == "1" else 0.12, 0.05))), "root"))

MATS = {
    "armor": ("armor", dict(name="RB_HoverArmor", labels=[(1, RED, 0.4), (2, SEAM, 0.6), (3, GOLD, 0.3)], seams=[2])),
    "frame": ("gunmetal", dict(name="RB_HoverFrame", labels=[(1, GOLD, 0.3), (2, (0.1, 0.1, 0.11), 0.6)], seams=[2])),
    "gold": ("chrome", dict(name="RB_HoverGold", base=GOLD)),
    "socket": ("lens_socket", dict(name="RB_HoverSocket")),
    "glow": ("glow", dict(name="RB_HoverGlow", col=AMBER)),
}
GLOW = {"Eye": (AMBER, 1.4, 0.5), "Thruster": (AMBER, 1.3, 0.5)}
LOW_TARGETS = {"Head": 720, "Brow": 160, "EyeRing": 120, "Eye": 80, "Thorax": 360, "Tail": 700, "Sting": 140, "Thruster": 40,
               "Legs": 240, "AntL": 60, "AntR": 60}
for k in WINGS:
    LOW_TARGETS["Wing" + k] = 120
FACE_Y = rot_from_axes(z_axis=(0, -1, 0))


def _key_band(c, axis, r, z0, w=0.022):
    """The Greek key (a meander) as a paint field round a pod: a band of hooked steps (label 1) on a ring."""
    ax = norm(axis)
    u = norm(np.cross(ax, v3((0, 0, 1)))) if abs(ax[2]) < 0.9 else v3((1, 0, 0))
    vv = np.cross(ax, u)
    def fn(P):
        q = P - c.astype(F)
        h = q @ ax.astype(F) - F(z0)
        a = np.arctan2(q @ vv.astype(F), q @ u.astype(F))
        s = a * F(12 / (2 * math.pi))
        fr = s - np.floor(s)
        hn = h / F(w)                                           # -1..1 across the band
        # the meander: a top rail, a bottom rail, and in each cell a hook from the top rail down and back
        rails = np.minimum(np.abs(hn - F(0.85)), np.abs(hn + F(0.85))) - F(0.15)
        stem = np.maximum(np.abs(fr - F(0.25)) - F(0.08), np.abs(hn - F(0.15)) - F(0.7))
        hook = np.maximum(np.abs(hn + F(0.25)) - F(0.12), np.abs(fr - F(0.45)) - F(0.2))
        stem2 = np.maximum(np.abs(fr - F(0.65)) - F(0.08), np.abs(hn + F(0.05)) - F(0.32))
        d = np.minimum(np.minimum(rails, stem), np.minimum(hook, stem2)) * F(w)
        return np.maximum(d, np.abs(h) - F(w * 1.05))
    return Func(fn, c - r - 0.05, c + r + 0.05)


def parts(fine=False):
    vx = 0.0042 if fine else 0.0075
    vs = 0.003 if fine else 0.006
    out = []
    # ---- the head pod: a rounded capsule, the eye socket in front, a red key band round it, seams
    f = Field("Head")
    f.add(Ellipsoid(HEAD_C, (0.15, 0.16, 0.13)))
    f.add(Ellipsoid(HEAD_C + v3((0, 0.08, -0.02)), (0.12, 0.12, 0.1)), k=0.04)
    f.sub(Sphere(HEAD_C + v3((0, -0.16, -0.005)), 0.085), k=0.012)
    f.paint(_key_band(HEAD_C, (0, 1, 0), 0.18, 0.03), 1)
    f.paint(RoundBox(HEAD_C + v3((0, 0, 0.0)), (0.003, 0.3, 0.3)), 2)
    for sx in (-1, 1):
        f.paint(RoundBox(HEAD_C + v3((sx * 0.13, 0.04, -0.03)), (0.03, 0.04, 0.03), 0.008), 3)       # gold vents
    out.append(("Head", f, vx, "root", "armor"))
    f = Field("Brow")                                                         # a red crest fin over the pod, a gold rim
    def crest(P):
        q = P - HEAD_C.astype(F)
        y, z = q[:, 1], q[:, 2]
        prof = F(0.2) - F(0.6) * (y + F(0.02)) ** 2 - F(0.03) * np.abs(np.sin((y + F(0.2)) * F(40)))   # a tufted top edge
        return np.maximum(np.maximum(np.abs(q[:, 0]) - F(0.016), z - prof), np.maximum(F(0.08) - z, np.abs(y + F(0.02)) - F(0.15)))
    f.add(Func(crest, HEAD_C - 0.3, HEAD_C + 0.3))
    f.paint(Sphere(HEAD_C, 1.0), 1)
    f.paint(Func(lambda P: P[:, 2] - F(HEAD_C[2] + 0.105), HEAD_C - 0.3, HEAD_C + 0.3), 3)                  # its gold foot
    out.append(("Brow", f, vs, "root", "armor"))
    f = Field("EyeRing")
    f.add(Torus(HEAD_C + v3((0, -0.155, -0.005)), 0.072, 0.016, R=FACE_Y))
    out.append(("EyeRing", f, vs, "eye", "gold"))
    f = Field("Eye")
    f.add(Ellipsoid(HEAD_C + v3((0, -0.15, -0.005)), (0.062, 0.035, 0.062)))
    out.append(("Eye", f, vs, "eye", "glow"))
    # ---- the thorax: gunmetal, the wing hinges in gold
    f = Field("Thorax")
    f.add(Ellipsoid(C, (0.1, 0.13, 0.09)))
    f.add(RoundCone(HEAD_C + v3((0, 0.1, -0.02)), C, 0.06, 0.07), k=0.03)
    f.add(RoundCone(C, TAIL_A, 0.07, 0.05), k=0.03)
    for k, (p, _) in WINGS.items():
        f.add(Sphere(C + p, 0.026), k=0.01)
        f.paint(Sphere(C + p, 0.034), 1)
    out.append(("Thorax", f, vs, "root", "frame"))
    # ---- the tail pod: three swelling ribbed rings banded red and gold, the sting, the thruster
    f = Field("Tail")
    ax = norm(TAIL_B - TAIL_A)
    L = float(np.linalg.norm(TAIL_B - TAIL_A))
    for i in range(3):
        t0, t1 = i / 3.0, (i + 1) / 3.0
        a, b = TAIL_A + ax * (L * t0 + 0.01), TAIL_A + ax * (L * t1 - 0.01)
        r = 0.085 + 0.045 * math.sin(math.pi * (t0 + t1) / 2)
        f.add(RoundCone(a, b, r * 0.9, r * 0.92), k=0.02)
        f.paint(Torus(b - ax * 0.01, r * 0.92, 0.016, R=rot_from_axes(z_axis=ax)), 1 if i != 1 else 3)
    f.paint(RoundBox(C + v3((0, 0.25, 0.0)), (0.003, 0.3, 0.3)), 2)
    out.append(("Tail", f, vx, "tail", "armor"))
    f = Field("Sting")
    f.add(RoundCone(TAIL_B - ax * 0.02, STING, 0.05, 0.012))
    f.add(Torus(TAIL_B, 0.05, 0.012, R=rot_from_axes(z_axis=ax)), k=0.006)
    out.append(("Sting", f, vs, "tail", "gold"))
    f = Field("Thruster")
    f.add(Sphere(STING + norm(STING - TAIL_B) * 0.006, 0.02))
    out.append(("Thruster", f, vs, "tail", "glow"))
    # ---- three pairs of little folded legs under the thorax
    f = Field("Legs")
    for j, y in enumerate((-0.06, 0.0, 0.06)):
        for sx in (-1, 1):
            a = C + v3((sx * 0.05, y, -0.06))
            b = a + v3((sx * 0.06, -0.02 + 0.02 * j, -0.06))
            c2 = b + v3((-sx * 0.02, 0.03, -0.06))
            f.add(RoundCone(a, b, 0.012, 0.01), k=0.004)
            f.add(RoundCone(b, c2, 0.01, 0.006), k=0.004)
    out.append(("Legs", f, vs, "root", "frame"))
    # ---- the antennae
    for side, sx in (("L", 1), ("R", -1)):
        f = Field("Ant" + side)
        a = HEAD_C + v3((sx * 0.05, -0.06, 0.1))
        b = HEAD_C + v3((sx * 0.09, -0.14, 0.17))
        c2 = HEAD_C + v3((sx * 0.12, -0.21, 0.2))
        f.add(RoundCone(a, b, 0.008, 0.006))
        f.add(RoundCone(b, c2, 0.006, 0.005), k=0.003)
        f.add(Sphere(c2, 0.012), k=0.003)
        out.append(("Ant" + side, f, vs, "ant." + side, "gold"))
    # ---- the blade wings: long thin leaf-shaped blades, ribbed, a gold spar along the leading edge
    for k, (p, ph) in WINGS.items():
        sx = 1 if k[0] == "L" else -1
        Lw = WING_L[0] if k[1] == "1" else WING_L[1]
        root = C + p
        d = norm(v3((sx * Lw, 0.08 if k[1] == "1" else 0.12, 0.05)))
        tip = root + d * Lw
        f = Field("Wing" + k)
        w = 0.07 if k[1] == "1" else 0.06
        side_v = norm(np.cross(d, v3((0, 0, 1))))
        R = rot_from_axes(x_axis=d, z_axis=norm(np.cross(d, side_v)))
        f.add(Ellipsoid(root + d * (Lw * 0.5), (Lw * 0.5, w, 0.008), R=R))
        f.add(RoundCone(root, tip, 0.011, 0.005), k=0.006)
        f.paint(RoundCone(root, tip, 0.016, 0.009), 3)
        for j in range(3):
            q = root + d * (Lw * (0.3 + 0.2 * j))
            f.paint(RoundCone(q, q + side_v * w * 0.9 * (1 if sx > 0 else -1) + d * 0.04, 0.004, 0.003), 2)
        out.append(("Wing" + k, f, vs, "wing." + k, "armor"))
    return out


def clips(arm):
    ants = {s: (Vector(BONES[3 if s == "L" else 4][1]), Vector(BONES[3 if s == "L" else 4][2])) for s in ("L", "R")}
    wing_rest = {}
    for b in BONES:
        if b[0].startswith("wing."):
            wing_rest[b[0]] = (Vector(b[1]), Vector(b[2]))
    tail0 = (Vector(TAIL_B) - Vector(TAIL_A)).normalized()
    def extra(t, aims):
        look = 0.3 * math.sin(2 * math.pi * t) + 0.1 * math.sin(6 * math.pi * t)
        aims["eye"] = Vector((math.sin(look), -math.cos(look), -0.12))
        # the wings buzz: 12 beats a loop, fore and hind wings out of step
        for nm, (h, tl) in wing_rest.items():
            ph = 0.0 if nm.endswith("1") else 0.5
            beat = math.sin(2 * math.pi * (12 * t + ph))
            d = (tl - h).normalized()
            side = 1.0 if ".L" in nm else -1.0
            aims[nm] = (Quaternion(Vector((0, 1, 0)), side * 0.55 * beat) @ d)
        sway = 0.18 * math.sin(2 * math.pi * 2 * t)
        aims["tail"] = Quaternion(Vector((0, 0, 1)), sway) @ (Quaternion(Vector((1, 0, 0)), 0.1 * math.sin(2 * math.pi * t)) @ tail0)
        for s, (h, tl) in ants.items():
            wob = 0.15 * math.sin(2 * math.pi * (3 * t + (0.0 if s == "L" else 0.3)))
            aims["ant." + s] = Quaternion(Vector((1, 0, 0)), wob) @ (tl - h).normalized()
    ra.hover(arm, "Fly", frames=48, bob=0.05, tilt=0.12, roll=0.08, spin_bones=(), extra=extra)
