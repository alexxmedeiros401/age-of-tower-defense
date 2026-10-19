"""Repair Drone, HQ: the Bronze Age's field medic. A plump white hover-drone with green markings: a rounded hull with a
green cross on its back, a gunmetal belly with a glowing green repair lens, four rotors in ducts on short arms, a
camera eye under a visor in front, and two folding repair arms underneath (a welding torch with a green flame and a
three-fingered gripper) that twitch as it flies. In game it heals the robots round it (enemies.json "heal"): the lens
flares green on each pulse. Faces -Y, Z up, hovers about 0.8 model units up; model_scale 0.9.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3, norm
import robot_anim as ra
from mathutils import Vector, Quaternion

ROOT_NAME = "RepairDrone"
GLB_NAME = "repair_drone"
TEX_PREFIX = "repair_drone"

GREEN = (0.16, 0.66, 0.3)
SEAM = (0.2, 0.2, 0.22)
GLOW_GREEN = (0.35, 1.0, 0.5)
C = v3((0, 0, 0.8))                  # hull centre
ROTORS = {"FL": v3((0.3, -0.24, 0.9)), "FR": v3((-0.3, -0.24, 0.9)), "BL": v3((0.3, 0.24, 0.9)), "BR": v3((-0.3, 0.24, 0.9))}
DUCT_R = 0.12
ARM_L = (v3((0.08, -0.06, 0.66)), v3((0.13, -0.16, 0.55)), v3((0.12, -0.24, 0.5)))     # shoulder, elbow, tool (rest)
ARM_R = (v3((-0.08, -0.06, 0.66)), v3((-0.13, -0.16, 0.55)), v3((-0.12, -0.24, 0.5)))

BONES = [
    ("root", tuple(C), tuple(C + v3((0, 0, 0.1))), None),
    ("eye", tuple(C + v3((0, -0.2, 0.0))), tuple(C + v3((0, -0.32, 0.0))), "root"),
    ("lens", tuple(C + v3((0, 0, -0.14))), tuple(C + v3((0, 0, -0.24))), "root"),
    ("arm.L", tuple(ARM_L[0]), tuple(ARM_L[1]), "root"),
    ("tool.L", tuple(ARM_L[1]), tuple(ARM_L[2]), "arm.L"),
    ("arm.R", tuple(ARM_R[0]), tuple(ARM_R[1]), "root"),
    ("tool.R", tuple(ARM_R[1]), tuple(ARM_R[2]), "arm.R"),
]
for k, p in ROTORS.items():
    BONES.append(("rotor." + k, tuple(p), tuple(p + v3((0, 0, 0.08))), "root"))

MATS = {
    "armor": ("armor", dict(name="RB_RepairArmor", labels=[(1, GREEN, 0.35), (2, SEAM, 0.6), (3, (0.26, 0.28, 0.32), 0.42)], seams=[2])),
    "frame": ("gunmetal", dict(name="RB_RepairFrame", labels=[(1, GREEN, 0.35), (2, (0.1, 0.1, 0.11), 0.6)], seams=[2])),
    "chrome": ("chrome", dict(name="RB_RepairChrome")),
    "socket": ("lens_socket", dict(name="RB_RepairSocket")),
    "rubber": ("rubber", dict(name="RB_RepairBlade", base=(0.14, 0.15, 0.17))),
    "glow": ("glow", dict(name="RB_RepairGlow", col=GLOW_GREEN)),
}
GLOW = {"Eye": (GLOW_GREEN, 1.3, 0.5), "Lens": (GLOW_GREEN, 1.3, 0.5), "Flame": ((0.5, 1.0, 0.6), 1.4, 0.5),
        "Lights": (GLOW_GREEN, 1.2, 0.5)}
LOW_TARGETS = {"Hull": 760, "Belly": 300, "Visor": 140, "EyeRing": 90, "Eye": 50, "LensRing": 110, "Lens": 60,
               "Struts": 260, "Ducts": 440, "Lights": 60, "ArmL": 180, "ArmR": 180, "Torch": 120, "Gripper": 200, "Flame": 40}
for k in ROTORS:
    LOW_TARGETS["Blades" + k] = 80
FACE_Y = rot_from_axes(z_axis=(0, -1, 0))


def parts(fine=False):
    vx = 0.0042 if fine else 0.0075
    vs = 0.0032 if fine else 0.0065
    out = []
    # ---- the hull: a plump rounded body, a green cross on its back, a green band, seams
    f = Field("Hull")
    f.add(Ellipsoid(C + v3((0, 0.0, 0.03)), (0.24, 0.27, 0.15)))
    f.add(RoundBox(C + v3((0, 0.02, -0.03)), (0.2, 0.23, 0.08), 0.06), k=0.05)
    f.sub(Sphere(C + v3((0, -0.25, 0.0)), 0.085), k=0.012)                       # the eye socket
    f.paint(RoundBox(C + v3((0, 0.02, 0.2)), (0.035, 0.13, 0.1), 0.005), 1)        # the green cross on its back
    f.paint(RoundBox(C + v3((0, 0.02, 0.2)), (0.13, 0.035, 0.1), 0.005), 1)
    f.paint(RoundBox(C + v3((0, 0, -0.035)), (0.4, 0.4, 0.016)), 1)               # a green band round its middle
    f.paint(RoundBox(C + v3((0, 0, -0.055)), (0.4, 0.4, 0.003)), 2)
    f.paint(RoundBox(C + v3((0, 0, -0.015)), (0.4, 0.4, 0.003)), 2)
    f.paint(RoundBox(C + v3((0, 0.0, 0.0)), (0.003, 0.5, 0.4)), 2)               # the hull's seam
    for sx in (-1, 1):
        f.paint(RoundBox(C + v3((sx * 0.2, 0.12, 0.04)), (0.03, 0.05, 0.03), 0.01), 3)   # vents
    out.append(("Hull", f, vx, "root", "armor"))
    f = Field("Belly")
    f.add(Ellipsoid(C + v3((0, 0.02, -0.1)), (0.19, 0.21, 0.07)))
    f.sub(Cylinder(C + v3((0, 0.0, -0.17)), 0.07, 0.06), k=0.01)
    for i in range(4):
        f.paint(RoundBox(C + v3((0, 0.05 + 0.035 * i, -0.13)), (0.11, 0.007, 0.05), 0.003), 2)     # cooling slats
    out.append(("Belly", f, vx, "root", "frame"))
    f = Field("LensRing")
    f.add(Torus(C + v3((0, 0.0, -0.155)), 0.07, 0.016))
    out.append(("LensRing", f, vs, "lens", "frame"))
    f = Field("Lens")
    f.add(Ellipsoid(C + v3((0, 0.0, -0.165)), (0.058, 0.058, 0.03)))
    out.append(("Lens", f, vs, "lens", "glow"))
    # ---- the camera eye under a visor
    f = Field("Visor")
    f.add(Ellipsoid(C + v3((0, -0.215, 0.07)), (0.12, 0.07, 0.035)))
    f.sub(Ellipsoid(C + v3((0, -0.2, 0.04)), (0.1, 0.08, 0.035)), k=0.01)
    out.append(("Visor", f, vs, "root", "armor"))
    f = Field("EyeRing")
    f.add(Torus(C + v3((0, -0.24, 0.0)), 0.068, 0.014, R=FACE_Y))
    out.append(("EyeRing", f, vs, "eye", "socket"))
    f = Field("Eye")
    f.add(Ellipsoid(C + v3((0, -0.235, 0.0)), (0.055, 0.03, 0.055)))
    out.append(("Eye", f, vs, "eye", "glow"))
    # ---- rotor arms, ducts, blades; running lights
    f = Field("Struts")
    for k, p in ROTORS.items():
        base = C + v3((p[0] * 0.45, p[1] * 0.55, 0.05))
        f.add(RoundCone(base, p - norm(v3((p[0], p[1], 0))) * DUCT_R, 0.026, 0.02), k=0.01)
        f.add(Cylinder(p, 0.026, 0.05, rr=0.008), k=0.006)
    out.append(("Struts", f, vs, "root", "frame"))
    f = Field("Ducts")
    for k, p in ROTORS.items():
        f.add(Torus(p, DUCT_R, 0.024))
        f.paint(Torus(p + v3((0, 0, 0.012)), DUCT_R, 0.026), 1)
    out.append(("Ducts", f, vs, "root", "armor"))
    f = Field("Lights")
    for k, p in ROTORS.items():
        f.add(Sphere(p + norm(v3((p[0], p[1], 0))) * (DUCT_R + 0.022), 0.012))
    out.append(("Lights", f, vs, "root", "glow"))
    for k, p in ROTORS.items():
        f = Field("Blades" + k)
        for i in range(3):
            a = i * 2 * math.pi / 3 + (0.4 if k in ("FL", "BR") else 0.0)
            d = v3((math.cos(a), math.sin(a), 0))
            f.add(RoundBox(p + d * 0.055 + v3((0, 0, 0.012)), (0.05, 0.016, 0.003), 0.003,
                           R=rot_from_axes(x_axis=d, z_axis=(0, 0, 1)) @ np.array([[1, 0, 0], [0, math.cos(0.3), -math.sin(0.3)], [0, math.sin(0.3), math.cos(0.3)]])), k=0.004)
        out.append(("Blades" + k, f, vs, "rotor." + k, "rubber"))
    # ---- the repair arms: a welding torch (left) and a gripper (right), folded under its chin
    for side, (a0, a1, a2), tool in (("L", ARM_L, "Torch"), ("R", ARM_R, "Gripper")):
        f = Field("Arm" + side)
        f.add(Sphere(a0, 0.028))
        f.add(RoundCone(a0, a1, 0.02, 0.017), k=0.006)
        f.add(Sphere(a1, 0.022), k=0.006)
        out.append(("Arm" + side, f, vs, "arm." + side, "frame"))
        f = Field(tool)
        ax = norm(a2 - a1)
        if tool == "Torch":
            f.add(RoundCone(a1, a2, 0.016, 0.012))
            f.add(Cylinder(a2 + ax * 0.005, 0.016, 0.02, rr=0.004, R=rot_from_axes(z_axis=ax)), k=0.004)
            f.add(RoundCone(a2, a2 + ax * 0.04, 0.009, 0.005), k=0.003)
            f.paint(Cylinder(a1 + (a2 - a1) * 0.5, 0.03, 0.03, R=rot_from_axes(z_axis=ax)), 1)
        else:
            f.add(RoundCone(a1, a2, 0.016, 0.014))
            f.add(Sphere(a2, 0.022), k=0.006)
            side_v = norm(np.cross(ax, v3((0, 0, 1))))
            up_v = norm(np.cross(side_v, ax))
            for ang in (0.0, 2.1, 4.2):
                d = side_v * math.cos(ang) + up_v * math.sin(ang)
                f1 = a2 + ax * 0.015 + d * 0.016
                f2 = f1 + ax * 0.03 + d * 0.012
                f3 = f2 + ax * 0.02 - d * 0.014
                f.add(RoundCone(f1, f2, 0.007, 0.006), k=0.003)
                f.add(RoundCone(f2, f3, 0.006, 0.004), k=0.003)
        out.append((tool, f, vs, "tool." + side, "chrome" if tool == "Gripper" else "frame"))
    f = Field("Flame")
    ax = norm(ARM_L[2] - ARM_L[1])
    tip = ARM_L[2] + ax * 0.045
    f.add(RoundCone(tip, tip + ax * 0.05, 0.008, 0.002))
    out.append(("Flame", f, vs, "tool.L", "glow"))
    return out


def clips(arm):
    a0, a1, a2 = (Vector(p) for p in ARM_L)
    b0, b1, b2 = (Vector(p) for p in ARM_R)
    def extra(t, aims):
        # the eye scans, the repair arms twitch and reach a little, the lens hangs steady
        look = 0.25 * math.sin(2 * math.pi * t) + 0.08 * math.sin(6 * math.pi * t)
        aims["eye"] = Vector((math.sin(look), -math.cos(look), -0.1))
        for (s0, s1, s2), sd, ph in (((a0, a1, a2), "L", 0.0), ((b0, b1, b2), "R", 0.5)):
            w = math.sin(2 * math.pi * (2 * t + ph))
            up = (s1 - s0).normalized() + Vector((0, -0.25 * max(0.0, w), 0.15 * w))
            aims["arm." + sd] = up
            aims["tool." + sd] = (s2 - s1).normalized() + Vector((0, -0.35 * max(0.0, w), 0.2 * w))
    ra.hover(arm, "Fly", frames=48, bob=0.04, tilt=0.1, roll=0.05,
             spin_bones=("rotor.FL", "rotor.FR", "rotor.BR", "rotor.BL"), spin_turns=7, extra=extra)
