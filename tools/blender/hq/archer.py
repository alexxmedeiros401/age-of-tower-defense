"""The Bronze Archer (HQ tower, Bronze Age). Rest pose = A-pose, facing -Y, feet at z=0; right side = -X.

A lean young archer of a river city: a short black beard, a bronze conical helmet with leather cheek guards over black
hair tied back in a short tail; a corselet of bronze scales over a white linen kilt with a red border, a leather belt
with a bronze buckle, a bracer on his bow arm, sandals. A composite recurve bow (dark lacquered limbs with a cream horn
belly, red cord round the grip, bronze tip caps) in his left fist; a red leather quiver of arrows on his back, its mouth
over his right shoulder.

He looses two arrows at once: the pair is nocked on the string on its own bone ("arrow", child of the drawing hand), and
the string's two halves are bones of their own (children of the bow hand) that the clips aim at the drawing fingers and
stretch along their length, so the string stays two straight lines from the bow tips to the fingers."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, grad, project_to, flow_line, Stone, lerp
from ugo import _blend_add

J = {
    "root": (0.0, 0.03, 0.82),
    "spine": (0.0, 0.03, 0.98),
    "chest": (0.0, 0.05, 1.18),
    "neck": (0.0, 0.065, 1.42),
    "head": (0.0, 0.02, 1.54),
    "head_end": (0.0, -0.02, 1.94),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.34, 0.07, 1.38)
    J["elbow_" + _s] = (_x * 0.55, 0.1, 1.12)
    J["wrist_" + _s] = (_x * 0.7, 0.04, 0.88)
    J["hip_" + _s] = (_x * 0.15, 0.04, 0.77)
    J["knee_" + _s] = (_x * 0.17, 0.0, 0.43)
    J["ankle_" + _s] = (_x * 0.18, 0.06, 0.11)
    J["toe_" + _s] = (_x * 0.2, -0.17, 0.035)
J = {k: v3(v) for k, v in J.items()}

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH = 0, 1, 2, 3, 4, 5, 8

HS = 1.08
DZ = -0.02
HPIV = v3((0.0, 0.02, 1.48))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


def hinv(P):
    """World points -> the head's design coordinates (the inverse of hp)."""
    return (P - HPIV.astype(F)) / F(HS) + HPIV.astype(F) - np.array([0, 0, DZ], F)


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.176, 0.19, 0.186)) * HS
EYE_R = hr(0.037)


def eye_c(sx):
    return hp((sx * 0.07, -0.15, 1.676))


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


HAND_S = 1.0
CURLS = {"R": (0.95, 1.05, 0.7), "L": (1.45, 1.6, 1.2)}           # drawing hook / bow fist


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    fist = side == "L"
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.062, 0.032, 0.066)) * s, 0.029 * s, R=Rp), 0.028, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.034, 0.029, 0.05)) * s, R=Rp), 0.019, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.043, 0.0145, -0.0145, -0.043)
    lens = (0.96, 1.02, 0.96, 0.8)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.0205 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.011, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.015 * s), 0.009, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.011, (0.012, 0.007, 0.015), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.051 * s + n * 0.011
    if fist:
        d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
        d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:
        d1 = norm(f * 0.5 + t * 0.8 + n * 0.25)
        d2 = norm(f * 0.75 + t * 0.4 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.025 * s, 0.022 * s, 0.019 * s], k=0.008), 0.018, SKIN)


def foot(fd, side, s=1.04):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.1)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    fd.add(Sphere(an + v3((0, 0.042, -0.05)), 0.058 * s), 0.028, SKIN)
    fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.07)), v3((0.064, 0.116, 0.034)) * s, 0.032, R=Rz), 0.031, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.036 + v3((0, 0, -0.03)), v3((0.062, 0.085, 0.047)) * s, R=Rz), 0.028, SKIN)
    inner = -sx
    for i, (o, r) in enumerate(((0.049, 0.027), (0.02, 0.021), (-0.005, 0.019), (-0.028, 0.017), (-0.047, 0.016))):
        base = an + fwd * (0.162 - 0.011 * i - (0.0 if i else -0.004)) + rgt * (o * inner) + v3((0, 0, -0.08))
        tip = base + fwd * (0.029 + r * 0.4) + v3((0, 0, -0.004))
        base[2] = 0.024 + r * 0.55
        tip[2] = 0.019 + r * 0.5
        fd.add(RoundCone(base, tip, r, r * 0.92), 0.011, SKIN)
        tn = norm(tip - base)
        fd.paint(Ellipsoid(tip + v3((0, 0, r * 0.55)), (r * 0.7, r * 0.75, r * 0.35), R=rot_from_axes(y_axis=tn, z_axis=(0, 0, 1))), NAIL)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.05, 0.0, 0.0)), 0.024), 0.018, SKIN)


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.055, 1.588), (0.16, 0.138, 0.13)), 0.07, SKIN)                          # square jaw
    fd.add(E((0, -0.13, 1.502), (0.086, 0.068, 0.064)), 0.05, SKIN)                          # chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.118, 1.63), 0.05), 0.05, SKIN)                                # cheekbones
        fd.add(S((sx * 0.134, -0.04, 1.552), 0.06), 0.05, SKIN)                                # jaw corners
        pts = [hp((sx * 0.152, -0.055, 1.742)), hp((sx * 0.116, -0.13, 1.75)), hp((sx * 0.06, -0.172, 1.748)), hp((0.0, -0.182, 1.748))]
        fd.add(Chain(pts, [hr(0.012), hr(0.022), hr(0.026), hr(0.026)], k=hr(0.022)), hr(0.035), SKIN)     # brow ridge
    # straight brows, inner ends a little low: a focused look
    for sx in (-1, 1):
        pts = [hp((sx * 0.024, -0.214, 1.758)), hp((sx * 0.066, -0.205, 1.768)), hp((sx * 0.11, -0.182, 1.772)), hp((sx * 0.15, -0.142, 1.766))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.009), hr(0.011), hr(0.009), hr(0.004)], k=hr(0.007)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.017), hr(0.019), hr(0.016), hr(0.009)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0065)), Plane(ec + v3((0, 0, hr(0.022))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.005)), Plane(ec + v3((0, 0, -hr(0.027))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.019))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
    # straight nose
    fd.add(RoundCone(hp((0, -0.182, 1.722)), hp((0, -0.232, 1.632)), hr(0.017), hr(0.024)), hr(0.017), SKIN)
    fd.add(S((0, -0.236, 1.616), 0.03), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.03, -0.212, 1.603), 0.02), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.016, -0.229, 1.59)), v3((0.009, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # mouth: closed, the corners just turned up
    slot = [hp((-0.062, -0.166, 1.556)), hp((-0.032, -0.192, 1.545)), hp((0, -0.199, 1.543)), hp((0.032, -0.192, 1.545)), hp((0.062, -0.166, 1.556))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.058, -0.163, 1.559), (-0.03, -0.184, 1.553), (-0.008, -0.189, 1.556), (0.008, -0.189, 1.556), (0.03, -0.184, 1.553), (0.058, -0.163, 1.559)]
    lo_lip = [(-0.05, -0.166, 1.546), (-0.026, -0.184, 1.534), (0, -0.188, 1.531), (0.026, -0.184, 1.534), (0.05, -0.166, 1.546)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.004), hr(0.0065), hr(0.007), hr(0.007), hr(0.0065), hr(0.004)], k=hr(0.006)), hr(0.008), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.008), hr(0.009), hr(0.008), hr(0.005)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.178, 0.035, 1.66)), v3((0.026, 0.047, 0.06)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)


# ======================================================================================= body
def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.19), (0.27, 0.22, 0.27), R=euler(-0.12, 0, 0)), 0.0),
        (Ellipsoid((0, 0.12, 1.24), (0.3, 0.16, 0.2)), 0.06),
        (Ellipsoid((0.12, -0.14, 1.27), (0.13, 0.055, 0.085), R=euler(0.1, 0, 0.18)), 0.045),
        (Ellipsoid((-0.12, -0.14, 1.27), (0.13, 0.055, 0.085), R=euler(0.1, 0, -0.18)), 0.045),
        (Ellipsoid((0, -0.01, 0.98), (0.21, 0.185, 0.2)), 0.08),
        (Ellipsoid((0, 0.045, 0.82), (0.23, 0.18, 0.16)), 0.08),
    ]


def traps():
    return Ellipsoid((0, 0.1, 1.41), (0.24, 0.13, 0.09), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.065, 1.36), hp((0, 0.02, 1.575)), 0.1, hr(0.086))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.022, -0.005, 0.014)), 0.11)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        fd.add(RoundCone(sh, el, 0.095, 0.072), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.025, 0)), (0.085, 0.088, 0.125), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)
        fd.add(RoundCone(el, wr, 0.07, 0.054), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.09, 0.08, 0.13), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.055), 0.028, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.135, 0.088), 0.065, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.122, 0.115, 0.185), R=rot_from_axes(z_axis=kn - hip)), 0.048, SKIN)
        fd.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.068), 0.038, SKIN)
        fd.add(RoundCone(kn, an, 0.084, 0.056), 0.038, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.095, 0.092, 0.14), R=rot_from_axes(z_axis=an - kn)), 0.043, SKIN)
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
        fd.add(RoundBox(hp((sx * 0.009, -0.176, 1.548)), v3((0.008, 0.006, 0.007)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= helmet rim, hair, beard
# The helmet's rim runs from the brow at the front down to the nape at the back (design coordinates).
RIM_F = v3((0.0, -0.19, 1.81))
RIM_B = v3((0.0, 0.205, 1.64))
_RIM_SLOPE = (RIM_B[2] - RIM_F[2]) / (RIM_B[1] - RIM_F[1])
_RIM_N = norm(v3((0, -_RIM_SLOPE, 1.0)))


def rim_d(P):
    """Signed distance (design units) above the helmet rim plane; positive = under the helmet."""
    Q = hinv(P)
    return (Q - RIM_F.astype(F)) @ _RIM_N.astype(F)


def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.055, 1.588), (0.16, 0.138, 0.13)), 0.07)
    fd.add(E((0, -0.13, 1.502), (0.086, 0.068, 0.064)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.112, -0.118, 1.63)), hr(0.05)), 0.05)
        fd.add(Sphere(hp((sx * 0.134, -0.04, 1.552)), hr(0.06)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


def beard_field():
    """A short, neat black beard along the jaw and chin, sideburns up to the helmet, a trimmed moustache."""
    fd = Field("Beard")
    hull = head_hull()
    strands = lambda P: F(0.0035) * NOISE(P * np.array([60, 60, 16], F)) + F(0.002) * NOISE(P * F(110))
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.534) + F(0.15) * smoothstep(0.06, 0.175, ax)                       # chin covered, cheeks bare
        top = np.where(ax > F(0.16), F(1.75), top)                                   # sideburns up under the cheek guards
        lips = (x / F(0.074)) ** 2 + ((y + F(0.18)) / F(0.07)) ** 2 + ((z - F(1.548)) / F(0.03)) ** 2 - F(1.0)
        neck = np.where(y < F(-0.05), F(1.445), F(1.47)) - z
        back = np.where(ax > F(0.14), y - F(0.06), y - F(0.0))
        return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), neck)
    fd.add(Inter(Shell(hull, 0.006, 0.016, pad=0.06, disp=strands, disp_amp=0.006), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.006), 0.0)
    # a squared-off chin: the beard gathers into a short block under the lower lip
    fd.add(Ellipsoid(hp((0.0, -0.152, 1.468)), v3((0.078, 0.052, 0.055)) * HS, disp=strands, disp_amp=0.006), hr(0.022))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.212, 1.574)), hp((sx * 0.04, -0.199, 1.569)), hp((sx * 0.07, -0.171, 1.55))]
        fd.add(Lock(pts, [hr(0.012), hr(0.016), hr(0.006)], [hr(0.008), hr(0.009), hr(0.004)], [norm(v3((sx * 0.2, -1, 0.3)))] * 3,
                    k=hr(0.006), disp=strands, disp_amp=0.004), hr(0.006))
    return fd


def hair_field():
    """Black hair showing below the helmet at the back and sides, tied into a short tail at the nape."""
    fd = Field("Hair")
    strands = lambda P: F(0.004) * NOISE(P * np.array([55, 55, 14], F)) + F(0.002) * NOISE(P * F(100))
    def band(P):
        Q = hinv(P)
        r = rim_d(P)
        return np.maximum(np.maximum(-r - F(0.11), r - F(0.01)), F(-0.02) - Q[:, 1])            # below the rim, behind the ears
    fd.add(Inter(Shell(Ellipsoid(HEAD_C, HEAD_RAD), 0.012, 0.03, pad=0.06, disp=strands, disp_amp=0.006),
                 Func(band, HEAD_C - 0.4, HEAD_C + 0.4), 0.008), 0.0)
    nape = hp((0.0, 0.205, 1.6))
    pts = [nape, nape + v3((0, 0.035, -0.06)), nape + v3((0, 0.045, -0.14)), nape + v3((0.006, 0.04, -0.22))]
    fd.add(Lock(pts, [hr(0.04), hr(0.036), hr(0.028), hr(0.008)], [hr(0.03), hr(0.028), hr(0.022), hr(0.006)],
                [v3((0, 1, 0))] * 4, k=hr(0.012), disp=strands, disp_amp=0.004), hr(0.012))
    return fd


TAIL_TIE = hp((0.0, 0.25, 1.53))


# ======================================================================================= helmet (bronze)
HELM_C = HEAD_C + v3((0, 0.01, 0.03))
HELM_R = HEAD_RAD + v3((0.024, 0.024, 0.05))
HELM_TOP = HELM_C + v3((0, 0.012, HELM_R[2] + 0.09))


def helmet_hull():
    f = Field("HelmHull")
    f.add(Ellipsoid(HELM_C, HELM_R), 0.0)
    f.add(RoundCone(HELM_C + v3((0, 0.006, HELM_R[2] * 0.62)), HELM_TOP, 0.11, 0.012), 0.06)      # rising to a point
    return f


def helmet(fd):
    hull = helmet_hull()
    lo, hi = HELM_C - 0.35, HELM_C + 0.4
    fd.add(Inter(Shell(hull, 0.0, 0.014, pad=0.12), Func(lambda P: -rim_d(P), lo, hi), 0.003), 0.0)
    fd.add(Inter(Shell(hull, 0.007, 0.024, pad=0.12), Func(lambda P: np.abs(rim_d(P) - F(0.012)) - F(0.016), lo, hi), 0.004), 0.004)   # rolled rim
    fd.add(Sphere(HELM_TOP + v3((0, 0, 0.008)), 0.02), 0.01)                                  # knob
    # a raised rib from the brow over the crown
    rs = []
    for k in range(9):
        th = math.radians(-60 + 140 * k / 8)
        o = HELM_C + v3((0, -math.cos(th), math.sin(th))) * 0.6 + v3((0, 0, 0.04))
        h, ok = ray_hit(hull, [o], [norm(HELM_C + v3((0, 0, 0.04)) - o)], tmax=0.7)
        if ok[0] and rim_d(np.array([h[0]], F))[0] > 0.02:
            rs.append(h[0])
    if len(rs) >= 3:
        fd.add(Chain(rs, [0.009] * len(rs), k=0.006), 0.006)
    # rivets along the rim
    for k in range(14):
        a = 2 * math.pi * k / 14
        dirv = v3((math.sin(a), -math.cos(a), 0.0))
        q = RIM_F + v3((0, (RIM_B[1] - RIM_F[1]) * (0.5 - 0.5 * math.cos(a)), 0))
        zq = RIM_F[2] + _RIM_SLOPE * (q[1] - RIM_F[1]) + 0.02
        o = hp(v3((0, 0.02, zq))) + dirv * 0.6
        h, ok = ray_hit(hull, [o], [-dirv], tmax=0.7)
        if ok[0]:
            fd.add(Sphere(h[0] + dirv * 0.012, 0.0085), 0.003)


# ======================================================================================= bronze scale corselet
def corselet_base():
    b = Field("CorseletBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    return b


def scale_disp(P):
    """Rows of overlapping bronze scales: each scale's rounded lower edge stands proud, its top tucks under the row above."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    a = np.arctan2(x, -(y - F(0.06)))
    s = a * F(0.25)
    h, w = F(0.034), F(0.04)
    i = np.floor(z / h)
    fz = z / h - i
    def row(i, fz):
        c = s / w + F(0.5) * np.mod(i, 2)
        fc = c - np.floor(c) - F(0.5)
        edge = F(0.38) * (F(2) * fc) ** 2
        t = np.where(fz >= edge, F(1) - (fz - edge) * F(0.85), F(-1))
        return t, fc
    t1, fc1 = row(i, fz)
    t0, fc0 = row(i - 1, fz + F(1))
    t = np.where(t1 >= 0, t1, np.clip(t0, 0, 1))
    fc = np.where(t1 >= 0, fc1, fc0)
    side = smoothstep(0.43, 0.5, np.abs(fc)) * F(0.5)
    return -F(0.0065) * (np.clip(t, 0, 1) - side) + F(0.0012) * NOISE(P * F(70))


def corselet(fd):
    base = corselet_base()
    def keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        bottom = F(0.935) - z
        front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
        neck_z = F(1.47) - F(0.11) * front * np.exp(-(x / F(0.12)) ** 2)                    # a scooped neckline at the front
        top = z - neck_z
        oval = ((y - F(0.06)) / F(0.16)) ** 2 + ((z - F(1.39)) / F(0.22)) ** 2 - F(1.0)        # armholes
        arm = np.where(np.abs(x) > F(0.17), -oval * F(0.1), F(-1))
        strap = np.where(z > F(1.4), np.abs(np.abs(x) - F(0.15)) - F(0.075), F(-1))
        return np.maximum(np.maximum(np.maximum(bottom, top), arm), strap)
    fd.add(Inter(Shell(base, 0.024, 0.02, pad=0.12, disp=scale_disp, disp_amp=0.009), Func(keep, (-1, -1, 0.8), (1, 1, 1.6)), 0.005), 0.0)
    # bronze edging along the bottom of the corselet
    fd.add(Inter(Shell(base, 0.03, 0.016, pad=0.12), Func(lambda P: np.abs(P[:, 2] - F(0.948)) - F(0.014), (-1, -1, 0.8), (1, 1, 1.1)), 0.004), 0.004)


def buckle(fd):
    p, _ = ray_hit(Func(lambda P: kilt_base().eval(P) - F(0.075), (-1, -1, 0.7), (1, 1, 1.2)), [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    c = p[0]
    fd.add(RoundBox(c + v3((0, -0.004, 0)), (0.042, 0.012, 0.034), 0.008), 0.0)
    fd.sub(Ellipsoid(c + v3((0, -0.018, 0)), (0.022, 0.008, 0.016)), 0.004)
    fd.add(Sphere(c + v3((0, -0.012, 0)), 0.011), 0.004)


def bronze_field():
    fd = Field("Bronze")
    helmet(fd)
    corselet(fd)
    buckle(fd)
    return fd


# ======================================================================================= linen kilt, leather
BELT_Z = 0.955


def kilt_base():
    b = Field("KiltBase")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    b.add(RoundCone((0, 0.035, 0.9), (0, 0.035, 0.47), 0.235, 0.31), 0.08)
    return b


def linen_field():
    """White linen kilt to above the knee, finely pleated, a front panel hanging from the belt; a red woven border
    (label 5) along the hem and down the panel's edges, a blue stripe (6) above it."""
    fd = Field("Linen")
    base = kilt_base()
    def pleats(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        k = smoothstep(0.92, 0.75, P[:, 2])
        return F(0.0035) * np.sin(a * F(30)) * k + F(0.0015) * NOISE(P * F(25))
    def hem_z(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        return F(0.5) + F(0.03) * np.clip(np.cos(a), 0, 1) + F(0.008) * NOISE(P * F(8))
    def keep(P):
        return np.maximum(hem_z(P) - P[:, 2], P[:, 2] - F(0.97))
    fd.add(Inter(Shell(base, 0.022, 0.022, pad=0.1, disp=pleats, disp_amp=0.006), Func(keep, (-1, -1, 0.3), (1, 1, 1.1)), 0.006), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (hem_z(P) + F(0.04)), (-1, -1, 0.3), (1, 1, 0.7)), 5)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - (hem_z(P) + F(0.058))) - F(0.008), (-1, -1, 0.3), (1, 1, 0.7)), 6)
    # front panel
    def panel(P):
        return np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.085), P[:, 1] + F(0.0)), np.maximum(F(0.47) - P[:, 2], P[:, 2] - F(0.95)))
    fd.add(Inter(Shell(base, 0.048, 0.011, pad=0.1, disp=lambda P: F(0.0015) * NOISE(P * F(30)), disp_amp=0.003), Func(panel, (-0.3, -0.6, 0.4), (0.3, 0.2, 1.0)), 0.004), 0.004)
    fd.paint(Func(lambda P: np.maximum(np.maximum(np.maximum(F(0.062) - np.abs(P[:, 0]), np.abs(P[:, 0]) - F(0.092)), -P[:, 2] + F(0.5)),
                                       P[:, 1] + F(0.12)), (-0.3, -0.6, 0.4), (0.3, 0.0, 1.0)), 5)
    fd.paint(Func(lambda P: np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.09), P[:, 2] - F(0.505)), P[:, 1] + F(0.12)), (-0.3, -0.6, 0.4), (0.3, 0.0, 0.6)), 5)
    return fd


def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.07, 0.054)


def baldric_plane():
    """The quiver strap runs from his right shoulder across his chest to his left hip."""
    a, b = v3((-0.22, 0.0, 1.43)), v3((0.24, 0.0, 0.94))
    d = norm(b - a)
    n = norm(np.cross(d, v3((0, 1, 0))))
    return a, n


def leather_field():
    """Belt, the quiver strap, cheek guards, bracer (bow arm), wrist wrap, sandals, the tie on his tail of hair."""
    fd = Field("Leather")
    kb = kilt_base()
    fd.add(Inter(Shell(kb, 0.05, 0.028, pad=0.1), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(0.032), (-1, -1, 0.8), (1, 1, 1.1)), 0.005), 0.0)
    # quiver strap
    cb = corselet_base()
    a, n = baldric_plane()
    fd.add(Inter(Shell(cb, 0.052, 0.014, pad=0.12), Func(lambda P: np.abs((P - a.astype(F)) @ n.astype(F)) - F(0.028), (-1, -1, 0.8), (1, 1, 1.6)), 0.004), 0.0)
    # cheek guards hanging from the helmet rim over the ears
    hull = helmet_hull()
    def guard(P):
        Q = hinv(P)
        r = rim_d(P)
        bottom = -r - (F(0.13) - F(0.5) * (Q[:, 1] + F(0.02)) ** 2)          # rounded lower edge
        return np.maximum(np.maximum(F(0.105) - np.abs(Q[:, 0]), np.abs(Q[:, 1] + F(0.02)) - F(0.085)), np.maximum(r - F(0.004), bottom))
    fd.add(Inter(Shell(hull, 0.004, 0.012, pad=0.12), Func(guard, HELM_C - 0.4, HELM_C + 0.3), 0.006), 0.0)
    # bracer on the left forearm, a wrap on the right wrist
    for side, length in (("L", 0.075), ("R", 0.03)):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.66 if side == "L" else 0.86)
        fd.add(Inter(Shell(_forearm(side), 0.012, 0.016, pad=0.06), Func(lambda P, c=c, ax=ax, L=length: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(L), c - 0.25, c + 0.25), 0.004), 0.0)
        if side == "L":
            for j in (-1, 0, 1):
                cc = c + ax * (j * 0.04)
                fd.add(Inter(Shell(_forearm(side), 0.02, 0.006, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.006), cc - 0.2, cc + 0.2), 0.002), 0.003)
    # sandals: a sole, a strap over the toes, one over the instep, one round the ankle
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.1)), (0.074, 0.15, 0.011), 0.009, R=Rz), 0.0)
        ft = Field("FootHull")
        foot(ft, side)
        for c, rad in ((an + fwd * 0.14 + v3((0, 0, -0.07)), 0.022), (an + fwd * 0.05 + v3((0, 0, -0.035)), 0.02)):
            fd.add(Inter(Shell(ft, 0.006, 0.01, pad=0.05), Func(lambda P, c=c, fwd=fwd, rad=rad: np.abs((P - c.astype(F)) @ fwd.astype(F)) - F(rad * 0.6), c - 0.15, c + 0.15), 0.003), 0.002)
        fd.add(Torus(an + v3((0, 0.004, 0.035)), 0.06, 0.008), 0.003)
    fd.add(Torus(TAIL_TIE, hr(0.03), 0.009, R=rot_from_axes(z_axis=(0, 0.3, -1))), 0.004)
    return fd


# ======================================================================================= bow, string, the nocked arrows
BOW_HALF = 0.6


def bow_frame():
    """Rest pose: the bow passes through the left fist along its thumb axis; B = the bow's back (the way the arrow
    flies), A = along the bow (upper limb +), S = A x B."""
    wr, f, n, t = hand_frame("L")
    G = fist_center("L")
    A = norm(t)
    B = norm(f - A * (f @ A))
    S = np.cross(A, B)
    return G, A, B, S


def bow_back(a):
    """Offset along the bow's back: the limbs sweep back toward the archer and the tips flick forward (recurve)."""
    a = abs(a)
    t = min(1.0, max(0.0, (a - 0.72) / 0.28))
    return -0.16 * a ** 1.5 + 0.06 * t * t * (3 - 2 * t)


def bow_point(s):
    G, A, B, S = bow_frame()
    return G + A * (s * BOW_HALF) + B * bow_back(s)


def bow_tips():
    return bow_point(1.0), bow_point(-1.0)


def string_mid():
    t1, t2 = bow_tips()
    return (t1 + t2) / 2


def bow_field():
    """Recurve limbs (flat, thicker at the grip), the grip wrapped in red cord (label 5), bronze tip caps (6), a cream horn
    belly on the string side (7)."""
    fd = Field("Bow")
    G, A, B, S = bow_frame()
    ss = np.linspace(-1.0, 1.0, 31)
    pts = [bow_point(s) for s in ss]
    ws = [0.03 - 0.014 * abs(s) ** 1.2 for s in ss]
    ts = [0.026 - 0.013 * min(1.0, abs(s) * 1.6) for s in ss]
    grain = lambda P: F(0.001) * NOISE(P * F(80))
    fd.add(Lock(pts, ws, ts, [B] * len(pts), k=0.004, disp=grain, disp_amp=0.002), 0.0)
    fd.add(Ellipsoid(G, (0.026, 0.026, 0.07), R=rot_from_axes(z_axis=A, y_axis=B)), 0.012)            # the grip
    for s in (1.0, -1.0):
        tp = bow_point(s)
        d = norm(bow_point(s) - bow_point(s * 0.94))
        fd.add(RoundCone(tp - d * 0.04, tp + d * 0.012, 0.013, 0.01), 0.004)                          # bronze cap / nock
    def along(P):
        return ((P - G.astype(F)) @ A.astype(F)) / F(BOW_HALF)
    fd.paint(Func(lambda P: np.abs(along(P)) - F(0.12), G - 0.3, G + 0.3), 5)
    fd.paint(Func(lambda P: F(0.9) - np.abs(along(P)), G - 1.0, G + 1.0), 6)
    def belly(P):
        s = np.clip(along(P), -1, 1)
        back = F(-0.16) * np.abs(s) ** F(1.5)
        lb = (P - G.astype(F)) @ B.astype(F) - back
        return np.maximum(lb + F(0.004), np.maximum(np.abs(along(P)) - F(0.9), F(0.13) - np.abs(along(P))))
    fd.paint(Func(belly, G - 1.0, G + 1.0), 7)
    return fd


def string_field():
    fd = Field("String")
    t1, t2 = bow_tips()
    fd.add(Chain([t1, string_mid(), t2], [0.0048, 0.0048, 0.0048], k=0.002), 0.0)
    return fd


def draw_point():
    """Where the string sits in the right hand's hooked fingers (rest pose)."""
    wr, f, n, t = hand_frame("R")
    return wr + f * 0.152 * HAND_S + n * 0.026


ARROW_LEN = 1.0


def arrow_axis():
    wr, f, n, t = hand_frame("R")
    return draw_point(), norm(t)


def _arrow(fd, nock, ax, up, label_head=6, label_fl=8, label_shaft=0, shaft_r=0.0092, full=True):
    """One arrow from its nock along `ax`: a reed shaft, a leaf-shaped bronze head, three fletching vanes (chunky enough
    to read at game scale)."""
    side = norm(np.cross(ax, up))
    up = np.cross(side, ax)
    tip = nock + ax * ARROW_LEN
    if full:
        fd.add(Chain([nock + ax * 0.01, tip - ax * 0.06], [shaft_r, shaft_r], k=0.002), 0.0, label_shaft)
        fd.add(Ellipsoid(tip - ax * 0.034, (0.022, 0.007, 0.052), R=rot_from_axes(z_axis=ax, y_axis=up)), 0.005, label_head)
        fd.add(Ellipsoid(tip - ax * 0.034, (0.007, 0.012, 0.05), R=rot_from_axes(z_axis=ax, y_axis=up)), 0.004, label_head)
    fd.add(Cylinder(nock + ax * 0.012, shaft_r + 0.0025, 0.026, rr=0.003, R=rot_from_axes(z_axis=ax)), 0.002, label_shaft)
    for j in range(3):
        ang = j * 2 * math.pi / 3 + 0.4
        vd = side * math.cos(ang) + up * math.sin(ang)
        c = nock + ax * 0.1 + vd * 0.017
        fd.add(Ellipsoid(c, (0.0026, 0.019, 0.07), R=rot_from_axes(z_axis=ax, y_axis=vd)), 0.002, label_fl)


def arrows_field():
    """The pair nocked on the string: reed shafts, leaf-shaped bronze heads (label 6), red and white fletching (8)."""
    fd = Field("Arrows")
    p0, ax = arrow_axis()
    wr, f, n, t = hand_frame("R")
    up = norm(np.cross(ax, n))
    side = norm(np.cross(ax, up))
    for k, off in enumerate((-0.016, 0.016)):
        _arrow(fd, p0 + side * off + up * (0.003 * k), ax, up)
    return fd


# ======================================================================================= quiver
Q_BOT = v3((0.16, 0.31, 0.95))
Q_TOP = v3((-0.17, 0.38, 1.56))


def quiver_field():
    """Red leather quiver slung on his back, mouth over the right shoulder: ochre bands (label 5), a bronze rim (6),
    six arrows showing (shafts 7, fletching 8)."""
    fd = Field("Quiver")
    ax = norm(Q_TOP - Q_BOT)
    grain = lambda P: F(0.0015) * NOISE(P * F(40))
    fd.add(RoundCone(Q_BOT, Q_TOP, 0.05, 0.058, disp=grain, disp_amp=0.002), 0.0)
    fd.add(Sphere(Q_BOT - ax * 0.01, 0.052), 0.02)
    fd.sub(RoundCone(Q_TOP - ax * 0.08, Q_TOP + ax * 0.05, 0.047, 0.05), 0.006)               # open mouth
    fd.add(Torus(Q_TOP - ax * 0.006, 0.056, 0.009, R=rot_from_axes(z_axis=ax)), 0.004, 6)       # rim
    for k, u in enumerate((0.18, 0.5, 0.82)):
        c = lerp(Q_BOT, Q_TOP, u)
        fd.add(Torus(c, 0.052 + 0.006 * u, 0.007, R=rot_from_axes(z_axis=ax)), 0.004, 5)
    up = norm(np.cross(ax, v3((1, 0, 0))))
    side = norm(np.cross(ax, up))
    rs = np.random.RandomState(9)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        o = Q_TOP - ax * 0.05 + (side * math.cos(a) + up * math.sin(a)) * 0.022
        d = norm(ax + (side * math.cos(a) + up * math.sin(a)) * 0.12 + rs.normal(0, 0.03, 3))
        nock = o + d * (0.16 + rs.uniform(0, 0.03))
        fd.add(Chain([o, nock - d * 0.01], [0.0066, 0.0066], k=0.002), 0.002, 7)
        _arrow(fd, nock, -d, up, label_fl=8, label_shaft=7, full=False)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.236, 1.616)), 0.05, 0.55)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.1, -0.14, 1.61)), 0.06, 0.45), (hp((sx * 0.178, 0.035, 1.66)), 0.05, 0.5),
                (J["elbow_" + sd] + v3((0, 0.025, 0)), 0.06, 0.3), (J["knee_" + sd] + v3((0, -0.03, 0)), 0.07, 0.35),
                (J["shoulder_" + sd] + v3((0, 0, 0.1)), 0.11, 0.25)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.043, 0.0145, -0.0145, -0.043):
            pts.append((wr + f * 0.138 + t * o - n * 0.012, 0.03, 0.45))
        an = J["ankle_" + side]
        pts.append((an + v3((0, -0.17, -0.07)), 0.06, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "bronze_archer"
ROOT_NAME = "BronzeArcherHQ"
TEX_PREFIX = "archer"
MAT_NAME = "ArcherMat"
MESH_NAME = "Archer"
BASE_MODULE = "archer_base"
ANIM_MODULE = "anim_archer"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Bronze", "Linen", "Leather", "Bow", "String", "Arrows", "Quiver"]
REGION_PARTS = ("Skin", "Linen", "Bow", "Arrows", "Quiver")
BLACK_HAIR = {"name": "HQ_ArcherHair", "base": (0.08, 0.065, 0.06), "hi": (0.28, 0.23, 0.21), "low": (0.035, 0.03, 0.028),
              "streak": (0.05, 0.04, 0.035), "tint": (0.16, 0.11, 0.09)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_ArcherSkin", "base": (0.74, 0.5, 0.34), "ruddy": (0.78, 0.44, 0.32), "lips": (0.62, 0.36, 0.3),
                      "brow": ((0.06, 0.045, 0.04), (0.14, 0.1, 0.08)), "extra": ((8, (0.05, 0.035, 0.03), 0.5),)}),
    "Hair": ("hair", BLACK_HAIR),
    "Beard": ("hair", dict(BLACK_HAIR, name="HQ_ArcherBeard")),
    "Bronze": ("bronze", {"name": "HQ_ArcherBronze"}),
    "Linen": ("linen", {"name": "HQ_ArcherLinen"}),
    "Leather": ("leather", {"name": "HQ_ArcherLeather", "base": (0.36, 0.2, 0.11)}),
    "Bow": ("bow", {"name": "HQ_Bow"}),
    "String": ("cord", {}),
    "Arrows": ("arrows", {"name": "HQ_Arrows"}),
    "Quiver": ("quiver", {"name": "HQ_Quiver"}),
}
LOW_TARGETS = {"Skin": 6400, "Hair": 800, "Beard": 700, "Teeth": 60, "Bronze": 3600, "Linen": 1700, "Leather": 1700,
               "Bow": 900, "String": 120, "Arrows": 520, "Quiver": 1300}
AO_EXCLUDE = ["Bow", "String", "Arrows"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.74, 0.9, 1.07, 1.45)


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.92), (0, 0.045, 1.13)),
        "chest": ((0, 0.045, 1.13), (0, 0.065, 1.38)),
        "neck": ((0, 0.065, 1.38), hp((0, 0.02, 1.56))),
        "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.38,
    }


def prop_bones():
    p0, ax = arrow_axis()
    return [("arrow", p0, p0 + ax * 0.3, "hand.R")]


def extra_bones():
    t1, t2 = bow_tips()
    m = string_mid()
    return [("string_top", t1, m, "hand.L"), ("string_bot", t2, m, "hand.L")]


def _helmet_vertex(p):
    return p.z > 1.58


def bronze_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L"})
    groups = {}
    for v in ob.data.vertices:
        if _helmet_vertex(v.co):
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"head": 1.0})


def leather_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "forearm.R", "forearm.L", "hand.R", "hand.L",
                                                       "shin.R", "shin.L", "foot.R", "foot.L", "head"})
    a, n = baldric_plane()
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        w = None
        if p.z > 1.56 and abs(p.x) < 0.3:                                          # cheek guards
            w = {"head": 1.0}
        elif p.y > 0.17 and 1.44 < p.z <= 1.56 and abs(p.x) < 0.1:                  # the tie on his tail of hair
            w = {"head": 0.6, "neck": 0.4}
        elif 1.0 < p.z < 1.52 and abs(float((np.array(p) - a) @ n)) < 0.05 and abs(p.x) < 0.36:
            w = {"chest": 0.8, "spine": 0.2} if p.z < 1.25 else {"chest": 1.0}
        if w is not None:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, w)


def hair_weights(ob, skin_ob, arm):
    groups = {}
    z1 = hp((0, 0, 1.6))[2]
    for v in ob.data.vertices:
        p = v.co
        if p.z < z1:
            t = max(0.0, min(1.0, (z1 - p.z) / 0.2))
            _blend_add(ob, groups, v.index, {"head": 1.0 - 0.6 * t, "neck": 0.6 * t})
        else:
            _blend_add(ob, groups, v.index, {"head": 1.0})


def string_weights(ob, skin_ob, arm):
    G, A, B, S = bow_frame()
    groups = {}
    for v in ob.data.vertices:
        top = float((np.array(v.co) - G) @ A) > 0
        _blend_add(ob, groups, v.index, {"string_top" if top else "string_bot": 1.0})


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Beard": ("rigid", "head"), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Bronze": ("custom", bronze_weights), "Leather": ("custom", leather_weights),
        "Linen": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Bow": ("rigid", "hand.L"), "String": ("custom", string_weights), "Arrows": ("rigid", "arrow"),
        "Quiver": ("rigid", "chest"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("String", "Arrows"):
        return 0.6
    if part == "Bow":
        return 0.8
    if part == "Skin" and abs(c.x) > 0.6 and c.z < 1.0:
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0028 if fine else 0.0036),
        ("Beard", beard_field(), 0.0024 if fine else 0.0032),
        ("Bronze", bronze_field(), 0.0024 if fine else 0.0034),
        ("Linen", linen_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Bow", bow_field(), 0.0018 if fine else 0.0024),
        ("String", string_field(), 0.0012 if fine else 0.0016),
        ("Arrows", arrows_field(), 0.0014 if fine else 0.0018),
        ("Quiver", quiver_field(), 0.0022 if fine else 0.003),
    ]
