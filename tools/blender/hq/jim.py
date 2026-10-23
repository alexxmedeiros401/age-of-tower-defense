"""Big Jim Coalfoot, Rail Boss (HQ hero, Industrial Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A giant, good-natured railway foreman: a huge chest and arms, a big bushy black beard flecked with grey, a booming laugh
in his face (his mouth wide open, his teeth showing, his eyes crinkled shut-ish above round cheeks), coal dust on his
cheeks and his nose; a striped engineer's cap of navy-and-white ticking (a puffed crown gathered into a band, a short
stiff peak, a button on top), black hair showing under it at his temples and nape; a red neckerchief with white spots,
knotted at the left of his throat; a navy work shirt, its sleeves rolled up above his elbows over huge bare forearms;
denim-blue bib overalls (orange top-stitching, brass buttons where the straps meet the bib and at the hips, a pocket on
the bib with a brass pocket watch peeking out of it on a short chain), the trouser legs turned up over his boots; brown
leather gauntlets (the gloves, flared cuffs over his wrists); big hobnailed boots.

His weapon: a massive spike maul (a railway spike driver): a long ash handle with a leather grip at its butt, a long
forged-iron head with two narrow driving faces. Swung two-handed: the maul is rigid on the `maul` bone in his right fist
(his lower hand, at the butt); anim_jim.py closes his left fist on the handle above it.

His body is the smith's (tarek.py: big and broad) with a bigger chest and bigger arms; his head is Tarek's face laughing."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp, project_to, grad
from ugo import _blend_add
import tarek as tk
from tarek import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, foot,
                   traps, neck_prim, TORSO, TORSO_Z, torso_bones, curls)

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, SOOT, GLOVE = 0, 1, 2, 3, 4, 5, 8, 9, 11

NAVY = (0.18, 0.22, 0.42)             # the Industrial corps' navy wool (his shirt; the cap's ticking)
DENIM = (0.34, 0.5, 0.72)             # his overalls (a faded denim, lighter than the navy)
STITCH = (0.86, 0.56, 0.22)           # their orange top-stitching
TICK_W = (0.9, 0.9, 0.85)             # the ticking's white stripes
KERCHIEF = (0.72, 0.09, 0.06)
SPOTS = (0.95, 0.93, 0.88)
GLOVE_C = (0.46, 0.27, 0.13)


# ======================================================================================= hands (gloved fists)
HAND_S = 1.1


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    """Both fists closed round the maul's handle, in leather gloves (painted: label GLOVE)."""
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.066, 0.036, 0.066)) * s, 0.03 * s, R=Rp), 0.028, GLOVE)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.037, 0.031, 0.052)) * s, R=Rp), 0.019, GLOVE)
    curl_ax = norm(np.cross(f, n))
    offs = (0.044, 0.0148, -0.0148, -0.044)
    lens = (0.96, 1.02, 0.96, 0.8)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.024 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, (1.45, 1.6, 1.2)[j] * (0.9 if i == 3 else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.92)
        fd.add(Chain(pts, rads, k=0.006), 0.011, GLOVE)
        fd.add(Sphere(pts[0] - n * 0.011, 0.017 * s), 0.009, GLOVE)
    tb = wr + f * 0.045 * s + t * 0.052 * s + n * 0.011
    d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
    d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.028 * s, 0.025 * s, 0.022 * s], k=0.008), 0.018, GLOVE)


# ======================================================================================= body (the smith's, bigger up top)
def torso_prims():
    return tk.torso_prims() + [(Ellipsoid((0, -0.01, 1.2), (0.305, 0.21, 0.23)), 0.07)]          # a huge chest


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.028, -0.005, 0.016)), 0.126)


def upper_arm(side):
    return RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.114, 0.088)


def forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.092, 0.064)


def arm_prims(side):
    """(prim, k) for one arm, shoulder to wrist: huge, the forearms above all."""
    sx = -1 if side == "R" else 1
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    return [(deltoid(side), 0.055), (upper_arm(side), 0.05),
            (Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.03, 0)), (0.108, 0.112, 0.142), R=rot_from_axes(z_axis=el - sh)), 0.04),
            (forearm(side), 0.035),
            (Ellipsoid(lerp(el, wr, 0.32) + v3((sx * 0.01, -0.004, 0)), (0.116, 0.104, 0.152), R=rot_from_axes(z_axis=wr - el)), 0.04),
            (Sphere(el + v3((0, 0.025, 0)), 0.064), 0.028)]


def leg_prims(side):
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(hip, kn, 0.142, 0.094), 0.065),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.132, 0.122, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.048),
            (Sphere(kn + v3((0, -0.03, 0.0)), 0.074), 0.038),
            (RoundCone(kn, an, 0.09, 0.06), 0.038),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.102, 0.099, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043)]


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        for p, k in arm_prims(side):
            fd.add(p, k, SKIN)
        hand(fd, side)
        # coal dust up his forearms
        fd.paint(Inter(RoundCone(lerp(el, wr, 0.5), wr, 0.11, 0.09),
                       Func(lambda P: F(0.025) - NOISE(P * F(11)) * F(0.06) - F(0.02), wr - 0.4, wr + 0.4), 0.01), SOOT)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


# ======================================================================================= head: a booming laugh
MOUTH_C = (0.0, -0.19, 1.53)          # design units: the open mouth
MOUTH_R = (0.072, 0.055, 0.046)


def head(fd):
    """Tarek's broad face, laughing: the mouth wide open (upper teeth showing, a tongue), round cheeks bunched up, the eyes
    crinkled nearly shut, bushy brows raised, a broad round nose; coal dust on his cheekbones, nose and brow."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.052, 1.585), (0.155, 0.14, 0.13)), 0.07, SKIN)                          # a broad jaw (under the beard)
    fd.add(E((0, -0.13, 1.49), (0.09, 0.074, 0.07)), 0.05, SKIN)                            # the chin, dropped (laughing)
    for sx in (-1, 1):
        fd.add(S((sx * 0.118, -0.13, 1.64), 0.058), 0.05, SKIN)                             # round cheeks, bunched up
        fd.add(S((sx * 0.13, -0.045, 1.552), 0.053), 0.05, SKIN)
        pts = [hp((sx * 0.156, -0.055, 1.744)), hp((sx * 0.118, -0.134, 1.758)), hp((sx * 0.062, -0.176, 1.756)), hp((0.0, -0.186, 1.752))]
        fd.add(Chain(pts, [hr(0.012), hr(0.019), hr(0.022), hr(0.02)], k=hr(0.022)), hr(0.03), SKIN)
    # forehead creases (raised brows)
    sk = tk.skull()
    for zc in (1.81, 1.835):
        pts = []
        for k in range(9):
            x = -0.08 + 0.16 * k / 8
            h, ok = ray_hit(sk, [hp((x, -0.6, zc + 0.012 * (x / 0.08) ** 2))], [v3((0, 1, 0))], tmax=0.7)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 3:
            fd.sub(Chain(pts, [hr(0.0024)] * len(pts), k=0.002), hr(0.003))
    # bushy brows, raised high
    tuft = lambda P: F(0.0024) * NOISE(P * F(140)) + F(0.0012) * np.sin(P[:, 0] * F(360))
    for sx in (-1, 1):
        pts = [hp((sx * 0.024, -0.212, 1.792)), hp((sx * 0.066, -0.208, 1.799)), hp((sx * 0.114, -0.186, 1.792)), hp((sx * 0.158, -0.146, 1.77))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.013), hr(0.016), hr(0.014), hr(0.007)], k=hr(0.008),
                     disp=tuft, disp_amp=0.003), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.025), hr(0.028), hr(0.025), hr(0.014)], k=hr(0.01)), BROW)
    # eyes crinkled by the laugh (narrow, the lower lids pushed up by his cheeks)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.014))), (sx * 0.22, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0064)), Plane(ec + v3((0, 0, -hr(0.004))), (sx * -0.2, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.011))), (sx * 0.22, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(3):                                                                      # laughter lines
            a = hp((sx * (0.11 + 0.004 * k), -0.128 + 0.006 * k, 1.684 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.026, 0.012, -0.002 - 0.009 * k)), hr(0.0024), hr(0.0015)), hr(0.003))
    # a broad, round nose
    fd.add(RoundCone(hp((0, -0.186, 1.726)), hp((0, -0.24, 1.636)), hr(0.021), hr(0.028)), hr(0.018), SKIN)
    fd.add(S((0, -0.242, 1.626), 0.032), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.039, -0.218, 1.61), 0.026), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.02, -0.238, 1.598)), v3((0.01, 0.012, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the laugh: the mouth wide open, a tongue in it, the lower lip
    fd.sub(Ellipsoid(hp(MOUTH_C), v3(MOUTH_R) * HS), hr(0.008))
    fd.paint(Ellipsoid(hp(MOUTH_C), (v3(MOUTH_R) + 0.005) * HS), MOUTH)
    fd.add(Ellipsoid(hp((0.0, -0.17, 1.508)), v3((0.042, 0.042, 0.016)) * HS), hr(0.006), LIP)
    lo_lip = [(-0.052, -0.176, 1.518), (-0.03, -0.198, 1.503), (0, -0.206, 1.498), (0.03, -0.198, 1.503), (0.052, -0.176, 1.518)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.008), hr(0.009), hr(0.008), hr(0.004)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.028, 0.05, 0.064)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.012, 0.032, 0.042)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
    # coal dust: smudged on his cheekbones, the tip of his nose, his brow
    for c, r, rot in (((0.118, -0.152, 1.668), (0.034, 0.02, 0.016), 0.4), ((-0.112, -0.158, 1.664), (0.03, 0.02, 0.015), -0.5),
                      ((0.0, -0.262, 1.63), (0.02, 0.014, 0.014), 0.0), ((-0.06, -0.2, 1.81), (0.03, 0.015, 0.01), 0.2)):
        fd.paint(Ellipsoid(hp(c), v3(r) * HS * 1.6, R=euler(0.2, 0.0, rot)), SOOT)


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
    """His upper teeth, big and white, showing under the moustache in the open laugh."""
    fd = Field("Teeth")
    for k in range(6):
        x = -0.05 + 0.02 * k
        y = -0.2 + 0.024 * (abs(x) / 0.05) ** 2
        fd.add(RoundBox(hp((x, y, 1.562 + 0.006 * (abs(x) / 0.05) ** 2)), v3((0.0094, 0.0065, 0.0105)) * HS, hr(0.003)), 0.002)
    return fd


# ======================================================================================= beard, hair
BEARD_LOW = 1.31


def beard_field():
    """A big bushy black beard (grey flecked through it: the material), over his cheeks and jaw and down onto the top of
    his chest, a round open hole for his laughing mouth; a thick bushy moustache over it, drooping at its ends."""
    fd = Field("Beard")
    hull = tk.head_hull()
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.565) + F(0.05) * smoothstep(0.07, 0.15, ax) + F(0.08) * smoothstep(0.13, 0.175, ax) * smoothstep(-0.11, -0.04, y)
        mo = (x / F(0.084)) ** 2 + ((y + F(0.19)) / F(0.08)) ** 2 + ((z - F(1.528)) / F(0.05)) ** 2 - F(1.0)
        back = np.where(ax > F(0.14), y - F(0.04), y - F(0.0))
        return np.maximum(np.maximum(np.maximum(z - top, back), -mo * F(0.03)), F(BEARD_LOW + 0.1) - z)
    bushy = lambda P: curls(P, 0.017, 0.0055) + F(0.0016) * NOISE(P * np.array([60.0, 60.0, 20.0], F))
    fd.add(Inter(Shell(hull, 0.016, 0.042, pad=0.08, disp=bushy, disp_amp=0.008), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.012), 0.0)
    # the bulk of it under his chin, spreading over the top of his chest (clear of the mouth)
    def chin_keep(P):
        Q = hinv(P)
        mo = (Q[:, 0] / F(0.08)) ** 2 + ((Q[:, 1] + F(0.2)) / F(0.08)) ** 2 + ((Q[:, 2] - F(1.528)) / F(0.048)) ** 2 - F(1.0)
        return -mo * F(0.03)
    big = Field("BeardBulk")
    big.add(Ellipsoid(hp((0, -0.15, 1.45)), v3((0.15, 0.1, 0.1)) * HS), 0.0)
    big.add(Ellipsoid(hp((0, -0.13, 1.36)), v3((0.13, 0.1, 0.075)) * HS), 0.05)
    for sx in (-1, 1):
        big.add(Ellipsoid(hp((sx * 0.1, -0.1, 1.44)), v3((0.08, 0.09, 0.1)) * HS), 0.04)
    blo, bhi = big.bounds()
    fd.add(Inter(Func(lambda P: big.eval(P, margin=0.04), blo - 0.03, bhi + 0.03, disp=bushy, disp_amp=0.008),
                 Func(chin_keep, blo - 0.05, bhi + 0.05), 0.01), 0.03)
    # the moustache: two thick bushy locks swept out and down past the corners of his mouth
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.236, 1.592)), hp((sx * 0.048, -0.226, 1.584)), hp((sx * 0.084, -0.2, 1.566)), hp((sx * 0.104, -0.176, 1.535)),
               hp((sx * 0.11, -0.16, 1.5))]
        fd.add(Lock(pts, [hr(0.02), hr(0.024), hr(0.021), hr(0.015), hr(0.009)], [hr(0.015), hr(0.016), hr(0.014), hr(0.011), hr(0.007)],
                    [norm(v3((sx * 0.3, -1, 0.3)))] * 5, k=hr(0.007), disp=lambda P: curls(P, 0.012, 0.0035), disp_amp=0.005), hr(0.008))
    return fd


CAP_IN = 0.03                          # the cap's inside: this far out from his skull
BAND_F = v3((0.0, -0.18, 1.862))       # the cap band's plane (design units): across his brow ...
BAND_B = v3((0.0, 0.215, 1.7))        # ... and low behind, at his nape
_BAND_N = norm(v3((0, -(BAND_B[2] - BAND_F[2]) / (BAND_B[1] - BAND_F[1]), 1.0)))
BAND_H = 0.03                          # half its height (design units)


def band_d(P):
    """Height above the cap band's middle plane (design units)."""
    return (hinv(P) - BAND_F.astype(F)) @ _BAND_N.astype(F)


def skull():
    return Ellipsoid(HEAD_C, HEAD_RAD)


def hair_field():
    """Short black hair showing under the cap: over his temples into the beard, round the back of his head to the nape."""
    fd = Field("Hair")
    sk = skull()
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        under = band_d(P) - F(0.0)                                                     # (up into the cap)
        face = np.where(ax < F(0.135), F(-0.09) - y, F(-0.075) - y + F(0.3) * np.maximum(F(1.6) - z, F(0)))
        ear = np.where((ax > F(0.15)) & (z < F(1.73)) & (np.abs(y - F(0.035)) < F(0.06)), F(0.02), F(-1.0))
        nape = F(1.57) - z
        return np.maximum(np.maximum(np.maximum(under, face), ear), nape)
    comb = lambda P: F(0.0016) * np.sin(hinv(P)[:, 2] * F(300)) + F(0.001) * NOISE(P * F(60))
    fd.add(Inter(Shell(sk, 0.006, 0.016, pad=0.06, disp=comb, disp_amp=0.002), Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.004), 0.0)
    return fd


# ======================================================================================= the engineer's cap
def _cap_axis(P):
    """Design coordinates round the cap's upright axis: (angle from his front, distance from the axis, z)."""
    Q = hinv(P)
    x, y = Q[:, 0], Q[:, 1] - F(0.03)
    return np.arctan2(x, -y), np.sqrt(x * x + y * y), Q[:, 2]


PEAK_R0 = 0.17                         # the peak: from inside the band (design units, from the cap's axis) ...
PEAK_L = 0.135                          # ... out this far at its middle
PEAK_A = 1.0                          # half the angle it spans
PEAK_Z = 1.85                          # its root's height (design units) and its slope down
PEAK_SLOPE = 0.3


def peak_d(P):
    a, r, z = _cap_axis(P)
    zc = F(PEAK_Z) - (r - F(PEAK_R0)) * F(PEAK_SLOPE) + F(0.02) * (a / F(PEAK_A)) ** 2
    rmax = F(PEAK_R0) + F(PEAK_L) * np.sqrt(np.clip(F(1) - (a / F(PEAK_A)) ** 2, 0, 1))
    outline = np.maximum(np.maximum(F(PEAK_R0 - 0.04) - r, r - rmax), np.abs(a) - F(PEAK_A))
    return np.maximum(outline, np.abs(z - zc) - F(0.0065)) * F(HS)


def cap_field():
    """Navy-and-white ticking (navy label 0, white stripes 6): a soft crown puffed out over his brow and gathered into a
    band, a short stiff peak, a cloth button on top."""
    fd = Field("Cap")
    lo, hi = HEAD_C + v3((-0.3, -0.36, -0.12)), HEAD_C + v3((0.3, 0.3, 0.32))
    sk = skull()
    cloth = lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.0008) * np.sin(_cap_axis(P)[0] * F(52))
    crown = Ellipsoid(hp((0.0, -0.03, 1.85)), v3((0.226, 0.25, 0.15)) * HS)
    def body(P):
        b = smin(crown(P), sk(P) - F(CAP_IN + 0.018), F(0.03))
        b = np.maximum(b, -(sk(P) - F(CAP_IN)))                                           # (its inside, over his head)
        return np.maximum(b, -band_d(P) * F(HS) - F(BAND_H * HS))                         # its foot = the band's foot
    fd.add(Func(body, lo, hi, disp=cloth, disp_amp=0.0015), 0.0)
    # the band, proud of the crown
    def band(P):
        d = sk(P)
        return np.maximum(np.abs(d - F(CAP_IN + 0.026)) - F(0.008), np.abs(band_d(P)) - F(BAND_H))
    fd.add(Inter(Func(band, lo, hi), Func(lambda P: -(sk(P) - F(CAP_IN)), lo, hi), 0.002), 0.004)
    # the peak, and the button on top
    fd.add(Func(peak_d, lo, hi), 0.008)
    top = hp((0.0, -0.03, 1.85 + 0.15)) + v3((0, 0, -0.004))
    fd.add(Ellipsoid(top, (0.022, 0.022, 0.012)), 0.006)
    # ticking: white stripes running up the crown and band, along the peak
    def stripes(P):
        a, r, z = _cap_axis(P)
        s = np.sin(a * F(30))
        crown_s = F(0.62) - s
        pk = np.sin(r * F(170) + a * F(0.0))
        on_peak = (peak_d(P) < F(0.004)) & (z < F(PEAK_Z + 0.01))
        return np.where(on_peak, F(0.55) - np.sin(a * F(30)), crown_s) * F(0.004)
    fd.paint(Func(stripes, lo, hi), 6)
    return fd


# ======================================================================================= the clothes' bodies
def torso_hull():
    """His torso as the clothes lie on it: the chest smoothed over (no pectorals), the shoulders' tops, the hips and the tops
    of his thighs."""
    b = Field("TorsoHull")
    for i, (p, k) in enumerate(torso_prims()):
        if i in (2, 3):
            continue
        b.add(p, k)
    b.add(Ellipsoid((0, -0.06, 1.26), (0.29, 0.18, 0.2)), 0.06)
    b.add(traps(), 0.06)
    b.add(RoundCone((0, 0.035, 0.98), (0, 0.035, 0.6), 0.26, 0.34), 0.08)
    return b


NECK_A = v3((0.0, 0.065, 1.34))
NECK_B = v3(hp((0.0, 0.02, 1.575)))


def neck_dist(P):
    ax = norm(NECK_B - NECK_A)
    q = P - NECK_A.astype(F)
    t = q @ ax.astype(F)
    c = q - t[:, None] * ax.astype(F)
    return np.sqrt((c * c).sum(1))


def neck_open(P, r=0.14):
    """> 0 inside the opening round his neck (the cut follows the neck, never the level of his shoulders)."""
    return np.where(P[:, 2] > F(1.33), F(r) - neck_dist(P), F(-1.0))


def arm_hull(side, upper_only=False):
    af = Field("Arm" + side)
    for i, (p, k) in enumerate(arm_prims(side)):
        if upper_only and i in (3, 4):
            continue
        af.add(p, k if af.ops else 0.0)
    return af


SLEEVE_END = -0.005                    # the rolled sleeves end this far past his elbows (along the forearm)


def _fore_along(P, side):
    """(distance along the forearm from the elbow, distance from its axis)."""
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    q = P - el.astype(F)
    along = q @ ax.astype(F)
    off = np.sqrt(np.maximum((q * q).sum(1) - along * along, 0))
    return along, off


def _sleeve_end(P):
    """> 0 past the sleeves' ends (only near each arm: the cut serves the sleeve and nothing else)."""
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        along, off = _fore_along(P, side)
        out = np.maximum(out, np.where((off < F(0.2)) & (along > F(-0.2)), along - F(SLEEVE_END), F(-1.0)))
    return out


SHIRT_OFF, SHIRT_T = 0.02, 0.013


def shirt_hull():
    th = torso_hull()
    b = Field("ShirtHull")
    b.add(Func(lambda P: th.eval(P, margin=0.06), (-0.6, -0.5, 0.5), (0.6, 0.6, 1.62)), 0.0)
    for side in ("R", "L"):
        af = arm_hull(side)
        alo, ahi = af.bounds()
        b.add(Func(lambda P, af=af: af.eval(P, margin=0.06) + F(0.004), alo - 0.05, ahi + 0.05), 0.05)
    return b


def shirt_field():
    """Navy wool (label 0): the work shirt, open at the neck, tucked into the overalls, its sleeves rolled up above his
    elbows in thick rolls."""
    fd = Field("Shirt")
    base = shirt_hull()
    folds = lambda P: F(0.0012) * NOISE(P * F(22)) + F(0.002) * NOISE(P * F(6))
    keep = lambda P: np.maximum(np.maximum(neck_open(P, 0.15), _sleeve_end(P)), F(0.92) - P[:, 2])
    fd.add(Inter(Func(keep, (-0.86, -0.42, 0.9), (0.86, 0.42, 1.62)), Shell(base, SHIRT_OFF, SHIRT_T, pad=0.1, disp=folds, disp_amp=0.004),
                 0.004), 0.0)
    # the rolled sleeves: two fat rolls at each sleeve's end
    for side in ("R", "L"):
        el = J["elbow_" + side]
        af = arm_hull(side)
        for j, (c0, w, off) in enumerate(((SLEEVE_END - 0.022, 0.024, 0.042), (SLEEVE_END - 0.062, 0.022, 0.038))):
            roll = lambda P, side=side, c0=c0, w=w: np.maximum(np.abs(_fore_along(P, side)[0] - F(c0)) - F(w), _fore_along(P, side)[1] - F(0.2))
            fd.add(Inter(Func(roll, el - 0.3, el + 0.3), Shell(af, off, 0.03, pad=0.08,
                                                                 disp=lambda P: F(0.002) * NOISE(P * F(25)), disp_amp=0.003), 0.012), 0.008)
    return fd


# ---------------------------------------------------------------------------------------------- the overalls
OV_OFF, OV_T = 0.04, 0.015            # the bib and waist over the shirt
LEG_OFF, LEG_T = 0.036, 0.014          # the trouser legs, loose
HEM_Z = 0.25
BIB_TOP = 1.29


def legs_hull():
    b = Field("Legs")
    tp = torso_prims()
    b.add(tp[5][0], 0.0)
    b.add(tp[4][0], tp[4][1])
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            b.add(p, k)
    return b


def bib_w(z):
    return F(0.165) + F(0.06) * smoothstep(1.12, 0.98, z)


def bib_top(x):
    return F(BIB_TOP) - F(0.03) * (x / F(0.165)) ** 2


def _waist(P):
    return F(1.0) + F(0.05) * smoothstep(-0.02, 0.15, P[:, 1])


def overalls_keep(P):
    """< 0 on the overalls above the legs: the waist all round, the bib up the front of his chest."""
    z, x, y = P[:, 2], P[:, 0], P[:, 1]
    bib = np.where(y < F(0.04), np.maximum(np.abs(x) - bib_w(z), z - bib_top(x)), F(1.0))
    return np.maximum(np.minimum(z - _waist(P), bib), F(0.78) - z)


def strap_path(sx):
    """One shoulder strap (design: from the bib's top corner up over his shoulder, down his back crossing to the other
    side of his waist), as points on the overall's outer surface with their normals."""
    sh = shirt_hull()
    outer = Field("StrapHull")
    outer.add(Func(lambda P: sh.eval(P, margin=0.1) - F(SHIRT_OFF + SHIRT_T * 0.5 + 0.012), (-0.8, -0.6, 0.8), (0.8, 0.7, 1.7)), 0.0)
    raw = [(sx * 0.14, -0.3, BIB_TOP - 0.015), (sx * 0.145, -0.25, 1.37), (sx * 0.16, -0.12, 1.47), (sx * 0.165, 0.04, 1.52),
           (sx * 0.15, 0.2, 1.46), (sx * 0.11, 0.3, 1.32), (sx * 0.04, 0.32, 1.2), (-sx * 0.05, 0.32, 1.1), (-sx * 0.11, 0.3, 1.02)]
    pts = project_to(outer, [v3(p) for p in raw], iters=4)
    nrm = [norm(grad(outer, np.array([p], F))[0]) for p in pts]
    return [v3(p) for p in pts], [v3(n) for n in nrm]


def overalls_field():
    """Denim (label 0) with orange top-stitching (6): the bib and waist over the shirt, the shoulder straps crossing on his
    back, the trouser legs loose and turned up at the hem, a patch pocket on the bib (its mouth on his left)."""
    fd = Field("Overalls")
    th = torso_hull()
    lh = legs_hull()
    wr = lambda P: F(0.0014) * NOISE(P * F(26)) + F(0.0022) * NOISE(P * np.array([6, 6, 3], F))
    fd.add(Inter(Func(overalls_keep, (-0.5, -0.45, 0.76), (0.5, 0.45, 1.33)), Shell(th, OV_OFF, OV_T, pad=0.1, disp=wr, disp_amp=0.004), 0.004), 0.0)
    fd.add(Inter(Func(lambda P: np.maximum(F(HEM_Z) - P[:, 2], P[:, 2] - F(0.99)), (-0.42, -0.36, HEM_Z - 0.02), (0.42, 0.36, 1.0)),
                 Shell(lh, LEG_OFF, LEG_T, pad=0.1, disp=wr, disp_amp=0.004), 0.004), 0.006)
    # the turned-up hems
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(HEM_Z + 0.022)) - F(0.022), (-0.42, -0.36, 0.15), (0.42, 0.36, 0.4)),
                 Shell(lh, LEG_OFF + 0.012, 0.016, pad=0.1), 0.005), 0.005)
    # the straps
    for sx in (-1, 1):
        pts, nrm = strap_path(sx)
        pts = [p + n * 0.004 for p, n in zip(pts, nrm)]
        fd.add(Lock(pts, [0.03] * len(pts), [0.0075] * len(pts), nrm, k=0.004), 0.004)
    # the bib pocket (on his left chest)
    po, pn = pocket_frame()
    side = norm(np.cross(v3((0, 0, 1)), pn))
    up = np.cross(pn, side)
    Rp = np.stack([side, up, pn], 1)
    fd.add(RoundBox(po, (0.062, 0.058, 0.006), 0.004, R=Rp), 0.003)
    # top-stitching: the bib's top edge and sides, the pocket's edges, the outside seams of the legs
    def stitch(P):
        z, x = P[:, 2], P[:, 0]
        top = np.maximum(np.abs(z - (bib_top(x) - F(0.014))) - F(0.0035), np.maximum(np.abs(x) - bib_w(z), P[:, 1] - F(0.0)))
        sides = np.maximum(np.abs(np.abs(x) - (bib_w(z) - F(0.014))) - F(0.0035),
                           np.maximum(np.maximum(z - bib_top(x) + F(0.012), F(1.0) - z), P[:, 1] - F(0.0)))
        q = P - po.astype(F)
        s, u = q @ side.astype(F), q @ up.astype(F)
        pk = np.maximum(np.abs(np.maximum(np.abs(s) - F(0.046), np.abs(u) - F(0.042))) - F(0.0035), np.abs(q @ pn.astype(F)) - F(0.03))
        leg = np.full(len(P), F(1.0))
        for sd in ("R", "L"):
            hx = J["hip_" + sd][0]
            leg = np.minimum(leg, np.maximum(np.abs(P[:, 0] - F(hx * 1.95)) - F(0.0035), np.maximum(z - F(0.9), np.abs(P[:, 1] - F(0.03)) - F(0.05))))
        return np.minimum(np.minimum(top, sides), np.minimum(pk, leg))
    fd.paint(Func(stitch, (-0.5, -0.45, 0.1), (0.5, 0.45, 1.34)), 6)
    return fd


def pocket_frame():
    """The bib pocket's middle and outward normal (on his left chest)."""
    th = torso_hull()
    outer = Func(lambda P: th.eval(P, margin=0.1) - F(OV_OFF + OV_T * 0.5 + 0.004), (-0.8, -0.8, 0.8), (0.8, 0.8, 1.6))
    h, ok = ray_hit(outer, [v3((0.075, -0.7, 1.16))], [v3((0, 1, 0))], tmax=0.8)
    p = h[0] if ok[0] else v3((0.075, -0.27, 1.16))
    e = 0.004
    g = np.array([(outer(np.array([p + d], F))[0] - outer(np.array([p - d], F))[0]) / (2 * e) for d in np.eye(3) * e])
    return p, norm(g)


def button_spots():
    """(centre, normal) of the brass buttons: one where each strap meets the bib, two at each hip."""
    out = []
    for sx in (-1, 1):
        pts, nrm = strap_path(sx)
        out.append((pts[0] + nrm[0] * 0.012 + v3((0, 0, -0.008)), nrm[0]))
    th = torso_hull()
    outer = Func(lambda P: th.eval(P, margin=0.1) - F(OV_OFF + OV_T * 0.5 + 0.002), (-0.8, -0.8, 0.8), (0.8, 0.8, 1.6))
    for sx in (-1, 1):
        for z in (0.985, 0.925):
            d = norm(v3((sx * 1.0, -0.45, 0.0)))
            o = v3((0.0, 0.0, z)) + d * 0.7
            h, ok = ray_hit(outer, [o], [-d], tmax=0.8)
            if ok[0]:
                out.append((h[0], d))
    return out


# ---------------------------------------------------------------------------------------------- neckerchief
def kerchief_field():
    """Red cotton (label 0) with white spots (6): rolled round his neck, knotted at the left of his throat, its two ends
    hanging out over his collarbone."""
    fd = Field("Kerchief")
    nk = Field("Neck")
    for p, kk in torso_prims():
        nk.add(p, kk)
    nk.add(traps(), 0.06)
    nk.add(neck_prim(), 0.05)
    def band(P):
        zc = F(1.45) - F(0.06) * smoothstep(0.02, -0.12, P[:, 1])
        return np.maximum(np.abs(P[:, 2] - zc) - F(0.04), neck_dist(P) - F(0.21))
    roll = lambda P: F(0.003) * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(0.06)) * F(9)) + F(0.0015) * NOISE(P * F(30))
    fd.add(Inter(Func(band, (-0.2, -0.2, 1.28), (0.2, 0.26, 1.52)), Shell(nk, 0.038, 0.036, pad=0.08, disp=roll, disp_amp=0.004), 0.008), 0.0)
    k = KNOT
    fd.add(Ellipsoid(k, (0.042, 0.036, 0.036), R=euler(0, 0.3, 0.6)), 0.012)
    for d, L, w in ((v3((0.55, -0.45, -0.7)), 0.13, 0.05), (v3((0.15, -0.6, -0.78)), 0.12, 0.046)):
        d = norm(d)
        pts = [k + d * 0.01, k + d * L * 0.5 + v3((0, -0.006, 0)), k + d * L]
        fd.add(Lock(pts, [w * 0.5, w * 0.9, w * 0.25], [0.01, 0.008, 0.005], [norm(v3((0.2, -1, 0.3)))] * 3, k=0.006), 0.008)
    def spots(P):
        q = P * F(1.0 / 0.024)
        c = np.floor(q) + F(0.5)
        return (np.sqrt(((q - c) ** 2).sum(1)) - F(0.24)) * F(0.024)
    fd.paint(Func(spots, (-0.3, -0.3, 1.1), (0.3, 0.3, 1.6)), 6)
    return fd


KNOT = v3((0.19, -0.06, 1.37))


# ---------------------------------------------------------------------------------------------- leather: gauntlets, boots
def leather_field():
    """Brown leather gauntlet cuffs (label 0), flaring from his wrists halfway up his forearms, a stitched seam (5) round
    each top; a dark leather strap (5) at each wrist with a brass stud (6)."""
    fd = Field("Leather")
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        a, b = wr + ax * 0.012, wr - ax * 0.15
        outer = RoundCone(a, b, 0.07, 0.106)
        inner = RoundCone(a + ax * 0.03, b - ax * 0.03, 0.058, 0.094)
        wrinkle = lambda P: F(0.002) * NOISE(P * F(30))
        cuff = Field("Cuff")
        cuff.add(outer, 0.0)
        cuff.sub(inner, 0.004)
        clo, chi = cuff.bounds()
        fd.add(Func(lambda P, cuff=cuff: cuff.eval(P), clo - 0.02, chi + 0.02, disp=wrinkle, disp_amp=0.003), 0.0)
        fd.add(Torus(b + ax * 0.012, 0.104, 0.007, R=rot_from_axes(z_axis=ax)), 0.004, 5)
        fd.add(Torus(wr - ax * 0.03, 0.078, 0.009, R=rot_from_axes(z_axis=ax)), 0.004, 5)
    return fd


BOOT_TOP = 0.31


def boot_hull(side):
    b = Field("BootHull")
    foot(b, side)
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    b.add(RoundCone(kn, an, 0.09, 0.06), 0.03)
    return b


def boots_field():
    """Big brown work boots (label 0) to above his ankles, thick soles and heels, a broad toe cap, hobnails round the soles
    and brass lace hooks (6)."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        bh = boot_hull(side)
        crease = lambda P: F(0.0016) * NOISE(P * F(28))
        fd.add(Inter(Shell(bh, 0.016, 0.018, pad=0.06, disp=crease, disp_amp=0.002),
                     Func(lambda P: P[:, 2] - F(BOOT_TOP), an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.3))), 0.006), 0.0)
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.094)), (0.088, 0.17, 0.016), 0.01, R=Rz), 0.008)          # the sole
        fd.add(RoundBox(an + fwd * -0.02 + v3((0, 0, -0.082)), (0.07, 0.058, 0.028), 0.01, R=Rz), 0.006)        # the heel
        fd.add(Ellipsoid(an + fwd * 0.16 + v3((0, 0, -0.058)), (0.084, 0.08, 0.05), R=Rz), 0.03)                # a broad toe cap
        # hobnails round the sole's edge
        for k in range(18):
            u = k / 18.0 * 2 * math.pi
            p = an + fwd * (0.08 + 0.158 * math.sin(u)) + (Rz @ v3((1, 0, 0))) * (0.082 * math.cos(u)) + v3((0, 0, -0.1))
            fd.add(Sphere(p, 0.0075), 0.002, 6)
        # brass lace hooks up the front
        for k in range(3):
            z = 0.16 + 0.05 * k
            for s2 in (-1, 1):
                c = an + fwd * (0.075 - 0.012 * k) + (Rz @ v3((1, 0, 0))) * (s2 * 0.034) + v3((0, 0, z - an[2]))
                h, ok = ray_hit(Func(lambda P, bh=bh: bh.eval(P, margin=0.1) - F(0.026), an - 0.4, an + 0.4), [c + fwd * 0.3], [-fwd], tmax=0.4)
                if ok[0]:
                    fd.add(Sphere(h[0], 0.009), 0.002, 6)
    return fd


# ---------------------------------------------------------------------------------------------- brass: buttons, the pocket watch
def watch_frame():
    """The pocket watch: its case standing up out of the bib pocket's mouth (its middle, normal, up)."""
    po, pn = pocket_frame()
    side = norm(np.cross(v3((0, 0, 1)), pn))
    up = np.cross(pn, side)
    c = po + up * 0.06 + pn * 0.012 - side * 0.006
    return c, pn, up, side


WATCH_R = 0.032


def brass_field():
    """Brass: the overalls' buttons; the pocket watch (a domed case, its crown and bow) on a short chain to the left
    strap's button."""
    fd = Field("Brass")
    for p, d in button_spots():
        fd.add(Cylinder(p, 0.016, 0.009, rr=0.0045, R=rot_from_axes(z_axis=d)), 0.0)
        fd.add(Sphere(p + d * 0.003, 0.009), 0.004)
    c, n, up, side = watch_frame()
    Rw = np.stack([side, up, n], 1)
    fd.add(Inter(Ellipsoid(c, (WATCH_R, WATCH_R, 0.016), R=Rw), Cylinder(c, WATCH_R + 0.01, 0.022, R=rot_from_axes(z_axis=n)), 0.003), 0.0)
    fd.add(Torus(c, WATCH_R - 0.002, 0.0035, R=rot_from_axes(z_axis=n)), 0.002)
    crown = c + up * (WATCH_R + 0.006)
    fd.add(Cylinder(crown, 0.0065, 0.012, rr=0.002, R=rot_from_axes(z_axis=up)), 0.002)
    bow = crown + up * 0.012
    fd.add(Torus(bow, 0.011, 0.0028, R=rot_from_axes(z_axis=side)), 0.002)
    # the chain, in a sagging loop up to the left strap's button
    btn = [p for p, d in button_spots()][1]
    a, b = bow + up * 0.01, btn
    pts = []
    for k in range(13):
        t = k / 12.0
        pts.append(a + (b - a) * t + v3((0, 0, -0.03 * math.sin(math.pi * t))) + n * (0.006 * math.sin(math.pi * t)))
    for k in range(len(pts) - 1):
        m = (pts[k] + pts[k + 1]) / 2
        d = norm(pts[k + 1] - pts[k])
        fd.add(Torus(m, 0.0055, 0.0018, R=rot_from_axes(z_axis=norm(np.cross(d, n)) if k % 2 else n, y_axis=d)), 0.0015)
    return fd


# ======================================================================================= the spike maul (rigid on `maul`)
MAUL_L = 0.92          # grip -> the head's centre, along the handle
MAUL_BUTT = 0.15       # grip -> the end of the handle
MAUL_R = 0.022         # the handle's radius at the grip
HEAD_HALF = 0.23       # the head: centre -> each driving face
FACE_R = 0.034         # the faces' radius


def maul_frame():
    """Rest pose: the grip (his right fist), the handle along the fist's thumb axis A (toward the head), the head's long
    axis along B (the fist's knuckles: one face strikes that way)."""
    wr, f, n, t = hand_frame("R")
    A = norm(t)
    B = norm(f - A * (f @ A))
    return fist_center("R"), A, B


def maul_head():
    G, A, B = maul_frame()
    return G + A * MAUL_L


def maul_face():
    """The striking face's middle (rest pose)."""
    G, A, B = maul_frame()
    return maul_head() + B * HEAD_HALF


def maul_field():
    """An ash handle (label 0), swelling toward the head, a leather grip bound round its butt (5); the forged iron head (8):
    a square eye round the handle, long tapering arms to two narrow round driving faces with chamfered rims, a steel wedge
    (7) in the top of the eye."""
    fd = Field("Maul")
    G, A, B = maul_frame()
    S = norm(np.cross(A, B))
    grain = lambda P: F(0.0016) * NOISE(P * np.array([70.0, 70.0, 70.0], F))
    fd.add(RoundCone(G - A * (MAUL_BUTT - 0.02), G + A * (MAUL_L - 0.02), MAUL_R, MAUL_R * 1.2, disp=grain, disp_amp=0.002), 0.0)
    fd.add(Ellipsoid(G - A * MAUL_BUTT, (0.03, 0.03, 0.024), R=rot_from_axes(z_axis=A)), 0.01)                   # the swelled butt
    for k in range(7):                                                                                          # leather grip
        fd.add(Torus(G - A * (0.115 - 0.022 * k), MAUL_R + 0.003, 0.0065, R=rot_from_axes(z_axis=A)), 0.002, 5)
    hc = maul_head()
    R = np.stack([S, A, B], axis=1)
    fd.add(RoundBox(hc, (0.05, 0.058, 0.062), 0.014, R=R), 0.0, 8)                                              # the eye
    for s in (-1, 1):
        face = hc + B * (s * HEAD_HALF)
        fd.add(RoundCone(hc + B * (s * 0.04), face - B * (s * 0.02), 0.05, FACE_R + 0.004), 0.012, 8)
        fd.add(Cylinder(face - B * (s * 0.01), FACE_R, 0.02, rr=0.006, R=rot_from_axes(z_axis=B)), 0.006, 8)
        fd.add(Torus(face - B * (s * 0.03), FACE_R + 0.004, 0.005, R=rot_from_axes(z_axis=B)), 0.004, 8)
    fd.add(RoundBox(hc + A * 0.058, (0.006, 0.006, 0.042), 0.003, R=R), 0.002, 7)                            # the wedge
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.62)), 0.05, 0.55)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.115, -0.15, 1.632)), 0.07, 0.75), (hp((sx * 0.18, 0.035, 1.664)), 0.055, 0.55),
                (J["elbow_" + sd] + v3((0, 0.03, 0)), 0.06, 0.25)]
    return pts


# ======================================================================================= build config
GLB_NAME = "jim"
ROOT_NAME = "HeroJimHQ"
TEX_PREFIX = "hero"
MAT_NAME = "JimMat"
MESH_NAME = "Jim"
BASE_MODULE = "jim_base"
ANIM_MODULE = "anim_jim"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Cap", "Shirt", "Overalls", "Kerchief", "Leather", "Boots", "Brass", "Maul"]
REGION_PARTS = ("Skin", "Cap", "Overalls", "Kerchief", "Leather", "Boots", "Maul")
BLACK_HAIR = {"name": "HQ_JimHair", "base": (0.07, 0.06, 0.055), "hi": (0.3, 0.27, 0.25), "low": (0.03, 0.026, 0.024),
              "streak": (0.05, 0.042, 0.038), "tint": (0.13, 0.11, 0.1), "fleck": (0.62, 0.6, 0.58), "fleck_amt": 0.55}
BRASS = {"name": "HQ_JimBrass", "base": (0.8, 0.55, 0.22), "hi": (1.0, 0.9, 0.56), "dark": (0.38, 0.24, 0.08), "patina": (0.42, 0.44, 0.24)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_JimSkin", "base": (0.84, 0.6, 0.46), "ruddy": (0.92, 0.46, 0.36), "lips": (0.66, 0.3, 0.27),
                      "brow": ((0.05, 0.045, 0.04), (0.3, 0.28, 0.26)),
                      "extra": ((LASH, (0.04, 0.03, 0.025), 0.5), (SOOT, (0.13, 0.12, 0.12), 0.7, 0.8),
                                (GLOVE, GLOVE_C, 0.6))}),
    "Hair": ("hair", BLACK_HAIR),
    "Beard": ("hair", dict(BLACK_HAIR, name="HQ_JimBeard")),
    "Cap": ("wool", {"name": "HQ_JimCap", "base": NAVY, "border": TICK_W, "stripe": TICK_W}),
    "Shirt": ("wool", {"name": "HQ_JimShirt", "base": NAVY, "border": NAVY, "stripe": NAVY}),
    "Overalls": ("wool", {"name": "HQ_JimOveralls", "base": DENIM, "border": STITCH, "stripe": STITCH}),
    "Kerchief": ("wool", {"name": "HQ_JimKerchief", "base": KERCHIEF, "border": SPOTS, "stripe": SPOTS}),
    "Leather": ("leather_dyed", {"name": "HQ_JimGauntlets", "base": GLOVE_C, "dyed": (0.24, 0.14, 0.08), "worn_c": (0.7, 0.5, 0.3)}),
    "Boots": ("leather_dyed", {"name": "HQ_JimBoots", "base": (0.3, 0.18, 0.1), "dyed": (0.16, 0.1, 0.06), "worn_c": (0.56, 0.4, 0.26)}),
    "Brass": ("bronze", BRASS),
    "Maul": ("armory", {"name": "HQ_SpikeMaul", "wood": (0.68, 0.52, 0.33), "wood2": (0.52, 0.38, 0.22), "grip": (0.2, 0.12, 0.07)}),
}
LOW_TARGETS = {"Skin": 6800, "Teeth": 120, "Hair": 500, "Beard": 2100, "Cap": 1500, "Shirt": 2300, "Overalls": 3400,
               "Kerchief": 700, "Leather": 700, "Boots": 1300, "Brass": 700, "Maul": 900}
AO_EXCLUDE = ["Maul", "Brass"]


def prop_bones():
    G, A, B = maul_frame()
    return [("maul", G, G + A * 0.3, "hand.R")]


CLOTH = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}


def _rigid(ob, groups, v, w):
    for g in list(ob.vertex_groups):
        g.remove([v.index])
    _blend_add(ob, groups, v.index, w)


def beard_weights(ob, skin_ob, arm):
    """The beard goes with his head and jaw; its bulk on his chest blends into his neck and chest."""
    groups = {}
    z1 = hp((0, 0, 1.47))[2]
    for v in ob.data.vertices:
        p = v.co
        if p.z >= z1:
            _blend_add(ob, groups, v.index, {"head": 1.0})
        else:
            t = max(0.0, min(1.0, (z1 - p.z) / 0.16))
            _blend_add(ob, groups, v.index, {"head": 1.0 - 0.6 * t, "neck": 0.4 * t, "chest": 0.2 * t})


def brass_weights(ob, skin_ob, arm):
    """Buttons with his torso (and hips); the watch and its chain with his chest."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO)
    c, n, up, side = watch_frame()
    groups = {}
    for v in ob.data.vertices:
        if v.co.z > 1.12 and abs(v.co.x) < 0.2 and v.co.y < -0.1:
            _rigid(ob, groups, v, {"chest": 1.0})


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Cap": ("rigid", "head"),
        "Beard": ("custom", beard_weights),
        "Shirt": ("transfer", CLOTH, None),
        "Overalls": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Kerchief": ("transfer", {"neck", "chest", "head"}, None),
        "Leather": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Boots": ("transfer", {"foot.R", "foot.L", "shin.R", "shin.L"}, None),
        "Brass": ("custom", brass_weights),
        "Maul": ("rigid", "maul"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.8
    if part == "Cap" and c.y < -0.05:
        return 1.3
    if part == "Maul":
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.003),
        ("Beard", beard_field(), 0.0024 if fine else 0.0034),
        ("Cap", cap_field(), 0.0024 if fine else 0.0034),
        ("Shirt", shirt_field(), 0.0026 if fine else 0.0036),
        ("Overalls", overalls_field(), 0.0026 if fine else 0.0036),
        ("Kerchief", kerchief_field(), 0.002 if fine else 0.003),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Boots", boots_field(), 0.0024 if fine else 0.0032),
        ("Brass", brass_field(), 0.0016 if fine else 0.0022),
        ("Maul", maul_field(), 0.002 if fine else 0.0028),
    ]
