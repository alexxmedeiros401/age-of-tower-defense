"""The Oracle (HQ tower, Classical Age): the Pythia of Delphi at her bronze tripod. Rest pose = A-pose, facing -Y, feet at
z = 0; right side = -X.

A tall woman of middle years, serene and far away: high cheekbones, a long straight nose, full lips closed in a calm
line, heavy-lidded eyes half shut in trance and drawn out in kohl, fine lines at their corners; dark hair with a streak
of grey, parted in the middle and waved back over her ears; a fine white veil over the back of her head falling to her
shoulder blades, held by a wreath of laurel. A long white linen chiton to her feet, finely pleated, its sleeves pinned
along her upper arms, girdled under her breasts with a gold cord; over it a saffron himation with a violet border,
wrapped round her hips and thrown up over her left shoulder (a gold brooch there); gold bracelets, sandals. A sprig of
laurel in her right fist; her left hand open, to waft the vapours to her face.

Beside her on her left, a little in front, the tall bronze tripod of Delphi: three slender legs on lion's paws, braced
by a ring, carrying a deep cauldron with two ring handles; embers glow in it (their own mesh, glowing) and the vapours
rise (game.gd). Her body, hands and feet are Mara's (mara.py): the laurel is rigid in her right fist, the tripod stands
on its own ("props" bone)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import mara as _m
from mara import (J, HS, DZ, HPIV, hp, hr, HEAD_C, HEAD_RAD, EYE_R, eye_c, hand_frame, HAND_S, fist_center, hand, foot,
                  torso_prims, traps, neck_prim, deltoid, eyes_field, teeth_field, TORSO, TORSO_Z, torso_bones)

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH = 0, 1, 2, 3, 4, 5, 8


def hinv(P):
    """World points -> the head's design coordinates (the inverse of hp)."""
    return (P - HPIV.astype(F)) / F(HS) + HPIV.astype(F) - np.array([0, 0, DZ], F)


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


# ======================================================================================= head
def head(fd):
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.058, 1.596), (0.146, 0.132, 0.13)), 0.07, SKIN)                          # a long oval jaw
    fd.add(E((0, -0.13, 1.506), (0.072, 0.062, 0.06)), 0.05, SKIN)                           # a small firm chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.114, -0.112, 1.634), 0.05), 0.05, SKIN)                               # high cheekbones
        fd.add(S((sx * 0.12, -0.05, 1.562), 0.054), 0.05, SKIN)
        pts = [hp((sx * 0.15, -0.06, 1.746)), hp((sx * 0.115, -0.128, 1.752)), hp((sx * 0.062, -0.164, 1.75))]
        fd.add(Chain(pts, [hr(0.01), hr(0.014), hr(0.012)], k=hr(0.02)), hr(0.03), SKIN)
    # fine arched brows
    for sx in (-1, 1):
        pts = [hp((sx * 0.03, -0.203, 1.77)), hp((sx * 0.072, -0.194, 1.786)), hp((sx * 0.114, -0.17, 1.784)), hp((sx * 0.148, -0.134, 1.766))]
        fd.add(Chain([p + v3((0, 0.007, 0)) for p in pts], [hr(0.006), hr(0.007), hr(0.006), hr(0.003)], k=hr(0.006)), hr(0.008), BROW)
        fd.paint(Chain(pts, [hr(0.012), hr(0.014), hr(0.012), hr(0.007)], k=hr(0.009)), BROW)
    # heavy-lidded eyes, half shut in trance; kohl drawn out in wings; lines at their corners
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0062)), Plane(ec + v3((0, 0, hr(0.004))), (sx * 0.16, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0048)), Plane(ec + v3((0, 0, -hr(0.024))), (sx * -0.12, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.009)), Plane(ec + v3((0, 0, hr(0.0)), ), (sx * 0.16, 0.05, -1.0)), hr(0.002)), LASH)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.008)), 0.0, hr(0.006)), Plane(ec + v3((0, 0, -hr(0.02))), (sx * -0.12, 0.05, 1.0)), hr(0.002)), LASH)
        wing = ec + v3((sx * hr(0.044), -hr(0.012), hr(0.004)))
        fd.paint(RoundCone(wing, wing + v3((sx * hr(0.03), hr(0.012), hr(0.01))), hr(0.006), hr(0.002)), LASH)
        for k in range(2):
            a = hp((sx * (0.116 + 0.004 * k), -0.126 + 0.006 * k, 1.68 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.02, 0.012, -0.004 - 0.008 * k)), hr(0.0018), hr(0.0012)), hr(0.0025))
    # a long straight nose
    fd.add(RoundCone(hp((0, -0.18, 1.728)), hp((0, -0.228, 1.634)), hr(0.013), hr(0.018)), hr(0.016), SKIN)
    fd.add(S((0, -0.229, 1.624), 0.022), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.025, -0.208, 1.611), 0.016), hr(0.011), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.013, -0.222, 1.6)), v3((0.008, 0.009, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
        # the lines from her nose to the corners of her mouth
        fd.sub(Chain([hp((sx * 0.04, -0.198, 1.602)), hp((sx * 0.058, -0.178, 1.574)), hp((sx * 0.066, -0.162, 1.548))],
                     [hr(0.0022), hr(0.0026), hr(0.0018)], k=hr(0.003)), hr(0.004))
    # full lips, closed in a calm line
    slot = [hp((-0.056, -0.163, 1.552)), hp((-0.029, -0.188, 1.545)), hp((0, -0.195, 1.543)), hp((0.029, -0.188, 1.545)), hp((0.056, -0.163, 1.552))]
    fd.sub(Chain(slot, [hr(0.002), hr(0.0028), hr(0.003), hr(0.0028), hr(0.002)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.054, -0.161, 1.555), (-0.028, -0.181, 1.554), (-0.008, -0.187, 1.558), (0.008, -0.187, 1.558), (0.028, -0.181, 1.554), (0.054, -0.161, 1.555)]
    lo_lip = [(-0.046, -0.163, 1.543), (-0.025, -0.181, 1.532), (0, -0.186, 1.528), (0.025, -0.181, 1.532), (0.046, -0.163, 1.543)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.004), hr(0.007), hr(0.0075), hr(0.0075), hr(0.007), hr(0.004)], k=hr(0.006)), hr(0.009), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.0085), hr(0.0095), hr(0.0085), hr(0.005)], k=hr(0.007)), hr(0.009), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.176, 0.035, 1.66)), v3((0.025, 0.044, 0.056)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.05, SKIN)
    fd.add(neck_prim(), 0.045, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.05, SKIN)
        fd.add(RoundCone(sh, el, 0.072, 0.054), 0.045, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.064, 0.066, 0.1), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(RoundCone(el, wr, 0.054, 0.042), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.066, 0.06, 0.108), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.022, 0)), 0.043), 0.025, SKIN)
        hand(fd, side, fist=(side == "R"))
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.122, 0.076), 0.06, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.02, 0)), (0.112, 0.102, 0.17), R=rot_from_axes(z_axis=kn - hip)), 0.045, SKIN)
        fd.add(Sphere(kn + v3((0, -0.026, 0.0)), 0.06), 0.035, SKIN)
        fd.add(RoundCone(kn, an, 0.074, 0.049), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.026, 0)), (0.082, 0.08, 0.128), R=rot_from_axes(z_axis=an - kn)), 0.04, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= hair, veil, wreath
def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    fd.add(Ellipsoid(hp((0, -0.058, 1.596)), v3((0.146, 0.132, 0.13)) * HS), 0.07)
    fd.add(neck_prim(), 0.05)
    return fd


def hair_tex(P):
    """Soft waves running back from the parting over her temples; positive pushes the surface in."""
    Q = hinv(P)
    ax = np.abs(Q[:, 0])
    wave = np.sin((Q[:, 2] - F(0.35) * ax) * F(70) + F(0.6) * NOISE(Q * F(8)))
    strands = np.abs(np.sin((Q[:, 2] + F(0.5) * Q[:, 1]) * F(260) + F(2.0) * NOISE(Q * F(14))))
    part = F(0.004) * np.exp(-(Q[:, 0] / F(0.006)) ** 2) * (Q[:, 1] < F(0.02)).astype(F)
    return F(0.0025) * wave + F(0.0012) * strands + part


def hair_field():
    """Dark hair parted in the middle, swept back in soft waves over her ears (the veil hides the knot at her nape)."""
    fd = Field("Hair")
    hull = head_hull()
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        front = F(1.83) - F(0.1) * smoothstep(0.03, 0.16, ax)                     # a high hairline, down the temples
        lo = np.where(y < F(-0.06), front, F(1.6) - F(0.1) * smoothstep(-0.06, 0.12, y))
        return np.maximum(lo - z, F(-0.12) - y - F(0.1) * smoothstep(1.75, 1.88, z))
    fd.add(Inter(Shell(hull, 0.012, 0.026, pad=0.08, disp=hair_tex, disp_amp=0.004), Func(keep, HEAD_C - 0.45, HEAD_C + 0.35), 0.006), 0.0)
    # the knot at her nape (mostly under the veil)
    fd.add(Ellipsoid(hp((0, 0.18, 1.63)), v3((0.06, 0.045, 0.05)) * HS, disp=hair_tex, disp_amp=0.004), 0.02)
    # a grey streak from the parting back over her right temple
    fd.paint(Func(lambda P: np.maximum(np.abs(hinv(P)[:, 0] + F(0.045)) - F(0.016), F(1.72) - hinv(P)[:, 2]), HEAD_C - 0.4, HEAD_C + 0.4), 5)
    return fd


WREATH_F = v3((0.0, -0.17, 1.84))       # the wreath's front and back (design coordinates)
WREATH_B = v3((0.0, 0.17, 1.8))
_WN = norm(v3((0, -(WREATH_B[2] - WREATH_F[2]) / (WREATH_B[1] - WREATH_F[1]), 1.0)))


def wreath_d(P):
    return (hinv(P) - WREATH_F.astype(F)) @ _WN.astype(F)


def veil_hull():
    fd = Field("VeilHull")
    fd.add(Ellipsoid(HEAD_C + v3((0, 0.01, 0.0)), HEAD_RAD + v3((0.022, 0.022, 0.022))), 0.0)
    fd.add(Ellipsoid(hp((0, 0.18, 1.63)), v3((0.075, 0.06, 0.065)) * HS), 0.05)       # over the knot
    fd.add(neck_prim(), 0.08)
    fd.add(traps(), 0.06)
    fd.add(Ellipsoid((0, 0.13, 1.2), (0.25, 0.14, 0.22)), 0.08)                          # her back (clear of the chiton)
    for side in ("R", "L"):
        fd.add(deltoid(side), 0.06)
    return fd


def veil_field():
    """Fine white linen over the back of her head from just behind the wreath, down over her hair's knot to her shoulder
    blades, a narrow violet border (label 5) along its edge."""
    fd = Field("Veil")
    hull = veil_hull()
    def folds(P):
        """Soft folds falling from the crown (none at its very top, where they would meet), deeper as the cloth hangs."""
        rxy = np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F(0.02)) ** 2)
        amp = (F(0.004) + F(0.007) * smoothstep(1.85, 1.35, P[:, 2])) * smoothstep(0.02, 0.1, rxy)
        return amp * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(0.02)) * F(11) + F(0.8) * NOISE(P * F(4))) + F(0.0012) * NOISE(P * F(30))
    def edge(P):
        """< 0 inside the veil: behind the wreath, behind her ears and jaw, down to its hem."""
        Q = hinv(P)
        y, z = P[:, 1], P[:, 2]
        front = wreath_d(P) - F(0.006)                                              # starts at the wreath
        side = F(-0.02) - Q[:, 1] + F(0.18) * smoothstep(1.75, 1.6, Q[:, 2])        # behind her ears, then her shoulders
        hem = F(1.12) + F(0.1) * smoothstep(0.05, 0.3, np.abs(P[:, 0])) + F(0.012) * NOISE(P * F(9)) - z
        return np.maximum(np.maximum(np.minimum(front, side), hem), F(-0.02) - y + F(0.0) * z)
    def cloth(P):
        d = hull.eval(P, margin=0.1)
        return np.maximum(d - (F(0.034) - folds(P)), F(0.014) - d)       # (folds push in the outer face only)
    fd.add(Inter(Func(cloth, (-0.6, -0.5, 0.9), (0.6, 0.6, 2.1)), Func(edge, (-0.6, -0.6, 0.9), (0.6, 0.7, 2.1)), 0.004), 0.0)
    fd.paint(Func(lambda P: np.abs(edge(P) + F(0.012)) - F(0.012), (-0.6, -0.6, 0.9), (0.6, 0.7, 2.1)), 5)
    return fd


def wreath_points(n=34):
    """Points round her head along the wreath's band (on the hair), front first."""
    hull = Field("WreathHull")
    hull.add(Ellipsoid(HEAD_C, HEAD_RAD + v3((0.03, 0.03, 0.03))), 0.0)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = v3((math.sin(a), -math.cos(a), 0.0))
        q = WREATH_F + (WREATH_B - WREATH_F) * (0.5 - 0.5 * math.cos(a))
        o = hp(v3((0, 0.02, q[2]))) + d * 0.6
        h, ok = ray_hit(hull, [o], [-d], tmax=0.7)
        if ok[0]:
            pts.append((h[0], d, a))
    return pts


def wreath_field():
    """A wreath of laurel: a twig band (label 7) round her head, pairs of long pointed leaves along it (0), sweeping from
    the back toward the front where the two branches meet over her brow."""
    fd = Field("Wreath")
    pts = [(p, d, a) for p, d, a in wreath_points() if a < math.radians(118) or a > math.radians(242)]
    pts = sorted(pts, key=lambda q: (q[2] + math.pi) % (2 * math.pi))           # from her right temple round to her left
    ring = [p for p, d, a in pts]
    fd.add(Chain(ring, [0.006] * len(ring), k=0.004), 0.0, 7)
    leafy = lambda P: F(0.0008) * NOISE(P * F(60))
    for i, (p, d, a) in enumerate(pts):
        if i % 2:
            continue
        tng = v3((math.cos(a), math.sin(a), 0.0)) * (-1.0 if a < math.pi else 1.0)      # along the band toward the front
        out = norm(d)
        for s in (-1, 1):
            ld = norm(tng + v3((0, 0, 0.32 * s)))
            c = p + ld * 0.032 + out * 0.008
            fd.add(Ellipsoid(c, (0.012, 0.004, 0.034), R=rot_from_axes(z_axis=ld, y_axis=out), disp=leafy, disp_amp=0.001), 0.003, 0)
    return fd


# ======================================================================================= chiton, himation
HEM_Z = 0.07


def dress_base():
    b = Field("DressBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(RoundCone((0, 0.04, 0.9), (0, 0.05, 0.08), 0.24, 0.33), 0.1)                 # the skirt to her feet
    for side in ("R", "L"):
        b.add(deltoid(side), 0.05)
        b.add(RoundCone(J["shoulder_" + side], J["elbow_" + side], 0.072, 0.054), 0.045)
    return b


def _neck_cut(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.04)) / F(0.2), 0, 1)
    return z - (F(1.43) - F(0.07) * front * np.exp(-(x / F(0.13)) ** 2) + F(0.3) * smoothstep(0.2, 0.28, np.abs(x)))


def _sleeve(P, side):
    """< 0 on the body side of the sleeve's end (just above the elbow)."""
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    n = norm(el - sh)
    c = sh + (el - sh) * 0.86
    d = (P - c.astype(F)) @ n.astype(F)
    sx = -1 if side == "R" else 1
    return np.where((P[:, 0] * F(sx) > F(0.26)) & (P[:, 2] > F(1.0)), d, F(-1.0))


def hem_z(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.04)))
    return F(HEM_Z) + F(0.012) * np.cos(a * 3) + F(0.006) * NOISE(P * F(8))


GIRDLE_Z = 1.06


def chiton_field():
    """White linen to her feet, fine vertical pleats falling from the girdle; sleeves to the elbow, pinned along the
    top of the arm (gold pins: the Gold part); gathered in under the girdle."""
    fd = Field("Chiton")
    base = dress_base()
    def pleats(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.04)))
        below = smoothstep(GIRDLE_Z - 0.02, GIRDLE_Z - 0.12, P[:, 2])
        above = smoothstep(GIRDLE_Z + 0.02, GIRDLE_Z + 0.1, P[:, 2])
        fine = F(0.004) * np.sin(a * F(44) + F(0.5) * NOISE(P * F(5)))
        deep = F(0.008) * np.sin(a * F(13) + F(0.9) * NOISE(P * F(2.5)))
        return (fine + deep) * below + F(0.003) * np.sin(a * F(30)) * above + F(0.0012) * NOISE(P * F(30)) \
            + F(0.006) * np.exp(-((P[:, 2] - F(GIRDLE_Z)) / F(0.015)) ** 2)       # pulled in under the girdle
    def keep(P):
        k = np.maximum(hem_z(P) - P[:, 2], _neck_cut(P))
        return np.maximum(np.maximum(k, _sleeve(P, "R")), _sleeve(P, "L"))
    def cloth(P):
        d = base.eval(P, margin=0.12)
        return np.maximum(d - (F(0.03) - pleats(P)), F(0.006) - d)
    fd.add(Inter(Func(cloth, (-0.75, -0.6, 0.0), (0.75, 0.6, 1.6)), Func(keep, (-1, -1, 0.0), (1, 1, 1.6)), 0.005), 0.0)
    return fd


def _drape(P):
    """< 0 inside the himation: a broad band from her left shoulder down across her chest and back to her right hip,
    and a wrap round her hips to below the knee."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    # the band: between two planes slanting from her left shoulder down to her right hip
    n = norm(v3((0.62, 0.0, 1.0)))
    s = (P - np.array([0.0, 0.0, 1.02], F)) @ n.astype(F)
    band = np.abs(s - F(0.03)) - F(0.13)
    wrap = np.maximum(F(0.5) + F(0.06) * x - z, z - (F(0.9) + F(0.05) * x))
    return np.minimum(band, wrap)


def himation_field():
    """The mantle: saffron wool with a violet border (label 5) and a thin dark stripe inside it (6), wrapped round her
    hips over the chiton and thrown up over her left shoulder, in broad folds; a thick roll along its top edge at the
    waist."""
    fd = Field("Himation")
    base = dress_base()
    folds = lambda P: F(0.007) * np.sin(np.arctan2(P[:, 0], -(P[:, 1] - F(0.04))) * F(7) + P[:, 2] * F(9) + F(0.8) * NOISE(P * F(3))) \
        + F(0.0015) * NOISE(P * F(25))
    def cloth(P):
        d = base.eval(P, margin=0.14)
        return np.maximum(d - (F(0.055) - folds(P)), F(0.031) - d)          # (just over the chiton, 0.006-0.03)
    fd.add(Inter(Func(cloth, (-0.8, -0.65, 0.3), (0.8, 0.65, 1.7)), Func(_drape, (-1, -1, 0.3), (1, 1, 1.7)), 0.008), 0.0)
    # the roll along its top edge round her waist (hugging her: a soft roll, not a hoop)
    def roll(P):
        z = P[:, 2]
        return np.abs(z - (F(0.9) + F(0.05) * P[:, 0])) - F(0.023)
    fd.add(Inter(Shell(base, 0.055, 0.022, pad=0.14), Func(roll, (-1, -1, 0.7), (1, 1, 1.1)), 0.008), 0.006)
    fd.paint(Func(lambda P: np.abs(_drape(P) + F(0.022)) - F(0.022), (-1, -1, 0.3), (1, 1, 1.7)), 5)
    fd.paint(Func(lambda P: np.abs(_drape(P) + F(0.052)) - F(0.004), (-1, -1, 0.3), (1, 1, 1.7)), 6)
    return fd


def gold_field():
    """The girdle (a double gold cord under her breasts, knotted in front), the pins along her sleeves, the brooch on her
    left shoulder, a bracelet on each wrist, earrings."""
    fd = Field("Gold")
    base = dress_base()
    for dz in (0.0, 0.022):
        fd.add(Inter(Shell(base, 0.042, 0.012, pad=0.1), Func(lambda P, dz=dz: np.abs(P[:, 2] - F(GIRDLE_Z + dz)) - F(0.0065), (-1, -1, 0.9), (1, 1, 1.2)), 0.003), 0.0)
    kp, ok = ray_hit(Func(lambda P: base.eval(P) - F(0.055), (-1, -1, 0.8), (1, 1, 1.3)), [v3((0.0, -0.7, GIRDLE_Z + 0.011))], [v3((0, 1, 0))], tmax=0.9)
    if ok[0]:
        k0 = kp[0]
        fd.add(Ellipsoid(k0, (0.022, 0.012, 0.02)), 0.004)
        for dx in (-1, 1):
            fd.add(Chain([k0, k0 + v3((dx * 0.012, -0.004, -0.05)), k0 + v3((dx * 0.016, -0.002, -0.11))], [0.006, 0.0055, 0.005], k=0.003), 0.003)
            fd.add(Sphere(k0 + v3((dx * 0.016, -0.002, -0.115)), 0.01), 0.003)
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ua = RoundCone(sh, el, 0.072, 0.054)
        for t in (0.25, 0.5, 0.75):
            c = lerp(sh, el, t)
            h, ok = ray_hit(Func(lambda P: ua.sdf(P) - F(0.035), c - 0.3, c + 0.3), [c + v3((0, 0, 0.3))], [v3((0, 0, -1))], tmax=0.4)
            if ok[0]:
                fd.add(Sphere(h[0], 0.011), 0.0)
        wr, el2 = J["wrist_" + side], J["elbow_" + side]
        ax = norm(wr - el2)
        cc = lerp(el2, wr, 0.88)
        fore = RoundCone(el2, wr, 0.054, 0.042)
        fd.add(Inter(Shell(fore, 0.008, 0.008, pad=0.05), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.008), cc - 0.2, cc + 0.2), 0.002), 0.0)
        fd.add(Inter(Shell(fore, 0.008, 0.008, pad=0.05), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F) + F(0.025)) - F(0.006), cc - 0.2, cc + 0.2), 0.002), 0.0)
    # the brooch pinning the mantle on her left shoulder: a disc with a rosette
    bp, ok = ray_hit(Func(lambda P: base.eval(P) - F(0.09), (-1, -1, 0.8), (1, 1, 1.7)), [v3((0.2, -0.6, 1.33))], [v3((0, 1, 0))], tmax=0.9)
    if ok[0]:
        c = bp[0]
        fd.add(Cylinder(c, 0.03, 0.01, rr=0.003, R=rot_from_axes(z_axis=(0, -1, 0.2))), 0.0)
        for k in range(8):
            a = 2 * math.pi * k / 8
            fd.add(Sphere(c + v3((math.cos(a) * 0.02, -0.006, math.sin(a) * 0.02)), 0.006), 0.002)
    for sx in (-1, 1):
        fd.add(Torus(hp((sx * 0.182, 0.02, 1.59)), hr(0.014), hr(0.0035), R=rot_from_axes(z_axis=(1, 0, 0))), 0.0)
    return fd


def leather_field():
    """Sandals: soles, a thong between the toes, straps over the instep and round the ankle."""
    fd = Field("Leather")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.07 + v3((0, 0, -0.09)), (0.066, 0.145, 0.011), 0.008, R=Rz), 0.0)
        ft = Field("FootHull")
        foot(ft, side)
        for c2, rad in ((an + fwd * 0.1 + v3((0, 0, -0.05)), 0.016), (an + fwd * 0.02 + v3((0, 0, -0.02)), 0.018)):
            fd.add(Inter(Shell(ft, 0.005, 0.009, pad=0.05), Func(lambda P, c=c2, fwd=fwd, rad=rad: np.abs((P - c.astype(F)) @ fwd.astype(F)) - F(rad * 0.6), c2 - 0.15, c2 + 0.15), 0.003), 0.002)
        fd.add(Torus(an + v3((0, 0.004, 0.03)), 0.058, 0.007), 0.003)
    return fd


# ======================================================================================= the laurel sprig (right fist)
def laurel_axis():
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t


LAUREL_L = 0.44


def laurel_field():
    """A sprig of laurel: a slender twig (label 7) curving a little, long pointed leaves (0) in alternate pairs up its
    upper two thirds, a tuft at the tip."""
    fd = Field("Laurel")
    a0, ax = laurel_axis()
    wr, f, n, t = hand_frame("R")
    up = norm(np.cross(ax, n))
    side = norm(np.cross(ax, up))
    ss = np.linspace(-0.07, LAUREL_L, 12)
    pts = [a0 + ax * s + up * (0.04 * (max(0.0, s) / LAUREL_L) ** 2) for s in ss]
    fd.add(Chain(pts, [0.009 - 0.005 * max(0.0, s) / LAUREL_L for s in ss], k=0.004), 0.0, 7)
    leafy = lambda P: F(0.0008) * NOISE(P * F(60))
    for i, s in enumerate(np.linspace(0.12, LAUREL_L - 0.02, 9)):
        c0 = a0 + ax * s + up * (0.04 * (s / LAUREL_L) ** 2)
        for sgn in (-1, 1):
            rot = 0.3 * i + (0.0 if sgn > 0 else math.pi)
            out = norm(side * math.cos(rot) + up * math.sin(rot))
            ld = norm(out + ax * 0.9)
            face = norm(np.cross(ax, out))                                      # the leaf lies flat beside the twig
            fd.add(Ellipsoid(c0 + ld * 0.035, (0.013, 0.004, 0.038), R=rot_from_axes(z_axis=ld, y_axis=face), disp=leafy, disp_amp=0.001), 0.003, 0)
    tip = pts[-1]
    for k in range(3):
        d = norm(ax + (side * math.cos(k * 2.1) + up * math.sin(k * 2.1)) * 0.35)
        fd.add(Ellipsoid(tip + d * 0.03, (0.004, 0.011, 0.032), R=rot_from_axes(z_axis=d, y_axis=up if abs(d @ up) < 0.9 else side)), 0.003, 0)
    return fd


# ======================================================================================= the tripod
TRIPOD = v3((0.5, -0.44, 0.0))       # where it stands (centre)
BOWL_Z = 0.98                         # the cauldron's rim
BOWL_R = 0.19
LEG_TOP_R = 0.15
LEG_FOOT_R = 0.3
EMBER_Z = BOWL_Z - 0.035


def tripod_field():
    """Bronze: three slender legs (each a rod with a raised moulding) on lion's paws, a brace ring halfway up, a ring
    under the cauldron; the cauldron deep and round with a rolled rim and two upright ring handles."""
    fd = Field("Tripod")
    c = TRIPOD
    for k in range(3):
        a = math.radians(90 + 120 * k)
        d = v3((math.cos(a), math.sin(a), 0.0))
        top = c + d * LEG_TOP_R + v3((0, 0, BOWL_Z - 0.17))
        foot_p = c + d * LEG_FOOT_R + v3((0, 0, 0.06))
        fd.add(RoundCone(foot_p, top, 0.016, 0.013), 0.0)
        fd.add(Sphere(lerp(foot_p, top, 0.62), 0.022), 0.008)                              # a moulding
        # the lion's paw: a rounded pad with four toes, turned outward
        paw = c + d * (LEG_FOOT_R + 0.02) + v3((0, 0, 0.03))
        fd.add(Ellipsoid(paw, (0.04, 0.04, 0.03), R=rot_from_axes(z_axis=(0, 0, 1), x_axis=d)), 0.012)
        tng = v3((-d[1], d[0], 0))
        for j in range(4):
            o = (j - 1.5) * 0.018
            fd.add(Sphere(paw + d * 0.034 + tng * o + v3((0, 0, -0.012)), 0.013), 0.006)
        fd.add(RoundCone(lerp(foot_p, top, 0.4), c + v3((0, 0, (BOWL_Z - 0.17) * 0.4 + 0.05)), 0.008, 0.008), 0.006)
    hz = (BOWL_Z - 0.17) * 0.4 + 0.05
    fd.add(Torus(c + v3((0, 0, hz)), 0.05, 0.012), 0.006)                                    # the brace's hub
    fd.add(Torus(c + v3((0, 0, BOWL_Z - 0.17)), LEG_TOP_R, 0.014), 0.006)                   # the ring under the cauldron
    bowl = Ellipsoid(c + v3((0, 0, BOWL_Z - 0.02)), (BOWL_R, BOWL_R, 0.17))
    fd.add(Inter(Shell(bowl, 0.0, 0.016, pad=0.04), Plane(c + v3((0, 0, BOWL_Z)), (0, 0, 1)), 0.004), 0.006)
    fd.add(Torus(c + v3((0, 0, BOWL_Z)), BOWL_R - 0.004, 0.014), 0.004)                     # the rolled rim
    for s in (-1, 1):
        hc = c + v3((s * (BOWL_R - 0.01), 0, BOWL_Z + 0.075))
        fd.add(Torus(hc, 0.06, 0.011, R=rot_from_axes(z_axis=(0, 1, 0))), 0.0)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(BOWL_Z - 0.05)) - F(0.012), c - 0.3, c + v3((0.3, 0.3, 1.2))), 5)   # a band
    return fd


def embers_field():
    """The embers heaped in the cauldron (glowing: their own mesh in game)."""
    fd = Field("Embers")
    fd.add(Ellipsoid(TRIPOD + v3((0, 0, EMBER_Z - 0.03)), (BOWL_R - 0.03, BOWL_R - 0.03, 0.045),
                     disp=lambda P: F(0.006) * NOISE(P * F(25)), disp_amp=0.008), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.23, 1.624)), 0.04, 0.35)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.1, -0.15, 1.6)), 0.06, 0.4), (hp((sx * 0.176, 0.035, 1.66)), 0.05, 0.45),
                (J["elbow_" + sd] + v3((0, 0.022, 0)), 0.05, 0.2)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.01, 0.028, 0.4))
    return pts


# ======================================================================================= build config
GLB_NAME = "oracle"
ROOT_NAME = "OracleHQ"
TEX_PREFIX = "oracle"
MAT_NAME = "OracleMat"
MESH_NAME = "Oracle"
BASE_MODULE = "oracle_base"
ANIM_MODULE = "anim_oracle"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Veil", "Wreath", "Chiton", "Himation", "Gold", "Leather", "Laurel", "Tripod", "Embers"]
REGION_PARTS = ("Skin", "Hair", "Veil", "Wreath", "Himation", "Laurel", "Tripod")
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_OracleSkin", "base": (0.8, 0.58, 0.44), "ruddy": (0.82, 0.5, 0.42), "lips": (0.66, 0.36, 0.33),
                      "brow": ((0.07, 0.05, 0.05), (0.16, 0.12, 0.1)),
                      "extra": ((LASH, (0.04, 0.03, 0.03), 0.7),)}),
    "Hair": ("hair", {"name": "HQ_OracleHair", "base": (0.1, 0.075, 0.065), "hi": (0.32, 0.25, 0.22), "low": (0.04, 0.03, 0.028),
                      "streak": (0.62, 0.6, 0.58), "tint": (0.18, 0.12, 0.1)}),
    "Veil": ("linen", {"name": "HQ_Veil", "base": (0.95, 0.93, 0.88), "border": (0.42, 0.18, 0.5), "stripe": (0.42, 0.18, 0.5)}),
    "Wreath": ("leafy", {"name": "HQ_Laurel", "leaf": (0.17, 0.32, 0.12), "vein": (0.36, 0.5, 0.2)}),
    "Laurel": ("leafy", {"name": "HQ_Laurel", "leaf": (0.17, 0.32, 0.12), "vein": (0.36, 0.5, 0.2)}),
    "Chiton": ("linen", {"name": "HQ_Chiton", "base": (0.95, 0.93, 0.88)}),
    "Himation": ("wool", {"name": "HQ_Himation", "base": (0.86, 0.6, 0.16), "border": (0.36, 0.14, 0.44), "stripe": (0.2, 0.08, 0.24)}),
    "Gold": ("gold", {"name": "HQ_OracleGold"}),
    "Leather": ("leather", {"name": "HQ_OracleSandals", "base": (0.42, 0.26, 0.14)}),
    "Tripod": ("bronze", {"name": "HQ_Tripod"}),
    "Embers": ("coals", {"name": "HQ_Embers"}),
}
GLOW = {"Embers": ((1.0, 0.5, 0.14), 1.0, 0.6)}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Hair": 1500, "Veil": 1500, "Wreath": 1100, "Chiton": 2800, "Himation": 2200,
               "Gold": 900, "Leather": 500, "Laurel": 700, "Tripod": 2200, "Embers": 300}
AO_EXCLUDE = ["Laurel", "Embers"]
# the tripod is baked away from her: her left hand hangs near it in the rest pose
BAKE_APART = (["Tripod", "Embers"], (3.0, 0.0, 0.0))


YAW_PIVOT = (0.25, -0.22, 0.0)      # the tower turns about this point (between her and the tripod)


def prop_bones():
    return []                       # the laurel is rigid in her right fist


def extra_bones():
    """The tripod stands on its own (it never moves); the embers' bone lets game.gd find the bowl."""
    return [("props", TRIPOD, TRIPOD + v3((0, 0, 0.3)), None),
            ("embers", TRIPOD + v3((0, 0, EMBER_Z)), TRIPOD + v3((0, 0, EMBER_Z + 0.15)), "props")]


def hair_weights(ob, skin_ob, arm):
    groups = {}
    z1 = hp((0, 0, 1.58))[2]
    for v in ob.data.vertices:
        p = v.co
        t = max(0.0, min(1.0, (z1 - p.z) / 0.15))
        _blend_add(ob, groups, v.index, {"head": 1.0 - 0.5 * t, "neck": 0.5 * t})


def veil_weights(ob, skin_ob, arm):
    """The veil rides her head at the top and her shoulders and back at its hem."""
    groups = {}
    z_head = hp((0, 0, 1.6))[2]
    for v in ob.data.vertices:
        p = v.co
        if p.z > z_head:
            w = {"head": 1.0}
        else:
            t = max(0.0, min(1.0, (z_head - p.z) / (z_head - 1.2)))
            w = {"head": 1.0 - t, "neck": 0.5 * t * (1.0 - t) * 2.0, "chest": t}
            s = sum(w.values())
            w = {k: x / s for k, x in w.items()}
        _blend_add(ob, groups, v.index, w)


def gold_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R",
                                                      "forearm.L", "hand.R", "hand.L", "head"})
    groups = {}
    for v in ob.data.vertices:
        if v.co.z > hp((0, 0, 1.5))[2] and abs(v.co.x) > 0.15 and abs(v.co.x) < 0.25:      # earrings
            for g in list(ob.vertex_groups):
                g.remove([v.index])
            _blend_add(ob, groups, v.index, {"head": 1.0})


def weight_rules():
    skirt = {"thigh.R": 0.5, "thigh.L": 0.5, "shin.R": 0.35, "shin.L": 0.35}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("custom", hair_weights), "Wreath": ("rigid", "head"),
        "Veil": ("custom", veil_weights),
        "Chiton": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L", "shin.R",
                                        "shin.L"}, skirt),
        "Himation": ("transfer", TORSO | {"clavicle.L", "upperarm.L", "thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45,
                                                                                             "upperarm.L": 0.6}),
        "Gold": ("custom", gold_weights),
        "Leather": ("transfer", {"foot.R", "foot.L", "shin.R", "shin.L"}, None),
        "Laurel": ("rigid", "hand.R"), "Tripod": ("rigid", "props"), "Embers": ("rigid", "embers"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Tripod", "Embers"):
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Veil", veil_field(), 0.0024 if fine else 0.0034),
        ("Wreath", wreath_field(), 0.0016 if fine else 0.0022),
        ("Chiton", chiton_field(), 0.0026 if fine else 0.0036),
        ("Himation", himation_field(), 0.0026 if fine else 0.0036),
        ("Gold", gold_field(), 0.0016 if fine else 0.0022),
        ("Leather", leather_field(), 0.002 if fine else 0.0028),
        ("Laurel", laurel_field(), 0.0016 if fine else 0.0022),
        ("Tripod", tripod_field(), 0.0024 if fine else 0.0032),
        ("Embers", embers_field(), 0.003 if fine else 0.004),
    ]
