"""Nova, Netrunner (HQ hero, Digital Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A brilliant, cocky young hacker: a bright, lively face (clear violet-grey eyes, a sly grin: the smile drawn up higher at
her left corner, a dimple there, her upper teeth showing; her left brow arched a little higher than the right), black
hair in an asymmetric undercut (her right side shaved close, the rest swept over from a hard parting into a long
side fringe that falls past her left cheek to her jaw), one magenta-violet streak through the front of the fringe. A slim
AR visor pushed up on her head like a headband (a violet-glowing lens strip), a small headset on her right ear (the
shaved side) with a mic boom to the corner of her mouth.

A navy armoured bodysuit (graphite plates over her midriff and the fronts of her thighs, black knee pads), a cropped
graphite tech jacket over it (a stand collar, open at the front, the sleeves to just below her elbows), violet light
strips along the jacket's front edges, hem, cuffs, over the shoulders and down the outsides of the sleeves (their own
glowing mesh, `Strips`, riding the jacket's bones); black fingerless gloves; on her right forearm a slim graphite
bracer, on her left the holo-deck (a gunmetal bracer with a glowing screen on top of her forearm, `Deck`); a slim
black belt, a mag-dock holster on her right hip and thigh (the pistol docks there in the Ability); sleek black boots
with a violet band round their tops.

Her weapon: a compact laser pistol (gloss-black housing, gunmetal side plates, a power cell on top, a finned barrel
shroud and the emitter at its nose: a violet lens and light strips along the housing's sides, their own glowing mesh,
`Emitter`). Fired one-handed.

She has Kira's build (kira.py) with both hands made fists (brenna.py) and Wren's booted feet (wren.py), as Ada (ada.py).
The pistol rides its own parentless bone (`laser`: the grip's middle to the emitter lens); the clips pose it in world
space and put her right fist on its grip (anim_nova.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from kira import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S,
                  fist_center, torso_prims, traps, neck_prim, deltoid, upper_arm, _forearm, eyes_field, TORSO, TORSO_Z,
                  torso_bones, hstripe)
from brenna import hand, leg_prims
from wren import foot
from isla import _seg_dist_np, boots_weights as _isla_boots_weights
from ada import ScaledField, _on_face, arm_prims, legs_hull, boot_hull, boot_top

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH = 0, 1, 2, 3, 4, 5, 8
IRIS = ((0.2, 0.13, 0.34), (0.5, 0.34, 0.74))           # violet-grey eyes (prep.paint_eyes)

GRAPHITE = (0.16, 0.17, 0.2)              # the corps' techwear (the brief's colours, sRGB)
NAVY = (0.12, 0.16, 0.3)
VIOLET = (0.85, 0.25, 0.95)               # the defenders' one accent (emissive)
BLACK = (0.06, 0.06, 0.07)
GUNMETAL = (0.24, 0.25, 0.28)


# ======================================================================================= head
def mouth_curves(x):
    """The sly grin (design units): the upper lip's edge and the lower lip's edge at x. Both corners are drawn up, the
    left one (+X) higher; the opening is widest in the middle (her upper teeth show) and closes at the corners."""
    x = np.asarray(x, dtype=np.float64)
    up = 1.5625 + 4.6 * x * x + 0.06 * x
    lo = up - 0.019 * np.clip(1.0 - (x / MOUTH_W) ** 2, 0.0, 1.0)
    return up, lo


MOUTH_W = 0.054                    # half the grin's width (design)


def head(fd):
    """Ada's face (ada.py) made a little sharper and set in a sly grin: a lean young jaw and a neat pointed chin, round
    cheeks pushed up by the smile; bright open eyes (the upper lids clear of the irises), winged lashes; level brows
    lying on her brow, the left one arched a touch higher; a small upturned nose; the open grin, its left corner higher,
    a dimple under it. Only her right ear is sculpted (the left lies under her hair)."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.062, 1.596), (0.134, 0.128, 0.122)), 0.07, SKIN)                          # a lean young jaw
    fd.add(E((0, -0.13, 1.508), (0.064, 0.058, 0.057)), 0.05, SKIN)                          # a neat pointed chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.106, -0.12, 1.636), 0.039), 0.05, SKIN)                               # cheekbones
        fd.add(S((sx * 0.11, -0.05, 1.568), 0.041), 0.05, SKIN)
        fd.add(S((sx * 0.076, -0.142, 1.612 + 0.002 * sx), 0.028), 0.03, SKIN)                 # round cheeks, pushed up
        pts = [hp((sx * 0.15, -0.056, 1.748)), hp((sx * 0.115, -0.12, 1.754)), hp((sx * 0.062, -0.152, 1.752))]
        fd.add(Chain(pts, [hr(0.005), hr(0.0065), hr(0.0055)], k=hr(0.02)), hr(0.03), SKIN)   # (a soft brow bone)
    # brows: level and lying on the brow, the left one (+X) arched a little higher (amused, never knitted)
    brows = {-1: [(-0.03, 1.772), (-0.066, 1.787), (-0.106, 1.792), (-0.145, 1.783)],
             1: [(0.03, 1.775), (0.066, 1.796), (0.106, 1.806), (0.145, 1.796)]}
    for sx in (-1, 1):
        on = _on_face(fd, brows[sx], lift=0.001)
        fd.add(Chain(on, [hr(0.004), hr(0.0052), hr(0.0046), hr(0.0022)], k=hr(0.006)), hr(0.004), BROW)
        fd.paint(Chain(on, [hr(0.0105), hr(0.0125), hr(0.011), hr(0.0058)], k=hr(0.008)), BROW)
    # eyes: open and bright; the upper lids up clear of the irises, the lower lids lifted a little by her cheeks;
    # lashes along the upper lids, flicked out into small wings
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, hr(0.0215))), (sx * 0.16, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0046)), Plane(ec + v3((0, 0, -hr(0.0165))), (sx * -0.3, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.006), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.0075)), Plane(ec + v3((0, 0, hr(0.0185))), (sx * 0.16, 0.05, -1.0)), hr(0.002)), LASH)
        flick = ec + v3((sx * hr(0.039), -hr(0.012), hr(0.014)))
        fd.add(RoundCone(flick, flick + v3((sx * hr(0.016), hr(0.006), hr(0.009))), hr(0.004), hr(0.0014)), hr(0.004), LASH)
    # a small, upturned nose
    fd.add(RoundCone(hp((0, -0.178, 1.722)), hp((0, -0.211, 1.654)), hr(0.0102), hr(0.0142)), hr(0.016), SKIN)
    fd.add(S((0, -0.212, 1.643), 0.018), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.021, -0.195, 1.629), 0.0128), hr(0.01), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.012, -0.208, 1.618)), v3((0.0068, 0.0088, 0.0048)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the open grin: a crescent between the lips' edges, its left corner higher
    xs = np.linspace(-MOUTH_W, MOUTH_W, 9)
    up_z, lo_z = mouth_curves(xs)
    upper = _on_face(fd, [(x, z + 0.004) for x, z in zip(xs, up_z)])
    lower = _on_face(fd, [(x, z - 0.0035) for x, z in zip(xs, lo_z)])
    def opening(P):
        Q = hinv(P)
        x, z = Q[:, 0], Q[:, 2]
        u, l = mouth_curves(x)
        dz = np.maximum(z - u.astype(F), l.astype(F) - z)
        dx = np.abs(x) - F(MOUTH_W)
        return np.maximum(np.maximum(dz, dx), (Q[:, 1] - F(-0.205)) * F(-1)) * F(HS)
    cav = Inter(Func(opening, hp((-0.09, -0.24, 1.48)), hp((0.09, -0.12, 1.62))),
                Ellipsoid(hp((0.0, -0.165, 1.555)), v3((0.072, 0.03, 0.046)) * HS), hr(0.002))
    fd.sub(cav, hr(0.004))
    fd.paint(Inter(Func(lambda P: opening(P) - F(0.0025), hp((-0.09, -0.24, 1.48)), hp((0.09, -0.12, 1.62))),
                   Ellipsoid(hp((0.0, -0.165, 1.555)), v3((0.078, 0.04, 0.056)) * HS), hr(0.002)), MOUTH)
    # the lips: a thin upper lip, a fuller lower one, tapering into the corners
    ru = [0.0024, 0.004, 0.0052, 0.0058, 0.006, 0.0058, 0.0052, 0.004, 0.0024]
    rl = [0.0026, 0.0046, 0.0062, 0.0072, 0.0076, 0.0072, 0.0062, 0.0046, 0.0026]
    fd.add(Chain(upper, [hr(r) for r in ru], k=hr(0.005)), hr(0.007), LIP)
    fd.add(Chain(lower, [hr(r) for r in rl], k=hr(0.006)), hr(0.008), LIP)
    for sx in (-1, 1):
        cx = sx * (MOUTH_W + 0.006)
        cz = float(mouth_curves(cx)[0])
        fd.add(S((sx * 0.077, -0.152, cz + 0.014), 0.011 + 0.002 * (sx > 0)), hr(0.01), SKIN)   # the smile's cheeks
    cz = float(mouth_curves(MOUTH_W + 0.006)[0])
    fd.sub(S((MOUTH_W + 0.016, -0.152, cz + 0.001), 0.0055), hr(0.006))                       # a dimple at her left corner
    fd.add(Ellipsoid(hp((-0.174, 0.035, 1.66)), v3((0.024, 0.043, 0.054)) * HS, R=euler(0, -0.25, 0.35)), hr(0.02), SKIN)  # right ear


def teeth_field():
    """Her upper teeth, showing under her upper lip in the grin (following its curve, set back in the mouth)."""
    fd = Field("Teeth")
    xs = np.linspace(-0.039, 0.039, 7)
    up_z, lo_z = mouth_curves(xs)
    pts = [hp((x, -0.177 + 7.0 * x * x, z - 0.0074)) for x, z in zip(xs, up_z)]
    fd.add(Chain(pts, [hr(0.0072)] * len(pts), k=hr(0.004)), 0.0)
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


# ======================================================================================= hair: an asymmetric undercut
EAR_C = {sx: hp((sx * 0.174, 0.035, 1.66)) for sx in (-1, 1)}
PART_X = -0.1                             # the hard parting (design x): her right side is shaved below and beside it


def hairline(P):
    """> 0 below her hairline (design units): her forehead, in front of her ears, round the nape."""
    Q = hinv(P)
    y = Q[:, 1]
    zl = F(1.852) - F(0.1) * smoothstep(-0.14, -0.06, y) - F(0.2) * smoothstep(0.075, 0.15, y)
    return zl - Q[:, 2]


def ear_r(P):
    q = P - EAR_C[-1].astype(F)
    return F(hr(0.062)) - np.sqrt((q * q).sum(1))


def long_side(P):
    """> 0 on the long side of the parting (design units), < 0 on her shaved right side."""
    return hinv(P)[:, 0] - F(PART_X)


def head_pt(d, off=0.0):
    """A point `off` out from the head's ellipsoid in the direction d from its centre, and the surface normal there."""
    u = norm(d)
    s = 1.0 / np.linalg.norm(u / HEAD_RAD)
    p = HEAD_C + u * s
    n = norm((p - HEAD_C) / HEAD_RAD ** 2)
    return p + n * off, n


def _strands(P):
    return F(0.0014) * NOISE(P * F(70)) + F(0.0009) * NOISE(P * F(160))


# the locks of the long side: each runs from the parting over her head to her left side and falls past her left cheek
# (the front ones sweep across her forehead above her brows, at the hairline; the back ones go over the crown)
FRONT_PATH = [(-0.56, -0.44, 0.71), (-0.2, -0.68, 0.7), (0.3, -0.69, 0.66), (0.72, -0.48, 0.5), (0.93, -0.27, 0.15)]
FRONT_HANG = [(0.212, -0.06, 1.672), (0.222, -0.05, 1.6), (0.214, -0.036, 1.53), (0.196, -0.024, 1.488)]
BACK_PATH = [(-0.5, 0.42, 0.76), (0.0, 0.5, 0.87), (0.48, 0.52, 0.7), (0.8, 0.45, 0.4), (0.9, 0.42, 0.02)]
BACK_HANG = [(0.19, 0.09, 1.69), (0.184, 0.11, 1.635), (0.17, 0.125, 1.6), (0.152, 0.13, 1.575)]
N_LOCKS = 10
STREAK_LOCKS = (0,)


def lock_spec(j):
    """(points, widths, thicknesses, normals) of lock j (0 = the front of the fringe)."""
    t = j / (N_LOCKS - 1.0)
    t = t ** 0.8
    dirs = [norm(lerp(v3(a), v3(b), t)) for a, b in zip(FRONT_PATH, BACK_PATH)]
    pts, nrm = [], []
    lift = 0.004 * (j % 2) + (0.005 if j in STREAK_LOCKS else 0.0)
    swoop = 1.0 - 0.55 * t                                      # (the front locks stand up highest: the swoop)
    for i in range(len(dirs) - 1):                             # densify over the head
        for s in ((0.0, 0.5) if i < len(dirs) - 2 else (0.0, 0.5, 1.0)):
            d = norm(lerp(dirs[i], dirs[i + 1], s))
            k = (i + s) / (len(dirs) - 1.0)
            off = 0.008 + swoop * 0.036 * smoothstep_f(0.0, 0.3, k) * (1.0 - 0.45 * smoothstep_f(0.55, 1.0, k)) + lift
            p, n = head_pt(d, off)
            pts.append(p)
            nrm.append(n)
    for a, b in zip(FRONT_HANG, BACK_HANG):
        q = hp(lerp(v3(a), v3(b), t))
        q = q + v3((lift, 0, 0))
        pts.append(q)
        nrm.append(v3((1.0, 0.0, 0.0)))
    n = len(pts)
    w0 = 0.054 * (1.1 if j in STREAK_LOCKS else 1.0)
    widths = [w0 * (0.7 + 0.3 * smoothstep_f(0.0, 0.2, i / (n - 1.0))) * (1.0 - 0.75 * smoothstep_f(0.6, 1.0, i / (n - 1.0))) for i in range(n)]
    thicks = [0.024 * (0.75 + 0.25 * smoothstep_f(0.0, 0.2, i / (n - 1.0))) * (1.0 - 0.6 * smoothstep_f(0.7, 1.0, i / (n - 1.0))) for i in range(n)]
    return pts, widths, thicks, nrm


def smoothstep_f(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def hair_field():
    """Black hair (label 0): a full cap on the long side of the parting (thinning to the hairline), shaved close below
    and beside the parting on her right side (a thin buzz over her skin), the long side's locks swept over her head from
    the parting and falling past her left cheek; short locks at the back of her head."""
    fd = Field("Hair")
    head_ = Ellipsoid(HEAD_C, HEAD_RAD)
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    def cap(P):
        d = head_(P)
        h = -hairline(P)
        side = long_side(P)
        th = F(0.005) + F(0.026) * smoothstep(0.0, 0.04, h) * smoothstep(-0.01, 0.03, side)
        return np.abs(d - (F(0.002) + th * F(0.5))) - th * F(0.5) + F(0.0012) * NOISE(P * F(45))
    def region(P):
        return np.maximum(hairline(P) * F(HS), -long_side(P) * F(HS) - F(0.004))
    fd.add(Inter(Func(cap, lo, hi), Func(region, lo, hi), 0.004), 0.0)
    # the shaved side: a thin buzz, its edge under the cap at the parting
    def buzz_region(P):
        return np.maximum(np.maximum(hairline(P) * F(HS), long_side(P) * F(HS) - F(0.006)), ear_r(P))
    fd.add(Inter(Shell(head_, 0.0025, 0.0035, pad=0.05, disp=lambda P: F(0.0005) * NOISE(P * F(120)), disp_amp=0.0006),
                 Func(buzz_region, lo, hi), 0.002), 0.0)
    # the long side's locks
    for j in range(N_LOCKS):
        if j in STREAK_LOCKS:
            continue
        pts, w, th, nr = lock_spec(j)
        fd.add(Lock(pts, w, th, nr, k=0.008, disp=_strands, disp_amp=0.003), 0.008)
    # short locks at the back of her head, combed down toward the nape
    for k in range(5):
        a = math.radians(-40 + 25 * k)
        d0 = v3((math.sin(a) * 0.9, 0.6, 0.55))
        d1 = v3((math.sin(a) * 0.95, 0.85, -0.05))
        d2 = v3((math.sin(a) * 0.9, 0.85, -0.45))
        pts, nr = [], []
        for s, d in enumerate((d0, lerp(d0, d1, 0.5), d1, lerp(d1, d2, 0.6))):
            p, n = head_pt(d, 0.012 + 0.004 * (k % 2))
            pts.append(p)
            nr.append(n)
        if long_side(np.array([pts[0]], F))[0] < 0.0:
            continue
        fd.add(Lock(pts, [0.04, 0.042, 0.036, 0.018], [0.013, 0.014, 0.011, 0.005], nr, k=0.006, disp=_strands, disp_amp=0.003), 0.008)
    return fd


def streak_field():
    """The magenta-violet streak: one lock at the front of the fringe (its own part, dyed)."""
    fd = Field("Streak")
    for j in STREAK_LOCKS:
        pts, w, th, nr = lock_spec(j)
        fd.add(Lock(pts, w, th, nr, k=0.008, disp=_strands, disp_amp=0.003), 0.0)
    return fd


# ======================================================================================= the AR visor (pushed up on her head)
_VA, _VB, _VC = hp((0.0, -0.06, 1.95)), hp((0.178, 0.05, 1.8)), hp((-0.178, 0.05, 1.8))
VIS_N = norm(np.cross(_VB - _VA, _VC - _VA))
if VIS_N[2] < 0:
    VIS_N = -VIS_N


def _vang(P):
    """The angle round her head (0 at her front, + toward her left)."""
    Q = P - HEAD_C.astype(F)
    return np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.01)))


_VIS_TAB = None


def _vis_table():
    """The hair's height over her head's ellipsoid along the visor's line, every few degrees round her head (rays in the
    visor's plane): the band rides on the hair."""
    global _VIS_TAB
    if _VIS_TAB is None:
        hf, sf = hair_field(), streak_field()
        both = Func(lambda P: np.minimum(hf.eval(P, margin=0.02), sf.eval(P, margin=0.02)), HEAD_C - 0.35, HEAD_C + 0.35)
        head_ = Ellipsoid(HEAD_C, HEAD_RAD)
        rays = np.radians(np.arange(-140.0, 141.0, 2.5))
        pa, po = [], []
        for a in rays:
            for dz in (-0.02, -0.01, 0.0, 0.01, 0.02):         # (across the band's height)
                d = v3((math.sin(a), -math.cos(a), 0.0))
                d = norm(d - VIS_N * float(d @ VIS_N))
                c = HEAD_C + VIS_N * float((_VA - HEAD_C) @ VIS_N) + VIS_N * dz
                h, ok = ray_hit(both, [c + d * 0.35], [-d], tmax=0.35, step=0.001)
                q = np.array([h[0] if ok[0] else c + d * 0.2], F)
                pa.append(float(_vang(q)[0]))
                po.append(float(head_(q)[0]) if ok[0] else 0.0)
        pa, po = np.array(pa), np.array(po)
        angs = np.radians(np.arange(-130.0, 131.0, 2.5))
        offs = np.array([po[np.abs(pa - x) < math.radians(9.0)].max(initial=0.0) for x in angs])
        _VIS_TAB = (angs.astype(F), (offs + 0.008).astype(F))
    return _VIS_TAB


def vis_off(P):
    """How far the visor stands off her head: on top of the hair (measured along its line), close over the buzz on her
    right."""
    a = _vang(P)
    angs, offs = _vis_table()
    return np.interp(a, angs, offs).astype(F)


def _vplane(P):
    return (P - _VA.astype(F)) @ VIS_N.astype(F)


def visor_field():
    """The visor's band (black polymer, label 5): a slim band round the front and sides of her head (to behind her ears),
    deeper across her brow where it holds the lens, a small gunmetal (9) hinge block over each ear."""
    fd = Field("Visor")
    head_ = Ellipsoid(HEAD_C, HEAD_RAD)
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    def band(P):
        d = head_(P) - vis_off(P)
        a = np.abs(_vang(P))
        hgt = F(0.009) + F(0.009) * smoothstep(1.15, 0.85, a)
        reg = np.maximum(np.abs(_vplane(P) + F(0.002) * smoothstep(1.15, 0.85, a)) - hgt, a - F(2.05))
        return np.maximum(np.abs(d - F(0.004)) - F(0.0055), reg)
    fd.add(Func(band, lo, hi), 0.0, 5)
    for sx in (-1, 1):
        a = sx * 1.55
        dv = v3((math.sin(a), -math.cos(a), 0.0))
        p0 = HEAD_C + dv * 0.3
        h, ok = ray_hit(Func(lambda P: band(P), lo, hi), [p0 + VIS_N * (-(p0 - _VA) @ VIS_N)], [-dv], tmax=0.4, step=0.001)
        if ok[0]:
            fd.add(RoundBox(h[0] + dv * 0.004, (0.012, 0.022, 0.012), 0.005, R=rot_from_axes(z_axis=VIS_N, y_axis=np.cross(VIS_N, dv))), 0.004, 9)
    return fd


def visor_lens_field():
    """The visor's lens: a curved strip across the front of the band (it glows violet: `GlowVisor`)."""
    fd = Field("VisorLens")
    head_ = Ellipsoid(HEAD_C, HEAD_RAD)
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    def lens(P):
        d = head_(P) - vis_off(P)
        a = np.abs(_vang(P))
        reg = np.maximum(np.abs(_vplane(P) + F(0.002)) - F(0.0115), a - F(0.92))
        return np.maximum(np.abs(d - F(0.0105)) - F(0.0028), reg)
    fd.add(Func(lens, lo, hi), 0.0)
    return fd


# ======================================================================================= the headset (her right ear)
CUP_R, CUP_H = 0.04, 0.026


def cup_frame():
    ax = norm(v3((-1.0, 0.08, -0.04)))
    return EAR_C[-1] + ax * 0.026 + v3((0, 0.002, 0.004)), ax


MIC = [hp((-0.2, -0.04, 1.625)), hp((-0.172, -0.13, 1.585)), hp((-0.12, -0.188, 1.562)), hp((-0.086, -0.207, 1.562))]


def headset_field():
    """Black (label 5) earpiece over her right ear (a gunmetal (9) rim, a violet-painted (6) ring on its face), a hook
    behind her ear, the mic boom to the corner of her mouth."""
    fd = Field("Headset")
    c, ax = cup_frame()
    R = rot_from_axes(z_axis=ax)
    fd.add(Cylinder(c + ax * (CUP_H * 0.5), CUP_R, CUP_H, rr=0.012, R=R), 0.0, 5)
    fd.add(Torus(c + ax * 0.004, CUP_R - 0.004, 0.008, R=R), 0.005, 9)
    fd.paint(Torus(c + ax * CUP_H, CUP_R * 0.62, 0.0045, R=R), 6)
    hook = [c + ax * 0.01 + v3((0, 0.015, 0.035)), hp((-0.19, 0.06, 1.72)), hp((-0.185, 0.085, 1.665)), hp((-0.18, 0.075, 1.61))]
    fd.add(Chain(hook, [0.0065, 0.006, 0.006, 0.0055], k=0.004), 0.004, 5)
    fd.add(Chain(MIC, [0.0062, 0.0058, 0.0054, 0.005], k=0.004), 0.004, 9)
    fd.add(Sphere(MIC[-1] + norm(MIC[-1] - MIC[-2]) * 0.006, 0.011), 0.004, 5)
    return fd


# ======================================================================================= the bodysuit
SUIT_OFF, SUIT_T = 0.008, 0.008
SUIT_OUT = SUIT_OFF + SUIT_T / 2


def body_hull():
    b = Field("BodyHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    for side in ("R", "L"):
        for p, k in arm_prims(side):
            b.add(p, k)
        for p, k in leg_prims(side):
            b.add(p, k)
    return b


def torso_hull():
    b = Field("TorsoHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    return b


def arms_hull():
    b = Field("ArmsHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    for side in ("R", "L"):
        for p, k in arm_prims(side):
            b.add(p, k)
    return b


def arm_hull(side):
    b = Field("Arm" + side)
    for p, k in arm_prims(side):
        b.add(p, k)
    return b


def neck_line(P, base=1.43):
    """> 0 above a neckline round her neck only (lifted clear of the shoulders, so it opens no hole on them)."""
    ax = np.abs(P[:, 0])
    return P[:, 2] - (F(base) + F(0.075) * smoothstep(-0.04, 0.12, P[:, 1]) + F(0.3) * smoothstep(0.12, 0.19, ax))


def wrist_cut(P):
    """> 0 past her wrists (only near the forearms): the suit's sleeves end under the gloves' cuffs."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        along = (P - wr.astype(F)) @ ax.astype(F) - F(0.004)
        near = _seg_dist_np(P, el, wr + ax * 0.2) < F(0.12)
        out = np.maximum(out, np.where(near, along, F(-1.0)))
    return out


def suit_field():
    """Navy stretch armour-weave (label 0) over her whole body, a mock neck under the jacket's collar, black (5) panel
    seams down her sides; graphite (13) plates: three segments over her midriff, a plate on the front of each thigh with
    a violet (6) line; black (5) knee pads."""
    fd = Field("Suit")
    hull = body_hull()
    weave = lambda P: F(0.0008) * NOISE(P * F(40))
    def cut(P):
        legs_end = F(0.3) - P[:, 2]
        return np.maximum(np.maximum(neck_line(P, 1.44), wrist_cut(P)), legs_end)
    fd.add(Inter(Shell(hull, SUIT_OFF, SUIT_T, pad=0.1, disp=weave, disp_amp=0.001), Func(cut, (-1, -0.6, 0.2), (1, 0.6, 1.7)), 0.003), 0.0)
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    fd.add(Inter(Shell(nk, 0.008, 0.008, pad=0.06), Func(lambda P: np.abs(P[:, 2] - F(1.425)) - F(0.035), (-0.3, -0.3, 1.3), (0.3, 0.3, 1.6)), 0.004), 0.006)
    # side seams (painted black)
    th = torso_hull()
    def seams(P):
        x = np.abs(P[:, 0])
        side = np.abs(P[:, 1] - F(0.035)) - F(0.006)
        return np.maximum(side, np.maximum(F(0.12) - x, np.abs(P[:, 2] - F(1.0)) - F(0.2)))
    fd.paint(Func(seams, (-0.5, -0.3, 0.7), (0.5, 0.3, 1.3)), 5)
    # the midriff plates: three curved segments over the front of her belly
    for z0, z1 in ((0.935, 0.965), (0.971, 0.999), (1.005, 1.031)):
        def seg_(P, z0=z0, z1=z1):
            reg = np.maximum(np.maximum(F(z0) - P[:, 2], P[:, 2] - F(z1)), np.maximum(P[:, 1] - F(-0.02), np.abs(P[:, 0]) - F(0.12)))
            return reg
        fd.add(Inter(Shell(th, SUIT_OUT + 0.008, 0.01, pad=0.08), Func(seg_, (-0.3, -0.4, 0.85), (0.3, 0.2, 1.1)), 0.004), 0.004, 13)
    # thigh plates: on the front of each thigh, a violet line down each
    for side in ("R", "L"):
        lb = legs_hull(side)
        hip, kn = J["hip_" + side], J["knee_" + side]
        ax = norm(kn - hip)
        def plate(P, hip=hip, ax=ax):
            s = (P - hip.astype(F)) @ ax.astype(F)
            q = P - hip.astype(F) - s[:, None] * ax.astype(F)
            fwd = -q[:, 1] / (np.sqrt((q * q).sum(1)) + F(1e-6))
            return np.maximum(np.maximum(F(0.1) - s, s - F(0.27)), F(0.72) - fwd)
        fd.add(Inter(Shell(lb, SUIT_OUT + 0.007, 0.01, pad=0.08), Func(plate, hip - v3((0.3, 0.3, 0.5)), hip + v3((0.3, 0.3, 0.1))), 0.004), 0.004, 13)
        def line(P, hip=hip, ax=ax):
            s = (P - hip.astype(F)) @ ax.astype(F)
            q = P - hip.astype(F) - s[:, None] * ax.astype(F)
            return np.maximum(np.abs(q[:, 0]) - F(0.006), np.maximum(F(0.12) - s, s - F(0.25)))
        fd.paint(Func(line, hip - v3((0.3, 0.3, 0.5)), hip + v3((0.3, 0.3, 0.1))), 6)
    # knee pads
    for side in ("R", "L"):
        kn, an = J["knee_" + side], J["ankle_" + side]
        ax = norm(an - kn)
        c = kn + v3((0, -0.088, -0.008))
        R = rot_from_axes(z_axis=-ax, y_axis=(0, -1, 0))
        fd.add(Ellipsoid(c, (0.06, 0.028, 0.072), R=R), 0.008, 5)
        fd.add(Ellipsoid(c + v3((0, -0.014, 0.004)), (0.044, 0.02, 0.052), R=R), 0.01, 5)
    return fd


# ======================================================================================= the cropped tech jacket
JK_OFF, JK_T = 0.03, 0.013
JK_OUT = JK_OFF + JK_T / 2
HEM_Z = 1.035                              # the jacket's hem (cropped at her lower ribs)
SLEEVE_T = 0.1                             # the sleeves end this far down the forearm from the elbow (fraction of el -> wr)
COLLAR_Z = (1.392, 1.478)


def open_w(z):
    """Half the front opening's width at height z."""
    return F(0.03) + F(0.03) * smoothstep(1.36, 1.08, z)


def sleeve_end(side):
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    return el + ax * (float(np.linalg.norm(wr - el)) * SLEEVE_T), ax


def jk_sleeve_cut(P):
    """> 0 past the sleeves' ends (only near the forearms)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        c, ax = sleeve_end(side)
        wr = J["wrist_" + side]
        along = (P - c.astype(F)) @ ax.astype(F)
        near = _seg_dist_np(P, c - ax * 0.12, wr + ax * 0.25) < F(0.13)
        out = np.maximum(out, np.where(near, along, F(-1.0)))
    return out


def jk_cut(P):
    """> 0 where there is no jacket: below the hem (round her torso only), above the neckline, past the sleeves' ends,
    in the front opening."""
    z = P[:, 2]
    torso = np.abs(P[:, 0]) < F(0.34)
    hem = np.where(torso, F(HEM_Z) - z, F(-1.0))
    opn = np.where(P[:, 1] < F(0.0), open_w(z) - np.abs(P[:, 0]), F(-1.0))
    return np.maximum(np.maximum(np.maximum(hem, neck_line(P, 1.41)), jk_sleeve_cut(P)), opn)


def jacket_field():
    """Graphite tech fabric (label 0): cropped at her lower ribs, open down the front, the sleeves ending just below the
    elbows; black (5) trim along every edge, a stand collar, a seam over each shoulder, a zip (gunmetal, 9) along each
    front edge."""
    fd = Field("Jacket")
    hull = arms_hull()
    wr_ = lambda P: (F(0.0012) * NOISE(P * F(26)) + F(0.0014) * np.sin(P[:, 2] * F(60) + F(2) * NOISE(P * F(5))) * smoothstep(0.24, 0.36, np.abs(P[:, 0])))
    fd.add(Inter(Shell(hull, JK_OFF, JK_T, pad=0.1, disp=wr_, disp_amp=0.0025), Func(jk_cut, (-1, -0.6, 0.8), (1, 0.6, 1.7)), 0.004), 0.0)
    # trim: a band along the edges (painted black), thickened a little
    fd.paint(Func(lambda P: -jk_cut(P) - F(0.016), (-1, -0.6, 0.8), (1, 0.6, 1.7)), 5)
    # the stand collar, open at the front
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    def collar(P):
        z = P[:, 2]
        band = np.maximum(F(COLLAR_Z[0]) - z, z - (F(COLLAR_Z[1]) - F(0.02) * smoothstep(0.0, -0.08, P[:, 1])))
        opn = np.where(P[:, 1] < F(0.0), F(0.032) - np.abs(P[:, 0]), F(-1.0))
        return np.maximum(band, opn)
    fd.add(Inter(Shell(nk, 0.026, 0.012, pad=0.08), Func(collar, (-0.3, -0.3, 1.3), (0.3, 0.3, 1.6)), 0.004), 0.008)
    fd.paint(Inter(Shell(nk, 0.026, 0.02, pad=0.08), Func(lambda P: np.abs(P[:, 2] - F(COLLAR_Z[1] - 0.006)) - F(0.008), (-0.3, -0.3, 1.3), (0.3, 0.3, 1.6)), 0.0), 5)
    # the zips: a raised tape along each front edge
    for sx in (-1, 1):
        def zipf(P, sx=sx):
            x = P[:, 0] * F(sx)
            return np.maximum(np.maximum(np.abs(x - (open_w(P[:, 2]) + F(0.006))) - F(0.004), P[:, 1] - F(0.0)),
                              np.maximum(F(HEM_Z + 0.006) - P[:, 2], P[:, 2] - F(1.4)))
        fd.add(Inter(Shell(hull, JK_OUT + 0.002, 0.006, pad=0.1), Func(zipf, (-0.4, -0.5, 0.9), (0.4, 0.2, 1.5)), 0.002), 0.003, 9)
    # the sleeves' cuffs: a thicker band
    for side in ("R", "L"):
        c, ax = sleeve_end(side)
        arm = arm_hull(side)
        def cuff(P, c=c, ax=ax):
            s = (P - c.astype(F)) @ ax.astype(F)
            near = _seg_dist_np(P, c - ax * 0.08, c + ax * 0.08) < F(0.14)
            return np.where(near, np.abs(s + F(0.014)) - F(0.014), F(1.0))
        fd.add(Inter(Shell(arm, JK_OFF + 0.004, JK_T + 0.006, pad=0.06), Func(cuff, c - 0.2, c + 0.2), 0.004), 0.004, 5)
    # a hem band
    th = torso_hull()
    def hemband(P):
        opn = np.where(P[:, 1] < F(0.0), open_w(P[:, 2]) - np.abs(P[:, 0]), F(-1.0))
        return np.maximum(np.abs(P[:, 2] - F(HEM_Z + 0.013)) - F(0.013), opn)
    fd.add(Inter(Shell(th, JK_OFF + 0.004, JK_T + 0.006, pad=0.08), Func(hemband, (-0.5, -0.4, 0.9), (0.5, 0.4, 1.2)), 0.004), 0.004, 5)
    return fd


def strips_field():
    """The jacket's light strips (they glow violet: `GlowStrips`, weighted as the jacket): down each front edge, round
    the hem, over each shoulder and down the outside of each sleeve, round each cuff."""
    fd = Field("Strips")
    hull = arms_hull()
    th = torso_hull()
    S_OFF, S_T = JK_OUT + 0.0035, 0.006
    lo, hi = (-1, -0.6, 0.8), (1, 0.6, 1.7)
    # the front edges
    def edges(P):
        x = np.abs(P[:, 0])
        return np.maximum(np.maximum(np.abs(x - (open_w(P[:, 2]) + F(0.019))) - F(0.0042), P[:, 1] - F(0.02)),
                          np.maximum(F(HEM_Z + 0.03) - P[:, 2], P[:, 2] - F(1.39)))
    fd.add(Inter(Shell(hull, S_OFF, S_T, pad=0.1), Func(edges, (-0.4, -0.5, 0.9), (0.4, 0.2, 1.5)), 0.002), 0.0)
    # the hem: a strip above the hem band
    def hem(P):
        opn = np.where(P[:, 1] < F(0.0), open_w(P[:, 2]) + F(0.012) - np.abs(P[:, 0]), F(-1.0))
        return np.maximum(np.abs(P[:, 2] - F(HEM_Z + 0.036)) - F(0.0042), opn)
    fd.add(Inter(Shell(th, S_OFF, S_T, pad=0.1), Func(hem, (-0.5, -0.4, 0.95), (0.5, 0.4, 1.15)), 0.002), 0.002)
    # over each shoulder (from the collar to the shoulder's point) and down the outside of the sleeve to its cuff
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        def over(P, sx=sx):
            x = P[:, 0] * F(sx)
            return np.maximum(np.abs(P[:, 1] - F(0.055)) - F(0.0042), np.maximum(F(0.12) - x, np.maximum(x - F(0.33), F(1.34) - P[:, 2])))
        fd.add(Inter(Shell(hull, S_OFF, S_T, pad=0.1), Func(over, (sx * 0.2 - 0.2, -0.2, 1.2), (sx * 0.2 + 0.2, 0.3, 1.6)), 0.002), 0.002)
        c, axf = sleeve_end(side)
        arm = arm_hull(side)
        a0, a1 = sh + v3((sx * 0.06, 0, 0.04)), c
        def down(P, a0=a0, a1=a1, sx=sx):
            ax = norm(a1 - a0)
            s = (P - a0.astype(F)) @ ax.astype(F)
            q = P - a0.astype(F) - s[:, None] * ax.astype(F)
            out = norm(v3((sx, 0, 0)) - ax * (sx * ax[0]))
            bn = np.cross(ax, out)
            L = float(np.linalg.norm(a1 - a0))
            return np.maximum(np.maximum(np.abs(q @ bn.astype(F)) - F(0.0042), -(q @ out.astype(F))),
                              np.maximum(-s, s - F(L - 0.032)))
        fd.add(Inter(Shell(arm, S_OFF, S_T, pad=0.08), Func(down, np.minimum(a0, a1) - 0.15, np.maximum(a0, a1) + 0.15), 0.002), 0.002)
        def ring(P, c=c, ax=axf):
            s = (P - c.astype(F)) @ ax.astype(F)
            near = _seg_dist_np(P, c - ax * 0.08, c + ax * 0.08) < F(0.14)
            return np.where(near, np.abs(s + F(0.036)) - F(0.0042), F(1.0))
        fd.add(Inter(Shell(arm, S_OFF, S_T, pad=0.06), Func(ring, c - 0.2, c + 0.2), 0.002), 0.002)
    return fd


# ======================================================================================= gloves, bracer, holo-deck
def gloves_field():
    """Black fingerless gloves (label 5): over the back of the hand and the palm, her fingers bare from the knuckles;
    a padded cuff at each wrist (gunmetal (9) knuckle plate on the back)."""
    fd = Field("Gloves")
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        s = HAND_S
        Rp = np.stack([t, n, f], axis=1)
        c = wr + f * 0.076 * s
        palm = Field("Palm" + side)
        palm.add(RoundBox(c - f * 0.006, v3((0.06, 0.03, 0.058)) * s, 0.028 * s, R=Rp), 0.027)
        palm.add(Ellipsoid(c - n * 0.01 + t * 0.03 * s - f * 0.01, v3((0.033, 0.028, 0.05)) * s, R=Rp), 0.018)
        fd.add(Shell(palm, 0.006, 0.008, pad=0.05, disp=lambda P: F(0.0007) * NOISE(P * F(60)), disp_amp=0.001), 0.003, 5)
        fd.add(RoundBox(c - n * 0.036 + f * 0.012, v3((0.05, 0.008, 0.03)) * s, 0.006, R=Rp), 0.004, 9)   # knuckle plate
        el = J["elbow_" + side]
        ax = norm(wr - el)
        arm = Field("Fore" + side)
        arm.add(_forearm(side), 0.0)
        hand(arm, side)
        def cuff(P, wr=wr, ax=ax):
            s_ = (P - wr.astype(F)) @ ax.astype(F)
            return np.abs(s_ + F(0.004)) - F(0.026)
        fd.add(Inter(Shell(arm, 0.014, 0.014, pad=0.06), Func(cuff, wr - 0.2, wr + 0.2), 0.004), 0.006, 5)
    return fd


def forearm_frame(side):
    """(el, ax: down the forearm, out: the back of the forearm (away from her body), top: its thumb side, L)."""
    sx = -1 if side == "R" else 1
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    out = norm(v3((sx, 0, 0)) - ax * float(v3((sx, 0, 0)) @ ax))
    top = norm(np.cross(ax, out))
    if top[1] > 0:
        top = -top
    return el, ax, out, top, float(np.linalg.norm(wr - el))


def forearm_field(side):
    f = Field("Forearm" + side)
    for p, k in arm_prims(side)[3:5]:
        f.add(p, k)
    return f


DECK_T = (0.34, 0.86)                     # the deck's housing: from this far down her left forearm to that
DECK_C = 0.6                              # the screen's middle (fraction el -> wr)
DECK_HALF = (0.03, 0.068)                 # the screen's half width (across the forearm) and half length


DECK_ANG = math.radians(100.0)           # the screen's place round her left forearm: from its back toward its thumb side


def deck_frame():
    """(centre, normal, along the forearm, across it) of the holo-deck's screen on the thumb side of her left forearm
    (the side that faces up when she raises it before her, anim_nova.py)."""
    el, ax, out, top, L = forearm_frame("L")
    nrm = norm(out * math.cos(DECK_ANG) + top * math.sin(DECK_ANG))
    c0 = el + ax * (L * DECK_C)
    f = forearm_field("L")
    h, ok = ray_hit(Func(lambda P: f.eval(P, margin=0.1) - F(SUIT_OUT + 0.02), c0 - 0.3, c0 + 0.3), [c0 + nrm * 0.25], [-nrm], tmax=0.3)
    base = h[0] if ok[0] else c0 + nrm * 0.07
    across = norm(np.cross(nrm, ax))
    return base, nrm, ax, across


def bracers_field():
    """Gunmetal (label 9) and black (5): on her right forearm a slim armoured guard on its back; on her left the
    holo-deck's housing: a bracer round the forearm (black straps), a raised frame round the screen (on the forearm's
    thumb side) with keys along one side (painted violet (6) pips)."""
    fd = Field("Bracers")
    # the right guard
    el, ax, out, top, L = forearm_frame("R")
    f = forearm_field("R")
    def guard(P):
        s = (P - el.astype(F)) @ ax.astype(F)
        q = P - el.astype(F) - s[:, None] * ax.astype(F)
        fac = (q @ out.astype(F)) / (np.sqrt((q * q).sum(1)) + F(1e-6))
        return np.maximum(np.maximum(F(L * 0.4) - s, s - F(L * 0.86)), F(0.2) - fac)
    fd.add(Inter(Shell(f, SUIT_OUT + 0.012, 0.012, pad=0.06), Func(guard, el - 0.4, el + 0.4), 0.004), 0.0, 9)
    for s0 in (0.5, 0.74):
        fd.add(Inter(Shell(f, SUIT_OUT + 0.004, 0.009, pad=0.06),
                     Func(lambda P, s0=s0: np.abs((P - el.astype(F)) @ ax.astype(F) - F(L * s0)) - F(0.011), el - 0.4, el + 0.4), 0.003), 0.003, 5)
    # the left: the deck's housing
    el, ax, out, top, L = forearm_frame("L")
    f = forearm_field("L")
    def band(P, s0, s1):
        s = (P - el.astype(F)) @ ax.astype(F)
        return np.maximum(F(L * s0) - s, s - F(L * s1))
    fd.add(Inter(Shell(f, SUIT_OUT + 0.008, 0.012, pad=0.06), Func(lambda P: band(P, *DECK_T), el - 0.4, el + 0.4), 0.004), 0.004, 5)
    c, n, a, t = deck_frame()
    R = np.stack([t, a, n], 1)
    fd.add(RoundBox(c, (DECK_HALF[0] + 0.014, DECK_HALF[1] + 0.016, 0.008), 0.006, R=R), 0.008, 9)
    fd.sub(RoundBox(c + n * 0.012, (DECK_HALF[0] + 0.002, DECK_HALF[1] + 0.002, 0.008), 0.004, R=R), 0.003)
    for k in range(5):                                                                   # keys along its thumb side
        p = c + t * (DECK_HALF[0] + 0.02) + a * (-0.05 + 0.025 * k) + n * 0.004
        fd.add(RoundBox(p, (0.006, 0.008, 0.005), 0.003, R=R), 0.002, 5)
        fd.paint(Sphere(p + n * 0.005, 0.0045), 6)
    return fd


def deck_field():
    """The holo-deck's screen in its frame (it glows violet: `GlowDeck`)."""
    fd = Field("Deck")
    c, n, a, t = deck_frame()
    R = np.stack([t, a, n], 1)
    fd.add(RoundBox(c + n * 0.007, (DECK_HALF[0], DECK_HALF[1], 0.004), 0.003, R=R), 0.0)
    return fd


# ======================================================================================= belt and holster, boots
BELT_Z, BELT_W = 0.9, 0.022


def _hips():
    hips = Field("Hips")
    tp = torso_prims()
    hips.add(tp[4][0], 0.0)
    hips.add(tp[5][0], tp[5][1])
    return hips


def belt_point(angle_deg, gap=0.0, z=BELT_Z):
    """A point on the belt's outer face at an angle round her (0 at her front, + toward her left), and the outward
    direction."""
    hips = _hips()
    a = math.radians(angle_deg)
    d = v3((math.sin(a), -math.cos(a), 0.0))
    h, ok = ray_hit(Func(lambda P: hips.eval(P, margin=0.12) - F(0.034 + gap), (-1, -1, 0.6), (1, 1, 1.2)),
                    [v3((0, 0.04, z)) + d * 0.7], [-d], tmax=0.8)
    return (h[0] if ok[0] else v3((0, 0.04, z)) + d * 0.25), d


DOCK_ANGLE = -98.0                       # the holster's dock on her right hip, a little behind her side
DOCK_Z = (0.6, 0.86)


def dock_frame():
    """(centre of the dock plate's face, its outward normal, its down axis, its forward axis) on her right thigh."""
    lb = legs_hull("R")
    a = math.radians(DOCK_ANGLE)
    d = v3((math.sin(a), -math.cos(a), 0.0))
    zc = 0.74
    hip = J["hip_R"]
    o = v3((hip[0], hip[1], zc)) + d * 0.5
    h, ok = ray_hit(Func(lambda P: lb.eval(P, margin=0.12) - F(SUIT_OUT + 0.016), hip - v3((0.6, 0.6, 0.6)), hip + v3((0.6, 0.6, 0.3))), [o], [-d], tmax=0.6)
    c = h[0] if ok[0] else v3((hip[0], hip[1], zc)) + d * 0.13
    down = norm(J["knee_R"] - hip)
    out = norm(d - down * float(d @ down))
    fwd = norm(np.cross(down, out))
    if fwd[1] > 0:
        fwd = -fwd
    return c, out, down, fwd


def dock_gun():
    """(G: the grip's middle, A: the emitter's direction, U: the pistol's top) of the pistol docked on her thigh (rest
    pose): the emitter down, its top toward her front, its left side on the plate, the grip up by her hip."""
    c, out, down, fwd = dock_frame()
    A, U = down, fwd
    s = GUN_SCALE
    recv = c + out * (0.014 + 0.046) - down * 0.05
    G = recv - A * (0.04 * s) - U * 0.04                  # (its height centred on the plate)
    return G, A, U


def belt_field():
    """A slim black belt (label 5) round her hips, a gunmetal (9) buckle; the holster's dock on her right thigh: a
    graphite (13) plate (a gunmetal clamp rail, a violet (6) status light), hung from the belt by a strap, two black
    straps round her thigh."""
    fd = Field("Belt")
    hips = _hips()
    def belt(P):
        d = hips.eval(P, margin=0.12)
        return np.maximum(np.abs(d - F(0.03)) - F(0.008), np.abs(P[:, 2] - F(BELT_Z)) - F(BELT_W))
    fd.add(Func(belt, (-0.42, -0.4, 0.8), (0.42, 0.45, 1.0), disp=lambda P: F(0.0007) * NOISE(P * F(40)), disp_amp=0.001), 0.0, 5)
    bc, d = belt_point(0.0, 0.006)
    R = np.stack([v3((1, 0, 0)), v3((0, -1, 0)), v3((0, 0, 1))], 1)
    fd.add(RoundBox(bc + v3((0, -0.004, 0)), (0.036, 0.008, 0.024), 0.006, R=R), 0.003, 9)
    fd.paint(RoundBox(bc + v3((0, -0.012, 0)), (0.016, 0.004, 0.005), 0.002, R=R), 6)
    # the dock
    c, out, down, fwd = dock_frame()
    Rd = np.stack([fwd, out, -down], 1)
    fd.add(RoundBox(c + out * 0.006 + down * 0.0, (0.05, 0.008, 0.1), 0.008, R=Rd), 0.004, 13)
    fd.add(RoundBox(c + out * 0.016, (0.012, 0.006, 0.085), 0.004, R=Rd), 0.003, 9)                      # the clamp rail
    fd.paint(Sphere(c + out * 0.016 - down * 0.075 + fwd * 0.034, 0.008), 6)
    bp, bd = belt_point(DOCK_ANGLE, 0.004)
    top = c - down * 0.1 + out * 0.004
    fd.add(Chain([bp + v3((0, 0, -0.01)), lerp(bp, top, 0.5) + out * 0.004, top], [0.012, 0.011, 0.011], k=0.004), 0.004, 5)
    lb = legs_hull("R")
    hip, kn = J["hip_R"], J["knee_R"]
    ax = norm(kn - hip)
    for s0 in (0.2, 0.34):
        p0 = hip + ax * (float(np.linalg.norm(kn - hip)) * s0)
        fd.add(Inter(Shell(lb, SUIT_OUT + 0.004, 0.009, pad=0.06),
                     Func(lambda P, p0=p0: np.abs((P - p0.astype(F)) @ ax.astype(F)) - F(0.012), p0 - 0.25, p0 + 0.25), 0.003), 0.004, 5)
    return fd


def boots_field():
    """Sleek black boots (label 0) to mid-calf: a smooth shaft with a seam up the front, a violet (6) band round the top
    (under a black (5) rolled collar), a graphite (13) shin plate, a thick rubber (12) sole with a stacked heel."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        bb = boot_hull(side)
        an, kn = J["ankle_" + side], J["knee_" + side]
        lo, hi = an - v3((0.2, 0.3, 0.2)), kn + v3((0.2, 0.2, 0.1))
        fd.add(Inter(Shell(bb, 0.016, 0.014, pad=0.06, disp=lambda P: F(0.0008) * NOISE(P * F(30)), disp_amp=0.001),
                     Func(lambda P: P[:, 2] - boot_top(P), lo, hi), 0.004), 0.0)
        def collar(P):
            t = boot_top(P)
            return np.abs(P[:, 2] - (t - F(0.008))) - F(0.01)
        fd.add(Inter(Shell(bb, 0.022, 0.012, pad=0.06), Func(collar, lo, hi), 0.003), 0.004, 5)
        fd.paint(Inter(Shell(bb, 0.016, 0.03, pad=0.06), Func(lambda P: np.abs(P[:, 2] - (boot_top(P) - F(0.031))) - F(0.007), lo, hi), 0.0), 6)
        # the shin plate
        def shin(P, an=an, kn=kn):
            ax = norm(kn - an)
            s = (P - an.astype(F)) @ ax.astype(F)
            q = P - an.astype(F) - s[:, None] * ax.astype(F)
            fwd = -q[:, 1] / (np.sqrt((q * q).sum(1)) + F(1e-6))
            return np.maximum(np.maximum(F(0.09) - s, s - F(0.225)), F(0.6) - fwd)
        fd.add(Inter(Shell(bb, 0.028, 0.01, pad=0.06), Func(shin, lo, hi), 0.004), 0.004, 13)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        lug = lambda P: F(0.0018) * np.abs(np.sin(P[:, 1] * F(150)))
        fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.092)), (0.07, 0.158, 0.014), 0.009, R=Rz, disp=lug, disp_amp=0.002), 0.006, 12)
        fd.add(RoundBox(an + fwd * -0.012 + v3((0, 0, -0.082)), (0.058, 0.052, 0.022), 0.008, R=Rz), 0.006, 12)
        fd.sub(Torus(an + fwd * 0.155 + v3((0, 0, -0.065)), 0.062, 0.0022, R=rot_from_axes(z_axis=fwd + v3((0, 0, 0.6)))), 0.0015)
    return fd


# ======================================================================================= the laser pistol
GUN_G0 = v3((-0.3, -0.5, 0.92))           # rest: the grip's middle (floating before her right hip) ...
GUN_A0 = v3((0.0, -1.0, 0.0))             # ... the emitter pointing ahead
GUN_U0 = v3((0.0, 0.0, 1.0))
GUN_S0 = np.cross(GUN_A0, GUN_U0)         # (her right: the pistol's right side as she holds it)
BAR_H = 0.086                             # the emitter's axis above the grip's middle
MUZZLE_U = 0.292                          # the lens' face
GUN_SCALE = 1.2                           # (drawn at 1, shipped 1.2 times bigger about the grip: it reads from above)


def _gr(u, v=0.0, h=0.0):
    return GUN_G0 + GUN_A0 * u + GUN_S0 * v + GUN_U0 * h


def gl(u, v=0.0, h=0.0):
    return GUN_G0 + (GUN_A0 * u + GUN_S0 * v + GUN_U0 * h) * GUN_SCALE


def grip_axis():
    """The grip's axis (from its foot up toward the housing: raked, the foot further back)."""
    return norm(GUN_U0 * 0.94 + GUN_A0 * 0.34)


def muzzle():
    return gl(MUZZLE_U, 0.0, BAR_H)


def laser_field():
    """Gloss-black polymer (label 0): the housing and the emitter's hood; black rubber (12): the grip; gunmetal (9): the
    side plates, the power cell on top, the finned shroud, the trigger and its guard; violet (6) paint on the cell's
    caps."""
    fd = Field("Laser")
    A, U, S = GUN_A0, GUN_U0, GUN_S0
    Rg = np.stack([S, A, U], 1)
    Ra = rot_from_axes(z_axis=A)
    tex = lambda P: F(0.0005) * NOISE(P * F(90))
    # the grip
    ga = grip_axis()
    gs = norm(np.cross(ga, S))
    Rgr = np.stack([S, gs, ga], 1)
    fd.add(RoundBox(_gr(0.0, 0.0, -0.004), (0.018, 0.024, 0.058), 0.014, R=Rgr, disp=tex, disp_amp=0.001), 0.0, 12)
    fd.add(RoundBox(_gr(0.0) - ga * 0.06 + gs * -0.004, (0.021, 0.028, 0.008), 0.006, R=Rgr), 0.006, 0)        # its foot
    # the housing: a chunky body, its back sloped
    fd.add(RoundBox(_gr(0.04, 0.0, 0.074), (0.029, 0.104, 0.036), 0.016, R=Rg), 0.012, 0)
    fd.sub(RoundBox(_gr(-0.085, 0.0, 0.118), (0.05, 0.04, 0.03), 0.01, R=Rg @ euler(0.6, 0, 0)), 0.01)
    for sv in (-1, 1):
        fd.add(RoundBox(_gr(0.05, sv * 0.03, 0.07), (0.004, 0.072, 0.022), 0.003, R=Rg), 0.003, 9)          # side plates
    # the power cell on top: a gunmetal tube with violet caps
    fd.add(Cylinder(_gr(0.03, 0.0, 0.118), 0.017, 0.13, rr=0.006, R=Ra), 0.006, 9)
    for u in (-0.03, 0.09):
        fd.paint(Cylinder(_gr(u, 0.0, 0.118), 0.02, 0.012, R=Ra), 6)
    for u in (0.0, 0.03, 0.06):
        fd.sub(RoundBox(_gr(u, 0.0, 0.134), (0.008, 0.008, 0.006), 0.003, R=Rg), 0.002)                      # (vent slots)
    # the barrel shroud with cooling fins
    fd.add(RoundBox(_gr(0.2, 0.0, BAR_H), (0.021, 0.07, 0.023), 0.01, R=Rg), 0.008, 9)
    for k in range(4):
        u = 0.158 + 0.03 * k
        fd.add(RoundBox(_gr(u, 0.0, BAR_H), (0.027, 0.0045, 0.029), 0.004, R=Rg), 0.003, 9)
    # the emitter's hood, recessed round the lens
    fd.add(Cylinder(_gr(0.276, 0.0, BAR_H), 0.027, 0.034, rr=0.008, R=Ra), 0.006, 0)
    fd.sub(Cylinder(_gr(MUZZLE_U + 0.004, 0.0, BAR_H), 0.019, 0.02, rr=0.003, R=Ra), 0.002)
    # the trigger and its guard
    fd.add(Chain([_gr(0.03, 0.0, 0.04), _gr(0.034, 0.0, 0.006), _gr(0.096, 0.0, 0.006), _gr(0.108, 0.0, 0.04)], [0.0058] * 4, k=0.003), 0.003, 9)
    fd.add(RoundCone(_gr(0.062, 0.0, 0.042), _gr(0.068, 0.0, 0.018), 0.0055, 0.0045), 0.002, 9)
    # a rear heat sink
    for k in range(3):
        fd.add(RoundBox(_gr(-0.062, 0.0, 0.05 + 0.016 * k), (0.026, 0.01, 0.004), 0.003, R=Rg), 0.003, 9)
    return ScaledField(fd, GUN_G0, GUN_SCALE)


def emitter_field():
    """The emitter's lens in its hood and a light strip along each side of the housing (they glow violet:
    `GlowEmitter`)."""
    fd = Field("Emitter")
    A, U, S = GUN_A0, GUN_U0, GUN_S0
    Rg = np.stack([S, A, U], 1)
    Ra = rot_from_axes(z_axis=A)
    fd.add(Cylinder(_gr(MUZZLE_U - 0.006, 0.0, BAR_H), 0.0175, 0.01, rr=0.003, R=Ra), 0.0)
    fd.add(Sphere(_gr(MUZZLE_U - 0.012, 0.0, BAR_H), 0.0165), 0.004)
    for sv in (-1, 1):
        fd.add(RoundBox(_gr(0.05, sv * 0.0345, 0.096), (0.0035, 0.07, 0.0042), 0.002, R=Rg), 0.0)
    return ScaledField(fd, GUN_G0, GUN_SCALE)


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.232, 1.622)), 0.045, 0.4)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.085, -0.15, 1.6)), 0.06, 0.5), (hp((-0.174, 0.035, 1.66)), 0.05, 0.45 if sx < 0 else 0.0),
                (J["elbow_" + sd] + v3((0, 0.022, 0)), 0.05, 0.25)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.01, 0.028, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "nova"
ROOT_NAME = "HeroNovaHQ"
TEX_PREFIX = "hero"
MAT_NAME = "NovaMat"
MESH_NAME = "Nova"
BASE_MODULE = "nova_base"
ANIM_MODULE = "anim_nova"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Streak", "Visor", "VisorLens", "Headset", "Suit", "Jacket", "Strips", "Gloves",
         "Bracers", "Deck", "Belt", "Boots", "Laser", "Emitter"]
REGION_PARTS = ("Skin", "Visor", "Headset", "Suit", "Jacket", "Gloves", "Bracers", "Belt", "Boots", "Laser")
KIT = dict(weave=1.0, black=(0.05, 0.05, 0.06), red=VIOLET, white=(0.92, 0.92, 0.95), gunmetal=GUNMETAL,
           rubber=(0.08, 0.08, 0.09), coyote=GRAPHITE)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_NovaSkin", "base": (0.84, 0.64, 0.52), "ruddy": (0.88, 0.52, 0.46), "lips": (0.72, 0.34, 0.4),
                      "nails": (0.42, 0.2, 0.5), "brow": ((0.06, 0.05, 0.06), (0.16, 0.13, 0.15)),
                      "extra": ((LASH, (0.05, 0.04, 0.06), 0.5),)}),
    "Hair": ("hair", {"name": "HQ_NovaHair", "base": (0.1, 0.09, 0.12), "hi": (0.32, 0.29, 0.38), "low": (0.035, 0.03, 0.045),
                      "streak": (0.06, 0.05, 0.08), "tint": (0.16, 0.13, 0.22)}),
    "Streak": ("hair", {"name": "HQ_NovaStreak", "base": (0.74, 0.2, 0.84), "hi": (0.98, 0.56, 1.0), "low": (0.38, 0.07, 0.48),
                        "streak": (0.56, 0.12, 0.68), "tint": (0.86, 0.3, 0.92)}),
    "Visor": ("modern_kit", dict(KIT, name="HQ_NovaKit", base=BLACK, weave=0.0)),
    "Headset": ("modern_kit", dict(KIT, name="HQ_NovaKit", base=BLACK, weave=0.0)),
    "Suit": ("modern_kit", dict(KIT, name="HQ_NovaSuit", base=NAVY)),
    "Jacket": ("modern_kit", dict(KIT, name="HQ_NovaJacket", base=GRAPHITE)),
    "Gloves": ("modern_kit", dict(KIT, name="HQ_NovaKit", base=BLACK, weave=0.0)),
    "Bracers": ("modern_kit", dict(KIT, name="HQ_NovaKit", base=BLACK, weave=0.0)),
    "Belt": ("modern_kit", dict(KIT, name="HQ_NovaKit", base=BLACK, weave=0.0)),
    "Boots": ("modern_kit", dict(KIT, name="HQ_NovaBoots", base=(0.07, 0.07, 0.08), weave=0.0)),
    "Laser": ("modern_kit", dict(KIT, name="HQ_NovaLaser", base=(0.06, 0.06, 0.07), weave=0.0)),
}
GLOW = {"Strips": (VIOLET, 1.1, 0.5), "Deck": ((0.9, 0.45, 1.0), 1.0, 0.5), "VisorLens": (VIOLET, 0.9, 0.45),
        "Emitter": (VIOLET, 1.3, 0.55)}
LOW_TARGETS = {"Skin": 7000, "Teeth": 100, "Hair": 2600, "Streak": 260, "Visor": 500, "VisorLens": 160, "Headset": 400,
               "Suit": 3000, "Jacket": 2600, "Strips": 900, "Gloves": 900, "Bracers": 900, "Deck": 60, "Belt": 900,
               "Boots": 1300, "Laser": 2000, "Emitter": 160}
AO_EXCLUDE = ["Laser", "Emitter", "Strips", "VisorLens", "Deck"]
BAKE_APART = (["Laser", "Emitter"], (3.0, 0.0, 0.0))     # (the pistol floats before her)


def prop_bones():
    """The pistol rides a parentless bone (every clip poses it in world space, anim_nova.py)."""
    return [("laser", GUN_G0, muzzle(), None)]


COAT_BONES = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}


def boots_weights(ob, skin_ob, arm):
    _isla_boots_weights(ob, skin_ob, arm)


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Streak": ("rigid", "head"),
        "Visor": ("rigid", "head"), "VisorLens": ("rigid", "head"), "Headset": ("rigid", "head"),
        "Suit": ("transfer", None, None),
        "Jacket": ("transfer", COAT_BONES, None),
        "Strips": ("transfer", COAT_BONES, None),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Bracers": ("transfer", {"forearm.R", "forearm.L"}, None),
        "Deck": ("rigid", "forearm.L"),
        "Belt": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.35, "thigh.L": 0.25}),
        "Boots": ("custom", boots_weights),
        "Laser": ("rigid", "laser"), "Emitter": ("rigid", "laser"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Laser", "Jacket", "Bracers", "Visor"):
        return 1.1
    if part in ("Suit", "Belt", "Boots"):
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Streak", streak_field(), 0.0022 if fine else 0.0032),
        ("Visor", visor_field(), 0.0016 if fine else 0.0024),
        ("VisorLens", visor_lens_field(), 0.0014 if fine else 0.002),
        ("Headset", headset_field(), 0.0016 if fine else 0.0024),
        ("Suit", suit_field(), 0.0026 if fine else 0.0036),
        ("Jacket", jacket_field(), 0.0024 if fine else 0.0034),
        ("Strips", strips_field(), 0.0016 if fine else 0.0024),
        ("Gloves", gloves_field(), 0.0016 if fine else 0.0024),
        ("Bracers", bracers_field(), 0.0016 if fine else 0.0024),
        ("Deck", deck_field(), 0.0014 if fine else 0.002),
        ("Belt", belt_field(), 0.0018 if fine else 0.0026),
        ("Boots", boots_field(), 0.0018 if fine else 0.0026),
        ("Laser", laser_field(), 0.0014 if fine else 0.002),
        ("Emitter", emitter_field(), 0.0012 if fine else 0.0018),
    ]
