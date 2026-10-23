"""Sgt. Maya Cole, Marine (HQ hero, Modern Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A confident, tough Marine sergeant in her late twenties: dark brown skin, a strong, friendly face (a firm jaw, a rounded
chin, high cheekbones), warm dark eyes under straight, strong brows, and a determined half-smile (her left corner drawn
up higher, the lips parted on her upper teeth, a dimple on that side); black hair in tight cornrow braids gathered into a
braided bun at her nape. A high-cut combat helmet in a coyote cover: a raised rim, black accessory rails along its
sides, a black NVG shroud on its brow, smoke-lensed ballistic goggles on a black strap pushed up onto its front; black
comms earcups over her ears with a mic boom to the corner of her mouth. Olive-drab fatigues: the blouse's sleeves rolled
tight above her elbows, a fold-down collar; the trousers bloused into black combat boots, a cargo pocket on each thigh,
black knee pads; black gloves. A coyote plate carrier: flat front and back plates in MOLLE webbing, a cummerbund round
her sides, padded shoulder straps; three magazine pouches across her front, an admin pouch on her chest with the
red-and-white unit patch, a smoke-grenade pouch on her left side (the red-topped grenade is its own prop: she throws
it in the Ability), a radio pouch on her back-left with a whip antenna standing up behind her left shoulder and the
radio's handset clipped to her left shoulder strap; a coyote rigger's belt with a black buckle.

Her weapon: a modern assault rifle (black polymer furniture: a collapsible stock, the pistol grip, the magazine, a
vertical foregrip; a gunmetal receiver, a long rail handguard and a flash hider; a tube red-dot sight on the top rail,
its front lens coated red). Shoulder-fired.

She has Kira's build (kira.py) with both hands made fists (brenna.py) and Wren's booted feet (wren.py), as Ada (ada.py).
The rifle rides its own parentless bone (`rifle`: the pistol grip's middle to the muzzle); the smoke grenade its own
(`smoke`: the grenade's foot to its top; a child of the chest, sitting in its pouch, posed in world space while she
throws it). The rifle's rest placement floats before her right hip, pointing ahead (-Y); the clips pose it in world
space and put her fists on its grips (anim_maya.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
from kira import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S,
                  fist_center, torso_prims, traps, neck_prim, deltoid, upper_arm, _forearm, eyes_field, TORSO, TORSO_Z,
                  torso_bones, hstripe)
from brenna import hand, leg_prims
from wren import foot
from isla import _seg_dist_np, _seg_dist, boots_weights as _isla_boots_weights
from ada import ScaledField, _on_face, arm_prims, legs_hull, boot_hull, boot_top, lace_points

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH = 0, 1, 2, 3, 4, 5, 8
IRIS = ((0.13, 0.075, 0.045), (0.34, 0.2, 0.1))          # warm dark brown eyes (prep.paint_eyes)


# ======================================================================================= head
def mouth_curves(x):
    """The half-smile (design units): the upper lip's edge and the lower lip's edge at x; both corners drawn up into the
    cheeks, her left one (+x) higher; the lips parted on her upper teeth, closing at the corners."""
    x = np.asarray(x, dtype=np.float64)
    tilt = 0.075 * x + 4.0 * np.maximum(x, 0) ** 2
    up = 1.5625 + 5.2 * x * x + tilt
    lo = 1.5625 - 0.019 + 11.2 * x * x + tilt
    return up, lo


MOUTH_W = 0.055                    # half the smile's width (design)


def head(fd):
    """Ada's construction (ada.py: the smile that reads cheerful from the game camera) on a stronger face: Isla's broader
    jaw and firm chin, high cheekbones, a straight, broad nose; straight strong brows lying on her brow (never knitted);
    friendly open eyes, the lower lids lifted a little by the smile; a half-smile, her left corner higher, a dimple."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.06, 1.594), (0.142, 0.131, 0.126)), 0.07, SKIN)                          # a strong jaw
    fd.add(E((0, -0.13, 1.507), (0.073, 0.064, 0.061)), 0.05, SKIN)                          # a firm, rounded chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.028, -0.138, 1.5), 0.03), 0.03, SKIN)                                 # the chin's corners
        fd.add(S((sx * 0.112, -0.038, 1.552), 0.04), 0.05, SKIN)                               # the jaw's angles
        fd.add(S((sx * 0.108, -0.12, 1.638), 0.041), 0.05, SKIN)                               # high cheekbones
        fd.add(S((sx * 0.112, -0.05, 1.566), 0.043), 0.05, SKIN)
        fd.add(S((sx * 0.076, -0.142, 1.61), 0.027), 0.03, SKIN)                               # cheeks, lifted by the smile
        pts = [hp((sx * 0.15, -0.058, 1.748)), hp((sx * 0.115, -0.124, 1.754)), hp((sx * 0.062, -0.156, 1.752))]
        fd.add(Chain(pts, [hr(0.007), hr(0.0095), hr(0.008)], k=hr(0.02)), hr(0.03), SKIN)    # a firm brow bone
    # brows: straight and strong, a gentle lift at the outer ends, lying on her brow (raised hair and a painted band)
    for sx in (-1, 1):
        lift = 0.002 if sx > 0 else 0.0
        xz = [(sx * 0.028, 1.781), (sx * 0.064, 1.79 + lift), (sx * 0.104, 1.794 + lift), (sx * 0.143, 1.781 + lift * 0.5)]
        on = _on_face(fd, xz, lift=0.001)
        fd.add(Chain(on, [hr(0.0046), hr(0.0056), hr(0.0048), hr(0.0024)], k=hr(0.006)), hr(0.004), BROW)
        fd.paint(Chain(on, [hr(0.0115), hr(0.0135), hr(0.0115), hr(0.006)], k=hr(0.008)), BROW)
    # eyes: open and friendly; the upper lids clear of the irises, the lower lids lifted a little by her cheeks
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, hr(0.0235))), (sx * 0.18, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0046)), Plane(ec + v3((0, 0, -hr(0.018))), (sx * -0.3, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.006), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.008)), Plane(ec + v3((0, 0, hr(0.0205))), (sx * 0.18, 0.05, -1.0)), hr(0.002)), LASH)
        flick = ec + v3((sx * hr(0.039), -hr(0.012), hr(0.016)))
        fd.add(RoundCone(flick, flick + v3((sx * hr(0.012), hr(0.006), hr(0.006))), hr(0.0038), hr(0.0014)), hr(0.004), LASH)
    # a straight, broad nose
    fd.add(RoundCone(hp((0, -0.178, 1.722)), hp((0, -0.212, 1.648)), hr(0.012), hr(0.016)), hr(0.016), SKIN)
    fd.add(S((0, -0.213, 1.639), 0.02), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.026, -0.195, 1.627), 0.0155), hr(0.01), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.013, -0.208, 1.616)), v3((0.008, 0.009, 0.005)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the half-smile: a narrow crescent between the lips' edges, corners up into the cheeks (her left one higher)
    xs = np.linspace(-MOUTH_W, MOUTH_W, 9)
    up_z, lo_z = mouth_curves(xs)
    upper = _on_face(fd, [(x, z + 0.004) for x, z in zip(xs, up_z)])
    lower = _on_face(fd, [(x, z - 0.0045) for x, z in zip(xs, lo_z)])
    def opening(P):
        Q = hinv(P)
        x, z = Q[:, 0], Q[:, 2]
        u, l = mouth_curves(x)
        dz = np.maximum(z - u.astype(F), l.astype(F) - z)
        dx = np.abs(x) - F(MOUTH_W)
        return np.maximum(np.maximum(dz, dx), (Q[:, 1] - F(-0.205)) * F(-1)) * F(HS)
    cav = Inter(Func(opening, hp((-0.09, -0.24, 1.48)), hp((0.09, -0.12, 1.62))),
                Ellipsoid(hp((0.0, -0.165, 1.555)), v3((0.075, 0.03, 0.05)) * HS), hr(0.002))
    fd.sub(cav, hr(0.004))
    fd.paint(Inter(Func(lambda P: opening(P) - F(0.0025), hp((-0.09, -0.24, 1.48)), hp((0.09, -0.12, 1.62))),
                   Ellipsoid(hp((0.0, -0.165, 1.555)), v3((0.08, 0.04, 0.06)) * HS), hr(0.002)), MOUTH)
    # full lips, tapering into the corners
    ru = [0.0026, 0.0046, 0.006, 0.0068, 0.007, 0.0068, 0.006, 0.0046, 0.0026]
    rl = [0.0028, 0.0055, 0.0076, 0.0088, 0.0092, 0.0088, 0.0076, 0.0055, 0.0028]
    fd.add(Chain(upper, [hr(r) for r in ru], k=hr(0.005)), hr(0.007), LIP)
    fd.add(Chain(lower, [hr(r) for r in rl], k=hr(0.006)), hr(0.008), LIP)
    for sx in (-1, 1):
        cx = sx * (MOUTH_W + 0.006)
        cz = float(mouth_curves(cx)[0])
        fd.add(S((sx * 0.078, -0.15, cz + 0.014 + (0.004 if sx > 0 else 0.0)), 0.012), hr(0.01), SKIN)   # the smile's cheeks
        if sx > 0:
            fd.sub(S((sx * (MOUTH_W + 0.016), -0.152, cz + 0.002), 0.0055), hr(0.006))                  # a dimple on her left
        fd.add(Ellipsoid(hp((sx * 0.174, 0.035, 1.66)), v3((0.024, 0.043, 0.054)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)


def teeth_field():
    """Her upper teeth, showing under her upper lip in the smile (following its curve, set back in the mouth)."""
    fd = Field("Teeth")
    xs = np.linspace(-0.04, 0.04, 7)
    up_z, lo_z = mouth_curves(xs)
    pts = [hp((x, -0.178 + 7.0 * x * x, z - 0.008)) for x, z in zip(xs, up_z)]
    fd.add(Chain(pts, [hr(0.0085)] * len(pts), k=hr(0.004)), 0.0)
    return fd


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.05, SKIN)
    fd.add(neck_prim(), 0.045, SKIN)
    for side in ("R", "L"):
        for p, k in arm_prims(side):
            fd.add(p, k, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= hair: cornrows into a bun at the nape
BUN = hp((0.0, 0.222, 1.618))             # the braided bun, low at her nape (under the helmet's back rim)
BUN_AX = norm(BUN - HEAD_C)
EAR_C = {sx: hp((sx * 0.174, 0.035, 1.66)) for sx in (-1, 1)}


def hairline(P):
    """> 0 below her hairline (design units): her forehead, in front of her ears, down to the nape."""
    Q = hinv(P)
    y = Q[:, 1]
    zl = F(1.852) - F(0.1) * smoothstep(-0.14, -0.06, y) - F(0.24) * smoothstep(0.075, 0.16, y)
    return zl - Q[:, 2]


def hair_region(P):
    ears = None
    for sx in (-1, 1):
        q = P - EAR_C[sx].astype(F)
        e = F(hr(0.064)) - np.sqrt((q * q).sum(1))
        ears = e if ears is None else np.maximum(ears, e)
    return np.maximum(hairline(P) * F(HS), ears)


def _cornrows(P):
    """Cornrows: tight braids running back from her hairline to the bun (grooves round the bun's axis), each braid's
    plaits a chain of small bumps along it."""
    e1 = norm(np.cross(BUN_AX, v3((1, 0, 0))))
    e2 = np.cross(BUN_AX, e1)
    q = P - HEAD_C.astype(F)
    a = np.arctan2(q @ e2.astype(F), q @ e1.astype(F))
    rows = np.abs(np.sin(a * F(13)))
    plait = np.abs(np.sin((q @ BUN_AX.astype(F)) * F(260) + a * F(13)))
    return F(0.0028) * rows ** 0.5 - F(0.0009) * plait * (F(1) - rows) + F(0.0006) * NOISE(P * F(45))


def hair_field():
    """Black hair braided in tight cornrows back to her nape, wound there into a braided bun."""
    fd = Field("Hair")
    head_ = Ellipsoid(HEAD_C, HEAD_RAD)
    def cap(P):
        d = head_(P)
        h = -hairline(P)
        th = F(0.004) + F(0.012) * smoothstep(0.0, 0.03, h)
        return np.abs(d - (F(0.002) + th * F(0.5))) - th * F(0.5) + _cornrows(P)
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    fd.add(Inter(Func(cap, lo, hi), Func(hair_region, lo, hi), 0.003), 0.0)
    # the bun: a braid coiled round on itself
    R = rot_from_axes(z_axis=BUN_AX)
    plaits = lambda P: F(0.0022) * np.abs(np.sin((P @ np.array([0.7, 0.4, 1.0], F)) * F(190))) + F(0.0008) * NOISE(P * F(60))
    fd.add(Ellipsoid(BUN - BUN_AX * 0.012, v3((0.046, 0.046, 0.03)) * HS, R=R), 0.012)
    pts = []
    for i in range(22):
        t = i / 21.0
        a = 2 * math.pi * 1.6 * t
        r = hr(0.044) * (1.0 - 0.75 * t)
        pts.append(BUN + R @ v3((math.cos(a) * r, math.sin(a) * r, 0.006 + 0.016 * t)))
    fd.add(Chain(pts, [hr(0.0135) * (1.0 - 0.35 * i / 21.0) for i in range(22)], k=hr(0.006), disp=plaits, disp_amp=0.0025), 0.006)
    return fd


# ======================================================================================= the helmet
H_OFF, H_T = 0.044, 0.026                # the shell's middle off her head's ellipsoid, its thickness
H_OUT = H_OFF + H_T / 2


def _hang(Q):
    """The angle round her head (design coordinates): 0 at her front, +/- pi behind, + toward her left."""
    return np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.03)))


def rim_z(Q):
    """The helmet's rim height (design): low on her brow (clear of her brows), rising a little over her ears (high-cut),
    down at the back over the nape."""
    a = np.abs(_hang(Q))
    return F(1.838) - F(0.125) * smoothstep(1.0, 2.6, a) + F(0.02) * np.exp(-((a - F(1.6)) / F(0.35)) ** 2)


def _helm_hull():
    return Ellipsoid(HEAD_C + v3((0.0, 0.004, 0.006)), HEAD_RAD)


def helm_point(a, dz, out=0.0):
    """A point on the helmet's outer surface at angle a round her head (degrees), dz above the rim (design), and its
    outward normal."""
    hull = _helm_hull()
    ar = math.radians(a)
    d = v3((math.sin(ar), -math.cos(ar), 0.0))
    z = 1.84
    for _ in range(3):
        o = hp((0.0, 0.03, z)) + d * 0.6
        h, ok = ray_hit(Func(lambda P: hull(P) - F(H_OUT + out), HEAD_C - 0.5, HEAD_C + 0.5), [o], [-d], tmax=0.8)
        p = h[0] if ok[0] else o - d * 0.4
        Q = hinv(p[None].astype(F))
        z = float(rim_z(Q)[0]) + dz
    eps = 1e-3
    g = np.array([(hull(np.array([p + e], F))[0] - hull(np.array([p - e], F))[0]) / (2 * eps) for e in np.eye(3) * eps])
    return p, norm(g)


def helmet_field():
    """A high-cut combat helmet in a coyote cloth cover (label 0): a raised rim; black (8) accessory rails along its
    sides, an NVG shroud on its brow, the goggles' strap round it and the goggles' frame on its front."""
    fd = Field("Helmet")
    hull = _helm_hull()
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    def below(P, extra=0.0):
        Q = hinv(P)
        return (rim_z(Q) + F(extra) - Q[:, 2]) * F(HS)
    wrin = lambda P: F(0.0012) * NOISE(P * F(26)) + F(0.0006) * NOISE(P * F(70))
    fd.add(Inter(Shell(hull, H_OFF, H_T, pad=0.07, disp=wrin, disp_amp=0.0015), Func(below, lo, hi), 0.004), 0.0)
    # the rim: a rolled edge round its lower lip
    fd.add(Inter(Shell(hull, H_OFF + 0.002, H_T + 0.008, pad=0.08), Func(lambda P: np.abs(below(P, 0.012)) - F(0.011), lo, hi), 0.004), 0.004)
    # side rails (black): a raised strip along each side above the ear
    def rails(P):
        Q = hinv(P)
        a = np.abs(_hang(Q))
        h = Q[:, 2] - rim_z(Q)
        return np.maximum(np.abs(h - F(0.028)) - F(0.008), np.maximum(F(1.05) - a, a - F(2.25)))
    fd.add(Inter(Shell(hull, H_OUT + 0.004, 0.014, pad=0.08), Func(rails, lo, hi), 0.003), 0.003, 8)
    # the goggles' strap round the helmet, above the rails
    def strap(P):
        Q = hinv(P)
        h = Q[:, 2] - rim_z(Q)
        return np.abs(h - F(0.058)) - F(0.012)
    fd.add(Inter(Shell(hull, H_OUT + 0.003, 0.009, pad=0.08), Func(strap, lo, hi), 0.003), 0.003, 8)
    # the goggles' frame on the front: a curved band with a window for the lens
    def gog(P, grow=0.0):
        Q = hinv(P)
        a = _hang(Q)
        h = Q[:, 2] - rim_z(Q)
        top = F(0.088) + F(0.008) * np.cos(a * F(2.4))
        return np.maximum(np.maximum(F(0.012) - h, h - top), np.abs(a) - F(0.78)) - F(grow)
    def window(P):
        Q = hinv(P)
        a = _hang(Q)
        h = Q[:, 2] - rim_z(Q)
        top = F(0.076) + F(0.008) * np.cos(a * F(2.4))
        nose = F(0.012) * np.exp(-(a / F(0.12)) ** 2)                     # (the bridge over her nose)
        return np.maximum(np.maximum(F(0.024) + nose - h, h - top), np.abs(a) - F(0.66))
    fd.add(Inter(Shell(hull, H_OUT + 0.016, 0.024, pad=0.1), Func(gog, lo, hi), 0.004), 0.004, 8)
    fd.sub(Inter(Shell(hull, H_OUT + 0.026, 0.014, pad=0.1), Func(window, lo, hi), 0.002), 0.002)
    # the NVG shroud on the brow, above the goggles: a plate with a mount
    p, n = helm_point(0.0, 0.112)
    R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
    fd.add(RoundBox(p + n * 0.006, (0.034, 0.026, 0.012), 0.006, R=R), 0.004, 8)
    fd.add(RoundBox(p + n * 0.016 - R[:, 1] * 0.008, (0.016, 0.014, 0.01), 0.004, R=R), 0.003, 8)
    # a velcro patch on the back
    p, n = helm_point(180.0, 0.07)
    fd.add(RoundBox(p, (0.04, 0.025, 0.006), 0.004, R=rot_from_axes(z_axis=n, y_axis=(0, 0, 1))), 0.003, 0)
    return fd


def lens_field():
    """The goggles' smoke lens in its frame's window."""
    fd = Field("Lens")
    hull = _helm_hull()
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    def win(P):
        Q = hinv(P)
        a = _hang(Q)
        h = Q[:, 2] - rim_z(Q)
        top = F(0.08) + F(0.008) * np.cos(a * F(2.4))
        nose = F(0.012) * np.exp(-(a / F(0.12)) ** 2)
        return np.maximum(np.maximum(F(0.02) + nose - h, h - top), np.abs(a) - F(0.7))
    fd.add(Inter(Shell(hull, H_OUT + 0.02, 0.012, pad=0.1), Func(win, lo, hi), 0.002), 0.0)
    return fd


# ======================================================================================= the headset
CUP_R, CUP_H = 0.058, 0.04


def cup_frame(sx):
    """(centre, outward axis) of an earcup over her ear."""
    ax = norm(v3((sx, 0.08, -0.04)))
    return EAR_C[sx] + ax * 0.026 + v3((0, 0.002, 0.004)), ax


MIC = [hp((-0.205, -0.03, 1.615)), hp((-0.175, -0.13, 1.575)), hp((-0.12, -0.19, 1.556)), hp((-0.082, -0.212, 1.556))]


def headset_field():
    """Black (label 5) comms earcups over her ears (dark (8) rims and a cushion against her head), the band behind her
    nape between them, the mic boom from her right cup to the corner of her mouth (a foam ball at its end)."""
    fd = Field("Headset")
    for sx in (-1, 1):
        c, ax = cup_frame(sx)
        R = rot_from_axes(z_axis=ax)
        fd.add(Cylinder(c + ax * (CUP_H * 0.5), CUP_R, CUP_H, rr=0.018, R=R), 0.0, 5)
        fd.add(Cylinder(c + ax * (CUP_H * 0.5 + 0.004), CUP_R * 0.7, CUP_H, rr=0.012, R=R), 0.006, 5)
        fd.add(Torus(c + ax * 0.004, CUP_R - 0.006, 0.01, R=R), 0.006, 8)                    # the cushion
        fd.add(RoundBox(c + ax * (CUP_H + 0.004) + v3((0, 0, 0.012)), (0.012, 0.022, 0.006), 0.004, R=R), 0.004, 8)   # buttons
    # the band behind her nape
    cR, aR = cup_frame(-1)
    cL, aL = cup_frame(1)
    band = [cR + aR * 0.012 + v3((0, 0.03, -0.03)), hp((-0.1, 0.19, 1.58)), hp((0.0, 0.215, 1.575)), hp((0.1, 0.19, 1.58)),
            cL + aL * 0.012 + v3((0, 0.03, -0.03))]
    fd.add(Chain(band, [0.011] * 5, k=0.006), 0.006, 8)
    # the mic boom
    fd.add(Chain(MIC, [0.0075, 0.007, 0.0065, 0.006], k=0.004), 0.004, 8)
    fd.add(Sphere(MIC[-1] + norm(MIC[-1] - MIC[-2]) * 0.008, 0.014), 0.004, 5)
    return fd


# ======================================================================================= the fatigues: blouse
SLEEVE_T = 0.2                     # the rolled sleeves' end: this far up the upper arm from the elbow (fraction of el -> sh)
BL_OFF, BL_T = 0.012, 0.01


def blouse_hull():
    b = Field("BlouseHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    for side in ("R", "L"):
        for p, k in arm_prims(side):
            b.add(p, k)
    return b


def sleeve_end(side):
    """The rolled sleeve's end on the upper arm (above the elbow) and the direction down the arm."""
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    ax = norm(el - sh)
    return el - ax * (float(np.linalg.norm(el - sh)) * SLEEVE_T), ax


def sleeve_cut(P):
    """> 0 past the rolled sleeves' ends (only near the arm below them)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        c, ax = sleeve_end(side)
        wr = J["wrist_" + side]
        along = (P - c.astype(F)) @ ax.astype(F)
        near = _seg_dist_np(P, c, wr + norm(wr - J["elbow_" + side]) * 0.25) < F(0.12)
        out = np.maximum(out, np.where(near, along, F(-1.0)))
    return out


def neck_line(P, base=1.43):
    """> 0 above a neckline round her neck only (lifted clear of the shoulders, so it opens no hole on them)."""
    ax = np.abs(P[:, 0])
    return P[:, 2] - (F(base) + F(0.075) * smoothstep(-0.04, 0.12, P[:, 1]) + F(0.3) * smoothstep(0.12, 0.19, ax))


def blouse_field():
    """Olive-drab ripstop (label 0): tucked into her trousers, the sleeves rolled tight above her elbows (a thick, flat
    roll), a fold-down collar open at her throat."""
    fd = Field("Shirt")
    hull = blouse_hull()
    def wr_(P):
        return (F(0.0013) * NOISE(P * F(28)) + F(0.0016) * np.sin(P[:, 2] * F(55) + F(2) * NOISE(P * F(5))) * smoothstep(0.24, 0.36, np.abs(P[:, 0]))
                + F(0.0012) * np.sin(P[:, 2] * F(80)) * smoothstep(1.0, 0.9, P[:, 2]))
    def cut(P):
        return np.maximum(np.maximum(F(0.86) - P[:, 2], neck_line(P)), sleeve_cut(P))
    fd.add(Inter(Shell(hull, BL_OFF, BL_T, pad=0.1, disp=wr_, disp_amp=0.003), Func(cut, (-1, -0.6, 0.7), (1, 0.6, 1.7)), 0.004), 0.0)
    # the rolled sleeves: a thick roll round each upper arm at the sleeve's end
    for side in ("R", "L"):
        c, ax = sleeve_end(side)
        arm = Field("Arm" + side)
        for p, k in arm_prims(side):
            arm.add(p, k)
        def band(P, c=c, ax=ax):
            s = (P - c.astype(F)) @ ax.astype(F)
            near = _seg_dist_np(P, c - ax * 0.08, c + ax * 0.08) < F(0.14)
            return np.where(near, np.abs(s + F(0.016)) - F(0.024), F(1.0))
        roll = lambda P: F(0.0025) * np.sin(np.arctan2(P[:, 2], P[:, 1]) * F(6) + F(2) * NOISE(P * F(12))) + F(0.001) * NOISE(P * F(40))
        fd.add(Inter(Shell(arm, BL_OFF + 0.014, 0.024, pad=0.06, disp=roll, disp_amp=0.003), Func(band, c - 0.2, c + 0.2), 0.008), 0.006)
    # the fold-down collar: a band round her neck flaring out over the shirt, open at her throat
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    def collar(P):
        z = P[:, 2]
        band = np.abs(z - F(1.43)) - F(0.028)
        opn = F(0.03) - np.abs(P[:, 0]) + F(0.25) * (z - F(1.40))
        return np.maximum(band, np.where(P[:, 1] < F(0.0), opn, F(-1.0)))
    def flared(P):
        off = F(0.018) + F(0.02) * smoothstep(1.455, 1.40, P[:, 2])
        return np.abs(nk.eval(P, margin=0.1) - off) - F(0.0055)
    fd.add(Inter(Func(flared, (-0.3, -0.3, 1.3), (0.3, 0.4, 1.6)), Func(collar, (-0.3, -0.3, 1.3), (0.3, 0.3, 1.6)), 0.004), 0.006)
    return fd


# ======================================================================================= the plate carrier
PC_OFF, PC_T = 0.038, 0.028
PC_OUT = PC_OFF + PC_T / 2
CB_Z = (0.93, 1.1)                     # the cummerbund
FRONT_Z = (0.93, 1.3)
BACK_Z = (0.95, 1.37)


def carrier_hull():
    """Her torso with the front and back flattened into plates."""
    b = Field("CarrierHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(RoundBox((0.0, -0.1, 1.1), (0.15, 0.075, 0.2), 0.05), 0.04)
    b.add(RoundBox((0.0, 0.16, 1.14), (0.17, 0.07, 0.21), 0.05), 0.04)
    return b


_CH = None


def _ch():
    global _CH
    if _CH is None:
        _CH = carrier_hull()
    return _CH


def pc_region(P):
    """< 0 on the carrier: the front and back plates, the cummerbund round her sides, the shoulder straps."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    top_f = F(FRONT_Z[1]) + F(0.035) * smoothstep(0.05, 0.15, ax)
    front = np.maximum(np.maximum(ax - F(0.165), y + F(0.02)), np.maximum(F(FRONT_Z[0]) - z, z - top_f))
    back = np.maximum(np.maximum(ax - F(0.18), F(0.05) - y), np.maximum(F(BACK_Z[0]) - z, z - F(BACK_Z[1])))
    cb = np.maximum(F(CB_Z[0]) - z, z - F(CB_Z[1]))
    straps = np.maximum(np.maximum(ax - F(0.168), F(0.085) - ax), F(1.24) - z)
    return np.minimum(np.minimum(front, back), np.minimum(cb, straps))


def molle(P):
    """MOLLE webbing: horizontal rows of stitched straps pressed into the plates and the cummerbund."""
    s = np.sin((P[:, 2] - F(0.93)) * F(2 * math.pi / 0.032))
    return F(0.0014) * smoothstep(-0.2, 0.6, s) + F(0.0007) * NOISE(P * F(40))


def pc_point(x, z, gap=0.0, front=True):
    """A point on the carrier's outer face, straight in front of (x, z) (or behind it), and the outward direction."""
    ch = _ch()
    d = v3((0, -1, 0)) if front else v3((0, 1, 0))
    h, ok = ray_hit(Func(lambda P: ch.eval(P, margin=0.12) - F(PC_OUT + gap), (-1, -1, 0.6), (1, 1, 1.7)),
                    [v3((x, 0.04, z)) + d * 0.7], [-d], tmax=0.8)
    return (h[0] if ok[0] else v3((x, 0.04, z)) + d * 0.25), d


def pc_side_point(angle_deg, z, gap=0.0):
    """A point on the carrier's outer face at an angle round her (from her front toward her left) and height z."""
    ch = _ch()
    a = math.radians(angle_deg)
    d = v3((math.sin(a), -math.cos(a), 0.0))
    h, ok = ray_hit(Func(lambda P: ch.eval(P, margin=0.12) - F(PC_OUT + gap), (-1, -1, 0.6), (1, 1, 1.7)),
                    [v3((0, 0.04, z)) + d * 0.7], [-d], tmax=0.8)
    return (h[0] if ok[0] else v3((0, 0.04, z)) + d * 0.3), d


MAG_X = (-0.096, 0.0, 0.096)
PATCH_Z = 1.215
NADE_ANGLE, NADE_Z = 64.0, 0.985           # the smoke grenade's pouch on her left side
RADIO_ANGLE, RADIO_Z = 146.0, 1.1          # the radio's pouch on her back-left


def _frame_out(d):
    side = norm(np.cross(v3((0, 0, 1)), d))
    return np.stack([side, d, v3((0, 0, 1))], 1)


def carrier_field():
    """Coyote nylon (label 0) in MOLLE rows: the plates, the cummerbund and the straps; three magazine pouches across her
    front (black (8) pull tabs), an admin pouch on her chest carrying the unit patch (red, 5, with a white (7) border and
    chevron), the smoke grenade's open pouch on her left side, black side-release buckles on the cummerbund."""
    fd = Field("Carrier")
    ch = _ch()
    hlo, hhi = ch.bounds()
    def plates(P):
        d = ch.eval(P, margin=0.07)
        return np.abs(d - F(PC_OFF)) - F(PC_T * 0.5) + molle(P)
    fd.add(Inter(Func(plates, hlo - 0.06, hhi + 0.06), Func(pc_region, (-0.6, -0.5, 0.8), (0.6, 0.5, 1.6)), 0.006), 0.0)
    # padded shoulder straps: a roll along each strap's middle
    for sx in (-1, 1):
        def pad(P, sx=sx):
            d = ch.eval(P, margin=0.1)
            return np.maximum(np.abs(d - F(PC_OUT + 0.006)) - F(0.012),
                              np.maximum(np.abs(P[:, 0] - F(sx * 0.127)) - F(0.03), F(1.28) - P[:, 2]))
        fd.add(Func(pad, (sx * 0.127 - 0.1, -0.35, 1.2), (sx * 0.127 + 0.1, 0.35, 1.6)), 0.008)
    # the magazine pouches
    for x in MAG_X:
        p, d = pc_point(x, 1.0)
        R = _frame_out(-d)
        fd.add(RoundBox(p + d * 0.03 + v3((0, 0, -0.004)), (0.043, 0.031, 0.068), 0.012, R=R,
                        disp=lambda P: F(0.0008) * NOISE(P * F(50)), disp_amp=0.001), 0.006)
        fd.add(RoundBox(p + d * 0.059 + v3((0, 0, 0.044)), (0.045, 0.006, 0.026), 0.005, R=R), 0.004)          # the flap
        fd.add(RoundBox(p + d * 0.066 + v3((0, 0, 0.036)), (0.012, 0.005, 0.02), 0.004, R=R), 0.002, 8)        # its pull tab
    # the admin pouch on her chest with the unit patch
    p, d = pc_point(0.0, PATCH_Z)
    R = _frame_out(-d)
    fd.add(RoundBox(p + d * 0.012, (0.074, 0.014, 0.052), 0.008, R=R), 0.005)
    pc = p + d * 0.027
    fd.add(RoundBox(pc, (0.045, 0.004, 0.032), 0.003, R=R), 0.002, 5)
    side = R[:, 0]
    def emblem(P, pc=pc, side=side):
        q = P - pc.astype(F)
        u, w = q @ side.astype(F), q[:, 2]
        border = F(0.006) - np.minimum(F(0.045) - np.abs(u), F(0.032) - np.abs(w))
        chev = np.abs(w - F(0.004) + np.abs(u) * F(0.75)) - F(0.0055)
        chev = np.maximum(chev, np.abs(u) - F(0.024))
        return np.minimum(-border, chev)
    fd.paint(Func(emblem, pc - 0.06, pc + 0.06), 7)
    # the smoke grenade's pouch: an open cylinder on her left side
    p, d = pc_side_point(NADE_ANGLE, NADE_Z)
    c = p + d * 0.04
    fd.add(Cylinder(c, 0.04, 0.085, rr=0.01), 0.006)
    fd.sub(Cylinder(c + v3((0, 0, 0.03)), 0.0315, 0.06, rr=0.004), 0.003)
    fd.add(RoundBox(c + d * 0.034 + v3((0, 0, 0.0)), (0.012, 0.005, 0.03), 0.004, R=_frame_out(d)), 0.002, 8)
    # side-release buckles at the cummerbund's front edges
    for sx in (-1, 1):
        p, d = pc_side_point(sx * 52.0, 1.015)
        fd.add(RoundBox(p + d * 0.004, (0.024, 0.006, 0.018), 0.004, R=_frame_out(d)), 0.003, 8)
    return fd


def nade_rest():
    """(foot, axis) of the smoke grenade sitting in its pouch."""
    p, d = pc_side_point(NADE_ANGLE, NADE_Z)
    c = p + d * 0.04
    ax = norm(v3((0, 0, 1)) + d * 0.06)
    return c - v3((0, 0, 0.004)), ax


NADE_R, NADE_L = 0.03, 0.125


def smoke_field():
    """An M18-style smoke grenade: a grey-green can (label 0: fieldgun's olive paint), its top and a band painted red
    (12), the fuze, spoon and pin ring of bright steel (7)."""
    fd = Field("Smoke")
    b, ax = nade_rest()
    R = rot_from_axes(z_axis=ax)
    fd.add(Cylinder(b + ax * (NADE_L * 0.42), NADE_R, NADE_L * 0.84, rr=0.008, R=R), 0.0, 0)
    fd.paint(Cylinder(b + ax * (NADE_L * 0.74), NADE_R + 0.01, 0.022, R=R), 12)
    fd.add(Cylinder(b + ax * (NADE_L * 0.86), NADE_R * 0.9, 0.012, rr=0.004, R=R), 0.003, 12)
    fd.add(Cylinder(b + ax * (NADE_L * 0.93), 0.012, 0.022, rr=0.004, R=R), 0.003, 7)          # the fuze
    sd = R[:, 0]
    sp = [b + ax * (NADE_L * 0.98) + sd * 0.006, b + ax * (NADE_L * 0.9) + sd * (NADE_R + 0.004), b + ax * (NADE_L * 0.45) + sd * (NADE_R + 0.004)]
    fd.add(Chain(sp, [0.005, 0.005, 0.004], k=0.003), 0.002, 7)                                 # the spoon
    fd.add(Torus(b + ax * (NADE_L * 0.94) - sd * 0.022, 0.011, 0.0025, R=rot_from_axes(z_axis=R[:, 1])), 0.002, 7)   # the pin's ring
    return fd


def radio_frame():
    p, d = pc_side_point(RADIO_ANGLE, RADIO_Z)
    R = _frame_out(d)
    return p, d, R


ANT_D = norm(v3((0.1, 0.16, 1.0)))
ANT_L = 0.64


def radio_field():
    """The radio in its coyote pouch (label 0) on her back-left: the black radio (8) showing above it, its whip antenna
    (8) standing up behind her left shoulder; the handset (8) clipped to her left shoulder strap."""
    fd = Field("Radio")
    p, d, R = radio_frame()
    c = p + d * 0.045
    fd.add(RoundBox(c, (0.062, 0.045, 0.09), 0.014, R=R, disp=lambda P: F(0.0008) * NOISE(P * F(50)), disp_amp=0.001), 0.0, 0)
    fd.add(RoundBox(c + v3((0, 0, 0.1)), (0.05, 0.036, 0.03), 0.01, R=R), 0.006, 8)              # the radio's top
    knob = c + v3((0, 0, 0.13)) + R[:, 0] * 0.025
    fd.add(Cylinder(knob, 0.011, 0.016, rr=0.004), 0.003, 8)
    base = c + v3((0, 0, 0.128)) - R[:, 0] * 0.02
    fd.add(Cylinder(base + v3((0, 0, 0.012)), 0.012, 0.028, rr=0.004), 0.003, 8)
    tip = base + ANT_D * ANT_L
    fd.add(RoundCone(base + v3((0, 0, 0.02)), tip, 0.0075, 0.0055), 0.003, 8)
    fd.add(Sphere(tip, 0.009), 0.003, 8)
    # the handset on her left shoulder strap
    hp0, hd = pc_point(0.128, 1.33, 0.012)
    Rh = _frame_out(-hd) @ euler(0.15, 0, 0)
    fd.add(RoundBox(hp0 + hd * 0.012, (0.02, 0.016, 0.052), 0.012, R=Rh), 0.004, 8)
    fd.add(RoundBox(hp0 + hd * 0.022 + v3((0, 0, 0.034)), (0.022, 0.014, 0.02), 0.01, R=Rh), 0.004, 8)   # its earpiece
    return fd


# ======================================================================================= trousers, pads, boots, belt
def trousers_field():
    """Olive-drab ripstop trousers (label 0) from her waist into her boots, bloused over the boots' tops, creased at the
    knees; a cargo pocket with a flap on the outside of each thigh."""
    fd = Field("Trousers")
    hips = Field("Hips")
    tp = torso_prims()
    hips.add(tp[4][0], 0.0)
    hips.add(tp[5][0], tp[5][1])
    crease = lambda P: F(0.0014) * NOISE(P * F(26)) + F(0.0012) * np.sin(P[:, 2] * F(110)) * smoothstep(0.52, 0.42, P[:, 2])
    fd.add(Inter(Shell(hips, 0.012, 0.01, pad=0.08), Func(lambda P: np.maximum(P[:, 2] - F(0.97), F(0.6) - P[:, 2]), (-0.6, -0.5, 0.5), (0.6, 0.5, 1.1)), 0.004), 0.0)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        lb = legs_hull(side)
        hip = J["hip_" + side]
        fd.add(Inter(Shell(lb, 0.01, 0.01, pad=0.06, disp=crease, disp_amp=0.002),
                     Func(lambda P: np.maximum(F(0.3) - P[:, 2], P[:, 2] - F(0.86)), hip - v3((0.3, 0.3, 0.8)), hip + v3((0.3, 0.3, 0.2))), 0.004), 0.02)
        # bloused over the boot's top: a soft roll
        blouse = lambda P: F(0.003) * np.sin(np.arctan2(P[:, 1], P[:, 0]) * F(9) + F(2) * NOISE(P * F(10)))
        fd.add(Inter(Shell(lb, 0.026, 0.024, pad=0.06, disp=blouse, disp_amp=0.004),
                     Func(lambda P: np.abs(P[:, 2] - (boot_top(P) + F(0.018))) - F(0.022), hip - v3((0.3, 0.4, 0.8)), hip + v3((0.3, 0.3, -0.2))), 0.008), 0.012)
        # the cargo pocket on the outside of the thigh
        o = v3((hip[0] + sx * 0.4, hip[1] - 0.01, 0.56))
        h, ok = ray_hit(Func(lambda P: lb.eval(P, margin=0.1) - F(0.02), hip - v3((0.5, 0.5, 0.6)), hip + v3((0.5, 0.5, 0.2))), [o], [v3((-sx, 0, 0))], tmax=0.6)
        q = h[0] if ok[0] else v3((hip[0] + sx * 0.12, hip[1], 0.56))
        n = norm(v3((sx, -0.15, 0)))
        Rp = rot_from_axes(z_axis=v3((0, 0, 1)), y_axis=n)
        fd.add(RoundBox(q + n * 0.008, (0.062, 0.022, 0.075), 0.016, R=Rp), 0.012)
        fd.add(RoundBox(q + n * 0.024 + v3((0, 0, 0.06)), (0.066, 0.008, 0.024), 0.006, R=Rp), 0.004)
    return fd


def pads_field():
    """Black knee pads (armory's leather, label 5): a moulded cap over each knee, its strap round the leg behind."""
    fd = Field("Pads")
    for side in ("R", "L"):
        kn, an, hip = J["knee_" + side], J["ankle_" + side], J["hip_" + side]
        ax = norm(an - kn)
        c = kn + v3((0, -0.098, -0.008))
        R = rot_from_axes(z_axis=-ax, y_axis=(0, -1, 0))
        fd.add(Ellipsoid(c, (0.066, 0.03, 0.08), R=R), 0.0, 5)
        fd.add(Ellipsoid(c + v3((0, -0.016, 0.004)), (0.05, 0.022, 0.06), R=R), 0.012, 5)
        lb = legs_hull(side)
        for dz, w in ((0.06, 0.012), (-0.07, 0.012)):
            z0 = kn[2] + dz
            fd.add(Inter(Shell(lb, 0.026, 0.012, pad=0.06), Func(lambda P, z0=z0, w=w: np.abs(P[:, 2] - F(z0)) - F(w), kn - v3((0.2, 0.2, 0.2)), kn + v3((0.2, 0.2, 0.2))), 0.003), 0.006, 5)
    return fd


BOOT_TOP_F, BOOT_TOP_B = 0.385, 0.355


def boots_field():
    """Black combat boots (leather_dyed: label 0) to mid-calf, laced up the front (black laces and eyelets, 5); a toecap
    seam, a stacked heel and a thick lugged sole (5)."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        bb = boot_hull(side)
        an, kn = J["ankle_" + side], J["knee_" + side]
        wrinkle = lambda P: F(0.0022) * np.sin(P[:, 2] * F(85)) * smoothstep(0.24, 0.13, P[:, 2]) + F(0.001) * NOISE(P * F(30))
        lo, hi = an - v3((0.2, 0.3, 0.2)), kn + v3((0.2, 0.2, 0.1))
        fd.add(Inter(Shell(bb, 0.016, 0.014, pad=0.06, disp=wrinkle, disp_amp=0.003), Func(lambda P: P[:, 2] - boot_top(P), lo, hi), 0.004), 0.0)
        def collar(P):
            t = boot_top(P)
            return np.abs(P[:, 2] - (t - F(0.008))) - F(0.01)
        fd.add(Inter(Shell(bb, 0.022, 0.012, pad=0.06), Func(collar, lo, hi), 0.003), 0.004)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        lug = lambda P: F(0.0025) * np.abs(np.sin(P[:, 1] * F(160)))
        fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.09)), (0.072, 0.16, 0.016), 0.009, R=Rz, disp=lug, disp_amp=0.003), 0.006, 5)
        fd.add(RoundBox(an + fwd * -0.012 + v3((0, 0, -0.08)), (0.06, 0.054, 0.024), 0.008, R=Rz), 0.006, 5)
        fd.sub(Torus(an + fwd * 0.155 + v3((0, 0, -0.065)), 0.062, 0.0022, R=rot_from_axes(z_axis=fwd + v3((0, 0, 0.6)))), 0.0015)
        pairs = lace_points(side)
        for i, (pa, pb) in enumerate(pairs):
            for p in (pa, pb):
                fd.add(Torus(p, 0.0055, 0.0022, R=rot_from_axes(z_axis=(0, -1, 0))), 0.002, 5)
            if i + 1 < len(pairs):
                qa, qb = pairs[i + 1]
                fd.add(RoundCone(pa + v3((0, -0.002, 0)), qb + v3((0, -0.002, 0)), 0.0028, 0.0028), 0.002, 5)
                fd.add(RoundCone(pb + v3((0, -0.003, 0)), qa + v3((0, -0.003, 0)), 0.0028, 0.0028), 0.002, 5)
    return fd


BELT_Z, BELT_W = 0.893, 0.026


def belt_field():
    """A coyote rigger's belt (uniform cloth, label 0) round her hips under the carrier, its black (8) cobra buckle at the
    front, black keepers."""
    fd = Field("Belt")
    hips = Field("Hips")
    tp = torso_prims()
    hips.add(tp[4][0], 0.0)
    hips.add(tp[5][0], tp[5][1])
    def belt(P):
        d = hips.eval(P, margin=0.12)
        return np.maximum(np.abs(d - F(0.034)) - F(0.008), np.abs(P[:, 2] - F(BELT_Z)) - F(BELT_W))
    fd.add(Func(belt, (-0.42, -0.4, 0.8), (0.42, 0.45, 1.0), disp=lambda P: F(0.0008) * NOISE(P * F(40)), disp_amp=0.001), 0.0)
    h, ok = ray_hit(Func(lambda P: hips.eval(P, margin=0.12) - F(0.042), (-1, -1, 0.6), (1, 1, 1.2)), [v3((0, -0.6, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    bc = h[0] if ok[0] else v3((0, -0.2, BELT_Z))
    R = np.stack([v3((1, 0, 0)), v3((0, -1, 0)), v3((0, 0, 1))], 1)
    fd.add(RoundBox(bc + v3((0, -0.006, 0)), (0.038, 0.009, 0.026), 0.006, R=R), 0.003, 8)
    fd.add(RoundBox(bc + v3((0, -0.013, 0)), (0.008, 0.006, 0.02), 0.003, R=R), 0.002, 8)
    for x in (-0.13, 0.13):
        h, ok = ray_hit(Func(lambda P: hips.eval(P, margin=0.12) - F(0.044), (-1, -1, 0.6), (1, 1, 1.2)), [v3((x, -0.6, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            fd.add(RoundBox(h[0], (0.01, 0.006, 0.03), 0.004), 0.002, 8)
    return fd


# ======================================================================================= gloves
def gloves_field():
    """Black gloves (armory leather, label 5) over her fists, a padded cuff at each wrist."""
    fd = Field("Gloves")
    for side in ("R", "L"):
        hf = Field("Hand" + side)
        hand(hf, side)
        fd.add(Shell(hf, 0.005, 0.009, pad=0.05, disp=lambda P: F(0.0008) * NOISE(P * F(60)), disp_amp=0.001), 0.003, 5)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        arm = Field("Fore" + side)
        arm.add(_forearm(side), 0.0)
        hand(arm, side)
        def cuff(P, wr=wr, ax=ax):
            s = (P - wr.astype(F)) @ ax.astype(F)
            return np.abs(s + F(0.008)) - F(0.03)
        fd.add(Inter(Shell(arm, 0.012, 0.014, pad=0.06), Func(cuff, wr - 0.2, wr + 0.2), 0.004), 0.006, 5)
    return fd


# ======================================================================================= the rifle
GUN_G0 = v3((-0.3, -0.52, 0.92))          # rest: the pistol grip's middle (floating before her right hip) ...
GUN_A0 = v3((0.0, -1.0, 0.0))             # ... the barrel pointing ahead
GUN_U0 = v3((0.0, 0.0, 1.0))
GUN_S0 = np.cross(GUN_A0, GUN_U0)         # (her right: the rifle's right side as she holds it)
BAR_H = 0.11                              # the bore's height above the grip's middle
MUZZLE_U = 0.665
BUTT_U = -0.335                           # the butt pad's face
FORE_U = 0.36                             # the vertical foregrip
OPTIC_U, OPTIC_H = 0.05, 0.19             # the red dot's tube: its middle (along), its axis' height
GUN_SCALE = 1.0


def _gr(u, v=0.0, h=0.0):
    return GUN_G0 + GUN_A0 * u + GUN_S0 * v + GUN_U0 * h


def gl(u, v=0.0, h=0.0):
    return GUN_G0 + (GUN_A0 * u + GUN_S0 * v + GUN_U0 * h) * GUN_SCALE


def grip_axis():
    """The pistol grip's axis (from its foot up toward the receiver: raked, the foot further back)."""
    return norm(GUN_U0 * 0.93 + GUN_A0 * 0.36)


def fore_axis():
    """The vertical foregrip's axis (from its foot up to the handguard)."""
    return norm(GUN_U0 * 0.98 + GUN_A0 * 0.08)


def muzzle():
    return gl(MUZZLE_U, 0.0, BAR_H)


def rifle_field():
    """Black polymer (armory's leather/grip colour, label 5): the stock, its butt pad, the pistol grip, the magazine, the
    handguard's rail covers and the vertical foregrip; gunmetal (dark iron, 8): the receivers, the buffer tube, the top
    rail, the handguard, the barrel, the flash hider, the trigger and its guard, the optic."""
    fd = Field("Rifle")
    A, U, S = GUN_A0, GUN_U0, GUN_S0
    Rg = np.stack([S, A, U], 1)
    tex = lambda P: F(0.0005) * NOISE(P * F(90))
    # the pistol grip
    ga = grip_axis()
    gs = norm(np.cross(ga, S))
    Rgr = np.stack([S, gs, ga], 1)
    fd.add(RoundBox(_gr(0.0, 0.0, -0.004), (0.017, 0.024, 0.066), 0.014, R=Rgr, disp=tex, disp_amp=0.001), 0.0, 5)
    fd.add(RoundBox(_gr(0.0, 0.0, -0.004) + gs * 0.022 - ga * 0.01, (0.018, 0.006, 0.05), 0.005, R=Rgr), 0.008, 5)   # finger swell
    # the lower receiver, the magazine well, the trigger guard and trigger
    fd.add(RoundBox(_gr(0.06, 0.0, 0.07), (0.022, 0.115, 0.03), 0.01, R=Rg), 0.01, 8)
    fd.add(RoundBox(_gr(0.145, 0.0, 0.05), (0.024, 0.04, 0.04), 0.01, R=Rg), 0.008, 8)
    fd.add(Chain([_gr(0.025, 0.0, 0.042), _gr(0.03, 0.0, 0.012), _gr(0.1, 0.0, 0.01), _gr(0.112, 0.0, 0.04)], [0.0055] * 4, k=0.003), 0.003, 8)
    fd.add(RoundCone(_gr(0.06, 0.0, 0.045), _gr(0.066, 0.0, 0.022), 0.005, 0.004), 0.002, 8)
    # the magazine: a curved polymer box, sweeping forward as it drops
    pts = []
    for i in range(5):
        t = i / 4.0
        pts.append((0.146 + 0.06 * t * t, 0.02 - 0.17 * t, -0.2 * t))
    for (u0, h0, a0), (u1, h1, a1) in zip(pts, pts[1:]):
        c = _gr((u0 + u1) / 2, 0.0, (h0 + h1) / 2)
        ang = (a0 + a1) / 2
        R = Rg @ euler(ang, 0, 0)
        fd.add(RoundBox(c, (0.018, 0.034, 0.026), 0.008, R=R), 0.01, 5)
    fd.add(RoundBox(_gr(0.212, 0.0, -0.152), (0.021, 0.04, 0.012), 0.008, R=Rg @ euler(-0.2, 0, 0)), 0.006, 5)   # its base plate
    # the upper receiver, the charging handle, the ejection port's cover
    fd.add(RoundBox(_gr(0.06, 0.0, 0.112), (0.024, 0.118, 0.024), 0.01, R=Rg), 0.008, 8)
    fd.add(RoundBox(_gr(-0.06, 0.0, 0.128), (0.03, 0.012, 0.008), 0.004, R=Rg), 0.004, 8)
    fd.add(RoundBox(_gr(0.05, 0.025, 0.108), (0.002, 0.04, 0.012), 0.002, R=Rg), 0.002, 8)
    # the top rail, from the receiver along the handguard (cross slots)
    fd.add(RoundBox(_gr(0.22, 0.0, 0.142), (0.014, 0.29, 0.008), 0.003, R=Rg), 0.004, 8)
    for k in range(26):
        u = -0.05 + 0.022 * k
        fd.sub(RoundBox(_gr(u, 0.0, 0.151), (0.02, 0.004, 0.004), 0.001, R=Rg), 0.001)
    # the buffer tube and the collapsible stock with its butt pad
    fd.add(RoundCone(_gr(-0.06, 0.0, 0.106), _gr(-0.26, 0.0, 0.106), 0.017, 0.017), 0.006, 8)
    fd.add(RoundBox(_gr(-0.245, 0.0, 0.102), (0.023, 0.078, 0.032), 0.012, R=Rg), 0.008, 5)
    fd.add(RoundBox(_gr(-0.25, 0.0, 0.133), (0.02, 0.06, 0.006), 0.004, R=Rg), 0.006, 5)                     # the cheek rest
    fd.add(RoundBox(_gr(-0.29, 0.0, 0.055), (0.021, 0.036, 0.062), 0.012, R=Rg @ euler(-0.15, 0, 0)), 0.012, 5)
    fd.add(RoundBox(_gr(-0.327, 0.0, 0.07), (0.025, 0.01, 0.085), 0.008, R=Rg), 0.006, 5)                      # the butt pad
    fd.sub(RoundBox(_gr(-0.27, 0.0, 0.03), (0.04, 0.02, 0.012), 0.006, R=Rg @ euler(-0.5, 0, 0)), 0.004)       # (the stock's cut-out)
    # the handguard: a long octagonal tube round the barrel, slots along its sides and underneath
    fd.add(RoundBox(_gr(0.35, 0.0, BAR_H), (0.03, 0.17, 0.03), 0.013, R=Rg), 0.006, 8)
    for k in range(5):
        u = 0.24 + 0.05 * k
        for sv in (-1, 1):
            fd.sub(RoundBox(_gr(u, sv * 0.03, BAR_H - 0.004), (0.006, 0.016, 0.006), 0.004, R=Rg), 0.002)
    fd.add(RoundBox(_gr(0.43, 0.0, BAR_H - 0.026), (0.02, 0.06, 0.008), 0.004, R=Rg), 0.004, 5)              # a rail cover
    # the vertical foregrip
    fa = fore_axis()
    fd.add(RoundCone(_gr(FORE_U, 0.0, BAR_H - 0.03) - fa * 0.115, _gr(FORE_U, 0.0, BAR_H - 0.03), 0.02, 0.017, disp=tex, disp_amp=0.001), 0.006, 5)
    fd.add(Sphere(_gr(FORE_U, 0.0, BAR_H - 0.03) - fa * 0.115, 0.021), 0.006, 5)
    # the barrel, its gas block, the flash hider
    fd.add(RoundCone(_gr(0.5, 0.0, BAR_H), _gr(0.61, 0.0, BAR_H), 0.012, 0.011), 0.004, 8)
    fd.add(RoundBox(_gr(0.535, 0.0, BAR_H + 0.004), (0.016, 0.014, 0.018), 0.005, R=Rg), 0.004, 8)
    fd.add(Cylinder(_gr(0.635, 0.0, BAR_H), 0.0165, 0.06, rr=0.004, R=rot_from_axes(z_axis=A)), 0.004, 8)
    for k in range(4):
        ang = 2 * math.pi * k / 4 + 0.4
        o = (S * math.cos(ang) + U * math.sin(ang)) * 0.016
        fd.sub(RoundBox(_gr(0.65, 0.0, BAR_H) + o, (0.006, 0.02, 0.006), 0.003, R=rot_from_axes(z_axis=o, y_axis=A)), 0.002)
    fd.sub(Cylinder(_gr(MUZZLE_U, 0.0, BAR_H), 0.008, 0.05, R=rot_from_axes(z_axis=A)), 0.002)
    # flip-up sights at the rail's ends (folded)
    fd.add(RoundBox(_gr(-0.025, 0.0, 0.158), (0.012, 0.014, 0.01), 0.004, R=Rg), 0.003, 8)
    fd.add(RoundBox(_gr(0.49, 0.0, 0.158), (0.01, 0.014, 0.01), 0.004, R=Rg), 0.003, 8)
    # the red-dot sight: its mount on the rail, the tube, its hoods, the turrets
    oc = _gr(OPTIC_U, 0.0, OPTIC_H)
    Ra = rot_from_axes(z_axis=A)
    fd.add(RoundBox(_gr(OPTIC_U, 0.0, 0.16), (0.018, 0.03, 0.012), 0.005, R=Rg), 0.004, 8)
    fd.add(Cylinder(oc, 0.026, 0.09, rr=0.008, R=Ra), 0.006, 8)
    fd.sub(Cylinder(oc + A * 0.047, 0.019, 0.016, rr=0.002, R=Ra), 0.002)
    fd.sub(Cylinder(oc - A * 0.047, 0.019, 0.016, rr=0.002, R=Ra), 0.002)
    fd.add(Cylinder(oc + U * 0.03, 0.01, 0.014, rr=0.003), 0.003, 8)
    fd.add(Cylinder(oc + S * 0.03, 0.01, 0.014, rr=0.003, R=rot_from_axes(z_axis=S)), 0.003, 8)
    return ScaledField(fd, GUN_G0, GUN_SCALE)


def optic_field():
    """The red dot's lenses: the front one coated red, the back one a dark glass."""
    fd = Field("Optic")
    oc = _gr(OPTIC_U, 0.0, OPTIC_H)
    Ra = rot_from_axes(z_axis=GUN_A0)
    fd.add(Cylinder(oc + GUN_A0 * 0.04, 0.0205, 0.008, rr=0.002, R=Ra), 0.0, 8)
    fd.add(Cylinder(oc - GUN_A0 * 0.04, 0.0205, 0.008, rr=0.002, R=Ra), 0.0)
    return ScaledField(fd, GUN_G0, GUN_SCALE)


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.232, 1.622)), 0.045, 0.4)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.085, -0.15, 1.6)), 0.06, 0.45), (J["elbow_" + sd] + v3((0, 0.022, 0)), 0.05, 0.25)]
    return pts


# ======================================================================================= build config
GLB_NAME = "maya"
ROOT_NAME = "HeroMayaHQ"
TEX_PREFIX = "hero"
MAT_NAME = "MayaMat"
MESH_NAME = "Maya"
BASE_MODULE = "maya_base"
ANIM_MODULE = "anim_maya"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Helmet", "Lens", "Headset", "Shirt", "Carrier", "Radio", "Trousers", "Pads",
         "Boots", "Belt", "Gloves", "Rifle", "Optic", "Smoke"]
REGION_PARTS = ("Skin", "Helmet", "Headset", "Carrier", "Radio", "Pads", "Boots", "Belt", "Gloves", "Rifle", "Optic", "Smoke")
OLIVE = (0.4, 0.42, 0.28)                  # the task force's olive drab
COYOTE = (0.6, 0.5, 0.36)                  # webbing and plate carriers
RED = (0.78, 0.1, 0.08)                    # the unit patch
WHITE = (0.93, 0.92, 0.88)
BLACK = (0.07, 0.07, 0.075)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_MayaSkin", "base": (0.44, 0.27, 0.18), "ruddy": (0.5, 0.27, 0.18), "lips": (0.33, 0.15, 0.13),
                      "nails": (0.62, 0.46, 0.38), "brow": ((0.04, 0.03, 0.025), (0.1, 0.07, 0.05)),
                      "extra": ((LASH, (0.03, 0.02, 0.02), 0.5),)}),
    "Hair": ("hair", {"name": "HQ_MayaHair", "base": (0.08, 0.06, 0.05), "hi": (0.24, 0.18, 0.14), "low": (0.03, 0.02, 0.02),
                      "streak": (0.05, 0.035, 0.03), "tint": (0.1, 0.07, 0.05)}),
    "Helmet": ("uniform", {"name": "HQ_MayaHelmet", "base": COYOTE, "black": BLACK}),
    "Lens": ("vials", {"name": "HQ_MayaLens", "glass": (0.3, 0.36, 0.4)}),
    "Headset": ("armory", {"name": "HQ_MayaKit", "grip": (0.09, 0.09, 0.09)}),
    "Shirt": ("uniform", {"name": "HQ_MayaFatigues", "base": OLIVE}),
    "Carrier": ("uniform", {"name": "HQ_MayaCarrier", "base": COYOTE, "facing": RED, "buff": WHITE, "black": BLACK}),
    "Radio": ("uniform", {"name": "HQ_MayaCarrier", "base": COYOTE, "facing": RED, "buff": WHITE, "black": BLACK}),
    "Trousers": ("uniform", {"name": "HQ_MayaFatigues", "base": OLIVE}),
    "Pads": ("armory", {"name": "HQ_MayaKit", "grip": (0.09, 0.09, 0.09)}),
    "Boots": ("leather_dyed", {"name": "HQ_MayaBoots", "base": (0.09, 0.085, 0.08), "dyed": (0.045, 0.045, 0.045),
                               "worn_c": (0.32, 0.31, 0.3)}),
    "Belt": ("uniform", {"name": "HQ_MayaCarrier", "base": COYOTE, "facing": RED, "buff": WHITE, "black": BLACK}),
    "Gloves": ("armory", {"name": "HQ_MayaKit", "grip": (0.09, 0.09, 0.09)}),
    "Rifle": ("armory", {"name": "HQ_MayaRifle", "grip": (0.08, 0.08, 0.085)}),
    "Optic": ("vials", {"name": "HQ_MayaOptic", "glass": (0.16, 0.2, 0.24)}),
    "Smoke": ("fieldgun", {"name": "HQ_MayaSmoke", "olive": (0.42, 0.45, 0.36), "red": (0.85, 0.12, 0.08)}),
}
LOW_TARGETS = {"Skin": 6000, "Teeth": 100, "Hair": 900, "Helmet": 2400, "Lens": 150, "Headset": 700, "Shirt": 2000,
               "Carrier": 3200, "Radio": 700, "Trousers": 1300, "Pads": 400, "Boots": 1300, "Belt": 500, "Gloves": 900,
               "Rifle": 3200, "Optic": 80, "Smoke": 300}
AO_EXCLUDE = ["Rifle", "Optic", "Smoke", "Lens"]
BAKE_APART = (["Rifle", "Optic", "Smoke"], (3.0, 0.0, 0.0))     # (the rifle floats before her, the grenade sits in its pouch)


def prop_bones():
    """The rifle rides a parentless bone (every clip poses it in world space, anim_maya.py); the smoke grenade a child of
    her chest (it sits in its pouch; the Ability poses it in world space while she throws it)."""
    b, ax = nade_rest()
    return [("rifle", GUN_G0, muzzle(), None),
            ("smoke", b, b + ax * NADE_L, "chest")]


WC_BONES = TORSO | {"clavicle.R", "clavicle.L"}
COAT_BONES = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}


def shirt_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=COAT_BONES, caps=None)


def boots_weights(ob, skin_ob, arm):
    _isla_boots_weights(ob, skin_ob, arm)


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Helmet": ("rigid", "head"),
        "Lens": ("rigid", "head"), "Headset": ("rigid", "head"),
        "Shirt": ("custom", shirt_weights),
        "Carrier": ("transfer", WC_BONES, None),
        "Radio": ("rigid", "chest"),
        "Trousers": ("transfer", {"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Pads": ("transfer", {"thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Boots": ("custom", boots_weights),
        "Belt": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.25, "thigh.L": 0.25}),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Rifle": ("rigid", "rifle"), "Optic": ("rigid", "rifle"), "Smoke": ("rigid", "smoke"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Rifle", "Helmet", "Carrier", "Smoke"):
        return 1.1
    if part in ("Trousers", "Pads", "Belt"):
        return 0.7
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Helmet", helmet_field(), 0.0022 if fine else 0.0032),
        ("Lens", lens_field(), 0.0016 if fine else 0.0024),
        ("Headset", headset_field(), 0.0018 if fine else 0.0026),
        ("Shirt", blouse_field(), 0.0024 if fine else 0.0034),
        ("Carrier", carrier_field(), 0.0024 if fine else 0.0034),
        ("Radio", radio_field(), 0.0016 if fine else 0.0024),
        ("Trousers", trousers_field(), 0.0028 if fine else 0.0038),
        ("Pads", pads_field(), 0.0022 if fine else 0.003),
        ("Boots", boots_field(), 0.0018 if fine else 0.0026),
        ("Belt", belt_field(), 0.002 if fine else 0.003),
        ("Gloves", gloves_field(), 0.0016 if fine else 0.0024),
        ("Rifle", rifle_field(), 0.0016 if fine else 0.0024),
        ("Optic", optic_field(), 0.0012 if fine else 0.0018),
        ("Smoke", smoke_field(), 0.0014 if fine else 0.002),
    ]
