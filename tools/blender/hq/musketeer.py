"""The Musketeer (HQ tower, Gunpowder Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A lean, weathered veteran in his late thirties, long-limbed and rangy (a contrast to the stocky Crossbowman): sharp
features, a long straight nose, keen narrowed eyes under straight dark brows, high cheekbones over lean cheeks, dark
hair falling to his shoulders, a pointed beard and a moustache with upturned ends. A broad-brimmed black felt hat, its
brim pinned up on his left side with a gold brooch, a gold-ochre band round its crown and a big crimson-and-white ostrich
plume curling over it. A buff-leather coat (tan-ochre, short skirts to mid-thigh, split before and behind, its sleeves
ending at the elbow, gold buttons) with a falling collar of white linen; the crimson sleeves of his doublet from the
elbow to white linen cuffs; a crimson sash knotted at his right hip, its ends fringed in gold. A crimson baldric edged
in gold over his right shoulder carrying a cup-hilted rapier at his left hip; over his left shoulder a bandolier hung
with the "twelve apostles" (small wooden powder flasks, black with brass caps, on cords), a priming flask and a leather
bullet bag. Crimson breeches; tall buff boots with wide turned-down bucket cuffs.

The musket: a matchlock nearly as long as he is tall (1.58 m): a walnut stock with a fishtail butt, a long round iron barrel
held by brass bands, a brass butt plate and trigger guard, the lock plate with its pan, the serpentine (an S-shaped
arm) holding the smouldering match (its glowing tip ships as its own emissive mesh, "Ember"), the match cord looped
round the stock's wrist, the ramrod under the barrel. The forked rest: an ash staff with an iron U-fork at its top and
an iron spike at its foot.

His build is the Spear Guard's way of building a body (spear.py) on longer, leaner bones, with his own head. The
musket, its ramrod, the rest and one of the apostles (the charge he pours) are props on bones of their own with no
parent, posed directly in every frame ("world" aims in anim_musketeer.py), so they can pass from hand to hand; the
serpentine is a bone of the musket's (it dips the match into the pan at the shot)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add

# lean and rangy: the Spear Guard's skeleton with longer legs and arms, narrower shoulders, everything above the hips
# 3 cm higher
J = {
    "root": (0.0, 0.03, 0.85),
    "spine": (0.0, 0.03, 1.01),
    "chest": (0.0, 0.05, 1.21),
    "neck": (0.0, 0.065, 1.45),
    "head": (0.0, 0.02, 1.57),
    "head_end": (0.0, -0.02, 1.97),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.325, 0.07, 1.41)
    J["elbow_" + _s] = (_x * 0.53, 0.1, 1.14)
    J["wrist_" + _s] = (_x * 0.68, 0.04, 0.89)
    J["hip_" + _s] = (_x * 0.14, 0.04, 0.8)
    J["knee_" + _s] = (_x * 0.16, 0.0, 0.45)
    J["ankle_" + _s] = (_x * 0.17, 0.06, 0.11)
    J["toe_" + _s] = (_x * 0.19, -0.17, 0.035)
J = {k: v3(v) for k, v in J.items()}

SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE = 0, 1, 2, 3, 4, 8, 9

# the head is designed in the Spear Guard's head coordinates (hp), lifted 3 cm with the shoulders
HS = 1.08
DZ = 0.01
HPIV = v3((0.0, 0.02, 1.51))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


def hinv(P):
    """World points -> the head's design coordinates (the inverse of hp)."""
    return (P - HPIV.astype(F)) / F(HS) + HPIV.astype(F) - np.array([0, 0, DZ], F)


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.168, 0.188, 0.186)) * HS
EYE_R = hr(0.035)
IRIS = ((0.2, 0.15, 0.08), (0.46, 0.36, 0.18))          # hazel-brown eyes (prep.paint_eyes)


def eye_c(sx):
    return hp((sx * 0.068, -0.152, 1.678))


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


# ======================================================================================= hands & feet (the Spear Guard's)
def hand_frame(side):
    sx = -1 if side == "R" else 1
    el, wr = J["elbow_" + side], J["wrist_" + side]
    f = norm((wr - el) + v3((sx * 0.06, 0, -0.10)))
    n = v3((-sx, 0, 0))
    n = norm(n - f * (n @ f))
    t = np.cross(f, n)
    if t[1] > 0:
        t = -t
    return wr, f, n, t


HAND_S = 0.98
CURLS = {"R": (1.45, 1.6, 1.2), "L": (1.45, 1.6, 1.2)}           # both fists: the musket, the rest, the ramrod


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    """A fist, as the Spear Guard's (spear.hand), a little leaner: long bony fingers."""
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.059, 0.03, 0.066)) * s, 0.027 * s, R=Rp), 0.027, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.032, 0.027, 0.05)) * s, R=Rp), 0.018, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.042, 0.014, -0.014, -0.042)
    lens = (0.98, 1.05, 0.98, 0.82)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.0195 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.053 * ls * s, 0.043 * ls * s, 0.035 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.011, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.0145 * s), 0.009, SKIN)                 # knuckles
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.011, (0.012, 0.007, 0.015), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.05 * s + n * 0.011
    d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
    d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.024 * s, 0.021 * s, 0.018 * s], k=0.008), 0.018, SKIN)


def foot(fd, side, s=1.04):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.1)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    fd.add(Sphere(an + v3((0, 0.042, -0.05)), 0.056 * s), 0.028, SKIN)
    fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.07)), v3((0.062, 0.118, 0.034)) * s, 0.031, R=Rz), 0.031, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.036 + v3((0, 0, -0.03)), v3((0.06, 0.085, 0.046)) * s, R=Rz), 0.028, SKIN)
    inner = -sx
    for i, (o, r) in enumerate(((0.048, 0.026), (0.02, 0.02), (-0.005, 0.018), (-0.027, 0.016), (-0.046, 0.015))):
        base = an + fwd * (0.164 - 0.011 * i - (0.0 if i else -0.004)) + rgt * (o * inner) + v3((0, 0, -0.08))
        tip = base + fwd * (0.029 + r * 0.4) + v3((0, 0, -0.004))
        base[2] = 0.024 + r * 0.55
        tip[2] = 0.019 + r * 0.5
        fd.add(RoundCone(base, tip, r, r * 0.92), 0.011, SKIN)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.048, 0.0, 0.0)), 0.022), 0.018, SKIN)


# ======================================================================================= head
def stubble_mask(P):
    """Cheeks and jaw (design coordinates): a shadow of stubble round the trimmed beard."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.6) + F(0.02) * smoothstep(0.06, 0.15, ax)
    return np.maximum(np.maximum(z - top, F(1.45) - z), y - F(0.03))


def head(fd):
    """A lean, sharp-featured face: a narrow jaw and a pointed chin, high cheekbones over lean cheeks, a long straight
    nose running on from the brow, straight dark brows drawn down at their inner ends over keen narrowed eyes, crow's
    feet and a furrow between the brows (weathered), a firm mouth."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.05, 1.592), (0.128, 0.126, 0.122)), 0.07, SKIN)                           # a lean jaw
    fd.add(E((0, -0.132, 1.503), (0.07, 0.064, 0.066)), 0.05, SKIN)                           # a narrow, pointed chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.116, 1.64), 0.047), 0.05, SKIN)                               # high cheekbones
        fd.add(S((sx * 0.116, -0.042, 1.562), 0.043), 0.05, SKIN)                              # jaw corners
        pts = [hp((sx * 0.15, -0.055, 1.744)), hp((sx * 0.114, -0.13, 1.752)), hp((sx * 0.06, -0.174, 1.75)), hp((0.0, -0.184, 1.75))]
        fd.add(Chain(pts, [hr(0.012), hr(0.022), hr(0.026), hr(0.026)], k=hr(0.022)), hr(0.035), SKIN)     # brow ridge
        # lean cheeks: a soft hollow under each cheekbone
        fd.sub(Ellipsoid(hp((sx * 0.118, -0.118, 1.572)), v3((0.026, 0.02, 0.03)) * HS, R=euler(0, 0, sx * -0.5)), hr(0.022))
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # straight dark brows, their inner ends drawn down: a keen, level look; a furrow between them
    for sx in (-1, 1):
        pts = [hp((sx * 0.022, -0.214, 1.748)), hp((sx * 0.064, -0.21, 1.764)), hp((sx * 0.108, -0.188, 1.772)), hp((sx * 0.15, -0.146, 1.77))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.011), hr(0.013), hr(0.011), hr(0.005)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.018), hr(0.02), hr(0.018), hr(0.01)], k=hr(0.01)), BROW)
        fd.sub(RoundCone(hp((sx * 0.009, -0.212, 1.736)), hp((sx * 0.011, -0.207, 1.77)), hr(0.0022), hr(0.0016)), hr(0.003))
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.012))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0056)), Plane(ec + v3((0, 0, -hr(0.019))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.01))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(3):                                                                      # crow's feet
            a = hp((sx * (0.108 + 0.004 * k), -0.134 + 0.006 * k, 1.688 - 0.011 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.026, 0.012, 0.006 - 0.01 * k)), hr(0.002), hr(0.0013)), hr(0.003))
        fd.add(Ellipsoid(hp((sx * 0.068, -0.156, 1.646)), v3((0.024, 0.011, 0.01)) * HS), hr(0.012), SKIN)     # tired lids below
    # a long straight nose from the brow
    fd.add(RoundCone(hp((0, -0.186, 1.73)), hp((0, -0.25, 1.62)), hr(0.0145), hr(0.021)), hr(0.016), SKIN)
    fd.add(S((0, -0.252, 1.606), 0.024), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.026, -0.222, 1.598), 0.018), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.014, -0.239, 1.587)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # mouth: a firm, thin line under the moustache; a thin lower lip
    slot = [hp((-0.052, -0.172, 1.552)), hp((-0.027, -0.194, 1.548)), hp((0, -0.2, 1.547)), hp((0.027, -0.194, 1.548)), hp((0.052, -0.172, 1.552))]
    fd.sub(Chain(slot, [hr(0.0024), hr(0.003), hr(0.0034), hr(0.003), hr(0.0024)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.003)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.042, -0.172, 1.541), (-0.022, -0.188, 1.534), (0, -0.192, 1.532), (0.022, -0.188, 1.534), (0.042, -0.172, 1.541)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0065), hr(0.0072), hr(0.0065), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    for sx in (-1, 1):                                                                          # ears (under his hair: kept
        fd.add(Ellipsoid(hp((sx * 0.157, 0.035, 1.66)), v3((0.02, 0.04, 0.05)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)  # in it)


# ======================================================================================= body
def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.22), (0.245, 0.2, 0.27), R=euler(-0.12, 0, 0)), 0.0),
        (Ellipsoid((0, 0.115, 1.27), (0.272, 0.148, 0.2)), 0.06),
        (Ellipsoid((0.108, -0.124, 1.3), (0.115, 0.05, 0.08), R=euler(0.1, 0, 0.18)), 0.045),
        (Ellipsoid((-0.108, -0.124, 1.3), (0.115, 0.05, 0.08), R=euler(0.1, 0, -0.18)), 0.045),
        (Ellipsoid((0, -0.002, 1.01), (0.183, 0.163, 0.2)), 0.08),                  # a lean waist
        (Ellipsoid((0, 0.045, 0.85), (0.205, 0.163, 0.16)), 0.08),
    ]


def traps():
    return Ellipsoid((0, 0.1, 1.44), (0.218, 0.118, 0.085), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.065, 1.39), hp((0, 0.02, 1.575)), 0.088, hr(0.079))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.02, -0.005, 0.012)), 0.097)


def upper_arm_prims(side):
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    return [(RoundCone(sh, el, 0.085, 0.065), 0.05),
            (Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.022, 0)), (0.075, 0.077, 0.118), R=rot_from_axes(z_axis=el - sh)), 0.04)]


def forearm_prims(side):
    sx = -1 if side == "R" else 1
    el, wr = J["elbow_" + side], J["wrist_" + side]
    return [(RoundCone(el, wr, 0.063, 0.049), 0.035),
            (Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.079, 0.071, 0.125), R=rot_from_axes(z_axis=wr - el)), 0.04),
            (Sphere(el + v3((0, 0.025, 0)), 0.05), 0.028)]


def leg_prims(side):
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(hip, kn, 0.122, 0.08), 0.065),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.02, 0)), (0.11, 0.104, 0.18), R=rot_from_axes(z_axis=kn - hip)), 0.048),
            (Sphere(kn + v3((0, -0.028, 0.0)), 0.062), 0.038)]


def shin_prims(side):
    kn, an = J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(kn, an, 0.077, 0.052), 0.038),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.086, 0.084, 0.135), R=rot_from_axes(z_axis=an - kn)), 0.043)]


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
    # nothing of his brow passes into the brim's felt (it showed through it in specks)
    def under_brim(P):
        q = hat_local(P)
        return np.maximum(brim_sd(q), F(-0.011) - crown_sd(q)) - F(0.004)
    fd.inter(Func(lambda P: -under_brim(P), HAT_O - 0.5, HAT_O + 0.5), 0.003)
    return fd


def eyes_field():
    fd = Field("Eyes")
    for sx in (-1, 1):
        fd.add(Sphere(eye_c(sx), EYE_R))
    return fd


def teeth_field():
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009 + 0.003, -0.178, 1.551)), v3((0.008, 0.006, 0.006)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= hair, beard
def hair_hull():
    hull = Field("HairHull")
    hull.add(Ellipsoid(HEAD_C, HEAD_RAD + v3((0.016, 0.02, 0.016))), 0.0)
    hull.add(Ellipsoid(hp((0, 0.1, 1.57)), v3((0.19, 0.125, 0.18)) * HS), 0.08)                  # falling behind his neck
    hull.add(Ellipsoid(v3((0, 0.13, 1.5)), (0.235, 0.115, 0.075)), 0.07)                        # spreading on his shoulders
    return hull


def hair_field():
    """Dark hair falling in loose waves from under his hat to his shoulders, over his ears; a few locks curling on his
    collar."""
    fd = Field("Hair")
    hull = hair_hull()
    def strands(P):
        a = np.arctan2(P[:, 0], P[:, 1] - F(0.05))
        return (F(0.0034) * np.sin(a * F(40) + P[:, 2] * F(16)) + F(0.0018) * np.sin(a * F(97))
                + F(0.0016) * NOISE(P * np.array([60, 60, 10], F)) + F(0.004) * np.sin(P[:, 2] * F(38) + a * F(3)))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        # in front: behind the temples, down past the ears to the jaw (no hair on his brow: the hat sits there)
        front = np.where(ax < F(0.118), F(0.06) - y, (F(-0.07) - F(0.02) * smoothstep(1.62, 1.74, z)) - y)
        ragged = F(0.018) * np.sin(x * F(41)) + F(0.01) * np.sin(x * F(97) + F(1.1))
        bottom = (F(1.45) + ragged + F(0.07) * smoothstep(0.08, -0.06, y)) - P[:, 2]
        top = Q[:, 2] - F(1.9)                                                    # (well up inside the hat's crown)
        return np.maximum(np.maximum(front, bottom), top)
    fd.add(Inter(Shell(hull, 0.0, 0.034, pad=0.08, disp=strands, disp_amp=0.008), Func(keep, HEAD_C + v3((-0.45, -0.4, -0.5)), HEAD_C + 0.35), 0.005), 0.0)
    # loose locks curling forward onto his collar, and two falling beside his cheeks
    lk = lambda P: F(0.002) * NOISE(P * np.array([70, 70, 14], F))
    for sx in (-1, 1):
        for k, (dx, dy, L) in enumerate(((0.15, 0.08, 0.15), (0.2, 0.1, 0.12), (0.1, 0.13, 0.14))):
            a = v3((sx * dx, dy, 1.6))
            pts = [a, a + v3((sx * 0.03, -0.01, -L * 0.5)), a + v3((sx * 0.045, -0.035, -L)), a + v3((sx * 0.035, -0.055, -L - 0.025))]
            fd.add(Lock(pts, [0.028, 0.026, 0.018, 0.008], [0.012, 0.011, 0.008, 0.004], [v3((sx, 0.2, 0.1))] * 4, k=0.006,
                        disp=lk, disp_amp=0.002), 0.012)
        a = hp((sx * 0.155, -0.05, 1.72))                                         # beside the cheek, in front of the ear
        pts = [a, a + v3((sx * 0.012, -0.004, -0.08)), a + v3((sx * 0.006, 0.0, -0.16)), a + v3((sx * -0.004, 0.012, -0.2))]
        fd.add(Lock(pts, [0.024, 0.022, 0.016, 0.006], [0.011, 0.01, 0.008, 0.003], [v3((sx, -0.3, 0.0))] * 4, k=0.006,
                    disp=lk, disp_amp=0.002), 0.01)
    # it rests on his collar and stays inside the hat: cut away wherever it would pass into the coat (with the linen on
    # it), the band round his neck, or the felt of the crown
    cb = coat_base()
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    def forbidden(P):
        coat = cb.eval(P, margin=0.12) - F(COAT_FACE + 0.011)
        band = np.maximum(nk.eval(P, margin=0.08) - F(0.04), P[:, 2] - F(1.505))
        q = hat_local(P)
        felt = np.maximum(F(-0.015) - q[:, 2], F(-0.014) - crown_sd(q))
        return np.minimum(np.minimum(coat, band), felt)
    fd.inter(Func(lambda P: -forbidden(P), HEAD_C - v3((0.6, 0.6, 0.7)), HEAD_C + v3((0.6, 0.6, 0.6))), 0.004)
    return fd


def chin_hull():
    fd = Field("ChinHull")
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.05, 1.592), (0.128, 0.126, 0.122)), 0.0)
    fd.add(E((0, -0.132, 1.503), (0.07, 0.064, 0.066)), 0.05)
    return fd


def beard_field():
    """A pointed beard on his chin (a tuft under his lip growing into a point that juts down and forward) and a
    moustache sweeping out over his lip, its waxed ends curling up."""
    fd = Field("Beard")
    hairs = lambda P: F(0.0016) * NOISE(P * np.array([90, 90, 30], F)) + F(0.0009) * NOISE(P * F(170))
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        top = F(1.522) + F(0.03) * smoothstep(0.02, 0.06, np.abs(x))
        return np.maximum(np.maximum(np.abs(x) - F(0.058), z - top), np.maximum(F(1.45) - z, y + F(0.09)))
    fd.add(Inter(Shell(chin_hull(), 0.004, 0.012, pad=0.06, disp=hairs, disp_amp=0.003), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.004), 0.0)
    strands = lambda P: F(0.0022) * NOISE(P * np.array([70, 70, 20], F))
    # the point: a smooth wedge from under his lip, narrowing to a tip that juts a little forward
    key = [(0.0, (0, -0.2, 1.527), 0.03, 0.016), (0.25, (0, -0.21, 1.492), 0.035, 0.021), (0.5, (0, -0.216, 1.458), 0.028, 0.019),
           (0.75, (0, -0.218, 1.426), 0.017, 0.013), (1.0, (0, -0.214, 1.396), 0.004, 0.004)]
    tuft, ws, ts = [], [], []
    for i in range(9):
        u = i / 8.0
        for (u0, p0, w0, t0), (u1, p1, w1, t1) in zip(key, key[1:]):
            if u0 <= u <= u1:
                a = (u - u0) / (u1 - u0)
                tuft.append(hp(v3(p0) + (v3(p1) - v3(p0)) * a))
                ws.append(hr(w0 + (w1 - w0) * a))
                ts.append(hr(t0 + (t1 - t0) * a))
                break
    fd.add(Lock(tuft, ws, ts, [v3((0, -1, 0.1))] * 9, k=hr(0.016), disp=strands, disp_amp=0.003), hr(0.012))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.23, 1.584)), hp((sx * 0.034, -0.222, 1.574)), hp((sx * 0.06, -0.206, 1.566)),
               hp((sx * 0.083, -0.196, 1.571)), hp((sx * 0.097, -0.196, 1.59)), hp((sx * 0.101, -0.2, 1.615))]
        fd.add(Lock(pts, [hr(0.012), hr(0.016), hr(0.013), hr(0.009), hr(0.006), hr(0.0025)],
                    [hr(0.008), hr(0.009), hr(0.008), hr(0.006), hr(0.004), hr(0.002)],
                    [norm(v3((sx * 0.3, -1, 0.2)))] * 6, k=hr(0.005), disp=strands, disp_amp=0.002), hr(0.006))
    return fd


# ======================================================================================= the hat (black felt) and its plume
HAT_O = v3((0.0, 0.035, 1.833))            # the crown's axis at the brim (world)
HAT_R = euler(0.06, -0.08, 0.0)            # tipped a little forward and down to his right (the pinned side rides up)
CROWN_H = 0.2
CROWN_R0 = (0.198, 0.214)                  # the crown's radii at the brim (x, y) and at its top
CROWN_R1 = (0.172, 0.188)
BRIM_IN, BRIM_LEN, BRIM_HT = 0.18, 0.19, 0.0068
BRIM_UP, BRIM_DOWN = 1.2, -0.06            # the brim's slope (radians): pinned up on his left, a slight droop elsewhere


def hat_local(P):
    return ((P - HAT_O.astype(F)) @ HAT_R.astype(F)).astype(F)


def hat_world(q):
    return HAT_O + HAT_R @ v3(q)


def crown_sd(q):
    """Signed distance to the crown (hat-local points): a tapering oval with a soft rounded top edge."""
    z = q[:, 2]
    t = np.clip(z / F(CROWN_H), 0, 1)
    rx = F(CROWN_R0[0]) + F(CROWN_R1[0] - CROWN_R0[0]) * t
    ry = F(CROWN_R0[1]) + F(CROWN_R1[1] - CROWN_R0[1]) * t
    e = (np.sqrt((q[:, 0] / rx) ** 2 + (q[:, 1] / ry) ** 2) - F(1.0)) * np.minimum(rx, ry)
    dz = np.maximum(z - F(CROWN_H), F(-0.03) - z)
    rr = F(0.045)
    a = e + rr
    b = dz + rr
    return np.sqrt(np.maximum(a, 0) ** 2 + np.maximum(b, 0) ** 2) + np.minimum(np.maximum(a, b), 0) - rr


def _brim_slope(q):
    a = np.arctan2(q[:, 0], -q[:, 1])                           # 0 = in front, +pi/2 = his left
    w = smoothstep(0.22, 0.8, np.sin(a))
    return F(BRIM_DOWN) + F(BRIM_UP - BRIM_DOWN) * w, a


def brim_sd(q):
    """The brim: in the half-plane through the crown's axis at each angle, a strip from the crown (BRIM_IN) out along
    the local slope (up against the crown on his left, drooping a little elsewhere)."""
    th, a = _brim_slope(q)
    rho = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - F(BRIM_IN)
    L = F(BRIM_LEN) + F(0.008) * np.cos(a * 2)
    c, s = np.cos(th), np.sin(th)
    t = np.clip(rho * c + q[:, 2] * s, 0, L)
    dx, dz = rho - t * c, q[:, 2] - t * s
    return np.sqrt(dx * dx + dz * dz) - F(BRIM_HT)


def brim_point(a, s, out=0.0):
    """A point on the brim (hat-local): angle a from the front, s along it from the crown, `out` off its upper/outer face."""
    q = np.array([[math.sin(a) * (BRIM_IN + 0.1), -math.cos(a) * (BRIM_IN + 0.1), 0.0]], F)
    th = float(_brim_slope(q)[0][0])
    d = v3((math.sin(a), -math.cos(a), 0.0))
    p = d * (BRIM_IN + s * math.cos(th)) + v3((0, 0, s * math.sin(th)))
    nrm = d * (-math.sin(th)) + v3((0, 0, math.cos(th)))          # (the brim's upper face; on the pinned side: toward the crown)
    return p + nrm * out, nrm


def hat_field():
    """Black felt: the crown (a felt shell) and the brim, pinned up on his left; a band of gold-ochre braid round the
    crown's foot (label 5)."""
    fd = Field("Hat")
    felt = lambda P: F(0.0009) * NOISE(P * F(45)) + F(0.0006) * NOISE(P * F(120))
    lo, hi = HAT_O - v3((0.45, 0.45, 0.2)), HAT_O + v3((0.45, 0.45, 0.35))
    fd.add(Func(lambda P: np.abs(crown_sd(hat_local(P)) + F(0.006)) - F(0.006), lo, hi, disp=felt, disp_amp=0.001), 0.0)
    # (the shell is open below the brim: the head fills it)
    fd.inter(Func(lambda P: F(-0.012) - hat_local(P)[:, 2], lo, hi), 0.0)
    fd.add(Func(lambda P: np.maximum(brim_sd(hat_local(P)), F(-0.011) - crown_sd(hat_local(P))), lo, hi, disp=felt, disp_amp=0.001), 0.006)
    # the band of braid round the crown's foot
    def band(P):
        q = hat_local(P)
        return np.maximum(np.abs(crown_sd(q) - F(0.002)) - F(0.0045), np.abs(q[:, 2] - F(0.03)) - F(0.022))
    fd.add(Func(band, lo, hi, disp=lambda P: F(0.0012) * np.abs(np.sin(hat_local(P)[:, 2] * F(260))), disp_amp=0.0015), 0.003, 5)
    return fd


BROOCH_A, BROOCH_S = math.pi / 2, 0.095


def brooch_frame():
    p, n = brim_point(BROOCH_A, BROOCH_S)
    q = hat_world(p)
    out = HAT_R @ (v3((1, 0, 0)) * 1.0)
    on = HAT_R @ -n                                                  # the brim's outer face (away from the crown)
    return q, norm(on)


def brooch_field():
    """A gold brooch pinning the brim up on his left: an oval boss in a ring of beads."""
    fd = Field("Brooch")
    c, nrm = brooch_frame()
    up = norm(HAT_R @ v3((0, 0, 1)) - nrm * float((HAT_R @ v3((0, 0, 1))) @ nrm))
    side = np.cross(nrm, up)
    c = c + nrm * (BRIM_HT + 0.004)
    R = np.stack([side, up, nrm], axis=1)
    fd.add(Ellipsoid(c + nrm * 0.006, (0.026, 0.032, 0.012), R=R), 0.0)
    fd.add(Ellipsoid(c + nrm * 0.014, (0.012, 0.016, 0.008), R=R), 0.004)
    for k in range(12):
        a = 2 * math.pi * k / 12
        fd.add(Sphere(c + side * (math.cos(a) * 0.033) + up * (math.sin(a) * 0.04) + nrm * 0.004, 0.0065), 0.002)
    return fd


def hat_surface(q):
    """Signed distance to the hat's outer surface (hat-local points): the crown, and the brim where it stands out of it."""
    return np.minimum(crown_sd(q), np.maximum(brim_sd(q), F(-0.011) - crown_sd(q)))


def _hat_grad(q, h=0.002):
    g = np.zeros_like(q)
    for k in range(3):
        e = np.zeros(3, F)
        e[k] = h
        g[:, k] = (hat_surface(q + e) - hat_surface(q - e)) / F(2 * h)
    return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), F(1e-9))


def settle(pts, clear):
    """Hat-local points moved along the hat's surface normal until they sit `clear` off its surface (a feather lying on
    the felt); returns them with the surface normals there (facing out from the crown: between the crown and the
    turned-up brim the brim's would face in)."""
    q = np.array(pts, F).reshape(-1, 3)
    c = np.broadcast_to(np.array(clear, F), (len(q),))
    for _ in range(6):
        d = hat_surface(q)
        q = q - _hat_grad(q) * (d - c)[:, None]
    n = _hat_grad(q)
    e = np.zeros_like(q)
    nc = np.zeros_like(q)
    for k in range(3):
        e[:] = 0
        e[:, k] = 0.002
        nc[:, k] = (crown_sd(q + e) - crown_sd(q - e)) / F(0.004)
    nc = nc / np.maximum(np.linalg.norm(nc, axis=1, keepdims=True), F(1e-9))
    flip = np.sum(n * nc, axis=1) < 0
    n[flip] = nc[flip]
    return q, n


# the feathers' spines (hat-local, rough: settled onto the felt; the last points hang free past the brim's edge)
PLUME_UNDER = [(0.215, -0.005, 0.07), (0.215, 0.015, 0.165), (0.165, 0.045, 0.24), (0.09, 0.09, 0.262), (0.04, 0.145, 0.25),
             (0.03, 0.2, 0.2), (0.035, 0.24, 0.12), (0.045, 0.3, 0.04)]
PLUME_UNDER_HANG = [(0.05, 0.37, 0.0), (0.06, 0.41, -0.05), (0.065, 0.4, -0.1), (0.07, 0.37, -0.118)]
PLUME_OVER = [(0.218, -0.03, 0.08), (0.212, -0.012, 0.18), (0.15, 0.0, 0.262), (0.06, 0.04, 0.29), (0.0, 0.1, 0.285),
               (-0.02, 0.17, 0.235), (-0.015, 0.22, 0.15)]
PLUME_OVER_HANG = [(-0.01, 0.25, 0.09), (0.0, 0.26, 0.045)]


def plume_paths():
    """The two ostrich feathers' spines (hat-local): their quills tucked behind the brooch, lying up over the crown
    from his left and down over its back, the lower one (white) drooping off the brim behind him in a curl; the upper
    one (crimson) lies on it, toward the front."""
    def path(pts, hang, th, lift=0.0):
        clear = [th + 0.004 + lift * smoothstep(0.0, 2.0, F(i)) for i in range(len(pts))]
        q, n = settle(pts, clear)
        q[0] = pts[0]                                                   # (the quill's foot stays tucked behind the brooch)
        out = [v3(x) for x in q]
        nn = [v3(x) for x in n]
        last = nn[-1]
        for h in hang:
            out.append(v3(h))
            nn.append(norm(last * 0.6 + v3((0, 0.4, 0.5))))
        return out, nn
    under = path(PLUME_UNDER, PLUME_UNDER_HANG, 0.03)
    over = path(PLUME_OVER, PLUME_OVER_HANG, 0.022, lift=0.04)
    return under, over


def _resample(path, n_out):
    """A spine (points, normals) resampled to n_out points along a Catmull-Rom curve through it."""
    pts, ns = [v3(p) for p in path[0]], [v3(x) for x in path[1]]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    seg = len(pts) - 1
    out_p, out_n = [], []
    for k in range(n_out):
        u = k / (n_out - 1) * seg
        i = min(int(u), seg - 1)
        t = u - i
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        out_p.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        out_n.append(norm(ns[i] * (1 - t) + ns[i + 1] * t))
    return out_p, out_n


def _feather(fd, path, w_max, th, label, seed, n_st=24, lobes=9):
    """A fluffy ostrich feather along a spine: a soft flat shaft lying on the felt, fringed on both edges with rounded
    lobes of barbs that sweep back toward the tip and droop a little (a scalloped edge); the tip curls."""
    pts_l, ns_l = _resample(path, n_st)
    pts = [hat_world(p) for p in pts_l]
    ns = [norm(HAT_R @ v3(n)) for n in ns_l]
    ws, ts = [], []
    for i in range(n_st):
        u = i / (n_st - 1)
        ws.append(w_max * (0.45 + 0.55 * math.sin(min(1.0, u / 0.3) * math.pi / 2)) * (1.0 - 0.8 * max(0.0, u - 0.7) / 0.3))
        ts.append(th * (1.0 - 0.45 * u))
    fluff = lambda P, seed=seed: F(0.0022) * NOISE(P * F(70) + F(seed)) + F(0.0012) * NOISE(P * F(160) + F(seed * 2))
    fd.add(Lock(pts, [w * 0.62 for w in ws], ts, ns, k=0.02, disp=fluff, disp_amp=0.0035), 0.014, label)
    fd.add(Chain([hat_world(p) for p in path[0][:3]], [0.006, 0.005, 0.004], k=0.003), 0.004, label)     # the quill's foot
    for i in sorted({int(round(1 + (n_st - 3) * k / (lobes - 1))) for k in range(lobes)}):
        t = norm(pts[i + 1] - pts[i - 1])
        n = ns[i]
        n = norm(n - t * float(n @ t))
        b = np.cross(t, n)
        for sgn in (-1, 1):
            d = norm(b * sgn * 0.8 + t * 0.6 + n * 0.25)                # back toward the tip, curling up and out
            w = ws[i]
            c = pts[i] + b * (sgn * w * 0.52) + t * (w * 0.12) + n * (ts[i] * 0.15)
            side = norm(np.cross(n, d))
            nn = np.cross(d, side)
            R = np.stack([side, nn, d], axis=1)
            jit = 0.85 + 0.3 * (0.5 + 0.5 * math.sin(i * 2.3 + sgn * 1.1 + seed))
            fd.add(Ellipsoid(c, (w * 0.42 * jit, ts[i] * 0.78 * jit, w * 0.52 * jit), R=R, disp=fluff, disp_amp=0.003), 0.018, label)


def plume_field():
    """A big ostrich plume: a white feather (label 5) under a crimson one (0), fluffy, lying over the crown from the
    brooch and falling off the brim behind him (the crimson one on top, toward the front)."""
    fd = Field("Plume")
    under, over = plume_paths()
    _feather(fd, under, 0.066, 0.03, 5, 0.3, n_st=26, lobes=11)
    _feather(fd, over, 0.062, 0.024, 0, 1.7, n_st=18, lobes=8)
    return fd


# ======================================================================================= the buff coat
COAT_OFF, COAT_T = 0.022, 0.014
COAT_HEM = 0.6
WAIST_Z = 0.965                             # the sash's middle


def coat_base():
    b = Field("CoatBase")
    tp = torso_prims()
    for i, (p, k) in enumerate(tp):
        if i in (2, 3):                     # (no pectorals: the buff leather lies smooth over his chest)
            continue
        b.add(p, k)
    b.add(Ellipsoid((0, -0.05, 1.3), (0.24, 0.15, 0.18)), 0.06)
    b.add(traps(), 0.06)
    b.add(Func(skirt_sd, (-0.4, -0.3, 0.45), (0.4, 0.36, 1.05)), 0.07)                 # the skirts, flaring over his hips
    for side in ("R", "L"):
        el = J["elbow_" + side]
        b.add(deltoid(side), 0.055)
        for p, k in upper_arm_prims(side):
            b.add(p, k)
        b.add(Sphere(el + v3((0, 0.02, 0)), 0.052), 0.03)
    return b


SKIRT_Z = (0.5, 0.62, 0.84, 0.99)
SKIRT_RX = (0.296, 0.292, 0.28, 0.19)
SKIRT_RY = (0.222, 0.22, 0.214, 0.158)


def skirt_sd(P):
    """An oval bell (axis at y = 0.035) from the waist, flaring over the hips to the hem."""
    z = P[:, 2]
    rx = np.interp(z, SKIRT_Z, SKIRT_RX).astype(F)
    ry = np.interp(z, SKIRT_Z, SKIRT_RY).astype(F)
    e = (np.sqrt((P[:, 0] / rx) ** 2 + ((P[:, 1] - F(0.035)) / ry) ** 2) - F(1.0)) * np.minimum(rx, ry)
    return np.maximum(e, np.maximum(z - F(SKIRT_Z[-1]), F(SKIRT_Z[0]) - z))


def coat_outer():
    """The coat's outer surface (for laying the sash, the straps and the collar on it)."""
    b = coat_base()
    return Func(lambda P: b.eval(P, margin=0.1) - F(COAT_OFF + COAT_T / 2), (-0.75, -0.6, 0.4), (0.75, 0.6, 1.65))


def _coat_neck(P):
    """> 0 above the coat's round neck: low in front; the line lifts clear of the shoulders (cut only round the neck)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.03)) / F(0.2), 0, 1)
    neck_z = F(1.475) - F(0.05) * front * np.exp(-(x / F(0.11)) ** 2) + F(0.35) * smoothstep(0.13, 0.2, np.abs(x))
    return z - neck_z


def _arm_seg_dist(P, side):
    """Distance to the upper arm and forearm's axis (for limiting cuts to the arm)."""
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    out = None
    for a, b in ((sh, el), (el, wr)):
        ab = (b - a).astype(F)
        t = np.clip(((P - a.astype(F)) @ ab) / F(ab @ ab), 0, 1)
        d = np.sqrt((((a.astype(F) + t[:, None] * ab) - P) ** 2).sum(1))
        out = d if out is None else np.minimum(out, d)
    return out


def _sleeve_end(P, back=0.0):
    """> 0 past the coat's sleeve ends (at the elbows), limited to the arms."""
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        along = (P - (el - ax * back).astype(F)) @ ax.astype(F)
        on = (P[:, 0] * F(sx) > F(0.36)) & (_arm_seg_dist(P, side) < F(0.16))
        out = np.maximum(out, np.where(on, along, F(-1.0)))
    return out


def coat_hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(COAT_HEM) + F(0.012) * np.cos(a * 2) + F(0.006) * NOISE(P * F(8))


def _coat_split(P):
    """> 0 inside the skirts' openings: the front parts below the waist, widening to the hem; a vent behind."""
    z = P[:, 2]
    fw = F(0.004) + F(0.065) * smoothstep(0.95, 0.6, z)
    bw = F(0.003) + F(0.03) * smoothstep(0.9, 0.6, z)
    front = np.where((P[:, 1] < F(-0.02)) & (z < F(0.96)), fw - np.abs(P[:, 0]), F(-1.0))
    back = np.where((P[:, 1] > F(0.08)) & (z < F(0.9)), bw - np.abs(P[:, 0]), F(-1.0))
    return np.maximum(front, back)


def coat_field():
    """Buff leather, thick and soft (label 0): the body buttoned down the front, the skirts to mid-thigh split before
    and behind, the sleeves ending at the elbow in a turned-back cuff; gold-ochre lace along the hem, the openings and
    the cuffs (5); gold buttons down the front (6)."""
    fd = Field("Coat")
    base = coat_base()
    soft = lambda P: (F(0.0018) * NOISE(P * F(14)) + F(0.0008) * NOISE(P * F(45))
                      + F(0.003) * np.sin(np.arctan2(P[:, 0], -(P[:, 1] - F(0.035))) * F(11)) * smoothstep(0.86, 0.62, P[:, 2]))
    lo, hi = (-0.8, -0.6, 0.45), (0.8, 0.6, 1.65)
    def keep(P):
        k = np.maximum(np.maximum(_coat_neck(P), coat_hem(P) - P[:, 2]), _sleeve_end(P))
        return np.maximum(k, _coat_split(P))
    fd.add(Inter(Shell(base, COAT_OFF, COAT_T, pad=0.12, disp=soft, disp_amp=0.005), Func(keep, lo, hi), 0.004), 0.0)
    # the turned-back cuffs at the elbows
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        c = el - ax * 0.022
        fd.add(Inter(Func(lambda P, c=c, ax=ax, side=side: np.maximum(np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.022),
                                                                      _arm_seg_dist(P, side) - F(0.15)), c - 0.16, c + 0.16),
                     Shell(base, COAT_OFF + 0.012, 0.012, pad=0.12), 0.003), 0.004, 5)
    # the seam down the front where it buttons: a groove in the leather's face only (cut deeper, it opened a slit)
    def seam(P):
        depth = F(COAT_OFF + COAT_T / 2 - 0.0035) - base.eval(P, margin=0.06)
        return np.maximum(np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.0025), P[:, 1] + F(0.05)),
                                     np.maximum(F(0.95) - P[:, 2], P[:, 2] - F(1.44))), depth)
    fd.sub(Func(seam, (-0.05, -0.4, 0.9), (0.05, 0.0, 1.5)), 0.0015)
    # gold-ochre lace: the hem, the openings' edges
    fd.paint(Func(lambda P: P[:, 2] - (coat_hem(P) + F(0.024)), (-0.6, -0.6, 0.45), (0.6, 0.6, 0.75)), 5)
    fd.paint(Func(lambda P: -_coat_split(P) - F(0.018), (-0.2, -0.6, 0.45), (0.2, 0.6, 1.0)), 5)
    # buttons down the front
    outer = coat_outer()
    for k in range(9):
        z = 1.4 - k * 0.052
        h, ok = ray_hit(outer, [v3((0.0, -0.7, z))], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            fd.add(Sphere(h[0] + v3((0, 0.002, 0)), 0.011), 0.003, 6)
    return fd


# ======================================================================================= linen: the falling collar, cuffs
def collar_region(P):
    """< 0 on the falling band: round his neck over his shoulders and back, two square tabs over his chest."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    r = np.sqrt(x * x + (y - F(0.05)) ** 2)
    a = np.arctan2(x, -(y - F(0.05)))
    reach = F(0.205) + F(0.02) * np.abs(np.sin(a))
    body = np.maximum(r - reach, F(1.37) - z)
    tabs = np.maximum(np.maximum(np.abs(x) - F(0.112), F(0.008) - np.abs(x)), np.maximum(F(1.27) - z, y + F(0.02)))
    return np.minimum(np.maximum(body, np.where(y < F(-0.02), np.maximum(F(0.008) - np.abs(x), F(-1)), F(-1))), tabs)


def linen_field():
    """White linen: a falling band lying over the coat's shoulders, square tabs on his chest, a tie with two tassels."""
    fd = Field("Linen")
    base = coat_base()
    weave = lambda P: F(0.0008) * NOISE(P * F(60)) + F(0.0012) * NOISE(P * F(15))
    lo, hi = (-0.33, -0.3, 1.24), (0.33, 0.36, 1.56)
    off = COAT_FACE + 0.0043
    fd.add(Inter(Func(lambda P: np.maximum(collar_region(P), _coat_neck(P) - F(0.012)), lo, hi),
                 Shell(base, off, 0.0065, pad=0.12, disp=weave, disp_amp=0.0015), 0.003), 0.0)
    # the band standing round his neck
    nk = Field("NeckBand")
    nk.add(neck_prim(), 0.0)
    fd.add(Inter(Shell(nk, 0.03, 0.007, pad=0.08), Func(lambda P: np.maximum(F(1.43) - P[:, 2], P[:, 2] - F(1.5)), lo, hi), 0.003), 0.004)
    # the tie: two short strings with tassels under the band's front
    h, ok = ray_hit(Func(lambda P: base.eval(P, margin=0.1) - F(off + 0.006), lo, hi), [v3((0.0, -0.7, 1.4))], [v3((0, 1, 0))], tmax=0.8)
    if ok[0]:
        t0 = h[0] + v3((0, -0.004, 0))
        for sx in (-1, 1):
            a, b = t0 + v3((sx * 0.006, -0.002, 0.0)), t0 + v3((sx * 0.018, -0.012, -0.06))
            fd.add(Chain([a, b], [0.0035, 0.003], k=0.002), 0.003)
            fd.add(Ellipsoid(b + v3((0, 0, -0.012)), (0.008, 0.008, 0.016)), 0.004)
    return fd


def cuffs_field():
    """Turned-back cuffs of white linen at his wrists, flaring over the doublet's sleeves."""
    fd = Field("Cuffs")
    weave = lambda P: F(0.0008) * NOISE(P * F(60)) + F(0.0012) * NOISE(P * F(15))
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        a0, a1 = wr - ax * 0.078, wr - ax * 0.006
        cone = RoundCone(a0, a1, 0.082, 0.09)
        half = float(np.linalg.norm(a1 - a0)) / 2
        fd.add(Inter(Func(lambda P, a0=a0, ax=ax, half=half: np.abs((P - (a0 + ax * half).astype(F)) @ ax.astype(F)) - F(half), a0 - 0.12, a1 + 0.12),
                     Shell(cone, 0.0, 0.006, pad=0.04, disp=weave, disp_amp=0.0015), 0.002), 0.0)
        fd.add(Torus(a1 - ax * 0.002, 0.09, 0.0045, R=rot_from_axes(z_axis=ax), disp=weave, disp_amp=0.0015), 0.003)        # a rolled edge
    return fd


# ======================================================================================= crimson wool: doublet sleeves, breeches
def _wrist_cut(P, back=0.03):
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        along = (P - (wr - ax * back).astype(F)) @ ax.astype(F)
        on = (P[:, 0] * F(sx) > F(0.4)) & (_arm_seg_dist(P, side) < F(0.14))
        out = np.maximum(out, np.where(on, along, F(-1.0)))
    return out


def crimson_field():
    """Crimson wool: the doublet's sleeves from under the coat's cuffs at the elbow to the linen cuffs; breeches from
    his waist to below the knee (into the boots), full at the thigh, a gold-ochre lace down their outer seams (5)."""
    fd = Field("Crimson")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        arm = Field("Sleeve" + side)
        for p, k in forearm_prims(side):
            arm.add(p, k)
        arm.add(RoundCone(lerp(sh, el, 0.74), el, 0.064, 0.058), 0.03)
        ax_u = norm(el - sh)
        wr_ax = norm(wr - el)
        crease = lambda P, el=el, wr_ax=wr_ax: (F(0.003) * np.sin((P - el.astype(F)) @ wr_ax.astype(F) * F(70)) * F(1.0)
                                                + F(0.0012) * NOISE(P * F(30)))
        def keep(P, sh=sh, el=el, ax_u=ax_u, side=side):
            start = (lerp(sh, el, 0.82) - P.astype(np.float64)).astype(F) @ ax_u.astype(F)        # (from inside the coat sleeve)
            return np.maximum(np.maximum(start, _wrist_cut(P, 0.05)), _arm_seg_dist(P, side) - F(0.14))
        fd.add(Inter(Func(keep, el - 0.4, el + 0.4), Shell(arm, 0.01, 0.01, pad=0.08, disp=crease, disp_amp=0.004), 0.004), 0.0)
    legs = Field("Breeches")
    tp = torso_prims()
    legs.add(tp[4][0], 0.0)
    legs.add(tp[5][0], tp[5][1])
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            legs.add(p, k)
    folds = lambda P: F(0.004) * np.sin(np.arctan2(P[:, 1] - F(0.02), P[:, 0] - np.sign(P[:, 0]) * F(0.15)) * F(7)) * smoothstep(0.8, 0.55, P[:, 2]) \
        + F(0.0012) * NOISE(P * F(25))
    fd.add(Inter(Shell(legs, 0.014, 0.012, pad=0.1, disp=folds, disp_amp=0.005),
                 Func(lambda P: np.maximum(F(0.44) - P[:, 2], P[:, 2] - F(1.0)), (-0.5, -0.4, 0.3), (0.5, 0.4, 1.1)), 0.004), 0.004)
    def seam(P):
        y_ax = F(0.04) * (P[:, 2] - F(0.45)) / F(0.35)
        return np.maximum(np.maximum(np.abs(P[:, 1] - y_ax) - F(0.011), F(0.2) - np.abs(P[:, 0])),
                          np.maximum(F(0.42) - P[:, 2], P[:, 2] - F(0.8)))
    fd.paint(Func(seam, (-0.5, -0.3, 0.35), (0.5, 0.3, 0.85)), 5)
    return fd


# ======================================================================================= the sash and the baldric
def _strap_plane(top, hip_f, hip_b):
    n = norm(np.cross(hip_f - top, hip_b - top))
    return top, n


BALDRIC = _strap_plane(v3((-0.17, 0.06, 1.5)), v3((0.25, -0.12, 0.86)), v3((0.25, 0.2, 0.86)))
BANDOLIER = _strap_plane(v3((0.17, 0.06, 1.5)), v3((-0.25, -0.12, 0.9)), v3((-0.25, 0.2, 0.9)))
BALDRIC_W, BANDOLIER_W = 0.036, 0.026        # half widths


def strap_d(P, plane):
    p0, n = plane
    return np.abs((P - p0.astype(F)) @ n.astype(F))


def sash_field():
    """Crimson wool (label 0): the sash round his waist over the coat, knotted at his right hip, its two ends hanging
    down his thigh in gold fringes (5); the baldric over his right shoulder to his left hip, edged in gold (5)."""
    fd = Field("Sash")
    base = coat_base()
    lo, hi = (-0.6, -0.5, 0.5), (0.6, 0.5, 1.62)
    wrinkle = lambda P: F(0.0035) * np.sin(P[:, 2] * F(150) + F(1.5) * NOISE(P * F(6))) + F(0.0012) * NOISE(P * F(30))
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(WAIST_Z)) - F(0.036), (-0.36, -0.32, WAIST_Z - 0.07), (0.36, 0.34, WAIST_Z + 0.07)),
                 Shell(base, COAT_FACE + 0.009, 0.016, pad=0.12, disp=wrinkle, disp_amp=0.005), 0.004), 0.0)
    # the knot at the front, a little to his left, and its hanging ends
    outer = Func(lambda P: base.eval(P, margin=0.12) - F(COAT_FACE + 0.02), lo, hi)
    h, ok = ray_hit(outer, [v3((0.085, -0.7, WAIST_Z))], [v3((0, 1, 0))], tmax=0.8)
    knot = h[0] if ok[0] else v3((0.085, -0.2, WAIST_Z))
    kn_out = norm(v3((0.3, -1, 0)))
    fd.add(Ellipsoid(knot + kn_out * 0.01, (0.034, 0.03, 0.03), R=rot_from_axes(z_axis=kn_out), disp=wrinkle, disp_amp=0.004), 0.008)
    fd.add(Ellipsoid(knot + kn_out * 0.006 + v3((0.022, 0, 0.012)), (0.03, 0.022, 0.024), R=rot_from_axes(z_axis=kn_out)), 0.008)
    fringe = lambda P: F(0.004) * np.abs(np.sin((P[:, 0] + P[:, 1]) * F(260)))
    ends = []
    for k, (dx, L, sw) in enumerate(((0.0, 0.33, 1.0), (0.035, 0.27, -1.0))):
        a = knot + kn_out * 0.012 + v3((dx, 0, -0.02))
        pts = [a]
        for j in range(1, 6):
            u = j / 5
            q = a + v3((0.01 * sw * math.sin(u * 3), 0.012 * u, -L * u)) + kn_out * (0.02 * u + 0.03 * u * u)
            h2, ok2 = ray_hit(outer, [q + kn_out * 0.25], [-kn_out], tmax=0.5)
            if ok2[0] and float((h2[0] - q) @ kn_out) > 0:
                q = h2[0] + kn_out * 0.004
            pts.append(q)
        ends.append(pts)
        fd.add(Lock(pts, [0.034, 0.033, 0.031, 0.03, 0.03, 0.03], [0.008] * 6, [kn_out] * 6, k=0.006, disp=wrinkle, disp_amp=0.003), 0.006)
        tip = pts[-1]
        d = norm(pts[-1] - pts[-2])
        fd.add(Lock([tip, tip + d * 0.05], [0.032, 0.034], [0.006, 0.005], [kn_out] * 2, k=0.004, disp=fringe, disp_amp=0.004), 0.004, 5)
    # the baldric
    def bald(P):
        return np.maximum(strap_d(P, BALDRIC) - F(BALDRIC_W), np.maximum(np.abs(P[:, 0]) - F(0.32), F(0.84) - P[:, 2]))
    blo, bhi = (-0.36, -0.32, 0.8), (0.36, 0.34, 1.58)
    fd.add(Inter(layer(base, baldric_off, 0.01, blo, bhi), Func(bald, blo, bhi), 0.003), 0.003)
    # its gold edges (only the baldric's: the sash round his waist stays crimson)
    def edges(P):
        d = strap_d(P, BALDRIC)
        return np.maximum(np.maximum(F(BALDRIC_W - 0.009) - d, d - F(BALDRIC_W + 0.004)), F(0.045) - np.abs(P[:, 2] - F(WAIST_Z)))
    fd.paint(Func(edges, blo, bhi), 5)
    return fd


# ======================================================================================= boots
BOOT_TOP = 0.42


def boot_base(side):
    b = Field("BootBase" + side)
    for p, k in shin_prims(side):
        b.add(p, k)
    foot(b, side)
    return b


def boots_field():
    """Tall boots of buff leather (label 0) to the knee, their wide bucket tops turned down round the knee in a flaring
    cuff, a rolled edge; thick soles and a heel (5: darker leather)."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        kn, an = J["knee_" + side], J["ankle_" + side]
        bb = boot_base(side)
        crease = lambda P: (F(0.0028) * np.sin(P[:, 2] * F(80) + F(0.6) * NOISE(P * F(5))) * smoothstep(0.3, 0.14, P[:, 2])
                            + F(0.0012) * NOISE(P * F(26)))
        lo, hi = an - v3((0.2, 0.35, 0.2)), an + v3((0.2, 0.25, 0.5))
        fd.add(Inter(Shell(bb, 0.016, 0.013, pad=0.06, disp=crease, disp_amp=0.004), Func(lambda P: P[:, 2] - F(BOOT_TOP), lo, hi), 0.004), 0.0)
        # the bucket cuff: a cone flaring up round the knee from the boot's leg, turned down
        ax = norm(kn - an)
        c0 = an + ax * (0.36 - an[2]) / ax[2]
        c1 = an + ax * (0.545 - an[2]) / ax[2]
        wave = lambda P, sx=sx: F(0.006) * np.sin(np.arctan2(P[:, 1], P[:, 0] - F(sx * 0.16)) * F(5)) * smoothstep(0.42, 0.54, P[:, 2]) \
            + F(0.0015) * NOISE(P * F(20))
        cone = RoundCone(c0, c1, 0.114, 0.156)
        fd.add(Inter(Shell(cone, 0.0, 0.012, pad=0.06, disp=wave, disp_amp=0.007),
                     Func(lambda P, c0=c0, c1=c1: np.maximum(F(c0[2]) - P[:, 2], P[:, 2] - F(c1[2] - 0.012)), lo, hi), 0.004), 0.006)
        fd.add(Torus(c1 + v3((0, 0, -0.016)), 0.154, 0.011, disp=wave, disp_amp=0.007), 0.006)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.078 + v3((0, 0, -0.098)), (0.068, 0.155, 0.014), 0.01, R=Rz), 0.006, 5)
        fd.add(RoundBox(an - fwd * 0.03 + v3((0, 0, -0.09)), (0.052, 0.05, 0.026), 0.01, R=Rz), 0.006, 5)      # the heel
    return fd


# ======================================================================================= straps on the coat
COAT_FACE = COAT_OFF + COAT_T / 2 + 0.004   # the coat's outer face (from its base field; + its soft bumps)


def layer(base, off_fn, t, lo, hi, disp=None, disp_amp=0.0):
    """A layer of thickness t over `base` at a varying offset off_fn(P) (it rides over what it crosses)."""
    def fn(P):
        return np.abs(base.eval(P, margin=0.12) - off_fn(P)) - F(t / 2)
    return Func(fn, lo, hi, disp=disp, disp_amp=disp_amp)


def _over_sash(P):
    return smoothstep(0.035, 0.012, np.abs(P[:, 2] - F(WAIST_Z)) - F(0.036))


def _over_baldric(P):
    return smoothstep(0.03, 0.008, strap_d(P, BALDRIC) - F(BALDRIC_W))


def _over_collar(P):
    return smoothstep(0.03, 0.006, collar_region(P))


def baldric_off(P):
    return F(COAT_FACE + 0.006) + np.maximum(F(0.019) * _over_sash(P), F(0.009) * _over_collar(P))


def bandolier_off(P):
    return F(COAT_FACE + 0.0055) + np.maximum(np.maximum(F(0.016) * _over_baldric(P), F(0.03) * _over_sash(P)),
                                              F(0.011) * _over_collar(P) + F(0.014) * _over_baldric(P) * _over_collar(P))


def _fgrad(fn, p, h=0.002):
    p = v3(p)
    g = []
    for i in range(3):
        e = np.zeros(3)
        e[i] = h
        vals = fn(np.array([p + e, p - e], F))
        g.append(float(vals[0] - vals[1]) / (2 * h))
    return norm(v3(g))


def strap_line(plane, zs, front=True, extra=0.0):
    """Points along a strap's middle on the coat's front (or back) at heights zs, with the outward normals (None where
    the strap misses the coat)."""
    p0, n = plane
    base = coat_base()
    d = norm(np.cross(n, v3((0, 0, 1))))
    if (d[1] < 0) == front:
        d = -d                                                          # (marching toward +y from the front)
    f = Func(lambda P: base.eval(P, margin=0.12) - F(COAT_FACE + 0.012 + extra), (-0.8, -0.8, 0.5), (0.8, 0.8, 1.7))
    out = []
    for z in zs:
        y0 = -0.8 if front else 0.8
        x = p0[0] - (n[1] * (y0 - p0[1]) + n[2] * (z - p0[2])) / n[0]
        o = v3((x, y0, z))
        h, ok = ray_hit(f, [o], [d], tmax=1.2, step=0.002)
        out.append((h[0], _fgrad(f, h[0])) if ok[0] else None)
    return out


# ======================================================================================= the bandolier and its apostles
FLASK_R, FLASK_H = 0.019, 0.062
APOSTLE_Z_FRONT = (1.3, 1.24, 1.18, 1.12, 1.06, 1.0, 0.94)     # (the cap tops' heights down the front)
APOSTLE_Z_BACK = (1.3, 1.2, 1.1, 1.0)
CHARGE_I = 4                                                    # the one he pours (front, on his right side)


_SPOTS = []


def _kit_obstacles():
    """Distance to what the apostles and the rapier must clear: the coat's face, the sash and the baldric, the collar,
    the bandolier's strap."""
    base = coat_base()
    sash = sash_field()
    lin = linen_field()
    def strap(P):
        lay = np.abs(base.eval(P, margin=0.12) - bandolier_off(P)) - F(0.0045)
        return np.maximum(lay, np.maximum(strap_d(P, BANDOLIER) - F(BANDOLIER_W), np.maximum(np.abs(P[:, 0]) - F(0.33), F(0.88) - P[:, 2])))
    def fn(P):
        P = np.asarray(P, F)
        d = base.eval(P, margin=0.12) - F(COAT_FACE)
        return np.minimum(np.minimum(d, sash.eval(P)), np.minimum(lin.eval(P), strap(P)))
    return fn


def _flask_samples(cap, hz):
    side = norm(np.cross(v3((0, 0, 1)), hz))
    pts = [cap + v3((0, 0, 0.012)) - hz * 0.004]
    for zz in (0.0, 0.012, 0.03, 0.048, FLASK_H):
        for a in np.linspace(0, 2 * math.pi, 10, endpoint=False):
            pts.append(cap + v3((0, 0, -zz)) + (hz * math.cos(a) + side * math.sin(a)) * (FLASK_R + 0.002))
    return np.array(pts, F)


def apostle_spots():
    """[(cap_top, strap_point, outward)]: each flask hangs on its cord from the strap, resting against the coat (pushed
    out until it clears whatever it hangs over)."""
    if _SPOTS:
        return list(_SPOTS)
    obst = _kit_obstacles()
    spots = []
    for front, zs in ((True, APOSTLE_Z_FRONT), (False, APOSTLE_Z_BACK)):
        line = strap_line(BANDOLIER, [z + 0.05 for z in zs], front=front, extra=-0.006)
        for hit, z in zip(line, zs):
            if hit is None:
                continue
            p, nrm = hit
            cap = p + v3((0, 0, -0.05))
            hz = norm(v3((nrm[0], nrm[1], 0.0)))
            cap = cap + hz * (FLASK_R - 0.004)
            for it in range(30):
                if float(obst(_flask_samples(cap, hz)).min()) > 0.002:
                    break
                cap = cap + hz * 0.003
            spots.append((cap, p, hz))
    _SPOTS.extend(spots)
    return spots


def _apostle(fd, cap, strap_pt, hz, cord=True):
    ax = v3((0, 0, -1))
    fd.add(RoundCone(cap + ax * 0.016, cap + ax * FLASK_H, FLASK_R, FLASK_R * 0.92), 0.0, 13)              # black-painted wood
    fd.add(Cylinder(cap + ax * 0.008, FLASK_R + 0.0015, 0.017, rr=0.004), 0.003, 5)                     # the brass cap
    fd.add(Sphere(cap + v3((0, 0, 0.004)), 0.0065), 0.002, 5)
    fd.add(Torus(cap + ax * (FLASK_H - 0.008), FLASK_R * 0.94, 0.0025), 0.002, 5)                        # a brass ring at its foot
    if cord:
        mid = lerp(cap, strap_pt, 0.5) + hz * 0.006
        fd.add(Chain([cap + v3((0, 0, 0.008)), mid, strap_pt], [0.0032, 0.0032, 0.0032], k=0.002), 0.002, 8)


def bandolier_end():
    line = strap_line(BANDOLIER, [0.93], front=True, extra=-0.006)
    return line[0] if line[0] is not None else (v3((-0.24, -0.1, 0.93)), norm(v3((-0.7, -0.7, 0))))


def bandolier_field():
    """The bandolier over his left shoulder to his right hip (leather, label 9) over the baldric and the sash; the
    apostles hanging from it on cords (8): small wooden flasks painted black (13) with brass caps (5); at its foot a
    priming flask (black, a brass nozzle) and a leather bullet bag."""
    fd = Field("Bandolier")
    base = coat_base()
    lo, hi = (-0.36, -0.32, 0.84), (0.36, 0.34, 1.58)
    def strap(P):
        return np.maximum(strap_d(P, BANDOLIER) - F(BANDOLIER_W), np.maximum(np.abs(P[:, 0]) - F(0.33), F(0.88) - P[:, 2]))
    fd.add(Inter(layer(base, bandolier_off, 0.009, lo, hi), Func(strap, lo, hi), 0.003), 0.0, 9)
    for i, (cap, sp, hz) in enumerate(apostle_spots()):
        if i == CHARGE_I:
            fd.add(Chain([sp, sp + v3((0, 0, -0.02)) + hz * 0.004], [0.0032, 0.0032], k=0.002), 0.002, 8)      # (its cord, empty)
            continue
        _apostle(fd, cap, sp, hz)
    # the priming flask and the bullet bag at its foot
    p, nrm = bandolier_end()
    hz = norm(v3((nrm[0], nrm[1], 0.0)))
    side = norm(np.cross(v3((0, 0, 1)), hz))
    pf, bg = foot_kit()
    fd.add(Ellipsoid(pf, (0.036, 0.022, 0.05), R=rot_from_axes(z_axis=(0, 0, 1), y_axis=hz)), 0.0, 13)
    fd.add(RoundCone(pf + v3((0, 0, 0.04)), pf + v3((0, 0, 0.075)), 0.009, 0.005), 0.004, 5)
    fd.add(Chain([pf + v3((0, 0, 0.07)), p + side * 0.03], [0.003, 0.003], k=0.002), 0.002, 8)
    fd.add(Ellipsoid(bg, (0.038, 0.026, 0.05), R=rot_from_axes(z_axis=(0, 0, 1), y_axis=hz), disp=lambda P: F(0.002) * NOISE(P * F(40)), disp_amp=0.002), 0.0, 9)
    fd.add(Ellipsoid(bg + v3((0, 0, 0.05)), (0.022, 0.016, 0.016), R=rot_from_axes(z_axis=(0, 0, 1), y_axis=hz)), 0.008, 9)
    fd.add(Chain([bg + v3((0, 0, 0.06)), p - side * 0.02], [0.004, 0.004], k=0.002), 0.002, 9)
    return fd


_FOOT = []


def foot_kit():
    """The priming flask's and the bullet bag's middles, hanging from the bandolier's foot clear of the skirts."""
    if _FOOT:
        return _FOOT[0]
    p, nrm = bandolier_end()
    hz = norm(v3((nrm[0], nrm[1], 0.0)))
    side = norm(np.cross(v3((0, 0, 1)), hz))
    base = coat_base()
    out = []
    for c, r in ((p + v3((0, 0, -0.085)) + side * 0.03, (0.036, 0.022, 0.05)), (p + v3((0, 0, -0.09)) - side * 0.035, (0.038, 0.026, 0.05))):
        for it in range(40):
            smp = np.array([c + (side * (r[0] * math.cos(a)) + hz * (r[1] * math.sin(a))) * math.cos(b) + v3((0, 0, r[2] * math.sin(b)))
                            for a in np.linspace(0, 2 * math.pi, 10, endpoint=False) for b in (-1.2, -0.6, 0.0, 0.6, 1.2)], F)
            if float((base.eval(smp, margin=0.12) - F(COAT_FACE)).min()) > 0.003:
                break
            c = c + hz * 0.004
        out.append(c)
    _FOOT.append(tuple(out))
    return _FOOT[0]


def charge_spot():
    return apostle_spots()[CHARGE_I]


def charge_field():
    """The apostle he pours: on its own bone (it rides in his right hand to the muzzle and back)."""
    fd = Field("Charge")
    cap, sp, hz = charge_spot()
    _apostle(fd, cap, cap + v3((0, 0, 0.022)) + hz * 0.002, hz, cord=True)
    return fd


# ======================================================================================= the rapier
RAP_D = norm(v3((0.14, 0.66, -0.74)))      # down along the scabbard, trailing back
RAP_L = 0.78
RAP_W = norm(np.cross(RAP_D, v3((1, 0, 0))))   # the blade's flat (across)
CUP_R = 0.048
_RAP = []


def rapier_throat():
    """The scabbard's throat at his left hip, a little forward: out from the coat until the cup hilt and the scabbard
    clear it, the sash and the baldric."""
    if _RAP:
        return _RAP[0]
    obst = _kit_obstacles()
    T = v3((0.24, -0.06, 0.86))
    X = np.cross(RAP_D, RAP_W)
    C = lambda T: T - RAP_D * 0.05
    def samples(T):
        pts = [C(T) + (RAP_W * math.cos(a) + X * math.sin(a)) * (CUP_R + 0.004) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
        pts += [T + RAP_D * (RAP_L * u) + X * sg * 0.02 for u in (0.0, 0.1, 0.25, 0.4, 0.6) for sg in (-1, 1)]
        pts += [C(T) - RAP_D * 0.128 + d * 0.025 for d in (RAP_W, -RAP_W, X, -X)]
        return np.array(pts, F)
    out = norm(v3((1.0, -0.15, 0.0)))
    for it in range(60):
        if float(obst(samples(T)).min()) > 0.003:
            break
        T = T + out * 0.004
    _RAP.append(T)
    return T


def rapier_field():
    """A cup-hilted rapier at his left hip: a steel cup (label 7), long straight quillons and a knuckle bow, a grip of
    dark leather bound with brass wire (5), a steel pommel; the scabbard of black leather (13) with a steel locket and
    chape."""
    fd = Field("Rapier")
    T, D, W = rapier_throat(), RAP_D, RAP_W
    X = np.cross(D, W)
    tip = T + D * RAP_L
    sc = [T + D * (RAP_L * u) for u in (0.0, 0.35, 0.7, 1.0)]
    R = lambda c: rot_from_axes(z_axis=D, x_axis=W)
    fd.add(Lock(sc, [0.019, 0.017, 0.015, 0.009], [0.012, 0.011, 0.01, 0.007], [X] * 4, k=0.004), 0.0, 13)
    fd.add(Ellipsoid(T + D * 0.03, (0.022, 0.015, 0.032), R=R(0)), 0.004, 7)                          # the locket
    fd.add(Ellipsoid(tip - D * 0.03, (0.013, 0.01, 0.04), R=R(0)), 0.004, 7)                          # the chape
    C = T - D * 0.05
    cup = Inter(Shell(Sphere(C, CUP_R), 0.0, 0.006), Plane(C + D * 0.004, -D), 0.002)
    fd.add(cup, 0.004, 7)
    fd.add(Torus(C + D * 0.004, CUP_R - 0.002, 0.0045, R=rot_from_axes(z_axis=D)), 0.003, 7)
    fd.add(Chain([C - W * 0.13, C + W * 0.13], [0.0055, 0.0055], k=0.002), 0.003, 7)                 # the quillons
    for sw in (-1, 1):
        fd.add(Sphere(C + W * (sw * 0.132), 0.01), 0.003, 7)
    g0, g1 = C - D * 0.008, C - D * 0.11
    fd.add(RoundCone(g0, g1, 0.013, 0.012), 0.004, 5)
    for k in range(6):
        fd.add(Torus(lerp(g0, g1, (k + 0.5) / 6), 0.0128, 0.002, R=rot_from_axes(z_axis=D)), 0.0015, 5)
    pm = C - D * 0.128
    fd.add(Sphere(pm, 0.021), 0.004, 7)
    fd.add(RoundCone(pm - D * 0.016, pm - D * 0.032, 0.008, 0.004), 0.004, 7)
    bow = [C - W * 0.05 + X * 0.03, C - D * 0.03 - W * 0.02 + X * 0.07, C - D * 0.075 + X * 0.07, C - D * 0.115 + X * 0.03]
    fd.add(Chain(bow, [0.005] * 4, k=0.003), 0.003, 7)
    return fd


# ======================================================================================= the musket
# Musket coordinates: u along the barrel (from the grip, forward), v to the gun's right (the lock side), h up; the
# grip (u = 0) is where his right fist holds the wrist of the stock, behind the lock.
BUTT_U, BUTT_NOTCH = -0.38, 0.03           # the butt's heel/toe, and how deep its fishtail notch is
BREECH_U, MUZZLE_U = 0.14, 1.2              # (1.58 m from butt to muzzle: stood on its butt it reaches his chin)
STOCK_END = 1.08
BAR_H = 0.045                              # the barrel's axis above the grip
PIVOT = (0.075, 0.012)                     # the serpentine's pivot (u, h) on the lock plate
PAN = (0.158, 0.04)                        # the priming pan
RAM_U = (0.78, 1.13)                       # the ramrod, stowed under the barrel (short enough to draw at arm's length)
RAM_H = -0.006
SERP_V = 0.011                             # (the serpentine's plane, just out from the lock plate: v = w + SERP_V)
SERP_DIP = 0.0                             # (set by the clips)


def musket_frame():
    """Rest pose: the musket in his right fist: the barrel along the fist's thumb axis A, the gun's top U along the
    palm's normal, S = A x U its right (lock) side."""
    wr, f, n, t = hand_frame("R")
    G = fist_center("R")
    A = norm(t)
    U = norm(n - A * (n @ A))
    S = np.cross(A, U)
    return G, A, U, S


def mpt(u, v=0.0, h=0.0):
    G, A, U, S = musket_frame()
    return G + A * u + S * v + U * h


def m_local(P):
    G, A, U, S = musket_frame()
    q = P - G.astype(F)
    return q @ A.astype(F), q @ S.astype(F), q @ U.astype(F)


def m_bounds(u0, u1, r=0.15):
    pts = [mpt(u, v, h) for u in (u0, u1) for v in (-r, r) for h in (-r, r)]
    return np.min(pts, 0), np.max(pts, 0)


def stock_profile(u):
    """(h_bot, h_top, half width) of the stock's cross-section at u (arrays)."""
    k = np.clip((F(-0.1) - u) / F(-0.1 - BUTT_U), 0, 1)                # 0 at the wrist .. 1 at the butt's end
    wrist = np.exp(-((u + F(0.03)) / F(0.06)) ** 2)
    lock = smoothstep(0.02, 0.07, u) * smoothstep(0.24, 0.16, u)
    fore = smoothstep(0.14, 0.3, u)
    hb = F(-0.03) - F(0.062) * k - F(0.032) * k ** 4 + F(0.006) * wrist + F(0.006) * lock + F(0.022) * fore * np.clip((u - F(0.3)) / F(0.8), 0, 1)
    hb = hb + F(0.012) * fore
    ht = F(0.031) - F(0.022) * k * k + F(0.016) * lock + F(0.014) * fore
    ht = np.minimum(ht, F(BAR_H))
    w = F(0.02) + F(0.009) * k - F(0.003) * wrist + F(0.003) * lock - F(0.004) * fore * np.clip((u - F(0.3)) / F(0.8), 0, 1)
    return hb, ht, w


def _stock_sd(P):
    u, v, h = m_local(P)
    hb, ht, w = stock_profile(u)
    hc, hh = (ht + hb) / F(2), (ht - hb) / F(2)
    hm_end = F(-0.055)
    umin = F(BUTT_U) + F(BUTT_NOTCH) * np.clip(F(1) - ((h - hm_end) / F(0.06)) ** 2, 0, 1)
    rr = F(0.008)
    qx = np.abs(v) - w + rr
    qy = np.abs(h - hc) - hh + rr
    qz = np.maximum(umin - u, u - F(STOCK_END)) + rr
    q = np.stack([qx, qy, qz], 1)
    d = np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - rr
    # the ramrod's groove under the fore-stock
    g = np.maximum(np.sqrt(v * v + (h - F(RAM_H)) ** 2) - F(0.0095), np.maximum(F(RAM_U[0] - 0.03) - u, u - F(STOCK_END + 0.01)))
    return np.maximum(d, -g)


def barrel_r(u):
    taper = F(0.0215) - F(0.0045) * np.clip((u - F(0.3)) / F(0.85), 0, 1)
    swell = F(0.0025) * smoothstep(1.19, 1.215, u)
    return taper + swell + F(0.002) * smoothstep(0.32, 0.26, u)


def _barrel_sd(P):
    u, v, h = m_local(P)
    rad = np.sqrt(v * v + (h - F(BAR_H)) ** 2) - barrel_r(u)
    ax = np.maximum(F(BREECH_U) - u, u - F(MUZZLE_U))
    q0, q1 = np.maximum(rad, 0), np.maximum(ax, 0)
    d = np.sqrt(q0 * q0 + q1 * q1) + np.minimum(np.maximum(rad, ax), 0)
    bore = np.maximum(np.sqrt(v * v + (h - F(BAR_H)) ** 2) - F(0.0088), F(MUZZLE_U - 0.07) - u)
    return np.maximum(d, -bore)


def _band_sd(u0, half):
    def fn(P):
        u, v, h = m_local(P)
        hb, ht, w = stock_profile(np.full(len(u), F(u0)))
        top = F(BAR_H) + barrel_r(np.full(len(u), F(u0)))
        wv = np.maximum(w, barrel_r(np.full(len(u), F(u0)))) + F(0.003)
        hc, hh = (top + hb) / F(2), (top - hb) / F(2) + F(0.003)
        rr = F(0.006)
        q = np.stack([np.abs(v) - wv + rr, np.abs(h - hc) - hh + rr, np.abs(u - F(u0)) - F(half) + rr], 1)
        return np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - rr
    return fn


def musket_field():
    """Walnut (label 0) stock with a fishtail butt, brass (5) butt plate, bands, nose cap, trigger guard and pan, forged
    iron (6) barrel, lock plate, tang, trigger and sights; the spare match coiled round the fore-stock (8)."""
    fd = Field("Musket")
    lo, hi = m_bounds(BUTT_U - 0.02, MUZZLE_U + 0.02, 0.075)
    grain = lambda P: F(0.0006) * NOISE(P * F(90))
    fd.add(Func(_stock_sd, lo, hi, disp=grain, disp_amp=0.001), 0.0)
    fd.add(Func(_barrel_sd, lo, hi), 0.002, 6)
    for u0 in (0.5, 0.82):
        fd.add(Func(_band_sd(u0, 0.009), *m_bounds(u0 - 0.03, u0 + 0.03)), 0.002, 5)
    fd.add(Func(_band_sd(STOCK_END - 0.008, 0.009), *m_bounds(STOCK_END - 0.04, STOCK_END + 0.02)), 0.002, 5)
    # the butt plate (brass, over the fishtail end)
    def plate(P):
        u, v, h = m_local(P)
        umin = F(BUTT_U) + F(BUTT_NOTCH) * np.clip(F(1) - ((h - F(-0.055)) / F(0.06)) ** 2, 0, 1)
        return u - (umin + F(0.012))
    fd.paint(Func(plate, *m_bounds(BUTT_U - 0.02, BUTT_U + 0.06)), 5)
    # the trigger guard (brass) and the trigger (iron)
    G, A, U, S = musket_frame()
    mp = lambda u, h, v=0.0: mpt(u, v, h)
    guard = [mp(-0.035, -0.027), mp(-0.025, -0.052), mp(0.01, -0.064), mp(0.05, -0.054), mp(0.068, -0.028)]
    fd.add(Chain(guard, [0.0045] * 5, k=0.003), 0.003, 5)
    fd.add(Chain([mp(0.022, -0.026), mp(0.016, -0.042), mp(0.006, -0.052)], [0.0042, 0.0038, 0.0032], k=0.002), 0.002, 6)
    # the lock plate (iron) on the right side, the serpentine's pivot boss, the pan (brass) and its open cover
    hb, ht, w = (float(x[0]) for x in stock_profile(np.array([0.1], F)))
    fd.add(RoundBox(mp(0.105, 0.012, w + 0.001), (0.07, 0.0025, 0.026), 0.002, R=np.stack([A, S, U], axis=1) @ np.eye(3)[[0, 1, 2]]), 0.003, 6)
    fd.add(Cylinder(mp(PIVOT[0], PIVOT[1], w + 0.006), 0.009, 0.008, rr=0.002, R=rot_from_axes(z_axis=S, y_axis=U)), 0.002, 6)
    pc = mp(PAN[0], PAN[1] - 0.006, 0.03)
    fd.add(Cylinder(pc, 0.0115, 0.009, rr=0.002, R=rot_from_axes(z_axis=U, y_axis=A)), 0.003, 5)
    fd.sub(Sphere(pc + U * 0.009, 0.008), 0.002)
    fd.add(RoundBox(mp(PAN[0] - 0.012, PAN[1] + 0.012, 0.034), (0.003, 0.012, 0.01), 0.002, R=np.stack([A, S, U], axis=1)), 0.002, 5)
    # the tang over the wrist, the sights
    fd.add(Chain([mp(BREECH_U, BAR_H - 0.004), mp(0.02, 0.034), mp(-0.07, 0.03)], [0.0045, 0.004, 0.0035], k=0.003), 0.002, 6)
    fd.add(RoundBox(mp(MUZZLE_U - 0.03, BAR_H + 0.021), (0.008, 0.0015, 0.005), 0.0012, R=np.stack([A, S, U], axis=1)), 0.002, 6)
    fd.add(RoundBox(mp(BREECH_U + 0.03, BAR_H + 0.024), (0.004, 0.006, 0.005), 0.0015, R=np.stack([A, S, U], axis=1)), 0.002, 6)
    # the ramrod's pipes (brass) under the fore-stock
    for u0 in (0.86, 1.02):
        fd.add(Torus(mp(u0, RAM_H), 0.0105, 0.0032, R=rot_from_axes(z_axis=A, y_axis=U)), 0.002, 5)
    # spare match coiled round the fore-stock ahead of the lock
    for k in range(3):
        u0 = 0.225 + 0.02 * k
        hb0, ht0, w0 = (float(x[0]) for x in stock_profile(np.array([u0], F)))
        ring = []
        for j in range(17):
            a = 2 * math.pi * j / 16
            hh = (BAR_H + 0.024 + hb0) / 2 + math.sin(a) * ((BAR_H + 0.024 - hb0) / 2 + 0.004)
            vv = math.cos(a) * (max(w0, 0.022) + 0.005)
            ring.append(mp(u0 + 0.004 * math.sin(a * 0.5), hh, vv))
        fd.add(Chain(ring, [0.0045] * len(ring), k=0.002), 0.002, 8)
    return fd


def serp_pts(dip=0.0):
    """The serpentine's S-arm and jaws (u, h), rotated by `dip` (radians, + = toward the pan) about its pivot."""
    pts = [(0.075, 0.012), (0.054, 0.034), (0.049, 0.062), (0.062, 0.086), (0.088, 0.096)]
    c, s = math.cos(-dip), math.sin(-dip)
    return [(PIVOT[0] + (u - PIVOT[0]) * c - (h - PIVOT[1]) * s, PIVOT[1] + (u - PIVOT[0]) * s + (h - PIVOT[1]) * c) for u, h in pts]


MATCH_TIP = (0.117, 0.09)                  # the match's glowing end (cocked)


def serpentine_field():
    """The serpentine (forged iron, label 6): an S-shaped arm from its pivot on the lock plate, jaws at its top with a
    thumbscrew; the match clamped in the jaws (8), its end charred black (12) round the glowing tip (the Ember)."""
    fd = Field("Serpentine")
    G, A, U, S = musket_frame()
    hb, ht, w = (float(x[0]) for x in stock_profile(np.array([0.1], F)))
    v0 = w + SERP_V
    sp = [mpt(u, v0, h) for u, h in serp_pts()]
    fd.add(Chain(sp, [0.0062, 0.0055, 0.005, 0.0052, 0.006], k=0.003), 0.0, 6)
    fd.add(Cylinder(sp[0], 0.008, 0.012, rr=0.002, R=rot_from_axes(z_axis=S, y_axis=U)), 0.003, 6)
    jaw = sp[-1]
    for sv in (-1, 1):
        fd.add(RoundBox(jaw + S * (sv * 0.006), (0.012, 0.0022, 0.009), 0.0015, R=np.stack([A, S, U], axis=1)), 0.002, 6)
    fd.add(RoundCone(jaw + U * 0.008, jaw + U * 0.022, 0.003, 0.003), 0.002, 6)                      # the thumbscrew
    fd.add(Sphere(jaw + U * 0.024, 0.0055), 0.002, 6)
    # the match in the jaws: from behind them to the charred end
    tip = mpt(MATCH_TIP[0], v0, MATCH_TIP[1])
    back = jaw - A * 0.014 + U * 0.002
    fd.add(Chain([back, jaw, tip - A * 0.006], [0.0042, 0.0042, 0.004], k=0.002), 0.002, 8)
    fd.paint(Sphere(tip, 0.011), 12)
    return fd


def match_tail_pts():
    """The match's tail from the serpentine's jaws back, down past the lock plate and forward to the coils."""
    G, A, U, S = musket_frame()
    hb, ht, w = (float(x[0]) for x in stock_profile(np.array([0.1], F)))
    v0 = w + SERP_V
    jaw = serp_pts()[-1]
    pts = [(jaw[0] - 0.014, jaw[1] + 0.002, v0), (0.06, 0.084, v0 + 0.006), (0.056, 0.05, v0 + 0.012), (0.066, 0.012, v0 + 0.014),
           (0.1, -0.012, v0 + 0.01), (0.15, -0.022, v0 + 0.004), (0.2, -0.02, 0.026), (0.225, -0.012, 0.03)]
    return [mpt(u, v, h) for u, h, v in pts]


def match_field():
    fd = Field("Match")
    pts = match_tail_pts()
    fd.add(Chain(pts, [0.0042] * len(pts), k=0.003), 0.0, 8)
    return fd


def ember_field():
    """The match's glowing end (its own emissive mesh, on the serpentine's bone)."""
    fd = Field("Ember")
    G, A, U, S = musket_frame()
    hb, ht, w = (float(x[0]) for x in stock_profile(np.array([0.1], F)))
    v0 = w + SERP_V
    tip = mpt(MATCH_TIP[0], v0, MATCH_TIP[1])
    fd.add(RoundCone(tip - A * 0.006, tip + A * 0.004, 0.0062, 0.0058), 0.0)
    return fd


def ramrod_field():
    """The ramrod (ash, label 14, its grain along it) with a brass tip (5), stowed under the barrel."""
    fd = Field("Ramrod")
    a, b = mpt(RAM_U[0], 0.0, RAM_H), mpt(RAM_U[1], 0.0, RAM_H)
    G, A, U, S = musket_frame()
    fd.add(RoundCone(a, b - A * 0.02, 0.0062, 0.0068), 0.0, 14)
    fd.add(RoundCone(b - A * 0.024, b, 0.0082, 0.0085), 0.002, 5)
    return fd


def ram_ends():
    return mpt(RAM_U[0], 0.0, RAM_H), mpt(RAM_U[1], 0.0, RAM_H)


# ======================================================================================= the forked rest
REST_FOOT, REST_CROTCH, REST_PRONG = -1.18, 0.28, 0.068     # along the staff from his left fist's grip (rest pose)


def rest_frame():
    """Rest pose: the rest's staff through his left fist along the thumb axis A (the fork ahead), the fork's prongs
    spread along W (the palm's normal)."""
    wr, f, n, t = hand_frame("L")
    K = fist_center("L")
    A = norm(t)
    W = norm(n - A * (n @ A))
    return K, A, W, np.cross(A, W)


def rpt(s, w=0.0, x=0.0):
    K, A, W, X = rest_frame()
    return K + A * s + W * w + X * x


def rest_field():
    """The musket rest: a staff of ash (label 14), an iron (6) U-fork bound to its top by a socket, an iron spike at its
    foot."""
    fd = Field("Rest")
    K, A, W, X = rest_frame()
    grain = lambda P: F(0.0012) * NOISE(P * np.array([50, 50, 50], F))
    fd.add(RoundCone(rpt(REST_FOOT + 0.07), rpt(REST_CROTCH - 0.03), 0.0165, 0.0145, disp=grain, disp_amp=0.0015), 0.0, 14)
    fd.add(RoundCone(rpt(REST_FOOT + 0.085), rpt(REST_FOOT), 0.013, 0.002), 0.003, 6)
    fd.add(Cylinder(rpt(REST_FOOT + 0.085), 0.018, 0.03, rr=0.004, R=rot_from_axes(z_axis=A)), 0.003, 6)
    fd.add(Cylinder(rpt(REST_CROTCH - 0.045), 0.0185, 0.05, rr=0.004, R=rot_from_axes(z_axis=A)), 0.003, 6)
    # the U: a half ring under the barrel's line and two prongs rising from it, their tips flared
    c = rpt(REST_CROTCH + 0.034)
    ring = []
    for j in range(13):
        a = math.pi * j / 12
        ring.append(c + W * (math.cos(a) * 0.034) - A * (math.sin(a) * 0.034))
    fd.add(Chain(ring, [0.0075] * len(ring), k=0.003), 0.004, 6)
    for sw in (-1, 1):
        p0 = c + W * (sw * 0.034)
        p1 = p0 + A * (REST_PRONG - 0.034) + W * (sw * 0.012)
        fd.add(RoundCone(p0, p1, 0.0075, 0.006), 0.003, 6)
        fd.add(Sphere(p1, 0.0075), 0.002, 6)
    fd.add(RoundCone(rpt(REST_CROTCH - 0.02), c - A * 0.034, 0.012, 0.0095), 0.004, 6)
    return fd


def rest_crotch():
    """Where the barrel lies in the fork (rest pose)."""
    return rpt(REST_CROTCH)


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.252, 1.606)), 0.045, 0.5)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.105, -0.14, 1.63)), 0.05, 0.4), (hp((sx * 0.17, 0.035, 1.66)), 0.05, 0.45)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.138 + t * o - n * 0.012, 0.03, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "musketeer"
ROOT_NAME = "MusketeerHQ"
TEX_PREFIX = "musk"
MAT_NAME = "MusketeerMat"
MESH_NAME = "Musketeer"
BASE_MODULE = "musketeer_base"
ANIM_MODULE = "anim_musketeer"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Hat", "Brooch", "Plume", "Coat", "Linen", "Cuffs", "Crimson", "Sash", "Boots",
         "Bandolier", "Charge", "Rapier", "Musket", "Serpentine", "Match", "Ember", "Ramrod", "Rest"]
REGION_PARTS = ("Skin", "Hat", "Plume", "Coat", "Crimson", "Sash", "Boots", "Bandolier", "Charge", "Rapier", "Musket",
                "Serpentine", "Match", "Ramrod", "Rest")
CRIMSON = (0.55, 0.08, 0.08)               # the army's colours (the brief): deep crimson, gold-ochre, buff, linen, black felt
GOLD = (0.85, 0.62, 0.2)
BUFF = (0.72, 0.53, 0.3)
BOOT_BUFF = (0.5, 0.34, 0.18)               # (his boots a darker, worn buff: they part from the coat)
LINEN = (0.95, 0.93, 0.87)
DARK_HAIR = {"name": "HQ_MuskHair", "base": (0.1, 0.075, 0.06), "hi": (0.3, 0.23, 0.18), "low": (0.04, 0.03, 0.025),
             "streak": (0.06, 0.045, 0.035), "tint": (0.18, 0.12, 0.08)}
ARMS = {"name": "HQ_Matchlock"}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_MuskSkin", "base": (0.78, 0.54, 0.4), "ruddy": (0.8, 0.45, 0.35), "lips": (0.62, 0.36, 0.31),
                      "brow": ((0.06, 0.045, 0.04), (0.14, 0.1, 0.08)),
                      "extra": ((LASH, (0.06, 0.04, 0.035), 0.5), (STUBBLE, (0.4, 0.29, 0.24), 0.55, 0.35))}),
    "Hair": ("hair", DARK_HAIR),
    "Beard": ("hair", DARK_HAIR),
    "Hat": ("wool", {"name": "HQ_Felt", "base": (0.075, 0.068, 0.072), "border": GOLD, "stripe": GOLD}),
    "Brooch": ("gold", {"name": "HQ_MuskGold"}),
    "Plume": ("plume", {"name": "HQ_Plume", "col": CRIMSON, "col2": LINEN}),
    "Coat": ("leather_dyed", {"name": "HQ_BuffCoat", "base": BUFF, "dyed": GOLD}),
    "Linen": ("linen", {"name": "HQ_MuskLinen", "base": LINEN}),
    "Cuffs": ("linen", {"name": "HQ_MuskLinen", "base": LINEN}),
    "Crimson": ("wool", {"name": "HQ_MuskCrimson", "base": CRIMSON, "border": GOLD, "stripe": GOLD}),
    "Sash": ("wool", {"name": "HQ_MuskSash", "base": CRIMSON, "border": GOLD, "stripe": GOLD}),
    "Boots": ("leather_dyed", {"name": "HQ_BuffBoots", "base": BOOT_BUFF, "dyed": (0.3, 0.19, 0.11)}),
    "Bandolier": ("matchlock", ARMS),
    "Charge": ("matchlock", ARMS),
    "Rapier": ("matchlock", ARMS),
    "Musket": ("matchlock", ARMS),
    "Serpentine": ("matchlock", ARMS),
    "Match": ("matchlock", ARMS),
    "Ember": ("glow_ball", {"name": "HQ_Ember", "col": (1.0, 0.36, 0.08), "strength": 3.0}),
    "Ramrod": ("matchlock", ARMS),
    "Rest": ("matchlock", ARMS),
}
GLOW = {"Ember": ((1.0, 0.34, 0.08), 1.25, 0.5)}
LOW_TARGETS = {"Skin": 5200, "Teeth": 60, "Hair": 1500, "Beard": 520, "Hat": 1700, "Brooch": 160, "Plume": 2400, "Coat": 3200,
               "Linen": 760, "Cuffs": 220, "Crimson": 1500, "Sash": 1300, "Boots": 1300, "Bandolier": 1900, "Charge": 90, "Rapier": 700,
               "Musket": 1700, "Serpentine": 220, "Match": 160, "Ember": 40, "Ramrod": 110, "Rest": 520}
AO_EXCLUDE = ["Musket", "Serpentine", "Match", "Ember", "Ramrod", "Rest", "Charge", "Brooch", "Rapier"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.77, 0.93, 1.1, 1.48)


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.95), (0, 0.045, 1.16)),
        "chest": ((0, 0.045, 1.16), (0, 0.065, 1.41)),
        "neck": ((0, 0.065, 1.41), hp((0, 0.02, 1.56))),
        "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.41,
    }


def prop_bones():
    """The musket, its ramrod, the rest and the charge have no parent (posed in the world, "world" aims); the
    serpentine is the musket's."""
    G, A, U, S = musket_frame()
    K, RA, W, X = rest_frame()
    hb, ht, w = (float(x[0]) for x in stock_profile(np.array([0.1], F)))
    r0, r1 = ram_ends()
    cap, sp, hz = charge_spot()
    return [("musket", G, mpt(MUZZLE_U, 0.0, BAR_H), None),
            ("serpentine", mpt(PIVOT[0], w + SERP_V, PIVOT[1]), mpt(PIVOT[0], w + SERP_V, PIVOT[1] + 0.06), "musket"),
            ("ramrod", r0, r1, None),
            ("rest", K, rpt(REST_CROTCH), None),
            ("charge", cap, cap + v3((0, 0, -FLASK_H)), None)]


def _vec(p):
    from mathutils import Vector
    return Vector((float(p[0]), float(p[1]), float(p[2])))


def hair_w(p):
    """The hair under the hat goes with the head; what falls to his shoulders passes to the neck and chest."""
    z1 = hp((0, 0, 1.62))[2]
    if p.z >= z1:
        return {"head": 1.0}
    t = max(0.0, min(1.0, (z1 - p.z) / 0.16))
    if p.y > 0.1 or abs(p.x) > 0.17:
        return {"head": max(0.0, 1.0 - 1.4 * t), "neck": 0.6 * (1.0 - abs(2 * t - 1.0)), "chest": max(0.0, 1.4 * t - 0.4)}
    return {"head": 1.0 - 0.6 * t, "neck": 0.6 * t}


def hair_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, hair_w(v.co))


def match_weights(ob, skin_ob, arm):
    """The match's tail: with the serpentine at the jaws, passing to the musket toward the coils."""
    pts = match_tail_pts()
    jaw, coil = pts[0], pts[-1]
    groups = {}
    for v in ob.data.vertices:
        p = np.array(v.co)
        a = float(np.linalg.norm(p - jaw))
        b = float(np.linalg.norm(p - pts[3]))
        k = max(0.0, min(1.0, a / max(a + b, 1e-6)))
        k = k * k * (3 - 2 * k)
        _blend_add(ob, groups, v.index, {"serpentine": 1.0 - k, "musket": k})


def weight_rules():
    body = TORSO | {"clavicle.R", "clavicle.L"}
    arms = {"upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Beard": ("rigid", "head"), "Hat": ("rigid", "head"),
        "Brooch": ("rigid", "head"), "Plume": ("rigid", "head"),
        "Hair": ("custom", hair_weights),
        "Coat": ("transfer", body | arms | {"thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Linen": ("transfer", body, None),
        "Cuffs": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Crimson": ("transfer", body | arms | {"thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Sash": ("transfer", body | {"thigh.R", "thigh.L"}, {"thigh.R": 0.4, "thigh.L": 0.4}),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Bandolier": ("transfer", body, None),
        "Charge": ("rigid", "charge"), "Rapier": ("rigid", "root"),
        "Musket": ("rigid", "musket"), "Serpentine": ("rigid", "serpentine"), "Ember": ("rigid", "serpentine"),
        "Match": ("custom", match_weights), "Ramrod": ("rigid", "ramrod"), "Rest": ("rigid", "rest"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Musket", "Rest", "Ramrod", "Match"):
        return 0.75
    if part in ("Plume", "Hat"):
        return 1.15
    if part == "Skin" and abs(c.x) > 0.6 and c.z < 1.0:
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0026 if fine else 0.0036),
        ("Beard", beard_field(), 0.0018 if fine else 0.0026),
        ("Hat", hat_field(), 0.0024 if fine else 0.0034),
        ("Brooch", brooch_field(), 0.0012 if fine else 0.0016),
        ("Plume", plume_field(), 0.0024 if fine else 0.0034),
        ("Coat", coat_field(), 0.0026 if fine else 0.0036),
        ("Linen", linen_field(), 0.002 if fine else 0.0028),
        ("Cuffs", cuffs_field(), 0.0018 if fine else 0.0024),
        ("Crimson", crimson_field(), 0.0024 if fine else 0.0034),
        ("Sash", sash_field(), 0.0022 if fine else 0.003),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Bandolier", bandolier_field(), 0.0016 if fine else 0.0022),
        ("Charge", charge_field(), 0.0012 if fine else 0.0016),
        ("Rapier", rapier_field(), 0.0016 if fine else 0.0022),
        ("Musket", musket_field(), 0.0016 if fine else 0.0022),
        ("Serpentine", serpentine_field(), 0.001 if fine else 0.0013),
        ("Match", match_field(), 0.0012 if fine else 0.0016),
        ("Ember", ember_field(), 0.001),
        ("Ramrod", ramrod_field(), 0.0012 if fine else 0.0016),
        ("Rest", rest_field(), 0.0016 if fine else 0.0022),
    ]
