"""Siege Crawler, HQ: the Bronze Age boss. A walking fortress on six spider legs: a long armoured hull in white plate
with cobalt and gold bands, a cyan glass dome on top in a ringed mount (its brain, glowing), a heavy cannon slung under
its nose with a glowing muzzle, a row of red sensor eyes across its brow, twin exhaust stacks at the back and a hatch
in its back that swings open when it lets out Shield Bots. Each leg: a ball hip on the hull, an armoured upper leg up
to a high chrome knee and a long lower leg down to a spiked foot.
Clips: Walk (a tripod gait: three legs swing while three carry it; a slow, heavy crawl) and Summon (it rears its front
up, the hatch swings open and the dome flares, its legs still walking). Faces -Y, Z up, model_scale 1.0.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3, norm
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser, two_bone, bone_len

ROOT_NAME = "SiegeCrawler"
GLB_NAME = "siege_crawler"
TEX_PREFIX = "siege_crawler"
WALK_STEP = 0.5            # each foot's stride: the body moves 2 * WALK_STEP per loop of WALK_FRAMES
WALK_FRAMES = 48           # (2 s at 24 fps): walk_speed = WALK_STEP * model_scale per second

BLUE = (0.12, 0.3, 0.74)
GOLD = (0.86, 0.62, 0.2)
SEAM = (0.2, 0.2, 0.22)
BLACK = (0.08, 0.08, 0.09)
CYAN = (0.3, 0.88, 1.0)
RED = (1.0, 0.22, 0.08)

HULL_C = v3((0.0, 0.05, 1.3))
LEG_Y = (-0.72, 0.06, 0.84)                 # front, middle, back
LEGS = {}
for i, y in enumerate(LEG_Y):
    for s, sx in (("L", 1), ("R", -1)):
        n = "%s%d" % (s, i + 1)
        spread = (-0.18, 0.0, 0.18)[i]
        LEGS[n] = {
            "hip": v3((sx * 0.62, y, 1.24)),
            "knee": v3((sx * 1.12, y + spread * 1.4, 1.86)),
            "foot": v3((sx * 1.42, y + spread * 2.6, 0.06)),
            "sx": sx,
        }
TRIPOD_A = ("L1", "R2", "L3")               # these swing while the others carry it, then the other way round

BONES = [
    ("root", tuple(HULL_C), tuple(HULL_C + v3((0, 0, 0.2))), None),
    ("dome", (0, 0.12, 1.66), (0, 0.12, 1.95), "root"),
    ("cannon", (0, -0.92, 1.12), (0, -1.32, 1.08), "root"),
    ("hatch", (0, 0.72, 1.64), (0, 0.98, 1.64), "root"),
]
for n, L in LEGS.items():
    BONES += [("thigh." + n, tuple(L["hip"]), tuple(L["knee"]), "root"),
              ("shin." + n, tuple(L["knee"]), tuple(L["foot"]), "thigh." + n)]

MATS = {
    "armor": ("armor", dict(name="RB_CrawlerArmor", base=(0.9, 0.9, 0.87), labels=[(1, BLUE, 0.35), (2, SEAM, 0.6), (3, BLACK, 0.4), (4, GOLD, 0.3)],
                            seams=[2], wear=1.3, scale=2.0)),
    "frame": ("gunmetal", dict(name="RB_CrawlerFrame", base=(0.2, 0.21, 0.25), labels=[(1, BLUE, 0.35), (2, (0.08, 0.08, 0.09), 0.6), (4, GOLD, 0.3)],
                               seams=[2], scale=2.0)),
    "chrome": ("chrome", dict(name="RB_CrawlerChrome")),
    "socket": ("lens_socket", dict(name="RB_CrawlerSocket")),
    "rubber": ("rubber", dict(name="RB_CrawlerPads", base=(0.12, 0.12, 0.13))),
    "glow": ("glow", dict(name="RB_CrawlerGlow", col=CYAN)),
}
GLOW = {"Dome": (CYAN, 1.0, 0.55), "Eyes": (RED, 1.3, 0.5), "Muzzle": ((1.0, 0.45, 0.12), 1.3, 0.5),
        "Exhaust": ((1.0, 0.55, 0.15), 1.3, 0.5), "Lights": (CYAN, 1.3, 0.5)}
LOW_TARGETS = {"Hull": 1500, "Skirt": 600, "DomeRing": 360, "Dome": 160, "Brow": 300, "Eyes": 60, "Cannon": 520,
               "Muzzle": 40, "Hatch": 320, "Stacks": 300, "Exhaust": 40, "Lights": 60, "Hips": 360}
for n in LEGS:
    LOW_TARGETS.update({"Thigh" + n: 300, "Knee" + n: 80, "Shin" + n: 260, "Foot" + n: 120})
FACE_Y = rot_from_axes(z_axis=(0, -1, 0))


def hazard(f, centre, half, n=8, angle=0.6, labs=(4, 3)):
    c = v3(centre)
    R = rot_from_axes(x_axis=(math.cos(angle), 0, math.sin(angle)), y_axis=(0, 1, 0))
    for i in range(n):
        off = ((i + 0.5) / n - 0.5) * 2 * half[0]
        f.paint(RoundBox(c + v3((off, 0, 0)), (half[0] / n, half[1], half[2] * 2.2), 0.0, R=R), labs[i % 2])


def parts(fine=False):
    vx = 0.008 if fine else 0.014
    vs = 0.006 if fine else 0.011
    out = []
    # ---- the hull: a long armoured shell, cobalt and gold bands, seams; a gunmetal skirt below
    f = Field("Hull")
    f.add(Ellipsoid(HULL_C + v3((0, 0, 0.06)), (0.68, 1.08, 0.36)))
    f.add(RoundBox(HULL_C + v3((0, 0.0, -0.06)), (0.6, 0.95, 0.2), 0.16), k=0.1)
    f.sub(Ellipsoid(HULL_C + v3((0, 0.07, 0.42)), (0.36, 0.42, 0.14)), k=0.04)      # the dome's seat
    f.sub(RoundBox((0, 0.85, 1.62), (0.26, 0.2, 0.06), 0.04), k=0.02)              # the hatch's opening
    f.paint(RoundBox(HULL_C + v3((0, -0.62, 0.0)), (0.9, 0.05, 0.6)), 1)            # a cobalt band round the nose
    f.paint(RoundBox(HULL_C + v3((0, 0.5, 0.0)), (0.9, 0.04, 0.6)), 1)
    for sx in (-1, 1):
        f.paint(RoundBox(HULL_C + v3((sx * 0.5, 0.0, 0.2)), (0.04, 0.8, 0.1)), 4)    # gold side stripes
        f.paint(RoundBox(HULL_C + v3((sx * 0.38, -0.3, 0.3)), (0.004, 0.3, 0.2)), 2)
    f.paint(RoundBox(HULL_C + v3((0, 0, -0.1)), (0.9, 1.3, 0.004)), 2)                # the hull's waist seam
    hazard(f, HULL_C + v3((0, -0.98, -0.12)), (0.4, 0.1, 0.05))
    out.append(("Hull", f, vx, "root", "armor"))
    f = Field("Skirt")
    f.add(RoundBox(HULL_C + v3((0, 0.05, -0.26)), (0.52, 0.86, 0.1), 0.08))
    for i in range(7):
        f.paint(RoundBox(HULL_C + v3((0, -0.6 + 0.2 * i, -0.33)), (0.5, 0.01, 0.05), 0.004), 2)
    out.append(("Skirt", f, vx, "root", "frame"))
    f = Field("Hips")
    for n, L in LEGS.items():
        f.add(Sphere(L["hip"], 0.12))
        f.add(Cylinder(L["hip"] - v3((L["sx"] * 0.07, 0, 0)), 0.15, 0.06, rr=0.02, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.02)
    out.append(("Hips", f, vs, "root", "frame"))
    # ---- the dome: a ring mount, the cyan glass
    f = Field("DomeRing")
    f.add(Torus((0, 0.12, 1.68), 0.36, 0.06))
    for i in range(10):
        a = i * 2 * math.pi / 10
        f.add(Sphere((0.36 * math.cos(a), 0.12 + 0.36 * math.sin(a), 1.71), 0.03), k=0.01)
    f.paint(Torus((0, 0.12, 1.72), 0.36, 0.04), 4)
    out.append(("DomeRing", f, vs, "dome", "frame"))
    f = Field("Dome")
    f.add(Ellipsoid((0, 0.12, 1.72), (0.32, 0.32, 0.3)))
    out.append(("Dome", f, vs, "dome", "glow"))
    # ---- the brow and its sensor eyes
    f = Field("Brow")
    f.add(RoundBox(HULL_C + v3((0, -0.9, 0.2)), (0.42, 0.12, 0.08), 0.06, R=rot_from_axes(y_axis=(0, -0.3, 1.0), x_axis=(1, 0, 0))))
    for sx in (-1, 0, 1):
        f.sub(Sphere(HULL_C + v3((sx * 0.2, -1.01, 0.18)), 0.07), k=0.01)
    out.append(("Brow", f, vs, "root", "frame"))
    f = Field("Eyes")
    for sx in (-1, 0, 1):
        f.add(Sphere(HULL_C + v3((sx * 0.2, -0.98, 0.18)), 0.055))
    out.append(("Eyes", f, vs, "root", "glow"))
    # ---- the cannon under its nose
    f = Field("Cannon")
    f.add(RoundBox((0, -0.92, 1.12), (0.2, 0.14, 0.14), 0.07))
    ax = norm(v3((0, -1.0, -0.1)))
    f.add(Cylinder(v3((0, -0.92, 1.12)) + ax * 0.45, 0.075, 0.6, rr=0.02, R=rot_from_axes(z_axis=ax)), k=0.03)
    f.add(Cylinder(v3((0, -0.92, 1.12)) + ax * 0.76, 0.1, 0.12, rr=0.03, R=rot_from_axes(z_axis=ax)), k=0.02)
    f.sub(Cylinder(v3((0, -0.92, 1.12)) + ax * 0.82, 0.055, 0.1, R=rot_from_axes(z_axis=ax)), k=0.01)
    for k in range(3):
        f.paint(Cylinder(v3((0, -0.92, 1.12)) + ax * (0.3 + 0.1 * k), 0.09, 0.02, R=rot_from_axes(z_axis=ax)), 4)
    out.append(("Cannon", f, vs, "cannon", "frame"))
    f = Field("Muzzle")
    f.add(Cylinder(v3((0, -0.92, 1.12)) + ax * 0.79, 0.056, 0.03, R=rot_from_axes(z_axis=ax)))
    out.append(("Muzzle", f, vs, "cannon", "glow"))
    # ---- the hatch in its back (the summon bay)
    f = Field("Hatch")
    f.add(RoundBox((0, 0.85, 1.64), (0.27, 0.21, 0.035), 0.03))
    f.add(RoundBox((0, 0.85, 1.68), (0.18, 0.04, 0.02), 0.015), k=0.01)
    f.paint(RoundBox((0, 0.85, 1.68), (0.28, 0.22, 0.03)), 1)
    hazard(f, (0, 0.85, 1.67), (0.24, 0.18, 0.012), n=6)
    out.append(("Hatch", f, vs, "hatch", "armor"))
    # ---- exhaust stacks and running lights
    f = Field("Stacks")
    for sx in (-1, 1):
        b = v3((sx * 0.32, 0.92, 1.38))
        f.add(Cylinder(b + v3((0, 0.05, 0.25)), 0.07, 0.42, rr=0.02), k=0.0)
        f.add(Torus(b + v3((0, 0.05, 0.45)), 0.07, 0.018), k=0.006)
        f.sub(Cylinder(b + v3((0, 0.05, 0.47)), 0.05, 0.06), k=0.006)
    out.append(("Stacks", f, vs, "root", "frame"))
    f = Field("Exhaust")
    for sx in (-1, 1):
        f.add(Cylinder(v3((sx * 0.32, 0.97, 1.83)), 0.05, 0.014, rr=0.004))
    out.append(("Exhaust", f, vs, "root", "glow"))
    f = Field("Lights")
    for sx in (-1, 1):
        for y in (-0.5, 0.0, 0.5):
            f.add(Sphere(HULL_C + v3((sx * 0.66, y, 0.02)), 0.028))
    out.append(("Lights", f, vs, "root", "glow"))
    # ---- the legs
    for n, L in LEGS.items():
        h, k_, ft, sx = L["hip"], L["knee"], L["foot"], L["sx"]
        f = Field("Thigh" + n)
        f.add(RoundCone(h, k_, 0.075, 0.06))
        mid = h + (k_ - h) * 0.5
        f.add(RoundBox(mid + v3((0, 0, 0.04)), (0.07, 0.035, 0.3), 0.03, R=rot_from_axes(z_axis=(k_ - h), y_axis=(0, 0, 1))), k=0.03)
        f.paint(RoundBox(mid + v3((0, 0, 0.08)), (0.1, 0.06, 0.06), 0.0, R=rot_from_axes(z_axis=(k_ - h))), 1)
        out.append(("Thigh" + n, f, vs, "thigh." + n, "armor"))
        f = Field("Knee" + n)
        f.add(Sphere(k_, 0.085))
        out.append(("Knee" + n, f, vs, "shin." + n, "chrome"))
        f = Field("Shin" + n)
        f.add(RoundCone(k_, ft + (k_ - ft) * 0.08, 0.06, 0.032))
        f.add(RoundCone(k_ + (ft - k_) * 0.1, k_ + (ft - k_) * 0.55, 0.075, 0.045), k=0.03)        # an armoured calf
        f.paint(RoundBox(k_ + (ft - k_) * 0.32, (0.2, 0.2, 0.03), 0.0, R=rot_from_axes(z_axis=(ft - k_))), 4)
        f.paint(RoundBox(k_ + (ft - k_) * 0.5, (0.2, 0.2, 0.004), 0.0, R=rot_from_axes(z_axis=(ft - k_))), 2)
        out.append(("Shin" + n, f, vs, "shin." + n, "frame"))
        f = Field("Foot" + n)
        f.add(RoundCone(ft + (k_ - ft) * 0.08, ft, 0.04, 0.018))
        f.add(Cylinder(ft + v3((0, 0, 0.0)), 0.07, 0.04, rr=0.015), k=0.02)
        out.append(("Foot" + n, f, vs, "shin." + n, "rubber"))
    return out


# ------------------------------------------------------------------------------------------------ clips
def _leg_aims(arm, n, foot):
    L = LEGS[n]
    la, lb = bone_len(arm, "thigh." + n), bone_len(arm, "shin." + n)
    pole = Vector((L["sx"] * 0.6, 0.0, 1.0))
    st = {}
    def thigh(P, base):
        hip = base.translation
        knee = two_bone(hip, foot, la, lb, pole)
        st["knee"] = knee
        return knee - hip
    def shin(P, base):
        return Vector(foot) - st["knee"]
    return {"thigh." + n: thigh, "shin." + n: shin}


def gait_feet(t, lift=0.22):
    """Each foot's target at loop time t: a tripod gait (two groups swinging in turn)."""
    out = {}
    for n, L in LEGS.items():
        ph = (t + (0.0 if n in TRIPOD_A else 0.5)) % 1.0
        f0 = Vector(L["foot"])
        if ph < 0.5:                                            # carrying: planted, sliding back under the body
            k = ph / 0.5
            y = -WALK_STEP / 2 + WALK_STEP * k
            z = 0.0
        else:                                                   # swinging forward, lifted high
            k = (ph - 0.5) / 0.5
            e = 0.5 - 0.5 * math.cos(math.pi * k)
            y = WALK_STEP / 2 - WALK_STEP * e
            z = lift * math.sin(math.pi * k) ** 1.5
        out[n] = f0 + Vector((0.0, y, z))
    return out


def crawl(arm, name="Walk", frames=WALK_FRAMES, rear=None):
    """The tripod crawl; `rear(t) -> (pitch, hatch angle, dome scale)` turns it into the Summon (legs unchanged)."""
    P = Poser(arm)
    act = ra.new_action(arm, name)
    for f in range(frames + 1):
        t = f / frames
        aims = {}
        for n, ft in gait_feet(t).items():
            aims.update(_leg_aims(arm, n, ft))
        bob = 0.035 * math.cos(4 * math.pi * t)
        roll = 0.035 * math.sin(2 * math.pi * t)
        pitch, hatch, dome = rear(t) if rear else (0.0, 0.0, 1.0)
        root_off = Vector((0.0, 0.0, bob + 0.12 * pitch))
        root_rot = Quaternion(Vector((0, 1, 0)), roll) @ Quaternion(Vector((1, 0, 0)), pitch)
        # the cannon sways a little against the hull; the hatch hinges up at its front edge
        aims["cannon"] = (Quaternion(Vector((1, 0, 0)), -0.04 * math.sin(2 * math.pi * t) - 0.6 * pitch) @ Vector((0, -1.0, -0.1)))
        aims["hatch"] = Quaternion(Vector((1, 0, 0)), hatch) @ Vector((0, 1.0, 0.0))
        sc = {"dome": dome}
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, frames, name == "Walk")
    return act


def clips(arm):
    crawl(arm, "Walk")
    def rear(t):
        k = math.sin(math.pi * min(1.0, t / 0.85)) ** 0.7
        return 0.16 * k, 1.9 * min(1.0, k * 1.4), 1.0 + 0.14 * k
    crawl(arm, "Summon", rear=rear)
