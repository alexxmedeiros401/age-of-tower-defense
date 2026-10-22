"""Sir Aldric, Knight Commander (HQ hero, Medieval Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A knight commander in his fifties, bare-headed in his harness: a weathered square face, heavy grey brows, deep-set
eyes, a straight strong nose, an old scar through his left brow down onto his cheek; grey hair cropped short and
receding at the temples; a short grey beard and moustache trimmed close. His mail coif is pushed back off his head and
lies bunched round his neck and over his shoulders. Under it all his plate harness (the Knight's: knight.py) over a
mail shirt; over the plate a crimson surcoat to the knee with a gold border, a gold crown over an upright sword on his
breast, split before and behind; a sword belt with a gold buckle; a long dark blue cloak hanging from his shoulders to
his calves, fastened across his chest by two gold rosettes and a gold chain.

In his right fist his longsword: a long straight blade with a fuller, a gold cross-guard with down-turned quillons, a
grip bound in red leather, a gold wheel pommel; on his left arm, in his fist by its grip, a heater shield: crimson
with the same gold crown and sword, an iron rim.

His body, hands and fists are the Spear Guard's (spear.py), with his own head. The sword is rigid in his right fist (the
blade along the fist's thumb axis), the shield in his left ("frame" aims in anim_aldric.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import spear as sp
import knight as kn
import crossbowman as xb
from spear import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R,
                   eye_c, smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, torso_prims, traps, neck_prim,
                   deltoid, eyes_field, teeth_field, _forearm, warm_points, TORSO, TORSO_Z, torso_bones, head_hull,
                   shield_frame)

SCAR = 10


# ======================================================================================= head
def head(fd):
    """A weathered square face: a firm jaw under the beard, heavy brows, deep-set eyes, a straight strong nose, a scar
    through his left brow onto his cheek, a level mouth."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.055, 1.586), (0.145, 0.134, 0.128)), 0.07, SKIN)
    fd.add(E((0, -0.136, 1.498), (0.09, 0.07, 0.068)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.11, -0.118, 1.632), 0.047), 0.05, SKIN)                               # cheekbones
        fd.add(S((sx * 0.126, -0.045, 1.556), 0.053), 0.05, SKIN)
        pts = [hp((sx * 0.152, -0.055, 1.744)), hp((sx * 0.116, -0.13, 1.754)), hp((sx * 0.06, -0.172, 1.754)), hp((0.0, -0.18, 1.752))]
        fd.add(Chain(pts, [hr(0.012), hr(0.021), hr(0.024), hr(0.024)], k=hr(0.02)), hr(0.032), SKIN)    # the brow ridge
        fd.add(S((sx * 0.062, -0.192, 1.592), 0.018), hr(0.02), SKIN)                            # lines from the nose
    for sx in (-1, 1):                                                                          # heavy grey brows
        pts = [hp((sx * 0.024, -0.21, 1.75)), hp((sx * 0.066, -0.204, 1.762)), hp((sx * 0.11, -0.183, 1.767)), hp((sx * 0.152, -0.142, 1.758))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.011), hr(0.013), hr(0.011), hr(0.006)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.019), hr(0.021), hr(0.018), hr(0.01)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0063)), Plane(ec + v3((0, 0, hr(0.014))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.005)), Plane(ec + v3((0, 0, -hr(0.021))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.011))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        crow = [ec + v3((sx * hr(0.05), hr(0.006), hr(0.008))), ec + v3((sx * hr(0.064), hr(0.016), hr(0.012)))]
        fd.sub(Chain(crow, [hr(0.0016), hr(0.001)], k=hr(0.002)), hr(0.002))                     # crow's feet
    fd.add(RoundCone(hp((0, -0.184, 1.724)), hp((0, -0.236, 1.636)), hr(0.017), hr(0.022)), hr(0.017), SKIN)
    fd.add(S((0, -0.238, 1.624), 0.026), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.03, -0.213, 1.608), 0.019), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.015, -0.229, 1.595)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    scar = [hp((0.046, -0.204, 1.79)), hp((0.062, -0.202, 1.745)), hp((0.08, -0.18, 1.69)), hp((0.092, -0.16, 1.645))]
    fd.sub(Chain(scar, [hr(0.003), hr(0.0035), hr(0.003), hr(0.002)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(scar, [hr(0.007), hr(0.008), hr(0.007), hr(0.005)], k=hr(0.004)), SCAR)
    slot = [hp((-0.058, -0.168, 1.548)), hp((-0.03, -0.192, 1.546)), hp((0, -0.198, 1.546)), hp((0.03, -0.192, 1.546)), hp((0.058, -0.168, 1.548))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.046, -0.168, 1.54), (-0.025, -0.186, 1.535), (0, -0.19, 1.533), (0.025, -0.186, 1.535), (0.046, -0.168, 1.54)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.0075), hr(0.0082), hr(0.0075), hr(0.005)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.176, 0.035, 1.66)), v3((0.025, 0.045, 0.058)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        fd.add(RoundCone(sh, el, 0.095, 0.072), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.025, 0)), (0.085, 0.088, 0.125), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)
        fd.add(RoundCone(el, wr, 0.07, 0.054), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.09, 0.08, 0.13), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.055), 0.028, SKIN)
        hand(fd, side)
        hip, knee, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, knee, 0.135, 0.088), 0.065, SKIN)
        fd.add(Ellipsoid(lerp(hip, knee, 0.42) + v3((0, -0.022, 0)), (0.122, 0.115, 0.185), R=rot_from_axes(z_axis=knee - hip)), 0.048, SKIN)
        fd.add(Sphere(knee + v3((0, -0.03, 0.0)), 0.068), 0.038, SKIN)
        fd.add(RoundCone(knee, an, 0.084, 0.056), 0.038, SKIN)
        fd.add(Ellipsoid(lerp(knee, an, 0.3) + v3((0, 0.03, 0)), (0.095, 0.092, 0.14), R=rot_from_axes(z_axis=an - knee)), 0.043, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= hair, beard
def hair_field():
    """Grey hair cropped short, receding at the temples (a widow's peak), the ears clear."""
    fd = Field("Hair")
    stub = lambda P: F(0.0022) * NOISE(P * np.array([80, 80, 30], F)) + F(0.001) * NOISE(P * F(140))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        line = F(1.79) + F(0.04) * smoothstep(0.02, 0.1, ax) - F(0.012) * np.exp(-(x / F(0.02)) ** 2)   # a widow's peak
        front = np.where(y < F(-0.05), line - z, F(-1.0))
        ears = np.where((ax > F(0.14)) & (z < F(1.71)) & (y < F(0.1)), F(0.02), F(-1.0))
        nape = F(1.56) - z
        return np.maximum(np.maximum(front, ears), nape)
    fd.add(Inter(Shell(Ellipsoid(HEAD_C, HEAD_RAD), 0.006, 0.012, pad=0.06, disp=stub, disp_amp=0.003),
                 Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.006), 0.0)
    return fd


def beard_field():
    """A short grey beard trimmed close on his jaw and chin, and a moustache (the Crossbowman's, crossbowman.py)."""
    return xb.beard_field()


# ======================================================================================= the mail coif, pushed back
def coif_field():
    """His mail coif pushed back off his head: the hood lies bunched behind his neck and the mail falls over his
    shoulders and the top of his chest (iron rings, label 0; a band of brass rings at its edge, 5)."""
    fd = Field("Coif")
    rings = lambda P: F(0.0014) * NOISE(P * F(30)) + F(0.003) * np.sin(P[:, 2] * F(90) + NOISE(P * F(6)))
    base = Field("CoifBase")
    base.add(neck_prim(), 0.0)
    base.add(traps(), 0.06)
    for side in ("R", "L"):
        base.add(deltoid(side), 0.055)
    base.add(Ellipsoid((0, 0.05, 1.24), (0.27, 0.2, 0.24)), 0.07)
    def keep(P):
        z = P[:, 2]
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.05)))
        hem = F(1.3) + F(0.035) * np.cos(a * 2) + F(0.01) * np.sin(a * 13)
        # the opening round his neck only: away from it the line climbs clear of the mail (cut level, it opened a hole
        # in the top of each shoulder, and his bare shoulders showed through)
        top = F(1.52) + F(0.3) * smoothstep(0.14, 0.2, np.sqrt(P[:, 0] ** 2 + (F(0.6) * (P[:, 1] - F(0.05))) ** 2))
        return np.maximum(hem - z, z - top)
    fd.add(Inter(Shell(base, 0.072, 0.014, pad=0.1, disp=rings, disp_amp=0.004), Func(keep, (-0.6, -0.5, 1.1), (0.6, 0.5, 1.7)), 0.006), 0.0)
    # the hood bunched behind his neck, in folds
    for k in range(5):
        a = math.radians(-60 + 30 * k)
        c = v3((math.sin(a) * 0.11, 0.08 + math.cos(a) * 0.07, 1.5 - 0.012 * abs(k - 2)))
        fd.add(Ellipsoid(c, (0.055, 0.045, 0.04), R=euler(0, 0, a), disp=rings, disp_amp=0.004), 0.025)
    fd.add(Torus(v3((0.0, 0.04, 1.49)), 0.105, 0.03, R=rot_from_axes(z_axis=norm(v3((0, 0.35, 1.0))))), 0.03)
    fd.paint(Func(lambda P: P[:, 2] - (F(1.33) + F(0.035) * np.cos(np.arctan2(P[:, 0], -(P[:, 1] - F(0.05))) * 2)), (-0.6, -0.5, 1.1), (0.6, 0.5, 1.7)), 5)
    return fd


# ======================================================================================= surcoat, cloak, belt, gold
SUR_HEM = 0.47
BELT_Z = 0.94


def surcoat_field():
    """Crimson wool (label 0), a gold border round its hem, armholes and neck (5), a gold crown over an upright sword on
    his breast (6); split before and behind below the belt; a few folds."""
    fd = Field("Surcoat")
    base = kn.tabard_base()
    base.add(RoundCone((0, 0.035, 0.6), (0, 0.035, 0.38), 0.3, 0.33), 0.08)
    folds = lambda P: F(0.005) * np.sin(np.arctan2(P[:, 0], -(P[:, 1] - F(0.035))) * F(7) + F(0.6) * NOISE(P * F(3))) \
        * smoothstep(0.92, 0.7, P[:, 2]) + F(0.0012) * NOISE(P * F(25))
    def hem(P):
        return F(SUR_HEM) + F(0.012) * NOISE(P * F(6))
    def cut(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        neck = z - (F(1.47) - F(0.06) * np.exp(-(x / F(0.1)) ** 2) * (y < F(0.05)) + F(0.3) * smoothstep(0.2, 0.28, np.abs(x)))
        arm = np.where(np.abs(x) > F(0.17), -(((y - F(0.06)) / F(0.19)) ** 2 + ((z - F(1.34)) / F(0.24)) ** 2 - F(1.0)) * F(0.1), F(-1.0))
        slit = np.where((z < F(0.8)) & (np.abs(x) < F(0.035)), F(0.035) - np.abs(x), F(-1.0))
        return np.maximum(np.maximum(np.maximum(neck, arm), hem(P) - z), slit)
    fd.add(Inter(Shell(base, 0.064, 0.012, pad=0.12, disp=folds, disp_amp=0.006), Func(cut, (-1, -1, 0.3), (1, 1, 1.7)), 0.004), 0.0)
    def edge(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        h = P[:, 2] - (hem(P) + F(0.034))
        arm = np.where(np.abs(x) > F(0.17), np.abs((((y - F(0.06)) / F(0.19)) ** 2 + ((z - F(1.34)) / F(0.24)) ** 2) - F(1.08)) - F(0.08), F(1.0))
        slit = np.where(z < F(0.8), np.abs(np.abs(x) - F(0.05)) - F(0.016), F(1.0))
        return np.minimum(np.minimum(h, arm), slit)
    fd.paint(Func(edge, (-1, -1, 0.3), (1, 1, 1.7)), 5)
    fd.paint(Func(breast_arms, (-0.6, -0.6, 0.8), (0.6, 0.1, 1.5)), 6)
    return fd


def arms_2d(u, v):
    """His arms as a 2D distance (< 0 inside), unit scale: an upright sword (its point at v = -0.2, the pommel at 0.15)
    under a crown (its band at v = 0.2, three points with balls above it); about 0.5 tall."""
    blade = np.maximum(np.abs(u) - F(0.018) * np.clip((v + F(0.2)) / F(0.06), 0, 1), np.maximum(F(-0.2) - v, v - F(0.08)))
    guard = np.maximum(np.abs(u) - F(0.07), np.abs(v - F(0.08)) - F(0.012))
    grip = np.maximum(np.abs(u) - F(0.012), np.maximum(F(0.08) - v, v - F(0.13)))
    pommel = np.sqrt(u * u + (v - F(0.14)) ** 2) - F(0.018)
    d = np.minimum(np.minimum(blade, guard), np.minimum(grip, pommel))
    band = np.maximum(np.abs(u) - F(0.095), np.abs(v - F(0.2)) - F(0.016))
    d = np.minimum(d, band)
    for c, top in ((-0.07, 0.25), (0.0, 0.262), (0.07, 0.25)):
        k = np.clip((v - F(0.214)) / F(top - 0.214), 0, 1)
        spike = np.maximum(np.abs(u - F(c)) - F(0.022) * (F(1) - k), np.maximum(F(0.21) - v, v - F(top)))
        ball = np.sqrt((u - F(c)) ** 2 + (v - F(top + 0.006)) ** 2) - F(0.013)
        d = np.minimum(d, np.minimum(spike, ball))
    return d


def breast_arms(P):
    """The arms on his breast (front only): 0.27 tall, centred at z 1.15."""
    sc = F(0.55)
    u, v = P[:, 0] / sc, (P[:, 2] - F(1.15)) / sc + F(0.03)
    return np.maximum(arms_2d(u, v) * sc, P[:, 1] + F(0.05))


def cloak_field():
    """A long dark blue wool cloak (label 0) hanging from his shoulders behind him to his calves, open in front, its edge
    bordered in gold (5); folds falling straight."""
    fd = Field("Cloak")
    hull = Field("CloakHull")
    for p, k in torso_prims():
        hull.add(p, k)
    hull.add(traps(), 0.06)
    for side in ("R", "L"):
        hull.add(deltoid(side), 0.06)
    hull.add(RoundCone((0, 0.12, 0.95), (0, 0.2, 0.3), 0.3, 0.38), 0.12)
    def fall(P):
        z = P[:, 2]
        a = np.arctan2(P[:, 0], P[:, 1] - F(0.0))
        drop = np.clip((F(1.3) - z) / F(0.9), 0, 1)
        return F(0.012) * np.sin(a * F(8) + F(0.5) * NOISE(P * F(2))) * drop + F(0.0015) * NOISE(P * F(20))
    def edge_y(z):
        return F(0.02) - F(0.08) * smoothstep(1.25, 1.45, z)                     # (it wraps a little over the shoulders)
    def keep(P):
        y, z = P[:, 1], P[:, 2]
        return np.maximum(np.maximum(edge_y(z) - y, F(0.28) + F(0.02) * NOISE(P * F(4)) - z), z - F(1.47))
    fd.add(Inter(Shell(hull, 0.09, 0.014, pad=0.14, disp=fall, disp_amp=0.014), Func(keep, (-0.8, -0.6, 0.2), (0.8, 0.8, 1.6)), 0.006), 0.0)
    fd.paint(Func(lambda P: np.minimum(np.abs(P[:, 1] - edge_y(P[:, 2])) - F(0.025), P[:, 2] - F(0.33)),
                  (-0.8, -0.6, 0.2), (0.8, 0.8, 1.6)), 5)
    return fd


def clasp_points():
    """The cloak's two gold rosettes on the front of his shoulders."""
    return [v3((sx * 0.21, -0.07, 1.4)) for sx in (-1, 1)]


def gold_field():
    """Gold: the cloak's two rosettes and the chain between them across his chest; the belt's buckle."""
    fd = Field("Gold")
    for c in clasp_points():
        fd.add(Cylinder(c, 0.03, 0.012, rr=0.004, R=rot_from_axes(z_axis=v3((0, -1, 0.2)))), 0.0)
        for k in range(8):
            a = 2 * math.pi * k / 8
            fd.add(Sphere(c + v3((math.cos(a) * 0.026, -0.006, math.sin(a) * 0.026)), 0.009), 0.003)
        fd.add(Sphere(c + v3((0, -0.01, 0)), 0.012), 0.003)
    a, b = clasp_points()
    mid = (a + b) / 2 + v3((0, -0.05, -0.1))
    pts = []
    for k in range(17):
        t = k / 16
        p = a * (1 - t) ** 2 + mid * 2 * t * (1 - t) + b * t * t
        pts.append(p)
    for i in range(0, 16):
        c = (pts[i] + pts[i + 1]) / 2
        d = norm(pts[i + 1] - pts[i])
        fd.add(Torus(c, 0.012, 0.0035, R=rot_from_axes(z_axis=v3((0, -1, 0)) if i % 2 else norm(np.cross(d, v3((0, -1, 0)))))), 0.0)
    bc = belt_front()
    fd.add(RoundBox(bc + v3((0, -0.006, 0)), (0.036, 0.008, 0.03), 0.006), 0.0)
    fd.sub(RoundBox(bc + v3((0, -0.014, 0)), (0.022, 0.008, 0.016), 0.004), 0.002)
    return fd


def _belt_base():
    bb = Field("BeltBase")
    tp = torso_prims()
    bb.add(tp[4][0], 0.0)
    bb.add(tp[5][0], tp[5][1])
    bb.add(RoundCone((0, 0.035, 0.92), (0, 0.035, 0.5), 0.245, 0.3), 0.08)
    return bb


def belt_front():
    bb = _belt_base()
    outer = Func(lambda P: bb.eval(P, margin=0.12) - F(0.1), (-1, -1, 0.7), (1, 1, 1.2))
    h, ok = ray_hit(outer, [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    return h[0] if ok[0] else v3((0, -0.3, BELT_Z))


def leather_field():
    """The sword belt over the surcoat (leather, label 0) with studs (6)."""
    fd = Field("Leather")
    bb = _belt_base()
    fd.add(Inter(Shell(bb, 0.09, 0.02, pad=0.12), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z) + F(0.03) * np.abs(P[:, 0])) - F(0.024),
                                                     (-1, -1, 0.8), (1, 1, 1.1)), 0.005), 0.0)
    return fd


# ======================================================================================= the longsword
GUARD_UP = 0.065
BLADE_LEN = 0.86
GRIP_DOWN = 0.12
POMMEL_DOWN = 0.14


def sword_frame():
    """Rest pose: the sword in the right fist: T along the blade (the fist's thumb axis), E toward the edge the knuckles
    face (the cross-guard lies along it), W = T x E across the blade's flat."""
    return kn.sword_frame()


def sword_field():
    """A steel blade with a fuller (label 0), a gold cross-guard with down-turned quillons and a gold wheel pommel (6),
    the grip bound in red leather (5)."""
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
        half = F(0.026) * (F(1) - F(0.45) * k) * np.clip((F(1) - k) / F(0.12), 0, 1) ** 0.6 + F(0.002)
        thick = F(0.006) * (F(1) - np.abs(e) / np.maximum(half, F(1e-3))) + F(0.0012)
        fuller = F(0.002) * np.exp(-(e / F(0.006)) ** 2) * (k < F(0.65))
        dw = np.abs(w) - (thick - fuller)
        de = np.abs(e) - half
        ds = np.maximum(-s, s - F(BLADE_LEN))
        return np.maximum(np.maximum(dw * F(0.8), de), ds)
    fd.add(Func(blade, np.minimum(b0, tip) - 0.1, np.maximum(b0, tip) + 0.1), 0.0)
    gc = G + T * GUARD_UP
    fd.add(Chain([gc - E * 0.12 + T * 0.025, gc - E * 0.1, gc, gc + E * 0.1, gc + E * 0.12 + T * 0.025], [0.009, 0.011, 0.013, 0.011, 0.009], k=0.004), 0.004, 6)
    for s in (-1, 1):
        fd.add(Sphere(gc + E * (s * 0.122) + T * 0.028, 0.013), 0.004, 6)
    g0, g1 = G - T * GRIP_DOWN, G + T * (GUARD_UP - 0.01)
    wrap = lambda P: F(0.0015) * np.abs(np.sin(((P - G.astype(F)) @ T.astype(F)) * F(160)))
    fd.add(RoundCone(g0, g1, 0.0165, 0.0155, disp=wrap, disp_amp=0.002), 0.004, 5)
    pc = G - T * POMMEL_DOWN
    fd.add(Cylinder(pc, 0.03, 0.022, rr=0.007, R=rot_from_axes(z_axis=W)), 0.004, 6)
    fd.add(Sphere(pc + W * 0.011, 0.011), 0.004, 6)
    fd.add(Sphere(pc - W * 0.011, 0.011), 0.004, 6)
    return fd


def sword_tip():
    G, T, E, W = sword_frame()
    return G + T * (GUARD_UP + 0.012 + BLADE_LEN)


# ======================================================================================= the heater shield
SH_W = 0.26               # half width at the top
SH_TOP = 0.3              # the grip -> the top edge (along S)
SH_BOT = 0.36             # the grip -> the point (along -S)
SH_RC = 0.75              # curved round a vertical axis behind it
SH_T = 0.024
SH_BACK = 0.05            # the grip -> the shield's back at the middle


def heater_frame():
    """Rest pose: the grip in the left fist along the thumb axis U (across the shield), its face along the knuckles N,
    S = N x U up its height."""
    return shield_frame()


def _sh_coords(P):
    """(u across, h up its height, distance off the curved face) in the shield's own coordinates. Its top is toward -S:
    held with the fist palm down (the grip's thumb end inward), S points down."""
    G, N, U, S = heater_frame()
    C = G + N * SH_BACK
    A0 = C - N * SH_RC
    q = P - A0.astype(F)
    h = -(q @ S.astype(F))
    rx = q @ U.astype(F)
    rn = q @ N.astype(F)
    rho = np.sqrt(rx * rx + rn * rn)
    a = np.arctan2(rx, rn)
    return a * F(SH_RC), h + F((G - A0) @ S), rho - F(SH_RC)


def _heater_plan(u, h):
    """< 0 inside the heater's outline: straight sides down a third of the way, then curving in to the point."""
    au = np.abs(u)
    top = h - F(SH_TOP)
    shoulder = F(SH_TOP - 0.22)
    side = au - F(SH_W)
    # the lower curve: an arc from (SH_W, shoulder) to the point (0, -SH_BOT)
    R = F(0.502)                                               # (the two arcs meet at the point)
    cx = F(SH_W) - R
    cy = shoulder
    curve = np.sqrt((au - cx) ** 2 + (h - cy) ** 2) - R
    lower = np.where(h < shoulder, curve, side)
    return np.maximum(np.maximum(lower, top), F(-SH_BOT) - h)


def heater_field():
    """A heater shield of boards: its face crimson (label 5), the arms in gold (7), an iron rim (6), the bare wooden back
    (0) and its grip."""
    fd = Field("Shield")
    G, N, U, S = heater_frame()
    C = G + N * SH_BACK
    corners = [C + U * su * 0.32 + S * ss * 0.42 + N * sn * 0.1 for su in (-1, 1) for ss in (-1, 1) for sn in (-1, 1)]
    lo, hi = np.minimum.reduce(corners), np.maximum.reduce(corners)
    paint = lambda P: F(0.0012) * NOISE(P * F(40))
    def body(P):
        u, h, d = _sh_coords(P)
        return np.maximum(_heater_plan(u, h), np.abs(d - F(SH_T * 0.5)) - F(SH_T * 0.5))
    fd.add(Func(body, lo, hi, disp=paint, disp_amp=0.002), 0.0)
    def rim(P):
        u, h, d = _sh_coords(P)
        pl = _heater_plan(u, h)
        return np.maximum(np.abs(pl + F(0.01)) - F(0.012), np.abs(d - F(SH_T * 0.5)) - F(SH_T * 0.5 + 0.005))
    fd.add(Func(rim, lo, hi), 0.004, 6)
    fd.add(RoundCone(G - U * 0.07, G + U * 0.07, 0.016, 0.016), 0.01, 0)
    fd.add(RoundBox(C - N * 0.004, (0.12, 0.03, 0.006), 0.004, R=rot_from_axes(z_axis=N, x_axis=U)), 0.004, 0)
    def front(P):
        u, h, d = _sh_coords(P)
        return F(SH_T * 0.55) - d
    fd.paint(Func(front, lo, hi), 5)
    def arms(P):
        u, h, d = _sh_coords(P)
        sc = F(0.9)
        return np.maximum(arms_2d(u / sc, h / sc + F(0.01)) * sc, front(P))
    fd.paint(Func(arms, lo, hi), 7)
    return fd


# ======================================================================================= painting
def warm_points():
    return sp.warm_points()


# ======================================================================================= build config
GLB_NAME = "aldric"
ROOT_NAME = "HeroAldricHQ"
TEX_PREFIX = "hero"
MAT_NAME = "AldricMat"
MESH_NAME = "Aldric"
BASE_MODULE = "aldric_base"
ANIM_MODULE = "anim_aldric"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Plate", "Chainmail", "Coif", "Surcoat", "Cloak", "Leather", "Gold",
         "Sword", "Shield"]
REGION_PARTS = ("Skin", "Plate", "Coif", "Surcoat", "Cloak", "Leather", "Gold", "Sword", "Shield")
CRIMSON = (0.62, 0.08, 0.07)
GOLD_C = (0.9, 0.68, 0.2)
GREY_HAIR = {"name": "HQ_AldricHair", "base": (0.58, 0.57, 0.56), "hi": (0.86, 0.85, 0.83), "low": (0.32, 0.31, 0.3),
             "streak": (0.46, 0.45, 0.44), "tint": (0.66, 0.64, 0.62)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_AldricSkin", "base": (0.8, 0.58, 0.46), "ruddy": (0.84, 0.48, 0.4), "lips": (0.66, 0.38, 0.34),
                      "brow": ((0.5, 0.49, 0.48), (0.74, 0.72, 0.7)),
                      "extra": ((LASH, (0.2, 0.17, 0.15), 0.5), (SCAR, (0.86, 0.6, 0.55), 0.45))}),
    "Hair": ("hair", GREY_HAIR),
    "Beard": ("hair", dict(GREY_HAIR, name="HQ_AldricBeard")),
    "Plate": ("roman_steel", {"name": "HQ_AldricSteel", "base": (0.5, 0.51, 0.54)}),
    "Chainmail": ("mail", {"name": "HQ_AldricMail", "base": (0.5, 0.51, 0.55)}),
    "Coif": ("mail", {"name": "HQ_AldricMail", "base": (0.5, 0.51, 0.55)}),
    "Surcoat": ("wool", {"name": "HQ_AldricSurcoat", "base": CRIMSON, "border": GOLD_C, "stripe": GOLD_C}),
    "Cloak": ("wool", {"name": "HQ_AldricCloak", "base": (0.1, 0.14, 0.32), "border": GOLD_C, "stripe": GOLD_C}),
    "Leather": ("leather_dyed", {"name": "HQ_AldricLeather", "base": (0.26, 0.15, 0.09)}),
    "Gold": ("gold", {"name": "HQ_AldricGold"}),
    "Sword": ("roman_steel", {"name": "HQ_AldricSword", "base": (0.56, 0.58, 0.62)}),
    "Shield": ("siege", {"name": "HQ_AldricShield", "wood": (0.5, 0.35, 0.21), "wood2": (0.36, 0.25, 0.14), "red": CRIMSON,
                         "blue": GOLD_C, "metal": "iron"}),
}
LOW_TARGETS = {"Skin": 5200, "Teeth": 60, "Hair": 1000, "Beard": 900, "Plate": 6000, "Chainmail": 1400, "Coif": 2200,
               "Surcoat": 2600, "Cloak": 2400, "Leather": 600, "Gold": 900, "Sword": 800, "Shield": 1200}
AO_EXCLUDE = ["Sword", "Shield", "Gold"]


def prop_bones():
    return []


def cloak_weights(ob, skin_ob, arm):
    """The cloak hangs from his shoulders: its top rides the clavicles and the chest, its length the spine, a little of
    the thighs' swing at its hem."""
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        sd = "R" if p.x < 0 else "L"
        t = max(0.0, min(1.0, (1.42 - p.z) / 0.5))
        low = max(0.0, min(1.0, (0.85 - p.z) / 0.5))
        w = {"clavicle." + sd: 0.5 * (1 - t), "chest": 0.5 * (1 - t) + 0.6 * t * (1 - low), "spine": 0.4 * t * (1 - low) + 0.6 * low,
             "thigh." + sd: 0.25 * low, "root": 0.15 * low}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    body = {"root", "spine", "chest", "neck", "head", "clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R",
            "forearm.L", "hand.R", "hand.L", "thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Beard": ("rigid", "head"),
        "Plate": ("transfer", body, None), "Chainmail": ("transfer", body, None),
        "Coif": ("transfer", {"neck", "chest", "clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"}, {"upperarm.R": 0.4, "upperarm.L": 0.4}),
        "Surcoat": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Cloak": ("custom", cloak_weights),
        "Leather": ("transfer", TORSO, None), "Gold": ("transfer", TORSO | {"clavicle.R", "clavicle.L"}, None),
        "Sword": ("rigid", "hand.R"), "Shield": ("rigid", "hand.L"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Shield":
        return 1.2
    if part == "Chainmail":
        return 0.5
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.003),
        ("Beard", beard_field(), 0.0022 if fine else 0.003),
        ("Plate", kn.plate_field(), 0.0024 if fine else 0.0034),
        ("Chainmail", kn.chainmail_field(), 0.003 if fine else 0.004),
        ("Coif", coif_field(), 0.0026 if fine else 0.0036),
        ("Surcoat", surcoat_field(), 0.0026 if fine else 0.0036),
        ("Cloak", cloak_field(), 0.0028 if fine else 0.0038),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Gold", gold_field(), 0.0016 if fine else 0.0024),
        ("Sword", sword_field(), 0.0016 if fine else 0.0022),
        ("Shield", heater_field(), 0.0024 if fine else 0.0032),
    ]
