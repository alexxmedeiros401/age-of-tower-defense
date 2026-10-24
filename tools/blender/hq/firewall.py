"""The Firewall (HQ tower, The Data Center, Control lineage): a Resistance hacker and the jury-rigged hacking rig he
runs. Rest pose: he stands in an A-pose facing -Y (the robots), feet at z = 0; the rig's server core and its mast stand
behind him on his left (+X, +Y), the crates with his keyboard and laptop before him on his right (-X, -Y).

Him: the Spear Guard's young, athletic body (spear.py), built as the Cryo technician (cryo.py) with his own face: young
and sharp, a lean oval face with a defined jaw and a neat chin, warm brown skin, straight dark brows set level and a
little low over keen dark eyes, a straight nose, a closed mouth with a sly half smile (his left corner up). Black hair:
faded close at the sides and the back, a short thick textured top. A black over-ear headset (a padded band over the
crown, big round cups with amber rings, a boom mic before his mouth on the left).
A charcoal hoodie, its hood down (a thick roll round his neck, the hood's body lying on his upper back), drawstrings with
steel tips hanging over his chest, a ribbed hem and a pouch pocket below the vest, its sleeves down into his gloves; an
amber armband round his left upper arm. A gunmetal armour vest (front and back plates on black straps, an amber chevron
sprayed on the front plate and a slash on the back, bare-metal scratches); a black utility belt with two pouches.
Smoky teal-grey trousers with black knee pads and a thigh pocket; black boots. Black fingerless gloves (his fingers bare
for the keys), gunmetal knuckle plates. On his left forearm the wrist rig: a white robot forearm plate, salvaged, strapped
on and slashed with amber paint, a small amber readout (`WristGlow`).

The rig (bones `machine`, `mast`, `core`, `flare`): a salvaged robot server core (white casing with panel lines and
dents, drive slots, its robot lights swapped for amber: `Lights`, a round amber eye and two strips; a big amber chevron
sprayed on its side) on a gunmetal skid; from its top a gunmetal mast (pipe sections, clamps, a cable taped round it,
a whip antenna clamped alongside) up to the emitter ring: a gunmetal ring on spokes carrying eight emitter cans facing
outward, their lenses glowing amber (`Emitters`), round a glowing amber node (`Node`, on `core`: the game's hack pulse
leaves its centre) in a cage of prongs; `Flare` (a ring of amber light round the emitters, on `flare`) is scaled to
nothing but at the pulse.

The workstation (on `machine`): two stacked ammo crates (teal-grey, amber stencils, black latches), on top a black
keyboard (keys, a big amber Enter key on its right end, which he slams) and a cracked laptop (gunmetal, an amber
Resistance chevron on its lid's back, its screen glowing amber: `Screen`, cracked across); bundles of cables from the
laptop down the crates and over the floor to the server core.

Painted labels (material mats.modern_kit): 0 base (cloth: charcoal; armour: gunmetal; machine: robot white), 5 black,
6 red, 7 robot white, 8 teal-grey (cloth, crates) or charcoal (armour), 9 gunmetal, 10 steel, 11 glass, 12 rubber,
13 amber paint."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
import emp as em
from spear import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R,
                   eye_c, smoothstep, hand_frame, HAND_S, foot, torso_prims, traps, neck_prim, deltoid, eyes_field,
                   TORSO, TORSO_Z, torso_bones)
from emp import arm_prims, leg_prims, shirt_base, _arm_s, _neck_open, legs_base, foot_hull, vest_base, _octagon

IRIS = ((0.12, 0.075, 0.04), (0.3, 0.19, 0.1))          # keen dark-brown eyes
Z = v3((0.0, 0.0, 1.0))
# labels (mats.modern_kit)
BASE, BLACK, RED, WHITE, TEAL, GUN, STEEL, GLASS, RUBBER, AMBER = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13
CHAR = TEAL                                               # (the armour's material makes label 8 charcoal)


# ======================================================================================= hands (typing)
CURLS = {"R": (0.5, 0.78, 0.5), "L": (0.5, 0.78, 0.5)}    # both hands loosely curled over the keys


def fist_center(side):
    """The palm's middle (where the hand is placed on the keys)."""
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.1 * HAND_S + n * 0.03


def finger_points(side, s=HAND_S):
    """The four fingers' joints (pts per finger) and the thumb's (tb, p1, p2)."""
    wr, f, n, t = hand_frame(side)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.043, 0.0145, -0.0145, -0.043)
    lens = (0.96, 1.02, 0.96, 0.8)
    fingers = []
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.8)
        pts = [p]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j]) @ d
            p = p + d * seglen[j]
            pts.append(p)
        fingers.append(pts)
    tb = wr + f * 0.045 * s + t * 0.051 * s + n * 0.011
    d1 = norm(f * 0.5 + t * 0.75 + n * 0.3)
    d2 = norm(f * 0.75 + t * 0.25 + n * 0.55)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    return fingers, (tb, p1, p2)


def hand(fd, side, s=HAND_S):
    """A young hand, the fingers loosely curled (on the keys), the thumb relaxed toward the space bar."""
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.062, 0.03, 0.066)) * s, 0.027 * s, R=Rp), 0.028, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.034, 0.028, 0.05)) * s, R=Rp), 0.019, SKIN)
    fingers, (tb, p1, p2) = finger_points(side, s)
    curl_ax = norm(np.cross(f, n))
    for i, pts in enumerate(fingers):
        r0 = 0.0195 * s * (0.92 if i == 3 else 1.0)
        rads = [r0, r0 * 0.92, r0 * 0.84, r0 * 0.78]
        fd.add(Chain(pts, rads, k=0.006), 0.011, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.015 * s), 0.009, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.011, (0.012, 0.007, 0.015), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    fd.add(Chain([tb, p1, p2], [0.024 * s, 0.021 * s, 0.018 * s], k=0.008), 0.017, SKIN)


# ======================================================================================= head
def face_mask(P):
    """His jaw and chin (design coordinates): the faintest shadow of a shave."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.57) + F(0.025) * smoothstep(0.06, 0.15, ax)
    return np.maximum(np.maximum(z - top, F(1.45) - z), y - F(0.02))


def mouth_slot():
    """A closed mouth, its left corner (+x) drawn up: a sly half smile."""
    return [hp((-0.05, -0.171, 1.561)), hp((-0.026, -0.192, 1.5525)), hp((0.0, -0.199, 1.551)), hp((0.028, -0.192, 1.555)),
            hp((0.056, -0.168, 1.569))]


def head(fd):
    """Young and sharp: a lean oval face, a defined jaw and a neat chin, high cheekbones, straight brows set level and a
    little low (keen, not cross), open eyes, a straight nose, a closed mouth with a sly half smile."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.055, 1.59), (0.124, 0.126, 0.122)), 0.07, SKIN)                           # a defined jaw
    fd.add(E((0, -0.136, 1.5), (0.07, 0.064, 0.062)), 0.05, SKIN)                             # a neat chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.108, -0.122, 1.636), 0.044), 0.05, SKIN)                               # high cheekbones
        fd.add(S((sx * 0.09, -0.142, 1.598), 0.031), 0.04, SKIN)                                # lean cheeks
        fd.add(S((sx * 0.117, -0.05, 1.56), 0.045), 0.05, SKIN)                                 # jaw corners
        pts = [hp((sx * 0.15, -0.055, 1.742)), hp((sx * 0.114, -0.13, 1.75)), hp((sx * 0.06, -0.172, 1.748)), hp((0.0, -0.182, 1.746))]
        fd.add(Chain(pts, [hr(0.01), hr(0.015), hr(0.017), hr(0.017)], k=hr(0.02)), hr(0.03), SKIN)     # brow ridge
    fd.paint(Func(face_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # straight brows with a gentle arch, set level over the eyes (keen, not cross: their inner ends not drawn down)
    for sx in (-1, 1):
        pts = [hp((sx * 0.028, -0.207, 1.772)), hp((sx * 0.066, -0.201, 1.787)), hp((sx * 0.107, -0.182, 1.79)), hp((sx * 0.147, -0.143, 1.775))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.0068), hr(0.0078), hr(0.0068), hr(0.0038)], k=hr(0.007)), hr(0.009), BROW)
        fd.paint(Chain(pts, [hr(0.012), hr(0.0135), hr(0.012), hr(0.007)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0066)), Plane(ec + v3((0, 0, hr(0.0285))), (sx * 0.16, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0052)), Plane(ec + v3((0, 0, -hr(0.025))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.0075)), Plane(ec + v3((0, 0, hr(0.027))), (sx * 0.16, 0.06, -1.0)), hr(0.002)), LASH)
    # a straight nose
    fd.add(RoundCone(hp((0, -0.186, 1.726)), hp((0, -0.229, 1.636)), hr(0.012), hr(0.017)), hr(0.016), SKIN)
    fd.add(S((0, -0.23, 1.618), 0.021), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.025, -0.21, 1.606), 0.017), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.015, -0.229, 1.594)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the mouth: closed, its left corner drawn up
    slot = mouth_slot()
    fd.sub(Chain(slot, [hr(0.0024), hr(0.003), hr(0.0033), hr(0.003), hr(0.0026)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.0032)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.048, -0.169, 1.5635), (-0.026, -0.186, 1.5575), (0.0, -0.191, 1.558), (0.028, -0.186, 1.5605), (0.054, -0.166, 1.5725)]
    lo_lip = [(-0.036, -0.174, 1.548), (-0.02, -0.186, 1.539), (0, -0.19, 1.537), (0.02, -0.186, 1.54), (0.04, -0.172, 1.551)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0045), hr(0.005), hr(0.0045), hr(0.003)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0058), hr(0.0062), hr(0.0058), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(S((0.064, -0.159, 1.578), 0.008), hr(0.006), SKIN)                                   # the smile's lifted corner
    fd.sub(S((0.068, -0.163, 1.574), 0.0045), hr(0.004))                                        # and its dimple
    fd.add(S((-0.06, -0.162, 1.566), 0.007), hr(0.006), SKIN)
    # ears: a rim, a hollow, a lobe (under the headset's cups)
    for sx in (-1, 1):
        R = euler(0, sx * 0.25, sx * -0.35)
        c = hp((sx * 0.157, 0.035, 1.66))
        fd.add(Ellipsoid(c, v3((0.02, 0.04, 0.052)) * HS, R=R), hr(0.02), SKIN)
        o = norm(R @ v3((sx, 0, 0)))
        fd.sub(Ellipsoid(c + o * hr(0.016) + v3((0, -0.004, -0.004)), v3((0.008, 0.022, 0.028)) * HS, R=R), hr(0.006))
        fd.add(Ellipsoid(c + v3((0, 0.002, -0.042)) + o * hr(0.004), v3((0.012, 0.016, 0.016)) * HS, R=R), hr(0.01), SKIN)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
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


def teeth_field():
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009 + 0.003, -0.178, 1.554)), v3((0.008, 0.006, 0.006)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= hair
def _head_d(P):
    """Signed distance (roughly) to the cranium's ellipsoid."""
    q = (P - HEAD_C.astype(F)) / HEAD_RAD.astype(F)
    k0 = np.sqrt((q * q).sum(1))
    k1 = np.sqrt(((q / HEAD_RAD.astype(F)) ** 2).sum(1))
    return k0 * (k0 - F(1)) / np.maximum(k1, F(1e-9))


def hair_thick(P):
    """How far the hair stands off the cranium: faded close at the sides and the back, a short thick top (a little
    fuller at the front)."""
    Q = hinv(P)
    y, z = Q[:, 1], Q[:, 2]
    top = smoothstep(1.76, 1.87, z)
    front = smoothstep(0.12, -0.12, y)
    return (F(0.004) + F(0.026) * top + F(0.008) * top * front) * F(HS)


# the hairline: its height (design z) by the angle round the head from the front (0) to the back (pi)
_HL_A = np.array([0.0, 0.5, 0.82, 1.02, 1.25, 1.36, 1.86, 2.2, math.pi])
_HL_Z = np.array([1.835, 1.85, 1.795, 1.7, 1.68, 1.74, 1.74, 1.635, 1.6])


def hair_keep(P):
    """< 0 where there is hair (above the hairline, off the face, round the ears)."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    a = np.abs(np.arctan2(x, -(y - F(0.03))))
    zl = np.interp(a, _HL_A, _HL_Z).astype(F) + F(0.003) * np.sin(x * F(70))
    d = (zl - z) * F(0.6)
    for sx in (-1, 1):                                                  # clear of the ears (the cups sit there)
        e = np.sqrt((x - F(sx * 0.16)) ** 2 + (y - F(0.03)) ** 2 + ((z - F(1.668)) * F(0.8)) ** 2)
        d = np.maximum(d, F(0.07) - e)
    return d


def hair_field():
    """Black hair (label 0): faded close at the sides, a short, thick, textured top (tight curls in lumps)."""
    fd = Field("Hair")
    lo, hi = HEAD_C - v3((0.24, 0.26, 0.17)), HEAD_C + v3((0.24, 0.26, 0.27))
    def tex(P):
        Q = hinv(P)
        top = smoothstep(1.77, 1.85, Q[:, 2])
        side = F(0.0005) * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(0.03)) * F(160) + P[:, 2] * F(40))
        curls = F(0.0032) * NOISE(P * F(55)) + F(0.0022) * NOISE(P * F(110)) + F(0.002) * NOISE(P * F(16))
        return side * (F(1) - top) + curls * top + F(0.0006) * NOISE(P * F(40))
    def fn(P):
        d = _head_d(P)
        t = hair_thick(P)
        return np.maximum(np.maximum(d - t, -d - F(0.004)), hair_keep(P))
    fd.add(Func(fn, lo, hi, disp=tex, disp_amp=0.006), 0.0)
    return fd


def hair_outer(P):
    """The hair's outer surface (as if hair were everywhere round the cranium): for laying the headset on."""
    return _head_d(P) - hair_thick(P) - F(0.004)


# ======================================================================================= the headset
BAND_Y = 0.045                               # the band's plane over his crown (world y)
CUP_D = {sx: norm(v3((sx * 1.0, 0.04, 0.12))) for sx in (-1, 1)}      # the cups' outward axes
CUP_R = 0.064


def _ear_hull():
    b = Field("EarHull")
    b.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    for sx in (-1, 1):
        R = euler(0, sx * 0.25, sx * -0.35)
        b.add(Ellipsoid(hp((sx * 0.157, 0.035, 1.66)), v3((0.02, 0.04, 0.052)) * HS, R=R), hr(0.02))
    b.add(Func(hair_outer, HEAD_C - 0.3, HEAD_C + 0.3), 0.0)
    return b


_CUP_CACHE = {}


def cup_frame(sx):
    """A cup's inner face centre (just off the ear) and its outward axis."""
    if sx in _CUP_CACHE:
        return _CUP_CACHE[sx]
    o = CUP_D[sx]
    aim = hp((sx * 0.157, 0.035, 1.664))
    h, ok = ray_hit(_ear_hull(), [aim + o * 0.3], [-o], tmax=0.35)
    c = (h[0] if ok[0] else aim + o * 0.03) + o * 0.006
    _CUP_CACHE[sx] = (c, o)
    return c, o


def band_path(n=21, lift=0.007):
    """The band's middle line over his crown (in the plane y = BAND_Y), from the right cup's top to the left's."""
    cR, _ = cup_frame(-1)
    cL, _ = cup_frame(1)
    ctr = v3((0.0, BAND_Y, float(HEAD_C[2]) - 0.02))
    pts = []
    for k in range(n):
        th = -math.pi * 0.5 + math.pi * k / (n - 1)          # -pi/2 his right, 0 the top, +pi/2 his left
        d = v3((math.sin(th), 0.0, math.cos(th)))
        ts = np.linspace(0.34, 0.0, 500)
        Q = (ctr[None, :] + ts[:, None] * d[None, :]).astype(F)
        v = hair_outer(Q)
        i = int(np.argmax(v < F(lift)))
        pts.append(v3(Q[i]))
    # the ends run down into the cups' tops
    for sx, c in ((-1, cR), (1, cL)):
        top = c + v3((0, 0, CUP_R * 0.8)) + CUP_D[sx] * 0.02
        if sx < 0:
            pts[0] = lerp(pts[0], top, 0.6)
        else:
            pts[-1] = lerp(pts[-1], top, 0.6)
    return pts


def mic_path():
    c, o = cup_frame(1)
    return [c + o * 0.03 + v3((0, -0.03, -0.035)), hp((0.155, -0.09, 1.57)), hp((0.125, -0.165, 1.54)), hp((0.088, -0.2, 1.528))]


def headset_field():
    """Black polymer (5): the padded band over his crown (a black cushion under a gunmetal spine 9), two big round
    cups over his ears (a black cushion, a black shell, an amber ring round the face 13, a steel yoke 10), a boom mic
    from the left cup to before his mouth (a black foam capsule)."""
    fd = Field("Headset")
    pts = band_path()
    nrm = [norm(p - v3((0.0, BAND_Y, float(HEAD_C[2]) - 0.02))) for p in pts]
    fd.add(Lock(pts, [0.02] * len(pts), [0.008] * len(pts), nrm, k=0.004), 0.0, BLACK)
    spine = [p + q * 0.008 for p, q in zip(pts, nrm)][1:-1]
    fd.add(Lock(spine, [0.011] * len(spine), [0.005] * len(spine), nrm[1:-1], k=0.003), 0.003, GUN)
    for sx in (-1, 1):
        c, o = cup_frame(sx)
        R = rot_from_axes(z_axis=o)
        fd.add(Cylinder(c + o * 0.011, CUP_R, 0.022, rr=0.01, R=R), 0.0, BLACK)                    # the cushion
        fd.add(Cylinder(c + o * 0.033, CUP_R - 0.004, 0.026, rr=0.012, R=R), 0.006, BLACK)        # the shell
        fd.add(Cylinder(c + o * 0.048, CUP_R - 0.022, 0.012, rr=0.005, R=R), 0.004, GUN)           # its cap
        fd.add(Torus(c + o * 0.044, CUP_R - 0.012, 0.006, R=R), 0.003, AMBER)                     # the amber ring
        # the yoke from the band's end over the cup's top
        top = c + o * 0.03 + v3((0, 0, CUP_R - 0.004))
        fd.add(Chain([top - v3((0, 0, 0.004)), top + v3((0, 0, 0.022)) - o * 0.004], [0.009, 0.009], k=0.004), 0.004, STEEL)
    mp = mic_path()
    fd.add(Chain(mp, [0.0065, 0.006, 0.0055, 0.0055], k=0.004), 0.003, BLACK)
    fd.add(Ellipsoid(mp[-1] + v3((-0.008, -0.004, 0.0)), (0.017, 0.012, 0.012), R=rot_from_axes(x_axis=norm(mp[-1] - mp[-2]))), 0.004, BLACK)
    return fd


# ======================================================================================= the hoodie
SUIT_OFF, SUIT_T = 0.018, 0.013
HEM_Z = 0.905                        # the hoodie's hem


def _sleeve_end(P):
    """> 0 past the sleeves' ends (inside the gloves' cuffs; only round each forearm)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2, L = _arm_s(P, side, 1)
        lateral = P[:, 0] * F(sx) - F(0.42)
        out = np.maximum(out, np.where((lateral > 0) & (d2 < F(0.16 ** 2)), s - F(L - 0.035), F(-1.0)))
    return out


def _waist_cut(P):
    """> 0 below the hoodie's hem (only round his body, not the arms)."""
    return np.where(np.abs(P[:, 0]) < F(0.38), F(HEM_Z) - P[:, 2], F(-1.0))


def hood_roll_path(n=23):
    """The rolled hood's middle line round his neck: from the front left, round the back, to the front right, lying on
    his traps (a ray down onto the neck hull at each angle). Returns points and the roll's radius at each."""
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    ax0 = v3((0.0, 0.07, 1.4))
    pts, rads = [], []
    for k in range(n):
        a = -2.55 + 5.1 * k / (n - 1)                     # from the front, round the back (a = pi), to the front
        back = abs(abs(a) - math.pi) < 1e-9
        u = v3((math.sin(a), -math.cos(a), 0.0))          # a = 0 would be straight ahead (-Y)
        rr = 0.148 + 0.02 * (1 - abs(math.cos(a / 2)))
        o = ax0 + u * rr + Z * 0.4
        h, ok = ray_hit(nk, [o], [v3((0, 0, -1))], tmax=0.6)
        p = h[0] if ok[0] else ax0 + u * rr
        w = 0.032 + 0.016 * (1 - abs(math.cos(a / 2))) ** 1.5         # fatter at the back
        pts.append(p + Z * (w * 0.75) + u * 0.01)
        rads.append(w)
    return pts, rads


def hoodie_field():
    """Charcoal fleece (label 0) over his torso and arms (the sleeves down into his gloves), a ribbed hem below the
    vest, a pouch pocket across the front, the hood down: a thick roll round his neck and the hood's body lying on his
    upper back; drawstrings over his chest (steel tips 10); an amber armband round his left upper arm (13)."""
    fd = Field("Hoodie")
    base = shirt_base()
    lo, hi = (-0.85, -0.42, 0.8), (0.85, 0.45, 1.56)
    fleece = lambda P: F(0.0018) * NOISE(P * F(14)) + F(0.0012) * NOISE(P * np.array([6, 6, 30], F))
    def fn(P):
        d = base.eval(P, margin=0.08)
        main = np.abs(d - F(SUIT_OFF) - fleece(P)) - F(SUIT_T * 0.5)
        return smax(main, np.maximum(np.maximum(_neck_open(P, 0.118), _sleeve_end(P)), _waist_cut(P)), 0.004)
    fd.add(Func(fn, lo, hi), 0.0, BASE)
    # the ribbed hem
    def hem(P):
        d = base.eval(P, margin=0.08)
        rib = F(0.0012) * np.sin(np.arctan2(P[:, 0], P[:, 1]) * F(90))
        sh = np.abs(d - F(SUIT_OFF + 0.006) - rib) - F(0.009)
        band = np.abs(P[:, 2] - F(HEM_Z + 0.022)) - F(0.022)
        return np.maximum(np.maximum(sh, band), np.abs(P[:, 0]) - F(0.36))
    fd.add(Func(hem, (-0.45, -0.4, 0.85), (0.45, 0.42, 0.98)), 0.004, BASE)
    # the pouch pocket across the front (below the vest)
    def pocket(P):
        d = base.eval(P, margin=0.08)
        sh = np.abs(d - F(SUIT_OFF + SUIT_T * 0.5 + 0.004)) - F(0.005)
        x, z = P[:, 0], P[:, 2]
        top = F(1.065) - F(0.25) * np.abs(x)
        reg = np.maximum(np.maximum(np.abs(x) - F(0.16) - F(0.15) * (F(1.07) - z), z - top), F(HEM_Z + 0.045) - z)
        return np.maximum(np.maximum(sh, reg), P[:, 1] + F(0.05))
    fd.add(Func(pocket, (-0.35, -0.4, 0.9), (0.35, 0.1, 1.1)), 0.003, BASE)
    # the rolled hood round his neck, the hood's body on his upper back
    pts, rads = hood_roll_path()
    roll = Chain(pts, rads, k=0.02, disp=lambda P: F(0.003) * NOISE(P * F(18)) + F(0.0015) * NOISE(P * F(45)), disp_amp=0.005)
    fd.add(roll, 0.012, BASE)
    vo = vest_outer()
    h, ok = ray_hit(vo, [v3((0.0, 0.8, 1.36))], [v3((0, -1, 0))], tmax=0.8)
    bc = (h[0] if ok[0] else v3((0.0, 0.3, 1.36))) + v3((0, 0.035, 0.0))
    sack = Ellipsoid(bc + v3((0, 0.0, -0.01)), (0.15, 0.05, 0.12), R=euler(0.35, 0, 0),
                     disp=lambda P: F(0.006) * NOISE(P * F(12)) + F(0.002) * NOISE(P * F(40)), disp_amp=0.008)
    fd.add(sack, 0.03, BASE)
    fd.sub(Ellipsoid(bc + v3((0, 0.045, 0.05)), (0.09, 0.02, 0.05), R=euler(0.35, 0, 0)), 0.02)       # its fold
    # drawstrings over his chest
    for sx in (-1, 1):
        x0 = sx * 0.042
        line = []
        for k, z in enumerate((1.4, 1.33, 1.27, 1.215)):
            hh, ok2 = ray_hit(vo, [v3((x0 + sx * 0.006 * k, -0.6, z))], [v3((0, 1, 0))], tmax=0.6)
            p = hh[0] if ok2[0] else v3((x0, -0.2, z))
            line.append(p + v3((0, -0.007, 0)))
        line[0] = line[0] + v3((0, 0.01, 0.0))
        fd.add(Chain(line, [0.0065] * len(line), k=0.004), 0.004, BLACK)
        fd.add(RoundCone(line[-1], line[-1] + v3((0, -0.004, -0.032)), 0.0075, 0.0068), 0.002, STEEL)
    # the amber armband round his left upper arm
    sh, el = J["shoulder_L"], J["elbow_L"]
    ua = norm(el - sh)
    ac = sh + ua * 0.2
    def band(P):
        s = (P - ac.astype(F)) @ ua.astype(F)
        return np.maximum(np.abs(base.eval(P, margin=0.08) - F(SUIT_OFF + SUIT_T + 0.004)) - F(0.006), np.abs(s) - F(0.032))
    fd.add(Func(band, ac - 0.2, ac + 0.2), 0.004, AMBER)
    return fd


# ======================================================================================= the armour vest and belt
RIG_OFF, RIG_T = 0.044, 0.02


def rig_keep(P):
    """< 0 on the vest: the front and back plates (shoulders cut in), side straps, two shoulder straps; never round his
    neck."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    top_f = F(1.33) - F(1.1) * np.clip(ax - F(0.09), 0, None) * smoothstep(0.08, 0.2, ax)
    top_b = F(1.36) - F(1.0) * np.clip(ax - F(0.1), 0, None) * smoothstep(0.08, 0.2, ax)
    front = y < F(0.06)
    top = np.where(front, top_f, top_b)
    bot = np.where(front, F(1.07) - F(0.25) * ax * ax, F(1.04))
    plates = np.maximum(np.maximum(ax - F(0.21), z - top), bot - z)
    side = np.maximum(np.abs(z - F(1.12)) - F(0.03), F(0.15) - ax)
    straps = np.maximum(np.maximum(F(0.105) - ax, ax - F(0.185)), F(1.2) - z)
    keep = np.minimum(np.minimum(plates, side), straps)
    return np.maximum(keep, _neck_open(P, 0.135))


def vest_outer():
    vb = vest_base()
    return Func(lambda P: vb.eval(P, margin=0.12) - F(RIG_OFF + RIG_T * 0.5 + 0.001), (-1, -1, 0.6), (1, 1, 1.8))


def chevron(u, v, w=0.024, arm=0.075):
    """A chevron (a V pointing down) in a plane's (u across, v up) coordinates, centred on (0, 0): < 0 inside."""
    au = np.abs(u)
    d = np.abs((v + F(0.03)) - au * F(1.0)) * F(0.7071) - F(w * 0.5)
    return np.maximum(d, au - F(arm))


def vest_field():
    """Gunmetal plates (label 0 in the armour's material) over the hoodie: the front plate (an amber chevron sprayed on
    its left 13, bare-metal scratches 10, a charcoal band across its foot 8), the back plate (a big amber slash), black
    side and shoulder straps (5); a black utility belt over the hoodie's hem with a steel buckle and two pouches."""
    fd = Field("Vest")
    base = vest_base()
    lo, hi = (-0.6, -0.5, 0.85), (0.6, 0.55, 1.62)
    def fn(P):
        d = base.eval(P, margin=0.12)
        ax = np.abs(P[:, 0])
        plate = smoothstep(0.23, 0.17, ax)
        off = F(RIG_OFF) - F(0.014) * (F(1) - plate)
        sh = np.abs(d - off) - F(RIG_T * 0.5) + F(0.007) * (F(1) - plate)
        return smax(sh, rig_keep(P), 0.006)
    dents = lambda P: F(0.0006) * NOISE(P * F(40)) - F(0.0025) * np.clip(NOISE(P * F(9)) - F(0.35), 0, None)
    fd.add(Func(fn, lo, hi, disp=dents, disp_amp=0.003), 0.0, BASE)
    def straps(P):
        ax = np.abs(P[:, 0])
        side = np.maximum(np.abs(P[:, 2] - F(1.12)) - F(0.034), F(0.2) - ax)
        sh = np.maximum(np.maximum(F(0.1) - ax, ax - F(0.19)), F(1.3) - P[:, 2])
        return np.minimum(side, np.where(P[:, 1] < F(0.06), sh, F(1.0)))
    fd.paint(Func(straps, lo, hi), BLACK)
    fd.paint(Func(lambda P: np.maximum(np.maximum(P[:, 2] - F(1.115), P[:, 1] + F(0.02)), np.abs(P[:, 0]) - F(0.21)), lo, hi), CHAR)
    vo = vest_outer()
    # the amber chevron on the front plate's left (his left: +x), sprayed a little crooked
    cc = v3((0.1, 0.0, 1.235))
    def chev_f(P):
        u = (P[:, 0] - F(cc[0])) * F(math.cos(0.12)) + (P[:, 2] - F(cc[2])) * F(math.sin(0.12))
        v = -(P[:, 0] - F(cc[0])) * F(math.sin(0.12)) + (P[:, 2] - F(cc[2])) * F(math.cos(0.12))
        sp = F(0.004) * NOISE(P * F(70))
        return np.maximum(chevron(u, v, w=0.026, arm=0.07) + sp, P[:, 1] + F(0.02))
    fd.paint(Func(chev_f, lo, hi), AMBER)
    # the big slash across the back plate
    def slash(P):
        u = P[:, 0] * F(0.8) + (P[:, 2] - F(1.2)) * F(0.6)
        v = -P[:, 0] * F(0.6) + (P[:, 2] - F(1.2)) * F(0.8)
        sp = F(0.005) * NOISE(P * F(60))
        return np.maximum(np.maximum(np.abs(v) - F(0.024) + sp, np.abs(u) - F(0.14)), F(0.1) - P[:, 1])
    fd.paint(Func(slash, lo, hi), AMBER)
    # bare-metal scratches on the plates
    rs = np.random.RandomState(7)
    for k in range(9):
        x = rs.uniform(-0.18, 0.18)
        z = rs.uniform(1.12, 1.3)
        front = k < 6
        a = rs.uniform(-0.6, 0.6)
        L = rs.uniform(0.025, 0.05)
        def scr(P, x=x, z=z, a=a, L=L, front=front):
            u = (P[:, 0] - F(x)) * F(math.cos(a)) + (P[:, 2] - F(z)) * F(math.sin(a))
            v = -(P[:, 0] - F(x)) * F(math.sin(a)) + (P[:, 2] - F(z)) * F(math.cos(a))
            side = P[:, 1] + F(0.02) if front else F(0.12) - P[:, 1]
            return np.maximum(np.maximum(np.abs(v) - F(0.0022), np.abs(u) - F(L)), side)
        fd.paint(Func(scr, lo, hi), STEEL)
    # panel lines: across the front plate, down its middle
    def lines(P):
        d = np.abs(vo(P))
        z, x = P[:, 2], P[:, 0]
        across = np.abs(z - F(1.13)) - F(0.0018)
        mid = np.maximum(np.abs(x + F(0.01)) - F(0.0018), np.maximum(F(1.13) - z, z - F(1.32)))
        return np.maximum(np.maximum(np.minimum(across, mid), d - F(0.006)), P[:, 1] + F(0.02))
    fd.sub(Func(lines, lo, hi), 0.0015)
    # rivets at the plate's corners
    for x, z in ((-0.17, 1.27), (0.17, 1.27), (-0.18, 1.1), (0.18, 1.1)):
        h, ok = ray_hit(vo, [v3((x, -0.6, z))], [v3((0, 1, 0))], tmax=0.6)
        if ok[0]:
            fd.add(Sphere(h[0] + v3((0, 0.004, 0)), 0.009), 0.002, STEEL)
    # the utility belt over the hoodie's hem
    hip = Field("Hip")
    tp = torso_prims()
    hip.add(tp[4][0], 0.0)
    hip.add(tp[5][0], 0.08)
    BZ = HEM_Z + 0.005
    def belt(P):
        d = hip.eval(P, margin=0.1)
        return np.maximum(np.abs(d - F(0.05)) - F(0.009), np.abs(P[:, 2] - F(BZ)) - F(0.024))
    fd.add(Func(belt, (-0.45, -0.4, 0.82), (0.45, 0.45, 1.0)), 0.0, BLACK)
    hs = Func(lambda P: hip.eval(P, margin=0.12) - F(0.06), (-0.5, -0.6, 0.8), (0.5, 0.5, 1.02))
    h, ok = ray_hit(hs, [v3((0, -0.6, BZ))], [v3((0, 1, 0))], tmax=0.6)
    if ok[0]:
        fd.add(RoundBox(h[0] + v3((0, -0.004, 0)), (0.034, 0.008, 0.026), 0.006), 0.003, STEEL)
    for sx in (-1, 1):                                                    # two pouches on his hips
        h, ok = ray_hit(hs, [v3((sx * 0.6, -0.12, BZ))], [norm(v3((-sx, 0.35, 0)))], tmax=0.7)
        if not ok[0]:
            continue
        out = norm(v3((sx, -0.5, 0)))
        R = rot_from_axes(y_axis=out, z_axis=Z)
        pc = h[0] + out * 0.028 + Z * (-0.012)
        fd.add(RoundBox(pc, (0.052, 0.026, 0.06), 0.014, R=R, disp=lambda P: F(0.001) * NOISE(P * F(30)), disp_amp=0.0015), 0.006, CHAR)
        fd.add(RoundBox(pc + out * 0.004 + Z * 0.048, (0.056, 0.03, 0.014), 0.008, R=R), 0.004, BLACK)
        fd.add(RoundBox(pc + out * 0.03 + Z * 0.03, (0.008, 0.004, 0.012), 0.003, R=R), 0.002, STEEL)
    return fd


# ======================================================================================= trousers, boots, gloves
def trousers_field():
    """Smoky teal-grey cloth (label 0 in the trousers' material) from his waist into his boots, black knee pads (5), a
    flat pocket on his right thigh with a black flap."""
    fd = Field("Trousers")
    lb = legs_base()
    lo, hi = v3((-0.5, -0.4, 0.15)), v3((0.5, 0.45, 1.06))
    def fn(P):
        d = lb.eval(P, margin=0.08)
        off = F(0.016) + F(0.009) * smoothstep(0.5, 0.3, P[:, 2])
        return np.abs(d - off) - F(0.0065)
    wr = lambda P: F(0.0016) * NOISE(P * np.array([30, 30, 60], F)) + F(0.0025) * np.sin(P[:, 2] * F(80) + F(2) * NOISE(P * F(5))) * smoothstep(0.52, 0.4, P[:, 2]) * smoothstep(0.3, 0.38, P[:, 2])
    fd.add(Inter(Func(fn, lo, hi, disp=wr, disp_amp=0.004), Func(lambda P: np.maximum(F(0.24) - P[:, 2], P[:, 2] - F(0.975)), lo, hi), 0.004), 0.0, BASE)
    surf = Func(lambda P: lb.eval(P, margin=0.12) - F(0.024), (-0.6, -0.5, 0.2), (0.6, 0.5, 1.1))
    for sx in (-1, 1):
        side = "R" if sx < 0 else "L"
        if sx < 0:                                                         # the thigh pocket (right)
            h, ok = ray_hit(surf, [v3((sx * 0.6, -0.03, 0.62))], [v3((-sx, 0.2, 0))], tmax=0.6)
            if ok[0]:
                c = h[0]
                out = norm(v3((sx, -0.2, 0)))
                R = rot_from_axes(y_axis=out, z_axis=Z)
                fd.add(RoundBox(c + out * 0.008, (0.07, 0.016, 0.08), 0.012, R=R, disp=lambda P: F(0.0012) * NOISE(P * F(30)), disp_amp=0.0015), 0.008, BASE)
                fd.add(RoundBox(c + out * 0.018 + Z * 0.066, (0.074, 0.012, 0.022), 0.008, R=R), 0.004, BLACK)
        kn, hip, an = J["knee_" + side], J["hip_" + side], J["ankle_" + side]
        h, ok = ray_hit(surf, [kn + v3((0, -0.5, 0.0))], [v3((0, 1, 0))], tmax=0.6)
        kc = h[0] if ok[0] else kn + v3((0, -0.1, 0))
        ax = norm(hip - an)
        Rk = rot_from_axes(y_axis=norm(v3((0, -1, 0)) - ax * (v3((0, -1, 0)) @ ax)), z_axis=ax)
        fd.add(Ellipsoid(kc + v3((0, 0.012, 0.0)), (0.072, 0.028, 0.088), R=Rk), 0.008, BLACK)
        fd.sub(Torus(kc + v3((0, -0.013, 0.0)), 0.046, 0.003, R=Rk @ rot_from_axes(z_axis=(0, 1, 0))), 0.002)
    return fd


def boots_field():
    return em.boots_field()


GLOVE_CUFF = (-0.07, 0.03)                   # the gloves' cuffs: from this far up the forearm to past the wrist (along it)


def gloves_field():
    """Black fingerless gloves (5): over the palm and the back of the hand to the first knuckles (the fingers and the
    thumb's tip bare), a snug cuff over the hoodie's sleeve; a gunmetal knuckle plate (9)."""
    fd = Field("Gloves")
    for side in ("R", "L"):
        hh = Field("HandHull")
        hand(hh, side)
        wrf, f, n, t = hand_frame(side)
        fingers, (tb, p1, p2) = finger_points(side)
        mids = [lerp(p[1], p[2], 0.15) for p in fingers]
        def keep(P, wrf=wrf, f=f, p2=p2):
            s = (P - wrf.astype(F)) @ f.astype(F)
            tip = np.sqrt(((P - p2.astype(F)) ** 2).sum(1)) - F(0.03)        # the thumb's tip bare
            return np.maximum(s - F(0.168), -tip)
        glove = Inter(Shell(hh, 0.006, 0.0095, pad=0.05, disp=lambda P: F(0.0008) * NOISE(P * F(50)), disp_amp=0.001),
                      Func(keep, wrf - 0.3, wrf + 0.3), 0.003)
        fd.add(glove, 0.0, BLACK)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        def cuff(P, wr=wr, ax=ax):
            s = (P - wr.astype(F)) @ ax.astype(F)
            q = P - wr.astype(F) - s[:, None] * ax.astype(F)[None, :]
            rho = np.sqrt((q * q).sum(1))
            r = F(0.071) - F(0.12) * np.clip(s, None, 0)
            return np.maximum(np.abs(rho - r) - F(0.0075), np.maximum(F(GLOVE_CUFF[0]) - s, s - F(GLOVE_CUFF[1])))
        fd.add(Func(cuff, wr - 0.3, wr + 0.3), 0.01, BLACK)
        h, ok = ray_hit(hh, [wrf + f * 0.12 - n * 0.3], [n], tmax=0.4)
        kc = (h[0] if ok[0] else wrf + f * 0.12 - n * 0.06) - n * 0.016
        Rk = np.stack([t, -n, f], axis=1)
        fd.add(RoundBox(kc, (0.058, 0.007, 0.022), 0.007, R=Rk), 0.006, GUN)
    return fd


# ======================================================================================= the wrist rig (left forearm)
def rig_frame():
    """(centre on the left sleeve, along (toward the wrist), out (its face), across)."""
    el, wr = J["elbow_L"], J["wrist_L"]
    ax = norm(wr - el)
    out = norm(v3((1.0, -0.45, 0.55)) - ax * float(v3((1.0, -0.45, 0.55)) @ ax))
    c = lerp(el, wr, 0.5)
    fd = Field("Fa")
    for p, k in arm_prims("L")[3:5]:
        fd.add(p, k)
    sv = Func(lambda P: fd.eval(P, margin=0.06) - F(SUIT_OFF + SUIT_T * 0.5), c - 0.3, c + 0.3)
    h, ok = ray_hit(sv, [c + out * 0.3], [-out], tmax=0.4)
    surf = h[0] if ok[0] else c + out * 0.09
    return surf, ax, out, norm(np.cross(out, ax)), fd


def wrist_rig_field():
    """A white robot forearm plate (7), salvaged: curved round the outside of his forearm, panel lines, a dent, an amber
    slash sprayed across it (13); strapped on with black straps (5) and steel buckles (10); a small black readout box (5)
    on it with a slot for the amber readout."""
    fd = Field("WristRig")
    c, ax, out, acr, fa = rig_frame()
    # the plate: a shell of the forearm, on its outer half
    def plate(P):
        d = fa.eval(P, margin=0.08)
        sh = np.abs(d - F(SUIT_OFF + SUIT_T + 0.012)) - F(0.006)
        s = (P - c.astype(F)) @ ax.astype(F)
        q = P - c.astype(F) - s[:, None] * ax.astype(F)[None, :]
        cosang = (q @ out.astype(F)) / (np.sqrt((q * q).sum(1)) + F(1e-6))
        return np.maximum(np.maximum(sh, np.abs(s) - F(0.1) + F(0.012) * cosang), F(0.05) - cosang)
    fd.add(Func(plate, c - 0.25, c + 0.25, disp=lambda P: F(0.0004) * NOISE(P * F(40)), disp_amp=0.0006), 0.0, WHITE)
    fd.sub(Sphere(c + out * 0.03 - ax * 0.06 + acr * 0.03, 0.022), 0.006)                      # a dent
    # panel lines on it
    def pl(P):
        s = (P - c.astype(F)) @ ax.astype(F)
        return np.maximum(np.abs(s + F(0.045)) - F(0.0016), np.abs(fa.eval(P, margin=0.08) - F(SUIT_OFF + SUIT_T + 0.018)) - F(0.004))
    fd.sub(Func(pl, c - 0.25, c + 0.25), 0.0012)
    # the amber slash across it
    def slash(P):
        q = P - c.astype(F)
        u = q @ ax.astype(F)
        v = q @ acr.astype(F)
        w = (u * F(0.6) - v * F(0.8))
        return np.maximum(np.maximum(np.abs(w) - F(0.013) + F(0.003) * NOISE(P * F(80)), np.abs(u * F(0.8) + v * F(0.6)) - F(0.07)),
                          F(0.0) - (q @ out.astype(F)))
    fd.paint(Func(slash, c - 0.2, c + 0.2), AMBER)
    # the readout box near the wrist end
    rc = c + ax * 0.045 + out * 0.026
    R = np.stack([acr, ax, out], axis=1)
    fd.add(RoundBox(rc, (0.03, 0.026, 0.012), 0.007, R=R), 0.004, BLACK)
    fd.sub(RoundBox(rc + out * 0.012, (0.02, 0.016, 0.004), 0.002, R=R), 0.002)
    # straps round the forearm
    for e in (-1, 1):
        sc = c + ax * (e * 0.075) - out * 0.06
        fd.add(Inter(Shell(Cylinder(sc, 0.083, 0.03, R=rot_from_axes(z_axis=ax)), 0.0, 0.006),
                     Func(lambda P, sc=sc: np.abs((P - sc.astype(F)) @ ax.astype(F)) - F(0.011), sc - 0.14, sc + 0.14), 0.002), 0.003, BLACK)
        fd.add(RoundBox(c + ax * (e * 0.075) + out * 0.03 - acr * 0.035, (0.012, 0.014, 0.006), 0.003, R=R), 0.002, STEEL)
    return fd


def wrist_glow_field():
    """The wrist rig's amber readout (shipped glowing)."""
    fd = Field("WristGlow")
    c, ax, out, acr, fa = rig_frame()
    R = np.stack([acr, ax, out], axis=1)
    rc = c + ax * 0.045 + out * 0.026
    fd.add(RoundBox(rc + out * 0.008, (0.018, 0.014, 0.003), 0.002, R=R), 0.0)
    return fd


# ======================================================================================= the rig: server core, mast, emitter ring
MAST_C = v3((0.54, 0.3, 0.0))             # the server core's (and the mast's) axis at the floor
FRONT = norm(v3((-0.45, -1.0, 0.0)))       # the camera's side
TOWARD = norm(v3((-MAST_C[0], -MAST_C[1], 0.0)))        # toward him
SRV_F = norm(FRONT + TOWARD * 0.6)         # the server core's front faces between him and the camera
SRV_X = norm(np.cross(Z, SRV_F))           # across its front
R_SRV = np.stack([SRV_X, SRV_F, Z], axis=1)
DECK_R, DECK_H = 0.29, 0.05
SRV_HALF = (0.19, 0.16, 0.29)              # the casing's half extents (across, front-back, height)
SRV_Z = DECK_H + SRV_HALF[2]               # its centre's height
SRV_TOP = DECK_H + 2 * SRV_HALF[2]
MAST_Z0, MAST_Z1, MAST_R = SRV_TOP, 1.8, 0.034
RING_Z = 1.93                              # the emitter ring's plane = the node's centre (the pulse's origin)
RING_R = 0.23
EMIT_N = 8
EMIT_A0 = math.atan2(FRONT[1], FRONT[0])   # an emitter faces the camera
NODE_R = 0.058
CORE_C = MAST_C + Z * RING_Z
FLARE_R = RING_R + 0.09                   # the flare ring's radius (just round the lenses)
ANT_P = MAST_C - SRV_X * 0.1 + SRV_F * -0.05     # the whip antenna's foot (clamped to the mast's side)
ANT_TIP = ANT_P + v3((-0.02, 0.0, 2.38))


def srv_pt(u, v, w):
    """A point on/in the casing: across (u), toward its front (v), up from its centre (w)."""
    return MAST_C + SRV_X * u + SRV_F * v + Z * (SRV_Z + w)


def _emit_c(k):
    a = EMIT_A0 + 2 * math.pi * k / EMIT_N
    d = v3((math.cos(a), math.sin(a), 0.0))
    return MAST_C + d * RING_R + Z * RING_Z, d


def machine_field():
    """On `machine`: the skid (gunmetal 9, steel bolts 10); the server core's casing (robot white 0: panel lines, dents,
    vents), its front: a black panel (5) with drive slots and slots for the amber light strips, the round eye socket
    (a black bezel) where the robot's light was; a big amber chevron sprayed on its side (13); a black cable gland on its
    top, black handles."""
    fd = Field("Machine")
    c = MAST_C
    rv = lambda P: F(0.0005) * NOISE(P * F(50))
    fd.add(Func(lambda P: _octagon(P, c, DECK_R, DECK_H, 0.0), c - 0.4, c + 0.4, disp=rv, disp_amp=0.001), 0.0, GUN)
    for k in range(8):
        a = 2 * math.pi * k / 8
        fd.add(Sphere(c + v3((math.cos(a), math.sin(a), 0)) * (DECK_R - 0.028) + Z * DECK_H, 0.01), 0.002, STEEL)
    # the casing: a rounded box with a bevelled top
    dents = lambda P: F(0.0005) * NOISE(P * F(45)) - F(0.004) * np.clip(NOISE(P * F(7)) - F(0.4), 0, None)
    fd.add(RoundBox(c + Z * SRV_Z, SRV_HALF, 0.035, R=R_SRV, disp=dents, disp_amp=0.004), 0.01, BASE)
    # panel lines round it (two levels) and down its sides
    def seams(P):
        q = (P - (c + Z * SRV_Z).astype(F)) @ R_SRV.astype(F)
        box = np.abs(np.maximum(np.maximum(np.abs(q[:, 0]) - F(SRV_HALF[0]), np.abs(q[:, 1]) - F(SRV_HALF[1])), np.abs(q[:, 2]) - F(SRV_HALF[2]))) - F(0.008)
        lv = np.minimum(np.abs(q[:, 2] - F(0.17)) - F(0.0018), np.abs(q[:, 2] + F(0.2)) - F(0.0018))
        dn = np.maximum(np.abs(np.abs(q[:, 1]) - F(0.03)) - F(0.0018), F(SRV_HALF[0] - 0.01) - np.abs(q[:, 0]))
        return np.maximum(np.minimum(lv, dn), box)
    fd.sub(Func(seams, c - 0.4, c + 0.8), 0.0015)
    # the front panel: black, inset
    fc = srv_pt(0.0, SRV_HALF[1] + 0.002, 0.02)
    fd.sub(RoundBox(fc, (SRV_HALF[0] - 0.035, 0.012, SRV_HALF[2] - 0.06), 0.012, R=R_SRV), 0.004)
    fd.add(RoundBox(fc - SRV_F * 0.008, (SRV_HALF[0] - 0.04, 0.006, SRV_HALF[2] - 0.065), 0.008, R=R_SRV), 0.003, BLACK)
    # drive slots (black recesses) in the lower half, the eye socket above, the light strips' slots down each side
    for k in range(4):
        fd.sub(RoundBox(srv_pt(-0.02, SRV_HALF[1] - 0.004, -0.18 + 0.045 * k), (0.09, 0.012, 0.012), 0.005, R=R_SRV), 0.002)
        fd.add(Sphere(srv_pt(0.09, SRV_HALF[1] - 0.006, -0.18 + 0.045 * k), 0.008), 0.002, STEEL)
    ec = srv_pt(0.0, SRV_HALF[1] - 0.004, 0.13)
    fd.add(Torus(ec, 0.052, 0.012, R=rot_from_axes(z_axis=SRV_F)), 0.004, GUN)
    fd.sub(Cylinder(ec + SRV_F * 0.004, 0.044, 0.02, R=rot_from_axes(z_axis=SRV_F)), 0.003)
    for e in (-1, 1):
        fd.sub(RoundBox(srv_pt(e * 0.115, SRV_HALF[1] - 0.004, 0.0), (0.009, 0.014, 0.16), 0.006, R=R_SRV), 0.002)
    # the amber chevron sprayed on its side (the side the camera sees: -SRV_X is toward him... use the outer side)
    side_n = SRV_X if (SRV_X @ v3((1, 0, 0))) > 0 else -SRV_X
    scen = c + Z * (SRV_Z + 0.02) + side_n * SRV_HALF[0]
    up = Z
    acr = norm(np.cross(up, side_n))
    def chev(P):
        q = P - scen.astype(F)
        u, v = q @ acr.astype(F), q @ up.astype(F)
        sp = F(0.006) * NOISE(P * F(50))
        return np.maximum(chevron(u, v, w=0.05, arm=0.13) + sp, np.abs(q @ side_n.astype(F)) - F(0.04))
    fd.paint(Func(chev, scen - 0.3, scen + 0.3), AMBER)
    # an amber stripe across its front's top edge (paint), and on the front panel the Resistance slash
    def stripe(P):
        q = (P - (c + Z * SRV_Z).astype(F)) @ R_SRV.astype(F)
        return np.maximum(np.maximum(np.abs(q[:, 2] - F(SRV_HALF[2] - 0.035)) - F(0.016), q[:, 1] - F(SRV_HALF[1] + 0.03)),
                          F(SRV_HALF[1] - 0.06) - q[:, 1])
    fd.paint(Func(stripe, c - 0.4, c + 0.8), AMBER)
    # vents on the back
    for k in range(5):
        fd.sub(RoundBox(srv_pt(0.0, -SRV_HALF[1], -0.1 + 0.04 * k), (0.12, 0.012, 0.007), 0.004, R=R_SRV), 0.002)
    # handles on the sides (black)
    for e in (-1, 1):
        hc = srv_pt(e * (SRV_HALF[0] + 0.012), 0.0, 0.2)
        fd.add(Chain([hc - SRV_F * 0.07 - SRV_X * e * 0.012, hc - SRV_F * 0.06, hc + SRV_F * 0.06, hc + SRV_F * 0.07 - SRV_X * e * 0.012],
                     [0.011] * 4, k=0.006), 0.004, BLACK)
    # a pried-up corner of the top (a bent plate, a black gap under it)
    pc = srv_pt(-SRV_HALF[0] + 0.07, -SRV_HALF[1] + 0.06, SRV_HALF[2])
    fd.sub(RoundBox(pc, (0.06, 0.05, 0.02), 0.01, R=R_SRV), 0.004)
    fd.add(RoundBox(pc + Z * 0.028 - SRV_X * 0.01, (0.06, 0.05, 0.006), 0.004, R=R_SRV @ euler(0.0, 0.35, 0.0)), 0.003, BASE)
    fd.add(RoundBox(pc - Z * 0.01, (0.05, 0.04, 0.008), 0.004, R=R_SRV), 0.003, BLACK)
    # the cable gland on the top's back (the mast's cables), steel bolts on the top's corners
    for e1 in (-1, 1):
        for e2 in (-1, 1):
            fd.add(Sphere(srv_pt(e1 * (SRV_HALF[0] - 0.035), e2 * (SRV_HALF[1] - 0.035), SRV_HALF[2] + 0.002), 0.009), 0.002, STEEL)
    return fd


def mast_field():
    """On `mast`: the collar on the casing's top (gunmetal 9), the pipe mast in sections (gunmetal, steel clamps 10),
    a black cable taped round it in a loose spiral (12, amber tape 13), the whip antenna clamped to its side (black, a
    steel base), up to the ring's hub."""
    fd = Field("Mast")
    c = MAST_C
    fd.add(Cylinder(c + Z * (MAST_Z0 + 0.02), 0.085, 0.04, rr=0.012), 0.0, GUN)
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        fd.add(Sphere(c + v3((math.cos(a), math.sin(a), 0)) * 0.07 + Z * (MAST_Z0 + 0.041), 0.008), 0.002, STEEL)
    fd.add(Cylinder(c + Z * ((MAST_Z0 + 1.05) / 2), MAST_R + 0.01, 1.05 - MAST_Z0, rr=0.01), 0.006, GUN)
    fd.add(Cylinder(c + Z * ((1.05 + MAST_Z1) / 2), MAST_R, MAST_Z1 - 1.05, rr=0.01), 0.006, GUN)
    for zz, rr in ((MAST_Z0 + 0.12, 0.054), (1.05, 0.056), (1.4, 0.046), (MAST_Z1 - 0.05, 0.046)):
        fd.add(Cylinder(c + Z * zz, rr, 0.03, rr=0.008), 0.004, STEEL)
    # a cable spiralling up it, taped on
    pts = []
    for k in range(26):
        z = MAST_Z0 + 0.08 + (MAST_Z1 - MAST_Z0 - 0.16) * k / 25
        a = 0.6 + 2.6 * math.pi * k / 25
        r = (MAST_R + 0.026) if z > 1.05 else (MAST_R + 0.036)
        pts.append(c + v3((math.cos(a), math.sin(a), 0)) * r + Z * z)
    fd.add(Chain(pts, [0.013] * len(pts), k=0.008), 0.004, RUBBER)
    for k in (4, 11, 18, 23):
        p = pts[k]
        fd.add(Sphere(p, 0.019), 0.004, AMBER)
    # the whip antenna clamped to the mast
    fd.add(Cylinder(ANT_P + Z * (MAST_Z0 + 0.12), 0.02, 0.1, rr=0.006), 0.004, STEEL)
    for zz in (0.95, 1.5):
        fd.add(Chain([c + Z * zz, ANT_P + Z * zz], [0.012, 0.012], k=0.004), 0.004, STEEL)
    fd.add(RoundCone(ANT_P + Z * (MAST_Z0 + 0.16), ANT_TIP, 0.011, 0.005), 0.004, BLACK)
    return fd


def ring_field():
    """On `mast`: the emitter ring: the hub, four spokes, the ring (gunmetal 9), eight emitter cans on it facing outward
    (black 5, a steel bezel 10 round each lens' window), the cup under the node and its cage of four prongs (gunmetal,
    steel tips)."""
    fd = Field("Ring")
    c = MAST_C
    hub = c + Z * (MAST_Z1 + 0.02)
    fd.add(Cylinder(hub, 0.06, 0.05, rr=0.014), 0.0, GUN)
    fd.add(RoundCone(c + Z * (MAST_Z1 - 0.04), hub, MAST_R + 0.004, 0.058), 0.01, GUN)
    for k in range(4):
        a = EMIT_A0 + math.pi / EMIT_N + 2 * math.pi * k / 4
        d = v3((math.cos(a), math.sin(a), 0.0))
        fd.add(RoundCone(hub + d * 0.04, c + d * (RING_R - 0.01) + Z * (RING_Z - 0.01), 0.013, 0.011), 0.006, GUN)
    fd.add(Torus(c + Z * RING_Z, RING_R, 0.017), 0.006, GUN)
    for k in range(EMIT_N):
        pc, d = _emit_c(k)
        R = rot_from_axes(z_axis=d)
        fd.add(Cylinder(pc + d * 0.035, 0.044, 0.07, rr=0.014, R=R), 0.006, BLACK)               # the can
        fd.add(Torus(pc + d * 0.07, 0.036, 0.008, R=R), 0.003, STEEL)                            # its bezel
        fd.sub(Cylinder(pc + d * 0.078, 0.031, 0.016, R=R), 0.002)                                # the lens' window
        fd.add(Cylinder(pc - Z * 0.03 + d * 0.02, 0.008, 0.03, rr=0.003), 0.003, STEEL)         # a little foot
    # the cup under the node, its cage of prongs
    fd.add(RoundCone(hub + Z * 0.02, CORE_C - Z * (NODE_R - 0.012), 0.034, 0.05), 0.01, GUN)
    fd.add(Torus(CORE_C - Z * (NODE_R - 0.014), 0.05, 0.008), 0.004, STEEL)
    for k in range(4):
        a = EMIT_A0 + 2 * math.pi * (k + 0.5) / 4
        d = v3((math.cos(a), math.sin(a), 0))
        pts = [CORE_C - Z * (NODE_R - 0.02) + d * 0.048, CORE_C + d * (NODE_R + 0.03), CORE_C + Z * (NODE_R + 0.03) + d * 0.04,
               CORE_C + Z * (NODE_R + 0.055) + d * 0.01]
        fd.add(Chain(pts, [0.009, 0.0085, 0.008, 0.007], k=0.004), 0.004, GUN)
    fd.add(Sphere(CORE_C + Z * (NODE_R + 0.06), 0.014), 0.004, STEEL)
    return fd


def emitters_field():
    """The emitters' lenses (shipped glowing amber), one in each can's window."""
    fd = Field("Emitters")
    for k in range(EMIT_N):
        pc, d = _emit_c(k)
        fd.add(Cylinder(pc + d * 0.076, 0.03, 0.014, rr=0.006, R=rot_from_axes(z_axis=d)), 0.0)
    return fd


def node_field():
    """The node (shipped glowing amber): a ball in its cage at the ring's centre."""
    fd = Field("Node")
    fd.add(Sphere(CORE_C, NODE_R), 0.0)
    return fd


def flare_field():
    """The flare: a ring of amber light round the emitters (scaled from nothing at the pulse)."""
    fd = Field("Flare")
    fd.add(Torus(CORE_C, FLARE_R, 0.022), 0.0)
    fd.add(Torus(CORE_C, FLARE_R - 0.06, 0.012), 0.0)
    return fd


def lights_field():
    """The server core's amber lights (shipped glowing): its round eye and the two strips down its front."""
    fd = Field("Lights")
    ec = srv_pt(0.0, SRV_HALF[1] - 0.004, 0.13)
    fd.add(Cylinder(ec + SRV_F * 0.0, 0.042, 0.012, rr=0.006, R=rot_from_axes(z_axis=SRV_F)), 0.0)
    for e in (-1, 1):
        fd.add(RoundBox(srv_pt(e * 0.115, SRV_HALF[1] - 0.008, 0.0), (0.0055, 0.008, 0.152), 0.0045, R=R_SRV), 0.0)
    return fd


# ======================================================================================= the workstation (crates, keyboard, laptop)
CON_P = v3((-0.27, -0.46, 0.0))                # the crates' foot (their middle)
CON_U = norm(v3((-CON_P[0], -CON_P[1], 0.0)))         # toward him (horizontal)
SW = norm(np.cross(CON_U, Z))                # across (+ his left as he faces them)
R_CON = np.stack([SW, CON_U, Z], axis=1)
CR1 = (0.26, 0.21, 0.27)                     # the bottom crate's half extents (across, toward him, up)
CR2 = (0.235, 0.2, 0.18)                    # the top crate's
CR2_YAW = 0.05
TOP_Z = 2 * CR1[2] + 2 * CR2[2] + 0.004      # the top crate's lid
KB_C = CON_P + CON_U * 0.115 + Z * (TOP_Z + 0.014)      # the keyboard's middle
KB_HALF = (0.18, 0.06, 0.012)
KB_R = R_CON @ euler(math.radians(4.0), 0, 0)
ENTER_C = KB_C + KB_R @ v3((-0.142, 0.0, KB_HALF[2] + 0.014))   # the Enter key's top (his right end)
LAP_C = CON_P - CON_U * 0.085 + Z * TOP_Z     # the laptop's base (its middle, on the lid)
LAP_HALF = (0.15, 0.1, 0.012)
LID_TILT = math.radians(108.0)               # the screen swung up from the base, leaning back


def con_pt(w, u, z):
    return CON_P + SW * w + CON_U * u + Z * z


def lid_frame():
    """The laptop's lid: (hinge, up the lid, its face normal toward him)."""
    hinge = LAP_C - CON_U * LAP_HALF[1] + Z * (LAP_HALF[2] * 2)
    u = norm(CON_U * math.cos(LID_TILT) + Z * math.sin(LID_TILT))
    n = norm(np.cross(SW, u))
    if n @ CON_U < 0:
        n = -n
    return hinge, u, n


def _crate(fd, c, half, R, rs, label=TEAL):
    """An ammo crate: a teal-grey box with ribs round it, black latches, rope handles, amber stencils."""
    fd.add(RoundBox(c, half, 0.018, R=R, disp=lambda P: F(0.0006) * NOISE(P * F(40)), disp_amp=0.001), 0.006, label)
    for e in (-1, 1):                                                   # ribs round it near each end
        fd.add(RoundBox(c + R[:, 0] * (e * (half[0] - 0.045)), (0.018, half[1] + 0.008, half[2] + 0.004), 0.008, R=R), 0.004, label)
    fd.add(RoundBox(c + R[:, 2] * (half[2] - 0.035), (half[0] + 0.006, half[1] + 0.006, 0.006), 0.004, R=R), 0.003, label)   # the lid's seam ridge
    for e in (-1, 1):                                                   # latches on the front
        p = c + R[:, 1] * (half[1] + 0.008) + R[:, 0] * (e * half[0] * 0.5) + R[:, 2] * (half[2] - 0.05)
        fd.add(RoundBox(p, (0.024, 0.008, 0.03), 0.005, R=R), 0.003, BLACK)
    for e in (-1, 1):                                                   # rope handles on the ends
        p = c + R[:, 0] * (e * (half[0] + 0.01)) + R[:, 2] * (half[2] * 0.3)
        fd.add(Torus(p, 0.04, 0.008, R=rot_from_axes(z_axis=R[:, 0]) @ euler(0, 0, 0)), 0.003, BLACK)


def console_field():
    """On `machine`: two stacked ammo crates (teal-grey 8, black latches and handles 5, amber stencils 13), the
    keyboard (black 5, dark keys 12, the big amber Enter key 13 on his right), the laptop (gunmetal 9, an amber chevron on
    its lid's back, a black bezel round the screen with a crack across it)."""
    fd = Field("Console")
    rs = np.random.RandomState(11)
    c1 = CON_P + Z * CR1[2]
    _crate(fd, c1, CR1, R_CON, rs)
    R2 = R_CON @ euler(0, 0, CR2_YAW)
    c2 = CON_P + Z * (2 * CR1[2] + CR2[2]) + CON_U * 0.01
    _crate(fd, c2, CR2, R2, rs)
    # stencils: an amber chevron and a stripe on the bottom crate's front (toward the camera: its -CON_U face is the far
    # side; paint the face toward him and the camera's side, -SW)
    for (cc, half, R) in ((c1, CR1, R_CON), (c2, CR2, R2)):
        for face, ext in ((R[:, 1], half[1]), (-R[:, 0], half[0])):
            fc = cc + face * ext
            acr = norm(np.cross(Z, face))
            def chev(P, fc=fc, face=face, acr=acr):
                q = P - fc.astype(F)
                u, v = q @ acr.astype(F), q @ Z.astype(F)
                return np.maximum(chevron(u, v, w=0.028, arm=0.075), np.abs(q @ face.astype(F)) - F(0.03))
            fd.paint(Func(chev, fc - 0.2, fc + 0.2), AMBER)
    # the keyboard
    Rk = KB_R
    fd.add(RoundBox(KB_C, KB_HALF, 0.008, R=Rk), 0.004, BLACK)
    for i in range(12):
        for j in range(4):
            w = -0.155 + 0.026 * i
            u = -0.04 + 0.027 * j
            if i >= 10 and j in (1, 2):
                continue                                           # (the Enter key goes there)
            fd.add(RoundBox(KB_C + Rk @ v3((w, u, KB_HALF[2] + 0.004)), (0.0105, 0.0105, 0.005), 0.003, R=Rk), 0.002, RUBBER)
    fd.add(RoundBox(KB_C + Rk @ v3((-0.01, 0.07 - 0.019, KB_HALF[2] + 0.004)), (0.07, 0.0105, 0.005), 0.003, R=Rk), 0.002, RUBBER)  # space bar
    ek = KB_C + Rk @ v3((-0.142 + 0.0, 0.0, KB_HALF[2] + 0.007))
    fd.add(RoundBox(ek, (0.024, 0.024, 0.007), 0.004, R=Rk), 0.002, AMBER)
    # the laptop: its base, the hinge, the lid (a black bezel on its face, an amber chevron on its back)
    fd.add(RoundBox(LAP_C + Z * LAP_HALF[2], LAP_HALF, 0.008, R=R_CON), 0.004, GUN)
    fd.sub(RoundBox(LAP_C + Z * (LAP_HALF[2] * 2) + CON_U * 0.015, (LAP_HALF[0] - 0.02, LAP_HALF[1] - 0.04, 0.003), 0.002, R=R_CON), 0.002)
    hinge, u, n = lid_frame()
    lc = hinge + u * 0.1
    Rl = np.stack([SW, u, n], axis=1)
    fd.add(RoundBox(lc - n * 0.004, (LAP_HALF[0], 0.1, 0.008), 0.007, R=Rl), 0.004, GUN)
    fd.add(RoundBox(lc + n * 0.002, (LAP_HALF[0] - 0.008, 0.092, 0.003), 0.003, R=Rl), 0.002, BLACK)
    fd.add(Cylinder(hinge, 0.009, 2 * LAP_HALF[0] - 0.03, rr=0.003, R=rot_from_axes(z_axis=SW)), 0.003, BLACK)
    def lchev(P):
        q = P - (lc - n * 0.012).astype(F)
        return np.maximum(chevron(q @ SW.astype(F), q @ u.astype(F) + F(0.01), w=0.03, arm=0.08), np.abs(q @ n.astype(F)) - F(0.01))
    fd.paint(Func(lchev, lc - 0.2, lc + 0.2), AMBER)
    # the cables: from the laptop's side down to the keyboard, and down the crates' back to the floor
    lp_side = LAP_C - SW * (LAP_HALF[0] + 0.005) + Z * 0.012
    fd.add(Chain([lp_side, lp_side - SW * 0.03 + CON_U * 0.04, KB_C - SW * (KB_HALF[0] + 0.02) + Z * 0.0, KB_C - SW * KB_HALF[0]],
                 [0.007] * 4, k=0.006), 0.003, RUBBER)
    return fd


def cable_field():
    """On `machine`: bundles of cable (black rubber 12, a few red 6 and amber-taped 13) from the laptop down the crates'
    back and over the floor to the server core's side and back; tie wraps."""
    fd = Field("Cable")
    back = LAP_C + SW * (LAP_HALF[0] - 0.02) - CON_U * (LAP_HALF[1] - 0.01) + Z * 0.012
    s_in = srv_pt(0.13, SRV_HALF[1] + 0.004, -0.2)
    rs = np.random.RandomState(3)
    acr = norm(v3((0.6, -0.8, 0.0)))
    for k, (lab, off) in enumerate(((RUBBER, 0.0), (RUBBER, 0.024), (RED, -0.022), (RUBBER, 0.045))):
        o = acr * off
        j = lambda: v3((rs.uniform(-0.015, 0.015), rs.uniform(-0.015, 0.015), 0.0))
        pts = [back + o * 0.4, back - CON_U * 0.05 - Z * 0.05 + o * 0.6,
               con_pt(CR2[0] + 0.02, -0.12, 0.6) + o, con_pt(CR1[0] + 0.03, -0.1, 0.05) + o,
               v3((0.12, -0.42, 0.016)) + o * 1.5 + j(), v3((0.36, -0.3, 0.016)) + o * 1.5 + j(),
               v3((0.58, -0.1, 0.02)) + o, v3((0.6, 0.0, 0.07)) + o * 0.6, s_in + o * 0.4]
        fd.add(Chain(pts, [0.012 if lab != RED else 0.009] * len(pts), k=0.012), 0.003, lab)
    # tie wraps (amber tape) round the bundle
    for p0, p1, t in ((v3((0.12, -0.42, 0.02)), v3((0.36, -0.3, 0.02)), 0.4), (v3((0.36, -0.3, 0.02)), v3((0.58, -0.1, 0.02)), 0.5)):
        p = lerp(p0, p1, t)
        fd.add(Torus(p + Z * 0.004 + acr * 0.02, 0.04, 0.008, R=rot_from_axes(z_axis=norm(p1 - p0))), 0.003, AMBER)
    # a cable from the server core's top up into the mast's foot
    t0 = srv_pt(0.0, -SRV_HALF[1] + 0.03, SRV_HALF[2] + 0.01)
    fd.add(Chain([t0, t0 + Z * 0.05 - SRV_F * 0.01, MAST_C + Z * (MAST_Z0 + 0.1) - SRV_F * 0.05], [0.014] * 3, k=0.008), 0.004, RUBBER)
    return fd


def screen_field():
    """The laptop's screen (shipped glowing amber), cracked across (a dark crack cut into it)."""
    fd = Field("Screen")
    hinge, u, n = lid_frame()
    lc = hinge + u * 0.1
    Rl = np.stack([SW, u, n], axis=1)
    fd.add(RoundBox(lc + n * 0.005, (LAP_HALF[0] - 0.02, 0.078, 0.002), 0.0015, R=Rl), 0.0)
    crack = [lc + SW * 0.12 + u * 0.06, lc + SW * 0.05 + u * 0.01, lc - SW * 0.02 + u * 0.03, lc - SW * 0.08 - u * 0.05]
    fd.sub(Chain([p + n * 0.006 for p in crack], [0.0025] * 4, k=0.0), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0.0, -0.24, 1.614)), 0.045, 0.35), (hp((0.0, -0.21, 1.69)), 0.03, 0.12)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.1, -0.14, 1.62)), 0.055, 0.35), (hp((sx * 0.07, -0.16, 1.63)), 0.03, 0.14),
                (hp((sx * 0.165, 0.035, 1.67)), 0.04, 0.25)]
    return pts


# ======================================================================================= build config
GLB_NAME = "firewall"
ROOT_NAME = "FirewallHQ"
TEX_PREFIX = "firewall"
MAT_NAME = "FirewallMat"
MESH_NAME = "Firewall"
BASE_MODULE = "firewall_base"
ANIM_MODULE = "anim_firewall"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Headset", "Hoodie", "Vest", "Trousers", "Boots", "Gloves", "WristRig",
         "WristGlow", "Machine", "Mast", "Ring", "Emitters", "Node", "Flare", "Lights", "Console", "Cable", "Screen"]
REGION_PARTS = ("Skin", "Headset", "Hoodie", "Vest", "Trousers", "Gloves", "WristRig", "Machine", "Mast", "Ring",
                "Console", "Cable")
CHARCOAL_C = (0.13, 0.13, 0.15)            # the Resistance's charcoal and gunmetal-black
GUNMETAL_C = (0.22, 0.23, 0.25)
TEAL_C = (0.2, 0.27, 0.28)                 # worn smoky teal-grey
AMBER_C = (0.95, 0.6, 0.14)                # amber paint
GLOW_A = (1.0, 0.62, 0.15)                 # the Resistance's ember amber (the glowing parts)
ROBOT_W = (0.86, 0.87, 0.88)               # salvaged robot white
CLOTH = {"base": CHARCOAL_C, "black": (0.05, 0.05, 0.06), "olive": TEAL_C, "coyote": AMBER_C, "white": ROBOT_W,
         "red": (0.7, 0.12, 0.08), "gunmetal": GUNMETAL_C, "steel": (0.62, 0.64, 0.68), "glass": (0.05, 0.055, 0.06),
         "rubber": (0.08, 0.08, 0.09)}
TROUSERS = dict(CLOTH, base=TEAL_C, olive=CHARCOAL_C)
ARMOR = dict(CLOTH, weave=0.0, base=GUNMETAL_C, olive=CHARCOAL_C, gloss=0.5)
MACHINE = dict(CLOTH, weave=0.0, base=ROBOT_W, olive=TEAL_C, gloss=0.45, gunmetal=(0.2, 0.21, 0.23))
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_FirewallSkin", "base": (0.66, 0.45, 0.32), "ruddy": (0.7, 0.4, 0.3), "lips": (0.52, 0.3, 0.25),
                      "brow": ((0.04, 0.03, 0.025), (0.1, 0.075, 0.06)),
                      "extra": ((LASH, (0.04, 0.03, 0.025), 0.5), (STUBBLE, (0.4, 0.3, 0.23), 0.2, 0.25))}),
    "Hair": ("hair", {"name": "HQ_FirewallHair", "base": (0.05, 0.045, 0.045), "hi": (0.2, 0.18, 0.18), "low": (0.02, 0.018, 0.018),
                      "streak": (0.04, 0.035, 0.035), "tint": (0.08, 0.07, 0.07)}),
    "Hoodie": ("modern_kit", dict(CLOTH, name="HQ_FirewallCloth")),
    "Gloves": ("modern_kit", dict(CLOTH, name="HQ_FirewallCloth")),
    "Trousers": ("modern_kit", dict(TROUSERS, name="HQ_FirewallTrousers")),
    "Vest": ("modern_kit", dict(ARMOR, name="HQ_FirewallArmor")),
    "Headset": ("modern_kit", dict(ARMOR, name="HQ_FirewallArmor")),
    "WristRig": ("modern_kit", dict(ARMOR, name="HQ_FirewallArmor")),
    "Boots": ("leather_dyed", {"name": "HQ_FirewallBoots", "base": (0.06, 0.06, 0.065), "dyed": (0.06, 0.06, 0.065),
                               "worn_c": (0.24, 0.24, 0.26)}),
    "Machine": ("modern_kit", dict(MACHINE, name="HQ_FirewallMachine")),
    "Mast": ("modern_kit", dict(MACHINE, name="HQ_FirewallMachine")),
    "Ring": ("modern_kit", dict(MACHINE, name="HQ_FirewallMachine")),
    "Console": ("modern_kit", dict(MACHINE, name="HQ_FirewallMachine")),
    "Cable": ("modern_kit", dict(MACHINE, name="HQ_FirewallMachine")),
    "WristGlow": ("glow_ball", {"name": "HQ_FirewallWristGlow", "col": GLOW_A, "strength": 1.0}),
    "Emitters": ("glow_ball", {"name": "HQ_FirewallEmitters", "col": GLOW_A, "strength": 1.2}),
    "Node": ("glow_ball", {"name": "HQ_FirewallNode", "col": (1.0, 0.72, 0.3), "strength": 1.3}),
    "Flare": ("glow_ball", {"name": "HQ_FirewallFlare", "col": (1.0, 0.7, 0.25), "strength": 1.2}),
    "Lights": ("glow_ball", {"name": "HQ_FirewallLights", "col": GLOW_A, "strength": 1.0}),
    "Screen": ("glow_ball", {"name": "HQ_FirewallScreen", "col": (1.0, 0.66, 0.22), "strength": 0.8}),
}
GLOW = {"WristGlow": (GLOW_A, 1.0, 0.5), "Emitters": (GLOW_A, 1.2, 0.5), "Node": ((1.0, 0.72, 0.3), 1.3, 0.6),
        "Flare": ((1.0, 0.7, 0.25), 1.2, 0.6), "Lights": (GLOW_A, 1.1, 0.5), "Screen": ((1.0, 0.66, 0.22), 0.8, 0.5)}
LOW_TARGETS = {"Skin": 5600, "Teeth": 60, "Hair": 1000, "Headset": 1100, "Hoodie": 3400, "Vest": 2000, "Trousers": 1500,
               "Boots": 1200, "Gloves": 1300, "WristRig": 500, "WristGlow": 30, "Machine": 2400, "Mast": 1200, "Ring": 1500,
               "Emitters": 200, "Node": 160, "Flare": 200, "Lights": 80, "Console": 2400, "Cable": 700, "Screen": 60}
AO_EXCLUDE = ["WristRig", "Flare"]
MACHINE_PARTS = ["Machine", "Mast", "Ring", "Console", "Cable"]
# the machine is baked 6 m away from him: his rest pose (his arms out) must leave no shadow on it
BAKE_APART = (MACHINE_PARTS, (6.0, 0.0, 0.0))
YAW_PIVOT = (0.06, -0.04, 0.0)            # the tower turns about this point (keeps the rig, the crates and him on the base)


def prop_bones():
    return []


def extra_bones():
    """machine (the server core, its skid, the crates, keyboard, laptop and cables: deforming nothing of him), mast (the
    mast, the antenna and the emitter ring: it shudders about its foot at the pulse), core (the glowing node: its centre
    is the point the game's hack pulse leaves from, bone_point ALONG 0; it swells as he types and flares at the pulse),
    flare (the ring of light round the emitters: scaled from nothing at the pulse; its head is the ring's centre)."""
    return [("machine", MAST_C + Z * 0.02, MAST_C + Z * 0.3, None),
            ("mast", MAST_C + Z * MAST_Z0, MAST_C + Z * (MAST_Z0 + 0.4), "machine"),
            ("core", CORE_C, CORE_C + Z * 0.15, "mast"),
            ("flare", CORE_C, CORE_C + Z * 0.2, "mast")]


def weight_rules():
    arms = {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Headset": ("rigid", "head"),
        "Hoodie": ("transfer", TORSO | arms | {"neck"}, None),
        "Vest": ("transfer", TORSO, None),
        "Trousers": ("transfer", {"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "WristRig": ("rigid", "forearm.L"), "WristGlow": ("rigid", "forearm.L"),
        "Machine": ("rigid", "machine"), "Mast": ("rigid", "mast"), "Ring": ("rigid", "mast"), "Emitters": ("rigid", "mast"),
        "Node": ("rigid", "core"), "Flare": ("rigid", "flare"), "Lights": ("rigid", "machine"),
        "Console": ("rigid", "machine"), "Cable": ("rigid", "machine"), "Screen": ("rigid", "machine"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Headset", "Hair") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Machine", "Mast", "Ring", "Console", "Cable"):
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.002 if fine else 0.003),
        ("Headset", headset_field(), 0.0016 if fine else 0.0024),
        ("Hoodie", hoodie_field(), 0.0024 if fine else 0.0034),
        ("Vest", vest_field(), 0.0022 if fine else 0.0032),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0022 if fine else 0.003),
        ("Gloves", gloves_field(), 0.0018 if fine else 0.0026),
        ("WristRig", wrist_rig_field(), 0.0016 if fine else 0.0024),
        ("WristGlow", wrist_glow_field(), 0.0012),
        ("Machine", machine_field(), 0.0026 if fine else 0.0036),
        ("Mast", mast_field(), 0.0022 if fine else 0.0032),
        ("Ring", ring_field(), 0.002 if fine else 0.003),
        ("Emitters", emitters_field(), 0.0014),
        ("Node", node_field(), 0.003),
        ("Flare", flare_field(), 0.003),
        ("Lights", lights_field(), 0.0014),
        ("Console", console_field(), 0.002 if fine else 0.003),
        ("Cable", cable_field(), 0.0026),
        ("Screen", screen_field(), 0.0012),
    ]
