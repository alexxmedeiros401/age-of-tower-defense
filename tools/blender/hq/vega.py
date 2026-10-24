"""Commander Vega, Resistance Leader (HQ hero, The Data Center). Rest pose = A-pose, facing -Y, feet at z = 0; right
side = -X.

Humanity's last general, a man in his fifties: a commanding, warm face (a broad square jaw, a strong chin with a cleft,
high cheekbones over lean cheeks, a straight strong nose), clear grey-blue eyes with smile creases at their corners,
level dark-grey brows (his left one lifted a little), a closed mouth in a confident half-smile drawn up at his left
corner; a shadow of grey stubble; an old pale scar straight down through his right brow and onto his cheek under the eye
(the brow split by it). Dark hair cut high and tight: short and swept back on top, buzzed close and gone silver at the
temples and round the back (`Temples`, its own part).

A long charcoal command coat to below his knees: a high stand collar turned up round his neck (lined in amber), open
at the chest in a V over his gunmetal armour, closed at the waist, its skirts parting below the belt and flaring to the
hem (a vent at the back); sleeves to the wrist with deep turned-back cuffs; a thin amber piping along its front edges,
the collar's top and the cuffs. Under it a gunmetal cuirass (a raised sternum ridge, segmented plates over his belly)
over a dark mock-neck. An amber Resistance sash over his left shoulder, across his chest to his right hip, knotted there
with two hanging ends; a black belt over the coat and the sash (a gunmetal buckle with the amber chevron), the
killswitch's holder on his left hip. On his left shoulder an epaulette: a gunmetal shoulder board edged in amber, three
amber rank bars. On his right shoulder a salvaged white robot pauldron: a domed plate and two lames
below it, dented and scuffed, strapped on with black straps, sprayed with the Resistance's amber chevron. Black gloves
(Ken's gloved fists, ken.py); charcoal-grey fatigue trousers bloused into black combat boots (ken.py's).

His weapon: a heavy plasma sidearm (a chunky gunmetal frame, a salvaged white robot shell over its top with an amber
slash, a black taped grip, an exposed plasma chamber in a gunmetal cage before the receiver and a fat vented barrel
shroud and muzzle brake; the chamber's cell and the muzzle's core glow amber: `Chamber`). Fired one-handed.

The killswitch (the Ability): a salvaged robot control rod: a black taped grip, a gunmetal collar, a white robot head
with amber stripes, a stubby antenna, and on its end a big amber thumb button (it glows: `Button`, on the `button` bone:
it swells when he thumbs it) under a flipped-open guard. At rest it hangs in its holder on his left hip.

His body is the Musketeer's (musketeer.py: the long, rangy skeleton) as Ken's (ken.py), with his own head. The pistol
and the killswitch ride parentless bones (`pistol`: the grip's middle to the muzzle; `switch`: the grip's middle to the
button), posed in world space by every clip (anim_vega.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import musketeer as mk
from musketeer import (J, hp, hr, hinv, HS, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S, fist_center,
                       foot, torso_prims, traps, neck_prim, deltoid, upper_arm_prims, forearm_prims, leg_prims, shin_prims,
                       _arm_seg_dist, _fgrad, torso_bones, TORSO_Z, TORSO, stubble_mask)
import ken as kn
from ken import hand, _on_face, _frame, _seg_dist, forearm_frame, eyes_field
from ada import ScaledField

SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, SCAR, GLOVE = 0, 1, 2, 3, 4, 8, 9, 10, 11
IRIS = ((0.2, 0.27, 0.34), (0.48, 0.6, 0.7))               # clear grey-blue eyes (prep.paint_eyes)

CHARCOAL = (0.13, 0.13, 0.15)           # the Resistance's dark fatigues and armour (the brief's colours, sRGB)
GUNMETAL = (0.22, 0.23, 0.25)
TEAL = (0.2, 0.27, 0.28)                # worn smoky teal-grey cloth
AMBER = (0.95, 0.58, 0.14)              # the Resistance's accent (paint, the sash)
AMBER_GLOW = (1.0, 0.62, 0.15)          # (emissive)
WHITE = (0.88, 0.88, 0.86)              # salvaged robot plates
BLACK = (0.06, 0.06, 0.065)

Z = v3((0.0, 0.0, 1.0))


# ======================================================================================= head
def head(fd):
    """Ken's face (ken.py), reviewed and proven, made older and commanding: a broader square jaw, a strong chin with a
    small cleft, cheekbones, a defined brow ridge; level brows lying on it (his left one lifted a little); clear open
    eyes with smile creases at their outer corners; a straight nose; a closed mouth in a half-smile (his left corner drawn
    up into the cheek); a shadow of stubble; the scar straight down through his right brow and on below the eye."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.05, 1.588), (0.133, 0.126, 0.122)), 0.07, SKIN)                          # a broad jaw
    fd.add(E((0, -0.132, 1.501), (0.075, 0.063, 0.063)), 0.05, SKIN)                         # a strong chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.108, -0.118, 1.64), 0.042), 0.05, SKIN)                              # cheekbones
        fd.add(S((sx * 0.118, -0.044, 1.56), 0.045), 0.05, SKIN)                              # square jaw corners
        fd.add(S((sx * 0.074, -0.14, 1.604), 0.024), 0.03, SKIN)                              # (cheeks, a little round: warm)
        pts = [hp((sx * 0.15, -0.055, 1.744)), hp((sx * 0.114, -0.128, 1.752)), hp((sx * 0.06, -0.17, 1.75)), hp((0.0, -0.18, 1.748))]
        fd.add(Chain(pts, [hr(0.009), hr(0.015), hr(0.017), hr(0.017)], k=hr(0.02)), hr(0.03), SKIN)   # a defined brow ridge
    fd.sub(Ellipsoid(hp((0.0, -0.196, 1.488)), v3((0.004, 0.007, 0.012)) * HS), hr(0.005))     # the cleft in his chin
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # brows: strong and level, lying on the brow; his left one (+X) lifted a little (warm, wry; never knitted)
    brows = {-1: [(-0.026, 1.779), (-0.064, 1.789), (-0.106, 1.789), (-0.148, 1.774)],
             1: [(0.026, 1.782), (0.064, 1.795), (0.106, 1.797), (0.148, 1.783)]}
    for sx in (-1, 1):
        on = _on_face(fd, brows[sx], lift=0.001)
        fd.add(Chain(on, [hr(0.0055), hr(0.0068), hr(0.006), hr(0.003)], k=hr(0.006)), hr(0.004), BROW)
        fd.paint(Chain(on, [hr(0.0125), hr(0.0145), hr(0.013), hr(0.007)], k=hr(0.008)), BROW)
    # eyes: open and clear (Ken's lids: the upper lids clear of the irises, the lower lids just under them); lashes;
    # smile creases at their outer corners
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0058)), Plane(ec + v3((0, 0, hr(0.0212))), (sx * 0.16, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0048)), Plane(ec + v3((0, 0, -hr(0.0168))), (sx * -0.3, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.006), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0192))), (sx * 0.16, 0.05, -1.0)), hr(0.002)), LASH)
        for k in range(2):
            a = hp((sx * (0.11 + 0.004 * k), -0.13 + 0.006 * k, 1.682 - 0.013 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, 0.004 - 0.009 * k)), hr(0.0019), hr(0.0012)), hr(0.003))
    # a straight nose, a firm tip
    fd.add(RoundCone(hp((0, -0.18, 1.726)), hp((0, -0.226, 1.646)), hr(0.0125), hr(0.017)), hr(0.016), SKIN)
    fd.add(S((0, -0.229, 1.633), 0.02), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.025, -0.208, 1.618), 0.017), hr(0.01), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.013, -0.223, 1.606)), v3((0.008, 0.009, 0.005)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the closed mouth (the Musketeer's line on the same jaw): firm, his left corner (+X) drawn up into the cheek
    slot = [hp((-0.05, -0.174, 1.552)), hp((-0.026, -0.194, 1.547)), hp((0, -0.199, 1.547)), hp((0.027, -0.193, 1.551)),
            hp((0.053, -0.171, 1.563))]
    fd.sub(Chain(slot, [hr(0.0022), hr(0.003), hr(0.0034), hr(0.003), hr(0.0024)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.0034)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.046, -0.174, 1.557), (-0.024, -0.191, 1.553), (0.0, -0.196, 1.554), (0.025, -0.19, 1.557), (0.048, -0.172, 1.567)]
    lo_lip = [(-0.04, -0.174, 1.541), (-0.021, -0.19, 1.534), (0, -0.194, 1.532), (0.022, -0.189, 1.535), (0.042, -0.174, 1.546)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0045), hr(0.005), hr(0.0045), hr(0.003)], k=hr(0.005)), hr(0.007), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0062), hr(0.007), hr(0.0062), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(S((0.066, -0.158, 1.578), 0.011), hr(0.018), SKIN)                                   # the smile's cheek
    # ears: a rim, a hollow, a lobe (Ken's)
    for sx in (-1, 1):
        R = euler(0, sx * 0.25, sx * -0.35)
        c = hp((sx * 0.157, 0.035, 1.66))
        fd.add(Ellipsoid(c, v3((0.02, 0.04, 0.052)) * HS, R=R), hr(0.02), SKIN)
        o = norm(R @ v3((sx, 0, 0)))
        fd.sub(Ellipsoid(c + o * hr(0.016) + v3((0, -0.004, -0.004)), v3((0.008, 0.022, 0.028)) * HS, R=R), hr(0.006))
        fd.add(Ellipsoid(c + v3((0, 0.002, -0.042)) + o * hr(0.004), v3((0.012, 0.016, 0.016)) * HS, R=R), hr(0.01), SKIN)
    # the scar: a pale, slightly sunken line straight down through his right brow (splitting it) and on below the eye
    for seg_ in ([(-0.082, 1.806), (-0.084, 1.784), (-0.086, 1.762), (-0.088, 1.738)],
                 [(-0.09, 1.642), (-0.093, 1.622), (-0.097, 1.6), (-0.101, 1.582)]):
        sc = _on_face(fd, seg_, lift=0.0)
        fd.sub(Chain(sc, [hr(0.0012), hr(0.0018), hr(0.0016), hr(0.001)], k=hr(0.002)), hr(0.002))
        fd.paint(Chain(sc, [hr(0.0045), hr(0.006), hr(0.0055), hr(0.0035)], k=hr(0.004)), SCAR)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        fd.add(deltoid(side), 0.055, SKIN)
        for p, k in upper_arm_prims(side) + forearm_prims(side):
            fd.add(p, k, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side) + shin_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


def teeth_field():
    """His teeth, behind his closed lips."""
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009 + 0.003, -0.178, 1.551)), v3((0.008, 0.006, 0.006)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= hair: high and tight
EAR_C = {sx: hp((sx * 0.157, 0.035, 1.66)) for sx in (-1, 1)}


def skull():
    return Ellipsoid(HEAD_C, HEAD_RAD)


def hairline(P):
    """> 0 below his hairline (design units): his forehead (a little higher at the temples), in front of his ears, the
    nape."""
    Q = hinv(P)
    y, ax = Q[:, 1], np.abs(Q[:, 0])
    zl = (F(1.858) + F(0.018) * smoothstep(0.05, 0.12, ax) * smoothstep(-0.06, -0.14, y)
          - F(0.115) * smoothstep(-0.13, -0.05, y) - F(0.19) * smoothstep(0.07, 0.15, y))
    return zl - Q[:, 2]


def ears_out(P):
    out = None
    for sx in (-1, 1):
        q = P - EAR_C[sx].astype(F)
        e = F(hr(0.06)) - np.sqrt((q * q).sum(1))
        out = e if out is None else np.maximum(out, e)
    return out


_HC_D = v3((0.0, 0.03, 1.73))            # (the head's centre and radii in design units)
_HR_D = v3((0.168, 0.188, 0.186))


def top_patch(P):
    """< 0 on the long top (design directions from the head's centre): a strip over the crown from his front hairline
    back past the crown, narrow across (high and tight), its edge feathered."""
    Q = hinv(P)
    n = (Q - _HC_D.astype(F)) / _HR_D.astype(F)
    n = n / (np.sqrt((n * n).sum(1))[:, None] + F(1e-6))
    w = F(0.7) + F(0.06) * smoothstep(0.2, -0.6, n[:, 1])               # (a touch wider over the brow)
    e = np.sqrt((n[:, 0] / w) ** 2 + (np.maximum(n[:, 1] - F(0.1), 0) / F(0.8)) ** 2)
    return np.maximum(e - F(1.0), F(0.15) - n[:, 2])


def _comb(P):
    Q = hinv(P)
    return (F(0.0011) * np.sin(Q[:, 0] * F(260) + F(2.0) * NOISE(P * F(14))) + F(0.0008) * NOISE(P * F(60)))


def hair_field():
    """Dark hair (label 0), short on top and combed back (grooves), standing up a little over his brow, thinning to
    nothing at the strip's edges over the silver buzz."""
    fd = Field("Hair")
    sk = skull()
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    def cap(P):
        d = sk(P)
        Q = hinv(P)
        inside = smoothstep(0.0, 0.32, -top_patch(P))
        front = smoothstep(-0.08, -0.17, Q[:, 1])
        th = F(0.004) + (F(0.016) + F(0.01) * front) * inside
        return np.abs(d - (F(0.003) + th * F(0.5))) - th * F(0.5)
    def region(P):
        return np.maximum(np.maximum(hairline(P) * F(HS), top_patch(P) * F(0.05)), ears_out(P))
    fd.add(Inter(Func(cap, lo, hi, disp=_comb, disp_amp=0.0015), Func(region, lo, hi), 0.003), 0.0)
    return fd


def temples_field():
    """Silver hair buzzed close (label 0) over the rest of his scalp: his temples, over and behind his ears, round the
    back of his head to the nape (under the top's strip)."""
    fd = Field("Temples")
    sk = skull()
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    def region(P):
        Q = hinv(P)
        nape = F(1.585) - Q[:, 2] + F(0.008) * np.sin(Q[:, 0] * F(70))
        return np.maximum(np.maximum(hairline(P), nape) * F(HS), ears_out(P))
    buzz = lambda P: F(0.0005) * NOISE(P * F(120)) + F(0.0004) * NOISE(P * F(30))
    fd.add(Inter(Shell(sk, 0.0045, 0.0055, pad=0.05, disp=buzz, disp_amp=0.0007), Func(region, lo, hi), 0.002), 0.0)
    return fd


# ======================================================================================= the mock-neck and the cuirass
def body_hull(arms=True):
    return kn.body_hull(arms)


def _flat_torso(b):
    """The torso's shapes without the pectorals, a broad smooth chest over them (the coat and the cuirass lie flat)."""
    for i, (p, k) in enumerate(torso_prims()):
        if i in (2, 3):
            continue
        b.add(p, k)
    b.add(Ellipsoid((0, -0.05, 1.3), (0.24, 0.155, 0.18)), 0.06)


def torso_hull():
    b = Field("TorsoHull")
    _flat_torso(b)
    b.add(traps(), 0.06)
    b.add(neck_prim(), 0.05)
    return b


_TH = []


def _th():
    if not _TH:
        _TH.append(torso_hull())
    return _TH[0]


ARM_OFF, ARM_T = 0.012, 0.012           # the cuirass over his torso
ARM_OUT = ARM_OFF + ARM_T / 2


def neck_line(P, base, rise=0.07):
    return kn.neck_line(P, base, rise)


def under_field():
    """The dark mock-neck (uniform cloth, label 0) round his neck above the cuirass, under the coat's collar."""
    fd = Field("Under")
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    knit = lambda P: F(0.0012) * np.sin(P[:, 2] * F(260)) + F(0.0006) * NOISE(P * F(50))
    fd.add(Inter(Shell(nk, 0.008, 0.009, pad=0.06, disp=knit, disp_amp=0.0013),
                 Func(lambda P: np.maximum(F(1.385) - P[:, 2], P[:, 2] - (F(1.45) + F(0.07) * smoothstep(-0.05, 0.08, P[:, 1]))),
                      (-0.3, -0.3, 1.3), (0.3, 0.3, 1.65)), 0.004), 0.0)
    return fd


def armour_field():
    """modern_kit (label 0 = gunmetal, smooth): the cuirass over his chest and belly, seen in the coat's V: a raised
    sternum ridge, plates over his belly with grooves between them, bright (9) edges; a gorget rim round its neck."""
    fd = Field("Armour")
    th = _th()
    lo, hi = (-0.4, -0.45, 0.85), (0.4, 0.3, 1.6)
    def region(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        return np.maximum(np.maximum(np.abs(x) - F(0.21), y - F(0.07)),
                          np.maximum(F(0.9) - z, neck_line(P, 1.405, 0.06)))
    tex = lambda P: F(0.0007) * NOISE(P * F(40)) + F(0.0012) * NOISE(P * F(9))
    fd.add(Inter(Shell(th, ARM_OFF, ARM_T, pad=0.1, disp=tex, disp_amp=0.0015), Func(region, lo, hi), 0.006), 0.0)
    # the sternum ridge
    def ridge(P):
        return np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.012), P[:, 1] + F(0.02)),
                          np.maximum(F(1.12) - P[:, 2], neck_line(P, 1.39, 0.06)))
    fd.add(Inter(Shell(th, ARM_OUT + 0.004, 0.01, pad=0.1), Func(ridge, lo, hi), 0.004), 0.006)
    # grooves between the belly plates
    for z in (1.0, 1.06, 1.12):
        def groove(P, z=z):
            return np.maximum(np.maximum(np.abs(P[:, 2] - F(z) - F(0.012) * np.abs(P[:, 0]) / F(0.2)) - F(0.0035), P[:, 1] + F(0.03)),
                              F(ARM_OUT - 0.003) - th.eval(P, margin=0.06))
        fd.sub(Func(groove, (-0.3, -0.4, z - 0.05), (0.3, 0.1, z + 0.05)), 0.002)
    # the gorget rim
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    fd.add(Inter(Shell(nk, 0.022, 0.012, pad=0.06), Func(lambda P: np.maximum(np.abs(P[:, 2] - F(1.395)) - F(0.012), P[:, 1] - F(0.02)),
                                                          (-0.3, -0.3, 1.3), (0.3, 0.3, 1.5)), 0.004), 0.006, 9)
    return fd


# ======================================================================================= the command coat
COAT_OFF, COAT_T = 0.032, 0.014
COAT_OUT = COAT_OFF + COAT_T / 2
HEM_Z = 0.4
SKIRT_Z = (0.95, 0.38)                  # the skirts' flare: from the waist to below his knees
SKIRT_RX = (0.215, 0.36)
SKIRT_RY = (0.175, 0.31)
SKIRT_YC = (0.04, 0.09)
SKIRT_LO, SKIRT_HI = (-0.4, -0.25, 0.36), (0.4, 0.42, 0.97)
WAIST_Z = 0.95                          # the belt


def skirt_sd(P):
    z = P[:, 2]
    t = np.clip((F(SKIRT_Z[0]) - z) / F(SKIRT_Z[0] - SKIRT_Z[1]), 0, 1)
    rx = F(SKIRT_RX[0]) + F(SKIRT_RX[1] - SKIRT_RX[0]) * t
    ry = F(SKIRT_RY[0]) + F(SKIRT_RY[1] - SKIRT_RY[0]) * t
    yc = F(SKIRT_YC[0]) + F(SKIRT_YC[1] - SKIRT_YC[0]) * t
    q = np.sqrt((P[:, 0] / rx) ** 2 + ((P[:, 1] - yc) / ry) ** 2)
    return np.maximum((q - F(1.0)) * np.minimum(rx, ry), np.maximum(z - F(SKIRT_Z[0]), F(SKIRT_Z[1]) - z))


def _sleeve_prims(side):
    """The sleeves' hull: a little slimmer than his arm (with the coat's offset they sit close)."""
    sx = -1 if side == "R" else 1
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    return [(Sphere(sh + v3((sx * 0.02, -0.005, 0.01)), SLV[0]), 0.045),
            (RoundCone(sh, el, SLV[1], SLV[2]), 0.04),
            (Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.02, 0)), SLV[3], R=rot_from_axes(z_axis=el - sh)), 0.03),
            (RoundCone(el, wr, SLV[4], SLV[5]), 0.03),
            (Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.007, 0, 0)), SLV[6], R=rot_from_axes(z_axis=wr - el)), 0.03),
            (Sphere(el + v3((0, 0.024, 0)), SLV[7]), 0.025)]


SLV = (0.078, 0.066, 0.05, (0.058, 0.06, 0.1), 0.048, 0.038, (0.06, 0.054, 0.104), 0.036)


_CH = {}


def coat_hull(arms=True):
    if arms in _CH:
        return _CH[arms]
    b = Field("CoatHull")
    _flat_torso(b)
    b.add(traps(), 0.06)
    b.add(Func(skirt_sd, SKIRT_LO, SKIRT_HI), 0.07)
    if arms:
        for side in ("R", "L"):
            for p, k in _sleeve_prims(side):
                b.add(p, k)
    _CH[arms] = b
    return b


def coat_w(z):
    """Half width of the coat's front opening at height z: a V from his collarbones closing at the waist, the skirts
    parting below it."""
    up = F(0.008) + F(0.104) * smoothstep(0.98, 1.44, z)
    lo = F(0.008) + F(0.13) * smoothstep(0.9, 0.45, z)
    return np.where(z > F(WAIST_Z), up, lo)


def coat_hem(P):
    return F(HEM_Z) - F(0.02) * smoothstep(0.0, 0.25, P[:, 1]) + F(0.008) * NOISE(P * F(6))


def coat_neck(P):
    """> 0 above the neckline: round his neck only (lifted clear of the shoulders: no hole on them)."""
    ax = np.abs(P[:, 0])
    return P[:, 2] - (F(1.46) + F(0.075) * smoothstep(-0.04, 0.12, P[:, 1]) + F(0.3) * smoothstep(0.14, 0.21, ax))


CUFF_A, CUFF_B = 0.6, 0.96              # the turned-back cuffs: from this far down the forearm to the sleeve's end
CUFF_R = (0.092, 0.1)


def cuff_frame(side):
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    L = float(np.linalg.norm(wr - el))
    return el + ax * (L * CUFF_A), el + ax * (L * CUFF_B), ax


def cuff_cut(P):
    """> 0 past the sleeves' ends near the wrist, only near the forearms."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        a, b, ax = cuff_frame(side)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        along = (P - b.astype(F)) @ ax.astype(F)
        near = _seg_dist(P, el, wr + ax * 0.2) < F(0.15)
        out = np.maximum(out, np.where(near, along, F(-1.0)))
    return out


def coat_front(P):
    return np.where(P[:, 1] < F(0.0), coat_w(P[:, 2]) - np.abs(P[:, 0]), F(-1.0))


def coat_vent(P):
    return np.where((P[:, 1] > F(0.12)) & (P[:, 2] < F(0.72)), F(0.008) - np.abs(P[:, 0]), F(-1.0))


def coat_cut(P):
    return np.maximum(np.maximum(np.maximum(coat_neck(P), coat_front(P)), np.maximum(coat_hem(P) - P[:, 2], cuff_cut(P))), coat_vent(P))


def coat_folds(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.05)))
    skirt = smoothstep(0.9, 0.5, P[:, 2])
    return (F(0.008) * np.sin(a * F(8) + F(0.8) * NOISE(P * F(3))) * skirt + F(0.0012) * NOISE(P * F(28))
            + F(0.0018) * np.sin(P[:, 2] * F(60)) * smoothstep(0.6, 0.9, np.abs(P[:, 0]) / F(0.68)))


def collar_region(P):
    """< 0 on the stand collar: high round the back and sides of his neck, open at the front."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    top = F(1.495) + F(0.045) * smoothstep(-0.06, 0.12, y)
    return np.maximum(np.maximum(z - top, F(1.42) - z), F(-0.05) - y + F(0.07) * smoothstep(0.05, 0.12, np.abs(x)))


def _collar_hull():
    nh = Field("CollarHull")
    nh.add(neck_prim(), 0.0)
    nh.add(traps(), 0.06)
    return nh


COLLAR_OFF, COLLAR_T = 0.036, 0.014


def coat_field():
    """modern_kit (label 0: charcoal cordura, a fine weave): the long coat, open at his chest in a V to the waist, its
    skirts parting below and flaring to below his knees (folds, a vent at the back); a raised facing along the front
    edges; the high stand collar (its inside lined amber, 6); deep turned-back cuffs; amber piping (6) along the facings'
    edges, the collar's top and the cuffs' tops; a pocket flap on each skirt."""
    fd = Field("Coat")
    hull = coat_hull()
    lo, hi = (-1, -1, 0.3), (1, 1, 1.7)
    hlo, hhi = hull.bounds()
    def cloth(P):
        d = hull.eval(P, margin=0.07)
        return np.abs(d - (F(COAT_OFF) - coat_folds(P))) - F(COAT_T * 0.5)
    fd.add(Inter(Func(cloth, hlo - 0.06, hhi + 0.06, disp=lambda P: F(0.0006) * NOISE(P * F(70)), disp_amp=0.0008),
                 Func(coat_cut, lo, hi), 0.005), 0.0)
    # the front edges: a raised facing along the opening, from the collar to the hem
    hull_t = coat_hull(arms=False)
    def facing(P):
        e = np.where(P[:, 1] < F(0.0), np.abs(P[:, 0]) - coat_w(P[:, 2]), F(1.0))
        band = np.abs(e - F(0.016)) - F(0.016)
        return np.maximum(np.maximum(band, coat_neck(P) + F(0.004)), np.maximum(coat_hem(P) - P[:, 2] + F(0.002), P[:, 1] - F(-0.04)))
    def fshell(P):
        return np.abs(hull_t.eval(P, margin=0.1) - (F(COAT_OFF + 0.007) - coat_folds(P))) - F(0.0065)
    fd.add(Inter(Func(fshell, (-0.5, -0.6, 0.3), (0.5, 0.2, 1.6)), Func(facing, (-0.5, -0.6, 0.3), (0.5, 0.2, 1.6)), 0.003), 0.004)
    def piping(P):
        e = np.where(P[:, 1] < F(0.0), np.abs(P[:, 0]) - coat_w(P[:, 2]), F(1.0))
        return np.maximum(np.abs(e - F(0.029)) - F(0.004), np.maximum(coat_hem(P) + F(0.01) - P[:, 2], coat_neck(P)))
    fd.paint(Func(piping, (-0.5, -0.6, 0.3), (0.5, 0.2, 1.6)), 6)
    # the stand collar: high round his neck, flaring a little, lined amber
    nh = _collar_hull()
    flare = lambda P: F(0.012) * smoothstep(1.44, 1.53, P[:, 2])
    def collar(P):
        d = nh.eval(P, margin=0.08)
        return np.abs(d - F(COLLAR_OFF) - flare(P)) - F(COLLAR_T * 0.5)
    clo, chi = (-0.3, -0.3, 1.32), (0.3, 0.4, 1.66)
    fd.add(Inter(Func(collar, clo, chi), Func(collar_region, clo, chi), 0.004), 0.006)
    fd.paint(Inter(Func(lambda P: np.abs(nh.eval(P, margin=0.08) - F(COLLAR_OFF - COLLAR_T * 0.5) - flare(P)) - F(0.004), clo, chi),
                   Func(lambda P: collar_region(P) + F(0.004), clo, chi), 0.0), 6)
    fd.paint(Func(lambda P: np.maximum((F(1.48) + F(0.045) * smoothstep(-0.06, 0.12, P[:, 1])) - P[:, 2],
                                       np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F(0.05)) ** 2) - F(0.17)), clo, chi), 6)
    # deep turned-back cuffs, amber-piped at their tops
    for side in ("R", "L"):
        a, b, ax = cuff_frame(side)
        cone = RoundCone(a, b, CUFF_R[0], CUFF_R[1])
        Lc = float(np.linalg.norm(b - a))
        def cband(P, a=a, ax=ax, Lc=Lc):
            s = (P - a.astype(F)) @ ax.astype(F)
            return np.maximum(-s, s - F(Lc))
        fd.add(Inter(Shell(cone, 0.0, 0.016, pad=0.05, disp=lambda P: F(0.001) * NOISE(P * F(30)), disp_amp=0.0015),
                     Func(cband, a - 0.25, b + 0.25), 0.003), 0.004)
        def ctrim(P, a=a, ax=ax):
            q = P - a.astype(F)
            s_ = q @ ax.astype(F)
            rad = np.sqrt(np.maximum((q * q).sum(1) - s_ * s_, 0))
            return np.maximum(np.abs(s_ - F(0.008)) - F(0.006), F(CUFF_R[0] - 0.004) - rad)
        fd.paint(Func(ctrim, a - 0.25, a + 0.25), 6)
    # pocket flaps on the skirts' fronts
    for sx in (-1, 1):
        ang = sx * math.radians(50)
        d = v3((math.sin(ang), -math.cos(ang), 0.0))
        h, ok = ray_hit(Func(lambda P: hull_t.eval(P, margin=0.1) - F(COAT_OUT + 0.003), (-1, -1, 0.5), (1, 1, 1.0)),
                        [v3((0, 0.05, 0.8)) + d * 0.7], [-d], tmax=0.8)
        if not ok[0]:
            continue
        c = h[0]
        def flap(P, c=c, ang=ang):
            a_ = np.arctan2(P[:, 0], -(P[:, 1] - F(0.05)))
            da = np.abs(a_ - F(ang)) * F(0.3)
            dz = P[:, 2] - F(c[2])
            return np.maximum(da - F(0.055), np.maximum(dz - F(0.02), -dz - F(0.026)))
        fd.add(Inter(Shell(hull_t, COAT_OFF + 0.012, 0.012, pad=0.1), Func(flap, c - 0.2, c + 0.2), 0.003), 0.004)
    return fd


# ======================================================================================= the sash, the belt
def _strap_plane(top, hip_f, hip_b):
    n = norm(np.cross(hip_f - top, hip_b - top))
    return top, n


SASH = _strap_plane(v3((0.17, 0.06, 1.52)), v3((-0.25, -0.12, 0.9)), v3((-0.25, 0.2, 0.9)))   # his left shoulder -> right hip
SASH_W = 0.04                          # half width


def strap_d(P, plane):
    p0, n = plane
    return np.abs((P - p0.astype(F)) @ n.astype(F))


def _over_belt(P):
    return smoothstep(0.03, 0.01, np.abs(P[:, 2] - F(WAIST_Z)) - F(0.03))


def sash_off(P):
    return F(COAT_OUT + 0.006)


def sash_field():
    """Amber cloth (uniform's cloth, label 0) over his left shoulder, across his chest (over the coat, bridging its V) to
    his right hip, knotted there over the belt, two ends hanging down his thigh, their tips fringed (5)."""
    fd = Field("Sash")
    base = coat_hull(arms=False)
    lo, hi = (-0.4, -0.35, 0.82), (0.4, 0.36, 1.6)
    wrinkle = lambda P: F(0.0014) * np.sin((P[:, 0] * F(0.6) + P[:, 2]) * F(70) + F(1.5) * NOISE(P * F(6))) + F(0.0012) * NOISE(P * F(20))
    def band(P):
        return np.maximum(strap_d(P, SASH) - F(SASH_W), np.maximum(F(0.86) - P[:, 2], P[:, 2] - F(1.6)))
    def layer(P):
        return np.abs(base.eval(P, margin=0.12) - sash_off(P)) - F(0.006)
    fd.add(Inter(Func(layer, lo, hi, disp=wrinkle, disp_amp=0.003), Func(band, lo, hi), 0.003), 0.0)
    # the knot on his right hip (over the belt) and its hanging ends
    outer = Func(lambda P: base.eval(P, margin=0.12) - F(COAT_OUT + 0.024), (-0.6, -0.5, 0.4), (0.6, 0.5, 1.2))
    a = math.radians(-62.0)
    d = v3((math.sin(a), -math.cos(a), 0.0))
    h, ok = ray_hit(outer, [v3((0, 0.04, WAIST_Z - 0.01)) + d * 0.7], [-d], tmax=0.8)
    knot = h[0] if ok[0] else v3((-0.2, -0.12, WAIST_Z))
    kd = norm(v3((d[0], d[1], 0.0)))
    fd.add(Ellipsoid(knot + kd * 0.012, (0.04, 0.034, 0.034), R=rot_from_axes(z_axis=kd), disp=wrinkle, disp_amp=0.004), 0.008)
    fd.add(Ellipsoid(knot + kd * 0.008 + v3((-0.026, 0, 0.016)), (0.032, 0.026, 0.026), R=rot_from_axes(z_axis=kd)), 0.008)
    fringe = lambda P: F(0.004) * np.abs(np.sin((P[:, 0] + P[:, 1]) * F(260)))
    for k, (dx, L, sw) in enumerate(((0.0, 0.26, 1.0), (-0.045, 0.21, -1.0))):
        a0 = knot + kd * 0.014 + v3((dx, 0, -0.024))
        pts = [a0]
        for j in range(1, 6):
            u = j / 5
            q = a0 + v3((0.012 * sw * math.sin(u * 3), 0.01 * u, -L * u)) + kd * (0.02 * u + 0.03 * u * u)
            h2, ok2 = ray_hit(outer, [q + kd * 0.25], [-kd], tmax=0.5)
            if ok2[0] and float((h2[0] - q) @ kd) > 0:
                q = h2[0] + kd * 0.004
            pts.append(q)
        fd.add(Lock(pts, [0.044, 0.046, 0.047, 0.048, 0.048, 0.046], [0.009] * 6, [kd] * 6, k=0.006, disp=wrinkle, disp_amp=0.003), 0.006)
        tip = pts[-1]
        dd = norm(pts[-1] - pts[-2])
        fd.add(Lock([tip - dd * 0.01, tip + dd * 0.03], [0.046, 0.048], [0.008, 0.006], [kd] * 2, k=0.004, disp=fringe, disp_amp=0.003), 0.004, 5)
    return fd


BELT_W = 0.026
BELT_OFF = COAT_OUT + 0.016             # (over the sash)


def belt_spot(angle_deg, out=0.0, dz=0.0):
    """A point on the belt's outer face at an angle round him (0 = his front, 90 = his left), and the outward normal."""
    hull = coat_hull(arms=False)
    a = math.radians(angle_deg)
    d = v3((math.sin(a), -math.cos(a), 0.0))
    f = Func(lambda P: hull.eval(P, margin=0.12) - F(BELT_OFF + 0.006 + out), (-0.8, -0.8, 0.6), (0.8, 0.8, 1.2))
    h, ok = ray_hit(f, [v3((0, 0.04, WAIST_Z + dz)) + d * 0.6], [-d], tmax=0.7)
    p = h[0] if ok[0] else v3((0, 0.04, WAIST_Z + dz)) + d * 0.24
    return p, norm(v3((d[0], d[1], 0.0)))


HOLDER_A = 118.0                        # the killswitch's holder on his left hip, behind his side


def belt_field():
    """modern_kit: a black (5) belt over the coat and the sash, a gunmetal (9) buckle with the amber (6) chevron; on his
    left hip the killswitch's holder (a black loop and a gunmetal clip); a cell pouch on his right hip, behind the sash's
    knot (black)."""
    fd = Field("Belt")
    hull = coat_hull(arms=False)
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(WAIST_Z)) - F(BELT_W), (-0.5, -0.45, WAIST_Z - 0.07), (0.5, 0.5, WAIST_Z + 0.07)),
                 Shell(hull, BELT_OFF, 0.013, pad=0.12, disp=lambda P: F(0.0006) * NOISE(P * F(60)), disp_amp=0.0008), 0.003), 0.0, 5)
    p, n = belt_spot(0.0, 0.004)
    Rb = _frame(n)
    fd.add(RoundBox(p + n * 0.008, (0.046, 0.034, 0.009), 0.006, R=Rb), 0.003, 9)
    def chev(P, p=p, Rb=Rb):
        q = (P - (p + n * 0.017).astype(F)) @ Rb.astype(F)
        return np.maximum(np.abs(q[:, 1] + F(0.008) - np.abs(q[:, 0]) * F(0.9)) - F(0.0065), np.abs(q[:, 0]) - F(0.03))
    fd.paint(Func(chev, p - 0.1, p + 0.1), 6)
    # the killswitch's holder
    p, n = belt_spot(HOLDER_A, 0.004)
    Rh = _frame(n)
    fd.add(RoundBox(p + n * 0.006 - Z * 0.012, (0.03, 0.05, 0.008), 0.005, R=Rh), 0.003, 9)          # the clip plate
    G, A, U = switch_rest()
    ring_c = G + A * 0.05
    fd.add(Torus(ring_c, 0.04, 0.008, R=rot_from_axes(z_axis=A)), 0.003, 5)                      # the loop round its grip
    fd.add(RoundCone(p + n * 0.006 - Z * 0.03, ring_c + n * -0.004, 0.009, 0.008), 0.003, 5)
    # a cell pouch on his right hip, behind the sash's knot
    p, n = belt_spot(-104.0, 0.004, dz=-0.05)
    Rp = _frame(n)
    fd.add(RoundBox(p + n * 0.022, (0.04, 0.052, 0.022), 0.012, R=Rp), 0.004, 5)
    fd.add(RoundBox(p + n * 0.03 + Rp[:, 1] * 0.036, (0.043, 0.02, 0.016), 0.008, R=Rp), 0.003, 5)
    fd.add(RoundBox(p + n * 0.046 + Rp[:, 1] * 0.03, (0.01, 0.012, 0.004), 0.002, R=Rp), 0.002, 9)
    return fd


# ======================================================================================= the epaulette (left), the pauldron (right)
def shoulder_spot(side, along, out=0.0):
    """A point on the coat's outer face over the top of his shoulder, `along` (0 at the collar, 1 at the shoulder's
    point), and its outward normal."""
    sx = -1 if side == "R" else 1
    hull = coat_hull()
    sh = J["shoulder_" + side]
    x = 0.13 + (abs(sh[0]) + 0.05 - 0.13) * along
    f = Func(lambda P: hull.eval(P, margin=0.12) - F(COAT_OUT + 0.004 + out), (-0.8, -0.4, 1.1), (0.8, 0.5, 1.8))
    h, ok = ray_hit(f, [v3((sx * x, 0.075, 1.85))], [v3((0, 0, -1))], tmax=0.6)
    p = h[0] if ok[0] else v3((sx * x, 0.075, 1.5))
    return p, _fgrad(f.fn, p)


def epaulette_field():
    """modern_kit: a gunmetal (9) shoulder board along the top of his left shoulder (from the collar to the shoulder's
    point, its outer end rounded), amber (6) piping round it and three amber rank bars across it, a button (9) at its
    inner end."""
    fd = Field("Epaulette")
    p0, n0 = shoulder_spot("L", 0.12, 0.01)
    p1, n1 = shoulder_spot("L", 0.98, 0.01)
    ax = norm(p1 - p0)
    L = float(np.linalg.norm(p1 - p0))
    nrm = norm(n0 + n1)
    across = norm(np.cross(nrm, ax))
    R = np.stack([ax, across, nrm], 1)
    c = (p0 + p1) / 2 + nrm * 0.008
    fd.add(RoundBox(c, (L / 2 + 0.01, 0.042, 0.007), 0.006, R=R), 0.0, 9)
    fd.add(Ellipsoid(p1 + nrm * 0.006 - ax * 0.004, (0.05, 0.05, 0.012), R=R), 0.012, 9)
    def edge(P):
        q = (P - c.astype(F)) @ R.astype(F)
        inner = np.maximum(np.abs(q[:, 0]) - F(L / 2 - 0.004), np.abs(q[:, 1]) - F(0.031))
        return np.maximum(np.maximum(-inner, F(-0.002) - q[:, 2]), np.abs(q[:, 0]) - F(L / 2 + 0.012))
    fd.paint(Func(edge, c - 0.2, c + 0.2), 6)
    for k in range(3):
        bc = c + ax * (-L * 0.25 + L * 0.2 * k) + nrm * 0.008
        fd.add(RoundBox(bc, (0.006, 0.028, 0.003), 0.002, R=R), 0.002, 6)
    fd.add(Sphere(p0 + nrm * 0.016 - ax * 0.004, 0.011), 0.003, 9)
    return fd


PAUL_C = J["shoulder_R"] + v3((-0.025, 0.0, 0.035))     # the pauldron dome's centre (over his right shoulder)
PAUL_OUT = norm(v3((-0.82, 0.0, 0.57)))                  # its axis (up and out)
PAUL_RAD = (0.19, 0.175, 0.165)                          # its radii (out across the shoulder, front-back, up)


def _paul_R():
    return rot_from_axes(z_axis=PAUL_OUT, y_axis=(0, 1, 0))


def pauldron_field():
    """modern_kit: the salvaged robot pauldron, white (7) armour plastic: a domed plate over his right shoulder (a raised
    rolled rim, a panel line, dents and scuffs, bolts (9) where it was torn off its machine), two lames below it over his
    upper arm; the Resistance's amber (6) chevron sprayed on its dome; black (5) straps holding it on."""
    fd = Field("Pauldron")
    R = _paul_R()
    dome = Ellipsoid(PAUL_C, PAUL_RAD, R=R)
    out = PAUL_OUT
    tex = lambda P: F(0.0006) * NOISE(P * F(50)) + F(0.0009) * NOISE(P * F(12))
    lo, hi = PAUL_C - 0.3, PAUL_C + 0.3
    def keep(P):
        h = (P - PAUL_C.astype(F)) @ out.astype(F)
        return F(0.035) - h
    fd.add(Inter(Shell(dome, 0.0, 0.018, pad=0.04, disp=tex, disp_amp=0.0012), Func(keep, lo, hi), 0.006), 0.0, 7)
    # the rolled rim round its edge
    def rim(P):
        h = (P - PAUL_C.astype(F)) @ out.astype(F)
        return np.maximum(np.abs(h - F(0.047)) - F(0.012), F(0.0) - h)
    fd.add(Inter(Shell(dome, 0.006, 0.024, pad=0.05), Func(rim, lo, hi), 0.004), 0.006, 7)
    # a panel line across the dome, dents
    fd.sub(Inter(Shell(dome, 0.009, 0.006, pad=0.05), Func(lambda P: np.abs((P - PAUL_C.astype(F)) @ R[:, 1].astype(F) - F(0.04)) - F(0.0025), lo, hi), 0.001), 0.0015)
    for d_ in ((0.5, -0.4, 0.75), (-0.2, 0.55, 0.8), (0.1, -0.1, 1.0)):
        dd = norm(R @ v3(d_))
        p = PAUL_C + dd * float(1.0 / np.linalg.norm((R.T @ dd) / v3(PAUL_RAD))) + dd * 0.012
        fd.sub(Sphere(p, 0.016), 0.006)
    # bolts round its inner edge (torn from the machine)
    for k in range(5):
        a = math.radians(140 + 20 * k)
        dd = norm(R @ v3((math.cos(a) * 0.9, math.sin(a) * 0.9, 0.42)))
        p = PAUL_C + dd * float(1.0 / np.linalg.norm((R.T @ dd) / v3(PAUL_RAD))) + dd * 0.012
        fd.add(Cylinder(p, 0.009, 0.012, rr=0.003, R=rot_from_axes(z_axis=dd)), 0.002, 9)
    # the amber chevron sprayed on the dome (a bold V pointing down its outside)
    def chevron(P):
        q = (P - PAUL_C.astype(F)) @ R.astype(F)
        u, v = q[:, 1], q[:, 0]                                  # (u: front-back, v: from the neck out across the shoulder)
        ch = np.abs(v - F(0.02) - np.abs(u) * F(0.9)) - F(0.024)
        return np.maximum(np.maximum(ch, np.abs(u) - F(0.1)), F(0.0) - q[:, 2])
    fd.paint(Func(chevron, lo, hi), 6)
    # two lames over his upper arm
    sh, el = J["shoulder_R"], J["elbow_R"]
    uax = norm(el - sh)
    arm = Field("ArmR")
    for p, k in _sleeve_prims("R")[:3]:
        arm.add(p, k)
    def lame(P, s0, s1):
        s = (P - sh.astype(F)) @ uax.astype(F)
        q = P - sh.astype(F) - s[:, None] * uax.astype(F)
        o = v3((-1.0, 0.0, 0.0)) - uax * float(v3((-1, 0, 0)) @ uax)
        fac = (q @ norm(o).astype(F)) / (np.sqrt((q * q).sum(1)) + F(1e-6))
        return np.maximum(np.maximum(F(s0) - s, s - F(s1)), F(-0.25) - fac)
    alo, ahi = np.minimum(sh, el) - 0.2, np.maximum(sh, el) + 0.2
    for s0, s1, off in ((0.07, 0.125, COAT_OUT + 0.024), (0.12, 0.17, COAT_OUT + 0.014)):
        fd.add(Inter(Shell(arm, off, 0.014, pad=0.08, disp=tex, disp_amp=0.001), Func(lambda P, s0=s0, s1=s1: lame(P, s0, s1), alo, ahi), 0.005), 0.004, 7)
    # the straps: one round his upper arm under the lames, one across the front of his shoulder to his armpit
    fd.add(Inter(Shell(arm, COAT_OUT + 0.004, 0.009, pad=0.08), Func(lambda P: np.abs((P - sh.astype(F)) @ uax.astype(F) - F(0.19)) - F(0.014), alo, ahi), 0.003), 0.004, 5)
    return fd


# ======================================================================================= the plasma sidearm
GUN_G0 = v3((-0.33, -0.52, 0.94))         # rest: the grip's middle (floating before his right hip) ...
GUN_A0 = v3((0.0, -1.0, 0.0))             # ... the muzzle pointing ahead
GUN_U0 = v3((0.0, 0.0, 1.0))
GUN_S0 = np.cross(GUN_A0, GUN_U0)         # (his right: the pistol's right side as he holds it)
BAR_H = 0.084                             # the barrel's axis above the grip's middle
MUZZLE_U = 0.352                          # the muzzle's face
GUN_SCALE = 1.3                           # (drawn at 1, shipped 1.3 times bigger about the grip: it reads from above)


def _gr(u, v=0.0, h=0.0):
    return GUN_G0 + GUN_A0 * u + GUN_S0 * v + GUN_U0 * h


def gl(u, v=0.0, h=0.0):
    return GUN_G0 + (GUN_A0 * u + GUN_S0 * v + GUN_U0 * h) * GUN_SCALE


def grip_axis():
    """The grip's axis (from its foot up toward the frame: raked, the foot further back)."""
    return norm(GUN_U0 * 0.94 + GUN_A0 * 0.34)


def muzzle():
    return gl(MUZZLE_U, 0.0, BAR_H)


CH_U = (0.125, 0.215)                     # the plasma chamber (along the barrel)


def pistol_field():
    """modern_kit: a gunmetal (9) frame and barrel shroud (vented), the muzzle brake; a salvaged white (7) robot shell over
    the receiver's top with an amber (6) slash; a black rubber (12) grip wrapped in tape (5); the chamber's cage
    (gunmetal bars and rings round the glowing cell); black (5) cables from the cell to the grip; the trigger and its
    guard (9)."""
    fd = Field("Pistol")
    A, U, S = GUN_A0, GUN_U0, GUN_S0
    Rg = np.stack([S, A, U], 1)
    Ra = rot_from_axes(z_axis=A)
    tex = lambda P: F(0.0005) * NOISE(P * F(90))
    # the grip, taped
    ga = grip_axis()
    gs = norm(np.cross(ga, S))
    Rgr = np.stack([S, gs, ga], 1)
    fd.add(RoundBox(_gr(0.0, 0.0, -0.004), (0.02, 0.027, 0.06), 0.015, R=Rgr, disp=tex, disp_amp=0.001), 0.0, 12)
    for k in range(3):
        fd.add(RoundBox(_gr(0.0, 0.0, -0.004) + ga * (-0.035 + 0.03 * k), (0.0225, 0.0295, 0.008), 0.012, R=Rgr), 0.003, 5)
    fd.add(RoundBox(_gr(0.0) - ga * 0.064 + gs * -0.004, (0.023, 0.031, 0.009), 0.006, R=Rgr), 0.006, 9)       # its foot
    # the frame: a chunky receiver, its back sloped, a heat sink behind
    fd.add(RoundBox(_gr(0.0, 0.0, 0.075), (0.033, 0.1, 0.04), 0.016, R=Rg), 0.012, 9)
    fd.sub(RoundBox(_gr(-0.13, 0.0, 0.124), (0.06, 0.04, 0.03), 0.01, R=Rg @ euler(0.6, 0, 0)), 0.01)
    for k in range(3):
        fd.add(RoundBox(_gr(-0.112, 0.0, 0.05 + 0.017 * k), (0.03, 0.012, 0.0045), 0.003, R=Rg), 0.003, 9)
    # the salvaged robot shell over its top: white, a sprayed amber slash
    fd.add(RoundBox(_gr(0.0, 0.0, 0.118), (0.038, 0.092, 0.016), 0.014, R=Rg, disp=tex, disp_amp=0.001), 0.006, 7)
    def slash(P):
        q = (P - _gr(0.0, 0.0, 0.118).astype(F)) @ Rg.astype(F)
        return np.maximum(np.abs((q[:, 1] + q[:, 0] * F(0.8)) - F(0.02)) - F(0.013), F(-0.006) - q[:, 2])
    fd.paint(Func(slash, _gr(0.0) - 0.2, _gr(0.0) + 0.2), 6)
    fd.sub(Sphere(_gr(-0.05, 0.03, 0.134), 0.01), 0.005)                                              # a dent
    # the chamber's cage: rings at its ends, four bars along it
    for u in CH_U:
        fd.add(Cylinder(_gr(u, 0.0, BAR_H), 0.031, 0.016, rr=0.005, R=Ra), 0.004, 9)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        off = S * (math.cos(a) * 0.028) + U * (math.sin(a) * 0.028)
        fd.add(RoundCone(_gr(CH_U[0], 0.0, BAR_H) + off, _gr(CH_U[1], 0.0, BAR_H) + off, 0.0055, 0.0055), 0.003, 9)
    # the barrel shroud with vents, the muzzle brake
    fd.add(Cylinder(_gr(0.27, 0.0, BAR_H), 0.029, 0.11, rr=0.01, R=Ra), 0.006, 9)
    for k in range(3):
        fd.sub(RoundBox(_gr(0.236 + 0.026 * k, 0.0, BAR_H + 0.026), (0.022, 0.0065, 0.008), 0.003, R=Rg), 0.002)
    fd.add(Cylinder(_gr(0.336, 0.0, BAR_H), 0.035, 0.034, rr=0.01, R=Ra), 0.006, 9)
    for sv in (-1, 1):
        fd.sub(RoundBox(_gr(0.334, sv * 0.034, BAR_H), (0.008, 0.012, 0.012), 0.004, R=Rg), 0.003)    # side ports
    fd.sub(Cylinder(_gr(MUZZLE_U - 0.002, 0.0, BAR_H), 0.021, 0.036, rr=0.004, R=Ra), 0.003)          # the bore
    # a salvaged white cell under the shroud
    fd.add(Cylinder(_gr(0.25, 0.0, BAR_H - 0.042), 0.017, 0.09, rr=0.007, R=Ra), 0.006, 7)
    fd.paint(Cylinder(_gr(0.25, 0.0, BAR_H - 0.042), 0.02, 0.014, R=Ra), 6)
    # cables from the chamber's back down round to the grip's front
    for sv in (-1, 1):
        pts = [_gr(CH_U[0] + 0.004, sv * 0.026, BAR_H - 0.02), _gr(0.11, sv * 0.034, 0.03), _gr(0.07, sv * 0.026, 0.0),
               _gr(0.034, sv * 0.018, -0.02)]
        fd.add(Chain(pts, [0.0065] * 4, k=0.004), 0.003, 5)
    # the trigger and its guard
    fd.add(Chain([_gr(0.03, 0.0, 0.04), _gr(0.034, 0.0, 0.004), _gr(0.104, 0.0, 0.004), _gr(0.116, 0.0, 0.04)], [0.0062] * 4, k=0.003), 0.003, 9)
    fd.add(RoundCone(_gr(0.066, 0.0, 0.042), _gr(0.072, 0.0, 0.017), 0.0058, 0.0046), 0.002, 9)
    return ScaledField(fd, GUN_G0, GUN_SCALE)


def chamber_field():
    """The plasma cell in its cage and the core deep in the muzzle (they glow amber: `GlowChamber`)."""
    fd = Field("Chamber")
    Ra = rot_from_axes(z_axis=GUN_A0)
    fd.add(Cylinder(_gr(sum(CH_U) / 2, 0.0, BAR_H), 0.023, CH_U[1] - CH_U[0], rr=0.008, R=Ra), 0.0)
    fd.add(Cylinder(_gr(0.33, 0.0, BAR_H), 0.02, 0.008, rr=0.003, R=Ra), 0.0)
    return ScaledField(fd, GUN_G0, GUN_SCALE)


# ======================================================================================= the killswitch
SW_SCALE = 1.6
SW_HEAD = 0.1                             # the head's middle this far along the rod from the grip's middle (drawn size)
SW_TOP = 0.145                            # the button's top


def switch_rest():
    """Rest pose: (G: the grip's middle, A: along the rod toward the button (up), U: the guard's side (outward)), the rod
    hanging in its holder on his left hip, its head up."""
    p, n = belt_spot(HOLDER_A, 0.004)
    A = norm(Z - n * 0.12)
    G = p + n * 0.062 - Z * 0.12
    U = norm(n - A * float(n @ A))
    return G, A, U


def _sw(G, A, U, s):
    """Drawn-size point along the rod: s along A, from the grip's middle."""
    return G + A * s


def switch_field():
    """modern_kit: the control rod: a black rubber (12) grip wrapped in tape (5), a gunmetal (9) pommel with a lanyard ring
    and a collar; the white (7) robot head with two amber (6) stripes, a stubby antenna (5, a gunmetal tip); the button's
    gunmetal bezel and its flipped-open guard."""
    fd = Field("Switch")
    G, A, U = switch_rest()
    V_ = norm(np.cross(A, U))
    Ra = rot_from_axes(z_axis=A, x_axis=U)
    fd.add(RoundCone(G - A * 0.06, G + A * 0.05, 0.018, 0.019), 0.0, 12)
    for k in range(3):
        fd.add(Torus(G + A * (-0.04 + 0.03 * k), 0.0195, 0.004, R=Ra), 0.002, 5)
    fd.add(Cylinder(G - A * 0.068, 0.022, 0.016, rr=0.006, R=Ra), 0.004, 9)                         # the pommel
    fd.add(Torus(G - A * 0.084, 0.012, 0.003, R=rot_from_axes(z_axis=V_)), 0.002, 9)
    fd.add(Cylinder(G + A * 0.058, 0.024, 0.014, rr=0.004, R=Ra), 0.004, 9)                          # the collar
    H = G + A * SW_HEAD
    fd.add(Cylinder(H, 0.033, 0.064, rr=0.012, R=Ra), 0.006, 7)                                      # the white head
    for s in (-0.014, 0.012):
        fd.paint(Cylinder(H + A * s, 0.036, 0.008, R=Ra), 6)
    fd.sub(Sphere(H + U * 0.034 + A * 0.004, 0.009), 0.004)                                          # a scuff
    fd.add(Cylinder(G + A * (SW_TOP - 0.01), 0.026, 0.012, rr=0.004, R=Ra), 0.004, 9)                # the button's bezel
    hinge = G + A * (SW_TOP - 0.006) + U * 0.026
    gd = norm(A * 0.85 + U * 0.55)                                                                   # the guard, flipped open
    fd.add(RoundBox(hinge + gd * 0.024, (0.004, 0.022, 0.024), 0.003, R=np.stack([norm(np.cross(gd, V_)), V_, gd], 1)), 0.003, 9)
    fd.add(Cylinder(hinge, 0.006, 0.036, rr=0.002, R=rot_from_axes(z_axis=V_)), 0.002, 9)
    ab = H - U * 0.03 + A * 0.01                                                                     # the antenna
    fd.add(RoundCone(ab, ab + norm(A * 0.8 - U * 0.6) * 0.07, 0.0065, 0.0045), 0.003, 5)
    fd.add(Sphere(ab + norm(A * 0.8 - U * 0.6) * 0.072, 0.008), 0.002, 9)
    return ScaledField(fd, G, SW_SCALE)


def button_field():
    """The killswitch's thumb button (it glows amber: `GlowButton`, on the `button` bone)."""
    fd = Field("Button")
    G, A, U = switch_rest()
    fd.add(Ellipsoid(G + A * SW_TOP, (0.018, 0.018, 0.011), R=rot_from_axes(z_axis=A)), 0.0)
    return ScaledField(fd, G, SW_SCALE)


def switch_point():
    """(rest) The button's top: the killswitch's point (the game's pulse)."""
    G, A, U = switch_rest()
    return G + A * (SW_TOP + 0.011) * SW_SCALE


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.24, 1.63)), 0.04, 0.45), (hp((-0.095, -0.19, 1.62)), 0.03, 0.25)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.088, -0.15, 1.6)), 0.055, 0.5), (hp((sx * 0.157, 0.035, 1.66)), 0.045, 0.5)]
    return pts


# ======================================================================================= build config
GLB_NAME = "vega"
ROOT_NAME = "HeroVegaHQ"
TEX_PREFIX = "hero"
MAT_NAME = "VegaMat"
MESH_NAME = "Vega"
BASE_MODULE = "vega_base"
ANIM_MODULE = "anim_vega"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Temples", "Under", "Armour", "Coat", "Sash", "Belt", "Epaulette", "Pauldron",
         "Trousers", "Boots", "Pistol", "Chamber", "Switch", "Button"]
REGION_PARTS = ("Skin", "Armour", "Coat", "Sash", "Belt", "Epaulette", "Pauldron", "Trousers", "Pistol", "Switch")
KIT = dict(black=(0.05, 0.05, 0.055), red=AMBER, white=WHITE, gunmetal=GUNMETAL, rubber=(0.07, 0.07, 0.075), coyote=TEAL)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_VegaSkin", "base": (0.8, 0.6, 0.48), "ruddy": (0.84, 0.5, 0.42), "lips": (0.66, 0.4, 0.36),
                      "brow": ((0.11, 0.1, 0.1), (0.3, 0.29, 0.29)),
                      "extra": ((LASH, (0.07, 0.06, 0.06), 0.5), (STUBBLE, (0.38, 0.34, 0.33), 0.55, 0.4),
                                (SCAR, (0.9, 0.68, 0.62), 0.45), (GLOVE, BLACK, 0.75))}),
    "Hair": ("hair", {"name": "HQ_VegaHair", "base": (0.12, 0.11, 0.11), "hi": (0.36, 0.35, 0.36), "low": (0.04, 0.035, 0.035),
                      "streak": (0.08, 0.075, 0.075), "tint": (0.16, 0.15, 0.15), "fleck": (0.62, 0.62, 0.64), "fleck_amt": 0.45}),
    "Temples": ("hair", {"name": "HQ_VegaTemples", "base": (0.48, 0.48, 0.5), "hi": (0.72, 0.72, 0.74), "low": (0.28, 0.28, 0.3),
                         "streak": (0.38, 0.38, 0.4), "tint": (0.52, 0.52, 0.54)}),
    "Under": ("uniform", {"name": "HQ_VegaUnder", "base": (0.1, 0.1, 0.11)}),
    "Armour": ("modern_kit", dict(KIT, name="HQ_VegaArmour", base=GUNMETAL, weave=0.0, gloss=0.45)),
    "Coat": ("modern_kit", dict(KIT, name="HQ_VegaCoat", base=CHARCOAL, weave=1.0)),
    "Sash": ("uniform", {"name": "HQ_VegaSash", "base": AMBER, "facing": (0.98, 0.78, 0.36)}),
    "Belt": ("modern_kit", dict(KIT, name="HQ_VegaKit", base=BLACK, weave=0.0)),
    "Epaulette": ("modern_kit", dict(KIT, name="HQ_VegaKit", base=BLACK, weave=0.0)),
    "Pauldron": ("modern_kit", dict(KIT, name="HQ_VegaPlate", base=WHITE, weave=0.0, gloss=0.5)),
    "Trousers": ("uniform", {"name": "HQ_VegaTrousers", "base": GUNMETAL, "facing": GUNMETAL, "buff": GUNMETAL, "brass": GUNMETAL,
                             "black": (0.05, 0.05, 0.055)}),
    "Boots": ("leather_dyed", {"name": "HQ_VegaBoots", "base": (0.075, 0.07, 0.07), "dyed": (0.035, 0.033, 0.033), "worn_c": (0.3, 0.29, 0.29)}),
    "Pistol": ("modern_kit", dict(KIT, name="HQ_VegaPistol", base=GUNMETAL, weave=0.0)),
    "Switch": ("modern_kit", dict(KIT, name="HQ_VegaSwitch", base=GUNMETAL, weave=0.0)),
}
GLOW = {"Chamber": (AMBER_GLOW, 1.3, 0.55), "Button": (AMBER_GLOW, 1.2, 0.55)}
LOW_TARGETS = {"Skin": 5600, "Teeth": 90, "Hair": 900, "Temples": 700, "Under": 300, "Armour": 1100, "Coat": 4600, "Sash": 1500,
               "Belt": 1100, "Epaulette": 700, "Pauldron": 1700, "Trousers": 1500, "Boots": 1100, "Pistol": 2200, "Chamber": 160,
               "Switch": 900, "Button": 80}
AO_EXCLUDE = ["Pistol", "Chamber", "Switch", "Button"]
BAKE_APART = (["Pistol", "Chamber"], (3.0, 0.0, 0.0))     # (the pistol floats before him)


def prop_bones():
    """The pistol and the killswitch ride parentless bones (every clip poses them in world space, anim_vega.py); the
    button is a child of the killswitch (it swells when he thumbs it)."""
    G, A, U = switch_rest()
    tip = switch_point()
    return [("pistol", GUN_G0, muzzle(), None),
            ("switch", G, tip, None),
            ("button", tip - A * 0.03, tip, "switch")]


COAT_BONES = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L", "hand.R", "hand.L",
                      "thigh.R", "thigh.L"}
COAT_CAPS = {"thigh.R": 0.45, "thigh.L": 0.45, "hand.R": 0.25, "hand.L": 0.25}
BODY_BONES = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L"}


def coat_weights(ob, skin_ob, arm):
    """The coat follows his body and arms; its skirts swing from his hips, pulled a little by his thighs; the cuffs ride
    his forearms."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=COAT_BONES, caps=COAT_CAPS)
    groups = {}
    for side in ("R", "L"):
        a, b, ax = cuff_frame(side)
        for v in ob.data.vertices:
            p = np.array(v.co)
            if _seg_dist(p[None].astype(F), a - ax * 0.02, b + ax * 0.01)[0] < CUFF_R[1] + 0.03 and abs(p[0]) > 0.45:
                for g in list(ob.vertex_groups):
                    g.remove([v.index])
                s = float((p - a) @ ax) / float(np.linalg.norm(b - a))
                k = max(0.0, min(1.0, (s - 0.75) / 0.25)) * 0.2
                _blend_add(ob, groups, v.index, {"forearm." + side: 1.0 - k, "hand." + side: k})


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Temples": ("rigid", "head"),
        "Under": ("transfer", TORSO, None),
        "Armour": ("transfer", TORSO | {"clavicle.R", "clavicle.L"}, None),
        "Coat": ("custom", coat_weights),
        "Sash": ("transfer", COAT_BONES, COAT_CAPS),
        "Epaulette": ("transfer", COAT_BONES, COAT_CAPS),
        "Pauldron": ("transfer", COAT_BONES, COAT_CAPS),
        "Belt": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.3, "thigh.L": 0.3}),
        "Trousers": ("transfer", TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Pistol": ("rigid", "pistol"), "Chamber": ("rigid", "pistol"),
        "Switch": ("rigid", "switch"), "Button": ("rigid", "button"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Pistol", "Pauldron", "Epaulette", "Switch"):
        return 1.15
    if part in ("Trousers", "Boots", "Under"):
        return 0.75
    return 1.0


def trousers_field():
    fd = kn.trousers_field()
    fd.name = "Trousers"
    return fd


def boots_field():
    return kn.boots_field()


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Temples", temples_field(), 0.0022 if fine else 0.0032),
        ("Under", under_field(), 0.0026 if fine else 0.0036),
        ("Armour", armour_field(), 0.0024 if fine else 0.0034),
        ("Coat", coat_field(), 0.0028 if fine else 0.0038),
        ("Sash", sash_field(), 0.0022 if fine else 0.0032),
        ("Belt", belt_field(), 0.0018 if fine else 0.0026),
        ("Epaulette", epaulette_field(), 0.0016 if fine else 0.0024),
        ("Pauldron", pauldron_field(), 0.0022 if fine else 0.0032),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Pistol", pistol_field(), 0.0014 if fine else 0.002),
        ("Chamber", chamber_field(), 0.0012),
        ("Switch", switch_field(), 0.0014 if fine else 0.002),
        ("Button", button_field(), 0.0012),
    ]
