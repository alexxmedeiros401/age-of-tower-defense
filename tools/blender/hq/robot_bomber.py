"""Bomber, HQ: the Gunpowder Age's flying bomb-carrier, a robot grenadier. A fat, rounded white fuselage like a small
airship pod with two hazard-orange bands and panel lines, a single big red eye lens at its nose under a frowning brow,
four stubby gunmetal fins at its tail (orange tips), four ducted rotors on short gunmetal arms; slung under its belly in a
four-fingered gunmetal claw, a big round black iron bomb (the Gunpowder Age's grenade, robot-style): a glowing
orange fuse at its front and cyan energy seams round it that hint at the EMP inside (enemies.json "emp" on_death: it
bursts into an EMP blast when it is destroyed).
Fly: it hovers and bobs, the rotors spinning, the bomb swaying a little in its claw (it hangs on a ball joint and keeps
hanging plumb while the body pitches and rolls), the eye scanning. Faces -Y, Z up; hovers about 0.94 model units up;
model_scale 0.9 (and "flying": the game lifts it 0.9 more).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3, norm, euler
import robot_anim as ra
from mathutils import Vector, Quaternion

ROOT_NAME = "Bomber"
GLB_NAME = "bomber"
TEX_PREFIX = "bomber"

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.12, 0.12, 0.14)
BLACK = (0.07, 0.07, 0.08)
RED_GLOW = (1.0, 0.22, 0.08)
FUSE_GLOW = (1.0, 0.56, 0.14)
CYAN = (0.3, 0.88, 1.0)

C = v3((0, 0, 0.94))                       # the fuselage's centre
EYE_C = v3((0, -0.385, 0.94))              # the eye (the ring's centre, on the nose)
ROTORS = {"FL": v3((0.44, -0.17, 1.0)), "FR": v3((-0.44, -0.17, 1.0)), "BL": v3((0.44, 0.27, 1.0)), "BR": v3((-0.44, 0.27, 1.0))}
DUCT_R = 0.125
PIVOT = v3((0, 0.03, 0.675))               # the claw's ball joint under the belly (the bomb swings about it)
HUB = v3((0, 0.03, 0.585))                 # the claw's hub, on a rod from the ball joint
B = v3((0, 0.03, 0.37))                    # the bomb's centre (rest): it hangs low, to show under the pod from above
RB = 0.19                                  # its radius
FUSE_D = norm(v3((0, -1.0, -0.5)))         # its fuse: at the front, a little below the equator
FINGERS = [math.radians(45 + 90 * i) for i in range(4)]     # the claw's fingers (azimuths), between the seams

BONES = [
    ("root", tuple(C), tuple(C + v3((0, 0, 0.1))), None),
    ("eye", tuple(EYE_C + v3((0, 0.03, 0))), tuple(EYE_C + v3((0, -0.09, 0))), "root"),
    ("bomb", tuple(PIVOT), tuple(B), "root"),
]
for k, p in ROTORS.items():
    BONES.append(("rotor." + k, tuple(p), tuple(p + v3((0, 0, 0.08))), "root"))

MATS = {
    "armor": ("armor", dict(name="RB_BomberArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.45)], seams=[2])),
    "frame": ("gunmetal", dict(name="RB_BomberFrame", labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6), (4, BLACK, 0.5)], seams=[2])),
    "iron": ("gunmetal", dict(name="RB_BomberIron", base=(0.075, 0.075, 0.085), edge=(0.36, 0.38, 0.42), labels=[(2, (0.03, 0.03, 0.035), 0.6)],
                              rough=0.36, seams=[2])),
    "chrome": ("chrome", dict(name="RB_BomberChrome")),
    "rubber": ("rubber", dict(name="RB_BomberBlade", base=(0.12, 0.12, 0.14))),
    "socket": ("lens_socket", dict(name="RB_BomberSocket")),
    "glow": ("glow", dict(name="RB_BomberGlow", col=RED_GLOW)),
}
GLOW = {"Eye": (RED_GLOW, 1.4, 0.5), "FuseGlow": (FUSE_GLOW, 1.4, 0.5), "Seams": (CYAN, 1.2, 0.55)}

LOW_TARGETS = {"Body": 950, "Brow": 150, "EyeRing": 170, "Eye": 90, "Pupil": 40, "Ducts": 520, "Arms": 320, "Fins": 320,
               "Pylon": 170, "Claw": 440, "Bomb": 520, "Seams": 240, "Fuse": 150, "Wick": 40, "FuseGlow": 60}
for k in ROTORS:
    LOW_TARGETS["Blades" + k] = 80
FACE_Y = rot_from_axes(z_axis=(0, -1, 0))


def body_sdf(P):
    """The fuselage alone (for placing things on it): a fat egg of a pod, fuller at the nose, tapering to the tail."""
    a = Ellipsoid(C + v3((0, -0.06, 0)), (0.25, 0.36, 0.24))(P)
    b = RoundCone(C + v3((0, 0.04, 0)), C + v3((0, 0.40, 0.012)), 0.215, 0.075)(P)
    from sdf import smin
    return smin(a, b, 0.07)


def _ring(f, y, half, label):
    f.paint(RoundBox(C + v3((0, y, 0)), (0.4, half, 0.4)), label)


def parts(fine=False):
    vx = 0.0042 if fine else 0.0075
    vs = 0.003 if fine else 0.006
    out = []
    # ---- the fuselage: a fat white pod, the eye socket in its nose, two orange bands, panel lines, side vents
    f = Field("Body")
    f.add(Ellipsoid(C + v3((0, -0.06, 0)), (0.25, 0.36, 0.24)))
    f.add(RoundCone(C + v3((0, 0.04, 0)), C + v3((0, 0.40, 0.012)), 0.215, 0.075), k=0.07)
    f.sub(Sphere(EYE_C + v3((0, -0.035, 0)), 0.112), k=0.012)                          # the eye's socket
    for y, half in ((-0.2, 0.032), (0.19, 0.03)):                                       # the orange bands, seams either side
        _ring(f, y, half, 1)
        _ring(f, y - half - 0.006, 0.0028, 2)
        _ring(f, y + half + 0.006, 0.0028, 2)
    f.paint(RoundBox(C + v3((0, 0.0, 0.17)), (0.0028, 0.17, 0.12)), 2)                 # a seam along its back, between the bands
    f.paint(RoundBox(C + v3((0, 0.0, -0.17)), (0.0028, 0.17, 0.12)), 2)                # and its belly
    for sx in (-1, 1):
        f.paint(RoundBox(C + v3((sx * 0.25, 0.0, 0.0)), (0.08, 0.17, 0.0028)), 2)      # a seam along each side
        for i in range(3):                                                             # vents behind the eye band
            f.paint(RoundBox(C + v3((sx * 0.24, -0.06 + 0.055 * i, 0.07)), (0.06, 0.016, 0.03), 0.008), 3)
    for sx in (-1, 1):                                                                 # an access hatch on its back
        f.paint(RoundBox(C + v3((sx * 0.07, 0.06, 0.22)), (0.0028, 0.07, 0.08)), 2)
    for dy in (-0.01, 0.13):
        f.paint(RoundBox(C + v3((0, dy, 0.22)), (0.07, 0.0028, 0.08)), 2)
    out.append(("Body", f, vx, "root", "armor"))
    # ---- the brow: two angled armour plates over the eye (a frown)
    f = Field("Brow")
    for sx in (-1, 1):
        f.add(RoundBox(EYE_C + v3((sx * 0.062, -0.012, 0.114)), (0.07, 0.036, 0.019), 0.016,
                       R=rot_from_axes(x_axis=(1, 0, sx * 0.38), y_axis=(0, -1, -0.45))), k=0.015)
    f.paint(RoundBox(EYE_C + v3((0, -0.06, 0.135)), (0.2, 0.02, 0.05)), 1)              # its front edge orange
    out.append(("Brow", f, vs, "root", "armor"))
    # ---- the eye: a gunmetal bezel with bolts, the red lens, a dark pupil
    f = Field("EyeRing")
    f.add(Torus(EYE_C, 0.106, 0.022, R=FACE_Y))
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        f.add(Sphere(EYE_C + v3((0.106 * math.cos(a), -0.022, 0.106 * math.sin(a))), 0.0105), k=0.004)
    out.append(("EyeRing", f, vs, "root", "frame"))
    f = Field("Eye")
    f.add(Ellipsoid(EYE_C + v3((0, 0.005, 0)), (0.092, 0.045, 0.092)))
    out.append(("Eye", f, vs, "eye", "glow"))
    f = Field("Pupil")
    f.add(Ellipsoid(EYE_C + v3((0, -0.042, 0)), (0.033, 0.009, 0.033)))
    out.append(("Pupil", f, vs * 0.8, "eye", "socket"))
    # ---- four ducted rotors on short gunmetal arms
    f = Field("Ducts")
    for k, p in ROTORS.items():
        f.add(Torus(p + v3((0, 0, 0.01)), DUCT_R, 0.027))
        f.add(Torus(p + v3((0, 0, -0.012)), DUCT_R, 0.022), k=0.015)
        f.paint(Torus(p + v3((0, 0, 0.03)), DUCT_R, 0.014), 1)                          # an orange rim round its top
        f.paint(Torus(p + v3((0, 0, -0.006)), DUCT_R + 0.026, 0.003), 2)
    out.append(("Ducts", f, vs, "root", "armor"))
    f = Field("Arms")
    for k, p in ROTORS.items():
        sx = 1.0 if p[0] > 0 else -1.0
        base = v3((sx * 0.19, p[1] * 0.85, 0.99))
        f.add(Sphere(base, 0.045))
        f.add(RoundCone(base, p + v3((-sx * (DUCT_R - 0.012), 0, -0.012)), 0.034, 0.025), k=0.012)
        f.add(Cylinder(p + v3((0, 0, -0.016)), 0.034, 0.056, rr=0.01), k=0.006)        # the motor
        for i in range(3):
            a = i * 2 * math.pi / 3 + (math.pi / 2 if sx < 0 else -math.pi / 2) + math.pi / 3
            d = v3((math.cos(a), math.sin(a), 0))
            f.add(RoundCone(p + v3((0, 0, -0.03)), p + d * (DUCT_R - 0.012) + v3((0, 0, -0.016)), 0.0085), k=0.005)
        f.paint(Cylinder(p + v3((0, 0, -0.03)), 0.04, 0.014), 1)                       # an orange collar on the motor
    out.append(("Arms", f, vs, "root", "frame"))
    for k, p in ROTORS.items():
        f = Field("Blades" + k)
        f.add(Cylinder(p + v3((0, 0, 0.016)), 0.025, 0.022, rr=0.008))
        for i in range(3):
            a = i * 2 * math.pi / 3 + (0.5 if k in ("FL", "BR") else 0.0)
            d = v3((math.cos(a), math.sin(a), 0))
            f.add(RoundBox(p + d * 0.054 + v3((0, 0, 0.016)), (0.04, 0.016, 0.0035), 0.0035,
                           R=rot_from_axes(x_axis=d, z_axis=(0, 0, 1)) @ euler(0.35, 0, 0)), k=0.004)
        out.append(("Blades" + k, f, 0.0028 if fine else 0.0055, "rotor." + k, "rubber"))
    # ---- the tail: four stubby swept fins (orange tips) round a gunmetal tail cap
    f = Field("Fins")
    tc = C + v3((0, 0.0, 0.012))
    f.add(RoundCone(tc + v3((0, 0.42, 0)), tc + v3((0, 0.505, 0)), 0.058, 0.036))
    f.add(Torus(tc + v3((0, 0.43, 0)), 0.06, 0.012, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.006)
    f.add(RoundBox(tc + v3((0, 0.40, 0.115)), (0.016, 0.075, 0.065), 0.014, R=euler(-0.45, 0, 0)), k=0.01)          # top
    f.add(RoundBox(tc + v3((0, 0.40, -0.1)), (0.016, 0.065, 0.05), 0.014, R=euler(0.45, 0, 0)), k=0.01)            # bottom
    for sx in (-1, 1):
        f.add(RoundBox(tc + v3((sx * 0.11, 0.40, 0.0)), (0.07, 0.075, 0.016), 0.014, R=euler(0, 0, sx * 0.45)), k=0.01)
    for p, r in ((tc + v3((0, 0.45, 0.175)), 0.04), (tc + v3((0, 0.44, -0.145)), 0.035),
                 (tc + v3((0.175, 0.45, 0)), 0.04), (tc + v3((-0.175, 0.45, 0)), 0.04)):
        f.paint(Sphere(p, r), 1)
    out.append(("Fins", f, vs, "root", "frame"))
    # ---- the pylon under its belly (hazard-striped), ending in the ball joint the claw hangs from
    f = Field("Pylon")
    f.add(RoundBox(C + v3((0, 0.03, -0.225)), (0.075, 0.12, 0.05), 0.03))
    f.add(Sphere(PIVOT, 0.036), k=0.012)
    for i in range(6):
        f.paint(RoundBox(C + v3((0, -0.07 + 0.04 * i, -0.235)), (0.2, 0.011, 0.07), 0.0, R=euler(0.6, 0, 0)), 4 if i % 2 else 1)
    out.append(("Pylon", f, vs, "root", "frame"))
    # ---- the claw: a hub on the ball joint, four hooked fingers wrapped round the bomb's top half
    f = Field("Claw")
    f.add(RoundCone(PIVOT, HUB, 0.026, 0.03))                                        # the rod down from the ball joint
    f.add(Torus(PIVOT + v3((0, 0, -0.045)), 0.03, 0.01), k=0.004)
    f.add(Cylinder(HUB, 0.07, 0.05, rr=0.016), k=0.01)
    f.paint(Cylinder(HUB, 0.077, 0.016), 1)
    for a in FINGERS:
        u = v3((math.cos(a), math.sin(a), 0))
        def sp(th, r):                                                                 # a point over the bomb at polar angle th
            return B + (u * math.sin(th) + v3((0, 0, 1)) * math.cos(th)) * r
        pts = [HUB + v3((0, 0, -0.01)) + u * 0.052, sp(math.radians(28), RB + 0.03), sp(math.radians(62), RB + 0.028),
               sp(math.radians(92), RB + 0.024), sp(math.radians(110), RB + 0.004)]
        rads = [0.024, 0.023, 0.02, 0.017, 0.011]
        for i in range(len(pts) - 1):
            f.add(RoundCone(pts[i], pts[i + 1], rads[i], rads[i + 1]), k=0.008)
        for i in (1, 2):
            f.add(Sphere(pts[i], 0.028), k=0.006)
    out.append(("Claw", f, vs, "bomb", "frame"))
    # ---- the bomb: a round black iron ball, grooved along three seams (an equator and two meridians) that glow cyan
    f = Field("Bomb")
    f.add(Sphere(B, RB))
    f.sub(Torus(B, RB, 0.013), k=0.004)
    f.sub(Torus(B, RB, 0.012, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004)
    f.sub(Torus(B, RB, 0.012, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.004)
    for a in FINGERS:                                                                  # rivets either side of each finger
        for da in (-0.36, 0.36):
            for e in (0.16, -0.16):
                f.add(Sphere(B + v3((math.cos(a + da) * math.cos(e), math.sin(a + da) * math.cos(e), math.sin(e))) * RB, 0.012), k=0.004)
    out.append(("Bomb", f, vs, "bomb", "iron"))
    f = Field("Seams")
    f.add(Torus(B, RB - 0.004, 0.0085))
    f.add(Torus(B, RB - 0.004, 0.0078, R=rot_from_axes(z_axis=(1, 0, 0))))
    f.add(Torus(B, RB - 0.004, 0.0078, R=rot_from_axes(z_axis=(0, 1, 0))))
    out.append(("Seams", f, vs, "bomb", "glow"))
    # ---- the fuse: a chrome cap on the bomb's front, a short wick, its glowing spark
    Rf = rot_from_axes(z_axis=FUSE_D)
    f = Field("Fuse")
    f.add(Cylinder(B + FUSE_D * (RB + 0.008), 0.046, 0.05, rr=0.012, R=Rf))
    f.add(Torus(B + FUSE_D * (RB + 0.032), 0.04, 0.011, R=Rf), k=0.005)
    out.append(("Fuse", f, vs, "bomb", "chrome"))
    wick0 = B + FUSE_D * (RB + 0.03)
    wick1 = B + FUSE_D * (RB + 0.072) + v3((0, 0, 0.014))
    f = Field("Wick")
    f.add(RoundCone(wick0, wick1, 0.011, 0.009))
    out.append(("Wick", f, vs, "bomb", "rubber"))
    f = Field("FuseGlow")
    f.add(Sphere(wick1, 0.03))
    for d in ((0, -1, 0.3), (0.8, -0.4, 0.4), (-0.8, -0.4, 0.4), (0, -0.3, 1.0), (0.5, -0.6, -0.6), (-0.5, -0.6, -0.6), (0, 0.3, 0.6)):
        dd = norm(d)
        f.add(RoundCone(wick1, wick1 + dd * 0.065, 0.014, 0.002), k=0.007)
    out.append(("FuseGlow", f, vs, "bomb", "glow"))
    return out


def clips(arm):
    down = Vector((0, 0, -1))
    def extra(t, aims):
        w = 2 * math.pi * t
        # the eye scans left and right
        look = 0.28 * math.sin(w) + 0.08 * math.sin(3 * w)
        aims["eye"] = Vector((math.sin(look), -math.cos(look), -0.1))
        # the bomb hangs plumb from its ball joint and sways a little (fore and aft twice a loop, side to side once)
        sw = Quaternion(Vector((1, 0, 0)), 0.12 * math.sin(2 * w + 0.7)) @ Quaternion(Vector((0, 1, 0)), 0.08 * math.sin(w + 1.9))
        aims["bomb"] = sw @ down
    ra.hover(arm, "Fly", frames=48, bob=0.045, tilt=0.1, roll=0.06,
             spin_bones=("rotor.FL", "rotor.FR", "rotor.BR", "rotor.BL"), spin_turns=6, extra=extra)
