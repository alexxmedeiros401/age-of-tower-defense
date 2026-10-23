"""The Laser Turret (HQ tower, Digital Age; Ranged lineage): a pedestal-mounted laser emitter of the tech corps and the
gunner who aims it by its twin grips. Rest pose: he stands in an A-pose facing -Y (the way it shoots), feet at z = 0; the
turret stands on its pedestal before him (its grips half a metre in front of his belly, its emitter lens a metre and a half
out), the tower turns about a point between them (YAW_PIVOT).

Him: the Missile Launcher's burly body (torsion.py; the Field Gun's gripping hands) with his own face: a warm light-tan
face, clean-shaven with a dark shadow of stubble on the jaw, a square jaw, a straight nose, dark brows with a confident
arch over steady dark-hazel eyes, a closed mouth with a hint of a smile at its corners; focused and sure of himself. A
slim graphite helmet with a navy crest down its middle (a violet light strip on the crest: `Crest`, shipped glowing), its
smoked visor flipped up onto its brow (glossy dark glass in a graphite frame, hinged at the temples), a black rubber trim
round its edge; slim black ear pieces over his ears (a violet status light on each, a boom mic to the corner of his mouth),
a black chin strap. A matte black under-suit with a high collar and long sleeves; a graphite armour shell over it: front
and back plates with navy borders and panel lines (violet light strips across his upper chest and on the power pack on
his back: `Strips`, shipped glowing), a navy segmented abdomen band with a slim black pouch on each side, navy shoulder
straps; two-lame graphite pauldrons with navy edges and a violet stripe; graphite forearm guards (a violet ring round
each); navy techwear trousers with graphite thigh plates and knee guards, a black belt with a gunmetal buckle; black
boots; black gloves with graphite knuckle plates.

The turret: a graphite pedestal (a bolted foot plate with a junction box and its cables into the floor, a gunmetal column,
a cable up its back) carrying a turntable and a fork (`yoke`, it traverses); in the fork on trunnions the gun (`gun`, it
elevates): a sleek gloss-black housing with gunmetal side panels, its twin grips behind (black rubber on gunmetal arms, a
violet thumb bar between them), a small sight block on top, a charge readout on its back face; on its right side the power
cell in a graphite cradle (a violet charge window) with cables into the housing; the vent hatch on its top (`vent`,
louvred, it pops open to dump heat; a glowing grille under it); forward of the housing the barrel: the capacitor coil
(`Coil`, violet windings shipped glowing on the `coil` bone, in a gunmetal cage), six cooling fins, and the emitter shroud,
a flared gloss-black cup with a gunmetal rim round the big front lens (`Lens`, shipped glowing violet, on the `lens` bone:
its head is the lens's centre, the bone points the way the beam leaves). Violet light strips along the housing's sides,
the cell's window, the readout and the grille ship as `Trim` (glowing, on `gun`).

Painted labels (material `modern_kit`): 0 the base colour (gloss black on the gun, graphite armour, navy trousers, black
suit), 5 black, 6 violet paint, 7 white, 8 the second colour (navy on armour and helmet, graphite on gun and trousers),
9 gunmetal, 10 bright steel, 11 smoked glass, 12 black rubber, 13 hazard yellow. Boots and gloves `leather_dyed` (0 black
leather, 5 graphite plates / soles)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp, project_to
from ugo import _blend_add
from torsion import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD,
                     EYE_R, eye_c, smoothstep, hand_frame, HAND_S, fist_center, foot, traps, neck_prim, deltoid,
                     upper_arm, eyes_field, skull, torso_prims, TORSO, TORSO_Z, torso_bones)
from field_gun import hand, palm_pt, legs_hull, boot_hull, _hand_hull, ARM_LEN, tunic_neck
from cannon import capped_cone, poly2d, _arm_coord
from musketeer import _fgrad
import missile as _m
from missile import (stencil, shirt_hull, SHIRT_OFF, SHIRT_T, SHIRT_FACE, SHIRT_HEM, rim_z, JAW, CHIN, cheekbone,
                     jaw_corner, face_hull, CUP_C, CUP_R, PC_IN, PLATE_T, PLATE_OFF, CB_T, CB_OFF, STRAP_T, _plate_region,
                     _cb_region, _strap_region, carrier_outer, _surface_frame, BELT_Z, TROUSER_TOP, TROUSER_BOT)

IRIS = ((0.2, 0.13, 0.07), (0.44, 0.3, 0.14))            # steady dark-hazel eyes (prep.paint_eyes)
GRAPHITE = (0.16, 0.17, 0.2)                              # the corps' armour (the brief)
NAVY = (0.12, 0.16, 0.3)                                  # its second colour
BLACK = (0.06, 0.06, 0.07)
GLOSS = (0.05, 0.05, 0.06)                                # the gun's gloss-black housing
GUNMETAL = (0.3, 0.31, 0.34)
VIOLET = (0.85, 0.25, 0.95)                               # the defenders' one accent (emissive)
WHITE = (0.9, 0.9, 0.92)
HAZARD = (0.92, 0.72, 0.14)
SMOKE = (0.06, 0.05, 0.09)                                # smoked glass
BASE_L, BLACK_L, VIO_L, WHITE_L, ALT_L, GUN_L, STEEL_L, GLASS_L, RUBBER_L, HAZ_L = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13
Z_ = v3((0.0, 0.0, 1.0))


# ======================================================================================= head
def stubble_mask(P):
    """The jaw, chin and upper lip below the cheekbones (design coordinates): a dark shadow of a close shave."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.592) + F(0.012) * smoothstep(0.05, 0.12, ax) - F(0.012) * smoothstep(0.06, 0.0, ax) * smoothstep(-0.16, -0.2, y)
    lips = np.sqrt((x / F(0.06)) ** 2 + ((y + F(0.19)) / F(0.05)) ** 2 + ((z - F(1.553)) / F(0.016)) ** 2) - F(1.0)
    back = y - F(0.03) + F(0.04) * smoothstep(1.58, 1.5, z)
    return np.maximum(np.maximum(np.maximum(z - top, F(1.43) - z), back), -lips * F(0.02))


MOUTH_SLOT = [(-0.05, -0.177, 1.556), (-0.026, -0.197, 1.549), (0.0, -0.203, 1.548), (0.026, -0.197, 1.549),
              (0.05, -0.177, 1.556)]


def head(fd):
    """A confident, focused face: a square jaw and chin, cheekbones over flat cheeks, a straight nose, dark brows with a
    confident arch, steady eyes, a closed mouth whose corners turn up a touch. (No ears: the ear pieces cover them.)"""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.79), (0.165, 0.175, 0.12)), 0.08, SKIN)
    fd.add(E(*JAW), 0.07, SKIN)
    fd.add(E(*CHIN), 0.05, SKIN)
    fd.add(E((0.0, -0.17, 1.492), (0.042, 0.026, 0.028)), 0.03, SKIN)                     # the chin's point
    for sx in (-1, 1):
        c, r = cheekbone(sx)
        fd.add(S(c, r), 0.05, SKIN)
        c, r = jaw_corner(sx)
        fd.add(S(c, r), 0.05, SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.114, -0.114, 1.582)), v3((0.022, 0.016, 0.024)) * HS, R=euler(0, 0, sx * -0.5)), hr(0.02))
        pts = [hp((sx * 0.154, -0.055, 1.744)), hp((sx * 0.116, -0.133, 1.756)), hp((sx * 0.061, -0.177, 1.754)), hp((0.0, -0.187, 1.748))]
        fd.add(Chain(pts, [hr(0.012), hr(0.021), hr(0.025), hr(0.023)], k=hr(0.022)), hr(0.033), SKIN)     # brow ridge
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # dark brows, set on the brow ridge: low and level at the inner ends, a confident arch over the outer third
    tuft = lambda P: F(0.0018) * NOISE(P * F(150)) + F(0.0008) * np.sin(P[:, 0] * F(380) + P[:, 2] * F(80))
    for sx in (-1, 1):
        pts = [hp((sx * 0.024, -0.214, 1.754)), hp((sx * 0.064, -0.211, 1.767)), hp((sx * 0.108, -0.192, 1.774)), hp((sx * 0.15, -0.15, 1.762))]
        fd.add(Chain([p + v3((0, 0.005, 0)) for p in pts], [hr(0.01), hr(0.012), hr(0.01), hr(0.005)], k=hr(0.008),
                     disp=tuft, disp_amp=0.003), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.016), hr(0.018), hr(0.016), hr(0.01)], k=hr(0.01)), BROW)
    # eyes open and steady (the upper lid a hair lower than wide open: focused)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.0185))), (sx * 0.12, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.006)), Plane(ec + v3((0, 0, -hr(0.0205))), (sx * -0.08, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0155))), (sx * 0.12, 0.06, -1.0)), hr(0.002)), LASH)
        a = hp((sx * 0.112, -0.132, 1.684))
        fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, 0.0)), hr(0.0018), hr(0.0012)), hr(0.003))               # a crease
    # a straight nose, a little narrower at the bridge
    fd.add(RoundCone(hp((0, -0.19, 1.728)), hp((0, -0.246, 1.632)), hr(0.014), hr(0.022)), hr(0.016), SKIN)
    fd.add(S((0, -0.248, 1.614), 0.026), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.03, -0.222, 1.603), 0.019), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.016, -0.238, 1.593)), v3((0.009, 0.011, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a closed mouth, its corners turned up a touch (sure of himself)
    slot = [hp(p) for p in MOUTH_SLOT]
    fd.sub(Chain(slot, [hr(0.002), hr(0.0026), hr(0.0028), hr(0.0026), hr(0.002)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0038), hr(0.004), hr(0.0038), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.046, -0.179, 1.56), (-0.022, -0.197, 1.56), (0.0, -0.202, 1.561), (0.022, -0.197, 1.56), (0.046, -0.179, 1.56)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0056), hr(0.006), hr(0.0056), hr(0.003)], k=hr(0.005)), hr(0.006), LIP)
    lo_lip = [(-0.044, -0.177, 1.545), (-0.022, -0.194, 1.535), (0, -0.199, 1.533), (0.022, -0.194, 1.535), (0.044, -0.177, 1.545)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0072), hr(0.0082), hr(0.0072), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(RoundCone(hp((0.0, -0.215, 1.594)), hp((0.0, -0.205, 1.568)), hr(0.007), hr(0.006)), hr(0.008), SKIN)      # philtrum


def body_parts(fd):
    """The Missile Launcher's burly body (torsion's torso and limbs, the Field Gun's gripping hands) with this head."""
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        fd.add(upper_arm(side), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.097, 0.1, 0.13), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)
        fd.add(RoundCone(el, wr, 0.08, 0.058), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.1, 0.09, 0.135), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.14, 0.092), 0.065, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.13, 0.12, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.048, SKIN)
        fd.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038, SKIN)
        fd.add(RoundCone(kn, an, 0.088, 0.058), 0.038, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= the helmet, visor and ear pieces
HELMET_OFF, HELMET_T = 0.03, 0.018         # a slim shell over the skull
HELM_OUT = HELMET_OFF + HELMET_T / 2


def helmet_outer(extra=0.0):
    sk = skull()
    return Func(lambda P: sk.eval(P, margin=0.1) - F(HELM_OUT + extra), HEAD_C - 0.4, HEAD_C + 0.4)


def _helmet_keep(P):
    Q = hinv(P)
    return (rim_z(Q) - Q[:, 2]) * F(HS)


def helmet_point(a, zd, out=0.0):
    """A point on the helmet's outer surface at angle a (0 = front, + toward his left) and design height zd; its normal."""
    ho = helmet_outer()
    c = hp((0.0, 0.02, zd))
    d = v3((math.sin(a), -math.cos(a), 0.0))
    h, ok = ray_hit(ho, [c + d * 0.6], [-d], tmax=0.7, step=0.0015)
    p = h[0]
    n = _fgrad(ho.fn, p)
    return p + n * out, n


def crest_points(n=11):
    """Points down the helmet's crest (its middle line, front to back) on its outer surface, and their normals."""
    ho = helmet_outer()
    pts, ns = [], []
    for y in np.linspace(-0.12, 0.215, n):
        o = v3((0.0, y, 2.4))
        h, ok = ray_hit(ho, [o], [v3((0, 0, -1))], tmax=0.8, step=0.0015)
        if not ok[0]:
            continue
        p = h[0]
        Q = hinv(p[None, :].astype(F))
        if float(Q[0, 2] - rim_z(Q)[0]) < 0.045:
            continue
        pts.append(p)
        ns.append(_fgrad(ho.fn, p))
    return pts, ns


def _visor_region(P):
    """< 0 on the flipped-up visor: a band across the helmet's front above its rim, wrapping round to the temples."""
    Q = hinv(P)
    a = np.abs(np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.02))))
    z0 = rim_z(Q) + F(0.028)
    z1 = z0 + F(0.07) - F(0.018) * smoothstep(0.7, 1.15, a)
    return np.maximum(np.maximum(z0 - Q[:, 2], Q[:, 2] - z1), (a - F(1.2)) * F(0.12)) * F(HS)


def helmet_field():
    """Graphite (0): a slim shell, its edge trimmed in black rubber (5); a navy crest (8) down its middle; panel lines; the
    smoked visor flipped up onto its brow (glass 11, a graphite frame), its hinges at the temples (gunmetal 9)."""
    fd = Field("Helmet")
    sk = skull()
    lo, hi = HEAD_C - 0.4, HEAD_C + 0.4
    fd.add(Inter(Shell(sk, HELMET_OFF, HELMET_T, pad=0.08), Func(_helmet_keep, lo, hi), 0.007), 0.0, BASE_L)
    def trim(P):
        Q = hinv(P)
        return (Q[:, 2] - rim_z(Q) - F(0.014)) * F(HS)
    fd.paint(Func(trim, lo, hi), BLACK_L)
    # a panel line round the shell, a hand's breadth above the rim
    def line(P):
        Q = hinv(P)
        return np.abs(Q[:, 2] - rim_z(Q) - F(0.11) - F(0.03) * np.clip(Q[:, 1] / F(0.2), -1, 1)) * F(HS) - F(0.0024)
    fd.paint(Func(line, lo, hi), BLACK_L)
    # the crest: a low navy ridge down the middle
    pts, ns = crest_points()
    fd.add(Lock([p + n * 0.004 for p, n in zip(pts, ns)], [0.024] * len(pts), [0.011] * len(pts), ns, k=0.005), 0.006, ALT_L)
    # the visor, flipped up: smoked glass over the helmet's brow, its frame graphite
    vis = Inter(Shell(sk, HELM_OUT + HELMET_T / 2 + 0.008, 0.013, pad=0.08), Func(_visor_region, lo, hi), 0.004)
    fd.add(vis, 0.004, GLASS_L)
    def frame(P):
        return np.maximum(_visor_region(P), -_visor_region(P) - F(0.007))
    fd.paint(Func(frame, lo, hi), BASE_L)
    for sx in (-1, 1):                                                           # its hinges at the temples
        p, n = helmet_point(sx * 1.28, 1.838, 0.006)
        fd.add(Cylinder(p, 0.019, 0.016, rr=0.005, R=rot_from_axes(z_axis=n)), 0.004, GUN_L)
        fd.add(Sphere(p + n * 0.008, 0.007), 0.002, BASE_L)
    return fd


def crest_field():
    """The violet light strip along the crest's top (shipped glowing)."""
    fd = Field("Crest")
    pts, ns = crest_points()
    pts, ns = pts[1:-1], ns[1:-1]
    fd.add(Lock([p + n * 0.0145 for p, n in zip(pts, ns)], [0.0075] * len(pts), [0.004] * len(pts), ns, k=0.003), 0.0)
    return fd


def comms_field():
    """Slim black (5) ear pieces over his ears, a violet status light (6) and a gunmetal hinge (9) on each, arms up into the
    helmet; the boom mic from the left one to the corner of his mouth; the black chin strap."""
    fd = Field("Comms")
    for sx in (-1, 1):
        c = hp((sx * (CUP_C[0] - 0.004), CUP_C[1], CUP_C[2]))
        R = euler(0, 0, sx * -0.06)
        rad = v3((0.032, 0.054, 0.062))
        fd.add(Inter(Ellipsoid(c, rad * HS, R=R), Plane(c + v3((sx * 0.022, 0, 0)), (sx, 0, 0)), 0.008), 0.0, BLACK_L)
        fd.add(Ellipsoid(c - v3((sx * 0.018, 0, 0)), v3((0.018, 0.05, 0.058)) * HS, R=R), 0.01, BLACK_L)     # the cushion
        fd.add(Cylinder(c + v3((sx * 0.024, 0.0, 0.0)), hr(0.03), 0.01, rr=0.004, R=rot_from_axes(z_axis=(1, 0, 0))), 0.004, BASE_L)
        fd.add(Cylinder(c + v3((sx * 0.03, -0.012, 0.012)), 0.007, 0.008, rr=0.002, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, VIO_L)
        top = hp((sx * 0.192, 0.035, 1.785))
        fd.add(RoundCone(c + v3((sx * 0.004, 0.0, hr(0.055))), top, 0.01, 0.008), 0.006, BLACK_L)
        fd.add(Cylinder(top, 0.011, 0.014, rr=0.004, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, GUN_L)
    pts = [hp(p) for p in ((0.214, -0.02, 1.63), (0.196, -0.1, 1.598), (0.15, -0.178, 1.568), (0.096, -0.218, 1.556))]
    fd.add(Chain(pts, [0.006, 0.0055, 0.005, 0.0045], k=0.004), 0.003, BLACK_L)
    fd.add(Sphere(hp((0.08, -0.226, 1.554)), hr(0.015)), 0.004, BLACK_L)
    hull = face_hull()
    off = Field("StrapHull")
    off.add(Func(lambda P: hull.eval(P, margin=0.05) - F(0.009), HEAD_C - 0.45, HEAD_C + 0.3), 0.0)
    for sx in (-1, 1):
        for guide in (((0.16, -0.052, 1.76), (0.158, -0.068, 1.66), (0.14, -0.07, 1.56), (0.1, -0.086, 1.48), (0.04, -0.112, 1.44)),
                      ((0.165, 0.11, 1.72), (0.16, 0.06, 1.6), (0.14, -0.02, 1.52), (0.1, -0.07, 1.47))):
            pts = project_to(off, np.array([hp((sx * x, y, z)) for x, y, z in guide]), iters=4)
            ns = [_fgrad(off.eval, p) for p in pts]
            fd.add(Lock(list(pts), [0.0075] * len(pts), [0.0026] * len(pts), ns, k=0.003), 0.002, BLACK_L)
    fd.add(Ellipsoid(hp((0.0, -0.125, 1.445)), v3((0.036, 0.028, 0.015)) * HS, R=euler(0.5, 0, 0)), 0.006, BLACK_L)
    return fd


def hair_field():
    """Short dark hair, cropped close: showing under the helmet's edge at his temples and nape, short sideburns."""
    fd = Field("Hair")
    sk = skull()
    strands = lambda P: F(0.0012) * NOISE(P * np.array([90, 90, 30], F)) + F(0.0008) * NOISE(P * F(150))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = z - (rim_z(Q) + F(0.03))
        nape = F(1.585) - z + F(0.04) * smoothstep(0.03, 0.12, ax)
        front = np.where(ax > F(0.13), F(-0.085) - y + F(0.02) * smoothstep(1.66, 1.72, z), F(-0.04) - y)
        side = np.where(y < F(0.08), F(1.63) - z, F(-1.0))
        return np.maximum(np.maximum(np.maximum(top, nape), front), side)
    fd.add(Inter(Shell(sk, 0.004, 0.009, pad=0.06, disp=strands, disp_amp=0.002), Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.004), 0.0)
    return fd


# ======================================================================================= the under-suit
SLEEVE_END = ARM_LEN - 0.03                # (under the gloves' cuffs)


def _suit_sleeve_cut(P):
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2 = _arm_coord(P, side)
        near = (d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3))
        out = np.maximum(out, np.where(near, s - F(SLEEVE_END), F(-1.0)))
    return out


def suit_keep(P):
    return np.maximum(np.maximum(F(SHIRT_HEM) - P[:, 2], tunic_neck(P) + F(0.012)), _suit_sleeve_cut(P))


def suit_field():
    """Matte black (0) under-suit: tucked in at his waist, long sleeves to his wrists (under the gloves), a high collar;
    black seams (5) down the sleeves."""
    fd = Field("Suit")
    base = shirt_hull()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        return F(0.0012) * np.sin(a * F(7) + F(0.9) * NOISE(P * F(3))) + F(0.0009) * NOISE(P * F(20))
    lo, hi = (-1, -0.6, 0.5), (1, 0.6, 1.7)
    fd.add(Inter(Shell(base, SHIRT_OFF, SHIRT_T, pad=0.12, disp=folds, disp_amp=0.003), Func(suit_keep, lo, hi), 0.004), 0.0)
    # the high collar
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    def band(P):
        front = np.clip(-(P[:, 1] - F(0.03)) / F(0.1), 0, 1)
        return np.maximum(F(1.39) - P[:, 2], P[:, 2] - F(1.49) + F(0.035) * front)
    fd.add(Inter(Shell(nk, 0.02, 0.016, pad=0.08), Func(band, (-0.3, -0.3, 1.3), (0.3, 0.3, 1.56)), 0.004), 0.004)
    # padded ribs down the outside of each sleeve (quilted techwear)
    for side in ("R", "L"):
        def rib(P, side=side):
            s, d2 = _arm_coord(P, side)
            sx = -1 if side == "R" else 1
            return np.where((d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3)),
                            np.abs(((s + F(10.0)) % F(0.06)) - F(0.03)) - F(0.0035), F(1.0))
        fd.paint(Func(rib, (-1, -0.6, 0.5), (1, 0.6, 1.7)), BLACK_L)
    return fd


def suit_outer():
    b = shirt_hull()
    return Func(lambda P: b.eval(P, margin=0.1) - F(SHIRT_FACE), (-1, -0.6, 0.5), (1, 0.6, 1.7))


# ======================================================================================= the armour shell
def _plate_edge(P):
    """< 0 in a band along the plates' edges (their navy borders)."""
    return -(_plate_region(P) + F(0.022))


def armour_field():
    """Graphite (0): the front and back plates, hard and smooth, navy borders (8), panel lines (5), a chevron of grooves on
    the chest; the navy (8) segmented abdomen band with a slim black (5) pouch on each side (gunmetal caps, 9); navy
    shoulder straps; the power pack on his back (graphite, navy end caps, gunmetal vents)."""
    fd = Field("Armour")
    base = shirt_hull()
    lo, hi = (-0.8, -0.6, 0.8), (0.8, 0.6, 1.7)
    hard = lambda P: F(0.0005) * NOISE(P * F(40))
    fd.add(Inter(Shell(base, PLATE_OFF, PLATE_T, pad=0.14, disp=hard, disp_amp=0.001), Func(_plate_region, lo, hi), 0.014), 0.0)
    fd.paint(Inter(Func(_plate_edge, lo, hi), Func(_plate_region, lo, hi)), ALT_L)
    fd.add(Inter(Shell(base, CB_OFF, CB_T, pad=0.14), Func(_cb_region, lo, hi), 0.006), 0.008, ALT_L)
    fd.add(Inter(Shell(base, PC_IN + STRAP_T / 2, STRAP_T, pad=0.14), Func(_strap_region, lo, hi), 0.01), 0.01, ALT_L)
    out = PLATE_OFF + PLATE_T / 2
    # the abdomen band's segments
    for zk in (1.05, 1.105):
        def seg(P, zk=zk):
            return np.maximum(np.abs(P[:, 2] - F(zk)) - F(0.004), np.abs(P[:, 0]) - F(0.4))
        fd.sub(Inter(Shell(base, CB_OFF + CB_T / 2, 0.012, pad=0.14), Func(seg, lo, hi), 0.0), 0.002)
    # panel lines: across the front plate under the chest, a chevron above it; down the back plate's middle
    def groove(P, a, b, w=0.0032):
        a, b = a.astype(F), b.astype(F)
        ab = b - a
        t = np.clip(((P[:, [0, 2]] - a) @ ab) / F(ab @ ab), 0, 1)
        q = P[:, [0, 2]] - (a + t[:, None] * ab)
        return np.sqrt((q * q).sum(1)) - F(w)
    front = lambda P: P[:, 1] < F(0.03)
    lines_f = [(np.array([-0.2, 1.16]), np.array([0.2, 1.16])),
               (np.array([-0.17, 1.33]), np.array([0.0, 1.235])), (np.array([0.17, 1.33]), np.array([0.0, 1.235]))]
    for a, b in lines_f:
        fd.sub(Inter(Shell(base, out, 0.014, pad=0.14),
                     Func(lambda P, a=a, b=b: np.where(front(P), groove(P, a, b), F(1.0)), lo, hi), 0.0), 0.002)
    fd.sub(Inter(Shell(base, out, 0.014, pad=0.14),
                 Func(lambda P: np.where(P[:, 1] > F(0.07), groove(P, np.array([0.0, 1.03]), np.array([0.0, 1.38])), F(1.0)), lo, hi), 0.0), 0.002)
    co = carrier_outer()
    # slim pouches on the abdomen band's front corners
    for sx in (-1, 1):
        d = norm(v3((sx * 0.6, -1.0, 0.0)))
        p, n = _surface_frame(co, v3((sx * 0.24, 0.0, 1.06)) - d * 0.8, d)
        n = norm(v3((n[0], n[1], 0.0)))
        R = np.stack([np.cross(Z_, n), Z_, n], axis=1)
        c = p + n * 0.02
        fd.add(RoundBox(c, (0.036, 0.05, 0.02), 0.01, R=R), 0.006, BLACK_L)
        fd.add(RoundBox(c + Z_ * 0.052, (0.03, 0.01, 0.017), 0.005, R=R), 0.004, GUN_L)
    # the power pack on his back
    p, n = pack_mount()
    R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
    pc = p + n * PACK_HALF[2]
    fd.add(RoundBox(pc, PACK_HALF, 0.024, R=R), 0.008, BASE_L)
    for sz in (-1, 1):
        fd.add(RoundBox(pc + R @ v3((0, sz * (PACK_HALF[1] - 0.012), 0.0)), (PACK_HALF[0] + 0.006, 0.014, PACK_HALF[2] + 0.004), 0.008, R=R), 0.004, ALT_L)
    fd.sub(RoundBox(pc + R @ v3((0.0, -0.04, PACK_HALF[2])), (0.07, 0.012, 0.006), 0.003, R=R), 0.002)        # the window's well
    for k in range(4):                                                                                       # vents
        fd.add(RoundBox(pc + R @ v3((-0.06 + 0.04 * k, 0.045, PACK_HALF[2] - 0.002)), (0.012, 0.03, 0.004), 0.003, R=R), 0.002, GUN_L)
    return fd


PACK_HALF = (0.12, 0.13, 0.035)            # the power pack: across, up, its depth (half)


def pack_mount():
    co = carrier_outer()
    return _surface_frame(co, v3((0.0, 0.8, 1.2)), v3((0, -1, 0)))


def strip_pts_front(sx):
    """The chest strip on his side sx: points on the plate's face just above the chevron groove (and its normal)."""
    co = carrier_outer()
    out = []
    for t in np.linspace(0.0, 1.0, 6):
        x = sx * (0.155 - 0.11 * t)
        z = 1.345 - 0.085 * t
        p, n = _surface_frame(co, v3((x, -0.8, z)), v3((0, 1, 0)))
        out.append((p, n))
    return out


def strips_field():
    """The violet light strips (shipped glowing): one along each arm of the chest chevron, the pack's window."""
    fd = Field("Strips")
    for sx in (-1, 1):
        pn = strip_pts_front(sx)
        fd.add(Lock([p + n * 0.003 for p, n in pn], [0.0085] * len(pn), [0.0035] * len(pn), [n for p, n in pn], k=0.003), 0.0)
    p, n = pack_mount()
    R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
    pc = p + n * PACK_HALF[2]
    fd.add(RoundBox(pc + R @ v3((0.0, -0.04, PACK_HALF[2] - 0.004)), (0.064, 0.008, 0.004), 0.003, R=R), 0.0)
    return fd


# ======================================================================================= pauldrons and forearm guards
def _pauldron_region(P, side, lame):
    sx = -1 if side == "R" else 1
    sh = J["shoulder_" + side]
    c = sh + v3((sx * 0.035, 0.0, 0.03))
    d = np.sqrt(((P - c.astype(F)) ** 2).sum(1))
    z = P[:, 2]
    inner = F(0.21) - P[:, 0] * F(sx)
    if lame == 0:
        return np.maximum(np.maximum(d - F(0.25), F(c[2] - 0.07) - z), inner)
    return np.maximum(np.maximum(d - F(0.27), np.maximum(F(c[2] - 0.17) - z, z - F(c[2] - 0.03))), inner + F(0.03))


def _bracer_region(P, side):
    sx = -1 if side == "R" else 1
    s, d2 = _arm_coord(P, side)
    near = (d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3))
    return np.where(near, np.abs(s - F(ARM_LEN - 0.145)) - F(0.085), F(1.0))


def guards_field():
    """Two-lame pauldrons over his shoulders (graphite 0, navy edges 8, a violet stripe 6 across the top lame) and forearm
    guards (graphite, navy edges, a violet ring round each)."""
    fd = Field("Guards")
    base = shirt_hull()
    lo, hi = (-1, -0.6, 0.6), (1, 0.6, 1.7)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh = J["shoulder_" + side]
        c = sh + v3((sx * 0.035, 0.0, 0.03))
        fd.add(Inter(Shell(base, PC_IN + 0.02, 0.022, pad=0.14), Func(lambda P, s=side: _pauldron_region(P, s, 1), lo, hi), 0.01), 0.004, BASE_L)
        fd.add(Inter(Shell(base, PC_IN + 0.04, 0.024, pad=0.14), Func(lambda P, s=side: _pauldron_region(P, s, 0), lo, hi), 0.012), 0.004, BASE_L)
        def edge(P, s=side):
            return np.maximum(-(_pauldron_region(P, s, 0) + F(0.014)), _pauldron_region(P, s, 0))
        fd.paint(Func(edge, lo, hi), ALT_L)
        def edge1(P, s=side):
            return np.maximum(-(_pauldron_region(P, s, 1) + F(0.012)), _pauldron_region(P, s, 1))
        fd.paint(Func(edge1, lo, hi), ALT_L)
        def stripe(P, c=c, sx=sx):
            # a band over the top lame, across the shoulder (front to back)
            return np.maximum(np.abs(P[:, 0] - F(c[0] + sx * 0.02)) - F(0.011), F(c[2] + 0.02) - P[:, 2])
        fd.paint(Func(stripe, lo, hi), VIO_L)
        # the forearm guard
        def bout(P, s=side):
            return _bracer_region(P, s)
        fd.add(Inter(Shell(base, SHIRT_FACE + SHIRT_T / 2 + 0.014, 0.02, pad=0.14), Func(bout, lo, hi), 0.008), 0.004, BASE_L)
        def bedge(P, s=side):
            r = _bracer_region(P, s)
            return np.maximum(-(r + F(0.012)), r)
        fd.paint(Func(bedge, lo, hi), ALT_L)
        def ring(P, s=side, sx=sx):
            ss, d2 = _arm_coord(P, s)
            near = (d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3))
            return np.where(near, np.abs(ss - F(ARM_LEN - 0.17)) - F(0.008), F(1.0))
        fd.paint(Func(ring, lo, hi), VIO_L)
    return fd


# ======================================================================================= trousers, belt, boots, gloves
def trousers_field():
    """Navy techwear (0): straight in the leg, bloused over the boots' tops; graphite (8) thigh plates and knee guards with
    black straps (5); the black belt (5) with its gunmetal buckle (9)."""
    fd = Field("Trousers")
    hull = legs_hull()
    lo, hi = v3((-0.5, -0.4, 0.2)), v3((0.5, 0.45, 1.1))
    def off(P):
        z = P[:, 2]
        return F(0.014) + F(0.012) * smoothstep(0.42, 0.56, z) + F(0.012) * smoothstep(0.42, 0.34, z)
    def fn(P):
        d = hull.eval(P, margin=0.1)
        return np.abs(d - off(P)) - F(0.01)
    folds = lambda P: (F(0.003) * np.sin(np.arctan2(P[:, 1] - F(0.03), np.abs(P[:, 0]) - F(0.17)) * F(6) + P[:, 2] * F(26)
                                         + F(0.8) * NOISE(P * F(4))) * smoothstep(0.38, 0.5, P[:, 2]) + F(0.001) * NOISE(P * F(25)))
    fd.add(Inter(Func(fn, lo, hi, disp=folds, disp_amp=0.005),
                 Func(lambda P: np.maximum(P[:, 2] - F(TROUSER_TOP), F(TROUSER_BOT) - P[:, 2]), lo, hi), 0.004), 0.0)
    outer = Func(lambda P: hull.eval(P, margin=0.1) - off(P) - F(0.01), lo, hi)
    # thigh plates on the outer thighs
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        hip, kn = J["hip_" + side], J["knee_" + side]
        c0 = lerp(hip, kn, 0.45)
        d = norm(v3((sx, -0.45, 0.0)))
        h, ok = ray_hit(outer, [c0 + d * 0.4], [-d], tmax=0.5)
        if not ok[0]:
            continue
        p = h[0]
        n = _fgrad(outer.fn, p)
        up = norm(hip - kn)
        up = norm(up - n * float(up @ n))
        R = np.stack([np.cross(up, n), up, n], axis=1)
        fd.add(Inter(Ellipsoid(p - n * 0.1, (0.085, 0.125, 0.116), R=R), Plane(p - n * 0.004, -n), 0.008), 0.008, ALT_L)
        for k in (-1, 1):
            fd.add(RoundBox(p + n * 0.012 + up * (k * 0.075), (0.07, 0.01, 0.006), 0.004, R=R), 0.003, BLACK_L)
    # knee guards
    for side in ("R", "L"):
        kn = J["knee_" + side]
        d = v3((0.0, -1.0, 0.05))
        h, ok = ray_hit(outer, [kn + d * 0.4], [-d], tmax=0.5)
        if not ok[0]:
            continue
        p = h[0]
        n = _fgrad(outer.fn, p)
        R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
        fd.add(Inter(Ellipsoid(p - n * 0.07, (0.075, 0.095, 0.095), R=R), Plane(p - n * 0.004, -n), 0.008), 0.008, ALT_L)
        fd.add(Inter(Ellipsoid(p - n * 0.07 + v3((0, 0, -0.035)), (0.06, 0.06, 0.088), R=R), Plane(p + n * 0.006, -n), 0.006), 0.006, ALT_L)
        for zk in (kn[2] + 0.08, kn[2] - 0.075):
            def strap(P, zk=zk, kn=kn):
                rho = np.sqrt((P[:, 0] - F(kn[0])) ** 2 + (P[:, 1] - F(kn[1])) ** 2)
                return np.maximum(np.abs(P[:, 2] - F(zk)) - F(0.011), rho - F(0.16))
            fd.add(Inter(Func(lambda P: np.abs(hull.eval(P, margin=0.1) - off(P) - F(0.013)) - F(0.004), lo, hi),
                         Func(strap, lo, hi), 0.002), 0.004, BLACK_L)
    # the belt and its buckle
    bh = Field("BeltHull")
    tb = shirt_hull()
    bh.add(Func(lambda P: tb.eval(P, margin=0.12) - F(SHIRT_FACE), (-0.5, -0.45, 0.8), (0.5, 0.45, 1.05)), 0.0)
    fd.add(Inter(Shell(bh, 0.012, 0.014, pad=0.06), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(0.026), (-0.6, -0.5, 0.8), (0.6, 0.5, 1.1)), 0.004), 0.004, BLACK_L)
    h, ok = ray_hit(bh, [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    c = h[0] if ok[0] else v3((0, -0.3, BELT_Z))
    R = rot_from_axes(z_axis=(0, -1, 0), y_axis=(0, 0, 1))
    fd.add(RoundBox(c + v3((0, -0.022, 0)), (0.04, 0.028, 0.009), 0.006, R=R), 0.003, GUN_L)
    fd.add(RoundBox(c + v3((0, -0.031, 0)), (0.026, 0.006, 0.003), 0.002, R=R), 0.002, VIO_L)
    return fd


def boots_field():
    """Black boots (0) to above the ankle, thick soles and a toe cap (5: graphite)."""
    fd = Field("Boots")
    crease = lambda P: F(0.0012) * NOISE(P * F(26))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an, kn = J["ankle_" + side], J["knee_" + side]
        ft = boot_hull(side)
        top = lambda P, kn=kn: P[:, 2] - (F(0.4) + F(0.02) * np.clip(-(P[:, 1] - F(kn[1])) / F(0.09), -1, 1))
        fd.add(Inter(Shell(ft, 0.018, 0.015, pad=0.07, disp=crease, disp_amp=0.002),
                     Func(top, an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.6))), 0.004), 0.0)
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.096)), (0.088, 0.172, 0.022), 0.012, R=Rz), 0.006, 5)
        fd.add(RoundBox(an + fwd * -0.035 + v3((0, 0, -0.082)), (0.066, 0.056, 0.032), 0.012, R=Rz), 0.008, 5)
        fd.add(Inter(Ellipsoid(an + fwd * 0.19 + v3((0, 0, -0.06)), (0.075, 0.07, 0.05), R=Rz), Plane(an + v3((0, 0, -0.09)), (0, 0, -1)), 0.004), 0.008, 5)
        for k in range(3):                                                            # straps over the instep
            c = an + fwd * (0.07 - 0.005 * k) + v3((0, 0, -0.03 + 0.05 * k))
            fd.add(RoundBox(c, (0.07, 0.012, 0.016), 0.006, R=Rz @ euler(0.5, 0, 0)), 0.004, 5)
    return fd


def gloves_field():
    """Black gloves (0): over the hands, a short cuff at the wrist, graphite knuckle plates (5)."""
    fd = Field("Gloves")
    crease = lambda P: F(0.0012) * NOISE(P * F(30))
    for side in ("R", "L"):
        hh = _hand_hull(side)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        fd.add(Shell(hh, 0.004, 0.006, pad=0.04, disp=crease, disp_amp=0.001), 0.0)
        fd.add(Inter(Shell(RoundCone(wr - ax * 0.06, wr + ax * 0.02, 0.07, 0.064), 0.0, 0.01, pad=0.04),
                     Func(lambda P, wr=wr, ax=ax: np.abs((P - (wr - ax * 0.025).astype(F)) @ ax.astype(F)) - F(0.03), wr - 0.25, wr + 0.25), 0.003), 0.004)
        w, f, n, t = hand_frame(side)
        fd.add(RoundBox(w + f * 0.142 * HAND_S - n * 0.022, (0.06, 0.012, 0.016), 0.007, R=np.stack([t, -n, f], 1)), 0.006, 5)
        fd.add(RoundBox(w + f * 0.07 * HAND_S - n * 0.03, (0.042, 0.01, 0.03), 0.008, R=np.stack([t, -n, f], 1)), 0.006, 5)
    return fd


# ======================================================================================= the turret (layout)
MY = -0.87                       # the pedestal's axis (x = 0, y = MY): the yoke traverses about it
TRUN = v3((0.0, MY, 1.08))       # the trunnions (the gun elevates about them)
GD = v3((0.0, -1.0, 0.0))        # (rest) along the gun, toward the lens
GU = v3((0.0, 0.0, 1.0))
GX_ = v3((1.0, 0.0, 0.0))
HB = (-0.30, 0.16)               # the housing's back and front (s along the gun from the trunnions)
HW, HV = 0.15, (-0.11, 0.13)     # its half width, its bottom and top (v)
BAR_S = (0.22, 0.6)             # the barrel
COIL_S = (0.265, 0.36)          # the coil's windings
FIN_S = [0.405 + 0.025 * k for k in range(7)]     # the cooling fins
SHROUD_S = (0.565, 0.71)         # the emitter's cup
LENS_S = 0.675                   # the lens's centre (it bulges out of the cup)
LENS_R = 0.116
GRIP_S, GRIP_U = -0.43, 0.22     # the twin grips (s, +-u)
GRIP_V = (-0.12, 0.02)           # their bottom and top
CELL_C = (-0.205, -0.218, 0.03)  # the power cell's middle (s, u, v): on the gun's right side
CELL_R, CELL_HL = 0.054, 0.092
VENT_S = (-0.04, 0.12)           # the vent hatch (s), on the housing's top
VENT_W = 0.088
HINGE_S = VENT_S[1] + 0.006      # its hinge, along its front edge
YOKE_X = 0.205                   # the fork's arms (+-x)
TT_Z = 0.79                      # the turntable's top
FOOT_HALF = 0.24


def gpt(s, u=0.0, v=0.0):
    """A point in the gun's frame (rest): s along it from the trunnions, u across (+X), v up."""
    return TRUN + GD * s + GX_ * u + GU * v


def _rgun():
    return np.stack([GX_, GD, GU], axis=1)


def g_local(P):
    q = (P - TRUN.astype(F)) @ _rgun().astype(F)
    return q[:, 0], q[:, 1], q[:, 2]


def gun_bounds(s0, s1, r=0.3):
    pts = [gpt(s, u, v) for s in (s0, s1) for u in (-r, r) for v in (-r, r)]
    return np.min(pts, 0), np.max(pts, 0)


def hinge_pt():
    return gpt(HINGE_S, 0.0, HV[1] + 0.008)


def lens_c():
    return gpt(LENS_S)


def coil_c():
    return gpt(0.5 * (COIL_S[0] + COIL_S[1]))


def grip_pt(sx, t=0.5):
    """A point on grip sx's axis (t 0 = its bottom, 1 = its top)."""
    return gpt(GRIP_S, sx * GRIP_U, GRIP_V[0] + (GRIP_V[1] - GRIP_V[0]) * t)


def cell_pt(ds=0.0, du=0.0, dv=0.0):
    return gpt(CELL_C[0] + ds, CELL_C[1] + du, CELL_C[2] + dv)


# ======================================================================================= the gun
def _housing_sd(P):
    u, s, v = g_local(P)
    # a rounded box whose width and height ease in toward the front
    k = np.clip((s - F(-0.05)) / F(HB[1] + 0.05), 0, 1)
    w = F(HW) - F(0.03) * k * k
    vt = F(HV[1]) - F(0.02) * k * k
    vb = F(HV[0]) + F(0.03) * k * k
    vc, vh = (vt + vb) * F(0.5), (vt - vb) * F(0.5)
    r = F(0.05)
    qx = np.abs(u) - w + r
    qy = np.abs(s - F((HB[0] + HB[1]) / 2)) - F((HB[1] - HB[0]) / 2) + r
    qz = np.abs(v - vc) - vh + r
    qq = np.stack([qx, qy, qz], 1)
    return np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0) - r


def gun_field():
    """The gun: the gloss-black housing (0) with gunmetal side panels (9) and black panel lines (5); the twin grips (black
    rubber 12 on gunmetal arms) and the violet thumb bar (6) between them; the sight block (graphite 8, smoked lenses 11);
    the charge readout's frame on the back face; the trunnion hubs; the vent's recess with its louvres (black); the power
    cell (black 5, gunmetal caps, a graphite cradle) and its cables (12); the barrel (gunmetal), the coil's cage (gunmetal
    collars, steel tie rods 10), six cooling fins (gunmetal, steel edges), the emitter cup (gloss black, a gunmetal rim);
    white stencils (7)."""
    fd = Field("Gun")
    R = _rgun()
    lo, hi = gun_bounds(HB[0] - 0.2, SHROUD_S[1] + 0.05)
    fd.add(Func(_housing_sd, *gun_bounds(HB[0] - 0.05, HB[1] + 0.05, 0.2)), 0.0, BASE_L)
    fd.add(capped_cone(gpt(0.08, 0, 0.005), gpt(0.245, 0, 0.0), 0.11, 0.072, rr=0.02), 0.05, BASE_L)   # the nose taper
    # gunmetal side panels, inset by a groove
    for su in (-1, 1):
        c = gpt(-0.08, su * (HW - 0.004), -0.01)
        Rp = np.stack([GD, GU, GX_ * su], axis=1)
        fd.add(RoundBox(c, (0.16, 0.06, 0.008), 0.02, R=Rp), 0.004, GUN_L)
        fd.paint(RoundBox(c, (0.17, 0.07, 0.03), 0.024, R=Rp), BLACK_L)
        fd.paint(RoundBox(c, (0.162, 0.062, 0.04), 0.02, R=Rp), GUN_L)
        stencil(fd, "LZR-7", gpt(-0.13, su * (HW + 0.004), -0.01), GD * (-su), GU, 0.026, WHITE_L, depth=0.01)
        for k in range(3):
            fd.add(Sphere(gpt(0.06 - 0.12 * k, su * (HW + 0.003), 0.045), 0.006), 0.001, STEEL_L)
    # panel lines round the housing
    for s0 in (HB[0] + 0.045, 0.1):
        def pl(P, s0=s0):
            u, s, v = g_local(P)
            return np.maximum(np.abs(s - F(s0)) - F(0.0028), -_housing_sd(P) - F(0.01))
        fd.sub(Func(pl, *gun_bounds(s0 - 0.05, s0 + 0.05, 0.2)), 0.001)
    # the vent's recess (the hatch closes over it) and its louvres
    vc = gpt(0.5 * (VENT_S[0] + VENT_S[1]), 0.0, HV[1])
    fd.sub(RoundBox(vc, (VENT_W - 0.006, 0.5 * (VENT_S[1] - VENT_S[0]) - 0.006, 0.026), 0.008, R=R), 0.004)
    for k in range(5):
        fd.add(RoundBox(gpt(VENT_S[0] + 0.02 + 0.03 * k, 0.0, HV[1] - 0.03), (VENT_W - 0.01, 0.004, 0.012), 0.002,
                        R=R @ euler(0.6, 0, 0)), 0.002, BLACK_L)
    # the sight block on top, behind the vent
    sc = gpt(-0.2, 0.0, HV[1] + 0.03)
    fd.add(RoundBox(sc, (0.036, 0.06, 0.03), 0.012, R=R), 0.006, ALT_L)
    fd.add(RoundBox(sc - GU * 0.03, (0.02, 0.04, 0.008), 0.004, R=R), 0.006, ALT_L)
    for ss in (-1, 1):
        fd.add(Cylinder(sc + GD * (ss * 0.06), 0.018, 0.008, rr=0.003, R=rot_from_axes(z_axis=GD)), 0.002, GLASS_L)
    fd.add(Sphere(sc + GU * 0.03 + GX_ * 0.018 - GD * 0.03, 0.006), 0.001, VIO_L)
    # the charge readout's frame on the back face (its bars glow: Trim)
    rc = gpt(HB[0], 0.0, 0.03)
    fd.sub(RoundBox(rc, (0.07, 0.008, 0.032), 0.006, R=R), 0.003)
    # the trunnion hubs
    for su in (-1, 1):
        fd.add(Cylinder(TRUN + GX_ * (su * (HW + 0.012)), 0.052, 0.03, rr=0.008, R=rot_from_axes(z_axis=GX_)), 0.006, GUN_L)
    # the twin grips: gunmetal arms out of the housing's back corners, black rubber handles, the violet thumb bar
    for su in (-1, 1):
        a = gpt(HB[0] + 0.05, su * (HW - 0.02), -0.03)
        b = gpt(HB[0] - 0.05, su * (GRIP_U - 0.015), -0.04)
        c = grip_pt(su, 0.0) + GD * 0.0 - GU * 0.012
        fd.add(Chain([a, b, gpt(GRIP_S + 0.015, su * GRIP_U, -0.04)], [0.02, 0.018, 0.018], k=0.01), 0.008, GUN_L)
        fd.add(RoundCone(grip_pt(su, 0.0), grip_pt(su, 1.0), 0.021, 0.021), 0.006, RUBBER_L)
        for t in (0.2, 0.4, 0.6, 0.8):                                               # finger ridges
            fd.add(Torus(grip_pt(su, t) + GD * 0.004, 0.02, 0.004, R=rot_from_axes(z_axis=GU)), 0.003, RUBBER_L)
        fd.add(Cylinder(grip_pt(su, 0.0) - GU * 0.008, 0.026, 0.016, rr=0.006, R=rot_from_axes(z_axis=GU)), 0.003, GUN_L)
        fd.add(Cylinder(grip_pt(su, 1.0) + GU * 0.01, 0.024, 0.016, rr=0.006, R=rot_from_axes(z_axis=GU)), 0.003, GUN_L)
    bar = [grip_pt(-1, 1.0) + GU * 0.01 - GD * 0.012 + GX_ * 0.03, gpt(GRIP_S - 0.01, -0.08, GRIP_V[1] + 0.02),
           gpt(GRIP_S - 0.01, 0.08, GRIP_V[1] + 0.02), grip_pt(1, 1.0) + GU * 0.01 - GD * 0.012 - GX_ * 0.03]
    fd.add(Chain(bar, [0.009] * 4, k=0.004), 0.003, VIO_L)
    # the power cell: on the right side (-X) in a graphite cradle, gunmetal caps, cables into the housing's back
    A = GD
    cc = cell_pt()
    fd.add(capped_cone(cc - A * CELL_HL, cc + A * CELL_HL, CELL_R, CELL_R, rr=0.012), 0.0, BLACK_L)
    for ss in (-1, 1):
        fd.add(Cylinder(cc + A * (ss * (CELL_HL - 0.004)), CELL_R + 0.006, 0.026, rr=0.008, R=rot_from_axes(z_axis=A)), 0.004, GUN_L)
        fd.add(Torus(cc + A * (ss * 0.045), CELL_R + 0.004, 0.008, R=rot_from_axes(z_axis=A)), 0.003, ALT_L)
        fd.add(RoundBox(cell_pt(ss * 0.045, 0.045, 0.0), (0.03, 0.012, 0.022), 0.006, R=R), 0.004, ALT_L)   # cradle arms
    fd.sub(RoundBox(cell_pt(0.0, -CELL_R, 0.0), (0.004, 0.058, 0.012), 0.004, R=R), 0.002)           # the window's slot
    for k, dv in enumerate((0.022, -0.018)):
        p0 = cc - A * (CELL_HL + 0.012) + GU * dv
        p3 = gpt(HB[0] + 0.004, -0.07 - 0.03 * k, dv - 0.03)
        fd.add(Chain([p0, p0 - A * 0.035, p3 - A * 0.03 + GX_ * -0.02, p3], [0.009] * 4, k=0.012), 0.004, RUBBER_L)
    # the barrel, the coil's cage, the fins
    fd.add(Cylinder(gpt(0.5 * (BAR_S[0] + BAR_S[1])), 0.07, BAR_S[1] - BAR_S[0], rr=0.008, R=rot_from_axes(z_axis=GD)), 0.01, GUN_L)
    for s0 in (COIL_S[0] - 0.02, COIL_S[1] + 0.02):
        fd.add(Cylinder(gpt(s0), 0.11, 0.018, rr=0.005, R=rot_from_axes(z_axis=GD)), 0.004, GUN_L)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = GX_ * math.cos(a) + GU * math.sin(a)
        fd.add(RoundCone(gpt(COIL_S[0] - 0.02) + d * 0.101, gpt(COIL_S[1] + 0.02) + d * 0.101, 0.007, 0.007), 0.003, STEEL_L)
    fd.add(Cylinder(gpt(0.5 * (COIL_S[0] + COIL_S[1])), 0.074, COIL_S[1] - COIL_S[0], rr=0.004, R=rot_from_axes(z_axis=GD)), 0.004, BLACK_L)
    for s0 in FIN_S:
        fd.add(Cylinder(gpt(s0), 0.132, 0.012, rr=0.004, R=rot_from_axes(z_axis=GD)), 0.003, GUN_L)
        fd.paint(Inter(Torus(gpt(s0), 0.132, 0.013, R=rot_from_axes(z_axis=GD)), Plane(gpt(s0), GU * -1.0)), STEEL_L)
    # the emitter cup: flared, gloss black, its mouth rimmed in gunmetal, hollow round the lens
    fd.add(capped_cone(gpt(SHROUD_S[0]), gpt(SHROUD_S[1]), 0.095, 0.15, rr=0.016), 0.012, BASE_L)
    fd.sub(Cylinder(gpt(SHROUD_S[1] + 0.02), LENS_R + 0.006, 0.12, rr=0.004, R=rot_from_axes(z_axis=GD)), 0.006)
    fd.add(Torus(gpt(SHROUD_S[1] - 0.006), 0.138, 0.013, R=rot_from_axes(z_axis=GD)), 0.005, GUN_L)
    for k in range(3):                                                                 # three emitter prongs inside the rim
        a = math.pi / 2 + k * 2 * math.pi / 3
        d = GX_ * math.cos(a) + GU * math.sin(a)
        fd.add(RoundCone(gpt(SHROUD_S[1] - 0.05) + d * 0.126, gpt(SHROUD_S[1] + 0.014) + d * 0.114, 0.01, 0.007), 0.004, STEEL_L)
    return fd


def vent_field():
    """The vent hatch (rest: closed over its recess on the housing's top): a graphite (8) plate with louvre ridges (5),
    its hinge knuckle along its front edge (gunmetal 9), a grip lip at its back."""
    fd = Field("Vent")
    R = _rgun()
    c = gpt(0.5 * (VENT_S[0] + VENT_S[1]), 0.0, HV[1] + 0.004)
    hl = 0.5 * (VENT_S[1] - VENT_S[0])
    fd.add(RoundBox(c, (VENT_W, hl, 0.008), 0.006, R=R), 0.0, ALT_L)
    for k in range(4):
        fd.add(RoundBox(gpt(VENT_S[0] + 0.032 + 0.032 * k, 0.0, HV[1] + 0.012), (VENT_W - 0.016, 0.006, 0.005), 0.003, R=R), 0.003, BLACK_L)
    fd.add(Cylinder(hinge_pt(), 0.009, 2 * VENT_W - 0.02, rr=0.003, R=rot_from_axes(z_axis=GX_)), 0.003, GUN_L)
    fd.add(RoundBox(gpt(VENT_S[0] - 0.002, 0.0, HV[1] + 0.012), (0.03, 0.006, 0.006), 0.003, R=R), 0.003, GUN_L)
    return fd


def lens_field():
    """The emitter lens (shipped glowing violet): a big domed disc bulging out of the cup."""
    fd = Field("Lens")
    fd.add(Ellipsoid(lens_c(), (LENS_R, LENS_R, 0.05), R=rot_from_axes(z_axis=GD)), 0.0)
    return fd


def coil_field():
    """The capacitor coil's windings (shipped glowing violet): five rings round the barrel inside the cage."""
    fd = Field("Coil")
    n = 5
    for k in range(n):
        s0 = COIL_S[0] + (COIL_S[1] - COIL_S[0]) * k / (n - 1)
        fd.add(Torus(gpt(s0), 0.086, 0.012, R=rot_from_axes(z_axis=GD)), 0.004)
    return fd


def trim_field():
    """The gun's other violet lights (shipped glowing): a strip along each side panel, the cell's charge window, the charge
    readout's bars on the back face, a bar in the vent's recess (seen when it opens)."""
    fd = Field("Trim")
    R = _rgun()
    for su in (-1, 1):
        fd.add(RoundCone(gpt(-0.22, su * (HW + 0.002), 0.058), gpt(0.06, su * (HW + 0.002), 0.058), 0.0065, 0.0065), 0.0)
    fd.add(RoundBox(cell_pt(0.0, -CELL_R + 0.003, 0.0), (0.004, 0.052, 0.008), 0.003, R=R), 0.0)
    for k in range(4):
        fd.add(RoundBox(gpt(HB[0] + 0.002, -0.045 + 0.03 * k, 0.03), (0.011, 0.004, 0.022 - 0.004 * abs(k - 1.5)), 0.002, R=R), 0.0)
    fd.add(RoundBox(gpt(0.5 * (VENT_S[0] + VENT_S[1]), 0.0, HV[1] - 0.022), (VENT_W - 0.02, 0.05, 0.004), 0.003, R=R), 0.0)
    return fd


# ======================================================================================= the pedestal and the yoke
def mount_field():
    """The pedestal: a graphite (8) foot plate, its bolts (9) and hazard-yellow corner chevrons (13); a junction box on it
    (graphite, a violet light 6) with cables (12) over the plate's edge into the floor; a gunmetal (9) column with a flange
    and a collar, a black cable up its back."""
    fd = Field("Mount")
    c0 = v3((0.0, MY, 0.0))
    fd.add(RoundBox(c0 + v3((0, 0, 0.025)), (FOOT_HALF, FOOT_HALF, 0.025), 0.014), 0.0, ALT_L)
    fd.add(RoundBox(c0 + v3((0, 0, 0.06)), (0.15, 0.15, 0.02), 0.012), 0.006, ALT_L)
    for sx in (-1, 1):
        for sy in (-1, 1):
            j = c0 + v3((sx * (FOOT_HALF - 0.04), sy * (FOOT_HALF - 0.04), 0.052))
            fd.add(Cylinder(j, 0.013, 0.008, rr=0.003), 0.002, GUN_L)
            def chev(P, sx=sx, sy=sy):
                q = P - c0.astype(F)
                along = (q[:, 0] * F(sx) + q[:, 1] * F(sy)) / F(1.414)
                across = (q[:, 0] * F(sx) - q[:, 1] * F(sy)) / F(1.414)
                return np.maximum(np.maximum(np.abs(along - F(0.25)) - F(0.016), np.abs(across) - F(0.05)), np.abs(q[:, 2] - F(0.05)) - F(0.012))
            fd.paint(Func(chev, c0 - 0.3, c0 + 0.3), HAZ_L)
    fd.add(Cylinder(c0 + v3((0, 0, 0.09)), 0.12, 0.03, rr=0.008), 0.006, GUN_L)                    # the flange
    fd.add(Cylinder(c0 + v3((0, 0, 0.42)), 0.075, 0.66, rr=0.01), 0.01, GUN_L)                      # the column
    fd.add(Cylinder(c0 + v3((0, 0, 0.72)), 0.1, 0.05, rr=0.01), 0.008, GUN_L)                       # its collar
    for z in (0.3, 0.52):
        fd.add(Torus(c0 + v3((0, 0, z)), 0.075, 0.008), 0.003, ALT_L)
    # the junction box at the column's back and its cables
    jb = c0 + v3((0.0, 0.17, 0.11))
    fd.add(RoundBox(jb, (0.07, 0.045, 0.05), 0.012), 0.006, ALT_L)
    fd.add(Sphere(jb + v3((0.04, 0.045, 0.02)), 0.008), 0.001, VIO_L)
    fd.add(Chain([jb + v3((0, -0.03, 0.04)), c0 + v3((0, 0.09, 0.2)), c0 + v3((0, 0.082, 0.62)), c0 + v3((0, 0.06, 0.7))],
                 [0.014] * 4, k=0.02), 0.004, RUBBER_L)
    for sx in (-1, 1):
        a = jb + v3((sx * 0.04, 0.04, -0.02))
        fd.add(Chain([a, a + v3((sx * 0.02, 0.06, -0.02)), c0 + v3((sx * 0.07, FOOT_HALF + 0.03, 0.035)),
                      c0 + v3((sx * 0.08, FOOT_HALF + 0.08, 0.006))], [0.013] * 4, k=0.02), 0.004, RUBBER_L)
    return fd


YOKE = [(-0.12, 0.8), (0.12, 0.8), (0.085, 0.98), (0.07, 1.13), (-0.07, 1.13), (-0.085, 0.98)]   # an arm's side profile (y from MY, z)


def yoke_field():
    """The turntable (graphite 8, a gunmetal ring 9) and the fork: two graphite arms up to the trunnions with gunmetal
    bearing caps and bolts; a black cable from the column into the gun's belly behind the trunnions."""
    fd = Field("Yoke")
    c0 = v3((0.0, MY, TT_Z))
    fd.add(Cylinder(c0 - v3((0, 0, 0.025)), 0.16, 0.05, rr=0.014), 0.0, ALT_L)
    fd.add(Torus(c0 - v3((0, 0, 0.024)), 0.16, 0.012), 0.004, GUN_L)
    fd.add(RoundBox(c0 + v3((0, 0, 0.012)), (YOKE_X + 0.01, 0.12, 0.02), 0.012), 0.008, ALT_L)
    p2 = poly2d(YOKE)
    for sx in (-1, 1):
        xc = sx * YOKE_X
        def plate(P, xc=xc):
            d2 = p2(P[:, 1] - F(MY), P[:, 2])
            disc = np.sqrt((P[:, 1] - F(TRUN[1])) ** 2 + (P[:, 2] - F(TRUN[2])) ** 2) - F(0.075)
            d2 = np.minimum(d2, disc)
            hole = np.sqrt((P[:, 1] - F(MY)) ** 2 + (P[:, 2] - F(0.93)) ** 2) - F(0.03)
            d2 = np.maximum(d2, -hole)
            dx = np.abs(P[:, 0] - F(xc)) - F(0.016)
            r = F(0.008)
            w0, w1 = d2 + r, dx + r
            return np.minimum(np.maximum(w0, w1), F(0)) + np.sqrt(np.maximum(w0, 0) ** 2 + np.maximum(w1, 0) ** 2) - r
        fd.add(Func(plate, (xc - 0.05, MY - 0.2, 0.7), (xc + 0.05, MY + 0.2, 1.2)), 0.008, ALT_L)
        fd.add(Cylinder(TRUN + GX_ * (sx * (YOKE_X + 0.02)), 0.06, 0.03, rr=0.008, R=rot_from_axes(z_axis=GX_)), 0.004, GUN_L)
        for k in range(6):
            a = 2 * math.pi * k / 6
            fd.add(Sphere(TRUN + GX_ * (sx * (YOKE_X + 0.036)) + v3((0, math.cos(a) * 0.042, math.sin(a) * 0.042)), 0.007), 0.001, STEEL_L)
        fd.add(Sphere(TRUN + GX_ * (sx * (YOKE_X + 0.04)), 0.012), 0.002, VIO_L)
    # the cable up into the gun's belly
    pts = [c0 + v3((0.05, 0.06, 0.02)), c0 + v3((0.06, 0.04, 0.12)), gpt(-0.05, 0.05, HV[0] - 0.05), gpt(-0.05, 0.05, HV[0] + 0.01)]
    fd.add(Chain(pts, [0.013] * 4, k=0.015), 0.004, RUBBER_L)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.614)), 0.045, 0.45)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.104, -0.14, 1.636)), 0.05, 0.35), (hp((sx * 0.05, -0.18, 1.77)), 0.06, 0.2)]
    return pts


# ======================================================================================= build config
GLB_NAME = "laser_turret"
ROOT_NAME = "LaserTurretHQ"
TEX_PREFIX = "laser_turret"
MAT_NAME = "LaserTurretMat"
MESH_NAME = "LaserTurret"
BASE_MODULE = "laser_base"
ANIM_MODULE = "anim_laser"
PARTS = ["Skin", "Eyes", "Hair", "Helmet", "Crest", "Comms", "Suit", "Armour", "Strips", "Guards", "Trousers", "Boots",
         "Gloves", "Mount", "Yoke", "Gun", "Vent", "Lens", "Coil", "Trim"]
REGION_PARTS = ("Skin", "Helmet", "Comms", "Suit", "Armour", "Guards", "Trousers", "Boots", "Gloves", "Mount", "Yoke", "Gun",
                "Vent")
KIT = dict(weave=0.0, black=BLACK, red=VIOLET, white=WHITE, gunmetal=GUNMETAL, glass=SMOKE, glass_hi=(0.55, 0.4, 0.7),
           rubber=(0.07, 0.07, 0.075), coyote=HAZARD)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_LzrSkin", "base": (0.8, 0.6, 0.47), "ruddy": (0.8, 0.5, 0.4), "lips": (0.66, 0.42, 0.36),
                      "brow": ((0.05, 0.035, 0.03), (0.12, 0.08, 0.06)),
                      "extra": ((LASH, (0.04, 0.03, 0.025), 0.5), (STUBBLE, (0.36, 0.26, 0.2), 0.62, 0.5))}),
    "Hair": ("hair", {"name": "HQ_LzrHair", "base": (0.05, 0.04, 0.035), "hi": (0.18, 0.14, 0.11), "low": (0.025, 0.02, 0.018),
                      "streak": (0.035, 0.03, 0.025), "tint": (0.08, 0.06, 0.05)}),
    "Helmet": ("modern_kit", dict(KIT, name="HQ_LzrHelmet", base=GRAPHITE, olive=NAVY, gloss=0.5)),
    "Comms": ("modern_kit", dict(KIT, name="HQ_LzrHelmet", base=GRAPHITE, olive=NAVY, gloss=0.5)),
    "Suit": ("modern_kit", dict(KIT, name="HQ_LzrSuit", base=(0.075, 0.075, 0.085), weave=1.0, black=(0.035, 0.035, 0.04))),
    "Armour": ("modern_kit", dict(KIT, name="HQ_LzrArmour", base=GRAPHITE, olive=NAVY, gloss=0.5)),
    "Guards": ("modern_kit", dict(KIT, name="HQ_LzrArmour", base=GRAPHITE, olive=NAVY, gloss=0.5)),
    "Trousers": ("modern_kit", dict(KIT, name="HQ_LzrTrousers", base=NAVY, weave=1.0, olive=GRAPHITE)),
    "Boots": ("leather_dyed", {"name": "HQ_LzrBoots", "base": (0.07, 0.068, 0.075), "dyed": (0.14, 0.15, 0.17), "worn_c": (0.3, 0.3, 0.33)}),
    "Gloves": ("leather_dyed", {"name": "HQ_LzrGloves", "base": (0.075, 0.075, 0.082), "dyed": GRAPHITE, "worn_c": (0.3, 0.3, 0.33)}),
    "Mount": ("modern_kit", dict(KIT, name="HQ_LzrTurret", base=GLOSS, olive=GRAPHITE, gloss=0.22)),
    "Yoke": ("modern_kit", dict(KIT, name="HQ_LzrTurret", base=GLOSS, olive=GRAPHITE, gloss=0.22)),
    "Gun": ("modern_kit", dict(KIT, name="HQ_LzrTurret", base=GLOSS, olive=GRAPHITE, gloss=0.22)),
    "Vent": ("modern_kit", dict(KIT, name="HQ_LzrTurret", base=GLOSS, olive=GRAPHITE, gloss=0.22)),
}
GLOW = {"Lens": ((0.86, 0.38, 1.0), 1.3, 0.5), "Coil": (VIOLET, 1.2, 0.5), "Trim": (VIOLET, 1.0, 0.5),
        "Strips": (VIOLET, 1.0, 0.5), "Crest": (VIOLET, 1.0, 0.5)}
LOW_TARGETS = {"Skin": 4800, "Hair": 350, "Helmet": 1500, "Crest": 90, "Comms": 700, "Suit": 2600, "Armour": 3200,
               "Strips": 140, "Guards": 1100, "Trousers": 2000, "Boots": 1100, "Gloves": 900, "Mount": 1300, "Yoke": 1000,
               "Gun": 3700, "Vent": 260, "Lens": 220, "Coil": 520, "Trim": 300}
AO_EXCLUDE = ["Comms", "Vent"]
MACHINE_PARTS = ["Mount", "Yoke", "Gun", "Vent"]
# the turret is baked 6 m away from him (his rest pose stands close behind its grips)
BAKE_APART = (MACHINE_PARTS, (6.0, 0.0, 0.0))
YAW_PIVOT = (0.0, -0.6, 0.0)                # the tower turns about this point (between him and the pedestal)


def prop_bones():
    return []                                # everything he handles is the turret's (extra_bones)


def extra_bones():
    """The turret's bones (none of them deform him): mount (the pedestal), yoke (the turntable and fork: it traverses
    about the column; child of the mount), gun (elevating about the trunnions; child of the yoke), vent (the hatch, on its
    hinge; child of the gun), coil (the glowing windings: they swell at the shot), lens (child of the gun: its head is the
    lens's centre, the bone points along the beam; the lens flares (scales) at the shot)."""
    L, C, H = lens_c(), coil_c(), hinge_pt()
    return [
        ("mount", v3((0.0, MY, 0.0)), v3((0.0, MY, 0.3)), None),
        ("yoke", v3((0.0, MY, TT_Z)), v3((0.0, MY, TT_Z + 0.2)), "mount"),
        ("gun", TRUN, TRUN + GD * 0.3, "yoke"),
        ("vent", H, H + GX_ * 0.1, "gun"),
        ("coil", C, C + GD * 0.1, "gun"),
        ("lens", L, L + GD * 0.1, "gun"),
    ]


def trousers_weights(ob, skin_ob, arm):
    """The trousers from his hips and legs; the belt with his hips (half root, half spine), not his thighs."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed={"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"})
    groups = {}
    for v in ob.data.vertices:
        p = np.array(v.co)
        if abs(p[2] - BELT_Z) < 0.045 and math.hypot(p[0], p[1] - 0.03) < 0.42:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"root": 0.55, "spine": 0.45})


def weight_rules():
    body = TORSO | {"clavicle.R", "clavicle.L"}
    arms = {"upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
    return {
        "Eyes": ("rigid", "head"), "Hair": ("rigid", "head"), "Helmet": ("rigid", "head"), "Crest": ("rigid", "head"),
        "Comms": ("rigid", "head"),
        "Suit": ("transfer", body | arms, None),
        "Armour": ("transfer", body, None),
        "Strips": ("rigid", "chest"),
        "Guards": ("transfer", body | arms, None),
        "Trousers": ("custom", trousers_weights),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Mount": ("rigid", "mount"), "Yoke": ("rigid", "yoke"), "Gun": ("rigid", "gun"), "Vent": ("rigid", "vent"),
        "Lens": ("rigid", "lens"), "Coil": ("rigid", "coil"), "Trim": ("rigid", "gun"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part == "Skin" and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Helmet", "Comms"):
        return 1.15
    if part in ("Mount", "Yoke"):
        return 0.75
    if part in ("Gun",):
        return 0.95
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Hair", hair_field(), 0.0022 if fine else 0.003),
        ("Helmet", helmet_field(), 0.0022 if fine else 0.0032),
        ("Crest", crest_field(), 0.0012 if fine else 0.0016),
        ("Comms", comms_field(), 0.0018 if fine else 0.0026),
        ("Suit", suit_field(), 0.0026 if fine else 0.0036),
        ("Armour", armour_field(), 0.0026 if fine else 0.0036),
        ("Strips", strips_field(), 0.0012 if fine else 0.0016),
        ("Guards", guards_field(), 0.0024 if fine else 0.0034),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Gloves", gloves_field(), 0.0018 if fine else 0.0026),
        ("Mount", mount_field(), 0.0026 if fine else 0.0036),
        ("Yoke", yoke_field(), 0.0024 if fine else 0.0034),
        ("Gun", gun_field(), 0.0022 if fine else 0.0032),
        ("Vent", vent_field(), 0.0016 if fine else 0.0022),
        ("Lens", lens_field(), 0.002),
        ("Coil", coil_field(), 0.0016 if fine else 0.002),
        ("Trim", trim_field(), 0.0012 if fine else 0.0016),
    ]
