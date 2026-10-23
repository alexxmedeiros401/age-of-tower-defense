"""Dr. Ken Ito, Field Engineer (HQ hero, Modern Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A brilliant, upbeat field engineer of the task force in his thirties: a friendly face with a confident grin (both corners
drawn up into round cheeks, his upper teeth showing), bright dark-brown eyes behind black rectangular glasses (a bolder
browline across their tops), thick black brows lifted high; short black hair cut close at the sides and the back. A
coyote-tan baseball cap worn backwards (six panels, a button on top, the brim over his nape) under a tactical headset: an
olive-drab ear cup over each ear on a black band over the cap, a boom mic from the left cup to the corner of his mouth.
Olive-drab fatigues: the combat shirt (a folded collar, the sleeves rolled up to just below his elbows, a small red unit
patch with a white bar on the left sleeve), the trousers (cargo pockets on the thighs, black knee pads, bloused over
his boots); a black rigger's belt; black boots; black tactical gloves. A coyote-tan engineer's vest zipped up the front
(PALS rows on its sides and back): a radio in a pouch on the left chest (its antenna up past his shoulder), a sleeve of
tools on the right chest (a yellow screwdriver, a pen, a torch), a pouch of two EMP grenades on the right of his belly (he
draws from it), a pouch with a yellow multimeter on the left, a battery pack on his back; a pliers holster on his right hip, a coil of
cable on a carabiner on his left.

On his left forearm a rugged tablet (black, rubber corners, a glowing screen: its own emissive mesh, `Screen`) strapped
on in a gunmetal mount. On his right forearm the concussion gauntlet: a black padded sleeve under gunmetal armour plates
with tan panels, two steel pistons along its back, a power cell on its top with three glowing slits (`Cells`); over his
fist a gunmetal housing carrying the seismic plate in front of his knuckles: a thick plate with a grille and a glowing
emitter ring (`Emitter`) in its face. He slams it into the ground: the plate rides its own bone, `plate` (a child of his
right hand; its tail = the middle of the plate's face, the game's shockwave origin).

The EMP grenade (the Ability): a chunky canister on a short black grip (a gunmetal body, black caps, a steel pin ring) with
a glowing blue band round its middle (`Core`, on the `core` bone: it swells when he arms it). It rides the free bone
`grenade` (its head = the canister's middle); at rest it sits in his right fist, the grip through it along the thumb axis,
the canister out past his thumb. The clips keep it hidden (scale 0) but in the Ability, between drawing it from his vest
and lobbing it.

His body is the Musketeer's (musketeer.py: the long, rangy skeleton, its limbs, hands and feet) with his own head."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
import musketeer as mk
from musketeer import (J, hp, hr, hinv, HS, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S, fist_center,
                       foot, torso_prims, traps, neck_prim, deltoid, upper_arm_prims, forearm_prims, leg_prims, shin_prims,
                       _arm_seg_dist, _fgrad, torso_bones, TORSO_Z, TORSO, CURLS)

SKIN, NAIL, LIP, MOUTH, BROW, LASH, GLOVE = 0, 1, 2, 3, 4, 8, 11
IRIS = ((0.16, 0.09, 0.045), (0.42, 0.27, 0.13))           # warm dark-brown eyes (prep.paint_eyes)

OLIVE = (0.4, 0.42, 0.28)               # the task force's olive drab
TAN = (0.6, 0.5, 0.36)                  # coyote tan (vest, pouches, cap)
TAN_DARK = (0.47, 0.38, 0.26)           # (PALS webbing)
BLACK = (0.07, 0.068, 0.072)
RED = (0.74, 0.1, 0.07)
WHITE = (0.93, 0.92, 0.88)
GUNMETAL = (0.3, 0.31, 0.33)
YELLOW = (0.93, 0.74, 0.14)
BLUE = (0.3, 0.72, 1.0)                 # the gear's glow (emitter, cells, the grenade's core)
SCREEN = (0.36, 0.86, 1.0)

Z = v3((0.0, 0.0, 1.0))


def _seg_dist(P, a, b):
    ab = (b - a).astype(F)
    t = np.clip(((P - a.astype(F)) @ ab) / F(ab @ ab), 0, 1)
    return np.sqrt((((a.astype(F) + t[:, None] * ab) - P) ** 2).sum(1))


def _frame(n, up=Z):
    """Columns (side, up, n): a frame on a surface with normal n, `up` projected into it."""
    n = norm(n)
    u = norm(v3(up) - n * float(v3(up) @ n))
    s = norm(np.cross(u, n))
    return np.stack([s, u, n], 1)


# ======================================================================================= hands (black gloves)
def hand(fd, side, s=HAND_S):
    """A fist in a black tactical glove (the Musketeer's fist, label GLOVE): a padded back, a cuff at the wrist."""
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.061, 0.031, 0.066)) * s, 0.027 * s, R=Rp), 0.027, GLOVE)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.033, 0.028, 0.05)) * s, R=Rp), 0.018, GLOVE)
    curl_ax = norm(np.cross(f, n))
    offs = (0.042, 0.014, -0.014, -0.042)
    lens = (0.98, 1.05, 0.98, 0.82)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.0205 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.053 * ls * s, 0.043 * ls * s, 0.035 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, CURLS[side][j] * (0.9 if i == 3 else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.92)
        fd.add(Chain(pts, rads, k=0.006), 0.011, GLOVE)
        fd.add(Sphere(pts[0] - n * 0.012, 0.016 * s), 0.009, GLOVE)                 # padded knuckles
    tb = wr + f * 0.045 * s + t * 0.05 * s + n * 0.011
    d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
    d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.025 * s, 0.022 * s, 0.019 * s], k=0.008), 0.018, GLOVE)
    fd.add(RoundBox(c - n * 0.03 + f * 0.015, v3((0.05, 0.008, 0.04)) * s, 0.006, R=Rp), 0.008, GLOVE)   # the padded back
    fd.add(Torus(wr - f * 0.005, 0.054, 0.011, R=rot_from_axes(z_axis=f)), 0.01, GLOVE)               # the cuff


# ======================================================================================= head: the grin
def _on_face(fd, pts_xz, lift=0.0):
    """Points on the face's surface (as sculpted so far) in front of design points (x, z): rays from the front."""
    org = [hp((x, -0.45, z)) for x, z in pts_xz]
    h, ok = ray_hit(fd, org, [v3((0, 1, 0))] * len(pts_xz), tmax=0.5, step=0.0008)
    out = []
    for i, (x, z) in enumerate(pts_xz):
        q = h[i] if ok[i] else hp((x, -0.18, z))
        out.append(q - v3((0, 1, 0)) * lift)
    return out


MOUTH_W = 0.06                         # half the grin's width (design)


def mouth_curves(x):
    """The open grin (design units): the upper lip's edge and the lower lip's edge at x (both corners drawn up)."""
    x = np.asarray(x, dtype=np.float64)
    up = 1.557 + 5.2 * x * x
    lo = 1.557 - 0.025 + 12.0 * x * x
    return up, lo


def head(fd):
    """A friendly, open face: a firm young jaw and a rounded chin, cheekbones, round cheeks pushed up by a confident grin
    (both corners drawn up, his upper teeth showing, smile folds and dimples), bright open eyes (the lower lids lifted a
    little by the cheeks, crinkles at their corners), thick black brows lifted high, a straight nose with a soft rounded
    tip; ears (under his headset's cups)."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.05, 1.59), (0.13, 0.126, 0.122)), 0.07, SKIN)                           # a firm young jaw
    fd.add(E((0, -0.13, 1.503), (0.073, 0.063, 0.062)), 0.05, SKIN)                          # a rounded chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.108, -0.118, 1.64), 0.042), 0.05, SKIN)                              # cheekbones
        fd.add(S((sx * 0.116, -0.046, 1.564), 0.043), 0.05, SKIN)                             # jaw corners
        fd.add(S((sx * 0.078, -0.144, 1.606), 0.029), 0.03, SKIN)                             # round cheeks (the grin)
        pts = [hp((sx * 0.15, -0.055, 1.744)), hp((sx * 0.114, -0.128, 1.752)), hp((sx * 0.06, -0.17, 1.75)), hp((0.0, -0.18, 1.748))]
        fd.add(Chain(pts, [hr(0.008), hr(0.014), hr(0.016), hr(0.016)], k=hr(0.02)), hr(0.03), SKIN)   # a soft brow ridge
    # thick black brows, lifted high, lying on the brow (a raised ridge of hair and a painted band)
    for sx in (-1, 1):
        xz = [(sx * 0.026, 1.786), (sx * 0.064, 1.797), (sx * 0.106, 1.797), (sx * 0.148, 1.781)]
        on = _on_face(fd, xz, lift=0.001)
        fd.add(Chain(on, [hr(0.0055), hr(0.0068), hr(0.006), hr(0.003)], k=hr(0.006)), hr(0.004), BROW)
        fd.paint(Chain(on, [hr(0.0125), hr(0.0145), hr(0.013), hr(0.007)], k=hr(0.008)), BROW)
    # eyes: open and bright; the upper lids clear of the irises, the lower lids lifted by the cheeks; smile crinkles
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0058)), Plane(ec + v3((0, 0, hr(0.0215))), (sx * 0.16, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0048)), Plane(ec + v3((0, 0, -hr(0.0158))), (sx * -0.3, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.006), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0195))), (sx * 0.16, 0.05, -1.0)), hr(0.002)), LASH)
        for k in range(2):
            a = hp((sx * (0.11 + 0.004 * k), -0.13 + 0.006 * k, 1.682 - 0.013 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, 0.004 - 0.009 * k)), hr(0.0019), hr(0.0012)), hr(0.003))
    # a straight nose, a soft rounded tip
    fd.add(RoundCone(hp((0, -0.18, 1.726)), hp((0, -0.226, 1.646)), hr(0.0115), hr(0.017)), hr(0.016), SKIN)
    fd.add(S((0, -0.23, 1.632), 0.0215), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.025, -0.208, 1.618), 0.017), hr(0.01), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.013, -0.223, 1.606)), v3((0.008, 0.009, 0.005)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
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
        return np.maximum(np.maximum(dz, dx), -(Q[:, 1] + F(0.205))) * F(HS)
    lo_b, hi_b = hp((-0.09, -0.25, 1.48)), hp((0.09, -0.12, 1.62))
    cav = Inter(Func(opening, lo_b, hi_b), Ellipsoid(hp((0.0, -0.17, 1.55)), v3((0.075, 0.03, 0.05)) * HS), hr(0.002))
    fd.sub(cav, hr(0.004))
    fd.paint(Inter(Func(lambda P: opening(P) - F(0.0025), lo_b, hi_b),
                   Ellipsoid(hp((0.0, -0.17, 1.55)), v3((0.08, 0.04, 0.06)) * HS), hr(0.002)), MOUTH)
    ru = [0.0024, 0.0038, 0.0048, 0.0053, 0.0055, 0.0053, 0.0048, 0.0038, 0.0024]
    rl = [0.0026, 0.0045, 0.006, 0.0068, 0.007, 0.0068, 0.006, 0.0045, 0.0026]
    fd.add(Chain(upper, [hr(r) for r in ru], k=hr(0.005)), hr(0.007), LIP)
    fd.add(Chain(lower, [hr(r) for r in rl], k=hr(0.006)), hr(0.008), LIP)
    for sx in (-1, 1):
        cz = float(mouth_curves(sx * (MOUTH_W + 0.006))[0])
        fd.add(S((sx * 0.082, -0.152, cz + 0.016), 0.012), hr(0.01), SKIN)                 # the grin's cheeks over the corners
        fd.sub(S((sx * (MOUTH_W + 0.017), -0.155, cz + 0.002), 0.0052), hr(0.006))          # dimples
        folds = _on_face(fd, [(sx * 0.046, 1.604), (sx * 0.066, 1.586), (sx * 0.079, 1.562)], lift=-0.002)
        fd.sub(Chain(folds, [hr(0.0022), hr(0.0026), hr(0.002)], k=hr(0.003)), hr(0.004))   # smile folds
    # ears: a rim, a hollow, a lobe
    for sx in (-1, 1):
        R = euler(0, sx * 0.25, sx * -0.35)
        c = hp((sx * 0.157, 0.035, 1.66))
        fd.add(Ellipsoid(c, v3((0.02, 0.04, 0.052)) * HS, R=R), hr(0.02), SKIN)
        o = norm(R @ v3((sx, 0, 0)))
        fd.sub(Ellipsoid(c + o * hr(0.016) + v3((0, -0.004, -0.004)), v3((0.008, 0.022, 0.028)) * HS, R=R), hr(0.006))
        fd.add(Ellipsoid(c + v3((0, 0.002, -0.042)) + o * hr(0.004), v3((0.012, 0.016, 0.016)) * HS, R=R), hr(0.01), SKIN)


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


def eyes_field():
    fd = Field("Eyes")
    for sx in (-1, 1):
        fd.add(Sphere(eye_c(sx), EYE_R))
    return fd


def teeth_field():
    """His upper teeth, showing under his upper lip in the grin (following its curve, set back in the mouth)."""
    fd = Field("Teeth")
    xs = np.linspace(-0.044, 0.044, 7)
    up_z, lo_z = mouth_curves(xs)
    pts = [hp((x, -0.173 + 7.0 * x * x, z - 0.0085)) for x, z in zip(xs, up_z)]
    fd.add(Chain(pts, [hr(0.0088)] * len(pts), k=hr(0.004)), 0.0)
    return fd


# ======================================================================================= the cap (worn backwards)
CAP_IN = 0.012                          # the cap's inside: this far out from his skull
CAP_T = 0.011
BAND_F = v3((0.0, -0.17, 1.868))        # the cap band's plane (design units): across his brow ...
BAND_B = v3((0.0, 0.215, 1.752))        # ... and lower behind, over his nape
_BAND_N = norm(v3((0, -(BAND_B[2] - BAND_F[2]) / (BAND_B[1] - BAND_F[1]), 1.0)))
BAND_H = 0.02                           # (design units) the band's half height


def band_d(P):
    """Height above the cap band's middle plane (design units)."""
    return (hinv(P) - BAND_F.astype(F)) @ _BAND_N.astype(F)


def skull():
    return Ellipsoid(HEAD_C, HEAD_RAD)


_CROWN = Ellipsoid(hp((0.0, 0.03, 1.848)), v3((0.184, 0.208, 0.116)) * HS)


def cap_outer(P):
    """Distance to the cap's outer surface (no cut: the crown all round)."""
    sk = skull()
    return smin(_CROWN(P), sk(P) - F(CAP_IN + CAP_T), F(0.02))


def _cap_axis(P):
    """(angle from his BACK, distance from the cap's upright axis, z) in design units."""
    Q = hinv(P)
    x, y = Q[:, 0], Q[:, 1] - F(0.03)
    return np.arctan2(x, y), np.sqrt(x * x + y * y), Q[:, 2]


PEAK_R0 = 0.198                         # the brim: from inside the band (design, from the cap's axis) ...
PEAK_L = 0.135                          # ... out this far behind him
PEAK_A = 1.0                            # half the angle it spans
PEAK_Z = 1.742
PEAK_SLOPE = 0.22


def peak_d(P):
    a, r, z = _cap_axis(P)
    zc = F(PEAK_Z) - (r - F(PEAK_R0)) * F(PEAK_SLOPE) - F(0.03) * (a / F(PEAK_A)) ** 2 * np.clip((r - F(PEAK_R0)) / F(PEAK_L), 0, 1)
    rmax = F(PEAK_R0) + F(PEAK_L) * np.sqrt(np.clip(F(1) - (a / F(PEAK_A)) ** 2, 0, 1))
    outline = np.maximum(np.maximum(F(PEAK_R0 - 0.04) - r, r - rmax), np.abs(a) - F(PEAK_A))
    return np.maximum(outline, np.abs(z - zc) - F(0.006)) * F(HS)


def cap_field():
    """Coyote-tan cotton twill (uniform material, label 0): six panels with sewn seams from a button on top, worn backwards
    (the brim out over his nape, slightly curved)."""
    fd = Field("Cap")
    lo, hi = HEAD_C + v3((-0.3, -0.33, -0.16)), HEAD_C + v3((0.3, 0.42, 0.32))
    sk = skull()
    twill = lambda P: F(0.0008) * NOISE(P * F(45)) + F(0.0008) * NOISE(P * F(14))
    def body(P):
        b = np.maximum(cap_outer(P), -(sk(P) - F(CAP_IN)))
        return np.maximum(b, -band_d(P) * F(HS) - F(BAND_H * HS))
    fd.add(Func(body, lo, hi, disp=twill, disp_amp=0.0012), 0.0)
    # sewn seams between the panels (grooves from the button down to the band)
    def seams(P):
        a, r, z = _cap_axis(P)
        k = np.round(a / F(math.pi / 3))
        dd = np.abs(np.sin(a - k * F(math.pi / 3))) * r * F(HS)
        return np.maximum(np.maximum(dd - F(0.0016), -cap_outer(P) - F(0.0028)), cap_outer(P) - F(0.004))
    fd.sub(Func(seams, lo, hi), 0.0012)
    # the brim, and the button on top
    fd.add(Func(peak_d, lo, hi), 0.008)
    h, ok = ray_hit(Func(cap_outer, lo, hi), [hp((0.0, 0.03, 2.3))], [v3((0, 0, -1))], tmax=0.6)
    top = h[0] if ok[0] else hp((0.0, 0.03, 1.97))
    fd.add(Ellipsoid(top, (0.017, 0.017, 0.009)), 0.005)
    return fd


# ======================================================================================= hair
def hair_field():
    """Short black hair, cut close at the sides and the back: under the cap's band over his temples and round the back of
    his head to the nape, short sideburns."""
    fd = Field("Hair")
    sk = skull()
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        under = band_d(P) - F(0.004)
        face = np.where(ax < F(0.135), F(-0.09) - y, F(-0.075) - y + F(0.3) * np.maximum(F(1.62) - z, F(0)))
        ear = np.where((ax > F(0.15)) & (z < F(1.735)) & (np.abs(y - F(0.035)) < F(0.058)), F(0.02), F(-1.0))
        nape = F(1.585) - z + F(0.01) * np.sin(x * F(70))
        return np.maximum(np.maximum(np.maximum(under, face), ear), nape)
    comb = lambda P: F(0.0007) * np.sin(hinv(P)[:, 2] * F(420) + F(2) * NOISE(P * F(20))) + F(0.0008) * NOISE(P * F(70))
    fd.add(Inter(Shell(sk, 0.004, 0.011, pad=0.06, disp=comb, disp_amp=0.0012), Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.003), 0.0)
    return fd


# ======================================================================================= headset and glasses
CUP_C = {sx: hp((sx * 0.208, 0.034, 1.664)) for sx in (-1, 1)}
CUP_N = {sx: norm(v3((sx, 0.06, 0.12))) for sx in (-1, 1)}
CUP_R = hr(0.05)


def band_points():
    """The headband's middle line over the cap (and the outward directions), from his right cup's top to his left's."""
    cb = hp((0.0, 0.034, 1.73))
    def outer(P):
        return np.minimum(cap_outer(P), skull()(P) - F(0.016))
    f = Func(outer, HEAD_C - 0.45, HEAD_C + 0.45)
    pts, nrm = [], []
    for th in np.linspace(-1.2, 1.2, 13):
        d = v3((math.sin(th), 0.0, math.cos(th)))
        h, ok = ray_hit(f, [cb + d * 0.45], [-d], tmax=0.45, step=0.001)
        p = (h[0] if ok[0] else cb + d * 0.22) + d * 0.008
        pts.append(p)
        nrm.append(d)
    ends = []
    for sx in (-1, 1):
        ends.append(CUP_C[sx] + v3((0, 0, CUP_R * 0.8)) + CUP_N[sx] * 0.004)
    return [ends[0]] + pts + [ends[1]], [v3((-1, 0, 0.2))] + nrm + [v3((1, 0, 0.2))]


def mic_points():
    return [hp((0.212, 0.0, 1.632)), hp((0.19, -0.1, 1.597)), hp((0.146, -0.176, 1.572)), hp((0.092, -0.224, 1.561))]


LENS_C = {sx: hp((sx * 0.071, -0.213, 1.68)) for sx in (-1, 1)}
LENS_N = {sx: norm(v3((sx * 0.17, -1.0, 0.04))) for sx in (-1, 1)}
LENS_HW, LENS_HH = hr(0.047), hr(0.033)


def _rim_d(P, c, R, hw, hh, cr, th, th_top, dp):
    q = (P - c.astype(F)) @ R.astype(F)
    qx = np.abs(q[:, 0]) - F(hw - cr)
    qy = np.abs(q[:, 1]) - F(hh - cr)
    d2 = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - F(cr)
    t = F(th) + F(th_top - th) * np.clip(q[:, 1] / F(hh), 0, 1) ** 2
    ring = np.abs(d2 + t * F(0.6)) - t
    dz = np.abs(q[:, 2]) - F(dp)
    return np.sqrt(np.maximum(ring, 0) ** 2 + np.maximum(dz, 0) ** 2) + np.minimum(np.maximum(ring, dz), 0)


def headgear_field():
    """fieldgun material: the headset's olive-drab cups (label 0) with black cushions and band (8), gunmetal (5) yokes and
    sliders; the boom mic (8); the glasses' black frames (8)."""
    fd = Field("Headgear")
    for sx in (-1, 1):
        c, n = CUP_C[sx], CUP_N[sx]
        Rn = rot_from_axes(z_axis=n)
        fd.add(Cylinder(c - n * hr(0.012), CUP_R * 0.95, hr(0.024), rr=hr(0.01), R=Rn), 0.0, 8)        # the cushion
        fd.add(Cylinder(c + n * hr(0.012), CUP_R, hr(0.03), rr=hr(0.012), R=Rn), 0.004, 0)             # the cup
        fd.add(Ellipsoid(c + n * hr(0.026), v3((0.042, 0.042, 0.016)) * HS, R=Rn), 0.006, 0)           # its domed face
        fd.add(Cylinder(c + n * hr(0.04), hr(0.012), hr(0.012), rr=hr(0.004), R=Rn), 0.003, 5)          # a knob
        # the yoke: from the cup's top up to the band
        top = c + v3((0, 0, CUP_R * 0.8)) + n * 0.004
        fd.add(RoundBox(top + v3((0, 0, 0.004)), (hr(0.014), hr(0.022), hr(0.01)), hr(0.004), R=_frame(n)), 0.004, 5)
    pts, nrm = band_points()
    fd.add(Lock(pts, [hr(0.022)] * len(pts), [hr(0.0075)] * len(pts), nrm, k=hr(0.004)), 0.004, 8)
    for i in (1, len(pts) - 2):                                                                          # the sliders
        d = norm(pts[i + 1] - pts[i - 1])
        fd.add(RoundBox(pts[i], (hr(0.016), hr(0.026), hr(0.012)), hr(0.005), R=rot_from_axes(z_axis=d, x_axis=nrm[i])), 0.003, 5)
    mp = mic_points()
    fd.add(Chain(mp, [hr(0.0055), hr(0.005), hr(0.0048), hr(0.0045)], k=hr(0.004)), 0.004, 8)
    fd.add(Ellipsoid(mp[-1] + norm(mp[-1] - mp[-2]) * hr(0.006), v3((0.014, 0.014, 0.017)) * HS, R=rot_from_axes(z_axis=mp[-1] - mp[-2])), 0.004, 8)
    # the glasses: black rectangular frames, a bolder browline, a bridge, temples back to his ears
    for sx in (-1, 1):
        c, n = LENS_C[sx], LENS_N[sx]
        R = _frame(n)
        fd.add(Func(lambda P, c=c, R=R: _rim_d(P, c, R, LENS_HW, LENS_HH, hr(0.016), hr(0.0034), hr(0.0072), hr(0.0042)),
                    c - 0.08, c + 0.08), 0.002, 8)
        a = c + R[:, 0] * (sx * LENS_HW * 0.98) + R[:, 1] * (LENS_HH * 0.55)
        tpts = [a, hp((sx * 0.162, -0.12, 1.703)), hp((sx * 0.176, -0.04, 1.699)), hp((sx * 0.184, 0.02, 1.686))]
        fd.add(Chain(tpts, [hr(0.0042), hr(0.0036), hr(0.0034), hr(0.0034)], k=hr(0.003)), 0.003, 8)
    b0 = LENS_C[-1] + _frame(LENS_N[-1])[:, 0] * (LENS_HW * 0.9) + _frame(LENS_N[-1])[:, 1] * (LENS_HH * 0.35)
    b1 = LENS_C[1] - _frame(LENS_N[1])[:, 0] * (LENS_HW * 0.9) + _frame(LENS_N[1])[:, 1] * (LENS_HH * 0.35)
    fd.add(Chain([b0, hp((0.0, -0.229, 1.696)), b1], [hr(0.0042), hr(0.004), hr(0.0042)], k=hr(0.003)), 0.003, 8)
    return fd


# ======================================================================================= the combat shirt (olive)
SH_OFF, SH_T = 0.014, 0.011
SH_OUT = SH_OFF + SH_T / 2
SLEEVE_T = 0.15                        # the rolled sleeves end this far down the forearm (fraction of elbow -> wrist)


def body_hull(arms=True):
    b = Field("BodyHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(neck_prim(), 0.05)                   # (as the skin is built: its smooth unions swell the same way)
    if arms:
        for side in ("R", "L"):
            b.add(deltoid(side), 0.055)
            for p, k in upper_arm_prims(side) + forearm_prims(side):
                b.add(p, k)
    return b


_BH = []


def shirt_hull():
    if not _BH:
        _BH.append(body_hull(True))
    return _BH[0]


def sleeve_end(side):
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    return el + ax * (float(np.linalg.norm(wr - el)) * SLEEVE_T), ax


def sleeve_cut(P):
    """> 0 past the rolled sleeves' ends (only near the forearms)."""
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        c, ax = sleeve_end(side)
        wr = J["wrist_" + side]
        along = (P - c.astype(F)) @ ax.astype(F)
        near = _seg_dist(P, c - ax * 0.12, wr + ax * 0.25) < F(0.13)
        out = np.maximum(out, np.where(near, along, F(-1.0)))
    return out


def neck_line(P, base, rise=0.07):
    """> 0 above a neckline round his neck only (lifted clear of the shoulders: no hole on them)."""
    ax = np.abs(P[:, 0])
    return P[:, 2] - (F(base) + F(rise) * smoothstep(-0.06, 0.1, P[:, 1]) + F(0.3) * smoothstep(0.11, 0.17, ax))


def shirt_field():
    """Olive-drab ripstop (uniform material, label 0): the combat shirt, tucked in at his waist, the sleeves rolled up to
    just below his elbows (a thick roll of cloth), a folded collar open at the throat; the unit patch on his left sleeve
    (red, 5, with a white bar, 7)."""
    fd = Field("Shirt")
    hull = shirt_hull()
    def wr_(P):
        return (F(0.0012) * NOISE(P * F(26)) + F(0.0016) * NOISE(P * F(7))
                + F(0.0015) * np.sin(P[:, 2] * F(55) + F(2) * NOISE(P * F(5))) * smoothstep(0.28, 0.4, np.abs(P[:, 0])))
    def cut(P):
        return np.maximum(np.maximum(F(0.86) - P[:, 2], neck_line(P, 1.43)), sleeve_cut(P))
    fd.add(Inter(Shell(hull, SH_OFF, SH_T, pad=0.1, disp=wr_, disp_amp=0.003), Func(cut, (-1, -0.6, 0.7), (1, 0.6, 1.7)), 0.004), 0.0)
    # the rolled sleeves
    for side in ("R", "L"):
        c, ax = sleeve_end(side)
        arm = Field("Arm" + side)
        arm.add(deltoid(side), 0.0)
        for p, k in upper_arm_prims(side) + forearm_prims(side):
            arm.add(p, k)
        def band(P, c=c, ax=ax):
            s = (P - c.astype(F)) @ ax.astype(F)
            near = _seg_dist(P, c - ax * 0.1, c + ax * 0.1) < F(0.14)
            return np.where(near, np.abs(s + F(0.014)) - F(0.023), F(1.0))
        roll = lambda P: F(0.003) * np.sin(np.arctan2(P[:, 2], P[:, 1]) * F(7) + F(2) * NOISE(P * F(12))) + F(0.001) * NOISE(P * F(40))
        fd.add(Inter(Shell(arm, SH_OFF + 0.014, 0.026, pad=0.06, disp=roll, disp_amp=0.004), Func(band, c - 0.2, c + 0.2), 0.008), 0.006)
    # the folded collar: a band round his neck, open at the throat, its points lying out over the vest
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    def collar(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        top = F(1.475) + F(0.05) * smoothstep(-0.06, 0.1, y)
        gap = np.where(y < F(0.0), F(0.032) - np.abs(x), F(-1.0))
        return np.maximum(np.maximum(z - top, F(1.405) - z), gap)
    fd.add(Inter(Shell(nk, 0.024, 0.011, pad=0.06), Func(collar, (-0.25, -0.25, 1.35), (0.25, 0.25, 1.6)), 0.003), 0.006)
    for sx in (-1, 1):
        pts = [v3((sx * 0.036, -0.088, 1.462)), v3((sx * 0.066, -0.112, 1.418)), v3((sx * 0.086, -0.13, 1.384))]
        fd.add(Lock(pts, [0.03, 0.026, 0.012], [0.006, 0.006, 0.005], [norm(v3((sx * 0.3, -1, 0.5)))] * 3, k=0.004), 0.006)
    # the unit patch on his left sleeve
    pc, pn, R = patch_frame()
    fd.add(RoundBox(pc + pn * 0.004, (0.034, 0.026, 0.004), 0.003, R=R), 0.003, 5)
    fd.paint(RoundBox(pc + pn * 0.004, (0.036, 0.0075, 0.012), 0.001, R=R), 7)
    return fd


def patch_frame():
    """The unit patch on his left sleeve: (centre on the sleeve, outward normal, frame (across, up the arm, normal))."""
    sh, el = J["shoulder_L"], J["elbow_L"]
    ax = norm(sh - el)
    p0 = lerp(sh, el, 0.36)
    o = norm(v3((1, -0.25, 0)) - ax * float(v3((1, -0.25, 0)) @ ax))
    hull = shirt_hull()
    f = Func(lambda P: hull.eval(P, margin=0.1) - F(SH_OUT + 0.002), p0 - 0.4, p0 + 0.4)
    h, ok = ray_hit(f, [p0 + o * 0.3], [-o], tmax=0.4)
    p = h[0] if ok[0] else p0 + o * 0.1
    n = _fgrad(f.fn, p)
    return p, n, _frame(n, ax)


# ======================================================================================= the engineer's vest (coyote tan)
V_OFF, V_T = 0.036, 0.016
V_OUT = V_OFF + V_T / 2
V_HEM = 0.955
_VH = []


def vest_hull():
    if not _VH:
        _VH.append(body_hull(False))
    return _VH[0]


def vest_cut(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    neck = neck_line(P, 1.405, 0.08)
    arm = ax - (F(0.2) + F(0.3) * smoothstep(1.2, 1.06, z))
    vee = np.where(y < F(0.0), F(0.006) + F(0.055) * smoothstep(1.27, 1.42, z) - ax, F(-1.0))
    hem = F(V_HEM) - z - F(0.012) * smoothstep(0.05, -0.1, y) * (F(1) - smoothstep(0.0, 0.1, ax))
    return np.maximum(np.maximum(np.maximum(neck, arm), vee), hem)


def vest_outer():
    h = vest_hull()
    return Func(lambda P: h.eval(P, margin=0.12) - F(V_OUT), (-0.6, -0.6, 0.8), (0.6, 0.6, 1.6))


def vest_field():
    """Coyote-tan cordura (uniform: label 0): zipped up the front (a black zip, 8), open at the throat in a short V, PALS
    rows of darker webbing (7) round its sides and back, padded shoulders."""
    fd = Field("Vest")
    hull = vest_hull()
    lo, hi = (-0.6, -0.5, 0.85), (0.6, 0.5, 1.62)
    def rows(P):
        z = P[:, 2]
        k = np.clip((z - F(0.985)) / F(0.034), -1, 7)
        fr = k - np.floor(k)
        on = smoothstep(0.96, 0.99, z) * smoothstep(1.24, 1.2, z)
        return F(0.0016) * smoothstep(0.18, 0.32, fr) * smoothstep(0.82, 0.68, fr) * on
    def cloth(P):
        d = hull.eval(P, margin=0.08)
        pad = F(0.006) * smoothstep(1.36, 1.44, P[:, 2]) * smoothstep(0.08, 0.13, np.abs(P[:, 0]))
        return np.abs(d - F(V_OFF) - pad) - F(V_T * 0.5) - rows(P) + F(0.0009) * NOISE(P * F(30))
    fd.add(Inter(Func(cloth, lo, hi), Func(vest_cut, lo, hi), 0.004), 0.0)
    # its edges bound in tape: a raised roll along the neck, the armholes and the hem
    def edge(P):
        e = -vest_cut(P)
        return np.maximum(np.abs(e - F(0.006)) - F(0.006), np.abs(hull.eval(P, margin=0.08) - F(V_OUT + 0.001)) - F(0.0075))
    fd.add(Func(edge, lo, hi), 0.003)
    # the PALS rows (painted darker), round the sides and back
    def pals(P):
        z = P[:, 2]
        k = (z - F(0.985)) / F(0.034)
        fr = k - np.floor(k)
        band = np.abs(fr - F(0.5)) - F(0.2)
        return np.maximum(np.maximum(band * F(0.034), np.maximum(F(0.975) - z, z - F(1.23))), F(0.1) - np.abs(P[:, 0]) - np.maximum(P[:, 1], 0) * F(4))
    fd.paint(Func(pals, lo, hi), 7)
    # the zip
    fd.paint(Func(lambda P: np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.0062), P[:, 1] + F(0.05)), P[:, 2] - F(1.3)), lo, hi), 8)
    return fd


# ---------------------------------------------------------------------------------------------- pouches, belt (the kit)
def vest_spot(x, z, front=True):
    """A point on the vest's outer face at (x, z) seen from the front (or back), and its outward normal."""
    f = vest_outer()
    y0 = -0.7 if front else 0.7
    h, ok = ray_hit(f, [v3((x, y0, z))], [v3((0, 1 if front else -1, 0))], tmax=1.0, step=0.0015)
    p = h[0] if ok[0] else v3((x, -0.22 if front else 0.28, z))
    return p, _fgrad(f.fn, p)


BELT_Z, BELT_W = 0.934, 0.021
T_OFF = 0.016                          # the trousers' offset over his hips
BELT_OFF = T_OFF + 0.012 + 0.008


def hips_hull():
    b = Field("Hips")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    return b


def belt_spot(angle_deg, out=0.0, dz=0.0):
    """A point on the belt's outer face at an angle round him (0 = his front, 90 = his left), and the outward normal."""
    hh = hips_hull()
    a = math.radians(angle_deg)
    d = v3((math.sin(a), -math.cos(a), 0.0))
    f = Func(lambda P: hh.eval(P, margin=0.12) - F(BELT_OFF + 0.006 + out), (-0.8, -0.8, 0.6), (0.8, 0.8, 1.2))
    h, ok = ray_hit(f, [v3((0, 0.04, BELT_Z + dz)) + d * 0.6], [-d], tmax=0.7)
    p = h[0] if ok[0] else v3((0, 0.04, BELT_Z + dz)) + d * 0.24
    return p, norm(v3((d[0], d[1], 0.0)))


POUCHES = {                             # (x, z, half sizes (across, up, out), front)
    "radio": (0.112, 1.255, (0.04, 0.062, 0.024), True),
    "tools": (-0.106, 1.262, (0.05, 0.05, 0.011), True),
    "grenades": (-0.118, 1.06, (0.068, 0.046, 0.032), True),
    "admin": (0.118, 1.058, (0.052, 0.05, 0.028), True),
    "pack": (0.0, 1.16, (0.115, 0.15, 0.042), False),
}


def pouch_frame(key):
    x, z, half, front = POUCHES[key]
    p, n = vest_spot(x, z, front)
    R = _frame(n)
    return p + n * (half[2] - 0.004), R, half


def _box_pouch(fd, key, flap=True, label=0):
    c, R, half = pouch_frame(key)
    s, u, n = R[:, 0], R[:, 1], R[:, 2]
    sc = lambda P: F(0.0009) * NOISE(P * F(32))
    fd.add(RoundBox(c, half, min(half) * 0.45, R=R, disp=sc, disp_amp=0.001), 0.006, label)
    if flap:
        fd.add(RoundBox(c + u * (half[1] * 0.62) + n * (half[2] * 0.2), (half[0] + 0.003, half[1] * 0.42, half[2] * 0.85), 0.008, R=R), 0.004, label)
        fd.add(RoundBox(c + u * (half[1] * 0.25) + n * (half[2] + 0.002), (0.011, 0.016, 0.004), 0.002, R=R), 0.002, 8)   # a buckle
    # webbing straps behind it (PALS), darker
    for k in (-1, 1):
        fd.add(RoundBox(c + s * (k * half[0] * 0.55) - n * (half[2] * 0.6), (0.011, half[1] * 0.85, 0.004), 0.002, R=R), 0.003, 7)
    return c, R, half


def kit_field():
    """Coyote tan (uniform: label 0) with darker webbing (7) and black buckles (8): the vest's pouches (a radio pouch, a
    flat sleeve of tools, a double pouch of EMP grenades, an admin pouch, the battery pack on his back); the black rigger's
    belt (8) with a gunmetal buckle (6); a pliers holster on his right hip; a carabiner (6) on his left."""
    fd = Field("Kit")
    _box_pouch(fd, "radio", flap=False)
    c, R, half = pouch_frame("tools")
    fd.add(RoundBox(c, half, 0.008, R=R), 0.004, 0)
    for k in (-1, 0, 1):                                                                 # stitched slots
        fd.sub(RoundBox(c + R[:, 0] * (k * 0.024 + 0.012) + R[:, 2] * half[2], (0.0012, half[1] * 0.8, 0.003), 0.001, R=R), 0.001)
    _box_pouch(fd, "grenades", flap=False)
    _box_pouch(fd, "admin", flap=True)
    c, R, half = _box_pouch(fd, "pack", flap=False)
    fd.add(RoundBox(c + R[:, 2] * (half[2] + 0.002) + R[:, 1] * 0.02, (half[0] * 0.7, half[1] * 0.55, 0.006), 0.004, R=R), 0.003, 7)
    # the belt
    hh = hips_hull()
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(BELT_W), (-0.45, -0.4, BELT_Z - 0.06), (0.45, 0.42, BELT_Z + 0.06)),
                 Shell(hh, BELT_OFF, 0.012, pad=0.12, disp=lambda P: F(0.0006) * NOISE(P * F(60)), disp_amp=0.0008), 0.003), 0.004, 8)
    p, n = belt_spot(0.0, 0.004)
    Rb = _frame(n)
    fd.add(RoundBox(p + n * 0.006, (0.036, 0.024, 0.008), 0.005, R=Rb), 0.003, 6)
    fd.add(RoundBox(p + n * 0.012, (0.02, 0.014, 0.004), 0.003, R=Rb), 0.002, 8)
    # the pliers holster on his right hip
    p, n = belt_spot(-96.0, 0.004, dz=-0.04)
    Rh = _frame(n)
    fd.add(RoundBox(p + n * 0.02, (0.03, 0.06, 0.016), 0.012, R=Rh), 0.004, 0)
    fd.add(RoundBox(p + n * 0.012 + Rh[:, 1] * 0.045, (0.026, 0.016, 0.01), 0.004, R=Rh), 0.003, 7)
    # the carabiner on his left hip
    p, n = belt_spot(96.0, 0.006, dz=-0.03)
    Rc = _frame(n)
    fd.add(Torus(p + n * 0.012 - Rc[:, 1] * 0.012, 0.022, 0.0045, R=rot_from_axes(z_axis=Rc[:, 0])), 0.002, 6)
    return fd


def tools_field():
    """fieldgun material: the radio (black, 8; gunmetal knobs, 5) and its antenna; a yellow (0) screwdriver, a black pen
    and a torch in the tool sleeve; two EMP grenades in their pouch (black caps, gunmetal, a blue band: 12); a yellow
    multimeter in the admin pouch (a dark screen, 8); the pliers in their holster (steel 7, black grips); a coil of black
    cable on the carabiner."""
    fd = Field("Tools")
    # the radio
    c, R, half = pouch_frame("radio")
    s, u, n = R[:, 0], R[:, 1], R[:, 2]
    rc = c + u * (half[1] + 0.012)
    fd.add(RoundBox(rc, (0.032, 0.036, 0.02), 0.008, R=R), 0.0, 8)
    fd.add(Cylinder(rc + u * 0.04 + s * 0.016, 0.009, 0.014, rr=0.003, R=rot_from_axes(z_axis=u)), 0.002, 5)
    fd.add(Cylinder(rc + u * 0.04 - s * 0.012, 0.006, 0.01, rr=0.002, R=rot_from_axes(z_axis=u)), 0.002, 5)
    a0 = rc + u * 0.036 + s * 0.016
    ad = norm(u * 1.0 + s * 0.25 + n * -0.12)
    fd.add(RoundCone(a0, a0 + ad * 0.17, 0.007, 0.005), 0.003, 8)
    fd.add(Sphere(a0 + ad * 0.17, 0.0065), 0.002, 8)
    # the tool sleeve: a screwdriver, a pen, a torch
    c, R, half = pouch_frame("tools")
    s, u, n = R[:, 0], R[:, 1], R[:, 2]
    top = c + u * half[1]
    sd = top - s * 0.024
    fd.add(RoundCone(sd - u * 0.03, sd + u * 0.05, 0.0105, 0.0095), 0.0, 0)
    fd.add(Sphere(sd + u * 0.05, 0.0095), 0.003, 0)
    pn = top + s * 0.002
    fd.add(RoundCone(pn - u * 0.03, pn + u * 0.04, 0.0055, 0.005), 0.002, 8)
    fd.add(RoundBox(pn + u * 0.025 + n * 0.006, (0.0025, 0.012, 0.002), 0.001, R=R), 0.001, 7)
    tc = top + s * 0.027
    fd.add(RoundCone(tc - u * 0.03, tc + u * 0.04, 0.0105, 0.0105), 0.002, 8)
    fd.add(Cylinder(tc + u * 0.045, 0.0135, 0.016, rr=0.003, R=rot_from_axes(z_axis=u)), 0.003, 5)
    # the EMP grenades in their pouch
    c, R, half = pouch_frame("grenades")
    s, u, n = R[:, 0], R[:, 1], R[:, 2]
    for k in (-1, 1):
        g = c + s * (k * 0.034) + u * (half[1] + 0.006)
        fd.add(Cylinder(g, 0.027, 0.03, rr=0.008, R=rot_from_axes(z_axis=u)), 0.0, 5)
        fd.add(Torus(g + u * 0.003, 0.0272, 0.0045, R=rot_from_axes(z_axis=u)), 0.002, 12)
        fd.add(Cylinder(g + u * 0.019, 0.023, 0.012, rr=0.004, R=rot_from_axes(z_axis=u)), 0.003, 8)
    # the multimeter in the admin pouch
    c, R, half = pouch_frame("admin")
    s, u, n = R[:, 0], R[:, 1], R[:, 2]
    mc = c + u * (half[1] + 0.008) - n * 0.004
    fd.add(RoundBox(mc, (0.034, 0.03, 0.013), 0.008, R=R), 0.0, 0)
    fd.add(RoundBox(mc + u * 0.008 + n * 0.012, (0.022, 0.012, 0.003), 0.002, R=R), 0.002, 8)
    # the pliers in their holster
    p, nn = belt_spot(-96.0, 0.004, dz=-0.04)
    Rh = _frame(nn)
    for k in (-1, 1):
        g0 = p + nn * 0.02 + Rh[:, 1] * 0.06 + Rh[:, 0] * (k * 0.008)
        fd.add(RoundCone(g0, g0 + Rh[:, 1] * 0.045 + Rh[:, 0] * (k * 0.01), 0.008, 0.007), 0.003, 8)
    fd.add(RoundCone(p + nn * 0.02 + Rh[:, 1] * 0.1, p + nn * 0.02 + Rh[:, 1] * 0.13, 0.009, 0.004), 0.003, 7)
    # a coil of cable on the carabiner
    p, nn = belt_spot(96.0, 0.006, dz=-0.03)
    Rc = _frame(nn)
    cc = p + nn * 0.022 - Rc[:, 1] * 0.05
    fd.add(Torus(cc, 0.04, 0.009, R=rot_from_axes(z_axis=Rc[:, 2] * 0.9 + Rc[:, 0] * 0.4)), 0.0, 8)
    fd.add(Torus(cc + Rc[:, 2] * 0.008, 0.036, 0.008, R=rot_from_axes(z_axis=Rc[:, 2] * 0.9 - Rc[:, 0] * 0.3)), 0.004, 8)
    return fd


# ======================================================================================= trousers, boots
BOOT_TOP = 0.36


def legs_hull():
    b = Field("Legs")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            b.add(p, k)
        sh = shin_prims(side)
        b.add(sh[0][0], sh[0][1])
        b.add(sh[1][0], sh[1][1])
    return b


def trousers_field():
    """Olive-drab ripstop (uniform: label 0) from his waist to his boots, bloused over their tops; a cargo pocket on each
    thigh with a flap; black knee pads (8)."""
    fd = Field("Trousers")
    legs = legs_hull()
    folds = lambda P: (F(0.004) * np.sin(np.arctan2(P[:, 1] - F(0.02), P[:, 0] - np.sign(P[:, 0]) * F(0.15)) * F(7)) * smoothstep(0.72, 0.5, P[:, 2])
                       + F(0.0012) * NOISE(P * F(25)))
    fd.add(Inter(Shell(legs, T_OFF, 0.012, pad=0.1, disp=folds, disp_amp=0.005),
                 Func(lambda P: np.maximum(F(BOOT_TOP + 0.02) - P[:, 2], P[:, 2] - F(1.0)), (-0.5, -0.4, 0.25), (0.5, 0.4, 1.1)), 0.004), 0.0)
    # bloused over the boots
    blouse = lambda P: F(0.004) * np.sin(np.arctan2(P[:, 1], P[:, 0] - np.sign(P[:, 0]) * F(0.165)) * F(9)) + F(0.001) * NOISE(P * F(30))
    fd.add(Inter(Shell(legs, T_OFF + 0.012, 0.022, pad=0.1, disp=blouse, disp_amp=0.005),
                 Func(lambda P: np.abs(P[:, 2] - F(BOOT_TOP + 0.04)) - F(0.035), (-0.5, -0.4, 0.25), (0.5, 0.4, 0.5)), 0.006), 0.012)
    outer = Func(lambda P: legs.eval(P, margin=0.1) - F(T_OFF + 0.006), (-0.6, -0.5, 0.2), (0.6, 0.5, 1.1))
    for sx in (-1, 1):
        # the cargo pocket
        h, ok = ray_hit(outer, [v3((sx * 0.55, 0.0, 0.6))], [v3((-sx, 0, 0))], tmax=0.6)
        if ok[0]:
            p = h[0]
            n = _fgrad(outer.fn, p)
            R = _frame(n, J["hip_" + ("R" if sx < 0 else "L")] - J["knee_" + ("R" if sx < 0 else "L")])
            fd.add(RoundBox(p + n * 0.012, (0.058, 0.07, 0.016), 0.012, R=R, disp=lambda P: F(0.001) * NOISE(P * F(30)), disp_amp=0.001), 0.006)
            fd.add(RoundBox(p + n * 0.026 + R[:, 1] * 0.05, (0.062, 0.026, 0.008), 0.006, R=R), 0.004)
        # the knee pad
        kn = J["knee_" + ("R" if sx < 0 else "L")]
        kc = kn + v3((0.0, -0.1, 0.01))
        fd.add(Ellipsoid(kc, (0.066, 0.034, 0.082), R=euler(0.12, 0, 0)), 0.01, 8)
        fd.add(Inter(Shell(legs, T_OFF + 0.008, 0.008, pad=0.1), Func(lambda P, kc=kc: np.maximum(np.abs(P[:, 2] - F(kc[2] + 0.06)) - F(0.012),
                                                                                                 np.abs(P[:, 0] - F(kc[0])) - F(0.14)), kc - 0.25, kc + 0.25), 0.003), 0.004, 8)
    return fd


def boot_base(side):
    b = Field("BootBase" + side)
    an = J["ankle_" + side]
    for p, k in shin_prims(side):
        b.add(p, k)
    b.add(RoundCone(an + v3((0, 0.01, -0.02)), an + v3((0, 0.02, 0.12)), 0.058, 0.06), 0.03)
    foot(b, side)
    return b


def boots_field():
    """Black leather combat boots (label 0) to mid-calf, a padded collar at the top, laced up the front, thick lugged
    soles (5)."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        bb = boot_base(side)
        crease = lambda P: F(0.0012) * NOISE(P * F(26)) + F(0.0015) * np.sin(P[:, 2] * F(90)) * smoothstep(0.12, 0.07, P[:, 2])
        lo, hi = an - v3((0.2, 0.35, 0.2)), an + v3((0.2, 0.25, 0.4))
        fd.add(Inter(Shell(bb, 0.018, 0.016, pad=0.06, disp=crease, disp_amp=0.003), Func(lambda P: P[:, 2] - F(BOOT_TOP), lo, hi), 0.004), 0.0)
        fd.add(Inter(Shell(bb, 0.026, 0.012, pad=0.06), Func(lambda P: np.abs(P[:, 2] - F(BOOT_TOP - 0.012)) - F(0.012), lo, hi), 0.003), 0.004)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        rgt = Rz @ v3((1, 0, 0))
        fd.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.098)), (0.075, 0.168, 0.018), 0.011, R=Rz), 0.006, 5)
        fd.add(RoundBox(an - fwd * 0.03 + v3((0, 0, -0.09)), (0.062, 0.056, 0.028), 0.01, R=Rz), 0.006, 5)
        for k in range(6):                                                                     # lugs round the sole
            fd.sub(RoundBox(an + fwd * (-0.06 + 0.05 * k) + v3((0, 0, -0.116)), (0.09, 0.007, 0.008), 0.003, R=Rz), 0.003)
        for k in range(6):                                                                     # the laces
            z = 0.13 + 0.04 * k
            c = an + fwd * (0.07 - 0.009 * k - (0.03 if k > 1 else 0.0)) + v3((0, 0, z - an[2]))
            h, ok = ray_hit(Func(lambda P, bb=bb: bb.eval(P, margin=0.1) - F(0.034), an - 0.4, an + 0.5), [c + fwd * 0.3], [-fwd], tmax=0.4)
            if ok[0]:
                fd.add(RoundCone(h[0] - rgt * 0.022, h[0] + rgt * 0.022, 0.0042, 0.0042), 0.003)
    return fd


# ======================================================================================= the gauntlet (right forearm, fist)
GA_T = (0.2, 0.97)                      # the sleeve: this far down the forearm to that (fractions of elbow -> wrist)


def forearm_frame(side="R"):
    """(el, ax: down the forearm, out: its outer side (away from his body), top: its thumb side, L)."""
    sx = -1 if side == "R" else 1
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    out = norm(v3((sx, 0, 0)) - ax * float(v3((sx, 0, 0)) @ ax))
    top = norm(np.cross(ax, out))
    if top[1] > 0:
        top = -top
    return el, ax, out, top, float(np.linalg.norm(wr - el))


def forearm_hull(side):
    f = Field("Forearm" + side)
    for p, k in forearm_prims(side):
        f.add(p, k)
    return f


def _fa_band(P, el, ax, L, s0, s1):
    s = (P - el.astype(F)) @ ax.astype(F)
    return np.maximum(F(L * s0) - s, s - F(L * s1))


def _fa_spot(side, s, dvec, gap=0.0):
    el, ax, out, top, L = forearm_frame(side)
    c0 = el + ax * (L * s)
    f = forearm_hull(side)
    h, ok = ray_hit(Func(lambda P: f.eval(P, margin=0.1) - F(gap), c0 - 0.3, c0 + 0.3), [c0 + dvec * 0.3], [-dvec], tmax=0.3)
    return h[0] if ok[0] else c0 + dvec * 0.08


def gauntlet_field():
    """fieldgun material (tan 0, gunmetal 5, steel 7, black 8): a black padded sleeve (8) from below his elbow over his
    wrist, gunmetal armour plates over it (tan panels on their outer faces), two steel pistons in gunmetal cylinders along
    its back, a power cell on its top (its three slits glow: Cells), a black cuff at its elbow end."""
    fd = Field("Gauntlet")
    el, ax, out, top, L = forearm_frame("R")
    f = forearm_hull("R")
    lo, hi = np.minimum(el, J["wrist_R"]) - 0.2, np.maximum(el, J["wrist_R"]) + 0.2
    fd.add(Inter(Shell(f, 0.013, 0.012, pad=0.06), Func(lambda P: _fa_band(P, el, ax, L, *GA_T), lo, hi), 0.004), 0.0, 8)
    fd.add(Inter(Shell(f, 0.022, 0.012, pad=0.06), Func(lambda P: _fa_band(P, el, ax, L, GA_T[0], GA_T[0] + 0.07), lo, hi), 0.003), 0.004, 8)
    # the armour: two shells (upper, lower) with a gap between, bevelled
    for s0, s1 in ((0.28, 0.58), (0.62, 0.92)):
        fd.add(Inter(Shell(f, 0.031, 0.013, pad=0.06), Func(lambda P, s0=s0, s1=s1: _fa_band(P, el, ax, L, s0, s1), lo, hi), 0.006), 0.004, 5)
        # a tan panel on its outer face
        def panel(P, s0=s0, s1=s1):
            q = P - el.astype(F)
            return np.maximum(_fa_band(P, el, ax, L, s0 + 0.04, s1 - 0.04), F(0.3) - (q - np.outer(q @ ax.astype(F), ax).astype(F)) @ out.astype(F) /
                              np.maximum(np.linalg.norm(q - np.outer(q @ ax.astype(F), ax).astype(F), axis=1), F(1e-6)))
        fd.paint(Func(panel, lo, hi), 0)
    # pistons along its back (the outer-lower side)
    back = norm(out * 0.55 - top * 0.85)
    for k in (-1, 1):
        side_v = norm(np.cross(ax, back))
        p0 = _fa_spot("R", 0.32, norm(back + side_v * (k * 0.35)), 0.05) + back * 0.006
        p1 = p0 + ax * (L * 0.5)
        fd.add(RoundCone(p0, p0 + ax * (L * 0.26), 0.013, 0.013), 0.004, 5)
        fd.add(RoundCone(p0 + ax * (L * 0.24), p1, 0.007, 0.007), 0.002, 7)
        fd.add(Cylinder(p1, 0.011, 0.014, rr=0.004, R=rot_from_axes(z_axis=ax)), 0.002, 5)
    # the power cell on its top
    cp = _fa_spot("R", 0.45, top, 0.05)
    Rt = np.stack([norm(np.cross(top, ax)), ax, top], 1)
    fd.add(RoundBox(cp + top * 0.008, (0.024, L * 0.17, 0.013), 0.007, R=Rt), 0.004, 5)
    for k in range(3):
        fd.sub(RoundBox(cp + top * 0.021 + ax * (L * (-0.09 + 0.09 * k)), (0.014, 0.006, 0.004), 0.002, R=Rt), 0.002)
    return fd


def cells_field():
    """The power cell's three glowing slits."""
    fd = Field("Cells")
    el, ax, out, top, L = forearm_frame("R")
    cp = _fa_spot("R", 0.45, top, 0.05)
    Rt = np.stack([norm(np.cross(top, ax)), ax, top], 1)
    for k in range(3):
        fd.add(RoundBox(cp + top * 0.017 + ax * (L * (-0.09 + 0.09 * k)), (0.0125, 0.0048, 0.004), 0.002, R=Rt), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the seismic plate (hand.R)
PLATE_F = 0.212                          # its middle this far out along the hand (wrist -> knuckles)
PLATE_N = 0.018                          # and toward the palm
PLATE_HALF = (0.078, 0.068, 0.022)       # (thumb axis, palm axis, out along the hand)


def plate_axes():
    wr, f, n, t = hand_frame("R")
    return wr, f, n, t, np.stack([t, n, f], 1)


def plate_face():
    """The middle of the plate's face (rest pose): where the shockwave leaves the ground."""
    wr, f, n, t, R = plate_axes()
    return wr + f * (PLATE_F + PLATE_HALF[2]) + n * PLATE_N


def plate_field():
    """fieldgun material: the gunmetal housing (5) over the back of his fist, struts down its sides to the plate: a thick
    gunmetal plate before his knuckles, a tan band (0) round its rim, its face black (8) with a grille of rings round the
    emitter (which glows: Emitter)."""
    fd = Field("Plate")
    wr, f, n, t, R = plate_axes()
    pc = wr + f * PLATE_F + n * PLATE_N
    fd.add(RoundBox(wr + f * 0.1 - n * 0.046, (0.066, 0.02, 0.085), 0.014, R=R), 0.0, 5)               # the housing
    fd.add(RoundBox(wr + f * 0.03 - n * 0.04, (0.058, 0.016, 0.03), 0.012, R=R), 0.008, 8)             # its padded heel
    for k in (-1, 1):
        fd.add(RoundBox(wr + f * 0.16 + t * (k * 0.072) + n * 0.005, (0.008, 0.045, 0.05), 0.006, R=R), 0.006, 5)   # struts
    fd.add(RoundBox(pc, PLATE_HALF, 0.016, R=R), 0.006, 5)
    fd.add(Inter(RoundBox(pc, (PLATE_HALF[0] + 0.004, PLATE_HALF[1] + 0.004, 0.009), 0.008, R=R),
                 Func(lambda P: -RoundBox(pc, (PLATE_HALF[0] - 0.01, PLATE_HALF[1] - 0.01, 0.05), 0.012, R=R)(P), pc - 0.2, pc + 0.2), 0.002), 0.004, 0)
    face = pc + f * PLATE_HALF[2]
    fd.paint(Func(lambda P: ((P - face.astype(F)) @ f.astype(F)) * F(-1) - F(0.004), pc - 0.2, pc + 0.2), 8)
    for r in (0.054, 0.062):                                                              # the grille's rings
        fd.sub(Torus(face, r, 0.0024, R=rot_from_axes(z_axis=f)), 0.001)
    fd.sub(Cylinder(face, 0.046, 0.008, rr=0.002, R=rot_from_axes(z_axis=f)), 0.002)    # (the emitter sits in it)
    fd.add(Cylinder(face - f * 0.002, 0.016, 0.006, rr=0.003, R=rot_from_axes(z_axis=f)), 0.002, 7)   # its steel hub
    for k in range(4):                                                                    # bolts at the corners
        a = math.pi / 4 + k * math.pi / 2
        fd.add(Sphere(face + t * (math.cos(a) * 0.084) + n * (math.sin(a) * 0.074) - f * 0.002, 0.006), 0.002, 7)
    return fd


def emitter_field():
    """The glowing emitter ring in the plate's face."""
    fd = Field("Emitter")
    wr, f, n, t, R = plate_axes()
    face = wr + f * (PLATE_F + PLATE_HALF[2]) + n * PLATE_N
    fd.add(Torus(face - f * 0.004, 0.034, 0.008, R=rot_from_axes(z_axis=f)), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the tablet (forearm.L)
TAB_S = 0.56                             # its middle this far down the forearm
TAB_HALF = (0.088, 0.06, 0.011)          # (along the forearm, across, thickness)


def tablet_frame():
    el, ax, out, top, L = forearm_frame("L")
    base = _fa_spot("L", TAB_S, out, 0.0)
    across = norm(np.cross(out, ax))
    c = base + out * (0.012 + 0.008 + TAB_HALF[2])
    return c, np.stack([ax, across, out], 1)


def tablet_field():
    """fieldgun material: a rugged tablet (black, 8) with thick rubber corners, a gunmetal mount plate under it (5), two
    tan straps round his forearm (0); the screen sits in its face (Screen)."""
    fd = Field("Tablet")
    el, ax, out, top, L = forearm_frame("L")
    c, R = tablet_frame()
    u, v, w = R[:, 0], R[:, 1], R[:, 2]
    fd.add(RoundBox(c, TAB_HALF, 0.007, R=R), 0.0, 8)
    fd.sub(RoundBox(c + w * (TAB_HALF[2] + 0.001), (TAB_HALF[0] - 0.012, TAB_HALF[1] - 0.012, 0.003), 0.003, R=R), 0.001)
    for a in (-1, 1):
        for b in (-1, 1):
            fd.add(RoundBox(c + u * (a * (TAB_HALF[0] - 0.008)) + v * (b * (TAB_HALF[1] - 0.008)), (0.016, 0.016, TAB_HALF[2] + 0.004), 0.008, R=R), 0.004, 8)
    fd.add(Cylinder(c + u * (TAB_HALF[0] - 0.004) + w * 0.0, 0.006, 0.01, rr=0.002, R=rot_from_axes(z_axis=v)), 0.002, 5)
    fd.add(RoundBox(c - w * (TAB_HALF[2] + 0.006), (TAB_HALF[0] * 0.8, TAB_HALF[1] * 0.7, 0.006), 0.004, R=R), 0.004, 5)
    f = forearm_hull("L")
    lo, hi = np.minimum(el, J["wrist_L"]) - 0.2, np.maximum(el, J["wrist_L"]) + 0.2
    for s0 in (TAB_S - 0.17, TAB_S + 0.15):
        fd.add(Inter(Shell(f, 0.012, 0.01, pad=0.06), Func(lambda P, s0=s0: _fa_band(P, el, ax, L, s0 - 0.04, s0 + 0.04), lo, hi), 0.003), 0.006, 0)
    return fd


def screen_field():
    fd = Field("Screen")
    c, R = tablet_frame()
    fd.add(RoundBox(c + R[:, 2] * (TAB_HALF[2] - 0.0005), (TAB_HALF[0] - 0.013, TAB_HALF[1] - 0.013, 0.0025), 0.002, R=R), 0.0)
    return fd


# ======================================================================================= the EMP grenade (free bone)
GREN_HEAD = 0.118                        # the canister's middle this far along the grip from the fist's middle
GREN_R, GREN_H = 0.05, 0.078


def grenade_frame():
    """Rest pose: (G: the grip's middle in his right fist, A: along the grip toward the canister (the thumb axis), C: the
    canister's middle)."""
    wr, f, n, t = hand_frame("R")
    G = fist_center("R")
    A = norm(t)
    return G, A, G + A * GREN_HEAD


def grenade_field():
    """fieldgun material: a black ribbed grip (8), the gunmetal canister (5) with black end caps (8) and ribs, a steel pin
    ring (7) on its top; the blue band round its middle glows (Core)."""
    fd = Field("Grenade")
    G, A, C = grenade_frame()
    Ra = rot_from_axes(z_axis=A)
    fd.add(RoundCone(G - A * 0.055, G + A * 0.07, 0.017, 0.018), 0.0, 8)
    for k in range(4):
        fd.add(Torus(G + A * (-0.04 + 0.026 * k), 0.018, 0.0028, R=Ra), 0.002, 8)
    fd.add(Cylinder(C, GREN_R, GREN_H, rr=0.016, R=Ra), 0.006, 5)
    for s in (-1, 1):
        fd.add(Cylinder(C + A * (s * (GREN_H * 0.5 - 0.004)), GREN_R - 0.006, 0.018, rr=0.007, R=Ra), 0.004, 8)
    side = norm(np.cross(A, v3((1, 0, 0))))
    side2 = np.cross(A, side)
    for k in range(6):
        a = 2 * math.pi * k / 6
        d = side * math.cos(a) + side2 * math.sin(a)
        fd.add(RoundBox(C + d * (GREN_R - 0.002), (0.006, 0.006, GREN_H * 0.4), 0.003, R=rot_from_axes(z_axis=A, x_axis=d)), 0.003, 8)
    fd.sub(Torus(C, GREN_R + 0.002, 0.008, R=Ra), 0.003)                               # (the band glows in it)
    top = C + A * (GREN_H * 0.5 + 0.008)
    fd.add(Cylinder(top, 0.012, 0.012, rr=0.004, R=Ra), 0.003, 7)
    fd.add(Torus(top + A * 0.006 + side * 0.022, 0.013, 0.0028, R=rot_from_axes(z_axis=side2)), 0.002, 7)
    return fd


def core_field():
    fd = Field("Core")
    G, A, C = grenade_frame()
    fd.add(Torus(C, GREN_R - 0.002, 0.0085, R=rot_from_axes(z_axis=A)), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.235, 1.63)), 0.04, 0.45)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.085, -0.15, 1.6)), 0.055, 0.55), (hp((sx * 0.157, 0.035, 1.66)), 0.045, 0.5),
                (J["elbow_" + ("R" if sx < 0 else "L")] + v3((0, 0.022, 0)), 0.05, 0.2)]
    return pts


# ======================================================================================= build config
GLB_NAME = "ken"
ROOT_NAME = "HeroKenHQ"
TEX_PREFIX = "hero"
MAT_NAME = "KenMat"
MESH_NAME = "Ken"
BASE_MODULE = "ken_base"
ANIM_MODULE = "anim_ken"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Cap", "Headgear", "Shirt", "Vest", "Kit", "Tools", "Trousers", "Boots",
         "Gauntlet", "Cells", "Plate", "Emitter", "Tablet", "Screen", "Grenade", "Core"]
REGION_PARTS = ("Skin", "Cap", "Headgear", "Shirt", "Vest", "Kit", "Tools", "Trousers", "Boots", "Gauntlet", "Plate", "Tablet",
                "Grenade")
HAIR = {"name": "HQ_KenHair", "base": (0.06, 0.055, 0.055), "hi": (0.26, 0.25, 0.26), "low": (0.025, 0.022, 0.024),
        "streak": (0.045, 0.04, 0.042), "tint": (0.1, 0.09, 0.1)}
CLOTH = dict(brass=GUNMETAL, black=BLACK)
GEAR = dict(grey=GUNMETAL, red=BLUE, white=WHITE)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_KenSkin", "base": (0.87, 0.67, 0.52), "ruddy": (0.88, 0.55, 0.44), "lips": (0.72, 0.42, 0.38),
                      "brow": ((0.04, 0.035, 0.035), (0.15, 0.13, 0.13)),
                      "extra": ((LASH, (0.04, 0.03, 0.03), 0.5), (GLOVE, BLACK, 0.75))}),
    "Hair": ("hair", HAIR),
    "Cap": ("uniform", dict(CLOTH, name="HQ_KenCap", base=TAN, facing=TAN_DARK, buff=TAN_DARK)),
    "Headgear": ("fieldgun", dict(GEAR, name="HQ_KenHeadset", olive=OLIVE)),
    "Shirt": ("uniform", dict(CLOTH, name="HQ_KenShirt", base=OLIVE, facing=RED, buff=WHITE)),
    "Vest": ("uniform", dict(CLOTH, name="HQ_KenVest", base=TAN, facing=TAN_DARK, buff=TAN_DARK)),
    "Kit": ("uniform", dict(CLOTH, name="HQ_KenKit", base=TAN, facing=TAN_DARK, buff=TAN_DARK)),
    "Tools": ("fieldgun", dict(GEAR, name="HQ_KenTools", olive=YELLOW)),
    "Trousers": ("uniform", dict(CLOTH, name="HQ_KenTrousers", base=OLIVE, facing=OLIVE, buff=OLIVE)),
    "Boots": ("leather_dyed", {"name": "HQ_KenBoots", "base": (0.075, 0.07, 0.07), "dyed": (0.035, 0.033, 0.033), "worn_c": (0.3, 0.29, 0.29)}),
    "Gauntlet": ("fieldgun", dict(GEAR, name="HQ_KenGauntlet", olive=TAN)),
    "Plate": ("fieldgun", dict(GEAR, name="HQ_KenGauntlet", olive=TAN)),
    "Tablet": ("fieldgun", dict(GEAR, name="HQ_KenTablet", olive=TAN)),
    "Grenade": ("fieldgun", dict(GEAR, name="HQ_KenGrenade", olive=TAN)),
}
GLOW = {"Cells": (BLUE, 1.0, 0.5), "Emitter": (BLUE, 1.1, 0.5), "Screen": (SCREEN, 0.9, 0.5), "Core": (BLUE, 1.2, 0.5)}
LOW_TARGETS = {"Skin": 5600, "Teeth": 90, "Hair": 700, "Cap": 900, "Headgear": 1000, "Shirt": 2300, "Vest": 1900, "Kit": 2200,
               "Tools": 1300, "Trousers": 1900, "Boots": 1100, "Gauntlet": 1600, "Cells": 60, "Plate": 1000, "Emitter": 140,
               "Tablet": 600, "Screen": 40, "Grenade": 600, "Core": 120}
AO_EXCLUDE = ["Grenade", "Headgear", "Tools"]
BAKE_APART = (["Grenade"], (3.0, 0.0, 0.0))     # (the grenade's rest is in his fist, inside the gauntlet's housing)


def prop_bones():
    """The grenade rides a free bone (posed in the world by the Ability; hidden otherwise), its glowing band a child of it
    (it swells when armed); the seismic plate a child of his right hand (its tail = the middle of the plate's face)."""
    G, A, C = grenade_frame()
    wr, f, n, t, R = plate_axes()
    pf = plate_face()
    return [("grenade", C, C + A * 0.08, None),
            ("core", C, C + A * 0.05, "grenade"),
            ("plate", pf - f * 0.06, pf, "hand.R")]


SHIRT_BONES = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
VEST_BONES = TORSO | {"clavicle.R", "clavicle.L"}


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Cap": ("rigid", "head"),
        "Headgear": ("rigid", "head"),
        "Shirt": ("transfer", SHIRT_BONES, None),
        "Vest": ("transfer", VEST_BONES, None),
        "Kit": ("transfer", VEST_BONES | {"thigh.R", "thigh.L"}, {"thigh.R": 0.25, "thigh.L": 0.25}),
        "Tools": ("transfer", VEST_BONES | {"thigh.R", "thigh.L"}, {"thigh.R": 0.25, "thigh.L": 0.25}),
        "Trousers": ("transfer", TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gauntlet": ("rigid", "forearm.R"), "Cells": ("rigid", "forearm.R"),
        "Plate": ("rigid", "plate"), "Emitter": ("rigid", "plate"),
        "Tablet": ("rigid", "forearm.L"), "Screen": ("rigid", "forearm.L"),
        "Grenade": ("rigid", "grenade"), "Core": ("rigid", "core"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Headgear", "Plate", "Tablet", "Grenade"):
        return 1.2
    if part in ("Tools", "Boots"):
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Cap", cap_field(), 0.0022 if fine else 0.0032),
        ("Headgear", headgear_field(), 0.0014 if fine else 0.002),
        ("Shirt", shirt_field(), 0.0026 if fine else 0.0036),
        ("Vest", vest_field(), 0.0026 if fine else 0.0036),
        ("Kit", kit_field(), 0.0018 if fine else 0.0026),
        ("Tools", tools_field(), 0.0014 if fine else 0.002),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Gauntlet", gauntlet_field(), 0.0018 if fine else 0.0026),
        ("Cells", cells_field(), 0.0012),
        ("Plate", plate_field(), 0.0016 if fine else 0.0024),
        ("Emitter", emitter_field(), 0.0014),
        ("Tablet", tablet_field(), 0.0014 if fine else 0.002),
        ("Screen", screen_field(), 0.0012),
        ("Grenade", grenade_field(), 0.0014 if fine else 0.002),
        ("Core", core_field(), 0.0014),
    ]
