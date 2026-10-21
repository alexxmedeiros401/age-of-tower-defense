"""The Legionary (HQ tower, Classical Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A grizzled legionary: a square stubbled jaw, a nose broken long ago and set crooked, a scar through his left brow, short
cropped black hair. An iron helmet (a galea): a polished bowl with a brow guard jutting over his eyes, a deep neck guard
flaring out behind, big cheek pieces edged in brass, a short red horsehair crest from front to back on a brass holder.
A lorica segmentata: iron hoops round his belly, plates over his chest and back, curved lames arching over each shoulder,
brass hinges and buckles; a red wool tunic to the knee showing below it and at the sleeves; a white neck scarf; a military
belt of brass plates with an apron of studded leather straps hanging in front; hobnailed sandal-boots laced up the
ankle. A big curved rectangular shield (a scutum) on his left arm: red, edged in brass, an iron boss, gold wings and
thunderbolts round the boss; a gladius in his right fist (a short steel blade with a sharp point, a bone grip ridged for
the fingers, a brass guard and a ball pommel).

His body, hands and fists are the Spear Guard's (spear.py); the gladius lies along the right fist's thumb axis, the
shield's grip runs across its back behind the boss, in the left fist (both rigid: "frame" aims in anim_legionary.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import spear as sp
from spear import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R,
                   eye_c, smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, torso_prims, traps, neck_prim,
                   deltoid, eyes_field, teeth_field, kilt_base, cuirass_base, _forearm, warm_points, TORSO, TORSO_Z,
                   torso_bones, head_hull, stubble_mask, shield_frame)

SCAR = 10


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.055, 1.585), (0.15, 0.136, 0.13)), 0.07, SKIN)                           # a broad square jaw
    fd.add(E((0, -0.136, 1.497), (0.094, 0.072, 0.07)), 0.05, SKIN)                          # a heavy chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.118, 1.628), 0.05), 0.05, SKIN)                               # cheekbones
        fd.add(S((sx * 0.13, -0.045, 1.555), 0.056), 0.05, SKIN)                               # jaw corners
        pts = [hp((sx * 0.152, -0.055, 1.742)), hp((sx * 0.116, -0.13, 1.752)), hp((sx * 0.06, -0.174, 1.752)), hp((0.0, -0.184, 1.75))]
        fd.add(Chain(pts, [hr(0.013), hr(0.024), hr(0.028), hr(0.028)], k=hr(0.022)), hr(0.035), SKIN)     # a heavy brow ridge
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # heavy straight brows, drawn down: a narrow-eyed squint
    for sx in (-1, 1):
        pts = [hp((sx * 0.024, -0.214, 1.748)), hp((sx * 0.066, -0.207, 1.758)), hp((sx * 0.11, -0.185, 1.762)), hp((sx * 0.152, -0.143, 1.754))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.012), hr(0.014), hr(0.012), hr(0.006)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.02), hr(0.022), hr(0.019), hr(0.011)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0065)), Plane(ec + v3((0, 0, hr(0.012))), (sx * 0.2, 0.06, -1.0)), hr(0.004))   # heavy lids
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.005)), Plane(ec + v3((0, 0, -hr(0.022))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.009))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
    # a broken nose: a lump on the bridge, the tip set crooked to his left
    fd.add(RoundCone(hp((0, -0.184, 1.722)), hp((0.012, -0.238, 1.634)), hr(0.019), hr(0.027)), hr(0.017), SKIN)
    fd.add(S((-0.003, -0.211, 1.69), 0.02), hr(0.012), SKIN)
    fd.add(S((0.013, -0.24, 1.618), 0.031), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.031 + 0.01, -0.213, 1.604), 0.021), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.016 + 0.01, -0.231, 1.591)), v3((0.009, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a scar through his left brow down onto the cheek
    scar = [hp((0.044, -0.205, 1.79)), hp((0.06, -0.203, 1.745)), hp((0.078, -0.18, 1.69)), hp((0.09, -0.16, 1.64))]
    fd.sub(Chain(scar, [hr(0.003), hr(0.0035), hr(0.003), hr(0.002)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(scar, [hr(0.007), hr(0.008), hr(0.007), hr(0.005)], k=hr(0.004)), SCAR)
    # mouth: a hard flat line, the corners down
    slot = [hp((-0.06, -0.166, 1.547)), hp((-0.031, -0.193, 1.546)), hp((0, -0.199, 1.547)), hp((0.031, -0.193, 1.546)), hp((0.06, -0.166, 1.547))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.056, -0.164, 1.551), (-0.03, -0.185, 1.554), (-0.008, -0.19, 1.557), (0.008, -0.19, 1.557), (0.03, -0.185, 1.554), (0.056, -0.164, 1.551)]
    lo_lip = [(-0.048, -0.167, 1.54), (-0.026, -0.185, 1.535), (0, -0.189, 1.533), (0.026, -0.185, 1.535), (0.048, -0.167, 1.54)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.004), hr(0.006), hr(0.0065), hr(0.0065), hr(0.006), hr(0.004)], k=hr(0.006)), hr(0.008), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.0075), hr(0.0085), hr(0.0075), hr(0.005)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.178, 0.035, 1.66)), v3((0.026, 0.047, 0.06)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        fd.add(RoundCone(sh, el, 0.098, 0.074), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.025, 0)), (0.088, 0.09, 0.128), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)
        fd.add(RoundCone(el, wr, 0.072, 0.055), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.093, 0.083, 0.132), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.056), 0.028, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.138, 0.09), 0.065, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.125, 0.118, 0.188), R=rot_from_axes(z_axis=kn - hip)), 0.048, SKIN)
        fd.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.069), 0.038, SKIN)
        fd.add(RoundCone(kn, an, 0.088, 0.058), 0.038, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.096, 0.142), R=rot_from_axes(z_axis=an - kn)), 0.043, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= helmet (iron, brass), hair, crest
RIM_F = v3((0.0, -0.19, 1.8))
RIM_B = v3((0.0, 0.2, 1.645))
_RIM_SLOPE = (RIM_B[2] - RIM_F[2]) / (RIM_B[1] - RIM_F[1])
_RIM_N = norm(v3((0, -_RIM_SLOPE, 1.0)))
HELM_C = HEAD_C + v3((0, 0.012, 0.024))
HELM_R = HEAD_RAD + v3((0.026, 0.026, 0.044))
EAR = [hp((sx * 0.178, 0.035, 1.66)) for sx in (-1, 1)]


def rim_d(P):
    """Signed distance (design units) above the helmet's rim plane; positive = under the helmet."""
    Q = hinv(P)
    return (Q - RIM_F.astype(F)) @ _RIM_N.astype(F)


def _ear_cut(P):
    """> 0 outside the notches the rim makes round each ear."""
    d = F(1.0) * np.ones(len(P), F)
    for e in EAR:
        q = (P - (e + v3((0, 0.0, 0.01))).astype(F)) / np.array([0.09, 0.062, 0.078], F)
        d = np.minimum(d, np.sqrt((q * q).sum(1)) - F(1.0))
    return d


def helmet_hull():
    f = Field("HelmHull")
    f.add(Ellipsoid(HELM_C, HELM_R), 0.0)
    return f


def crest_ridge(lift=0.0, n=26):
    """Points along the helmet's top centre line, from the brow over the crown (+ lift outward)."""
    hull = helmet_hull()
    pts = []
    for k in range(n):
        th = math.radians(38 + 120 * k / (n - 1))
        d = v3((0, -math.cos(th), math.sin(th)))
        o = HELM_C + d * 0.6
        h, ok = ray_hit(hull, [o], [-d], tmax=0.7)
        if ok[0]:
            pts.append(h[0] + d * lift)
    return pts


def helmet(fd):
    """The galea (label 0 iron, 6 brass): the bowl down to the rim (notched round the ears), a brow guard jutting forward,
    a ridge across the brow, a deep neck guard flaring out behind, cheek pieces edged in brass (hinged at the rim), brass
    rivets and a brass crest holder."""
    hull = helmet_hull()
    lo, hi = HELM_C - 0.4, HELM_C + 0.4
    polish = lambda P: F(0.001) * NOISE(P * F(45))
    fd.add(Inter(Inter(Shell(hull, 0.0, 0.014, pad=0.12, disp=polish, disp_amp=0.002), Func(lambda P: -rim_d(P), lo, hi), 0.003),
                 Func(lambda P: -_ear_cut(P), lo, hi), 0.004), 0.0)
    # the brow guard: a strip jutting forward over the eyes along the front of the rim
    def brow(P):
        Q = hinv(P)
        r = rim_d(P)
        front = np.clip(-(Q[:, 1] - F(0.0)) / F(0.18), 0, 1)
        return np.maximum(np.abs(r - F(0.006)) - F(0.008), F(0.5) - front)
    fd.add(Inter(Shell(hull, 0.006, 0.026, pad=0.12), Func(brow, lo, hi), 0.004), 0.004)
    # a raised ridge across the brow, a hand's width above the rim (brass)
    def ridge(P):
        Q = hinv(P)
        r = rim_d(P)
        front = np.clip(-(Q[:, 1] + F(0.02)) / F(0.16), 0, 1)
        return np.maximum(np.abs(r + F(0.045)) - F(0.008), F(0.45) - front)
    fd.add(Inter(Shell(hull, 0.008, 0.01, pad=0.12), Func(ridge, lo, hi), 0.003), 0.003, 6)
    # the neck guard: a broad plate flaring out and down behind the nape, its edge rolled in brass
    nc = hp((0.0, 0.16, 1.64))
    R = euler(math.radians(26), 0, 0)
    def guard(P, nc=nc, R=R):
        q = (P - nc.astype(F)) @ R.astype(F)
        el = (q[:, 0] / F(0.2)) ** 2 + (q[:, 1] / F(0.17)) ** 2 - F(1.0)
        return np.maximum(np.maximum(el * F(0.08), np.abs(q[:, 2]) - F(0.008)), F(-0.02) - q[:, 1])
    fd.add(Func(guard, nc - 0.3, nc + 0.3), 0.01)
    def guard_rim(P, nc=nc, R=R):
        q = (P - nc.astype(F)) @ R.astype(F)
        el = np.sqrt((q[:, 0] / F(0.2)) ** 2 + (q[:, 1] / F(0.17)) ** 2)
        return np.maximum(np.maximum(np.abs(el - F(0.97)) * F(0.17) - F(0.008), np.abs(q[:, 2]) - F(0.013)), F(0.04) - q[:, 1])
    fd.add(Func(guard_rim, nc - 0.3, nc + 0.3), 0.004, 6)
    # cheek pieces over the cheeks and jaw (a shell of the face), scalloped in front of the eye and the mouth, brass-edged
    face = head_hull()
    def cheek(P):
        Q = hinv(P)
        r = rim_d(P)
        y = Q[:, 1] + F(0.02)
        bottom = F(1.53) - F(0.6) * y * y - Q[:, 2]
        front = F(-0.165) + F(0.25) * np.clip(F(1.69) - Q[:, 2], 0, 0.14) - F(0.05) * np.clip(F(1.6) - Q[:, 2], 0, 0.1) - Q[:, 1]
        return np.maximum(np.maximum(F(0.1) - np.abs(Q[:, 0]), np.maximum(front, Q[:, 1] - F(0.08))), np.maximum(r - F(0.012), bottom))
    fd.add(Inter(Shell(face, 0.018, 0.012, pad=0.12), Func(cheek, HEAD_C - 0.4, HEAD_C + 0.3), 0.005), 0.0)
    def cheek_edge(P):
        Q = hinv(P)
        r = rim_d(P)
        y = Q[:, 1] + F(0.02)
        bottom = F(1.53) - F(0.6) * y * y - Q[:, 2]
        front = F(-0.165) + F(0.25) * np.clip(F(1.69) - Q[:, 2], 0, 0.14) - F(0.05) * np.clip(F(1.6) - Q[:, 2], 0, 0.1) - Q[:, 1]
        k = np.maximum(np.maximum(F(0.1) - np.abs(Q[:, 0]), np.maximum(front, Q[:, 1] - F(0.08))), np.maximum(r - F(0.012), bottom))
        return np.abs(k + F(0.007)) - F(0.007)
    fd.paint(Func(cheek_edge, HEAD_C - 0.4, HEAD_C + 0.3), 6)
    for sx in (-1, 1):
        o = hp((sx * 0.5, 0.0, 1.63))
        h, ok = ray_hit(Func(lambda P: face.eval(P) - F(0.03), HEAD_C - 0.5, HEAD_C + 0.5), [o], [v3((-sx, 0, 0))], tmax=0.6)
        if ok[0]:
            fd.add(Sphere(h[0], 0.011), 0.003, 6)
    # rivets round the bowl just above the rim, brass
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        dirv = v3((math.sin(a), -math.cos(a), 0.0))
        q = RIM_F + v3((0, (RIM_B[1] - RIM_F[1]) * (0.5 - 0.5 * math.cos(a)), 0))
        zq = RIM_F[2] + _RIM_SLOPE * (q[1] - RIM_F[1]) + 0.03
        o = hp(v3((0, 0.02, zq))) + dirv * 0.6
        h, ok = ray_hit(hull, [o], [-dirv], tmax=0.7)
        if ok[0] and _ear_cut(np.array([h[0]], F))[0] > 0.02:
            fd.add(Sphere(h[0] + dirv * 0.012, 0.0085), 0.003, 6)
    # the crest holder: a brass saddle along the top
    rid = crest_ridge(lift=0.006)
    fd.add(Chain(rid, [0.012] * len(rid), k=0.006), 0.006, 6)
    fd.add(Sphere(rid[0] + v3((0, -0.004, 0.004)), 0.017), 0.005, 6)


def crest_field():
    """A full red horsehair crest along the top of the helmet, front to back, a little longer at the back."""
    fd = Field("Crest")
    ridge = crest_ridge(lift=0.0)
    n = len(ridge)
    hairs = lambda P: F(0.0025) * NOISE(P * np.array([90, 14, 90], F)) + F(0.0015) * NOISE(P * F(130))
    pts, ws, ts, ns = [], [], [], []
    for k, p in enumerate(ridge):
        u = k / (n - 1)
        h = 0.075 + 0.04 * math.sin(min(1.0, u * 1.2) * math.pi * 0.5)
        out = norm(p - HELM_C)
        pts.append(p + out * (h * 0.5 + 0.014))
        ws.append(h * 0.5)
        ts.append(0.032 - 0.006 * u)
        ns.append(v3((1, 0, 0)))
    last = pts[-1]
    for j, (dy, dz) in enumerate(((0.035, -0.04), (0.055, -0.09))):
        pts.append(last + v3((0, dy, dz)))
        ws.append(ws[-1] * 0.8)
        ts.append(ts[-1] * 0.85)
        ns.append(v3((1, 0, 0)))
    fd.add(Lock(pts, ws, ts, ns, k=0.012, disp=hairs, disp_amp=0.004), 0.0)
    return fd


def hair_field():
    """Short cropped black hair showing under the helmet at the temples and the nape."""
    fd = Field("Hair")
    stub = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F)) + F(0.001) * NOISE(P * F(140))
    def band(P):
        Q = hinv(P)
        r = rim_d(P)
        return np.maximum(np.maximum(-r - F(0.075), r - F(0.012)), F(-0.075) - Q[:, 1])
    fd.add(Inter(Shell(Ellipsoid(HEAD_C, HEAD_RAD), 0.004, 0.01, pad=0.06, disp=stub, disp_amp=0.003),
                 Func(band, HEAD_C - 0.4, HEAD_C + 0.4), 0.006), 0.0)
    return fd


# ======================================================================================= lorica segmentata (iron, brass)
HOOP_TOP = 1.19
HOOP_BOT = 0.935
N_HOOPS = 6


def _hoops_disp(P):
    """The girth hoops: each band's lower edge stands proud of the one below it."""
    z = P[:, 2]
    h = F((HOOP_TOP - HOOP_BOT) / N_HOOPS)
    u = (z - F(HOOP_BOT)) / h
    fz = u - np.floor(u)
    return -F(0.006) * (F(1) - fz) + F(0.0008) * NOISE(P * F(50))


def _cut_top(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
    neck_z = F(1.48) - F(0.05) * front * np.exp(-(x / F(0.13)) ** 2) + F(0.3) * smoothstep(0.16, 0.24, np.abs(x))
    return z - neck_z


def _cut_arm(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    oval = ((y - F(0.06)) / F(0.17)) ** 2 + ((z - F(1.37)) / F(0.2)) ** 2 - F(1.0)
    return np.where(np.abs(x) > F(0.19), -oval * F(0.1), F(-1))


def shoulder_axis(side):
    sx = -1 if side == "R" else 1
    a = v3((sx * 0.12, 0.06, 1.47))
    b = J["shoulder_" + side] + v3((sx * 0.12, 0.0, -0.06))
    return a, norm(b - a)


def lorica(fd):
    base = cuirass_base()
    # the hoops round his belly
    def hoops_keep(P):
        return np.maximum(F(HOOP_BOT) - P[:, 2], P[:, 2] - F(HOOP_TOP + 0.01))
    fd.add(Inter(Shell(base, 0.032, 0.018, pad=0.12, disp=_hoops_disp, disp_amp=0.008), Func(hoops_keep, (-1, -1, 0.8), (1, 1, 1.3)), 0.004), 0.0)
    # the chest and back plates above them (three overlapping plates, front and back)
    def plates_disp(P):
        z = P[:, 2]
        u = (z - F(HOOP_TOP)) / F(0.085)
        fz = u - np.floor(u)
        return -F(0.005) * (F(1) - fz) + F(0.0008) * NOISE(P * F(50))
    def plates_keep(P):
        return np.maximum(np.maximum(F(HOOP_TOP - 0.01) - P[:, 2], _cut_top(P)), _cut_arm(P))
    fd.add(Inter(Shell(base, 0.03, 0.018, pad=0.12, disp=plates_disp, disp_amp=0.007), Func(plates_keep, (-1, -1, 1.1), (1, 1, 1.6)), 0.004), 0.004)
    # the shoulder guards: curved lames arching over each shoulder, stepping out along the arm
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        a, ax = shoulder_axis(side)
        sh = Field("ShoulderHull")
        sh.add(deltoid(side), 0.0)
        sh.add(traps(), 0.05)
        def lames(P, a=a, ax=ax):
            t = (P - a.astype(F)) @ ax.astype(F)
            u = t / F(0.05)
            fz = u - np.floor(u)
            return -F(0.006) * fz + F(0.0008) * NOISE(P * F(50))
        def keep(P, a=a, ax=ax, sx=sx):
            t = (P - a.astype(F)) @ ax.astype(F)
            below = F(1.33) + F(0.02) * np.clip(t, 0, 1) - P[:, 2]
            return np.maximum(np.maximum(-t, t - F(0.25)), below)
        fd.add(Inter(Shell(sh, 0.036, 0.016, pad=0.1, disp=lames, disp_amp=0.008), Func(keep, a - 0.5, a + 0.5), 0.004), 0.004)
    # brass: a hinge on each chest plate, buckles closing the hoops at the front, rivets along the plates' edges
    outer = Func(lambda P: base.eval(P, margin=0.08) - F(0.05), (-0.6, -0.6, 0.8), (0.6, 0.6, 1.6))
    for sx in (-1, 1):
        h, ok = ray_hit(outer, [v3((sx * 0.11, -0.7, 1.33))], [v3((0, 1, 0))], tmax=0.9)
        if ok[0]:
            c = h[0]
            fd.add(RoundBox(c, (0.026, 0.006, 0.034), 0.004), 0.002, 6)
            fd.add(Sphere(c + v3((0, -0.006, 0.02)), 0.007), 0.002, 6)
            fd.add(Sphere(c + v3((0, -0.006, -0.02)), 0.007), 0.002, 6)
    hh = (HOOP_TOP - HOOP_BOT) / N_HOOPS
    for k in range(N_HOOPS):
        z = HOOP_BOT + hh * (k + 0.55)
        for sx in (-1, 1):
            h, ok = ray_hit(outer, [v3((sx * 0.035, -0.7, z))], [v3((0, 1, 0))], tmax=0.9)
            if ok[0]:
                fd.add(RoundBox(h[0] + v3((0, -0.002, 0)), (0.014, 0.005, 0.011), 0.003), 0.002, 6)


def helmet_field():
    fd = Field("Helmet")
    helmet(fd)
    return fd


def iron_field():
    fd = Field("Iron")
    lorica(fd)
    return fd


# ======================================================================================= red tunic, white scarf
HEM_Z = 0.53


def tunic_base():
    b = Field("TunicBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(RoundCone((0, 0.035, 0.9), (0, 0.035, 0.45), 0.235, 0.31), 0.08)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.055)
        b.add(RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.098, 0.074), 0.05)
    return b


def _sleeve_cut(P):
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        c = lerp(sh, el, 0.42)
        along = (P - c.astype(F)) @ ax.astype(F)
        sx = -1 if side == "R" else 1
        out = np.maximum(out, np.where(P[:, 0] * F(sx) > F(0.25), along, F(-1.0)))
    return out


def tunic_hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(HEM_Z) + F(0.02) * np.cos(a * 2) + F(0.008) * NOISE(P * F(9))


def tunic_field():
    """A red wool tunic: its sleeves to below the shoulder guards, its skirt to just above the knee, gathered into folds
    below the armour (cut away where the armour covers it); a white scarf (label 5) knotted round his neck."""
    fd = Field("Tunic")
    base = tunic_base()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        k = smoothstep(0.92, 0.7, P[:, 2])
        return F(0.006) * np.sin(a * F(16) + F(0.8) * NOISE(P * F(3))) * k + F(0.0015) * NOISE(P * F(25))
    def keep(P):
        x, z = P[:, 0], P[:, 2]
        hidden = np.minimum(np.minimum(z - F(0.98), F(0.26) - np.abs(x)), F(1.42) - z)
        neck = z - (F(1.47) + F(0.3) * smoothstep(0.13, 0.21, np.abs(x)))
        return np.maximum(np.maximum(np.maximum(neck, _sleeve_cut(P)), tunic_hem(P) - z), hidden)
    fd.add(Inter(Shell(base, 0.016, 0.02, pad=0.1, disp=folds, disp_amp=0.006), Func(keep, (-1, -1, 0.4), (1, 1, 1.6)), 0.005), 0.0)
    # the scarf: a roll of white cloth round his neck above the armour, its ends tucked in at the front
    cl = lambda P: F(0.003) * NOISE(P * F(20)) + F(0.0015) * NOISE(P * F(55))
    pts = []
    for k in range(17):
        a = 2 * math.pi * k / 16
        pts.append(v3((0.122 * math.sin(a), 0.065 - 0.118 * math.cos(a), 1.465 + 0.012 * math.cos(a))))
    fd.add(Chain(pts, [0.032] * len(pts), k=0.01, disp=cl, disp_amp=0.004), 0.012, 5)
    fd.add(Ellipsoid(v3((0.0, -0.075, 1.43)), (0.045, 0.03, 0.05), disp=cl, disp_amp=0.004), 0.01, 5)
    return fd


# ======================================================================================= leather: belt, apron, boots
BELT_Z = 0.935


def apron_straps():
    """The six straps of the apron hanging from the belt in front: (x, top, bottom)."""
    return [(-0.1 + 0.04 * k, BELT_Z - 0.01, 0.62 - 0.015 * abs(k - 2.5)) for k in range(6)]


def leather_field():
    """The military belt (leather, brass plates: label 6) over the bottom hoop, the apron of six leather straps hanging
    in front from it, each studded with brass and ending in a brass pendant; hobnailed sandal-boots laced up the ankle;
    a wrap on his sword wrist."""
    fd = Field("Leather")
    kb = kilt_base()
    fd.add(Inter(Shell(kb, 0.066, 0.02, pad=0.1), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(0.026), (-1, -1, 0.8), (1, 1, 1.1)), 0.004), 0.0)
    def plates(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        s = np.mod(a * F(12 / (2 * math.pi)), F(1.0))
        return np.maximum(np.abs(P[:, 2] - F(BELT_Z)) - F(0.02), np.abs(s - F(0.5)) - F(0.36))
    fd.paint(Func(plates, (-1, -1, 0.8), (1, 1, 1.1)), 6)
    # the apron
    skirt = Field("ApronHull")
    skirt.add(RoundCone((0, 0.035, 0.95), (0, 0.035, 0.45), 0.26, 0.33), 0.0)
    for x, top, bot in apron_straps():
        def strap(P, x=x, top=top, bot=bot):
            return np.maximum(np.maximum(np.abs(P[:, 0] - F(x)) - F(0.012), np.maximum(P[:, 2] - F(top), F(bot) - P[:, 2])),
                              P[:, 1] - F(0.0))                      # (the front only: the shell wraps round behind him too)
        fd.add(Inter(Shell(skirt, 0.028, 0.008, pad=0.08), Func(strap, (x - 0.05, -0.6, bot - 0.02), (x + 0.05, 0.1, top + 0.02)), 0.003), 0.003)
        y0 = None
        for j in range(6):
            z = top - 0.03 - j * (top - bot - 0.06) / 5.0
            h, ok = ray_hit(Func(lambda P: skirt.eval(P) - F(0.04), (-0.6, -0.6, 0.3), (0.6, 0.2, 1.1)), [v3((x, -0.7, z))], [v3((0, 1, 0))], tmax=0.8)
            if ok[0]:
                fd.add(Sphere(h[0] + v3((0, 0.002, 0)), 0.0085), 0.002, 6)
                y0 = h[0]
        if y0 is not None:
            fd.add(Ellipsoid(y0 + v3((0, 0.0, -0.045)), (0.014, 0.006, 0.022)), 0.004, 6)
    # wrist wrap (sword hand)
    el, wr = J["elbow_R"], J["wrist_R"]
    ax = norm(wr - el)
    c = lerp(el, wr, 0.86)
    fd.add(Inter(Shell(_forearm("R"), 0.012, 0.014, pad=0.06), Func(lambda P: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.035), c - 0.25, c + 0.25), 0.004), 0.0)
    # caligae: a thick hobnailed sole, an open-work upper of straps over the foot, laced up the ankle
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.098)), (0.078, 0.155, 0.016), 0.01, R=Rz), 0.0)
        ft = Field("FootHull")
        foot(ft, side)
        for c2, rad in ((an + fwd * 0.15 + v3((0, 0, -0.07)), 0.018), (an + fwd * 0.1 + v3((0, 0, -0.055)), 0.018),
                        (an + fwd * 0.05 + v3((0, 0, -0.035)), 0.018), (an + fwd * 0.0 + v3((0, 0, -0.02)), 0.02)):
            fd.add(Inter(Shell(ft, 0.006, 0.01, pad=0.05), Func(lambda P, c=c2, fwd=fwd, rad=rad: np.abs((P - c.astype(F)) @ fwd.astype(F)) - F(rad * 0.6), c2 - 0.15, c2 + 0.15), 0.003), 0.002)
        shin = Field("ShinHull")
        shin.add(RoundCone(J["knee_" + side], an, 0.088, 0.058), 0.0)
        shin.add(Sphere(an + v3((0, 0.042, -0.05)), 0.058 * 1.04), 0.03)
        for zz in (0.07, 0.115, 0.16, 0.205):
            fd.add(Inter(Shell(shin, 0.006, 0.009, pad=0.05), Func(lambda P, zz=zz: np.abs(P[:, 2] - F(zz)) - F(0.008), an - 0.2, an + 0.2), 0.003), 0.002)
    return fd


# ======================================================================================= the gladius
GL_GRIP = 0.055           # fist centre -> the guard
GL_BLADE = 0.5            # the guard -> the point
GL_W = 0.028              # the blade's half width


def gladius_axis():
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t


def gladius_field():
    """A short sword: a straight steel blade with parallel edges and a short sharp point, a fuller down its middle
    (label 0); a bone grip ridged for the fingers (5); an oval brass guard and a ball pommel (6)."""
    fd = Field("Gladius")
    a0, ax = gladius_axis()
    wr, f, n, t = hand_frame("R")
    flat = norm(np.cross(ax, n))                 # the blade's flat faces this way (its edges lie along n)
    g0 = a0 + ax * GL_GRIP
    tip = g0 + ax * GL_BLADE
    def blade(P):
        q = P - g0.astype(F)
        u = q @ ax.astype(F)
        v = q @ n.astype(F)
        w = q @ flat.astype(F)
        L = F(GL_BLADE)
        taper = np.clip((L - u) / F(0.1), 0, 1)                          # the point: the last 0.1
        hw = F(GL_W) * (F(0.35) + F(0.65) * taper) * np.where(u < L - F(0.1), F(1.0), taper)
        th = F(0.0075) * (F(0.4) + F(0.6) * np.clip(F(1) - np.abs(v) / np.maximum(hw, F(1e-4)), 0, 1))
        d_w = np.abs(v) - hw
        d_t = np.abs(w) - th
        d_u = np.maximum(-u, u - L)
        return np.maximum(np.maximum(d_w, d_t), d_u)
    fd.add(Func(blade, np.minimum(g0, tip) - 0.06, np.maximum(g0, tip) + 0.06), 0.0)
    fd.sub(Chain([g0 + ax * 0.03, g0 + ax * (GL_BLADE - 0.12)], [0.004, 0.003], k=0.002), 0.002)       # the fuller
    # grip, guard, pommel
    fd.add(RoundCone(a0 - ax * 0.055, a0 + ax * 0.05, 0.018, 0.017), 0.0, 5)
    for k in range(4):
        fd.add(Torus(a0 + ax * (-0.04 + 0.027 * k), 0.018, 0.0045, R=rot_from_axes(z_axis=ax)), 0.003, 5)
    fd.add(Ellipsoid(a0 + ax * (GL_GRIP - 0.004), (0.045, 0.026, 0.012), R=rot_from_axes(z_axis=ax, x_axis=n)), 0.004, 6)
    fd.add(Sphere(a0 - ax * 0.072, 0.03), 0.006, 6)
    fd.add(Ellipsoid(a0 - ax * 0.058, (0.032, 0.022, 0.01), R=rot_from_axes(z_axis=ax, x_axis=n)), 0.004, 6)
    return fd


# ======================================================================================= the scutum
SC_W = 0.36               # half width along its curve
SC_H = 0.54               # half height
SC_RC = 0.58              # the radius it is curved to (round a vertical axis behind it)
SC_T = 0.028
SC_BACK = 0.055           # the grip -> the shield's back at the middle


def scutum_frame():
    """Rest pose: the grip (in the left fist, along the thumb axis U) runs across the shield's back behind the boss; its
    face points along the knuckles N; S = N x U is its height."""
    G, N, U, S = shield_frame()
    return G, N, U, S


def _sc_coords(P):
    """(u along the curve, h up its height, rho - radius) for points P (the shield's own cylindrical coordinates)."""
    G, N, U, S = scutum_frame()
    C = G + N * SC_BACK
    A0 = C - N * SC_RC
    q = P - A0.astype(F)
    h = q @ S.astype(F)
    rx = q @ U.astype(F)
    rn = q @ N.astype(F)
    rho = np.sqrt(rx * rx + rn * rn)
    a = np.arctan2(rx, rn)
    return a * F(SC_RC), h, rho - F(SC_RC)


def scutum_field():
    """A big curved rectangular shield: red-painted (label 0) with gold (5): a border line inset from the edge, a pair of
    wings spreading from the boss, four thunderbolts zigzagging out to the corners; a brass edging all round (6); an iron
    boss on a square plate in the middle (7); the bare wooden back and its grip (8)."""
    fd = Field("Shield")
    G, N, U, S = scutum_frame()
    C = G + N * SC_BACK
    paint = lambda P: F(0.0012) * NOISE(P * F(40))
    box_lo = np.minimum.reduce([C + U * su * 0.42 + S * ss * 0.6 + N * sn * 0.2 for su in (-1, 1) for ss in (-1, 1) for sn in (-1, 1)])
    box_hi = np.maximum.reduce([C + U * su * 0.42 + S * ss * 0.6 + N * sn * 0.2 for su in (-1, 1) for ss in (-1, 1) for sn in (-1, 1)])
    def rounded(P):
        u, h, d = _sc_coords(P)
        cr = F(0.045)
        qx = np.maximum(np.abs(u) - F(SC_W) + cr, 0)
        qy = np.maximum(np.abs(h) - F(SC_H) + cr, 0)
        corner = np.sqrt(qx * qx + qy * qy) - cr
        inside = np.maximum(np.abs(u) - F(SC_W), np.abs(h) - F(SC_H))
        plan = np.where((qx > 0) & (qy > 0), corner, inside)
        return np.maximum(plan, np.abs(d - F(SC_T * 0.5)) - F(SC_T * 0.5))
    fd.add(Func(rounded, box_lo, box_hi, disp=paint, disp_amp=0.002), 0.0)
    # the brass edging: a rim proud of the face and the back all round
    def edging(P):
        u, h, d = _sc_coords(P)
        cr = F(0.045)
        qx = np.maximum(np.abs(u) - F(SC_W) + cr, 0)
        qy = np.maximum(np.abs(h) - F(SC_H) + cr, 0)
        corner = np.sqrt(qx * qx + qy * qy) - cr
        inside = np.maximum(np.abs(u) - F(SC_W), np.abs(h) - F(SC_H))
        plan = np.where((qx > 0) & (qy > 0), corner, inside)
        return np.maximum(np.abs(plan + F(0.012)) - F(0.014), np.abs(d - F(SC_T * 0.5)) - F(SC_T * 0.5 + 0.006))
    fd.add(Func(edging, box_lo, box_hi), 0.004, 6)
    # the boss on its square plate
    face = C + N * SC_T
    fd.add(RoundBox(face + N * 0.003, (0.11, 0.11, 0.006), 0.004, R=rot_from_axes(z_axis=N, x_axis=U)), 0.004, 7)
    fd.add(Inter(Sphere(face - N * 0.03, 0.105), Plane(face + N * 0.006, -N), 0.004), 0.006, 7)
    for su in (-1, 1):
        for ss in (-1, 1):
            fd.add(Sphere(face + U * su * 0.088 + S * ss * 0.088 + N * 0.01, 0.009), 0.002, 6)
    # the grip behind the boss (across the back, in his fist) and its bar
    fd.add(RoundCone(G - U * 0.08, G + U * 0.08, 0.016, 0.016), 0.01, 8)
    fd.add(RoundBox(C - N * 0.004, (0.14, 0.03, 0.006), 0.004, R=rot_from_axes(z_axis=N, x_axis=U)), 0.004, 8)
    # gold paint on the face; the back bare wood
    def front(P):
        u, h, d = _sc_coords(P)
        return F(SC_T * 0.55) - d
    def border(P):
        u, h, d = _sc_coords(P)
        e = np.maximum(np.abs(u) - F(SC_W - 0.06), np.abs(h) - F(SC_H - 0.06))
        return np.maximum(np.abs(e) - F(0.008), front(P))
    fd.paint(Func(border, box_lo, box_hi), 5)
    def wings(P):
        u, h, d = _sc_coords(P)
        au = np.abs(u)
        # a wing: a curved feathered blade sweeping out and up from beside the boss
        t = np.clip((au - F(0.12)) / F(0.2), 0, 1)
        centre = F(0.02) + F(0.12) * t * t
        half = F(0.045) * (F(1) - t) + F(0.008)
        feathers = F(0.012) * np.abs(np.sin(au * F(55)))
        wing = np.maximum(np.abs(h + centre) - half + feathers * t, np.maximum(F(0.12) - au, au - F(0.32)))   # (its +h points down as held)
        return np.maximum(wing, front(P))
    fd.paint(Func(wings, box_lo, box_hi), 5)
    def bolts(P):
        u, h, d = _sc_coords(P)
        au, ah = np.abs(u), np.abs(h)
        out = F(1.0) * np.ones(len(P), F)
        pts = [(0.07, 0.1), (0.13, 0.2), (0.1, 0.24), (0.2, 0.42)]
        for i in range(len(pts) - 1):
            a, b = np.array(pts[i], F), np.array(pts[i + 1], F)
            ab = b - a
            tt = np.clip(((au - a[0]) * ab[0] + (ah - a[1]) * ab[1]) / float(ab @ ab), 0, 1)
            dx = au - (a[0] + tt * ab[0])
            dy = ah - (a[1] + tt * ab[1])
            w = F(0.014) * (F(1) - F(0.6) * (F(i) + tt) / F(3))
            out = np.minimum(out, np.sqrt(dx * dx + dy * dy) - w)
        return np.maximum(out, front(P))
    fd.paint(Func(bolts, box_lo, box_hi), 5)
    fd.paint(Func(lambda P: _sc_coords(P)[2] - F(SC_T * 0.3), box_lo, box_hi), 8)
    return fd


# ======================================================================================= build config
GLB_NAME = "legionary"
ROOT_NAME = "LegionaryHQ"
TEX_PREFIX = "legion"
MAT_NAME = "LegionMat"
MESH_NAME = "Legionary"
BASE_MODULE = "legionary_base"
ANIM_MODULE = "anim_legionary"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Crest", "Helmet", "Iron", "Tunic", "Leather", "Gladius", "Shield"]
REGION_PARTS = ("Skin", "Helmet", "Iron", "Tunic", "Leather", "Gladius", "Shield")
BLACK_HAIR = {"name": "HQ_LegionHair", "base": (0.08, 0.065, 0.06), "hi": (0.28, 0.23, 0.21), "low": (0.035, 0.03, 0.028),
              "streak": (0.05, 0.04, 0.035), "tint": (0.16, 0.11, 0.09)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_LegionSkin", "base": (0.78, 0.53, 0.37), "ruddy": (0.82, 0.47, 0.35), "lips": (0.64, 0.37, 0.31),
                      "brow": ((0.06, 0.045, 0.04), (0.14, 0.1, 0.08)),
                      "extra": ((LASH, (0.05, 0.035, 0.03), 0.5), (STUBBLE, (0.34, 0.26, 0.23), 0.6, 0.45), (SCAR, (0.88, 0.58, 0.5), 0.75))}),
    "Hair": ("hair", BLACK_HAIR),
    "Crest": ("hair", {"name": "HQ_LegionCrest", "base": (0.68, 0.1, 0.06), "hi": (0.96, 0.34, 0.18), "low": (0.32, 0.04, 0.03),
                       "streak": (0.5, 0.06, 0.04), "tint": (0.82, 0.22, 0.08)}),
    "Helmet": ("roman_steel", {"name": "HQ_Galea"}),
    "Iron": ("roman_steel", {"name": "HQ_Lorica"}),
    "Tunic": ("wool", {"name": "HQ_LegionTunic", "base": (0.66, 0.1, 0.07), "border": (0.94, 0.92, 0.86), "stripe": (0.12, 0.1, 0.1)}),
    "Leather": ("leather_dyed", {"name": "HQ_LegionLeather", "base": (0.32, 0.19, 0.1)}),
    "Gladius": ("gladius", {"name": "HQ_Gladius"}),
    "Shield": ("scutum", {"name": "HQ_Scutum"}),
}
LOW_TARGETS = {"Skin": 6400, "Hair": 500, "Crest": 700, "Teeth": 60, "Helmet": 2400, "Iron": 3400, "Tunic": 1500, "Leather": 1800,
               "Gladius": 420, "Shield": 1400}
AO_EXCLUDE = ["Gladius", "Shield"]
BAKE_APART = (["Shield"], (3.0, 0.0, 0.0))     # (at rest the shield passes through his left thigh: baked apart from him)


def prop_bones():
    return []                       # the gladius and the shield are rigid in the fists


def iron_weights(ob, skin_ob, arm):
    """The lorica from the torso; the shoulder lames follow the clavicles and the upper arms."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"})
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        w = None
        if abs(p.x) > 0.2 and p.z > 1.3:                                     # the shoulder lames
            side = "R" if p.x < 0 else "L"
            t = max(0.0, min(1.0, (abs(p.x) - 0.2) / 0.2))
            w = {"clavicle." + side: 1.0 - 0.45 * t, "upperarm." + side: 0.45 * t}
        if w is not None:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, w)


def hair_weights(ob, skin_ob, arm):
    groups = {}
    z1 = hp((0, 0, 1.6))[2]
    for v in ob.data.vertices:
        p = v.co
        t = max(0.0, min(1.0, (z1 - p.z) / 0.2))
        _blend_add(ob, groups, v.index, {"head": 1.0 - 0.6 * t, "neck": 0.6 * t})


def leather_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"forearm.R", "hand.R", "shin.R", "shin.L", "foot.R", "foot.L"})
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.y < 0.0 and 0.55 < p.z < BELT_Z - 0.02 and abs(p.x) < 0.16:              # the apron swings from the belt
            t = max(0.0, min(1.0, (BELT_Z - p.z) / 0.3))
            w = {"root": 1.0 - 0.4 * t, "thigh.R": 0.2 * t, "thigh.L": 0.2 * t}
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Crest": ("rigid", "head"), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Helmet": ("rigid", "head"), "Iron": ("custom", iron_weights), "Leather": ("custom", leather_weights),
        "Tunic": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L"},
                  {"thigh.R": 0.45, "thigh.L": 0.45}),
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
    if part == "Skin" and abs(c.x) > 0.6 and c.z < 1.0:
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0026 if fine else 0.0036),
        ("Crest", crest_field(), 0.0026 if fine else 0.0036),
        ("Helmet", helmet_field(), 0.0022 if fine else 0.0032),
        ("Iron", iron_field(), 0.0024 if fine else 0.0034),
        ("Tunic", tunic_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Gladius", gladius_field(), 0.0016 if fine else 0.0022),
        ("Shield", scutum_field(), 0.0026 if fine else 0.0034),
    ]
