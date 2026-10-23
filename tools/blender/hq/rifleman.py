"""The Rifleman (HQ tower, Industrial Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A lean, steady marksman of the steam corps in his thirties, built on the Musketeer's long, rangy skeleton: a weathered,
clean-cut face (a square jaw, a straight nose, keen grey-blue eyes under level brows), short brown hair, neat sideburns
and a trimmed moustache. A navy-blue peaked cap (a forage cap with a flat top, a black band, brass piping round its
crown, a glossy black leather peak and chin strap, a brass corps badge at the front). A navy wool tunic with a high
stand collar piped in brass, brass buttons down the front, shoulder straps and pointed cuffs; navy trousers; khaki
puttees wound from the ankle to below the knee; black ankle boots. Buff webbing: a belt with a brass buckle and two
ammunition pouches; over his left shoulder a brown leather bandolier of brass cartridges.

The rifle: a bolt-action service rifle (1.3 m): a walnut stock with a semi-pistol grip, a blued barrel and receiver,
the box magazine under it, a brass butt plate, two barrel bands, sights, a leather sling between its swivels. The bolt
(its cocking piece, the bolt body and the handle with its round knob) is a bone of its own: the clips lift it, draw it
back, run it home and turn it down.

His body is the Musketeer's (musketeer.py: skeleton, hands, feet, limbs) with his own head and face. The rifle and the
bolt are props on bones with no parent, posed directly in every frame ("world" aims in anim_rifleman.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
import musketeer as mk
from musketeer import (J, hp, hr, hinv, HS, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S,
                       fist_center, hand, foot, torso_prims, traps, neck_prim, deltoid, upper_arm_prims, forearm_prims,
                       leg_prims, shin_prims, _arm_seg_dist, layer, _fgrad, strap_d, _strap_plane, torso_bones, TORSO_Z,
                       TORSO)

SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE = 0, 1, 2, 3, 4, 8, 9
IRIS = ((0.2, 0.26, 0.32), (0.46, 0.58, 0.66))           # keen grey-blue eyes (prep.paint_eyes)


# ======================================================================================= head
def stubble_mask(P):
    """Cheeks, jaw and chin (design coordinates): the shadow of a close shave."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.6) + F(0.02) * smoothstep(0.06, 0.15, ax)
    return np.maximum(np.maximum(z - top, F(1.45) - z), y - F(0.03))


def head(fd):
    """A clean-cut, weathered face: a square jaw and a firm chin with a cleft, cheekbones over flat cheeks, a straight
    nose, level brows over keen eyes (crow's feet from squinting down a barrel), a firm mouth; ears showing under the
    cap."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.05, 1.588), (0.124, 0.124, 0.12)), 0.07, SKIN)                            # a square jaw
    fd.add(E((0, -0.13, 1.505), (0.08, 0.066, 0.064)), 0.05, SKIN)                            # a firm, broad chin
    fd.sub(RoundCone(hp((0, -0.2, 1.488)), hp((0, -0.196, 1.512)), hr(0.004), hr(0.003)), hr(0.006))   # its cleft
    for sx in (-1, 1):
        fd.add(S((sx * 0.1, -0.12, 1.64), 0.036), 0.05, SKIN)                                  # cheekbones
        fd.add(S((sx * 0.114, -0.05, 1.566), 0.042), 0.05, SKIN)                               # square jaw corners
        pts = [hp((sx * 0.15, -0.055, 1.744)), hp((sx * 0.114, -0.13, 1.752)), hp((sx * 0.06, -0.174, 1.75)), hp((0.0, -0.184, 1.75))]
        fd.add(Chain(pts, [hr(0.012), hr(0.022), hr(0.026), hr(0.026)], k=hr(0.022)), hr(0.035), SKIN)     # brow ridge
        fd.sub(Ellipsoid(hp((sx * 0.116, -0.114, 1.58)), v3((0.022, 0.016, 0.024)) * HS, R=euler(0, 0, sx * -0.5)), hr(0.02))
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # level brows, thick, a little drawn down at their inner ends (a steady, keen look)
    for sx in (-1, 1):
        pts = [hp((sx * 0.022, -0.212, 1.752)), hp((sx * 0.064, -0.208, 1.766)), hp((sx * 0.108, -0.188, 1.772)), hp((sx * 0.15, -0.146, 1.766))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.012), hr(0.014), hr(0.012), hr(0.006)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.019), hr(0.021), hr(0.019), hr(0.011)], k=hr(0.01)), BROW)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.0145))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0056)), Plane(ec + v3((0, 0, -hr(0.019))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0135))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(3):                                                                      # crow's feet
            a = hp((sx * (0.108 + 0.004 * k), -0.134 + 0.006 * k, 1.688 - 0.011 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.024, 0.012, 0.006 - 0.01 * k)), hr(0.002), hr(0.0013)), hr(0.003))
    # a straight nose
    fd.add(RoundCone(hp((0, -0.188, 1.728)), hp((0, -0.246, 1.628)), hr(0.015), hr(0.021)), hr(0.016), SKIN)
    fd.add(S((0, -0.248, 1.612), 0.024), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.027, -0.22, 1.602), 0.018), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.014, -0.236, 1.592)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # mouth: a firm line under the moustache, a full lower lip
    slot = [hp((-0.05, -0.174, 1.552)), hp((-0.026, -0.195, 1.548)), hp((0, -0.201, 1.547)), hp((0.026, -0.195, 1.548)), hp((0.05, -0.174, 1.552))]
    fd.sub(Chain(slot, [hr(0.0024), hr(0.003), hr(0.0034), hr(0.003), hr(0.0024)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.003)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.04, -0.174, 1.541), (-0.021, -0.19, 1.533), (0, -0.194, 1.531), (0.021, -0.19, 1.533), (0.04, -0.174, 1.541)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.005), hr(0.0075), hr(0.0082), hr(0.0075), hr(0.005)], k=hr(0.006)), hr(0.007), LIP)
    # ears (showing under his cap): a rim, a hollow
    for sx in (-1, 1):
        R = euler(0, sx * 0.25, sx * -0.35)
        c = hp((sx * 0.157, 0.035, 1.66))
        fd.add(Ellipsoid(c, v3((0.02, 0.04, 0.052)) * HS, R=R), hr(0.02), SKIN)
        out = norm(R @ v3((sx, 0, 0)))
        fd.sub(Ellipsoid(c + out * hr(0.016) + v3((0, -0.004, -0.004)), v3((0.008, 0.022, 0.028)) * HS, R=R), hr(0.006))
        fd.add(Ellipsoid(c + v3((0, 0.002, -0.042)) + out * hr(0.004), v3((0.012, 0.016, 0.016)) * HS, R=R), hr(0.01), SKIN)   # lobe


# ======================================================================================= body
def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        fd.add(deltoid(side), 0.055, SKIN)
        for p, k in upper_arm_prims(side) + forearm_prims(side):
            fd.add(p, k, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side) + shin_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def _under_cap(P):
    """< 0 where the head may be: below the cap's band, or well inside its crown (nothing of him shows through the felt)."""
    q = cap_local(P)
    return np.minimum(q[:, 2] + F(0.004), crown_sd(q) + F(CAP_T + 0.004))


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    fd.inter(Func(_under_cap, CAP_O - 0.5, CAP_O + 0.5), 0.003)
    return fd


def eyes_field():
    fd = Field("Eyes")
    for sx in (-1, 1):
        fd.add(Sphere(eye_c(sx), EYE_R))
    return fd


def teeth_field():
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009 + 0.003, -0.178, 1.551)), v3((0.008, 0.006, 0.006)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= the cap
CAP_O = v3((0.0, 0.026, 1.838))             # the band's foot, on the crown's axis (world)
CAP_R = euler(0.06, 0.0, 0.0)              # tipped a little forward
CAP_H = 0.18
CAP_R0 = (0.192, 0.214)                    # the crown's radii at the band (x, y) and at its flat top
CAP_R1 = (0.2, 0.226)
CAP_T = 0.009
BAND_H = 0.056
PEAK_A, PEAK_L, PEAK_TH, PEAK_SLOPE = 1.05, 0.09, 0.0055, -0.2


def cap_local(P):
    return ((P - CAP_O.astype(F)) @ CAP_R.astype(F)).astype(F)


def cap_world(q):
    return CAP_O + CAP_R @ v3(q)


def crown_sd(q):
    """Signed distance to the crown (cap-local): an oval widening a little to a flat top with a soft rounded edge."""
    z = q[:, 2]
    t = np.clip(z / F(CAP_H), 0, 1)
    rx = F(CAP_R0[0]) + F(CAP_R1[0] - CAP_R0[0]) * t
    ry = F(CAP_R0[1]) + F(CAP_R1[1] - CAP_R0[1]) * t
    e = (np.sqrt((q[:, 0] / rx) ** 2 + (q[:, 1] / ry) ** 2) - F(1.0)) * np.minimum(rx, ry)
    dz = np.maximum(z - F(CAP_H), F(-0.03) - z)
    rr = F(0.04)
    a = e + rr
    b = dz + rr
    return np.sqrt(np.maximum(a, 0) ** 2 + np.maximum(b, 0) ** 2) + np.minimum(np.maximum(a, b), 0) - rr


def _band_r(a):
    """The band's radius in the direction at angle a from the front (an ellipse)."""
    return 1.0 / np.sqrt((np.sin(a) / F(CAP_R0[0])) ** 2 + (np.cos(a) / F(CAP_R0[1])) ** 2)


def peak_sd(q):
    """The peak: a half-moon of stiff leather from the band's front edge, sloping down over his brows."""
    a = np.arctan2(q[:, 0], -q[:, 1])
    rho = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - (_band_r(a) - F(0.006))
    L = F(PEAK_L) * np.sqrt(np.clip(F(1) - (a / F(PEAK_A)) ** 2, 0, 1))
    c, s = F(math.cos(PEAK_SLOPE)), F(math.sin(PEAK_SLOPE))
    z = q[:, 2] - F(0.013)
    t = np.clip(rho * c + z * s, 0, L)
    dx, dz = rho - t * c, z - t * s
    d = np.sqrt(dx * dx + dz * dz) - F(PEAK_TH)
    return np.maximum(d, (np.abs(a) - F(PEAK_A)) * F(0.2))


def cap_field():
    """Navy wool (label 0): the crown (a felt shell on a stiff band) with a flat top; the band black (6), brass piping round
    the top's edge (5)."""
    fd = Field("Cap")
    cloth = lambda P: F(0.0008) * NOISE(P * F(45)) + F(0.0006) * NOISE(P * F(120))
    lo, hi = CAP_O - v3((0.4, 0.4, 0.15)), CAP_O + v3((0.4, 0.4, 0.4))
    fd.add(Func(lambda P: np.abs(crown_sd(cap_local(P)) + F(CAP_T / 2)) - F(CAP_T / 2), lo, hi, disp=cloth, disp_amp=0.001), 0.0)
    fd.inter(Func(lambda P: F(-0.002) - cap_local(P)[:, 2], lo, hi), 0.0)
    # a slight welt where the top meets the side
    def welt(P):
        q = cap_local(P)
        return np.maximum(np.abs(crown_sd(q) - F(0.001)) - F(0.0045), np.abs(q[:, 2] - F(CAP_H - 0.022)) - F(0.006))
    fd.add(Func(welt, lo, hi), 0.003, 5)
    fd.paint(Func(lambda P: cap_local(P)[:, 2] - F(BAND_H), lo, hi), 6)
    return fd


def peak_field():
    """Black glossy leather: the peak and the chin strap across the band's front."""
    fd = Field("Peak")
    lo, hi = CAP_O - v3((0.35, 0.4, 0.12)), CAP_O + v3((0.35, 0.1, 0.15))
    fd.add(Func(lambda P: peak_sd(cap_local(P)), lo, hi), 0.0)
    def strap(P):
        q = cap_local(P)
        a = np.arctan2(q[:, 0], -q[:, 1])
        sh = np.abs(crown_sd(q) - F(0.002)) - F(0.0025)
        return np.maximum(np.maximum(sh, np.abs(q[:, 2] - F(0.034)) - F(0.0085)), np.abs(a) - F(1.42))
    fd.add(Func(strap, lo, hi), 0.002)
    return fd


def cap_surface_point(a, z, out=0.0):
    """A point on the crown's outer surface (cap-local) at angle a from the front, height z; its outward normal."""
    q = np.array([[math.sin(a) * 0.3, -math.cos(a) * 0.3, z]], F)
    for _ in range(8):
        d = crown_sd(q)
        g = np.zeros_like(q)
        for k in range(2):
            e = np.zeros(3, F)
            e[k] = 0.001
            g[:, k] = (crown_sd(q + e) - crown_sd(q - e)) / F(0.002)
        g = g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), F(1e-9))
        q = q - g * d[:, None]
    n = norm(v3(g[0]))
    return v3(q[0]) + n * out, n


def badge_field():
    """Brass: the corps badge on the cap's front (a star of eight rays round a boss in a ring of beads) and the two
    small buttons holding the chin strap."""
    fd = Field("Badge")
    q, n = cap_surface_point(0.0, 0.098, 0.0)
    c = cap_world(q)
    nw = norm(CAP_R @ n)
    up = norm(CAP_R @ v3((0, 0, 1)) - nw * float((CAP_R @ v3((0, 0, 1))) @ nw))
    side = np.cross(nw, up)
    R = np.stack([side, up, nw], axis=1)
    fd.add(Ellipsoid(c + nw * 0.003, (0.026, 0.03, 0.006), R=R), 0.0)
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = side * math.cos(a) + up * math.sin(a)
        L = 0.038 if k % 2 == 0 else 0.03
        fd.add(RoundCone(c + nw * 0.004 + d * 0.01, c + nw * 0.003 + d * L, 0.007, 0.002), 0.003)
    fd.add(Torus(c + nw * 0.008, 0.015, 0.0028, R=R), 0.002)
    fd.add(Ellipsoid(c + nw * 0.009, (0.009, 0.011, 0.006), R=R), 0.003)
    for sa in (-1, 1):
        q2, n2 = cap_surface_point(sa * 1.42, 0.034, 0.004)
        fd.add(Sphere(cap_world(q2), 0.0085), 0.0)
    return fd


# ======================================================================================= hair, moustache
def hair_field():
    """Short brown hair under the cap: cropped close at the back and over the ears, neat sideburns down to his ear lobes."""
    fd = Field("Hair")
    hull = Field("HairHull")
    hull.add(Ellipsoid(HEAD_C, HEAD_RAD + v3((0.004, 0.006, 0.006))), 0.0)
    strands = lambda P: (F(0.0006) * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(0.03)) * F(140) + P[:, 2] * F(40))
                         + F(0.001) * NOISE(P * np.array([110, 110, 40], F)) + F(0.0008) * NOISE(P * F(30)))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        back = smoothstep(0.03, 0.1, y)
        burn = smoothstep(0.0, -0.03, y) * smoothstep(0.1, 0.13, ax)
        bottom = F(1.716) + F(1.588 - 1.716) * back + F(1.62 - 1.716) * burn
        bottom = bottom + F(0.006) * np.sin(x * F(60))
        front = np.where(ax > F(0.125), F(-0.075) - y, F(-0.02) - y)
        return np.maximum(bottom - z, front)
    fd.add(Inter(Shell(hull, 0.002, 0.011, pad=0.06, disp=strands, disp_amp=0.002),
                 Func(keep, HEAD_C - v3((0.4, 0.4, 0.5)), HEAD_C + 0.35), 0.003), 0.0)
    fd.inter(Func(_under_cap, CAP_O - 0.5, CAP_O + 0.5), 0.002)
    return fd


def beard_field():
    """A neat, trimmed moustache over his lip, its ends turned a little down past the corners of his mouth."""
    fd = Field("Beard")
    strands = lambda P: F(0.0018) * NOISE(P * np.array([90, 90, 25], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.004, -0.232, 1.588)), hp((sx * 0.03, -0.226, 1.58)), hp((sx * 0.052, -0.212, 1.568)),
               hp((sx * 0.066, -0.198, 1.552)), hp((sx * 0.07, -0.19, 1.538))]
        fd.add(Lock(pts, [hr(0.014), hr(0.017), hr(0.014), hr(0.009), hr(0.004)],
                    [hr(0.009), hr(0.01), hr(0.009), hr(0.007), hr(0.004)],
                    [norm(v3((sx * 0.25, -1, 0.15)))] * 5, k=hr(0.005), disp=strands, disp_amp=0.002), hr(0.006))
    return fd


# ======================================================================================= the tunic (navy wool)
TUNIC_OFF, TUNIC_T = 0.018, 0.012
TUNIC_FACE = TUNIC_OFF + TUNIC_T / 2 + 0.003
TUNIC_HEM = 0.71
WAIST_Z = 0.95                              # the belt's middle
SK_Z = (0.64, 0.74, 0.88, 0.99)
SK_RX = (0.284, 0.28, 0.266, 0.19)
SK_RY = (0.214, 0.212, 0.205, 0.158)


def skirt_sd(P):
    z = P[:, 2]
    rx = np.interp(z, SK_Z, SK_RX).astype(F)
    ry = np.interp(z, SK_Z, SK_RY).astype(F)
    e = (np.sqrt((P[:, 0] / rx) ** 2 + ((P[:, 1] - F(0.035)) / ry) ** 2) - F(1.0)) * np.minimum(rx, ry)
    return np.maximum(e, np.maximum(z - F(SK_Z[-1]), F(SK_Z[0]) - z))


_TB = []


def tunic_base():
    if _TB:
        return _TB[0]
    b = Field("TunicBase")
    for i, (p, k) in enumerate(torso_prims()):
        if i in (2, 3):
            continue
        b.add(p, k)
    b.add(Ellipsoid((0, -0.05, 1.3), (0.24, 0.15, 0.18)), 0.06)
    b.add(traps(), 0.06)
    b.add(Func(skirt_sd, (-0.4, -0.3, 0.55), (0.4, 0.36, 1.05)), 0.06)
    for side in ("R", "L"):
        el = J["elbow_" + side]
        b.add(deltoid(side), 0.055)
        for p, k in upper_arm_prims(side) + forearm_prims(side):
            b.add(p, k)
        b.add(Sphere(el + v3((0, 0.02, 0)), 0.052), 0.03)
    _TB.append(b)
    return b


def _neck_cut(P):
    """> 0 above the tunic's round neck (the stand collar rises from it); lifted clear of the shoulders."""
    rho = np.sqrt(P[:, 0] ** 2 + ((P[:, 1] - F(0.05)) * F(0.95)) ** 2)
    return P[:, 2] - (F(1.462) + F(0.4) * smoothstep(0.112, 0.14, rho))


def _wrist_cut(P, back=0.03):
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        along = (P - (wr - ax * back).astype(F)) @ ax.astype(F)
        on = (P[:, 0] * F(sx) > F(0.4)) & (_arm_seg_dist(P, side) < F(0.14))
        out = np.maximum(out, np.where(on, along, F(-1.0)))
    return out


def _hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.035)))
    return F(TUNIC_HEM) + F(0.008) * np.cos(a * 2) + F(0.004) * NOISE(P * F(8))


def _vent(P):
    z = P[:, 2]
    bw = F(0.003) + F(0.02) * smoothstep(0.86, 0.72, z)
    return np.where((P[:, 1] > F(0.08)) & (z < F(0.88)), bw - np.abs(P[:, 0]), F(-1.0))


def tunic_outer():
    b = tunic_base()
    return Func(lambda P: b.eval(P, margin=0.1) - F(TUNIC_OFF + TUNIC_T / 2), (-0.8, -0.6, 0.6), (0.8, 0.6, 1.65))


def collar_region(P, extra=0.0):
    """The stand collar's band round his neck (low in front, under his chin), open a finger's width at the front."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.03)) / F(0.12), 0, 1)
    top = F(1.522) - F(0.045) * front * np.exp(-(x / F(0.1)) ** 2) + F(extra)
    gap = np.where(y < F(0.0), F(0.006) - np.abs(x), F(-1.0))
    return np.maximum(np.maximum(z - top, F(1.43) - z), gap)


def coat_field():
    """The tunic: navy wool (label 0) with brass-coloured piping (5) on the collar's top edge, the front edge and the
    cuffs; a high stand collar; long sleeves ending in pointed cuffs; skirts to the hips with a vent behind; shoulder
    straps."""
    fd = Field("Coat")
    base = tunic_base()
    soft = lambda P: (F(0.0016) * NOISE(P * F(14)) + F(0.0008) * NOISE(P * F(45))
                      + F(0.002) * np.sin(np.arctan2(P[:, 0], -(P[:, 1] - F(0.035))) * F(9)) * smoothstep(0.86, 0.72, P[:, 2]))
    lo, hi = (-0.85, -0.6, 0.55), (0.85, 0.6, 1.65)
    def keep(P):
        k = np.maximum(np.maximum(_neck_cut(P), _hem(P) - P[:, 2]), _wrist_cut(P, 0.035))
        return np.maximum(k, _vent(P))
    fd.add(Inter(Shell(base, TUNIC_OFF, TUNIC_T, pad=0.12, disp=soft, disp_amp=0.004), Func(keep, lo, hi), 0.004), 0.0)
    # the stand collar
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    clo, chi = (-0.2, -0.2, 1.38), (0.2, 0.25, 1.6)
    fd.add(Inter(Shell(nk, 0.026, 0.012, pad=0.06), Func(collar_region, clo, chi), 0.003), 0.004)
    def piping(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        front = np.clip(-(y - F(0.03)) / F(0.12), 0, 1)
        top = F(1.522) - F(0.045) * front * np.exp(-(x / F(0.1)) ** 2)
        return np.maximum(F(-0.004) - (z - top), nk.eval(P, margin=0.06) - F(0.05))
    fd.paint(Func(piping, clo, chi), 5)
    # the seam down the front where it buttons (a groove in the wool's face), piped
    def seam(P):
        depth = F(TUNIC_OFF + TUNIC_T / 2 - 0.003) - base.eval(P, margin=0.06)
        return np.maximum(np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.002), P[:, 1] + F(0.05)),
                                     np.maximum(F(0.72) - P[:, 2], P[:, 2] - F(1.46))), depth)
    fd.sub(Func(seam, (-0.05, -0.4, 0.68), (0.05, 0.0, 1.5)), 0.0015)
    fd.paint(Func(lambda P: np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.007), P[:, 1] + F(0.05)),
                                       np.maximum(F(0.7) - P[:, 2], P[:, 2] - F(1.47))), (-0.05, -0.4, 0.66), (0.05, 0.0, 1.5)), 5)
    # pointed cuffs: a raised band at each sleeve's end, rising to a point on the outside of the forearm, piped
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        end = wr - ax * 0.035
        outv = norm(v3((sx, 0, 0)) - ax * float(v3((sx, 0, 0)) @ ax))
        def cuff_len(P, end=end, ax=ax, outv=outv):
            r = P - end.astype(F)
            along = -(r @ ax.astype(F))
            rad = r - np.outer(r @ ax.astype(F), ax).astype(F)
            rn = rad / np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), F(1e-6))
            point = np.clip(rn @ outv.astype(F), 0, 1) ** 3
            return along, F(0.05) + F(0.05) * point
        def cuff(P, side=side, cuff_len=cuff_len):
            along, L = cuff_len(P)
            return np.maximum(np.maximum(-along, along - L), _arm_seg_dist(P, side) - F(0.15))
        def cuff_pipe(P, side=side, cuff_len=cuff_len):
            along, L = cuff_len(P)
            return np.maximum(np.abs(along - L + F(0.004)) - F(0.0055), _arm_seg_dist(P, side) - F(0.15))
        c0 = end
        fd.add(Inter(Func(cuff, c0 - 0.2, c0 + 0.2), Shell(base, TUNIC_OFF + 0.007, TUNIC_T, pad=0.12), 0.002), 0.003)
        fd.paint(Func(cuff_pipe, c0 - 0.2, c0 + 0.2), 5)
    # shoulder straps
    outer = tunic_outer()
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        pts, ns = [], []
        for t in np.linspace(0.0, 1.0, 5):
            x = sx * (0.11 + 0.2 * t)
            h, ok = ray_hit(outer, [v3((x, 0.06, 1.75))], [v3((0, 0, -1))], tmax=0.6)
            if ok[0]:
                pts.append(h[0] + v3((0, 0, 0.003)))
                ns.append(_fgrad(outer.fn, h[0]))
        if len(pts) >= 3:
            fd.add(Lock(pts, [0.026] * len(pts), [0.006] * len(pts), ns, k=0.004), 0.004)
    return fd


def buttons_field():
    """Brass buttons: down the tunic's front, on the shoulder straps and on the cuffs' points."""
    fd = Field("Buttons")
    outer = tunic_outer()
    for k in range(6):
        z = 1.41 - k * 0.075
        if abs(z - WAIST_Z) < 0.045:
            continue
        h, ok = ray_hit(outer, [v3((0.0, -0.7, z))], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            n = _fgrad(outer.fn, h[0])
            fd.add(Ellipsoid(h[0] + n * 0.004, (0.012, 0.012, 0.008), R=rot_from_axes(z_axis=n)), 0.0)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        h, ok = ray_hit(outer, [v3((sx * 0.29, 0.06, 1.75))], [v3((0, 0, -1))], tmax=0.6)
        if ok[0]:
            fd.add(Ellipsoid(h[0] + v3((0, 0, 0.011)), (0.0095, 0.0095, 0.006)), 0.0)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        end = wr - ax * 0.035
        outv = norm(v3((sx, 0, 0)) - ax * float(v3((sx, 0, 0)) @ ax))
        p0 = end - ax * 0.07
        h, ok = ray_hit(outer, [p0 + outv * 0.3], [-outv], tmax=0.5)
        if ok[0]:
            fd.add(Ellipsoid(h[0] + outv * 0.012, (0.0085, 0.0085, 0.005), R=rot_from_axes(z_axis=outv)), 0.0)
    return fd


# ======================================================================================= trousers, puttees, boots
PUTTEE_TOP, PUTTEE_BOT = 0.43, 0.13


def trousers_field():
    """Navy trousers (darker than the tunic) from his waist into the puttees, full at the thigh."""
    fd = Field("Trousers")
    legs = Field("Legs")
    tp = torso_prims()
    legs.add(tp[4][0], 0.0)
    legs.add(tp[5][0], tp[5][1])
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            legs.add(p, k)
        sh = shin_prims(side)
        legs.add(sh[0][0], sh[0][1])
    folds = lambda P: F(0.004) * np.sin(np.arctan2(P[:, 1] - F(0.02), P[:, 0] - np.sign(P[:, 0]) * F(0.15)) * F(7)) * smoothstep(0.72, 0.5, P[:, 2]) \
        + F(0.0012) * NOISE(P * F(25))
    fd.add(Inter(Shell(legs, 0.014, 0.012, pad=0.1, disp=folds, disp_amp=0.005),
                 Func(lambda P: np.maximum(F(PUTTEE_TOP - 0.04) - P[:, 2], P[:, 2] - F(1.0)), (-0.5, -0.4, 0.3), (0.5, 0.4, 1.1)), 0.004), 0.0)
    return fd


def puttees_field():
    """Khaki wool puttees wound in a spiral from the boot to below the knee, a tape tied round the top."""
    fd = Field("Puttees")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        kn, an = J["knee_" + side], J["ankle_" + side]
        sb = Field("Shin" + side)
        for p, k in shin_prims(side):
            sb.add(p, k)
        sb.add(RoundCone(an + v3((0, 0.01, -0.02)), an + v3((0, 0.02, 0.12)), 0.058, 0.06), 0.03)
        ax = norm(kn - an)
        def spiral(P, an=an, ax=ax, sx=sx):
            r = P - an.astype(F)
            s = r @ ax.astype(F)
            a = np.arctan2(r[:, 1], r[:, 0] * F(sx))
            ph = s / F(0.042) + a / F(2 * math.pi) * F(-sx)
            fr = ph - np.floor(ph)
            return F(-0.0035) * smoothstep(0.0, 0.12, fr) * smoothstep(1.0, 0.85, fr) + F(0.001) * NOISE(P * F(40))
        lo, hi = an - v3((0.2, 0.2, 0.15)), kn + v3((0.2, 0.2, 0.1))
        fd.add(Inter(Shell(sb, 0.021, 0.012, pad=0.06, disp=spiral, disp_amp=0.004),
                     Func(lambda P: np.maximum(F(PUTTEE_BOT) - P[:, 2], P[:, 2] - F(PUTTEE_TOP)), lo, hi), 0.003), 0.0)
        c = an + ax * ((PUTTEE_TOP - 0.03 - an[2]) / ax[2])
        fd.add(Inter(Shell(sb, 0.029, 0.006, pad=0.06), Func(lambda P, c=c: np.abs(P[:, 2] - F(c[2])) - F(0.009), lo, hi), 0.002), 0.003, 5)
    return fd


def boot_base(side):
    b = Field("BootBase" + side)
    an = J["ankle_" + side]
    for p, k in shin_prims(side):
        b.add(p, k)
    b.add(RoundCone(an + v3((0, 0.01, -0.02)), an + v3((0, 0.02, 0.12)), 0.058, 0.06), 0.03)
    foot(b, side)
    return b


def boots_field():
    """Black leather ankle boots (label 0), laced over the instep, thick soles and heels (5)."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        bb = boot_base(side)
        crease = lambda P: F(0.0012) * NOISE(P * F(26)) + F(0.0015) * np.sin(P[:, 2] * F(90)) * smoothstep(0.12, 0.07, P[:, 2])
        lo, hi = an - v3((0.2, 0.35, 0.2)), an + v3((0.2, 0.25, 0.2))
        fd.add(Inter(Shell(bb, 0.016, 0.014, pad=0.06, disp=crease, disp_amp=0.003), Func(lambda P: P[:, 2] - F(PUTTEE_BOT + 0.035), lo, hi), 0.004), 0.0)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        rgt = Rz @ v3((1, 0, 0))
        fd.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.1)), (0.07, 0.158, 0.014), 0.01, R=Rz), 0.006, 5)
        fd.add(RoundBox(an - fwd * 0.028 + v3((0, 0, -0.09)), (0.055, 0.05, 0.026), 0.01, R=Rz), 0.006, 5)      # the heel
        # the laces' ridge over the instep
        for k in range(4):
            c = an + fwd * (0.045 + 0.022 * k) + v3((0, 0, 0.0 - 0.018 * k))
            fd.add(RoundCone(c - rgt * 0.022, c + rgt * 0.022, 0.0045, 0.0045), 0.003)
    return fd


# ======================================================================================= webbing: belt, pouches, bandolier
BANDOLIER = _strap_plane(v3((0.17, 0.06, 1.5)), v3((-0.25, -0.12, 0.9)), v3((-0.25, 0.2, 0.9)))
BANDOLIER_W = 0.03
BELT_W = 0.028


def _over_belt(P):
    return smoothstep(0.03, 0.01, np.abs(P[:, 2] - F(WAIST_Z)) - F(BELT_W))


def _over_collar(P):
    return smoothstep(0.03, 0.006, collar_region(P, 0.01))


def bandolier_off(P):
    return F(TUNIC_FACE + 0.006) + np.maximum(F(0.017) * _over_belt(P), F(0.012) * _over_collar(P))


def strap_line(zs, front=True, extra=0.0):
    """Points along the bandolier's middle on the tunic's front (or back) at heights zs, with the outward normals."""
    p0, n = BANDOLIER
    base = tunic_base()
    d = norm(np.cross(n, v3((0, 0, 1))))
    if (d[1] < 0) == front:
        d = -d
    f = Func(lambda P: base.eval(P, margin=0.12) - F(TUNIC_FACE + 0.012 + extra), (-0.8, -0.8, 0.5), (0.8, 0.8, 1.7))
    out = []
    for z in zs:
        y0 = -0.8 if front else 0.8
        x = p0[0] - (n[1] * (y0 - p0[1]) + n[2] * (z - p0[2])) / n[0]
        o = v3((x, y0, z))
        h, ok = ray_hit(f, [o], [d], tmax=1.2, step=0.002)
        out.append((h[0], _fgrad(f, h[0])) if ok[0] else None)
    return out


CART_Z = tuple(1.33 - 0.034 * i for i in range(10))      # the cartridges down the bandolier's front


def cartridge_spots():
    """[(centre, along the cartridge (bullet end), the strap's outward normal)] down the bandolier's front."""
    p0, n = BANDOLIER
    sdir = norm(np.cross(n, v3((0, 0, 1))))                 # (horizontal, in the strap's plane)
    out = []
    for hit in strap_line(CART_Z, front=True, extra=-0.004):
        if hit is None:
            continue
        p, nrm = hit
        along = norm(np.cross(nrm, n))                       # across the strap, in its face
        if along[2] < 0:
            along = -along
        out.append((p, along, nrm))
    return out


def pouch_spots():
    outer = tunic_outer()
    out = []
    for sx in (-1, 1):
        h, ok = ray_hit(outer, [v3((sx * 0.115, -0.7, WAIST_Z + 0.005))], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            n = _fgrad(outer.fn, h[0])
            n = norm(v3((n[0], n[1], 0.0)))
            out.append((h[0], n))
    return out


def webbing_field():
    """Buff webbing (label 0): the belt and two ammunition pouches on its front, their flaps fastened with brass studs;
    the brass buckle plate (6); the bandolier of brown leather (5) over his left shoulder to his right hip, a row of brass
    cartridges (6) in its loops."""
    fd = Field("Webbing")
    base = tunic_base()
    weave = lambda P: F(0.0007) * np.abs(np.sin(P[:, 2] * F(500))) + F(0.0006) * NOISE(P * F(60))
    blo, bhi = (-0.4, -0.35, WAIST_Z - 0.08), (0.4, 0.38, WAIST_Z + 0.08)
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(WAIST_Z)) - F(BELT_W), blo, bhi),
                 Shell(base, TUNIC_FACE + 0.006, 0.012, pad=0.12, disp=weave, disp_amp=0.001), 0.003), 0.0)
    outer = tunic_outer()
    h, ok = ray_hit(outer, [v3((0.0, -0.7, WAIST_Z))], [v3((0, 1, 0))], tmax=0.8)
    if ok[0]:
        n = norm(_fgrad(outer.fn, h[0]) * v3((1, 1, 0)))
        R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
        c = h[0] + n * 0.016
        fd.add(RoundBox(c, (0.042, 0.034, 0.006), 0.004, R=R), 0.002, 6)
        fd.sub(RoundBox(c + n * 0.006, (0.03, 0.022, 0.004), 0.003, R=R), 0.002)
        fd.add(RoundBox(c + n * 0.004, (0.012, 0.012, 0.004), 0.003, R=R), 0.002, 6)
    for p, n in pouch_spots():
        side = norm(np.cross(v3((0, 0, 1)), n))
        R = np.stack([side, v3((0, 0, 1)), n], axis=1)
        c = p + n * 0.04 + v3((0, 0, -0.008))
        fd.add(RoundBox(c, (0.052, 0.05, 0.028), 0.012, R=R, disp=lambda P: F(0.0012) * NOISE(P * F(30)), disp_amp=0.0015), 0.004)
        # the flap: over its top, down its front
        fd.add(RoundBox(c + n * 0.006 + v3((0, 0, 0.022)), (0.056, 0.032, 0.026), 0.01, R=R), 0.003)
        fd.add(Ellipsoid(c + n * 0.034 + v3((0, 0, 0.0)), (0.008, 0.008, 0.005), R=R), 0.002, 6)
    # the bandolier
    def strap(P):
        return np.maximum(strap_d(P, BANDOLIER) - F(BANDOLIER_W), np.maximum(np.abs(P[:, 0]) - F(0.34), F(0.86) - P[:, 2]))
    lo, hi = (-0.38, -0.34, 0.82), (0.38, 0.36, 1.6)
    fd.add(Inter(layer(base, bandolier_off, 0.01, lo, hi), Func(strap, lo, hi), 0.003), 0.0, 5)
    for c, along, nrm in cartridge_spots():
        a0 = c + nrm * 0.004 - along * 0.022
        a1 = a0 + along * 0.034
        fd.add(RoundCone(a0, a1, 0.0075, 0.0075), 0.0, 6)
        fd.add(RoundCone(a1, a1 + along * 0.014, 0.0068, 0.0028), 0.002, 6)
        lp = c + nrm * 0.004 - along * 0.006
        fd.add(Inter(Shell(Sphere(lp, 0.0085), 0.0, 0.003), Func(lambda P, lp=lp, along=along: np.abs((P - lp.astype(F)) @ along.astype(F)) - F(0.006), lp - 0.02, lp + 0.02), 0.001), 0.002, 5)
    return fd


# ======================================================================================= the rifle
# Rifle coordinates: u along the barrel (from the grip, forward), v to the gun's right (the bolt side), h up; the grip
# (u = 0) is where his right fist holds the wrist of the stock, behind the receiver.
BUTT_U = -0.36
STOCK_END = 0.74
MUZZLE_U = 0.94                            # (1.3 m from butt to muzzle)
BAR_H = 0.045                              # the bore's axis above the grip
RECV_U = (0.065, 0.2)                      # the receiver
RECV_R = 0.0195
BOLT_U = (0.03, 0.19)                      # the bolt body (rear: the cocking piece behind the receiver)
BOLT_R = 0.0105
HANDLE_U = 0.054                           # where the handle leaves the bolt
KNOB = (0.044, 0.05, BAR_H - 0.036)        # the handle's knob (u, v, h), bolt closed (turned down)
MAG_U = (0.105, 0.175)
FORE_GRIP_U = 0.4                          # his left hand on the fore-stock
BANDS_U = (0.5, 0.715)
SWIVEL_U = (0.5, -0.22)
RIFLE_FRAME = mk.musket_frame


def mpt(u, v=0.0, h=0.0):
    G, A, U, S = RIFLE_FRAME()
    return G + A * u + S * v + U * h


def m_local(P):
    G, A, U, S = RIFLE_FRAME()
    q = P - G.astype(F)
    return q @ A.astype(F), q @ S.astype(F), q @ U.astype(F)


def m_bounds(u0, u1, r=0.15):
    pts = [mpt(u, v, h) for u in (u0, u1) for v in (-r, r) for h in (-r, r)]
    return np.min(pts, 0), np.max(pts, 0)


def stock_profile(u):
    """(h_bot, h_top, half width) of the stock's cross-section at u (arrays)."""
    u = np.asarray(u, F)
    k = np.clip((F(-0.06) - u) / F(-0.06 - BUTT_U), 0, 1)                 # 0 at the wrist .. 1 at the butt's end
    fore = smoothstep(0.2, 0.3, u)
    taper = np.clip((u - F(0.3)) / F(STOCK_END - 0.3), 0, 1)
    grip = np.exp(-((u - F(-0.01)) / F(0.04)) ** 2)                          # the semi-pistol grip's swell below
    hb_rear = F(-0.038) - F(0.078) * k ** F(1.2) - F(0.012) * grip
    hb_front = F(-0.017) + F(0.009) * taper
    hb = hb_rear * (F(1) - fore) + hb_front * fore
    ht_rear = F(0.022) + F(0.008) * k + F(0.006) * smoothstep(0.03, 0.08, u)
    ht = ht_rear * (F(1) - fore) + F(BAR_H + 0.002) * fore
    w = (F(0.0165) + F(0.006) * k) * (F(1) - fore) + (F(0.0155) - F(0.003) * taper) * fore
    return hb, ht, w


def _stock_sd(P):
    u, v, h = m_local(P)
    hb, ht, w = stock_profile(u)
    hc, hh = (ht + hb) / F(2), (ht - hb) / F(2)
    rr = F(0.008)
    qx = np.abs(v) - w + rr
    qy = np.abs(h - hc) - hh + rr
    qz = np.maximum(F(BUTT_U) - u, u - F(STOCK_END)) + rr
    q = np.stack([qx, qy, qz], 1)
    d = np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - rr
    # the barrel's channel and the receiver's bed (the metal lies in the wood)
    ch = np.maximum(np.sqrt(v * v + (h - F(BAR_H)) ** 2) - F(0.0135), F(RECV_U[0] - 0.005) - u)
    return np.maximum(d, -ch)


def barrel_r(u):
    return F(0.0128) - F(0.0024) * np.clip((u - F(0.2)) / F(MUZZLE_U - 0.2), 0, 1) + F(0.0012) * smoothstep(MUZZLE_U - 0.03, MUZZLE_U - 0.01, u)


def _barrel_sd(P):
    u, v, h = m_local(P)
    rad = np.sqrt(v * v + (h - F(BAR_H)) ** 2) - barrel_r(u)
    ax = np.maximum(F(RECV_U[1] - 0.01) - u, u - F(MUZZLE_U))
    q0, q1 = np.maximum(rad, 0), np.maximum(ax, 0)
    d = np.sqrt(q0 * q0 + q1 * q1) + np.minimum(np.maximum(rad, ax), 0)
    bore = np.maximum(np.sqrt(v * v + (h - F(BAR_H)) ** 2) - F(0.0045), F(MUZZLE_U - 0.05) - u)
    return np.maximum(d, -bore)


def _receiver_sd(P):
    """The receiver round the bolt: a cylinder, flattened on its sides, a bridge at its front; open behind for the bolt."""
    u, v, h = m_local(P)
    r = np.sqrt((v / F(0.92)) ** 2 + (h - F(BAR_H)) ** 2) - F(RECV_R)
    ax = np.abs(u - F((RECV_U[0] + RECV_U[1]) / 2)) - F((RECV_U[1] - RECV_U[0]) / 2)
    rr = F(0.004)
    a, b = r + rr, ax + rr
    d = np.sqrt(np.maximum(a, 0) ** 2 + np.maximum(b, 0) ** 2) + np.minimum(np.maximum(a, b), 0) - rr
    # the bolt's way through it
    way = np.maximum(np.sqrt(v * v + (h - F(BAR_H)) ** 2) - F(BOLT_R + 0.0012), u - F(RECV_U[1] - 0.02))
    return np.maximum(d, -way)


def _band_sd(u0, half):
    def fn(P):
        u, v, h = m_local(P)
        hb, ht, w = stock_profile(np.full(len(u), F(u0)))
        top = F(BAR_H) + barrel_r(np.full(len(u), F(u0)))
        wv = np.maximum(w, barrel_r(np.full(len(u), F(u0)))) + F(0.0025)
        hc, hh = (top + hb) / F(2), (top - hb) / F(2) + F(0.0025)
        rr = F(0.006)
        q = np.stack([np.abs(v) - wv + rr, np.abs(h - hc) - hh + rr, np.abs(u - F(u0)) - F(half) + rr], 1)
        return np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - rr
    return fn


def rifle_field():
    """Walnut (label 0) stock; blued steel (6): barrel, receiver, magazine, bands, sights, trigger guard and trigger,
    swivels; brass (5) butt plate."""
    fd = Field("Rifle")
    G, A, U, S = RIFLE_FRAME()
    Rm = np.stack([A, S, U], axis=1)
    lo, hi = m_bounds(BUTT_U - 0.02, MUZZLE_U + 0.02, 0.13)
    grain = lambda P: F(0.0005) * NOISE(P * F(90))
    fd.add(Func(_stock_sd, lo, hi, disp=grain, disp_amp=0.001), 0.0)
    fd.add(Func(_barrel_sd, lo, hi), 0.002, 6)
    fd.add(Func(_receiver_sd, *m_bounds(RECV_U[0] - 0.02, RECV_U[1] + 0.02, 0.05)), 0.002, 6)
    for u0 in BANDS_U:
        fd.add(Func(_band_sd(u0, 0.008), *m_bounds(u0 - 0.03, u0 + 0.03)), 0.002, 6)
    # the butt plate
    fd.paint(Func(lambda P: m_local(P)[0] - F(BUTT_U + 0.01), *m_bounds(BUTT_U - 0.02, BUTT_U + 0.05)), 5)
    mp = lambda u, h, v=0.0: mpt(u, v, h)
    # the box magazine under the receiver, standing out of the stock
    mc = mp((MAG_U[0] + MAG_U[1]) / 2, -0.048)
    fd.add(RoundBox(mc, ((MAG_U[1] - MAG_U[0]) / 2, 0.0135, 0.034), 0.005, R=Rm @ euler(0, 0.12, 0)), 0.003, 6)
    # the trigger guard and the trigger
    guard = [mp(0.03, -0.034), mp(0.032, -0.06), mp(0.062, -0.072), mp(0.094, -0.06), mp(0.1, -0.036)]
    fd.add(Chain(guard, [0.0042] * 5, k=0.003), 0.003, 6)
    fd.add(Chain([mp(0.07, -0.034), mp(0.064, -0.05), mp(0.056, -0.058)], [0.0038, 0.0034, 0.003], k=0.002), 0.002, 6)
    # sights: a ladder sight's block before the receiver, the foresight on a ramp at the muzzle
    fd.add(RoundBox(mp(0.26, BAR_H + 0.012), (0.026, 0.011, 0.006), 0.003, R=Rm), 0.003, 6)
    for sv in (-1, 1):
        fd.add(RoundBox(mp(0.27, BAR_H + 0.02, sv * 0.008), (0.012, 0.0022, 0.008), 0.0015, R=Rm), 0.002, 6)
    fd.add(RoundBox(mp(MUZZLE_U - 0.03, BAR_H + 0.013), (0.016, 0.006, 0.006), 0.003, R=Rm), 0.003, 6)
    fd.add(RoundBox(mp(MUZZLE_U - 0.028, BAR_H + 0.022), (0.005, 0.0016, 0.007), 0.0012, R=Rm), 0.002, 6)
    # the sling's swivels
    for u0 in SWIVEL_U:
        hb = float(stock_profile(np.array([u0], F))[0][0])
        fd.add(Torus(mp(u0, hb - 0.012), 0.011, 0.0028, R=rot_from_axes(z_axis=S, y_axis=A)), 0.002, 6)
        fd.add(RoundCone(mp(u0, hb + 0.004), mp(u0, hb - 0.002), 0.005, 0.004), 0.002, 6)
    return fd


def sling_pts():
    """The sling's middle line from the front swivel to the butt's, hanging in a shallow curve below the stock."""
    out = []
    u0, u1 = SWIVEL_U
    h0 = float(stock_profile(np.array([u0], F))[0][0]) - 0.022
    h1 = float(stock_profile(np.array([u1], F))[0][0]) - 0.022
    for i in range(9):
        t = i / 8
        u = u0 + (u1 - u0) * t
        h = h0 + (h1 - h0) * t - 0.05 * (1 - (2 * t - 1) ** 2)
        out.append(mpt(u, 0.0, h))
    return out


def sling_field():
    """The sling: a strap of brown leather (label 9) between the swivels, brass (5) keepers."""
    fd = Field("Sling")
    G, A, U, S = RIFLE_FRAME()
    pts = sling_pts()
    fd.add(Lock(pts, [0.012] * len(pts), [0.0026] * len(pts), [S] * len(pts), k=0.003,
                disp=lambda P: F(0.0006) * NOISE(P * F(60)), disp_amp=0.0008), 0.0, 9)
    for i in (2, 6):
        d = norm(pts[i + 1] - pts[i - 1])
        fd.add(RoundBox(pts[i], (0.0045, 0.0145, 0.006), 0.002, R=rot_from_axes(z_axis=d, x_axis=S)), 0.002, 5)
    return fd


def bolt_field():
    """The bolt (bright steel, label 7): its body in the receiver, the cocking piece behind (blued, 6) and the handle,
    turned down, with its round knob."""
    fd = Field("Bolt")
    G, A, U, S = RIFLE_FRAME()
    fd.add(RoundCone(mpt(BOLT_U[0] + 0.012, 0.0, BAR_H), mpt(BOLT_U[1], 0.0, BAR_H), BOLT_R, BOLT_R), 0.0, 7)
    fd.add(Cylinder(mpt(BOLT_U[0] + 0.006, 0.0, BAR_H), 0.0125, 0.02, rr=0.004, R=rot_from_axes(z_axis=A)), 0.003, 6)
    fd.add(Sphere(mpt(BOLT_U[0] - 0.004, 0.0, BAR_H + 0.002), 0.008), 0.004, 6)
    root = mpt(HANDLE_U, 0.006, BAR_H)
    knob = mpt(*KNOB)
    mid = mpt((HANDLE_U + KNOB[0]) / 2, 0.034, BAR_H - 0.01)
    fd.add(Chain([root, mid, knob], [0.0058, 0.005, 0.0048], k=0.003), 0.003, 7)
    fd.add(Sphere(knob + (knob - mid) * 0.15, 0.0115), 0.003, 7)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.248, 1.612)), 0.045, 0.5)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.105, -0.14, 1.63)), 0.05, 0.4), (hp((sx * 0.162, 0.035, 1.66)), 0.04, 0.55)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.042, 0.014, -0.014, -0.042):
            pts.append((wr + f * 0.138 + t * o - n * 0.012, 0.03, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "rifleman"
ROOT_NAME = "RiflemanHQ"
TEX_PREFIX = "rifle"
MAT_NAME = "RiflemanMat"
MESH_NAME = "Rifleman"
BASE_MODULE = "rifleman_base"
ANIM_MODULE = "anim_rifleman"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Beard", "Cap", "Peak", "Badge", "Coat", "Buttons", "Trousers", "Puttees", "Boots",
         "Webbing", "Rifle", "Bolt", "Sling"]
REGION_PARTS = ("Skin", "Cap", "Coat", "Puttees", "Boots", "Webbing", "Rifle", "Bolt", "Sling")
NAVY = (0.18, 0.22, 0.42)                   # the corps' navy (the lead's ruling for every Industrial unit)
NAVY_DARK = (0.14, 0.17, 0.33)              # (his trousers: a shade darker)
BRASS = (0.8, 0.55, 0.22)
BLACK = (0.07, 0.065, 0.07)
KHAKI = (0.62, 0.53, 0.35)                  # buff webbing and khaki puttees
BUFF = (0.7, 0.58, 0.38)
BROWN = (0.36, 0.21, 0.11)
HAIR = {"name": "HQ_RifleHair", "base": (0.2, 0.125, 0.07), "hi": (0.42, 0.28, 0.16), "low": (0.08, 0.05, 0.03),
        "streak": (0.12, 0.075, 0.045), "tint": (0.3, 0.18, 0.1)}
ARMS = {"name": "HQ_ServiceRifle", "wood": (0.44, 0.23, 0.11), "wood2": (0.28, 0.13, 0.06)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_RifleSkin", "base": (0.8, 0.56, 0.42), "ruddy": (0.82, 0.47, 0.37), "lips": (0.66, 0.38, 0.33),
                      "brow": ((0.1, 0.065, 0.04), (0.22, 0.14, 0.08)),
                      "extra": ((LASH, (0.08, 0.05, 0.035), 0.5), (STUBBLE, (0.46, 0.34, 0.28), 0.55, 0.22))}),
    "Hair": ("hair", HAIR),
    "Beard": ("hair", HAIR),
    "Cap": ("wool", {"name": "HQ_RifleCap", "base": NAVY, "border": BRASS, "stripe": BLACK}),
    "Peak": ("leather_dyed", {"name": "HQ_RiflePeak", "base": (0.06, 0.055, 0.055), "dyed": (0.06, 0.055, 0.055), "worn_c": (0.36, 0.35, 0.36)}),
    "Badge": ("gold", {"name": "HQ_RifleBrass"}),
    "Coat": ("wool", {"name": "HQ_RifleTunic", "base": NAVY, "border": BRASS, "stripe": BLACK}),
    "Buttons": ("gold", {"name": "HQ_RifleBrass"}),
    "Trousers": ("wool", {"name": "HQ_RifleTrousers", "base": NAVY_DARK, "border": BRASS, "stripe": BLACK}),
    "Puttees": ("wool", {"name": "HQ_Puttees", "base": KHAKI, "border": (0.48, 0.4, 0.26), "stripe": BLACK}),
    "Boots": ("leather_dyed", {"name": "HQ_RifleBoots", "base": (0.08, 0.07, 0.065), "dyed": (0.05, 0.045, 0.04), "worn_c": (0.32, 0.3, 0.29)}),
    "Webbing": ("leather_dyed", {"name": "HQ_Webbing", "base": BUFF, "dyed": BROWN, "worn_c": (0.84, 0.74, 0.54)}),
    "Rifle": ("matchlock", ARMS),
    "Bolt": ("matchlock", ARMS),
    "Sling": ("matchlock", ARMS),
}
LOW_TARGETS = {"Skin": 5200, "Teeth": 60, "Hair": 900, "Beard": 240, "Cap": 1300, "Peak": 480, "Badge": 260, "Coat": 3700,
               "Buttons": 420, "Trousers": 1300, "Puttees": 1300, "Boots": 1100, "Webbing": 2500, "Rifle": 1800, "Bolt": 260,
               "Sling": 220}
AO_EXCLUDE = ["Rifle", "Bolt", "Sling", "Badge"]


def prop_bones():
    """The rifle and its bolt have no parent (posed in the world, "world" aims)."""
    return [("rifle", mpt(0.0), mpt(MUZZLE_U, 0.0, BAR_H), None),
            ("bolt", mpt(HANDLE_U, 0.0, BAR_H), mpt(HANDLE_U + 0.1, 0.0, BAR_H), None)]


def weight_rules():
    body = TORSO | {"clavicle.R", "clavicle.L"}
    arms = {"upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Beard": ("rigid", "head"), "Hair": ("rigid", "head"),
        "Cap": ("rigid", "head"), "Peak": ("rigid", "head"), "Badge": ("rigid", "head"),
        "Coat": ("transfer", body | arms | {"thigh.R", "thigh.L"}, {"thigh.R": 0.4, "thigh.L": 0.4}),
        "Buttons": ("transfer", body | arms, None),
        "Trousers": ("transfer", body | {"thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Puttees": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Webbing": ("transfer", body, None),
        "Rifle": ("rigid", "rifle"), "Sling": ("rigid", "rifle"), "Bolt": ("rigid", "bolt"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Rifle", "Sling"):
        return 0.8
    if part in ("Cap", "Badge", "Bolt"):
        return 1.2
    if part == "Skin" and abs(c.x) > 0.6 and c.z < 1.0:
        return 1.3
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Beard", beard_field(), 0.0016 if fine else 0.0022),
        ("Cap", cap_field(), 0.0022 if fine else 0.0032),
        ("Peak", peak_field(), 0.0016 if fine else 0.0022),
        ("Badge", badge_field(), 0.001 if fine else 0.0014),
        ("Coat", coat_field(), 0.0026 if fine else 0.0036),
        ("Buttons", buttons_field(), 0.0012 if fine else 0.0016),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Puttees", puttees_field(), 0.0022 if fine else 0.003),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Webbing", webbing_field(), 0.0016 if fine else 0.0022),
        ("Rifle", rifle_field(), 0.0016 if fine else 0.0022),
        ("Bolt", bolt_field(), 0.001 if fine else 0.0013),
        ("Sling", sling_field(), 0.0012 if fine else 0.0016),
    ]
