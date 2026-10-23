"""The Field Gun (HQ tower, Industrial Age): a breech-loading steel field gun of about 1900 and the gun-layer of the steam
corps who serves it. Rest pose: he stands in an A-pose facing -Y (the way it shoots), feet at z = 0, the gun on his left
(+X) with its axle in front of him; the gun is loaded, its breech closed.

Him: the Cannon's burly body (torsion.py), his own face: ruddy and set, a square jaw and a shaved chin, a straight strong
nose, narrowed grey eyes under russet brows drawn down in a frown, thick russet mutton-chop whiskers joined to a heavy
moustache over a firm closed mouth; short russet hair under a peaked forage cap (a navy crown piped in scarlet, a buff
band, a black patent-leather peak and chin strap, a brass flaming-grenade badge). A navy wool tunic to the upper thigh,
buttoned down the front with seven brass buttons, a scarlet standing collar, two breast pockets with buttoned flaps; a
brown leather belt with a brass buckle; navy trousers with a scarlet stripe down the outer seam, tucked into brown knee
boots; brown leather gauntlets; a pair of black field glasses with brass rims on a strap round his neck, on his chest.

The gun: a long steel barrel (gunmetal grey) from a square breech ring with a horizontal sliding block and its lever to
a swelled muzzle, riding on a cradle with the recoil cylinder under it and a brass telescope sight on its right; the
cradle's trunnions in a saddle of two side plates over the axle; an armoured shield of riveted steel in front with an
aperture for the barrel and a sighting slot, an apron below the axle; two big spoked wheels with steel tyres and brass
hub caps; a box trail ending in a spade dug into the ground; the elevating handwheel on the saddle's right side; the
firing lanyard (a cord and a wooden toggle) hanging from the cradle. Olive-drab and gunmetal-grey paint, brass fittings.
Beside him (on his right) a ready-use ammunition box, its lid thrown back, three fixed rounds (brass cases, grey shells
with copper driving bands and brass fuses) lying in it.

Painted labels on the gun (material `fieldgun`): 0 olive drab, 5 gunmetal grey, 6 brass, 7 bright steel, 8 black iron,
9 wood, 10 cord, 11 copper. On the uniform (material `uniform`): 0 navy wool, 5 scarlet facings, 6 brass, 7 buff,
8 black patent leather."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import torsion as _t
from torsion import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD,
                     EYE_R, eye_c, smoothstep, hand_frame, HAND_S, fist_center, foot, traps, neck_prim, deltoid,
                     upper_arm, eyes_field, skull, torso_prims, belt_base, TORSO, TORSO_Z, torso_bones)
from cannon import capped_cone, poly2d, _ring_x, _arm_coord

IRIS = ((0.3, 0.36, 0.42), (0.56, 0.64, 0.7))           # steely grey eyes (prep.paint_eyes)
NAVY = (0.05, 0.07, 0.17)                               # the corps' wool (the brief's colour)
SCARLET = (0.62, 0.09, 0.07)
BRASS = (0.8, 0.55, 0.22)
COPPER = (0.75, 0.35, 0.18)
BUFF = (0.74, 0.6, 0.38)
RUSSET = (0.27, 0.13, 0.06)                             # his hair and whiskers
FACING, BRASS_L, BUFF_L, BLACK_L = 5, 6, 7, 8           # uniform labels (navy wool is 0)
OLIVE_L, GREY_L, STEEL_L, IRON_L, WOOD_L, CORD_L, COPPER_L = 0, 5, 7, 8, 9, 10, 11   # gun labels (brass is 6)


# ======================================================================================= hands (gripping, in gloves)
CURLS = {"R": (1.3, 1.45, 1.1), "L": (1.25, 1.4, 1.05)}


def hand(fd, side, s=HAND_S):
    """torsion.hand with both hands half closed (the lanyard's toggle, the lever, the handwheel's knob, a round)."""
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.064, 0.034, 0.066)) * s, 0.03 * s, R=Rp), 0.028, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.036, 0.03, 0.052)) * s, R=Rp), 0.019, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.044, 0.0148, -0.0148, -0.044)
    lens = (0.96, 1.02, 0.96, 0.8)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.022 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j]) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.011, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.016 * s), 0.009, SKIN)
    tb = wr + f * 0.045 * s + t * 0.052 * s + n * 0.011
    d1 = norm(f * 0.55 + t * 0.6 + n * 0.5)
    d2 = norm(f * 0.4 - t * 0.4 + n * 0.5)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.026 * s, 0.023 * s, 0.02 * s], k=0.008), 0.018, SKIN)


def palm_pt(side):
    """The middle of the palm's grip (rest pose): where a held thing touches."""
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.1 * HAND_S + n * 0.045


# ======================================================================================= head
JAW = ((0.0, -0.056, 1.584), (0.154, 0.14, 0.132))
CHIN = ((0.0, -0.14, 1.497), (0.088, 0.07, 0.07))


def cheek(sx):
    return (sx * 0.112, -0.128, 1.632), 0.052


def jowl(sx):
    return (sx * 0.132, -0.048, 1.556), 0.052


def chin_mask(P):
    """His shaved chin and upper throat (design coordinates): a shadow of stubble."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    return np.maximum(np.maximum(np.abs(x) - F(0.08), z - F(1.535)), np.maximum(F(1.43) - z, y + F(0.05)))


MOUTH_SLOT = [(-0.05, -0.174, 1.551), (-0.026, -0.196, 1.546), (0.0, -0.202, 1.547), (0.026, -0.196, 1.546), (0.05, -0.174, 1.551)]


def head(fd):
    """A square, ruddy, set face: a strong jaw and chin, full cheeks, a heavy brow, narrowed eyes under brows drawn down in
    a frown, a straight strong nose with a fleshy tip, a firm closed mouth, ears standing out from the whiskers."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.79), (0.165, 0.175, 0.12)), 0.08, SKIN)
    fd.add(E(*JAW), 0.07, SKIN)
    fd.add(E(*CHIN), 0.05, SKIN)
    fd.add(E((0.0, -0.17, 1.488), (0.05, 0.03, 0.03)), 0.03, SKIN)                        # the chin's square point
    for sx in (-1, 1):
        fd.add(S(*cheek(sx)), 0.05, SKIN)
        fd.add(S(*jowl(sx)), 0.05, SKIN)
        fd.add(E((sx * 0.125, -0.02, 1.52), (0.04, 0.06, 0.04)), 0.05, SKIN)              # the jaw's corners
        pts = [hp((sx * 0.156, -0.055, 1.744)), hp((sx * 0.118, -0.134, 1.756)), hp((sx * 0.062, -0.18, 1.752)), hp((0.0, -0.19, 1.746))]
        fd.add(Chain(pts, [hr(0.013), hr(0.023), hr(0.027), hr(0.025)], k=hr(0.022)), hr(0.034), SKIN)     # heavy brow ridge
    fd.paint(Func(chin_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # a frown: two deep lines between the brows, creases across the forehead
    for sx in (-1, 1):
        fd.sub(RoundCone(hp((sx * 0.011, -0.201, 1.736)), hp((sx * 0.016, -0.198, 1.764)), hr(0.0022), hr(0.0016)), hr(0.003))
    sk = skull()
    for zc in (1.79,):
        pts = []
        for k in range(9):
            x = -0.08 + 0.16 * k / 8
            h, ok = ray_hit(sk, [hp((x, -0.6, zc + 0.008 * (x / 0.08) ** 2))], [v3((0, 1, 0))], tmax=0.7)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 3:
            fd.sub(Chain(pts, [hr(0.0024)] * len(pts), k=0.002), hr(0.003))
    # russet brows, bushy, the inner ends drawn down and in
    tuft = lambda P: F(0.0024) * NOISE(P * F(140)) + F(0.0011) * np.sin(P[:, 0] * F(360) + P[:, 2] * F(90))
    for sx in (-1, 1):
        pts = [hp((sx * 0.02, -0.215, 1.741)), hp((sx * 0.064, -0.211, 1.759)), hp((sx * 0.11, -0.19, 1.772)),
               hp((sx * 0.155, -0.147, 1.768))]
        fd.add(Chain([p + v3((0, 0.004, 0)) for p in pts], [hr(0.013), hr(0.016), hr(0.014), hr(0.007)], k=hr(0.009),
                     disp=tuft, disp_amp=0.004), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.022), hr(0.025), hr(0.022), hr(0.013)], k=hr(0.01)), BROW)
    # eyes narrowed in concentration: both lids closing in, the upper tilted down toward the nose
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.0148))), (sx * 0.3, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.006)), Plane(ec + v3((0, 0, -hr(0.0185))), (sx * -0.15, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0125))), (sx * 0.3, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(2):                                                                    # crow's feet
            a = hp((sx * (0.112 + 0.004 * k), -0.13 + 0.006 * k, 1.676 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.024, 0.012, -0.002 - 0.008 * k)), hr(0.0022), hr(0.0015)), hr(0.003))
        fd.add(Ellipsoid(hp((sx * 0.07, -0.156, 1.642)), v3((0.026, 0.011, 0.01)) * HS), hr(0.012), SKIN)    # bags under the eyes
    # a straight strong nose, a fleshy tip
    fd.add(RoundCone(hp((0, -0.19, 1.726)), hp((0, -0.248, 1.636)), hr(0.019), hr(0.026)), hr(0.018), SKIN)
    fd.add(S((0, -0.212, 1.69), 0.017), hr(0.012), SKIN)
    fd.add(S((0, -0.25, 1.618), 0.033), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.036, -0.224, 1.602), 0.023), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.018, -0.242, 1.59)), v3((0.01, 0.012, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a firm closed mouth (its upper lip under the moustache), the corners pressed down
    slot = [hp(p) for p in MOUTH_SLOT]
    fd.sub(Chain(slot, [hr(0.002), hr(0.0026), hr(0.0028), hr(0.0026), hr(0.002)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0038), hr(0.004), hr(0.0038), hr(0.003)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.046, -0.174, 1.541), (-0.024, -0.193, 1.532), (0, -0.198, 1.53), (0.024, -0.193, 1.532), (0.046, -0.174, 1.541)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0072), hr(0.0082), hr(0.0072), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    for sx in (-1, 1):
        fd.sub(RoundCone(hp((sx * 0.056, -0.168, 1.548)), hp((sx * 0.062, -0.158, 1.53)), hr(0.002), hr(0.0015)), hr(0.003))
    # ears, standing out behind the whiskers
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.029, 0.052, 0.066)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.013, 0.033, 0.043)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))


def body_parts(fd):
    """The Torsion engineer's barrel-chested body (torsion.body_parts) with this head and gripping hands."""
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


# ======================================================================================= whiskers and hair
def face_hull():
    fd = Field("FaceHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E(*JAW), 0.07)
    fd.add(E(*CHIN), 0.05)
    for sx in (-1, 1):
        c, r = cheek(sx)
        fd.add(Sphere(hp(c), hr(r)), 0.05)
        c, r = jowl(sx)
        fd.add(Sphere(hp(c), hr(r)), 0.05)
        fd.add(E((sx * 0.125, -0.02, 1.52), (0.04, 0.06, 0.04)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


CHOP_PTS = [(0.168, -0.035, 1.75), (0.172, -0.05, 1.672), (0.164, -0.074, 1.594), (0.14, -0.108, 1.545),
            (0.112, -0.14, 1.556), (0.092, -0.162, 1.574)]
CHOP_RAD = [0.024, 0.034, 0.05, 0.048, 0.036, 0.024]


def _chop_region(Q):
    """< 0 inside the mutton chops (design coordinates): a broad band from each temple down over the cheek to the jaw and
    forward along it to the corner of the mouth; the chin and the lips left bare."""
    out = None
    for sx in (-1, 1):
        pts = [v3((sx * x, y, z)) for x, y, z in CHOP_PTS]
        d = Chain(pts, CHOP_RAD, k=0.02).sdf(Q)
        out = d if out is None else np.minimum(out, d)
    lips = np.sqrt((Q[:, 0] / F(0.066)) ** 2 + ((Q[:, 1] + F(0.18)) / F(0.06)) ** 2 + ((Q[:, 2] - F(1.542)) / F(0.03)) ** 2) - F(1.0)
    return np.maximum(out, -lips * F(0.03))


def whiskers_field():
    """Thick russet mutton chops from his temples down his cheeks to the jaw, bushy at the jaw, swept forward to the corners
    of his mouth, joined to a heavy moustache that hides his upper lip."""
    fd = Field("Whiskers")
    hull = face_hull()
    hairs = lambda P: F(0.0024) * NOISE(P * np.array([90, 90, 28], F)) + F(0.001) * NOISE(P * F(170))
    def chops(P):
        d = hull.eval(P, margin=0.06)
        m = _chop_region(hinv(P)) * F(HS)
        depth = np.clip(-m / F(0.026), 0, 1)
        outer = F(0.004) + F(0.024) * np.sqrt(depth)
        vol = np.maximum(d - outer, F(-0.006) - d)
        return np.maximum(vol, m)
    lo, hi = HEAD_C + v3((-0.32, -0.36, -0.42)), HEAD_C + v3((0.32, 0.12, 0.1))
    fd.add(Func(chops, lo, hi, disp=hairs, disp_amp=0.003), 0.0)
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):                                                       # the moustache, drooping to the chops
        pts = [hp((sx * 0.004, -0.237, 1.59)), hp((sx * 0.042, -0.227, 1.584)), hp((sx * 0.074, -0.202, 1.572)),
               hp((sx * 0.096, -0.17, 1.566))]
        fd.add(Lock(pts, [hr(0.021), hr(0.026), hr(0.022), hr(0.017)], [hr(0.013), hr(0.015), hr(0.013), hr(0.011)],
                    [norm(v3((sx * 0.3, -1, 0.1)))] * 4, k=hr(0.007), disp=strands, disp_amp=0.003), hr(0.008))
    return fd


# the forage cap's lower edge (design coordinates): level, just above his brows
CAP_HEM = 1.8
CAP_BAND = 0.07             # the band's height (design)
CAP_CROWN = 0.072           # the crown above it


def _skull_extent(zd):
    """The skull's half widths at design height zd: (x, y front, y back) in world units, for fitting the cap."""
    sk = skull()
    c = hp((0.0, 0.0, zd))
    out = []
    for d in ((1, 0, 0), (0, -1, 0), (0, 1, 0)):
        o = c + v3(d) * 0.6
        h, ok = ray_hit(sk, [o], [-v3(d)], tmax=0.7)
        out.append(float(np.linalg.norm(h[0] - c)) if ok[0] else 0.2)
    return out


_SK = _skull_extent(CAP_HEM + 0.01)
CAP_RX = _SK[0] + 0.016                                  # the band: an elliptic cylinder hugging his head
CAP_RY = 0.5 * (_SK[1] + _SK[2]) + 0.016
CAP_CY = 0.5 * (_SK[2] - _SK[1])                         # its centre (y, world) relative to the head's axis
CAP_Z0 = float(hp((0, 0, CAP_HEM))[2])
CAP_Z1 = CAP_Z0 + hr(CAP_BAND)
CAP_Z2 = CAP_Z1 + hr(CAP_CROWN)
CAP_C = v3((0.0, float(hp((0, 0, CAP_HEM))[1]) + CAP_CY, CAP_Z0))


def _ell_cyl(P, c, rx, ry, z0, z1, rr):
    """A rounded elliptic cylinder (axis Z) from z0 to z1."""
    q = P - c.astype(F)
    e = (np.sqrt((q[:, 0] / F(rx)) ** 2 + (q[:, 1] / F(ry)) ** 2) - F(1.0)) * F(min(rx, ry))
    dz = np.maximum(F(z0) - P[:, 2], P[:, 2] - F(z1))
    w0, w1 = e + F(rr), dz + F(rr)
    return np.minimum(np.maximum(w0, w1), F(0)) + np.sqrt(np.maximum(w0, 0) ** 2 + np.maximum(w1, 0) ** 2) - F(rr)


def peak_sd(P):
    """The cap's peak: a crescent of patent leather from the band's front, sloping down over his eyes, its sides curving
    down a little."""
    q = P - CAP_C.astype(F)
    x, y = q[:, 0], q[:, 1]
    a, b = F(CAP_RX * 0.98), F(CAP_RY + 0.085)
    e_out = (np.sqrt((x / a) ** 2 + (y / b) ** 2) - F(1.0)) * F(0.08)
    e_in = (np.sqrt((x / F(CAP_RX)) ** 2 + (y / F(CAP_RY)) ** 2) - F(1.0))
    out = np.maximum(e_in, F(0)) * F(CAP_RY)
    zp = F(CAP_Z0 + 0.004) - F(0.42) * out - F(0.012) * (x / a) ** 2
    d_sheet = np.abs(P[:, 2] - zp) - F(0.0045)
    front = y + F(0.02)                                                  # in front of the head only
    return np.maximum(np.maximum(d_sheet * F(0.8), e_out), np.maximum(front, F(-0.004) - e_in * F(CAP_RY)))


def cap_field():
    """A peaked forage cap: a buff band (7), a navy crown a little wider than the band (0) piped in scarlet round its top
    (5), a black patent-leather peak and chin strap (8), brass side buttons and a brass flaming-grenade badge (6)."""
    fd = Field("Cap")
    lo, hi = CAP_C - v3((0.3, 0.3, 0.05)), CAP_C + v3((0.3, 0.3, 0.25))
    fd.add(Func(lambda P: _ell_cyl(P, CAP_C, CAP_RX, CAP_RY, CAP_Z0, CAP_Z1 + 0.01, 0.006), lo, hi), 0.0, BUFF_L)
    soft = lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.0006) * NOISE(P * F(90))
    cr = CAP_C + v3((0.0, -0.004, 0.0))
    fd.add(Func(lambda P: _ell_cyl(P, cr, CAP_RX + 0.022, CAP_RY + 0.026, CAP_Z1, CAP_Z2, 0.022), lo, hi, disp=soft, disp_amp=0.002), 0.012, 0)
    # the scarlet piping round the crown's top edge
    def piping(P):
        q = P - cr.astype(F)
        e = (np.sqrt((q[:, 0] / F(CAP_RX + 0.022)) ** 2 + (q[:, 1] / F(CAP_RY + 0.026)) ** 2) - F(1.0)) * F(CAP_RX)
        return np.sqrt(e * e + (P[:, 2] - F(CAP_Z2 - 0.018)) ** 2) - F(0.006)
    fd.add(Func(piping, lo, hi), 0.002, FACING)
    fd.add(Func(peak_sd, lo, hi), 0.004, BLACK_L)
    # the chin strap across the band's front, above the peak, from button to button
    def strap(P):
        q = P - CAP_C.astype(F)
        e = (np.sqrt((q[:, 0] / F(CAP_RX)) ** 2 + (q[:, 1] / F(CAP_RY)) ** 2) - F(1.0)) * F(CAP_RX)
        zs = F(CAP_Z0 + 0.022) + F(0.004) * (q[:, 0] / F(CAP_RX)) ** 2
        return np.maximum(np.maximum(np.abs(e - F(0.004)) - F(0.004), np.abs(P[:, 2] - zs) - F(0.008)), q[:, 1] + F(CAP_RY * 0.05))
    fd.add(Func(strap, lo, hi), 0.002, BLACK_L)
    for sx in (-1, 1):
        p = CAP_C + v3((sx * (CAP_RX + 0.006) * 0.985, -(CAP_RY + 0.006) * 0.17, CAP_Z0 + 0.022 - CAP_C[2]))
        fd.add(Sphere(p, 0.011), 0.002, BRASS_L)
    # the badge: a brass grenade with a flame on the band's front
    bf = CAP_C + v3((0.0, -CAP_RY - 0.008, hr(CAP_BAND) * 0.55))
    fd.add(Sphere(bf, 0.017), 0.003, BRASS_L)
    for k, (dx, h) in enumerate(((-0.012, 0.03), (0.0, 0.042), (0.012, 0.03))):
        fd.add(RoundCone(bf + v3((dx * 0.6, -0.002, 0.012)), bf + v3((dx, -0.004, h)), 0.008, 0.002), 0.004, BRASS_L)
    return fd


def hair_field():
    """Short russet hair under the cap: round the back of his head and over his temples, down to the whiskers in front of
    his ears; his ears left bare."""
    fd = Field("Hair")
    sk = skull()
    strands = lambda P: F(0.002) * NOISE(P * np.array([70, 70, 22], F)) + F(0.001) * NOISE(P * F(130))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        top = z - F(CAP_HEM + 0.03)
        nape = F(1.6) - z + F(0.05) * smoothstep(0.03, 0.12, np.abs(x))
        front = F(-0.07) - y
        ear = F(1.0) - np.sqrt(((np.abs(x) - F(0.18)) / F(0.05)) ** 2 + ((y - F(0.035)) / F(0.068)) ** 2 + ((z - F(1.664)) / F(0.078)) ** 2)
        return np.maximum(np.maximum(np.maximum(top, nape), front), ear * F(0.05))
    fd.add(Inter(Shell(sk, 0.006, 0.012, pad=0.06, disp=strands, disp_amp=0.003), Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.006), 0.0)
    return fd


# ======================================================================================= the tunic
TUNIC_HEM = 0.64
TUNIC_OFF, TUNIC_T = 0.024, 0.018
SKIRT_Z = (0.6, 0.66, 0.82, 0.98)
SKIRT_RX = (0.318, 0.312, 0.29, 0.24)
SKIRT_RY = (0.232, 0.228, 0.222, 0.2)


def skirt_sd(P):
    """An oval bell from the waist, flaring over his hips and thighs to the hem."""
    z = P[:, 2]
    rx = np.interp(z, SKIRT_Z, SKIRT_RX).astype(F)
    ry = np.interp(z, SKIRT_Z, SKIRT_RY).astype(F)
    e = (np.sqrt((P[:, 0] / rx) ** 2 + ((P[:, 1] - F(0.035)) / ry) ** 2) - F(1.0)) * np.minimum(rx, ry)
    return np.maximum(e, np.maximum(z - F(SKIRT_Z[-1]), F(SKIRT_Z[0]) - z))


def tunic_hull():
    b = Field("TunicHull")
    for i, (p, k) in enumerate(torso_prims()):
        if i in (2, 3):                                     # (no pectorals: the wool hangs smooth over his chest)
            continue
        b.add(p, k)
    b.add(Ellipsoid((0, -0.07, 1.22), (0.26, 0.15, 0.17)), 0.06)
    b.add(traps(), 0.06)
    b.add(Func(skirt_sd, (-0.45, -0.3, 0.55), (0.45, 0.36, 1.05)), 0.07)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        b.add(deltoid(side), 0.055)
        b.add(upper_arm(side), 0.05)
        b.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.097, 0.1, 0.13), R=rot_from_axes(z_axis=el - sh)), 0.04)
        b.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028)
        b.add(RoundCone(el, wr, 0.08, 0.058), 0.035)
        b.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.1, 0.09, 0.135), R=rot_from_axes(z_axis=wr - el)), 0.04)
    return b


ARM_LEN = float(np.linalg.norm(J["elbow_R"] - J["shoulder_R"]) + np.linalg.norm(J["wrist_R"] - J["elbow_R"]))


def _sleeve_cut(P):
    """> 0 past the sleeves' ends (a little short of the wrist; the gauntlets' cuffs cover them), only near his arms."""
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2 = _arm_coord(P, side)
        near = (d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3))
        out = np.maximum(out, np.where(near, s - F(ARM_LEN - 0.035), F(-1.0)))
    return out


def tunic_neck(P):
    """> 0 above the tunic's neck (round the neck only; it lifts clear of the shoulders)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.18), 0, 1)
    return z - (F(1.415) - F(0.015) * front + F(0.3) * smoothstep(0.15, 0.22, np.abs(x)))


def tunic_hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(TUNIC_HEM) + F(0.006) * np.cos(a * 2) + F(0.004) * NOISE(P * F(8))


def tunic_keep(P):
    k = np.maximum(tunic_hem(P) - P[:, 2], tunic_neck(P))
    return np.maximum(k, _sleeve_cut(P))


def tunic_outer():
    b = tunic_hull()
    return Func(lambda P: b.eval(P, margin=0.1) - F(TUNIC_OFF + TUNIC_T / 2), (-1, -0.6, 0.5), (1, 0.6, 1.7))


BUTTON_Z = (1.36, 1.29, 1.22, 1.15, 1.08, 0.88, 0.77)          # down the front (the belt hides the waist)
POCKETS = ((-0.125, 1.24), (0.125, 1.24))


def tunic_field():
    """Navy wool (0): the body to the upper thigh, its sleeves to the wrists, buttoned down the front with brass buttons
    (6) on a placket, two breast pockets with buttoned flaps; a scarlet standing collar (5) hooked at the throat."""
    fd = Field("Tunic")
    base = tunic_hull()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        return (F(0.0025) * np.sin(a * F(9) + F(0.9) * NOISE(P * F(3))) * smoothstep(0.95, 0.7, P[:, 2])
                + F(0.0012) * NOISE(P * F(20)))
    fd.add(Inter(Shell(base, TUNIC_OFF, TUNIC_T, pad=0.12, disp=folds, disp_amp=0.004),
                 Func(tunic_keep, (-1, -0.6, 0.5), (1, 0.6, 1.7)), 0.004), 0.0)
    outer = tunic_outer()
    # the placket: a raised strip down the front, the buttons on it
    pts = []
    for z in np.linspace(1.4, TUNIC_HEM + 0.01, 12):
        h, ok = ray_hit(outer, [v3((0.0, -0.7, z))], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            pts.append(h[0] + v3((0, 0.002, 0)))
    fd.add(Lock(pts, [0.026] * len(pts), [0.0045] * len(pts), [v3((0, -1, 0))] * len(pts), k=0.004), 0.004)
    for z in BUTTON_Z:
        h, ok = ray_hit(outer, [v3((0.0, -0.7, z))], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            fd.add(Sphere(h[0] + v3((0, -0.004, 0)), 0.0115), 0.002, BRASS_L)
    # breast pockets: a patch with a box pleat, a pointed flap, a button
    for x, z in POCKETS:
        h, ok = ray_hit(outer, [v3((x, -0.7, z))], [v3((0, 1, 0))], tmax=0.8)
        if not ok[0]:
            continue
        c = h[0]
        nrm = norm(v3((x * 0.6, -1.0, 0.1)))
        R = rot_from_axes(z_axis=(0, 0, 1), y_axis=-nrm)
        fd.add(RoundBox(c + v3((0, 0.004, -0.045)), (0.058, 0.006, 0.06), 0.006, R=R), 0.006)
        fd.add(RoundBox(c + v3((0, -0.006, 0.026)), (0.064, 0.007, 0.022), 0.006, R=R), 0.004)
        fd.add(RoundCone(c + v3((0, -0.008, 0.012)), c + v3((0, -0.009, 0.0)), 0.016, 0.008), 0.004)          # the flap's point
        fd.add(Sphere(c + v3((0, -0.016, 0.006)), 0.0085), 0.002, BRASS_L)
    # the standing collar: a scarlet band round the neck, closed at the throat with a brass hook
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    def band(P):
        return np.maximum(F(1.37) - P[:, 2] + F(0.02) * np.clip(P[:, 1] / F(0.1), -1, 1),
                          P[:, 2] - F(1.47) - F(0.01) * np.clip(P[:, 1] / F(0.1), -1, 1))
    fd.add(Inter(Shell(nk, 0.02, 0.016, pad=0.08), Func(band, (-0.3, -0.3, 1.3), (0.3, 0.3, 1.55)), 0.004), 0.004, FACING)
    h, ok = ray_hit(Func(lambda P: nk.eval(P, margin=0.05) - F(0.024), (-0.3, -0.3, 1.3), (0.3, 0.3, 1.55)),
                    [v3((0.0, -0.6, 1.43))], [v3((0, 1, 0))], tmax=0.7)
    if ok[0]:
        fd.add(Sphere(h[0] + v3((0, -0.002, 0)), 0.008), 0.002, BRASS_L)
    return fd


# ======================================================================================= trousers
def legs_hull():
    b = Field("LegsHull")
    tp = torso_prims()
    b.add(tp[5][0], 0.0)
    b.add(tp[4][0], 0.08)
    for side in ("R", "L"):
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        b.add(RoundCone(hip, kn, 0.14, 0.092), 0.065)
        b.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.13, 0.12, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.048)
        b.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038)
        b.add(RoundCone(kn, an, 0.088, 0.058), 0.038)
        b.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043)
    return b


TROUSER_TOP, TROUSER_BOT = 0.98, 0.38


def _seam_stripe(P):
    """< 0 on the scarlet stripe down each leg's outer seam."""
    out = None
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        z = P[:, 2]
        t1 = np.clip((F(hip[2]) - z) / F(hip[2] - kn[2]), 0, 1)
        t2 = np.clip((F(kn[2]) - z) / F(kn[2] - an[2]), 0, 1)
        cy = np.where(z > F(kn[2]), F(hip[1]) + (F(kn[1]) - F(hip[1])) * t1, F(kn[1]) + (F(an[1]) - F(kn[1])) * t2)
        cx = np.where(z > F(kn[2]), F(hip[0]) + (F(kn[0]) - F(hip[0])) * t1, F(kn[0]) + (F(an[0]) - F(kn[0])) * t2)
        d = np.maximum(np.abs(P[:, 1] - cy) - F(0.011), F(sx) * (cx - P[:, 0]))
        out = d if out is None else np.minimum(out, d)
    return out


def trousers_field():
    """Navy wool trousers (0), straight in the leg, a scarlet stripe down the outer seams (5), tucked into his boots."""
    fd = Field("Trousers")
    hull = legs_hull()
    lo, hi = v3((-0.5, -0.4, 0.25)), v3((0.5, 0.45, 1.1))
    def off(z):
        return F(0.014) + F(0.014) * smoothstep(0.42, 0.56, z)
    def fn(P):
        d = hull.eval(P, margin=0.1)
        return np.abs(d - off(P[:, 2])) - F(0.01)
    folds = lambda P: (F(0.004) * np.sin(np.arctan2(P[:, 1] - F(0.03), np.abs(P[:, 0]) - F(0.17)) * F(6) + P[:, 2] * F(26)
                                         + F(0.8) * NOISE(P * F(4))) * smoothstep(0.4, 0.55, P[:, 2]) + F(0.0012) * NOISE(P * F(25)))
    fd.add(Inter(Func(fn, lo, hi, disp=folds, disp_amp=0.005),
                 Func(lambda P: np.maximum(P[:, 2] - F(TROUSER_TOP), F(TROUSER_BOT) - P[:, 2]), lo, hi), 0.004), 0.0)
    fd.paint(Func(_seam_stripe, lo, hi), FACING)
    return fd


# ======================================================================================= leather: boots, belt, gauntlets, strap
BELT_Z = 0.95


def boot_hull(side):
    ft = Field("BootHull")
    foot(ft, side)
    kn, an = J["knee_" + side], J["ankle_" + side]
    ft.add(RoundCone(kn, an, 0.088, 0.058), 0.03)
    ft.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043)
    ft.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038)
    return ft


def _hand_hull(side):
    f = Field("HandHull")
    hand(f, side)
    f.add(Sphere(J["wrist_" + side], 0.045), 0.03)
    return f


def belt_hull():
    b = Field("BeltHull")
    tb = tunic_hull()
    b.add(Func(lambda P: tb.eval(P, margin=0.12) - F(TUNIC_OFF + TUNIC_T / 2), (-0.5, -0.45, 0.82), (0.5, 0.45, 1.08)), 0.0)
    return b


def buckle_c():
    bh = belt_hull()
    h, ok = ray_hit(bh, [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    return h[0] if ok[0] else v3((0, -0.3, BELT_Z))


def leather_field():
    """Brown leather (0): knee boots with thick soles and heels; a broad belt over the tunic with a brass buckle (6);
    gauntlets with flared cuffs over the sleeves' ends; the strap of his field glasses round his neck."""
    fd = Field("Leather")
    crease = lambda P: F(0.0016) * NOISE(P * F(26))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an, kn = J["ankle_" + side], J["knee_" + side]
        ft = boot_hull(side)
        top = lambda P, kn=kn: P[:, 2] - (F(0.5) + F(0.035) * np.clip(-(P[:, 1] - F(kn[1])) / F(0.09), -1, 1))
        fd.add(Inter(Shell(ft, 0.018, 0.013, pad=0.07, disp=crease, disp_amp=0.002),
                     Func(top, an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.6))), 0.004), 0.0)
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.098)), (0.084, 0.168, 0.017), 0.01, R=Rz), 0.006)
        fd.add(RoundBox(an + fwd * -0.035 + v3((0, 0, -0.08)), (0.062, 0.052, 0.032), 0.012, R=Rz), 0.008)          # the heel
    # the belt and its buckle
    bh = belt_hull()
    fd.add(Inter(Shell(bh, 0.009, 0.012, pad=0.06), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(0.034), (-0.6, -0.5, 0.8), (0.6, 0.5, 1.1)), 0.004), 0.0)
    c = buckle_c()
    R = rot_from_axes(z_axis=(0, -1, 0), y_axis=(0, 0, 1))
    fd.add(RoundBox(c + v3((0, -0.012, 0)), (0.042, 0.034, 0.006), 0.006, R=R), 0.004, BRASS_L)
    fd.sub(RoundBox(c + v3((0, -0.02, 0)), (0.026, 0.02, 0.006), 0.004, R=R), 0.002)
    fd.add(RoundBox(c + v3((0, -0.014, 0)), (0.004, 0.022, 0.004), 0.002, R=R), 0.002, BRASS_L)              # the prong
    # gauntlets, their cuffs flaring over the sleeves' ends
    for side in ("R", "L"):
        hh = _hand_hull(side)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        fd.add(Shell(hh, 0.004, 0.006, pad=0.04, disp=crease, disp_amp=0.001), 0.0)
        fd.add(Inter(Shell(RoundCone(wr - ax * 0.11, wr + ax * 0.01, 0.104, 0.074), 0.0, 0.009, pad=0.04),
                     Func(lambda P, wr=wr, ax=ax: np.abs((P - (wr - ax * 0.05).astype(F)) @ ax.astype(F)) - F(0.06), wr - 0.25, wr + 0.25), 0.003), 0.004)
    # the field glasses' strap: from their eyes round the back of his neck
    for p in strap_paths():
        nn = [norm(v3((q[0] * 2.0, q[1] - 0.06, 0.4))) for q in p]
        fd.add(Lock(p, [0.014] * len(p), [0.0035] * len(p), nn, k=0.004), 0.003)
    return fd


# ======================================================================================= the field glasses (on their own bone)
def glasses_frame():
    """The glasses' middle G on his chest (rest pose), across (Xg, along X), up their barrels toward the eyepieces (Ug,
    lying on his chest: up and a little out), Ng out of his chest."""
    outer = tunic_outer()
    h, ok = ray_hit(outer, [v3((0.0, -0.7, 1.13))], [v3((0, 1, 0))], tmax=0.8)
    p = h[0] if ok[0] else v3((0.0, -0.3, 1.13))
    Ng = norm(v3((0.0, -1.0, 0.25)))
    Ug = norm(np.cross(Ng, v3((1, 0, 0))) * -1.0)
    if Ug[2] < 0:
        Ug = -Ug
    return p + Ng * 0.034, v3((1, 0, 0)), Ug, Ng


GL_SEP = 0.034              # each barrel's axis from the middle
GL_LEN = 0.09               # objective -> eyepiece


def glasses_field():
    """Field glasses: two black-enamelled barrels (8) on a hinge, brass rims and focusing wheel (6), the eyepieces up
    (toward his chin), the objectives down; the strap's eyes on their sides."""
    fd = Field("Glasses")
    G, X, U, N = glasses_frame()
    for s in (-1, 1):
        a = G + X * (s * GL_SEP) - U * (GL_LEN * 0.5)
        b = G + X * (s * GL_SEP) + U * (GL_LEN * 0.5)
        fd.add(RoundCone(a + U * 0.012, b - U * 0.022, 0.026, 0.022), 0.0, IRON_L)               # the barrel
        fd.add(Cylinder(a + U * 0.008, 0.028, 0.016, rr=0.004, R=rot_from_axes(z_axis=U)), 0.003, BRASS_L)    # objective rim
        fd.sub(Cylinder(a, 0.02, 0.008, R=rot_from_axes(z_axis=U)), 0.002)
        fd.add(Cylinder(b - U * 0.014, 0.016, 0.026, rr=0.004, R=rot_from_axes(z_axis=U)), 0.003, IRON_L)    # the eyepiece
        fd.add(Torus(b - U * 0.004, 0.014, 0.003, R=rot_from_axes(z_axis=U)), 0.002, BRASS_L)
        fd.add(Sphere(G + X * (s * (GL_SEP + 0.026)) + U * 0.01, 0.006), 0.002, BRASS_L)            # strap eyes
    fd.add(Cylinder(G + U * 0.012, 0.012, 2 * GL_SEP, rr=0.003, R=rot_from_axes(z_axis=X)), 0.004, IRON_L)     # the hinge
    fd.add(Cylinder(G + U * 0.03 + N * 0.006, 0.011, 0.02, rr=0.003, R=rot_from_axes(z_axis=X)), 0.003, BRASS_L)   # focus wheel
    return fd


def strap_paths():
    """The strap's two halves: from each eye of the glasses up over his collarbones to the back of his neck."""
    G, X, U, N = glasses_frame()
    th = tunic_hull()
    outer = Func(lambda P: th.eval(P, margin=0.1) - F(TUNIC_OFF + TUNIC_T + 0.004), (-0.6, -0.6, 0.9), (0.6, 0.6, 1.7))
    out = []
    for s in (-1, 1):
        e = G + X * (s * (GL_SEP + 0.026)) + U * 0.01
        pts = [e]
        for x, y, z in ((0.075, -0.24, 1.26), (0.11, -0.17, 1.38), (0.12, -0.05, 1.45), (0.09, 0.08, 1.46), (0.0, 0.13, 1.44)):
            o = v3((s * x, y, z))
            d = norm(v3((s * x, y - 0.05, 0.0)) + v3((0, 0, 0.6)))
            h, ok = ray_hit(outer, [o + d * 0.4], [-d], tmax=0.6)
            pts.append(h[0] if ok[0] else o)
        if s > 0:
            pts = pts[:-1]
        out.append(pts)
    return out


# ======================================================================================= the gun (layout)
MX = 0.8                    # the gun's centre line (x); it shoots toward -Y
AY = -0.62                  # the axle (y)
WR = 0.44                   # the wheels' radius (to the tyres' tread)
WX = 0.48                   # the wheels' mid planes (x, from MX)
ELEV = math.radians(3.0)    # the barrel's elevation (the muzzle up)
GD = v3((0.0, -math.cos(ELEV), math.sin(ELEV)))     # along the bore, toward the muzzle
GU = v3((0.0, math.sin(ELEV), math.cos(ELEV)))      # up, across the bore
GX_ = v3((1.0, 0.0, 0.0))
TRUN = v3((MX, AY + 0.1, 0.74))                     # the cradle's trunnions (it elevates about them)
BAR_UP = 0.085              # the barrel's axis above the trunnions
CYL_UP = -0.04              # the recoil cylinder's axis
S_MUZ = 0.98                # trunnions -> the muzzle's face (along the bore)
S_BR = -0.42                # ... the breech ring's rear face
S_RING = -0.2               # ... its front face
S_BLK = S_BR + 0.06         # ... the sliding block's middle
BLK_HALF = (0.13, 0.034, 0.075)
BLK_SLIDE = 0.18            # how far the block slides out (toward +X, away from him) to open
S_CASE = S_BR + 0.098       # the cartridge case's base in the chamber
CASE_L, CASE_R, RIM_R = 0.27, 0.043, 0.05
SHELL_L = 0.45              # a fixed round: base -> the fuse's tip
BORE_R = 0.036
RING_HALF = (0.118, 0.108)  # the breech ring's half width and half height


def bore_pt(s, up=0.0, side=0.0):
    return TRUN + GD * s + GU * (BAR_UP + up) + GX_ * side


def cyl_pt(s, up=0.0, side=0.0):
    return TRUN + GD * s + GU * (CYL_UP + up) + GX_ * side


MUZZLE = bore_pt(S_MUZ)
BLK_C = bore_pt(S_BLK, side=BLK_HALF[0] - RING_HALF[0])            # (closed: flush with the ring's right side)
LEV_P = bore_pt(S_BR + 0.085, up=0.02, side=-(RING_HALF[0] + 0.012))    # the breech lever's pivot
LEV_L = 0.16
CORD_A = v3((MX - 0.135 - 0.011 - 0.024, AY + 0.12, 0.72))              # the lanyard's eye (on the right saddle plate)
LAN_L = 0.17                # the lanyard's rest length (hanging)
TOG0 = CORD_A + v3((0.0, 0.0, -LAN_L))
HW_C = v3((MX - 0.25, AY + 0.3, 0.66))                                  # the elevating handwheel's hub
HW_R = 0.085
KICK_P = v3((MX, AY + 1.0, 0.0))                                        # the spade: the gun rocks about it at the shot
CRATE_C = v3((-0.13, -0.02, 0.24))                                       # the ready-use box (floor middle), on his right ...
CRATE_HALF = (0.15, 0.26, 0.24)                                          # (its length along Y) ...
CRATE_LOW = 0.24                                                         # ... on top of a closed one
CRATE_ROUNDS = (-0.08, 0.0, 0.08)                                        # the top layer of rounds (x from its middle); he takes the last
SH_A0 = v3((0.0, 1.0, 0.0))                                              # (rest) the round's axis, base -> fuse (noses to the back)
SH_BASE0 = CRATE_C + v3((CRATE_ROUNDS[-1], -0.225, CRATE_HALF[2] - 0.035))   # (rest) its base's middle


def hub_c(sx):
    return v3((MX + sx * WX, AY, WR))


def _rgd(z=GU):
    return rot_from_axes(z_axis=z, y_axis=GD)


# ======================================================================================= the barrel, block, lever
def barrel_field():
    """Gunmetal-grey steel (5): the square breech ring with the slot for the sliding block and the chamber's mouth, the
    jacket with a reinforce ring, the long tube, the swelled muzzle; the slides under the jacket; a brass maker's plate
    on the ring (6)."""
    fd = Field("Barrel")
    sc = lambda P: F(0.0005) * NOISE(P * F(60))
    rc = bore_pt(0.5 * (S_BR + S_RING))
    fd.add(RoundBox(rc, (RING_HALF[0], 0.5 * (S_RING - S_BR), RING_HALF[1]), 0.02, R=_rgd(), disp=sc, disp_amp=0.001), 0.0, GREY_L)
    fd.add(capped_cone(bore_pt(S_RING - 0.02), bore_pt(0.36), 0.092, 0.08, rr=0.01), 0.012, GREY_L)        # the jacket
    fd.add(Cylinder(bore_pt(S_RING + 0.02), 0.099, 0.04, rr=0.01, R=rot_from_axes(z_axis=GD)), 0.004, GREY_L)
    fd.add(Cylinder(bore_pt(0.34), 0.088, 0.03, rr=0.008, R=rot_from_axes(z_axis=GD)), 0.004, GREY_L)
    fd.add(capped_cone(bore_pt(0.32), bore_pt(0.91), 0.066, 0.056, rr=0.008), 0.01, GREY_L)                # the tube
    fd.add(capped_cone(bore_pt(0.87), bore_pt(S_MUZ), 0.057, 0.067, rr=0.01), 0.008, GREY_L)               # the muzzle's swell
    fd.add(Cylinder(bore_pt(S_MUZ - 0.012), 0.069, 0.016, rr=0.006, R=rot_from_axes(z_axis=GD)), 0.003, GREY_L)
    fd.sub(Cylinder(bore_pt(S_MUZ - 0.2), BORE_R, 0.42, R=rot_from_axes(z_axis=GD)), 0.004)                # the bore
    # the slides under the jacket (they run on the cradle)
    fd.add(RoundBox(bore_pt(0.06, up=-0.082), (0.06, 0.26, 0.016), 0.006, R=_rgd()), 0.006, GREY_L)
    # the slot for the block (through the ring from side to side) and the chamber's mouth behind it
    fd.sub(RoundBox(bore_pt(S_BLK), (0.3, BLK_HALF[1] + 0.003, BLK_HALF[2] + 0.003), 0.004, R=_rgd()), 0.003)
    fd.sub(Cylinder(bore_pt(S_BR + 0.03), RIM_R + 0.004, 0.08, R=rot_from_axes(z_axis=GD)), 0.004)
    fd.sub(Cylinder(bore_pt(S_CASE + 0.12), CASE_R + 0.003, 0.3, R=rot_from_axes(z_axis=GD)), 0.003)
    # a brass plate on the ring's top, a lifting eye in front of it
    fd.add(RoundBox(bore_pt(0.5 * (S_BR + S_RING) + 0.01, up=RING_HALF[1]), (0.05, 0.06, 0.006), 0.003, R=_rgd()), 0.003, BRASS_L)
    fd.add(Torus(bore_pt(S_RING + 0.08, up=0.1), 0.025, 0.007, R=rot_from_axes(z_axis=GX_)), 0.004, GREY_L)
    return fd


def block_field():
    """The sliding breech block: bright machined steel (7), a firing-pin boss on its back, a grip on its left end (8)."""
    fd = Field("Block")
    fd.add(RoundBox(BLK_C, BLK_HALF, 0.008, R=_rgd()), 0.0, STEEL_L)
    fd.add(Cylinder(BLK_C - GX_ * (BLK_HALF[0] - RING_HALF[0]) - GD * BLK_HALF[1], 0.022, 0.016, rr=0.004, R=rot_from_axes(z_axis=GD)), 0.003, STEEL_L)
    e = BLK_C + GX_ * BLK_HALF[0]
    fd.add(RoundBox(e + GX_ * 0.008, (0.012, 0.03, 0.05), 0.006, R=_rgd()), 0.003, IRON_L)
    return fd


def lever_field():
    """The breech lever on the ring's right side: a flat bar (8) from its pivot boss forward, a brass knob (6)."""
    fd = Field("Lever")
    Rx = rot_from_axes(z_axis=GX_)
    fd.add(Cylinder(LEV_P, 0.026, 0.024, rr=0.006, R=Rx), 0.0, IRON_L)
    a, b = LEV_P, LEV_P + GD * LEV_L
    fd.add(RoundBox(lerp(a, b, 0.5), (0.008, LEV_L * 0.5, 0.013), 0.005, R=_rgd()), 0.006, IRON_L)
    fd.add(Sphere(b + GX_ * -0.01, 0.022), 0.006, BRASS_L)
    fd.add(Cylinder(LEV_P - GX_ * 0.014, 0.012, 0.01, rr=0.003, R=Rx), 0.002, BRASS_L)
    return fd


# ======================================================================================= the cradle
def cradle_field():
    """Olive drab (0): the bed the barrel slides on, the recoil cylinder under it (grey, 5) with its end caps, the
    trunnions; the brass telescope sight (6) on a bracket at the right, black eyecup and rings (8); the firing gear (8)
    with the lanyard's eye at its back."""
    fd = Field("Cradle")
    fd.add(RoundBox(bore_pt(0.26, up=-0.112), (0.078, 0.47, 0.022), 0.008, R=_rgd()), 0.0, OLIVE_L)
    for sx in (-1, 1):                                                                   # the bed's side rails
        fd.add(RoundBox(bore_pt(0.26, up=-0.09, side=sx * 0.07), (0.012, 0.47, 0.024), 0.006, R=_rgd()), 0.004, OLIVE_L)
    fd.add(capped_cone(cyl_pt(-0.27), cyl_pt(0.72), 0.058, 0.054, rr=0.012), 0.008, GREY_L)                # the cylinder
    for s, R in ((-0.25, 0.062), (0.7, 0.059)):
        fd.add(Cylinder(cyl_pt(s), R, 0.03, rr=0.008, R=rot_from_axes(z_axis=GD)), 0.003, GREY_L)
    fd.add(Cylinder(cyl_pt(0.735), 0.03, 0.02, rr=0.006, R=rot_from_axes(z_axis=GD)), 0.003, STEEL_L)      # the rod's nut
    fd.add(RoundBox(TRUN + GU * 0.02, (0.1, 0.12, 0.07), 0.016, R=_rgd()), 0.012, OLIVE_L)                # the trunnion block
    fd.add(Cylinder(TRUN, 0.036, 0.3, rr=0.006, R=rot_from_axes(z_axis=GX_)), 0.004, OLIVE_L)
    # the sight: a bracket up from the cradle's right, a brass telescope along the bore
    t0 = TRUN + GD * -0.08 + GU * 0.02 + GX_ * -0.09
    t1 = TRUN + GD * -0.08 + GU * 0.23 + GX_ * -0.185
    fd.add(Chain([t0, lerp(t0, t1, 0.5) + GX_ * -0.03, t1], [0.018, 0.016, 0.014], k=0.006), 0.006, OLIVE_L)
    sc = TRUN + GU * 0.25 + GX_ * -0.185
    fd.add(capped_cone(sc + GD * -0.25, sc + GD * 0.08, 0.021, 0.026, rr=0.005), 0.004, BRASS_L)
    fd.add(Cylinder(sc + GD * 0.075, 0.03, 0.02, rr=0.005, R=rot_from_axes(z_axis=GD)), 0.003, BRASS_L)
    fd.sub(Cylinder(sc + GD * 0.086, 0.018, 0.01, R=rot_from_axes(z_axis=GD)), 0.002)
    fd.add(capped_cone(sc + GD * -0.3, sc + GD * -0.24, 0.022, 0.02, rr=0.006), 0.004, IRON_L)          # the eyecup
    for s in (-0.17, -0.02):
        fd.add(Torus(sc + GD * s, 0.025, 0.006, R=rot_from_axes(z_axis=GD)), 0.002, IRON_L)
    return fd


# ======================================================================================= the carriage, shield and trail
# a saddle plate's side profile (y relative to the axle, z), counter-clockwise seen from +X
SADDLE = [(-0.15, 0.38), (0.36, 0.38), (0.46, 0.5), (0.4, 0.6), (0.22, 0.79), (-0.02, 0.8), (-0.15, 0.62)]
SADDLE_X, SADDLE_T = 0.135, 0.022
TRAIL_A = v3((MX, AY + 0.3, 0.45))          # the box trail's top middle at the saddle ...
TRAIL_B = v3((MX, AY + 0.98, 0.1))          # ... and at the spade
TRAIL_W = (0.12, 0.075)                     # its half width, there and at the spade
TRAIL_H = (0.075, 0.05)                     # its half height
SH_Y = AY - 0.17                            # the shield's foot (y)
SH_Z0 = 0.42                                # ... and its height
SH_TILT = math.radians(8.0)                 # leaning back
SH_N = v3((0.0, -math.cos(SH_TILT), math.sin(SH_TILT)))     # out of its face (forward)
SH_V = v3((0.0, math.sin(SH_TILT), math.cos(SH_TILT)))      # up its face
SH_P0 = v3((MX, SH_Y, SH_Z0))
SHIELD = [(-0.43, 0.0), (0.43, 0.0), (0.43, 0.6), (0.3, 0.74), (-0.3, 0.74), (-0.43, 0.6)]   # its outline (u across, v up)
APERTURE = (0.12, 0.17, 0.56)               # the barrel's aperture: half width, from v, to v
SLOT = (-0.185, 0.05, 0.022)                # the sighting slot: u, half width, half height (v at the sight's line)
SH_T = 0.018


def sh_pt(u, v, w=0.0):
    return SH_P0 + GX_ * u + SH_V * v + SH_N * w


def _slot_v():
    sc = TRUN + GU * 0.25
    return float((sc[2] - SH_Z0) / math.cos(SH_TILT)) - 0.006


def _shield_uv(P):
    q = P - SH_P0.astype(F)
    return q @ GX_.astype(F), q @ SH_V.astype(F), q @ SH_N.astype(F)


def _rrect(u, v, cu, cv, hu, hv, r):
    du, dv = np.abs(u - F(cu)) - F(hu - r), np.abs(v - F(cv)) - F(hv - r)
    return np.minimum(np.maximum(du, dv), F(0)) + np.sqrt(np.maximum(du, 0) ** 2 + np.maximum(dv, 0) ** 2) - F(r)


def shield_sd(P):
    u, v, w = _shield_uv(P)
    d2 = poly2d(SHIELD)(u, v)
    ap = _rrect(u, v, 0.0, 0.5 * (APERTURE[1] + APERTURE[2]), APERTURE[0], 0.5 * (APERTURE[2] - APERTURE[1]), 0.05)
    sl = _rrect(u, v, SLOT[0], _slot_v(), SLOT[1], SLOT[2], 0.008)
    d2 = np.maximum(d2, -np.minimum(ap, sl))
    dw = np.abs(w) - F(SH_T / 2)
    r = F(0.006)
    w0, w1 = d2 + r, dw + r
    return np.minimum(np.maximum(w0, w1), F(0)) + np.sqrt(np.maximum(w0, 0) ** 2 + np.maximum(w1, 0) ** 2) - r


def saddle_func(sx):
    xc = MX + sx * SADDLE_X
    p2 = poly2d(SADDLE)
    r = 0.01
    def fn(P):
        d2 = p2(P[:, 1] - F(AY), P[:, 2])
        dx = np.abs(P[:, 0] - F(xc)) - F(SADDLE_T / 2)
        w0, w1 = d2 + F(r), dx + F(r)
        return np.minimum(np.maximum(w0, w1), F(0)) + np.sqrt(np.maximum(w0, 0) ** 2 + np.maximum(w1, 0) ** 2) - F(r)
    return Func(fn, (xc - 0.05, AY - 0.2, 0.3), (xc + 0.05, AY + 0.5, 0.85))


def trail_sd(P):
    ax = TRAIL_B - TRAIL_A
    L = float(np.linalg.norm(ax))
    a = norm(ax)
    up = norm(np.cross(GX_, a)) * -1.0
    if up[2] < 0:
        up = -up
    q = P - TRAIL_A.astype(F)
    t = q @ a.astype(F)
    k = np.clip(t / F(L), 0, 1)
    w = F(TRAIL_W[0]) + F(TRAIL_W[1] - TRAIL_W[0]) * k
    h = F(TRAIL_H[0]) + F(TRAIL_H[1] - TRAIL_H[0]) * k
    dx = np.abs(q[:, 0]) - w
    dz = np.abs(q @ up.astype(F) + h) - h                   # (its top is the line A-B)
    dt = np.maximum(-t - F(0.1), t - F(L))
    r = F(0.012)
    qq = np.stack([dx + r, dz + r, dt + r], 1)
    return np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0) - r


def trail_frame():
    ax = TRAIL_B - TRAIL_A
    a = norm(ax)
    up = norm(np.cross(GX_, a)) * -1.0
    if up[2] < 0:
        up = -up
    return a, up, float(np.linalg.norm(ax))


def carriage_field():
    """Olive drab steel (0): the saddle's two side plates over the axle carrying the trunnions (brass oil cups, 6), the
    axle-tree, the box trail to the spade (rivets along its edges), the spade dug into the ground, the trail's eye (8);
    the shield of riveted plate with its aperture and sighting slot (a grey shutter, 5) and a brass maker's plate, its stays,
    the apron below the axle; the elevating handwheel's shaft out of the right side plate."""
    fd = Field("Carriage")
    rv = lambda: None
    for sx in (-1, 1):
        fd.add(saddle_func(sx), 0.0, OLIVE_L)
        xc = MX + sx * (SADDLE_X + SADDLE_T / 2 + 0.008)
        fd.add(Cylinder(v3((xc, TRUN[1], TRUN[2])), 0.05, 0.03, rr=0.008, R=rot_from_axes(z_axis=GX_)), 0.004, OLIVE_L)   # bearing cap
        fd.add(Cylinder(v3((MX + sx * SADDLE_X, TRUN[1], TRUN[2] + 0.07)), 0.012, 0.03, rr=0.004), 0.003, BRASS_L)          # oil cup
        for yb, zb in ((-0.08, 0.45), (0.12, 0.45), (0.32, 0.45), (0.0, 0.7), (0.2, 0.7)):
            fd.add(Sphere(v3((xc - sx * 0.006, AY + yb, zb)), 0.0085), 0.002, OLIVE_L)
    fd.add(RoundBox(v3((MX, AY, WR)), (SADDLE_X + 0.02, 0.06, 0.055), 0.014), 0.006, OLIVE_L)                   # the axle-tree
    fd.add(Cylinder(v3((MX, AY, WR)), 0.036, 2 * (WX + 0.06), rr=0.006, R=rot_from_axes(z_axis=GX_)), 0.004, GREY_L)
    # the box trail and its rivets
    fd.add(Func(trail_sd, (MX - 0.2, AY + 0.1, -0.05), (MX + 0.2, AY + 1.2, 0.6)), 0.01, OLIVE_L)
    a, up, L = trail_frame()
    for k in range(9):
        t = 0.04 + (L - 0.08) * k / 8
        kk = t / L
        w = TRAIL_W[0] + (TRAIL_W[1] - TRAIL_W[0]) * kk
        for sx in (-1, 1):
            fd.add(Sphere(TRAIL_A + a * t + GX_ * (sx * (w + 0.002)) - up * 0.012, 0.0075), 0.002, OLIVE_L)
    # the spade: a broad plate braced under the trail's end, its edge dug into the ground; the trail's eye
    sp = TRAIL_B + a * 0.02 + v3((0.0, 0.0, -0.08))
    fd.add(RoundBox(sp, (0.16, 0.014, 0.1), 0.008, R=euler(-0.35, 0, 0)), 0.012, OLIVE_L)
    for sx in (-1, 1):
        fd.add(RoundBox(sp + v3((sx * 0.07, -0.05, 0.03)), (0.008, 0.05, 0.05), 0.004, R=euler(-0.35, 0, 0)), 0.006, OLIVE_L)
    fd.add(Torus(TRAIL_B + a * 0.07 + v3((0, 0, 0.0)), 0.04, 0.011), 0.004, IRON_L)
    # the shield, its rivets, the sighting slot's shutter, the maker's plate, the stays
    fd.add(Func(shield_sd, (MX - 0.5, SH_Y - 0.15, SH_Z0 - 0.05), (MX + 0.5, SH_Y + 0.2, SH_Z0 + 0.8)), 0.0, OLIVE_L)
    out = SH_T / 2 + 0.002
    edge = []
    for (u0, v0), (u1, v1) in zip(SHIELD, SHIELD[1:] + SHIELD[:1]):
        n = max(1, int(round(math.hypot(u1 - u0, v1 - v0) / 0.075)))
        for k in range(n):
            t = k / n
            u, v = u0 + (u1 - u0) * t, v0 + (v1 - v0) * t
            uu = u - math.copysign(0.03, u) if abs(u) > 0.05 else u
            vv = min(max(v, 0.03), 0.71)
            edge.append((uu, vv))
    for v in (0.3,):
        for k in range(12):
            u = -0.39 + 0.78 * k / 11
            if abs(u) > APERTURE[0] + 0.03:
                edge.append((u, v))
    for u, v in edge:
        fd.add(Sphere(sh_pt(u, v, out), 0.0085), 0.002, OLIVE_L)
    sv = _slot_v()
    fd.add(RoundBox(sh_pt(SLOT[0], sv + SLOT[2] + 0.018, out + 0.004), (SLOT[1] + 0.012, 0.016, 0.004), 0.003,
                    R=rot_from_axes(z_axis=SH_N, y_axis=SH_V)), 0.003, GREY_L)                              # the shutter, raised
    fd.add(RoundBox(sh_pt(0.25, 0.12, out), (0.05, 0.03, 0.004), 0.003, R=rot_from_axes(z_axis=SH_N, y_axis=SH_V)), 0.003, BRASS_L)
    for sx in (-1, 1):
        fd.add(Chain([sh_pt(sx * 0.24, 0.06, -SH_T / 2), v3((MX + sx * 0.2, AY - 0.02, WR + 0.03))], [0.014, 0.012], k=0.004), 0.006, OLIVE_L)
    # the apron below the axle
    ap = v3((MX, AY - 0.11, 0.25))
    fd.add(RoundBox(ap, (0.4, 0.009, 0.12), 0.006, R=euler(-0.08, 0, 0)), 0.0, OLIVE_L)
    for k in range(9):
        fd.add(Sphere(ap + v3((-0.36 + 0.09 * k, -0.012, 0.09)), 0.0075), 0.002, OLIVE_L)
    # the firing gear on the right side plate: a lever on a boss, the lanyard's eye at its end
    xs = MX - SADDLE_X - SADDLE_T / 2
    fd.add(Cylinder(v3((xs - 0.008, CORD_A[1] - 0.05, CORD_A[2] + 0.04)), 0.022, 0.016, rr=0.004, R=rot_from_axes(z_axis=GX_)), 0.003, IRON_L)
    fd.add(Chain([v3((xs - 0.014, CORD_A[1] - 0.05, CORD_A[2] + 0.04)), CORD_A + v3((0.004, 0, 0.012))], [0.009, 0.008], k=0.003), 0.003, IRON_L)
    fd.add(Torus(CORD_A + v3((0, 0, 0.004)), 0.011, 0.0035, R=rot_from_axes(z_axis=(0, 1, 0))), 0.002, IRON_L)
    # the elevating handwheel's shaft and boss on the right side plate
    xs = MX - SADDLE_X - SADDLE_T / 2
    fd.add(Cylinder(v3(((xs + HW_C[0]) / 2, HW_C[1], HW_C[2])), 0.016, abs(xs - HW_C[0]) - 0.02, rr=0.004, R=rot_from_axes(z_axis=GX_)), 0.004, GREY_L)
    fd.add(Cylinder(v3((xs - 0.012, HW_C[1], HW_C[2])), 0.036, 0.024, rr=0.006, R=rot_from_axes(z_axis=GX_)), 0.004, OLIVE_L)
    return fd


# ======================================================================================= the wheels and the handwheel
N_SPOKES = 12


def wheels_field():
    """Two big wheels: spokes and felloes painted olive drab (0) and dished outward, steel tyres worn bright (7) with
    their bolts (8), steel naves (5) with brass hub caps (6)."""
    fd = Field("Wheels")
    grain = lambda P: F(0.001) * NOISE(P * F(60))
    for sx in (-1, 1):
        c = hub_c(sx)
        fd.add(_ring_x(c, 0.404, WR, 0.036, 0.007), 0.0, STEEL_L)
        for k in range(16):
            a = 2 * math.pi * (k + 0.25) / 16
            d = v3((0, math.cos(a), math.sin(a)))
            fd.add(Sphere(c + d * (WR - 0.006) + v3((sx * 0.037, 0, 0)), 0.007), 0.002, IRON_L)
        fd.add(_ring_x(c + v3((sx * 0.004, 0, 0)), 0.33, 0.41, 0.03, 0.008), 0.004, OLIVE_L)
        for k in range(N_SPOKES):
            a = 2 * math.pi * k / N_SPOKES
            d = v3((0, math.cos(a), math.sin(a)))
            fd.add(RoundCone(c + d * 0.07 - v3((sx * 0.025, 0, 0)), c + d * 0.335 + v3((sx * 0.008, 0, 0)), 0.02, 0.015,
                             disp=grain, disp_amp=0.001), 0.008, OLIVE_L)
        fd.add(capped_cone(c - v3((sx * 0.1, 0, 0)), c + v3((sx * 0.02, 0, 0)), 0.068, 0.088, rr=0.014), 0.008, GREY_L)
        fd.add(capped_cone(c + v3((sx * 0.015, 0, 0)), c + v3((sx * 0.105, 0, 0)), 0.086, 0.062, rr=0.014), 0.008, GREY_L)
        fd.add(capped_cone(c + v3((sx * 0.1, 0, 0)), c + v3((sx * 0.15, 0, 0)), 0.056, 0.044, rr=0.012), 0.006, BRASS_L)
        for k in range(6):
            a = 2 * math.pi * k / 6
            fd.add(Sphere(c + v3((sx * 0.06, 0.07 * math.cos(a), 0.07 * math.sin(a))), 0.008), 0.002, GREY_L)
    return fd


def handwheel_field():
    """The elevating handwheel: a brass rim (6), four grey spokes and a hub (5), a wooden knob on a crank pin (9)."""
    fd = Field("Handwheel")
    Rx = rot_from_axes(z_axis=GX_)
    fd.add(Torus(HW_C, HW_R, 0.011, R=Rx), 0.0, BRASS_L)
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        d = v3((0, math.cos(a), math.sin(a)))
        fd.add(RoundCone(HW_C + d * 0.02, HW_C + d * (HW_R - 0.004), 0.009, 0.007), 0.005, GREY_L)
    fd.add(Cylinder(HW_C, 0.024, 0.04, rr=0.006, R=Rx), 0.005, GREY_L)
    k0 = knob_pt(0.0)
    fd.add(RoundCone(k0 + GX_ * 0.008, k0 - GX_ * 0.02, 0.008, 0.008), 0.003, GREY_L)
    fd.add(RoundCone(k0 - GX_ * 0.02, k0 - GX_ * 0.07, 0.013, 0.015), 0.004, WOOD_L)
    return fd


def knob_pt(phi):
    """The handwheel's knob (on its rim, the crank pin's root) at a turn phi from its rest (rest: up and to the front)."""
    a = math.radians(115.0) + phi
    return HW_C + v3((0.0, math.cos(a), math.sin(a))) * HW_R


KNOB_OUT = 0.045            # the knob's grip: this far out (-X) from the rim


# ======================================================================================= the lanyard, the rounds, the box
def lanyard_field():
    fd = Field("Lanyard")
    fd.add(RoundCone(CORD_A, TOG0 + v3((0, 0, 0.006)), 0.0055, 0.0055), 0.0, CORD_L)
    return fd


def toggle_field():
    """The lanyard's wooden toggle (9), its whipping (10)."""
    fd = Field("Toggle")
    fd.add(Cylinder(TOG0 + v3((0, 0, -0.004)), 0.013, 0.1, rr=0.006, R=rot_from_axes(z_axis=GX_)), 0.0, WOOD_L)
    fd.add(Torus(TOG0 + v3((0, 0, -0.004)), 0.014, 0.004, R=rot_from_axes(z_axis=GX_)), 0.002, CORD_L)
    return fd


def round_into(fd, base, A, k=0.0):
    """A fixed round: a brass case (6) with its rim, the grey shell (5) with a copper driving band (11), a brass fuse."""
    A = norm(A)
    R = rot_from_axes(z_axis=A)
    fd.add(Cylinder(base + A * 0.006, RIM_R, 0.012, rr=0.003, R=R), k, BRASS_L)
    fd.add(capped_cone(base + A * 0.008, base + A * CASE_L, CASE_R + 0.001, CASE_R - 0.002, rr=0.004), 0.004, BRASS_L)
    fd.add(capped_cone(base + A * (CASE_L - 0.012), base + A * 0.345, 0.04, 0.04, rr=0.004), 0.003, GREY_L)
    fd.add(Torus(base + A * 0.3, 0.04, 0.0055, R=R), 0.002, COPPER_L)
    fd.add(RoundCone(base + A * 0.34, base + A * 0.41, 0.039, 0.016), 0.006, GREY_L)
    fd.add(RoundCone(base + A * 0.405, base + A * (SHELL_L - 0.006), 0.016, 0.006), 0.003, BRASS_L)
    fd.add(Torus(base + A * 0.4, 0.017, 0.003, R=R), 0.001, BRASS_L)


def shell_field():
    fd = Field("Shell")
    round_into(fd, SH_BASE0, SH_A0)
    return fd


def case_field():
    """The spent case (6), open at its mouth (rest pose: in the chamber)."""
    fd = Field("Case")
    base = bore_pt(S_CASE)
    R = rot_from_axes(z_axis=GD)
    fd.add(Cylinder(base + GD * 0.006, RIM_R, 0.012, rr=0.003, R=R), 0.0, BRASS_L)
    fd.add(capped_cone(base + GD * 0.008, base + GD * CASE_L, CASE_R + 0.001, CASE_R - 0.002, rr=0.004), 0.004, BRASS_L)
    fd.sub(Cylinder(base + GD * CASE_L, CASE_R - 0.007, 0.08, R=R), 0.003)
    fd.add(Torus(base + GD * (CASE_L - 0.002), CASE_R - 0.005, 0.0035, R=R), 0.002, BRASS_L)
    return fd


def crate_field():
    """The ready-use box: pine boards (9) with board joints, iron corner plates (8), rope handles at its ends (10), its lid
    thrown down on the ground in front of it; full of rounds: the top layer lies on a rack (9) at its rim (two of them
    here; the third is the one he takes), noses to the back."""
    fd = Field("Crate")
    c = CRATE_C
    hx, hy, h = CRATE_HALF
    t = 0.018
    board = lambda P: F(0.0009) * NOISE(P * np.array([30, 6, 30], F))
    def box(P):
        q = P - c.astype(F)
        outer = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx), np.abs(q[:, 1]) - F(hy)), np.maximum(-q[:, 2], q[:, 2] - F(h)))
        inner = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx - t), np.abs(q[:, 1]) - F(hy - t)), F(h - 0.09) - q[:, 2])
        return np.maximum(outer, -inner)
    lo, hi = c - v3((hx + 0.03, hy + 0.03, 0.02)), c + v3((hx + 0.03, hy + 0.03, h + 0.03))
    fd.add(Func(box, lo, hi, disp=board, disp_amp=0.0015), 0.0, WOOD_L)
    # the closed box under it (a little askew), its lid nailed on with battens
    c2 = c - v3((0.0, 0.0, CRATE_LOW))
    R2 = euler(0, 0, 0.06)
    fd.add(RoundBox(c2 + v3((0.012, 0.0, CRATE_LOW / 2)), (hx + 0.01, hy + 0.01, CRATE_LOW / 2 - 0.002), 0.008, R=R2, disp=board, disp_amp=0.0012), 0.0, WOOD_L)
    for yy in (-0.17, 0.17):
        fd.add(RoundBox(c2 + R2 @ v3((0.0, yy, 0.0)) + v3((0.012, 0.0, CRATE_LOW + 0.004)), (hx + 0.012, 0.025, 0.008), 0.003, R=R2), 0.002, WOOD_L)
    for k in range(1, 3):
        z = CRATE_LOW * k / 3
        fd.sub(Func(lambda P, z=z: np.abs(P[:, 2] - F(c2[2] + z)) - F(0.0018), c2 - v3((hx + 0.05, hy + 0.05, 0.0)), c2 + v3((hx + 0.05, hy + 0.05, CRATE_LOW))), 0.001)
    for k in range(1, 4):                                                                   # board joints round the sides
        z = h * k / 4
        def joint(P, z=z):
            q = P - c.astype(F)
            ring = np.maximum(np.abs(q[:, 0]) - F(hx - 0.004), np.abs(q[:, 1]) - F(hy - 0.004))
            return np.maximum(np.abs(q[:, 2] - F(z)) - F(0.0018), -ring)
        fd.sub(Func(joint, lo, hi), 0.001)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(RoundBox(c + v3((sx * hx, sy * hy, h - 0.035)), (0.008, 0.008, 0.035), 0.003), 0.002, IRON_L)
            fd.add(RoundBox(c + v3((sx * hx, sy * hy, 0.035)), (0.008, 0.008, 0.035), 0.003), 0.002, IRON_L)
    for sy in (-1, 1):                                                                       # rope handles
        e = c + v3((0.0, sy * (hy + 0.012), h * 0.66))
        fd.add(Inter(Torus(e, 0.045, 0.007, R=rot_from_axes(z_axis=(0, 1, 0))), Plane(e + v3((0, 0, 0.01)), (0, 0, 1))), 0.002, CORD_L)
    # the lid, thrown down on the ground in front of the box (its hinges at the box's front edge)
    lid_c = c + v3((0.0, -hy - 0.1, 0.035 - CRATE_LOW))
    fd.add(RoundBox(lid_c, (hx + 0.006, 0.09, 0.012), 0.004, R=euler(-0.3, 0, 0), disp=board, disp_amp=0.0012), 0.004, WOOD_L)
    for sx in (-1, 1):
        fd.add(RoundBox(lid_c + v3((sx * 0.08, 0.0, 0.018)), (0.012, 0.07, 0.004), 0.002, R=euler(-0.3, 0, 0)), 0.002, IRON_L)
    # the rack under the top layer, the two rounds left on it
    for yy in (-0.15, 0.13):
        fd.add(RoundBox(c + v3((0.0, yy, SH_BASE0[2] - c[2] - RIM_R + 0.004)), (hx - t - 0.002, 0.02, 0.012), 0.004), 0.003, WOOD_L)
    for x in CRATE_ROUNDS[:-1]:
        round_into(fd, SH_BASE0 + v3((x - CRATE_ROUNDS[-1], 0.0, 0.0)), SH_A0, k=0.002)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.618)), 0.07, 0.95)]                                   # a ruddy nose
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.11, -0.15, 1.636)), 0.07, 0.85), (hp((sx * 0.18, 0.035, 1.664)), 0.055, 0.6),
                (hp((sx * 0.05, -0.18, 1.79)), 0.08, 0.35), (hp((0.0, -0.17, 1.5)), 0.06, 0.3)]
    return pts


# ======================================================================================= build config
GLB_NAME = "field_gun"
ROOT_NAME = "FieldGunHQ"
TEX_PREFIX = "field_gun"
MAT_NAME = "FieldGunMat"
MESH_NAME = "FieldGun"
BASE_MODULE = "field_gun_base"
ANIM_MODULE = "anim_field_gun"
PARTS = ["Skin", "Eyes", "Whiskers", "Hair", "Cap", "Tunic", "Trousers", "Leather", "Glasses", "Barrel", "Block", "Lever",
         "Cradle", "Carriage", "Wheels", "Handwheel", "Lanyard", "Toggle", "Shell", "Case", "Crate"]
REGION_PARTS = ("Skin", "Cap", "Tunic", "Trousers", "Leather", "Glasses", "Barrel", "Block", "Lever", "Cradle", "Carriage",
                "Wheels", "Handwheel", "Lanyard", "Toggle", "Shell", "Case", "Crate")
UNIFORM = {"base": NAVY, "facing": SCARLET, "brass": BRASS, "buff": BUFF}
GUN = {"olive": (0.33, 0.34, 0.2), "grey": (0.3, 0.32, 0.34), "brass": BRASS, "copper": COPPER}
WHISKER = {"base": RUSSET, "hi": (0.56, 0.32, 0.15), "low": (0.11, 0.055, 0.03), "streak": (0.17, 0.085, 0.04),
           "tint": (0.42, 0.22, 0.1)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_LayerSkin", "base": (0.82, 0.56, 0.42), "ruddy": (0.86, 0.38, 0.29), "lips": (0.64, 0.33, 0.28),
                      "brow": ((0.2, 0.1, 0.05), (0.38, 0.2, 0.09)),
                      "extra": ((LASH, (0.12, 0.06, 0.03), 0.5), (STUBBLE, (0.4, 0.22, 0.14), 0.6, 0.45))}),
    "Whiskers": ("hair", dict(WHISKER, name="HQ_LayerWhiskers")),
    "Hair": ("hair", dict(WHISKER, name="HQ_LayerHair")),
    "Cap": ("uniform", dict(UNIFORM, name="HQ_LayerCap")),
    "Tunic": ("uniform", dict(UNIFORM, name="HQ_LayerTunic")),
    "Trousers": ("uniform", dict(UNIFORM, name="HQ_LayerTrousers")),
    "Leather": ("leather_dyed", {"name": "HQ_LayerLeather", "base": (0.36, 0.2, 0.1), "dyed": (0.36, 0.2, 0.1)}),
    "Glasses": ("fieldgun", dict(GUN, name="HQ_FieldGlasses")),
    "Barrel": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Block": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Lever": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Cradle": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Carriage": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Wheels": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Handwheel": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Lanyard": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Toggle": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Shell": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Case": ("fieldgun", dict(GUN, name="HQ_FieldGun")),
    "Crate": ("fieldgun", dict(GUN, name="HQ_AmmoBox", wood=(0.66, 0.52, 0.32))),
}
LOW_TARGETS = {"Skin": 6000, "Whiskers": 1400, "Hair": 700, "Cap": 1100, "Tunic": 4000, "Trousers": 1300, "Leather": 2600,
               "Glasses": 320, "Barrel": 2200, "Block": 160, "Lever": 200, "Cradle": 1700, "Carriage": 4400, "Wheels": 3800,
               "Handwheel": 420, "Lanyard": 40, "Toggle": 90, "Shell": 300, "Case": 150, "Crate": 1300}
AO_EXCLUDE = ["Lanyard", "Toggle", "Shell", "Case", "Glasses", "Lever"]
GUN_PARTS = ["Barrel", "Block", "Lever", "Cradle", "Carriage", "Wheels", "Handwheel", "Lanyard", "Toggle", "Shell", "Case", "Crate"]
# the gun and the box are baked 6 m away from him: his rest pose (his right foot stands in the box) must leave no shadow
BAKE_APART = (GUN_PARTS, (6.0, 0.0, 0.0))
YAW_PIVOT = (0.45, -0.5, 0.0)                     # the tower turns about this point (keeps the gun, him and the box on the base)


def prop_bones():
    return []                                        # everything he handles is a free bone (extra_bones)


def extra_bones():
    """The gun's bones (none of them deform him): carriage (rocking about the spade at the shot), cradle (elevating about
    the trunnions), barrel (sliding back along the cradle at the shot: from the trunnions to the muzzle's face, bone_point
    ALONG 1.0 is the muzzle), block (sliding out to open the breech), lever (on the barrel, swinging up and back),
    handwheel (turning); the lanyard (from its eye on the firing gear, stretched to the toggle) and the toggle; the round he
    loads (shell: base -> fuse) and the spent case; props (the ammunition box, still); glasses (his field glasses)."""
    G, X, U, N = glasses_frame()
    cb = bore_pt(S_CASE)
    return [
        ("carriage", KICK_P, KICK_P + v3((0, -0.4, 0)), None),
        ("cradle", TRUN, TRUN + GD * 0.3, "carriage"),
        ("barrel", TRUN, MUZZLE, None),
        ("block", BLK_C, BLK_C + GX_ * 0.15, None),
        ("lever", LEV_P, LEV_P + GD * LEV_L, "barrel"),
        ("handwheel", HW_C, HW_C - GX_ * 0.12, "carriage"),
        ("lanyard", CORD_A, TOG0, None),                 # (its eye rides the carriage)
        ("toggle", TOG0, TOG0 + GX_ * 0.1, None),
        ("shell", SH_BASE0, SH_BASE0 + SH_A0 * SHELL_L, None),
        ("case", cb, cb + GD * CASE_L, None),
        ("props", CRATE_C, CRATE_C + v3((0, 0, 0.2)), None),
        ("glasses", G, G + U * 0.1, None),
    ]


def leather_weights(ob, skin_ob, arm):
    """Boots, gauntlets from the body; the belt with his hips; the glasses' strap from his neck and chest, its ends with
    the glasses."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "forearm.R", "forearm.L", "hand.R", "hand.L",
                                                       "thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"})
    G, X, U, N = glasses_frame()
    groups = {}
    for v in ob.data.vertices:
        p = np.array(v.co)
        w = None
        if abs(p[2] - BELT_Z) < 0.07 and math.hypot(p[0], p[1] - 0.03) < 0.42:
            w = {"root": 0.5, "spine": 0.5}
        elif p[2] > 1.08 and abs(p[0]) < 0.24 and np.linalg.norm(p - G) < 0.55 and p[2] < 1.52 and _near_strap(p):
            d = float(np.linalg.norm(p - G))
            k = max(0.0, min(1.0, (d - 0.05) / 0.14))
            w = {"glasses": 1.0 - k, "chest": 0.7 * k, "neck": 0.3 * k}
        if w is None:
            continue
        for g in list(ob.vertex_groups):
            g.remove([v.index])
        _blend_add(ob, groups, v.index, w)


_STRAPS = None


def _near_strap(p):
    global _STRAPS
    if _STRAPS is None:
        _STRAPS = [np.array(q) for path in strap_paths() for q in path]
    return min(float(np.linalg.norm(p - q)) for q in _STRAPS) < 0.05


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Whiskers": ("rigid", "head"), "Hair": ("rigid", "head"), "Cap": ("rigid", "head"),
        "Tunic": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L",
                                       "thigh.R", "thigh.L"}, {"thigh.R": 0.35, "thigh.L": 0.35}),
        "Trousers": ("transfer", {"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Leather": ("custom", leather_weights),
        "Glasses": ("rigid", "glasses"),
        "Barrel": ("rigid", "barrel"), "Block": ("rigid", "block"), "Lever": ("rigid", "lever"), "Cradle": ("rigid", "cradle"),
        "Carriage": ("rigid", "carriage"), "Wheels": ("rigid", "carriage"), "Handwheel": ("rigid", "handwheel"),
        "Lanyard": ("rigid", "lanyard"), "Toggle": ("rigid", "toggle"), "Shell": ("rigid", "shell"), "Case": ("rigid", "case"),
        "Crate": ("rigid", "props"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Whiskers") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.8
    if part in ("Carriage", "Wheels", "Crate"):
        return 0.72
    if part in ("Barrel", "Cradle"):
        return 0.85
    if part in ("Shell", "Case", "Lever", "Block", "Handwheel", "Toggle", "Lanyard", "Glasses"):
        return 0.9
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Whiskers", whiskers_field(), 0.0022 if fine else 0.003),
        ("Hair", hair_field(), 0.0022 if fine else 0.003),
        ("Cap", cap_field(), 0.0022 if fine else 0.003),
        ("Tunic", tunic_field(), 0.0026 if fine else 0.0036),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Glasses", glasses_field(), 0.0014 if fine else 0.002),
        ("Barrel", barrel_field(), 0.0026 if fine else 0.0036),
        ("Block", block_field(), 0.002 if fine else 0.003),
        ("Lever", lever_field(), 0.0016 if fine else 0.0024),
        ("Cradle", cradle_field(), 0.0024 if fine else 0.0034),
        ("Carriage", carriage_field(), 0.0032 if fine else 0.0046),
        ("Wheels", wheels_field(), 0.0028 if fine else 0.004),
        ("Handwheel", handwheel_field(), 0.0016 if fine else 0.0024),
        ("Lanyard", lanyard_field(), 0.0014 if fine else 0.002),
        ("Toggle", toggle_field(), 0.0014 if fine else 0.002),
        ("Shell", shell_field(), 0.0016 if fine else 0.0024),
        ("Case", case_field(), 0.0016 if fine else 0.0024),
        ("Crate", crate_field(), 0.0024 if fine else 0.0034),
    ]
