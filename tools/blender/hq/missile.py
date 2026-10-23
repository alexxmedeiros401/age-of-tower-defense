"""The Missile Launcher (HQ tower, Modern Age; Siege lineage): a compact pedestal-mounted missile launcher of the task
force and the soldier who fires it. Rest pose: he stands in an A-pose facing -Y (the way it shoots), feet at z = 0, the
launcher on his left (+X) and a little ahead of him; behind him his ready crate of missiles. The launcher is loaded.

Him: the Field Gun's burly body (torsion.py), his own face: a medium-brown, clean-shaven face with a shadow of stubble on
the jaw, a square jaw and chin, a straight nose, level dark brows, steady dark eyes, a firm closed mouth; focused, calm.
A high-cut combat helmet (olive paint worn on its edges, a black rubber edge trim, a black NVG mount at the front, side
rails, a black strobe pouch behind) with a black headset on the rails (big ear cups over his ears, a boom mic to the corner
of his mouth) and a black chin strap. An olive combat shirt, its sleeves rolled up to mid-forearm, a small stand collar,
a red-and-white unit patch on his left sleeve; a coyote-tan plate carrier over it (front and back plate bags, padded
shoulder straps, a cummerbund, two magazine pouches on each side, a velcro panel with a red-and-white patch on his chest,
a radio pouch on his back with a black whip antenna), its fire-control tablet clipped to the front; olive trousers with
cargo pockets and black knee pads, a black rigger's belt, black combat boots, black gloves.

The fire-control unit (on its own bone, `tablet`): a rugged tablet in a black case (grey rubber corners, a grip bar down
each side, an antenna stub), its screen a dark teal tactical display (a white grid, white tracks, a red target mark).
It rides his chest mount at rest; the clips take it off and hold it out before him.

The launcher: a squat steel pedestal (a base plate on four levelling jacks, a gunmetal column, a traversing ring and an
olive turret plate) carrying an olive yoke of two side plates; between them, on trunnions, the launch pod: a box of four
launch tubes (two by two), matte olive with stencilled markings and a red-and-white unit stripe round its back, ribs and
lifting handles, an elevating arc of teeth on its far side; the tubes' mouths rimmed in gunmetal, the four missiles' pale
grey nose cones showing in them; each mouth's blast cover flipped open on its hinge (the upper ones lying back on the
pod's top, the lower ones folded under it). On the yoke's near side the control box (a black panel with a small screen,
red and white buttons and a key switch, two handles), black cables down the yoke. The near upper tube fires (its missile
and its cover each have a bone).

The ready crate (on the `props` bone): an olive composite case (white stencils, black foam cradles inside, its lid open
behind it) with one missile lying in it and the empty cradle of the one he takes.

Painted labels on the launcher, the crate and the tablet (material `fieldgun`): 0 olive paint (the tablet: its screen),
5 gunmetal grey, 7 bright steel, 8 black (enamel, rubber, polymer), 12 red, 13 white (stencils, the missiles' noses).
On his clothes (material `uniform`): 0 olive or coyote cloth, 5 red, 6 steel, 7 a second cloth (white, black), 8 black
plastic."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp, project_to
from ugo import _blend_add
import field_gun as fg
from torsion import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD,
                     EYE_R, eye_c, smoothstep, hand_frame, HAND_S, fist_center, foot, traps, neck_prim, deltoid,
                     upper_arm, eyes_field, skull, torso_prims, TORSO, TORSO_Z, torso_bones)
from field_gun import hand, palm_pt, tunic_hull, legs_hull, boot_hull, _hand_hull, ARM_LEN, tunic_neck
from cannon import capped_cone, poly2d, _arm_coord
from musketeer import layer, _fgrad

IRIS = ((0.17, 0.1, 0.06), (0.36, 0.22, 0.12))           # steady dark-brown eyes (prep.paint_eyes)
OLIVE = (0.4, 0.42, 0.28)                                 # the task force's olive drab
OLIVE_KIT = (0.37, 0.39, 0.25)                            # the launcher's matte olive paint
COYOTE = (0.6, 0.5, 0.36)                                 # plate carrier, pouches
BLACK = (0.075, 0.075, 0.08)
RED = (0.72, 0.1, 0.07)
WHITE = (0.9, 0.88, 0.82)
GUNMETAL = (0.3, 0.32, 0.34)
STEEL_C = (0.52, 0.53, 0.55)
RED_L, METAL_L, CLOTH2_L, PLASTIC_L = 5, 6, 7, 8          # uniform labels (the cloth itself is 0)
OLIVE_L, GREY_L, STEEL_L, BLACK_L, KRED_L, KWHITE_L = 0, 5, 7, 8, 12, 13    # fieldgun labels


# ======================================================================================= stencils (a tiny stroke font)
GLYPHS = {
    "A": [((0, 0), (1, 3)), ((1, 3), (2, 0)), ((0.4, 1.2), (1.6, 1.2))],
    "C": [((2, 3), (0, 3)), ((0, 3), (0, 0)), ((0, 0), (2, 0))],
    "D": [((0, 0), (0, 3)), ((0, 3), (1.4, 3)), ((1.4, 3), (2, 2.2)), ((2, 2.2), (2, 0.8)), ((2, 0.8), (1.4, 0)), ((1.4, 0), (0, 0))],
    "E": [((2, 3), (0, 3)), ((0, 3), (0, 0)), ((0, 0), (2, 0)), ((0, 1.5), (1.5, 1.5))],
    "F": [((2, 3), (0, 3)), ((0, 3), (0, 0)), ((0, 1.5), (1.5, 1.5))],
    "G": [((2, 3), (0, 3)), ((0, 3), (0, 0)), ((0, 0), (2, 0)), ((2, 0), (2, 1.4)), ((2, 1.4), (1.1, 1.4))],
    "H": [((0, 0), (0, 3)), ((2, 0), (2, 3)), ((0, 1.5), (2, 1.5))],
    "I": [((1, 0), (1, 3))],
    "K": [((0, 0), (0, 3)), ((2, 3), (0, 1.3)), ((0.6, 1.8), (2, 0))],
    "L": [((0, 3), (0, 0)), ((0, 0), (2, 0))],
    "M": [((0, 0), (0, 3)), ((0, 3), (1, 1.5)), ((1, 1.5), (2, 3)), ((2, 3), (2, 0))],
    "N": [((0, 0), (0, 3)), ((0, 3), (2, 0)), ((2, 0), (2, 3))],
    "O": [((0, 0), (2, 0)), ((2, 0), (2, 3)), ((2, 3), (0, 3)), ((0, 3), (0, 0))],
    "P": [((0, 0), (0, 3)), ((0, 3), (2, 3)), ((2, 3), (2, 1.5)), ((2, 1.5), (0, 1.5))],
    "R": [((0, 0), (0, 3)), ((0, 3), (2, 3)), ((2, 3), (2, 1.5)), ((2, 1.5), (0, 1.5)), ((0.8, 1.5), (2, 0))],
    "S": [((2, 3), (0, 3)), ((0, 3), (0, 1.5)), ((0, 1.5), (2, 1.5)), ((2, 1.5), (2, 0)), ((2, 0), (0, 0))],
    "T": [((0, 3), (2, 3)), ((1, 3), (1, 0))],
    "U": [((0, 3), (0, 0)), ((0, 0), (2, 0)), ((2, 0), (2, 3))],
    "V": [((0, 3), (1, 0)), ((1, 0), (2, 3))],
    "X": [((0, 0), (2, 3)), ((0, 3), (2, 0))],
    "0": [((0, 0), (2, 0)), ((2, 0), (2, 3)), ((2, 3), (0, 3)), ((0, 3), (0, 0))],
    "1": [((1, 0), (1, 3)), ((1, 3), (0.4, 2.4))],
    "2": [((0, 3), (2, 3)), ((2, 3), (2, 1.5)), ((2, 1.5), (0, 1.5)), ((0, 1.5), (0, 0)), ((0, 0), (2, 0))],
    "3": [((0, 3), (2, 3)), ((2, 3), (2, 0)), ((2, 0), (0, 0)), ((0.6, 1.5), (2, 1.5))],
    "4": [((0, 3), (0, 1.2)), ((0, 1.2), (2, 1.2)), ((1.6, 3), (1.6, 0))],
    "5": [((2, 3), (0, 3)), ((0, 3), (0, 1.5)), ((0, 1.5), (2, 1.5)), ((2, 1.5), (2, 0)), ((2, 0), (0, 0))],
    "6": [((2, 3), (0, 3)), ((0, 3), (0, 0)), ((0, 0), (2, 0)), ((2, 0), (2, 1.5)), ((2, 1.5), (0, 1.5))],
    "7": [((0, 3), (2, 3)), ((2, 3), (0.6, 0))],
    "8": [((0, 0), (2, 0)), ((2, 0), (2, 3)), ((2, 3), (0, 3)), ((0, 3), (0, 0)), ((0, 1.5), (2, 1.5))],
    "9": [((2, 1.5), (0, 1.5)), ((0, 1.5), (0, 3)), ((0, 3), (2, 3)), ((2, 3), (2, 0)), ((2, 0), (0, 0))],
    "-": [((0.3, 1.5), (1.7, 1.5))],
    "/": [((0, 0), (2, 3))],
    ".": [((0.9, 0.0), (1.1, 0.0))],
}


def stencil(fd, text, origin, right, up, height, label, depth=0.012, weight=0.1, centre=True):
    """Paint `text` in stencil strokes on a surface through `origin` (the line's middle or its left end), letters `height`
    tall along `right`, standing on `up` (both unit vectors in the surface)."""
    right, up = norm(v3(right)), norm(v3(up))
    u = height / 3.0
    adv = u * 2.9
    w = max(height * weight, 0.0018)
    x0 = -adv * (len(text) - 0.3) * 0.5 if centre else 0.0
    nrm = np.cross(right, up)
    for i, ch in enumerate(text):
        for (a, b) in GLYPHS.get(ch, []):
            pa = v3(origin) + right * (x0 + adv * i + a[0] * u) + up * ((a[1] - 1.5) * u)
            pb = v3(origin) + right * (x0 + adv * i + b[0] * u) + up * ((b[1] - 1.5) * u)
            # a thin slab through the surface (a capsule flattened along the normal), so the stroke has crisp sides
            fd.paint(Func(_stroke_sd(pa, pb, w, nrm, depth), np.minimum(pa, pb) - depth - w, np.maximum(pa, pb) + depth + w), label)


def _stroke_sd(a, b, w, n, depth):
    a, b, n = a.astype(F), b.astype(F), n.astype(F)
    ab = b - a
    L2 = max(float(ab @ ab), 1e-12)
    def fn(P):
        t = np.clip(((P - a) @ ab) / F(L2), 0, 1)
        q = P - (a + t[:, None] * ab)
        dn = q @ n
        inplane = np.sqrt(np.maximum((q * q).sum(1) - dn * dn, 0))
        return np.maximum(inplane - F(w), np.abs(dn) - F(depth))
    return fn


# ======================================================================================= head
JAW = ((0.0, -0.058, 1.585), (0.146, 0.132, 0.127))
CHIN = ((0.0, -0.138, 1.5), (0.084, 0.068, 0.068))


def cheekbone(sx):
    return (sx * 0.104, -0.128, 1.642), 0.04


def jaw_corner(sx):
    return (sx * 0.124, -0.04, 1.552), 0.048


def stubble_mask(P):
    """Cheeks below the cheekbones, the jaw, chin and upper lip (design coordinates): a shadow of a close shave."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.598) + F(0.01) * smoothstep(0.05, 0.12, ax) - F(0.012) * smoothstep(0.06, 0.0, ax) * smoothstep(-0.16, -0.2, y)
    lips = np.sqrt((x / F(0.06)) ** 2 + ((y + F(0.19)) / F(0.05)) ** 2 + ((z - F(1.551)) / F(0.016)) ** 2) - F(1.0)
    back = y - F(0.04) + F(0.04) * smoothstep(1.58, 1.5, z)
    return np.maximum(np.maximum(np.maximum(z - top, F(1.43) - z), back), -lips * F(0.02))


def head(fd):
    """A calm, focused face: a square jaw and chin, cheekbones over flat cheeks, a straight nose, level dark brows set close
    over steady eyes, a firm closed mouth. (No ears: the headset's cups cover where they are.)"""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.79), (0.165, 0.175, 0.12)), 0.08, SKIN)
    fd.add(E(*JAW), 0.07, SKIN)
    fd.add(E(*CHIN), 0.05, SKIN)
    fd.add(E((0.0, -0.171, 1.49), (0.046, 0.026, 0.028)), 0.03, SKIN)                     # the chin's square point
    for sx in (-1, 1):
        c, r = cheekbone(sx)
        fd.add(S(c, r), 0.05, SKIN)
        c, r = jaw_corner(sx)
        fd.add(S(c, r), 0.05, SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.114, -0.114, 1.582)), v3((0.022, 0.016, 0.024)) * HS, R=euler(0, 0, sx * -0.5)), hr(0.02))
        pts = [hp((sx * 0.154, -0.055, 1.744)), hp((sx * 0.116, -0.133, 1.754)), hp((sx * 0.061, -0.177, 1.752)), hp((0.0, -0.187, 1.748))]
        fd.add(Chain(pts, [hr(0.012), hr(0.021), hr(0.025), hr(0.023)], k=hr(0.022)), hr(0.033), SKIN)     # brow ridge
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # level brows, thick and dark, the inner ends a touch lower (attentive, not frowning)
    tuft = lambda P: F(0.0018) * NOISE(P * F(150)) + F(0.0008) * np.sin(P[:, 0] * F(380) + P[:, 2] * F(80))
    for sx in (-1, 1):
        pts = [hp((sx * 0.021, -0.214, 1.748)), hp((sx * 0.064, -0.21, 1.76)), hp((sx * 0.108, -0.19, 1.766)), hp((sx * 0.152, -0.148, 1.76))]
        fd.add(Chain([p + v3((0, 0.005, 0)) for p in pts], [hr(0.012), hr(0.015), hr(0.013), hr(0.007)], k=hr(0.008),
                     disp=tuft, disp_amp=0.003), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.02), hr(0.023), hr(0.02), hr(0.012)], k=hr(0.01)), BROW)
    # eyes open and steady
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.0185))), (sx * 0.12, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.006)), Plane(ec + v3((0, 0, -hr(0.0205))), (sx * -0.08, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0165))), (sx * 0.12, 0.06, -1.0)), hr(0.002)), LASH)
        a = hp((sx * 0.112, -0.132, 1.684))
        fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, 0.0)), hr(0.0018), hr(0.0012)), hr(0.003))               # a crease
    # a straight nose
    fd.add(RoundCone(hp((0, -0.19, 1.728)), hp((0, -0.245, 1.632)), hr(0.016), hr(0.023)), hr(0.016), SKIN)
    fd.add(S((0, -0.248, 1.613), 0.027), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.031, -0.222, 1.602), 0.02), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.016, -0.238, 1.592)), v3((0.009, 0.011, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a firm closed mouth: upper and lower lips, the corners level
    slot = [hp(p) for p in ((-0.05, -0.176, 1.552), (-0.026, -0.197, 1.548), (0.0, -0.203, 1.548), (0.026, -0.197, 1.548), (0.05, -0.176, 1.552))]
    fd.sub(Chain(slot, [hr(0.002), hr(0.0026), hr(0.0028), hr(0.0026), hr(0.002)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0038), hr(0.004), hr(0.0038), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.046, -0.178, 1.556), (-0.022, -0.197, 1.559), (0.0, -0.202, 1.56), (0.022, -0.197, 1.559), (0.046, -0.178, 1.556)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0058), hr(0.0062), hr(0.0058), hr(0.003)], k=hr(0.005)), hr(0.006), LIP)
    lo_lip = [(-0.044, -0.176, 1.542), (-0.022, -0.194, 1.534), (0, -0.199, 1.532), (0.022, -0.194, 1.534), (0.044, -0.176, 1.542)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0074), hr(0.0084), hr(0.0074), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(RoundCone(hp((0.0, -0.215, 1.594)), hp((0.0, -0.205, 1.566)), hr(0.007), hr(0.006)), hr(0.008), SKIN)      # philtrum


def body_parts(fd):
    """The Torsion engineer's barrel-chested body (torsion.body_parts) with this head and the Field Gun's gripping hands."""
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


def face_hull():
    fd = Field("FaceHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E(*JAW), 0.07)
    fd.add(E(*CHIN), 0.05)
    for sx in (-1, 1):
        c, r = cheekbone(sx)
        fd.add(Sphere(hp(c), hr(r)), 0.05)
        c, r = jaw_corner(sx)
        fd.add(Sphere(hp(c), hr(r)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


# ======================================================================================= the helmet and headset
HELMET_OFF, HELMET_T = 0.036, 0.022       # the shell over the skull


def rim_z(Q):
    """The helmet's lower edge (design z) round his head: low over the brow, cut high over the ears, down to the nape."""
    a = np.abs(np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.02))))
    return (F(1.8) - F(0.028) * smoothstep(0.5, 1.0, a) - F(0.11) * smoothstep(1.95, 2.6, a)
            + F(0.012) * smoothstep(1.15, 1.45, a) * smoothstep(1.95, 1.65, a))


def _helmet_keep(P):
    Q = hinv(P)
    return (rim_z(Q) - Q[:, 2]) * F(HS)


def helmet_outer():
    sk = skull()
    return Func(lambda P: sk.eval(P, margin=0.1) - F(HELMET_OFF + HELMET_T / 2), HEAD_C - 0.4, HEAD_C + 0.4)


def helmet_point(a, zd, out=0.0):
    """A point on the helmet's outer surface at angle a (0 = front, + toward his left) and design height zd; its normal."""
    ho = helmet_outer()
    c = hp((0.0, 0.02, zd))
    d = v3((math.sin(a), -math.cos(a), 0.0))
    h, ok = ray_hit(ho, [c + d * 0.6], [-d], tmax=0.7, step=0.0015)
    p = h[0]
    n = _fgrad(ho.fn, p)
    return p + n * out, n


def helmet_field():
    """Olive paint (0) worn on its edges: the shell, a black rubber trim round its edge (8), a black NVG mount on the front
    (8, grey screws 5), side rails (8) with grey screws, a black strobe pouch at the back."""
    fd = Field("Helmet")
    sk = skull()
    lo, hi = HEAD_C - 0.4, HEAD_C + 0.4
    fd.add(Inter(Shell(sk, HELMET_OFF, HELMET_T, pad=0.08), Func(_helmet_keep, lo, hi), 0.008), 0.0, OLIVE_L)
    # the edge trim
    def trim(P):
        Q = hinv(P)
        return (Q[:, 2] - rim_z(Q) - F(0.016)) * F(HS)
    fd.paint(Func(trim, lo, hi), BLACK_L)
    # the NVG mount
    p, n = helmet_point(0.0, 1.835)
    up = norm(v3((0, 0, 1)) - n * float(n[2]))
    R = rot_from_axes(z_axis=n, y_axis=up)
    fd.add(RoundBox(p + n * 0.004, (0.036, 0.026, 0.01), 0.006, R=R), 0.004, BLACK_L)
    fd.sub(RoundBox(p + n * 0.014 - up * 0.004, (0.016, 0.012, 0.006), 0.003, R=R), 0.002)
    for sx in (-1, 1):
        fd.add(Sphere(p + n * 0.012 + np.cross(up, n) * (sx * 0.024) + up * 0.016, 0.005), 0.001, GREY_L)
    # side rails, a little above the rim from the temple round to behind the ear
    for sx in (-1, 1):
        pts, ns = [], []
        for a in np.linspace(0.75, 2.05, 7):
            aa = sx * a
            Qz = float(rim_z(np.array([[math.sin(aa) * 0.2, -math.cos(aa) * 0.2 + 0.02, 0.0]], F))[0])
            q, nn = helmet_point(aa, Qz + 0.032, 0.002)
            pts.append(q)
            ns.append(nn)
        fd.add(Lock(pts, [0.009] * len(pts), [0.006] * len(pts), ns, k=0.004), 0.003, BLACK_L)
        for i in (1, 3, 5):
            fd.add(Sphere(pts[i] + ns[i] * 0.006, 0.0045), 0.001, GREY_L)
    # a strobe pouch at the back, a velcro patch on top
    p, n = helmet_point(math.pi, 1.79)
    up = norm(v3((0, 0, 1)) - n * float(n[2]))
    fd.add(RoundBox(p + n * 0.012, (0.03, 0.024, 0.014), 0.008, R=rot_from_axes(z_axis=n, y_axis=up)), 0.005, BLACK_L)
    return fd


CUP_C = (0.207, 0.03, 1.662)               # (design) the ear cups' middles, his left (+x); the right mirrored
CUP_R = (0.036, 0.062, 0.072)


def headset_field():
    """Black (8) ear cups over his ears, grey (5) volume knobs and hinges, black arms up to the helmet's rails; the boom mic
    from the left cup to the corner of his mouth, a black foam ball at its end."""
    fd = Field("Headset")
    for sx in (-1, 1):
        c = hp((sx * CUP_C[0], CUP_C[1], CUP_C[2]))
        R = euler(0, 0, sx * -0.06)
        fd.add(Inter(Ellipsoid(c, v3(CUP_R) * HS, R=R), Plane(c + v3((sx * 0.024, 0, 0)), (sx, 0, 0)), 0.01), 0.0, BLACK_L)
        fd.add(Ellipsoid(c - v3((sx * 0.02, 0, 0)), v3((0.02, 0.058, 0.066)) * HS, R=R), 0.01, BLACK_L)     # the cushion
        fd.add(Cylinder(c + v3((sx * 0.026, 0.0, 0.0)), hr(0.034), 0.01, rr=0.004, R=rot_from_axes(z_axis=(1, 0, 0))), 0.004, BLACK_L)
        fd.add(Cylinder(c + v3((sx * 0.028, -0.03, -0.042)), 0.009, 0.012, rr=0.003, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, GREY_L)
        # the arm up to the rail
        top = hp((sx * 0.196, 0.035, 1.79))
        fd.add(RoundCone(c + v3((sx * 0.006, 0.0, hr(0.06))), top, 0.011, 0.009), 0.006, BLACK_L)
        fd.add(Cylinder(top, 0.012, 0.016, rr=0.004, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, GREY_L)
    # the boom mic (his left)
    pts = [hp(p) for p in ((0.22, -0.02, 1.63), (0.198, -0.1, 1.598), (0.15, -0.178, 1.568), (0.096, -0.218, 1.556))]
    fd.add(Chain(pts, [0.0065, 0.006, 0.0055, 0.005], k=0.004), 0.003, BLACK_L)
    fd.add(Sphere(hp((0.08, -0.226, 1.554)), hr(0.017)), 0.004, BLACK_L)
    # the chin strap: from the rails in front of and behind the cups down to a cup under his chin
    hull = face_hull()
    off = Field("StrapHull")
    off.add(Func(lambda P: hull.eval(P, margin=0.05) - F(0.009), HEAD_C - 0.45, HEAD_C + 0.3), 0.0)
    for sx in (-1, 1):
        for guide in (((0.16, -0.052, 1.76), (0.158, -0.068, 1.66), (0.14, -0.07, 1.56), (0.1, -0.086, 1.48), (0.04, -0.112, 1.44)),
                      ((0.165, 0.11, 1.72), (0.16, 0.06, 1.6), (0.14, -0.02, 1.52), (0.1, -0.07, 1.47))):
            pts = project_to(off, np.array([hp((sx * x, y, z)) for x, y, z in guide]), iters=4)
            ns = [_fgrad(off.eval, p) for p in pts]
            fd.add(Lock(list(pts), [0.0085] * len(pts), [0.0028] * len(pts), ns, k=0.003), 0.002, BLACK_L)
    fd.add(Ellipsoid(hp((0.0, -0.125, 1.445)), v3((0.04, 0.03, 0.016)) * HS, R=euler(0.5, 0, 0)), 0.006, BLACK_L)
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


# ======================================================================================= the combat shirt
SHIRT_OFF, SHIRT_T = 0.022, 0.016
SHIRT_FACE = SHIRT_OFF + SHIRT_T / 2
SHIRT_HEM = 0.9
ROLL_S = ARM_LEN - 0.155                   # the rolled sleeve's end (along the arm from the shoulder)


_SH = []


def shirt_hull():
    """The Field Gun's tunic hull (field_gun.tunic_hull) with his pectorals: the shirt and the carrier lie over them."""
    if _SH:
        return _SH[0]
    b = tunic_hull()
    tp = torso_prims()
    for i in (2, 3):
        b.add(tp[i][0], tp[i][1])
    _SH.append(b)
    return b


def _sleeve_cut(P):
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2 = _arm_coord(P, side)
        near = (d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3))
        out = np.maximum(out, np.where(near, s - F(ROLL_S), F(-1.0)))
    return out


def _roll_band(P):
    out = np.full(len(P), F(1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2 = _arm_coord(P, side)
        near = (d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3))
        out = np.minimum(out, np.where(near, np.abs(s - F(ROLL_S - 0.026)) - F(0.03), F(1.0)))
    return out


def shirt_keep(P):
    return np.maximum(np.maximum(F(SHIRT_HEM) - P[:, 2], tunic_neck(P) + F(0.012)), _sleeve_cut(P))


def shirt_outer():
    b = shirt_hull()
    return Func(lambda P: b.eval(P, margin=0.1) - F(SHIRT_FACE), (-1, -0.6, 0.5), (1, 0.6, 1.7))


def upper_arm_spot(side, t, out=0.0):
    """A point on the sleeve's outer face at fraction t down the upper arm (on its outer side), and the outward normal."""
    sx = -1 if side == "R" else 1
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    c = lerp(sh, el, t)
    ax = norm(el - sh)
    d = norm(v3((sx, -0.25, 0.0)) - ax * float(v3((sx, -0.25, 0.0)) @ ax))
    so = shirt_outer()
    h, ok = ray_hit(so, [c + d * 0.4], [-d], tmax=0.5)
    p = h[0] if ok[0] else c + d * 0.12
    n = _fgrad(so.fn, p)
    return p + n * out, n, ax


def shirt_field():
    """Olive cloth (0): the shirt tucked in at his waist, a small stand collar, the sleeves rolled up to mid-forearm (a
    thick roll at their ends), the unit patch on his left sleeve: a red shield (5) with a white chevron (7)."""
    fd = Field("Shirt")
    base = shirt_hull()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        return F(0.0016) * np.sin(a * F(7) + F(0.9) * NOISE(P * F(3))) + F(0.0011) * NOISE(P * F(20))
    lo, hi = (-1, -0.6, 0.5), (1, 0.6, 1.7)
    fd.add(Inter(Shell(base, SHIRT_OFF, SHIRT_T, pad=0.12, disp=folds, disp_amp=0.003), Func(shirt_keep, lo, hi), 0.004), 0.0)
    # the rolled cuffs: a thicker band at each sleeve's end
    roll = lambda P: F(0.0025) * np.sin(_arm_coord(P, "R")[0] * F(180)) + F(0.001) * NOISE(P * F(25))
    fd.add(Inter(Inter(Shell(base, SHIRT_OFF + 0.012, 0.026, pad=0.12, disp=roll, disp_amp=0.003), Func(_roll_band, lo, hi), 0.006),
                 Func(lambda P: P[:, 2] - F(1.2), lo, hi), 0.0), 0.006)
    # the stand collar
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    def band(P):
        front = np.clip(-(P[:, 1] - F(0.03)) / F(0.1), 0, 1)
        return np.maximum(F(1.39) - P[:, 2], P[:, 2] - F(1.475) + F(0.03) * front)
    fd.add(Inter(Shell(nk, 0.02, 0.014, pad=0.08), Func(band, (-0.3, -0.3, 1.3), (0.3, 0.3, 1.55)), 0.004), 0.004)
    # the unit patch on the left sleeve
    p, n, ax = upper_arm_spot("L", 0.3)
    side = norm(np.cross(n, ax))
    R = np.stack([side, -ax, n], axis=1)
    fd.add(RoundBox(p + n * 0.001, (0.036, 0.042, 0.004), 0.003, R=R), 0.003, RED_L)
    fd.paint(RoundBox(p, (0.04, 0.047, 0.03), 0.01, R=R), RED_L)
    tip = p + ax * 0.014                                                              # the white chevron
    for s in (-1, 1):
        fd.paint(RoundCone(p + side * (s * 0.025) - ax * 0.008, tip, 0.0072, 0.0072), CLOTH2_L)
    return fd


# ======================================================================================= trousers, belt, boots, gloves
TROUSER_TOP, TROUSER_BOT = 0.98, 0.3
BELT_Z = 0.915


def trousers_field():
    """Olive cloth (0): straight in the leg, bloused over the boots' tops, cargo pockets on the thighs; black (7) knee pads;
    the black rigger's belt (7) with its steel buckle (6)."""
    fd = Field("Trousers")
    hull = legs_hull()
    lo, hi = v3((-0.5, -0.4, 0.2)), v3((0.5, 0.45, 1.1))
    def off(P):
        z = P[:, 2]
        return F(0.014) + F(0.014) * smoothstep(0.42, 0.56, z) + F(0.012) * smoothstep(0.42, 0.34, z)
    def fn(P):
        d = hull.eval(P, margin=0.1)
        return np.abs(d - off(P)) - F(0.01)
    folds = lambda P: (F(0.0035) * np.sin(np.arctan2(P[:, 1] - F(0.03), np.abs(P[:, 0]) - F(0.17)) * F(6) + P[:, 2] * F(26)
                                          + F(0.8) * NOISE(P * F(4))) * smoothstep(0.38, 0.5, P[:, 2]) + F(0.0012) * NOISE(P * F(25)))
    fd.add(Inter(Func(fn, lo, hi, disp=folds, disp_amp=0.005),
                 Func(lambda P: np.maximum(P[:, 2] - F(TROUSER_TOP), F(TROUSER_BOT) - P[:, 2]), lo, hi), 0.004), 0.0)
    outer = Func(lambda P: hull.eval(P, margin=0.1) - off(P) - F(0.01), lo, hi)
    # cargo pockets on the outer thighs, a flap on each
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        hip, kn = J["hip_" + side], J["knee_" + side]
        c0 = lerp(hip, kn, 0.5)
        d = norm(v3((sx, -0.35, 0.0)))
        h, ok = ray_hit(outer, [c0 + d * 0.4], [-d], tmax=0.5)
        if not ok[0]:
            continue
        p = h[0]
        n = _fgrad(outer.fn, p)
        up = norm(hip - kn)
        up = norm(up - n * float(up @ n))
        R = np.stack([np.cross(up, n), up, n], axis=1)
        fd.add(RoundBox(p + n * 0.006, (0.055, 0.065, 0.012), 0.008, R=R), 0.008)
        fd.add(RoundBox(p + n * 0.014 + up * 0.05, (0.06, 0.022, 0.008), 0.005, R=R), 0.004)
    # knee pads
    for side in ("R", "L"):
        kn = J["knee_" + side]
        d = v3((0.0, -1.0, 0.05))
        h, ok = ray_hit(outer, [kn + d * 0.4], [-d], tmax=0.5)
        if not ok[0]:
            continue
        p = h[0]
        n = _fgrad(outer.fn, p)
        R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
        fd.add(Inter(Ellipsoid(p - n * 0.07, (0.075, 0.09, 0.095), R=R), Plane(p - n * 0.004, -n), 0.008), 0.008, CLOTH2_L)
        # its straps round the leg, above and below the knee
        for zk in (kn[2] + 0.075, kn[2] - 0.07):
            def strap(P, zk=zk, kn=kn):
                rho = np.sqrt((P[:, 0] - F(kn[0])) ** 2 + (P[:, 1] - F(kn[1])) ** 2)
                return np.maximum(np.abs(P[:, 2] - F(zk)) - F(0.011), rho - F(0.16))
            fd.add(Inter(Func(lambda P: np.abs(hull.eval(P, margin=0.1) - off(P) - F(0.013)) - F(0.004), lo, hi),
                         Func(strap, lo, hi), 0.002), 0.004, CLOTH2_L)
    # the belt and its buckle
    bh = Field("BeltHull")
    tb = shirt_hull()
    bh.add(Func(lambda P: tb.eval(P, margin=0.12) - F(SHIRT_FACE), (-0.5, -0.45, 0.8), (0.5, 0.45, 1.05)), 0.0)
    fd.add(Inter(Shell(bh, 0.012, 0.014, pad=0.06), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(0.026), (-0.6, -0.5, 0.8), (0.6, 0.5, 1.1)), 0.004), 0.004, CLOTH2_L)
    h, ok = ray_hit(bh, [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    c = h[0] if ok[0] else v3((0, -0.3, BELT_Z))
    R = rot_from_axes(z_axis=(0, -1, 0), y_axis=(0, 0, 1))
    fd.add(RoundBox(c + v3((0, -0.022, 0)), (0.036, 0.03, 0.008), 0.005, R=R), 0.003, METAL_L)
    fd.sub(RoundBox(c + v3((0, -0.03, 0)), (0.02, 0.017, 0.006), 0.003, R=R), 0.002)
    return fd


def boots_field():
    """Black leather combat boots (0) to above the ankle, laced up the front, thick black rubber soles (5)."""
    fd = Field("Boots")
    crease = lambda P: F(0.0014) * NOISE(P * F(26))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an, kn = J["ankle_" + side], J["knee_" + side]
        ft = boot_hull(side)
        top = lambda P, kn=kn: P[:, 2] - (F(0.33) + F(0.02) * np.clip(-(P[:, 1] - F(kn[1])) / F(0.09), -1, 1))
        fd.add(Inter(Shell(ft, 0.018, 0.015, pad=0.07, disp=crease, disp_amp=0.002),
                     Func(top, an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.6))), 0.004), 0.0)
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        rgt = Rz @ v3((1, 0, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.096)), (0.086, 0.17, 0.02), 0.012, R=Rz), 0.006, 5)
        fd.add(RoundBox(an + fwd * -0.035 + v3((0, 0, -0.082)), (0.064, 0.054, 0.03), 0.012, R=Rz), 0.008, 5)
        for k in range(5):                                                            # the laces up the front
            c = an + fwd * (0.07 - 0.008 * k) + v3((0, 0, -0.035 + 0.05 * k))
            if k > 2:
                c = an + fwd * (0.06 - 0.004 * k) + v3((0, 0, -0.035 + 0.05 * k))
            fd.add(RoundCone(c - rgt * 0.024, c + rgt * 0.024, 0.0045, 0.0045), 0.003)
    return fd


def gloves_field():
    """Black gloves (0): over the hands, a short cuff at the wrist, padded knuckles."""
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
        for o in (0.044, 0.0148, -0.0148, -0.044):                                    # knuckle pads
            fd.add(Ellipsoid(w + f * 0.142 * HAND_S + t * o * HAND_S - n * 0.02, (0.016, 0.01, 0.014), R=np.stack([t, -n, f], 1)), 0.006)
    return fd


# ======================================================================================= the plate carrier
PC_IN = SHIRT_FACE + SHIRT_T / 2 + 0.004       # its inner face over the shirt
PLATE_T = 0.044
PLATE_OFF = PC_IN + PLATE_T / 2
CB_T = 0.022
CB_OFF = PC_IN + CB_T / 2
STRAP_T = 0.026
TAB_Z = 1.165                                  # the tablet's middle on his chest (stowed)


def _front_top(x):
    return F(1.38) - F(0.05) * np.exp(-(x / F(0.08)) ** 2)


def _plate_region(P):
    """< 0 on the plate bags: the front (to his collarbones, scooped at the neck) and the back (higher)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    w = np.abs(x) - F(0.205)
    front = np.maximum(np.maximum(w, y - F(0.02)), np.maximum(F(1.0) - z, z - _front_top(x)))
    back = np.maximum(np.maximum(w, F(0.07) - y), np.maximum(F(1.0) - z, z - F(1.42) + F(0.04) * smoothstep(0.12, 0.2, np.abs(x))))
    return np.minimum(front, back)


def _cb_region(P):
    return np.maximum(np.maximum(F(0.995) - P[:, 2], P[:, 2] - F(1.16)), np.abs(P[:, 0]) - F(0.36))


def _strap_region(P):
    ax = np.abs(P[:, 0])
    return np.maximum(np.maximum(F(0.085) - ax, ax - F(0.17)), F(1.3) - P[:, 2])


def carrier_outer():
    b = shirt_hull()
    return Func(lambda P: b.eval(P, margin=0.12) - F(PLATE_OFF + PLATE_T / 2), (-0.8, -0.6, 0.8), (0.8, 0.6, 1.7))


def _surface_frame(fn_func, origin, d):
    h, ok = ray_hit(fn_func, [origin], [d], tmax=0.9)
    p = h[0] if ok[0] else origin
    n = _fgrad(fn_func.fn, p)
    return p, n


def tablet_mount():
    """The tablet's mount on the carrier's front: (its middle, its normal) on the plate bag's face."""
    co = carrier_outer()
    return _surface_frame(co, v3((0.0, -0.8, TAB_Z)), v3((0, 1, 0)))


def carrier_field():
    """Coyote cloth (0): the front and back plate bags with rows of webbing, a cummerbund round his waist, padded shoulder
    straps, two magazine pouches on each side (black magazine baseplates showing, 8), a velcro panel on his chest with a red
    (5) and white (7) unit patch, the tablet's black mount (8), a radio pouch on his back with a black whip antenna (8),
    steel D-rings (6)."""
    fd = Field("Carrier")
    base = shirt_hull()
    lo, hi = (-0.8, -0.6, 0.8), (0.8, 0.6, 1.7)
    cloth = lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.0006) * NOISE(P * F(90))
    fd.add(Inter(Shell(base, PLATE_OFF, PLATE_T, pad=0.14, disp=cloth, disp_amp=0.002), Func(_plate_region, lo, hi), 0.012), 0.0)
    fd.add(Inter(Shell(base, CB_OFF, CB_T, pad=0.14, disp=cloth, disp_amp=0.002), Func(_cb_region, lo, hi), 0.006), 0.008)
    fd.add(Inter(Shell(base, PC_IN + STRAP_T / 2, STRAP_T, pad=0.14), Func(_strap_region, lo, hi), 0.01), 0.01)
    # rows of webbing across the plate bags (grooves between the strips)
    out = PLATE_OFF + PLATE_T / 2
    for zk in (1.04, 1.085):
        def groove(P, zk=zk):
            return np.maximum(np.abs(P[:, 2] - F(zk)) - F(0.0035), np.abs(np.abs(P[:, 0]) - F(0.11)) - F(0.085))
        fd.sub(Inter(Shell(base, out, 0.012, pad=0.14), Func(groove, lo, hi), 0.0), 0.002)
    for zk in (1.08, 1.13, 1.18, 1.23, 1.28):
        def groove_b(P, zk=zk):
            return np.maximum(np.maximum(np.abs(P[:, 2] - F(zk)) - F(0.0035), np.abs(P[:, 0]) - F(0.18)), F(0.07) - P[:, 1])
        fd.sub(Inter(Shell(base, out, 0.012, pad=0.14), Func(groove_b, lo, hi), 0.0), 0.002)
    co = carrier_outer()
    # the velcro panel and its patches, high on his chest
    p, n = _surface_frame(co, v3((0.0, -0.8, 1.285)), v3((0, 1, 0)))
    up = norm(v3((0, 0, 1)) - n * float(n[2]))
    R = rot_from_axes(z_axis=n, y_axis=up)
    side = np.cross(up, n)
    fd.add(RoundBox(p + n * 0.002, (0.15, 0.026, 0.006), 0.004, R=R), 0.004)
    pc = p + n * 0.008 + side * 0.08                                          # (his left)
    fd.add(RoundBox(pc, (0.032, 0.022, 0.003), 0.002, R=R), 0.002, RED_L)
    fd.paint(RoundBox(pc, (0.034, 0.024, 0.012), 0.002, R=R), RED_L)
    fd.paint(RoundBox(pc, (0.034, 0.0055, 0.014), 0.001, R=R), CLOTH2_L)
    stencil(fd, "TF-7", p + n * 0.008 - side * 0.06, side, up, 0.02, CLOTH2_L, depth=0.008, weight=0.11)
    # the tablet's mount: a black plate with two clips
    pm, nm = tablet_mount()
    upm = norm(v3((0, 0, 1)) - nm * float(nm[2]))
    Rm = rot_from_axes(z_axis=nm, y_axis=upm)
    fd.add(RoundBox(pm + nm * 0.004, (0.09, 0.06, 0.006), 0.004, R=Rm), 0.004, PLASTIC_L)
    for sx in (-1, 1):
        fd.add(RoundBox(pm + nm * 0.01 + np.cross(upm, nm) * (sx * 0.075) - upm * 0.06, (0.012, 0.012, 0.01), 0.004, R=Rm), 0.003, PLASTIC_L)
    # magazine pouches on the cummerbund's front corners
    for sx in (-1, 1):
        for k, x in enumerate((0.215, 0.29)):
            d = norm(v3((sx * (0.45 + 0.6 * k), -1.0, 0.0)))
            p, n = _surface_frame(co, v3((sx * x, 0.0, 1.06)) - d * 0.8, d)
            n = norm(v3((n[0], n[1], 0.0)))
            up = v3((0, 0, 1))
            R = np.stack([np.cross(up, n), up, n], axis=1)
            c = p + n * 0.026
            fd.add(RoundBox(c, (0.034, 0.055, 0.024), 0.01, R=R, disp=cloth, disp_amp=0.001), 0.006)
            fd.add(RoundBox(c + up * 0.06 + n * 0.0, (0.026, 0.012, 0.016), 0.005, R=R), 0.004, PLASTIC_L)     # the mag's baseplate
            fd.add(RoundBox(c + n * 0.024 + up * 0.03, (0.006, 0.02, 0.004), 0.002, R=R), 0.002, PLASTIC_L)    # the bungee tab
    # D-rings on the shoulder straps
    for sx in (-1, 1):
        p, n = _surface_frame(co, v3((sx * 0.13, -0.8, 1.33)), v3((0, 1, 0)))
        fd.add(Torus(p + n * 0.006, 0.012, 0.0028, R=rot_from_axes(z_axis=n)), 0.002, METAL_L)
    # the radio pouch on his back (his left), its antenna
    p, n = _surface_frame(co, v3((0.11, 0.8, 1.22)), v3((0, -1, 0)))
    R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
    rc = p + n * 0.035
    fd.add(RoundBox(rc, (0.045, 0.075, 0.032), 0.012, R=R, disp=cloth, disp_amp=0.001), 0.008)
    a0 = rc + v3((0.025, 0.0, 0.075))
    fd.add(Cylinder(a0 + v3((0, 0, 0.01)), 0.012, 0.03, rr=0.004), 0.003, PLASTIC_L)
    fd.add(Chain([a0 + v3((0, 0, 0.02)), a0 + v3((0.03, 0.02, 0.18)), a0 + v3((0.07, 0.045, 0.36))], [0.0075, 0.0055, 0.004], k=0.003), 0.002, PLASTIC_L)
    return fd


# ======================================================================================= the fire-control tablet
TB_HALF = (0.122, 0.084, 0.014)            # across, up its face, its thickness
TB_HANDLE = 0.152                          # its grip bars' axes, out from its middle


def tablet_frame():
    """The tablet's middle C (rest: clipped to his chest), across (X), up its face (U), out of its screen (N)."""
    p, n = tablet_mount()
    N = norm(v3((0.0, -1.0, 0.26)))                     # (its screen faces out and a little up)
    X = v3((1.0, 0.0, 0.0))
    U = norm(np.cross(N, X))
    if U[2] < 0:
        U = -U
    return p + N * (TB_HALF[2] + 0.016) + U * 0.004, X, U, N


def tb_pt(u, v, w=0.0):
    C, X, U, N = tablet_frame()
    return C + X * u + U * v + N * w


def tablet_field():
    """The fire-control unit: a black rugged case (8) with grey rubber corners (5), its screen (0: a dark teal display)
    showing a white grid and tracks (13) and a red target mark (12), a row of grey keys; a grip bar down each side (grey
    5, black rubber grips 8); an antenna stub on its top corner."""
    fd = Field("Tablet")
    C, X, U, N = tablet_frame()
    R = np.stack([X, U, N], axis=1)
    hx, hu, hn = TB_HALF
    fd.add(RoundBox(C, (hx, hu, hn), 0.01, R=R), 0.0, BLACK_L)
    for su in (-1, 1):
        for sv in (-1, 1):
            fd.add(RoundBox(tb_pt(su * (hx - 0.012), sv * (hu - 0.012)), (0.02, 0.02, hn + 0.004), 0.008, R=R), 0.004, GREY_L)
    # the screen, a shallow recess in the face
    sc = tb_pt(-0.012, 0.008, hn)
    fd.sub(RoundBox(sc, (0.084, 0.062, 0.003), 0.004, R=R), 0.002)
    def screen(P):
        q = P - sc.astype(F)
        u, v, w = q @ X.astype(F), q @ U.astype(F), q @ N.astype(F)
        return np.maximum(np.maximum(np.abs(u) - F(0.082), np.abs(v) - F(0.06)), np.abs(w) - F(0.01))
    fd.paint(Func(screen, sc - 0.12, sc + 0.12), OLIVE_L)
    for k in range(-3, 4):                                                    # the grid
        a, b = sc + X * (0.024 * k) - U * 0.058 - N * 0.003, sc + X * (0.024 * k) + U * 0.058 - N * 0.003
        fd.paint(RoundCone(a, b, 0.0014, 0.0014), KWHITE_L)
    for k in range(-2, 3):
        a, b = sc + U * (0.024 * k) - X * 0.08 - N * 0.003, sc + U * (0.024 * k) + X * 0.08 - N * 0.003
        fd.paint(RoundCone(a, b, 0.0014, 0.0014), KWHITE_L)
    trk = [sc + X * -0.07 + U * -0.045, sc + X * -0.03 + U * -0.012, sc + X * 0.01 + U * 0.004, sc + X * 0.05 + U * 0.03]
    fd.paint(Chain([t - N * 0.003 for t in trk], [0.0028] * 4, k=0.002), KWHITE_L)
    fd.paint(Torus(sc + X * 0.05 + U * 0.03, 0.011, 0.0032, R=R), KRED_L)
    fd.paint(Sphere(sc + X * 0.05 + U * 0.03, 0.0045), KRED_L)
    for k in range(4):                                                        # keys under the screen
        fd.add(RoundBox(tb_pt(-0.06 + 0.032 * k, -hu + 0.012, hn), (0.011, 0.006, 0.004), 0.003, R=R), 0.002, GREY_L)
    # the fire key, by his right thumb when he holds it (the tablet's +X side: his right as he looks at the screen)
    fd.add(Cylinder(tb_pt(0.098, 0.02, hn + 0.002), 0.011, 0.008, rr=0.003, R=rot_from_axes(z_axis=N)), 0.002, KRED_L)
    # the grip bars
    for su in (-1, 1):
        a, b = tb_pt(su * TB_HANDLE, -hu + 0.012), tb_pt(su * TB_HANDLE, hu - 0.012)
        fd.add(RoundCone(a, b, 0.012, 0.012), 0.004, BLACK_L)
        for v in (-hu + 0.012, hu - 0.012):
            fd.add(RoundCone(tb_pt(su * (hx - 0.004), v), tb_pt(su * TB_HANDLE, v), 0.009, 0.009), 0.004, GREY_L)
    fd.add(RoundCone(tb_pt(hx - 0.018, hu - 0.004, -0.002), tb_pt(hx - 0.02, hu + 0.06, -0.004), 0.008, 0.0055), 0.003, BLACK_L)
    return fd


# ======================================================================================= the launcher (layout)
MX = 0.8                    # the pod's middle line (x); it shoots toward -Y
TRUN = v3((MX, -0.45, 1.05))  # the trunnions (the pod elevates about them)
ELEV0 = math.radians(10.0)   # the pod's elevation in the sculpt (rest)
GD = v3((0.0, -math.cos(ELEV0), math.sin(ELEV0)))      # along the tubes, toward their mouths
GU = v3((0.0, math.sin(ELEV0), math.cos(ELEV0)))       # up, across the tubes
GX_ = v3((1.0, 0.0, 0.0))
POD_HW, POD_HH = 0.24, 0.225     # the pod's half width and half height
POD_F, POD_B = 0.38, -0.28       # its front and back faces (along the tubes from the trunnions)
TUBES = ((-0.118, 0.112), (0.118, 0.112), (-0.118, -0.112), (0.118, -0.112))    # (u across, v up) of the four tubes
FIRE = 0                         # the near upper tube fires (its missile and its cover are bones)
TUBE_R = 0.08
MSL_R, MSL_L = 0.064, 0.56       # a missile's radius and length
NOSE_L = 0.16
MSL_TIP = POD_B + 0.06 + MSL_L   # the seated missile's nose tip (along the tubes): its tail a few fingers inside the back
YOKE_X = POD_HW + 0.058          # the yoke plates' middles (x from MX)
BASE_Y = TRUN[1] + 0.02          # the pedestal's middle (y)
COVER_OPEN = math.radians(262.0) # the covers' swing from shut (upper ones up and back onto the pod's top)
HINGE_V = POD_HH + 0.017         # the covers' hinges (up from the pod's axis; the lower ones mirrored)


def bpt(s, u=0.0, v=0.0):
    """A point in the pod's frame (rest): s along the tubes from the trunnions, u across (+X), v up."""
    return TRUN + GD * s + GX_ * u + GU * v


def tube_c(i, s):
    u, v = TUBES[i]
    return bpt(s, u, v)


def _rpod():
    return np.stack([GX_, GD, GU], axis=1)


def cover_rot(i, ang):
    """The rotation (about the hinge's axis, X) swinging tube i's cover open by `ang` from shut."""
    sgn = 1.0 if TUBES[i][1] > 0 else -1.0
    # an upper cover's middle swings from below its hinge (shut) to in front of it (90 degrees), above it and back over
    # the pod's top; a lower one mirrored, under the pod
    return axis_angle(GX_, -sgn * ang)


def hinge_pt(i):
    u, v = TUBES[i]
    sgn = 1.0 if v > 0 else -1.0
    return bpt(POD_F + 0.004, u, sgn * HINGE_V)


# ======================================================================================= the missile
def missile_into(fd, tail, A, k=0.0, label_body=OLIVE_L):
    """A missile from its tail (nozzle) along A: an olive body (0) with a white band (13), black (8) folded fins at its
    tail and a black nozzle, a black band at the nose's foot, the pale nose cone (13) with a black tip."""
    A = norm(A)
    R = rot_from_axes(z_axis=A)
    nb = tail + A * (MSL_L - NOSE_L)
    fd.add(capped_cone(tail + A * 0.01, nb, MSL_R, MSL_R, rr=0.006), k, label_body)
    fd.add(Cylinder(tail + A * 0.24, MSL_R + 0.0015, 0.03, rr=0.003, R=R), 0.002, KWHITE_L)
    fd.add(Cylinder(nb - A * 0.008, MSL_R + 0.001, 0.018, rr=0.003, R=R), 0.002, BLACK_L)
    fd.add(RoundCone(nb, tail + A * (MSL_L - 0.006), MSL_R - 0.002, 0.008), 0.01, KWHITE_L)
    fd.paint(Sphere(tail + A * MSL_L, 0.02), BLACK_L)
    fd.sub(Cylinder(tail, MSL_R - 0.016, 0.03, R=R), 0.004)                                  # the nozzle's mouth
    fd.paint(Cylinder(tail, MSL_R - 0.01, 0.05, R=R), BLACK_L)
    side = norm(np.cross(A, v3((0, 0, 1)) if abs(A[2]) < 0.9 else v3((1, 0, 0))))
    up = np.cross(side, A)
    for k2 in range(4):
        a = math.pi / 4 + k2 * math.pi / 2
        d = side * math.cos(a) + up * math.sin(a)
        Rf = np.stack([np.cross(A, d), d, A], axis=1)
        fd.add(RoundBox(tail + A * 0.07 + d * (MSL_R + 0.002), (0.004, 0.006, 0.05), 0.002, R=Rf), 0.003, BLACK_L)


def seated_tail(i):
    return tube_c(i, MSL_TIP - MSL_L)


def missile_field():
    """The missile in the firing tube (rest: seated, its tail just inside the pod's back, its nose inside the mouth)."""
    fd = Field("Missile")
    missile_into(fd, seated_tail(FIRE), GD)
    return fd


# ======================================================================================= the launch pod
def _pod_box(P, grow=0.0, s0=POD_B, s1=POD_F):
    q = (P - TRUN.astype(F)) @ _rpod().astype(F)
    u, s, v = q[:, 0], q[:, 1], q[:, 2]
    r = F(0.03)
    qx = np.abs(u) - F(POD_HW + grow) + r
    qy = np.abs(s - F((s0 + s1) / 2)) - F((s1 - s0) / 2) + r
    qz = np.abs(v) - F(POD_HH + grow) + r
    qq = np.stack([qx, qy, qz], 1)
    return np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0) - r


def _pod_local(P):
    q = (P - TRUN.astype(F)) @ _rpod().astype(F)
    return q[:, 0], q[:, 1], q[:, 2]


def cover_into(fd, i, ang, k=0.0):
    """Tube i's blast cover, swung open by `ang` about its hinge: an olive disc (0) with a black rubber seal (8), a grip tab
    and the hinge's knuckle (grey 5)."""
    u, v = TUBES[i]
    sgn = 1.0 if v > 0 else -1.0
    H = hinge_pt(i)
    R = cover_rot(i, ang)
    c_shut = tube_c(i, POD_F + 0.01)
    rel = lambda p: H + R @ (v3(p) - H)
    Rc = R @ rot_from_axes(z_axis=GD)
    c = rel(c_shut)
    nrm = R @ GD
    fd.add(Cylinder(c, TUBE_R + 0.018, 0.014, rr=0.005, R=Rc), k, OLIVE_L)
    fd.add(Torus(c - nrm * 0.008, TUBE_R + 0.004, 0.006, R=Rc), 0.003, BLACK_L)
    fd.add(Cylinder(c + nrm * 0.008, TUBE_R - 0.02, 0.006, rr=0.002, R=Rc), 0.003, OLIVE_L)              # a raised boss
    tab = rel(tube_c(i, POD_F + 0.016) - GU * sgn * (TUBE_R + 0.022))
    fd.add(RoundBox(tab, (0.022, 0.006, 0.012), 0.004, R=Rc), 0.003, BLACK_L)
    arm0 = rel(c_shut + GU * sgn * (TUBE_R * 0.6))
    fd.add(RoundCone(arm0, H, 0.009, 0.009), 0.004, GREY_L)
    fd.add(Cylinder(H, 0.011, 0.05, rr=0.003, R=rot_from_axes(z_axis=GX_)), 0.003, GREY_L)


def pod_bounds(m=0.06, cover=0.0):
    pts = [bpt(s, u, v) for s in (POD_B, POD_F) for u in (-POD_HW, POD_HW) for v in (-POD_HH - cover, POD_HH + cover)]
    return np.min(pts, 0) - m, np.max(pts, 0) + m


def pod_field():
    """The launch pod (olive paint 0): a box with rounded edges, ribs round it, lifting handles (black 8), the four tubes'
    mouths with gunmetal rims (5) and their black bores (8), the three seated missiles' noses (13), three blast covers
    flipped open (the fourth is its own part), the back face with the tubes' rear rings and the missiles' nozzles, a red
    (12) and white (13) unit stripe round its back end, white stencils on its top, black ones on its side; the trunnions'
    hubs (grey); the toothed elevating arc on its far side (grey)."""
    fd = Field("Pod")
    lo, hi = pod_bounds(0.05)
    paintn = lambda P: F(0.0006) * NOISE(P * F(60))
    fd.add(Func(_pod_box, lo, hi, disp=paintn, disp_amp=0.001), 0.0, OLIVE_L)
    # ribs round the box
    for s0 in (-0.235, 0.04, 0.33):
        fd.add(Func(lambda P, s0=s0: _pod_box(P, 0.008, s0 - 0.014, s0 + 0.014), lo, hi), 0.004, OLIVE_L)
    # the bores, through the box (the missiles fill them)
    for i in range(4):
        fd.sub(Cylinder(tube_c(i, 0.05), TUBE_R, 1.2, R=rot_from_axes(z_axis=GD)), 0.004)
        fd.paint(Cylinder(tube_c(i, 0.05), TUBE_R + 0.003, 1.21, R=rot_from_axes(z_axis=GD)), BLACK_L)
        for s in (POD_F + 0.006, POD_B - 0.006):
            fd.add(Torus(tube_c(i, s), TUBE_R + 0.011, 0.011, R=rot_from_axes(z_axis=GD)), 0.004, GREY_L)
    # the three other missiles, seated
    for i in range(4):
        if i != FIRE:
            missile_into(fd, seated_tail(i), GD)
    # the three other covers, flipped open
    for i in range(4):
        if i != FIRE:
            cover_into(fd, i, COVER_OPEN)
    # lifting handles on its sides, a grab bar across its back
    for su in (-1, 1):
        for s in (-0.12, 0.2):
            a, b = bpt(s - 0.06, su * (POD_HW + 0.004), 0.06), bpt(s + 0.06, su * (POD_HW + 0.004), 0.06)
            fd.add(Chain([a, a + GX_ * (su * 0.035), b + GX_ * (su * 0.035), b], [0.009] * 4, k=0.004), 0.004, BLACK_L)
    a, b = bpt(POD_B - 0.004, -0.17, 0.0), bpt(POD_B - 0.004, 0.17, 0.0)
    fd.add(Chain([a, a - GD * 0.04, b - GD * 0.04, b], [0.01] * 4, k=0.004), 0.004, BLACK_L)
    # the trunnions' hubs
    for su in (-1, 1):
        fd.add(Cylinder(TRUN + GX_ * (su * (POD_HW + 0.02)), 0.062, 0.05, rr=0.01, R=rot_from_axes(z_axis=GX_)), 0.008, GREY_L)
    # the elevating arc on the far side (+X), below the trunnion: a toothed sector riding the pod
    xa = MX + POD_HW + 0.022
    def arc(P):
        q = P - TRUN.astype(F)
        r = np.sqrt(q[:, 1] ** 2 + q[:, 2] ** 2)
        # angle from the pod's "down" (-GU) in the y-z plane
        ang = np.arctan2(q @ GD.astype(F), q @ (-GU).astype(F))
        d_r = np.abs(r - F(0.15)) - F(0.05)
        d_a = np.abs(ang) - F(0.75)
        d_x = np.abs(P[:, 0] - F(xa)) - F(0.008)
        return np.maximum(np.maximum(d_r, d_a * F(0.15)), d_x)
    fd.add(Func(arc, (xa - 0.03, TRUN[1] - 0.3, TRUN[2] - 0.3), (xa + 0.03, TRUN[1] + 0.3, TRUN[2] + 0.3)), 0.004, GREY_L)
    for k in range(-9, 10):
        a = k * 0.075
        d = -GU * math.cos(a) + GD * math.sin(a)
        fd.add(RoundBox(TRUN + d * 0.205 + GX_ * (xa - MX), (0.008, 0.008, 0.012), 0.003,
                        R=np.stack([GX_, np.cross(d, GX_), d], axis=1)), 0.002, GREY_L)
    # the unit stripe round its back end: white, red, white
    def band(s0, s1):
        def fn(P):
            u, s, v = _pod_local(P)
            return np.maximum(np.maximum(F(s0) - s, s - F(s1)), np.maximum(np.abs(u) - F(POD_HW + 0.03), np.abs(v) - F(POD_HH + 0.03)))
        return Func(fn, lo, hi)
    fd.paint(band(-0.2, -0.142), KWHITE_L)
    fd.paint(band(-0.185, -0.157), KRED_L)
    # stencils: on its top (white) and on its near side (black)
    # (read from behind the pod on its top, from beside it on its sides)
    stencil(fd, "MSL 4X", bpt(0.03, 0.0, POD_HH), -GX_, GD, 0.045, KWHITE_L)
    stencil(fd, "LOT 07-26", bpt(-0.09, 0.0, POD_HH), -GX_, GD, 0.024, KWHITE_L)
    stencil(fd, "DANGER", bpt(0.17, -POD_HW, 0.12), GD, GU, 0.03, BLACK_L)
    stencil(fd, "ROCKET MOTOR", bpt(0.08, -POD_HW, -0.06), GD, GU, 0.02, BLACK_L)
    stencil(fd, "NO STEP", bpt(-0.1, -POD_HW, 0.12), GD, GU, 0.018, KWHITE_L)
    stencil(fd, "4X MSL", bpt(0.06, POD_HW, 0.04), -GD, GU, 0.032, BLACK_L)
    return fd


def cover_field():
    fd = Field("Cover")
    cover_into(fd, FIRE, COVER_OPEN)
    return fd


# ======================================================================================= the pedestal, yoke and control box
YOKE = [(-0.21, 0.6), (0.2, 0.6), (0.13, 0.8), (0.08, 1.0), (-0.08, 1.0), (-0.16, 0.8)]   # a yoke plate's side profile (y from TRUN, z)
CB_C = v3((MX - YOKE_X - 0.1, TRUN[1] + 0.12, 0.735))      # the control box's middle (on the near yoke plate's outer face)
CB_HALF = (0.05, 0.105, 0.085)


def mount_field():
    """The pedestal: an olive base plate (0) on four levelling jacks (grey 5, steel screws 7), bolted to a gunmetal column
    (5) with a flange, the traversing ring (grey, its teeth), the olive turret plate; the olive yoke plates with their
    lightening holes, the trunnions' bearing caps (grey, bolts); the control box on the near plate (olive, a black panel
    (8) with a small screen, red (12) and white (13) buttons, a key switch, two grey handles); black cables (8) from the box
    down the yoke and into the pod's hub."""
    fd = Field("Mount")
    c0 = v3((MX, BASE_Y, 0.0))
    fd.add(RoundBox(c0 + v3((0, 0, 0.03)), (0.25, 0.25, 0.03), 0.014), 0.0, OLIVE_L)
    for sx in (-1, 1):
        for sy in (-1, 1):
            j = c0 + v3((sx * 0.25, sy * 0.25, 0.0))
            fd.add(RoundBox(j + v3((0, 0, 0.03)) - v3((sx * 0.03, sy * 0.03, 0)), (0.05, 0.05, 0.028), 0.01), 0.01, OLIVE_L)
            fd.add(Cylinder(j + v3((0, 0, 0.05)), 0.026, 0.1, rr=0.006), 0.004, GREY_L)
            fd.add(Cylinder(j + v3((0, 0, 0.008)), 0.042, 0.016, rr=0.005), 0.003, STEEL_L)
            fd.add(Cylinder(j + v3((0, 0, 0.11)), 0.012, 0.03, rr=0.003), 0.002, STEEL_L)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(Sphere(c0 + v3((sx * 0.13, sy * 0.13, 0.062)), 0.012), 0.002, GREY_L)
    fd.add(Cylinder(c0 + v3((0, 0, 0.075)), 0.17, 0.03, rr=0.008), 0.006, GREY_L)                 # the column's flange
    fd.add(Cylinder(c0 + v3((0, 0, 0.3)), 0.115, 0.46, rr=0.01), 0.01, GREY_L)                    # the column
    fd.add(Cylinder(c0 + v3((0, 0, 0.535)), 0.2, 0.07, rr=0.012), 0.008, GREY_L)                 # the traversing ring
    for k in range(28):
        a = 2 * math.pi * k / 28
        fd.add(RoundBox(c0 + v3((math.cos(a) * 0.2, math.sin(a) * 0.2, 0.522)), (0.012, 0.008, 0.02), 0.003, R=euler(0, 0, a)), 0.002, GREY_L)
    fd.add(RoundBox(c0 + v3((0, 0, 0.59)), (YOKE_X + 0.03, 0.23, 0.026), 0.014), 0.008, OLIVE_L)  # the turret plate
    # the yoke plates
    p2 = poly2d(YOKE)
    for sx in (-1, 1):
        xc = MX + sx * YOKE_X
        def plate(P, xc=xc):
            d2 = p2(P[:, 1] - F(TRUN[1]), P[:, 2])
            disc = np.sqrt((P[:, 1] - F(TRUN[1])) ** 2 + (P[:, 2] - F(TRUN[2])) ** 2) - F(0.09)
            d2 = np.minimum(d2, disc)
            hole = np.sqrt((P[:, 1] - F(TRUN[1] + 0.01)) ** 2 + (P[:, 2] - F(0.76)) ** 2) - F(0.045)
            d2 = np.maximum(d2, -hole)
            dx = np.abs(P[:, 0] - F(xc)) - F(0.016)
            r = F(0.008)
            w0, w1 = d2 + r, dx + r
            return np.minimum(np.maximum(w0, w1), F(0)) + np.sqrt(np.maximum(w0, 0) ** 2 + np.maximum(w1, 0) ** 2) - r
        fd.add(Func(plate, (xc - 0.05, TRUN[1] - 0.3, 0.5), (xc + 0.05, TRUN[1] + 0.3, 1.12)), 0.008, OLIVE_L)
        fd.add(Cylinder(TRUN + GX_ * (sx * (YOKE_X + 0.022)), 0.066, 0.03, rr=0.008, R=rot_from_axes(z_axis=GX_)), 0.004, GREY_L)
        for k in range(6):
            a = 2 * math.pi * k / 6
            fd.add(Sphere(TRUN + GX_ * (sx * (YOKE_X + 0.038)) + v3((0, math.cos(a) * 0.046, math.sin(a) * 0.046)), 0.008), 0.001, STEEL_L)
        # gussets down to the turret plate
        for sy in (-1, 1):
            fd.add(RoundBox(v3((xc + sx * 0.022, TRUN[1] + sy * 0.15, 0.66)), (0.006, 0.04, 0.05), 0.004, R=euler(sy * 0.6, 0, 0)), 0.006, OLIVE_L)
    # the elevating gearbox on the far plate's inner face (its pinion on the arc)
    gb = v3((MX + POD_HW + 0.034, TRUN[1] + 0.0, TRUN[2] - 0.235))
    fd.add(RoundBox(gb, (0.012, 0.05, 0.04), 0.008), 0.006, GREY_L)
    # the control box
    c = CB_C
    hx, hy, hz = CB_HALF
    fd.add(RoundBox(c, (hx, hy, hz), 0.012), 0.0, OLIVE_L)
    fd.add(RoundBox(c + v3((hx * 0.6 + 0.02, 0, 0)), (0.03, 0.06, 0.05), 0.008), 0.006, OLIVE_L)  # its bracket to the plate
    pf = c - v3((hx, 0, 0))
    Rp = rot_from_axes(z_axis=(-1, 0, 0), y_axis=(0, 0, 1))
    fd.add(RoundBox(pf, (hy - 0.012, hz - 0.012, 0.006), 0.004, R=Rp), 0.003, BLACK_L)
    fd.sub(RoundBox(pf + v3((-0.004, 0.02, 0.03)), (0.05, 0.026, 0.004), 0.003, R=Rp), 0.002)         # the screen's well
    fd.paint(RoundBox(pf + v3((-0.002, 0.02, 0.03)), (0.046, 0.022, 0.01), 0.003, R=Rp), OLIVE_L)
    for k, (dy, dz, lab) in enumerate(((-0.05, -0.02, KRED_L), (-0.02, -0.02, KWHITE_L), (0.01, -0.02, KWHITE_L), (0.04, -0.02, KWHITE_L))):
        fd.add(Cylinder(pf + v3((-0.008, dy, dz)), 0.011 if k == 0 else 0.008, 0.012, rr=0.003, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, lab)
    fd.add(Cylinder(pf + v3((-0.008, 0.06, -0.05)), 0.012, 0.012, rr=0.003, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, GREY_L)   # the key switch
    fd.add(RoundBox(pf + v3((-0.018, 0.06, -0.05)), (0.003, 0.012, 0.004), 0.001), 0.002, STEEL_L)
    for sz in (-1, 1):                                                                              # handles
        a, b = c + v3((-hx, -hy + 0.01, sz * (hz - 0.012))), c + v3((-hx, hy - 0.01, sz * (hz - 0.012)))
        fd.add(Chain([a, a - v3((0.028, 0, 0)), b - v3((0.028, 0, 0)), b], [0.007] * 4, k=0.003), 0.003, GREY_L)
    # the cables
    cb0 = c + v3((0.0, -0.02, -hz))
    pts = [cb0, cb0 + v3((0.0, -0.01, -0.06)), v3((MX - YOKE_X - 0.03, TRUN[1] - 0.1, 0.62)), v3((MX - YOKE_X + 0.02, TRUN[1] - 0.16, 0.63))]
    fd.add(Chain(pts, [0.012] * 4, k=0.008), 0.004, BLACK_L)
    cb1 = c + v3((0.01, hy, 0.02))
    pts = [cb1, cb1 + v3((0.0, 0.04, 0.05)), TRUN + GX_ * -(YOKE_X + 0.05) + v3((0, 0.06, 0.04)), TRUN + GX_ * -(YOKE_X + 0.04)]
    fd.add(Chain(pts, [0.011] * 4, k=0.008), 0.004, BLACK_L)
    # stencils on the turret plate's edge
    stencil(fd, "A-07", v3((MX, BASE_Y - 0.232, 0.59)), v3((1, 0, 0)), v3((0, 0, 1)), 0.026, KWHITE_L)
    return fd


# ======================================================================================= the ready crate
CRATE_LOW = 0.17                            # (it stands on a closed crate of the same kind)
CRATE_C = v3((-0.31, 0.05, CRATE_LOW))      # its floor's middle (on his right)
CRATE_HALF = (0.12, 0.32, 0.13)             # (its length along Y)
CR_SLOTS = (0.055, -0.055)                  # the two cradles (x from its middle): the near one (toward him) is his
MSL_BOX_A = v3((0.0, -1.0, 0.0))            # (rest) a crated missile's axis, tail -> nose (noses forward)


def crate_tail(j):
    return CRATE_C + v3((CR_SLOTS[j], MSL_L * 0.5, CRATE_HALF[2] - 0.035))


def crate_field():
    """An olive composite case (0) with black corner guards and latches (8), white stencils (13), black foam inside with
    two cradles: one missile in the far one, the near one empty (his); the lid (0, black foam 8) standing open on its far
    side. It stands on a closed one (a little askew), its lid strapped down."""
    fd = Field("Crate")
    c = CRATE_C
    hx, hy, h = CRATE_HALF
    t = 0.016
    # the closed one under it
    c2 = c - v3((0.0, 0.0, CRATE_LOW))
    R2 = euler(0, 0, 0.05)
    fd.add(RoundBox(c2 + v3((0.008, 0.0, CRATE_LOW / 2)), (hx + 0.01, hy + 0.01, CRATE_LOW / 2 - 0.002), 0.014, R=R2), 0.0, OLIVE_L)
    for yy in (-0.2, 0.2):
        fd.add(RoundBox(c2 + R2 @ v3((0.0, yy, 0.0)) + v3((0.008, 0.0, CRATE_LOW * 0.5)), (hx + 0.016, 0.022, CRATE_LOW * 0.5 + 0.004), 0.004, R=R2), 0.002, BLACK_L)
    stencil(fd, "MSL 1X", c2 + R2 @ v3((hx + 0.01, 0.0, 0.0)) + v3((0.008, 0.0, CRATE_LOW * 0.5)), R2 @ v3((0, -1, 0)), v3((0, 0, 1)), 0.03, KWHITE_L)
    def box(P):
        q = P - c.astype(F)
        outer = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx), np.abs(q[:, 1]) - F(hy)), np.maximum(-q[:, 2], q[:, 2] - F(h)))
        inner = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx - t), np.abs(q[:, 1]) - F(hy - t)), F(h - 0.075) - q[:, 2])
        return np.maximum(outer, -inner)
    lo, hi = c - v3((hx + 0.04, hy + 0.04, 0.02)), c + v3((hx + 0.04, hy + 0.04, h + 0.04))
    fd.add(Func(box, lo, hi), 0.0, OLIVE_L)
    fd.add(Func(lambda P: np.maximum(box(P) - F(0.004), np.abs(P[:, 2] - F(c[2] + h * 0.5)) - F(0.012)), lo, hi), 0.004, OLIVE_L)  # a rib
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(RoundBox(c + v3((sx * hx, sy * hy, h * 0.5)), (0.016, 0.016, h * 0.5 + 0.004), 0.006), 0.003, BLACK_L)
    for sy in (-1, 1):
        fd.add(RoundBox(c + v3((0.0, sy * (hy + 0.008), h * 0.62)), (0.04, 0.006, 0.012), 0.004), 0.003, BLACK_L)   # handles
        fd.add(RoundBox(c + v3((hx + 0.004, sy * 0.2, h - 0.025)), (0.006, 0.018, 0.02), 0.004), 0.002, BLACK_L)    # latches
    # the foam bed and its cradles
    def foam(P):
        q = P - c.astype(F)
        bed = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx - t), np.abs(q[:, 1]) - F(hy - t)), np.maximum(F(0.02) - q[:, 2], q[:, 2] - F(h - 0.03)))
        cr = None
        for x in CR_SLOTS:
            d = np.sqrt((q[:, 0] - F(x)) ** 2 + (q[:, 2] - F(h - 0.035)) ** 2) - F(MSL_R + 0.006)
            d = np.maximum(d, np.abs(q[:, 1]) - F(MSL_L * 0.5 + 0.01))
            cr = d if cr is None else np.minimum(cr, d)
        return np.maximum(bed, -cr)
    fd.add(Func(foam, lo, hi, disp=lambda P: F(0.001) * NOISE(P * F(80)), disp_amp=0.001), 0.003, BLACK_L)
    missile_into(fd, crate_tail(1), MSL_BOX_A, k=0.002)
    # the lid, open on its hinges along the far side, standing up and leaning out a little
    Rl = euler(0, -1.75, 0)
    hinge = c + v3((-hx, 0.0, h))
    lc = hinge + Rl @ v3((hx, 0.0, -0.02))
    fd.add(RoundBox(lc, (hx, hy, 0.022), 0.01, R=Rl), 0.004, OLIVE_L)
    fd.add(RoundBox(lc + Rl @ v3((0, 0, -0.022)), (hx - 0.02, hy - 0.02, 0.01), 0.006, R=Rl), 0.003, BLACK_L)
    for sy in (-1, 1):
        fd.add(Cylinder(hinge + v3((-0.004, sy * 0.22, 0.0)), 0.009, 0.05, rr=0.003, R=rot_from_axes(z_axis=(0, 1, 0))), 0.002, BLACK_L)
    # stencils on its near side and on the lid
    stencil(fd, "MSL 1X", c + v3((hx, 0.12, h * 0.48)), v3((0, -1, 0)), v3((0, 0, 1)), 0.032, KWHITE_L)
    stencil(fd, "LOT 07", c + v3((hx, -0.16, h * 0.48)), v3((0, -1, 0)), v3((0, 0, 1)), 0.024, KWHITE_L)
    lid_in = lc + Rl @ v3((0, 0, -0.033))
    stencil(fd, "HANDLE WITH CARE", lid_in, v3((0, -1, 0)), norm(Rl @ v3((-1, 0, 0))), 0.024, KWHITE_L)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.614)), 0.045, 0.45)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.104, -0.14, 1.636)), 0.05, 0.35), (hp((sx * 0.05, -0.18, 1.77)), 0.06, 0.2)]
    return pts


# ======================================================================================= build config
GLB_NAME = "missile_launcher"
ROOT_NAME = "MissileLauncherHQ"
TEX_PREFIX = "missile_launcher"
MAT_NAME = "MissileLauncherMat"
MESH_NAME = "MissileLauncher"
BASE_MODULE = "missile_base"
ANIM_MODULE = "anim_missile"
PARTS = ["Skin", "Eyes", "Hair", "Helmet", "Headset", "Shirt", "Carrier", "Trousers", "Boots", "Gloves", "Tablet",
         "Mount", "Pod", "Cover", "Missile", "Crate"]
REGION_PARTS = ("Skin", "Helmet", "Headset", "Shirt", "Carrier", "Trousers", "Boots", "Tablet", "Mount", "Pod", "Cover",
                "Missile", "Crate")
KIT = {"olive": OLIVE_KIT, "grey": GUNMETAL, "red": RED, "white": (0.86, 0.85, 0.8)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_MslSkin", "base": (0.6, 0.4, 0.28), "ruddy": (0.62, 0.34, 0.24), "lips": (0.46, 0.27, 0.22),
                      "brow": ((0.05, 0.035, 0.03), (0.12, 0.08, 0.06)),
                      "extra": ((LASH, (0.04, 0.03, 0.025), 0.5), (STUBBLE, (0.3, 0.21, 0.16), 0.6, 0.45))}),
    "Hair": ("hair", {"name": "HQ_MslHair", "base": (0.06, 0.045, 0.035), "hi": (0.2, 0.15, 0.11), "low": (0.03, 0.025, 0.02),
                      "streak": (0.04, 0.03, 0.025), "tint": (0.09, 0.07, 0.05)}),
    "Helmet": ("fieldgun", dict(KIT, name="HQ_MslHelmet", olive=OLIVE)),
    "Headset": ("fieldgun", dict(KIT, name="HQ_MslHelmet", olive=OLIVE)),
    "Shirt": ("uniform", {"name": "HQ_MslShirt", "base": OLIVE, "facing": RED, "brass": STEEL_C, "buff": WHITE, "black": BLACK}),
    "Trousers": ("uniform", {"name": "HQ_MslTrousers", "base": OLIVE, "facing": RED, "brass": STEEL_C, "buff": (0.1, 0.1, 0.1), "black": BLACK}),
    "Carrier": ("uniform", {"name": "HQ_MslCarrier", "base": COYOTE, "facing": RED, "brass": STEEL_C, "buff": WHITE, "black": BLACK}),
    "Boots": ("leather_dyed", {"name": "HQ_MslBoots", "base": (0.07, 0.065, 0.065), "dyed": (0.05, 0.048, 0.048), "worn_c": (0.3, 0.29, 0.28)}),
    "Gloves": ("leather_dyed", {"name": "HQ_MslGloves", "base": (0.08, 0.08, 0.085), "dyed": (0.08, 0.08, 0.085), "worn_c": (0.28, 0.28, 0.29)}),
    "Tablet": ("fieldgun", dict(KIT, name="HQ_MslTablet", olive=(0.1, 0.24, 0.23))),
    "Mount": ("fieldgun", dict(KIT, name="HQ_Launcher")),
    "Pod": ("fieldgun", dict(KIT, name="HQ_Launcher")),
    "Cover": ("fieldgun", dict(KIT, name="HQ_Launcher")),
    "Missile": ("fieldgun", dict(KIT, name="HQ_Launcher")),
    "Crate": ("fieldgun", dict(KIT, name="HQ_Launcher")),
}
LOW_TARGETS = {"Skin": 5200, "Hair": 380, "Helmet": 1500, "Headset": 760, "Shirt": 3200, "Carrier": 3100, "Trousers": 1900,
               "Boots": 1100, "Gloves": 900, "Tablet": 520, "Mount": 3000, "Pod": 3900, "Cover": 220, "Missile": 420, "Crate": 1400}
AO_EXCLUDE = ["Tablet", "Cover", "Missile", "Headset"]
MACHINE_PARTS = ["Mount", "Pod", "Cover", "Missile", "Crate"]
# the launcher and the crate are baked 6 m away from him (his rest pose stands close to both)
BAKE_APART = (MACHINE_PARTS, (6.0, 0.0, 0.0))
YAW_PIVOT = (0.33, -0.08, 0.0)              # the tower turns about this point (keeps him, the launcher and the crate on the base)


def prop_bones():
    return []                                # everything he handles is a free bone (extra_bones)


def extra_bones():
    """The launcher's bones (none of them deform him): mount (the pedestal: it shudders at the shot), pod (elevating about
    the trunnions; child of the mount), cover (the firing tube's blast cover, hinged on the pod), missile (the firing
    tube's missile, tail -> nose: posed in the world, hidden from the shot until he lifts the next one from the crate),
    tablet (his fire-control unit), props (the ready crate, still)."""
    C, X, U, N = tablet_frame()
    tail = seated_tail(FIRE)
    H = hinge_pt(FIRE)
    return [
        ("mount", v3((MX, BASE_Y, 0.0)), v3((MX, BASE_Y, 0.3)), None),
        ("pod", TRUN, TRUN + GD * 0.3, "mount"),
        ("cover", H, H + GX_ * 0.1, "pod"),
        ("missile", tail, tail + GD * MSL_L, None),
        ("tablet", C, C + U * 0.12, None),
        ("props", CRATE_C, CRATE_C + v3((0, 0, 0.2)), None),
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
    return {
        "Eyes": ("rigid", "head"), "Hair": ("rigid", "head"), "Helmet": ("rigid", "head"), "Headset": ("rigid", "head"),
        "Shirt": ("transfer", body | {"upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}, None),
        "Carrier": ("transfer", body, None),
        "Trousers": ("custom", trousers_weights),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Tablet": ("rigid", "tablet"),
        "Mount": ("rigid", "mount"), "Pod": ("rigid", "pod"), "Cover": ("rigid", "cover"), "Missile": ("rigid", "missile"),
        "Crate": ("rigid", "props"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part == "Skin" and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Tablet",):
        return 1.4
    if part in ("Mount", "Crate"):
        return 0.75
    if part in ("Pod",):
        return 0.9
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Hair", hair_field(), 0.0022 if fine else 0.003),
        ("Helmet", helmet_field(), 0.0024 if fine else 0.0034),
        ("Headset", headset_field(), 0.0018 if fine else 0.0026),
        ("Shirt", shirt_field(), 0.0026 if fine else 0.0036),
        ("Carrier", carrier_field(), 0.0026 if fine else 0.0036),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Gloves", gloves_field(), 0.0018 if fine else 0.0026),
        ("Tablet", tablet_field(), 0.0014 if fine else 0.002),
        ("Mount", mount_field(), 0.003 if fine else 0.0042),
        ("Pod", pod_field(), 0.0026 if fine else 0.0036),
        ("Cover", cover_field(), 0.0016 if fine else 0.0024),
        ("Missile", missile_field(), 0.0016 if fine else 0.0024),
        ("Crate", crate_field(), 0.0024 if fine else 0.0034),
    ]
