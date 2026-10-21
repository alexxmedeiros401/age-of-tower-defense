"""Theron of Delphi, Oracle Sage (HQ hero, Classical Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

An old seer of Apollo's sanctuary: tall and lean (the Druid's build, druid.py), a high bald dome with three creases
across it, bushy white brows arched in thought, deep-set grey eyes, a broad snub nose, full cheeks; tight snail curls of
grey-white hair round the back and sides of his head, and a full rounded beard of the same curls to his upper chest
under a heavy moustache; a wreath of gold laurel on his brow. An ankle-length chiton of fine white linen, finely
pleated, its short sleeves to his elbows; over it a himation of saffron wool with a dark red border, wrapped round his
hips to his shins and thrown up across his chest over his left shoulder, falling down his back, pinned at the shoulder
with a gold disc brooch; sandals. In his right fist a straight staff of olive wood (its grain twisting), crowned with a
gold sun: a disc ringed by twelve rays, an open eye at its middle whose iris glows (its own glowing mesh, on the `gem`
bone). His left hand is open (it reads the air).

The staff is rigid in his right fist ("frame" aims in anim_theron.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import druid as dr
from druid import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S, fist_center,
                   hand, foot, skull, torso_prims, traps, neck_prim, deltoid, upper_arm, eyes_field, teeth_field, TORSO, TORSO_Z,
                   torso_bones, _seg_dist, staff_axis, staff_frame, STAFF_R)

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, SPOT = 0, 1, 2, 3, 4, 5, 8, 9


# ======================================================================================= head
def head(fd):
    """The Druid's skull with a philosopher's face: full cheeks, a broad snub nose, brows arched in thought."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.8), (0.158, 0.17, 0.116)), 0.08, SKIN)                            # the high bald dome
    fd.add(E((0, -0.06, 1.585), (0.122, 0.122, 0.12)), 0.07, SKIN)                          # a broad jaw (under the beard)
    fd.add(E((0, -0.138, 1.5), (0.07, 0.058, 0.066)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.106, -0.13, 1.64), 0.042), 0.05, SKIN)                             # full round cheeks
        fd.add(S((sx * 0.11, -0.05, 1.56), 0.038), 0.05, SKIN)
        pts = [hp((sx * 0.152, -0.055, 1.744)), hp((sx * 0.115, -0.132, 1.758)), hp((sx * 0.06, -0.176, 1.758)), hp((0.0, -0.186, 1.752))]
        fd.add(Chain(pts, [hr(0.012), hr(0.019), hr(0.022), hr(0.02)], k=hr(0.022)), hr(0.03), SKIN)      # brow ridge
        fd.sub(Ellipsoid(hp((sx * 0.148, -0.08, 1.735)), v3((0.018, 0.026, 0.028)) * HS), hr(0.02))       # temples
    sk = skull()
    for zc, w in ((1.8, 0.075), (1.826, 0.085), (1.852, 0.08)):                             # creases across the dome
        pts = []
        for k in range(9):
            x = -w + 2 * w * k / 8
            h, ok = ray_hit(sk, [hp((x, -0.6, zc + 0.016 * (x / w) ** 2 - 0.004 * math.cos(x * 30)))], [v3((0, 1, 0))], tmax=0.7)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 3:
            fd.sub(Chain(pts, [hr(0.0024)] * len(pts), k=0.002), hr(0.003))
    for sx in (-1, 1):
        for k in range(3):                                                                  # crow's feet
            a = hp((sx * (0.11 + 0.004 * k), -0.128 + 0.006 * k, 1.68 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.024, 0.012, 0.006 - 0.01 * k)), hr(0.0021), hr(0.0014)), hr(0.003))
        fd.add(Ellipsoid(hp((sx * 0.07, -0.15, 1.646)), v3((0.026, 0.012, 0.011)) * HS), hr(0.012), SKIN)  # bags under the eyes
    # bushy white brows, arched high in the middle (he is listening to something far off)
    brow_tuft = lambda P: F(0.0025) * NOISE(P * F(160)) + F(0.0012) * np.sin(P[:, 0] * F(400))
    for sx in (-1, 1):
        pts = [hp((sx * 0.022, -0.212, 1.758)), hp((sx * 0.062, -0.206, 1.784)), hp((sx * 0.106, -0.188, 1.79)),
               hp((sx * 0.146, -0.152, 1.778)), hp((sx * 0.17, -0.12, 1.76))]
        fd.add(Chain([p + v3((0, -0.002, 0)) for p in pts], [hr(0.011), hr(0.015), hr(0.015), hr(0.011), hr(0.005)], k=hr(0.008),
                     disp=brow_tuft, disp_amp=0.003), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.022), hr(0.026), hr(0.025), hr(0.02), hr(0.011)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.013))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, -hr(0.02))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0105))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
    # a broad snub nose: a short bridge, a round bulb, wide nostrils
    fd.add(RoundCone(hp((0, -0.186, 1.728)), hp((0, -0.228, 1.64)), hr(0.017), hr(0.024)), hr(0.016), SKIN)
    fd.add(S((0, -0.236, 1.622), 0.03), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.034, -0.214, 1.608), 0.021), hr(0.011), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.018, -0.236, 1.597)), v3((0.009, 0.011, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    slot = [hp((-0.05, -0.17, 1.548)), hp((-0.026, -0.19, 1.542)), hp((0, -0.196, 1.541)), hp((0.026, -0.19, 1.542)), hp((0.05, -0.17, 1.548))]
    fd.sub(Chain(slot, [hr(0.0022), hr(0.003), hr(0.0033), hr(0.003), hr(0.0022)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.003)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.042, -0.17, 1.54), (-0.022, -0.186, 1.531), (0, -0.19, 1.529), (0.022, -0.186, 1.531), (0.042, -0.17, 1.54)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0066), hr(0.0072), hr(0.0066), hr(0.004)], k=hr(0.006)), hr(0.008), LIP)
    for sx in (-1, 1):                                                                      # big ears (the curls behind them)
        fd.add(Ellipsoid(hp((sx * 0.177, 0.032, 1.655)), v3((0.028, 0.05, 0.068)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.196, 0.026, 1.66)), v3((0.012, 0.032, 0.044)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
    rs = np.random.RandomState(7)
    for k in range(6):                                                                      # age spots on the dome
        x, z = rs.uniform(-0.1, 0.1), rs.uniform(1.82, 1.9)
        h, ok = ray_hit(sk, [hp((x, -0.6, z))], [v3((0, 1, 0))], tmax=0.7)
        if ok[0]:
            fd.paint(Sphere(h[0], hr(rs.uniform(0.006, 0.01))), SPOT)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.05, SKIN)
        fd.add(upper_arm(side), 0.045, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.02, 0)), (0.07, 0.072, 0.11), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(RoundCone(el, wr, 0.058, 0.044), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.07, 0.063, 0.115), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.022, 0)), 0.048), 0.025, SKIN)
        fd.add(Sphere(wr + v3((sx * 0.012, 0.0, 0.006)), 0.03), 0.02, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.115, 0.078), 0.06, SKIN)
        fd.add(Sphere(kn + v3((0, -0.028, 0.0)), 0.06), 0.035, SKIN)
        fd.add(RoundCone(kn, an, 0.07, 0.048), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.028, 0)), (0.078, 0.075, 0.125), R=rot_from_axes(z_axis=an - kn)), 0.04, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= curls: hair and beard
def head_hull(extra=0.0):
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD + extra), 0.0)
    fd.add(Ellipsoid(hp((0, 0.02, 1.8)), v3((0.158, 0.17, 0.116)) * HS + extra), 0.08)
    return fd


def hair_keep(P):
    """< 0 where the hair grows: round the back and sides of his head below the bald dome, behind his ears, to his
    nape."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    crown = z - (F(1.785) + F(0.05) * smoothstep(0.0, 0.2, y))                    # the bald dome above
    front = (F(-0.07) + F(0.05) * smoothstep(1.72, 1.62, z)) - y                  # back from his temples
    ear = np.where((ax > F(0.14)) & (z < F(1.73)) & (z > F(1.57)), F(0.07) - y, F(-1.0))
    nape = (F(1.53) + F(0.02) * np.sin(x * F(40))) - z
    return np.maximum(np.maximum(np.maximum(crown, front), ear), nape)


def _fib_dirs(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)


def _curl(fd, p, n, r, k=0.006):
    """A snail curl: a round knob with a dimple spiralling into its middle."""
    fd.add(Sphere(p + n * r * 0.25, r), k)
    fd.sub(Sphere(p + n * r * 1.25, r * 0.38), r * 0.25)


def hair_field():
    """Tight snail curls of grey-white hair round the back and sides of his head (the dome bare above them)."""
    fd = Field("Hair")
    hull = head_hull(0.01)
    lo, hi = HEAD_C - 0.4, HEAD_C + 0.4
    fd.add(Inter(Shell(hull, 0.006, 0.024, pad=0.06), Func(hair_keep, lo, hi), 0.004), 0.0)
    surf = Func(lambda P: hull.eval(P, margin=0.06) - F(0.014), lo, hi)
    dirs = _fib_dirs(420)
    o = HEAD_C[None, :] + dirs * 0.6
    h, ok = ray_hit(surf, o, -dirs, tmax=0.7)
    for p, d, good in zip(h, dirs, ok):
        if not good or hair_keep(p[None, :].astype(F))[0] > 0.002:   # (curls to the hair's edge: no smooth rim)
            continue
        _curl(fd, p, norm(v3(d)), 0.0165)
    return fd


def beard_hull():
    return dr.beard_hull()


def beard_mask(P):
    """< 0 inside the beard: round his jaw and up his cheeks into the hair, his lips left clear, down to his upper
    chest."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.56) + F(0.1) * smoothstep(0.05, 0.14, ax)
    top = np.where(ax > F(0.15), F(1.66), top)
    lips = (x / F(0.062)) ** 2 + ((y + F(0.178)) / F(0.07)) ** 2 + ((z - F(1.543)) / F(0.024)) ** 2 - F(1.0)
    back = np.where(ax > F(0.13), y - F(0.03), y - F(0.0))
    return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), F(1.42) - z)


BEARD_LOBES = (((0, -0.17, 1.45), (0.122, 0.07, 0.075)), ((0, -0.19, 1.38), (0.098, 0.056, 0.07)))


def beard_field():
    """A full rounded beard of snail curls round his jaw, falling in a rounded mass to his upper chest; a heavy
    moustache drooping into it."""
    fd = Field("Beard")
    hull = beard_hull()
    fd.add(Inter(Shell(hull, 0.008, 0.024, pad=0.06), Func(beard_mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.006), 0.0)
    for c, r in BEARD_LOBES:
        fd.add(Ellipsoid(v3(c), r), 0.04)
    mass = Field("BeardMass")
    mass.add(Inter(Shell(hull, 0.008, 0.024, pad=0.06), Func(beard_mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.006), 0.0)
    for c, r in BEARD_LOBES:
        mass.add(Ellipsoid(v3(c), r), 0.04)
    surf = Func(lambda P: mass.eval(P, margin=0.05) - F(0.002), (-0.4, -0.5, 1.2), (0.4, 0.3, 1.8))
    # rows of curls all over it: its front, round his jaw to his ears and up his cheeks (rays in toward the beard's
    # middle); the curls may straddle its edge, so no smooth rim of beard shows round them
    rows = np.arange(1.32, 1.68, 0.026)
    rs = np.random.RandomState(11)
    for j, z0 in enumerate(rows):
        for a0 in np.arange(-2.4, 2.41, 0.2) + (0.1 if j % 2 else 0.0):
            a = a0 + rs.uniform(-0.05, 0.05)                    # (a little irregular: curls, not a pine cone)
            z = z0 + rs.uniform(-0.007, 0.007)
            d = v3((math.sin(a), -math.cos(a), 0.0))
            o = v3((0.0, -0.12, z)) + d * 0.5
            h, ok = ray_hit(surf, [o], [-d], tmax=0.6)
            if not ok[0]:
                continue
            p = h[0]
            if beard_mask(p[None, :].astype(F))[0] > 0.003 and p[2] > 1.44:
                continue
            _curl(fd, p, d, 0.0155 * rs.uniform(0.85, 1.12))
    # the moustache: two heavy locks from under the nose, drooping past his mouth into the beard
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.228, 1.583)), hp((sx * 0.048, -0.214, 1.568)), hp((sx * 0.074, -0.194, 1.536)),
               hp((sx * 0.084, -0.184, 1.5))]
        fd.add(Lock(pts, [hr(0.017), hr(0.023), hr(0.019), hr(0.011)], [hr(0.012), hr(0.014), hr(0.011), hr(0.007)],
                    [norm(v3((sx * 0.3, -1, 0.15)))] * 4, k=hr(0.006), disp=strands, disp_amp=0.003), hr(0.006))
    return fd


# ======================================================================================= the gold laurel wreath
WREATH_Z = 1.8           # its height at the front (design units); it dips a little at the back, over the curls


def wreath_d(P):
    Q = hinv(P)
    return Q[:, 2] - (F(WREATH_Z) - F(0.05) * smoothstep(-0.15, 0.2, Q[:, 1]))


def wreath_off(P):
    """How far out from the head the wreath sits: on the bald dome in front, on the curls behind."""
    return F(0.0) + F(0.036) * smoothstep(-0.1, 0.04, hinv(P)[:, 1])


def _laurel_sd(P, c, u, v, n, L, W):
    """A laurel leaf: a long pointed blade along u (half length L, half width W), a little cupped."""
    q = P - c.astype(F)
    s = q @ u.astype(F)
    t = q @ v.astype(F)
    h = q @ n.astype(F)
    k = np.clip(s / F(L), -1, 1)
    w = F(W) * np.power(np.maximum(F(1) - k * k, 0), F(0.75))
    cup = F(0.004) * (t / F(W)) ** 2
    d = np.maximum(np.abs(t) - w, np.abs(s) - F(L))
    return np.maximum(d, np.abs(h - cup) - F(0.0026))


def wreath_points(n=26):
    hull = head_hull()
    out = []
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        dirh = v3((math.sin(a), -math.cos(a), 0.0))
        z = WREATH_Z - 0.05 * (0.5 - 0.5 * math.cos(a)) + (0.012 if k % 2 else -0.012)
        o = hp((0, 0.03, z)) + dirh * 0.6
        surf = Func(lambda P: hull.eval(P, margin=0.08) - wreath_off(P) - F(0.008), HEAD_C - 0.5, HEAD_C + 0.5)
        h, ok = ray_hit(surf, [o], [-dirh], tmax=0.6)
        if not ok[0]:
            continue
        tang = v3((math.cos(a), math.sin(a), 0.0))
        sgn = 1.0 if a < math.pi else -1.0                     # both branches run forward to meet over his brow
        u = norm(-tang * sgn + v3((0, 0, 0.2 if k % 2 else -0.15)))
        out_n = norm(dirh + v3((0, 0, 0.3 if k % 2 else -0.1)))
        out.append((h[0], u, out_n))
    return out


def wreath_field():
    """Gold: a twig band round his head and long pointed laurel leaves along it, the two branches meeting over his brow,
    three berries where they meet."""
    fd = Field("Wreath")
    hull = head_hull()
    ring = Func(lambda P: np.abs(wreath_d(P)) - F(0.007), HEAD_C - 0.4, HEAD_C + 0.4)
    band = Func(lambda P: np.abs(hull.eval(P, margin=0.08) - wreath_off(P)) - F(0.006), HEAD_C - 0.5, HEAD_C + 0.5)
    fd.add(Inter(band, ring, 0.003), 0.0)
    for c, u, n in wreath_points():
        v = norm(np.cross(n, u))
        cc = c + u * 0.03
        fd.add(Func(lambda P, c=cc, u=u, v=v, n=n: _laurel_sd(P, c, u, v, n, 0.036, 0.012), cc - 0.06, cc + 0.06), 0.003)
    o = hp((0, -0.6, WREATH_Z + 0.004))
    h, ok = ray_hit(Func(lambda P: hull.eval(P, margin=0.08) - wreath_off(P) - F(0.012), HEAD_C - 0.5, HEAD_C + 0.5), [o], [v3((0, 1, 0))], tmax=0.7)
    if ok[0]:
        for dx, dz in ((-0.012, 0.0), (0.012, 0.0), (0.0, 0.014)):
            fd.add(Sphere(h[0] + v3((dx, -0.004, dz)), 0.0085), 0.002)
    return fd


# ======================================================================================= chiton, himation
def dress_base():
    b = Field("DressBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.05)
        b.add(upper_arm(side), 0.045)
    b.add(RoundCone((0, 0.03, 0.9), (0, 0.035, 0.12), 0.2, 0.28), 0.09)                  # to his ankles
    b.add(Ellipsoid((0, -0.02, 1.22), (0.19, 0.15, 0.16)), 0.08)                           # one smooth chest under the cloth
    return b


def hem_z(P):
    return F(0.13) + F(0.008) * NOISE(P * F(7))


def _sleeve(P, side):
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    ax = norm(el - sh)
    c = el - ax * 0.03
    sx = -1 if side == "R" else 1
    return np.where(P[:, 0] * F(sx) > F(0.27), (P - c.astype(F)) @ ax.astype(F), F(-1.0))


def chiton_field():
    """Fine white linen, closely pleated, to his ankles; short sleeves to his elbows."""
    fd = Field("Chiton")
    base = dress_base()
    def pleats(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        return F(0.0035) * np.abs(np.sin(a * F(30))) + F(0.001) * NOISE(P * F(30))
    def cloth(P):
        d = base.eval(P, margin=0.1)
        return np.maximum(d - (F(0.024) - pleats(P)), F(0.006) - d)
    def keep(P):
        neck = P[:, 2] - (F(1.47) + F(0.3) * smoothstep(0.14, 0.21, np.abs(P[:, 0])))
        k = np.maximum(hem_z(P) - P[:, 2], neck)
        return np.maximum(np.maximum(k, _sleeve(P, "R")), _sleeve(P, "L"))
    fd.add(Inter(Func(cloth, (-0.9, -0.6, 0.0), (0.9, 0.6, 1.7)), Func(keep, (-1, -1, 0.0), (1, 1, 1.7)), 0.004), 0.0)
    return fd


def _drape(P):
    """< 0 inside the himation: a broad band from his right hip up across his chest and back over his left shoulder, and
    a wrap round his hips to his shins."""
    x, z = P[:, 0], P[:, 2]
    n = norm(v3((-0.6, 0.0, 1.0)))
    s = (P - np.array([0.0, 0.0, 1.06], F)) @ n.astype(F)
    band = np.abs(s - F(0.04)) - F(0.14)
    wrap = np.maximum(F(0.3) + F(0.03) * np.sin(x * F(9)) - z, z - (F(0.96) - F(0.06) * x))
    return np.minimum(band, wrap)


def himation_field():
    """Saffron wool with a dark red border (label 5) and a thin dark stripe inside it (6), in broad folds; a thick roll
    along the wrap's top edge at his waist."""
    fd = Field("Himation")
    base = dress_base()
    folds = lambda P: F(0.008) * np.sin(np.arctan2(P[:, 0], -(P[:, 1] - F(0.04))) * F(7) + P[:, 2] * F(9) + F(0.8) * NOISE(P * F(3))) \
        + F(0.0015) * NOISE(P * F(25))
    def cloth(P):
        d = base.eval(P, margin=0.14)
        return np.maximum(d - (F(0.052) - folds(P)), F(0.027) - d)
    fd.add(Inter(Func(cloth, (-0.85, -0.65, 0.2), (0.85, 0.65, 1.75)), Func(_drape, (-1, -1, 0.2), (1, 1, 1.75)), 0.008), 0.0)
    def roll(P):                                   # (hugging his waist: a soft roll, not a hoop)
        return np.abs(P[:, 2] - (F(0.955) - F(0.06) * P[:, 0])) - F(0.024)
    fd.add(Inter(Shell(base, 0.05, 0.022, pad=0.14), Func(roll, (-1, -1, 0.8), (1, 1, 1.1)), 0.008), 0.006)
    fd.paint(Func(lambda P: np.abs(_drape(P) + F(0.024)) - F(0.024), (-1, -1, 0.2), (1, 1, 1.75)), 5)
    fd.paint(Func(lambda P: np.abs(_drape(P) + F(0.056)) - F(0.004), (-1, -1, 0.2), (1, 1, 1.75)), 6)
    return fd


def gold_field():
    """The disc brooch pinning the himation on his left shoulder (a rosette in a ring); a plain ring on his left hand."""
    fd = Field("Gold")
    base = dress_base()
    bp, ok = ray_hit(Func(lambda P: base.eval(P, margin=0.12) - F(0.09), (-1, -1, 0.8), (1, 1, 1.8)), [v3((0.22, -0.6, 1.36))], [v3((0, 1, 0))], tmax=0.9)
    if ok[0]:
        c = bp[0]
        n = norm(v3((0.15, -1.0, 0.3)))
        R = rot_from_axes(z_axis=n)
        fd.add(Cylinder(c, 0.032, 0.01, rr=0.003, R=R), 0.0)
        fd.add(Torus(c + n * 0.005, 0.028, 0.004, R=R), 0.002)
        for k in range(8):
            a = 2 * math.pi * k / 8
            fd.add(Sphere(c + R @ v3((math.cos(a) * 0.016, math.sin(a) * 0.016, 0.006)), 0.0065), 0.002)
        fd.add(Sphere(c + n * 0.008, 0.008), 0.002)
    wr, f, nn, t = hand_frame("L")
    p = wr + f * 0.17 * HAND_S - t * 0.0135 * HAND_S - nn * 0.004
    fd.add(Torus(p, 0.0135, 0.0035, R=rot_from_axes(z_axis=f)), 0.0)
    return fd


def leather_field():
    """Sandals: a sole, a thong between the toes, straps across the instep and round the ankle."""
    fd = Field("Leather")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.074 + v3((0, 0, -0.1)), (0.07, 0.15, 0.011), 0.009, R=Rz), 0.0)
        ft = Field("FootHull")
        foot(ft, side)
        for c, rad in ((an + fwd * 0.15 + v3((0, 0, -0.07)), 0.02), (an + fwd * 0.06 + v3((0, 0, -0.035)), 0.02)):
            fd.add(Inter(Shell(ft, 0.006, 0.01, pad=0.05), Func(lambda P, c=c, fwd=fwd, rad=rad: np.abs((P - c.astype(F)) @ fwd.astype(F)) - F(rad * 0.6),
                                                             c - 0.15, c + 0.15), 0.003), 0.002)
        fd.add(Inter(Shell(ft, 0.006, 0.01, pad=0.05), Func(lambda P, an=an: np.abs(P[:, 2] - F(an[2] + 0.005)) - F(0.008), an - 0.2, an + 0.2), 0.003), 0.002)
    return fd


# ======================================================================================= the staff and its sun
STAFF_BACK = 1.04          # grip -> the butt
SUN_S = 0.68               # grip -> the sun's middle
SUN_R = 0.07
EYE_W = 0.032              # the eye's half width


def sun_frame():
    """The sun's middle, the staff's axis, the disc's face (toward the knuckles' side) and its across."""
    a0, ax, u, w = staff_frame()
    return a0 + ax * SUN_S, ax, u, w


def staff_field():
    """Olive wood (bark_wood: the bare wood, label 0, its grain twisting round the shaft), worn smooth where he grips it
    (5); a socket under the sun."""
    fd = Field("Staff")
    a0, ax, u, w = staff_frame()
    twist = lambda P: F(0.0022) * np.sin(np.arctan2((P - a0.astype(F)) @ w.astype(F), (P - a0.astype(F)) @ u.astype(F)) * F(5)
                                         + ((P - a0.astype(F)) @ ax.astype(F)) * F(14)) + F(0.0012) * NOISE(P * F(60))
    def bend(s):
        return u * (0.006 * math.sin(s * 4.0 + 0.4)) + w * (0.005 * math.sin(s * 3.1 + 1.1))
    pts, rads = [], []
    for k in range(13):
        s = -STAFF_BACK + (SUN_S - SUN_R - 0.02 + STAFF_BACK) * k / 12
        pts.append(a0 + ax * s + bend(s))
        rads.append(STAFF_R * (1.04 - 0.1 * (k / 12)))
    fd.add(Chain(pts, rads, k=0.006, disp=twist, disp_amp=0.003), 0.0)
    fd.add(Sphere(a0 - ax * STAFF_BACK + bend(-STAFF_BACK), STAFF_R * 1.04), 0.008)
    fd.paint(Func(lambda P: np.abs((P - a0.astype(F)) @ ax.astype(F)) - F(0.07), a0 - 0.2, a0 + 0.2), 5)
    return fd


def sun_field():
    """Gold: a socket on the staff's head, a disc ringed by twelve rays (long and short by turns), a raised rim, and the
    almond of an eye at its middle (its lids; the iris is the Gem)."""
    fd = Field("Sun")
    c, ax, u, w = sun_frame()
    R = rot_from_axes(z_axis=u, x_axis=w)
    fd.add(RoundCone(c - ax * (SUN_R + 0.05), c - ax * (SUN_R - 0.01), STAFF_R * 1.1, STAFF_R * 1.4), 0.0)
    fd.add(Torus(c - ax * (SUN_R + 0.03), STAFF_R * 1.15, 0.005, R=rot_from_axes(z_axis=ax)), 0.003)
    fd.add(Cylinder(c, SUN_R, 0.016, rr=0.005, R=R), 0.004)
    fd.add(Torus(c + u * 0.006, SUN_R - 0.004, 0.006, R=R), 0.003)
    for k in range(12):
        a = 2 * math.pi * k / 12
        d = w * math.cos(a) + ax * math.sin(a)
        L = 0.06 if k % 2 == 0 else 0.038
        b = c + d * (SUN_R - 0.008)
        def ray(P, b=b, d=d, L=L):
            q = P - b.astype(F)
            s = q @ d.astype(F)
            side = norm(np.cross(u, d))
            t = q @ side.astype(F)
            h = q @ u.astype(F)
            wd = F(0.016) * np.clip(F(1) - s / F(L), 0, 1)
            return np.maximum(np.maximum(np.abs(t) - wd, np.maximum(-s, s - F(L))), np.abs(h) - F(0.005))
        fd.add(Func(ray, b - 0.1, b + 0.1), 0.004)
    # the eye: an almond-shaped rim (its lids) round a hollow where the glowing iris sits
    def lids(P):
        q = P - c.astype(F)
        x = q @ w.astype(F)
        y = q @ ax.astype(F)
        h = q @ u.astype(F)
        kx = np.clip(x / F(EYE_W), -1, 1)
        half = F(0.017) * (F(1) - kx * kx)
        almond = np.maximum(np.abs(y) - half, np.abs(x) - F(EYE_W))
        return np.maximum(np.abs(almond + F(0.004)) - F(0.004), np.abs(h - F(0.012)) - F(0.005))
    fd.add(Func(lids, c - 0.1, c + 0.1), 0.003)
    return fd


def gem_field():
    """The eye's glowing iris in the middle of the sun (its own glowing mesh)."""
    fd = Field("Gem")
    c, ax, u, w = sun_frame()
    fd.add(Ellipsoid(c + u * 0.008, (0.016, 0.016, 0.009), R=rot_from_axes(z_axis=u, x_axis=w)), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.236, 1.622)), 0.04, 0.6)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.106, -0.13, 1.64)), 0.05, 0.45), (hp((sx * 0.177, 0.032, 1.655)), 0.05, 0.55),
                (J["elbow_" + sd] + v3((0, 0.022, 0)), 0.05, 0.3)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.04, 0.0135, -0.0135, -0.04):
            pts.append((wr + f * 0.138 + t * o - n * 0.012, 0.028, 0.5))
    return pts


# ======================================================================================= build config
GLB_NAME = "theron"
ROOT_NAME = "HeroTheronHQ"
TEX_PREFIX = "hero"
MAT_NAME = "TheronMat"
MESH_NAME = "Theron"
BASE_MODULE = "theron_base"
ANIM_MODULE = "anim_theron"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Wreath", "Chiton", "Himation", "Gold", "Leather", "Staff", "Sun", "Gem"]
REGION_PARTS = ("Skin", "Himation", "Staff")
GREY = {"base": (0.78, 0.77, 0.74), "hi": (0.97, 0.96, 0.93), "low": (0.42, 0.41, 0.4), "streak": (0.6, 0.59, 0.57),
        "tint": (0.84, 0.82, 0.78)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_TheronSkin", "base": (0.8, 0.58, 0.44), "ruddy": (0.84, 0.48, 0.4), "lips": (0.62, 0.38, 0.34),
                      "brow": ((0.78, 0.77, 0.74), (0.96, 0.95, 0.92)),
                      "extra": ((LASH, (0.7, 0.68, 0.64), 0.6), (SPOT, (0.6, 0.42, 0.3), 0.6, 0.5))}),
    "Hair": ("hair", dict(name="HQ_TheronHair", **GREY)),
    "Beard": ("hair", dict(name="HQ_TheronHair", **GREY)),
    "Wreath": ("gold", {"name": "HQ_TheronGold"}),
    "Chiton": ("linen", {"name": "HQ_TheronChiton", "base": (0.94, 0.92, 0.86)}),
    "Himation": ("wool", {"name": "HQ_TheronHimation", "base": (0.86, 0.58, 0.14), "border": (0.5, 0.1, 0.07), "stripe": (0.3, 0.08, 0.05)}),
    "Gold": ("gold", {"name": "HQ_TheronGold"}),
    "Leather": ("leather", {"name": "HQ_TheronLeather", "base": (0.42, 0.26, 0.14)}),
    "Staff": ("bark_wood", {"name": "HQ_OliveStaff", "bark": (0.46, 0.4, 0.3), "wood": (0.72, 0.62, 0.44)}),
    "Sun": ("gold", {"name": "HQ_TheronGold"}),
    "Gem": ("glow_ball", {"name": "HQ_TheronEye", "col": (1.0, 0.86, 0.42)}),
}
GLOW = {"Gem": ((1.0, 0.84, 0.36), 1.0, 0.55)}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Hair": 2400, "Beard": 2400, "Wreath": 1400, "Chiton": 2600, "Himation": 2600, "Gold": 500,
               "Leather": 700, "Staff": 900, "Sun": 1100, "Gem": 120}
AO_EXCLUDE = ["Staff", "Sun", "Gem"]


def prop_bones():
    c, ax, u, w = sun_frame()
    return [("gem", c, c + ax * 0.1, "hand.R")]


def hair_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        _blend_add(ob, groups, v.index, {"head": 1.0})


def beard_weights(ob, skin_ob, arm):
    """The beard rides his jaw (the head); its lower mass blends into the neck and the chest it lies on."""
    groups = {}
    for v in ob.data.vertices:
        z = v.co.z
        k = min(1.0, max(0.0, (z - 1.32) / 0.2))
        k = k * k * (3 - 2 * k)
        w = {"head": max(k, 0.0)}
        if k < 1.0:
            w["neck"] = (1 - k) * 0.5
            w["chest"] = (1 - k) * 0.5
        _blend_add(ob, groups, v.index, w)


def gold_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        p = np.array(v.co)
        w = {"hand.L": 1.0} if abs(p[0]) > 0.5 else {"chest": 0.6, "clavicle.L": 0.4}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Wreath": ("rigid", "head"),
        "Hair": ("custom", hair_weights), "Beard": ("custom", beard_weights),
        "Chiton": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L", "shin.R", "shin.L"},
                   {"thigh.R": 0.4, "thigh.L": 0.4, "shin.R": 0.3, "shin.L": 0.3}),
        "Himation": ("transfer", TORSO | {"clavicle.L", "upperarm.L", "thigh.R", "thigh.L", "shin.R", "shin.L"},
                     {"upperarm.L": 0.5, "thigh.R": 0.4, "thigh.L": 0.4, "shin.R": 0.25, "shin.L": 0.25}),
        "Gold": ("custom", gold_weights),
        "Leather": ("transfer", {"foot.R", "foot.L", "shin.R", "shin.L"}, None),
        "Staff": ("rigid", "hand.R"), "Sun": ("rigid", "hand.R"), "Gem": ("rigid", "gem"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Beard", "Wreath", "Sun"):
        return 1.2
    if part == "Staff":
        return 0.6
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Beard", beard_field(), 0.0022 if fine else 0.0032),
        ("Wreath", wreath_field(), 0.0014 if fine else 0.002),
        ("Chiton", chiton_field(), 0.0026 if fine else 0.0036),
        ("Himation", himation_field(), 0.0028 if fine else 0.0038),
        ("Gold", gold_field(), 0.0014 if fine else 0.002),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Staff", staff_field(), 0.0018 if fine else 0.0026),
        ("Sun", sun_field(), 0.0014 if fine else 0.002),
        ("Gem", gem_field(), 0.0014 if fine else 0.002),
    ]
