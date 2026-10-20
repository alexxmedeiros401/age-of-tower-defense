"""Brenna Ironhide, Shieldmaiden (HQ hero, Iron Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A tall, strong young woman of a hill fort's war band: an open, freckled face set hard, straight brows drawn down, two
blue woad stripes across each cheekbone; copper-red hair parted in the middle and drawn back over her ears into two
thick braids that fall forward over her shoulders, bound at their ends with gold; a twisted gold torc. A shirt of iron
mail to mid-thigh with short sleeves (a band of bronze rings at its edges), belted with wide leather; blue checked
trousers bound with thongs; leather bracers, gold bracelets, shoes. A long ash spear with a leaf-shaped iron head in her
right fist; on her left a round shield of painted boards: blue, a white triskele wheeling round its iron boss, an iron
rim.

She has Kira's build (kira.py): her body comes from there, with both hands made fists (the spear, the shield's grip).
The spear and the shield are rigid in her fists ("frame" aims in anim_brenna.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import kira as kr
from kira import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S, foot,
                  fist_center, torso_prims, traps, neck_prim, deltoid, upper_arm, _forearm, eyes_field, teeth_field, TORSO,
                  TORSO_Z, torso_bones, hstripe)

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH = 0, 1, 2, 3, 4, 5, 8
CURLS = {"R": (1.45, 1.6, 1.2), "L": (1.45, 1.6, 1.2)}       # both fists: the spear, the shield's grip


# ======================================================================================= hands (both fists)
def hand(fd, side, s=HAND_S):
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.076 * s
    fd.add(RoundBox(c, v3((0.06, 0.03, 0.064)) * s, 0.028 * s, R=Rp), 0.027, SKIN)
    fd.add(Ellipsoid(c - n * 0.01 + t * 0.03 * s - f * 0.01, v3((0.033, 0.028, 0.05)) * s, R=Rp), 0.018, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.042, 0.014, -0.014, -0.042)
    lens = (0.97, 1.03, 0.97, 0.82)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.019 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.01, SKIN)
        fd.add(Sphere(pts[0] - n * 0.01, 0.014 * s), 0.009, SKIN)
        tipd = norm(pts[3] - pts[2])
        back = norm(np.cross(curl_ax, tipd))
        fd.paint(Ellipsoid(pts[3] - tipd * 0.006 - back * 0.01, (0.011, 0.0065, 0.014), R=rot_from_axes(z_axis=tipd, y_axis=back)), NAIL)
    tb = wr + f * 0.045 * s + t * 0.05 * s + n * 0.01
    d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
    d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.023 * s, 0.02 * s, 0.017 * s], k=0.008), 0.017, SKIN)


# ======================================================================================= head
def head(fd):
    """An open face set hard: a firm jaw, straight brows drawn down a little at their inner ends, a straight nose, a
    level mouth; two blue woad stripes across each cheekbone (freckles come from the skin's material)."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.06, 1.594), (0.141, 0.132, 0.126)), 0.07, SKIN)
    fd.add(E((0, -0.131, 1.505), (0.075, 0.066, 0.064)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.109, -0.118, 1.636), 0.04), 0.05, SKIN)
        fd.add(S((sx * 0.117, -0.05, 1.562), 0.046), 0.05, SKIN)
        pts = [hp((sx * 0.15, -0.06, 1.744)), hp((sx * 0.115, -0.13, 1.75)), hp((sx * 0.062, -0.164, 1.748))]
        fd.add(Chain(pts, [hr(0.011), hr(0.016), hr(0.014)], k=hr(0.02)), hr(0.03), SKIN)
    for sx in (-1, 1):
        pts = [hp((sx * 0.034, -0.201, 1.754)), hp((sx * 0.072, -0.196, 1.767)), hp((sx * 0.112, -0.174, 1.772)), hp((sx * 0.148, -0.134, 1.765))]
        fd.add(Chain([p + v3((0, 0.008, 0)) for p in pts], [hr(0.005), hr(0.0065), hr(0.0056), hr(0.0026)], k=hr(0.006)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.012), hr(0.014), hr(0.012), hr(0.006)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0058)), Plane(ec + v3((0, 0, hr(0.017))), (sx * 0.2, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0044)), Plane(ec + v3((0, 0, -hr(0.025))), (sx * -0.12, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.008)), Plane(ec + v3((0, 0, hr(0.014))), (sx * 0.2, 0.05, -1.0)), hr(0.002)), LASH)
    fd.add(RoundCone(hp((0, -0.178, 1.722)), hp((0, -0.217, 1.646)), hr(0.012), hr(0.016)), hr(0.016), SKIN)
    fd.add(S((0, -0.218, 1.635), 0.02), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.023, -0.2, 1.622), 0.014), hr(0.01), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.012, -0.213, 1.611)), v3((0.007, 0.009, 0.005)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    slot = [hp((-0.056, -0.166, 1.556)), hp((-0.029, -0.188, 1.548)), hp((0, -0.195, 1.546)), hp((0.029, -0.188, 1.548)),
            hp((0.056, -0.166, 1.556))]
    fd.sub(Chain(slot, [hr(0.0022), hr(0.003), hr(0.0034), hr(0.003), hr(0.0022)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0044), hr(0.0048), hr(0.0044), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.054, -0.163, 1.559), (-0.028, -0.181, 1.555), (0, -0.186, 1.557), (0.028, -0.181, 1.555), (0.054, -0.163, 1.559)]
    lo_lip = [(-0.046, -0.165, 1.548), (-0.024, -0.181, 1.536), (0, -0.185, 1.534), (0.024, -0.181, 1.536), (0.046, -0.165, 1.548)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.0038), hr(0.0066), hr(0.007), hr(0.0066), hr(0.0038)], k=hr(0.006)), hr(0.009), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.0045), hr(0.008), hr(0.0088), hr(0.008), hr(0.0045)], k=hr(0.007)), hr(0.009), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.174, 0.035, 1.66)), v3((0.024, 0.043, 0.054)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
    for sx in (-1, 1):                                            # woad: two stripes across each cheekbone
        for dz in (0.0, -0.026):
            fd.paint(hstripe((sx * 0.066, 1.634 + dz), (sx * 0.146, 1.648 + dz), 0.0075, 0.0045, y0=-0.5, y1=-0.04), PAINT)


# ======================================================================================= body
def leg_prims(side):
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(hip, kn, 0.122, 0.076), 0.06),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.02, 0)), (0.112, 0.103, 0.17), R=rot_from_axes(z_axis=kn - hip)), 0.045),
            (Sphere(kn + v3((0, -0.026, 0.0)), 0.06), 0.035),
            (RoundCone(kn, an, 0.074, 0.048), 0.035),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.028, 0)), (0.084, 0.082, 0.13), R=rot_from_axes(z_axis=an - kn)), 0.04)]


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
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.07, 0.072, 0.104), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(_forearm(side), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.073, 0.065, 0.11), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
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


# ======================================================================================= mail
BELT_Z = 0.93
HEM_Z = 0.56


def mail_base():
    b = Field("MailBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(RoundCone((0, 0.035, 0.88), (0, 0.035, 0.46), 0.235, 0.3), 0.08)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.05)
        b.add(upper_arm(side), 0.045)
    return b


def _neck_cut(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.03)) / F(0.18), 0, 1)
    neck_z = F(1.43) - F(0.05) * front * np.exp(-(x / F(0.11)) ** 2)
    return z - neck_z


def _sleeve_cut(P):
    """> 0 past the short sleeves (40% down the upper arm)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        c = lerp(sh, el, 0.4)
        along = (P - c.astype(F)) @ ax.astype(F)
        sx = -1 if side == "R" else 1
        lateral = P[:, 0] * F(sx) - F(0.26)
        out = np.maximum(out, np.where(lateral > 0, along, F(-1.0)))
    return out


def mail_hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(HEM_Z) + F(0.016) * np.cos(a * 2) + F(0.006) * NOISE(P * F(10))


def mail_field():
    """Iron mail from her neck to mid-thigh with short sleeves, gathered at the belt; a band of bronze rings (label 5)
    round the hem and the sleeves' ends."""
    fd = Field("Mail")
    base = mail_base()
    def shell(P):
        d = base.eval(P, margin=0.1)
        z = P[:, 2]
        below = np.clip((F(BELT_Z) - z) / F(0.12), 0, 1)
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        folds = F(0.005) * np.sin(a * F(11)) * below + F(0.0025) * NOISE(P * F(12))
        off = F(0.024) - F(0.01) * np.exp(-((z - F(BELT_Z)) / F(0.05)) ** 2) + folds + F(0.01) * below
        return np.abs(d - off) - F(0.0085)
    def keep(P):
        return np.maximum(np.maximum(_neck_cut(P), _sleeve_cut(P)), mail_hem(P) - P[:, 2])
    lo, hi = (-0.7, -0.45, 0.4), (0.7, 0.45, 1.58)
    fd.add(Inter(Func(shell, lo, hi), Func(keep, lo, hi), 0.004), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (mail_hem(P) + F(0.032)), (-0.6, -0.6, 0.4), (0.6, 0.6, 0.7)), 5)
    fd.paint(Func(lambda P: np.maximum(-_sleeve_cut(P) - F(0.032), F(1.0) - P[:, 2]), (-0.8, -0.5, 1.0), (0.8, 0.5, 1.5)), 5)
    return fd


def mail_point(x, z, off=0.034):
    """A point on the mail's outer surface in front of her, at (x, z) (a ray from the front)."""
    base = mail_base()
    h, ok = ray_hit(Func(lambda P: base.eval(P, margin=0.1) - F(off), (-0.8, -0.6, 0.3), (0.8, 0.6, 1.7)), [v3((x, -0.8, z))],
                    [v3((0, 1, 0))], tmax=0.9)
    return h[0] if ok[0] else v3((x, -0.2, z))


# ======================================================================================= hair: two braids
def braid_path(sx):
    """One braid's centre line (sx = +1 her left): from behind her ear, over her shoulder, down over her breast."""
    r = 0.024                                                    # (the braid's half-thickness)
    pts = [v3((sx * 0.135, 0.085, 1.585)), v3((sx * 0.172, 0.06, 1.5)), v3((sx * 0.196, 0.005, 1.43))]
    for x, z in ((0.19, 1.34), (0.168, 1.24), (0.152, 1.14), (0.146, 1.05)):
        pts.append(mail_point(sx * x, z, off=0.034 + r) + v3((0, 0.004, 0)))
    return pts


def braid_at(sx, t):
    path = braid_path(sx)
    n = len(path) - 1
    s = min(int(t * n), n - 1)
    u = t * n - s
    return lerp(path[s], path[s + 1], u), norm(path[s + 1] - path[s])


def hair_field():
    """Copper-red hair parted in the middle and drawn back smooth over her ears (grooves running back), gathered behind
    each ear into a thick three-strand braid that falls forward over her shoulder and down her front, ending in a
    tuft below a gold band."""
    fd = Field("Hair")
    hc, hrad = HEAD_C, HEAD_RAD
    cap = Ellipsoid(hc, hrad + 0.011)
    pfront, pback = hp((0, -0.156, 1.832)), hp((0, 0.215, 1.6))
    slope = (pback[2] - pfront[2]) / (pback[1] - pfront[1])
    hl_n = norm((0, slope, -1.0))
    def hairline(P):
        x = P[:, 0]
        temple = F(0.03) * smoothstep(0.08, 0.15, np.abs(x))                  # it recedes a little at the temples
        return ((P - pfront.astype(F)) @ hl_n.astype(F)) + temple + F(0.004) * NOISE(P * F(24))
    def ears(P):                                                              # (the hair covers the tops of her ears)
        Q = hinv(P)
        return np.where((np.abs(Q[:, 0]) > F(0.15)) & (Q[:, 2] < F(1.62)) & (Q[:, 1] < F(0.08)), F(0.02), F(-1.0))
    fd.add(Inter(cap, Func(lambda P: np.maximum(hairline(P), ears(P)), hc - 0.5, hc + 0.5), 0.02), 0.0)
    for sx in (-1, 1):                                                        # the hair swept back over each ear
        a = hp((sx * 0.16, -0.04, 1.71))
        b = hp((sx * 0.172, 0.06, 1.64))
        fd.add(Lock([a, b, braid_path(sx)[0]], [hr(0.05), hr(0.05), hr(0.04)], [hr(0.018), hr(0.02), hr(0.024)],
                    [v3((sx, 0, 0.2))] * 3, k=hr(0.012)), hr(0.02))
        fd.add(Ellipsoid(braid_path(sx)[0], (0.042, 0.04, 0.046)), hr(0.02))        # gathered behind the ear
    # the parting, and grooves combed back from it to each braid
    part = [hp((0.0, -0.16, 1.83)), hp((0.0, -0.06, 1.9)), hp((0.0, 0.05, 1.905))]
    fd.sub(Chain(part, [hr(0.0045)] * 3, k=0.002), hr(0.003))
    for sx in (-1, 1):
        tgt = norm(braid_path(sx)[0] - hc)
        for j in range(11):
            u0 = j / 10
            s0 = norm(v3((sx * 0.08, -1.0 + 1.3 * u0, 0.7 + 0.5 * math.sin(math.pi * u0))))
            pts = []
            for k in range(12):
                u = k / 11
                d = norm(s0 * (1 - u) + tgt * u + v3((sx * 0.25 * math.sin(math.pi * u), 0, 0.15 * math.sin(math.pi * u))))
                o = hc + d * 0.5
                h, ok = ray_hit(Func(lambda P: cap(P), hc - 0.5, hc + 0.5), [o], [-d], tmax=0.5)
                if ok[0]:
                    pts.append(h[0] + d * hr(0.001))
            pts = [p for p in pts if hairline(np.array([p], F))[0] < -0.006]
            if len(pts) >= 3:
                fd.sub(Chain(pts, [hr(0.0032)] * len(pts), k=0.003), hr(0.003))
    # the braids: three-strand plaits as alternating lobes, thinning toward their ends
    nseg = 16
    for sx in (-1, 1):
        for i in range(1, nseg):
            t0, t1 = i / nseg * 0.94, (i + 1) / nseg * 0.94
            a, da = braid_at(sx, t0)
            b, _ = braid_at(sx, t1)
            w = 0.034 - 0.01 * t0
            sgn = 1 if i % 2 else -1
            nrm = norm(np.cross(b - a, v3((1, 0, 0)))) if abs(norm(b - a)[0]) < 0.9 else v3((0, 1, 0))
            side = norm(np.cross(b - a, nrm))
            mid = (a + b) / 2 + side * sgn * w * 0.3
            fd.add(Ellipsoid(mid, (w, w * 0.72, np.linalg.norm(b - a) * 0.76), R=rot_from_axes(z_axis=norm(b - a + side * sgn * 0.02), x_axis=side)),
                   hr(0.006))
        end, d = braid_at(sx, 0.94)
        fd.add(Lock([end, end + d * 0.04, end + d * 0.1], [hr(0.028), hr(0.03), hr(0.008)], [hr(0.016), hr(0.016), hr(0.005)],
                    [v3((0, -1, 0))] * 3, k=hr(0.006)), hr(0.008))
    return fd


# ======================================================================================= gold
TORC_C = v3((0.0, 0.03, 1.425))
TORC_U = norm(v3((0.0, -0.93, -0.37)))
TORC_S = v3((1.0, 0.0, 0.0))
TORC_RY, TORC_RX = 0.112, 0.118
TORC_N = norm(np.cross(TORC_S, TORC_U))


def torc_point(a):
    return TORC_C + TORC_U * (math.cos(a) * TORC_RY) + TORC_S * (math.sin(a) * TORC_RX)


def gold_field():
    """A torc of three twisted strands with round terminals; a band round each braid's end; a bracelet at each wrist."""
    fd = Field("Gold")
    n = 44
    for strand in range(3):
        pts = []
        for k in range(n + 1):
            a = math.radians(26 + (360 - 52) * k / n)
            p = torc_point(a)
            radial = norm(p - TORC_C)
            tw = a * 4.0 + strand * 2 * math.pi / 3
            pts.append(p + (radial * math.cos(tw) + TORC_N * math.sin(tw)) * 0.0075)
        fd.add(Chain(pts, [0.0066] * len(pts), k=0.003), 0.004)
    for a in (math.radians(22), math.radians(-22)):
        fd.add(Sphere(torc_point(a), 0.017), 0.006)
    for sx in (-1, 1):
        p, d = braid_at(sx, 0.9)
        fd.add(Torus(p, 0.026, 0.0075, R=rot_from_axes(z_axis=d)), 0.003)
        fd.add(Torus(p - d * 0.016, 0.026, 0.006, R=rot_from_axes(z_axis=d)), 0.003)
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.9)
        fa = _forearm(side)
        fd.add(Inter(Shell(fa, 0.008, 0.012, pad=0.05), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.011),
                                                          c - 0.15, c + 0.15), 0.003), 0.0)
    return fd


# ======================================================================================= trousers, leather
def legs_base():
    b = Field("LegsBase")
    b.add(torso_prims()[5][0], 0.0)
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            b.add(p, k)
    return b


def trousers_field():
    """Blue checked wool trousers from under the mail to her shins, a little loose, creased at the knees."""
    fd = Field("Trousers")
    base = legs_base()
    def shell(P):
        d = base.eval(P, margin=0.08)
        z = P[:, 2]
        crease = F(0.003) * np.sin(z * F(60) + P[:, 0] * F(20)) + F(0.002) * NOISE(P * F(14))
        return np.abs(d - (F(0.018) + crease)) - F(0.0075)
    def keep(P):
        z = P[:, 2]
        return np.maximum(z - F(0.68), F(0.2) - z)
    lo, hi = (-0.45, -0.35, 0.1), (0.45, 0.4, 0.72)
    fd.add(Inter(Func(shell, lo, hi), Func(keep, lo, hi), 0.004), 0.0)
    return fd


def shoe_hull(side):
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    Rz = euler(0, 0, sx * 0.1)
    fwd = Rz @ v3((0, -1, 0))
    f = Field("ShoeHull")
    f.add(Sphere(an + v3((0, 0.04, -0.05)), 0.058), 0.0)
    f.add(RoundBox(an + fwd * 0.072 + v3((0, 0, -0.066)), (0.062, 0.115, 0.035), 0.032, R=Rz), 0.04)
    f.add(Ellipsoid(an + fwd * 0.155 + v3((0, 0, -0.07)), (0.058, 0.056, 0.034), R=Rz), 0.03)
    f.add(Cylinder(an + v3((0, 0.005, 0.02)), 0.06, 0.1, rr=0.03), 0.04)
    return f, fwd, Rz


def leg_axis_point(side, z):
    kn, an = J["knee_" + side], J["ankle_" + side]
    u = (kn[2] - z) / (kn[2] - an[2])
    return lerp(kn, an, u)


def leather_field():
    """A wide belt over the mail (a bronze buckle, label 6), bracers on her forearms, shoes, and thongs criss-crossing
    up her shins over the trousers."""
    fd = Field("Leather")
    mb = mail_base()
    fd.add(Func(lambda P: np.maximum(np.abs(mb.eval(P, margin=0.08) - F(0.04)) - F(0.011), np.abs(P[:, 2] - F(BELT_Z)) - F(0.034)),
                (-0.5, -0.45, 0.83), (0.5, 0.45, 1.04)), 0.0)
    h, ok = ray_hit(Func(lambda P: mb.eval(P, margin=0.1) - F(0.052), (-0.5, -0.6, 0.8), (0.5, 0.5, 1.1)), [v3((0, -0.7, BELT_Z))],
                    [v3((0, 1, 0))], tmax=0.8)
    c = h[0] if ok[0] else v3((0, -0.17, BELT_Z))
    fd.add(RoundBox(c + v3((0, -0.004, 0)), (0.034, 0.008, 0.03), 0.006), 0.004, 6)
    fd.sub(RoundBox(c + v3((0, -0.012, 0)), (0.022, 0.01, 0.019), 0.004), 0.002)
    fd.add(RoundBox(c + v3((0.004, -0.01, 0)), (0.004, 0.006, 0.024), 0.002), 0.002, 6)
    for side in ("L", "R"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c2 = lerp(el, wr, 0.62)
        fa = _forearm(side)
        fd.add(Inter(Shell(fa, 0.011, 0.015, pad=0.06), Func(lambda P, c2=c2, ax=ax: np.abs((P - c2.astype(F)) @ ax.astype(F)) - F(0.065),
                                                           c2 - 0.25, c2 + 0.25), 0.004), 0.0)
        for j in (-1, 0, 1):
            cc = c2 + ax * (j * 0.04)
            fd.add(Inter(Shell(fa, 0.019, 0.005, pad=0.06), Func(lambda P, cc=cc, ax=ax: np.abs((P - cc.astype(F)) @ ax.astype(F)) - F(0.005),
                                                               cc - 0.2, cc + 0.2), 0.002), 0.003)
    for side in ("R", "L"):
        an = J["ankle_" + side]
        sh, fwd, Rz = shoe_hull(side)
        top = an[2] + 0.07
        fd.add(Inter(Shell(sh, 0.0, 0.024, pad=0.06), Func(lambda P, top=top: P[:, 2] - F(top), an - 0.35, an + 0.35), 0.006), 0.0)
        fd.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.098)), (0.07, 0.15, 0.011), 0.01, R=Rz), 0.008)
        fd.add(Torus(an + v3((0, 0.006, 0.068)), 0.062, 0.01), 0.004)
        leg = Field("LegHull")
        for p, k in leg_prims(side):
            leg.add(p, k)
        z0, z1 = an[2] + 0.07, J["knee_" + side][2] - 0.06
        for hand_dir in (1, -1):
            pts = []
            for k in range(22):
                u = k / 21.0
                z = z0 + (z1 - z0) * u
                cz = leg_axis_point(side, z)
                th = hand_dir * u * 2.0 * 2 * math.pi + (0.0 if hand_dir > 0 else math.pi)
                d = v3((math.cos(th), math.sin(th), 0.0))
                hh, okk = ray_hit(Func(lambda P, leg=leg: leg.eval(P, margin=0.06) - F(0.03), an - 0.4, J["knee_" + side] + 0.4),
                                  [cz + d * 0.35], [-d], tmax=0.4)
                if okk[0]:
                    pts.append(hh[0])
            if len(pts) > 4:
                fd.add(Chain(pts, [0.0062] * len(pts), k=0.003), 0.003)
    return fd


# ======================================================================================= the spear, the shield
SPEAR_FWD = 1.24           # grip -> spear point
SPEAR_BACK = 0.74          # grip -> butt spike's tip
SPEAR_R = 0.016


def spear_axis():
    wr, f, n, t = hand_frame("R")
    return fist_center("R"), t


def spear_field():
    """An ash shaft (label 0), a long leaf-shaped iron head with a midrib on its socket and an iron butt spike (6), a
    leather binding below the head (5)."""
    fd = Field("Spear")
    a0, ax = spear_axis()
    wr, f, n, t = hand_frame("R")
    grain = lambda P: F(0.0016) * NOISE(P * F(70))
    fd.add(Chain([a0 - ax * (SPEAR_BACK - 0.07), a0 + ax * (SPEAR_FWD - 0.24)], [SPEAR_R, SPEAR_R * 0.92], k=0.0, disp=grain, disp_amp=0.002), 0.0)
    sock0, sock1 = a0 + ax * (SPEAR_FWD - 0.26), a0 + ax * (SPEAR_FWD - 0.19)
    fd.add(RoundCone(sock0, sock1, SPEAR_R + 0.004, SPEAR_R + 0.001), 0.003, 6)
    fd.add(Ellipsoid(a0 + ax * (SPEAR_FWD - 0.095), (0.03, 0.0065, 0.105), R=rot_from_axes(z_axis=ax, y_axis=n)), 0.006, 6)
    fd.add(Chain([sock1 - ax * 0.01, a0 + ax * (SPEAR_FWD - 0.005)], [0.0095, 0.0028], k=0.004), 0.006, 6)
    for k in range(5):
        c = a0 + ax * (SPEAR_FWD - 0.28 - 0.012 * k)
        fd.add(Torus(c, SPEAR_R + 0.003, 0.0042, R=rot_from_axes(z_axis=ax)), 0.002, 5)
    b0 = a0 - ax * (SPEAR_BACK - 0.07)
    fd.add(RoundCone(b0, b0 - ax * 0.025, SPEAR_R + 0.0028, SPEAR_R + 0.001), 0.002, 6)
    fd.add(RoundCone(b0 - ax * 0.025, a0 - ax * SPEAR_BACK, SPEAR_R, 0.003), 0.004, 6)
    return fd


SHIELD_R = 0.31
SHIELD_DOME = 0.04
SHIELD_T = 0.022
SHIELD_BACK = 0.045        # grip -> the shield's back at the middle


def shield_frame():
    """Rest pose: the shield's grip is in the left fist along the fist's thumb axis U; its face points along the
    knuckles N; S = N x U."""
    wr, f, n, t = hand_frame("L")
    G = fist_center("L")
    U = norm(t)
    N = norm(f - U * (f @ U))
    S = np.cross(N, U)
    return G, N, U, S


def shield_field():
    """A round shield of boards (wood, label 0), its face painted blue (7) with a white triskele wheeling round the boss
    and a white ring at its edge (5); an iron rim and a domed iron boss with a flange and rivets (6); the leather-bound
    grip behind the boss (9)."""
    fd = Field("Shield")
    G, N, U, S = shield_frame()
    C = G + N * SHIELD_BACK
    Rs = (SHIELD_R ** 2 + SHIELD_DOME ** 2) / (2 * SHIELD_DOME)
    sc = C + N * (SHIELD_DOME - Rs)
    boards = lambda P: F(0.0012) * NOISE(P * F(40)) + F(0.0012) * np.abs(np.sin(((P - C.astype(F)) @ S.astype(F)) * F(52)))
    def disc(P):
        q = P - C.astype(F)
        h = q @ N.astype(F)
        rr = np.sqrt(np.maximum((q * q).sum(1) - h * h, 0))
        return np.maximum(rr - F(SHIELD_R), F(-0.1) - h)
    fd.add(Inter(Func(disc, C - 0.4, C + 0.4),
                 Shell(Sphere(sc, Rs), SHIELD_T * 0.5, SHIELD_T, pad=0.05, disp=boards, disp_amp=0.002), 0.006), 0.0)
    def front_side(P):
        d = P - sc.astype(F)
        return F(Rs + SHIELD_T * 0.25) - np.sqrt((d * d).sum(1))
    def polar(P):
        q = P - C.astype(F)
        u, s = q @ U.astype(F), q @ S.astype(F)
        return np.sqrt(u * u + s * s), np.arctan2(s, u)
    def white(P):
        rr, a = polar(P)
        best = np.abs(rr - F(0.275)) - F(0.012)                       # the ring at the edge
        best = np.minimum(best, np.abs(rr - F(0.09)) - F(0.01))       # the ring round the boss
        for k in range(3):                                           # the triskele's three arms
            th = F(k * 2 * math.pi / 3) + F(2.6) * (rr - F(0.09)) / F(0.17)
            da = np.mod(a - th + F(math.pi), F(2 * math.pi)) - F(math.pi)
            u = np.clip((rr - F(0.09)) / F(0.16), 0, 1)
            width = F(0.034) * (F(1.0) - u) + F(0.008)
            arm = np.abs(da) * rr - width
            arm = np.maximum(arm, np.maximum(F(0.088) - rr, rr - F(0.26)))
            best = np.minimum(best, arm)
        return np.maximum(best, front_side(P))
    # the blue leaves the white out: the material lays label 7 over label 5, so overlapping paints would hide the white
    fd.paint(Func(lambda P: np.maximum(front_side(P), -white(P)), C - 0.5, C + 0.5), 7)
    fd.paint(Func(white, C - 0.5, C + 0.5), 5)
    # (the iron and the grip after the paint: where they stand proud they keep their own labels)
    rim_c = sc + N * math.sqrt(max(Rs * Rs - SHIELD_R * SHIELD_R, 0.0))
    fd.add(Torus(rim_c + N * 0.006, SHIELD_R - 0.005, 0.015, R=rot_from_axes(z_axis=N, y_axis=U)), 0.006, 6)
    face = C + N * (SHIELD_DOME + SHIELD_T)
    fd.add(Inter(Sphere(face - N * 0.03, 0.072), Plane(face - N * 0.022, -N), 0.004), 0.008, 6)
    fd.add(Torus(face - N * 0.02, 0.07, 0.009, R=rot_from_axes(z_axis=N, y_axis=U)), 0.004, 6)
    for k in range(6):
        a = 2 * math.pi * k / 6
        fd.add(Sphere(face - N * 0.012 + (U * math.cos(a) + S * math.sin(a)) * 0.07, 0.0075), 0.002, 6)
    fd.add(RoundCone(G - U * 0.07, G + U * 0.07, 0.016, 0.016), 0.01, 9)
    fd.add(RoundCone(C - N * 0.002 - U * 0.1, C - N * 0.002 + U * 0.1, 0.013, 0.013), 0.008, 9)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = kr.warm_points()
    return pts


# ======================================================================================= build config
GLB_NAME = "brenna"
ROOT_NAME = "HeroBrennaHQ"
TEX_PREFIX = "hero"
MAT_NAME = "BrennaMat"
MESH_NAME = "Brenna"
BASE_MODULE = "brenna_base"
ANIM_MODULE = "anim_brenna"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Gold", "Mail", "Trousers", "Leather", "Spear", "Shield"]
REGION_PARTS = ("Skin", "Mail", "Leather", "Spear", "Shield")
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_BrennaSkin", "base": (0.9, 0.7, 0.58), "ruddy": (0.9, 0.55, 0.46), "lips": (0.74, 0.42, 0.4),
                      "brow": ((0.5, 0.22, 0.1), (0.72, 0.38, 0.2)), "paint": (0.12, 0.26, 0.64),
                      "extra": ((LASH, (0.34, 0.15, 0.08), 0.5),)}),
    "Hair": ("hair", {"name": "HQ_BrennaHair", "base": (0.64, 0.22, 0.07), "hi": (0.95, 0.5, 0.22), "low": (0.3, 0.08, 0.03),
                      "streak": (0.46, 0.14, 0.05), "tint": (0.78, 0.3, 0.1)}),
    "Gold": ("gold", {"name": "HQ_BrennaGold"}),
    "Mail": ("mail", {"name": "HQ_BrennaMail"}),
    "Trousers": ("plaid", {"name": "HQ_BrennaTrousers", "base": (0.16, 0.28, 0.56), "stripe": (0.08, 0.12, 0.26),
                           "line": (0.9, 0.88, 0.82), "border": (0.08, 0.12, 0.26), "period": 0.1}),
    "Leather": ("leather_dyed", {"name": "HQ_BrennaLeather", "base": (0.36, 0.22, 0.12), "dyed": (0.2, 0.3, 0.55)}),
    "Spear": ("javelin_shaft", {"name": "HQ_BrennaSpear"}),
    "Shield": ("siege", {"name": "HQ_BrennaShield", "wood": (0.52, 0.36, 0.22), "wood2": (0.38, 0.25, 0.14), "red": (0.92, 0.9, 0.82),
                         "blue": (0.13, 0.3, 0.68), "metal": "iron"}),
}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Hair": 2400, "Gold": 700, "Mail": 2600, "Trousers": 1400, "Leather": 1800, "Spear": 420,
               "Shield": 1400}
AO_EXCLUDE = ["Spear", "Gold"]


def prop_bones():
    return []


def hair_weights(ob, skin_ob, arm):
    """The hair on her head rides the head; each braid passes from the head (behind her ear) to the neck and the chest
    as it falls over her shoulder, and lies on her chest."""
    groups = {}
    z_head = hp((0, 0, 1.6))[2]
    for v in ob.data.vertices:
        p = v.co
        if p.z >= z_head or abs(p.x) < 0.11:
            w = {"head": 1.0}
        else:
            t = max(0.0, min(1.0, (1.58 - p.z) / 0.2))                     # 0 behind the ear, 1 on the front of the shoulder
            w = {"head": 1.0 - t, "neck": 0.6 * t * (1 - t), "chest": t}
            if p.z < 1.38:
                w = {"chest": 1.0}
        _blend_add(ob, groups, v.index, w)


def gold_weights(ob, skin_ob, arm):
    """The torc rides her neck and chest; the braid bands her chest; the bracelets her forearms."""
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if abs(p.x) > 0.45:
            w = {"forearm.R" if p.x < 0 else "forearm.L": 1.0}
        elif p.z < 1.2:
            w = {"chest": 1.0}
        else:
            w = {"chest": 0.65, "neck": 0.35}
        for g in list(ob.vertex_groups):
            g.remove([v.index])
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Gold": ("custom", gold_weights),
        "Mail": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L"},
                 {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Trousers": ("transfer", TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Leather": ("transfer", TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Spear": ("rigid", "hand.R"), "Shield": ("rigid", "hand.L"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Spear":
        return 0.6
    if part == "Shield":
        return 1.2
    if part == "Skin" and abs(c.x) > 0.55 and c.z < 1.0:
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Gold", gold_field(), 0.0016 if fine else 0.0024),
        ("Mail", mail_field(), 0.0026 if fine else 0.0036),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Spear", spear_field(), 0.0016 if fine else 0.0022),
        ("Shield", shield_field(), 0.0024 if fine else 0.0032),
    ]
