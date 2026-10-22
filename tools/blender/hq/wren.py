"""Wren the Bowmistress, Forest Archer (HQ hero, Medieval Age). Rest pose = A-pose, facing -Y, feet at z = 0; right
side = -X.

A lithe young woman of the greenwood: level brows, clear green eyes, a small sure smile. Honey-blonde hair parted in the
middle and swept back over her ears, a loose lock by each cheek, plaited at her nape into one long braid down her back.
A capuchon of bright forest green with its hood thrown back: a short cape over her shoulders, its hem cut in rounded
leaf dags edged in ochre, a cowl round her throat, the hood bunched behind her neck under the braid. A darker green wool
tunic to mid-thigh with sleeves to her wrists and an ochre trim; over it a brown leather jerkin laced up the front, a
belt with a brass buckle; brown hose; soft boots to below the knee with turned-down cuffs; a leather bracer on her bow
arm, a shooting glove on her draw hand. A yew longbow as tall as she is (pale sapwood on its back, orange heartwood on
its belly, horn nocks, a leather grip); arrows of ash with grey goose fletching, green and red cresting and steel bodkin
heads, carried in a leather quiver on her right hip.

She has Kira's build (kira.py), with Brenna's and the Bronze Archer's way with props: the nocked arrow is on its own
bone ("arrow", child of the drawing hand); each limb of the bow is two bones (inner, outer: children of the bow hand)
that the clips bend as she draws, and the string's two halves are bones on the outer limbs' tips that the clips aim at
the nocking point and stretch, so the string stays two straight lines from the tips to her fingers."""
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
    "neck": (0.0, 0.06, 1.38),
    "head": (0.0, 0.02, 1.5),
    "head_end": (0.0, -0.02, 1.88),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.295, 0.06, 1.36)
    J["elbow_" + _s] = (_x * 0.485, 0.09, 1.11)
    J["wrist_" + _s] = (_x * 0.625, 0.03, 0.88)
    J["hip_" + _s] = (_x * 0.14, 0.04, 0.76)
    J["knee_" + _s] = (_x * 0.155, 0.0, 0.42)
    J["ankle_" + _s] = (_x * 0.165, 0.06, 0.1)
    J["toe_" + _s] = (_x * 0.18, -0.16, 0.03)
J = {k: v3(v) for k, v in J.items()}

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, GLOVE = 0, 1, 2, 3, 4, 5, 8, 9

HS = 1.03
DZ = -0.06
HPIV = v3((0.0, 0.02, 1.46))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


def hinv(P):
    return (P - HPIV.astype(F)) / F(HS) + HPIV.astype(F) - np.array([0, 0, DZ], F)


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.17, 0.184, 0.182)) * HS
EYE_R = hr(0.035)
IRIS = ((0.12, 0.3, 0.1), (0.42, 0.62, 0.22))          # green eyes: the iris's outer ring, its inner ring (prep.paint_eyes)


def eye_c(sx):
    return hp((sx * 0.07, -0.146, 1.676))


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


HAND_S = 0.95
CURLS = {"R": (0.95, 1.05, 0.7), "L": (1.45, 1.6, 1.2)}        # drawing hook / the fist round the bow's grip


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.033


def finger_chains(side, s=HAND_S):
    """The four fingers' joint chains (points, radii) of a hand, index first."""
    wr, f, n, t = hand_frame(side)
    fist = side == "L"
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    out = []
    for i, (o, ls) in enumerate(zip((0.042, 0.014, -0.014, -0.042), (0.97, 1.03, 0.97, 0.82))):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.019 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        out.append((pts, rads))
    return out


def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    fist = side == "L"
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.076 * s
    fd.add(RoundBox(c, v3((0.06, 0.03, 0.064)) * s, 0.028 * s, R=Rp), 0.027, SKIN)
    fd.add(Ellipsoid(c - n * 0.01 + t * 0.03 * s - f * 0.01, v3((0.033, 0.028, 0.05)) * s, R=Rp), 0.018, SKIN)
    curl_ax = norm(np.cross(f, n))
    for i, (pts, rads) in enumerate(finger_chains(side, s)):
        fd.add(Chain(pts, rads, k=0.006), 0.01, SKIN)
        fd.add(Sphere(pts[0] - n * 0.01, 0.014 * s), 0.009, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.01, (0.011, 0.0065, 0.014), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.05 * s + n * 0.01
    if fist:
        d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
        d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:
        d1 = norm(f * 0.5 + t * 0.8 + n * 0.25)
        d2 = norm(f * 0.75 + t * 0.4 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.023 * s, 0.02 * s, 0.017 * s], k=0.008), 0.017, SKIN)
    if side == "R":
        # the shooting glove (painted leather): her first three fingers and the back of the hand, a strap at the wrist
        for pts, rads in finger_chains(side, s)[:3]:
            fd.paint(Chain(pts, [r + 0.004 for r in rads], k=0.006), GLOVE)
        fd.paint(RoundBox(c, v3((0.066, 0.04, 0.07)) * s, 0.03 * s, R=Rp), GLOVE)


def foot(fd, side):
    """A plain foot (it lives in a boot): heel, arch and a rounded toe box, no separate toes."""
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.1)
    fwd = Rz @ v3((0, -1, 0))
    lift = 0.018                     # (the boot's sole, not her heel, stands on the ground)
    fd.add(Sphere(an + v3((0, 0.04, -0.05 + lift)), 0.054), 0.027, SKIN)
    fd.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.068 + lift)), (0.058, 0.12, 0.032), 0.03, R=Rz), 0.03, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.035 + v3((0, 0, -0.03 + lift)), (0.058, 0.08, 0.045), R=Rz), 0.027, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.17 + v3((0, 0, -0.07 + lift)), (0.055, 0.05, 0.03), R=Rz), 0.02, SKIN)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.046, 0.0, 0.0)), 0.022), 0.017, SKIN)


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.06, 1.594), (0.137, 0.13, 0.125)), 0.07, SKIN)                           # an oval jaw
    fd.add(E((0, -0.13, 1.506), (0.07, 0.062, 0.06)), 0.05, SKIN)                             # a small firm chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.106, -0.118, 1.632), 0.04), 0.05, SKIN)                               # cheekbones
        fd.add(S((sx * 0.11, -0.05, 1.566), 0.043), 0.05, SKIN)
        pts = [hp((sx * 0.15, -0.06, 1.744)), hp((sx * 0.115, -0.128, 1.75)), hp((sx * 0.062, -0.162, 1.748))]
        fd.add(Chain(pts, [hr(0.01), hr(0.014), hr(0.012)], k=hr(0.02)), hr(0.03), SKIN)
    # level brows, a touch lower at their inner ends: steady, watchful
    for sx in (-1, 1):
        pts = [hp((sx * 0.034, -0.2, 1.764)), hp((sx * 0.072, -0.195, 1.773)), hp((sx * 0.112, -0.172, 1.774)), hp((sx * 0.148, -0.134, 1.764))]
        fd.add(Chain([p + v3((0, 0.008, 0)) for p in pts], [hr(0.0045), hr(0.0058), hr(0.005), hr(0.0025)], k=hr(0.006)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.011), hr(0.012), hr(0.01), hr(0.006)], k=hr(0.01)), BROW)
    # almond eyes, lashes on the upper lids
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, hr(0.019))), (sx * 0.18, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0042)), Plane(ec + v3((0, 0, -hr(0.026))), (sx * -0.14, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.008)), Plane(ec + v3((0, 0, hr(0.015))), (sx * 0.18, 0.05, -1.0)), hr(0.002)), LASH)
    # a straight nose, a little upturned
    fd.add(RoundCone(hp((0, -0.178, 1.722)), hp((0, -0.212, 1.65)), hr(0.011), hr(0.015)), hr(0.016), SKIN)
    fd.add(S((0, -0.213, 1.638), 0.019), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.022, -0.196, 1.624), 0.013), hr(0.01), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.012, -0.209, 1.613)), v3((0.007, 0.009, 0.005)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a small sure smile: both corners turned up
    slot = [hp((-0.056, -0.164, 1.561)), hp((-0.03, -0.187, 1.547)), hp((0, -0.195, 1.544)), hp((0.03, -0.187, 1.547)),
            hp((0.056, -0.164, 1.561))]
    fd.sub(Chain(slot, [hr(0.0022), hr(0.003), hr(0.0034), hr(0.003), hr(0.0022)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0044), hr(0.0048), hr(0.0044), hr(0.003)], k=hr(0.004)), MOUTH)
    for sx in (-1, 1):
        fd.add(S((sx * 0.062, -0.154, 1.567), 0.011), hr(0.01), SKIN)                          # the smile's cheeks
    up_lip = [(-0.053, -0.162, 1.563), (-0.029, -0.18, 1.555), (-0.008, -0.185, 1.557), (0.008, -0.185, 1.557), (0.029, -0.18, 1.555),
              (0.053, -0.162, 1.563)]
    lo_lip = [(-0.045, -0.165, 1.55), (-0.024, -0.18, 1.536), (0, -0.184, 1.533), (0.024, -0.18, 1.536), (0.045, -0.165, 1.55)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.0038), hr(0.0066), hr(0.007), hr(0.007), hr(0.0066), hr(0.0038)], k=hr(0.006)), hr(0.009), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.0045), hr(0.008), hr(0.0088), hr(0.008), hr(0.0045)], k=hr(0.007)), hr(0.009), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.174, 0.035, 1.66)), v3((0.024, 0.043, 0.054)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)


# ======================================================================================= body (Kira's)
def torso_prims():
    return [
        (Ellipsoid((0, 0.04, 1.14), (0.215, 0.163, 0.22), R=euler(-0.1, 0, 0)), 0.0),
        (Ellipsoid((0, 0.1, 1.19), (0.245, 0.12, 0.17)), 0.05),
        (Ellipsoid((0.078, -0.108, 1.17), (0.082, 0.062, 0.072), R=euler(0.3, 0, 0.2)), 0.04),
        (Ellipsoid((-0.078, -0.108, 1.17), (0.082, 0.062, 0.072), R=euler(0.3, 0, -0.2)), 0.04),
        (Ellipsoid((0, -0.0, 0.95), (0.16, 0.135, 0.15)), 0.07),
        (Ellipsoid((0, 0.04, 0.8), (0.225, 0.165, 0.15)), 0.07),
    ]


def traps():
    return Ellipsoid((0, 0.09, 1.36), (0.195, 0.105, 0.072), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.06, 1.32), hp((0, 0.02, 1.575)), 0.066, hr(0.07))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.02, -0.005, 0.012)), 0.088)


def upper_arm(side):
    return RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.074, 0.056)


def bicep(side):
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    return Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.067, 0.07, 0.102), R=rot_from_axes(z_axis=el - sh))


def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.057, 0.044)


def forearm_bulk(side):
    sx = -1 if side == "R" else 1
    el, wr = J["elbow_" + side], J["wrist_" + side]
    return Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.071, 0.063, 0.11), R=rot_from_axes(z_axis=wr - el))


def thigh_prims(side):
    hip, kn = J["hip_" + side], J["knee_" + side]
    return [(RoundCone(hip, kn, 0.122, 0.076), 0.06),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.02, 0)), (0.112, 0.103, 0.17), R=rot_from_axes(z_axis=kn - hip)), 0.045),
            (Sphere(kn + v3((0, -0.026, 0.0)), 0.06), 0.035)]


def shin_prims(side):
    kn, an = J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(kn, an, 0.074, 0.048), 0.035),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.028, 0)), (0.084, 0.082, 0.13), R=rot_from_axes(z_axis=an - kn)), 0.04)]


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.05, SKIN)
    fd.add(neck_prim(), 0.045, SKIN)
    for side in ("R", "L"):
        el = J["elbow_" + side]
        fd.add(deltoid(side), 0.05, SKIN)
        fd.add(upper_arm(side), 0.045, SKIN)
        fd.add(bicep(side), 0.035, SKIN)
        fd.add(_forearm(side), 0.03, SKIN)
        fd.add(forearm_bulk(side), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.022, 0)), 0.044), 0.025, SKIN)
        hand(fd, side)
        for p, k in thigh_prims(side) + shin_prims(side):
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
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009, -0.17, 1.546)), v3((0.008, 0.006, 0.008)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= hair: parted, swept back, one braid
TIE = hp((0.0, 0.17, 1.6))              # where the hair is gathered and tied, at her nape


def braid_path():
    """The braid's centre line: from the tie at her nape out over the bunched hood, then down her back to the waist."""
    t0 = TIE
    return [t0, t0 + v3((0, 0.05, -0.03)), v3((0.0, 0.29, 1.47)), v3((0.004, 0.322, 1.4)), v3((0.008, 0.318, 1.31)),
            v3((0.01, 0.302, 1.2)), v3((0.008, 0.29, 1.1)), v3((0.0, 0.284, 0.99))]


def braid_at(t):
    path = braid_path()
    n = len(path) - 1
    s = min(int(t * n), n - 1)
    u = t * n - s
    return lerp(path[s], path[s + 1], u), norm(path[s + 1] - path[s])


def braid_width(t):
    return 0.036 - 0.012 * t


def hair_field():
    """Honey-blonde hair parted in the middle and drawn back smooth over the tops of her ears (grooves combed back from
    the parting to the tie), a loose lock falling by each cheek, the knot at her nape and the long three-strand braid."""
    fd = Field("Hair")
    hc, hrad = HEAD_C, HEAD_RAD
    cap = Ellipsoid(hc, hrad + 0.011)
    pfront, pback = hp((0, -0.156, 1.832)), hp((0, 0.215, 1.585))
    slope = (pback[2] - pfront[2]) / (pback[1] - pfront[1])
    hl_n = norm((0, slope, -1.0))
    def hairline(P):
        x = P[:, 0]
        temple = F(0.026) * smoothstep(0.08, 0.15, np.abs(x))
        return ((P - pfront.astype(F)) @ hl_n.astype(F)) + temple + F(0.004) * NOISE(P * F(24))
    def ears(P):                                                              # (the hair covers the tops of her ears)
        Q = hinv(P)
        return np.where((np.abs(Q[:, 0]) > F(0.15)) & (Q[:, 2] < F(1.625)) & (Q[:, 1] < F(0.08)), F(0.02), F(-1.0))
    fd.add(Inter(cap, Func(lambda P: np.maximum(hairline(P), ears(P)), hc - 0.5, hc + 0.5), 0.02), 0.0)
    for sx in (-1, 1):                                                        # the hair swept back over each ear to the tie
        a = hp((sx * 0.158, -0.05, 1.716))
        b = hp((sx * 0.172, 0.05, 1.652))
        c = hp((sx * 0.1, 0.152, 1.6))
        fd.add(Lock([a, b, c, TIE + v3((sx * 0.02, 0, 0))], [hr(0.05), hr(0.052), hr(0.045), hr(0.03)],
                    [hr(0.016), hr(0.02), hr(0.02), hr(0.02)], [v3((sx, 0, 0.2)), v3((sx, 0.2, 0.1)), v3((sx * 0.7, 0.7, 0)), v3((0, 1, 0))],
                    k=hr(0.012)), hr(0.02))
    fd.add(Ellipsoid(TIE + v3((0, 0.016, 0.0)), (0.05, 0.04, 0.042)), hr(0.02))                 # the gathered knot
    # the parting, and grooves combed back from it over the ears to the tie
    part = [hp((0.0, -0.16, 1.83)), hp((0.0, -0.06, 1.9)), hp((0.0, 0.05, 1.905))]
    fd.sub(Chain(part, [hr(0.0045)] * 3, k=0.002), hr(0.003))
    tgt = norm(TIE - hc)
    for sx in (-1, 1):
        for j in range(12):
            u0 = j / 11
            s0 = norm(v3((sx * 0.08, -1.0 + 1.35 * u0, 0.75 + 0.45 * math.sin(math.pi * u0))))
            pts = []
            for k in range(13):
                u = k / 12
                d = norm(s0 * (1 - u) + tgt * u + v3((sx * 0.55 * math.sin(math.pi * u), 0, 0.1 * math.sin(math.pi * u))))
                o = hc + d * 0.5
                h, ok = ray_hit(Func(lambda P: cap(P), hc - 0.5, hc + 0.5), [o], [-d], tmax=0.5)
                if ok[0]:
                    pts.append(h[0] + d * hr(0.001))
            pts = [p for p in pts if hairline(np.array([p], F))[0] < -0.006]
            if len(pts) >= 3:
                fd.sub(Chain(pts, [hr(0.0032)] * len(pts), k=0.003), hr(0.003))
    # a loose lock by each cheek, from the parting's ends in front of the ear down to her jaw, curling in at its end
    for sx in (-1, 1):
        pts = [hp((sx * 0.12, -0.13, 1.79)), hp((sx * 0.16, -0.1, 1.71)), hp((sx * 0.168, -0.09, 1.63)), hp((sx * 0.152, -0.1, 1.56)),
               hp((sx * 0.135, -0.118, 1.52))]
        fd.add(Lock(pts, [hr(0.022), hr(0.02), hr(0.017), hr(0.012), hr(0.005)], [hr(0.009), hr(0.008), hr(0.007), hr(0.006), hr(0.003)],
                    [v3((sx, -0.3, 0.2))] * 5, k=hr(0.006)), hr(0.008))
    # the braid: three-strand plaits as alternating lobes, thinning toward its end, a tuft below the tie
    nseg = 20
    for i in range(1, nseg):
        t0, t1 = i / nseg * 0.96, (i + 1) / nseg * 0.96
        a, _ = braid_at(t0)
        b, _ = braid_at(t1)
        w = braid_width(t0)
        sgn = 1 if i % 2 else -1
        side = norm(np.cross(b - a, v3((0, 1, 0)))) if abs(norm(b - a)[1]) < 0.95 else v3((1, 0, 0))
        mid = (a + b) / 2 + side * sgn * w * 0.32
        fd.add(Ellipsoid(mid, (w, w * 0.72, np.linalg.norm(b - a) * 0.74), R=rot_from_axes(z_axis=norm(b - a + side * sgn * 0.02))), hr(0.006))
    end, d = braid_at(0.96)
    fd.add(Lock([end, end + d * 0.05 + v3((0, 0.004, 0)), end + d * 0.12], [hr(0.028), hr(0.026), hr(0.006)],
                [hr(0.015), hr(0.013), hr(0.004)], [v3((0, 1, 0))] * 3, k=hr(0.006)), hr(0.008))
    return fd


BRAID_TIES = (0.08, 0.955)             # leather ties round the braid (path parameters)


# ======================================================================================= tunic, hose
def tunic_base():
    b = Field("TunicBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(RoundCone((0, 0.035, 0.88), (0, 0.035, 0.52), 0.225, 0.285), 0.08)              # the skirt, flaring a little
    for side in ("R", "L"):
        el = J["elbow_" + side]
        b.add(deltoid(side), 0.05)
        b.add(upper_arm(side), 0.045)
        b.add(bicep(side), 0.035)
        b.add(_forearm(side), 0.03)
        b.add(forearm_bulk(side), 0.035)
        b.add(Sphere(el + v3((0, 0.022, 0)), 0.044), 0.025)
    return b


def tunic_hem(P):
    return F(0.55) + F(0.012) * NOISE(P * F(7))


def _cuff(P, side, back=0.012):
    """Cuts the sleeve at the wrist, square to the forearm."""
    el, wr = J["elbow_" + side], J["wrist_" + side]
    n = norm(wr - el)
    c = wr - n * back
    d = (P - c.astype(F)) @ n.astype(F)
    sx = -1 if side == "R" else 1
    return np.where((P[:, 0] * F(sx) > F(0.3)) & (P[:, 2] > F(0.7)), d, F(-1.0))


def tunic_field():
    """A darker green wool tunic to mid-thigh, its sleeves to her wrists; an ochre woven trim (label 5) at the hem and
    the cuffs. Soft folds down the skirt and round the elbows."""
    fd = Field("Tunic")
    base = tunic_base()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        k = smoothstep(0.86, 0.62, P[:, 2])
        return F(0.0045) * np.sin(a * F(13) + F(0.5) * np.sin(a * F(3))) * k + F(0.0012) * NOISE(P * F(30))
    def keep(P):
        neck = P[:, 2] - F(1.44)
        k = np.maximum(tunic_hem(P) - P[:, 2], neck)
        return np.maximum(np.maximum(k, _cuff(P, "R")), _cuff(P, "L"))
    fd.add(Inter(Shell(base, 0.014, 0.012, pad=0.1, disp=folds, disp_amp=0.005), Func(keep, (-1, -1, 0.4), (1, 1, 1.6)), 0.005), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (tunic_hem(P) + F(0.035)), (-1, -1, 0.4), (1, 1, 0.7)), 5)
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        n = norm(wr - el)
        c = wr - n * 0.012
        fd.paint(Func(lambda P, c=c, n=n: np.where(np.abs(P[:, 0]) > F(0.3), F(-0.035) - (P - c.astype(F)) @ n.astype(F), F(1.0)),
                      c - 0.25, c + 0.25), 5)
    return fd


def leg_base(side):
    b = Field("LegBase" + side)
    for p, k in thigh_prims(side) + shin_prims(side):
        b.add(p, k)
    return b


def hose_field():
    """Brown wool hose from under the tunic's skirt down into the boots."""
    fd = Field("Hose")
    for side in ("R", "L"):
        lb = leg_base(side)
        hip, an = J["hip_" + side], J["ankle_" + side]
        fd.add(Inter(Shell(lb, 0.006, 0.008, pad=0.06, disp=lambda P: F(0.001) * NOISE(P * F(30)), disp_amp=0.0015),
                     Func(lambda P: np.maximum(F(0.26) - P[:, 2], P[:, 2] - F(0.82)), hip - v3((0.25, 0.25, 0.8)), hip + v3((0.25, 0.25, 0.2))), 0.004), 0.0)
    return fd


# ======================================================================================= the capuchon (hood thrown back)
def cape_base():
    b = Field("CapeBase")
    for p, k in torso_prims()[:4]:
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.05)
        b.add(upper_arm(side), 0.045)
        b.add(bicep(side), 0.035)
    b.add(neck_prim(), 0.05)
    return b


CAPE_OFF, CAPE_T = 0.052, 0.014
N_DAGS = 22
DAG_LEN = 0.062


def _cape_angle(P):
    return np.arctan2(P[:, 0], -(P[:, 1] - F(0.05)))


def cape_edge(P):
    """The hem's line (z) before the dags: over her breast in front, a little lower on her back, rising at her sides and
    over her shoulders (the cape caps them, it does not sleeve her arms)."""
    y = P[:, 1]
    a = _cape_angle(P)
    s2 = np.sin(a) ** 2
    z = F(1.2) + F(0.02) * smoothstep(0.05, -0.12, y) - F(0.03) * smoothstep(0.0, 0.18, y) + F(0.075) * s2
    return z + F(0.004) * NOISE(P * F(9))


DAG_GIRTH = 0.27                       # the cape's rough radius round her (sets the dags' width in metres)


def dag_sd(P):
    """< 0 on the cloth: above the hem line, or inside one of the rounded leaf-shaped dags hanging from it."""
    below = cape_edge(P) - P[:, 2]                         # > 0 under the hem line
    u = _cape_angle(P) * F(N_DAGS / (2 * math.pi)) + F(0.5)
    slot = F(2 * math.pi * DAG_GIRTH / N_DAGS)
    x = (u - np.floor(u) - F(0.5)) * slot                  # metres across the dag from its middle
    hw = slot * F(0.42)
    q = np.sqrt((x / hw) ** 2 + (np.maximum(below, F(0)) / F(DAG_LEN)) ** 2)
    tongue = (q - F(1.0)) * np.minimum(hw, F(DAG_LEN))
    return np.minimum(below, tongue)


def cape_top(P):
    """The cowl's upper edge round her throat: low in front, rising behind into the bunched hood. It only cuts round her
    neck: away from it the line climbs clear of the cloth, so the cape caps her shoulders whole (cut level everywhere,
    it opened a hole in the top of each shoulder)."""
    y = P[:, 1]
    lift = F(0.25) * smoothstep(0.13, 0.19, np.abs(P[:, 0]))
    return P[:, 2] - (F(1.445) + F(0.07) * smoothstep(-0.05, 0.14, y) + lift)


def hood_frame():
    base = cape_base()
    h, ok = ray_hit(Func(lambda P: base.eval(P, margin=0.12) - F(CAPE_OFF + CAPE_T / 2), (-1, -1, 0.9), (1, 1, 1.8)),
                    [v3((0.0, 0.8, 1.45))], [v3((0, -1, 0))], tmax=0.9)
    return h[0] if ok[0] else v3((0.0, 0.2, 1.45))


def hood_field():
    """The capuchon of bright forest green: a short cape over her shoulders cut at its hem into rounded leaf dags edged
    in ochre (label 5), a cowl round her throat with a rolled edge, the hood bunched in soft folds behind her neck."""
    fd = Field("Hood")
    base = cape_base()
    cloth = lambda P: (F(0.004) * np.sin(_cape_angle(P) * F(9) + F(0.7)) * smoothstep(1.36, 1.18, P[:, 2]) + F(0.0012) * NOISE(P * F(30)))
    def keep(P):
        return np.maximum(dag_sd(P), cape_top(P))
    shell = Shell(base, CAPE_OFF, CAPE_T, pad=0.12, disp=cloth, disp_amp=0.005)
    fd.add(Inter(shell, Func(keep, (-0.85, -0.6, 0.95), (0.85, 0.6, 1.75)), 0.004), 0.0)
    # the ochre edging along the dags (a band just inside the cut)
    def edging(P):
        return np.abs(dag_sd(P) + F(0.011)) - F(0.008)
    fd.paint(Inter(Func(edging, (-0.85, -0.6, 0.95), (0.85, 0.6, 1.4)), Func(lambda P: P[:, 2] - F(1.3), (-0.85, -0.6, 0.95), (0.85, 0.6, 1.4))), 5)
    # the cowl's rolled edge round her throat (low in front, rising behind), along the cut itself: in each direction,
    # where a level going out from her neck leaves the cloth, the lowest level that is cut away (rays coming in from
    # outside found the tops of her shoulders at the sides)
    pts = []
    zs = np.arange(1.38, 1.62, 0.003)
    rs = np.arange(0.0, 0.35, 0.002)
    for k in range(25):
        a = 2 * math.pi * k / 24
        cols = np.array([0.0, 0.05]) + rs[:, None] * np.array([math.sin(a), -math.cos(a)])[None, :]
        P = np.concatenate([np.tile(cols, (len(zs), 1)), np.repeat(zs, len(rs))[:, None]], 1).astype(F)
        out = ((base.eval(P, margin=0.12) - F(CAPE_OFF + CAPE_T * 0.5)) > 0).reshape(len(zs), len(rs))
        ir = np.argmax(out, 1)
        ok = out.any(1) & (ir > 0)
        ex = np.concatenate([cols[ir], zs[:, None]], 1).astype(F)
        g = cape_top(ex)
        idx = np.flatnonzero(ok[:-1] & ok[1:] & (g[:-1] < 0) & (g[1:] >= 0))
        if len(idx):
            pts.append(v3(ex[idx[0]]) - v3((0, 0, 0.012)))
    if len(pts) > 6:
        fd.add(Chain(pts, [0.016] * len(pts), k=0.008, disp=lambda P: F(0.0015) * NOISE(P * F(40)), disp_amp=0.002), 0.008)
    # the hood itself, thrown back: a thick roll of cloth bunched behind her neck, its opening scooped out on top,
    # a fold or two across it
    hc = hood_frame() + v3((0.0, 0.03, 0.0))
    fd.add(Ellipsoid(hc, (0.15, 0.065, 0.085), R=euler(-0.3, 0, 0), disp=cloth, disp_amp=0.004), 0.03)
    fd.sub(Ellipsoid(hc + v3((0, 0.016, 0.06)), (0.11, 0.042, 0.06), R=euler(-0.3, 0, 0)), 0.02)
    for sx in (-1, 1):
        fd.add(Lock([hc + v3((sx * 0.13, -0.02, 0.0)), hc + v3((sx * 0.07, 0.05, -0.04)), hc + v3((sx * 0.01, 0.06, -0.07))],
                    [0.03, 0.028, 0.018], [0.014, 0.014, 0.01], [v3((0, 1, 0.2))] * 3, k=0.01), 0.012)
    return fd


# ======================================================================================= leather: jerkin, belt, boots, bracer
def jerkin_base():
    b = Field("JerkinBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    return b


JERKIN_OFF, JERKIN_T = 0.036, 0.014
JERKIN_HEM = 0.78
BELT_Z = 0.885
LACE_Z = (0.93, 1.2)


def _jerkin_arm(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    oval = ((y - F(0.06)) / F(0.15)) ** 2 + ((z - F(1.37)) / F(0.21)) ** 2 - F(1.0)
    return np.where(np.abs(x) > F(0.17), -oval * F(0.1), F(-1))


def _jerkin_top(P):
    """A round neck, higher behind; wide straps over the shoulders."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
    neck_z = F(1.44) - F(0.08) * front * np.exp(-(x / F(0.12)) ** 2)
    return np.maximum(z - neck_z, np.where(z > F(1.33), np.abs(np.abs(x) - F(0.14)) - F(0.07), F(-1)))


def _jerkin_open(P):
    """The front opening, laced across."""
    return np.where(P[:, 1] < F(-0.05), F(0.011) - np.abs(P[:, 0]), F(-1.0))


def boot_base(side):
    b = Field("BootBase" + side)
    for p, k in shin_prims(side):
        b.add(p, k)
    foot(b, side)
    return b


BOOT_TOP = 0.35


def leather_field():
    """A brown leather jerkin, sleeveless, laced up the front with a rawhide thong (label 5); a belt with a brass buckle
    (6), its tongue hanging; soft boots to below the knee, the cuff turned down; a bracer laced on her bow arm (5)."""
    fd = Field("Leather")
    base = jerkin_base()
    scuff = lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.0008) * NOISE(P * F(70))
    def keep(P):
        k = np.maximum(F(JERKIN_HEM) + F(0.006) * NOISE(P * F(6)) - P[:, 2], _jerkin_top(P))
        return np.maximum(np.maximum(k, _jerkin_arm(P)), _jerkin_open(P))
    fd.add(Inter(Shell(base, JERKIN_OFF, JERKIN_T, pad=0.12, disp=scuff, disp_amp=0.002), Func(keep, (-0.6, -0.5, 0.7), (0.6, 0.5, 1.55)), 0.004), 0.0)
    # stitched seams down the sides and a rolled edge at the hem (a cord along it)
    fd.add(Inter(Shell(base, JERKIN_OFF + 0.004, 0.012, pad=0.12), Func(lambda P: np.maximum(np.abs(P[:, 2] - F(JERKIN_HEM + 0.008)) - F(0.006), _jerkin_open(P)),
                                                                         (-0.6, -0.5, 0.7), (0.6, 0.5, 0.9)), 0.003), 0.003)
    # the lacing: eyelets each side of the opening, a thong crossing between them
    outer = Func(lambda P: base.eval(P, margin=0.08) - F(JERKIN_OFF + JERKIN_T / 2), (-0.6, -0.6, 0.8), (0.6, 0.6, 1.4))
    zs = np.linspace(LACE_Z[0], LACE_Z[1], 6)
    eye = {}
    for sx in (-1, 1):
        for z in zs:
            h, ok = ray_hit(outer, [v3((sx * 0.024, -0.7, z))], [v3((0, 1, 0))], tmax=0.8)
            if ok[0]:
                eye[(sx, round(float(z), 4))] = h[0]
                fd.add(Torus(h[0] + v3((0, -0.001, 0)), 0.0055, 0.0022, R=rot_from_axes(z_axis=(0, -1, 0))), 0.002, 6)
    for i in range(len(zs) - 1):
        for sx in (-1, 1):
            a, b = eye.get((sx, round(float(zs[i]), 4))), eye.get((-sx, round(float(zs[i + 1]), 4)))
            if a is not None and b is not None:
                mid = (a + b) / 2 + v3((0, -0.006, 0))
                fd.add(Chain([a, mid, b], [0.0032, 0.0036, 0.0032], k=0.002), 0.002, 5)
    # the belt over the jerkin, and its brass buckle a little to her left, the tongue's end hanging
    fd.add(Inter(Shell(base, JERKIN_OFF + 0.017, 0.02, pad=0.12), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(0.021), (-0.6, -0.5, 0.8), (0.6, 0.5, 1.0)), 0.004), 0.004)
    bo = Func(lambda P: base.eval(P, margin=0.1) - F(JERKIN_OFF + 0.03), (-0.6, -0.6, 0.8), (0.6, 0.6, 1.0))
    h, ok = ray_hit(bo, [v3((0.05, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    if ok[0]:
        c = h[0] + v3((0, -0.004, 0))
        R = rot_from_axes(z_axis=(0.15, -1, 0), x_axis=(1, 0, 0))
        fd.add(Inter(RoundBox(c, (0.03, 0.026, 0.006), 0.004, R=R), Func(lambda P, c=c: -(np.maximum(np.abs(P[:, 0] - F(c[0])) - F(0.017), np.abs(P[:, 2] - F(c[2])) - F(0.013))),
                                                                       c - 0.1, c + 0.1), 0.002), 0.002, 6)
        fd.add(RoundCone(c + v3((-0.014, -0.006, 0)), c + v3((0.012, -0.006, 0.0)), 0.0028, 0.0028), 0.002, 6)      # the prong
        fd.add(RoundBox(c + v3((0.045, -0.006, -0.06)), (0.016, 0.004, 0.06), 0.003, R=euler(0, 0, 0.12)), 0.003)
    # boots: a shell round shin and foot to below the knee, the cuff turned down, a sole
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        bb = boot_base(side)
        an = J["ankle_" + side]
        wrinkle = lambda P: F(0.0025) * np.sin(P[:, 2] * F(90)) * smoothstep(0.26, 0.12, P[:, 2]) + F(0.001) * NOISE(P * F(30))
        lo, hi = an - v3((0.15, 0.3, 0.2)), an + v3((0.15, 0.25, 0.4))
        fd.add(Inter(Shell(bb, 0.016, 0.013, pad=0.06, disp=wrinkle, disp_amp=0.003), Func(lambda P: P[:, 2] - F(BOOT_TOP), lo, hi), 0.004), 0.0)
        fd.add(Inter(Shell(bb, 0.028, 0.013, pad=0.06, disp=scuff, disp_amp=0.002),
                     Func(lambda P: np.maximum(np.abs(P[:, 2] - F(BOOT_TOP - 0.035)) - F(0.042), F(0.2) - P[:, 2]), lo, hi), 0.004), 0.003)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.078 + v3((0, 0, -0.094)), (0.066, 0.15, 0.01), 0.008, R=Rz), 0.006, 0)
    # the bracer on her bow arm (left forearm), laced on its inner side
    el, wr = J["elbow_L"], J["wrist_L"]
    ax = norm(wr - el)
    c = lerp(el, wr, 0.62)
    fa = Field("ForearmL")
    fa.add(_forearm("L"), 0.0)
    fa.add(forearm_bulk("L"), 0.035)
    fd.add(Inter(Shell(fa, 0.03, 0.012, pad=0.06, disp=scuff, disp_amp=0.002),
                 Func(lambda P: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.075), c - 0.25, c + 0.25), 0.004), 0.003, 0)
    for j in (-1, 0, 1):
        cc = c + ax * (j * 0.045)
        fd.add(Inter(Shell(fa, 0.038, 0.005, pad=0.06), Func(lambda P, cc=cc: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.0035), cc - 0.2, cc + 0.2), 0.002), 0.002, 5)
    return fd


# ======================================================================================= the longbow
BOW_HALF = 0.8
BRACE = 0.125                 # how far the braced limbs' tips sit back toward her from the grip
LIMB_S = (0.12, 0.56)         # where each limb's inner and outer bones start (fractions of BOW_HALF from the grip)


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
    """A self bow's gentle arc when braced: the limbs sweep back toward her, most toward the tips."""
    a = abs(a)
    return -BRACE * a ** 1.8


def bow_point(s):
    G, A, B, S = bow_frame()
    return G + A * (s * BOW_HALF) + B * bow_back(s)


def bow_tips():
    return bow_point(1.0), bow_point(-1.0)


def string_mid():
    t1, t2 = bow_tips()
    return (t1 + t2) / 2


def bow_field():
    """Yew, D-sectioned: the flat back pale sapwood (label 7), the round belly orange heartwood; thick at the grip,
    tapering to the tips; a leather grip (5) with the arrow pass above it; horn nocks (6)."""
    fd = Field("Bow")
    G, A, B, S = bow_frame()
    ss = np.linspace(-1.0, 1.0, 41)
    pts = [bow_point(s) for s in ss]
    ws = [0.017 - 0.008 * abs(s) ** 1.3 for s in ss]                    # half width (across, along S)
    ts = [0.016 - 0.008 * min(1.0, abs(s) * 1.25) for s in ss]          # half thickness (back to belly)
    grain = lambda P: F(0.0006) * NOISE(P * np.array([90, 90, 90], F))
    fd.add(Lock(pts, ws, ts, [B] * len(pts), k=0.003, disp=grain, disp_amp=0.001), 0.0)
    # the grip: thicker, wrapped in leather
    fd.add(Ellipsoid(G, (0.021, 0.024, 0.075), R=rot_from_axes(z_axis=A, y_axis=B)), 0.01)
    for s in (1.0, -1.0):
        tp = bow_point(s)
        d = norm(bow_point(s) - bow_point(s * 0.94))
        fd.add(RoundCone(tp - d * 0.05, tp + d * 0.018, 0.011, 0.006), 0.004)                # horn nock
    def along(P):
        return ((P - G.astype(F)) @ A.astype(F)) / F(BOW_HALF)
    fd.paint(Func(lambda P: np.abs(along(P) + F(0.01)) - F(0.085), G - 0.3, G + 0.3), 5)
    fd.paint(Func(lambda P: F(0.93) - np.abs(along(P)), G - 1.0, G + 1.0), 6)
    def back_side(P):
        s = np.clip(along(P), -1, 1)
        lb = (P - G.astype(F)) @ B.astype(F) - F(-BRACE) * np.abs(s) ** F(1.8)
        return np.maximum(-lb + F(0.002), np.maximum(np.abs(along(P)) - F(0.93), F(0.1) - np.abs(along(P))))
    fd.paint(Func(back_side, G - 1.0, G + 1.0), 7)
    return fd


def string_field():
    fd = Field("String")
    t1, t2 = bow_tips()
    fd.add(Chain([t1, string_mid(), t2], [0.0042, 0.0042, 0.0042], k=0.002), 0.0)
    return fd


def draw_point():
    """Where the string sits in the right hand's hooked fingers (rest pose)."""
    wr, f, n, t = hand_frame("R")
    return wr + f * 0.152 * HAND_S + n * 0.026


ARROW_LEN = 0.8


def arrow_axis():
    wr, f, n, t = hand_frame("R")
    return draw_point(), norm(t)


def _arrow(fd, nock, ax, up, label_head=6, label_fl=8, label_shaft=0, label_crest=5, shaft_r=0.0078, full=True, length=ARROW_LEN):
    """One arrow from its nock along `ax`: an ash shaft, a steel bodkin head, three goose-feather vanes (chunky enough to
    read at game scale), painted cresting bands (label 5) in front of the fletching."""
    side = norm(np.cross(ax, up))
    up = np.cross(side, ax)
    tip = nock + ax * length
    if full:
        fd.add(Chain([nock + ax * 0.01, tip - ax * 0.05], [shaft_r, shaft_r], k=0.002), 0.0, label_shaft)
        fd.add(RoundCone(tip - ax * 0.062, tip, 0.0105, 0.0016), 0.004, label_head)              # the bodkin: a long square point
        fd.add(Cylinder(tip - ax * 0.07, shaft_r + 0.0018, 0.014, rr=0.002, R=rot_from_axes(z_axis=ax)), 0.002, label_head)
    fd.add(Cylinder(nock + ax * 0.01, shaft_r + 0.002, 0.022, rr=0.003, R=rot_from_axes(z_axis=ax)), 0.002, label_shaft)
    for j in range(3):
        ang = j * 2 * math.pi / 3 + 0.4
        vd = side * math.cos(ang) + up * math.sin(ang)
        c = nock + ax * 0.095 + vd * 0.015
        fd.add(Ellipsoid(c, (0.0024, 0.017, 0.065), R=rot_from_axes(z_axis=ax, y_axis=vd)), 0.002, label_fl)
    for k, (u, w) in enumerate(((0.19, 0.007), (0.215, 0.004))):
        c = nock + ax * u
        fd.paint(Cylinder(c, shaft_r + 0.004, w, R=rot_from_axes(z_axis=ax)), label_crest if k == 0 else 9)


def arrows_field():
    """The arrow on the string: ash (label 0), a steel bodkin (6), grey and white goose fletching (8), cresting (5, 9)."""
    fd = Field("Arrows")
    p0, ax = arrow_axis()
    wr, f, n, t = hand_frame("R")
    up = norm(np.cross(ax, n))
    _arrow(fd, p0, ax, up)
    return fd


# ======================================================================================= quiver (on her right hip)
Q_TOP = v3((-0.335, -0.115, 0.95))       # the mouth, forward and up at her hip
Q_BOT = v3((-0.36, 0.17, 0.56))
Q_R = (0.046, 0.054)                     # radius at the bottom, at the mouth


def quiver_axis():
    return norm(Q_TOP - Q_BOT)


def quiver_field():
    """Brown leather quiver hanging from her belt on her right hip, mouth forward and up: green-dyed bands (label 5), a
    brass rim (6), a strap up to the belt; a sheaf of arrows in it, the fletching (8) and cresting showing above the
    mouth, the ash shafts (7)."""
    fd = Field("Quiver")
    ax = quiver_axis()
    grain = lambda P: F(0.0012) * NOISE(P * F(40))
    fd.add(RoundCone(Q_BOT, Q_TOP, Q_R[0], Q_R[1], disp=grain, disp_amp=0.002), 0.0)
    fd.add(Sphere(Q_BOT - ax * 0.008, Q_R[0] * 1.02), 0.02)
    fd.sub(RoundCone(Q_TOP - ax * 0.07, Q_TOP + ax * 0.05, Q_R[1] - 0.005, Q_R[1] - 0.002), 0.005)        # its open mouth
    fd.add(Torus(Q_TOP - ax * 0.006, Q_R[1] + 0.001, 0.0075, R=rot_from_axes(z_axis=ax)), 0.004, 6)
    for u in (0.2, 0.62):
        c = lerp(Q_BOT, Q_TOP, u)
        fd.add(Torus(c, Q_R[0] + (Q_R[1] - Q_R[0]) * u + 0.002, 0.0075, R=rot_from_axes(z_axis=ax)), 0.004, 5)
    # the strap: from the rim up to the belt behind her hip
    belt = v3((-0.255, 0.03, BELT_Z))
    s0 = Q_TOP - ax * 0.03 + v3((0.0, 0.02, 0.0))
    fd.add(Chain([s0, lerp(s0, belt, 0.5) + v3((-0.012, 0, 0.01)), belt], [0.007, 0.007, 0.007], k=0.003), 0.003)
    up = norm(np.cross(ax, v3((1, 0, 0))))
    side = norm(np.cross(ax, up))
    rs = np.random.RandomState(13)
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.2
        r = 0.026 if k else 0.0
        o = Q_TOP - ax * 0.04 + (side * math.cos(a) + up * math.sin(a)) * r
        d = norm(ax + (side * math.cos(a) + up * math.sin(a)) * 0.1 + rs.normal(0, 0.025, 3))
        nock = o + d * (0.15 + rs.uniform(0, 0.03))
        fd.add(Chain([o, nock - d * 0.01], [0.0062, 0.0062], k=0.002), 0.002, 7)
        _arrow(fd, nock, -d, up, label_fl=8, label_shaft=7, full=False)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.232, 1.622)), 0.045, 0.45)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.1, -0.15, 1.6)), 0.06, 0.5), (hp((sx * 0.174, 0.035, 1.66)), 0.05, 0.5)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.01, 0.028, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "wren"
ROOT_NAME = "HeroWrenHQ"
TEX_PREFIX = "hero"
MAT_NAME = "WrenMat"
MESH_NAME = "Wren"
BASE_MODULE = "wren_base"
ANIM_MODULE = "anim_wren"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Hood", "Tunic", "Hose", "Leather", "Bow", "String", "Arrows", "Quiver"]
REGION_PARTS = ("Skin", "Hood", "Tunic", "Leather", "Bow", "Arrows", "Quiver")
FOREST = (0.24, 0.46, 0.15)             # the capuchon's bright forest green
TUNIC_C = (0.12, 0.27, 0.12)
OCHRE = (0.86, 0.62, 0.22)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_WrenSkin", "base": (0.86, 0.64, 0.5), "ruddy": (0.88, 0.5, 0.42), "lips": (0.74, 0.4, 0.38),
                      "brow": ((0.36, 0.25, 0.13), (0.5, 0.36, 0.2)),
                      "extra": ((LASH, (0.16, 0.1, 0.06), 0.5), (GLOVE, (0.4, 0.24, 0.12), 0.7))}),
    "Hair": ("hair", {"name": "HQ_WrenHair", "base": (0.64, 0.46, 0.22), "hi": (0.95, 0.82, 0.54), "low": (0.33, 0.21, 0.09),
                      "streak": (0.78, 0.6, 0.32), "tint": (0.58, 0.4, 0.18)}),
    "Hood": ("wool", {"name": "HQ_WrenHood", "base": FOREST, "border": OCHRE, "stripe": OCHRE}),
    "Tunic": ("wool", {"name": "HQ_WrenTunic", "base": TUNIC_C, "border": OCHRE, "stripe": OCHRE}),
    "Hose": ("wool", {"name": "HQ_WrenHose", "base": (0.3, 0.2, 0.12)}),
    "Leather": ("leather_dyed", {"name": "HQ_WrenLeather", "base": (0.4, 0.24, 0.12), "dyed": (0.66, 0.52, 0.34)}),
    "Bow": ("yew_bow", {"name": "HQ_Longbow"}),
    "String": ("cord", {}),
    "Arrows": ("arrows", {"name": "HQ_WrenArrows", "head": (0.5, 0.52, 0.56), "head_hi": (0.82, 0.84, 0.88), "head_rough": 0.34,
                          "shaft": ((0.8, 0.68, 0.48), (0.66, 0.54, 0.36)),
                          "fletch": ((0.56, 0.56, 0.58), (0.95, 0.94, 0.9)), "crest": (0.16, 0.42, 0.14), "crest2": (0.72, 0.12, 0.08)}),
    "Quiver": ("quiver", {"name": "HQ_WrenQuiver", "base": (0.36, 0.21, 0.11), "band": (0.2, 0.4, 0.15), "rim": (0.86, 0.66, 0.32),
                          "shaft": (0.8, 0.68, 0.48), "fletch": ((0.56, 0.56, 0.58), (0.95, 0.94, 0.9)),
                          "worn": (0.6, 0.42, 0.26), "scratch": (0.14, 0.08, 0.04)}),
}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Hair": 2600, "Hood": 2000, "Tunic": 2600, "Hose": 700, "Leather": 2800,
               "Bow": 1000, "String": 120, "Arrows": 260, "Quiver": 1300}
AO_EXCLUDE = ["Bow", "String", "Arrows"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.74, 0.9, 1.06, 1.42)


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.9), (0, 0.045, 1.1)),
        "chest": ((0, 0.045, 1.1), (0, 0.06, 1.33)),
        "neck": ((0, 0.06, 1.33), hp((0, 0.02, 1.56))),
        "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.34,
    }


def prop_bones():
    p0, ax = arrow_axis()
    return [("arrow", p0, p0 + ax * 0.3, "hand.R")]


def extra_bones():
    """The bow's limbs (inner and outer bone each, so they bend in an arc), and the string's halves on the tips."""
    out = []
    for nm, sg in (("top", 1.0), ("bot", -1.0)):
        a, b = bow_point(sg * LIMB_S[0]), bow_point(sg * LIMB_S[1])
        out.append(("limb_" + nm, a, b, "hand.L"))
        out.append(("limb_" + nm + "2", b, bow_point(sg), "limb_" + nm))
    t1, t2 = bow_tips()
    m = string_mid()
    out += [("string_top", t1, m, "limb_top2"), ("string_bot", t2, m, "limb_bot2")]
    return out


def _limb_w(s):
    """Bone weights of a point of the bow at s (-1..1 along it, from the grip)."""
    a = abs(s)
    nm = "top" if s > 0 else "bot"
    def ss(e0, e1, x):
        t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
        return t * t * (3 - 2 * t)
    k1 = ss(LIMB_S[0] - 0.06, LIMB_S[0] + 0.08, a)          # grip -> inner limb
    k2 = ss(LIMB_S[1] - 0.1, LIMB_S[1] + 0.1, a)            # inner -> outer
    w = {"hand.L": 1.0 - k1, "limb_" + nm: k1 * (1.0 - k2), "limb_" + nm + "2": k1 * k2}
    return {k: v for k, v in w.items() if v > 0.004}


def bow_weights(ob, skin_ob, arm):
    G, A, B, S = bow_frame()
    groups = {}
    for v in ob.data.vertices:
        s = float((np.array(v.co) - G) @ A) / BOW_HALF
        _blend_add(ob, groups, v.index, _limb_w(s))


def string_weights(ob, skin_ob, arm):
    G, A, B, S = bow_frame()
    groups = {}
    for v in ob.data.vertices:
        top = float((np.array(v.co) - G) @ A) > 0
        _blend_add(ob, groups, v.index, {"string_top" if top else "string_bot": 1.0})


def _braid_weight(p):
    z1, z0 = hp((0, 0, 1.6))[2], 1.0
    t = max(0.0, min(1.0, (z1 - p.z) / (z1 - z0)))
    return {"head": 1.0 - 0.75 * t, "neck": 0.3 * t, "chest": 0.45 * t, "spine": 0.2 * t}


def hair_weights(ob, skin_ob, arm):
    """The hair on her head rides the head; the braid down her back blends to the neck and chest as it falls."""
    groups = {}
    z1 = hp((0, 0, 1.6))[2]
    for v in ob.data.vertices:
        p = v.co
        if p.z < z1 and p.y > 0.12:
            _blend_add(ob, groups, v.index, _braid_weight(p))
        else:
            _blend_add(ob, groups, v.index, {"head": 1.0})


def hood_weights(ob, skin_ob, arm):
    """The cape rides the chest and shoulders (a little of each upper arm over the shoulder), the cowl and the bunched
    hood the neck and chest."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"},
                         caps={"upperarm.R": 0.45, "upperarm.L": 0.45, "neck": 0.5})


def leather_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L",
                                                       "forearm.L", "hand.L"},
                         caps={"thigh.R": 0.35, "thigh.L": 0.35})
    groups = {}
    el, wr = J["elbow_L"], J["wrist_L"]
    for v in ob.data.vertices:
        p = np.array(v.co)
        w = None
        if p[0] > 0.4 and _seg_dist(p, el, wr) < 0.11:                    # the bracer: rigid on the forearm
            w = {"forearm.L": 1.0}
        elif p[2] < BOOT_TOP + 0.03:                                       # the boots: shin and foot only
            side = "R" if p[0] < 0 else "L"
            an = J["ankle_" + side]
            if p[2] > an[2] + 0.04:
                w = {"shin." + side: 1.0}
            else:
                k = max(0.0, min(1.0, (an[1] - p[1]) / 0.12))
                w = {"shin." + side: 1.0 - k, "foot." + side: k}
        if w is not None:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, w)


def quiver_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"root": 1.0})


def _seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
    return float(np.linalg.norm(a + ab * t - p))


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Hood": ("custom", hood_weights),
        "Tunic": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L", "hand.R", "hand.L",
                                       "thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Hose": ("transfer", {"root", "thigh.R", "thigh.L", "shin.R", "shin.L"}, {}),
        "Leather": ("custom", leather_weights),
        "Bow": ("custom", bow_weights), "String": ("custom", string_weights), "Arrows": ("rigid", "arrow"),
        "Quiver": ("custom", quiver_weights),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("String", "Arrows"):
        return 0.6
    if part == "Bow":
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Hood", hood_field(), 0.0026 if fine else 0.0036),
        ("Tunic", tunic_field(), 0.0026 if fine else 0.0036),
        ("Hose", hose_field(), 0.0028 if fine else 0.0038),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Bow", bow_field(), 0.0016 if fine else 0.0022),
        ("String", string_field(), 0.0012 if fine else 0.0016),
        ("Arrows", arrows_field(), 0.0012 if fine else 0.0016),
        ("Quiver", quiver_field(), 0.002 if fine else 0.0028),
    ]
