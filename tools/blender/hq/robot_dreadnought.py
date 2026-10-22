"""Dreadnought Walker, HQ: the Gunpowder Age boss, a ship of the line that walks. A tall hull of white armour plates over
a gunmetal frame (its underbelly and deck gunmetal): a raked bow-like prow in front with hazard stripes, along each
flank a gun deck of three square ports between orange pinstripes, a gunmetal cannon barrel poking out of each; on its
deck a command tower (a slanted front with a wide red visor slit, an overhanging roof) on a turret ring, a tesla mast
rising from the tower's roof (copper windings, a crown ring, a cyan-glowing orb: its EMP), twin raked smokestacks
venting behind it, a red glowing core in a gunmetal ring on the foredeck and a hangar hatch on its back deck (two
hazard-striped doors over a dark bay with launch lights) from which Bombers launch. It strides on two heavy armoured
legs: gunmetal hips and knee joints, white thigh plates, knee caps and shins (a chrome piston behind each), big
gunmetal feet with three toes and white spats.
Walk: a slow, ponderous stride, the hull rolling a little like a ship, the tower turning to scan. Summon: the hatch
doors swing open and it rears back while two Bombers lift off (SUMMON_FRAME), its core blazing. Emp: it braces (both
feet planted), its tesla orb flares, and every cannon fires a broadside (EMP_FIRE: the barrels recoil, muzzle flashes
pop; the game fires the EMP there). In the one-shots its feet keep pace with its real ground speed (ONE_STEP), so they
don't slide while the game moves it. Faces -Y, Z up, model_scale 1.0.
"""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, rot_from_axes, v3, norm,
                 euler, F, smax)
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser

ROOT_NAME = "Dreadnought"
GLB_NAME = "dreadnought"
TEX_PREFIX = "dreadnought"
WALK_STEP = 0.7            # each foot's stride: the body moves 2 * WALK_STEP per loop of WALK_FRAMES
WALK_FRAMES = 48           # (2 s at 24 fps): walk_speed = 2 * 0.7 * 1.0 * 24 / 48 = 0.7
ONE_STEP = 0.42            # the one-shots' stride: 0.42 per second at 1x = enemies.json speed 0.42 (no sliding feet)
SUMMON_FRAMES = 48
SUMMON_FRAME = 16          # the doors are open, it has reared back: the Bombers lift off from the bay here
EMP_FRAMES = 40
EMP_FIRE = 12              # the broadside (and the EMP) fires here

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.22, 0.23, 0.26)
BLACK = (0.07, 0.07, 0.08)
COPPER = (0.78, 0.42, 0.22)
RED_GLOW = (1.0, 0.2, 0.08)
CYAN = (0.3, 0.88, 1.0)
VENT = (1.0, 0.55, 0.15)
FLASH = (1.0, 0.8, 0.38)


def mirror(p):
    return (-p[0], p[1], p[2])


J = {   # (the toe level with the ankle: the foot's bone lies flat, so the feet stay flat when the clips aim it forward)
    "hip_L": (0.46, 0.0, 1.48), "knee_L": (0.5, -0.2, 0.9), "ankle_L": (0.5, 0.05, 0.28), "toe_L": (0.5, -0.35, 0.28),
}
for k in list(J):
    if k.endswith("_L"):
        J[k[:-2] + "_R"] = mirror(J[k])

HULL_TOP = 2.34
TIP = v3((0, -1.38, HULL_TOP))             # the prow's tip at the deck (its stem rakes back below)
PORT_Y = (-0.15, 0.2, 0.55)                # the gun ports along each flank
PORT_Z = 1.98
GUN_X0, GUN_X1 = 0.48, 0.88                # a barrel from inside its port out to its muzzle
TC = v3((0, -0.32, 2.62))                  # the command tower's centre
MAST = v3((0, -0.27, 2.91))                # the mast's foot on the tower roof
ORB = MAST + v3((0, 0, 0.47))              # the tesla orb
STACKS = {sx: (v3((sx * 0.16, 0.12, 2.3)), v3((sx * 0.16, 0.22, 3.05))) for sx in (-1, 1)}
CORE_C = v3((0, -0.86, 2.36))              # the core on the foredeck
BAY = v3((0, 0.66, 2.34))                  # the hangar hatch (the bay's opening)
BAY_HALF = (0.25, 0.2)
DOOR_OPEN = math.radians(112)

BONES = [
    ("root", (0, 0, 1.48), (0, 0, 1.7), None),
    ("hull", (0, 0, 1.7), (0, 0, 2.5), "root"),
    ("tower", (TC[0], TC[1], 2.36), (TC[0], TC[1], 2.9), "hull"),
    ("spark", tuple(ORB), tuple(ORB + v3((0, 0, 0.15))), "tower"),
    ("core", tuple(CORE_C), tuple(CORE_C + v3((0, 0, 0.18))), "hull"),
    ("bay", tuple(BAY), tuple(BAY + v3((0, 0, 0.2))), "hull"),
    ("hatch.L", (BAY_HALF[0], BAY[1], BAY[2] + 0.018), (0.02, BAY[1], BAY[2] + 0.018), "hull"),
    ("hatch.R", (-BAY_HALF[0], BAY[1], BAY[2] + 0.018), (-0.02, BAY[1], BAY[2] + 0.018), "hull"),
]
for s, sx in (("L", 1), ("R", -1)):
    ym = sum(PORT_Y) / len(PORT_Y)
    BONES.append(("guns." + s, (sx * GUN_X0, ym, PORT_Z), (sx * GUN_X1, ym, PORT_Z), "hull"))
    for i, y in enumerate(PORT_Y):
        BONES.append(("flash.%s%d" % (s, i), (sx * GUN_X1, y, PORT_Z), (sx * (GUN_X1 + 0.12), y, PORT_Z), "hull"))
for s in ("L", "R"):
    BONES += [
        ("thigh." + s, J["hip_" + s], J["knee_" + s], "root"),
        ("shin." + s, J["knee_" + s], J["ankle_" + s], "thigh." + s),
        ("foot." + s, J["ankle_" + s], J["toe_" + s], "shin." + s),
    ]
FLASH_BONES = [b[0] for b in BONES if b[0].startswith("flash.")]

MATS = {
    "armor": ("armor", dict(name="RB_DreadArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.42), (4, BLACK, 0.45)],
                            seams=[2], wear=1.2, scale=2.0)),
    "frame": ("gunmetal", dict(name="RB_DreadFrame", base=(0.21, 0.22, 0.25), labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6),
                                                                                       (4, COPPER, 0.3), (5, BLACK, 0.5)],
                               seams=[2], scale=2.0)),
    "chrome": ("chrome", dict(name="RB_DreadChrome")),
    "glow": ("glow", dict(name="RB_DreadGlow", col=CYAN)),
}
GLOW = {"Visor": (RED_GLOW, 1.5, 0.5), "Core": (RED_GLOW, 1.5, 0.5), "Orb": (CYAN, 1.3, 0.55), "Vents": (VENT, 1.3, 0.5),
        "Lights": (VENT, 1.3, 0.5)}
for b in FLASH_BONES:
    GLOW["Flash" + b[6:]] = (FLASH, 1.5, 0.6)

LOW_TARGETS = {"Hull": 2600, "Ports": 420, "Frame": 520, "Tower": 1000, "TowerRing": 160, "Visor": 40, "Mast": 640, "Orb": 120,
               "Stacks": 620, "Vents": 40, "CoreRing": 300, "Core": 100, "DoorL": 220, "DoorR": 220, "Lights": 60,
               "GunsL": 520, "GunsR": 520}
for b in FLASH_BONES:
    LOW_TARGETS["Flash" + b[6:]] = 36
for s in "LR":
    LOW_TARGETS.update({"Thigh" + s: 220, "ThighPlate" + s: 320, "Knee" + s: 260, "KneeCap" + s: 260, "Shin" + s: 520,
                        "Piston" + s: 80, "Foot" + s: 480, "Spat" + s: 260})
X_AX = rot_from_axes(z_axis=(1, 0, 0))


# ------------------------------------------------------------------------------------------------ the hull's shape
_BOX = RoundBox((0, -0.2, 1.82), (0.62, 1.2, 0.52), 0.16)                      # y -1.4..1.0, z 1.3..2.34
_CUTS = [(Plane(TIP, (sx * 1.0, -0.62, -0.186)), 0.1) for sx in (-1, 1)] + \
        [(Plane((0, 0, 1.36), (sx * 0.5, 0, -0.866)), 0.12) for sx in (-1, 1)] + \
        [(Plane((0, 1.0, HULL_TOP), (0, 1, -0.3)), 0.08)]                      # the bow, the keel's V, the raked stern
H_LO, H_HI = (-0.75, -1.5, 1.2), (0.75, 1.1, 2.45)


def hull_sd(P):
    d = _BOX(P)
    for pl, k in _CUTS:
        d = smax(d, pl(P), k)
    return d


def _outline(P, z=2.2):
    """The hull's plan outline (signed distance in x, y at height z)."""
    Q = P.copy()
    Q[:, 2] = F(z)
    return hull_sd(Q)


def _hazard(f, lo, hi, w=0.07, band=None, d=(0, 1, 1)):
    """Diagonal hazard stripes (orange 1 / black 4) over the box lo..hi (optionally only where band(P) < 0), running
    across the direction d (in the plane of the surface they are painted on)."""
    lo, hi = v3(lo), v3(hi)
    dd = norm(d).astype(F)
    def box(P):
        return np.max(np.stack([lo.astype(F) - P, P - hi.astype(F)], 0), axis=(0, 2))
    def orange(P):
        d = box(P)
        return d if band is None else np.maximum(d, band(P))
    def black(P):
        s = (P @ dd) / F(w)
        fr = s - np.floor(s)
        return np.maximum(orange(P), (np.abs(fr - F(0.25)) - F(0.25)) * F(w * 0.7))
    f.paint(Func(orange, lo - 0.01, hi + 0.01), 1)
    f.paint(Func(black, lo - 0.01, hi + 0.01), 4)


def parts(fine=False):
    vx = 0.008 if fine else 0.014
    vs = 0.0055 if fine else 0.01
    out = []
    # ---- the hull: white plates (panel lines between them), a gunmetal underbelly and deck, the gun ports, orange stripes
    f = Field("Hull")
    f.add(Func(hull_sd, H_LO, H_HI))
    for sx in (-1, 1):
        for y in PORT_Y:
            f.sub(RoundBox((sx * 0.62, y, PORT_Z), (0.1, 0.075, 0.075), 0.02), k=0.01)                     # a square port
    f.sub(RoundBox(BAY + v3((0, 0, 0.02)), (BAY_HALF[0], BAY_HALF[1], 0.1), 0.03), k=0.01)              # the hangar bay
    # (paint) the deck gunmetal inside a white rim, its plating lines; the underbelly gunmetal below a seam
    deck = lambda P: np.maximum(_outline(P) + F(0.13), F(2.29) - P[:, 2])
    f.paint(Func(deck, H_LO, H_HI), 3)
    for y in (-0.95, -0.55, -0.05, 0.35, 0.95):
        f.paint(Func(lambda P, y=y: np.maximum(np.maximum(np.abs(P[:, 1] - F(y)) - F(0.004), F(2.3) - P[:, 2]), _outline(P) + F(0.13)),
                     H_LO, H_HI), 2)
    f.paint(Func(lambda P: P[:, 2] - F(1.745), H_LO, H_HI), 3)
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(1.765)) - F(0.004), H_LO, H_HI), 2)
    # (paint) orange pinstripes above and below the gun deck, all round; a sheer stripe under the deck's edge
    for z, w in ((PORT_Z + 0.115, 0.014), (PORT_Z - 0.115, 0.014), (2.165, 0.02)):
        f.paint(Func(lambda P, z=z, w=w: np.maximum(np.abs(P[:, 2] - F(z)) - F(w), F(1.7) - P[:, 2]), H_LO, H_HI), 1)
    # (paint) the plates' panel lines on the flanks, between the ports
    for y in (-0.52, 0.025, 0.375, 0.76):
        f.paint(RoundBox((0, y, 1.95), (0.8, 0.004, 0.2)), 2)
    # (paint) the ports' insides dark, hazard stripes on the bow under the deck's edge
    for sx in (-1, 1):
        for y in PORT_Y:
            f.paint(RoundBox((sx * 0.58, y, PORT_Z), (0.1, 0.083, 0.083), 0.02), 3)
    _hazard(f, (-0.7, -1.42, 2.035), (0.7, -0.95, 2.185))
    f.paint(RoundBox(BAY, (BAY_HALF[0] + 0.012, BAY_HALF[1] + 0.012, 0.2), 0.03), 3)                     # the bay's inside
    out.append(("Hull", f, vx, "hull", "armor"))
    # ---- the port frames (gunmetal) round each port
    f = Field("Ports")
    for sx in (-1, 1):
        for y in PORT_Y:
            f.add(RoundBox((sx * 0.625, y, PORT_Z), (0.024, 0.104, 0.104), 0.016))
            f.sub(RoundBox((sx * 0.625, y, PORT_Z), (0.06, 0.077, 0.077), 0.012), k=0.004)
    out.append(("Ports", f, vs, "hull", "frame"))
    # ---- the frame under the hull: the pelvis block, the hip housings and balls
    f = Field("Frame")
    f.add(RoundBox((0, 0.0, 1.47), (0.34, 0.27, 0.14), 0.08))
    for s, sx in (("L", 1), ("R", -1)):
        hp = v3(J["hip_" + s])
        f.add(Cylinder(hp - v3((sx * 0.1, 0, 0)), 0.2, 0.1, rr=0.03, R=X_AX), k=0.03)
        f.add(Sphere(hp, 0.15), k=0.02)
        f.paint(Torus(hp - v3((sx * 0.05, 0, 0)), 0.19, 0.03, R=X_AX), 1)
    f.paint(RoundBox((0, -0.27, 1.47), (0.36, 0.02, 0.15), 0.02), 1)
    out.append(("Frame", f, vx, "root", "frame"))
    # ---- the gun barrels, a broadside of three each side (one bone per side: they recoil together)
    for s, sx in (("L", 1), ("R", -1)):
        f = Field("Guns" + s)
        for y in PORT_Y:
            c = v3((sx * (GUN_X0 + GUN_X1) / 2, y, PORT_Z))
            f.add(Cylinder(c, 0.05, GUN_X1 - GUN_X0, rr=0.012, R=X_AX))
            f.add(Torus(v3((sx * (GUN_X1 - 0.035), y, PORT_Z)), 0.05, 0.024, R=X_AX), k=0.01)               # the muzzle swell
            f.add(Torus(v3((sx * 0.7, y, PORT_Z)), 0.052, 0.012, R=X_AX), k=0.004)                       # a reinforcing ring
            f.sub(Cylinder(v3((sx * GUN_X1, y, PORT_Z)), 0.03, 0.1, R=X_AX), k=0.006)                     # the bore
            f.paint(Cylinder(v3((sx * 0.775, y, PORT_Z)), 0.08, 0.035, R=X_AX), 1)
        out.append(("Guns" + s, f, vs, "guns." + s, "frame"))
        for i, y in enumerate(PORT_Y):                                                                  # muzzle flashes
            m = v3((sx * GUN_X1, y, PORT_Z))
            f = Field("Flash%s%d" % (s, i))
            f.add(Ellipsoid(m + v3((sx * 0.11, 0, 0)), (0.11, 0.065, 0.065)))
            for d in ((1, 0.6, 0), (1, -0.6, 0), (1, 0, 0.6), (1, 0, -0.6), (1, 0, 0)):
                dd = norm(v3((sx * d[0], d[1], d[2])))
                f.add(RoundCone(m + v3((sx * 0.06, 0, 0)), m + v3((sx * 0.06, 0, 0)) + dd * 0.17, 0.045, 0.01), k=0.02)
            out.append(("Flash%s%d" % (s, i), f, vs, "flash.%s%d" % (s, i), "glow"))
    # ---- the command tower: a slanted front with the wide red visor slit, an overhanging roof, portholes
    f = Field("Tower")
    f.add(RoundBox(TC, (0.3, 0.25, 0.25), 0.08))
    f.inter(Plane(TC + v3((0, -0.25, 0)), (0, -1, 0.35)), k=0.04)
    f.add(RoundBox(TC + v3((0, 0.035, 0.272)), (0.315, 0.225, 0.026), 0.02), k=0.012)                    # the roof
    face_y = TC[1] - 0.25 + 0.35 * 0.1                                                                  # (the front at the slit)
    f.sub(RoundBox(v3((0, face_y, 2.72)), (0.245, 0.06, 0.036), 0.02), k=0.008)
    for sx in (-1, 1):
        for dy in (-0.08, 0.08):
            f.sub(Sphere(TC + v3((sx * 0.32, dy, 0.08)), 0.04), k=0.008)                                  # portholes
            f.paint(Sphere(TC + v3((sx * 0.32, dy, 0.08)), 0.058), 3)
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(2.47)) - F(0.03), TC - 0.5, TC + 0.5), 1)                # an orange band
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(2.43)) - F(0.004), TC - 0.5, TC + 0.5), 2)
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(2.51)) - F(0.004), TC - 0.5, TC + 0.5), 2)
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(2.892)) - F(0.02), TC - 0.5, TC + 0.5), 1)                # the roof's rim
    out.append(("Tower", f, vx, "tower", "armor"))
    f = Field("TowerRing")
    f.add(Cylinder(v3((TC[0], TC[1], 2.355)), 0.335, 0.05, rr=0.015))
    for i in range(10):
        a = i * 2 * math.pi / 10
        f.add(Sphere(v3((TC[0] + 0.33 * math.cos(a), TC[1] + 0.33 * math.sin(a), 2.37)), 0.018), k=0.006)
    out.append(("TowerRing", f, vs, "hull", "frame"))
    f = Field("Visor")
    f.add(RoundBox(v3((0, face_y + 0.024, 2.72)), (0.235, 0.026, 0.028), 0.016))
    out.append(("Visor", f, vs, "tower", "glow"))
    # ---- the tesla mast on the tower roof: copper windings, a crown ring and struts, the cyan orb (its EMP)
    f = Field("Mast")
    f.add(Cylinder(MAST + v3((0, 0, 0.03)), 0.115, 0.06, rr=0.02))
    f.add(Cylinder(MAST + v3((0, 0, 0.2)), 0.052, 0.36, rr=0.012), k=0.02)
    for i in range(7):
        f.add(Torus(MAST + v3((0, 0, 0.1 + 0.032 * i)), 0.085, 0.017), k=0.003, label=4)
    f.add(Torus(MAST + v3((0, 0, 0.36)), 0.155, 0.024), k=0.01)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        u = v3((math.cos(a), math.sin(a), 0))
        f.add(RoundCone(MAST + v3((0, 0, 0.3)) + u * 0.04, MAST + v3((0, 0, 0.36)) + u * 0.15, 0.013), k=0.004)
    f.paint(Torus(MAST + v3((0, 0, 0.36)), 0.155, 0.03), 1)
    out.append(("Mast", f, vs, "tower", "frame"))
    f = Field("Orb")
    f.add(Sphere(ORB, 0.105))
    out.append(("Orb", f, vs, "spark", "glow"))
    # ---- twin smokestacks, raked aft, banded; their mouths glow
    f = Field("Stacks")
    gv = Field("Vents")
    for sx, (b0, b1) in STACKS.items():
        ax = norm(b1 - b0)
        L = float(np.linalg.norm(b1 - b0))
        R = rot_from_axes(z_axis=ax)
        f.add(Cylinder((b0 + b1) / 2, 0.1, L, rr=0.02, R=R))
        f.add(Cylinder(b1 - ax * 0.03, 0.125, 0.07, rr=0.022, R=R), k=0.02)                              # the flared cap
        f.sub(Cylinder(b1 + ax * 0.02, 0.083, 0.16, R=R), k=0.01)                                       # its mouth
        f.add(Torus(b0 + ax * L * 0.4, 0.101, 0.016, R=R), k=0.006)
        f.paint(Cylinder(b0 + ax * L * 0.72, 0.14, 0.11, R=R), 1)
        f.paint(Cylinder(b1 - ax * 0.03, 0.15, 0.08, R=R), 5)
        gv.add(Cylinder(b1 - ax * 0.05, 0.085, 0.02, rr=0.006, R=R))
    out.append(("Stacks", f, vs, "hull", "frame"))
    out.append(("Vents", gv, vs, "hull", "glow"))
    # ---- the core on the foredeck: a gunmetal ring of bolts round a red glowing dome, two bars across it
    f = Field("CoreRing")
    f.add(Cylinder(CORE_C + v3((0, 0, -0.005)), 0.2, 0.05, rr=0.018))
    f.add(Torus(CORE_C + v3((0, 0, 0.025)), 0.165, 0.03), k=0.01)
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        f.add(Sphere(CORE_C + v3((0.19 * math.cos(a), 0.19 * math.sin(a), 0.025)), 0.017), k=0.005)
    for a in (0.0, math.pi / 2):
        f.add(Func(lambda P, a=a: np.maximum(Torus(CORE_C, 0.13, 0.014, R=rot_from_axes(z_axis=(math.cos(a), math.sin(a), 0)))(P),
                                             F(CORE_C[2]) - P[:, 2]), CORE_C - 0.2, CORE_C + 0.2), k=0.006)
    f.paint(Torus(CORE_C + v3((0, 0, -0.005)), 0.2, 0.028), 1)
    out.append(("CoreRing", f, vs, "hull", "frame"))
    f = Field("Core")
    f.add(Ellipsoid(CORE_C + v3((0, 0, 0.03)), (0.135, 0.135, 0.095)))
    out.append(("Core", f, vs, "core", "glow"))
    # ---- the hangar hatch: two doors (hinged at their outer edges) over the bay, hazard-striped; lights at its corners
    for s, sx in (("L", 1), ("R", -1)):
        f = Field("Door" + s)
        c = v3((sx * BAY_HALF[0] / 2, BAY[1], BAY[2] + 0.018))
        f.add(RoundBox(c, (BAY_HALF[0] / 2, BAY_HALF[1] + 0.012, 0.022), 0.012))
        f.add(Cylinder(v3((sx * (BAY_HALF[0] + 0.005), BAY[1], BAY[2] + 0.018)), 0.026, BAY_HALF[1] * 2 + 0.02, rr=0.008,
                       R=rot_from_axes(z_axis=(0, 1, 0))), k=0.006)                                   # its hinge
        _hazard(f, c - v3((BAY_HALF[0] / 2 - 0.012, BAY_HALF[1] - 0.012, -0.012)), c + v3((BAY_HALF[0] / 2 - 0.012, BAY_HALF[1] - 0.012, 0.05)),
                w=0.08, d=(1, 1, 0))
        f.paint(RoundBox(v3((0, BAY[1], BAY[2] + 0.045)), (0.01, 0.4, 0.05)), 2)
        out.append(("Door" + s, f, vs, "hatch." + s, "armor"))
    f = Field("Lights")
    for sx in (-1, 1):
        for sy in (-1, 1):
            f.add(Sphere(BAY + v3((sx * (BAY_HALF[0] + 0.05), sy * (BAY_HALF[1] + 0.045), 0.0)), 0.022))
    out.append(("Lights", f, vs, "hull", "glow"))
    # ---- the legs: gunmetal frame and joints, white armour plates, big feet
    for s, sx in (("L", 1), ("R", -1)):
        hp, kn, an = (v3(J[k + "_" + s]) for k in ("hip", "knee", "ankle"))
        tax = norm(kn - hp)
        f = Field("Thigh" + s)
        f.add(RoundCone(hp, kn, 0.13, 0.115))
        out.append(("Thigh" + s, f, vx, "thigh." + s, "frame"))
        f = Field("ThighPlate" + s)                                       # an armour plate over its front and outside
        Rt = rot_from_axes(z_axis=tax, y_axis=(0, -1, 0))
        f.add(Ellipsoid(hp + (kn - hp) * 0.46 + v3((sx * 0.05, -0.05, 0.0)), (0.17, 0.14, 0.27), R=Rt))
        f.sub(Ellipsoid(hp + (kn - hp) * 0.46 + v3((-sx * 0.1, 0.11, 0.0)), (0.16, 0.14, 0.4), R=Rt), k=0.04)
        f.paint(Func(lambda P, c=hp + (kn - hp) * 0.32, ax=tax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.035), hp - 0.6, hp + 0.6), 1)
        f.paint(Func(lambda P, c=hp + (kn - hp) * 0.62, ax=tax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.004), hp - 0.6, hp + 0.6), 2)
        out.append(("ThighPlate" + s, f, vx, "thigh." + s, "armor"))
        f = Field("Knee" + s)                                             # the knee joint: a ball on an axle
        f.add(Sphere(kn, 0.14))
        f.add(Cylinder(kn, 0.11, 0.38, rr=0.03, R=X_AX), k=0.02)
        f.paint(Cylinder(kn, 0.115, 0.4, R=X_AX), 5)
        out.append(("Knee" + s, f, vs, "shin." + s, "frame"))
        f = Field("KneeCap" + s)
        f.add(Ellipsoid(kn + v3((0, -0.12, 0.0)), (0.17, 0.1, 0.17)))
        f.add(RoundBox(kn + v3((0, -0.2, 0.0)), (0.025, 0.04, 0.12), 0.02), k=0.03)                       # a ridge
        _hazard(f, kn + v3((-0.2, -0.3, -0.04)), kn + v3((0.2, 0.0, 0.08)), w=0.06, d=(1, 0, 1))
        out.append(("KneeCap" + s, f, vs, "shin." + s, "armor"))
        f = Field("Shin" + s)
        f.add(RoundCone(kn + (an - kn) * 0.14, an + (kn - an) * 0.14, 0.165, 0.15))
        f.add(Ellipsoid(kn + (an - kn) * 0.46 + v3((0, -0.03, 0)), (0.2, 0.19, 0.25), R=rot_from_axes(z_axis=an - kn, y_axis=(0, -1, 0))), k=0.07)
        sax = norm(an - kn)
        f.paint(Func(lambda P, c=kn + (an - kn) * 0.76, ax=sax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.03), kn - 0.8, kn + 0.8), 1)
        f.paint(Func(lambda P, c=kn + (an - kn) * 0.3, ax=sax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.004), kn - 0.8, kn + 0.8), 2)
        f.paint(RoundBox(kn + (an - kn) * 0.5, (0.004, 0.4, 0.5), 0.0, R=rot_from_axes(z_axis=an - kn, y_axis=(0, -1, 0))), 2)
        out.append(("Shin" + s, f, vx, "shin." + s, "armor"))
        f = Field("Piston" + s)                                           # a chrome piston down the back of the shin
        f.add(RoundCone(kn + v3((0, 0.24, -0.08)), an + v3((0, 0.25, 0.16)), 0.034))
        out.append(("Piston" + s, f, vs, "shin." + s, "chrome"))
        f = Field("Foot" + s)                                             # a big foot: three toes, a heel, the ankle ball
        f.add(RoundBox(an + v3((0, -0.1, -0.19)), (0.24, 0.34, 0.09), 0.07))
        for dx in (-0.15, 0.0, 0.15):
            f.add(Ellipsoid(an + v3((dx, -0.44, -0.18)), (0.085, 0.12, 0.09)), k=0.03)
            f.paint(Ellipsoid(an + v3((dx, -0.5, -0.17)), (0.1, 0.08, 0.1)), 1)
        f.add(RoundBox(an + v3((0, 0.24, -0.2)), (0.15, 0.1, 0.08), 0.05), k=0.04)
        f.add(Sphere(an, 0.13), k=0.04)
        f.paint(Func(lambda P, z=an[2] - 0.255: F(z) - P[:, 2], an - 0.6, an + 0.6), 5)                  # the sole
        out.append(("Foot" + s, f, vx, "foot." + s, "frame"))
        f = Field("Spat" + s)                                             # a white plate over the top of the foot
        f.add(Ellipsoid(an + v3((0, -0.16, -0.08)), (0.21, 0.27, 0.1)))
        f.sub(Sphere(an + v3((0, 0.02, 0.0)), 0.16), k=0.03)
        f.paint(RoundBox(an + v3((0, -0.16, -0.08)), (0.004, 0.4, 0.3)), 2)
        out.append(("Spat" + s, f, vs, "foot." + s, "armor"))
    return out


# ------------------------------------------------------------------------------------------------ clips
V = lambda *a: Vector(a)


def _smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / float(b - a)))
    return t * t * (3 - 2 * t)


def _toe(pitch):
    """The foot's forward direction, its toe raised by `pitch` (rad)."""
    return Quaternion(V(1, 0, 0), -pitch) @ V(0, -1, 0)


def _march(arm, t, step, lift=0.14):
    """Both legs of the march at loop time t: each foot planted half the loop (sliding back under the body) and swung
    forward the other half, lifted flat, its toe a little up before it lands."""
    aims = {}
    for side, off in (("L", 0.0), ("R", 0.5)):
        ph = (t + off) % 1.0
        if ph < 0.5:
            y, z, pitch = -step / 2 + step * ph / 0.5, 0.0, 0.0
        else:
            k = (ph - 0.5) / 0.5
            e = 0.5 - 0.5 * math.cos(math.pi * k)
            y = step / 2 - step * e
            z = lift * math.sin(math.pi * k) ** 1.6
            pitch = 0.18 * math.sin(math.pi * k) ** 2 * k
        aims.update(ra.leg(arm, side, Vector(J["ankle_" + side]) + V(0, y, z), _toe(pitch), V(0, -1, 0.05)))
    return aims


def _rel(arm, name, d):
    """An aim given in the parent's rest frame: direction d (armature space, rest pose) carried by the parent's pose."""
    R0i = arm.data.bones[name].matrix_local.to_3x3().inverted()
    d = Vector(d)
    return lambda P, base: (base.to_3x3() @ R0i) @ d


def _door_aims(arm, ang):
    return {"hatch.L": _rel(arm, "hatch.L", (-math.cos(ang), 0.0, math.sin(ang))),
            "hatch.R": _rel(arm, "hatch.R", (math.cos(ang), 0.0, math.sin(ang)))}


def _yaw(a):
    return lambda P, base: (base.col[1].xyz.copy(), a)


def _hidden_flashes(sc):
    for b in FLASH_BONES:
        sc[b] = 0.01
    return sc


def walk(arm):
    """The ponderous stride: a heavy dip at each footfall, the hull rolling over the planted foot like a ship in a swell,
    the tower turning slowly to scan."""
    P = Poser(arm)
    act = ra.new_action(arm, "Walk")
    for f in range(WALK_FRAMES + 1):
        t = f / WALK_FRAMES
        w = 2 * math.pi * t
        aims = _march(arm, t, WALK_STEP)
        c = math.cos(2 * w)
        bob = 0.03                      # (lowest at each footfall; at mid-stance no higher than its legs reach)
        dip = -bob * c - 1.6 * bob * max(0.0, c) ** 4
        root_off = V(0.06 * math.sin(w), 0.0, dip + bob)
        root_rot = Quaternion(V(0, 0, 1), 0.04 * math.sin(w)) @ Quaternion(V(1, 0, 0), -0.02)
        roll = 0.055 * math.sin(w - 0.5)
        pitch = 0.018 * math.sin(2 * w - 0.4)
        aims["hull"] = V(math.sin(roll), math.sin(pitch), 1.0)
        aims["tower"] = _yaw(0.13 * math.sin(w + 0.8))
        sc = _hidden_flashes({"core": 1.0 + 0.06 * math.sin(2 * w), "spark": 1.0 + 0.05 * math.sin(4 * w)})
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, WALK_FRAMES, True)


def summon(arm):
    """The hatch doors swing open and it rears back (nose up, knees bent) while two Bombers lift off from the bay at
    SUMMON_FRAME, its core blazing; the doors close and it settles. Its legs keep marching at its real speed."""
    P = Poser(arm)
    act = ra.new_action(arm, "Summon")
    for f in range(SUMMON_FRAMES + 1):
        t = f / SUMMON_FRAMES
        w = 2 * math.pi * t
        aims = _march(arm, t, ONE_STEP, lift=0.1)
        k = _smooth(0, 14, f) * (1.0 - _smooth(30, 46, f))
        door = DOOR_OPEN * _smooth(1, 12, f) * (1.0 - _smooth(33, 44, f))
        c = math.cos(2 * w)
        root_off = V(0.04 * math.sin(w), 0.05 * k, -0.03 * c + 0.03 - 0.08 * k)
        aims["hull"] = V(0.03 * math.sin(w - 0.5), math.sin(0.2 * k), 1.0)
        aims["tower"] = _yaw(0.0)
        aims.update(_door_aims(arm, door))
        sc = _hidden_flashes({"core": 1.0 + 0.4 * k, "spark": 1.0 + 0.12 * k})
        ch, _ = P.solve(aims, root_off=root_off, root_rot=Quaternion(V(1, 0, 0), -0.02), scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, SUMMON_FRAMES, False)


def _brace_feet(f):
    """The Emp's footwork, both feet keeping to the ground as it moves at ONE_STEP per second: the right foot steps
    forward (0-10), both stay planted through the brace and the broadside (10-26), the left steps forward (26-36)."""
    g = ONE_STEP / 24.0
    out = {}
    for side, y0, swings in (("L", -ONE_STEP / 2, [(26, 36, -ONE_STEP / 2)]), ("R", ONE_STEP / 2, [(0, 10, -0.2)])):
        y, last, z, pitch = y0, 0, 0.0, 0.0
        res = None
        for f0, f1, yl in swings:
            if f <= f0:
                res = (y + g * (f - last), 0.0, 0.0)
                break
            ys = y + g * (f0 - last)
            if f <= f1:
                k = (f - f0) / float(f1 - f0)
                e = 0.5 - 0.5 * math.cos(math.pi * k)
                res = (ys + (yl - ys) * e, 0.1 * math.sin(math.pi * k) ** 1.6, 0.16 * math.sin(math.pi * k) ** 2 * k)
                break
            y, last = yl, f1
        if res is None:
            res = (y + g * (f - last), 0.0, 0.0)
        out[side] = res
    return out


def emp(arm):
    """It braces (crouching, both feet planted, the hull dipping forward), its tesla orb swells, and at EMP_FIRE every
    cannon fires: the barrels recoil into their ports, muzzle flashes burst, the orb flares and the hull jolts; then it
    rises and walks on."""
    P = Poser(arm)
    act = ra.new_action(arm, "Emp")
    for f in range(EMP_FRAMES + 1):
        aims = {}
        for side, (y, z, pitch) in _brace_feet(f).items():
            aims.update(ra.leg(arm, side, Vector(J["ankle_" + side]) + V(0, y, z), _toe(pitch), V(0, -1, 0.05)))
        kb = _smooth(0, 9, f) * (1.0 - _smooth(22, 34, f))
        shift = 0.05 * (math.sin(math.pi * min(1.0, f / 10.0)) if f <= 10 else 0.0) - \
            0.05 * (math.sin(math.pi * (f - 26) / 10.0) if 26 <= f <= 36 else 0.0)
        jolt = 0.0
        kick = 0.0
        if f >= EMP_FIRE:
            u = f - EMP_FIRE
            jolt = 0.045 * math.exp(-u * 0.42) * math.cos(u * 1.5)
            kick = 0.05 * math.exp(-u * 0.5)
        root_off = V(shift, 0.0, -0.11 * kb + jolt)
        aims["hull"] = V(0.0, -math.sin(0.05 * kb) + kick, 1.0)
        aims["tower"] = _yaw(0.0)
        charge = _smooth(1, 11, f)
        orb = 1.0 + 0.4 * charge if f < EMP_FIRE else 1.0 + 0.9 * math.exp(-(f - EMP_FIRE) * 0.3) + 0.4 * (1.0 - _smooth(EMP_FIRE, 24, f))
        recoil = 1.0 if f < EMP_FIRE else 1.0 - 0.28 * math.exp(-(f - EMP_FIRE) / 2.5)
        fl = {0: 1.0, 1: 1.25, 2: 0.9, 3: 0.45}.get(f - EMP_FIRE, 0.01)
        sc = {"core": 1.0 + 0.25 * charge * (1.0 - _smooth(16, 30, f)), "spark": orb,
              "guns.L": (1.0, recoil, 1.0), "guns.R": (1.0, recoil, 1.0)}
        for b in FLASH_BONES:
            sc[b] = fl
        ch, _ = P.solve(aims, root_off=root_off, root_rot=Quaternion(V(1, 0, 0), -0.02), scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, EMP_FRAMES, False)


def clips(arm):
    walk(arm)
    summon(arm)
    emp(arm)
