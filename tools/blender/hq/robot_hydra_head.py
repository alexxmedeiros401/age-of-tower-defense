"""Hydra Head, HQ: one head of the Hydra, a robot serpent crawling on its own. A long segmented body of white armour
plates (a red stripe down its spine, gold rims at every joint, a gunmetal belly) slithers along the ground in waves;
its front third rears up like a cobra's into a long armoured neck and a great serpent head: a long snout with gold
fangs, two amber eyes under red brow ridges, a hinged jaw with an amber glow in its throat, and a fan of gold blades
spread behind its head like a crest. Three hover drones ride docked along its back (released when it is destroyed:
enemies.json "on_death"). Walk: the slither (a wave running down its body), the neck swaying, the jaw working.
Faces -Y, Z up; model_scale 0.9.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3, norm, Func, F, NOISE
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser

ROOT_NAME = "HydraHead"
GLB_NAME = "hydra_head"
TEX_PREFIX = "hydra_head"
WALK_FRAMES = 48

RED = (0.78, 0.12, 0.08)
GOLD = (0.95, 0.72, 0.28)
SEAM = (0.2, 0.2, 0.22)
BELLY = (0.26, 0.28, 0.31)
AMBER = (1.0, 0.62, 0.16)

# the body's joints from the neck's foot back to the tail's tip, and their radii
B = [v3(p) for p in ((0, -0.15, 0.13), (0, 0.06, 0.13), (0, 0.26, 0.125), (0, 0.45, 0.115), (0, 0.62, 0.1), (0, 0.78, 0.085),
                     (0, 0.92, 0.07), (0, 1.04, 0.055))]
BR = [0.16, 0.172, 0.17, 0.155, 0.132, 0.106, 0.082, 0.056]
# the neck rising from the body's front, and the head
N = [B[0], v3((0, -0.31, 0.37)), v3((0, -0.39, 0.66)), v3((0, -0.37, 0.92))]
NR = [0.16, 0.14, 0.122, 0.108]
HEAD_C = v3((0, -0.48, 0.99))
SNOUT = v3((0, -0.74, 0.96))
JAW0 = v3((0, -0.42, 0.92))
PODS = [v3((0, 0.36, 0.33)), v3((0, 0.62, 0.28)), v3((0, 0.86, 0.22))]
POD_BONE = ["b1", "b2", "b4"]

BONES = [("root", tuple(B[2]), tuple(B[2] + v3((0, 0, 0.1))), None),
         ("f1", tuple(B[2]), tuple(B[1]), "root"), ("f2", tuple(B[1]), tuple(B[0]), "f1"),
         ("b1", tuple(B[2]), tuple(B[3]), "root")]
for i in range(3, 7):
    BONES.append(("b%d" % (i - 1), tuple(B[i]), tuple(B[i + 1]), "b%d" % (i - 2)))
BONES += [("n1", tuple(N[0]), tuple(N[1]), "f2"), ("n2", tuple(N[1]), tuple(N[2]), "n1"), ("n3", tuple(N[2]), tuple(N[3]), "n2"),
          ("head", tuple(N[3]), tuple(SNOUT), "n3"), ("jaw", tuple(JAW0), tuple(SNOUT + v3((0, 0.02, -0.07))), "head")]
for i, p in enumerate(PODS):
    BONES.append(("pod%d" % i, tuple(p), tuple(p + v3((0, -0.15, 0))), POD_BONE[i]))
# the body segment each bone owns: (bone, joint a, joint b, radius a, radius b)
SEGS = [("f2", B[0], B[1], BR[0], BR[1]), ("f1", B[1], B[2], BR[1], BR[2])] + \
       [("b%d" % (i - 1), B[i], B[i + 1], BR[i], BR[i + 1]) for i in range(2, 7)]
NSEGS = [("n%d" % (i + 1), N[i], N[i + 1], NR[i], NR[i + 1]) for i in range(3)]

MATS = {
    "armor": ("armor", dict(name="RB_HydraArmor", labels=[(1, RED, 0.4), (2, SEAM, 0.6), (3, GOLD, 0.3), (4, BELLY, 0.45)], seams=[2])),
    "frame": ("gunmetal", dict(name="RB_HydraFrame", labels=[(1, GOLD, 0.3), (2, (0.1, 0.1, 0.11), 0.6)], seams=[2])),
    "gold": ("chrome", dict(name="RB_HydraGold", base=GOLD)),
    "socket": ("lens_socket", dict(name="RB_HydraSocket")),
    "glow": ("glow", dict(name="RB_HydraGlow", col=AMBER)),
}
GLOW = {"Eyes": (AMBER, 1.4, 0.5), "Throat": (AMBER, 1.2, 0.5)}
LOW_TARGETS = {"Head": 1100, "Jaw": 420, "Fangs": 160, "Eyes": 90, "Brows": 160, "Throat": 40, "Crest": 700}
for s in SEGS + NSEGS:
    LOW_TARGETS["Seg_" + s[0]] = 380
for i in range(3):
    LOW_TARGETS["Pod%d" % i] = 300
    LOW_TARGETS["PodEye%d" % i] = 40
    GLOW["PodEye%d" % i] = (AMBER, 1.3, 0.5)


def segment(f, a, b, ra_, rb_, spine=True):
    """An armoured body ring from joint a to b: a white shell, a red stripe down the spine, gold rims at both ends, a
    gunmetal belly; a dark joint ball at its front end fills the gap when the body bends."""
    ax = norm(b - a)
    L = float(np.linalg.norm(b - a))
    f.add(RoundCone(a + ax * 0.012, b - ax * 0.012, ra_ * 0.97, rb_ * 0.97))
    f.add(Sphere(a, ra_ * 0.86), k=0.01)
    up = norm(v3((0, 0, 1)) - ax * ax[2]) if abs(ax[2]) < 0.95 else v3((0, 1, 0))
    if spine:                                    # a raised scute along its back, overlapping the next one
        rm = (ra_ + rb_) * 0.5
        c = a + ax * (L * 0.55) + up * (rm * 0.5)
        f.add(Ellipsoid(c, (rm * 0.82, rm * 0.5, L * 0.62), R=rot_from_axes(z_axis=ax, y_axis=up)), k=0.02)
    if spine:
        f.paint(Func(lambda P, a=a, up=up: np.maximum(np.abs((P - a.astype(F)) @ np.cross(ax, up).astype(F)) - F(0.03),
                                                       F(0.0) - (P - a.astype(F)) @ up.astype(F)), a - 0.4, b + 0.4), 1)
    for e, r in ((a + ax * 0.02, ra_), (b - ax * 0.02, rb_)):
        f.paint(Torus(e, r * 0.97, 0.016, R=rot_from_axes(z_axis=ax)), 3)
    f.paint(Func(lambda P, a=a, up=up: (P - a.astype(F)) @ up.astype(F) + F(0.55 * ra_), a - 0.4, b + 0.4), 4)
    f.paint(Torus(a + ax * (L * 0.5), (ra_ + rb_) * 0.49, 0.004, R=rot_from_axes(z_axis=ax)), 2)


def drone(f, p, label_band=1):
    """A docked hover drone, folded: head pod, tail pod, wings laid back along it."""
    f.add(Ellipsoid(p + v3((0, -0.05, 0.0)), (0.07, 0.075, 0.06)))
    f.add(Ellipsoid(p + v3((0, 0.07, -0.01)), (0.055, 0.09, 0.05)), k=0.02)
    f.sub(Sphere(p + v3((0, -0.12, 0.0)), 0.035), k=0.006)
    f.paint(Torus(p + v3((0, 0.07, -0.01)), 0.052, 0.01, R=rot_from_axes(z_axis=(0, 1, 0))), label_band)
    for sx in (-1, 1):
        f.add(Ellipsoid(p + v3((sx * 0.05, 0.05, 0.05)), (0.025, 0.12, 0.006), R=rot_from_axes(x_axis=(1, 0, sx * 0.3))), k=0.004)
        f.paint(Ellipsoid(p + v3((sx * 0.05, 0.05, 0.055)), (0.012, 0.13, 0.01)), 3)


def parts(fine=False):
    vx = 0.0045 if fine else 0.008
    vs = 0.0034 if fine else 0.0065
    out = []
    for bone, a, b, r1, r2 in SEGS + NSEGS:
        f = Field("Seg_" + bone)
        segment(f, a, b, r1, r2)
        out.append(("Seg_" + bone, f, vx, bone, "armor"))
    # ---- the head: a long armoured skull and snout, red brow ridges, the eye sockets, a red crest ridge
    f = Field("Head")
    f.add(Ellipsoid(HEAD_C, (0.135, 0.17, 0.1)))
    f.add(RoundCone(HEAD_C + v3((0, -0.08, -0.01)), SNOUT, 0.1, 0.055), k=0.04)
    f.add(Sphere(N[3], NR[3] * 0.9), k=0.04)
    for sx in (-1, 1):
        f.sub(Sphere(HEAD_C + v3((sx * 0.1, -0.08, 0.04)), 0.042), k=0.01)
        f.sub(Sphere(SNOUT + v3((sx * 0.025, -0.01, 0.03)), 0.012), k=0.004)                     # nostrils
    f.sub(RoundBox(HEAD_C + v3((0, -0.16, -0.075)), (0.09, 0.2, 0.035), 0.02), k=0.01)             # the mouth's slot
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 0]) - F(0.022), F(HEAD_C[2] + 0.06) - P[:, 2]), HEAD_C - 0.4, HEAD_C + 0.4), 1)
    f.paint(Torus(N[3] + v3((0, -0.02, 0.0)), NR[3] * 0.92, 0.015, R=rot_from_axes(z_axis=norm(SNOUT - N[3]))), 3)
    f.paint(Func(lambda P: (P[:, 2] - F(HEAD_C[2] - 0.05)), HEAD_C - 0.4, HEAD_C + 0.4), 4)
    out.append(("Head", f, vs, "head", "armor"))
    f = Field("Brows")
    for sx in (-1, 1):
        a = HEAD_C + v3((sx * 0.06, -0.02, 0.085))
        b = HEAD_C + v3((sx * 0.13, -0.13, 0.065))
        f.add(RoundCone(a, b, 0.024, 0.016))
    f.paint(Sphere(HEAD_C, 1.0), 1)
    out.append(("Brows", f, vs, "head", "armor"))
    f = Field("Eyes")
    for sx in (-1, 1):
        f.add(Ellipsoid(HEAD_C + v3((sx * 0.098, -0.085, 0.04)), (0.028, 0.034, 0.024)))
    out.append(("Eyes", f, vs, "head", "glow"))
    f = Field("Fangs")
    for sx in (-1, 1):
        a = SNOUT + v3((sx * 0.032, 0.03, -0.035))
        f.add(RoundCone(a, a + v3((sx * 0.004, -0.004, -0.06)), 0.013, 0.003))
        for j in range(3):
            c = SNOUT + v3((sx * 0.05, 0.08 + 0.05 * j, -0.04))
            f.add(RoundCone(c, c + v3((0, 0, -0.025)), 0.008, 0.002), k=0.003)
    out.append(("Fangs", f, vs, "head", "gold"))
    f = Field("Jaw")
    f.add(RoundCone(JAW0, SNOUT + v3((0, 0.03, -0.075)), 0.08, 0.04))
    f.sub(RoundBox(HEAD_C + v3((0, -0.16, -0.045)), (0.07, 0.19, 0.025), 0.015), k=0.01)
    for sx in (-1, 1):
        for j in range(3):
            c = SNOUT + v3((sx * 0.04, 0.1 + 0.05 * j, -0.06))
            f.add(RoundCone(c, c + v3((0, 0, 0.022)), 0.007, 0.002), k=0.003)
    f.paint(Sphere(HEAD_C, 1.0), 4)
    out.append(("Jaw", f, vs, "jaw", "armor"))
    f = Field("Throat")
    f.add(Ellipsoid(HEAD_C + v3((0, -0.1, -0.06)), (0.05, 0.07, 0.02)))
    out.append(("Throat", f, vs, "jaw", "glow"))
    # ---- the crest: a fan of gold blades spread behind its head, a red ridge along the fan's middle blade
    f = Field("Crest")
    base = N[3] + v3((0, 0.06, 0.02))
    for k in range(7):
        ang = math.radians(-72 + 24 * k)
        d = norm(v3((math.sin(ang), 0.55, math.cos(ang) * 0.9)))
        L = 0.26 - 0.05 * abs(k - 3) / 3
        f.add(RoundCone(base + d * 0.04, base + d * L, 0.022, 0.006), k=0.012)
        f.add(Ellipsoid(base + d * (L * 0.6), (0.012, 0.05, L * 0.4), R=rot_from_axes(z_axis=d, x_axis=norm(np.cross(d, v3((0, 1, 0)))))), k=0.01)
    f.add(Torus(base, 0.06, 0.02, R=rot_from_axes(z_axis=(0, 1, 0.3))), k=0.01)
    out.append(("Crest", f, vs, "n3", "gold"))
    # ---- three docked drones, each on its own bone
    for i, p in enumerate(PODS):
        f = Field("Pod%d" % i)
        drone(f, p)
        out.append(("Pod%d" % i, f, vs, "pod%d" % i, "armor"))
        f = Field("PodEye%d" % i)
        f.add(Ellipsoid(p + v3((0, -0.118, 0.0)), (0.028, 0.012, 0.028)))
        out.append(("PodEye%d" % i, f, vs, "pod%d" % i, "glow"))
    return out


def slither(arm, name="Walk", frames=WALK_FRAMES, amp_head=0.03, amp_tail=0.14, wave=1.15, neck_sway=0.12, jaw=0.25,
            extra=None):
    """The body's joints ride a sideways wave running from the neck to the tail (one wave a loop); every body bone aims
    from its joint to the next one's place on the wave; the neck sways slowly and the head keeps looking ahead."""
    P = Poser(arm)
    act = ra.new_action(arm, name)
    def wpos(i, t):
        p = Vector(B[i])
        s = (float(B[i][1]) - float(B[0][1])) / wave                    # arc position (waves) from the neck's foot
        amp = amp_head + (amp_tail - amp_head) * (i / (len(B) - 1)) ** 1.2
        return p + Vector((amp * math.sin(2 * math.pi * (t * 1.0 - s)), 0.0, 0.0))
    for f in range(frames + 1):
        t = f / frames
        aims = {}
        pts = [wpos(i, t) for i in range(len(B))]
        aims["f1"] = pts[1] - pts[2]
        aims["f2"] = pts[0] - pts[1]
        for i in range(2, 7):
            aims["b%d" % (i - 1)] = pts[i + 1] - pts[i]
        # the neck: a slow S-sway, the head steady, looking ahead (a little down)
        sw = neck_sway * math.sin(2 * math.pi * t + 0.8)
        for k, nm in enumerate(("n1", "n2", "n3")):
            d = Vector(N[k + 1]) - Vector(N[k])
            aims[nm] = Quaternion(Vector((0, 0, 1)), sw * (1.0 - 0.6 * k)) @ d
        aims["head"] = (Vector(SNOUT) - Vector(N[3])) + Vector((-0.08 * math.sin(2 * math.pi * t + 0.8), 0.0, 0.02 * math.sin(4 * math.pi * t)))
        op = max(0.0, math.sin(2 * math.pi * (t * 2.0)))                   # the jaw works twice a loop
        jd = Vector(SNOUT + v3((0, 0.02, -0.07))) - Vector(JAW0)
        aims["jaw"] = Quaternion(Vector((1, 0, 0)), jaw * op) @ jd
        for i in range(3):
            aims["pod%d" % i] = Vector((0.05 * math.sin(2 * math.pi * (2 * t + 0.3 * i)), -1.0, 0.03 * math.sin(2 * math.pi * t + i)))
        if extra is not None:
            extra(t, aims)
        roll = 0.04 * math.sin(2 * math.pi * t)
        ch, _ = P.solve(aims, root_off=Vector((pts[2].x, 0.0, 0.005 * math.sin(4 * math.pi * t))),
                        root_rot=Quaternion(Vector((0, 1, 0)), roll))
        P.key(ch, f)
    ra.finish_action(arm, act, frames, True)
    return act


def clips(arm):
    slither(arm)
