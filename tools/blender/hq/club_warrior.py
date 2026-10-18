"""The Club Warrior (HQ tower). Rest pose = A-pose, facing -Y, feet at z=0; right side = -X.

A hulking, top-heavy brute: huge shoulders and traps, long Popeye arms, barrel chest and a solid gut on short sturdy
legs. A wild red mane, a bushy red beard with one braid, a broken boxer's nose, a clenched-teeth snarl
with a gap, blue war paint (a band across the eyes, claw slashes on the chest). A grey wolf's hide is slung over his
left shoulder: its head sits on the shoulder like a pauldron, the hide crosses his chest and back to the right hip
where the tail hangs. Hide kilt with a rope belt, leather shin wraps, a bone cuff, and a huge log club
studded with flint shards."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, grad, project_to, flow_line, Stone, lerp
from ugo import stripe2d, bez3, _blend_add

J = {
    "root": (0.0, 0.03, 0.78),
    "spine": (0.0, 0.03, 0.97),
    "chest": (0.0, 0.06, 1.22),
    "neck": (0.0, 0.1, 1.5),
    "head": (0.0, 0.03, 1.6),
    "head_end": (0.0, -0.02, 1.98),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.5, 0.09, 1.45)
    J["elbow_" + _s] = (_x * 0.77, 0.12, 1.15)
    J["wrist_" + _s] = (_x * 0.96, 0.05, 0.89)
    J["hip_" + _s] = (_x * 0.17, 0.04, 0.72)
    J["knee_" + _s] = (_x * 0.205, 0.0, 0.41)
    J["ankle_" + _s] = (_x * 0.215, 0.06, 0.11)
    J["toe_" + _s] = (_x * 0.24, -0.18, 0.035)
J = {k: v3(v) for k, v in J.items()}

# skin labels
SKIN, NAIL, LIP, MOUTH, BROW, PAINT, SCAR = 0, 1, 2, 3, 4, 5, 6
# wolf hide labels
WFUR, WNOSE, WINNER, WSOCKET, WSUEDE, WMUZZLE = 0, 7, 8, 9, 10, 11

# head: designed in the Rock Slinger's head coordinates, pushed forward (hunch) and scaled about the top of the neck
HS = 1.06
DY = -0.035
HPIV = v3((0.0, 0.02, 1.52))


def hp(p):
    p = v3(p) + v3((0, DY, 0))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


HEAD_C = hp((0.0, 0.035, 1.72))
HEAD_RAD = v3((0.19, 0.195, 0.175)) * HS
EYE_R = hr(0.035)


def eye_c(sx):
    return hp((sx * 0.07, -0.152, 1.668))


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


HAND_S = 1.24


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.036


def hand(fd, side, fist, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.078 * s
    fd.add(RoundBox(c, v3((0.066, 0.036, 0.068)) * s, 0.032 * s, R=Rp), 0.03, SKIN)
    fd.add(Ellipsoid(c - n * 0.012 + t * 0.032 * s - f * 0.01, v3((0.037, 0.032, 0.053)) * s, R=Rp), 0.02, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = (1.45, 1.6, 1.2) if fist else (0.3, 0.5, 0.35)
    offs = (0.045, 0.015, -0.015, -0.045)
    lens = (0.95, 1.0, 0.95, 0.8)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.144 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.024 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.007), 0.013, SKIN)
        fd.add(Sphere(pts[0] - n * 0.013, 0.019 * s), 0.01, SKIN)          # big knuckles
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.007 - back * 0.014, (0.015, 0.008, 0.017), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.047 * s + t * 0.054 * s + n * 0.012
    if fist:
        d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
        d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:
        d1 = norm(f * 0.55 + t * 0.75 + n * 0.25)
        d2 = norm(f * 0.8 + t * 0.35 + n * 0.45)
    p1 = tb + d1 * 0.052 * s
    p2 = p1 + d2 * 0.044 * s
    fd.add(Chain([tb, p1, p2], [0.028 * s, 0.025 * s, 0.022 * s], k=0.008), 0.02, SKIN)
    back = norm(np.cross(d2, curl_ax)) if fist else -n
    fd.paint(Ellipsoid(p2 - d2 * 0.009 - back * 0.014, (0.017, 0.009, 0.019), R=rot_from_axes(z_axis=d2, y_axis=back)), NAIL)


def foot(fd, side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.14)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    s = 1.1
    fd.add(Sphere(an + v3((0, 0.05, -0.052)), 0.068), 0.03, SKIN)
    fd.add(RoundBox(an + fwd * 0.08 * s + v3((0, 0, -0.07)), v3((0.082, 0.13, 0.04)) * s, 0.038, R=Rz), 0.035, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.04 + v3((0, 0, -0.03)), (0.078, 0.096, 0.055), R=Rz), 0.03, SKIN)
    inner = -sx
    toes = [(0.06, 0.034), (0.025, 0.026), (-0.006, 0.024), (-0.034, 0.022), (-0.058, 0.02)]
    for i, (o, r) in enumerate(toes):
        base = an + fwd * ((0.18 - 0.012 * i - (0.0 if i else -0.004)) * s) + rgt * (o * inner * s) + v3((0, 0, -0.08))
        tip = base + fwd * (0.032 + r * 0.4) + v3((0, 0, -0.004))
        base[2] = 0.027 + r * 0.55
        tip[2] = 0.022 + r * 0.5
        fd.add(RoundCone(base, tip, r, r * 0.92), 0.012, SKIN)
        tn = norm(tip - base)
        fd.paint(Ellipsoid(tip + v3((0, 0, r * 0.55)), (r * 0.7, r * 0.75, r * 0.35), R=rot_from_axes(y_axis=tn, z_axis=(0, 0, 1))), NAIL)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.06, 0.0, 0.0)), 0.029), 0.02, SKIN)


# ======================================================================================= head
def hstripe(a, b, ra, rb, y0=-0.4, y1=0.02):
    """stripe2d with its ends given in head coordinates (x, z)."""
    m = lambda q: (q[0] * HS, HPIV[2] + (q[1] - HPIV[2]) * HS)
    return stripe2d(m(a), m(b), ra * HS, rb * HS, y0=y0, y1=y1)


def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)                                         # low, wide cranium
    fd.add(E((0, -0.045, 1.572), (0.205, 0.16, 0.15)), 0.07, SKIN)                          # heavy jaw
    fd.add(E((0, -0.14, 1.487), (0.132, 0.092, 0.08)), 0.05, SKIN)                          # jutting chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.118, -0.122, 1.628), 0.06), 0.045, SKIN)                          # cheekbones
        fd.add(S((sx * 0.158, -0.035, 1.528), 0.082), 0.05, SKIN)                          # wide jaw corners
        # a heavy, straight brow shelf
        pts = [hp((sx * 0.16, -0.05, 1.728)), hp((sx * 0.122, -0.132, 1.735)), hp((sx * 0.06, -0.182, 1.731)), hp((0.0, -0.196, 1.733))]
        fd.add(Chain(pts, [hr(0.024), hr(0.043), hr(0.05), hr(0.052)], k=hr(0.03)), hr(0.045), SKIN)
    fd.add(E((0, -0.172, 1.762), (0.074, 0.04, 0.045)), hr(0.04), SKIN)
    # bushy brows, slammed down toward the nose
    for sx in (-1, 1):
        pts = [hp((sx * 0.018, -0.234, 1.738)), hp((sx * 0.058, -0.224, 1.758)), hp((sx * 0.102, -0.198, 1.773)), hp((sx * 0.142, -0.158, 1.776)),
               hp((sx * 0.168, -0.128, 1.774))]
        brow = Chain(pts, [hr(0.022), hr(0.027), hr(0.025), hr(0.018), hr(0.006)], k=hr(0.013),
                     disp=lambda P: F(0.003) * NOISE(P * np.array([30, 30, 90], F)), disp_amp=0.004)
        fd.add(brow, hr(0.012), BROW)
        fd.paint(Chain(pts, [hr(0.028), hr(0.033), hr(0.031), hr(0.023), hr(0.01)], k=hr(0.013)), BROW)
    # small, deep-set eyes under the shelf, lids low (a glower)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.009)), Plane(ec + v3((0, 0, hr(0.008))), (sx * 0.25, 0.1, -1.0)), hr(0.004))
        fd.add(up, hr(0.006), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.007)), Plane(ec + v3((0, 0, -hr(0.021))), (sx * -0.12, 0.1, 1.0)), hr(0.004))
        fd.add(lo, hr(0.006), SKIN)
    # broad, broken boxer's nose: the bridge kinks to his left
    fd.add(RoundCone(hp((0, -0.194, 1.71)), hp((0.014, -0.232, 1.658)), hr(0.031), hr(0.035)), hr(0.02), SKIN)
    fd.add(RoundCone(hp((0.014, -0.232, 1.658)), hp((0.0, -0.248, 1.618)), hr(0.035), hr(0.042)), hr(0.018), SKIN)
    fd.add(E((0, -0.248, 1.6), (0.064, 0.05, 0.048)), hr(0.018), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.054, -0.218, 1.588), 0.036), hr(0.016), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.027, -0.238, 1.567)), v3((0.014, 0.017, 0.009)) * HS, R=euler(0.4, 0, sx * 0.3)), hr(0.006))
    # clenched-teeth snarl: a wide opening, upper lip lifted, corners pulled down
    slot = [hp((-0.094, -0.162, 1.526)), hp((-0.052, -0.197, 1.531)), hp((0, -0.212, 1.533)), hp((0.052, -0.197, 1.531)), hp((0.094, -0.162, 1.526))]
    fd.sub(Chain(slot, [hr(0.012), hr(0.021), hr(0.023), hr(0.021), hr(0.012)], k=hr(0.01)), hr(0.008))
    fd.paint(Chain(slot, [hr(0.012), hr(0.021), hr(0.024), hr(0.021), hr(0.012)], k=hr(0.01)), MOUTH)
    up_lip = [(-0.1, -0.155, 1.532), (-0.054, -0.2, 1.557), (0, -0.218, 1.559), (0.054, -0.2, 1.557), (0.1, -0.155, 1.532)]
    lo_lip = [(-0.092, -0.158, 1.515), (-0.05, -0.196, 1.502), (0, -0.21, 1.499), (0.05, -0.196, 1.502), (0.092, -0.158, 1.515)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.009), hr(0.013), hr(0.014), hr(0.013), hr(0.009)], k=hr(0.01)), hr(0.008), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.009), hr(0.013), hr(0.014), hr(0.013), hr(0.009)], k=hr(0.01)), hr(0.008), LIP)
    for sx in (-1, 1):                                              # snarl creases beside the nose
        fd.add(Chain([hp((sx * 0.065, -0.205, 1.6)), hp((sx * 0.095, -0.18, 1.56)), hp((sx * 0.105, -0.16, 1.53))], [hr(0.012), hr(0.011), hr(0.008)],
                     k=hr(0.008)), hr(0.012), SKIN)
    # small cauliflower ears
    for sx in (-1, 1):
        c = hp((sx * 0.185, 0.04, 1.655))
        fd.add(Ellipsoid(c, v3((0.03, 0.05, 0.062)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        for j, (dy, dz) in enumerate(((-0.012, 0.03), (0.018, 0.012), (0.0, -0.025))):
            fd.add(Sphere(c + v3((sx * 0.018, dy, dz)) * HS, hr(0.016)), hr(0.01), SKIN)
    # blue war paint: a band across the eyes, temple to temple
    fd.paint(hstripe((-0.176, 1.672), (0.176, 1.672), 0.026, 0.026), PAINT)
    # an old scar from his right brow down across the cheek
    fd.paint(hstripe((-0.112, 1.745), (-0.078, 1.655), 0.005, 0.0035), SCAR)


# ======================================================================================= body
def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.25), (0.4, 0.29, 0.32), R=euler(-0.1, 0, 0)), 0.0),               # barrel ribcage
        (Ellipsoid((0, 0.15, 1.3), (0.45, 0.21, 0.25)), 0.06),                                    # back / lats
        (RoundBox((0.17, -0.2, 1.34), (0.17, 0.045, 0.1), 0.045, R=euler(0.14, 0, 0.25)), 0.05),  # pecs
        (RoundBox((-0.17, -0.2, 1.34), (0.17, 0.045, 0.1), 0.045, R=euler(0.14, 0, -0.25)), 0.05),
        (Ellipsoid((0, -0.06, 1.0), (0.3, 0.27, 0.25)), 0.08),                                    # a solid gut
        (Ellipsoid((0, 0.04, 0.8), (0.28, 0.22, 0.17)), 0.08),                                    # pelvis
    ]


def traps():
    return Ellipsoid((0, 0.13, 1.53), (0.36, 0.17, 0.13), R=euler(0.3, 0, 0))


def neck_prim():
    return RoundCone((0, 0.09, 1.46), hp((0, 0.02, 1.575)), 0.16, hr(0.125))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.025, -0.005, 0.015)), 0.172)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(Ellipsoid((0, -0.255, 1.03), (0.05, 0.02, 0.03)), 0.04, SKIN)                     # navel bump
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.06, SKIN)
        fd.add(RoundCone(sh, el, 0.14, 0.105), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.035, 0)), (0.132, 0.136, 0.18), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)   # biceps
        fd.add(Ellipsoid(lerp(sh, el, 0.45) + v3((sx * 0.02, 0.05, 0)), (0.11, 0.1, 0.16), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)  # triceps
        fd.add(RoundCone(el, wr, 0.105, 0.08), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.32) + v3((sx * 0.012, 0, 0)), (0.145, 0.125, 0.18), R=rot_from_axes(z_axis=wr - el)), 0.045, SKIN)  # Popeye forearm
        fd.add(Sphere(el + v3((0, 0.035, 0)), 0.08), 0.03, SKIN)
        hand(fd, side, fist=True)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.17, 0.112), 0.07, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.025, 0)), (0.158, 0.148, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.05, SKIN)
        fd.add(Sphere(kn + v3((0, -0.038, 0.0)), 0.088), 0.04, SKIN)
        fd.add(RoundCone(kn, an, 0.108, 0.072), 0.04, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.04, 0)), (0.126, 0.12, 0.15), R=rot_from_axes(z_axis=an - kn)), 0.045, SKIN)
        foot(fd, side)
    head(fd)
    # blue war paint: three claw slashes down his right pec, two bands round the right upper arm
    for k in range(3):
        x0 = -0.15 - 0.058 * k
        fd.paint(stripe2d((x0 - 0.03, 1.45 - 0.012 * k), (x0 + 0.045, 1.22 - 0.012 * k), 0.017, 0.006, y0=-0.5, y1=-0.08), PAINT)
    sh, el = J["shoulder_R"], J["elbow_R"]
    ax = norm(el - sh)
    for t0 in (0.52, 0.65):
        c = lerp(sh, el, t0)
        fd.paint(Func(lambda P, c=c: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.019), c - 0.3, c + 0.3), PAINT)


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
    """Clenched teeth, both rows, with a gap where he lost one (his left upper incisor)."""
    fd = Field("Teeth")
    n = 8
    for row, (z0, y0, h) in enumerate(((1.538, -0.205, 0.0125), (1.513, -0.199, 0.0105))):
        for i in range(n):
            u = (i - (n - 1) / 2) / ((n - 1) / 2)
            if row == 0 and i == 4:
                continue                                           # the gap
            x = u * 0.078
            y = y0 + 0.04 * u * u
            z = z0 + (0.012 if row == 0 else -0.004) * u * u
            w = 0.0105 if abs(u) < 0.35 else 0.0092
            fd.add(RoundBox(hp((x, y, z)), v3((w, 0.008, h)) * HS, hr(0.0045), R=euler(0.1 * (1 - 2 * row), 0, -u * 0.62)), 0.0)
    return fd


# ======================================================================================= hair & beard
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
                if u < 0.15 or u > 0.74:
                    continue
                tng = norm(pts[min(i + 1, m)] - pts[i - 1])
                lat = norm(np.cross(tng, ns[i]))
                gp.append(pts[i] + lat * ws[i] * off * 1.2 + ns[i] * ts[i] * 1.04)
            if len(gp) >= 2:
                fd.sub(Chain(gp, [hr(0.0045)] * len(gp), k=0.003), hr(0.004))
    return lock


def head_hull():
    fd = Field("HeadHull")
    head(fd)
    fd.add(neck_prim(), 0.05)
    fd.add(traps(), 0.06)
    fd.add(Ellipsoid((0, 0.04, 1.3), (0.42, 0.33, 0.36), R=euler(-0.1, 0, 0)), 0.06)
    return fd


KNOT_C = hp((0.0, 0.13, 1.95))


def hair_field(seed=3):
    """Wild red mane: a whorl of thick, spiky locks from the crown swept back and out, the front swept up and back off a
    low hairline, a ragged lower layer flaring out at the sides and the nape."""
    rng = np.random.RandomState(seed)
    fd = Field("Hair")
    hc, hrad = HEAD_C, HEAD_RAD
    pfront, pback = hp((0, -0.15, 1.79)), hp((0, 0.22, 1.585))
    slope = (pback[2] - pfront[2]) / (pback[1] - pfront[1])
    hl_n = norm((0, slope, -1.0))
    hairline = Func(lambda P: ((P - pfront.astype(F)) @ hl_n.astype(F)) + F(0.012) * NOISE(P * F(24)), hc - 0.5, hc + 0.5)
    fd.add(Inter(Ellipsoid(hc, hrad + 0.014), hairline, 0.02), 0.0)
    hull = Field("HairHull")
    hull.add(Ellipsoid(hc, hrad + 0.02), 0.0)
    hull.add(Ellipsoid(hp((0, 0.15, 1.66)), v3((0.2, 0.13, 0.19)) * HS), hr(0.08))
    crown = hc + v3((0, 0.07, hrad[2] * 0.95))
    # layer 1: the crown whorl, short at the front, longest at the back, tips kicking up
    n1 = 16
    for i in range(n1):
        a = 2 * math.pi * i / n1 + rng.uniform(-0.07, 0.07)
        hd = v3((math.sin(a), -math.cos(a), 0.0))
        frontness = max(0.0, math.cos(a))
        backness = max(0.0, -math.cos(a))
        L = hr(0.19 + 0.12 * backness + 0.05 * (1 - frontness - backness) - 0.05 * frontness ** 2) + rng.uniform(0, 0.025)
        fan_lock(hull, crown + hd * 0.03, hd, L, hr(0.105), hr(0.038), segs=8, gravity=0.12 + 0.45 * (1 - frontness),
                 lift=hr(0.05 + 0.02 * frontness), tip_up=hr(0.045), grooves=2, fd=fd)
    # layer 2: ragged locks under it at the sides and back, flaring out
    n2 = 12
    for i in range(n2):
        a = math.pi * (0.33 + 1.34 * (i + 0.5) / n2) + rng.uniform(-0.05, 0.05)
        hd = v3((math.sin(a), -math.cos(a), 0.0))
        o = hc + v3((0, 0.02, -0.03)) + hd * 0.5
        st, ok = ray_hit(hull, [o], [-hd], tmax=0.5)
        if not ok[0]:
            continue
        backness = max(0.0, -math.cos(a))
        L = hr(0.12 + 0.08 * backness) + rng.uniform(0, 0.02)
        fan_lock(hull, st[0], hd * 0.7 + v3((0, 0, -0.5)), L, hr(0.088), hr(0.03), segs=6, gravity=0.2,
                 lift=hr(0.06), tip_up=hr(0.035), grooves=1, fd=fd)
    # front: thick locks swept up and back off the hairline
    nf = 8
    for i in range(nf):
        u = -1 + 2 * (i + 0.5) / nf
        x = u * 0.15
        hz = pfront[2] + slope * (hp((0, -0.15 + 0.1 * u * u, 0))[1] - pfront[1])
        o = hp((x, -0.6, 0)) + v3((0, 0, hz - hp((0, 0, 0))[2] + hr(0.032)))
        st, ok = ray_hit(hull, [o], [v3((0, 1, 0))], tmax=0.8)
        if not ok[0]:
            continue
        hd = norm(v3((u * 0.45, 1.0, 0.0)))
        fan_lock(hull, st[0], hd, hr(0.17 + rng.uniform(0, 0.04)), hr(0.092), hr(0.034), segs=6, gravity=-0.3,
                 lift=hr(0.04), tip_up=hr(0.03), grooves=2, fd=fd, thin_root=True)
    return fd


def beard_field(seed=5):
    """Bushy red beard, widest at the jaw (kept short so his chest shows), a heavy moustache and one braid hanging from
    the chin with a bone bead."""
    rng = np.random.RandomState(seed)
    fd = Field("Beard")
    hull = head_hull()
    hull.add(Ellipsoid(hp((0, -0.15, 1.46)), v3((0.13, 0.08, 0.095)) * HS), hr(0.05))
    def root_at(u, zb=1.462):
        ax = abs(u) * 0.18
        z = zb + 0.2 * (ax / 0.18) ** 1.8
        th = u * 1.8
        d = norm(v3((math.sin(th), -math.cos(th), 0.0)) * 1.0 + v3((0, 0, (z - 1.56) * 2.5)))
        o = hp((0, -0.02, z)) + d * 0.5
        h, ok = ray_hit(hull, [o], [-d], tmax=0.5)
        return h[0] if ok[0] else None
    nb = 19
    for i in range(nb):
        u = -1 + 2 * i / (nb - 1)
        r = root_at(u * 0.98)
        if r is None:
            continue
        front = 1 - abs(u)
        hd = v3((-u * 0.55, -0.3, -1.0))
        L = hr(0.13 + 0.06 * front ** 1.2) + rng.uniform(0, 0.015)
        fan_lock(hull, r + v3((0, 0, 0.008)), hd, L, hr(0.07 + 0.03 * front), hr(0.026 + 0.012 * front), segs=7, gravity=0.2,
                 lift=hr(0.035 + 0.04 * front ** 1.5), tip_up=hr(0.012), grooves=2, fd=fd, thin_root=True)
    for i in range(5):                                       # under the chin: fills out the beard
        u = (-1 + 2 * i / 4) * 0.45
        r = root_at(u, zb=1.47)
        if r is None:
            continue
        fan_lock(hull, r + v3((0, 0.01, -0.01)), v3((-u * 0.4, -0.15, -1.0)), hr(0.11), hr(0.075), hr(0.026), segs=6, gravity=0.25,
                 lift=hr(0.02), tip_up=hr(0.01), grooves=1, fd=fd, thin_root=True)
    for sx in (-1, 1):                                       # moustache
        pts = [hp((sx * 0.004, -0.245, 1.568)), hp((sx * 0.055, -0.236, 1.564)), hp((sx * 0.108, -0.2, 1.548)), hp((sx * 0.138, -0.166, 1.51)),
               hp((sx * 0.148, -0.152, 1.47))]
        ns = [norm(v3((sx * 0.3, -1.0, 0.3)))] * 5
        fd.add(Lock(pts, [hr(0.022), hr(0.034), hr(0.033), hr(0.022), hr(0.004)], [hr(0.017), hr(0.021), hr(0.02), hr(0.014), hr(0.003)], ns,
                    k=hr(0.013)), hr(0.008))
        for g in (-0.25, 0.25):
            gp = [lerp(pts[j], pts[j + 1], 0.5) + v3((0, -0.013, g * 0.02)) for j in range(3)]
            fd.sub(Chain(gp, [hr(0.004)] * 3, k=0.002), hr(0.003))
    # the braid: alternating plaits from the point of the beard down onto his chest
    top = hp((0, -0.27, 1.34))
    bot = BEAD_C + v3((0, 0, 0.03))
    nseg = 6
    for i in range(nseg):
        t0, t1 = i / nseg, (i + 1) / nseg
        a, b = lerp(top, bot, t0), lerp(top, bot, t1)
        sgn = 1 if i % 2 else -1
        w = hr(0.033 - 0.008 * t0)
        mid = (a + b) / 2 + v3((sgn * w * 0.35, 0, 0))
        fd.add(Ellipsoid(mid, (w, w * 0.65, np.linalg.norm(b - a) * 0.72), R=rot_from_axes(z_axis=norm(b - a + v3((sgn * 0.02, 0, 0))))), hr(0.005))
    tip = BEAD_C + v3((0, -0.004, -0.03))
    fd.add(Lock([tip, tip + v3((0.006, -0.01, -0.045)), tip + v3((0.01, -0.012, -0.09))], [hr(0.032), hr(0.026), hr(0.004)],
                [hr(0.015), hr(0.012), hr(0.003)], [v3((0, -1, 0))] * 3, k=hr(0.006)), hr(0.006))
    return fd


BEAD_C = hp((0, -0.29, 1.15))


# ======================================================================================= the wolf hide
WOLF_C = v3((0.47, -0.01, 1.68))          # the wolf's head on his left shoulder (cranium centre)
WOLF_FWD = norm(v3((0.18, -1.0, -0.1)))


def wolf_frame():
    f = WOLF_FWD
    up = norm(v3((0.15, 0, 1.0)) - f * (v3((0.15, 0, 1.0)) @ f))
    side = np.cross(up, f)
    return f, up, side


def pelt_base():
    b = Field("PeltBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(deltoid("L"), 0.06)
    b.add(RoundCone(J["shoulder_L"], J["elbow_L"], 0.14, 0.105), 0.05)
    return b


SASH_C = v3((0.06, 0.03, 1.2))
SASH_N = norm(v3((0.7, 0.0, -0.72)))


def wolf_field():
    """The wolf: its head as a pauldron on his left shoulder (long snout, black nose, fangs, tall pointed ears, cheek
    ruffs, dark eye holes), its hide a broad sash across chest and back to the right hip, its forelegs hanging over his
    upper arm and its bushy tail at his right hip."""
    fd = Field("Wolf")
    base = pelt_base()
    fur = lambda P: F(0.006) * NOISE(P * np.array([16, 16, 5], F)) + F(0.004) * NOISE(P * np.array([42, 42, 12], F) + 3) + F(0.0015) * NOISE(P * F(90))
    def band(P):
        d = np.abs((P - SASH_C.astype(F)) @ SASH_N.astype(F))
        w = F(0.16) + F(0.035) * np.abs(np.sin(P[:, 2] * F(31) + P[:, 0] * F(17))) + F(0.014) * NOISE(P * F(13))
        return d - w
    fd.add(Inter(Shell(base, 0.022, 0.044, pad=0.1, disp=fur, disp_amp=0.012), Func(band, (-1, -1, 0.5), (1, 1, 2.0)), 0.008), 0.0, WFUR)
    fd.paint(Func(lambda P: base.eval(P, margin=0.08) - F(0.022), (-1, -1, 0.5), (1, 1, 2.0)), WSUEDE)
    f, up, side = wolf_frame()
    R = np.stack([side, -f, up], axis=1)
    L = wolf_L
    s = WS
    fd.add(Ellipsoid(L(0, 0.02, 0), v3((0.11, 0.12, 0.072)) * s, R=R, disp=fur, disp_amp=0.01), 0.04, WFUR)              # cranium
    fd.add(Ellipsoid(L(0, 0.15, -0.04), v3((0.12, 0.13, 0.06)) * s, R=R, disp=fur, disp_amp=0.01), 0.05, WFUR)           # neck hide
    for sx in (-1, 1):
        fd.add(Sphere(L(sx * 0.05, -0.075, 0.035), 0.036 * s), 0.03 * s, WFUR)                                      # brow ridges
        fd.add(Sphere(L(sx * 0.082, -0.02, -0.025), 0.05 * s), 0.04 * s, WFUR)                                      # cheeks
    fd.add(RoundCone(L(0, -0.085, -0.005), L(0, -0.29, -0.04), 0.058 * s, 0.024 * s), 0.035 * s, WMUZZLE)          # snout, tapering
    fd.add(RoundCone(L(0, -0.08, 0.032), L(0, -0.27, -0.016), 0.03 * s, 0.017 * s), 0.025 * s, WFUR)               # bridge
    for sx in (-1, 1):
        fd.add(Ellipsoid(L(sx * 0.028, -0.2, -0.058), v3((0.024, 0.085, 0.022)) * s, R=R), 0.02 * s, WMUZZLE)       # upper lips
        es = L(sx * 0.056, -0.1, 0.022)
        er = R @ euler(0, 0, sx * 0.45)
        fd.sub(Ellipsoid(es, v3((0.024, 0.014, 0.011)) * s, R=er), 0.005)                                        # eye holes
        fd.paint(Ellipsoid(es, v3((0.03, 0.019, 0.016)) * s, R=er), WSOCKET)
        # tall pointed ears, up and back, hollow facing forward
        eb = L(sx * 0.062, 0.03, 0.055)
        ed = norm(up * 1.0 - f * 0.4 + side * sx * 0.3)
        en = norm(f * 1.0 + side * sx * 0.45)
        ear = Inter(RoundCone(eb, eb + ed * 0.115 * s, 0.05 * s, 0.004), Func(lambda P, eb=eb, en=en: np.abs((P - eb.astype(F)) @ en.astype(F)) - F(0.015 * s),
                                                                              eb - 0.3, eb + 0.3), 0.006)
        fd.add(ear, 0.02 * s, WFUR)
        hol = RoundCone(eb + en * 0.03 * s + ed * 0.012, eb + en * 0.03 * s + ed * 0.1 * s, 0.028 * s, 0.003)
        fd.sub(hol, 0.004)
        fd.paint(RoundCone(eb + en * 0.022 * s + ed * 0.01, eb + en * 0.022 * s + ed * 0.1 * s, 0.036 * s, 0.006), WINNER)
        for j, dz in enumerate((0.0, -0.035, -0.07)):       # cheek ruff
            a = L(sx * 0.11, -0.03, dz)
            pts = [a, a + (side * sx * 0.03 - f * 0.05 + up * -0.01) * s, a + (side * sx * 0.05 - f * 0.11 + up * -0.03) * s]
            nrm = norm(side * sx * 1.0 + f * 0.3)
            fd.add(Lock(pts, [0.03 * s, 0.024 * s, 0.004], [0.011 * s, 0.009 * s, 0.003], [nrm] * 3, k=0.006), 0.012, WFUR)
    nose = L(0, -0.29, -0.014)                                  # black nose on the tip, tilted up
    fd.add(Ellipsoid(nose, v3((0.026, 0.026, 0.019)) * s, R=R @ euler(-0.35, 0, 0)), 0.01, WNOSE)
    for sx in (-1, 1):
        fd.sub(Ellipsoid(L(sx * 0.011, -0.315, -0.017), v3((0.006, 0.004, 0.004)) * s, R=R @ euler(0, 0, sx * 0.5)), 0.002)
        fd.paint(Chain([L(sx * 0.01, -0.285, -0.065), L(sx * 0.036, -0.22, -0.076), L(sx * 0.054, -0.14, -0.072)], [0.007, 0.008, 0.006], k=0.004), WNOSE)
    sh, el = J["shoulder_L"], J["elbow_L"]
    arm_hull = Field("ArmHull")
    arm_hull.add(deltoid("L"), 0.0)
    arm_hull.add(RoundCone(sh, el, 0.14, 0.105), 0.05)
    arm_hull.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.035, 0)), (0.132, 0.136, 0.18), R=rot_from_axes(z_axis=el - sh)), 0.04)
    for yo in (-1, 1):
        path = [L(0.0, 0.05, -0.07), lerp(sh, el, 0.12) + v3((0.05, yo * 0.16, 0.06)), lerp(sh, el, 0.38) + v3((0.04, yo * 0.15, 0.0)),
                lerp(sh, el, 0.6) + v3((0.03, yo * 0.14, -0.02))]
        pts, ns = [], []
        for p in path:
            q = project_to(arm_hull, [p], iters=4)[0]
            n = grad(arm_hull, [q])[0].astype(np.float64)
            pts.append(q + n * 0.034)
            ns.append(n)
        fd.add(Lock(pts, [0.048, 0.042, 0.038, 0.035], [0.03, 0.029, 0.027, 0.026], ns, k=0.015, disp=fur, disp_amp=0.008), 0.015, WFUR)
        ax = norm(pts[-1] - pts[-2])
        pw = pts[-1] + ax * 0.03
        fd.add(Ellipsoid(pw, (0.042, 0.036, 0.044), disp=fur, disp_amp=0.006), 0.02, WFUR)
        tside = norm(np.cross(ax, ns[-1]))
        for j in range(3):
            u = j - 1
            fd.add(Sphere(pw + ax * 0.034 + tside * u * 0.022 + ns[-1] * 0.008, 0.017), 0.01, WFUR)
    t0 = v3((-0.27, 0.2, 0.9))
    tp = [t0, t0 + v3((-0.04, 0.07, -0.12)), t0 + v3((-0.06, 0.08, -0.28)), t0 + v3((-0.05, 0.05, -0.42))]
    fd.add(Chain(tp, [0.05, 0.065, 0.055, 0.02], k=0.03, disp=fur, disp_amp=0.012), 0.03, WFUR)
    return fd


def fangs_field():
    """The wolf's fangs and incisors."""
    fd = Field("Fangs")
    f, up, side = wolf_frame()
    L = wolf_L
    s = WS
    for sx in (-1, 1):
        a = L(sx * 0.034, -0.27, -0.066)
        fd.add(RoundCone(a, a - up * 0.05 * s - f * 0.006, 0.0095 * s, 0.002), 0.0)
        b = L(sx * 0.044, -0.18, -0.072)
        fd.add(RoundCone(b, b - up * 0.024 * s, 0.006 * s, 0.0015), 0.0)
    for i in range(4):
        u = (i - 1.5) / 1.5
        a = L(u * 0.018, -0.298 + 0.006 * u * u, -0.066)
        fd.add(RoundCone(a, a - up * 0.015 * s, 0.0048 * s, 0.0015), 0.0)
    return fd


# ======================================================================================= clothing
def kilt_base():
    b = Field("KiltBase")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    b.add(RoundCone((0, 0.03, 0.92), (0, 0.035, 0.5), 0.3, 0.38), 0.08)
    return b


BELT_Z = 0.92


def leather_field():
    """Hide kilt (ragged hem, split on the left), shin wraps, the right wrist wrap and the club's grip wrap."""
    fd = Field("Leather")
    base = kilt_base()
    hide = lambda P: F(0.004) * NOISE(P * F(14)) + F(0.002) * NOISE(P * F(40))
    def keep(P):
        hem = F(0.5) + F(0.03) * np.abs(np.sin(np.arctan2(P[:, 0], -(P[:, 1] - F(0.035))) * F(5.5))) + F(0.014) * NOISE(P * F(9)) - P[:, 2]
        top = P[:, 2] - F(BELT_Z + 0.03)
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        split = F(0.12) - np.abs(a - F(1.45)) * F(0.6)                       # an open slit on his left side
        split = np.where(P[:, 2] < F(0.74), split, F(-1))
        return np.maximum(np.maximum(hem, top), split)
    fd.add(Inter(Shell(base, 0.018, 0.026, pad=0.08, disp=hide, disp_amp=0.006), Func(keep, (-1, -1, 0.3), (1, 1, 1.2)), 0.006), 0.0)
    for side in ("R", "L"):
        kn, an = J["knee_" + side], J["ankle_" + side]
        calf = RoundCone(kn, an, 0.108, 0.072)
        ax = norm(an - kn)
        for j, (t0, tilt) in enumerate(((0.55, 0.35), (0.66, -0.35), (0.77, 0.35))):
            c = lerp(kn, an, t0)
            nrm = norm(ax + v3((tilt, 0.0, 0.0)) * 0.5)
            fd.add(Inter(Shell(calf, 0.012, 0.014, pad=0.06),
                         Func(lambda P, c=c, nrm=nrm: np.abs((P - c.astype(F)) @ nrm.astype(F)) - F(0.022), c - 0.25, c + 0.25), 0.003), 0.004)
    el, wr = J["elbow_R"], J["wrist_R"]
    ax = norm(wr - el)
    c = lerp(el, wr, 0.82)
    fd.add(Inter(Shell(RoundCone(el, wr, 0.105, 0.08), 0.013, 0.018, pad=0.06),
                 Func(lambda P: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.05), c - 0.25, c + 0.25), 0.004), 0.0)
    a0, ax2 = club_axis()
    for i in range(5):
        p0 = a0 + ax2 * (-0.03 + 0.05 * i)
        fd.add(Torus(p0, 0.047, 0.012, R=rot_from_axes(z_axis=norm(ax2 + v3((0.25, 0, 0))))), 0.004)
    return fd


def rope_field():
    """Thick rope belt with a knot and hanging ends, lashings round the club head."""
    fd = Field("Rope")
    base = kilt_base()
    belt = Inter(Shell(base, 0.05, 0.034, pad=0.1), Func(lambda P: np.abs(P[:, 2] - (F(BELT_Z) + F(0.05) * P[:, 1])) - F(0.019), (-1, -1, 0.6), (1, 1, 1.2)), 0.006)
    fd.add(belt, 0.0)
    kp, _ = ray_hit(Func(lambda P: base.eval(P) - F(0.065), (-1, -1, 0.5), (1, 1, 1.3)), [v3((0.15, -0.8, BELT_Z - 0.02))], [v3((0, 1, 0))], tmax=0.8)
    k0 = kp[0] + v3((0, -0.012, 0))
    fd.add(Ellipsoid(k0, (0.038, 0.028, 0.034)), 0.008)
    fd.add(Chain([k0, k0 + v3((-0.012, -0.02, -0.09)), k0 + v3((-0.025, -0.02, -0.19))], [0.016, 0.015, 0.012], k=0.01), 0.008)
    fd.add(Chain([k0, k0 + v3((0.02, -0.02, -0.07)), k0 + v3((0.035, -0.012, -0.15))], [0.016, 0.015, 0.012], k=0.01), 0.008)
    # lashings that bind the flint into the club head
    a0, ax = club_axis()
    for s in (0.5, 0.73, 0.98):
        fd.add(Torus(a0 + ax * s, club_radius(s) + 0.008, 0.012, R=rot_from_axes(z_axis=ax)), 0.004)
    return fd


def bone_field():
    """Bone cuff on the left wrist, the club's bone spikes, the bead on the beard braid."""
    fd = Field("Bone")
    el, wr = J["elbow_L"], J["wrist_L"]
    ax = norm(wr - el)
    c = lerp(el, wr, 0.8)
    fore = RoundCone(el, wr, 0.105, 0.08)
    fd.add(Inter(Shell(fore, 0.016, 0.024, pad=0.06), Func(lambda P: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.045), c - 0.25, c + 0.25), 0.006), 0.0)
    for j in (-1, 1):
        cc = c + ax * (j * 0.03)
        fd.add(Inter(Shell(fore, 0.03, 0.008, pad=0.06), Func(lambda P, cc=cc: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.007), cc - 0.2, cc + 0.2), 0.002), 0.003)
    # bone spikes in the club head, between the flint rings
    a0, ax2 = club_axis()
    for s, ang in ((0.74, 70.0), (0.58, 250.0)):
        d = club_dir_at(ang)
        p = a0 + ax2 * s
        r = club_radius(s)
        fd.add(RoundCone(p + d * (r - 0.02), p + d * (r + 0.11) + ax2 * 0.035, 0.024, 0.004), 0.004)
    # bead at the end of the braid
    fd.add(Cylinder(BEAD_C, hr(0.026), hr(0.042), rr=hr(0.008)), 0.0)
    fd.sub(Torus(BEAD_C, hr(0.027), hr(0.004)), 0.001)
    return fd


# ======================================================================================= the club
CLUB_LEN = 0.98


def club_axis():
    """Grip centre and club direction in the rest pose: the handle runs through the right fist, head toward the thumb."""
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t


def club_radius(s):
    """Radius along the club (s = distance from the grip centre): handle, then a long swell into the head."""
    if s < 0.22:
        return 0.044
    u = min(1.0, (s - 0.22) / 0.68)
    return 0.044 + 0.118 * (u ** 1.1)


def club_side_dirs():
    a0, ax = club_axis()
    u = norm(np.cross(ax, v3((0, 0, 1))))
    w = np.cross(ax, u)
    return [norm(u * math.cos(a) + w * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]


def club_field():
    """A gnarled log club: leather-wrapped handle with a knob, swelling into a long heavy head with a blunt, rounded
    end; bark, knots and a snapped-off branch."""
    fd = Field("Club")
    a0, ax = club_axis()
    bark = lambda P: (F(0.006) * NOISE(P * np.array([40, 40, 40], F)) + F(0.004) * NOISE(P * F(110)))
    ss = np.linspace(-0.1, CLUB_LEN - 0.08, 15)
    pts = [a0 + ax * s for s in ss]
    rads = [club_radius(s) for s in ss]
    rads[0] = 0.05
    fd.add(Chain(pts, rads, k=0.02, disp=bark, disp_amp=0.008), 0.0)
    fd.add(Sphere(a0 + ax * -0.12, 0.056), 0.02)                                      # pommel knob
    end = a0 + ax * (CLUB_LEN - 0.08)
    fd.add(Ellipsoid(end, (0.158, 0.158, 0.075), R=rot_from_axes(z_axis=ax), disp=bark, disp_amp=0.008), 0.05)   # blunt end
    sd = club_side_dirs()
    for s, d, r in ((0.55, sd[1], 0.032), (0.78, sd[5], 0.036), (0.4, sd[6], 0.024)):   # knots
        p = a0 + ax * s + d * club_radius(s) * 0.9
        fd.add(Sphere(p, r), 0.02)
    p = a0 + ax * 0.66 + sd[7] * club_radius(0.66) * 0.8                             # snapped-off branch
    fd.add(RoundCone(p, p + sd[7] * 0.08 + ax * 0.05, 0.03, 0.026), 0.015)
    fd.sub(Ellipsoid(p + sd[7] * 0.085 + ax * 0.055, (0.03, 0.03, 0.012), R=rot_from_axes(z_axis=norm(sd[7] + ax * 0.6))), 0.004)
    return fd


def flint_field():
    """Big flint shards hafted into the club head, edges out, in three staggered rings."""
    fd = Field("Flint")
    a0, ax = club_axis()
    u = norm(np.cross(ax, v3((0, 0, 1))))
    w = np.cross(ax, u)
    k = 0
    for ring, (s, a_off) in enumerate(((0.5, 0.0), (0.66, 0.5), (0.82, 0.05))):
        for i in range(4):
            a = a_off + i * math.pi / 2 + 0.15 * ring
            d = norm(u * math.cos(a) + w * math.sin(a))
            if ring == 1 and i == 3:
                continue                                       # the branch stub sits here
            r = club_radius(s)
            c = a0 + ax * s + d * (r + 0.04)
            R = rot_from_axes(z_axis=norm(d + ax * 0.2), y_axis=np.cross(d, ax))
            fd.add(Stone(c, 0.085, seed=200 + k, cuts=7, squash=(0.6, 0.17, 1.0), soft=0.05, depth=(0.6, 0.86), R=R, noise=0.02), 0.0)
            k += 1
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.248, 1.6)), 0.08, 0.95)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.105, -0.15, 1.6)), 0.07, 0.5), (hp((sx * 0.19, 0.04, 1.655)), 0.07, 0.7),
                (J["elbow_" + sd] + v3((0, 0.035, 0)), 0.09, 0.35),
                (J["knee_" + sd] + v3((0, -0.04, 0)), 0.1, 0.4),
                (J["shoulder_" + sd] + v3((0, 0, 0.13)), 0.15, 0.3)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.045, 0.015, -0.015, -0.045):
            pts.append((wr + f * 0.144 * HAND_S + t * o * HAND_S - n * 0.014, 0.04, 0.55))
        an = J["ankle_" + side]
        pts.append((an + v3((0, -0.19, -0.07)), 0.075, 0.5))
        pts.append((an + v3((0, 0.05, -0.07)), 0.065, 0.3))
    return pts


WS = 1.22                                 # wolf head scale


def wolf_L(x, y, z):
    """Point on the wolf's head: x across, y back (negative = toward the nose), z up; scaled by WS."""
    f, up, side = wolf_frame()
    return WOLF_C + (side * x - f * y + up * z) * WS


def club_dir_at(angle_deg):
    a0, ax = club_axis()
    u = norm(np.cross(ax, v3((0, 0, 1))))
    w = np.cross(ax, u)
    a = math.radians(angle_deg)
    return norm(u * math.cos(a) + w * math.sin(a))


# ======================================================================================= build config
GLB_NAME = "club_warrior"
ROOT_NAME = "ClubWarriorHQ"
TEX_PREFIX = "warrior"
MAT_NAME = "WarriorMat"
MESH_NAME = "Warrior"
BASE_MODULE = "club_base"
ANIM_MODULE = "anim_club"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Wolf", "Fangs", "Leather", "Rope", "Bone", "Club", "Flint"]
REGION_PARTS = ("Skin", "Wolf")
RED_HAIR = {"name": "HQ_RedHair", "base": (0.62, 0.22, 0.08), "hi": (0.95, 0.5, 0.2)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_WarriorSkin", "base": (0.8, 0.55, 0.4), "ruddy": (0.84, 0.44, 0.33),
                      "brow": ((0.42, 0.13, 0.05), (0.78, 0.36, 0.13)), "paint": (0.12, 0.32, 0.72),
                      "extra": ((6, (0.86, 0.62, 0.52), 0.5),)}),
    "Hair": ("hair", RED_HAIR), "Beard": ("hair", RED_HAIR),
    "Leather": ("leather", {"name": "HQ_WarriorHide", "base": (0.46, 0.29, 0.16)}),
    "Rope": ("cord", {}), "Fangs": ("fang", {"name": "HQ_WolfFang"}),
}
LOW_TARGETS = {"Skin": 7200, "Hair": 2400, "Beard": 1700, "Wolf": 2800, "Fangs": 220, "Leather": 1400, "Rope": 700, "Bone": 700,
               "Teeth": 420, "Club": 1100, "Flint": 520}
AO_EXCLUDE = ["Bone", "Rope", "Club", "Flint", "Fangs"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.74, 0.92, 1.12, 1.6)


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.95), (0, 0.05, 1.2)),
        "chest": ((0, 0.05, 1.2), (0, 0.08, 1.47)),
        "neck": ((0, 0.08, 1.47), hp((0, 0.02, 1.56))),
        "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.45,
    }


def prop_bones():
    return []                     # the club is rigid in his right fist (weighted to hand.R)


def wolf_weights(ob, skin_ob, arm):
    """Head and forelegs with his left shoulder/arm; the sash with the torso; the tail with the hips."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.L", "upperarm.L", "clavicle.R", "thigh.R", "thigh.L"},
                         caps={"upperarm.L": 0.6, "clavicle.R": 0.3, "thigh.R": 0.2, "thigh.L": 0.2})
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.x > 0.3 and p.z > 1.5:                                  # the wolf's head
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"clavicle.L": 0.55, "upperarm.L": 0.25, "chest": 0.2})
        elif p.z < 0.95:                                             # the tail and the hide's end at his hip
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            t = max(0.0, min(1.0, (0.9 - p.z) / 0.4))
            _blend_add(ob, groups, v.index, {"root": 1.0 - 0.25 * t, "thigh.R": 0.25 * t})


def fangs_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"clavicle.L": 0.55, "upperarm.L": 0.25, "chest": 0.2})


def _near_club(p, pad=0.05):
    a0, ax = club_axis()
    q = np.array(p) - a0
    s = q @ ax
    r = np.linalg.norm(q - ax * s)
    return -0.2 < s < CLUB_LEN + 0.15 and r < club_radius(max(s, 0)) + pad


def leather_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L", "forearm.R", "hand.R"},
                         caps={"thigh.R": 0.4, "thigh.L": 0.4})
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if _near_club(p, 0.03):
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"hand.R": 1.0})
        elif p.z > 1.75:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"head": 1.0})


def rope_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"thigh.R", "thigh.L"}, caps={"thigh.R": 0.3, "thigh.L": 0.3})
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if _near_club(p, 0.06):
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"hand.R": 1.0})


def bone_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if _near_club(p, 0.15):
            w = {"hand.R": 1.0}
        elif p.x > 0.75:
            w = {"forearm.L": 1.0}
        elif np.linalg.norm(np.array(p) - BEAD_C) < 0.06:
            w = {"head": 1.0}
        else:
            w = {"chest": 1.0}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Hair": ("rigid", "head"), "Beard": ("rigid", "head"), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Wolf": ("custom", wolf_weights), "Fangs": ("custom", fangs_weights),
        "Leather": ("custom", leather_weights), "Rope": ("custom", rope_weights), "Bone": ("custom", bone_weights),
        "Club": ("rigid", "hand.R"), "Flint": ("rigid", "hand.R"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Fangs",):
        return 1.6
    if part in ("Bone", "Flint"):
        return 1.1
    if part in ("Rope",):
        return 0.7
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Wolf" and c.x > 0.3 and c.z > 1.5:
        return 1.5
    if part == "Skin" and (abs(c.x) > 0.85 and c.z < 1.05):
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.0032 if fine else 0.005),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0028 if fine else 0.0035),
        ("Beard", beard_field(), 0.0028 if fine else 0.0035),
        ("Wolf", wolf_field(), 0.003 if fine else 0.0045),
        ("Fangs", fangs_field(), 0.001 if fine else 0.0015),
        ("Leather", leather_field(), 0.0025 if fine else 0.0032),
        ("Rope", rope_field(), 0.002 if fine else 0.0028),
        ("Bone", bone_field(), 0.0015 if fine else 0.002),
        ("Club", club_field(), 0.003 if fine else 0.004),
        ("Flint", flint_field(), 0.0015 if fine else 0.002),
    ]
