"""The Arc Cannon (HQ tower, The Data Center; Ranged lineage): an improvised lightning gun of the Resistance, built from
salvaged robot tech on a swivel mount, and the veteran gunner who aims it by its twin grips. Rest pose: he stands in an
A-pose facing -Y (the way it shoots), feet at z = 0; the cannon stands on its pedestal before him (its grips half a metre
in front of his belly, its electrode fork a metre and a half out), the tower turns about a point between them (YAW_PIVOT).

Him: the Laser gunner's burly body (torsion.py; the Field Gun's gripping hands) with his own face: a weathered
medium-brown face, a square jaw with a greying stubble, a scar through his right brow and down his cheek, a cocked right
brow and the left drawn a little down, steady dark eyes, a straight nose with a bump, a wry half-smile (the right corner
up); short salt-and-pepper hair cropped close. Black goggles pushed up on his forehead (amber lenses, a worn tan strap round
his head). A smoky teal-grey scarf wound round his neck, knotted at his left, its ends on his chest. Charcoal fatigues
(long sleeves, an amber armband round his right upper arm); a gunmetal plate vest over them (borders and shoulder straps in
charcoal, a field battery pack on his back); a gunmetal pauldron on his right shoulder and forearm guards; on his left
shoulder a salvaged white robot plate strapped on (dented, bolted, a strap across his chest) sprayed with the
Resistance's amber slash. Charcoal trousers with gunmetal thigh plates and knee guards, black boots, black gloves.

The cannon: the Laser Turret's pedestal and turntable fork (`mount`, `yoke`), and in the fork on trunnions the gun (`gun`):
a boxy gunmetal housing welded up from scrap, salvaged white robot plates bolted to its cheeks (amber slashes, held by
black straps), twin grips behind (black rubber on gunmetal arms, an amber thumb bar), a charge readout on its back face;
on its top, in a steel cage on saddles, the exposed power cell (`Cell`, its amber core shipped glowing on the `cell` bone);
the cell's vent hatch in front of it (`vent`, it pops open to dump heat); forward of the housing the stubby barrel: a
stack of brown-glazed insulator rings, a bolted collar, thick cables arching from the housing to the collar, and the
electrode fork: three copper prongs with steel bands curving in round a steel centre electrode, their tips and the
centre's ball glowing amber (`Tip`, shipped glowing on the `tip` bone: its head is the centre ball, the arc's origin, the
bone points the way the arc leaves; the prongs' beads glow with the gun's other amber lights, `Trim`).

Painted labels (material `modern_kit`): 0 the base colour (gunmetal-black armour and housing, charcoal cloth), 5 black,
6 amber paint, 7 robot white, 8 the second colour (charcoal on armour, brown insulator glaze on the gun), 9 gunmetal,
10 bright steel, 11 lens glass, 12 black rubber, 13 hazard (amber-orange on the mount), 14 copper."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp, project_to
from ugo import _blend_add
from torsion import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD,
                     EYE_R, eye_c, smoothstep, hand_frame, HAND_S, fist_center, foot, traps, neck_prim, deltoid,
                     upper_arm, eyes_field, teeth_field, skull, torso_prims, TORSO, TORSO_Z, torso_bones)
from field_gun import hand, palm_pt, legs_hull, boot_hull, _hand_hull, ARM_LEN, tunic_neck
from cannon import capped_cone, poly2d, _arm_coord
from musketeer import _fgrad
from missile import (stencil, shirt_hull, SHIRT_OFF, SHIRT_T, SHIRT_FACE, SHIRT_HEM, PC_IN, PLATE_T, PLATE_OFF,
                     carrier_outer, _surface_frame, _plate_region, BELT_Z)
import laser as _lz
from laser import (Clip, armour_field, trousers_field, boots_field, gloves_field, mount_field, yoke_field,
                   _pauldron_region, _bracer_region, trousers_weights, MY, TRUN, GD, GU, GX_, YOKE_X, TT_Z, FOOT_HALF,
                   GRIP_S, GRIP_U, GRIP_V, gpt, _rgun, g_local, gun_bounds, grip_pt)

IRIS = ((0.17, 0.11, 0.06), (0.36, 0.24, 0.12))           # steady dark-brown eyes (prep.paint_eyes)
SCAR = 10                                                  # skin label: the old scar
GUNBLACK = (0.22, 0.23, 0.25)                              # gunmetal-black armour (the brief)
CHARCOAL = (0.13, 0.13, 0.15)                              # charcoal fatigues (the brief)
TEALGREY = (0.2, 0.27, 0.28)                               # the worn smoky teal-grey scarf (the brief)
BLACK = (0.06, 0.06, 0.07)
GUNMETAL = (0.3, 0.31, 0.34)
AMBER = (1.0, 0.62, 0.15)                                  # the Resistance's one accent (emissive)
AMBER_PAINT = (0.93, 0.58, 0.13)                           # ... as spray paint
ROBOT_WHITE = (0.86, 0.87, 0.88)                           # salvaged robot plates
CERAMIC = (0.46, 0.22, 0.12)                               # brown-glazed insulators
COPPER = (0.78, 0.42, 0.22)
SMOKE_AMBER = (0.2, 0.1, 0.03)                             # the goggles' amber glass
BASE_L, BLACK_L, AMB_L, WHITE_L, ALT_L, GUN_L, STEEL_L, GLASS_L, RUBBER_L, HAZ_L, COP_L = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
Z_ = v3((0.0, 0.0, 1.0))


# ======================================================================================= head
def stubble_mask(P):
    """The greying stubble on his jaw, chin and upper lip, up to short sideburns (design coordinates): <= 0 inside."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.588) + F(0.07) * smoothstep(0.05, 0.14, ax)
    top = np.where(ax > F(0.15), F(1.69), top)                                     # up to the sideburns
    lip = np.where((ax < F(0.05)) & (y < F(-0.15)), F(1.588), F(-1.0))             # the upper lip (under the nose)
    top = np.maximum(top, lip)
    lips = (x / F(0.064)) ** 2 + ((y + F(0.18)) / F(0.05)) ** 2 + ((z - F(1.551)) / F(0.02)) ** 2 - F(1.0)
    back = y - F(0.03)
    return np.maximum(np.maximum(np.maximum(z - top, back), -lips * F(0.03)), F(1.43) - z)


SCAR_PTS = [(-0.074, -0.192, 1.79), (-0.088, -0.186, 1.752), (-0.1, -0.168, 1.7), (-0.112, -0.146, 1.652),
            (-0.118, -0.128, 1.612)]                       # through his right brow, past the eye, down the cheek


def head(fd):
    """A weathered, wry face: a square jaw and a strong chin, high cheekbones, a straight nose with a bump on its
    bridge, the right brow cocked and the left drawn a little down, both eyes open and steady (the left lid a touch
    lower), crow's feet, a half-smile with the right corner up; an old scar through the right brow; ears."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.79), (0.16, 0.17, 0.12)), 0.08, SKIN)                            # the dome (under his hair)
    fd.add(E((0, -0.05, 1.59), (0.138, 0.128, 0.126)), 0.07, SKIN)                        # a square jaw
    fd.add(E((0, -0.142, 1.497), (0.084, 0.068, 0.07)), 0.05, SKIN)                       # a strong chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.118, 1.636), 0.05), 0.05, SKIN)                            # high cheekbones
        fd.add(S((sx * 0.126, -0.045, 1.556), 0.048), 0.05, SKIN)                           # jaw corners
        pts = [hp((sx * 0.152, -0.055, 1.744)), hp((sx * 0.116, -0.132, 1.755)), hp((sx * 0.062, -0.176, 1.754)), hp((0.0, -0.186, 1.75))]
        fd.add(Chain(pts, [hr(0.011), hr(0.02), hr(0.024), hr(0.022)], k=hr(0.02)), hr(0.03), SKIN)     # brow ridge
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.3), STUBBLE)
    # brows: the right one cocked up, the left level and a little low (sceptical); the scar notches the right one
    for sx in (-1, 1):
        if sx < 0:
            pts = [hp((sx * 0.026, -0.213, 1.766)), hp((sx * 0.066, -0.207, 1.789)), hp((sx * 0.11, -0.186, 1.794)), hp((sx * 0.154, -0.144, 1.776))]
        else:
            pts = [hp((sx * 0.026, -0.214, 1.758)), hp((sx * 0.066, -0.209, 1.765)), hp((sx * 0.112, -0.187, 1.768)), hp((sx * 0.155, -0.146, 1.758))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.009), hr(0.012), hr(0.01), hr(0.005)], k=hr(0.008)), hr(0.009), BROW)
        fd.paint(Chain(pts, [hr(0.02), hr(0.022), hr(0.019), hr(0.011)], k=hr(0.01)), BROW)
    sc = [hp(p) for p in SCAR_PTS]
    fd.sub(Chain(sc[:2], [hr(0.006), hr(0.006)], k=hr(0.003)), hr(0.003))                  # the notch in the brow
    for sx in (-1, 1):
        ec = eye_c(sx)
        low = sx > 0                                                                        # the left lid a touch lower
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up_z = hr(0.0195) if low else hr(0.0225)
        lo_z = -hr(0.02) if low else -hr(0.0215)
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, up_z)), (sx * 0.16, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0055)), Plane(ec + v3((0, 0, lo_z)), (sx * -0.1, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, up_z - hr(0.003))), (sx * 0.16, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(2):                                                                  # crow's feet
            a = hp((sx * (0.112 + 0.004 * k), -0.13 + 0.006 * k, 1.672 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, -0.004 - 0.008 * k)), hr(0.0022), hr(0.0015)), hr(0.003))
    # a straight nose with a bump on the bridge (broken once)
    fd.add(RoundCone(hp((0, -0.188, 1.73)), hp((0, -0.23, 1.64)), hr(0.015), hr(0.019)), hr(0.016), SKIN)
    fd.add(S((0.003, -0.214, 1.69), 0.017), hr(0.01), SKIN)
    fd.add(S((0, -0.23, 1.634), 0.02), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.03, -0.216, 1.606), 0.019), hr(0.011), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.015, -0.23, 1.594)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the mouth: a wry half-smile, the right corner up
    slot = [hp((-0.068, -0.16, 1.579)), hp((-0.037, -0.189, 1.559)), hp((0, -0.198, 1.55)), hp((0.034, -0.19, 1.548)), hp((0.06, -0.165, 1.553))]
    fd.sub(Chain(slot, [hr(0.0025), hr(0.0032), hr(0.0034), hr(0.003), hr(0.0024)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0032), hr(0.0045), hr(0.0048), hr(0.0042), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.064, -0.159, 1.582), (-0.034, -0.184, 1.562), (-0.008, -0.19, 1.558), (0.012, -0.189, 1.556), (0.034, -0.183, 1.553), (0.056, -0.164, 1.553)]
    lo_lip = [(-0.048, -0.169, 1.558), (-0.028, -0.185, 1.542), (0, -0.189, 1.537), (0.028, -0.184, 1.537), (0.05, -0.167, 1.542)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0045), hr(0.005), hr(0.005), hr(0.0045), hr(0.003)], k=hr(0.005)), hr(0.006), LIP)
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0065), hr(0.0075), hr(0.0065), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(Sphere(hp((-0.076, -0.156, 1.58)), hr(0.009)), hr(0.008), SKIN)                 # the cheek bunched by the smile
    fd.sub(Sphere(hp((-0.073, -0.165, 1.572)), hr(0.004)), hr(0.004))
    fd.sub(Chain([hp((-0.046, -0.198, 1.6)), hp((-0.064, -0.176, 1.575)), hp((-0.07, -0.161, 1.548))], [hr(0.0025), hr(0.003), hr(0.002)], k=hr(0.003)), hr(0.004))
    # the scar: a pale seam from the brow past the eye's outer corner down the cheek (painted, a faint ridge)
    fd.paint(Chain(sc, [hr(0.0055), hr(0.006), hr(0.0065), hr(0.006), hr(0.0045)], k=hr(0.004)), SCAR)
    fd.add(Chain(sc[2:], [hr(0.0016), hr(0.0018), hr(0.0012)], k=hr(0.002)), hr(0.003), SKIN)
    # ears
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.178, 0.035, 1.664)), v3((0.026, 0.047, 0.06)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.197, 0.028, 1.668)), v3((0.012, 0.03, 0.04)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))


def body_parts(fd):
    """The Laser gunner's burly body (torsion's torso and limbs, the Field Gun's gripping hands) with this head."""
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
        fd.add(RoundCone(el, wr, 0.08, 0.058), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.1, 0.09, 0.135), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028, SKIN)
        hand(fd, side)
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(RoundCone(hip, kn, 0.14, 0.092), 0.065, SKIN)
        fd.add(Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.022, 0)), (0.13, 0.12, 0.19), R=rot_from_axes(z_axis=kn - hip)), 0.048, SKIN)
        fd.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038, SKIN)
        fd.add(RoundCone(kn, an, 0.088, 0.058), 0.038, SKIN)
        fd.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= hair: cropped close
CROWN = v3((0.0, 0.07, 1.87))
# where the hair ends, by the angle round his head (0 = the middle of his brow, pi = the nape): (angle, height)
_HAIRLINE = [(0.0, 1.83), (0.5, 1.826), (0.9, 1.81), (1.1, 1.745), (1.27, 1.69), (1.41, 1.69), (1.51, 1.756),
             (1.84, 1.756), (2.04, 1.64), (math.pi, 1.61)]
_HL_A = np.array([a for a, _ in _HAIRLINE], F)
_HL_Z = np.array([z for _, z in _HAIRLINE], F)


def hair_tex(P):
    """A close crop: fine short strands swept back from the brow, a little tufted."""
    Q = hinv(P)
    phi = np.arctan2(Q[:, 0], -(Q[:, 1] - F(CROWN[1])))
    return (F(0.0004) * np.sin(phi * F(90) + F(2.5) * NOISE(Q * F(18))) + F(0.0012) * NOISE(Q * np.array([140, 140, 90], F))
            + F(0.0009) * NOISE(Q * F(45)))


def hair_shell_out():
    return 0.006 + 0.006            # the hair shell's outer face (Shell(sk, 0.006, 0.012))


def hair_field():
    fd = Field("Hair")
    sk = skull()
    def keep(P):
        Q = hinv(P)
        th = np.abs(np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.02))))
        zl = np.interp(th, _HL_A, _HL_Z).astype(F)
        return zl - Q[:, 2]
    fd.add(Inter(Shell(sk, 0.006, 0.012, pad=0.06, disp=hair_tex, disp_amp=0.003), Func(keep, HEAD_C - 0.4, HEAD_C + 0.35), 0.004), 0.0)
    return fd


def hair_outer():
    sk = skull()
    return Func(lambda P: sk.eval(P, margin=0.1) - F(hair_shell_out()), HEAD_C - 0.4, HEAD_C + 0.4)


# ======================================================================================= the goggles (pushed up)
STRAP_C = hp((0.0, -0.14, 1.9))                # the strap's middle on his brow (design point)
STRAP_N = norm(v3((0.0, 0.42, 1.0)))           # its plane tilts down toward the back of his head


def goggle_frames():
    """(centre on the hair over his brow, outward axis) for each lens: either side of the middle, tipped up."""
    hull = hair_outer()
    out = []
    for sx in (-1, 1):
        o = hp((sx * 0.06, -0.6, 1.9))
        h, ok = ray_hit(hull, [o], [v3((0, 1, 0))], tmax=0.8)
        p = h[0] if ok[0] else hp((sx * 0.06, -0.15, 1.9))
        n = _fgrad(hull.fn, p)
        out.append((p, norm(n + Z_ * 0.35)))
    return out


def goggles_field():
    """Black (5) rubber-framed goggles pushed up over his brow: two round cups with rolled rims (12) and amber lenses
    (11), a bridge between them; the strap (13: worn tan webbing) round his head over the hair."""
    fd = Field("Goggles")
    hull = hair_outer()
    sk = skull()
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    def strap(P):
        Q = hinv(P)
        band = np.abs((Q - STRAP_C.astype(F)) @ STRAP_N.astype(F)) - F(0.016)
        d = sk.eval(P, margin=0.06) - F(hair_shell_out())
        return np.maximum(np.abs(d - F(0.004)) - F(0.0045), band * F(HS))
    fd.add(Func(strap, lo, hi), 0.0, HAZ_L)
    fr = goggle_frames()
    for p, a in fr:
        R = rot_from_axes(z_axis=a)
        fd.add(Cylinder(p + a * 0.006, 0.047, 0.016, rr=0.006, R=R), 0.004, RUBBER_L)            # the gasket
        fd.add(Cylinder(p + a * 0.026, 0.043, 0.03, rr=0.008, R=R), 0.004, BLACK_L)              # the cup
        fd.add(Torus(p + a * 0.042, 0.039, 0.007, R=R), 0.003, RUBBER_L)                          # its rim
        fd.add(Cylinder(p + a * 0.041, 0.035, 0.007, rr=0.002, R=R), 0.002, GLASS_L)              # the lens
    (p0, a0), (p1, a1) = fr
    m = (p0 + p1) / 2 + norm(a0 + a1) * 0.03
    d01 = norm(p1 - p0)
    fd.add(Chain([p0 + a0 * 0.03 + d01 * 0.035, m, p1 + a1 * 0.03 - d01 * 0.035], [0.008, 0.009, 0.008], k=0.004), 0.003, BLACK_L)
    return fd


# ======================================================================================= the fatigues (shirt)
SLEEVE_END = ARM_LEN - 0.03                # (under the gloves' cuffs)
ARMBAND_S = (0.15, 0.23)                   # the amber armband along his right upper arm (from the shoulder)


def _suit_sleeve_cut(P):
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2 = _arm_coord(P, side)
        near = (d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3))
        out = np.maximum(out, np.where(near, s - F(SLEEVE_END), F(-1.0)))
    return out


def suit_keep(P):
    return np.maximum(np.maximum(F(SHIRT_HEM) - P[:, 2], tunic_neck(P) + F(0.012)), _suit_sleeve_cut(P))


def suit_outer():
    b = shirt_hull()
    return Func(lambda P: b.eval(P, margin=0.1) - F(SHIRT_FACE + SHIRT_T / 2), (-1, -0.6, 0.5), (1, 0.6, 1.7))


def suit_field():
    """Charcoal (0) fatigues: tucked in at his waist, long sleeves to his wrists (under the gloves), a seam (5) down each
    sleeve, a pocket on each upper arm (the left under the salvaged plate); the amber (6) armband round his right upper
    arm, a black (5) edge stitched along it."""
    fd = Field("Suit")
    base = shirt_hull()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        return F(0.0016) * np.sin(a * F(7) + F(0.9) * NOISE(P * F(3))) + F(0.0012) * NOISE(P * F(20))
    lo, hi = (-1, -0.6, 0.5), (1, 0.6, 1.7)
    fd.add(Inter(Shell(base, SHIRT_OFF, SHIRT_T, pad=0.12, disp=folds, disp_amp=0.003), Func(suit_keep, lo, hi), 0.004), 0.0)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        def seam(P, side=side, sx=sx):
            s, d2 = _arm_coord(P, side)
            near = (d2 < F(0.17 ** 2)) & (P[:, 0] * F(sx) > F(0.3)) & (P[:, 1] > F(0.05))
            return np.where(near, np.abs(P[:, 1] - F(0.1) - F(0.03) * (s / F(ARM_LEN))) - F(0.004), F(1.0))
        fd.paint(Func(seam, lo, hi), BLACK_L)
    # the amber armband round his right upper arm
    so = suit_outer()
    sh, el = J["shoulder_R"], J["elbow_R"]
    def ab(P):
        s, d2 = _arm_coord(P, "R")
        near = (d2 < F(0.17 ** 2)) & (P[:, 0] < F(-0.3))
        return np.where(near, np.abs(s - F(0.5 * (ARMBAND_S[0] + ARMBAND_S[1]))) - F(0.5 * (ARMBAND_S[1] - ARMBAND_S[0])), F(1.0))
    band = Inter(Func(lambda P: np.abs(so.fn(P) - F(0.008)) - F(0.008), sh - 0.3, el + 0.3), Func(ab, sh - 0.3, el + 0.3), 0.004)
    fd.add(band, 0.004, AMB_L)
    def edge(P):
        s, d2 = _arm_coord(P, "R")
        near = (d2 < F(0.17 ** 2)) & (P[:, 0] < F(-0.3))
        mid = F(0.5 * (ARMBAND_S[0] + ARMBAND_S[1]))
        hw = F(0.5 * (ARMBAND_S[1] - ARMBAND_S[0]))
        return np.where(near, np.abs(np.abs(s - mid) - hw + F(0.008)) - F(0.0035), F(1.0))
    fd.paint(Func(edge, sh - 0.3, el + 0.3), BLACK_L)
    return fd


# ======================================================================================= the scarf
NECK_AX = (v3((0.0, 0.065, 1.34)), v3(hp((0.0, 0.02, 1.575))))
SCARF_OFF, SCARF_T = 0.03, 0.03


def _head_only():
    """His jaw and chin (the scarf keeps clear of them)."""
    hd = Field("JawChin")
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    hd.add(E((0, -0.05, 1.59), (0.138, 0.128, 0.126)), 0.0)
    hd.add(E((0, -0.142, 1.497), (0.084, 0.068, 0.07)), 0.05)
    for sx in (-1, 1):
        hd.add(Sphere(hp((sx * 0.126, -0.045, 1.556)), hr(0.048)), 0.05)
    return hd


_SC = []


def scarf_hull():
    """The surface the scarf is wound on: his shirt's hull and his neck, blended."""
    if _SC:
        return _SC[0]
    sh = shirt_hull()
    nk = Field("ScarfNeck")
    nk.add(neck_prim(), 0.0)
    f = Func(lambda P: smin(sh.eval(P, margin=0.12), nk.eval(P, margin=0.12), 0.05), (-0.45, -0.45, 1.15), (0.45, 0.45, 1.65))
    _SC.append(f)
    return f


def _scarf_region(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.045)))
    rad = np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F(0.045)) ** 2)
    zlo = F(1.335) + F(0.085) * (F(1) - np.cos(a)) * F(0.5) + F(0.008) * np.sin(a * F(5))
    hd = _head_only()
    up = F(0.024) - hd.eval(P, margin=0.1)
    top = P[:, 2] - F(1.53)
    return np.maximum(np.maximum(np.maximum(zlo - P[:, 2], rad - F(0.27)), up), top)


def scarf_knot():
    """The knot: on the cowl's rolled lower edge at the front, to his left, over the vest's collar."""
    sh = scarf_hull()
    co = carrier_outer()
    o, d = v3((0.105, -0.7, 1.36)), v3((0, 1, 0))
    h, ok = ray_hit(Func(lambda P: np.minimum(sh.fn(P) - F(SCARF_OFF + SCARF_T + 0.012), co.fn(P) - F(0.006)), (-0.4, -0.8, 1.1), (0.4, 0.4, 1.6)),
                    [o], [d], tmax=0.8)
    p = h[0]
    n = norm(_fgrad(co.fn, p) + v3((0, 0, 0.3)))
    return p + n * 0.026, n


def scarf_tails():
    """(points, normals) of the scarf's two ends over the vest's front, from the knot down his left chest."""
    k, kn = scarf_knot()
    co = carrier_outer()
    tails = []
    for dx, zs in ((-0.014, (1.3, 1.245, 1.19, 1.14)), (0.036, (1.305, 1.255, 1.205))):
        pts = [(k + v3((dx * 0.6, -0.004, -0.028)), kn)]
        for j, z in enumerate(zs):
            p, n = _surface_frame(co, v3((k[0] + dx + 0.012 * j, -0.8, z)), v3((0, 1, 0)))
            pts.append((p + n * 0.012, n))
        tails.append(pts)
    return tails


def scarf_field():
    """The scarf (smoky teal-grey cloth, 0): wound round his neck in a thick cowl from the vest's collar up to under his
    jaw, deep folds round it, knotted low at his left, the two ends lying on his chest with frayed tips."""
    fd = Field("Scarf")
    sh = scarf_hull()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.045)))
        return (F(0.006) * np.sin(a * F(8) + P[:, 2] * F(30) + F(1.5) * NOISE(P * F(6))) + F(0.002) * NOISE(P * F(30)))
    lo, hi = (-0.4, -0.45, 1.2), (0.4, 0.45, 1.62)
    fd.add(Inter(Func(lambda P: np.abs(sh.fn(P) - F(SCARF_OFF + SCARF_T / 2)) - F(SCARF_T / 2), lo, hi, disp=folds, disp_amp=0.008),
                 Func(_scarf_region, lo, hi), 0.012), 0.0)
    # a thick rolled lower edge
    def roll(P):
        r = _scarf_region(P)
        return np.maximum(np.abs(sh.fn(P) - F(SCARF_OFF + SCARF_T)) - F(0.022), np.abs(r + F(0.006)) - F(0.03))
    def roll_keep(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.045)))
        zlo = F(1.335) + F(0.085) * (F(1) - np.cos(a)) * F(0.5) + F(0.008) * np.sin(a * F(5))
        return np.maximum(P[:, 2] - zlo - F(0.045), _scarf_region(P) - F(0.02))
    fd.add(Inter(Func(roll, lo, hi, disp=folds, disp_amp=0.008), Func(roll_keep, lo, hi), 0.01), 0.014)
    k, kn = scarf_knot()
    cl = lambda P: F(0.003) * NOISE(P * F(20)) + F(0.0015) * NOISE(P * F(55))
    fd.add(Ellipsoid(k, (0.04, 0.03, 0.034), R=rot_from_axes(z_axis=kn, y_axis=(0, 0, 1)), disp=cl, disp_amp=0.004), 0.014)
    rag = lambda P: F(0.002) * NOISE(P * F(26))
    for tail, w0, w1 in zip(scarf_tails(), (0.042, 0.038), (0.052, 0.046)):
        pts = [p for p, n in tail]
        ns = [n for p, n in tail]
        ws = list(np.linspace(w0, w1, len(pts)))
        fd.add(Lock(pts, ws, [0.01] * len(pts), ns, k=0.01, disp=rag, disp_amp=0.002), 0.01)
        e, e0 = pts[-1], pts[-2]
        d = norm(e - e0)
        for j, o in enumerate((-0.6, 0.0, 0.6)):
            Rn = rot_from_axes(z_axis=d, y_axis=ns[-1])
            fd.sub(Ellipsoid(e + d * (0.006 + 0.008 * (j % 2)) + Rn[:, 0] * (o * w1), (0.01, 0.03, 0.022), R=Rn), 0.003)
    return fd


def vest_field():
    """The Laser gunner's plate vest (laser.armour_field: front and back plates, borders, shoulder straps, the abdomen
    band and its pouches, the battery pack on his back) in the Resistance's colours, the amber (6) slash sprayed across
    its front plate below the scarf's ends, on his right."""
    fd = armour_field()
    co = carrier_outer()
    def slash(P):
        a, b = np.array([-0.17, 1.26], F), np.array([-0.04, 1.08], F)
        ab = b - a
        q2 = P[:, [0, 2]]
        t = np.clip(((q2 - a) @ ab) / F(ab @ ab), 0, 1)
        q = q2 - (a + t[:, None] * ab)
        w = F(0.026) + F(0.008) * t + F(0.004) * NOISE(P * F(30))
        return np.maximum(np.sqrt((q * q).sum(1)) - w, np.maximum(P[:, 1] - F(0.0), np.abs(co.fn(P)) - F(0.02)))
    fd.paint(Func(slash, (-0.4, -0.5, 0.9), (0.2, 0.1, 1.4)), AMB_L)
    return fd


# ======================================================================================= the right pauldron, forearm guards
def guards_field():
    """A two-lame gunmetal-black (0) pauldron on his right shoulder with charcoal (8) edges and an amber (6) stripe; forearm
    guards on both arms (gunmetal-black, charcoal edges, scuffed)."""
    fd = Field("Guards")
    base = shirt_hull()
    lo, hi = (-1, -0.6, 0.6), (1, 0.6, 1.7)
    side = "R"
    sh = J["shoulder_R"]
    c = sh + v3((-0.035, 0.0, 0.03))
    fd.add(Clip(Shell(base, PC_IN + 0.016, 0.02, pad=0.14), Func(lambda P: _pauldron_region(P, side, 1), lo, hi), 0.01), 0.004, BASE_L)
    fd.add(Clip(Shell(base, PC_IN + 0.034, 0.022, pad=0.14), Func(lambda P: _pauldron_region(P, side, 0), lo, hi), 0.012), 0.004, BASE_L)
    def edge(P):
        return np.maximum(-(_pauldron_region(P, side, 0) + F(0.014)), _pauldron_region(P, side, 0))
    fd.paint(Func(edge, lo, hi), ALT_L)
    def edge1(P):
        return np.maximum(-(_pauldron_region(P, side, 1) + F(0.012)), _pauldron_region(P, side, 1))
    fd.paint(Func(edge1, lo, hi), ALT_L)
    def stripe(P):
        return np.maximum(np.abs(P[:, 0] - F(c[0] - 0.02)) - F(0.012), F(c[2] + 0.02) - P[:, 2])
    fd.paint(Func(stripe, lo, hi), AMB_L)
    for sd in ("R", "L"):
        sx = -1 if sd == "R" else 1
        fd.add(Clip(Shell(base, SHIRT_FACE + SHIRT_T / 2 + 0.014, 0.02, pad=0.14), Func(lambda P, s=sd: _bracer_region(P, s), lo, hi), 0.008), 0.004, BASE_L)
        def bedge(P, s=sd):
            r = _bracer_region(P, s)
            return np.maximum(-(r + F(0.012)), r)
        fd.paint(Func(bedge, lo, hi), ALT_L)
    return fd


# ======================================================================================= the salvaged robot plate (left shoulder)
SAL_C = J["shoulder_L"] + v3((0.04, 0.0, 0.04))


def _salvage_region(P):
    """< 0 on the plate: a broad cap over his left shoulder (front to back), down his upper arm."""
    d = np.sqrt(((P - SAL_C.astype(F)) ** 2).sum(1))
    z = P[:, 2]
    inner = F(0.2) - P[:, 0]
    return np.maximum(np.maximum(d - F(0.235), F(SAL_C[2] - 0.15) - z), inner)


SAL_IN, SAL_T = PC_IN + 0.03, 0.03


def salvage_outer():
    b = shirt_hull()
    return Func(lambda P: b.eval(P, margin=0.12) - F(SAL_IN + SAL_T / 2), (0.0, -0.5, 1.0), (0.8, 0.5, 1.7))


def salvage_field():
    """A white (7) robot armour plate taken from a machine and strapped over his left shoulder: a thick, hard cap with a
    raised rim, a panel line, two dents and a scorch; bolted on (gunmetal 9 bolts), sprayed with the Resistance's bold
    amber (6) slash across its top; black (5) straps round his upper arm and across his chest to his right side."""
    fd = Field("Salvage")
    base = shirt_hull()
    lo, hi = (0.0, -0.5, 1.0), (0.8, 0.5, 1.7)
    hard = lambda P: F(0.0004) * NOISE(P * F(40))
    fd.add(Clip(Shell(base, SAL_IN, SAL_T, pad=0.16, disp=hard, disp_amp=0.001), Func(_salvage_region, lo, hi), 0.016), 0.0, WHITE_L)
    so = salvage_outer()
    # a raised rim round its edge and a panel line across it
    def rim(P):
        r = _salvage_region(P)
        return np.maximum(r, -(r + F(0.022)))
    fd.add(Inter(Func(lambda P: np.abs(so.fn(P) - F(0.003)) - F(0.006), lo, hi), Func(rim, lo, hi), 0.003), 0.004, WHITE_L)
    def pline(P):
        return np.maximum(np.abs(P[:, 0] - F(SAL_C[0] + 0.07)) - F(0.0035), _salvage_region(P) + F(0.03))
    fd.sub(Inter(Func(lambda P: np.abs(so.fn(P)) - F(0.006), lo, hi), Func(pline, lo, hi), 0.0), 0.002)
    # dents
    for q in ((0.33, -0.08, 1.46), (0.47, 0.1, 1.38)):
        p, n = _surface_frame(so, v3(q) + v3((0, 0, 0.4)), v3((0, 0, -1)))
        fd.sub(Sphere(p + n * 0.016, 0.024), 0.006)
    # the amber slash: a bold diagonal stripe over its top, from the front edge back over the shoulder
    def slash(P):
        a = v3((0.27, -0.16, 0.0))
        b = v3((0.5, 0.18, 0.0))
        ab_ = (b - a)[:2]
        t = np.clip(((P[:, :2] - a[:2].astype(F)) @ ab_.astype(F)) / F(ab_ @ ab_), 0, 1)
        q = P[:, :2] - (a[:2].astype(F) + t[:, None] * ab_.astype(F))
        w = F(0.032) + F(0.012) * t
        return np.maximum(np.sqrt((q * q).sum(1)) - w, F(SAL_C[2] - 0.06) - P[:, 2])
    fd.paint(Func(slash, lo, hi), AMB_L)
    # bolts at its corners
    for q in ((0.26, -0.14, 1.5), (0.26, 0.2, 1.52), (0.52, -0.12, 1.36), (0.53, 0.2, 1.37)):
        h, ok = ray_hit(so, [v3(q) + v3((0.3, 0, 0.3))], [norm(v3((-0.5, 0, -0.6)))], tmax=0.8)
        if ok[0]:
            p = h[0]
            n = _fgrad(so.fn, p)
            fd.add(Cylinder(p + n * 0.003, 0.013, 0.01, rr=0.003, R=rot_from_axes(z_axis=n)), 0.002, GUN_L)
    # the straps: round his upper arm below the plate, and from the plate's front across his chest to his right side
    sh, el = J["shoulder_L"], J["elbow_L"]
    uo = suit_outer()
    def arm_band(P):
        s, d2 = _arm_coord(P, "L")
        near = (d2 < F(0.17 ** 2)) & (P[:, 0] > F(0.3))
        return np.where(near, np.abs(s - F(0.2)) - F(0.016), F(1.0))
    fd.add(Inter(Func(lambda P: np.abs(uo.fn(P) - F(0.006)) - F(0.006), sh - 0.3, el + 0.3), Func(arm_band, sh - 0.3, el + 0.3), 0.003), 0.004, BLACK_L)
    co = carrier_outer()
    pts, ns = [], []
    for x, z in ((0.25, 1.33), (0.16, 1.27), (0.06, 1.2), (-0.05, 1.13), (-0.15, 1.07), (-0.22, 1.03)):
        p, n = _surface_frame(co, v3((x, -0.8, z)), v3((0, 1, 0)))
        pts.append(p + n * 0.006)
        ns.append(n)
    fd.add(Lock(pts, [0.028] * len(pts), [0.006] * len(pts), ns, k=0.006), 0.004, BLACK_L)
    fd.add(RoundBox(pts[2] + ns[2] * 0.008, (0.03, 0.022, 0.006), 0.004, R=rot_from_axes(z_axis=ns[2], y_axis=norm(pts[1] - pts[3]))), 0.003, STEEL_L)
    return fd


# ======================================================================================= the cannon (layout; the gun frame is the laser's)
HB = (-0.30, 0.14)               # the housing's back and front (s along the gun from the trunnions)
HW, HV = 0.15, (-0.115, 0.115)   # its half width, its bottom and top (v)
CELL_S = (-0.255, 0.035)         # the power cell along the housing's top (its caps' outer faces)
CELL_V = HV[1] + 0.078           # its axis (v)
CELL_R = 0.062                   # its cage's radius
CORE_R = 0.046                   # the glowing core's radius
VENT_S = (0.06, 0.132)           # the vent hatch (s), on the housing's top in front of the cell
VENT_W = 0.07
HINGE_S = VENT_S[1] + 0.006      # its hinge, along its front edge
BAR_S = (0.12, 0.47)             # the stubby barrel
BAR_R = 0.072
INS_S = [0.19, 0.236, 0.282, 0.328, 0.374]        # the insulator rings
INS_R = 0.118
COLLAR_S = (0.405, 0.465)        # the bolted collar
PRONG_A = [math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3]
PRONG_PATH = [(0.44, 0.074), (0.53, 0.112), (0.63, 0.118), (0.71, 0.1), (0.765, 0.074)]    # (s, r) along each prong
PRONG_R = 0.017
TIP_S = 0.79                     # the centre electrode's glowing ball (the arc's origin)
TIP_R = 0.036


def hinge_pt():
    return gpt(HINGE_S, 0.0, HV[1] + 0.008)


def tip_c():
    return gpt(TIP_S)


def cell_c():
    return gpt(0.5 * (CELL_S[0] + CELL_S[1]), 0.0, CELL_V)


def cell_pt(ds=0.0, du=0.0, dv=0.0):
    return gpt(0.5 * (CELL_S[0] + CELL_S[1]) + ds, du, CELL_V + dv)


def prong_pts(a):
    d = GX_ * math.cos(a) + GU * math.sin(a)
    return [gpt(s) + d * r for s, r in PRONG_PATH], d


def _housing_sd(P):
    u, s, v = g_local(P)
    k = np.clip((s - F(0.0)) / F(HB[1]), 0, 1)
    w = F(HW) - F(0.02) * k
    vt, vb = F(HV[1]), F(HV[0]) + F(0.02) * k
    vc, vh = (vt + vb) * F(0.5), (vt - vb) * F(0.5)
    r = F(0.03)
    qx = np.abs(u) - w + r
    qy = np.abs(s - F((HB[0] + HB[1]) / 2)) - F((HB[1] - HB[0]) / 2) + r
    qz = np.abs(v - vc) - vh + r
    qq = np.stack([qx, qy, qz], 1)
    return np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0) - r


def weld(fd, pts, r=0.008, n=None):
    """A weld bead along a polyline: a row of small overlapping lumps (gunmetal)."""
    P = [v3(p) for p in pts]
    out = []
    for a, b in zip(P[:-1], P[1:]):
        L = float(np.linalg.norm(b - a))
        m = max(2, int(L / (r * 1.1)))
        for j in range(m):
            out.append(a + (b - a) * (j / float(m)))
    out.append(P[-1])
    fd.add(Chain(out, [r] * len(out), k=r * 0.5, disp=lambda Q: F(0.0015) * NOISE(Q * F(160)), disp_amp=0.002), 0.003, GUN_L)


def gun_field():
    """The gun: the housing (gunmetal-black 0, welded seams 9), white (7) salvaged plates on its cheeks with amber (6)
    slashes, held by black (5) straps with steel buckles; the twin grips (black rubber 12 on gunmetal arms) and the amber
    thumb bar; the charge readout's frame on the back face; the trunnion hubs; the vent's recess; the power cell's cage
    (gunmetal end caps, steel bars, saddles, black straps) and its cables (12); the barrel (gunmetal), the insulator rings
    (brown glaze 8), the bolted collar, the cables arching to it, the copper (14) prongs with steel (10) bands and tips,
    the steel centre electrode."""
    fd = Field("Gun")
    R = _rgun()
    fd.add(Func(_housing_sd, *gun_bounds(HB[0] - 0.05, HB[1] + 0.05, 0.2)), 0.0, BASE_L)
    # welded seams along the housing's top and bottom edges, and round its front
    for su in (-1, 1):
        weld(fd, [gpt(HB[0] + 0.03, su * (HW - 0.012), HV[1] - 0.008), gpt(HB[1] - 0.04, su * (HW - 0.03), HV[1] - 0.008)], 0.007)
        weld(fd, [gpt(HB[0] + 0.03, su * (HW - 0.012), HV[0] + 0.01), gpt(HB[1] - 0.03, su * (HW - 0.03), HV[0] + 0.03)], 0.007)
    # the salvaged white plates on its cheeks: curved, a raised rim, an amber slash, a dent; held by two straps
    for su in (-1, 1):
        Rp = np.stack([GD, GU, GX_ * su], axis=1)
        c = gpt(-0.075, su * (HW + 0.012), 0.0)
        plate = Inter(Ellipsoid(c - GX_ * (su * 0.3), (0.2, 0.105, 0.32), R=Rp), Plane(c - GX_ * (su * 0.008), -GX_ * su), 0.006)
        fd.add(plate, 0.006, WHITE_L)
        def sl(P, su=su, c=c):
            q = (P - c.astype(F)) @ Rp.astype(F)
            d = np.abs(q[:, 0] * F(0.5) + q[:, 1] * F(0.86)) - F(0.022)
            return np.maximum(d, np.abs(q[:, 0]) - F(0.15))
        fd.paint(Func(sl, c - 0.3, c + 0.3), AMB_L)
        fd.sub(Sphere(c + GX_ * (su * 0.03) + GD * 0.09 + GU * -0.05, 0.026), 0.006)          # a dent
        for k in range(4):
            sb = c + GD * (-0.15 + 0.1 * k) + GU * (0.075 if k % 2 else -0.075) + GX_ * (su * 0.012)
            fd.add(Cylinder(sb, 0.01, 0.012, rr=0.003, R=rot_from_axes(z_axis=GX_)), 0.002, GUN_L)
        stencil(fd, "ARC-1", gpt(-0.12, su * (HW + 0.03), -0.055), GD * (-su), GU, 0.022, BLACK_L, depth=0.008)
    for s0 in (-0.2, 0.03):                                                       # the straps round housing and plates
        def strap(P, s0=s0):
            u, s, v = g_local(P)
            return np.maximum(np.abs(s - F(s0)) - F(0.016), np.abs(_housing_sd(P) - F(0.03)) - F(0.006))
        fd.add(Func(strap, *gun_bounds(s0 - 0.05, s0 + 0.05, 0.25)), 0.003, BLACK_L)
        fd.add(RoundBox(gpt(s0, -0.06, HV[0] - 0.034), (0.022, 0.026, 0.008), 0.004, R=R), 0.003, STEEL_L)
    # the vent's recess in front of the cell (the hatch closes over it) and its louvres
    vc = gpt(0.5 * (VENT_S[0] + VENT_S[1]), 0.0, HV[1])
    fd.sub(RoundBox(vc, (VENT_W - 0.006, 0.5 * (VENT_S[1] - VENT_S[0]) - 0.006, 0.026), 0.008, R=R), 0.004)
    for k in range(3):
        fd.add(RoundBox(gpt(VENT_S[0] + 0.018 + 0.02 * k, 0.0, HV[1] - 0.03), (VENT_W - 0.01, 0.004, 0.012), 0.002,
                        R=R @ euler(0.6, 0, 0)), 0.002, BLACK_L)
    # the charge readout's frame on the back face (its bars glow: Trim)
    fd.sub(RoundBox(gpt(HB[0], 0.0, 0.02), (0.07, 0.008, 0.032), 0.006, R=R), 0.003)
    # the trunnion hubs
    for su in (-1, 1):
        fd.add(Cylinder(TRUN + GX_ * (su * (HW + 0.03)), 0.052, 0.03, rr=0.008, R=rot_from_axes(z_axis=GX_)), 0.006, GUN_L)
    # the twin grips: gunmetal arms welded to the housing's back corners, black rubber handles, the amber thumb bar
    for su in (-1, 1):
        a = gpt(HB[0] + 0.05, su * (HW - 0.02), -0.03)
        b = gpt(HB[0] - 0.05, su * (GRIP_U - 0.015), -0.04)
        fd.add(Chain([a, b, gpt(GRIP_S + 0.015, su * GRIP_U, -0.04)], [0.02, 0.018, 0.018], k=0.01), 0.008, GUN_L)
        weld(fd, [a + GD * 0.02 + GU * 0.02, a + GD * 0.02 - GU * 0.02], 0.007)
        fd.add(RoundCone(grip_pt(su, 0.0), grip_pt(su, 1.0), 0.021, 0.021), 0.006, RUBBER_L)
        for t in (0.2, 0.4, 0.6, 0.8):
            fd.add(Torus(grip_pt(su, t) + GD * 0.004, 0.02, 0.004, R=rot_from_axes(z_axis=GU)), 0.003, RUBBER_L)
        fd.add(Cylinder(grip_pt(su, 0.0) - GU * 0.008, 0.026, 0.016, rr=0.006, R=rot_from_axes(z_axis=GU)), 0.003, GUN_L)
        fd.add(Cylinder(grip_pt(su, 1.0) + GU * 0.01, 0.024, 0.016, rr=0.006, R=rot_from_axes(z_axis=GU)), 0.003, GUN_L)
    bar = [grip_pt(-1, 1.0) + GU * 0.01 - GD * 0.012 + GX_ * 0.03, gpt(GRIP_S - 0.01, -0.08, GRIP_V[1] + 0.02),
           gpt(GRIP_S - 0.01, 0.08, GRIP_V[1] + 0.02), grip_pt(1, 1.0) + GU * 0.01 - GD * 0.012 - GX_ * 0.03]
    fd.add(Chain(bar, [0.009] * 4, k=0.004), 0.003, AMB_L)
    # the power cell's cage on the housing's top: saddles, gunmetal end caps, six steel bars, two black straps
    A = GD
    cc = cell_c()
    L = CELL_S[1] - CELL_S[0]
    for ss in (-1, 1):
        cap = cc + A * (ss * (L / 2 - 0.016))
        fd.add(Cylinder(cap, CELL_R + 0.008, 0.032, rr=0.008, R=rot_from_axes(z_axis=A)), 0.004, GUN_L)
        fd.add(Cylinder(cap + A * (ss * 0.022), 0.032, 0.014, rr=0.004, R=rot_from_axes(z_axis=A)), 0.003, STEEL_L)     # terminal
        fd.add(RoundBox(cell_pt(ss * (L / 2 - 0.05), 0.0, -0.05), (0.05, 0.016, 0.022), 0.006, R=R), 0.004, GUN_L)      # saddle
    for k in range(6):
        a = 2 * math.pi * k / 6 + math.pi / 6
        d = GX_ * math.cos(a) + GU * math.sin(a)
        fd.add(RoundCone(cc - A * (L / 2 - 0.03) + d * (CELL_R - 0.004), cc + A * (L / 2 - 0.03) + d * (CELL_R - 0.004), 0.007, 0.007), 0.003, STEEL_L)
    for ds in (-0.06, 0.06):
        fd.add(Torus(cc + A * ds, CELL_R + 0.004, 0.009, R=rot_from_axes(z_axis=A)), 0.003, BLACK_L)
    # cables: from the cell's back terminal down into the housing's back; from the housing's front, arching past the
    # insulators to the collar
    p0 = cc - A * (L / 2 + 0.03)
    fd.add(Chain([p0, p0 - A * 0.035 - GU * 0.02, gpt(HB[0] - 0.02, 0.06, 0.07), gpt(HB[0] + 0.01, 0.07, 0.03)], [0.014] * 4, k=0.015), 0.004, RUBBER_L)
    for su in (-1, 1):
        pts = [gpt(HB[1] - 0.03, su * 0.1, 0.07), gpt(0.2, su * 0.15, 0.08), gpt(0.33, su * 0.152, 0.07), gpt(0.43, su * 0.105, 0.05)]
        fd.add(Chain(pts, [0.017, 0.017, 0.017, 0.015], k=0.02), 0.005, RUBBER_L)
        fd.add(Cylinder(pts[0] - GD * 0.012, 0.022, 0.03, rr=0.005, R=rot_from_axes(z_axis=norm(pts[1] - pts[0]))), 0.003, GUN_L)
    # the barrel, the insulator rings, the bolted collar
    fd.add(Cylinder(gpt(0.5 * (BAR_S[0] + BAR_S[1])), BAR_R, BAR_S[1] - BAR_S[0], rr=0.01, R=rot_from_axes(z_axis=GD)), 0.012, GUN_L)
    fd.add(Cylinder(gpt(BAR_S[0] + 0.02), 0.095, 0.04, rr=0.01, R=rot_from_axes(z_axis=GD)), 0.006, GUN_L)
    weld(fd, [gpt(BAR_S[0] + 0.0, 0.0, 0.095)] + [gpt(BAR_S[0], 0.095 * math.sin(a), 0.095 * math.cos(a)) for a in np.linspace(0.3, 6.0, 12)], 0.007)
    fd.add(Cylinder(gpt(0.5 * (INS_S[0] + INS_S[-1])), 0.085, INS_S[-1] - INS_S[0] + 0.03, rr=0.01, R=rot_from_axes(z_axis=GD)), 0.006, ALT_L)
    for k, s0 in enumerate(INS_S):
        r = INS_R if k % 2 == 0 else INS_R - 0.016
        fd.add(Cylinder(gpt(s0), r, 0.024, rr=0.011, R=rot_from_axes(z_axis=GD)), 0.008, ALT_L)
    fd.add(Cylinder(gpt(0.5 * (COLLAR_S[0] + COLLAR_S[1])), 0.104, COLLAR_S[1] - COLLAR_S[0], rr=0.01, R=rot_from_axes(z_axis=GD)), 0.006, GUN_L)
    for k in range(8):
        a = 2 * math.pi * k / 8
        fd.add(Sphere(gpt(COLLAR_S[0] + 0.012, 0.09 * math.cos(a), 0.09 * math.sin(a)) - GD * 0.004, 0.009), 0.002, STEEL_L)
    # the electrode fork: three copper prongs (steel bands, steel tips) curving in round the steel centre electrode
    for a in PRONG_A:
        pts, d = prong_pts(a)
        fd.add(Chain(pts, [PRONG_R + 0.004, PRONG_R, PRONG_R, PRONG_R - 0.002, PRONG_R - 0.003], k=0.01), 0.006, COP_L)
        fd.add(RoundBox(gpt(COLLAR_S[1] - 0.004) + d * 0.078, (0.03, 0.026, 0.02), 0.008, R=rot_from_axes(z_axis=GD, y_axis=np.cross(GD, d))), 0.004, GUN_L)
        for j in (1, 3):
            ax = norm(pts[j + 1] - pts[j - 1])
            fd.add(Torus(pts[j], PRONG_R + 0.003, 0.005, R=rot_from_axes(z_axis=ax)), 0.002, STEEL_L)
        e = pts[-1] + norm(pts[-1] - pts[-2]) * 0.008
        fd.add(Sphere(e, 0.02), 0.006, STEEL_L)
    fd.add(RoundCone(gpt(COLLAR_S[1] - 0.01), gpt(TIP_S - 0.03), 0.03, 0.018), 0.006, STEEL_L)
    for k in range(5):                                                                 # copper windings on its root
        fd.add(Torus(gpt(0.49 + 0.016 * k), 0.03 - 0.0015 * k, 0.006, R=rot_from_axes(z_axis=GD)), 0.002, COP_L)
    fd.add(Cylinder(gpt(TIP_S - 0.034), 0.026, 0.014, rr=0.004, R=rot_from_axes(z_axis=GD)), 0.003, STEEL_L)       # the ball's seat
    return fd


def vent_field():
    """The vent hatch (rest: closed over its recess on the housing's top, in front of the cell): a gunmetal-black (0) plate
    with louvre ridges (5), its hinge knuckle along its front edge (gunmetal 9), a grip lip at its back painted amber (6)."""
    fd = Field("Vent")
    R = _rgun()
    c = gpt(0.5 * (VENT_S[0] + VENT_S[1]), 0.0, HV[1] + 0.004)
    hl = 0.5 * (VENT_S[1] - VENT_S[0])
    fd.add(RoundBox(c, (VENT_W, hl, 0.008), 0.006, R=R), 0.0, BASE_L)
    for k in range(3):
        fd.add(RoundBox(gpt(VENT_S[0] + 0.016 + 0.02 * k, 0.0, HV[1] + 0.012), (VENT_W - 0.014, 0.005, 0.005), 0.003, R=R), 0.003, BLACK_L)
    fd.add(Cylinder(hinge_pt(), 0.009, 2 * VENT_W - 0.02, rr=0.003, R=rot_from_axes(z_axis=GX_)), 0.003, GUN_L)
    fd.add(RoundBox(gpt(VENT_S[0] - 0.002, 0.0, HV[1] + 0.012), (0.03, 0.006, 0.006), 0.003, R=R), 0.003, AMB_L)
    return fd


def cell_field():
    """The power cell's core (shipped glowing amber): a fat cylinder inside the cage, banded."""
    fd = Field("Cell")
    cc = cell_c()
    L = CELL_S[1] - CELL_S[0]
    fd.add(Cylinder(cc, CORE_R, L - 0.05, rr=0.012, R=rot_from_axes(z_axis=GD)), 0.0)
    return fd


def tip_field():
    """The centre electrode's glowing ball (shipped glowing amber, on the `tip` bone: the arc's origin)."""
    fd = Field("Tip")
    fd.add(Sphere(tip_c(), TIP_R), 0.0)
    return fd


def trim_field():
    """The gun's other amber lights (shipped glowing): a bead on each prong's tip, the charge readout's bars on the back
    face, a bar in the vent's recess (seen when it opens)."""
    fd = Field("Trim")
    R = _rgun()
    for a in PRONG_A:
        pts, d = prong_pts(a)
        e = pts[-1] + norm(pts[-1] - pts[-2]) * 0.022
        fd.add(Sphere(e, 0.013), 0.0)
    for k in range(4):
        fd.add(RoundBox(gpt(HB[0] + 0.002, -0.045 + 0.03 * k, 0.02), (0.011, 0.004, 0.022 - 0.004 * abs(k - 1.5)), 0.002, R=R), 0.0)
    fd.add(RoundBox(gpt(0.5 * (VENT_S[0] + VENT_S[1]), 0.0, HV[1] - 0.022), (VENT_W - 0.02, 0.03, 0.004), 0.003, R=R), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.614)), 0.045, 0.4)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.104, -0.14, 1.636)), 0.05, 0.3), (hp((sx * 0.05, -0.18, 1.77)), 0.06, 0.15)]
    return pts


# ======================================================================================= build config
GLB_NAME = "arc_cannon"
ROOT_NAME = "ArcCannonHQ"
TEX_PREFIX = "arc_cannon"
MAT_NAME = "ArcCannonMat"
MESH_NAME = "ArcCannon"
BASE_MODULE = "arc_cannon_base"
ANIM_MODULE = "anim_arc_cannon"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Goggles", "Scarf", "Suit", "Armour", "Guards", "Salvage", "Trousers", "Boots",
         "Gloves", "Mount", "Yoke", "Gun", "Vent", "Cell", "Tip", "Trim"]
REGION_PARTS = ("Skin", "Goggles", "Suit", "Armour", "Guards", "Salvage", "Trousers", "Boots", "Gloves", "Mount", "Yoke",
                "Gun", "Vent")
KIT = dict(weave=0.0, black=BLACK, red=AMBER_PAINT, white=ROBOT_WHITE, gunmetal=GUNMETAL, glass=SMOKE_AMBER,
           glass_hi=(0.95, 0.6, 0.2), rubber=(0.07, 0.07, 0.075), coyote=AMBER_PAINT, brass=COPPER)
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_ArcSkin", "base": (0.55, 0.37, 0.26), "ruddy": (0.6, 0.33, 0.24), "lips": (0.45, 0.27, 0.22),
                      "brow": ((0.07, 0.06, 0.055), (0.2, 0.18, 0.17)),
                      "extra": ((LASH, (0.04, 0.03, 0.025), 0.5), (STUBBLE, (0.34, 0.3, 0.28), 0.62, 0.55),
                                (SCAR, (0.72, 0.52, 0.44), 0.45, 0.8))}),
    "Hair": ("hair", {"name": "HQ_ArcHair", "base": (0.09, 0.08, 0.075), "hi": (0.3, 0.28, 0.27), "low": (0.04, 0.035, 0.03),
                      "streak": (0.07, 0.065, 0.06), "tint": (0.14, 0.13, 0.12), "fleck": (0.6, 0.58, 0.56), "fleck_amt": 0.55}),
    "Goggles": ("modern_kit", dict(KIT, name="HQ_ArcGoggles", base=BLACK, gloss=0.5, coyote=(0.42, 0.34, 0.24),
                                   glass=(0.5, 0.27, 0.05), glass_hi=(1.0, 0.75, 0.35))),
    "Scarf": ("cloth", {"name": "HQ_ArcScarf", "col": TEALGREY}),
    "Suit": ("modern_kit", dict(KIT, name="HQ_ArcSuit", base=CHARCOAL, weave=1.0, black=(0.05, 0.05, 0.055))),
    "Armour": ("modern_kit", dict(KIT, name="HQ_ArcArmour", base=GUNBLACK, olive=CHARCOAL, gloss=0.62)),
    "Guards": ("modern_kit", dict(KIT, name="HQ_ArcArmour", base=GUNBLACK, olive=CHARCOAL, gloss=0.62)),
    "Salvage": ("modern_kit", dict(KIT, name="HQ_ArcSalvage", base=ROBOT_WHITE, gloss=0.42)),
    "Trousers": ("modern_kit", dict(KIT, name="HQ_ArcTrousers", base=CHARCOAL, weave=1.0, olive=GUNBLACK)),
    "Boots": ("leather_dyed", {"name": "HQ_ArcBoots", "base": (0.07, 0.068, 0.075), "dyed": (0.14, 0.15, 0.17), "worn_c": (0.3, 0.3, 0.33)}),
    "Gloves": ("leather_dyed", {"name": "HQ_ArcGloves", "base": (0.075, 0.075, 0.082), "dyed": GUNBLACK, "worn_c": (0.3, 0.3, 0.33)}),
    "Mount": ("modern_kit", dict(KIT, name="HQ_ArcMount", base=GUNBLACK, olive=CHARCOAL, gloss=0.5)),
    "Yoke": ("modern_kit", dict(KIT, name="HQ_ArcMount", base=GUNBLACK, olive=CHARCOAL, gloss=0.5)),
    "Gun": ("modern_kit", dict(KIT, name="HQ_ArcGun", base=GUNBLACK, olive=CERAMIC, gloss=0.5)),
    "Vent": ("modern_kit", dict(KIT, name="HQ_ArcGun", base=GUNBLACK, olive=CERAMIC, gloss=0.5)),
}
GLOW = {"Tip": ((1.0, 0.7, 0.25), 1.4, 0.55), "Cell": (AMBER, 1.2, 0.5), "Trim": (AMBER, 1.0, 0.5)}
LOW_TARGETS = {"Skin": 4800, "Eyes": 300, "Teeth": 60, "Hair": 700, "Goggles": 700, "Scarf": 1100, "Suit": 2300,
               "Armour": 2900, "Guards": 1000, "Salvage": 1100, "Trousers": 2000, "Boots": 1100, "Gloves": 900,
               "Mount": 1300, "Yoke": 1000, "Gun": 3900, "Vent": 220, "Cell": 160, "Tip": 160, "Trim": 260}
AO_EXCLUDE = ["Goggles", "Vent"]
MACHINE_PARTS = ["Mount", "Yoke", "Gun", "Vent"]
# the cannon is baked 6 m away from him (his rest pose stands close behind its grips)
BAKE_APART = (MACHINE_PARTS, (6.0, 0.0, 0.0))
YAW_PIVOT = (0.0, -0.6, 0.0)                # the tower turns about this point (between him and the pedestal)


def prop_bones():
    return []                                # everything he handles is the cannon's (extra_bones)


def extra_bones():
    """The cannon's bones (none of them deform him): mount (the pedestal), yoke (the turntable and fork: it traverses
    about the column; child of the mount), gun (elevating about the trunnions; child of the yoke), vent (the hatch, on its
    hinge; child of the gun), cell (the glowing core: it swells at the shot and pulses as it vents), tip (child of the
    gun: its head is the centre electrode's ball, the arc's origin; the bone points the way the arc leaves; it flares
    (scales) at the shot)."""
    T, C, H = tip_c(), cell_c(), hinge_pt()
    return [
        ("mount", v3((0.0, MY, 0.0)), v3((0.0, MY, 0.3)), None),
        ("yoke", v3((0.0, MY, TT_Z)), v3((0.0, MY, TT_Z + 0.2)), "mount"),
        ("gun", TRUN, TRUN + GD * 0.3, "yoke"),
        ("vent", H, H + GX_ * 0.1, "gun"),
        ("cell", C, C + GD * 0.1, "gun"),
        ("tip", T, T + GD * 0.1, "gun"),
    ]


def weight_rules():
    body = TORSO | {"clavicle.R", "clavicle.L"}
    arms = {"upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Goggles": ("rigid", "head"),
        "Scarf": ("transfer", {"neck", "chest", "spine", "clavicle.R", "clavicle.L"}, None),
        "Suit": ("transfer", body | arms, None),
        "Armour": ("transfer", body, None),
        "Guards": ("transfer", body | arms, None),
        "Salvage": ("transfer", body | arms, None),
        "Trousers": ("custom", trousers_weights),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Mount": ("rigid", "mount"), "Yoke": ("rigid", "yoke"), "Gun": ("rigid", "gun"), "Vent": ("rigid", "vent"),
        "Cell": ("rigid", "cell"), "Tip": ("rigid", "tip"), "Trim": ("rigid", "gun"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part == "Skin" and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Goggles", "Salvage"):
        return 1.15
    if part in ("Mount", "Yoke"):
        return 0.75
    if part in ("Gun",):
        return 0.95
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0022 if fine else 0.003),
        ("Goggles", goggles_field(), 0.0018 if fine else 0.0026),
        ("Scarf", scarf_field(), 0.0026 if fine else 0.0036),
        ("Suit", suit_field(), 0.0026 if fine else 0.0036),
        ("Armour", vest_field(), 0.0026 if fine else 0.0036),
        ("Guards", guards_field(), 0.0024 if fine else 0.0034),
        ("Salvage", salvage_field(), 0.0024 if fine else 0.0034),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Gloves", gloves_field(), 0.0018 if fine else 0.0026),
        ("Mount", mount_field(), 0.0026 if fine else 0.0036),
        ("Yoke", yoke_field(), 0.0024 if fine else 0.0034),
        ("Gun", gun_field(), 0.0022 if fine else 0.0032),
        ("Vent", vent_field(), 0.0016 if fine else 0.0022),
        ("Cell", cell_field(), 0.0018 if fine else 0.0024),
        ("Tip", tip_field(), 0.0014 if fine else 0.002),
        ("Trim", trim_field(), 0.0012 if fine else 0.0016),
    ]
