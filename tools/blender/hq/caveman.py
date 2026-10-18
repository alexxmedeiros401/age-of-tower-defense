"""The Rock Slinger caveman, sculpted as distance fields (rest pose = A-pose, facing -Y, feet at z=0).

Character's right side is -X. Joint positions in J are shared with the armature (rig.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)

R_, L_ = -1, 1


def lerp(a, b, t):
    return v3(a) + (v3(b) - v3(a)) * t


J = {
    "root": (0.0, 0.03, 0.80),
    "spine": (0.0, 0.03, 0.97),
    "chest": (0.0, 0.05, 1.17),
    "neck": (0.0, 0.07, 1.42),
    "head": (0.0, 0.02, 1.56),
    "head_end": (0.0, -0.02, 1.96),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.37, 0.07, 1.37)
    J["elbow_" + _s] = (_x * 0.60, 0.10, 1.10)
    J["wrist_" + _s] = (_x * 0.77, 0.04, 0.86)
    J["hip_" + _s] = (_x * 0.15, 0.04, 0.74)
    J["knee_" + _s] = (_x * 0.18, 0.0, 0.42)
    J["ankle_" + _s] = (_x * 0.19, 0.06, 0.11)
    J["toe_" + _s] = (_x * 0.21, -0.16, 0.035)
J = {k: v3(v) for k, v in J.items()}

# labels (painting masks in the skin)
SKIN, NAIL, LIP, MOUTH, BROW = 0, 1, 2, 3, 4


class Inter(Prim):
    """Smooth intersection of two prims (bounds of the first)."""

    def __init__(self, a, b, k=0.0):
        super().__init__()
        self.a, self.b, self.k = a, b, k
        self.lo, self.hi = a.lo, a.hi

    def sdf(self, P):
        return smax(self.a(P), self.b(P), self.k)


class Shell(Prim):
    """Hollow layer of a field: surface offset by `off`, thickness `t` (centered on the offset)."""

    def __init__(self, field_or_prim, off, t, pad=0.08, disp=None, disp_amp=0.0):
        super().__init__(disp=disp, disp_amp=disp_amp)
        self.f, self.off, self.t = field_or_prim, off, t
        if isinstance(field_or_prim, Field):
            lo, hi = field_or_prim.bounds()
        else:
            lo, hi = field_or_prim.lo, field_or_prim.hi
        self.lo, self.hi = lo - pad - disp_amp, hi + pad + disp_amp

    def sdf(self, P):
        d = self.f.eval(P, margin=abs(self.off) + self.t) if isinstance(self.f, Field) else self.f(P)
        return np.abs(d - F(self.off)) - F(self.t / 2)


# ======================================================================================= hands & feet
def hand_frame(side):
    sx = -1 if side == "R" else 1
    el, wr = J["elbow_" + side], J["wrist_" + side]
    f = norm((wr - el) + v3((sx * 0.06, 0, -0.10)))          # fingers point down along the arm
    n = v3((-sx, 0, 0))                                      # palm faces the body
    n = norm(n - f * (n @ f))
    t = np.cross(f, n)
    if t[1] > 0:                                             # thumb side forward (-Y)
        t = -t
    return wr, f, n, t


def hand(fd, side, fist):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.075
    fd.add(RoundBox(c, (0.064, 0.034, 0.066), 0.03, R=Rp), 0.03, SKIN)              # palm
    fd.add(Ellipsoid(c - n * 0.012 + t * 0.03 - f * 0.01, (0.035, 0.03, 0.05), R=Rp), 0.02, SKIN)  # thumb pad
    curl_ax = norm(np.cross(f, n))
    curls = (1.45, 1.6, 1.2) if fist else (0.35, 0.55, 0.4)
    offs = (0.043, 0.0145, -0.0145, -0.043)
    lens = (0.95, 1.0, 0.95, 0.8)
    tips = []
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 + t * o - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.022 * (0.92 if i == 3 else 1.0)]
        seglen = (0.05 * ls, 0.04 * ls, 0.033 * ls)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.012, SKIN)
        fd.add(Sphere(pts[0] - n * 0.012, 0.016), 0.01, SKIN)                     # knuckle
        # nail on the back of the last segment
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.012, (0.014, 0.008, 0.016),
                           R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
        tips.append(pts[3])
    # thumb
    tb = wr + f * 0.045 + t * 0.052 + n * 0.012
    if fist:
        d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
        d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:
        d1 = norm(f * 0.55 + t * 0.75 + n * 0.25)
        d2 = norm(f * 0.8 + t * 0.35 + n * 0.45)
    p1 = tb + d1 * 0.05
    p2 = p1 + d2 * 0.042
    fd.add(Chain([tb, p1, p2], [0.026, 0.023, 0.02], k=0.008), 0.02, SKIN)
    back = norm(np.cross(d2, curl_ax)) if fist else -n
    fd.paint(Ellipsoid(p2 - d2 * 0.008 - back * 0.012, (0.015, 0.008, 0.017), R=rot_from_axes(z_axis=d2, y_axis=back)), NAIL)
    return wr + f * 0.1 + n * 0.035


def foot(fd, side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.12)
    fwd = Rz @ v3((0, -1, 0))
    rgt = Rz @ v3((1, 0, 0))
    fd.add(Sphere(an + v3((0, 0.045, -0.05)), 0.062), 0.03, SKIN)                      # heel
    fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.068)), (0.074, 0.12, 0.038), 0.036, R=Rz), 0.035, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.04 + v3((0, 0, -0.03)), (0.07, 0.09, 0.05), R=Rz), 0.03, SKIN)  # instep
    inner = -sx
    toes = [(0.055, 0.031), (0.022, 0.023), (-0.006, 0.021), (-0.031, 0.019), (-0.052, 0.017)]
    for i, (o, r) in enumerate(toes):
        base = an + fwd * (0.17 - 0.012 * i - (0.0 if i else -0.004)) + rgt * (o * inner) + v3((0, 0, -0.077))
        tip = base + fwd * (0.03 + r * 0.4) + v3((0, 0, -0.004))
        base[2] = 0.025 + r * 0.55
        tip[2] = 0.02 + r * 0.5
        fd.add(RoundCone(base, tip, r, r * 0.92), 0.012, SKIN)
        tn = norm(tip - base)
        fd.paint(Ellipsoid(tip + v3((0, 0, r * 0.55)), (r * 0.7, r * 0.75, r * 0.35), R=rot_from_axes(y_axis=tn, z_axis=(0, 0, 1))), NAIL)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.055, 0.0, 0.0)), 0.026), 0.02, SKIN)              # ankle bones


# ======================================================================================= head
# the head is designed at 1.0 and scaled up about the top of the neck (bigger head = more charm, reads from above)
HS = 1.13
HPIV = v3((0.0, 0.02, 1.52))


def hp(p):
    return HPIV + (v3(p) - HPIV) * HS


def hr(r):
    return r * HS


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.185, 0.195, 0.19)) * HS
EYE_R = hr(0.037)


def eye_c(sx):
    return hp((sx * 0.071, -0.152, 1.676))


def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)                                         # cranium
    fd.add(E((0, -0.05, 1.585), (0.183, 0.152, 0.135)), 0.07, SKIN)                         # jaw mass
    fd.add(E((0, -0.125, 1.505), (0.125, 0.082, 0.074)), 0.05, SKIN)                        # chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.125, 1.628), 0.062), 0.045, SKIN)                         # cheekbones
        fd.add(S((sx * 0.138, -0.045, 1.545), 0.07), 0.05, SKIN)                           # jaw corners
        # heavy brow: a shelf that follows the curve of the forehead and melts into the temples
        pts = [hp((sx * 0.155, -0.045, 1.742)), hp((sx * 0.118, -0.128, 1.748)), hp((sx * 0.06, -0.178, 1.745)), hp((0.0, -0.19, 1.748))]
        fd.add(Chain(pts, [hr(0.02), hr(0.036), hr(0.043), hr(0.045)], k=hr(0.03)), hr(0.045), SKIN)
    fd.add(E((0, -0.17, 1.775), (0.075, 0.04, 0.05)), hr(0.04), SKIN)                       # glabella / forehead bump
    # bushy brows sculpted onto the shelf (inner ends low = stern), painted as hair
    for sx in (-1, 1):
        pts = [hp((sx * 0.02, -0.226, 1.758)), hp((sx * 0.062, -0.214, 1.772)), hp((sx * 0.105, -0.188, 1.784)), hp((sx * 0.145, -0.15, 1.788)),
               hp((sx * 0.165, -0.125, 1.794))]
        brow = Chain(pts, [hr(0.02), hr(0.024), hr(0.022), hr(0.016), hr(0.005)], k=hr(0.012),
                     disp=lambda P: F(0.0025) * NOISE(P * np.array([30, 30, 90], F)), disp_amp=0.003)
        fd.add(brow, hr(0.012), BROW)
        fd.paint(Chain(pts, [hr(0.026), hr(0.03), hr(0.028), hr(0.021), hr(0.009)], k=hr(0.012)), BROW)
    # eye sockets + lids (stern but awake)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0085)), Plane(ec + v3((0, 0, hr(0.013))), (sx * 0.22, 0.12, -1.0)), hr(0.004))
        fd.add(up, hr(0.006), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0065)), Plane(ec + v3((0, 0, -hr(0.024))), (sx * -0.12, 0.1, 1.0)), hr(0.004))
        fd.add(lo, hr(0.006), SKIN)
    # nose
    fd.add(RoundCone(hp((0, -0.19, 1.712)), hp((0, -0.235, 1.628)), hr(0.03), hr(0.04)), hr(0.02), SKIN)
    fd.add(S((0, -0.248, 1.604), 0.058), hr(0.02), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.047, -0.217, 1.587), 0.033), hr(0.016), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.025, -0.238, 1.565)), v3((0.012, 0.016, 0.009)) * HS, R=euler(0.4, 0, sx * 0.3)), hr(0.006))
    # big toothy grin: a curved slot (corners up) framed by lips
    slot = [hp((-0.092, -0.165, 1.548)), hp((-0.05, -0.198, 1.522)), hp((0, -0.212, 1.514)), hp((0.05, -0.198, 1.522)), hp((0.092, -0.165, 1.548))]
    fd.sub(Chain(slot, [hr(0.012), hr(0.02), hr(0.022), hr(0.02), hr(0.012)], k=hr(0.01)), hr(0.008))
    fd.paint(Chain(slot, [hr(0.012), hr(0.02), hr(0.023), hr(0.02), hr(0.012)], k=hr(0.01)), MOUTH)
    up_lip = [(-0.095, -0.158, 1.556), (-0.05, -0.198, 1.543), (0, -0.215, 1.538), (0.05, -0.198, 1.543), (0.095, -0.158, 1.556)]
    lo_lip = [(-0.085, -0.163, 1.528), (-0.045, -0.194, 1.502), (0, -0.205, 1.495), (0.045, -0.194, 1.502), (0.085, -0.163, 1.528)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.009), hr(0.013), hr(0.014), hr(0.013), hr(0.009)], k=hr(0.01)), hr(0.008), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.008), hr(0.011), hr(0.012), hr(0.011), hr(0.008)], k=hr(0.01)), hr(0.008), LIP)
    # ears
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.183, 0.035, 1.665)), v3((0.03, 0.054, 0.07)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.205, 0.022, 1.668)), v3((0.014, 0.034, 0.044)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))


# ======================================================================================= body
def body_parts(fd):
    fd.add(Ellipsoid((0, 0.05, 1.19), (0.30, 0.25, 0.29), R=euler(-0.14, 0, 0)), 0, SKIN)   # ribcage
    fd.add(Ellipsoid((0, 0.13, 1.24), (0.32, 0.19, 0.22)), 0.06, SKIN)                      # back / lats
    for sx in (-1, 1):
        fd.add(Ellipsoid((sx * 0.135, -0.155, 1.272), (0.15, 0.065, 0.098), R=euler(0.1, 0, sx * 0.18)), 0.045, SKIN)  # pecs
    fd.add(Ellipsoid((0, -0.03, 0.975), (0.265, 0.25, 0.232)), 0.08, SKIN)                # belly
    fd.add(Ellipsoid((0, 0.045, 0.80), (0.255, 0.205, 0.17)), 0.08, SKIN)                  # pelvis
    fd.add(Ellipsoid((0, 0.11, 1.42), (0.27, 0.15, 0.10), R=euler(0.26, 0, 0)), 0.06, SKIN)  # traps
    fd.add(RoundCone((0, 0.07, 1.38), hp((0, 0.02, 1.575)), 0.13, hr(0.105)), 0.05, SKIN)         # neck
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(Sphere(sh + v3((sx * 0.025, -0.005, 0.015)), 0.145), 0.06, SKIN)            # deltoid
        fd.add(RoundCone(sh, el, 0.12, 0.09), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.03, 0)), (0.108, 0.112, 0.152), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)   # biceps
        fd.add(RoundCone(el, wr, 0.086, 0.066), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.01, 0, 0)), (0.116, 0.102, 0.158), R=rot_from_axes(z_axis=wr - el)), 0.045, SKIN)  # forearm
        fd.add(Sphere(el + v3((0, 0.03, 0)), 0.07), 0.03, SKIN)                            # elbow
        hand(fd, side, fist=(side == "R"))
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.15, 0.098), 0.07, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.025, 0)), (0.138, 0.128, 0.2), R=rot_from_axes(z_axis=kn - hip)), 0.05, SKIN)  # quads
        fd.add(Sphere(kn + v3((0, -0.035, 0.0)), 0.078), 0.04, SKIN)                       # kneecap
        fd.add(RoundCone(kn, an, 0.094, 0.062), 0.04, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.035, 0)), (0.108, 0.105, 0.155), R=rot_from_axes(z_axis=an - kn)), 0.045, SKIN)  # calf
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
    n = 8
    for i in range(n):
        u = (i - (n - 1) / 2) / ((n - 1) / 2)
        x = u * 0.072
        y = -0.21 + 0.036 * u * u
        z = 1.523 + 0.02 * u * u
        w = 0.0098 if abs(u) < 0.35 else 0.0088
        h = 0.0135 if abs(u) < 0.35 else 0.0118
        fd.add(RoundBox(hp((x, y, z)), v3((w, 0.008, h)) * HS, hr(0.0045), R=euler(0.12, 0, -u * 0.62)), 0.0)
    for i in range(4):
        u = (i - 1.5) / 1.5
        x = u * 0.03
        fd.add(RoundBox(hp((x, -0.196 + 0.012 * u * u, 1.497)), v3((0.0085, 0.007, 0.009)) * HS, hr(0.004), R=euler(-0.1, 0, -u * 0.4)), 0.0)
    for sx in (-1, 1):
        fd.add(RoundCone(hp((sx * 0.05, -0.188, 1.493)), hp((sx * 0.056, -0.197, 1.528)), hr(0.011), hr(0.004)), 0.0)   # lower tusks
    return fd



# ======================================================================================= helpers
def ray_hit(field, origins, dirs, tmax=0.8, step=0.002):
    """First surface hit of each ray (rays start outside). Returns (points, hit_mask)."""
    o = np.atleast_2d(np.asarray(origins, dtype=np.float64))
    d = np.atleast_2d(np.asarray(dirs, dtype=np.float64))
    d = d / np.linalg.norm(d, axis=1, keepdims=True)
    ts = np.arange(0.0, tmax, step)
    P = o[:, None, :] + d[:, None, :] * ts[None, :, None]
    vals = np.asarray(field.eval(P.reshape(-1, 3).astype(F)) if isinstance(field, Field) else field(P.reshape(-1, 3).astype(F))).reshape(len(o), len(ts))
    inside = vals < 0
    has = inside.any(1)
    i1 = np.argmax(inside, axis=1)
    i0 = np.maximum(i1 - 1, 0)
    v0 = vals[np.arange(len(o)), i0]
    v1 = vals[np.arange(len(o)), i1]
    t = ts[i0] + (ts[i1] - ts[i0]) * np.clip(v0 / np.maximum(v0 - v1, 1e-9), 0, 1)
    return o + d * t[:, None], has


def clump(root, d0, length, r0, r_tip=0.004, bend=(0, 0, -1), bend_amt=0.5, segs=4, curl_axis=None, curl=0.0, jitter=0.0, rng=None, k=None):
    pts, rads = [v3(root)], [r0]
    d = norm(d0)
    p = v3(root)
    bend = v3(bend)
    for i in range(segs):
        t = (i + 1) / segs
        d = norm(d + bend * bend_amt / segs + (rng.normal(0, jitter, 3) if rng is not None and jitter else 0))
        if curl and curl_axis is not None:
            d = axis_angle(curl_axis, curl / segs) @ d
        p = p + d * length / segs
        pts.append(p)
        rads.append(r0 + (r_tip - r0) * t ** 0.85)
    return Chain(pts, rads, k=r0 * 0.35 if k is None else k)


class Stone(Prim):
    """Chiselled stone: a squashed sphere cut by random planes (soft edges) plus a little noise."""

    def __init__(self, c, r, seed=0, cuts=8, squash=(1.0, 1.0, 0.82), soft=0.18, depth=(0.72, 0.92), R=None, noise=0.0, **kw):
        rs = np.random.RandomState(seed)
        R = R if R is not None else euler(*rs.uniform(0, 6.28, 3))
        super().__init__(c, R, disp_amp=noise * r, **kw)
        self.r = r
        self.sq = v3(squash)
        n = rs.normal(size=(cuts, 3))
        self.n = (n / np.linalg.norm(n, axis=1, keepdims=True)).astype(F)
        self.o = (rs.uniform(depth[0], depth[1], cuts) * r).astype(F)
        self.k = soft * r
        self.noise = noise
        self.seed = seed
        e = r * self.sq.max()
        self.bounds_from_local((-e,) * 3, (e,) * 3)

    def sdf(self, P):
        q = self.local(P) / self.sq.astype(F)
        d = np.sqrt((q * q).sum(1)) - F(self.r)
        for n, o in zip(self.n, self.o):
            d = smax(d, q @ n - o, self.k)
        d = d * F(self.sq.min())
        if self.noise:
            d = d + F(self.noise * self.r) * NOISE((P + self.seed * 3.7) * F(4.5 / self.r))
        return d


# ======================================================================================= hair & beard
class Lock(Prim):
    """A flattened, tapering lock of hair along a polyline: a smooth chain of oriented ellipsoids.
    `normals` give the flat direction (usually the surface normal it lies on)."""

    def __init__(self, pts, widths, thicks, normals, k=None, overlap=1.45, **kw):
        super().__init__(**kw)
        pts = [v3(p) for p in pts]
        self.parts = []
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            t = norm(b - a)
            n = v3(normals[i]) + v3(normals[i + 1])
            n = norm(n - t * (n @ t))
            bvec = np.cross(t, n)
            R = np.stack([bvec, n, t], axis=1)
            w = 0.5 * (widths[i] + widths[i + 1])
            th = 0.5 * (thicks[i] + thicks[i + 1])
            L = np.linalg.norm(b - a) * 0.5 * overlap
            self.parts.append(Ellipsoid((a + b) / 2, (max(w, 1e-3), max(th, 1e-3), max(L, w * 0.6)), R=R))
        self.k = (min(widths[:-1]) * 0.6) if k is None else k
        self.lo = np.min([p.lo for p in self.parts], 0) - self.k - self.disp_amp
        self.hi = np.max([p.hi for p in self.parts], 0) + self.k + self.disp_amp

    def sdf(self, P):
        d = None
        for p in self.parts:
            b = p.sdf(P)
            d = b if d is None else smin(d, b, self.k)
        return d


def grad(field, P, h=1e-3):
    P = np.atleast_2d(np.asarray(P, dtype=F))
    g = np.zeros_like(P)
    for i in range(3):
        e = np.zeros(3, F)
        e[i] = h
        g[:, i] = (field.eval(P + e) - field.eval(P - e)) / (2 * h)
    return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)


def project_to(field, P, iters=3):
    P = np.atleast_2d(np.asarray(P, dtype=np.float64))
    for _ in range(iters):
        d = field.eval(P.astype(F)).astype(np.float64)
        g = grad(field, P).astype(np.float64)
        P = P - g * d[:, None]
    return P


def flow_line(field, start, flow, steps, step, depth=0.0):
    """Trace a curve over a surface following a flow direction function p->dir (tangent-projected)."""
    p = project_to(field, [start])[0]
    out = [p]
    for i in range(steps):
        n = grad(field, [p])[0].astype(np.float64)
        d = v3(flow(p, i))
        d = d - n * (d @ n)
        if np.linalg.norm(d) < 1e-6:
            break
        q = project_to(field, [p + norm(d) * step])[0]
        if np.linalg.norm(q - p) > 2.5 * step or abs(float(field.eval(q[None].astype(F))[0])) > 0.01:
            break
        p = q
        out.append(p)
    return [q - grad(field, [q])[0] * depth for q in out]


def surface_lock(field, root, flow, length, w0, t0, segs=5, lift=0.0, tip_w=0.1, tip_curl=None, rng=None):
    """A lock that lies on `field` (following `flow`), lifting off the surface toward its tip.
    Width tapers smoothly to a point; the tip never bulges."""
    line = flow_line(field, root, flow, segs, length / segs)
    pts, ws, ts, ns = [], [], [], []
    for i, p in enumerate(line):
        u = i / max(1, len(line) - 1)
        n = grad(field, [p])[0].astype(np.float64)
        q = p + n * (t0 * 0.3 + lift * u * u)
        if tip_curl is not None:
            q = q + v3(tip_curl) * (u ** 3) * length * 0.25
        pts.append(q)
        ws.append(w0 * max(tip_w, 1 - 0.92 * u ** 1.35))
        ts.append(t0 * max(0.18, 1 - 0.78 * u))
        ns.append(n)
    return Lock(pts, ws, ts, ns)


def head_hull():
    """Head + neck + chest only (fast surface for tracing hair/beard locks)."""
    fd = Field("HeadHull")
    head(fd)
    fd.add(RoundCone((0, 0.07, 1.38), hp((0, 0.02, 1.575)), 0.13, hr(0.105)), 0.05)
    fd.add(Ellipsoid((0, 0.04, 1.19), (0.35, 0.31, 0.34), R=euler(-0.14, 0, 0)), 0.06)     # chest + pelt thickness
    return fd


def fib_points(n):
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        a = i * math.pi * (3 - math.sqrt(5))
        out.append(v3((r * math.cos(a), r * math.sin(a), z)))
    return out


def poisson_pick(cands, min_d, limit, rng):
    rng.shuffle(cands)
    picked = []
    for c in cands:
        if all(np.linalg.norm(c[0] - p[0]) >= min_d for p in picked):
            picked.append(c)
        if len(picked) >= limit:
            break
    return picked


def fan_lock(hull, start, heading, length, w_max, t0, segs=8, gravity=0.0, lift=0.0, tip_up=0.0, grooves=2, fd=None, rng=None, thin_root=False):
    """A big lock that starts at `start` and sweeps over `hull` along `heading` (bending down with gravity).
    Width swells from the root to ~40% then tapers to a point; grooves carve sub-strands along it."""
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
        # grooves: thin channels along the lock (sub-strands)
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


def hair_field(skin=None, seed=3):
    rng = np.random.RandomState(seed)
    fd = Field("Hair")
    hc, hrad = HEAD_C, HEAD_RAD
    pfront, pback = hp((0, -0.165, 1.80)), hp((0, 0.22, 1.585))
    slope = (pback[2] - pfront[2]) / (pback[1] - pfront[1])
    hl_n = norm((0, slope, -1.0))
    hairline = Func(lambda P: ((P - pfront.astype(F)) @ hl_n.astype(F)) + F(0.01) * NOISE(P * F(26)), hc - 0.5, hc + 0.5)
    fd.add(Inter(Ellipsoid(hc, hrad + 0.016), hairline, 0.02), 0.0)          # scalp layer
    hull = Field("HairHull")
    hull.add(Ellipsoid(hc, hrad + 0.02), 0.0)
    hull.add(Ellipsoid(hp((0, 0.15, 1.67)), v3((0.195, 0.13, 0.2)) * HS), hr(0.08))
    crown = hc + v3((0, 0.05, hrad[2] * 0.97))
    # layer 1: a fan of big locks from the crown
    n1 = 17
    for i in range(n1):
        a = 2 * math.pi * i / n1 + rng.uniform(-0.06, 0.06)
        hd = v3((math.sin(a), -math.cos(a), 0.0))        # a=0 -> toward the face
        frontness = max(0.0, math.cos(a))
        backness = max(0.0, -math.cos(a))
        L = hr(0.27 + 0.18 * backness + 0.06 * (1 - frontness - backness) - 0.09 * frontness ** 2) + rng.uniform(0, 0.02)
        start = crown + hd * 0.03
        fan_lock(hull, start, hd, L, hr(0.105 if frontness < 0.7 else 0.09), hr(0.036), segs=9,
                 gravity=0.25 + 0.9 * (1 - frontness), lift=hr(0.03 + 0.015 * frontness), tip_up=hr(0.012 * frontness),
                 grooves=2, fd=fd, rng=rng)
    # layer 2: underneath, longer at the back and sides, fills the edge and makes it ragged
    n2 = 13
    for i in range(n2):
        a = math.pi * (0.3 + 1.4 * (i + 0.5) / n2) + rng.uniform(-0.05, 0.05)
        hd = v3((math.sin(a), -math.cos(a), 0.0))
        o = hc + v3((0, 0.02, 0.02)) + hd * 0.5
        st, ok = ray_hit(hull, [o], [-hd], tmax=0.5)
        if not ok[0]:
            continue
        backness = max(0.0, -math.cos(a))
        L = hr(0.16 + 0.12 * backness) + rng.uniform(0, 0.02)
        fan_lock(hull, st[0], hd * 0.4 + v3((0, 0, -1)), L, hr(0.085), hr(0.03), segs=7, gravity=0.6,
                 lift=hr(0.035), tip_up=hr(0.015), grooves=1, fd=fd, rng=rng)
    # front layer: swept up and back from the hairline (covers the scalp above the brow)
    nf = 8
    for i in range(nf):
        u = -1 + 2 * (i + 0.5) / nf
        x = u * 0.15
        hz = pfront[2] + slope * (hp((0, -0.15 + 0.1 * u * u, 0))[1] - pfront[1])
        o = hp((x, -0.6, 0)) + v3((0, 0, hz - hp((0, 0, 0))[2] + hr(0.035)))
        st, ok = ray_hit(hull, [o], [v3((0, 1, 0))], tmax=0.8)
        if not ok[0]:
            continue
        hd = norm(v3((u * 0.5, 1.0, 0.0)))
        fan_lock(hull, st[0], hd, hr(0.16 + rng.uniform(0, 0.03)), hr(0.088), hr(0.032), segs=6, gravity=-0.25,
                 lift=hr(0.03), tip_up=hr(0.02), grooves=2, fd=fd, rng=rng, thin_root=True)
    return fd


def beard_field(skin, seed=5):
    rng = np.random.RandomState(seed)
    fd = Field("Beard")
    hull = head_hull()
    hull.add(Ellipsoid(hp((0, -0.15, 1.45)), v3((0.13, 0.08, 0.1)) * HS), hr(0.05))
    ctr = hp((0, -0.02, 1.57))
    # roots along a line from the sideburns, under the cheekbones, to under the lower lip
    def root_at(u):
        ax = abs(u) * 0.175
        z = 1.468 + 0.17 * (ax / 0.175) ** 1.8
        th = u * 1.75
        d = norm(v3((math.sin(th), -math.cos(th), 0.0)) * 1.0 + v3((0, 0, (z - 1.56) * 2.5)))
        o = hp((0, -0.02, z)) + d * 0.5
        h, ok = ray_hit(hull, [o], [-d], tmax=0.5)
        return h[0] if ok[0] else None
    nb = 15
    for i in range(nb):
        u = -1 + 2 * i / (nb - 1)
        r = root_at(u * 0.98)
        if r is None:
            continue
        front = 1 - abs(u)
        hd = v3((-u * 0.4, -0.22, -1.0))
        L = hr(0.15 + 0.1 * front ** 1.2) + rng.uniform(0, 0.015)
        fan_lock(hull, r + v3((0, 0, 0.008)), hd, L, hr(0.062 + 0.048 * front), hr(0.02 + 0.016 * front), segs=8, gravity=0.3,
                 lift=hr(0.02 + 0.05 * front ** 1.5), grooves=2, fd=fd, rng=rng, thin_root=True)
    # moustache: two heavy flat locks drooping past the corners of the grin
    for sx in (-1, 1):
        pts = [hp((sx * 0.004, -0.24, 1.565)), hp((sx * 0.05, -0.232, 1.562)), hp((sx * 0.104, -0.2, 1.552)), hp((sx * 0.145, -0.16, 1.515)),
               hp((sx * 0.162, -0.14, 1.47))]
        ns = [norm(v3((sx * 0.3, -1.0, 0.3)))] * 5
        fd.add(Lock(pts, [hr(0.02), hr(0.032), hr(0.032), hr(0.022), hr(0.003)], [hr(0.016), hr(0.02), hr(0.019), hr(0.014), hr(0.003)], ns,
                    k=hr(0.012)), hr(0.008))
        for g in (-0.25, 0.25):
            gp = [lerp(pts[j], pts[j + 1], 0.5) + v3((0, -0.012, g * 0.02)) for j in range(3)]
            fd.sub(Chain(gp, [hr(0.004)] * 3, k=0.002), hr(0.003))
    return fd


# ======================================================================================= clothing
def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.19), (0.30, 0.25, 0.29), R=euler(-0.14, 0, 0)), 0.0),
        (Ellipsoid((0, 0.13, 1.24), (0.32, 0.19, 0.22)), 0.06),
        (Ellipsoid((0.135, -0.155, 1.272), (0.15, 0.065, 0.098), R=euler(0.1, 0, 0.18)), 0.045),
        (Ellipsoid((-0.135, -0.155, 1.272), (0.15, 0.065, 0.098), R=euler(0.1, 0, -0.18)), 0.045),
        (Ellipsoid((0, -0.03, 0.975), (0.265, 0.25, 0.232)), 0.08),
        (Ellipsoid((0, 0.045, 0.80), (0.255, 0.205, 0.17)), 0.08),
    ]


def pelt_base():
    b = Field("PeltBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(Ellipsoid((0.0, 0.11, 1.42), (0.27, 0.15, 0.10), R=euler(0.26, 0, 0)), 0.06)   # traps
    sh, el = J["shoulder_L"], J["elbow_L"]
    b.add(Sphere(sh + v3((0.025, -0.005, 0.015)), 0.145), 0.06)                          # left deltoid
    b.add(RoundCone(sh, el, 0.12, 0.09), 0.05)
    b.add(RoundCone((0, 0.03, 0.93), (0, 0.035, 0.50), 0.285, 0.33), 0.08)               # skirt
    return b


def hem_cut(z0=0.565, amp=0.034, teeth=7, noise=0.016, axis=(0.0, 0.035)):
    ax = v3((axis[0], axis[1], 0))
    def fn(P):
        th = np.arctan2(P[:, 0] - F(ax[0]), -(P[:, 1] - F(ax[1])))
        x = th * F(teeth / (2 * math.pi))
        tri = F(2) * np.abs(F(2) * (x - np.floor(x + F(0.5)))) - F(1)
        hz = F(z0) + F(amp) * tri + F(noise) * NOISE(P * F(9))
        return hz - P[:, 2]
    return Func(fn, (-2, -2, -2), (2, 2, 5))


def pelt_field():
    fd = Field("Pelt")
    base = pelt_base()
    fur = lambda P: F(0.006) * NOISE(P * np.array([16, 16, 5], F)) + F(0.004) * NOISE(P * np.array([42, 42, 12], F) + 3) + F(0.0015) * NOISE(P * F(90))
    fd.add(Shell(base, 0.018, 0.046, disp=fur, disp_amp=0.012), 0.0)
    # one-shoulder cut (over the left shoulder, under the right arm), ragged edge
    n1 = norm((-0.78, 0.0, 1.0))
    c1 = v3((0.0, 0.05, 1.335))
    fd.inter(Func(lambda P: (P - c1.astype(F)) @ n1.astype(F) + F(0.012) * NOISE(P * F(22)), (-3, -3, -3), (3, 3, 3)), 0.006)
    # left sleeve edge
    sh, el = J["shoulder_L"], J["elbow_L"]
    n2 = norm(el - sh)
    c2 = sh + (el - sh) * 0.34
    def sleeve(P, c2=c2, n2=n2, sh=sh):
        d = (P - c2.astype(F)) @ n2.astype(F) + F(0.014) * NOISE(P * F(20) + 5)
        near = (P[:, 0] > F(sh[0] - 0.05)) & (P[:, 2] > F(sh[2] - 0.75))
        return np.where(near, d, F(-1.0))
    fd.inter(Func(sleeve, (-3, -3, -3), (3, 3, 3)), 0.006)
    fd.inter(hem_cut(), 0.006)
    # fur ankle wraps
    for side in ("R", "L"):
        kn, an = J["knee_" + side], J["ankle_" + side]
        calf = RoundCone(kn, an, 0.094, 0.062)
        wrap = Inter(Shell(calf, 0.016, 0.034, pad=0.06, disp=fur, disp_amp=0.01),
                     Func(lambda P, an=an: np.abs(P[:, 2] - F(an[2] + 0.075)) - F(0.05) + F(0.012) * NOISE(P * F(25)),
                          an - 0.2, an + 0.25), 0.004)
        fd.add(wrap, 0.0)
    return fd


def _forearm(side):
    return RoundCone(J["elbow_" + side], J["wrist_" + side], 0.086, 0.066)


def leather_field(skin, pelt):
    fd = Field("Leather")
    base = pelt_base()
    # belt riding on the pelt, slightly lower at the front
    belt = Inter(Shell(base, 0.042, 0.026, pad=0.1),
                 Func(lambda P: np.abs(P[:, 2] - (F(0.865) + F(0.08) * P[:, 1])) - F(0.036), (-1, -1, 0.6), (1, 1, 1.1)), 0.004)
    fd.add(belt, 0.0)
    # knot + hanging ends at the front left
    kp, _ = ray_hit(pelt, [v3((0.16, -0.7, 0.845))], [v3((0, 1, 0))], tmax=0.7)
    k0 = kp[0] + v3((0, -0.02, 0))
    fd.add(Ellipsoid(k0, (0.034, 0.024, 0.03)), 0.008)
    fd.add(Chain([k0, k0 + v3((-0.01, -0.02, -0.07)), k0 + v3((-0.022, -0.022, -0.15))], [0.013, 0.012, 0.01], k=0.01), 0.008)
    fd.add(Chain([k0, k0 + v3((0.02, -0.018, -0.06)), k0 + v3((0.03, -0.01, -0.12))], [0.013, 0.012, 0.01], k=0.01), 0.008)
    # wrist cuffs
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.84)
        fd.add(Inter(Shell(_forearm(side), 0.012, 0.016, pad=0.06),
                     Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.042), c - 0.2, c + 0.2), 0.004), 0.0)
        for j in (-1, 1):   # lacing ridges
            cc = c + ax * (j * 0.022)
            fd.add(Inter(Shell(_forearm(side), 0.019, 0.006, pad=0.06),
                         Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.006), cc - 0.2, cc + 0.2), 0.002), 0.003)
    # hide bag on the right hip, hanging from the belt
    bp, _ = ray_hit(pelt, [v3((-0.62, -0.42, 0.74))], [norm((0.55, 0.83, 0))], tmax=0.8)
    out = norm((-0.55, -0.83, 0))
    bc = bp[0] + out * 0.05
    bag_R = rot_from_axes(y_axis=out, z_axis=(0, 0, 1))
    fd.add(Ellipsoid(bc, (0.085, 0.055, 0.092), R=bag_R, disp=lambda P: F(0.003) * NOISE(P * F(30)), disp_amp=0.004), 0.0)
    fd.sub(Ellipsoid(bc + v3((0, 0, 0.085)), (0.06, 0.035, 0.03), R=bag_R), 0.01)      # open mouth
    fd.add(Torus(bc + v3((0, 0, 0.055)), 0.068, 0.009, R=bag_R @ euler(0, 0, 0)), 0.006)   # drawstring
    fd.add(Chain([bc + v3((0, 0, 0.06)) - out * 0.02, bc + v3((0.0, 0, 0.11)) - out * 0.04], [0.012, 0.012]), 0.008)  # strap to belt
    return fd, bc, bag_R


def bag_stones(bc, bag_R):
    fd = Field("BagStones")
    for i, (dx, dy, r) in enumerate(((-0.025, 0.0, 0.034), (0.022, 0.008, 0.03), (0.0, -0.012, 0.028))):
        fd.add(Stone(bc + bag_R @ v3((dx, dy, 0.0)) + v3((0, 0, 0.078 + 0.01 * i)), r, seed=40 + i, noise=0.05), 0.002)
    return fd


def necklace(skin, pelt):
    """Cord draped around the base of the neck, dipping to the front-right; fang + bone beads."""
    both = Func(lambda P: np.minimum(skin.eval(P), pelt.eval(P)), (-1, -1, 0.5), (1, 1, 2.0))
    ctr = v3((0.0, 0.06, 1.4))
    pts = []
    n = 28
    for i in range(n):
        a = 2 * math.pi * i / n
        dirv = v3((math.sin(a) * 0.82, -math.cos(a), 0.0))
        front = max(0.0, -dirv[1] * 0.85 - dirv[0] * 0.3)
        z = 1.47 - 0.2 * front ** 1.6
        o = v3((ctr[0], ctr[1], z)) + norm(dirv) * 0.6
        h, ok = ray_hit(both, [o], [-norm(dirv)], tmax=0.6)
        pts.append(h[0] + norm(dirv) * 0.009)
    pts.append(pts[0])
    cord = Field("Cord")
    cord.add(Chain(pts, [0.0075] * len(pts), k=0.004), 0.0)
    bone = Field("Bone")
    lo = min(range(n), key=lambda i: pts[i][2])
    p = pts[lo]
    out = norm(p - v3((ctr[0], ctr[1], p[2])))
    fang = [p + out * 0.006, p + v3((0, 0, -0.04)) + out * 0.02, p + v3((0.012, 0, -0.085)) + out * 0.024, p + v3((0.03, 0, -0.115)) + out * 0.022]
    bone.add(Chain(fang, [0.019, 0.017, 0.011, 0.003], k=0.01), 0.0)
    bone.add(Torus(p, 0.014, 0.005, R=rot_from_axes(z_axis=norm(pts[lo + 1] - pts[lo - 1]))), 0.004)
    for j in (-2, -1, 1, 2):
        q = pts[(lo + j) % n]
        tdir = norm(pts[(lo + j + 1) % n] - pts[(lo + j - 1) % n])
        bone.add(RoundCone(q - tdir * 0.014, q + tdir * 0.014, 0.011, 0.011), 0.0)
        bone.add(Sphere(q - tdir * 0.016, 0.0125), 0.004)
        bone.add(Sphere(q + tdir * 0.016, 0.0125), 0.004)
    hb0, hb1 = hp((-0.11, 0.08, 1.93)), hp((0.1, 0.02, 1.98))
    bone.add(RoundCone(hb0, hb1, 0.011, 0.011), 0.0)
    for q in (hb0, hb1):
        bone.add(Sphere(q, 0.018), 0.006)
    return cord, bone


# ======================================================================================= sling
def sling_points():
    """Rest pose: the sling hangs from the bottom of the right fist."""
    wr, f, n, t = hand_frame("R")
    fist = wr + f * 0.1 + n * 0.035
    attach = fist - t * 0.05 + v3((0, 0, -0.02))
    pouch = attach + v3((0, 0, -0.43))
    return fist, attach, pouch


def sling_field():
    fist, attach, pouch = sling_points()
    fd = Field("Sling")
    cup = Inter(Shell(Ellipsoid(pouch, (0.088, 0.062, 0.066)), 0.0, 0.011, pad=0.03),
                Plane(pouch + v3((0, 0, 0.012)), (0, 0, 1)), 0.004)
    fd.add(cup, 0.0)
    for sx in (-1, 1):
        rim = pouch + v3((sx * 0.083, 0, 0.008))
        mid = lerp(attach, rim, 0.5) + v3((sx * 0.004, 0, 0))
        fd.add(Chain([attach + v3((sx * 0.004, 0, 0)), mid, rim], [0.0065, 0.0065, 0.008], k=0.004), 0.003)
    fd.add(Sphere(attach + v3((0, 0, -0.005)), 0.014), 0.006)          # knot under the fist
    stone = Field("SlingStone")
    stone.add(Stone(pouch + v3((0, 0, 0.03)), 0.062, seed=11, noise=0.04), 0.0)
    return fd, stone


# ======================================================================================= painting
def warm_points():
    """Ruddy spots painted into the skin: nose, cheeks, ears, knuckles, elbows, knees, toes, sunburnt shoulders."""
    pts = [(hp((0, -0.248, 1.604)), 0.075, 0.95)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.105, -0.15, 1.6)), 0.065, 0.55), (hp((sx * 0.19, 0.03, 1.665)), 0.07, 0.75),
                (J["elbow_" + sd] + v3((0, 0.03, 0)), 0.08, 0.35),
                (J["knee_" + sd] + v3((0, -0.04, 0)), 0.09, 0.4),
                (J["shoulder_" + sd] + v3((0, 0, 0.11)), 0.13, 0.25)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.043, 0.0145, -0.0145, -0.043):
            pts.append((wr + f * 0.138 + t * o - n * 0.012, 0.035, 0.5))
        an = J["ankle_" + side]
        pts.append((an + v3((0, -0.17, -0.07)), 0.07, 0.5))
        pts.append((an + v3((0, 0.05, -0.07)), 0.06, 0.3))
    return pts


# ======================================================================================= build config (Rock Slinger)
GLB_NAME = "rock_slinger"
ROOT_NAME = "RockSlingerHQ"
TEX_PREFIX = "caveman"
MAT_NAME = "CavemanMat"
BASE_MODULE = "base"
ANIM_MODULE = "anim"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Pelt", "Leather", "BagStones", "Cord", "Bone", "Sling", "SlingStone"]
LOW_TARGETS = {"Skin": 6800, "Hair": 3000, "Beard": 1600, "Pelt": 2300, "Leather": 1100, "Teeth": 360, "Cord": 380,
               "Bone": 420, "Sling": 700, "SlingStone": 140, "BagStones": 200}
AO_EXCLUDE = ["Cord", "Bone", "Sling", "SlingStone", "BagStones", "Leather"]
TORSO = {"root", "spine", "chest", "neck"}


def weight_rules():
    return {
        "Pelt": ("transfer", TORSO | {"clavicle.L", "upperarm.L", "thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"},
                 {"thigh.R": 0.3, "thigh.L": 0.3, "upperarm.L": 0.85}),
        "Leather": ("transfer", TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "upperarm.R", "upperarm.L", "thigh.R"}, {"thigh.R": 0.3}),
        "Cord": ("transfer", TORSO | {"head"}, None),
        "Bone": ("transfer", TORSO | {"head"}, None),
        "BagStones": ("transfer", TORSO | {"thigh.R"}, {"thigh.R": 0.3}),
        "Hair": ("rigid", "head"), "Beard": ("rigid", "head"), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Sling": ("rigid", "sling"), "SlingStone": ("rigid", "stone"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Cord", "Sling", "Bone", "SlingStone", "BagStones"):
        return 0.6
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0:
        return 1.9
    if part == "Skin" and (abs(c.x) > 0.62 and c.z < 1.0):
        return 1.35
    return 1.0


def sculpt_parts(fine=True):
    """(name, field, voxel) for every high-poly part."""
    skin = skin_field()
    pelt = pelt_field()
    leather, bc, bagR = leather_field(skin, pelt)
    cord, bone = necklace(skin, pelt)
    sling, sstone = sling_field()
    return [
        ("Skin", skin, 0.0032 if fine else 0.005),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(skin), 0.003 if fine else 0.0035),
        ("Beard", beard_field(skin), 0.003 if fine else 0.0035),
        ("Pelt", pelt, 0.0035 if fine else 0.005),
        ("Leather", leather, 0.0025 if fine else 0.003),
        ("BagStones", bag_stones(bc, bagR), 0.002),
        ("Cord", cord, 0.0015 if fine else 0.002),
        ("Bone", bone, 0.0015 if fine else 0.002),
        ("Sling", sling, 0.0015 if fine else 0.002),
        ("SlingStone", sstone, 0.002),
    ]
