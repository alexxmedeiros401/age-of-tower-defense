"""The Boulder Catapult (HQ tower): a lashed-log counterweight catapult on a sled, and the strong young woman who works
it from the platform at the back. Rest pose: she stands in an A-pose facing -Y (the way the catapult shoots), feet on the
platform at z = 0; the machine is cocked (throwing arm down at the back, a boulder in its bucket).

Her: sturdy and broad-shouldered, a round freckled face with thick brows, a determined smile, dark hair swept back into a
high ponytail, a leather headband; a one-shoulder deer-hide dress with a fur trim, a belt with a pouch, leather bracers, a river-
stone pendant and hide foot wraps.

The machine: two log runners and crossbars, a plank platform at the back, two A-frames carrying the axle, a long throwing
arm with a hide-lined bucket at its long end and a rope net of stones hanging from its short end, a padded stop bar on
two posts at the front, a windlass with spokes that winds the arm back down (its rope tied to the arm), a trigger lever
by her right hand and a basket of boulders on the platform."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, grad, project_to, flow_line, Stone, lerp
from ugo import stripe2d, bez3, _blend_add

J = {
    "root": (0.0, 0.03, 0.74),
    "spine": (0.0, 0.03, 0.9),
    "chest": (0.0, 0.05, 1.1),
    "neck": (0.0, 0.06, 1.31),
    "head": (0.0, 0.02, 1.42),
    "head_end": (0.0, -0.02, 1.8),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.3, 0.06, 1.29)
    J["elbow_" + _s] = (_x * 0.5, 0.09, 1.05)
    J["wrist_" + _s] = (_x * 0.65, 0.03, 0.83)
    J["hip_" + _s] = (_x * 0.15, 0.04, 0.7)
    J["knee_" + _s] = (_x * 0.17, 0.0, 0.39)
    J["ankle_" + _s] = (_x * 0.18, 0.06, 0.1)
    J["toe_" + _s] = (_x * 0.2, -0.15, 0.03)
J = {k: v3(v) for k, v in J.items()}

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, FRECKLE, LASH = 0, 1, 2, 3, 4, 5, 6, 8

# head: designed in the Rock Slinger's head coordinates, lowered onto her neck and scaled about its top
HS = 1.05
DZ = -0.12
HPIV = v3((0.0, 0.02, 1.4))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.178, 0.188, 0.182)) * HS
EYE_R = hr(0.041)


def eye_c(sx):
    return hp((sx * 0.072, -0.148, 1.672))


def hstripe(a, b, ra, rb, y0=-0.4, y1=0.02):
    m = lambda q: (q[0] * HS, HPIV[2] + (q[1] + DZ - HPIV[2]) * HS)
    return stripe2d(m(a), m(b), ra * HS, rb * HS, y0=y0, y1=y1)


# ======================================================================================= the machine (layout)
MX, MY = -0.55, -1.1          # machine reference: the axle sits above (MX, MY + 0.02)
GROUND_Z = -0.2               # the ground under the sled (her platform is at z = 0)
AXLE = v3((MX, MY + 0.02, 0.8))
COCK = math.radians(-32.0)    # arm angle (long end, from horizontal-back) when cocked
FIRED = math.radians(102.0)   # ... when it rests on the stop bar
LONG, SHORT = 1.15, 0.42
DRUM = v3((MX + 0.03, MY + 0.72, 0.38))
LEVER_P = v3((MX + 0.15, MY + 0.86, 0.0))      # on the crossbar in front of the platform, by her right hand
LEVER_T = v3((MX + 0.14, MY + 0.8, 0.86))
BASKET = v3((0.4, 0.08, 0.0))
YAW_PIVOT = (MX + 0.25, MY + 0.5, 0.0)       # the tower turns about this point (keeps the whole sled on the base)
HAUL_AT = 0.55                               # where the windlass rope is tied on the arm (along the long end)
PLAT_X0, PLAT_X1 = MX - 0.36, 0.6            # the platform's ends


def arm_dir(a):
    """Unit vector along the long end of the arm at angle a (0 = horizontal toward the back, + = up)."""
    return v3((0.0, math.cos(a), math.sin(a)))


def arm_up(a):
    """The arm's 'up' side (where the bucket opens)."""
    return v3((0.0, -math.sin(a), math.cos(a)))


def bucket_c(a=COCK):
    return AXLE + arm_dir(a) * (LONG - 0.07) + arm_up(a) * 0.12


def short_tip(a=COCK):
    return AXLE - arm_dir(a) * SHORT


def haul_point(a=COCK):
    return AXLE + arm_dir(a) * (LONG * HAUL_AT) - arm_up(a) * 0.05


SPOKE_X = MX + 0.42


def spoke_end(phi, k):
    """End of spoke k of the windlass turned by phi."""
    a = phi + k * math.pi / 2
    return DRUM + v3((SPOKE_X - DRUM[0], 0.0, 0.0)) + v3((0.0, math.cos(a), math.sin(a))) * 0.17


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


HAND_S = 0.96


def hand(fd, side, fist, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.076 * s
    fd.add(RoundBox(c, v3((0.062, 0.032, 0.064)) * s, 0.029 * s, R=Rp), 0.028, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.034, 0.029, 0.05)) * s, R=Rp), 0.019, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = (1.45, 1.6, 1.2) if fist else (0.35, 0.55, 0.4)
    offs = (0.043, 0.0145, -0.0145, -0.043)
    lens = (0.95, 1.0, 0.95, 0.8)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.021 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.05 * ls * s, 0.04 * ls * s, 0.033 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.011, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.015 * s), 0.01, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.011, (0.012, 0.007, 0.014), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.05 * s + n * 0.011
    if fist:
        d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
        d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:
        d1 = norm(f * 0.55 + t * 0.75 + n * 0.25)
        d2 = norm(f * 0.8 + t * 0.35 + n * 0.45)
    p1 = tb + d1 * 0.049 * s
    p2 = p1 + d2 * 0.042 * s
    fd.add(Chain([tb, p1, p2], [0.025 * s, 0.022 * s, 0.019 * s], k=0.008), 0.018, SKIN)


def foot(fd, side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.12)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    fd.add(Sphere(an + v3((0, 0.04, -0.05)), 0.058), 0.028, SKIN)
    fd.add(RoundBox(an + fwd * 0.07 + v3((0, 0, -0.068)), (0.066, 0.112, 0.036), 0.033, R=Rz), 0.032, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.035 + v3((0, 0, -0.03)), (0.064, 0.082, 0.048), R=Rz), 0.028, SKIN)
    inner = -sx
    toes = [(0.05, 0.028), (0.02, 0.021), (-0.005, 0.019), (-0.028, 0.017), (-0.047, 0.016)]
    for i, (o, r) in enumerate(toes):
        base = an + fwd * (0.158 - 0.011 * i - (0.0 if i else -0.004)) + rgt * (o * inner) + v3((0, 0, -0.08))
        tip = base + fwd * (0.028 + r * 0.4) + v3((0, 0, -0.004))
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
    fd.add(E((0, -0.06, 1.592), (0.152, 0.135, 0.128)), 0.07, SKIN)                          # round jaw
    fd.add(E((0, -0.125, 1.51), (0.078, 0.064, 0.06)), 0.05, SKIN)                           # small chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.104, -0.118, 1.604), 0.052), 0.05, SKIN)                              # round cheeks
        fd.add(S((sx * 0.124, -0.05, 1.566), 0.052), 0.05, SKIN)
        pts = [hp((sx * 0.15, -0.06, 1.744)), hp((sx * 0.115, -0.128, 1.75)), hp((sx * 0.062, -0.162, 1.748))]
        fd.add(Chain(pts, [hr(0.01), hr(0.014), hr(0.012)], k=hr(0.02)), hr(0.03), SKIN)       # orbit rim, no glabella bulge
    # thick dark brows with a confident arch (mostly paint, a little raised)
    for sx in (-1, 1):
        pts = [hp((sx * 0.03, -0.198, 1.765)), hp((sx * 0.068, -0.19, 1.779)), hp((sx * 0.108, -0.168, 1.784)), hp((sx * 0.145, -0.134, 1.774))]
        fd.add(Chain([p + v3((0, 0.007, 0)) for p in pts], [hr(0.007), hr(0.008), hr(0.007), hr(0.003)], k=hr(0.006)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.019), hr(0.021), hr(0.018), hr(0.009)], k=hr(0.01)), BROW)
    # big open eyes, lashes on the upper lids
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, hr(0.031))), (sx * 0.18, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0045)), Plane(ec + v3((0, 0, -hr(0.03))), (sx * -0.1, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.008)), Plane(ec + v3((0, 0, hr(0.027))), (sx * 0.18, 0.05, -1.0)), hr(0.002)), LASH)
        flick = ec + v3((sx * hr(0.045), -hr(0.012), hr(0.02)))
        fd.add(RoundCone(flick, flick + v3((sx * hr(0.018), hr(0.006), hr(0.008))), hr(0.005), hr(0.0015)), hr(0.004), LASH)
    # small upturned nose
    fd.add(RoundCone(hp((0, -0.178, 1.72)), hp((0, -0.222, 1.646)), hr(0.014), hr(0.02)), hr(0.016), SKIN)
    fd.add(S((0, -0.226, 1.628), 0.026), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.027, -0.205, 1.613), 0.018), hr(0.011), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.014, -0.221, 1.6)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a determined half-smile: her left corner (+x) up, a dimple
    slot = [hp((-0.06, -0.164, 1.556)), hp((-0.032, -0.189, 1.542)), hp((0, -0.196, 1.539)), hp((0.034, -0.188, 1.544)), hp((0.064, -0.16, 1.566))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0035), hr(0.004), hr(0.0035), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0035), hr(0.005), hr(0.0055), hr(0.005), hr(0.0035)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.058, -0.161, 1.558), (-0.03, -0.181, 1.551), (-0.008, -0.186, 1.554), (0.008, -0.186, 1.555), (0.032, -0.18, 1.557), (0.062, -0.157, 1.569)]
    lo_lip = [(-0.05, -0.163, 1.543), (-0.027, -0.181, 1.531), (0, -0.185, 1.528), (0.029, -0.18, 1.533), (0.054, -0.161, 1.552)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.004), hr(0.0075), hr(0.008), hr(0.008), hr(0.0075), hr(0.004)], k=hr(0.006)), hr(0.009), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.009), hr(0.01), hr(0.009), hr(0.005)], k=hr(0.007)), hr(0.009), LIP)
    fd.sub(S((0.072, -0.156, 1.571), 0.006), hr(0.006))                                     # dimple at the smile
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.66)), v3((0.026, 0.045, 0.058)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.198, 0.024, 1.664)), v3((0.012, 0.03, 0.038)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
    # freckles across her nose and cheeks
    rs = np.random.RandomState(8)
    for i in range(26):
        x = rs.uniform(-0.13, 0.13)
        z = 1.625 + rs.uniform(-0.03, 0.035) - 0.15 * x * x
        if abs(x) < 0.025 and z < 1.63:
            continue
        r = rs.uniform(0.0035, 0.0055)
        fd.paint(hstripe((x, z), (x + 0.001, z), r, r, y0=-0.5, y1=-0.08), FRECKLE)


# ======================================================================================= body
def torso_prims():
    return [
        (Ellipsoid((0, 0.04, 1.1), (0.22, 0.17, 0.22), R=euler(-0.1, 0, 0)), 0.0),                # ribcage
        (Ellipsoid((0, 0.1, 1.15), (0.25, 0.12, 0.17)), 0.05),                                     # back
        (Ellipsoid((0.08, -0.11, 1.13), (0.088, 0.065, 0.078), R=euler(0.3, 0, 0.2)), 0.04),        # bust
        (Ellipsoid((-0.08, -0.11, 1.13), (0.088, 0.065, 0.078), R=euler(0.3, 0, -0.2)), 0.04),
        (Ellipsoid((0, -0.0, 0.92), (0.18, 0.15, 0.15)), 0.07),                                     # waist
        (Ellipsoid((0, 0.04, 0.77), (0.245, 0.18, 0.15)), 0.07),                                    # hips
    ]


def traps():
    return Ellipsoid((0, 0.09, 1.3), (0.2, 0.11, 0.075), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.06, 1.27), hp((0, 0.02, 1.575)), 0.075, hr(0.08))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.02, -0.005, 0.012)), 0.098)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.05, SKIN)
    fd.add(neck_prim(), 0.045, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.05, SKIN)
        fd.add(RoundCone(sh, el, 0.084, 0.064), 0.045, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.02, 0)), (0.075, 0.078, 0.11), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(RoundCone(el, wr, 0.064, 0.048), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.08, 0.07, 0.12), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.05), 0.025, SKIN)
        hand(fd, side, fist=False)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.135, 0.085), 0.06, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.02, 0)), (0.125, 0.115, 0.17), R=rot_from_axes(z_axis=kn - hip)), 0.045, SKIN)
        fd.add(Sphere(kn + v3((0, -0.028, 0.0)), 0.068), 0.035, SKIN)
        fd.add(RoundCone(kn, an, 0.082, 0.054), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.028, 0)), (0.093, 0.09, 0.13), R=rot_from_axes(z_axis=an - kn)), 0.04, SKIN)
        foot(fd, side)
    head(fd)
    # three ochre dots under each eye: her crew's mark
    for sx in (-1, 1):
        for k in range(3):
            x = sx * (0.08 + 0.025 * k)
            fd.paint(hstripe((x, 1.596 - 0.006 * k), (x + 0.001, 1.596 - 0.006 * k), 0.0085, 0.0085, y0=-0.5, y1=-0.05), PAINT)


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
    """A hint of teeth would fight her closed smile: just two tiny incisors hidden behind the lips (keeps the part)."""
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009, -0.17, 1.54)), v3((0.008, 0.006, 0.009)) * HS, hr(0.003)), 0.0)
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


PONY = [hp(p) for p in ((0, 0.18, 1.86), (0, 0.245, 1.905), (0, 0.31, 1.875), (0, 0.345, 1.78), (0, 0.335, 1.645),
                          (0, 0.3, 1.51), (0, 0.255, 1.39))]
PONY_R = [hr(r) for r in (0.036, 0.046, 0.054, 0.054, 0.048, 0.036, 0.012)]
TIE_C = PONY[0] + norm(PONY[1] - PONY[0]) * 0.012


def _pony_at(t):
    """Point and tangent along the ponytail, t in 0..1 (piecewise linear through PONY)."""
    n = len(PONY) - 1
    seg = min(int(t * n), n - 1)
    u = t * n - seg
    return lerp(PONY[seg], PONY[seg + 1], u), norm(PONY[seg + 1] - PONY[seg]), PONY_R[seg] + (PONY_R[seg + 1] - PONY_R[seg]) * u


def hair_hull():
    hull = Field("HairHull")
    hull.add(Ellipsoid(HEAD_C, HEAD_RAD + 0.02), 0.0)
    hull.add(Ellipsoid(hp((0, 0.12, 1.69)), v3((0.18, 0.12, 0.17)) * HS), hr(0.07))
    return hull


def hair_field(seed=3):
    """Thick dark hair swept back from a clean hairline into a high ponytail tied with leather (Leather); two loose
    strands at her temples."""
    rng = np.random.RandomState(seed)
    fd = Field("Hair")
    hc, hrad = HEAD_C, HEAD_RAD
    pfront, pback = hp((0, -0.155, 1.805)), hp((0, 0.22, 1.585))
    slope = (pback[2] - pfront[2]) / (pback[1] - pfront[1])
    hl_n = norm((0, slope, -1.0))
    hairline = Func(lambda P: ((P - pfront.astype(F)) @ hl_n.astype(F)) + F(0.006) * NOISE(P * F(24)), hc - 0.5, hc + 0.5)
    fd.add(Inter(Ellipsoid(hc, hrad + 0.014), hairline, 0.02), 0.0)
    hull = hair_hull()
    target = PONY[0]
    # swept-back locks: from all round the hairline, over the skull to the tie
    n = 22
    for i in range(n):
        a = -math.pi * 0.95 + 2 * math.pi * 0.95 * (i + 0.5) / n                 # 0 = front (-Y)
        d = v3((math.sin(a), -math.cos(a), 0.0))
        o = hc + d * 0.5 + v3((0, 0, 0.0))
        # start just above the hairline, found by marching down the hairline plane
        lo_z = pfront[2] + (hc[1] + d[1] * hrad[1] - pfront[1]) * slope
        o = v3((hc[0] + d[0] * 0.5, hc[1] + d[1] * 0.5, lo_z + 0.062))
        st, ok = ray_hit(hull, [o], [-d], tmax=0.6)
        if not ok[0]:
            continue
        def flow(p, k):
            return norm(target - p)
        L = np.linalg.norm(target - st[0]) * 1.3
        segs = 9
        line = flow_line(hull, st[0], flow, segs, L / segs)
        for k, p in enumerate(line):
            if np.linalg.norm(p - target) < 0.04:
                line = line[:k + 1]
                break
        if len(line) < 4:
            continue
        pts, ws, ts, ns = [], [], [], []
        m = len(line) - 1
        w0 = hr(0.036) + rng.uniform(-0.004, 0.004)
        for k, p in enumerate(line):
            u = k / m
            nn = grad(hull, [p])[0].astype(np.float64)
            ramp = 0.35 + 0.65 * math.sin(min(1.0, u / 0.2) * math.pi / 2)      # roots melt into the cap
            pts.append(p + nn * hr(0.004) * ramp)
            ws.append(w0 * (1.0 - 0.5 * u) * (0.6 + 0.4 * ramp))
            ts.append(hr(0.014) * (1.0 - 0.3 * u) * ramp)
            ns.append(nn)
        fd.add(Lock(pts, ws, ts, ns, k=w0 * 0.3), hr(0.006))
        gp = [pts[k] + ns[k] * ts[k] * 1.0 for k in range(1, m) if 0.15 < k / m < 0.8]
        if len(gp) >= 2:
            fd.sub(Chain(gp, [hr(0.0035)] * len(gp), k=0.003), hr(0.003))
    # the ponytail: a core and six strands twisted a little round it
    ts_ = np.linspace(0, 1, 15)
    core = [_pony_at(t) for t in ts_]
    fd.add(Chain([c[0] for c in core], [c[2] * 0.8 for c in core], k=hr(0.01)), hr(0.012))
    side = v3((1, 0, 0))
    for j in range(6):
        pts, ws, th, ns = [], [], [], []
        for t in ts_:
            p, tg, r = _pony_at(t)
            upp = norm(np.cross(tg, side))
            ang = j * math.pi / 3 + 0.5 * t
            rd = side * math.cos(ang) + upp * math.sin(ang)
            pts.append(p + rd * r * 0.55)
            ws.append(max(hr(0.004), r * 0.62))
            th.append(max(hr(0.003), r * 0.36))
            ns.append(rd)
        fd.add(Lock(pts, ws, th, ns, k=hr(0.006)), hr(0.008))
    # tuft above the tie
    tg0 = norm(PONY[0] - PONY[1])
    fd.add(Ellipsoid(PONY[0] + tg0 * hr(0.012), v3((0.034, 0.03, 0.02)) * HS, R=rot_from_axes(z_axis=tg0)), hr(0.01))
    return fd


# ======================================================================================= clothing
def dress_base():
    b = Field("DressBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(deltoid("L"), 0.05)
    b.add(RoundCone((0, 0.04, 0.86), (0, 0.04, 0.46), 0.25, 0.31), 0.08)          # skirt
    return b


def dress_field():
    """One-shoulder deer-hide dress to mid-thigh: over her left shoulder, under her right arm, a fringed hem."""
    fd = Field("Dress")
    base = dress_base()
    hide = lambda P: F(0.003) * NOISE(P * F(14)) + F(0.0015) * NOISE(P * F(40))
    fd.add(Shell(base, 0.016, 0.022, pad=0.1, disp=hide, disp_amp=0.005), 0.0)
    n1 = norm((-0.72, 0.0, 1.0))
    c1 = v3((0.0, 0.05, 1.24))
    fd.inter(Func(lambda P: (P - c1.astype(F)) @ n1.astype(F), (-3, -3, -3), (3, 3, 3)), 0.006)
    sh, el = J["shoulder_L"], J["elbow_L"]
    n2 = norm(el - sh)
    c2 = sh + (el - sh) * 0.22
    def sleeve(P, c2=c2, n2=n2, sh=sh):
        d = (P - c2.astype(F)) @ n2.astype(F)
        near = (P[:, 0] > F(sh[0] - 0.05)) & (P[:, 2] > F(sh[2] - 0.6))
        return np.where(near, d, F(-1.0))
    fd.inter(Func(sleeve, (-3, -3, -3), (3, 3, 3)), 0.006)
    def hem(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.04)))
        fr = F(0.02) * (np.abs(np.sin(a * F(30))) > F(0.5)).astype(F)        # fringe
        return F(0.5) + fr - P[:, 2]
    fd.inter(Func(hem, (-2, -2, -2), (2, 2, 5)), 0.004)
    return fd


def fur_field():
    """White fur trim along the dress's neckline and a fur band round its hem; fur cuffs on her foot wraps."""
    fd = Field("Fur")
    base = dress_base()
    fur = lambda P: F(0.005) * NOISE(P * np.array([30, 30, 12], F)) + F(0.002) * NOISE(P * F(70))
    n1 = norm((-0.72, 0.0, 1.0))
    c1 = v3((0.0, 0.05, 1.24))
    fd.add(Inter(Shell(base, 0.03, 0.03, pad=0.1, disp=fur, disp_amp=0.006),
                 Func(lambda P: np.abs((P - c1.astype(F)) @ n1.astype(F) + F(0.022)) - F(0.026), (-1, -1, 0.9), (1, 1, 1.5)), 0.006), 0.0)
    fd.add(Inter(Shell(base, 0.03, 0.03, pad=0.1, disp=fur, disp_amp=0.006),
                 Func(lambda P: np.abs(P[:, 2] - F(0.56)) - F(0.035), (-1, -1, 0.4), (1, 1, 0.7)), 0.006), 0.0)
    for side in ("R", "L"):
        an = J["ankle_" + side]
        fd.add(Torus(an + v3((0, 0.01, 0.07)), 0.066, 0.025, disp=fur, disp_amp=0.006), 0.0)
    return fd


BELT_Z = 0.84


def leather_field():
    """Belt and pouch, bracers, foot wraps, the ponytail wrap and the headband."""
    fd = Field("Leather")
    base = dress_base()
    fd.add(Inter(Shell(base, 0.04, 0.02, pad=0.1), Func(lambda P: np.abs(P[:, 2] - (F(BELT_Z) + F(0.05) * P[:, 1])) - F(0.022),
                                                       (-1, -1, 0.6), (1, 1, 1.1)), 0.004), 0.0)
    bp, _ = ray_hit(Func(lambda P: base.eval(P) - F(0.04), (-1, -1, 0.5), (1, 1, 1.3)), [v3((-0.6, -0.35, 0.74))], [norm(v3((0.85, 0.5, 0)))], tmax=0.9)
    out = norm(v3((-0.85, -0.5, 0)))
    bc = bp[0] + out * 0.04
    R = rot_from_axes(y_axis=out, z_axis=(0, 0, 1))
    fd.add(Ellipsoid(bc, (0.06, 0.04, 0.065), R=R, disp=lambda P: F(0.003) * NOISE(P * F(30)), disp_amp=0.004), 0.0)
    fd.add(Torus(bc + v3((0, 0, 0.04)), 0.05, 0.007, R=R), 0.005)
    fd.add(Chain([bc + v3((0, 0, 0.045)) - out * 0.015, bc + v3((0.0, 0, 0.09)) - out * 0.03], [0.009, 0.009]), 0.006)
    for side in ("R", "L"):                                             # bracers
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.68)
        fore = RoundCone(el, wr, 0.064, 0.048)
        fd.add(Inter(Shell(fore, 0.012, 0.016, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.07), c - 0.25, c + 0.25), 0.004), 0.0)
        for j in (-1, 0, 1):
            cc = c + ax * (j * 0.04)
            fd.add(Inter(Shell(fore, 0.02, 0.005, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.005), cc - 0.2, cc + 0.2), 0.002), 0.003)
        # foot wraps: hide shoes laced up the ankle
        an = J["ankle_" + side]
        sx = -1 if side == "R" else 1
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        shoe = Field("Shoe")
        shoe.add(Sphere(an + v3((0, 0.04, -0.05)), 0.058), 0.0)
        shoe.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.065)), (0.068, 0.13, 0.04), 0.036, R=Rz), 0.035)
        shoe.add(RoundCone(an + v3((0, 0.01, -0.02)), an + v3((0, 0.01, 0.06)), 0.058, 0.055), 0.02)
        fd.add(Inter(Shell(shoe, 0.008, 0.016, pad=0.05), Func(lambda P, an=an: P[:, 2] - F(an[2] + 0.06), an - 0.3, an + 0.3), 0.004), 0.0)
    tg = norm(PONY[1] - PONY[0])                                      # the ponytail's leather wrap
    for j in range(3):
        fd.add(Torus(TIE_C + tg * hr(0.012 * j), hr(0.04), hr(0.009), R=rot_from_axes(z_axis=tg)), 0.003)
    hb = Inter(Shell(Ellipsoid(HEAD_C, HEAD_RAD + 0.014), 0.009, 0.014, pad=0.06),
               Func(lambda P: np.abs((P - v3(HEAD_C).astype(F)) @ norm(v3((0, 0.45, 1.0))).astype(F) - F(0.02)) - F(0.016),
                    HEAD_C - 0.4, HEAD_C + 0.4), 0.004)
    fd.add(hb, 0.0)                                                     # headband
    return fd


def bone_field():
    """Her river-stone pendant on a cord (the stone is in Stones), a bone bangle on her left wrist, a pin in her headband."""
    fd = Field("Bone")
    el, wr = J["elbow_L"], J["wrist_L"]
    ax = norm(wr - el)
    c = lerp(el, wr, 0.9)
    fd.add(Torus(c, 0.06, 0.011, R=rot_from_axes(z_axis=ax)), 0.0)
    pin = HEAD_C + v3((0.12, -0.02, 0.15)) * HS
    fd.add(RoundCone(pin + v3((-0.03, -0.04, -0.01)), pin + v3((0.05, 0.06, 0.02)), 0.008, 0.005), 0.0)
    fd.add(Sphere(pin + v3((-0.03, -0.04, -0.01)), 0.013), 0.004)
    return fd


def pendant_points():
    hull = Field("NeckHull")
    for p, k in torso_prims():
        hull.add(p, k)
    hull.add(traps(), 0.05)
    hull.add(neck_prim(), 0.05)
    pts = []
    for i in range(24):
        a = 2 * math.pi * i / 24
        dirv = v3((math.sin(a) * 0.85, -math.cos(a), 0.0))
        front = max(0.0, -dirv[1])
        z = 1.39 - 0.12 * front ** 1.5
        o = v3((0, 0.07, z)) + norm(dirv) * 0.6
        h, ok = ray_hit(Func(lambda P: hull.eval(P) - F(0.03), (-1, -1, 0.8), (1, 1, 1.7)), [o], [-norm(dirv)], tmax=0.6)
        pts.append(h[0] + norm(dirv) * 0.006)
    return pts


# ======================================================================================= the machine (sculpt)
def log(fd, a, b, r0, r1=None, k=0.0, bark=True):
    r1 = r0 if r1 is None else r1
    d = (lambda P: F(0.003) * NOISE(P * np.array([40, 40, 40], F)) + F(0.0015) * NOISE(P * F(110))) if bark else None
    fd.add(RoundCone(a, b, r0, r1, disp=d, disp_amp=0.004 if bark else 0.0), k)


def frame_field():
    """Runners, crossbars, the platform, A-frames, axle, stop posts and bar, windlass posts."""
    fd = Field("Frame")
    gz = GROUND_Z
    for x in (MX - 0.34, MX + 0.34):                                                 # runners, tips curled up at the front
        log(fd, v3((x, MY + 1.38, gz + 0.065)), v3((x, MY - 0.55, gz + 0.065)), 0.065)
        log(fd, v3((x, MY - 0.55, gz + 0.065)), v3((x, MY - 0.7, gz + 0.14)), 0.065, 0.058, 0.02)
    log(fd, v3((PLAT_X1 - 0.07, MY + 0.82, gz + 0.06)), v3((PLAT_X1 - 0.07, MY + 1.38, gz + 0.06)), 0.055)  # runner under the side platform
    for y in (MY - 0.5, MY + 0.12, MY + 0.86):                                       # crossbars
        log(fd, v3((MX - 0.44, y, gz + 0.165)), v3((PLAT_X1 if y > MY + 0.5 else MX + 0.44, y, gz + 0.165)), 0.05)
    for i in range(4):                                                               # platform planks
        y = MY + 0.93 + i * 0.118
        fd.add(RoundBox(v3(((PLAT_X0 + PLAT_X1) / 2, y, -0.022)), ((PLAT_X1 - PLAT_X0) / 2, 0.054, 0.022), 0.012,
                        disp=lambda P: F(0.002) * NOISE(P * np.array([6, 60, 60], F)), disp_amp=0.003), 0.004)
    for x in (MX - 0.3, MX + 0.3):                                                   # A-frames
        apex = v3((x, AXLE[1], AXLE[2] + 0.04))
        log(fd, v3((x, MY - 0.42, gz + 0.17)), apex, 0.046, 0.042)
        log(fd, v3((x, MY + 0.46, gz + 0.17)), apex, 0.046, 0.042)
        log(fd, v3((x, MY - 0.3, gz + 0.45)), v3((x, MY + 0.34, gz + 0.45)), 0.032)   # brace
    log(fd, v3((MX - 0.42, AXLE[1], AXLE[2])), v3((MX + 0.42, AXLE[1], AXLE[2])), 0.042, k=0.01)           # axle
    for x in (MX - 0.42, MX + 0.42):
        fd.add(Sphere(v3((x, AXLE[1], AXLE[2])), 0.05), 0.01)
    for x in (MX - 0.31, MX + 0.31):                                                 # stop posts
        log(fd, v3((x, MY - 0.2, gz + 0.17)), v3((x, MY - 0.17, 1.36)), 0.04, 0.036)
        log(fd, v3((x, MY - 0.5, gz + 0.17)), v3((x, MY - 0.2, 0.6)), 0.028)          # struts
    log(fd, v3((MX - 0.37, MY - 0.17, 1.3)), v3((MX + 0.37, MY - 0.17, 1.3)), 0.04)  # stop bar
    for x in (MX - 0.27, MX + 0.27):                                                 # windlass posts
        log(fd, v3((x, DRUM[1], gz + 0.17)), v3((x, DRUM[1], DRUM[2] + 0.06)), 0.038)
    return fd


def winch_field():
    """The windlass drum with four spokes at its end (turns with the 'winch' bone)."""
    fd = Field("Winch")
    log(fd, v3((MX - 0.3, DRUM[1], DRUM[2])), v3((SPOKE_X - 0.02, DRUM[1], DRUM[2])), 0.058, k=0.0)
    for k in range(4):
        e = spoke_end(0.35, k)
        root = v3((SPOKE_X - 0.03, DRUM[1], DRUM[2]))
        log(fd, root, e, 0.02, 0.017, 0.01)
        fd.add(Sphere(e, 0.022), 0.008)
    return fd


def beam_field():
    """The throwing arm, cocked: a long tapered log through the axle, the bucket frame at its long end."""
    fd = Field("Beam")
    d = arm_dir(COCK)
    up = arm_up(COCK)
    log(fd, AXLE - d * SHORT, AXLE, 0.074, 0.084, 0.0)
    log(fd, AXLE, AXLE + d * LONG, 0.084, 0.062, 0.02)
    fd.add(Ellipsoid(AXLE, (0.1, 0.115, 0.115)), 0.02)                                  # the hub round the axle
    # bucket rim: a bent-wood hoop lashed on the arm's end
    bc = bucket_c(COCK)
    fd.add(Torus(bc + up * 0.08, 0.148, 0.019, R=rot_from_axes(z_axis=up)), 0.0)
    return fd


def lever_field():
    fd = Field("Lever")
    log(fd, LEVER_P, LEVER_T, 0.026, 0.024, 0.0)
    fd.add(Sphere(LEVER_T, 0.032), 0.01)
    fd.add(Cylinder(LEVER_P, 0.04, 0.05, rr=0.01, R=rot_from_axes(z_axis=(1, 0, 0))), 0.01)   # pivot block
    return fd


def hide_field():
    """The hide-lined bucket on the arm, the stuffed hide pad on the stop bar."""
    fd = Field("Hide")
    up = arm_up(COCK)
    bc = bucket_c(COCK)
    cup = Inter(Shell(Ellipsoid(bc, (0.158, 0.158, 0.13), R=rot_from_axes(z_axis=up)), 0.0, 0.018, pad=0.04),
                Func(lambda P: (P - (bc + up * 0.07).astype(F)) @ up.astype(F), bc - 0.3, bc + 0.3), 0.006)
    fd.add(cup, 0.0)
    fd.add(Ellipsoid(v3((MX, MY - 0.17, 1.3)), (0.12, 0.07, 0.07), disp=lambda P: F(0.004) * NOISE(P * F(25)), disp_amp=0.005), 0.0)
    return fd


def rope_field():
    """Lashings everywhere logs meet, the bucket's lashing, the counterweight's net bag and its ropes, the windlass rope
    and the trigger cord."""
    fd = Field("Rope")
    gz = GROUND_Z
    def lash(c, ax, r, n=2):
        for j in range(n):
            fd.add(Torus(c + v3(ax) * (j - (n - 1) / 2) * 0.022, r, 0.0095, R=rot_from_axes(z_axis=norm(v3(ax) + v3((0.3, 0.2, 0.1))))), 0.003)
    for x in (MX - 0.3, MX + 0.3):
        lash(v3((x, AXLE[1], AXLE[2] + 0.04)), (0, 0, 1), 0.062)
    for x in (MX - 0.34, MX + 0.34):
        for y in (MY - 0.5, MY + 0.12, MY + 0.86):
            lash(v3((x, y, gz + 0.12)), (1, 0, 0), 0.07, 1)
    for x in (MX - 0.31, MX + 0.31):
        lash(v3((x, MY - 0.17, 1.3)), (1, 0, 0), 0.05, 2)
    d = arm_dir(COCK)
    lash(AXLE + d * (LONG - 0.18), tuple(d), 0.062, 2)
    # counterweight: a net bag of stones hanging from the short end on two ropes (cw bone)
    st = short_tip(COCK)
    bagc = st + v3((0, 0, -0.27))
    for sx in (-1, 1):
        fd.add(RoundCone(st + v3((sx * 0.02, 0, -0.02)), bagc + v3((sx * 0.07, 0, 0.09)), 0.008, 0.008), 0.0)
    net = Field("Net")
    net.add(Ellipsoid(bagc, (0.14, 0.14, 0.12)), 0.0)
    for i in range(6):                                                               # meridians
        a = i * math.pi / 6
        R = rot_from_axes(z_axis=(math.cos(a), math.sin(a), 0.0))
        fd.add(Inter(Torus(bagc, 0.14, 0.008, R=R), Plane(bagc + v3((0, 0, 0.09)), (0, 0, 1)), 0.002), 0.002)
    for z in (-0.05, 0.03):                                                          # rings
        rr = 0.14 * math.sqrt(max(0.0, 1 - (z / 0.12) ** 2))
        fd.add(Torus(bagc + v3((0, 0, z)), rr, 0.007), 0.002)
    fd.add(Torus(bagc + v3((0, 0, 0.095)), 0.088, 0.011), 0.004)
    # the windlass rope, cocked: from the drum to the arm (haul bone, stretched in game)
    hp0, hp1 = haul_start(), haul_point(COCK)
    fd.add(RoundCone(hp0, hp1, 0.011, 0.011), 0.0)
    fd.add(Torus(DRUM + v3((0.0, 0, 0)), 0.064, 0.012, R=rot_from_axes(z_axis=(1, 0, 0))), 0.0)        # turns round the drum
    fd.add(Torus(DRUM + v3((0.03, 0, 0)), 0.064, 0.012, R=rot_from_axes(z_axis=(1, 0, 0))), 0.0)
    return fd


def haul_start():
    return DRUM + norm(haul_point(COCK) - DRUM) * 0.06


def stones_field():
    """The boulder in the bucket, the counterweight stones in the net, the boulders in the basket (the top one is the one
    she carries, its own bone)."""
    fd = Field("Stones")
    bc = bucket_c(COCK)
    up = arm_up(COCK)
    fd.add(Stone(bc + up * 0.085, 0.14, seed=11, cuts=10, noise=0.03), 0.0)
    bagc = short_tip(COCK) + v3((0, 0, -0.27))
    for i, (dx, dy, dz, r) in enumerate(((-0.05, -0.04, -0.03, 0.065), (0.055, -0.02, -0.035, 0.06), (0.0, 0.055, -0.03, 0.062),
                                         (-0.02, 0.0, 0.04, 0.058), (0.05, 0.04, 0.035, 0.05))):
        fd.add(Stone(bagc + v3((dx, dy, dz)) * 1.0 + v3((dx, dy, dz)) * 0.17, r * 1.17, seed=20 + i, cuts=8, noise=0.03), 0.004)
    for i, (dx, dy, dz, r) in enumerate(((-0.06, -0.03, 0.12, 0.085), (0.06, 0.02, 0.12, 0.08), (0.0, 0.07, 0.12, 0.075))):
        fd.add(Stone(BASKET + v3((dx, dy, dz)), r, seed=30 + i, cuts=9, noise=0.03), 0.004)
    fd.add(Stone(CARRY_C, 0.128, seed=12, cuts=10, noise=0.03), 0.0)
    return fd


CARRY_C = BASKET + v3((0.0, -0.01, 0.31))     # sits on the heap, touching none of it (its own bone)


def basket_field():
    fd = Field("Basket")
    c = BASKET
    body = RoundCone(c + v3((0, 0, 0.03)), c + v3((0, 0, 0.2)), 0.15, 0.185)
    def weave(P):
        q = P - c.astype(F)
        a = np.arctan2(q[:, 1], q[:, 0])
        return F(0.005) * np.sin(a * 20) * np.sin(q[:, 2] * F(110)) + F(0.003) * np.sin(q[:, 2] * F(220))
    fd.add(Inter(Shell(body, 0.0, 0.026, pad=0.03, disp=weave, disp_amp=0.008), Plane(c + v3((0, 0, 0.22)), (0, 0, 1)), 0.008), 0.0)
    fd.add(Torus(c + v3((0, 0, 0.215)), 0.185, 0.019), 0.008)
    fd.add(Cylinder(c + v3((0, 0, 0.03)), 0.15, 0.05, rr=0.018), 0.008)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.232, 1.626)), 0.05, 0.55)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.1, -0.15, 1.6)), 0.06, 0.7), (hp((sx * 0.18, 0.03, 1.66)), 0.06, 0.55),
                (J["elbow_" + sd] + v3((0, 0.025, 0)), 0.06, 0.3), (J["knee_" + sd] + v3((0, -0.03, 0)), 0.07, 0.35),
                (J["shoulder_" + sd] + v3((0, 0, 0.09)), 0.1, 0.2)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.043, 0.0145, -0.0145, -0.043):
            pts.append((wr + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.011, 0.03, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "boulder_catapult"
ROOT_NAME = "BoulderCatapultHQ"
TEX_PREFIX = "catapult"
MAT_NAME = "CatapultMat"
MESH_NAME = "Catapult"
BASE_MODULE = "catapult_base"
ANIM_MODULE = "anim_catapult"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Dress", "Fur", "Leather", "Bone", "Frame", "Winch", "Beam", "Lever", "Hide", "Rope",
         "Stones", "Basket"]
REGION_PARTS = ("Skin",)
DARK_HAIR = {"name": "HQ_DarkHair", "base": (0.16, 0.1, 0.07), "hi": (0.36, 0.24, 0.16)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_OperatorSkin", "base": (0.74, 0.52, 0.38), "ruddy": (0.8, 0.45, 0.36), "lips": (0.72, 0.38, 0.36),
                      "brow": ((0.12, 0.08, 0.05), (0.24, 0.16, 0.1)), "paint": (0.82, 0.5, 0.14),
                      "extra": ((6, (0.55, 0.33, 0.22), 0.55), (8, (0.1, 0.06, 0.04), 0.5))}),
    "Hair": ("hair", DARK_HAIR),
    "Dress": ("leather", {"name": "HQ_DeerHide", "base": (0.66, 0.48, 0.3)}),
    "Fur": ("fur", {"name": "HQ_WhiteFur", "base": (0.82, 0.8, 0.76), "tip": (0.97, 0.96, 0.93)}),
    "Leather": ("leather", {"name": "HQ_OperatorLeather", "base": (0.4, 0.24, 0.13)}),
    "Frame": ("club_wood", {"name": "HQ_CatapultWood"}), "Winch": ("club_wood", {"name": "HQ_CatapultWood"}),
    "Beam": ("club_wood", {"name": "HQ_CatapultWood"}), "Lever": ("club_wood", {"name": "HQ_CatapultWood"}),
    "Hide": ("leather", {"name": "HQ_BucketHide", "base": (0.5, 0.33, 0.2)}),
    "Rope": ("cord", {}), "Stones": ("stone", {"name": "HQ_Boulder", "scale": 0.5}), "Basket": ("basket", {}),
}
LOW_TARGETS = {"Skin": 6400, "Hair": 2200, "Teeth": 60, "Dress": 1500, "Fur": 900, "Leather": 1500, "Bone": 260,
               "Frame": 3200, "Winch": 500, "Beam": 900, "Lever": 220, "Hide": 600, "Rope": 1600, "Stones": 1400, "Basket": 700}
AO_EXCLUDE = ["Bone", "Rope", "Stones", "Lever", "Winch", "Beam", "Hide"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.7, 0.86, 1.0, 1.36)


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.86), (0, 0.045, 1.05)),
        "chest": ((0, 0.045, 1.05), (0, 0.06, 1.27)),
        "neck": ((0, 0.06, 1.27), hp((0, 0.02, 1.56))),
        "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.28,
    }


def prop_bones():
    return []


def extra_bones():
    """The machine's bones (none of them deform her): frame (static), beam (turns on the axle), boulder (in the bucket),
    cw (the counterweight, hangs straight down), haul (the windlass rope, stretched toward the arm), winch (the drum),
    lever (the trigger) and carry (the boulder she lifts from the basket)."""
    d = arm_dir(COCK)
    up = arm_up(COCK)
    bc = bucket_c(COCK)
    st = short_tip(COCK)
    h0, h1 = haul_start(), haul_point(COCK)
    return [
        ("frame", v3((MX, MY + 0.4, GROUND_Z + 0.2)), v3((MX, MY + 0.4, GROUND_Z + 0.5)), None),
        ("beam", AXLE, AXLE + d * 0.6, "frame"),
        ("boulder", bc + up * 0.085, bc + up * 0.22, "beam"),
        ("cw", st, st + v3((0, 0, -0.3)), "beam"),
        ("haul", h0, h1, "frame"),
        ("winch", v3((MX - 0.3, DRUM[1], DRUM[2])), v3((SPOKE_X, DRUM[1], DRUM[2])), "frame"),
        ("lever", LEVER_P, LEVER_T, "frame"),
        ("carry", CARRY_C, CARRY_C + v3((0, 0, 0.15)), None),
    ]


def _rigid_by(ob, fn):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {fn(np.array(v.co)): 1.0})


def _seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
    return np.linalg.norm(a + ab * t - p)


def rope_weights(ob, skin_ob, arm):
    d = arm_dir(COCK)
    st = short_tip(COCK)
    bagc = st + v3((0, 0, -0.27))
    h0, h1 = haul_start(), haul_point(COCK)
    def which(p):
        if np.linalg.norm(p - bagc) < 0.16 or _seg_dist(p, st, bagc) < 0.1:
            return "cw"
        if _seg_dist(p, h0, h1) < 0.03:
            return "haul"
        if np.linalg.norm(p - (AXLE + d * (LONG - 0.18))) < 0.12:
            return "beam"
        if np.linalg.norm(p - DRUM) < 0.09:
            return "winch"
        return "frame"
    _rigid_by(ob, which)


def stone_centres():
    """(centre, radius, bone) of every stone in Stones."""
    bc = bucket_c(COCK)
    up = arm_up(COCK)
    bagc = short_tip(COCK) + v3((0, 0, -0.27))
    out = [(bc + up * 0.085, 0.14, "boulder"), (CARRY_C, 0.128, "carry")]
    for dx, dy, dz, r in ((-0.05, -0.04, -0.03, 0.065), (0.055, -0.02, -0.035, 0.06), (0.0, 0.055, -0.03, 0.062),
                          (-0.02, 0.0, 0.04, 0.058), (0.05, 0.04, 0.035, 0.05)):
        out.append((bagc + v3((dx, dy, dz)) * 1.17, r * 1.17, "cw"))
    for dx, dy, dz, r in ((-0.06, -0.03, 0.12, 0.085), (0.06, 0.02, 0.12, 0.08), (0.0, 0.07, 0.12, 0.075)):
        out.append((BASKET + v3((dx, dy, dz)), r, "frame"))
    return out


def stones_weights(ob, skin_ob, arm):
    """Each stone (mesh island) goes rigidly to the bone of the stone whose centre is nearest its own centre."""
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
        bone = min(cs, key=lambda c: np.linalg.norm(cen - c[0]) / c[1])[2]
        for i in isl:
            _blend_add(ob, groups, i, {bone: 1.0})
    bm.free()


def leather_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "thigh.R", "thigh.L", "shin.R", "shin.L",
                                                       "foot.R", "foot.L", "head"}, caps={"thigh.R": 0.3, "thigh.L": 0.3})
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z > 1.5:                                                    # headband
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"head": 1.0})


def hair_weights(ob, skin_ob, arm):
    """Hair with the head; the lower half of the ponytail lags a little toward her neck and chest."""
    groups = {}
    z1, z0 = hp((0, 0, 1.7))[2], PONY[-1][2]
    for v in ob.data.vertices:
        p = v.co
        if p.z < z1 and p.y > 0.16:
            t = max(0.0, min(1.0, (z1 - p.z) / (z1 - z0)))
            _blend_add(ob, groups, v.index, {"head": 1.0 - 0.5 * t, "neck": 0.3 * t, "chest": 0.2 * t})
        else:
            _blend_add(ob, groups, v.index, {"head": 1.0})


def bone_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"forearm.L": 1.0} if v.co.x > 0.4 else {"head": 1.0})


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Dress": ("transfer", TORSO | {"clavicle.L", "upperarm.L", "thigh.R", "thigh.L"}, {"thigh.R": 0.4, "thigh.L": 0.4, "upperarm.L": 0.8}),
        "Fur": ("transfer", TORSO | {"clavicle.L", "upperarm.L", "thigh.R", "thigh.L", "shin.R", "shin.L"}, {"thigh.R": 0.4, "thigh.L": 0.4}),
        "Leather": ("custom", leather_weights), "Bone": ("custom", bone_weights),
        "Frame": ("rigid", "frame"), "Winch": ("rigid", "winch"), "Beam": ("rigid", "beam"), "Lever": ("rigid", "lever"),
        "Hide": ("custom", lambda ob, s, a: _rigid_by(ob, lambda p: "frame" if p[2] > 1.1 else "beam")),
        "Rope": ("custom", rope_weights), "Stones": ("custom", stones_weights), "Basket": ("rigid", "frame"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Frame", "Rope", "Basket", "Winch"):
        return 0.75
    if part in ("Beam", "Stones", "Hide"):
        return 0.9
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0026 if fine else 0.0034),
        ("Dress", dress_field(), 0.003 if fine else 0.0042),
        ("Fur", fur_field(), 0.0028 if fine else 0.0038),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Bone", bone_field(), 0.0015 if fine else 0.002),
        ("Frame", frame_field(), 0.004 if fine else 0.0055),
        ("Winch", winch_field(), 0.003 if fine else 0.004),
        ("Beam", beam_field(), 0.0035 if fine else 0.0045),
        ("Lever", lever_field(), 0.003 if fine else 0.004),
        ("Hide", hide_field(), 0.003 if fine else 0.004),
        ("Rope", rope_field(), 0.0022 if fine else 0.003),
        ("Stones", stones_field(), 0.004 if fine else 0.005),
        ("Basket", basket_field(), 0.003 if fine else 0.004),
    ]
