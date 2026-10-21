"""HYDRA SWARM, HQ: the Classical Age boss, the drone hive the Hydra heads come from. A huge robot serpent (the Hydra
Head's build, half as big again: white armour plates with a red spine stripe, gold rims, a gunmetal belly, raised
scutes) carrying a domed hive on its back: a gold-ribbed dome of white armour patterned with hexagonal cells, an amber
beacon on its crown and six round hatches round its foot, each opening on its own hinge (amber light inside) when it
summons drones; three long necks rise from its front, each with a Hydra head (long snout, gold fangs, amber eyes under
red brows, a hinged jaw glowing in the throat, a fan of gold blades behind it), the middle one tallest; hover drones
cling to the hive. Walk: the slither, the three heads swaying out of step, jaws working; Summon: the heads rear back
and open their jaws, the hatches spring open and the beacon blazes while the drones fly out.
Faces -Y, Z up; model_scale 1.0.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, rot_from_axes, v3, norm, Func, F, NOISE
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser
import robot_hydra_head as hh

ROOT_NAME = "HydraSwarm"
GLB_NAME = "hydra_swarm"
TEX_PREFIX = "hydra_swarm"
WALK_FRAMES = 48
SUMMON_FRAMES = 48

RED, GOLD, SEAM, BELLY, AMBER = hh.RED, hh.GOLD, hh.SEAM, hh.BELLY, hh.AMBER
S = 1.55
B = [v3((p[0] * S, p[1] * S + 0.15, p[2] * S)) for p in hh.B]
BR = [r * S * 1.12 for r in hh.BR]
HIVE_C = (B[2] + B[3]) * 0.5 + v3((0, 0, 0.32))
HIVE_R = 0.42
HATCHES = 6
# the three necks: (name, base offset from the body's front joint, the neck's joints, head scale)
NECKS = {}
for nm, sx, rise, out in (("L", 1, 1.0, 0.34), ("C", 0, 1.22, 0.0), ("R", -1, 1.0, 0.34)):
    n0 = B[0] + v3((sx * 0.2, 0.05, 0.12))
    n1 = n0 + v3((sx * out * 0.6, -0.22, 0.42 * rise))
    n2 = n1 + v3((sx * out * 0.5, -0.12, 0.42 * rise))
    n3 = n2 + v3((sx * out * 0.2, 0.0, 0.36 * rise))
    NECKS[nm] = [n0, n1, n2, n3]
NR = [0.17, 0.15, 0.13, 0.115]
HS = 1.15                                    # the heads' size (of the Hydra Head's)


def head_geom(nm):
    """The head's key points for neck `nm` (the Hydra Head's head scaled and moved onto this neck's top)."""
    n3 = NECKS[nm][3]
    def m(p):
        return n3 + (v3(p) - hh.N[3]) * HS
    return {"HEAD_C": m(hh.HEAD_C), "SNOUT": m(hh.SNOUT), "JAW0": m(hh.JAW0), "N3": n3}


BONES = [("root", tuple(B[2]), tuple(B[2] + v3((0, 0, 0.1))), None),
         ("f1", tuple(B[2]), tuple(B[1]), "root"), ("f2", tuple(B[1]), tuple(B[0]), "f1"),
         ("b1", tuple(B[2]), tuple(B[3]), "root")]
for i in range(3, 7):
    BONES.append(("b%d" % (i - 1), tuple(B[i]), tuple(B[i + 1]), "b%d" % (i - 2)))
BONES.append(("hive", tuple(HIVE_C), tuple(HIVE_C + v3((0, 0, 0.3))), "b1"))
for k in range(HATCHES):
    a = 2 * math.pi * (k + 0.5) / HATCHES
    d = v3((math.cos(a), math.sin(a), 0.0))
    hinge = HIVE_C + d * (HIVE_R * 0.92) + v3((0, 0, 0.1))
    BONES.append(("hatch%d" % k, tuple(hinge), tuple(hinge + v3((0, 0, -0.16))), "hive"))
for nm, n in NECKS.items():
    g = head_geom(nm)
    BONES += [("n1" + nm, tuple(n[0]), tuple(n[1]), "f2"), ("n2" + nm, tuple(n[1]), tuple(n[2]), "n1" + nm),
              ("n3" + nm, tuple(n[2]), tuple(n[3]), "n2" + nm), ("head" + nm, tuple(n[3]), tuple(g["SNOUT"]), "n3" + nm),
              ("jaw" + nm, tuple(g["JAW0"]), tuple(g["SNOUT"] + v3((0, 0.02, -0.08))), "head" + nm)]
SEGS = [("f2", B[0], B[1], BR[0], BR[1]), ("f1", B[1], B[2], BR[1], BR[2])] + \
       [("b%d" % (i - 1), B[i], B[i + 1], BR[i], BR[i + 1]) for i in range(2, 7)]
NSEGS = [("n%d%s" % (i + 1, nm), n[i], n[i + 1], NR[i], NR[i + 1]) for nm, n in NECKS.items() for i in range(3)]
DRONES = [(HIVE_C + v3((0.28, -0.2, 0.22)), "hive"), (HIVE_C + v3((-0.3, 0.12, 0.2)), "hive"), (HIVE_C + v3((0.05, 0.32, 0.26)), "hive")]

MATS = {
    "armor": ("armor", dict(name="RB_SwarmArmor", labels=[(1, RED, 0.4), (2, SEAM, 0.6), (3, GOLD, 0.3), (4, BELLY, 0.45)], seams=[2])),
    "frame": ("gunmetal", dict(name="RB_SwarmFrame", labels=[(1, GOLD, 0.3), (2, (0.1, 0.1, 0.11), 0.6)], seams=[2])),
    "gold": ("chrome", dict(name="RB_SwarmGold", base=GOLD)),
    "glow": ("glow", dict(name="RB_SwarmGlow", col=AMBER)),
}
GLOW = {"Beacon": (AMBER, 1.5, 0.5), "HiveGlow": (AMBER, 1.2, 0.5)}
LOW_TARGETS = {"Hive": 2400, "HiveRibs": 900, "Beacon": 80, "HiveGlow": 160}
for s in SEGS + NSEGS:
    LOW_TARGETS["Seg_" + s[0]] = 420
for k in range(HATCHES):
    LOW_TARGETS["Hatch%d" % k] = 160
for nm in NECKS:
    for p, n in (("Head", 1100), ("Jaw", 420), ("Fangs", 160), ("Eyes", 90), ("Brows", 160), ("Throat", 40), ("Crest", 700)):
        LOW_TARGETS[p + nm] = n
    GLOW["Eyes" + nm] = (AMBER, 1.4, 0.5)
    GLOW["Throat" + nm] = (AMBER, 1.2, 0.5)
for i in range(len(DRONES)):
    LOW_TARGETS["Drone%d" % i] = 300
    LOW_TARGETS["DroneEye%d" % i] = 40
    GLOW["DroneEye%d" % i] = (AMBER, 1.3, 0.5)


def head_parts(out, nm, vs):
    g = head_geom(nm)
    HC, SN, J0, N3 = g["HEAD_C"], g["SNOUT"], g["JAW0"], g["N3"]
    s = HS
    f = Field("Head" + nm)
    f.add(Ellipsoid(HC, v3((0.135, 0.17, 0.1)) * s))
    f.add(RoundCone(HC + v3((0, -0.08, -0.01)) * s, SN, 0.1 * s, 0.055 * s), k=0.04)
    f.add(Sphere(N3, NR[3] * 0.9), k=0.04)
    for sx in (-1, 1):
        f.sub(Sphere(HC + v3((sx * 0.1, -0.08, 0.04)) * s, 0.042 * s), k=0.01)
        f.sub(Sphere(SN + v3((sx * 0.025, -0.01, 0.03)) * s, 0.012 * s), k=0.004)
    f.sub(RoundBox(HC + v3((0, -0.16, -0.075)) * s, v3((0.09, 0.2, 0.035)) * s, 0.02), k=0.01)
    f.paint(Func(lambda P, HC=HC: np.maximum(np.abs(P[:, 0] - F(HC[0])) - F(0.022 * s), F(HC[2] + 0.06 * s) - P[:, 2]), HC - 0.5, HC + 0.5), 1)
    f.paint(Torus(N3 + norm(SN - N3) * 0.02, NR[3] * 0.92, 0.015, R=rot_from_axes(z_axis=norm(SN - N3))), 3)
    f.paint(Func(lambda P, HC=HC: P[:, 2] - F(HC[2] - 0.05 * s), HC - 0.5, HC + 0.5), 4)
    out.append(("Head" + nm, f, vs, "head" + nm, "armor"))
    f = Field("Brows" + nm)
    for sx in (-1, 1):
        f.add(RoundCone(HC + v3((sx * 0.06, -0.02, 0.085)) * s, HC + v3((sx * 0.13, -0.13, 0.065)) * s, 0.024 * s, 0.016 * s))
    f.paint(Sphere(HC, 2.0), 1)
    out.append(("Brows" + nm, f, vs, "head" + nm, "armor"))
    f = Field("Eyes" + nm)
    for sx in (-1, 1):
        f.add(Ellipsoid(HC + v3((sx * 0.098, -0.085, 0.04)) * s, v3((0.028, 0.034, 0.024)) * s))
    out.append(("Eyes" + nm, f, vs, "head" + nm, "glow"))
    f = Field("Fangs" + nm)
    for sx in (-1, 1):
        a = SN + v3((sx * 0.032, 0.03, -0.035)) * s
        f.add(RoundCone(a, a + v3((sx * 0.004, -0.004, -0.06)) * s, 0.013 * s, 0.003))
        for j in range(3):
            c = SN + v3((sx * 0.05, 0.08 + 0.05 * j, -0.04)) * s
            f.add(RoundCone(c, c + v3((0, 0, -0.025)) * s, 0.008 * s, 0.002), k=0.003)
    out.append(("Fangs" + nm, f, vs, "head" + nm, "gold"))
    f = Field("Jaw" + nm)
    f.add(RoundCone(J0, SN + v3((0, 0.03, -0.075)) * s, 0.08 * s, 0.04 * s))
    f.sub(RoundBox(HC + v3((0, -0.16, -0.045)) * s, v3((0.07, 0.19, 0.025)) * s, 0.015), k=0.01)
    for sx in (-1, 1):
        for j in range(3):
            c = SN + v3((sx * 0.04, 0.1 + 0.05 * j, -0.06)) * s
            f.add(RoundCone(c, c + v3((0, 0, 0.022)) * s, 0.007 * s, 0.002), k=0.003)
    f.paint(Sphere(HC, 2.0), 4)
    out.append(("Jaw" + nm, f, vs, "jaw" + nm, "armor"))
    f = Field("Throat" + nm)
    f.add(Ellipsoid(HC + v3((0, -0.1, -0.06)) * s, v3((0.05, 0.07, 0.02)) * s))
    out.append(("Throat" + nm, f, vs, "jaw" + nm, "glow"))
    f = Field("Crest" + nm)
    base = N3 + v3((0, 0.06, 0.02)) * s
    for k in range(7):
        ang = math.radians(-72 + 24 * k)
        d = norm(v3((math.sin(ang), 0.55, math.cos(ang) * 0.9)))
        L = (0.26 - 0.05 * abs(k - 3) / 3) * s
        f.add(RoundCone(base + d * 0.04, base + d * L, 0.022 * s, 0.006), k=0.012)
        f.add(Ellipsoid(base + d * (L * 0.6), (0.012 * s, 0.05 * s, L * 0.4), R=rot_from_axes(z_axis=d, x_axis=norm(np.cross(d, v3((0, 1, 0)))))), k=0.01)
    f.add(Torus(base, 0.06 * s, 0.02 * s, R=rot_from_axes(z_axis=(0, 1, 0.3))), k=0.01)
    out.append(("Crest" + nm, f, vs, "n3" + nm, "gold"))


def _hex_cells(P, c, r):
    """< 0 on the thin walls between hexagonal cells on the dome (a paint field: the seams)."""
    q = P - c.astype(F)
    th = np.arctan2(q[:, 1], q[:, 0])
    ph = np.arccos(np.clip(q[:, 2] / (np.sqrt((q * q).sum(1)) + F(1e-6)), -1, 1))
    u = th * F(r * 1.0) / F(0.11)
    v = ph * F(r) / F(0.095)
    row = np.floor(v)
    u = u + F(0.5) * np.mod(row, F(2))
    du = np.abs(u - np.round(u))
    dv = np.abs(v - np.round(v))
    return np.minimum(du * F(0.11), dv * F(0.095)) - F(0.006)


def parts(fine=False):
    vx = 0.0055 if fine else 0.0095
    vs = 0.0038 if fine else 0.0072
    out = []
    for bone, a, b, r1, r2 in SEGS + NSEGS:
        f = Field("Seg_" + bone)
        hh.segment(f, a, b, r1, r2)
        out.append(("Seg_" + bone, f, vx, bone, "armor"))
    for nm in NECKS:
        head_parts(out, nm, vs)
    # ---- the hive: a white armoured dome on a gunmetal collar, hexagonal cells, six hatch openings at its foot
    f = Field("Hive")
    f.add(Ellipsoid(HIVE_C, (HIVE_R, HIVE_R * 1.08, HIVE_R * 0.82)))
    f.add(Cylinder(HIVE_C + v3((0, 0, -0.16)), HIVE_R * 1.02, 0.2, rr=0.04), k=0.04)
    for k in range(HATCHES):
        a = 2 * math.pi * (k + 0.5) / HATCHES
        d = v3((math.cos(a), math.sin(a), 0.0))
        f.sub(Cylinder(HIVE_C + d * (HIVE_R * 0.98) + v3((0, 0, 0.0)), 0.085, 0.2, rr=0.01, R=rot_from_axes(z_axis=d)), k=0.01)
    f.paint(Func(lambda P: _hex_cells(P, HIVE_C, HIVE_R), HIVE_C - 0.6, HIVE_C + 0.6), 2)
    f.paint(Func(lambda P: P[:, 2] - F(HIVE_C[2] - 0.12), HIVE_C - 0.6, HIVE_C + 0.6), 4)
    out.append(("Hive", f, vx, "hive", "armor"))
    f = Field("HiveRibs")                                         # gold ribs from the crown down to the collar
    for k in range(HATCHES):
        a = 2 * math.pi * k / HATCHES
        pts = []
        for j in range(9):
            ph = math.radians(8 + 82 * j / 8)
            pts.append(HIVE_C + v3((math.sin(ph) * math.cos(a) * HIVE_R * 1.02, math.sin(ph) * math.sin(a) * HIVE_R * 1.1,
                                    math.cos(ph) * HIVE_R * 0.84)))
        f.add(Sphere(pts[0], 0.02))
        for p0, p1 in zip(pts, pts[1:]):
            f.add(RoundCone(p0, p1, 0.022, 0.022), k=0.008)
    f.add(Torus(HIVE_C + v3((0, 0, HIVE_R * 0.84)), 0.07, 0.022), k=0.01)
    f.add(Torus(HIVE_C + v3((0, 0, -0.06)), HIVE_R * 1.04, 0.026), k=0.01)
    out.append(("HiveRibs", f, vs, "hive", "gold"))
    f = Field("Beacon")
    f.add(Sphere(HIVE_C + v3((0, 0, HIVE_R * 0.84 + 0.04)), 0.06))
    out.append(("Beacon", f, vs, "hive", "glow"))
    f = Field("HiveGlow")                                          # the amber light inside the hatch openings
    for k in range(HATCHES):
        a = 2 * math.pi * (k + 0.5) / HATCHES
        d = v3((math.cos(a), math.sin(a), 0.0))
        f.add(Cylinder(HIVE_C + d * (HIVE_R * 0.86), 0.07, 0.02, rr=0.006, R=rot_from_axes(z_axis=d)))
    out.append(("HiveGlow", f, vs, "hive", "glow"))
    for k in range(HATCHES):                                        # the hatch doors (closed), each on its hinge bone
        a = 2 * math.pi * (k + 0.5) / HATCHES
        d = v3((math.cos(a), math.sin(a), 0.0))
        c = HIVE_C + d * (HIVE_R * 1.0)
        f = Field("Hatch%d" % k)
        f.add(Cylinder(c, 0.094, 0.022, rr=0.008, R=rot_from_axes(z_axis=d)))
        f.add(Torus(c + d * 0.012, 0.06, 0.008, R=rot_from_axes(z_axis=d)), k=0.004)
        f.paint(Sphere(c + d * 0.02, 0.03), 1)
        out.append(("Hatch%d" % k, f, vs, "hatch%d" % k, "armor"))
    for i, (p, bone) in enumerate(DRONES):
        f = Field("Drone%d" % i)
        hh.drone(f, p)
        out.append(("Drone%d" % i, f, vs, bone, "armor"))
        f = Field("DroneEye%d" % i)
        f.add(Ellipsoid(p + v3((0, -0.118, 0.0)), (0.028, 0.012, 0.028)))
        out.append(("DroneEye%d" % i, f, vs, bone, "glow"))
    return out


def _pose(t, aims, rear=0.0, gape=0.0, hatches=0.0):
    """The neck and head aims for the three heads at loop time t (rear: 0-1, the heads drawn back and up; gape: the
    jaws open; hatches: 0-1 open)."""
    for k, nm in enumerate(("L", "C", "R")):
        n = NECKS[nm]
        g = head_geom(nm)
        ph = 2 * math.pi * (t + 0.31 * k)
        sw = 0.14 * math.sin(ph)
        for j in range(3):
            d = Vector(n[j + 1]) - Vector(n[j])
            d = Quaternion(Vector((0, 0, 1)), sw * (1.0 - 0.5 * j)) @ d
            d = Quaternion(Vector((1, 0, 0)), -0.45 * rear * (0.4 + 0.3 * j)) @ d
            aims["n%d%s" % (j + 1, nm)] = d
        hd = Vector(g["SNOUT"]) - Vector(n[3])
        hd = Quaternion(Vector((1, 0, 0)), 0.5 * rear) @ (hd + Vector((-0.06 * math.sin(ph), 0, 0.02 * math.sin(2 * ph))))
        aims["head" + nm] = hd
        op = max(0.0, math.sin(2 * math.pi * (2 * t + 0.25 * k))) * 0.22 + gape
        jd = Vector(g["SNOUT"] + v3((0, 0.02, -0.08))) - Vector(g["JAW0"])
        aims["jaw" + nm] = Quaternion(Vector((1, 0, 0)), min(0.7, op)) @ jd
    for k in range(HATCHES):
        a = 2 * math.pi * (k + 0.5) / HATCHES
        d = Vector((math.cos(a), math.sin(a), 0.0))
        down = Vector((0, 0, -1))
        aims["hatch%d" % k] = down.lerp(d, hatches).normalized() if hatches > 0.0 else down


def clips(arm):
    # Walk: the Hydra Head's slither on this body, the three heads swaying out of step
    P = Poser(arm)
    act = ra.new_action(arm, "Walk")
    wave = 1.15 * S
    for f in range(WALK_FRAMES + 1):
        t = f / WALK_FRAMES
        aims = {}
        def wpos(i):
            p = Vector(B[i])
            s = (float(B[i][1]) - float(B[0][1])) / wave
            amp = 0.04 + (0.2 - 0.04) * (i / (len(B) - 1)) ** 1.2
            return p + Vector((amp * math.sin(2 * math.pi * (t - s)), 0.0, 0.0))
        pts = [wpos(i) for i in range(len(B))]
        aims["f1"] = pts[1] - pts[2]
        aims["f2"] = pts[0] - pts[1]
        for i in range(2, 7):
            aims["b%d" % (i - 1)] = pts[i + 1] - pts[i]
        aims["hive"] = Vector((0.03 * math.sin(2 * math.pi * t), 0.0, 1.0))
        _pose(t, aims)
        ch, _ = P.solve(aims, root_off=Vector((pts[2].x, 0.0, 0.006 * math.sin(4 * math.pi * t))),
                        root_rot=Quaternion(Vector((0, 1, 0)), 0.03 * math.sin(2 * math.pi * t)))
        P.key(ch, f)
    ra.finish_action(arm, act, WALK_FRAMES, True)
    # Summon: the heads rear back and gape, the hatches spring open, then all settle
    P = Poser(arm)
    act = ra.new_action(arm, "Summon")
    for f in range(SUMMON_FRAMES + 1):
        t = f / SUMMON_FRAMES
        up = math.sin(math.pi * min(1.0, t / 0.8))
        aims = {"hive": Vector((0.0, 0.0, 1.0))}
        _pose(t * 0.5, aims, rear=up, gape=0.45 * up, hatches=min(1.0, 2.5 * up))
        ch, _ = P.solve(aims, root_off=Vector((0.0, 0.0, 0.02 * up)), root_rot=Quaternion(Vector((1, 0, 0)), 0.05 * up))
        P.key(ch, f)
    ra.finish_action(arm, act, SUMMON_FRAMES, False)
