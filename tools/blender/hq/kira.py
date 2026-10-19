"""Kira Sunblade, Bronze Duelist (HQ hero). Rest pose = A-pose, facing -Y, feet at z=0; right side = -X.

A lithe, athletic young swordswoman of a river city: a confident half-smile, arched brows, almond eyes lined with kohl
drawn out in wings, a gold stripe painted along each cheekbone. Black hair pulled back hard into a high ponytail, braided
and bound with gold rings, falling down her back. A gold diadem with a sun disc on her brow, gold hoop earrings. A molded
bronze bodice with a sun embossed between the breasts and a rolled rim, one bronze guard on her sword shoulder, bronze
bracers; a short pleated white linen kilt with a red border and a blue stripe, red leather strips hanging over it from
a studded belt; sandals laced up her calves. In her right fist a bronze khopesh: a sickle sword whose blade curves out
from a straight shank, its sun-stone pommel glowing (its own mesh, on the `gem` bone).

The sword is rigid in her right fist ("frame" aims in anim_kira.py: the sword along the fist's thumb axis, its edge
along the knuckles)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, grad, project_to, flow_line, Stone, lerp
from ugo import stripe2d, bez3, _blend_add

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

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, KOHL = 0, 1, 2, 3, 4, 5, 8, 9

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
EYE_R = hr(0.037)


def eye_c(sx):
    return hp((sx * 0.07, -0.146, 1.676))


def hstripe(a, b, ra, rb, y0=-0.4, y1=0.02):
    m = lambda q: (q[0] * HS, HPIV[2] + (q[1] + DZ - HPIV[2]) * HS)
    return stripe2d(m(a), m(b), ra * HS, rb * HS, y0=y0, y1=y1)


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
CURLS = {"R": (1.45, 1.6, 1.2), "L": (0.2, 0.32, 0.22)}       # right fist round the sword's grip, left hand open


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.033


def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    fist = side == "R"
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.076 * s
    fd.add(RoundBox(c, v3((0.06, 0.03, 0.064)) * s, 0.028 * s, R=Rp), 0.027, SKIN)
    fd.add(Ellipsoid(c - n * 0.01 + t * 0.03 * s - f * 0.01, v3((0.033, 0.028, 0.05)) * s, R=Rp), 0.018, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.042, 0.014, -0.014, -0.042)
    lens = (0.97, 1.03, 0.97, 0.82)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * (1.2 if fist else 2.6))
        pts, rads = [p], [0.019 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
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
        d1 = norm(f * 0.45 + t * 0.85 + n * 0.2)
        d2 = norm(f * 0.75 + t * 0.45 + n * 0.35)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.023 * s, 0.02 * s, 0.017 * s], k=0.008), 0.017, SKIN)


def foot(fd, side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.1)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    fd.add(Sphere(an + v3((0, 0.04, -0.05)), 0.054), 0.027, SKIN)
    fd.add(RoundBox(an + fwd * 0.072 + v3((0, 0, -0.068)), (0.06, 0.11, 0.033), 0.03, R=Rz), 0.03, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.035 + v3((0, 0, -0.03)), (0.058, 0.08, 0.045), R=Rz), 0.027, SKIN)
    inner = -sx
    for i, (o, r) in enumerate(((0.046, 0.025), (0.019, 0.019), (-0.005, 0.017), (-0.026, 0.015), (-0.044, 0.014))):
        base = an + fwd * (0.156 - 0.011 * i - (0.0 if i else -0.004)) + rgt * (o * inner) + v3((0, 0, -0.08))
        tip = base + fwd * (0.027 + r * 0.4) + v3((0, 0, -0.004))
        base[2] = 0.023 + r * 0.55
        tip[2] = 0.018 + r * 0.5
        fd.add(RoundCone(base, tip, r, r * 0.92), 0.011, SKIN)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.046, 0.0, 0.0)), 0.022), 0.017, SKIN)


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.06, 1.592), (0.145, 0.133, 0.128)), 0.07, SKIN)                           # a neat oval jaw
    fd.add(E((0, -0.13, 1.506), (0.072, 0.064, 0.062)), 0.05, SKIN)                           # a firm little chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.11, -0.114, 1.632), 0.045), 0.05, SKIN)                               # high cheekbones
        fd.add(S((sx * 0.12, -0.05, 1.56), 0.05), 0.05, SKIN)
        pts = [hp((sx * 0.15, -0.06, 1.744)), hp((sx * 0.115, -0.128, 1.75)), hp((sx * 0.062, -0.162, 1.748))]
        fd.add(Chain(pts, [hr(0.01), hr(0.014), hr(0.012)], k=hr(0.02)), hr(0.03), SKIN)
    # arched brows, a little raised at their outer ends: confident, amused
    for sx in (-1, 1):
        pts = [hp((sx * 0.03, -0.203, 1.762)), hp((sx * 0.07, -0.196, 1.776)), hp((sx * 0.112, -0.172, 1.781)), hp((sx * 0.15, -0.132, 1.771))]
        fd.add(Chain([p + v3((0, 0.007, 0)) for p in pts], [hr(0.006), hr(0.0075), hr(0.0065), hr(0.003)], k=hr(0.006)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.013), hr(0.015), hr(0.013), hr(0.007)], k=hr(0.01)), BROW)
    # almond eyes, lashes on the upper lids, kohl drawn out in wings
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, hr(0.025))), (sx * 0.22, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0045)), Plane(ec + v3((0, 0, -hr(0.028))), (sx * -0.14, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.008)), Plane(ec + v3((0, 0, hr(0.021))), (sx * 0.22, 0.05, -1.0)), hr(0.002)), LASH)
        flick = ec + v3((sx * hr(0.044), -hr(0.012), hr(0.014)))
        fd.add(RoundCone(flick, flick + v3((sx * hr(0.024), hr(0.008), hr(0.009))), hr(0.005), hr(0.0015)), hr(0.004), LASH)
        k0 = hp((sx * 0.032, -0.17, 1.664))
        k1 = hp((sx * 0.07, -0.186, 1.656))
        k2 = hp((sx * 0.112, -0.163, 1.664))
        k3 = hp((sx * 0.158, -0.122, 1.69))
        fd.paint(Chain([k0, k1, k2, k3], [hr(0.006), hr(0.008), hr(0.007), hr(0.0035)], k=hr(0.006)), KOHL)
    # a straight, slightly upturned nose
    fd.add(RoundCone(hp((0, -0.178, 1.722)), hp((0, -0.222, 1.64)), hr(0.013), hr(0.018)), hr(0.016), SKIN)
    fd.add(S((0, -0.224, 1.628), 0.023), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.025, -0.204, 1.614), 0.016), hr(0.011), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.013, -0.219, 1.602)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a confident half-smile: the left corner (her left, +X) drawn up
    slot = [hp((-0.056, -0.165, 1.556)), hp((-0.029, -0.188, 1.544)), hp((0, -0.195, 1.542)), hp((0.03, -0.186, 1.548)),
            hp((0.06, -0.16, 1.566))]
    fd.sub(Chain(slot, [hr(0.0022), hr(0.003), hr(0.0034), hr(0.003), hr(0.0024)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0044), hr(0.0048), hr(0.0044), hr(0.0034)], k=hr(0.004)), MOUTH)
    fd.add(S((0.066, -0.155, 1.566), 0.012), hr(0.01), SKIN)                                   # her dimple's cheek
    up_lip = [(-0.054, -0.162, 1.558), (-0.028, -0.18, 1.552), (-0.008, -0.185, 1.555), (0.008, -0.185, 1.556), (0.03, -0.179, 1.556), (0.058, -0.158, 1.567)]
    lo_lip = [(-0.046, -0.164, 1.546), (-0.025, -0.18, 1.533), (0, -0.184, 1.531), (0.026, -0.179, 1.536), (0.05, -0.16, 1.552)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.0038), hr(0.0068), hr(0.0072), hr(0.0072), hr(0.0066), hr(0.0038)], k=hr(0.006)), hr(0.009), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.0045), hr(0.0082), hr(0.009), hr(0.0082), hr(0.0045)], k=hr(0.007)), hr(0.009), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.174, 0.035, 1.66)), v3((0.024, 0.043, 0.054)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
    # a gold stripe along each cheekbone (painted)
    for sx in (-1, 1):
        fd.paint(hstripe((sx * 0.07, 1.632), (sx * 0.142, 1.645), 0.008, 0.005, y0=-0.5, y1=-0.04), PAINT)


# ======================================================================================= body (lithe, athletic)
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


def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.057, 0.044)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.05, SKIN)
    fd.add(neck_prim(), 0.045, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.05, SKIN)
        fd.add(upper_arm(side), 0.045, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.067, 0.07, 0.102), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(_forearm(side), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.071, 0.063, 0.11), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.022, 0)), 0.044), 0.025, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.122, 0.076), 0.06, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.02, 0)), (0.112, 0.103, 0.17), R=rot_from_axes(z_axis=kn - hip)), 0.045, SKIN)
        fd.add(Sphere(kn + v3((0, -0.026, 0.0)), 0.06), 0.035, SKIN)
        fd.add(RoundCone(kn, an, 0.074, 0.048), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.028, 0)), (0.084, 0.082, 0.13), R=rot_from_axes(z_axis=an - kn)), 0.04, SKIN)
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


# ======================================================================================= hair: a high braided ponytail
TIE = hp((0.0, 0.122, 1.905))           # where the hair is gathered and tied, high on the back of her head


def tail_path():
    """The ponytail's centre line: up and back from the tie, then down her back to the waist."""
    t0 = TIE
    return [t0, t0 + v3((0, 0.06, 0.035)), t0 + v3((0, 0.14, -0.03)), v3((0.0, 0.3, 1.66)), v3((0.01, 0.3, 1.5)),
            v3((0.012, 0.282, 1.34)), v3((0.008, 0.268, 1.19)), v3((0.0, 0.258, 1.06))]


def tail_at(t):
    path = tail_path()
    n = len(path) - 1
    s = min(int(t * n), n - 1)
    u = t * n - s
    return lerp(path[s], path[s + 1], u), norm(path[s + 1] - path[s])


def hair_field(seed=5):
    """Black hair pulled back hard from a clean hairline to the tie (grooves running to it), the gathered knot, the
    braided tail down her back ending in a loose tuft."""
    rng = np.random.RandomState(seed)
    fd = Field("Hair")
    hc, hrad = HEAD_C, HEAD_RAD
    pfront, pback = hp((0, -0.156, 1.832)), hp((0, 0.215, 1.6))
    slope = (pback[2] - pfront[2]) / (pback[1] - pfront[1])
    hl_n = norm((0, slope, -1.0))
    hairline = Func(lambda P: ((P - pfront.astype(F)) @ hl_n.astype(F)) + F(0.004) * NOISE(P * F(24)), hc - 0.5, hc + 0.5)
    cap = Ellipsoid(hc, hrad + 0.011)
    fd.add(Inter(cap, hairline, 0.02), 0.0)
    # the hair drawn tight toward the tie: grooves along great circles from the hairline to it
    tdir = norm(TIE - hc)
    for j in range(22):
        a = -math.pi * 0.92 + 1.84 * math.pi * j / 21
        start_dir = norm(v3((math.sin(a) * 1.0, -math.cos(a) * 1.0, -0.1)))
        if start_dir[1] > 0.55:                                    # (round the back: the nape is drawn up too)
            start_dir = norm(start_dir + v3((0, 0, -0.35)))
        pts = []
        for k in range(14):
            u = k / 13
            d = norm(start_dir * (1 - u) + tdir * u + v3((0, 0, 0.25 * math.sin(u * math.pi))))
            o = hc + d * 0.5
            h, ok = ray_hit(Func(lambda P: cap(P) - F(0.0), hc - 0.5, hc + 0.5), [o], [-d], tmax=0.5)
            if ok[0]:
                pts.append(h[0] + d * hr(0.001))
        if len(pts) >= 4:
            pts = [p for p in pts if hairline(np.array([p], F))[0] < -0.004]
            if len(pts) >= 3:
                fd.sub(Chain(pts, [hr(0.0034)] * len(pts), k=0.003), hr(0.003))
    # the gathered knot under the tie
    fd.add(Ellipsoid(TIE + v3((0, 0.022, 0.006)), (0.05, 0.05, 0.044)), hr(0.02))
    # the braid: three-strand plaits as alternating lobes, thinning toward its end
    nseg = 18
    for i in range(1, nseg):
        t0, t1 = i / nseg * 0.97, (i + 1) / nseg * 0.97
        a, da = tail_at(t0)
        b, _ = tail_at(t1)
        w = 0.042 - 0.014 * t0
        sgn = 1 if i % 2 else -1
        side = norm(np.cross(b - a, v3((0, 1, 0)))) if abs(norm(b - a)[1]) < 0.95 else v3((1, 0, 0))
        mid = (a + b) / 2 + side * sgn * w * 0.32
        fd.add(Ellipsoid(mid, (w, w * 0.72, np.linalg.norm(b - a) * 0.74), R=rot_from_axes(z_axis=norm(b - a + side * sgn * 0.02))), hr(0.006))
    end, d = tail_at(0.97)
    fd.add(Lock([end, end + d * 0.05 + v3((0, 0.004, 0)), end + d * 0.12], [hr(0.03), hr(0.026), hr(0.006)],
                [hr(0.016), hr(0.013), hr(0.004)], [v3((0, 1, 0))] * 3, k=hr(0.006)), hr(0.008))
    return fd


RING_T = (0.03, 0.42, 0.7)              # gold rings round the ponytail (path parameters)


# ======================================================================================= gold: diadem, rings, earrings
DIADEM_N = norm(v3((0, 0.36, 1.0)))
DIADEM_C = HEAD_C + v3((0, -0.006, 0.026))


def diadem_d(P):
    return (P - DIADEM_C.astype(F)) @ DIADEM_N.astype(F) - F(0.062)


def ear_lobe(sx):
    return hp((sx * 0.178, 0.02, 1.612))


def gold_field():
    """A gold diadem over the hairline with a sun disc and rays on her brow, rings round the ponytail, hoop earrings."""
    fd = Field("Gold")
    hull = Ellipsoid(HEAD_C, HEAD_RAD + 0.026)
    fd.add(Inter(Shell(hull, 0.0, 0.011, pad=0.06), Func(lambda P: np.abs(diadem_d(P)) - F(0.011), HEAD_C - 0.4, HEAD_C + 0.4), 0.003), 0.0)
    o = DIADEM_C + DIADEM_N * 0.062 + v3((0, -0.6, 0))
    h, ok = ray_hit(Func(lambda P: hull(P) - F(0.006), HEAD_C - 0.5, HEAD_C + 0.5), [o], [v3((0, 1, 0))], tmax=0.8)
    if ok[0]:
        c = h[0] + v3((0, -0.003, 0.01))
        R = rot_from_axes(z_axis=(0, -1, 0.2))
        fd.add(Cylinder(c, 0.028, 0.009, rr=0.003, R=R), 0.004)
        for k in range(12):
            a = 2 * math.pi * k / 12
            dd = R @ v3((math.cos(a), math.sin(a), 0))
            L = 0.022 if k % 2 == 0 else 0.014
            fd.add(RoundCone(c + dd * 0.027, c + dd * (0.027 + L), 0.0045, 0.0015), 0.003)
    for t in RING_T:
        p, d = tail_at(t)
        w = 0.042 - 0.014 * t
        fd.add(Torus(p, w + 0.004, 0.0075, R=rot_from_axes(z_axis=d)), 0.003)
        fd.add(Torus(p + d * 0.018, w + 0.003, 0.006, R=rot_from_axes(z_axis=d)), 0.003)
    for sx in (-1, 1):
        lobe = ear_lobe(sx)
        fd.add(Torus(lobe + v3((sx * 0.004, -0.004, -0.034)), 0.03, 0.0042, R=rot_from_axes(z_axis=(1, 0.25, 0))), 0.0)
    return fd


# ======================================================================================= bronze: bodice, shoulder guard, bracers
def bodice_base():
    b = Field("BodiceBase")
    for p, k in torso_prims()[:5]:
        b.add(p, k)
    b.add(traps(), 0.05)
    return b


def _bodice_top(P):
    """Above the cut: a scooped neckline in front, higher at the back; straps over the shoulders."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
    neck_z = F(1.45) - F(0.14) * front * np.exp(-(x / F(0.11)) ** 2)
    top = z - neck_z
    strap = np.where(z > F(1.3), np.abs(np.abs(x) - F(0.13)) - F(0.055), F(-1))
    return np.maximum(top, strap)


def _bodice_arm(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    oval = ((y - F(0.06)) / F(0.15)) ** 2 + ((z - F(1.37)) / F(0.2)) ** 2 - F(1.0)
    return np.where(np.abs(x) > F(0.165), -oval * F(0.1), F(-1))


BODICE_Z = 0.965                     # its lower edge, over the belt


def bronze_field():
    fd = Field("Bronze")
    base = bodice_base()
    hammer = lambda P: F(0.001) * NOISE(P * F(45))
    def keep(P):
        return np.maximum(np.maximum(F(BODICE_Z) - P[:, 2], _bodice_top(P)), _bodice_arm(P))
    fd.add(Inter(Shell(base, 0.026, 0.017, pad=0.12, disp=hammer, disp_amp=0.002), Func(keep, (-1, -1, 0.85), (1, 1, 1.6)), 0.005), 0.0)
    def edge(P):
        k = np.maximum(_bodice_top(P), _bodice_arm(P))
        return np.maximum(np.abs(k + F(0.006)) - F(0.008), F(BODICE_Z + 0.02) - P[:, 2])
    fd.add(Inter(Shell(base, 0.036, 0.012, pad=0.12), Func(edge, (-1, -1, 0.9), (1, 1, 1.6)), 0.004), 0.004)
    fd.add(Inter(Shell(base, 0.036, 0.012, pad=0.12), Func(lambda P: np.abs(P[:, 2] - F(BODICE_Z + 0.008)) - F(0.009), (-1, -1, 0.85), (1, 1, 1.1)), 0.004), 0.004)
    # the embossed sun between the breasts, its rays fanning out
    outer = Func(lambda P: base.eval(P, margin=0.06) - F(0.036), (-0.6, -0.6, 0.85), (0.6, 0.6, 1.6))
    sc, ok = ray_hit(outer, [v3((0, -0.6, 1.235))], [v3((0, 1, 0))], tmax=0.8)
    if ok[0]:
        c = sc[0]
        fd.add(Ellipsoid(c + v3((0, -0.002, 0)), (0.026, 0.012, 0.026)), 0.006)
        for k in range(8):
            a = 2 * math.pi * k / 8 + math.pi / 8
            o = c + v3((math.cos(a) * 0.05, -0.3, math.sin(a) * 0.05))
            h, ok2 = ray_hit(outer, [o], [v3((0, 1, 0))], tmax=0.6)
            if ok2[0]:
                fd.add(RoundCone(c + v3((math.cos(a) * 0.03, -0.004, math.sin(a) * 0.03)), h[0], 0.006, 0.002), 0.004)
    # the guard on her sword shoulder: two overlapping lames over the deltoid (the upper one outside the lower), kept to
    # the outside of the shoulder
    sh = J["shoulder_R"]
    dl = Sphere(sh + v3((-0.025, -0.005, 0.015)), 0.088)
    for off, z_cut in ((0.024, -0.085), (0.038, -0.012)):
        fd.add(Inter(Shell(dl, off, 0.012, pad=0.06),
                     Func(lambda P, z_cut=z_cut: np.maximum(np.maximum(F(sh[2] + z_cut) - P[:, 2], np.abs(P[:, 1] - F(sh[1])) - F(0.105)),
                                                            P[:, 0] + F(0.215)), sh - 0.25, sh + 0.25), 0.004), 0.004)
    # bracers on both forearms, rimmed
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.66)
        fd.add(Inter(Shell(_forearm(side), 0.013, 0.012, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.07), c - 0.25, c + 0.25), 0.004), 0.0)
        for j in (-1, 1):
            cc = c + ax * (j * 0.066)
            fd.add(Inter(Shell(_forearm(side), 0.02, 0.008, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.006), cc - 0.2, cc + 0.2), 0.002), 0.003)
    # the belt's round plate
    kb = kilt_base()
    p, ok = ray_hit(Func(lambda P: kb.eval(P) - F(0.06), (-1, -1, 0.7), (1, 1, 1.2)), [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    if ok[0]:
        fd.add(Cylinder(p[0] + v3((0, -0.004, 0)), 0.032, 0.012, rr=0.004, R=rot_from_axes(z_axis=(0, -1, 0))), 0.004)
    return fd


# ======================================================================================= linen kilt, leather
BELT_Z = 0.93


def kilt_base():
    b = Field("KiltBase")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    b.add(RoundCone((0, 0.035, 0.88), (0, 0.035, 0.5), 0.225, 0.29), 0.08)
    return b


def kilt_hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(0.55) + F(0.035) * np.clip(np.cos(a), 0, 1) - F(0.03) * np.clip(-np.cos(a), 0, 1) + F(0.006) * NOISE(P * F(8))


def linen_field():
    """A short white linen kilt, finely pleated, a red woven border (label 5) along the hem and a blue stripe (6)
    above it."""
    fd = Field("Linen")
    base = kilt_base()
    def pleats(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        k = smoothstep(0.9, 0.7, P[:, 2])
        return F(0.0035) * np.sin(a * F(36)) * k + F(0.0012) * NOISE(P * F(25))
    fd.add(Inter(Shell(base, 0.02, 0.018, pad=0.1, disp=pleats, disp_amp=0.005),
                 Func(lambda P: np.maximum(kilt_hem(P) - P[:, 2], P[:, 2] - F(BELT_Z + 0.03)), (-1, -1, 0.35), (1, 1, 1.1)), 0.006), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (kilt_hem(P) + F(0.036)), (-1, -1, 0.35), (1, 1, 0.75)), 5)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - (kilt_hem(P) + F(0.05))) - F(0.006), (-1, -1, 0.35), (1, 1, 0.75)), 6)
    return fd


STRIPS = [-0.62, -0.38, -0.13, 0.13, 0.38, 0.62, 2.55, 2.9, 3.25, 3.6]      # angles (front = 0) of the hanging leather strips


def leather_field():
    """A studded belt, red leather strips hanging from it over the kilt (label 5 = red-dyed), the sword's grip wrap is
    on the sword; sandals laced up her calves."""
    fd = Field("Leather")
    kb = kilt_base()
    fd.add(Inter(Shell(kb, 0.042, 0.024, pad=0.1), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(0.026), (-1, -1, 0.8), (1, 1, 1.1)), 0.005), 0.0)
    out = Func(lambda P: kb.eval(P) - F(0.05), (-1, -1, 0.5), (1, 1, 1.1))
    for a in STRIPS:
        d = v3((math.sin(a), -math.cos(a), 0))
        top, ok = ray_hit(out, [v3((0, 0.035, BELT_Z - 0.02)) + d * 0.6], [-d], tmax=0.7)
        bot, ok2 = ray_hit(out, [v3((0, 0.035, BELT_Z - 0.2)) + d * 0.6], [-d], tmax=0.7)
        if not (ok[0] and ok2[0]):
            continue
        t0, b0 = top[0] + d * 0.006, bot[0] + d * 0.02
        ax = norm(b0 - t0)
        L = float(np.linalg.norm(b0 - t0))
        R = rot_from_axes(z_axis=ax, y_axis=d)
        fd.add(RoundBox((t0 + b0) / 2, (0.026, 0.005, L / 2), 0.004, R=R), 0.002, 5)
        for zz in (0.25, 0.75):
            fd.add(Sphere(lerp(t0, b0, zz) + d * 0.005, 0.0055), 0.002, 0)
    for k in range(16):                                                     # studs round the belt
        a = 2 * math.pi * k / 16
        d = v3((math.sin(a), -math.cos(a), 0))
        h, ok = ray_hit(Func(lambda P: kb.eval(P) - F(0.066), (-1, -1, 0.8), (1, 1, 1.1)), [v3((0, 0.035, BELT_Z)) + d * 0.6], [-d], tmax=0.7)
        if ok[0] and abs(a) > 0.2 and abs(a - 2 * math.pi) > 0.2:
            fd.add(Sphere(h[0], 0.007), 0.002, 6)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an, kn = J["ankle_" + side], J["knee_" + side]
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.073 + v3((0, 0, -0.1)), (0.07, 0.145, 0.011), 0.009, R=Rz), 0.0)
        ft = Field("FootHull")
        foot(ft, side)
        for c, rad in ((an + fwd * 0.14 + v3((0, 0, -0.07)), 0.022), (an + fwd * 0.05 + v3((0, 0, -0.035)), 0.02)):
            fd.add(Inter(Shell(ft, 0.006, 0.01, pad=0.05), Func(lambda P, c=c, fwd=fwd, rad=rad: np.abs((P - c.astype(F)) @ fwd.astype(F)) - F(rad * 0.6), c - 0.15, c + 0.15), 0.003), 0.002)
        # laces crossing up the calf: rings round the shin, joined by crossing straps in front
        shin = Field("Shin")
        shin.add(RoundCone(kn, an, 0.074, 0.048), 0.0)
        shin.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.028, 0)), (0.084, 0.082, 0.13), R=rot_from_axes(z_axis=an - kn)), 0.04)
        zs = [an[2] + 0.04 + (kn[2] - 0.07 - an[2] - 0.04) * k / 4 for k in range(5)]
        for z in zs:
            fd.add(Inter(Shell(shin, 0.006, 0.008, pad=0.05), Func(lambda P, z=z: np.abs(P[:, 2] - F(z)) - F(0.006), an - 0.2, kn + 0.2), 0.002), 0.002)
        sh_out = Func(lambda P: shin.eval(P) - F(0.008), an - v3((0.2, 0.2, 0.05)), kn + v3((0.2, 0.2, 0.05)))
        for k in range(4):
            for sgn in (-1, 1):
                pa = v3((an[0] + sgn * 0.04, an[1] - 0.3, zs[k]))
                pb = v3((an[0] - sgn * 0.04, an[1] - 0.3, zs[k + 1]))
                ha, oka = ray_hit(sh_out, [pa], [v3((0, 1, 0))], tmax=0.5)
                hb, okb = ray_hit(sh_out, [pb], [v3((0, 1, 0))], tmax=0.5)
                if oka[0] and okb[0]:
                    mid = (ha[0] + hb[0]) / 2 + v3((0, -0.006, 0))
                    fd.add(Chain([ha[0], mid, hb[0]], [0.005, 0.0055, 0.005], k=0.003), 0.002)
    return fd


# ======================================================================================= the khopesh
GRIP_BACK = 0.075          # fist centre -> pommel
SHANK = (0.075, 0.27)      # straight shank, from the guard
GEM_R = 0.022


def sword_axis():
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t, f          # origin, along the sword, toward its edge (the knuckles)


def blade_curve():
    """The blade's centre line from the end of the shank: out and curving round to the hooked tip (toward the back,
    away from the edge), with its half-width at each point."""
    a0, ax, ed = sword_axis()
    p0 = a0 + ax * SHANK[1]
    p1 = a0 + ax * (SHANK[1] + 0.2)
    p2 = a0 + ax * (SHANK[1] + 0.36) - ed * 0.07
    p3 = a0 + ax * (SHANK[1] + 0.33) - ed * 0.2
    ts = np.linspace(0, 1, 16)
    pts = [bez3(p0, p1, p2, p3, t) for t in ts]
    widths = [0.026 + 0.012 * math.sin(t * math.pi * 0.9) - 0.022 * t ** 3 for t in ts]
    return pts, widths


def _blade_sd(P, a, b, wa, wb, side, half_t):
    """A flat tapering strip from a to b: its edge side (toward `side`) is ground to a sharp bevel."""
    d = b - a
    L = float(np.linalg.norm(d))
    ax = d / L
    nrm = norm(np.cross(ax, side))
    q = P - a.astype(F)
    u = q @ ax.astype(F)
    v = q @ side.astype(F)
    w = q @ nrm.astype(F)
    t = np.clip(u / F(L), 0, 1)
    hw = F(wa) + (F(wb) - F(wa)) * t
    th = F(half_t) * np.clip(F(1.0) - np.maximum(v, F(0)) / np.maximum(hw, F(1e-4)) * F(0.7), F(0.25), F(1))   # the bevel
    d_u = np.maximum(-u, u - F(L))
    d_v = np.abs(v) - hw
    d_w = np.abs(w) - th
    qq = np.stack([d_u, d_v, d_w], 1)
    return np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0)


def sword_field():
    """Bronze (label 6) khopesh: a ribbed shank and the sickle blade, a crescent guard; the grip wrapped in red cord (5)
    on a dark wooden core (0); a socket on the pommel for the sun-stone."""
    fd = Field("Sword")
    a0, ax, ed = sword_axis()
    side = norm(np.cross(ax, ed))                       # the blade's flat faces look this way
    R = rot_from_axes(z_axis=ax, x_axis=ed)
    # grip and its cord wrap
    fd.add(RoundCone(a0 - ax * GRIP_BACK, a0 + ax * SHANK[0], 0.016, 0.017), 0.0, 0)
    for k in range(7):
        fd.add(Torus(a0 + ax * (-0.058 + 0.019 * k), 0.0175, 0.0042, R=R), 0.002, 5)
    # pommel cup (the gem sits in it)
    pc = a0 - ax * (GRIP_BACK + 0.012)
    fd.add(Cylinder(pc, 0.026, 0.024, rr=0.008, R=R), 0.005, 6)
    fd.sub(Sphere(pc - ax * 0.018, GEM_R * 0.95), 0.003)
    # guard: a short crescent across the edge line
    gc = a0 + ax * SHANK[0]
    fd.add(Chain([gc - ed * 0.042 - ax * 0.012, gc - ed * 0.02, gc + ed * 0.02, gc + ed * 0.042 - ax * 0.012], [0.008, 0.011, 0.011, 0.008],
                 k=0.006), 0.004, 6)
    # the shank: a flat bar with a raised midrib
    s0, s1 = a0 + ax * SHANK[0], a0 + ax * SHANK[1]
    fd.add(Func(lambda P: _blade_sd(P, s0, s1, 0.017, 0.02, ed, 0.0065), np.minimum(s0, s1) - 0.05, np.maximum(s0, s1) + 0.05), 0.004, 6)
    fd.add(RoundCone(s0, s1, 0.0055, 0.0045), 0.002, 6)
    # the blade, a chain of beveled strips along the curve, the edge on the outside of the curve
    pts, ws = blade_curve()
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        tng = norm(b - a)
        out = norm(np.cross(side, tng))                 # in the blade's plane, perpendicular to the curve
        if out @ ed < 0:
            out = -out
        a2, b2 = a - tng * 0.006, b + tng * 0.006
        fd.add(Func(lambda P, a2=a2, b2=b2, wa=ws[i], wb=ws[i + 1], out=out: _blade_sd(P, a2, b2, wa, wb, out, 0.006),
                    np.minimum(a2, b2) - 0.06, np.maximum(a2, b2) + 0.06), 0.004, 6)
    fd.add(Sphere(pts[0], 0.008), 0.006, 6)
    return fd


def gem_center():
    a0, ax, ed = sword_axis()
    return a0 - ax * (GRIP_BACK + 0.03)


def gem_field():
    """The sun-stone in the pommel (its own glowing mesh)."""
    fd = Field("Gem")
    fd.add(Sphere(gem_center(), GEM_R), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.232, 1.622)), 0.045, 0.45)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.1, -0.15, 1.6)), 0.06, 0.5), (hp((sx * 0.174, 0.035, 1.66)), 0.05, 0.5),
                (J["elbow_" + sd] + v3((0, 0.022, 0)), 0.05, 0.25), (J["knee_" + sd] + v3((0, -0.026, 0)), 0.06, 0.3)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.01, 0.028, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "kira"
ROOT_NAME = "HeroKiraHQ"
TEX_PREFIX = "hero"
MAT_NAME = "KiraMat"
MESH_NAME = "Kira"
BASE_MODULE = "kira_base"
ANIM_MODULE = "anim_kira"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Gold", "Bronze", "Linen", "Leather", "Sword", "Gem"]
REGION_PARTS = ("Skin", "Linen", "Leather", "Sword")
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_KiraSkin", "base": (0.76, 0.52, 0.36), "ruddy": (0.8, 0.46, 0.36), "lips": (0.66, 0.34, 0.3),
                      "brow": ((0.05, 0.04, 0.035), (0.12, 0.09, 0.07)), "paint": (0.95, 0.72, 0.22),
                      "extra": ((LASH, (0.05, 0.035, 0.03), 0.5), (KOHL, (0.04, 0.035, 0.05), 0.45))}),
    "Hair": ("hair", {"name": "HQ_KiraHair", "base": (0.07, 0.055, 0.05), "hi": (0.27, 0.22, 0.2), "low": (0.03, 0.022, 0.02),
                      "streak": (0.045, 0.035, 0.03), "tint": (0.14, 0.1, 0.08)}),
    "Gold": ("gold", {"name": "HQ_KiraGold"}),
    "Bronze": ("bronze", {"name": "HQ_KiraBronze"}),
    "Linen": ("linen", {"name": "HQ_KiraLinen"}),
    "Leather": ("leather_dyed", {"name": "HQ_KiraLeather"}),
    "Sword": ("spear_shaft", {"name": "HQ_Khopesh"}),
    "Gem": ("glow_ball", {"name": "HQ_SunStone", "col": (1.0, 0.78, 0.3)}),
}
GLOW = {"Gem": ((1.0, 0.7, 0.2), 1.0, 0.55)}
LOW_TARGETS = {"Skin": 6800, "Teeth": 60, "Hair": 2400, "Gold": 700, "Bronze": 2200, "Linen": 1300, "Leather": 1900,
               "Sword": 900, "Gem": 120}
AO_EXCLUDE = ["Sword", "Gem", "Gold"]
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
    g = gem_center()
    a0, ax, ed = sword_axis()
    return [("gem", g, g - ax * 0.08, "hand.R")]


def hair_weights(ob, skin_ob, arm):
    """The hair on her head rides the head; the braid down her back blends to the neck and chest as it falls."""
    groups = {}
    z1, z0 = hp((0, 0, 1.62))[2], 1.08
    for v in ob.data.vertices:
        p = v.co
        if p.z < z1 and p.y > 0.12:
            t = max(0.0, min(1.0, (z1 - p.z) / (z1 - z0)))
            _blend_add(ob, groups, v.index, {"head": 1.0 - 0.7 * t, "neck": 0.3 * t, "chest": 0.45 * t, "spine": 0.15 * t})
        else:
            _blend_add(ob, groups, v.index, {"head": 1.0})


def gold_weights(ob, skin_ob, arm):
    groups = {}
    z1, z0 = hp((0, 0, 1.62))[2], 1.08
    for v in ob.data.vertices:
        p = v.co
        if p.z < z1 and p.y > 0.12:                     # rings on the braid
            t = max(0.0, min(1.0, (z1 - p.z) / (z1 - z0)))
            w = {"head": 1.0 - 0.7 * t, "neck": 0.3 * t, "chest": 0.45 * t, "spine": 0.15 * t}
        else:
            w = {"head": 1.0}
        _blend_add(ob, groups, v.index, w)


def leather_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"},
                         caps={"thigh.R": 0.5, "thigh.L": 0.5})


def bronze_weights(ob, skin_ob, arm):
    """The bodice rides the torso; the shoulder guard the right upper arm (and a little the clavicle); the bracers their
    forearms."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "forearm.R", "forearm.L", "hand.R", "hand.L"},
                         caps={"upperarm.R": 1.0})
    groups = {}
    shR = J["shoulder_R"]
    for v in ob.data.vertices:
        p = np.array(v.co)
        side = "R" if p[0] < 0 else "L"
        el, wr = J["elbow_" + side], J["wrist_" + side]
        if _seg_dist(p, el, wr) < 0.09 and abs(p[0]) > 0.4:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"forearm." + side: 1.0})
        elif np.linalg.norm(p - shR) < 0.15 and p[0] < -0.22:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"upperarm.R": 0.75, "clavicle.R": 0.25})


def _seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
    return float(np.linalg.norm(a + ab * t - p))


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Gold": ("custom", gold_weights), "Bronze": ("custom", bronze_weights),
        "Linen": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Leather": ("custom", leather_weights),
        "Sword": ("rigid", "hand.R"), "Gem": ("rigid", "gem"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Sword":
        return 0.9
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Gold", gold_field(), 0.0015 if fine else 0.0022),
        ("Bronze", bronze_field(), 0.0024 if fine else 0.0034),
        ("Linen", linen_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Sword", sword_field(), 0.0016 if fine else 0.0024),
        ("Gem", gem_field(), 0.0015),
    ]
