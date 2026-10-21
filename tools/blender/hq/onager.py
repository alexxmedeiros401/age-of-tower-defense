"""The Onager (HQ tower, Classical Age): the Roman one-armed torsion engine with a sling, lying on its timber frame on the
ground, and the legion artilleryman who works it. Rest pose: he stands in an A-pose facing -Y (the way it shoots), feet
at z = 0, the engine on his left (+X); it is wound (its arm drawn back and down, the stone in the sling's pouch resting
on the board at the frame's back end).

Him: a lean, hard-faced Roman, clean-shaven (a blue-black shadow on his jaw), short dark hair combed forward to a
straight fringe, a high-bridged Roman nose, a cleft chin, a cocky half-smile; his left eye narrowed in a gunner's squint,
the right brow cocked. A knee-length tunic of undyed wool with two red stripes (clavi) over the shoulders and red bands
at the hem, a red neck scarf (focale) knotted at his throat, the military belt with brass plates and a short apron of
studded straps, hobnailed sandal-boots laced up the ankle, leather wrist wraps. A wooden mallet with iron bands, rigid
in his right fist.

The engine: two massive side beams lying on the ground joined by cross beams, a raised spring block on each over the
twisted sinew skein (big iron washers with their levers on the outside), the throwing arm through the skein (rope-bound
at its foot, iron bands, an iron cap and the release prong at its tip) and the sling hanging from the tip: two ropes to
a leather pouch with the stone in it, lying on a board at the back of the frame. In front the buffer: two posts braced
forward, a cross bar and a great stuffed sack lashed to it (the arm slams into it). At the back the windlass (rope on
the drum, an iron ratchet wheel and a crank on his side) and its rope up to a ring under the arm; the trigger: a pawl in
the ratchet held by a pin on a post, which he knocks out with the mallet (the drum runs free and the arm flies). Behind
him a heap of stone balls on a straw mat and two clay fire pots stopped with straw.

Painted labels on the engine (material `siege`, iron fittings): 0 wood with the grain along Y, 10 along X, 11 along Z;
5 Roman red; 6 iron; 8 rope and sinew; 9 leather."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import torsion as _t
from torsion import (J, SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD,
                     EYE_R, eye_c, smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, traps, neck_prim,
                     deltoid, upper_arm, eyes_field, teeth_field, skull, _forearm, _sleeve, mallet_frame, MALLET_L,
                     MALLET_BUTT, MALLET_HEAD, tbeam, GRAIN, box, stone_ball, TORSO, TORSO_Z, torso_bones)

GX, GZ, RED, IRON, ROPE, HIDE = 10, 11, 5, 6, 8, 9          # engine labels (wood grain Y is 0)


# ======================================================================================= head (clean-shaven, the hair is its own part)
def stubble_mask(P):
    """The shaven shadow on his jaw, chin and upper lip (design coordinates): <= 0 inside."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.585) + F(0.075) * smoothstep(0.05, 0.14, ax)
    top = np.where(ax > F(0.15), F(1.69), top)                                     # up to the sideburns
    lip = np.where((ax < F(0.05)) & (y < F(-0.15)), F(1.585), F(-1.0))             # the upper lip (under the nose)
    top = np.maximum(top, lip)
    lips = (x / F(0.062)) ** 2 + ((y + F(0.18)) / F(0.05)) ** 2 + ((z - F(1.549)) / F(0.019)) ** 2 - F(1.0)
    back = y - F(0.03)
    return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), F(1.43) - z)


def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.79), (0.16, 0.17, 0.12)), 0.08, SKIN)                            # the dome (under his hair)
    fd.add(E((0, -0.05, 1.59), (0.136, 0.128, 0.126)), 0.07, SKIN)                        # a square jaw
    fd.add(E((0, -0.142, 1.497), (0.082, 0.068, 0.07)), 0.05, SKIN)                       # a strong chin...
    fd.sub(RoundCone(hp((0, -0.207, 1.518)), hp((0, -0.203, 1.478)), hr(0.0035), hr(0.005)), hr(0.007))   # ...cleft
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.118, 1.636), 0.05), 0.05, SKIN)                            # high cheekbones
        fd.add(S((sx * 0.124, -0.045, 1.558), 0.047), 0.05, SKIN)                           # jaw corners
        pts = [hp((sx * 0.152, -0.055, 1.744)), hp((sx * 0.116, -0.132, 1.755)), hp((sx * 0.062, -0.176, 1.754)), hp((0.0, -0.186, 1.75))]
        fd.add(Chain(pts, [hr(0.011), hr(0.02), hr(0.024), hr(0.022)], k=hr(0.02)), hr(0.03), SKIN)     # brow ridge
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.3), STUBBLE)
    # brows: the right one cocked up in an arch, the left drawn down over the squinting eye
    for sx in (-1, 1):
        if sx < 0:
            pts = [hp((sx * 0.024, -0.214, 1.758)), hp((sx * 0.064, -0.208, 1.78)), hp((sx * 0.11, -0.186, 1.786)), hp((sx * 0.154, -0.144, 1.772))]
        else:
            pts = [hp((sx * 0.024, -0.215, 1.741)), hp((sx * 0.066, -0.209, 1.752)), hp((sx * 0.112, -0.187, 1.758)), hp((sx * 0.155, -0.146, 1.756))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.009), hr(0.012), hr(0.01), hr(0.005)], k=hr(0.008)), hr(0.009), BROW)
        fd.paint(Chain(pts, [hr(0.02), hr(0.022), hr(0.019), hr(0.011)], k=hr(0.01)), BROW)
    # a frown line over the squinting eye
    fd.sub(RoundCone(hp((0.012, -0.2, 1.738)), hp((0.016, -0.197, 1.762)), hr(0.0018), hr(0.0016)), hr(0.003))
    for sx in (-1, 1):
        ec = eye_c(sx)
        squint = sx > 0
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up_z = hr(0.0065) if squint else hr(0.0165)
        lo_z = -hr(0.012) if squint else -hr(0.02)
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, up_z)), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, lo_z)), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, up_z - hr(0.003))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(2 if squint else 1):                                                 # crow's feet
            a = hp((sx * (0.112 + 0.004 * k), -0.13 + 0.006 * k, 1.672 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, -0.004 - 0.008 * k)), hr(0.0022), hr(0.0015)), hr(0.003))
    # a high-bridged Roman nose
    fd.add(RoundCone(hp((0, -0.188, 1.73)), hp((0, -0.236, 1.634)), hr(0.016), hr(0.022)), hr(0.016), SKIN)
    fd.add(S((0, -0.214, 1.692), 0.018), hr(0.01), SKIN)                                    # the bump on the bridge
    fd.add(S((0, -0.236, 1.624), 0.024), hr(0.014), SKIN)                                   # the tip, a little down
    for sx in (-1, 1):
        fd.add(S((sx * 0.029, -0.214, 1.607), 0.019), hr(0.011), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.015, -0.227, 1.596)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # mouth: a cocky half-smile, the right corner up
    slot = [hp((-0.066, -0.162, 1.572)), hp((-0.036, -0.19, 1.556)), hp((0, -0.198, 1.548)), hp((0.034, -0.19, 1.545)), hp((0.062, -0.164, 1.548))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.062, -0.161, 1.576), (-0.034, -0.184, 1.562), (-0.008, -0.19, 1.557), (0.012, -0.189, 1.555), (0.034, -0.183, 1.552), (0.058, -0.163, 1.551)]
    lo_lip = [(-0.05, -0.168, 1.557), (-0.028, -0.185, 1.541), (0, -0.189, 1.536), (0.028, -0.184, 1.536), (0.052, -0.166, 1.541)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0045), hr(0.005), hr(0.005), hr(0.0045), hr(0.003)], k=hr(0.005)), hr(0.006), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0065), hr(0.0075), hr(0.0065), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(Sphere(hp((-0.074, -0.158, 1.573)), hr(0.008)), hr(0.008), SKIN)                 # the cheek bunched by the smirk
    fd.sub(Sphere(hp((-0.07, -0.168, 1.566)), hr(0.004)), hr(0.004))                         # ...and its dimple
    # the smile line on the cocked side, from the nose wing down past the corner of his mouth
    fd.sub(Chain([hp((-0.046, -0.196, 1.6)), hp((-0.064, -0.175, 1.575)), hp((-0.07, -0.16, 1.548))], [hr(0.0025), hr(0.003), hr(0.002)], k=hr(0.003)), hr(0.004))
    # ears
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.178, 0.035, 1.664)), v3((0.026, 0.047, 0.06)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.197, 0.028, 1.668)), v3((0.012, 0.03, 0.04)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))


# ======================================================================================= body (lean and hard)
def deltoid(side):
    sx = -1 if side == "R" else 1
    return Sphere(J["shoulder_" + side] + v3((sx * 0.022, -0.005, 0.01)), 0.106)


def torso_prims():
    return [
        (Ellipsoid((0, 0.05, 1.17), (0.285, 0.23, 0.27), R=euler(-0.1, 0, 0)), 0.0),
        (Ellipsoid((0, 0.12, 1.22), (0.32, 0.16, 0.21)), 0.06),
        (Ellipsoid((0.13, -0.14, 1.24), (0.135, 0.06, 0.09), R=euler(0.1, 0, 0.18)), 0.045),
        (Ellipsoid((-0.13, -0.14, 1.24), (0.135, 0.06, 0.09), R=euler(0.1, 0, -0.18)), 0.045),
        (Ellipsoid((0, -0.01, 0.98), (0.22, 0.19, 0.2)), 0.08),                      # a flat belly
        (Ellipsoid((0, 0.045, 0.8), (0.245, 0.185, 0.16)), 0.08),
    ]


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        fd.add(upper_arm(side), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.094, 0.097, 0.13), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)
        fd.add(RoundCone(el, wr, 0.078, 0.057), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.097, 0.087, 0.135), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.058), 0.028, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.136, 0.09), 0.065, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.125, 0.117, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.048, SKIN)
        fd.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.07), 0.038, SKIN)
        fd.add(RoundCone(kn, an, 0.086, 0.057), 0.038, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.098, 0.095, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= hair: cropped, combed forward
CROWN = v3((0.0, 0.07, 1.87))       # the whorl the hair is combed out from (design coordinates)
# where the hair ends, by the angle round his head (0 = the middle of his brow, pi = the nape): (angle, height)
_HAIRLINE = [(0.0, 1.803), (0.9, 1.8), (1.1, 1.73), (1.27, 1.67), (1.41, 1.672), (1.51, 1.756), (1.84, 1.756),
             (2.04, 1.635), (math.pi, 1.605)]
_HL_A = np.array([a for a, _ in _HAIRLINE], F)
_HL_Z = np.array([z for _, z in _HAIRLINE], F)


def _comb_angle(Q):
    return np.arctan2(Q[:, 0], -(Q[:, 1] - F(CROWN[1])))


def hair_tex(P):
    """Short comma-shaped locks combed out from the crown (forward over his brow), in staggered rows; positive pushes the
    surface in."""
    Q = hinv(P)
    phi = _comb_angle(Q) + F(0.25) * NOISE(Q * F(6))
    r = np.sqrt(Q[:, 0] ** 2 + (Q[:, 1] - F(CROWN[1])) ** 2 + (F(0.6) * (Q[:, 2] - F(CROWN[2]))) ** 2)
    u = phi * F(30 / (2 * math.pi))
    iu = np.floor(u)
    v = r / F(0.034) + F(0.5) * np.mod(iu, F(2)) + F(0.35) * (u - iu)       # each lock sweeps a little sideways
    du = u - iu - F(0.5)
    dv = v - np.floor(v) - F(0.5)
    d = (du / F(0.46)) ** 2 + (dv / F(0.52)) ** 2
    dome = np.clip(F(1) - d, 0, 1) ** F(0.7)
    return F(0.0026) - F(0.0046) * dome + F(0.0007) * NOISE(Q * np.array([110, 110, 50], F))


def hair_field():
    fd = Field("Hair")
    sk = skull()
    def keep(P):
        Q = hinv(P)
        th = np.abs(np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.02))))
        zl = np.interp(th, _HL_A, _HL_Z).astype(F)
        # the fringe's ragged edge: lock tips in front, a clean trim over the ears and at the nape
        tips = F(0.009) * np.abs(np.sin(Q[:, 0] * F(105) + F(0.6) * NOISE(Q * F(20)))) * (F(1) - smoothstep(0.7, 1.0, th))
        return zl - tips - Q[:, 2]
    fd.add(Inter(Shell(sk, 0.008, 0.019, pad=0.06, disp=hair_tex, disp_amp=0.004), Func(keep, HEAD_C - 0.4, HEAD_C + 0.35), 0.003), 0.0)
    return fd


# ======================================================================================= tunic (undyed, red clavi), scarf
HEM_Z = 0.5


def tunic_base():
    """His body under the tunic: the chest one broad flat curve (the cloth hangs straight over his pectorals)."""
    b = Field("TunicBase")
    for i, (p, k) in enumerate(torso_prims()):
        if i not in (2, 3):
            b.add(p, k)
    b.add(Ellipsoid((0, -0.1, 1.215), (0.255, 0.1, 0.15), R=euler(0.12, 0, 0)), 0.06)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.055)
        b.add(upper_arm(side), 0.05)
    b.add(RoundCone((0, 0.03, 0.92), (0, 0.03, 0.45), 0.25, 0.32), 0.09)            # the skirt
    return b


def _neck_cut(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
    return z - (F(1.445) - F(0.045) * front * np.exp(-(x / F(0.14)) ** 2) + F(0.3) * smoothstep(0.17, 0.25, np.abs(x)))


def hem_z(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
    return F(HEM_Z) + F(0.018) * np.cos(a * 2) + F(0.007) * NOISE(P * F(8))


def tunic_field():
    """Undyed wool to the knee, short sleeves; two red stripes (clavi, label 6) from the neckline over the shoulders down
    the front and the back, red bands round the hem and the sleeves."""
    fd = Field("Tunic")
    base = tunic_base()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        k = smoothstep(0.9, 0.7, P[:, 2])
        return F(0.005) * np.sin(a * F(14) + F(0.7) * NOISE(P * F(3))) * k + F(0.0015) * NOISE(P * F(25))
    def keep(P):
        k = np.maximum(hem_z(P) - P[:, 2], _neck_cut(P))
        return np.maximum(np.maximum(k, _sleeve(P, "R")), _sleeve(P, "L"))
    fd.add(Inter(Shell(base, 0.019, 0.019, pad=0.1, disp=folds, disp_amp=0.006), Func(keep, (-1, -1, 0.3), (1, 1, 1.6)), 0.005), 0.0)
    for sx in (-1, 1):                                                           # the clavi
        fd.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 0] - F(sx * 0.1)) - F(0.017), F(0.6) - P[:, 2]),
                      (-1, -1, 0.3), (1, 1, 1.7)), 6)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - (hem_z(P) + F(0.045))) - F(0.012), (-1, -1, 0.3), (1, 1, 0.7)), 6)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - (hem_z(P) + F(0.016))) - F(0.006), (-1, -1, 0.3), (1, 1, 0.7)), 6)
    for side in ("R", "L"):
        def cuff(P, side=side):
            s = _sleeve(P, side)
            return np.where(s > F(-0.5), np.abs(s + F(0.03)) - F(0.012), F(1.0))
        fd.paint(Func(cuff, (-1, -1, 0.8), (1, 1, 1.6)), 6)
    return fd


def scarf_field():
    """The focale: a red wool scarf rolled round his neck, knotted at his throat, the ends hanging onto his chest."""
    fd = Field("Scarf")
    cl = lambda P: F(0.003) * NOISE(P * F(20)) + F(0.0015) * NOISE(P * F(55))
    pts = []
    for k in range(17):
        a = 2 * math.pi * k / 16
        pts.append(v3((0.118 * math.sin(a), 0.04 - 0.114 * math.cos(a), 1.48 + 0.004 * math.cos(a))))
    fd.add(Chain(pts, [0.036] * len(pts), k=0.012, disp=cl, disp_amp=0.004), 0.0)
    knot = v3((0.012, -0.088, 1.45))
    fd.add(Ellipsoid(knot, (0.04, 0.03, 0.035), disp=cl, disp_amp=0.004), 0.01)
    for dx, ln in ((-0.022, 0.15), (0.03, 0.12)):
        p0 = knot + v3((dx * 0.5, -0.004, -0.02))
        fd.add(Lock([p0, p0 + v3((dx, -0.012, -ln * 0.5)), p0 + v3((dx * 1.3, -0.006, -ln))], [0.03, 0.028, 0.024],
                    [0.006, 0.006, 0.005], [v3((0, -1, 0))] * 3, k=0.006, disp=cl, disp_amp=0.003), 0.006)
    return fd


# ======================================================================================= belt, apron, boots (leather, brass)
BELT_Z = 0.965


def belt_base():
    b = Field("BeltBase")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    return b


def apron_straps():
    """The four straps of the apron hanging in front from the belt: (x, top, bottom)."""
    return [(-0.066 + 0.044 * k, BELT_Z - 0.01, 0.7 - 0.012 * abs(k - 1.5)) for k in range(4)]


def leather_field():
    """The military belt (leather, brass plates: label 6), the apron of four studded straps with brass pendants; wrist
    wraps; caligae: a thick hobnailed sole, an open-work upper of straps, laced up the ankle."""
    fd = Field("Leather")
    bb = belt_base()
    fd.add(Inter(Shell(bb, 0.06, 0.022, pad=0.1), Func(lambda P: np.abs(P[:, 2] - (F(BELT_Z) + F(0.02) * P[:, 1])) - F(0.03), (-1, -1, 0.8), (1, 1, 1.2)), 0.004), 0.0)
    def plates(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.0)))
        s = np.mod(a * F(12 / (2 * math.pi)), F(1.0))
        return np.maximum(np.abs(P[:, 2] - (F(BELT_Z) + F(0.02) * P[:, 1])) - F(0.023), np.abs(s - F(0.5)) - F(0.34))
    fd.paint(Func(plates, (-1, -1, 0.8), (1, 1, 1.2)), 6)
    skirt = Field("ApronHull")
    skirt.add(RoundCone((0, 0.03, 0.95), (0, 0.03, 0.45), 0.27, 0.34), 0.0)
    for x, top, bot in apron_straps():
        def strap(P, x=x, top=top, bot=bot):
            return np.maximum(np.maximum(np.abs(P[:, 0] - F(x)) - F(0.012), np.maximum(P[:, 2] - F(top), F(bot) - P[:, 2])),
                              P[:, 1] - F(0.0))                      # (the front only: the shell wraps round behind him too)
        fd.add(Inter(Shell(skirt, 0.03, 0.008, pad=0.08), Func(strap, (x - 0.05, -0.6, bot - 0.02), (x + 0.05, 0.1, top + 0.02)), 0.003), 0.003)
        last = None
        for j in range(4):
            z = top - 0.035 - j * (top - bot - 0.06) / 3.0
            h, ok = ray_hit(Func(lambda P: skirt.eval(P) - F(0.042), (-0.6, -0.6, 0.3), (0.6, 0.2, 1.1)), [v3((x, -0.7, z))], [v3((0, 1, 0))], tmax=0.8)
            if ok[0]:
                fd.add(Sphere(h[0] + v3((0, 0.002, 0)), 0.0085), 0.002, 6)
                last = h[0]
        if last is not None:
            fd.add(Ellipsoid(last + v3((0, 0.0, -0.045)), (0.014, 0.006, 0.022)), 0.004, 6)
    for side in ("L", "R"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.82)
        fd.add(Inter(Shell(_forearm(side), 0.012, 0.016, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.05), c - 0.25, c + 0.25), 0.004), 0.0)
        for j in (-1, 1):
            cc = c + ax * (j * 0.032)
            fd.add(Inter(Shell(_forearm(side), 0.02, 0.006, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.005), cc - 0.2, cc + 0.2), 0.002), 0.003, 6)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.098)), (0.08, 0.157, 0.016), 0.01, R=Rz), 0.0)
        ft = Field("FootHull")
        foot(ft, side)
        for c2, rad in ((an + fwd * 0.15 + v3((0, 0, -0.07)), 0.018), (an + fwd * 0.1 + v3((0, 0, -0.055)), 0.018),
                        (an + fwd * 0.05 + v3((0, 0, -0.035)), 0.018), (an + fwd * 0.0 + v3((0, 0, -0.02)), 0.02)):
            fd.add(Inter(Shell(ft, 0.006, 0.01, pad=0.05), Func(lambda P, c=c2, fwd=fwd, rad=rad: np.abs((P - c.astype(F)) @ fwd.astype(F)) - F(rad * 0.6), c2 - 0.15, c2 + 0.15), 0.003), 0.002)
        shin = Field("ShinHull")
        shin.add(RoundCone(J["knee_" + side], an, 0.086, 0.057), 0.0)
        shin.add(Sphere(an + v3((0, 0.042, -0.05)), 0.062), 0.03)
        for zz in (0.075, 0.12, 0.165, 0.21):
            fd.add(Inter(Shell(shin, 0.006, 0.009, pad=0.05), Func(lambda P, zz=zz: np.abs(P[:, 2] - F(zz)) - F(0.008), an - 0.2, an + 0.2), 0.003), 0.002)
        for k in range(9):                                                          # hobnails round the sole's edge
            a = 2 * math.pi * k / 9
            c3 = an + fwd * (0.075 + 0.13 * math.cos(a)) + (Rz @ v3((1, 0, 0))) * (0.068 * math.sin(a)) + v3((0, 0, -0.113))
            fd.add(Sphere(c3, 0.007), 0.002, 6)
    return fd


# ======================================================================================= the mallet (rigid in his right fist)
def mallet_field():
    """Hard wood (label 0), two iron bands round the head and an iron collar (6), a red cord grip (5)."""
    fd = Field("Mallet")
    G, T, Fv = mallet_frame()
    fd.add(RoundCone(G - T * MALLET_BUTT, G + T * (MALLET_L - 0.04), 0.019, 0.016, disp=GRAIN, disp_amp=0.002), 0.0)
    fd.add(Sphere(G - T * MALLET_BUTT, 0.022), 0.006)
    hc = G + T * MALLET_L
    r, hl = MALLET_HEAD
    fd.add(Cylinder(hc, r, hl * 2, rr=0.012, R=rot_from_axes(z_axis=Fv), disp=GRAIN, disp_amp=0.002), 0.008)
    for s in (-1, 1):
        fd.add(Cylinder(hc + Fv * s * (hl - 0.022), r + 0.004, 0.018, rr=0.004, R=rot_from_axes(z_axis=Fv)), 0.002, IRON)
    fd.add(Cylinder(hc - T * (r + 0.004), 0.025, 0.02, rr=0.005, R=rot_from_axes(z_axis=T)), 0.006, IRON)
    for k in range(6):
        c = G + T * (-0.05 + 0.02 * k)
        fd.add(Torus(c, 0.019, 0.0045, R=rot_from_axes(z_axis=T)), 0.002, RED)
    return fd


# ======================================================================================= the engine (layout)
MX = 0.74                     # the frame's centre line (x); it shoots toward -Y
BW = 0.27                     # side beams' centre offset from MX
BEAM_HW, BEAM_HH = 0.068, 0.082
BEAM_Z = BEAM_HH              # the side beams lie on the ground
BEAM_TOP = 2 * BEAM_HH
AXLE = v3((MX, -0.95, 0.31))  # the skein's centre: the arm turns about it
COCK = math.radians(12.0)     # the arm's angle (from horizontal, toward the back) wound down
FIRED = math.radians(94.0)    # ... against the buffer
LONG = 0.94                   # pivot -> the sling's prong at the tip
W0, D0, W1, D1 = 0.052, 0.06, 0.04, 0.042    # the arm's half width and half depth at its foot and its tip
BALL_R = 0.078
SLING_LEFT = v3((MX, 0.2, BEAM_TOP + 0.012 + 0.012 + BALL_R))   # the stone's centre in the pouch on the back board
HAUL_S = 0.8                  # where the windlass rope is tied under the arm
DRUM = v3((MX, -0.02, 0.28))
DRUM_R = 0.06
NEAR = MX - BW                # the near side beam (his side, -X)
CRANK_X = NEAR - 0.125        # the crank's plane
CRANK_R = 0.13
CRANK_PHI = math.radians(70.0)          # the crank's angle in the rest pose (0 = toward the back, + = up)
HANDLE_L = 0.13
PAD_RY = 0.075                # the stuffed sack's half depth (toward the arm)


def arm_dir(a):
    return v3((0.0, math.cos(a), math.sin(a)))


def arm_up(a):
    return v3((0.0, -math.sin(a), math.cos(a)))


def arm_pt(s, a=COCK, up=0.0):
    return AXLE + arm_dir(a) * s + arm_up(a) * up


def arm_depth(s):
    return D0 + (D1 - D0) * max(0.0, min(1.0, (s + 0.12) / (LONG + 0.14)))


PAD = arm_pt(0.8, FIRED, arm_depth(0.8) + PAD_RY)       # the sack the arm slams into (at FIRED, 0.8 along it)
BAR = PAD + v3((0, -(PAD_RY + 0.05), 0))                 # the buffer's cross bar
POST_Y = BAR[1] - 0.1
POST_TOP = 1.24
Y0, Y1 = POST_Y - 0.12, 0.36   # the side beams' front and back ends
PIN_Y = -0.2
TRIG_TOP = 0.42               # the trigger post's top
PIN_TOP = v3((NEAR - 0.012, PIN_Y, TRIG_TOP + 0.05))
PILE = v3((-0.1, 0.36, 0.0))                   # the heap of stone balls (clear of his heels)
POTS = (v3((-0.4, -0.6, 0.0)), v3((-0.22, -0.75, 0.0)))     # in front of him, out of his way
YAW_PIVOT = (0.44, -0.555, 0.0)                # the tower turns about this point (keeps the whole frame on the base)


def hook_pt(a=COCK):
    """The prong at the arm's tip the sling's loop rides on."""
    return arm_pt(LONG, a, arm_depth(LONG) + 0.012)


SLING_L = float(np.linalg.norm(SLING_LEFT - hook_pt(COCK)))   # the prong -> the stone's centre


def ball_c(a=COCK):
    """The stone in the sling's pouch (at rest: on the back board)."""
    return SLING_LEFT


def haul_point(a=COCK):
    return arm_pt(HAUL_S, a, -arm_depth(HAUL_S) - 0.014)


def haul_start():
    """Where the rope leaves the drum (toward the arm)."""
    d = norm(haul_point(COCK) - DRUM)
    return DRUM + d * (DRUM_R + 0.01)


def crank_handle(phi):
    """The crank handle's inner and outer ends at crank angle phi (0 = toward the back, + = up)."""
    c = v3((CRANK_X, DRUM[1] + CRANK_R * math.cos(phi), DRUM[2] + CRANK_R * math.sin(phi)))
    return c, c - v3((HANDLE_L, 0, 0))


def pile_balls():
    """(centre, bone) of the stone balls in the heap: three on the mat, one on them (the one he lifts), one rolled aside."""
    m = 0.012
    out = []
    for k in range(3):
        a = math.radians(30 + 120 * k)
        out.append((PILE + v3((math.cos(a) * 0.0866, math.sin(a) * 0.0866, m + BALL_R)), "props"))
    out.append((PILE + v3((0, 0, m + BALL_R + math.sqrt((2 * BALL_R) ** 2 - 0.0866 ** 2) + 0.009)), "carry"))
    out.append((PILE + v3((0.15, 0.05, BALL_R)), "props"))
    return out


CARRY_C = pile_balls()[3][0]


# ======================================================================================= the engine (sculpt)
def frame_field():
    """Side beams on the ground, cross beams, the spring blocks with their washers and levers, the skein, the buffer
    (posts, braces, cross bar, the stuffed sack lashed to it), the back board, the windlass's bearing blocks, the trigger
    post and its pin."""
    fd = Field("Frame")
    zb = BEAM_Z
    for sx in (-1, 1):
        x = MX + sx * BW
        fd.add(box((x, (Y0 + Y1) / 2, zb), (BEAM_HW, (Y1 - Y0) / 2, BEAM_HH)), 0.0, 0)
        for ye in (Y0, Y1):                                                   # iron shoes on the beam ends
            sgn = -1 if ye == Y0 else 1
            fd.add(Inter(RoundBox(v3((x, ye - sgn * 0.03, zb)), (BEAM_HW + 0.006, 0.04, BEAM_HH + 0.006), 0.012),
                         Func(lambda P, ye=ye, sgn=sgn: (F(ye) - P[:, 1]) * F(sgn) - F(0.075), (x - 0.12, ye - 0.12, zb - 0.12), (x + 0.12, ye + 0.12, zb + 0.12)), 0.002), 0.003, IRON)
        # Roman red along the outer face, iron straps round the beam by the spring block
        def stripe(P, x=x, sx=sx):
            return np.maximum(np.maximum(np.abs(P[:, 2] - F(zb)) - F(0.04), (F(x) - P[:, 0]) * F(sx) + F(0.02)),
                              np.abs(P[:, 1] - F((Y0 + Y1) / 2)) - F((Y1 - Y0) / 2 - 0.09))
        fd.paint(Func(stripe, (x - 0.12, Y0, zb - 0.12), (x + 0.12, Y1, zb + 0.12)), RED)
        for yb in (AXLE[1] - 0.24, AXLE[1] + 0.24, DRUM[1] - 0.12):
            sbox = (x, yb, zb)
            fd.add(Inter(Shell(RoundBox(v3(sbox), (BEAM_HW, 0.2, BEAM_HH), 0.012), 0.005, 0.008, pad=0.05),
                         Func(lambda P, yb=yb: np.abs(P[:, 1] - F(yb)) - F(0.022), (x - 0.12, yb - 0.1, -0.05), (x + 0.12, yb + 0.1, 0.3)), 0.002), 0.003, IRON)
    for yc in (Y0 + 0.07, POST_Y, AXLE[1] + 0.34, Y1 - 0.05):                  # cross beams
        fd.add(box((MX, yc, BEAM_TOP - 0.05), (BW - 0.03, 0.045, 0.05)), 0.006, GX)
    # the back board the sling's pouch lies on
    fd.add(box((MX, SLING_LEFT[1], BEAM_TOP - 0.004), (BW - 0.05, 0.13, 0.016)), 0.004, GX)
    # spring blocks, washers, levers
    for sx in (-1, 1):
        x = MX + sx * BW
        fd.add(box((x, AXLE[1], (BEAM_TOP + 0.5) / 2), (0.08, 0.17, (0.5 - BEAM_TOP) / 2 + 0.01), r=0.02), 0.012, GZ)
        fd.add(RoundBox(v3((x + sx * 0.08, AXLE[1], AXLE[2])), (0.006, 0.14, 0.14), 0.006), 0.002, IRON)      # the seat plate
        for k in range(4):                                                    # its nails
            a = math.pi / 4 + k * math.pi / 2
            fd.add(Sphere(v3((x + sx * 0.087, AXLE[1] + 0.12 * math.cos(a), AXLE[2] + 0.12 * math.sin(a))), 0.011), 0.002, IRON)
        wc = v3((x + sx * 0.098, AXLE[1], AXLE[2]))
        Rx = rot_from_axes(z_axis=(1, 0, 0))
        fd.add(Cylinder(wc, 0.112, 0.028, rr=0.006, R=Rx), 0.003, IRON)
        for k in range(12):                                                   # the ratchet teeth round the washer
            a = 2 * math.pi * k / 12
            d = v3((0, math.cos(a), math.sin(a)))
            tng = v3((0, -math.sin(a), math.cos(a)))
            fd.add(RoundBox(wc + d * 0.114 + tng * 0.008, (0.013, 0.012, 0.016), 0.003, R=rot_from_axes(y_axis=d, z_axis=(1, 0, 0))), 0.003, IRON)
        fd.add(Torus(wc + v3((sx * 0.015, 0, 0)), 0.075, 0.017, R=Rx), 0.004, IRON)
        lev = norm(v3((0, math.sin(math.radians(28)), math.cos(math.radians(28)))))
        lc = wc + v3((sx * 0.042, 0, 0))
        fd.add(RoundCone(lc - lev * 0.18, lc + lev * 0.2, 0.022, 0.02), 0.004, IRON)
        for e in (lc - lev * 0.18, lc + lev * 0.2):
            fd.add(Sphere(e, 0.026), 0.004, IRON)
        fd.add(Ellipsoid(lc + v3((-sx * 0.008, 0, 0)), (0.03, 0.05, 0.05), disp=lambda P: F(0.003) * np.sin(P[:, 1] * F(260) + P[:, 2] * F(260)), disp_amp=0.004), 0.008, ROPE)
        stop = v3((x + sx * 0.118, AXLE[1] - 0.125, AXLE[2] - 0.13))           # the peg the lever bears against
        fd.add(Cylinder(stop, 0.017, 0.08, rr=0.004, R=Rx), 0.003, IRON)
    # the skein: a thick bundle of twisted sinew between the blocks (the arm through its middle)
    def skein(P):
        q = P - AXLE.astype(F)
        rr = np.sqrt(q[:, 1] ** 2 + q[:, 2] ** 2)
        a = np.arctan2(q[:, 2], q[:, 1])
        tw = F(0.006) * np.sin(a * F(9) + q[:, 0] * F(60))
        bulge = F(0.018) * np.exp(-(q[:, 0] / F(0.085)) ** 2)
        return np.maximum(rr - (F(0.08) + bulge) + tw, np.abs(q[:, 0]) - F(BW + 0.06))
    fd.add(Func(skein, AXLE - v3((0.5, 0.16, 0.16)), AXLE + v3((0.5, 0.16, 0.16)), disp=lambda P: F(0.0012) * NOISE(P * F(160)), disp_amp=0.002), 0.004, ROPE)
    # the buffer: two posts braced forward, a cross bar on their backs, a great stuffed sack lashed to it
    for sx in (-1, 1):
        x = MX + sx * BW
        fd.add(box((x, POST_Y, (BEAM_TOP + POST_TOP) / 2), (0.054, 0.054, (POST_TOP - BEAM_TOP) / 2 + 0.01)), 0.008, GZ)
        fd.add(tbeam((x, Y0 + 0.1, BEAM_TOP - 0.01), (x, POST_Y - 0.04, 0.86), (1, 0, 0), 0.04, 0.04, disp=GRAIN, disp_amp=0.002), 0.01, GZ)
        fd.add(RoundBox(v3((x, POST_Y, POST_TOP - 0.004)), (0.06, 0.06, 0.016), 0.005), 0.003, IRON)
        fd.add(Sphere(v3((x, POST_Y, POST_TOP + 0.03)), 0.04), 0.006, IRON)
        for zz in (0.5, 0.9):                                                # iron straps round the posts
            fd.add(Inter(Shell(RoundBox(v3((x, POST_Y, zz)), (0.054, 0.054, 0.1), 0.012), 0.005, 0.008, pad=0.05),
                         Func(lambda P, zz=zz: np.abs(P[:, 2] - F(zz)) - F(0.02), (x - 0.12, POST_Y - 0.12, zz - 0.1), (x + 0.12, POST_Y + 0.12, zz + 0.1)), 0.002), 0.003, IRON)
        fd.paint(Func(lambda P, x=x: np.maximum(np.abs(P[:, 2] - F(0.7)) - F(0.08), np.abs(P[:, 0] - F(x)) - F(0.07)),
                      (x - 0.12, POST_Y - 0.12, 0.5), (x + 0.12, POST_Y + 0.12, 0.9)), RED)
    fd.add(box(BAR, (BW + 0.085, 0.05, 0.056)), 0.008, GX)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 0] - F(MX)) - F(BW - 0.07), np.abs(P[:, 2] - F(BAR[2])) - F(0.07)),
                  BAR - v3((0.5, 0.1, 0.1)), BAR + v3((0.5, 0.1, 0.1))), RED)
    for sx in (-1, 1):
        fd.add(RoundBox(BAR + v3((sx * (BW + 0.085), 0, 0)), (0.012, 0.056, 0.062), 0.006), 0.003, IRON)
    sack = lambda P: F(0.004) * NOISE(P * F(16)) + F(0.0015) * NOISE(P * F(50))
    fd.add(Ellipsoid(PAD + v3((0, 0, -0.01)), (0.2, PAD_RY + 0.006, 0.15), disp=sack, disp_amp=0.006), 0.012, HIDE)
    bp = Field("BarPad")
    bp.add(RoundBox(BAR, (BW + 0.085, 0.05, 0.056), 0.012), 0.0)
    bp.add(Ellipsoid(PAD + v3((0, 0, -0.01)), (0.2, PAD_RY + 0.006, 0.15)), 0.012)
    for cx in (MX - 0.13, MX - 0.045, MX + 0.045, MX + 0.13):
        fd.add(Inter(Shell(bp, 0.004, 0.012, pad=0.05), Func(lambda P, cx=cx: np.abs(P[:, 0] - F(cx)) - F(0.011), BAR - 0.35, BAR + 0.35), 0.003), 0.004, ROPE)
    # the windlass's bearing blocks, the trigger post on the near beam
    for sx in (-1, 1):
        fd.add(box((MX + sx * BW, DRUM[1], (BEAM_TOP + DRUM[2] + 0.07) / 2), (0.06, 0.066, (DRUM[2] + 0.07 - BEAM_TOP) / 2 + 0.01)), 0.008, GZ)
        fd.add(RoundBox(v3((MX + sx * BW, DRUM[1], DRUM[2] + 0.07)), (0.066, 0.07, 0.012), 0.005), 0.003, IRON)
    fd.add(box((NEAR, PIN_Y, (BEAM_TOP + TRIG_TOP) / 2), (0.056, 0.06, (TRIG_TOP - BEAM_TOP) / 2 + 0.01)), 0.008, GZ)
    fd.add(RoundBox(v3((NEAR, PIN_Y, TRIG_TOP)), (0.062, 0.066, 0.012), 0.005), 0.003, IRON)
    fd.add(Cylinder(PIN_TOP - v3((0, 0, 0.05)), 0.011, 0.1, rr=0.003), 0.003, IRON)          # the trigger pin
    fd.add(Ellipsoid(PIN_TOP, (0.03, 0.03, 0.017)), 0.004, IRON)
    return fd


def arm_field():
    """The throwing arm (wound down): a tapered beam through the skein, rope-bound at its foot, iron bands, the rope ring
    underneath, an iron cap at its tip with the prong the sling's loop rides on."""
    fd = Field("Arm")
    d, up = arm_dir(COCK), arm_up(COCK)
    a0, a1 = arm_pt(-0.12), arm_pt(LONG + 0.02)
    fd.add(tbeam(a0, a1, up, W0, D0, W1, D1, r=0.016, disp=GRAIN, disp_amp=0.002), 0.0, 0)
    def band(s0, w, label, extra=0.007, ridges=False):
        c = arm_pt(s0)
        dd = d.astype(F)
        rid = (lambda P: F(0.002) * np.sin(((P - c.astype(F)) @ dd) * F(330))) if ridges else None
        fd.add(Inter(tbeam(a0, a1, up, W0 + extra, D0 + extra, W1 + extra, D1 + extra, r=0.018, disp=rid, disp_amp=0.003 if ridges else 0.0),
                     Func(lambda P: np.abs((P - c.astype(F)) @ dd) - F(w), c - 0.2, c + 0.2), 0.002), 0.003, label)
    band(0.17, 0.06, ROPE, 0.008, ridges=True)
    band(-0.09, 0.024, ROPE, 0.008, ridges=True)
    band(0.42, 0.017, IRON)
    band(0.66, 0.017, IRON)
    band(LONG - 0.02, 0.04, IRON, 0.006)
    hp_ = haul_point(COCK)
    fd.add(Torus(hp_ + up * 0.004, 0.019, 0.0058, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, IRON)
    fd.add(RoundBox(arm_pt(HAUL_S, up=-arm_depth(HAUL_S) + 0.004), (0.042, 0.013, 0.012), 0.004, R=rot_from_axes(z_axis=up, y_axis=d)), 0.004, IRON)
    # the prong: an iron hook on the tip's top, curving back toward the skein (the loop slips off it at the throw)
    h0 = arm_pt(LONG - 0.035, up=arm_depth(LONG) - 0.004)
    fd.add(Chain([h0, h0 + up * 0.03 + d * 0.012, h0 + up * 0.045 - d * 0.012], [0.011, 0.009, 0.007], k=0.004), 0.004, IRON)
    return fd


def sling_field():
    """The sling (wound): two ropes from the arm's tip (one tied round it, one looped over the prong) to the two ends of a
    leather pouch cradling the stone; the stone itself is a Stones part."""
    fd = Field("Sling")
    H = hook_pt(COCK)
    tip = arm_pt(LONG - 0.01, up=0.0)
    S = SLING_LEFT
    ax = norm(S - H)
    side = v3((1.0, 0.0, 0.0))
    third = norm(np.cross(ax, side))                       # across the pouch, along the frame
    Rp = np.stack([side, third, ax], axis=1)
    pouch = Ellipsoid(S + ax * 0.012, (0.1, 0.09, 0.07), R=Rp)
    def open_top(P):
        return -(((P - S.astype(F)) @ ax.astype(F)) + F(0.025))        # keep the pouch's far half (under the stone)
    leather = lambda P: F(0.0015) * NOISE(P * F(40))
    fd.add(Inter(Shell(pouch, 0.0, 0.014, pad=0.04, disp=leather, disp_amp=0.002), Func(open_top, S - 0.25, S + 0.25), 0.006), 0.0, HIDE)
    tw = lambda P: F(0.0012) * NOISE(P * F(120))
    for sx in (-1, 1):
        e = S + side * (sx * 0.095) - ax * 0.01
        a = H + side * (sx * 0.006) if sx > 0 else tip + side * (sx * 0.035)
        fd.add(RoundCone(a, e, 0.008, 0.008, disp=tw, disp_amp=0.0015), 0.004, ROPE)
        fd.add(Sphere(e, 0.014), 0.004, HIDE)
    fd.add(Torus(H, 0.016, 0.0055, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, ROPE)            # the loop on the prong
    fd.add(Torus(tip, W1 + 0.012, 0.007, R=rot_from_axes(z_axis=arm_dir(COCK))), 0.003, ROPE)    # the turns round the tip
    return fd


def winch_field():
    """The windlass: the drum with rope on it, iron rims, the ratchet wheel and the crank on his side (it turns with the
    'winch' bone)."""
    fd = Field("Winch")
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    L = 2 * (BW - 0.06)
    fd.add(Cylinder(DRUM, DRUM_R, L, rr=0.008, R=Rx, disp=GRAIN, disp_amp=0.002), 0.0, GX)
    for sx in (-1, 1):
        fd.add(Torus(DRUM + v3((sx * (L / 2 - 0.012), 0, 0)), DRUM_R + 0.004, 0.011, R=Rx), 0.003, IRON)
    for k in range(7):
        fd.add(Torus(DRUM + v3((-0.075 + 0.025 * k, 0, 0)), DRUM_R + 0.006, 0.009, R=Rx), 0.002, ROPE)
    ax0, ax1 = v3((MX + BW + 0.08, DRUM[1], DRUM[2])), v3((CRANK_X - 0.012, DRUM[1], DRUM[2]))
    fd.add(Cylinder((ax0 + ax1) / 2, 0.026, float(np.linalg.norm(ax1 - ax0)), rr=0.006, R=Rx), 0.004, IRON)
    rc = v3((NEAR - 0.08, DRUM[1], DRUM[2]))                                     # the ratchet wheel
    fd.add(Cylinder(rc, 0.07, 0.022, rr=0.004, R=Rx), 0.003, IRON)
    for k in range(10):
        a = 2 * math.pi * k / 10
        dd = v3((0, math.cos(a), math.sin(a)))
        tng = v3((0, -math.sin(a), math.cos(a)))
        fd.add(RoundBox(rc + dd * 0.074 + tng * 0.007, (0.011, 0.012, 0.014), 0.003, R=rot_from_axes(y_axis=dd, z_axis=(1, 0, 0))), 0.002, IRON)
    h0, h1 = crank_handle(CRANK_PHI)
    fd.add(tbeam(v3((CRANK_X, DRUM[1], DRUM[2])), h0, (1, 0, 0), 0.026, 0.012, 0.02, 0.011, r=0.006), 0.004, IRON)
    fd.add(Sphere(v3((CRANK_X, DRUM[1], DRUM[2])), 0.032), 0.004, IRON)
    fd.add(RoundCone(h0 + v3((0.012, 0, 0)), h1, 0.023, 0.021, disp=GRAIN, disp_amp=0.0015), 0.004, GX)
    fd.add(Sphere(h1 - v3((0.012, 0, 0)), 0.029), 0.004, IRON)
    return fd


PAWL_P = v3((NEAR - 0.08, PIN_Y + 0.05, TRIG_TOP - 0.1))     # the pawl's pivot on the trigger post


def pawl_tip():
    rc = v3((NEAR - 0.08, DRUM[1], DRUM[2]))
    d = norm(PAWL_P - rc)
    return rc + d * 0.082


def trigger_field():
    """The pawl that drops into the ratchet's teeth (the pin that holds it down is on the frame)."""
    fd = Field("Trigger")
    tip = pawl_tip()
    fd.add(tbeam(PAWL_P, tip, (1, 0, 0), 0.013, 0.012, 0.011, 0.008, r=0.005), 0.0, IRON)
    fd.add(Cylinder(PAWL_P, 0.022, 0.03, rr=0.005, R=rot_from_axes(z_axis=(1, 0, 0))), 0.004, IRON)
    return fd


def haul_field():
    """The windlass rope, wound: from the drum up to the ring under the arm (stretched in game)."""
    fd = Field("Haul")
    a, b = haul_start(), haul_point(COCK)
    tw = lambda P: F(0.0015) * np.sin(((P - a.astype(F)) @ norm(b - a).astype(F)) * F(420) + P[:, 0] * F(300))
    fd.add(RoundCone(a, b + norm(a - b) * 0.012, 0.0095, 0.0095, disp=tw, disp_amp=0.002), 0.0)
    return fd


def stones_field():
    """The stone in the sling's pouch, the heap of stones on the mat behind him (the top one is the one he lifts)."""
    fd = Field("Stones")
    fd.add(stone_ball(SLING_LEFT, BALL_R, 3), 0.0)
    for i, (c, bone) in enumerate(pile_balls()):
        fd.add(stone_ball(c, BALL_R, 10 + i), 0.0)
    return fd


def stone_centres():
    return [(SLING_LEFT, "stone")] + [(c, b) for c, b in pile_balls()]


def pots_field():
    """Two clay fire pots: round-bellied jars with a short neck and a lip, black bands painted on (label 5)."""
    fd = Field("Pots")
    for i, p in enumerate(POTS):
        c = p + v3((0, 0, 0.11))
        fd.add(Ellipsoid(c, (0.095, 0.095, 0.105)), 0.0)
        fd.add(RoundCone(c + v3((0, 0, 0.07)), c + v3((0, 0, 0.14)), 0.042, 0.034), 0.02)
        fd.add(Torus(c + v3((0, 0, 0.142)), 0.036, 0.009), 0.006)
        fd.add(Cylinder(p + v3((0, 0, 0.018)), 0.05, 0.036, rr=0.01), 0.03)
        for zz, w in ((0.03, 0.009), (0.0, 0.006), (-0.035, 0.009)):
            fd.paint(Func(lambda P, c=c, zz=zz, w=w: np.abs(P[:, 2] - F(c[2] + zz)) - F(w), c - 0.2, c + 0.2), 5)
    return fd


def mat_field():
    """A straw mat under the heap of stones, and the straw plugs in the pots' necks (bound with cord, label 5)."""
    fd = Field("Mat")
    fib = lambda P: F(0.0015) * np.sin(P[:, 0] * F(400)) + F(0.001) * NOISE(P * F(60))
    fd.add(RoundBox(PILE + v3((0.04, 0.0, 0.006)), (0.2, 0.15, 0.006), 0.005, R=euler(0, 0, -0.25), disp=fib, disp_amp=0.002), 0.0)
    for p in POTS:
        c = p + v3((0, 0, 0.11 + 0.15))
        fd.add(Ellipsoid(c, (0.03, 0.03, 0.04), disp=lambda P: F(0.004) * NOISE(P * F(70)), disp_amp=0.005), 0.0)
        fd.add(Torus(c - v3((0, 0, 0.02)), 0.03, 0.006), 0.003, 5)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.24, 1.622)), 0.05, 0.55)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.11, -0.13, 1.63)), 0.055, 0.4), (hp((sx * 0.178, 0.035, 1.664)), 0.055, 0.55),
                (J["elbow_" + sd] + v3((0, 0.025, 0)), 0.065, 0.3), (J["knee_" + sd] + v3((0, -0.03, 0)), 0.075, 0.35),
                (J["shoulder_" + sd] + v3((0, 0, 0.1)), 0.12, 0.2)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.044, 0.0148, -0.0148, -0.044):
            pts.append((wr + f * 0.14 + t * o - n * 0.012, 0.032, 0.45))
        an = J["ankle_" + side]
        pts.append((an + v3((0, -0.17, -0.07)), 0.065, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "onager"
ROOT_NAME = "OnagerHQ"
TEX_PREFIX = "onager"
MAT_NAME = "OnagerMat"
MESH_NAME = "Onager"
BASE_MODULE = "onager_base"
ANIM_MODULE = "anim_onager"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Tunic", "Scarf", "Leather", "Mallet", "Frame", "Arm", "Sling", "Winch",
         "Trigger", "Haul", "Stones", "Pots", "Mat"]
REGION_PARTS = ("Skin", "Tunic", "Leather", "Mallet", "Frame", "Arm", "Sling", "Winch", "Pots", "Mat")
SIEGE = {"name": "HQ_RomanSiege", "wood": (0.56, 0.38, 0.22), "wood2": (0.4, 0.26, 0.14), "red": (0.62, 0.1, 0.07), "metal": "iron"}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_RomanSkin", "base": (0.76, 0.52, 0.36), "ruddy": (0.8, 0.45, 0.33), "lips": (0.62, 0.35, 0.29),
                      "brow": ((0.05, 0.04, 0.035), (0.12, 0.09, 0.07)),
                      "extra": ((LASH, (0.05, 0.035, 0.03), 0.5), (STUBBLE, (0.4, 0.33, 0.31), 0.55, 0.4))}),
    "Hair": ("hair", {"name": "HQ_RomanHair", "base": (0.1, 0.07, 0.055), "hi": (0.32, 0.24, 0.18), "low": (0.04, 0.03, 0.025),
                      "streak": (0.06, 0.045, 0.035), "tint": (0.18, 0.12, 0.08)}),
    "Tunic": ("wool", {"name": "HQ_RomanTunic", "base": (0.86, 0.8, 0.66), "border": (0.62, 0.1, 0.07), "stripe": (0.64, 0.1, 0.07)}),
    "Scarf": ("cloth", {"name": "HQ_Focale", "col": (0.74, 0.12, 0.08)}),
    "Leather": ("leather_dyed", {"name": "HQ_RomanBelt", "base": (0.33, 0.2, 0.11)}),
    "Mallet": ("siege", SIEGE),
    "Frame": ("siege", SIEGE), "Arm": ("siege", SIEGE), "Sling": ("siege", SIEGE), "Winch": ("siege", SIEGE),
    "Trigger": ("siege", SIEGE),
    "Haul": ("cord", {}),
    "Stones": ("limestone", {"name": "HQ_OnagerStones"}),
    "Pots": ("terracotta", {"name": "HQ_FirePots"}),
    "Mat": ("reed", {"name": "HQ_StrawMat", "base": (0.72, 0.62, 0.34)}),
}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Hair": 900, "Tunic": 1900, "Scarf": 520, "Leather": 1500, "Mallet": 380,
               "Frame": 5400, "Arm": 950, "Sling": 520, "Winch": 700, "Trigger": 170, "Haul": 80, "Stones": 900, "Pots": 520,
               "Mat": 220}
AO_EXCLUDE = ["Arm", "Sling", "Winch", "Trigger", "Haul", "Stones", "Mallet"]
# the engine and its props are baked 6 m away from him: his rest pose (his left hand hangs over the frame) must leave no
# shadow on it, nor the frame on him
BAKE_APART = (["Frame", "Arm", "Sling", "Winch", "Trigger", "Haul", "Stones", "Pots", "Mat"], (6.0, 0.0, 0.0))


def prop_bones():
    return []                       # the mallet is rigid in his right fist


KICK_P = v3((MX, Y0, 0.0))          # the frame rocks about its front end when the arm slams


def extra_bones():
    """The engine's bones (none of them deform him): frame (it rocks when the arm slams), arm (turns on the skein), sling
    (from the prong to the stone: it trails and whips round as the arm flies), stone (in the pouch), haul (the windlass
    rope, stretched toward the arm), winch (drum and crank), trigger (the pawl), carry (the stone he lifts from the heap)
    and props (the heap, mat and pots: still)."""
    h0, h1 = haul_start(), haul_point(COCK)
    H = hook_pt(COCK)
    return [
        ("frame", KICK_P, KICK_P + v3((0, 0.4, 0)), None),
        ("arm", AXLE, AXLE + arm_dir(COCK) * 0.6, "frame"),
        ("sling", H, SLING_LEFT, "arm"),
        ("stone", SLING_LEFT, SLING_LEFT + v3((0, 0, 0.15)), "sling"),
        ("haul", h0, h1, "frame"),
        ("winch", v3((MX + BW, DRUM[1], DRUM[2])), v3((CRANK_X, DRUM[1], DRUM[2])), "frame"),
        ("trigger", PAWL_P, pawl_tip(), "frame"),
        ("carry", CARRY_C, CARRY_C + v3((0, 0, 0.15)), None),
        ("props", PILE, PILE + v3((0, 0, 0.3)), None),
    ]


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
        bone = min(cs, key=lambda c: np.linalg.norm(cen - c[0]))[1]
        for i in isl:
            _blend_add(ob, groups, i, {bone: 1.0})
    bm.free()


def hair_weights(ob, skin_ob, arm):
    groups = {}
    z1 = hp((0, 0, 1.62))[2]
    for v in ob.data.vertices:
        p = v.co
        t = max(0.0, min(1.0, (z1 - p.z) / 0.15))
        _blend_add(ob, groups, v.index, {"head": 1.0 - 0.5 * t, "neck": 0.5 * t})


def scarf_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        t = max(0.0, min(1.0, (1.47 - p.z) / 0.1))
        _blend_add(ob, groups, v.index, {"neck": 0.6 * (1.0 - t), "chest": 0.4 + 0.6 * t})


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("custom", hair_weights),
        "Scarf": ("custom", scarf_weights),
        "Tunic": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L"},
                  {"thigh.R": 0.45, "thigh.L": 0.45, "upperarm.R": 0.85, "upperarm.L": 0.85}),
        "Leather": ("transfer", TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "thigh.R", "thigh.L", "shin.R", "shin.L",
                                         "foot.R", "foot.L"}, {"thigh.R": 0.25, "thigh.L": 0.25}),
        "Mallet": ("rigid", "hand.R"),
        "Frame": ("rigid", "frame"), "Arm": ("rigid", "arm"), "Sling": ("rigid", "sling"), "Winch": ("rigid", "winch"),
        "Trigger": ("rigid", "trigger"), "Haul": ("rigid", "haul"), "Stones": ("custom", stones_weights),
        "Pots": ("rigid", "props"), "Mat": ("rigid", "props"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Hair") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.8
    if part in ("Frame", "Winch", "Mat", "Pots"):
        return 0.72
    if part in ("Arm", "Stones", "Trigger", "Haul", "Sling"):
        return 0.85
    if part == "Mallet":
        return 0.9
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Tunic", tunic_field(), 0.0026 if fine else 0.0036),
        ("Scarf", scarf_field(), 0.0024 if fine else 0.0034),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Mallet", mallet_field(), 0.002 if fine else 0.003),
        ("Frame", frame_field(), 0.0036 if fine else 0.005),
        ("Arm", arm_field(), 0.003 if fine else 0.0042),
        ("Sling", sling_field(), 0.0022 if fine else 0.003),
        ("Winch", winch_field(), 0.0026 if fine else 0.0036),
        ("Trigger", trigger_field(), 0.0018 if fine else 0.0026),
        ("Haul", haul_field(), 0.0016 if fine else 0.0022),
        ("Stones", stones_field(), 0.0026 if fine else 0.0036),
        ("Pots", pots_field(), 0.0026 if fine else 0.0036),
        ("Mat", mat_field(), 0.0022 if fine else 0.003),
    ]
