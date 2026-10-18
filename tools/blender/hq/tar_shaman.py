"""The Tar Pit Shaman (HQ tower). Rest pose = A-pose, facing -Y, feet at z=0; right side = -X.

A wiry, hunched old elder: bony limbs, a long white beard to his belly, long wispy white hair from under his cap,
huge white eyebrows sweeping out past his temples, a hooked nose, big ears, one eye wide and one squinting, a gap-toothed
grin. He wears an aurochs' skull as a cap (its great horns sweep out and up), a purple-dyed hide robe with ochre dots
and tar stains at the hem, a dark bear-fur mantle with a bone clasp, a cord belt with a pouch and bone charms. His left
hand is clawed and black with tar that drips from his fingertips; his right holds a gnarled staff whose top splits into
three tines cradling a glowing green spirit stone."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, grad, project_to, flow_line, Stone, lerp
from ugo import stripe2d, bez3, _blend_add

J = {
    "root": (0.0, 0.05, 0.76),
    "spine": (0.0, 0.04, 0.93),
    "chest": (0.0, 0.0, 1.14),
    "neck": (0.0, -0.06, 1.34),
    "head": (0.0, -0.1, 1.44),
    "head_end": (0.0, -0.14, 1.82),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.29, 0.0, 1.3)
    J["elbow_" + _s] = (_x * 0.46, 0.04, 1.05)
    J["wrist_" + _s] = (_x * 0.6, -0.02, 0.82)
    J["hip_" + _s] = (_x * 0.13, 0.05, 0.72)
    J["knee_" + _s] = (_x * 0.15, -0.01, 0.41)
    J["ankle_" + _s] = (_x * 0.16, 0.06, 0.1)
    J["toe_" + _s] = (_x * 0.185, -0.16, 0.03)
J = {k: v3(v) for k, v in J.items()}

# skin labels
SKIN, NAIL, LIP, MOUTH, BROW, PAINT, TAR = 0, 1, 2, 3, 4, 5, 7
# robe labels
CLOTH, OCHRE, RTAR = 0, 5, 7

# head: designed in the Rock Slinger's head coordinates, moved down and forward onto his stooped neck
HS = 1.04
DY, DZ = -0.12, -0.1
HPIV = v3((0.0, -0.1, 1.42))


def hp(p):
    p = v3(p) + v3((0, DY, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


HEAD_C = hp((0.0, 0.03, 1.735))
HEAD_RAD = v3((0.178, 0.19, 0.195)) * HS
EYE_R = hr(0.037)


def eye_c(sx):
    return hp((sx * 0.071, -0.152, 1.676))


def hstripe(a, b, ra, rb, y0=-0.6, y1=-0.1):
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


HAND_S = 1.0


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, fist, s=HAND_S, spread=0.0, claw=False):
    """Bony old hand: long fingers, knobbly knuckles. `spread` fans the fingers, `claw` curls them like talons."""
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.078 * s
    fd.add(RoundBox(c, v3((0.06, 0.03, 0.066)) * s, 0.026 * s, R=Rp), 0.025, SKIN)
    fd.add(Ellipsoid(c - n * 0.01 + t * 0.03 * s - f * 0.01, v3((0.032, 0.026, 0.048)) * s, R=Rp), 0.018, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = (1.45, 1.6, 1.2) if fist else ((0.55, 0.75, 0.6) if claw else (0.3, 0.5, 0.35))
    offs = (0.042, 0.014, -0.014, -0.042)
    lens = (1.0, 1.06, 1.0, 0.85)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.14 * s + t * o * s - n * 0.004
        d = norm(f - t * o * (1.2 + 6.0 * spread))
        pts, rads = [p], [0.019 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.058 * ls * s, 0.047 * ls * s, 0.037 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.88)
        fd.add(Chain(pts, rads, k=0.005), 0.01, SKIN)
        for j in (0, 1):                                              # knobbly knuckles
            fd.add(Sphere(pts[j] - n * 0.004 * (1 if j else 3), rads[j] * 1.12), 0.008, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.004 - back * 0.011, (0.012, 0.007, 0.016), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.05 * s + n * 0.01
    if fist:
        d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
        d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:
        d1 = norm(f * 0.45 + t * 0.85 + n * 0.25)
        d2 = norm(f * 0.75 + t * 0.45 + n * 0.45)
    p1 = tb + d1 * 0.052 * s
    p2 = p1 + d2 * 0.046 * s
    fd.add(Chain([tb, p1, p2], [0.023 * s, 0.02 * s, 0.017 * s], k=0.007), 0.016, SKIN)
    return [pts]


def finger_tips(side, s=HAND_S, spread=0.6, claw=True):
    """Where the open hand's fingertips end (for tar drips)."""
    wr, f, n, t = hand_frame(side)
    curl_ax = norm(np.cross(f, n))
    curls = (0.55, 0.75, 0.6) if claw else (0.3, 0.5, 0.35)
    out = []
    for i, (o, ls) in enumerate(zip((0.042, 0.014, -0.014, -0.042), (1.0, 1.06, 1.0, 0.85))):
        p = wr + f * 0.14 * s + t * o * s - n * 0.004
        d = norm(f - t * o * (1.2 + 6.0 * spread))
        for j, L in enumerate((0.058, 0.047, 0.037)):
            d = axis_angle(curl_ax, curls[j]) @ d
            p = p + d * L * ls * s
        out.append((p, d))
    return out


def foot(fd, side):
    """Long, bony bare feet."""
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.16)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    fd.add(Sphere(an + v3((0, 0.04, -0.05)), 0.055), 0.025, SKIN)
    fd.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.07)), (0.062, 0.122, 0.03), 0.028, R=Rz), 0.03, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.04 + v3((0, 0, -0.03)), (0.058, 0.085, 0.045), R=Rz), 0.025, SKIN)
    inner = -sx
    toes = [(0.047, 0.026), (0.018, 0.019), (-0.006, 0.018), (-0.027, 0.016), (-0.045, 0.015)]
    for i, (o, r) in enumerate(toes):
        base = an + fwd * (0.18 - 0.012 * i - (0.0 if i else -0.006)) + rgt * (o * inner) + v3((0, 0, -0.08))
        tip = base + fwd * (0.036 + r * 0.5) + v3((0, 0, -0.004))
        base[2] = 0.022 + r * 0.55
        tip[2] = 0.017 + r * 0.5
        fd.add(RoundCone(base, tip, r, r * 0.9), 0.01, SKIN)
        fd.add(Sphere(lerp(base, tip, 0.45) + v3((0, 0, r * 0.35)), r * 0.85), 0.006, SKIN)    # knobbly toe joints
        tn = norm(tip - base)
        fd.paint(Ellipsoid(tip + v3((0, 0, r * 0.55)), (r * 0.7, r * 0.75, r * 0.35), R=rot_from_axes(y_axis=tn, z_axis=(0, 0, 1))), NAIL)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.05, 0.0, 0.0)), 0.024), 0.016, SKIN)


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)                                         # tall, bald dome
    fd.add(E((0, -0.05, 1.588), (0.168, 0.14, 0.128)), 0.07, SKIN)                          # narrow jaw
    fd.add(E((0, -0.128, 1.502), (0.09, 0.07, 0.07)), 0.05, SKIN)                           # small pointed chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.115, -0.12, 1.636), 0.056), 0.045, SKIN)                          # sharp cheekbones
        fd.add(S((sx * 0.13, -0.05, 1.555), 0.06), 0.05, SKIN)
        pts = [hp((sx * 0.152, -0.048, 1.744)), hp((sx * 0.118, -0.128, 1.75)), hp((sx * 0.06, -0.176, 1.747)), hp((0.0, -0.188, 1.749))]
        fd.add(Chain(pts, [hr(0.02), hr(0.034), hr(0.04), hr(0.042)], k=hr(0.03)), hr(0.045), SKIN)
    fd.add(E((0, -0.165, 1.78), (0.072, 0.04, 0.05)), hr(0.04), SKIN)
    # huge white eyebrows sweeping out and down past his temples, tips sticking out
    for sx in (-1, 1):
        pts = [hp((sx * 0.036, -0.222, 1.752)), hp((sx * 0.072, -0.21, 1.768)), hp((sx * 0.114, -0.184, 1.774)), hp((sx * 0.158, -0.142, 1.762)),
               hp((sx * 0.196, -0.104, 1.736)), hp((sx * 0.228, -0.082, 1.704))]
        brow = Chain(pts, [hr(0.018), hr(0.025), hr(0.027), hr(0.023), hr(0.014), hr(0.003)], k=hr(0.012),
                     disp=lambda P: F(0.0035) * NOISE(P * np.array([30, 30, 90], F)), disp_amp=0.004)
        fd.add(brow, hr(0.012), BROW)
        fd.paint(Chain(pts, [hr(0.023), hr(0.03), hr(0.032), hr(0.028), hr(0.019), hr(0.007)], k=hr(0.012)), BROW)
    # eyes: his left wide open (the wild one), his right squinting
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        lid_up = hr(0.026) if sx > 0 else hr(0.008)
        up = Inter(Sphere(ec, EYE_R + hr(0.0085)), Plane(ec + v3((0, 0, lid_up)), (sx * 0.2, 0.12, -1.0)), hr(0.004))
        fd.add(up, hr(0.006), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, -hr(0.024 if sx > 0 else 0.018))), (sx * -0.1, 0.1, 1.0)), hr(0.004))
        fd.add(lo, hr(0.006), SKIN)
        fd.add(E((sx * 0.072, -0.16, 1.632), (0.036, 0.014, 0.011)), hr(0.01), SKIN)          # bags under the eyes
        for j, (dz, ang) in enumerate(((0.012, 0.25), (-0.004, 0.0), (-0.02, -0.25))):     # crow's feet
            a = hp((sx * 0.112, -0.125, 1.676 + dz))
            b = a + v3((sx * 0.03, 0.012, math.sin(ang) * 0.02))
            fd.sub(RoundCone(a, b, hr(0.0035), hr(0.002)), hr(0.002))
    # hooked nose: a bump on the bridge, a drooping tip
    fd.add(RoundCone(hp((0, -0.188, 1.728)), hp((0, -0.24, 1.655)), hr(0.026), hr(0.033)), hr(0.018), SKIN)
    fd.add(S((0, -0.222, 1.7), 0.03), hr(0.014), SKIN)
    fd.add(E((0, -0.262, 1.608), (0.04, 0.05, 0.046)), hr(0.016), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.04, -0.222, 1.6), 0.027), hr(0.013), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.021, -0.246, 1.578)), v3((0.01, 0.013, 0.008)) * HS, R=euler(0.4, 0, sx * 0.3)), hr(0.005))
    # gap-toothed grin under the moustache
    slot = [hp((-0.075, -0.17, 1.535)), hp((-0.04, -0.2, 1.518)), hp((0, -0.212, 1.513)), hp((0.042, -0.2, 1.52)), hp((0.08, -0.168, 1.54))]
    fd.sub(Chain(slot, [hr(0.01), hr(0.018), hr(0.02), hr(0.018), hr(0.01)], k=hr(0.01)), hr(0.008))
    fd.paint(Chain(slot, [hr(0.01), hr(0.018), hr(0.021), hr(0.018), hr(0.01)], k=hr(0.01)), MOUTH)
    up_lip = [(-0.08, -0.164, 1.546), (-0.044, -0.2, 1.538), (0, -0.214, 1.536), (0.046, -0.2, 1.54), (0.084, -0.16, 1.553)]
    lo_lip = [(-0.072, -0.165, 1.52), (-0.04, -0.196, 1.498), (0, -0.206, 1.494), (0.042, -0.196, 1.499), (0.076, -0.163, 1.524)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.007), hr(0.01), hr(0.011), hr(0.01), hr(0.007)], k=hr(0.009)), hr(0.007), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.007), hr(0.01), hr(0.011), hr(0.01), hr(0.007)], k=hr(0.009)), hr(0.007), LIP)
    # big old ears with long lobes
    for sx in (-1, 1):
        c = hp((sx * 0.183, 0.03, 1.655))
        R = euler(0, sx * 0.25, sx * -0.35)
        fd.add(Ellipsoid(c, v3((0.033, 0.06, 0.085)) * HS, R=R), hr(0.02), SKIN)
        fd.add(Sphere(c + v3((sx * 0.006, -0.012, -0.075)) * HS, hr(0.022)), hr(0.015), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.205, 0.018, 1.665)), v3((0.014, 0.036, 0.05)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))


# ======================================================================================= body
def torso_prims():
    return [
        (Ellipsoid((0, 0.02, 1.12), (0.21, 0.17, 0.22), R=euler(0.35, 0, 0)), 0.0),            # stooped ribcage
        (Ellipsoid((0, 0.1, 1.19), (0.23, 0.14, 0.17), R=euler(0.4, 0, 0)), 0.05),             # rounded upper back
        (Ellipsoid((0.09, -0.115, 1.17), (0.09, 0.04, 0.06), R=euler(0.35, 0, 0.2)), 0.04),    # thin old pecs
        (Ellipsoid((-0.09, -0.115, 1.17), (0.09, 0.04, 0.06), R=euler(0.35, 0, -0.2)), 0.04),
        (Ellipsoid((0, -0.035, 0.95), (0.17, 0.15, 0.16)), 0.07),                                # a little paunch
        (Ellipsoid((0, 0.05, 0.8), (0.19, 0.15, 0.13)), 0.07),                                   # pelvis
    ]


def traps():
    return Ellipsoid((0, 0.04, 1.31), (0.2, 0.1, 0.07), R=euler(0.6, 0, 0))


def neck_prim():
    return RoundCone((0, 0.0, 1.27), hp((0, 0.02, 1.575)), 0.075, hr(0.078))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.015, 0.0, 0.01)), 0.085)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.05, SKIN)
    fd.add(neck_prim(), 0.04, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.04, SKIN)
        fd.add(RoundCone(sh, el, 0.072, 0.056), 0.04, SKIN)
        fd.add(RoundCone(el, wr, 0.056, 0.043), 0.025, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.07, 0.062, 0.13), R=rot_from_axes(z_axis=wr - el)), 0.03, SKIN)
        fd.add(Sphere(el + v3((0, 0.03, 0)), 0.05), 0.02, SKIN)                                  # bony elbow
        fd.add(Sphere(wr + v3((sx * 0.02, 0.02, 0.0)), 0.026), 0.012, SKIN)                     # wrist bone
        hand(fd, side, fist=(side == "R"), spread=0.0 if side == "R" else 0.6, claw=(side == "L"))
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.1, 0.066), 0.05, SKIN)
        fd.add(Sphere(kn + v3((0, -0.022, 0.0)), 0.064), 0.025, SKIN)                           # knobbly knee
        fd.add(RoundCone(kn, an, 0.064, 0.042), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.025, 0)), (0.07, 0.068, 0.11), R=rot_from_axes(z_axis=an - kn)), 0.03, SKIN)
        foot(fd, side)
    head(fd)
    # tar: his left hand is black with it up to the wrist, and it drips from his fingers; his toes are dipped in it
    wr, f, n, t = hand_frame("L")
    hc = wr + f * 0.1
    fd.paint(Func(lambda P: np.linalg.norm(P - hc.astype(F), axis=1) - F(0.15) + F(0.03) * NOISE(P * F(24)), hc - 0.3, hc + 0.3), TAR)
    for k, (tip, d) in enumerate(finger_tips("L")):
        if k == 3:
            continue
        L = 0.035 + 0.015 * (k % 2)
        a = tip + d * 0.004
        fd.add(Chain([a, a + v3((0, 0, -L * 0.6)), a + v3((0, 0, -L))], [0.012, 0.007, 0.0095], k=0.006), 0.006, TAR)
    fd.paint(Func(lambda P: P[:, 2] - F(0.045) + F(0.012) * NOISE(P * F(30)), (-0.4, -0.5, -0.1), (0.4, 0.3, 0.2)), TAR)


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
    """A few yellowed teeth left: two in front, one on the side up top, one below."""
    fd = Field("Teeth")
    for x, y, z, w, h, rz in ((-0.013, -0.207, 1.53, 0.0095, 0.012, 0.1), (0.012, -0.207, 1.531, 0.009, 0.0115, -0.1),
                              (0.052, -0.19, 1.533, 0.008, 0.01, -0.5), (-0.03, -0.199, 1.507, 0.008, 0.009, 0.3)):
        fd.add(RoundBox(hp((x, y, z)), v3((w, 0.008, h)) * HS, hr(0.0042), R=euler(0.1, 0, rz)), 0.0)
    return fd


# ======================================================================================= hair & beard
def fan_lock(hull, start, heading, length, w_max, t0, segs=8, gravity=0.0, lift=0.0, tip_up=0.0, grooves=2, fd=None, thin_root=False,
             wave=0.0):
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
        if wave:
            tng = norm(line[min(i + 1, m)] - line[max(i - 1, 0)])
            lat = norm(np.cross(tng, n))
            q = q + lat * wave * math.sin(u * math.pi * 2.2)
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
                gp.append(pts[i] + lat * ws[i] * off * 1.2 + ns[i] * ts[i] * 1.04)
            if len(gp) >= 2:
                fd.sub(Chain(gp, [hr(0.0042)] * len(gp), k=0.003), hr(0.004))
    return lock


def head_hull():
    fd = Field("HeadHull")
    head(fd)
    fd.add(neck_prim(), 0.05)
    fd.add(Ellipsoid((0, -0.02, 1.12), (0.25, 0.22, 0.26), R=euler(0.35, 0, 0)), 0.05)     # chest + robe
    fd.add(Ellipsoid((0, -0.06, 0.95), (0.21, 0.19, 0.2)), 0.07)
    return fd


def hair_field(seed=3):
    """Long, thin white hair from under the skull cap at the sides and back, falling over his shoulders."""
    rng = np.random.RandomState(seed)
    fd = Field("Hair")
    hull = Field("HairHull")
    hull.add(Ellipsoid(HEAD_C, HEAD_RAD + 0.012), 0.0)
    hull.add(neck_prim(), 0.05)
    hull.add(traps(), 0.05)
    hull.add(Ellipsoid((0, 0.06, 1.2), (0.3, 0.2, 0.2), R=euler(0.4, 0, 0)), 0.06)       # mantle on the shoulders
    n = 13
    for i in range(n):
        a = math.pi * (0.42 + 1.16 * (i + 0.5) / n)
        hd = v3((math.sin(a), -math.cos(a), 0.0))
        o = v3((HEAD_C[0], HEAD_C[1], hp((0, 0, 1.7))[2])) + hd * 0.5
        st, ok = ray_hit(hull, [o], [-hd], tmax=0.5)
        if not ok[0]:
            continue
        backness = max(0.0, -math.cos(a))
        L = hr(0.3 + 0.08 * backness) + rng.uniform(0, 0.03)
        fan_lock(hull, st[0], hd * 0.25 + v3((0, 0, -1.0)), L, hr(0.07), hr(0.022), segs=8, gravity=0.6, lift=hr(0.03),
                 tip_up=hr(0.01), grooves=2, fd=fd, wave=hr(0.012))
    return fd


def beard_field(seed=5):
    """A long white beard, wavy, down to his belly and tapering to a point; a long drooping moustache."""
    rng = np.random.RandomState(seed)
    fd = Field("Beard")
    hull = beard_hull()
    def root_at(u):
        ax = abs(u) * 0.165
        z = 1.47 + 0.17 * (ax / 0.165) ** 1.8
        th = u * 1.75
        d = norm(v3((math.sin(th), -math.cos(th), 0.0)) * 1.0 + v3((0, 0, (z - 1.56) * 2.5)))
        o = hp((0, -0.02, z)) + d * 0.5
        h, ok = ray_hit(hull, [o], [-d], tmax=0.5)
        return h[0] if ok[0] else None
    nb = 17
    for i in range(nb):
        u = -1 + 2 * i / (nb - 1)
        r = root_at(u * 0.96)
        if r is None:
            continue
        front = 1 - abs(u)
        hd = v3((-u * 0.35, -0.12, -1.0))
        L = hr(0.2 + 0.32 * front ** 1.3) + rng.uniform(0, 0.02)
        fan_lock(hull, r + v3((0, 0, 0.008)), hd, L, hr(0.07 + 0.03 * front), hr(0.024 + 0.01 * front), segs=12, gravity=0.25,
                 lift=hr(0.015 + 0.02 * front ** 1.5), tip_up=hr(0.0), grooves=2, fd=fd, thin_root=True, wave=hr(0.01))
    for sx in (-1, 1):                                          # long drooping moustache
        pts = [hp((sx * 0.004, -0.244, 1.566)), hp((sx * 0.05, -0.236, 1.562)), hp((sx * 0.1, -0.205, 1.54)), hp((sx * 0.13, -0.18, 1.48)),
               hp((sx * 0.14, -0.175, 1.41)), hp((sx * 0.135, -0.18, 1.35))]
        ns = [norm(v3((sx * 0.3, -1.0, 0.2)))] * 6
        fd.add(Lock(pts, [hr(0.018), hr(0.026), hr(0.024), hr(0.018), hr(0.012), hr(0.003)],
                    [hr(0.014), hr(0.017), hr(0.016), hr(0.012), hr(0.009), hr(0.003)], ns, k=hr(0.011)), hr(0.008))
    return fd


def beard_bead_points():
    """Two bone beads threaded on locks of the beard (on its surface, low down)."""
    hull = beard_hull()
    out = []
    for x, z in ((-0.05, 1.18), (0.055, 1.1)):
        h, ok = ray_hit(hull, [v3((x, -0.8, z))], [v3((0, 1, 0))], tmax=0.8)
        out.append(h[0] + v3((0, -0.03, 0)))
    return out


# ======================================================================================= the aurochs skull cap
CAP_C = HEAD_C + v3((0.0, 0.01, 0.04))


def skull_field():
    """An aurochs' skull worn as a cap: the dome of its cranium over his crown, the poll ridge across the top between the
    horns, the broad frontal plate with the beast's deep eye sockets at its corners above his brows, and the short stub
    of its broken snout pointing down his forehead."""
    fd = Field("Skull")
    pit = lambda P: F(0.003) * NOISE(P * F(35))
    cut = F(hp((0, 0, 1.765))[2])
    cap = Inter(Shell(Ellipsoid(HEAD_C, HEAD_RAD), 0.026, 0.03, pad=0.08, disp=pit, disp_amp=0.004),
                Func(lambda P: cut - P[:, 2] - (P[:, 1] - F(HEAD_C[1])) * F(0.35), HEAD_C - 0.4, HEAD_C + 0.4), 0.01)
    fd.add(cap, 0.0)
    fd.add(Chain([hp((-0.15, 0.06, 1.9)), hp((0, 0.07, 1.935)), hp((0.15, 0.06, 1.9))], [hr(0.038), hr(0.045), hr(0.038)], k=hr(0.02),
                 disp=pit, disp_amp=0.004), hr(0.03))                                             # poll ridge
    R = euler(-0.62, 0, 0)
    fd.add(RoundBox(hp((0, -0.115, 1.835)), v3((0.15, 0.035, 0.085)) * HS, hr(0.03), R=R, disp=pit, disp_amp=0.004), hr(0.03))  # frontal plate
    for sx in (-1, 1):
        oc = hp((sx * 0.135, -0.17, 1.8))
        Ro = rot_from_axes(z_axis=norm(v3((sx * 0.7, -0.7, 0.15))))
        fd.add(Torus(oc, hr(0.038), hr(0.017), R=Ro), hr(0.022))                                   # orbit rims
        fd.sub(Ellipsoid(oc + Ro @ v3((0, 0, 0.004)), v3((0.03, 0.03, 0.04)) * HS, R=Ro), hr(0.006))   # deep sockets
    # broken snout: a flat stub down the middle of his forehead, ragged at the end
    a, b = hp((0, -0.175, 1.835)), hp((0, -0.235, 1.765))
    nrm = norm(np.cross(b - a, v3((1, 0, 0))))
    stub = Inter(RoundCone(a, b, hr(0.05), hr(0.04)), Func(lambda P: np.abs((P - a.astype(F)) @ nrm.astype(F)) - F(hr(0.026)), a - 0.3, a + 0.3), 0.01)
    fd.add(stub, hr(0.02))
    tip = b + norm(b - a) * hr(0.03)
    fd.sub(Func(lambda P: (P - tip.astype(F)) @ norm(b - a).astype(F) * F(-1) + F(0.008) * np.abs(np.sin(P[:, 0] * F(110))) + F(0.004) * NOISE(P * F(60)),
                tip - 0.15, tip + 0.15), 0.004)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.175, 0.03, 1.9)), hr(0.05)), hr(0.025))                       # horn bases
    return fd


def horn_curve(sx):
    p0 = hp((sx * 0.175, 0.03, 1.9))
    p1 = p0 + v3((sx * 0.26, 0.04, -0.01))
    p2 = p0 + v3((sx * 0.43, -0.1, 0.12))
    p3 = p0 + v3((sx * 0.38, -0.24, 0.33))
    return p0, p1, p2, p3


def horns_field():
    """The aurochs' great horns: out to the sides, then curving forward and up."""
    fd = Field("Horns")
    for sx in (-1, 1):
        p0, p1, p2, p3 = horn_curve(sx)
        ts = np.linspace(0, 1, 20)
        pts = [bez3(p0, p1, p2, p3, t) for t in ts]
        rad = [hr(0.058) * (1 - t) ** 0.75 + 0.006 for t in ts]
        fd.add(Chain(pts, rad, k=0.01, disp=lambda P: F(0.0025) * NOISE(P * np.array([30, 30, 30], F)), disp_amp=0.003), 0.0)
        for t in (0.08, 0.14, 0.2):                                     # growth rings near the base
            c = bez3(p0, p1, p2, p3, t)
            tg = norm(bez3(p0, p1, p2, p3, t + 0.01) - bez3(p0, p1, p2, p3, t - 0.01))
            fd.add(Torus(c, hr(0.058) * (1 - t) ** 0.75 + 0.004, 0.006, R=rot_from_axes(z_axis=tg)), 0.004)
    return fd


# ======================================================================================= clothing
def robe_base():
    b = Field("RobeBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.04)
        b.add(RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.072, 0.056), 0.04)
    b.add(RoundCone((0, 0.04, 0.86), (0, 0.02, 0.26), 0.2, 0.33), 0.08)                        # long skirt, flaring
    return b


def robe_field():
    """Purple-dyed hide robe to his shins: ragged hem, sleeves to the elbows, a band of ochre dots near the hem and tar
    stains where it drags."""
    fd = Field("Robe")
    base = robe_base()
    hide = lambda P: F(0.004) * NOISE(P * F(12)) + F(0.002) * NOISE(P * F(36)) + F(0.006) * np.sin(P[:, 0] * F(26) + F(0.5) * NOISE(P * F(3))) * np.clip((F(0.8) - P[:, 2]) * F(2), 0, 1)
    def keep(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        hem = F(0.28) + F(0.035) * np.abs(np.sin(a * F(6.5))) + F(0.016) * NOISE(P * F(8)) - P[:, 2]
        neck = F(0.1) - np.sqrt(P[:, 0] ** 2 + (P[:, 1] + F(0.02)) ** 2) - (P[:, 2] - F(1.36)) * F(0.4)
        neck = np.where(P[:, 2] > F(1.18), neck, F(-1))
        vee = F(0.05) + (F(1.36) - P[:, 2]) * F(0.35) - np.abs(P[:, 0])
        vee = np.where((P[:, 1] < F(-0.05)) & (P[:, 2] > F(1.08)), vee, F(-1))
        out = np.maximum(np.maximum(hem, neck), vee)
        for side, sx in (("R", -1), ("L", 1)):
            sh, el = J["shoulder_" + side], J["elbow_" + side]
            ax = norm(el - sh)
            c = sh + (el - sh) * 0.8
            sl = (P - c.astype(F)) @ ax.astype(F) + F(0.012) * NOISE(P * F(22) + 4 * sx)
            sl = np.where(P[:, 0] * F(sx) > F(0.22), sl, F(-1))
            out = np.maximum(out, sl)
        return out
    fd.add(Inter(Shell(base, 0.016, 0.024, pad=0.1, disp=hide, disp_amp=0.01), Func(keep, (-1, -1, 0.1), (1, 1, 1.6)), 0.006), 0.0, CLOTH)
    # a band of ochre dots near the hem
    for i in range(16):
        a = 2 * math.pi * (i + 0.5) / 16
        for row, z0 in enumerate((0.45, 0.53)):
            zc = z0 + (0.0 if (i + row) % 2 else 0.02)
            fd.paint(Func(lambda P, a=a, zc=zc: _dot2d(P, a, zc) - F(0.019), (-0.6, -0.6, zc - 0.1), (0.6, 0.6, zc + 0.1)), OCHRE)
    fd.paint(Func(lambda P: P[:, 2] - F(0.36) + F(0.035) * NOISE(P * F(11)) + F(0.02) * np.abs(np.sin(P[:, 0] * F(17))), (-0.6, -0.6, 0.0), (0.6, 0.6, 0.6)), RTAR)
    return fd


def _dot2d(P, a, z0):
    """Distance on the robe (angle around his body x height) to an ochre dot at angle a, height z0."""
    ang = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
    da = np.angle(np.exp(1j * (ang - a))).astype(F)
    return np.sqrt((da * F(0.31)) ** 2 + (P[:, 2] - F(z0)) ** 2)


def mantle_base():
    b = Field("MantleBase")
    for p, k in torso_prims()[:4]:
        b.add(p, k)
    b.add(traps(), 0.05)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.04)
        b.add(RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.072, 0.056), 0.04)
    b.add(neck_prim(), 0.05)
    return b


def mantle_field():
    """Dark bear-fur mantle over his shoulders and hunched back, open at the front, a ragged edge."""
    fd = Field("Mantle")
    base = mantle_base()
    fur = lambda P: F(0.008) * NOISE(P * np.array([14, 14, 5], F)) + F(0.005) * NOISE(P * np.array([40, 40, 12], F) + 3) + F(0.002) * NOISE(P * F(90))
    def keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        back = np.clip((y + F(0.05)) / F(0.2), 0, 1)
        zb = F(1.14) - F(0.2) * back + F(0.03) * np.abs(np.sin(np.arctan2(x, -y) * F(7))) + F(0.015) * NOISE(P * F(9))
        front = np.where(y < F(-0.02), F(0.07) + (F(1.3) - z) * F(0.5) - np.abs(x), F(-1))
        neckc = F(0.115) - np.sqrt(x * x + (y + F(0.03)) ** 2)
        neckc = np.where(z > F(1.3), neckc, F(-1))
        arm = np.maximum(np.abs(x) - F(0.4), F(-1))
        return np.maximum(np.maximum(np.maximum(zb - z, front), neckc), arm)
    fd.add(Inter(Shell(base, 0.042, 0.038, pad=0.12, disp=fur, disp_amp=0.016), Func(keep, (-1, -1, 0.6), (1, 1, 1.7)), 0.01), 0.0)
    return fd


BELT_Z = 0.86


def rope_field():
    """Cord belt round the robe (knot and hanging ends), the necklace cord, the bindings on the staff."""
    fd = Field("Rope")
    base = robe_base()
    belt = Inter(Shell(base, 0.04, 0.02, pad=0.1), Func(lambda P: np.abs(P[:, 2] - (F(BELT_Z) + F(0.05) * P[:, 1])) - F(0.011), (-1, -1, 0.6), (1, 1, 1.1)), 0.004)
    fd.add(belt, 0.0)
    kp, _ = ray_hit(Func(lambda P: base.eval(P) - F(0.05), (-1, -1, 0.5), (1, 1, 1.3)), [v3((-0.08, -0.8, BELT_Z - 0.01))], [v3((0, 1, 0))], tmax=0.8)
    k0 = kp[0] + v3((0, -0.01, 0))
    fd.add(Ellipsoid(k0, (0.024, 0.018, 0.022)), 0.006)
    fd.add(Chain([k0, k0 + v3((-0.01, -0.02, -0.1)), k0 + v3((-0.02, -0.022, -0.2))], [0.009, 0.009, 0.007], k=0.006), 0.006)
    fd.add(Chain([k0, k0 + v3((0.012, -0.02, -0.08)), k0 + v3((0.022, -0.018, -0.16))], [0.009, 0.009, 0.007], k=0.006), 0.006)
    a0, ax = staff_axis()
    for s in (0.6, 0.64):
        fd.add(Torus(a0 + ax * s, staff_radius(s) + 0.004, 0.007, R=rot_from_axes(z_axis=ax)), 0.003)
    for s, ang in ((0.62, 30.0), (0.62, 200.0)):                     # cords for the hanging charms
        top, bot = charm_points(s, ang)
        fd.add(RoundCone(top, bot, 0.004, 0.004), 0.002)
    return fd


def leather_field():
    """A hide pouch on his belt, the staff's grip wrap."""
    fd = Field("Leather")
    base = robe_base()
    bp, _ = ray_hit(Func(lambda P: base.eval(P) - F(0.04), (-1, -1, 0.5), (1, 1, 1.3)), [v3((0.6, -0.4, 0.78))], [norm(v3((-0.8, 0.6, 0)))], tmax=0.9)
    out = norm(v3((0.8, -0.6, 0)))
    bc = bp[0] + out * 0.045
    R = rot_from_axes(y_axis=out, z_axis=(0, 0, 1))
    fd.add(Ellipsoid(bc, (0.06, 0.042, 0.068), R=R, disp=lambda P: F(0.003) * NOISE(P * F(30)), disp_amp=0.004), 0.0)
    fd.add(Torus(bc + v3((0, 0, 0.04)), 0.05, 0.007, R=R), 0.005)
    fd.add(Chain([bc + v3((0, 0, 0.045)) - out * 0.015, bc + v3((0.0, 0, 0.09)) - out * 0.03], [0.009, 0.009]), 0.006)
    a0, ax = staff_axis()
    for i in range(4):
        fd.add(Torus(a0 + ax * (-0.05 + 0.04 * i), staff_radius(0) + 0.005, 0.009, R=rot_from_axes(z_axis=norm(ax + v3((0.3, 0, 0))))), 0.003)
    return fd


def bone_field():
    """Necklace of bone beads and claws, the mantle's bone clasp, charms hanging from the staff, beads in his beard."""
    fd = Field("Bone")
    # necklace on his chest, below the beard's sides
    hull = Field("ChestHull")
    for p, k in torso_prims():
        hull.add(p, k)
    hull.add(traps(), 0.05)
    hull.add(neck_prim(), 0.05)
    for i in range(9):
        u = (i - 4) / 4
        a = u * 1.1
        d = v3((math.sin(a), -math.cos(a), 0.0))
        z = 1.2 + 0.07 * u * u
        o = v3((0, 0.0, z)) + d * 0.6
        h, ok = ray_hit(Func(lambda P: hull.eval(P) - F(0.045), (-1, -1, 0.8), (1, 1, 1.6)), [o], [-d], tmax=0.6)
        if not ok[0]:
            continue
        p = h[0]
        if i % 2:
            fd.add(Sphere(p, 0.017), 0.0)
        else:
            fd.add(Chain([p, p + d * 0.012 + v3((0, 0, -0.03)), p + d * 0.018 + v3((0.004, 0, -0.055))], [0.013, 0.01, 0.003], k=0.006), 0.0)
    # mantle clasp: a bone toggle where the fur meets at his collarbone
    c = v3((0.0, -0.205, 1.27))
    fd.add(RoundCone(c + v3((-0.05, 0, 0.004)), c + v3((0.05, 0, -0.004)), 0.014, 0.014), 0.0)
    for sx in (-1, 1):
        fd.add(Sphere(c + v3((sx * 0.052, 0, -sx * 0.004)), 0.018), 0.004)
    # charms hanging from the staff
    for s, ang in ((0.62, 30.0), (0.62, 200.0)):
        top, bot = charm_points(s, ang)
        fd.add(RoundCone(bot, bot + v3((0, 0, -0.045)), 0.012, 0.008), 0.0)
        fd.add(Sphere(bot + v3((0, 0, -0.05)), 0.014), 0.004)
    # beads braided into the beard
    for b in beard_bead_points():
        fd.add(Cylinder(b, hr(0.018), hr(0.03), rr=hr(0.006)), 0.0)
    return fd


# ======================================================================================= the staff and its spirit stone
STAFF_TOP = 0.72        # where the staff splits into three tines
ORB_S = 0.86            # spirit stone along the staff
ORB_R = 0.072


def staff_axis():
    """Grip centre and staff direction in the rest pose: the staff runs through the right fist, top toward the thumb."""
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t


def staff_radius(s):
    return 0.029 + 0.008 * max(0.0, min(1.0, (s - 0.3) / 0.4))


def charm_points(s, ang):
    a0, ax = staff_axis()
    u = norm(np.cross(ax, v3((0, 0, 1))))
    w = np.cross(ax, u)
    d = norm(u * math.cos(math.radians(ang)) + w * math.sin(math.radians(ang)))
    top = a0 + ax * s + d * (staff_radius(s) + 0.004)
    return top, top + d * 0.01 + v3((0, 0, -0.07))


def staff_field():
    """A gnarled staff, taller than him, splitting at the top into three tines that curl round the spirit stone."""
    fd = Field("Staff")
    a0, ax = staff_axis()
    u = norm(np.cross(ax, v3((0, 0, 1))))
    w = np.cross(ax, u)
    bark = lambda P: F(0.004) * NOISE(P * np.array([50, 50, 50], F)) + F(0.002) * NOISE(P * F(120))
    ss = np.linspace(-1.1, STAFF_TOP, 22)
    pts = []
    for s in ss:
        wob = 0.012 * math.sin(s * 5.0) * u + 0.01 * math.sin(s * 3.3 + 1.0) * w
        pts.append(a0 + ax * s + wob)
    fd.add(Chain(pts, [staff_radius(s) for s in ss], k=0.01, disp=bark, disp_amp=0.006), 0.0)
    for s, a, r in ((-0.6, 0.5, 0.02), (-0.25, 2.6, 0.018), (0.35, 4.4, 0.02)):               # knots
        d = norm(u * math.cos(a) + w * math.sin(a))
        fd.add(Sphere(a0 + ax * s + d * staff_radius(s) * 0.9, r), 0.01)
    oc = a0 + ax * ORB_S
    for k in range(3):                                                                         # three tines
        a = k * 2 * math.pi / 3 + 0.3
        d = norm(u * math.cos(a) + w * math.sin(a))
        p0 = a0 + ax * (STAFF_TOP - 0.03)
        p1 = a0 + ax * (STAFF_TOP + 0.06) + d * 0.05
        p2 = oc + d * (ORB_R + 0.03) + ax * 0.0
        p3 = oc + d * (ORB_R * 0.55) + ax * (ORB_R + 0.035)
        tpts = [bez3(p0, p1, p2, p3, t) for t in np.linspace(0, 1, 9)]
        fd.add(Chain(tpts, [0.022 - 0.016 * t for t in np.linspace(0, 1, 9)], k=0.008, disp=bark, disp_amp=0.004), 0.01)
    fd.add(Sphere(a0 + ax * -1.1, 0.034), 0.01)                                                 # worn butt
    return fd


def orb_field():
    fd = Field("Orb")
    a0, ax = staff_axis()
    fd.add(Sphere(a0 + ax * ORB_S, ORB_R, disp=lambda P: F(0.003) * NOISE(P * F(30)), disp_amp=0.004), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.262, 1.608)), 0.07, 0.95)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.105, -0.15, 1.6)), 0.06, 0.45), (hp((sx * 0.19, 0.03, 1.655)), 0.08, 0.8),
                (J["elbow_" + sd] + v3((0, 0.03, 0)), 0.06, 0.4), (J["knee_" + sd] + v3((0, -0.03, 0)), 0.07, 0.4)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.14 + t * o - n * 0.012, 0.03, 0.5))
        an = J["ankle_" + side]
        pts.append((an + v3((0, -0.18, -0.07)), 0.06, 0.5))
    return pts


def beard_hull():
    """Head, plus the volume the long beard hangs over: from the jaw down over his chest to his belly."""
    fd = head_hull()
    fd.add(Ellipsoid(hp((0, -0.15, 1.46)), v3((0.12, 0.08, 0.09)) * HS), hr(0.05))
    top = hp((0, -0.13, 1.47))
    fd.add(Ellipsoid(v3((0, top[1] - 0.005, 1.17)), (0.135, 0.085, 0.27), R=euler(0.12, 0, 0)), 0.08)
    return fd


# ======================================================================================= build config
GLB_NAME = "tar_shaman"
ROOT_NAME = "TarShamanHQ"
TEX_PREFIX = "shaman"
MAT_NAME = "ShamanMat"
MESH_NAME = "Shaman"
BASE_MODULE = "shaman_base"
ANIM_MODULE = "anim_shaman"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Skull", "Horns", "Robe", "Mantle", "Rope", "Leather", "Bone", "Staff", "Orb"]
REGION_PARTS = ("Skin", "Robe")
WHITE_HAIR = {"name": "HQ_WhiteHair", "base": (0.86, 0.85, 0.82), "hi": (1.0, 0.99, 0.97), "low": (0.6, 0.58, 0.56),
              "streak": (0.66, 0.64, 0.6), "tint": (0.8, 0.77, 0.7)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_ShamanSkin", "base": (0.78, 0.58, 0.46), "ruddy": (0.8, 0.48, 0.4), "lips": (0.66, 0.42, 0.4),
                      "brow": ((0.82, 0.8, 0.76), (0.98, 0.97, 0.94)), "extra": ((7, (0.04, 0.035, 0.04), 0.12),)}),
    "Hair": ("hair", WHITE_HAIR), "Beard": ("hair", WHITE_HAIR),
    "Skull": ("bone", {"name": "HQ_SkullCap"}),
    "Horns": ("horn", {}),
    "Robe": ("robe", {}),
    "Mantle": ("fur", {"name": "HQ_BearFur", "base": (0.22, 0.15, 0.1), "tip": (0.48, 0.37, 0.26)}),
    "Leather": ("leather", {"name": "HQ_ShamanLeather", "base": (0.38, 0.24, 0.14)}),
    "Staff": ("club_wood", {"name": "HQ_StaffWood"}),
    "Orb": ("glow_ball", {"name": "HQ_SpiritStone"}),
}
GLOW = {"Orb": ((0.42, 1.0, 0.52), 1.5)}            # stronger washes out to white in game
LOW_TARGETS = {"Skin": 6600, "Hair": 1100, "Beard": 1900, "Skull": 1100, "Horns": 900, "Robe": 2600, "Mantle": 1800, "Rope": 600,
               "Leather": 360, "Bone": 600, "Teeth": 120, "Staff": 1000, "Orb": 320}
AO_EXCLUDE = ["Bone", "Rope", "Staff", "Orb", "Leather"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.72, 0.88, 1.04, 1.4)


def torso_bones():
    return {
        "spine": ((0, 0.04, 0.9), (0, 0.04, 1.08)),
        "chest": ((0, 0.04, 1.08), (0, -0.02, 1.3)),
        "neck": ((0, -0.02, 1.3), hp((0, 0.02, 1.56))),
        "head": (hp((0, 0.02, 1.56)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.29,
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
    return -1.2 < s < ORB_S + 0.2 and r < 0.16 + pad


def beard_weights(ob, skin_ob, arm):
    """The top of the beard moves with his head, the long lower part hangs with his chest."""
    groups = {}
    z1, z0 = hp((0, 0, 1.47))[2], 1.18
    for v in ob.data.vertices:
        z = v.co.z
        t = max(0.0, min(1.0, (z1 - z) / (z1 - z0)))
        t = t * t * (3 - 2 * t)
        _blend_add(ob, groups, v.index, {"head": 1.0 - t, "neck": 0.25 * t * (1 - t) * 4 * 0.5, "chest": t * 0.85, "spine": t * 0.15})


def hair_weights(ob, skin_ob, arm):
    groups = {}
    z1, z0 = hp((0, 0, 1.6))[2], 1.25
    for v in ob.data.vertices:
        t = max(0.0, min(1.0, (z1 - v.co.z) / (z1 - z0)))
        _blend_add(ob, groups, v.index, {"head": 1.0 - 0.6 * t, "neck": 0.3 * t, "chest": 0.3 * t})


def rope_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"thigh.R", "thigh.L"}, caps={"thigh.R": 0.3, "thigh.L": 0.3})
    groups = {}
    for v in ob.data.vertices:
        if _near_staff(v.co) and v.co.x < -0.45:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"hand.R": 1.0})


def leather_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        if _near_staff(v.co) and v.co.x < -0.45:
            w = {"hand.R": 1.0}
        else:
            w = {"root": 0.6, "spine": 0.2, "thigh.L": 0.2}
        _blend_add(ob, groups, v.index, w)


def bone_weights(ob, skin_ob, arm):
    groups = {}
    beads = beard_bead_points()
    for v in ob.data.vertices:
        p = np.array(v.co)
        if _near_staff(p) and p[0] < -0.45:
            w = {"hand.R": 1.0}
        elif min(np.linalg.norm(p - b) for b in beads) < 0.05:
            w = {"chest": 0.85, "spine": 0.15}
        else:
            w = {"chest": 1.0}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Beard": ("custom", beard_weights), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Skull": ("rigid", "head"), "Horns": ("rigid", "head"),
        "Robe": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L", "shin.R", "shin.L"},
                 {"thigh.R": 0.4, "thigh.L": 0.4, "shin.R": 0.25, "shin.L": 0.25, "upperarm.R": 0.9, "upperarm.L": 0.9}),
        "Mantle": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"}, {"upperarm.R": 0.45, "upperarm.L": 0.45}),
        "Rope": ("custom", rope_weights), "Leather": ("custom", leather_weights), "Bone": ("custom", bone_weights),
        "Staff": ("rigid", "hand.R"), "Orb": ("rigid", "orb"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < -0.1 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Bone", "Rope"):
        return 0.8
    if part == "Skull" and c.y < -0.1:
        return 1.3
    if part == "Skin" and abs(c.x) > 0.55 and c.z < 0.95:
        return 1.35
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.0028 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0026 if fine else 0.0034),
        ("Beard", beard_field(), 0.0026 if fine else 0.0034),
        ("Skull", skull_field(), 0.0025 if fine else 0.0035),
        ("Horns", horns_field(), 0.0025 if fine else 0.0035),
        ("Robe", robe_field(), 0.0032 if fine else 0.0045),
        ("Mantle", mantle_field(), 0.0032 if fine else 0.0045),
        ("Rope", rope_field(), 0.0018 if fine else 0.0024),
        ("Leather", leather_field(), 0.002 if fine else 0.0028),
        ("Bone", bone_field(), 0.0015 if fine else 0.002),
        ("Staff", staff_field(), 0.0022 if fine else 0.003),
        ("Orb", orb_field(), 0.002),
    ]
