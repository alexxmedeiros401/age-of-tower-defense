"""The Druid (HQ tower, Iron Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

An old druid of the oak groves: tall and lean, a long hooked nose, deep-set eyes under great bushy white brows, a long
white beard falling in locks to the middle of his chest under a heavy moustache, long white hair flowing back from a
high bald brow to his shoulders, a wreath of oak leaves round his head with sprigs of mistletoe (white berries) at its
front. A long robe of undyed white wool to his ankles with wide sleeves and a green woven border; over his shoulders a
short green wool cape with its hood folded down on his back, pinned with a gold ring brooch; a twisted gold torc round
his neck; a rope belt with a golden sickle at his left hip; leather shoes. In his right fist a gnarled oak staff whose
head splits into three twisting branches holding a glowing green stone (the stone ships as its own glowing mesh, on the
`gem` bone), a sprig of mistletoe tied under it. His left hand is open (it calls the roots up).

The staff is rigid in his right fist ("frame" aims in anim_druid.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, grad, project_to, flow_line, Stone, lerp
from ugo import _blend_add

J = {
    "root": (0.0, 0.03, 0.84),
    "spine": (0.0, 0.03, 1.0),
    "chest": (0.0, 0.045, 1.2),
    "neck": (0.0, 0.055, 1.43),
    "head": (0.0, 0.02, 1.55),
    "head_end": (0.0, -0.02, 1.95),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.31, 0.06, 1.39)
    J["elbow_" + _s] = (_x * 0.5, 0.09, 1.13)
    J["wrist_" + _s] = (_x * 0.64, 0.03, 0.89)
    J["hip_" + _s] = (_x * 0.14, 0.04, 0.8)
    J["knee_" + _s] = (_x * 0.16, 0.0, 0.45)
    J["ankle_" + _s] = (_x * 0.17, 0.06, 0.11)
    J["toe_" + _s] = (_x * 0.19, -0.17, 0.035)
J = {k: v3(v) for k, v in J.items()}

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, SPOT = 0, 1, 2, 3, 4, 5, 8, 9

HS = 1.05
DZ = -0.01
HPIV = v3((0.0, 0.02, 1.49))


def hp(p):
    p = v3(p) + v3((0, 0, DZ))
    return HPIV + (p - HPIV) * HS


def hr(r):
    return r * HS


def hinv(P):
    return (P - HPIV.astype(F)) / F(HS) + HPIV.astype(F) - np.array([0, 0, DZ], F)


HEAD_C = hp((0.0, 0.03, 1.73))
HEAD_RAD = v3((0.17, 0.186, 0.184)) * HS
EYE_R = hr(0.032)


def eye_c(sx):
    return hp((sx * 0.068, -0.138, 1.674))        # deep-set under the brow


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


HAND_S = 0.98
CURLS = {"R": (1.45, 1.6, 1.2), "L": (0.25, 0.3, 0.2)}       # right fist round the staff, left hand open


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    """An old man's hand: long bony fingers, knuckles standing out."""
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    fist = side == "R"
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.058, 0.028, 0.065)) * s, 0.025 * s, R=Rp), 0.024, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.031, 0.026, 0.048)) * s, R=Rp), 0.017, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.04, 0.0135, -0.0135, -0.04)
    lens = (1.02, 1.1, 1.02, 0.86)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * (1.2 if fist else 2.0))
        pts, rads = [p], [0.0175 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.056 * ls * s, 0.046 * ls * s, 0.037 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 and fist else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.88)
        fd.add(Chain(pts, rads, k=0.005), 0.01, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.0145 * s), 0.008, SKIN)
        fd.add(Sphere(pts[1], rads[1] * 1.08), 0.004, SKIN)                                   # knobbly knuckles
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.01, (0.0105, 0.0065, 0.014), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.05 * s + n * 0.011
    if fist:
        d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
        d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    else:
        d1 = norm(f * 0.45 + t * 0.85 + n * 0.15)
        d2 = norm(f * 0.75 + t * 0.55 + n * 0.1)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.022 * s, 0.019 * s, 0.016 * s], k=0.007), 0.015, SKIN)


def foot(fd, side, s=1.02):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.1)
    fwd = Rz @ v3((0, -1, 0))
    fd.add(Sphere(an + v3((0, 0.042, -0.05)), 0.056 * s), 0.028, SKIN)
    fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.07)), v3((0.062, 0.116, 0.033)) * s, 0.031, R=Rz), 0.031, SKIN)
    fd.add(Ellipsoid(an + fwd * 0.036 + v3((0, 0, -0.03)), v3((0.06, 0.084, 0.046)) * s, R=Rz), 0.028, SKIN)
    for s2 in (-1, 1):
        fd.add(Sphere(an + v3((s2 * 0.05, 0.0, 0.0)), 0.023), 0.018, SKIN)


# ======================================================================================= head
def skull():
    fd = Field("Skull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    fd.add(Ellipsoid(hp((0, 0.02, 1.8)), v3((0.158, 0.17, 0.116)) * HS), 0.08)
    return fd


def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.8), (0.158, 0.17, 0.116)), 0.08, SKIN)                            # a high, domed, bald brow
    fd.add(E((0, -0.06, 1.585), (0.114, 0.12, 0.12)), 0.07, SKIN)                           # a long lean jaw (under the beard)
    fd.add(E((0, -0.138, 1.5), (0.068, 0.058, 0.066)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.108, -0.128, 1.646), 0.036), 0.045, SKIN)                          # high cheekbones
        fd.add(S((sx * 0.106, -0.04, 1.56), 0.035), 0.05, SKIN)
        pts = [hp((sx * 0.152, -0.055, 1.744)), hp((sx * 0.115, -0.132, 1.755)), hp((sx * 0.06, -0.176, 1.754)), hp((0.0, -0.186, 1.75))]
        fd.add(Chain(pts, [hr(0.012), hr(0.021), hr(0.025), hr(0.023)], k=hr(0.022)), hr(0.032), SKIN)     # heavy brow ridge
        fd.sub(Ellipsoid(hp((sx * 0.1, -0.136, 1.594)), v3((0.03, 0.017, 0.038)) * HS, R=euler(0, 0, sx * 0.4)), hr(0.02))   # sunken cheeks
        fd.sub(Ellipsoid(hp((sx * 0.148, -0.08, 1.735)), v3((0.02, 0.03, 0.03)) * HS), hr(0.02))                          # hollow temples
    sk = skull()
    # creases across the high forehead, two frown lines between the brows, crow's feet, bags under the eyes
    for zc, w in ((1.792, 0.075), (1.818, 0.085), (1.846, 0.08)):
        pts = []
        for k in range(9):
            x = -w + 2 * w * k / 8
            h, ok = ray_hit(sk, [hp((x, -0.6, zc + 0.014 * (x / w) ** 2 - 0.004 * math.cos(x * 30)))], [v3((0, 1, 0))], tmax=0.7)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 3:
            fd.sub(Chain(pts, [hr(0.0024)] * len(pts), k=0.002), hr(0.003))
    for sx in (-1, 1):
        fd.sub(RoundCone(hp((sx * 0.011, -0.2, 1.738)), hp((sx * 0.016, -0.198, 1.764)), hr(0.0018), hr(0.0016)), hr(0.003))
        for k in range(3):
            a = hp((sx * (0.11 + 0.004 * k), -0.128 + 0.006 * k, 1.68 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.024, 0.012, 0.006 - 0.01 * k)), hr(0.0021), hr(0.0014)), hr(0.003))
        fd.add(Ellipsoid(hp((sx * 0.07, -0.15, 1.646)), v3((0.026, 0.012, 0.011)) * HS), hr(0.012), SKIN)
    # great bushy white brows, tufting up and out at their outer ends
    brow_tuft = lambda P: F(0.003) * NOISE(P * F(160)) + F(0.0015) * np.sin(P[:, 0] * F(400))
    for sx in (-1, 1):
        pts = [hp((sx * 0.02, -0.214, 1.752)), hp((sx * 0.062, -0.21, 1.77)), hp((sx * 0.108, -0.192, 1.777)),
               hp((sx * 0.15, -0.155, 1.776)), hp((sx * 0.178, -0.118, 1.79))]
        fd.add(Chain([p + v3((0, -0.002, 0)) for p in pts], [hr(0.013), hr(0.017), hr(0.017), hr(0.013), hr(0.006)], k=hr(0.009),
                     disp=brow_tuft, disp_amp=0.004), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.024), hr(0.028), hr(0.027), hr(0.022), hr(0.012)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.011))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)                                                            # heavy, hooded lids
        lo = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, -hr(0.019))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0085))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
    # a long hooked nose
    fd.add(RoundCone(hp((0, -0.186, 1.728)), hp((0, -0.25, 1.622)), hr(0.016), hr(0.022)), hr(0.016), SKIN)
    fd.add(S((0, -0.222, 1.69), 0.019), hr(0.012), SKIN)
    fd.add(S((0, -0.25, 1.612), 0.024), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.028, -0.218, 1.6), 0.018), hr(0.011), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.015, -0.234, 1.589)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the mouth, under the moustache: a thin old mouth, the lower lip showing
    slot = [hp((-0.05, -0.168, 1.548)), hp((-0.026, -0.19, 1.542)), hp((0, -0.196, 1.541)), hp((0.026, -0.19, 1.542)), hp((0.05, -0.168, 1.548))]
    fd.sub(Chain(slot, [hr(0.0022), hr(0.003), hr(0.0033), hr(0.003), hr(0.0022)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.003)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.042, -0.168, 1.54), (-0.022, -0.185, 1.531), (0, -0.189, 1.529), (0.022, -0.185, 1.531), (0.042, -0.168, 1.54)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0065), hr(0.007), hr(0.0065), hr(0.004)], k=hr(0.006)), hr(0.008), LIP)
    # big ears (the hair falls behind them)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.177, 0.032, 1.655)), v3((0.028, 0.052, 0.07)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.196, 0.026, 1.66)), v3((0.012, 0.033, 0.045)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
    # age spots on the bald brow
    rs = np.random.RandomState(5)
    for k in range(7):
        x, z = rs.uniform(-0.1, 0.1), rs.uniform(1.8, 1.9)
        h, ok = ray_hit(sk, [hp((x, -0.6, z))], [v3((0, 1, 0))], tmax=0.7)
        if ok[0]:
            fd.paint(Sphere(h[0], hr(rs.uniform(0.006, 0.011))), SPOT)


# ======================================================================================= body (lean, old)
def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.2), (0.23, 0.19, 0.25), R=euler(-0.1, 0, 0)), 0.0),
        (Ellipsoid((0, 0.115, 1.25), (0.26, 0.14, 0.18)), 0.06),
        (Ellipsoid((0.105, -0.12, 1.28), (0.105, 0.048, 0.072), R=euler(0.1, 0, 0.18)), 0.045),
        (Ellipsoid((-0.105, -0.12, 1.28), (0.105, 0.048, 0.072), R=euler(0.1, 0, -0.18)), 0.045),
        (Ellipsoid((0, 0.0, 1.0), (0.18, 0.16, 0.19)), 0.08),
        (Ellipsoid((0, 0.045, 0.84), (0.2, 0.165, 0.15)), 0.08),
    ]


def traps():
    return Ellipsoid((0, 0.09, 1.42), (0.2, 0.12, 0.08), R=euler(0.26, 0, 0))


def neck_prim():
    return RoundCone((0, 0.055, 1.38), hp((0, 0.02, 1.575)), 0.084, hr(0.078))


def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.02, -0.005, 0.012)), 0.09)


def upper_arm(side):
    return RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.08, 0.06)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.05, SKIN)
        fd.add(upper_arm(side), 0.045, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.02, 0)), (0.07, 0.072, 0.11), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(RoundCone(el, wr, 0.058, 0.044), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.07, 0.063, 0.115), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.022, 0)), 0.048), 0.025, SKIN)
        fd.add(Sphere(wr + v3((sx * 0.012, 0.0, 0.006)), 0.03), 0.02, SKIN)                      # bony wrist
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.115, 0.078), 0.06, SKIN)
        fd.add(Sphere(kn + v3((0, -0.028, 0.0)), 0.06), 0.035, SKIN)
        fd.add(RoundCone(kn, an, 0.07, 0.048), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.028, 0)), (0.078, 0.075, 0.125), R=rot_from_axes(z_axis=an - kn)), 0.04, SKIN)
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
        fd.add(RoundBox(hp((sx * 0.009, -0.176, 1.547)), v3((0.008, 0.006, 0.007)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= hair and beard
def hair_hull():
    hull = Field("HairHull")
    hull.add(Ellipsoid(HEAD_C, HEAD_RAD + v3((0.018, 0.024, 0.018))), 0.0)
    hull.add(Ellipsoid(hp((0, 0.02, 1.8)), v3((0.158, 0.17, 0.116)) * HS + 0.018), 0.08)
    hull.add(Ellipsoid(hp((0, 0.1, 1.56)), v3((0.19, 0.13, 0.19)) * HS), 0.08)                   # falling behind his neck
    hull.add(Ellipsoid(v3((0, 0.12, 1.43)), (0.23, 0.12, 0.08)), 0.07)                          # lying on his shoulders
    return hull


def hair_field():
    """Long white hair from a high bald brow: swept back over the crown, behind his ears (they stand clear), falling to
    his shoulders and spreading on them in loose locks."""
    fd = Field("Hair")
    hull = hair_hull()
    def strands(P):
        a = np.arctan2(P[:, 0], P[:, 1] - F(0.05))
        return (F(0.0032) * np.sin(a * F(46) + P[:, 2] * F(14)) + F(0.0018) * np.sin(a * F(110))
                + F(0.0014) * NOISE(P * np.array([60, 60, 10], F)))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        # the hairline: far back over the bald dome, sweeping down behind the temples and the ears
        line = F(-0.035) + F(0.075) * smoothstep(1.86, 1.66, z) * smoothstep(0.06, 0.16, ax)
        line = np.where(ax < F(0.11), F(-0.01) + F(0.05) * smoothstep(1.9, 1.78, z), line)
        front = line - y
        ear = np.where((ax > F(0.15)) & (z < F(1.74)), F(0.052) - y, F(-1.0))                  # behind the ears
        ragged = F(0.025) * np.sin(x * F(38)) + F(0.012) * np.sin(x * F(91) + F(1.3))
        bottom = (F(1.385) + ragged + F(0.06) * smoothstep(0.06, -0.04, y)) - P[:, 2]
        return np.maximum(np.maximum(front, ear), bottom)
    fd.add(Inter(Shell(hull, 0.0, 0.036, pad=0.08, disp=strands, disp_amp=0.005), Func(keep, HEAD_C + v3((-0.45, -0.4, -0.5)), HEAD_C + 0.35), 0.005), 0.0)
    # a few loose locks over his shoulders
    lk = lambda P: F(0.0018) * NOISE(P * np.array([70, 70, 14], F))
    for sx in (-1, 1):
        for k, (dx, L) in enumerate(((0.16, 0.16), (0.21, 0.13))):
            a = v3((sx * dx, 0.1, 1.52))
            pts = [a, a + v3((sx * 0.025, 0.0, -L * 0.5)), a + v3((sx * 0.04, 0.012, -L))]
            fd.add(Lock(pts, [0.026, 0.024, 0.012], [0.011, 0.01, 0.006], [v3((sx, 0.3, 0))] * 3, k=0.006, disp=lk, disp_amp=0.002), 0.01)
    return fd


def beard_hull():
    fd = Field("BeardHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.06, 1.585), (0.114, 0.12, 0.12)), 0.07)
    fd.add(E((0, -0.138, 1.5), (0.068, 0.058, 0.066)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.108, -0.128, 1.646)), hr(0.036)), 0.045)
        fd.add(Sphere(hp((sx * 0.106, -0.04, 1.56)), hr(0.035)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


def beard_tex(P):
    """Long wavy locks running down the beard; positive pushes the surface in."""
    x, z = P[:, 0], P[:, 2]
    ph = x / F(0.026) + F(0.45) * np.sin(z * F(26) + x * F(7))
    lock = np.abs(np.sin(ph * F(math.pi)))
    return F(0.003) - F(0.006) * lock * lock + F(0.0013) * NOISE(P * np.array([90, 90, 22], F))


BEARD_TIP = v3((0.0, -0.212, 1.17))


def beard_field():
    """A long white beard: full round his jaw and up his cheeks to the hair, falling in wavy locks from his chin down
    over his chest to a point; a heavy moustache drooping into it."""
    fd = Field("Beard")
    hull = beard_hull()
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.56) + F(0.1) * smoothstep(0.05, 0.14, ax)                             # up the cheeks
        top = np.where(ax > F(0.15), F(1.72), top)                                      # sideburns into the hair
        lips = (x / F(0.062)) ** 2 + ((y + F(0.178)) / F(0.07)) ** 2 + ((z - F(1.543)) / F(0.024)) ** 2 - F(1.0)
        back = np.where(ax > F(0.13), y - F(0.03), y - F(0.0))
        return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), F(1.44) - z)
    fd.add(Inter(Shell(hull, 0.008, 0.026, pad=0.06, disp=beard_tex, disp_amp=0.008), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.008), 0.0)
    # the long fall over his chest: flattened lobes, narrowing to the point
    for c, r in (((0, -0.168, 1.47), (0.122, 0.066, 0.07)), ((0, -0.198, 1.38), (0.11, 0.05, 0.09)),
                 ((0, -0.21, 1.29), (0.08, 0.042, 0.085)), ((0, -0.212, 1.21), (0.04, 0.032, 0.06))):
        fd.add(Ellipsoid(v3(c), r, disp=beard_tex, disp_amp=0.008), 0.045)
    # stray locks at its edges and the point
    lk = lambda P: F(0.0018) * NOISE(P * np.array([80, 80, 20], F))
    for sx in (-1, 1):
        a = v3((sx * 0.09, -0.19, 1.42))
        pts = [a, a + v3((sx * 0.012, -0.008, -0.08)), a + v3((sx * 0.004, -0.01, -0.15))]
        fd.add(Lock(pts, [0.024, 0.02, 0.008], [0.011, 0.009, 0.005], [v3((0, -1, 0))] * 3, k=0.006, disp=lk, disp_amp=0.002), 0.01)
    fd.add(Lock([BEARD_TIP + v3((0.0, 0.0, 0.06)), BEARD_TIP + v3((0.004, -0.004, -0.0)), BEARD_TIP + v3((0.012, -0.006, -0.05))],
                [0.022, 0.016, 0.005], [0.012, 0.01, 0.005], [v3((0, -1, 0))] * 3, k=0.006, disp=lk, disp_amp=0.002), 0.012)
    # the moustache: two heavy locks from under the nose, drooping past his mouth into the beard
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.222, 1.58)), hp((sx * 0.046, -0.21, 1.566)), hp((sx * 0.074, -0.19, 1.532)),
               hp((sx * 0.086, -0.18, 1.47))]
        fd.add(Lock(pts, [hr(0.016), hr(0.022), hr(0.018), hr(0.01)], [hr(0.012), hr(0.014), hr(0.011), hr(0.007)],
                    [norm(v3((sx * 0.3, -1, 0.15)))] * 4, k=hr(0.006), disp=strands, disp_amp=0.003), hr(0.006))
    return fd


# ======================================================================================= the wreath
WREATH_Z = 1.83         # the wreath's height at the front (design units); it dips at the back


def wreath_d(P):
    Q = hinv(P)
    return Q[:, 2] - (F(WREATH_Z) - F(0.09) * smoothstep(-0.15, 0.2, Q[:, 1]))


def _leaf_sd(P, c, u, v, n, L, W):
    """An oak leaf: a flat blade along u (half length L), lobed edges (half width W at most), on the plane (u, v)."""
    q = P - c.astype(F)
    s = q @ u.astype(F)
    t = q @ v.astype(F)
    h = q @ n.astype(F)
    k = np.clip(s / F(L), -1, 1)
    w = F(W) * np.sqrt(np.maximum(F(1) - k * k, 0)) * (F(0.72) + F(0.28) * np.cos(k * F(math.pi * 4.5)))
    curl = F(0.006) * (s / F(L)) ** 2                                  # its tip curls up off the wreath a little
    d = np.maximum(np.abs(t) - w, np.abs(s) - F(L))
    return np.maximum(d, np.abs(h - curl) - F(0.0028))


def wreath_off(P):
    """How far out from the hair hull the wreath sits: on the bald brow in front, on the hair behind."""
    return F(-0.006) + F(0.03) * smoothstep(-0.12, 0.02, hinv(P)[:, 1])


def wreath_surf(hull, extra=0.0):
    return Func(lambda P: hull.eval(P, margin=0.06) - wreath_off(P) - F(extra), HEAD_C - 0.5, HEAD_C + 0.5)


def wreath_points(n=20):
    """(centre, along, normal) of the leaves round the wreath: each leaf pointing back along the ring and tilted out
    from it, alternately higher and lower."""
    hull = hair_hull()
    surf = wreath_surf(hull, 0.01)
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        dirh = v3((math.sin(a), -math.cos(a), 0.0))
        z = WREATH_Z - 0.09 * (0.5 - 0.5 * math.cos(a)) * 1.0 + (0.012 if k % 2 else -0.012)
        o = hp((0, 0.03, z)) + dirh * 0.6
        h, ok = ray_hit(surf, [o], [-dirh], tmax=0.6)
        if not ok[0]:
            continue
        c = h[0]
        tang = v3((math.cos(a), math.sin(a), 0.0))                     # round the head (clockwise from above)
        out_n = norm(dirh + v3((0, 0, 0.35 if k % 2 else -0.1)))
        u = norm(tang * (1 if k % 2 else -1) + v3((0, 0, 0.25)))
        out.append((c, u, out_n))
    return out


MISTLETOE = [(-0.07, 0.0), (0.0, 0.025), (0.07, 0.0)]                 # sprigs at the wreath's front (design x, lift)


def wreath_field():
    """A wreath of oak leaves on a ring of twigs (label 7); at its front three sprigs of mistletoe: pairs of narrow
    yellow-green leaves (6) and white berries (5)."""
    fd = Field("Wreath")
    hull = hair_hull()
    ring = Func(lambda P: np.abs(wreath_d(P)) - F(0.009), HEAD_C - 0.4, HEAD_C + 0.4)
    band = Func(lambda P: np.abs(hull.eval(P, margin=0.06) - wreath_off(P)) - F(0.007), HEAD_C - 0.5, HEAD_C + 0.5)
    fd.add(Inter(band, ring, 0.003), 0.0, 7)
    for c, u, n in wreath_points():
        v = norm(np.cross(n, u))
        fd.add(Func(lambda P, c=c, u=u, v=v, n=n: _leaf_sd(P, c, u, v, n, 0.046, 0.022), c - 0.06, c + 0.06), 0.003, 0)
    rs = np.random.RandomState(11)
    for x, lift in MISTLETOE:
        o = hp((x, -0.6, WREATH_Z + 0.01 + lift))
        h, ok = ray_hit(wreath_surf(hull, 0.012), [o], [v3((0, 1, 0))], tmax=0.7)
        if not ok[0]:
            continue
        c = h[0] + v3((0, -0.006, 0.004))
        for j in range(5):                                              # berries
            a = 2 * math.pi * j / 5 + rs.uniform(-0.3, 0.3)
            p = c + v3((math.cos(a) * 0.012, -0.006 + math.sin(a) * 0.004, math.sin(a) * 0.01))
            fd.add(Sphere(p, 0.0075), 0.002, 5)
        for sd in (-1, 1):                                              # a pair of narrow leaves
            d = norm(v3((sd * 0.8, -0.2, 0.55)))
            mid = c + d * 0.024
            nn = norm(np.cross(d, v3((0, 1, 0))))
            fd.add(Ellipsoid(mid, (0.022, 0.009, 0.003), R=rot_from_axes(x_axis=d, z_axis=v3((0, -1, 0.2)))), 0.003, 6)
    return fd


# ======================================================================================= robe, cape, belt
def robe_base():
    b = Field("RobeBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        b.add(deltoid(side), 0.05)
        b.add(upper_arm(side), 0.045)
        b.add(RoundCone(el, wr - norm(wr - el) * 0.02, 0.068, 0.098), 0.04)               # wide sleeves, flaring
    b.add(RoundCone((0, 0.03, 0.9), (0, 0.035, 0.12), 0.2, 0.3), 0.09)                    # to his ankles
    return b


def hem_z(P):
    return F(0.125) + F(0.008) * NOISE(P * F(7))


def _cuff(P, side):
    """Cuts the sleeve off a little short of the wrist, square to the forearm."""
    el, wr = J["elbow_" + side], J["wrist_" + side]
    n = norm(wr - el)
    c = wr - n * 0.035
    d = (P - c.astype(F)) @ n.astype(F)
    sx = -1 if side == "R" else 1
    return np.where((P[:, 0] * F(sx) > F(0.3)) & (P[:, 2] > F(0.7)), d, F(-1.0))


def robe_field():
    """A long robe of undyed white wool with wide sleeves; a green woven border at the hem and the cuffs (label 5), a
    gold-brown stripe above it (6). Deep folds down the skirt."""
    fd = Field("Robe")
    base = robe_base()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        k = smoothstep(0.95, 0.6, P[:, 2])
        return F(0.006) * np.sin(a * F(11) + F(0.6) * np.sin(a * F(3))) * k + F(0.0014) * NOISE(P * F(30))
    def keep(P):
        neck = P[:, 2] - (F(1.47) + F(0.3) * smoothstep(0.14, 0.21, np.abs(P[:, 0])))
        k = np.maximum(hem_z(P) - P[:, 2], neck)
        return np.maximum(np.maximum(k, _cuff(P, "R")), _cuff(P, "L"))
    fd.add(Inter(Shell(base, 0.02, 0.018, pad=0.1, disp=folds, disp_amp=0.007), Func(keep, (-1, -1, 0.0), (1, 1, 1.7)), 0.005), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (hem_z(P) + F(0.06)), (-1, -1, 0.0), (1, 1, 0.4)), 5)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - (hem_z(P) + F(0.08))) - F(0.008), (-1, -1, 0.0), (1, 1, 0.4)), 6)
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        n = norm(wr - el)
        c = wr - n * 0.035
        fd.paint(Func(lambda P, c=c, n=n: np.where(np.abs(P[:, 0]) > F(0.3), F(-0.06) - (P - c.astype(F)) @ n.astype(F), F(1.0)),
                      c - 0.25, c + 0.25), 5)
    return fd


def cape_base():
    b = Field("CapeBase")
    for p, k in torso_prims()[:4]:
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.05)
        b.add(upper_arm(side), 0.045)
    b.add(neck_prim(), 0.05)
    return b


def cape_hem(P):
    """The cape's lower edge: mid-back behind, rising toward the front, over the upper arms."""
    y = P[:, 1]
    return F(1.1) + F(0.13) * smoothstep(0.05, -0.15, y) + F(0.01) * NOISE(P * F(9))


def cape_field():
    """A short cape of green wool over his shoulders, open down the front (under his beard), a gold zigzag border (5) at
    its edge; its hood folded down on his back."""
    fd = Field("Cape")
    base = cape_base()
    cloth = lambda P: F(0.004) * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(0.05)) * F(9)) * smoothstep(1.35, 1.15, P[:, 2]) + F(0.0012) * NOISE(P * F(30))
    def keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        ax = np.abs(x)
        lower = cape_hem(P) - z
        neck = z - (F(1.5) + F(0.25) * smoothstep(0.13, 0.2, ax))
        opening = np.where(y < F(-0.02), (F(0.1) + F(0.05) * smoothstep(1.42, 1.2, z)) - ax, F(-1.0))
        return np.maximum(np.maximum(lower, neck), opening)
    shell = Shell(base, 0.05, 0.02, pad=0.1, disp=cloth, disp_amp=0.005)
    fd.add(Inter(shell, Func(keep, (-0.8, -0.6, 0.9), (0.8, 0.6, 1.75)), 0.006), 0.0)
    def border(P):
        ax = np.abs(P[:, 0])
        hem = np.abs(P[:, 2] - cape_hem(P)) - F(0.032)
        edge = np.where(P[:, 1] < F(-0.02), np.abs(ax - F(0.1) - F(0.05) * smoothstep(1.42, 1.2, P[:, 2])) - F(0.026), F(1.0))
        return np.minimum(hem, edge)
    fd.paint(Func(border, (-0.8, -0.6, 0.9), (0.8, 0.6, 1.75)), 5)
    # the hood, folded down on his back: a thick roll of cloth, its opening scooped up
    h, ok = ray_hit(Func(lambda P: base.eval(P, margin=0.1) - F(0.07), (-1, -1, 0.9), (1, 1, 1.8)), [v3((0.0, 0.8, 1.37))], [v3((0, -1, 0))], tmax=0.9)
    hc = (h[0] if ok[0] else v3((0.0, 0.3, 1.37))) + v3((0.0, 0.035, 0.0))
    fd.add(Ellipsoid(hc, (0.15, 0.06, 0.1), R=euler(-0.25, 0, 0), disp=cloth, disp_amp=0.004), 0.03)
    fd.sub(Ellipsoid(hc + v3((0, 0.012, 0.065)), (0.11, 0.04, 0.07), R=euler(-0.25, 0, 0)), 0.02)
    return fd


def cape_point(x, z, extra=0.0):
    """A point on the cape's outer surface in front, at (x, z) (a ray from the front)."""
    base = cape_base()
    o = v3((x, -0.8, z))
    h, ok = ray_hit(Func(lambda P: base.eval(P, margin=0.1) - F(0.06 + extra), (-1, -1, 0.9), (1, 1, 1.8)), [o], [v3((0, 1, 0))], tmax=0.9)
    return h[0] if ok[0] else o




def belt_field():
    """A rope belt round his waist, knotted at the front with its ends hanging, tasselled."""
    fd = Field("Belt")
    base = robe_base()
    rope = lambda P: F(0.0018) * np.sin(np.arctan2(P[:, 0], P[:, 1]) * F(70) + P[:, 2] * F(260))
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(0.93)) - F(0.012), (-0.4, -0.36, 0.86), (0.4, 0.4, 1.0)),
                 Shell(base, 0.04, 0.024, pad=0.1, disp=rope, disp_amp=0.002), 0.004), 0.0)
    p, _ = ray_hit(Func(lambda P: base.eval(P) - F(0.05), (-1, -1, 0.5), (1, 1, 1.3)), [v3((0.06, -0.7, 0.93))], [v3((0, 1, 0))], tmax=0.8)
    k0 = p[0] + v3((0, -0.012, 0))
    fd.add(Sphere(k0, 0.024, disp=rope, disp_amp=0.002), 0.006)
    for k, dx in enumerate((-0.012, 0.022)):
        pts = [k0 + v3((dx * 0.5, -0.004, -0.015)), k0 + v3((dx, -0.014, -0.16)), k0 + v3((dx * 1.4, -0.016, -0.3 + 0.05 * k))]
        fd.add(Chain(pts, [0.0105, 0.0105, 0.0105], k=0.004, disp=rope, disp_amp=0.0015), 0.004)
        tip = pts[-1]
        fd.add(RoundCone(tip, tip + v3((0, -0.002, -0.06)), 0.013, 0.018, disp=lambda P: F(0.003) * np.sin(np.arctan2(P[:, 0], P[:, 1]) * F(30)),
                         disp_amp=0.003), 0.005)
    return fd


def robe_point(o, d, extra=0.0):
    """A point on the robe's outer surface (its body: the arms and sleeves left out), along the ray o + t d."""
    base = Field("RobeBody")
    for p_, k in torso_prims():
        base.add(p_, k)
    base.add(RoundCone((0, 0.03, 0.9), (0, 0.035, 0.12), 0.2, 0.3), 0.09)
    h, ok = ray_hit(Func(lambda P: base.eval(P, margin=0.1) - F(0.03 + extra), (-1, -1, 0.0), (1, 1, 1.8)), [v3(o)], [norm(v3(d))], tmax=0.9)
    return h[0] if ok[0] else v3(o)


def gold_field():
    """A twisted gold torc round his neck with round terminals at the front; the ring brooch pinning his cape; the golden
    sickle hanging from his belt at his left hip."""
    fd = Field("Gold")
    # the torc: a twisted ring round the neck, open at the front under the beard
    c0 = v3((0.0, 0.045, 1.425))
    def torc(P):
        q = P - c0.astype(F)
        a = np.arctan2(q[:, 0], -q[:, 1])
        r = np.sqrt((q[:, 0] / F(1.0)) ** 2 + (q[:, 1] / F(1.1)) ** 2)
        R = F(0.112)
        tube = np.sqrt((r - R) ** 2 + (q[:, 2] - F(0.012) * np.cos(a)) ** 2)
        twist = F(0.0025) * np.sin(a * F(36) + q[:, 2] * F(200))
        gap = F(0.35) - np.abs(a)
        return np.maximum(tube - F(0.0115) + twist, gap * F(0.11))
    fd.add(Func(torc, c0 - 0.2, c0 + 0.2), 0.0)
    for sx in (-1, 1):
        a = 0.35 * sx
        p = c0 + v3((math.sin(a) * 0.112, -math.cos(a) * 0.112 * 1.1, 0.012 * math.cos(a)))
        fd.add(Sphere(p, 0.019), 0.006)
    # the ring brooch: a penannular ring with knobbed ends and its pin across, on the cape's front edge
    BROOCH = cape_point(-0.125, 1.33, extra=0.012)
    N = norm(v3((0.25, -1.0, 0.12)))
    Rr = rot_from_axes(z_axis=N, y_axis=v3((0, 0, 1)))
    fd.add(Torus(BROOCH, 0.033, 0.006, R=Rr), 0.0)
    for s_ in (-1, 1):
        fd.add(Sphere(BROOCH + Rr @ v3((s_ * 0.012, -0.031, 0.0)), 0.009), 0.003)
    fd.add(RoundCone(BROOCH + Rr @ v3((0.0, 0.04, 0.004)), BROOCH + Rr @ v3((0.004, -0.05, 0.004)), 0.0035, 0.0022), 0.002)
    # the sickle: a slim crescent blade on a short handle, hanging by a loop from the belt
    ax = norm(v3((0.15, -0.3, -1.0)))
    side = norm(np.cross(ax, v3((1, 0, 0))))
    hb = robe_point((0.8, -0.08, 0.88), (-1, 0, 0), extra=0.03)
    he = hb + ax * 0.08
    fd.add(Chain([hb, he], [0.012, 0.011], k=0.0), 0.0)
    fd.add(Torus(hb - ax * 0.01, 0.014, 0.004, R=rot_from_axes(z_axis=side)), 0.003)
    pts = []
    for k in range(9):
        t = k / 8
        ang = math.pi * 0.95 * t
        pts.append(he + ax * (0.06 * math.sin(ang)) + side * (0.075 * (1 - math.cos(ang))) + ax * 0.004)
    rad = [0.009 * (1 - 0.8 * (k / 8) ** 1.5) + 0.0015 for k in range(9)]
    blade = Chain(pts, rad, k=0.004)
    nb = norm(np.cross(ax, side))
    fd.add(Inter(blade, Func(lambda P, c=he, nb=nb: np.abs((P - c.astype(F)) @ nb.astype(F)) - F(0.0028), he - 0.2, he + 0.2), 0.001), 0.002)
    return fd


def leather_field():
    """Plain shoes of soft leather, laced at the instep."""
    fd = Field("Leather")
    for side in ("R", "L"):
        ft = Field("FootHull")
        foot(ft, side)
        an = J["ankle_" + side]
        fd.add(Inter(Shell(ft, 0.008, 0.012, pad=0.05), Func(lambda P, an=an: P[:, 2] - F(an[2] + 0.02), an - 0.3, an + 0.3), 0.004), 0.0)
        sx = -1 if side == "R" else 1
        fwd = euler(0, 0, sx * 0.1) @ v3((0, -1, 0))
        fd.add(Chain([an + fwd * 0.03 + v3((sx * 0.04, 0, -0.005)), an + fwd * 0.07 + v3((0, 0, -0.03)),
                      an + fwd * 0.03 + v3((-sx * 0.04, 0, -0.005))], [0.004, 0.004, 0.004], k=0.0), 0.003)
    return fd


# ======================================================================================= the staff
STAFF_R = 0.022
STAFF_BACK = 1.04         # grip -> the butt
CROWN_S = 0.6             # grip -> where the shaft splits into its three branches
GEM_S = 0.7               # grip -> the stone's centre
GEM_R = 0.048


def staff_axis():
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t


def staff_frame():
    """The staff's axis and two directions across it (the knuckles' side first)."""
    a0, ax = staff_axis()
    wr, f, n, t = hand_frame("R")
    u = norm(f - ax * (f @ ax))
    w = np.cross(ax, u)
    return a0, ax, u, w


def staff_field():
    """Gnarled oak (bark, label 0): a crooked shaft with knots and burrs, splitting at its head into three branches that
    twist up round the stone and curl in over it; a cord binding (7) under the head; worn smooth (5) where he grips it."""
    fd = Field("Staff")
    a0, ax, u, w = staff_frame()
    bark = lambda P: F(0.003) * NOISE(P * np.array([60, 60, 60], F)) + F(0.0015) * NOISE(P * F(150))
    def bend(s):
        return u * (0.012 * math.sin(s * 5.0 + 0.4)) + w * (0.01 * math.sin(s * 3.7 + 1.1))
    pts, rads = [], []
    for k in range(13):
        s = -STAFF_BACK + (CROWN_S + STAFF_BACK) * k / 12
        pts.append(a0 + ax * s + bend(s))
        rads.append(STAFF_R * (1.08 - 0.12 * (k / 12)))
    fd.add(Chain(pts, rads, k=0.006, disp=bark, disp_amp=0.004), 0.0)
    rs = np.random.RandomState(3)
    for k in range(6):                                                     # knots and burrs
        s = rs.uniform(-0.9, 0.5)
        if -0.08 < s < 0.08:
            continue
        a = rs.uniform(0, 2 * math.pi)
        d = u * math.cos(a) + w * math.sin(a)
        fd.add(Ellipsoid(a0 + ax * s + bend(s) + d * STAFF_R * 0.85, (0.016, 0.016, 0.022), R=rot_from_axes(z_axis=ax), disp=bark, disp_amp=0.003), 0.01)
    fd.add(Sphere(a0 - ax * STAFF_BACK + bend(-STAFF_BACK), STAFF_R * 1.05, disp=bark, disp_amp=0.003), 0.008)
    fd.paint(Func(lambda P: np.abs((P - a0.astype(F)) @ ax.astype(F)) - F(0.07), a0 - 0.2, a0 + 0.2), 5)
    # the cord binding under the head
    top = a0 + ax * CROWN_S + bend(CROWN_S)
    for k in range(4):
        fd.add(Torus(top - ax * (0.05 + 0.011 * k), STAFF_R * 0.95 + 0.003, 0.0045, R=rot_from_axes(z_axis=ax)), 0.002, 7)
    # three branches twisting up round the stone, curling in over it
    gem = a0 + ax * GEM_S
    for b in range(3):
        a = 2 * math.pi * b / 3 + 0.4
        bp = []
        for k in range(8):
            t = k / 7
            ang = a + 1.3 * t
            d = u * math.cos(ang) + w * math.sin(ang)
            r_out = STAFF_R * 0.4 + (GEM_R + 0.012) * math.sin(math.pi * min(1.0, t * 0.95)) ** 0.8
            h = CROWN_S + (GEM_S - CROWN_S + GEM_R * 1.25) * t
            bp.append(a0 + ax * h + d * r_out - d * (0.02 * max(0.0, t - 0.75) / 0.25))
        rr = [STAFF_R * 0.55 * (1 - 0.65 * k / 7) + 0.003 for k in range(8)]
        fd.add(Chain(bp, rr, k=0.004, disp=bark, disp_amp=0.002), 0.012)
    return fd


def gem_field():
    """The glowing green stone in the staff's crown (its own glowing mesh)."""
    fd = Field("Gem")
    a0, ax, u, w = staff_frame()
    c = a0 + ax * GEM_S
    fd.add(Ellipsoid(c, (GEM_R * 0.9, GEM_R * 0.9, GEM_R * 1.15), R=rot_from_axes(z_axis=ax, x_axis=u),
                     disp=lambda P: F(0.003) * NOISE(P * F(40)), disp_amp=0.003), 0.0)
    return fd


def sprig_field():
    """A sprig of mistletoe tied under the staff's head: forked twigs (label 7), pairs of narrow yellow-green leaves (6),
    a cluster of white berries (5)."""
    fd = Field("Sprig")
    a0, ax, u, w = staff_frame()
    base = a0 + ax * (CROWN_S - 0.07) + w * (STAFF_R + 0.004)
    rs = np.random.RandomState(9)
    for k, (du, dw, L) in enumerate(((0.5, 0.8, 0.09), (-0.5, 0.8, 0.08), (0.0, 1.0, 0.1))):
        d = norm(u * du + w * dw - ax * 0.55)
        tip = base + d * L
        fd.add(Chain([base, tip], [0.004, 0.003], k=0.0), 0.002, 7)
        for sd in (-1, 1):
            ld = norm(d + norm(np.cross(d, ax)) * sd * 0.9)
            fd.add(Ellipsoid(tip + ld * 0.022, (0.024, 0.009, 0.0032), R=rot_from_axes(x_axis=ld, z_axis=norm(np.cross(ld, d)) * sd)), 0.002, 6)
        for j in range(3):
            fd.add(Sphere(tip + v3(rs.uniform(-0.008, 0.008, 3)), 0.0075), 0.002, 5)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.62)), 0.04, 0.6)]                                    # a reddened nose
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.1, -0.14, 1.61)), 0.05, 0.4), (hp((sx * 0.176, 0.035, 1.66)), 0.05, 0.55),
                (J["elbow_" + sd] + v3((0, 0.022, 0)), 0.05, 0.3), (J["knee_" + sd] + v3((0, -0.028, 0)), 0.06, 0.3)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.04, 0.0135, -0.0135, -0.04):
            pts.append((wr + f * 0.138 + t * o - n * 0.012, 0.028, 0.5))
    return pts


# ======================================================================================= build config
GLB_NAME = "druid"
ROOT_NAME = "DruidHQ"
TEX_PREFIX = "druid"
MAT_NAME = "DruidMat"
MESH_NAME = "Druid"
BASE_MODULE = "druid_base"
ANIM_MODULE = "anim_druid"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Wreath", "Robe", "Cape", "Belt", "Gold", "Leather", "Staff", "Sprig", "Gem"]
REGION_PARTS = ("Skin", "Robe", "Cape", "Beard", "Staff")
WHITE = {"base": (0.86, 0.85, 0.82), "hi": (1.0, 1.0, 0.98), "low": (0.5, 0.5, 0.48), "streak": (0.72, 0.71, 0.68),
         "tint": (0.9, 0.88, 0.82)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_DruidSkin", "base": (0.82, 0.6, 0.5), "ruddy": (0.86, 0.48, 0.42), "lips": (0.62, 0.38, 0.35),
                      "brow": ((0.8, 0.79, 0.75), (0.97, 0.96, 0.93)),
                      "extra": ((LASH, (0.78, 0.76, 0.72), 0.6), (SPOT, (0.62, 0.42, 0.3), 0.6, 0.5))}),
    "Hair": ("hair", dict(name="HQ_DruidHair", **WHITE)),
    "Beard": ("hair", dict(name="HQ_DruidHair", **WHITE)),
    "Wreath": ("leafy", {"name": "HQ_Leafy"}),
    "Sprig": ("leafy", {"name": "HQ_Leafy"}),
    "Robe": ("wool", {"name": "HQ_DruidRobe", "base": (0.88, 0.86, 0.78), "border": (0.24, 0.44, 0.2), "stripe": (0.62, 0.48, 0.22)}),
    "Cape": ("wool", {"name": "HQ_DruidCape", "base": (0.17, 0.32, 0.15), "border": (0.78, 0.62, 0.26), "stripe": (0.1, 0.18, 0.08)}),
    "Belt": ("cord", {}),
    "Gold": ("gold", {"name": "HQ_DruidGold"}),
    "Leather": ("leather", {"name": "HQ_DruidLeather", "base": (0.38, 0.24, 0.13)}),
    "Staff": ("bark_wood", {"name": "HQ_DruidStaff", "bark": (0.3, 0.22, 0.14), "wood": (0.62, 0.48, 0.32)}),
    "Gem": ("glow_ball", {"name": "HQ_DruidGem", "col": (0.5, 1.0, 0.45)}),
}
GLOW = {"Gem": ((0.45, 1.0, 0.4), 1.0, 0.55)}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Hair": 1800, "Beard": 1800, "Wreath": 1600, "Robe": 2600, "Cape": 1500, "Belt": 500,
               "Gold": 700, "Leather": 500, "Staff": 1400, "Sprig": 300, "Gem": 240}
AO_EXCLUDE = ["Staff", "Gem", "Sprig"]
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.76, 0.92, 1.1, 1.47)


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.94), (0, 0.04, 1.15)),
        "chest": ((0, 0.04, 1.15), (0, 0.055, 1.4)),
        "neck": ((0, 0.055, 1.4), hp((0, 0.02, 1.57))),
        "head": (hp((0, 0.02, 1.57)), hp((0, 0.0, 1.95))),
        "clavicle_z": 1.4,
    }


def prop_bones():
    a0, ax, u, w = staff_frame()
    c = a0 + ax * GEM_S
    return [("gem", c, c + ax * 0.1, "hand.R")]


def _seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
    return float(np.linalg.norm(a + ab * t - p))


def hair_weights(ob, skin_ob, arm):
    """The hair rides his head; its fall onto his shoulders blends into the neck and chest (so a turn of the head doesn't
    sweep it through his back)."""
    groups = {}
    for v in ob.data.vertices:
        z = v.co.z
        k = min(1.0, max(0.0, (z - 1.4) / 0.22))
        k = k * k * (3 - 2 * k)
        w = {"head": k}
        if k < 1.0:
            w["neck"] = (1 - k) * 0.55
            w["chest"] = (1 - k) * 0.45
        _blend_add(ob, groups, v.index, w)


def beard_weights(ob, skin_ob, arm):
    """The beard rides his jaw (the head); its long fall blends into the neck and the chest it lies on."""
    groups = {}
    for v in ob.data.vertices:
        z = v.co.z
        k = min(1.0, max(0.0, (z - 1.24) / 0.24))
        k = k * k * (3 - 2 * k)
        w = {"head": max(k, 0.0)}
        if k < 1.0:
            w["neck"] = (1 - k) * 0.4
            w["chest"] = (1 - k) * 0.6
        _blend_add(ob, groups, v.index, w)


def gold_weights(ob, skin_ob, arm):
    """The torc rides his neck, the brooch his chest, the sickle his left thigh a little."""
    groups = {}
    for v in ob.data.vertices:
        p = np.array(v.co)
        if p[2] > 1.38 and abs(p[0]) < 0.17:
            w = {"neck": 0.6, "chest": 0.4}
        elif p[2] > 1.2:
            w = {"chest": 1.0}
        else:
            w = {"root": 0.6, "thigh.L": 0.4}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Wreath": ("rigid", "head"),
        "Hair": ("custom", hair_weights), "Beard": ("custom", beard_weights),
        "Robe": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L", "thigh.R",
                                      "thigh.L", "shin.R", "shin.L"},
                 {"thigh.R": 0.4, "thigh.L": 0.4, "shin.R": 0.3, "shin.L": 0.3}),
        # (no cap on the upper arms: a capped cape lagged the arm and the robe's sleeve came out through it when he
        # held his hand out)
        "Cape": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"}, None),
        "Belt": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.3, "thigh.L": 0.3}),
        "Gold": ("custom", gold_weights),
        "Leather": ("transfer", {"foot.R", "foot.L", "shin.R", "shin.L"}, None),
        "Staff": ("rigid", "hand.R"), "Sprig": ("rigid", "hand.R"), "Gem": ("rigid", "gem"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Beard", "Wreath"):
        return 1.2
    if part == "Staff":
        return 0.6
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Beard", beard_field(), 0.0022 if fine else 0.0032),
        ("Wreath", wreath_field(), 0.0014 if fine else 0.002),
        ("Robe", robe_field(), 0.0028 if fine else 0.0038),
        ("Cape", cape_field(), 0.0026 if fine else 0.0036),
        ("Belt", belt_field(), 0.0018 if fine else 0.0026),
        ("Gold", gold_field(), 0.0014 if fine else 0.002),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Staff", staff_field(), 0.0018 if fine else 0.0026),
        ("Sprig", sprig_field(), 0.0012 if fine else 0.0018),
        ("Gem", gem_field(), 0.0016 if fine else 0.0022),
    ]
