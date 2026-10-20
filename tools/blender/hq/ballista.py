"""The Ballista (HQ tower, Iron Age): a great crossbow on a timber stand, and the hill-fort engineer who works it. Rest
pose: he stands in an A-pose facing -Y (the way it shoots), feet at z = 0, the ballista on his left (+X); it is drawn
(its arms swept back, the string on the claw, a bolt in the groove).

Him: big and barrel-chested, a hooked nose and heavy black brows, a short full black beard and a heavy moustache drooping
past the corners of his mouth; an iron helmet with a knob on its crown, a short neck guard and cheek pieces; a blue wool
tunic checked in dark red with thin yellow lines, to mid-thigh with short sleeves, a wide leather belt with an iron
buckle, checked brown trousers, leather shoes with thongs bound up his shins, leather wrist wraps, iron armlets above
the elbows. An iron-bound mallet, rigid in his right fist.

The ballista: an upright post on four splayed feet with braces and iron straps, a swivel and a fork on top carrying the
stock on its trunnion pin; on the stock the slider in its dovetail, the bolt groove along its top, the claw and its
trigger lever at its back end; at the front the spring frame (top and bottom plates, four uprights, iron straps) with two
twisted rope skeins under big iron washers and their levers, the two bow arms (iron-capped) and the bowstring drawn back
to the claw; at the back the windlass (rope drum, iron ratchet wheel, a crank on his side) and the rope to the slider.
Behind him a bundle of spare bolts on two log rests (the top one is the one he lifts).

Painted labels on the engine (material `siege`, iron fittings): 0 wood with the grain along Y, 10 along X, 11 along Z;
5 red ochre, 7 blue paint; 6 iron; 8 rope and sinew; 9 leather."""
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
    J["shoulder_" + _s] = (_x * 0.36, 0.07, 1.36)
    J["elbow_" + _s] = (_x * 0.58, 0.1, 1.1)
    J["wrist_" + _s] = (_x * 0.73, 0.04, 0.86)
    J["hip_" + _s] = (_x * 0.16, 0.04, 0.75)
    J["knee_" + _s] = (_x * 0.18, 0.0, 0.42)
    J["ankle_" + _s] = (_x * 0.19, 0.06, 0.11)
    J["toe_" + _s] = (_x * 0.21, -0.17, 0.035)
J = {k: v3(v) for k, v in J.items()}

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, STUBBLE = 0, 1, 2, 3, 4, 5, 8, 9
GX, GZ, RED, BLUE, IRON, ROPE, HIDE = 10, 11, 5, 7, 6, 8, 9          # engine labels (wood grain Y is 0)

HS = 1.08
DZ = -0.04
HPIV = v3((0.0, 0.02, 1.46))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


def hinv(P):
    """World points -> the head's design coordinates (the inverse of hp)."""
    return (P - HPIV.astype(F)) / F(HS) + HPIV.astype(F) - np.array([0, 0, DZ], F)


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.18, 0.19, 0.186)) * HS
EYE_R = hr(0.036)


def eye_c(sx):
    return hp((sx * 0.07, -0.148, 1.674))


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


HAND_S = 1.06
CURLS = {"R": (1.45, 1.6, 1.2), "L": (0.95, 1.15, 0.85)}       # right fist round the mallet, left hand a loose grip


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
        d1 = norm(f * 0.55 + t * 0.7 + n * 0.4)
        d2 = norm(f * 0.6 + t * 0.2 + n * 0.55)
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


# ======================================================================================= head (shaven, the beard is its own part)
def fringe_mask(P):
    """The shaven fringe round the back and sides of his scalp (design coordinates): a shadow of short dark hair."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.775) - F(0.03) * smoothstep(0.0, 0.18, y)
    band = np.maximum(z - top, F(1.6) - z)
    front = F(-0.045) - y + F(0.05) * smoothstep(1.68, 1.76, z)
    ear = np.where((ax > F(0.165)) & (y < F(0.085)) & (z < F(1.72)), F(1.0), F(-1.0))
    return np.maximum(np.maximum(band, front), ear)


def skull():
    fd = Field("Skull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    fd.add(Ellipsoid(hp((0, 0.02, 1.79)), v3((0.165, 0.175, 0.12)) * HS), 0.08)
    return fd


def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.79), (0.165, 0.175, 0.12)), 0.08, SKIN)                          # a broad, bare dome
    fd.add(E((0, -0.052, 1.59), (0.15, 0.136, 0.128)), 0.07, SKIN)                         # heavy jaw (under the beard)
    fd.add(E((0, -0.132, 1.5), (0.09, 0.07, 0.068)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.116, -0.12, 1.628), 0.055), 0.05, SKIN)                             # full cheeks
        fd.add(S((sx * 0.13, -0.045, 1.556), 0.052), 0.05, SKIN)
        pts = [hp((sx * 0.156, -0.055, 1.744)), hp((sx * 0.118, -0.134, 1.756)), hp((sx * 0.062, -0.178, 1.754)), hp((0.0, -0.188, 1.75))]
        fd.add(Chain(pts, [hr(0.012), hr(0.021), hr(0.025), hr(0.023)], k=hr(0.022)), hr(0.032), SKIN)     # heavy brow ridge
    fd.paint(Func(fringe_mask, HEAD_C - 0.4, HEAD_C + 0.3), STUBBLE)
    # two frown lines between the brows and creases across the forehead
    for sx in (-1, 1):
        fd.sub(RoundCone(hp((sx * 0.011, -0.2, 1.739)), hp((sx * 0.015, -0.197, 1.762)), hr(0.0018), hr(0.0016)), hr(0.003))
    sk = skull()
    for zc in (1.81, 1.835):
        pts = []
        for k in range(9):
            x = -0.085 + 0.17 * k / 8
            h, ok = ray_hit(sk, [hp((x, -0.6, zc + 0.012 * (x / 0.085) ** 2))], [v3((0, 1, 0))], tmax=0.7)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 3:
            fd.sub(Chain(pts, [hr(0.0026)] * len(pts), k=0.002), hr(0.003))
    # bushy brows, the inner ends drawn down: a craftsman frowning at his work
    for sx in (-1, 1):
        pts = [hp((sx * 0.024, -0.216, 1.751)), hp((sx * 0.066, -0.209, 1.768)), hp((sx * 0.112, -0.186, 1.776)), hp((sx * 0.155, -0.145, 1.769))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.011), hr(0.013), hr(0.011), hr(0.005)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.022), hr(0.024), hr(0.021), hr(0.012)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.0135))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, -hr(0.019))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0105))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(2):                                                                      # crow's feet
            a = hp((sx * (0.112 + 0.004 * k), -0.13 + 0.006 * k, 1.672 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, -0.004 - 0.008 * k)), hr(0.0022), hr(0.0015)), hr(0.003))
    # a big hooked nose
    fd.add(RoundCone(hp((0, -0.186, 1.726)), hp((0, -0.252, 1.628)), hr(0.02), hr(0.028)), hr(0.018), SKIN)
    fd.add(S((0, -0.226, 1.686), 0.022), hr(0.012), SKIN)
    fd.add(S((0, -0.252, 1.618), 0.03), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.034, -0.222, 1.603), 0.022), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.017, -0.238, 1.592)), v3((0.009, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # mouth (mostly under the moustache): a pleased half-smile
    slot = [hp((-0.056, -0.17, 1.55)), hp((-0.03, -0.194, 1.542)), hp((0, -0.2, 1.542)), hp((0.032, -0.193, 1.546)), hp((0.06, -0.168, 1.558))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.046, -0.17, 1.541), (-0.025, -0.187, 1.531), (0, -0.191, 1.529), (0.026, -0.186, 1.535), (0.05, -0.168, 1.549)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.0085), hr(0.0095), hr(0.0085), hr(0.005)], k=hr(0.007)), hr(0.008), LIP)
    # big ears (nothing hides them)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.029, 0.052, 0.066)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.013, 0.033, 0.043)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))


# ======================================================================================= body (barrel-chested)
def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.17), (0.29, 0.24, 0.27), R=euler(-0.1, 0, 0)), 0.0),
        (Ellipsoid((0, 0.12, 1.22), (0.32, 0.17, 0.21)), 0.06),
        (Ellipsoid((0.13, -0.15, 1.24), (0.14, 0.06, 0.09), R=euler(0.1, 0, 0.18)), 0.045),
        (Ellipsoid((-0.13, -0.15, 1.24), (0.14, 0.06, 0.09), R=euler(0.1, 0, -0.18)), 0.045),
        (Ellipsoid((0, -0.045, 0.98), (0.245, 0.225, 0.21)), 0.08),                    # a solid belly
        (Ellipsoid((0, 0.045, 0.8), (0.25, 0.19, 0.16)), 0.08),
    ]


def traps():
    return Ellipsoid((0, 0.1, 1.39), (0.26, 0.14, 0.1), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.065, 1.34), hp((0, 0.02, 1.575)), 0.112, hr(0.092))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.024, -0.005, 0.014)), 0.118)


def upper_arm(side):
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    return RoundCone(sh, el, 0.105, 0.08)


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


def eyes_field():
    fd = Field("Eyes")
    for sx in (-1, 1):
        fd.add(Sphere(eye_c(sx), EYE_R))
    return fd


def teeth_field():
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009 + 0.003, -0.178, 1.547)), v3((0.008, 0.006, 0.007)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= beard, helmet
def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.052, 1.59), (0.15, 0.136, 0.128)), 0.07)
    fd.add(E((0, -0.132, 1.5), (0.09, 0.07, 0.068)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.116, -0.12, 1.628)), hr(0.055)), 0.05)
        fd.add(Sphere(hp((sx * 0.13, -0.045, 1.556)), hr(0.052)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


def beard_tex(P):
    """Wavy locks running down the beard; positive pushes the surface in."""
    x, z = P[:, 0], P[:, 2]
    ph = x / F(0.024) + F(0.35) * np.sin(z * F(40) + x * F(9))
    lock = np.abs(np.sin(ph * F(math.pi)))
    return F(0.0026) - F(0.0052) * lock * lock + F(0.0012) * NOISE(P * np.array([90, 90, 30], F))


def beard_field():
    """A short, full beard round his jaw and chin, squared under the chin, and a heavy moustache drooping past the
    corners of his mouth (the hill-fort way)."""
    fd = Field("Beard")
    hull = head_hull()
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.557) + F(0.085) * smoothstep(0.055, 0.14, ax)                       # chin and jaw, up the cheeks
        top = np.where(ax > F(0.152), F(1.7), top)                                      # sideburns to the cheek pieces
        lips = (x / F(0.066)) ** 2 + ((y + F(0.18)) / F(0.07)) ** 2 + ((z - F(1.545)) / F(0.026)) ** 2 - F(1.0)
        back = np.where(ax > F(0.14), y - F(0.035), y - F(0.0))
        return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), F(1.44) - z)
    fd.add(Inter(Shell(hull, 0.008, 0.022, pad=0.06, disp=beard_tex, disp_amp=0.007), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.008), 0.0)
    fd.add(Ellipsoid(hp((0, -0.15, 1.47)), v3((0.12, 0.068, 0.058)) * HS, disp=beard_tex, disp_amp=0.007), 0.04)   # fuller at the chin
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.224, 1.575)), hp((sx * 0.045, -0.212, 1.561)), hp((sx * 0.07, -0.192, 1.528)),
               hp((sx * 0.08, -0.176, 1.478))]
        fd.add(Lock(pts, [hr(0.015), hr(0.02), hr(0.016), hr(0.009)], [hr(0.011), hr(0.013), hr(0.01), hr(0.006)],
                    [norm(v3((sx * 0.3, -1, 0.15)))] * 4, k=hr(0.006), disp=strands, disp_amp=0.003), hr(0.006))
    return fd


# the helmet's rim runs round his head above the brows, lower at the back (design coordinates)
HELM_F = v3((0.0, -0.19, 1.79))
HELM_B = v3((0.0, 0.2, 1.665))
_HELM_N = norm(v3((0, -(HELM_B[2] - HELM_F[2]) / (HELM_B[1] - HELM_F[1]), 1.0)))
KNOB = hp((0.0, 0.03, 1.958))


def helm_d(P):
    """Height above the helmet's rim plane (design coordinates, + = up into the bowl)."""
    return (hinv(P) - HELM_F.astype(F)) @ _HELM_N.astype(F)


def bowl():
    """The helmet's bowl: the skull, raised into a low peak under the knob."""
    b = Field("Bowl")
    b.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    b.add(Ellipsoid(hp((0, 0.02, 1.79)), v3((0.165, 0.175, 0.12)) * HS), 0.08)
    b.add(Ellipsoid(hp((0, 0.03, 1.86)), v3((0.1, 0.11, 0.09)) * HS), 0.07)
    return b


def helmet_field():
    """An iron helmet (Montefortino-like): a peaked bowl with a raised rib round its base and a cast knob on its crown, a
    short flared neck guard behind, and two cheek pieces hinged at the rim, each with three bosses."""
    fd = Field("Helmet")
    bw = bowl()
    hammer = lambda P: F(0.0008) * NOISE(P * F(70))
    keep = Func(lambda P: -helm_d(P), HEAD_C - 0.45, HEAD_C + 0.45)
    fd.add(Inter(Shell(bw, 0.016, 0.014, pad=0.08, disp=hammer, disp_amp=0.0012), keep, 0.004), 0.0)
    # the rib round its base and a second one a little above
    for lift, w in ((0.012, 0.009), (0.05, 0.004)):
        ring = Func(lambda P, lift=lift, w=w: np.abs(helm_d(P) - F(lift)) - F(w), HEAD_C - 0.45, HEAD_C + 0.45)
        fd.add(Inter(Shell(bw, 0.028, 0.012, pad=0.08), ring, 0.003), 0.004)
    # the knob: a short neck and a flattened ball on the crown
    up = norm(KNOB - HEAD_C)
    fd.add(RoundCone(KNOB - up * 0.03, KNOB + up * 0.018, 0.022, 0.015), 0.008)
    fd.add(Ellipsoid(KNOB + up * 0.034, (0.026, 0.026, 0.019), R=rot_from_axes(z_axis=up)), 0.006)
    fd.add(Torus(KNOB - up * 0.008, 0.026, 0.006, R=rot_from_axes(z_axis=up)), 0.004)
    # the neck guard: a short flared brim behind, sloping out and down
    nb = Field("NeckBrim")
    nb.add(Ellipsoid(hp((0.0, 0.05, 1.67)), v3((0.21, 0.23, 0.07)) * HS), 0.0)
    brim = Inter(Shell(nb, 0.0, 0.012, pad=0.06), Func(lambda P: np.maximum(F(0.06) - hinv(P)[:, 1], np.abs(hinv(P)[:, 2] - F(1.66)) - F(0.03)),
                                                       HEAD_C - 0.45, HEAD_C + 0.45), 0.004)
    fd.add(brim, 0.008)
    # cheek pieces: shaped plates from the rim down over his cheeks, in front of the ears, three bosses on each
    hh = head_hull()
    for sx in (-1, 1):
        c = hp((sx * 0.15, -0.075, 1.66))
        def plate(P, sx=sx):
            Q = hinv(P)
            x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
            u = (y + F(0.075)) / F(0.07)
            v = (z - F(1.66)) / F(0.1)
            outline = u * u + v * v * (F(1.0) + F(0.35) * (v < 0)) - F(1.0)
            return np.maximum(outline * F(0.05), F(0.06) - x * F(sx))
        fd.add(Inter(Shell(hh, 0.024, 0.012, pad=0.08, disp=hammer, disp_amp=0.0012), Func(plate, c - 0.25, c + 0.25), 0.003), 0.0)
        for (yy, zz) in ((-0.07, 1.69), (-0.04, 1.64), (-0.085, 1.62)):
            q, ok = ray_hit(Func(lambda P: hh.eval(P, margin=0.05) - F(0.036), HEAD_C - 0.5, HEAD_C + 0.5),
                            [hp((sx * 0.5, yy, zz))], [v3((-sx, 0, 0))], tmax=0.6)
            if ok[0]:
                fd.add(Sphere(q[0], 0.0105), 0.004)
        hinge = hp((sx * 0.162, -0.05, 1.735))
        fd.add(RoundBox(hinge, (0.008, 0.018, 0.012), 0.004), 0.004)
    return fd


# ======================================================================================= tunic, trousers, leather, iron
def tunic_base():
    b = Field("TunicBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.055)
        b.add(upper_arm(side), 0.05)
    b.add(RoundCone((0, 0.03, 0.92), (0, 0.03, 0.55), 0.26, 0.31), 0.09)            # the skirt
    return b


def _neck_cut(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
    return z - (F(1.47) - F(0.06) * front * np.exp(-(x / F(0.15)) ** 2) + F(0.3) * smoothstep(0.17, 0.25, np.abs(x)))


def _sleeve(P, side):
    """< 0 on the body side of the sleeve's end (a plane across the upper arm, 45% of the way to the elbow)."""
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    n = norm(el - sh)
    c = sh + (el - sh) * 0.46
    d = (P - c.astype(F)) @ n.astype(F)
    sx = -1 if side == "R" else 1
    return np.where((P[:, 0] * F(sx) > F(0.34)) & (P[:, 2] > F(1.0)), d, F(-1.0))


def hem_z(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
    return F(0.6) + F(0.016) * np.clip(np.cos(a), 0, 1) + F(0.006) * NOISE(P * F(8))


def tunic_field():
    """A checked wool tunic to mid-thigh with short sleeves (the checks are in the material), a woven border (label 5)
    round the hem, the sleeves and the neck."""
    fd = Field("Tunic")
    base = tunic_base()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        k = smoothstep(0.95, 0.75, P[:, 2])
        return F(0.005) * np.sin(a * F(13) + F(0.7) * NOISE(P * F(3))) * k + F(0.0015) * NOISE(P * F(25))
    def keep(P):
        k = np.maximum(hem_z(P) - P[:, 2], _neck_cut(P))
        return np.maximum(np.maximum(k, _sleeve(P, "R")), _sleeve(P, "L"))
    fd.add(Inter(Shell(base, 0.024, 0.022, pad=0.1, disp=folds, disp_amp=0.006), Func(keep, (-1, -1, 0.4), (1, 1, 1.6)), 0.005), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (hem_z(P) + F(0.04)), (-1, -1, 0.4), (1, 1, 0.8)), 5)
    for side in ("R", "L"):
        def cuff(P, side=side):
            s = _sleeve(P, side)
            return np.where(s > F(-0.5), np.abs(s + F(0.022)) - F(0.022), F(1.0))
        fd.paint(Func(cuff, (-1, -1, 0.8), (1, 1, 1.6)), 5)
    fd.paint(Func(lambda P: np.abs(_neck_cut(P) + F(0.016)) - F(0.016), (-1, -1, 1.2), (1, 1, 1.6)), 5)
    return fd


def leg_prims(side):
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(hip, kn, 0.14, 0.092), 0.065),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.13, 0.12, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.048),
            (Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038),
            (RoundCone(kn, an, 0.088, 0.058), 0.038),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043)]


def legs_base():
    b = Field("LegsBase")
    b.add(torso_prims()[5][0], 0.0)
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            b.add(p, k)
    return b


def trousers_field():
    """Loose checked trousers from his waist (under the tunic) to his ankles, creased at the knees."""
    fd = Field("Trousers")
    base = legs_base()
    def shell(P):
        d = base.eval(P, margin=0.08)
        z = P[:, 2]
        creases = F(0.006) * NOISE(P * np.array([10, 10, 30], F)) + F(0.003) * NOISE(P * F(25))
        off = F(0.024) + creases + F(0.006) * np.clip((F(0.5) - z) / F(0.3), 0, 1)
        return np.abs(d - off) - F(0.008)
    an_z = float(J["ankle_R"][2])
    keep = lambda P: np.maximum(P[:, 2] - F(0.95), F(an_z + 0.05) - P[:, 2])
    lo, hi = (-0.5, -0.45, 0.0), (0.5, 0.45, 1.0)
    fd.add(Inter(Func(shell, lo, hi), Func(keep, lo, hi), 0.004), 0.0)
    return fd


BELT_Z = 0.975


def belt_base():
    b = Field("BeltBase")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    return b


def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.08, 0.058)


def shoe_hull(side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.12)
    fwd = Rz @ v3((0, -1, 0))
    f = Field("ShoeHull")
    f.add(Sphere(an + v3((0, 0.042, -0.05)), 0.066), 0.0)
    f.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.07)), (0.072, 0.13, 0.038), 0.035, R=Rz), 0.04)
    f.add(Ellipsoid(an + fwd * 0.17 + v3((0, 0, -0.074)), (0.066, 0.062, 0.038), R=Rz), 0.03)
    f.add(Cylinder(an + v3((0, 0.005, 0.02)), 0.07, 0.1, rr=0.03), 0.04)
    return f, fwd, Rz


def leg_axis_point(side, z):
    kn, an = J["knee_" + side], J["ankle_" + side]
    u = (kn[2] - z) / (kn[2] - an[2])
    return lerp(kn, an, u)


def leather_field():
    """A wide belt, wrist wraps, leather shoes and thongs criss-crossing up his shins over the trousers."""
    fd = Field("Leather")
    bb = belt_base()
    fd.add(Inter(Shell(bb, 0.056, 0.026, pad=0.1), Func(lambda P: np.abs(P[:, 2] - (F(BELT_Z) + F(0.03) * P[:, 1])) - F(0.042), (-1, -1, 0.8), (1, 1, 1.2)), 0.005), 0.0)
    for side in ("L", "R"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.82)
        fd.add(Inter(Shell(_forearm(side), 0.012, 0.016, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.05), c - 0.25, c + 0.25), 0.004), 0.0)
        for j in (-1, 0, 1):
            cc = c + ax * (j * 0.03)
            fd.add(Inter(Shell(_forearm(side), 0.02, 0.006, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.005), cc - 0.2, cc + 0.2), 0.002), 0.003)
    for side in ("R", "L"):
        an = J["ankle_" + side]
        sh, fwd, Rz = shoe_hull(side)
        top = an[2] + 0.075
        fd.add(Inter(Shell(sh, 0.0, 0.026, pad=0.06), Func(lambda P, top=top: P[:, 2] - F(top), an - 0.35, an + 0.35), 0.006), 0.0)
        fd.add(RoundBox(an + fwd * 0.085 + v3((0, 0, -0.1)), (0.08, 0.165, 0.012), 0.01, R=Rz), 0.008)          # sole
        fd.add(Torus(an + v3((0, 0.006, 0.072)), 0.072, 0.011), 0.004)                                           # turned top
        leg = Field("LegHull")
        for p, k in leg_prims(side):
            leg.add(p, k)
        z0, z1 = an[2] + 0.07, J["knee_" + side][2] - 0.07
        for hand_dir in (1, -1):
            pts = []
            for k in range(24):
                u = k / 23.0
                z = z0 + (z1 - z0) * u
                c = leg_axis_point(side, z)
                th = hand_dir * u * 2.0 * 2 * math.pi + (0.0 if hand_dir > 0 else math.pi)
                d = v3((math.cos(th), math.sin(th), 0.0))
                h, ok = ray_hit(Func(lambda P, leg=leg: leg.eval(P, margin=0.06) - F(0.034), an - 0.4, J["knee_" + side] + 0.4),
                                [c + d * 0.35], [-d], tmax=0.4)
                if ok[0]:
                    pts.append(h[0])
            if len(pts) > 4:
                fd.add(Chain(pts, [0.0068] * len(pts), k=0.003), 0.003)
    return fd


def belt_front():
    bb = belt_base()
    p, _ = ray_hit(Func(lambda P: bb.eval(P) - F(0.085), (-1, -1, 0.7), (1, 1, 1.3)), [v3((0, -0.8, BELT_Z - 0.03 * 0.25))], [v3((0, 1, 0))], tmax=0.9)
    return p[0]


def iron_field():
    """Iron armlets above the elbows (three rings each) and the belt's buckle: a rectangular frame with its pin."""
    fd = Field("Iron")
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        ua = Field("UA")
        ua.add(upper_arm(side), 0.0)
        ua.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.097, 0.1, 0.13), R=rot_from_axes(z_axis=el - sh)), 0.04)
        for j in range(3):
            c = lerp(sh, el, 0.66 + 0.055 * j)
            fd.add(Inter(Shell(ua, 0.012, 0.014, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.009), c - 0.2, c + 0.2), 0.003), 0.004)
    c = belt_front()
    frame = Func(lambda P: np.maximum(np.maximum(np.abs(P[:, 0] - F(c[0])) - F(0.06), np.abs(P[:, 2] - F(c[2])) - F(0.046)),
                                      -np.maximum(np.abs(P[:, 0] - F(c[0])) - F(0.04), np.abs(P[:, 2] - F(c[2])) - F(0.028))),
                 c - 0.1, c + 0.1)
    fd.add(Inter(frame, Func(lambda P: np.abs(P[:, 1] - F(c[1] - 0.006)) - F(0.008), c - 0.1, c + 0.1), 0.002), 0.0)
    fd.add(RoundCone(c + v3((-0.04, -0.016, 0.0)), c + v3((0.046, -0.016, 0.004)), 0.006, 0.005), 0.003)
    return fd


# ======================================================================================= the mallet (rigid in his right fist)
MALLET_L = 0.36            # grip -> the head's centre
MALLET_BUTT = 0.07         # grip -> the end of the handle (below the fist)
MALLET_HEAD = (0.056, 0.09)  # the head's radius, half length


def mallet_frame():
    """Rest pose: grip G at the right fist's centre, the handle along the thumb axis T, the head's faces along F."""
    wr, f, n, t = hand_frame("R")
    G = fist_center("R")
    T = norm(t)
    Fv = norm(f - T * (f @ T))
    return G, T, Fv


def mallet_field():
    """Hard wood (label 0), two iron bands round the head and an iron collar (6), a leather-bound grip (5)."""
    fd = Field("Mallet")
    G, T, Fv = mallet_frame()
    grain = lambda P: F(0.0015) * NOISE(P * F(70))
    fd.add(RoundCone(G - T * MALLET_BUTT, G + T * (MALLET_L - 0.04), 0.019, 0.016, disp=grain, disp_amp=0.002), 0.0)
    fd.add(Sphere(G - T * MALLET_BUTT, 0.022), 0.006)
    hc = G + T * MALLET_L
    r, hl = MALLET_HEAD
    fd.add(Cylinder(hc, r, hl * 2, rr=0.012, R=rot_from_axes(z_axis=Fv), disp=grain, disp_amp=0.002), 0.008)
    for s in (-1, 1):
        fd.add(Cylinder(hc + Fv * s * (hl - 0.022), r + 0.004, 0.018, rr=0.004, R=rot_from_axes(z_axis=Fv)), 0.002, 6)
    fd.add(Cylinder(hc - T * (r + 0.004), 0.025, 0.02, rr=0.005, R=rot_from_axes(z_axis=T)), 0.006, 6)
    for k in range(6):
        c = G + T * (-0.05 + 0.02 * k)
        fd.add(Torus(c, 0.019, 0.0045, R=rot_from_axes(z_axis=T)), 0.002, 5)
    return fd


# ======================================================================================= the ballista (layout)
MX = 0.8                      # the stock's centre line (x); it shoots toward -Y
SW, SH = 0.064, 0.052         # the stock's half width and half height
STOCK_Z = 0.98                # the stock's top surface
SZ = STOCK_Z - SH             # its centre (z)
YF, YB = -1.12, 0.26          # its front and back ends (the windlass cheeks carry on behind it)
SLW, SLH = 0.048, 0.026       # the slider's half width and half height (riding on the stock)
SL_TOP = STOCK_Z + 2 * SLH    # the slider's top (the bolt lies in a groove along it)
SL_LEN = 0.86
YH = -0.8                     # the spring frame's centre (y)
FHW, FHD = 0.36, 0.085        # the frame's half width (x) and half depth (y)
F_TOP, F_BOT = STOCK_Z + 0.21, STOCK_Z - 0.25   # the top of its top plate, the bottom of its bottom plate
PLATE_T = 0.035
SKX = 0.2                     # the skeins' offset from MX
SKEIN_R = 0.05
ARM_L = 0.46                  # skein -> arm tip
COCKED = math.radians(40.0)   # the arms' sweep back from straight out to the sides, drawn
LOOSE = math.radians(12.0)    # ... loosed (against the outer uprights)
ARM_Z = SL_TOP + 0.012        # the arms' and the string's height (just over the slider)
STR_HALF = SKX + ARM_L * math.cos(LOOSE)        # half the string (straight between the tips when loosed)
YT = -0.4                     # the trunnion (and the post) under the stock
POST_TOP = SZ - SH - 0.08     # the swivel block's top
LEG_R = 0.38                  # the feet's distance from the post (along x and y)
DRUM = v3((MX, 0.33, SZ + 0.01))                # the windlass drum (its axis along X)
DRUM_R = 0.052
CHEEK_X = SW + 0.022          # the windlass cheeks' offset from MX
NEAR = MX - CHEEK_X - 0.02    # the near cheek's outer face (his side, -X)
CRANK_X = NEAR - 0.1          # the crank's plane
CRANK_R = 0.13
CRANK_PHI = math.radians(70.0)          # the crank's angle in the rest pose (0 = toward the back, + = up)
HANDLE_L = 0.12
BOLT_L = 0.84
BOLT_R = 0.016
PILE = v3((0.12, 0.47, 0.0))            # the bundle of spare bolts behind him
RESTS_Z = 0.07                          # the top of the two log rests under them
YAW_PIVOT = (0.4, -0.38, 0.0)           # the tower turns about this point (keeps the whole ballista on the base)


def arm_dir(side, th):
    """An arm's direction from its skein (side -1 = the near arm, at -X; +1 = the far one): out to its side, swept back
    (toward +Y) by th."""
    return v3((side * math.cos(th), math.sin(th), 0.0))


def skein_c(side):
    return v3((MX + side * SKX, YH, ARM_Z))


def arm_tip(side, th):
    return skein_c(side) + arm_dir(side, th) * ARM_L


def claw_y(th):
    """Where the middle of the string is (y) with the arms at th (it doesn't stretch)."""
    tx = SKX + ARM_L * math.cos(th)
    ty = YH + ARM_L * math.sin(th)
    return ty + math.sqrt(max(STR_HALF ** 2 - tx ** 2, 0.0))


def arm_for_claw(y):
    """The arms' sweep at which the middle of the string is at y (claw_y grows with th: bisection)."""
    lo, hi = LOOSE, math.radians(75.0)
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if claw_y(m) < y:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


CLAW_COCK = claw_y(COCKED)              # the claw (holding the string) drawn back
CLAW_LOOSE = claw_y(LOOSE)              # ... pushed forward to the loosed string
CLAW_BACK = 0.06                        # the claw -> the slider's back end (the claw block between)


def claw_pt(y=CLAW_COCK):
    return v3((MX, y, ARM_Z))


def slider_back(y=CLAW_COCK):
    return y + CLAW_BACK


TRIG_P = v3((MX, CLAW_COCK + 0.03, SL_TOP + 0.034))     # the claw's pivot pin (axis X) on the claw block


def bolt_nock(y=CLAW_COCK):
    return v3((MX, y - 0.012, SL_TOP + 0.009))


def bolt_point():
    return bolt_nock() + v3((0, -BOLT_L, 0))


def haul_start():
    """Where the rope leaves the drum (its top, toward the slider)."""
    return DRUM + v3((0, -0.012, DRUM_R + 0.004))


def haul_end(y=CLAW_COCK):
    """Where the rope is tied to the back of the claw block."""
    return v3((MX, slider_back(y) + 0.008, STOCK_Z + SLH))


def crank_handle(phi):
    """The crank handle's inner and outer ends at crank angle phi (0 = toward the back, + = up)."""
    c = v3((CRANK_X, DRUM[1] + CRANK_R * math.cos(phi), DRUM[2] + CRANK_R * math.sin(phi)))
    return c, c - v3((HANDLE_L, 0, 0))


def pile_bolts():
    """(nock, direction, bone) of the spare bolts: four side by side on the rests, one on top (the one he lifts)."""
    d = v3((1.0, 0.0, 0.0))
    z = RESTS_Z + BOLT_R + 0.002
    out = []
    for k, oy in enumerate((-0.057, -0.019, 0.019, 0.057)):
        out.append((PILE + v3((-BOLT_L * 0.5, oy, z)), d, "props"))
    zt = z + math.sqrt((2 * BOLT_R) ** 2 - 0.019 ** 2) + 0.006
    out.append((PILE + v3((-BOLT_L * 0.5, 0.0, zt)), d, "carry"))
    return out


CARRY_C = pile_bolts()[4][0] + v3((BOLT_L * 0.5, 0, 0))          # the middle of the bolt he lifts


# ======================================================================================= the ballista (sculpt)
def tbeam(a, b, up, w0, d0, w1=None, d1=None, r=0.012, disp=None, disp_amp=0.0):
    """A tapered beam with rounded edges from a to b; half width w (across), half depth d (along `up`)."""
    w1 = w0 if w1 is None else w1
    d1 = d0 if d1 is None else d1
    a, b = v3(a), v3(b)
    L = float(np.linalg.norm(b - a))
    ax = (b - a) / L
    upv = norm(v3(up) - ax * (v3(up) @ ax))
    side = np.cross(ax, upv)
    A, AX, UP, SD = a.astype(F), ax.astype(F), upv.astype(F), side.astype(F)
    def fn(P):
        q = P - A
        u = q @ AX
        t = np.clip(u / F(L), 0, 1)
        hw = F(w0) + (F(w1) - F(w0)) * t - F(r)
        hd = F(d0) + (F(d1) - F(d0)) * t - F(r)
        qx = np.abs(q @ SD) - hw
        qy = np.abs(q @ UP) - hd
        qz = np.abs(u - F(L / 2)) - F(L / 2 - r)
        out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
        return out + np.minimum(np.maximum(np.maximum(qx, qy), qz), 0) - F(r)
    pad = max(w0, d0, w1, d1) + 0.03
    return Func(fn, np.minimum(a, b) - pad, np.maximum(a, b) + pad, disp=disp, disp_amp=disp_amp)


GRAIN = lambda P: F(0.0016) * NOISE(P * F(55)) + F(0.0008) * NOISE(P * F(140))


def box(c, half, r=0.012, R=None):
    return RoundBox(v3(c), half, r, R=R, disp=GRAIN, disp_amp=0.002)


def strap(fd, c, half, axis, w=0.012, extra=0.006):
    """An iron strap round a timber of half extents `half` at c, `w` wide along `axis` (0 = x, 1 = y, 2 = z)."""
    hb = v3(half) + extra
    hb[axis] = w
    fd.add(RoundBox(v3(c), hb, 0.004), 0.003, IRON)


def frame_field():
    """The stand (post, four splayed legs with feet and braces, the swivel and the fork with its pin), the stock with its
    iron shoe and straps, the spring frame (plates, uprights, straps), the skeins with their washers and levers, and the
    windlass cheeks."""
    fd = Field("Frame")
    # ---- the stand
    base_z = 0.0
    fd.add(box((MX, YT, POST_TOP / 2), (0.062, 0.062, POST_TOP / 2)), 0.0, GZ)
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            top = v3((MX + s1 * 0.05, YT + s2 * 0.05, 0.46))
            foot = v3((MX + s1 * LEG_R, YT + s2 * LEG_R, base_z + 0.035))
            fd.add(tbeam(top, foot, (s1 * -0.7, s2 * -0.7, 0.7), 0.036, 0.036, 0.04, 0.04, disp=GRAIN, disp_amp=0.002), 0.012, GZ)
            fd.add(box(foot + v3((0, 0, -0.012)), (0.07, 0.07, 0.024), r=0.014), 0.008, GX)          # its foot block
            mid = lerp(top, foot, 0.62)
            fd.add(tbeam(mid, v3((MX + s1 * 0.055, YT + s2 * 0.055, 0.68)), (s1, s2, 0.0), 0.022, 0.022, disp=GRAIN, disp_amp=0.0015), 0.008, GZ)
            fd.add(Sphere(lerp(top, foot, 0.08), 0.014), 0.003, IRON)
    for zz in (0.12, 0.44, POST_TOP - 0.05):
        strap(fd, (MX, YT, zz), (0.062, 0.062, 0.06), 2)
    # the swivel block, the fork cheeks round the stock and the trunnion pin through them
    fd.add(Cylinder(v3((MX, YT, POST_TOP + 0.025)), 0.085, 0.05, rr=0.01, disp=GRAIN, disp_amp=0.002), 0.006, GZ)
    fd.add(Cylinder(v3((MX, YT, POST_TOP + 0.003)), 0.09, 0.014, rr=0.004), 0.002, IRON)
    for sx in (-1, 1):
        cx = MX + sx * (SW + 0.026)
        fd.add(box((cx, YT, (POST_TOP + 0.05 + SZ + 0.045) / 2), (0.022, 0.06, (SZ + 0.045 - POST_TOP - 0.05) / 2)), 0.006, GZ)
        fd.add(Cylinder(v3((cx + sx * 0.026, YT, SZ)), 0.024, 0.016, rr=0.004, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, IRON)
    fd.add(Cylinder(v3((MX, YT, SZ)), 0.012, 2 * (SW + 0.06), rr=0.003, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, IRON)
    # ---- the stock: a heavy beam, its front shod with iron, straps along it; a dovetail rail on its top
    fd.add(box((MX, (YF + YB) / 2, SZ), (SW, (YB - YF) / 2, SH)), 0.0, 0)
    fd.add(Inter(RoundBox(v3((MX, YF + 0.04, SZ)), (SW + 0.007, 0.05, SH + 0.007), 0.01),
                 Plane(v3((MX, YF + 0.09, SZ)), (0, 1, 0)), 0.002), 0.003, IRON)
    for yy in (YF + 0.2, YT - 0.16, YT + 0.16, YB - 0.06):
        strap(fd, (MX, yy, SZ), (SW, 0.0, SH), 1, w=0.014)
    for sx in (-1, 1):                                                        # the rail lips the slider runs between
        fd.add(box((MX + sx * (SLW + 0.012), (YF + 0.12 + YB) / 2, STOCK_Z + 0.012), (0.01, (YB - YF - 0.12) / 2, 0.012), r=0.004), 0.004, 0)
    # paint: a red band along each side of the stock, blue toward its ends
    for sx in (-1, 1):
        x = MX + sx * SW
        def side_band(P, x=x, sx=sx):
            return np.maximum(np.maximum(np.abs(P[:, 2] - F(SZ)) - F(0.022), (F(x) - P[:, 0]) * F(sx) + F(0.02)),
                              np.abs(P[:, 1] - F((YF + YB) / 2)) - F((YB - YF) / 2 - 0.12))
        fd.paint(Func(side_band, (x - 0.1, YF, SZ - 0.1), (x + 0.1, YB, SZ + 0.1)), RED)
    # ---- the spring frame
    for zc, lab in ((F_TOP - PLATE_T / 2, GX), (F_BOT + PLATE_T / 2, GX)):
        fd.add(box((MX, YH, zc), (FHW, FHD, PLATE_T / 2)), 0.006, lab)
        fd.paint(Func(lambda P, zc=zc: np.maximum(np.abs(P[:, 2] - F(zc)) - F(PLATE_T / 2 + 0.01), np.abs(P[:, 0] - F(MX)) - F(0.06)),
                      (MX - 0.5, YH - 0.2, zc - 0.1), (MX + 0.5, YH + 0.2, zc + 0.1)), BLUE)
        for sx in (-1, 1):                                                    # iron corner plates
            fd.add(RoundBox(v3((MX + sx * (FHW - 0.03), YH, zc)), (0.034, FHD + 0.006, PLATE_T / 2 + 0.006), 0.005), 0.003, IRON)
    for xo in (0.1, 0.33):                                                    # the uprights
        for sx in (-1, 1):
            fd.add(box((MX + sx * xo, YH, (F_TOP + F_BOT) / 2), (0.03, 0.034, (F_TOP - F_BOT) / 2 - PLATE_T + 0.01)), 0.008, GZ)
    fd.add(box((MX, YH, (F_BOT + PLATE_T + STOCK_Z - 2 * SH) / 2), (SW, FHD - 0.01, (STOCK_Z - 2 * SH - F_BOT - PLATE_T) / 2 + 0.01)), 0.008, GZ)
    # the skeins: thick bundles of twisted rope between the plates, under big iron washers with their levers
    for sx in (-1, 1):
        sc = skein_c(sx)
        def skein(P, sc=sc):
            q = P - sc.astype(F)
            rr = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
            a = np.arctan2(q[:, 1], q[:, 0])
            tw = F(0.005) * np.sin(a * F(9) + q[:, 2] * F(60))
            bulge = F(0.012) * np.exp(-((q[:, 2]) / F(0.09)) ** 2)
            z0, z1 = F(F_BOT + PLATE_T - sc[2]), F(F_TOP - PLATE_T - sc[2])
            return np.maximum(rr - (F(SKEIN_R) + bulge) + tw, np.maximum(z0 - q[:, 2], q[:, 2] - z1) - F(0.01))
        fd.add(Func(skein, sc - v3((0.2, 0.2, 0.5)), sc + v3((0.2, 0.2, 0.5)), disp=lambda P: F(0.0012) * NOISE(P * F(160)), disp_amp=0.002), 0.004, ROPE)
        for zw, sg in ((F_TOP + 0.012, 1), (F_BOT - 0.012, -1)):
            wc = v3((sc[0], sc[1], zw))
            fd.add(Cylinder(wc, 0.078, 0.026, rr=0.006), 0.003, IRON)
            fd.add(Torus(wc + v3((0, 0, sg * 0.014)), 0.05, 0.012), 0.003, IRON)
            for k in range(12):                                              # notches round the washer's rim
                a = 2 * math.pi * k / 12
                d = v3((math.cos(a), math.sin(a), 0))
                fd.add(RoundBox(wc + d * 0.08, (0.012, 0.01, 0.014), 0.003, R=rot_from_axes(x_axis=d)), 0.002, IRON)
            lev = norm(v3((0.55, -0.83, 0.0)) * v3((sx, 1, 1)))
            lc = wc + v3((0, 0, sg * 0.03))
            fd.add(RoundCone(lc - lev * 0.11, lc + lev * 0.12, 0.016, 0.014, disp=GRAIN, disp_amp=0.002), 0.004, GZ)
            fd.add(Sphere(lc + lev * 0.12, 0.018), 0.003, IRON)
            fd.add(Ellipsoid(lc, (0.03, 0.03, 0.022), disp=lambda P: F(0.003) * np.sin(P[:, 0] * F(260) + P[:, 1] * F(260)), disp_amp=0.004), 0.008, ROPE)
    # ---- the windlass cheeks behind the stock (the drum turns between them)
    for sx in (-1, 1):
        cx = MX + sx * CHEEK_X
        fd.add(box((cx, (YB - 0.04 + DRUM[1] + 0.09) / 2, SZ), (0.022, (DRUM[1] + 0.09 - YB + 0.04) / 2, SH + 0.012)), 0.006, 0)
        fd.add(Cylinder(v3((cx + sx * 0.022, DRUM[1], DRUM[2])), 0.034, 0.012, rr=0.003, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, IRON)
    fd.add(box((MX, DRUM[1] + 0.075, SZ - 0.03), (CHEEK_X + 0.012, 0.022, 0.03)), 0.006, GX)
    return fd


def arms_field():
    """The two bow arms (drawn back): tapered ash, rope-bound where they leave the skeins, iron caps on their tips with a
    notch for the string."""
    fd = Field("Arms")
    for sx in (-1, 1):
        d = arm_dir(sx, COCKED)
        a0 = skein_c(sx) - d * 0.03
        a1 = skein_c(sx) + d * (ARM_L - 0.02)
        up = v3((0, 0, 1))
        fd.add(tbeam(a0, a1, up, 0.03, 0.034, 0.022, 0.024, r=0.012, disp=GRAIN, disp_amp=0.0018), 0.0, 0)
        fd.add(Inter(tbeam(a0, a1, up, 0.038, 0.042, 0.03, 0.032, r=0.012, disp=lambda P: F(0.002) * np.sin(P[:, 0] * F(330) + P[:, 1] * F(330)), disp_amp=0.003),
                     Func(lambda P, c=skein_c(sx) + d * 0.1, d=d: np.abs((P - c.astype(F)) @ d.astype(F)) - F(0.035), a0 - 0.2, a1 + 0.2), 0.002), 0.003, ROPE)
        tip = arm_tip(sx, COCKED)
        fd.add(Inter(tbeam(skein_c(sx) + d * (ARM_L - 0.09), tip + d * 0.012, up, 0.028, 0.03, 0.026, 0.028, r=0.01),
                     Plane(skein_c(sx) + d * (ARM_L - 0.085), -d), 0.002), 0.004, IRON)
        fd.add(Sphere(tip + d * 0.01, 0.026), 0.006, IRON)
        fd.sub(Torus(tip, 0.024, 0.006, R=rot_from_axes(z_axis=(0, 0, 1))), 0.002)            # the string's notch
    return fd


def strings_field():
    """The bowstring (twisted sinew), drawn back: from each arm's tip to the claw (each half is stretched in game)."""
    fd = Field("Strings")
    c = claw_pt()
    for sx in (-1, 1):
        a = arm_tip(sx, COCKED)
        tw = lambda P, a=a: F(0.0012) * np.sin(((P - a.astype(F)) @ norm(c - a).astype(F)) * F(500) + P[:, 2] * F(300))
        fd.add(RoundCone(a + norm(c - a) * 0.004, c + norm(a - c) * 0.006, 0.0085, 0.0085, disp=tw, disp_amp=0.0015), 0.0)
        fd.add(Torus(a, 0.016, 0.0075, R=rot_from_axes(z_axis=(0, 0, 1))), 0.003)              # looped round the tip
    return fd


def slider_field():
    """The slider: a beam riding in the stock's dovetail, the bolt groove along its top; the claw block at its back end,
    ironed, with the cheeks the claw's pin runs through and the ring the windlass rope is tied to."""
    fd = Field("Slider")
    yb = slider_back()
    yf = yb - SL_LEN
    zc = STOCK_Z + SLH
    fd.add(box((MX, (yb + yf) / 2, zc), (SLW, SL_LEN / 2, SLH), r=0.008), 0.0, 0)
    fd.sub(RoundCone(v3((MX, yf - 0.05, SL_TOP + 0.006)), v3((MX, yb - 0.07, SL_TOP + 0.006)), 0.017, 0.017), 0.004)   # the groove
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 0] - F(MX)) - F(SLW + 0.01), np.abs(P[:, 2] - F(zc)) - F(0.012)), (MX - 0.2, yf, zc - 0.1), (MX + 0.2, yb, zc + 0.1)), RED)
    # the claw block
    cb = v3((MX, yb - 0.024, SL_TOP + 0.022))
    fd.add(box(cb, (SLW + 0.004, 0.024, 0.026), r=0.008), 0.006, GX)
    for sx in (-1, 1):
        fd.add(RoundBox(v3((MX + sx * 0.03, TRIG_P[1], TRIG_P[2])), (0.008, 0.028, 0.03), 0.004), 0.003, IRON)
    fd.add(RoundBox(v3((MX, yb - 0.006, cb[2])), (SLW + 0.01, 0.007, 0.03), 0.004), 0.003, IRON)
    fd.add(Torus(haul_end(), 0.016, 0.005, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, IRON)
    return fd


def trigger_field():
    """The claw: an iron hook on its pin curling forward over the string, and its lever sticking up behind it (he knocks
    it with the mallet)."""
    fd = Field("Trigger")
    p = TRIG_P
    c = claw_pt()
    hook = [p, p + v3((0, -0.012, 0.018)), c + v3((0, -0.006, 0.02)), c + v3((0, -0.016, 0.004)), c + v3((0, -0.014, -0.008))]
    fd.add(Chain(hook, [0.013, 0.012, 0.011, 0.009, 0.007], k=0.004), 0.0, IRON)
    tail = p + v3((0, 0.11, 0.075))
    fd.add(RoundCone(p, tail, 0.012, 0.01), 0.004, IRON)
    fd.add(Sphere(tail, 0.017), 0.003, IRON)
    fd.add(Cylinder(p, 0.011, 2 * 0.036, rr=0.003, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, IRON)
    return fd


def winch_field():
    """The windlass: the drum with rope on it, iron rims, the ratchet wheel and the crank on his side (it turns with the
    'winch' bone)."""
    fd = Field("Winch")
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    L = 2 * (CHEEK_X - 0.024)
    fd.add(Cylinder(DRUM, DRUM_R, L, rr=0.008, R=Rx, disp=GRAIN, disp_amp=0.002), 0.0, GX)
    for sx in (-1, 1):
        fd.add(Torus(DRUM + v3((sx * (L / 2 - 0.01), 0, 0)), DRUM_R + 0.004, 0.009, R=Rx), 0.003, IRON)
    for k in range(4):
        fd.add(Torus(DRUM + v3((-0.03 + 0.02 * k, 0, 0)), DRUM_R + 0.005, 0.0085, R=Rx), 0.002, ROPE)
    ax0, ax1 = v3((MX + CHEEK_X + 0.05, DRUM[1], DRUM[2])), v3((CRANK_X - 0.012, DRUM[1], DRUM[2]))
    fd.add(Cylinder((ax0 + ax1) / 2, 0.02, float(np.linalg.norm(ax1 - ax0)), rr=0.005, R=Rx), 0.004, IRON)
    rc = v3((NEAR - 0.035, DRUM[1], DRUM[2]))                                     # the ratchet wheel
    fd.add(Cylinder(rc, 0.062, 0.02, rr=0.004, R=Rx), 0.003, IRON)
    for k in range(10):
        a = 2 * math.pi * k / 10
        dd = v3((0, math.cos(a), math.sin(a)))
        tng = v3((0, -math.sin(a), math.cos(a)))
        fd.add(RoundBox(rc + dd * 0.066 + tng * 0.006, (0.01, 0.011, 0.013), 0.003, R=rot_from_axes(y_axis=dd, z_axis=(1, 0, 0))), 0.002, IRON)
    h0, h1 = crank_handle(CRANK_PHI)
    fd.add(tbeam(v3((CRANK_X, DRUM[1], DRUM[2])), h0, (1, 0, 0), 0.024, 0.011, 0.019, 0.01, r=0.005), 0.004, IRON)
    fd.add(Sphere(v3((CRANK_X, DRUM[1], DRUM[2])), 0.028), 0.004, IRON)
    fd.add(RoundCone(h0 + v3((0.012, 0, 0)), h1, 0.021, 0.019, disp=GRAIN, disp_amp=0.0015), 0.004, GX)
    fd.add(Sphere(h1 - v3((0.012, 0, 0)), 0.026), 0.004, IRON)
    return fd


def haul_field():
    """The windlass rope, drawn: from the drum to the ring on the claw block (stretched in game)."""
    fd = Field("Haul")
    a, b = haul_start(), haul_end()
    tw = lambda P: F(0.0014) * np.sin(((P - a.astype(F)) @ norm(b - a).astype(F)) * F(420) + P[:, 0] * F(300))
    fd.add(RoundCone(a, b + norm(a - b) * 0.012, 0.009, 0.009, disp=tw, disp_amp=0.002), 0.0)
    return fd


def bolt_prims(fd, nock, d, side=None, seed=0):
    """A bolt from its nock along d: an ash shaft, three leather flights near the nock (label 5), a long four-sided
    iron head on a socket (6)."""
    d = norm(v3(d))
    up = v3((0, 0, 1)) if abs(d[2]) < 0.9 else v3((1, 0, 0))
    s1 = norm(np.cross(d, up))
    s2 = np.cross(s1, d)
    tip = nock + d * BOLT_L
    fd.add(RoundCone(nock + d * 0.008, tip - d * 0.12, BOLT_R * 0.92, BOLT_R, disp=GRAIN, disp_amp=0.0012), 0.0, 0)
    fd.add(Sphere(nock + d * 0.01, BOLT_R * 0.95), 0.004, 0)
    fd.add(RoundCone(tip - d * 0.15, tip - d * 0.1, BOLT_R * 1.25, BOLT_R * 1.15), 0.003, IRON)
    D, S1, S2, T = d.astype(F), s1.astype(F), s2.astype(F), tip.astype(F)
    def head(P):
        q = P - T
        u = -(q @ D)                                                   # back from the point
        hw = F(BOLT_R * 1.15) * np.clip(u / F(0.1), 0, 1)
        side_d = np.maximum(np.abs(q @ S1), np.abs(q @ S2)) - hw
        return np.maximum(np.maximum(side_d * F(0.8), -u), u - F(0.1))
    fd.add(Func(head, tip - 0.15, tip + 0.15), 0.004, IRON)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        rad = s1 * math.cos(a) + s2 * math.sin(a)
        fd.add(RoundBox(nock + d * 0.1 + rad * (BOLT_R + 0.014), (0.0025, 0.016, 0.07), 0.0022, R=rot_from_axes(z_axis=d, y_axis=rad)), 0.003, 5)


def bolt_field():
    """The bolt in the groove."""
    fd = Field("Bolt")
    bolt_prims(fd, bolt_nock(), v3((0, -1, 0)))
    return fd


def spares_field():
    """The bundle of spare bolts on their rests, under the one he lifts."""
    fd = Field("Spares")
    for nock, d, bone in pile_bolts():
        if bone == "props":
            bolt_prims(fd, nock, d)
    return fd


def carry_field():
    """The top bolt of the bundle (the one he lifts and lays in the groove)."""
    fd = Field("Carry")
    for nock, d, bone in pile_bolts():
        if bone == "carry":
            bolt_prims(fd, nock, d)
    return fd


def rests_field():
    """Two short logs on the ground under the bundle of bolts."""
    fd = Field("Rests")
    bark = lambda P: F(0.003) * NOISE(P * F(40)) + F(0.0015) * np.sin(np.arctan2(P[:, 2] - F(0.035), P[:, 0]) * F(14))
    for xo in (-0.26, 0.26):
        c = PILE + v3((xo, 0.0, 0.035))
        fd.add(Cylinder(c, 0.035, 0.24, rr=0.012, R=rot_from_axes(z_axis=(0, 1, 0)), disp=bark, disp_amp=0.004), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.255, 1.616)), 0.055, 0.6)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.11, -0.14, 1.62)), 0.06, 0.45), (hp((sx * 0.18, 0.035, 1.664)), 0.055, 0.55),
                (J["elbow_" + sd] + v3((0, 0.025, 0)), 0.065, 0.3), (J["knee_" + sd] + v3((0, -0.03, 0)), 0.075, 0.35),
                (J["shoulder_" + sd] + v3((0, 0, 0.1)), 0.12, 0.25), (hp((sx * 0.05, -0.15, 1.83)), 0.08, 0.25)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.044, 0.0148, -0.0148, -0.044):
            pts.append((wr + f * 0.14 + t * o - n * 0.012, 0.032, 0.45))
        an = J["ankle_" + side]
        pts.append((an + v3((0, -0.17, -0.07)), 0.065, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "ballista"
ROOT_NAME = "BallistaHQ"
TEX_PREFIX = "ballista"
MAT_NAME = "BallistaMat"
MESH_NAME = "Ballista"
BASE_MODULE = "ballista_base"
ANIM_MODULE = "anim_ballista"
PARTS = ["Skin", "Eyes", "Teeth", "Beard", "Helmet", "Tunic", "Trousers", "Leather", "Iron", "Mallet", "Frame", "Arms",
         "Strings", "Slider", "Trigger", "Winch", "Haul", "Bolt", "Spares", "Carry", "Rests"]
REGION_PARTS = ("Skin", "Tunic", "Mallet", "Frame", "Arms", "Slider", "Winch", "Bolt", "Spares", "Carry")
SIEGE = ("siege", {"name": "HQ_BalSiege", "wood": (0.56, 0.38, 0.22), "wood2": (0.4, 0.26, 0.14), "red": (0.66, 0.14, 0.08),
                   "blue": (0.16, 0.28, 0.55), "metal": "iron"})
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_BalSkin", "base": (0.8, 0.56, 0.42), "ruddy": (0.84, 0.46, 0.36), "lips": (0.64, 0.36, 0.3),
                      "brow": ((0.05, 0.04, 0.035), (0.12, 0.09, 0.07)),
                      "extra": ((LASH, (0.05, 0.035, 0.03), 0.5), (STUBBLE, (0.3, 0.22, 0.18), 0.6, 0.5))}),
    "Beard": ("hair", {"name": "HQ_BalBeard", "base": (0.07, 0.055, 0.05), "hi": (0.3, 0.24, 0.21), "low": (0.03, 0.025, 0.022),
                       "streak": (0.045, 0.035, 0.03), "tint": (0.15, 0.1, 0.08)}),
    "Helmet": ("iron", {"name": "HQ_BalHelmet"}),
    "Tunic": ("plaid", {"name": "HQ_BalTunic", "base": (0.14, 0.24, 0.48), "stripe": (0.5, 0.12, 0.08), "line": (0.86, 0.68, 0.24),
                        "border": (0.62, 0.14, 0.08)}),
    "Trousers": ("plaid", {"name": "HQ_BalTrousers", "base": (0.27, 0.21, 0.12), "stripe": (0.4, 0.13, 0.07),
                           "line": (0.72, 0.6, 0.3), "border": (0.4, 0.13, 0.07), "period": 0.1}),
    "Leather": ("leather", {"name": "HQ_BalLeather", "base": (0.34, 0.19, 0.1)}),
    "Iron": ("iron", {"name": "HQ_BalIron"}),
    "Mallet": ("javelin_shaft", {"name": "HQ_BalMallet"}),
    "Frame": SIEGE, "Arms": SIEGE, "Slider": SIEGE, "Winch": SIEGE,
    "Trigger": ("iron", {"name": "HQ_BalIron"}),
    "Strings": ("cord", {}), "Haul": ("cord", {}),
    "Bolt": ("javelin_shaft", {"name": "HQ_BalBolts"}), "Spares": ("javelin_shaft", {"name": "HQ_BalBolts"}),
    "Carry": ("javelin_shaft", {"name": "HQ_BalBolts"}),
    "Rests": ("bark_wood", {"name": "HQ_BalRests"}),
}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Beard": 1200, "Helmet": 1300, "Tunic": 1900, "Trousers": 1500, "Leather": 1600,
               "Iron": 600, "Mallet": 380, "Frame": 6200, "Arms": 900, "Strings": 160, "Slider": 700, "Trigger": 220,
               "Winch": 800, "Haul": 80, "Bolt": 320, "Spares": 900, "Carry": 220, "Rests": 220}
AO_EXCLUDE = ["Arms", "Strings", "Slider", "Trigger", "Winch", "Haul", "Bolt", "Carry", "Mallet"]
# the ballista and its props are baked 6 m away from him: his rest pose (his left hand hangs by the stock) must leave no
# shadow on it, nor it on him
BAKE_APART = (["Frame", "Arms", "Strings", "Slider", "Trigger", "Winch", "Haul", "Bolt", "Spares", "Carry", "Rests"], (6.0, 0.0, 0.0))
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.72, 0.88, 1.05, 1.43)


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.9), (0, 0.045, 1.11)),
        "chest": ((0, 0.045, 1.11), (0, 0.065, 1.36)),
        "neck": ((0, 0.065, 1.36), hp((0, 0.02, 1.56))),
        "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.36,
    }


def prop_bones():
    return []                       # the mallet is rigid in his right fist


KICK_P = v3((MX, YT - LEG_R, 0.0))  # the ballista rocks back about its front feet when it shoots


def extra_bones():
    """The ballista's bones (none of them deform him): frame (stand and stock: it rocks back a little as it shoots),
    arm_n / arm_f (each bow arm, turning on its skein), str_n / str_f (each half of the string, riding its arm's tip:
    aimed at the claw and stretched to reach it), slider (with the claw block: parentless, posed whole as it runs along
    the stock and rocks with it), trigger (the claw, on its pin), winch (drum and crank), haul (the windlass rope: aimed at the claw block and stretched), bolt (the bolt in
    the groove), carry (the bolt he lifts) and props (the bundle of bolts and its rests: still)."""
    sb = v3((MX, slider_back(), STOCK_Z + SLH))
    return [
        ("frame", KICK_P, KICK_P + v3((0, 0.4, 0)), None),
        ("arm_n", skein_c(-1), arm_tip(-1, COCKED), "frame"),
        ("arm_f", skein_c(1), arm_tip(1, COCKED), "frame"),
        ("str_n", arm_tip(-1, COCKED), claw_pt(), "arm_n"),
        ("str_f", arm_tip(1, COCKED), claw_pt(), "arm_f"),
        ("slider", sb, sb - v3((0, 0.3, 0)), None),
        ("trigger", TRIG_P, TRIG_P + v3((0, 0.11, 0.075)), "slider"),
        ("winch", v3((MX + CHEEK_X, DRUM[1], DRUM[2])), v3((CRANK_X, DRUM[1], DRUM[2])), "frame"),
        ("haul", haul_start(), haul_end(), "frame"),
        ("bolt", bolt_nock(), bolt_nock() + v3((0, -0.3, 0)), "slider"),
        ("carry", CARRY_C, CARRY_C + v3((0, 0, 0.15)), None),
        ("props", PILE, PILE + v3((0, 0, 0.3)), None),
    ]


def _by_side(near, far):
    def fn(ob, skin_ob, arm):
        groups = {}
        for v in ob.data.vertices:
            _blend_add(ob, groups, v.index, {near if v.co.x < MX else far: 1.0})
    return fn


def iron_weights(ob, skin_ob, arm):
    """The armlets ride the upper arms, the buckle the belly."""
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if abs(p.x) > 0.3:
            w = {"upperarm.R" if p.x < 0 else "upperarm.L": 1.0}
        else:
            w = {"spine": 0.7, "root": 0.3}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Beard": ("rigid", "head"), "Helmet": ("rigid", "head"),
        "Tunic": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L"},
                  {"thigh.R": 0.45, "thigh.L": 0.45, "upperarm.R": 0.85, "upperarm.L": 0.85}),
        "Trousers": ("transfer", TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Leather": ("transfer", TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Iron": ("custom", iron_weights), "Mallet": ("rigid", "hand.R"),
        "Frame": ("rigid", "frame"), "Arms": ("custom", _by_side("arm_n", "arm_f")),
        "Strings": ("custom", _by_side("str_n", "str_f")), "Slider": ("rigid", "slider"), "Trigger": ("rigid", "trigger"),
        "Winch": ("rigid", "winch"), "Haul": ("rigid", "haul"), "Bolt": ("rigid", "bolt"), "Spares": ("rigid", "props"),
        "Carry": ("rigid", "carry"), "Rests": ("rigid", "props"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.8
    if part in ("Frame", "Rests", "Spares"):
        return 0.7
    if part in ("Arms", "Slider", "Winch", "Bolt", "Carry", "Trigger", "Haul", "Strings"):
        return 0.85
    if part in ("Mallet", "Helmet"):
        return 0.95
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Beard", beard_field(), 0.0022 if fine else 0.0032),
        ("Helmet", helmet_field(), 0.002 if fine else 0.003),
        ("Tunic", tunic_field(), 0.0026 if fine else 0.0036),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Iron", iron_field(), 0.0018 if fine else 0.0026),
        ("Mallet", mallet_field(), 0.002 if fine else 0.003),
        ("Frame", frame_field(), 0.0036 if fine else 0.005),
        ("Arms", arms_field(), 0.0026 if fine else 0.0036),
        ("Strings", strings_field(), 0.0016 if fine else 0.0022),
        ("Slider", slider_field(), 0.0024 if fine else 0.0034),
        ("Trigger", trigger_field(), 0.0016 if fine else 0.0024),
        ("Winch", winch_field(), 0.0024 if fine else 0.0034),
        ("Haul", haul_field(), 0.0016 if fine else 0.0022),
        ("Bolt", bolt_field(), 0.0016 if fine else 0.0022),
        ("Spares", spares_field(), 0.0018 if fine else 0.0024),
        ("Carry", carry_field(), 0.0016 if fine else 0.0022),
        ("Rests", rests_field(), 0.0026 if fine else 0.0036),
    ]
