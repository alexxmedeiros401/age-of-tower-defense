"""Captain Isla Reyes, Privateer (HQ hero, Gunpowder Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A dashing privateer captain in her thirties: sun-browned skin, a strong jaw, a confident lopsided grin (her left corner
drawn up, the upper teeth showing), dark eyes, a small scar through her left eyebrow, a gold hoop in her left ear; thick
dark curly hair tied back loosely in a bunch of ringlets, a few curls loose at her temples; a red bandana under a black
felt tricorne edged with gold braid, a long blue feather swept back from it. A long deep-blue frock coat: wide
turned-back cuffs, gold buttons, gold trim along its front edges, hem, collar and pocket flaps, open at the chest over a
white linen shirt with a ruffled jabot at her throat (lace at her wrists), its skirts flaring from her waist to her knees;
a crimson sash knotted at her right hip and a wide black belt with a big brass buckle over it; a buff baldric over her
right shoulder carrying a cutlass (a curved steel blade, a brass basket hilt) in a black scabbard on her left hip; snug
buff breeches and tall black boots with turned-down tan cuffs. In her fists a pair of flintlock pistols (walnut stocks,
steel barrels and locks, brass butt caps and nose caps).

She has Kira's build (kira.py) with both hands made fists (Brenna's, brenna.py) and Wren's booted feet (wren.py). Each
pistol rides its own parentless bone (pistol_R, pistol_L: the grip's middle to the muzzle), the cutlass its own
(cutlass: the grip's middle to the blade's point; sheathed at rest). The clips pose the props in world space
(anim_isla.py): a pistol in its fist or tucked through the sash, the cutlass in the scabbard or in her right fist."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
from kira import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S,
                  fist_center, torso_prims, traps, neck_prim, deltoid, upper_arm, _forearm, eyes_field, TORSO, TORSO_Z,
                  torso_bones, ear_lobe)
from brenna import hand, leg_prims
from wren import foot

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH = 0, 1, 2, 3, 4, 5, 8
SCAR = 10
IRIS = ((0.16, 0.09, 0.05), (0.36, 0.21, 0.11))          # dark brown eyes (prep.paint_eyes)


def _seg_dist_np(P, a, b):
    """Distance of each point to the segment a-b (float32 arrays)."""
    a = v3(a).astype(F)
    ab = (v3(b) - v3(a)).astype(F)
    t = np.clip(((P - a) @ ab) / F(ab @ ab), 0, 1)
    c = a + t[:, None] * ab
    return np.sqrt(((P - c) ** 2).sum(1))


def _seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
    return float(np.linalg.norm(a + ab * t - p))


# ======================================================================================= head
def head(fd):
    """Kira's face made a woman in her thirties: a broader jaw and a squarer chin, the brows confident (her left one a
    touch raised, a scar through it), a lopsided grin: her left corner drawn up into the cheek, the lips parted on her
    upper teeth, the lower lids lifted a little by the smile."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.058, 1.594), (0.143, 0.132, 0.127)), 0.07, SKIN)                          # a strong jaw
    fd.add(E((0, -0.134, 1.506), (0.077, 0.066, 0.064)), 0.05, SKIN)                          # a firm, square chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.03, -0.141, 1.499), 0.032), 0.03, SKIN)                                # the chin's corners
        fd.add(S((sx * 0.113, -0.036, 1.55), 0.04), 0.05, SKIN)                                 # the jaw's angles
        fd.add(S((sx * 0.108, -0.118, 1.638), 0.039), 0.05, SKIN)                              # cheekbones
        fd.add(S((sx * 0.112, -0.05, 1.566), 0.043), 0.05, SKIN)
        pts = [hp((sx * 0.15, -0.06, 1.744)), hp((sx * 0.115, -0.128, 1.75)), hp((sx * 0.062, -0.162, 1.748))]
        fd.add(Chain(pts, [hr(0.011), hr(0.015), hr(0.013)], k=hr(0.02)), hr(0.03), SKIN)
    # brows: arched, confident; her left one (+X) a touch higher, split by the scar
    for sx in (-1, 1):
        lift = 0.005 if sx > 0 else 0.0
        pts = [hp((sx * 0.035, -0.201, 1.764 + lift * 0.5)), hp((sx * 0.072, -0.195, 1.777 + lift)),
               hp((sx * 0.112, -0.172, 1.781 + lift)), hp((sx * 0.148, -0.133, 1.771 + lift * 0.6))]
        rr = [hr(0.005), hr(0.0065), hr(0.0056), hr(0.0026)]
        rp = [hr(0.012), hr(0.014), hr(0.012), hr(0.0065)]
        if sx < 0:
            fd.add(Chain([p + v3((0, 0.008, 0)) for p in pts], rr, k=hr(0.006)), hr(0.01), BROW)
            fd.paint(Chain(pts, rp, k=hr(0.01)), BROW)
        else:
            g0 = lerp(pts[1], pts[2], 0.42)                    # the scar's gap
            g1 = lerp(pts[1], pts[2], 0.72)
            for seg, r_, p_ in (([pts[0], pts[1], g0], rr[:2] + [hr(0.004)], rp[:2] + [hr(0.009)]),
                                ([g1, pts[2], pts[3]], [hr(0.004)] + rr[2:], [hr(0.009)] + rp[2:])):
                fd.add(Chain([p + v3((0, 0.008, 0)) for p in seg], r_, k=hr(0.006)), hr(0.01), BROW)
                fd.paint(Chain(seg, p_, k=hr(0.01)), BROW)
    # the scar: a pale nick down through her left brow
    scar = [hp((0.086, -0.2, 1.802)), hp((0.093, -0.195, 1.78)), hp((0.1, -0.189, 1.758))]
    fd.sub(Chain(scar, [hr(0.002), hr(0.0026), hr(0.0018)], k=hr(0.002)), hr(0.002))
    fd.paint(Chain(scar, [hr(0.0055), hr(0.0065), hr(0.0045)], k=hr(0.004)), SCAR)
    # almond eyes, lashes on the upper lids flicked out at the corners; the lower lids lifted by the grin
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, hr(0.0195))), (sx * 0.22, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0046)), Plane(ec + v3((0, 0, -hr(0.022))), (sx * -0.16, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.008)), Plane(ec + v3((0, 0, hr(0.0155))), (sx * 0.22, 0.05, -1.0)), hr(0.002)), LASH)
        flick = ec + v3((sx * hr(0.04), -hr(0.01), hr(0.011)))
        fd.add(RoundCone(flick, flick + v3((sx * hr(0.014), hr(0.006), hr(0.006))), hr(0.0045), hr(0.0015)), hr(0.004), LASH)
    # a straight nose, a little stronger than Kira's
    fd.add(RoundCone(hp((0, -0.178, 1.722)), hp((0, -0.215, 1.648)), hr(0.0115), hr(0.0155)), hr(0.016), SKIN)
    fd.add(S((0, -0.216, 1.637), 0.0195), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.023, -0.198, 1.623), 0.0135), hr(0.01), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.012, -0.212, 1.612)), v3((0.007, 0.009, 0.005)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the lopsided grin: the mouth's line curving up to her left, the lips parted on her upper teeth
    slot = [hp((-0.056, -0.165, 1.553)), hp((-0.03, -0.189, 1.541)), hp((0, -0.197, 1.539)), hp((0.032, -0.188, 1.548)),
            hp((0.063, -0.157, 1.572))]
    fd.sub(Chain(slot, [hr(0.0022), hr(0.003), hr(0.0034), hr(0.003), hr(0.0024)], k=hr(0.003)), hr(0.003))
    gap = Ellipsoid(hp((0.008, -0.19, 1.546)), v3((0.04, 0.03, 0.0052)) * HS, R=euler(0, -0.17, 0))
    fd.sub(gap, hr(0.004))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0034)], k=hr(0.004)), MOUTH)
    fd.paint(Ellipsoid(hp((0.008, -0.183, 1.546)), v3((0.046, 0.03, 0.0085)) * HS, R=euler(0, -0.17, 0)), MOUTH)
    fd.add(S((0.068, -0.152, 1.574), 0.0135), hr(0.01), SKIN)                                    # her grin's cheek, a dimple
    fd.add(S((-0.06, -0.158, 1.558), 0.0105), hr(0.01), SKIN)
    up_lip = [(-0.054, -0.162, 1.556), (-0.028, -0.181, 1.553), (-0.008, -0.186, 1.556), (0.01, -0.186, 1.557),
              (0.034, -0.178, 1.561), (0.06, -0.156, 1.575)]
    lo_lip = [(-0.046, -0.164, 1.543), (-0.024, -0.18, 1.531), (0.002, -0.184, 1.529), (0.028, -0.178, 1.536),
              (0.052, -0.159, 1.556)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.0036), hr(0.0064), hr(0.007), hr(0.007), hr(0.0062), hr(0.0034)], k=hr(0.006)), hr(0.009), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.0044), hr(0.0078), hr(0.0086), hr(0.0076), hr(0.0042)], k=hr(0.007)), hr(0.009), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.174, 0.035, 1.66)), v3((0.024, 0.043, 0.054)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)


def teeth_field():
    """Her upper teeth, showing in the grin."""
    fd = Field("Teeth")
    pts = [hp((-0.03, -0.17, 1.55)), hp((-0.012, -0.18, 1.548)), hp((0.012, -0.181, 1.55)), hp((0.036, -0.172, 1.556))]
    fd.add(Chain(pts, [hr(0.0088)] * 4, k=hr(0.004)), 0.0)
    return fd


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.05, SKIN)
    fd.add(neck_prim(), 0.045, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.05, SKIN)
        fd.add(upper_arm(side), 0.045, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.067, 0.07, 0.102), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(_forearm(side), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.071, 0.063, 0.11), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.022, 0)), 0.044), 0.025, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= bandana, hair
BAND_F = v3((0.0, -0.17, 1.8))           # the bandana's lower edge (design coordinates): across her forehead ...
BAND_B = v3((0.0, 0.215, 1.585))         # ... down to her nape
_BAND_SLOPE = (BAND_B[2] - BAND_F[2]) / (BAND_B[1] - BAND_F[1])
_BAND_N = norm(v3((0, -_BAND_SLOPE, 1.0)))
BAND_HULL_C = HEAD_C + v3((0.0, 0.008, 0.004))
BAND_HULL_R = HEAD_RAD + v3((0.017, 0.02, 0.016))
KNOT = hp((0.045, 0.218, 1.69))          # the bandana's knot, at the back of her head


def band_d(P):
    """Signed distance (design units) above the bandana's lower edge; > 0 under the bandana."""
    return (hinv(P) - BAND_F.astype(F)) @ _BAND_N.astype(F)


def bandana_field():
    """Red cotton (label 0): tied over her head under the hat, its lower edge rolled across her forehead and round over
    the tops of her ears to her nape; knotted at the back of her head, two short tails hanging from the knot."""
    fd = Field("Bandana")
    hull = Ellipsoid(BAND_HULL_C, BAND_HULL_R)
    creases = lambda P: F(0.0022) * np.sin((P[:, 1] * F(3) + P[:, 2]) * F(70) + F(2) * NOISE(P * F(6))) + F(0.001) * NOISE(P * F(40))
    lo, hi = HEAD_C - 0.4, HEAD_C + 0.4
    fd.add(Inter(Shell(hull, 0.0, 0.012, pad=0.06, disp=creases, disp_amp=0.003), Func(lambda P: -band_d(P), lo, hi), 0.004), 0.0)
    # the rolled edge: points round the head where the edge plane meets the hull
    pts = []
    for k in range(29):
        a = -math.pi + 2 * math.pi * k / 28
        d = v3((math.sin(a), -math.cos(a), 0.0))
        # walk down from the top along the hull until band_d crosses zero
        best = None
        for el in np.linspace(1.2, -0.6, 90):
            dd = norm(d * math.cos(el) + v3((0, 0, math.sin(el))))
            p = BAND_HULL_C + dd * BAND_HULL_R
            if band_d(np.array([p], F))[0] < 0:
                best = p
                break
        if best is not None:
            pts.append(best + v3((0, 0, 0.004)))
    if len(pts) > 8:
        fd.add(Chain(pts, [0.008] * len(pts), k=0.006, disp=lambda P: F(0.0012) * NOISE(P * F(40)), disp_amp=0.0015), 0.006)
    # the knot and its tails
    fd.add(Ellipsoid(KNOT, (0.034, 0.026, 0.028), R=euler(0.3, 0, 0.2), disp=creases, disp_amp=0.003), 0.012)
    for dx, L in ((-0.02, 0.13), (0.035, 0.11)):
        a = KNOT + v3((dx * 0.3, 0.01, -0.012))
        pts = [a, a + v3((dx * 0.6, 0.028, -L * 0.45)), a + v3((dx, 0.04, -L))]
        fd.add(Lock(pts, [0.024, 0.026, 0.022], [0.006, 0.006, 0.005], [v3((0, 1, 0.1))] * 3, k=0.006, disp=creases, disp_amp=0.003), 0.008)
    return fd


TAIL_TOP = hp((0.0, 0.2, 1.585))         # where her hair is gathered at the nape


def tail_path():
    t0 = TAIL_TOP
    return [t0, t0 + v3((0.0, 0.06, -0.05)), t0 + v3((0.004, 0.09, -0.14)), t0 + v3((0.006, 0.098, -0.24)),
            t0 + v3((0.004, 0.095, -0.31))]


def _path_at(path, t):
    n = len(path) - 1
    s = min(int(t * n), n - 1)
    u = t * n - s
    return lerp(path[s], path[s + 1], u), norm(path[s + 1] - path[s])


def _ringlet(fd, pts, r_coil, r_hair, turns, phase, label=0):
    """A ringlet: a helix of hair round the polyline `pts` (a chain of round cones), thinning to its end."""
    path = [v3(p) for p in pts]
    n = max(12, int(turns * 7))
    out, rads = [], []
    for i in range(n + 1):
        t = i / n
        c, d = _path_at(path, t)
        u = norm(np.cross(d, v3((1, 0, 0)))) if abs(d[0]) < 0.9 else norm(np.cross(d, v3((0, 1, 0))))
        w = np.cross(d, u)
        a = phase + 2 * math.pi * turns * t
        rc = r_coil * (1.0 - 0.3 * t)
        out.append(c + (u * math.cos(a) + w * math.sin(a)) * rc)
        rads.append(r_hair * (1.0 - 0.45 * t ** 1.5))
    fd.add(Chain(out, rads, k=r_hair * 0.8), r_hair * 0.6, label)


def hair_field(seed=11):
    """Thick dark curls: a curly band below the bandana from behind her ears round to her nape, a few loose ringlets at
    her temples, and the hair gathered loosely at her nape into a thick bunch of ringlets falling between her shoulders."""
    rng = np.random.RandomState(seed)
    fd = Field("Hair")
    curls = lambda P: F(0.006) * np.abs(NOISE(P * F(55))) + F(0.003) * NOISE(P * F(110))
    head = Ellipsoid(HEAD_C, HEAD_RAD)
    def region(P):
        Q = hinv(P)
        b = band_d(P)
        under = b - F(0.016)                                     # tucked under the bandana's edge
        deep = F(0.02) + F(0.11) * smoothstep(0.02, 0.17, Q[:, 1])
        below = -b - deep                                        # how far below the edge it reaches (deep at the back)
        ears = np.where((np.abs(Q[:, 0]) > F(0.12)) & (Q[:, 1] < F(0.085)), F(0.02), F(-1.0))
        face = np.where(Q[:, 1] < F(-0.04), F(0.02), F(-1.0))
        nape = F(1.505) - P[:, 2]                                # (clear of the coat's collar)
        return np.maximum(np.maximum(np.maximum(under, below), np.maximum(ears, face)), nape)
    fd.add(Inter(Shell(head, 0.018, 0.03, pad=0.06, disp=curls, disp_amp=0.007), Func(region, HEAD_C - 0.4, HEAD_C + 0.4), 0.008), 0.0)
    # loose ringlets at her temples, in front of her ears, from under the bandana to her jaw
    for sx in (-1, 1):
        for j, (dy, L) in enumerate(((-0.075, 0.12), (-0.045, 0.15))):
            top = hp((sx * 0.155, dy, 1.715))
            bot = hp((sx * (0.165 + 0.01 * j), dy - 0.01, 1.715 - L))
            _ringlet(fd, [top, lerp(top, bot, 0.5) + v3((sx * 0.008, 0, 0)), bot], 0.009, 0.0105, 3.0 + j, rng.uniform(0, 6.28))
    # the gathered bunch: a core and ringlets round it, spreading a little as they fall
    path = tail_path()
    core = [p + v3((0, -0.012, 0)) for p in path]
    fd.add(Lock(core, [0.05, 0.062, 0.058, 0.048, 0.03], [0.034, 0.042, 0.04, 0.032, 0.018], [v3((0, 1, 0))] * 5, k=0.02, disp=curls, disp_amp=0.007), 0.02)
    for k in range(9):
        a = 2 * math.pi * k / 9 + rng.uniform(-0.2, 0.2)
        spread = v3((math.cos(a), 0.0, 0.0)) * 0.034 + v3((0, math.sin(a) * 0.022, 0))
        L = rng.uniform(0.8, 1.0)
        pts = [path[0] + spread * 0.5, path[1] + spread * 1.0, path[2] + spread * 1.2, path[3] + spread * 1.25,
               lerp(path[3], path[4], L) + spread * 1.1]
        _ringlet(fd, pts, 0.012, 0.0125, 6.5 * L, rng.uniform(0, 6.28))
    fd.add(Ellipsoid(TAIL_TOP + v3((0, 0.03, 0.0)), (0.06, 0.045, 0.045)), 0.02)            # where it is gathered
    return fd


# ======================================================================================= the tricorne
HAT_O = HEAD_C + v3((0.0, -0.01, 0.122))       # the middle of the brim's floor
HAT_R = euler(-0.1, 0.03, 0.0)                 # tipped back a little (the front corner up), cocked a hair to her left
HAT_A = 0.215                                  # the side walls' distance from the middle (plan)
HAT_D = 0.45                                   # the side walls' curvature (radius - HAT_A of each side's arc)
HAT_WALL = 0.075                               # the turned-up brim's height at the middle of a side
HAT_LEAN = 0.32
HAT_T = 0.012
CROWN_R = v3((0.174, 0.186, 0.135))


def hat_local(P):
    return ((P - HAT_O.astype(F)) @ HAT_R.astype(F)).astype(F)


def hat_world(q):
    return HAT_O + HAT_R @ v3(q)


def _tri_plan(L):
    """Signed distance in plan to the tricorne's outline (three arcs, the front corner toward -Y), growing as it rises."""
    x, y, z = L[:, 0], L[:, 1], L[:, 2]
    a = F(HAT_A) + F(HAT_LEAN) * np.maximum(z, F(0))
    d = None
    for k in range(3):
        th = 2 * math.pi * k / 3
        cu = (math.sin(th), -math.cos(th))                  # corner k's direction; the side opposite it faces -cu
        cx, cy = cu[0] * HAT_D, cu[1] * HAT_D               # that side's arc centre (beyond the corner)
        dk = np.sqrt((x - F(cx)) ** 2 + (y - F(cy)) ** 2) - (F(HAT_D) + a)
        d = dk if d is None else smax(d, dk, 0.018)
    return d


def _wall_top(L):
    """Height of the turned-up brim's edge: a little higher at the three corners."""
    ang = np.arctan2(L[:, 0], -L[:, 1])
    return F(HAT_WALL) + F(0.012) * np.cos(ang * F(3)) ** 2 * np.sign(np.cos(ang * F(3))).clip(0, 1) + F(0.003) * NOISE(L * F(20))


def hat_field():
    """Black felt (label 0): a round crown, the brim turned up into three walls meeting in three corners, one over her
    brow; gold braid (5) along the walls' top edge, a gold cord round the crown's foot."""
    fd = Field("Hat")
    felt = lambda P: F(0.0008) * NOISE(P * F(60))
    def tray(P):
        L = hat_local(P)
        d_open = smax(_tri_plan(L), -L[:, 2], 0.03)
        shell = np.abs(d_open) - F(HAT_T * 0.5)
        return np.maximum(shell, L[:, 2] - _wall_top(L))
    m = 0.5
    fd.add(Func(tray, HAT_O - v3((0.4, 0.4, 0.07)), HAT_O + v3((0.4, 0.4, 0.17)), disp=felt, disp_amp=0.001), 0.0)
    crown = Ellipsoid(HAT_O + HAT_R @ v3((0, 0.012, 0.0)), CROWN_R, R=HAT_R, disp=felt, disp_amp=0.001)
    fd.add(Inter(crown, Func(lambda P: -hat_local(P)[:, 2] - F(0.01), HAT_O - m, HAT_O + m), 0.004), 0.02)
    # the braid along the top edge of the walls (both faces)
    fd.paint(Func(lambda P: (_wall_top(hat_local(P)) - F(0.016)) - hat_local(P)[:, 2], HAT_O - m, HAT_O + m), 5)
    # a cord round the crown's foot
    pts = []
    for k in range(33):
        a = 2 * math.pi * k / 32
        d = v3((math.sin(a), -math.cos(a), 0.0))
        r = CROWN_R[0] * CROWN_R[1] / math.sqrt((CROWN_R[1] * d[0]) ** 2 + (CROWN_R[0] * d[1]) ** 2)
        pts.append(hat_world(v3((d[0] * r, d[1] * r + 0.012, 0.012))))
    fd.add(Chain(pts, [0.0075] * len(pts), k=0.004), 0.004, 5)
    return fd


def feather_pts():
    """The plume's spine: from the gutter at her left behind the crown, up and swept back past the hat's back."""
    q = [(0.2, 0.06, 0.02), (0.215, 0.13, 0.11), (0.215, 0.25, 0.16), (0.18, 0.38, 0.145), (0.13, 0.48, 0.095)]
    return [hat_world(v3(p)) for p in q]


def feather_field():
    """A long blue ostrich plume: a pale quill (label 5), barbs grooved across it, curling at its tip."""
    fd = Field("Feather")
    pts = feather_pts()
    n = len(pts)
    barbs = lambda P: F(0.0025) * np.abs(np.sin((P @ np.array([0.2, 1.0, 0.4], F)) * F(160))) + F(0.001) * NOISE(P * F(90))
    ws = [0.016, 0.034, 0.042, 0.036, 0.016]
    ts = [0.006, 0.009, 0.01, 0.009, 0.006]
    ns = []
    for i in range(n):
        d = norm(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])
        up = norm(HAT_R @ v3((0.35, 0.0, 1.0)))
        ns.append(norm(up - d * float(up @ d)))
    fd.add(Lock(pts, ws, ts, ns, k=0.01, disp=barbs, disp_amp=0.003), 0.0)
    fd.add(Chain(pts[:4], [0.0045, 0.0042, 0.0038, 0.003], k=0.002), 0.002, 5)
    return fd


# ======================================================================================= the frock coat
COAT_OFF, COAT_T = 0.03, 0.014
COAT_OUT = COAT_OFF + COAT_T / 2           # the coat's outer surface (distance from its hull)
HEM_Z = 0.47
SKIRT_Z = (0.9, 0.4)                       # the skirts' flare: from the waist to below her knees
SKIRT_RX = (0.19, 0.32)
SKIRT_RY = (0.155, 0.285)
SKIRT_YC = (0.04, 0.085)


SKIRT_LO, SKIRT_HI = (-0.34, -0.22, 0.38), (0.34, 0.39, 0.92)


def skirt_sd(P):
    """The coat's skirts: a flared elliptic frustum from her waist to below her knees, hanging a little back."""
    z = P[:, 2]
    t = np.clip((F(SKIRT_Z[0]) - z) / F(SKIRT_Z[0] - SKIRT_Z[1]), 0, 1)
    rx = F(SKIRT_RX[0]) + F(SKIRT_RX[1] - SKIRT_RX[0]) * t
    ry = F(SKIRT_RY[0]) + F(SKIRT_RY[1] - SKIRT_RY[0]) * t
    yc = F(SKIRT_YC[0]) + F(SKIRT_YC[1] - SKIRT_YC[0]) * t
    q = np.sqrt((P[:, 0] / rx) ** 2 + ((P[:, 1] - yc) / ry) ** 2)
    d_side = (q - F(1.0)) * np.minimum(rx, ry)
    d_z = np.maximum(z - F(SKIRT_Z[0]), F(SKIRT_Z[1]) - z)
    return np.maximum(d_side, d_z)


def coat_hull(arms=True):
    b = Field("CoatHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(Func(skirt_sd, SKIRT_LO, SKIRT_HI), 0.06)
    if arms:
        for side in ("R", "L"):
            sx = -1 if side == "R" else 1
            sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
            b.add(deltoid(side), 0.05)
            b.add(upper_arm(side), 0.045)
            b.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.06, 0.063, 0.1), R=rot_from_axes(z_axis=el - sh)), 0.035)
            b.add(_forearm(side), 0.03)
            b.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.064, 0.057, 0.105), R=rot_from_axes(z_axis=wr - el)), 0.035)
            b.add(Sphere(el + v3((0, 0.022, 0)), 0.042), 0.025)
    return b


def coat_w(z):
    """Half width of the coat's front opening at height z: a V from her collarbones closing at her waist, the skirts
    parting below it."""
    up = F(0.008) + F(0.098) * smoothstep(0.95, 1.43, z)
    lo = F(0.01) + F(0.15) * smoothstep(0.9, 0.5, z)
    return np.where(z > F(0.93), up, lo)


def coat_hem(P):
    return F(HEM_Z) - F(0.025) * smoothstep(0.0, 0.25, P[:, 1]) + F(0.008) * NOISE(P * F(6))


def coat_neck(P):
    """> 0 above the neckline: round her neck only (lifted clear of the shoulders, so it opens no hole on them)."""
    ax = np.abs(P[:, 0])
    return P[:, 2] - (F(1.435) + F(0.075) * smoothstep(-0.04, 0.12, P[:, 1]) + F(0.3) * smoothstep(0.13, 0.2, ax))


def cuff_cut(P):
    """> 0 past the sleeves' ends at her wrists, only near her forearms (a cut limited to the limb it serves)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = wr - ax * 0.008
        along = (P - c.astype(F)) @ ax.astype(F)
        near = _seg_dist_np(P, el, wr + ax * 0.2) < F(0.14)
        out = np.maximum(out, np.where(near, along, F(-1.0)))
    return out


def coat_front(P):
    """> 0 inside the front opening (on her front only)."""
    return np.where(P[:, 1] < F(0.0), coat_w(P[:, 2]) - np.abs(P[:, 0]), F(-1.0))


def coat_vent(P):
    return np.where((P[:, 1] > F(0.12)) & (P[:, 2] < F(0.74)), F(0.007) - np.abs(P[:, 0]), F(-1.0))


def coat_cut(P):
    return np.maximum(np.maximum(np.maximum(coat_neck(P), coat_front(P)), np.maximum(coat_hem(P) - P[:, 2], cuff_cut(P))), coat_vent(P))


def coat_folds(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.05)))
    skirt = smoothstep(0.86, 0.5, P[:, 2])
    return (F(0.008) * np.sin(a * F(9) + F(0.8) * NOISE(P * F(3))) * skirt + F(0.0012) * NOISE(P * F(28))
            + F(0.002) * np.sin(P[:, 2] * F(70)) * smoothstep(0.86, 0.95, np.abs(P[:, 0]) / F(0.62)))


CUFF_A, CUFF_B = 0.5, 1.02                 # the cuffs: from halfway down the forearm to the wrist (fractions of el -> wr)
CUFF_R = (0.1, 0.112)


def cuff_frame(side):
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    L = float(np.linalg.norm(wr - el))
    return el + ax * (L * CUFF_A), el + ax * (L * CUFF_B), ax


def pocket_specs():
    """(centre, outward normal, its angle) of the two pocket flaps on the skirts' fronts."""
    hull = coat_hull(arms=False)
    out = []
    for sx in (-1, 1):
        a = sx * math.radians(52)
        d = v3((math.sin(a), -math.cos(a), 0.0))
        z = 0.745
        h, ok = ray_hit(Func(lambda P: hull.eval(P, margin=0.1) - F(COAT_OUT + 0.003), (-1, -1, 0.5), (1, 1, 1.0)),
                        [v3((0, 0.05, z)) + d * 0.7], [-d], tmax=0.8)
        if ok[0]:
            out.append((h[0], d, a))
    return out


def _button(fd, c, nrm, r=0.0125, label=0):
    R = rot_from_axes(z_axis=nrm)
    fd.add(Cylinder(c + nrm * 0.002, r, 0.008, rr=0.003, R=R), 0.0, label)
    fd.add(Sphere(c + nrm * 0.002, r * 0.62), 0.004, label)


def coat_field():
    """Deep blue wool (label 0) with gold trim (5): the coat open at her chest in a V down to her waist, its skirts parting
    below it and flaring to her knees (folds, a vent at the back); a standing collar behind her neck; the front edges
    turned back in a raised gold-trimmed facing; wide turned-back cuffs edged in gold, two gold buttons on each; the shirt's
    lace frilled at her wrists (6: white); pocket flaps on the skirts."""
    fd = Field("Coat")
    hull = coat_hull()
    lo, hi = (-1, -1, 0.3), (1, 1, 1.7)
    fd.add(Inter(Shell(hull, COAT_OFF, COAT_T, pad=0.05, disp=coat_folds, disp_amp=0.009), Func(lambda P: coat_cut(P), lo, hi), 0.005), 0.0)
    # the front edges: a raised facing along the opening (gold-trimmed), from the collar to the hem
    def facing(P):
        e = np.where(P[:, 1] < F(0.0), np.abs(P[:, 0]) - coat_w(P[:, 2]), F(1.0))         # distance from the edge, on the cloth
        band = np.abs(e - F(0.014)) - F(0.014)
        return np.maximum(np.maximum(band, coat_neck(P) + F(0.004)), np.maximum(coat_hem(P) - P[:, 2] + F(0.002), P[:, 1] - F(-0.04)))
    hull_t = coat_hull(arms=False)
    fd.add(Inter(Shell(hull_t, COAT_OFF + 0.006, 0.012, pad=0.12), Func(facing, (-0.5, -0.6, 0.3), (0.5, 0.2, 1.6)), 0.003), 0.004, 5)
    # gold trim painted along the hem
    fd.paint(Func(lambda P: P[:, 2] - (coat_hem(P) + F(0.03)), (-1, -1, 0.3), (1, 1, 0.62)), 5)
    # the standing collar behind her neck (gold along its top)
    nh = Field("NeckHull")
    nh.add(neck_prim(), 0.0)
    nh.add(traps(), 0.05)
    def collar(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        top = F(1.505) + F(0.015) * smoothstep(0.0, 0.12, y)
        return np.maximum(np.maximum(z - top, F(1.43) - z), F(-0.035) - y + F(0.06) * smoothstep(0.06, 0.12, np.abs(x)))
    fd.add(Inter(Shell(nh, 0.034, 0.013, pad=0.08), Func(collar, (-0.3, -0.3, 1.3), (0.3, 0.4, 1.65)), 0.004), 0.006)
    fd.paint(Func(lambda P: (F(1.49) + F(0.015) * smoothstep(0.0, 0.12, P[:, 1])) - P[:, 2], (-0.3, -0.3, 1.3), (0.3, 0.4, 1.65)), 5)
    # wide turned-back cuffs, flaring to the wrist, gold-edged at their top
    for side in ("R", "L"):
        a, b, ax = cuff_frame(side)
        cone = RoundCone(a, b, CUFF_R[0], CUFF_R[1])
        Lc = float(np.linalg.norm(b - a))
        def cband(P, a=a, ax=ax, Lc=Lc):
            s = (P - a.astype(F)) @ ax.astype(F)
            return np.maximum(-s, s - F(Lc))
        fd.add(Inter(Shell(cone, 0.0, 0.016, pad=0.05, disp=lambda P: F(0.001) * NOISE(P * F(30)), disp_amp=0.0015),
                     Func(cband, a - 0.25, b + 0.25), 0.003), 0.004)
        fd.paint(Func(lambda P, a=a, ax=ax: (P - a.astype(F)) @ ax.astype(F) - F(0.026), a - 0.25, a + 0.25), 5)
    # lace at the wrists: a short frilled flare round each wrist, just past the cuff
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        a, b = wr - ax * 0.03, wr + ax * 0.018
        def lace(P, wr=wr, ax=ax):
            q = P - wr.astype(F)
            ref = norm(np.cross(ax, v3((0, 1, 0))))
            u = q @ ref.astype(F)
            w = q @ norm(np.cross(ax, ref)).astype(F)
            return F(0.004) * np.sin(np.arctan2(w, u) * F(14)) * smoothstep(-0.01, 0.018, q @ ax.astype(F))
        cone = RoundCone(a, b, 0.056, 0.07)
        def lband(P, a=a, ax=ax):
            s = (P - a.astype(F)) @ ax.astype(F)
            return np.maximum(-s, s - F(0.048))
        fd.add(Inter(Shell(cone, 0.0, 0.007, pad=0.04, disp=lace, disp_amp=0.005), Func(lband, a - 0.2, b + 0.2), 0.002), 0.003, 6)
    for side in ("R", "L"):
        a, b, ax = cuff_frame(side)
        sx = -1 if side == "R" else 1
        out = norm(v3((sx, 0.0, 0.0)) - ax * float(v3((sx, 0, 0)) @ ax))
        for t in (0.3, 0.6):
            c = lerp(a, b, t) + out * (CUFF_R[0] + (CUFF_R[1] - CUFF_R[0]) * t + 0.008)
            _button(fd, c, out, 0.011, 5)
    # pocket flaps on the skirts' fronts, gold-trimmed
    for c, d, ang in pocket_specs():
        def flap(P, c=c, ang=ang):
            a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.05)))
            da = np.abs(a - F(ang)) * F(0.3)
            dz = P[:, 2] - F(c[2])
            return np.maximum(da - F(0.06), np.maximum(dz - F(0.022), -dz - F(0.03) + F(0.012) * np.cos(da * F(52))))
        fd.add(Inter(Shell(hull_t, COAT_OFF + 0.012, 0.012, pad=0.1), Func(flap, c - 0.2, c + 0.2), 0.003), 0.004)
        fd.paint(Func(lambda P, flap=flap: np.abs(flap(P) + F(0.006)) - F(0.006), c - 0.2, c + 0.2), 5)
    return fd


# ======================================================================================= shirt, jabot, lace
def shirt_hull():
    b = Field("ShirtHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    return b


def jabot_specs():
    """(centre, its outward normal, half width, half height) of the jabot's tiers, down her breast from her throat."""
    hull = shirt_hull()
    out = []
    for k, z in enumerate((1.425, 1.375, 1.325, 1.275)):
        h, ok = ray_hit(Func(lambda P: hull.eval(P, margin=0.1) - F(0.02), (-0.5, -0.6, 1.0), (0.5, 0.4, 1.6)),
                        [v3((0.0, -0.6, z))], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            out.append((h[0] + v3((0, -0.004 * k, 0.0)), 0.044 + 0.007 * k, 0.034))
    return out


def shirt_field():
    """White linen (label 0): the shirt's front showing in the coat's V, a high collar (stock) round her throat, the
    ruffled jabot falling in four frilled tiers from it (the lace at her wrists is the coat's: it rides the cuffs)."""
    fd = Field("Shirt")
    hull = shirt_hull()
    wr_ = lambda P: F(0.0014) * NOISE(P * F(30)) + F(0.0012) * np.sin(P[:, 0] * F(140))
    def keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        return np.maximum(np.maximum(y - F(0.03), np.abs(x) - F(0.17)), np.maximum(F(0.9) - z, z - F(1.46)))
    fd.add(Inter(Shell(hull, 0.012, 0.01, pad=0.1, disp=wr_, disp_amp=0.002), Func(keep, (-0.5, -0.5, 0.85), (0.5, 0.2, 1.6)), 0.004), 0.0)
    # the stock: a high collar round her throat
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    fd.add(Inter(Shell(nk, 0.012, 0.012, pad=0.06), Func(lambda P: np.abs(P[:, 2] - F(1.45)) - F(0.028), (-0.3, -0.3, 1.3), (0.3, 0.3, 1.6)), 0.004), 0.006)
    # the jabot: frilled tiers, each a little wider and further out than the one above
    for c, hw, hh in jabot_specs():
        R = rot_from_axes(z_axis=(0, -1, 0.15), x_axis=(1, 0, 0))
        def frill(P, c=c):
            q = P - c.astype(F)
            a = np.arctan2(q[:, 2], q[:, 0])
            return F(0.0045) * np.sin(a * F(15) + F(0.5) * NOISE(P * F(20))) + F(0.001) * NOISE(P * F(60))
        fd.add(Ellipsoid(c + v3((0, -0.006, -0.006)), (hw, 0.016, hh), R=R, disp=frill, disp_amp=0.005), 0.008)
    return fd


# ======================================================================================= sash, belt, baldric, scabbard
SASH_Z = 0.94
SASH_IN, SASH_OUT = COAT_OUT + 0.015, COAT_OUT + 0.042        # (over the coat and the baldric)
BELT_Z = 0.945
BELT_IN, BELT_OUT = SASH_OUT - 0.004, SASH_OUT + 0.014
BALD_IN, BALD_OUT = COAT_OUT + 0.002, COAT_OUT + 0.014
BALD_C0 = v3((-0.16, 0.06, 1.48))          # the baldric: over her right shoulder ...
BALD_N = norm(v3((0.838, 0.0, 0.545)))     # ... down to her left hip (the normal of its plane)
BALD_W = 0.036                             # half its width


def waist_hull():
    return coat_hull(arms=False)


def sash_knot():
    wh = waist_hull()
    a = math.radians(-72)
    d = v3((math.sin(a), -math.cos(a), 0.0))
    h, ok = ray_hit(Func(lambda P: wh.eval(P, margin=0.12) - F(SASH_OUT), (-1, -1, 0.8), (1, 1, 1.1)), [v3((0, 0.04, SASH_Z - 0.02)) + d * 0.7], [-d], tmax=0.8)
    return (h[0] if ok[0] else v3((-0.27, -0.06, 0.92))), d


def sash_field():
    """Crimson silk (label 0) wound round her waist over the coat, knotted at her right hip, its two ends hanging
    fringed (5)."""
    fd = Field("Sash")
    wh = waist_hull()
    fold = lambda P: F(0.0035) * np.sin(P[:, 2] * F(150) + F(1.5) * NOISE(P * F(5))) + F(0.0015) * NOISE(P * F(30))
    def band(P):
        return np.abs(P[:, 2] - (F(SASH_Z) + F(0.012) * P[:, 0])) - F(0.048)
    def cloth(P):
        d = wh.eval(P, margin=0.12)
        return np.maximum(d - (F(SASH_OUT) - fold(P)), F(SASH_IN) - d)
    fd.add(Inter(Func(cloth, (-0.34, -0.32, 0.87), (0.34, 0.36, 1.01)), Func(band, (-0.34, -0.32, 0.87), (0.34, 0.36, 1.01)), 0.005), 0.0)
    k0, d = sash_knot()
    fd.add(Ellipsoid(k0 + d * 0.012, (0.036, 0.026, 0.032), R=rot_from_axes(z_axis=d), disp=fold, disp_amp=0.004), 0.01)
    side = norm(np.cross(v3((0, 0, 1)), d))
    for dx, L in ((-0.025, 0.25), (0.03, 0.21)):
        p0 = k0 + d * 0.012
        pts = [p0, p0 + side * dx * 0.5 + d * 0.014 + v3((0, 0, -L * 0.5)), p0 + side * dx + d * 0.022 + v3((0, 0, -L))]
        fd.add(Lock(pts, [0.03, 0.034, 0.036], [0.007, 0.007, 0.006], [d] * 3, k=0.008, disp=fold, disp_amp=0.004), 0.006)
        end = pts[-1]
        fd.paint(Sphere(end, 0.03), 5)
        for j in range(6):                                                  # the fringe
            o = end + side * (-0.026 + 0.0104 * j)
            fd.add(RoundCone(o, o + v3((0, 0, -0.032)) + d * 0.004, 0.0035, 0.0022), 0.002, 5)
    return fd


def buckle_center():
    wh = waist_hull()
    h, ok = ray_hit(Func(lambda P: wh.eval(P, margin=0.12) - F(BELT_OUT), (-1, -1, 0.8), (1, 1, 1.1)), [v3((0.0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.8)
    return h[0] if ok[0] else v3((0.0, -0.24, BELT_Z))


def bald_band(P):
    return np.abs((P - BALD_C0.astype(F)) @ BALD_N.astype(F)) - F(BALD_W)


def bald_hull():
    b = Field("BaldHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(Func(skirt_sd, SKIRT_LO, SKIRT_HI), 0.06)
    return b


# the cutlass, sheathed at rest: its frame (the grip's middle, the blade's direction, its edge's direction)
SC_DIR = norm(v3((0.55, 0.45, -1.0)))       # down along the scabbard: raked back, splayed out over the coat's skirt
SC_ANGLE = 60.0                             # the throat's place round her (degrees from her front toward her left)
SC_Z = 0.86
CUT_GRIP = 0.075                            # the grip's middle above the scabbard's throat
CUT_BLADE = (0.056, 0.6)                    # the blade from the guard to the point (along A from the grip's middle)
CUT_CURVE = 0.16                            # the blade's curve: its back bows toward -E by CUT_CURVE * s^2
CUT_W = 0.022                               # the blade's half width
_FROG = None


def _coat_point(angle_deg, z, gap):
    """A point `gap` out from the coat's outer surface at an angle round her (from her front toward her left) and a
    height; with the outward direction."""
    hull = coat_hull(arms=False)
    a = math.radians(angle_deg)
    d = v3((math.sin(a), -math.cos(a), 0.0))
    h, ok = ray_hit(Func(lambda P: hull.eval(P, margin=0.12) - F(COAT_OUT + gap), (-1, -1, 0.5), (1, 1, 1.2)),
                    [v3((0, 0.04, z)) + d * 0.7], [-d], tmax=0.8)
    return (h[0] if ok[0] else v3((0.25, -0.1, z))), d


def cutlass_rest():
    """(grip centre, A: along the blade, E: toward its edge, W = A x E, the scabbard's throat) as sheathed at the front
    of her left hip, the hilt forward for her right hand's cross draw."""
    global _FROG
    if _FROG is None:
        _FROG = _coat_point(SC_ANGLE, SC_Z, 0.032)
    throat, d = _FROG
    A = SC_DIR
    E = v3((0, 0, -1)) - A * float(v3((0, 0, -1)) @ A)
    E = norm(E)
    W = np.cross(A, E)
    return throat - A * CUT_GRIP, A, E, W, throat


def cut_point(s, side=0.0, g=None):
    """A point of the blade's back line at s along it (from the grip's middle), `side` across toward the edge."""
    G, A, E, W, _ = cutlass_rest() if g is None else g
    return G + A * s - E * (CUT_CURVE * max(0.0, s - CUT_BLADE[0]) ** 2) + E * side


def cutlass_tip():
    return cut_point(CUT_BLADE[1], CUT_W * 0.35)


def _blade_strip(P, a, b, wa, wb, side, half_t):
    d = b - a
    L = float(np.linalg.norm(d))
    ax = d / L
    nrm = norm(np.cross(ax, side))
    q = P - a.astype(F)
    u = q @ ax.astype(F)
    v = q @ side.astype(F)
    w = q @ nrm.astype(F)
    t = np.clip(u / F(L), 0, 1)
    hw = F(wa) + (F(wb) - F(wa)) * t
    th = F(half_t) * np.clip(F(1.0) - np.maximum(v, F(0)) / np.maximum(hw, F(1e-4)) * F(0.75), F(0.22), F(1))
    d_u = np.maximum(-u, u - F(L))
    d_v = np.abs(v) - hw
    d_w = np.abs(w) - th
    qq = np.stack([d_u, d_v, d_w], 1)
    return np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0)


def cutlass_field():
    """A cutlass: a broad curved steel blade (label 7) with a clipped point, a brass basket hilt (6): a dish guard, a
    knuckle bow and two side bars, a brass pommel; a black leather grip (5) bound with brass wire (6)."""
    fd = Field("Cutlass")
    G, A, E, W, _ = cutlass_rest()
    # the blade, from the guard to the point, as beveled strips along its curve (the edge on the convex side)
    n = 16
    s0, s1 = CUT_BLADE
    for i in range(n):
        sa, sb = s0 + (s1 - s0) * i / n, s0 + (s1 - s0) * (i + 1) / n
        ta, tb = (sa - s0) / (s1 - s0), (sb - s0) / (s1 - s0)
        wa = CUT_W * (1.0 + 0.12 * ta) * (1.0 if ta < 0.82 else max(0.05, 1 - (ta - 0.82) / 0.18) ** 0.6)
        wb = CUT_W * (1.0 + 0.12 * tb) * (1.0 if tb < 0.82 else max(0.05, 1 - (tb - 0.82) / 0.18) ** 0.6)
        ca, cb = cut_point(sa, wa), cut_point(sb, wb)            # the strips' middles (back + half width)
        tng = norm(cb - ca)
        out = norm(E - tng * float(E @ tng))
        a2, b2 = ca - tng * 0.004, cb + tng * 0.004
        fd.add(Func(lambda P, a2=a2, b2=b2, wa=wa, wb=wb, out=out: _blade_strip(P, a2, b2, wa, wb, out, 0.0042),
                    np.minimum(a2, b2) - 0.05, np.maximum(a2, b2) + 0.05), 0.003, 7)
    fd.sub(Chain([cut_point(0.1, 0.008), cut_point(0.4, 0.008)], [0.0026, 0.002], k=0.002), 0.002)        # the fuller
    # the grip: black leather bound with brass wire
    fd.add(RoundCone(G - A * 0.055, G + A * 0.05, 0.0165, 0.0175), 0.0, 5)
    for k in range(6):
        fd.add(Torus(G + A * (-0.042 + 0.017 * k), 0.017, 0.0026, R=rot_from_axes(z_axis=A)), 0.002, 6)
    # the pommel: a brass cap
    fd.add(Sphere(G - A * 0.066, 0.021), 0.006, 6)
    fd.add(RoundCone(G - A * 0.07, G - A * 0.094, 0.012, 0.007), 0.004, 6)
    # the dish guard at the blade's foot, cupped toward the hand, wider on the edge side
    gc = G + A * 0.054 + E * 0.016
    R = rot_from_axes(z_axis=A, x_axis=E)
    fd.add(Inter(Shell(Ellipsoid(gc - A * 0.02, (0.055, 0.042, 0.03), R=R), 0.0, 0.007, pad=0.03),
                 Plane(gc - A * 0.006, -A), 0.003), 0.004, 6)
    # the knuckle bow and two side bars, from the guard's edge round to the pommel
    bow = [G + A * 0.05 + E * 0.062, G + A * 0.01 + E * 0.07, G - A * 0.035 + E * 0.058, G - A * 0.062 + E * 0.022]
    fd.add(Chain(bow, [0.0065, 0.0062, 0.006, 0.0058], k=0.004), 0.004, 6)
    for sw in (-1, 1):
        bar = [G + A * 0.046 + E * 0.03 + W * (sw * 0.036), G + A * 0.012 + E * 0.054 + W * (sw * 0.03), G - A * 0.02 + E * 0.064]
        fd.add(Chain(bar, [0.0048, 0.0046, 0.0044], k=0.004), 0.004, 6)
    return fd


def leather_field():
    """Black leather (label 0), buff leather (5), brass (6): the wide belt over the sash; the baldric over her right
    shoulder and across her breast and back to her left hip; the frog and the scabbard (a black, curved sheath with a
    brass locket and chape)."""
    fd = Field("Leather")
    wh = waist_hull()
    scuff = lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.0008) * NOISE(P * F(70))
    # the belt
    def belt(P):
        d = wh.eval(P, margin=0.12)
        return np.maximum(np.maximum(d - F(BELT_OUT), F(BELT_IN) - d), np.abs(P[:, 2] - F(BELT_Z)) - F(0.027))
    fd.add(Func(belt, (-0.32, -0.3, 0.9), (0.32, 0.36, 0.99), disp=scuff, disp_amp=0.002), 0.0)
    # the baldric (buff), lying on the coat
    bh = bald_hull()
    def baldric(P):
        d = bh.eval(P, margin=0.12)
        return np.maximum(np.maximum(d - F(BALD_OUT), F(BALD_IN) - d), bald_band(P))
    fd.add(Func(baldric, (-0.3, -0.32, 0.68), (0.4, 0.38, 1.58), disp=scuff, disp_amp=0.002), 0.0, 5)
    fd.paint(Func(lambda P: np.abs(bald_band(P) + F(0.004)) - F(0.0035), (-0.6, -0.5, 0.65), (0.6, 0.5, 1.62)), 0)      # its stitched black edges
    # the scabbard, along the blade's curve, a little bigger
    G, A, E, W, throat = cutlass_rest()
    n = 12
    s0, s1 = CUT_BLADE[0] - 0.004, CUT_BLADE[1] + 0.03
    for i in range(n):
        sa, sb = s0 + (s1 - s0) * i / n, s0 + (s1 - s0) * (i + 1) / n
        ta, tb = (sa - s0) / (s1 - s0), (sb - s0) / (s1 - s0)
        wa = (CUT_W + 0.008) * (1.0 + 0.1 * ta) * (1.0 if ta < 0.85 else max(0.35, 1 - (ta - 0.85) / 0.15 * 0.65))
        wb = (CUT_W + 0.008) * (1.0 + 0.1 * tb) * (1.0 if tb < 0.85 else max(0.35, 1 - (tb - 0.85) / 0.15 * 0.65))
        ca, cb = cut_point(sa, wa - 0.004), cut_point(sb, wb - 0.004)
        tng = norm(cb - ca)
        out = norm(E - tng * float(E @ tng))
        a2, b2 = ca - tng * 0.005, cb + tng * 0.005
        fd.add(Func(lambda P, a2=a2, b2=b2, wa=wa, wb=wb, out=out: _blade_strip(P, a2, b2, wa, wb, out, 0.011),
                    np.minimum(a2, b2) - 0.06, np.maximum(a2, b2) + 0.06), 0.006, 0)
    # the brass locket at the throat and the chape at the point
    lk = cut_point(CUT_BLADE[0] + 0.03, CUT_W * 0.5)
    fd.add(RoundBox(lk, (CUT_W + 0.014, 0.016, 0.032), 0.006, R=rot_from_axes(z_axis=A, x_axis=E)), 0.004, 6)
    ch = cut_point(CUT_BLADE[1] + 0.005, CUT_W * 0.35)
    tng = norm(cut_point(CUT_BLADE[1] + 0.02, 0) - cut_point(CUT_BLADE[1] - 0.04, 0))
    fd.add(RoundCone(ch - tng * 0.05, ch + tng * 0.025, 0.017, 0.009), 0.005, 6)
    # the frog: a buff strap from under the sash (the baldric's end) down round the locket
    ft, d = _coat_point(SC_ANGLE, SASH_Z - 0.03, 0.004)
    fd.add(Chain([ft, lerp(ft, lk, 0.5) + d * 0.01, lk + d * 0.008], [0.012, 0.011, 0.012], k=0.006), 0.006, 5)
    return fd


# ======================================================================================= breeches, boots
def leg_hull(side):
    b = Field("Leg" + side)
    for p, k in leg_prims(side):
        b.add(p, k)
    return b


def breeches_field():
    """Snug buff breeches (label 0) from her waist into her boots, creased a little at the knees."""
    fd = Field("Breeches")
    hips = Field("Hips")
    tp = torso_prims()
    hips.add(tp[4][0], 0.0)
    hips.add(tp[5][0], tp[5][1])
    crease = lambda P: F(0.0014) * NOISE(P * F(26)) + F(0.0012) * np.sin(P[:, 2] * F(110)) * smoothstep(0.52, 0.42, P[:, 2])
    fd.add(Inter(Shell(hips, 0.012, 0.01, pad=0.08), Func(lambda P: np.maximum(P[:, 2] - F(0.98), F(0.6) - P[:, 2]), (-0.6, -0.5, 0.5), (0.6, 0.5, 1.1)), 0.004), 0.0)
    for side in ("R", "L"):
        lb = leg_hull(side)
        hip = J["hip_" + side]
        fd.add(Inter(Shell(lb, 0.01, 0.01, pad=0.06, disp=crease, disp_amp=0.002),
                     Func(lambda P: np.maximum(F(0.3) - P[:, 2], P[:, 2] - F(0.86)), hip - v3((0.3, 0.3, 0.8)), hip + v3((0.3, 0.3, 0.2))), 0.004), 0.02)
    return fd


BOOT_TOP_F, BOOT_TOP_B = 0.43, 0.395         # the boot's top: higher in front (over the knee), lower behind it


def boot_hull(side):
    b = Field("BootHull" + side)
    for p, k in leg_prims(side)[3:]:
        b.add(p, k)
    foot(b, side)
    return b


def boot_top(P):
    return F(BOOT_TOP_B) + F(BOOT_TOP_F - BOOT_TOP_B) * smoothstep(0.06, -0.06, P[:, 1])


def boots_field():
    """Tall black riding boots (label 0) to her knees, higher in front; the tops turned down in wide cuffs showing their
    tan lining (5); a stacked heel and a thick sole."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        bb = boot_hull(side)
        an, kn = J["ankle_" + side], J["knee_" + side]
        wrinkle = lambda P: F(0.0025) * np.sin(P[:, 2] * F(85)) * smoothstep(0.24, 0.12, P[:, 2]) + F(0.001) * NOISE(P * F(30))
        lo, hi = an - v3((0.2, 0.3, 0.2)), kn + v3((0.2, 0.2, 0.2))
        fd.add(Inter(Shell(bb, 0.016, 0.014, pad=0.06, disp=wrinkle, disp_amp=0.003), Func(lambda P: P[:, 2] - boot_top(P), lo, hi), 0.004), 0.0)
        # the turned-down cuff: a flared band below the top, the lining out
        def cuff(P):
            t = boot_top(P)
            return np.maximum(P[:, 2] - (t + F(0.006)), (t - F(0.085)) - P[:, 2])
        flare = lambda P: F(-0.008) * smoothstep(0.36, 0.3, P[:, 2]) + F(0.001) * NOISE(P * F(30))
        fd.add(Inter(Shell(bb, 0.032, 0.012, pad=0.06, disp=flare, disp_amp=0.01), Func(cuff, lo, hi), 0.004), 0.004, 5)
        # sole and heel
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.094)), (0.068, 0.155, 0.011), 0.008, R=Rz), 0.006)
        fd.add(RoundBox(an + fwd * -0.012 + v3((0, 0, -0.084)), (0.056, 0.05, 0.02), 0.008, R=Rz), 0.006)
    return fd


# ======================================================================================= gold: buttons, buckle, earring
def _coat_surface_point(x, z, extra=0.0, hull=None):
    hull = hull or coat_hull(arms=False)
    h, ok = ray_hit(Func(lambda P: hull.eval(P, margin=0.1) - F(COAT_OFF + 0.012 + extra), (-1, -1, 0.3), (1, 1, 1.7)),
                    [v3((x, -0.7, z))], [v3((0, 1, 0))], tmax=0.9)
    return h[0] if ok[0] else None


def button_points():
    """Gold buttons down both front edges (above the sash on the facings, below it on the skirts), clear of the baldric."""
    hull = coat_hull(arms=False)
    out = []
    for sx in (-1, 1):
        for z in (1.03, 1.12, 1.21, 1.3):
            x = sx * (float(coat_w(np.array([z], F))[0]) + 0.042)
            p = _coat_surface_point(x, z, -0.005, hull)
            if p is not None and bald_band(np.array([p], F))[0] > 0.012:
                out.append(p)
        for z in (0.83, 0.71, 0.59):
            x = sx * (float(coat_w(np.array([z], F))[0]) + 0.042)
            p = _coat_surface_point(x, z, -0.005, hull)
            if p is not None and bald_band(np.array([p], F))[0] > 0.012:
                out.append(p)
    return out


def gold_field():
    """Gold (label 0): the coat's buttons (its fronts, the pocket flaps); the belt's big buckle; the hoop in her left ear."""
    fd = Field("Gold")
    for p in button_points():
        n = norm(v3((p[0] * 0.6, -1.0, 0.0)))
        _button(fd, p + n * 0.004, n)
    for c, d, ang in pocket_specs():
        for k in (-1, 0, 1):
            aa = ang + k * 0.14
            dd = v3((math.sin(aa), -math.cos(aa), 0.0))
            p = v3((0, 0.05, c[2] - 0.022)) + dd * (np.linalg.norm((c - v3((0, 0.05, c[2])))[:2]) + 0.01)
            _button(fd, p, dd, 0.01)
    # the buckle: a big brass frame, its bar and prong
    bc = buckle_center()
    R = rot_from_axes(z_axis=(0, -1, 0), x_axis=(1, 0, 0))
    frame = Inter(RoundBox(bc + v3((0, -0.004, 0)), (0.05, 0.007, 0.04), 0.005, R=R),
                  Func(lambda P, bc=bc: -np.maximum(np.abs(P[:, 0] - F(bc[0])) - F(0.032), np.abs(P[:, 2] - F(bc[2])) - F(0.022)), bc - 0.1, bc + 0.1), 0.003)
    fd.add(frame, 0.0)
    fd.add(RoundCone(bc + v3((0.0, -0.006, 0.024)), bc + v3((0.0, -0.006, -0.024)), 0.005, 0.005), 0.003)
    fd.add(RoundCone(bc + v3((0.0, -0.011, 0.0)), bc + v3((0.034, -0.011, 0.0)), 0.004, 0.0035), 0.002)
    # the hoop in her left ear
    lobe = ear_lobe(1)
    fd.add(Torus(lobe + v3((0.004, -0.004, -0.032)), 0.028, 0.0045, R=rot_from_axes(z_axis=(1, 0.25, 0))), 0.0)
    return fd


# ======================================================================================= the pistols
PB_UP = 0.076          # the barrel's axis above the grip's middle (along the pistol's U)
PB_BACK = 0.045        # its breech behind the grip's middle (along -B)
PB_LEN = 0.255         # breech -> muzzle
PB_R = (0.0155, 0.0135)


def pistol_frame(side):
    """At rest, in her fist: G the grip's middle (the fist's), B the barrel's direction (the hand's f), U the pistol's
    top (toward the thumb), S = B x U (its lock side)."""
    wr, f, n, t = hand_frame(side)
    G = fist_center(side)
    B = norm(f)
    U = norm(t - B * float(t @ B))
    S = np.cross(B, U)
    return G, B, U, S


def pistol_muzzle(side, frame=None):
    G, B, U, S = pistol_frame(side) if frame is None else frame
    return G + U * PB_UP + B * (PB_LEN - PB_BACK)


def _pistol(fd, G, B, U, S):
    """One flintlock pistol about its grip's middle G: walnut (label 0), brass (6), steel (7)."""
    breech = G + U * PB_UP - B * PB_BACK
    muzzle = breech + B * PB_LEN
    wood = lambda P: F(0.0006) * NOISE(P * np.array([80, 80, 80], F))
    # the barrel: round, tapering a little, a swelled ring at the muzzle, the bore
    fd.add(RoundCone(breech, muzzle, PB_R[0], PB_R[1]), 0.0, 7)
    fd.add(Torus(muzzle - B * 0.008, PB_R[1] + 0.001, 0.0045, R=rot_from_axes(z_axis=B)), 0.003, 7)
    fd.add(Torus(breech + B * 0.03, PB_R[0] + 0.001, 0.0035, R=rot_from_axes(z_axis=B)), 0.002, 7)
    fd.sub(Cylinder(muzzle, 0.0068, 0.05, R=rot_from_axes(z_axis=B)), 0.001)
    # the stock under the barrel to two thirds of its length, a brass nose cap
    s0, s1 = breech + B * 0.0 - U * 0.016, breech + B * (PB_LEN * 0.66) - U * 0.016
    R = rot_from_axes(z_axis=B, x_axis=S)
    fd.add(RoundBox((s0 + s1) / 2, (0.0145, 0.012, PB_LEN * 0.33), 0.009, R=R, disp=wood, disp_amp=0.001), 0.008, 0)
    fd.add(RoundBox(s1 + B * 0.006, (0.0145, 0.0115, 0.008), 0.006, R=R), 0.003, 6)
    # the grip: curving down and back from the breech to a bulbous brass butt cap
    gd = norm(-U * 0.92 - B * 0.4)
    g0, g2 = breech + B * 0.022 - U * 0.008, G - U * 0.075 - B * 0.072
    g1 = lerp(g0, g2, 0.5) - B * 0.006
    fd.add(Chain([g0, g1, g2], [0.019, 0.0175, 0.02], k=0.01, disp=wood, disp_amp=0.001), 0.01, 0)
    fd.add(Ellipsoid(g2 + gd * 0.012, (0.024, 0.027, 0.02), R=rot_from_axes(z_axis=gd, x_axis=S)), 0.006, 6)
    # the lock on its side: a plate, the cock (hammer) cocked back, the frizzen and pan
    lp = breech + B * 0.02 - U * 0.006 + S * 0.016
    fd.add(RoundBox(lp, (0.0035, 0.012, 0.03), 0.003, R=rot_from_axes(z_axis=B, x_axis=S)), 0.003, 7)
    ck = [breech - B * 0.002 + S * 0.016 + U * 0.004, breech - B * 0.012 + S * 0.016 + U * 0.024, breech - B * 0.002 + S * 0.016 + U * 0.036]
    fd.add(Chain(ck, [0.0055, 0.005, 0.0045], k=0.003), 0.003, 7)
    fd.add(RoundBox(breech + B * 0.03 + S * 0.016 + U * 0.012, (0.003, 0.012, 0.008), 0.002, R=rot_from_axes(z_axis=U, x_axis=S)), 0.003, 7)
    # the trigger, a small steel blade in front of the grip
    fd.add(RoundCone(G + U * 0.034 + B * 0.02, G + U * 0.012 + B * 0.026, 0.004, 0.003), 0.002, 7)


def pistols_field():
    """A pair of flintlock pistols, one in each fist."""
    fd = Field("Pistols")
    for side in ("R", "L"):
        _pistol(fd, *pistol_frame(side))
    return fd


# the pistols tucked through the sash (the clips put them there): grip middle, barrel direction, top
def pistol_tuck(side):
    sx = -1 if side == "R" else 1
    B = norm(v3((sx * 0.3, 0.12, -1.0)))
    U = norm(v3((sx * 0.25, 1.0, 0.0)) - B * float(v3((sx * 0.25, 1.0, 0.0)) @ B))
    breech = v3((sx * 0.105, -(0.135 + SASH_OUT) + 0.012, SASH_Z + 0.056))
    G = breech - U * PB_UP + B * PB_BACK
    return G, B, U, np.cross(B, U)


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.232, 1.622)), 0.045, 0.45)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.1, -0.15, 1.6)), 0.06, 0.55), (hp((sx * 0.174, 0.035, 1.66)), 0.05, 0.5)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.01, 0.028, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "isla"
ROOT_NAME = "HeroIslaHQ"
TEX_PREFIX = "hero"
MAT_NAME = "IslaMat"
MESH_NAME = "Isla"
BASE_MODULE = "isla_base"
ANIM_MODULE = "anim_isla"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Bandana", "Hat", "Feather", "Coat", "Shirt", "Sash", "Leather", "Breeches", "Boots",
         "Gold", "Pistols", "Cutlass"]
REGION_PARTS = ("Skin", "Hat", "Feather", "Coat", "Sash", "Leather", "Boots", "Pistols", "Cutlass")
NAVY = (0.12, 0.23, 0.52)                  # her deep blue
GOLD_C = (0.86, 0.63, 0.2)
CRIMSON = (0.56, 0.08, 0.08)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_IslaSkin", "base": (0.7, 0.47, 0.32), "ruddy": (0.76, 0.42, 0.31), "lips": (0.62, 0.32, 0.27),
                      "brow": ((0.06, 0.045, 0.04), (0.14, 0.1, 0.08)),
                      "extra": ((LASH, (0.05, 0.035, 0.03), 0.5), (SCAR, (0.86, 0.66, 0.54), 0.7))}),
    "Hair": ("hair", {"name": "HQ_IslaHair", "base": (0.1, 0.07, 0.055), "hi": (0.32, 0.23, 0.17), "low": (0.035, 0.025, 0.02),
                      "streak": (0.06, 0.04, 0.03), "tint": (0.18, 0.11, 0.07)}),
    "Bandana": ("cloth", {"name": "HQ_IslaBandana", "col": (0.74, 0.12, 0.09)}),
    "Hat": ("wool", {"name": "HQ_IslaTricorne", "base": (0.075, 0.07, 0.075), "border": GOLD_C, "stripe": GOLD_C}),
    "Feather": ("wool", {"name": "HQ_IslaPlume", "base": (0.2, 0.42, 0.88), "border": (0.92, 0.9, 0.84), "stripe": (0.92, 0.9, 0.84)}),
    "Coat": ("wool", {"name": "HQ_IslaCoat", "base": NAVY, "border": GOLD_C, "stripe": (0.95, 0.93, 0.87)}),
    "Shirt": ("linen", {"name": "HQ_IslaShirt"}),
    "Sash": ("wool", {"name": "HQ_IslaSash", "base": CRIMSON, "border": GOLD_C, "stripe": GOLD_C}),
    "Leather": ("leather_dyed", {"name": "HQ_IslaLeather", "base": (0.075, 0.065, 0.062), "dyed": (0.74, 0.58, 0.36)}),
    "Breeches": ("linen", {"name": "HQ_IslaBreeches", "base": (0.82, 0.71, 0.52)}),
    "Boots": ("leather_dyed", {"name": "HQ_IslaBoots", "base": (0.075, 0.065, 0.062), "dyed": (0.62, 0.42, 0.24)}),
    "Gold": ("gold", {"name": "HQ_IslaGold"}),
    "Pistols": ("armory", {"name": "HQ_IslaPistols"}),
    "Cutlass": ("armory", {"name": "HQ_IslaCutlass"}),
}
LOW_TARGETS = {"Skin": 6000, "Teeth": 100, "Hair": 2000, "Bandana": 700, "Hat": 1500, "Feather": 450, "Coat": 4400, "Shirt": 1500,
               "Sash": 800, "Leather": 1700, "Breeches": 500, "Boots": 1200, "Gold": 900, "Pistols": 1500, "Cutlass": 700}
AO_EXCLUDE = ["Pistols", "Cutlass", "Feather", "Gold"]
BAKE_APART = (["Cutlass"], (3.0, 0.0, 0.0))     # (sheathed at rest: baked apart from the scabbard round it)


def prop_bones():
    """The props' bones are parentless: every clip poses them in world space (anim_isla.prop_aims): a pistol in its fist
    or tucked through the sash, the cutlass in its scabbard or in her right fist (the Poser keys a bone's location only
    when it has no parent)."""
    out = []
    for side in ("R", "L"):
        G = pistol_frame(side)[0]
        out.append(("pistol_" + side, G, pistol_muzzle(side), None))
    G, A, E, W, _ = cutlass_rest()
    out.append(("cutlass", G, cutlass_tip(), None))
    return out


def hair_weights(ob, skin_ob, arm):
    """The hair on her head rides the head; the bunch at her nape blends to the neck and chest as it falls."""
    groups = {}
    z1, z0 = TAIL_TOP[2], TAIL_TOP[2] - 0.32
    for v in ob.data.vertices:
        p = v.co
        if p.z < z1 and p.y > 0.12 and abs(p.x) < 0.12:
            t = max(0.0, min(1.0, (z1 - p.z) / (z1 - z0)))
            _blend_add(ob, groups, v.index, {"head": 1.0 - 0.75 * t, "neck": 0.35 * t, "chest": 0.4 * t})
        else:
            _blend_add(ob, groups, v.index, {"head": 1.0})


COAT_BONES = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L", "hand.R", "hand.L",
                      "thigh.R", "thigh.L"}
COAT_CAPS = {"thigh.R": 0.45, "thigh.L": 0.45, "hand.R": 0.25, "hand.L": 0.25}


def coat_weights(ob, skin_ob, arm):
    """The coat follows her body and arms; its skirts swing from her hips, pulled a little by her thighs; the cuffs ride
    her forearms."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=COAT_BONES, caps=COAT_CAPS)
    groups = {}
    for side in ("R", "L"):
        a, b, ax = cuff_frame(side)
        for v in ob.data.vertices:
            p = np.array(v.co)
            if _seg_dist(p, a - ax * 0.02, b + ax * 0.01) < CUFF_R[1] + 0.03 and abs(p[0]) > 0.4:
                for g in list(ob.vertex_groups):
                    g.remove([v.index])
                s = float((p - a) @ ax) / float(np.linalg.norm(b - a))
                k = max(0.0, min(1.0, (s - 0.75) / 0.25)) * 0.2
                _blend_add(ob, groups, v.index, {"forearm." + side: 1.0 - k, "hand." + side: k})


def leather_weights(ob, skin_ob, arm):
    """The belt and the baldric ride her body like the coat under them; the scabbard and its frog hang rigid from her
    hips."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"},
                         caps={"upperarm.R": 0.45, "upperarm.L": 0.45})
    groups = {}
    G, A, E, W, throat = cutlass_rest()
    for v in ob.data.vertices:
        p = np.array(v.co)
        if _seg_dist(p, throat - A * 0.03, cut_point(CUT_BLADE[1] + 0.04, 0.0)) < 0.07:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"root": 1.0})


def boots_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        p = np.array(v.co)
        side = "R" if p[0] < 0 else "L"
        an = J["ankle_" + side]
        if p[2] > an[2] + 0.04:
            w = {"shin." + side: 1.0}
        else:
            k = max(0.0, min(1.0, (an[1] - p[1]) / 0.12))
            w = {"shin." + side: 1.0 - k, "foot." + side: k}
        _blend_add(ob, groups, v.index, w)


def gold_weights(ob, skin_ob, arm):
    """The buttons ride the coat; the cuffs' buttons their forearms; the buckle the belt; the earring her head."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=COAT_BONES, caps=COAT_CAPS)
    groups = {}
    for v in ob.data.vertices:
        p = np.array(v.co)
        w = None
        if p[2] > 1.5:
            w = {"head": 1.0}
        else:
            for side in ("R", "L"):
                a, b, ax = cuff_frame(side)
                if _seg_dist(p, a, b) < CUFF_R[1] + 0.04 and abs(p[0]) > 0.4:
                    w = {"forearm." + side: 1.0}
        if w is not None:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, w)


def pistols_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"pistol_R" if v.co.x < 0 else "pistol_L": 1.0})


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Bandana": ("rigid", "head"), "Hat": ("rigid", "head"), "Feather": ("rigid", "head"),
        "Coat": ("custom", coat_weights),
        "Shirt": ("transfer", COAT_BONES, COAT_CAPS),
        "Sash": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.3, "thigh.L": 0.3}),
        "Leather": ("custom", leather_weights),
        "Breeches": ("transfer", {"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Boots": ("custom", boots_weights),
        "Gold": ("custom", gold_weights),
        "Pistols": ("custom", pistols_weights), "Cutlass": ("rigid", "cutlass"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Pistols", "Cutlass"):
        return 0.9
    if part == "Breeches":
        return 0.7
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Bandana", bandana_field(), 0.0022 if fine else 0.0032),
        ("Hat", hat_field(), 0.0022 if fine else 0.0032),
        ("Feather", feather_field(), 0.0016 if fine else 0.0024),
        ("Coat", coat_field(), 0.0028 if fine else 0.0038),
        ("Shirt", shirt_field(), 0.0022 if fine else 0.0032),
        ("Sash", sash_field(), 0.0024 if fine else 0.0034),
        ("Leather", leather_field(), 0.0022 if fine else 0.0032),
        ("Breeches", breeches_field(), 0.0028 if fine else 0.0038),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Gold", gold_field(), 0.0014 if fine else 0.002),
        ("Pistols", pistols_field(), 0.0014 if fine else 0.002),
        ("Cutlass", cutlass_field(), 0.0014 if fine else 0.002),
    ]
