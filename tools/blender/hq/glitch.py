"""Glitch, Rogue Android (HQ hero, Digital Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A robot that chose humanity: a sleek humanoid android who defected from the invaders to the tech corps, built so he can
never be taken for one of them (they are white with hazard orange, cyan glows and red eyes): graphite and midnight-navy
armour plates over a dark, flexible under-suit, and his own glow colour, a mint teal.

His head: a rounded graphite helmet-skull with a raised navy crest running back over it, steel audio discs for ears,
and a smooth pale-steel faceplate that still reads as a friendly face from above: big glowing teal eyes (lens domes in
dark glass sockets, their lower edges lifted a little, as if smiling, a white catchlight in each), graphite brow plates
arched over them, the hint of a nose, and a teal light bar for a mouth, curved up in a smile.

His armour: a graphite cuirass with navy side panels and panel lines, a teal heart-shaped core in a steel bezel on his
breastbone (the heart he chose), vents on his back, a panel missing on his right flank with the cables showing; two
navy bands over his belly, a graphite belt with a steel buckle, navy plates on his hips; big navy pauldrons with graphite
rims, the left one cracked across and patched with an X of grey tape (he has been through things); graphite plates on his
upper arms, steel elbow cops, graphite gauntlets with a navy blade housing along the outside of each forearm, graphite
knuckle plates; graphite thigh plates, navy knee cops, graphite shin guards, armoured shoes with black soles. His side:
a ragged scrap of the corps' violet scarf wound round his neck (knotted at his left, one tail down his chest, one over
his left shoulder down his back) and a violet armband on his left arm.

His weapons: an energy blade out of each forearm housing, along the forearm and past his fist (over its back): a steel
core with glowing teal edges and point (their own meshes, `GlowEdgeR` / `GlowEdgeL`). Each blade rides its own bone
(`blade.R`, `blade.L`, children of the forearms, from inside the housing to the point): scaled to 0.06 along its length
it is drawn back into the housing (Idle, the start of the Ability). The `flash` bone (a child of the head) carries
`GlowFlash`, a brighter copy of his eyes that the Ability pops at its signal; it is scaled to 0 everywhere else.

His body is the Musketeer's (musketeer.py: the long, rangy skeleton, its limbs, fists and feet) as the under-suit (the
"Skin" part), with no head of its own: his head is a rigid part. Every armour plate is rigid on one bone (machines don't
bend): the plates are kept apart, and each piece (mesh island) goes to the bone it sits on (rest pose)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp, grad
import musketeer as mk
from musketeer import (J, hp, hr, hinv, HS, HEAD_C, HEAD_RAD, smoothstep, hand_frame, HAND_S, fist_center, foot,
                       torso_prims, traps, neck_prim, deltoid, upper_arm_prims, forearm_prims, leg_prims, shin_prims,
                       torso_bones, TORSO_Z, TORSO)

# the android material's labels (mats.android)
SUIT, GRAPHITE, NAVY, SEAM, VIOLET, TAPE, STEEL, GLASS, FACE, WHITE, ORANGE, RUBBER = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
TEAL = (0.12, 1.0, 0.78)                 # his own glow (eyes, mouth, heart, blade edges): greener than the robots' cyan
EYE_R = hr(0.05)
Z = v3((0.0, 0.0, 1.0))


def _seg(P, a, b):
    """(distance to the segment a-b, the unclamped parameter along it)."""
    ab = (b - a).astype(F)
    t = ((P - a.astype(F)) @ ab) / F(ab @ ab)
    tc = np.clip(t, 0, 1)
    return np.sqrt((((a.astype(F) + tc[:, None] * ab) - P) ** 2).sum(1)), t


def _surf_frame(fn, p, h=0.0015):
    """The outward normal of a distance function at p."""
    p = v3(p)
    g = []
    for i in range(3):
        e = np.zeros(3)
        e[i] = h
        vals = fn(np.array([p + e, p - e], F))
        g.append(float(vals[0] - vals[1]) / (2 * h))
    return norm(v3(g))


def _hit(fn, origin, d, tmax=0.9):
    """First hit of a ray on a distance function (Field or callable) and the normal there (None if it misses)."""
    h, ok = ray_hit(fn, [v3(origin)], [v3(d)], tmax=tmax, step=0.001)
    if not ok[0]:
        return None, None
    f = fn.eval if isinstance(fn, Field) else fn
    return v3(h[0]), _surf_frame(f, h[0])


def _frame(n, up=Z):
    """Columns (side, up, n): a frame on a surface with normal n."""
    n = norm(n)
    u = norm(v3(up) - n * float(v3(up) @ n))
    s = norm(np.cross(u, n))
    return np.stack([s, u, n], 1)


# ======================================================================================= the under-suit ("Skin")
def body_parts(fd):
    """The Musketeer's body as a dark, flexible under-suit (label SUIT): torso, neck (steel rings round it), arms, fists
    (the suit's gloves), legs and feet. No head (his head is the rigid Head part)."""
    for p, k in torso_prims():
        fd.add(p, k, SUIT)
    fd.add(traps(), 0.06, SUIT)
    fd.add(neck_prim(), 0.05, SUIT)
    na, nb = v3((0, 0.065, 1.39)), hp((0, 0.02, 1.575))
    nax = norm(nb - na)
    for t in (0.42, 0.62):
        fd.add(Torus(lerp(na, nb, t), 0.083 - 0.004 * t, 0.007, R=rot_from_axes(z_axis=nax)), 0.006, STEEL)
    for side in ("R", "L"):
        fd.add(deltoid(side), 0.055, SUIT)
        for p, k in upper_arm_prims(side) + forearm_prims(side):
            fd.add(p, k, SUIT)
        mk.hand(fd, side)
        for p, k in leg_prims(side) + shin_prims(side):
            fd.add(p, k, SUIT)
        foot(fd, side)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= the head (rigid on `head`)
SK_C, SK_R = (0.0, 0.03, 1.748), (0.178, 0.197, 0.19)
EYE_X, EYE_Z = 0.071, 1.692              # the eyes' middles (design units)
MOUTH_Z, MOUTH_W = 1.574, 0.05           # the smile: its middle's height, its half width (design)
FACE_A = 1.02                            # the faceplate spans this many radians each side of his front


def skull():
    return Ellipsoid(hp(SK_C), v3(SK_R) * HS)


def _head_base():
    """Skull and face shapes (no detail): what the details are placed on."""
    fd = Field("HeadBase")
    fd.add(skull(), 0.0, GRAPHITE)
    fd.add(Ellipsoid(hp((0, -0.045, 1.67)), v3((0.172, 0.158, 0.15)) * HS), 0.05, FACE)            # the face (broad, flat-fronted)
    fd.add(Ellipsoid(hp((0, -0.084, 1.574)), v3((0.104, 0.106, 0.08)) * HS), 0.05, FACE)          # jaw and chin
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.094, -0.116, 1.618)), hr(0.05)), 0.04, FACE)                    # cheeks
    fd.add(RoundCone(hp((0, -0.196, 1.705)), hp((0, -0.214, 1.642)), hr(0.011), hr(0.0155)), hr(0.022), FACE)  # a hint of a nose
    return fd


_HB = []


def head_base():
    if not _HB:
        _HB.append(_head_base())
    return _HB[0]


def face_mask(P):
    """< 0 on the faceplate (design units): a band round his front, from his forehead to under his chin."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1] - F(0.03), Q[:, 2]
    ang = np.arctan2(x, -y)
    r = np.sqrt(x * x + y * y)
    ztop = F(1.808) - F(0.05) * (ang / F(FACE_A)) ** 2
    return np.maximum(np.maximum((np.abs(ang) - F(FACE_A)) * r, z - ztop), F(1.47) - z) * F(HS)


def face_pt(x, z, lift=0.0):
    """A point on the face's surface in front of design (x, z), lifted `lift` along the normal, and the normal."""
    hb = head_base()
    p, n = _hit(hb, hp((x, -0.5, z)), (0, 1, 0), tmax=0.9)
    if p is None:
        raise ValueError("face_pt(%.3f, %.3f) misses the face" % (x, z))
    return p + n * lift, n


def eye_frame(sx):
    """(centre on the faceplate, local frame (side, up, out))."""
    p, n = face_pt(sx * EYE_X, EYE_Z)
    R = _frame(n)
    return p, R


def eye_c(sx):
    p, R = eye_frame(sx)
    return p - R[:, 2] * 0.01


def _cheek(sx):
    """The ellipsoid that lifts the eye's lower edge (a smiling eye)."""
    p, R = eye_frame(sx)
    return Ellipsoid(p - R[:, 1] * hr(0.066), v3((0.08, 0.03, 0.06)) * HS, R=R)


def _eye_shape(sx, grow=1.0, out=0.0, depth=0.012):
    p, R = eye_frame(sx)
    e = Ellipsoid(p + R[:, 2] * (out - hr(0.002)), v3((0.044 * grow, 0.051 * grow, depth)) * HS, R=R)
    return Inter(e, Func(lambda P, c=_cheek(sx): -c(P), p - 0.2, p + 0.2), hr(0.002))


def mouth_points(lift=0.0):
    xs = np.linspace(-MOUTH_W, MOUTH_W, 9)
    pts, ns = [], []
    for x in xs:
        p, n = face_pt(x, MOUTH_Z + 6.4 * x * x, lift)
        pts.append(p)
        ns.append(n)
    return pts, ns


def head_field():
    """Graphite skull (5) with a raised navy crest (6) running back over it; the pale steel faceplate (12) ringed by a
    panel line (7); steel ear discs (10); dark glass (11) eye sockets and mouth slot; graphite brow plates."""
    fd = Field("Head")
    hb = head_base()
    for op in hb.ops:
        fd.ops.append(op)
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    # the crest: a raised strip over the top of his skull, front to back
    def crest(P):
        Q = hinv(P)
        return np.maximum(np.maximum(np.abs(Q[:, 0]) - F(0.021), F(-0.1) - Q[:, 1]), F(1.63) - Q[:, 2])
    fd.add(Inter(Shell(skull(), hr(0.006), hr(0.022), pad=0.05), Func(crest, lo, hi), hr(0.004)), hr(0.006), NAVY)
    # ears: steel audio discs with a ring groove
    for sx in (-1, 1):
        c = hp((sx * 0.176, 0.036, 1.69))
        ax = norm(v3((sx, 0.05, 0.0)))
        Rr = rot_from_axes(z_axis=ax)
        fd.add(Cylinder(c, hr(0.054), hr(0.04), rr=hr(0.012), R=Rr), hr(0.012), STEEL)
        fd.sub(Torus(c + ax * hr(0.02), hr(0.034), hr(0.004), R=Rr), hr(0.002))
        fd.add(Cylinder(c + ax * hr(0.018), hr(0.016), hr(0.012), rr=hr(0.004), R=Rr), hr(0.003), STEEL)
    # paint: graphite off the faceplate, the faceplate, its panel line; seams down the skull beside the crest
    fd.paint(Func(lambda P: -face_mask(P), lo, hi), GRAPHITE)
    fd.paint(Func(face_mask, lo, hi), FACE)
    fd.paint(Func(lambda P: np.abs(face_mask(P)) - F(hr(0.0032)), lo, hi), SEAM)
    def side_seams(P):
        Q = hinv(P)
        return np.maximum(np.abs(np.abs(Q[:, 0]) - F(0.05)) - F(0.0026), np.maximum(F(-0.05) - Q[:, 1], F(1.7) - Q[:, 2]))
    fd.paint(Func(side_seams, lo, hi), SEAM)
    # eye sockets (dark glass), their lower edges lifted by the cheeks
    for sx in (-1, 1):
        p, R = eye_frame(sx)
        fd.sub(_eye_shape(sx, 1.08, 0.0, 0.016), hr(0.003))
        fd.paint(_eye_shape(sx, 1.2, 0.0, 0.03), GLASS)
    # brow plates: graphite arcs over the eyes, raised kindly
    for sx in (-1, 1):
        pts = []
        for x, z in ((0.03, 1.756), (0.07, 1.772), (0.11, 1.761), (0.132, 1.744)):
            q, n = face_pt(sx * x, z, hr(0.003))
            pts.append(q)
        fd.add(Chain(pts, [hr(0.008), hr(0.0105), hr(0.0095), hr(0.006)], k=hr(0.006)), hr(0.004), GRAPHITE)
    # the mouth slot (the light bar sits in it: GlowFace)
    pts, ns = mouth_points()
    rads = [hr(0.004), hr(0.0055), hr(0.006), hr(0.006), hr(0.006), hr(0.006), hr(0.006), hr(0.0055), hr(0.004)]
    fd.sub(Chain(pts, rads, k=hr(0.003)), hr(0.002))
    fd.paint(Chain(pts, [r + hr(0.0045) for r in rads], k=hr(0.004)), GLASS)
    # vents on his cheeks: three short slanted lines each side
    for sx in (-1, 1):
        for k in range(3):
            a, _ = face_pt(sx * (0.11 + 0.003 * k), 1.612 - 0.015 * k)
            b, _ = face_pt(sx * (0.128 + 0.003 * k), 1.624 - 0.015 * k)
            fd.paint(RoundCone(a, b, hr(0.0028), hr(0.0028)), SEAM)
    return fd


def face_glow_field():
    """His glowing eyes (lens domes standing a little proud of their sockets) and the smile's light bar."""
    fd = Field("Face")
    for sx in (-1, 1):
        fd.add(_eye_shape(sx, 1.0, hr(0.0), 0.012), 0.0)
    pts, ns = mouth_points(-hr(0.0015))
    rads = [hr(0.0026), hr(0.0038), hr(0.0044), hr(0.0046), hr(0.0046), hr(0.0046), hr(0.0044), hr(0.0038), hr(0.0026)]
    fd.add(Chain(pts, rads, k=hr(0.002)), 0.0)
    return fd


def spark_field():
    """A white catchlight high on the outer side of each eye."""
    fd = Field("Spark")
    for sx in (-1, 1):
        p, R = eye_frame(sx)
        c = p + R[:, 1] * hr(0.024) + R[:, 0] * (sx * hr(0.013)) + R[:, 2] * hr(0.0085)
        fd.add(Ellipsoid(c, v3((0.0095, 0.0105, 0.004)) * HS, R=R), 0.0)
    return fd


def flash_field():
    """The eyes' flash (the Ability): brighter, bigger copies of them, in front (on the `flash` bone, hidden otherwise)."""
    fd = Field("Flash")
    for sx in (-1, 1):
        p, R = eye_frame(sx)
        fd.add(Ellipsoid(p + R[:, 2] * hr(0.004), v3((0.052, 0.06, 0.012)) * HS, R=R), 0.0)
    return fd


def flash_bone():
    a = hp((0.0, -0.06, 1.692))
    return a, a + v3((0, -0.12, 0))


# ======================================================================================= torso armour ("Armor")
def torso_hull():
    """His torso as the cuirass lies on it: the chest smoothed into one broad plate (no pectorals)."""
    b = Field("TorsoHull")
    for i, (p, k) in enumerate(torso_prims()):
        if i in (2, 3):
            continue
        b.add(p, k)
    b.add(Ellipsoid((0, -0.04, 1.27), (0.22, 0.155, 0.16)), 0.06)
    b.add(traps(), 0.06)
    return b


def belly_hull():
    b = Field("BellyHull")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    return b


_TH, _BH = [], []


def th():
    if not _TH:
        _TH.append(torso_hull())
    return _TH[0]


def bh():
    if not _BH:
        _BH.append(belly_hull())
    return _BH[0]


CU_OFF, CU_T = 0.03, 0.026               # the cuirass: its middle's offset from the hull, its thickness
CU_OUT = CU_OFF + CU_T / 2
NECK_A = v3((0.0, 0.065, 1.34))
NECK_B = v3(hp((0.0, 0.02, 1.575)))
FLANK = v3((-0.235, 0.05, 1.19))         # the missing panel on his right flank


def neck_dist(P):
    ax = norm(NECK_B - NECK_A)
    q = P - NECK_A.astype(F)
    t = q @ ax.astype(F)
    c = q - t[:, None] * ax.astype(F)
    return np.sqrt((c * c).sum(1))


def _flank_hole(P):
    q = (P - FLANK.astype(F)) / np.array([0.09, 0.075, 0.058], F)
    return F(1.0) - np.sqrt((q * q).sum(1))


def cuirass_region(P):
    """< 0 on the cuirass: chest and back from below the ribs up to his neck, round the arm holes, less the flank panel."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    bot = F(1.1) - F(0.035) * smoothstep(0.13, 0.0, ax) * (y < F(0.0)) - z
    neck = np.where(z > F(1.33), F(0.122) - neck_dist(P), F(-1.0))
    arms = F(-1.0)
    for sx in (-1, 1):
        c = v3((sx * 0.335, 0.075, 1.375)).astype(F)
        arms = np.maximum(arms, F(0.165) - np.sqrt(((P - c) ** 2).sum(1)))
    return np.maximum(np.maximum(bot, neck), np.maximum(arms, _flank_hole(P) * F(0.05)))


def cu_pt(x, z, front=True, out=0.0):
    """A point on the cuirass' outer face in front of (behind) (x, z), and the outward normal."""
    d = v3((0, -1, 0)) if front else v3((0, 1, 0))
    f = lambda P: th().eval(P, margin=0.12) - F(CU_OUT + out)
    p, n = _hit(f, v3((x, 0.06, z)) + d * 0.7, -d)
    return p, n


HEART_Z = 1.268


def heart2d(u, v):
    """A heart (2D distance, < 0 inside; its point down), about 6 cm across."""
    c1 = np.sqrt((u + F(0.0135)) ** 2 + (v - F(0.004)) ** 2) - F(0.0168)
    c2 = np.sqrt((u - F(0.0135)) ** 2 + (v - F(0.004)) ** 2) - F(0.0168)
    w = np.maximum((np.abs(u) - (v + F(0.031))) * F(0.7071), v - F(0.006))
    return np.minimum(np.minimum(c1, c2), w)


def heart_frame():
    p, n = cu_pt(0.0, HEART_Z)
    return p, _frame(n)


def heart_prim(grow=0.0, depth=(-0.01, 0.01)):
    p, R = heart_frame()
    def fn(P):
        q = (P - p.astype(F)) @ R.astype(F)
        return np.maximum(heart2d(q[:, 0], q[:, 1]) - F(grow), np.maximum(F(depth[0]) - q[:, 2], q[:, 2] - F(depth[1])))
    return Func(fn, p - 0.08, p + 0.08)


def armor_field():
    """The cuirass (graphite 5, navy side panels 6, panel lines 7): its back with two vents and a spine ridge, the heart's
    steel bezel (10) on his breastbone; the flank's missing panel with the cables in it (rubber 15, steel 10); two navy
    bands over his belly; the graphite belt with its steel buckle (a violet (8) chevron on it); navy hip plates."""
    fd = Field("Armor")
    T = th()
    tlo, thi = T.bounds()
    fd.add(Inter(Func(cuirass_region, (-0.6, -0.5, 1.0), (0.6, 0.55, 1.65)), Shell(T, CU_OFF, CU_T, pad=0.06), 0.006), 0.0, GRAPHITE)
    # side panels (navy) and panel lines
    def side_panels(P):
        return np.maximum(F(0.148) - np.abs(P[:, 0]), F(1.0) - P[:, 2])
    fd.paint(Func(side_panels, (-0.6, -0.5, 1.0), (0.6, 0.55, 1.65)), NAVY)
    def lines(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        v = np.abs(np.abs(x) - F(0.148)) - F(0.0028)
        h = np.maximum(np.abs(z - F(1.19)) - F(0.0028), F(0.148) - np.abs(x))
        back = np.maximum(np.abs(np.abs(x) - F(0.06)) - F(0.0028), F(0.1) - y)
        return np.minimum(np.minimum(v, h), back)
    fd.paint(Func(lines, (-0.6, -0.5, 1.0), (0.6, 0.55, 1.65)), SEAM)
    # the heart's bezel: a raised steel rim round a recess
    fd.add(heart_prim(0.011, (-0.012, 0.009)), 0.004, STEEL)
    fd.sub(heart_prim(0.0015, (-0.004, 0.03)), 0.0015)
    # the back: a spine ridge, two vents
    for z0, z1 in ((1.14, 1.4),):
        a, na = cu_pt(0.0, z0, front=False)
        b, nb = cu_pt(0.0, z1, front=False)
        m, nm = cu_pt(0.0, (z0 + z1) / 2, front=False)
        fd.add(Chain([a + na * 0.004, m + nm * 0.008, b + nb * 0.004], [0.016, 0.018, 0.014], k=0.01), 0.008, NAVY)
    for sx in (-1, 1):
        p, n = cu_pt(sx * 0.1, 1.3, front=False)
        R = _frame(n)
        fd.add(RoundBox(p + n * 0.003, (0.045, 0.034, 0.008), 0.006, R=R), 0.005, NAVY)
        for k in range(3):
            fd.sub(RoundBox(p + n * 0.012 + R[:, 1] * (-0.02 + 0.02 * k), (0.034, 0.0035, 0.01), 0.003, R=R), 0.002)
    # the flank: cables in the missing panel's hole, over the suit
    for i, (dy, lab, r) in enumerate(((-0.025, RUBBER, 0.011), (0.01, STEEL, 0.008), (0.042, RUBBER, 0.01))):
        pts = []
        for z in (1.12, 1.16, 1.2, 1.24, 1.27):
            p, n = _hit(T, v3((-0.7, FLANK[1] + dy + 0.01 * math.sin(z * 40 + i), z)), (1, 0, 0))
            pts.append(p + n * (r + 0.004 + 0.004 * math.sin(z * 30 + i * 2)))
        fd.add(Chain(pts, [r] * len(pts), k=0.006), 0.003, lab)
    # two navy bands over his belly, the graphite belt with its buckle
    B = bh()
    for zc in (1.058, 0.996):
        fd.add(Inter(Func(lambda P, zc=zc: np.abs(P[:, 2] - F(zc)) - F(0.025), (-0.5, -0.45, zc - 0.05), (0.5, 0.45, zc + 0.05)),
                     Shell(B, 0.02, 0.022, pad=0.06), 0.005), 0.0, NAVY)
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(0.905)) - F(0.036), (-0.5, -0.45, 0.85), (0.5, 0.45, 0.96)),
                 Shell(B, 0.024, 0.026, pad=0.06), 0.005), 0.0, GRAPHITE)
    p, n = _hit(lambda P: B.eval(P, margin=0.1) - F(0.037), v3((0, -0.7, 0.905)), (0, 1, 0))
    R = _frame(n)
    bc = p + n * 0.008
    fd.add(RoundBox(bc, (0.05, 0.036, 0.01), 0.008, R=R), 0.004, STEEL)
    def chevron(P):
        q = (P - bc.astype(F)) @ R.astype(F)
        c = np.abs(q[:, 1] + F(0.006) - np.abs(q[:, 0]) * F(0.7)) - F(0.0055)
        return np.maximum(np.maximum(c, np.abs(q[:, 0]) - F(0.026)), F(0.004) - q[:, 2])
    fd.paint(Func(chevron, bc - 0.06, bc + 0.06), VIOLET)
    # navy plates on his hips (over the belt's ends, down the sides of his hips)
    for sx in (-1, 1):
        def hip_reg(P, sx=sx):
            a = np.arctan2(P[:, 1] - F(0.04), P[:, 0] * F(sx))
            return np.maximum(np.abs(a) - F(0.62), np.maximum(F(0.765) - P[:, 2], P[:, 2] - F(0.875)))
        fd.add(Inter(Func(hip_reg, (sx * 0.05 - 0.35, -0.35, 0.7), (sx * 0.05 + 0.35, 0.4, 0.92)),
                     Shell(B, 0.046, 0.02, pad=0.06), 0.005), 0.0, NAVY)
    return fd


def core_field():
    """The heart-shaped core in its bezel (GlowCore)."""
    fd = Field("Core")
    fd.add(heart_prim(0.0, (-0.006, 0.0068)), 0.0)
    return fd


# ======================================================================================= pauldrons ("Shoulders")
def pauldron_c(side):
    sx = -1 if side == "R" else 1
    return J["shoulder_" + side] + v3((sx * 0.025, -0.005, 0.03))


def pauldron_u(side):
    sx = -1 if side == "R" else 1
    return norm(v3((sx * 0.62, 0.0, 1.0)))


PD_R = 0.1                               # the pauldron's sphere (round the deltoid) ...
PD_OFF, PD_T = 0.036, 0.024              # ... the cap: its offset and thickness


def _crack_axes():
    """The left cap's crack runs over its top from front to back (along S), zigzagging along W."""
    u = pauldron_u("L")
    S = norm(v3((0, 1, 0)) - u * float(u[1]))
    W = norm(np.cross(u, S))
    return u, S, W


def crack_points():
    c = pauldron_c("L")
    u, S, W = _crack_axes()
    r_out = PD_R + PD_OFF + PD_T / 2
    pts = []
    for k in range(9):
        t = -1.0 + 2.0 * k / 8
        d = norm(u + S * (t * 0.62) + W * (0.07 * (1 if k % 2 else -1) + 0.05 * t))
        pts.append(c + d * (r_out + 0.002))
    return pts


def tape_strips():
    """The two strips of tape over the left pauldron's crack, crossed in an X on its front half: (middle on the
    surface, its normal, along, across)."""
    c = pauldron_c("L")
    u, S, W = _crack_axes()
    m = norm(u - S * 0.3)
    out = []
    for ang in (0.7, -0.7):
        w = norm(W - m * float(W @ m))
        along = norm(axis_angle(m, ang) @ w)
        out.append((c + m * (PD_R + PD_OFF + PD_T / 2), m, along, norm(np.cross(m, along))))
    return out


def shoulders_field():
    """Navy pauldrons (6) with raised graphite rims (5), a lame under each; the left one cracked across (a dark seam) and
    patched with an X of grey tape (9)."""
    fd = Field("Shoulders")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        c, u = pauldron_c(side), pauldron_u(side)
        sph = Sphere(c, PD_R)
        lo, hi = c - 0.3, c + 0.3
        def cap(P, c=c, u=u, sx=sx):
            return np.maximum(F(-0.015) - (P - c.astype(F)) @ u.astype(F), F(0.2) - P[:, 0] * F(sx))
        fd.add(Inter(Func(cap, lo, hi), Shell(sph, PD_OFF, PD_T, pad=0.1), 0.006), 0.0, NAVY)
        def rim(P, c=c, u=u, sx=sx):
            s = (P - c.astype(F)) @ u.astype(F)
            return np.maximum(np.abs(s + F(0.01)) - F(0.009), F(0.205) - P[:, 0] * F(sx))
        fd.add(Inter(Func(rim, lo, hi), Shell(sph, PD_OFF + 0.006, PD_T + 0.01, pad=0.1), 0.004), 0.004, GRAPHITE)
        def lame(P, c=c, u=u, sx=sx):
            s = (P - c.astype(F)) @ u.astype(F)
            out = (P - c.astype(F)) @ np.array([sx, 0.0, 0.0], F)
            return np.maximum(np.maximum(np.abs(s + F(0.058)) - F(0.017), F(0.0) - out), F(0.21) - P[:, 0] * F(sx))
        fd.add(Inter(Func(lame, lo, hi), Shell(sph, PD_OFF + 0.002, 0.022, pad=0.1), 0.004), 0.0, NAVY)
    # the crack across the left cap, and the tape over it
    c = pauldron_c("L")
    pts = crack_points()
    fd.sub(Chain(pts, [0.004] * len(pts), k=0.002), 0.002)
    fd.paint(Chain(pts, [0.008] * len(pts), k=0.004), SEAM)
    for mid, m, along, across in tape_strips():
        def strip(P, mid=mid, along=along, across=across):
            q = P - mid.astype(F)
            return np.maximum(np.abs(q @ across.astype(F)) - F(0.017), np.abs(q @ along.astype(F)) - F(0.068))
        crinkle = lambda P: F(0.0007) * NOISE(P * F(90))
        fd.add(Inter(Func(strip, mid - 0.1, mid + 0.1), Shell(Sphere(c, PD_R), PD_OFF + PD_T / 2 + 0.003, 0.005, pad=0.1,
                                                                disp=crinkle, disp_amp=0.001), 0.002), 0.002, TAPE)
    return fd


# ======================================================================================= arms ("Arms") and the blades
def arm_hull(side, upper):
    f = Field("Arm" + side)
    for i, (p, k) in enumerate(upper_arm_prims(side) if upper else forearm_prims(side)[:2]):
        f.add(p, k if i else 0.0)
    return f


BLADE_OFF = 0.066                        # the blade's plane: this far out over the back of the forearm and fist
BLADE_L = 0.43                           # its point: this far past the wrist
BLADE_ROOT = -0.15                       # its root, inside the housing
BLADE_HW = 0.032                         # its half width (edges included)
EDGE_W = 0.0135                          # the glowing edges' width
HOUSING_C = -0.075                       # the housing's middle along the forearm (from the wrist)


def blade_axes(side):
    """(origin at the wrist on the blade's plane, along (the forearm), across (toward the thumb), normal (toward the
    palm)): the blade lies in the plane (along, across), BLADE_OFF out over the back of the forearm."""
    el, wr = J["elbow_" + side], J["wrist_" + side]
    a = norm(wr - el)
    _w, f, n, t = hand_frame(side)
    nn = norm(n - a * (n @ a))
    tt = norm(np.cross(a, nn))
    if tt @ t < 0:
        tt = -tt
    return wr - nn * BLADE_OFF, a, tt, nn


def blade_tip(side):
    O, a, tt, nn = blade_axes(side)
    return O + a * BLADE_L


def _blade_hw(u):
    taper = F(BLADE_HW) - F(0.005) * np.clip(u / F(BLADE_L), 0, 1)
    tip = np.clip((F(BLADE_L) - u) / F(0.08), 0, 1) ** F(0.7)
    return taper * tip


def _blade_box(side):
    O, a, tt, nn = blade_axes(side)
    p0, p1 = O + a * BLADE_ROOT, O + a * BLADE_L
    return np.minimum(p0, p1) - 0.045, np.maximum(p0, p1) + 0.045


def _blade_q(P, side):
    O, a, tt, nn = blade_axes(side)
    q = P - O.astype(F)
    return q @ a.astype(F), q @ tt.astype(F), q @ nn.astype(F)


def blade_core(side):
    O, a, tt, nn = blade_axes(side)
    def fn(P):
        u, v, w = _blade_q(P, side)
        hw = _blade_hw(u) - F(EDGE_W - 0.002)
        th = F(0.0058) - F(0.0022) * np.clip(np.abs(v) / np.maximum(hw, F(0.004)), 0, 1)
        return np.maximum(np.maximum(np.abs(v) - hw, np.abs(w) - th), np.maximum(F(BLADE_ROOT) - u, u - F(BLADE_L)))
    return Func(fn, *_blade_box(side))


def blade_edge(side):
    O, a, tt, nn = blade_axes(side)
    def fn(P):
        u, v, w = _blade_q(P, side)
        hw = _blade_hw(u)
        return np.maximum(np.maximum(np.abs(v) - hw, F(hw - EDGE_W) - np.abs(v)),
                          np.maximum(np.abs(w) - F(0.0074), np.maximum(F(BLADE_ROOT + 0.03) - u, u - F(BLADE_L))))
    return Func(fn, *_blade_box(side))


def blades_field():
    """The blades' steel cores (10)."""
    fd = Field("Blades")
    for side in ("R", "L"):
        fd.add(blade_core(side), 0.0, STEEL)
    return fd


def edge_field(side):
    fd = Field("Edge" + side)
    fd.add(blade_edge(side), 0.0)
    return fd


def blade_bone(side):
    O, a, tt, nn = blade_axes(side)
    return O + a * HOUSING_C, O + a * BLADE_L


def arms_field():
    """Graphite (5) plates on his upper arms, steel (10) elbow cops, graphite gauntlets with a navy (6) panel along the
    outside, the navy blade housing on each (its mouth at the wrist, a steel lip), graphite knuckle plates."""
    fd = Field("Arms")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        ua = arm_hull(side, True)
        fa = arm_hull(side, False)
        def band(P, a=sh, b=el, t0=0.42, t1=0.86):
            d, t = _seg(P, a, b)
            return np.maximum(np.maximum(F(t0) - t, t - F(t1)), d - F(0.2))
        fd.add(Inter(Func(band, sh - 0.3, el + 0.3), Shell(ua, 0.017, 0.02, pad=0.06), 0.004), 0.0, GRAPHITE)
        # the elbow cop (at the back of the elbow), a little down the forearm
        a = norm(wr - el)
        back = norm(v3((sx * 0.35, 1.0, 0.1)) - a * float(v3((sx * 0.35, 1.0, 0.1)) @ a))
        ec = el + a * 0.016
        def cop(P, ec=ec, back=back):
            return F(-0.006) - (P - ec.astype(F)) @ back.astype(F)
        fd.add(Inter(Func(cop, ec - 0.15, ec + 0.15), Shell(Sphere(ec, 0.058), 0.014, 0.018, pad=0.05), 0.004), 0.0, STEEL)
        # the gauntlet
        def fband(P, a_=el, b_=wr):
            d, t = _seg(P, a_, b_)
            return np.maximum(np.maximum(F(0.2) - t, t - F(0.97)), d - F(0.2))
        fd.add(Inter(Func(fband, el - 0.3, wr + 0.3), Shell(fa, 0.016, 0.022, pad=0.06), 0.004), 0.0, GRAPHITE)
        O, ax, tt, nn = blade_axes(side)
        def outer(P, O=O, nn=nn):
            return ((P - O.astype(F)) @ nn.astype(F)) - F(BLADE_OFF - 0.045)
        fd.paint(Func(outer, el - 0.3, wr + 0.3), NAVY)
        # the blade housing along the outside of the forearm, its mouth just past the wrist
        Rh = np.stack([tt, nn, ax], 1)
        hc = O + ax * HOUSING_C
        fd.add(RoundBox(hc, (0.044, 0.026, 0.094), 0.014, R=Rh), 0.008, NAVY)
        fd.add(RoundBox(O + ax * (HOUSING_C + 0.082), (0.047, 0.029, 0.008), 0.006, R=Rh), 0.004, STEEL)
        fd.sub(RoundBox(O + ax * (HOUSING_C + 0.094), (0.036, 0.0095, 0.03), 0.004, R=Rh), 0.002)
        def hlines(P, hc=hc, ax=ax):
            s = (P - hc.astype(F)) @ ax.astype(F)
            return np.minimum(np.abs(s + F(0.03)) - F(0.0025), np.abs(s - F(0.03)) - F(0.0025))
        fd.paint(Func(hlines, hc - 0.15, hc + 0.15), SEAM)
        # the knuckle plate over the back of the fist
        _w, f, n, t = hand_frame(side)
        fc = fist_center(side)
        Rk = np.stack([t, n, f], 1)
        fd.add(RoundBox(fc - n * 0.054 + f * 0.006, (0.052, 0.01, 0.046), 0.008, R=Rk), 0.0, GRAPHITE)
    return fd


# ======================================================================================= legs ("Legs")
def leg_hull(side, thigh):
    f = Field("Leg" + side)
    for i, (p, k) in enumerate(leg_prims(side)[:2] if thigh else shin_prims(side)):
        f.add(p, k if i else 0.0)
    return f


def foot_hull(side):
    f = Field("Foot" + side)
    foot(f, side)
    return f


SHOE_TOP = 0.128


def legs_field():
    """Graphite (5) thigh plates with a navy (6) stripe, navy knee cops with a steel (10) boss, graphite shin guards with
    navy sides, armoured graphite shoes with black rubber (15) soles and a navy toe cap."""
    fd = Field("Legs")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        tl, sl = leg_hull(side, True), leg_hull(side, False)
        def tband(P, a=hip, b=kn, sx=sx):
            d, t = _seg(P, a, b)
            ax_ = (a + (b - a) * 0.5).astype(F)
            front = (P[:, 1] - ax_[1]) - F(0.03) - F(0.06) * np.maximum((P[:, 0] - ax_[0]) * F(sx), F(0))
            return np.maximum(np.maximum(F(0.2) - t, t - F(0.72)), front)
        fd.add(Inter(Func(tband, hip - 0.3, kn + 0.3), Shell(tl, 0.017, 0.022, pad=0.06), 0.005), 0.0, GRAPHITE)
        fd.paint(Func(lambda P, sx=sx, x0=lerp(hip, kn, 0.5)[0], zk=kn[2]: np.maximum(np.abs((P[:, 0] - F(x0)) * F(sx) - F(0.035)) - F(0.012),
                                                                                  F(zk + 0.05) - P[:, 2]), hip - 0.3, kn + 0.3), NAVY)
        # the knee cop, a little below the knee
        kc = kn + v3((0, -0.034, -0.016))
        fd.add(Inter(Func(lambda P, kc=kc: (P[:, 1] - F(kc[1] + 0.02)), kc - 0.2, kc + 0.2),
                     Shell(Ellipsoid(kc, (0.07, 0.058, 0.064)), 0.012, 0.02, pad=0.05), 0.006), 0.0, NAVY)
        kb, kn_ = _hit(lambda P, kc=kc: Ellipsoid(kc, (0.07, 0.058, 0.064))(P) - F(0.022), kc + v3((0, -0.4, 0)), (0, 1, 0))
        if kb is not None:
            fd.add(Cylinder(kb, 0.02, 0.012, rr=0.004, R=rot_from_axes(z_axis=kn_)), 0.004, STEEL)
        # the shin guard
        def sband(P, a=kn, b=an, sx=sx):
            d, t = _seg(P, a, b)
            ax_ = (a + (b - a) * 0.5).astype(F)
            front = (P[:, 1] - ax_[1]) - F(0.04)
            return np.maximum(np.maximum(F(0.34) - t, t - F(0.84)), front)
        fd.add(Inter(Func(sband, kn - 0.3, an + 0.3), Shell(sl, 0.016, 0.022, pad=0.06), 0.005), 0.0, GRAPHITE)
        fd.paint(Func(lambda P, sx=sx, x0=lerp(kn, an, 0.5)[0], zk=kn[2]: np.maximum(F(0.04) - np.abs(P[:, 0] - F(x0)), P[:, 2] - F(zk - 0.04)),
                      kn - 0.3, an + 0.3), NAVY)
        # the shoe: a shell over the foot below the ankle, a toe cap, a thick sole
        fh = foot_hull(side)
        flo, fhi = fh.bounds()
        fd.add(Inter(Func(lambda P: P[:, 2] - F(SHOE_TOP) + F(0.03) * (P[:, 1] - F(an[1])), flo - 0.1, fhi + 0.1),
                     Shell(fh, 0.012, 0.018, pad=0.06), 0.005), 0.0, GRAPHITE)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.paint(Func(lambda P, an=an, fwd=fwd: F(0.13) - (P - an.astype(F)) @ fwd.astype(F), flo - 0.1, fhi + 0.1), NAVY)
        fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.098)), (0.074, 0.172, 0.014), 0.008, R=Rz), 0.006, RUBBER)
    return fd


# ======================================================================================= the violet scarf and armband ("Cloth")
def _cu_surface(P):
    return th().eval(P, margin=0.15) - F(CU_OUT + 0.012)


def scarf_knot():
    """The knot: on the cuirass at the left of his chest, just below the scarf's roll."""
    p, n = _hit(_cu_surface, v3((0.092, -0.7, 1.39)), (0, 1, 0))
    return p + n * 0.026, n


def scarf_tails():
    """(points, normals) of the scarf's two tails over the cuirass: one from the knot down his chest on his left, one
    from the knot up over his left shoulder and down his back."""
    k, kn = scarf_knot()
    front = [(k + kn * -0.012 + v3((0.004, 0.0, -0.03)), kn)]
    for x, z in ((0.104, 1.31), (0.112, 1.25), (0.118, 1.19), (0.122, 1.14)):
        p, n = _hit(_cu_surface, v3((x, -0.7, z)), (0, 1, 0))
        front.append((p + n * 0.004, n))
    back = [(k + v3((0.03, 0.03, 0.03)), norm(kn + v3((0, 0, 0.8))))]
    p, n = _hit(_cu_surface, v3((0.175, 0.03, 1.9)), (0, 0, -1))
    back.append((p + n * 0.018, n))
    for x, z in ((0.17, 1.42), (0.168, 1.34), (0.166, 1.26), (0.162, 1.18), (0.158, 1.11)):
        p, n = _hit(_cu_surface, v3((x, 0.75, z)), (0, -1, 0))
        back.append((p + n * 0.004, n))
    return front, back


ARMBAND_T = 0.6


def _densify(pts, nrm, n):
    """Catmull-Rom through the points, n samples per span (a smooth tail, not a string of beads)."""
    P = [v3(p) for p in pts]
    N = [v3(x) for x in nrm]
    out, on = [], []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for j in range(n):
            t = j / float(n)
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
            out.append(q)
            on.append(norm(N[i] * (1 - t) + N[i + 1] * t))
    out.append(P[-1])
    on.append(N[-1])
    return out, on


def cloth_field():
    """Violet cloth (8): the scarf rolled round his neck and lying in a thick roll on the cuirass round the neck's
    opening, knotted at his left, its tails ragged at the ends; the armband round his left upper arm (over its plate)."""
    fd = Field("Cloth")
    T = th()
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    folds = lambda P: (F(0.0035) * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(0.06)) * F(9) + F(2) * NOISE(P * F(9)))
                       + F(0.0012) * NOISE(P * F(40)))
    # the roll lying on the cuirass round the neck's opening
    ring = lambda P: np.abs(neck_dist(P) - F(0.15)) - F(0.048)
    fd.add(Inter(Func(lambda P: np.maximum(ring(P), F(1.3) - P[:, 2]), (-0.3, -0.3, 1.25), (0.3, 0.36, 1.7)),
                 Shell(T, CU_OUT + 0.018, 0.038, pad=0.08, disp=folds, disp_amp=0.004), 0.012), 0.0, VIOLET)
    # wound round his neck above it
    def wrap(P):
        top = F(1.478) + F(0.03) * smoothstep(-0.05, 0.12, P[:, 1])
        return np.maximum(P[:, 2] - top, F(1.36) - P[:, 2])
    fd.add(Inter(Func(wrap, (-0.25, -0.25, 1.3), (0.25, 0.3, 1.6)), Shell(nk, 0.042, 0.04, pad=0.1, disp=folds, disp_amp=0.004), 0.01),
           0.02, VIOLET)
    k, kn = scarf_knot()
    fd.add(Ellipsoid(k, (0.046, 0.038, 0.04), R=_frame(kn) @ euler(0, 0, 0.5), disp=lambda P: F(0.002) * NOISE(P * F(30)),
                     disp_amp=0.003), 0.012, VIOLET)
    front, back = scarf_tails()
    rag = lambda P: F(0.002) * NOISE(P * F(26))
    for tail, w0, w1 in ((front, 0.05, 0.064), (back, 0.056, 0.072)):
        pts, nrm = _densify([p for p, n in tail], [n for p, n in tail], 3)
        ws = list(np.linspace(w0, w1, len(pts)))
        fd.add(Lock(pts, ws, [0.012] * len(pts), nrm, k=0.012, overlap=1.9, disp=rag, disp_amp=0.002), 0.008, VIOLET)
        # ragged ends: notches cut into the last segment
        e, e0 = pts[-1], pts[-2]
        d = norm(e - e0)
        for j, o in enumerate((-0.62, 0.04, 0.6)):
            Rn = rot_from_axes(z_axis=d, y_axis=nrm[-1])
            fd.sub(Ellipsoid(e + d * (0.004 + 0.01 * (j % 2)) + Rn[:, 0] * (o * w1), (0.012, 0.03, 0.026), R=Rn), 0.003)
    # the armband round his left upper arm
    sh, el = J["shoulder_L"], J["elbow_L"]
    ua = arm_hull("L", True)
    def ab(P):
        d, t = _seg(P, sh, el)
        return np.maximum(np.abs(t - F(ARMBAND_T)) - F(0.075), d - F(0.2))
    fd.add(Inter(Func(ab, sh - 0.3, el + 0.3), Shell(ua, 0.035, 0.017, pad=0.06, disp=lambda P: F(0.0008) * NOISE(P * F(50)), disp_amp=0.001),
                 0.004), 0.0, VIOLET)
    return fd


# ======================================================================================= painting
def warm_points():
    return []


# ======================================================================================= build config
GLB_NAME = "glitch"
ROOT_NAME = "HeroGlitchHQ"
TEX_PREFIX = "hero"
MAT_NAME = "GlitchMat"
MESH_NAME = "Glitch"
BASE_MODULE = "glitch_base"
ANIM_MODULE = "anim_glitch"
PARTS = ["Skin", "Head", "Armor", "Shoulders", "Arms", "Legs", "Cloth", "Blades",
         "Face", "Spark", "Core", "EdgeR", "EdgeL", "Flash"]
REGION_PARTS = ("Skin", "Head", "Armor", "Shoulders", "Arms", "Legs", "Cloth", "Blades")
MAT_OVERRIDES = {nm: ("android", {"name": "HQ_Glitch" + nm}) for nm in REGION_PARTS}
GLOW = {"Face": (TEAL, 1.3, 0.5), "Spark": ((0.92, 1.0, 0.97), 1.0, 0.95), "Core": (TEAL, 1.3, 0.5),
        "EdgeR": (TEAL, 1.3, 0.5), "EdgeL": (TEAL, 1.3, 0.5), "Flash": ((0.78, 1.0, 0.95), 1.5, 0.7)}
LOW_TARGETS = {"Skin": 5200, "Head": 2600, "Armor": 3800, "Shoulders": 1600, "Arms": 3000, "Legs": 3600, "Cloth": 1700,
               "Blades": 300, "Face": 500, "Spark": 60, "Core": 120, "EdgeR": 240, "EdgeL": 240, "Flash": 200}
AO_EXCLUDE = ["Blades", "EdgeR", "EdgeL", "Flash"]


def prop_bones():
    """Each blade on its own bone (a child of its forearm: from the housing's middle to the point); the eyes' flash on
    `flash` (a child of the head)."""
    out = []
    for side in ("R", "L"):
        a, b = blade_bone(side)
        out.append(("blade." + side, a, b, "forearm." + side))
    a, b = flash_bone()
    out.append(("flash", a, b, "head"))
    return out


def _islands(ob):
    """[(vertex indices, centroid)] of the mesh's connected pieces."""
    from mathutils import Vector
    me = ob.data
    n = len(me.vertices)
    parent = list(range(n))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    out = []
    for idx in groups.values():
        c = Vector((0, 0, 0))
        for i in idx:
            c += me.vertices[i].co
        out.append((idx, c / len(idx)))
    return out


def _rigid_islands(ob, classify, wts=None):
    """Every piece rigid on the bone `classify(centroid)` names (or blended as `wts(bone)` gives)."""
    for g in list(ob.vertex_groups):
        ob.vertex_groups.remove(g)
    tally = {}
    for idx, c in _islands(ob):
        b = classify(c)
        w = wts(b) if wts else {b: 1.0}
        for nm, x in w.items():
            g = ob.vertex_groups.get(nm) or ob.vertex_groups.new(name=nm)
            g.add(idx, x, "REPLACE")
        tally[b] = tally.get(b, 0) + 1
    print("[glitch] %s pieces:" % ob.name, tally, flush=True)


def _torso_bone(c):
    return "chest" if c.z > 1.1 else ("spine" if c.z > 0.96 else "root")


def _arm_bone(c):
    side = "R" if c.x < 0 else "L"
    p = np.array([[c.x, c.y, c.z]], F)
    du, tu = _seg(p, J["shoulder_" + side], J["elbow_" + side])
    df, tf = _seg(p, J["elbow_" + side], J["wrist_" + side])
    if tf[0] > 1.03:
        return "hand." + side
    return ("upperarm." if du[0] + 0.02 < df[0] and tu[0] < 1.0 else "forearm.") + side


def _leg_bone(c):
    side = "R" if c.x < 0 else "L"
    if c.z > J["knee_" + side][2] + 0.03:
        return "thigh." + side
    if c.z > J["ankle_" + side][2] + 0.035:
        return "shin." + side
    return "foot." + side


def armor_weights(ob, skin_ob, arm):
    _rigid_islands(ob, _torso_bone)


def shoulder_weights(ob, skin_ob, arm):
    """Each pauldron mostly with its upper arm, a little with the clavicle (it rides the shoulder as the arm lifts)."""
    _rigid_islands(ob, lambda c: "upperarm." + ("R" if c.x < 0 else "L"),
                   wts=lambda b: {b: 0.72, "clavicle." + b[-1]: 0.28})


def arms_weights(ob, skin_ob, arm):
    _rigid_islands(ob, _arm_bone)


def legs_weights(ob, skin_ob, arm):
    _rigid_islands(ob, _leg_bone)


def blades_weights(ob, skin_ob, arm):
    _rigid_islands(ob, lambda c: "blade." + ("R" if c.x < 0 else "L"))


def cloth_weights(ob, skin_ob, arm):
    """The scarf with his neck and chest; the armband rigid on his left upper arm."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed={"neck", "chest"}, caps=None)
    idx = [v.index for v in ob.data.vertices if v.co.x > 0.27]
    for g in list(ob.vertex_groups):
        g.remove(idx)
    g = ob.vertex_groups.get("upperarm.L") or ob.vertex_groups.new(name="upperarm.L")
    g.add(idx, 1.0, "REPLACE")


def weight_rules():
    return {
        "Head": ("rigid", "head"), "Face": ("rigid", "head"), "Spark": ("rigid", "head"), "Flash": ("rigid", "flash"),
        "Armor": ("custom", armor_weights), "Core": ("rigid", "chest"),
        "Shoulders": ("custom", shoulder_weights),
        "Arms": ("custom", arms_weights),
        "Legs": ("custom", legs_weights),
        "Cloth": ("custom", cloth_weights),
        "Blades": ("custom", blades_weights), "EdgeR": ("rigid", "blade.R"), "EdgeL": ("rigid", "blade.L"),
    }


def uv_boost(c, part):
    if part == "Head" and c.y < 0.0 and c.z > 1.5:
        return 1.8
    if part in ("Head", "Shoulders", "Armor"):
        return 1.15
    if part in ("Legs", "Blades"):
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Head", head_field(), 0.0018 if fine else 0.0026),
        ("Armor", armor_field(), 0.0024 if fine else 0.0034),
        ("Shoulders", shoulders_field(), 0.0018 if fine else 0.0026),
        ("Arms", arms_field(), 0.002 if fine else 0.003),
        ("Legs", legs_field(), 0.0024 if fine else 0.0034),
        ("Cloth", cloth_field(), 0.0022 if fine else 0.0032),
        ("Blades", blades_field(), 0.0012 if fine else 0.0018),
        ("Face", face_glow_field(), 0.0012 if fine else 0.0016),
        ("Spark", spark_field(), 0.0008 if fine else 0.0012),
        ("Core", core_field(), 0.0012 if fine else 0.0016),
        ("EdgeR", edge_field("R"), 0.0012 if fine else 0.0016),
        ("EdgeL", edge_field("L"), 0.0012 if fine else 0.0016),
        ("Flash", flash_field(), 0.0014 if fine else 0.002),
    ]
