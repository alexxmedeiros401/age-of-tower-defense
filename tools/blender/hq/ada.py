"""Ada Gearwright, Inventor (HQ hero, Industrial Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A brilliant, cheerful young inventor: a round, freckled face, green eyes, a wide determined grin (both corners up, her
upper teeth showing, dimples), auburn hair swept up into a messy bun on the back of her head with a yellow pencil stuck
through it and a few loose wisps at her temples; brass goggles with green lenses pushed up on top of her head on a
black leather strap. A white linen blouse with a high collar (a navy ribbon bow at her throat), its sleeves rolled up
to her elbows; a navy corset-waistcoat over it (a deep V at the front, brass piping, two rows of brass buttons, a point
at the front of its hem); a maroon overskirt hitched up at the sides and open at the front, falling to her knees behind
(a bustle of gathers at the back, brass braid at its hem), over buff canvas trousers tucked into brown lace-up boots
(brass eyelets). A brown leather tool belt slung low on her hips: a big iron spanner tucked through a loop on her right
hip (its own bone: she draws it in the Ability), two screwdrivers and a small spanner in loops on her left hip, a pouch
behind. On her right forearm a brass mechanical gauntlet: riveted bands, a big brass gear on its outer side (it spins:
its own bone, `gear`) round a glowing amber core (its own emissive mesh on the `core` bone, swelled in the Ability), a
small pressure gauge, a copper pipe and a lever.

Her weapon, the steam bolt launcher (fired from the hip): a walnut pistol grip and short butt cap, a brass receiver, a steel
barrel with a brass muzzle, a copper pressure tank under it with a gauge, a walnut fore-grip for her left hand, and a
brass pan magazine of eight steel bolts lying flat on top (its own bone, `drum`, a child of the launcher's: it turns one
bolt on after each shot).

She has Kira's build (kira.py) with both hands made fists (brenna.py) and Wren's booted feet (wren.py), as Isla (isla.py).
The launcher rides its own parentless bone (`launcher`: the grip's middle to the muzzle), the spanner its own (`wrench`:
the grip's middle toward its jaw; tucked in her belt at rest). The launcher's rest placement floats before her right hip,
pointing ahead (-Y); the clips pose it in world space and put her fists on its grips (anim_ada.py)."""
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
from isla import _seg_dist_np, _seg_dist, _ringlet, _button, boots_weights as _isla_boots_weights

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, FRECKLE, LASH = 0, 1, 2, 3, 4, 5, 6, 8
IRIS = ((0.12, 0.32, 0.12), (0.44, 0.66, 0.24))           # green eyes (prep.paint_eyes)


class ScaledField(Field):
    """A field scaled by `s` about the point `c` (labels and painted regions kept): the props are drawn at one size and
    shipped at another."""

    def __init__(self, inner, c, s):
        self.name, self.inner, self.c, self.s = inner.name, inner, v3(c), float(s)
        self.ops = []

    def _in(self, P):
        return ((np.asarray(P, F) - self.c.astype(F)) / F(self.s) + self.c.astype(F)).astype(F)

    def bounds(self):
        lo, hi = self.inner.bounds()
        return self.c + (lo - self.c) * self.s, self.c + (hi - self.c) * self.s

    def eval(self, P, labels=False, margin=0.0):
        r = self.inner.eval(self._in(P), labels=labels, margin=margin / self.s)
        if labels:
            return r[0] * F(self.s), r[1]
        return r * F(self.s)

    def paint_dist(self, P, band=0.004):
        return {k: v * F(self.s) for k, v in self.inner.paint_dist(self._in(P), band / self.s).items()}


# ======================================================================================= head
def head(fd):
    """Kira's face made younger and rounder: soft apple cheeks lifted by a wide grin, both corners of the mouth drawn up,
    the lips parted on her upper teeth, dimples; arched brows drawn a touch down at their inner ends (determined); a small
    upturned nose; freckles across her nose and cheeks."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.062, 1.594), (0.139, 0.13, 0.124)), 0.07, SKIN)                          # a soft young jaw
    fd.add(E((0, -0.127, 1.508), (0.069, 0.061, 0.059)), 0.05, SKIN)                         # a small round chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.106, -0.12, 1.634), 0.04), 0.05, SKIN)                                # cheekbones
        fd.add(S((sx * 0.112, -0.05, 1.566), 0.043), 0.05, SKIN)
        fd.add(S((sx * 0.076, -0.148, 1.602), 0.025), 0.03, SKIN)                              # apple cheeks (the grin)
        pts = [hp((sx * 0.15, -0.06, 1.744)), hp((sx * 0.115, -0.128, 1.75)), hp((sx * 0.062, -0.162, 1.748))]
        fd.add(Chain(pts, [hr(0.01), hr(0.014), hr(0.012)], k=hr(0.02)), hr(0.03), SKIN)
    # brows: arched, a little drawn down at their inner ends
    for sx in (-1, 1):
        pts = [hp((sx * 0.034, -0.202, 1.769)), hp((sx * 0.07, -0.198, 1.787)), hp((sx * 0.11, -0.175, 1.794)),
               hp((sx * 0.148, -0.135, 1.781))]
        fd.add(Chain([p + v3((0, 0.009, 0)) for p in pts], [hr(0.0042), hr(0.0056), hr(0.0048), hr(0.0022)], k=hr(0.006)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.0105), hr(0.0125), hr(0.0105), hr(0.0055)], k=hr(0.01)), BROW)
    # eyes wide open, lashes on the upper lids flicked out at the corners; the lower lids lifted by the grin
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, hr(0.0245))), (sx * 0.18, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0046)), Plane(ec + v3((0, 0, -hr(0.0235))), (sx * -0.2, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.008)), Plane(ec + v3((0, 0, hr(0.0205))), (sx * 0.18, 0.05, -1.0)), hr(0.002)), LASH)
        flick = ec + v3((sx * hr(0.04), -hr(0.01), hr(0.016)))
        fd.add(RoundCone(flick, flick + v3((sx * hr(0.013), hr(0.006), hr(0.006))), hr(0.0042), hr(0.0015)), hr(0.004), LASH)
    # a small, upturned nose
    fd.add(RoundCone(hp((0, -0.178, 1.722)), hp((0, -0.212, 1.652)), hr(0.0105), hr(0.0145)), hr(0.016), SKIN)
    fd.add(S((0, -0.213, 1.641), 0.0185), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.022, -0.196, 1.627), 0.013), hr(0.01), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.012, -0.209, 1.616)), v3((0.007, 0.009, 0.005)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the grin: both corners drawn up into the cheeks, the lips parted on her upper teeth
    slot = [hp((-0.068, -0.153, 1.58)), hp((-0.038, -0.184, 1.553)), hp((0, -0.195, 1.544)), hp((0.038, -0.184, 1.553)),
            hp((0.068, -0.153, 1.58))]
    fd.sub(Chain(slot, [hr(0.0024), hr(0.0031), hr(0.0034), hr(0.0031), hr(0.0024)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0034), hr(0.0046), hr(0.005), hr(0.0046), hr(0.0034)], k=hr(0.004)), MOUTH)
    for sx in (-1, 1):
        fd.add(S((sx * 0.075, -0.149, 1.592), 0.011), hr(0.01), SKIN)                         # the grin's cheeks
    up_lip = [(-0.066, -0.152, 1.584), (-0.036, -0.179, 1.565), (-0.011, -0.186, 1.563), (0.011, -0.186, 1.563),
              (0.036, -0.179, 1.565), (0.066, -0.152, 1.584)]
    lo_lip = [(-0.058, -0.157, 1.564), (-0.03, -0.178, 1.534), (0.0, -0.184, 1.526), (0.03, -0.178, 1.534),
              (0.058, -0.157, 1.564)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.0034), hr(0.0062), hr(0.0068), hr(0.0068), hr(0.0062), hr(0.0034)], k=hr(0.006)), hr(0.009), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.0042), hr(0.0078), hr(0.0086), hr(0.0078), hr(0.0042)], k=hr(0.007)), hr(0.009), LIP)
    gap = Inter(Ellipsoid(hp((0.0, -0.19, 1.548)), v3((0.052, 0.032, 0.0115)) * HS),
                Func(lambda P: (F(1.5395) + F(3.2) * hinv(P)[:, 0] ** 2 - hinv(P)[:, 2]) * F(HS), (-1, -1, 1.3), (1, 1, 1.8)), hr(0.002))
    fd.sub(gap, hr(0.003))                                                               # (its lower edge curving up: a smile)
    fd.paint(Ellipsoid(hp((0.0, -0.18, 1.549)), v3((0.056, 0.03, 0.014)) * HS), MOUTH)
    for sx in (-1, 1):
        fd.sub(S((sx * 0.08, -0.15, 1.584), 0.0055), hr(0.006))                               # dimples
        fd.add(Ellipsoid(hp((sx * 0.174, 0.035, 1.66)), v3((0.024, 0.043, 0.054)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
    # freckles across her nose and cheeks
    rs = np.random.RandomState(12)
    for i in range(40):
        x = rs.uniform(-0.12, 0.12)
        z = 1.632 + rs.uniform(-0.026, 0.026) - 0.16 * x * x
        if abs(x) < 0.022 and z < 1.636:
            continue
        r = rs.uniform(0.0024, 0.0036)
        fd.paint(hstripe((x, z), (x + 0.001, z), r, r, y0=-0.5, y1=-0.08), FRECKLE)


def teeth_field():
    """Her upper teeth, showing in the grin."""
    fd = Field("Teeth")
    pts = [hp((-0.04, -0.165, 1.558)), hp((-0.014, -0.179, 1.551)), hp((0.014, -0.179, 1.551)), hp((0.04, -0.165, 1.558))]
    fd.add(Chain(pts, [hr(0.0092)] * 4, k=hr(0.004)), 0.0)
    return fd


def arm_prims(side):
    """The arm's shapes (as body_parts builds them), for hulls."""
    sx = -1 if side == "R" else 1
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    return [(deltoid(side), 0.05), (upper_arm(side), 0.045),
            (Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.067, 0.07, 0.102), R=rot_from_axes(z_axis=el - sh)), 0.035),
            (_forearm(side), 0.03),
            (Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.071, 0.063, 0.11), R=rot_from_axes(z_axis=wr - el)), 0.035),
            (Sphere(el + v3((0, 0.022, 0)), 0.044), 0.025)]


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


# ======================================================================================= hair: swept up into a messy bun
BUN = hp((0.0, 0.17, 1.912))             # the bun, high on the back of her head
BUN_AX = norm(BUN - HEAD_C)
EAR_C = {sx: hp((sx * 0.174, 0.035, 1.66)) for sx in (-1, 1)}


def hairline(P):
    """> 0 below her hairline (design units): her forehead, in front of her ears, round the nape."""
    Q = hinv(P)
    y = Q[:, 1]
    zl = F(1.852) - F(0.1) * smoothstep(-0.14, -0.06, y) - F(0.17) * smoothstep(0.075, 0.14, y)
    return zl - Q[:, 2]


def hair_region(P):
    """> 0 where there is no hair: below the hairline, round her ears."""
    ears = None
    for sx in (-1, 1):
        q = P - EAR_C[sx].astype(F)
        e = F(hr(0.062)) - np.sqrt((q * q).sum(1))
        ears = e if ears is None else np.maximum(ears, e)
    return np.maximum(hairline(P) * F(HS), ears)


def _combed(P):
    """Grooves running up from the hairline to the bun, a little messy."""
    e1 = norm(np.cross(BUN_AX, v3((1, 0, 0))))
    e2 = np.cross(BUN_AX, e1)
    q = P - HEAD_C.astype(F)
    a = np.arctan2(q @ e2.astype(F), q @ e1.astype(F))
    return F(0.0022) * np.abs(np.sin(a * F(11) + F(1.6) * NOISE(P * F(7)))) + F(0.0012) * NOISE(P * F(45)) + F(0.002) * NOISE(P * F(12))


def hair_field(seed=4):
    """Auburn hair drawn up from her face and nape into a messy bun (loops of hair wound round a knot, a few ends sticking
    out); a wisp at each temple, two at the nape."""
    rng = np.random.RandomState(seed)
    fd = Field("Hair")
    head = Ellipsoid(HEAD_C, HEAD_RAD)
    def cap(P):
        d = head(P)
        h = -hairline(P)                                     # how far above the hairline (design units)
        th = F(0.005) + F(0.019) * smoothstep(0.0, 0.035, h)  # thinning to the hairline (no helmet edge)
        return np.abs(d - (F(0.003) + th * F(0.5))) - th * F(0.5) + _combed(P)
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    fd.add(Inter(Func(cap, lo, hi), Func(hair_region, lo, hi), 0.004), 0.0)
    # the bun: a knot with loops of hair wound round it
    R = rot_from_axes(z_axis=BUN_AX)
    grooves = lambda P: F(0.0025) * np.abs(np.sin((P @ np.array([1.0, 0.6, 0.3], F)) * F(150))) + F(0.0015) * NOISE(P * F(45))
    fd.add(Ellipsoid(BUN - BUN_AX * 0.008, v3((0.07, 0.066, 0.05)) * HS, R=R, disp=grooves, disp_amp=0.003), 0.02)
    for k in range(6):
        tilt = rng.uniform(-0.6, 0.6, 2)
        Rk = R @ euler(tilt[0], tilt[1], rng.uniform(0, 6.28))
        r0 = hr(0.062) * rng.uniform(0.85, 1.05)
        a0 = rng.uniform(0, 6.28)
        span = rng.uniform(3.4, 4.6)
        pts, ns = [], []
        for i in range(7):
            a = a0 + span * i / 6
            loc = v3((math.cos(a) * r0, math.sin(a) * r0, 0.012 * math.sin(a * 1.7)))
            pts.append(BUN + Rk @ loc)
            ns.append(Rk @ norm(loc + v3((0, 0, 0.02))))
        fd.add(Lock(pts, [0.034, 0.04, 0.042, 0.04, 0.038, 0.033, 0.024], [0.018, 0.021, 0.022, 0.021, 0.019, 0.016, 0.011], ns, k=0.008,
                    disp=grooves, disp_amp=0.003), 0.008)
    for k in range(4):                                       # ends sticking out of the bun
        d = norm(BUN_AX * 0.4 + v3((rng.uniform(-1, 1), rng.uniform(-0.6, 0.8), rng.uniform(0.2, 1.0))))
        side = norm(np.cross(d, BUN_AX))
        p0 = BUN + d * hr(0.056)
        L = rng.uniform(0.05, 0.08)
        pts = [p0, p0 + d * L * 0.5 + side * 0.008, p0 + d * L + side * 0.02 + v3((0, 0, -0.01))]
        fd.add(Lock(pts, [0.016, 0.011, 0.004], [0.007, 0.005, 0.002], [side] * 3, k=0.004, disp=grooves, disp_amp=0.002), 0.005)
    # loose wisps at her temples (in front of her ears) and at the nape
    for sx in (-1, 1):
        for j, (dy, L) in enumerate(((-0.08, 0.15), (-0.06, 0.12))):
            top = hp((sx * 0.148, dy, 1.775))
            pts = [top, top + v3((sx * 0.016, -0.012, -L * 0.45)), top + v3((sx * 0.008, -0.022, -L * 0.85)), top + v3((sx * -0.004, -0.016, -L))]
            nrm = v3((sx, -0.3, 0.0))
            fd.add(Lock(pts, [0.016, 0.017, 0.012, 0.004], [0.006, 0.006, 0.005, 0.002], [nrm] * 4, k=0.004,
                        disp=lambda P: F(0.0012) * NOISE(P * F(80)), disp_amp=0.0015), 0.004)
        top = hp((sx * 0.055, 0.17, 1.605))
        bot = hp((sx * 0.068, 0.183, 1.555))
        _ringlet(fd, [top, bot], 0.007, 0.0065, 1.2, rng.uniform(0, 6.28))
    return fd


# the pencil through the bun: its sharpened tip out to her left, the eraser to her right
PENCIL_D = norm(v3((1.0, -0.18, 0.32)))
PENCIL_A = BUN - PENCIL_D * 0.115       # the eraser's end
PENCIL_B = BUN + PENCIL_D * 0.135       # the point


def pencil_field():
    """A yellow-painted pencil (label 5) of pale cedar (0) sharpened to a graphite point (6), a metal ferrule (6) and a pink
    eraser (7) at its other end."""
    fd = Field("Pencil")
    d = PENCIL_D
    R = rot_from_axes(z_axis=d)
    L = float(np.linalg.norm(PENCIL_B - PENCIL_A))
    body0, body1 = PENCIL_A + d * 0.022, PENCIL_B - d * 0.028
    def hexa(P, a=body0, b=body1):
        q = (P - a.astype(F)) @ R.astype(F)
        ang = np.arctan2(q[:, 1], q[:, 0])
        rr = F(0.0088) / np.cos(np.mod(ang + F(math.pi / 6), F(math.pi / 3)) - F(math.pi / 6))   # a hexagon
        Lb = float(np.linalg.norm(b - a))
        return np.maximum(np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - rr * F(0.97), np.maximum(-q[:, 2], q[:, 2] - F(Lb)))
    fd.add(Func(hexa, np.minimum(body0, body1) - 0.02, np.maximum(body0, body1) + 0.02), 0.0, 5)
    fd.add(RoundCone(body1 - d * 0.002, PENCIL_B, 0.0083, 0.0013), 0.002, 0)                # the sharpened wood
    fd.paint(Sphere(PENCIL_B, 0.008), 6)                                                     # graphite
    fd.add(Cylinder(PENCIL_A + d * 0.014, 0.0094, 0.016, rr=0.002, R=R), 0.002, 6)          # the ferrule
    fd.add(Cylinder(PENCIL_A + d * 0.004, 0.0088, 0.012, rr=0.0042, R=R), 0.002, 7)         # the eraser
    return fd


# ======================================================================================= goggles
GOG_F = v3((0.0, -0.1, 1.885))           # the strap's plane (design units): across the top of her head ...
GOG_B = v3((0.0, 0.215, 1.66))           # ... and round under the bun at the back
_GOG_N = norm(v3((0.0, -(GOG_B[2] - GOG_F[2]) / (GOG_B[1] - GOG_F[1]), 1.0)))
GOG_X = 0.058                            # the cups' distance from the middle (design)
CUP_R, CUP_H = 0.037, 0.03


def gog_d(P):
    return (hinv(P) - GOG_F.astype(F)) @ _GOG_N.astype(F)


def cup_frames():
    """(centre of the cup's base, its axis) of the two goggle cups, lying on top of her hair at the front of her head."""
    out = []
    for sx in (-1, 1):
        best = None
        for y in np.linspace(-0.2, 0.05, 400):
            z = GOG_F[2] + (y - GOG_F[1]) * (GOG_B[2] - GOG_F[2]) / (GOG_B[1] - GOG_F[1])
            p = hp((sx * GOG_X, y, z))
            q = (p - HEAD_C) / HEAD_RAD
            if q @ q <= 1.0:
                best = p
                break
        g = (best - HEAD_C) / (HEAD_RAD ** 2)
        n = norm(g)
        out.append((best + n * 0.03, n))
    return out


def goggles_field():
    """Brass goggle cups (label 6) on a black leather strap (5) round her head; a brass bridge between them, rivets."""
    fd = Field("Goggles")
    head = Ellipsoid(HEAD_C, HEAD_RAD)
    lo, hi = HEAD_C - 0.3, HEAD_C + 0.3
    fd.add(Inter(Shell(head, 0.03, 0.0075, pad=0.05), Func(lambda P: np.abs(gog_d(P)) * F(HS) - F(0.013), lo, hi), 0.002), 0.0, 5)
    frames = cup_frames()
    for c, n in frames:
        R = rot_from_axes(z_axis=n)
        fd.add(Cylinder(c + n * (CUP_H * 0.5), CUP_R, CUP_H, rr=0.008, R=R), 0.004, 6)
        fd.add(Torus(c + n * (CUP_H - 0.002), CUP_R - 0.004, 0.0055, R=R), 0.003, 6)             # the rim
        fd.sub(Cylinder(c + n * (CUP_H + 0.004), CUP_R - 0.009, 0.014, rr=0.002, R=R), 0.002)    # (the lens sits in it)
        side = norm(np.cross(n, v3((0, 1, 0))))
        for k in range(6):
            a = 2 * math.pi * k / 6
            o = (side * math.cos(a) + np.cross(n, side) * math.sin(a)) * (CUP_R + 0.001)
            fd.add(Sphere(c + n * (CUP_H * 0.45) + o, 0.0045), 0.002, 6)                       # rivets round the cup
    (c0, n0), (c1, n1) = frames
    m = (c0 + c1) / 2 + (n0 + n1) * 0.5 * 0.022
    fd.add(Chain([c0 + n0 * 0.02 + norm(c1 - c0) * CUP_R * 0.8, m, c1 + n1 * 0.02 - norm(c1 - c0) * CUP_R * 0.8], [0.007, 0.006, 0.007], k=0.004), 0.004, 6)
    return fd


def lenses_field():
    """Green glass lenses in the cups."""
    fd = Field("Lenses")
    for c, n in cup_frames():
        R = rot_from_axes(z_axis=n)
        fd.add(Inter(Sphere(c + n * (CUP_H - 0.03), 0.042), Cylinder(c + n * CUP_H, CUP_R - 0.008, 0.03, R=R), 0.002), 0.0)
    return fd


# ======================================================================================= the blouse
SLEEVE_T = 0.06                    # the rolled sleeves' end: this far down the forearm from the elbow (fraction of el -> wr)
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
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    return el + ax * (float(np.linalg.norm(wr - el)) * SLEEVE_T), ax


def sleeve_cut(P):
    """> 0 past the rolled sleeves' ends (only near the forearms)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        c, ax = sleeve_end(side)
        wr = J["wrist_" + side]
        along = (P - c.astype(F)) @ ax.astype(F)
        near = _seg_dist_np(P, c - ax * 0.12, wr + ax * 0.25) < F(0.13)
        out = np.maximum(out, np.where(near, along, F(-1.0)))
    return out


def neck_line(P, base=1.43):
    """> 0 above a neckline round her neck only (lifted clear of the shoulders, so it opens no hole on them)."""
    ax = np.abs(P[:, 0])
    return P[:, 2] - (F(base) + F(0.075) * smoothstep(-0.04, 0.12, P[:, 1]) + F(0.3) * smoothstep(0.12, 0.19, ax))


def blouse_field():
    """White linen (label 0): tucked in at her waist, fine pin-tucks down its front, the sleeves full and rolled up to just
    below her elbows (a thick roll of cloth), a high collar round her throat."""
    fd = Field("Blouse")
    hull = blouse_hull()
    def wr_(P):
        front = smoothstep(0.0, -0.08, P[:, 1]) * smoothstep(0.98, 1.06, P[:, 2]) * smoothstep(0.14, 0.08, np.abs(P[:, 0]))
        return (F(0.0013) * NOISE(P * F(28)) + F(0.0012) * np.abs(np.sin(P[:, 0] * F(160))) * front
                + F(0.0016) * np.sin(P[:, 2] * F(55) + F(2) * NOISE(P * F(5))) * smoothstep(0.24, 0.36, np.abs(P[:, 0])))
    def cut(P):
        return np.maximum(np.maximum(F(0.88) - P[:, 2], neck_line(P)), sleeve_cut(P))
    fd.add(Inter(Shell(hull, BL_OFF, BL_T, pad=0.1, disp=wr_, disp_amp=0.003), Func(cut, (-1, -0.6, 0.7), (1, 0.6, 1.7)), 0.004), 0.0)
    # the rolled sleeves: a thick roll of cloth round each arm at the sleeve's end
    for side in ("R", "L"):
        c, ax = sleeve_end(side)
        sx = -1 if side == "R" else 1
        arm = Field("Arm" + side)
        for p, k in arm_prims(side):
            arm.add(p, k)
        def band(P, c=c, ax=ax):
            s = (P - c.astype(F)) @ ax.astype(F)
            near = _seg_dist_np(P, c - ax * 0.1, c + ax * 0.1) < F(0.14)
            return np.where(near, np.abs(s + F(0.012)) - F(0.021), F(1.0))
        roll = lambda P: F(0.003) * np.sin(np.arctan2(P[:, 2], P[:, 1]) * F(7) + F(2) * NOISE(P * F(12))) + F(0.001) * NOISE(P * F(40))
        fd.add(Inter(Shell(arm, BL_OFF + 0.014, 0.024, pad=0.06, disp=roll, disp_amp=0.004), Func(band, c - 0.2, c + 0.2), 0.008), 0.006)
    # the high collar round her throat
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    fd.add(Inter(Shell(nk, 0.012, 0.011, pad=0.06), Func(lambda P: np.abs(P[:, 2] - F(1.452)) - F(0.03), (-0.3, -0.3, 1.3), (0.3, 0.3, 1.6)), 0.004), 0.006)
    return fd


# ======================================================================================= the corset-waistcoat
WC_OFF, WC_T = 0.03, 0.014
WC_OUT = WC_OFF + WC_T / 2


_NECK = neck_prim()


def wc_hull():
    b = Field("WcHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    return b


def wc_w(z):
    """Half width of the waistcoat's V at height z: closed (buttoned) below 1.0, opening up to her collarbones."""
    return F(0.012) + F(0.105) * smoothstep(1.0, 1.36, z)


def wc_hem(P):
    """The hem: a point at the front middle dipping over the trousers."""
    ax = np.abs(P[:, 0])
    return F(0.86) - F(0.055) * (F(1) - smoothstep(0.0, 0.12, ax)) * smoothstep(0.0, -0.08, P[:, 1])


def wc_cut(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    front = np.where(y < F(0.0), wc_w(z) - ax, F(-1.0))
    arm = ax - (F(0.205) + F(0.25) * smoothstep(1.13, 0.99, z))           # the armholes
    neck = F(0.022) - _NECK(P)                                            # (clear of her neck and the blouse's collar)
    return np.maximum(np.maximum(np.maximum(neck_line(P, 1.425), front), np.maximum(arm, neck)), wc_hem(P) - z)


def wc_seams(P):
    """Princess seams (the corset's boning) pressed into the cloth, and a fine twill."""
    x = P[:, 0]
    s = None
    for x0 in (-0.15, -0.075, 0.075, 0.15):
        e = np.exp(-((x - F(x0)) / F(0.004)) ** 2)
        s = e if s is None else s + e
    return F(0.0018) * s * smoothstep(1.24, 1.1, P[:, 2]) + F(0.0008) * NOISE(P * F(40))


def corset_field():
    """Navy wool (label 0) with brass braid piping (5) along its V, armholes and hem; shaped to her waist, boned in princess
    seams; a navy ribbon bow (0) at her throat on the blouse's collar."""
    fd = Field("Corset")
    hull = wc_hull()
    lo, hi = (-0.6, -0.5, 0.7), (0.6, 0.5, 1.6)
    hlo, hhi = hull.bounds()
    def cloth(P):
        d = hull.eval(P, margin=0.07)
        return np.abs(d - F(WC_OFF)) - F(WC_T * 0.5) + wc_seams(P)
    fd.add(Inter(Func(cloth, hlo - 0.06, hhi + 0.06), Func(wc_cut, lo, hi), 0.004), 0.0)
    # the piping: a raised cord along every edge (the V, the armholes, the neck, the hem)
    def edge(P):
        e = -wc_cut(P)                                     # > 0 on the cloth: the distance from its edge (roughly)
        return np.maximum(np.abs(e - F(0.007)) - F(0.0075), np.abs(hull.eval(P, margin=0.07) - F(WC_OUT + 0.002)) - F(0.006))
    fd.add(Func(edge, lo, hi), 0.003, 5)
    # the bow at her throat
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    h, ok = ray_hit(Func(lambda P: nk.eval(P, margin=0.1) - F(0.012), (-0.3, -0.5, 1.3), (0.3, 0.3, 1.6)), [v3((0.0, -0.4, 1.428))], [v3((0, 1, 0))], tmax=0.6)
    knot = h[0] if ok[0] else v3((0.0, -0.075, 1.428))
    fold = lambda P: F(0.0015) * np.sin(P[:, 2] * F(260)) + F(0.0008) * NOISE(P * F(50))
    fd.add(Ellipsoid(knot + v3((0, -0.006, 0)), (0.016, 0.012, 0.014), disp=fold, disp_amp=0.002), 0.004)
    for sx in (-1, 1):
        lp = [knot + v3((sx * 0.01, -0.006, 0.002)), knot + v3((sx * 0.032, -0.008, 0.014)), knot + v3((sx * 0.052, -0.002, 0.004)),
              knot + v3((sx * 0.04, -0.004, -0.01)), knot + v3((sx * 0.014, -0.008, -0.004))]
        fd.add(Lock(lp, [0.012, 0.018, 0.016, 0.014, 0.01], [0.004, 0.004, 0.004, 0.004, 0.004], [v3((0, -1, 0.1))] * 5, k=0.005, disp=fold, disp_amp=0.002), 0.004)
        tl = [knot + v3((sx * 0.006, -0.008, -0.008)), knot + v3((sx * 0.018, -0.012, -0.04)), knot + v3((sx * 0.028, -0.012, -0.068))]
        fd.add(Lock(tl, [0.011, 0.012, 0.013], [0.0035, 0.0035, 0.003], [v3((0, -1, 0))] * 3, k=0.004, disp=fold, disp_amp=0.002), 0.004)
    return fd


def wc_button_points():
    hull = wc_hull()
    out = []
    for sx in (-1, 1):
        for z in (0.92, 0.985, 1.05, 1.115, 1.18):
            x = sx * (float(wc_w(np.array([z], F))[0]) + 0.03)
            h, ok = ray_hit(Func(lambda P: hull.eval(P, margin=0.1) - F(WC_OUT - 0.002), (-1, -1, 0.7), (1, 1, 1.6)),
                            [v3((x, -0.6, z))], [v3((0, 1, 0))], tmax=0.8)
            if ok[0]:
                out.append(h[0])
    return out


# ======================================================================================= the overskirt and trousers
SK_OFF, SK_T = 0.045, 0.012
SK_OUT = SK_OFF + SK_T / 2
SKIRT_Z = (0.92, 0.4)                    # the skirts' flare: from the waist to below her knees
SKIRT_RX = (0.19, 0.31)
SKIRT_RY = (0.155, 0.27)
SKIRT_YC = (0.04, 0.09)
SKIRT_LO, SKIRT_HI = (-0.34, -0.22, 0.38), (0.34, 0.39, 0.94)
SK_OPEN = 0.95                           # the front opening's half angle (radians from her front)


def skirt_sd(P):
    z = P[:, 2]
    t = np.clip((F(SKIRT_Z[0]) - z) / F(SKIRT_Z[0] - SKIRT_Z[1]), 0, 1)
    rx = F(SKIRT_RX[0]) + F(SKIRT_RX[1] - SKIRT_RX[0]) * t
    ry = F(SKIRT_RY[0]) + F(SKIRT_RY[1] - SKIRT_RY[0]) * t
    yc = F(SKIRT_YC[0]) + F(SKIRT_YC[1] - SKIRT_YC[0]) * t
    q = np.sqrt((P[:, 0] / rx) ** 2 + ((P[:, 1] - yc) / ry) ** 2)
    d_side = (q - F(1.0)) * np.minimum(rx, ry)
    d_z = np.maximum(z - F(SKIRT_Z[0]), F(SKIRT_Z[1]) - z)
    return np.maximum(d_side, d_z)


def skirt_hull():
    b = Field("SkirtHull")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(Func(skirt_sd, SKIRT_LO, SKIRT_HI), 0.06)
    b.add(Ellipsoid((0.0, 0.17, 0.83), (0.17, 0.11, 0.1)), 0.06)          # the bustle
    return b


def sk_angle(P):
    return np.arctan2(P[:, 0], -(P[:, 1] - F(0.06)))


def sk_hem(P):
    """The hem: at her knees behind, hitched up toward the front edges."""
    a = np.abs(sk_angle(P))
    return F(0.43) + F(0.25) * smoothstep(2.5, 1.05, a) + F(0.012) * np.sin(sk_angle(P) * F(11)) + F(0.006) * NOISE(P * F(6))


def sk_cut(P):
    a = np.abs(sk_angle(P))
    top = F(BELT_Z + 0.012) + F(BELT_TILT) * P[:, 0]                      # (under the belt all round)
    return np.maximum(np.maximum(P[:, 2] - top, F(SK_OPEN) - a), sk_hem(P) - P[:, 2])


def sk_folds(P):
    a = sk_angle(P)
    low = smoothstep(0.86, 0.5, P[:, 2])
    hitch = np.exp(-((np.abs(a) - F(1.2)) / F(0.35)) ** 2) * smoothstep(0.85, 0.65, P[:, 2])      # gathered where it is hitched
    bust = np.exp(-((np.abs(a) - F(math.pi)) / F(0.7)) ** 2) * np.exp(-((P[:, 2] - F(0.8)) / F(0.06)) ** 2)
    return (F(0.009) * np.sin(a * F(10) + F(0.8) * NOISE(P * F(3))) * low + F(0.006) * np.sin(a * F(22)) * hitch
            + F(0.006) * np.sin(P[:, 2] * F(70)) * bust + F(0.0012) * NOISE(P * F(28)))


def skirt_field():
    """Maroon wool (label 0): gathered at her waist under the belt, open at the front, hitched up at the sides in gathers and
    falling to her knees behind over a bustle; brass braid (5) along its hem and front edges."""
    fd = Field("Skirt")
    hull = skirt_hull()
    hlo, hhi = hull.bounds()
    def cloth(P):
        d = hull.eval(P, margin=0.08)
        return np.abs(d - (F(SK_OFF) - sk_folds(P))) - F(SK_T * 0.5)
    lo, hi = (-0.6, -0.5, 0.3), (0.6, 0.6, 1.0)
    fd.add(Inter(Func(cloth, hlo - 0.07, hhi + 0.07), Func(sk_cut, lo, hi), 0.005), 0.0)
    def trim(P):
        a = np.abs(sk_angle(P))
        e = np.minimum(P[:, 2] - sk_hem(P), (a - F(SK_OPEN)) * F(0.28))
        return e - F(0.022)
    fd.paint(Func(trim, lo, hi), 5)
    return fd


def legs_hull(side):
    b = Field("Leg" + side)
    for p, k in leg_prims(side):
        b.add(p, k)
    return b


def trousers_field():
    """Buff canvas trousers (label 0) from her waist into her boots, creased a little at the knees."""
    fd = Field("Trousers")
    hips = Field("Hips")
    tp = torso_prims()
    hips.add(tp[4][0], 0.0)
    hips.add(tp[5][0], tp[5][1])
    crease = lambda P: F(0.0014) * NOISE(P * F(26)) + F(0.0012) * np.sin(P[:, 2] * F(110)) * smoothstep(0.52, 0.42, P[:, 2])
    fd.add(Inter(Shell(hips, 0.012, 0.01, pad=0.08), Func(lambda P: np.maximum(P[:, 2] - F(0.97), F(0.6) - P[:, 2]), (-0.6, -0.5, 0.5), (0.6, 0.5, 1.1)), 0.004), 0.0)
    for side in ("R", "L"):
        lb = legs_hull(side)
        hip = J["hip_" + side]
        fd.add(Inter(Shell(lb, 0.01, 0.01, pad=0.06, disp=crease, disp_amp=0.002),
                     Func(lambda P: np.maximum(F(0.28) - P[:, 2], P[:, 2] - F(0.86)), hip - v3((0.3, 0.3, 0.8)), hip + v3((0.3, 0.3, 0.2))), 0.004), 0.02)
    return fd


# ======================================================================================= boots
BOOT_TOP_F, BOOT_TOP_B = 0.385, 0.355


def boot_hull(side):
    b = Field("BootHull" + side)
    for p, k in leg_prims(side)[3:]:
        b.add(p, k)
    foot(b, side)
    return b


def boot_top(P):
    return F(BOOT_TOP_B) + F(BOOT_TOP_F - BOOT_TOP_B) * smoothstep(0.06, -0.06, P[:, 1])


def lace_points(side):
    """Pairs of eyelets up the front of the boot (left, right of the lacing)."""
    bb = boot_hull(side)
    an = J["ankle_" + side]
    out = []
    for z in np.linspace(0.145, 0.345, 6):
        x0 = an[0] + (J["knee_" + side][0] - an[0]) * (z - an[2]) / (J["knee_" + side][2] - an[2])
        pair = []
        for dx in (-0.019, 0.019):
            h, ok = ray_hit(Func(lambda P: bb.eval(P, margin=0.1) - F(0.024), (-1, -1, 0.0), (1, 1, 0.6)),
                            [v3((x0 + dx, -0.4, z))], [v3((0, 1, 0))], tmax=0.6)
            pair.append(h[0] if ok[0] else None)
        if pair[0] is not None and pair[1] is not None:
            out.append(pair)
    return out


def boots_field():
    """Sturdy brown lace-up boots (label 0) to mid-calf, laced up the front (dark laces, 5) through brass eyelets (6); a
    toecap seam, a stacked heel and a thick sole (5)."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        bb = boot_hull(side)
        an, kn = J["ankle_" + side], J["knee_" + side]
        wrinkle = lambda P: F(0.0022) * np.sin(P[:, 2] * F(85)) * smoothstep(0.24, 0.13, P[:, 2]) + F(0.001) * NOISE(P * F(30))
        lo, hi = an - v3((0.2, 0.3, 0.2)), kn + v3((0.2, 0.2, 0.1))
        fd.add(Inter(Shell(bb, 0.016, 0.014, pad=0.06, disp=wrinkle, disp_amp=0.003), Func(lambda P: P[:, 2] - boot_top(P), lo, hi), 0.004), 0.0)
        # a rolled collar round the top
        def collar(P):
            t = boot_top(P)
            return np.abs(P[:, 2] - (t - F(0.008))) - F(0.01)
        fd.add(Inter(Shell(bb, 0.022, 0.012, pad=0.06), Func(collar, lo, hi), 0.003), 0.004)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.092)), (0.07, 0.158, 0.013), 0.009, R=Rz), 0.006, 5)      # the sole
        fd.add(RoundBox(an + fwd * -0.012 + v3((0, 0, -0.082)), (0.058, 0.052, 0.022), 0.008, R=Rz), 0.006, 5)    # the heel
        fd.sub(Torus(an + fwd * 0.155 + v3((0, 0, -0.065)), 0.062, 0.0022, R=rot_from_axes(z_axis=fwd + v3((0, 0, 0.6)))), 0.0015)  # toecap seam
        pairs = lace_points(side)
        for i, (pa, pb) in enumerate(pairs):
            for p in (pa, pb):
                fd.add(Torus(p, 0.0055, 0.0022, R=rot_from_axes(z_axis=(0, -1, 0))), 0.002, 6)
            if i + 1 < len(pairs):
                qa, qb = pairs[i + 1]
                fd.add(RoundCone(pa + v3((0, -0.002, 0)), qb + v3((0, -0.002, 0)), 0.0028, 0.0028), 0.002, 5)
                fd.add(RoundCone(pb + v3((0, -0.003, 0)), qa + v3((0, -0.003, 0)), 0.0028, 0.0028), 0.002, 5)
        top = pairs[-1]
        bow_c = (top[0] + top[1]) / 2 + v3((0, -0.006, 0.006))
        for s2 in (-1, 1):
            fd.add(Lock([bow_c, bow_c + v3((s2 * 0.018, -0.004, 0.008)), bow_c + v3((s2 * 0.026, -0.004, -0.002))],
                        [0.006, 0.008, 0.005], [0.0025, 0.0025, 0.002], [v3((0, -1, 0))] * 3, k=0.002), 0.002, 5)
            fd.add(RoundCone(bow_c, bow_c + v3((s2 * 0.01, -0.006, -0.05)), 0.0028, 0.0024), 0.002, 5)
    return fd


# ======================================================================================= the tool belt
BELT_Z = 0.9
BELT_TILT = 0.09                     # slung lower on her right hip (z = BELT_Z + BELT_TILT * x)
BELT_IN, BELT_OUT = SK_OUT + 0.003, SK_OUT + 0.02
BELT_W = 0.031


def belt_band(P):
    return np.abs(P[:, 2] - (F(BELT_Z) + F(BELT_TILT) * P[:, 0])) - F(BELT_W)


def belt_point(angle_deg, gap=0.0, dz=0.0):
    """A point on the belt's outer face at an angle round her (from her front toward her left), and the outward direction."""
    hull = skirt_hull()
    a = math.radians(angle_deg)
    d = v3((math.sin(a), -math.cos(a), 0.0))
    z = BELT_Z + BELT_TILT * math.sin(a) * 0.3 + dz
    for _ in range(3):
        h, ok = ray_hit(Func(lambda P: hull.eval(P, margin=0.12) - F(BELT_OUT + gap), (-1, -1, 0.6), (1, 1, 1.2)),
                        [v3((0, 0.05, z)) + d * 0.7], [-d], tmax=0.8)
        p = h[0] if ok[0] else v3((d[0] * 0.3, d[1] * 0.3, z))
        z = BELT_Z + BELT_TILT * p[0] + dz
    return v3((p[0], p[1], z)), d


WRENCH_ANGLE = -102.0                 # the spanner's loop on her right hip, a little behind
DRIVER_ANGLES = (62.0, 76.0)          # the screwdrivers' loops on her left hip
SPANNER_ANGLE = 94.0
POUCH_ANGLE = 140.0


def belt_field():
    """Brown leather (label 0) with dark stitching (5) and brass (6): the belt with its big brass buckle, a loop for the
    spanner on her right hip, loops for two screwdrivers and a small spanner on her left hip, a pouch behind."""
    fd = Field("Belt")
    hull = skirt_hull()
    scuff = lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.0008) * NOISE(P * F(70))
    def belt(P):
        d = hull.eval(P, margin=0.12)
        return np.maximum(np.maximum(d - F(BELT_OUT), F(BELT_IN) - d), belt_band(P))
    fd.add(Func(belt, (-0.42, -0.4, 0.8), (0.42, 0.45, 1.0), disp=scuff, disp_amp=0.002), 0.0)
    fd.paint(Func(lambda P: np.abs(np.abs(P[:, 2] - (F(BELT_Z) + F(BELT_TILT) * P[:, 0])) - F(BELT_W - 0.007)) - F(0.0022),
                  (-0.6, -0.6, 0.7), (0.6, 0.6, 1.1)), 5)                                               # stitching
    # the buckle
    bc, d = belt_point(0.0, 0.004)
    R = rot_from_axes(z_axis=d, x_axis=(1, 0, BELT_TILT))
    frame = Inter(RoundBox(bc, (0.044, 0.036, 0.007), 0.005, R=R),
                  Func(lambda P, bc=bc: -np.maximum(np.abs(P[:, 0] - F(bc[0])) - F(0.028), np.abs(P[:, 2] - F(bc[2])) - F(0.02)), bc - 0.1, bc + 0.1), 0.003)
    fd.add(frame, 0.002, 6)
    fd.add(RoundCone(bc + d * 0.006 + v3((0, 0, 0.022)), bc + d * 0.006 + v3((0, 0, -0.022)), 0.0045, 0.0045), 0.002, 6)
    fd.add(RoundCone(bc + d * 0.01, bc + d * 0.01 + v3((0.03, 0, 0.003)), 0.0035, 0.003), 0.002, 6)
    # loops: short leather straps standing off the belt
    for ang, w in [(WRENCH_ANGLE, 0.036)] + [(a, 0.02) for a in DRIVER_ANGLES] + [(SPANNER_ANGLE, 0.024)]:
        p, d = belt_point(ang, 0.006)
        side = norm(np.cross(v3((0, 0, 1)), d))
        deep = 0.022 if ang == WRENCH_ANGLE else 0.008             # (the spanner's loop stands out round its handle)
        fd.add(RoundBox(p + d * (deep - 0.004) - v3((0, 0, 0.006)), (w * 0.5, deep, BELT_W + 0.008), 0.004, R=np.stack([side, d, v3((0, 0, 1))], 1)), 0.004, 0)
        for s in (-1, 1):
            fd.add(Sphere(p + d * 0.012 + side * (s * w * 0.32) + v3((0, 0, BELT_W - 0.004)), 0.004), 0.002, 6)   # rivets
    # the pouch behind on her left
    p, d = belt_point(POUCH_ANGLE, 0.0, dz=-0.04)
    side = norm(np.cross(v3((0, 0, 1)), d))
    Rp = np.stack([side, d, v3((0, 0, 1))], 1)
    fd.add(RoundBox(p + d * 0.022 + v3((0, 0, -0.03)), (0.06, 0.028, 0.065), 0.018, R=Rp, disp=scuff, disp_amp=0.002), 0.006, 0)
    fd.add(Inter(Ellipsoid(p + d * 0.047 + v3((0, 0, 0.03)), (0.064, 0.022, 0.05), R=Rp), Plane(p + v3((0, 0, -0.01)), (0, 0, -1)), 0.004), 0.004, 0)   # the flap
    fd.add(Sphere(p + d * 0.07 + v3((0, 0, -0.008)), 0.008), 0.002, 6)                    # its stud
    return fd


def tools_field():
    """Tools in the belt's loops: two screwdrivers (walnut handles, 0; brass ferrules, 6; steel shafts, 7) and a small
    spanner (dark iron, 8) on her left hip."""
    fd = Field("Tools")
    for i, ang in enumerate(DRIVER_ANGLES):
        p, d = belt_point(ang, 0.018)
        up = norm(v3((0, 0, 1)) + d * 0.18 + v3((0.05 * (i - 0.5), 0, 0)))
        h0 = p + up * 0.01
        fd.add(RoundCone(h0, h0 + up * 0.085, 0.0125, 0.011), 0.0, 0)
        fd.add(Sphere(h0 + up * 0.085, 0.0115), 0.006, 0)
        fd.add(Cylinder(h0 - up * 0.004, 0.0085, 0.014, rr=0.002, R=rot_from_axes(z_axis=up)), 0.002, 6)
        fd.add(RoundCone(h0 - up * 0.01, h0 - up * (0.1 + 0.025 * i), 0.0045, 0.0035), 0.002, 7)
    p, d = belt_point(SPANNER_ANGLE, 0.016)
    up = norm(v3((0, 0, 1)) + d * 0.12)
    side = norm(np.cross(up, d))
    R = np.stack([side, d, up], 1)
    fd.add(RoundBox(p - up * 0.02, (0.009, 0.004, 0.075), 0.003, R=R), 0.0, 8)
    jc = p + up * 0.065
    fd.add(Inter(Cylinder(jc, 0.024, 0.009, rr=0.003, R=rot_from_axes(z_axis=d)),
                 Func(lambda P, jc=jc, up=up: -(np.maximum(np.abs((P - jc.astype(F)) @ side.astype(F)) - F(0.008), -((P - jc.astype(F)) @ up.astype(F)) + F(0.002))), jc - 0.1, jc + 0.1), 0.002), 0.004, 8)
    return fd


# ======================================================================================= the spanner (prop: `wrench`)
WR_LEN = (0.16, 0.11)          # the grip's middle -> the handle's end (back), -> the jaw's middle (forward) (as drawn)
WR_JAW_R = 0.047
WR_SCALE = 1.25                # (shipped this much bigger about its grip)


def wrench_rest():
    """(G: the grip's middle, A: along it toward the jaw, E: the jaw's opening, N: the flat's normal) as tucked through its
    loop on her right hip, the jaw up above the belt, the handle down along her hip."""
    p, d = belt_point(WRENCH_ANGLE, 0.026)
    A = norm(-d * 0.16 + v3((0.0, -0.3, 1.0)))          # (the handle raked back, down behind her hip)
    N = norm(d - A * float(d @ A))
    E = norm(np.cross(N, A))
    G = p - A * 0.02
    return G, A, E, N


def wrench_jaw():
    G, A, E, N = wrench_rest()
    return G + A * (WR_LEN[1] * WR_SCALE)


def wrench_field():
    """A big open-jawed spanner of dark forged iron (label 8): a flat handle with a leather-wrapped grip (5), a hole at its
    end, the open jaw (its throat bright steel, 7) angled across the handle."""
    fd = Field("Wrench")
    G, A, E, N = wrench_rest()
    R = np.stack([E, N, A], 1)
    back, fwd = WR_LEN
    fd.add(RoundBox(G + A * ((fwd - back) * 0.5 - 0.02), (0.017, 0.007, (fwd + back) * 0.5 - 0.03), 0.005, R=R), 0.0, 8)
    fd.add(Cylinder(G - A * back, 0.024, 0.014, rr=0.005, R=rot_from_axes(z_axis=N)), 0.008, 8)            # the handle's end
    fd.sub(Cylinder(G - A * back, 0.009, 0.05, rr=0.002, R=rot_from_axes(z_axis=N)), 0.002)
    fd.add(RoundCone(G - A * 0.065, G + A * 0.065, 0.016, 0.016), 0.004, 5)                                 # the grip
    jc = G + A * fwd
    Rj = rot_from_axes(z_axis=N, x_axis=A)
    fd.add(Cylinder(jc, WR_JAW_R, 0.016, rr=0.006, R=Rj), 0.012, 8)
    ang = math.radians(15)
    opn = norm(A * math.cos(ang) + E * math.sin(ang))
    wd = norm(np.cross(N, opn))
    def jaw_slot(P, hw, back):
        """< 0 inside the jaw's slot (half width hw, from `back` behind the jaw's middle out through its mouth)."""
        q = P - jc.astype(F)
        return np.maximum(np.abs(q @ wd.astype(F)) - F(hw), -(q @ opn.astype(F)) - F(back))
    fd.sub(Func(lambda P: jaw_slot(P, 0.021, 0.005), jc - 0.1, jc + 0.1), 0.003)          # the open jaw
    fd.paint(Func(lambda P: jaw_slot(P, 0.027, 0.012), jc - 0.1, jc + 0.1), 7)               # its bright throat
    return ScaledField(fd, G, WR_SCALE)


# ======================================================================================= the gauntlet (right forearm)
GA_T = (0.36, 0.9)               # the bracer: from this far down the forearm to that (fractions of el -> wr)
GEAR_T = 0.6
GEAR_R, GEAR_TH = 0.05, 0.012


def forearm_frame():
    """(el, ax: down the forearm, out: its outer side (away from her body), top: its thumb side, L)."""
    el, wr = J["elbow_R"], J["wrist_R"]
    ax = norm(wr - el)
    out = norm(v3((-1, 0, 0)) - ax * float(v3((-1, 0, 0)) @ ax))
    top = norm(np.cross(ax, out))
    if top[1] > 0:
        top = -top
    return el, ax, out, top, float(np.linalg.norm(wr - el))


def forearm_field():
    f = Field("ForearmR")
    for p, k in arm_prims("R")[3:5]:
        f.add(p, k)
    return f


def gear_frame():
    """(centre, axis) of the gauntlet's big gear, on the forearm's outer side."""
    el, ax, out, top, L = forearm_frame()
    c0 = el + ax * (L * GEAR_T)
    f = forearm_field()
    h, ok = ray_hit(Func(lambda P: f.eval(P, margin=0.1) - F(0.03), c0 - 0.3, c0 + 0.3), [c0 + out * 0.25], [-out], tmax=0.3)
    base = h[0] if ok[0] else c0 + out * 0.09
    return base + out * (GEAR_TH * 0.5 + 0.004), out


def core_center():
    return gear_frame()[0]


def gauntlet_field():
    """Brass (label 6) plates round her forearm, riveted iron bands (8) at its ends and middle, a housing for the gear,
    a small pressure gauge (a steel face, 7) on its top, a copper pipe (9) from the gauge round to the gear's housing, a
    lever with a red-lacquered knob (leather, 5) by her wrist, leather straps (5) under the plates."""
    fd = Field("Gauntlet")
    el, ax, out, top, L = forearm_frame()
    f = forearm_field()
    a, b = el + ax * (L * GA_T[0]), el + ax * (L * GA_T[1])
    def band(P, s0, s1):
        s = (P - el.astype(F)) @ ax.astype(F)
        return np.maximum(F(L * s0) - s, s - F(L * s1))
    ham = lambda P: F(0.0008) * NOISE(P * F(50))
    fd.add(Inter(Shell(f, 0.016, 0.012, pad=0.06, disp=ham, disp_amp=0.001), Func(lambda P: band(P, *GA_T), a - 0.2, b + 0.2), 0.004), 0.0, 6)
    for s0 in (GA_T[0], 0.62, GA_T[1] - 0.045):
        s1 = s0 + 0.05
        fd.add(Inter(Shell(f, 0.024, 0.01, pad=0.06), Func(lambda P, s0=s0, s1=s1: band(P, s0, s1), a - 0.2, b + 0.2), 0.003), 0.003, 8)
        for k in range(8):                                     # rivets round the band
            ang = 2 * math.pi * k / 8
            dvec = out * math.cos(ang) + top * math.sin(ang)
            c = el + ax * (L * (s0 + 0.025))
            h, ok = ray_hit(Func(lambda P: f.eval(P, margin=0.1) - F(0.03), c - 0.3, c + 0.3), [c + dvec * 0.25], [-dvec], tmax=0.3)
            if ok[0]:
                fd.add(Sphere(h[0], 0.005), 0.002, 6)
    # the gear's housing: a raised brass boss on the outer side
    gc, gn = gear_frame()
    fd.add(Cylinder(gc - gn * (GEAR_TH * 0.5 + 0.004), GEAR_R * 0.82, 0.014, rr=0.004, R=rot_from_axes(z_axis=gn)), 0.006, 6)
    # the gauge on the top, nearer the elbow
    c0 = el + ax * (L * 0.46)
    h, ok = ray_hit(Func(lambda P: f.eval(P, margin=0.1) - F(0.03), c0 - 0.3, c0 + 0.3), [c0 + top * 0.25], [-top], tmax=0.3)
    gp = (h[0] if ok[0] else c0 + top * 0.07)
    gpn = norm(top + out * 0.35)
    gpc = gp + gpn * 0.016
    fd.add(Cylinder(gpc, 0.024, 0.016, rr=0.004, R=rot_from_axes(z_axis=gpn)), 0.004, 6)
    fd.add(Cylinder(gpc + gpn * 0.007, 0.0185, 0.006, rr=0.002, R=rot_from_axes(z_axis=gpn)), 0.0015, 7)
    nd = norm(np.cross(gpn, ax))
    fd.add(RoundCone(gpc + gpn * 0.0105, gpc + gpn * 0.0105 + nd * 0.014 + ax * 0.004, 0.0018, 0.0012), 0.001, 8)
    # the copper pipe from the gauge round to the housing
    p0 = gpc - ax * 0.015 + out * 0.01
    p3 = gc - gn * 0.004 - ax * 0.05 + top * 0.03
    pipe = [p0, p0 + gpn * 0.012 - ax * 0.01, lerp(p0, p3, 0.5) + out * 0.03 + gpn * 0.01, p3]
    fd.add(Chain(pipe, [0.0055] * 4, k=0.004), 0.003, 9)
    # the lever by her wrist, its knob up
    c1 = el + ax * (L * 0.82)
    h, ok = ray_hit(Func(lambda P: f.eval(P, margin=0.1) - F(0.03), c1 - 0.3, c1 + 0.3), [c1 + top * 0.25], [-top], tmax=0.3)
    lp = (h[0] if ok[0] else c1 + top * 0.06) - top * 0.004
    tip = lp + top * 0.04 - ax * 0.02
    fd.add(Cylinder(lp, 0.011, 0.012, rr=0.003, R=rot_from_axes(z_axis=out)), 0.003, 6)
    fd.add(RoundCone(lp, tip, 0.0045, 0.004), 0.002, 6)
    fd.add(Sphere(tip, 0.009), 0.002, 5)
    return fd


def gear_field():
    """The gauntlet's big brass gear (label 6): twelve teeth, four spokes, a hub round the core."""
    fd = Field("Gear")
    c, n = gear_frame()
    R = rot_from_axes(z_axis=n)
    def gear(P):
        q = (P - c.astype(F)) @ R.astype(F)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        a = np.arctan2(q[:, 1], q[:, 0])
        tooth = np.clip(np.cos(a * F(12)) * F(2.2), -1, 1) * F(0.5) + F(0.5)
        rad = F(GEAR_R - 0.008) + F(0.012) * tooth
        d_r = r - rad
        d_z = np.abs(q[:, 2]) - F(GEAR_TH * 0.5)
        dd = np.maximum(d_r, d_z)
        # four windows between the spokes (< 0 inside a window)
        win = np.maximum(np.maximum(F(0.021) - r, r - F(GEAR_R - 0.017)), (F(0.42) - np.abs(np.sin(a * F(2)))) * F(0.03))
        return np.maximum(dd, -win)
    fd.add(Func(gear, c - 0.08, c + 0.08), 0.0, 6)
    fd.add(Torus(c, 0.019, 0.0055, R=R), 0.003, 6)                                    # the hub's rim
    for k in range(4):                                                                 # a rivet on each spoke
        ang = math.pi * k / 2
        o = R @ v3((math.cos(ang) * 0.028, math.sin(ang) * 0.028, GEAR_TH * 0.5))
        fd.add(Sphere(c + o, 0.0035), 0.0015, 6)
    return fd


def core_field():
    """The glowing amber core in the gear's hub (its own emissive mesh, on the `core` bone)."""
    fd = Field("Core")
    c, n = gear_frame()
    fd.add(Inter(Sphere(c + n * (GEAR_TH * 0.5 - 0.006), 0.018), Cylinder(c, 0.0155, 0.06, R=rot_from_axes(z_axis=n)), 0.002), 0.0)
    return fd


# ======================================================================================= the steam bolt launcher
GUN_G0 = v3((-0.32, -0.48, 0.9))          # rest: the pistol grip's middle (floating before her right hip) ...
GUN_A0 = v3((0.0, -1.0, 0.0))             # ... the barrel pointing ahead
GUN_U0 = v3((0.0, 0.0, 1.0))
GUN_S0 = np.cross(GUN_A0, GUN_U0)         # (her right: the launcher's outer side as she holds it at her hip)
MUZZLE_U, BAR_H = 0.6, 0.112
FORE_U = 0.27                             # the fore-grip
DRUM_U, DRUM_H = 0.05, 0.172              # the pan magazine's middle (on top of the receiver)
DRUM_R = 0.072
N_BOLTS = 8


GUN_SCALE = 1.2                           # (drawn at 1, shipped 1.2 times bigger about the grip: it reads from above)


def _gr(u, v=0.0, h=0.0):
    """A point of the launcher as drawn (launcher coordinates: u along the barrel, v to its right, h up)."""
    return GUN_G0 + GUN_A0 * u + GUN_S0 * v + GUN_U0 * h


def gl(u, v=0.0, h=0.0):
    """A point of the launcher (drawing coordinates), where it is at rest (scaled)."""
    return GUN_G0 + (GUN_A0 * u + GUN_S0 * v + GUN_U0 * h) * GUN_SCALE


def grip_axis():
    """The pistol grip's axis (from its foot up toward the receiver)."""
    return norm(GUN_U0 * 0.93 + GUN_A0 * 0.36)


def muzzle():
    return gl(MUZZLE_U, 0.0, BAR_H)


def drum_center():
    return gl(DRUM_U, 0.0, DRUM_H)


def launcher_field():
    """Walnut (label 0), black leather (5), polished brass (6), bright steel (7), dark iron (8), copper (9): the pistol grip
    and a short butt cap, the brass receiver (rivets, an iron side plate), the steel barrel with brass bands and a flared brass
    muzzle, the copper tank under it (brass bands, a gauge, a valve, a pipe up into the receiver), the fore-grip, the
    trigger and its guard, the pan magazine's brass collar."""
    fd = Field("Launcher")
    A, U, S = GUN_A0, GUN_U0, GUN_S0
    Rg = np.stack([S, A, U], 1)
    wood = lambda P: F(0.0007) * NOISE(P * np.array([60, 60, 60], F))
    # the pistol grip
    ga = grip_axis()
    gs = norm(np.cross(ga, S))
    Rgr = np.stack([S, gs, ga], 1)
    fd.add(RoundBox(_gr(0.0, 0.0, -0.006), (0.016, 0.022, 0.062), 0.013, R=Rgr, disp=wood, disp_amp=0.001), 0.0, 0)
    fd.add(Ellipsoid(_gr(0.0) - ga * 0.068, (0.02, 0.026, 0.012), R=Rgr), 0.006, 6)          # its brass cap
    # the receiver
    fd.add(RoundBox(_gr(0.05, 0.0, 0.095), (0.032, 0.115, 0.042), 0.013, R=Rg), 0.012, 6)
    for sv in (-1, 1):
        fd.add(RoundBox(_gr(0.04, sv * 0.03, 0.09), (0.004, 0.07, 0.026), 0.003, R=Rg), 0.003, 8)   # iron side plates
        for u in (-0.01, 0.03, 0.07, 0.11):
            for hh in (0.068, 0.112):
                fd.add(Sphere(_gr(u, sv * 0.034, hh), 0.0042), 0.0015, 6)
    # a short walnut butt cap behind the receiver (no long stock: she fires from the hip), a brass end plate
    fd.add(Ellipsoid(_gr(-0.08, 0.0, 0.1), (0.03, 0.055, 0.038), R=Rg, disp=wood, disp_amp=0.001), 0.02, 0)
    fd.add(Cylinder(_gr(-0.128, 0.0, 0.1), 0.026, 0.008, rr=0.003, R=rot_from_axes(z_axis=A)), 0.006, 6)
    # the barrel, its bands and the flared muzzle
    b0, b1 = _gr(0.16, 0.0, BAR_H), _gr(MUZZLE_U - 0.03, 0.0, BAR_H)
    fd.add(RoundCone(b0, b1, 0.021, 0.019), 0.006, 7)
    for u in (0.26, 0.42):
        fd.add(Torus(_gr(u, 0.0, BAR_H), 0.021, 0.0055, R=rot_from_axes(z_axis=A)), 0.003, 6)
    fd.add(RoundCone(_gr(MUZZLE_U - 0.05, 0.0, BAR_H), _gr(MUZZLE_U, 0.0, BAR_H), 0.021, 0.028), 0.006, 6)
    fd.add(Torus(_gr(MUZZLE_U - 0.004, 0.0, BAR_H), 0.026, 0.005, R=rot_from_axes(z_axis=A)), 0.003, 6)
    fd.sub(Cylinder(_gr(MUZZLE_U, 0.0, BAR_H), 0.011, 0.08, R=rot_from_axes(z_axis=A)), 0.002)
    fd.add(RoundBox(_gr(MUZZLE_U - 0.03, 0.0, BAR_H + 0.026), (0.003, 0.01, 0.008), 0.002, R=Rg), 0.003, 6)    # the sight
    # the copper tank under the barrel
    t0, t1 = _gr(0.135, 0.0, 0.038), _gr(0.45, 0.0, 0.038)
    fd.add(RoundCone(t0, t1, 0.033, 0.033), 0.006, 9)
    for u in (0.18, 0.3, 0.42):
        fd.add(Torus(_gr(u, 0.0, 0.038), 0.034, 0.0045, R=rot_from_axes(z_axis=A)), 0.002, 6)
        fd.add(RoundBox(_gr(u, 0.0, 0.08), (0.007, 0.006, 0.02), 0.003, R=Rg), 0.003, 6)         # straps up to the barrel
    for u in np.linspace(0.15, 0.44, 8):
        fd.add(Sphere(_gr(u, 0.0, 0.074), 0.0035), 0.0015, 9)                                    # a riveted seam on top
    # its gauge, on the outer side
    gpc = _gr(0.25, 0.037, 0.034)
    fd.add(Cylinder(gpc, 0.022, 0.014, rr=0.004, R=rot_from_axes(z_axis=S)), 0.004, 6)
    fd.add(Cylinder(gpc + S * 0.006, 0.017, 0.005, rr=0.002, R=rot_from_axes(z_axis=S)), 0.0015, 7)
    fd.add(RoundCone(gpc + S * 0.009, gpc + S * 0.009 + norm(A + U * 0.6) * 0.013, 0.0017, 0.0012), 0.001, 8)
    # a valve on the tank's front, a pipe from its back up into the receiver
    fd.add(RoundCone(_gr(0.475, 0.0, 0.038), _gr(0.5, 0.0, 0.038), 0.012, 0.009), 0.003, 6)
    fd.add(Torus(_gr(0.504, 0.0, 0.038), 0.014, 0.0035, R=rot_from_axes(z_axis=A)), 0.002, 8)
    fd.add(Chain([_gr(0.11, -0.014, 0.03), _gr(0.085, -0.03, 0.04), _gr(0.07, -0.03, 0.062)], [0.0065] * 3, k=0.004), 0.003, 9)
    # the fore-grip
    fd.add(RoundCone(_gr(FORE_U, 0.0, 0.0), _gr(FORE_U - 0.01, 0.0, -0.105), 0.017, 0.02, disp=wood, disp_amp=0.001), 0.006, 0)
    fd.add(Ellipsoid(_gr(FORE_U - 0.011, 0.0, -0.11), (0.022, 0.022, 0.011), R=Rg), 0.005, 6)
    # the trigger and its guard
    fd.add(RoundCone(_gr(0.042, 0.0, 0.052), _gr(0.05, 0.0, 0.03), 0.0045, 0.0035), 0.002, 7)
    fd.add(Chain([_gr(0.02, 0.0, 0.058), _gr(0.035, 0.0, 0.014), _gr(0.07, 0.0, 0.012), _gr(0.09, 0.0, 0.05)], [0.0042] * 4, k=0.003), 0.003, 6)
    # the pan magazine's collar on the receiver
    fd.add(Cylinder(_gr(DRUM_U, 0.0, 0.147), 0.03, 0.024, rr=0.004, R=rot_from_axes(z_axis=U)), 0.006, 6)
    return ScaledField(fd, GUN_G0, GUN_SCALE)


def bolt_dirs():
    """The bolts' directions in the pan (rest), radial."""
    S, A = GUN_S0, GUN_A0
    return [S * math.cos(2 * math.pi * k / N_BOLTS + 0.4) + A * math.sin(2 * math.pi * k / N_BOLTS + 0.4) for k in range(N_BOLTS)]


def drum_field():
    """The pan magazine (its own bone, `drum`): a flat brass pan (label 6) with a raised rim and a dark iron hub (8), eight
    steel bolts (7) lying in it, radially, their bodkin points out over the rim, brass fletching (6) at the hub."""
    fd = Field("Drum")
    c, U = _gr(DRUM_U, 0.0, DRUM_H), GUN_U0
    R = rot_from_axes(z_axis=U)
    fd.add(Cylinder(c, DRUM_R, 0.032, rr=0.008, R=R), 0.0, 6)
    fd.add(Torus(c + U * 0.016, DRUM_R - 0.003, 0.005, R=R), 0.003, 6)
    fd.sub(Cylinder(c + U * 0.02, DRUM_R - 0.01, 0.016, rr=0.003, R=R), 0.003)
    fd.add(Cylinder(c + U * 0.015, 0.022, 0.03, rr=0.006, R=R), 0.004, 8)
    fd.add(Sphere(c + U * 0.03, 0.012), 0.004, 8)
    for d in bolt_dirs():
        d = norm(d)
        a, b = c + d * 0.024 + U * 0.027, c + d * (DRUM_R - 0.006) + U * 0.027
        fd.add(RoundCone(a, b, 0.0055, 0.0055), 0.002, 7)
        fd.add(RoundCone(b, b + d * 0.026, 0.0085, 0.0015), 0.002, 7)                            # the bodkin point
        side = norm(np.cross(U, d))
        fd.add(RoundBox(a + d * 0.008 + U * 0.004, (0.0015, 0.008, 0.007), 0.0012, R=np.stack([side, d, U], 1)), 0.0015, 6)
    return ScaledField(fd, GUN_G0, GUN_SCALE)


# ======================================================================================= brass: buttons
def brass_field():
    """Brass (label 0): the waistcoat's two rows of buttons."""
    fd = Field("Brass")
    for p in wc_button_points():
        n = norm(v3((p[0] * 0.5, -1.0, 0.0)))
        _button(fd, p + n * 0.003, n, r=0.0105)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.232, 1.622)), 0.045, 0.45)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.085, -0.15, 1.6)), 0.06, 0.6), (hp((sx * 0.174, 0.035, 1.66)), 0.05, 0.5),
                (J["elbow_" + sd] + v3((0, 0.022, 0)), 0.05, 0.25)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.01, 0.028, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "ada"
ROOT_NAME = "HeroAdaHQ"
TEX_PREFIX = "hero"
MAT_NAME = "AdaMat"
MESH_NAME = "Ada"
BASE_MODULE = "ada_base"
ANIM_MODULE = "anim_ada"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Pencil", "Goggles", "Lenses", "Blouse", "Corset", "Skirt", "Trousers", "Boots",
         "Belt", "Tools", "Brass", "Gauntlet", "Gear", "Core", "Launcher", "Drum", "Wrench"]
REGION_PARTS = ("Skin", "Pencil", "Goggles", "Corset", "Skirt", "Boots", "Belt", "Tools", "Gauntlet", "Gear", "Launcher", "Drum",
                "Wrench")
NAVY = (0.18, 0.22, 0.42)                 # the corps' navy (the lead's ruling: reads as navy from the game camera)
BRASS = (0.8, 0.55, 0.22)
MAROON = (0.4, 0.09, 0.11)
COPPER = ((0.75, 0.35, 0.18), (0.98, 0.66, 0.44))
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_AdaSkin", "base": (0.9, 0.69, 0.56), "ruddy": (0.92, 0.55, 0.46), "lips": (0.78, 0.4, 0.38),
                      "brow": ((0.42, 0.15, 0.06), (0.6, 0.25, 0.11)),
                      "extra": ((LASH, (0.24, 0.1, 0.05), 0.5), (FRECKLE, (0.74, 0.47, 0.32), 0.55))}),
    "Hair": ("hair", {"name": "HQ_AdaHair", "base": (0.54, 0.18, 0.06), "hi": (0.9, 0.46, 0.2), "low": (0.24, 0.065, 0.02),
                      "streak": (0.38, 0.11, 0.04), "tint": (0.7, 0.26, 0.08)}),
    "Pencil": ("siege", {"name": "HQ_AdaPencil", "wood": (0.88, 0.72, 0.5), "wood2": (0.74, 0.58, 0.38), "red": (0.96, 0.76, 0.14),
                         "blue": (0.94, 0.55, 0.58), "metal": "iron"}),
    "Goggles": ("armory", {"name": "HQ_AdaGoggles"}),
    "Lenses": ("vials", {"name": "HQ_AdaLenses", "glass": (0.36, 0.68, 0.52)}),
    "Blouse": ("linen", {"name": "HQ_AdaBlouse", "base": (0.95, 0.93, 0.87)}),
    "Corset": ("wool", {"name": "HQ_AdaCorset", "base": NAVY, "border": BRASS, "stripe": BRASS}),
    "Skirt": ("wool", {"name": "HQ_AdaSkirt", "base": MAROON, "border": BRASS, "stripe": BRASS}),
    "Trousers": ("linen", {"name": "HQ_AdaTrousers", "base": (0.74, 0.62, 0.44)}),
    "Boots": ("leather_dyed", {"name": "HQ_AdaBoots", "base": (0.36, 0.21, 0.11), "dyed": (0.12, 0.08, 0.06)}),
    "Belt": ("leather_dyed", {"name": "HQ_AdaBelt", "base": (0.44, 0.26, 0.13), "dyed": (0.2, 0.12, 0.07)}),
    "Tools": ("armory", {"name": "HQ_AdaTools"}),
    "Brass": ("bronze", {"name": "HQ_AdaBrass", "base": BRASS, "hi": (1.0, 0.9, 0.58), "dark": (0.36, 0.22, 0.07),
                         "patina": (0.5, 0.42, 0.2)}),
    "Gauntlet": ("armory", {"name": "HQ_AdaGauntlet", "grip": (0.55, 0.06, 0.05), "copper": COPPER}),
    "Gear": ("armory", {"name": "HQ_AdaGear"}),
    "Launcher": ("armory", {"name": "HQ_AdaLauncher", "copper": COPPER}),
    "Drum": ("armory", {"name": "HQ_AdaDrum"}),
    "Wrench": ("armory", {"name": "HQ_AdaWrench", "grip": (0.3, 0.17, 0.09)}),
}
GLOW = {"Core": ((1.0, 0.62, 0.18), 1.0, 0.5)}
LOW_TARGETS = {"Skin": 6000, "Teeth": 100, "Hair": 2200, "Pencil": 160, "Goggles": 800, "Lenses": 120, "Blouse": 1800,
               "Corset": 1800, "Skirt": 1600, "Trousers": 600, "Boots": 1300, "Belt": 1200, "Tools": 500, "Brass": 400,
               "Gauntlet": 1300, "Gear": 450, "Core": 120, "Launcher": 2400, "Drum": 900, "Wrench": 450}
AO_EXCLUDE = ["Launcher", "Drum", "Wrench", "Pencil", "Brass", "Gear"]
BAKE_APART = (["Launcher", "Drum", "Wrench"], (3.0, 0.0, 0.0))     # (the launcher floats before her, the spanner is in its loop)


def prop_bones():
    """The launcher and the spanner ride parentless bones (every clip poses them in world space, anim_ada.py); the pan
    magazine a child of the launcher's (it turns on after a shot); the gear and its core children of her right forearm."""
    G, A, E, N = wrench_rest()
    c, n = gear_frame()
    cc = core_center()
    dc = drum_center()
    return [("launcher", GUN_G0, muzzle(), None),
            ("drum", dc, dc + GUN_U0 * 0.06, "launcher"),
            ("wrench", G, wrench_jaw(), None),
            ("gear", c, c + n * 0.05, "forearm.R"),
            ("core", cc, cc + n * 0.03, "forearm.R")]


COAT_BONES = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L", "hand.R", "hand.L",
                      "thigh.R", "thigh.L"}
COAT_CAPS = {"thigh.R": 0.45, "thigh.L": 0.45, "hand.R": 0.25, "hand.L": 0.25}
WC_BONES = TORSO | {"clavicle.R", "clavicle.L"}


def blouse_weights(ob, skin_ob, arm):
    """The blouse follows her body and arms; the rolled sleeves ride the arm round the elbow."""
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=COAT_BONES - {"hand.R", "hand.L", "thigh.R", "thigh.L"}, caps=None)


def boots_weights(ob, skin_ob, arm):
    _isla_boots_weights(ob, skin_ob, arm)


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Pencil": ("rigid", "head"),
        "Goggles": ("rigid", "head"), "Lenses": ("rigid", "head"),
        "Blouse": ("custom", blouse_weights),
        "Corset": ("transfer", WC_BONES, None),
        "Skirt": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Trousers": ("transfer", {"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Boots": ("custom", boots_weights),
        "Belt": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.25, "thigh.L": 0.25}),
        "Tools": ("rigid", "root"),
        "Brass": ("transfer", WC_BONES, None),
        "Gauntlet": ("rigid", "forearm.R"), "Gear": ("rigid", "gear"), "Core": ("rigid", "core"),
        "Launcher": ("rigid", "launcher"), "Drum": ("rigid", "drum"), "Wrench": ("rigid", "wrench"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Launcher", "Drum", "Gauntlet", "Gear", "Goggles"):
        return 1.1
    if part in ("Trousers", "Tools"):
        return 0.7
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Pencil", pencil_field(), 0.0012 if fine else 0.0018),
        ("Goggles", goggles_field(), 0.0016 if fine else 0.0024),
        ("Lenses", lenses_field(), 0.0016 if fine else 0.0024),
        ("Blouse", blouse_field(), 0.0024 if fine else 0.0034),
        ("Corset", corset_field(), 0.0024 if fine else 0.0034),
        ("Skirt", skirt_field(), 0.0028 if fine else 0.0038),
        ("Trousers", trousers_field(), 0.0028 if fine else 0.0038),
        ("Boots", boots_field(), 0.0018 if fine else 0.0026),
        ("Belt", belt_field(), 0.002 if fine else 0.003),
        ("Tools", tools_field(), 0.0014 if fine else 0.002),
        ("Brass", brass_field(), 0.0014 if fine else 0.002),
        ("Gauntlet", gauntlet_field(), 0.0016 if fine else 0.0024),
        ("Gear", gear_field(), 0.0012 if fine else 0.0018),
        ("Core", core_field(), 0.0015),
        ("Launcher", launcher_field(), 0.0016 if fine else 0.0024),
        ("Drum", drum_field(), 0.0013 if fine else 0.002),
        ("Wrench", wrench_field(), 0.0016 if fine else 0.0024),
    ]
