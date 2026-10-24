"""Sentinel, HQ: The Data Center's guardian, the robot that shields and mends the others. A tall, sleek humanoid in
white armour plates with chrome joints and hazard-orange trim: a V-tapered chest with a keel down its front and a
glowing cyan shield emitter set in its heart (a lens in a gunmetal bezel ringed in orange: the source of its energy
shield, which game.gd draws), a slim gunmetal waist of stacked rings, flared shoulder pauldrons with orange edges, a
narrow helmet with a swept orange crest and a black visor holding a red V-shaped eye slit (a stern frown), round ear
discs. Over its back a halo: a glowing cyan ring held up behind its head on a stalk from its backpack, tilted toward
the viewer. Its left forearm carries a hexagonal buckler (white, a hazard-striped rim); its right forearm ends in a
healing projector instead of a hand: a gunmetal muzzle with three chrome prongs round a cyan lens, the prong tips
glowing cyan (the heal emitter: it pulses). Long legs with white thigh plates, orange knee caps, white shins with a
chrome calf piston, gunmetal feet with white toe caps.
Walk (18 frames): a brisk, upright march, the projector held forward and steady, the buckler arm swinging, the halo
hovering and the emitters pulsing (walk_speed = 2 * 0.48 * 0.9 * 24 / 18 = 1.15). Faces -Y, Z up; model_scale 0.9.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Func, rot_from_axes, v3, norm, F
from robot_stealth_jet import facet, mirror_pts, hazard, rel
import robot_anim as ra
from mathutils import Vector

ROOT_NAME = "Sentinel"
GLB_NAME = "sentinel"
TEX_PREFIX = "sentinel"
WALK_STEP = 0.48
WALK_FRAMES = 18           # walk_speed = 2 * WALK_STEP * 0.9 * 24 / WALK_FRAMES = 1.15 (its speed is 1.2)

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.22, 0.23, 0.26)
BLACK = (0.07, 0.07, 0.08)
RED_GLOW = (1.0, 0.16, 0.08)
CYAN = (0.3, 0.88, 1.0)


def mirror(p):
    return (-p[0], p[1], p[2])


J = {
    "hip_L": (0.125, 0.01, 0.80), "knee_L": (0.14, -0.11, 0.46), "ankle_L": (0.14, 0.02, 0.12), "toe_L": (0.14, -0.17, 0.045),
    "shoulder_L": (0.27, 0.02, 1.25), "elbow_L": (0.32, 0.06, 1.03), "wrist_L": (0.33, -0.02, 0.83), "hand_L": (0.33, -0.05, 0.73),
    # the projector arm: the forearm angled forward, the projector pointing ahead and a little down
    "shoulder_R": (-0.27, 0.02, 1.25), "elbow_R": (-0.32, 0.07, 1.04), "wrist_R": (-0.31, -0.13, 0.9), "hand_R": (-0.3, -0.25, 0.86),
}
for _k in ("hip", "knee", "ankle", "toe"):
    J[_k + "_R"] = mirror(J[_k + "_L"])

HEAD_C = v3((0, 0.0, 1.43))
EMIT_C = v3((0, -0.152, 1.135))            # the chest emitter's lens
HALO_C = v3((0, 0.2, 1.61))                # the halo ring's centre
HALO_N = norm(v3((0, -0.42, 0.906)))       # its axis: tilted toward a viewer in front and above
HALO_R = 0.165
HALO_W = norm(np.cross(HALO_N, v3((1, 0, 0))))       # in its plane: back and up
HALO_BACK = HALO_C + HALO_W * HALO_R       # the point where the stalk's fork holds it
_ax_r = norm(v3(J["hand_R"]) - v3(J["wrist_R"]))
PROJ_C = v3(J["wrist_R"]) + _ax_r * 0.07   # the projector's muzzle
HEAL_C = v3(J["wrist_R"]) + _ax_r * 0.14   # its lens (the heal pulse comes from here)

BONES = [
    ("root", (0, 0, 0.80), (0, 0, 0.88), None),
    ("spine", (0, 0, 0.88), (0, 0, 1.30), "root"),
    ("head", (0, 0, 1.33), (0, 0, 1.55), "spine"),
    ("halo", tuple(HALO_C), tuple(HALO_C + HALO_N * 0.12), "spine"),
    ("emitter", tuple(EMIT_C + v3((0, 0.03, 0))), tuple(EMIT_C + v3((0, -0.08, 0))), "spine"),
]
for _s in ("L", "R"):
    BONES += [
        ("upperarm." + _s, J["shoulder_" + _s], J["elbow_" + _s], "spine"),
        ("forearm." + _s, J["elbow_" + _s], J["wrist_" + _s], "upperarm." + _s),
        ("hand." + _s, J["wrist_" + _s], J["hand_" + _s], "forearm." + _s),
        ("thigh." + _s, J["hip_" + _s], J["knee_" + _s], "root"),
        ("shin." + _s, J["knee_" + _s], J["ankle_" + _s], "thigh." + _s),
        ("foot." + _s, J["ankle_" + _s], J["toe_" + _s], "shin." + _s),
    ]
BONES.append(("heal", tuple(HEAL_C - _ax_r * 0.02), tuple(HEAL_C + _ax_r * 0.08), "hand.R"))

MATS = {
    "armor": ("armor", dict(name="RB_SentinelArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.42), (4, BLACK, 0.4)],
                            seams=[2], wear=0.9)),
    "frame": ("gunmetal", dict(name="RB_SentinelFrame", base=(0.21, 0.22, 0.25), labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6)],
                               seams=[2])),
    "chrome": ("chrome", dict(name="RB_SentinelChrome")),
    "socket": ("lens_socket", dict(name="RB_SentinelSocket")),
    "glow": ("glow", dict(name="RB_SentinelGlow", col=CYAN)),
}
GLOW = {"Emitter": (CYAN, 1.5, 0.6), "Eye": (RED_GLOW, 1.7, 0.5), "Halo": (CYAN, 1.5, 0.6), "HealTips": (CYAN, 1.7, 0.6),
        "HealLens": (CYAN, 1.6, 0.6)}
LOW_TARGETS = {"Torso": 900, "Abdomen": 220, "Pelvis": 260, "Back": 360, "HaloMount": 220, "Halo": 160, "Bezel": 160,
               "Emitter": 70, "Neck": 50, "Head": 700, "Eye": 50, "Ears": 100, "Buckler": 200, "Projector": 260,
               "Prongs": 120, "HealTips": 40, "HealLens": 40}
for _s in "LR":
    LOW_TARGETS.update({"Shoulder" + _s: 300, "UpperArm" + _s: 90, "Elbow" + _s: 50, "Forearm" + _s: 200, "Thigh" + _s: 130,
                        "ThighPlate" + _s: 140, "Knee" + _s: 90, "Shin" + _s: 230, "Calf" + _s: 60, "Foot" + _s: 230})
LOW_TARGETS["HandL"] = 160

FACE_Y = rot_from_axes(z_axis=(0, -1, 0))
X_AX = rot_from_axes(z_axis=(1, 0, 0))


def _zband(f, z, w, lab, half=0.6):
    f.paint(RoundBox((0, 0, z), (half, half, w)), lab)


def parts(fine=False):
    vx = 0.0042 if fine else 0.0075
    vs = 0.0032 if fine else 0.006
    out = []
    # ---- the chest: a V-tapered faceted shell with a keel down its front, the emitter socket in its heart
    f = Field("Torso")
    f.add(facet(mirror_pts([(0.1, -0.11, 0.97), (0.1, 0.1, 0.97), (0.205, -0.135, 1.12), (0.2, 0.115, 1.12),
                            (0.235, -0.11, 1.245), (0.215, 0.12, 1.25), (0.12, -0.085, 1.315), (0.12, 0.1, 1.32),
                            (0.0, -0.165, 1.1), (0.0, -0.14, 1.265), (0.0, -0.13, 0.99)]), k=0.012))
    f.sub(Sphere(EMIT_C + v3((0, -0.035, 0)), 0.078), k=0.012)                    # the emitter's socket
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(1.262)) - F(0.012), (-0.4, -0.4, 0.9), (0.4, 0.4, 1.4)), 1)   # orange collar band
    for sx in (-1, 1):
        f.paint(Func(lambda P, sx=sx: np.abs(P[:, 0] * F(sx) - F(0.085) - (F(1.25) - P[:, 2]) * F(0.25)) - F(0.004),
                     (-0.4, -0.4, 0.9), (0.4, 0.4, 1.4)), 2)                     # panel seams down the chest
        f.paint(RoundBox((sx * 0.16, -0.12, 1.02), (0.035, 0.08, 0.012), 0.008), 1)  # orange flank chevrons
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(1.0)) - F(0.004), (-0.4, -0.4, 0.9), (0.4, 0.4, 1.4)), 2)
    out.append(("Torso", f, vx, "spine", "armor"))
    f = Field("Bezel")                                                            # gunmetal bezel ringed in orange
    f.add(Torus(EMIT_C - v3((0, 0.005, 0)), 0.064, 0.016, R=FACE_Y))
    for i in range(6):
        a = i * math.pi / 3 + math.pi / 6
        f.add(Sphere(EMIT_C + v3((0.082 * math.cos(a), -0.004, 0.082 * math.sin(a))), 0.012), k=0.004)
    f.paint(Torus(EMIT_C - v3((0, 0.012, 0)), 0.064, 0.011, R=FACE_Y), 1)
    out.append(("Bezel", f, vs, "spine", "frame"))
    f = Field("Emitter")
    f.add(Ellipsoid(EMIT_C, (0.056, 0.03, 0.056)))
    out.append(("Emitter", f, vs, "emitter", "glow"))
    f = Field("Abdomen")                                                          # the slim waist: stacked rings
    for z, r in ((0.87, 0.1), (0.91, 0.108), (0.95, 0.116)):
        f.add(Cylinder((0, 0.0, z), r, 0.034, rr=0.012), k=0.004)
    out.append(("Abdomen", f, vx, "spine", "frame"))
    f = Field("Pelvis")
    f.add(RoundBox((0, 0.01, 0.815), (0.12, 0.085, 0.05), 0.04))
    for sx in (-1, 1):
        f.add(Sphere((sx * 0.125, 0.01, 0.8), 0.058), k=0.015)
    hazard(f, (-0.2, -0.2, 0.83), (0.2, 0.2, 0.86), w=0.045, d=(1, 0, 1))
    out.append(("Pelvis", f, vx, "root", "frame"))
    # ---- the back: a backpack and the stalk that holds the halo up behind the head (a fork round the ring)
    f = Field("Back")
    f.add(RoundBox((0, 0.135, 1.14), (0.12, 0.06, 0.11), 0.035))
    for sx in (-1, 1):
        f.add(RoundBox((sx * 0.07, 0.19, 1.12), (0.018, 0.02, 0.08), 0.01), k=0.008)   # cooling fins
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(1.2)) - F(0.012), (-0.3, 0.0, 0.9), (0.3, 0.4, 1.4)), 1)
    out.append(("Back", f, vx, "spine", "armor"))
    f = Field("HaloMount")
    s0 = v3((0, 0.18, 1.22))
    s1 = HALO_BACK + v3((0, 0.03, -0.075))
    f.add(RoundCone(s0, s1, 0.028, 0.02))
    f.add(Sphere(s0, 0.04), k=0.01)
    Rh = rot_from_axes(z_axis=HALO_N, y_axis=HALO_W)
    for sx in (-1, 1):                                   # the fork's two cheeks either side of the ring
        f.add(RoundBox(HALO_BACK + Rh @ v3((sx * 0.035, 0.005, 0.0)) + v3((0, 0.01, -0.03)), (0.008, 0.03, 0.04), 0.006, R=Rh), k=0.01)
    f.add(RoundBox(s1 + v3((0, 0.0, 0.0)), (0.045, 0.025, 0.02), 0.01, R=Rh), k=0.012)
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(1.4)) - F(0.015), (-0.2, 0.0, 1.1), (0.2, 0.5, 1.8)), 1)
    out.append(("HaloMount", f, vs, "spine", "frame"))
    f = Field("Halo")
    f.add(Torus(HALO_C, HALO_R, 0.017, R=Rh))
    out.append(("Halo", f, vs, "halo", "glow"))
    # ---- the head: a narrow helmet, a swept orange crest, a black visor band holding the red V eye slit
    f = Field("Neck")
    f.add(Cylinder((0, 0.0, 1.325), 0.045, 0.07, rr=0.01))
    out.append(("Neck", f, vs, "spine", "frame"))
    f = Field("Head")
    f.add(Ellipsoid(HEAD_C + v3((0, 0.005, 0.01)), (0.092, 0.115, 0.095)))
    f.add(RoundBox(HEAD_C + v3((0, -0.03, -0.055)), (0.072, 0.075, 0.035), 0.03), k=0.03)          # the jaw
    f.add(RoundBox(HEAD_C + v3((0, 0.01, 0.1)), (0.014, 0.1, 0.03), 0.012,
                   R=rot_from_axes(y_axis=(0, -0.97, 0.24), x_axis=(1, 0, 0))), k=0.02)           # the crest
    f.sub(RoundBox(HEAD_C + v3((0, -0.118, 0.005)), (0.085, 0.035, 0.03), 0.02), k=0.01)            # the visor recess
    f.paint(RoundBox(HEAD_C + v3((0, -0.1, 0.005)), (0.1, 0.05, 0.045), 0.02), 4)                    # (black)
    f.paint(Func(lambda P: np.abs(P[:, 0]) - F(0.016), HEAD_C - 0.3, HEAD_C + 0.3), 1)              # the orange crest stripe
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(HEAD_C[2] - 0.06)) - F(0.004), F(-0.05) - P[:, 1] * F(-1)),
                 HEAD_C - 0.3, HEAD_C + 0.3), 2)
    out.append(("Head", f, vx, "head", "armor"))
    f = Field("Eye")                                                             # \ / : the inner ends low (a frown)
    for sx in (-1, 1):
        a = v3((sx * 0.006, -0.103, HEAD_C[2] - 0.006))
        b = v3((sx * 0.066, -0.088, HEAD_C[2] + 0.014))
        f.add(RoundCone(a, b, 0.011, 0.009), k=0.006)
    out.append(("Eye", f, vs, "head", "glow"))
    f = Field("Ears")
    for sx in (-1, 1):
        c = HEAD_C + v3((sx * 0.092, 0.01, 0.0))
        f.add(Cylinder(c, 0.036, 0.03, rr=0.01, R=X_AX))
        f.add(RoundCone(c + v3((sx * 0.01, 0.02, 0.02)), c + v3((sx * 0.02, 0.11, 0.07)), 0.012, 0.006), k=0.005)   # a swept fin
        f.paint(Torus(c + v3((sx * 0.016, 0, 0)), 0.03, 0.008, R=X_AX), 1)
    out.append(("Ears", f, vs, "head", "frame"))
    # ---- arms
    for s, sx in (("L", 1), ("R", -1)):
        sh, el, wr, hd = (v3(J[k + "_" + s]) for k in ("shoulder", "elbow", "wrist", "hand"))
        f = Field("Shoulder" + s)                                                # a flared pauldron, orange edged
        pc = sh + v3((sx * 0.035, 0, 0.045))
        f.add(Ellipsoid(pc, (0.115, 0.12, 0.08)))
        f.add(Ellipsoid(pc + v3((sx * 0.02, 0, -0.045)), (0.12, 0.115, 0.04)), k=0.02)
        f.sub(Ellipsoid(sh + v3((sx * 0.03, 0, -0.05)), (0.09, 0.09, 0.07)), k=0.01)
        f.paint(Func(lambda P, pc=pc: np.abs(P[:, 2] - F(pc[2] - 0.05)) - F(0.016), pc - 0.3, pc + 0.3), 1)   # the orange lower edge
        f.paint(Func(lambda P, pc=pc: np.abs(P[:, 1] - F(pc[1])) - F(0.004), pc - 0.3, pc + 0.3), 2)
        out.append(("Shoulder" + s, f, vx, "upperarm." + s, "armor"))
        f = Field("UpperArm" + s)
        f.add(RoundCone(sh, el, 0.042, 0.036))
        out.append(("UpperArm" + s, f, vs, "upperarm." + s, "frame"))
        f = Field("Elbow" + s)
        f.add(Sphere(el, 0.044))
        out.append(("Elbow" + s, f, vs, "forearm." + s, "chrome"))
        ax = norm(wr - el)
        f = Field("Forearm" + s)
        f.add(RoundCone(el + ax * 0.04, wr, 0.056, 0.05))
        f.add(RoundBox(el + (wr - el) * 0.55, (0.03, 0.05, 0.085), 0.02, R=rot_from_axes(z_axis=ax, x_axis=(1, 0, 0))), k=0.02)
        f.paint(Func(lambda P, o=wr - ax * 0.03, a=ax: np.abs((P - o.astype(F)) @ a.astype(F)) - F(0.012), wr - 0.4, wr + 0.4), 1)
        out.append(("Forearm" + s, f, vx, "forearm." + s, "armor"))
    # the buckler on the left forearm: a white hexagon with a hazard rim, turned out and forward
    el, wr, hd = (v3(J[k + "_L"]) for k in ("elbow", "wrist", "hand"))
    ax = norm(wr - el)
    bn = norm(v3((1.0, -0.35, 0.0)))                   # its face looks out and a little forward
    bu = norm(np.cross(bn, ax))
    bv = norm(np.cross(bu, bn))
    bc = el + (wr - el) * 0.55 + bn * 0.075
    hexp = []
    for i in range(6):
        a = i * math.pi / 3
        for t in (-0.014, 0.014):
            hexp.append(tuple(bc + (bu * math.cos(a) + bv * math.sin(a)) * 0.115 + bn * t))
    f = Field("Buckler")
    f.add(facet(hexp, k=0.008))
    f.add(Sphere(bc + bn * 0.008, 0.035), k=0.012)
    hazard(f, bc - 0.2, bc + 0.2, w=0.04, d=tuple(bu + bv),
           band=lambda P, c=bc, n=bn: F(0.085) - np.linalg.norm((P - c.astype(F)) - np.outer((P - c.astype(F)) @ n.astype(F), n.astype(F)), axis=1))
    f.paint(Sphere(bc + bn * 0.008, 0.045), 1)
    out.append(("Buckler", f, vs, "forearm.L", "armor"))
    f = Field("HandL")
    ax = norm(hd - wr)
    f.add(RoundBox(wr + ax * 0.045, (0.042, 0.036, 0.04), 0.02, R=rot_from_axes(z_axis=ax)))
    for dx in (-0.026, 0.0, 0.026):
        base = wr + ax * 0.075 + v3((0, dx, 0))
        f.add(RoundCone(base, base + ax * 0.05 + v3((-0.012, 0, 0)), 0.014, 0.008), k=0.006)
    out.append(("HandL", f, vs, "hand.L", "frame"))
    # the healing projector that ends the right forearm: a muzzle, three chrome prongs round a cyan lens
    wr = v3(J["wrist_R"])
    ax = _ax_r
    pu = norm(np.cross(ax, v3((0, 0, 1))))
    pv = norm(np.cross(pu, ax))
    f = Field("Projector")
    f.add(Cylinder(wr + ax * 0.03, 0.05, 0.08, rr=0.015, R=rot_from_axes(z_axis=ax)))
    f.add(Cylinder(PROJ_C, 0.042, 0.03, rr=0.01, R=rot_from_axes(z_axis=ax)), k=0.01)
    f.paint(Func(lambda P: np.abs((P - (wr + ax * 0.03).astype(F)) @ ax.astype(F)) - F(0.012), wr - 0.3, wr + 0.3), 1)
    out.append(("Projector", f, vs, "hand.R", "frame"))
    f = Field("Prongs")
    g = Field("HealTips")
    for i in range(3):
        a = math.pi / 2 + i * 2 * math.pi / 3
        d = pu * math.cos(a) + pv * math.sin(a)
        p0 = PROJ_C + d * 0.032
        p1 = PROJ_C + ax * 0.085 + d * 0.042
        f.add(RoundCone(p0, p1, 0.011, 0.007), k=0.004)
        g.add(Sphere(p1 + ax * 0.008, 0.013))
    out.append(("Prongs", f, vs, "hand.R", "chrome"))
    out.append(("HealTips", g, vs, "heal", "glow"))
    f = Field("HealLens")
    f.add(Ellipsoid(PROJ_C + ax * 0.02, (0.026, 0.026, 0.012), R=rot_from_axes(z_axis=ax)))
    out.append(("HealLens", f, vs, "heal", "glow"))
    # ---- legs
    for s, sx in (("L", 1), ("R", -1)):
        hp, kn, an, to = (v3(J[k + "_" + s]) for k in ("hip", "knee", "ankle", "toe"))
        tax = norm(kn - hp)
        f = Field("Thigh" + s)
        f.add(RoundCone(hp, kn, 0.056, 0.046))
        out.append(("Thigh" + s, f, vs, "thigh." + s, "frame"))
        f = Field("ThighPlate" + s)                                        # a white plate over its front and outside
        Rt = rot_from_axes(z_axis=tax, y_axis=(-sx * 0.35, -1.0, 0.0))
        f.add(RoundBox(hp + (kn - hp) * 0.48 + v3((sx * 0.012, -0.03, 0)), (0.058, 0.04, 0.13), 0.035, R=Rt))
        f.paint(Func(lambda P, o=hp + tax * 0.06, a=tax: np.abs((P - o.astype(F)) @ a.astype(F)) - F(0.01), hp - 0.5, hp + 0.5), 1)
        out.append(("ThighPlate" + s, f, vx, "thigh." + s, "armor"))
        f = Field("Knee" + s)
        f.add(Ellipsoid(kn + v3((0, -0.045, 0.01)), (0.058, 0.04, 0.06)))
        f.paint(Sphere(kn, 1.0), 1)
        f.paint(Func(lambda P, kn=kn: np.abs(P[:, 0] - F(kn[0])) - F(0.004), kn - 0.2, kn + 0.2), 2)
        out.append(("Knee" + s, f, vs, "shin." + s, "armor"))
        sax = norm(an - kn)
        f = Field("Shin" + s)
        f.add(RoundCone(kn + sax * 0.05, an + (kn - an) * 0.08, 0.064, 0.05))
        f.add(Ellipsoid(kn + (an - kn) * 0.38 + v3((0, -0.012, 0)), (0.066, 0.064, 0.11), R=rot_from_axes(z_axis=sax)), k=0.03)
        f.paint(Func(lambda P, o=kn + sax * 0.27, a=sax: np.abs((P - o.astype(F)) @ a.astype(F)) - F(0.004), kn - 0.5, kn + 0.5), 2)
        f.paint(Func(lambda P, o=an - sax * 0.07, a=sax: np.abs((P - o.astype(F)) @ a.astype(F)) - F(0.012), kn - 0.5, an + 0.5), 1)
        out.append(("Shin" + s, f, vx, "shin." + s, "armor"))
        f = Field("Calf" + s)                                               # a chrome piston down the back of the shin
        f.add(RoundCone(kn + sax * 0.08 + v3((0, 0.06, 0)), an - sax * 0.07 + v3((0, 0.05, 0)), 0.016, 0.013))
        out.append(("Calf" + s, f, vs, "shin." + s, "chrome"))
        f = Field("Foot" + s)
        f.add(RoundBox(an + v3((0, -0.06, -0.072)), (0.062, 0.12, 0.04), 0.03))
        f.add(Ellipsoid(an + v3((0, -0.135, -0.07)), (0.064, 0.07, 0.045)), k=0.02)
        f.add(Sphere(an, 0.045), k=0.02)
        f.add(RoundCone(an + v3((0, 0.03, -0.07)), an + v3((0, 0.085, -0.095)), 0.03, 0.018), k=0.015)   # a heel spur
        f.paint(Ellipsoid(an + v3((0, -0.15, -0.055)), (0.08, 0.075, 0.06)), 3)                           # (the toe cap: dark label)
        f.paint(Func(lambda P, an=an: F(an[2] - 0.103) - P[:, 2], an - 0.3, an + 0.3), 2)
        out.append(("Foot" + s, f, vx, "foot." + s, "frame"))
    return out


# ------------------------------------------------------------------------------------------------ clips
def clips(arm):
    shR, elR, wrR, hdR = (Vector(J[k + "_R"]) for k in ("shoulder", "elbow", "wrist", "hand"))
    up0, fo0 = (elR - shR).normalized(), (wrR - elR).normalized()

    def extra(t, aims):
        w = 2 * math.pi * t
        # the projector arm swings only a little and stays aimed ahead (its swing opposes the right leg's)
        s = -math.sin(w)
        aims["upperarm.R"] = ra.rot_dir(up0, (1, 0, 0), 0.1 * s)
        aims["forearm.R"] = ra.rot_dir(fo0, (1, 0, 0), 0.08 * s)
        aims["hand.R"] = ra.rot_dir((hdR - wrR).normalized(), (1, 0, 0), 0.06 * s)
        # the halo hovers: it rocks a little on its stalk
        aims["halo"] = rel(arm, "halo", Vector(HALO_N) + Vector((0.05 * math.sin(w), 0.04 * math.sin(2 * w + 0.6), 0.0)))

    def scales(t):
        w = 2 * math.pi * t
        return {"heal": 1.0 + 0.22 * max(0.0, math.sin(w)) ** 2, "emitter": 1.0 + 0.06 * math.sin(2 * w),
                "halo": 1.0 + 0.025 * math.sin(2 * w + 1.0)}

    ra.walk(arm, J, "Walk", frames=WALK_FRAMES, step=WALK_STEP, lift=0.085, bob=0.02, sway=0.016, arm_swing=0.32, lean=0.07,
            twist=0.09, heavy=0.25, extra=extra, scales=scales)
