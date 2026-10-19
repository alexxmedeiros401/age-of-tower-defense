"""The Javelin Thrower (HQ tower, Iron Age). Rest pose = A-pose, facing -Y, feet at z=0; right side = -X.

A lean young skirmisher of a hill fort: his hair limed stiff and pale and swept back from his brow in spikes, a long
drooping moustache, blue woad spirals on his arms and two stripes on each cheek, a twisted gold torc round his neck; a
sleeveless green tunic checked in red and yellow, belted, over red-brown checked trousers bound with leather thongs
from his shoes to below his knees; leather bracers. An iron-headed ash javelin in his right fist, four more in a
leather case on his back with their heads over his right shoulder; his left hand open (it points at the robots as he
throws).

The javelin is rigid on the `javelin` bone in his right fist: anim_javelin.py hides it as it leaves his hand and shows
a fresh one when he draws the next from the case."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp, fan_lock
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
HEAD_RAD = v3((0.174, 0.19, 0.188)) * HS
EYE_R = hr(0.036)


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
CURLS = {"R": (1.45, 1.6, 1.2), "L": (0.22, 0.3, 0.2)}           # the javelin's grip; an open hand (it points)


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    fist = side == "R"
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.06, 0.03, 0.066)) * s, 0.028 * s, R=Rp), 0.028, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.033, 0.028, 0.05)) * s, R=Rp), 0.019, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.042, 0.0142, -0.0142, -0.042)
    lens = (0.96, 1.04, 0.98, 0.8)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * (1.2 if fist else 0.5))
        pts, rads = [p], [0.0198 * s * (0.92 if i == 3 else 1.0)]
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
        d1, d2 = norm(f * 0.55 + t * 0.55 + n * 0.6), norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:                                                    # (the open hand's thumb lies along its fingers)
        d1, d2 = norm(f * 0.7 + t * 0.6 + n * 0.25), norm(f * 0.85 + t * 0.2 + n * 0.2)
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
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.05, 0.0, 0.0)), 0.024), 0.018, SKIN)


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.055, 1.59), (0.134, 0.128, 0.124)), 0.07, SKIN)                          # a lean jaw
    fd.add(E((0, -0.134, 1.502), (0.082, 0.066, 0.064)), 0.05, SKIN)                         # chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.114, -0.117, 1.634), 0.048), 0.05, SKIN)                              # high cheekbones
        fd.add(S((sx * 0.121, -0.045, 1.56), 0.047), 0.05, SKIN)                               # jaw corners
        pts = [hp((sx * 0.152, -0.055, 1.742)), hp((sx * 0.116, -0.13, 1.75)), hp((sx * 0.06, -0.172, 1.748)), hp((0.0, -0.182, 1.748))]
        fd.add(Chain(pts, [hr(0.012), hr(0.021), hr(0.025), hr(0.025)], k=hr(0.022)), hr(0.035), SKIN)     # brow ridge
    # straight brows, their outer ends a little raised: alert
    for sx in (-1, 1):
        pts = [hp((sx * 0.026, -0.214, 1.755)), hp((sx * 0.066, -0.207, 1.767)), hp((sx * 0.11, -0.185, 1.776)), hp((sx * 0.153, -0.143, 1.776))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.009), hr(0.011), hr(0.01), hr(0.005)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.017), hr(0.019), hr(0.017), hr(0.01)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0065)), Plane(ec + v3((0, 0, hr(0.018))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.005)), Plane(ec + v3((0, 0, -hr(0.026))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.016))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
    # a long straight nose
    fd.add(RoundCone(hp((0, -0.182, 1.724)), hp((0, -0.24, 1.626)), hr(0.016), hr(0.024)), hr(0.016), SKIN)
    fd.add(S((0, -0.242, 1.612), 0.028), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.029, -0.214, 1.602), 0.02), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.015, -0.231, 1.589)), v3((0.009, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # mouth: set firm under the moustache
    slot = [hp((-0.058, -0.17, 1.548)), hp((-0.03, -0.193, 1.546)), hp((0, -0.199, 1.547)), hp((0.03, -0.193, 1.546)), hp((0.058, -0.17, 1.548))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.047, -0.17, 1.539), (-0.025, -0.186, 1.531), (0, -0.19, 1.529), (0.025, -0.186, 1.531), (0.047, -0.17, 1.539)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.008), hr(0.009), hr(0.008), hr(0.005)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.176, 0.035, 1.66)), v3((0.026, 0.047, 0.06)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
    # woad: two stripes across each cheekbone (thin slabs through the face, front to back)
    for sx in (-1, 1):
        for dz in (0.0, -0.025):
            a, b = hp((sx * 0.074, -0.2, 1.624 + dz)), hp((sx * 0.142, -0.2, 1.605 + dz))
            d = norm(b - a)
            fd.paint(RoundBox((a + b) / 2, (np.linalg.norm(b - a) / 2, 0.11, hr(0.0062)), hr(0.004), R=rot_from_axes(x_axis=d, y_axis=(0, 1, 0))), PAINT)


# ======================================================================================= body
def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.19), (0.26, 0.21, 0.27), R=euler(-0.12, 0, 0)), 0.0),
        (Ellipsoid((0, 0.12, 1.24), (0.29, 0.155, 0.2)), 0.06),
        (Ellipsoid((0.12, -0.135, 1.27), (0.125, 0.052, 0.082), R=euler(0.1, 0, 0.18)), 0.045),
        (Ellipsoid((-0.12, -0.135, 1.27), (0.125, 0.052, 0.082), R=euler(0.1, 0, -0.18)), 0.045),
        (Ellipsoid((0, -0.01, 0.98), (0.2, 0.18, 0.2)), 0.08),
        (Ellipsoid((0, 0.045, 0.82), (0.225, 0.175, 0.16)), 0.08),
    ]


def traps():
    return Ellipsoid((0, 0.1, 1.41), (0.235, 0.125, 0.09), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.065, 1.36), hp((0, 0.02, 1.575)), 0.098, hr(0.084))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.022, -0.005, 0.014)), 0.105)


def upper_arm_prims(side):
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    return [(RoundCone(sh, el, 0.092, 0.07), 0.05),
            (Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.025, 0)), (0.082, 0.085, 0.122), R=rot_from_axes(z_axis=el - sh)), 0.04)]


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        el, wr = J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        for p, k in upper_arm_prims(side):
            fd.add(p, k, SKIN)
        fd.add(RoundCone(el, wr, 0.068, 0.053), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.087, 0.078, 0.128), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.054), 0.028, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def leg_prims(side):
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(hip, kn, 0.132, 0.086), 0.065),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.12, 0.113, 0.182), R=rot_from_axes(z_axis=kn - hip)), 0.048),
            (Sphere(kn + v3((0, -0.03, 0.0)), 0.067), 0.038),
            (RoundCone(kn, an, 0.083, 0.055), 0.038),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.093, 0.09, 0.138), R=rot_from_axes(z_axis=an - kn)), 0.043)]


def arm_hull(side):
    f = Field("ArmHull")
    f.add(deltoid(side), 0.0)
    for p, k in upper_arm_prims(side):
        f.add(p, 0.05)
    return f


def woad(fd):
    """Blue woad on both upper arms: a spiral on the outside of each, a ring round it above the elbow."""
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        out = norm(v3((sx, -0.25, 0.0)) - ax * (v3((sx, -0.25, 0.0)) @ ax))
        side_v = np.cross(ax, out)
        hull = arm_hull(side)
        c0 = lerp(sh, el, 0.44)
        pts = []
        for k in range(30):
            th = k / 29.0 * 2.3 * 2 * math.pi
            r = 0.007 + 0.0058 * th
            a, s = r * math.cos(th) * sx, r * math.sin(th)
            phi = a / 0.095                                     # (arc length round the arm -> angle)
            dirv = out * math.cos(phi) + side_v * math.sin(phi)
            o = c0 + ax * s + dirv * 0.4
            h, ok = ray_hit(hull, [o], [-dirv], tmax=0.5)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 4:
            fd.paint(Chain(pts, [0.0072] * len(pts), k=0.003), PAINT)
        for u, wdt in ((0.8, 0.0085), (0.86, 0.0045)):
            c = lerp(sh, el, u)
            fd.paint(Func(lambda P, c=c, ax=ax, wdt=wdt: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(wdt), c - 0.14, c + 0.14), PAINT)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    woad(fd)
    return fd


def eyes_field():
    fd = Field("Eyes")
    for sx in (-1, 1):
        fd.add(Sphere(eye_c(sx), EYE_R))
    return fd


def teeth_field():
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009, -0.178, 1.549)), v3((0.008, 0.006, 0.007)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= limed hair, moustache
def hair_field(seed=13):
    """Hair limed stiff and pale: thick locks swept up from his brow and back over his head, more from the crown down the
    back of his head and back over his ears, their ends standing out in spikes."""
    rng = np.random.RandomState(seed)
    fd = Field("Hair")
    hc, hrad = HEAD_C, HEAD_RAD
    pfront, pback = hp((0, -0.17, 1.82)), hp((0, 0.215, 1.585))
    slope = (pback[2] - pfront[2]) / (pback[1] - pfront[1])
    hl_n = norm((0, slope, -1.0))
    hairline = Func(lambda P: ((P - pfront.astype(F)) @ hl_n.astype(F)) + F(0.008) * NOISE(P * F(26)), hc - 0.5, hc + 0.5)
    fd.add(Inter(Ellipsoid(hc, hrad + 0.01), hairline, 0.02), 0.0)          # scalp layer
    hull = Field("HairHull")
    hull.add(Ellipsoid(hc, hrad + 0.02), 0.0)
    hull.add(Ellipsoid(hp((0, 0.15, 1.67)), v3((0.19, 0.13, 0.2)) * HS), hr(0.08))
    # front: thick locks swept up from the hairline and back over the crown, their ends standing up
    nf = 7
    for i in range(nf):
        u = -1 + 2 * (i + 0.5) / nf
        x = u * 0.15
        hz = pfront[2] + slope * (hp((0, -0.15 + 0.1 * u * u, 0))[1] - pfront[1])
        o = hp((x, -0.6, 0)) + v3((0, 0, hz - hp((0, 0, 0))[2] + hr(0.008)))
        st, ok = ray_hit(hull, [o], [v3((0, 1, 0))], tmax=0.8)
        if not ok[0]:
            continue
        hd = norm(v3((u * 0.35, 1.0, 0.25)))
        fan_lock(hull, st[0], hd, hr(0.27 + rng.uniform(0, 0.04)), hr(0.08), hr(0.034), segs=8, gravity=-0.3,
                 lift=hr(0.045), tip_up=hr(0.07), grooves=1, fd=fd, rng=rng, thin_root=True)
    # from the crown down the back of his head, lying close, the ends kicking out
    crown = hc + v3((0, 0.0, hrad[2] * 0.98))
    for i in range(11):
        a = math.pi * (0.5 + (i + 0.5) / 11) + rng.uniform(-0.04, 0.04)
        hd = v3((math.sin(a), -math.cos(a), 0.0))
        fan_lock(hull, crown + hd * 0.02, hd, hr(0.32 + 0.06 * rng.rand()), hr(0.085), hr(0.032), segs=10, gravity=0.55,
                 lift=hr(0.03), tip_up=hr(0.05), grooves=1, fd=fd, rng=rng)
    # under them, down the back of his head to the nape, the ends kicking out
    for i in range(9):
        a = math.pi * (0.62 + 0.76 * (i + 0.5) / 9) + rng.uniform(-0.04, 0.04)
        hd = v3((math.sin(a), -math.cos(a), 0.0))
        o = hc + v3((0, 0, 0.03)) + hd * 0.5
        st, ok = ray_hit(hull, [o], [-hd], tmax=0.5)
        if not ok[0]:
            continue
        fan_lock(hull, st[0], hd * 0.35 + v3((0, 0, -1.0)), hr(0.2 + 0.04 * rng.rand()), hr(0.085), hr(0.03), segs=8, gravity=0.2,
                 lift=hr(0.03), grooves=1, fd=fd, rng=rng)
    # over his temples, swept back over his ears
    for sx in (-1, 1):
        for k, (y0, dz) in enumerate(((-0.07, 0.0), (0.01, -0.02))):
            o = hp((sx * 0.6, y0, 1.79 + dz))
            st, ok = ray_hit(hull, [o], [v3((-sx, 0, 0))], tmax=0.8)
            if not ok[0]:
                continue
            fan_lock(hull, st[0], v3((sx * 0.1, 1.0, -0.25)), hr(0.24), hr(0.075), hr(0.03), segs=8, gravity=0.3,
                     lift=hr(0.035), tip_up=hr(0.04), grooves=1, fd=fd, rng=rng, thin_root=True)
    return fd


def moustache_field():
    """A long moustache drooping past the corners of his mouth to his jaw."""
    fd = Field("Moustache")
    strands = lambda P: F(0.0022) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.004, -0.236, 1.592)), hp((sx * 0.036, -0.226, 1.582)), hp((sx * 0.066, -0.203, 1.562)),
               hp((sx * 0.08, -0.186, 1.53)), hp((sx * 0.086, -0.176, 1.49)), hp((sx * 0.088, -0.17, 1.455))]
        nrm = [norm(v3((sx * 0.15, -1, 0.4))), norm(v3((sx * 0.4, -1, 0.3))), norm(v3((sx * 0.8, -1, 0.1))),
               norm(v3((sx * 1, -0.8, 0))), norm(v3((sx * 1, -0.6, 0))), norm(v3((sx * 1, -0.6, 0)))]
        fd.add(Lock(pts, [hr(0.014), hr(0.019), hr(0.017), hr(0.013), hr(0.009), hr(0.004)],
                    [hr(0.01), hr(0.012), hr(0.011), hr(0.009), hr(0.007), hr(0.003)], nrm, k=hr(0.006),
                    disp=strands, disp_amp=0.003), 0.004)
    return fd


# ======================================================================================= tunic, trousers (checked wool)
BELT_Z = 0.955
HEM_Z = 0.6


def tunic_base():
    b = Field("TunicBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(RoundCone((0, 0.035, 0.9), (0, 0.035, 0.5), 0.232, 0.3), 0.08)
    return b


def _neck_cut(P):
    """> 0 above the neckline: round at the back, dipping in a short slit at the front."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
    neck_z = F(1.475) - F(0.06) * front * np.exp(-(x / F(0.12)) ** 2)
    slit = np.where((y < F(-0.05)) & (z < neck_z + F(0.01)) & (z > F(1.34)), F(0.011) - np.abs(x), F(-1))
    return np.maximum(z - neck_z, slit)


def _arm_cut(P):
    """> 0 in the armholes (the tunic is sleeveless; his shoulders are bare past the top of the arm)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    oval = ((y - F(0.07)) / F(0.17)) ** 2 + ((z - F(1.35)) / F(0.23)) ** 2 - F(1.0)
    hole = np.where(ax > F(0.2), -oval * F(0.1), F(-1))
    top = np.where(z > F(1.36), ax - F(0.245), F(-1))
    return np.maximum(hole, top)


def hem_z(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(HEM_Z) + F(0.022) * np.cos(a * 2) + F(0.01) * np.sin(a * 5 + 1.0) + F(0.008) * NOISE(P * F(8))


def tunic_field():
    """Sleeveless, to mid-thigh, belted: gathered at the belt, falling in folds below it; a woven border (label 5)
    along the hem."""
    fd = Field("Tunic")
    base = tunic_base()
    def shell(P):
        d = base.eval(P, margin=0.1)
        z = P[:, 2]
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        below = np.clip((F(BELT_Z) - z) / F(0.12), 0, 1)
        folds = F(0.008) * np.sin(a * F(13) + F(0.6) * np.sin(a * F(3))) * below + F(0.004) * NOISE(P * F(14))
        off = F(0.03) - F(0.014) * np.exp(-((z - F(BELT_Z)) / F(0.05)) ** 2) + folds + F(0.012) * below
        return np.abs(d - off) - F(0.0085)
    def keep(P):
        return np.maximum(np.maximum(_neck_cut(P), _arm_cut(P)), hem_z(P) - P[:, 2])
    lo, hi = (-0.5, -0.45, 0.4), (0.5, 0.5, 1.62)
    fd.add(Inter(Func(shell, lo, hi), Func(keep, lo, hi), 0.004), 0.0)
    # a rolled edge round the neck and the armholes
    def edge(P):
        k = np.maximum(_neck_cut(P), _arm_cut(P))
        return np.maximum(np.abs(k + F(0.006)) - F(0.008), F(1.1) - P[:, 2])
    fd.add(Inter(Shell(base, 0.036, 0.016, pad=0.1), Func(edge, (-0.5, -0.45, 1.0), (0.5, 0.5, 1.62)), 0.004), 0.004)
    fd.paint(Func(lambda P: P[:, 2] - (hem_z(P) + F(0.042)), (-0.6, -0.6, 0.4), (0.6, 0.6, 0.75)), 5)
    return fd


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
    keep = lambda P: np.maximum(P[:, 2] - F(0.97), F(an_z + 0.05) - P[:, 2])
    lo, hi = (-0.45, -0.4, 0.0), (0.45, 0.4, 1.02)
    fd.add(Inter(Func(shell, lo, hi), Func(keep, lo, hi), 0.004), 0.0)
    return fd


# ======================================================================================= leather: belt, baldric, bracers, shoes, thongs
def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.068, 0.053)


def baldric_plane():
    """The case's strap runs from his right shoulder across his chest to his left hip."""
    a, b = v3((-0.22, 0.0, 1.45)), v3((0.24, 0.0, 0.95))
    d = norm(b - a)
    n = norm(np.cross(d, v3((0, 1, 0))))
    return a, n


def shoe_hull(side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.1)
    fwd = Rz @ v3((0, -1, 0))
    f = Field("ShoeHull")
    f.add(Sphere(an + v3((0, 0.04, -0.05)), 0.062), 0.0)
    f.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.068)), (0.066, 0.128, 0.036), 0.034, R=Rz), 0.04)
    f.add(Ellipsoid(an + fwd * 0.17 + v3((0, 0, -0.072)), (0.062, 0.06, 0.036), R=Rz), 0.03)
    f.add(Cylinder(an + v3((0, 0.005, 0.02)), 0.066, 0.1, rr=0.03), 0.04)
    return f, fwd, Rz


def leg_axis_point(side, z):
    kn, an = J["knee_" + side], J["ankle_" + side]
    u = (kn[2] - z) / (kn[2] - an[2])
    return lerp(kn, an, u)


def leather_field():
    """The belt, the case's strap, bracers on both forearms, shoes, and thongs criss-crossing up his shins."""
    fd = Field("Leather")
    tb = tunic_base()
    fd.add(Func(lambda P: np.maximum(np.abs(tb.eval(P, margin=0.08) - F(0.03)) - F(0.012), np.abs(P[:, 2] - F(BELT_Z)) - F(0.03)),
                (-0.5, -0.45, 0.85), (0.5, 0.45, 1.06)), 0.0)
    a, n = baldric_plane()
    fd.add(Inter(Shell(tb, 0.05, 0.013, pad=0.12), Func(lambda P: np.abs((P - a.astype(F)) @ n.astype(F)) - F(0.027), (-0.6, -0.6, 0.8), (0.6, 0.6, 1.62)), 0.004), 0.0)
    for side in ("L", "R"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.7)
        fd.add(Inter(Shell(_forearm(side), 0.012, 0.016, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.068), c - 0.25, c + 0.25), 0.004), 0.0)
        for j in (-1, 0, 1):
            cc = c + ax * (j * 0.042)
            fd.add(Inter(Shell(_forearm(side), 0.021, 0.006, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.0055), cc - 0.2, cc + 0.2), 0.002), 0.003)
    for side in ("R", "L"):
        an = J["ankle_" + side]
        sh, fwd, Rz = shoe_hull(side)
        top = an[2] + 0.075
        fd.add(Inter(Shell(sh, 0.0, 0.026, pad=0.06), Func(lambda P, top=top: P[:, 2] - F(top), an - 0.35, an + 0.35), 0.006), 0.0)
        fd.add(RoundBox(an + fwd * 0.085 + v3((0, 0, -0.1)), (0.076, 0.16, 0.012), 0.01, R=Rz), 0.008)       # sole
        fd.add(Torus(an + v3((0, 0.006, 0.072)), 0.068, 0.011), 0.004)                                          # turned top
        # thongs crossing up the shin over the trousers, from the shoe to below the knee (laid on the trouser surface)
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


# ======================================================================================= gold: the torc, the belt's buckle
TORC_C = v3((0.0, 0.035, 1.47))
TORC_U = norm(v3((0.0, -0.928, -0.371)))            # toward the front, sloping down: it sits low at the throat
TORC_S = v3((1.0, 0.0, 0.0))
TORC_RY, TORC_RX = 0.13, 0.135


def torc_point(a):
    """A point on the torc's centre line, `a` radians round from the front (it is open at the front)."""
    return TORC_C + TORC_U * (math.cos(a) * TORC_RY) + TORC_S * (math.sin(a) * TORC_RX)


TORC_N = norm(np.cross(TORC_S, TORC_U))


def gold_field():
    """A torc of three twisted gold strands, open at the front with two round terminals; a round buckle on the belt."""
    fd = Field("Gold")
    n = 48
    for strand in range(3):
        pts = []
        for k in range(n + 1):
            a = math.radians(26 + (360 - 52) * k / n)
            p = torc_point(a)
            radial = norm(p - TORC_C)
            tw = a * 4.0 + strand * 2 * math.pi / 3
            pts.append(p + (radial * math.cos(tw) + TORC_N * math.sin(tw)) * 0.0085)
        fd.add(Chain(pts, [0.0075] * len(pts), k=0.003), 0.004)
    for a in (math.radians(22), math.radians(-22)):
        fd.add(Sphere(torc_point(a), 0.019), 0.006)
    # the buckle at the front of the belt
    tb = tunic_base()
    h, ok = ray_hit(Func(lambda P: tb.eval(P, margin=0.1) - F(0.045), (-0.5, -0.6, 0.8), (0.5, 0.5, 1.1)), [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    c = h[0]
    fd.add(Torus(c + v3((0, -0.004, 0)), 0.03, 0.009, R=rot_from_axes(z_axis=(0, 1, 0))), 0.0)
    fd.add(RoundBox(c + v3((0, -0.006, 0)), (0.006, 0.006, 0.028), 0.004), 0.004)
    return fd


# ======================================================================================= the javelin, the case on his back
JAV_FWD = 0.74          # grip -> point
JAV_BACK = 0.46         # grip -> butt
JAV_R = 0.0125


def javelin_axis():
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), norm(t)


def _javelin(fd, a0, ax, up, back=JAV_BACK, fwd=JAV_FWD, wood=0, full=True):
    """One javelin through `a0` along `ax`: an ash shaft (label `wood`), a leather binding below the head (5), a
    long-socketed iron head, leaf-shaped with a midrib, and an iron butt cap (6)."""
    side = norm(np.cross(ax, up))
    up = np.cross(side, ax)
    grain = lambda P: F(0.0015) * NOISE(P * F(70))
    fd.add(Chain([a0 - ax * (back - 0.025), a0 + ax * (fwd - 0.19)], [JAV_R * 0.92, JAV_R], k=0.0, disp=grain, disp_amp=0.0015), 0.0, wood)
    s0, s1 = a0 + ax * (fwd - 0.2), a0 + ax * (fwd - 0.13)
    fd.add(RoundCone(s0, s1, JAV_R + 0.0025, JAV_R - 0.002), 0.003, 6)
    fd.add(Ellipsoid(a0 + ax * (fwd - 0.065), (0.025, 0.0055, 0.07), R=rot_from_axes(z_axis=ax, x_axis=side)), 0.005, 6)
    fd.add(Chain([s1 - ax * 0.01, a0 + ax * (fwd - 0.004)], [0.0085, 0.0025], k=0.004), 0.005, 6)
    for k in range(4):
        c = a0 + ax * (fwd - 0.215 - 0.011 * k)
        fd.add(Torus(c, JAV_R + 0.0025, 0.004, R=rot_from_axes(z_axis=ax)), 0.002, 5)
    if full:
        b0 = a0 - ax * back
        fd.add(RoundCone(b0 + ax * 0.04, b0 + ax * 0.004, JAV_R + 0.002, JAV_R * 0.8), 0.003, 6)


def javelin_field():
    fd = Field("Javelin")
    a0, ax = javelin_axis()
    wr, f, n, t = hand_frame("R")
    _javelin(fd, a0, ax, n)
    return fd


Q_BOT = v3((0.16, 0.35, 0.95))
Q_TOP = v3((-0.19, 0.45, 1.52))
Q_R = 0.054


def case_heads():
    """The four javelins in the case: (a point on each where it leaves the case's mouth, its direction)."""
    ax = norm(Q_TOP - Q_BOT)
    up = norm(np.cross(ax, v3((1, 0, 0))))
    side = norm(np.cross(ax, up))
    out = []
    for k, (u, v, lean) in enumerate(((-0.6, -0.4, 0.06), (0.55, -0.45, 0.08), (-0.1, 0.55, 0.05), (0.5, 0.45, 0.1))):
        o = Q_TOP + (side * u + up * v) * 0.026
        d = norm(ax + (side * u + up * v) * lean)
        out.append((o, d))
    return out


def quiver_field():
    """A leather case slung on his back, its mouth behind his right shoulder: rawhide bands (label 5); four javelins in
    it (ash 7, iron heads and their bindings 6/5) standing out over his shoulder."""
    fd = Field("Quiver")
    ax = norm(Q_TOP - Q_BOT)
    grain = lambda P: F(0.0015) * NOISE(P * F(40))
    fd.add(RoundCone(Q_BOT, Q_TOP, Q_R * 0.86, Q_R, disp=grain, disp_amp=0.002), 0.0)
    fd.add(Sphere(Q_BOT - ax * 0.01, Q_R * 0.88), 0.02)
    fd.sub(RoundCone(Q_TOP - ax * 0.07, Q_TOP + ax * 0.05, Q_R - 0.007, Q_R - 0.004), 0.006)               # open mouth
    fd.add(Torus(Q_TOP - ax * 0.005, Q_R + 0.001, 0.008, R=rot_from_axes(z_axis=ax)), 0.004, 5)
    for u in (0.2, 0.55):
        c = lerp(Q_BOT, Q_TOP, u)
        fd.add(Torus(c, Q_R * (0.88 + 0.12 * u) + 0.002, 0.007, R=rot_from_axes(z_axis=ax)), 0.004, 5)
    up = norm(np.cross(ax, v3((1, 0, 0))))
    for o, d in case_heads():
        _javelin(fd, o + d * 0.06, d, up, back=0.12, fwd=0.42, wood=7, full=False)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.242, 1.612)), 0.05, 0.55)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.1, -0.14, 1.61)), 0.06, 0.45), (hp((sx * 0.176, 0.035, 1.66)), 0.05, 0.5),
                (J["elbow_" + sd] + v3((0, 0.025, 0)), 0.06, 0.3), (J["knee_" + sd] + v3((0, -0.03, 0)), 0.07, 0.35),
                (J["shoulder_" + sd] + v3((0, 0, 0.1)), 0.11, 0.3)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.0142, -0.0142, -0.042):
            pts.append((wr + f * 0.138 + t * o - n * 0.012, 0.03, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "javelin_thrower"
ROOT_NAME = "JavelinThrowerHQ"
TEX_PREFIX = "javelin"
MAT_NAME = "JavelinMat"
MESH_NAME = "Javelineer"
BASE_MODULE = "javelin_base"
ANIM_MODULE = "anim_javelin"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Moustache", "Gold", "Tunic", "Trousers", "Leather", "Quiver", "Javelin"]
REGION_PARTS = ("Skin", "Tunic", "Quiver", "Javelin")
LIMED = {"name": "HQ_LimedHair", "base": (0.86, 0.8, 0.64), "hi": (0.98, 0.96, 0.9), "low": (0.5, 0.42, 0.28),
         "streak": (0.66, 0.58, 0.42), "tint": (0.8, 0.7, 0.5)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_JavSkin", "base": (0.86, 0.64, 0.5), "ruddy": (0.88, 0.5, 0.4), "lips": (0.7, 0.42, 0.36),
                      "brow": ((0.52, 0.4, 0.22), (0.72, 0.58, 0.34)), "paint": (0.1, 0.22, 0.56),
                      "extra": ((LASH, (0.36, 0.27, 0.16), 0.5),)}),
    "Hair": ("hair", LIMED),
    "Moustache": ("hair", {"name": "HQ_JavMoustache", "base": (0.66, 0.48, 0.24), "hi": (0.88, 0.72, 0.42), "low": (0.34, 0.22, 0.1),
                           "streak": (0.48, 0.32, 0.14), "tint": (0.72, 0.52, 0.26)}),
    "Gold": ("gold", {"name": "HQ_JavGold"}),
    "Tunic": ("plaid", {"name": "HQ_JavTunic"}),
    "Trousers": ("plaid", {"name": "HQ_JavTrousers", "base": (0.46, 0.2, 0.11), "stripe": (0.14, 0.3, 0.16),
                           "line": (0.84, 0.7, 0.3), "border": (0.14, 0.3, 0.16), "period": 0.1}),
    "Leather": ("leather", {"name": "HQ_JavLeather", "base": (0.38, 0.23, 0.12)}),
    "Quiver": ("javelin_case", {"name": "HQ_JavCase"}),
    "Javelin": ("javelin_shaft", {"name": "HQ_Javelin"}),
}
LOW_TARGETS = {"Skin": 6400, "Hair": 1200, "Moustache": 260, "Teeth": 60, "Gold": 520, "Tunic": 2100, "Trousers": 1500,
               "Leather": 1800, "Quiver": 1100, "Javelin": 420}
AO_EXCLUDE = ["Javelin"]
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
    a0, ax = javelin_axis()
    return [("javelin", a0, a0 + ax * 0.3, "hand.R")]


def _rigid(ob, groups, v, w):
    for g in list(ob.vertex_groups):
        g.remove([v.index])
    _blend_add(ob, groups, v.index, w)


def gold_weights(ob, skin_ob, arm):
    """The torc rides on his chest; the buckle goes with the belt."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO)
    groups = {}
    for v in ob.data.vertices:
        if v.co.z > 1.3:
            _rigid(ob, groups, v, {"chest": 1.0})


def leather_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "forearm.R", "forearm.L", "hand.R", "hand.L",
                                                       "thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"})
    a, n = baldric_plane()
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if 1.0 < p.z < 1.54 and abs(float((np.array(p) - a) @ n)) < 0.05 and abs(p.x) < 0.36:
            _rigid(ob, groups, v, {"chest": 0.8, "spine": 0.2} if p.z < 1.25 else {"chest": 1.0})


def weight_rules():
    return {
        "Hair": ("rigid", "head"), "Moustache": ("rigid", "head"), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Gold": ("custom", gold_weights), "Leather": ("custom", leather_weights),
        "Tunic": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Trousers": ("transfer", TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Quiver": ("rigid", "chest"), "Javelin": ("rigid", "javelin"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Moustache") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Javelin":
        return 0.6
    if part == "Skin" and abs(c.x) > 0.6 and c.z < 1.0:
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0026 if fine else 0.0036),
        ("Moustache", moustache_field(), 0.0018 if fine else 0.0026),
        ("Gold", gold_field(), 0.0016 if fine else 0.0024),
        ("Tunic", tunic_field(), 0.0026 if fine else 0.0036),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Quiver", quiver_field(), 0.0022 if fine else 0.003),
        ("Javelin", javelin_field(), 0.0016 if fine else 0.0022),
    ]
