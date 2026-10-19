"""Tarek the Smith, Forge Master (HQ hero). Rest pose = A-pose, facing -Y, feet at z=0; right side = -X.

A big, broad-chested smith with a booming laugh: a broad flat nose, bushy brows, a short thick curly black beard trimmed
round, black hair tied up in a knot, a leather sweat-band, soot smeared on his cheeks and forearms; a heavy leather
apron from his chest to his knees (a neck strap, a pocket with tongs' handles poking out) over a short ochre kilt; thick
leather wrist wraps, bronze armlets, sandals. In his right fist a smith's hammer: an ash handle and a bronze head, its
striking face glowing red-hot (the hot head ships as its own glowing mesh on the `hammer` bone, so the whole hammer can
be hidden when he throws it and appear again in his hand).

The hammer is rigid on the `hammer` bone, a child of his right hand ("frame" aims in anim_tarek.py: the handle along the
fist's thumb axis, the striking face along the knuckles)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, grad, project_to, flow_line, Stone, lerp
from ugo import _blend_add

J = {
    "root": (0.0, 0.03, 0.8),
    "spine": (0.0, 0.03, 0.96),
    "chest": (0.0, 0.05, 1.16),
    "neck": (0.0, 0.065, 1.4),
    "head": (0.0, 0.02, 1.52),
    "head_end": (0.0, -0.02, 1.92),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.355, 0.07, 1.36)
    J["elbow_" + _s] = (_x * 0.575, 0.1, 1.1)
    J["wrist_" + _s] = (_x * 0.725, 0.04, 0.86)
    J["hip_" + _s] = (_x * 0.16, 0.04, 0.75)
    J["knee_" + _s] = (_x * 0.18, 0.0, 0.42)
    J["ankle_" + _s] = (_x * 0.19, 0.06, 0.11)
    J["toe_" + _s] = (_x * 0.21, -0.17, 0.035)
J = {k: v3(v) for k, v in J.items()}

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, SOOT = 0, 1, 2, 3, 4, 5, 8, 9

HS = 1.08
DZ = -0.04
HPIV = v3((0.0, 0.02, 1.46))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


def hinv(P):
    return (P - HPIV.astype(F)) / F(HS) + HPIV.astype(F) - np.array([0, 0, DZ], F)


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.18, 0.19, 0.186)) * HS
EYE_R = hr(0.037)


def eye_c(sx):
    return hp((sx * 0.07, -0.146, 1.674))


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


# ======================================================================================= hands & feet
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


HAND_S = 1.07
CURLS = {"R": (1.45, 1.6, 1.2), "L": (0.6, 0.8, 0.6)}       # right fist round the hammer, left hand half open


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    fist = side == "R"
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
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.011, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.016 * s), 0.009, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.012, (0.012, 0.007, 0.015), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.052 * s + n * 0.011
    if fist:
        d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
        d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:
        d1 = norm(f * 0.55 + t * 0.7 + n * 0.3)
        d2 = norm(f * 0.6 + t * 0.35 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.026 * s, 0.023 * s, 0.02 * s], k=0.008), 0.018, SKIN)


def foot(fd, side, s=1.06):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.12)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    fd.add(Sphere(an + v3((0, 0.042, -0.05)), 0.06 * s), 0.028, SKIN)
    fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.07)), v3((0.068, 0.118, 0.035)) * s, 0.032, R=Rz), 0.031, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.036 + v3((0, 0, -0.03)), v3((0.065, 0.087, 0.048)) * s, R=Rz), 0.028, SKIN)
    inner = -sx
    for i, (o, r) in enumerate(((0.051, 0.028), (0.021, 0.022), (-0.005, 0.02), (-0.029, 0.018), (-0.049, 0.017))):
        base = an + fwd * (0.164 - 0.011 * i - (0.0 if i else -0.004)) + rgt * (o * inner) + v3((0, 0, -0.08))
        tip = base + fwd * (0.029 + r * 0.4) + v3((0, 0, -0.004))
        base[2] = 0.024 + r * 0.55
        tip[2] = 0.019 + r * 0.5
        fd.add(RoundCone(base, tip, r, r * 0.92), 0.011, SKIN)
        tn = norm(tip - base)
        fd.paint(Ellipsoid(tip + v3((0, 0, r * 0.55)), (r * 0.7, r * 0.75, r * 0.35), R=rot_from_axes(y_axis=tn, z_axis=(0, 0, 1))), NAIL)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.052, 0.0, 0.0)), 0.025), 0.018, SKIN)


# ======================================================================================= head
def skull():
    fd = Field("Skull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    return fd


def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.052, 1.59), (0.152, 0.138, 0.128)), 0.07, SKIN)                         # a broad jaw (under the beard)
    fd.add(E((0, -0.134, 1.5), (0.09, 0.072, 0.068)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.116, -0.124, 1.63), 0.054), 0.05, SKIN)                             # round, ruddy cheeks
        fd.add(S((sx * 0.13, -0.045, 1.556), 0.052), 0.05, SKIN)
        pts = [hp((sx * 0.156, -0.055, 1.744)), hp((sx * 0.118, -0.134, 1.756)), hp((sx * 0.062, -0.176, 1.754)), hp((0.0, -0.186, 1.75))]
        fd.add(Chain(pts, [hr(0.012), hr(0.019), hr(0.022), hr(0.02)], k=hr(0.022)), hr(0.03), SKIN)
    # forehead creases
    sk = skull()
    for zc in (1.815, 1.84):
        pts = []
        for k in range(9):
            x = -0.08 + 0.16 * k / 8
            h, ok = ray_hit(sk, [hp((x, -0.6, zc + 0.012 * (x / 0.08) ** 2))], [v3((0, 1, 0))], tmax=0.7)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 3:
            fd.sub(Chain(pts, [hr(0.0024)] * len(pts), k=0.002), hr(0.003))
    # bushy brows, raised: a jolly, booming man
    for sx in (-1, 1):
        pts = [hp((sx * 0.026, -0.211, 1.782)), hp((sx * 0.068, -0.206, 1.799)), hp((sx * 0.114, -0.184, 1.799)), hp((sx * 0.156, -0.145, 1.778))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.0095), hr(0.0115), hr(0.0095), hr(0.0045)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.022), hr(0.024), hr(0.021), hr(0.012)], k=hr(0.01)), BROW)
    # eyes crinkled by his smile
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.026))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0062)), Plane(ec + v3((0, 0, -hr(0.016))), (sx * -0.16, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.023))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(3):                                                                      # laughter lines
            a = hp((sx * (0.11 + 0.004 * k), -0.128 + 0.006 * k, 1.68 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.024, 0.012, -0.002 - 0.009 * k)), hr(0.0022), hr(0.0015)), hr(0.003))
    # a broad, flat nose
    fd.add(RoundCone(hp((0, -0.186, 1.726)), hp((0, -0.238, 1.636)), hr(0.02), hr(0.026)), hr(0.018), SKIN)
    fd.add(S((0, -0.238, 1.626), 0.03), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.038, -0.218, 1.61), 0.025), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.02, -0.236, 1.6)), v3((0.01, 0.012, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a wide grin (mostly framed by the beard), teeth showing
    slot = [hp((-0.07, -0.16, 1.568)), hp((-0.04, -0.19, 1.546)), hp((0, -0.2, 1.538)), hp((0.04, -0.19, 1.546)), hp((0.07, -0.16, 1.568))]
    fd.sub(Chain(slot, [hr(0.005), hr(0.011), hr(0.014), hr(0.011), hr(0.005)], k=hr(0.004)), hr(0.004))
    fd.paint(Chain(slot, [hr(0.006), hr(0.0125), hr(0.0155), hr(0.0125), hr(0.006)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.058, -0.166, 1.556), (-0.032, -0.188, 1.53), (0, -0.194, 1.524), (0.032, -0.188, 1.53), (0.058, -0.166, 1.556)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0075), hr(0.0085), hr(0.0075), hr(0.004)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.028, 0.05, 0.064)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.012, 0.032, 0.042)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
    # soot smudged on his cheekbones and brow
    for c, r in (((0.115, -0.15, 1.648), (0.03, 0.02, 0.016)), ((-0.1, -0.16, 1.655), (0.024, 0.018, 0.012)),
                 ((0.05, -0.2, 1.8), (0.03, 0.015, 0.01))):
        fd.paint(Ellipsoid(hp(c), v3(r) * HS * 1.6, R=euler(0.2, 0.0, 0.4)), SOOT)


# ======================================================================================= body (big and broad)
def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.17), (0.28, 0.23, 0.27), R=euler(-0.1, 0, 0)), 0.0),
        (Ellipsoid((0, 0.12, 1.22), (0.31, 0.16, 0.21)), 0.06),
        (Ellipsoid((0.13, -0.14, 1.24), (0.14, 0.06, 0.09), R=euler(0.1, 0, 0.18)), 0.045),
        (Ellipsoid((-0.13, -0.14, 1.24), (0.14, 0.06, 0.09), R=euler(0.1, 0, -0.18)), 0.045),
        (Ellipsoid((0, -0.035, 0.98), (0.235, 0.21, 0.21)), 0.08),
        (Ellipsoid((0, 0.045, 0.8), (0.245, 0.185, 0.16)), 0.08),
    ]


def traps():
    return Ellipsoid((0, 0.1, 1.39), (0.25, 0.14, 0.1), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.065, 1.34), hp((0, 0.02, 1.575)), 0.11, hr(0.09))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.024, -0.005, 0.014)), 0.118)


def upper_arm(side):
    return RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.106, 0.081)


def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.082, 0.06)


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
        # soot up his forearms
        fd.paint(Inter(RoundCone(lerp(el, wr, 0.45), wr + (wr - el) * 0.15, 0.1, 0.09), Func(lambda P, s2=sx: F(0.02) - NOISE(P * F(12)) * F(0.06) - F(0.02), wr - 0.4, wr + 0.4), 0.01), SOOT)
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


def eyes_field():
    fd = Field("Eyes")
    for sx in (-1, 1):
        fd.add(Sphere(eye_c(sx), EYE_R))
    return fd


def teeth_field():
    """Two rows of teeth behind his grin."""
    fd = Field("Teeth")
    for k in range(6):
        x = -0.05 + 0.02 * k
        y = -0.18 + 0.014 * (abs(x) / 0.05) ** 2
        fd.add(RoundBox(hp((x, y, 1.552 + 0.006 * (abs(x) / 0.05) ** 2)), v3((0.0092, 0.006, 0.0085)) * HS, hr(0.003)), 0.002)
    return fd


# ======================================================================================= hair, beard, sweat-band
def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.052, 1.59), (0.152, 0.138, 0.128)), 0.07)
    fd.add(E((0, -0.134, 1.5), (0.09, 0.072, 0.068)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.116, -0.124, 1.63)), hr(0.054)), 0.05)
        fd.add(Sphere(hp((sx * 0.13, -0.045, 1.556)), hr(0.052)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


def _hash3(i, k):
    d = i[:, 0] * F(127.1 + 3.3 * k) + i[:, 1] * F(311.7 - 5.1 * k) + i[:, 2] * F(74.7 + 7.9 * k)
    return np.mod(np.sin(d) * F(43758.5453), F(1.0)).astype(F)


def curls(P, scale=0.022, depth=0.006):
    """Tight round curls: a dome round each point of a jittered lattice (the nearest of its 2x2x2 neighbourhood, so the
    field is continuous), the lattice wandering under a noise warp; positive pushes the surface in."""
    s = F(1.0 / scale)
    W = P + F(scale * 0.7) * np.stack([NOISE(P * s * F(0.3) + F(5.3 * k)) for k in range(3)], 1)
    q = W * s
    b = np.floor(q - F(0.5))
    best = np.zeros(len(P), F)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                i = b + np.array([dx, dy, dz], F)
                c = i + F(0.5) + (np.stack([_hash3(i, k) for k in range(3)], 1) - F(0.5)) * F(0.7)
                r = F(0.46) + F(0.12) * _hash3(i, 5)
                d2 = ((q - c) ** 2).sum(1)
                best = np.maximum(best, np.clip(F(1) - d2 / (r * r), 0, 1))
    return F(depth) * (F(0.45) - np.sqrt(best)) + F(0.0012) * NOISE(P * F(80))


KNOT = hp((0.0, 0.1, 1.94))


def hair_field():
    """Black hair drawn back over his scalp from a receding hairline to a knot on top at the back, curly."""
    fd = Field("Hair")
    hc, hrad = HEAD_C, HEAD_RAD
    pfront, pback = hp((0, -0.13, 1.85)), hp((0, 0.215, 1.6))
    slope = (pback[2] - pfront[2]) / (pback[1] - pfront[1])
    hl_n = norm((0, slope, -1.0))
    hairline = Func(lambda P: ((P - pfront.astype(F)) @ hl_n.astype(F)) + F(0.005) * NOISE(P * F(20)), hc - 0.5, hc + 0.5)
    def temples(P):
        Q = hinv(P)
        return np.where((np.abs(Q[:, 0]) > F(0.15)) & (Q[:, 1] < F(0.06)) & (Q[:, 2] < F(1.74)), F(0.02), F(-1.0))
    fd.add(Inter(Inter(Ellipsoid(hc, hrad + 0.014, disp=lambda P: curls(P, 0.015, 0.0038), disp_amp=0.006), hairline, 0.015),
                 Func(temples, hc - 0.5, hc + 0.5), 0.01), 0.0)
    fd.add(Sphere(KNOT, 0.068, disp=lambda P: curls(P, 0.015, 0.0042), disp_amp=0.007), 0.03)
    return fd


BEARD_LOW = 1.4


def beard_field():
    """A short, thick, curly beard trimmed round, over his cheeks and jaw and a little onto his throat; a thick
    moustache."""
    fd = Field("Beard")
    hull = head_hull()
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.56) + F(0.055) * smoothstep(0.07, 0.16, ax) + F(0.085) * smoothstep(0.135, 0.175, ax) * smoothstep(-0.11, -0.04, y)
        lips = (x / F(0.084)) ** 2 + ((y + F(0.18)) / F(0.07)) ** 2 + ((z - F(1.548)) / F(0.036)) ** 2 - F(1.0)
        back = np.where(ax > F(0.14), y - F(0.035), y - F(0.0))
        return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), F(BEARD_LOW) - z)
    fd.add(Inter(Shell(hull, 0.012, 0.03, pad=0.06, disp=lambda P: curls(P, 0.02, 0.007), disp_amp=0.008), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.01), 0.0)
    fd.add(Ellipsoid(hp((0, -0.15, 1.475)), v3((0.12, 0.075, 0.07)) * HS, disp=lambda P: curls(P, 0.02, 0.007), disp_amp=0.008), 0.04)
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.23, 1.586)), hp((sx * 0.046, -0.216, 1.578)), hp((sx * 0.08, -0.19, 1.566)), hp((sx * 0.098, -0.166, 1.55))]
        fd.add(Lock(pts, [hr(0.015), hr(0.019), hr(0.016), hr(0.009)], [hr(0.011), hr(0.012), hr(0.01), hr(0.0065)],
                    [norm(v3((sx * 0.25, -1, 0.35)))] * 4, k=hr(0.006), disp=lambda P: curls(P, 0.012, 0.003), disp_amp=0.004), hr(0.006))
    return fd


BAND_F = v3((0.0, -0.18, 1.83))
BAND_B = v3((0.0, 0.2, 1.75))
_BAND_N = norm(v3((0, -(BAND_B[2] - BAND_F[2]) / (BAND_B[1] - BAND_F[1]), 1.0)))


def band_d(P):
    return (hinv(P) - BAND_F.astype(F)) @ _BAND_N.astype(F)


# ======================================================================================= apron, kilt, leather, bronze
def apron_base():
    b = Field("ApronBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(RoundCone((0, 0.03, 0.9), (0, 0.03, 0.42), 0.25, 0.31), 0.09)
    return b


APRON_W = 0.2               # half width at the chest
APRON_HEM = 0.44


def apron_keep(P):
    """< 0 on the apron: a bib over his chest up to under the collarbones, widening over the belly and down past his
    knees, front only."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    w = F(APRON_W) + F(0.08) * smoothstep(1.2, 0.95, z)
    side = np.abs(x) - w
    top = z - F(1.36) + F(0.06) * (np.abs(x) / F(0.2)) ** 2
    front = y - F(0.02)
    hem = F(APRON_HEM) - z + F(0.008) * NOISE(P * F(9))
    return np.maximum(np.maximum(np.maximum(side, top), front), hem)


def leather_field():
    """The heavy apron (label 0, scorched dark in places: 5) with its neck strap and a pocket with tongs' handles poking
    out; the sweat-band, wrist wraps, sandals and the belt that ties the apron (label 6 = its bronze ring)."""
    fd = Field("Leather")
    base = apron_base()
    creases = lambda P: F(0.003) * NOISE(P * np.array([10, 10, 22], F)) + F(0.0012) * NOISE(P * F(40))
    fd.add(Inter(Shell(base, 0.03, 0.02, pad=0.1, disp=creases, disp_amp=0.005), Func(apron_keep, (-1, -1, 0.3), (1, 1, 1.5)), 0.006), 0.0)
    for c, r in (((0.08, -0.28, 0.82), (0.07, 0.03, 0.05)), ((-0.12, -0.26, 1.02), (0.05, 0.03, 0.04)), ((0.02, -0.26, 0.6), (0.06, 0.03, 0.04))):
        fd.paint(Ellipsoid(v3(c), r), 5)
    # neck strap over his shoulders
    for sx in (-1, 1):
        pts = [v3((sx * 0.17, -0.16, 1.33)), v3((sx * 0.17, -0.06, 1.47)), v3((sx * 0.13, 0.08, 1.49)), v3((sx * 0.09, 0.15, 1.45))]
        hullf = Field("StrapHull")
        hullf.add(Func(lambda P: base.eval(P) - F(0.03), (-1, -1, 1.0), (1, 1, 1.7)), 0.0)
        pp = [project_to(hullf, [p])[0] for p in pts]
        fd.add(Chain(pp, [0.016] * len(pp), k=0.006), 0.004)
    # the pocket, and the tongs' handles in it
    pc = v3((-0.1, -0.29, 0.9))
    h, ok = ray_hit(Func(lambda P: base.eval(P) - F(0.05), (-1, -1, 0.5), (1, 1, 1.3)), [pc + v3((0, -0.4, 0))], [v3((0, 1, 0))], tmax=0.6)
    if ok[0]:
        q = h[0]
        fd.add(RoundBox(q + v3((0, -0.006, 0)), (0.075, 0.012, 0.065), 0.01), 0.004)
    # belt (ties the apron), wrist wraps, sandals, sweat-band
    bb = Field("BeltBase")
    tp = torso_prims()
    bb.add(tp[4][0], 0.0)
    bb.add(tp[5][0], tp[5][1])
    fd.add(Inter(Shell(bb, 0.06, 0.024, pad=0.1), Func(lambda P: np.abs(P[:, 2] - F(0.96)) - F(0.03), (-1, -1, 0.8), (1, 1, 1.2)), 0.005), 0.0)
    for side in ("L", "R"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.8)
        fd.add(Inter(Shell(_forearm(side), 0.012, 0.018, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.06), c - 0.25, c + 0.25), 0.004), 0.0)
        for j in (-1, 0, 1):
            cc = c + ax * (j * 0.035)
            fd.add(Inter(Shell(_forearm(side), 0.021, 0.006, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.005), cc - 0.2, cc + 0.2), 0.002), 0.003)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.1)), (0.078, 0.155, 0.012), 0.01, R=Rz), 0.0)
        ft = Field("FootHull")
        foot(ft, side)
        for c, rad in ((an + fwd * 0.145 + v3((0, 0, -0.07)), 0.024), (an + fwd * 0.05 + v3((0, 0, -0.035)), 0.021)):
            fd.add(Inter(Shell(ft, 0.006, 0.01, pad=0.05), Func(lambda P, c=c, fwd=fwd, rad=rad: np.abs((P - c.astype(F)) @ fwd.astype(F)) - F(rad * 0.6), c - 0.15, c + 0.15), 0.003), 0.002)
        fd.add(Torus(an + v3((0, 0.004, 0.035)), 0.064, 0.009), 0.003)
    sk = skull()
    fd.add(Inter(Shell(sk, 0.01, 0.016, pad=0.06), Func(lambda P: np.abs(band_d(P)) - F(0.018), HEAD_C - 0.35, HEAD_C + 0.35), 0.005), 0.0)
    return fd


def kilt_field():
    """A short ochre wool kilt showing at his sides and back below the apron (label 5 = a dark border)."""
    fd = Field("Kilt")
    base = apron_base()
    def hem(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        return F(0.55) + F(0.01) * NOISE(P * F(8)) + F(0.0) * a
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        return F(0.004) * np.sin(a * F(16)) * smoothstep(0.9, 0.7, P[:, 2]) + F(0.0015) * NOISE(P * F(25))
    fd.add(Inter(Shell(base, 0.018, 0.02, pad=0.1, disp=folds, disp_amp=0.005),
                 Func(lambda P: np.maximum(hem(P) - P[:, 2], P[:, 2] - F(0.99)), (-1, -1, 0.4), (1, 1, 1.1)), 0.005), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (hem(P) + F(0.03)), (-1, -1, 0.4), (1, 1, 0.7)), 5)
    return fd


def bronze_field():
    """Thick armlets above his elbows, the apron belt's ring at his back."""
    fd = Field("Bronze")
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        ua = Field("UA")
        ua.add(upper_arm(side), 0.0)
        ua.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.1, 0.104, 0.134), R=rot_from_axes(z_axis=el - sh)), 0.04)
        for j in range(2):
            c = lerp(sh, el, 0.68 + 0.07 * j)
            fd.add(Inter(Shell(ua, 0.013, 0.016, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.012), c - 0.2, c + 0.2), 0.003), 0.004)
    bb = Field("BeltBase")
    tp = torso_prims()
    bb.add(tp[4][0], 0.0)
    bb.add(tp[5][0], tp[5][1])
    h, ok = ray_hit(Func(lambda P: bb.eval(P) - F(0.09), (-1, -1, 0.7), (1, 1, 1.2)), [v3((0, 0.7, 0.96))], [v3((0, -1, 0))], tmax=0.9)
    if ok[0]:
        fd.add(Torus(h[0], 0.03, 0.008, R=rot_from_axes(z_axis=(0, 1, 0))), 0.0)
    return fd


# ======================================================================================= the hammer (rigid on the `hammer` bone)
HAMMER_L = 0.42            # grip -> the head's centre
HAMMER_BUTT = 0.08         # grip -> the end of the handle
HEAD_HALF = (0.062, 0.055, 0.135)    # the head: half sizes (across the handle, along the handle, face to peen)


def hammer_frame():
    """Rest pose: grip G at the right fist's centre, the handle along the thumb axis T, the striking face along F."""
    wr, f, n, t = hand_frame("R")
    G = fist_center("R")
    T = norm(t)
    Fv = norm(f - T * (f @ T))
    return G, T, Fv


def hammer_head_center():
    G, T, Fv = hammer_frame()
    return G + T * HAMMER_L


def hammer_field():
    """Ash handle (label 0) wrapped with red cord at the grip (5), the bronze head (6): a flat striking face on one side,
    a rounded peen on the other."""
    fd = Field("Hammer")
    G, T, Fv = hammer_frame()
    grain = lambda P: F(0.0015) * NOISE(P * F(70))
    fd.add(RoundCone(G - T * HAMMER_BUTT, G + T * (HAMMER_L + 0.02), 0.024, 0.02, disp=grain, disp_amp=0.002), 0.0)
    fd.add(Sphere(G - T * HAMMER_BUTT, 0.026), 0.006)
    for k in range(6):
        fd.add(Torus(G + T * (-0.05 + 0.02 * k), 0.024, 0.0048, R=rot_from_axes(z_axis=T)), 0.002, 5)
    hc = hammer_head_center()
    side = norm(np.cross(T, Fv))
    R = np.stack([side, T, Fv], axis=1)
    hx, hy, hz = HEAD_HALF
    fd.add(RoundBox(hc - Fv * 0.012, (hx, hy, hz * 0.82), 0.012, R=R), 0.006, 6)              # the body, toward the peen
    fd.add(RoundCone(hc - Fv * (hz * 0.6), hc - Fv * (hz + 0.02), 0.05, 0.032), 0.01, 6)       # the rounded peen
    return fd


def hot_field():
    """The red-hot striking end of the head (its own glowing mesh)."""
    fd = Field("Hot")
    G, T, Fv = hammer_frame()
    hc = hammer_head_center()
    hx, hy, hz = HEAD_HALF
    side = norm(np.cross(T, Fv))
    R = np.stack([side, T, Fv], axis=1)
    fd.add(RoundBox(hc + Fv * (hz * 0.62), (hx + 0.004, hy + 0.004, hz * 0.4), 0.014, R=R), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.62)), 0.05, 0.5)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.11, -0.15, 1.62)), 0.065, 0.55), (hp((sx * 0.18, 0.035, 1.664)), 0.055, 0.5),
                (J["elbow_" + sd] + v3((0, 0.025, 0)), 0.06, 0.3), (J["knee_" + sd] + v3((0, -0.03, 0)), 0.07, 0.3)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.044, 0.0148, -0.0148, -0.044):
            pts.append((wr + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.012, 0.03, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "tarek"
ROOT_NAME = "HeroTarekHQ"
TEX_PREFIX = "hero"
MAT_NAME = "TarekMat"
MESH_NAME = "Tarek"
BASE_MODULE = "tarek_base"
ANIM_MODULE = "anim_tarek"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Leather", "Kilt", "Bronze", "Hammer", "Hot"]
REGION_PARTS = ("Skin", "Leather", "Kilt", "Hammer")
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_TarekSkin", "base": (0.72, 0.48, 0.34), "ruddy": (0.8, 0.44, 0.32), "lips": (0.6, 0.32, 0.28),
                      "brow": ((0.04, 0.035, 0.03), (0.1, 0.08, 0.06)), "paint": (0.85, 0.52, 0.14),
                      "extra": ((LASH, (0.04, 0.03, 0.025), 0.5), (SOOT, (0.12, 0.1, 0.09), 0.55))}),
    "Hair": ("hair", {"name": "HQ_TarekHair", "base": (0.06, 0.05, 0.045), "hi": (0.22, 0.18, 0.16), "low": (0.025, 0.02, 0.018),
                      "streak": (0.04, 0.032, 0.028), "tint": (0.12, 0.09, 0.07)}),
    "Beard": ("hair", {"name": "HQ_TarekBeard", "base": (0.06, 0.05, 0.045), "hi": (0.22, 0.18, 0.16), "low": (0.025, 0.02, 0.018),
                       "streak": (0.04, 0.032, 0.028), "tint": (0.12, 0.09, 0.07)}),
    "Leather": ("leather_dyed", {"name": "HQ_Apron", "base": (0.4, 0.24, 0.13), "dyed": (0.16, 0.1, 0.07)}),
    "Kilt": ("wool", {"name": "HQ_TarekKilt", "base": (0.72, 0.5, 0.18), "border": (0.3, 0.16, 0.08)}),
    "Bronze": ("bronze", {"name": "HQ_TarekBronze"}),
    "Hammer": ("spear_shaft", {"name": "HQ_Hammer"}),
    "Hot": ("glow_ball", {"name": "HQ_HotIron", "col": (1.0, 0.42, 0.1)}),
}
GLOW = {"Hot": ((1.0, 0.36, 0.06), 1.1, 0.5)}
LOW_TARGETS = {"Skin": 7000, "Teeth": 120, "Hair": 900, "Beard": 1800, "Leather": 2600, "Kilt": 800, "Bronze": 700,
               "Hammer": 700, "Hot": 160}
AO_EXCLUDE = ["Hammer", "Hot", "Bronze"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.74, 0.9, 1.06, 1.42)


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.9), (0, 0.045, 1.1)),
        "chest": ((0, 0.045, 1.1), (0, 0.065, 1.33)),
        "neck": ((0, 0.065, 1.33), hp((0, 0.02, 1.56))),
        "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.34,
    }


def prop_bones():
    G, T, Fv = hammer_frame()
    return [("hammer", G, G + T * 0.2, "hand.R")]


def leather_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "thigh.R", "thigh.L", "shin.R", "shin.L",
                                                       "foot.R", "foot.L", "forearm.R", "forearm.L", "head"},
                         caps={"thigh.R": 0.45, "thigh.L": 0.45})
    groups = {}
    for v in ob.data.vertices:
        if v.co.z > 1.6:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"head": 1.0})


def weight_rules():
    return {
        "Hair": ("rigid", "head"), "Beard": ("transfer", {"head", "neck"}, None), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Leather": ("custom", leather_weights),
        "Kilt": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.4, "thigh.L": 0.4}),
        "Bronze": ("transfer", TORSO | {"upperarm.R", "upperarm.L"}, {"upperarm.R": 1.0, "upperarm.L": 1.0}),
        "Hammer": ("rigid", "hammer"), "Hot": ("rigid", "hammer"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Hammer":
        return 0.9
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Beard", beard_field(), 0.0024 if fine else 0.0034),
        ("Leather", leather_field(), 0.0026 if fine else 0.0036),
        ("Kilt", kilt_field(), 0.0028 if fine else 0.0038),
        ("Bronze", bronze_field(), 0.0022 if fine else 0.003),
        ("Hammer", hammer_field(), 0.0018 if fine else 0.0026),
        ("Hot", hot_field(), 0.0016),
    ]
