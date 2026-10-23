"""The EMP Tower (HQ tower, Modern Age, Control lineage): a field EMP emitter and the electronic-warfare specialist of
the task force who fires it. Rest pose: he stands in an A-pose facing -Y (the robots), feet at z = 0, the emitter behind
him on his left (+X, +Y), its rugged control case on a tripod before him on his right (-X, -Y); the case's safety guard
is closed over the trigger.

Him: the Spear Guard's young, athletic body (spear.py) with his own face: young and focused, a smooth oval face with a
firm jaw, level dark brows drawn a little together over steady brown eyes, a straight nose, a closed, set mouth. Short
dark-brown hair cropped close under an olive patrol cap (a flat-topped crown, a short curved bill); a black tactical
headset over the cap (a padded band over the crown, big ear cups, a boom mic before his mouth). Olive combat shirt with
its sleeves rolled above the elbows, a small red-and-white unit patch on his left sleeve; olive trousers with cargo
pockets; black combat boots; black gloves with hard knuckles. A coyote plate carrier (front and back plates, a
cummerbund, shoulder straps, webbing bands) with three pouches across its front, a radio pouch on his left side and a
radio on his back whose whip antenna rises over his head; a coyote rigger's belt. On his left forearm a rugged control
pad (a black housing, a pale green screen).

The emitter (taller than him; bones `machine`, `mast`, `emitter`, `charge`): an octagonal steel skid; a finned housing
on it; three capacitor canisters round it (gunmetal, ribbed caps, copper terminals, black cables to the housing), each
with a charge window (`Charge`, shipped glowing cyan, rides the `charge` bone: scaled up its length as the bank charges);
the mast from the housing (olive, telescoped, collars), a heat sink of fins, a stack of three copper ring coils in olive
clamps, a gunmetal cup and a cage of four prongs round the emitter head (`Emitter`, shipped glowing blue-white, rides
the `emitter` bone: the game's EMP rings leave its centre). Hazard stripes round the housing, a warning plate on it.

The control case (on `machine`): an olive tripod, an open rugged case (olive polymer, black handles), its lid up with
the screen (`Screen`, shipped glowing pale green), on its panel a key switch, a row of toggles, lamps, and the big red
trigger in a yellow collar under a hinged yellow-and-black safety guard (`guard`, hinged at its far edge; open in the
fight); the trigger's cap rides `button` (squashed when he slams it).

Painted labels: uniform (fatigues, cap): 0 olive, 5 red, 6 white, 7 coyote, 8 black; uniform (kit: vest, headset, pad,
gloves): 0 coyote, 5 olive, 7 dark webbing, 8 black; fieldgun (the machine): 0 olive drab, 5 gunmetal, 6 copper (its
`brass`), 7 bright steel, 8 black, 12 red, 13 hazard yellow (its `white`)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
import spear as sp
from spear import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R,
                   eye_c, smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, torso_prims, traps, neck_prim,
                   deltoid, eyes_field, TORSO, TORSO_Z, torso_bones)

IRIS = ((0.2, 0.12, 0.06), (0.42, 0.27, 0.13))          # steady brown eyes (prep.paint_eyes: outer ring, inner ring)
Z = v3((0.0, 0.0, 1.0))
# labels: fatigues / kit (mats.uniform), machine (mats.fieldgun)
OLIVE, RED, WHITE, COYOTE, BLACK = 0, 5, 6, 7, 8
K_COY, K_OLIVE, K_WEB, K_BLACK = 0, 5, 7, 8
M_OLIVE, M_GUN, M_COPPER, M_STEEL, M_BLACK, M_RED, M_YELLOW = 0, 5, 6, 7, 8, 12, 13


# ======================================================================================= head
def face_mask(P):
    """His jaw and chin (design coordinates): the faintest shadow of a morning's shave."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.575) + F(0.025) * smoothstep(0.06, 0.15, ax)
    return np.maximum(np.maximum(z - top, F(1.45) - z), y - F(0.02))


def mouth_slot():
    return [hp((-0.05, -0.172, 1.553)), hp((-0.026, -0.193, 1.549)), hp((0.0, -0.199, 1.548)), hp((0.026, -0.193, 1.549)),
            hp((0.05, -0.172, 1.553))]


def head(fd):
    """Young and focused: a smooth oval face, a firm jaw and a rounded chin, full young cheeks, level brows drawn a little
    together and down at their inner ends (concentration), steady open eyes, a straight nose, a closed, set mouth."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.055, 1.59), (0.13, 0.128, 0.122)), 0.07, SKIN)                            # a firm jaw
    fd.add(E((0, -0.134, 1.502), (0.078, 0.066, 0.064)), 0.05, SKIN)                           # a rounded chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.106, -0.12, 1.632), 0.046), 0.05, SKIN)                                # cheekbones
        fd.add(S((sx * 0.094, -0.142, 1.594), 0.036), 0.04, SKIN)                               # full young cheeks
        fd.add(S((sx * 0.118, -0.05, 1.562), 0.046), 0.05, SKIN)                                # jaw corners
        pts = [hp((sx * 0.15, -0.055, 1.742)), hp((sx * 0.114, -0.13, 1.75)), hp((sx * 0.06, -0.172, 1.748)), hp((0.0, -0.182, 1.746))]
        fd.add(Chain(pts, [hr(0.012), hr(0.02), hr(0.024), hr(0.024)], k=hr(0.022)), hr(0.034), SKIN)     # brow ridge
    fd.paint(Func(face_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # level brows, their inner ends drawn down and together: concentration
    for sx in (-1, 1):
        pts = [hp((sx * 0.02, -0.213, 1.744)), hp((sx * 0.062, -0.207, 1.761)), hp((sx * 0.106, -0.188, 1.768)), hp((sx * 0.15, -0.146, 1.762))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.011), hr(0.013), hr(0.011), hr(0.005)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.018), hr(0.02), hr(0.018), hr(0.01)], k=hr(0.01)), BROW)
        fd.sub(RoundCone(hp((sx * 0.012, -0.206, 1.75)), hp((sx * 0.015, -0.203, 1.772)), hr(0.0016), hr(0.0013)), hr(0.003))  # a frown line
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0066)), Plane(ec + v3((0, 0, hr(0.024))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0052)), Plane(ec + v3((0, 0, -hr(0.026))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0225))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
    # a straight nose
    fd.add(RoundCone(hp((0, -0.186, 1.726)), hp((0, -0.24, 1.632)), hr(0.015), hr(0.021)), hr(0.016), SKIN)
    fd.add(S((0, -0.242, 1.614), 0.025), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.028, -0.216, 1.603), 0.019), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.015, -0.232, 1.592)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a closed, set mouth: a straight line, a full lower lip
    slot = mouth_slot()
    fd.sub(Chain(slot, [hr(0.0024), hr(0.003), hr(0.0033), hr(0.003), hr(0.0024)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.048, -0.17, 1.556), (-0.026, -0.187, 1.556), (0.0, -0.191, 1.558), (0.026, -0.187, 1.556), (0.048, -0.17, 1.556)]
    lo_lip = [(-0.038, -0.172, 1.543), (-0.02, -0.186, 1.536), (0, -0.19, 1.534), (0.02, -0.186, 1.536), (0.038, -0.172, 1.543)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0045), hr(0.005), hr(0.0045), hr(0.003)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.006), hr(0.0065), hr(0.006), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    # ears (under the headset's cups)
    for sx in (-1, 1):
        R = euler(0, sx * 0.25, sx * -0.35)
        c = hp((sx * 0.162, 0.035, 1.66))
        fd.add(Ellipsoid(c, v3((0.02, 0.04, 0.052)) * HS, R=R), hr(0.02), SKIN)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        for p, k in arm_prims(side):
            fd.add(p, k, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def arm_prims(side):
    sx = -1 if side == "R" else 1
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    return [(deltoid(side), 0.055),
            (RoundCone(sh, el, 0.095, 0.072), 0.05),
            (Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.025, 0)), (0.085, 0.088, 0.125), R=rot_from_axes(z_axis=el - sh)), 0.04),
            (RoundCone(el, wr, 0.07, 0.054), 0.035),
            (Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.09, 0.08, 0.13), R=rot_from_axes(z_axis=wr - el)), 0.04),
            (Sphere(el + v3((0, 0.025, 0)), 0.055), 0.028)]


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
    fd.inter(Func(_under_cap, CAP_O - 0.5, CAP_O + 0.5), 0.003)
    return fd


def teeth_field():
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009 + 0.003, -0.178, 1.551)), v3((0.008, 0.006, 0.006)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= the patrol cap (olive)
CAP_O = v3((0.0, 0.03, 1.806))             # the band's foot, on the crown's axis (world)
CAP_R = euler(0.08, 0.0, 0.0)              # tipped a little forward
CAP_H = 0.128
CAP_R0 = (0.2, 0.216)                      # the crown's radii at the band (x, y) and at its flat top
CAP_R1 = (0.198, 0.218)
CAP_T = 0.009
PEAK_A, PEAK_L, PEAK_TH, PEAK_SLOPE = 1.0, 0.085, 0.0065, -0.32


def cap_local(P):
    return ((P - CAP_O.astype(F)) @ CAP_R.astype(F)).astype(F)


def cap_world(q):
    return CAP_O + CAP_R @ v3(q)


def crown_sd(q):
    """Signed distance to the crown (cap-local): an oval, near upright, a flat top with a firm rounded edge."""
    z = q[:, 2]
    t = np.clip(z / F(CAP_H), 0, 1)
    rx = F(CAP_R0[0]) + F(CAP_R1[0] - CAP_R0[0]) * t
    ry = F(CAP_R0[1]) + F(CAP_R1[1] - CAP_R0[1]) * t
    e = (np.sqrt((q[:, 0] / rx) ** 2 + (q[:, 1] / ry) ** 2) - F(1.0)) * np.minimum(rx, ry)
    dz = np.maximum(z - F(CAP_H), F(-0.03) - z)
    rr = F(0.03)
    a = e + rr
    b = dz + rr
    return np.sqrt(np.maximum(a, 0) ** 2 + np.maximum(b, 0) ** 2) + np.minimum(np.maximum(a, b), 0) - rr


def _band_r(a):
    return 1.0 / np.sqrt((np.sin(a) / F(CAP_R0[0])) ** 2 + (np.cos(a) / F(CAP_R0[1])) ** 2)


def peak_sd(q):
    """The bill: a half-moon from the band's front, sloping down over his brows and curved down at its sides."""
    a = np.arctan2(q[:, 0], -q[:, 1])
    rho = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - (_band_r(a) - F(0.006))
    L = F(PEAK_L) * np.sqrt(np.clip(F(1) - (a / F(PEAK_A)) ** 2, 0, 1))
    c, s = F(math.cos(PEAK_SLOPE)), F(math.sin(PEAK_SLOPE))
    z = q[:, 2] - F(0.008) + F(0.03) * (a / F(PEAK_A)) ** 2              # the sides curve down
    t = np.clip(rho * c + z * s, 0, L)
    dx, dz = rho - t * c, z - t * s
    d = np.sqrt(dx * dx + dz * dz) - F(PEAK_TH)
    return np.maximum(d, (np.abs(a) - F(PEAK_A)) * F(0.2))


def _under_cap(P):
    """< 0 where the head may be: below the cap's foot, or well inside its crown."""
    q = cap_local(P)
    return np.minimum(q[:, 2] + F(0.004), crown_sd(q) + F(CAP_T + 0.004))


def cap_field():
    """Olive ripstop (label 0): the crown with its flat top, a welt round the top's edge, the curved bill; a small red
    and white flag patch on the front of the crown is left out (the unit patch is on his sleeve)."""
    fd = Field("Cap")
    cloth = lambda P: F(0.0008) * NOISE(P * F(45)) + F(0.0006) * NOISE(P * F(120))
    lo, hi = CAP_O - v3((0.4, 0.4, 0.15)), CAP_O + v3((0.4, 0.4, 0.35))
    fd.add(Func(lambda P: np.abs(crown_sd(cap_local(P)) + F(CAP_T / 2)) - F(CAP_T / 2), lo, hi, disp=cloth, disp_amp=0.001), 0.0)
    fd.inter(Func(lambda P: F(-0.002) - cap_local(P)[:, 2], lo, hi), 0.0)
    def welt(P):
        q = cap_local(P)
        return np.maximum(np.abs(crown_sd(q) - F(0.001)) - F(0.004), np.abs(q[:, 2] - F(CAP_H - 0.016)) - F(0.005))
    fd.add(Func(welt, lo, hi), 0.003)
    fd.add(Func(lambda P: peak_sd(cap_local(P)), CAP_O - v3((0.35, 0.4, 0.12)), CAP_O + v3((0.35, 0.1, 0.15))), 0.004)
    # vertical seams down the crown's sides
    def seams(P):
        q = cap_local(P)
        a = np.arctan2(q[:, 0], -q[:, 1])
        out = F(1.0) * np.ones(len(P), F)
        for ac in (-1.5, 1.5, math.pi):
            d = np.abs(np.mod(a - F(ac) + F(math.pi), F(2 * math.pi)) - F(math.pi)) * F(0.2)
            out = np.minimum(out, d)
        return np.maximum(np.maximum(out - F(0.0016), np.abs(crown_sd(q)) - F(0.004)), q[:, 2] - F(CAP_H - 0.02))
    fd.sub(Func(seams, lo, hi), 0.0015)
    return fd


def cap_surface(a, z, out=0.0):
    """A point on the crown's outer surface (cap-local) at angle a from the front and height z, and its normal."""
    q = np.array([[math.sin(a) * 0.3, -math.cos(a) * 0.3, z]], F)
    for _ in range(10):
        d = crown_sd(q)
        g = np.zeros_like(q)
        for k in range(3):
            e = np.zeros(3, F)
            e[k] = 0.001
            g[:, k] = (crown_sd(q + e) - crown_sd(q - e)) / F(0.002)
        g = g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), F(1e-9))
        q = q - g * d[:, None]
    n = norm(v3(g[0]))
    return v3(q[0]) + n * out, n


# ======================================================================================= hair
def hair_field():
    """Short dark-brown hair cropped close at the back and over the ears, under the cap."""
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
        bottom = F(1.716) + F(1.6 - 1.716) * back + F(1.64 - 1.716) * burn
        bottom = bottom + F(0.005) * np.sin(x * F(60))
        front = np.where(ax > F(0.125), F(-0.07) - y, F(-0.02) - y)
        return np.maximum(bottom - z, front)
    fd.add(Inter(Shell(hull, 0.002, 0.01, pad=0.06, disp=strands, disp_amp=0.002),
                 Func(keep, HEAD_C - v3((0.4, 0.4, 0.5)), HEAD_C + 0.35), 0.003), 0.0)
    fd.inter(Func(_under_cap, CAP_O - 0.5, CAP_O + 0.5), 0.002)
    return fd


# ======================================================================================= headset (black)
CUP_C = {sx: hp((sx * 0.175, 0.03, 1.655)) for sx in (-1, 1)}      # the ear cups' centres (over the ears)
CUP_R, CUP_T = 0.066, 0.05
BAND_Y = 0.03                                                    # the headband's plane (y, cap-local-ish), over the crown


def _cup_axis(sx):
    return norm(v3((sx * 1.0, 0.0, 0.08)))


def _cup_out(sx):
    """The cup's outer face centre."""
    return CUP_C[sx] + _cup_axis(sx) * (0.038 + CUP_T * 0.5)


def headband_path():
    """The band's middle line: up from each cup, over the cap's sides and its flat top (cap-local, lifted 0.012)."""
    pts = []
    for k in range(13):
        th = -math.pi / 2 + math.pi * k / 12          # -90 (his right) .. +90 (his left)
        d = np.array([math.sin(th), 0.0, math.cos(th)])
        c = np.array([0.0, BAND_Y, 0.04])
        # march from outside toward the cap's centre line until outside the crown by 0.012
        ts = np.linspace(0.45, 0.0, 400)
        Q = (c[None, :] + ts[:, None] * d[None, :]).astype(F)
        v = crown_sd(Q)
        i = np.argmax(v < F(0.013))
        pts.append(cap_world(Q[i]))
    return pts


def headset_field():
    """Black polymer (8) and coyote padding (0, kit material): the band over the cap, two big ear cups on short yokes,
    a boom mic from the left cup to his mouth with a black foam tip."""
    fd = Field("Headset")
    band = headband_path()
    ns = [norm(cap_world(np.array([0, BAND_Y, 0.04])) - p) * -1 for p in band]
    fd.add(Lock(band, [0.03] * len(band), [0.011] * len(band), ns, k=0.004), 0.0, K_BLACK)
    fd.add(Lock(band[3:-3], [0.02] * (len(band) - 6), [0.016] * (len(band) - 6), ns[3:-3], k=0.004), 0.004, K_BLACK)   # the pad
    for sx in (-1, 1):
        ax = _cup_axis(sx)
        c = CUP_C[sx] + ax * 0.038
        R = rot_from_axes(z_axis=ax)
        fd.add(Cylinder(c, CUP_R - 0.008, 0.024, rr=0.01, R=R), 0.006, K_COY)                      # the cushion
        fd.add(Cylinder(c + ax * (CUP_T * 0.5), CUP_R, CUP_T, rr=0.02, R=R), 0.006, K_BLACK)          # the cup
        fd.add(Cylinder(c + ax * (CUP_T + 0.004), CUP_R * 0.62, 0.012, rr=0.005, R=R), 0.004, K_BLACK)  # its boss
        fd.sub(Torus(c + ax * (CUP_T + 0.006), CUP_R * 0.78, 0.004, R=R), 0.002)
        # the yoke: from the band's end down to the cup's top
        top = band[0] if sx < 0 else band[-1]
        cup_top = c + ax * (CUP_T * 0.5) + Z * (CUP_R - 0.006)
        mid = lerp(top, cup_top, 0.5) + v3((sx * 0.012, 0, 0))
        fd.add(Chain([top, mid, cup_top], [0.011, 0.011, 0.012], k=0.004), 0.004, K_BLACK)
    # the boom mic: from the left cup's front round to his mouth
    c = CUP_C[1] + _cup_axis(1) * (0.038 + CUP_T * 0.5)
    pts = [c + v3((0.004, -0.045, -0.02)), c + v3((-0.02, -0.1, -0.05)), hp((0.12, -0.15, 1.56)), hp((0.085, -0.19, 1.552))]
    fd.add(Chain(pts, [0.008, 0.007, 0.006, 0.006], k=0.004), 0.003, K_BLACK)
    fd.add(Ellipsoid(hp((0.078, -0.198, 1.55)), (0.02, 0.015, 0.015), R=euler(0, 0, 0.8)), 0.004, K_BLACK)
    return fd


# ======================================================================================= the combat shirt (olive)
SHIRT_OFF, SHIRT_T = 0.016, 0.012
ROLL_S = 0.075                       # the sleeves end this far down the forearm (rolled above the elbow's crease)


def shirt_base():
    b = Field("ShirtBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        for p, k in arm_prims(side):
            b.add(p, k)
    return b


def _arm_s(P, side, seg):
    """Distance along an arm segment (0: upper arm, 1: forearm), the squared distance off its axis, its length."""
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    a, b = (sh, el) if seg == 0 else (el, wr)
    ax = norm(b - a)
    L = float(np.linalg.norm(b - a))
    q = P - a.astype(F)
    s = q @ ax.astype(F)
    perp = q - s[:, None] * ax.astype(F)[None, :]
    return s, (perp ** 2).sum(1), L


def _sleeve_end(P, extra=0.0):
    """> 0 past the rolled sleeves' ends (only round each forearm)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2, L = _arm_s(P, side, 1)
        lateral = P[:, 0] * F(sx) - F(0.42)
        out = np.maximum(out, np.where((lateral > 0) & (d2 < F(0.16 ** 2)), s - F(ROLL_S + extra), F(-1.0)))
    return out


def _neck_open(P, r=0.128):
    """> 0 inside the opening round his neck (near the neck's axis only)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    yn = F(0.07) - F(0.2) * np.clip(z - F(1.36), 0, None)
    rho = np.sqrt(x * x + (F(0.9) * (y - yn)) ** 2)
    return np.minimum(F(r) - rho, z - F(1.37))


def _waist_cut(P):
    """> 0 below the shirt's tail (tucked in under the belt), only round his body (not the arms)."""
    return np.where(np.abs(P[:, 0]) < F(0.38), F(0.915) - P[:, 2], F(-1.0))


def shirt_field():
    """Olive ripstop (label 0) over his torso and arms, the sleeves rolled above the elbows into thick cuffs, a stand
    collar round his neck; the unit patch on his left sleeve: a red shield (5) with a white bar across it (6)."""
    fd = Field("Shirt")
    base = shirt_base()
    lo, hi = (-0.8, -0.4, 0.85), (0.8, 0.45, 1.56)
    def fn(P):
        d = base.eval(P, margin=0.08)
        z = P[:, 2]
        folds = F(0.0018) * NOISE(P * F(14)) + F(0.0012) * NOISE(P * np.array([6, 6, 30], F))
        main = np.abs(d - F(SHIRT_OFF) - folds) - F(SHIRT_T * 0.5)
        return smax(main, np.maximum(np.maximum(_neck_open(P), _sleeve_end(P)), _waist_cut(P)), 0.004)
    fd.add(Func(fn, lo, hi), 0.0)
    # the rolled cuffs: a fat roll round each forearm just below the elbow
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = el + ax * (ROLL_S - 0.012)
        fd.add(Torus(c, 0.07, 0.019, R=rot_from_axes(z_axis=ax), disp=lambda P: F(0.002) * NOISE(P * F(30)), disp_amp=0.002), 0.012)
        fd.add(Torus(c - ax * 0.024, 0.074, 0.016, R=rot_from_axes(z_axis=ax)), 0.012)
    # the stand collar
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    def collar(P):
        z = P[:, 2]
        top = F(1.47) + F(0.03) * smoothstep(-0.02, 0.1, P[:, 1])
        return np.maximum(z - top, F(1.37) - z)
    fd.add(Inter(Shell(nk, 0.026, 0.012, pad=0.1), Func(collar, (-0.4, -0.4, 1.3), (0.4, 0.4, 1.6)), 0.004), 0.004)
    # the unit patch on his left sleeve
    sh, el = J["shoulder_L"], J["elbow_L"]
    pax = norm(el - sh)
    outw = norm(v3((1.0, -0.15, 0.35)) - pax * float(v3((1.0, -0.15, 0.35)) @ pax))
    pc = sh + pax * 0.12
    def patch(P, w=0.042, h=0.05):
        q = P - pc.astype(F)
        s = q @ pax.astype(F)
        perp = q - s[:, None] * pax.astype(F)[None, :]
        r = np.sqrt((perp ** 2).sum(1)) + F(1e-6)
        cosang = (perp @ outw.astype(F)) / r
        u = np.arccos(np.clip(cosang, -1, 1)) * F(0.1)             # across the sleeve (arc length)
        return np.maximum(np.maximum(u - F(w), np.abs(s) - F(h)), F(0.3) - cosang)
    fd.paint(Func(lambda P: patch(P), pc - 0.2, pc + 0.2), RED)
    fd.paint(Func(lambda P: np.maximum(patch(P), np.abs((P - pc.astype(F)) @ pax.astype(F)) - F(0.011)), pc - 0.2, pc + 0.2), WHITE)
    return fd


# ======================================================================================= trousers, boots, gloves
def legs_base():
    b = Field("Legs")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], 0.08)
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            b.add(p, k)
    return b


def trousers_field():
    """Olive ripstop (label 0) from his waist into his boots, creased at the knees, a cargo pocket with a flap on the
    outside of each thigh."""
    fd = Field("Trousers")
    lb = legs_base()
    lo, hi = v3((-0.5, -0.4, 0.15)), v3((0.5, 0.45, 1.06))
    def fn(P):
        d = lb.eval(P, margin=0.08)
        z = P[:, 2]
        off = F(0.014) + F(0.01) * smoothstep(0.5, 0.3, z)
        return np.abs(d - off) - F(0.0065)
    wr = lambda P: F(0.0016) * NOISE(P * np.array([30, 30, 60], F)) + F(0.0025) * np.sin(P[:, 2] * F(80) + F(2) * NOISE(P * F(5))) * smoothstep(0.52, 0.4, P[:, 2]) * smoothstep(0.3, 0.38, P[:, 2])
    fd.add(Inter(Func(fn, lo, hi, disp=wr, disp_amp=0.004), Func(lambda P: np.maximum(F(0.24) - P[:, 2], P[:, 2] - F(0.975)), lo, hi), 0.004), 0.0)
    # cargo pockets
    surf = Func(lambda P: lb.eval(P, margin=0.12) - F(0.024), (-0.6, -0.5, 0.2), (0.6, 0.5, 1.1))
    for sx in (-1, 1):
        o = v3((sx * 0.6, -0.0, 0.6))
        h, ok = ray_hit(surf, [o], [v3((-sx, 0, 0))], tmax=0.6)
        if not ok[0]:
            continue
        c = h[0]
        out = norm(v3((sx, -0.1, 0)))
        R = rot_from_axes(y_axis=out, z_axis=Z)
        fd.add(RoundBox(c + out * 0.006, (0.075, 0.016, 0.085), 0.012, R=R, disp=lambda P: F(0.0012) * NOISE(P * F(30)), disp_amp=0.0015), 0.008)
        fd.add(RoundBox(c + out * 0.016 + Z * 0.07, (0.08, 0.012, 0.026), 0.008, R=R), 0.004)                    # the flap
    return fd


def foot_hull(side):
    ft = Field("FootHull")
    foot(ft, side)
    kn, an = J["knee_" + side], J["ankle_" + side]
    ft.add(RoundCone(kn, an, 0.084, 0.056), 0.03)
    return ft


def boots_field():
    """Black leather combat boots (label 0) laced high up the shin over the trousers, padded collars, thick lugged soles."""
    fd = Field("Boots")
    crease = lambda P: F(0.0014) * NOISE(P * F(26))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        ft = foot_hull(side)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        def fn(P, ft=ft):
            d = ft.eval(P, margin=0.06)
            off = F(0.008) + F(0.034) * smoothstep(0.1, 0.19, P[:, 2])
            return np.abs(d - off) - F(0.012)
        fd.add(Inter(Func(fn, an - 0.35, an + 0.35, disp=crease, disp_amp=0.002), Func(lambda P: P[:, 2] - F(0.3), an - 0.35, an + 0.35), 0.006), 0.0)
        kn = J["knee_" + side]
        ax = norm(kn - an)
        fd.add(Torus(an + ax * 0.19 + v3((0, 0.004, 0.0)), 0.094, 0.014, R=rot_from_axes(z_axis=ax)), 0.008)          # the collar
        fd.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.098)), (0.074, 0.168, 0.016), 0.01, R=Rz,
                        disp=lambda P: F(0.0015) * NOISE(P * F(40)), disp_amp=0.002), 0.008)
        fd.add(RoundBox(an + fwd * -0.032 + v3((0, 0, -0.08)), (0.06, 0.055, 0.032), 0.012, R=Rz), 0.008)
        # laces up the front
        for k in range(6):
            z = 0.085 + 0.034 * k
            p = an + fwd * (0.1 - 0.012 * k) + v3((0, 0, z - an[2] + 0.02))
            fd.add(RoundBox(p, (0.03, 0.006, 0.004), 0.003, R=Rz @ euler(-0.3, 0, 0)), 0.002)
    return fd


def gloves_field():
    """Black tactical gloves (label 8, kit material): snug over his fists, hard knuckle guards, short cuffs with tabs."""
    fd = Field("Gloves")
    for side in ("R", "L"):
        hh = Field("HandHull")
        hand(hh, side)
        fd.add(Shell(hh, 0.006, 0.01, pad=0.05, disp=lambda P: F(0.0008) * NOISE(P * F(50)), disp_amp=0.001), 0.0, K_BLACK)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        def cuff(P, wr=wr, ax=ax):
            s = (P - wr.astype(F)) @ ax.astype(F)
            q = P - wr.astype(F) - s[:, None] * ax.astype(F)[None, :]
            rho = np.sqrt((q * q).sum(1))
            return np.maximum(np.abs(rho - F(0.064)) - F(0.008), np.maximum(-s - F(0.055), s - F(0.03)))
        fd.add(Func(cuff, wr - 0.3, wr + 0.3), 0.012, K_BLACK)
        wrf, f, n, t = hand_frame(side)
        # the hard knuckle guard: a moulded plate over the back of the fist
        h, ok = ray_hit(hh, [wrf + f * 0.115 - n * 0.3], [n], tmax=0.4)
        kc = (h[0] if ok[0] else wrf + f * 0.115 - n * 0.06) - n * 0.012
        Rk = np.stack([t, -n, f], axis=1)
        fd.add(RoundBox(kc, (0.062, 0.008, 0.03), 0.008, R=Rk), 0.008, K_WEB)
        for o in (-0.042, -0.014, 0.014, 0.042):
            fd.add(Ellipsoid(kc + t * o - n * 0.008 + f * 0.012, (0.013, 0.008, 0.014), R=Rk), 0.006, K_WEB)
    return fd


# ======================================================================================= the control pad (left forearm)
def pad_frame():
    """(centre on the forearm, along (toward the wrist), out (its face), across)."""
    el, wr = J["elbow_L"], J["wrist_L"]
    ax = norm(wr - el)
    out = norm(v3((1.0, -0.35, 0.6)) - ax * float(v3((1.0, -0.35, 0.6)) @ ax))
    c = lerp(el, wr, 0.55)
    fd = Field("Fa")
    for p, k in arm_prims("L")[3:5]:
        fd.add(p, k)
    h, ok = ray_hit(fd, [c + out * 0.3], [-out], tmax=0.4)
    surf = h[0] if ok[0] else c + out * 0.07
    return surf, ax, out, norm(np.cross(out, ax))


def pad_field():
    """A rugged control pad strapped to his left forearm: a black polymer housing (8) with bumpers, a pale green screen
    (0: painted, kit material's coyote is replaced by the pad's own colours: 0 screen, 8 housing), buttons; two straps."""
    fd = Field("Pad")
    c, ax, out, acr = pad_frame()
    R = np.stack([acr, ax, out], axis=1)
    fd.add(RoundBox(c + out * 0.016, (0.042, 0.06, 0.012), 0.008, R=R), 0.0, 8)
    for e in (-1, 1):
        fd.add(RoundBox(c + out * 0.016 + ax * (e * 0.058), (0.046, 0.01, 0.014), 0.006, R=R), 0.004, 8)        # bumpers
    fd.paint(RoundBox(c + out * 0.028, (0.03, 0.04, 0.006), 0.004, R=R), 0)                                     # the screen
    fd.sub(RoundBox(c + out * 0.03, (0.031, 0.041, 0.002), 0.003, R=R), 0.002)
    for k in range(3):
        fd.add(Sphere(c + out * 0.026 + ax * 0.05 + acr * (-0.024 + 0.024 * k), 0.006), 0.002, 5)
    # straps round the forearm
    for e in (-1, 1):
        sc = c + ax * (e * 0.035) - out * 0.06
        fd.add(Inter(Shell(Cylinder(sc, 0.072, 0.03, R=rot_from_axes(z_axis=ax)), 0.0, 0.006),
                     Func(lambda P, sc=sc: np.abs((P - sc.astype(F)) @ ax.astype(F)) - F(0.012), sc - 0.12, sc + 0.12), 0.002), 0.003, 8)
    return fd


# ======================================================================================= the plate carrier, belt, radio
VEST_OFF, VEST_T = 0.044, 0.034


def vest_base():
    b = Field("VestBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    return b


def _box(v, lo, hi):
    return np.maximum(F(lo) - v, v - F(hi))


def vest_keep(P):
    """< 0 on the carrier: the front and back plates (their shoulders cut in), the cummerbund round his sides, two
    shoulder straps over his traps; never round his neck."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    top_f = F(1.33) - F(1.1) * np.clip(ax - F(0.09), 0, None) ** 1.0 * smoothstep(0.08, 0.2, ax)
    top_b = F(1.37) - F(1.0) * np.clip(ax - F(0.1), 0, None) * smoothstep(0.08, 0.2, ax)
    top = np.where(y < F(0.06), top_f, top_b)
    plates = np.maximum(np.maximum(ax - F(0.215), z - top), F(0.975) - z)
    cumm = _box(z, 0.975, 1.12)
    straps = np.maximum(_box(ax, 0.105, 0.19), F(1.2) - z)
    keep = np.minimum(np.minimum(plates, cumm), straps)
    return np.maximum(keep, _neck_open(P, 0.135))


def vest_outer():
    vb = vest_base()
    return Func(lambda P: vb.eval(P, margin=0.14) - F(VEST_OFF + VEST_T * 0.5 + 0.002), (-1, -1, 0.6), (1, 1, 1.8))


def vest_field():
    """Coyote nylon (label 0): the plate carrier with rows of webbing (7) across its plates, three pouches across the
    front (their flaps, black buckles 8), a radio pouch on his left side, a small black radio on his back with its whip
    antenna; the rigger's belt (0) with a black buckle (8)."""
    fd = Field("Vest")
    base = vest_base()
    lo, hi = (-0.6, -0.5, 0.85), (0.6, 0.55, 1.62)
    def fn(P):
        d = base.eval(P, margin=0.12)
        z = P[:, 2]
        ax = np.abs(P[:, 0])
        # the plates stand off more than the cummerbund
        plate = smoothstep(0.24, 0.18, ax) * smoothstep(1.1, 1.14, z)
        off = F(VEST_OFF) - F(0.012) * (F(1) - plate)
        sh = np.abs(d - off) - F(VEST_T * 0.5) + F(0.008) * (F(1) - plate)
        return smax(sh, vest_keep(P), 0.006)
    fd.add(Func(fn, lo, hi, disp=lambda P: F(0.0008) * NOISE(P * F(40)), disp_amp=0.001), 0.0, K_COY)
    # webbing rows across the plates (painted darker, a little raised)
    def web(P):
        z = P[:, 2]
        row = np.abs(np.mod(z - F(1.0), F(0.042)) - F(0.021)) - F(0.0085)
        d = base.eval(P, margin=0.12)
        return np.maximum(np.maximum(row, np.abs(d - F(VEST_OFF + VEST_T * 0.5)) - F(0.004)),
                          np.maximum(np.abs(P[:, 0]) - F(0.19), np.maximum(F(1.13) - z, z - F(1.3))))
    fd.add(Func(web, lo, hi), 0.002, K_WEB)
    vo = vest_outer()
    # three pouches across the front
    for x in (-0.11, 0.0, 0.11):
        h, ok = ray_hit(vo, [v3((x, -0.6, 1.08))], [v3((0, 1, 0))], tmax=0.6)
        if not ok[0]:
            continue
        c = h[0] + v3((0, -0.026, 0))
        fd.add(RoundBox(c, (0.047, 0.028, 0.068), 0.014, R=euler(-0.08, 0, 0), disp=lambda P: F(0.0012) * NOISE(P * F(30)), disp_amp=0.0015), 0.008, K_COY)
        fd.add(RoundBox(c + v3((0, -0.012, 0.05)), (0.05, 0.024, 0.024), 0.01, R=euler(-0.1, 0, 0)), 0.004, K_COY)   # the flap
        fd.add(RoundBox(c + v3((0, -0.035, 0.03)), (0.012, 0.004, 0.016), 0.003), 0.002, K_BLACK)                 # its buckle
    # the radio pouch on his left side
    h, ok = ray_hit(vo, [v3((0.6, -0.02, 1.06))], [v3((-1, 0, 0))], tmax=0.6)
    if ok[0]:
        c = h[0] + v3((0.032, 0, 0))
        fd.add(RoundBox(c, (0.03, 0.045, 0.08), 0.014, R=euler(0, 0, 0.05)), 0.008, K_COY)
        fd.add(RoundBox(c + v3((0.004, 0, 0.09)), (0.022, 0.03, 0.02), 0.006), 0.004, K_BLACK)                     # the radio's top
        fd.add(Cylinder(c + v3((0.004, 0.012, 0.13)), 0.007, 0.06, rr=0.003), 0.002, K_BLACK)                       # a stub antenna
    # the radio on his back and its whip antenna
    h, ok = ray_hit(vo, [v3((0.06, 0.7, 1.17))], [v3((0, -1, 0))], tmax=0.7)
    rb = (h[0] if ok[0] else v3((0.06, 0.3, 1.17))) + v3((0, 0.045, 0))
    fd.add(RoundBox(rb, (0.08, 0.042, 0.12), 0.016, R=euler(0.06, 0, 0)), 0.006, K_BLACK)
    fd.add(RoundBox(rb + v3((0, 0.02, 0.0)), (0.084, 0.03, 0.09), 0.012, R=euler(0.06, 0, 0)), 0.004, K_COY)        # its pouch
    ab = rb + v3((0.055, 0.02, 0.13))
    fd.add(Cylinder(ab + Z * 0.02, 0.014, 0.04, rr=0.004), 0.003, K_BLACK)
    fd.add(Chain([ab + Z * 0.04, ab + v3((0.01, 0.02, 0.09))], [0.011, 0.009], k=0.0), 0.003, K_BLACK)              # the spring
    tip = ANT_TIP
    fd.add(RoundCone(ab + v3((0.01, 0.02, 0.09)), tip, 0.0075, 0.0045), 0.002, K_BLACK)
    fd.add(Sphere(tip, 0.009), 0.002, K_BLACK)
    # the rigger's belt
    hip = Field("Hip")
    tp = torso_prims()
    hip.add(tp[4][0], 0.0)
    hip.add(tp[5][0], 0.08)
    def belt(P):
        d = hip.eval(P, margin=0.1)
        return np.maximum(np.abs(d - F(0.036)) - F(0.01), np.abs(P[:, 2] - F(0.955)) - F(0.025))
    fd.add(Func(belt, (-0.45, -0.4, 0.88), (0.45, 0.45, 1.03)), 0.0, K_COY)
    h, ok = ray_hit(Func(lambda P: hip.eval(P, margin=0.12) - F(0.046), (-0.5, -0.6, 0.85), (0.5, 0.5, 1.05)), [v3((0, -0.6, 0.955))], [v3((0, 1, 0))], tmax=0.6)
    if ok[0]:
        fd.add(RoundBox(h[0] + v3((0, -0.006, 0)), (0.04, 0.008, 0.03), 0.006), 0.003, K_BLACK)
    return fd


ANT_TIP = v3((0.1, 0.5, 2.08))            # the whip antenna's tip (over his left shoulder, behind)


# ======================================================================================= the emitter (machine)
MAST_C = v3((0.56, 0.3, 0.0))             # the mast's axis at the floor
DECK_R, DECK_H = 0.29, 0.06
HOUSE = (0.1, 0.1, 0.2)                    # the housing's half extents (z: half height), on the deck
HOUSE_Z = DECK_H + HOUSE[2]
MAST_Z0 = DECK_H + 2 * HOUSE[2]            # the mast's foot (the housing's top)
MAST_R = 0.048
RINGS = ((1.48, 0.25), (1.69, 0.215), (1.88, 0.18))      # (height, major radius) of the ring coils
RING_r = 0.036
CUP_Z = 2.02                                # the emitter's cup
EMIT_Z = 2.2                                # the emitter head's centre
EMIT_R = 0.085
EMIT_C = MAST_C + Z * EMIT_Z
FRONT = norm(v3((-0.45, -1.0, 0.0)))       # the machine's front (toward him and the robots: the camera's side)
CAPS = (-115.0, -45.0, 70.0)                # the capacitor canisters' angles round the mast (deg, from +X)
CAP_RAD, CAP_HH, CAP_DIST = 0.072, 0.21, 0.215
CHARGE_Z0, CHARGE_Z1 = DECK_H + 0.07, DECK_H + 0.36    # the charge windows' foot and top


def cap_c(a):
    r = math.radians(a)
    return MAST_C + v3((math.cos(r), math.sin(r), 0.0)) * CAP_DIST


def cap_window_dir(a):
    """The direction a canister's charge window faces: outward, turned toward the camera's side."""
    c = cap_c(a)
    o = norm(v3((c[0] - MAST_C[0], c[1] - MAST_C[1], 0.0)))
    return norm(o + FRONT * 0.8)


def _octagon(P, c, r, h, z0, rr=0.012):
    q = P - c.astype(F)
    d = F(-1e3) * np.ones(len(P), F)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        d = np.maximum(d, q[:, 0] * F(math.cos(a)) + q[:, 1] * F(math.sin(a)) - F(r - rr))
    dz = np.abs(P[:, 2] - F(z0 + h / 2)) - F(h / 2 - rr)
    return np.minimum(np.maximum(d, dz), 0) + np.sqrt(np.maximum(d, 0) ** 2 + np.maximum(dz, 0) ** 2) - F(rr)


def machine_field():
    """On `machine`: the skid, the housing with its fins, hazard band and warning plate, the capacitor canisters and
    their cables."""
    fd = Field("Machine")
    c = MAST_C
    rv = lambda P: F(0.0006) * NOISE(P * F(50))
    fd.add(Func(lambda P: _octagon(P, c, DECK_R, DECK_H, 0.0), c - 0.4, c + 0.4, disp=rv, disp_amp=0.001), 0.0, M_OLIVE)
    for k in range(8):                                                        # bolts round the deck's top edge
        a = 2 * math.pi * k / 8
        fd.add(Sphere(c + v3((math.cos(a), math.sin(a), 0)) * (DECK_R - 0.03) + Z * DECK_H, 0.011), 0.002, M_GUN)
    # the housing
    hc = c + Z * HOUSE_Z
    Rf = rot_from_axes(y_axis=FRONT, z_axis=Z)
    acr_h = norm(np.cross(Z, FRONT))
    fd.add(RoundBox(hc, HOUSE, 0.018, R=Rf, disp=rv, disp_amp=0.001), 0.006, M_OLIVE)
    fd.add(RoundBox(c + Z * (MAST_Z0 - 0.012), (HOUSE[0] + 0.012, HOUSE[1] + 0.012, 0.014), 0.008, R=Rf), 0.004, M_GUN)     # its lid
    for k in range(4):                                                        # cooling fins on its four sides
        d = Rf @ v3((math.cos(k * math.pi / 2), math.sin(k * math.pi / 2), 0))
        sd = np.cross(Z, d)
        for j in range(-3, 4):
            if k == 1 and abs(j) <= 2:
                continue                                                      # (the front's middle: the warning plate)
            p = hc + d * (HOUSE[0] + 0.012) + sd * (j * 0.03) + Z * -0.02
            fd.add(RoundBox(p, (0.004, 0.018, 0.13), 0.003, R=rot_from_axes(x_axis=sd, z_axis=Z)), 0.002, M_GUN)
    # hazard stripes round the housing's top
    def hz_band(P):
        q = P - hc.astype(F)
        near = np.maximum(np.abs(q @ acr_h.astype(F)), np.abs(q @ FRONT.astype(F))) - F(HOUSE[0] + 0.04)
        return np.maximum(np.abs(P[:, 2] - F(MAST_Z0 - 0.045)) - F(0.022), near)
    fd.paint(Func(hz_band, hc - 0.3, hc + 0.3), M_YELLOW)
    def hz_stripes(P):
        u = (P[:, 0] + P[:, 1]) * F(1.0) + P[:, 2] * F(1.0)
        st = np.abs(np.mod(u, F(0.06)) - F(0.03)) - F(0.014)
        return np.maximum(st, hz_band(P))
    fd.paint(Func(hz_stripes, hc - 0.3, hc + 0.3), M_BLACK)
    # the warning plate on the housing's front: a yellow triangle edged black, a black bolt
    wp = hc + FRONT * (HOUSE[1] + 0.006) + Z * 0.0
    Rw = rot_from_axes(z_axis=FRONT, y_axis=Z)
    up, acr = Z, norm(np.cross(Z, FRONT))
    fd.add(RoundBox(wp, (0.055, 0.058, 0.004), 0.003, R=Rw), 0.002, M_YELLOW)
    def tri(P, s=1.0):
        q = P - wp.astype(F)
        u, v = q @ acr.astype(F), q @ up.astype(F) + F(0.02 * s)
        d1 = v - F(0.07 * s) + np.abs(u) * F(1.9)                      # the two upper edges (apex up)
        d2 = -v
        return np.maximum(np.maximum(d1 * F(0.45), d2), np.abs(q @ FRONT.astype(F)) - F(0.012))
    fd.paint(Func(lambda P: np.maximum(tri(P, 1.0), -tri(P, 0.78)), wp - 0.1, wp + 0.1), M_BLACK)
    def bolt(P):
        q = P - wp.astype(F)
        u, v = q @ acr.astype(F), q @ up.astype(F) + F(0.005)
        zig = np.abs(u - v * F(0.35) + np.where(v > 0, F(-0.004), F(0.004))) - F(0.0045)
        return np.maximum(np.maximum(zig, np.abs(v) - F(0.022)), np.abs(q @ FRONT.astype(F)) - F(0.012))
    fd.paint(Func(bolt, wp - 0.1, wp + 0.1), M_BLACK)
    # the capacitor canisters
    for a in CAPS:
        cc = cap_c(a)
        wd = cap_window_dir(a)
        fd.add(Cylinder(cc + Z * (DECK_H + CAP_HH), CAP_RAD, 2 * CAP_HH, rr=0.016, disp=rv, disp_amp=0.001), 0.006, M_GUN)
        for zz in (DECK_H + 0.035, DECK_H + 2 * CAP_HH - 0.03):
            fd.add(Torus(cc + Z * zz, CAP_RAD + 0.002, 0.009), 0.004, M_OLIVE)            # olive bands
        fd.add(Cylinder(cc + Z * (DECK_H + 2 * CAP_HH + 0.012), CAP_RAD - 0.012, 0.028, rr=0.008), 0.004, M_BLACK)    # the cap
        for k in range(10):                                                                               # its ribs
            ra = 2 * math.pi * k / 10
            fd.add(RoundBox(cc + Z * (DECK_H + 2 * CAP_HH + 0.014) + v3((math.cos(ra), math.sin(ra), 0)) * (CAP_RAD - 0.016),
                            (0.004, 0.012, 0.016), 0.003, R=rot_from_axes(y_axis=v3((math.cos(ra), math.sin(ra), 0)), z_axis=Z)), 0.002, M_BLACK)
        tp = cc + Z * (DECK_H + 2 * CAP_HH + 0.03)
        fd.add(Cylinder(tp + Z * 0.016, 0.018, 0.032, rr=0.005), 0.003, M_STEEL)                          # the terminal
        # the charge window: a recessed slot in a black frame (the glowing bar sits in it)
        wc = cc + wd * CAP_RAD + Z * ((CHARGE_Z0 + CHARGE_Z1) / 2)
        Rw2 = rot_from_axes(z_axis=wd, y_axis=Z)
        fd.add(RoundBox(wc, (0.03, (CHARGE_Z1 - CHARGE_Z0) / 2 + 0.018, 0.012), 0.006, R=Rw2), 0.004, M_BLACK)
        fd.sub(RoundBox(wc + wd * 0.012, (0.019, (CHARGE_Z1 - CHARGE_Z0) / 2 + 0.004, 0.012), 0.003, R=Rw2), 0.002)
        # a hazard label on its side
        lc = cc + norm(np.cross(Z, wd)) * CAP_RAD * 0.97 + Z * (DECK_H + 0.3)
        fd.paint(Sphere(lc, 0.032), M_YELLOW)
        # the cable from the terminal over to the housing's side
        hd = norm(v3((MAST_C[0] - cc[0], MAST_C[1] - cc[1], 0.0)))
        end = MAST_C + -hd * (HOUSE[0] + 0.01) + Z * (MAST_Z0 - 0.08)
        pts = [tp + Z * 0.03, tp + Z * 0.05 + hd * 0.04, lerp(tp, end, 0.6) + Z * 0.045, end - hd * 0.03 + Z * 0.01, end]
        fd.add(Chain(pts, [0.016] * len(pts), k=0.01), 0.004, M_BLACK)
    # the console's cable arriving at the deck: a gland on the deck's edge
    gd = norm(v3((CON_P[0] - c[0], CON_P[1] - c[1], 0.0)))
    fd.add(Cylinder(c + gd * (DECK_R - 0.02) + Z * (DECK_H + 0.025), 0.03, 0.05, rr=0.008), 0.004, M_GUN)
    return fd


def mast_field():
    """On `mast`: the telescoped mast (olive) with its collars, the heat sink, the three ring coils (copper winding in
    olive clamps, spokes to the mast), the gunmetal cup and the cage of four prongs round the emitter head, a finial."""
    fd = Field("Mast")
    c = MAST_C
    rv = lambda P: F(0.0006) * NOISE(P * F(50))
    fd.add(Cylinder(c + Z * ((MAST_Z0 + 1.1) / 2), MAST_R, 1.1 - MAST_Z0, rr=0.01, disp=rv, disp_amp=0.001), 0.0, M_OLIVE)
    fd.add(Cylinder(c + Z * ((1.1 + CUP_Z) / 2), MAST_R - 0.01, CUP_Z - 1.1, rr=0.008), 0.004, M_OLIVE)
    for zz, rr in ((MAST_Z0 + 0.03, 0.07), (1.1, 0.062), (1.32, 0.055)):
        fd.add(Cylinder(c + Z * zz, rr, 0.04, rr=0.01), 0.006, M_GUN)                        # collars
        for k in range(4):
            a = 2 * math.pi * (k + 0.5) / 4
            fd.add(Sphere(c + v3((math.cos(a), math.sin(a), 0)) * rr + Z * zz, 0.008), 0.002, M_STEEL)
    # the heat sink: a stack of thin fins
    for k in range(7):
        fd.add(Cylinder(c + Z * (0.66 + 0.036 * k), 0.118, 0.011, rr=0.004), 0.003, M_GUN)
    # the ring coils
    winding = lambda P: F(0.0018) * np.sin(np.arctan2(P[:, 1] - F(c[1]), P[:, 0] - F(c[0])) * F(150))
    for z, R in RINGS:
        rc = c + Z * z
        fd.add(Torus(rc, R, RING_r, disp=winding, disp_amp=0.002), 0.0, M_COPPER)
        fd.add(Cylinder(rc, 0.07, 0.05, rr=0.012), 0.006, M_GUN)                             # the hub
        for k in range(3):
            a = 2 * math.pi * k / 3 + 0.4
            d = v3((math.cos(a), math.sin(a), 0))
            fd.add(RoundCone(rc + d * 0.06, rc + d * (R - RING_r * 0.4), 0.013, 0.011), 0.004, M_OLIVE)   # spokes
            fd.add(RoundBox(rc + d * R, (0.022, 0.03, RING_r + 0.012), 0.01, R=rot_from_axes(y_axis=d, z_axis=Z)), 0.004, M_OLIVE)  # clamps
    # the cup and the cage round the emitter head
    fd.add(RoundCone(c + Z * (CUP_Z - 0.06), c + Z * CUP_Z, 0.05, 0.1), 0.01, M_GUN)
    fd.add(Torus(c + Z * (CUP_Z + 0.004), 0.1, 0.014), 0.004, M_GUN)
    fd.add(Cylinder(c + Z * (CUP_Z + 0.03), 0.04, 0.05, rr=0.01), 0.004, M_STEEL)            # the insulator under the head
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        d = v3((math.cos(a), math.sin(a), 0))
        pts = [c + Z * (CUP_Z + 0.004) + d * 0.1, c + Z * (EMIT_Z - 0.05) + d * 0.15, c + Z * (EMIT_Z + 0.07) + d * 0.135,
               c + Z * (EMIT_Z + 0.15) + d * 0.06]
        fd.add(Chain(pts, [0.016, 0.014, 0.012, 0.01], k=0.006), 0.004, M_GUN)
        fd.add(Sphere(pts[2], 0.02), 0.004, M_STEEL)
    fd.add(Torus(c + Z * (EMIT_Z + 0.15), 0.06, 0.012), 0.004, M_GUN)
    fd.add(RoundCone(c + Z * (EMIT_Z + 0.15), c + Z * (EMIT_Z + 0.21), 0.022, 0.008), 0.004, M_STEEL)
    fd.add(Sphere(c + Z * (EMIT_Z + 0.22), 0.016), 0.003, M_RED)                              # a red beacon on top
    return fd


def emitter_field():
    """The emitter head (shipped glowing blue-white): a ball in its cage."""
    fd = Field("Emitter")
    fd.add(Sphere(EMIT_C, EMIT_R), 0.0)
    return fd


def charge_field():
    """The capacitors' charge bars (shipped glowing cyan), one in each window, from its foot up."""
    fd = Field("Charge")
    for a in CAPS:
        cc = cap_c(a)
        wd = cap_window_dir(a)
        wc = cc + wd * (CAP_RAD + 0.006) + Z * ((CHARGE_Z0 + CHARGE_Z1) / 2)
        fd.add(RoundBox(wc, (0.016, (CHARGE_Z1 - CHARGE_Z0) / 2, 0.006), 0.004, R=rot_from_axes(z_axis=wd, y_axis=Z)), 0.0)
    return fd


# ======================================================================================= the control case on its tripod
CON_P = v3((-0.52, -0.36, 0.0))              # the tripod's foot
CON_U = norm(v3((-CON_P[0], -CON_P[1], 0.0)))         # toward him (horizontal)
SN = norm(Z + CON_U * 0.36)                  # the panel's face (tilted toward him)
SU = norm(CON_U - SN * (CON_U @ SN))         # down the panel, toward him
SW = norm(np.cross(SU, SN))                  # across it (- is on his right as he faces it)
R_SLAB = np.stack([SW, SU, SN], axis=1)
SLAB_H = 0.86
SLAB_C = CON_P + Z * SLAB_H
SLAB_HALF = (0.2, 0.14, 0.04)
BTN_W, BTN_S = -0.075, 0.035                 # the trigger on the panel (across, toward him)
BTN_R = 0.034
GUARD_HINGE_S = BTN_S - 0.05                 # the guard's hinge, on the far side of the trigger
GUARD_OPEN = 118.0                           # its swing open (deg, about SW: up and away)


def slab_pt(w, s, h):
    """A point over the panel's top face: across, toward him, up off the face."""
    return SLAB_C + SW * w + SU * s + SN * (SLAB_HALF[2] + h)


BTN_BASE = slab_pt(BTN_W, BTN_S, 0.0)
BTN_TOP = slab_pt(BTN_W, BTN_S, 0.05)          # the trigger cap's top (rest)
GUARD_HINGE = slab_pt(BTN_W, GUARD_HINGE_S, 0.012)
LID_HINGE = slab_pt(0.0, -SLAB_HALF[1], 0.0)
LID_TILT = math.radians(125.0)                 # the lid open: swung up from the panel past upright, leaning back


def lid_frame():
    """The lid stands up from the hinge along LID_U, its inner face (the screen) toward him (LID_N)."""
    u = norm(SU * math.cos(LID_TILT) + SN * math.sin(LID_TILT))
    n = norm(np.cross(u, SW))
    if n @ CON_U < 0:
        n = -n
    return u, n


def console_field():
    """On `machine`: the tripod (olive legs, gunmetal head), the open rugged case (olive 0) with black handles and
    latches (8), the panel (gunmetal 5) with the key switch (steel 7), a row of toggles, lamps (red 12, yellow 13), the
    trigger's yellow collar (13), the lid with the screen's black bezel; the cable down the tripod and over the floor
    to the emitter's deck."""
    fd = Field("Console")
    c = CON_P
    # the tripod
    head = c + Z * (SLAB_H - 0.1)
    fd.add(Cylinder(head, 0.04, 0.06, rr=0.012), 0.0, M_GUN)
    fd.add(RoundCone(head, c + Z * 0.42, 0.024, 0.026), 0.006, M_OLIVE)
    fd.add(Cylinder(c + Z * 0.42, 0.04, 0.05, rr=0.012), 0.006, M_GUN)
    feet = []
    for k in range(3):
        a = math.atan2(CON_U[1], CON_U[0]) + math.pi / 3 + 2 * math.pi * k / 3
        d = v3((math.cos(a), math.sin(a), 0))
        ft = c + d * 0.21 + Z * 0.012
        feet.append(ft)
        fd.add(RoundCone(c + Z * 0.42 + d * 0.025, ft + Z * 0.02, 0.016, 0.013), 0.004, M_OLIVE)
        fd.add(Sphere(ft + Z * 0.005, 0.02), 0.004, M_BLACK)
    fd.add(Ellipsoid(SLAB_C - SN * 0.065, (0.07, 0.07, 0.03), R=R_SLAB), 0.02, M_GUN)          # the mounting plate
    # the case's lower half and its panel
    fd.add(RoundBox(SLAB_C - SN * 0.004, (SLAB_HALF[0] + 0.012, SLAB_HALF[1] + 0.012, SLAB_HALF[2]), 0.016, R=R_SLAB,
                    disp=lambda P: F(0.0006) * NOISE(P * F(40)), disp_amp=0.001), 0.004, M_OLIVE)
    fd.add(RoundBox(SLAB_C + SN * (SLAB_HALF[2] - 0.006), (SLAB_HALF[0] - 0.008, SLAB_HALF[1] - 0.008, 0.01), 0.005, R=R_SLAB), 0.003, M_GUN)
    for sx in (-1, 1):                                                       # carry handles on the sides
        hc = SLAB_C + SW * (sx * (SLAB_HALF[0] + 0.03))
        fd.add(Chain([hc - SU * 0.06 - SW * sx * 0.02, hc - SU * 0.05, hc + SU * 0.05, hc + SU * 0.06 - SW * sx * 0.02],
                     [0.011] * 4, k=0.004), 0.004, M_BLACK)
    for sx in (-1, 1):                                                       # latches on the near side
        fd.add(RoundBox(SLAB_C + SU * (SLAB_HALF[1] + 0.014) + SW * (sx * 0.11) + SN * 0.01, (0.022, 0.008, 0.02), 0.004, R=R_SLAB), 0.003, M_BLACK)
    # the panel's controls
    fd.add(Cylinder(BTN_BASE + SN * 0.006, BTN_R + 0.014, 0.014, rr=0.004, R=R_SLAB), 0.003, M_YELLOW)          # the collar
    fd.add(Cylinder(slab_pt(0.1, 0.05, 0.008), 0.018, 0.016, rr=0.004, R=R_SLAB), 0.003, M_STEEL)                # the key switch
    fd.add(RoundBox(slab_pt(0.1, 0.05, 0.022), (0.004, 0.012, 0.012), 0.002, R=R_SLAB), 0.002, M_BLACK)          # its key
    for k in range(4):
        w = -0.13 + 0.06 * k
        if abs(w - BTN_W) < 0.05:
            continue
        fd.add(RoundBox(slab_pt(w, -0.075, 0.006), (0.012, 0.012, 0.006), 0.003, R=R_SLAB), 0.002, M_BLACK)
        fd.add(RoundCone(slab_pt(w, -0.075, 0.01), slab_pt(w, -0.088, 0.034), 0.005, 0.0045), 0.002, M_STEEL)     # toggles
    for k, lab in enumerate((M_RED, M_YELLOW, M_YELLOW)):
        fd.add(Sphere(slab_pt(0.06 + 0.035 * k, -0.03, 0.002), 0.01), 0.002, lab)                                 # lamps
    # the lid, the screen's bezel
    u, n = lid_frame()
    lc = LID_HINGE + u * 0.14
    Rl = np.stack([SW, u, n], axis=1)
    fd.add(RoundBox(lc, (SLAB_HALF[0] + 0.012, 0.14, 0.026), 0.016, R=Rl), 0.0, M_OLIVE)
    fd.add(RoundBox(lc + n * 0.024, (SLAB_HALF[0] - 0.01, 0.12, 0.008), 0.006, R=Rl), 0.003, M_BLACK)
    fd.add(Cylinder(LID_HINGE, 0.012, 2 * SLAB_HALF[0] + 0.02, rr=0.004, R=rot_from_axes(z_axis=SW)), 0.003, M_GUN)
    # the cable: from under the case down the tripod, over the floor to the emitter's deck
    gd = norm(v3((c[0] - MAST_C[0], c[1] - MAST_C[1], 0.0)))
    end = MAST_C + gd * (DECK_R + 0.01) + Z * (DECK_H * 0.5)
    pts = [SLAB_C - SN * 0.07 - SU * 0.04, head - CON_U * 0.04, c + Z * 0.45 - CON_U * 0.05, c + Z * 0.06 - CON_U * 0.12 + v3((0, 0.04, 0)),
           c + v3((0.06, 0.24, 0.018)), v3((-0.12, 0.42, 0.018)), v3((0.18, 0.44, 0.018)), end + gd * 0.08 + v3((0, 0, -0.012)), end]
    fd.add(Chain(pts, [0.016] * len(pts), k=0.012), 0.004, M_BLACK)
    return fd


def screen_field():
    """The lid's screen (shipped glowing pale green)."""
    fd = Field("Screen")
    u, n = lid_frame()
    lc = LID_HINGE + u * 0.14
    fd.add(RoundBox(lc + n * 0.033, (SLAB_HALF[0] - 0.028, 0.102, 0.003), 0.002, R=np.stack([SW, u, n], axis=1)), 0.0)
    return fd


def guard_field():
    """The trigger's safety guard (closed): a hinged box cover over the trigger, yellow (13) with black stripes (8)."""
    fd = Field("Guard")
    gc = slab_pt(BTN_W, BTN_S, 0.034)
    half = (BTN_R + 0.02, BTN_R + 0.024, 0.032)
    fd.add(Inter(Shell(RoundBox(gc, half, 0.014, R=R_SLAB), 0.0, 0.007), Func(lambda P: F(0.004) - (P - slab_pt(0, 0, 0.0).astype(F)) @ SN.astype(F),
                                                                             gc - 0.2, gc + 0.2), 0.002), 0.0, M_YELLOW)
    def stripes(P):
        q = P - gc.astype(F)
        u = q @ SW.astype(F) + q @ SU.astype(F)
        return np.abs(np.mod(u, F(0.03)) - F(0.015)) - F(0.0065)
    fd.paint(Func(stripes, gc - 0.15, gc + 0.15), M_BLACK)
    fd.add(Cylinder(GUARD_HINGE, 0.009, 2 * half[0], rr=0.003, R=rot_from_axes(z_axis=SW)), 0.003, M_GUN)
    return fd


def button_field():
    """The big red trigger (12) in its collar: a mushroom cap on a short stem."""
    fd = Field("Button")
    fd.add(Cylinder(slab_pt(BTN_W, BTN_S, 0.024), 0.016, 0.03, rr=0.004, R=R_SLAB), 0.0, M_BLACK)
    fd.add(Cylinder(slab_pt(BTN_W, BTN_S, 0.038), BTN_R, 0.02, rr=0.008, R=R_SLAB), 0.004, M_RED)
    fd.add(Ellipsoid(slab_pt(BTN_W, BTN_S, 0.044), (BTN_R - 0.004, BTN_R - 0.004, 0.012), R=R_SLAB), 0.006, M_RED)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0.0, -0.242, 1.614)), 0.045, 0.45), (hp((0.0, -0.21, 1.69)), 0.03, 0.2)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.1, -0.14, 1.62)), 0.055, 0.45), (hp((sx * 0.07, -0.16, 1.63)), 0.03, 0.2)]
    return pts


# ======================================================================================= build config
GLB_NAME = "emp_tower"
ROOT_NAME = "EmpTowerHQ"
TEX_PREFIX = "emp"
MAT_NAME = "EmpMat"
MESH_NAME = "Emp"
BASE_MODULE = "emp_base"
ANIM_MODULE = "anim_emp"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Cap", "Headset", "Shirt", "Trousers", "Boots", "Gloves", "Pad", "Vest",
         "Machine", "Mast", "Emitter", "Charge", "Console", "Screen", "Guard", "Button"]
REGION_PARTS = ("Skin", "Shirt", "Headset", "Gloves", "Pad", "Vest", "Machine", "Mast", "Console", "Guard", "Button")
OLIVE_C = (0.4, 0.42, 0.28)               # the task force's olive drab
COYOTE_C = (0.6, 0.5, 0.36)
FATIGUES = {"base": OLIVE_C, "facing": (0.74, 0.1, 0.08), "brass": (0.93, 0.92, 0.88), "buff": COYOTE_C,
            "black": (0.05, 0.05, 0.05)}
KIT = {"base": COYOTE_C, "facing": OLIVE_C, "brass": (0.4, 0.4, 0.42), "buff": (0.46, 0.38, 0.27), "black": (0.06, 0.06, 0.065)}
MACHINE = {"olive": (0.36, 0.38, 0.24), "grey": (0.38, 0.4, 0.42), "brass": (0.78, 0.4, 0.2), "copper": (0.78, 0.4, 0.2),
           "red": (0.8, 0.08, 0.06), "white": (0.96, 0.76, 0.12)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_EmpSkin", "base": (0.8, 0.58, 0.44), "ruddy": (0.82, 0.48, 0.38), "lips": (0.68, 0.4, 0.34),
                      "brow": ((0.16, 0.1, 0.06), (0.3, 0.19, 0.11)),
                      "extra": ((LASH, (0.12, 0.07, 0.04), 0.5), (STUBBLE, (0.55, 0.4, 0.32), 0.3, 0.3))}),
    "Hair": ("hair", {"name": "HQ_EmpHair", "base": (0.16, 0.1, 0.06), "hi": (0.34, 0.22, 0.13), "low": (0.07, 0.045, 0.03),
                      "streak": (0.12, 0.08, 0.05), "tint": (0.22, 0.14, 0.08)}),
    "Cap": ("uniform", dict(FATIGUES, name="HQ_EmpFatigues")),
    "Shirt": ("uniform", dict(FATIGUES, name="HQ_EmpFatigues")),
    "Trousers": ("uniform", dict(FATIGUES, name="HQ_EmpFatigues")),
    "Headset": ("uniform", dict(KIT, name="HQ_EmpKit")),
    "Gloves": ("uniform", dict(KIT, name="HQ_EmpKit")),
    "Vest": ("uniform", dict(KIT, name="HQ_EmpKit")),
    "Pad": ("uniform", dict(KIT, name="HQ_EmpPad", base=(0.62, 0.86, 0.66), facing=(0.3, 0.75, 0.4))),
    "Boots": ("leather_dyed", {"name": "HQ_EmpBoots", "base": (0.07, 0.065, 0.065), "dyed": (0.07, 0.065, 0.065),
                               "worn_c": (0.26, 0.25, 0.24)}),
    "Machine": ("fieldgun", dict(MACHINE, name="HQ_EmpMachine")),
    "Mast": ("fieldgun", dict(MACHINE, name="HQ_EmpMachine")),
    "Console": ("fieldgun", dict(MACHINE, name="HQ_EmpMachine")),
    "Guard": ("fieldgun", dict(MACHINE, name="HQ_EmpMachine")),
    "Button": ("fieldgun", dict(MACHINE, name="HQ_EmpMachine")),
    "Emitter": ("glow_ball", {"name": "HQ_EmpEmitter", "col": (0.72, 0.9, 1.0), "strength": 1.2}),
    "Charge": ("glow_ball", {"name": "HQ_EmpCharge", "col": (0.3, 0.9, 1.0), "strength": 1.0}),
    "Screen": ("glow_ball", {"name": "HQ_EmpScreen", "col": (0.5, 0.95, 0.62), "strength": 0.8}),
}
GLOW = {"Emitter": ((0.72, 0.9, 1.0), 1.3, 0.6), "Charge": ((0.3, 0.9, 1.0), 1.0, 0.5), "Screen": ((0.5, 0.95, 0.62), 0.8, 0.5)}
LOW_TARGETS = {"Skin": 6000, "Teeth": 60, "Hair": 600, "Cap": 900, "Headset": 1300, "Shirt": 3200, "Trousers": 1500,
               "Boots": 1300, "Gloves": 1300, "Pad": 300, "Vest": 3000, "Machine": 3000, "Mast": 2800, "Emitter": 260,
               "Charge": 120, "Console": 2000, "Screen": 40, "Guard": 260, "Button": 160}
AO_EXCLUDE = ["Pad", "Guard", "Button"]
MACHINE_PARTS = ["Machine", "Mast", "Console", "Guard", "Button"]
# the machine is baked 6 m away from him: his rest pose (his arms out) must leave no shadow on it
BAKE_APART = (MACHINE_PARTS, (6.0, 0.0, 0.0))
YAW_PIVOT = (0.04, 0.0, 0.0)              # the tower turns about this point (keeps the emitter, the case and him on the base)


def prop_bones():
    return []


def extra_bones():
    """machine (the emitter's skid, housing and capacitors, and the control case: deforming nothing of him), mast (the
    mast, the coils and the cage: shudders about its foot at the discharge), emitter (the glowing head: its centre is
    the point the game's EMP rings leave from, bone_point ALONG 0; it swells as the bank charges and flashes at the
    discharge), charge (the capacitors' glowing bars: scaled up their length (bone y) as the bank charges), guard (the
    trigger's safety guard, hinged at its far edge; turns about SW), button (the trigger's cap: squashed along its axis,
    bone y, when he slams it)."""
    return [("machine", MAST_C + Z * 0.02, MAST_C + Z * 0.3, None),
            ("mast", MAST_C + Z * MAST_Z0, MAST_C + Z * (MAST_Z0 + 0.4), "machine"),
            ("emitter", EMIT_C, EMIT_C + Z * 0.2, "mast"),
            ("charge", MAST_C + Z * CHARGE_Z0, MAST_C + Z * CHARGE_Z1, "machine"),
            ("guard", GUARD_HINGE, GUARD_HINGE + SU * 0.08, "machine"),
            ("button", BTN_BASE, BTN_BASE + SN * 0.06, "machine")]


def weight_rules():
    arms = {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Cap": ("rigid", "head"),
        "Headset": ("rigid", "head"),
        "Shirt": ("transfer", TORSO | arms, None),
        "Trousers": ("transfer", {"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Pad": ("rigid", "forearm.L"),
        "Vest": ("transfer", TORSO, None),
        "Machine": ("rigid", "machine"), "Mast": ("rigid", "mast"), "Emitter": ("rigid", "emitter"),
        "Charge": ("rigid", "charge"), "Console": ("rigid", "machine"), "Screen": ("rigid", "machine"),
        "Guard": ("rigid", "guard"), "Button": ("rigid", "button"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Headset") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Machine", "Mast", "Console"):
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Cap", cap_field(), 0.002 if fine else 0.003),
        ("Headset", headset_field(), 0.0018 if fine else 0.0026),
        ("Shirt", shirt_field(), 0.0024 if fine else 0.0034),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0022 if fine else 0.003),
        ("Gloves", gloves_field(), 0.002 if fine else 0.003),
        ("Pad", pad_field(), 0.0016 if fine else 0.0024),
        ("Vest", vest_field(), 0.0024 if fine else 0.0034),
        ("Machine", machine_field(), 0.0026 if fine else 0.0036),
        ("Mast", mast_field(), 0.0026 if fine else 0.0036),
        ("Emitter", emitter_field(), 0.004),
        ("Charge", charge_field(), 0.002),
        ("Console", console_field(), 0.0022 if fine else 0.0032),
        ("Screen", screen_field(), 0.002),
        ("Guard", guard_field(), 0.0016 if fine else 0.0024),
        ("Button", button_field(), 0.0016 if fine else 0.0024),
    ]
