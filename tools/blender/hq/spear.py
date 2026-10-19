"""The Spear Guard (HQ tower, Bronze Age). Rest pose = A-pose, facing -Y, feet at z=0; right side = -X.

A tall young guardsman of a river city's gate: clean-shaven (a shadow of stubble), a strong cleft chin, heavy black
brows, long black hair in thin braids down his back under a rounded bronze helmet with cheek pieces and a tall red
horsehair crest that streams down behind; a bronze bell cuirass embossed with spirals, a red wool kilt with a cream
border, bronze greaves, sandals. A long spear with a leaf-shaped bronze head (red cord below it, a bronze butt spike) in
his right fist, a round shield on his left (held by a grip behind its boss): cream ox-hide, a red sun of eight rays round
the bronze boss, a red band, bronze studs and a bronze rim.

The spear and the shield are rigid in his fists: "frame" aims in anim_spear.py turn them with the hands."""
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

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, STUBBLE = 0, 1, 2, 3, 4, 5, 8, 9

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
CURLS = {"R": (1.45, 1.6, 1.2), "L": (1.45, 1.6, 1.2)}           # both fists: spear and shield grip


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    fist = True
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
    d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
    d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
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
def stubble_mask(P):
    """Jaw, chin and upper lip (design coordinates): a shadow of stubble."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.578) + F(0.03) * smoothstep(0.06, 0.15, ax)
    top = np.where(ax < F(0.05), F(1.6), top)                                         # the upper lip
    return np.maximum(np.maximum(z - top, F(1.44) - z), y - F(0.02))


def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.055, 1.588), (0.14, 0.132, 0.126)), 0.07, SKIN)                          # square jaw
    fd.add(E((0, -0.136, 1.5), (0.09, 0.07, 0.068)), 0.05, SKIN)                             # strong chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.118, 1.63), 0.05), 0.05, SKIN)                                # cheekbones
        fd.add(S((sx * 0.125, -0.045, 1.558), 0.05), 0.05, SKIN)                               # jaw corners
        pts = [hp((sx * 0.152, -0.055, 1.742)), hp((sx * 0.116, -0.13, 1.75)), hp((sx * 0.06, -0.172, 1.748)), hp((0.0, -0.182, 1.748))]
        fd.add(Chain(pts, [hr(0.012), hr(0.022), hr(0.026), hr(0.026)], k=hr(0.022)), hr(0.035), SKIN)     # brow ridge
    fd.sub(RoundCone(hp((0, -0.205, 1.513)), hp((0, -0.196, 1.47)), hr(0.0045), hr(0.006)), hr(0.008))     # cleft chin
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # heavy brows, their inner ends drawn down: a stern look
    for sx in (-1, 1):
        pts = [hp((sx * 0.024, -0.214, 1.752)), hp((sx * 0.066, -0.206, 1.766)), hp((sx * 0.11, -0.183, 1.774)), hp((sx * 0.152, -0.142, 1.768))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.011), hr(0.013), hr(0.011), hr(0.005)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.019), hr(0.021), hr(0.018), hr(0.01)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0065)), Plane(ec + v3((0, 0, hr(0.019))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.005)), Plane(ec + v3((0, 0, -hr(0.027))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.016))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
    # a strong nose with a bump on the bridge
    fd.add(RoundCone(hp((0, -0.182, 1.722)), hp((0, -0.236, 1.632)), hr(0.018), hr(0.026)), hr(0.017), SKIN)
    fd.add(S((0, -0.212, 1.684), 0.017), hr(0.012), SKIN)
    fd.add(S((0, -0.238, 1.616), 0.031), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.031, -0.212, 1.603), 0.021), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.016, -0.23, 1.59)), v3((0.009, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # mouth: a confident half-smile (his left corner up)
    slot = [hp((-0.06, -0.168, 1.552)), hp((-0.031, -0.193, 1.544)), hp((0, -0.199, 1.544)), hp((0.033, -0.191, 1.549)), hp((0.064, -0.163, 1.563))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.056, -0.165, 1.555), (-0.03, -0.185, 1.552), (-0.008, -0.19, 1.556), (0.008, -0.19, 1.557), (0.031, -0.184, 1.557), (0.06, -0.161, 1.566)]
    lo_lip = [(-0.048, -0.168, 1.543), (-0.026, -0.185, 1.533), (0, -0.189, 1.531), (0.027, -0.184, 1.537), (0.052, -0.165, 1.552)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.004), hr(0.0065), hr(0.007), hr(0.007), hr(0.0065), hr(0.004)], k=hr(0.006)), hr(0.008), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.008), hr(0.009), hr(0.008), hr(0.005)], k=hr(0.007)), hr(0.008), LIP)
    fd.add(S((0.068, -0.158, 1.566), 0.008), hr(0.006), SKIN)                                 # the smile's dimple
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
        fd.add(RoundBox(hp((sx * 0.009 + 0.004, -0.177, 1.549)), v3((0.008, 0.006, 0.007)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= helmet rim, hair
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
    fd.add(E((0, -0.055, 1.588), (0.14, 0.132, 0.126)), 0.07)
    fd.add(E((0, -0.136, 1.5), (0.09, 0.07, 0.068)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.112, -0.118, 1.63)), hr(0.05)), 0.05)
        fd.add(Sphere(hp((sx * 0.125, -0.045, 1.558)), hr(0.05)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


def back_hull():
    """The cuirass's outer surface (for laying the braids down his back)."""
    b = cuirass_base()
    return Func(lambda P: b.eval(P) - F(0.06), (-0.6, -0.4, 0.8), (0.6, 0.6, 1.7))


BRAID_X = (-0.1, -0.05, 0.0, 0.05, 0.1)


def braid_paths():
    """Five braids from the nape down his back to the shoulder blades, laid on the cuirass."""
    bh = back_hull()
    paths = []
    for i, x0 in enumerate(BRAID_X):
        pts = []
        for k in range(8):
            u = k / 7.0
            x = x0 * (1.0 + 0.9 * u) + 0.01 * math.sin(i * 1.7 + u * 3)
            z = 1.62 - 0.36 * u - 0.03 * abs(x0) * 6 * u
            o = v3((x, 0.75, z))
            h, ok = ray_hit(bh, [o], [v3((0, -1, 0))], tmax=0.9)
            p = h[0] if ok[0] and z < 1.52 else v3((x, 0.23 + 0.05 * max(0.0, 1.6 - z) / 0.1, z))
            if k == 0:
                p = hp((x0 * 0.9, 0.2, 1.63))
            pts.append(p + v3((0, 0.004, 0)))
        paths.append(pts)
    return paths


def hair_field():
    """Black hair showing below the helmet at the back and sides, and five thin braids down his back."""
    fd = Field("Hair")
    strands = lambda P: F(0.004) * NOISE(P * np.array([55, 55, 14], F)) + F(0.002) * NOISE(P * F(100))
    def band(P):
        Q = hinv(P)
        r = rim_d(P)
        return np.maximum(np.maximum(-r - F(0.11), r - F(0.01)), F(-0.02) - Q[:, 1])
    fd.add(Inter(Shell(Ellipsoid(HEAD_C, HEAD_RAD), 0.012, 0.03, pad=0.06, disp=strands, disp_amp=0.006),
                 Func(band, HEAD_C - 0.4, HEAD_C + 0.4), 0.008), 0.0)
    for i, pts in enumerate(braid_paths()):
        # a braid: plaited beads of hair, tilted left and right in turn, tapering, tied off at the end
        for k in range(len(pts) - 1):
            a, b = pts[k], pts[k + 1]
            d = norm(b - a)
            for j, u in enumerate((0.0, 0.5)):
                c = lerp(a, b, u)
                side = norm(np.cross(d, v3((0, 1, 0))))
                tilt = 0.45 if (k * 2 + j) % 2 == 0 else -0.45
                ax = norm(d + side * tilt)
                r = 0.017 - 0.007 * (k + u) / (len(pts) - 1)
                fd.add(Ellipsoid(c, (r, r * 0.8, r * 1.8), R=rot_from_axes(z_axis=ax, y_axis=v3((0, 1, 0)))), 0.004)
        end = pts[-1]
        fd.add(Ellipsoid(end + norm(pts[-1] - pts[-2]) * 0.03, (0.012, 0.01, 0.026),
                         R=rot_from_axes(z_axis=norm(pts[-1] - pts[-2]), y_axis=v3((0, 1, 0)))), 0.004)
    return fd


BRAID_TIES = None


def braid_ties():
    return [pts[-1] + norm(pts[-1] - pts[-2]) * 0.004 for pts in braid_paths()]


# ======================================================================================= helmet, crest (bronze, horsehair)
HELM_C = HEAD_C + v3((0, 0.012, 0.022))
HELM_R = HEAD_RAD + v3((0.026, 0.026, 0.046))


def helmet_hull():
    f = Field("HelmHull")
    f.add(Ellipsoid(HELM_C, HELM_R), 0.0)
    return f


def crest_ridge(lift=0.0, n=34):
    """Points along the helmet's top centre line, from above the brow over the crown to the back (+ lift outward)."""
    hull = helmet_hull()
    pts = []
    for k in range(n):
        th = math.radians(22 + 168 * k / (n - 1))          # 0 = straight ahead, 90 = straight up, 180 = straight back
        d = v3((0, -math.cos(th), math.sin(th)))
        o = HELM_C + d * 0.6
        h, ok = ray_hit(hull, [o], [-d], tmax=0.7)
        if ok[0] and rim_d(np.array([h[0]], F))[0] > 0.015:
            pts.append(h[0] + d * lift)
    return pts


def helmet(fd):
    hull = helmet_hull()
    lo, hi = HELM_C - 0.35, HELM_C + 0.4
    fd.add(Inter(Shell(hull, 0.0, 0.014, pad=0.12, disp=lambda P: F(0.0012) * NOISE(P * F(45)), disp_amp=0.002),
                 Func(lambda P: -rim_d(P), lo, hi), 0.003), 0.0)
    fd.add(Inter(Shell(hull, 0.007, 0.024, pad=0.12), Func(lambda P: np.abs(rim_d(P) - F(0.012)) - F(0.016), lo, hi), 0.004), 0.004)   # rolled rim
    # the crest holder: a bronze ridge over the crown, a knob at the front
    ridge = crest_ridge(lift=0.004)
    fd.add(Chain(ridge, [0.014] * len(ridge), k=0.006), 0.006)
    fd.add(Sphere(ridge[0] + v3((0, -0.006, 0.004)), 0.02), 0.006)
    # cheek pieces hanging from the rim over the cheeks and jaw (a shell of the face), a rivet on each
    face = head_hull()
    def guard(P):
        Q = hinv(P)
        r = rim_d(P)
        y = Q[:, 1] + F(0.02)
        bottom = F(1.556) - F(0.5) * y * y + F(0.05) * np.clip(-y - F(0.04), 0, 1) - Q[:, 2]      # rounded, cut back at the front
        front = F(-0.152) + F(0.2) * np.clip(F(1.69) - Q[:, 2], 0, 0.2) - Q[:, 1]                 # over the cheek, clear of the eye
        return np.maximum(np.maximum(F(0.105) - np.abs(Q[:, 0]), np.maximum(front, Q[:, 1] - F(0.075))), np.maximum(r - F(0.012), bottom))
    fd.add(Inter(Shell(face, 0.016, 0.012, pad=0.12), Func(guard, HEAD_C - 0.4, HEAD_C + 0.3), 0.005), 0.0)
    for sx in (-1, 1):
        o = hp((sx * 0.5, 0.0, 1.66))
        h, ok = ray_hit(Func(lambda P: face.eval(P) - F(0.023), HEAD_C - 0.5, HEAD_C + 0.5), [o], [v3((-sx, 0, 0))], tmax=0.6)
        if ok[0]:
            fd.add(Sphere(h[0], 0.0105), 0.003)
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


def crest_field():
    """A tall red horsehair crest from the brow over the crown, streaming down behind the helmet."""
    fd = Field("Crest")
    ridge = crest_ridge(lift=0.0)
    n = len(ridge)
    hairs = lambda P: F(0.0025) * NOISE(P * np.array([90, 14, 90], F)) + F(0.0015) * NOISE(P * F(130))
    pts, ws, ts, ns = [], [], [], []
    for k, p in enumerate(ridge):
        u = k / (n - 1)
        h = 0.07 + 0.08 * math.sin(min(1.0, u * 1.25) * math.pi * 0.5) - 0.02 * max(0.0, u - 0.8) / 0.2
        out = norm(p - HELM_C)
        pts.append(p + out * (h * 0.5 + 0.012))
        ws.append(h * 0.5)
        ts.append(0.02 - 0.004 * u)
        ns.append(v3((1, 0, 0)))
    # the tail streaming down behind the head
    last, prev = pts[-1], pts[-2]
    d = norm(last - prev)
    for j, (dy, dz) in enumerate(((0.05, -0.06), (0.085, -0.15), (0.1, -0.25))):
        pts.append(last + v3((0, dy, dz)))
        ws.append(ws[-1] * (0.8 if j == 0 else 0.7))
        ts.append(ts[-1] * 0.85)
        ns.append(v3((1, 0, 0)))
    fd.add(Lock(pts, ws, ts, ns, k=0.012, disp=hairs, disp_amp=0.004), 0.0)
    # a few loose locks at the end of the tail
    for sx in (-1, 0, 1):
        a = pts[-1] + v3((sx * 0.012, 0.0, 0.02))
        fd.add(Chain([a, a + v3((sx * 0.012, 0.015, -0.06)), a + v3((sx * 0.02, 0.025, -0.1))], [0.01, 0.008, 0.003], k=0.006,
                     disp=hairs, disp_amp=0.003), 0.008)
    return fd


# ======================================================================================= bronze bell cuirass, greaves
def cuirass_base():
    b = Field("CuirassBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    return b


def _cut_top(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
    neck_z = F(1.49) - F(0.05) * front * np.exp(-(x / F(0.13)) ** 2)
    return z - neck_z


def _cut_arm(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    oval = ((y - F(0.06)) / F(0.16)) ** 2 + ((z - F(1.39)) / F(0.22)) ** 2 - F(1.0)
    arm = np.where(np.abs(x) > F(0.17), -oval * F(0.1), F(-1))
    strap = np.where(z > F(1.42), np.abs(np.abs(x) - F(0.14)) - F(0.085), F(-1))
    return np.maximum(arm, strap)


def cuirass(fd):
    base = cuirass_base()
    hammer = lambda P: F(0.0012) * NOISE(P * F(45))
    def keep(P):
        return np.maximum(np.maximum(F(0.935) - P[:, 2], _cut_top(P)), _cut_arm(P))
    fd.add(Inter(Shell(base, 0.03, 0.02, pad=0.12, disp=hammer, disp_amp=0.002), Func(keep, (-1, -1, 0.8), (1, 1, 1.6)), 0.005), 0.0)
    # the bell's flared lower edge
    fd.add(Inter(Shell(base, 0.05, 0.016, pad=0.12), Func(lambda P: np.abs(P[:, 2] - F(0.947)) - F(0.017), (-1, -1, 0.8), (1, 1, 1.1)), 0.006), 0.006)
    # rolled rims round the neck and the armholes
    def edge(P):
        k = np.maximum(_cut_top(P), _cut_arm(P))
        return np.maximum(np.abs(k + F(0.006)) - F(0.009), F(0.97) - P[:, 2])
    fd.add(Inter(Shell(base, 0.042, 0.013, pad=0.12), Func(edge, (-1, -1, 0.9), (1, 1, 1.6)), 0.004), 0.004)
    # embossed: a spiral on each breast and a curved line under them
    outer = Func(lambda P: base.eval(P, margin=0.06) - F(0.04), (-0.6, -0.6, 0.8), (0.6, 0.6, 1.6))
    for sx in (-1, 1):
        c = v3((sx * 0.115, 0.0, 1.275))
        pts = []
        for k in range(26):
            th = k / 25.0 * 2.6 * math.pi
            r = 0.012 + 0.0085 * th
            ang = sx * th + (math.pi if sx < 0 else 0.0)
            o = c + v3((math.cos(ang) * r, -0.6, math.sin(ang) * r * 0.95))
            h, ok = ray_hit(outer, [o], [v3((0, 1, 0))], tmax=0.8)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 4:
            fd.add(Chain(pts, [0.0045] * len(pts), k=0.003), 0.004)
    under = []
    for k in range(17):
        x = -0.22 + 0.44 * k / 16
        z = 1.165 + 0.05 * (abs(x) / 0.22) ** 1.6
        h, ok = ray_hit(outer, [v3((x, -0.6, z))], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            under.append(h[0])
    if len(under) > 4:
        fd.add(Chain(under, [0.005] * len(under), k=0.003), 0.004)


def greaves(fd):
    """Bronze greaves from below the knee to above the ankle, open at the back of the calf, with rolled edges."""
    for side in ("R", "L"):
        kn, an = J["knee_" + side], J["ankle_" + side]
        shin = Field("Shin")
        shin.add(RoundCone(kn, an, 0.084, 0.056), 0.0)
        shin.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.095, 0.092, 0.14), R=rot_from_axes(z_axis=an - kn)), 0.043)
        z_top, z_bot = kn[2] - 0.045, an[2] + 0.075
        def keep(P, z_top=z_top, z_bot=z_bot, yb=kn[1] + 0.055):
            return np.maximum(np.maximum(P[:, 2] - F(z_top), F(z_bot) - P[:, 2]), P[:, 1] - F(yb))
        fd.add(Inter(Shell(shin, 0.016, 0.011, pad=0.08), Func(keep, kn - 0.3, an + v3((0.3, 0.3, 0.1))), 0.004), 0.0)
        for zz in (z_top - 0.006, z_bot + 0.006):
            fd.add(Inter(Shell(shin, 0.024, 0.01, pad=0.08),
                         Func(lambda P, zz=zz, yb=kn[1] + 0.05: np.maximum(np.abs(P[:, 2] - F(zz)) - F(0.008), P[:, 1] - F(yb)),
                              kn - 0.3, an + v3((0.3, 0.3, 0.1))), 0.003), 0.003)


def buckle(fd):
    p, _ = ray_hit(Func(lambda P: kilt_base().eval(P) - F(0.075), (-1, -1, 0.7), (1, 1, 1.2)), [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    c = p[0]
    fd.add(RoundBox(c + v3((0, -0.004, 0)), (0.042, 0.012, 0.034), 0.008), 0.0)
    fd.sub(Ellipsoid(c + v3((0, -0.018, 0)), (0.022, 0.008, 0.016)), 0.004)
    fd.add(Sphere(c + v3((0, -0.012, 0)), 0.011), 0.004)


def bronze_field():
    fd = Field("Bronze")
    helmet(fd)
    cuirass(fd)
    greaves(fd)
    buckle(fd)
    for t in braid_ties():
        fd.add(Sphere(t, 0.011), 0.0)
    return fd


# ======================================================================================= wool kilt, leather
BELT_Z = 0.955


def kilt_base():
    b = Field("KiltBase")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    b.add(RoundCone((0, 0.035, 0.9), (0, 0.035, 0.47), 0.235, 0.31), 0.08)
    return b


def kilt_field():
    """Red wool kilt to above the knee, pleated, a front panel hanging from the belt; a cream woven border (label 5)
    along the hem and down the panel's edges, a dark stripe (6) above it."""
    fd = Field("Kilt")
    base = kilt_base()
    def pleats(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        k = smoothstep(0.92, 0.75, P[:, 2])
        return F(0.004) * np.sin(a * F(24)) * k + F(0.0015) * NOISE(P * F(25))
    def hem_z(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        return F(0.5) + F(0.03) * np.clip(np.cos(a), 0, 1) + F(0.008) * NOISE(P * F(8))
    def keep(P):
        return np.maximum(hem_z(P) - P[:, 2], P[:, 2] - F(0.97))
    fd.add(Inter(Shell(base, 0.022, 0.022, pad=0.1, disp=pleats, disp_amp=0.006), Func(keep, (-1, -1, 0.3), (1, 1, 1.1)), 0.006), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (hem_z(P) + F(0.045)), (-1, -1, 0.3), (1, 1, 0.7)), 5)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - (hem_z(P) + F(0.064))) - F(0.008), (-1, -1, 0.3), (1, 1, 0.7)), 6)
    def panel(P):
        return np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.085), P[:, 1] + F(0.0)), np.maximum(F(0.47) - P[:, 2], P[:, 2] - F(0.95)))
    fd.add(Inter(Shell(base, 0.048, 0.011, pad=0.1, disp=lambda P: F(0.0015) * NOISE(P * F(30)), disp_amp=0.003), Func(panel, (-0.3, -0.6, 0.4), (0.3, 0.2, 1.0)), 0.004), 0.004)
    fd.paint(Func(lambda P: np.maximum(np.maximum(np.maximum(F(0.062) - np.abs(P[:, 0]), np.abs(P[:, 0]) - F(0.092)), -P[:, 2] + F(0.5)),
                                       P[:, 1] + F(0.12)), (-0.3, -0.6, 0.4), (0.3, 0.0, 1.0)), 5)
    fd.paint(Func(lambda P: np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.09), P[:, 2] - F(0.505)), P[:, 1] + F(0.12)), (-0.3, -0.6, 0.4), (0.3, 0.0, 0.6)), 5)
    return fd


def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.07, 0.054)


def leather_field():
    """Belt, wrist wraps, sandals."""
    fd = Field("Leather")
    kb = kilt_base()
    fd.add(Inter(Shell(kb, 0.05, 0.028, pad=0.1), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(0.032), (-1, -1, 0.8), (1, 1, 1.1)), 0.005), 0.0)
    for side in ("L", "R"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.84)
        fd.add(Inter(Shell(_forearm(side), 0.012, 0.016, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.04), c - 0.25, c + 0.25), 0.004), 0.0)
        for j in (-1, 1):
            cc = c + ax * (j * 0.022)
            fd.add(Inter(Shell(_forearm(side), 0.02, 0.006, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.006), cc - 0.2, cc + 0.2), 0.002), 0.003)
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
    return fd


# ======================================================================================= spear, shield
SPEAR_FWD = 1.36          # grip -> spear point
SPEAR_BACK = 0.98         # grip -> butt spike's tip
SPEAR_R = 0.0175


def spear_axis():
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t


def spear_field():
    """Ash shaft, a leaf-shaped bronze head with a midrib on a socket (label 6), red cord bound below it (5), a bronze
    butt spike (6)."""
    fd = Field("Spear")
    a0, ax = spear_axis()
    wr, f, n, t = hand_frame("R")
    flat = norm(np.cross(ax, n))
    grain = lambda P: F(0.0018) * NOISE(P * F(70))
    fd.add(Chain([a0 - ax * (SPEAR_BACK - 0.07), a0 + ax * (SPEAR_FWD - 0.26)], [SPEAR_R, SPEAR_R * 0.92], k=0.0, disp=grain, disp_amp=0.002), 0.0)
    sock0, sock1 = a0 + ax * (SPEAR_FWD - 0.27), a0 + ax * (SPEAR_FWD - 0.2)
    fd.add(RoundCone(sock0, sock1, SPEAR_R + 0.004, SPEAR_R + 0.001), 0.003, 6)
    blade_c = a0 + ax * (SPEAR_FWD - 0.1)
    fd.add(Ellipsoid(blade_c, (0.034, 0.0075, 0.112), R=rot_from_axes(z_axis=ax, y_axis=n)), 0.006, 6)
    fd.add(Chain([sock1 - ax * 0.01, a0 + ax * (SPEAR_FWD - 0.005)], [0.0105, 0.003], k=0.004), 0.006, 6)        # midrib to the point
    for k in range(5):                                                                            # cord binding
        c = a0 + ax * (SPEAR_FWD - 0.3 - 0.013 * k)
        fd.add(Torus(c, SPEAR_R + 0.003, 0.0045, R=rot_from_axes(z_axis=ax)), 0.002, 5)
    b0 = a0 - ax * (SPEAR_BACK - 0.08)
    fd.add(RoundCone(b0, b0 - ax * 0.03, SPEAR_R + 0.003, SPEAR_R + 0.001), 0.002, 6)
    fd.add(RoundCone(b0 - ax * 0.03, a0 - ax * SPEAR_BACK, SPEAR_R, 0.003), 0.004, 6)
    return fd


SHIELD_R = 0.33
SHIELD_DOME = 0.055       # how far the face bulges out at the boss
SHIELD_T = 0.02


def shield_frame():
    """Rest pose: the shield's grip is in the left fist along the fist's thumb axis U; its face points along the
    knuckles N; S = N x U."""
    wr, f, n, t = hand_frame("L")
    G = fist_center("L")
    U = norm(t)
    N = norm(f - U * (f @ U))
    S = np.cross(N, U)
    return G, N, U, S


SHIELD_BACK = 0.045       # grip -> the shield's back at the middle


def shield_field():
    """A round shield: a convex disc of hide (cream, label 0) on a frame, painted with a red band and a red sun of eight
    rays round the bronze boss (5); a bronze rim, boss and studs (6); the wooden grip behind the boss (7)."""
    fd = Field("Shield")
    G, N, U, S = shield_frame()
    C = G + N * SHIELD_BACK                                     # middle of the shield's back
    Rs = (SHIELD_R ** 2 + SHIELD_DOME ** 2) / (2 * SHIELD_DOME)  # sphere through the rim and the bulge
    sc = C + N * (SHIELD_DOME - Rs)
    hide = lambda P: F(0.0012) * NOISE(P * F(40))
    def disc(P):
        q = P - C.astype(F)
        h = q @ N.astype(F)
        rr = np.sqrt(np.maximum((q * q).sum(1) - h * h, 0))
        return np.maximum(rr - F(SHIELD_R), F(-0.1) - h)              # (only the near cap of the sphere)
    # (the disc goes first: an intersection takes its bounds from its first shape, and the sphere's are huge)
    fd.add(Inter(Func(disc, C - 0.4, C + 0.4),
                 Shell(Sphere(sc, Rs), SHIELD_T * 0.5, SHIELD_T, pad=0.05, disp=hide, disp_amp=0.002), 0.006), 0.0)
    # rim, boss, studs
    rim_c = sc + N * math.sqrt(max(Rs * Rs - SHIELD_R * SHIELD_R, 0.0))
    fd.add(Torus(rim_c + N * 0.006, SHIELD_R - 0.006, 0.017, R=rot_from_axes(z_axis=N, y_axis=U)), 0.006, 6)
    face = C + N * (SHIELD_DOME + SHIELD_T)
    fd.add(Inter(Sphere(face - N * 0.025, 0.07), Plane(face - N * 0.02, -N), 0.004), 0.008, 6)
    fd.add(Torus(face - N * 0.018, 0.068, 0.008, R=rot_from_axes(z_axis=N, y_axis=U)), 0.004, 6)
    def on_face(r, a):
        d = U * math.cos(a) + S * math.sin(a)
        dz = math.sqrt(max(Rs * Rs - r * r, 0.0)) - (Rs - SHIELD_DOME)
        return C + d * r + N * (dz + SHIELD_T)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        fd.add(Sphere(on_face(0.265, a), 0.013), 0.003, 6)
    # the grip behind the boss
    fd.add(RoundCone(G - U * 0.07, G + U * 0.07, 0.016, 0.016), 0.01, 7)
    fd.add(RoundCone(C - N * 0.002 - U * 0.09, C - N * 0.002 + U * 0.09, 0.012, 0.012), 0.008, 7)
    # painted: a red band inside the studs and a sun of eight rays round the boss
    def front_side(P):                                          # < 0 on the outer half of the hide
        d = P - sc.astype(F)
        return F(Rs + SHIELD_T * 0.5) - np.sqrt((d * d).sum(1))
    def band(P):
        q = P - C.astype(F)
        rr = np.sqrt(np.maximum((q * q).sum(1) - (q @ N.astype(F)) ** 2, 0))
        return np.maximum(np.abs(rr - F(0.27)) - F(0.035), front_side(P))
    fd.paint(Func(band, C - 0.5, C + 0.5), 5)
    def rays(P):
        q = P - C.astype(F)
        u, s = q @ U.astype(F), q @ S.astype(F)
        rr = np.sqrt(u * u + s * s)
        a = np.arctan2(s, u)
        m = np.mod(a + F(math.pi / 8), F(math.pi / 4)) - F(math.pi / 8)
        width = F(0.02) + F(0.035) * np.clip((F(0.19) - rr) / F(0.12), 0, 1)            # rays wide at the boss, pointed
        ray = np.abs(m) * rr - width * np.clip((F(0.2) - rr) / F(0.13), 0, 1)
        return np.maximum(np.maximum(ray, F(0.06) - rr), np.maximum(rr - F(0.205), front_side(P)))
    fd.paint(Func(rays, C - 0.5, C + 0.5), 5)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.238, 1.616)), 0.05, 0.55)]
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
GLB_NAME = "spear_guard"
ROOT_NAME = "SpearGuardHQ"
TEX_PREFIX = "guard"
MAT_NAME = "GuardMat"
MESH_NAME = "Guard"
BASE_MODULE = "spear_base"
ANIM_MODULE = "anim_spear"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Crest", "Bronze", "Kilt", "Leather", "Spear", "Shield"]
REGION_PARTS = ("Skin", "Kilt", "Spear", "Shield")
BLACK_HAIR = {"name": "HQ_GuardHair", "base": (0.08, 0.065, 0.06), "hi": (0.28, 0.23, 0.21), "low": (0.035, 0.03, 0.028),
              "streak": (0.05, 0.04, 0.035), "tint": (0.16, 0.11, 0.09)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_GuardSkin", "base": (0.8, 0.56, 0.4), "ruddy": (0.82, 0.48, 0.36), "lips": (0.66, 0.38, 0.32),
                      "brow": ((0.06, 0.045, 0.04), (0.14, 0.1, 0.08)),
                      "extra": ((LASH, (0.05, 0.035, 0.03), 0.5), (STUBBLE, (0.36, 0.27, 0.24), 0.55, 0.45))}),
    "Hair": ("hair", BLACK_HAIR),
    "Crest": ("hair", {"name": "HQ_Crest", "base": (0.68, 0.1, 0.06), "hi": (0.96, 0.34, 0.18), "low": (0.32, 0.04, 0.03),
                       "streak": (0.5, 0.06, 0.04), "tint": (0.82, 0.22, 0.08)}),
    "Bronze": ("bronze", {"name": "HQ_GuardBronze"}),
    "Kilt": ("wool", {"name": "HQ_GuardKilt"}),
    "Leather": ("leather", {"name": "HQ_GuardLeather", "base": (0.36, 0.2, 0.11)}),
    "Spear": ("spear_shaft", {"name": "HQ_Spear"}),
    "Shield": ("shield_hide", {"name": "HQ_Shield"}),
}
LOW_TARGETS = {"Skin": 6400, "Hair": 1100, "Crest": 900, "Teeth": 60, "Bronze": 4400, "Kilt": 1700, "Leather": 1300,
               "Spear": 520, "Shield": 1500}
AO_EXCLUDE = ["Spear", "Shield"]
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
    return []                       # the spear and the shield are rigid in the fists


def bronze_weights(ob, skin_ob, arm):
    """Cuirass from the torso, greaves from the shins, the helmet (with its cheek pieces) and the braid ties rigid."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "shin.R", "shin.L"})
    ties = braid_ties()
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        w = None
        if p.z > 1.56 and abs(p.x) < 0.32 and p.y < 0.32:
            w = {"head": 1.0}
        else:
            for t in ties:
                if (p - _vec(t)).length < 0.03:
                    w = hair_w(p)
                    break
        if w is not None:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, w)


def _vec(p):
    from mathutils import Vector
    return Vector((float(p[0]), float(p[1]), float(p[2])))


def hair_w(p):
    """The hair under the helmet goes with the head; the braids down his back pass from the head to the chest."""
    z1 = hp((0, 0, 1.6))[2]
    if p.z >= z1:
        return {"head": 1.0}
    t = max(0.0, min(1.0, (z1 - p.z) / 0.24))
    if p.y > 0.12:                                   # braids on his back
        return {"head": max(0.0, 1.0 - 1.6 * t), "neck": 0.6 * (1.0 - abs(2 * t - 1.0)), "chest": max(0.0, 1.6 * t - 0.6)}
    return {"head": 1.0 - 0.6 * t, "neck": 0.6 * t}


def hair_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, hair_w(v.co))


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Crest": ("rigid", "head"), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Bronze": ("custom", bronze_weights),
        "Leather": ("transfer", TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Kilt": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Spear": ("rigid", "hand.R"), "Shield": ("rigid", "hand.L"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Spear":
        return 0.6
    if part == "Shield":
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
        ("Crest", crest_field(), 0.0026 if fine else 0.0036),
        ("Bronze", bronze_field(), 0.0024 if fine else 0.0034),
        ("Kilt", kilt_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Spear", spear_field(), 0.0016 if fine else 0.0022),
        ("Shield", shield_field(), 0.0024 if fine else 0.0032),
    ]
