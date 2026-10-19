"""Carrier, HQ: a hovering orange drone barge with three Scout drones docked on its back (it releases them when it is
destroyed). A chunky orange hull with white panels and black hazard stripes, a red sensor eye in its nose, four
thrusters glowing underneath, side fins with marker lights and an antenna mast. Faces -Y, Z up (model_scale 0.9).
"""
import math
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3
import robot_anim as ra
from mathutils import Vector

ROOT_NAME = "Carrier"
GLB_NAME = "carrier"
TEX_PREFIX = "carrier"

ORANGE = (0.98, 0.5, 0.12)
WHITE = (0.93, 0.93, 0.9)
SEAM = (0.22, 0.14, 0.08)
BLACK = (0.08, 0.08, 0.09)
HZ = 0.58                                  # hull centre height (it hovers)
PODS = [v3((0, -0.27, HZ + 0.2)), v3((0.0, 0.03, HZ + 0.2)), v3((0, 0.33, HZ + 0.2))]
THR = [v3((sx * 0.3, sy * 0.38, HZ - 0.13)) for sx in (-1, 1) for sy in (-1, 1)]

BONES = [("root", (0, 0, HZ), (0, 0, HZ + 0.15), None),
         ("antenna", (0.22, 0.48, HZ + 0.12), (0.26, 0.56, HZ + 0.52), "root")]
for i, p in enumerate(PODS):
    BONES.append(("pod%d" % i, tuple(p), tuple(p + v3((0, -0.1, 0))), "root"))

MATS = {
    "hull": ("armor", dict(name="RB_CarrierHull", base=ORANGE, metal=(0.78, 0.76, 0.74), labels=[(1, WHITE, 0.32), (2, SEAM, 0.6), (3, BLACK, 0.4)], seams=[2], wear=1.1)),
    "pod": ("armor", dict(name="RB_CarrierPod", labels=[(1, ORANGE, 0.35), (2, (0.2, 0.2, 0.22), 0.6), (3, (0.26, 0.28, 0.32), 0.42)], seams=[2])),
    "frame": ("gunmetal", dict(name="RB_CarrierFrame", labels=[(1, ORANGE, 0.35), (2, (0.1, 0.1, 0.11), 0.6)], seams=[2])),
    "socket": ("lens_socket", dict(name="RB_CarrierSocket")),
    "glow": ("glow", dict(name="RB_CarrierGlow", col=(1.0, 0.25, 0.1))),
}
GLOW_RED = (1.0, 0.22, 0.08)
GLOW = {"Eye": (GLOW_RED, 1.3, 0.5), "Thrusters": ((1.0, 0.55, 0.15), 1.3, 0.5),
        "Lights": ((1.0, 0.3, 0.1), 1.4, 0.5), "AntennaTip": (GLOW_RED, 1.3, 0.5)}
LOW_TARGETS = {"Hull": 900, "Deck": 380, "Nose": 140, "Eye": 60, "ThrusterPods": 360, "Thrusters": 80, "Fins": 200,
               "Lights": 50, "Antenna": 60, "AntennaTip": 30}
for i in range(3):
    LOW_TARGETS["Pod%d" % i] = 260
FACE_Y = rot_from_axes(z_axis=(0, -1, 0))


def parts(fine=False):
    vx = 0.005 if fine else 0.009
    vs = 0.0038 if fine else 0.0075
    out = []
    f = Field("Hull")
    f.add(RoundBox((0, 0.04, HZ), (0.36, 0.5, 0.1), 0.08))
    f.add(RoundBox((0, -0.42, HZ - 0.01), (0.27, 0.12, 0.085), 0.07), k=0.06)          # tapering nose
    f.add(RoundBox((0, 0.04, HZ - 0.07), (0.3, 0.44, 0.06), 0.05), k=0.04)             # keel
    f.sub(Sphere((0, -0.56, HZ + 0.0), 0.075), k=0.012)                                 # sensor socket
    for sx in (-1, 1):                                                                  # white side panels
        f.paint(RoundBox((sx * 0.36, 0.04, HZ + 0.01), (0.06, 0.34, 0.05), 0.02), 1)
    for i in range(9):                                                                  # hazard band round the stern
        y = 0.5 - 0.0
        f.paint(RoundBox((-0.32 + i * 0.08, 0.53, HZ), (0.03, 0.1, 0.2), 0.0,
                         R=rot_from_axes(x_axis=(math.cos(0.6), 0, math.sin(0.6)), y_axis=(0, 1, 0))), 3 if i % 2 == 0 else 0)
    f.paint(RoundBox((0, 0.04, HZ + 0.02), (0.5, 0.004, 0.2)), 2)
    f.paint(RoundBox((0, 0.04, HZ - 0.04), (0.5, 0.7, 0.004)), 2)
    out.append(("Hull", f, vx, "root", "hull"))
    f = Field("Deck")                                                                   # gunmetal deck with three cradles
    f.add(RoundBox((0, 0.04, HZ + 0.1), (0.24, 0.46, 0.025), 0.02))
    for p in PODS:
        f.add(Torus(p + v3((0, 0, -0.085)), 0.15, 0.028), k=0.01)
        for i in range(3):
            a = i * 2 * math.pi / 3 + 0.3
            f.add(RoundCone(p + v3((0.15 * math.cos(a), 0.15 * math.sin(a), -0.085)), p + v3((0.13 * math.cos(a), 0.13 * math.sin(a), -0.15)), 0.014, 0.014), k=0.006)
    for i in range(6):
        f.paint(RoundBox((0, -0.4 + i * 0.16, HZ + 0.125), (0.3, 0.005, 0.01)), 2)
    out.append(("Deck", f, vs, "root", "frame"))
    f = Field("Nose")
    f.add(Torus((0, -0.545, HZ), 0.082, 0.02, R=FACE_Y))
    f.add(RoundBox((0, -0.5, HZ + 0.07), (0.1, 0.05, 0.02), 0.015, R=rot_from_axes(x_axis=(1, 0, 0), y_axis=(0, -1, -0.5))), k=0.01)
    out.append(("Nose", f, vs, "root", "frame"))
    f = Field("Eye")
    f.add(Ellipsoid((0, -0.53, HZ), (0.07, 0.04, 0.07)))
    out.append(("Eye", f, vs, "root", "glow"))
    f = Field("ThrusterPods")
    for t in THR:
        f.add(Cylinder(t + v3((0, 0, 0.03)), 0.075, 0.09, rr=0.02))
        f.add(Torus(t + v3((0, 0, -0.01)), 0.07, 0.016), k=0.008)
        f.sub(Cylinder(t + v3((0, 0, -0.03)), 0.052, 0.05), k=0.005)
    out.append(("ThrusterPods", f, vs, "root", "frame"))
    f = Field("Thrusters")
    for t in THR:
        f.add(Cylinder(t + v3((0, 0, -0.012)), 0.05, 0.012, rr=0.004))
    out.append(("Thrusters", f, vs, "root", "glow"))
    f = Field("Fins")
    for sx in (-1, 1):
        f.add(RoundBox((sx * 0.46, 0.25, HZ + 0.02), (0.08, 0.16, 0.018), 0.015,
                       R=rot_from_axes(x_axis=(1, 0, sx * 0.25), y_axis=(0, 1, 0))))
        f.add(RoundBox((sx * 0.44, 0.38, HZ + 0.1), (0.015, 0.06, 0.08), 0.012), k=0.01)
        f.paint(RoundBox((sx * 0.5, 0.25, HZ + 0.04), (0.06, 0.18, 0.05)), 1)
    out.append(("Fins", f, vs, "root", "hull"))
    f = Field("Lights")
    for sx in (-1, 1):
        f.add(Sphere((sx * 0.535, 0.12, HZ + 0.035), 0.022))
        f.add(Sphere((sx * 0.44, 0.43, HZ + 0.17), 0.02))
    out.append(("Lights", f, vs, "root", "glow"))
    a0, a1 = v3((0.22, 0.48, HZ + 0.12)), v3((0.26, 0.56, HZ + 0.52))
    f = Field("Antenna")
    f.add(Cylinder(a0, 0.03, 0.04, rr=0.01))
    f.add(RoundCone(a0, a1, 0.012, 0.008), k=0.006)
    out.append(("Antenna", f, vs, "antenna", "frame"))
    f = Field("AntennaTip")
    f.add(Sphere(a1, 0.024))
    out.append(("AntennaTip", f, vs, "antenna", "glow"))
    # the three docked scouts: white-and-gunmetal spheres with an orange band, each on its own bone
    for i, p in enumerate(PODS):
        f = Field("Pod%d" % i)
        f.add(Sphere(p, 0.13))
        f.sub(Sphere(p + v3((0, -0.12, 0.0)), 0.07), k=0.01)
        f.paint(RoundBox(p + v3((0, 0, -0.13)), (0.3, 0.3, 0.09)), 3)
        f.paint(RoundBox(p + v3((0, 0, 0.065)), (0.3, 0.3, 0.012)), 1)
        f.paint(RoundBox(p, (0.003, 0.3, 0.3)), 2)
        out.append(("Pod%d" % i, f, vs, "pod%d" % i, "pod"))
    for i, p in enumerate(PODS):
        f = Field("PodRing%d" % i)
        f.add(Torus(p + v3((0, -0.105, 0.0)), 0.065, 0.015, R=FACE_Y))
        out.append(("PodRing%d" % i, f, vs, "pod%d" % i, "frame"))
        f = Field("PodEye%d" % i)
        f.add(Ellipsoid(p + v3((0, -0.1, 0.0)), (0.055, 0.03, 0.055)))
        out.append(("PodEye%d" % i, f, vs, "pod%d" % i, "glow"))
    return out


for i in range(3):
    GLOW["PodEye%d" % i] = (GLOW_RED, 1.3, 0.5)
    LOW_TARGETS["PodRing%d" % i] = 50
    LOW_TARGETS["PodEye%d" % i] = 40


def clips(arm):
    def extra(t, aims):
        for i in range(3):
            ph = 2 * math.pi * (t * 2 + i * 0.33)
            aims["pod%d" % i] = Vector((0.18 * math.sin(ph), -1.0, 0.1 * math.sin(ph + 1.0)))
        aims["antenna"] = Vector((0.1 + 0.08 * math.sin(2 * math.pi * t + 1.4), 0.2 + 0.1 * math.sin(4 * math.pi * t), 1.0))
    ra.hover(arm, "Fly", frames=48, bob=0.04, tilt=0.05, roll=0.045, extra=extra)
