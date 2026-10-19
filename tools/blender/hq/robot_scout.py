"""Scout Drone, HQ: a fast hovering eye. A white-and-gunmetal sphere with one big glowing red eye under an armoured brow,
two ducted rotors on struts, an orange stripe round its middle, a thruster glowing under it and a whip antenna.
Faces -Y, Z up; hovers about 0.85 model units up (the game adds a hover bob of its own only to v2 models).
"""
import math
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3
import robot_anim as ra
from mathutils import Vector, Quaternion

ROOT_NAME = "Scout"
GLB_NAME = "scout"
TEX_PREFIX = "scout"

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
C = v3((0, 0, 0.86))                 # body centre
R = 0.23                             # body radius
ROT_L = v3((0.43, 0.03, 0.93))       # rotor hubs
ROT_R = v3((-0.43, 0.03, 0.93))

BONES = [
    ("root", tuple(C), tuple(C + v3((0, 0, 0.1))), None),
    ("eye", tuple(C + v3((0, -0.17, 0))), tuple(C + v3((0, -0.3, 0))), "root"),
    ("rotor.L", tuple(ROT_L), tuple(ROT_L + v3((0, 0, 0.08))), "root"),
    ("rotor.R", tuple(ROT_R), tuple(ROT_R + v3((0, 0, 0.08))), "root"),
    ("antenna", tuple(C + v3((0.06, 0.12, 0.2))), tuple(C + v3((0.1, 0.24, 0.42))), "root"),
]

MATS = {
    "armor": ("armor", dict(name="RB_ScoutArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, (0.26, 0.28, 0.32), 0.42)], seams=[2])),
    "frame": ("gunmetal", dict(name="RB_ScoutFrame", labels=[(2, (0.1, 0.1, 0.11), 0.6)], seams=[2])),
    "chrome": ("chrome", dict(name="RB_ScoutChrome")),
    "socket": ("lens_socket", dict(name="RB_ScoutSocket")),
    "rubber": ("rubber", dict(name="RB_ScoutBlade", base=(0.14, 0.15, 0.17))),
    "glow": ("glow", dict(name="RB_ScoutGlow", col=(1.0, 0.25, 0.1))),
}
GLOW_RED = (1.0, 0.22, 0.08)
GLOW = {"Eye": (GLOW_RED, 1.3, 0.5), "Thruster": ((1.0, 0.55, 0.15), 1.2, 0.5), "AntennaTip": (GLOW_RED, 1.2, 0.5)}

LOW_TARGETS = {"Body": 700, "Brow": 160, "EyeRing": 120, "Pupil": 40, "Eye": 90, "Struts": 220, "Ducts": 360,
               "BladesL": 90, "BladesR": 90, "Belly": 160, "Thruster": 40, "Antenna": 50, "AntennaTip": 30}
FACE_Y = rot_from_axes(z_axis=(0, -1, 0))


def parts(fine=False):
    vx = 0.0045 if fine else 0.008
    vs = 0.0035 if fine else 0.007
    out = []
    f = Field("Body")
    f.add(Sphere(C, R))
    f.sub(Sphere(C + v3((0, -0.2, 0.0)), 0.13), k=0.015)                     # eye socket
    f.paint(RoundBox(C + v3((0, 0, -0.22)), (0.4, 0.4, 0.17)), 3)            # gunmetal lower part
    f.paint(RoundBox(C + v3((0, 0, 0.13)), (0.4, 0.4, 0.016)), 1)            # orange band above the equator
    f.paint(RoundBox(C + v3((0, 0, 0.115)), (0.4, 0.4, 0.003)), 2)
    f.paint(RoundBox(C + v3((0, 0, 0.145)), (0.4, 0.4, 0.003)), 2)
    f.paint(RoundBox(C + v3((0, 0.0, 0.0)), (0.003, 0.4, 0.4)), 2)           # meridian seam
    for sx in (-1, 1):                                                        # side vents
        f.paint(RoundBox(C + v3((sx * 0.22, 0.04, 0.0)), (0.03, 0.05, 0.045), 0.01), 3)
    out.append(("Body", f, vx, "root", "armor"))
    f = Field("Brow")                                                         # armoured brow over the eye: a frown
    for sx in (-1, 1):                                                        # two angled brow plates: a frown
        f.add(RoundBox(C + v3((sx * 0.065, -0.2, 0.125)), (0.075, 0.035, 0.02), 0.018,
                       R=rot_from_axes(x_axis=(1, 0, sx * 0.38), y_axis=(0, -1, -0.45))), k=0.015)
    out.append(("Brow", f, vs, "root", "armor"))
    f = Field("EyeRing")
    f.add(Torus(C + v3((0, -0.19, 0.0)), 0.115, 0.024, R=FACE_Y))
    for i in range(8):
        a = i * math.pi / 4
        f.add(Sphere(C + v3((0.115 * math.cos(a), -0.215, 0.115 * math.sin(a))), 0.011), k=0.004)
    out.append(("EyeRing", f, vs, "root", "frame"))
    f = Field("Eye")
    f.add(Ellipsoid(C + v3((0, -0.17, 0.0)), (0.1, 0.06, 0.1)))
    out.append(("Eye", f, vs, "eye", "glow"))
    f = Field("Pupil")                                                       # a dark round pupil in the glowing iris
    f.add(Ellipsoid(C + v3((0, -0.226, 0.0)), (0.036, 0.01, 0.036)))
    out.append(("Pupil", f, vs * 0.8, "eye", "socket"))
    f = Field("Struts")
    for s, hub in (("L", ROT_L), ("R", ROT_R)):
        sx = 1 if s == "L" else -1
        f.add(RoundCone(C + v3((sx * 0.18, 0.02, 0.03)), hub + v3((-sx * 0.09, 0, -0.02)), 0.04, 0.026), k=0.01)
        f.add(Cylinder(hub + v3((0, 0, -0.045)), 0.03, 0.06, rr=0.01), k=0.01)
    out.append(("Struts", f, vs, "root", "frame"))
    f = Field("Ducts")                                                       # ducted fans round the rotors
    for hub in (ROT_L, ROT_R):
        f.add(Torus(hub, 0.13, 0.03))
        f.add(Torus(hub + v3((0, 0, -0.03)), 0.13, 0.022), k=0.015)
        for i in range(3):
            a = i * 2 * math.pi / 3 + 0.5
            f.add(RoundCone(hub + v3((0, 0, -0.045)), hub + v3((0.12 * math.cos(a), 0.12 * math.sin(a), -0.03)), 0.008, 0.008), k=0.006)
        f.paint(RoundBox(hub + v3((0, 0, 0.012)), (0.3, 0.3, 0.012)), 1)
    out.append(("Ducts", f, vs, "root", "armor"))
    for s, hub in (("L", ROT_L), ("R", ROT_R)):
        f = Field("Blades" + s)
        f.add(Cylinder(hub, 0.03, 0.03, rr=0.01))
        for i in range(3):
            a = i * 2 * math.pi / 3
            d = v3((math.cos(a), math.sin(a), 0))
            mid = hub + d * 0.06
            f.add(RoundBox(mid, (0.06, 0.017, 0.004), 0.004,
                           R=rot_from_axes(x_axis=d, z_axis=(0, 0, 1)) @ rot_from_axes(x_axis=(1, 0, 0), y_axis=(0, math.cos(0.4), math.sin(0.4)))), k=0.004)
        out.append(("Blades" + s, f, 0.0028 if fine else 0.006, "rotor." + s, "rubber"))
    f = Field("Belly")                                                       # thruster nozzle underneath
    f.add(Cylinder(C + v3((0, 0.02, -0.235)), 0.06, 0.05, rr=0.012))
    f.add(Cylinder(C + v3((0, 0.02, -0.265)), 0.075, 0.03, rr=0.01), k=0.01)
    f.sub(Cylinder(C + v3((0, 0.02, -0.29)), 0.05, 0.04), k=0.005)
    out.append(("Belly", f, vs, "root", "frame"))
    f = Field("Thruster")
    f.add(Cylinder(C + v3((0, 0.02, -0.27)), 0.048, 0.012, rr=0.004))
    out.append(("Thruster", f, vs, "root", "glow"))
    f = Field("Antenna")
    a0, a1 = C + v3((0.06, 0.12, 0.2)), C + v3((0.1, 0.24, 0.42))
    f.add(Cylinder(a0, 0.028, 0.03, rr=0.008))
    f.add(RoundCone(a0, a1, 0.011, 0.007), k=0.005)
    out.append(("Antenna", f, vs, "antenna", "frame"))
    f = Field("AntennaTip")
    f.add(Sphere(a1, 0.022))
    out.append(("AntennaTip", f, vs, "antenna", "glow"))
    return out


def clips(arm):
    def extra(t, aims):
        # the eye glances left and right, the antenna trails the bob
        look = 0.22 * math.sin(2 * math.pi * t) + 0.07 * math.sin(6 * math.pi * t)
        aims["eye"] = Vector((math.sin(look), -math.cos(look), -0.08))
        aims["antenna"] = Vector((0.15 + 0.08 * math.sin(2 * math.pi * t + 1.4), 0.5 + 0.15 * math.sin(4 * math.pi * t), 1.0))
    ra.hover(arm, "Fly", frames=48, bob=0.045, tilt=0.12, roll=0.06, spin_bones=("rotor.L", "rotor.R"), spin_turns=6, extra=extra)
