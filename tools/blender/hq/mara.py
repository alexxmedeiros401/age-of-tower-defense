"""Mara Stonecaller, Earth Shaman (HQ hero). Rest pose = A-pose, facing -Y, feet at z=0; right side = -X.

A tall, calm young woman: strong straight brows, almond eyes, a quiet smile, ochre lines on her cheeks and chin. Long
near-black hair parted in the middle, falling down her back, with two thick braids forward over her shoulders ending in
amber beads. A leather circlet with an amber stone on her brow and a pair of red-deer antlers rising from it. A sleeveless
dress of pale fox fur to her knees, a purple sash knotted at her left hip, a necklace of amber and bone beads, leather
bracers, fur-cuffed boots. Her staff is pale driftwood whose top opens into three claws round a glowing amber orb.
Three carved stones orbit her (their own mesh, SpinSlowStones, turned in game)."""
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
    J["shoulder_" + _s] = (_x * 0.29, 0.06, 1.36)
    J["elbow_" + _s] = (_x * 0.48, 0.09, 1.11)
    J["wrist_" + _s] = (_x * 0.62, 0.03, 0.88)
    J["hip_" + _s] = (_x * 0.14, 0.04, 0.76)
    J["knee_" + _s] = (_x * 0.155, 0.0, 0.42)
    J["ankle_" + _s] = (_x * 0.165, 0.06, 0.1)
    J["toe_" + _s] = (_x * 0.18, -0.16, 0.03)
J = {k: v3(v) for k, v in J.items()}

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH = 0, 1, 2, 3, 4, 5, 8

HS = 1.03
DZ = -0.06
HPIV = v3((0.0, 0.02, 1.46))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.172, 0.186, 0.184)) * HS
EYE_R = hr(0.039)


def eye_c(sx):
    return hp((sx * 0.07, -0.148, 1.675))


def hstripe(a, b, ra, rb, y0=-0.4, y1=0.02):
    m = lambda q: (q[0] * HS, HPIV[2] + (q[1] + DZ - HPIV[2]) * HS)
    return stripe2d(m(a), m(b), ra * HS, rb * HS, y0=y0, y1=y1)


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


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.033


def hand(fd, side, fist, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.076 * s
    fd.add(RoundBox(c, v3((0.06, 0.03, 0.064)) * s, 0.028 * s, R=Rp), 0.027, SKIN)
    fd.add(Ellipsoid(c - n * 0.01 + t * 0.03 * s - f * 0.01, v3((0.033, 0.028, 0.05)) * s, R=Rp), 0.018, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = (1.45, 1.6, 1.2) if fist else (0.25, 0.4, 0.3)
    offs = (0.042, 0.014, -0.014, -0.042)
    lens = (0.97, 1.03, 0.97, 0.82)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * (1.2 if fist else 2.6))
        pts, rads = [p], [0.0195 * s * (0.92 if i == 3 else 1.0)]
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
    fd.add(Chain([tb, p1, p2], [0.024 * s, 0.021 * s, 0.018 * s], k=0.008), 0.017, SKIN)


def foot(fd, side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.1)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    fd.add(Sphere(an + v3((0, 0.04, -0.05)), 0.056), 0.027, SKIN)
    fd.add(RoundBox(an + fwd * 0.072 + v3((0, 0, -0.068)), (0.062, 0.112, 0.034), 0.031, R=Rz), 0.03, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.035 + v3((0, 0, -0.03)), (0.06, 0.082, 0.046), R=Rz), 0.027, SKIN)
    inner = -sx
    for i, (o, r) in enumerate(((0.047, 0.026), (0.019, 0.02), (-0.005, 0.018), (-0.027, 0.016), (-0.045, 0.015))):
        base = an + fwd * (0.158 - 0.011 * i - (0.0 if i else -0.004)) + rgt * (o * inner) + v3((0, 0, -0.08))
        tip = base + fwd * (0.028 + r * 0.4) + v3((0, 0, -0.004))
        base[2] = 0.023 + r * 0.55
        tip[2] = 0.018 + r * 0.5
        fd.add(RoundCone(base, tip, r, r * 0.92), 0.011, SKIN)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.048, 0.0, 0.0)), 0.023), 0.017, SKIN)


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.06, 1.592), (0.152, 0.135, 0.128)), 0.07, SKIN)                           # oval jaw
    fd.add(E((0, -0.128, 1.508), (0.075, 0.064, 0.06)), 0.05, SKIN)                           # neat chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.112, 1.628), 0.048), 0.05, SKIN)                               # high cheekbones
        fd.add(S((sx * 0.125, -0.05, 1.56), 0.058), 0.05, SKIN)
        pts = [hp((sx * 0.15, -0.06, 1.744)), hp((sx * 0.115, -0.128, 1.75)), hp((sx * 0.062, -0.162, 1.748))]
        fd.add(Chain(pts, [hr(0.01), hr(0.014), hr(0.012)], k=hr(0.02)), hr(0.03), SKIN)                      # soft orbit rim, no glabella bulge
    # strong straight brows
    for sx in (-1, 1):
        pts = [hp((sx * 0.028, -0.204, 1.767)), hp((sx * 0.07, -0.194, 1.772)), hp((sx * 0.112, -0.17, 1.772)), hp((sx * 0.148, -0.134, 1.76))]
        fd.add(Chain([p + v3((0, 0.007, 0)) for p in pts], [hr(0.007), hr(0.008), hr(0.007), hr(0.003)], k=hr(0.006)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.015), hr(0.017), hr(0.014), hr(0.008)], k=hr(0.01)), BROW)
    # almond eyes, calm, lashes on the upper lids
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, hr(0.029))), (sx * 0.2, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0045)), Plane(ec + v3((0, 0, -hr(0.029))), (sx * -0.12, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.008)), Plane(ec + v3((0, 0, hr(0.025))), (sx * 0.2, 0.05, -1.0)), hr(0.002)), LASH)
        flick = ec + v3((sx * hr(0.044), -hr(0.012), hr(0.016)))
        fd.add(RoundCone(flick, flick + v3((sx * hr(0.02), hr(0.008), hr(0.006))), hr(0.005), hr(0.0015)), hr(0.004), LASH)
    # straight nose
    fd.add(RoundCone(hp((0, -0.178, 1.722)), hp((0, -0.224, 1.638)), hr(0.014), hr(0.019)), hr(0.016), SKIN)
    fd.add(S((0, -0.226, 1.624), 0.025), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.026, -0.206, 1.611), 0.017), hr(0.011), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.014, -0.221, 1.599)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a quiet smile
    slot = [hp((-0.058, -0.164, 1.558)), hp((-0.03, -0.189, 1.543)), hp((0, -0.196, 1.54)), hp((0.03, -0.189, 1.543)), hp((0.058, -0.164, 1.558))]
    fd.sub(Chain(slot, [hr(0.0022), hr(0.003), hr(0.0035), hr(0.003), hr(0.0022)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0045), hr(0.005), hr(0.0045), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.056, -0.161, 1.56), (-0.029, -0.181, 1.552), (-0.008, -0.186, 1.555), (0.008, -0.186, 1.555), (0.029, -0.181, 1.552), (0.056, -0.161, 1.56)]
    lo_lip = [(-0.048, -0.163, 1.545), (-0.026, -0.181, 1.532), (0, -0.185, 1.529), (0.026, -0.181, 1.532), (0.048, -0.163, 1.545)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.004), hr(0.0075), hr(0.008), hr(0.008), hr(0.0075), hr(0.004)], k=hr(0.006)), hr(0.009), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.009), hr(0.01), hr(0.009), hr(0.005)], k=hr(0.007)), hr(0.009), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.176, 0.035, 1.66)), v3((0.025, 0.044, 0.056)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
    # face paint: two short ochre lines under each eye, one down her chin
    for sx in (-1, 1):
        for k in range(2):
            x = sx * (0.07 + 0.03 * k)
            fd.paint(hstripe((x, 1.622), (x + sx * 0.004, 1.585), 0.007, 0.005, y0=-0.5, y1=-0.05), PAINT)
    fd.paint(hstripe((0, 1.52), (0, 1.475), 0.007, 0.006, y0=-0.5, y1=-0.05), PAINT)


# ======================================================================================= body
def torso_prims():
    return [
        (Ellipsoid((0, 0.04, 1.14), (0.215, 0.165, 0.22), R=euler(-0.1, 0, 0)), 0.0),
        (Ellipsoid((0, 0.1, 1.19), (0.24, 0.12, 0.17)), 0.05),
        (Ellipsoid((0.08, -0.11, 1.17), (0.085, 0.064, 0.076), R=euler(0.3, 0, 0.2)), 0.04),
        (Ellipsoid((-0.08, -0.11, 1.17), (0.085, 0.064, 0.076), R=euler(0.3, 0, -0.2)), 0.04),
        (Ellipsoid((0, -0.0, 0.95), (0.17, 0.145, 0.15)), 0.07),
        (Ellipsoid((0, 0.04, 0.8), (0.235, 0.17, 0.15)), 0.07),
    ]


def traps():
    return Ellipsoid((0, 0.09, 1.36), (0.19, 0.105, 0.072), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.06, 1.32), hp((0, 0.02, 1.575)), 0.068, hr(0.072))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.02, -0.005, 0.012)), 0.09)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.05, SKIN)
    fd.add(neck_prim(), 0.045, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.05, SKIN)
        fd.add(RoundCone(sh, el, 0.074, 0.056), 0.045, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.066, 0.068, 0.1), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(RoundCone(el, wr, 0.056, 0.043), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.07, 0.062, 0.11), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.022, 0)), 0.044), 0.025, SKIN)
        hand(fd, side, fist=(side == "R"))
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.125, 0.078), 0.06, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.02, 0)), (0.115, 0.105, 0.17), R=rot_from_axes(z_axis=kn - hip)), 0.045, SKIN)
        fd.add(Sphere(kn + v3((0, -0.026, 0.0)), 0.062), 0.035, SKIN)
        fd.add(RoundCone(kn, an, 0.076, 0.05), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.026, 0)), (0.085, 0.082, 0.13), R=rot_from_axes(z_axis=an - kn)), 0.04, SKIN)
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
        fd.add(RoundBox(hp((sx * 0.009, -0.172, 1.546)), v3((0.008, 0.006, 0.008)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= hair
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
                if u < 0.15 or u > 0.75:
                    continue
                tng = norm(pts[min(i + 1, m)] - pts[i - 1])
                lat = norm(np.cross(tng, ns[i]))
                gp.append(pts[i] + lat * ws[i] * off * 1.2 + ns[i] * ts[i] * 1.04)
            if len(gp) >= 2:
                fd.sub(Chain(gp, [hr(0.0042)] * len(gp), k=0.003), hr(0.004))
    return lock


def braid_path(sx):
    a = hp((sx * 0.17, 0.0, 1.6))
    return [a, a + v3((sx * 0.045, -0.06, -0.11)), v3((sx * 0.2, -0.14, 1.3)), v3((sx * 0.18, -0.18, 1.12)), v3((sx * 0.165, -0.19, 0.94))]


def hair_field(seed=3):
    """Center-parted near-black hair: smooth over the crown from a high, clean hairline, swept back behind her ears and
    falling down her back; two braids forward over her shoulders."""
    rng = np.random.RandomState(seed)
    fd = Field("Hair")
    hc, hrad = HEAD_C, HEAD_RAD
    pfront, pback = hp((0, -0.158, 1.835)), hp((0, 0.22, 1.585))
    slope = (pback[2] - pfront[2]) / (pback[1] - pfront[1])
    hl_n = norm((0, slope, -1.0))
    hairline = Func(lambda P: ((P - pfront.astype(F)) @ hl_n.astype(F)) + F(0.005) * NOISE(P * F(24)), hc - 0.5, hc + 0.5)
    fd.add(Inter(Ellipsoid(hc, hrad + 0.013), hairline, 0.02), 0.0)
    hull = Field("HairHull")
    hull.add(Ellipsoid(hc, hrad + 0.02), 0.0)
    hull.add(Ellipsoid(hp((0, 0.14, 1.67)), v3((0.19, 0.13, 0.19)) * HS), hr(0.08))
    hull.add(neck_prim(), 0.06)
    hull.add(traps(), 0.06)
    hull.add(Ellipsoid((0, 0.1, 1.15), (0.25, 0.14, 0.2)), 0.08)              # her back, for the long hair to lie on
    # from the parting: sideways first, then back behind the ears toward the nape
    for sx in (-1, 1):
        target = hp((sx * 0.1, 0.235, 1.56))
        for j in range(9):
            u = j / 8
            o = hp((sx * 0.014, -0.15 + 0.29 * u, 1.86 + 0.02 * math.sin(u * math.pi)))
            st, ok = ray_hit(hull, [o + v3((0, 0, 0.3))], [v3((0, 0, -1))], tmax=0.6)
            if not ok[0]:
                continue
            h0 = norm(v3((sx, 0.15 + 0.5 * u, -0.25)))
            def flow(p, k, h0=h0, target=target):
                w = min(1.0, (k + 1) / 5.0)
                return norm(h0 * (1 - w) + norm(target - p) * w)
            L = hr(0.36 - 0.12 * u) + rng.uniform(0, 0.015)
            segs = 9
            line = flow_line(hull, st[0], flow, segs, L / segs)
            if len(line) < 4:
                continue
            pts, ws, ts, ns = [], [], [], []
            mm = len(line) - 1
            w0 = hr(0.05) + rng.uniform(-0.004, 0.004)
            for k, p in enumerate(line):
                uu = k / mm
                nn = grad(hull, [p])[0].astype(np.float64)
                pts.append(p + nn * hr(0.003))
                ws.append(w0 * (0.75 + 0.25 * math.sin(min(1.0, uu / 0.3) * math.pi / 2)) * (1 - 0.35 * uu))
                ts.append(hr(0.014) * (1 - 0.3 * uu))
                ns.append(nn)
            fd.add(Lock(pts, ws, ts, ns, k=w0 * 0.3), hr(0.006))
            gp = [pts[k] + ns[k] * ts[k] for k in range(1, mm) if 0.15 < k / mm < 0.85]
            if len(gp) >= 2:
                fd.sub(Chain(gp, [hr(0.0032)] * len(gp), k=0.003), hr(0.003))
    # the long fall down her back
    for i in range(10):
        a = math.pi * (0.68 + 0.64 * (i + 0.5) / 10)
        hd = v3((math.sin(a), -math.cos(a), 0.0))
        o = hc + v3((0, 0.02, 0.03)) + hd * 0.5
        st, ok = ray_hit(hull, [o], [-hd], tmax=0.5)
        if not ok[0]:
            continue
        fan_lock(hull, st[0], hd * 0.25 + v3((0, 0, -1)), hr(0.5) + rng.uniform(0, 0.04), hr(0.09), hr(0.018), segs=11, gravity=0.25,
                 lift=hr(0.004), tip_up=hr(0.004), grooves=2, fd=fd, thin_root=True)
    # braids
    for sx in (-1, 1):
        path = braid_path(sx)
        def P_at(t):
            seg = min(int(t * (len(path) - 1)), len(path) - 2)
            u = t * (len(path) - 1) - seg
            return lerp(path[seg], path[seg + 1], u)
        nseg = 10
        for i in range(nseg):
            t0, t1 = i / nseg, (i + 1) / nseg
            a, b = P_at(t0), P_at(t1)
            w = hr(0.034 - 0.01 * t0)
            sgn = 1 if i % 2 else -1
            side = norm(np.cross(b - a, v3((0, -1, 0)))) if abs(norm(b - a)[1]) < 0.95 else v3((1, 0, 0))
            mid = (a + b) / 2 + side * sgn * w * 0.35
            fd.add(Ellipsoid(mid, (w, w * 0.7, np.linalg.norm(b - a) * 0.72), R=rot_from_axes(z_axis=norm(b - a + side * sgn * 0.02))), hr(0.006))
        end = path[-1]
        d = norm(path[-1] - path[-2])
        fd.add(Lock([end + d * 0.04, end + d * 0.09 + v3((0, -0.006, 0)), end + d * 0.15], [hr(0.028), hr(0.024), hr(0.005)],
                    [hr(0.015), hr(0.012), hr(0.004)], [v3((0, -1, 0))] * 3, k=hr(0.006)), hr(0.008))
    return fd


# ======================================================================================= circlet & antlers
CIRCLET_N = norm(v3((0, 0.42, 1.0)))
CIRCLET_C = HEAD_C + v3((0, -0.005, 0.02))


def circlet_hull():
    return Ellipsoid(HEAD_C, HEAD_RAD + 0.03)


def antler_curves(sx):
    """Main beam and two tines of one antler, rising from the circlet at the temple."""
    b0 = hp((sx * 0.15, -0.04, 1.84))
    b1 = b0 + v3((sx * 0.06, 0.02, 0.12))
    b2 = b0 + v3((sx * 0.16, 0.08, 0.24))
    b3 = b0 + v3((sx * 0.2, 0.06, 0.36))
    main = (b0, b1, b2, b3)
    t1 = bez3(*main, 0.35)
    t2 = bez3(*main, 0.68)
    tines = [(t1, t1 + v3((sx * 0.02, -0.08, 0.08))), (t2, t2 + v3((sx * -0.03, -0.07, 0.09)))]
    return main, tines


def antler_field():
    fd = Field("Antlers")
    rough = lambda P: F(0.003) * NOISE(P * F(40))
    for sx in (-1, 1):
        main, tines = antler_curves(sx)
        ts = np.linspace(0, 1, 14)
        pts = [bez3(*main, t) for t in ts]
        fd.add(Chain(pts, [0.031 * (1 - t) ** 0.6 + 0.009 for t in ts], k=0.008, disp=rough, disp_amp=0.004), 0.0)
        fd.add(Sphere(main[0], 0.03, disp=rough, disp_amp=0.004), 0.01)                       # burr
        for a, b in tines:
            fd.add(RoundCone(a, b, 0.019, 0.006, disp=rough, disp_amp=0.003), 0.01)
    return fd


def amber_field():
    """The amber stone on her circlet, amber beads on her necklace and at the ends of her braids."""
    fd = Field("Amber")
    front = hp((0, -0.19, 1.835))
    fd.add(Ellipsoid(front + v3((0, -0.012, 0)), (0.026, 0.014, 0.03)), 0.0)
    for sx in (-1, 1):
        path = braid_path(sx)
        d = norm(path[-1] - path[-2])
        fd.add(Ellipsoid(path[-1] + d * 0.012, (0.024, 0.024, 0.03), R=rot_from_axes(z_axis=d)), 0.0)
    for p, is_amber in necklace_beads():
        if is_amber:
            fd.add(Sphere(p, 0.016), 0.0)
    return fd


def necklace_points(n=26):
    hull = Field("NeckHull")
    for p, k in torso_prims():
        hull.add(p, k)
    hull.add(traps(), 0.05)
    hull.add(neck_prim(), 0.05)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        dirv = v3((math.sin(a) * 0.85, -math.cos(a), 0.0))
        front = max(0.0, -dirv[1])
        z = 1.43 - 0.13 * front ** 1.5
        o = v3((0, 0.07, z)) + norm(dirv) * 0.6
        h, ok = ray_hit(Func(lambda P: hull.eval(P) - F(0.025), (-1, -1, 0.8), (1, 1, 1.7)), [o], [-norm(dirv)], tmax=0.6)
        pts.append(h[0] + norm(dirv) * 0.008)
    return pts


def necklace_beads():
    nk = necklace_points()
    out = []
    front = sorted(range(len(nk)), key=lambda i: nk[i][1])[:9]
    for j, i in enumerate(sorted(front, key=lambda i: nk[i][0])):
        out.append((nk[i], j % 2 == 0))
    return out


# ======================================================================================= clothing
def dress_base():
    b = Field("DressBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(RoundCone((0, 0.04, 0.88), (0, 0.04, 0.42), 0.24, 0.31), 0.08)
    return b


def fur_field():
    """Pale fox-fur dress: sleeveless, straps over the shoulders, a scooped neckline, a ragged hem at the knee; fur
    cuffs on her boots."""
    fd = Field("Fur")
    base = dress_base()
    fur = lambda P: F(0.006) * NOISE(P * np.array([18, 18, 6], F)) + F(0.004) * NOISE(P * np.array([45, 45, 14], F) + 3) + F(0.0015) * NOISE(P * F(90))
    def keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        a = np.arctan2(x, -(y - F(0.04)))
        hem = F(0.46) + F(0.035) * np.abs(np.sin(a * F(6))) + F(0.014) * NOISE(P * F(9)) - z
        # neckline: scooped at the front, higher at the back; armholes
        neck_z = F(1.3) - F(0.05) * np.cos(a) * 0 - F(0.08) * np.clip(-np.cos(a), 0, 1)
        strap = np.abs(np.abs(x) - F(0.12)) - F(0.045)
        top = np.where(z > neck_z, strap, F(-1))
        arm = np.where((np.abs(x) > F(0.2)) & (z > F(1.18)), F(0.02), F(-1))
        return np.maximum(np.maximum(hem, top), arm)
    fd.add(Inter(Shell(base, 0.022, 0.034, pad=0.1, disp=fur, disp_amp=0.01), Func(keep, (-1, -1, 0.2), (1, 1, 1.6)), 0.008), 0.0)
    for side in ("R", "L"):
        an = J["ankle_" + side]
        fd.add(Torus(an + v3((0, 0.01, 0.12)), 0.064, 0.026, disp=fur, disp_amp=0.006), 0.0)
    return fd


SASH_Z = 0.86


def cloth_field():
    """Purple sash round her waist, knotted at her left hip with two hanging tails."""
    fd = Field("Cloth")
    base = dress_base()
    fold = lambda P: F(0.004) * np.sin(P[:, 2] * F(150)) + F(0.002) * NOISE(P * F(30))
    fd.add(Inter(Shell(base, 0.05, 0.022, pad=0.1, disp=fold, disp_amp=0.005),
                 Func(lambda P: np.abs(P[:, 2] - (F(SASH_Z) + F(0.03) * P[:, 1])) - F(0.045), (-1, -1, 0.6), (1, 1, 1.1)), 0.006), 0.0)
    kp, _ = ray_hit(Func(lambda P: base.eval(P) - F(0.07), (-1, -1, 0.5), (1, 1, 1.3)), [v3((0.6, -0.3, SASH_Z))], [norm(v3((-0.9, 0.45, 0)))], tmax=0.9)
    k0 = kp[0]
    fd.add(Ellipsoid(k0, (0.035, 0.03, 0.035)), 0.008)
    out = norm(v3((0.9, -0.45, 0)))
    for j, (dx, L) in enumerate(((-0.02, 0.3), (0.025, 0.24))):
        pts = [k0, k0 + out * 0.02 + v3((dx, 0, -L * 0.4)), k0 + out * 0.025 + v3((dx * 1.5, 0, -L))]
        fd.add(Lock(pts, [0.04, 0.036, 0.03], [0.007, 0.007, 0.006], [out] * 3, k=0.01, disp=fold, disp_amp=0.004), 0.006)
    return fd


def leather_field():
    """Circlet band, bracers, boots, the staff's grip wrap."""
    fd = Field("Leather")
    band = Inter(Shell(circlet_hull(), 0.008, 0.016, pad=0.06),
                 Func(lambda P: np.abs((P - CIRCLET_C.astype(F)) @ CIRCLET_N.astype(F) - F(0.085)) - F(0.016), HEAD_C - 0.4, HEAD_C + 0.4), 0.004)
    fd.add(band, 0.0)
    front = hp((0, -0.19, 1.835))
    fd.add(Ellipsoid(front + v3((0, 0.004, 0)), (0.036, 0.012, 0.04)), 0.006)                # setting behind the amber
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.68)
        fore = RoundCone(el, wr, 0.056, 0.043)
        fd.add(Inter(Shell(fore, 0.011, 0.015, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.065), c - 0.25, c + 0.25), 0.004), 0.0)
        an = J["ankle_" + side]
        sx = -1 if side == "R" else 1
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        shoe = Field("Boot")
        shoe.add(Sphere(an + v3((0, 0.04, -0.05)), 0.056), 0.0)
        shoe.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.065)), (0.064, 0.13, 0.038), 0.034, R=Rz), 0.034)
        shoe.add(RoundCone(an + v3((0, 0.01, -0.02)), an + v3((0, 0.01, 0.12)), 0.056, 0.052), 0.02)
        fd.add(Inter(Shell(shoe, 0.008, 0.016, pad=0.05), Func(lambda P, an=an: P[:, 2] - F(an[2] + 0.11), an - 0.3, an + 0.3), 0.004), 0.0)
    a0, ax2 = staff_axis()
    for i in range(4):
        fd.add(Torus(a0 + ax2 * (-0.05 + 0.04 * i), STAFF_R + 0.005, 0.009, R=rot_from_axes(z_axis=norm(ax2 + v3((0.3, 0, 0))))), 0.003)
    return fd


def bone_field():
    """Bone beads on her necklace (between the amber ones) and its cord, a bone armlet on her left arm."""
    fd = Field("Bone")
    nk = necklace_points()
    fd.add(Chain(nk + [nk[0]], [0.0055] * (len(nk) + 1), k=0.003), 0.0)
    for p, is_amber in necklace_beads():
        if not is_amber:
            fd.add(Cylinder(p, 0.012, 0.03, rr=0.005, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002)
    sh, el = J["shoulder_L"], J["elbow_L"]
    ax = norm(el - sh)
    c = lerp(sh, el, 0.62)
    fd.add(Inter(Shell(RoundCone(sh, el, 0.074, 0.056), 0.012, 0.016, pad=0.06),
                 Func(lambda P: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.02), c - 0.2, c + 0.2), 0.004), 0.0)
    return fd


# ======================================================================================= staff, orb, orbiting stones
STAFF_R = 0.028
ORB_S = 0.98
ORB_R = 0.075


def staff_axis():
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t


def staff_field():
    """Pale driftwood staff, its top opening into three curved claws round the orb."""
    fd = Field("Staff")
    a0, ax = staff_axis()
    u = norm(np.cross(ax, v3((0, 0, 1))))
    w = np.cross(ax, u)
    grain = lambda P: F(0.003) * NOISE(P * np.array([50, 50, 50], F))
    ss = np.linspace(-1.12, 0.86, 20)
    pts = [a0 + ax * s + 0.008 * math.sin(s * 4.0) * u for s in ss]
    fd.add(Chain(pts, [STAFF_R + 0.006 * max(0.0, (s - 0.5) / 0.4) for s in ss], k=0.01, disp=grain, disp_amp=0.004), 0.0)
    oc = a0 + ax * ORB_S
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.2
        d = norm(u * math.cos(a) + w * math.sin(a))
        p0 = a0 + ax * 0.84
        p1 = a0 + ax * 0.9 + d * 0.06
        p2 = oc + d * (ORB_R + 0.035)
        p3 = oc + d * (ORB_R * 0.4) + ax * (ORB_R + 0.04)
        tpts = [bez3(p0, p1, p2, p3, t) for t in np.linspace(0, 1, 9)]
        fd.add(Chain(tpts, [0.02 - 0.015 * t for t in np.linspace(0, 1, 9)], k=0.008, disp=grain, disp_amp=0.003), 0.01)
    fd.add(Sphere(a0 + ax * -1.12, 0.032), 0.01)
    return fd


def orb_field():
    fd = Field("Orb")
    a0, ax = staff_axis()
    fd.add(Sphere(a0 + ax * ORB_S, ORB_R, disp=lambda P: F(0.003) * NOISE(P * F(30)), disp_amp=0.004), 0.0)
    return fd


ORBIT_R, ORBIT_Z = 0.8, 0.98
ORBIT_C = v3((0.0, 0.03, ORBIT_Z))


def orbit_stones():
    out = []
    for k, dz in enumerate((0.05, -0.03, 0.0)):
        a = math.pi / 2 + k * 2 * math.pi / 3
        out.append((ORBIT_C + v3((math.cos(a) * ORBIT_R, math.sin(a) * ORBIT_R, dz)), 0.075 - 0.008 * k, 300 + k, a))
    return out


def orbit_field():
    """Three round river stones with a spiral carved and painted on each, circling her."""
    fd = Field("Orbit")
    for c, r, seed, a in orbit_stones():
        out = v3((math.cos(a), math.sin(a), 0))
        fd.add(Stone(c, r, seed=seed, cuts=6, squash=(1.0, 1.0, 0.8), soft=0.2, depth=(0.82, 0.95), noise=0.02), 0.0)
        fd.paint(Func(lambda P, c=c, out=out, r=r: _spiral_on(P, c + out * r * 0.7, out, r * 0.55), c - 0.2, c + 0.2), 5)
    return fd


def _spiral_on(P, c, nrm, r1, turns=2.0, w=0.006):
    """Distance to a spiral drawn on the plane through c facing nrm (any depth up to 0.05)."""
    n = norm(nrm)
    u = norm(np.cross(n, v3((0, 0, 1))))
    vv = np.cross(n, u)
    q = P - c.astype(F)
    x, y = q @ u.astype(F), q @ vv.astype(F)
    rr = np.sqrt(x * x + y * y)
    th = np.arctan2(y, x)
    k = F(r1 / (turns * 2 * math.pi))
    m = np.clip(np.round((rr / k - th) / F(2 * math.pi)), 0, turns)
    d = np.abs(rr - k * (th + F(2 * math.pi) * m))
    d = np.where(rr > F(r1 + w), rr - F(r1), d)
    return np.maximum(d - F(w), np.abs(q @ n.astype(F)) - F(0.05))


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.236, 1.62)), 0.045, 0.45)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.1, -0.15, 1.6)), 0.06, 0.55), (hp((sx * 0.176, 0.035, 1.66)), 0.05, 0.5),
                (J["elbow_" + sd] + v3((0, 0.022, 0)), 0.05, 0.25), (J["knee_" + sd] + v3((0, -0.026, 0)), 0.06, 0.3)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.01, 0.028, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "mara"
ROOT_NAME = "HeroMaraHQ"
TEX_PREFIX = "hero"
MAT_NAME = "MaraMat"
MESH_NAME = "Mara"
BASE_MODULE = "mara_base"
ANIM_MODULE = "anim_mara"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Antlers", "Amber", "Fur", "Cloth", "Leather", "Bone", "Staff", "Orb", "Orbit"]
REGION_PARTS = ("Skin", "Orbit")
BLACK_HAIR = {"name": "HQ_BlackHair", "base": (0.09, 0.07, 0.07), "hi": (0.3, 0.24, 0.24), "low": (0.04, 0.03, 0.03),
              "streak": (0.05, 0.04, 0.04), "tint": (0.18, 0.12, 0.1)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_MaraSkin", "base": (0.8, 0.58, 0.44), "ruddy": (0.84, 0.5, 0.42), "lips": (0.72, 0.4, 0.4),
                      "brow": ((0.07, 0.05, 0.05), (0.16, 0.11, 0.09)), "paint": (0.85, 0.52, 0.14),
                      "extra": ((8, (0.06, 0.04, 0.04), 0.5),)}),
    "Hair": ("hair", BLACK_HAIR),
    "Antlers": ("bone", {"name": "HQ_Antler"}),
    "Fur": ("fur", {"name": "HQ_FoxFur", "base": (0.8, 0.78, 0.74), "tip": (0.97, 0.96, 0.94)}),
    "Cloth": ("cloth", {"name": "HQ_PurpleSash", "col": (0.48, 0.24, 0.66)}),
    "Leather": ("leather", {"name": "HQ_MaraLeather", "base": (0.42, 0.26, 0.15)}),
    "Staff": ("bone", {"name": "HQ_Driftwood"}),
    "Orb": ("glow_ball", {"name": "HQ_AmberOrb", "col": (1.0, 0.62, 0.16)}),
    "Orbit": ("stone", {"name": "HQ_OrbitStone", "paint": True, "scale": 0.5}),
}
GLOW = {"Orb": ((1.0, 0.55, 0.12), 1.3)}            # stronger washes out to white in game
SPLIT = {"Orbit": ("SpinSlowStones", tuple(ORBIT_C))}          # parts split off as their own (unskinned) mesh after baking
LOW_TARGETS = {"Skin": 6600, "Hair": 2600, "Teeth": 60, "Antlers": 700, "Amber": 300, "Fur": 2000, "Cloth": 700, "Leather": 1300,
               "Bone": 500, "Staff": 900, "Orb": 300, "Orbit": 600}
AO_EXCLUDE = ["Bone", "Amber", "Staff", "Orb", "Orbit", "Antlers"]
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
    a0, ax = staff_axis()
    oc = a0 + ax * ORB_S
    return [("orb", oc, oc + ax * 0.12, "hand.R")]


def _near_staff(p, pad=0.02):
    a0, ax = staff_axis()
    q = np.array(p) - a0
    s = q @ ax
    r = np.linalg.norm(q - ax * s)
    return -1.2 < s < ORB_S + 0.2 and r < 0.13 + pad


def hair_weights(ob, skin_ob, arm):
    groups = {}
    z1, z0 = hp((0, 0, 1.56))[2], 0.95
    for v in ob.data.vertices:
        p = v.co
        if p.z < z1:
            t = max(0.0, min(1.0, (z1 - p.z) / (z1 - z0)))
            _blend_add(ob, groups, v.index, {"head": 1.0 - 0.75 * t, "neck": 0.25 * t, "chest": 0.4 * t, "spine": 0.1 * t})
        else:
            _blend_add(ob, groups, v.index, {"head": 1.0})


def amber_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z > hp((0, 0, 1.7))[2]:
            w = {"head": 1.0}
        elif p.z < 1.05:                                  # braid ends
            w = {"head": 0.25, "neck": 0.25, "chest": 0.5}
        else:
            w = {"chest": 1.0}
        _blend_add(ob, groups, v.index, w)


def leather_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "shin.R", "shin.L", "foot.R", "foot.L", "head"})
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z > 1.6:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"head": 1.0})
        elif _near_staff(p) and p.x < -0.45:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"hand.R": 1.0})


def bone_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.L", "upperarm.L"}, caps={"upperarm.L": 1.0})
    groups = {}
    for v in ob.data.vertices:
        if v.co.z > 1.25 and abs(v.co.x) < 0.25:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"chest": 0.8, "neck": 0.2})


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Antlers": ("rigid", "head"),
        "Amber": ("custom", amber_weights),
        "Fur": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "thigh.R", "thigh.L", "shin.R", "shin.L"},
                {"thigh.R": 0.45, "thigh.L": 0.45, "shin.R": 1.0, "shin.L": 1.0}),
        "Cloth": ("transfer", TORSO | {"thigh.L", "thigh.R"}, {"thigh.L": 0.3, "thigh.R": 0.3}),
        "Leather": ("custom", leather_weights), "Bone": ("custom", bone_weights),
        "Staff": ("rigid", "hand.R"), "Orb": ("rigid", "orb"), "Orbit": ("rigid", "root"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Amber",):
        return 1.2
    if part in ("Bone", "Staff"):
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0026 if fine else 0.0034),
        ("Antlers", antler_field(), 0.0018 if fine else 0.0025),
        ("Amber", amber_field(), 0.0015 if fine else 0.002),
        ("Fur", fur_field(), 0.003 if fine else 0.0042),
        ("Cloth", cloth_field(), 0.0024 if fine else 0.0032),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Bone", bone_field(), 0.0015 if fine else 0.002),
        ("Staff", staff_field(), 0.0022 if fine else 0.003),
        ("Orb", orb_field(), 0.002),
        ("Orbit", orbit_field(), 0.0025 if fine else 0.0035),
    ]
