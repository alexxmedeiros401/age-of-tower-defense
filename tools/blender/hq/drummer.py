"""The War Drummer (HQ tower, Gunpowder Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A big, broad-shouldered sergeant drummer in his forties, jolly and loud: a round ruddy face, full jowls, round apple
cheeks pushed up by a broad grin, a bulbous red nose, twinkling blue eyes narrowed by the smile, bushy brows lifted; thick
grey-streaked mutton-chop whiskers joined to his moustache (his chin shaved); powdered hair rolled over his ears and tied
back in a short queue wrapped in black ribbon. A black felt tricorne pushed back on his head, edged with gold lace, a
crimson cockade on its left side. A crimson coat with wide gold lapels and cuffs, brass buttons, gold-lace chevrons down
its sleeves, a gold standing collar, its skirts turned back before and behind to show their gold lining; a buff waistcoat
over his paunch; a white stock; a white cross-belt over his right shoulder carrying the drum on a brass hook at his left
hip; off-white breeches; black gaiters buttoned to the knee; black shoes with brass buckles.

The drum hangs at his left thigh, its head tilted up toward his right hand: a wooden shell painted crimson with the
regiment's gold device (a crowned sunburst), black hoops painted with gold dogteeth, white rope laced in a zigzag through
leather buffs, pale calfskin heads. A drumstick with an acorn tip in each fist, along the fist's thumb axis (each on its own
bone, stick.R and stick.L). The drum rides its own bone (drum, on the root, pivoting on its hook); the drumhead's centre
has a bone of its own (drumhead: the game's shockwave leaves it at the beat).

His body, hands and fists are the Spear Guard's (spear.py), with a paunch and his own head."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import spear as sp
from spear import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R,
                   eye_c, smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, torso_prims, traps, neck_prim,
                   deltoid, eyes_field, _forearm, TORSO, TORSO_Z, torso_bones)

RED_NOSE = 10
IRIS = ((0.1, 0.24, 0.46), (0.36, 0.58, 0.82))          # twinkling blue eyes (prep.paint_eyes: outer ring, inner ring)


# ======================================================================================= head
JAW = ((0.0, -0.06, 1.582), (0.157, 0.139, 0.133))
CHIN = ((0.0, -0.13, 1.5), (0.088, 0.072, 0.068))
DCHIN = ((0.0, -0.085, 1.462), (0.104, 0.072, 0.046))


def cheek(sx):
    return (sx * 0.1, -0.142, 1.628), 0.05


def jowl(sx):
    return (sx * 0.13, -0.052, 1.56), 0.056


def head(fd):
    """A round jolly face: full jowls, round apple cheeks pushed up by a broad grin, a bulbous nose, twinkling eyes narrowed
    by the smile (crow's feet), bushy brows lifted, a round shaved chin (a shadow of stubble) over a soft double chin."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E(*JAW), 0.07, SKIN)
    fd.add(E(*CHIN), 0.05, SKIN)
    fd.add(E(*DCHIN), 0.04, SKIN)
    for sx in (-1, 1):
        fd.add(S(*cheek(sx)), 0.05, SKIN)
        fd.add(S(*jowl(sx)), 0.05, SKIN)
        pts = [hp((sx * 0.152, -0.055, 1.744)), hp((sx * 0.116, -0.13, 1.756)), hp((sx * 0.06, -0.174, 1.758)), hp((0.0, -0.182, 1.755))]
        fd.add(Chain(pts, [hr(0.01), hr(0.017), hr(0.019), hr(0.018)], k=hr(0.02)), hr(0.03), SKIN)     # the brow ridge
    # bushy brows, lifted in the middle (a jolly look), grey-streaked
    tuft = lambda P: F(0.0022) * NOISE(P * F(150)) + F(0.001) * np.sin(P[:, 0] * F(380))
    for sx in (-1, 1):
        pts = [hp((sx * 0.026, -0.21, 1.782)), hp((sx * 0.066, -0.205, 1.795)), hp((sx * 0.11, -0.186, 1.794)),
               hp((sx * 0.15, -0.147, 1.774))]
        fd.add(Chain([p + v3((0, 0.005, 0)) for p in pts], [hr(0.012), hr(0.015), hr(0.013), hr(0.006)], k=hr(0.008),
                     disp=tuft, disp_amp=0.003), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.02), hr(0.023), hr(0.02), hr(0.011)], k=hr(0.01)), BROW)
    # eyes narrowed by the smile: the lower lids pushed up (rising to the outer corners), crow's feet
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.023))), (sx * 0.12, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0062)), Plane(ec + v3((0, 0, -hr(0.012))), (sx * -0.45, 0.12, 1.0)), hr(0.004))
        fd.add(lo, hr(0.006), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)),
                       Plane(ec + v3((0, 0, hr(0.02))), (sx * 0.12, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(3):                                                                # crow's feet
            a = hp((sx * (0.112 + 0.004 * k), -0.132 + 0.006 * k, 1.69 - 0.013 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.026, 0.012, 0.008 - 0.011 * k)), hr(0.0022), hr(0.0014)), hr(0.003))
        fd.add(Ellipsoid(hp((sx * 0.07, -0.158, 1.64)), v3((0.028, 0.012, 0.012)) * HS), hr(0.012), SKIN)   # the smile's lift
    # a big bulbous nose
    fd.add(RoundCone(hp((0, -0.188, 1.724)), hp((0, -0.238, 1.644)), hr(0.016), hr(0.026)), hr(0.017), SKIN)
    fd.add(S((0, -0.212, 1.69), 0.016), hr(0.012), SKIN)
    fd.add(S((0, -0.252, 1.614), 0.043), hr(0.016), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.041, -0.226, 1.598), 0.026), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.02, -0.246, 1.577)), v3((0.011, 0.013, 0.008)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    fd.paint(Sphere(hp((0.0, -0.256, 1.616)), hr(0.05)), RED_NOSE)
    # a broad open grin under the moustache: the corners drawn up, the upper teeth showing, a full lower lip
    slot = mouth_slot()
    fd.sub(Chain(slot, [hr(0.003), hr(0.0085), hr(0.011), hr(0.0085), hr(0.003)], k=hr(0.004)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0045), hr(0.011), hr(0.0135), hr(0.011), hr(0.0045)], k=hr(0.005)), MOUTH)
    lo_lip = [(-0.062, -0.16, 1.562), (-0.033, -0.187, 1.533), (0, -0.196, 1.523), (0.033, -0.187, 1.533), (0.062, -0.16, 1.562)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0078), hr(0.0088), hr(0.0078), hr(0.004)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.sub(S((sx * 0.08, -0.152, 1.584), 0.006), hr(0.006))                        # the smile's dimples
    fd.paint(Func(chin_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.178, 0.035, 1.66)), v3((0.026, 0.047, 0.06)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)


def mouth_slot():
    return [hp((-0.074, -0.154, 1.578)), hp((-0.044, -0.186, 1.55)), hp((0.0, -0.199, 1.538)), hp((0.044, -0.186, 1.55)),
            hp((0.074, -0.154, 1.578))]


def chin_mask(P):
    """His shaved chin (design coordinates): a shadow of stubble."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    return np.maximum(np.maximum(np.abs(x) - F(0.075), z - F(1.535)), np.maximum(F(1.43) - z, y + F(0.06)))


def paunch():
    return Ellipsoid((0.0, -0.04, 0.985), (0.212, 0.186, 0.182))


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(paunch(), 0.08, SKIN)
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
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def leg_prims(side):
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(hip, kn, 0.135, 0.088), 0.065),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.122, 0.115, 0.185), R=rot_from_axes(z_axis=kn - hip)), 0.048),
            (Sphere(kn + v3((0, -0.03, 0.0)), 0.068), 0.038),
            (RoundCone(kn, an, 0.084, 0.056), 0.038),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.095, 0.092, 0.14), R=rot_from_axes(z_axis=an - kn)), 0.043)]


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


def teeth_field():
    """His upper teeth, showing in the grin under the moustache."""
    fd = Field("Teeth")
    slot = mouth_slot()
    pts = [lerp(slot[1], slot[2], 0.15), slot[2], lerp(slot[3], slot[2], 0.15)]
    pts = [p + v3((0, 0.006, 0.0045)) for p in pts]
    fd.add(Chain(pts, [hr(0.0062), hr(0.0068), hr(0.0062)], k=hr(0.004)), 0.0)
    return fd


# ======================================================================================= whiskers
def face_hull():
    fd = Field("FaceHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E(*JAW), 0.07)
    fd.add(E(*CHIN), 0.05)
    fd.add(E(*DCHIN), 0.04)
    for sx in (-1, 1):
        c, r = cheek(sx)
        fd.add(Sphere(hp(c), hr(r)), 0.05)
        c, r = jowl(sx)
        fd.add(Sphere(hp(c), hr(r)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


CHOP_PTS = [(0.168, -0.03, 1.738), (0.172, -0.048, 1.664), (0.163, -0.074, 1.588), (0.138, -0.11, 1.54),
            (0.11, -0.142, 1.552), (0.09, -0.162, 1.578)]
CHOP_RAD = [0.022, 0.032, 0.047, 0.045, 0.034, 0.022]


def _chop_region(Q):
    """< 0 inside the mutton chops (design coordinates): a broad band from each temple down over the cheek to the jaw and
    forward along it to the corner of the mouth; the chin and the lips left clear."""
    out = None
    for sx in (-1, 1):
        pts = [v3((sx * x, y, z)) for x, y, z in CHOP_PTS]
        c = Chain(pts, CHOP_RAD, k=0.02)
        d = c.sdf(Q)
        out = d if out is None else np.minimum(out, d)
    lips = np.sqrt((Q[:, 0] / F(0.066)) ** 2 + ((Q[:, 1] + F(0.18)) / F(0.06)) ** 2 + ((Q[:, 2] - F(1.548)) / F(0.03)) ** 2) - F(1.0)
    return np.maximum(out, -lips * F(0.03))


def whiskers_field():
    """Thick grey-streaked mutton chops from his temples down his cheeks to the jaw, bushy at the jaw, swept forward to the
    corners of his mouth, joined to a thick moustache over his grin."""
    fd = Field("Whiskers")
    hull = face_hull()
    hairs = lambda P: F(0.0022) * NOISE(P * np.array([90, 90, 28], F)) + F(0.001) * NOISE(P * F(170))
    def chops(P):
        d = hull.eval(P, margin=0.06)
        m = _chop_region(hinv(P)) * F(HS)
        depth = np.clip(-m / F(0.026), 0, 1)
        outer = F(0.004) + F(0.022) * np.sqrt(depth)
        vol = np.maximum(d - outer, F(-0.006) - d)
        return np.maximum(vol, m)
    lo, hi = HEAD_C + v3((-0.32, -0.36, -0.42)), HEAD_C + v3((0.32, 0.12, 0.1))
    fd.add(Func(chops, lo, hi, disp=hairs, disp_amp=0.003), 0.0)
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):                                                       # the moustache, joining the chops
        pts = [hp((sx * 0.004, -0.238, 1.594)), hp((sx * 0.042, -0.228, 1.59)), hp((sx * 0.078, -0.2, 1.588)),
               hp((sx * 0.1, -0.166, 1.594))]
        fd.add(Lock(pts, [hr(0.019), hr(0.025), hr(0.022), hr(0.017)], [hr(0.012), hr(0.014), hr(0.013), hr(0.011)],
                    [norm(v3((sx * 0.3, -1, 0.15)))] * 4, k=hr(0.007), disp=strands, disp_amp=0.003), hr(0.008))
    return fd


# ======================================================================================= hair (powdered)
QUEUE_TOP = hp((0.0, 0.205, 1.628))            # the queue's tie at his nape
QUEUE_END = hp((0.0, 0.272, 1.5))


def hair_field():
    """Powdered hair: drawn back over his head under the hat (showing at the temples and the nape), rolled in a curl over
    each ear, gathered at his nape into the queue (its white tuft shows below the ribbon)."""
    fd = Field("Hair")
    strands = lambda P: F(0.003) * NOISE(P * np.array([60, 60, 18], F)) + F(0.0015) * NOISE(P * F(110))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        front = np.where(y < F(-0.04), F(1.77) + F(0.02) * smoothstep(0.06, 0.15, ax) - z, F(-1.0))     # the hairline
        ears = np.where((ax > F(0.13)) & (z < F(1.735)) & (y < F(0.1)) & (y > F(-0.12)), F(0.02), F(-1.0))
        nape = F(1.6) - z
        return np.maximum(np.maximum(front, ears), nape)
    fd.add(Inter(Shell(Ellipsoid(HEAD_C, HEAD_RAD), 0.01, 0.02, pad=0.06, disp=strands, disp_amp=0.004),
                 Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.008), 0.0)
    for sx in (-1, 1):                                                       # a roll over each ear
        pts = [hp((sx * 0.168, -0.07, 1.752)), hp((sx * 0.182, 0.0, 1.752)), hp((sx * 0.178, 0.07, 1.746)), hp((sx * 0.155, 0.13, 1.735))]
        fd.add(Chain(pts, [hr(0.022), hr(0.027), hr(0.026), hr(0.02)], k=hr(0.012), disp=strands, disp_amp=0.003), hr(0.012))
    fd.add(Ellipsoid(hp((0.0, 0.19, 1.66)), v3((0.07, 0.05, 0.06)) * HS, disp=strands, disp_amp=0.003), hr(0.03))   # gathered at the nape
    d = norm(QUEUE_END - QUEUE_TOP)
    fd.add(RoundCone(QUEUE_END - d * 0.02, QUEUE_END + d * 0.045, 0.024, 0.012, disp=strands, disp_amp=0.003), 0.01)  # the tuft
    return fd


# ======================================================================================= tricorne (black felt), the queue's ribbon
HAT_O = hp((0.0, 0.03, 1.79))                  # the hat's base (where the brim turns up) at its middle
HAT_R = euler(-0.12, 0.0, 0.0)                 # pushed back on his head (the front point lifts)
CROWN_RAD = v3((0.206, 0.22, 0.158))
R_MID, R_CORNER = 0.226, 0.362                 # the turned-up brim: the middles of its sides hug the crown, the corners stand out
R_SIDE = (R_CORNER * R_MID - R_CORNER ** 2 - R_MID ** 2) / (R_CORNER - 2 * R_MID)    # each side an arc through two corners
WALL_T = 0.017
LEAN = 0.24
H_MID, H_BACK, H_FRONT = 0.104, 0.088, 0.066   # the brim's height up the crown: mid-side, at the back corners, the front


def _dir(th):
    return v3((math.sin(th), -math.cos(th), 0.0))


ARC_C = [(R_SIDE - R_MID) * _dir(2 * math.pi * k / 3) for k in range(3)]      # (the side opposite corner k bulges from ARC_C[k])


def hat_local(P):
    return ((P - HAT_O.astype(F)) @ HAT_R.astype(F)).astype(F)


def hat_world(q):
    return HAT_O + HAT_R @ v3(q)


def _plan_in(q):
    """< 0 inside the hat's rounded triangle (its plan, hat coordinates), the distance to its edge."""
    d = None
    for c in ARC_C:
        e = np.sqrt((q[:, 0] - F(c[0])) ** 2 + (q[:, 1] - F(c[1])) ** 2) - F(R_SIDE)
        d = e if d is None else np.maximum(d, e)
    return d


def _wall_h(q):
    th = np.arctan2(q[:, 0], -q[:, 1])
    corner = ((F(1) + np.cos(F(3) * th)) / F(2)) ** 2
    hc = F(H_BACK) + F(H_FRONT - H_BACK) * ((F(1) + np.cos(th)) / F(2)) ** 4
    return F(H_MID) - (F(H_MID) - hc) * corner


def hat_dist(P):
    q = hat_local(P)
    h = q[:, 2]
    pin = _plan_in(q)
    wall = np.maximum(np.abs(pin - F(LEAN) * np.maximum(h, 0) + F(WALL_T * 0.5)) - F(WALL_T * 0.5), np.maximum(-h, h - _wall_h(q)))
    plate = np.maximum(pin + F(0.004), np.abs(h - F(0.008)) - F(0.008))
    cr = np.sqrt((q[:, 0] / F(CROWN_RAD[0])) ** 2 + (q[:, 1] / F(CROWN_RAD[1])) ** 2 + (np.maximum(h, 0) / F(CROWN_RAD[2])) ** 2)
    crown = np.maximum((cr - F(1)) * F(CROWN_RAD[2]), -h - F(0.002))
    return np.minimum(np.minimum(wall, plate), crown)


def cockade_frame():
    """The cockade on the brim's front-left side, near the front point: its centre, outward normal and the way up the wall."""
    th = math.radians(34)
    q0 = (R_SIDE - R_MID) * _dir(4 * math.pi / 3)               # (the front-left side bulges from the arc opposite corner 2)
    d = _dir(th)
    # the point on that arc in direction th (from the hat's middle), at the cockade's height
    lo, hi = 0.0, 0.5
    for _ in range(40):
        m = (lo + hi) / 2
        p = d * m
        if np.linalg.norm(p[:2] - q0[:2]) < R_SIDE:
            lo = m
        else:
            hi = m
    hgt = 0.056
    p = d * lo + v3((0, 0, hgt))
    p = p + norm(v3((p[0] - q0[0], p[1] - q0[1], 0))) * (LEAN * hgt)
    n_loc = norm(v3((p[0] - q0[0], p[1] - q0[1], 0)) + v3((0, 0, -LEAN * 0.9)))
    up_loc = norm(v3((0, 0, 1)) - n_loc * n_loc[2])
    return hat_world(p + n_loc * 0.005), HAT_R @ n_loc, HAT_R @ up_loc


def hat_field():
    """The tricorne: black felt (label 0) with its brim turned up against the crown in three sides that meet in points,
    the front one over his brow; gold lace along the brim's edge (5); a crimson cockade (6) on the front-left side with a
    gold button and loop (5). Also the black ribbon wrapping his queue, with a bow at his nape (label 0)."""
    fd = Field("Hat")
    felt = lambda P: F(0.0008) * NOISE(P * F(60))
    lo, hi = HAT_O - 0.5, HAT_O + 0.5
    fd.add(Func(hat_dist, lo, hi, disp=felt, disp_amp=0.001), 0.0)
    def lace(P):
        q = hat_local(P)
        h = q[:, 2]
        wall = np.abs(_plan_in(q) - F(LEAN) * np.maximum(h, 0) + F(WALL_T * 0.5)) - F(WALL_T * 0.5)
        return np.maximum(_wall_h(q) - F(0.017) - h, wall - F(0.004))
    fd.paint(Func(lace, lo, hi), 5)
    # the cockade: a pleated rosette, a gold button and a loop of lace up to the brim's edge
    c, n, up = cockade_frame()
    Rc = rot_from_axes(z_axis=n, y_axis=up)
    side = np.cross(up, n)
    def rosette(P):
        q = (P - c.astype(F)) @ Rc.astype(F)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        a = np.arctan2(q[:, 1], q[:, 0])
        pleat = F(0.0025) * np.cos(a * F(14)) * np.clip(r / F(0.03), 0, 1)
        dome = F(0.006) * (F(1) - np.clip(r / F(0.04), 0, 1) ** 2)
        return np.maximum(r - F(0.04) - F(0.002) * np.cos(a * F(14)), np.abs(q[:, 2] - dome - pleat) - F(0.006))
    fd.add(Func(rosette, c - 0.08, c + 0.08), 0.003, 6)
    fd.add(Sphere(c + n * 0.009, 0.011), 0.003, 5)
    top = c + up * 0.05 + n * 0.002
    fd.add(Chain([c + n * 0.008, lerp(c, top, 0.5) + n * 0.006, top], [0.0045, 0.0045, 0.0045], k=0.002), 0.002, 5)
    # the queue's ribbon: wrapped down the queue, a bow at its top
    d = norm(QUEUE_END - QUEUE_TOP)
    wrap = lambda P: F(0.002) * np.sin(((P - QUEUE_TOP.astype(F)) @ d.astype(F)) * F(140))
    fd.add(RoundCone(QUEUE_TOP, QUEUE_END - d * 0.01, 0.028, 0.021, disp=wrap, disp_amp=0.002), 0.004)
    bc = QUEUE_TOP + v3((0, 0.022, 0.006))
    for sx in (-1, 1):
        lc = bc + v3((sx * 0.04, 0.008, 0.008))
        fd.add(Torus(lc, 0.026, 0.009, R=rot_from_axes(z_axis=v3((0, 1, 0.25)))), 0.006)
        fd.add(Lock([bc, bc + v3((sx * 0.025, 0.018, -0.05)), bc + v3((sx * 0.035, 0.026, -0.1))], [0.016, 0.015, 0.013],
                    [0.004, 0.004, 0.003], [v3((0, 1, 0.1))] * 3, k=0.004), 0.004)
    fd.add(Sphere(bc, 0.017), 0.006)
    return fd


# ======================================================================================= the coat (crimson wool)
WAIST_Z = 0.96
HEM_Z = 0.5
COAT_OFF, COAT_T = 0.04, 0.014
SLEEVE_OFF = 0.026
FLAP = 0.012                                   # the lapels, cuffs and turnbacks: a layer on top of the coat


def coat_base():
    b = Field("CoatBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(paunch(), 0.08)
    b.add(traps(), 0.06)
    b.add(RoundCone((0.0, 0.04, 0.95), (0.0, 0.06, 0.48), 0.24, 0.29), 0.08)
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


def _ang(P):
    """The angle round his body from straight ahead (0) to straight behind (pi), and the distance from its axis."""
    dx, dy = P[:, 0], P[:, 1] - F(0.04)
    return np.arctan2(np.abs(dx), -dy), np.sqrt(dx * dx + dy * dy)


def _below(z):
    return smoothstep(WAIST_Z, HEM_Z, z)


def _cutaway(z):
    return np.sqrt(np.clip((F(WAIST_Z) - z) / F(WAIST_Z - HEM_Z), 0, 1))


def front_a(z):
    """The coat's front edge (an angle round him): straight down his chest, cut away steeply below the waist."""
    return F(0.29) + F(0.85) * _cutaway(z)


def turn_a(z):
    """The turnbacks' edge: the gold lining shows between the front edge and this."""
    return front_a(z) + F(0.4) * _cutaway(z) ** 1.6


def _vent(z):
    v = smoothstep(0.84, HEM_Z, z)
    return F(0.03) + F(0.28) * v, F(0.42) * v                  # the back vent's half opening, the back turnbacks' width


def hem_z(P):
    a, r = _ang(P)
    return F(HEM_Z) + F(0.012) * np.cos(a) + F(0.006) * NOISE(P * F(8))


def _arm_s(P, side, seg):
    """Distance along an arm segment (0: upper arm, 1: forearm), the squared distance off its axis, and the angle round it
    from its outer side (toward the front: +)."""
    sx = -1 if side == "R" else 1
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    a, b = (sh, el) if seg == 0 else (el, wr)
    ax = norm(b - a)
    L = float(np.linalg.norm(b - a))
    q = P - a.astype(F)
    s = q @ ax.astype(F)
    perp = q - s[:, None] * ax.astype(F)[None, :]
    out = norm(v3((sx, 0, 0)) - ax * (sx * ax[0]))
    fwd = norm(v3((0, -1, 0)) - ax * (-ax[1]))
    fwd = norm(fwd - out * (fwd @ out))
    ang = np.arctan2(perp @ fwd.astype(F), perp @ out.astype(F))
    return s, (perp ** 2).sum(1), ang, L


def _sleeve_end(P):
    """> 0 past the sleeves' ends at the wrists (only round each forearm)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2, ang, L = _arm_s(P, side, 1)
        lateral = P[:, 0] * F(sx) - F(0.42)
        out = np.maximum(out, np.where((lateral > 0) & (d2 < F(0.16 ** 2)), s - F(L - 0.012), F(-1.0)))
    return out


def _cuff(P):
    """< 0 on the cuffs: the last 13 cm of each sleeve."""
    out = F(1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2, ang, L = _arm_s(P, side, 1)
        c = np.abs(s - F(L - 0.078)) - F(0.066)
        out = np.minimum(out, np.where((P[:, 0] * F(sx) > F(0.4)) & (d2 < F(0.17 ** 2)), c, F(1.0)))
    return out


def _neck_open(P):
    """> 0 inside the coat's opening round his neck (near the neck's axis only: cut level, it would open the coat on top
    of his shoulders)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    yn = F(0.07) - F(0.2) * np.clip(z - F(1.36), 0, None)
    rho = np.sqrt(x * x + (F(0.9) * (y - yn)) ** 2)
    return np.minimum(F(0.138) - rho, z - F(1.38))


def coat_cut(P):
    """< 0 where the coat is: open down the front (the lapels' inner edges), cut away below the waist, a vent behind,
    round the neck, at the wrists, at the hem (above his knees)."""
    a, r = _ang(P)
    z = P[:, 2]
    front = (front_a(z) - a) * np.maximum(r, F(0.1))
    vh, vw = _vent(z)
    vent = np.where(z < F(0.86), (a - (F(math.pi) - vh)) * np.maximum(r, F(0.1)), F(-1.0))
    return np.maximum(np.maximum(np.maximum(front, vent), np.maximum(_neck_open(P), _sleeve_end(P))), hem_z(P) - z)


def coat_shell(P, base, extra=0.0, t=COAT_T):
    d = base.eval(P, margin=0.1)
    x = np.abs(P[:, 0])
    arm = smoothstep(0.33, 0.44, x)
    z = P[:, 2]
    a, r = _ang(P)
    below = _below(z)
    folds = (F(0.006) * np.sin(a * F(11) + F(0.7) * NOISE(P * F(2))) * below + F(0.0016) * NOISE(P * F(14))) * (F(1) - arm)
    off = F(COAT_OFF) - F(COAT_OFF - SLEEVE_OFF) * arm + folds + F(0.012) * below + F(extra)
    return np.abs(d - off) - F(t * 0.5)


def lapel_region(P):
    """< 0 on the lapels: a band beside the front edge from the collar down to the waist, a little wider at the top."""
    a, r = _ang(P)
    z = P[:, 2]
    w = F(0.25) + F(0.07) * smoothstep(1.0, 1.42, z)
    band = np.maximum(front_a(z) - a, a - (front_a(z) + w)) * np.maximum(r, F(0.1))
    return np.maximum(np.maximum(band, F(WAIST_Z + 0.015) - z), P[:, 1] + F(0.02))


def turnback_region(P):
    """< 0 on the turnbacks: triangles of gold lining beside the skirts' front edges and either side of the back vent."""
    a, r = _ang(P)
    z = P[:, 2]
    rr = np.maximum(r, F(0.1))
    fr = np.maximum(front_a(z) - a, a - turn_a(z)) * rr
    vh, vw = _vent(z)
    bk = np.maximum((F(math.pi) - vh - vw) - a, a - (F(math.pi) - vh)) * rr
    tri = np.minimum(fr, np.where(z < F(0.84), bk, F(1.0)))
    return np.maximum(np.maximum(tri, z - F(WAIST_Z - 0.01)), hem_z(P) - z)


def chevrons(P):
    """< 0 on the lace chevrons down his sleeves: three on each upper arm, two above each cuff, pointing down, on the
    outer side."""
    out = F(1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        lat = P[:, 0] * F(sx) > F(0.3)
        for seg, ss in ((0, (0.13, 0.19, 0.25)), (1, (0.12, 0.17))):
            s, d2, ang, L = _arm_s(P, side, seg)
            rad = np.sqrt(d2)
            for s0 in ss:
                line = F(s0) - np.abs(ang) * F(0.05)
                c = np.maximum(np.abs(s - line) - F(0.0085), np.abs(ang) - F(1.15))
                out = np.minimum(out, np.where(lat & (rad < F(0.16)), c, F(1.0)))
    return out


def collar_region(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    return np.maximum(np.abs(z - F(1.448)) - F(0.042), np.where(y < F(-0.02), F(0.07) - np.abs(x), F(-1.0)))


def coat_field():
    """Crimson wool (label 0): open down the front over the waistcoat, its skirts to above his knees turned back before
    and behind; wide gold lapels on his chest, gold cuffs, a gold standing collar and gold turnbacks (5, a layer raised a
    little over the coat); bright gold lace (6): chevrons down the sleeves, the lapels' edging."""
    fd = Field("Coat")
    base = coat_base()
    lo, hi = (-0.86, -0.42, 0.42), (0.86, 0.44, 1.57)
    def coat_all(P):
        d = base.eval(P, margin=0.1)
        x = np.abs(P[:, 0])
        arm = smoothstep(0.33, 0.44, x)
        z = P[:, 2]
        a, r = _ang(P)
        below = _below(z)
        folds = (F(0.006) * np.sin(a * F(11) + F(0.7) * NOISE(P * F(2))) * below + F(0.0016) * NOISE(P * F(14))) * (F(1) - arm)
        off = F(COAT_OFF) - F(COAT_OFF - SLEEVE_OFF) * arm + folds + F(0.012) * below
        main = np.abs(d - off) - F(COAT_T * 0.5)
        flap = np.abs(d - off - F(COAT_T * 0.5 + FLAP * 0.5 - 0.002)) - F(FLAP * 0.5)
        reg = np.minimum(np.minimum(lapel_region(P), turnback_region(P)), _cuff(P))
        return smax(smin(main, np.maximum(flap, reg), 0.003), coat_cut(P), 0.004)
    fd.add(Func(coat_all, lo, hi), 0.0)
    fd.paint(Func(lambda P: np.minimum(np.minimum(lapel_region(P), turnback_region(P)), _cuff(P)), lo, hi), 5)
    fd.paint(Func(chevrons, lo, hi), 6)
    def lapel_lace(P):
        reg = lapel_region(P)
        return np.maximum(np.abs(reg + F(0.007)) - F(0.0055), -reg - F(0.02))
    fd.paint(Func(lapel_lace, lo, hi), 6)
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    fd.add(Inter(Shell(nk, 0.03, 0.016, pad=0.1), Func(collar_region, (-0.4, -0.4, 1.3), (0.4, 0.4, 1.6)), 0.004), 0.004, 5)
    return fd


# ======================================================================================= waistcoat (buff), stock, breeches
def waistcoat_base():
    b = Field("WaistcoatBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(paunch(), 0.08)
    b.add(traps(), 0.06)
    b.add(RoundCone((0.0, 0.04, 0.95), (0.0, 0.05, 0.72), 0.235, 0.255), 0.08)
    return b


def waistcoat_field():
    """Buff wool over his paunch, buttoned down the front, from his throat to the tops of his thighs (its fronts curving
    away below the last button); under the coat it ends at his sides."""
    fd = Field("Waistcoat")
    base = waistcoat_base()
    def keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        yn = F(0.07) - F(0.2) * np.clip(z - F(1.36), 0, None)
        rho = np.sqrt(x * x + (F(0.9) * (y - yn)) ** 2)
        neck = np.minimum(F(0.118) - rho, z - F(1.36))
        hem = F(0.74) + F(0.07) * np.exp(-(x / F(0.07)) ** 2) * (y < F(0.0))
        return np.maximum(np.maximum(neck, hem - z), np.maximum(y - F(0.14), np.abs(x) - F(0.31)))
    lo, hi = (-0.6, -0.6, 0.6), (0.6, 0.4, 1.6)
    fd.add(Inter(Shell(base, 0.022, 0.012, pad=0.1, disp=lambda P: F(0.0012) * NOISE(P * F(20)), disp_amp=0.002),
                 Func(keep, lo, hi), 0.004), 0.0)
    return fd


def legs_base():
    b = Field("Legs")
    tp = torso_prims()
    b.add(tp[5][0], 0.0)
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            b.add(p, k)
    return b


def linen_field():
    """Off-white linen: his breeches from the waist to the gaiters' tops (wrinkled at the knees) and the stock round his
    neck."""
    fd = Field("Linen")
    lb = legs_base()
    wr = lambda P: F(0.0014) * NOISE(P * np.array([30, 30, 60], F))
    fd.add(Inter(Shell(lb, 0.008, 0.01, pad=0.08, disp=wr, disp_amp=0.002),
                 Func(lambda P: np.maximum(F(0.4) - P[:, 2], P[:, 2] - F(0.96)), (-0.6, -0.6, 0.3), (0.6, 0.6, 1.1)), 0.004), 0.0)
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    fd.add(Inter(Shell(nk, 0.012, 0.014, pad=0.08), Func(lambda P: np.abs(P[:, 2] - F(1.43)) - F(0.05), (-0.3, -0.3, 1.3), (0.3, 0.3, 1.56)),
                 0.004), 0.0)
    return fd


# ======================================================================================= gaiters, shoes
def shin_hull(side):
    an, kn = J["ankle_" + side], J["knee_" + side]
    ft = Field("ShinHull")
    foot(ft, side)
    ft.add(RoundCone(kn, an, 0.084, 0.056), 0.03)
    ft.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.095, 0.092, 0.14), R=rot_from_axes(z_axis=an - kn)), 0.043)
    ft.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.068), 0.038)
    return ft


GAITER_TOP = 0.47


def gaiter_button_pts(side):
    """Buttons up the outer side of each gaiter, from the ankle to the knee."""
    sx = -1 if side == "R" else 1
    hull = shin_hull(side)
    an = J["ankle_" + side]
    out = []
    for k in range(7):
        z = 0.15 + k * (GAITER_TOP - 0.2) / 6
        o = v3((an[0] + sx * 0.4, an[1] + 0.02 - 0.06 * (z - 0.15), z))
        h, ok = ray_hit(Func(lambda P: hull.eval(P, margin=0.06) - F(0.03), an - 0.5, an + 0.6), [o], [v3((-sx, 0, 0))], tmax=0.5)
        if ok[0]:
            out.append(h[0])
    return out


def gaiters_field():
    """Black canvas gaiters (label 0) from his shoes to the knee, over the shoes' insteps, buttoned up the outer side
    (pewter buttons, 5), a black garter strap round the top (6)."""
    fd = Field("Gaiters")
    crease = lambda P: F(0.0015) * NOISE(P * F(26)) + F(0.0012) * np.sin(P[:, 2] * F(90))
    for side in ("R", "L"):
        an = J["ankle_" + side]
        sx = -1 if side == "R" else 1
        hull = shin_hull(side)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        def keep(P, an=an, fwd=fwd):
            ahead = (P - an.astype(F)) @ fwd.astype(F)
            bottom = F(0.085) + F(0.06) * np.clip((ahead - F(0.02)) / F(0.08), 0, 1)     # over the instep, clear of the toes
            return np.maximum(P[:, 2] - F(GAITER_TOP), bottom - P[:, 2])
        fd.add(Inter(Shell(hull, 0.016, 0.012, pad=0.06, disp=crease, disp_amp=0.003), Func(keep, an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.6))),
                     0.004), 0.0)
        fd.add(Inter(Shell(hull, 0.026, 0.012, pad=0.06), Func(lambda P: np.abs(P[:, 2] - F(GAITER_TOP - 0.022)) - F(0.016),
                                                             an + v3((-0.3, -0.3, 0.1)), an + v3((0.3, 0.3, 0.6))), 0.003), 0.004, 6)
        for p in gaiter_button_pts(side):
            fd.add(Ellipsoid(p, (0.011, 0.011, 0.011)), 0.003, 5)
    return fd


def shoes_field():
    """Black leather shoes (label 0) with thick soles, square toes and big brass buckles (6) on their insteps."""
    fd = Field("Shoes")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        ft = Field("FootHull")
        foot(ft, side)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(Inter(Shell(ft, 0.0, 0.022, pad=0.06), Func(lambda P: P[:, 2] - F(0.13), an - 0.35, an + 0.35), 0.006), 0.0)
        fd.add(RoundBox(an + fwd * 0.078 + v3((0, 0, -0.1)), (0.07, 0.158, 0.013), 0.01, R=Rz), 0.008)
        bk = an + fwd * 0.118 + v3((0, 0, -0.03))
        h, ok = ray_hit(Func(lambda P: ft.eval(P, margin=0.06) - F(0.016), an - 0.4, an + 0.4), [bk + v3((0, 0, 0.3))], [v3((0, 0, -1))], tmax=0.4)
        bc = h[0] if ok[0] else bk
        nrm = norm(v3((0, 0, 1)) + fwd * 0.6)
        Rb = rot_from_axes(z_axis=nrm, y_axis=fwd)
        fd.add(RoundBox(bc, (0.042, 0.03, 0.006), 0.004, R=Rb), 0.003, 6)
        fd.sub(RoundBox(bc + nrm * 0.006, (0.026, 0.016, 0.006), 0.003, R=Rb), 0.002)
    return fd


# ======================================================================================= the drum
DRUM_R = 0.2                   # the shell's radius
DRUM_D = 0.33                  # the shell's length (head to head)
HOOP_H, HOOP_T, HOOP_UP = 0.048, 0.018, 0.012
N_V = 8                        # the rope's V's round the shell
DRUM_HEAD = v3((0.22, -0.42, 0.87))                          # the batter head's centre (rest pose)
DRUM_AX = norm(v3((-0.5, 0.12, 0.86)))                      # the drum's axis, up out of the batter head (tilted to his right)
DRUM_C = DRUM_HEAD - DRUM_AX * (DRUM_D / 2 + 0.002)
DRUM_U = norm(v3((0.7, -0.7, 0.0)) - DRUM_AX * (v3((0.7, -0.7, 0.0)) @ DRUM_AX))   # the device faces out to his front-left


def drum_frame(c=None, a=None, u=None):
    c = DRUM_C if c is None else v3(c)
    a = DRUM_AX if a is None else norm(a)
    u = DRUM_U if u is None else norm(v3(u) - norm(a) * (v3(u) @ norm(a)))
    v = np.cross(a, u)
    return c, a, u, v, np.stack([u, v, a], axis=1)


def _rr(qx, qy, rr):
    q = np.stack([qx, qy], 1) + F(rr)
    return np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - F(rr)


def sunburst_2d(u, v):
    """The regiment's device, < 0 inside (shell coordinates, metres): a sun of sixteen rays, long and short in turn, under
    a crown."""
    r = np.sqrt(u * u + v * v)
    a = np.arctan2(u, v)
    disc = r - F(0.038)
    m = np.mod(a + F(math.pi / 16), F(math.pi / 8)) - F(math.pi / 16)
    longr = np.mod(np.floor((a + F(math.pi / 16)) / F(math.pi / 8)), F(2)) < F(0.5)
    tip = np.where(longr, F(0.096), F(0.074))
    k = np.clip((r - F(0.03)) / (tip - F(0.03)), 0, 1)
    ray = np.maximum(np.abs(m) * r - F(0.011) * (F(1) - k), np.maximum(F(0.03) - r, r - tip))
    sun = np.minimum(disc, ray)
    ring = np.abs(r - F(0.03)) - F(0.0035)
    sun = np.maximum(sun, -ring)                               # a fine ring of shell colour round the sun's disc
    cv = v - F(0.1)
    band = np.maximum(np.abs(u) - F(0.048), np.abs(cv) - F(0.008))
    crown = band
    for cx, top in ((-0.034, 0.02), (0.0, 0.026), (0.034, 0.02)):
        kk = np.clip(cv / F(top), 0, 1)
        spike = np.maximum(np.abs(u - F(cx)) - F(0.012) * (F(1) - kk), np.maximum(-cv, cv - F(top)))
        ball = np.sqrt((u - F(cx)) ** 2 + (cv - F(top + 0.004)) ** 2) - F(0.0065)
        crown = np.minimum(crown, np.minimum(spike, ball))
    return np.minimum(sun, crown)


def drum_into(fd, c=None, a=None, u=None, nv=N_V, device=True, worn=True, hook=None, s=1.0):
    """A side drum into field fd: the shell (painted, label 0) with the device (5) on its u side, calfskin heads (10),
    black hoops (6) with gold dogteeth (7), the rope's zigzag (8) through leather buffs (9); the batter head (at +a) worn
    grey where the sticks strike (13); a brass ring on the top hoop at `hook` (11). s scales it."""
    c, a, u, v, Rm = drum_frame(c, a, u)
    def loc(P):
        return ((P - c.astype(F)) @ Rm.astype(F)).astype(F)
    R0, D0, HH, HT, HU = DRUM_R * s, DRUM_D * s, HOOP_H * s, HOOP_T * s, HOOP_UP * s
    zt = D0 / 2
    grain = lambda P: F(0.0006) * NOISE(P * F(60))
    fd.add(Cylinder(c, R0, D0, rr=0.006, R=Rm, disp=grain, disp_amp=0.001), 0.0, 0)
    if device:
        def dev(P):
            q = loc(P)
            r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
            ang = np.arctan2(q[:, 1], q[:, 0])
            return np.maximum(sunburst_2d(ang * F(R0 / s), (q[:, 2] + F(0.012 * s)) / F(s)) * F(s), np.abs(r - F(R0)) - F(0.006))
        fd.paint(Func(dev, c - 0.3, c + 0.3), 5)
    for e in (-1, 1):
        fd.add(Cylinder(c + a * (e * (zt + 0.001)), R0 - 0.004, 0.008, rr=0.003, R=Rm), 0.002, 10)
    def hoop_d(P, e):
        q = loc(P)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        zc = F(e * (zt + HU - HH / 2))
        return _rr(np.abs(r - F(R0 + HT / 2 - 0.004)) - F(HT / 2 + 0.004), np.abs(q[:, 2] - zc) - F(HH / 2), 0.004)
    for e in (-1, 1):
        fd.add(Func(lambda P, e=e: hoop_d(P, e), c - 0.35, c + 0.35), 0.002, 6)
        def teeth(P, e=e):
            q = loc(P)
            ang = np.arctan2(q[:, 1], q[:, 0])
            t = np.mod(ang * F(22 / (2 * math.pi)), F(1.0))
            tri = np.abs(F(2) * t - F(1))
            hz = (q[:, 2] - F(e * (zt + HU - HH / 2))) * F(e) / F(HH) + F(0.5)    # 0 at the hoop's inner edge
            return np.maximum(hoop_d(P, e) - F(0.003), (hz - (F(0.15) + F(0.7) * tri)) * F(0.04))
        fd.paint(Func(teeth, c - 0.35, c + 0.35), 7)
    # the rope: a zigzag round the shell between the hoops, through the buffs
    rr = R0 + 0.0075 * s
    z1 = zt + HU - HH - 0.002
    z0 = -z1
    pts = []
    step = 2 * math.pi / nv
    for k in range(nv):
        for j in range(4):
            t = j / 4.0
            ang = k * step + step * 0.5 * t
            z = z1 + (z0 - z1) * t
            pts.append(c + u * (math.cos(ang) * rr) + v * (math.sin(ang) * rr) + a * z)
        for j in range(4):
            t = j / 4.0
            ang = k * step + step * 0.5 + step * 0.5 * t
            z = z0 + (z1 - z0) * t
            pts.append(c + u * (math.cos(ang) * rr) + v * (math.sin(ang) * rr) + a * z)
    pts.append(pts[0])
    fd.add(Chain(pts, [0.0062 * s] * len(pts), k=0.002), 0.002, 8)
    for k in range(nv):
        ang = k * step + step * 0.5
        d = u * math.cos(ang) + v * math.sin(ang)
        t = np.cross(a, d)
        bc = c + d * (R0 + 0.013 * s) + a * (z0 + 0.075 * s)
        fd.add(RoundBox(bc, v3((0.021, 0.008, 0.03)) * s, 0.005, R=np.stack([t, d, a], axis=1)), 0.003, 9)
    if worn:
        fd.paint(Func(lambda P: np.maximum(np.sqrt(loc(P)[:, 0] ** 2 + loc(P)[:, 1] ** 2) - F(0.075 * s), np.abs(loc(P)[:, 2] - F(zt + 0.005)) - F(0.008)),
                      c - 0.3, c + 0.3), 13)
    if hook is not None:
        hd = norm(v3(hook) - c - a * (a @ (v3(hook) - c)))
        hp_ = c + a * (zt + HU - HH * 0.45) + hd * (R0 + HT + 0.008)
        fd.add(Torus(hp_, 0.017, 0.0048, R=rot_from_axes(z_axis=np.cross(a, hd), y_axis=a)), 0.003, 11)
    return c, a, u, v


def hook_point():
    """Where the drum hangs from its belt: the brass ring on the top hoop, toward his left hip."""
    c, a, u, v, Rm = drum_frame()
    want = v3((1.0, 1.2, 0.0))
    hd = norm(want - a * (a @ want))
    return c + a * (DRUM_D / 2 + HOOP_UP - HOOP_H * 0.45) + hd * (DRUM_R + HOOP_T + 0.008), hd


def drum_field():
    fd = Field("Drum")
    hk, hd = hook_point()
    drum_into(fd, hook=hk)
    return fd


# ======================================================================================= the drumsticks
STICK_BACK = 0.085             # fist centre -> the butt
STICK_TIP = 0.312              # fist centre -> the acorn tip's centre


def stick_frame(side):
    wr, f, n, t = hand_frame(side)
    return fist_center(side), norm(t)


def sticks_field():
    """Two drumsticks of light wood (siege label 0, the grain along them), tapering from a rounded butt to an acorn tip."""
    fd = Field("Sticks")
    grain = lambda P: F(0.0006) * NOISE(P * F(80))
    for side in ("R", "L"):
        G, T = stick_frame(side)
        fd.add(RoundCone(G - T * STICK_BACK, G + T * (STICK_TIP - 0.03), 0.0135, 0.0088, disp=grain, disp_amp=0.001), 0.0)
        fd.add(Ellipsoid(G + T * STICK_TIP, (0.0165, 0.0165, 0.024), R=rot_from_axes(z_axis=T)), 0.006)
        fd.add(Sphere(G - T * STICK_BACK, 0.0145), 0.004)
    return fd


# ======================================================================================= the cross-belt, brass
def torso_hull():
    """The coat's hull without the arms (the belt lies on it)."""
    b = Field("TorsoHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(paunch(), 0.08)
    b.add(traps(), 0.06)
    b.add(RoundCone((0.0, 0.04, 0.95), (0.0, 0.06, 0.48), 0.24, 0.29), 0.08)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.055)
    return b


BELT_W = 0.062
BELT_OFF = COAT_OFF + 0.021            # the belt's middle over the coat's hull (on the lapels; it bridges the opening)


def belt_path():
    """The drum belt: from the hook at his left hip up across his chest (over both lapels, bridging the opening between
    them) to the top of his right shoulder, over it and down his back to his left hip and round to the hook."""
    base = torso_hull()
    hull = Func(lambda P: base.eval(P, margin=0.14) - F(BELT_OFF), (-1, -1, 0.5), (1, 1, 1.8))
    hk, hd = hook_point()
    pts = [hk + v3((0.0, 0.0, 0.035))]
    for x, z in ((0.235, 0.975), (0.15, 1.05), (0.085, 1.11), (-0.09, 1.27), (-0.15, 1.33), (-0.2, 1.4)):
        h, ok = ray_hit(hull, [v3((x, -0.8, z))], [v3((0, 1, 0))], tmax=1.0)
        pts.append(h[0] if ok[0] else v3((x, -0.25, z)))
    for x, y in ((-0.235, -0.04), (-0.24, 0.06), (-0.235, 0.16)):
        h, ok = ray_hit(hull, [v3((x, y, 1.9))], [v3((0, 0, -1))], tmax=1.0)
        pts.append(h[0] if ok[0] else v3((x, y, 1.5)))
    for x, z in ((-0.2, 1.38), (-0.12, 1.29), (-0.03, 1.2), (0.06, 1.11), (0.15, 1.02), (0.23, 0.95)):
        h, ok = ray_hit(hull, [v3((x, 0.8, z))], [v3((0, -1, 0))], tmax=1.0)
        pts.append(h[0] if ok[0] else v3((x, 0.3, z)))
    for ang in (1.95, 1.6, 1.25):                              # round his left hip toward the front, down to the hook
        d = v3((math.sin(ang), -math.cos(ang), 0.0))
        o = v3((0.0, 0.04, 0.935)) + d * 0.9
        h, ok = ray_hit(hull, [o], [-d], tmax=1.0)
        pts.append(h[0] if ok[0] else v3((0.32, 0.1, 0.93)))
    pts.append(hk + v3((0.0, 0.0, 0.035)))
    return pts


def belt_field():
    """The white cross-belt (label 0), over his right shoulder."""
    fd = Field("Belt")
    base = torso_hull()
    pts = belt_path()
    nrm = []
    for p in pts:
        e = 0.004
        P = np.array([p + v3(d) * e for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))], F)
        dd = base.eval(P, margin=0.2)
        nrm.append(norm(v3((dd[0] - dd[1], dd[2] - dd[3], dd[4] - dd[5]))))
    fd.add(Lock(pts, [BELT_W * 0.5] * len(pts), [0.0055] * len(pts), nrm, k=0.006), 0.0)
    return fd


def _surface_pt(fn, o, d, tmax=1.0):
    h, ok = ray_hit(fn, [o], [d], tmax=tmax)
    return h[0] if ok[0] else None


def button_spots():
    """Brass buttons: on the lapels' outer edges, the cuffs, down the waistcoat, at the turnbacks' corners. (point, normal)"""
    base = coat_base()
    out = []
    lapel = Func(lambda P: base.eval(P, margin=0.14) - F(COAT_OFF + COAT_T * 0.5 + FLAP), (-1, -1, 0.5), (1, 1, 1.8))
    for z in (1.37, 1.27, 1.17, 1.07, 0.995):
        for sx in (-1, 1):
            zz = np.array([[0, 0, z]], F)
            a = float(front_a(zz[:, 2])[0]) + 0.26
            d = v3((sx * math.sin(a), -math.cos(a), 0.0))
            o = v3((0, 0.04, z)) + d * 0.8
            p = _surface_pt(lapel, o, -d)
            if p is not None:
                out.append((p, d))
    wb = waistcoat_base()
    wc = Func(lambda P: wb.eval(P, margin=0.14) - F(0.028), (-1, -1, 0.5), (1, 1, 1.8))
    for z in (1.33, 1.24, 1.15, 1.06, 0.97, 0.88, 0.8):
        p = _surface_pt(wc, v3((0, -0.8, z)), v3((0, 1, 0)))
        if p is not None:
            out.append((p, v3((0, -1, 0))))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        L = float(np.linalg.norm(wr - el))
        cuff = Func(lambda P: base.eval(P, margin=0.14) - F(SLEEVE_OFF + COAT_T * 0.5 + FLAP), (-1, -1, 0.5), (1, 1, 1.8))
        for s in (L - 0.12, L - 0.08, L - 0.04):
            c = el + ax * s
            back = norm(v3((sx * 0.5, 1.0, 0.0)) - ax * (ax @ v3((sx * 0.5, 1.0, 0.0))))
            p = _surface_pt(cuff, c + back * 0.4, -back, 0.5)
            if p is not None:
                out.append((p, back))
    return out


def brass_field():
    """Brass (label 0): the coat's and waistcoat's buttons, the belt plate on his breast."""
    fd = Field("Brass")
    for p, n in button_spots():
        fd.add(Ellipsoid(p + n * 0.003, (0.0125, 0.0125, 0.0065), R=rot_from_axes(z_axis=n)), 0.0)
    pts = belt_path()
    i = 4
    c = pts[i]
    t = norm(pts[i + 1] - pts[i - 1])
    n = norm(np.cross(t, v3((1, 0, 0))) if abs(t[0]) < 0.9 else v3((0, -1, 0)))
    if n[1] > 0:
        n = -n
    fd.add(Ellipsoid(c + n * 0.008, (0.034, 0.044, 0.008), R=rot_from_axes(z_axis=n, y_axis=t)), 0.0)
    fd.add(Ellipsoid(c + n * 0.014, (0.02, 0.026, 0.005), R=rot_from_axes(z_axis=n, y_axis=t)), 0.004)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0.0, -0.256, 1.616)), 0.06, 0.8)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.1, -0.15, 1.63)), 0.065, 0.75), (hp((sx * 0.13, -0.08, 1.58)), 0.05, 0.3),
                (hp((sx * 0.178, 0.035, 1.66)), 0.05, 0.55)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.043, 0.0145, -0.0145, -0.043):
            pts.append((wr + f * 0.138 + t * o - n * 0.012, 0.03, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "war_drummer"
ROOT_NAME = "WarDrummerHQ"
TEX_PREFIX = "drum"
MAT_NAME = "DrummerMat"
MESH_NAME = "Drummer"
BASE_MODULE = "drummer_base"
ANIM_MODULE = "anim_drummer"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Whiskers", "Hat", "Coat", "Waistcoat", "Linen", "Gaiters", "Shoes", "Belt", "Brass",
         "Drum", "Sticks"]
REGION_PARTS = ("Skin", "Hat", "Coat", "Gaiters", "Shoes", "Drum")
CRIMSON = (0.55, 0.08, 0.08)
GOLD = (0.85, 0.62, 0.2)
LACE = (0.97, 0.8, 0.36)
BUFF = (0.8, 0.66, 0.42)
LINEN = (0.92, 0.89, 0.8)
BLACK = (0.075, 0.07, 0.075)
POWDER = {"name": "HQ_DrummerHair", "base": (0.84, 0.83, 0.81), "hi": (0.98, 0.97, 0.95), "low": (0.56, 0.55, 0.54),
          "streak": (0.74, 0.73, 0.71), "tint": (0.9, 0.88, 0.85)}
WHISKERS = {"name": "HQ_DrummerWhiskers", "base": (0.42, 0.36, 0.31), "hi": (0.8, 0.78, 0.74), "low": (0.2, 0.16, 0.13),
            "streak": (0.7, 0.68, 0.65), "tint": (0.5, 0.44, 0.38)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_DrummerSkin", "base": (0.88, 0.62, 0.5), "ruddy": (0.9, 0.42, 0.36), "lips": (0.7, 0.36, 0.34),
                      "brow": ((0.36, 0.3, 0.26), (0.74, 0.72, 0.68)),
                      "extra": ((LASH, (0.2, 0.15, 0.12), 0.5), (RED_NOSE, (0.86, 0.38, 0.32), 0.42),
                                (STUBBLE, (0.6, 0.5, 0.46), 0.55, 0.35))}),
    "Hair": ("hair", POWDER),
    "Whiskers": ("hair", WHISKERS),
    "Hat": ("wool", {"name": "HQ_Tricorne", "base": BLACK, "border": LACE, "stripe": CRIMSON}),
    "Coat": ("wool", {"name": "HQ_DrummerCoat", "base": CRIMSON, "border": GOLD, "stripe": LACE}),
    "Waistcoat": ("wool", {"name": "HQ_DrummerWaistcoat", "base": BUFF, "border": BUFF, "stripe": BUFF}),
    "Linen": ("linen", {"name": "HQ_DrummerLinen", "base": LINEN}),
    "Gaiters": ("wool", {"name": "HQ_Gaiters", "base": BLACK, "border": (0.42, 0.42, 0.44), "stripe": (0.03, 0.03, 0.03)}),
    "Shoes": ("leather_dyed", {"name": "HQ_DrummerShoes", "base": (0.09, 0.08, 0.08), "dyed": (0.09, 0.08, 0.08)}),
    "Belt": ("linen", {"name": "HQ_CrossBelt", "base": (0.95, 0.94, 0.9)}),
    "Brass": ("gold", {"name": "HQ_DrummerBrass"}),
    "Drum": ("drum", {"name": "HQ_Drum", "shell": CRIMSON, "device": GOLD, "hoop_gold": GOLD}),
    "Sticks": ("siege", {"name": "HQ_Sticks", "wood": (0.7, 0.5, 0.3), "wood2": (0.55, 0.37, 0.2), "metal": "iron"}),
}
LOW_TARGETS = {"Skin": 6200, "Teeth": 80, "Hair": 1300, "Whiskers": 1100, "Hat": 1600, "Coat": 5000, "Waistcoat": 900,
               "Linen": 1100, "Gaiters": 1100, "Shoes": 700, "Belt": 500, "Brass": 900, "Drum": 2600, "Sticks": 300}
AO_EXCLUDE = ["Sticks"]


def prop_bones():
    out = []
    for side in ("R", "L"):
        G, T = stick_frame(side)
        out.append(("stick." + side, G, G + T * 0.3, "hand." + side))
    return out


def extra_bones():
    """The drum hangs from its hook (drum, on the root: it can swing a little on the hook); the drumhead's centre (drumhead,
    deforming nothing: the point the game's shockwave leaves from)."""
    hk, hd = hook_point()
    return [("drum", hk, DRUM_C, "root"), ("drumhead", DRUM_HEAD, DRUM_HEAD + DRUM_AX * 0.12, "drum")]


def hair_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"head": 1.0})


def stick_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"stick.R" if v.co.x < 0 else "stick.L": 1.0})


def weight_rules():
    arms = {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("custom", hair_weights), "Whiskers": ("rigid", "head"),
        "Hat": ("rigid", "head"),
        "Coat": ("transfer", TORSO | arms | {"thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Waistcoat": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.35, "thigh.L": 0.35}),
        "Linen": ("transfer", TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Gaiters": ("transfer", {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Shoes": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Belt": ("transfer", TORSO | {"clavicle.R"}, None),
        "Brass": ("transfer", TORSO | arms, None),
        "Drum": ("rigid", "drum"), "Sticks": ("custom", stick_weights),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Whiskers") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Drum":
        return 1.25
    if part == "Hat":
        return 1.15
    if part == "Sticks":
        return 0.7
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Whiskers", whiskers_field(), 0.0022 if fine else 0.003),
        ("Hat", hat_field(), 0.0024 if fine else 0.0032),
        ("Coat", coat_field(), 0.0026 if fine else 0.0036),
        ("Waistcoat", waistcoat_field(), 0.0026 if fine else 0.0036),
        ("Linen", linen_field(), 0.0024 if fine else 0.0034),
        ("Gaiters", gaiters_field(), 0.0024 if fine else 0.0032),
        ("Shoes", shoes_field(), 0.0022 if fine else 0.003),
        ("Belt", belt_field(), 0.0022 if fine else 0.003),
        ("Brass", brass_field(), 0.0016 if fine else 0.0022),
        ("Drum", drum_field(), 0.0022 if fine else 0.003),
        ("Sticks", sticks_field(), 0.0016 if fine else 0.0022),
    ]
