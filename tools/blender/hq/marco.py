"""Marco the Grenadier, Bomb Thrower (HQ hero, Gunpowder Age). Rest pose = A-pose, facing -Y, feet at z = 0; right
side = -X.

A big, strong grenadier in his late twenties, all swagger and good humour: a broad face, rosy cheeks bunched up by a
wide grin (his teeth showing), a big black moustache waxed out into a curl at each end, thick black brows (the left one
cocked), a strong jaw with a dimpled chin, a soot smudge on his right cheek; short black hair under his cap, tied at the
nape in a short queue with a black ribbon. A tall grenadier's mitre cap: a stiff crimson front embroidered in gold (a
border and a flaming grenade), a crimson bag behind it, a gold-edged headband, a gold tassel on top. The Gunpowder
army's coat: crimson, open down the front over a buff waistcoat, gold-ochre lapels with brass buttons and gold lace
loops beside them, wide gold cuffs, the skirts turned back to show their gold lining; a black leather stock at his
throat. A white cross-belt over his left shoulder to a black grenade pouch on his right hip (a brass flaming-grenade badge
on its flap), a brass match case on the belt across his chest with the slow match smouldering in it; a white waist belt
over the waistcoat; a short curved hanger at his left hip in a black scabbard (brass hilt and fittings); off-white
breeches, black gaiters buttoned to above the knee, black buckled shoes.

His grenade: a round black iron ball the size of a big orange with a wooden fuse plug and a short fuse that fizzes with
sparks once lit (the sparks ship as their own glowing mesh on the `spark` bone, shown only while it is lit). It rides the
`grenade` bone, a free bone the clips keep in his cupped right hand (and toss in the air: Idle); its scale hides it from
the throw until he draws the next one from his pouch. His small powder keg stands on the flagstones at his right front
(the free `keg` bone; its own sparks on `keg_spark`); his cap rides the free `cap` bone, which the clips keep on his head
(his left hand raises it in the Cheer).

His body is the smith's (tarek.py: big and broad), with his own head and hands (the right hand cupped round the
grenade, the left half open)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import tarek as tk
from tarek import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, foot,
                   torso_prims, traps, neck_prim, deltoid, upper_arm, _forearm, TORSO, TORSO_Z, torso_bones)

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, STUBBLE, SOOT = 0, 1, 2, 3, 4, 5, 8, 9, 10

CRIMSON = (0.55, 0.08, 0.08)          # the Gunpowder army's coats
GOLD = (0.85, 0.62, 0.2)              # facings, lace and trim
LACE = (0.92, 0.72, 0.3)
BUFF = (0.8, 0.64, 0.42)
LINEN = (0.9, 0.87, 0.79)
WHITE = (0.93, 0.92, 0.88)
BLACK = (0.075, 0.068, 0.066)


# ======================================================================================= hands & the grenade
HAND_S = 1.07
# the right hand cupped round the grenade: per finger (index .. little) curl angles, fitted to the ball (the fingers lie on
# it); the thumb along its side. The left hand half open.
CUP_CURLS = ((1.15, 0.4, 0.7), (0.9, 0.6, 0.6), (0.9, 0.55, 0.6), (1.2, 0.15, 0.6))
OPEN_CURLS = (0.6, 0.8, 0.6)
GREN_R = 0.052                         # a big orange
FUSE_LEN = 0.034                       # the fuse plug and cord, out of the ball


def _hand_axes(side):
    return hand_frame(side)


def grenade_center():
    """Rest pose: the ball in the right hand's cup (fitted: the fingers and thumb on its surface)."""
    wr, f, n, t = hand_frame("R")
    return wr + f * 0.12 + n * 0.07


def fuse_dir():
    """The fuse points out past the little finger's side of his hand, a little toward the fingertips (rest pose)."""
    wr, f, n, t = hand_frame("R")
    return norm(-t * 0.9 + n * 0.25 + f * 0.25)


def fuse_tip():
    return grenade_center() + fuse_dir() * (GREN_R + FUSE_LEN)


def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    cup = side == "R"
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.064, 0.034, 0.066)) * s, 0.03 * s, R=Rp), 0.028, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.036, 0.03, 0.052)) * s, R=Rp), 0.019, SKIN)
    curl_ax = norm(np.cross(f, n))
    offs = (0.044, 0.0148, -0.0148, -0.044)
    lens = (0.96, 1.02, 0.96, 0.8)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        curls = CUP_CURLS[i] if cup else OPEN_CURLS
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
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.012, (0.012, 0.007, 0.015), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.052 * s + n * 0.011
    if cup:
        d1 = norm(f * 2.0 + t * 0.55 + n * 2.0)
        d2 = norm(-t * 0.3 + n * 1.4)
    else:
        d1 = norm(f * 0.55 + t * 0.7 + n * 0.3)
        d2 = norm(f * 0.6 + t * 0.35 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.026 * s, 0.023 * s, 0.02 * s], k=0.008), 0.018, SKIN)


# ======================================================================================= head
def stubble_mask(P):
    """Jaw and chin (design coordinates): a faint shadow of stubble (he shaves; the moustache is his pride)."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.56) + F(0.05) * smoothstep(0.08, 0.16, ax)
    return np.maximum(np.maximum(z - top, F(1.44) - z), y - F(0.02))


def head(fd):
    """A broad, good-humoured face: a strong square jaw and a dimpled chin, round cheeks bunched up by his grin, thick
    black brows (the left cocked), eyes crinkled with laughter, a strong straight nose with a round tip, a wide grin with
    his teeth showing, a soot smudge on his right cheek."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.05, 1.588), (0.156, 0.14, 0.13)), 0.07, SKIN)                          # a broad, strong jaw
    fd.add(E((0, -0.138, 1.498), (0.094, 0.072, 0.07)), 0.05, SKIN)                         # a square chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.114, -0.128, 1.636), 0.056), 0.05, SKIN)                            # round cheeks, bunched by the grin
        fd.add(S((sx * 0.134, -0.045, 1.554), 0.055), 0.05, SKIN)                            # the jaw's corners
        pts = [hp((sx * 0.156, -0.055, 1.744)), hp((sx * 0.118, -0.134, 1.756)), hp((sx * 0.062, -0.176, 1.754)), hp((0.0, -0.186, 1.75))]
        fd.add(Chain(pts, [hr(0.012), hr(0.02), hr(0.023), hr(0.021)], k=hr(0.022)), hr(0.03), SKIN)     # the brow ridge
    fd.sub(RoundCone(hp((0, -0.21, 1.514)), hp((0, -0.2, 1.47)), hr(0.0048), hr(0.0062)), hr(0.008))      # the dimple in his chin
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # thick black brows, raised in good humour, the left one cocked higher
    tuft = lambda P: F(0.0022) * NOISE(P * F(150)) + F(0.001) * np.sin(P[:, 0] * F(380))
    for sx in (-1, 1):
        dz = 0.012 if sx > 0 else 0.0
        pts = [hp((sx * 0.026, -0.211, 1.782 + dz * 0.3)), hp((sx * 0.068, -0.206, 1.799 + dz)), hp((sx * 0.114, -0.184, 1.8 + dz)),
               hp((sx * 0.157, -0.145, 1.779 + dz * 0.5))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.012), hr(0.015), hr(0.013), hr(0.006)], k=hr(0.008),
                     disp=tuft, disp_amp=0.003), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.024), hr(0.027), hr(0.024), hr(0.013)], k=hr(0.01)), BROW)
    # eyes crinkled by his grin (the left, under the cocked brow, a little more open)
    for sx in (-1, 1):
        ec = eye_c(sx)
        top = 0.026 if sx > 0 else 0.023
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(top))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0062)), Plane(ec + v3((0, 0, -hr(0.015))), (sx * -0.16, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(top - 0.003))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(2):                                                                      # laughter lines
            a = hp((sx * (0.11 + 0.004 * k), -0.128 + 0.006 * k, 1.68 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, -0.002 - 0.009 * k)), hr(0.002), hr(0.0014)), hr(0.003))
    # a strong straight nose with a round tip
    fd.add(RoundCone(hp((0, -0.185, 1.724)), hp((0, -0.238, 1.634)), hr(0.019), hr(0.026)), hr(0.017), SKIN)
    fd.add(S((0, -0.239, 1.622), 0.029), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.034, -0.216, 1.606), 0.023), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.018, -0.234, 1.596)), v3((0.0095, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a wide grin, his teeth showing under the moustache; its corners up into his cheeks
    slot = [hp((-0.074, -0.157, 1.576)), hp((-0.043, -0.19, 1.551)), hp((0, -0.2, 1.542)), hp((0.043, -0.19, 1.551)), hp((0.074, -0.157, 1.576))]
    fd.sub(Chain(slot, [hr(0.005), hr(0.011), hr(0.014), hr(0.011), hr(0.005)], k=hr(0.004)), hr(0.004))
    fd.paint(Chain(slot, [hr(0.006), hr(0.0125), hr(0.0155), hr(0.0125), hr(0.006)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.06, -0.164, 1.563), (-0.033, -0.188, 1.534), (0, -0.194, 1.527), (0.033, -0.188, 1.534), (0.06, -0.164, 1.563)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0075), hr(0.0085), hr(0.0075), hr(0.004)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(S((sx * 0.082, -0.15, 1.574), 0.009), hr(0.007), SKIN)                          # the grin's corners in his cheeks
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.028, 0.05, 0.064)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.012, 0.032, 0.042)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
    # a soot smudge on his right cheek (and a fleck by his left brow)
    fd.paint(Ellipsoid(hp((-0.118, -0.152, 1.64)), v3((0.032, 0.02, 0.017)) * HS * 1.5, R=euler(0.2, 0.0, -0.45)), SOOT)
    fd.paint(Ellipsoid(hp((0.13, -0.15, 1.76)), v3((0.014, 0.01, 0.008)) * HS * 1.5, R=euler(0.2, 0.0, 0.5)), SOOT)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        fd.add(upper_arm(side), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.1, 0.104, 0.134), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)
        fd.add(_forearm(side), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.104, 0.094, 0.14), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def leg_prims(side):
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(hip, kn, 0.14, 0.092), 0.065),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.13, 0.12, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.048),
            (Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038),
            (RoundCone(kn, an, 0.088, 0.058), 0.038),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043)]


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
    """His upper teeth, white and even, in the grin."""
    fd = Field("Teeth")
    for k in range(6):
        x = -0.05 + 0.02 * k
        y = -0.181 + 0.014 * (abs(x) / 0.05) ** 2
        fd.add(RoundBox(hp((x, y, 1.554 + 0.006 * (abs(x) / 0.05) ** 2)), v3((0.0092, 0.006, 0.0085)) * HS, hr(0.003)), 0.002)
    return fd


# ======================================================================================= hair, moustache
def skull():
    return Ellipsoid(HEAD_C, HEAD_RAD)


def hair_field():
    """Short black hair combed straight back over his head (flat under the cap), sideburns to mid-ear, tied at the nape
    in a short thick queue bound with a black ribbon tied in a bow."""
    fd = Field("Hair")
    def comb(P):
        Q = hinv(P)
        return F(0.0016) * np.sin(Q[:, 0] * F(300) + F(0.5) * np.sin(Q[:, 1] * F(25))) + F(0.0008) * NOISE(P * np.array([70, 20, 70], F))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        line = F(-0.12) + F(0.05) * smoothstep(0.06, 0.14, ax)                       # the hairline over his brow
        front = np.where(z > F(1.75), line - y, F(-1.0))
        temple = np.where((ax > F(0.12)) & (z < F(1.77)) & (y < F(0.0)), F(-0.06) - y + F(0.4) * (F(1.77) - z), F(-1.0))
        ear = np.where((ax > F(0.15)) & (z < F(1.735)) & (np.abs(y - F(0.035)) < F(0.058)), F(0.02), F(-1.0))   # clear of the ears
        side = np.where((ax > F(0.14)) & (y < F(-0.02)), F(1.6) - z, F(-1.0))         # sideburns to mid-ear
        nape = F(1.585) - z
        return np.maximum(np.maximum(np.maximum(front, temple), np.maximum(ear, side)), nape)
    fd.add(Inter(Shell(skull(), 0.006, 0.014, pad=0.06, disp=comb, disp_amp=0.002), Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.004), 0.0)
    # the queue: gathered at the nape, a short thick tail down the back of his neck
    strands = lambda P: F(0.0018) * np.sin(P[:, 0] * F(320)) + F(0.0012) * NOISE(P * np.array([70, 70, 14], F))
    q = queue_pts()
    fd.add(Lock(q, [0.026, 0.024, 0.02, 0.014, 0.006], [0.02, 0.019, 0.016, 0.012, 0.005], [v3((0, 1, 0.15))] * 5, k=0.008,
                disp=strands, disp_amp=0.003), 0.012)
    # the ribbon's bow at its top
    c = q[0] + norm(q[1] - q[0]) * 0.03 + v3((0, 0.018, 0))
    for sx in (-1, 1):
        fd.add(Ellipsoid(c + v3((sx * 0.024, 0.0, 0.004)), (0.024, 0.008, 0.014), R=euler(0, sx * 0.3, 0)), 0.004, 5)
    fd.add(Sphere(c, 0.011), 0.004, 5)
    return fd


def queue_pts():
    return [hp((0.0, 0.205, 1.6)), hp((0.0, 0.232, 1.55)), hp((0.0, 0.252, 1.5)), hp((0.0, 0.262, 1.46)), hp((0.0, 0.266, 1.43))]


def moustache_pts(sx):
    """One half of the moustache: its sweep out over the upper lip (design units: points, widths, thicknesses), then the
    curl it is waxed into: up and round, back in toward the cheek (a spiral, as points and radii)."""
    sweep = [(sx * 0.004, -0.236, 1.586), (sx * 0.04, -0.227, 1.578), (sx * 0.076, -0.208, 1.578), (sx * 0.106, -0.192, 1.585),
             (sx * 0.124, -0.186, 1.584)]
    widths = [0.017, 0.019, 0.015, 0.01, 0.0075]
    thicks = [0.012, 0.013, 0.011, 0.008, 0.007]
    cc = v3((sx * 0.13, -0.19, 1.606))
    e_out = norm(v3((sx * 0.894, 0.447, 0.0)))
    e_up = v3((0, 0, 1))
    curl, rads = [], []
    for k in range(15):
        u = k / 14.0
        ph = math.radians(-90 + 400 * u)
        R = 0.024 * (1 - 0.62 * u)
        curl.append(cc + e_out * (R * math.cos(ph)) + e_up * (R * math.sin(ph)))
        rads.append(0.0065 * (1 - 0.55 * u))
    return sweep, widths, thicks, curl, rads


def moustache_field():
    """A big black moustache, full over his upper lip and swept out along his cheeks, its ends waxed into tight curls."""
    fd = Field("Moustache")
    strands = lambda P: F(0.0016) * NOISE(P * np.array([30, 90, 90], F)) + F(0.001) * np.sin(P[:, 2] * F(420))
    for sx in (-1, 1):
        sweep, widths, thicks, curl, rads = moustache_pts(sx)
        pts = [hp(p) for p in sweep]
        nrm = [norm(v3((sx * 0.25 * k / 4, -1.0, 0.25))) for k in range(5)]
        fd.add(Lock(pts, [hr(w) for w in widths], [hr(t) for t in thicks], nrm, k=hr(0.006), disp=strands, disp_amp=0.003), hr(0.006))
        cp = [hp(p) for p in curl]
        fd.add(Chain([pts[-1]] + cp, [hr(0.0072)] + [hr(r) for r in rads], k=hr(0.003)), hr(0.004))
    return fd


# ======================================================================================= the mitre cap
BAND_F = v3((0.0, -0.175, 1.86))       # the headband's plane (design units): across his brow, well above his eyebrows,
BAND_B = v3((0.0, 0.215, 1.67))        # lower behind, at the nape; over his ears at the sides
_BAND_N = norm(v3((0, -(BAND_B[2] - BAND_F[2]) / (BAND_B[1] - BAND_F[1]), 1.0)))
BAND_H = 0.026                         # the band's half height (design units)
PLATE_TILT = math.radians(9.0)         # the stiff front leans back a little (it faces the camera above)
PLATE_O = hp((0.0, -0.17, 1.835))      # the front's foot, on the band
PLATE_H = 0.36                         # (world units from here on)
PLATE_R1, PLATE_V1 = 0.215, 0.065      # its outline: a broad round foot ...
PLATE_R2 = 0.07                        # ... tapering to a round top
PLATE_T = 0.016
PLATE_RC = 0.36                        # curved round an upright axis behind it (following his brow)
CAP_IN = 0.032                         # the cap's inside: this far out from his skull (the hair lies under it)


def band_d(P):
    """Height above the headband's middle plane (design units)."""
    return (hinv(P) - BAND_F.astype(F)) @ _BAND_N.astype(F)


def plate_axes():
    V = v3((0.0, math.sin(PLATE_TILT), math.cos(PLATE_TILT)))
    W = v3((0.0, -math.cos(PLATE_TILT), math.sin(PLATE_TILT)))
    U = v3((1.0, 0.0, 0.0))
    return PLATE_O, U, V, W


def _plate_uvw(P):
    O, U, V, W = plate_axes()
    q = P - O.astype(F)
    return q @ U.astype(F), q @ V.astype(F), q @ W.astype(F)


def _plate_surf(u):
    """The front's middle surface (w) at u: curved back toward its sides."""
    return -(F(PLATE_RC) - np.sqrt(np.maximum(F(PLATE_RC * PLATE_RC) - u * u, F(1e-6))))


def plate_outline(u, v):
    """2D distance to the front's outline (< 0 inside): an uneven capsule from a broad round foot to a round top, cut flat
    at its foot (v = 0)."""
    h = F(PLATE_H - PLATE_R2 - PLATE_V1)
    r1, r2 = F(PLATE_R1), F(PLATE_R2)
    x = np.abs(u)
    y = v - F(PLATE_V1)
    b = (r1 - r2) / h
    a = np.sqrt(F(1) - b * b)
    k = -b * x + a * y
    d = np.where(k < 0, np.sqrt(x * x + y * y) - r1,
                 np.where(k > a * h, np.sqrt(x * x + (y - h) ** 2) - r2, a * x + b * y - r1))
    return np.maximum(d, -v)


def _capsule2(u, v, a, b, ra, rb):
    """2D distance to a capsule from point a (radius ra) to b (radius rb), approximately."""
    pa = np.stack([u - F(a[0]), v - F(a[1])], 1)
    ba = np.array([b[0] - a[0], b[1] - a[1]], F)
    t = np.clip((pa @ ba) / F(ba @ ba), 0, 1)
    d = np.sqrt(((pa - t[:, None] * ba) ** 2).sum(1))
    return d - (F(ra) + (F(rb) - F(ra)) * t)


def badge_2d(u, v, c, s):
    """A flaming grenade (2D, < 0 inside): a ball with a fuse, three flames rising from it; centred at c, scale s."""
    x, y = (u - F(c[0])) / F(s), (v - F(c[1])) / F(s)
    ball = np.sqrt(x * x + (y + F(0.2)) ** 2) - F(0.32)
    neck = np.maximum(np.abs(x) - F(0.09), np.abs(y - F(0.15)) - F(0.06))
    flames = _capsule2(x, y, (0.0, 0.2), (0.02, 0.86), 0.17, 0.0)
    for sg in (-1, 1):
        flames = np.minimum(flames, _capsule2(x, y, (sg * 0.1, 0.18), (sg * 0.36, 0.64), 0.12, 0.0))
        flames = np.minimum(flames, _capsule2(x, y, (sg * 0.2, 0.12), (sg * 0.55, 0.36), 0.08, 0.0))
    ring = np.abs(np.sqrt(x * x + (y + F(0.2)) ** 2) - F(0.2)) - F(0.025)        # a ring embroidered on the ball
    d = np.minimum(np.minimum(np.maximum(ball, -ring), neck), flames)
    return d * F(s)


BADGE_C = (0.0, 0.14)
BADGE_S = 0.15


def cap_field():
    """The mitre cap: a stiff crimson front (label 0) with a gold embroidered border (5) and a gold flaming grenade (6), a
    crimson bag behind it resting on his head, a headband with gold edges (5), a gold tassel on top (6)."""
    fd = Field("Cap")
    O, U, V, W = plate_axes()
    lo, hi = HEAD_C + v3((-0.27, -0.26, -0.09)), HEAD_C + v3((0.27, 0.31, 0.5))
    skull_f = skull()
    cloth = lambda P: F(0.0012) * NOISE(P * F(30))
    def front(P):
        u, v, w = _plate_uvw(P)
        return np.maximum(plate_outline(u, v), np.abs(w - _plate_surf(u)) - F(PLATE_T / 2))
    def wedge(P):
        """The bag: behind the front, its back sloping from the band at his nape up to the front's top."""
        u, v, w = _plate_uvw(P)
        back = F(-0.45) + (v + F(0.07)) * F(1.06)
        side = plate_outline(u, v) + F(0.012)
        return smax(smax(side, back - w, 0.03), w - (_plate_surf(u) - F(PLATE_T * 0.4)), 0.006)
    def crown(P):
        return skull_f(P) - F(CAP_IN + 0.016)
    def body(P):
        b = smin(smin(wedge(P), crown(P), F(0.03)), front(P), F(0.004))
        b = np.maximum(b, -(skull_f(P) - F(CAP_IN)))                                      # its inside, over his head
        return np.maximum(b, -band_d(P) * F(HS) - F(BAND_H * HS))                         # its foot = the band's foot
    fd.add(Func(body, lo, hi, disp=cloth, disp_amp=0.0015), 0.0)
    # the headband: a band round its foot, proud of the bag
    def band(P):
        d = skull_f(P)
        return np.maximum(np.abs(d - F(CAP_IN + 0.022)) - F(0.008), np.abs(band_d(P)) - F(BAND_H))
    fd.add(Inter(Func(band, lo, hi), Func(lambda P: -(skull_f(P) - F(CAP_IN)), lo, hi), 0.002), 0.004)
    # the tassel: a gold knob on the front's top, its threads hanging down behind
    tq = O + V * (PLATE_H - 0.012) - W * 0.03
    fd.add(Sphere(tq, 0.022), 0.006, 6)
    rs = np.random.RandomState(3)
    for k in range(6):
        a = -0.9 + 1.8 * k / 5
        d = norm(-W * 0.55 - V * 1.0 + U * (a * 0.35))
        p0 = tq + d * 0.012
        fd.add(Chain([p0, p0 + d * 0.035 + U * a * 0.006, p0 + d * 0.07 + U * a * 0.012 + rs.uniform(-0.004, 0.004, 3)],
                     [0.006, 0.005, 0.0035], k=0.003), 0.004, 6)
    # embroidery on the front's face only: a gold border round its edge, the flaming grenade in the middle
    def on_face(P):
        u, v, w = _plate_uvw(P)
        return _plate_surf(u) - F(0.002) - w                                              # < 0 on the front half
    def border(P):
        u, v, w = _plate_uvw(P)
        o = plate_outline(u, v)
        return np.maximum(np.maximum(-o - F(0.022), o - F(0.004)), on_face(P))
    fd.paint(Func(border, lo, hi), 5)
    def badge(P):
        u, v, w = _plate_uvw(P)
        return np.maximum(badge_2d(u, v, BADGE_C, BADGE_S), on_face(P))
    fd.paint(Func(badge, lo, hi), 6)
    def band_edges(P):
        d = skull_f(P)
        b = np.abs(band_d(P))
        return np.maximum(np.maximum(F(BAND_H - 0.009) - b, b - F(BAND_H + 0.004)), F(CAP_IN + 0.01) - d)
    fd.paint(Func(band_edges, lo, hi), 5)
    return fd


def cap_root():
    """The cap bone's head: the middle of its foot, inside it (on his head)."""
    return hp((0.0, 0.03, 1.79))


# ======================================================================================= the clothes' bodies
def torso_hull():
    """His torso as the clothes lie on it: the chest smoothed over (no pectorals), the shoulders' tops (traps), and a cone
    round his hips and the tops of his thighs."""
    b = Field("TorsoHull")
    tp = torso_prims()
    for i, (p, k) in enumerate(tp):
        if i in (2, 3):
            continue
        b.add(p, k)
    b.add(Ellipsoid((0, -0.06, 1.26), (0.28, 0.17, 0.2)), 0.06)
    b.add(traps(), 0.06)
    b.add(RoundCone((0, 0.035, 0.98), (0, 0.035, 0.6), 0.26, 0.335), 0.08)
    return b


NECK_A = v3((0.0, 0.065, 1.34))
NECK_B = v3(hp((0.0, 0.02, 1.575)))


def neck_dist(P):
    """Distance from the neck's axis (extended up past his chin)."""
    ax = norm(NECK_B - NECK_A)
    q = P - NECK_A.astype(F)
    t = q @ ax.astype(F)
    c = q - t[:, None] * ax.astype(F)
    return np.sqrt((c * c).sum(1))


def neck_open(P, r=0.14):
    """> 0 inside the opening round his neck (the cut follows the neck, never the level of his shoulders)."""
    return np.where(P[:, 2] > F(1.33), F(r) - neck_dist(P), F(-1.0))


# offsets (from torso_hull's surface) of the layers over his torso
WC_OFF, WC_T = 0.024, 0.012           # the waistcoat
WB_OFF, WB_T = 0.037, 0.01            # the waist belt (under the coat)
COAT_IN = 0.024                       # the coat's own body: the torso inflated over the waistcoat ...
COAT_OFF, COAT_T = 0.03, 0.016        # ... and the coat shell on it (sleeves: this far off the arm)
COAT_HEM = 0.46
YC = 0.05                             # the axis the coat's front opening is measured round


def coat_angle(P):
    """Angle round his body from straight ahead (0) to straight behind (+-pi)."""
    return np.arctan2(P[:, 0], -(P[:, 1] - F(YC)))


def coat_open(z):
    """Half the angle of the coat's open front at height z: narrow over his chest (the lapels nearly meet), swept back
    below the waist where the skirts are turned back."""
    return F(0.27) + F(0.78) * smoothstep(0.97, 0.47, z)


def lapel_w(z):
    return F(0.27) * (F(1.0) - smoothstep(1.0, 0.94, z))           # (radians, beside the opening)


def turnback_w(z):
    return F(0.42) * smoothstep(0.95, 0.5, z)


def coat_hull(arms=True, skirt=True):
    th = torso_hull()
    b = Field("CoatHull")
    b.add(Func(lambda P: th.eval(P, margin=0.06) - F(COAT_IN), (-0.6, -0.5, 0.5), (0.6, 0.6, 1.62)), 0.0)
    if skirt:
        b.add(RoundCone((0, 0.05, 0.98), (0, 0.085, 0.4), 0.3, 0.385), 0.08)
    if arms:
        for side in ("R", "L"):
            sx = -1 if side == "R" else 1
            sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
            b.add(deltoid(side), 0.055)
            b.add(upper_arm(side), 0.05)
            b.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.1, 0.104, 0.134), R=rot_from_axes(z_axis=el - sh)), 0.04)
            b.add(_forearm(side), 0.035)
            b.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.104, 0.094, 0.14), R=rot_from_axes(z_axis=wr - el)), 0.04)
            b.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028)
    return b


def _sleeve_end(P):
    """> 0 past the sleeves' ends at his wrists (only near each forearm: the cut serves the sleeve and nothing else)."""
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        q = P - wr.astype(F)
        along = q @ ax.astype(F) + F(0.006)
        off = np.sqrt(np.maximum((q * q).sum(1) - (q @ ax.astype(F)) ** 2, 0))
        out = np.maximum(out, np.where((off < F(0.17)) & (along > F(-0.2)), along, F(-1.0)))
    return out


def coat_keep(P):
    """< 0 on the coat: open down the front, round his neck and at his wrists, its skirts to his knees."""
    z = P[:, 2]
    a = np.abs(coat_angle(P))
    r = np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F(YC)) ** 2)
    torso = np.abs(P[:, 0]) < F(0.36)
    front = np.where(torso & (z < F(1.52)), (coat_open(z) - a) * np.maximum(r, F(0.15)), F(-1.0))
    hem = F(COAT_HEM) + F(0.008) * NOISE(P * F(7)) - z
    return np.maximum(np.maximum(front, neck_open(P)), np.maximum(hem, _sleeve_end(P)))


def coat_field():
    """Crimson wool (label 0), gold-ochre facings (6: the lapels, the cuffs, the turned-back skirts' lining), gold lace
    (5: loops beside the lapels, the cuffs' tops)."""
    fd = Field("Coat")
    base = coat_hull()
    folds = lambda P: (F(0.004) * np.sin(coat_angle(P) * F(9) + F(0.6) * NOISE(P * F(3))) * smoothstep(0.92, 0.6, P[:, 2])
                       + F(0.0012) * NOISE(P * F(25)))
    lo, hi = (-1.0, -0.7, 0.35), (1.0, 0.7, 1.7)
    # (the keep box goes first: an intersection takes its bounds from its first shape, and the coat's own are huge)
    fd.add(Inter(Func(coat_keep, (-0.88, -0.47, 0.43), (0.88, 0.56, 1.64)),
                 Shell(base, COAT_OFF, COAT_T, pad=0.1, disp=folds, disp_amp=0.005), 0.004), 0.0)
    # the lapels: a turned-back band down each front edge of his chest, standing a little proud of the coat
    tb = coat_hull(arms=False, skirt=False)
    def lapel(P):
        z = P[:, 2]
        a = np.abs(coat_angle(P))
        r = np.maximum(np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F(YC)) ** 2), F(0.15))
        o = coat_open(z)
        reg = np.maximum((o - a) * r, (a - o - lapel_w(z)) * r)
        return np.maximum(np.maximum(reg, np.maximum(F(0.95) - z, neck_open(P, 0.135))), np.abs(P[:, 0]) - F(0.36))
    fd.add(Inter(Func(lapel, (-0.3, -0.42, 0.92), (0.3, 0.05, 1.56)), Shell(tb, COAT_OFF + 0.011, 0.012, pad=0.1), 0.003), 0.003, 6)
    # the cuffs: wide, a ring round each forearm above the wrist
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        fh = Field("Fore")
        fh.add(_forearm(side), 0.0)
        c0 = wr - ax * 0.078
        fd.add(Inter(Shell(fh, 0.05, 0.016, pad=0.08), Func(lambda P, c0=c0, ax=ax: np.abs((P - c0.astype(F)) @ ax.astype(F)) - F(0.072),
                                                              c0 - 0.25, c0 + 0.25), 0.004), 0.004, 6)
        fd.paint(Inter(Shell(fh, 0.05, 0.03, pad=0.08), Func(lambda P, c0=c0, ax=ax: np.abs((P - c0.astype(F)) @ ax.astype(F) + F(0.066)) - F(0.008),
                                                             c0 - 0.25, c0 + 0.25), 0.0), 5)
        for p, d in cuff_buttons(side):                                                  # three buttons on each cuff
            fd.add(Cylinder(p, 0.0095, 0.007, rr=0.003, R=rot_from_axes(z_axis=d)), 0.003, 5)
    # the turned-back skirts: their lining shows along the front edges below the waist, widening to the hem
    def turnback(P):
        z = P[:, 2]
        a = np.abs(coat_angle(P))
        r = np.maximum(np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F(YC)) ** 2), F(0.15))
        return np.maximum((a - coat_open(z) - turnback_w(z)) * r, z - F(0.95))
    fd.paint(Func(turnback, lo, hi), 6)
    # gold lace loops on the coat beside each lapel, one at each button
    def loops(P):
        z = P[:, 2]
        a = np.abs(coat_angle(P))
        r = np.maximum(np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F(YC)) ** 2), F(0.15))
        o = coat_open(z) + lapel_w(z)
        d = F(1.0)
        for zc in LAPEL_Z:
            d = np.minimum(d, np.maximum(np.abs(z - F(zc)) - F(0.011), np.maximum((o - a) * r, (a - o - F(0.2)) * r)))
        return d
    fd.paint(Func(loops, lo, hi), 5)
    return fd


LAPEL_Z = (1.36, 1.29, 1.22, 1.15, 1.08, 1.01)


def cuff_buttons(side):
    sx = -1 if side == "R" else 1
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    fh = Field("Fore")
    fh.add(_forearm(side), 0.0)
    outer = Func(lambda P: fh.eval(P, margin=0.1) - F(0.058), wr - 0.4, wr + 0.4)
    out = norm(v3((sx * 1.0, 0.0, 0.0)) - ax * (sx * ax[0]))
    pts = []
    for k in range(3):
        c = wr - ax * (0.035 + 0.04 * k)
        h, ok = ray_hit(outer, [c + out * 0.3], [-out], tmax=0.4)
        if ok[0]:
            pts.append((h[0], out))
    return pts


def lapel_buttons():
    """Brass buttons down the middle of each lapel (on the coat's outer surface)."""
    tb = coat_hull(arms=False, skirt=False)
    outer = Func(lambda P: tb.eval(P, margin=0.1) - F(COAT_OFF + 0.0175), (-0.8, -0.8, 0.8), (0.8, 0.8, 1.6))
    pts = []
    for sx in (-1, 1):
        for zc in LAPEL_Z:
            a = float(coat_open(np.array([zc], F))[0] + lapel_w(np.array([zc], F))[0] * 0.5) * sx
            d = v3((math.sin(a), -math.cos(a), 0.0))
            o = v3((0.0, YC, zc)) + d * 0.7
            h, ok = ray_hit(outer, [o], [-d], tmax=0.8)
            if ok[0]:
                pts.append((h[0], d))
    return pts


def waistcoat_field():
    """Buff wool (label 0) from his throat to the tops of his thighs, its front edged in gold lace (5); only its front
    shows (between the coat's open fronts)."""
    fd = Field("Waistcoat")
    th = torso_hull()
    def keep(P):
        z = P[:, 2]
        hem = F(0.665) + F(0.03) * smoothstep(0.0, 0.12, np.abs(P[:, 0])) - z
        return np.maximum(np.maximum(hem, neck_open(P, 0.128)), P[:, 1] - F(0.1))
    lo, hi = (-0.6, -0.6, 0.5), (0.6, 0.3, 1.62)
    fd.add(Inter(Func(keep, (-0.42, -0.4, 0.62), (0.42, 0.13, 1.6)),
                 Shell(th, WC_OFF, WC_T, pad=0.1, disp=lambda P: F(0.001) * NOISE(P * F(30)), disp_amp=0.0015), 0.004), 0.0)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 0]) - F(0.016), P[:, 1]), lo, hi), 5)
    fd.paint(Func(lambda P: np.maximum(P[:, 2] - F(0.69) - F(0.03) * smoothstep(0.0, 0.12, np.abs(P[:, 0])), P[:, 1]), lo, hi), 5)
    return fd


WAISTCOAT_Z = (1.36, 1.29, 1.22, 1.15, 1.08, 1.01, 0.88, 0.81, 0.74)


def waistcoat_buttons():
    th = torso_hull()
    outer = Func(lambda P: th.eval(P, margin=0.1) - F(WC_OFF + WC_T * 0.5 + 0.002), (-0.8, -0.8, 0.5), (0.8, 0.8, 1.6))
    pts = []
    for zc in WAISTCOAT_Z:
        h, ok = ray_hit(outer, [v3((0.026, -0.7, zc))], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            pts.append((h[0], v3((0, -1, 0))))
    return pts


# ======================================================================================= legs: breeches, gaiters, shoes
def legs_hull(top=True):
    b = Field("Legs")
    tp = torso_prims()
    if top:
        b.add(tp[5][0], 0.0)
        b.add(tp[4][0], tp[4][1])
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            b.add(p, k if b.ops else 0.0)
    return b


def breeches_field():
    """Off-white linen breeches from his waist to below his knees (their tops under the waistcoat)."""
    fd = Field("Breeches")
    lh = legs_hull()
    wr = lambda P: F(0.0012) * NOISE(P * np.array([30, 30, 60], F))
    fd.add(Inter(Func(lambda P: np.maximum(F(0.37) - P[:, 2], P[:, 2] - F(1.0)), (-0.38, -0.3, 0.33), (0.38, 0.3, 1.03)),
                 Shell(lh, 0.012, 0.01, pad=0.08, disp=wr, disp_amp=0.002), 0.004), 0.0)
    return fd


def shin_hull(side):
    """The leg as the breeches lie on it (the same shapes: the gaiters stay outside them), and the heel."""
    b = Field("Shin")
    for p, k in leg_prims(side):
        b.add(p, k if b.ops else 0.0)
    an = J["ankle_" + side]
    b.add(Sphere(an + v3((0, 0.042, -0.05)), 0.06 * 1.06), 0.04)
    return b


GAITER_TOP = 0.52


def gaiters_field():
    """Black wool gaiters from his shoes to above his knees, buttoned up the outside, their tops a little flared."""
    fd = Field("Gaiters")
    crease = lambda P: F(0.0016) * NOISE(P * np.array([25, 25, 50], F))
    for side in ("R", "L"):
        sh = shin_hull(side)
        an = J["ankle_" + side]
        blo, bhi = v3((an[0] - 0.17, -0.2, 0.06)), v3((an[0] + 0.17, 0.22, GAITER_TOP + 0.02))
        fd.add(Inter(Func(lambda P: np.maximum(F(0.075) - P[:, 2], P[:, 2] - F(GAITER_TOP)), blo, bhi),
                     Shell(sh, 0.027, 0.012, pad=0.08, disp=crease, disp_amp=0.002), 0.004), 0.0)
        fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(GAITER_TOP - 0.012)) - F(0.012), blo, bhi), Shell(sh, 0.034, 0.01, pad=0.08),
                     0.003), 0.004)
    for p, d in gaiter_buttons():                                                       # buttoned up the outside
        fd.add(Sphere(p, 0.0085), 0.003)
    return fd


def gaiter_buttons():
    pts = []
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh = shin_hull(side)
        outer = Func(lambda P: sh.eval(P, margin=0.1) - F(0.035), J["ankle_" + side] - 0.4, J["knee_" + side] + 0.4)
        kn, an = J["knee_" + side], J["ankle_" + side]
        for k in range(6):
            z = 0.14 + (GAITER_TOP - 0.2) * k / 5
            c = lerp(an, kn, (z - an[2]) / (kn[2] - an[2]))
            d = norm(v3((sx * 1.0, 0.25, 0.0)))
            h, ok = ray_hit(outer, [c + d * 0.4], [-d], tmax=0.5)
            if ok[0]:
                pts.append((h[0], d))
    return pts


def foot_hull(side):
    b = Field("Foot")
    foot(b, side)
    return b


# ======================================================================================= black leather: stock, shoes, pouch, hanger
POUCH_C = v3((-0.392, 0.07, 0.8))      # the grenade pouch at his right hip, on the coat (its face out)
POUCH_N = norm(v3((-1.0, 0.2, 0.0)))
POUCH_HALF = (0.085, 0.064, 0.03)      # half sizes: along his side, up, out
HANG_TOP = v3((0.392, -0.06, 0.94))    # the hanger: its scabbard's mouth at his left hip ...
HANG_TIP = v3((0.43, 0.33, 0.44))      # ... the scabbard's tip behind his left knee (the blade curves back)
HANG_BOW = 0.06


def hanger_curve(n=10, back=0.0):
    """The scabbard's (and the blade's) centre line, curving back toward its tip."""
    d = HANG_TIP - HANG_TOP
    side = norm(np.cross(norm(d), v3((1, 0, 0))))
    if side[1] < 0:
        side = -side
    pts = []
    for k in range(n + 1):
        u = k / n
        pts.append(HANG_TOP + d * u + side * (HANG_BOW * math.sin(math.pi * u * 0.9) * u))
    return pts


def pouch_frame():
    N = POUCH_N
    Up = v3((0, 0, 1))
    S = norm(np.cross(Up, N))
    return POUCH_C, S, Up, N


def shoes_field():
    """Black leather shoes (label 0) over his feet to his ankles, thick soles and low heels, a brass buckle (6) on each
    instep."""
    fd = Field("Shoes")
    # the shoes: over his feet to his ankles, thick soles and low heels, a tongue and a brass buckle on the instep
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        fh = foot_hull(side)
        fd.add(Inter(Shell(fh, 0.009, 0.012, pad=0.06, disp=lambda P: F(0.0012) * NOISE(P * F(30)), disp_amp=0.0015),
                     Func(lambda P: P[:, 2] - F(0.135), an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.2))), 0.004), 0.0)
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.098)), (0.078, 0.158, 0.012), 0.009, R=Rz), 0.006)
        fd.add(RoundBox(an + fwd * -0.018 + v3((0, 0, -0.088)), (0.06, 0.05, 0.022), 0.01, R=Rz), 0.006)            # the heel
        # the buckle on the instep
        h, ok = ray_hit(Func(lambda P, fh=fh: fh.eval(P, margin=0.1) - F(0.021), an - 0.4, an + 0.4),
                        [an + fwd * 0.08 + v3((0, 0, 0.3))], [v3((0, 0, -1))], tmax=0.5)
        if ok[0]:
            c = h[0]
            nrm = norm(v3((0, 0, 1)) - fwd * 0.6)
            R = rot_from_axes(z_axis=nrm, y_axis=fwd)
            fd.add(RoundBox(c + nrm * 0.004, (0.034, 0.024, 0.006), 0.004, R=R), 0.004, 6)
            fd.sub(RoundBox(c + nrm * 0.009, (0.02, 0.012, 0.006), 0.003, R=R), 0.002)
            fd.add(RoundBox(c, (0.03, 0.03, 0.006), 0.004, R=R), 0.004)                                             # the strap
    return fd


def black_field():
    """Black leather (label 0), brass (6): the stock round his throat; the grenade pouch with its flap and a brass flaming
    grenade on it; the hanger's scabbard (brass locket and chape) and the hanger's brass hilt (a knuckle bow, a ridged
    grip, a cap pommel)."""
    fd = Field("Black")
    # the stock: a band of black leather round his neck
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(1.445)) - F(0.042), (-0.16, -0.12, 1.38), (0.16, 0.22, 1.51)), Shell(nk, 0.01, 0.012, pad=0.06),
                 0.004), 0.0)
    # the grenade pouch: a stiff box with a rounded flap, a brass badge on it
    C, S, Up, N = pouch_frame()
    hx, hy, hz = POUCH_HALF
    R = np.stack([S, Up, N], axis=1)
    fd.add(RoundBox(C, (hx, hy, hz), 0.012, R=R), 0.0)
    def flap(P):
        q = P - (C + N * (hz + 0.004) + Up * (hy * 0.25)).astype(F)
        s, u, n = q @ S.astype(F), q @ Up.astype(F), q @ N.astype(F)
        outline = np.maximum(np.abs(s) - F(hx + 0.006), u - F(hy * 0.8))
        bottom = np.sqrt(s * s / F((hx + 0.006) ** 2) + np.minimum(u + F(hy * 0.45), F(0)) ** 2 / F(0.05 ** 2)) - F(1.0)
        o = np.maximum(outline, bottom * F(0.04))
        return np.maximum(o, np.abs(n) - F(0.005))
    fd.add(Func(flap, C - 0.2, C + 0.2), 0.003)
    def badge(P):
        q = P - (C + N * (hz + 0.009) + Up * (hy * 0.05)).astype(F)
        s, u, n = q @ S.astype(F), q @ Up.astype(F), q @ N.astype(F)
        return np.maximum(badge_2d(s, u, (0.0, -0.006), 0.075), np.abs(n) - F(0.003))
    fd.add(Func(badge, C - 0.2, C + 0.2), 0.002, 6)
    # the scabbard: black leather, a brass locket at its mouth and a brass chape at its tip
    pts = hanger_curve()
    side_n = norm(np.cross(norm(pts[-1] - pts[0]), v3((0, 1, 0))))
    ws = [0.028 - 0.012 * k / 10 for k in range(11)]
    ts = [0.013 - 0.004 * k / 10 for k in range(11)]
    fd.add(Lock(pts, ws, ts, [side_n] * len(pts), k=0.004), 0.0)
    d0 = norm(pts[1] - pts[0])
    fd.add(Lock([pts[0] - d0 * 0.01, pts[0] + d0 * 0.06], [0.034, 0.033], [0.018, 0.018], [side_n] * 2, k=0.003), 0.004, 6)
    d1 = norm(pts[-1] - pts[-2])
    fd.add(Lock([pts[-1] - d1 * 0.06, pts[-1] + d1 * 0.012], [0.02, 0.008], [0.012, 0.007], [side_n] * 2, k=0.003), 0.004, 6)
    # the hilt: a ridged brass grip rising forward out of the mouth, a knuckle bow from the guard to the pommel
    gd = norm(-d0 + v3((0, -0.25, 0.0)))
    g0 = pts[0] - d0 * 0.012
    g1 = g0 + gd * 0.1
    ridges = lambda P: F(0.0015) * np.abs(np.sin(((P - g0.astype(F)) @ gd.astype(F)) * F(180)))
    fd.add(RoundCone(g0 + gd * 0.012, g1, 0.016, 0.014, disp=ridges, disp_amp=0.0016), 0.003, 6)
    fd.add(Sphere(g1 + gd * 0.008, 0.019), 0.004, 6)
    fd.add(Lock([g0 - side_n * 0.0, g0 + side_n * 0.0 + gd * 0.004], [0.03, 0.03], [0.008, 0.008], [gd, gd], k=0.002), 0.003, 6)  # guard
    out = norm(np.cross(gd, side_n))
    if out[1] > 0:
        out = -out
    bow = [g0 + out * 0.02, g0 + out * 0.045 + gd * 0.03, g0 + out * 0.048 + gd * 0.07, g1 + out * 0.02 + gd * 0.006]
    fd.add(Chain(bow, [0.0065, 0.006, 0.006, 0.0065], k=0.004), 0.004, 6)
    return fd


# ======================================================================================= white belts
BELT_A = v3((0.2, 0.08, 1.5))          # the cross-belt goes over his left shoulder here ...
BELT_B = v3((-0.33, 0.06, 0.82))       # ... and down to the pouch on his right hip
BELT_W = 0.034                         # half its width
BELT_OFF = COAT_OFF + COAT_T * 0.5 + 0.009
WAIST_Z = 0.965


def belt_plane():
    n = norm(np.cross(BELT_B - BELT_A, v3((0, 1, 0))))
    return BELT_A, n


def belt_base():
    return coat_hull(arms=True, skirt=True)


def belts_field():
    """Whitened buff leather: the cross-belt from his left shoulder across his chest and back to his right hip, and the
    waist belt over the waistcoat (it shows between the coat's fronts)."""
    fd = Field("Belts")
    bb = belt_base()
    A, n = belt_plane()
    lo, hi = (-0.7, -0.7, 0.6), (0.7, 0.7, 1.75)
    def slab(P):
        d = (P - A.astype(F)) @ n.astype(F)
        return np.maximum(np.abs(d) - F(BELT_W), neck_open(P, 0.15))
    fd.add(Inter(Func(slab, (-0.5, -0.42, 0.68), (0.4, 0.46, 1.66)), Shell(bb, BELT_OFF, 0.011, pad=0.1), 0.003), 0.0)
    th = torso_hull()
    fd.add(Inter(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(WAIST_Z)) - F(0.026), P[:, 1] - F(0.05)), (-0.42, -0.42, 0.9), (0.42, 0.1, 1.03)),
                 Shell(th, WB_OFF, WB_T, pad=0.1), 0.003), 0.0)
    return fd


def belt_point(z):
    """A point on the cross-belt's front strand at height z (on its outer face), with the belt's outward normal."""
    bb = belt_base()
    A, n = belt_plane()
    x = A[0] + (z - A[2]) * (-n[2] / n[0])
    outer = Func(lambda P: bb.eval(P, margin=0.1) - F(BELT_OFF + 0.0055), (-0.8, -0.8, 0.6), (0.8, 0.8, 1.7))
    h, ok = ray_hit(outer, [v3((x, -0.7, z))], [v3((0, 1, 0))], tmax=0.8)
    p = h[0] if ok[0] else v3((x, -0.33, z))
    e = 0.004
    g = np.array([(outer(np.array([p + d], F))[0] - outer(np.array([p - d], F))[0]) / (2 * e) for d in np.eye(3) * e])
    return p, norm(g)


# ======================================================================================= brass: buttons, the match case
MATCH_Z = 1.29                         # the match case on the cross-belt, at the middle of his chest
MATCH_LEN = 0.085
MATCH_R = 0.017


def match_frame():
    p, nrm = belt_point(MATCH_Z)
    up = norm(v3((0, 0, 1)) - nrm * nrm[2])
    c = p + nrm * (MATCH_R * 0.9)
    return c, up, nrm


def match_tip():
    """The smouldering end of the slow match, just out of the case's top (the fuse is touched to it)."""
    c, up, nrm = match_frame()
    return c + up * (MATCH_LEN * 0.5 + 0.026) + nrm * 0.004


def brass_field():
    """Brass: the buttons (lapels, waistcoat) and the match case: a pierced tube with a domed cap on a
    chain, a ring clipping it to the belt."""
    fd = Field("Brass")
    for p, d in lapel_buttons() + waistcoat_buttons():
        fd.add(Cylinder(p, 0.0115 if abs(p[0]) > 0.04 else 0.0085, 0.007, rr=0.0034, R=rot_from_axes(z_axis=d)), 0.0)
    c, up, nrm = match_frame()
    holes = lambda P: F(0.0016) * (np.sin(((P - c.astype(F)) @ up.astype(F)) * F(260)) > F(0.5))
    fd.add(RoundCone(c - up * (MATCH_LEN * 0.5), c + up * (MATCH_LEN * 0.5), MATCH_R, MATCH_R * 0.92, disp=holes, disp_amp=0.002), 0.0)
    fd.add(Inter(Sphere(c + up * (MATCH_LEN * 0.5 - 0.004), MATCH_R * 1.02), Plane(c + up * (MATCH_LEN * 0.5), -up), 0.002), 0.003)
    for zz in (-0.3, 0.25):
        fd.add(Torus(c + up * (MATCH_LEN * zz), MATCH_R + 0.002, 0.003, R=rot_from_axes(z_axis=up)), 0.002)
    return fd


def ember_field():
    """The slow match's smouldering end (its own glowing mesh)."""
    fd = Field("Ember")
    c, up, nrm = match_frame()
    tip = match_tip()
    fd.add(RoundCone(c + up * (MATCH_LEN * 0.5), tip, 0.0062, 0.0075), 0.0)
    fd.add(Sphere(tip, 0.0095), 0.003)
    return fd


# ======================================================================================= the grenade, its sparks
def grenade_field():
    """A black cast-iron ball (label 0) with a raised seam, a wooden fuse plug (5) and a short tarred fuse (8)."""
    fd = Field("Grenade")
    C = grenade_center()
    D = fuse_dir()
    pits = lambda P: F(0.0012) * NOISE(P * F(55))
    fd.add(Sphere(C, GREN_R, disp=pits, disp_amp=0.0014), 0.0)
    e = norm(np.cross(D, v3((0, 0, 1)) if abs(D[2]) < 0.9 else v3((1, 0, 0))))
    fd.add(Torus(C, GREN_R, 0.0026, R=rot_from_axes(z_axis=e)), 0.002)                                  # the casting seam
    p0 = C + D * (GREN_R - 0.008)
    fd.add(RoundCone(p0, p0 + D * 0.026, 0.0135, 0.011), 0.003, 5)
    side = norm(np.cross(D, e))
    tip = fuse_tip()
    fd.add(Chain([p0 + D * 0.024, p0 + D * 0.032 + side * 0.003, tip], [0.0045, 0.004, 0.0035], k=0.002), 0.002, 8)
    return fd


def _spark(fd, c, size, seed):
    rs = np.random.RandomState(seed)
    fd.add(Sphere(c, size * 0.32), 0.0)
    for k in range(9):
        d = norm(rs.normal(size=3))
        L = size * rs.uniform(0.7, 1.1)
        fd.add(RoundCone(c + d * size * 0.15, c + d * L, size * 0.13, size * 0.03), size * 0.08)


def spark_field():
    fd = Field("Spark")
    _spark(fd, fuse_tip(), 0.034, 11)
    return fd


# ======================================================================================= his powder keg
KEG_C = v3((-0.44, -0.15, 0.0))        # its foot, on the flagstones at his right front (clear of his right shoe)
KEG_H = 0.27
KEG_R0, KEG_R1 = 0.092, 0.112          # its heads and its belly
KEG_FUSE = 0.05


def keg_tip():
    return KEG_C + v3((0.03, 0.0, KEG_H + KEG_FUSE))


def keg_field():
    """A small oak powder keg: staves (label 0, the grain along them: 11) bulging to its belly, four iron hoops (6), its top
    head with a bung and a short tarred fuse (8)."""
    fd = Field("Keg")
    c = KEG_C
    def barrel(P):
        q = P - c.astype(F)
        z = q[:, 2]
        k = np.clip(z / F(KEG_H), 0, 1)
        r = F(KEG_R0) + F(KEG_R1 - KEG_R0) * np.sin(k * F(math.pi))
        a = np.arctan2(q[:, 1], q[:, 0])
        stave = F(0.0016) * (np.abs(np.sin(a * F(9))) ** 0.3)
        rr = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        d_r = rr - r + stave
        d_z = np.abs(z - F(KEG_H / 2)) - F(KEG_H / 2)
        qq = np.stack([np.maximum(d_r + F(0.008), 0), np.maximum(d_z + F(0.008), 0)], 1)
        return np.sqrt((qq ** 2).sum(1)) + np.minimum(np.maximum(d_r + F(0.008), d_z + F(0.008)), 0) - F(0.008)
    grain = lambda P: F(0.0012) * NOISE(P * np.array([60, 60, 5], F))
    fd.add(Func(barrel, c - v3((0.2, 0.2, 0.05)), c + v3((0.2, 0.2, KEG_H + 0.05)), disp=grain, disp_amp=0.0015), 0.0, 11)
    fd.sub(Cylinder(c + v3((0, 0, KEG_H + 0.002)), KEG_R0 - 0.012, 0.012, rr=0.003), 0.003)                # the head sits in the chime
    for zf in (0.07, 0.19, 0.81, 0.93):
        z = KEG_H * zf
        r = KEG_R0 + (KEG_R1 - KEG_R0) * math.sin(zf * math.pi)
        fd.add(Torus(c + v3((0, 0, z)), r + 0.001, 0.0055), 0.003, 6)
    tip = keg_tip()
    bung = c + v3((0.03, 0.0, KEG_H - 0.004))
    fd.add(Cylinder(bung, 0.017, 0.012, rr=0.004), 0.003, 11)
    fd.add(Chain([bung + v3((0, 0, 0.004)), bung + v3((0.006, 0.004, 0.026)), tip], [0.0055, 0.005, 0.0042], k=0.002), 0.002, 8)
    return fd


def keg_spark_field():
    fd = Field("KegSpark")
    _spark(fd, keg_tip(), 0.042, 23)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.62)), 0.05, 0.45)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.112, -0.15, 1.628)), 0.07, 0.7), (hp((sx * 0.18, 0.035, 1.664)), 0.055, 0.5),
                (hp((sx * 0.06, -0.2, 1.52)), 0.04, 0.25)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.044, 0.0148, -0.0148, -0.044):
            pts.append((wr + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.012, 0.03, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "marco"
ROOT_NAME = "HeroMarcoHQ"
TEX_PREFIX = "hero"
MAT_NAME = "MarcoMat"
MESH_NAME = "Marco"
BASE_MODULE = "marco_base"
ANIM_MODULE = "anim_marco"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Moustache", "Cap", "Coat", "Waistcoat", "Breeches", "Gaiters", "Belts", "Black",
         "Shoes", "Brass", "Grenade", "Keg", "Spark", "KegSpark", "Ember"]
REGION_PARTS = ("Skin", "Cap", "Coat", "Waistcoat", "Black", "Shoes", "Grenade", "Keg")
BLACK_HAIR = {"name": "HQ_MarcoHair", "base": (0.07, 0.06, 0.055), "hi": (0.3, 0.26, 0.24), "low": (0.03, 0.026, 0.024),
              "streak": (0.05, 0.042, 0.038), "tint": (0.14, 0.11, 0.09)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_MarcoSkin", "base": (0.82, 0.58, 0.44), "ruddy": (0.9, 0.44, 0.36), "lips": (0.7, 0.36, 0.32),
                      "brow": ((0.04, 0.035, 0.03), (0.11, 0.09, 0.08)),
                      "extra": ((LASH, (0.04, 0.03, 0.025), 0.5), (STUBBLE, (0.42, 0.33, 0.3), 0.55, 0.32),
                                (SOOT, (0.13, 0.11, 0.1), 0.6, 0.85))}),
    "Hair": ("hair", BLACK_HAIR),
    "Moustache": ("hair", dict(BLACK_HAIR, name="HQ_MarcoMoustache", hi=(0.36, 0.32, 0.3))),
    "Cap": ("wool", {"name": "HQ_MarcoCap", "base": CRIMSON, "border": LACE, "stripe": GOLD}),
    "Coat": ("wool", {"name": "HQ_MarcoCoat", "base": CRIMSON, "border": LACE, "stripe": GOLD}),
    "Waistcoat": ("wool", {"name": "HQ_MarcoWaistcoat", "base": BUFF, "border": LACE, "stripe": GOLD}),
    "Breeches": ("linen", {"name": "HQ_MarcoBreeches", "base": LINEN}),
    "Gaiters": ("wool", {"name": "HQ_MarcoGaiters", "base": BLACK, "border": BLACK, "stripe": BLACK}),
    "Belts": ("linen", {"name": "HQ_MarcoBelts", "base": WHITE}),
    "Black": ("leather_dyed", {"name": "HQ_MarcoBlack", "base": (0.075, 0.066, 0.064), "dyed": (0.075, 0.066, 0.064),
                               "worn_c": (0.36, 0.34, 0.33)}),
    "Shoes": ("leather_dyed", {"name": "HQ_MarcoBlack", "base": (0.075, 0.066, 0.064), "dyed": (0.075, 0.066, 0.064),
                               "worn_c": (0.36, 0.34, 0.33)}),
    "Brass": ("bronze", {"name": "HQ_MarcoBrass", "base": (0.8, 0.6, 0.24), "hi": (1.0, 0.92, 0.6), "dark": (0.38, 0.25, 0.08),
                         "patina": (0.42, 0.44, 0.24)}),
    "Grenade": ("iron", {"name": "HQ_Grenade", "col": {"base": (0.1, 0.1, 0.11), "hi": (0.46, 0.47, 0.5), "dark": (0.03, 0.03, 0.035),
                                                         "rust": (0.26, 0.15, 0.08)},
                         "wood": (0.62, 0.46, 0.28), "cord": (0.3, 0.24, 0.17)}),
    "Keg": ("siege", {"name": "HQ_PowderKeg", "wood": (0.52, 0.34, 0.19), "wood2": (0.38, 0.24, 0.13), "metal": "iron"}),
    "Spark": ("glow_ball", {"name": "HQ_Spark", "col": (1.0, 0.7, 0.2)}),
    "KegSpark": ("glow_ball", {"name": "HQ_Spark", "col": (1.0, 0.7, 0.2)}),
    "Ember": ("glow_ball", {"name": "HQ_MatchEmber", "col": (1.0, 0.36, 0.08)}),
}
GLOW = {"Spark": ((1.0, 0.66, 0.2), 1.3, 0.5), "KegSpark": ((1.0, 0.66, 0.2), 1.3, 0.5), "Ember": ((1.0, 0.38, 0.08), 1.1, 0.5)}
LOW_TARGETS = {"Skin": 6000, "Teeth": 100, "Hair": 900, "Moustache": 800, "Cap": 1900, "Coat": 4400, "Waistcoat": 900,
               "Breeches": 900, "Gaiters": 1000, "Belts": 800, "Black": 1500, "Shoes": 800, "Brass": 1100, "Grenade": 300, "Keg": 700,
               "Spark": 140, "KegSpark": 140, "Ember": 60}
AO_EXCLUDE = ["Grenade", "Keg", "Spark", "KegSpark", "Ember", "Brass"]


def prop_bones():
    """The grenade (a free bone kept in his right hand by the clips), its sparks (on it), his cap (a free bone kept on his
    head by the clips)."""
    wr, f, n, t = hand_frame("R")
    C = grenade_center()
    tip = fuse_tip()
    cr = cap_root()
    return [("grenade", C, C + f * 0.12, None),
            ("spark", tip, tip + fuse_dir() * 0.06, "grenade"),
            ("cap", cr, cr + v3((0.0, 0.0, 0.22)), None)]


def extra_bones():
    """His powder keg (free: the Ability lifts it) and its sparks."""
    tip = keg_tip()
    return [("keg", KEG_C + v3((0, 0, 0.02)), KEG_C + v3((0, 0, 0.24)), None),
            ("keg_spark", tip, tip + v3((0, 0, 0.06)), "keg")]


BODY = {"root", "spine", "chest", "neck", "head", "clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R",
        "forearm.L", "hand.R", "hand.L", "thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}
CLOTH = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L", "thigh.R", "thigh.L"}
CLOTH_CAPS = {"thigh.R": 0.45, "thigh.L": 0.45}


def hair_weights(ob, skin_ob, arm):
    """His head; the queue down the back of his neck blends from the head into the neck."""
    groups = {}
    zq = hp((0, 0, 1.6))[2]
    for v in ob.data.vertices:
        z, y = v.co.z, v.co.y
        if y > 0.16 and z < zq:
            k = min(1.0, max(0.0, (zq - z) / 0.2))
            w = {"head": 1.0 - 0.7 * k, "neck": 0.7 * k}
        else:
            w = {"head": 1.0}
        _blend_add(ob, groups, v.index, w)


def _clear(ob, v):
    for g in list(ob.vertex_groups):
        g.remove([v.index])


def black_weights(ob, skin_ob, arm):
    """The stock with his neck; the pouch and the hanger rigid with his hips."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed={"neck", "chest", "head"})
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z > 1.3:
            continue                                    # the stock (transferred: neck)
        _clear(ob, v)
        _blend_add(ob, groups, v.index, {"root": 1.0})


def brass_weights(ob, skin_ob, arm):
    """Buttons with the cloth they are on; the match case rigid with his chest (its ember is)."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=BODY)
    c, up, nrm = match_frame()
    groups = {}
    for v in ob.data.vertices:
        if np.linalg.norm(np.array(v.co) - c) < 0.08:
            _clear(ob, v)
            _blend_add(ob, groups, v.index, {"chest": 1.0})


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("custom", hair_weights), "Moustache": ("rigid", "head"),
        "Cap": ("rigid", "cap"),
        "Coat": ("transfer", CLOTH, CLOTH_CAPS),
        "Waistcoat": ("transfer", CLOTH, CLOTH_CAPS),
        "Breeches": ("transfer", {"root", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Gaiters": ("transfer", {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Belts": ("transfer", TORSO | {"clavicle.L", "clavicle.R"}, None),
        "Black": ("custom", black_weights), "Shoes": ("transfer", {"foot.R", "foot.L", "shin.R", "shin.L"}, None),
        "Brass": ("custom", brass_weights),
        "Grenade": ("rigid", "grenade"), "Spark": ("rigid", "spark"),
        "Keg": ("rigid", "keg"), "KegSpark": ("rigid", "keg_spark"),
        "Ember": ("rigid", "chest"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Moustache") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Cap" and c.y < -0.05:
        return 1.35
    if part in ("Grenade", "Keg"):
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.003),
        ("Moustache", moustache_field(), 0.0016 if fine else 0.0022),
        ("Cap", cap_field(), 0.0024 if fine else 0.0034),
        ("Coat", coat_field(), 0.0026 if fine else 0.0036),
        ("Waistcoat", waistcoat_field(), 0.0026 if fine else 0.0036),
        ("Breeches", breeches_field(), 0.0026 if fine else 0.0036),
        ("Gaiters", gaiters_field(), 0.0024 if fine else 0.0034),
        ("Belts", belts_field(), 0.0026 if fine else 0.0034),
        ("Black", black_field(), 0.0024 if fine else 0.0032),
        ("Shoes", shoes_field(), 0.0022 if fine else 0.003),
        ("Brass", brass_field(), 0.0018 if fine else 0.0026),
        ("Grenade", grenade_field(), 0.0016 if fine else 0.0022),
        ("Keg", keg_field(), 0.002 if fine else 0.0028),
        ("Spark", spark_field(), 0.0012),
        ("KegSpark", keg_spark_field(), 0.0012),
        ("Ember", ember_field(), 0.0012),
    ]
