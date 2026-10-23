"""The Cryo Field (HQ tower, Digital Age, Control lineage): a cryo field projector and the tech-corps cryo technician who
runs it. Rest pose: he stands in an A-pose facing -Y (the robots), feet at z = 0, the projector behind him on his left
(+X, +Y), its control pedestal before him on his right (-X, -Y); the control lever stands raised.

Him: the Spear Guard's young, athletic body (spear.py), built as the EMP Tower's specialist (emp.py) with his own face:
calm and clever, a smooth oval face, a firm jaw and a rounded chin, level dark brows with a gentle arch, steady dark eyes,
a straight nose, a closed mouth with the faintest smile. Short black hair: cropped close at the sides and the back,
longer on top and swept back. A slim headset (a black band round his head, a pod over each temple) carrying a smoked HUD
visor pushed up onto his hairline (a violet light line along its top edge: `VisorGlow`, its own glowing mesh).
Graphite techwear: a fitted jacket with a high black collar, navy side panels and navy forearms, its sleeves running
into the cuffs of thick insulated gloves (black, padded, navy gauntlet cuffs, hard knuckle plates); a sleek graphite
chest rig (front and back plates on straps, panel lines, two violet light strips down the front plate: `Strips`, their
own glowing mesh) and rounded shoulder plates crusted with frost; a black belt; graphite trousers with a navy stripe down
each leg and black knee plates; black boots. On his left forearm a black wrist display.

The projector (bones `machine`, `mast`, `coils`, `core`, `vapour`): a squat cryogenic tank (brushed steel, navy bands,
frosted round its foot, a hazard diamond) on an octagonal skid crusted with frost; on its domed top a pair of gauges in a
tilted housing (facing him and the camera), a frost-crusted valve with a yellow handwheel, and a vent stack (`vapour`:
the cloud of cold vapour it puffs, `Vapour`, a soft white glowing mesh, scaled to nothing but when it vents). From the
dome the mast: a graphite housing with three violet light strips (`Lights`), fed by two insulated hoses, a gloss-black
pole, and on top the projector ring: six coil cans on spokes round a glowing cryo core (`Core`, on the `core` bone: the
game's frost rings leave its centre), each can with a window on its outer face holding a glowing icy bar (`Coils`, on the
`coils` bone: scaled along its length, bone y, as the field charges), a thin cage of three prongs round the core.

The control pedestal (on `machine`): a black foot plate, a graphite column, a slanted panel (a raised display at its far
edge, `Screen`, glowing pale violet; buttons and lamps), and the control lever (`lever`: a steel arm on a pivot at the
panel's far side with a black T-grip, raised toward him; he slams it down onto the panel to fire); its cable runs over the
floor to the tank's skid.

Painted labels (material mats.modern_kit): 0 graphite (cloth or polymer), 5 black, 6 red (the machine: hazard yellow),
7 frost white, 8 navy, 9 gunmetal, 10 brushed steel, 11 smoked glass, 12 black rubber, 13 violet paint."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
import emp as em
from spear import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R,
                   eye_c, smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, torso_prims, traps, neck_prim,
                   deltoid, eyes_field, TORSO, TORSO_Z, torso_bones)
from emp import arm_prims, leg_prims, shirt_base, _arm_s, _neck_open, _waist_cut, legs_base, foot_hull, vest_base, _octagon

IRIS = ((0.14, 0.09, 0.05), (0.34, 0.22, 0.12))          # dark brown eyes
Z = v3((0.0, 0.0, 1.0))
# labels (mats.modern_kit)
GRAPH, BLACK, RED, FROST, NAVY, GUN, STEEL, GLASS, RUBBER, VIOLET = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13
HAZARD = RED                                              # the machine's material makes label 6 hazard yellow


# ======================================================================================= head
def face_mask(P):
    """His jaw and chin (design coordinates): the faintest shadow of a shave."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.575) + F(0.025) * smoothstep(0.06, 0.15, ax)
    return np.maximum(np.maximum(z - top, F(1.45) - z), y - F(0.02))


def mouth_slot():
    """A closed mouth, its corners lifted a little: the faintest smile."""
    return [hp((-0.049, -0.173, 1.5585)), hp((-0.026, -0.193, 1.5505)), hp((0.0, -0.199, 1.549)), hp((0.026, -0.193, 1.5505)),
            hp((0.049, -0.173, 1.5585))]


def head(fd):
    """Calm and clever: a smooth oval face, a firm jaw and a rounded chin, full young cheeks, level brows with a gentle
    arch (relaxed, not drawn together), steady open eyes, a straight nose, a closed mouth with the faintest smile."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.055, 1.59), (0.128, 0.128, 0.122)), 0.07, SKIN)                           # a firm jaw
    fd.add(E((0, -0.134, 1.502), (0.076, 0.066, 0.064)), 0.05, SKIN)                           # a rounded chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.106, -0.12, 1.632), 0.046), 0.05, SKIN)                                # cheekbones
        fd.add(S((sx * 0.092, -0.142, 1.594), 0.035), 0.04, SKIN)                               # young cheeks
        fd.add(S((sx * 0.117, -0.05, 1.562), 0.045), 0.05, SKIN)                                # jaw corners
        pts = [hp((sx * 0.15, -0.055, 1.742)), hp((sx * 0.114, -0.13, 1.75)), hp((sx * 0.06, -0.172, 1.748)), hp((0.0, -0.182, 1.746))]
        fd.add(Chain(pts, [hr(0.012), hr(0.019), hr(0.022), hr(0.022)], k=hr(0.022)), hr(0.034), SKIN)     # brow ridge
    fd.paint(Func(face_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # level brows with a gentle arch, their inner ends relaxed (a calm look)
    for sx in (-1, 1):
        pts = [hp((sx * 0.022, -0.213, 1.752)), hp((sx * 0.064, -0.206, 1.768)), hp((sx * 0.107, -0.187, 1.772)), hp((sx * 0.148, -0.146, 1.761))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.009), hr(0.011), hr(0.01), hr(0.005)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.016), hr(0.018), hr(0.016), hr(0.009)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0066)), Plane(ec + v3((0, 0, hr(0.024))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0052)), Plane(ec + v3((0, 0, -hr(0.026))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0225))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
    # a straight nose
    fd.add(RoundCone(hp((0, -0.186, 1.726)), hp((0, -0.238, 1.632)), hr(0.014), hr(0.02)), hr(0.016), SKIN)
    fd.add(S((0, -0.24, 1.614), 0.024), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.027, -0.215, 1.603), 0.018), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.015, -0.231, 1.592)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a closed mouth, the corners lifted a little, a full lower lip
    slot = mouth_slot()
    fd.sub(Chain(slot, [hr(0.0024), hr(0.003), hr(0.0033), hr(0.003), hr(0.0024)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.047, -0.171, 1.5615), (-0.026, -0.187, 1.5565), (0.0, -0.191, 1.558), (0.026, -0.187, 1.5565), (0.047, -0.171, 1.5615)]
    lo_lip = [(-0.037, -0.173, 1.546), (-0.02, -0.186, 1.537), (0, -0.19, 1.535), (0.02, -0.186, 1.537), (0.037, -0.173, 1.546)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0045), hr(0.005), hr(0.0045), hr(0.003)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.006), hr(0.0065), hr(0.006), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    for sx in (-1, 1):
        fd.add(S((sx * 0.058, -0.165, 1.566), 0.007), hr(0.006), SKIN)                          # the smile's soft corners
    # ears: a rim, a hollow, a lobe (bare: the headset's pods sit over his temples)
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
        fd.add(RoundBox(hp((sx * 0.009 + 0.003, -0.178, 1.552)), v3((0.008, 0.006, 0.006)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= hair
def _head_d(P):
    """Signed distance (roughly) to the cranium's ellipsoid."""
    q = (P - HEAD_C.astype(F)) / HEAD_RAD.astype(F)
    k0 = np.sqrt((q * q).sum(1))
    k1 = np.sqrt(((q / HEAD_RAD.astype(F)) ** 2).sum(1))
    return k0 * (k0 - F(1)) / np.maximum(k1, F(1e-9))


def hair_thick(P):
    """How far the hair stands off the cranium: cropped close at the sides and the back, longer on top (most at the
    front, where it is swept back)."""
    Q = hinv(P)
    y, z = Q[:, 1], Q[:, 2]
    top = smoothstep(1.77, 1.89, z)
    front = smoothstep(0.1, -0.14, y)
    return (F(0.0045) + F(0.016) * top + F(0.016) * top * front) * F(HS)


# the hairline: its height (design z) by the angle round the head from the front (0) to the back (pi)
_HL_A = np.array([0.0, 0.5, 0.82, 1.02, 1.25, 1.36, 1.86, 2.2, math.pi])
_HL_Z = np.array([1.838, 1.852, 1.795, 1.69, 1.672, 1.738, 1.738, 1.63, 1.6])


def hair_keep(P):
    """< 0 where there is hair (above the hairline, off the face, round the ears)."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    a = np.abs(np.arctan2(x, -(y - F(0.03))))
    zl = np.interp(a, _HL_A, _HL_Z).astype(F) + F(0.004) * np.sin(x * F(70))
    d = (zl - z) * F(0.6)
    for sx in (-1, 1):                                                  # clear of the ears
        e = np.sqrt((x - F(sx * 0.16)) ** 2 + (y - F(0.03)) ** 2 + ((z - F(1.668)) * F(0.8)) ** 2)
        d = np.maximum(d, F(0.068) - e)
    return d


def hair_field():
    """Black hair (label 0): a short crop, swept back on top in fine grooves, close at the sides and the nape."""
    fd = Field("Hair")
    lo, hi = HEAD_C - v3((0.24, 0.26, 0.17)), HEAD_C + v3((0.24, 0.26, 0.26))
    def strands(P):
        Q = hinv(P)
        top = smoothstep(1.78, 1.86, Q[:, 2])
        side = F(0.0006) * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(0.03)) * F(140) + P[:, 2] * F(40))
        swept = F(0.0013) * np.sin(P[:, 0] * F(230) + F(3) * NOISE(P * F(9)) + P[:, 1] * F(25))
        return side * (F(1) - top) + swept * top + F(0.0008) * NOISE(P * F(30))
    def fn(P):
        d = _head_d(P)
        t = hair_thick(P)
        return np.maximum(np.maximum(d - t, -d - F(0.004)), hair_keep(P))
    fd.add(Func(fn, lo, hi, disp=strands, disp_amp=0.002), 0.0)
    return fd


def hair_outer(P):
    """The hair's outer surface (as if hair were everywhere round the cranium): for laying the headset on."""
    return _head_d(P) - hair_thick(P)


# ======================================================================================= the headset and the visor
BAND_F = hp((0.0, -0.205, 1.858))           # the band's front (its middle, under the visor)
BAND_B = hp((0.0, 0.21, 1.70))              # its back (under the occiput)
BAND_N = norm(np.cross(BAND_B - BAND_F, v3((1.0, 0.0, 0.0))))
if BAND_N[2] < 0:
    BAND_N = -BAND_N
BAND_C = lerp(BAND_F, BAND_B, 0.5)


def band_path(n=25, lift=0.006):
    """The headset band's middle line round his head, in the tilted plane through BAND_F and BAND_B, standing `lift` off
    the hair's outer surface. th = 0 at the front, +pi/2 on his left."""
    ex = v3((1.0, 0.0, 0.0))
    ey = norm(np.cross(BAND_N, ex))           # toward the front or back, in the plane
    if (BAND_F - BAND_C) @ ey < 0:
        ey = -ey
    pts, ths = [], []
    for k in range(n):
        th = -math.pi + 2 * math.pi * k / (n - 1)
        d = ey * math.cos(th) + ex * math.sin(th)
        ts = np.linspace(0.32, 0.0, 400)
        Q = (BAND_C[None, :] + ts[:, None] * d[None, :]).astype(F)
        v = hair_outer(Q)
        i = int(np.argmax(v < F(lift)))
        pts.append(v3(Q[i]))
        ths.append(th)
    return pts, ths


def _band_normals(pts):
    return [norm(p - BAND_C) for p in pts]


POD_TH = 1.38                                # the pods sit over his temples, this far round from the front (rad)


def pod_frame(sx):
    """A pod's centre and its outward axis (over the temple, on the band)."""
    pts, ths = band_path(73)
    th = sx * POD_TH
    i = int(np.argmin([abs(t - th) for t in ths]))
    c = pts[i]
    o = norm(c - BAND_C)
    o = norm(o - BAND_N * (o @ BAND_N) * 0.5)
    return c + o * 0.006, o


VIS_A = 1.16                                 # the visor wraps this far round each side from the front (rad)
VIS_LIFT = 0.032                             # pushed up: its middle this far over the band at the front
VIS_W = 0.026                                # its half height


def visor_path(n=17):
    """The visor's middle line (pushed up onto his hairline) and its frames (tangent, outward normal, up across it)."""
    pts, ths = band_path(73, lift=0.012)
    out = []
    for k in range(n):
        th = -VIS_A + 2 * VIS_A * k / (n - 1)
        i = int(np.argmin([abs(t - th) for t in ths]))
        p = pts[i]
        f = math.cos(0.5 * math.pi * th / VIS_A) ** 1.2
        q = p + BAND_N * (VIS_LIFT * f) + v3((0, 0.012 * f, 0))
        # stand clear of the hair
        o = norm(q - BAND_C)
        for _ in range(12):
            v = float(hair_outer(q[None, :].astype(F))[0])
            if v > 0.014:
                break
            q = q + o * 0.003
        out.append(q)
    frames = []
    for k, p in enumerate(out):
        t = norm(out[min(k + 1, n - 1)] - out[max(k - 1, 0)])
        o = norm(p - BAND_C)
        up = norm(BAND_N + o * 0.9 * math.cos(0.5 * math.pi * (-VIS_A + 2 * VIS_A * k / (n - 1)) / VIS_A))   # tipped up
        nrm = norm(np.cross(up, t))
        if nrm @ o < 0:
            nrm = -nrm
        up = norm(np.cross(t, nrm))
        if up[2] < 0:
            up = -up
        frames.append((t, nrm, up))
    return out, frames


def headset_field():
    """Black polymer (5): the band round his head, a pod over each temple (a violet ring painted round its boss); the
    visor pushed up onto his hairline: smoked glass (11) between black rims, black hinges at the pods."""
    fd = Field("Headset")
    pts, ths = band_path(25)
    ns = _band_normals(pts)
    fd.add(Lock(pts, [0.011] * len(pts), [0.0055] * len(pts), ns, k=0.004), 0.0, BLACK)
    for sx in (-1, 1):
        c, o = pod_frame(sx)
        R = rot_from_axes(z_axis=o)
        fd.add(Cylinder(c, 0.03, 0.026, rr=0.011, R=R), 0.005, BLACK)
        fd.add(Cylinder(c + o * 0.014, 0.019, 0.01, rr=0.004, R=R), 0.003, BLACK)
        fd.paint(Inter(Shell(Cylinder(c + o * 0.014, 0.0225, 0.03, R=R), 0.0, 0.004), Plane(c + o * 0.01, -o), 0.001), VIOLET)
    vp, fr = visor_path()
    nrm = [f[1] for f in fr]
    fd.add(Lock(vp, [VIS_W] * len(vp), [0.0045] * len(vp), nrm, k=0.004), 0.0, GLASS)
    for e in (-1, 1):                                            # the rims along its top and bottom edges
        rim = [p + f[2] * (e * (VIS_W - 0.002)) for p, f in zip(vp, fr)]
        fd.add(Chain(rim, [0.0055] * len(rim), k=0.003), 0.003, BLACK)
    for sx, k in ((-1, 0), (1, len(vp) - 1)):                    # the end caps and the hinge arms back to the pods
        c, o = pod_frame(sx)
        fd.add(RoundBox(vp[k], (0.007, 0.006, VIS_W), 0.005, R=np.stack([fr[k][0], fr[k][1], fr[k][2]], axis=1)), 0.004, BLACK)
        fd.add(Chain([vp[k], lerp(vp[k], c, 0.5) + o * 0.006, c + o * 0.01], [0.007, 0.007, 0.008], k=0.004), 0.004, BLACK)
    return fd


def visor_glow_field():
    """The violet light line along the visor's top edge (shipped glowing)."""
    fd = Field("VisorGlow")
    vp, fr = visor_path()
    line = [p + f[2] * (VIS_W - 0.0085) + f[1] * 0.0042 for p, f in zip(vp, fr)][1:-1]
    fd.add(Chain(line, [0.0026] * len(line), k=0.002), 0.0)
    return fd


# ======================================================================================= the techwear jacket
SUIT_OFF, SUIT_T = 0.018, 0.012
SLEEVE_S = 0.235                     # the sleeves end this far down the forearm (inside the gloves' cuffs)


def _sleeve_end(P):
    """> 0 past the sleeves' ends (only round each forearm)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2, L = _arm_s(P, side, 1)
        lateral = P[:, 0] * F(sx) - F(0.42)
        out = np.maximum(out, np.where((lateral > 0) & (d2 < F(0.16 ** 2)), s - F(SLEEVE_S), F(-1.0)))
    return out


def _forearm_part(P, side, s0=0.02):
    """< 0 on the forearm past s0 along it (navy)."""
    s, d2, L = _arm_s(P, side, 1)
    return np.maximum(F(s0) - s, d2 - F(0.14 ** 2))


def suit_field():
    """Graphite techwear (label 0) over his torso and arms, a high black stand collar (5), navy panels down his sides and
    navy forearms (8), violet piping round the collar's top (13)."""
    fd = Field("Suit")
    base = shirt_base()
    lo, hi = (-0.85, -0.42, 0.85), (0.85, 0.45, 1.56)
    def fn(P):
        d = base.eval(P, margin=0.08)
        folds = F(0.0016) * NOISE(P * F(14)) + F(0.001) * NOISE(P * np.array([6, 6, 30], F))
        main = np.abs(d - F(SUIT_OFF) - folds) - F(SUIT_T * 0.5)
        return smax(main, np.maximum(np.maximum(_neck_open(P, 0.122), _sleeve_end(P)), _waist_cut(P)), 0.004)
    fd.add(Func(fn, lo, hi), 0.0, GRAPH)
    # navy side panels (under the arms, down to the waist) and navy forearms
    def sides(P):
        ax = np.abs(P[:, 0])
        return np.maximum(np.maximum(F(0.165) - ax, ax - F(0.36)), np.maximum(F(0.88) - P[:, 2], P[:, 2] - F(1.27)))
    fd.paint(Func(sides, lo, hi), NAVY)
    for side in ("R", "L"):
        fd.paint(Func(lambda P, side=side: _forearm_part(P, side), lo, hi), NAVY)
    # the high stand collar
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    def collar(P):
        z = P[:, 2]
        top = F(1.475) + F(0.035) * smoothstep(-0.04, 0.1, P[:, 1])
        return np.maximum(z - top, F(1.37) - z)
    fd.add(Inter(Shell(nk, 0.022, 0.013, pad=0.1), Func(collar, (-0.4, -0.4, 1.3), (0.4, 0.4, 1.62)), 0.004), 0.004, BLACK)
    def piping(P):
        z = P[:, 2]
        top = F(1.475) + F(0.035) * smoothstep(-0.04, 0.1, P[:, 1])
        return np.maximum(np.abs(z - top + F(0.007)) - F(0.0035), np.abs(nk.eval(P, margin=0.05) - F(0.0285)) - F(0.012))
    fd.paint(Func(piping, (-0.4, -0.4, 1.3), (0.4, 0.4, 1.62)), VIOLET)
    # a seam down the front (a zip line)
    def zip_line(P):
        outer = np.abs(base.eval(P, margin=0.08) - F(SUIT_OFF + SUIT_T * 0.5)) - F(0.004)
        return np.maximum(np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.0016), P[:, 1] + F(0.05)), outer),
                          np.maximum(F(0.9) - P[:, 2], P[:, 2] - F(1.36)))
    fd.sub(Func(zip_line, lo, hi), 0.0015)
    return fd


# ======================================================================================= the chest rig, belt and shoulder plates
RIG_OFF, RIG_T = 0.038, 0.018


def rig_keep(P):
    """< 0 on the chest rig: the front and back plates (shoulders cut in), side straps, two shoulder straps; never round
    his neck."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    top_f = F(1.335) - F(1.1) * np.clip(ax - F(0.09), 0, None) * smoothstep(0.08, 0.2, ax)
    top_b = F(1.37) - F(1.0) * np.clip(ax - F(0.1), 0, None) * smoothstep(0.08, 0.2, ax)
    front = y < F(0.06)
    top = np.where(front, top_f, top_b)
    bot = np.where(front, F(1.075) - F(0.25) * ax * ax, F(1.06))
    plates = np.maximum(np.maximum(ax - F(0.205), z - top), bot - z)
    side = np.maximum(np.abs(z - F(1.13)) - F(0.026), F(0.15) - ax)
    straps = np.maximum(np.maximum(F(0.105) - ax, ax - F(0.185)), F(1.2) - z)
    keep = np.minimum(np.minimum(plates, side), straps)
    return np.maximum(keep, _neck_open(P, 0.13))


def rig_outer():
    vb = vest_base()
    return Func(lambda P: vb.eval(P, margin=0.12) - F(RIG_OFF + RIG_T * 0.5 + 0.001), (-1, -1, 0.6), (1, 1, 1.8))


STRIP_X = (-0.075, 0.075)                   # the light strips down the front plate
STRIP_Z = (1.165, 1.3)


def strip_line(x, out=0.0):
    """Points down the front plate's surface at x (from its top to the strip's foot), `out` off the surface."""
    vo = rig_outer()
    pts = []
    for z in np.linspace(STRIP_Z[1], STRIP_Z[0], 6):
        h, ok = ray_hit(vo, [v3((x, -0.6, z))], [v3((0, 1, 0))], tmax=0.6)
        p = h[0] if ok[0] else v3((x, -0.2, z))
        pts.append(p + v3((0, -out, 0)))
    return pts


def armor_field():
    """Sleek graphite polymer (label 0): the chest rig's front and back plates with panel lines, a navy band across the
    front plate's foot (8), black side straps (5), slots down the front plate for the light strips; a black belt (5)
    with a steel buckle (10); a small black pack on his back."""
    fd = Field("Armor")
    base = vest_base()
    lo, hi = (-0.6, -0.5, 0.85), (0.6, 0.55, 1.62)
    def fn(P):
        d = base.eval(P, margin=0.12)
        ax = np.abs(P[:, 0])
        plate = smoothstep(0.23, 0.17, ax)
        off = F(RIG_OFF) - F(0.014) * (F(1) - plate)
        sh = np.abs(d - off) - F(RIG_T * 0.5) + F(0.006) * (F(1) - plate)
        return smax(sh, rig_keep(P), 0.006)
    fd.add(Func(fn, lo, hi, disp=lambda P: F(0.0004) * NOISE(P * F(40)), disp_amp=0.0006), 0.0, GRAPH)
    # black side straps and shoulder straps
    def straps(P):
        ax = np.abs(P[:, 0])
        side = np.maximum(np.abs(P[:, 2] - F(1.13)) - F(0.03), F(0.2) - ax)
        sh = np.maximum(np.maximum(F(0.1) - ax, ax - F(0.19)), F(1.31) - P[:, 2])
        return np.minimum(side, np.where(P[:, 1] < F(0.06), sh, F(1.0)))
    fd.paint(Func(straps, lo, hi), BLACK)
    # the navy band across the front plate's foot
    fd.paint(Func(lambda P: np.maximum(np.maximum(P[:, 2] - F(1.125), P[:, 1] + F(0.02)), np.abs(P[:, 0]) - F(0.21)), lo, hi), NAVY)
    vo = rig_outer()
    # panel lines: across the front plate, down its middle, round the strips
    def lines(P):
        d = np.abs(vo(P))
        z, x = P[:, 2], P[:, 0]
        across = np.abs(z - F(1.14)) - F(0.0018)
        mid = np.maximum(np.abs(x) - F(0.0018), np.maximum(F(1.14) - z, z - F(1.33)))
        g = np.minimum(across, mid)
        return np.maximum(np.maximum(g, d - F(0.006)), P[:, 1] + F(0.02))
    fd.sub(Func(lines, lo, hi), 0.0015)
    for x in STRIP_X:                                           # the light strips' slots
        pts = strip_line(x)
        fd.sub(Chain(pts, [0.0075] * len(pts), k=0.002), 0.002)
    # the belt
    hip = Field("Hip")
    tp = torso_prims()
    hip.add(tp[4][0], 0.0)
    hip.add(tp[5][0], 0.08)
    def belt(P):
        d = hip.eval(P, margin=0.1)
        return np.maximum(np.abs(d - F(0.034)) - F(0.009), np.abs(P[:, 2] - F(0.955)) - F(0.024))
    fd.add(Func(belt, (-0.45, -0.4, 0.88), (0.45, 0.45, 1.03)), 0.0, BLACK)
    h, ok = ray_hit(Func(lambda P: hip.eval(P, margin=0.12) - F(0.044), (-0.5, -0.6, 0.85), (0.5, 0.5, 1.05)), [v3((0, -0.6, 0.955))], [v3((0, 1, 0))], tmax=0.6)
    if ok[0]:
        fd.add(RoundBox(h[0] + v3((0, -0.006, 0)), (0.036, 0.008, 0.026), 0.006), 0.003, STEEL)
    # a small black pack on his back (a power cell), a violet line painted across it
    h, ok = ray_hit(vo, [v3((0.0, 0.7, 1.2))], [v3((0, -1, 0))], tmax=0.7)
    pc = (h[0] if ok[0] else v3((0.0, 0.26, 1.2))) + v3((0, 0.04, 0))
    R = euler(0.08, 0, 0)
    fd.add(RoundBox(pc, (0.1, 0.04, 0.11), 0.03, R=R), 0.008, BLACK)
    fd.add(RoundBox(pc + v3((0, 0.03, 0.0)), (0.075, 0.016, 0.085), 0.012, R=R), 0.004, GRAPH)
    fd.paint(RoundBox(pc + v3((0, 0.05, 0.03)), (0.06, 0.03, 0.007), 0.003, R=R), VIOLET)
    return fd


def strips_field():
    """The violet light strips down the front plate (shipped glowing)."""
    fd = Field("Strips")
    for x in STRIP_X:
        pts = strip_line(x, out=-0.001)
        fd.add(Chain(pts, [0.0058] * len(pts), k=0.002), 0.0)
    return fd


def pauldron_axis(sx):
    return norm(v3((sx * 1.0, 0.02, 0.95)))


PAUL_R = 0.158                              # the shoulder plates' radius (from the deltoid's centre)


def pauldrons_field():
    """Rounded graphite shoulder plates (0) over the jacket, a black lip round each (5), a navy band (8) and a violet
    stripe (13) on their outer faces; their tops crusted with frost (7)."""
    fd = Field("Pauldrons")
    rs = np.random.RandomState(17)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        dl = deltoid(side)
        c = dl.c + v3((sx * 0.004, 0.0, -0.005))
        a = pauldron_axis(sx)
        cosmax = math.cos(math.radians(66))
        def cap(P, c=c, a=a):
            q = P - c.astype(F)
            r = np.sqrt((q * q).sum(1)) + F(1e-6)
            return (F(cosmax) - (q @ a.astype(F)) / r) * F(0.16)
        shell = Shell(Sphere(c, PAUL_R), 0.0, 0.018)
        fd.add(Inter(shell, Func(cap, c - 0.3, c + 0.3), 0.006), 0.0, GRAPH)
        Ra = rot_from_axes(z_axis=a)
        rim_c = c + a * (PAUL_R * cosmax)
        fd.add(Torus(rim_c, PAUL_R * math.sin(math.radians(66)) + 0.002, 0.011, R=Ra), 0.005, BLACK)
        # a second, smaller plate below its rim, down the arm (a lame)
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ua = norm(el - sh)
        lc = sh + ua * 0.11
        ring = Torus(lc, 0.112, 0.016, R=rot_from_axes(z_axis=ua))
        fd.add(Inter(ring, Func(lambda P, lc=lc, sx=sx: (F(0.0) - (P[:, 0] - F(lc[0])) * F(sx)) - F(0.0), lc - 0.3, lc + 0.3), 0.01), 0.004, GRAPH)
        # navy band and violet stripe on the outer face
        def band(P, c=c, a=a, w=0.012, at=0.75):
            q = P - c.astype(F)
            r = np.sqrt((q * q).sum(1)) + F(1e-6)
            cs = (q @ a.astype(F)) / r
            return np.maximum(np.abs(cs - F(at)) * F(0.16) - F(w), np.abs(r - F(PAUL_R)) - F(0.03))
        fd.paint(Func(lambda P: band(P, w=0.016, at=0.62), c - 0.3, c + 0.3), NAVY)
        fd.paint(Func(lambda P: band(P, w=0.0045, at=0.62), c - 0.3, c + 0.3), VIOLET)
        # frost: painted over the top, crusted in lumps
        def frost(P, c=c):
            q = P - c.astype(F)
            n = F(0.03) * NOISE(P * F(16)) + F(0.015) * NOISE(P * F(40))
            return F(0.075) + n - q[:, 2]
        fd.paint(Func(frost, c - 0.3, c + 0.3), FROST)
        for k in range(9):
            u = rs.uniform(0, 2 * math.pi)
            t = rs.uniform(0.0, 0.5)
            d = norm(Z * math.cos(t) + (v3((math.cos(u), math.sin(u), 0.0))) * math.sin(t))
            p = c + d * (PAUL_R + 0.006)
            fd.add(Ellipsoid(p, (rs.uniform(0.022, 0.036), rs.uniform(0.02, 0.032), rs.uniform(0.008, 0.013)), R=rot_from_axes(z_axis=d),
                             disp=lambda P: F(0.003) * NOISE(P * F(60)), disp_amp=0.004), 0.012, FROST)
    return fd


# ======================================================================================= trousers, boots, gloves, wrist display
def trousers_field():
    """Graphite techwear (label 0) from his waist into his boots, a navy stripe down the outside of each leg (8), black
    knee plates (5), a flat pocket on each thigh."""
    fd = Field("Trousers")
    lb = legs_base()
    lo, hi = v3((-0.5, -0.4, 0.15)), v3((0.5, 0.45, 1.06))
    def fn(P):
        d = lb.eval(P, margin=0.08)
        off = F(0.014) + F(0.008) * smoothstep(0.5, 0.3, P[:, 2])
        return np.abs(d - off) - F(0.0065)
    wr = lambda P: F(0.0014) * NOISE(P * np.array([30, 30, 60], F)) + F(0.002) * np.sin(P[:, 2] * F(80) + F(2) * NOISE(P * F(5))) * smoothstep(0.52, 0.4, P[:, 2]) * smoothstep(0.3, 0.38, P[:, 2])
    fd.add(Inter(Func(fn, lo, hi, disp=wr, disp_amp=0.004), Func(lambda P: np.maximum(F(0.24) - P[:, 2], P[:, 2] - F(0.975)), lo, hi), 0.004), 0.0, GRAPH)
    # the navy stripes down the outsides
    def stripe(P):
        u = np.abs(P[:, 0]) - F(0.155) - (F(0.025) - F(0.03) * (P[:, 2] - F(0.4)))
        return np.maximum(np.maximum(np.abs(P[:, 1] - F(0.03)) - F(0.032), F(0.11) - np.abs(P[:, 0])), np.maximum(F(0.26) - P[:, 2], P[:, 2] - F(0.96)))
    fd.paint(Func(stripe, lo, hi), NAVY)
    surf = Func(lambda P: lb.eval(P, margin=0.12) - F(0.022), (-0.6, -0.5, 0.2), (0.6, 0.5, 1.1))
    for sx in (-1, 1):
        side = "R" if sx < 0 else "L"
        # a flat thigh pocket
        h, ok = ray_hit(surf, [v3((sx * 0.6, -0.04, 0.64))], [v3((-sx, 0.3, 0))], tmax=0.6)
        if ok[0]:
            c = h[0]
            out = norm(v3((sx, -0.35, 0)))
            R = rot_from_axes(y_axis=out, z_axis=Z)
            fd.add(RoundBox(c + out * 0.004, (0.06, 0.012, 0.075), 0.01, R=R), 0.006, GRAPH)
            fd.add(RoundBox(c + out * 0.012 + Z * 0.062, (0.064, 0.01, 0.018), 0.007, R=R), 0.004, BLACK)
        # the knee plate
        kn, hip, an = J["knee_" + side], J["hip_" + side], J["ankle_" + side]
        h, ok = ray_hit(surf, [kn + v3((0, -0.5, 0.0))], [v3((0, 1, 0))], tmax=0.6)
        kc = h[0] if ok[0] else kn + v3((0, -0.1, 0))
        ax = norm(hip - an)
        Rk = rot_from_axes(y_axis=norm(v3((0, -1, 0)) - ax * (v3((0, -1, 0)) @ ax)), z_axis=ax)
        fd.add(Ellipsoid(kc + v3((0, 0.012, 0.0)), (0.07, 0.026, 0.085), R=Rk), 0.008, BLACK)
        fd.sub(Torus(kc + v3((0, -0.012, 0.0)), 0.045, 0.003, R=Rk @ rot_from_axes(z_axis=(0, 1, 0))), 0.002)
    return fd


def boots_field():
    fd = em.boots_field()
    return fd


GLOVE_CUFF = (-0.1, 0.028)                   # the gauntlet cuffs: from this far up the forearm to past the wrist (along it)


def gloves_field():
    """Thick insulated gloves: padded black (5) over his fists, hard knuckle plates (0), long navy gauntlet cuffs (8)
    flaring up the forearm with ribbed bands (5)."""
    fd = Field("Gloves")
    for side in ("R", "L"):
        hh = Field("HandHull")
        hand(hh, side)
        fd.add(Shell(hh, 0.0095, 0.013, pad=0.05, disp=lambda P: F(0.0012) * NOISE(P * F(40)), disp_amp=0.0015), 0.0, BLACK)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        def cuff(P, wr=wr, ax=ax):
            s = (P - wr.astype(F)) @ ax.astype(F)
            q = P - wr.astype(F) - s[:, None] * ax.astype(F)[None, :]
            rho = np.sqrt((q * q).sum(1))
            r = F(0.081) - F(0.12) * np.clip(s, None, 0) * F(1.0)
            return np.maximum(np.abs(rho - r) - F(0.0075), np.maximum(F(GLOVE_CUFF[0]) - s, s - F(GLOVE_CUFF[1])))
        fd.add(Func(cuff, wr - 0.3, wr + 0.3), 0.01, NAVY)
        for s0 in (-0.085, 0.012):                                # ribbed bands at the cuff's ends
            r = 0.081 - 0.12 * min(s0, 0.0)
            fd.add(Torus(wr + ax * s0, r + 0.002, 0.007, R=rot_from_axes(z_axis=ax)), 0.004, BLACK)
        wrf, f, n, t = hand_frame(side)
        h, ok = ray_hit(hh, [wrf + f * 0.115 - n * 0.3], [n], tmax=0.4)
        kc = (h[0] if ok[0] else wrf + f * 0.115 - n * 0.06) - n * 0.02
        Rk = np.stack([t, -n, f], axis=1)
        fd.add(RoundBox(kc, (0.064, 0.009, 0.032), 0.009, R=Rk), 0.008, GRAPH)
        fd.add(RoundBox(kc - n * 0.004 - f * 0.065, (0.05, 0.008, 0.03), 0.009, R=Rk), 0.008, GRAPH)        # the back of the hand
    return fd


def pad_frame():
    """(centre on the left sleeve, along (toward the wrist), out (its face), across)."""
    el, wr = J["elbow_L"], J["wrist_L"]
    ax = norm(wr - el)
    out = norm(v3((1.0, -0.35, 0.6)) - ax * float(v3((1.0, -0.35, 0.6)) @ ax))
    c = lerp(el, wr, 0.42)
    fd = Field("Fa")
    for p, k in arm_prims("L")[3:5]:
        fd.add(p, k)
    sv = Func(lambda P: fd.eval(P, margin=0.06) - F(SUIT_OFF + SUIT_T * 0.5), c - 0.3, c + 0.3)
    h, ok = ray_hit(sv, [c + out * 0.3], [-out], tmax=0.4)
    surf = h[0] if ok[0] else c + out * 0.09
    return surf, ax, out, norm(np.cross(out, ax))


def pad_field():
    """A black wrist display on his left forearm (5): a smoked screen (11) with a violet line across it (13), two straps."""
    fd = Field("Pad")
    c, ax, out, acr = pad_frame()
    R = np.stack([acr, ax, out], axis=1)
    fd.add(RoundBox(c + out * 0.012, (0.04, 0.052, 0.011), 0.008, R=R), 0.0, BLACK)
    fd.paint(RoundBox(c + out * 0.022, (0.029, 0.038, 0.006), 0.004, R=R), GLASS)
    fd.sub(RoundBox(c + out * 0.025, (0.03, 0.039, 0.002), 0.003, R=R), 0.002)
    fd.paint(RoundBox(c + out * 0.022 + ax * 0.012, (0.022, 0.004, 0.01), 0.002, R=R), VIOLET)
    for e in (-1, 1):
        sc = c + ax * (e * 0.03) - out * 0.075
        fd.add(Inter(Shell(Cylinder(sc, 0.087, 0.03, R=rot_from_axes(z_axis=ax)), 0.0, 0.006),
                     Func(lambda P, sc=sc: np.abs((P - sc.astype(F)) @ ax.astype(F)) - F(0.011), sc - 0.14, sc + 0.14), 0.002), 0.003, BLACK)
    return fd


# ======================================================================================= the projector (machine)
MAST_C = v3((0.56, 0.3, 0.0))             # the mast's axis at the floor
FRONT = norm(v3((-0.45, -1.0, 0.0)))       # the camera's side
TOWARD = norm(v3((-MAST_C[0], -MAST_C[1], 0.0)))        # toward him
GAUGE_D = norm(FRONT + TOWARD)             # the gauges face between him and the camera
ACROSS_G = norm(np.cross(Z, GAUGE_D))
VALVE_D = norm(v3((0.74, -0.67, 0.0)))     # the valve: on the camera's right of the dome
VENT_D = norm(v3((0.95, 0.3, 0.0)))        # the vent stack: outward, away from him
DECK_R, DECK_H = 0.3, 0.05
TANK_R = 0.24
TANK_Z1 = 0.58                             # the cylinder's top (the dome rises above it)
DOME_H = 0.1
TANK_TOP = TANK_Z1 + DOME_H
HOUSE_Z0, HOUSE_Z1, HOUSE_R = 0.66, 1.03, 0.086
POLE_Z1, POLE_R = 1.74, 0.042
RING_Z = 1.9                               # the projector ring's plane = the core's centre (the pulse's origin)
RING_R = 0.235
POD_N, POD_R, POD_HH = 6, 0.05, 0.1
POD_A0 = math.atan2(FRONT[1], FRONT[0])    # a pod faces the camera
CORE_R = 0.07
CORE_C = MAST_C + Z * RING_Z
BAR_HH = 0.072                             # the coil windows' glowing bars' half length (full)
LIGHT_A = (0.0, 2.1, -2.1)                 # the housing's light strips (angles from FRONT)
LIGHT_Z = (0.72, 0.98)
GAUGE_C = MAST_C + GAUGE_D * 0.19 + Z * 0.79
GAUGE_N = norm(GAUGE_D + Z * 0.85)


def dome_z(r):
    return TANK_Z1 + DOME_H * math.sqrt(max(0.0, 1.0 - (r / TANK_R) ** 2))


def gauge_frame():
    up = norm(np.cross(GAUGE_N, ACROSS_G))
    if up[2] < 0:
        up = -up
    return np.stack([ACROSS_G, up, GAUGE_N], axis=1)


GAUGE_PTS = [GAUGE_C + GAUGE_N * 0.03 + ACROSS_G * (e * 0.042) for e in (-1, 1)]    # the two dials' centres (his tap)
VENT_P = MAST_C + VENT_D * 0.285 + Z * 0.76                                          # the vent's mouth
VENT_DIR = norm(VENT_D * 0.55 + Z)


def _frost_blobs(fd, rs, centre_fn, n, size, k=0.012):
    for i in range(n):
        p, d = centre_fn(rs)
        a, b, c = (rs.uniform(*s) for s in size)
        fd.add(Ellipsoid(p, (a, b, c), R=rot_from_axes(z_axis=d), disp=lambda P: F(0.003) * NOISE(P * F(55)), disp_amp=0.004), k, FROST)


def machine_field():
    """On `machine`: the skid (gunmetal 9, steel bolts 10) crusted with frost round the tank's foot (7); the tank
    (brushed steel 10, navy bands 8, frost painted round its foot, a hazard diamond 6 with a black snowflake 5, a grille of
    vents); the gauges (a graphite housing, steel bezels, white faces, black needles, violet sectors), the valve (steel,
    a gunmetal body, a yellow handwheel 6, frost), the vent stack; black lifting lugs."""
    fd = Field("Machine")
    c = MAST_C
    rv = lambda P: F(0.0005) * NOISE(P * F(50))
    rs = np.random.RandomState(23)
    fd.add(Func(lambda P: _octagon(P, c, DECK_R, DECK_H, 0.0), c - 0.4, c + 0.4, disp=rv, disp_amp=0.001), 0.0, GUN)
    for k in range(8):
        a = 2 * math.pi * k / 8
        fd.add(Sphere(c + v3((math.cos(a), math.sin(a), 0)) * (DECK_R - 0.028) + Z * DECK_H, 0.01), 0.002, STEEL)
    # the tank
    brushed = lambda P: F(0.0004) * np.sin(P[:, 2] * F(900) + F(4) * NOISE(P * F(20)))
    fd.add(Cylinder(c + Z * ((DECK_H + TANK_Z1) / 2), TANK_R, TANK_Z1 - DECK_H, rr=0.03, disp=brushed, disp_amp=0.0006), 0.01, STEEL)
    fd.add(Ellipsoid(c + Z * TANK_Z1, (TANK_R, TANK_R, DOME_H)), 0.03, STEEL)
    for zz in (0.17, 0.47):
        fd.add(Torus(c + Z * zz, TANK_R + 0.002, 0.014), 0.006, NAVY)
    fd.add(Torus(c + Z * (DECK_H + 0.02), TANK_R + 0.006, 0.016), 0.006, GUN)                  # its foot ring
    # frost painted round its foot
    def frost_paint(P):
        q = P - c.astype(F)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        h = F(0.15) + F(0.06) * NOISE(P * F(7)) + F(0.03) * NOISE(P * F(22))
        return np.maximum(P[:, 2] - h, F(TANK_R - 0.05) - r)
    fd.paint(Func(frost_paint, c - 0.4, c + 0.4), FROST)
    # the hazard diamond on its front, a black snowflake on it
    hd = norm(FRONT + v3((0.5, 0.0, 0.0)))
    hc = c + hd * TANK_R + Z * 0.32
    Rh = rot_from_axes(z_axis=hd, y_axis=Z)
    hx = norm(np.cross(Z, hd))
    def diamond(P, s=0.058):
        q = P - hc.astype(F)
        u, v = q @ hx.astype(F), q @ Z.astype(F)
        return np.maximum(np.abs(u) + np.abs(v) - F(s), np.abs(q @ hd.astype(F)) - F(0.03))
    fd.paint(Func(diamond, hc - 0.12, hc + 0.12), HAZARD)
    def flake(P):
        q = P - hc.astype(F)
        u, v = q @ hx.astype(F), q @ Z.astype(F)
        d = F(1.0) * np.ones(len(P), F)
        for a in (0.0, math.pi / 3, -math.pi / 3):
            ca, sa = F(math.cos(a)), F(math.sin(a))
            along = u * sa + v * ca
            acr = u * ca - v * sa
            d = np.minimum(d, np.maximum(np.abs(acr) - F(0.0045), np.abs(along) - F(0.03)))
        return np.maximum(d, np.abs(q @ hd.astype(F)) - F(0.03))
    fd.paint(Func(flake, hc - 0.12, hc + 0.12), BLACK)
    # vents for the cold vapour: a grille of slits on its outer side
    for k in range(5):
        vc = c + VENT_D * (TANK_R + 0.002) + Z * (0.25 + 0.04 * k)
        fd.sub(RoundBox(vc, (0.012, 0.06, 0.008), 0.005, R=rot_from_axes(x_axis=VENT_D, z_axis=Z)), 0.003)
    fd.add(RoundBox(c + VENT_D * (TANK_R - 0.004) + Z * 0.33, (0.012, 0.075, 0.115), 0.01, R=rot_from_axes(x_axis=VENT_D, z_axis=Z)), 0.004, GUN)
    for k in range(5):
        vc = c + VENT_D * (TANK_R + 0.009) + Z * (0.25 + 0.04 * k)
        fd.sub(RoundBox(vc, (0.012, 0.058, 0.008), 0.005, R=rot_from_axes(x_axis=VENT_D, z_axis=Z)), 0.003)
    # lifting lugs on the dome
    for a in (0.9, 0.9 + math.pi):
        d = v3((math.cos(a), math.sin(a), 0))
        p = c + d * 0.2 + Z * (dome_z(0.2) + 0.012)
        fd.add(Torus(p, 0.02, 0.0065, R=rot_from_axes(z_axis=np.cross(Z, d))), 0.003, BLACK)
    # the gauges: a stalk from the dome, a tilted housing, two dials
    Rg = gauge_frame()
    base = c + GAUGE_D * 0.17 + Z * dome_z(0.17)
    fd.add(RoundCone(base - Z * 0.01, GAUGE_C - GAUGE_N * 0.01, 0.024, 0.02), 0.006, GUN)
    fd.add(RoundBox(GAUGE_C, (0.098, 0.052, 0.022), 0.014, R=Rg), 0.004, GRAPH)
    for e, p in zip((-1, 1), GAUGE_PTS):
        fd.add(Torus(p, 0.035, 0.0065, R=Rg), 0.003, STEEL)
        fd.add(Cylinder(p - GAUGE_N * 0.002, 0.034, 0.008, rr=0.003, R=Rg), 0.003, FROST)
        # a violet sector and the needle
        ang0 = 0.6 if e < 0 else 1.1
        def sector(P, p=p):
            q = P - p.astype(F)
            u, v = q @ ACROSS_G.astype(F), q @ Rg[:, 1].astype(F)
            r = np.sqrt(u * u + v * v)
            a = np.arctan2(v, u)
            return np.maximum(np.maximum(np.abs(r - F(0.025)) - F(0.005), np.abs(a - F(0.55)) * F(0.03) - F(0.012)), np.abs(q @ GAUGE_N.astype(F)) - F(0.01))
        fd.paint(Func(sector, p - 0.06, p + 0.06), VIOLET)
        nd = norm(ACROSS_G * math.cos(ang0 + 0.9) + Rg[:, 1] * math.sin(ang0 + 0.9))
        fd.add(RoundCone(p + GAUGE_N * 0.003 - nd * 0.004, p + GAUGE_N * 0.003 + nd * 0.024, 0.0035, 0.0022), 0.001, BLACK)
        fd.add(Sphere(p + GAUGE_N * 0.003, 0.005), 0.001, BLACK)
    # the valve: a pipe up from the dome, the valve's body, the handwheel; frost crusted on it
    vb = c + VALVE_D * 0.15
    vz = dome_z(0.15)
    fd.add(Cylinder(vb + Z * (vz + 0.04), 0.022, 0.1, rr=0.006), 0.006, STEEL)
    fd.add(Cylinder(vb + Z * (vz + 0.075), 0.034, 0.05, rr=0.012), 0.006, GUN)
    fd.add(Cylinder(vb + Z * (vz + 0.115), 0.008, 0.05, rr=0.003), 0.003, STEEL)
    wc = vb + Z * (vz + 0.135)
    fd.add(Torus(wc, 0.055, 0.0095), 0.003, HAZARD)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.3
        d = v3((math.cos(a), math.sin(a), 0))
        fd.add(RoundCone(wc, wc + d * 0.052, 0.007, 0.006), 0.003, HAZARD)
    fd.add(Sphere(wc, 0.012), 0.003, GUN)
    def vfrost(rs):
        u = rs.uniform(0, 2 * math.pi)
        z = rs.uniform(vz + 0.0, vz + 0.1)
        rr = 0.024 if z < vz + 0.05 else 0.034
        d = v3((math.cos(u), math.sin(u), 0))
        return vb + d * rr + Z * z, norm(d + Z * 0.3)
    _frost_blobs(fd, rs, vfrost, 10, ((0.014, 0.024), (0.012, 0.02), (0.007, 0.011)), k=0.008)
    def wfrost(rs):
        u = rs.uniform(0, 2 * math.pi)
        d = v3((math.cos(u), math.sin(u), 0))
        return wc + d * 0.055 + Z * 0.004, norm(Z + d * 0.4)
    _frost_blobs(fd, rs, wfrost, 7, ((0.012, 0.02), (0.01, 0.016), (0.006, 0.009)), k=0.006)
    # the vent stack: out of the dome's edge, its flared mouth up and out
    vs = c + VENT_D * 0.19 + Z * (dome_z(0.19) - 0.01)
    fd.add(Chain([vs, vs + Z * 0.05 + VENT_D * 0.03, VENT_P - VENT_DIR * 0.03], [0.026, 0.024, 0.024], k=0.01), 0.008, GUN)
    fd.add(RoundCone(VENT_P - VENT_DIR * 0.035, VENT_P, 0.026, 0.036), 0.006, STEEL)
    fd.sub(RoundCone(VENT_P - VENT_DIR * 0.03, VENT_P + VENT_DIR * 0.02, 0.016, 0.027), 0.004)
    fd.add(Torus(VENT_P - VENT_DIR * 0.004, 0.034, 0.005, R=rot_from_axes(z_axis=VENT_DIR)), 0.003, HAZARD)
    # frost crusted on the skid round the tank's foot
    def dfrost(rs):
        u = rs.uniform(0, 2 * math.pi)
        d = v3((math.cos(u), math.sin(u), 0))
        return c + d * (TANK_R + rs.uniform(-0.005, 0.04)) + Z * (DECK_H + 0.004), norm(Z + d * 0.5)
    _frost_blobs(fd, rs, dfrost, 26, ((0.03, 0.055), (0.022, 0.04), (0.012, 0.024)), k=0.014)
    def deck_paint(P):
        q = P - c.astype(F)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        return np.maximum(r - F(TANK_R + 0.05) - F(0.02) * NOISE(P * F(14)), P[:, 2] - F(DECK_H + 0.04))
    fd.paint(Func(deck_paint, c - 0.4, c + 0.4), FROST)
    # the console's cable arriving at the skid: a gland on its edge
    gd = norm(v3((CON_P[0] - c[0], CON_P[1] - c[1], 0.0)))
    fd.add(Cylinder(c + gd * (DECK_R - 0.02) + Z * (DECK_H + 0.022), 0.028, 0.045, rr=0.008), 0.004, GUN)
    return fd


def _pod_c(k):
    a = POD_A0 + 2 * math.pi * k / POD_N
    d = v3((math.cos(a), math.sin(a), 0.0))
    return MAST_C + d * RING_R + Z * RING_Z, d


def mast_field():
    """On `mast`: the collar on the dome (gunmetal 9), the housing (graphite 0) with slots for its three light strips and a
    grille, the two insulated hoses from the dome into it (black rubber 12, frosted at their feet 7), the gloss-black pole
    (5) and its collars, up to the ring's hub."""
    fd = Field("Mast")
    c = MAST_C
    rv = lambda P: F(0.0005) * NOISE(P * F(50))
    fd.add(Cylinder(c + Z * (TANK_TOP - 0.005), 0.115, 0.045, rr=0.015), 0.0, GUN)
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        fd.add(Sphere(c + v3((math.cos(a), math.sin(a), 0)) * 0.1 + Z * (TANK_TOP + 0.015), 0.009), 0.002, STEEL)
    fd.add(Cylinder(c + Z * ((HOUSE_Z0 + HOUSE_Z1) / 2), HOUSE_R, HOUSE_Z1 - HOUSE_Z0, rr=0.025, disp=rv, disp_amp=0.001), 0.008, GRAPH)
    for zz in (HOUSE_Z0 + 0.06, HOUSE_Z1 - 0.012):
        fd.add(Cylinder(c + Z * zz, HOUSE_R + 0.008, 0.024, rr=0.008), 0.004, BLACK)
    for a in LIGHT_A:                                            # the light strips' slots
        ang = POD_A0 + a
        d = v3((math.cos(ang), math.sin(ang), 0))
        sc = c + d * HOUSE_R + Z * ((LIGHT_Z[0] + LIGHT_Z[1]) / 2)
        fd.sub(RoundBox(sc, (0.009, 0.012, (LIGHT_Z[1] - LIGHT_Z[0]) / 2), 0.006, R=rot_from_axes(y_axis=d, z_axis=Z)), 0.002)
    # a grille on its back
    bd = -norm(FRONT)
    for k in range(6):
        fd.sub(RoundBox(c + bd * HOUSE_R + Z * (0.76 + 0.03 * k), (0.045, 0.012, 0.006), 0.004, R=rot_from_axes(y_axis=bd, z_axis=Z)), 0.002)
    # two insulated hoses from the dome into the housing
    for e in (-1, 1):
        a = POD_A0 + math.pi + e * 1.15
        d = v3((math.cos(a), math.sin(a), 0))
        p0 = c + d * 0.17 + Z * (dome_z(0.17) - 0.01)
        p3 = c + d * (HOUSE_R - 0.01) + Z * (HOUSE_Z1 - 0.07)
        pts = [p0, p0 + Z * 0.06 + d * 0.035, c + d * 0.2 + Z * 0.86, c + d * 0.15 + Z * 0.96, p3]
        rib = lambda P, pts=pts: F(0.0025) * np.sin(P[:, 2] * F(260) + (P[:, 0] + P[:, 1]) * F(120))
        fd.add(Chain(pts, [0.026] * len(pts), k=0.012, disp=rib, disp_amp=0.003), 0.006, RUBBER)
        fd.add(Cylinder(p0 + Z * 0.012, 0.034, 0.03, rr=0.008), 0.004, STEEL)
        fd.add(Sphere(p3, 0.032), 0.004, STEEL)
        def hfrost(P, p0=p0):
            return np.sqrt(((P - p0.astype(F)) ** 2).sum(1)) - F(0.11) - F(0.03) * NOISE(P * F(20))
        fd.paint(Func(hfrost, p0 - 0.2, p0 + 0.2), FROST)
    # the pole, its collars
    fd.add(Cylinder(c + Z * ((HOUSE_Z1 + POLE_Z1) / 2), POLE_R, POLE_Z1 - HOUSE_Z1, rr=0.01), 0.006, BLACK)
    for zz, rr in ((HOUSE_Z1 + 0.02, 0.06), (1.38, 0.055)):
        fd.add(Cylinder(c + Z * zz, rr, 0.034, rr=0.01), 0.005, GUN)
    fd.add(RoundCone(c + Z * (POLE_Z1 - 0.06), c + Z * (POLE_Z1 + 0.02), POLE_R, 0.07), 0.01, GUN)
    return fd


def ring_field():
    """On `mast`: the projector ring: the hub and its six spokes, the coil cans (black caps, navy windings 8, black window
    frames with slots for the glowing bars), the rings over and under them (gunmetal 9), the cup under the core and the
    cage of three prongs round it (gunmetal, steel tips 10)."""
    fd = Field("Ring")
    c = MAST_C
    hub = c + Z * (POLE_Z1 + 0.02)
    fd.add(Cylinder(hub, 0.075, 0.05, rr=0.016), 0.0, GUN)
    fd.add(RoundCone(c + Z * (POLE_Z1 - 0.03), hub, POLE_R + 0.004, 0.07), 0.01, GUN)
    wind = lambda P: F(0.0016) * np.sin(P[:, 2] * F(260))
    for k in range(POD_N):
        pc, d = _pod_c(k)
        bot = pc - Z * (POD_HH + 0.01)
        fd.add(RoundCone(hub + d * 0.05, bot - d * 0.02, 0.016, 0.014), 0.006, BLACK)          # a spoke
        fd.add(Cylinder(pc, POD_R, 2 * POD_HH - 0.05, rr=0.012, disp=wind, disp_amp=0.002), 0.004, NAVY)   # the windings
        for e in (-1, 1):                                                                   # black end caps
            fd.add(Cylinder(pc + Z * (e * (POD_HH - 0.016)), POD_R + 0.008, 0.034, rr=0.012), 0.006, BLACK)
        fd.add(Cylinder(pc - Z * (POD_HH + 0.006), 0.022, 0.02, rr=0.006), 0.004, GUN)
        # the window: a black frame on its outer face, a slot in it for the glowing bar
        Rw = rot_from_axes(z_axis=d, y_axis=Z)
        wc = pc + d * (POD_R + 0.002)
        fd.add(RoundBox(wc, (0.024, BAR_HH + 0.016, 0.012), 0.008, R=Rw), 0.004, BLACK)
        fd.sub(RoundBox(wc + d * 0.012, (0.0125, BAR_HH + 0.003, 0.012), 0.004, R=Rw), 0.002)
        fd.add(Sphere(pc + Z * (POD_HH + 0.012), 0.012), 0.004, STEEL)
    fd.add(Torus(c + Z * (RING_Z + POD_HH + 0.004), RING_R, 0.012), 0.006, GUN)          # the ring over their tops
    fd.add(Torus(c + Z * (RING_Z - POD_HH - 0.004), RING_R, 0.01), 0.006, GUN)           # and under them
    # the cup under the core, the cage of prongs round it
    fd.add(RoundCone(hub + Z * 0.02, CORE_C - Z * (CORE_R - 0.01), 0.04, 0.058), 0.01, GUN)
    fd.add(Torus(CORE_C - Z * (CORE_R - 0.012), 0.058, 0.009), 0.004, STEEL)
    for k in range(3):
        a = POD_A0 + 2 * math.pi * (k + 0.5) / 3
        d = v3((math.cos(a), math.sin(a), 0))
        pts = [CORE_C - Z * (CORE_R - 0.02) + d * 0.056, CORE_C + d * (CORE_R + 0.035), CORE_C + Z * (CORE_R + 0.03) + d * 0.05,
               CORE_C + Z * (CORE_R + 0.06) + d * 0.012]
        fd.add(Chain(pts, [0.011, 0.01, 0.009, 0.008], k=0.005), 0.004, GUN)
        fd.add(Sphere(pts[1], 0.015), 0.003, STEEL)
    fd.add(Sphere(CORE_C + Z * (CORE_R + 0.065), 0.016), 0.004, STEEL)
    return fd


def lights_field():
    """The housing's violet light strips (shipped glowing)."""
    fd = Field("Lights")
    for a in LIGHT_A:
        ang = POD_A0 + a
        d = v3((math.cos(ang), math.sin(ang), 0))
        sc = MAST_C + d * (HOUSE_R - 0.003) + Z * ((LIGHT_Z[0] + LIGHT_Z[1]) / 2)
        fd.add(RoundBox(sc, (0.0055, 0.006, (LIGHT_Z[1] - LIGHT_Z[0]) / 2 - 0.004), 0.0045, R=rot_from_axes(y_axis=d, z_axis=Z)), 0.0)
    return fd


def coils_field():
    """The coil cans' glowing bars (icy blue-white), one in each window, centred on the ring's plane (they grow along
    the `coils` bone's length as the field charges)."""
    fd = Field("Coils")
    for k in range(POD_N):
        pc, d = _pod_c(k)
        wc = pc + d * (POD_R + 0.009)
        fd.add(RoundBox(wc, (0.0085, BAR_HH, 0.006), 0.005, R=rot_from_axes(z_axis=d, y_axis=Z)), 0.0)
    return fd


def core_field():
    """The cryo core (shipped glowing icy white): a ball in its cage at the ring's centre."""
    fd = Field("Core")
    fd.add(Sphere(CORE_C, CORE_R), 0.0)
    return fd


def vapour_field():
    """A puff of cold vapour from the vent (shipped soft white, glowing faintly): billows along VENT_DIR, spreading."""
    fd = Field("Vapour")
    rs = np.random.RandomState(41)
    side = norm(np.cross(VENT_DIR, Z))
    up2 = norm(np.cross(side, VENT_DIR))
    puff = lambda P: F(0.008) * NOISE(P * F(14)) + F(0.004) * NOISE(P * F(35))
    for t, r in ((0.05, 0.04), (0.12, 0.055), (0.21, 0.07), (0.31, 0.08)):
        fd.add(Sphere(VENT_P + VENT_DIR * t, r, disp=puff, disp_amp=0.012), 0.03)
        for k in range(2):
            o = side * rs.uniform(-1, 1) + up2 * rs.uniform(-1, 1)
            fd.add(Sphere(VENT_P + VENT_DIR * (t + 0.02) + o * r * 0.6, r * 0.7, disp=puff, disp_amp=0.012), 0.03)
    return fd


# ======================================================================================= the control pedestal
CON_P = v3((-0.52, -0.36, 0.0))              # the pedestal's foot
CON_U = norm(v3((-CON_P[0], -CON_P[1], 0.0)))         # toward him (horizontal)
SN = norm(Z + CON_U * 0.36)                  # the panel's face (tilted toward him)
SU = norm(CON_U - SN * (CON_U @ SN))         # down the panel, toward him
SW = norm(np.cross(SU, SN))                  # across it
R_SLAB = np.stack([SW, SU, SN], axis=1)
SLAB_H = 0.86
SLAB_C = CON_P + Z * SLAB_H
SLAB_HALF = (0.19, 0.15, 0.04)
LEV_W = -0.045                               # the lever's line across the panel
LEV_PIV = SLAB_C + SW * LEV_W + SU * -0.075 + SN * (SLAB_HALF[2] + 0.03)       # its pivot (the panel's far half)
LEV_L = 0.29                                 # pivot -> the grip's middle
LEV_UP = 58.0                                # its rest (and Combat) angle up from the panel (deg)
GRIP_HALF = 0.06


def slab_pt(w, s, h):
    """A point over the panel's top face: across, toward him, up off the face."""
    return SLAB_C + SW * w + SU * s + SN * (SLAB_HALF[2] + h)


def lever_dir(deg):
    a = math.radians(deg)
    return norm(SU * math.cos(a) + SN * math.sin(a))


LEV_GRIP = LEV_PIV + lever_dir(LEV_UP) * LEV_L
LID_HINGE = slab_pt(0.0, -SLAB_HALF[1], 0.0)
LID_TILT = math.radians(118.0)


def lid_frame():
    u = norm(SU * math.cos(LID_TILT) + SN * math.sin(LID_TILT))
    n = norm(np.cross(u, SW))
    if n @ CON_U < 0:
        n = -n
    return u, n


def console_field():
    """On `machine`: a black foot plate (5), a graphite column (0) with a violet line painted down its front (13), the
    slanted panel (graphite, a black inset face 5), a slot for the lever, the lever's black clevis, three buttons (violet
    13, steel 10), two lamps (yellow 6), the raised display at its far edge (a black bezel), and its cable down the column
    and over the floor to the tank's skid (black rubber 12)."""
    fd = Field("Console")
    c = CON_P
    fd.add(Cylinder(c + Z * 0.012, 0.16, 0.024, rr=0.01), 0.0, BLACK)
    fd.add(RoundBox(c + Z * 0.43, (0.075, 0.06, 0.4), 0.03, R=rot_from_axes(y_axis=CON_U, z_axis=Z)), 0.012, GRAPH)
    fd.add(RoundBox(c + Z * 0.06, (0.1, 0.085, 0.04), 0.02, R=rot_from_axes(y_axis=CON_U, z_axis=Z)), 0.01, GRAPH)
    fd.paint(RoundBox(c + CON_U * 0.06 + Z * 0.45, (0.008, 0.02, 0.28), 0.004, R=rot_from_axes(y_axis=CON_U, z_axis=Z)), VIOLET)
    fd.add(Ellipsoid(SLAB_C - SN * 0.065, (0.08, 0.07, 0.035), R=R_SLAB), 0.02, GRAPH)
    fd.add(RoundBox(SLAB_C - SN * 0.004, (SLAB_HALF[0] + 0.01, SLAB_HALF[1] + 0.01, SLAB_HALF[2]), 0.02, R=R_SLAB), 0.006, GRAPH)
    fd.add(RoundBox(SLAB_C + SN * (SLAB_HALF[2] - 0.006), (SLAB_HALF[0] - 0.012, SLAB_HALF[1] - 0.012, 0.01), 0.006, R=R_SLAB), 0.003, BLACK)
    # the lever's slot and clevis
    fd.sub(RoundBox(slab_pt(LEV_W, 0.03, 0.0), (0.013, 0.11, 0.02), 0.008, R=R_SLAB), 0.003)
    for e in (-1, 1):
        fd.add(RoundBox(LEV_PIV + SW * (e * 0.026) - SN * 0.012, (0.008, 0.028, 0.03), 0.007, R=R_SLAB), 0.003, BLACK)
    fd.add(Cylinder(LEV_PIV, 0.012, 0.07, rr=0.004, R=rot_from_axes(z_axis=SW)), 0.003, STEEL)
    # buttons and lamps on the panel's right half (his left)
    for k, lab in enumerate((VIOLET, VIOLET, STEEL)):
        fd.add(Cylinder(slab_pt(0.07 + 0.042 * k, 0.07, 0.006), 0.015, 0.014, rr=0.005, R=R_SLAB), 0.003, lab)
    for k in range(2):
        fd.add(Sphere(slab_pt(0.09 + 0.05 * k, -0.02, 0.0), 0.009), 0.002, HAZARD)
    # the raised display at the far edge
    u, n = lid_frame()
    lc = LID_HINGE + u * 0.1
    Rl = np.stack([SW, u, n], axis=1)
    fd.add(RoundBox(lc, (SLAB_HALF[0] - 0.01, 0.1, 0.02), 0.014, R=Rl), 0.004, GRAPH)
    fd.add(RoundBox(lc + n * 0.018, (SLAB_HALF[0] - 0.026, 0.084, 0.006), 0.004, R=Rl), 0.003, BLACK)
    fd.add(Cylinder(LID_HINGE, 0.016, 2 * SLAB_HALF[0] - 0.02, rr=0.005, R=rot_from_axes(z_axis=SW)), 0.003, GUN)
    # the cable's start: down the column's back
    pts = [SLAB_C - SN * 0.07 - SU * 0.05, c + Z * 0.6 - CON_U * 0.08, c + Z * 0.2 - CON_U * 0.08, c + Z * 0.05 - CON_U * 0.11]
    fd.add(Chain(pts, [0.016] * len(pts), k=0.012), 0.004, RUBBER)
    return fd


def cable_field():
    """On `machine`: the pedestal's cable over the floor to the tank's skid (black rubber 12)."""
    fd = Field("Cable")
    c = CON_P
    gd = norm(v3((c[0] - MAST_C[0], c[1] - MAST_C[1], 0.0)))
    end = MAST_C + gd * (DECK_R + 0.01) + Z * (DECK_H * 0.5)
    pts = [c + Z * 0.05 - CON_U * 0.11, c + Z * 0.02 - CON_U * 0.16 + v3((0, 0.04, 0)),
           c + v3((0.08, 0.26, 0.016)), v3((-0.1, 0.4, 0.016)), v3((0.18, 0.44, 0.016)), end + gd * 0.08 + v3((0, 0, -0.01)), end]
    fd.add(Chain(pts, [0.016] * len(pts), k=0.012), 0.0, RUBBER)
    return fd


def screen_field():
    """The display's screen (shipped glowing pale violet)."""
    fd = Field("Screen")
    u, n = lid_frame()
    lc = LID_HINGE + u * 0.1
    fd.add(RoundBox(lc + n * 0.026, (SLAB_HALF[0] - 0.04, 0.07, 0.003), 0.002, R=np.stack([SW, u, n], axis=1)), 0.0)
    return fd


def lever_field():
    """The control lever (rest: raised LEV_UP toward him): a steel arm (10) from its hub on the pivot, a hazard-yellow
    collar (6), a black rubber T-grip across its end (12) with black end caps (5)."""
    fd = Field("Lever")
    d = lever_dir(LEV_UP)
    fd.add(Cylinder(LEV_PIV, 0.024, 0.04, rr=0.008, R=rot_from_axes(z_axis=SW)), 0.0, GUN)
    fd.add(RoundCone(LEV_PIV, LEV_GRIP - d * 0.012, 0.014, 0.011), 0.006, STEEL)
    fd.add(Cylinder(LEV_PIV + d * 0.1, 0.017, 0.03, rr=0.006, R=rot_from_axes(z_axis=d)), 0.004, HAZARD)
    fd.add(Cylinder(LEV_GRIP, 0.019, 2 * GRIP_HALF, rr=0.008, R=rot_from_axes(z_axis=SW),
                    disp=lambda P: F(0.0012) * np.sin(((P - LEV_GRIP.astype(F)) @ SW.astype(F)) * F(260)), disp_amp=0.0015), 0.006, RUBBER)
    for e in (-1, 1):
        fd.add(Cylinder(LEV_GRIP + SW * (e * (GRIP_HALF + 0.004)), 0.022, 0.014, rr=0.006, R=rot_from_axes(z_axis=SW)), 0.003, BLACK)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0.0, -0.24, 1.614)), 0.045, 0.4), (hp((0.0, -0.21, 1.69)), 0.03, 0.15)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.1, -0.14, 1.62)), 0.055, 0.42), (hp((sx * 0.07, -0.16, 1.63)), 0.03, 0.18),
                (hp((sx * 0.165, 0.035, 1.67)), 0.04, 0.3)]
    return pts


# ======================================================================================= build config
GLB_NAME = "cryo_field"
ROOT_NAME = "CryoFieldHQ"
TEX_PREFIX = "cryo"
MAT_NAME = "CryoMat"
MESH_NAME = "Cryo"
BASE_MODULE = "cryo_base"
ANIM_MODULE = "anim_cryo"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Headset", "VisorGlow", "Suit", "Armor", "Strips", "Pauldrons", "Trousers",
         "Boots", "Gloves", "Pad", "Machine", "Mast", "Ring", "Lights", "Coils", "Core", "Vapour", "Console", "Cable",
         "Screen", "Lever"]
REGION_PARTS = ("Skin", "Headset", "Suit", "Armor", "Pauldrons", "Trousers", "Gloves", "Pad", "Machine", "Mast", "Ring",
                "Console", "Lever")
GRAPHITE_C = (0.16, 0.17, 0.2)             # the tech corps' graphite and midnight navy
NAVY_C = (0.12, 0.16, 0.3)
VIOLET_C = (0.62, 0.24, 0.8)               # violet paint (the glowing trim is its own meshes)
GLOW_V = (0.85, 0.25, 0.95)                # the corps' neon violet
ICE = (0.72, 0.92, 1.0)                    # the cryo emitters' icy white-blue
KIT = {"base": GRAPHITE_C, "black": (0.05, 0.05, 0.06), "olive": NAVY_C, "coyote": VIOLET_C, "white": (0.84, 0.92, 1.0),
       "red": (0.74, 0.1, 0.08), "gunmetal": (0.24, 0.25, 0.28), "steel": (0.62, 0.64, 0.68), "glass": (0.05, 0.055, 0.08),
       "rubber": (0.08, 0.08, 0.09)}
MACHINE = dict(KIT, weave=0.0, red=(0.95, 0.74, 0.12), steel=(0.66, 0.68, 0.72))
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_CryoSkin", "base": (0.86, 0.66, 0.53), "ruddy": (0.86, 0.54, 0.45), "lips": (0.72, 0.45, 0.4),
                      "brow": ((0.07, 0.055, 0.05), (0.16, 0.12, 0.1)),
                      "extra": ((LASH, (0.06, 0.045, 0.04), 0.5), (STUBBLE, (0.6, 0.47, 0.4), 0.2, 0.2))}),
    "Hair": ("hair", {"name": "HQ_CryoHair", "base": (0.07, 0.06, 0.06), "hi": (0.26, 0.24, 0.27), "low": (0.03, 0.026, 0.026),
                      "streak": (0.05, 0.045, 0.045), "tint": (0.1, 0.09, 0.1)}),
    "Suit": ("modern_kit", dict(KIT, name="HQ_CryoSuit")),
    "Trousers": ("modern_kit", dict(KIT, name="HQ_CryoSuit")),
    "Gloves": ("modern_kit", dict(KIT, name="HQ_CryoSuit")),
    "Armor": ("modern_kit", dict(KIT, name="HQ_CryoArmor", weave=0.0)),
    "Pauldrons": ("modern_kit", dict(KIT, name="HQ_CryoArmor", weave=0.0)),
    "Headset": ("modern_kit", dict(KIT, name="HQ_CryoArmor", weave=0.0)),
    "Pad": ("modern_kit", dict(KIT, name="HQ_CryoArmor", weave=0.0)),
    "Boots": ("leather_dyed", {"name": "HQ_CryoBoots", "base": (0.06, 0.06, 0.065), "dyed": (0.06, 0.06, 0.065),
                               "worn_c": (0.24, 0.24, 0.26)}),
    "Machine": ("modern_kit", dict(MACHINE, name="HQ_CryoMachine")),
    "Mast": ("modern_kit", dict(MACHINE, name="HQ_CryoMachine")),
    "Ring": ("modern_kit", dict(MACHINE, name="HQ_CryoMachine")),
    "Cable": ("modern_kit", dict(MACHINE, name="HQ_CryoMachine")),
    "Console": ("modern_kit", dict(MACHINE, name="HQ_CryoMachine")),
    "Lever": ("modern_kit", dict(MACHINE, name="HQ_CryoMachine")),
    "VisorGlow": ("glow_ball", {"name": "HQ_CryoVisorGlow", "col": GLOW_V, "strength": 1.0}),
    "Strips": ("glow_ball", {"name": "HQ_CryoStrips", "col": GLOW_V, "strength": 1.0}),
    "Lights": ("glow_ball", {"name": "HQ_CryoLights", "col": GLOW_V, "strength": 1.0}),
    "Coils": ("glow_ball", {"name": "HQ_CryoCoils", "col": ICE, "strength": 1.2}),
    "Core": ("glow_ball", {"name": "HQ_CryoCore", "col": (0.82, 0.95, 1.0), "strength": 1.3}),
    "Vapour": ("glow_ball", {"name": "HQ_CryoVapour", "col": (0.9, 0.96, 1.0), "strength": 0.5}),
    "Screen": ("glow_ball", {"name": "HQ_CryoScreen", "col": (0.78, 0.64, 1.0), "strength": 0.8}),
}
GLOW = {"VisorGlow": (GLOW_V, 1.1, 0.5), "Strips": (GLOW_V, 1.1, 0.5), "Lights": (GLOW_V, 1.1, 0.5),
        "Coils": (ICE, 1.2, 0.6), "Core": ((0.82, 0.95, 1.0), 1.3, 0.6), "Vapour": ((0.9, 0.96, 1.0), 0.45, 1.0),
        "Screen": ((0.78, 0.64, 1.0), 0.8, 0.5)}
LOW_TARGETS = {"Skin": 5400, "Teeth": 60, "Hair": 900, "Headset": 1000, "VisorGlow": 80, "Suit": 3000, "Armor": 1800,
               "Strips": 60, "Pauldrons": 1300, "Trousers": 1500, "Boots": 1200, "Gloves": 1400, "Pad": 240,
               "Machine": 2700, "Mast": 1200, "Ring": 1300, "Lights": 60, "Coils": 140, "Core": 200, "Vapour": 400, "Console": 1300,
               "Cable": 150, "Screen": 30, "Lever": 300}
AO_EXCLUDE = ["Pad", "Lever", "Vapour"]
MACHINE_PARTS = ["Machine", "Mast", "Ring", "Console", "Cable", "Lever"]
# the machine is baked 6 m away from him: his rest pose (his arms out) must leave no shadow on it
BAKE_APART = (MACHINE_PARTS, (6.0, 0.0, 0.0))
YAW_PIVOT = (0.04, 0.0, 0.0)              # the tower turns about this point (keeps the projector, the pedestal and him on the base)


def prop_bones():
    return []


def extra_bones():
    """machine (the tank, its skid, gauges and valve, and the control pedestal: deforming nothing of him), mast (the
    mast, the hoses, the projector ring: it shudders about its foot at the pulse), coils (the coil cans' glowing bars:
    scaled along its length, bone y, as the field charges; its head is the ring's centre), core (the glowing core: its
    centre is the point the game's frost rings leave from, bone_point ALONG 0; it swells as the field charges and flares
    at the pulse), lever (the control lever: turns about SW, its pivot), vapour (the vent's puff of cold vapour: scaled
    from nothing at the vent's mouth)."""
    return [("machine", MAST_C + Z * 0.02, MAST_C + Z * 0.3, None),
            ("mast", MAST_C + Z * TANK_TOP, MAST_C + Z * (TANK_TOP + 0.4), "machine"),
            ("coils", CORE_C, CORE_C + Z * 0.2, "mast"),
            ("core", CORE_C, CORE_C + Z * 0.15, "mast"),
            ("lever", LEV_PIV, LEV_GRIP, "machine"),
            ("vapour", VENT_P, VENT_P + VENT_DIR * 0.3, "machine")]


def weight_rules():
    arms = {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Headset": ("rigid", "head"),
        "VisorGlow": ("rigid", "head"),
        "Suit": ("transfer", TORSO | arms, None),
        "Pauldrons": ("transfer", TORSO | arms, None),
        "Armor": ("transfer", TORSO, None),
        "Strips": ("rigid", "chest"),
        "Trousers": ("transfer", {"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Pad": ("rigid", "forearm.L"),
        "Machine": ("rigid", "machine"), "Mast": ("rigid", "mast"), "Ring": ("rigid", "mast"), "Lights": ("rigid", "mast"),
        "Cable": ("rigid", "machine"),
        "Coils": ("rigid", "coils"), "Core": ("rigid", "core"), "Vapour": ("rigid", "vapour"),
        "Console": ("rigid", "machine"), "Screen": ("rigid", "machine"), "Lever": ("rigid", "lever"),
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
        ("VisorGlow", visor_glow_field(), 0.0012),
        ("Suit", suit_field(), 0.0024 if fine else 0.0034),
        ("Armor", armor_field(), 0.0022 if fine else 0.0032),
        ("Strips", strips_field(), 0.0014),
        ("Pauldrons", pauldrons_field(), 0.0022 if fine else 0.0032),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0022 if fine else 0.003),
        ("Gloves", gloves_field(), 0.002 if fine else 0.003),
        ("Pad", pad_field(), 0.0016 if fine else 0.0024),
        ("Machine", machine_field(), 0.0026 if fine else 0.0036),
        ("Mast", mast_field(), 0.0024 if fine else 0.0034),
        ("Ring", ring_field(), 0.0022 if fine else 0.0032),
        ("Lights", lights_field(), 0.0016),
        ("Coils", coils_field(), 0.0016),
        ("Core", core_field(), 0.003),
        ("Vapour", vapour_field(), 0.004),
        ("Console", console_field(), 0.0022 if fine else 0.0032),
        ("Cable", cable_field(), 0.003),
        ("Screen", screen_field(), 0.002),
        ("Lever", lever_field(), 0.0016 if fine else 0.0024),
    ]
