"""The Alchemist (HQ tower, Medieval Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A keen alchemist of middle years at her furnace: a long clever face, high cheekbones, arched brows (the left cocked), a
long nose with a little hook and a pair of round rivet spectacles of brass perched on it, a thin wry mouth, a beauty
spot; chestnut hair streaked grey at the temples, parted and drawn back under a dark red kerchief knotted at her nape
over the knot of her braid. A long gown of dark green wool to her ankles with a gold and black border, its sleeves
rolled above the elbow; over it a scorched leather apron from her breast to her shins with a pocket; a belt with a
pouch and a brass funnel; across her chest from her right shoulder a bandolier of stoppered glass vials (green, amber,
violet, red); leather gauntlets to mid-forearm; leather shoes. In her right fist, by its neck, a round glass flask of
glowing green brew (the bulb ships as its own glowing mesh).

Before her stands her athanor (the tower turns about it: YAW_PIVOT): a round furnace of red brick on a stone plinth,
bound with iron, its arched firing door glowing with coals, its domed crown holding an iron crucible of green brew
(glowing meshes: Brew, Coals). When she pours, a stream of brew runs from the flask (the Stream mesh on its own bone).

She has Kira's build (kira.py) with her own head; Brenna's shoes (brenna.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import kira as kr
import brenna as br
from kira import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S, foot,
                  fist_center, torso_prims, traps, neck_prim, deltoid, upper_arm, _forearm, eyes_field, teeth_field, TORSO,
                  TORSO_Z, torso_bones)

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH = 0, 1, 2, 3, 4, 5, 8
CURLS = {"R": (1.45, 1.6, 1.2), "L": (0.45, 0.6, 0.4)}       # right: a fist round the flask's neck; left: half open


# ======================================================================================= hands
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
    open_ = side == "L"
    d1 = norm(f * 0.55 + t * 0.55 + n * (0.3 if open_ else 0.6))
    d2 = norm(f * 0.25 - t * (0.4 if open_ else 0.85) + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.023 * s, 0.02 * s, 0.017 * s], k=0.008), 0.017, SKIN)


# ======================================================================================= head
BROW_L_UP = 0.007                  # her left brow is cocked


def head(fd):
    """A long clever face: high cheekbones, a narrow jaw, arched brows (the left cocked), a long nose with a little hook,
    thin lips set in a wry half smile (the left corner up), a beauty spot by her mouth on the left."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.06, 1.598), (0.136, 0.13, 0.13)), 0.07, SKIN)
    fd.add(E((0, -0.128, 1.502), (0.066, 0.062, 0.064)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.112, 1.646), 0.039), 0.05, SKIN)                     # cheekbones, high
        fd.add(S((sx * 0.108, -0.05, 1.56), 0.042), 0.05, SKIN)
        pts = [hp((sx * 0.15, -0.06, 1.744)), hp((sx * 0.115, -0.13, 1.752)), hp((sx * 0.062, -0.164, 1.75))]
        fd.add(Chain(pts, [hr(0.011), hr(0.016), hr(0.014)], k=hr(0.02)), hr(0.03), SKIN)
    for sx in (-1, 1):                                                                  # arched brows
        up = BROW_L_UP if sx > 0 else 0.0
        pts = [hp((sx * 0.032, -0.2, 1.752 + up * 0.4)), hp((sx * 0.07, -0.197, 1.773 + up)),
               hp((sx * 0.112, -0.176, 1.781 + up)), hp((sx * 0.148, -0.136, 1.768 + up * 0.6))]
        fd.add(Chain([p + v3((0, 0.008, 0)) for p in pts], [hr(0.0045), hr(0.006), hr(0.0052), hr(0.0024)], k=hr(0.006)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.011), hr(0.013), hr(0.011), hr(0.005)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        lid = hr(0.015) if sx < 0 else hr(0.018)                                       # (the cocked side's eye a little wider)
        up = Inter(Sphere(ec, EYE_R + hr(0.0058)), Plane(ec + v3((0, 0, lid)), (sx * 0.2, 0.05, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0044)), Plane(ec + v3((0, 0, -hr(0.023))), (sx * -0.12, 0.05, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.008)), Plane(ec + v3((0, 0, lid - hr(0.003))), (sx * 0.2, 0.05, -1.0)), hr(0.002)), LASH)
    # the nose: long, a little hook at its bridge, a fine tip
    fd.add(RoundCone(hp((0, -0.178, 1.728)), hp((0, -0.226, 1.642)), hr(0.011), hr(0.015)), hr(0.016), SKIN)
    fd.add(S((0, -0.203, 1.69), 0.012), hr(0.012), SKIN)
    fd.add(S((0, -0.226, 1.632), 0.018), hr(0.013), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.021, -0.207, 1.62), 0.013), hr(0.01), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.011, -0.22, 1.609)), v3((0.0065, 0.008, 0.0045)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the mouth: thin, its left corner drawn up
    slot = [hp((-0.052, -0.166, 1.552)), hp((-0.027, -0.186, 1.547)), hp((0, -0.193, 1.546)), hp((0.029, -0.186, 1.551)),
            hp((0.056, -0.164, 1.562))]
    fd.sub(Chain(slot, [hr(0.002), hr(0.0028), hr(0.0032), hr(0.0028), hr(0.002)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0028), hr(0.004), hr(0.0044), hr(0.004), hr(0.0028)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.05, -0.163, 1.555), (-0.026, -0.18, 1.552), (0, -0.185, 1.554), (0.028, -0.18, 1.557), (0.055, -0.161, 1.566)]
    lo_lip = [(-0.043, -0.165, 1.545), (-0.023, -0.18, 1.535), (0, -0.184, 1.533), (0.024, -0.18, 1.537), (0.047, -0.163, 1.553)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.0032), hr(0.0054), hr(0.0058), hr(0.0054), hr(0.0032)], k=hr(0.006)), hr(0.008), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.0038), hr(0.0068), hr(0.0074), hr(0.0068), hr(0.0038)], k=hr(0.007)), hr(0.008), LIP)
    fd.sub(S((0.064, -0.168, 1.566), 0.006), hr(0.006))                               # the smile's dimple
    fd.paint(Sphere(hp((0.072, -0.153, 1.58)), hr(0.0045)), PAINT)                      # the beauty spot
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.172, 0.035, 1.66)), v3((0.023, 0.042, 0.053)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)


# ======================================================================================= body
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
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.066, 0.068, 0.1), R=rot_from_axes(z_axis=el - sh)), 0.035, SKIN)
        fd.add(_forearm(side), 0.03, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.068, 0.06, 0.106), R=rot_from_axes(z_axis=wr - el)), 0.035, SKIN)
        fd.add(Sphere(el + v3((0, 0.022, 0)), 0.042), 0.025, SKIN)
        hand(fd, side)
        for p, k in br.leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= hair and kerchief
KER_FRONT = hp((0.0, -0.118, 1.866))          # the kerchief's front edge, over the crown (her hair shows before it)
KER_BACK = hp((0.0, 0.2, 1.632))              # ...behind the tops of her ears, down to the nape
KNOT = hp((0.0, 0.205, 1.575))                # the knot of her braid at the back of her head (half under the kerchief)


def _ker_edge(P):
    """> 0 in front of / below the kerchief's edge: a plane from over her crown back down behind her ears to her nape."""
    n = norm(np.cross(v3((1.0, 0.0, 0.0)), KER_BACK - KER_FRONT))                    # (pointing up and back)
    return -((P - KER_FRONT.astype(F)) @ n.astype(F))


def hair_cap():
    return Ellipsoid(HEAD_C, HEAD_RAD + 0.011)


def hair_field():
    """Chestnut hair parted in the middle, drawn back smooth from her brow and over the tops of her ears to the kerchief;
    the knot of her braid at the back (under the kerchief's cloth)."""
    fd = Field("Hair")
    hc = HEAD_C
    cap = hair_cap()
    pfront = hp((0, -0.156, 1.832))
    def hairline(P):
        x = P[:, 0]
        temple = F(0.026) * smoothstep(0.08, 0.15, np.abs(x))
        n = norm((0, 0.62, -1.0))
        return ((P - pfront.astype(F)) @ n.astype(F)) + temple + F(0.004) * NOISE(P * F(24))
    def ears(P):
        Q = hinv(P)
        return np.where((np.abs(Q[:, 0]) > F(0.15)) & (Q[:, 2] < F(1.62)) & (Q[:, 1] < F(0.08)), F(0.02), F(-1.0))
    fd.add(Inter(cap, Func(lambda P: np.maximum(hairline(P), ears(P)), hc - 0.5, hc + 0.5), 0.02), 0.0)
    for sx in (-1, 1):                                                         # swept back over each ear
        a = hp((sx * 0.158, -0.045, 1.715))
        b = hp((sx * 0.176, 0.05, 1.64))
        c = hp((sx * 0.1, 0.17, 1.6))
        fd.add(Lock([a, b, c], [hr(0.048), hr(0.05), hr(0.04)], [hr(0.016), hr(0.018), hr(0.016)], [v3((sx, 0, 0.2))] * 3, k=hr(0.012)), hr(0.02))
    fd.add(Ellipsoid(KNOT, (0.075, 0.05, 0.062)), hr(0.03))
    part = [hp((0.0, -0.16, 1.83)), hp((0.0, -0.12, 1.865))]
    fd.sub(Chain(part, [hr(0.004)] * 2, k=0.002), hr(0.003))
    for sx in (-1, 1):                                                         # combed back from the parting
        for j in range(7):
            u0 = j / 6
            pts = []
            for k in range(9):
                u = k / 8
                d = norm(v3((sx * (0.05 + 0.9 * u), -1.0 + 0.9 * u0 + 0.5 * u, 0.55 + 0.4 * u0 - 0.2 * u)))
                o = hc + d * 0.5
                h, ok = ray_hit(Func(lambda P: cap(P), hc - 0.5, hc + 0.5), [o], [-d], tmax=0.5)
                if ok[0]:
                    pts.append(h[0] + d * hr(0.001))
            pts = [p for p in pts if hairline(np.array([p], F))[0] < -0.006 and _ker_edge(np.array([p], F))[0] > 0.004]
            if len(pts) >= 3:
                fd.sub(Chain(pts, [hr(0.003)] * len(pts), k=0.003), hr(0.003))
    return fd


def grey_field():
    """Grey streaks swept back at her temples."""
    fd = Field("Grey")
    for sx in (-1, 1):
        a = hp((sx * 0.135, -0.1, 1.77))
        b = hp((sx * 0.166, -0.03, 1.73))
        c = hp((sx * 0.178, 0.04, 1.68))
        fd.add(Lock([a, b, c], [hr(0.018), hr(0.022), hr(0.016)], [hr(0.007), hr(0.008), hr(0.006)], [v3((sx, 0, 0.3))] * 3, k=hr(0.006)), 0.0)
    return fd


def kerchief_field():
    """Dark red wool (label 0) with a black border along its front edge (5): it covers her crown and the back of her head
    over the knot of her braid, tied at her nape in a knot with two short tails."""
    fd = Field("Kerchief")
    hull = Field("KerHull")
    hull.add(hair_cap(), 0.0)
    hull.add(Ellipsoid(KNOT, (0.075, 0.05, 0.062)), hr(0.03))
    folds = lambda P: F(0.0025) * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(HEAD_C[1])) * F(7) + (P[:, 2] - F(1.6)) * F(14)) + F(0.001) * NOISE(P * F(30))
    lo, hi = HEAD_C - 0.4, HEAD_C + 0.4
    fd.add(Inter(Shell(hull, 0.016, 0.011, pad=0.06, disp=folds, disp_amp=0.004), Func(_ker_edge, lo, hi), 0.004), 0.0)
    fd.paint(Func(lambda P: np.abs(_ker_edge(P) + F(0.016)) - F(0.012), lo, hi), 5)
    nape = hp((0.0, 0.222, 1.64))
    fd.add(Ellipsoid(nape, (0.034, 0.026, 0.028)), 0.01)
    for sx in (-1, 1):
        fd.add(Lock([nape + v3((sx * 0.01, 0.01, -0.01)), nape + v3((sx * 0.03, 0.03, -0.06)), nape + v3((sx * 0.04, 0.035, -0.12))],
                    [0.022, 0.026, 0.02], [0.006, 0.006, 0.005], [v3((0, 1, 0))] * 3, k=0.006, disp=folds, disp_amp=0.003), 0.008)
    return fd


# ======================================================================================= the gown, the apron
BELT_Z = 0.94
HEM_Z = 0.13


def gown_base():
    b = Field("GownBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.05)
    b.add(neck_prim(), 0.045)                    # (the high collar hugs her throat)
    b.add(RoundCone((0, 0.03, 0.92), (0, 0.04, 0.12), 0.235, 0.34), 0.08)
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        b.add(deltoid(side), 0.05)
        b.add(upper_arm(side), 0.045)
        b.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.018, 0)), (0.066, 0.068, 0.1), R=rot_from_axes(z_axis=el - sh)), 0.035)
        b.add(Sphere(el + v3((0, 0.022, 0)), 0.042), 0.025)
    return b


def _gown_neck(P):
    """> 0 above the neckline: high and round at the front, closing over the shoulders."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    out = np.clip((np.abs(x) - F(0.13)) / F(0.08), 0, 1)
    return z - (F(1.445) + F(0.3) * out * out * (F(3) - F(2) * out))


def _sleeve_end(P):
    """> 0 past the rolled sleeves (a little above the elbow)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        c = lerp(sh, el, 0.8)
        along = (P - c.astype(F)) @ ax.astype(F)
        sx = -1 if side == "R" else 1
        lateral = P[:, 0] * F(sx) - F(0.24)
        out = np.maximum(out, np.where(lateral > 0, along, F(-1.0)))
    return out


def gown_hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(HEM_Z) + F(0.012) * np.cos(a * 3) + F(0.005) * NOISE(P * F(10))


def gown_field():
    """Dark green wool (label 0) from her neck to her ankles, fitted to the waist and falling in folds below it, the
    sleeves rolled above the elbow (a thick roll); a gold border (5) with a black stripe (6) round the hem."""
    fd = Field("Gown")
    base = gown_base()
    def shell(P):
        d = base.eval(P, margin=0.1)
        z = P[:, 2]
        below = np.clip((F(BELT_Z) - z) / F(0.25), 0, 1)
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
        folds = F(0.008) * np.sin(a * F(9) + F(0.8) * NOISE(P * F(2))) * below + F(0.0018) * NOISE(P * F(14))
        off = F(0.02) + folds + F(0.012) * below
        return np.abs(d - off) - F(0.008)
    def keep(P):
        return np.maximum(np.maximum(_gown_neck(P), _sleeve_end(P)), gown_hem(P) - P[:, 2])
    lo, hi = (-0.75, -0.55, 0.05), (0.75, 0.55, 1.6)
    fd.add(Inter(Func(shell, lo, hi), Func(keep, lo, hi), 0.004), 0.0)
    for side in ("R", "L"):                                                    # the rolled sleeves
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        c = lerp(sh, el, 0.8)
        ua = Field("UA")
        ua.add(upper_arm(side), 0.0)
        ua.add(Sphere(el + v3((0, 0.022, 0)), 0.042), 0.025)
        fd.add(Inter(Shell(ua, 0.034, 0.03, pad=0.08), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F) + F(0.012)) - F(0.022),
                                                          c - 0.2, c + 0.2), 0.006), 0.006)
    fd.paint(Func(lambda P: P[:, 2] - (gown_hem(P) + F(0.05)), (-0.6, -0.6, 0.0), (0.6, 0.6, 0.3)), 5)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - (gown_hem(P) + F(0.028))) - F(0.007), (-0.6, -0.6, 0.0), (0.6, 0.6, 0.3)), 6)
    return fd


def gown_point(x, z, off=0.03):
    """A point on the gown's outer surface in front of her, at (x, z) (a ray from the front)."""
    base = gown_base()
    h, ok = ray_hit(Func(lambda P: base.eval(P, margin=0.1) - F(off), (-0.8, -0.6, 0.0), (0.8, 0.6, 1.7)), [v3((x, -0.8, z))],
                    [v3((0, 1, 0))], tmax=0.9)
    return h[0] if ok[0] else v3((x, -0.2, z))


APRON_TOP, APRON_HEM = 1.3, 0.3


def apron_field():
    """Scorched leather (label 0, burns: 5) hanging from a strap round her neck, from her breast to her shins, tied round
    her waist; a pocket on its front with a stitched edge."""
    fd = Field("Apron")
    base = gown_base()
    def shell(P):
        d = base.eval(P, margin=0.1)
        z = P[:, 2]
        below = np.clip((F(BELT_Z) - z) / F(0.25), 0, 1)
        flat = F(0.012) * below
        return np.abs(d - (F(0.046) + flat)) - F(0.006)
    def keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        half = F(0.13) + F(0.12) * smoothstep(1.02, 0.86, z)
        side = np.abs(x) - half
        front = y - F(0.02)
        return np.maximum(np.maximum(np.maximum(side, front), z - F(APRON_TOP)), F(APRON_HEM) - z)
    lo, hi = (-0.6, -0.55, 0.2), (0.6, 0.3, 1.4)
    fd.add(Inter(Func(shell, lo, hi), Func(keep, lo, hi), 0.006), 0.0)
    # burns: dark scorch patches
    rs = np.random.RandomState(5)
    for k in range(7):
        x, z = rs.uniform(-0.18, 0.18), rs.uniform(0.4, 1.2)
        p = gown_point(x, z, 0.046)
        fd.paint(Ellipsoid(p, (rs.uniform(0.02, 0.04), 0.03, rs.uniform(0.015, 0.03))), 5)
    # the pocket
    pc = gown_point(0.07, 0.68, 0.058)
    fd.add(RoundBox(pc, (0.07, 0.008, 0.06), 0.006, R=euler(0, 0, 0.1)), 0.004)
    # the neck strap
    for sx in (-1, 1):
        a = gown_point(sx * 0.12, APRON_TOP - 0.01, 0.05)
        b = v3((sx * 0.125, 0.04, 1.465))
        c = v3((0.0, 0.158, 1.455))
        fd.add(Chain([a, lerp(a, b, 0.5) + v3((0, 0, 0.02)), b, c], [0.01, 0.01, 0.01, 0.01], k=0.004), 0.004)
    return fd


# ======================================================================================= leather: belt, bandolier, gauntlets, shoes
def surface_normal(fd, p, e=0.004):
    """The outward normal of field fd near point p (central differences)."""
    P = np.array([p + v3(d) * e for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))], F)
    d = fd.eval(P, margin=0.2)
    return norm(v3((d[0] - d[1], d[2] - d[3], d[4] - d[5])))


def forearm_hull(side):
    """The forearm as in her skin (the muscle's swell too): gauntlets wrap this."""
    sx = -1 if side == "R" else 1
    el, wr = J["elbow_" + side], J["wrist_" + side]
    h = Field("ForearmHull")
    h.add(_forearm(side), 0.0)
    h.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.006, 0, 0)), (0.068, 0.06, 0.106), R=rot_from_axes(z_axis=wr - el)), 0.035)
    return h


def bandolier_path():
    """From the top of her right shoulder over her breast to her left hip, lying on the apron and the gown."""
    pts = [v3((-0.17, 0.0, 1.44)), v3((-0.13, -0.08, 1.38))]
    for x, z in ((-0.07, 1.27), (0.0, 1.17), (0.07, 1.08), (0.14, 0.99), (0.2, 0.92)):
        pts.append(gown_point(x, z, 0.06))
    pts.append(v3((0.25, 0.0, 0.88)))
    return pts


def vial_spots():
    """Where the vials ride on the bandolier: (centre, axis along the vial, outward normal), five of them, upright as the
    curve of her front allows (each lies along the surface it rides on)."""
    path = bandolier_path()
    gb = gown_base()
    out = []
    for i, u in enumerate((0.22, 0.34, 0.46, 0.58, 0.7)):
        n = len(path) - 1
        s = min(int(u * n), n - 1)
        t = u * n - s
        p = lerp(path[s], path[s + 1], t)
        nrm = surface_normal(gb, p)
        up = v3((0, 0, 1))
        ax = norm(up - nrm * float(up @ nrm))
        out.append((p + nrm * 0.024, ax, nrm))
    return out


def leather_field():
    """The belt (label 0) with a brass buckle (6) and a pouch; the bandolier with its loops; gauntlets with flared cuffs;
    shoes."""
    fd = Field("Leather")
    gb = gown_base()
    off = lambda P: gb.eval(P, margin=0.1)
    fd.add(Func(lambda P: np.maximum(np.abs(off(P) - F(0.062)) - F(0.01), np.abs(P[:, 2] - F(BELT_Z)) - F(0.026)),
                (-0.5, -0.5, 0.85), (0.5, 0.5, 1.03)), 0.0)
    bc = gown_point(0.0, BELT_Z, 0.074)
    fd.add(RoundBox(bc, (0.03, 0.008, 0.026), 0.006), 0.004, 6)
    fd.sub(RoundBox(bc + v3((0, -0.008, 0)), (0.019, 0.01, 0.015), 0.004), 0.002)
    pp = gown_point(-0.24, 0.84, 0.08)                                        # the pouch on her right hip
    fd.add(RoundBox(pp + v3((0, 0.01, 0)), (0.06, 0.03, 0.065), 0.02, R=euler(0, 0, -0.5)), 0.006)
    fd.add(Ellipsoid(pp + v3((0, -0.012, 0.05)), (0.062, 0.03, 0.022), R=euler(0, 0, -0.5)), 0.006)
    path = bandolier_path()
    nrms = [surface_normal(gb, p) for p in path]
    fd.add(Lock(path, [0.022] * len(path), [0.0055] * len(path), nrms, k=0.004), 0.004)
    for c, ax, n in vial_spots():                                            # the loops
        fd.add(Torus(c, 0.019, 0.005, R=rot_from_axes(z_axis=ax)), 0.003)
    for side in ("R", "L"):                                                  # gauntlets
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        fa = forearm_hull(side)
        c = lerp(el, wr, 0.75)
        fd.add(Inter(Shell(fa, 0.012, 0.012, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.085),
                                                          c - 0.25, c + 0.25), 0.004), 0.0)
        cuff = lerp(el, wr, 0.45)
        fd.add(Inter(Shell(fa, 0.03, 0.01, pad=0.06), Func(lambda P, cuff=cuff, ax=ax: np.abs((P - cuff.astype(F)) @ ax.astype(F) - F(0.02)) - F(0.022),
                                                         cuff - 0.2, cuff + 0.2), 0.004), 0.004)
        hwr, hf, hn, ht = hand_frame(side)
        hh = Field("HandBack")
        hand(hh, side)
        fd.add(Inter(Shell(hh, 0.004, 0.008, pad=0.04), Func(lambda P, hwr=hwr, hf=hf: (P - hwr.astype(F)) @ hf.astype(F) - F(0.07),
                                                           hwr - 0.2, hwr + 0.2), 0.003), 0.003)
    for side in ("R", "L"):                                                  # shoes
        an = J["ankle_" + side]
        sh, fwd, Rz = br.shoe_hull(side)
        top = an[2] + 0.06
        fd.add(Inter(Shell(sh, 0.0, 0.022, pad=0.06), Func(lambda P, top=top: P[:, 2] - F(top), an - 0.35, an + 0.35), 0.006), 0.0)
        fd.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.098)), (0.068, 0.15, 0.011), 0.01, R=Rz), 0.008)
    return fd


def vials_field():
    """Stoppered glass vials (glass 0) of brews (green 5, amber 6, violet 7, red 8), corks (9), in the bandolier's loops."""
    fd = Field("Vials")
    for i, (c, ax, n) in enumerate(vial_spots()):
        lab = (5, 6, 7, 8, 5)[i]
        fd.add(RoundCone(c - ax * 0.04, c + ax * 0.03, 0.0135, 0.012), 0.0)
        fd.add(Torus(c + ax * 0.03, 0.013, 0.003, R=rot_from_axes(z_axis=ax)), 0.002)
        fd.add(RoundCone(c + ax * 0.028, c + ax * 0.05, 0.0095, 0.0105), 0.002, 9)
        fd.paint(Func(lambda P, c=c, ax=ax: (P - c.astype(F)) @ ax.astype(F) - F(0.012), c - 0.1, c + 0.1), lab)
        fd.paint(Func(lambda P, c=c, ax=ax: F(0.027) - (P - c.astype(F)) @ ax.astype(F), c - 0.1, c + 0.1), 9)
    return fd


# ======================================================================================= spectacles, brass
def spec_centres():
    out = []
    for sx in (-1, 1):
        ec = eye_c(sx)
        out.append(ec + v3((sx * 0.002, -0.052, -0.014)))
    return out


SPEC_R = 0.029


def spectacles_field():
    """Round rivet spectacles of brass, perched low on her nose: two rims and a riveted bridge over the nose."""
    fd = Field("Spectacles")
    cs = spec_centres()
    for c in cs:
        nrm = norm(v3((0, -1.0, 0.18)))
        fd.add(Torus(c, SPEC_R, 0.0042, R=rot_from_axes(z_axis=nrm)), 0.0)
    a = cs[0] + v3((SPEC_R * 0.85, 0.002, 0.012))
    b = cs[1] + v3((-SPEC_R * 0.85, 0.002, 0.012))
    top = hp((0.0, -0.236, 1.664))
    fd.add(Chain([a, lerp(a, top, 0.6) + v3((0, -0.004, 0.004)), top, lerp(b, top, 0.6) + v3((0, -0.004, 0.004)), b],
                 [0.0036] * 5, k=0.003), 0.002)
    fd.add(Sphere(top + v3((0, -0.002, 0)), 0.0055), 0.002)
    return fd


def funnel_field():
    """A brass funnel hanging from her belt on her left hip, and the belt's brass rings."""
    fd = Field("Brass")
    p = gown_point(0.23, 0.86, 0.085)
    ax = norm(v3((0.15, -0.1, -1.0)))
    fd.add(Shell(RoundCone(p, p + ax * 0.08, 0.045, 0.012), 0.0, 0.005, pad=0.03), 0.0)
    fd.add(RoundCone(p + ax * 0.075, p + ax * 0.13, 0.009, 0.006), 0.003)
    fd.add(Torus(p - ax * 0.004, 0.045, 0.004, R=rot_from_axes(z_axis=ax)), 0.002)
    hook = gown_point(0.22, BELT_Z - 0.02, 0.076)
    fd.add(Torus(hook, 0.016, 0.004, R=rot_from_axes(z_axis=v3((0, -1, 0)))), 0.002)
    fd.add(Chain([hook, lerp(hook, p, 0.5), p + v3((0, 0, 0.004))], [0.003] * 3, k=0.002), 0.002)
    return fd


# ======================================================================================= the flask
FLASK_NECK = 0.075         # fist centre -> the mouth
FLASK_BULB = 0.118         # fist centre -> the bulb's centre (the other way)
FLASK_R = 0.062


def flask_frame():
    """The flask in her right fist: its neck along the fist's thumb axis (the mouth beyond her thumb)."""
    wr, f, n, t = hand_frame("R")
    G = fist_center("R")
    return G, norm(t)


def flask_mouth():
    G, T = flask_frame()
    return G + T * FLASK_NECK


def flask_field():
    """The glass neck and lip (label 0) of the flask (its bulb of brew is the Potion mesh)."""
    fd = Field("Flask")
    G, T = flask_frame()
    fd.add(RoundCone(G - T * (FLASK_BULB - FLASK_R + 0.012), G + T * FLASK_NECK, 0.016, 0.013), 0.0)
    fd.add(Torus(G + T * FLASK_NECK, 0.014, 0.0045, R=rot_from_axes(z_axis=T)), 0.003)
    fd.add(Inter(Shell(Sphere(G - T * FLASK_BULB, FLASK_R + 0.002), 0.0, 0.004),
                 Func(lambda P: ((P - G.astype(F)) @ (-T).astype(F)) - F(FLASK_BULB - FLASK_R * 0.55), G - 0.3, G + 0.3), 0.003), 0.004)
    return fd


def potion_field():
    """The flask's bulb full of glowing green brew."""
    fd = Field("Potion")
    G, T = flask_frame()
    fd.add(Sphere(G - T * FLASK_BULB, FLASK_R), 0.0)
    return fd


STREAM_L = 0.2


def stream_field():
    """The stream of brew she pours: a thin column falling from the flask's mouth (its bone stretches it to the
    crucible and hides it when she is not pouring)."""
    fd = Field("Stream")
    m = flask_mouth()
    fd.add(RoundCone(m, m - v3((0, 0, STREAM_L)), 0.008, 0.0065), 0.0)
    return fd


# ======================================================================================= the athanor
YAW_PIVOT = (0.0, -0.5, 0.0)       # the tower turns about the furnace's axis
FURN = v3(YAW_PIVOT)
PLINTH_R, PLINTH_H = 0.27, 0.08
FURN_R0, FURN_R1 = 0.235, 0.215    # the brick body's radius at its foot and at its shoulder
FURN_TOP = 0.62                    # the shoulder (the dome above)
DOME_H = 0.1
CRUC_R = 0.1                       # the crucible's rim radius
CRUC_Z = 0.775                     # its rim's height
BREW_Z = 0.76                      # the brew's surface
DOOR_DIR = v3((1.0, 0.0, 0.0))     # the firing door faces her left


def furnace_field():
    """Red brick (label 0) laid in courses, a domed crown with a hole for the crucible, an arched firing door."""
    fd = Field("Furnace")
    def body(P):
        q = P - FURN.astype(F)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        z = P[:, 2]
        t = np.clip((z - F(PLINTH_H)) / F(FURN_TOP - PLINTH_H), 0, 1)
        R = F(FURN_R0) + F(FURN_R1 - FURN_R0) * t
        side = r - R
        dome = np.sqrt((r / F(FURN_R1)) ** 2 + (np.maximum(z - F(FURN_TOP), 0) / F(DOME_H)) ** 2) * F(FURN_R1) - F(FURN_R1)
        top = np.where(z > F(FURN_TOP), dome, side)
        return np.maximum(top, F(PLINTH_H - 0.01) - z)
    bricks = lambda P: F(0.0025) * NOISE(P * F(22))
    lo, hi = FURN - v3((0.35, 0.35, 0.0)), FURN + v3((0.35, 0.35, 1.0))
    fd.add(Func(body, lo, hi, disp=bricks, disp_amp=0.003), 0.0)
    fd.sub(Cylinder(FURN + v3((0, 0, CRUC_Z)), CRUC_R + 0.004, 0.2, rr=0.01), 0.006)          # the crucible's seat
    # the firing door: an arched recess on her left
    dc = FURN + DOOR_DIR * (FURN_R0 - 0.02) + v3((0, 0, 0.2))
    R = rot_from_axes(z_axis=DOOR_DIR, y_axis=v3((0, 0, 1)))
    fd.sub(RoundBox(dc + v3((0, 0, -0.03)), (0.062, 0.07, 0.09), 0.01, R=R), 0.006)
    fd.sub(Cylinder(dc + v3((0, 0, 0.04)), 0.062, 0.18, rr=0.01, R=R), 0.006)
    return fd


def iron_field():
    """Iron (label 0): two bands round the furnace, a frame round the door, the crucible with its rim and two ring
    handles."""
    fd = Field("Iron")
    for z, r in ((FURN_TOP - 0.02, FURN_R1 + 0.006), (0.3, FURN_R0 - 0.007)):
        fd.add(Torus(FURN + v3((0, 0, z)), r, 0.012), 0.0)
    dc = FURN + DOOR_DIR * (FURN_R0 - 0.01) + v3((0, 0, 0.2))
    def arch(P):
        q = P - dc.astype(F)
        u = q @ np.cross(DOOR_DIR, v3((0, 0, 1))).astype(F)
        w = q[:, 2]
        inner = np.where(w > F(0.04), np.sqrt(u * u + (w - F(0.04)) ** 2) - F(0.062), np.maximum(np.abs(u) - F(0.062), F(-0.12) - w))
        outer = np.where(w > F(0.04), np.sqrt(u * u + (w - F(0.04)) ** 2) - F(0.084), np.maximum(np.abs(u) - F(0.084), F(-0.14) - w))
        return np.maximum(np.maximum(outer, -inner), np.abs(q @ DOOR_DIR.astype(F)) - F(0.012))
    fd.add(Func(arch, dc - 0.2, dc + 0.2), 0.003)
    cc = FURN + v3((0, 0, CRUC_Z))
    pot = Ellipsoid(cc + v3((0, 0, -0.03)), (CRUC_R, CRUC_R, 0.09))
    fd.add(Inter(Shell(pot, 0.0, 0.012, pad=0.05), Func(lambda P: P[:, 2] - F(CRUC_Z), cc - 0.2, cc + 0.2), 0.004), 0.004)
    fd.add(Torus(cc, CRUC_R - 0.002, 0.009), 0.004)
    for s in (-1, 1):
        h = cc + v3((s * (CRUC_R + 0.012), 0, -0.012))
        fd.add(Torus(h, 0.018, 0.0045, R=rot_from_axes(z_axis=(0, 1, 0))), 0.002)
    for k in range(10):                                                       # rivets on the upper band
        a = 2 * math.pi * k / 10 + 0.3
        d = v3((math.cos(a), math.sin(a), 0))
        fd.add(Sphere(FURN + d * (FURN_R1 + 0.017) + v3((0, 0, FURN_TOP - 0.02)), 0.007), 0.002)
    return fd


def plinth_field():
    """A round stone plinth under the furnace."""
    fd = Field("Plinth")
    fd.add(Cylinder(FURN + v3((0, 0, PLINTH_H / 2)), PLINTH_R, PLINTH_H, rr=0.016, disp=lambda P: F(0.003) * NOISE(P * F(18)), disp_amp=0.004), 0.0)
    return fd


def brew_field():
    fd = Field("Brew")
    fd.add(Cylinder(FURN + v3((0, 0, BREW_Z - 0.01)), CRUC_R - 0.01, 0.024, rr=0.008), 0.0)
    for k in range(5):                                                        # bubbles
        a = 2 * math.pi * k / 5 + 0.4
        fd.add(Sphere(FURN + v3((math.cos(a) * 0.045, math.sin(a) * 0.045, BREW_Z + 0.004)), 0.012), 0.004)
    return fd


def coals_field():
    """Glowing coals heaped in the firing door."""
    fd = Field("Coals")
    dc = FURN + DOOR_DIR * (FURN_R0 - 0.07) + v3((0, 0, 0.13))
    rs = np.random.RandomState(9)
    side = np.cross(DOOR_DIR, v3((0, 0, 1)))
    for k in range(9):
        p = dc + side * rs.uniform(-0.045, 0.045) + DOOR_DIR * rs.uniform(-0.03, 0.04) + v3((0, 0, rs.uniform(0.0, 0.04)))
        fd.add(Ellipsoid(p, (0.024, 0.02, 0.016), R=euler(rs.uniform(0, 3), rs.uniform(0, 3), rs.uniform(0, 3))), 0.006)
    return fd


# ======================================================================================= painting
def warm_points():
    return kr.warm_points()


# ======================================================================================= build config
GLB_NAME = "alchemist"
ROOT_NAME = "AlchemistHQ"
TEX_PREFIX = "alch"
MAT_NAME = "AlchemistMat"
MESH_NAME = "Alchemist"
BASE_MODULE = "alchemist_base"
ANIM_MODULE = "anim_alchemist"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Grey", "Kerchief", "Gown", "Apron", "Leather", "Vials", "Spectacles", "Brass",
         "Flask", "Potion", "Stream", "Furnace", "Iron", "Plinth", "Brew", "Coals"]
REGION_PARTS = ("Skin", "Gown", "Apron", "Leather", "Kerchief", "Furnace", "Iron")
GREEN = (0.13, 0.27, 0.17)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_AlchemistSkin", "base": (0.88, 0.68, 0.56), "ruddy": (0.86, 0.52, 0.45), "lips": (0.66, 0.34, 0.33),
                      "brow": ((0.32, 0.2, 0.12), (0.5, 0.34, 0.22)), "paint": (0.24, 0.13, 0.09),
                      "extra": ((LASH, (0.2, 0.12, 0.08), 0.5),)}),
    "Hair": ("hair", {"name": "HQ_AlchemistHair", "base": (0.36, 0.2, 0.11), "hi": (0.62, 0.38, 0.22), "low": (0.16, 0.08, 0.04),
                      "streak": (0.26, 0.14, 0.08), "tint": (0.48, 0.26, 0.14)}),
    "Grey": ("hair", {"name": "HQ_AlchemistGrey", "base": (0.66, 0.64, 0.62), "hi": (0.9, 0.89, 0.87), "low": (0.4, 0.38, 0.37),
                      "streak": (0.54, 0.52, 0.5), "tint": (0.72, 0.7, 0.68)}),
    "Kerchief": ("wool", {"name": "HQ_Kerchief", "base": (0.5, 0.09, 0.07), "border": (0.08, 0.07, 0.07), "stripe": (0.08, 0.07, 0.07)}),
    "Gown": ("wool", {"name": "HQ_AlchemistGown", "base": GREEN, "border": (0.86, 0.64, 0.2), "stripe": (0.06, 0.06, 0.05)}),
    "Apron": ("leather_dyed", {"name": "HQ_AlchemistApron", "base": (0.46, 0.3, 0.17), "dyed": (0.12, 0.08, 0.05)}),
    "Leather": ("leather_dyed", {"name": "HQ_AlchemistLeather", "base": (0.32, 0.2, 0.11), "dyed": (0.5, 0.36, 0.12)}),
    "Vials": ("vials", {"name": "HQ_Vials"}),
    "Spectacles": ("gold", {"name": "HQ_Spectacles"}),
    "Brass": ("gold", {"name": "HQ_AlchemistBrass"}),
    "Flask": ("vials", {"name": "HQ_Vials"}),
    "Furnace": ("mudbrick", {"name": "HQ_Athanor", "base": (0.6, 0.27, 0.17), "mortar": (0.72, 0.64, 0.54), "course": 0.055, "brick": 0.13}),
    "Iron": ("iron", {"name": "HQ_AthanorIron"}),
    "Plinth": ("stone", {"name": "HQ_Plinth", "scale": 0.6}),
}
GLOW = {"Potion": ((0.42, 1.0, 0.3), 1.1, 0.5), "Stream": ((0.42, 1.0, 0.3), 1.1, 0.5), "Brew": ((0.42, 1.0, 0.3), 1.1, 0.5),
        "Coals": ((1.0, 0.45, 0.12), 1.3, 0.5)}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Hair": 1800, "Grey": 300, "Kerchief": 1700, "Gown": 3400, "Apron": 1500,
               "Leather": 2000, "Vials": 700, "Spectacles": 360, "Brass": 360, "Flask": 260, "Potion": 200, "Stream": 60,
               "Furnace": 2400, "Iron": 1600, "Plinth": 400, "Brew": 160, "Coals": 300}
AO_EXCLUDE = ["Flask", "Potion", "Stream", "Brew", "Coals", "Spectacles"]
BAKE_APART = (["Furnace", "Iron", "Plinth", "Brew", "Coals"], (3.0, 0.0, 0.0))


def prop_bones():
    return []


def extra_bones():
    """The furnace stands still (furnace); the brew's surface can swell (brew); the poured stream hangs from the flask's
    mouth (stream, on her right hand: aimed down and stretched to the crucible)."""
    m = flask_mouth()
    return [("furnace", FURN, FURN + v3((0, 0, 0.3)), None),
            ("brew", FURN + v3((0, 0, BREW_Z)), FURN + v3((0, 0, BREW_Z + 0.1)), "furnace"),
            ("stream", m, m - v3((0, 0, STREAM_L)), "hand.R")]


def head_weights(ob, skin_ob, arm):
    """Hair, kerchief: the head; the kerchief's knot and tails at the nape share the neck."""
    groups = {}
    z1 = hp((0, 0, 1.56))[2]
    for v in ob.data.vertices:
        p = v.co
        if p.z >= z1 or p.y < 0.1:
            w = {"head": 1.0}
        else:
            t = max(0.0, min(1.0, (z1 - p.z) / 0.12))
            w = {"head": 1.0 - 0.6 * t, "neck": 0.6 * t}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    skirt = {"thigh.R": 0.5, "thigh.L": 0.5, "shin.R": 0.3, "shin.L": 0.3}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("custom", head_weights), "Grey": ("rigid", "head"),
        "Kerchief": ("custom", head_weights), "Spectacles": ("rigid", "head"),
        "Gown": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "thigh.R", "thigh.L", "shin.R", "shin.L"},
                 skirt),
        "Apron": ("transfer", TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L"}, skirt),
        "Leather": ("transfer", TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Vials": ("rigid", "chest"), "Brass": ("transfer", TORSO | {"thigh.L"}, {"thigh.L": 0.3}),
        "Flask": ("rigid", "hand.R"), "Potion": ("rigid", "hand.R"), "Stream": ("rigid", "stream"),
        "Furnace": ("rigid", "furnace"), "Iron": ("rigid", "furnace"), "Plinth": ("rigid", "furnace"),
        "Brew": ("rigid", "brew"), "Coals": ("rigid", "furnace"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Furnace", "Plinth"):
        return 0.8
    if part in ("Vials", "Spectacles", "Flask"):
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Grey", grey_field(), 0.0018 if fine else 0.0026),
        ("Kerchief", kerchief_field(), 0.0024 if fine else 0.0034),
        ("Gown", gown_field(), 0.0026 if fine else 0.0036),
        ("Apron", apron_field(), 0.0024 if fine else 0.0034),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Vials", vials_field(), 0.0014 if fine else 0.002),
        ("Spectacles", spectacles_field(), 0.0012 if fine else 0.0016),
        ("Brass", funnel_field(), 0.0016 if fine else 0.0022),
        ("Flask", flask_field(), 0.0014 if fine else 0.002),
        ("Potion", potion_field(), 0.002 if fine else 0.003),
        ("Stream", stream_field(), 0.002 if fine else 0.003),
        ("Furnace", furnace_field(), 0.003 if fine else 0.0042),
        ("Iron", iron_field(), 0.0022 if fine else 0.003),
        ("Plinth", plinth_field(), 0.003 if fine else 0.0042),
        ("Brew", brew_field(), 0.002 if fine else 0.003),
        ("Coals", coals_field(), 0.002 if fine else 0.003),
    ]
