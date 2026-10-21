"""The Crossbowman (HQ tower, Medieval Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A stocky veteran of the free companies, a hired marksman in his forties: a broad weathered face, full ruddy cheeks, a big
round nose broken long ago, small sharp eyes (the left one squinting: he aims with the right), bushy brown brows, a
close-trimmed brown beard and a thick drooping moustache. A steel kettle hat (a round crown with a raised comb from front
to back, a wide brim turned down all round with a rolled edge, rivets round the crown's foot) over a mail coif that frames
his face and falls over his shoulders in a short cape, brass rings along its edges. A padded gambeson of blue linen
quilted in upright channels (its long sleeves quilted in rings) to mid-thigh; a broad leather belt with a brass buckle, a
box quiver of bolts at his right hip (hide over wood, an iron rim, the bolts' vanes dyed yellow and blue), a dagger at his
left hip; parti-coloured hose (his right leg yellow, his left blue); brown leather gloves; mid-calf boots with
turned-down cuffs.

The crossbow: a stout walnut stock (the butt painted blue with a yellow band), a steel prod lashed through its front with
cord bridles, an iron stirrup, a bone nut, a long iron trigger lever under the stock, the string, and a bolt in the groove
(a thick shaft, a square bodkin head, two leather vanes).

His body, hands and fists are the Spear Guard's (spear.py). The crossbow is rigid in his left fist, which holds the
fore-stock from below; his right hand takes the stock's wrist to shoot, and spans the string between shots ("frame" aims
in anim_crossbowman.py). The string is two bones from the prod's tips to its middle; the bolt rides its own bone (its
scale hides it from the shot until the reload)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import spear as sp
from spear import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R,
                   eye_c, smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, torso_prims, traps, neck_prim,
                   deltoid, eyes_field, teeth_field, kilt_base, _forearm, TORSO, TORSO_Z, torso_bones)

RED_NOSE = 10


# ======================================================================================= head
def head(fd):
    """A broad weathered face: full cheeks, a big round nose (broken: a bump on the bridge, set a little to his left),
    heavy brows, the left eye squinting."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.06, 1.586), (0.15, 0.136, 0.13)), 0.07, SKIN)                             # a broad round jaw
    fd.add(E((0, -0.132, 1.5), (0.086, 0.07, 0.066)), 0.05, SKIN)                             # chin (under the beard)
    for sx in (-1, 1):
        fd.add(S((sx * 0.108, -0.126, 1.62), 0.054), 0.05, SKIN)                                # full cheeks
        fd.add(S((sx * 0.128, -0.05, 1.56), 0.052), 0.05, SKIN)                                 # jowls
        pts = [hp((sx * 0.152, -0.055, 1.744)), hp((sx * 0.116, -0.13, 1.752)), hp((sx * 0.06, -0.176, 1.75)), hp((0.0, -0.186, 1.75))]
        fd.add(Chain(pts, [hr(0.013), hr(0.025), hr(0.029), hr(0.028)], k=hr(0.022)), hr(0.035), SKIN)     # heavy brow ridge
    # bushy brown brows; the left one drawn down over the squinting eye
    tuft = lambda P: F(0.0022) * NOISE(P * F(150)) + F(0.001) * np.sin(P[:, 0] * F(380))
    for sx in (-1, 1):
        dz = -0.008 if sx > 0 else 0.0
        pts = [hp((sx * 0.024, -0.214, 1.755 + dz)), hp((sx * 0.066, -0.208, 1.768 + dz)), hp((sx * 0.11, -0.186, 1.772 + dz * 0.6)),
               hp((sx * 0.15, -0.146, 1.762))]
        fd.add(Chain([p + v3((0, 0.005, 0)) for p in pts], [hr(0.012), hr(0.015), hr(0.013), hr(0.006)], k=hr(0.008),
                     disp=tuft, disp_amp=0.003), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.02), hr(0.023), hr(0.02), hr(0.011)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        squint = sx > 0
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.008 if squint else 0.021))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0058)), Plane(ec + v3((0, 0, -hr(0.012 if squint else 0.024))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)),
                       Plane(ec + v3((0, 0, hr(0.006 if squint else 0.019))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(3 if squint else 2):                                                   # crow's feet
            a = hp((sx * (0.112 + 0.004 * k), -0.13 + 0.006 * k, 1.684 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.026, 0.012, 0.006 - 0.01 * k)), hr(0.0022), hr(0.0014)), hr(0.003))
        fd.add(Ellipsoid(hp((sx * 0.07, -0.152, 1.643)), v3((0.026, 0.012, 0.011)) * HS), hr(0.012), SKIN)     # bags
    # a big round nose, broken long ago: a bump on the bridge, the tip set a little to his left
    fd.add(RoundCone(hp((0, -0.186, 1.724)), hp((0.006, -0.234, 1.636)), hr(0.017), hr(0.026)), hr(0.017), SKIN)
    fd.add(S((-0.006, -0.212, 1.688), 0.018), hr(0.012), SKIN)
    fd.add(S((0.008, -0.248, 1.612), 0.037), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.037 + 0.006, -0.222, 1.598), 0.023), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.019 + 0.006, -0.242, 1.585)), v3((0.01, 0.012, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    fd.paint(Sphere(hp((0.008, -0.25, 1.612)), hr(0.034)), RED_NOSE)
    # mouth: a firm line under the moustache; a full lower lip
    slot = [hp((-0.056, -0.168, 1.548)), hp((-0.03, -0.193, 1.54)), hp((0, -0.2, 1.539)), hp((0.03, -0.193, 1.54)), hp((0.056, -0.168, 1.548))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.046, -0.168, 1.538), (-0.024, -0.188, 1.528), (0, -0.192, 1.525), (0.024, -0.188, 1.528), (0.046, -0.168, 1.538)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.0085), hr(0.0095), hr(0.0085), hr(0.005)], k=hr(0.007)), hr(0.008), LIP)


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
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.135, 0.088), 0.065, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.122, 0.115, 0.185), R=rot_from_axes(z_axis=kn - hip)), 0.048, SKIN)
        fd.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.068), 0.038, SKIN)
        fd.add(RoundCone(kn, an, 0.084, 0.056), 0.038, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.095, 0.092, 0.14), R=rot_from_axes(z_axis=an - kn)), 0.043, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= beard
def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.06, 1.586), (0.15, 0.136, 0.13)), 0.07)
    fd.add(E((0, -0.132, 1.5), (0.086, 0.07, 0.066)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.108, -0.126, 1.62)), hr(0.054)), 0.05)
        fd.add(Sphere(hp((sx * 0.128, -0.05, 1.56)), hr(0.052)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


def beard_field():
    """A close-trimmed brown beard on his jaw and chin (his cheeks bare), and a thick moustache drooping past his mouth."""
    fd = Field("Beard")
    hull = head_hull()
    hairs = lambda P: F(0.0016) * NOISE(P * np.array([90, 90, 30], F)) + F(0.0009) * NOISE(P * F(170))
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.548) + F(0.05) * smoothstep(0.05, 0.14, ax)
        lips = (x / F(0.066)) ** 2 + ((y + F(0.18)) / F(0.07)) ** 2 + ((z - F(1.542)) / F(0.026)) ** 2 - F(1.0)
        return np.maximum(np.maximum(np.maximum(z - top, y - F(0.0)), -lips * F(0.03)), F(1.45) - z)
    fd.add(Inter(Shell(hull, 0.004, 0.012, pad=0.06, disp=hairs, disp_amp=0.003), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.005), 0.0)
    fd.add(Ellipsoid(hp((0.0, -0.152, 1.486)), v3((0.066, 0.046, 0.046)) * HS, disp=hairs, disp_amp=0.003), hr(0.02))
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.228, 1.58)), hp((sx * 0.046, -0.214, 1.566)), hp((sx * 0.072, -0.192, 1.538)),
               hp((sx * 0.08, -0.178, 1.502))]
        fd.add(Lock(pts, [hr(0.016), hr(0.021), hr(0.016), hr(0.009)], [hr(0.011), hr(0.013), hr(0.01), hr(0.006)],
                    [norm(v3((sx * 0.3, -1, 0.15)))] * 4, k=hr(0.006), disp=strands, disp_amp=0.003), hr(0.006))
    return fd


# ======================================================================================= mail coif
COIF_HEM_Z = 1.31          # the cape's hem over his shoulders


def coif_head_base():
    b = Field("CoifHead")
    b.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    b.add(E((0, -0.06, 1.586), (0.15, 0.136, 0.13)), 0.07)
    b.add(E((0, -0.132, 1.5), (0.086, 0.07, 0.066)), 0.05)
    for sx in (-1, 1):
        b.add(Sphere(hp((sx * 0.128, -0.05, 1.56)), hr(0.052)), 0.05)
    return b


def mantle_base():
    """The shoulders and the top of the chest (no pectorals: the cape lies smooth over the padding)."""
    b = Field("Mantle")
    b.add(Ellipsoid((0, 0.05, 1.22), (0.27, 0.21, 0.27), R=euler(-0.12, 0, 0)), 0.0)
    b.add(traps(), 0.06)
    b.add(neck_prim(), 0.05)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.055)
    return b


def coif_open(P):
    """< 0 inside the face opening: an oval from his brow to under his chin, cheekbone to cheekbone (front only)."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    e = np.sqrt((x / F(0.118)) ** 2 + ((z - F(1.628)) / F(0.176)) ** 2) - F(1.0)
    return np.maximum(e * F(0.12), y + F(0.03))


def coif_hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.06)))
    return F(COIF_HEM_Z) - F(0.05) * np.abs(np.sin(a)) + F(0.008) * np.sin(a * F(9)) + F(0.004) * NOISE(P * F(12))


def mail_field():
    """The coif: mail over his head and neck, the face left open, falling over his shoulders in a short cape; a band of
    brass rings (label 5) along the face opening and the hem."""
    fd = Field("Mail")
    hb = coif_head_base()
    mb = mantle_base()
    drape = lambda P: F(0.0015) * NOISE(P * F(25))
    lo, hi = v3((-0.6, -0.5, 1.0)), v3((0.6, 0.5, 2.1))
    def keep(P):
        return np.maximum(-coif_open(P), coif_hem(P) - P[:, 2])
    shape = Field("CoifShape")
    shape.add(Shell(hb, 0.012, 0.012, pad=0.08, disp=drape, disp_amp=0.002), 0.0)
    shape.add(Inter(Shell(mb, 0.05, 0.012, pad=0.12, disp=drape, disp_amp=0.002),
                    Func(lambda P: P[:, 2] - F(1.62), lo, hi), 0.02), 0.03)
    fd.add(Inter(Func(lambda P: shape.eval(P), lo, hi), Func(keep, lo, hi), 0.004), 0.0)
    # a roll of mail round the face (the coif's edge turned back)
    def face_rim(P):
        return np.maximum(np.abs(coif_open(P) + F(0.006)) - F(0.008), hinv(P)[:, 1] - F(0.06))
    fd.add(Inter(Shell(hb, 0.016, 0.014, pad=0.08), Func(face_rim, lo, hi), 0.003), 0.004)
    fd.paint(Func(lambda P: np.minimum(np.maximum(coif_open(P) - F(0.012), -coif_open(P) - F(0.03)),
                                       P[:, 2] - (coif_hem(P) + F(0.028))), lo, hi), 5)
    return fd


# ======================================================================================= kettle hat
HAT_C = hp((0.0, 0.032, 1.78))             # the crown's centre
HAT_R = v3((0.218, 0.231, 0.19))
BRIM_Z = hp((0.0, 0.0, 1.81))[2]           # where the brim leaves the crown
BRIM_IN, BRIM_OUT = 0.2, 0.345
BRIM_SLOPE = 0.34


def brim_z(r):
    return BRIM_Z - BRIM_SLOPE * (r - BRIM_IN)


def comb_points(lift=0.0, n=24):
    hull = Ellipsoid(HAT_C, HAT_R + 0.008)
    pts = []
    for k in range(n):
        th = math.radians(12 + 156 * k / (n - 1))
        d = v3((0, -math.cos(th), math.sin(th)))
        o = HAT_C + d * 0.6
        h, ok = ray_hit(Func(lambda P: hull(P), HAT_C - 0.5, HAT_C + 0.5), [o], [-d], tmax=0.7)
        if ok[0] and h[0][2] > BRIM_Z + 0.012:
            pts.append(h[0] + d * lift)
    return pts


def steel_field():
    """The kettle hat: a round crown (plain steel, label 0) with a raised comb from front to back, a wide brim sloping down
    all round to a rolled edge, rivets round the crown's foot."""
    fd = Field("Steel")
    hammer = lambda P: F(0.0008) * NOISE(P * F(50))
    crown = Inter(Shell(Ellipsoid(HAT_C, HAT_R), 0.004, 0.008, pad=0.06, disp=hammer, disp_amp=0.001),
                  Plane(v3((0, 0, BRIM_Z - 0.004)), (0, 0, -1)), 0.003)
    fd.add(crown, 0.0)
    ridge = comb_points(lift=0.006)
    fd.add(Chain(ridge, [0.009] * len(ridge), k=0.004), 0.005)
    def brim(P):
        q = P - HAT_C.astype(F)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        zb = F(BRIM_Z) - F(BRIM_SLOPE) * (r - F(BRIM_IN))
        return np.maximum(np.abs(P[:, 2] - zb) * F(0.95) - F(0.004), np.maximum(F(BRIM_IN - 0.012) - r, r - F(BRIM_OUT)))
    fd.add(Func(brim, HAT_C + v3((-0.4, -0.4, -0.12)), HAT_C + v3((0.4, 0.4, 0.08)), disp=hammer, disp_amp=0.001), 0.006)
    fd.add(Torus(v3((HAT_C[0], HAT_C[1], brim_z(BRIM_OUT) - 0.002)), BRIM_OUT, 0.0068), 0.004)
    # the crown's foot: a band, rivets
    fd.add(Inter(Shell(Ellipsoid(HAT_C, HAT_R), 0.01, 0.01, pad=0.06),
                 Func(lambda P: np.abs(P[:, 2] - F(BRIM_Z + 0.012)) - F(0.011), HAT_C - 0.4, HAT_C + 0.4), 0.002), 0.004)
    hull = Ellipsoid(HAT_C, HAT_R + 0.014)
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        d = v3((math.sin(a), -math.cos(a), 0.0))
        o = v3((HAT_C[0], HAT_C[1], BRIM_Z + 0.012)) + d * 0.5
        h, ok = ray_hit(Func(lambda P: hull(P), HAT_C - 0.5, HAT_C + 0.5), [o], [-d], tmax=0.6)
        if ok[0]:
            fd.add(Sphere(h[0], 0.0075), 0.002)
    return fd


# ======================================================================================= gambeson (quilted blue linen)
HEM_Z = 0.52


def gambeson_base():
    b = Field("GambesonBase")
    tp = torso_prims()
    for i, (p, k) in enumerate(tp):
        if i in (2, 3):                     # (no pectorals: the padding lies smooth and round over the chest)
            continue
        b.add(p, k)
    b.add(Ellipsoid((0, -0.055, 1.29), (0.27, 0.16, 0.19)), 0.06)          # (big enough to cover his chest)
    b.add(traps(), 0.06)
    b.add(RoundCone((0, 0.035, 0.92), (0, 0.035, 0.47), 0.24, 0.31), 0.08)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        b.add(deltoid(side), 0.055)
        b.add(RoundCone(sh, el, 0.095, 0.072), 0.05)
        b.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.025, 0)), (0.085, 0.088, 0.125), R=rot_from_axes(z_axis=el - sh)), 0.04)
        b.add(RoundCone(el, wr, 0.07, 0.056), 0.035)
        b.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.09, 0.08, 0.13), R=rot_from_axes(z_axis=wr - el)), 0.04)
        b.add(Sphere(el + v3((0, 0.025, 0)), 0.055), 0.028)
    return b


def _arm_coord(P, side):
    """Distance along his arm from the shoulder (upper arm, then forearm) and the squared distance off its axis."""
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    out_s = None
    out_d = None
    acc = 0.0
    for a, b in ((sh, el), (el, wr)):
        ax = b - a
        L = float(np.linalg.norm(ax))
        ax = ax / L
        t = np.clip((P - a.astype(F)) @ ax.astype(F), F(0), F(L))
        c = a.astype(F) + t[:, None] * ax.astype(F)
        d = ((P - c) ** 2).sum(1)
        s = t + F(acc)
        if out_s is None:
            out_s, out_d = s, d
        else:
            use = d < out_d
            out_s = np.where(use, s, out_s)
            out_d = np.where(use, d, out_d)
        acc += L
    return out_s, out_d


def quilting(P):
    """Displacement: upright channels round his body, rings round his sleeves (the stitched seams sink in)."""
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    s = np.mod(a * F(30 / (2 * math.pi)), F(1.0))
    body = F(1.0) - np.sin(s * F(math.pi))
    sleeve = None
    w = np.zeros(len(P), F)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sa, d2 = _arm_coord(P, side)
        ring = F(1.0) - np.sin(np.mod(sa / F(0.034), F(1.0)) * F(math.pi))
        on = smoothstep(0.28, 0.36, P[:, 0] * F(sx))
        sleeve = ring if sleeve is None else np.where(P[:, 0] * F(sx) > 0, ring, sleeve)
        w = np.maximum(w, on)
    q = body * (F(1) - w) + sleeve * w
    return F(0.0055) * q ** 2 + F(0.0012) * NOISE(P * F(30))


def gambeson_hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(HEM_Z) + F(0.015) * np.cos(a * 2) + F(0.006) * NOISE(P * F(8))


def _cuff_cut(P):
    """> 0 past the sleeves' ends (just short of the wrists)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        along = (P - wr.astype(F)) @ ax.astype(F) + F(0.012)
        sx = -1 if side == "R" else 1
        out = np.maximum(out, np.where(P[:, 0] * F(sx) > F(0.4), along, F(-1.0)))
    return out


def gambeson_field():
    """Blue linen padded thick, quilted in upright channels round the body and in rings round the long sleeves, to
    mid-thigh; a standing collar under the coif's cape; the sleeves end in plain cuffs (label 5: a yellow edging)."""
    fd = Field("Gambeson")
    base = gambeson_base()
    def keep(P):
        x, z = P[:, 0], P[:, 2]
        neck = z - (F(1.5) - F(0.03) * np.exp(-(x / F(0.1)) ** 2) + F(0.3) * smoothstep(0.14, 0.22, np.abs(x)))
        return np.maximum(np.maximum(neck, _cuff_cut(P)), gambeson_hem(P) - z)
    fd.add(Inter(Shell(base, 0.028, 0.026, pad=0.1, disp=quilting, disp_amp=0.007), Func(keep, (-1, -1, 0.4), (1, 1, 1.7)), 0.005), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (gambeson_hem(P) + F(0.028)), (-1, -1, 0.4), (1, 1, 0.65)), 5)
    fd.paint(Func(lambda P: np.maximum(-_cuff_cut(P) - F(0.03), F(1.0) - P[:, 2] - F(0.4)), (-1, -1, 0.5), (1, 1, 1.2)), 5)
    return fd


# ======================================================================================= hose
def legs_base(side):
    b = Field("Leg")
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    b.add(RoundCone(hip, kn, 0.135, 0.088), 0.0)
    b.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.122, 0.115, 0.185), R=rot_from_axes(z_axis=kn - hip)), 0.048)
    b.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.068), 0.038)
    b.add(RoundCone(kn, an, 0.084, 0.056), 0.038)
    b.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.095, 0.092, 0.14), R=rot_from_axes(z_axis=an - kn)), 0.043)
    return b


def hose_field():
    """Tight wool hose: his right leg yellow (label 0), his left blue (6); a wrinkle at the knees and ankles."""
    fd = Field("Hose")
    wr = lambda P: F(0.0012) * NOISE(P * np.array([30, 30, 60], F))
    for side in ("R", "L"):
        lb = legs_base(side)
        kn = J["knee_" + side]
        fd.add(Inter(Shell(lb, 0.006, 0.008, pad=0.06, disp=wr, disp_amp=0.002),
                     Func(lambda P: np.maximum(F(0.26) - P[:, 2], P[:, 2] - F(0.64)), kn - v3((0.4, 0.4, 0.5)), kn + v3((0.4, 0.4, 0.4))),
                     0.004), 0.006)
    fd.paint(Func(lambda P: -P[:, 0], (0, -1, 0), (1, 1, 1)), 6)
    return fd


# ======================================================================================= leather: belt, gloves, boots, dagger
BELT_Z = 0.935
DAG_TOP = v3((0.31, 0.1, 1.04))            # the dagger's pommel (at his left hip, a little behind)
DAG_AX = norm(v3((0.08, 0.1, -1.0)))       # down along the blade, raked back


def belt_base():
    b = Field("BeltBase")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    b.add(RoundCone((0, 0.035, 0.92), (0, 0.035, 0.47), 0.24, 0.31), 0.08)
    return b


def _hand_hull(side):
    f = Field("HandHull")
    hand(f, side)
    f.add(Sphere(J["wrist_" + side], 0.045), 0.03)
    return f


def leather_field():
    """A broad belt (label 0) with a brass buckle (6); brown gloves with flared cuffs; mid-calf boots with turned-down
    cuffs and thick soles; the dagger's sheath (5: dark red) and its grip."""
    fd = Field("Leather")
    bb = belt_base()
    fd.add(Inter(Shell(bb, 0.058, 0.02, pad=0.1), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(0.03), (-1, -1, 0.8), (1, 1, 1.1)), 0.005), 0.0)
    p, ok = ray_hit(Func(lambda P: bb.eval(P, margin=0.1) - F(0.07), (-1, -1, 0.7), (1, 1, 1.2)), [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    c = p[0] if ok[0] else v3((0, -0.27, BELT_Z))
    fd.add(Torus(c + v3((0, -0.004, 0)), 0.032, 0.007, R=rot_from_axes(z_axis=(0, 1, 0))), 0.002, 6)
    fd.add(RoundCone(c + v3((0, -0.012, 0.026)), c + v3((0, -0.012, -0.026)), 0.0045, 0.0045), 0.002, 6)
    fd.add(RoundBox(c + v3((0.06, -0.006, 0)), (0.03, 0.006, 0.022), 0.004), 0.003)                     # the strap's end
    # gloves, their cuffs flaring over the sleeves' ends
    for side in ("R", "L"):
        hh = _hand_hull(side)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        fd.add(Shell(hh, 0.004, 0.006, pad=0.04), 0.0)
        fd.add(Inter(Shell(RoundCone(wr - ax * 0.09, wr + ax * 0.01, 0.075, 0.056), 0.004, 0.008, pad=0.04),
                     Func(lambda P, wr=wr, ax=ax: np.abs((P - (wr - ax * 0.04).astype(F)) @ ax.astype(F)) - F(0.05), wr - 0.2, wr + 0.2), 0.003), 0.004)
    # boots: to mid-calf, the tops turned down in a cuff, thick soles
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an, kn = J["ankle_" + side], J["knee_" + side]
        ft = Field("BootHull")
        foot(ft, side)
        ft.add(RoundCone(kn, an, 0.084, 0.056), 0.03)
        ft.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.095, 0.092, 0.14), R=rot_from_axes(z_axis=an - kn)), 0.043)
        crease = lambda P: F(0.0015) * NOISE(P * F(26))
        fd.add(Inter(Shell(ft, 0.012, 0.012, pad=0.06, disp=crease, disp_amp=0.002),
                     Func(lambda P: P[:, 2] - F(0.31), an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.3))), 0.004), 0.0)
        fd.add(Inter(Shell(ft, 0.026, 0.012, pad=0.06, disp=crease, disp_amp=0.002),
                     Func(lambda P: np.abs(P[:, 2] - F(0.295)) - F(0.028), an - v3((0.3, 0.4, 0.0)), an + v3((0.3, 0.3, 0.3))), 0.004), 0.005)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.07 + v3((0, 0, -0.098)), (0.075, 0.16, 0.014), 0.01, R=Rz), 0.006)
    # the dagger's sheath at his left hip (its grip and pommel above the belt)
    tip = DAG_TOP + DAG_AX * 0.4
    s0 = DAG_TOP + DAG_AX * 0.12
    side_n = norm(np.cross(DAG_AX, v3((0, 1, 0))))
    fd.add(Lock([s0, lerp(s0, tip, 0.5), tip], [0.026, 0.022, 0.008], [0.012, 0.011, 0.007], [side_n] * 3, k=0.004), 0.0, 5)
    fd.add(Torus(s0 + DAG_AX * 0.012, 0.02, 0.005, R=rot_from_axes(z_axis=DAG_AX)), 0.003, 6)
    fd.add(Sphere(tip, 0.009), 0.003, 6)
    fd.add(RoundCone(DAG_TOP + DAG_AX * 0.025, DAG_TOP + DAG_AX * 0.1, 0.012, 0.013), 0.004)                # the grip
    fd.add(Sphere(DAG_TOP + DAG_AX * 0.01, 0.019), 0.004, 6)                                               # a round pommel
    fd.add(RoundBox(DAG_TOP + DAG_AX * 0.106, (0.05, 0.009, 0.008), 0.004, R=rot_from_axes(z_axis=DAG_AX, x_axis=side_n)), 0.003, 6)
    return fd


# ======================================================================================= box quiver of bolts
Q_TOP = v3((-0.36, 0.07, 0.99))            # the mouth's middle (at his right hip, hanging on the belt's outside)
Q_BOT = v3((-0.39, 0.16, 0.62))
Q_W, Q_D = 0.062, 0.042                    # the mouth's half width (across) and half depth


def quiver_frame():
    ax = norm(Q_TOP - Q_BOT)
    out = norm(v3((-1, 0.0, 0.0)) - ax * (v3((-1, 0, 0)) @ ax))
    side = np.cross(ax, out)
    return ax, out, side


def quiver_field():
    """A box quiver: a tapering box of wood covered in brown hide (leather, label 9) with the hair on, an iron rim round
    its mouth (6); eight bolts stand in it, their vanes dyed yellow (5) and blue (7)."""
    fd = Field("Quiver")
    ax, out, side = quiver_frame()
    L = float(np.linalg.norm(Q_TOP - Q_BOT))
    hair = lambda P: F(0.0015) * NOISE(P * np.array([60, 60, 140], F))
    def box(P):
        q = P - Q_BOT.astype(F)
        u = q @ ax.astype(F)
        k = np.clip(u / F(L), 0, 1)
        w = F(0.045) + (F(Q_W) - F(0.045)) * k
        d = F(0.032) + (F(Q_D) - F(0.032)) * k
        qx = np.abs(q @ side.astype(F)) - w
        qy = np.abs(q @ out.astype(F)) - d
        qz = np.abs(u - F(L / 2)) - F(L / 2)
        qq = np.stack([qx, qy, qz], 1) + F(0.012)
        return np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0) - F(0.012)
    lo, hi = np.minimum(Q_TOP, Q_BOT) - 0.12, np.maximum(Q_TOP, Q_BOT) + 0.12
    fd.add(Func(box, lo, hi, disp=hair, disp_amp=0.002), 0.0, 9)
    def rim(P):
        q = P - Q_TOP.astype(F)
        u = q @ ax.astype(F)
        qx = np.abs(q @ side.astype(F)) - F(Q_W + 0.004)
        qy = np.abs(q @ out.astype(F)) - F(Q_D + 0.004)
        ring = np.maximum(np.maximum(qx, qy), -np.maximum(qx + F(0.01), qy + F(0.01)))
        return np.maximum(ring, np.abs(u + F(0.012)) - F(0.012))
    fd.add(Func(rim, Q_TOP - 0.12, Q_TOP + 0.12), 0.002, 6)
    # the bolts: eight shafts standing out of the mouth, two vanes each
    rs = np.random.RandomState(5)
    for i in range(8):
        cx = (-0.5 + (i % 4) / 3.0) * Q_W * 1.3
        cy = (-0.5 + (i // 4)) * Q_D * 1.0
        c0 = Q_TOP + side * cx + out * cy
        d = norm(ax + side * rs.uniform(-0.06, 0.06) + out * rs.uniform(-0.05, 0.05))
        c1 = c0 + d * rs.uniform(0.07, 0.1)
        fd.add(RoundCone(c0 - d * 0.04, c1, 0.0065, 0.006), 0.002)
        vn = norm(np.cross(d, out)) if i % 2 else norm(np.cross(d, side))
        lab = 5 if i % 2 else 7
        for sgn in (-1, 1):
            vc = c1 - d * 0.035 + vn * sgn * 0.012
            fd.add(RoundBox(vc, (0.0012, 0.012, 0.03), 0.001, R=rot_from_axes(z_axis=d, y_axis=vn * sgn)), 0.002, lab)
    return fd


# ======================================================================================= the crossbow
P_FWD = 0.38               # left fist -> the prod's middle (along the stock)
S_FWD = 0.43               # left fist -> the stock's front end
NUT_BACK = 0.04            # left fist -> the nut (just behind his left hand, which holds the stock from below)
GRIP_BACK = 0.2            # left fist -> the right hand's grip on the stock's wrist
BUTT_BACK = 0.45           # left fist -> the butt's end
PROD_HALF = 0.3
PROD_DRAW = 0.075          # the prod's tips bent back toward him (spanned)
STOCK_TOP = 0.03           # the stock's top face above its axis (the groove, the string's line)
BOLT_LEN = 0.44


def xbow_frame():
    """Rest pose: the left fist holds the fore-stock from below: the stock runs along the fist's thumb axis A (forward,
    toward the prod), its top U along the palm's normal, S = A x U (the stock's right side)."""
    wr, f, n, t = hand_frame("L")
    G = fist_center("L")
    A = norm(t)
    U = norm(n - A * (n @ A))
    S = np.cross(A, U)
    return G, A, U, S


def prod_point(s):
    """A point along the prod's middle line: s in [-1, 1] from its right tip to its left tip."""
    G, A, U, S = xbow_frame()
    c = G + A * P_FWD + U * (STOCK_TOP - 0.006)
    return c + S * (-s * PROD_HALF) - A * (PROD_DRAW * s * s) + A * 0.006 * (1 - s * s)


def prod_tips():
    return prod_point(-1.0), prod_point(1.0)                 # (right tip, left tip)


def nut_point():
    G, A, U, S = xbow_frame()
    return G - A * NUT_BACK + U * (STOCK_TOP + 0.004)


def braced_point():
    """Where the string's middle sits when it is loose (just after a shot)."""
    G, A, U, S = xbow_frame()
    return G + A * (P_FWD - PROD_DRAW - 0.02) + U * (STOCK_TOP + 0.004)


def grip_point():
    G, A, U, S = xbow_frame()
    return G - A * GRIP_BACK


def bolt_axis():
    """The bolt in the groove: its back end at the nut, along the stock."""
    G, A, U, S = xbow_frame()
    return nut_point() + A * 0.006 + U * 0.008, A


def _stock_dist(P):
    G, A, U, S = xbow_frame()
    q = P - G.astype(F)
    u = q @ A.astype(F)                                      # along: -BUTT_BACK (butt) .. S_FWD (front)
    s = q @ S.astype(F)
    h = q @ U.astype(F)
    butt = smoothstep(-(GRIP_BACK + 0.04), -(BUTT_BACK - 0.04), u)    # the butt deepens and widens toward its end
    wrist = np.exp(-((u + F(GRIP_BACK)) / F(0.06)) ** 2)      # slimmer where the right hand takes it
    half_w = F(0.022) + F(0.008) * butt - F(0.003) * wrist
    top = F(STOCK_TOP)
    bot = F(-0.03) - F(0.04) * butt + F(0.004) * wrist
    hc = (top + bot) / F(2)
    hh = (top - bot) / F(2)
    qx = np.abs(s) - half_w
    qy = np.abs(h - hc) - hh
    qz = np.abs(u - F((S_FWD - BUTT_BACK) / 2)) - F((S_FWD + BUTT_BACK) / 2)
    qq = np.stack([qx, qy, qz], 1) + F(0.008)
    d = np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0) - F(0.008)
    groove = np.maximum(np.maximum(np.abs(s) - F(0.0065), np.abs(h - top) - F(0.005)), np.maximum(F(-NUT_BACK) - u, u - F(S_FWD - 0.01)))
    return np.maximum(d, -groove)


def crossbow_field():
    """Walnut stock (label 0, the grain along it) with its butt painted blue (7) and a yellow band (5), a steel prod (6)
    lashed through the stock's front with cord bridles (8), an iron stirrup (6), a bone nut, an iron trigger lever (6)."""
    fd = Field("Crossbow")
    G, A, U, S = xbow_frame()
    lo = np.minimum.reduce([G - A * 0.7, G + A * 0.45]) - 0.4
    hi = np.maximum.reduce([G - A * 0.7, G + A * 0.45]) + 0.4
    grain = lambda P: F(0.0007) * NOISE(P * F(90))
    fd.add(Func(_stock_dist, lo, hi, disp=grain, disp_amp=0.001), 0.0)
    # the prod: a flat steel bow through the stock, tapering to its tips, with little hooks for the string
    ss = np.linspace(-1.0, 1.0, 25)
    pts = [prod_point(s) for s in ss]
    ws = [0.024 - 0.01 * abs(s) for s in ss]                 # (stout: it reads at a distance)
    ts = [0.011 - 0.004 * abs(s) for s in ss]
    fd.add(Lock(pts, ws, ts, [A] * len(pts), k=0.006), 0.004, 6)
    for s in (-1.0, 1.0):
        tp = prod_point(s)
        out = norm(prod_point(s) - prod_point(s * 0.92))
        fd.add(RoundCone(tp, tp + out * 0.014 - A * 0.006, 0.006, 0.0035), 0.003, 6)
    # bridles: cord lashed round the prod and the stock's front, both sides of the stock
    pc = G + A * P_FWD + U * (STOCK_TOP - 0.006)
    for sg in (-1, 1):
        c = pc + S * (sg * 0.042)
        for k in range(3):
            fd.add(Torus(c + S * (sg * 0.008 * k), 0.026, 0.0042, R=rot_from_axes(z_axis=S, y_axis=A)), 0.002, 8)
    # iron cheeks round the stock's front and the stirrup: a loop of iron bar ahead of the prod
    fd.add(Inter(Shell(Func(_stock_dist, lo, hi), 0.0, 0.006),
                 Func(lambda P: np.abs((P - G.astype(F)) @ A.astype(F) - F(S_FWD - 0.02)) - F(0.016), lo, hi), 0.002), 0.003, 6)
    st0 = G + A * (S_FWD - 0.01) + U * 0.0
    loop = [st0 + S * 0.024 - A * 0.035]
    for k in range(13):
        a = math.pi * k / 12
        loop.append(st0 + S * (math.cos(a) * 0.06) + A * (0.02 + math.sin(a) * 0.12) - U * (0.006 * math.sin(a)))
    loop.append(st0 - S * 0.024 - A * 0.035)
    fd.add(Chain(loop, [0.0075] * len(loop), k=0.003), 0.004, 6)
    # the nut: a bone cylinder set in the stock's top, its notch holding the string
    nc = G - A * NUT_BACK + U * (STOCK_TOP - 0.006)
    fd.add(Cylinder(nc, 0.018, 0.034, rr=0.004, R=rot_from_axes(z_axis=S, y_axis=U)), 0.003, 8)
    # the trigger lever: an iron bar pivoted under the stock behind the nut, running back under his fingers
    piv = G - A * (NUT_BACK + 0.03) + U * (-0.032)
    fd.add(Chain([piv, piv - A * 0.12 - U * 0.035, piv - A * 0.27 - U * 0.05], [0.0075, 0.0065, 0.0055], k=0.004), 0.003, 6)
    fd.add(Sphere(piv, 0.009), 0.003, 6)
    # paint: the butt blue with a yellow band where the paint ends
    def butt_paint(P):
        u = (P - G.astype(F)) @ A.astype(F)
        return u + F(BUTT_BACK - 0.2)
    def band(P):
        u = (P - G.astype(F)) @ A.astype(F)
        return np.abs(u + F(BUTT_BACK - 0.215)) - F(0.016)
    fd.paint(Func(butt_paint, lo, hi), 7)
    fd.paint(Func(band, lo, hi), 5)
    return fd


def string_field():
    fd = Field("String")
    t1, t2 = prod_tips()
    fd.add(Chain([t1, nut_point(), t2], [0.0052, 0.0052, 0.0052], k=0.002), 0.0)
    return fd


def bolt_field():
    """A crossbow bolt: a thick ash shaft (label 0), a square bodkin head of iron (6), two leather vanes (9) at the back."""
    fd = Field("Bolt")
    p0, ax = bolt_axis()
    G, A, U, S = xbow_frame()
    p1 = p0 + ax * (BOLT_LEN - 0.06)
    fd.add(RoundCone(p0 + ax * 0.004, p1, 0.0072, 0.0078), 0.0)
    h0, h1 = p1 - ax * 0.008, p1 + ax * 0.065
    def bodkin(P):
        q = P - h0.astype(F)
        u = q @ ax.astype(F)
        k = np.clip(u / F(0.073), 0, 1)
        half = F(0.011) * (F(1) - k) + F(0.0012)
        qa = np.abs(q @ U.astype(F))
        qb = np.abs(q @ S.astype(F))
        return np.maximum(np.maximum(qa, qb) * F(0.92) - half, np.maximum(-u, u - F(0.073)))
    fd.add(Func(bodkin, h0 - 0.1, h1 + 0.1), 0.003, 6)
    for sg in (-1, 1):
        vc = p0 + ax * 0.06 + S * (sg * 0.013) + U * 0.004
        fd.add(RoundBox(vc, (0.012, 0.0013, 0.045), 0.0012, R=rot_from_axes(z_axis=ax, x_axis=S * sg)), 0.002, 9)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0.008, -0.25, 1.612)), 0.05, 0.75)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.1, -0.15, 1.61)), 0.06, 0.55), (hp((sx * 0.12, -0.1, 1.57)), 0.05, 0.3)]
    return pts


# ======================================================================================= build config
GLB_NAME = "crossbowman"
ROOT_NAME = "CrossbowmanHQ"
TEX_PREFIX = "xbow"
MAT_NAME = "CrossbowMat"
MESH_NAME = "Crossbowman"
BASE_MODULE = "crossbowman_base"
ANIM_MODULE = "anim_crossbowman"
PARTS = ["Skin", "Eyes", "Teeth", "Beard", "Mail", "Steel", "Gambeson", "Hose", "Leather", "Quiver", "Crossbow", "String", "Bolt"]
REGION_PARTS = ("Skin", "Mail", "Gambeson", "Hose", "Leather", "Quiver", "Crossbow", "Bolt")
BROWN_HAIR = {"name": "HQ_XbowBeard", "base": (0.26, 0.16, 0.09), "hi": (0.5, 0.34, 0.2), "low": (0.12, 0.07, 0.04),
              "streak": (0.36, 0.24, 0.14), "tint": (0.42, 0.26, 0.14)}
BLUE = (0.14, 0.27, 0.62)
YELLOW = (0.88, 0.66, 0.16)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_XbowSkin", "base": (0.8, 0.56, 0.42), "ruddy": (0.86, 0.46, 0.36), "lips": (0.66, 0.38, 0.33),
                      "brow": ((0.2, 0.12, 0.07), (0.38, 0.24, 0.14)),
                      "extra": ((LASH, (0.12, 0.08, 0.05), 0.5), (RED_NOSE, (0.82, 0.42, 0.36), 0.45))}),
    "Beard": ("hair", BROWN_HAIR),
    "Mail": ("mail", {"name": "HQ_XbowMail", "base": (0.56, 0.57, 0.61)}),
    "Steel": ("roman_steel", {"name": "HQ_KettleHat"}),
    "Gambeson": ("wool", {"name": "HQ_Gambeson", "base": BLUE, "border": YELLOW, "stripe": (0.1, 0.12, 0.3)}),
    "Hose": ("wool", {"name": "HQ_Hose", "base": YELLOW, "border": YELLOW, "stripe": BLUE}),
    "Leather": ("leather_dyed", {"name": "HQ_XbowLeather", "base": (0.38, 0.22, 0.12), "dyed": (0.42, 0.1, 0.07)}),
    "Quiver": ("siege", {"name": "HQ_XbowQuiver", "wood": (0.56, 0.38, 0.22), "wood2": (0.42, 0.27, 0.15), "red": YELLOW,
                         "blue": BLUE, "metal": "iron"}),
    "Crossbow": ("siege", {"name": "HQ_Crossbow", "wood": (0.44, 0.27, 0.15), "wood2": (0.3, 0.18, 0.1), "red": YELLOW,
                           "blue": BLUE, "metal": "iron"}),
    "String": ("cord", {}),
    "Bolt": ("siege", {"name": "HQ_Crossbow", "wood": (0.44, 0.27, 0.15), "wood2": (0.3, 0.18, 0.1), "red": YELLOW,
                       "blue": BLUE, "metal": "iron"}),
}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Beard": 900, "Mail": 2400, "Steel": 1600, "Gambeson": 3600, "Hose": 900,
               "Leather": 2400, "Quiver": 900, "Crossbow": 1500, "String": 100, "Bolt": 260}
AO_EXCLUDE = ["Crossbow", "String", "Bolt"]


def prop_bones():
    p0, ax = bolt_axis()
    return [("bolt", p0, p0 + ax * 0.3, "hand.L")]


def extra_bones():
    t1, t2 = prod_tips()
    m = nut_point()
    return [("string_r", t1, m, "hand.L"), ("string_l", t2, m, "hand.L")]


def _vec(p):
    from mathutils import Vector
    return Vector((float(p[0]), float(p[1]), float(p[2])))


def mail_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed={"head", "neck", "chest", "clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"})
    groups = {}
    z_head = hp((0, 0, 1.6))[2]
    for v in ob.data.vertices:
        p = v.co
        if p.z > z_head:
            w = {"head": 1.0}
        elif p.z > 1.45 and abs(p.x) < 0.2:
            t = max(0.0, min(1.0, (z_head - p.z) / 0.15))
            w = {"head": 1.0 - 0.7 * t, "neck": 0.7 * t}
        else:
            continue
        for g in list(ob.vertex_groups):
            g.remove([v.index])
        _blend_add(ob, groups, v.index, w)


def leather_weights(ob, skin_ob, arm):
    """Belt and boots from the body; the gloves with the hands; the dagger rigid with the hips."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "thigh.R", "thigh.L",
                                                       "shin.R", "shin.L", "foot.R", "foot.L"})
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        q = np.array(p) - DAG_TOP
        along = float(q @ DAG_AX)
        off = np.linalg.norm(q - DAG_AX * along)
        if -0.03 < along < 0.42 and off < 0.06 and p.z > 0.55:
            w = {"root": 1.0}
        else:
            continue
        for g in list(ob.vertex_groups):
            g.remove([v.index])
        _blend_add(ob, groups, v.index, w)


def string_weights(ob, skin_ob, arm):
    G, A, U, S = xbow_frame()
    groups = {}
    for v in ob.data.vertices:
        right = float((np.array(v.co) - G) @ S) > 0
        _blend_add(ob, groups, v.index, {"string_r" if right else "string_l": 1.0})


def weight_rules():
    return {
        "Beard": ("rigid", "head"), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Steel": ("rigid", "head"),
        "Mail": ("custom", mail_weights),
        "Gambeson": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L",
                                          "thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Hose": ("transfer", {"root", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Leather": ("custom", leather_weights), "Quiver": ("rigid", "root"),
        "Crossbow": ("rigid", "hand.L"), "String": ("custom", string_weights), "Bolt": ("rigid", "bolt"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("String", "Bolt"):
        return 0.6
    if part == "Skin" and abs(c.x) > 0.6 and c.z < 1.0:
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Beard", beard_field(), 0.0022 if fine else 0.003),
        ("Mail", mail_field(), 0.0024 if fine else 0.0034),
        ("Steel", steel_field(), 0.0022 if fine else 0.003),
        ("Gambeson", gambeson_field(), 0.0026 if fine else 0.0036),
        ("Hose", hose_field(), 0.0024 if fine else 0.0034),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Quiver", quiver_field(), 0.002 if fine else 0.0028),
        ("Crossbow", crossbow_field(), 0.0018 if fine else 0.0024),
        ("String", string_field(), 0.0012 if fine else 0.0016),
        ("Bolt", bolt_field(), 0.0014 if fine else 0.0018),
    ]
