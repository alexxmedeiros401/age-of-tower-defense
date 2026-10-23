"""The Plasma Mortar (HQ tower, Digital Age; Siege lineage): a sleek magnetic plasma mortar of the tech corps and the
artillerist who serves it. Rest pose: he stands in an A-pose facing -Y (the way it shoots), feet at z = 0; the mortar
stands ahead of him on his left (+X), its tube angled up toward -Y; behind him on his left its charging rack of plasma
cells. The mortar is charged: a cell sits in its breech.

Him: the Missile Launcher's sturdy, barrel-chested body (torsion.py, field_gun.py's gripping hands) with his own face:
a fair, ruddy face with a square jaw and a shadow of stubble, round cheeks pushed up by a broad grin (both corners up,
his upper teeth showing, dimples and smile folds), bright blue-grey eyes with crinkles at their corners, brows lifted
high, a straight nose with a broad soft tip; good-humoured and unflappable. A slim graphite helmet (a low crest down its
middle between panel lines, a violet stripe down each side, a black rubber edge), its smoked visor flipped up over his
brow on gunmetal hinges; slim black ear pieces (a violet ring round each), a boom mic on his left, a black chin strap; a
small camera module on the helmet's right side. A matte black under-suit with long sleeves (graphite armour panels on
the upper arms, a violet stripe down each sleeve), a high stand collar; over it a graphite armour vest (front and back
plates with panel lines, a navy cummerbund and shoulder straps, a unit badge, a slim power unit on his back) with violet
light strips inlaid down its front and over its straps (their own emissive mesh, `Strips`); navy trousers with cargo
pockets, graphite knee pads and belt; black boots and gloves.

The mortar (material `modern_kit`): a round base plate and a turntable on a short column, a gunmetal yoke of two side
plates carrying the gimbal ring on trunnions; through the ring the tube: short and fat, its gloss-black breech housing at
the bottom (the cell port in its top), a collar of heat-sink fins, three graphite coil collars ringing it (each with a
glowing violet coil band sunk in a groove) and a flared muzzle with a glowing plasma charge deep in its bore (bands and
charge: one emissive mesh on the `coils` bone, scaled in toward the tube's axis to put them out). A power pack under the
tube's front (a violet window), its cables up into the breech; a firing grip on the near yoke plate. The plasma cell (its
own bone): a black canister with gunmetal caps and three slots showing its glowing core (`CellCore`, on its own bone:
scaled in to go dark). The charging rack: a stand with four sockets, three cells charging in them (cores glowing), the
fourth socket his.

Painted labels (modern_kit): 0 the part's base colour (graphite polymer, cloth), 5 gloss black, 6 violet paint,
7 white (stencils), 8 navy, 9 gunmetal, 10 bright steel, 11 smoked glass, 12 black rubber, 13 hazard yellow."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp, project_to
import missile as mm
from missile import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD,
                     EYE_R, eye_c, smoothstep, hand_frame, HAND_S, fist_center, foot, traps, neck_prim, deltoid,
                     upper_arm, eyes_field, skull, torso_prims, TORSO, TORSO_Z, torso_bones, hand, palm_pt, ARM_LEN,
                     tunic_neck, _arm_coord, layer, _fgrad, capped_cone, poly2d, stencil, JAW, CHIN, cheekbone,
                     jaw_corner, stubble_mask, shirt_hull, SHIRT_OFF, SHIRT_T, SHIRT_FACE, SHIRT_HEM, PC_IN, PLATE_T,
                     PLATE_OFF, CB_T, CB_OFF, STRAP_T, _plate_region, _cb_region, _strap_region, carrier_outer,
                     _surface_frame, trousers_field, boots_field, gloves_field, trousers_weights, face_hull, BELT_Z)

IRIS = ((0.14, 0.24, 0.32), (0.36, 0.5, 0.6))            # bright blue-grey eyes (prep.paint_eyes)
GRAPHITE = (0.16, 0.17, 0.2)
NAVY = (0.12, 0.16, 0.3)
SUIT_BLACK = (0.07, 0.07, 0.08)
HOUSING = (0.19, 0.2, 0.23)                               # the mortar's housings (graphite polymer, a shade lighter)
GUNMETAL = (0.3, 0.31, 0.34)
VIOLET = (0.85, 0.25, 0.95)                               # the corps' glow
VIOLET_P = (0.6, 0.2, 0.74)                               # violet paint (not lit)
HAZARD = (0.92, 0.72, 0.12)
WHITE = (0.9, 0.9, 0.92)
BASE_L, BLACK_L, VIO_L, WHITE_L, NAVY_L, GM_L, STEEL_L, GLASS_L, RUBBER_L, HAZ_L = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13


# ======================================================================================= head: the grin
def _on_face(fd, pts_xz, lift=0.0):
    """Points on the face's surface (as sculpted so far) in front of design points (x, z): rays from the front."""
    org = [hp((x, -0.45, z)) for x, z in pts_xz]
    h, ok = ray_hit(fd, org, [v3((0, 1, 0))] * len(pts_xz), tmax=0.5, step=0.0008)
    out = []
    for i, (x, z) in enumerate(pts_xz):
        q = h[i] if ok[i] else hp((x, -0.19, z))
        out.append(q - v3((0, 1, 0)) * lift)
    return out


MOUTH_W = 0.062                       # half the grin's width (design)


def mouth_curves(x):
    """The open grin (design units): the upper lip's edge and the lower lip's edge at x (both corners drawn up)."""
    x = np.asarray(x, dtype=np.float64)
    up = 1.556 + 5.0 * x * x
    lo = 1.556 - 0.024 + 11.5 * x * x
    return up, lo


def head(fd):
    """A sturdy, good-humoured face: the square jaw and chin (missile.py's), cheekbones over round cheeks pushed up by a
    broad grin (both corners drawn up, the upper teeth showing, smile folds and dimples), bright open eyes (the lower lids
    lifted by the cheeks, crinkles at their corners), brows lifted high and a little arched, a straight nose with a broad
    soft tip, a shadow of stubble. (No ears: the ear pieces cover where they are.)"""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.79), (0.165, 0.175, 0.12)), 0.08, SKIN)
    fd.add(E(*JAW), 0.07, SKIN)
    fd.add(E(*CHIN), 0.05, SKIN)
    fd.add(E((0.0, -0.168, 1.49), (0.046, 0.026, 0.028)), 0.03, SKIN)                     # the chin's square point
    for sx in (-1, 1):
        c, r = cheekbone(sx)
        fd.add(S(c, r), 0.05, SKIN)
        c, r = jaw_corner(sx)
        fd.add(S(c, r), 0.05, SKIN)
        fd.add(S((sx * 0.08, -0.146, 1.606), 0.031), 0.03, SKIN)                              # round cheeks (the grin)
        pts = [hp((sx * 0.154, -0.055, 1.744)), hp((sx * 0.116, -0.133, 1.756)), hp((sx * 0.061, -0.175, 1.754)), hp((0.0, -0.184, 1.75))]
        fd.add(Chain(pts, [hr(0.01), hr(0.017), hr(0.02), hr(0.019)], k=hr(0.022)), hr(0.032), SKIN)   # a soft brow ridge
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # brows lifted high and a little arched (a raised ridge of hair and a painted band)
    for sx in (-1, 1):
        xz = [(sx * 0.024, 1.784), (sx * 0.064, 1.797), (sx * 0.108, 1.799), (sx * 0.15, 1.784)]
        on = _on_face(fd, xz, lift=0.001)
        tuft = lambda P: F(0.0014) * NOISE(P * F(150))
        fd.add(Chain(on, [hr(0.0062), hr(0.0074), hr(0.0066), hr(0.0034)], k=hr(0.006), disp=tuft, disp_amp=0.002), hr(0.004), BROW)
        fd.paint(Chain(on, [hr(0.0132), hr(0.0152), hr(0.0136), hr(0.0074)], k=hr(0.008)), BROW)
    # eyes: open and bright; the upper lids clear of the irises, the lower lids lifted by the cheeks; smile crinkles
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0058)), Plane(ec + v3((0, 0, hr(0.0215))), (sx * 0.16, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0048)), Plane(ec + v3((0, 0, -hr(0.0165))), (sx * -0.3, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.006), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0195))), (sx * 0.16, 0.05, -1.0)), hr(0.002)), LASH)
        for k in range(2):
            a = hp((sx * (0.112 + 0.004 * k), -0.13 + 0.006 * k, 1.682 - 0.013 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, 0.004 - 0.009 * k)), hr(0.0019), hr(0.0012)), hr(0.003))
    # a straight nose, a broad soft tip
    fd.add(RoundCone(hp((0, -0.19, 1.728)), hp((0, -0.243, 1.636)), hr(0.015), hr(0.022)), hr(0.016), SKIN)
    fd.add(S((0, -0.247, 1.617), 0.027), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.031, -0.222, 1.604), 0.02), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.016, -0.238, 1.594)), v3((0.009, 0.011, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the grin: a crescent between the lips' edges, corners up into the cheeks
    xs = np.linspace(-MOUTH_W, MOUTH_W, 9)
    up_z, lo_z = mouth_curves(xs)
    upper = _on_face(fd, [(x, z + 0.004) for x, z in zip(xs, up_z)])
    lower = _on_face(fd, [(x, z - 0.004) for x, z in zip(xs, lo_z)])
    def opening(P):
        Q = hinv(P)
        x, z = Q[:, 0], Q[:, 2]
        u, l = mouth_curves(x)
        dz = np.maximum(z - u.astype(F), l.astype(F) - z)
        dx = np.abs(x) - F(MOUTH_W)
        return np.maximum(np.maximum(dz, dx), -(Q[:, 1] + F(0.21))) * F(HS)
    lo_b, hi_b = hp((-0.09, -0.26, 1.48)), hp((0.09, -0.12, 1.62))
    cav = Inter(Func(opening, lo_b, hi_b), Ellipsoid(hp((0.0, -0.175, 1.55)), v3((0.077, 0.03, 0.05)) * HS), hr(0.002))
    fd.sub(cav, hr(0.004))
    fd.paint(Inter(Func(lambda P: opening(P) - F(0.0025), lo_b, hi_b),
                   Ellipsoid(hp((0.0, -0.175, 1.55)), v3((0.082, 0.04, 0.06)) * HS), hr(0.002)), MOUTH)
    ru = [0.0024, 0.0038, 0.0048, 0.0053, 0.0055, 0.0053, 0.0048, 0.0038, 0.0024]
    rl = [0.0026, 0.0045, 0.006, 0.0068, 0.007, 0.0068, 0.006, 0.0045, 0.0026]
    fd.add(Chain(upper, [hr(r) for r in ru], k=hr(0.005)), hr(0.007), LIP)
    fd.add(Chain(lower, [hr(r) for r in rl], k=hr(0.006)), hr(0.008), LIP)
    for sx in (-1, 1):
        cz = float(mouth_curves(sx * (MOUTH_W + 0.006))[0])
        fd.add(S((sx * 0.084, -0.156, cz + 0.016), 0.012), hr(0.01), SKIN)                 # the grin's cheeks over the corners
        fd.sub(S((sx * (MOUTH_W + 0.017), -0.16, cz + 0.002), 0.0052), hr(0.006))          # dimples
        folds = _on_face(fd, [(sx * 0.048, 1.604), (sx * 0.068, 1.586), (sx * 0.081, 1.562)], lift=-0.002)
        fd.sub(Chain(folds, [hr(0.0022), hr(0.0026), hr(0.002)], k=hr(0.003)), hr(0.004))   # smile folds


def body_parts(fd):
    """The Missile Launcher's body (missile.body_parts) with this head."""
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


def teeth_field():
    """His upper teeth, showing under his upper lip in the grin (following its curve, set back in the mouth)."""
    fd = Field("Teeth")
    xs = np.linspace(-0.046, 0.046, 7)
    up_z, lo_z = mouth_curves(xs)
    pts = [hp((x, -0.178 + 7.0 * x * x, z - 0.0085)) for x, z in zip(xs, up_z)]
    fd.add(Chain(pts, [hr(0.0088)] * len(pts), k=hr(0.004)), 0.0)
    return fd


# ======================================================================================= the helmet
HELMET_OFF, HELMET_T = 0.028, 0.018       # the shell over the skull (slim)
HELMET_FACE = HELMET_OFF + HELMET_T / 2


def _ang(Q):
    """Angle round his head (design coordinates): 0 at the front, pi at the back."""
    return np.abs(np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.02))))


def rim_z(Q):
    """The helmet's lower edge (design z): over the brow (clear of the lifted brows), up over the ear pieces, down to the
    nape."""
    a = _ang(Q)
    return (F(1.835) - F(0.035) * smoothstep(0.55, 1.05, a) - F(0.105) * smoothstep(1.95, 2.6, a)
            + F(0.012) * smoothstep(1.15, 1.45, a) * smoothstep(1.95, 1.65, a))


def _helmet_keep(P):
    Q = hinv(P)
    return (rim_z(Q) - Q[:, 2]) * F(HS)


def helmet_outer():
    sk = skull()
    return Func(lambda P: sk.eval(P, margin=0.1) - F(HELMET_FACE), HEAD_C - 0.4, HEAD_C + 0.4)


def helmet_point(a, zd, out=0.0, side=1):
    """A point on the helmet's outer surface at angle a (0 = front, + toward his left) and design height zd; its normal."""
    ho = helmet_outer()
    c = hp((0.0, 0.02, zd))
    d = v3((math.sin(a), -math.cos(a), 0.0))
    h, ok = ray_hit(ho, [c + d * 0.6], [-d], tmax=0.7, step=0.0015)
    p = h[0]
    n = _fgrad(ho.fn, p)
    return p + n * out, n


VISOR_LO, VISOR_HI = 0.012, 0.074          # the raised visor's band above the rim (design units, at the front)
VISOR_A = 1.2                              # its half span round the helmet (radians)


def _visor_region(P):
    Q = hinv(P)
    a = _ang(Q)
    rz_ = rim_z(Q)
    zlo = rz_ + F(VISOR_LO) + F(0.012) * smoothstep(0.6, 1.2, a)
    zhi = rz_ + F(VISOR_HI) - F(0.018) * smoothstep(0.7, 1.2, a)
    return np.maximum(np.maximum(zlo - Q[:, 2], Q[:, 2] - zhi), a - F(VISOR_A)) * F(HS)


def helmet_field():
    """Graphite polymer (0): the slim shell, a black rubber edge (5), a low crest down its middle between grooved panel
    lines, a violet stripe (6) down each side; the smoked visor (11) flipped up over the brow, its gunmetal (9) rim and
    hinges at the temples; slim black ear pieces with violet rings and gunmetal rims, a black boom mic, a camera module on
    its right side (a smoked lens); the black chin strap."""
    fd = Field("Helmet")
    sk = skull()
    lo, hi = HEAD_C - 0.4, HEAD_C + 0.4
    fd.add(Inter(Shell(sk, HELMET_OFF, HELMET_T, pad=0.08), Func(_helmet_keep, lo, hi), 0.008), 0.0, BASE_L)
    def trim(P):
        Q = hinv(P)
        return (Q[:, 2] - rim_z(Q) - F(0.012)) * F(HS)
    fd.paint(Func(trim, lo, hi), BLACK_L)
    # the crest: a low ridge from the brow over the top to the back, panel-line grooves either side
    def crest(P):
        Q = hinv(P)
        return np.maximum(np.abs(Q[:, 0]) - F(0.026), rim_z(Q) + F(0.045) - Q[:, 2]) * F(HS)
    fd.add(Inter(Shell(sk, HELMET_FACE + 0.004, 0.012, pad=0.08), Func(crest, lo, hi), 0.004), 0.004, BASE_L)
    for sx in (-1, 1):
        def groove(P, sx=sx):
            Q = hinv(P)
            return np.maximum(np.abs(Q[:, 0] - F(sx * 0.052)) - F(0.0026), rim_z(Q) + F(0.03) - Q[:, 2]) * F(HS)
        fd.sub(Inter(Shell(sk, HELMET_FACE + HELMET_T / 2, 0.01, pad=0.08), Func(groove, lo, hi), 0.0), 0.002)
    # the side stripes (violet), from the temple back round to behind the ear piece
    def stripe(P):
        Q = hinv(P)
        a = _ang(Q)
        zc = rim_z(Q) + F(0.04)
        return np.maximum(np.maximum(np.abs(Q[:, 2] - zc) - F(0.0075), F(1.15) - a), a - F(2.35)) * F(HS)
    fd.paint(Func(stripe, lo, hi), VIO_L)
    # a panel line above the stripe
    def pline(P):
        Q = hinv(P)
        a = _ang(Q)
        zc = rim_z(Q) + F(0.064)
        return np.maximum(np.maximum(np.abs(Q[:, 2] - zc) - F(0.0024), F(1.25) - a), a - F(2.5)) * F(HS)
    fd.sub(Inter(Shell(sk, HELMET_FACE + HELMET_T / 2, 0.01, pad=0.08), Func(pline, lo, hi), 0.0), 0.002)
    # the visor, flipped up: a smoked band standing a little off the shell's front, a gunmetal rim along its lower edge
    fd.add(Inter(Shell(sk, HELMET_FACE + HELMET_T / 2 + 0.009, 0.009, pad=0.08), Func(_visor_region, lo, hi), 0.004), 0.003, GLASS_L)
    def vrim(P):
        Q = hinv(P)
        a = _ang(Q)
        zlo = rim_z(Q) + F(VISOR_LO) + F(0.012) * smoothstep(0.6, 1.2, a)
        return np.maximum(np.abs(Q[:, 2] - zlo - F(0.004)) - F(0.0055), a - F(VISOR_A)) * F(HS)
    fd.add(Inter(Shell(sk, HELMET_FACE + HELMET_T / 2 + 0.01, 0.013, pad=0.08), Func(vrim, lo, hi), 0.003), 0.003, GM_L)
    for sx in (-1, 1):
        z0 = float(rim_z(np.array([[sx * 0.2, -0.02, 1.8]], F))[0])
        p, n = helmet_point(sx * 1.3, z0 + 0.032)
        fd.add(Cylinder(p + n * 0.008, 0.022, 0.016, rr=0.005, R=rot_from_axes(z_axis=n)), 0.003, GM_L)
        fd.add(Cylinder(p + n * 0.016, 0.009, 0.008, rr=0.003, R=rot_from_axes(z_axis=n)), 0.002, BLACK_L)
    # the camera module on his right (-x) side, above the ear piece, a smoked lens looking forward
    p, n = helmet_point(-1.45, 1.835)
    R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
    cm_c = p + n * 0.016
    fd.add(RoundBox(cm_c, (0.018, 0.016, 0.042), 0.007, R=rot_from_axes(z_axis=(0, -1, 0), x_axis=n)), 0.004, BLACK_L)
    fd.add(Cylinder(cm_c + v3((0, -0.044, 0.0)), 0.011, 0.01, rr=0.003, R=rot_from_axes(z_axis=(0, -1, 0))), 0.002, GLASS_L)
    # the ear pieces: slim black pods over his ears, gunmetal rims, a violet ring on each
    for sx in (-1, 1):
        c = hp((sx * 0.203, 0.03, 1.662))
        Rr = rot_from_axes(z_axis=(sx, 0, 0))
        fd.add(Inter(Ellipsoid(c, v3((0.034, 0.047, 0.054)) * HS), Plane(c + v3((sx * 0.02, 0, 0)), (sx, 0, 0)), 0.008), 0.0, BLACK_L)
        fd.add(Torus(c + v3((sx * 0.016, 0, 0)), hr(0.036), 0.006, R=Rr), 0.004, GM_L)
        fd.paint(Torus(c + v3((sx * 0.024, 0, 0)), hr(0.022), 0.006, R=Rr), VIO_L)
        top = hp((sx * 0.192, 0.035, 1.775))
        fd.add(RoundCone(c + v3((sx * 0.004, 0.0, hr(0.046))), top, 0.009, 0.008), 0.005, BLACK_L)
    # the boom mic (his left), held off the grin's corner
    pts = [hp(p) for p in ((0.22, -0.02, 1.628), (0.2, -0.1, 1.596), (0.156, -0.18, 1.568), (0.106, -0.226, 1.556))]
    fd.add(Chain(pts, [0.0058, 0.0054, 0.005, 0.0046], k=0.004), 0.003, BLACK_L)
    fd.add(Sphere(hp((0.094, -0.234, 1.554)), hr(0.014)), 0.004, BLACK_L)
    # the chin strap: from the shell in front of and behind the ear pieces down to a cup under his chin
    hull = face_hull()
    off = Field("StrapHull")
    off.add(Func(lambda P: hull.eval(P, margin=0.05) - F(0.009), HEAD_C - 0.45, HEAD_C + 0.3), 0.0)
    for sx in (-1, 1):
        for guide in (((0.16, -0.06, 1.78), (0.158, -0.07, 1.66), (0.14, -0.072, 1.56), (0.1, -0.088, 1.48), (0.04, -0.112, 1.44)),
                      ((0.165, 0.11, 1.72), (0.16, 0.06, 1.6), (0.14, -0.02, 1.52), (0.1, -0.072, 1.47))):
            pts = project_to(off, np.array([hp((sx * x, y, z)) for x, y, z in guide]), iters=4)
            ns = [_fgrad(off.eval, p) for p in pts]
            fd.add(Lock(list(pts), [0.0085] * len(pts), [0.0028] * len(pts), ns, k=0.003), 0.002, BLACK_L)
    fd.add(Ellipsoid(hp((0.0, -0.125, 1.445)), v3((0.04, 0.03, 0.016)) * HS, R=euler(0.5, 0, 0)), 0.006, BLACK_L)
    return fd


def hair_field():
    """Short brown hair, cropped close: showing under the helmet's edge at his temples and nape, short sideburns."""
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
SLEEVE_END = ARM_LEN - 0.04                # the sleeves end under the gloves' cuffs


def _sleeve_cut(P):
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2 = _arm_coord(P, side)
        near = (d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3))
        out = np.maximum(out, np.where(near, s - F(SLEEVE_END), F(-1.0)))
    return out


def suit_keep(P):
    return np.maximum(np.maximum(F(SHIRT_HEM) - P[:, 2], tunic_neck(P) + F(0.012)), _sleeve_cut(P))


def suit_outer():
    b = shirt_hull()
    return Func(lambda P: b.eval(P, margin=0.1) - F(SHIRT_FACE), (-1, -0.6, 0.5), (1, 0.6, 1.7))


def _arm_out(side, s_frac, seg, out=0.0, around=0.0):
    """A point on the suit's outer face on the outside of his arm: seg 'upper' or 'fore', s_frac along it; `around` turns
    the outward direction toward the front (+) round the arm's axis. Returns (point, normal, axis)."""
    sx = -1 if side == "R" else 1
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    a, b = (sh, el) if seg == "upper" else (el, wr)
    c = lerp(a, b, s_frac)
    ax = norm(b - a)
    d0 = v3((sx, 0.0, 0.0))
    d0 = norm(d0 - ax * float(d0 @ ax))
    fw = norm(np.cross(ax, d0)) * (-sx)
    if fw[1] > 0:
        fw = -fw
    d = norm(d0 * math.cos(around) + fw * math.sin(around))
    so = suit_outer()
    h, ok = ray_hit(so, [c + d * 0.4], [-d], tmax=0.5)
    p = h[0] if ok[0] else c + d * 0.1
    n = _fgrad(so.fn, p)
    return p + n * out, n, ax


def suit_field():
    """Matte black cloth (0): the long-sleeved under-suit tucked in at his waist, a high stand collar; graphite armour
    panels (8) on the outside of the upper arms, a violet stripe (6) down the outside of each sleeve."""
    fd = Field("Suit")
    base = shirt_hull()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        return F(0.0014) * np.sin(a * F(7) + F(0.9) * NOISE(P * F(3))) + F(0.0011) * NOISE(P * F(20))
    lo, hi = (-1, -0.6, 0.5), (1, 0.6, 1.7)
    fd.add(Inter(Shell(base, SHIRT_OFF, SHIRT_T, pad=0.12, disp=folds, disp_amp=0.003), Func(suit_keep, lo, hi), 0.004), 0.0)
    # the high stand collar
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    def band(P):
        front = np.clip(-(P[:, 1] - F(0.03)) / F(0.1), 0, 1)
        return np.maximum(F(1.39) - P[:, 2], P[:, 2] - F(1.5) + F(0.03) * front)
    fd.add(Inter(Shell(nk, 0.02, 0.014, pad=0.08), Func(band, (-0.3, -0.3, 1.3), (0.3, 0.3, 1.56)), 0.004), 0.004)
    # armour panels on the upper arms and the violet stripes down the sleeves
    for side in ("R", "L"):
        p, n, ax = _arm_out(side, 0.42, "upper")
        side_v = norm(np.cross(n, ax))
        R = np.stack([side_v, ax, n], axis=1)
        fd.add(RoundBox(p + n * 0.004, (0.052, 0.085, 0.008), 0.007, R=R), 0.006, NAVY_L)
        fd.sub(RoundBox(p + n * 0.013 - ax * 0.03, (0.06, 0.0025, 0.006), 0.001, R=R), 0.0015)      # a panel line
        pts = [_arm_out(side, t, "upper", around=0.75)[0] for t in (0.08, 0.5, 0.95)]
        pts += [_arm_out(side, t, "fore", around=0.75)[0] for t in (0.15, 0.55, 0.85)]
        fd.paint(Chain(pts, [0.0075] * len(pts), k=0.004), VIO_L)
    return fd


# ======================================================================================= the armour vest
STRIP_X = 0.118                            # the light strips down the front plate (x)
STRIP_Z = (1.075, 1.305)


def _strip_lines():
    """The light strips' lines on the vest's outer face: two down the front plate, one over each shoulder strap."""
    co = carrier_outer()
    b = shirt_hull()
    so = Func(lambda P: b.eval(P, margin=0.12) - F(PC_IN + STRAP_T), (-0.8, -0.6, 0.8), (0.8, 0.6, 1.7))
    lines = []
    for sx in (-1, 1):
        pts, ns = [], []
        for z in np.linspace(STRIP_Z[0], STRIP_Z[1], 6):
            x = sx * (STRIP_X + 0.012 * (z - STRIP_Z[0]) / (STRIP_Z[1] - STRIP_Z[0]))
            p, n = _surface_frame(co, v3((x, -0.8, z)), v3((0, 1, 0)))
            pts.append(p)
            ns.append(n)
        lines.append((pts, ns))
        pts, ns = [], []
        for y in np.linspace(-0.19, 0.06, 5):
            p, n = _surface_frame(so, v3((sx * 0.128, y, 1.9)), v3((0, 0, -1)))
            pts.append(p)
            ns.append(n)
        lines.append((pts, ns))
    return lines


def strips_field():
    """The light strips (their own emissive mesh): flat bars lying in channels on the vest."""
    fd = Field("Strips")
    for pts, ns in _strip_lines():
        fd.add(Lock([p + n * 0.001 for p, n in zip(pts, ns)], [0.0105] * len(pts), [0.0068] * len(pts), ns, k=0.004), 0.003)
    return fd


def vest_field():
    """Graphite polymer (0): the front and back plates with panel-line grooves, a navy (8) cummerbund and padded shoulder
    straps, the channels the light strips lie in, a violet (6) edge along the plates' tops, a unit badge on his left chest
    (a gunmetal hexagon with a violet chevron), a gunmetal (9) buckle on each strap, two cell holders on the cummerbund
    (black, violet caps), a slim power unit on the back plate (gunmetal fins)."""
    fd = Field("Vest")
    base = shirt_hull()
    lo, hi = (-0.8, -0.6, 0.8), (0.8, 0.6, 1.7)
    cloth = lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.0006) * NOISE(P * F(90))
    fd.add(Inter(Shell(base, PLATE_OFF, PLATE_T, pad=0.14), Func(_plate_region, lo, hi), 0.012), 0.0)
    fd.add(Inter(Shell(base, CB_OFF, CB_T, pad=0.14, disp=cloth, disp_amp=0.002), Func(_cb_region, lo, hi), 0.006), 0.008, NAVY_L)
    fd.add(Inter(Shell(base, PC_IN + STRAP_T / 2, STRAP_T, pad=0.14, disp=cloth, disp_amp=0.001), Func(_strap_region, lo, hi), 0.01), 0.01, NAVY_L)
    out = PLATE_OFF + PLATE_T / 2
    # panel lines: across the front plate below the strips, round its middle, down its sides
    for zk in (1.045,):
        def groove(P, zk=zk):
            return np.maximum(np.maximum(np.abs(P[:, 2] - F(zk)) - F(0.0028), np.abs(P[:, 0]) - F(0.19)), P[:, 1] - F(0.02))
        fd.sub(Inter(Shell(base, out, 0.012, pad=0.14), Func(groove, lo, hi), 0.0), 0.002)
    def mid_groove(P):
        return np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.0028), P[:, 2] - F(1.27)), P[:, 1] - F(0.02))
    fd.sub(Inter(Shell(base, out, 0.012, pad=0.14), Func(mid_groove, lo, hi), 0.0), 0.002)
    for zk in (1.12, 1.24):
        def groove_b(P, zk=zk):
            return np.maximum(np.maximum(np.abs(P[:, 2] - F(zk)) - F(0.003), np.abs(P[:, 0]) - F(0.18)), F(0.07) - P[:, 1])
        fd.sub(Inter(Shell(base, out, 0.012, pad=0.14), Func(groove_b, lo, hi), 0.0), 0.002)
    # the violet edge along the front plate's top (the scoop at his neck)
    def edge(P):
        x = P[:, 0]
        top = mm._front_top(x)
        return np.maximum(np.maximum(np.abs(P[:, 2] - (top - F(0.012))) - F(0.007), np.abs(x) - F(0.2)), P[:, 1] - F(0.02))
    fd.paint(Func(edge, lo, hi), VIO_L)
    # channels for the light strips
    for pts, ns in _strip_lines():
        fd.sub(Lock([p + n * 0.002 for p, n in zip(pts, ns)], [0.0135] * len(pts), [0.009] * len(pts), ns, k=0.004), 0.002)
    co = carrier_outer()
    # the unit badge (his left chest, outside the strip)
    p, n = _surface_frame(co, v3((0.165, -0.8, 1.2)), v3((0, 1, 0)))
    up = norm(v3((0, 0, 1)) - n * float(n[2]))
    side = np.cross(up, n)
    R = rot_from_axes(z_axis=n, y_axis=up)
    hexd = lambda P, c=p + n * 0.004: _hex_sd(P, c, R, 0.026, 0.004)
    fd.add(Func(hexd, p - 0.05, p + 0.05), 0.002, GM_L)
    for s in (-1, 1):
        fd.paint(RoundCone(p + n * 0.008 + side * (s * 0.014) + up * 0.006, p + n * 0.008 - up * 0.008, 0.0045, 0.0045), VIO_L)
    # buckles on the shoulder straps
    for sx in (-1, 1):
        p, n = _surface_frame(co, v3((sx * 0.128, -0.8, 1.335)), v3((0, 1, 0)))
        fd.add(RoundBox(p + n * 0.004, (0.022, 0.014, 0.006), 0.004, R=rot_from_axes(z_axis=n, y_axis=(0, 0, 1))), 0.003, GM_L)
    # two cell holders on the cummerbund's front corners (black tubes, violet caps)
    for sx in (-1, 1):
        d = norm(v3((sx * 0.8, -1.0, 0.0)))
        p, n = _surface_frame(co, v3((sx * 0.25, 0.0, 1.06)) - d * 0.8, d)
        n = norm(v3((n[0], n[1], 0.0)))
        c = p + n * 0.024
        fd.add(Cylinder(c, 0.022, 0.1, rr=0.006), 0.006, BLACK_L)
        fd.add(Cylinder(c + v3((0, 0, 0.055)), 0.024, 0.016, rr=0.005), 0.003, VIO_L)
        fd.add(RoundBox(c - n * 0.016, (0.02, 0.008, 0.035), 0.004, R=rot_from_axes(z_axis=n, y_axis=(0, 0, 1))), 0.004, NAVY_L)
    # the slim power unit on the back plate: a gunmetal case with cooling fins and a violet status bar
    p, n = _surface_frame(co, v3((0.0, 0.8, 1.2)), v3((0, -1, 0)))
    R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
    pu = p + n * 0.022
    fd.add(RoundBox(pu, (0.085, 0.1, 0.02), 0.01, R=R), 0.008, GM_L)
    for k in range(5):
        fd.add(RoundBox(pu + n * 0.022 + R @ v3((0.0, -0.06 + 0.03 * k, 0.0)), (0.07, 0.004, 0.006), 0.002, R=R), 0.002, GM_L)
    fd.paint(RoundBox(pu + n * 0.02 + R @ v3((0.0, 0.088, 0.0)), (0.05, 0.006, 0.02), 0.002, R=R), VIO_L)
    return fd


def _hex_sd(P, c, R, r, t):
    q = (P - c.astype(F)) @ R.astype(F)
    x, y, z = np.abs(q[:, 0]), np.abs(q[:, 1]), q[:, 2]
    k = (F(-0.8660254), F(0.5))
    d = np.maximum(x * F(0.8660254) + y * F(0.5), y) - F(r)
    return np.maximum(d, np.abs(z) - F(t))


# ======================================================================================= the mortar (layout)
MX = 0.55                                  # the tube's middle line (x); it shoots toward -Y
TRUN = v3((MX, -0.28, 0.72))               # the trunnions (the gimbal ring tilts about them)
ELEV = math.radians(55.0)                  # the tube's elevation (fixed: a mortar lobs)
GD = v3((0.0, -math.cos(ELEV), math.sin(ELEV)))      # along the tube, toward its mouth
GU = v3((0.0, math.sin(ELEV), math.cos(ELEV)))       # across the tube, up and back
GX_ = v3((1.0, 0.0, 0.0))
TUBE_R = 0.128                             # the tube's body
BORE_R = 0.09
S_BREECH = (-0.37, -0.15)                  # the breech housing (s along the tube from the trunnions)
BREECH_R = 0.165
S_FINS = (-0.135, -0.045)                  # the heat-sink fins
COIL_S = (0.1, 0.212, 0.324)               # the coil collars' middles
COIL_HW = 0.04                             # a collar's half width (along the tube)
COIL_R = 0.165                             # a collar's outer radius ...
GROOVE_R = 0.149                           # ... its groove's bottom ...
BAND_R0, BAND_R1, BAND_HW = 0.136, 0.161, 0.012      # ... the glowing band in the groove (inner, outer radius, half width)
S_MOUTH = 0.52                             # the muzzle's mouth
S_CHARGE = 0.43                            # the plasma charge's middle, deep in the bore
S_PORT = -0.255                            # the cell port (on the breech's top, toward +GU)
RING_IN, RING_OUT, RING_HW = 0.152, 0.205, 0.034     # the gimbal ring
YOKE_X = 0.255                             # the yoke plates' middles (x from MX)
MOUNT_C = v3((MX, -0.22, 0.0))             # the mount's middle on the ground
TT_Z = (0.15, 0.205)                       # the turntable (z range)
TT_R = 0.32
CELL_L, CELL_R = 0.2, 0.036                # a plasma cell
CORE_R, CORE_L = 0.031, 0.124              # its glowing core
SLOT_D = 0.026                             # its slots go in to here
CELL_OUT = 0.07                            # a seated cell stands this far out of its port's top
GRIP_C = v3((0.255, -0.03, 0.835))         # the firing grip's middle
GRIP_A = norm(v3((0.0, -0.3, 1.0)))        # its axis (thumb up it)
RACK_C = v3((0.62, 0.52, 0.0))             # the charging rack's middle on the ground
RACK_TOP = 0.66                            # its socket block's top
RACK_SLOTS = ((-0.046, -0.046), (0.046, -0.046), (-0.046, 0.046), (0.046, 0.046))   # (dx, dy) of its four sockets
HIS_SLOT = 0                               # the socket nearest him (front, his side): the cell he takes
PACK_C = v3((MX, -0.43, 0.31))             # the power pack's middle (under the tube's front)
PACK_HALF = (0.12, 0.075, 0.1)


def tpt(s, u=0.0, v=0.0):
    """A point in the tube's frame (rest): s along the tube from the trunnions, u across (+X), v up-and-back (GU)."""
    return TRUN + GD * s + GX_ * u + GU * v


def _rtube():
    return np.stack([GX_, GD, GU], axis=1)


def _tube_local(P):
    q = (P - TRUN.astype(F)) @ _rtube().astype(F)
    return q[:, 0], q[:, 1], q[:, 2]


def _ring_sd(s0, s1, r0, r1, rr=0.006):
    """< 0 inside the annulus r0..r1 round the tube's axis between s0 and s1 (rounded edges)."""
    def fn(P):
        u, s, v = _tube_local(P)
        r = np.sqrt(u * u + v * v)
        dr = np.abs(r - F((r0 + r1) / 2)) - F((r1 - r0) / 2) + F(rr)
        ds = np.abs(s - F((s0 + s1) / 2)) - F((s1 - s0) / 2) + F(rr)
        return np.minimum(np.maximum(dr, ds), 0) + np.sqrt(np.maximum(dr, 0) ** 2 + np.maximum(ds, 0) ** 2) - F(rr)
    return fn


def _tube_bounds(s0, s1, r):
    pts = [tpt(s, u, v) for s in (s0, s1) for u in (-r, r) for v in (-r, r)]
    return np.min(pts, 0) - 0.03, np.max(pts, 0) + 0.03


def port_top():
    """The cell port's mouth (the middle of its top face) and its axis (out of the breech)."""
    return tpt(S_PORT, 0.0, BREECH_R + 0.052), GU


def seated_cell():
    """The seated cell's middle and its axis (bottom -> top)."""
    pt, ax = port_top()
    return pt + ax * (CELL_OUT - CELL_L / 2), ax


def rack_slot(i):
    """Rack socket i: the middle of a cell standing in it, its axis (up)."""
    dx, dy = RACK_SLOTS[i]
    return RACK_C + v3((dx, dy, RACK_TOP + CELL_OUT - CELL_L / 2)), v3((0.0, 0.0, 1.0))


# ======================================================================================= the plasma cell
def cell_into(fd, mid, ax, k=0.0, seed=0.0):
    """A plasma cell: a gloss-black canister (5) with three long slots down it (its core shows through them), gunmetal end
    caps (9) with a grip ring on the top cap (10), a white band (7)."""
    ax = norm(ax)
    R = rot_from_axes(z_axis=ax)
    fd.add(Cylinder(mid, CELL_R, CELL_L - 0.05, rr=0.006, R=R), k, BLACK_L)
    for s in (-1, 1):
        fd.add(Cylinder(mid + ax * (s * (CELL_L / 2 - 0.018)), CELL_R + 0.004, 0.036, rr=0.008, R=R), 0.003, GM_L)
    fd.add(Torus(mid + ax * (CELL_L / 2 + 0.002), 0.018, 0.005, R=R), 0.002, STEEL_L)
    side = norm(np.cross(ax, v3((0.0, 0.0, 1.0)) if abs(ax[2]) < 0.9 else v3((1.0, 0.0, 0.0))))
    up = np.cross(ax, side)
    for k2 in range(3):
        a = seed + 2 * math.pi * k2 / 3
        d = side * math.cos(a) + up * math.sin(a)
        Rs = np.stack([np.cross(ax, d), d, ax], axis=1)
        fd.sub(RoundBox(mid + d * (SLOT_D + 0.03), (0.0085, 0.03, CORE_L / 2 - 0.006), 0.004, R=Rs), 0.002)
    fd.paint(Cylinder(mid - ax * (CORE_L / 2 + 0.004), CELL_R + 0.01, 0.007, R=R), WHITE_L)


def core_into(fd, mid, ax, k=0.0):
    ax = norm(ax)
    fd.add(Cylinder(mid, CORE_R, CORE_L, rr=0.008, R=rot_from_axes(z_axis=ax)), k)


def cell_field():
    fd = Field("Cell")
    mid, ax = seated_cell()
    cell_into(fd, mid, ax)
    return fd


def cellcore_field():
    fd = Field("CellCore")
    mid, ax = seated_cell()
    core_into(fd, mid, ax)
    return fd


# ======================================================================================= the tube
def tube_field():
    """The tube (modern_kit): its body (graphite 0), the gloss-black breech housing (5) with grooved panel lines, the
    cell port (a gunmetal socket on its top, its rim painted violet), a collar of gunmetal heat-sink fins, the trunnion band,
    three graphite coil collars each with a groove round its middle (the coil band glows in it), a flared gunmetal muzzle
    with a black bore; white stencils."""
    fd = Field("Tube")
    lo, hi = _tube_bounds(S_BREECH[0] - 0.02, S_MOUTH + 0.02, 0.24)
    fd.add(capped_cone(tpt(S_BREECH[1] - 0.02), tpt(S_MOUTH - 0.08), TUBE_R, TUBE_R - 0.004, rr=0.01), 0.0, BASE_L)
    # the breech housing: a rounded drum, its bottom domed
    fd.add(Cylinder(tpt((S_BREECH[0] + S_BREECH[1]) / 2), BREECH_R, S_BREECH[1] - S_BREECH[0], rr=0.055,
                    R=rot_from_axes(z_axis=GD)), 0.012, BLACK_L)
    fd.add(Ellipsoid(tpt(S_BREECH[0] + 0.02), (0.12, 0.12, 0.05), R=rot_from_axes(z_axis=GD)), 0.03, BLACK_L)
    for s in (-0.3, -0.21):
        fd.sub(Func(_ring_sd(s - 0.0025, s + 0.0025, BREECH_R - 0.006, BREECH_R + 0.02, rr=0.0), lo, hi), 0.0015)
    fd.add(Func(_ring_sd(S_BREECH[1] - 0.01, S_BREECH[1] + 0.012, TUBE_R - 0.01, BREECH_R - 0.004), lo, hi), 0.006, GM_L)
    # the cell port: a socket boss on the breech's top, a bore into it for the cell
    pt, ax = port_top()
    Rp = rot_from_axes(z_axis=ax)
    fd.add(Cylinder(pt - ax * 0.034, 0.056, 0.068, rr=0.012, R=Rp), 0.012, GM_L)
    fd.sub(Cylinder(pt - ax * 0.06, CELL_R + 0.006, 0.14, R=Rp), 0.003)
    fd.paint(Torus(pt, 0.047, 0.006, R=Rp), VIO_L)
    for s in (-1, 1):                                                                  # its latches
        fd.add(RoundBox(pt - ax * 0.02 + GX_ * (s * 0.058), (0.008, 0.018, 0.024), 0.004, R=rot_from_axes(z_axis=ax, x_axis=GX_)), 0.003, STEEL_L)
    # cable sockets under the breech (the power pack's cables plug in here)
    for s in (-1, 1):
        c = tpt(-0.2, s * 0.05, -BREECH_R + 0.01)
        fd.add(Cylinder(c, 0.024, 0.04, rr=0.006, R=rot_from_axes(z_axis=-GU)), 0.006, GM_L)
    # the heat-sink fins
    n_fin = 14
    for k in range(n_fin):
        a = 2 * math.pi * (k + 0.5) / n_fin
        d = GX_ * math.cos(a) + GU * math.sin(a)
        Rf = np.stack([np.cross(GD, d), GD, d], axis=1)
        c = tpt((S_FINS[0] + S_FINS[1]) / 2) + d * (TUBE_R + 0.03)
        fd.add(RoundBox(c, (0.0045, (S_FINS[1] - S_FINS[0]) / 2, 0.034), 0.003, R=Rf), 0.004, GM_L)
    fd.add(Func(_ring_sd(S_FINS[0] - 0.012, S_FINS[0] + 0.002, TUBE_R - 0.01, TUBE_R + 0.035), lo, hi), 0.004, GM_L)
    # the trunnion band (it rides in the gimbal ring)
    fd.add(Func(_ring_sd(-0.032, 0.032, TUBE_R - 0.01, RING_IN - 0.008), lo, hi), 0.006, GM_L)
    # the coil collars, each with a groove round its middle (the band glows in it), thin rims either side
    for s in COIL_S:
        fd.add(Func(_ring_sd(s - COIL_HW, s + COIL_HW, TUBE_R - 0.01, COIL_R, rr=0.01), lo, hi), 0.008, BASE_L)
        fd.sub(Func(_ring_sd(s - BAND_HW - 0.002, s + BAND_HW + 0.002, GROOVE_R, COIL_R + 0.02, rr=0.0), lo, hi), 0.002)
        for e in (-1, 1):
            fd.paint(Func(_ring_sd(s + e * (COIL_HW - 0.007) - 0.005, s + e * (COIL_HW - 0.007) + 0.005, TUBE_R, COIL_R + 0.01, rr=0.0), lo, hi), GM_L)
    # the muzzle: a flared gunmetal collar, the black bore
    fd.add(capped_cone(tpt(S_MOUTH - 0.1), tpt(S_MOUTH), TUBE_R + 0.012, 0.162, rr=0.016), 0.012, GM_L)
    fd.add(Torus(tpt(S_MOUTH - 0.012), 0.148, 0.014, R=rot_from_axes(z_axis=GD)), 0.006, GM_L)
    fd.sub(Cylinder(tpt(S_MOUTH), BORE_R, 2 * (S_MOUTH - S_CHARGE) + 0.03, rr=0.0, R=rot_from_axes(z_axis=GD)), 0.008)
    def bore(P):
        u, s, v = _tube_local(P)
        r = np.sqrt(u * u + v * v)
        return np.maximum(r - F(BORE_R + 0.008), F(S_CHARGE - 0.04) - s)
    fd.paint(Func(bore, lo, hi), BLACK_L)
    # stencils on the tube's top (read from behind it) and a white band below the muzzle
    stencil(fd, "PM-9", tpt(-0.262, -BREECH_R - 0.001, 0.0), GD, GU, 0.034, WHITE_L, depth=0.01)
    fd.paint(Func(_ring_sd(0.385, 0.398, TUBE_R - 0.02, TUBE_R + 0.03, rr=0.0), lo, hi), VIO_L)
    return fd


def coils_field():
    """The coil bands (glowing, sunk in their grooves) and the plasma charge deep in the bore: one emissive mesh, scaled in
    toward the tube's axis to put them out (the bands sink below the grooves' bottoms)."""
    fd = Field("Coils")
    lo, hi = _tube_bounds(COIL_S[0] - 0.05, S_MOUTH, 0.2)
    for s in COIL_S:
        fd.add(Func(_ring_sd(s - BAND_HW, s + BAND_HW, BAND_R0, BAND_R1, rr=0.004), lo, hi), 0.0)
    # the charge: a domed lens of plasma filling the bore's bottom
    c = tpt(S_CHARGE)
    fd.add(Inter(Sphere(c - GD * 0.05, 0.1), Cylinder(c, BORE_R - 0.004, 0.06, rr=0.006, R=rot_from_axes(z_axis=GD)), 0.004), 0.0)
    return fd


# ======================================================================================= the gimbal ring (cradle)
def cradle_field():
    """The gimbal ring round the tube's trunnion band (gunmetal 9, a graphite (0) face, a violet painted line), its
    trunnion pins out to the yoke plates."""
    fd = Field("Cradle")
    lo, hi = _tube_bounds(-RING_HW - 0.02, RING_HW + 0.02, RING_OUT + 0.12)
    fd.add(Func(_ring_sd(-RING_HW, RING_HW, RING_IN, RING_OUT, rr=0.012), lo, hi), 0.0, GM_L)
    fd.add(Func(_ring_sd(-RING_HW - 0.004, -RING_HW + 0.012, RING_IN + 0.01, RING_OUT - 0.008, rr=0.004), lo, hi), 0.003, BASE_L)
    fd.paint(Func(_ring_sd(-0.004, 0.004, RING_OUT - 0.02, RING_OUT + 0.02, rr=0.0), lo, hi), VIO_L)
    for sx in (-1, 1):
        a = TRUN + GX_ * (sx * (RING_OUT - 0.01))
        b = TRUN + GX_ * (sx * (YOKE_X - 0.01))
        fd.add(Cylinder((a + b) / 2, 0.042, float(np.linalg.norm(b - a)), rr=0.008, R=rot_from_axes(z_axis=GX_)), 0.008, GM_L)
    return fd


# ======================================================================================= the mount, pack, grip and rack
YOKE = [(-0.24, 0.205), (0.22, 0.205), (0.12, 0.6), (0.075, 0.79), (-0.075, 0.79), (-0.14, 0.6)]   # (y from TRUN, z)


def mount_field():
    """The mount (modern_kit): a round base plate (graphite 0, a hazard-yellow (13) and black ring round its edge, bolts),
    a short gunmetal column, the turntable (graphite, a violet line round its rim, gunmetal teeth), the yoke's two side
    plates (graphite, lightening slots, gunmetal trunnion caps); the power pack under the tube's front (gloss black, cooling
    fins, the violet window's frame), its cables up into the breech; the firing grip on the near plate (black rubber 12, a
    gunmetal bracket, a violet trigger guard); the charging rack (a gunmetal stand, a graphite socket block with violet
    rims, three cells in it, the fourth socket empty) with its cable along the ground to the base plate."""
    fd = Field("Mount")
    c0 = v3((MOUNT_C[0], MOUNT_C[1], 0.0))
    fd.add(Cylinder(c0 + v3((0, 0, 0.026)), 0.36, 0.052, rr=0.018), 0.0, BASE_L)
    def edge_ring(P):
        r = np.sqrt((P[:, 0] - F(c0[0])) ** 2 + (P[:, 1] - F(c0[1])) ** 2)
        return np.maximum(np.abs(r - F(0.33)) - F(0.016), P[:, 2] - F(0.06))
    fd.paint(Func(edge_ring, c0 - v3((0.4, 0.4, 0.0)), c0 + v3((0.4, 0.4, 0.1))), HAZ_L)
    def stripes(P):
        a = np.arctan2(P[:, 1] - F(c0[1]), P[:, 0] - F(c0[0]))
        r = np.sqrt((P[:, 0] - F(c0[0])) ** 2 + (P[:, 1] - F(c0[1])) ** 2)
        ph = (a * F(0.33) + (r - F(0.33))) / F(0.032)
        st = np.abs((ph % F(2.0)) - F(1.0)) - F(0.5)
        return np.maximum(np.maximum(np.abs(r - F(0.33)) - F(0.017), P[:, 2] - F(0.06)), st * F(0.02))
    fd.paint(Func(stripes, c0 - v3((0.4, 0.4, 0.0)), c0 + v3((0.4, 0.4, 0.1))), BLACK_L)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        fd.add(Cylinder(c0 + v3((math.cos(a) * 0.27, math.sin(a) * 0.27, 0.054)), 0.012, 0.012, rr=0.004), 0.002, GM_L)
    fd.add(Cylinder(c0 + v3((0, 0, (0.05 + TT_Z[0]) / 2)), 0.13, TT_Z[0] - 0.04, rr=0.01), 0.008, GM_L)
    fd.add(Cylinder(c0 + v3((0, 0, (TT_Z[0] + TT_Z[1]) / 2)), TT_R, TT_Z[1] - TT_Z[0], rr=0.014), 0.006, BASE_L)
    def tt_line(P):
        r = np.sqrt((P[:, 0] - F(c0[0])) ** 2 + (P[:, 1] - F(c0[1])) ** 2)
        return np.maximum(np.abs(P[:, 2] - F(TT_Z[0] + 0.022)) - F(0.006), F(TT_R - 0.02) - r)
    fd.paint(Func(tt_line, c0 - v3((0.4, 0.4, 0.0)), c0 + v3((0.4, 0.4, 0.3))), VIO_L)
    for k in range(30):
        a = 2 * math.pi * k / 30
        fd.add(RoundBox(c0 + v3((math.cos(a) * (TT_R - 0.17), math.sin(a) * (TT_R - 0.17), TT_Z[0] - 0.012)),
                        (0.012, 0.008, 0.014), 0.003, R=euler(0, 0, a)), 0.002, GM_L)
    # the yoke plates
    p2 = poly2d(YOKE)
    for sx in (-1, 1):
        xc = MX + sx * YOKE_X
        def plate(P, xc=xc):
            d2 = p2(P[:, 1] - F(TRUN[1]), P[:, 2])
            disc = np.sqrt((P[:, 1] - F(TRUN[1])) ** 2 + (P[:, 2] - F(TRUN[2])) ** 2) - F(0.085)
            d2 = np.minimum(d2, disc)
            slot = np.maximum(np.abs(P[:, 1] - F(TRUN[1] - 0.005)) - F(0.03), np.abs(P[:, 2] - F(0.44)) - F(0.11))
            d2 = np.maximum(d2, -(slot - F(0.012)))
            dx = np.abs(P[:, 0] - F(xc)) - F(0.018)
            r = F(0.01)
            w0, w1 = d2 + r, dx + r
            return np.minimum(np.maximum(w0, w1), F(0)) + np.sqrt(np.maximum(w0, 0) ** 2 + np.maximum(w1, 0) ** 2) - r
        fd.add(Func(plate, (xc - 0.05, TRUN[1] - 0.3, 0.15), (xc + 0.05, TRUN[1] + 0.3, 0.86)), 0.008, BASE_L)
        cap = TRUN + GX_ * (sx * (YOKE_X + 0.024))
        fd.add(Cylinder(cap, 0.06, 0.026, rr=0.008, R=rot_from_axes(z_axis=GX_)), 0.004, GM_L)
        fd.paint(Torus(cap + GX_ * (sx * 0.013), 0.042, 0.005, R=rot_from_axes(z_axis=GX_)), VIO_L)
        for k in range(6):
            a = 2 * math.pi * k / 6
            fd.add(Sphere(TRUN + GX_ * (sx * (YOKE_X + 0.038)) + v3((0, math.cos(a) * 0.044, math.sin(a) * 0.044)), 0.0065), 0.001, STEEL_L)
        stencil(fd, "PM-9", v3((xc + sx * 0.019, TRUN[1] - 0.02, 0.33)), v3((0, -sx, 0)), v3((0, 0, 1)), 0.028, WHITE_L, depth=0.008)
    # the power pack under the tube's front: a gloss-black case, cooling fins on its sides, a window frame on its front
    pc = PACK_C
    hx, hy, hz = PACK_HALF
    fd.add(RoundBox(pc, (hx, hy, hz), 0.026), 0.0, BLACK_L)
    fd.add(RoundBox(pc + v3((0, 0, -hz + 0.01)), (hx + 0.012, hy + 0.012, 0.016), 0.008), 0.006, GM_L)
    for sx in (-1, 1):
        for k in range(5):
            fd.add(RoundBox(pc + v3((sx * (hx + 0.008), -hy + 0.03 + 0.03 * k, 0.0)), (0.012, 0.004, hz - 0.03), 0.002), 0.003, GM_L)
    fw = pc + v3((0, -hy, 0.012))
    fd.add(RoundBox(fw + v3((0, -0.004, 0)), (hx - 0.022, 0.006, hz - 0.035), 0.006), 0.004, GM_L)
    fd.sub(RoundBox(fw + v3((0, -0.01, 0)), (hx - 0.036, 0.008, hz - 0.05), 0.004), 0.002)
    stencil(fd, "PWR", pc + v3((0, -hy - 0.002, -hz + 0.035)), v3((1, 0, 0)), v3((0, 0, 1)), 0.022, WHITE_L, depth=0.008)
    # its cables, up into the sockets under the breech
    for s in (-1, 1):
        a = pc + v3((s * 0.05, hy - 0.01, hz - 0.01))
        e = tpt(-0.2, s * 0.05, -BREECH_R - 0.012)
        mid = (a + e) * 0.5 + v3((0, 0.02, -0.03))
        fd.add(Chain([a, a + v3((0, 0.02, 0.03)), mid, e], [0.016] * 4, k=0.01), 0.004, RUBBER_L)
    # the firing grip on the near yoke plate: a bracket out and up from the plate, the grip, a trigger guard
    xc = MX - YOKE_X
    b0 = v3((xc - 0.012, TRUN[1] + 0.13, 0.62))
    gb = GRIP_C - GRIP_A * 0.07
    fd.add(Chain([b0, b0 + v3((-0.02, 0.06, 0.04)), gb + v3((0.0, 0.0, -0.035)), gb], [0.022, 0.02, 0.018, 0.018], k=0.012), 0.008, GM_L)
    fd.add(RoundCone(GRIP_C - GRIP_A * 0.062, GRIP_C + GRIP_A * 0.062, 0.022, 0.02), 0.008, RUBBER_L)
    fd.add(Sphere(GRIP_C + GRIP_A * 0.072, 0.026), 0.008, GM_L)
    fwd_g = norm(v3((0.0, -1.0, 0.3)))
    gd_pts = [GRIP_C + GRIP_A * 0.05 + fwd_g * 0.02, GRIP_C + GRIP_A * 0.02 + fwd_g * 0.065, GRIP_C - GRIP_A * 0.045 + fwd_g * 0.05,
              GRIP_C - GRIP_A * 0.06 + fwd_g * 0.018]
    fd.add(Chain(gd_pts, [0.0065] * 4, k=0.004), 0.003, VIO_L)
    fd.add(RoundBox(GRIP_C + GRIP_A * 0.02 + fwd_g * 0.03, (0.006, 0.01, 0.016), 0.003, R=rot_from_axes(z_axis=GRIP_A, y_axis=fwd_g)), 0.002, STEEL_L)
    # the charging rack
    rc = RACK_C
    fd.add(RoundBox(rc + v3((0, 0, 0.014)), (0.13, 0.13, 0.014), 0.008), 0.0, GM_L)
    fd.add(Cylinder(rc + v3((0, 0, 0.29)), 0.04, 0.54, rr=0.01), 0.006, GM_L)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        fd.add(RoundCone(rc + v3((math.cos(a) * 0.11, math.sin(a) * 0.11, 0.03)), rc + v3((0, 0, 0.16)), 0.014, 0.012), 0.008, GM_L)
    blk = rc + v3((0, 0, RACK_TOP - 0.06))
    fd.add(RoundBox(blk, (0.105, 0.105, 0.06), 0.018), 0.008, BASE_L)
    for i in range(4):
        mid, ax = rack_slot(i)
        top = v3((mid[0], mid[1], RACK_TOP))
        fd.sub(Cylinder(top - v3((0, 0, 0.05)), CELL_R + 0.006, 0.12), 0.003)
        fd.paint(Torus(top, CELL_R + 0.012, 0.005), VIO_L)
        if i != HIS_SLOT:
            cell_into(fd, mid, ax, k=0.002, seed=0.6 * i)
    fd.paint(RoundBox(blk + v3((0, -0.105, -0.02)), (0.07, 0.01, 0.012), 0.004), WHITE_L)
    # the rack's cable along the ground to the base plate
    a = rc + v3((0.04, -0.1, 0.018))
    e = c0 + v3((0.08, 0.33, 0.03))
    fd.add(Chain([a, a + v3((0.01, -0.08, -0.004)), (a + e) * 0.5 + v3((0.04, 0.0, -0.006)), e], [0.014] * 4, k=0.02), 0.004, RUBBER_L)
    return fd


def mountglow_field():
    """The mount's glows (one emissive mesh): the charging cells' cores in the rack, the power pack's window."""
    fd = Field("MountGlow")
    for i in range(4):
        if i != HIS_SLOT:
            mid, ax = rack_slot(i)
            core_into(fd, mid, ax)
    fw = PACK_C + v3((0, -PACK_HALF[1], 0.012))
    fd.add(RoundBox(fw + v3((0, -0.002, 0)), (PACK_HALF[0] - 0.034, 0.006, PACK_HALF[2] - 0.048), 0.004), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.618)), 0.045, 0.5)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.09, -0.15, 1.616)), 0.05, 0.45), (hp((sx * 0.05, -0.18, 1.77)), 0.06, 0.2)]
    return pts


# ======================================================================================= build config
GLB_NAME = "plasma_mortar"
ROOT_NAME = "PlasmaMortarHQ"
TEX_PREFIX = "plasma_mortar"
MAT_NAME = "PlasmaMortarMat"
MESH_NAME = "PlasmaMortar"
BASE_MODULE = "plasma_mortar_base"
ANIM_MODULE = "anim_plasma_mortar"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Helmet", "Suit", "Vest", "Strips", "Trousers", "Boots", "Gloves",
         "Mount", "MountGlow", "Cradle", "Tube", "Coils", "Cell", "CellCore"]
REGION_PARTS = ("Skin", "Helmet", "Suit", "Vest", "Trousers", "Boots", "Mount", "Cradle", "Tube", "Cell")
KIT = dict(red=VIOLET_P, white=WHITE, olive=NAVY, gunmetal=GUNMETAL, steel=(0.62, 0.64, 0.68), glass=(0.05, 0.05, 0.08),
           rubber=(0.09, 0.09, 0.1), coyote=HAZARD, black=(0.05, 0.05, 0.06))
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_PmSkin", "base": (0.8, 0.58, 0.46), "ruddy": (0.84, 0.46, 0.38), "lips": (0.7, 0.4, 0.36),
                      "brow": ((0.16, 0.1, 0.06), (0.3, 0.19, 0.11)),
                      "extra": ((LASH, (0.08, 0.05, 0.035), 0.5), (STUBBLE, (0.45, 0.32, 0.24), 0.45, 0.4))}),
    "Hair": ("hair", {"name": "HQ_PmHair", "base": (0.2, 0.13, 0.08), "hi": (0.38, 0.25, 0.15), "low": (0.1, 0.065, 0.04),
                      "streak": (0.15, 0.1, 0.06), "tint": (0.24, 0.16, 0.09)}),
    "Helmet": ("modern_kit", dict(KIT, name="HQ_PmHelmet", base=GRAPHITE, weave=0.0)),
    "Suit": ("modern_kit", dict(KIT, name="HQ_PmSuit", base=SUIT_BLACK, weave=1.0, olive=GRAPHITE)),
    "Vest": ("modern_kit", dict(KIT, name="HQ_PmVest", base=GRAPHITE, weave=0.0)),
    "Trousers": ("uniform", {"name": "HQ_PmTrousers", "base": NAVY, "facing": VIOLET_P, "brass": (0.62, 0.64, 0.68),
                             "buff": GRAPHITE, "black": SUIT_BLACK}),
    "Boots": ("leather_dyed", {"name": "HQ_PmBoots", "base": (0.07, 0.068, 0.075), "dyed": (0.05, 0.048, 0.055), "worn_c": (0.3, 0.29, 0.31)}),
    "Gloves": ("leather_dyed", {"name": "HQ_PmGloves", "base": (0.08, 0.08, 0.09), "dyed": (0.08, 0.08, 0.09), "worn_c": (0.28, 0.28, 0.3)}),
    "Mount": ("modern_kit", dict(KIT, name="HQ_PmMortar", base=HOUSING, weave=0.0)),
    "Cradle": ("modern_kit", dict(KIT, name="HQ_PmMortar", base=HOUSING, weave=0.0)),
    "Tube": ("modern_kit", dict(KIT, name="HQ_PmMortar", base=HOUSING, weave=0.0)),
    "Cell": ("modern_kit", dict(KIT, name="HQ_PmMortar", base=HOUSING, weave=0.0)),
}
GLOW = {"Strips": (VIOLET, 1.1, 0.5), "Coils": (VIOLET, 1.3, 0.5), "CellCore": (VIOLET, 1.2, 0.5), "MountGlow": (VIOLET, 1.1, 0.5)}
LOW_TARGETS = {"Skin": 5200, "Teeth": 120, "Hair": 380, "Helmet": 1700, "Suit": 3000, "Vest": 2800, "Strips": 160,
               "Trousers": 1900, "Boots": 1100, "Gloves": 900, "Mount": 3600, "MountGlow": 260, "Cradle": 700, "Tube": 3200,
               "Coils": 520, "Cell": 360, "CellCore": 80}
AO_EXCLUDE = ["Cell", "Helmet"]
MACHINE_PARTS = ["Mount", "Cradle", "Tube", "Cell"]
# the mortar is baked 6 m away from him (his rest pose stands close to it)
BAKE_APART = (MACHINE_PARTS, (6.0, 0.0, 0.0))
YAW_PIVOT = (0.24, -0.02, 0.0)             # the tower turns about this point (keeps him, the mortar and the rack on the base)


def prop_bones():
    return []                                # everything he handles is a free bone (extra_bones)


def extra_bones():
    """The mortar's bones (none of them deform him): mount (the base, turntable, yoke, pack, grip and rack: still),
    cradle (the gimbal ring, tilting about the trunnions; child of the mount), tube (free: it recoils along its axis),
    coils (child of the tube, along its axis: the glowing bands and charge, scaled in across the axis to go dark),
    cell (free: the plasma cell, bottom -> top along its axis; seated in the port at rest), cellcore (child of the cell, along
    its axis: its glowing core, scaled in to go dark); mouth (child of the tube: its head in the middle of the muzzle's
    mouth, its tail 0.1 out along the bore: where the game's plasma ball leaves, and which way)."""
    mid, ax = seated_cell()
    return [
        ("mount", v3((MOUNT_C[0], MOUNT_C[1], 0.0)), v3((MOUNT_C[0], MOUNT_C[1], 0.3)), None),
        ("cradle", TRUN, TRUN + GD * 0.3, "mount"),
        ("tube", TRUN, TRUN + GD * 0.3, None),
        ("coils", TRUN, TRUN + GD * 0.3, "tube"),
        ("mouth", tpt(S_MOUTH), tpt(S_MOUTH + 0.1), "tube"),
        ("cell", mid, mid + ax * 0.1, None),
        ("cellcore", mid, mid + ax * 0.1, "cell"),
    ]


def weight_rules():
    body = TORSO | {"clavicle.R", "clavicle.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Helmet": ("rigid", "head"),
        "Suit": ("transfer", body | {"upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}, None),
        "Vest": ("transfer", body, None),
        "Strips": ("rigid", "chest"),
        "Trousers": ("custom", trousers_weights),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Mount": ("rigid", "mount"), "MountGlow": ("rigid", "mount"), "Cradle": ("rigid", "cradle"),
        "Tube": ("rigid", "tube"), "Coils": ("rigid", "coils"), "Cell": ("rigid", "cell"), "CellCore": ("rigid", "cellcore"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part == "Skin" and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Cell",):
        return 1.3
    if part in ("Mount",):
        return 0.75
    if part in ("Tube",):
        return 1.0
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012 if fine else 0.0016),
        ("Hair", hair_field(), 0.0022 if fine else 0.003),
        ("Helmet", helmet_field(), 0.0022 if fine else 0.0032),
        ("Suit", suit_field(), 0.0026 if fine else 0.0036),
        ("Vest", vest_field(), 0.0026 if fine else 0.0036),
        ("Strips", strips_field(), 0.0016 if fine else 0.0022),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Gloves", gloves_field(), 0.0018 if fine else 0.0026),
        ("Mount", mount_field(), 0.0028 if fine else 0.004),
        ("MountGlow", mountglow_field(), 0.0018 if fine else 0.0026),
        ("Cradle", cradle_field(), 0.0024 if fine else 0.0034),
        ("Tube", tube_field(), 0.0024 if fine else 0.0034),
        ("Coils", coils_field(), 0.0018 if fine else 0.0026),
        ("Cell", cell_field(), 0.0014 if fine else 0.002),
        ("CellCore", cellcore_field(), 0.0016 if fine else 0.0022),
    ]
