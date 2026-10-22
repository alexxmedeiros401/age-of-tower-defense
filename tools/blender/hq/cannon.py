"""The Cannon (HQ tower, Gunpowder Age): a long bronze field gun on its timber carriage, and the master gunner who serves
it. Rest pose: he stands in an A-pose facing -Y (the way it shoots), feet at z = 0, the gun on his left (+X) with its
wheels' axle a little in front of him; the gun is loaded and run out.

Him: the Bronze Age engineer's burly body (torsion.py), his own face: bald under a red knitted cap pushed back on his
head (a ribbed cuff, the top slouching back), a big black spade beard and a bushy moustache, bushy black brows drawn
down, a broad fleshy nose, a wide gap-toothed grin, a gold hoop in his left ear, a smudge of soot on his left cheek. A
white linen shirt open at the throat, its sleeves rolled up over his thick forearms; an open, sleeveless leather jerkin
studded with brass; a crimson sash knotted at his right hip, its ends fringed with gold; baggy dark breeches gathered at
the knee into tall boots with turned-down cuffs; a leather cartridge bag at his left hip on a strap over his right
shoulder, two rounds showing in its mouth. In his right fist the linstock: an ash staff with an iron foot and a forked
iron head holding the slow match, its tip smouldering (`Match`, shipped glowing). A rammer-and-sponge staff leans against
the front of the carriage; the round he loads (a ball tied to a cloth cartridge) rides its own bone.

The gun: a long bronze barrel (golden brown, patina in the recesses) tapering from the reinforced breech to a flared
muzzle, moulded rings at each step, a cascabel button, the vent on top of the breech, two dolphins (lifting handles) over
the trunnions, a crowned shield in relief on the chase; the trunnions in the beds of two thick oak cheeks with iron cap
squares; the cheeks stepped down to the trail that rests on the ground, iron bands and bolts, three transoms, the stool
bed and the elevating quoin under the breech; the axle-tree on iron arms through two big spoked wheels with iron tyres.

Painted labels on the carriage and wheels (material `siege`, iron fittings): 0 wood with the grain along Y, 10 along X,
11 along Z; 5 crimson paint; 6 iron."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import torsion as _t
from torsion import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD,
                     EYE_R, eye_c, smoothstep, hand_frame, HAND_S, fist_center, hand, foot, traps, neck_prim, deltoid,
                     upper_arm, eyes_field, skull, _forearm, torso_prims, belt_base, TORSO, TORSO_Z, torso_bones)

SOOT = 10                                                         # skin label: the smudge on his cheek
GX, GZ, CRIMSON, IRON = 10, 11, 5, 6                              # carriage labels (wood grain Y is 0)


# ======================================================================================= head
def fringe_mask(P):
    """The shaven fringe round the back and sides of his head below the cap (design coordinates): a shadow of stubble."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = cap_hem(Q) + F(0.01)
    band = np.maximum(z - top, F(1.6) - z)
    front = F(-0.03) - y + F(0.06) * smoothstep(1.66, 1.74, z)
    ear = np.where((ax > F(0.165)) & (y < F(0.085)) & (z < F(1.72)), F(1.0), F(-1.0))
    return np.maximum(np.maximum(band, front), ear)


# the cap's lower edge: a plane tilted back (pushed back on his head, the bald forehead showing) and a little to his left
def cap_hem(Q):
    return F(1.842) - F(0.29) * (Q[:, 1] + F(0.19)) + F(0.022) * Q[:, 0] / F(0.18)


def mouth_lines(x):
    """The grin's opening (design coordinates): the upper lip's lower edge and the lower lip's upper edge at x."""
    t = (x / F(0.07)) ** 2
    return F(1.557) + F(0.014) * t, F(1.527) + F(0.04) * t


def mouth_y(x):
    """The face's front at the mouth (design coordinates), curving back to the corners."""
    return F(-0.197) + F(0.034) * (x / F(0.07)) ** 2


def _mouth_cut(P):
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    zu, zl = mouth_lines(x)
    zc, hh = (zu + zl) / F(2), (zu - zl) / F(2)
    d = np.maximum(np.abs(z - zc) - hh, np.abs(x) - F(0.068))
    return np.maximum(d, y - (mouth_y(x) + F(0.05))) * F(HS)


def head(fd):
    """A broad, fierce, merry face: round cheeks pushed up by a wide grin, a heavy brow, deep-set eyes squeezed by the
    grin, a broad fleshy nose, big ears."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.79), (0.165, 0.175, 0.12)), 0.08, SKIN)                          # a broad, bald dome
    fd.add(E((0, -0.055, 1.588), (0.152, 0.138, 0.13)), 0.07, SKIN)                       # a heavy jaw (under the beard)
    fd.add(E((0, -0.134, 1.5), (0.09, 0.072, 0.07)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.11, -0.13, 1.636), 0.058), 0.05, SKIN)                             # round cheeks, pushed up
        fd.add(S((sx * 0.13, -0.045, 1.556), 0.052), 0.05, SKIN)
        pts = [hp((sx * 0.156, -0.055, 1.744)), hp((sx * 0.118, -0.134, 1.756)), hp((sx * 0.062, -0.178, 1.754)), hp((0.0, -0.188, 1.75))]
        fd.add(Chain(pts, [hr(0.013), hr(0.023), hr(0.027), hr(0.025)], k=hr(0.022)), hr(0.034), SKIN)     # heavy brow ridge
    fd.paint(Func(fringe_mask, HEAD_C - 0.4, HEAD_C + 0.3), STUBBLE)
    # two deep frown lines between the brows, two creases across the bald forehead
    for sx in (-1, 1):
        fd.sub(RoundCone(hp((sx * 0.012, -0.2, 1.738)), hp((sx * 0.016, -0.197, 1.764)), hr(0.002), hr(0.0017)), hr(0.003))
    sk = skull()
    for zc in (1.795, 1.82):
        pts = []
        for k in range(9):
            x = -0.085 + 0.17 * k / 8
            h, ok = ray_hit(sk, [hp((x, -0.6, zc + 0.01 * (x / 0.085) ** 2))], [v3((0, 1, 0))], tmax=0.7)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 3:
            fd.sub(Chain(pts, [hr(0.0026)] * len(pts), k=0.002), hr(0.003))
    # very bushy black brows, the inner ends drawn down, the outer ends flaring
    tuft = lambda P: F(0.0026) * NOISE(P * F(140)) + F(0.0012) * np.sin(P[:, 0] * F(360) + P[:, 2] * F(90))
    for sx in (-1, 1):
        pts = [hp((sx * 0.022, -0.214, 1.748)), hp((sx * 0.066, -0.21, 1.772)), hp((sx * 0.112, -0.188, 1.784)),
               hp((sx * 0.158, -0.142, 1.79))]
        fd.add(Chain([p + v3((0, 0.004, 0)) for p in pts], [hr(0.015), hr(0.019), hr(0.016), hr(0.008)], k=hr(0.009),
                     disp=tuft, disp_amp=0.004), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.024), hr(0.028), hr(0.024), hr(0.014)], k=hr(0.01)), BROW)
    # eyes, squeezed by the grin: the lower lids pushed up, laughing lines
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.0115))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.006)), Plane(ec + v3((0, 0, -hr(0.012))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.add(Ellipsoid(hp((sx * 0.07, -0.155, 1.64)), v3((0.03, 0.012, 0.011)) * HS), hr(0.012), SKIN)     # the grin's bags
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0085))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(3):                                                                    # laughing lines
            a = hp((sx * (0.11 + 0.004 * k), -0.132 + 0.006 * k, 1.684 - 0.013 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.026, 0.013, 0.008 - 0.012 * k)), hr(0.0022), hr(0.0014)), hr(0.003))
    # a broad fleshy nose: a short bridge, a big round tip, flared wings
    fd.add(RoundCone(hp((0, -0.19, 1.722)), hp((0, -0.236, 1.64)), hr(0.019), hr(0.027)), hr(0.018), SKIN)
    fd.add(S((0, -0.252, 1.616), 0.036), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.038, -0.226, 1.603), 0.025), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.019, -0.244, 1.588)), v3((0.01, 0.012, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
        # the grin's folds: from the nose wings round the cheeks to the mouth's corners
        fd.sub(Chain([hp((sx * 0.052, -0.214, 1.606)), hp((sx * 0.074, -0.19, 1.582)), hp((sx * 0.084, -0.17, 1.556))],
                     [hr(0.0028), hr(0.0034), hr(0.0024)], k=hr(0.003)), hr(0.004))
    # the grin: a wide open mouth (the teeth are their own part), dark inside; a full lower lip, a thin upper one
    lo, hi = HEAD_C + v3((-0.2, -0.4, -0.35)), HEAD_C + v3((0.2, 0.1, -0.05))
    fd.sub(Func(_mouth_cut, lo, hi), hr(0.003))
    fd.paint(Func(lambda P: _mouth_cut(P) - F(0.004), lo, hi), MOUTH)
    xs = np.linspace(-0.066, 0.066, 7)
    zl = [float(mouth_lines(F(x))[1]) for x in xs]
    zu = [float(mouth_lines(F(x))[0]) for x in xs]
    ys = [float(mouth_y(F(x))) for x in xs]
    rl = [0.004, 0.0075, 0.0095, 0.01, 0.0095, 0.0075, 0.004]
    fd.add(Chain([hp((x, y + 0.004, z - r * 0.8)) for x, y, z, r in zip(xs, ys, zl, rl)], [hr(r) for r in rl], k=hr(0.006)), hr(0.007), LIP)
    ru = [0.003, 0.004, 0.0045, 0.0045, 0.0045, 0.004, 0.003]
    fd.add(Chain([hp((x, y + 0.004, z + r * 0.8)) for x, y, z, r in zip(xs, ys, zu, ru)], [hr(r) for r in ru], k=hr(0.004)), hr(0.005), LIP)
    # big ears, the left lobe pierced for the hoop
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.029, 0.052, 0.066)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.013, 0.033, 0.043)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
        fd.add(Sphere(hp((sx * 0.188, 0.028, 1.608)), hr(0.017)), hr(0.01), SKIN)                 # fleshy lobes
    # soot: a smudge across his left cheekbone and a smear on his brow (the gunner wipes his face with sooty hands)
    def soot(P):
        Q = hinv(P)
        a = ((Q[:, 0] - F(0.112)) / F(0.045)) ** 2 + ((Q[:, 1] + F(0.14)) / F(0.05)) ** 2 + ((Q[:, 2] - F(1.664) + F(0.15) * (Q[:, 0] - F(0.11))) / F(0.02)) ** 2
        b = ((Q[:, 0] + F(0.05)) / F(0.04)) ** 2 + ((Q[:, 1] + F(0.18)) / F(0.06)) ** 2 + ((Q[:, 2] - F(1.808)) / F(0.012)) ** 2
        n = F(0.35) * NOISE(Q * F(38)) + F(0.2) * NOISE(Q * F(90))
        return (np.minimum(a, b) - F(1.0) + n) * F(0.02)
    fd.paint(Func(soot, HEAD_C - 0.3, HEAD_C + 0.3), SOOT)


def body_parts(fd):
    """The Torsion engineer's barrel-chested body (torsion.body_parts) with this head, thick hairy forearms."""
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
        fd.add(RoundCone(el, wr, 0.082, 0.06), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.104, 0.094, 0.14), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.14, 0.092), 0.065, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.13, 0.12, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.048, SKIN)
        fd.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038, SKIN)
        fd.add(RoundCone(kn, an, 0.088, 0.058), 0.038, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043, SKIN)
        foot(fd, side)
        # dark hair on his forearms (only near the forearm's axis)
        ax = norm(wr - el)
        def hairy(P, el=el, ax=ax):
            q = P - el.astype(F)
            t = q @ ax.astype(F)
            perp = np.sqrt(np.maximum((q * q).sum(1) - t * t, F(0)))
            return np.maximum(np.abs(t - F(0.17)) - F(0.12), perp - F(0.11))
        fd.paint(Func(hairy, el - 0.4, el + 0.4), STUBBLE)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


def teeth_field():
    """The grin's teeth: a row of six big upper teeth (one missing on his right) and four lower ones."""
    fd = Field("Teeth")
    for x in (-0.047, -0.03, -0.01, 0.01, 0.03, 0.047):
        if abs(x + 0.03) < 1e-6:
            continue                                                               # a gap where a tooth was knocked out
        zu, _ = mouth_lines(F(x))
        y = float(mouth_y(F(x))) + 0.011 + 0.006 * (x / 0.047) ** 2
        w = 0.0085 if abs(x) < 0.02 else 0.0075
        yaw = math.atan2(0.034 * 2 * x / 0.07 ** 2, 1.0)
        fd.add(RoundBox(hp((x, y, float(zu) - 0.008)), v3((w, 0.006, 0.011)) * HS, hr(0.0035), R=euler(0, 0, yaw)), 0.0)
    for x in (-0.026, -0.009, 0.009, 0.026):
        _, zl = mouth_lines(F(x))
        y = float(mouth_y(F(x))) + 0.014
        fd.add(RoundBox(hp((x, y, float(zl) + 0.003)), v3((0.007, 0.005, 0.007)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= spade beard, moustache
def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.055, 1.588), (0.152, 0.138, 0.13)), 0.07)
    fd.add(E((0, -0.134, 1.5), (0.09, 0.072, 0.07)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.11, -0.13, 1.636)), hr(0.058)), 0.05)
        fd.add(Sphere(hp((sx * 0.13, -0.045, 1.556)), hr(0.052)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


SPADE_TOP = hp((0.0, -0.17, 1.47))                     # the spade's top middle, under his chin
SPADE_DN = norm(v3((0.0, -0.3, -1.0)))                 # down the spade (it lies out over his chest)
SPADE_N = norm(v3((0.0, -1.0, 0.3)))                   # out of its face
SPADE_L = 0.31                                         # its length, to the point
SPADE_W = 0.128                                        # its half width at the top


def _spade_hw(v):
    k = np.clip((F(SPADE_L) - v) / F(SPADE_L - 0.1), 0, 1)
    return np.where(v < F(0.1), F(SPADE_W) + F(0.012) * np.sin(v / F(0.1) * F(math.pi / 2)), F(SPADE_W + 0.012) * k ** F(0.72))


def beard_tex(P):
    """Wavy locks running down the beard, following the spade's outline to its point; positive pushes in."""
    q = P - SPADE_TOP.astype(F)
    v = np.maximum(q @ SPADE_DN.astype(F), F(0))
    hw = np.maximum(_spade_hw(v), F(0.03))
    ph = P[:, 0] / hw * F(6.5) + F(0.35) * np.sin(P[:, 2] * F(28) + P[:, 0] * F(12))
    lock = np.abs(np.sin(ph * F(math.pi / 2)))
    return F(0.003) - F(0.0062) * lock * lock + F(0.0013) * NOISE(P * np.array([90, 90, 30], F))


def _spade(P):
    q = P - SPADE_TOP.astype(F)
    v = q @ SPADE_DN.astype(F)
    w = q @ SPADE_N.astype(F)
    x = P[:, 0]
    hw = _spade_hw(np.maximum(v, F(0)))
    th = F(0.06) - F(0.034) * np.clip(v / F(SPADE_L), 0, 1)
    belly = th * (F(1) - F(0.45) * (x / np.maximum(hw, F(0.02))) ** 2)
    d_w = np.maximum(w - belly, -th - w)
    d_x = np.abs(x) - hw
    d_v = np.maximum(-v - F(0.04), v - F(SPADE_L))
    return np.maximum(np.maximum(d_x, d_w), d_v) * F(0.8)


def beard_field():
    """A big black spade beard: over the jaw and up the cheeks to the sideburns, hanging broad onto his chest and
    trimmed to a point; a bushy moustache sweeping out over the grin, its ends turned up."""
    fd = Field("Beard")
    hull = head_hull()
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.545) + F(0.095) * smoothstep(0.065, 0.145, ax)                 # chin and jaw, up the cheeks
        top = np.where(ax > F(0.15), F(1.7), top)                                 # sideburns to the ears
        lips = (x / F(0.084)) ** 2 + ((y + F(0.185)) / F(0.07)) ** 2 + ((z - F(1.546)) / F(0.034)) ** 2 - F(1.0)
        back = np.where(ax > F(0.14), y - F(0.03), y - F(0.0))
        return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), F(1.38) - z)
    fd.add(Inter(Shell(hull, 0.012, 0.03, pad=0.06, disp=beard_tex, disp_amp=0.008), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.008), 0.0)
    lo = SPADE_TOP - v3((0.2, 0.25, 0.4))
    hi = SPADE_TOP + v3((0.2, 0.15, 0.12))
    fd.add(Func(_spade, lo, hi, disp=beard_tex, disp_amp=0.008), 0.045)
    fd.add(Ellipsoid(hp((0, -0.16, 1.47)), v3((0.13, 0.07, 0.07)) * HS, disp=beard_tex, disp_amp=0.008), 0.04)
    # the moustache: two thick locks from under the nose out over the grin, curling up at the ends
    strands = lambda P: F(0.0022) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.23, 1.583)), hp((sx * 0.04, -0.218, 1.574)), hp((sx * 0.074, -0.194, 1.572)),
               hp((sx * 0.1, -0.168, 1.582)), hp((sx * 0.112, -0.152, 1.6))]
        fd.add(Lock(pts, [hr(0.016), hr(0.02), hr(0.017), hr(0.012), hr(0.006)], [hr(0.011), hr(0.013), hr(0.011), hr(0.008), hr(0.005)],
                    [norm(v3((sx * 0.25, -1, 0.3)))] * 5, k=hr(0.006), disp=strands, disp_amp=0.003), hr(0.006))
    return fd


# ======================================================================================= the knitted cap
def cap_field():
    """A red knitted cap pushed back on his bald head: a snug crown with fine knitted ribs, a thick ribbed cuff rolled
    round its edge, the top slouching back."""
    fd = Field("Cap")
    sk = skull()
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.34
    def above(P, off):
        Q = hinv(P)
        return (cap_hem(Q) + F(off) - Q[:, 2]) * F(HS)
    def knit(P):
        Q = hinv(P)
        a = np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.02)))
        return F(0.0011) * np.sin(a * F(54)) * np.sin(Q[:, 2] * F(260)) + F(0.0008) * NOISE(Q * F(70))
    def ribs(P):
        Q = hinv(P)
        a = np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.02)))
        return F(0.0032) * np.abs(np.sin(a * F(30))) + F(0.0008) * NOISE(Q * F(60))
    fd.add(Inter(Shell(sk, 0.013, 0.018, pad=0.06, disp=knit, disp_amp=0.002), Func(lambda P: above(P, 0.03), lo, hi), 0.004), 0.0)
    # the slouch: the cap's top, too long for his head, folded over backward
    fd.add(Ellipsoid(hp((0.025, 0.1, 1.945)), v3((0.13, 0.115, 0.068)) * HS, R=euler(0.45, 0.1, 0.2), disp=knit, disp_amp=0.002), 0.04)
    # the rolled cuff
    def band(P):
        Q = hinv(P)
        h = Q[:, 2] - cap_hem(Q)
        return np.maximum(-h, h - F(0.046)) * F(HS)
    fd.add(Inter(Shell(sk, 0.027, 0.03, pad=0.07, disp=ribs, disp_amp=0.004), Func(band, lo, hi), 0.008), 0.006)
    return fd


def gold_field():
    """A gold hoop through his left earlobe."""
    fd = Field("Gold")
    lobe = hp((0.192, 0.026, 1.603))
    c = lobe + v3((0.006, 0.0, -0.022))
    fd.add(Torus(c, 0.024, 0.0048, R=rot_from_axes(z_axis=(0.96, -0.1, 0.25))), 0.0)
    return fd


# ======================================================================================= shirt, jerkin, sash, breeches
def _arm_coord(P, side):
    """Distance along his arm from the shoulder (upper arm, then forearm) and the squared distance off its axis."""
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    out_s = out_d = None
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


UA_LEN = float(np.linalg.norm(J["elbow_R"] - J["shoulder_R"]))
ROLL_S = UA_LEN * 0.8                       # the rolled sleeves' roll: 80% of the way down his upper arm


def shirt_base():
    b = Field("ShirtBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(neck_prim(), 0.05)
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        b.add(deltoid(side), 0.055)
        b.add(upper_arm(side), 0.05)
        b.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.097, 0.1, 0.13), R=rot_from_axes(z_axis=el - sh)), 0.04)
        b.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028)
    return b


def _sleeve_cut(P):
    """> 0 past the rolled sleeves' ends (only near his arms)."""
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2 = _arm_coord(P, side)
        near = (d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3))
        out = np.maximum(out, np.where(near, s - F(ROLL_S), F(-1.0)))
    return out


def shirt_neck(P):
    """The shirt's neck: open in a deep slit at the front (it rises away from his neck over the shoulders)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.0)) / F(0.18), 0, 1)
    slit = F(0.2) * front * np.exp(-(x / F(0.055)) ** 2)
    return z - (F(1.47) - F(0.05) * front * np.exp(-(x / F(0.15)) ** 2) - slit + F(0.3) * smoothstep(0.17, 0.25, np.abs(x)))


def shirt_field():
    """White linen (label 0): full, tucked into the breeches, open at the throat in a slit with its collar turned
    back; the sleeves rolled up above the elbows in thick rolls."""
    fd = Field("Shirt")
    base = shirt_base()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        return F(0.0035) * np.sin(a * F(11) + F(0.9) * NOISE(P * F(3))) + F(0.0015) * NOISE(P * F(22))
    def keep(P):
        k = np.maximum(F(0.86) - P[:, 2], shirt_neck(P))
        return np.maximum(k, _sleeve_cut(P))
    fd.add(Inter(Shell(base, 0.024, 0.02, pad=0.1, disp=folds, disp_amp=0.005), Func(keep, (-1, -1, 0.7), (1, 1, 1.7)), 0.005), 0.0)
    # the rolls: a fat doughnut of linen round each upper arm, two folds in it
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        c = sh + ax * (ROLL_S + 0.005)
        arm = Field("ArmHull")
        arm.add(upper_arm(side), 0.0)
        arm.add(Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.097, 0.1, 0.13), R=rot_from_axes(z_axis=el - sh)), 0.04)
        arm.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028)
        roll = lambda P, c=c, ax=ax: F(0.003) * np.sin((P - c.astype(F)) @ ax.astype(F) * F(190)) + F(0.002) * NOISE(P * F(30))
        fd.add(Inter(Shell(arm, 0.042, 0.046, pad=0.08, disp=roll, disp_amp=0.004),
                     Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.03), c - 0.25, c + 0.25), 0.01), 0.008)
    # the collar: turned back on each side of the slit, lying on the shirt
    outer = Func(lambda P: base.eval(P, margin=0.1) - F(0.036), (-1, -1, 0.7), (1, 1, 1.7))
    for sx in (-1, 1):
        pts = []
        for x, z in ((0.03, 1.27), (0.055, 1.36), (0.09, 1.43), (0.13, 1.47)):
            h, ok = ray_hit(outer, [v3((sx * x, -0.7, z))], [v3((0, 1, 0))], tmax=0.9)
            if ok[0]:
                pts.append(h[0] + v3((0, -0.004, 0)))
        if len(pts) >= 3:
            ws = [0.018, 0.028, 0.03, 0.026][:len(pts)]
            fd.add(Lock(pts, ws, [0.006] * len(pts), [v3((sx * 0.3, -1, 0.3))] * len(pts), k=0.006), 0.006)
    return fd


def jerkin_base():
    b = Field("JerkinBase")
    for i, (p, k) in enumerate(torso_prims()):
        if i in (2, 3):                                     # (no pectorals: the leather hangs straight over his chest)
            continue
        b.add(p, k)
    b.add(Ellipsoid((0, -0.1, 1.215), (0.27, 0.115, 0.155), R=euler(0.12, 0, 0)), 0.06)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.055)
    return b


JERKIN_HEM = 0.95


def jerkin_open(z):
    """Half the width of the jerkin's open front at height z (it hangs open, wider toward the hem)."""
    return F(0.075) + F(0.075) * smoothstep(1.32, 0.95, z)


def _armhole(P, side):
    sx = -1 if side == "R" else 1
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    ax = norm(el - sh)
    c = sh + ax * 0.06 + v3((sx * 0.02, 0.0, -0.05))
    R = rot_from_axes(z_axis=ax)
    q = (P - c.astype(F)) @ R.astype(F)
    return (np.sqrt((q[:, 0] / F(0.15)) ** 2 + (q[:, 1] / F(0.16)) ** 2 + (q[:, 2] / F(0.22)) ** 2) - F(1.0)) * F(0.15)


def jerkin_keep(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    neck = z - (F(1.45) - F(0.05) * np.clip(-y / F(0.18), 0, 1) + F(0.3) * smoothstep(0.17, 0.25, np.abs(x)))
    front = np.minimum(jerkin_open(z) - np.abs(x), F(-0.03) - y)
    k = np.maximum(np.maximum(neck, F(JERKIN_HEM) - z), front)
    for side in ("R", "L"):
        k = np.maximum(k, -_armhole(P, side))
    return k


def jerkin_field():
    """An open sleeveless jerkin of brown leather (label 0) to the waist, a rolled edge, brass studs (6) down the fronts."""
    fd = Field("Jerkin")
    base = jerkin_base()
    stiff = lambda P: F(0.0015) * NOISE(P * F(18)) + F(0.0008) * NOISE(P * F(55))
    fd.add(Inter(Shell(base, 0.06, 0.018, pad=0.12, disp=stiff, disp_amp=0.002), Func(jerkin_keep, (-1, -1, 0.8), (1, 1, 1.7)), 0.004), 0.0)
    # brass studs down each front edge
    outer = Func(lambda P: base.eval(P, margin=0.12) - F(0.07), (-1, -1, 0.8), (1, 1, 1.7))
    for sx in (-1, 1):
        for k in range(6):
            z = 1.0 + 0.055 * k
            x = sx * (float(jerkin_open(F(z))) + 0.018)
            h, ok = ray_hit(outer, [v3((x, -0.8, z))], [v3((0, 1, 0))], tmax=0.9)
            if ok[0]:
                fd.add(Sphere(h[0], 0.0085), 0.002, 6)
    return fd


SASH_Z = 0.915


def sash_knot():
    """The sash's knot: on its outside at his right hip, a little to the front."""
    bb = belt_base()
    d = norm(v3((-0.86, -0.5, 0.0)))
    h, ok = ray_hit(Func(lambda P: bb.eval(P, margin=0.15) - F(0.1), (-1, -1, 0.6), (1, 1, 1.2)),
                    [v3((0, 0.0, 0.905)) + d * 0.7], [-d], tmax=0.8)
    return (h[0] if ok[0] else v3((-0.33, -0.17, 0.905))) + d * 0.02


KNOT = sash_knot()


def sash_field():
    """A crimson wool sash (label 0) wound round his waist over the jerkin's hem, knotted at his right hip, two ends
    hanging, fringed with gold (5); gold stripes along its edges (6)."""
    fd = Field("Sash")
    bb = belt_base()
    folds = lambda P: F(0.004) * np.sin(P[:, 2] * F(150) + F(1.2) * NOISE(P * F(6))) + F(0.0015) * NOISE(P * F(30))
    def band(P):
        return np.abs(P[:, 2] - (F(SASH_Z) + F(0.03) * P[:, 1])) - F(0.058)
    fd.add(Inter(Shell(bb, 0.08, 0.034, pad=0.12, disp=folds, disp_amp=0.005), Func(band, (-1, -1, 0.7), (1, 1, 1.15)), 0.006), 0.0)
    fd.paint(Func(lambda P: np.abs(np.abs(P[:, 2] - (F(SASH_Z) + F(0.03) * P[:, 1])) - F(0.044)) - F(0.006), (-1, -1, 0.7), (1, 1, 1.15)), 6)
    cl = lambda P: F(0.003) * NOISE(P * F(25)) + F(0.0015) * NOISE(P * F(60))
    fd.add(Ellipsoid(KNOT, (0.045, 0.04, 0.05), R=euler(0, 0, -0.5), disp=cl, disp_amp=0.004), 0.012)
    for dx, ln, sw in ((-0.03, 0.27, 0.0), (0.025, 0.22, 0.04)):
        p0 = KNOT + v3((dx * 0.5, -0.01, -0.03))
        pts = [p0, p0 + v3((dx, -0.02 + sw * 0.3, -ln * 0.5)), p0 + v3((dx * 1.4 + sw * 0.3, -0.012, -ln))]
        nn = norm(v3((-0.6, -1.0, 0.0)))
        fd.add(Lock(pts, [0.04, 0.042, 0.04], [0.007, 0.007, 0.006], [nn] * 3, k=0.006, disp=cl, disp_amp=0.003), 0.006)
        end = pts[-1]
        for j in range(7):                                                   # the fringe
            o = (j - 3) * 0.011
            side = norm(np.cross(nn, v3((0, 0, 1))))
            a = end + side * o + v3((0, 0, 0.008))
            fd.add(RoundCone(a, a + v3((0, -0.004, -0.045 - 0.006 * (j % 2))), 0.0045, 0.003), 0.002, 5)
    return fd


def legs_hull():
    b = Field("LegsHull")
    tp = torso_prims()
    b.add(tp[5][0], 0.0)
    b.add(tp[4][0], 0.08)
    for side in ("R", "L"):
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        b.add(RoundCone(hip, kn, 0.14, 0.092), 0.065)
        b.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.13, 0.12, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.048)
        b.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038)
        b.add(RoundCone(kn, an, 0.088, 0.058), 0.038)
        b.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043)
    return b


BREECH_TOP, BREECH_BOT = 0.99, 0.37


def breeches_field():
    """Baggy breeches of dark wool (label 0), full over the thighs, gathered below the knee into the boots."""
    fd = Field("Breeches")
    hull = legs_hull()
    lo, hi = v3((-0.5, -0.4, 0.25)), v3((0.5, 0.45, 1.1))
    def off(z):
        return F(0.017) + F(0.034) * smoothstep(0.43, 0.6, z) * (F(1) - F(0.35) * smoothstep(0.85, 0.98, z))
    def fn(P):
        d = hull.eval(P, margin=0.1)
        return np.abs(d - off(P[:, 2])) - F(0.011)
    folds = lambda P: (F(0.006) * np.sin(np.arctan2(P[:, 1] - F(0.03), np.abs(P[:, 0]) - F(0.17)) * F(7) + P[:, 2] * F(30)
                                         + F(0.8) * NOISE(P * F(4))) * smoothstep(0.47, 0.6, P[:, 2]) + F(0.0015) * NOISE(P * F(25)))
    fd.add(Inter(Func(fn, lo, hi, disp=folds, disp_amp=0.007),
                 Func(lambda P: np.maximum(P[:, 2] - F(BREECH_TOP), F(BREECH_BOT) - P[:, 2]), lo, hi), 0.004), 0.0)
    return fd


# ======================================================================================= leather: boots, strap, cartridge bag
SAT_C = v3((0.41, 0.0, 0.8))                     # the cartridge bag's middle (at his left hip)
SAT_HALF = (0.05, 0.11, 0.085)                   # its half depth (x), width (y), height (z)


def sat_mouth():
    return SAT_C + v3((0.0, 0.0, SAT_HALF[2]))


def boot_hull(side):
    ft = Field("BootHull")
    foot(ft, side)
    kn, an = J["knee_" + side], J["ankle_" + side]
    ft.add(RoundCone(kn, an, 0.088, 0.058), 0.03)
    ft.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043)
    ft.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038)
    return ft


def leather_field():
    """Tall boots of dark leather (label 0) with turned-down bucket tops and thick soles; the cartridge bag's strap over
    his right shoulder; the bag itself at his left hip, its flap thrown back, two rounds (iron balls, 6, tied to cloth
    cartridges, 5) showing in its mouth; iron buckles."""
    fd = Field("Leather")
    crease = lambda P: F(0.0016) * NOISE(P * F(26))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an, kn = J["ankle_" + side], J["knee_" + side]
        ft = boot_hull(side)
        fd.add(Inter(Shell(ft, 0.016, 0.013, pad=0.07, disp=crease, disp_amp=0.002),
                     Func(lambda P: P[:, 2] - F(0.44), an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.45))), 0.004), 0.0)
        # the bucket top: a wide cuff turned down over the boot's shaft
        def cuff(P, kn=kn):
            return np.maximum(P[:, 2] - (F(0.5) - F(0.03) * (P[:, 1] - F(kn[1])) / F(0.1)), F(0.38) - P[:, 2])
        fd.add(Inter(Shell(ft, 0.045, 0.012, pad=0.09, disp=crease, disp_amp=0.002), Func(cuff, kn - v3((0.3, 0.3, 0.2)), kn + v3((0.3, 0.3, 0.2))), 0.006), 0.006)
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.098)), (0.082, 0.165, 0.016), 0.01, R=Rz), 0.006)
        fd.add(RoundBox(an + fwd * -0.035 + v3((0, 0, -0.08)), (0.06, 0.05, 0.03), 0.012, R=Rz), 0.008)          # the heel
    # the strap: over his right shoulder, across his chest and back to the bag at his left hip
    jb = jerkin_base()
    a = v3((-0.2, 0.06, 1.47))
    b = SAT_C + v3((-0.02, 0.0, SAT_HALF[2] - 0.02))
    nrm = norm(np.cross(b - a, v3((0, 1, 0))))
    def strap(P):
        return np.abs((P - a.astype(F)) @ nrm.astype(F)) - F(0.024)
    fd.add(Inter(Shell(jb, 0.088, 0.012, pad=0.14), Func(strap, (-0.7, -0.6, 0.7), (0.7, 0.6, 1.7)), 0.003), 0.003)
    # the bag: a stiff leather box, open at the top, its flap thrown back over his hip
    R = rot_from_axes(z_axis=(0, 0, 1), y_axis=(0, 1, 0))
    hx, hy, hz = SAT_HALF
    box = RoundBox(SAT_C, (hx, hy, hz), 0.03, R=R)
    fd.add(box, 0.0)
    fd.sub(RoundBox(SAT_C + v3((0, 0, hz)), (hx - 0.012, hy - 0.012, 0.05), 0.012), 0.006)
    fd.add(RoundBox(SAT_C + v3((0.0, hy + 0.01, hz - 0.045)), (hx + 0.004, 0.006, 0.06), 0.005, R=euler(-0.12, 0, 0)), 0.004)   # the flap, thrown back
    fd.add(Torus(SAT_C + v3((0.0, hy + 0.018, hz - 0.08)), 0.016, 0.0045, R=rot_from_axes(z_axis=(0, 1, 0))), 0.002, 6)      # its buckle
    # two rounds showing in its mouth
    for k, yy in enumerate((-0.05, 0.045)):
        c = SAT_C + v3((0.0, yy, hz - 0.012))
        fd.add(Sphere(c + v3((0, 0, 0.02)), ROUND_R * 0.95), 0.003, 6)
        fd.add(Cylinder(c - v3((0, 0, 0.03)), ROUND_R * 0.82, 0.06, rr=0.012), 0.004, 5)
    return fd


# ======================================================================================= the linstock (rigid in his right fist)
LS_LEN = 1.12              # the iron foot's tip -> the fork's crotch
LS_GRIP = 0.34             # the foot's tip -> where his fist holds it in the rest pose
LS_EMBER = 1.262           # the foot's tip -> the smouldering end of the match (along the staff)


def linstock_frame():
    """Rest pose: the staff along the right fist's thumb axis T through the fist's middle G; Fv across it (the fist's
    fingers), B = T x Fv (the fork's plane is (T, B)). Returns G, T, Fv, B and the foot's tip."""
    wr, f, n, t = hand_frame("R")
    G = fist_center("R")
    T = norm(t)
    Fv = norm(f - T * (f @ T))
    B = norm(np.cross(T, Fv))
    return G, T, Fv, B, G - T * LS_GRIP


def ember_pt():
    """The match's smouldering end (rest pose): out past the fork's B-side tip."""
    G, T, Fv, B, foot0 = linstock_frame()
    return foot0 + T * LS_EMBER + B * 0.028


def linstock_field():
    """An ash staff (label 0) with an iron-shod point (6) to stand it in the ground and a forked iron head; the slow
    match (5) coiled round the staff under the head, both ends clamped in the fork's jaws."""
    fd = Field("Linstock")
    G, T, Fv, B, f0 = linstock_frame()
    grain = lambda P: F(0.0008) * NOISE(P * F(90))
    fd.add(RoundCone(f0 + T * 0.075, f0 + T * (LS_LEN - 0.03), 0.017, 0.019, disp=grain, disp_amp=0.001), 0.0)
    fd.add(RoundCone(f0 + T * 0.004, f0 + T * 0.07, 0.004, 0.017), 0.004, 6)                  # the point
    fd.add(Cylinder(f0 + T * 0.085, 0.021, 0.035, rr=0.004, R=rot_from_axes(z_axis=T)), 0.003, 6)
    fd.add(Cylinder(f0 + T * (LS_LEN - 0.03), 0.024, 0.07, rr=0.006, R=rot_from_axes(z_axis=T)), 0.004, 6)    # the socket
    C = f0 + T * LS_LEN
    for s in (-1, 1):                                                                     # the fork's arms, curling in
        pts = [C - T * 0.01, C + T * 0.03 + B * (s * 0.036), C + T * 0.075 + B * (s * 0.046), C + T * 0.108 + B * (s * 0.03)]
        fd.add(Chain(pts, [0.011, 0.009, 0.008, 0.007], k=0.004), 0.004, 6)
        fd.add(Sphere(pts[-1], 0.0095), 0.003, 6)
    # the match: a coil round the staff, its two ends up to the jaws (the lit end out past the B-side jaw)
    coil = []
    for k in range(29):
        a = 2 * math.pi * k / 7
        coil.append(f0 + T * (0.84 + 0.0042 * k) + (Fv * math.cos(a) + B * math.sin(a)) * 0.027)
    fd.add(Chain(coil, [0.0075] * len(coil), k=0.003), 0.003, 5)
    top = coil[-1]
    for s in (-1, 1):
        tip = C + T * 0.108 + B * (s * 0.03)
        end = tip + T * 0.016 + B * (s * 0.006) if s < 0 else ember_pt() - T * 0.012
        fd.add(Chain([top, C - T * 0.03 + B * (s * 0.03), C + T * 0.05 + B * (s * 0.05), tip, end], [0.0075] * 5, k=0.004), 0.003, 5)
    return fd


def match_field():
    """The match's smouldering end (shipped as a glowing mesh)."""
    fd = Field("Match")
    G, T, Fv, B, f0 = linstock_frame()
    e = ember_pt()
    fd.add(RoundCone(e - T * 0.024, e - T * 0.006, 0.0125, 0.011), 0.0)
    return fd


# ======================================================================================= the gun (layout)
MX = 1.0                    # the gun's centre line (x); it shoots toward -Y
AY = -0.5                   # the axle (y)
WR = 0.4                    # the wheels' radius (to the tyres' tread)
WX = 0.355                  # the wheels' planes (x, from MX)
TY, TZ = AY - 0.02, 0.64    # the trunnions' axis
ELEV = math.radians(4.0)    # the barrel's elevation (the muzzle up)
GD = v3((0.0, -math.cos(ELEV), math.sin(ELEV)))     # along the bore, toward the muzzle
GU = v3((0.0, math.sin(ELEV), math.cos(ELEV)))      # up, across the bore
GX_ = v3((1.0, 0.0, 0.0))
TRUN = v3((MX, TY, TZ))
S_MUZ = 0.932               # trunnions -> the muzzle's face
S_VENT = -0.468             # trunnions -> the vent
S_BREECH = -0.555           # trunnions -> the base ring (the breech's face)
BORE_R = 0.052
ROUND_R = 0.045             # the shot's radius
CHEEK_X = 0.19              # the cheeks' middle planes (x, from MX)
CHEEK_T = 0.07              # their thickness
TRAIL_Y = AY + 0.81         # where the trail meets the ground


def bore_pt(s, up=0.0, side=0.0):
    return TRUN + GD * s + GU * up + GX_ * side


def barrel_r(s):
    """The barrel's outer radius at s (plain surface between the mouldings)."""
    tab = [(-0.555, 0.146), (-0.06, 0.137), (-0.058, 0.13), (0.29, 0.121), (0.292, 0.111), (0.8, 0.091), (0.802, 0.089),
           (0.905, 0.113), (0.932, 0.113)]
    xs = [a for a, _ in tab]
    ys = [b for _, b in tab]
    return float(np.interp(s, xs, ys))


VENT = bore_pt(S_VENT, barrel_r(S_VENT) + 0.012)     # the vent's mouth (the match touches it here)
MUZZLE = bore_pt(S_MUZ)


def capped_cone(a, b, ra, rb, rr=0.0, disp=None, disp_amp=0.0):
    """A capped cone from a (radius ra) to b (radius rb), its rims rounded by rr (Inigo Quilez's sdCappedCone)."""
    a, b = v3(a), v3(b)
    ax = norm(b - a)
    A, Bp = (a + ax * rr).astype(F), (b - ax * rr).astype(F)
    r0, r1 = F(ra - rr), F(rb - rr)
    ba = Bp - A
    baba = F(ba @ ba)
    rba = r1 - r0
    kk = rba * rba + baba
    def fn(P):
        pa = P - A
        papa = (pa * pa).sum(1)
        paba = (pa @ ba) / baba
        x = np.sqrt(np.maximum(papa - paba * paba * baba, F(0)))
        cax = np.maximum(F(0), x - np.where(paba < F(0.5), r0, r1))
        cay = np.abs(paba - F(0.5)) - F(0.5)
        f = np.clip((rba * (x - r0) + paba * baba) / kk, 0, 1)
        cbx = x - r0 - f * rba
        cby = paba - f
        sg = np.where((cbx < 0) & (cay < 0), F(-1), F(1))
        return sg * np.sqrt(np.minimum(cax * cax + cay * cay * baba, cbx * cbx + cby * cby * baba)) - F(rr)
    r = max(ra, rb)
    return Func(fn, np.minimum(a, b) - r - 0.01, np.maximum(a, b) + r + 0.01, disp=disp, disp_amp=disp_amp)


def _ring(s, R, r):
    return Torus(bore_pt(s), R, r, R=rot_from_axes(z_axis=GD))


def _barrel_local(P):
    q = P - TRUN.astype(F)
    s = q @ GD.astype(F)
    x = q @ GX_.astype(F)
    u = q @ GU.astype(F)
    return s, x, u


S_ARMS = 0.46               # the crowned shield's middle on the chase


def _arms(P, which):
    """The crowned shield in relief on top of the chase (its crown toward the breech): 'shield' or 'crown'."""
    s, x, u = _barrel_local(P)
    rho = np.sqrt(x * x + u * u)
    rs = F(0.111) + (F(0.091) - F(0.111)) * np.clip((s - F(0.292)) / F(0.508), 0, 1)
    a = s - F(S_ARMS)
    b = np.arctan2(x, u) * rs
    if which == "shield":
        hw, R = F(0.036), F(0.064)
        rect = np.maximum(np.maximum(np.abs(b) - hw, F(-0.042) - a), a - F(0.01))
        c1 = np.sqrt((a - F(0.01)) ** 2 + (b + (R - hw)) ** 2) - R
        c2 = np.sqrt((a - F(0.01)) ** 2 + (b - (R - hw)) ** 2) - R
        low = np.maximum(np.maximum(c1, c2), F(0.01) - a)
        d2 = np.minimum(rect, low)
        h = F(0.0065)
    elif which == "cross":
        d2 = np.minimum(np.maximum(np.abs(b) - F(0.0075), np.abs(a - F(0.008)) - F(0.043)),
                        np.maximum(np.abs(a + F(0.008)) - F(0.0075), np.abs(b) - F(0.027)))
        h = F(0.0105)
    else:
        band = np.maximum(np.abs(b) - F(0.034), np.abs(a + F(0.055)) - F(0.008))
        pts = None
        for bb in (-0.027, 0.0, 0.027):
            t = np.clip((F(-0.063) - a) / F(0.024), 0, 1)                     # up from the band toward the breech
            p = np.maximum(np.abs(b - F(bb)) - F(0.011) * (F(1) - t), np.maximum(F(-0.088) - a, a + F(0.06)))
            pr = np.sqrt((a + F(0.09)) ** 2 + (b - F(bb)) ** 2) - F(0.0065)
            p = np.minimum(p, pr)
            pts = p if pts is None else np.minimum(pts, p)
        d2 = np.minimum(band, pts)
        h = F(0.008)
    return np.maximum(np.maximum(d2, rho - (rs + h)), (rs - F(0.012)) - rho)


def barrel_field():
    """The bronze barrel (label 0; the crown and the cross on the arms gilt, 5): breech, first and second reinforce,
    chase and muzzle with moulded rings at each step, a cascabel button, the vent field, the trunnions and their
    rimbases, two dolphins, the crowned shield; the bore."""
    fd = Field("Barrel")
    hammer = lambda P: F(0.0006) * NOISE(P * F(60))
    fd.add(capped_cone(bore_pt(S_BREECH), bore_pt(-0.058), 0.146, 0.137, rr=0.012, disp=hammer, disp_amp=0.001), 0.0)
    fd.add(capped_cone(bore_pt(-0.062), bore_pt(0.292), 0.13, 0.121, rr=0.01, disp=hammer, disp_amp=0.001), 0.004)
    fd.add(capped_cone(bore_pt(0.288), bore_pt(0.804), 0.111, 0.091, rr=0.008, disp=hammer, disp_amp=0.001), 0.004)
    fd.add(capped_cone(bore_pt(0.8), bore_pt(S_MUZ), 0.089, 0.113, rr=0.008, disp=hammer, disp_amp=0.001), 0.006)
    # the breech: a dome behind the base ring, the cascabel's neck and button
    fd.add(Ellipsoid(bore_pt(S_BREECH + 0.004), (0.138, 0.138, 0.068), R=rot_from_axes(z_axis=GD)), 0.01)
    fd.add(RoundCone(bore_pt(-0.6), bore_pt(-0.655), 0.045, 0.026), 0.012)
    fd.add(_ring(-0.64, 0.032, 0.0085), 0.004)
    fd.add(Sphere(bore_pt(-0.69), 0.046), 0.008)
    # mouldings
    for s, R, r in ((-0.546, 0.146, 0.017), (-0.515, 0.145, 0.008), (-0.405, 0.143, 0.009), (-0.072, 0.137, 0.014),
                    (-0.046, 0.13, 0.007), (0.276, 0.121, 0.012), (0.306, 0.111, 0.008), (0.786, 0.092, 0.01),
                    (0.81, 0.089, 0.0065), (0.912, 0.113, 0.013)):
        fd.add(_ring(s, R, r), 0.003)
    # the bore
    fd.sub(Cylinder(bore_pt(0.7), BORE_R, 0.5, R=rot_from_axes(z_axis=GD)), 0.004)
    # the vent: a raised field on top of the breech, a little dished pan, the touch hole
    vc = bore_pt(S_VENT, barrel_r(S_VENT))
    Rv = rot_from_axes(z_axis=GU, y_axis=GD)
    fd.add(RoundBox(vc + GU * 0.003, (0.028, 0.03, 0.01), 0.006, R=Rv), 0.004)
    fd.sub(Sphere(vc + GU * 0.029, 0.019), 0.002)
    fd.sub(Cylinder(vc, 0.0075, 0.06, R=rot_from_axes(z_axis=GU)), 0.002)
    # the trunnions and their rimbases
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    fd.add(Cylinder(TRUN, 0.047, 2 * 0.236, rr=0.012, R=Rx), 0.006)
    for sx in (-1, 1):
        fd.add(Cylinder(TRUN + GX_ * (sx * 0.128), 0.066, 0.026, rr=0.008, R=Rx), 0.005)
    # two dolphins arching over the trunnions, heads toward the muzzle
    for sx in (-1, 1):
        th = sx * 0.34
        rad = GU * math.cos(th) + GX_ * math.sin(th)
        pts, rads = [], []
        for k in range(8):
            t = k / 7.0
            s = 0.012 + 0.16 * t
            h = 0.072 * math.sin(math.pi * t) ** 0.75 + 0.004
            pts.append(bore_pt(s) + rad * (barrel_r(s) + h - 0.008))
            rads.append(0.011 + 0.008 * t + 0.004 * math.sin(math.pi * t))
        fd.add(Chain(pts, rads, k=0.006), 0.006)
        hd = bore_pt(0.168) + rad * (barrel_r(0.168) + 0.012)
        fd.add(Ellipsoid(hd + GD * 0.012, (0.02, 0.026, 0.034), R=rot_from_axes(z_axis=GD, y_axis=rad)), 0.008)
        for e in (-1, 1):                                                     # eyes
            fd.add(Sphere(hd + GD * 0.026 + rad * 0.012 + np.cross(GD, rad) * (e * 0.014), 0.0055), 0.002, 5)
        tl = bore_pt(0.012) + rad * (barrel_r(0.012) + 0.01)
        for e in (-1, 1):                                                     # the tail's flukes
            fd.add(Ellipsoid(tl - GD * 0.02 + np.cross(GD, rad) * (e * 0.016), (0.018, 0.006, 0.026),
                             R=rot_from_axes(z_axis=norm(-GD + np.cross(GD, rad) * (e * 0.7)), y_axis=rad)), 0.006)
    # the crowned shield on the chase; the crown and the shield's cross gilt
    lo, hi = bore_pt(S_ARMS - 0.12) - 0.16, bore_pt(S_ARMS + 0.1) + 0.16
    fd.add(Func(lambda P: _arms(P, "shield"), np.minimum(lo, hi), np.maximum(lo, hi)), 0.002)
    fd.add(Func(lambda P: _arms(P, "cross"), np.minimum(lo, hi), np.maximum(lo, hi)), 0.002, 5)
    fd.add(Func(lambda P: _arms(P, "crown"), np.minimum(lo, hi), np.maximum(lo, hi)), 0.002, 5)
    return fd


# ======================================================================================= the carriage
# a cheek's side profile (y relative to the axle, z), counter-clockwise seen from +X
CHEEK = [(-0.25, 0.37), (0.14, 0.33), (0.8, 0.0), (0.85, 0.03), (0.85, 0.17), (0.52, 0.355), (0.45, 0.395), (0.43, 0.49),
         (0.29, 0.53), (0.27, 0.6), (0.08, 0.625), (-0.12, 0.632), (-0.25, 0.56)]


def poly2d(pts):
    V = np.array(pts, F)
    def fn(Yc, Zc):
        n = len(V)
        d = np.full(len(Yc), F(1e9))
        inside = np.zeros(len(Yc), bool)
        for i in range(n):
            a, b = V[i], V[(i + 1) % n]
            e = b - a
            wy, wz = Yc - a[0], Zc - a[1]
            t = np.clip((wy * e[0] + wz * e[1]) / F(e @ e), 0, 1)
            dy, dz = wy - e[0] * t, wz - e[1] * t
            d = np.minimum(d, dy * dy + dz * dz)
            cond = (a[1] > Zc) != (b[1] > Zc)
            if abs(e[1]) > 1e-9:
                xint = a[0] + (Zc - a[1]) * e[0] / e[1]
                inside ^= cond & (Yc < xint)
        return np.where(inside, -np.sqrt(d), np.sqrt(d))
    return fn


def cheek_func(sx, grow=0.0):
    xc = MX + sx * CHEEK_X
    p2 = poly2d(CHEEK)
    r = 0.014
    def fn(P):
        d2 = p2(P[:, 1] - F(AY), P[:, 2]) - F(grow)
        dx = np.abs(P[:, 0] - F(xc)) - F(CHEEK_T / 2 + grow)
        w0, w1 = d2 + F(r), dx + F(r)
        return np.minimum(np.maximum(w0, w1), F(0)) + np.sqrt(np.maximum(w0, 0) ** 2 + np.maximum(w1, 0) ** 2) - F(r)
    return Func(fn, (xc - 0.08, AY - 0.32, -0.05), (xc + 0.08, AY + 1.02, 0.7))


def cheek_mid_z(y):
    """The middle of a cheek's height at y (relative to the axle): where its bolts go."""
    top = [(-0.25, 0.5), (-0.12, 0.632), (0.08, 0.625), (0.27, 0.6), (0.29, 0.53), (0.43, 0.49), (0.45, 0.395), (0.52, 0.355), (0.85, 0.17)]
    bot = [(-0.25, 0.37), (0.14, 0.33), (0.8, 0.0), (0.85, 0.03)]
    zt = np.interp(y, [a for a, _ in top], [b for _, b in top])
    zb = np.interp(y, [a for a, _ in bot], [b for _, b in bot])
    return 0.5 * (zt + zb)


BED_TOP = 0.37


def carriage_field():
    """Two thick oak cheeks (wood, grain along Y: 0) stepped down from the trunnion beds to the trail, three transoms
    (grain across: 10), the axle-tree (10), the stool bed and the quoin under the breech; iron (6): cap squares over the
    trunnions, bands round the cheeks, bolts, rings, the trail's shoes, the axle's arms, washers and linchpins."""
    fd = Field("Carriage")
    for sx in (-1, 1):
        xc = MX + sx * CHEEK_X
        fd.add(cheek_func(sx), 0.0, 0)
        fd.sub(Cylinder(v3((xc, TY, TZ)), 0.05, 0.12, R=rot_from_axes(z_axis=(1, 0, 0))), 0.004)          # the trunnion bed
    # transoms, the axle-tree, the stool bed
    fd.add(RoundBox(v3((MX, AY - 0.17, 0.43)), (CHEEK_X - 0.03, 0.05, 0.06), 0.012, disp=_t.GRAIN, disp_amp=0.002), 0.006, GX)
    fd.add(RoundBox(v3((MX, AY + 0.44, 0.28)), (CHEEK_X - 0.03, 0.055, 0.06), 0.012, disp=_t.GRAIN, disp_amp=0.002), 0.006, GX)
    fd.add(RoundBox(v3((MX, AY + 0.765, 0.09)), (CHEEK_X - 0.03, 0.06, 0.075), 0.012, disp=_t.GRAIN, disp_amp=0.002), 0.006, GX)
    fd.add(RoundBox(v3((MX, AY, WR)), (CHEEK_X + 0.045, 0.06, 0.062), 0.014, disp=_t.GRAIN, disp_amp=0.002), 0.006, GX)
    fd.add(RoundBox(v3((MX, AY + 0.4, BED_TOP - 0.02)), (CHEEK_X - 0.03, 0.145, 0.02), 0.008, disp=_t.GRAIN, disp_amp=0.002), 0.004, 0)
    # the quoin: a wedge on the stool bed (its thin end forward), a round handle at its back
    def quoin(P):
        y, z = P[:, 1] - F(AY), P[:, 2]
        t = np.clip((y - F(0.3)) / F(0.24), 0, 1)
        top = F(0.415) + F(0.045) * t
        d = np.maximum(np.maximum(z - top, F(BED_TOP) - z), np.maximum(F(0.27) - y, y - F(0.545)))
        return np.maximum(d, np.abs(P[:, 0] - F(MX)) - F(0.09))
    fd.add(Func(quoin, (MX - 0.15, AY + 0.2, 0.3), (MX + 0.15, AY + 0.62, 0.52), disp=_t.GRAIN, disp_amp=0.0015), 0.006, GX)
    hq = v3((MX, AY + 0.545, 0.425))
    fd.add(RoundCone(hq, hq + v3((0, 0.06, 0.004)), 0.014, 0.013), 0.004, 0)
    fd.add(Sphere(hq + v3((0, 0.075, 0.005)), 0.022), 0.004, 0)
    # iron: cap squares over the trunnions, their bolts
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    for sx in (-1, 1):
        xc = MX + sx * CHEEK_X
        cap = Inter(Shell(Cylinder(v3((xc, TY, TZ)), 0.047, 0.2, R=Rx), 0.011, 0.012, pad=0.05),
                    Func(lambda P, xc=xc: np.maximum(F(TZ - 0.006) - P[:, 2], np.abs(P[:, 0] - F(xc)) - F(0.03)), (xc - 0.1, TY - 0.12, TZ - 0.1), (xc + 0.1, TY + 0.12, TZ + 0.12)), 0.003)
        fd.add(cap, 0.003, IRON)
        for dy in (-0.085, 0.085):
            fd.add(RoundBox(v3((xc, TY + dy, 0.633)), (0.03, 0.03, 0.006), 0.004), 0.003, IRON)
            fd.add(Sphere(v3((xc, TY + dy * 1.12, 0.643)), 0.011), 0.002, IRON)
        # bands round the cheek
        for yb in (0.2, 0.5, 0.71):
            fd.add(Inter(Shell(cheek_func(sx), 0.004, 0.008, pad=0.04), Func(lambda P, yb=yb: np.abs(P[:, 1] - F(AY + yb)) - F(0.02), (xc - 0.1, AY + yb - 0.1, -0.05), (xc + 0.1, AY + yb + 0.1, 0.7)), 0.002), 0.003, IRON)
        # bolt heads on the outer face, with square washers
        xo = xc + sx * (CHEEK_T / 2)
        for yb in (-0.17, 0.06, 0.35, 0.58):
            zb = cheek_mid_z(yb)
            fd.add(RoundBox(v3((xo + sx * 0.002, AY + yb, zb)), (0.004, 0.022, 0.022), 0.003), 0.002, IRON)
            fd.add(Ellipsoid(v3((xo + sx * 0.006, AY + yb, zb)), (0.008, 0.014, 0.014)), 0.002, IRON)
        # a ring on an eye bolt near the trail (for the handspike and the drag ropes)
        er = v3((xo + sx * 0.01, AY + 0.65, cheek_mid_z(0.65) + 0.02))
        fd.add(Sphere(er, 0.012), 0.002, IRON)
        fd.add(Torus(er + v3((sx * 0.012, 0, -0.032)), 0.03, 0.0065, R=rot_from_axes(z_axis=(0, 1, 0))), 0.002, IRON)
        # the trail's iron shoe
        fd.add(RoundBox(v3((xc, AY + 0.825, 0.03)), (CHEEK_T / 2 + 0.006, 0.035, 0.032), 0.008), 0.003, IRON)
        # the axle's arm, the washer and the linchpin outside the hub
        xa0, xa1 = MX + sx * (CHEEK_X + 0.035), MX + sx * (WX + 0.15)
        fd.add(Cylinder(v3(((xa0 + xa1) / 2, AY, WR)), 0.03, abs(xa1 - xa0), rr=0.006, R=Rx), 0.004, IRON)
        fd.add(Cylinder(v3((MX + sx * (WX + 0.128), AY, WR)), 0.046, 0.012, rr=0.004, R=Rx), 0.002, IRON)
        lp = v3((MX + sx * (WX + 0.143), AY, WR))
        fd.add(RoundCone(lp + v3((0, 0, 0.05)), lp - v3((0, 0, 0.042)), 0.007, 0.006), 0.002, IRON)
        fd.add(Torus(lp + v3((0, 0, 0.058)), 0.012, 0.004, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, IRON)
    return fd


# ======================================================================================= the wheels
N_SPOKES = 10


def _ring_x(c, r0, r1, hw, rr):
    C = c.astype(F)
    def fn(P):
        q = P - C
        rho = np.sqrt(q[:, 1] ** 2 + q[:, 2] ** 2)
        w0 = np.abs(rho - F((r0 + r1) / 2)) - F((r1 - r0) / 2) + F(rr)
        w1 = np.abs(q[:, 0]) - F(hw) + F(rr)
        return np.minimum(np.maximum(w0, w1), F(0)) + np.sqrt(np.maximum(w0, 0) ** 2 + np.maximum(w1, 0) ** 2) - F(rr)
    e = r1 + 0.02
    return Func(fn, c - v3((hw + 0.02, e, e)), c + v3((hw + 0.02, e, e)))


def hub_c(sx):
    return v3((MX + sx * WX, AY, WR))


def wheels_field():
    """Two big spoked wheels: oak felloes (0) and spokes (11) dished outward, a hub (10) with two iron hoops, an iron
    tyre (6) nailed on; the hubs painted crimson (5)."""
    fd = Field("Wheels")
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    grain = lambda P: F(0.0012) * NOISE(P * F(60))
    for sx in (-1, 1):
        c = hub_c(sx)
        fd.add(_ring_x(c, 0.372, WR, 0.031, 0.006), 0.0, IRON)                                   # the tyre
        for k in range(18):
            a = 2 * math.pi * (k + 0.25) / 18
            d = v3((0, math.cos(a), math.sin(a)))
            fd.add(Sphere(c + d * (WR - 0.001) + v3((((k % 2) * 2 - 1) * 0.014, 0, 0)), 0.0075), 0.002, IRON)
        fd.add(_ring_x(c + v3((sx * 0.003, 0, 0)), 0.3, 0.375, 0.026, 0.008), 0.004, 0)          # the felloes
        for k in range(5):                                                                     # their joints
            a = 2 * math.pi * (k + 0.5) / 5 + math.pi / N_SPOKES * 0.5
            d = v3((0, math.cos(a), math.sin(a)))
            fd.sub(RoundBox(c + d * 0.335, (0.035, 0.0022, 0.05), 0.001, R=rot_from_axes(z_axis=d, x_axis=(1, 0, 0))), 0.001)
        for k in range(N_SPOKES):                                                              # the spokes, dished
            a = 2 * math.pi * k / N_SPOKES + math.pi / N_SPOKES * 0.5
            d = v3((0, math.cos(a), math.sin(a)))
            fd.add(RoundCone(c + d * 0.07 - v3((sx * 0.02, 0, 0)), c + d * 0.31 + v3((sx * 0.006, 0, 0)), 0.022, 0.016,
                             disp=grain, disp_amp=0.0015), 0.008, GZ)
        # the hub: a fat barrel along the axle, iron hoops at its ends, crimson between
        fd.add(capped_cone(c - v3((sx * 0.085, 0, 0)), c + v3((sx * 0.015, 0, 0)), 0.07, 0.088, rr=0.014), 0.008, GX)
        fd.add(capped_cone(c + v3((sx * 0.01, 0, 0)), c + v3((sx * 0.12, 0, 0)), 0.088, 0.064, rr=0.014), 0.008, GX)
        for xx, R in ((-0.072, 0.073), (0.104, 0.068)):
            fd.add(Torus(c + v3((sx * xx, 0, 0)), R, 0.009, R=Rx), 0.002, IRON)
        fd.paint(Func(lambda P, c=c, sx=sx: np.maximum(np.abs((P[:, 0] - F(c[0])) * F(sx) - F(0.016)) - F(0.075),
                                                      np.sqrt((P[:, 1] - F(c[1])) ** 2 + (P[:, 2] - F(c[2])) ** 2) - F(0.095)),
                      c - 0.2, c + 0.2), CRIMSON)
    return fd


# ======================================================================================= the rammer and the round
RAM_LEN = 0.66              # the rammer's face -> the sponge's end
RAM_SP = 0.53               # where the sponge starts
_TYRE_Z = 0.55              # (at rest) the staff leans on the near wheel's tyre this high, just in front of the wheel
_tc = v3((MX - WX, AY - math.sqrt(WR ** 2 - (_TYRE_Z - WR) ** 2) - 0.021, _TYRE_Z))
R_AX = norm(v3((0.0, 0.17, 0.985)))
R_FOOT = _tc - R_AX * ((_TYRE_Z - 0.03) / R_AX[2])            # the rammer's head on the deck


def rammer_field():
    """A rammer-and-sponge staff: an ash staff (7) with a turned wooden rammer head at one end (7) and a fleece sponge
    (5) at the other, iron ferrules (6). At rest it leans against the front of the near wheel."""
    fd = Field("Rammer")
    A, f0 = R_AX, R_FOOT
    Ra = rot_from_axes(z_axis=A)
    grain = lambda P: F(0.0008) * NOISE(P * F(90))
    fd.add(Cylinder(f0 + A * 0.04, 0.046, 0.08, rr=0.012, R=Ra, disp=grain, disp_amp=0.001), 0.0, 7)       # the rammer head
    fd.add(RoundCone(f0 + A * 0.08, f0 + A * 0.1, 0.03, 0.022), 0.006, 7)
    fd.add(Cylinder(f0 + A * 0.1, 0.024, 0.02, rr=0.004, R=Ra), 0.003, 6)
    fd.add(RoundCone(f0 + A * 0.1, f0 + A * (RAM_SP - 0.01), 0.019, 0.019, disp=grain, disp_amp=0.001), 0.004, 7)
    fd.add(Cylinder(f0 + A * (RAM_SP - 0.005), 0.024, 0.02, rr=0.004, R=Ra), 0.003, 6)
    fleece = lambda P: F(0.004) * NOISE(P * F(55)) + F(0.003) * NOISE(P * F(120))
    fd.add(Cylinder(f0 + A * (RAM_SP + RAM_LEN) / 2, 0.05, RAM_LEN - RAM_SP, rr=0.022, R=Ra, disp=fleece, disp_amp=0.006), 0.008, 5)
    return fd


def round_frame():
    """Rest pose: the round's ball in his left palm (C), its cartridge standing off the palm (A, the palm's normal): he
    pushes it into the muzzle palm first, the cartridge leading."""
    wr, f, n, t = hand_frame("L")
    C = wr + f * 0.1 + n * (0.03 + ROUND_R * 0.9)
    return C, norm(n)


def round_field():
    """The round he loads: an iron ball (6) tied to a cloth cartridge of powder (5), the cord binding (0)."""
    fd = Field("Round")
    C, A = round_frame()
    fd.add(Sphere(C, ROUND_R, disp=lambda P: F(0.0008) * NOISE(P * F(70)), disp_amp=0.001), 0.0, 6)
    cloth = lambda P: F(0.0015) * NOISE(P * F(40))
    fd.add(Cylinder(C + A * 0.085, ROUND_R * 0.86, 0.1, rr=0.014, R=rot_from_axes(z_axis=A), disp=cloth, disp_amp=0.002), 0.006, 5)
    fd.add(Torus(C + A * 0.03, ROUND_R * 0.78, 0.005, R=rot_from_axes(z_axis=A)), 0.002, 0)
    fd.add(Ellipsoid(C + A * 0.142, (0.022, 0.022, 0.014), R=rot_from_axes(z_axis=A), disp=cloth, disp_amp=0.002), 0.006, 5)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.252, 1.616)), 0.06, 0.75)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.11, -0.15, 1.636)), 0.06, 0.6), (hp((sx * 0.18, 0.035, 1.664)), 0.055, 0.55),
                (J["elbow_" + sd] + v3((0, 0.025, 0)), 0.065, 0.3), (hp((sx * 0.05, -0.17, 1.8)), 0.09, 0.3)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.044, 0.0148, -0.0148, -0.044):
            pts.append((wr + f * 0.14 + t * o - n * 0.012, 0.032, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "cannon"
ROOT_NAME = "CannonHQ"
TEX_PREFIX = "cannon"
MAT_NAME = "CannonMat"
MESH_NAME = "Cannon"
BASE_MODULE = "cannon_base"
ANIM_MODULE = "anim_cannon"
PARTS = ["Skin", "Eyes", "Teeth", "Beard", "Cap", "Gold", "Shirt", "Jerkin", "Sash", "Breeches", "Leather", "Linstock",
         "Match", "Barrel", "Carriage", "Wheels", "Rammer", "Round"]
REGION_PARTS = ("Skin", "Shirt", "Jerkin", "Sash", "Leather", "Linstock", "Barrel", "Carriage", "Wheels", "Rammer", "Round")
CRIMSON_C = (0.55, 0.08, 0.08)                     # the Gunpowder Age's army colours (linear-ish albedo targets)
GOLD_C = (0.85, 0.62, 0.2)
OAK = {"wood": (0.5, 0.33, 0.19), "wood2": (0.36, 0.22, 0.12), "red": (0.62, 0.1, 0.08), "blue": (0.14, 0.27, 0.6),
       "metal": "iron"}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_GunnerSkin", "base": (0.8, 0.55, 0.4), "ruddy": (0.86, 0.45, 0.34), "lips": (0.64, 0.33, 0.28),
                      "brow": ((0.04, 0.035, 0.03), (0.12, 0.1, 0.09)),
                      "extra": ((LASH, (0.05, 0.035, 0.03), 0.5), (STUBBLE, (0.24, 0.18, 0.15), 0.6, 0.55),
                                (SOOT, (0.1, 0.09, 0.085), 0.9, 0.85))}),
    "Beard": ("hair", {"name": "HQ_GunnerBeard", "base": (0.06, 0.05, 0.045), "hi": (0.26, 0.22, 0.2), "low": (0.025, 0.02, 0.02),
                       "streak": (0.04, 0.032, 0.028), "tint": (0.12, 0.09, 0.08)}),
    "Cap": ("wool", {"name": "HQ_GunnerCap", "base": (0.7, 0.1, 0.07), "border": (0.7, 0.1, 0.07), "stripe": (0.5, 0.07, 0.05)}),
    "Gold": ("gold", {"name": "HQ_GunnerGold"}),
    "Shirt": ("linen", {"name": "HQ_GunnerShirt", "base": (0.93, 0.91, 0.84)}),
    "Jerkin": ("leather_dyed", {"name": "HQ_Jerkin", "base": (0.44, 0.27, 0.14), "dyed": (0.44, 0.27, 0.14)}),
    "Sash": ("wool", {"name": "HQ_Sash", "base": CRIMSON_C, "border": GOLD_C, "stripe": GOLD_C}),
    "Breeches": ("wool", {"name": "HQ_Breeches", "base": (0.17, 0.16, 0.19)}),
    "Leather": ("javelin_case", {"name": "HQ_GunnerLeather", "base": (0.27, 0.16, 0.09)}),
    "Linstock": ("javelin_shaft", {"name": "HQ_Linstock"}),
    "Match": ("glow_ball", {"name": "HQ_Match", "col": (1.0, 0.42, 0.1)}),
    "Barrel": ("bronze", {"name": "HQ_GunBronze", "base": (0.72, 0.46, 0.2), "patina": (0.27, 0.54, 0.44), "gilt": 5}),
    "Carriage": ("siege", dict(OAK, name="HQ_GunCarriage")),
    "Wheels": ("siege", dict(OAK, name="HQ_GunCarriage")),
    "Rammer": ("javelin_case", {"name": "HQ_Rammer", "base": (0.3, 0.18, 0.1)}),
    "Round": ("javelin_case", {"name": "HQ_Round", "base": (0.3, 0.18, 0.1)}),
}
GLOW = {"Match": ((1.0, 0.42, 0.1), 1.2, 0.5)}
LOW_TARGETS = {"Skin": 6400, "Teeth": 140, "Beard": 1700, "Cap": 1000, "Gold": 90, "Shirt": 1800, "Jerkin": 1300,
               "Sash": 1000, "Breeches": 1200, "Leather": 1800, "Linstock": 520, "Match": 40, "Barrel": 3400,
               "Carriage": 3600, "Wheels": 3600, "Rammer": 420, "Round": 220}
AO_EXCLUDE = ["Linstock", "Match", "Rammer", "Round", "Gold"]
# the gun is baked 6 m away from him: his rest pose (his left hand hangs by the breech) must leave no shadow on it
BAKE_APART = (["Barrel", "Carriage", "Wheels", "Rammer"], (6.0, 0.0, 0.0))
YAW_PIVOT = (0.72, -0.5, 0.0)                     # the tower turns about this point (keeps the gun and him on the base)


def prop_bones():
    return []                                        # the linstock, the rammer and the round are free bones (extra_bones)


KICK_P = v3((MX, TRAIL_Y, 0.0))                      # the carriage rocks about the trail's end as the gun kicks


def extra_bones():
    """The gun's bones (none of them deform him): carriage (rocking about the trail's end, rolled back by offsets), gun
    (the barrel, from the trunnions to the muzzle's face: bone_point ALONG 1.0 is the muzzle), wheel_a / wheel_b (the near
    and far wheels, turning about the axle); and his three free props, posed in the world: linstock (from his fist's grip
    along the staff), rammer (from its rammer face along the staff) and round (from the ball along the cartridge)."""
    G, T, Fv, B, f0 = linstock_frame()
    C, A = round_frame()
    return [
        ("carriage", KICK_P, KICK_P + v3((0, -0.4, 0)), None),
        ("gun", TRUN, MUZZLE, "carriage"),
        ("wheel_a", hub_c(-1), hub_c(-1) - v3((0.2, 0, 0)), "carriage"),
        ("wheel_b", hub_c(1), hub_c(1) + v3((0.2, 0, 0)), "carriage"),
        ("linstock", G, G + T * 0.3, None),
        ("rammer", R_FOOT, R_FOOT + R_AX * 0.3, None),
        ("round", C, C + A * 0.2, None),
    ]


def wheel_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"wheel_a" if v.co.x < MX else "wheel_b": 1.0})


def leather_weights(ob, skin_ob, arm):
    """Boots and strap from the body; the cartridge bag rigid with his hips."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "thigh.R", "thigh.L", "shin.R", "shin.L",
                                                       "foot.R", "foot.L"}, caps={"thigh.L": 0.3})
    groups = {}
    for v in ob.data.vertices:
        q = np.array(v.co) - SAT_C
        if abs(q[0]) < 0.1 and abs(q[1]) < 0.15 and -0.12 < q[2] < 0.14:
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"root": 0.75, "thigh.L": 0.25})


def sash_weights(ob, skin_ob, arm):
    """The band with the body; the knot and the hanging ends with his hips and right thigh."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"thigh.R", "thigh.L"}, caps={"thigh.R": 0.3, "thigh.L": 0.3})
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z < SASH_Z - 0.07 and p.x < -0.12:
            t = max(0.0, min(1.0, (SASH_Z - 0.07 - p.z) / 0.25))
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"root": 1.0 - 0.45 * t, "thigh.R": 0.45 * t})


def beard_weights(ob, skin_ob, arm):
    """The beard on his face with the head; the spade hanging onto his chest follows the neck and chest more and more
    toward its point (it lies on him when he turns his head)."""
    groups = {}
    z0 = 1.43
    for v in ob.data.vertices:
        t = max(0.0, min(1.0, (z0 - v.co.z) / 0.26))
        _blend_add(ob, groups, v.index, {"head": 1.0 - 0.75 * t, "neck": 0.35 * t, "chest": 0.4 * t})


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Beard": ("custom", beard_weights), "Cap": ("rigid", "head"),
        "Gold": ("rigid", "head"),
        "Shirt": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"}, None),
        "Jerkin": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"}, {"upperarm.R": 0.35, "upperarm.L": 0.35}),
        "Sash": ("custom", sash_weights),
        "Breeches": ("transfer", {"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Leather": ("custom", leather_weights),
        "Linstock": ("rigid", "linstock"), "Match": ("rigid", "linstock"),
        "Barrel": ("rigid", "gun"), "Carriage": ("rigid", "carriage"), "Wheels": ("custom", wheel_weights),
        "Rammer": ("rigid", "rammer"), "Round": ("rigid", "round"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.8
    if part in ("Carriage", "Wheels"):
        return 0.72
    if part == "Barrel":
        return 0.9
    if part in ("Rammer", "Round", "Linstock"):
        return 0.85
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Beard", beard_field(), 0.0022 if fine else 0.003),
        ("Cap", cap_field(), 0.0022 if fine else 0.003),
        ("Gold", gold_field(), 0.0012 if fine else 0.0015),
        ("Shirt", shirt_field(), 0.0026 if fine else 0.0036),
        ("Jerkin", jerkin_field(), 0.0026 if fine else 0.0036),
        ("Sash", sash_field(), 0.0024 if fine else 0.0034),
        ("Breeches", breeches_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Linstock", linstock_field(), 0.0016 if fine else 0.0022),
        ("Match", match_field(), 0.0012 if fine else 0.0015),
        ("Barrel", barrel_field(), 0.0026 if fine else 0.0036),
        ("Carriage", carriage_field(), 0.0032 if fine else 0.0045),
        ("Wheels", wheels_field(), 0.0026 if fine else 0.0036),
        ("Rammer", rammer_field(), 0.002 if fine else 0.0028),
        ("Round", round_field(), 0.0016 if fine else 0.0022),
    ]
