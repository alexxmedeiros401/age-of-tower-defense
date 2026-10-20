"""Kael Hillwarden, Javelin Hunter (HQ hero, Iron Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A hunter of the hill country in his prime, weathered and watchful: dark brown hair drawn back from his brow under a
leather headband and bound in a short tail, a short dark beard trimmed close, an old scar through his left brow; a long
cloak of green-and-blue checked wool with an ochre border hanging from his shoulders to mid-thigh, a roll of grey wolf
fur round its neck, pinned at the front of his shoulders by two gold disc brooches with a gold chain sagging between
them; a sleeveless russet tunic checked in green, belted, over brown checked trousers bound with thongs; leather
bracers, a twisted gold torc and gold armlets; a hunting horn on its cord at his left hip. An iron-headed javelin in
his right fist, four more in a leather case on his back (slung over the cloak).

He shares the Javelin Thrower's build (javelin.py): his body, clothes, case and javelin come from there, so the throw
(anim_javelin.py) fits him as it is. The cloak hangs from two bones (cape.1, cape.2) that the clips aim in world
space."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import javelin as jv
from javelin import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S, CURLS,
                     fist_center, hand, foot, torso_prims, traps, neck_prim, deltoid, upper_arm_prims, leg_prims, arm_hull,
                     eyes_field, teeth_field, tunic_base, tunic_field, trousers_field, leather_field, javelin_axis, javelin_field,
                     quiver_field, Q_TOP, Q_BOT, Q_R, case_heads, JAV_FWD, JAV_BACK, JAV_R, BELT_Z, torso_bones, prop_bones,
                     TORSO, TORSO_Z, baldric_plane, gold_weights, leather_weights, _rigid)

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, SCAR = 0, 1, 2, 3, 4, 5, 8, 9


# ======================================================================================= head
def head(fd):
    """The Javelin Thrower's lean face, older and harder: a broader jaw (under the beard), lines at his eyes, a scar
    through his left brow; brows drawn low and level."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.055, 1.59), (0.14, 0.13, 0.124)), 0.07, SKIN)
    fd.add(E((0, -0.134, 1.502), (0.086, 0.068, 0.066)), 0.05, SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.114, -0.117, 1.634), 0.048), 0.05, SKIN)
        fd.add(S((sx * 0.124, -0.045, 1.56), 0.05), 0.05, SKIN)
        pts = [hp((sx * 0.152, -0.055, 1.742)), hp((sx * 0.116, -0.13, 1.752)), hp((sx * 0.06, -0.174, 1.75)), hp((0.0, -0.184, 1.748))]
        fd.add(Chain(pts, [hr(0.013), hr(0.022), hr(0.026), hr(0.025)], k=hr(0.022)), hr(0.035), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.1, -0.142, 1.598)), v3((0.026, 0.014, 0.034)) * HS, R=euler(0, 0, sx * 0.4)), hr(0.016))
    for sx in (-1, 1):
        pts = [hp((sx * 0.024, -0.215, 1.752)), hp((sx * 0.066, -0.208, 1.762)), hp((sx * 0.11, -0.186, 1.768)), hp((sx * 0.153, -0.144, 1.764))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.01), hr(0.012), hr(0.011), hr(0.005)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.018), hr(0.02), hr(0.018), hr(0.01)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0066)), Plane(ec + v3((0, 0, hr(0.015))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)                                              # a hunter's narrowed eyes
        lo = Inter(Sphere(ec, EYE_R + hr(0.005)), Plane(ec + v3((0, 0, -hr(0.023))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.013))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(2):                                                       # lines at the corners of his eyes
            a = hp((sx * (0.112 + 0.004 * k), -0.132 + 0.006 * k, 1.676 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.02, 0.012, -0.003 - 0.008 * k)), hr(0.002), hr(0.0014)), hr(0.003))
    # the scar: a pale raised seam through his left brow, from the forehead down onto the cheekbone
    sc = [hp((0.07, -0.19, 1.81)), hp((0.082, -0.2, 1.77)), hp((0.094, -0.19, 1.725)), hp((0.104, -0.17, 1.69))]
    fd.add(Chain(sc, [hr(0.0035), hr(0.0045), hr(0.004), hr(0.003)], k=hr(0.003)), hr(0.003), SCAR)
    fd.paint(Chain(sc, [hr(0.007), hr(0.009), hr(0.008), hr(0.006)], k=hr(0.004)), SCAR)
    # a straight nose, a little broken
    fd.add(RoundCone(hp((0, -0.182, 1.724)), hp((0.004, -0.242, 1.626)), hr(0.017), hr(0.024)), hr(0.016), SKIN)
    fd.add(S((0.003, -0.216, 1.69), 0.019), hr(0.01), SKIN)
    fd.add(S((0.004, -0.244, 1.612), 0.027), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.03 + 0.003, -0.215, 1.602), 0.02), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.016 + 0.003, -0.232, 1.589)), v3((0.009, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    slot = [hp((-0.054, -0.17, 1.548)), hp((-0.028, -0.193, 1.545)), hp((0, -0.199, 1.546)), hp((0.028, -0.193, 1.545)), hp((0.054, -0.17, 1.548))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0036), hr(0.0032), hr(0.0025)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.005), hr(0.0045), hr(0.0032)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.045, -0.17, 1.539), (-0.024, -0.186, 1.531), (0, -0.19, 1.529), (0.024, -0.186, 1.531), (0.045, -0.17, 1.539)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.008), hr(0.009), hr(0.008), hr(0.005)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.176, 0.035, 1.66)), v3((0.026, 0.047, 0.06)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.194, 0.028, 1.664)), v3((0.011, 0.03, 0.04)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.009))


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        el, wr = J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        for p, k in upper_arm_prims(side):
            fd.add(p, k, SKIN)
        fd.add(RoundCone(el, wr, 0.068, 0.053), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.087, 0.078, 0.128), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.054), 0.028, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    jv.woad(fd)                                           # the hill folk's woad spirals on his upper arms
    return fd


# ======================================================================================= hair, beard
def hair_hull():
    hull = Field("HairHull")
    hull.add(Ellipsoid(HEAD_C, HEAD_RAD + v3((0.014, 0.018, 0.014))), 0.0)
    hull.add(Ellipsoid(hp((0, 0.11, 1.65)), v3((0.17, 0.12, 0.15)) * HS), 0.07)          # drawn back to the nape
    return hull


HB_F = v3((0.0, -0.12, 1.8))          # the headband's front (design units): across his forehead below the hairline,
HB_B = v3((0.0, 0.17, 1.72))          # lower behind


def band_d(P):
    """Height above the headband's centre plane (design units)."""
    n = norm(v3((0.0, -(HB_B[2] - HB_F[2]) / (HB_B[1] - HB_F[1]), 1.0)))
    return (hinv(P) - HB_F.astype(F)) @ n.astype(F)


TAIL = [v3((0.0, 0.2, 1.63)), v3((0.0, 0.25, 1.56)), v3((0.0, 0.298, 1.49)), v3((0.0, 0.322, 1.42)), v3((0.0, 0.33, 1.37))]
TAIL_W = [0.04, 0.036, 0.03, 0.022, 0.008]
TAIL_T = [0.024, 0.022, 0.018, 0.014, 0.006]


def hair_field():
    """Dark brown hair drawn straight back from his brow under the headband (the grooves of the comb running back over
    his head), gathered at the nape and bound in a long tail down his back."""
    fd = Field("Hair")
    hull = hair_hull()
    def strands(P):
        Q = hinv(P)
        a = np.arctan2(Q[:, 0], F(0.6))                                       # grooves running front to back
        return F(0.0024) * np.sin(Q[:, 0] * F(260) + F(0.4) * np.sin(Q[:, 1] * F(30))) + F(0.0012) * NOISE(P * np.array([60, 20, 60], F))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        line = F(-0.13) + F(0.1) * smoothstep(0.08, 0.17, ax) + F(0.12) * smoothstep(1.78, 1.66, z)   # the hairline
        front = np.where(z > F(1.6), line - y, F(-1.0))
        ear = np.where((ax > F(0.15)) & (z < F(1.72)) & (z > F(1.55)), F(0.06) - y, F(-1.0))
        bottom = F(1.58) - z
        return np.maximum(np.maximum(front, ear), bottom)
    fd.add(Inter(Shell(hull, 0.0, 0.03, pad=0.08, disp=strands, disp_amp=0.004), Func(keep, HEAD_C - 0.45, HEAD_C + 0.35), 0.005), 0.0)
    # the tail: gathered at the nape, falling down his back over the wolf skin, tapering
    lk = lambda P: F(0.0022) * np.sin(P[:, 0] * F(300)) + F(0.0016) * NOISE(P * np.array([70, 70, 14], F))
    fd.add(tail_lock(lk, 0.003), 0.012)
    return fd


def beard_hull():
    fd = Field("BeardHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.055, 1.59), (0.14, 0.13, 0.124)), 0.07)
    fd.add(E((0, -0.134, 1.502), (0.086, 0.068, 0.066)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.114, -0.117, 1.634)), hr(0.048)), 0.05)
        fd.add(Sphere(hp((sx * 0.124, -0.045, 1.56)), hr(0.05)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


def beard_tex(P):
    x, z = P[:, 0], P[:, 2]
    ph = x / F(0.018) + F(0.3) * np.sin(z * F(60) + x * F(9))
    lock = np.abs(np.sin(ph * F(math.pi)))
    return F(0.0018) - F(0.0036) * lock * lock + F(0.001) * NOISE(P * np.array([110, 110, 40], F))


def beard_field():
    """A short dark beard trimmed close along his jaw and chin, up to the sideburns; a full moustache over his mouth."""
    fd = Field("Beard")
    hull = beard_hull()
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.555) + F(0.085) * smoothstep(0.06, 0.14, ax)
        top = np.where(ax > F(0.15), F(1.705), top)
        lips = (x / F(0.062)) ** 2 + ((y + F(0.18)) / F(0.07)) ** 2 + ((z - F(1.543)) / F(0.022)) ** 2 - F(1.0)
        back = np.where(ax > F(0.14), y - F(0.035), y - F(0.0))
        return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), F(1.45) - z)
    fd.add(Inter(Shell(hull, 0.006, 0.014, pad=0.06, disp=beard_tex, disp_amp=0.004), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.006), 0.0)
    fd.add(Ellipsoid(hp((0, -0.148, 1.478)), v3((0.098, 0.06, 0.05)) * HS, disp=beard_tex, disp_amp=0.004), 0.03)
    strands = lambda P: F(0.0018) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.226, 1.578)), hp((sx * 0.04, -0.214, 1.567)), hp((sx * 0.064, -0.196, 1.546)),
               hp((sx * 0.072, -0.184, 1.522))]
        fd.add(Lock(pts, [hr(0.013), hr(0.017), hr(0.014), hr(0.008)], [hr(0.01), hr(0.011), hr(0.009), hr(0.006)],
                    [norm(v3((sx * 0.3, -1, 0.15)))] * 4, k=hr(0.006), disp=strands, disp_amp=0.003), hr(0.006))
    return fd


# ======================================================================================= the cloak, the fur collar
CLOAK_HEM = 0.6            # the cloak's hem at the middle of his back (mid-thigh)


def cloak_base():
    b = Field("CloakBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.05)
    b.add(neck_prim(), 0.05)
    b.add(RoundBox((0.0, 0.05, 0.74), (0.29, 0.17, 0.26), 0.1, R=euler(0.04, 0, 0)), 0.16)     # it hangs, not hugging his waist
    return b


def _cloak_edges(P):
    """(front edge, side edges, hem): each > 0 outside the cloak."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    up = smoothstep(1.12, 1.36, z)
    front = (F(0.07) - F(0.13) * up + F(0.01) * NOISE(P * F(9))) - y           # over his shoulders it comes forward
    side = np.abs(x) - (F(0.35) + F(0.012) * NOISE(P * F(11) + 3))
    hem = (F(CLOAK_HEM) + F(0.2) * smoothstep(0.2, 0.0, y) + F(0.012) * np.sin(x * F(40)) + F(0.01) * NOISE(P * F(7))) - z
    return front, side, hem


def cloak_keep(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front, side, hem = _cloak_edges(P)
    neck = np.where(z > F(1.42), F(0.15) - np.sqrt(x * x + (y - F(0.07)) ** 2), F(-1))
    return np.maximum(np.maximum(np.maximum(front, side), hem), neck)


def cloak_field():
    """A long cloak of green-and-blue checked wool: over his shoulders (under the fur collar), down his back to
    mid-thigh, a woven border (label 5) along its edges; it hangs in folds below his shoulder blades."""
    fd = Field("Cloak")
    base = cloak_base()
    def folds(P):
        lo = smoothstep(1.2, 0.75, P[:, 2])
        return F(0.012) * np.sin(P[:, 0] * F(26) + F(0.7) * NOISE(P * F(3))) * lo + F(0.0015) * NOISE(P * F(30))
    def shell(P):
        d = base.eval(P, margin=0.12)
        off = F(0.038) + F(0.024) * smoothstep(1.3, 1.44, P[:, 2]) + folds(P)       # higher over the shoulders: over the strap
        return np.abs(d - off) - F(0.008)
    lo, hi = (-0.6, -0.4, 0.4), (0.6, 0.6, 1.72)
    fd.add(Inter(Func(shell, lo, hi), Func(cloak_keep, lo, hi), 0.004), 0.0)
    def border(P):
        front, side, hem = _cloak_edges(P)
        return -(np.maximum(np.maximum(front, side), hem) + F(0.034))
    fd.paint(Func(border, lo, hi), 5)
    return fd


def collar_path():
    """The fur collar's centre line: from the front of his right shoulder, over it, round the back of his neck and over
    his left shoulder to its front (rays dropped onto the cloak's base)."""
    base = cloak_base()
    f = Func(lambda P: base.eval(P, margin=0.1) - F(0.045), (-0.8, -0.6, 0.9), (0.8, 0.6, 1.9))
    pts = []
    for k in range(15):
        a = math.radians(-136 + 272 * k / 14)               # 0 = behind his neck
        o = v3((0.235 * math.sin(a), 0.045 + 0.175 * math.cos(a), 2.0))
        h, ok = ray_hit(f, [o], [v3((0, 0, -1))], tmax=0.9)
        pts.append(h[0] if ok[0] else o - v3((0, 0, 0.55)))
    return pts


def brooch_frames():
    """(centre, facing) of the two gold brooches pinning the cloak's corners, in front of the collar's ends."""
    pts = collar_path()
    out = []
    for e, i in ((pts[0], 1), (pts[-1], -2)):
        d = norm(e - pts[i])                                  # along the collar, out past its end
        face = norm(v3((e[0] * 1.2, -1.0, 0.45)))
        out.append((e + d * 0.02 + face * 0.032, face))
    return out


def fur_field():
    """A thick roll of grey wolf fur round the cloak's neck, over his shoulders and behind his neck."""
    fd = Field("Fur")
    pts = collar_path()
    fur = lambda P: F(0.007) * NOISE(P * np.array([34, 34, 14], F)) + F(0.003) * NOISE(P * F(95))
    rads = [0.034 + 0.012 * math.sin(math.pi * k / 14) for k in range(15)]
    fd.add(Chain(pts, rads, k=0.012, disp=fur, disp_amp=0.01), 0.0)
    return fd


def chain_path():
    """The gold chain between the brooches: sagging across his upper chest below the torc, laid on the tunic."""
    (b0, _), (b1, _) = brooch_frames()
    tb = tunic_base()
    f = Func(lambda P: tb.eval(P, margin=0.1) - F(0.04), (-0.6, -0.7, 0.9), (0.6, 0.5, 1.7))
    pts = []
    for k in range(13):
        u = k / 12
        x = b0[0] + (b1[0] - b0[0]) * u
        z = b0[2] + (b1[2] - b0[2]) * u - 0.075 * math.sin(math.pi * u) - 0.012
        h, ok = ray_hit(f, [v3((x, -0.8, z))], [v3((0, 1, 0))], tmax=0.9)
        if ok[0]:
            pts.append(h[0])
    return pts


# ======================================================================================= gold, horn, headband
def gold_field():
    """The torc and the belt buckle (as the Javelin Thrower's); broad gold armlets on his upper arms; two disc brooches
    pinning the cloak at the front of his shoulders (a raised boss in a ring of granules) and a chain sagging between
    them across his chest; the horn's mounts."""
    fd = jv.gold_field()
    fd.name = "Gold"
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        hull = arm_hull(side)
        ax = norm(el - sh)
        c = lerp(sh, el, 0.62)
        fd.add(Inter(Shell(hull, 0.008, 0.016, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.026),
                                                               c - 0.2, c + 0.2), 0.003), 0.004)
        for s_ in (-1, 1):
            fd.add(Inter(Shell(hull, 0.018, 0.006, pad=0.06), Func(lambda P, c=c, ax=ax, s_=s_: np.abs((P - c.astype(F)) @ ax.astype(F) - F(s_ * 0.022)) - F(0.004),
                                                                   c - 0.2, c + 0.2), 0.002), 0.003)
    for c, face in brooch_frames():
        R = rot_from_axes(z_axis=face)
        fd.add(Cylinder(c, 0.034, 0.009, rr=0.004, R=R), 0.0)
        fd.add(Torus(c + face * 0.004, 0.031, 0.0045, R=R), 0.002)
        fd.add(Sphere(c + face * 0.002, 0.016), 0.006)
        u = norm(np.cross(face, v3((0, 0, 1))))
        w = norm(np.cross(face, u))
        for k in range(10):
            a = 2 * math.pi * k / 10
            fd.add(Sphere(c + face * 0.005 + (u * math.cos(a) + w * math.sin(a)) * 0.023, 0.0042), 0.001)
    pts = chain_path()
    link = lambda P: F(0.0016) * np.abs(np.sin(P[:, 0] * F(260)))
    fd.add(Chain(pts, [0.0048] * len(pts), k=0.002, disp=link, disp_amp=0.0016), 0.002)
    for c, r in horn_mounts():
        a, d = c
        fd.add(Torus(a, r + 0.004, 0.006, R=rot_from_axes(z_axis=d)), 0.003)
    return fd


def horn_curve():
    """The hunting horn's centre line, from its mouthpiece (at the front of his left hip) curving down and back to its
    bell at his side, with its radius along it."""
    tb = tunic_base()
    h, ok = ray_hit(Func(lambda P: tb.eval(P, margin=0.1) - F(0.062), (-0.6, -0.6, 0.6), (0.6, 0.6, 1.1)), [v3((0.7, -0.06, 0.86))],
                    [v3((-1, 0, 0))], tmax=0.8)
    c = h[0] if ok[0] else v3((0.27, -0.06, 0.86))
    pts, rads = [], []
    for k in range(10):
        t = k / 9
        ang = math.pi * 0.9 * t
        p = c + v3((0.02 * math.sin(ang), -0.1 * math.cos(ang) + 0.02, -0.085 * math.sin(ang) - 0.01 * t))
        pts.append(p)
        rads.append(0.011 + 0.028 * t ** 1.6)
    return pts, rads


def horn_mounts():
    pts, rads = horn_curve()
    d0 = norm(pts[1] - pts[0])
    d1 = norm(pts[-1] - pts[-2])
    return [((pts[0] + d0 * 0.01, d0), rads[0]), ((pts[-1] - d1 * 0.012, d1), rads[-1])]


def horn_field():
    """A cow horn, pale and polished, banded darker toward its tip."""
    fd = Field("Horn")
    pts, rads = horn_curve()
    fd.add(Chain(pts, rads, k=0.004, disp=lambda P: F(0.001) * NOISE(P * F(60)), disp_amp=0.001), 0.0)
    d1 = norm(pts[-1] - pts[-2])
    fd.sub(RoundCone(pts[-1] - d1 * 0.03, pts[-1] + d1 * 0.02, rads[-1] - 0.007, rads[-1] - 0.004), 0.004)              # its bell
    return fd


def tail_lock(disp=None, amp=0.0):
    return Lock(TAIL, TAIL_W, TAIL_T, [v3((0, 1, 0.1))] * len(TAIL), k=0.01, disp=disp, disp_amp=amp)


def kit_field():
    """Leather: the headband round his brow, two thongs binding his tail, the horn's cord from his belt."""
    fd = Field("Kit")
    hull = hair_hull()
    def band(P):                       # on his skin across the forehead and temples, on the hair round the back
        d = hull.eval(P, margin=0.06)
        yd = hinv(P)[:, 1]
        off = F(-0.008) + F(0.03) * smoothstep(-0.06, 0.02, yd)
        return np.maximum(np.abs(d - off) - F(0.006), np.abs(band_d(P)) - F(0.016))
    fd.add(Func(band, HEAD_C - 0.4, HEAD_C + 0.4), 0.0)
    lock = tail_lock()
    for u in (0.3, 0.62):
        c = lerp(TAIL[0], TAIL[1], u)
        d = norm(TAIL[1] - TAIL[0])
        fd.add(Inter(Shell(lock, 0.002, 0.009, pad=0.04), Func(lambda P, c=c, d=d: np.abs((P - c.astype(F)) @ d.astype(F)) - F(0.0065),
                                                              c - 0.1, c + 0.1), 0.002), 0.003)
    pts, rads = horn_curve()
    a = pts[0] + v3((0.0, 0.0, 0.02))
    b = pts[-1] + v3((0.0, 0.0, 0.035))
    top = v3((pts[0][0] - 0.02, pts[0][1] + 0.03, BELT_Z - 0.01))
    fd.add(Chain([top, a], [0.0045, 0.0045], k=0.0), 0.002)
    fd.add(Chain([top + v3((0.0, 0.05, 0.0)), b], [0.0045, 0.0045], k=0.0), 0.002)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = jv.warm_points()
    pts.append((hp((0.09, -0.19, 1.74)), 0.03, 0.4))                       # the scar's flush
    return pts


# ======================================================================================= build config
GLB_NAME = "kael"
ROOT_NAME = "HeroKaelHQ"
TEX_PREFIX = "hero"
MAT_NAME = "KaelMat"
MESH_NAME = "Kael"
BASE_MODULE = "kael_base"
ANIM_MODULE = "anim_kael"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Gold", "Tunic", "Trousers", "Leather", "Kit", "Cloak", "Fur", "Horn", "Quiver",
         "Javelin"]
REGION_PARTS = ("Skin", "Tunic", "Quiver", "Javelin", "Cloak")
DARK = {"name": "HQ_KaelHair", "base": (0.2, 0.13, 0.08), "hi": (0.42, 0.29, 0.18), "low": (0.08, 0.05, 0.03),
        "streak": (0.13, 0.08, 0.05), "tint": (0.28, 0.18, 0.1)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_KaelSkin", "base": (0.8, 0.58, 0.44), "ruddy": (0.84, 0.46, 0.36), "lips": (0.64, 0.38, 0.33),
                      "brow": ((0.12, 0.08, 0.05), (0.26, 0.17, 0.11)), "paint": (0.1, 0.22, 0.56),
                      "extra": ((LASH, (0.1, 0.07, 0.05), 0.5), (SCAR, (0.86, 0.6, 0.55), 0.5))}),
    "Hair": ("hair", DARK),
    "Beard": ("hair", dict(DARK, name="HQ_KaelBeard")),
    "Gold": ("gold", {"name": "HQ_KaelGold"}),
    "Tunic": ("plaid", {"name": "HQ_KaelTunic", "base": (0.46, 0.23, 0.11), "stripe": (0.2, 0.3, 0.14), "line": (0.86, 0.76, 0.42),
                        "border": (0.2, 0.3, 0.14)}),
    "Trousers": ("plaid", {"name": "HQ_KaelTrousers", "base": (0.27, 0.19, 0.12), "stripe": (0.44, 0.22, 0.1),
                           "line": (0.56, 0.48, 0.28), "border": (0.44, 0.22, 0.1), "period": 0.1}),
    "Cloak": ("plaid", {"name": "HQ_KaelCloak", "base": (0.15, 0.3, 0.15), "stripe": (0.09, 0.13, 0.26), "line": (0.8, 0.66, 0.24),
                        "border": (0.74, 0.54, 0.16), "period": 0.14}),
    "Fur": ("fur", {"name": "HQ_WolfCollar", "base": (0.36, 0.35, 0.33), "tip": (0.8, 0.78, 0.74)}),
    "Leather": ("leather", {"name": "HQ_KaelLeather", "base": (0.34, 0.21, 0.11)}),
    "Kit": ("leather", {"name": "HQ_KaelLeather", "base": (0.34, 0.21, 0.11)}),
    "Horn": ("bone", {"name": "HQ_HuntHorn", "banded": True}),
    "Quiver": ("javelin_case", {"name": "HQ_KaelCase", "base": (0.32, 0.2, 0.1)}),
    "Javelin": ("javelin_shaft", {"name": "HQ_Javelin"}),
}
LOW_TARGETS = {"Skin": 6400, "Hair": 1100, "Beard": 900, "Teeth": 60, "Gold": 900, "Tunic": 2000, "Trousers": 1500, "Leather": 1800,
               "Kit": 420, "Cloak": 2400, "Fur": 1100, "Horn": 260, "Quiver": 1100, "Javelin": 420}
AO_EXCLUDE = ["Javelin"]


def extra_bones():
    """The cloak hangs from two bones down his back (aimed in world space by the clips, so it trails his moves)."""
    return [("cape.1", (0.0, 0.29, 1.3), (0.0, 0.31, 0.98), "chest"),
            ("cape.2", (0.0, 0.31, 0.98), (0.0, 0.33, 0.6), "cape.1")]


def cloak_weights(ob, skin_ob, arm):
    """Chest over his shoulders (a little of the clavicles at their tops), blending into the two cape bones down his
    back."""
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        z = p.z
        if z > 1.3:
            w_cl = max(0.0, min(1.0, (abs(p.x) - 0.16) / 0.14)) * 0.4
            w = {"chest": 1.0 - w_cl}
            if w_cl > 0.01:
                w["clavicle.R" if p.x < 0 else "clavicle.L"] = w_cl
        elif z > 1.04:
            t = (1.3 - z) / 0.26
            w = {"chest": 1 - t, "cape.1": t}
        elif z > 0.82:
            t = (1.04 - z) / 0.22
            w = {"cape.1": 1 - t * 0.6, "cape.2": t * 0.6}
        else:
            t = min(1.0, (0.82 - z) / 0.2)
            w = {"cape.1": 0.4 * (1 - t), "cape.2": 0.6 + 0.4 * t}
        _blend_add(ob, groups, v.index, w)


def fur_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        w_cl = max(0.0, min(1.0, (abs(p.x) - 0.14) / 0.1)) * 0.3
        w = {"chest": 1.0 - w_cl}
        if w_cl > 0.01:
            w["clavicle.R" if p.x < 0 else "clavicle.L"] = w_cl
        _blend_add(ob, groups, v.index, w)


def hair_weights(ob, skin_ob, arm):
    """His head; the tail down the back of his neck blends from the head into the neck and chest."""
    groups = {}
    for v in ob.data.vertices:
        z, y = v.co.z, v.co.y
        if y > 0.17 and z < 1.62:
            k = min(1.0, max(0.0, (z - 1.38) / 0.24))
            w = {"head": 0.25 + 0.75 * k * k, "neck": 0.45 * (1 - k * k), "chest": 0.3 * (1 - k * k)}
        else:
            w = {"head": 1.0}
        _blend_add(ob, groups, v.index, w)


def gold_weights_k(ob, skin_ob, arm):
    """The torc, brooches, chain and buckle as the Javelin Thrower's torc and buckle (chest; the belt); the armlets
    ride the upper arms; the horn's mounts his hip."""
    gold_weights(ob, skin_ob, arm)
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if abs(p.x) > 0.36 and p.z > 1.05:
            _rigid(ob, groups, v, {"upperarm.R" if p.x < 0 else "upperarm.L": 1.0})
        elif p.x > 0.2 and p.z < 0.95:
            _rigid(ob, groups, v, {"root": 0.6, "thigh.L": 0.4})


def kit_weights(ob, skin_ob, arm):
    groups = {}
    for v in ob.data.vertices:
        p = v.co
        if p.z > 1.62:
            w = {"head": 1.0}
        elif p.y > 0.15:
            k = min(1.0, max(0.0, (p.z - 1.38) / 0.24))
            w = {"head": 0.25 + 0.75 * k * k, "neck": 0.45 * (1 - k * k), "chest": 0.3 * (1 - k * k)}
        else:
            w = {"root": 0.6, "thigh.L": 0.4}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Hair": ("custom", hair_weights), "Beard": ("rigid", "head"), "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"),
        "Gold": ("custom", gold_weights_k), "Leather": ("custom", leather_weights), "Kit": ("custom", kit_weights),
        "Cloak": ("custom", cloak_weights), "Fur": ("custom", fur_weights), "Horn": ("transfer", {"root", "thigh.L"}, {"thigh.L": 0.4}),
        "Tunic": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Trousers": ("transfer", TORSO | {"thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Quiver": ("rigid", "chest"), "Javelin": ("rigid", "javelin"),
    }


def uv_boost(c, part):
    return jv.uv_boost(c, "Moustache" if part == "Beard" else part)


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Beard", beard_field(), 0.0018 if fine else 0.0026),
        ("Gold", gold_field(), 0.0016 if fine else 0.0024),
        ("Tunic", tunic_field(), 0.0026 if fine else 0.0036),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Kit", kit_field(), 0.0018 if fine else 0.0026),
        ("Cloak", cloak_field(), 0.0028 if fine else 0.0038),
        ("Fur", fur_field(), 0.0026 if fine else 0.0036),
        ("Horn", horn_field(), 0.0016 if fine else 0.0024),
        ("Quiver", quiver_field(), 0.0022 if fine else 0.003),
        ("Javelin", javelin_field(), 0.0016 if fine else 0.0022),
    ]
