"""Cassia the Legate, Legion Commander (HQ hero, Classical Age). Rest pose = A-pose, facing -Y, feet at z = 0; right
side = -X.

A tall woman in her prime who leads from the front: level dark brows, a straight Roman nose, a firm mouth, a small white
scar on her chin; black hair drawn back tight into a knot at her nape. A bronze officer's helmet: a polished bowl with
a gold brow-band rising to a peak over her forehead, hinged cheek pieces edged in gold, a short neck guard, and a tall
crest of red horsehair set across it from ear to ear. A moulded bronze cuirass with a gold gorgon's head on her breast,
a red sash (the legate's) knotted at her waist, white leather strips (pteruges) at her shoulders and in two rows below
the cuirass, fringed in gold, over a red tunic; a red cloak pinned at her right shoulder with a gold brooch, falling
behind her to her calves; bronze greaves; sandals laced up her calves. A gladius in her right fist (a steel blade, a
gold guard and an eagle's-head pommel); on her left arm an oval shield, red, a gold eagle with spread wings and a
laurel wreath round its edge, a bronze rim and a gold boss.

She has Kira's build (kira.py) with both hands made fists (Brenna's, brenna.py); the gladius and the shield are rigid
in her fists ("frame" aims in anim_cassia.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import kira as kr
import brenna as br
from kira import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S, foot,
                  fist_center, torso_prims, traps, neck_prim, deltoid, upper_arm, _forearm, eyes_field, teeth_field, TORSO,
                  TORSO_Z, torso_bones, kilt_base, bodice_base, _bodice_arm)
from brenna import hand, leg_prims, shield_frame

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH = 0, 1, 2, 3, 4, 5, 8
SCAR = 10


# ======================================================================================= head
def head(fd):
    """Level brows a little drawn down, steady eyes, a straight Roman nose with a slight bump, a firm level mouth, a
    strong chin with a small scar."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.06, 1.594), (0.142, 0.132, 0.126)), 0.07, SKIN)
    fd.add(E((0, -0.133, 1.503), (0.077, 0.066, 0.064)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.11, -0.118, 1.636), 0.042), 0.05, SKIN)
        fd.add(S((sx * 0.118, -0.05, 1.562), 0.047), 0.05, SKIN)
        pts = [hp((sx * 0.15, -0.06, 1.744)), hp((sx * 0.115, -0.13, 1.75)), hp((sx * 0.062, -0.164, 1.748))]
        fd.add(Chain(pts, [hr(0.011), hr(0.016), hr(0.014)], k=hr(0.02)), hr(0.03), SKIN)
    for sx in (-1, 1):
        pts = [hp((sx * 0.032, -0.202, 1.75)), hp((sx * 0.072, -0.197, 1.762)), hp((sx * 0.112, -0.175, 1.766)), hp((sx * 0.148, -0.135, 1.761))]
        fd.add(Chain([p + v3((0, 0.008, 0)) for p in pts], [hr(0.0055), hr(0.0072), hr(0.006), hr(0.003)], k=hr(0.006)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.013), hr(0.015), hr(0.013), hr(0.007)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0058)), Plane(ec + v3((0, 0, hr(0.014))), (sx * 0.2, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0044)), Plane(ec + v3((0, 0, -hr(0.024))), (sx * -0.12, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.008)), Plane(ec + v3((0, 0, hr(0.011))), (sx * 0.2, 0.05, -1.0)), hr(0.002)), LASH)
    fd.add(RoundCone(hp((0, -0.18, 1.724)), hp((0, -0.222, 1.642)), hr(0.013), hr(0.017)), hr(0.016), SKIN)
    fd.add(S((0, -0.2, 1.69), 0.015), hr(0.01), SKIN)                                                # the bump on the bridge
    fd.add(S((0, -0.222, 1.632), 0.021), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.024, -0.203, 1.619), 0.015), hr(0.01), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.012, -0.216, 1.608)), v3((0.007, 0.009, 0.005)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    slot = [hp((-0.055, -0.167, 1.552)), hp((-0.029, -0.189, 1.548)), hp((0, -0.195, 1.547)), hp((0.029, -0.189, 1.548)),
            hp((0.055, -0.167, 1.552))]
    fd.sub(Chain(slot, [hr(0.0022), hr(0.003), hr(0.0034), hr(0.003), hr(0.0022)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0044), hr(0.0048), hr(0.0044), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.053, -0.164, 1.556), (-0.028, -0.182, 1.556), (0, -0.187, 1.558), (0.028, -0.182, 1.556), (0.053, -0.164, 1.556)]
    lo_lip = [(-0.045, -0.166, 1.547), (-0.024, -0.182, 1.537), (0, -0.186, 1.535), (0.024, -0.182, 1.537), (0.045, -0.166, 1.547)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.0035), hr(0.006), hr(0.0065), hr(0.006), hr(0.0035)], k=hr(0.006)), hr(0.009), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.0042), hr(0.0075), hr(0.0082), hr(0.0075), hr(0.0042)], k=hr(0.007)), hr(0.009), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.174, 0.035, 1.66)), v3((0.024, 0.043, 0.054)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
    scar = [hp((0.018, -0.196, 1.512)), hp((0.03, -0.19, 1.494)), hp((0.038, -0.18, 1.478))]
    fd.sub(Chain(scar, [hr(0.0025), hr(0.003), hr(0.002)], k=hr(0.002)), hr(0.002))
    fd.paint(Chain(scar, [hr(0.006), hr(0.007), hr(0.005)], k=hr(0.004)), SCAR)


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
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.07, 0.072, 0.104), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(_forearm(side), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.073, 0.065, 0.11), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.022, 0)), 0.044), 0.025, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= hair, helmet, crest
RIM_F = v3((0.0, -0.19, 1.81))          # the helmet's rim, front and back (design coordinates)
RIM_B = v3((0.0, 0.2, 1.64))
_RIM_SLOPE = (RIM_B[2] - RIM_F[2]) / (RIM_B[1] - RIM_F[1])
_RIM_N = norm(v3((0, -_RIM_SLOPE, 1.0)))
HELM_C = HEAD_C + v3((0, 0.01, 0.022))
HELM_R = HEAD_RAD + v3((0.026, 0.026, 0.04))
EAR = [hp((sx * 0.174, 0.035, 1.66)) for sx in (-1, 1)]


def rim_d(P):
    """Signed distance (design units) above the rim plane; positive = under the helmet."""
    return (hinv(P) - RIM_F.astype(F)) @ _RIM_N.astype(F)


def _ear_cut(P):
    d = F(1.0) * np.ones(len(P), F)
    for e in EAR:
        q = (P - (e + v3((0, 0.0, 0.012))).astype(F)) / np.array([0.09, 0.06, 0.075], F)
        d = np.minimum(d, np.sqrt((q * q).sum(1)) - F(1.0))
    return d


def helmet_hull():
    f = Field("HelmHull")
    f.add(Ellipsoid(HELM_C, HELM_R), 0.0)
    return f


def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    fd.add(Ellipsoid(hp((0, -0.06, 1.594)), v3((0.142, 0.132, 0.126)) * HS), 0.07)
    fd.add(neck_prim(), 0.05)
    return fd


def hair_field():
    """Black hair showing under the helmet at her temples and nape, drawn back into a knot below the neck guard."""
    fd = Field("Hair")
    strands = lambda P: F(0.0018) * np.abs(np.sin((hinv(P)[:, 2] + F(0.4) * hinv(P)[:, 1]) * F(240))) + F(0.001) * NOISE(P * F(90))
    def band(P):
        r = rim_d(P)
        Q = hinv(P)
        return np.maximum(np.maximum(-r - F(0.07), r - F(0.012)), F(-0.09) - Q[:, 1] + F(0.04) * smoothstep(0.08, 0.15, np.abs(Q[:, 0])))
    fd.add(Inter(Shell(Ellipsoid(HEAD_C, HEAD_RAD), 0.006, 0.014, pad=0.06, disp=strands, disp_amp=0.003),
                 Func(band, HEAD_C - 0.4, HEAD_C + 0.4), 0.006), 0.0)
    knot = hp((0, 0.185, 1.535))
    fd.add(Ellipsoid(knot, v3((0.066, 0.046, 0.05)) * HS, disp=lambda P: F(0.003) * np.abs(np.sin(np.arctan2(P[:, 2] - F(knot[2]), P[:, 0]) * F(10))), disp_amp=0.004), 0.015)
    return fd


def helmet_field():
    """Bronze (label 0) and gold (6): the bowl down to the rim (notched round the ears), the gold brow-band rising to a
    peak over her forehead, a ridge across the top carrying the crest holder, a short flared neck guard, cheek pieces
    edged in gold, gold rivets."""
    fd = Field("Helmet")
    hull = helmet_hull()
    lo, hi = HELM_C - 0.4, HELM_C + 0.4
    polish = lambda P: F(0.0008) * NOISE(P * F(45))
    fd.add(Inter(Inter(Shell(hull, 0.0, 0.014, pad=0.12, disp=polish, disp_amp=0.002), Func(lambda P: -rim_d(P), lo, hi), 0.003),
                 Func(lambda P: -_ear_cut(P), lo, hi), 0.004), 0.0)
    # the brow-band: a gold strip along the front of the rim, rising to a peak at the middle of her forehead
    def stephane(P):
        Q = hinv(P)
        r = rim_d(P)
        front = np.clip(-(Q[:, 1] + F(0.02)) / F(0.16), 0, 1)
        peak = F(0.05) * np.clip(F(1) - np.abs(Q[:, 0]) / F(0.1), 0, 1)
        return np.maximum(np.maximum(-r - F(0.0), r - F(0.022) - peak), F(0.4) - front)
    fd.add(Inter(Shell(hull, 0.01, 0.014, pad=0.12), Func(stephane, lo, hi), 0.003), 0.003, 6)
    # the neck guard: a short plate flaring out behind the nape
    nc = hp((0.0, 0.16, 1.63))
    R = euler(math.radians(-22), 0, 0)
    def guard(P, nc=nc, R=R):
        q = (P - nc.astype(F)) @ R.astype(F)
        el = (q[:, 0] / F(0.17)) ** 2 + (q[:, 1] / F(0.11)) ** 2 - F(1.0)
        return np.maximum(np.maximum(el * F(0.07), np.abs(q[:, 2]) - F(0.007)), F(-0.02) - q[:, 1])
    fd.add(Func(guard, nc - 0.3, nc + 0.3), 0.01)
    # cheek pieces over the cheeks, gold-edged, hinged at the rim
    face = head_hull()
    def cheek(P):
        Q = hinv(P)
        r = rim_d(P)
        y = Q[:, 1] + F(0.03)
        bottom = F(1.55) - F(0.6) * y * y - Q[:, 2]
        front = F(-0.15) + F(0.2) * np.clip(F(1.69) - Q[:, 2], 0, 0.14) - Q[:, 1]
        return np.maximum(np.maximum(F(0.1) - np.abs(Q[:, 0]), np.maximum(front, Q[:, 1] + F(0.016))), np.maximum(r - F(0.012), bottom))
    fd.add(Inter(Shell(face, 0.018, 0.012, pad=0.12), Func(cheek, HEAD_C - 0.4, HEAD_C + 0.3), 0.005), 0.0)
    fd.paint(Func(lambda P: np.abs(cheek(P) + F(0.007)) - F(0.007), HEAD_C - 0.4, HEAD_C + 0.3), 6)
    for sx in (-1, 1):
        o = hp((sx * 0.5, -0.06, 1.66))
        h, ok = ray_hit(Func(lambda P: face.eval(P) - F(0.03), HEAD_C - 0.5, HEAD_C + 0.5), [o], [v3((-sx, 0, 0))], tmax=0.6)
        if ok[0]:
            fd.add(Sphere(h[0], 0.011), 0.003, 6)
    # the crest holder: a ridge across the top from ear to ear, gold
    for k in range(13):
        a = math.radians(-64 + 128 * k / 12)
        d = v3((math.sin(a), 0.0, math.cos(a)))
        h, ok = ray_hit(hull, [HELM_C + d * 0.6], [-d], tmax=0.7)
        if ok[0]:
            fd.add(Sphere(h[0] + d * 0.008, 0.014), 0.008, 6)
    return fd


def crest_ridge(n=24):
    """Points across the helmet's top from ear to ear (the crest holder)."""
    hull = helmet_hull()
    pts = []
    for k in range(n):
        a = math.radians(-66 + 132 * k / (n - 1))
        d = v3((math.sin(a), 0.0, math.cos(a)))
        h, ok = ray_hit(hull, [HELM_C + d * 0.6], [-d], tmax=0.7)
        if ok[0]:
            pts.append((h[0], d))
    return pts


def crest_field():
    """A tall crest of red horsehair set across the helmet from ear to ear, fanning out at its ends."""
    fd = Field("Crest")
    hairs = lambda P: F(0.0025) * NOISE(P * np.array([90, 90, 14], F)) + F(0.0015) * NOISE(P * F(130))
    pts, ws, ts, ns = [], [], [], []
    ridge = crest_ridge()
    n = len(ridge)
    for k, (p, d) in enumerate(ridge):
        u = k / (n - 1)
        h = 0.1 + 0.03 * math.sin(math.pi * u)
        pts.append(p + d * (h * 0.5 + 0.016))
        ws.append(h * 0.5)
        ts.append(0.024 + 0.006 * math.sin(math.pi * u))
        ns.append(v3((0, 1, 0)))
    fd.add(Lock(pts, ws, ts, ns, k=0.012, disp=hairs, disp_amp=0.004), 0.0)
    return fd


# ======================================================================================= cuirass, sash, pteruges, tunic, cloak
CUIRASS_Z = 0.975


def _cuirass_top(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
    neck_z = F(1.45) - F(0.07) * front * np.exp(-(x / F(0.1)) ** 2) + F(0.3) * smoothstep(0.15, 0.22, np.abs(x))
    return z - neck_z


def cuirass_field():
    """Bronze (label 0): the moulded cuirass from her neck to her waist, a rolled rim round the neck, the armholes and
    the hem; the gorgon's head on her breast is gold (the Gold part); bronze greaves on her shins."""
    fd = Field("Bronze")
    base = bodice_base()
    hammer = lambda P: F(0.001) * NOISE(P * F(45))
    def keep(P):
        return np.maximum(np.maximum(F(CUIRASS_Z) - P[:, 2], _cuirass_top(P)), _bodice_arm(P))
    fd.add(Inter(Shell(base, 0.028, 0.018, pad=0.12, disp=hammer, disp_amp=0.002), Func(keep, (-1, -1, 0.85), (1, 1, 1.6)), 0.005), 0.0)
    def rims(P):
        k = np.maximum(_cuirass_top(P), _bodice_arm(P))
        return np.maximum(np.abs(k + F(0.006)) - F(0.008), F(CUIRASS_Z + 0.02) - P[:, 2])
    fd.add(Inter(Shell(base, 0.038, 0.012, pad=0.12), Func(rims, (-1, -1, 0.9), (1, 1, 1.6)), 0.004), 0.004)
    fd.add(Inter(Shell(base, 0.038, 0.012, pad=0.12), Func(lambda P: np.abs(P[:, 2] - F(CUIRASS_Z + 0.008)) - F(0.009), (-1, -1, 0.85), (1, 1, 1.1)), 0.004), 0.004)
    # a moulded line down the middle of the belly
    outer = Func(lambda P: base.eval(P, margin=0.06) - F(0.038), (-0.6, -0.6, 0.85), (0.6, 0.6, 1.6))
    pts = []
    for z in np.linspace(1.0, 1.16, 5):
        h, ok = ray_hit(outer, [v3((0, -0.6, z))], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            pts.append(h[0])
    if len(pts) > 2:
        fd.sub(Chain(pts, [0.004] * len(pts), k=0.003), 0.004)
    # greaves
    for side in ("R", "L"):
        kn, an = J["knee_" + side], J["ankle_" + side]
        ax = norm(an - kn)
        L = float(np.linalg.norm(an - kn))
        shin = Field("Shin")
        for p, k in leg_prims(side)[2:]:
            shin.add(p, k)
        def gkeep(P, kn=kn, ax=ax, L=L):
            t = (P - kn.astype(F)) @ ax.astype(F)
            span = np.maximum(F(-0.06) - t, t - F(L * 0.78))
            c = kn.astype(F) + t[:, None] * ax.astype(F)
            return np.maximum(span, (P[:, 1] - c[:, 1]) - F(0.04))
        fd.add(Inter(Shell(shin, 0.014, 0.01, pad=0.08, disp=hammer, disp_amp=0.002), Func(gkeep, kn - 0.3, an + 0.3), 0.004), 0.0)
        for t0 in (-0.06, L * 0.78):
            def grim(P, t0=t0, kn=kn, ax=ax):
                t = (P - kn.astype(F)) @ ax.astype(F)
                c = kn.astype(F) + t[:, None] * ax.astype(F)
                return np.maximum(np.abs(t - F(t0)) - F(0.008), (P[:, 1] - c[:, 1]) - F(0.04))
            fd.add(Inter(Shell(shin, 0.02, 0.009, pad=0.08), Func(grim, kn - 0.3, an + 0.3), 0.003), 0.003)
    return fd


SASH_Z = 1.05


def sash_field():
    """The legate's red sash: tied round her waist over the cuirass, knotted in front, its two ends hanging."""
    fd = Field("Sash")
    base = bodice_base()
    fold = lambda P: F(0.003) * np.sin(P[:, 2] * F(160)) + F(0.0015) * NOISE(P * F(30))
    def band(P):
        return np.abs(P[:, 2] - (F(SASH_Z) + F(0.015) * P[:, 0])) - F(0.022)
    def cloth(P):
        d = base.eval(P, margin=0.1)
        return np.maximum(d - (F(0.064) - fold(P)), F(0.044) - d)
    fd.add(Inter(Func(cloth, (-0.6, -0.5, 0.85), (0.6, 0.5, 1.15)), Func(band, (-0.6, -0.5, 0.85), (0.6, 0.5, 1.15)), 0.005), 0.0)
    kp, ok = ray_hit(Func(lambda P: base.eval(P) - F(0.07), (-0.6, -0.6, 0.85), (0.6, 0.6, 1.15)), [v3((0.03, -0.7, SASH_Z))], [v3((0, 1, 0))], tmax=0.8)
    k0 = kp[0] if ok[0] else v3((0.03, -0.2, SASH_Z))
    fd.add(Ellipsoid(k0, (0.032, 0.022, 0.026)), 0.008)
    for dx, L in ((-0.03, 0.15), (0.035, 0.12)):
        pts = [k0, k0 + v3((dx * 0.5, -0.012, -L * 0.45)), k0 + v3((dx, -0.008, -L))]
        fd.add(Lock(pts, [0.034, 0.03, 0.028], [0.006, 0.006, 0.005], [v3((0, -1, 0))] * 3, k=0.008, disp=fold, disp_amp=0.003), 0.006)
    return fd


def _strip_tex(n, ph):
    """Grooves between the strips of a row of pteruges (one-sided: positive pushes the outer face in)."""
    def fn(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        s = np.mod(a * F(n / (2 * math.pi)) + F(ph), F(1.0))
        return F(0.006) * smoothstep(0.1, 0.0, np.minimum(s, F(1) - s)) + F(0.0008) * NOISE(P * F(40))
    return fn


def pteruges_field():
    """White leather strips (label 0) fringed in gold (5): two rows below the cuirass to mid-thigh, and over each
    shoulder a short row hanging over the upper arm."""
    fd = Field("Pteruges")
    kb = kilt_base()
    for off_in, off_out, z1, n, ph in ((0.03, 0.048, 0.66, 22, 0.0), (0.036, 0.062, 0.76, 18, 0.5)):
        tex = _strip_tex(n, ph)
        def strips(P, off_in=off_in, off_out=off_out, tex=tex):
            d = kb.eval(P, margin=0.12)
            return np.maximum(d - (F(off_out) - tex(P)), F(off_in) - d)
        def keep(P, z1=z1, n=n, ph=ph):
            a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
            s = np.mod(a * F(n / (2 * math.pi)) + F(ph), F(1.0))
            round_end = F(0.012) * (F(1) - (F(2) * s - F(1)) ** 2)
            return np.maximum(F(z1) - round_end - P[:, 2], P[:, 2] - F(CUIRASS_Z + 0.01))
        fd.add(Inter(Func(strips, (-0.6, -0.6, 0.55), (0.6, 0.6, 1.05)), Func(keep, (-1, -1, 0.5), (1, 1, 1.05)), 0.003), 0.003)
        fd.paint(Func(lambda P, z1=z1: np.maximum(P[:, 2] - F(z1 + 0.026), F(z1 - 0.05) - P[:, 2]), (-1, -1, 0.5), (1, 1, 1.0)), 5)
    # the shoulder rows: strips hanging from the armhole over the deltoid
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        hull = Field("ArmHull")
        hull.add(deltoid(side), 0.0)
        hull.add(upper_arm(side), 0.045)
        ax = norm(el - sh)
        def shtex(P, sh=sh, ax=ax):
            q = P - sh.astype(F)
            a = np.arctan2(q[:, 1], q[:, 2] * F(0.6) + F(0.1))
            s = np.mod(a * F(12 / math.pi), F(1.0))
            return F(0.007) * smoothstep(0.12, 0.0, np.minimum(s, F(1) - s))
        def sh_strips(P, hull=hull, shtex=shtex):
            d = hull.eval(P, margin=0.1)
            return np.maximum(d - (F(0.036) - shtex(P)), F(0.016) - d)
        def sh_keep(P, sh=sh, ax=ax, sx=sx):
            t = (P - sh.astype(F)) @ ax.astype(F)
            return np.maximum(np.maximum(t - F(0.15), F(-0.01) - t), F(0.22) - P[:, 0] * F(sx))
        fd.add(Inter(Func(sh_strips, sh - 0.3, sh + 0.3), Func(sh_keep, sh - 0.4, sh + 0.4), 0.003), 0.003)
        fd.paint(Func(lambda P, sh=sh, ax=ax: np.abs((P - sh.astype(F)) @ ax.astype(F) - F(0.137)) - F(0.014), sh - 0.4, sh + 0.4), 5)
    return fd


TUNIC_HEM = 0.58


def tunic_field():
    """A red wool tunic: its sleeves under the shoulder strips, its skirt under the hip strips to above the knee."""
    fd = Field("Tunic")
    b = Field("TunicBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(RoundCone((0, 0.035, 0.88), (0, 0.035, 0.5), 0.225, 0.29), 0.08)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.05)
        b.add(upper_arm(side), 0.045)
    folds = lambda P: F(0.004) * np.sin(np.arctan2(P[:, 0], -(P[:, 1] - F(0.035))) * F(16)) * smoothstep(0.9, 0.7, P[:, 2]) + F(0.0012) * NOISE(P * F(25))
    def cloth(P):
        d = b.eval(P, margin=0.1)
        return np.maximum(d - (F(0.026) - folds(P)), F(0.006) - d)
    def keep(P):
        x, z = P[:, 0], P[:, 2]
        hidden = np.minimum(np.minimum(z - F(0.99), F(0.25) - np.abs(x)), F(1.42) - z)        # under the cuirass
        sleeve = F(-1.0) * np.ones(len(P), F)
        for side in ("R", "L"):
            sh, el = J["shoulder_" + side], J["elbow_" + side]
            ax = norm(el - sh)
            c = lerp(sh, el, 0.5)
            sxx = -1 if side == "R" else 1
            sleeve = np.maximum(sleeve, np.where(P[:, 0] * F(sxx) > F(0.24), (P - c.astype(F)) @ ax.astype(F), F(-1.0)))
        neck = z - (F(1.46) + F(0.3) * smoothstep(0.13, 0.21, np.abs(x)))
        return np.maximum(np.maximum(np.maximum(neck, sleeve), F(TUNIC_HEM) - z), hidden)
    fd.add(Inter(Func(cloth, (-0.7, -0.5, 0.45), (0.7, 0.5, 1.6)), Func(keep, (-1, -1, 0.45), (1, 1, 1.6)), 0.005), 0.0)
    return fd


def cloak_hull():
    fd = Field("CloakHull")
    for p, k in torso_prims():
        fd.add(p, k)
    fd.add(traps(), 0.06)
    for side in ("R", "L"):
        fd.add(deltoid(side), 0.06)
    fd.add(RoundCone((0, 0.14, 1.12), (0, 0.22, 0.32), 0.26, 0.34), 0.12)      # it hangs behind her hips and legs
    return fd


CLOAK_HEM = 0.36


def cloak_field():
    """The red cloak (paludamentum): over both shoulders and down her back to her calves in long folds, its top edge
    across her collarbones, pinned at her right shoulder (the gold brooch: the Gold part)."""
    fd = Field("Cloak")
    hull = cloak_hull()
    def folds(P):
        a = np.arctan2(P[:, 0], P[:, 1] - F(0.0))
        k = smoothstep(1.25, 0.9, P[:, 2])
        return F(0.02) * np.sin(a * F(6) + F(0.6) * NOISE(P * F(3))) * k + F(0.0015) * NOISE(P * F(25))
    def cloth(P):
        d = hull.eval(P, margin=0.14)
        return np.maximum(d - (F(0.08) - folds(P)), F(0.05) - d)
    def keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        wrap = F(0.13) * smoothstep(0.12, 0.24, np.abs(x)) * smoothstep(1.24, 1.4, z)
        back = F(0.02) - y + F(0.14) * smoothstep(1.3, 1.0, z) - wrap
        top = z - (F(1.47) - F(0.06) * np.clip(-(y - F(0.05)) / F(0.15), 0, 1) + F(0.25) * smoothstep(0.14, 0.24, np.abs(x)))
        hem = F(CLOAK_HEM) + F(0.03) * np.sin(x * F(14)) + F(0.012) * NOISE(P * F(8)) - z
        return np.maximum(np.maximum(back, top), hem)
    fd.add(Inter(Func(cloth, (-0.8, -0.5, 0.2), (0.8, 0.8, 1.6)), Func(keep, (-1, -1, 0.2), (1, 1, 1.6)), 0.006), 0.0)
    return fd


def gold_field():
    """The gorgon's head on her breast (a round medallion: a face in a ring of snakes), the cloak's brooch on her right
    shoulder, a bracelet on her sword wrist, small earrings."""
    fd = Field("Gold")
    base = bodice_base()
    outer = Func(lambda P: base.eval(P, margin=0.06) - F(0.04), (-0.6, -0.6, 0.85), (0.6, 0.6, 1.6))
    h, ok = ray_hit(outer, [v3((0, -0.6, 1.27))], [v3((0, 1, 0))], tmax=0.8)
    if ok[0]:
        c = h[0]
        n = v3((0, -1, 0.25))
        R = rot_from_axes(z_axis=n)
        fd.add(Cylinder(c, 0.05, 0.012, rr=0.004, R=R), 0.0)
        fd.add(Ellipsoid(c + norm(n) * 0.008, (0.026, 0.028, 0.012), R=R), 0.004)                 # the face
        for k in range(10):
            a = 2 * math.pi * k / 10
            d = R @ v3((math.cos(a), math.sin(a), 0))
            fd.add(Torus(c + d * 0.042 + norm(n) * 0.006, 0.009, 0.0035, R=R), 0.002)            # the snakes' coils
    ch = cloak_hull()
    bp, ok = ray_hit(Func(lambda P: ch.eval(P, margin=0.1) - F(0.07), (-1, -1, 0.8), (1, 1, 1.9)), [v3((-0.21, -0.05, 1.9))], [v3((0, 0, -1))], tmax=0.8)
    if ok[0]:
        c = bp[0]
        nb = norm(v3((-0.2, -0.75, 0.6)))
        fd.add(Cylinder(c, 0.036, 0.008, rr=0.004, R=rot_from_axes(z_axis=nb)), 0.0)
        fd.add(Sphere(c + nb * 0.01, 0.016), 0.003)
        for k in range(8):
            a = 2 * math.pi * k / 8
            d = rot_from_axes(z_axis=nb) @ v3((math.cos(a), math.sin(a), 0))
            fd.add(Sphere(c + d * 0.03 + nb * 0.006, 0.006), 0.002)
    el, wr = J["elbow_R"], J["wrist_R"]
    ax = norm(wr - el)
    cc = lerp(el, wr, 0.86)
    fd.add(Inter(Shell(_forearm("R"), 0.009, 0.009, pad=0.05), Func(lambda P: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.012), cc - 0.2, cc + 0.2), 0.002), 0.0)
    return fd


def leather_field():
    """Sandals laced up her calves (Kira's), a wrap on her sword hand's wrist."""
    fd = Field("Leather")
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
        shin = Field("Shin")
        for p, k in leg_prims(side)[3:]:
            shin.add(p, k)
        for z in (an[2] + 0.03, an[2] + 0.055):
            fd.add(Inter(Shell(shin, 0.006, 0.008, pad=0.05), Func(lambda P, z=z: np.abs(P[:, 2] - F(z)) - F(0.006), an - 0.2, kn + 0.2), 0.002), 0.002)
    return fd


# ======================================================================================= gladius, shield
GL_GRIP = 0.05            # fist centre -> the guard
GL_BLADE = 0.5            # the guard -> the point
GL_W = 0.027


def gladius_axis():
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t


def gladius_field():
    """A steel blade with parallel edges and a short sharp point, a fuller (label 0); a ridged bone grip (5); a gold
    guard and an eagle's-head pommel (6). Its edges face the knuckles and the wrist; its flats the palm and the back
    of the hand."""
    fd = Field("Gladius")
    a0, ax = gladius_axis()
    wr, f, n, t = hand_frame("R")
    edge = norm(f - ax * (f @ ax))
    flat = norm(np.cross(ax, edge))
    g0 = a0 + ax * GL_GRIP
    tip = g0 + ax * GL_BLADE
    def blade(P):
        q = P - g0.astype(F)
        u = q @ ax.astype(F)
        v = q @ edge.astype(F)
        w = q @ flat.astype(F)
        L = F(GL_BLADE)
        taper = np.clip((L - u) / F(0.1), 0, 1)
        hw = F(GL_W) * (F(0.35) + F(0.65) * taper) * np.where(u < L - F(0.1), F(1.0), taper)
        th = F(0.0075) * (F(0.4) + F(0.6) * np.clip(F(1) - np.abs(v) / np.maximum(hw, F(1e-4)), 0, 1))
        return np.maximum(np.maximum(np.abs(v) - hw, np.abs(w) - th), np.maximum(-u, u - L))
    fd.add(Func(blade, np.minimum(g0, tip) - 0.06, np.maximum(g0, tip) + 0.06), 0.0)
    fd.sub(Chain([g0 + ax * 0.03, g0 + ax * (GL_BLADE - 0.12)], [0.004, 0.003], k=0.002), 0.002)
    fd.add(RoundCone(a0 - ax * 0.055, a0 + ax * 0.045, 0.018, 0.017), 0.0, 5)
    for k in range(4):
        fd.add(Torus(a0 + ax * (-0.04 + 0.025 * k), 0.018, 0.0045, R=rot_from_axes(z_axis=ax)), 0.003, 5)
    fd.add(Ellipsoid(a0 + ax * (GL_GRIP - 0.004), (0.048, 0.026, 0.012), R=rot_from_axes(z_axis=ax, x_axis=edge)), 0.004, 6)
    # the eagle's head pommel: a rounded head, a hooked beak toward the knuckles
    ph = a0 - ax * 0.078
    fd.add(Sphere(ph, 0.026), 0.006, 6)
    fd.add(RoundCone(ph + edge * 0.012, ph + edge * 0.036 - ax * 0.012, 0.012, 0.005), 0.005, 6)
    for sf in (-1, 1):
        fd.sub(Sphere(ph + edge * 0.008 + flat * sf * 0.024 - ax * 0.004, 0.005), 0.002)        # its eyes
    return fd


SHIELD_RX, SHIELD_RY = 0.3, 0.4      # the oval's half width and half height
SHIELD_DOME = 0.045
SHIELD_T = 0.022
SHIELD_BACK = 0.045


def shield_field():
    """An oval shield, gently domed: red (label 0); a gold eagle with spread wings in the middle and a laurel wreath
    round the edge (5); a bronze rim (6); a gold boss (6, raised); the bare wooden back and its grip (8)."""
    fd = Field("Shield")
    G, N, U, S = shield_frame()
    C = G + N * SHIELD_BACK
    paint = lambda P: F(0.0012) * NOISE(P * F(40))
    def oval(P):
        q = P - C.astype(F)
        u, s, h = q @ U.astype(F), -(q @ S.astype(F)), q @ N.astype(F)          # (s: up as held; +S points down)
        e = np.sqrt((u / F(SHIELD_RX)) ** 2 + (s / F(SHIELD_RY)) ** 2)
        dome = F(SHIELD_DOME) * (F(1) - np.minimum(e, F(1)) ** 2)
        return u, s, h - dome, e
    def body(P):
        u, s, hh, e = oval(P)
        return np.maximum((e - F(1)) * F(SHIELD_RX), np.abs(hh - F(SHIELD_T * 0.5)) - F(SHIELD_T * 0.5))
    lo = np.minimum.reduce([C + U * su * 0.45 + S * ss * 0.55 + N * sn * 0.2 for su in (-1, 1) for ss in (-1, 1) for sn in (-1, 1)])
    hi = np.maximum.reduce([C + U * su * 0.45 + S * ss * 0.55 + N * sn * 0.2 for su in (-1, 1) for ss in (-1, 1) for sn in (-1, 1)])
    fd.add(Func(body, lo, hi, disp=paint, disp_amp=0.002), 0.0)
    def rim(P):
        u, s, hh, e = oval(P)
        return np.maximum(np.abs(e - F(0.985)) * F(SHIELD_RX) - F(0.012), np.abs(hh - F(SHIELD_T * 0.5)) - F(SHIELD_T * 0.5 + 0.006))
    fd.add(Func(rim, lo, hi), 0.004, 6)
    face = C + N * (SHIELD_DOME + SHIELD_T)
    fd.add(Inter(Sphere(face - N * 0.035, 0.085), Plane(face - N * 0.005, -N), 0.004), 0.006, 6)
    def front(P):
        u, s, hh, e = oval(P)
        return F(SHIELD_T * 0.55) - hh
    def eagle(P):
        u, s, hh, e = oval(P)
        au = np.abs(u)
        body_ = np.sqrt((u / F(0.04)) ** 2 + ((s - F(0.02)) / F(0.12)) ** 2) - F(1)                 # (s: up as held)
        t = np.clip(au / F(0.24), 0, 1)
        wing_c = F(0.06) + F(0.1) * t - F(0.08) * t * t
        wing = np.maximum(np.abs(s - wing_c) - (F(0.05) * (F(1) - t) + F(0.012)) + F(0.012) * np.abs(np.sin(au * F(60))) * t,
                          np.maximum(F(0.03) - au, au - F(0.24)))
        tail = np.maximum(np.abs(u) - F(0.03) - F(0.2) * np.clip(F(-0.08) - s, 0, 1), np.maximum(s + F(0.17), F(-0.08) - s - F(0.0)))
        return np.maximum(np.minimum(np.minimum(body_ * F(0.04), wing), tail), front(P))
    fd.paint(Func(eagle, lo, hi), 5)
    def wreath(P):
        u, s, hh, e = oval(P)
        a = np.arctan2(s, u)
        leaves = np.abs(np.sin(a * F(28)))
        ring = np.abs(e - F(0.84)) * F(SHIELD_RX) - F(0.008) - F(0.012) * leaves
        return np.maximum(ring, front(P))
    fd.paint(Func(wreath, lo, hi), 5)
    fd.paint(Func(lambda P: oval(P)[2] - F(SHIELD_T * 0.3), lo, hi), 8)
    fd.add(RoundCone(G - U * 0.07, G + U * 0.07, 0.016, 0.016), 0.01, 8)
    fd.add(RoundBox(C - N * 0.004, (0.13, 0.03, 0.006), 0.004, R=rot_from_axes(z_axis=N, x_axis=U)), 0.004, 8)
    return fd


# ======================================================================================= painting
def warm_points():
    return br.warm_points()


# ======================================================================================= build config
GLB_NAME = "cassia"
ROOT_NAME = "HeroCassiaHQ"
TEX_PREFIX = "hero"
MAT_NAME = "CassiaMat"
MESH_NAME = "Cassia"
BASE_MODULE = "cassia_base"
ANIM_MODULE = "anim_cassia"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Helmet", "Crest", "Bronze", "Sash", "Pteruges", "Tunic", "Cloak", "Gold", "Leather",
         "Gladius", "Shield"]
REGION_PARTS = ("Skin", "Helmet", "Pteruges", "Gladius", "Shield")
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_CassiaSkin", "base": (0.82, 0.6, 0.46), "ruddy": (0.84, 0.5, 0.42), "lips": (0.7, 0.38, 0.35),
                      "brow": ((0.05, 0.04, 0.04), (0.12, 0.09, 0.08)),
                      "extra": ((LASH, (0.04, 0.03, 0.03), 0.6), (SCAR, (0.9, 0.7, 0.62), 0.7))}),
    "Hair": ("hair", {"name": "HQ_CassiaHair", "base": (0.06, 0.05, 0.05), "hi": (0.26, 0.22, 0.22), "low": (0.03, 0.025, 0.025),
                      "streak": (0.04, 0.035, 0.035), "tint": (0.12, 0.08, 0.08)}),
    "Helmet": ("bronze", {"name": "HQ_CassiaHelmet", "gilt": 6}),
    "Crest": ("hair", {"name": "HQ_CassiaCrest", "base": (0.7, 0.1, 0.06), "hi": (0.98, 0.36, 0.2), "low": (0.32, 0.04, 0.03),
                       "streak": (0.5, 0.06, 0.04), "tint": (0.84, 0.22, 0.08)}),
    "Bronze": ("bronze", {"name": "HQ_CassiaBronze"}),
    "Sash": ("cloth", {"name": "HQ_LegateSash", "col": (0.7, 0.08, 0.1)}),
    "Pteruges": ("linen", {"name": "HQ_Pteruges", "base": (0.92, 0.88, 0.78), "border": (0.92, 0.7, 0.28)}),
    "Tunic": ("wool", {"name": "HQ_CassiaTunic", "base": (0.68, 0.1, 0.07)}),
    "Cloak": ("wool", {"name": "HQ_Paludamentum", "base": (0.62, 0.08, 0.07)}),
    "Gold": ("gold", {"name": "HQ_CassiaGold"}),
    "Leather": ("leather", {"name": "HQ_CassiaLeather", "base": (0.4, 0.22, 0.12)}),
    "Gladius": ("gladius", {"name": "HQ_CassiaGladius"}),
    "Shield": ("scutum", {"name": "HQ_CassiaShield"}),
}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Hair": 700, "Helmet": 2200, "Crest": 800, "Bronze": 2800, "Sash": 700, "Pteruges": 2800,
               "Tunic": 1400, "Cloak": 2200, "Gold": 800, "Leather": 1000, "Gladius": 420, "Shield": 1300}
AO_EXCLUDE = ["Gladius", "Shield"]
BAKE_APART = (["Shield"], (3.0, 0.0, 0.0))


def prop_bones():
    return []


def hair_weights(ob, skin_ob, arm):
    groups = {}
    z1 = hp((0, 0, 1.58))[2]
    for v in ob.data.vertices:
        p = v.co
        t = max(0.0, min(1.0, (z1 - p.z) / 0.15))
        _blend_add(ob, groups, v.index, {"head": 1.0 - 0.5 * t, "neck": 0.5 * t})


def bronze_weights(ob, skin_ob, arm):
    """The cuirass on her torso (its shoulder edges with the clavicles); the greaves on her shins."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "shin.R", "shin.L"})


def cloak_weights(ob, skin_ob, arm):
    """The cloak rides her shoulders and chest at the top and her spine and hips lower down (not her legs: it hangs)."""
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z > 1.25:
            side = "R" if p.x < 0 else "L"
            t = max(0.0, min(1.0, (abs(p.x) - 0.12) / 0.15))
            w = {"chest": 1.0 - 0.5 * t, "clavicle." + side: 0.5 * t}
        else:
            t = max(0.0, min(1.0, (1.25 - p.z) / 0.7))
            w = {"chest": 1.0 - t, "spine": 0.6 * t, "root": 0.4 * t}
        _blend_add(ob, groups, v.index, w)


def gold_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z > hp((0, 0, 1.5))[2] and abs(p.x) > 0.15:
            w = {"head": 1.0}
        elif abs(p.x) > 0.45:
            w = {"forearm.R": 1.0}
        else:
            w = {"chest": 1.0}
        _blend_add(ob, groups, v.index, w)


def pteruges_weights(ob, skin_ob, arm):
    """The hip strips swing from the root, the thighs pulling at them; the shoulder rows ride the upper arms."""
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z > 1.15:
            side = "R" if p.x < 0 else "L"
            w = {"upperarm." + side: 0.75, "clavicle." + side: 0.25}
        else:
            t = max(0.0, min(1.0, (CUIRASS_Z - p.z) / 0.3))
            side = "R" if p.x < 0 else "L"
            w = {"root": 1.0 - 0.45 * t, "thigh." + side: 0.45 * t}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Helmet": ("rigid", "head"),
        "Crest": ("rigid", "head"), "Bronze": ("custom", bronze_weights), "Sash": ("rigid", "spine"),
        "Pteruges": ("custom", pteruges_weights),
        "Tunic": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L"},
                  {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Cloak": ("custom", cloak_weights), "Gold": ("custom", gold_weights),
        "Leather": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gladius": ("rigid", "hand.R"), "Shield": ("rigid", "hand.L"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Gladius":
        return 0.7
    if part == "Shield":
        return 1.2
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Helmet", helmet_field(), 0.0022 if fine else 0.0032),
        ("Crest", crest_field(), 0.0026 if fine else 0.0036),
        ("Bronze", cuirass_field(), 0.0024 if fine else 0.0034),
        ("Sash", sash_field(), 0.0024 if fine else 0.0034),
        ("Pteruges", pteruges_field(), 0.0024 if fine else 0.0034),
        ("Tunic", tunic_field(), 0.0026 if fine else 0.0036),
        ("Cloak", cloak_field(), 0.0028 if fine else 0.0038),
        ("Gold", gold_field(), 0.0016 if fine else 0.0024),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Gladius", gladius_field(), 0.0016 if fine else 0.0022),
        ("Shield", shield_field(), 0.0024 if fine else 0.0032),
    ]
