"""The Sun Priest (HQ tower, Bronze Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A tall, lean priest of the sun in a river city: clean-shaven, calm and severe, eyes lined with kohl, a short black wig cut
straight at the jaw under a gold circlet with a small sun disc. A long white pleated linen robe to the ankles, a broad
collar of gold, lapis, carnelian and turquoise bands over his shoulders, a leopard skin across his body from his left
shoulder (the cat's head on his shoulder, its paws and tail hanging at his right hip), a red sash, gold armlets and
bracelets, sandals. In his right fist a tall dark staff with gold bands, crowned with a glowing sun disc in a ring of
golden rays (the disc ships as its own glowing mesh, on the `sun` bone).

The staff is rigid in his right fist ("frame" aims in anim_sunpriest.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, grad, project_to, flow_line, Stone, lerp
from ugo import _blend_add

J = {
    "root": (0.0, 0.03, 0.84),
    "spine": (0.0, 0.03, 1.0),
    "chest": (0.0, 0.045, 1.2),
    "neck": (0.0, 0.055, 1.43),
    "head": (0.0, 0.02, 1.55),
    "head_end": (0.0, -0.02, 1.95),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.31, 0.06, 1.39)
    J["elbow_" + _s] = (_x * 0.5, 0.09, 1.13)
    J["wrist_" + _s] = (_x * 0.64, 0.03, 0.89)
    J["hip_" + _s] = (_x * 0.14, 0.04, 0.8)
    J["knee_" + _s] = (_x * 0.16, 0.0, 0.45)
    J["ankle_" + _s] = (_x * 0.17, 0.06, 0.11)
    J["toe_" + _s] = (_x * 0.19, -0.17, 0.035)
J = {k: v3(v) for k, v in J.items()}

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, KOHL = 0, 1, 2, 3, 4, 5, 8, 9

HS = 1.05
DZ = -0.01
HPIV = v3((0.0, 0.02, 1.49))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


def hinv(P):
    return (P - HPIV.astype(F)) / F(HS) + HPIV.astype(F) - np.array([0, 0, DZ], F)


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.172, 0.188, 0.186)) * HS
EYE_R = hr(0.034)


def eye_c(sx):
    return hp((sx * 0.069, -0.142, 1.676))        # set a little deeper than the guards': calm, hooded eyes


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


HAND_S = 0.98
CURLS = {"R": (1.45, 1.6, 1.2), "L": (0.25, 0.3, 0.2)}       # right fist round the staff, left hand open (it blesses, commands)


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    fist = side == "R"
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.06, 0.03, 0.065)) * s, 0.027 * s, R=Rp), 0.026, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.033, 0.028, 0.05)) * s, R=Rp), 0.018, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.042, 0.014, -0.014, -0.042)
    lens = (0.98, 1.05, 0.98, 0.82)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * (1.2 if fist else 2.0))
        pts, rads = [p], [0.0195 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.054 * ls * s, 0.044 * ls * s, 0.036 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.88)
        fd.add(Chain(pts, rads, k=0.006), 0.011, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.015 * s), 0.009, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.011, (0.011, 0.007, 0.014), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.05 * s + n * 0.011
    if fist:
        d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
        d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:
        d1 = norm(f * 0.45 + t * 0.85 + n * 0.15)
        d2 = norm(f * 0.75 + t * 0.55 + n * 0.1)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.024 * s, 0.021 * s, 0.018 * s], k=0.008), 0.017, SKIN)


def foot(fd, side, s=1.02):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.1)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    fd.add(Sphere(an + v3((0, 0.042, -0.05)), 0.056 * s), 0.028, SKIN)
    fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.07)), v3((0.062, 0.116, 0.033)) * s, 0.031, R=Rz), 0.031, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.036 + v3((0, 0, -0.03)), v3((0.06, 0.084, 0.046)) * s, R=Rz), 0.028, SKIN)
    inner = -sx
    for i, (o, r) in enumerate(((0.048, 0.026), (0.02, 0.02), (-0.005, 0.018), (-0.027, 0.016), (-0.046, 0.015))):
        base = an + fwd * (0.162 - 0.011 * i - (0.0 if i else -0.004)) + rgt * (o * inner) + v3((0, 0, -0.08))
        tip = base + fwd * (0.029 + r * 0.4) + v3((0, 0, -0.004))
        base[2] = 0.024 + r * 0.55
        tip[2] = 0.019 + r * 0.5
        fd.add(RoundCone(base, tip, r, r * 0.92), 0.011, SKIN)
        tn = norm(tip - base)
        fd.paint(Ellipsoid(tip + v3((0, 0, r * 0.55)), (r * 0.7, r * 0.75, r * 0.35), R=rot_from_axes(y_axis=tn, z_axis=(0, 0, 1))), NAIL)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.05, 0.0, 0.0)), 0.023), 0.018, SKIN)


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.06, 1.585), (0.118, 0.124, 0.124)), 0.07, SKIN)                        # a long, lean jaw
    fd.add(E((0, -0.14, 1.503), (0.072, 0.062, 0.07)), 0.05, SKIN)                          # a firm, narrow chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.106, -0.13, 1.642), 0.037), 0.045, SKIN)                           # high cheekbones
        fd.add(S((sx * 0.108, -0.04, 1.56), 0.038), 0.05, SKIN)
        pts = [hp((sx * 0.15, -0.055, 1.742)), hp((sx * 0.114, -0.13, 1.75)), hp((sx * 0.06, -0.172, 1.748)), hp((0.0, -0.182, 1.748))]
        fd.add(Chain(pts, [hr(0.011), hr(0.019), hr(0.022), hr(0.022)], k=hr(0.022)), hr(0.032), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.1, -0.138, 1.596)), v3((0.028, 0.016, 0.036)) * HS, R=euler(0, 0, sx * 0.4)), hr(0.02))   # hollow cheeks
    # straight brows, level and calm
    for sx in (-1, 1):
        pts = [hp((sx * 0.026, -0.212, 1.755)), hp((sx * 0.066, -0.205, 1.764)), hp((sx * 0.108, -0.184, 1.767)), hp((sx * 0.148, -0.146, 1.758))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.009), hr(0.01), hr(0.009), hr(0.004)], k=hr(0.007)), hr(0.009), BROW)
        fd.paint(Chain(pts, [hr(0.015), hr(0.017), hr(0.015), hr(0.008)], k=hr(0.009)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0065)), Plane(ec + v3((0, 0, hr(0.016))), (sx * 0.15, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.005)), Plane(ec + v3((0, 0, -hr(0.024))), (sx * -0.1, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.013))), (sx * 0.15, 0.05, -1.0)), hr(0.002)), LASH)
        # kohl: a dark line round the eye, drawn out toward the temple
        k0 = hp((sx * 0.03, -0.17, 1.674))
        k1 = hp((sx * 0.07, -0.19, 1.67))
        k2 = hp((sx * 0.112, -0.165, 1.672))
        k3 = hp((sx * 0.15, -0.13, 1.678))
        fd.paint(Chain([k0, k1, k2, k3], [hr(0.008), hr(0.011), hr(0.008), hr(0.004)], k=hr(0.006)), KOHL)
    # a straight, narrow nose
    fd.add(RoundCone(hp((0, -0.186, 1.722)), hp((0, -0.234, 1.628)), hr(0.015), hr(0.022)), hr(0.016), SKIN)
    fd.add(S((0, -0.233, 1.617), 0.021), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.027, -0.214, 1.604), 0.018), hr(0.011), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.014, -0.229, 1.592)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a calm closed mouth, full lips
    slot = [hp((-0.05, -0.17, 1.552)), hp((-0.026, -0.192, 1.547)), hp((0, -0.198, 1.546)), hp((0.026, -0.192, 1.547)), hp((0.05, -0.17, 1.552))]
    fd.sub(Chain(slot, [hr(0.0022), hr(0.003), hr(0.0033), hr(0.003), hr(0.0022)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.048, -0.168, 1.556), (-0.026, -0.187, 1.555), (-0.008, -0.192, 1.559), (0.008, -0.192, 1.559), (0.026, -0.187, 1.555), (0.048, -0.168, 1.556)]
    lo_lip = [(-0.042, -0.17, 1.544), (-0.022, -0.188, 1.535), (0, -0.192, 1.533), (0.022, -0.188, 1.535), (0.042, -0.17, 1.544)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.0035), hr(0.0058), hr(0.0062), hr(0.0062), hr(0.0058), hr(0.0035)], k=hr(0.006)), hr(0.008), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.0045), hr(0.0072), hr(0.008), hr(0.0072), hr(0.0045)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.176, 0.035, 1.66)), v3((0.025, 0.045, 0.058)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)


# ======================================================================================= body (lean)
def torso_prims():
    return [
        (Ellipsoid((0, 0.045, 1.2), (0.24, 0.195, 0.25), R=euler(-0.1, 0, 0)), 0.0),
        (Ellipsoid((0, 0.11, 1.25), (0.27, 0.14, 0.18)), 0.06),
        (Ellipsoid((0.11, -0.125, 1.28), (0.11, 0.05, 0.075), R=euler(0.1, 0, 0.18)), 0.045),
        (Ellipsoid((-0.11, -0.125, 1.28), (0.11, 0.05, 0.075), R=euler(0.1, 0, -0.18)), 0.045),
        (Ellipsoid((0, 0.0, 1.0), (0.18, 0.16, 0.19)), 0.08),
        (Ellipsoid((0, 0.045, 0.84), (0.2, 0.165, 0.15)), 0.08),
    ]


def traps():
    return Ellipsoid((0, 0.09, 1.42), (0.21, 0.12, 0.08), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.055, 1.38), hp((0, 0.02, 1.575)), 0.088, hr(0.08))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.02, -0.005, 0.012)), 0.095)


def upper_arm(side):
    return RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.084, 0.064)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.05, SKIN)
        fd.add(upper_arm(side), 0.045, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.02, 0)), (0.074, 0.076, 0.115), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(RoundCone(el, wr, 0.062, 0.048), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.076, 0.068, 0.12), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.022, 0)), 0.05), 0.025, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.12, 0.08), 0.06, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.02, 0)), (0.105, 0.1, 0.17), R=rot_from_axes(z_axis=kn - hip)), 0.045, SKIN)
        fd.add(Sphere(kn + v3((0, -0.028, 0.0)), 0.062), 0.035, SKIN)
        fd.add(RoundCone(kn, an, 0.074, 0.05), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.028, 0)), (0.083, 0.08, 0.13), R=rot_from_axes(z_axis=an - kn)), 0.04, SKIN)
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
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009, -0.178, 1.55)), v3((0.008, 0.006, 0.007)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= wig, circlet
def skull():
    fd = Field("Skull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    return fd


def wig_field():
    """A short black wig cut straight at the jaw: a fringe over the brow, thick at the sides and the back, fine strands
    running down it."""
    fd = Field("Wig")
    sk = skull()
    strands = lambda P: F(0.0025) * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(HEAD_C[1])) * F(70)) + F(0.0015) * NOISE(P * np.array([60, 60, 12], F))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        face = np.where(y < F(-0.06), np.minimum(F(1.79) - z, F(0.135) - ax), F(-1.0))   # the face, under a straight fringe
        cheek = np.where(z < F(1.74), F(-0.09) - y, F(-1.0))                            # the sides end in front of the ears
        bottom = F(1.56) - F(0.015) * smoothstep(-0.05, 0.1, y) - z                       # cut straight at the jaw
        return np.maximum(np.maximum(face, cheek), bottom)
    hull = Field("WigHull")
    hull.add(Ellipsoid(HEAD_C, HEAD_RAD + v3((0.024, 0.03, 0.02))), 0.0)
    hull.add(Ellipsoid(hp((0, 0.04, 1.62)), v3((0.2, 0.17, 0.12)) * HS), 0.06)
    fd.add(Inter(Shell(hull, 0.0, 0.034, pad=0.08, disp=strands, disp_amp=0.004), Func(keep, HEAD_C - 0.45, HEAD_C + 0.35), 0.004), 0.0)
    return fd


CIRC_Z = 1.795           # the circlet sits on the wig just above the fringe (design height at the front)


def circlet_d(P):
    """Height above the circlet's plane (design units): level at the front, a little lower at the back."""
    Q = hinv(P)
    return Q[:, 2] - (F(CIRC_Z) - F(0.06) * smoothstep(-0.2, 0.2, Q[:, 1]))


def gold_field():
    """The gold circlet on his wig, a small sun disc with rays at its front."""
    fd = Field("Gold")
    hull = Field("CircHull")
    hull.add(Ellipsoid(HEAD_C, HEAD_RAD + v3((0.024, 0.03, 0.02))), 0.0)
    # seated on the wig (its outer face is at the hull + 0.017), not standing off it like a brim
    fd.add(Inter(Shell(hull, 0.02, 0.011, pad=0.08), Func(lambda P: np.abs(circlet_d(P)) - F(0.016), HEAD_C - 0.4, HEAD_C + 0.4), 0.003), 0.0)
    o = hp((0.0, -0.6, CIRC_Z + 0.03))
    h, ok = ray_hit(Func(lambda P: hull.eval(P) - F(0.03), HEAD_C - 0.5, HEAD_C + 0.5), [o], [v3((0, 1, 0))], tmax=0.8)
    if ok[0]:
        c = h[0] + v3((0, -0.004, 0.0))
        fd.add(Cylinder(c, 0.03, 0.01, rr=0.003, R=rot_from_axes(z_axis=(0, -1, 0.15))), 0.004)
        for k in range(10):
            a = 2 * math.pi * k / 10
            d = rot_from_axes(z_axis=(0, -1, 0.15)) @ v3((math.cos(a), math.sin(a), 0))
            fd.add(RoundCone(c + d * 0.03, c + d * 0.046, 0.005, 0.002), 0.003)
    return fd


def bangles_field():
    """Gold armlets above his elbows and bracelets on his wrists."""
    fd = Field("Bangles")
    for side in ("R", "L"):
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        ua = Field("UA")
        ua.add(upper_arm(side), 0.0)
        ua.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.02, 0)), (0.074, 0.076, 0.115), R=rot_from_axes(z_axis=el - sh)), 0.035)
        ax = norm(el - sh)
        c = lerp(sh, el, 0.58)
        fd.add(Inter(Shell(ua, 0.01, 0.014, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.022), c - 0.2, c + 0.2), 0.003), 0.004)
        fa = Field("FA")
        fa.add(RoundCone(el, wr, 0.062, 0.048), 0.0)
        fa.add(Ellipsoid(lerp(el, wr, 0.3), (0.076, 0.068, 0.12), R=rot_from_axes(z_axis=wr - el)), 0.035)
        ax2 = norm(wr - el)
        c2 = lerp(el, wr, 0.86)
        fd.add(Inter(Shell(fa, 0.01, 0.014, pad=0.06), Func(lambda P, c=c2, ax=ax2: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.026), c2 - 0.2, c2 + 0.2), 0.003), 0.004)
    return fd


def _ray_sd(P, a, b, side, n):
    """A flat tapering ray (a long thin triangle with rounded edges) from a to b."""
    ab = b - a
    L = float(np.linalg.norm(ab))
    d = ab / L
    q = P - a.astype(F)
    t = np.clip((q @ d.astype(F)) / F(L), 0, 1)
    w = F(0.016) * (F(1) - t) + F(0.002)
    along = q @ d.astype(F)
    lat = np.abs(q @ side.astype(F)) - w
    thick = np.abs(q @ n.astype(F)) - F(0.006)
    endc = np.maximum(-along, along - F(L))
    return np.maximum(np.maximum(lat, thick), endc)


# ======================================================================================= robe, collar, leopard skin, sash
def robe_base():
    b = Field("RobeBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.05)
        b.add(upper_arm(side), 0.045)
    b.add(RoundCone((0, 0.03, 0.9), (0, 0.03, 0.12), 0.21, 0.3), 0.09)            # to the ankles, flaring a little
    return b


def hem_z(P):
    return F(0.13) + F(0.008) * NOISE(P * F(7))


def _sleeve(P, side):
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    n = norm(el - sh)
    c = sh + (el - sh) * 0.62
    d = (P - c.astype(F)) @ n.astype(F)
    sx = -1 if side == "R" else 1
    return np.where((P[:, 0] * F(sx) > F(0.3)) & (P[:, 2] > F(0.95)), d, F(-1.0))


def linen_field():
    """A long white pleated linen robe to his ankles with short sleeves; a red woven border at the hem (label 5) and a
    blue stripe above it (6)."""
    fd = Field("Linen")
    base = robe_base()
    def pleats(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        k = smoothstep(0.98, 0.8, P[:, 2])
        return F(0.0035) * np.sin(a * F(40)) * k + F(0.0012) * NOISE(P * F(30))
    def keep(P):
        neck = P[:, 2] - (F(1.465) + F(0.3) * smoothstep(0.15, 0.22, np.abs(P[:, 0])))
        k = np.maximum(hem_z(P) - P[:, 2], neck)
        return np.maximum(np.maximum(k, _sleeve(P, "R")), _sleeve(P, "L"))
    fd.add(Inter(Shell(base, 0.02, 0.018, pad=0.1, disp=pleats, disp_amp=0.005), Func(keep, (-1, -1, 0.0), (1, 1, 1.7)), 0.005), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (hem_z(P) + F(0.05)), (-1, -1, 0.0), (1, 1, 0.4)), 5)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - (hem_z(P) + F(0.07))) - F(0.008), (-1, -1, 0.0), (1, 1, 0.4)), 6)
    return fd


def collar_base():
    b = Field("CollarBase")
    for p, k in torso_prims()[:4]:
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.05)
    b.add(neck_prim(), 0.05)
    return b


COLLAR_C = v3((0.0, 0.0, 1.44))


def collar_r(P):
    """Distance in the collar's own terms: from the neck outward over the chest and shoulders (0 at its inner edge)."""
    q = P - COLLAR_C.astype(F)
    return np.sqrt(q[:, 0] ** 2 + (q[:, 1] * F(1.15)) ** 2 + (q[:, 2] * F(0.7)) ** 2)


def collar_field():
    """A broad collar of beads over his shoulders and chest: bands of gold (label 0), lapis blue (5), carnelian red (6)
    and turquoise (7), a row of drop beads round its edge."""
    fd = Field("Collar")
    base = collar_base()
    beads = lambda P: F(0.0015) * np.sin(np.arctan2(P[:, 0], -P[:, 1]) * F(140)) + F(0.0008) * NOISE(P * F(120))
    def keep(P):
        r = collar_r(P)
        return np.maximum(F(0.12) - r, r - F(0.25)) + np.where(P[:, 2] < F(1.1), F(1.0), F(0.0))
    fd.add(Inter(Shell(base, 0.03, 0.014, pad=0.1, disp=beads, disp_amp=0.003), Func(keep, (-0.6, -0.6, 1.0), (0.6, 0.6, 1.7)), 0.004), 0.0)
    for lo, hi, lab in ((0.135, 0.16, 5), (0.165, 0.185, 6), (0.19, 0.21, 7), (0.215, 0.232, 5)):
        fd.paint(Func(lambda P, lo=lo, hi=hi: np.maximum(F(lo) - collar_r(P), collar_r(P) - F(hi)), (-0.6, -0.6, 1.0), (0.6, 0.6, 1.7)), lab)
    return fd


def pelt_band(P):
    """The leopard skin's band across his body: from his left shoulder down across his chest and back to his right hip."""
    a = v3((0.2, 0.0, 1.42))
    b = v3((-0.18, 0.0, 0.88))
    d = norm(b - a)
    q = P - a.astype(F)
    t = q @ d.astype(F)
    perp = q - t[:, None] * d.astype(F)[None, :]
    lat = perp[:, 0] * F(d[2]) - perp[:, 2] * F(d[0])                     # across the band, in the body's front plane
    return np.abs(lat) - F(0.11)


def pelt_field():
    """A leopard skin worn across him from the left shoulder to the right hip (front and back), the cat's head on his
    left shoulder, two paws and the tail hanging at his right hip."""
    fd = Field("Pelt")
    base = robe_base()
    fur = lambda P: F(0.004) * NOISE(P * np.array([30, 30, 10], F)) + F(0.002) * NOISE(P * F(80))
    def keep(P):
        return np.maximum(pelt_band(P), np.maximum(F(0.78) - P[:, 2], P[:, 2] - F(1.52)))
    fd.add(Inter(Func(keep, (-0.42, -0.36, 0.74), (0.42, 0.4, 1.58)), Shell(base, 0.05, 0.022, pad=0.1, disp=fur, disp_amp=0.006), 0.006), 0.0)
    # the cat's head on his left shoulder, looking forward
    hc = v3((0.17, -0.12, 1.4))
    fd.add(Ellipsoid(hc, (0.06, 0.07, 0.05), disp=fur, disp_amp=0.004), 0.02)
    fd.add(Ellipsoid(hc + v3((0.0, -0.06, -0.012)), (0.038, 0.035, 0.03), disp=fur, disp_amp=0.003), 0.015)        # muzzle
    for sx in (-1, 1):
        fd.add(Ellipsoid(hc + v3((sx * 0.042, 0.02, 0.04)), (0.018, 0.012, 0.022), R=euler(0, sx * 0.4, 0)), 0.008)   # ears
    # paws and tail hanging at his right hip
    hip = v3((-0.2, -0.06, 0.88))
    for k, (dx, L) in enumerate(((-0.02, 0.2), (0.05, 0.18))):
        a = hip + v3((dx, -0.08, 0.0))
        pts = [a, a + v3((dx * 0.3, -0.03, -L * 0.5)), a + v3((dx * 0.4, -0.035, -L))]
        fd.add(Chain(pts, [0.026, 0.022, 0.02], k=0.006, disp=fur, disp_amp=0.003), 0.008)
        fd.add(Ellipsoid(pts[-1] + v3((0, -0.01, -0.02)), (0.026, 0.03, 0.022), disp=fur, disp_amp=0.003), 0.008)
    t0 = hip + v3((-0.04, 0.06, -0.02))
    tail = [t0 + v3((-0.01 * k, 0.012 * k, -0.06 * k)) for k in range(7)]
    fd.add(Chain(tail, [0.017 - 0.0012 * k for k in range(7)], k=0.006, disp=fur, disp_amp=0.003), 0.006)
    return fd


def sash_field():
    """A red sash at his waist, its ends hanging in front."""
    fd = Field("Sash")
    base = robe_base()
    cloth = lambda P: F(0.0015) * NOISE(P * F(40))
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(0.93)) - F(0.035), (-0.4, -0.36, 0.84), (0.4, 0.4, 1.02)), Shell(base, 0.04, 0.03, pad=0.1, disp=cloth, disp_amp=0.002), 0.005), 0.0)
    p, _ = ray_hit(Func(lambda P: base.eval(P) - F(0.06), (-1, -1, 0.5), (1, 1, 1.3)), [v3((0.03, -0.7, 0.92))], [v3((0, 1, 0))], tmax=0.8)
    k0 = p[0] + v3((0, -0.012, 0))
    fd.add(Ellipsoid(k0, (0.03, 0.02, 0.028)), 0.006)
    for k, dx in enumerate((-0.02, 0.025)):
        pts = [k0 + v3((dx * 0.5, -0.005, -0.02)), k0 + v3((dx, -0.02, -0.18)), k0 + v3((dx * 1.3, -0.02, -0.34 + 0.04 * k))]
        fd.add(Lock(pts, [0.03, 0.032, 0.03], [0.006, 0.006, 0.006], [v3((0, -1, 0))] * 3, k=0.006, disp=cloth, disp_amp=0.002), 0.006)
    return fd


def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.062, 0.048)


def leather_field():
    """Sandals (soles and straps)."""
    fd = Field("Leather")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.1)), (0.072, 0.15, 0.011), 0.009, R=Rz), 0.0)
        ft = Field("FootHull")
        foot(ft, side)
        for c, rad in ((an + fwd * 0.14 + v3((0, 0, -0.07)), 0.022), (an + fwd * 0.05 + v3((0, 0, -0.035)), 0.02)):
            fd.add(Inter(Shell(ft, 0.006, 0.01, pad=0.05), Func(lambda P, c=c, fwd=fwd, rad=rad: np.abs((P - c.astype(F)) @ fwd.astype(F)) - F(rad * 0.6), c - 0.15, c + 0.15), 0.003), 0.002)
    return fd


# ======================================================================================= the sun staff
STAFF_R = 0.019
STAFF_BACK = 1.02         # grip -> the butt
SUN_S = 1.0               # grip -> the sun disc's centre
SUN_R = 0.1


def staff_axis():
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t


def sun_frame():
    """The sun disc: centre, face normal (forward, across the staff), and its in-plane axes."""
    a0, ax = staff_axis()
    c = a0 + ax * SUN_S
    wr, f, n0, t = hand_frame("R")
    nrm = norm(f - ax * (f @ ax))                 # the disc faces along the knuckles
    u = ax
    w = np.cross(nrm, u)
    return c, nrm, u, w


def staff_field():
    """Dark lacquered wood (label 0) with a red cord grip (5); its gold (6): bands, the socket under the disc and the ring
    of rays round it."""
    fd = Field("Staff")
    a0, ax = staff_axis()
    grain = lambda P: F(0.0015) * NOISE(P * F(70))
    fd.add(RoundCone(a0 - ax * STAFF_BACK, a0 + ax * (SUN_S - 0.19), STAFF_R, STAFF_R * 0.92, disp=grain, disp_amp=0.002), 0.0)
    fd.add(Sphere(a0 - ax * STAFF_BACK, STAFF_R + 0.006), 0.006, 6)
    for k in range(5):
        fd.add(Torus(a0 + ax * (-0.04 + 0.02 * k), STAFF_R + 0.003, 0.0045, R=rot_from_axes(z_axis=ax)), 0.002, 5)
    for s_ in (-0.95, -0.4, 0.12, 0.52):
        fd.add(Torus(a0 + ax * s_, STAFF_R + 0.004, 0.009, R=rot_from_axes(z_axis=ax)), 0.003, 6)
    fd.add(RoundCone(a0 + ax * (SUN_S - 0.2), a0 + ax * (SUN_S - SUN_R - 0.01), STAFF_R + 0.006, 0.03), 0.01, 6)
    sc, n, u, w = sun_frame()
    fd.add(Torus(sc, SUN_R + 0.012, 0.012, R=rot_from_axes(z_axis=n, y_axis=u)), 0.004, 6)
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        d = u * math.cos(a) + w * math.sin(a)
        L = 0.085 if k % 2 == 0 else 0.055
        base = sc + d * (SUN_R + 0.018)
        tip = base + d * L
        side = norm(np.cross(n, d))
        fd.add(Func(lambda P, base=base, tip=tip, side=side: _ray_sd(P, base, tip, side, n), np.minimum(base, tip) - 0.03,
                    np.maximum(base, tip) + 0.03), 0.003, 6)
    return fd


def sun_field():
    """The sun disc itself (shipped as its own glowing mesh)."""
    fd = Field("Sun")
    sc, n, u, w = sun_frame()
    fd.add(Cylinder(sc, SUN_R, 0.026, rr=0.011, R=rot_from_axes(z_axis=n, y_axis=u)), 0.0)
    fd.add(Ellipsoid(sc + n * 0.008, (SUN_R * 0.7, SUN_R * 0.7, 0.02), R=rot_from_axes(z_axis=n, y_axis=u)), 0.01)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.24, 1.616)), 0.045, 0.45)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.1, -0.14, 1.61)), 0.055, 0.35), (hp((sx * 0.176, 0.035, 1.66)), 0.05, 0.5),
                (J["elbow_" + sd] + v3((0, 0.022, 0)), 0.055, 0.3), (J["knee_" + sd] + v3((0, -0.028, 0)), 0.065, 0.3)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.138 + t * o - n * 0.012, 0.03, 0.45))
        an = J["ankle_" + side]
        pts.append((an + v3((0, -0.17, -0.07)), 0.06, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "sun_priest"
ROOT_NAME = "SunPriestHQ"
TEX_PREFIX = "priest"
MAT_NAME = "PriestMat"
MESH_NAME = "Priest"
BASE_MODULE = "sunpriest_base"
ANIM_MODULE = "anim_sunpriest"
PARTS = ["Skin", "Eyes", "Teeth", "Wig", "Gold", "Bangles", "Linen", "Collar", "Pelt", "Sash", "Leather", "Staff", "Sun"]
REGION_PARTS = ("Skin", "Linen", "Collar", "Staff")
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_PriestSkin", "base": (0.7, 0.47, 0.32), "ruddy": (0.74, 0.42, 0.3), "lips": (0.55, 0.3, 0.25),
                      "brow": ((0.05, 0.04, 0.035), (0.12, 0.09, 0.07)),
                      "extra": ((LASH, (0.05, 0.035, 0.03), 0.5), (KOHL, (0.04, 0.035, 0.05), 0.4))}),
    "Wig": ("hair", {"name": "HQ_Wig", "base": (0.06, 0.05, 0.05), "hi": (0.25, 0.22, 0.22), "low": (0.025, 0.02, 0.02),
                     "streak": (0.04, 0.035, 0.035), "tint": (0.12, 0.09, 0.08)}),
    "Gold": ("gold", {"name": "HQ_PriestGold"}), "Bangles": ("gold", {"name": "HQ_PriestGold"}),
    "Linen": ("linen", {"name": "HQ_PriestLinen"}),
    "Collar": ("collar", {"name": "HQ_Collar"}),
    "Pelt": ("pelt", {}),
    "Sash": ("cloth", {"name": "HQ_Sash", "col": (0.72, 0.12, 0.08)}),
    "Leather": ("leather", {"name": "HQ_PriestLeather", "base": (0.42, 0.26, 0.14)}),
    "Staff": ("bow", {"name": "HQ_SunStaff"}),
    "Sun": ("glow_ball", {"name": "HQ_SunDisc", "col": (1.0, 0.8, 0.3)}),
}
GLOW = {"Sun": ((1.0, 0.74, 0.22), 1.0, 0.55)}        # (colour, strength, albedo factor): brighter washes out in game
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Wig": 1300, "Gold": 500, "Bangles": 700, "Linen": 2400, "Collar": 1100, "Pelt": 1500,
               "Sash": 500, "Leather": 600, "Staff": 1100, "Sun": 300}
AO_EXCLUDE = ["Staff", "Sun", "Bangles"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.76, 0.92, 1.1, 1.47)


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.94), (0, 0.04, 1.15)),
        "chest": ((0, 0.04, 1.15), (0, 0.055, 1.4)),
        "neck": ((0, 0.055, 1.4), hp((0, 0.02, 1.57))),
        "head": (hp((0, 0.02, 1.57)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.4,
    }


def prop_bones():
    sc, n, u, w = sun_frame()
    return [("sun", sc, sc + u * 0.12, "hand.R")]


def bangle_weights(ob, skin_ob, arm):
    """Armlets ride the upper arms, bracelets the forearms."""
    groups = {}
    for v in ob.data.vertices:
        p = np.array(v.co)
        side = "R" if p[0] < 0 else "L"
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        w = {("upperarm." if _seg_dist(p, sh, el) < _seg_dist(p, el, wr) else "forearm.") + side: 1.0}
        _blend_add(ob, groups, v.index, w)


def _seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
    return float(np.linalg.norm(a + ab * t - p))


def pelt_weights(ob, skin_ob, arm):
    """The skin rides his torso; its head on his left shoulder; the paws and the tail swing a little with his right thigh."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.L", "clavicle.R", "upperarm.L", "thigh.R"},
                         caps={"upperarm.L": 0.3, "thigh.R": 0.35})


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Wig": ("rigid", "head"),
        "Gold": ("rigid", "head"), "Bangles": ("custom", bangle_weights),
        "Linen": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L", "shin.R", "shin.L"},
                  {"thigh.R": 0.4, "thigh.L": 0.4, "shin.R": 0.3, "shin.L": 0.3, "upperarm.R": 0.85, "upperarm.L": 0.85}),
        "Collar": ("transfer", TORSO | {"clavicle.R", "clavicle.L"}, None),
        "Pelt": ("custom", pelt_weights),
        "Sash": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.3, "thigh.L": 0.3}),
        "Leather": ("transfer", {"foot.R", "foot.L", "shin.R", "shin.L"}, None),
        "Staff": ("rigid", "hand.R"), "Sun": ("rigid", "sun"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Staff":
        return 0.6
    if part in ("Collar", "Pelt"):
        return 1.15
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Wig", wig_field(), 0.0024 if fine else 0.0034),
        ("Gold", gold_field(), 0.0016 if fine else 0.0024),
        ("Bangles", bangles_field(), 0.002 if fine else 0.0028),
        ("Linen", linen_field(), 0.0028 if fine else 0.0038),
        ("Collar", collar_field(), 0.0022 if fine else 0.003),
        ("Pelt", pelt_field(), 0.0026 if fine else 0.0036),
        ("Sash", sash_field(), 0.0024 if fine else 0.0034),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Staff", staff_field(), 0.0017 if fine else 0.0024),
        ("Sun", sun_field(), 0.0016 if fine else 0.0022),
    ]
