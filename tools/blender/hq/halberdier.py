"""The Halberdier (HQ tower, Gunpowder Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A big, barrel-chested Landsknecht, cheerful and fearless: a broad ruddy face, a big hooked nose, bright blue eyes under
bushy brows, an enormous upturned moustache and a short forked beard, a gap-toothed grin (his upper left front tooth is
gone). A steel morion: a tall comb along its crown, the brim sweeping up to points front and back, brass rivets round
it, a crimson-and-gold plume curling back from a brass holder. A polished steel peascod breastplate (a ridge down its
middle, a rolled neck, armholes and waist) and a gorget of lames over a crimson doublet with huge puffed-and-slashed
sleeves (crimson and gold panes, gold lining puffing out of the slashes, rolls down the forearms, gold cuffs); puffed
breeches paned and slashed the same way, gathered below the knee and gartered there with gold sashes tied in bows;
off-white hose, wide flat cow-mouth shoes (slashed over the toes, crimson showing). A leather belt with a brass buckle;
a katzbalger (a short sword with an S-shaped guard) slung across his left hip in a black scabbard with a brass chape.

The halberd, taller than he is: an ash shaft, a polished steel head (a broad axe blade with a curved edge, a hooked
back spike, a long four-sided top spike), iron langets riveted down the shaft, a crimson-and-gold tassel at the socket,
a steel butt cap. It rides its own bone (`halberd`, no parent: anim_halberdier.py poses it in world space and closes
his fists on the shaft every frame, so his hands can sit anywhere along it).

His body (barrel-chested), feet and face construction are the Bronze Age engineer's (torsion.py); both hands are fists."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import torsion as _t
from torsion import (J, SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD,
                     EYE_R, eye_c, smoothstep, hand_frame, HAND_S, foot, traps, neck_prim, deltoid, upper_arm,
                     torso_prims, TORSO, TORSO_Z, torso_bones, _forearm)

GOLD_L = 6            # gold panes, lining, stripes (wool / linen recipes: label 6 = the stripe colour)
TRIM_L = 5            # woven gold border (wool label 5)
BRASS_L = 6           # brass on steel (roman_steel label 6)


# ======================================================================================= hands (both fists)
CURLS = {"R": (1.45, 1.6, 1.2), "L": (1.45, 1.6, 1.2)}


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.064, 0.034, 0.066)) * s, 0.03 * s, R=Rp), 0.028, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.036, 0.03, 0.052)) * s, R=Rp), 0.019, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.044, 0.0148, -0.0148, -0.044)
    lens = (0.96, 1.02, 0.96, 0.8)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.022 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.011, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.016 * s), 0.009, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.012, (0.012, 0.007, 0.015), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.052 * s + n * 0.011
    d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
    d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.026 * s, 0.023 * s, 0.02 * s], k=0.008), 0.018, SKIN)


# ======================================================================================= head
def head(fd):
    """A broad ruddy face, the cheeks pushed up by a grin; a big hooked nose; bright eyes, wide open, smile lines at
    their corners; bushy brows arched high; an open grin, its corners up (the teeth are their own part); big ears."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.79), (0.165, 0.175, 0.12)), 0.08, SKIN)                           # the crown (under the morion)
    fd.add(E((0, -0.052, 1.59), (0.156, 0.138, 0.13)), 0.07, SKIN)                         # a broad heavy jaw
    fd.add(E((0, -0.134, 1.5), (0.092, 0.07, 0.068)), 0.05, SKIN)                           # chin (under the beard)
    for sx in (-1, 1):
        fd.add(S((sx * 0.108, -0.134, 1.634), 0.058), 0.05, SKIN)                            # round apple cheeks, up
        fd.add(S((sx * 0.132, -0.045, 1.556), 0.052), 0.05, SKIN)                            # jowls
        pts = [hp((sx * 0.156, -0.055, 1.744)), hp((sx * 0.118, -0.134, 1.756)), hp((sx * 0.062, -0.178, 1.754)), hp((0.0, -0.188, 1.75))]
        fd.add(Chain(pts, [hr(0.012), hr(0.021), hr(0.025), hr(0.023)], k=hr(0.022)), hr(0.032), SKIN)     # brow ridge
    # bushy brows arched high (a cheerful lift, no frown)
    tuft = lambda P: F(0.0024) * NOISE(P * F(150)) + F(0.0012) * np.sin(P[:, 0] * F(380))
    for sx in (-1, 1):
        pts = [hp((sx * 0.026, -0.216, 1.764)), hp((sx * 0.066, -0.211, 1.783)), hp((sx * 0.112, -0.19, 1.788)), hp((sx * 0.158, -0.148, 1.772))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.013), hr(0.017), hr(0.015), hr(0.007)], k=hr(0.008),
                     disp=tuft, disp_amp=0.003), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.021), hr(0.025), hr(0.022), hr(0.012)], k=hr(0.01)), BROW)
    # bright eyes, wide open; the lower lids pushed up a little by the cheeks (a smile)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.021))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.006)), Plane(ec + v3((0, 0, -hr(0.016))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.018))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for j, (dz, ang) in enumerate(((0.012, 0.3), (-0.002, 0.0), (-0.016, -0.3))):         # laughter lines
            a = hp((sx * 0.114, -0.128, 1.676 + dz))
            b = a + v3((sx * 0.028, 0.012, math.sin(ang) * 0.018))
            fd.sub(RoundCone(a, b, hr(0.0032), hr(0.0018)), hr(0.002))
    # a big hooked nose: a bump on the bridge, the tip drooping over the nostrils
    fd.add(RoundCone(hp((0, -0.186, 1.728)), hp((0, -0.258, 1.634)), hr(0.021), hr(0.029)), hr(0.018), SKIN)
    fd.add(S((0, -0.231, 1.69), 0.024), hr(0.012), SKIN)
    fd.add(E((0, -0.264, 1.612), (0.035, 0.04, 0.04)), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.037, -0.224, 1.602), 0.024), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.018, -0.242, 1.588)), v3((0.01, 0.012, 0.008)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # an open grin, its corners turned up (a dimple at each)
    slot = [hp((-0.078, -0.168, 1.557)), hp((-0.044, -0.197, 1.538)), hp((0, -0.208, 1.532)), hp((0.044, -0.197, 1.538)), hp((0.078, -0.168, 1.557))]
    fd.sub(Chain(slot, [hr(0.006), hr(0.013), hr(0.015), hr(0.013), hr(0.006)], k=hr(0.007)), hr(0.006))
    fd.paint(Chain(slot, [hr(0.008), hr(0.015), hr(0.017), hr(0.015), hr(0.008)], k=hr(0.007)), MOUTH)
    up_lip = [(-0.074, -0.167, 1.565), (-0.042, -0.198, 1.555), (0, -0.21, 1.553), (0.042, -0.198, 1.555), (0.074, -0.167, 1.565)]
    lo_lip = [(-0.07, -0.168, 1.538), (-0.038, -0.197, 1.52), (0, -0.207, 1.514), (0.038, -0.197, 1.52), (0.07, -0.168, 1.538)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.004), hr(0.006), hr(0.0065), hr(0.006), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.0085), hr(0.0095), hr(0.0085), hr(0.005)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(S((sx * 0.083, -0.161, 1.562), 0.009), hr(0.006), SKIN)
    # big ears (under the morion's brim)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.029, 0.052, 0.066)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.013, 0.033, 0.043)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))


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
        fd.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.097, 0.1, 0.13), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)
        fd.add(RoundCone(el, wr, 0.08, 0.058), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.1, 0.09, 0.135), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def leg_prims(side):
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(hip, kn, 0.14, 0.092), 0.065),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.13, 0.12, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.048),
            (Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038),
            (RoundCone(kn, an, 0.088, 0.058), 0.038),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043)]


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
    """His upper teeth in the grin: square front teeth, his upper left one gone (the gap), canines at the corners."""
    fd = Field("Teeth")
    for x, w, h in ((-0.046, 0.0075, 0.0085), (-0.029, 0.0082, 0.0105), (-0.0105, 0.0092, 0.012), (0.029, 0.0082, 0.0105),
                    (0.046, 0.0075, 0.0085)):
        y = -0.203 + 0.031 * (x / 0.078) ** 2
        rz = -math.atan2(2 * 0.031 * x / 0.078 ** 2, 1.0)
        fd.add(RoundBox(hp((x, y + 0.004, 1.5455 - h * 0.5)), v3((w, 0.006, h)) * HS, hr(0.003), R=euler(0.12, 0, rz)), 0.0)
    return fd


def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.052, 1.59), (0.156, 0.138, 0.13)), 0.07)
    fd.add(E((0, -0.134, 1.5), (0.092, 0.07, 0.068)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.108, -0.134, 1.634)), hr(0.058)), 0.05)
        fd.add(Sphere(hp((sx * 0.132, -0.045, 1.556)), hr(0.052)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


# ======================================================================================= beard, moustache, hair
def beard_tex(P):
    """Wavy locks running down the beard (positive pushes the surface in)."""
    x, z = P[:, 0], P[:, 2]
    ph = x / F(0.022) + F(0.35) * np.sin(z * F(40) + x * F(9))
    lock = np.abs(np.sin(ph * F(math.pi)))
    return F(0.0024) - F(0.0048) * lock * lock + F(0.0012) * NOISE(P * np.array([90, 90, 30], F))


def moustache_path(sx):
    """The moustache's middle line on one side (design coordinates): from under the nose out over the corner of the
    grin, sweeping out past the cheek and curling up at the tip."""
    return [(sx * 0.004, -0.224, 1.586), (sx * 0.04, -0.206, 1.575), (sx * 0.08, -0.193, 1.568), (sx * 0.12, -0.178, 1.572),
            (sx * 0.16, -0.154, 1.588), (sx * 0.198, -0.142, 1.612), (sx * 0.228, -0.136, 1.645), (sx * 0.244, -0.133, 1.684),
            (sx * 0.238, -0.135, 1.716)]


def beard_field():
    """An enormous upturned moustache (two thick locks from under his nose, out past his cheeks, curled up to points at
    the tips), a short beard on his chin that forks into two points under it, short dark hair at his nape and over his
    ears under the morion. His cheeks and jaw are bare (ruddy)."""
    fd = Field("Beard")
    hull = head_hull()
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        lips = (x / F(0.08)) ** 2 + ((y + F(0.19)) / F(0.06)) ** 2 + ((z - F(1.528)) / F(0.026)) ** 2 - F(1.0)
        side = np.abs(x) - (F(0.075) + F(0.035) * smoothstep(1.5, 1.44, z))
        return np.maximum(np.maximum(np.maximum(z - F(1.512), side), -lips * F(0.03)), np.maximum(F(1.43) - z, y + F(0.02)))
    fd.add(Inter(Shell(hull, 0.006, 0.018, pad=0.06, disp=beard_tex, disp_amp=0.006), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.008), 0.0)
    fd.add(Ellipsoid(hp((0, -0.168, 1.474)), v3((0.075, 0.048, 0.046)) * HS, disp=beard_tex, disp_amp=0.006), 0.03)   # fuller at the chin
    strands = lambda P: F(0.0022) * NOISE(P * np.array([80, 80, 30], F))
    # the fork: two short locks below the chin, parting to points
    for sx in (-1, 1):
        pts = [hp((sx * 0.014, -0.18, 1.468)), hp((sx * 0.03, -0.2, 1.44)), hp((sx * 0.048, -0.214, 1.414)), hp((sx * 0.066, -0.222, 1.392))]
        fd.add(Lock(pts, [hr(0.052), hr(0.046), hr(0.032), hr(0.009)], [hr(0.03), hr(0.028), hr(0.02), hr(0.007)],
                    [norm(v3((sx * 0.25, -1.0, -0.3)))] * 4, k=hr(0.01), disp=strands, disp_amp=0.003), hr(0.012))
    # the moustache
    for sx in (-1, 1):
        pts = [hp(p) for p in moustache_path(sx)]
        n = len(pts)
        ws = [hr(w) for w in (0.024, 0.031, 0.033, 0.031, 0.026, 0.02, 0.014, 0.009, 0.003)]
        ts = [hr(t) for t in (0.018, 0.021, 0.021, 0.019, 0.016, 0.013, 0.01, 0.007, 0.003)]
        ns = []
        for i in range(n):
            u = i / (n - 1)
            ns.append(norm(v3((sx * (0.12 + 0.8 * u), -1.0, 0.2 * u))))
        fd.add(Lock(pts, ws, ts, ns, k=hr(0.008), disp=strands, disp_amp=0.003), hr(0.006))
    # short hair at his nape and over his ears, under the morion's rim
    stub = lambda P: F(0.0025) * NOISE(P * np.array([70, 70, 26], F)) + F(0.0012) * NOISE(P * F(140))
    def band(P):
        Q = hinv(P)
        y, z = Q[:, 1], Q[:, 2]
        top = F(1.8)
        bot = F(1.738) - F(0.11) * smoothstep(0.06, 0.16, y)
        return np.maximum(np.maximum(z - top, bot - z), F(0.03) - y)
    fd.add(Inter(Shell(Ellipsoid(HEAD_C, HEAD_RAD), 0.006, 0.016, pad=0.06, disp=stub, disp_amp=0.004),
                 Func(band, HEAD_C - 0.4, HEAD_C + 0.4), 0.006), 0.0)
    return fd


# ======================================================================================= the morion
CROWN_C = v3((0.0, 0.03, 1.77))
CROWN_R = v3((0.222, 0.236, 0.245))
FOOT_Z = 1.786                     # where the brim leaves the crown
W_SIDE, W_FRONT, W_BACK = 0.046, 0.14, 0.16     # the brim's width at the sides and at its front and back points
S_TIP, S_SIDE = 1.0, 0.48          # its slope up toward the points, down at the sides
BRIM_T = 0.009
COMB_LY, COMB_LZ = 0.212, 0.375    # the comb: an ellipse through the crown's middle (its top 0.13 above the crown)
_FOOT_K = math.sqrt(max(0.0, 1.0 - ((FOOT_Z - CROWN_C[2]) / CROWN_R[2]) ** 2))


def _polar(P):
    x = P[:, 0]
    y = P[:, 1] - F(CROWN_C[1])
    return np.sqrt(x * x + y * y), np.arctan2(x, -y)


def _r0(phi):
    a, b = F(CROWN_R[0] * _FOOT_K), F(CROWN_R[1] * _FOOT_K)
    return F(1.0) / np.sqrt((np.sin(phi) / a) ** 2 + (np.cos(phi) / b) ** 2)


def brim_w(phi):
    c = np.cos(phi)
    tip = np.where(c > 0, F(W_FRONT), F(W_BACK))
    return F(W_SIDE) + (tip - F(W_SIDE)) * np.abs(c) ** F(9.0)


def brim_h(q, phi):
    """The brim's height q out from the crown's foot at angle phi (0 = front), and its slope there."""
    c2 = np.cos(phi) ** 2
    s = F(S_TIP) * c2 - F(S_SIDE) * (F(1) - c2)
    return F(FOOT_Z) + q * s + F(2.4) * q * q * c2, s + F(4.8) * q * c2


def _brim(P, t=BRIM_T, band=None):
    r, phi = _polar(P)
    q = r - _r0(phi)
    w = brim_w(phi)
    h, s = brim_h(np.clip(q, 0, None), phi)
    dz = (np.abs(P[:, 2] - h) - F(t / 2)) / np.sqrt(F(1) + s * s)
    if band is None:
        dr = np.maximum(F(-0.006) - q, q - w)
    else:
        dr = np.abs(q - (w - F(band))) - F(band)
    return np.maximum(dz, dr)


def brim_edge_pt(phi):
    """A point on the brim's outer edge at angle phi (for laying things along it)."""
    p = np.array([[0.0, 0.0, 0.0]], F)
    r0 = float(_r0(np.array([phi], F))[0])
    w = float(brim_w(np.array([phi], F))[0])
    h, s = brim_h(np.array([w], F), np.array([phi], F))
    return v3((math.sin(phi) * (r0 + w), CROWN_C[1] - math.cos(phi) * (r0 + w), float(h[0])))


def _comb_e(P):
    y = P[:, 1] - F(CROWN_C[1])
    z = P[:, 2] - F(CROWN_C[2])
    return (np.sqrt((y / F(COMB_LY)) ** 2 + (z / F(COMB_LZ)) ** 2) - F(1)) * F(min(COMB_LY, COMB_LZ)), z


def helmet_field():
    """Polished steel (label 0): the crown, the comb with a rolled edge, the brim sweeping up to points front and back
    with a rolled rim; brass (6): rivets round the crown's foot and the plume holder at the back."""
    fd = Field("Helmet")
    hammer = lambda P: F(0.0007) * NOISE(P * F(45))
    lo, hi = CROWN_C - v3((0.45, 0.5, 0.2)), CROWN_C + v3((0.45, 0.5, 0.36))
    fd.add(Inter(Shell(Ellipsoid(CROWN_C, CROWN_R), 0.004, 0.009, pad=0.06, disp=hammer, disp_amp=0.001),
                 Func(lambda P: F(FOOT_Z - 0.003) - P[:, 2], lo, hi), 0.003), 0.0)
    fd.add(Func(_brim, lo, hi, disp=hammer, disp_amp=0.001), 0.007)
    fd.add(Func(lambda P: _brim(P, t=0.018, band=0.0075), lo, hi), 0.004)                     # the rolled rim
    # the comb: a tall half-moon plate along the crown, a rolled bead round its edge
    def comb(P):
        e, z = _comb_e(P)
        return np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.0055), e), F(0.03) - z)
    def bead(P):
        e, z = _comb_e(P)
        return np.maximum(np.sqrt(e * e + P[:, 0] * P[:, 0]) - F(0.0085), F(0.06) - z)
    clo, chi = CROWN_C - v3((0.05, 0.3, 0.0)), CROWN_C + v3((0.05, 0.3, 0.36))
    fd.add(Func(comb, clo, chi, disp=hammer, disp_amp=0.001), 0.006)
    fd.add(Func(bead, clo, chi), 0.004)
    # brass rivets round the crown's foot
    hull = Ellipsoid(CROWN_C, CROWN_R + 0.008)
    for k in range(18):
        a = 2 * math.pi * (k + 0.5) / 18
        d = v3((math.sin(a), -math.cos(a), 0.0))
        o = v3((CROWN_C[0], CROWN_C[1], FOOT_Z + 0.016)) + d * 0.5
        h, ok = ray_hit(Func(lambda P: hull(P), CROWN_C - 0.5, CROWN_C + 0.5), [o], [-d], tmax=0.6)
        if ok[0]:
            fd.add(Sphere(h[0], 0.0085), 0.002, BRASS_L)
    # the plume holder: a brass tube on the back of the crown, left of the comb
    b0, b1 = plume_socket()
    fd.add(RoundCone(b0, b1, 0.016, 0.014), 0.004, BRASS_L)
    fd.add(Torus(b1, 0.016, 0.005, R=rot_from_axes(z_axis=b1 - b0)), 0.003, BRASS_L)
    return fd


def plume_socket():
    a = math.radians(152.0)                                     # round the crown from the front, toward his left
    d = v3((math.sin(a), -math.cos(a), 0.0))
    o = v3((CROWN_C[0], CROWN_C[1], FOOT_Z + 0.06)) + d * 0.5
    h, ok = ray_hit(Func(lambda P: Ellipsoid(CROWN_C, CROWN_R)(P), CROWN_C - 0.5, CROWN_C + 0.5), [o], [-d], tmax=0.6)
    b0 = h[0] if ok[0] else CROWN_C + d * 0.2
    up = norm(d * 0.35 + v3((0, 0, 1.0)))
    return b0 - up * 0.01, b0 + up * 0.075


def plume_field():
    """Six curled ostrich plumes from the holder: up, then back over the crown and down behind it, crimson (label 0) and
    gold (6) by turns, fanned a little."""
    fd = Field("Plume")
    b0, b1 = plume_socket()
    barbs = lambda P: F(0.0028) * NOISE(P * np.array([110, 110, 40], F)) + F(0.0016) * NOISE(P * F(190))
    fd.add(Sphere(b1 + norm(b1 - b0) * 0.012, 0.022, disp=barbs, disp_amp=0.003), 0.0)
    for k in range(6):
        s = (k - 2.5) / 2.5                                      # -1 .. 1 across the fan
        fan = math.radians(-20.0 + 30.0 * s)
        out = v3((math.sin(fan) * 0.55 + 0.3, math.cos(fan) * 0.25 + 0.15, 1.0))
        back = v3((0.18 + 0.4 * s, 1.0, 0.0))
        p0 = b1 + norm(out) * 0.01
        p1 = p0 + norm(out) * (0.11 + 0.025 * (1 - abs(s)))
        p2 = p1 + norm(norm(out) * 0.6 + norm(back)) * 0.12
        p3 = p2 + norm(norm(back) + v3((0, 0, -0.45))) * 0.12
        p4 = p3 + norm(norm(back) * 0.6 + v3((0, 0, -1.0))) * 0.09
        p5 = p4 + norm(norm(back) * -0.2 + v3((0, 0, -1.0)) + v3((0, -0.6, 0))) * 0.05      # the curl at the tip
        pts = [p0, p1, p2, p3, p4, p5]
        nrm = norm(np.cross(norm(back), v3((1, 0, 0)) * (1 if s >= 0 else -1) + v3((0, 0, 0.0)))) if abs(s) > 0.1 else v3((1, 0, 0))
        ns = [norm(v3((1.0, -0.2 * s, 0.3)))] * 6
        fd.add(Lock(pts, [0.026, 0.046, 0.056, 0.054, 0.04, 0.018], [0.014, 0.018, 0.02, 0.018, 0.014, 0.008], ns,
                    k=0.01, disp=barbs, disp_amp=0.004), 0.01, GOLD_L if k % 2 else 0)
    return fd


# ======================================================================================= breastplate, gorget
def breast_hull():
    """His torso without the pectorals, one smooth swell over the chest, and the peascod belly low in front."""
    b = Field("BreastHull")
    tp = torso_prims()
    for i in (0, 1, 4, 5):
        b.add(tp[i][0], tp[i][1])
    b.add(Ellipsoid((0, -0.07, 1.26), (0.29, 0.17, 0.2)), 0.06)
    b.add(Ellipsoid((0, -0.1, 1.03), (0.25, 0.2, 0.21)), 0.07)
    b.add(traps(), 0.06)
    return b


BP_OFF = 0.05
BP_BOT = 0.935


def bp_keep(P):
    """< 0 where the breastplate is: from its flared waist up to a U round his neck; armholes cut out at the sides
    (front and back plates meet below his armpits)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    top = z - (F(1.405) + F(0.06) * smoothstep(-0.02, 0.14, y) - F(0.07) * np.exp(-(x / F(0.11)) ** 2) * (y < F(0.0)))
    arm = F(1.0) - ((ax - F(0.43)) / F(0.24)) ** 2 - ((z - F(1.37)) / F(0.25)) ** 2
    return np.maximum(np.maximum(F(BP_BOT) - z, top), arm * F(0.1))


def steel_field():
    """Polished steel (label 0): the peascod breastplate and backplate with a ridge down the front and rolled edges, a
    flared lame at the waist; a gorget of lames round his neck, low in front under his chin; brass rivets (6)."""
    fd = Field("Steel")
    hammer = lambda P: F(0.0007) * NOISE(P * F(45))
    cb = breast_hull()
    lo, hi = v3((-0.7, -0.6, 0.85)), v3((0.7, 0.6, 1.62))
    ridge = lambda P: hammer(P) - F(0.007) * np.exp(-(P[:, 0] / F(0.022)) ** 2) * (P[:, 1] < F(-0.05)) * smoothstep(1.4, 1.3, P[:, 2])
    fd.add(Inter(Shell(cb, BP_OFF, 0.016, pad=0.12, disp=ridge, disp_amp=0.008), Func(bp_keep, lo, hi), 0.004), 0.0)
    # rolled edges round the neck, the armholes and the waist
    def edge(P):
        k = bp_keep(P)
        return np.maximum(np.abs(k + F(0.007)) - F(0.008), F(BP_BOT - 0.03) - P[:, 2])
    fd.add(Inter(Shell(cb, BP_OFF + 0.01, 0.014, pad=0.12), Func(edge, lo, hi), 0.003), 0.004)
    # the flared lame at the waist (the fauld)
    fd.add(Inter(Shell(cb, BP_OFF + 0.018, 0.014, pad=0.12, disp=hammer, disp_amp=0.001),
                 Func(lambda P: np.abs(P[:, 2] - F(BP_BOT - 0.012)) - F(0.03), lo, hi), 0.004), 0.006)
    # the gorget: lames lying round the foot of his neck over the shoulders' tops and the breastplate's neck edge, a low
    # collar round the neck itself (low in front, under his chin and beard), a rolled edge
    gb = Field("GorgetBase")
    gb.add(neck_prim(), 0.0)
    gb.add(traps(), 0.05)
    def g_keep(P):
        y, z = P[:, 1], P[:, 2]
        back = smoothstep(-0.12, 0.12, y)
        rad = np.sqrt(P[:, 0] ** 2 + ((y - F(0.05)) / F(1.1)) ** 2)
        bot = F(1.3) + F(0.1) * back
        top = F(1.365) + F(0.13) * back
        collar = np.minimum(F(0.165) + F(0.11) * (F(1) - back) - rad, z - top)          # the top cut round the neck only
        return np.maximum(np.maximum(bot - z, rad - F(0.252)), collar)
    def g_lames(P):
        rad = np.sqrt(P[:, 0] ** 2 + ((P[:, 1] - F(0.05)) / F(1.1)) ** 2)
        u = (rad + (F(1.5) - P[:, 2]) * F(0.6)) / F(0.034)
        return -F(0.0045) * (u - np.floor(u)) + F(0.0006) * NOISE(P * F(50))
    glo, ghi = (-0.45, -0.45, 1.2), (0.45, 0.5, 1.65)
    fd.add(Inter(Shell(gb, 0.078, 0.012, pad=0.1, disp=g_lames, disp_amp=0.005), Func(g_keep, glo, ghi), 0.004), 0.004)
    def g_edge(P):
        k = g_keep(P)
        return np.abs(k + F(0.006)) - F(0.007)
    fd.add(Inter(Shell(gb, 0.085, 0.014, pad=0.1), Func(g_edge, glo, ghi), 0.003), 0.004)
    # brass rivets: two at each shoulder where the plates meet the gorget, a row along the waist
    outer = Func(lambda P: cb.eval(P, margin=0.08) - F(BP_OFF + 0.01), lo, hi)
    for sx in (-1, 1):
        for zz in (1.06, 1.16):
            h, ok = ray_hit(outer, [v3((sx * 0.6, -0.02, zz))], [v3((-sx, 0, 0))], tmax=0.7)
            if ok[0]:
                fd.add(Sphere(h[0], 0.009), 0.002, BRASS_L)
    for k in range(9):
        a = math.radians(-60 + 15 * k)
        d = v3((math.sin(a), -math.cos(a), 0.0))
        h, ok = ray_hit(outer, [v3((0, 0.0, BP_BOT + 0.02)) + d * 0.6], [-d], tmax=0.7)
        if ok[0]:
            fd.add(Sphere(h[0], 0.0085), 0.002, BRASS_L)
    return fd


# ======================================================================================= the doublet (crimson and gold)
def arm_axis(side):
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    a = norm(el - sh)
    sx = -1 if side == "R" else 1
    e1 = norm(np.cross(a, v3((0, 1, 0))))
    if e1[0] * sx < 0:
        e1 = -e1
    e2 = np.cross(a, e1)
    return sh, el, a, e1, e2


def _ang(P, c, a, e1, e2):
    q = P - c.astype(F)
    return np.arctan2(q @ e2.astype(F), q @ e1.astype(F)), q @ a.astype(F)


PUFF_N = 8          # panes round a puff (crimson and gold by turns)


def sleeve_hull(side):
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    sx = -1 if side == "R" else 1
    h = Field("SleeveHull")
    h.add(deltoid(side), 0.0)
    h.add(upper_arm(side), 0.05)
    h.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.097, 0.1, 0.13), R=rot_from_axes(z_axis=el - sh)), 0.04)
    h.add(RoundCone(el, wr, 0.08, 0.058), 0.035)
    h.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.1, 0.09, 0.135), R=rot_from_axes(z_axis=wr - el)), 0.04)
    h.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028)
    return h


def puff_center(side):
    sh, el, a, e1, e2 = arm_axis(side)
    return lerp(sh, el, 0.44) + e1 * 0.022 + v3((0, 0, 0.012))


PUFF_R = (0.158, 0.205)          # across, along the arm


def _cuff_cut(P, side):
    """> 0 past the sleeve's end (short of his wrist), only round that forearm."""
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    q = P - wr.astype(F)
    along = q @ ax.astype(F) + F(0.035)
    off = np.sqrt(np.maximum((q * q).sum(1) - (q @ ax.astype(F)) ** 2, 0))
    return np.where(off < F(0.16), along, F(-1.0))


def doublet_field():
    """Crimson wool (label 0) with gold (6): the body under the breastplate (gold stripes down it), huge puffed upper
    sleeves of crimson and gold panes (the crimson ones slashed, gold lining puffing out of the slashes), fitted
    forearm sleeves striped gold with two crimson rolls round each, gold cuffs (5) short of the wrists."""
    fd = Field("Doublet")
    nap = lambda P: F(0.0012) * NOISE(P * F(30))
    cb = breast_hull()
    lo, hi = v3((-0.6, -0.5, 0.8)), v3((0.6, 0.5, 1.62))
    nk = v3((0, 0.06, 1.38))
    def body_keep(P):
        z = P[:, 2]
        rad = np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F(0.055)) ** 2)
        neck = np.minimum(F(0.112) - rad, z - F(1.37))                 # the collar opening round the neck only
        return np.maximum(F(0.86) - z, neck)
    fd.add(Inter(Shell(cb, 0.022, 0.02, pad=0.12, disp=nap, disp_amp=0.002), Func(body_keep, lo, hi), 0.005), 0.0)
    def body_stripes(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.04)))
        return np.abs(np.mod(a * F(10 / (2 * math.pi)), F(1.0)) - F(0.5)) - F(0.12)
    fd.paint(Func(body_stripes, lo, hi), GOLD_L)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, a, e1, e2 = arm_axis(side)
        wr = J["wrist_" + side]
        # the fitted sleeve under it all, shoulder to wrist
        hull = sleeve_hull(side)
        slo, shi = np.minimum(sh, wr) - 0.3, np.maximum(sh, wr) + 0.3
        fd.add(Inter(Shell(hull, 0.016, 0.02, pad=0.06, disp=nap, disp_amp=0.002), Func(lambda P, side=side: _cuff_cut(P, side), slo, shi), 0.004), 0.02)
        # the puff: a big paned balloon round the upper arm
        c = puff_center(side)
        Rp = np.stack([e1, e2, a], axis=1)
        def panes(P, c=c, a=a, e1=e1, e2=e2):
            th, u = _ang(P, c, a, e1, e2)
            k = np.clip(F(1) - (u / F(PUFF_R[1])) ** 2, 0, 1)
            return -F(0.013) * np.cos(th * F(PUFF_N)) * k + F(0.004) * (F(1) - k) + nap(P)
        fd.add(Ellipsoid(c, (PUFF_R[0], PUFF_R[0], PUFF_R[1]), R=Rp, disp=panes, disp_amp=0.015), 0.03)
        def gold_panes(P, c=c, a=a, e1=e1, e2=e2):
            th, u = _ang(P, c, a, e1, e2)
            return np.cos(th * F(PUFF_N / 2)) * F(0.02)
        fd.paint(Func(gold_panes, c - 0.3, c + 0.3), GOLD_L)
        # the slashes: a slit down the middle of each crimson pane, gold lining puffing out of it
        for j in range(PUFF_N // 2):
            th = j * (4 * math.pi / PUFF_N)                       # (the crimson panes: cos(4 th) > 0)
            d = e1 * math.cos(th) + e2 * math.sin(th)
            s0 = c + d * (PUFF_R[0] + 0.006) - a * 0.085
            s1 = c + d * (PUFF_R[0] + 0.006) + a * 0.085
            fd.sub(RoundCone(s0, s1, 0.011, 0.011), 0.004)
            fd.add(Ellipsoid(c + d * (PUFF_R[0] - 0.006), (0.012, 0.012, 0.075), R=rot_from_axes(z_axis=a, x_axis=d)), 0.003, GOLD_L)
        # two crimson rolls round the forearm, gold stripes down the fitted sleeve
        fa = norm(wr - el)
        f1 = norm(np.cross(fa, v3((0, 1, 0))))
        f2 = np.cross(fa, f1)
        for t in (0.3, 0.62):
            cc = lerp(el, wr, t)
            fd.add(Torus(cc, 0.088 - 0.016 * t, 0.026, R=rot_from_axes(z_axis=fa),
                         disp=lambda P, cc=cc, fa=fa, f1=f1, f2=f2: -F(0.004) * np.cos(_ang(P, cc, fa, f1, f2)[0] * F(10)), disp_amp=0.005), 0.012)
        def fa_stripes(P, el=el, fa=fa, f1=f1, f2=f2):
            th, u = _ang(P, el, fa, f1, f2)
            st = np.abs(np.mod(th * F(6 / (2 * math.pi)), F(1.0)) - F(0.5)) - F(0.1)
            return np.maximum(st, np.maximum(F(0.04) - u, u - F(0.3)))
        fd.paint(Func(fa_stripes, el - 0.3, el + 0.4), GOLD_L)
        def cuff(P, side=side):
            s = _cuff_cut(P, side)
            return np.where(s > F(-0.5), np.abs(s + F(0.017)) - F(0.017), F(1.0))
        fd.paint(Func(cuff, wr - 0.3, wr + 0.3), TRIM_L)
    return fd


# ======================================================================================= breeches, hose, garters
KNEE_END = 0.355                 # the breeches end (gathered) just below his knees


def leg_axis(side):
    hip, kn = J["hip_" + side], J["knee_" + side]
    a = norm(kn - hip)
    sx = -1 if side == "R" else 1
    e1 = norm(np.cross(a, v3((0, 1, 0))))
    if e1[0] * sx < 0:
        e1 = -e1
    e2 = np.cross(a, e1)
    return hip, kn, a, e1, e2


LEG_PUFF = (0.19, 0.245)


def leg_puff_center(side):
    hip, kn, a, e1, e2 = leg_axis(side)
    return lerp(hip, kn, 0.45) + e1 * 0.018 + v3((0, -0.006, 0))


SEAT_C = v3((0.0, 0.05, 0.86))
SEAT_R = v3((0.31, 0.25, 0.175))


def breeches_field():
    """Puffed breeches of crimson (label 0) and gold (6) panes from his waist to below his knees, the crimson panes
    slashed (gold lining puffing out), gathered tight at the knee."""
    fd = Field("Breeches")
    nap = lambda P: F(0.0012) * NOISE(P * F(30))
    def seat_panes(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.05)))
        k = smoothstep(0.7, 0.88, P[:, 2])
        return -F(0.008) * np.cos(a * F(14)) * k + nap(P)
    fd.add(Ellipsoid(SEAT_C, SEAT_R, disp=seat_panes, disp_amp=0.01), 0.0)
    fd.add(RoundCone((0, 0.04, 0.86), (0, 0.04, 0.97), 0.28, 0.255), 0.05)                     # up to the waist
    for side in ("R", "L"):
        hip, kn, a, e1, e2 = leg_axis(side)
        c = leg_puff_center(side)
        Rp = np.stack([e1, e2, a], axis=1)
        def panes(P, c=c, a=a, e1=e1, e2=e2):
            th, u = _ang(P, c, a, e1, e2)
            k = np.clip(F(1) - (u / F(LEG_PUFF[1])) ** 2, 0, 1)
            return -F(0.014) * np.cos(th * F(PUFF_N)) * k + nap(P)
        fd.add(Ellipsoid(c, (LEG_PUFF[0], LEG_PUFF[0], LEG_PUFF[1]), R=Rp, disp=panes, disp_amp=0.016), 0.05)
        # gathered at the knee: snug round the knee and the top of the shin down to its end
        sh_ = shin_hull(side)
        an = J["ankle_" + side]
        fd.add(Inter(Func(lambda P, sh_=sh_: sh_.eval(P, margin=0.04) - F(0.03), kn - v3((0.25, 0.25, 0.2)), kn + v3((0.25, 0.25, 0.2))),
                     Func(lambda P: np.maximum(F(KNEE_END - 0.01) - P[:, 2], P[:, 2] - F(0.56)), kn - v3((0.25, 0.25, 0.2)), kn + v3((0.25, 0.25, 0.2))),
                     0.01, ), 0.05)
        def gold_panes(P, c=c, a=a, e1=e1, e2=e2):
            th, u = _ang(P, c, a, e1, e2)
            return np.cos(th * F(PUFF_N / 2)) * F(0.02)
        fd.paint(Func(gold_panes, c - 0.35, c + 0.35), GOLD_L)
        for j in range(PUFF_N // 2):
            th = j * (4 * math.pi / PUFF_N)
            d = e1 * math.cos(th) + e2 * math.sin(th)
            s0 = c + d * (LEG_PUFF[0] + 0.006) - a * 0.1
            s1 = c + d * (LEG_PUFF[0] + 0.006) + a * 0.1
            fd.sub(RoundCone(s0, s1, 0.012, 0.012), 0.004)
            fd.add(Ellipsoid(c + d * (LEG_PUFF[0] - 0.006), (0.013, 0.013, 0.09), R=rot_from_axes(z_axis=a, x_axis=d)), 0.003, GOLD_L)
    # cut off below the knee, round each shin only
    for side in ("R", "L"):
        an = J["ankle_" + side]
        fd.sub(Func(lambda P, an=an: np.maximum(P[:, 2] - F(KNEE_END), np.sqrt((P[:, 0] - F(an[0])) ** 2 + (P[:, 1] - F(an[1])) ** 2) - F(0.2)),
                    an - v3((0.3, 0.3, 0.3)), an + v3((0.3, 0.3, 0.3)) + v3((0, 0, KNEE_END))), 0.004)
    fd.inter(Plane((0, 0, 0.99), (0, 0, 1)), 0.01)                # (its top hidden under the breastplate)
    return fd


def breeches_hull():
    """The breeches' waist (without the panes): the belt lies on it."""
    b = Field("BreechesHull")
    b.add(Ellipsoid(SEAT_C, SEAT_R), 0.0)
    b.add(RoundCone((0, 0.04, 0.86), (0, 0.04, 0.97), 0.28, 0.255), 0.05)
    return b


def shin_hull(side):
    kn, an = J["knee_" + side], J["ankle_" + side]
    h = Field("ShinHull")
    h.add(RoundCone(kn, an, 0.088, 0.058), 0.0)
    h.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043)
    h.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038)
    return h


def hose_field():
    """Off-white linen hose from under the breeches into the shoes (label 0)."""
    fd = Field("Hose")
    wr = lambda P: F(0.0012) * NOISE(P * np.array([30, 30, 60], F))
    for side in ("R", "L"):
        kn, an = J["knee_" + side], J["ankle_" + side]
        h = shin_hull(side)
        foot(h, side)
        fd.add(Inter(Shell(h, 0.007, 0.009, pad=0.06, disp=wr, disp_amp=0.002),
                     Func(lambda P: np.maximum(F(0.035) - P[:, 2], P[:, 2] - F(KNEE_END + 0.06)), an - v3((0.3, 0.4, 0.3)), kn + v3((0.3, 0.3, 0.3))),
                     0.004), 0.006)
    return fd


GARTER_Z = KNEE_END - 0.012


def sash_field():
    """Gold sashes (wool, label 0) tied round each leg below the knee, a big bow on the outside of each leg, its ends
    hanging."""
    fd = Field("Sash")
    cl = lambda P: F(0.0015) * NOISE(P * F(40))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        kn, an = J["knee_" + side], J["ankle_" + side]
        c = lerp(kn, an, (kn[2] - GARTER_Z) / (kn[2] - an[2]))
        h = shin_hull(side)
        fd.add(Inter(Shell(h, 0.034, 0.03, pad=0.06, disp=cl, disp_amp=0.002),
                     Func(lambda P: np.abs(P[:, 2] - F(GARTER_Z)) - F(0.019), c - 0.25, c + 0.25), 0.008), 0.0)
        # the bow: a knot on the outside of the leg, a loop out to the front and one to the back, two ends hanging
        out = norm(v3((sx * 1.0, -0.15, 0.0)))
        hk, ok = ray_hit(Func(lambda P, h=h: h.eval(P, margin=0.06) - F(0.05), c - 0.3, c + 0.3), [c + out * 0.3], [-out], tmax=0.35)
        kc = hk[0] if ok[0] else c + out * 0.12
        fd.add(Ellipsoid(kc, (0.028, 0.026, 0.031), disp=cl, disp_amp=0.002), 0.006)
        for fb in (-1, 1):
            lc = kc + v3((0, fb * 0.054, 0.018)) + out * 0.006
            fd.add(Torus(lc, 0.037, 0.0135, R=rot_from_axes(z_axis=out, x_axis=v3((0, fb, 0.5))), disp=cl, disp_amp=0.002), 0.008)
        for fb in (-1, 1):
            pts = [kc + v3((0, fb * 0.012, -0.012)), kc + out * 0.01 + v3((0, fb * 0.032, -0.07)), kc + out * 0.014 + v3((0, fb * 0.046, -0.13))]
            fd.add(Lock(pts, [0.02, 0.023, 0.026], [0.007, 0.007, 0.007], [out] * 3, k=0.005, disp=cl, disp_amp=0.002), 0.006)
    return fd


# ======================================================================================= shoes, leather, katzbalger
def shoe_frame(side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.12)
    return an, Rz, Rz @ v3((0, -1, 0)), Rz @ v3((1, 0, 0))


def shoe_hull(side):
    an, Rz, fwd, rgt = shoe_frame(side)
    f = Field("ShoeHull")
    f.add(Sphere(an + v3((0, 0.042, -0.05)), 0.07), 0.0)
    f.add(RoundBox(an + fwd * 0.07 + v3((0, 0, -0.072)), (0.074, 0.11, 0.036), 0.034, R=Rz), 0.04)
    f.add(RoundBox(an + fwd * 0.17 + v3((0, 0, -0.074)), (0.094, 0.062, 0.035), 0.03, R=Rz), 0.04)   # the broad flat toe
    return f


def shoes_field():
    """Cow-mouth shoes of dark leather (label 0): a broad flat square toe, low sides, a strap over the instep; three
    slashes over the toes show crimson (5); a thin sole."""
    fd = Field("Shoes")
    for side in ("R", "L"):
        an, Rz, fwd, rgt = shoe_frame(side)
        sh = shoe_hull(side)
        top = an[2] - 0.035
        crease = lambda P: F(0.0012) * NOISE(P * F(26))
        def keep(P, an=an, fwd=fwd):
            q = P - an.astype(F)
            front = q @ fwd.astype(F)
            z = P[:, 2] - F(an[2])
            # low sides: cut down to the instep behind the toe box
            return z - (F(-0.035) - F(0.012) * smoothstep(0.08, 0.0, front) + F(0.03) * smoothstep(0.05, 0.13, front))
        fd.add(Inter(Shell(sh, 0.0, 0.016, pad=0.06, disp=crease, disp_amp=0.002), Func(keep, an - 0.35, an + 0.35), 0.005), 0.0)
        fd.add(RoundBox(an + fwd * 0.09 + v3((0, 0, -0.103)), (0.1, 0.17, 0.008), 0.007, R=Rz), 0.006)            # sole
        # the strap over the instep
        sc = an + fwd * 0.05 + v3((0, 0, -0.01))
        fd.add(Inter(Shell(sh, 0.008, 0.01, pad=0.06), Func(lambda P, sc=sc, fwd=fwd: np.abs((P - sc.astype(F)) @ fwd.astype(F)) - F(0.016),
                                                          an - 0.3, an + 0.3), 0.003), 0.004)
        # slashes across the toe box (crimson lining)
        for j, o in enumerate((-0.04, 0.0, 0.04)):
            c = an + fwd * 0.19 + rgt * o + v3((0, 0, -0.05))
            h, ok = ray_hit(Func(lambda P, sh=sh: sh.eval(P, margin=0.05) - F(0.008), an - 0.4, an + 0.4), [c + v3((0, 0, 0.2))], [v3((0, 0, -1))], tmax=0.4)
            if ok[0]:
                p = h[0]
                fd.sub(RoundCone(p - fwd * 0.035, p + fwd * 0.035, 0.007, 0.007), 0.003)
                fd.add(Ellipsoid(p - v3((0, 0, 0.006)), (0.007, 0.03, 0.006), R=Rz), 0.002, 5)
    return fd


BELT_Z = 0.865


def belt_base():
    return breeches_hull()


# the katzbalger: slung across his left hip, the hilt forward
KZ_G = v3((0.27, -0.27, 0.875))          # the guard's middle
KZ_D = norm(v3((0.42, 1.0, -0.2)))       # down the blade (toward the scabbard's tip)
KZ_BLADE = 0.5
KZ_GRIP = 0.095


def kz_frame():
    D = KZ_D
    U = norm(v3((0, 0, 1)) - D * float(D @ v3((0, 0, 1))))      # the edges up and down
    S = np.cross(D, U)                                          # the flats
    return D, U, S


def leather_field():
    """The belt (brown leather, label 0) with a brass buckle (6), the katzbalger's scabbard (black, 5) hanging from it
    by two straps, a brass chape at its tip (6)."""
    fd = Field("Leather")
    bb = belt_base()
    fd.add(Inter(Shell(bb, 0.02, 0.018, pad=0.1), Func(lambda P: np.abs(P[:, 2] - (F(BELT_Z) - F(0.015) * P[:, 1])) - F(0.028),
                                                      (-1, -1, 0.7), (1, 1, 1.1)), 0.004), 0.0)
    p, ok = ray_hit(Func(lambda P: bb.eval(P, margin=0.1) - F(0.04), (-1, -1, 0.7), (1, 1, 1.2)), [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    c = p[0] if ok[0] else v3((0, -0.3, BELT_Z))
    fd.add(RoundBox(c + v3((0, -0.006, 0)), (0.044, 0.008, 0.038), 0.007), 0.003, BRASS_L)
    fd.sub(RoundBox(c + v3((0, -0.016, 0)), (0.028, 0.008, 0.022), 0.004), 0.002)
    fd.add(RoundCone(c + v3((-0.012, -0.014, 0.02)), c + v3((-0.012, -0.014, -0.02)), 0.0045, 0.0045), 0.002, BRASS_L)
    # the scabbard
    D, U, S = kz_frame()
    s0 = KZ_G + D * 0.012
    tip = KZ_G + D * KZ_BLADE
    fd.add(Lock([s0, lerp(s0, tip, 0.5), tip], [0.032, 0.03, 0.016], [0.013, 0.012, 0.009], [S] * 3, k=0.004), 0.0, 5)
    fd.add(Lock([tip - D * 0.07, tip + D * 0.015], [0.022, 0.012], [0.012, 0.009], [S] * 2, k=0.004), 0.003, BRASS_L)
    fd.add(Torus(s0 + D * 0.01, 0.026, 0.005, R=rot_from_axes(z_axis=D)), 0.002, BRASS_L)
    for t in (0.12, 0.3):                                       # two straps up to the belt
        a = KZ_G + D * t
        b = v3((a[0] * 0.92, a[1] * 0.85, BELT_Z - 0.01))
        fd.add(RoundCone(a + U * 0.02, b, 0.011, 0.011), 0.004)
    return fd


def katz_field():
    """The katzbalger's hilt: an S-shaped guard (its quillons curled back in a figure of eight), a short grip bound in
    crimson leather (5), a broad flat pommel; steel (0), a brass ring at the grip (6)."""
    fd = Field("Katz")
    D, U, S = kz_frame()
    g = KZ_G
    # the S-guard in the blade's plane: one quillon curls up and round toward the grip, the other down and round toward
    # the blade (a figure of eight)
    for sg in (-1, 1):
        c = g + U * (sg * 0.03)
        Dp = -D * sg
        pts = []
        for k in range(13):
            th = math.pi - (math.pi + 1.05) * k / 12.0
            pts.append(c + (U * (sg * math.cos(th)) + Dp * math.sin(th)) * 0.03)
        fd.add(Chain(pts, [0.0072 - 0.0018 * (k / 12.0) for k in range(13)], k=0.004), 0.003)
        fd.add(Sphere(pts[-1], 0.0085), 0.003)
    fd.add(RoundBox(g, (0.012, 0.016, 0.026), 0.005, R=rot_from_axes(z_axis=U, y_axis=S)), 0.004)
    gp0, gp1 = g - D * 0.006, g - D * KZ_GRIP
    fd.add(RoundCone(gp0, gp1, 0.015, 0.017, disp=lambda P: F(0.0012) * np.abs(np.sin(((P - g.astype(F)) @ D.astype(F)) * F(170))), disp_amp=0.002), 0.004, 5)
    fd.add(Torus(gp0 - D * 0.008, 0.016, 0.004, R=rot_from_axes(z_axis=D)), 0.002, BRASS_L)
    pc = g - D * (KZ_GRIP + 0.018)
    fd.add(Ellipsoid(pc, (0.03, 0.012, 0.022), R=rot_from_axes(z_axis=-D, y_axis=S)), 0.006)       # the flat pommel
    return fd


# ======================================================================================= the halberd
HB_LEN = 2.32            # the butt -> the top spike's point
SHAFT_R = 0.0205
SOCKET_S = 1.75          # the steel socket begins
HEAD_S = 1.96            # the axe blade's middle (along the shaft)
LANGET_S = 1.38          # the langets run down to here
TASSEL_S = 1.715
BLADE_W = 0.205          # the shaft's axis -> the edge (at its middle)
O_REST = v3((-0.98, 0.1, 0.0))            # rest pose: standing upright on his right, the blade turned out to his right
A_REST = v3((0.0, 0.0, 1.0))
B_REST = v3((-1.0, 0.0, 0.0))


def hb_frame(O=O_REST, A=A_REST, B=B_REST):
    A = norm(A)
    B = norm(B - A * float(B @ A))
    W = np.cross(A, B)
    return v3(O), A, B, W


def hb_point(s, b=0.0, w=0.0, frame=None):
    O, A, B, W = frame or hb_frame()
    return O + A * s + B * b + W * w


def blade_center():
    """The axe blade's middle (rest pose): game.gd's cleave sits here at the blow."""
    return hb_point(HEAD_S - 0.01, 0.11)


def halberd_field():
    """The steel (label 0): the socket and its collar, the axe blade (a broad blade, its edge curved out, the lower
    horn sweeping down), the hooked back spike, the long four-sided top spike, the langets riveted down the shaft
    (rivets brass, 6), the butt cap."""
    fd = Field("Halberd")
    O, A, B, W = hb_frame()
    hammer = lambda P: F(0.0006) * NOISE(P * F(50))
    sock0, sock1 = hb_point(SOCKET_S), hb_point(HEAD_S + 0.09)
    fd.add(RoundCone(sock0, sock1, SHAFT_R + 0.008, SHAFT_R + 0.006), 0.0)
    fd.add(Torus(sock0 + A * 0.006, SHAFT_R + 0.009, 0.0055, R=rot_from_axes(z_axis=A)), 0.003)
    fd.add(Torus(hb_point(HEAD_S - 0.11), SHAFT_R + 0.008, 0.005, R=rot_from_axes(z_axis=A)), 0.003)
    hc = hb_point(HEAD_S)
    Af, Bf, Wf, hcf = A.astype(F), B.astype(F), W.astype(F), hc.astype(F)
    def blade(P):
        q = P - hcf
        u = q @ Bf
        v = q @ Af
        w = q @ Wf
        k = np.clip(u / F(BLADE_W), 0, 1)
        top = F(0.085) + F(0.055) * k ** 2                                  # the upper horn rising to a point
        bot = F(-0.075) - F(0.12) * k ** 1.5                                # the lower horn sweeping down
        edge = F(BLADE_W) - F(0.04) + F(0.045) * np.cos(np.clip((v + F(0.01)) / F(0.17), -1.5, 1.5))
        d2 = np.maximum(np.maximum(v - top, bot - v), np.maximum(u - edge, F(0.008) - u))
        thick = F(0.0075) * (F(1.0) - F(0.72) * k) + F(0.0012)
        return np.maximum(d2 * F(0.9), np.abs(w) - thick)
    blo, bhi = hc - 0.35, hc + 0.35
    fd.add(Func(blade, blo, bhi, disp=hammer, disp_amp=0.001), 0.006)
    # the hooked back spike (the fluke)
    pts = [hb_point(HEAD_S + 0.02, -0.02), hb_point(HEAD_S + 0.025, -0.07), hb_point(HEAD_S + 0.01, -0.12),
           hb_point(HEAD_S - 0.03, -0.16), hb_point(HEAD_S - 0.075, -0.18)]
    fd.add(Lock(pts, [0.034, 0.026, 0.018, 0.01, 0.002], [0.011, 0.01, 0.009, 0.006, 0.002], [W] * 5, k=0.006), 0.006)
    # the top spike: four-sided, long, tapering to a point
    t0 = HEAD_S + 0.07
    L = HB_LEN - t0
    sp0 = hb_point(t0)
    def spike(P):
        q = P - sp0.astype(F)
        v = q @ Af
        kk = np.clip(v / F(L), 0, 1)
        hb_, hw_ = F(0.024) * (F(1) - kk) + F(0.0015), F(0.014) * (F(1) - kk) + F(0.0015)
        d = (np.abs(q @ Bf) / hb_ + np.abs(q @ Wf) / hw_ - F(1)) * hw_
        return np.maximum(d, np.maximum(-v, v - F(L)))
    fd.add(Func(spike, sp0 - 0.45, sp0 + 0.45), 0.008)
    # langets: iron straps down the shaft on both flats, riveted
    for sg in (-1, 1):
        def langet(P, sg=sg):
            q = P - O.astype(F)
            v = q @ Af
            w = q @ Wf
            b = q @ Bf
            return np.maximum(np.maximum(np.abs(w - F(sg * (SHAFT_R + 0.002))) - F(0.0035), np.abs(b) - F(0.011)),
                              np.maximum(F(LANGET_S) - v, v - F(SOCKET_S + 0.02)))
        fd.add(Func(langet, hb_point(LANGET_S) - 0.1, hb_point(SOCKET_S) + 0.1), 0.003)
        for s in (LANGET_S + 0.03, LANGET_S + 0.17, LANGET_S + 0.31):
            fd.add(Sphere(hb_point(s, 0.0, sg * (SHAFT_R + 0.006)), 0.0055), 0.0015, BRASS_L)
    # the butt cap
    fd.add(RoundCone(hb_point(0.004), hb_point(0.07), SHAFT_R + 0.004, SHAFT_R + 0.003), 0.0)
    fd.add(Torus(hb_point(0.07), SHAFT_R + 0.004, 0.0035, R=rot_from_axes(z_axis=A)), 0.002)
    return fd


def haft_field():
    """The ash shaft (label 0), a little thicker toward the head."""
    fd = Field("Haft")
    grain = lambda P: F(0.0014) * NOISE(P * F(70))
    fd.add(RoundCone(hb_point(0.03), hb_point(SOCKET_S + 0.04), SHAFT_R, SHAFT_R * 1.06, disp=grain, disp_amp=0.0015), 0.0)
    return fd


def tassel_field():
    """A crimson tassel (label 0) at the socket: a round knot bound with gold (6) and a skirt of cords hanging round the
    shaft below it, gold cords among the crimson."""
    fd = Field("Tassel")
    O, A, B, W = hb_frame()
    Af, Bf, Wf = A.astype(F), B.astype(F), W.astype(F)
    kc = hb_point(TASSEL_S)
    fd.add(Ellipsoid(kc, (0.04, 0.04, 0.03), R=rot_from_axes(z_axis=A)), 0.0)
    sk0, sk1 = hb_point(TASSEL_S - 0.012), hb_point(TASSEL_S - 0.15)
    def cords(P):
        q = P - kc.astype(F)
        th = np.arctan2(q @ Wf, q @ Bf)
        return F(0.004) * np.abs(np.sin(th * F(12))) + F(0.001) * NOISE(P * F(90))
    fd.add(RoundCone(sk0, sk1, 0.034, 0.05, disp=cords, disp_amp=0.005), 0.012)
    fd.paint(Func(lambda P: np.abs((P - kc.astype(F)) @ Af) - F(0.008), kc - 0.1, kc + 0.1), GOLD_L)
    def gold_cords(P):
        q = P - kc.astype(F)
        th = np.arctan2(q @ Wf, q @ Bf)
        v = q @ Af
        return np.maximum(np.cos(th * F(6)) * F(0.02) + F(0.004), np.maximum(v + F(0.03), F(-0.2) - v))
    fd.paint(Func(gold_cords, kc - 0.25, kc + 0.1), GOLD_L)
    return fd


# ======================================================================================= painting
def warm_points():
    """Ruddy: the nose, the apple cheeks, the ears, the knuckles."""
    pts = [(hp((0, -0.258, 1.616)), 0.06, 0.75), (hp((0, -0.23, 1.68)), 0.04, 0.35)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.11, -0.15, 1.632)), 0.07, 0.7), (hp((sx * 0.18, 0.035, 1.664)), 0.05, 0.55),
                (hp((sx * 0.13, -0.1, 1.58)), 0.05, 0.35)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.044, 0.0148, -0.0148, -0.044):
            pts.append((wr + f * 0.138 * HAND_S + t * o - n * 0.012, 0.03, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "halberdier"
ROOT_NAME = "HalberdierHQ"
TEX_PREFIX = "halberd"
MAT_NAME = "HalberdierMat"
MESH_NAME = "Halberdier"
BASE_MODULE = "halberdier_base"
ANIM_MODULE = "anim_halberdier"
PARTS = ["Skin", "Eyes", "Teeth", "Beard", "Helmet", "Plume", "Steel", "Doublet", "Breeches", "Hose", "Sash", "Shoes",
         "Leather", "Katz", "Halberd", "Haft", "Tassel"]
REGION_PARTS = ("Skin", "Helmet", "Plume", "Steel", "Doublet", "Breeches", "Shoes", "Leather", "Katz", "Halberd", "Tassel")
CRIMSON = (0.55, 0.08, 0.08)
GOLD = (0.85, 0.62, 0.2)
IRIS = ((0.1, 0.27, 0.52), (0.34, 0.6, 0.86))          # bright blue eyes (the iris's outer ring, its inner ring)
STEEL = {"name": "HQ_LandsSteel", "base": (0.46, 0.47, 0.5)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_LandsSkin", "base": (0.88, 0.64, 0.5), "ruddy": (0.92, 0.46, 0.38), "lips": (0.72, 0.38, 0.34),
                      "brow": ((0.16, 0.09, 0.05), (0.32, 0.19, 0.1)),
                      "extra": ((LASH, (0.12, 0.07, 0.04), 0.5),)}),
    "Beard": ("hair", {"name": "HQ_LandsBeard", "base": (0.27, 0.15, 0.08), "hi": (0.56, 0.36, 0.2), "low": (0.12, 0.065, 0.035),
                       "streak": (0.36, 0.22, 0.12), "tint": (0.46, 0.26, 0.12)}),
    "Helmet": ("roman_steel", STEEL),
    "Plume": ("wool", {"name": "HQ_LandsPlume", "base": CRIMSON, "border": GOLD, "stripe": GOLD}),
    "Steel": ("roman_steel", STEEL),
    "Doublet": ("wool", {"name": "HQ_LandsDoublet", "base": CRIMSON, "border": GOLD, "stripe": GOLD}),
    "Breeches": ("wool", {"name": "HQ_LandsDoublet", "base": CRIMSON, "border": GOLD, "stripe": GOLD}),
    "Hose": ("linen", {"name": "HQ_LandsHose", "base": (0.93, 0.9, 0.82)}),
    "Sash": ("wool", {"name": "HQ_LandsSash", "base": GOLD, "border": (0.95, 0.8, 0.4), "stripe": (0.7, 0.48, 0.12)}),
    "Shoes": ("leather_dyed", {"name": "HQ_LandsShoes", "base": (0.2, 0.12, 0.07), "dyed": CRIMSON}),
    "Leather": ("leather_dyed", {"name": "HQ_LandsBelt", "base": (0.4, 0.23, 0.12), "dyed": (0.09, 0.075, 0.07)}),
    "Katz": ("roman_steel", {"name": "HQ_Katzbalger", "base": (0.5, 0.51, 0.54)}),
    "Halberd": ("roman_steel", {"name": "HQ_HalberdHead", "base": (0.52, 0.53, 0.57)}),
    "Haft": ("javelin_shaft", {"name": "HQ_HalberdHaft"}),
    "Tassel": ("wool", {"name": "HQ_HalberdTassel", "base": CRIMSON, "border": GOLD, "stripe": GOLD}),
}
LOW_TARGETS = {"Skin": 4500, "Teeth": 120, "Beard": 1400, "Helmet": 1900, "Plume": 1100, "Steel": 2500, "Doublet": 2800,
               "Breeches": 2100, "Hose": 600, "Sash": 600, "Shoes": 800, "Leather": 700, "Katz": 380, "Halberd": 1100,
               "Haft": 280, "Tassel": 320}
AO_EXCLUDE = ["Halberd", "Haft", "Tassel"]
# the halberd stands beside him at rest: baked 3 m away so his body leaves no shadow on its shaft
BAKE_APART = (["Halberd", "Haft", "Tassel"], (3.0, 0.0, 0.0))


def prop_bones():
    """The halberd's bone: from the butt up the shaft, no parent (posed in world space in every frame)."""
    O, A, B, W = hb_frame()
    return [("halberd", O, O + A * 0.4, None)]


def _rigid(ob, groups, v, w):
    for g in list(ob.vertex_groups):
        g.remove([v.index])
    _blend_add(ob, groups, v.index, w)


def steel_weights(ob, skin_ob, arm):
    """The breastplate with his body; the gorget with his neck and chest, its flare over the collarbones with them."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO)
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z > 1.3 and math.hypot(p.x, (p.y - 0.05) / 1.1) < 0.28 and not (p.y < -0.12 and p.z < 1.36):
            side = "R" if p.x < 0 else "L"
            t = max(0.0, min(1.0, (abs(p.x) - 0.1) / 0.14))
            up = max(0.0, min(1.0, (p.z - 1.32) / 0.12))
            w = {"chest": 1.0 - 0.35 * t - 0.25 * up, "clavicle." + side: 0.35 * t, "neck": 0.25 * up}
            _rigid(ob, groups, v, w)


def leather_weights(ob, skin_ob, arm):
    """The belt with his body; the scabbard and its straps rigid with his hips."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO)
    groups = {}
    D, U, S = kz_frame()
    for v in ob.data.vertices:
        q = np.array(v.co) - KZ_G
        along = float(q @ D)
        off = np.linalg.norm(q - D * along)
        if -0.05 < along < KZ_BLADE + 0.05 and off < 0.08:
            _rigid(ob, groups, v, {"root": 1.0})


def weight_rules():
    arms = {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L", "hand.R", "hand.L"}
    legs = {"thigh.R", "thigh.L", "shin.R", "shin.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Beard": ("rigid", "head"), "Helmet": ("rigid", "head"),
        "Plume": ("rigid", "head"),
        "Steel": ("custom", steel_weights),
        "Doublet": ("transfer", TORSO | arms, None),
        "Breeches": ("transfer", TORSO | legs, None),
        "Hose": ("transfer", {"root"} | legs | {"foot.R", "foot.L"}, None),
        "Sash": ("transfer", legs, None),
        "Shoes": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Leather": ("custom", leather_weights),
        "Katz": ("rigid", "root"),
        "Halberd": ("rigid", "halberd"), "Haft": ("rigid", "halberd"), "Tassel": ("rigid", "halberd"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.8
    if part in ("Halberd", "Tassel"):
        return 0.85
    if part == "Haft":
        return 0.5
    if part in ("Hose", "Katz"):
        return 0.8
    if part == "Skin" and c.z < 1.35 and abs(c.x) < 0.55:
        return 0.35                 # (his body, under his clothes)
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Beard", beard_field(), 0.0022 if fine else 0.0032),
        ("Helmet", helmet_field(), 0.0022 if fine else 0.0032),
        ("Plume", plume_field(), 0.0024 if fine else 0.0034),
        ("Steel", steel_field(), 0.0024 if fine else 0.0034),
        ("Doublet", doublet_field(), 0.0026 if fine else 0.0036),
        ("Breeches", breeches_field(), 0.0026 if fine else 0.0036),
        ("Hose", hose_field(), 0.0024 if fine else 0.0034),
        ("Sash", sash_field(), 0.0022 if fine else 0.003),
        ("Shoes", shoes_field(), 0.0022 if fine else 0.003),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Katz", katz_field(), 0.0016 if fine else 0.0022),
        ("Halberd", halberd_field(), 0.0018 if fine else 0.0026),
        ("Haft", haft_field(), 0.002 if fine else 0.003),
        ("Tassel", tassel_field(), 0.002 if fine else 0.0028),
    ]
