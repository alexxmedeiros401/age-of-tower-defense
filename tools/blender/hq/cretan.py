"""The Cretan Archer (HQ tower, Classical Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A lean young bowman from Crete, a hired marksman: tight black curls bound with a red fillet whose ends hang at the back
of his head, a short curly black beard, a straight Greek nose running on from his brow. A white linen corselet (a
linothorax: two flaps drawn forward over his shoulders from the back and tied down on his chest, a red border, a black
key band round the waist) over a short red tunic whose sleeves and skirt show; a skirt of white leather strips (pteruges)
at his hips; bronze greaves moulded to his shins; sandals; a leather bracer on his bow arm. A short horn-and-sinew bow
with a double curve (the limbs bulge out past the grip, sweep back and flick forward at the tips) in his left fist; a
dark leather quiver with bronze bands on his back, its mouth over his right shoulder.

His body and the bow rig are the Bronze Archer's (archer.py): the nocked pair of arrows rides the "arrow" bone, the
string's two halves are bones aimed at his drawing fingers. He shoots kneeling (anim_cretan.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import archer as ar
from archer import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c,
                    smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, torso_prims, traps, neck_prim, deltoid,
                    eyes_field, teeth_field, kilt_base, corselet_base, _forearm, draw_point, ARROW_LEN, arrow_axis,
                    arrows_field, quiver_field, warm_points, TORSO, TORSO_Z, torso_bones, head_hull, Q_BOT, Q_TOP)
from tarek import curls


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.055, 1.59), (0.152, 0.135, 0.128)), 0.07, SKIN)                         # a narrow jaw
    fd.add(E((0, -0.128, 1.502), (0.078, 0.066, 0.064)), 0.05, SKIN)                         # chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.11, -0.12, 1.636), 0.05), 0.05, SKIN)                                 # high cheekbones
        fd.add(S((sx * 0.128, -0.04, 1.552), 0.057), 0.05, SKIN)                               # jaw corners
        pts = [hp((sx * 0.152, -0.055, 1.745)), hp((sx * 0.116, -0.13, 1.752)), hp((sx * 0.06, -0.17, 1.752)), hp((0.0, -0.178, 1.752))]
        fd.add(Chain(pts, [hr(0.012), hr(0.021), hr(0.024), hr(0.024)], k=hr(0.022)), hr(0.035), SKIN)     # brow ridge
    # the Greek profile: the nose runs straight on from the brow, without a dip at the bridge
    fd.add(RoundCone(hp((0, -0.184, 1.752)), hp((0, -0.2, 1.722)), hr(0.016), hr(0.018)), hr(0.02), SKIN)
    fd.add(RoundCone(hp((0, -0.2, 1.722)), hp((0, -0.236, 1.63)), hr(0.019), hr(0.023)), hr(0.016), SKIN)
    fd.add(S((0, -0.236, 1.616), 0.027), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.027, -0.214, 1.603), 0.019), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.015, -0.229, 1.59)), v3((0.009, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # brows: black, gently arched, level: a keen look
    for sx in (-1, 1):
        pts = [hp((sx * 0.026, -0.205, 1.756)), hp((sx * 0.066, -0.2, 1.768)), hp((sx * 0.11, -0.178, 1.77)), hp((sx * 0.148, -0.14, 1.758))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.009), hr(0.011), hr(0.009), hr(0.004)], k=hr(0.007)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.017), hr(0.019), hr(0.016), hr(0.009)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0065)), Plane(ec + v3((0, 0, hr(0.02))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.005)), Plane(ec + v3((0, 0, -hr(0.027))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.017))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
    # mouth: closed, firm
    slot = [hp((-0.058, -0.166, 1.556)), hp((-0.03, -0.192, 1.546)), hp((0, -0.199, 1.544)), hp((0.03, -0.192, 1.546)), hp((0.058, -0.166, 1.556))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.054, -0.163, 1.559), (-0.028, -0.184, 1.554), (-0.008, -0.19, 1.557), (0.008, -0.19, 1.557), (0.028, -0.184, 1.554), (0.054, -0.163, 1.559)]
    lo_lip = [(-0.046, -0.166, 1.547), (-0.024, -0.184, 1.535), (0, -0.188, 1.532), (0.024, -0.184, 1.535), (0.046, -0.166, 1.547)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.004), hr(0.0065), hr(0.007), hr(0.007), hr(0.0065), hr(0.004)], k=hr(0.006)), hr(0.008), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.008), hr(0.0092), hr(0.008), hr(0.005)], k=hr(0.007)), hr(0.008), LIP)
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
        fd.add(RoundCone(sh, el, 0.092, 0.07), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.025, 0)), (0.082, 0.085, 0.122), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)
        fd.add(RoundCone(el, wr, 0.068, 0.053), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.088, 0.078, 0.128), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.054), 0.028, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.132, 0.086), 0.065, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.12, 0.112, 0.182), R=rot_from_axes(z_axis=kn - hip)), 0.048, SKIN)
        fd.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.067), 0.038, SKIN)
        fd.add(RoundCone(kn, an, 0.082, 0.055), 0.038, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.093, 0.09, 0.138), R=rot_from_axes(z_axis=an - kn)), 0.043, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= curly hair, beard
# the hairline round his head, by the angle from the front (0) round to the back (pi): (angle, height) in design units
_HL_A = (0.0, 0.42, 0.7, 0.93, 1.22, 1.62, 2.05, 2.5, 3.2)
_HL_Z = (1.802, 1.806, 1.83, 1.77, 1.715, 1.72, 1.64, 1.585, 1.57)


def hairline_d(P):
    """> 0 below his hairline (bare skin), < 0 above it (hair)."""
    Q = hinv(P)
    a = np.abs(np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.02))))
    zl = np.interp(a, _HL_A, _HL_Z).astype(F) + F(0.004) * NOISE(P * F(30))
    return zl - Q[:, 2]


def hair_field():
    """Tight black curls all over his head: a low hairline straight across the brow, a little notch at each temple, over
    the tops of his ears and down to the nape; a little fuller on the crown."""
    fd = Field("Hair")
    hc, hrad = HEAD_C, HEAD_RAD
    cl = lambda P: curls(P, 0.022, 0.0058)
    line = Func(hairline_d, hc - 0.5, hc + 0.5)
    fd.add(Inter(Ellipsoid(hc + v3((0, 0.004, 0.006)), hrad + 0.016, disp=cl, disp_amp=0.007), line, 0.012), 0.0)
    fd.add(Inter(Ellipsoid(hc + v3((0, 0.012, 0.03)), hrad * v3((0.94, 0.95, 0.9)) + 0.018, disp=cl, disp_amp=0.007), line, 0.012), 0.012)
    return fd


def beard_field():
    """A short curly black beard along the jaw and over the chin, joining his hair in front of the ears; a short
    moustache."""
    fd = Field("Beard")
    hull = head_hull()
    cl = lambda P: curls(P, 0.013, 0.0034)
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.535) + F(0.055) * smoothstep(0.05, 0.14, ax)                      # the chin and jaw, cheeks bare
        top = np.where((ax > F(0.155)) & (y > F(-0.07)), F(1.72), top)              # narrow sideburns up to the hair
        lips = (x / F(0.07)) ** 2 + ((y + F(0.18)) / F(0.07)) ** 2 + ((z - F(1.55)) / F(0.03)) ** 2 - F(1.0)
        neck = np.where(y < F(-0.05), F(1.45), F(1.48)) - z
        back = np.where(ax > F(0.14), y - F(0.07), y - F(0.0))
        return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), neck)
    fd.add(Inter(Shell(hull, 0.004, 0.012, pad=0.06, disp=cl, disp_amp=0.005), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.005), 0.0)
    fd.add(Ellipsoid(hp((0.0, -0.148, 1.478)), v3((0.06, 0.04, 0.04)) * HS, disp=cl, disp_amp=0.005), hr(0.02))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.213, 1.575)), hp((sx * 0.038, -0.2, 1.57)), hp((sx * 0.064, -0.174, 1.552))]
        fd.add(Lock(pts, [hr(0.011), hr(0.014), hr(0.006)], [hr(0.008), hr(0.009), hr(0.004)], [norm(v3((sx * 0.2, -1, 0.3)))] * 3,
                    k=hr(0.006), disp=lambda P: curls(P, 0.01, 0.0025), disp_amp=0.003), hr(0.006))
    return fd


# the fillet round his head: over the curls high on the brow, lower at the back, knotted there
BAND_F = v3((0.0, -0.17, 1.842))
BAND_B = v3((0.0, 0.2, 1.71))
_BAND_N = norm(v3((0, -(BAND_B[2] - BAND_F[2]) / (BAND_B[1] - BAND_F[1]), 1.0)))
KNOT = hp((0.0, 0.236, 1.705))


def band_d(P):
    return (hinv(P) - BAND_F.astype(F)) @ _BAND_N.astype(F)


# ======================================================================================= red tunic (chiton)
HEM_Z = 0.6


def chiton_base():
    b = Field("ChitonBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(RoundCone((0, 0.035, 0.9), (0, 0.035, 0.5), 0.235, 0.31), 0.08)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.055)
        b.add(RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.092, 0.07), 0.05)
    return b


def _sleeve_cut(P):
    """> 0 past the sleeves' ends (a third of the way down the upper arm)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        c = lerp(sh, el, 0.36)
        along = (P - c.astype(F)) @ ax.astype(F)
        sx = -1 if side == "R" else 1
        out = np.maximum(out, np.where(P[:, 0] * F(sx) > F(0.25), along, F(-1.0)))
    return out


def chiton_hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(HEM_Z) + F(0.02) * np.cos(a * 2) + F(0.008) * NOISE(P * F(9))


def chiton_field():
    """A short tunic of red wool: its sleeves to a third of the way down his upper arms, its skirt to mid-thigh below
    the leather strips, folds in the skirt; a cream border (label 5) round the hem and the sleeves' ends. Under the
    corselet it is cut away (only what shows is built)."""
    fd = Field("Chiton")
    base = chiton_base()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        k = smoothstep(0.92, 0.7, P[:, 2])
        return F(0.005) * np.sin(a * F(14) + F(0.8) * NOISE(P * F(3))) * k + F(0.0015) * NOISE(P * F(25))
    def keep(P):
        x, z = P[:, 0], P[:, 2]
        hidden = np.minimum(np.minimum(z - F(1.0), F(0.24) - np.abs(x)), F(1.27) + F(0.16) * smoothstep(0.06, 0.16, P[:, 1]) - z)
        neck = z - (F(1.47) - F(0.03) * np.exp(-(x / F(0.1)) ** 2) + F(0.3) * smoothstep(0.13, 0.21, np.abs(x)))   # a ring: the shoulders stay covered
        return np.maximum(np.maximum(np.maximum(neck, _sleeve_cut(P)), chiton_hem(P) - z), hidden)
    fd.add(Inter(Shell(base, 0.016, 0.02, pad=0.1, disp=folds, disp_amp=0.006), Func(keep, (-1, -1, 0.4), (1, 1, 1.6)), 0.005), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (chiton_hem(P) + F(0.03)), (-1, -1, 0.4), (1, 1, 0.75)), 5)
    fd.paint(Func(lambda P: np.maximum(-_sleeve_cut(P) - F(0.028), F(1.0) - P[:, 2]), (-1, -1, 1.0), (1, 1, 1.6)), 5)
    return fd


# ======================================================================================= linen corselet, leather strips
CORS_BOT = 0.94


def _flap_band(P):
    """< 0 inside the two shoulder flaps (over each shoulder, a hand's width, from the back to the tie on his chest)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    across = np.abs(ax - F(0.148)) - F(0.064)
    front_end = np.where(y < F(0.0), F(1.255) - z, F(-1.0))                 # they end on his chest
    return np.maximum(np.maximum(across, front_end), F(1.2) - z)


def linothorax_field():
    """The linothorax: a tube of stiffened white linen round his chest from the armpits to the waist (higher at the back,
    up to the nape), two flaps drawn forward over his shoulders and tied down on his chest (red cord knots); a red border
    (label 5) along the bottom edge and the flaps' edges, a black key band (6) round the waist. Below it two rows of
    white leather strips (pteruges), each strip fringed red at its end."""
    fd = Field("Linen")
    base = corselet_base()
    stiff = lambda P: F(0.0012) * NOISE(P * F(30))
    def keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        bottom = F(CORS_BOT) - z
        back = smoothstep(0.06, 0.16, y)                                  # the back plate, behind the arms
        top = z - (F(1.3) + F(0.16) * back * smoothstep(0.3, 0.2, np.abs(x)))
        return np.maximum(bottom, top)
    fd.add(Inter(Shell(base, 0.03, 0.02, pad=0.12, disp=stiff, disp_amp=0.003), Func(keep, (-1, -1, 0.8), (1, 1, 1.6)), 0.005), 0.0)
    # the shoulder flaps, lying over the tube's top edge
    fd.add(Inter(Shell(base, 0.046, 0.012, pad=0.12, disp=stiff, disp_amp=0.003), Func(_flap_band, (-0.5, -0.5, 1.1), (0.5, 0.5, 1.7)), 0.004), 0.004)
    # red cord knots tying the flaps down
    for sx in (-1, 1):
        p, ok = ray_hit(Func(lambda P: base.eval(P, margin=0.1) - F(0.06), (-1, -1, 1.0), (1, 1, 1.6)), [v3((sx * 0.148, -0.7, 1.275))],
                        [v3((0, 1, 0))], tmax=0.8)
        c = p[0] if ok[0] else v3((sx * 0.148, -0.25, 1.275))
        fd.add(Sphere(c + v3((0, -0.006, 0)), 0.017), 0.006, 5)
        for dx in (-1, 1):
            fd.add(Chain([c, c + v3((dx * 0.018, -0.008, -0.04)), c + v3((dx * 0.024, -0.01, -0.07))], [0.007, 0.006, 0.004], k=0.004), 0.004, 5)
    fd.paint(Func(lambda P: P[:, 2] - F(CORS_BOT + 0.024), (-1, -1, 0.8), (1, 1, 1.1)), 5)
    fd.paint(Func(lambda P: np.maximum(-(_flap_band(P) + F(0.016)), _flap_band(P)), (-0.5, -0.5, 1.1), (0.5, 0.5, 1.7)), 5)
    def key(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.05)))
        band = np.abs(P[:, 2] - F(1.0)) - F(0.018)
        gaps = F(0.4) - np.abs(np.sin(a * F(15)))                      # dark blocks with light gaps between them
        inner = np.where(np.abs(P[:, 2] - F(1.0)) < F(0.007), F(0.6) - np.abs(np.sin(a * F(15) + F(1.57))), F(-1.0))
        return np.maximum(band, np.maximum(gaps, inner))
    fd.paint(Func(key, (-1, -1, 0.9), (1, 1, 1.1)), 6)
    # pteruges: two rows of strips, grooved apart (grooves, not slits: a strip cut free falls apart in the decimation).
    # Only the outer face is grooved and the outer row's inner face is sunk into the inner row, so the two rows are one
    # solid: a groove thinning a Shell from both sides (or a hair gap between the rows) leaves pinholes in the mesh, and
    # every pinhole is a handle the decimator cannot collapse (the first cut had ~880 of them and stuck at 9k tris)
    kb = kilt_base()
    for off_in, off_out, z1, n_str, ph in ((0.035, 0.052, 0.745, 26, 0.0), (0.041, 0.067, 0.835, 22, 0.5)):
        def strips(P, off_in=off_in, off_out=off_out, n=n_str, ph=ph):
            d = kb.eval(P, margin=0.12)
            a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
            s = np.mod(a * F(n / (2 * math.pi)) + F(ph), F(1.0))
            groove = F(0.004) * smoothstep(0.08, 0.0, np.minimum(s, F(1) - s)) + F(0.001) * NOISE(P * F(40))
            return np.maximum(d - (F(off_out) - groove), F(off_in) - d)
        def keep2(P, z1=z1, n=n_str, ph=ph):
            a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
            s = np.mod(a * F(n / (2 * math.pi)) + F(ph), F(1.0))
            round_end = F(0.012) * (F(1) - (F(2) * s - F(1)) ** 2)            # each strip's end rounded
            return np.maximum(F(z1) - round_end - P[:, 2], P[:, 2] - F(CORS_BOT + 0.03))
        fd.add(Inter(Func(strips, (-0.6, -0.6, 0.6), (0.6, 0.6, 1.1)), Func(keep2, (-1, -1, 0.6), (1, 1, 1.05)), 0.003), 0.003)
        fd.paint(Func(lambda P, z1=z1: np.maximum(P[:, 2] - F(z1 + 0.03), F(z1 - 0.05) - P[:, 2]), (-1, -1, 0.6), (1, 1, 1.0)), 5)
    return fd


# ======================================================================================= bronze greaves
def _shin(side):
    f = Field("Shin")
    kn, an = J["knee_" + side], J["ankle_" + side]
    f.add(RoundCone(kn, an, 0.082, 0.055), 0.0)
    f.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.093, 0.09, 0.138), R=rot_from_axes(z_axis=an - kn)), 0.043)
    f.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.067), 0.038)
    return f


def bronze_field():
    """Bronze greaves moulded to his shins and knees, open at the back of the calf, a rolled rim top and bottom."""
    fd = Field("Bronze")
    for side in ("R", "L"):
        kn, an = J["knee_" + side], J["ankle_" + side]
        ax = norm(an - kn)
        L = float(np.linalg.norm(an - kn))
        shin = _shin(side)
        def keep(P, kn=kn, ax=ax, L=L):
            t = (P - kn.astype(F)) @ ax.astype(F)
            span = np.maximum(F(-0.07) - t, t - F(L * 0.84))
            c = kn.astype(F) + t[:, None] * ax.astype(F)
            back = (P[:, 1] - c[:, 1]) - F(0.045)
            return np.maximum(span, back)
        mould = lambda P: F(0.001) * NOISE(P * F(30))
        fd.add(Inter(Shell(shin, 0.008, 0.008, pad=0.08, disp=mould, disp_amp=0.002), Func(keep, kn - 0.3, an + 0.3), 0.004), 0.0)
        for t0 in (-0.07, L * 0.84):
            def rim(P, t0=t0, kn=kn, ax=ax):
                t = (P - kn.astype(F)) @ ax.astype(F)
                c = kn.astype(F) + t[:, None] * ax.astype(F)
                return np.maximum(np.abs(t - F(t0)) - F(0.009), (P[:, 1] - c[:, 1]) - F(0.045))
            fd.add(Inter(Shell(shin, 0.013, 0.007, pad=0.08), Func(rim, kn - 0.3, an + 0.3), 0.003), 0.004)
    return fd


# ======================================================================================= leather: fillet, strap, bracer, sandals
def baldric_plane():
    """The quiver strap runs from his right shoulder across his chest to his left hip."""
    a, b = v3((-0.22, 0.0, 1.43)), v3((0.24, 0.0, 0.94))
    d = norm(b - a)
    n = norm(np.cross(d, v3((0, 1, 0))))
    return a, n


def leather_field():
    """The red fillet round his curls (label 5) with its ends hanging from a knot at the back, the quiver strap over the
    corselet, a bracer on his bow arm and a wrap on his right wrist, sandals."""
    fd = Field("Leather")
    hc, hrad = HEAD_C, HEAD_RAD
    fd.add(Inter(Shell(Ellipsoid(hc + v3((0, 0.004, 0.006)), hrad), 0.014, 0.014, pad=0.08),
                 Func(lambda P: np.abs(band_d(P)) - F(0.0125), hc - 0.4, hc + 0.4), 0.004), 0.0, 5)
    fd.add(Sphere(KNOT, hr(0.022)), hr(0.01), 5)
    for sx in (-1, 1):
        pts = [KNOT + v3((sx * 0.01, 0.005, -0.01)), KNOT + v3((sx * 0.03, 0.03, -0.07)), KNOT + v3((sx * 0.036, 0.035, -0.13))]
        fd.add(Lock(pts, [hr(0.02), hr(0.022), hr(0.02)], [hr(0.005), hr(0.005), hr(0.004)], [v3((0, 1, 0))] * 3, k=hr(0.004)), hr(0.005), 5)
    cb = corselet_base()
    a, n = baldric_plane()
    fd.add(Inter(Shell(cb, 0.06, 0.012, pad=0.12), Func(lambda P: np.abs((P - a.astype(F)) @ n.astype(F)) - F(0.026), (-1, -1, 0.8), (1, 1, 1.6)), 0.004), 0.0)
    for side, length in (("L", 0.075), ("R", 0.03)):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.66 if side == "L" else 0.86)
        fd.add(Inter(Shell(_forearm(side), 0.012, 0.016, pad=0.06), Func(lambda P, c=c, ax=ax, L=length: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(L), c - 0.25, c + 0.25), 0.004), 0.0)
        if side == "L":
            for j in (-1, 0, 1):
                cc = c + ax * (j * 0.04)
                fd.add(Inter(Shell(_forearm(side), 0.02, 0.006, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.006), cc - 0.2, cc + 0.2), 0.002), 0.003, 5)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.1)), (0.074, 0.15, 0.011), 0.009, R=Rz), 0.0)
        ft = Field("FootHull")
        foot(ft, side)
        for c, rad in ((an + fwd * 0.14 + v3((0, 0, -0.07)), 0.022), (an + fwd * 0.05 + v3((0, 0, -0.035)), 0.02)):
            fd.add(Inter(Shell(ft, 0.006, 0.01, pad=0.05), Func(lambda P, c=c, fwd=fwd, rad=rad: np.abs((P - c.astype(F)) @ fwd.astype(F)) - F(rad * 0.6), c - 0.15, c + 0.15), 0.003), 0.002)
        fd.add(Torus(an + v3((0, 0.004, 0.035)), 0.06, 0.008), 0.003)
    return fd


# ======================================================================================= the double-curved bow, its string
BOW_HALF = 0.56


def bow_frame():
    return ar.bow_frame()


def _bow_back_np(a):
    a = np.abs(np.asarray(a, dtype=np.float64))
    bulge = np.where(a < 0.55, 0.045 * np.sin(math.pi * np.minimum(a, 0.55) / 0.55), 0.0)
    flick = 0.16 * np.clip((a - 0.7) / 0.3, 0.0, 1.0) ** 2
    return bulge - 0.24 * a * a + flick


def bow_back(a):
    """Offset along the bow's back (the way the arrow flies): past the grip the limbs bulge forward, then sweep back
    toward the archer, and the tips flick forward again (the Scythian bow's double curve)."""
    return float(_bow_back_np(a))


def bow_point(s):
    G, A, B, S = bow_frame()
    return G + A * (s * BOW_HALF) + B * bow_back(s)


def bow_tips():
    return bow_point(1.0), bow_point(-1.0)


def string_mid():
    t1, t2 = bow_tips()
    return (t1 + t2) / 2


def bow_field():
    """Horn-and-sinew limbs (dark lacquer, a cream horn belly (label 7)), the grip bound in red cord (5), bone nocks at
    the tips (6)."""
    fd = Field("Bow")
    G, A, B, S = bow_frame()
    ss = np.linspace(-1.0, 1.0, 33)
    pts = [bow_point(s) for s in ss]
    ws = [0.031 - 0.016 * abs(s) ** 1.1 for s in ss]
    ts = [0.026 - 0.013 * min(1.0, abs(s) * 1.5) for s in ss]
    grain = lambda P: F(0.001) * NOISE(P * F(80))
    fd.add(Lock(pts, ws, ts, [B] * len(pts), k=0.012, disp=grain, disp_amp=0.002), 0.0)
    fd.add(Ellipsoid(G, (0.026, 0.026, 0.07), R=rot_from_axes(z_axis=A, y_axis=B)), 0.012)
    for s in (1.0, -1.0):
        tp = bow_point(s)
        d = norm(bow_point(s) - bow_point(s * 0.94))
        fd.add(RoundCone(tp - d * 0.045, tp + d * 0.014, 0.012, 0.009), 0.004)
    def along(P):
        return ((P - G.astype(F)) @ A.astype(F)) / F(BOW_HALF)
    fd.paint(Func(lambda P: np.abs(along(P)) - F(0.12), G - 0.3, G + 0.3), 5)
    fd.paint(Func(lambda P: F(0.91) - np.abs(along(P)), G - 1.0, G + 1.0), 6)
    def belly(P):
        s = np.clip(along(P), -1, 1)
        back = _bow_back_np(s).astype(F)
        lb = (P - G.astype(F)) @ B.astype(F) - back
        return np.maximum(lb + F(0.004), np.maximum(np.abs(along(P)) - F(0.91), F(0.13) - np.abs(along(P))))
    fd.paint(Func(belly, G - 1.0, G + 1.0), 7)
    return fd


def string_field():
    fd = Field("String")
    t1, t2 = bow_tips()
    fd.add(Chain([t1, string_mid(), t2], [0.0048, 0.0048, 0.0048], k=0.002), 0.0)
    return fd


# ======================================================================================= build config
GLB_NAME = "cretan_archer"
ROOT_NAME = "CretanArcherHQ"
TEX_PREFIX = "cretan"
MAT_NAME = "CretanMat"
MESH_NAME = "Cretan"
BASE_MODULE = "cretan_base"
ANIM_MODULE = "anim_cretan"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Chiton", "Linen", "Bronze", "Leather", "Bow", "String", "Arrows", "Quiver"]
REGION_PARTS = ("Skin", "Chiton", "Linen", "Leather", "Bow", "Arrows", "Quiver")
BLACK_HAIR = {"name": "HQ_CretanHair", "base": (0.075, 0.06, 0.055), "hi": (0.3, 0.25, 0.22), "low": (0.03, 0.025, 0.024),
              "streak": (0.05, 0.04, 0.035), "tint": (0.16, 0.11, 0.09)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_CretanSkin", "base": (0.76, 0.52, 0.35), "ruddy": (0.8, 0.45, 0.32), "lips": (0.64, 0.36, 0.3),
                      "brow": ((0.05, 0.04, 0.035), (0.13, 0.095, 0.08)), "extra": ((8, (0.05, 0.035, 0.03), 0.5),)}),
    "Hair": ("hair", BLACK_HAIR),
    "Beard": ("hair", dict(BLACK_HAIR, name="HQ_CretanBeard")),
    "Chiton": ("wool", {"name": "HQ_CretanChiton", "base": (0.72, 0.13, 0.08), "border": (0.93, 0.86, 0.7), "stripe": (0.12, 0.1, 0.1)}),
    "Linen": ("linen", {"name": "HQ_Linothorax", "base": (0.95, 0.93, 0.86), "border": (0.74, 0.12, 0.07), "stripe": (0.1, 0.08, 0.07)}),
    "Bronze": ("bronze", {"name": "HQ_CretanBronze"}),
    "Leather": ("leather_dyed", {"name": "HQ_CretanLeather", "base": (0.4, 0.24, 0.13), "dyed": (0.72, 0.11, 0.07)}),
    "Bow": ("bow", {"name": "HQ_CretanBow"}),
    "String": ("cord", {}),
    "Arrows": ("arrows", {"name": "HQ_CretanArrows"}),
    "Quiver": ("quiver", {"name": "HQ_CretanQuiver", "base": (0.3, 0.17, 0.09)}),
}
LOW_TARGETS = {"Skin": 6400, "Hair": 1300, "Beard": 700, "Teeth": 60, "Chiton": 1500, "Linen": 2800, "Bronze": 900,
               "Leather": 1500, "Bow": 900, "String": 120, "Arrows": 520, "Quiver": 1300}
AO_EXCLUDE = ["Bow", "String", "Arrows"]


def prop_bones():
    p0, ax = arrow_axis()
    return [("arrow", p0, p0 + ax * 0.3, "hand.R")]


def extra_bones():
    t1, t2 = bow_tips()
    m = string_mid()
    return [("string_top", t1, m, "hand.L"), ("string_bot", t2, m, "hand.L")]


def leather_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "forearm.R", "forearm.L", "hand.R", "hand.L",
                                                       "shin.R", "shin.L", "foot.R", "foot.L", "head"})
    a, n = baldric_plane()
    groups = {}
    z_head = hp((0, 0, 1.6))[2]
    for v in ob.data.vertices:
        p = v.co
        w = None
        if p.z > z_head and abs(p.x) < 0.3 and p.y > -0.3:                         # the fillet and its knot
            w = {"head": 1.0}
        elif p.y > 0.15 and 1.4 < p.z <= z_head and abs(p.x) < 0.12:               # its hanging ends
            t = max(0.0, min(1.0, (z_head - p.z) / 0.16))
            w = {"head": 1.0 - 0.6 * t, "neck": 0.6 * t}
        elif 1.0 < p.z < 1.52 and abs(float((np.array(p) - a) @ n)) < 0.05 and abs(p.x) < 0.36:
            w = {"chest": 0.8, "spine": 0.2} if p.z < 1.25 else {"chest": 1.0}
        if w is not None:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, w)


def hair_weights(ob, skin_ob, arm):
    groups = {}
    z1 = hp((0, 0, 1.62))[2]
    for v in ob.data.vertices:
        p = v.co
        if p.z < z1:
            t = max(0.0, min(1.0, (z1 - p.z) / 0.16))
            _blend_add(ob, groups, v.index, {"head": 1.0 - 0.6 * t, "neck": 0.6 * t})
        else:
            _blend_add(ob, groups, v.index, {"head": 1.0})


def bronze_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"shin.R" if v.co.x < 0 else "shin.L": 1.0})


def string_weights(ob, skin_ob, arm):
    G, A, B, S = bow_frame()
    groups = {}
    for v in ob.data.vertices:
        top = float((np.array(v.co) - G) @ A) > 0
        _blend_add(ob, groups, v.index, {"string_top" if top else "string_bot": 1.0})


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Beard": ("rigid", "head"), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Chiton": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L"},
                   {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Linen": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "thigh.R", "thigh.L"}, {"thigh.R": 0.3, "thigh.L": 0.3}),
        "Bronze": ("custom", bronze_weights), "Leather": ("custom", leather_weights),
        "Bow": ("rigid", "hand.L"), "String": ("custom", string_weights), "Arrows": ("rigid", "arrow"),
        "Quiver": ("rigid", "chest"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("String", "Arrows"):
        return 0.6
    if part == "Bow":
        return 0.8
    if part == "Skin" and abs(c.x) > 0.6 and c.z < 1.0:
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Beard", beard_field(), 0.0022 if fine else 0.003),
        ("Chiton", chiton_field(), 0.0026 if fine else 0.0036),
        ("Linen", linothorax_field(), 0.0024 if fine else 0.0034),
        ("Bronze", bronze_field(), 0.0022 if fine else 0.0032),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Bow", bow_field(), 0.0018 if fine else 0.0024),
        ("String", string_field(), 0.0012 if fine else 0.0016),
        ("Arrows", arrows_field(), 0.0014 if fine else 0.0018),
        ("Quiver", quiver_field(), 0.0022 if fine else 0.003),
    ]
