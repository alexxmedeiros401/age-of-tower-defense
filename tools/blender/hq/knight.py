"""The Knight (HQ tower, Medieval Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A knight in full plate, his face hidden: a flat-topped great helm of polished steel (a keel down its face, a vision slit
across it, a brass cross over the face plate, breaths pierced in a cross below the slit on his right, rivets round its
foot), a torse of twisted blue and yellow cloth round its crown and a plume of blue feathers sweeping back from it. A
gorget of lames round his neck; big layered pauldrons; rerebraces, couters with fan wings, vambraces; gauntlets with
flared cuffs and lamed fingers; cuisses, poleyns with fan wings, greaves, lamed sabatons; under it all a breastplate.
Over the breastplate a blue tabard to mid-thigh with a yellow cross on breast and back and a yellow border, split at
the sides, girt with a sword belt (brass buckle and studs); the hem of a mail skirt shows under it. A great sword in
both hands: a long straight double-edged blade with a fuller, long straight quillons, a grip bound in red leather long
enough for both hands, a wheel pommel; brass on the hilt.

His body, hands and fists are the Spear Guard's (spear.py), hidden in the armour. The sword is rigid in his right fist
(the blade along the fist's thumb axis, its edge toward his knuckles); the left hand takes the grip below it ("frame"
aims and IK in anim_knight.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import spear as sp
from spear import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R,
                   eye_c, smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, torso_prims, traps, neck_prim,
                   deltoid, eyes_field, teeth_field, cuirass_base, kilt_base, _forearm, TORSO, TORSO_Z, torso_bones,
                   body_parts)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= the great helm
HELM_C = v3((0.0, 0.0, 1.7))
HELM_RX, HELM_RY = 0.23, 0.262   # (round his ears and his nose, with room to spare)
HELM_BOT = 1.4                   # its foot, resting on the gorget
HELM_TOP = 1.95                  # the top plate's rim (it domes a little above)
SLIT_Z = 1.682                   # the vision slit (at his eyes)


def _helm_rho(P):
    q = P - HELM_C.astype(F)
    return np.sqrt((q[:, 0] / F(HELM_RX)) ** 2 + (q[:, 1] / F(HELM_RY)) ** 2)


def helm_dist(P):
    """The helm's outer surface: an upright oval drum with a keel down the face, a low dome on top."""
    q = P - HELM_C.astype(F)
    a = np.arctan2(q[:, 0], -q[:, 1])                                     # 0 = straight ahead
    keel = F(0.022) * np.exp(-(a / F(0.32)) ** 2)                         # the face plate's two halves meet in a ridge
    taper = F(0.012) * smoothstep(1.6, 1.46, P[:, 2])                     # drawn in a little at the foot
    side = (_helm_rho(P) - F(1.0)) * F(HELM_RX) - keel + taper
    top = P[:, 2] - (F(HELM_TOP) + F(0.035) * np.clip(F(1) - _helm_rho(P) ** 2, 0, 1))
    bot = F(HELM_BOT) - P[:, 2]
    q2 = np.stack([np.maximum(side + F(0.012), 0), np.maximum(top + F(0.012), 0)], 1)
    inside = np.minimum(np.maximum(side, top), 0)
    return np.maximum(np.sqrt((q2 ** 2).sum(1)) + inside - F(0.012), bot)


def helm_field():
    """Polished steel (label 0): the helm, its vision slit and breaths cut through, a brass cross over the face plate
    (6), rivets round its foot and round the top plate's seam (6)."""
    fd = Field("Helm")
    lo, hi = HELM_C - v3((0.34, 0.38, 0.36)), HELM_C + v3((0.34, 0.38, 0.36))
    hammer = lambda P: F(0.0007) * NOISE(P * F(45))
    fd.add(Func(helm_dist, lo, hi, disp=hammer, disp_amp=0.001), 0.0)
    # the vision slit: across the front, between the brass bands
    def slit(P):
        q = P - HELM_C.astype(F)
        a = np.arctan2(q[:, 0], -q[:, 1])
        return np.maximum(np.maximum(np.abs(P[:, 2] - F(SLIT_Z)) - F(0.009), np.abs(a) - F(1.05)), -q[:, 1] - F(0.4))
    fd.sub(Func(slit, lo, hi), 0.003)
    # breaths: small holes in a cross on his right, below the slit
    outer = Func(lambda P: helm_dist(P), lo, hi)
    for (dx, dz) in ((0, 0), (0.025, 0), (-0.025, 0), (0, 0.025), (0, -0.025), (0, -0.05), (0.05, 0)):
        o = v3((-0.075 + dx, -0.6, 1.585 + dz))
        h, ok = ray_hit(outer, [o], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            fd.sub(Sphere(h[0], 0.0065), 0.002)
    # the brass cross: a band down the keel, a band along each side of the slit
    def cross_v(P):
        q = P - HELM_C.astype(F)
        a = np.arctan2(q[:, 0], -q[:, 1])
        return np.maximum(np.abs(a) - F(0.09), np.maximum(F(HELM_BOT + 0.03) - P[:, 2], P[:, 2] - F(HELM_TOP - 0.02)))
    def cross_h(P):
        q = P - HELM_C.astype(F)
        a = np.arctan2(q[:, 0], -q[:, 1])
        return np.maximum(np.abs(np.abs(P[:, 2] - F(SLIT_Z)) - F(0.021)) - F(0.0095), np.abs(a) - F(1.1))
    fd.add(Inter(Shell(Func(helm_dist, lo, hi), 0.002, 0.007), Func(lambda P: np.minimum(cross_v(P), cross_h(P)), lo, hi), 0.002), 0.002, 6)
    fd.sub(Func(slit, lo, hi), 0.003)
    # rivets: round the foot and round the top seam
    for z0, n in ((HELM_BOT + 0.022, 18), (HELM_TOP - 0.015, 16)):
        for k in range(n):
            a = 2 * math.pi * (k + 0.5) / n
            d = v3((math.sin(a), -math.cos(a), 0.0))
            o = v3((HELM_C[0], HELM_C[1], z0)) + d * 0.5
            h, ok = ray_hit(outer, [o], [-d], tmax=0.6)
            if ok[0]:
                fd.add(Sphere(h[0], 0.0075), 0.002, 6)
    return fd


def crest_field():
    """A torse of twisted cloth round the helm's crown (blue, label 0, and yellow, 5) and a plume of blue feathers
    sweeping up and back from its top."""
    fd = Field("Crest")
    zc = HELM_TOP + 0.012
    def torse(P):
        q = P - HELM_C.astype(F)
        rho = _helm_rho(P)
        r = (rho - F(1.0)) * F(HELM_RX)
        return np.sqrt(r * r + (P[:, 2] - F(zc)) ** 2) - F(0.024)
    lo, hi = HELM_C - v3((0.3, 0.3, -0.1)), HELM_C + v3((0.3, 0.3, 0.4))
    twist = lambda P: F(0.004) * np.abs(np.sin(np.arctan2(P[:, 0], -P[:, 1]) * F(9) + (P[:, 2] - F(zc)) * F(80)))
    fd.add(Func(torse, lo, hi, disp=twist, disp_amp=0.005), 0.0)
    fd.paint(Func(lambda P: np.sin(np.arctan2(P[:, 0], -P[:, 1]) * F(9) + (P[:, 2] - F(zc)) * F(80)), lo, hi), 5)
    # the plume: seven feathers from a socket on the top plate, rising and sweeping back
    base = v3((0.0, 0.06, HELM_TOP + 0.04))
    fd.add(Sphere(base, 0.03), 0.01)
    barbs = lambda P: F(0.0018) * NOISE(P * np.array([120, 120, 40], F))
    for k in range(7):
        s = (k - 3) / 3.0
        out = norm(v3((s * 0.5, 0.35 + 0.15 * (1 - abs(s)), 1.0)))
        back = norm(v3((s * 0.35, 1.0, -0.1)))
        p0 = base + out * 0.02
        p1 = p0 + out * 0.13
        p2 = p1 + norm(out + back * 0.9) * 0.13
        p3 = p2 + norm(back + v3((0, 0, -0.25))) * 0.12
        nrm = norm(np.cross(back, v3((1, 0, 0)))) if abs(s) < 0.9 else v3((0, 0, 1))
        fd.add(Lock([p0, p1, p2, p3], [0.02, 0.032, 0.03, 0.012], [0.006, 0.006, 0.005, 0.003], [nrm] * 4, k=0.008,
                    disp=barbs, disp_amp=0.002), 0.008)
    return fd


# ======================================================================================= plate harness
def _band(a, b, t0, t1, extra=0.0):
    """< 0 between fractions t0..t1 along a->b (the parts of a limb a plate covers)."""
    ax = norm(b - a)
    L = float(np.linalg.norm(b - a))
    def fn(P):
        t = ((P - a.astype(F)) @ ax.astype(F)) / F(L)
        return np.maximum(F(t0) - t, t - F(t1)) * F(L) - F(extra)
    return fn


def _lames(a, ax, step, depth=0.005):
    """Displacement: overlapping lames down a limb (each one's lower edge proud of the next)."""
    def fn(P):
        u = ((P - a.astype(F)) @ ax.astype(F)) / F(step)
        fz = u - np.floor(u)
        return -F(depth) * fz + F(0.0006) * NOISE(P * F(50))
    return fn


def _wing(fd, c, n, r, label=0):
    """A fan-shaped wing (a couter's or a poleyn's), a shallow cup of plate facing along n, a rib round its rim."""
    R = rot_from_axes(z_axis=n)
    fd.add(Inter(Shell(Sphere(c - n * 0.16, 0.18), 0.0, 0.006), Cylinder(c, r, 0.2, R=R), 0.002), 0.004, label)
    fd.add(Torus(c - n * (0.16 - math.sqrt(max(0.18 ** 2 - r * r, 0.0))) + n * 0.002, r - 0.004, 0.0045, R=R), 0.002, label)


def plate_field():
    """Polished steel (label 0), brass rivets and buckles (6), red-dyed leather straps (5)."""
    fd = Field("Plate")
    hammer = lambda P: F(0.0007) * NOISE(P * F(45))
    # breastplate and backplate (under the tabard: they show at its armholes and its neck)
    cb = cuirass_base()
    def bp_keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        top = z - (F(1.47) + F(0.3) * smoothstep(0.17, 0.25, np.abs(x)))
        arm = np.where(np.abs(x) > F(0.18), -(((y - F(0.06)) / F(0.17)) ** 2 + ((z - F(1.37)) / F(0.21)) ** 2 - F(1.0)) * F(0.1), F(-1.0))
        return np.maximum(np.maximum(F(0.9) - z, top), arm)
    fd.add(Inter(Shell(cb, 0.034, 0.016, pad=0.12, disp=hammer, disp_amp=0.001), Func(bp_keep, (-1, -1, 0.8), (1, 1, 1.7)), 0.004), 0.0)
    # the gorget: lames round his neck, flaring over his collarbones
    gb = Field("GorgetBase")
    gb.add(neck_prim(), 0.0)
    gb.add(traps(), 0.05)
    nk = v3((0, 0.06, 1.38))
    fd.add(Inter(Shell(gb, 0.045, 0.012, pad=0.1, disp=_lames(v3((0, 0, 1.52)), v3((0, 0, -1)), 0.03, 0.004), disp_amp=0.005),
                 Func(lambda P: np.maximum(np.maximum(F(1.34) - P[:, 2], P[:, 2] - F(1.52)),
                                           np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F(0.05)) ** 2) - F(0.24)), (-0.4, -0.4, 1.2), (0.4, 0.4, 1.6)),
                 0.004), 0.004)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        # pauldron: layered lames over the shoulder, stepping down the arm, a rolled edge at the top
        ph = Field("PauldronHull")
        ph.add(deltoid(side), 0.0)
        ph.add(Ellipsoid(sh + v3((sx * -0.08, 0.0, 0.05)), (0.12, 0.13, 0.08)), 0.05)
        out_ax = norm(v3((sx * 0.55, 0.0, -0.84)))
        top = sh + v3((sx * -0.06, 0.0, 0.14))
        def p_keep(P, sh=sh, sx=sx, top=top, out_ax=out_ax):
            t = (P - top.astype(F)) @ out_ax.astype(F)
            inner = F(0.13) - P[:, 0] * F(sx)                                    # not over his neck
            return np.maximum(np.maximum(-t - F(0.02), t - F(0.27)), inner)
        fd.add(Inter(Shell(ph, 0.085, 0.014, pad=0.1, disp=_lames(top, out_ax, 0.055, 0.007), disp_amp=0.008),
                     Func(p_keep, sh - 0.45, sh + 0.45), 0.004), 0.004)
        fd.add(Inter(Shell(ph, 0.095, 0.016, pad=0.1), Func(lambda P, top=top, out_ax=out_ax, sx=sx: np.maximum(
            np.abs((P - top.astype(F)) @ out_ax.astype(F) + F(0.012)) - F(0.012), F(0.13) - P[:, 0] * F(sx)), sh - 0.45, sh + 0.45), 0.003), 0.004)
        # rerebrace, couter (with its fan wing on the outside), vambrace
        arm_u = RoundCone(sh, el, 0.095, 0.072)
        fd.add(Inter(Shell(arm_u, 0.022, 0.011, pad=0.06, disp=hammer, disp_amp=0.001), Func(_band(sh, el, 0.42, 0.86), sh - 0.4, sh + 0.4), 0.003), 0.003)
        cop = Sphere(el + v3((0, 0.025, 0)), 0.055)
        fd.add(Inter(Shell(cop, 0.026, 0.012, pad=0.05), Func(_band(sh, wr, 0.4, 0.62), el - 0.3, el + 0.3), 0.004), 0.004)
        ax_ue = norm(el - sh)
        out = norm(np.cross(ax_ue, v3((0, 1, 0)))) * sx
        out = norm(out - ax_ue * (out @ ax_ue))
        _wing(fd, el + v3((0, 0.02, 0)) + out * 0.072, out, 0.052)
        arm_f = RoundCone(el, wr, 0.07, 0.054)
        fd.add(Inter(Shell(arm_f, 0.021, 0.011, pad=0.06, disp=hammer, disp_amp=0.001), Func(_band(el, wr, 0.16, 0.8), el - 0.4, el + 0.4), 0.003), 0.003)
        # gauntlet: a flared cuff and plates over the back of the hand and the fingers
        ax_f = norm(wr - el)
        fd.add(Inter(Shell(RoundCone(wr - ax_f * 0.11, wr + ax_f * 0.01, 0.083, 0.06), 0.006, 0.01, pad=0.05),
                     Func(lambda P, wr=wr, ax_f=ax_f: np.abs((P - (wr - ax_f * 0.05).astype(F)) @ ax_f.astype(F)) - F(0.06), wr - 0.25, wr + 0.25), 0.003), 0.004)
        hh = Field("HandHull")
        hand(hh, side)
        hwr, hf, hn, ht = hand_frame(side)
        fd.add(Shell(hh, 0.006, 0.008, pad=0.04, disp=_lames(hwr, hf, 0.03, 0.004), disp_amp=0.005), 0.003)
        # cuisse (from under the tabard to the knee), poleyn with its fan wing, greave, lamed sabaton
        thigh = RoundCone(hip, kn, 0.135, 0.088)
        fd.add(Inter(Shell(thigh, 0.024, 0.012, pad=0.06, disp=hammer, disp_amp=0.001), Func(_band(hip, kn, 0.3, 0.86), hip - 0.4, hip + 0.4), 0.003), 0.003)
        knee = Sphere(kn + v3((0, -0.03, 0.0)), 0.068)
        fd.add(Inter(Shell(knee, 0.026, 0.012, pad=0.05), Func(_band(hip, an, 0.42, 0.6), kn - 0.3, kn + 0.3), 0.004), 0.004)
        _wing(fd, kn + v3((sx * 0.085, -0.02, 0.0)), norm(v3((sx * 1.0, -0.35, 0.0))), 0.05)
        shin = Field("Shin")
        shin.add(RoundCone(kn, an, 0.084, 0.056), 0.0)
        shin.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.095, 0.092, 0.14), R=rot_from_axes(z_axis=an - kn)), 0.043)
        fd.add(Inter(Shell(shin, 0.022, 0.012, pad=0.06, disp=hammer, disp_amp=0.001), Func(_band(kn, an, 0.18, 0.92), kn - 0.4, kn + 0.4), 0.003), 0.003)
        ft = Field("FootHull")
        foot(ft, side)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(Inter(Shell(ft, 0.014, 0.012, pad=0.05, disp=_lames(an, fwd, 0.04, 0.005), disp_amp=0.006),
                     Func(lambda P: F(0.02) - P[:, 2], an - 0.4, an + 0.4), 0.003), 0.0)
        fd.add(RoundBox(an + fwd * 0.07 + v3((0, 0, -0.1)), (0.072, 0.16, 0.012), 0.009, R=Rz), 0.006)
    return fd


# ======================================================================================= tabard, mail skirt, belt
TAB_HEM = 0.6
BELT_Z = 0.94


def tabard_base():
    b = Field("TabardBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(RoundCone((0, 0.035, 0.92), (0, 0.035, 0.5), 0.245, 0.3), 0.08)
    return b


def tabard_hem(P):
    return F(TAB_HEM) + F(0.012) * NOISE(P * F(6))


def tabard_field():
    """Blue wool (label 0), a yellow border round its hem, armholes and neck (5), a yellow cross on breast and back (6);
    split at the sides below the belt, hanging in a few soft folds."""
    fd = Field("Tabard")
    base = tabard_base()
    folds = lambda P: F(0.004) * np.sin(np.arctan2(P[:, 0], -(P[:, 1] - F(0.035))) * F(7) + F(0.6) * NOISE(P * F(3))) \
        * smoothstep(0.92, 0.7, P[:, 2]) + F(0.0012) * NOISE(P * F(25))
    def cut(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        neck = z - (F(1.47) - F(0.06) * np.exp(-(x / F(0.1)) ** 2) * (y < F(0.05)) + F(0.3) * smoothstep(0.2, 0.28, np.abs(x)))
        arm = np.where(np.abs(x) > F(0.17), -(((y - F(0.06)) / F(0.19)) ** 2 + ((z - F(1.34)) / F(0.24)) ** 2 - F(1.0)) * F(0.1), F(-1.0))
        slit = np.where((z < F(0.88)) & (np.abs(y - F(0.035)) < F(0.05)), F(0.05) - np.abs(y - F(0.035)), F(-1.0))
        return np.maximum(np.maximum(np.maximum(neck, arm), tabard_hem(P) - z), slit)
    fd.add(Inter(Shell(base, 0.068, 0.012, pad=0.12, disp=folds, disp_amp=0.006), Func(cut, (-1, -1, 0.4), (1, 1, 1.7)), 0.004), 0.0)
    def edge(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        hem = P[:, 2] - (tabard_hem(P) + F(0.032))
        arm = np.where(np.abs(x) > F(0.17), np.abs((((y - F(0.06)) / F(0.19)) ** 2 + ((z - F(1.34)) / F(0.24)) ** 2) - F(1.08)) - F(0.08), F(1.0))
        slit = np.where(z < F(0.88), np.abs(np.abs(y - F(0.035)) - F(0.07)) - F(0.025), F(1.0))
        return np.minimum(np.minimum(hem, arm), slit)
    fd.paint(Func(edge, (-1, -1, 0.4), (1, 1, 1.7)), 5)
    def cross(P):
        x, z = P[:, 0], P[:, 2]
        v = np.maximum(np.abs(x) - F(0.045), np.maximum(F(0.7) - z, z - F(1.38)))
        h = np.maximum(np.abs(z - F(1.17)) - F(0.045), np.abs(x) - F(0.2))
        return np.minimum(v, h)
    fd.paint(Func(cross, (-1, -1, 0.4), (1, 1, 1.7)), 6)
    return fd


def mail_field():
    """The hem of a mail skirt under the tabard (iron rings, label 0; a band of brass rings at its edge, 5)."""
    fd = Field("Mail")
    kb = kilt_base()
    fd.add(Inter(Shell(kb, 0.05, 0.01, pad=0.1, disp=lambda P: F(0.0015) * NOISE(P * F(20)), disp_amp=0.002),
                 Func(lambda P: np.maximum(F(TAB_HEM - 0.07) - P[:, 2], P[:, 2] - F(0.86)), (-1, -1, 0.3), (1, 1, 1.0)), 0.004), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - F(TAB_HEM - 0.05), (-1, -1, 0.3), (1, 1, 1.0)), 5)
    return fd


def leather_field():
    """The sword belt over the tabard (leather, label 0) with a brass buckle and studs (6)."""
    fd = Field("Leather")
    bb = Field("BeltBase")
    tp = torso_prims()
    bb.add(tp[4][0], 0.0)
    bb.add(tp[5][0], tp[5][1])
    bb.add(RoundCone((0, 0.035, 0.92), (0, 0.035, 0.5), 0.245, 0.3), 0.08)
    fd.add(Inter(Shell(bb, 0.088, 0.02, pad=0.12), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z) + F(0.03) * np.abs(P[:, 0])) - F(0.026),
                                                       (-1, -1, 0.8), (1, 1, 1.1)), 0.005), 0.0)
    outer = Func(lambda P: bb.eval(P, margin=0.12) - F(0.1), (-1, -1, 0.7), (1, 1, 1.2))
    h, ok = ray_hit(outer, [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    c = h[0] if ok[0] else v3((0, -0.3, BELT_Z))
    fd.add(RoundBox(c + v3((0, -0.006, 0)), (0.036, 0.008, 0.03), 0.006), 0.003, 6)
    fd.sub(RoundBox(c + v3((0, -0.016, 0)), (0.022, 0.008, 0.016), 0.004), 0.002)
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        if abs(math.sin(a)) < 0.2 and math.cos(a) > 0.9:
            continue
        d = v3((math.sin(a), -math.cos(a), 0.0))
        z = BELT_Z - 0.03 * abs(math.sin(a)) * 0.3
        h, ok = ray_hit(outer, [v3((0, 0.035, z)) + d * 0.6], [-d], tmax=0.7)
        if ok[0]:
            fd.add(Sphere(h[0], 0.009), 0.002, 6)
    return fd


# ======================================================================================= the great sword
GUARD_UP = 0.07           # right fist centre -> the cross-guard
BLADE_LEN = 1.0
GRIP_DOWN = 0.25          # right fist centre -> the grip's lower end (the left hand takes it at LEFT_DOWN)
LEFT_DOWN = 0.135
POMMEL_DOWN = 0.29


def sword_frame():
    """Rest pose: the sword in the right fist: T along the blade (the fist's thumb axis), E toward the edge the knuckles
    face (the cross-guard lies along it), W = T x E across the blade's flat."""
    wr, f, n, t = hand_frame("R")
    G = fist_center("R")
    T = norm(t)
    E = norm(f - T * (f @ T))
    W = np.cross(T, E)
    return G, T, E, W


def sword_field():
    """A steel blade with a fuller (label 0), the cross-guard and the wheel pommel in brass (6), the grip bound in red
    leather (5)."""
    fd = Field("Sword")
    G, T, E, W = sword_frame()
    b0 = G + T * (GUARD_UP + 0.012)
    tip = b0 + T * BLADE_LEN
    def blade(P):
        q = P - b0.astype(F)
        s = q @ T.astype(F)
        e = q @ E.astype(F)
        w = q @ W.astype(F)
        k = np.clip(s / F(BLADE_LEN), 0, 1)
        half = F(0.028) * (F(1) - F(0.4) * k) * np.clip((F(1) - k) / F(0.1), 0, 1) ** 0.6 + F(0.002)
        thick = F(0.0065) * (F(1) - np.abs(e) / np.maximum(half, F(1e-3))) + F(0.0012)
        fuller = F(0.0022) * np.exp(-(e / F(0.007)) ** 2) * (k < F(0.7))
        dw = np.abs(w) - (thick - fuller)
        de = np.abs(e) - half
        ds = np.maximum(-s, s - F(BLADE_LEN))
        return np.maximum(np.maximum(dw * F(0.8), de), ds)
    lo = np.minimum(b0, tip) - 0.1
    hi = np.maximum(b0, tip) + 0.1
    fd.add(Func(blade, lo, hi), 0.0)
    # the cross-guard: long straight quillons along the edge direction, a little swelling at the ends
    gc = G + T * GUARD_UP
    fd.add(Chain([gc - E * 0.16, gc, gc + E * 0.16], [0.011, 0.014, 0.011], k=0.004), 0.004, 6)
    for s in (-1, 1):
        fd.add(Sphere(gc + E * (s * 0.165), 0.016), 0.004, 6)
    fd.add(RoundBox(gc + T * 0.008, (0.024, 0.012, 0.02), 0.005, R=rot_from_axes(z_axis=T, x_axis=E)), 0.004, 6)    # the langet
    # the grip: long enough for both fists, bound in red leather (a spiral wrap)
    g0, g1 = G - T * GRIP_DOWN, G + T * (GUARD_UP - 0.01)
    wrap = lambda P: F(0.0015) * np.abs(np.sin(((P - G.astype(F)) @ T.astype(F)) * F(160)))
    fd.add(RoundCone(g0, g1, 0.0175, 0.0165, disp=wrap, disp_amp=0.002), 0.004, 5)
    # the wheel pommel
    pc = G - T * POMMEL_DOWN
    fd.add(Cylinder(pc, 0.034, 0.024, rr=0.008, R=rot_from_axes(z_axis=W)), 0.004, 6)
    fd.add(Sphere(pc + W * 0.012, 0.012), 0.004, 6)
    fd.add(Sphere(pc - W * 0.012, 0.012), 0.004, 6)
    fd.add(RoundCone(g0, pc + T * 0.02, 0.016, 0.014), 0.004, 6)
    return fd


def sword_tip():
    G, T, E, W = sword_frame()
    return G + T * (GUARD_UP + 0.012 + BLADE_LEN)


# ======================================================================================= build config
GLB_NAME = "knight"
ROOT_NAME = "KnightHQ"
TEX_PREFIX = "knight"
MAT_NAME = "KnightMat"
MESH_NAME = "Knight"
BASE_MODULE = "knight_base"
ANIM_MODULE = "anim_knight"
PARTS = ["Skin", "Helm", "Crest", "Plate", "Tabard", "Mail", "Leather", "Sword"]
REGION_PARTS = ("Skin", "Helm", "Crest", "Plate", "Tabard", "Mail", "Leather", "Sword")
BLUE = (0.14, 0.27, 0.62)
YELLOW = (0.9, 0.68, 0.16)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_KnightSkin"}),
    "Helm": ("roman_steel", {"name": "HQ_KnightSteel", "base": (0.46, 0.47, 0.5)}),
    "Crest": ("wool", {"name": "HQ_KnightCrest", "base": BLUE, "border": YELLOW, "stripe": YELLOW}),
    "Plate": ("roman_steel", {"name": "HQ_KnightSteel", "base": (0.46, 0.47, 0.5)}),
    "Tabard": ("wool", {"name": "HQ_KnightTabard", "base": BLUE, "border": YELLOW, "stripe": YELLOW}),
    "Mail": ("mail", {"name": "HQ_KnightMail", "base": (0.56, 0.57, 0.61)}),
    "Leather": ("leather_dyed", {"name": "HQ_KnightLeather", "base": (0.3, 0.18, 0.1), "dyed": (0.5, 0.1, 0.07)}),
    "Sword": ("roman_steel", {"name": "HQ_GreatSword", "base": (0.52, 0.54, 0.58)}),
}
LOW_TARGETS = {"Skin": 1500, "Helm": 2200, "Crest": 1400, "Plate": 7400, "Tabard": 2400, "Mail": 700, "Leather": 900,
               "Sword": 900}
AO_EXCLUDE = ["Sword"]


def prop_bones():
    return []                       # the sword is rigid in the right fist


def weight_rules():
    body = {"root", "spine", "chest", "neck", "head", "clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R",
            "forearm.L", "hand.R", "hand.L", "thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}
    return {
        "Helm": ("rigid", "head"), "Crest": ("rigid", "head"),
        "Plate": ("transfer", body, None),
        "Tabard": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Mail": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.5, "thigh.L": 0.5}),
        "Leather": ("transfer", TORSO, None),
        "Sword": ("rigid", "hand.R"),
    }


def uv_boost(c, part):
    if part == "Skin":
        return 0.25                 # (hidden inside the armour)
    if part == "Helm":
        return 1.5
    if part == "Sword":
        return 0.8
    return 1.0


def warm_points():
    return [(hp((0, -0.238, 1.616)), 0.05, 0.5)]


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.004 if fine else 0.006),
        ("Helm", helm_field(), 0.0022 if fine else 0.003),
        ("Crest", crest_field(), 0.0022 if fine else 0.003),
        ("Plate", plate_field(), 0.0024 if fine else 0.0034),
        ("Tabard", tabard_field(), 0.0026 if fine else 0.0036),
        ("Mail", mail_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Sword", sword_field(), 0.0016 if fine else 0.0022),
    ]
