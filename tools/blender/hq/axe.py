"""The Axe Warrior (HQ tower, Iron Age). Rest pose = A-pose, facing -Y, feet at z=0; right side = -X.

A huge champion of a hill fort: his head shaved and painted with blue woad spirals, bushy red brows drawn down in a
glare, a broken nose, a big red beard split into two braids bound with iron rings; a shirt of iron mail to mid-thigh
with short sleeves, a wide leather belt with an iron buckle; a wolf pelt over his shoulders pinned at his chest with an
iron ring brooch; blue-and-green checked trousers, leather shoes bound with thongs to his knees; iron rings round his
upper arms. Both fists on the haft of a great two-handed axe: a long ash haft bound with leather, a broad bearded iron
blade and a spike behind it.

The axe is rigid on the `axe` bone in his right fist (his lower hand, near the butt); anim_axe.py closes his left fist
on the haft above it in every pose."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add

J = {
    "root": (0.0, 0.03, 0.8),
    "spine": (0.0, 0.03, 0.96),
    "chest": (0.0, 0.05, 1.17),
    "neck": (0.0, 0.065, 1.41),
    "head": (0.0, 0.02, 1.53),
    "head_end": (0.0, -0.02, 1.93),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.37, 0.07, 1.37)
    J["elbow_" + _s] = (_x * 0.6, 0.1, 1.1)
    J["wrist_" + _s] = (_x * 0.75, 0.04, 0.86)
    J["hip_" + _s] = (_x * 0.165, 0.04, 0.75)
    J["knee_" + _s] = (_x * 0.185, 0.0, 0.42)
    J["ankle_" + _s] = (_x * 0.195, 0.06, 0.11)
    J["toe_" + _s] = (_x * 0.215, -0.17, 0.035)
J = {k: v3(v) for k, v in J.items()}

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, SCAR = 0, 1, 2, 3, 4, 5, 8, 9

HS = 1.08
DZ = -0.03
HPIV = v3((0.0, 0.02, 1.47))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


def hinv(P):
    return (P - HPIV.astype(F)) / F(HS) + HPIV.astype(F) - np.array([0, 0, DZ], F)


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.182, 0.194, 0.19)) * HS
EYE_R = hr(0.035)


def eye_c(sx):
    return hp((sx * 0.07, -0.148, 1.676))


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


HAND_S = 1.08
CURLS = {"R": (1.45, 1.6, 1.2), "L": (1.45, 1.6, 1.2)}          # both fists round the haft


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
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
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.011, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.016 * s), 0.009, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.012, (0.012, 0.007, 0.015), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.052 * s + n * 0.011
    d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
    d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
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
    fd.add(E((0, -0.05, 1.59), (0.156, 0.14, 0.13)), 0.07, SKIN)                            # a heavy jaw (under the beard)
    fd.add(E((0, -0.134, 1.5), (0.092, 0.074, 0.07)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.118, -0.124, 1.632), 0.054), 0.05, SKIN)
        fd.add(S((sx * 0.132, -0.045, 1.556), 0.054), 0.05, SKIN)
        pts = [hp((sx * 0.158, -0.055, 1.744)), hp((sx * 0.12, -0.136, 1.758)), hp((sx * 0.062, -0.18, 1.756)), hp((0.0, -0.19, 1.752))]
        fd.add(Chain(pts, [hr(0.014), hr(0.023), hr(0.027), hr(0.026)], k=hr(0.022)), hr(0.034), SKIN)     # a heavy brow ridge
    # bushy brows drawn down to the nose: a glare
    for sx in (-1, 1):
        pts = [hp((sx * 0.024, -0.214, 1.752)), hp((sx * 0.066, -0.209, 1.771)), hp((sx * 0.112, -0.188, 1.784)), hp((sx * 0.156, -0.146, 1.784))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.011), hr(0.0135), hr(0.012), hr(0.006)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.022), hr(0.025), hr(0.022), hr(0.012)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.007)), Plane(ec + v3((0, 0, hr(0.013))), (sx * 0.28, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.006)), Plane(ec + v3((0, 0, -hr(0.022))), (sx * -0.14, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.011))), (sx * 0.28, 0.06, -1.0)), hr(0.002)), LASH)
    # a broad nose, broken once (a kink in the bridge)
    fd.add(RoundCone(hp((0, -0.188, 1.726)), hp((0.008, -0.226, 1.682)), hr(0.02), hr(0.023)), hr(0.016), SKIN)
    fd.add(RoundCone(hp((0.008, -0.226, 1.682)), hp((-0.004, -0.242, 1.632)), hr(0.023), hr(0.027)), hr(0.016), SKIN)
    fd.add(S((-0.004, -0.242, 1.62), 0.03), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.038 - 0.004, -0.22, 1.606), 0.025), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.02 - 0.004, -0.238, 1.596)), v3((0.01, 0.012, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # mouth: set hard (mostly in the beard)
    slot = [hp((-0.056, -0.168, 1.55)), hp((-0.03, -0.192, 1.546)), hp((0, -0.198, 1.546)), hp((0.03, -0.192, 1.546)), hp((0.056, -0.168, 1.55))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.183, 0.035, 1.664)), v3((0.028, 0.05, 0.064)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.203, 0.028, 1.668)), v3((0.012, 0.032, 0.042)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
    # an old scar from his left brow down across his cheek
    sc = [hp((0.08, -0.2, 1.8)), hp((0.1, -0.19, 1.74)), hp((0.118, -0.17, 1.66)), hp((0.125, -0.15, 1.61))]
    fd.paint(Chain(sc, [hr(0.007), hr(0.008), hr(0.007), hr(0.005)], k=hr(0.004)), SCAR)
    fd.sub(Chain([p + v3((0, -0.004, 0)) for p in sc], [hr(0.0018)] * 4, k=hr(0.002)), hr(0.002))


def scalp_woad(fd):
    """Woad on his shaved head: three spirals round the crown, joined at the middle (a triskele), and a line from each
    down the back of his head."""
    sk = skull()
    top = HEAD_C + v3((0, 0.02, HEAD_RAD[2]))
    for arm in range(3):
        a0 = 2 * math.pi * arm / 3 + 0.3
        c = top + v3((math.cos(a0), math.sin(a0), 0)) * 0.075
        pts = []
        for k in range(26):
            th = k / 25.0 * 2.0 * 2 * math.pi
            r = 0.006 + 0.0058 * th
            q = c + v3((math.cos(a0 + th + math.pi), math.sin(a0 + th + math.pi), 0)) * r
            h, ok = ray_hit(sk, [q + v3((0, 0, 0.3))], [v3((0, 0, -1))], tmax=0.5)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 4:
            fd.paint(Chain(pts, [0.0068] * len(pts), k=0.003), PAINT)
        # a line down the back of his head from it
        line = []
        for k in range(10):
            u = k / 9.0
            ang = a0 + math.pi * 0.0
            d = norm(v3((math.cos(ang) * (0.3 + 0.7 * u), math.sin(ang) * (0.3 + 0.7 * u) + 0.6 * u, 1.0 - 1.1 * u)))
            h, ok = ray_hit(sk, [HEAD_C + d * 0.5], [-d], tmax=0.6)
            if ok[0] and float(h[0][1]) > float(HEAD_C[1]) - 0.06:
                line.append(h[0])
        if len(line) > 3:
            fd.paint(Chain(line, [0.006] * len(line), k=0.003), PAINT)


# ======================================================================================= body (huge)
def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.18), (0.29, 0.235, 0.28), R=euler(-0.1, 0, 0)), 0.0),
        (Ellipsoid((0, 0.12, 1.23), (0.325, 0.165, 0.215)), 0.06),
        (Ellipsoid((0.135, -0.145, 1.25), (0.145, 0.062, 0.092), R=euler(0.1, 0, 0.18)), 0.045),
        (Ellipsoid((-0.135, -0.145, 1.25), (0.145, 0.062, 0.092), R=euler(0.1, 0, -0.18)), 0.045),
        (Ellipsoid((0, -0.04, 0.98), (0.245, 0.215, 0.215)), 0.08),
        (Ellipsoid((0, 0.045, 0.8), (0.25, 0.19, 0.16)), 0.08),
    ]


def traps():
    return Ellipsoid((0, 0.1, 1.4), (0.26, 0.145, 0.104), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.065, 1.35), hp((0, 0.02, 1.575)), 0.115, hr(0.094))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.025, -0.005, 0.014)), 0.122)


def upper_arm(side):
    return RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.11, 0.084)


def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.085, 0.062)


def bicep(side):
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    return Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.03, 0)), (0.104, 0.108, 0.138), R=rot_from_axes(z_axis=el - sh))


def leg_prims(side):
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(hip, kn, 0.145, 0.095), 0.065),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.134, 0.124, 0.195), R=rot_from_axes(z_axis=kn - hip)), 0.048),
            (Sphere(kn + v3((0, -0.03, 0.0)), 0.074), 0.038),
            (RoundCone(kn, an, 0.09, 0.06), 0.038),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.103, 0.1, 0.148), R=rot_from_axes(z_axis=an - kn)), 0.043)]


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        el, wr = J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        fd.add(upper_arm(side), 0.05, SKIN)
        fd.add(bicep(side), 0.04, SKIN)
        fd.add(_forearm(side), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.108, 0.097, 0.144), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.062), 0.028, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)
    scalp_woad(fd)


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
        fd.add(RoundBox(hp((sx * 0.009, -0.178, 1.549)), v3((0.008, 0.006, 0.007)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= beard
def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.05, 1.59), (0.156, 0.14, 0.13)), 0.07)
    fd.add(E((0, -0.134, 1.5), (0.092, 0.074, 0.07)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.118, -0.124, 1.632)), hr(0.054)), 0.05)
        fd.add(Sphere(hp((sx * 0.132, -0.045, 1.556)), hr(0.054)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


BEARD_LOW = 1.43


def curls(P, scale, amp):
    return F(amp) * NOISE(P / F(scale)) + F(amp * 0.5) * NOISE(P / F(scale * 0.45) + F(3.1))


def braid_paths():
    """The beard's two braids: from under his chin down onto his chest, a little apart, the ends swinging out."""
    out = []
    for sx in (-1, 1):
        a = hp((sx * 0.045, -0.2, 1.44))
        pts = [a]
        for k in range(1, 8):
            u = k / 7.0
            pts.append(a + v3((sx * (0.012 * k + 0.004 * k * k * 0.3), -0.035 * u - 0.03 * u * u, -0.045 * k)))
        out.append(pts)
    return out


def beard_field():
    """A big full beard over his cheeks and jaw, thick under his chin; a heavy moustache merging into it; below his chin it
    splits into two thick braids that hang onto his chest, each tied off in an iron ring (Iron)."""
    fd = Field("Beard")
    hull = head_hull()
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.585) + F(0.06) * smoothstep(0.075, 0.16, ax) + F(0.075) * smoothstep(0.135, 0.175, ax) * smoothstep(-0.11, -0.04, y)
        lips = (x / F(0.07)) ** 2 + ((y + F(0.18)) / F(0.06)) ** 2 + ((z - F(1.548)) / F(0.026)) ** 2 - F(1.0)
        back = np.where(ax > F(0.14), y - F(0.04), y - F(0.0))
        return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), F(BEARD_LOW) - z)
    cur = lambda P: curls(P, 0.022, 0.008)
    fd.add(Inter(Shell(hull, 0.016, 0.036, pad=0.06, disp=cur, disp_amp=0.01), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.012), 0.0)
    fd.add(Ellipsoid(hp((0, -0.16, 1.47)), v3((0.13, 0.085, 0.08)) * HS, disp=cur, disp_amp=0.01), 0.045)
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.234, 1.59)), hp((sx * 0.046, -0.222, 1.58)), hp((sx * 0.082, -0.196, 1.56)), hp((sx * 0.1, -0.17, 1.53))]
        fd.add(Lock(pts, [hr(0.017), hr(0.022), hr(0.019), hr(0.012)], [hr(0.012), hr(0.014), hr(0.012), hr(0.008)],
                    [norm(v3((sx * 0.25, -1, 0.35)))] * 4, k=hr(0.007), disp=lambda P: curls(P, 0.012, 0.003), disp_amp=0.004), hr(0.006))
    for pts in braid_paths():
        for k in range(len(pts) - 1):
            a, b = pts[k], pts[k + 1]
            d = norm(b - a)
            for j, u in enumerate((0.0, 0.5)):
                c = lerp(a, b, u)
                side = norm(np.cross(d, v3((0, 1, 0))))
                tilt = 0.5 if (k * 2 + j) % 2 == 0 else -0.5
                ax = norm(d + side * tilt)
                r = 0.03 - 0.012 * (k + u) / (len(pts) - 1)
                fd.add(Ellipsoid(c, (r, r * 0.8, r * 1.7), R=rot_from_axes(z_axis=ax, y_axis=v3((0, 1, 0))), disp=strands, disp_amp=0.003), 0.006)
        end = pts[-1]
        dd = norm(pts[-1] - pts[-2])
        fd.add(Ellipsoid(end + dd * 0.035, (0.018, 0.014, 0.034), R=rot_from_axes(z_axis=dd, y_axis=v3((0, 1, 0))), disp=strands, disp_amp=0.003), 0.006)
    return fd


def braid_ties():
    return [(pts[-1] - norm(pts[-1] - pts[-2]) * 0.004, norm(pts[-1] - pts[-2])) for pts in braid_paths()]


# ======================================================================================= mail, pelt
BELT_Z = 0.95
HEM_Z = 0.58


def mail_base():
    b = Field("MailBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(RoundCone((0, 0.035, 0.9), (0, 0.035, 0.48), 0.25, 0.32), 0.08)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.055)
        b.add(upper_arm(side), 0.05)
        b.add(bicep(side), 0.04)
    return b


def _neck_cut(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
    neck_z = F(1.47) - F(0.05) * front * np.exp(-(x / F(0.13)) ** 2)
    return z - neck_z


def _sleeve_cut(P):
    """> 0 past the short sleeves (40% down the upper arm)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        c = lerp(sh, el, 0.42)
        along = (P - c.astype(F)) @ ax.astype(F)
        sx = -1 if side == "R" else 1
        lateral = P[:, 0] * F(sx) - F(0.3)                       # (only out on the arm)
        out = np.maximum(out, np.where(lateral > 0, along, F(-1.0)))
    return out


def hem_z(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(HEM_Z) + F(0.018) * np.cos(a * 2) + F(0.006) * NOISE(P * F(10))


def mail_field():
    """A shirt of iron mail from his neck to mid-thigh with short sleeves, gathered at the belt; a band of bronze rings
    (label 5) round the hem and the sleeves' ends."""
    fd = Field("Mail")
    base = mail_base()
    def shell(P):
        d = base.eval(P, margin=0.1)
        z = P[:, 2]
        below = np.clip((F(BELT_Z) - z) / F(0.12), 0, 1)
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        folds = F(0.006) * np.sin(a * F(11)) * below + F(0.003) * NOISE(P * F(12))
        off = F(0.028) - F(0.012) * np.exp(-((z - F(BELT_Z)) / F(0.05)) ** 2) + folds + F(0.01) * below
        return np.abs(d - off) - F(0.009)
    def keep(P):
        return np.maximum(np.maximum(_neck_cut(P), _sleeve_cut(P)), hem_z(P) - P[:, 2])
    lo, hi = (-0.8, -0.5, 0.4), (0.8, 0.5, 1.62)
    fd.add(Inter(Func(shell, lo, hi), Func(keep, lo, hi), 0.004), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (hem_z(P) + F(0.035)), (-0.6, -0.6, 0.4), (0.6, 0.6, 0.7)), 5)
    fd.paint(Func(lambda P: np.maximum(-_sleeve_cut(P) - F(0.035), F(1.0) - P[:, 2]), (-0.9, -0.5, 1.0), (0.9, 0.5, 1.5)), 5)
    return fd


def pelt_field():
    """A wolf pelt over his shoulders and down his back, ragged at the edges, pinned at his chest."""
    fd = Field("Pelt")
    base = mail_base()
    fur = lambda P: F(0.006) * NOISE(P * np.array([30, 30, 14], F)) + F(0.004) * NOISE(P * F(60))
    def edge_z(P):
        y = P[:, 1]
        a = np.arctan2(P[:, 0], P[:, 1])
        backness = np.clip((y + F(0.02)) / F(0.2), 0, 1)
        return F(1.33) - F(0.36) * backness + F(0.03) * np.sin(a * F(9)) + F(0.02) * NOISE(P * F(9))
    def keep(P):
        x, z = P[:, 0], P[:, 2]
        arm_cut = np.abs(x) - F(0.5)                            # (it hangs over the shoulders, not down the arms)
        return np.maximum(np.maximum(edge_z(P) - z, z - F(1.56)), arm_cut)
    fd.add(Inter(Shell(base, 0.06, 0.04, pad=0.12, disp=fur, disp_amp=0.008), Func(keep, (-0.7, -0.5, 0.7), (0.7, 0.5, 1.7)), 0.01), 0.0)
    # the rolled collar round his neck
    fd.add(Inter(Shell(base, 0.075, 0.05, pad=0.12, disp=fur, disp_amp=0.008),
                 Func(lambda P: np.maximum(np.abs(_neck_cut(P) + F(0.02)) - F(0.035), F(1.38) - P[:, 2]), (-0.5, -0.5, 1.2), (0.5, 0.5, 1.7)), 0.01), 0.01)
    return fd


# ======================================================================================= trousers, leather
def legs_base():
    b = Field("LegsBase")
    b.add(torso_prims()[5][0], 0.0)
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            b.add(p, k)
    return b


def trousers_field():
    fd = Field("Trousers")
    base = legs_base()
    def shell(P):
        d = base.eval(P, margin=0.08)
        z = P[:, 2]
        creases = F(0.006) * NOISE(P * np.array([10, 10, 30], F)) + F(0.003) * NOISE(P * F(25))
        off = F(0.025) + creases + F(0.006) * np.clip((F(0.5) - z) / F(0.3), 0, 1)
        return np.abs(d - off) - F(0.008)
    an_z = float(J["ankle_R"][2])
    keep = lambda P: np.maximum(P[:, 2] - F(0.97), F(an_z + 0.05) - P[:, 2])
    lo, hi = (-0.48, -0.42, 0.0), (0.48, 0.42, 1.02)
    fd.add(Inter(Func(shell, lo, hi), Func(keep, lo, hi), 0.004), 0.0)
    return fd


def shoe_hull(side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.12)
    fwd = Rz @ v3((0, -1, 0))
    f = Field("ShoeHull")
    f.add(Sphere(an + v3((0, 0.04, -0.05)), 0.064), 0.0)
    f.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.068)), (0.07, 0.13, 0.037), 0.035, R=Rz), 0.04)
    f.add(Ellipsoid(an + fwd * 0.17 + v3((0, 0, -0.072)), (0.066, 0.062, 0.037), R=Rz), 0.03)
    f.add(Cylinder(an + v3((0, 0.005, 0.02)), 0.07, 0.1, rr=0.03), 0.04)
    return f, fwd, Rz


def leg_axis_point(side, z):
    kn, an = J["knee_" + side], J["ankle_" + side]
    u = (kn[2] - z) / (kn[2] - an[2])
    return lerp(kn, an, u)


def leather_field():
    """A wide belt, bracers on both forearms, shoes, and thongs criss-crossing up his shins."""
    fd = Field("Leather")
    mb = mail_base()
    fd.add(Func(lambda P: np.maximum(np.abs(mb.eval(P, margin=0.08) - F(0.032)) - F(0.014), np.abs(P[:, 2] - F(BELT_Z)) - F(0.042)),
                (-0.5, -0.45, 0.85), (0.5, 0.45, 1.06)), 0.0)
    for side in ("L", "R"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.66)
        fd.add(Inter(Shell(_forearm(side), 0.013, 0.017, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.08), c - 0.25, c + 0.25), 0.004), 0.0)
        for j in (-1, 0, 1):
            cc = c + ax * (j * 0.05)
            fd.add(Inter(Shell(_forearm(side), 0.022, 0.006, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.006), cc - 0.2, cc + 0.2), 0.002), 0.003)
    for side in ("R", "L"):
        an = J["ankle_" + side]
        sh, fwd, Rz = shoe_hull(side)
        top = an[2] + 0.08
        fd.add(Inter(Shell(sh, 0.0, 0.028, pad=0.06), Func(lambda P, top=top: P[:, 2] - F(top), an - 0.35, an + 0.35), 0.006), 0.0)
        fd.add(RoundBox(an + fwd * 0.085 + v3((0, 0, -0.1)), (0.08, 0.165, 0.013), 0.01, R=Rz), 0.008)
        fd.add(Torus(an + v3((0, 0.006, 0.077)), 0.072, 0.012), 0.004)
        leg = Field("LegHull")
        for p, k in leg_prims(side):
            leg.add(p, k)
        z0, z1 = an[2] + 0.075, J["knee_" + side][2] - 0.07
        surf = Func(lambda P, leg=leg: leg.eval(P, margin=0.06) - F(0.035), an - 0.4, J["knee_" + side] + 0.4)
        for hand_dir in (1, -1):
            pts = []
            for k in range(24):
                u = k / 23.0
                z = z0 + (z1 - z0) * u
                c = leg_axis_point(side, z)
                th = hand_dir * u * 2.0 * 2 * math.pi + (0.0 if hand_dir > 0 else math.pi)
                d = v3((math.cos(th), math.sin(th), 0.0))
                h, ok = ray_hit(surf, [c + d * 0.35], [-d], tmax=0.4)
                if ok[0]:
                    pts.append(h[0])
            if len(pts) > 4:
                fd.add(Chain(pts, [0.0072] * len(pts), k=0.003), 0.003)
    return fd


# ======================================================================================= iron: buckle, brooch, arm rings, braid rings
def iron_field():
    fd = Field("Iron")
    mb = mail_base()
    h, ok = ray_hit(Func(lambda P: mb.eval(P, margin=0.1) - F(0.05), (-0.5, -0.6, 0.8), (0.5, 0.5, 1.1)), [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    c = h[0]
    fd.add(RoundBox(c + v3((0, -0.006, 0)), (0.05, 0.012, 0.04), 0.01), 0.0)                    # the buckle's plate
    fd.add(Torus(c + v3((0, -0.016, 0)), 0.028, 0.008, R=rot_from_axes(z_axis=(0, 1, 0))), 0.004)
    # a ring brooch pinning the pelt at his chest, its pin across it
    pb = pelt_field()
    h2, ok2 = ray_hit(Func(lambda P: pb.eval(P, margin=0.1) - F(0.004), (-0.5, -0.6, 1.1), (0.5, 0.5, 1.5)), [v3((0.0, -0.7, 1.36))], [v3((0, 1, 0))], tmax=0.8)
    if ok2[0]:
        b = h2[0] + v3((0, -0.01, 0))
        fd.add(Torus(b, 0.045, 0.011, R=rot_from_axes(z_axis=(0, 0.35, 1.0)) @ euler(math.pi / 2, 0, 0)), 0.0)
        fd.add(RoundCone(b + v3((-0.055, -0.008, 0.03)), b + v3((0.06, -0.008, -0.034)), 0.008, 0.005), 0.004)
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        for u, rr in ((0.6, 0.0), (0.68, 0.0)):
            c2 = lerp(sh, el, u)
            rad = 0.11 - 0.022 * u + 0.016
            fd.add(Torus(c2, rad, 0.011, R=rot_from_axes(z_axis=ax)), 0.004)
    for t, d in braid_ties():
        fd.add(Torus(t, 0.02, 0.008, R=rot_from_axes(z_axis=d)), 0.003)
    return fd


# ======================================================================================= the axe
AXE_FWD = 0.98          # grip -> the head's top edge, along the haft
AXE_BACK = 0.2          # grip -> the butt
AXE_R = 0.021


def axe_frame():
    """Rest pose: the grip (in his right fist), the haft along the fist's thumb axis A (toward the head), the blade's
    edge facing B (the fist's knuckles, as a hammer's face)."""
    wr, f, n, t = hand_frame("R")
    A = norm(t)
    B = norm(f - A * (f @ A))
    return fist_center("R"), A, B


def axe_field():
    """An ash haft (label 0) bound with leather (5) below the head and at the butt; a broad bearded iron blade (6), its
    edge bright, a spike behind it, an iron butt knob."""
    fd = Field("Axe")
    G, A, B = axe_frame()
    S = norm(np.cross(A, B))
    grain = lambda P: F(0.0018) * NOISE(P * F(70))
    fd.add(Chain([G - A * (AXE_BACK - 0.03), G + A * (AXE_FWD - 0.02)], [AXE_R, AXE_R * 0.92], k=0.0, disp=grain, disp_amp=0.002), 0.0)
    fd.add(Sphere(G - A * AXE_BACK, AXE_R * 1.45), 0.006, 6)                                         # butt knob
    for k in range(6):                                                                           # leather wraps
        fd.add(Torus(G - A * (0.06 + 0.017 * k), AXE_R + 0.003, 0.0055, R=rot_from_axes(z_axis=A)), 0.002, 5)
        fd.add(Torus(G + A * (AXE_FWD - 0.34 - 0.017 * k), AXE_R + 0.003, 0.0055, R=rot_from_axes(z_axis=A)), 0.002, 5)
    # the head: an eye round the haft, a long beard of blade sweeping down, a spike behind
    hc = G + A * (AXE_FWD - 0.12)
    fd.add(RoundBox(hc, (0.036, 0.04, 0.09), 0.012, R=rot_from_axes(x_axis=S, y_axis=B)), 0.006, 6)
    def blade(P):
        q = P - hc.astype(F)
        u = q @ B.astype(F)                                   # out toward the edge
        v = q @ A.astype(F)                                   # along the haft (up)
        w = q @ S.astype(F)                                   # through the blade
        # the outline: from the eye the blade widens to a curved edge 0.3 tall, its lower horn (the beard) sweeping down
        top = F(0.07) + F(0.05) * np.clip(u / F(0.24), 0, 1) ** 2
        bot = F(-0.06) - F(0.17) * np.clip(u / F(0.24), 0, 1) ** 1.6
        edge = F(0.25) + F(0.035) * np.cos(np.clip((v + F(0.04)) / F(0.2), -1.4, 1.4))
        d2 = np.maximum(np.maximum(v - top, bot - v), np.maximum(u - edge, F(0.02) - u))
        thick = F(0.012) * (F(1.0) - F(0.75) * np.clip(u / F(0.25), 0, 1))
        return np.maximum(d2, np.abs(w) - thick)
    fd.add(Func(blade, hc - 0.4, hc + 0.4), 0.008, 6)
    fd.add(RoundCone(hc - B * 0.03, hc - B * 0.15 + A * 0.01, 0.03, 0.004), 0.008, 6)              # the spike behind
    return fd


def axe_edge():
    """The blade's edge middle (rest pose), for game.gd's arc."""
    G, A, B = axe_frame()
    return G + A * (AXE_FWD - 0.14) + B * 0.27


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.242, 1.62)), 0.05, 0.6)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.1, -0.15, 1.64)), 0.06, 0.5), (hp((sx * 0.183, 0.035, 1.664)), 0.05, 0.55),
                (J["elbow_" + sd] + v3((0, 0.025, 0)), 0.065, 0.3), (J["knee_" + sd] + v3((0, -0.03, 0)), 0.075, 0.35),
                (J["shoulder_" + sd] + v3((0, 0, 0.1)), 0.12, 0.3), (HEAD_C + v3((0, 0, HEAD_RAD[2])), 0.12, 0.25)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.044, 0.0148, -0.0148, -0.044):
            pts.append((wr + f * 0.138 * HAND_S + t * o - n * 0.012, 0.03, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "axe_warrior"
ROOT_NAME = "AxeWarriorHQ"
TEX_PREFIX = "axe"
MAT_NAME = "AxeMat"
MESH_NAME = "AxeWarrior"
BASE_MODULE = "axe_base"
ANIM_MODULE = "anim_axe"
PARTS = ["Skin", "Eyes", "Teeth", "Beard", "Mail", "Pelt", "Trousers", "Leather", "Iron", "Axe"]
REGION_PARTS = ("Skin", "Mail", "Axe")
RED = {"name": "HQ_AxeBeard", "base": (0.62, 0.25, 0.1), "hi": (0.9, 0.5, 0.24), "low": (0.3, 0.1, 0.04),
       "streak": (0.42, 0.15, 0.06), "tint": (0.72, 0.32, 0.12)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_AxeSkin", "base": (0.86, 0.62, 0.48), "ruddy": (0.9, 0.48, 0.38), "lips": (0.68, 0.38, 0.32),
                      "brow": ((0.5, 0.18, 0.06), (0.74, 0.34, 0.12)), "paint": (0.1, 0.22, 0.56),
                      "extra": ((LASH, (0.4, 0.16, 0.07), 0.5), (SCAR, (0.94, 0.66, 0.58), 0.5, 0.85))}),
    "Beard": ("hair", RED),
    "Mail": ("mail", {"name": "HQ_Mail"}),
    "Pelt": ("fur", {"name": "HQ_WolfPelt", "base": (0.44, 0.4, 0.36), "tip": (0.72, 0.68, 0.62)}),
    "Trousers": ("plaid", {"name": "HQ_AxeTrousers", "base": (0.16, 0.24, 0.42), "stripe": (0.18, 0.4, 0.2),
                           "line": (0.86, 0.8, 0.6), "border": (0.18, 0.4, 0.2), "period": 0.1}),
    "Leather": ("leather", {"name": "HQ_AxeLeather", "base": (0.34, 0.2, 0.1)}),
    "Iron": ("iron", {"name": "HQ_AxeIron"}),
    "Axe": ("javelin_shaft", {"name": "HQ_Axe"}),
}
LOW_TARGETS = {"Skin": 6600, "Beard": 1500, "Teeth": 60, "Mail": 2600, "Pelt": 1500, "Trousers": 1500, "Leather": 1800,
               "Iron": 700, "Axe": 900}
AO_EXCLUDE = ["Axe"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.72, 0.88, 1.06, 1.45)


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.91), (0, 0.045, 1.12)),
        "chest": ((0, 0.045, 1.12), (0, 0.065, 1.38)),
        "neck": ((0, 0.065, 1.38), hp((0, 0.02, 1.56))),
        "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.37,
    }


def prop_bones():
    G, A, B = axe_frame()
    return [("axe", G, G + A * 0.3, "hand.R")]


def _rigid(ob, groups, v, w):
    for g in list(ob.vertex_groups):
        g.remove([v.index])
    _blend_add(ob, groups, v.index, w)


def beard_weights(ob, skin_ob, arm):
    """The beard goes with his head and jaw; the braids swing from his chin down onto his chest."""
    groups = {}
    z1 = hp((0, 0, 1.45))[2]
    for v in ob.data.vertices:
        p = v.co
        if p.z >= z1:
            _blend_add(ob, groups, v.index, {"head": 1.0})
        else:
            t = max(0.0, min(1.0, (z1 - p.z) / 0.3))
            _blend_add(ob, groups, v.index, {"head": 1.0 - 0.7 * t, "neck": 0.4 * t, "chest": 0.3 * t})


def iron_weights(ob, skin_ob, arm):
    """The buckle with the belt, the brooch with his chest, the arm rings with his upper arms, the braid rings with the
    braids."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"upperarm.R", "upperarm.L"})
    groups = {}
    ties = braid_ties()
    for v in ob.data.vertices:
        p = v.co
        for t, d in ties:
            if (p - _vec(t)).length < 0.04:
                z1 = hp((0, 0, 1.45))[2]
                tt = max(0.0, min(1.0, (z1 - p.z) / 0.3))
                _rigid(ob, groups, v, {"head": 1.0 - 0.7 * tt, "neck": 0.4 * tt, "chest": 0.3 * tt})
                break
        else:
            if 1.25 < p.z < 1.5 and abs(p.x) < 0.12 and p.y < -0.1:
                _rigid(ob, groups, v, {"chest": 1.0})


def _vec(p):
    from mathutils import Vector
    return Vector((float(p[0]), float(p[1]), float(p[2])))


def weight_rules():
    return {
        "Beard": ("custom", beard_weights), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Mail": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L"},
                 {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Pelt": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"}, {"upperarm.R": 0.3, "upperarm.L": 0.3}),
        "Trousers": ("transfer", TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Leather": ("transfer", TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Iron": ("custom", iron_weights), "Axe": ("rigid", "axe"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and abs(c.x) < 0.3:
        return 1.9
    if part == "Beard" and c.z > face_z:
        return 1.4
    if part == "Axe":
        return 0.8
    if part == "Skin" and abs(c.x) > 0.6 and c.z < 1.0:
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Beard", beard_field(), 0.0024 if fine else 0.0034),
        ("Mail", mail_field(), 0.0026 if fine else 0.0036),
        ("Pelt", pelt_field(), 0.0028 if fine else 0.0038),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Iron", iron_field(), 0.0018 if fine else 0.0026),
        ("Axe", axe_field(), 0.0018 if fine else 0.0026),
    ]
