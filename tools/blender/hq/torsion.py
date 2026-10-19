"""The Torsion Catapult (HQ tower, Bronze Age): a one-armed torsion engine on a four-wheeled cart, and the burly engineer
who works it. Rest pose: he stands in an A-pose facing -Y (the way it shoots), feet at z = 0, the cart on his left (+X);
the engine is cocked (its arm wound down toward the back, a stone ball in the cup).

Him: big and barrel-chested, shaven-headed, heavy black brows, a hooked nose and a great square black beard of wavy
locks ending in rows of tight curls, a curled moustache; a red cloth band round his head with a bronze rosette; a saffron
wool tunic to the knee with short sleeves and a blue border with a red stripe and a fringe, a wide leather belt with a
bronze plate, bronze armlets, leather wrist wraps and sandals. A wooden mallet with bronze bands, rigid in his right fist.

The engine: two cedar side beams on four solid wheels (three planks and two battens each, leather tyres studded with
bronze nails), cross beams, a raised spring block on each beam carrying the twisted sinew skein between big bronze
washers with their lever bars, the throwing arm through the skein (rope-bound, bronze bands, a bronze-bound cup at its
end), two posts with a cross bar and a stuffed leather buffer that stops the arm, a windlass at the back (rope on the
drum, a bronze ratchet and a crank on his side), the trigger: a pawl in the ratchet held by a pin he knocks down with
the mallet (the drum runs free and the arm flies). Behind him a heap of dressed stone balls on a reed mat and two pitch
pots stopped with straw.

Painted labels on the engine (material `siege`): 0 wood with the grain along Y, 10 along X, 11 along Z; 5 red ochre, 7
blue paint; 6 bronze; 8 rope and sinew; 9 leather."""
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
GX, GZ, RED, BLUE, BRONZE, ROPE, HIDE = 10, 11, 5, 7, 6, 8, 9        # engine labels (wood grain Y is 0)

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


# ======================================================================================= beard, head band
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


CURL_Z = 1.33              # below this the beard ends in rows of tight round curls


def beard_tex(P):
    """Wavy locks running down the beard, ending in rows of tight round curls along its squared bottom (the Assyrian
    way); positive pushes the surface in."""
    x, z = P[:, 0], P[:, 2]
    ph = x / F(0.027) + F(0.32) * np.sin(z * F(36) + x * F(9))
    lock = np.abs(np.sin(ph * F(math.pi)))
    d_lock = F(0.0028) - F(0.0055) * lock * lock + F(0.0012) * NOISE(P * np.array([90, 90, 30], F))
    zz = (F(CURL_Z) - z) / F(0.036)
    r = np.floor(zz)
    v = zz - r
    u = x / F(0.034) + F(0.5) * np.mod(r, F(2))
    u = u - np.floor(u)
    d2 = (u - F(0.5)) ** 2 + (v - F(0.5)) ** 2
    b = np.clip(F(1) - d2 * F(3.6), 0, 1)
    dome = b * b * (F(3) - F(2) * b)
    ring = np.exp(-((np.sqrt(d2) - F(0.17)) / F(0.06)) ** 2)            # a spiral's raised turn round each curl's heart
    d_curl = F(0.004) - F(0.006) * dome - F(0.002) * ring + F(0.001) * NOISE(P * F(110))
    t = smoothstep(-0.2, 0.25, zz)
    return d_lock * (F(1) - t) + d_curl * t


BEARD_TILT = -0.41


def beard_field():
    """A great square black beard: over the cheeks and jaw and hanging onto his chest, squared off below; wavy locks
    ending in rows of tight curls; a moustache curled up at both ends."""
    fd = Field("Beard")
    hull = head_hull()
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.557) + F(0.085) * smoothstep(0.055, 0.14, ax)                       # chin and jaw, up the cheeks
        top = np.where(ax > F(0.152), F(1.71), top)                                     # sideburns to the temples
        lips = (x / F(0.066)) ** 2 + ((y + F(0.18)) / F(0.07)) ** 2 + ((z - F(1.545)) / F(0.026)) ** 2 - F(1.0)
        back = np.where(ax > F(0.14), y - F(0.035), y - F(0.0))
        return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), F(1.4) - z)
    fd.add(Inter(Shell(hull, 0.01, 0.026, pad=0.06, disp=beard_tex, disp_amp=0.008), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.008), 0.0)
    # the hanging block: from under the chin down onto the chest, tilted out over it, a squared bottom
    fd.add(RoundBox(v3((0, -0.19, 1.345)), (0.13, 0.055, 0.12), 0.05, R=euler(BEARD_TILT, 0, 0), disp=beard_tex, disp_amp=0.008), 0.045)
    fd.add(Ellipsoid(hp((0, -0.15, 1.47)), v3((0.13, 0.07, 0.07)) * HS, disp=beard_tex, disp_amp=0.008), 0.04)
    # moustache: two thick locks from under the nose out over the mouth's corners, curled up at the ends
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.222, 1.574)), hp((sx * 0.042, -0.21, 1.566)), hp((sx * 0.076, -0.184, 1.551)),
               hp((sx * 0.098, -0.162, 1.548))]
        fd.add(Lock(pts, [hr(0.014), hr(0.019), hr(0.016), hr(0.01)], [hr(0.011), hr(0.012), hr(0.01), hr(0.007)],
                    [norm(v3((sx * 0.25, -1, 0.35)))] * 4, k=hr(0.006), disp=strands, disp_amp=0.003), hr(0.006))
        c = hp((sx * 0.104, -0.158, 1.562))
        fd.add(Torus(c, hr(0.011), hr(0.006), R=rot_from_axes(z_axis=(sx * 0.35, -1.0, 0.0))), hr(0.004))
    return fd


# the head band runs round the skull above the brows, a little lower at the back (design coordinates)
BAND_F = v3((0.0, -0.19, 1.808))
BAND_B = v3((0.0, 0.2, 1.73))
_BAND_N = norm(v3((0, -(BAND_B[2] - BAND_F[2]) / (BAND_B[1] - BAND_F[1]), 1.0)))


def band_d(P):
    return (hinv(P) - BAND_F.astype(F)) @ _BAND_N.astype(F)


def band_field():
    """A red cloth band round his head (tied at the back, two short tails)."""
    fd = Field("Band")
    sk = skull()
    cloth = lambda P: F(0.0012) * NOISE(P * F(60))
    fd.add(Inter(Shell(sk, 0.008, 0.016, pad=0.06, disp=cloth, disp_amp=0.002), Func(lambda P: np.abs(band_d(P)) - F(0.022), HEAD_C - 0.35, HEAD_C + 0.35), 0.005), 0.0)
    knot = hp((0.0, 0.21, 1.735))
    fd.add(Ellipsoid(knot + v3((0, 0.012, 0)), (0.03, 0.022, 0.024)), 0.006)
    for sx in (-1, 1):
        pts = [knot + v3((sx * 0.012, 0.01, -0.01)), knot + v3((sx * 0.03, 0.04, -0.07)), knot + v3((sx * 0.038, 0.05, -0.14))]
        fd.add(Lock(pts, [0.016, 0.018, 0.016], [0.004, 0.004, 0.0035], [v3((0, 1, 0))] * 3, k=0.004, disp=cloth, disp_amp=0.002), 0.006)
    return fd


def band_front():
    """The point on the band at the middle of his forehead, and the outward normal there."""
    sk = skull()
    o = hp((0.0, -0.6, 1.808 + 0.0))
    h, ok = ray_hit(Func(lambda P: sk.eval(P) - F(0.018), HEAD_C - 0.5, HEAD_C + 0.5), [o], [v3((0, 1, 0))], tmax=0.7)
    return h[0], norm(v3((0, -1, 0.15)))


# ======================================================================================= tunic, belt, leather, bronze
def tunic_base():
    b = Field("TunicBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.055)
        b.add(upper_arm(side), 0.05)
    b.add(RoundCone((0, 0.03, 0.92), (0, 0.03, 0.45), 0.26, 0.33), 0.09)            # the skirt
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
    return F(0.47) + F(0.02) * np.clip(np.cos(a), 0, 1) + F(0.006) * NOISE(P * F(8))


def tunic_field():
    """Saffron wool tunic to the knee, short sleeves; a blue border (label 5) with a red stripe (6) round the hem and the
    sleeves; a short fringe along the hem."""
    fd = Field("Tunic")
    base = tunic_base()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        k = smoothstep(0.9, 0.7, P[:, 2])
        return F(0.005) * np.sin(a * F(15) + F(0.7) * NOISE(P * F(3))) * k + F(0.0015) * NOISE(P * F(25))
    def keep(P):
        fringe = F(0.03) * (np.abs(np.sin(np.arctan2(P[:, 0], -(P[:, 1] - F(0.03))) * F(55))) > F(0.45)).astype(F)
        k = np.maximum(hem_z(P) - fringe - P[:, 2], _neck_cut(P))
        return np.maximum(np.maximum(k, _sleeve(P, "R")), _sleeve(P, "L"))
    fd.add(Inter(Shell(base, 0.024, 0.022, pad=0.1, disp=folds, disp_amp=0.006), Func(keep, (-1, -1, 0.3), (1, 1, 1.6)), 0.005), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (hem_z(P) + F(0.06)), (-1, -1, 0.3), (1, 1, 0.7)), 5)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - (hem_z(P) + F(0.032))) - F(0.008), (-1, -1, 0.3), (1, 1, 0.7)), 6)
    for side in ("R", "L"):
        def cuff(P, side=side):
            s = _sleeve(P, side)
            return np.where(s > F(-0.5), np.abs(s + F(0.03)) - F(0.03), F(1.0))
        def stripe(P, side=side):
            s = _sleeve(P, side)
            return np.where(s > F(-0.5), np.abs(s + F(0.032)) - F(0.007), F(1.0))
        fd.paint(Func(cuff, (-1, -1, 0.8), (1, 1, 1.6)), 5)
        fd.paint(Func(stripe, (-1, -1, 0.8), (1, 1, 1.6)), 6)
    # the neckline's border
    fd.paint(Func(lambda P: np.abs(_neck_cut(P) + F(0.02)) - F(0.02), (-1, -1, 1.2), (1, 1, 1.6)), 5)
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


def leather_field():
    """A wide belt, wrist wraps, sandals."""
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
    return fd


def belt_front():
    bb = belt_base()
    p, _ = ray_hit(Func(lambda P: bb.eval(P) - F(0.085), (-1, -1, 0.7), (1, 1, 1.3)), [v3((0, -0.8, BELT_Z - 0.03 * 0.25))], [v3((0, 1, 0))], tmax=0.9)
    return p[0]


def bronze_field():
    """Spiral armlets above the elbows, the belt plate with a rosette, the rosette on his head band."""
    fd = Field("Bronze")
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
    fd.add(RoundBox(c + v3((0, -0.004, 0)), (0.07, 0.012, 0.046), 0.01), 0.0)
    fd.add(Sphere(c + v3((0, -0.016, 0)), 0.018), 0.005)
    for k in range(8):
        a = 2 * math.pi * k / 8
        fd.add(Sphere(c + v3((math.cos(a) * 0.03, -0.012, math.sin(a) * 0.026)), 0.0075), 0.003)
    p, n = band_front()
    fd.add(Cylinder(p + n * 0.004, 0.026, 0.008, rr=0.003, R=rot_from_axes(z_axis=n)), 0.0)
    fd.add(Sphere(p + n * 0.01, 0.01), 0.003)
    for k in range(6):
        a = 2 * math.pi * k / 6
        d = rot_from_axes(z_axis=n) @ v3((math.cos(a), math.sin(a), 0))
        fd.add(Sphere(p + n * 0.008 + d * 0.017, 0.0055), 0.002)
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
    """Hard wood (label 0), two bronze bands round the head and a bronze collar (6), a red cord grip (5)."""
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


# ======================================================================================= the engine (layout)
MX, MY = 0.74, -0.66          # the cart's centre line (x) and reference (y); it shoots toward -Y
BW = 0.27                     # side beams' centre offset from MX
BEAM_Z = 0.33
BEAM_HW, BEAM_HH = 0.052, 0.07
Y0, Y1 = MY - 0.72, MY + 1.16  # the side beams' front and back ends
WR, WT, WX = 0.23, 0.034, 0.385
WY = (MY - 0.5, MY + 0.32)    # front and back axles (y): the back wheels clear of the crank's circle
AXLE = v3((MX, MY + 0.06, 0.48))         # the skein's centre: the arm turns about it
COCK = math.radians(15.0)     # the arm's angle (from horizontal, toward the back) wound down
FIRED = math.radians(96.0)    # ... against the buffer
LONG = 1.12                   # pivot -> the cup's centre
CUP_UP = 0.04
CUP_R = 0.118
BALL_R = 0.078
HAUL_S = 0.92                 # where the windlass rope is tied on the arm
DRUM = v3((MX, MY + 0.66, 0.49))
DRUM_R = 0.062
NEAR = MX - BW                # the near side beam (his side, -X)
CRANK_X = NEAR - 0.1          # the crank's plane
CRANK_R = 0.14
CRANK_PHI = math.radians(70.0)          # the crank's angle in the rest pose (0 = toward the back, + = up)
HANDLE_L = 0.13
PAD = v3((MX, MY - 0.128, 1.255))       # the stuffed pad the arm hits (at FIRED, 0.78 along the arm)
BAR = v3((MX, MY - 0.235, 1.255))       # the buffer's cross bar
POST_Y = MY - 0.325
POST_TOP = 1.37
PIN_Y = MY + 0.42
PIN_TOP = v3((NEAR - 0.012, PIN_Y, 0.585))
PILE = v3((0.12, 0.44, 0.0))              # the heap of stone balls
POTS = (v3((-0.27, 0.3, 0.0)), v3((-0.11, 0.44, 0.0)))
YAW_PIVOT = (0.44, -0.47, 0.0)            # the tower turns about this point (keeps the whole cart on the base)


def arm_dir(a):
    return v3((0.0, math.cos(a), math.sin(a)))


def arm_up(a):
    return v3((0.0, -math.sin(a), math.cos(a)))


def arm_pt(s, a=COCK, up=0.0):
    return AXLE + arm_dir(a) * s + arm_up(a) * up


def cup_c(a=COCK):
    return arm_pt(LONG, a, CUP_UP)


def ball_c(a=COCK):
    """The stone ball in the cup."""
    return cup_c(a) + arm_up(a) * (BALL_R - 0.045)


def haul_point(a=COCK):
    return arm_pt(HAUL_S, a, -0.058)


def haul_start():
    """Where the rope leaves the drum (its top, toward the arm)."""
    d = norm(haul_point(COCK) - DRUM)
    return DRUM + d * (DRUM_R + 0.01)


def crank_handle(phi):
    """The crank handle's inner and outer ends at crank angle phi (0 = toward the back, + = up)."""
    c = v3((CRANK_X, DRUM[1] + CRANK_R * math.cos(phi), DRUM[2] + CRANK_R * math.sin(phi)))
    return c, c - v3((HANDLE_L, 0, 0))


def pile_balls():
    """(centre, bone) of the stone balls in the heap: three on the mat, one on them (the one he lifts), one rolled aside."""
    m = 0.012
    out = []
    for k in range(3):
        a = math.radians(30 + 120 * k)
        out.append((PILE + v3((math.cos(a) * 0.0866, math.sin(a) * 0.0866, m + BALL_R)), "props"))
    # (the top ball sits a hair proud of the three under it, so it meshes as its own island and rides the carry bone)
    out.append((PILE + v3((0, 0, m + BALL_R + math.sqrt((2 * BALL_R) ** 2 - 0.0866 ** 2) + 0.009)), "carry"))
    out.append((PILE + v3((-0.15, -0.1, BALL_R)), "props"))
    return out


CARRY_C = pile_balls()[3][0]


# ======================================================================================= the engine (sculpt)
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


def wheel(fd, x, y, outward):
    """A solid wheel of three planks held by two battens, a leather tyre studded with bronze nails, a hub with a
    lynch pin. `outward` = +1/-1 (the side the battens are on)."""
    c = v3((x, y, WR))
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    def disc(P):
        q = P - c.astype(F)
        rr = np.sqrt(q[:, 1] ** 2 + q[:, 2] ** 2)
        t = F(WT) + F(0.012) * np.clip(F(1) - rr / F(WR), 0, 1)              # thicker toward the hub
        return np.maximum(rr - F(WR - 0.016), np.abs(q[:, 0]) - t)
    fd.add(Func(disc, c - 0.25, c + 0.25, disp=GRAIN, disp_amp=0.002), 0.0, GZ)
    for s in (-1, 1):                                                         # the plank seams
        fd.sub(Func(lambda P, s=s: np.maximum(np.abs(P[:, 1] - F(y + s * 0.07)) - F(0.0025),
                                              np.abs(np.abs(P[:, 0] - F(x)) - F(WT + 0.006)) - F(0.006)), c - 0.25, c + 0.25), 0.002)
    for s in (-1, 1):                                                         # battens across the planks
        fd.add(RoundBox(c + v3((outward * (WT + 0.006), 0, s * 0.1)), (0.012, WR * 0.76, 0.022), 0.006, disp=GRAIN, disp_amp=0.0015), 0.004, 0)
        for k in (-1, 0, 1):
            fd.add(Sphere(c + v3((outward * (WT + 0.02), k * 0.07, s * 0.1)), 0.0095), 0.002, BRONZE)
    fd.add(Torus(c, WR - 0.012, 0.024, R=Rx), 0.004, HIDE)                    # the tyre
    for k in range(20):
        a = 2 * math.pi * k / 20
        for s in (-1, 1):
            fd.add(Sphere(c + v3((s * 0.016, math.cos(a) * (WR + 0.006), math.sin(a) * (WR + 0.006))), 0.0085), 0.002, BRONZE)
    fd.add(Cylinder(c, 0.06, 0.14, rr=0.016, R=Rx), 0.01, RED)               # the hub
    fd.add(Torus(c + v3((outward * 0.07, 0, 0)), 0.045, 0.009, R=Rx), 0.003, BRONZE)
    fd.add(RoundCone(c + v3((outward * 0.085, 0, 0.04)), c + v3((outward * 0.085, 0, -0.045)), 0.008, 0.007), 0.003, BRONZE)


def frame_field():
    """Side beams, cross beams, axles and wheels, spring blocks and washers with their levers, the skein, the buffer
    posts, braces, cross bar and pad, the windlass's bearing blocks, the trigger block."""
    fd = Field("Frame")
    zb = BEAM_Z
    for sx in (-1, 1):
        x = MX + sx * BW
        fd.add(box((x, (Y0 + Y1) / 2, zb), (BEAM_HW, (Y1 - Y0) / 2, BEAM_HH)), 0.0, 0)
        for ye in (Y0, Y1):                                                   # bronze shoes on the beam ends
            sgn = -1 if ye == Y0 else 1
            fd.add(Inter(RoundBox(v3((x, ye - sgn * 0.03, zb)), (BEAM_HW + 0.006, 0.04, BEAM_HH + 0.006), 0.012),
                         Func(lambda P, ye=ye, sgn=sgn: (F(ye) - P[:, 1]) * F(sgn) - F(0.075), (x - 0.1, ye - 0.12, zb - 0.1), (x + 0.1, ye + 0.12, zb + 0.1)), 0.002), 0.003, BRONZE)
        # paint: a red stripe along the outer face, blue toward the ends
        def stripe(P, x=x, sx=sx):
            return np.maximum(np.maximum(np.abs(P[:, 2] - F(zb)) - F(0.022), (F(x) - P[:, 0]) * F(sx) + F(0.02)),
                              np.abs(P[:, 1] - F((Y0 + Y1) / 2)) - F((Y1 - Y0) / 2 - 0.1))
        fd.paint(Func(stripe, (x - 0.1, Y0, zb - 0.1), (x + 0.1, Y1, zb + 0.1)), RED)
        for yb in (Y0 + 0.13, Y1 - 0.13):
            fd.paint(Func(lambda P, yb=yb, x=x, sx=sx: np.maximum(np.abs(P[:, 1] - F(yb)) - F(0.03), (F(x) - P[:, 0]) * F(sx) + F(0.02)),
                          (x - 0.1, yb - 0.1, zb - 0.1), (x + 0.1, yb + 0.1, zb + 0.1)), BLUE)
    for yc in (Y0 + 0.05, POST_Y, Y1 - 0.05):                                   # cross beams
        fd.add(box((MX, yc, zb + 0.005), (BW - 0.03, 0.042, 0.048)), 0.006, GX)
    for yw in WY:                                                            # axles and wheels
        fd.add(Cylinder(v3((MX, yw, WR)), 0.03, 2 * (WX + 0.08), rr=0.008, R=rot_from_axes(z_axis=(1, 0, 0)), disp=GRAIN, disp_amp=0.002), 0.004, GX)
        for sx in (-1, 1):
            fd.add(box((MX + sx * BW, yw, (WR + zb - BEAM_HH) / 2 + 0.005), (0.045, 0.06, (zb - BEAM_HH - WR) / 2 + 0.025)), 0.006, GZ)
            wheel(fd, MX + sx * WX, yw, sx)
    # spring blocks, washers, levers
    for sx in (-1, 1):
        x = MX + sx * BW
        fd.add(box((x, AXLE[1], AXLE[2] - 0.015), (0.066, 0.15, 0.14), r=0.02), 0.01, 0)
        fd.add(RoundBox(v3((x + sx * 0.066, AXLE[1], AXLE[2])), (0.006, 0.13, 0.13), 0.006), 0.002, BRONZE)       # the seat plate
        wc = v3((x + sx * 0.084, AXLE[1], AXLE[2]))
        Rx = rot_from_axes(z_axis=(1, 0, 0))
        fd.add(Cylinder(wc, 0.11, 0.026, rr=0.006, R=Rx), 0.003, BRONZE)
        for k in range(12):                                                  # the ratchet teeth round the washer
            a = 2 * math.pi * k / 12
            d = v3((0, math.cos(a), math.sin(a)))
            tng = v3((0, -math.sin(a), math.cos(a)))
            fd.add(RoundBox(wc + d * 0.112 + tng * 0.008, (0.012, 0.012, 0.016), 0.003, R=rot_from_axes(y_axis=d, z_axis=(1, 0, 0))), 0.003, BRONZE)
        fd.add(Torus(wc + v3((sx * 0.014, 0, 0)), 0.075, 0.017, R=Rx), 0.004, BRONZE)
        lev = norm(v3((0, math.sin(math.radians(28)), math.cos(math.radians(28)))))
        lc = wc + v3((sx * 0.04, 0, 0))
        fd.add(RoundCone(lc - lev * 0.17, lc + lev * 0.19, 0.021, 0.019, disp=GRAIN, disp_amp=0.002), 0.004, GZ)
        for e in (lc - lev * 0.17, lc + lev * 0.19):
            fd.add(Sphere(e, 0.025), 0.004, BRONZE)
        fd.add(Ellipsoid(lc + v3((-sx * 0.008, 0, 0)), (0.03, 0.05, 0.05), disp=lambda P: F(0.003) * np.sin(P[:, 1] * F(260) + P[:, 2] * F(260)), disp_amp=0.004), 0.008, ROPE)
        stop = v3((x + sx * 0.104, AXLE[1] - 0.12, AXLE[2] - 0.125))          # the peg the lever bears against
        fd.add(Cylinder(stop, 0.016, 0.08, rr=0.004, R=Rx), 0.003, BRONZE)
    # the skein: a thick bundle of twisted sinew between the blocks (the arm through its middle)
    def skein(P):
        q = P - AXLE.astype(F)
        rr = np.sqrt(q[:, 1] ** 2 + q[:, 2] ** 2)
        a = np.arctan2(q[:, 2], q[:, 1])
        tw = F(0.006) * np.sin(a * F(9) + q[:, 0] * F(60))
        bulge = F(0.016) * np.exp(-(q[:, 0] / F(0.085)) ** 2)
        return np.maximum(rr - (F(0.072) + bulge) + tw, np.abs(q[:, 0]) - F(BW + 0.08))
    fd.add(Func(skein, AXLE - v3((0.5, 0.15, 0.15)), AXLE + v3((0.5, 0.15, 0.15)), disp=lambda P: F(0.0012) * NOISE(P * F(160)), disp_amp=0.002), 0.004, ROPE)
    # the buffer: two posts braced forward, a cross bar on their backs, a stuffed leather pad lashed to it
    for sx in (-1, 1):
        x = MX + sx * BW
        fd.add(box((x, POST_Y, (zb + BEAM_HH + POST_TOP) / 2), (0.048, 0.048, (POST_TOP - zb - BEAM_HH) / 2)), 0.006, GZ)
        fd.add(tbeam((x, Y0 + 0.12, zb + 0.04), (x, POST_Y - 0.03, 1.08), (1, 0, 0), 0.036, 0.036, disp=GRAIN, disp_amp=0.002), 0.008, GZ)
        fd.add(Sphere(v3((x, POST_Y, POST_TOP + 0.028)), 0.042), 0.006, BRONZE)
        fd.add(RoundBox(v3((x, POST_Y, POST_TOP - 0.004)), (0.054, 0.054, 0.015), 0.005), 0.003, BRONZE)
        for zz in (0.82, 0.9):
            fd.paint(Func(lambda P, zz=zz, x=x: np.maximum(np.abs(P[:, 2] - F(zz)) - F(0.025), np.abs(P[:, 0] - F(x)) - F(0.06)),
                          (x - 0.1, POST_Y - 0.1, zz - 0.06), (x + 0.1, POST_Y + 0.1, zz + 0.06)), RED if zz < 0.86 else BLUE)
    fd.add(box(BAR, (BW + 0.075, 0.045, 0.05)), 0.006, GX)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 0] - F(MX)) - F(BW - 0.06), np.abs(P[:, 2] - F(BAR[2])) - F(0.06)),
                  BAR - v3((0.5, 0.1, 0.1)), BAR + v3((0.5, 0.1, 0.1))), BLUE)
    for sx in (-1, 1):
        fd.add(RoundBox(BAR + v3((sx * (BW + 0.075), 0, 0)), (0.012, 0.05, 0.055), 0.006), 0.003, BRONZE)
    fd.add(Ellipsoid(PAD, (0.13, 0.062, 0.08), disp=lambda P: F(0.003) * NOISE(P * F(22)), disp_amp=0.004), 0.01, HIDE)
    bp = Field("BarPad")
    bp.add(RoundBox(BAR, (BW + 0.075, 0.045, 0.05), 0.012), 0.0)
    bp.add(Ellipsoid(PAD, (0.13, 0.062, 0.08)), 0.01)
    for sx in (-1, 1):
        cx = MX + sx * 0.088
        fd.add(Inter(Shell(bp, 0.004, 0.012, pad=0.05), Func(lambda P, cx=cx: np.abs(P[:, 0] - F(cx)) - F(0.011), BAR - 0.3, BAR + 0.3), 0.003), 0.004, ROPE)
    # the windlass's bearing blocks, the trigger block on the near beam
    for sx in (-1, 1):
        fd.add(box((MX + sx * BW, DRUM[1], DRUM[2] - 0.005), (0.055, 0.058, 0.09)), 0.008, GZ)
        fd.add(RoundBox(v3((MX + sx * BW, DRUM[1], DRUM[2] + 0.09)), (0.06, 0.064, 0.012), 0.005), 0.003, BRONZE)
    fd.add(box((NEAR, PIN_Y, zb + BEAM_HH + 0.045), (0.06, 0.07, 0.045)), 0.008, 0)
    fd.add(RoundBox(v3((NEAR - 0.062, PIN_Y, zb + BEAM_HH + 0.045)), (0.006, 0.06, 0.035), 0.004), 0.002, BRONZE)
    fd.add(Cylinder(PIN_TOP - v3((0, 0, 0.05)), 0.011, 0.1, rr=0.003), 0.003, BRONZE)          # the trigger pin
    fd.add(Ellipsoid(PIN_TOP, (0.03, 0.03, 0.017)), 0.004, BRONZE)
    return fd


def arm_field():
    """The throwing arm (cocked): a tapered beam through the skein, rope-bound by it, two bronze bands, the rope ring, and
    the bronze-bound cup at its end lined with leather."""
    fd = Field("Arm")
    d, up = arm_dir(COCK), arm_up(COCK)
    a0, a1 = arm_pt(-0.11), arm_pt(LONG - 0.07)
    W0, D0, W1, D1 = 0.05, 0.058, 0.038, 0.04
    fd.add(tbeam(a0, a1, up, W0, D0, W1, D1, r=0.016, disp=GRAIN, disp_amp=0.002), 0.0, 0)
    def band(s0, w, label, extra=0.007, ridges=False):
        c = arm_pt(s0)
        dd = d.astype(F)
        rid = (lambda P: F(0.002) * np.sin(((P - c.astype(F)) @ dd) * F(330))) if ridges else None
        t = s0 / LONG
        fd.add(Inter(tbeam(a0, a1, up, W0 + extra, D0 + extra, W1 + extra, D1 + extra, r=0.018, disp=rid, disp_amp=0.003 if ridges else 0.0),
                     Func(lambda P: np.abs((P - c.astype(F)) @ dd) - F(w), c - 0.2, c + 0.2), 0.002), 0.003, label)
    band(0.19, 0.055, ROPE, 0.008, ridges=True)
    band(-0.08, 0.026, ROPE, 0.008, ridges=True)
    band(0.46, 0.017, BRONZE)
    band(0.74, 0.017, BRONZE)
    hpnt = haul_point(COCK)
    fd.add(Torus(hpnt + up * 0.004, 0.018, 0.0055, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, BRONZE)
    fd.add(RoundBox(arm_pt(HAUL_S, up=-0.04), (0.04, 0.012, 0.012), 0.004, R=rot_from_axes(z_axis=up, y_axis=d)), 0.004, BRONZE)
    # the cup: a carved wooden bowl, its rim and two straps of bronze, leather inside
    cc = cup_c(COCK)
    Rc = rot_from_axes(z_axis=up, y_axis=d)
    bowl = Ellipsoid(cc, (CUP_R, CUP_R, 0.082), R=Rc)
    rim_n = up
    fd.add(Inter(Shell(bowl, 0.0, 0.026, pad=0.04, disp=GRAIN, disp_amp=0.002), Plane(cc + up * 0.045, rim_n), 0.006), 0.012, 0)
    fd.add(RoundBox(arm_pt(LONG - 0.13, up=0.0), (0.04, 0.05, 0.03), 0.012, R=rot_from_axes(z_axis=up, y_axis=d)), 0.03, 0)
    fd.add(Ellipsoid(cc - up * 0.042, (0.052, 0.08, 0.05), R=Rc), 0.03, 0)             # where the bowl sits on the arm
    rim_c = cc + up * 0.04
    rim_r = CUP_R * math.sqrt(max(0.0, 1 - (0.04 / 0.082) ** 2))
    fd.add(Torus(rim_c, rim_r, 0.012, R=Rc), 0.004, BRONZE)
    for ang in (0.0, math.pi / 2):
        ax2 = Rc @ v3((math.cos(ang), math.sin(ang), 0))
        strap = Inter(Shell(bowl, 0.012, 0.007, pad=0.04), Func(lambda P, ax2=ax2: np.abs((P - cc.astype(F)) @ ax2.astype(F)) - F(0.012), cc - 0.3, cc + 0.3), 0.002)
        fd.add(Inter(strap, Plane(cc + up * 0.04, up), 0.002), 0.003, BRONZE)
    fd.paint(Inter(Ellipsoid(cc, (CUP_R - 0.006, CUP_R - 0.006, 0.077), R=Rc), Plane(cc + up * 0.03, up), 0.0), HIDE)
    return fd


def winch_field():
    """The windlass: the drum with rope on it, bronze rims, the ratchet wheel and the crank on his side (it turns with the
    'winch' bone)."""
    fd = Field("Winch")
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    L = 2 * (BW - 0.055)
    fd.add(Cylinder(DRUM, DRUM_R, L, rr=0.008, R=Rx, disp=GRAIN, disp_amp=0.002), 0.0, GX)
    for sx in (-1, 1):
        fd.add(Torus(DRUM + v3((sx * (L / 2 - 0.012), 0, 0)), DRUM_R + 0.004, 0.011, R=Rx), 0.003, BRONZE)
    for k in range(7):
        fd.add(Torus(DRUM + v3((-0.075 + 0.025 * k, 0, 0)), DRUM_R + 0.006, 0.009, R=Rx), 0.002, ROPE)
    ax0, ax1 = v3((MX + BW + 0.07, DRUM[1], DRUM[2])), v3((CRANK_X - 0.012, DRUM[1], DRUM[2]))
    fd.add(Cylinder((ax0 + ax1) / 2, 0.026, float(np.linalg.norm(ax1 - ax0)), rr=0.006, R=Rx), 0.004, BRONZE)
    rc = v3((NEAR - 0.075, DRUM[1], DRUM[2]))                                    # the ratchet wheel
    fd.add(Cylinder(rc, 0.07, 0.022, rr=0.004, R=Rx), 0.003, BRONZE)
    for k in range(10):
        a = 2 * math.pi * k / 10
        dd = v3((0, math.cos(a), math.sin(a)))
        tng = v3((0, -math.sin(a), math.cos(a)))
        fd.add(RoundBox(rc + dd * 0.074 + tng * 0.007, (0.011, 0.012, 0.014), 0.003, R=rot_from_axes(y_axis=dd, z_axis=(1, 0, 0))), 0.002, BRONZE)
    h0, h1 = crank_handle(CRANK_PHI)
    fd.add(tbeam(v3((CRANK_X, DRUM[1], DRUM[2])), h0, (1, 0, 0), 0.026, 0.012, 0.02, 0.011, r=0.006), 0.004, BRONZE)
    fd.add(Sphere(v3((CRANK_X, DRUM[1], DRUM[2])), 0.032), 0.004, BRONZE)
    fd.add(RoundCone(h0 + v3((0.012, 0, 0)), h1, 0.023, 0.021, disp=GRAIN, disp_amp=0.0015), 0.004, GX)
    fd.add(Sphere(h1 - v3((0.012, 0, 0)), 0.029), 0.004, BRONZE)
    return fd


PAWL_P = v3((NEAR - 0.075, PIN_Y + 0.03, BEAM_Z + BEAM_HH + 0.06))     # the pawl's pivot on the trigger block


def pawl_tip():
    rc = v3((NEAR - 0.075, DRUM[1], DRUM[2]))
    d = norm(PAWL_P - rc)
    return rc + d * 0.082


def trigger_field():
    """The pawl that drops into the ratchet's teeth (the pin that holds it down is on the frame)."""
    fd = Field("Trigger")
    tip = pawl_tip()
    fd.add(tbeam(PAWL_P, tip, (1, 0, 0), 0.013, 0.012, 0.011, 0.008, r=0.005), 0.0, BRONZE)
    fd.add(Cylinder(PAWL_P, 0.022, 0.03, rr=0.005, R=rot_from_axes(z_axis=(1, 0, 0))), 0.004, BRONZE)
    return fd


def haul_field():
    """The windlass rope, cocked: from the drum up to the ring on the arm (stretched in game)."""
    fd = Field("Haul")
    a, b = haul_start(), haul_point(COCK)
    tw = lambda P: F(0.0015) * np.sin(((P - a.astype(F)) @ norm(b - a).astype(F)) * F(420) + P[:, 0] * F(300))
    fd.add(RoundCone(a, b + norm(a - b) * 0.012, 0.0095, 0.0095, disp=tw, disp_amp=0.002), 0.0)
    return fd


def stone_ball(c, r, seed):
    """A dressed stone ball: round, with faint flat facets and chisel pocks."""
    rs = np.random.RandomState(seed)
    cuts = [norm(rs.normal(size=3)) for _ in range(9)]
    def fn(P, c=c):
        q = P - c.astype(F)
        d = np.sqrt((q * q).sum(1)) - F(r)
        for n in cuts:
            d = np.maximum(d, q @ n.astype(F) - F(r * 0.965))
        return d
    return Func(fn, c - r - 0.02, c + r + 0.02, disp=lambda P: F(0.0018) * NOISE(P * F(55)) + F(0.0008) * NOISE(P * F(150)), disp_amp=0.003)


def stones_field():
    """The ball in the cup, the heap of balls on the mat behind him (the top one is the one he lifts)."""
    fd = Field("Stones")
    fd.add(stone_ball(ball_c(COCK), BALL_R, 3), 0.0)
    for i, (c, bone) in enumerate(pile_balls()):
        fd.add(stone_ball(c, BALL_R, 10 + i), 0.0)
    return fd


def stone_centres():
    return [(ball_c(COCK), "stone")] + [(c, b) for c, b in pile_balls()]


def pots_field():
    """Two pitch pots: round-bellied jars with a short neck and a lip, black bands painted on (label 5)."""
    fd = Field("Pots")
    for i, p in enumerate(POTS):
        c = p + v3((0, 0, 0.11))
        fd.add(Ellipsoid(c, (0.095, 0.095, 0.105)), 0.0)
        fd.add(RoundCone(c + v3((0, 0, 0.07)), c + v3((0, 0, 0.14)), 0.042, 0.034), 0.02)
        fd.add(Torus(c + v3((0, 0, 0.142)), 0.036, 0.009), 0.006)
        fd.add(Cylinder(p + v3((0, 0, 0.018)), 0.05, 0.036, rr=0.01), 0.03)
        for zz, w in ((0.03, 0.009), (0.0, 0.006), (-0.035, 0.009)):
            fd.paint(Func(lambda P, c=c, zz=zz, w=w: np.abs(P[:, 2] - F(c[2] + zz)) - F(w), c - 0.2, c + 0.2), 5)
    return fd


def mat_field():
    """A reed mat under the heap of balls, and the straw plugs in the pots' necks (bound with cord, label 5)."""
    fd = Field("Mat")
    fib = lambda P: F(0.0015) * np.sin(P[:, 0] * F(400)) + F(0.001) * NOISE(P * F(60))
    fd.add(RoundBox(PILE + v3((0.0, 0.02, 0.006)), (0.18, 0.16, 0.006), 0.005, R=euler(0, 0, 0.3), disp=fib, disp_amp=0.002), 0.0)
    for p in POTS:
        c = p + v3((0, 0, 0.11 + 0.15))
        fd.add(Ellipsoid(c, (0.03, 0.03, 0.04), disp=lambda P: F(0.004) * NOISE(P * F(70)), disp_amp=0.005), 0.0)
        fd.add(Torus(c - v3((0, 0, 0.02)), 0.03, 0.006), 0.003, 5)
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
GLB_NAME = "torsion_catapult"
ROOT_NAME = "TorsionCatapultHQ"
TEX_PREFIX = "torsion"
MAT_NAME = "TorsionMat"
MESH_NAME = "Torsion"
BASE_MODULE = "torsion_base"
ANIM_MODULE = "anim_torsion"
PARTS = ["Skin", "Eyes", "Teeth", "Beard", "Band", "Tunic", "Leather", "Bronze", "Mallet", "Frame", "Arm", "Winch",
         "Trigger", "Haul", "Stones", "Pots", "Mat"]
REGION_PARTS = ("Skin", "Tunic", "Mallet", "Frame", "Arm", "Winch", "Pots", "Mat")
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_EngineerSkin", "base": (0.74, 0.5, 0.34), "ruddy": (0.8, 0.44, 0.32), "lips": (0.62, 0.34, 0.28),
                      "brow": ((0.05, 0.04, 0.035), (0.12, 0.09, 0.07)),
                      "extra": ((LASH, (0.05, 0.035, 0.03), 0.5), (STUBBLE, (0.3, 0.22, 0.18), 0.6, 0.5))}),
    "Beard": ("hair", {"name": "HQ_EngineerBeard", "base": (0.07, 0.055, 0.05), "hi": (0.3, 0.24, 0.21), "low": (0.03, 0.025, 0.022),
                       "streak": (0.045, 0.035, 0.03), "tint": (0.15, 0.1, 0.08)}),
    "Band": ("cloth", {"name": "HQ_HeadBand", "col": (0.74, 0.12, 0.08)}),
    "Tunic": ("wool", {"name": "HQ_Tunic", "base": (0.86, 0.6, 0.17), "border": (0.15, 0.3, 0.62), "stripe": (0.72, 0.13, 0.08)}),
    "Leather": ("leather", {"name": "HQ_EngineerLeather", "base": (0.34, 0.19, 0.1)}),
    "Bronze": ("bronze", {"name": "HQ_EngineerBronze"}),
    "Mallet": ("spear_shaft", {"name": "HQ_Mallet"}),
    "Frame": ("siege", {"name": "HQ_Siege"}), "Arm": ("siege", {"name": "HQ_Siege"}), "Winch": ("siege", {"name": "HQ_Siege"}),
    "Trigger": ("bronze", {"name": "HQ_EngineerBronze"}),
    "Haul": ("cord", {}),
    "Stones": ("limestone", {"name": "HQ_StoneBalls"}),
    "Pots": ("terracotta", {"name": "HQ_PitchPots"}),
    "Mat": ("reed", {"name": "HQ_ReedMat"}),
}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Beard": 1900, "Band": 320, "Tunic": 1900, "Leather": 1100, "Bronze": 800,
               "Mallet": 380, "Frame": 5600, "Arm": 950, "Winch": 700, "Trigger": 170, "Haul": 80, "Stones": 900, "Pots": 520,
               "Mat": 220}
AO_EXCLUDE = ["Arm", "Winch", "Trigger", "Haul", "Stones", "Mallet"]
# the engine and its props are baked 6 m away from him: his rest pose (his left hand hangs over the cart) must leave no
# shadow on it, nor the cart on him
BAKE_APART = (["Frame", "Arm", "Winch", "Trigger", "Haul", "Stones", "Pots", "Mat"], (6.0, 0.0, 0.0))
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


KICK_P = v3((MX, WY[0], 0.0))       # the cart rocks about its front wheels' footing when the arm slams


def extra_bones():
    """The engine's bones (none of them deform him): frame (the cart; it rocks when the arm slams), arm (turns on the
    skein), stone (the ball in the cup), haul (the windlass rope, stretched toward the arm), winch (drum and crank),
    trigger (the pawl and pin), carry (the ball he lifts from the heap) and props (the heap, mat and pots: still)."""
    h0, h1 = haul_start(), haul_point(COCK)
    up = arm_up(COCK)
    return [
        ("frame", KICK_P, KICK_P + v3((0, 0.4, 0)), None),
        ("arm", AXLE, AXLE + arm_dir(COCK) * 0.6, "frame"),
        ("stone", ball_c(COCK), ball_c(COCK) + up * 0.15, "arm"),
        ("haul", h0, h1, "frame"),
        ("winch", v3((MX + BW, DRUM[1], DRUM[2])), v3((CRANK_X, DRUM[1], DRUM[2])), "frame"),
        ("trigger", PAWL_P, pawl_tip(), "frame"),
        ("carry", CARRY_C, CARRY_C + v3((0, 0, 0.15)), None),
        ("props", PILE, PILE + v3((0, 0, 0.3)), None),
    ]


def _rigid_by(ob, fn):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {fn(np.array(v.co)): 1.0})


def stones_weights(ob, skin_ob, arm):
    """Each ball (mesh island) goes rigidly to the bone of the ball whose centre is nearest its own centre."""
    import bmesh
    cs = stone_centres()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    seen, groups = set(), {}
    for v0 in bm.verts:
        if v0.index in seen:
            continue
        stack, isl = [v0], []
        seen.add(v0.index)
        while stack:
            v = stack.pop()
            isl.append(v.index)
            for e in v.link_edges:
                w = e.other_vert(v)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
        cen = np.mean([np.array(bm.verts[i].co) for i in isl], axis=0)
        bone = min(cs, key=lambda c: np.linalg.norm(cen - c[0]))[1]
        for i in isl:
            _blend_add(ob, groups, i, {bone: 1.0})
    bm.free()


def bronze_weights(ob, skin_ob, arm):
    """Armlets ride the upper arms, the belt plate the belly, the rosette the head."""
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z > 1.55:
            w = {"head": 1.0}
        elif abs(p.x) > 0.3:
            w = {"upperarm.R" if p.x < 0 else "upperarm.L": 1.0}
        else:
            w = {"spine": 0.7, "root": 0.3}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Beard": ("rigid", "head"), "Band": ("rigid", "head"),
        "Tunic": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L"},
                  {"thigh.R": 0.45, "thigh.L": 0.45, "upperarm.R": 0.85, "upperarm.L": 0.85}),
        "Leather": ("transfer", TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Bronze": ("custom", bronze_weights), "Mallet": ("rigid", "hand.R"),
        "Frame": ("rigid", "frame"), "Arm": ("rigid", "arm"), "Winch": ("rigid", "winch"), "Trigger": ("rigid", "trigger"),
        "Haul": ("rigid", "haul"), "Stones": ("custom", stones_weights), "Pots": ("rigid", "props"), "Mat": ("rigid", "props"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.8
    if part in ("Frame", "Winch", "Mat", "Pots"):
        return 0.72
    if part in ("Arm", "Stones", "Trigger", "Haul"):
        return 0.85
    if part == "Mallet":
        return 0.9
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Beard", beard_field(), 0.0022 if fine else 0.0032),
        ("Band", band_field(), 0.002 if fine else 0.003),
        ("Tunic", tunic_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Bronze", bronze_field(), 0.0022 if fine else 0.0028),
        ("Mallet", mallet_field(), 0.002 if fine else 0.003),
        ("Frame", frame_field(), 0.0036 if fine else 0.005),
        ("Arm", arm_field(), 0.003 if fine else 0.0042),
        ("Winch", winch_field(), 0.0026 if fine else 0.0036),
        ("Trigger", trigger_field(), 0.0018 if fine else 0.0026),
        ("Haul", haul_field(), 0.0016 if fine else 0.0022),
        ("Stones", stones_field(), 0.0026 if fine else 0.0036),
        ("Pots", pots_field(), 0.0026 if fine else 0.0036),
        ("Mat", mat_field(), 0.0022 if fine else 0.003),
    ]
