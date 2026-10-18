"""Ugo the Firstborn, Sling Champion (HQ hero). Rest pose = A-pose, facing -Y, feet at z=0; right side = -X.

A heroic build (V-shaped torso, square jaw, red war paint, full dark beard) wearing a sabertooth pelt: the cat's head
is his hood (amber stones for eyes, saber fangs framing his face), its hide hangs down his back as a cape and its
forelegs come over his shoulders, the paws tied across his chest. Spotted fur loincloth, wide belt with a bone buckle,
leather bracers, a stone pouch on the hip and a champion's sling with red tassels."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, grad, project_to, flow_line, Stone, lerp, hem_cut

J = {
    "root": (0.0, 0.03, 0.86),
    "spine": (0.0, 0.03, 1.04),
    "chest": (0.0, 0.05, 1.26),
    "neck": (0.0, 0.07, 1.5),
    "head": (0.0, 0.02, 1.63),
    "head_end": (0.0, -0.02, 2.04),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.42, 0.07, 1.46)
    J["elbow_" + _s] = (_x * 0.66, 0.10, 1.18)
    J["wrist_" + _s] = (_x * 0.84, 0.04, 0.93)
    J["hip_" + _s] = (_x * 0.155, 0.04, 0.80)
    J["knee_" + _s] = (_x * 0.185, 0.0, 0.45)
    J["ankle_" + _s] = (_x * 0.195, 0.06, 0.115)
    J["toe_" + _s] = (_x * 0.215, -0.17, 0.035)
J = {k: v3(v) for k, v in J.items()}

# skin labels
SKIN, NAIL, LIP, MOUTH, BROW, PAINT = 0, 1, 2, 3, 4, 5
# sabertooth pelt labels (hood + cape share one material)
FUR, MUZZLE, NOSEPAD, AMBER, INNER, SUEDE, PAD = 0, 6, 7, 8, 9, 10, 11

# head: designed in the Rock Slinger's head coordinates, lifted DZ and scaled HS about the top of the neck
HS = 1.08
DZ = 0.075
HPIV = v3((0.0, 0.02, 1.595))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.185, 0.195, 0.19)) * HS
EYE_R = hr(0.038)


def eye_c(sx):
    return hp((sx * 0.072, -0.148, 1.678))


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


def hand(fd, side, fist, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.078 * s
    fd.add(RoundBox(c, v3((0.066, 0.035, 0.068)) * s, 0.031 * s, R=Rp), 0.03, SKIN)
    fd.add(Ellipsoid(c - n * 0.012 + t * 0.032 - f * 0.01, v3((0.036, 0.031, 0.052)) * s, R=Rp), 0.02, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = (1.45, 1.6, 1.2) if fist else (0.3, 0.5, 0.35)
    offs = (0.045, 0.015, -0.015, -0.045)
    lens = (0.95, 1.0, 0.95, 0.8)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.144 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.023 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.012, SKIN)
        fd.add(Sphere(pts[0] - n * 0.012, 0.017 * s), 0.01, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.012, (0.013, 0.007, 0.015), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.047 * s + t * 0.054 * s + n * 0.012
    if fist:
        d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
        d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:
        d1 = norm(f * 0.55 + t * 0.75 + n * 0.25)
        d2 = norm(f * 0.8 + t * 0.35 + n * 0.45)
    p1 = tb + d1 * 0.052 * s
    p2 = p1 + d2 * 0.044 * s
    fd.add(Chain([tb, p1, p2], [0.027 * s, 0.024 * s, 0.021 * s], k=0.008), 0.02, SKIN)


def foot(fd, side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.12)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    fd.add(Sphere(an + v3((0, 0.045, -0.052)), 0.064), 0.03, SKIN)
    fd.add(RoundBox(an + fwd * 0.078 + v3((0, 0, -0.07)), (0.077, 0.125, 0.039), 0.037, R=Rz), 0.035, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.04 + v3((0, 0, -0.03)), (0.072, 0.092, 0.052), R=Rz), 0.03, SKIN)
    inner = -sx
    toes = [(0.057, 0.032), (0.023, 0.024), (-0.006, 0.022), (-0.032, 0.02), (-0.054, 0.018)]
    for i, (o, r) in enumerate(toes):
        base = an + fwd * (0.176 - 0.012 * i - (0.0 if i else -0.004)) + rgt * (o * inner) + v3((0, 0, -0.08))
        tip = base + fwd * (0.031 + r * 0.4) + v3((0, 0, -0.004))
        base[2] = 0.026 + r * 0.55
        tip[2] = 0.021 + r * 0.5
        fd.add(RoundCone(base, tip, r, r * 0.92), 0.012, SKIN)
        tn = norm(tip - base)
        fd.paint(Ellipsoid(tip + v3((0, 0, r * 0.55)), (r * 0.7, r * 0.75, r * 0.35), R=rot_from_axes(y_axis=tn, z_axis=(0, 0, 1))), NAIL)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.056, 0.0, 0.0)), 0.027), 0.02, SKIN)


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.05, 1.58), (0.188, 0.152, 0.138)), 0.07, SKIN)                        # square jaw mass
    fd.add(E((0, -0.13, 1.495), (0.118, 0.085, 0.074)), 0.05, SKIN)                       # strong chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.115, -0.123, 1.632), 0.058), 0.045, SKIN)                         # cheekbones
        fd.add(S((sx * 0.148, -0.04, 1.535), 0.074), 0.05, SKIN)                           # jaw corners
        pts = [hp((sx * 0.152, -0.05, 1.743)), hp((sx * 0.116, -0.125, 1.749)), hp((sx * 0.058, -0.172, 1.745)), hp((0.0, -0.183, 1.748))]
        fd.add(Chain(pts, [hr(0.018), hr(0.032), hr(0.038), hr(0.04)], k=hr(0.03)), hr(0.045), SKIN)
    fd.add(E((0, -0.165, 1.775), (0.07, 0.038, 0.048)), hr(0.04), SKIN)
    # bold brows, angled down to the nose: determined
    for sx in (-1, 1):
        pts = [hp((sx * 0.022, -0.218, 1.757)), hp((sx * 0.062, -0.207, 1.774)), hp((sx * 0.104, -0.182, 1.787)), hp((sx * 0.142, -0.146, 1.79)),
               hp((sx * 0.16, -0.122, 1.787))]
        brow = Chain(pts, [hr(0.019), hr(0.023), hr(0.021), hr(0.015), hr(0.005)], k=hr(0.012),
                     disp=lambda P: F(0.0025) * NOISE(P * np.array([30, 30, 90], F)), disp_amp=0.003)
        fd.add(brow, hr(0.012), BROW)
        fd.paint(Chain(pts, [hr(0.025), hr(0.029), hr(0.027), hr(0.02), hr(0.009)], k=hr(0.012)), BROW)
    # eyes: open, steady
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0085)), Plane(ec + v3((0, 0, hr(0.017))), (sx * 0.2, 0.12, -1.0)), hr(0.004))
        fd.add(up, hr(0.006), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0065)), Plane(ec + v3((0, 0, -hr(0.025))), (sx * -0.1, 0.1, 1.0)), hr(0.004))
        fd.add(lo, hr(0.006), SKIN)
    # big rounded nose
    fd.add(RoundCone(hp((0, -0.188, 1.712)), hp((0, -0.234, 1.628)), hr(0.027), hr(0.036)), hr(0.02), SKIN)
    fd.add(S((0, -0.246, 1.608), 0.05), hr(0.018), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.04, -0.218, 1.592), 0.029), hr(0.014), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.022, -0.238, 1.572)), v3((0.011, 0.014, 0.008)) * HS, R=euler(0.4, 0, sx * 0.3)), hr(0.005))
    # confident grin, his left corner higher
    slot = [hp((-0.08, -0.168, 1.535)), hp((-0.042, -0.199, 1.519)), hp((0, -0.212, 1.516)), hp((0.045, -0.199, 1.524)), hp((0.088, -0.166, 1.55))]
    fd.sub(Chain(slot, [hr(0.01), hr(0.017), hr(0.019), hr(0.017), hr(0.01)], k=hr(0.01)), hr(0.008))
    fd.paint(Chain(slot, [hr(0.01), hr(0.017), hr(0.02), hr(0.017), hr(0.01)], k=hr(0.01)), MOUTH)
    up_lip = [(-0.084, -0.162, 1.546), (-0.046, -0.198, 1.537), (0, -0.214, 1.534), (0.048, -0.198, 1.541), (0.092, -0.16, 1.562)]
    lo_lip = [(-0.077, -0.164, 1.522), (-0.04, -0.195, 1.5), (0, -0.206, 1.495), (0.045, -0.195, 1.505), (0.085, -0.162, 1.537)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.008), hr(0.012), hr(0.013), hr(0.012), hr(0.008)], k=hr(0.01)), hr(0.008), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.008), hr(0.011), hr(0.012), hr(0.011), hr(0.008)], k=hr(0.01)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.185, 0.035, 1.665)), v3((0.029, 0.052, 0.068)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
    # war paint: two red ochre stripes on each cheek, one over the bridge of the nose
    for sx in (-1, 1):
        for dz, w in ((0.0, 0.0115), (-0.038, 0.0105)):
            fd.paint(stripe2d((sx * 0.052, 1.712 + dz), (sx * 0.178, 1.738 + dz * 0.7), w, w * 0.75), PAINT)
    fd.paint(stripe2d((-0.034, 1.79), (0.034, 1.79), 0.0105, 0.0105), PAINT)


def stripe2d(a, b, ra, rb, y0=-0.34, y1=-0.04):
    """Face paint stroke drawn in the front (x/z) view and projected straight back onto the face."""
    a, b = np.array(a, F), np.array(b, F)
    ab = b - a
    L2 = F(ab @ ab)
    def fn(P):
        q = P[:, [0, 2]] - a
        t = np.clip((q @ ab) / L2, 0, 1)
        d = np.linalg.norm(q - t[:, None] * ab[None, :], axis=1) - (F(ra) + (F(rb) - F(ra)) * t)
        depth = np.maximum(F(y0) - P[:, 1], P[:, 1] - F(y1))
        return np.maximum(d, depth)
    lo = (min(a[0], b[0]) - 0.03, y0, min(a[1], b[1]) - 0.03)
    hi = (max(a[0], b[0]) + 0.03, y1, max(a[1], b[1]) + 0.03)
    return Func(fn, lo, hi)


# ======================================================================================= body
def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.29), (0.33, 0.25, 0.30), R=euler(-0.12, 0, 0)), 0.0),
        (Ellipsoid((0, 0.13, 1.33), (0.37, 0.19, 0.23)), 0.06),
        (RoundBox((0.142, -0.158, 1.39), (0.15, 0.036, 0.08), 0.034, R=euler(0.14, 0, 0.3)), 0.045),
        (RoundBox((-0.142, -0.158, 1.39), (0.15, 0.036, 0.08), 0.034, R=euler(0.14, 0, -0.3)), 0.045),
        (Ellipsoid((0, -0.01, 1.07), (0.2, 0.18, 0.19)), 0.08),
        (Ellipsoid((0, 0.045, 0.875), (0.245, 0.2, 0.17)), 0.08),
    ]


def traps():
    return Ellipsoid((0, 0.11, 1.52), (0.29, 0.15, 0.10), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.07, 1.47), hp((0, 0.02, 1.575)), 0.135, hr(0.11))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.025, -0.005, 0.015)), 0.152)


def handprint(P, c, s=1.0, U=(1.0, 0.0, 0.0), V=(0.0, 0.0, 1.0)):
    """2-D red ochre handprint centred at c in the plane spanned by U (across the palm) and V (toward the fingers),
    any depth: negative inside."""
    U, V = v3(U).astype(F), v3(V).astype(F)
    Q = P - v3(c).astype(F)
    x = (Q @ U) / F(s)
    z = (Q @ V) / F(s)
    d = np.sqrt((x / F(0.042)) ** 2 + (z / F(0.048)) ** 2) * F(0.042) - F(0.042)
    for ang, L, off in ((-0.32, 0.062, -0.03), (-0.1, 0.075, -0.011), (0.06, 0.08, 0.009), (0.24, 0.07, 0.028)):
        ax, az = math.sin(ang), math.cos(ang)
        x0, z0 = off, 0.035
        t = np.clip((x - F(x0)) * F(ax) + (z - F(z0)) * F(az), 0, L)
        dx = x - (F(x0) + t * F(ax))
        dz = z - (F(z0) + t * F(az))
        d = np.minimum(d, np.sqrt(dx * dx + dz * dz) - F(0.0125))
    ax, az = math.sin(-1.05), math.cos(-1.05)
    t = np.clip((x + F(0.035)) * F(ax) + (z + F(0.005)) * F(az), 0, 0.06)
    dx = x - (F(-0.035) + t * F(ax))
    dz = z - (F(-0.005) + t * F(az))
    d = np.minimum(d, np.sqrt(dx * dx + dz * dz) - F(0.014))
    return d * F(s)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    for row, (z, y) in enumerate(((1.19, -0.178), (1.115, -0.176), (1.04, -0.173))):          # abs
        for sx in (-1, 1):
            fd.add(Ellipsoid((sx * 0.05, y, z), (0.042, 0.022, 0.03)), 0.03, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.06, SKIN)
        fd.add(RoundCone(sh, el, 0.126, 0.093), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.03, 0)), (0.116, 0.118, 0.16), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)
        fd.add(RoundCone(el, wr, 0.09, 0.07), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.01, 0, 0)), (0.122, 0.106, 0.165), R=rot_from_axes(z_axis=wr - el)), 0.045, SKIN)
        fd.add(Sphere(el + v3((0, 0.03, 0)), 0.073), 0.03, SKIN)
        hand(fd, side, fist=(side == "R"))
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.155, 0.1), 0.07, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.025, 0)), (0.146, 0.134, 0.21), R=rot_from_axes(z_axis=kn - hip)), 0.05, SKIN)
        fd.add(Sphere(kn + v3((0, -0.035, 0.0)), 0.08), 0.04, SKIN)
        fd.add(RoundCone(kn, an, 0.097, 0.064), 0.04, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.035, 0)), (0.113, 0.108, 0.16), R=rot_from_axes(z_axis=an - kn)), 0.045, SKIN)
        foot(fd, side)
    head(fd)
    # war paint on the body: a red handprint on his left shoulder, stripes round the right upper arm
    dc = deltoid("L").c
    nrm = norm(v3((0.62, -0.62, 0.48)))
    hc = dc + nrm * 0.15
    Vv = norm(v3((0, 0, 1)) - nrm * nrm[2])
    U = norm(np.cross(Vv, nrm))
    fd.paint(Func(lambda P: np.maximum(handprint(P, hc - Vv * 0.012, 0.92, U, Vv), np.abs((P - hc.astype(F)) @ nrm.astype(F)) - F(0.09)),
                  hc - 0.25, hc + 0.25), PAINT)
    sh, el = J["shoulder_R"], J["elbow_R"]
    ax = norm(el - sh)
    for t0 in (0.5, 0.62):
        c = lerp(sh, el, t0)
        fd.paint(Func(lambda P, c=c: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.016), c - 0.25, c + 0.25), PAINT)


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
    n = 6
    for i in range(n):
        u = (i - (n - 1) / 2) / ((n - 1) / 2)
        x = u * 0.052 + 0.004
        y = -0.207 + 0.03 * u * u
        z = 1.527 + 0.012 * u * u + 0.007 * u
        w = 0.0098 if abs(u) < 0.35 else 0.0088
        fd.add(RoundBox(hp((x, y, z)), v3((w, 0.008, 0.012)) * HS, hr(0.0045), R=euler(0.12, 0, -u * 0.55)), 0.0)
    return fd


# ======================================================================================= beard
def fan_lock(hull, start, heading, length, w_max, t0, segs=8, gravity=0.0, lift=0.0, tip_up=0.0, grooves=2, fd=None, thin_root=False):
    hdir = v3(heading)
    def flow(p, i):
        return norm(hdir) + v3((0, 0, -gravity * (i + 1) / segs))
    line = flow_line(hull, start, flow, segs, length / segs)
    if len(line) < 3:
        return None
    pts, ws, ts, ns = [], [], [], []
    m = len(line) - 1
    for i, p in enumerate(line):
        u = i / m
        n = grad(hull, [p])[0].astype(np.float64)
        q = p + n * (t0 * 0.25 + lift * u * u) + v3((0, 0, tip_up * u ** 3))
        pts.append(q)
        sw = math.sin(min(1.0, u / 0.4) * math.pi / 2)
        ws.append(w_max * (0.55 + 0.45 * sw) * (1 - u ** 1.6) + w_max * 0.05)
        root_k = (0.45 + 0.55 * math.sin(min(1.0, u / 0.35) * math.pi / 2)) if thin_root else 1.0
        ts.append((t0 * (1 - 0.8 * u ** 1.3) + t0 * 0.08) * root_k)
        ns.append(n)
    lock = Lock(pts, ws, ts, ns, k=w_max * 0.3)
    if fd is not None:
        fd.add(lock, hr(0.006))
        for g in range(grooves):
            off = (g + 1) / (grooves + 1) - 0.5
            gp = []
            for i in range(1, m):
                u = i / m
                if u < 0.15 or u > 0.88:
                    continue
                tng = norm(pts[min(i + 1, m)] - pts[i - 1])
                lat = norm(np.cross(tng, ns[i]))
                gp.append(pts[i] + lat * ws[i] * off * 1.2 + ns[i] * ts[i] * 0.95)
            if len(gp) >= 2:
                fd.sub(Chain(gp, [hr(0.0055)] * len(gp), k=0.003), hr(0.004))
    return lock


def head_hull():
    fd = Field("HeadHull")
    head(fd)
    fd.add(neck_prim(), 0.05)
    fd.add(Ellipsoid((0, 0.04, 1.3), (0.37, 0.32, 0.35), R=euler(-0.12, 0, 0)), 0.06)
    return fd


def beard_field(skin, seed=5):
    """A full, groomed dark beard: chunky locks round the jaw (kept short so his chest shows), plus a heavy moustache.
    Whatever would poke through the hood's side panels is trimmed away."""
    rng = np.random.RandomState(seed)
    fd = Field("Beard")
    hull = head_hull()
    hull.add(Ellipsoid(hp((0, -0.15, 1.46)), v3((0.125, 0.075, 0.09)) * HS), hr(0.05))
    def root_at(u):
        ax = abs(u) * 0.175
        z = 1.47 + 0.17 * (ax / 0.175) ** 1.8
        th = u * 1.75
        d = norm(v3((math.sin(th), -math.cos(th), 0.0)) * 1.0 + v3((0, 0, (z - 1.56) * 2.5)))
        o = hp((0, -0.02, z)) + d * 0.5
        h, ok = ray_hit(hull, [o], [-d], tmax=0.5)
        return h[0] if ok[0] else None
    nb = 11
    for i in range(nb):
        u = (-1 + 2 * i / (nb - 1)) * 0.6
        r = root_at(u)
        if r is None:
            continue
        front = 1 - abs(u) / 0.6
        hd = v3((-u * 0.3, -0.25, -1.0))
        L = hr(0.085 + 0.05 * front ** 1.2) + rng.uniform(0, 0.01)
        fan_lock(hull, r + v3((0, 0, 0.008)), hd, L, hr(0.07 + 0.04 * front), hr(0.028 + 0.016 * front), segs=6, gravity=0.15,
                 lift=hr(0.035 + 0.05 * front ** 1.5), tip_up=hr(0.01), grooves=2, fd=fd, thin_root=True)
    # moustache: two heavy locks over the corners of the grin
    for sx in (-1, 1):
        pts = [hp((sx * 0.004, -0.24, 1.566)), hp((sx * 0.05, -0.232, 1.562)), hp((sx * 0.1, -0.2, 1.548)), hp((sx * 0.135, -0.162, 1.515)),
               hp((sx * 0.146, -0.148, 1.478))]
        ns = [norm(v3((sx * 0.3, -1.0, 0.3)))] * 5
        fd.add(Lock(pts, [hr(0.02), hr(0.031), hr(0.03), hr(0.02), hr(0.003)], [hr(0.015), hr(0.019), hr(0.018), hr(0.013), hr(0.003)], ns,
                    k=hr(0.012)), hr(0.008))
        for g in (-0.25, 0.25):
            gp = [lerp(pts[j], pts[j + 1], 0.5) + v3((0, -0.012, g * 0.02)) for j in range(3)]
            fd.sub(Chain(gp, [hr(0.004)] * 3, k=0.002), hr(0.003))
    fd.sub(hood_space(), 0.004)
    return fd
CAP_C = HEAD_C + v3((0.0, 0.018, 0.0))
CAP_R = HEAD_RAD + v3((0.06, 0.048, 0.042))
HOOD_T = 0.035                     # pelt thickness


def hood_hull():
    """Outer surface of the hood minus its thickness: the cat's cranium over his head, its hide falling down the sides
    of his face (flaring toward the shoulders) and a flap down the back of his neck."""
    h = Field("HoodHull")
    h.add(Ellipsoid(CAP_C, CAP_R - (HOOD_T + 0.0125)), 0.0)
    h.add(RoundCone((0, -0.012, 1.76), (0, 0.0, 1.57), 0.19, 0.228), 0.07)
    h.add(RoundCone((0, 0.07, 1.64), (0, 0.11, 1.46), 0.2, 0.232), 0.08)
    return h


def hood_keep(P):
    """<0 where the hood exists: outside the face opening and above the ragged lower edge."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    e = np.sqrt((x / F(0.188)) ** 2 + ((z - F(1.712)) / F(0.228)) ** 2) - F(1.0)
    face = np.maximum(e * F(0.19), y)
    tb = np.clip((y + F(0.02)) / F(0.17), 0, 1)
    tb = tb * tb * (F(3) - F(2) * tb)
    zb = F(1.575) + (F(1.465) - F(1.575)) * tb + F(0.012) * NOISE(P * F(18))
    a = np.arctan2(x, y - F(0.06))                            # fringe teeth along the back edge
    zb = zb - F(0.016) * tb * np.abs(np.sin(a * F(4.5)))
    return np.maximum(-face, zb - z)


def cat_face(fd):
    """The cat's face over his brow, snarling: heavy angry brow, amber stones for eyes, wrinkled nose, raised lip;
    small ears on the sides of its head and fur swept back from its cheeks."""
    fd.add(Ellipsoid((0, -0.2, 2.02), (0.165, 0.09, 0.085)), 0.05, FUR)                 # cat's forehead
    fd.add(Ellipsoid((0, -0.268, 1.973), (0.112, 0.088, 0.06)), 0.04, MUZZLE)            # muzzle
    fd.add(RoundCone((0, -0.245, 2.06), (0, -0.33, 2.015), 0.036, 0.03), 0.03, FUR)      # nose bridge
    for k, z in enumerate((2.049, 2.033, 2.02)):                                          # snarl wrinkles
        y = -0.272 - 0.024 * k
        fd.add(Chain([v3((-0.042, y + 0.012, z - 0.004)), v3((0, y, z)), v3((0.042, y + 0.012, z - 0.004))], [0.008, 0.01, 0.008], k=0.006), 0.01, FUR)
    for sx in (-1, 1):
        fd.add(Sphere((sx * 0.052, -0.322, 1.965), 0.043), 0.025, MUZZLE)                  # whisker pads (lifted)
        fd.add(Chain([v3((sx * 0.026, -0.29, 2.047)), v3((sx * 0.085, -0.275, 2.069)), v3((sx * 0.148, -0.228, 2.083))],
                     [0.025, 0.03, 0.021], k=0.02), 0.03, FUR)                             # angry brow ridges
        fd.add(Sphere((sx * 0.14, -0.205, 1.973), 0.052), 0.04, FUR)                       # cheeks
        R = rot_from_axes(x_axis=(1, 0, sx * 0.4))
        fd.sub(Ellipsoid((sx * 0.084, -0.272, 2.028), (0.037, 0.03, 0.02), R=R), 0.006)    # almond sockets
        fd.add(Ellipsoid((sx * 0.084, -0.265, 2.027), (0.03, 0.02, 0.0165), R=R), 0.0, AMBER)
        for j in range(3):                                                                  # whisker dots
            fd.paint(Sphere((sx * (0.035 + 0.02 * j), -0.357 + 0.012 * j, 1.961 - 0.006 * (j % 2)), 0.006), NOSEPAD)
        # cheek ruff: flat locks of fur swept back along the sides of the hood
        for j, dz in enumerate((0.035, 0.0, -0.035)):
            a = v3((sx * 0.17, -0.2, 1.98 + dz))
            pts = [a, a + v3((sx * 0.05, 0.05, -0.012)), a + v3((sx * 0.075, 0.115, -0.03))]
            nrm = norm(v3((sx * 1.0, -0.3, 0.2)))
            fd.add(Lock(pts, [0.032, 0.026, 0.004], [0.012, 0.01, 0.003], [nrm] * 3, k=0.006), 0.012, FUR)
    fd.add(Sphere((-0.024, -0.352, 2.01), 0.019), 0.0, NOSEPAD)                          # triangular nose pad
    fd.add(Sphere((0.024, -0.352, 2.01), 0.019), 0.012, NOSEPAD)
    fd.add(Sphere((0.0, -0.356, 1.99), 0.017), 0.012, NOSEPAD)
    fd.paint(RoundCone((0, -0.364, 1.983), (0, -0.348, 1.947), 0.006, 0.005), NOSEPAD)
    rim = [(-0.13, -0.205, 1.945), (-0.08, -0.29, 1.927), (0, -0.33, 1.925), (0.08, -0.29, 1.927), (0.13, -0.205, 1.945)]
    fd.add(Chain([v3(p) for p in rim], [0.017, 0.019, 0.02, 0.019, 0.017], k=0.015), 0.016, MUZZLE)
    fd.sub(Chain([v3((-0.06, -0.338, 1.913)), v3((0, -0.355, 1.909)), v3((0.06, -0.338, 1.913))], [0.006, 0.007, 0.006], k=0.004), 0.004)
    fd.paint(Chain([v3((-0.07, -0.33, 1.911)), v3((0, -0.35, 1.907)), v3((0.07, -0.33, 1.911))], [0.01, 0.011, 0.01], k=0.004), NOSEPAD)
    for sx in (-1, 1):                                    # small round ears on the sides of the cat's head, turned out
        R = euler(0.2, sx * 0.5, sx * -0.6)
        c = v3((sx * 0.19, 0.035, 2.05))
        fd.add(Ellipsoid(c, (0.06, 0.028, 0.068), R=R), 0.03, FUR)
        fd.sub(Ellipsoid(c + R @ v3((0, -0.02, 0.008)), (0.034, 0.014, 0.04), R=R), 0.008)
        fd.paint(Ellipsoid(c + R @ v3((0, -0.02, 0.008)), (0.04, 0.02, 0.046), R=R), INNER)


def hood_field():
    fd = Field("Hood")
    hull = hood_hull()
    fur = lambda P: F(0.004) * NOISE(P * np.array([30, 30, 12], F)) + F(0.002) * NOISE(P * F(70))
    lo, hi = CAP_C - v3((0.4, 0.4, 0.5)), CAP_C + v3((0.4, 0.4, 0.4))
    shell = Inter(Shell(hull, 0.0125 + HOOD_T / 2, HOOD_T, pad=0.09, disp=fur, disp_amp=0.006), Func(hood_keep, lo, hi), 0.01)
    fd.add(shell, 0.0, FUR)
    fd.paint(Func(lambda P: hull.eval(P, margin=0.08) - F(0.0125 + HOOD_T * 0.45), lo, hi), SUEDE)       # inner side = tanned hide
    # fur fringe along the face opening: short flat tufts curling over the edge
    rng = np.random.RandomState(12)
    for sx in (-1, 1):
        for i, z in enumerate(np.linspace(1.6, 1.87, 8)):
            ex = 0.188 * math.sqrt(max(0.0, 1 - ((z - 1.712) / 0.228) ** 2))
            o = v3((sx * (ex + 0.012), -0.6, z))
            h, ok = ray_hit(shell, [o], [v3((0, 1, 0))], tmax=0.6)
            if not ok[0]:
                continue
            a = h[0] + v3((0, 0.012, 0))
            L = 0.05 + rng.uniform(0, 0.015)
            d = norm(v3((-sx * 0.55, -0.15, -0.8)))
            pts = [a, a + d * L * 0.5 + v3((0, -0.006, 0)), a + d * L + v3((0, 0.004, 0))]
            fd.add(Lock(pts, [0.026, 0.02, 0.004], [0.011, 0.009, 0.003], [v3((0, -1, 0))] * 3, k=0.005), 0.01, FUR)
    cat_face(fd)
    return fd


def fangs_field():
    """Saber fangs framing his face (flat curved blades), the cat's incisors, and the claws on the paws."""
    fd = Field("Fangs")
    for sx in (-1, 1):
        p0, p1, p2, p3 = v3((sx * 0.13, -0.226, 1.95)), v3((sx * 0.165, -0.272, 1.85)), v3((sx * 0.205, -0.27, 1.72)), v3((sx * 0.222, -0.212, 1.64))
        ts = np.linspace(0, 1, 13)
        pts = [bez3(p0, p1, p2, p3, t) for t in ts]
        ws = [0.034 * (1 - t ** 1.7) + 0.002 for t in ts]
        th = [0.018 * (1 - t ** 1.5) + 0.0015 for t in ts]
        ns = [norm(v3((1, 0, 0.15 * sx)))] * len(ts)
        fd.add(Lock(pts, ws, th, ns, k=0.012), 0.0)
    for i in range(6):
        u = (i - 2.5) / 2.5
        b = v3((u * 0.058, -0.336 + 0.03 * u * u, 1.913))
        fd.add(RoundCone(b, b + v3((0, -0.003, -0.02 + 0.004 * abs(u))), 0.0075, 0.0018), 0.0)
    for sx in (-1, 1):
        pc = PAW_C(sx)
        for j in range(4):
            u = (j - 1.5) / 1.5
            c = pc + v3((u * 0.034, -0.03, -0.046))
            fd.add(Chain([c, c + v3((0, -0.016, -0.016)), c + v3((0, -0.009, -0.038))], [0.0095, 0.0068, 0.0016], k=0.003), 0.0)
    return fd


def feather_field():
    """Two feathers tucked into the hood behind the cat's left ear."""
    fd = Field("Feather")
    for base, d, L, w in (((0.2, 0.1, 2.01), (0.3, 0.6, 1.0), 0.29, 0.026), ((0.218, 0.06, 1.99), (0.6, 0.38, 0.9), 0.24, 0.022)):
        base, d = v3(base), norm(d)
        side = norm(np.cross(d, v3((0, -1, 0.2))))
        nrm = norm(np.cross(side, d))
        n = 10
        ts_ = np.linspace(0, 1, n)
        pts = [base + d * L * t + nrm * 0.035 * math.sin(t * math.pi) * t for t in ts_]
        ws = [w * (0.35 + 0.65 * math.sin(min(1.0, t * 1.4) * math.pi / 2)) * (1 - t ** 4) + 0.002 for t in ts_]
        fd.add(Lock(pts[2:], ws[2:], [0.0035] * (n - 2), [nrm] * (n - 2), k=0.004), 0.0)
        fd.add(Chain(pts, [0.0055 - 0.0035 * t for t in ts_], k=0.002), 0.002)
        for t, sgn in ((0.5, 1), (0.66, -1), (0.8, 1)):                       # split vanes
            p = base + d * L * t + side * sgn * w * 1.0
            fd.sub(Ellipsoid(p, (0.018, 0.0035, 0.008), R=rot_from_axes(x_axis=norm(side * sgn * 0.5 - d), z_axis=nrm)), 0.001)
    return fd
def PAW_C(sx):
    return v3((sx * 0.098, -0.262, 1.255))


def cape_base():
    b = Field("CapeBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(Ellipsoid((0, 0.07, 0.86), (0.28, 0.225, 0.25)), 0.08)
    b.add(RoundBox((0, 0.165, 0.7), (0.3, 0.085, 0.3), 0.08, R=euler(0.06, 0, 0)), 0.14)
    return b


def cape_keep(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    t = np.clip((z - F(1.3)) / F(0.22), 0, 1)
    t = t * t * (F(3) - F(2) * t)
    lo = np.clip((F(1.15) - z) / F(0.2), 0, 1)
    lo = lo * lo * (F(3) - F(2) * lo)
    yb = F(0.04) - F(0.1) * t + F(0.07) * lo + F(0.012) * NOISE(P * F(13))
    xw = F(0.345) - F(0.025) * t + F(0.012) * NOISE(P * F(11) + 4)
    neck = F(0.165) - np.sqrt(x * x + (y - F(0.07)) ** 2)
    neck = np.where(z > F(1.48), neck, F(-1))
    # pelt outline at the hem: the tail in the middle and the hind legs at the corners hang lower
    ax = np.abs(x)
    hz = (F(0.5) - F(0.1) * np.exp(-(ax / F(0.055)) ** 2) - F(0.13) * np.exp(-((ax - F(0.3)) / F(0.06)) ** 2)
          + F(0.016) * np.abs(np.sin(x * F(55))) + F(0.014) * NOISE(P * F(9)))
    return np.maximum(np.maximum(np.maximum(yb - y, ax - xw - F(0.08) * lo), neck), hz - z)


def cape_field():
    fd = Field("Cape")
    base = cape_base()
    def fur(P):
        lo = np.clip((F(1.15) - P[:, 2]) / F(0.5), 0, 1)
        folds = F(0.014) * np.sin(P[:, 0] * F(23) + F(0.6) * NOISE(P * F(3))) * lo
        return F(0.006) * NOISE(P * np.array([16, 16, 5], F)) + F(0.004) * NOISE(P * np.array([42, 42, 12], F) + 3) + folds
    fd.add(Shell(base, 0.05, 0.032, disp=fur, disp_amp=0.026), 0.0, FUR)
    fd.inter(Func(cape_keep, (-3, -3, -3), (3, 3, 3)), 0.012)
    fd.paint(Func(lambda P: base.eval(P, margin=0.08) - F(0.05), (-1, -1, 0), (1, 1, 2)), SUEDE)
    # the cat's forelegs over his shoulders (flat hide), paws tied across his chest
    skin = skin_field()
    furl = lambda P: F(0.006) * NOISE(P * np.array([16, 16, 5], F)) + F(0.004) * NOISE(P * np.array([42, 42, 12], F) + 3)
    for sx in (-1, 1):
        path = [v3((sx * 0.22, 0.1, 1.64)), v3((sx * 0.255, -0.03, 1.6)), v3((sx * 0.245, -0.165, 1.49)), v3((sx * 0.19, -0.24, 1.37)),
                PAW_C(sx) + v3((sx * 0.012, 0.0, 0.05))]
        ws = [0.085, 0.08, 0.072, 0.064, 0.056]
        th = [0.026, 0.026, 0.024, 0.024, 0.024]
        pts, ns = [], []
        for p, t_ in zip(path, th):
            q = project_to(skin, [p], iters=4)[0]
            n = grad(skin, [q])[0].astype(np.float64)
            pts.append(q + n * (t_ + 0.008))
            ns.append(n)
        fd.add(Lock(pts, ws, th, ns, k=0.02, disp=furl, disp_amp=0.01), 0.02, FUR)
        pc = PAW_C(sx)
        fd.add(Ellipsoid(pc, (0.066, 0.042, 0.06), disp=furl, disp_amp=0.008), 0.025, FUR)
        for j in range(4):
            u = (j - 1.5) / 1.5
            fd.add(Sphere(pc + v3((u * 0.034, -0.024, -0.038)), 0.022), 0.012, FUR)
            fd.paint(Sphere(pc + v3((u * 0.034, 0.0, -0.058)), 0.017), PAD)
    return fd
def pelt_field():
    """Spotted fur loincloth (shorts + a front flap) and fur shin wraps."""
    fd = Field("Pelt")
    base = hip_base("ShortsBase")
    fur = lambda P: F(0.005) * NOISE(P * np.array([16, 16, 5], F)) + F(0.003) * NOISE(P * F(40))
    band = Func(lambda P: np.abs(P[:, 2] - F(0.8) - F(0.06) * P[:, 1]) - F(0.15) + F(0.014) * NOISE(P * F(20)), (-1, -1, 0.4), (1, 1, 1.2))
    fd.add(Inter(Shell(base, 0.02, 0.032, disp=fur, disp_amp=0.01), band, 0.006), 0.0)
    # front flap hanging from the belt
    flap = RoundCone((0, -0.0, 0.98), (0, 0.02, 0.5), 0.2, 0.19)
    def flap_keep(P):
        hem = F(0.52) + F(0.03) * np.abs(np.sin(P[:, 0] * F(40))) + F(0.012) * NOISE(P * F(15)) - P[:, 2]
        return np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.125) + F(0.04) * np.clip((F(0.7) - P[:, 2]) * F(4), 0, 1), P[:, 1] + F(0.05)),
                          np.maximum(hem, P[:, 2] - F(0.96)))
    fd.add(Inter(Shell(flap, 0.012, 0.024, pad=0.05, disp=fur, disp_amp=0.008), Func(flap_keep, (-0.3, -0.5, 0.4), (0.3, 0.2, 1.1)), 0.006), 0.006)
    for side in ("R", "L"):
        kn, an = J["knee_" + side], J["ankle_" + side]
        calf = RoundCone(kn, an, 0.097, 0.064)
        fd.add(Inter(Shell(calf, 0.016, 0.034, pad=0.06, disp=fur, disp_amp=0.01),
                     Func(lambda P, an=an: np.abs(P[:, 2] - F(an[2] + 0.1)) - F(0.06) + F(0.012) * NOISE(P * F(25)), an - 0.2, an + 0.3),
                     0.004), 0.0)
    return fd


def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.09, 0.07)


BELT_Z = 0.955


def leather_field(pelt):
    fd = Field("Leather")
    pel = hip_base("PelvisBase", legs=False)
    # wide belt
    bz = BELT_Z - 0.04 * 0.26
    bh, _ = ray_hit(Func(lambda P: pel.eval(P) - F(0.068), (-1, -1, 0.5), (1, 1, 1.3)), [v3((0, -0.8, bz))], [v3((0, 1, 0))], tmax=0.8)
    buckle = bh[0] + v3((0, -0.011, 0))
    fd.add(Inter(Shell(pel, 0.056, 0.024, pad=0.1),
                 Func(lambda P: np.abs(P[:, 2] - (F(BELT_Z) + F(0.04) * P[:, 1])) - F(0.042), (-1, -1, 0.7), (1, 1, 1.2)), 0.004), 0.0)
    for j in (-1, 1):                                        # stitched edges
        fd.add(Inter(Shell(pel, 0.068, 0.006, pad=0.1),
                     Func(lambda P, j=j: np.abs(P[:, 2] - (F(BELT_Z + j * 0.034) + F(0.04) * P[:, 1])) - F(0.005), (-1, -1, 0.7), (1, 1, 1.2)), 0.002), 0.003)
    # bracers
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.7)
        fd.add(Inter(Shell(_forearm(side), 0.014, 0.018, pad=0.06),
                     Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.075), c - 0.25, c + 0.25), 0.004), 0.0)
        for j in (-1, 0, 1):
            cc = c + ax * (j * 0.045)
            fd.add(Inter(Shell(_forearm(side), 0.024, 0.006, pad=0.06),
                         Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.006), cc - 0.2, cc + 0.2), 0.002), 0.003)
    # stone pouch on the right hip, a smaller one on the left
    bags = []
    for sx, s, ang in ((-1, 1.0, -0.62), (1, 0.75, 0.75)):
        d = norm(v3((math.sin(ang) * 1.0, -math.cos(ang), 0.0)))
        bp, _ = ray_hit(pelt, [v3((0, 0.03, 0.8)) + d * 0.7], [-d], tmax=0.8)
        out = d
        bc = bp[0] + out * 0.05 * s
        R = rot_from_axes(y_axis=out, z_axis=(0, 0, 1))
        fd.add(Ellipsoid(bc, v3((0.085, 0.055, 0.092)) * s, R=R, disp=lambda P: F(0.003) * NOISE(P * F(30)), disp_amp=0.004), 0.0)
        fd.sub(Ellipsoid(bc + v3((0, 0, 0.085 * s)), v3((0.06, 0.035, 0.03)) * s, R=R), 0.01)
        fd.add(Torus(bc + v3((0, 0, 0.055 * s)), 0.068 * s, 0.009, R=R), 0.006)
        fd.add(Chain([bc + v3((0, 0, 0.06 * s)) - out * 0.02, bc + v3((0.0, 0, 0.15)) - out * 0.035], [0.012, 0.012]), 0.008)
        bags.append((bc, R, s))
    # the knot that ties the paws together
    k0 = v3((0.0, -0.29, 1.252))
    fd.add(Ellipsoid(k0, (0.03, 0.022, 0.026)), 0.006)
    for sx in (-1, 1):
        fd.add(RoundCone(k0, PAW_C(sx) + v3((-sx * 0.04, -0.026, 0.0)), 0.013, 0.011), 0.006)
    fd.add(Chain([k0, k0 + v3((0.012, -0.012, -0.06)), k0 + v3((0.02, -0.01, -0.11))], [0.011, 0.01, 0.008], k=0.006), 0.006)
    fd.add(Chain([k0, k0 + v3((-0.012, -0.014, -0.05)), k0 + v3((-0.026, -0.012, -0.09))], [0.011, 0.01, 0.008], k=0.006), 0.006)
    return fd, bags, buckle


def bag_stones(bags):
    fd = Field("BagStones")
    k = 0
    for bc, R, s in bags:
        for i, (dx, dy, r) in enumerate(((-0.025, 0.0, 0.034), (0.022, 0.008, 0.03), (0.0, -0.012, 0.028))[: 3 if s > 0.9 else 2]):
            fd.add(Stone(bc + R @ (v3((dx, dy, 0.0)) * s) + v3((0, 0, 0.078 * s + 0.01 * i)), r * s, seed=40 + k, noise=0.05), 0.002)
            k += 1
    return fd


def bone_field(buckle):
    """Bone buckle on the belt (a carved disc with a sun boss) and the toggle in the paw knot."""
    fd = Field("Bone")
    c = v3(buckle) + v3((0, -0.004, 0))
    R = rot_from_axes(z_axis=(0, -1, 0.1))
    fd.add(Cylinder(c, 0.056, 0.022, rr=0.009, R=R), 0.0)
    fd.add(Sphere(c + R @ v3((0, 0, 0.004)), 0.026), 0.006)
    fd.sub(Torus(c + R @ v3((0, 0, 0.0115)), 0.041, 0.0045, R=R), 0.002)
    for i in range(8):
        a = i * math.pi / 4
        p = c + R @ v3((math.cos(a) * 0.041, math.sin(a) * 0.041, 0.0125))
        fd.add(Sphere(p, 0.0065), 0.002)
    k0 = v3((0.0, -0.302, 1.252))
    fd.add(RoundCone(k0 + v3((-0.05, -0.006, 0.006)), k0 + v3((0.05, -0.006, -0.006)), 0.012, 0.012), 0.0)
    for sx in (-1, 1):
        fd.add(Sphere(k0 + v3((sx * 0.052, -0.006, -sx * 0.006)), 0.016), 0.004)
    return fd
def sling_points():
    wr, f, n, t = hand_frame("R")
    fist = wr + f * 0.106 + n * 0.037
    attach = fist - t * 0.053 + v3((0, 0, -0.02))
    pouch = attach + v3((0, 0, -0.45))
    return fist, attach, pouch


def sling_field():
    fist, attach, pouch = sling_points()
    fd = Field("Sling")
    cup = Inter(Shell(Ellipsoid(pouch, (0.092, 0.065, 0.068)), 0.0, 0.011, pad=0.03), Plane(pouch + v3((0, 0, 0.012)), (0, 0, 1)), 0.004)
    fd.add(cup, 0.0)
    for sx in (-1, 1):
        rim = pouch + v3((sx * 0.087, 0, 0.008))
        mid = lerp(attach, rim, 0.5) + v3((sx * 0.004, 0, 0))
        fd.add(Chain([attach + v3((sx * 0.004, 0, 0)), mid, rim], [0.0068, 0.0068, 0.0085], k=0.004), 0.003)
    fd.add(Sphere(attach + v3((0, 0, -0.005)), 0.015), 0.006)
    stone = Field("SlingStone")
    stone.add(Stone(pouch + v3((0, 0, 0.03)), 0.064, seed=11, noise=0.04), 0.0)
    cloth = Field("Cloth")
    for sx in (-1, 1):            # red tassels where the cords meet the pouch
        r0 = pouch + v3((sx * 0.092, 0, 0.004))
        cloth.add(Sphere(r0, 0.014), 0.0)
        for j in (-1, 1):
            cloth.add(Lock([r0, r0 + v3((sx * 0.012, j * 0.008, -0.05)), r0 + v3((sx * 0.018, j * 0.014, -0.1))], [0.011, 0.009, 0.002],
                           [0.004, 0.004, 0.0015], [v3((0, 1, 0))] * 3, k=0.004), 0.004)
    return fd, stone, cloth


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.246, 1.608)), 0.075, 0.9)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.105, -0.15, 1.6)), 0.065, 0.45),
                (J["elbow_" + sd] + v3((0, 0.03, 0)), 0.08, 0.3),
                (J["knee_" + sd] + v3((0, -0.04, 0)), 0.09, 0.35),
                (J["shoulder_" + sd] + v3((0, 0, 0.12)), 0.13, 0.22)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.045, 0.015, -0.015, -0.045):
            pts.append((wr + f * 0.145 + t * o - n * 0.012, 0.035, 0.45))
        an = J["ankle_" + side]
        pts.append((an + v3((0, -0.18, -0.07)), 0.07, 0.45))
        pts.append((an + v3((0, 0.05, -0.07)), 0.06, 0.3))
    return pts


# ======================================================================================= build config (Ugo)
GLB_NAME = "ugo"
ROOT_NAME = "HeroUgoHQ"
TEX_PREFIX = "hero"
MAT_NAME = "UgoMat"
MESH_NAME = "Ugo"
BASE_MODULE = "ugo_base"
ANIM_MODULE = "anim_ugo"
PARTS = ["Skin", "Eyes", "Teeth", "Beard", "Hood", "Fangs", "Feather", "Cape", "Pelt", "Leather", "BagStones", "Bone",
         "Sling", "SlingStone", "Cloth"]
REGION_PARTS = ("Skin", "Hood", "Cape")
MAT_OVERRIDES = {"Beard": ("hair", {"name": "HQ_UgoBeard", "base": (0.13, 0.085, 0.06), "hi": (0.34, 0.22, 0.14)}),
                 "Leather": ("leather", {"name": "HQ_UgoLeather", "base": (0.4, 0.23, 0.12)}),
                 "Pelt": ("fur", {"name": "HQ_UgoFur", "base": (0.33, 0.2, 0.11), "tip": (0.62, 0.45, 0.28)})}
LOW_TARGETS = {"Skin": 7000, "Beard": 1500, "Hood": 3000, "Fangs": 1400, "Feather": 260, "Cape": 3000, "Pelt": 1500,
               "Leather": 1500, "Teeth": 300, "Bone": 300, "Sling": 700, "SlingStone": 140, "BagStones": 200, "Cloth": 180}
AO_EXCLUDE = ["Bone", "Sling", "SlingStone", "BagStones", "Cloth", "Feather", "Fangs"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.76, 0.94, 1.12, 1.56)       # sdf_weights: centre-line torso shapes -> root / spine / chest by height


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.99), (0, 0.045, 1.21)),
        "chest": ((0, 0.045, 1.21), (0, 0.06, 1.47)),
        "neck": ((0, 0.06, 1.47), hp((0, 0.02, 1.56))),
        "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.46,
    }


def extra_bones():
    return [("cape.1", (0.0, 0.3, 1.36), (0.0, 0.36, 0.95), "chest"),
            ("cape.2", (0.0, 0.36, 0.95), (0.0, 0.4, 0.45), "cape.1")]


def _blend_add(ob, groups, i, w):
    for n, x in w.items():
        if x <= 0.005:
            continue
        g = groups.get(n) or ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n)
        groups[n] = g
        g.add([i], x, "REPLACE")


def hood_weights(ob, skin_ob, arm):
    """Head above the jaw line; the side panels and the neck flap blend into the neck and chest."""
    groups = {}
    z0 = 1.68
    for v in ob.data.vertices:
        p = v.co
        if p.z >= z0:
            _blend_add(ob, groups, v.index, {"head": 1.0})
            continue
        t = min(1.0, (z0 - p.z) / 0.2)
        back = max(0.0, min(1.0, (p.y - 0.0) / 0.12))
        t *= 0.45 + 0.55 * back
        _blend_add(ob, groups, v.index, {"head": 1.0 - t, "neck": t * 0.7, "chest": t * 0.3})


def cape_weights(ob, skin_ob, arm):
    """Chest at the top, blending into the two cape bones down the back; forelegs/paws follow the chest
    (a little of the clavicles over the shoulders); the hind legs and tail hang from cape.2."""
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.y < 0.06 and p.z > 1.25:             # forelegs + paws
            w_cl = max(0.0, min(1.0, (abs(p.x) - 0.15) / 0.12)) * 0.35
            w = {"chest": 1.0 - w_cl}
            if w_cl > 0.01:
                w["clavicle.R" if p.x < 0 else "clavicle.L"] = w_cl
            _blend_add(ob, groups, v.index, w)
            continue
        z = p.z
        if z > 1.32:
            w = {"chest": 1.0}
            if abs(p.x) > 0.24:
                w = {"chest": 0.7, ("clavicle.R" if p.x < 0 else "clavicle.L"): 0.3}
        elif z > 1.02:
            t = (1.32 - z) / 0.3
            w = {"chest": 1 - t, "cape.1": t}
        elif z > 0.75:
            t = (1.02 - z) / 0.27
            w = {"cape.1": 1 - t * 0.6, "cape.2": t * 0.6}
        else:
            t = min(1.0, (0.75 - z) / 0.2)
            w = {"cape.1": 0.4 * (1 - t), "cape.2": 0.6 + 0.4 * t}
        _blend_add(ob, groups, v.index, w)


def fangs_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"chest" if v.co.z < 1.45 else "head": 1.0})


def bone_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"chest": 1.0} if v.co.z > 1.2 else {"root": 0.6, "spine": 0.4})


def leather_weights(ob, skin_ob, arm):
    """Belt + pouches with the hips, bracers with the forearms, the paw knot with the chest."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "thigh.R", "thigh.L"},
                         caps={"thigh.R": 0.3, "thigh.L": 0.3})
    groups = {}
    for v in ob.data.vertices:
        if v.co.z > 1.22 and abs(v.co.x) < 0.2 and v.co.y < -0.15:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"chest": 1.0})


def weight_rules():
    return {
        "Hood": ("custom", hood_weights), "Fangs": ("custom", fangs_weights), "Feather": ("rigid", "head"),
        "Beard": ("rigid", "head"), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Cape": ("custom", cape_weights),
        "Pelt": ("transfer", TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Leather": ("custom", leather_weights),
        "Bone": ("custom", bone_weights),
        "BagStones": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.3, "thigh.L": 0.3}),
        "Sling": ("rigid", "sling"), "SlingStone": ("rigid", "stone"), "Cloth": ("rigid", "sling"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part == "Fangs":                        # sabers, incisors and the paws' claws: small but they catch the eye
        return 2.2
    if part in ("Bone", "Cloth"):
        return 1.3
    if part in ("Sling", "SlingStone", "BagStones", "Feather"):
        return 0.8
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0:
        return 1.9
    if part == "Hood" and c.y < -0.1 and c.z > 1.6:
        return 1.35
    if part == "Skin" and (abs(c.x) > 0.66 and c.z < 1.05):
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    skin = skin_field()
    pelt = pelt_field()
    leather, bags, buckle = leather_field(pelt)
    sling, sstone, cloth = sling_field()
    return [
        ("Skin", skin, 0.0032 if fine else 0.005),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Beard", beard_field(skin), 0.0028 if fine else 0.0035),
        ("Hood", hood_field(), 0.0028 if fine else 0.004),
        ("Fangs", fangs_field(), 0.0015 if fine else 0.002),
        ("Feather", feather_field(), 0.0012 if fine else 0.0018),
        ("Cape", cape_field(), 0.0035 if fine else 0.005),
        ("Pelt", pelt, 0.0035 if fine else 0.005),
        ("Leather", leather, 0.0025 if fine else 0.003),
        ("BagStones", bag_stones(bags), 0.002),
        ("Bone", bone_field(buckle), 0.0015 if fine else 0.002),
        ("Sling", sling, 0.0015 if fine else 0.002),
        ("SlingStone", sstone, 0.002),
        ("Cloth", cloth, 0.0012 if fine else 0.0018),
    ]



class _Off:
    """A field offset outward by `off` (for projecting onto a shell's outer surface)."""

    def __init__(self, f, off):
        self.f, self.off = f, off

    def eval(self, P):
        return self.f.eval(P, margin=self.off + 0.05) - F(self.off)


def hood_space():
    """<0 inside the hood's outer surface wherever the hood exists (used to trim the beard under the side panels)."""
    hull = hood_hull()
    lo, hi = CAP_C - v3((0.4, 0.4, 0.5)), CAP_C + v3((0.4, 0.4, 0.4))
    return Func(lambda P: np.maximum(hull.eval(P, margin=0.08) - F(0.0125 + HOOD_T + 0.004), hood_keep(P)), lo, hi)


def bez3(p0, p1, p2, p3, t):
    u = 1 - t
    return p0 * u ** 3 + p1 * 3 * u * u * t + p2 * 3 * u * t * t + p3 * t ** 3


def hip_base(name="HipBase", legs=True):
    """Belly + pelvis (+ thighs) exactly as sculpted in the skin: the shorts and belt are layered on this."""
    b = Field(name)
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    if legs:
        for side in ("R", "L"):
            b.add(RoundCone(J["hip_" + side], J["knee_" + side], 0.155, 0.1), 0.07)
            b.add(Ellipsoid(lerp(J["hip_" + side], J["knee_" + side], 0.42) + v3((0, -0.025, 0)), (0.146, 0.134, 0.21),
                            R=rot_from_axes(z_axis=J["knee_" + side] - J["hip_" + side])), 0.05)
    return b