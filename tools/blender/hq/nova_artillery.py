"""The Nova Artillery (HQ tower, The Data Center; Siege lineage): a heavy field howitzer of the Resistance, built from
salvage, and the old artillerist who serves it. Rest pose: he stands in an A-pose facing -Y (the way it shoots), feet at
z = 0; the howitzer stands on his left (+X), its long barrel laid toward -Y and a little up, its breech level with his
belt; on his right his ready rack of glowing shells. The gun is loaded, its breech closed.

Him: the Missile Launcher's sturdy body (missile.py, torsion.py, field_gun.py's gripping hands) with his own face: an
older man, weathered and leathery, a square jaw under a short grey beard joined to a heavy grey moustache, deep-set
hazel eyes under bushy grey brows (crow's feet, bags under them), a broad nose with a broken bridge, a pale scar across
his left cheek, a firm mouth under the moustache; grey hair cropped short at his temples and nape, his ears showing. A
smoky teal-grey bandana tied over his head (a rolled front edge, a knot and two tails at the back); his goggles pushed up
on it (black rubber cups, gunmetal rims, amber lenses, a rubber strap round the bandana). A charcoal fatigue shirt, its
sleeves rolled up to mid-forearm, a stand collar, an amber armband round his left upper arm; over it his chest guard: a
white robot breast plate taken from the enemy (panel lines, dents and scrapes down to the metal, gunmetal bolts) with the
Resistance's bold amber chevron sprayed across it, strapped on with black webbing (shoulder straps, a cummerbund, a
webbing panel on his back); charcoal trousers with cargo pockets and knee pads, a black belt, black boots and gloves.

The howitzer (material `modern_kit`): the carriage: a round firing platform on the floor (four jack pads) under a short
column and a turntable, a saddle of two side plates carrying the trunnions, a box trail back to a spade braced in the
floor and two front legs splayed out to pads on the floor (amber bands near their ends, weld beads, rivets); the firing grip on the near side plate (a black
T-grip, an amber trigger guard). The cradle (on the carriage): the recoil sled the barrel slides on (a bed with side
rails, a collar at its front), two recoil cylinders above the barrel, the trunnion block. The barrel (it slides back at
the shot): a square breech ring with the slot of a sliding block and the chamber's mouth, a salvaged robot power cell
strapped on the ring's top (its amber window glows), a jacket wrapped in four copper coil collars, each with a glowing
amber band sunk in a groove round its middle (`Coils`: their own emissive mesh, scaled in across the bore to go dark),
cables from the cell into the coils, a long thick tube, a heavy muzzle brake with two ports a side and the glowing bore
deep in it (`BarrelGlow`, with the cell's window). The sliding breech block (bright steel) and the breech lever with an
amber knob. The shield: a salvaged white robot panel, curved, with panel lines, dents and bullet scars, the amber
Resistance chevron sprayed on it, a notch for the barrel, bolted to the saddle on gunmetal brackets. The shell (its own
bone): a gunmetal case with a rim and an amber stripe, the projectile a dark steel cage of four ribs and two rings round
a glowing amber core (`ShellGlow`), a steel nose. The spent case (its own bone). The ready rack (on the `props` bone): an
open steel cradle on a salvaged crate, two shells lying in it noses to the back (cores glowing: `RackGlow`), the third
cradle his.

Painted labels (modern_kit): 0 the part's base colour, 5 black (webbing, polymer), 6 amber paint, 7 robot white,
8 teal-grey cloth, 9 gunmetal, 10 bright steel, 11 glass, 12 black rubber, 13 hazard orange, 14 brass/copper.
On his clothes (material `uniform`): 0 charcoal cloth, 5 amber (the armband), 6 steel, 7 black (belt, knee pads)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp, project_to
from ugo import _blend_add
import missile as mm
from missile import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD,
                     EYE_R, eye_c, smoothstep, hand_frame, HAND_S, fist_center, foot, traps, neck_prim, deltoid,
                     upper_arm, eyes_field, skull, torso_prims, TORSO, TORSO_Z, torso_bones, hand, palm_pt, ARM_LEN,
                     tunic_neck, _arm_coord, layer, _fgrad, capped_cone, poly2d, stencil, JAW, CHIN, cheekbone,
                     jaw_corner, shirt_hull, SHIRT_OFF, SHIRT_T, SHIRT_FACE, SHIRT_HEM, ROLL_S, shirt_keep, _roll_band,
                     upper_arm_spot, PC_IN, PLATE_T, PLATE_OFF, CB_T, CB_OFF, STRAP_T, _plate_region, _cb_region,
                     _strap_region, carrier_outer, _surface_frame, trousers_field, boots_field, gloves_field,
                     trousers_weights, face_hull, BELT_Z, _front_top)

SCAR = 10                                                 # skin label: the scar on his cheek
IRIS = ((0.24, 0.17, 0.08), (0.46, 0.36, 0.16))           # deep-set hazel eyes (prep.paint_eyes)
CHARCOAL = (0.13, 0.13, 0.15)                             # fatigues
CHARCOAL2 = (0.2, 0.2, 0.23)                              # the shirt (a shade lighter than the trousers)
ARMOUR = (0.22, 0.23, 0.25)                               # gunmetal-black kit, the gun's carriage
TEAL = (0.2, 0.27, 0.28)                                  # worn smoky teal-grey cloth
AMBER = (1.0, 0.62, 0.15)                                 # the Resistance's glow
AMBER_P = (0.95, 0.6, 0.12)                               # amber paint (not lit)
ROBOT_WHITE = (0.88, 0.89, 0.9)
GUNMETAL = (0.3, 0.31, 0.34)
GREY_HAIR = (0.62, 0.6, 0.57)
BASE_L, BLACK_L, AMB_L, WHITE_L, TEAL_L, GM_L, STEEL_L, GLASS_L, RUBBER_L, HAZ_L, BRASS_L = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
U_AMB, U_METAL, U_BLACK = 5, 6, 7                         # uniform labels


# ======================================================================================= head: the old artillerist
def _on_face(fd, pts_xz, lift=0.0):
    """Points on the face's surface (as sculpted so far) in front of design points (x, z): rays from the front."""
    org = [hp((x, -0.45, z)) for x, z in pts_xz]
    h, ok = ray_hit(fd, org, [v3((0, 1, 0))] * len(pts_xz), tmax=0.5, step=0.0008)
    out = []
    for i, (x, z) in enumerate(pts_xz):
        q = h[i] if ok[i] else hp((x, -0.19, z))
        out.append(q - v3((0, 1, 0)) * lift)
    return out


def stubble_mask(P):
    """Under his chin and down his throat (design coordinates): grey stubble below the beard's edge."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    return np.maximum(np.maximum(np.abs(x) - F(0.11), z - F(1.5)), np.maximum(F(1.4) - z, y - F(0.02)))


def head(fd):
    """A weathered old face: the square jaw and chin (missile.py's), strong cheekbones over lean cheeks, a heavy brow, deep-set
    eyes (open and steady, bags under them, deep crow's feet), bushy brows set level on the brow ridge, a broad nose with a
    bump where it was broken, a firm closed mouth, lines from the nose to the mouth's corners, a scar across the left cheek,
    ears standing out under the bandana."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, 0.02, 1.79), (0.165, 0.175, 0.12)), 0.08, SKIN)
    fd.add(E(*JAW), 0.07, SKIN)
    fd.add(E(*CHIN), 0.05, SKIN)
    fd.add(E((0.0, -0.17, 1.49), (0.048, 0.027, 0.028)), 0.03, SKIN)                     # the chin's square point
    for sx in (-1, 1):
        c, r = cheekbone(sx)
        fd.add(S((c[0] + sx * 0.004, c[1], c[2] + 0.004), r + 0.004), 0.05, SKIN)
        c, r = jaw_corner(sx)
        fd.add(S(c, r), 0.05, SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.112, -0.112, 1.586)), v3((0.022, 0.016, 0.026)) * HS, R=euler(0, 0, sx * -0.5)), hr(0.02))
        pts = [hp((sx * 0.155, -0.055, 1.746)), hp((sx * 0.117, -0.134, 1.758)), hp((sx * 0.062, -0.179, 1.756)), hp((0.0, -0.189, 1.75))]
        fd.add(Chain(pts, [hr(0.013), hr(0.023), hr(0.027), hr(0.024)], k=hr(0.022)), hr(0.034), SKIN)     # heavy brow ridge
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # a forehead crease (between the brows and the bandana's edge) and two short lines between the brows
    sk = skull()
    pts = []
    for k in range(9):
        x = -0.07 + 0.14 * k / 8
        h, ok = ray_hit(sk, [hp((x, -0.6, 1.806 + 0.006 * (x / 0.07) ** 2))], [v3((0, 1, 0))], tmax=0.7)
        if ok[0]:
            pts.append(h[0])
    if len(pts) > 3:
        fd.sub(Chain(pts, [hr(0.0022)] * len(pts), k=0.002), hr(0.003))
    for sx in (-1, 1):
        fd.sub(RoundCone(hp((sx * 0.012, -0.203, 1.738)), hp((sx * 0.015, -0.2, 1.762)), hr(0.0018), hr(0.0014)), hr(0.003))
    # bushy grey brows, level, set on the brow ridge
    tuft = lambda P: F(0.0024) * NOISE(P * F(140)) + F(0.0011) * np.sin(P[:, 0] * F(360) + P[:, 2] * F(90))
    for sx in (-1, 1):
        pts = [hp((sx * 0.021, -0.216, 1.752)), hp((sx * 0.064, -0.212, 1.765)), hp((sx * 0.109, -0.192, 1.772)),
               hp((sx * 0.153, -0.15, 1.765))]
        if sx > 0:                                                                  # (the scar's nick in his left brow)
            pts[2] = pts[2] + v3((0, 0.002, 0.002))
        fd.add(Chain([p + v3((0, 0.004, 0)) for p in pts], [hr(0.013), hr(0.016), hr(0.014), hr(0.008)], k=hr(0.009),
                     disp=tuft, disp_amp=0.004), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.021), hr(0.024), hr(0.021), hr(0.013)], k=hr(0.01)), BROW)
    # deep-set eyes, open and steady (the upper lids a little low, never over the irises), bags under them, crow's feet
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.0178))), (sx * 0.14, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.006)), Plane(ec + v3((0, 0, -hr(0.0198))), (sx * -0.1, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.016))), (sx * 0.14, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(3):                                                                    # crow's feet
            a = hp((sx * (0.111 + 0.003 * k), -0.132 + 0.005 * k, 1.684 - 0.011 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.024, 0.013, 0.006 - 0.008 * k)), hr(0.0021), hr(0.0014)), hr(0.003))
        fd.add(Ellipsoid(hp((sx * 0.07, -0.158, 1.64)), v3((0.026, 0.011, 0.01)) * HS), hr(0.012), SKIN)    # bags under the eyes
        b = hp((sx * 0.05, -0.17, 1.628))
        fd.sub(RoundCone(b, b + v3((sx * 0.03, 0.01, -0.004)), hr(0.0016), hr(0.0011)), hr(0.003))           # the bags' lower line
    # a broad nose, a bump where it was broken, a fleshy tip
    fd.add(RoundCone(hp((0, -0.19, 1.728)), hp((0, -0.248, 1.634)), hr(0.018), hr(0.025)), hr(0.017), SKIN)
    fd.add(S((0.002, -0.214, 1.692), 0.017), hr(0.01), SKIN)
    fd.add(S((0, -0.25, 1.616), 0.031), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.035, -0.224, 1.602), 0.022), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.017, -0.241, 1.591)), v3((0.01, 0.012, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a firm closed mouth (the moustache over its upper lip)
    slot = [hp(p) for p in ((-0.05, -0.176, 1.552), (-0.026, -0.197, 1.548), (0.0, -0.203, 1.548), (0.026, -0.197, 1.548), (0.05, -0.176, 1.552))]
    fd.sub(Chain(slot, [hr(0.002), hr(0.0026), hr(0.0028), hr(0.0026), hr(0.002)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0038), hr(0.004), hr(0.0038), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.046, -0.178, 1.556), (-0.022, -0.197, 1.559), (0.0, -0.202, 1.56), (0.022, -0.197, 1.559), (0.046, -0.178, 1.556)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0055), hr(0.006), hr(0.0055), hr(0.003)], k=hr(0.005)), hr(0.006), LIP)
    lo_lip = [(-0.044, -0.176, 1.542), (-0.022, -0.194, 1.535), (0, -0.199, 1.533), (0.022, -0.194, 1.535), (0.044, -0.176, 1.542)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0068), hr(0.0076), hr(0.0068), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    # lines from the nose's wings toward the mouth's corners
    for sx in (-1, 1):
        folds = _on_face(fd, [(sx * 0.046, 1.606), (sx * 0.062, 1.584), (sx * 0.07, 1.562)], lift=-0.002)
        fd.sub(Chain(folds, [hr(0.0015), hr(0.0018), hr(0.0013)], k=hr(0.003)), hr(0.004))
    # the scar across his left cheek: a pale raised seam
    sc = _on_face(fd, [(0.075, 1.668), (0.093, 1.64), (0.11, 1.612), (0.124, 1.588)], lift=0.0)
    fd.add(Chain(sc, [hr(0.0022), hr(0.0028), hr(0.0026), hr(0.0018)], k=hr(0.002)), hr(0.003), SCAR)
    fd.paint(Chain(sc, [hr(0.006), hr(0.0072), hr(0.0068), hr(0.005)], k=hr(0.003)), SCAR)
    # ears, standing out under the bandana
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.028, 0.05, 0.064)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.013, 0.032, 0.042)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))


def body_parts(fd):
    """The Missile Launcher's body (missile.body_parts) with this head."""
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


# ======================================================================================= beard and hair
def _beard_region(Q):
    """< 0 inside the beard (design coordinates): the jaw, chin and cheeks below the cheekbones, up the sideburns to the
    bandana's edge in front of the ears; the lips and the nose left bare."""
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = (F(1.585) + F(0.04) * smoothstep(0.05, 0.12, ax) + F(0.13) * smoothstep(0.125, 0.165, ax))
    d = z - top
    d = np.maximum(d, F(1.44) - z - F(0.06) * smoothstep(-0.12, 0.0, y))         # its lower edge under the jaw
    d = np.maximum(d, y - F(0.035) + F(0.04) * smoothstep(1.62, 1.72, z))        # (in front of the ears)
    lips = np.sqrt((x / F(0.052)) ** 2 + ((y + F(0.19)) / F(0.06)) ** 2 + ((z - F(1.543)) / F(0.019)) ** 2) - F(1.0)
    return np.maximum(d, -lips * F(0.03))


def whiskers_field():
    """A short grey beard, clipped close (thicker at the chin), up the sideburns to the bandana; a heavy grey moustache over
    the upper lip, its ends drooping into the beard."""
    fd = Field("Whiskers")
    hull = face_hull()
    hairs = lambda P: F(0.0018) * NOISE(P * np.array([95, 95, 30], F)) + F(0.0009) * NOISE(P * F(170))
    def beard(P):
        d = hull.eval(P, margin=0.06)
        Q = hinv(P)
        m = _beard_region(Q) * F(HS)
        depth = np.clip(-m / F(0.02), 0, 1)
        chin = F(0.008) * smoothstep(-0.08, -0.15, Q[:, 1]) * smoothstep(1.56, 1.5, Q[:, 2])
        outer = F(0.003) + (F(0.011) + chin) * np.sqrt(depth)
        vol = np.maximum(d - outer, F(-0.006) - d)
        return np.maximum(vol, m)
    lo, hi = HEAD_C + v3((-0.32, -0.36, -0.42)), HEAD_C + v3((0.32, 0.14, 0.12))
    fd.add(Func(beard, lo, hi, disp=hairs, disp_amp=0.003), 0.0)
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.004, -0.236, 1.588)), hp((sx * 0.04, -0.226, 1.582)), hp((sx * 0.07, -0.203, 1.566)),
               hp((sx * 0.085, -0.178, 1.548))]
        fd.add(Lock(pts, [hr(0.019), hr(0.023), hr(0.019), hr(0.014)], [hr(0.012), hr(0.014), hr(0.012), hr(0.009)],
                    [norm(v3((sx * 0.3, -1, 0.1)))] * 4, k=hr(0.007), disp=strands, disp_amp=0.003), hr(0.008))
    return fd


def _ang(Q):
    """Angle round his head (design coordinates): 0 at the front, pi at the back."""
    return np.abs(np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.02))))


def rim_z(Q):
    """The bandana's lower edge (design z): above the brows, over the tops of the ears, down to the nape."""
    a = _ang(Q)
    return F(1.83) - F(0.07) * smoothstep(0.6, 1.3, a) - F(0.1) * smoothstep(1.9, 2.7, a)


def hair_field():
    """Grey hair, cropped short: under the bandana's edge at his temples and nape, the sideburns down into the beard; his
    ears left bare."""
    fd = Field("Hair")
    sk = skull()
    strands = lambda P: F(0.0012) * NOISE(P * np.array([90, 90, 30], F)) + F(0.0008) * NOISE(P * F(150))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = z - (rim_z(Q) + F(0.02))
        nape = F(1.6) - z + F(0.04) * smoothstep(0.03, 0.12, ax)
        front = np.where(ax > F(0.13), F(-0.085) - y + F(0.02) * smoothstep(1.66, 1.72, z), F(-0.04) - y)
        ear = F(1.0) - np.sqrt(((ax - F(0.18)) / F(0.05)) ** 2 + ((y - F(0.035)) / F(0.068)) ** 2 + ((z - F(1.664)) / F(0.078)) ** 2)
        return np.maximum(np.maximum(np.maximum(top, nape), front), ear * F(0.05))
    fd.add(Inter(Shell(sk, 0.004, 0.009, pad=0.06, disp=strands, disp_amp=0.002), Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.004), 0.0)
    return fd


# ======================================================================================= the bandana and goggles
BAND_OFF, BAND_T = 0.009, 0.011           # the bandana over the skull (close: cloth, not a helmet)
BAND_FACE = BAND_OFF + BAND_T / 2
GOG_Z = 1.875                              # the goggles' strap round the bandana (design height, at the front)


def _band_keep(P):
    Q = hinv(P)
    return (rim_z(Q) - Q[:, 2]) * F(HS)


def bandana_outer():
    sk = skull()
    return Func(lambda P: sk.eval(P, margin=0.1) - F(BAND_FACE), HEAD_C - 0.4, HEAD_C + 0.4)


def band_point(a, zd, out=0.0):
    """A point on the bandana's outer surface at angle a (0 = front, + toward his left) and design height zd; its normal."""
    bo = bandana_outer()
    c = hp((0.0, 0.02, zd))
    d = v3((math.sin(a), -math.cos(a), 0.0))
    h, ok = ray_hit(bo, [c + d * 0.6], [-d], tmax=0.7, step=0.0015)
    p = h[0]
    n = _fgrad(bo.fn, p)
    return p + n * out, n


def _strap_zc(Q):
    a = _ang(Q)
    return F(GOG_Z) - F(0.075) * smoothstep(1.2, 2.8, a)


def bandana_field():
    """Teal-grey cloth (0, woven): tied over his head, creased where it pulls, a rolled edge round its hem, the knot at the
    back of his head and its two tails hanging over the nape."""
    fd = Field("Bandana")
    sk = skull()
    lo, hi = HEAD_C - 0.4, HEAD_C + 0.4
    def creases(P):
        Q = hinv(P)
        a = np.arctan2(Q[:, 0], -(Q[:, 1] - F(0.02)))
        return F(0.0016) * np.sin(a * F(9) + Q[:, 2] * F(30) + F(1.2) * NOISE(P * F(4))) + F(0.001) * NOISE(P * F(25))
    fd.add(Inter(Shell(sk, BAND_OFF, BAND_T, pad=0.08, disp=creases, disp_amp=0.003), Func(_band_keep, lo, hi), 0.006), 0.0)
    # the rolled hem
    def hem(P):
        Q = hinv(P)
        return (np.abs(Q[:, 2] - rim_z(Q) - F(0.007)) - F(0.0075)) * F(HS)
    fd.add(Inter(Shell(sk, BAND_OFF + 0.003, 0.014, pad=0.08), Func(hem, lo, hi), 0.004), 0.006)
    # the knot at the back and its tails
    kp, kn = band_point(math.pi, 1.712, 0.006)
    fd.add(Ellipsoid(kp, (0.034, 0.024, 0.026), R=rot_from_axes(z_axis=kn, x_axis=(1, 0, 0))), 0.01)
    for sx in (-1, 1):
        fd.add(Ellipsoid(kp + v3((sx * 0.026, 0.004, 0.004)), (0.024, 0.016, 0.018), R=euler(0, sx * 0.4, 0)), 0.008)
        pts = [kp + v3((sx * 0.01, 0.008, -0.015)), kp + v3((sx * 0.024, 0.014, -0.06)), kp + v3((sx * 0.034, 0.016, -0.11)),
               kp + v3((sx * 0.04, 0.014, -0.15))]
        ns = [norm(v3((sx * 0.25, 1.0, 0.25)))] * 4
        fd.add(Lock(pts, [0.026, 0.03, 0.03, 0.022], [0.006, 0.006, 0.006, 0.005], ns, k=0.006,
                    disp=lambda P: F(0.0012) * NOISE(P * F(30)), disp_amp=0.002), 0.006)
    return fd


def goggles_field():
    """Black rubber (12): two lens cups pushed up on the bandana's front (amber lenses 11 in gunmetal rims 9), the bridge
    between them, the strap round his head over the bandana; a gunmetal buckle on the strap."""
    fd = Field("Goggles")
    sk = skull()
    lo, hi = HEAD_C - 0.4, HEAD_C + 0.4
    def strap(P):
        Q = hinv(P)
        return (np.abs(Q[:, 2] - _strap_zc(Q)) - F(0.011)) * F(HS)
    fd.add(Inter(Shell(sk, BAND_FACE + BAND_T / 2 + 0.003, 0.007, pad=0.08), Func(strap, lo, hi), 0.003), 0.0, RUBBER_L)
    cups = []
    for sx in (-1, 1):
        p, n = band_point(sx * 0.33, GOG_Z + 0.004)
        n = norm(n + v3((0, 0, 0.08)))
        R = rot_from_axes(z_axis=n)
        c = p + n * 0.016
        fd.add(Cylinder(c, 0.042, 0.034, rr=0.01, R=R), 0.004, RUBBER_L)
        fd.add(Torus(c + n * 0.017, 0.035, 0.0075, R=R), 0.003, GM_L)
        fd.add(Cylinder(c + n * 0.014, 0.032, 0.008, rr=0.003, R=R), 0.002, GLASS_L)
        cups.append((c, n))
    (c0, n0), (c1, n1) = cups
    mid = (c0 + c1) * 0.5 + (n0 + n1) * 0.004
    fd.add(Chain([c0 + (c1 - c0) * 0.3, mid, c1 + (c0 - c1) * 0.3], [0.009, 0.008, 0.009], k=0.004), 0.003, RUBBER_L)
    bp, bn = band_point(-1.6, GOG_Z - 0.03, 0.012)
    fd.add(RoundBox(bp, (0.012, 0.018, 0.014), 0.004, R=rot_from_axes(z_axis=bn, y_axis=(0, 0, 1))), 0.003, GM_L)
    return fd


# ======================================================================================= the shirt and the chest guard
ARMBAND_S = (0.13, 0.205)                  # the armband round his left upper arm (along the arm from the shoulder)


def _armband_region(P):
    s, d2 = _arm_coord(P, "L")
    near = (d2 < F(0.16 ** 2)) & (P[:, 0] > F(0.3))
    return np.where(near, np.abs(s - F(sum(ARMBAND_S) / 2)) - F((ARMBAND_S[1] - ARMBAND_S[0]) / 2), F(1.0))


def shirt_field():
    """Charcoal cloth (0): the fatigue shirt tucked in at his waist, a stand collar, the sleeves rolled up to mid-forearm (a
    thick roll at their ends); the amber armband (5) round his left upper arm, a pocket on each breast."""
    fd = Field("Shirt")
    base = shirt_hull()
    def folds(P):
        a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
        return F(0.0016) * np.sin(a * F(7) + F(0.9) * NOISE(P * F(3))) + F(0.0011) * NOISE(P * F(20))
    lo, hi = (-1, -0.6, 0.5), (1, 0.6, 1.7)
    fd.add(Inter(Shell(base, SHIRT_OFF, SHIRT_T, pad=0.12, disp=folds, disp_amp=0.003), Func(shirt_keep, lo, hi), 0.004), 0.0)
    roll = lambda P: F(0.0025) * np.sin(_arm_coord(P, "R")[0] * F(180)) + F(0.001) * NOISE(P * F(25))
    fd.add(Inter(Inter(Shell(base, SHIRT_OFF + 0.012, 0.026, pad=0.12, disp=roll, disp_amp=0.003), Func(_roll_band, lo, hi), 0.006),
                 Func(lambda P: P[:, 2] - F(1.2), lo, hi), 0.0), 0.006)
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    def band(P):
        front = np.clip(-(P[:, 1] - F(0.03)) / F(0.1), 0, 1)
        return np.maximum(F(1.39) - P[:, 2], P[:, 2] - F(1.475) + F(0.03) * front)
    fd.add(Inter(Shell(nk, 0.02, 0.014, pad=0.08), Func(band, (-0.3, -0.3, 1.3), (0.3, 0.3, 1.55)), 0.004), 0.004)
    # the armband: a band of amber cloth round the sleeve (only near his left upper arm)
    lo_a, hi_a = (0.2, -0.3, 0.9), (0.75, 0.4, 1.5)
    fd.add(Inter(Shell(base, SHIRT_OFF + 0.01, 0.014, pad=0.12, disp=lambda P: F(0.0008) * NOISE(P * F(30)), disp_amp=0.001),
                 Func(_armband_region, lo_a, hi_a), 0.003), 0.004, U_AMB)
    return fd


def plate_field():
    """The chest guard: a white robot breast plate (0 = robot white) over the front (panel-line grooves, a raised rim, dents,
    scrapes down to the gunmetal (9), gunmetal bolts), the bold amber chevron (6) sprayed across it; black webbing (5): the
    shoulder straps, the cummerbund, a panel on his back; gunmetal buckles."""
    fd = Field("Plate")
    base = shirt_hull()
    lo, hi = (-0.8, -0.6, 0.8), (0.8, 0.6, 1.7)
    cloth = lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.0006) * NOISE(P * F(90))
    def front_region(P):
        r = _plate_region(P)
        return np.maximum(r, P[:, 1] - F(0.02))
    def back_region(P):
        r = _plate_region(P)
        return np.maximum(r, F(0.05) - P[:, 1])
    fd.add(Inter(Shell(base, PLATE_OFF, PLATE_T, pad=0.14), Func(front_region, lo, hi), 0.012), 0.0, BASE_L)
    fd.add(Inter(Shell(base, CB_OFF + 0.004, CB_T, pad=0.14, disp=cloth, disp_amp=0.002), Func(back_region, lo, hi), 0.008), 0.004, BLACK_L)
    fd.add(Inter(Shell(base, CB_OFF, CB_T, pad=0.14, disp=cloth, disp_amp=0.002), Func(_cb_region, lo, hi), 0.006), 0.008, BLACK_L)
    fd.add(Inter(Shell(base, PC_IN + STRAP_T / 2, STRAP_T, pad=0.14, disp=cloth, disp_amp=0.001), Func(_strap_region, lo, hi), 0.01), 0.01, BLACK_L)
    out = PLATE_OFF + PLATE_T / 2
    # panel lines on the plate: a groove down its middle (to the chevron) and one across under the collarbones
    def mid_groove(P):
        return np.maximum(np.maximum(np.abs(P[:, 0]) - F(0.0028), F(1.25) - P[:, 2]), P[:, 1] - F(0.02))
    fd.sub(Inter(Shell(base, out, 0.012, pad=0.14), Func(mid_groove, lo, hi), 0.0), 0.002)
    def cross_groove(P):
        x = P[:, 0]
        return np.maximum(np.maximum(np.abs(P[:, 2] - F(1.06)) - F(0.003), np.abs(x) - F(0.18)), P[:, 1] - F(0.02))
    fd.sub(Inter(Shell(base, out, 0.012, pad=0.14), Func(cross_groove, lo, hi), 0.0), 0.002)
    co = carrier_outer()
    # the amber chevron: a bold V across the plate, point down
    for sx in (-1, 1):
        a, _ = _surface_frame(co, v3((sx * 0.15, -0.8, 1.29)), v3((0, 1, 0)))
        b, _ = _surface_frame(co, v3((0.0, -0.8, 1.13)), v3((0, 1, 0)))
        fd.paint(RoundCone(a, b, 0.03, 0.03), AMB_L)
    # dents and scrapes
    for x, z, r in ((-0.12, 1.2, 0.022), (0.1, 1.08, 0.018), (0.05, 1.3, 0.014)):
        p, n = _surface_frame(co, v3((x, -0.8, z)), v3((0, 1, 0)))
        fd.sub(Sphere(p + n * (r * 0.75), r), 0.006)
    for (x0, z0), (x1, z1) in (((-0.17, 1.12), (-0.09, 1.05)), ((0.12, 1.24), (0.18, 1.19)), ((-0.06, 1.33), (0.0, 1.31))):
        a, _ = _surface_frame(co, v3((x0, -0.8, z0)), v3((0, 1, 0)))
        b, _ = _surface_frame(co, v3((x1, -0.8, z1)), v3((0, 1, 0)))
        fd.paint(RoundCone(a, b, 0.006, 0.004), GM_L)
    # bolts at its corners, buckles on the straps
    for sx in (-1, 1):
        for z in (1.03, 1.31):
            p, n = _surface_frame(co, v3((sx * 0.175, -0.8, z)), v3((0, 1, 0)))
            fd.add(Cylinder(p + n * 0.002, 0.011, 0.01, rr=0.003, R=rot_from_axes(z_axis=n)), 0.002, GM_L)
        p, n = _surface_frame(co, v3((sx * 0.128, -0.8, 1.355)), v3((0, 1, 0)))
        fd.add(RoundBox(p + n * 0.004, (0.022, 0.014, 0.006), 0.004, R=rot_from_axes(z_axis=n, y_axis=(0, 0, 1))), 0.003, GM_L)
    # a pouch on the cummerbund's left front (black, a gunmetal snap)
    d = norm(v3((0.8, -1.0, 0.0)))
    p, n = _surface_frame(co, v3((0.25, 0.0, 1.07)) - d * 0.8, d)
    n = norm(v3((n[0], n[1], 0.0)))
    R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
    fd.add(RoundBox(p + n * 0.02, (0.045, 0.05, 0.022), 0.01, R=R), 0.006, BLACK_L)
    fd.add(RoundBox(p + n * 0.04 + v3((0, 0, 0.03)), (0.046, 0.018, 0.006), 0.004, R=R), 0.003, BLACK_L)
    fd.add(Cylinder(p + n * 0.046 + v3((0, 0, 0.026)), 0.007, 0.006, rr=0.002, R=R), 0.002, GM_L)
    return fd


# ======================================================================================= the howitzer (layout)
MX = 0.8                                   # the gun's middle line (x); it shoots toward -Y
TY = -0.4                                  # the trunnions' y
TRUN = v3((MX, TY, 0.8))                   # the trunnions (the barrel's line is laid about them)
ELEV = math.radians(15.0)                  # the barrel's elevation (fixed: laid for range)
GD = v3((0.0, -math.cos(ELEV), math.sin(ELEV)))     # along the bore, toward the muzzle
GU = v3((0.0, math.sin(ELEV), math.cos(ELEV)))      # up, across the bore
GX_ = v3((1.0, 0.0, 0.0))
BAR_UP = 0.1                               # the bore's axis above the trunnions
S_BR = -0.56                               # (along the bore from the trunnions) the breech ring's rear face ...
S_RING = -0.38                             # ... its front face
RING_HALF = (0.14, 0.135)                  # its half width and half height
S_BLK = S_BR + 0.065                       # the sliding block's middle
BLK_HALF = (0.16, 0.036, 0.095)
BLK_SLIDE = 0.21                           # how far the block slides out (toward +X, away from him) to open
S_CASE = S_BR + 0.105                      # the case's base in the chamber
CASE_L, CASE_R, RIM_R = 0.27, 0.054, 0.063
SHELL_L = 0.47                             # a round: base -> the nose's tip
PROJ_R = 0.05                              # the projectile's body
BORE_R = 0.056
R_J = 0.118                                # the jacket under the coils
S_J1 = -0.05                               # ... it ends here; the tube runs on to the brake
COIL_S = (-0.33, -0.265, -0.2, -0.135)     # the coil collars' middles
COIL_HW, COIL_R = 0.025, 0.148             # a collar's half width and radius ...
GROOVE_R = 0.132                           # ... its groove's bottom ...
BAND_R0, BAND_R1, BAND_HW = 0.112, 0.142, 0.011      # ... the glowing band in the groove
TUBE_R = (0.1, 0.088)                    # the tube (at S_J1, at the brake)
S_MUZ = 1.02                               # the muzzle's face
S_BRAKE = S_MUZ - 0.17                     # the muzzle brake's back
BRAKE_R = 0.12
S_BED = (-0.02, 0.48)                      # the recoil sled (bed, collar at its front end)
REC_MAX = 0.32                             # the recoil's run (the brake stays clear of the collar)
LEV_L = 0.2


def bore_pt(s, up=0.0, side=0.0):
    return TRUN + GD * s + GU * (BAR_UP + up) + GX_ * side


def _rgd(z=GU):
    return rot_from_axes(z_axis=z, y_axis=GD)


def _bore_local(P):
    """(across +X, along the bore from the trunnions, up across it) of points P in the barrel's rest frame."""
    q = P - (TRUN + GU * BAR_UP).astype(F)
    return q @ GX_.astype(F), q @ GD.astype(F), q @ GU.astype(F)


def _ring_sd(s0, s1, r0, r1, rr=0.006):
    """< 0 inside the annulus r0..r1 round the bore's axis between s0 and s1 (rounded edges)."""
    def fn(P):
        u, s, v = _bore_local(P)
        r = np.sqrt(u * u + v * v)
        dr = np.abs(r - F((r0 + r1) / 2)) - F((r1 - r0) / 2) + F(rr)
        ds = np.abs(s - F((s0 + s1) / 2)) - F((s1 - s0) / 2) + F(rr)
        return np.minimum(np.maximum(dr, ds), 0) + np.sqrt(np.maximum(dr, 0) ** 2 + np.maximum(ds, 0) ** 2) - F(rr)
    return fn


def _bore_bounds(s0, s1, r):
    pts = [bore_pt(s, up=v, side=u) for s in (s0, s1) for u in (-r, r) for v in (-r, r)]
    return np.min(pts, 0) - 0.03, np.max(pts, 0) + 0.03


MUZZLE = bore_pt(S_MUZ)
BLK_C = bore_pt(S_BLK, side=BLK_HALF[0] - RING_HALF[0])            # (closed: flush with the ring's near side)
LEV_P = bore_pt(S_BR + 0.09, up=0.03, side=-(RING_HALF[0] + 0.013))    # the breech lever's pivot (on his side)
SPADE_Y = 0.6                              # the trail's spade (y)
TRAIL_A = v3((MX, TY + 0.24, 0.42))        # the box trail's top middle at the saddle ...
TRAIL_B = v3((MX, SPADE_Y, 0.1))           # ... and at the spade
LEGS = (0.16, 0.42, -0.08, -0.32)          # the front legs: x from MX at the saddle and at their pads, y from TY there
KICK_P = v3((MX, SPADE_Y, 0.0))            # the gun rocks about its spade at the shot
GRIP_C = v3((MX - 0.27, TY + 0.2, 0.8))    # the firing grip's middle (out from the near side plate)
GRIP_A = norm(v3((0.0, -0.25, 1.0)))       # its axis (thumb up it)
RACK_C = v3((-0.2, 0.05, 0.0))             # the ready rack (its foot's middle) on his right ...
RACK_HALF = (0.15, 0.27, 0.2)              # ... its crate (length along Y)
RACK_SHELLS = (-0.09, 0.0, 0.09)           # the shells lying in its cradles (x from its middle); he takes the last
SH_A0 = v3((0.0, 1.0, 0.0))                # (rest) the shell's axis, base -> nose (noses to the back)
SH_BASE0 = RACK_C + v3((RACK_SHELLS[-1], -0.235, 0.5))     # (rest) its base's middle


# ======================================================================================= the shell
def shell_into(fd, base, A, k=0.0):
    """A round: a gunmetal case (9) with its rim and an amber stripe (6), the projectile: a dark steel cage (0) of four
    ribs between two rings round its core (the glow shows between the ribs), a steel (10) ogive and nose."""
    A = norm(A)
    R = rot_from_axes(z_axis=A)
    fd.add(Cylinder(base + A * 0.007, RIM_R, 0.014, rr=0.003, R=R), k, GM_L)
    fd.add(capped_cone(base + A * 0.01, base + A * CASE_L, CASE_R + 0.001, CASE_R - 0.002, rr=0.005), 0.004, GM_L)
    fd.paint(Cylinder(base + A * 0.12, CASE_R + 0.01, 0.024, R=R), AMB_L)
    fd.add(Cylinder(base + A * (CASE_L + 0.006), PROJ_R + 0.002, 0.018, rr=0.004, R=R), 0.003, BASE_L)
    fd.add(Cylinder(base + A * 0.375, PROJ_R + 0.003, 0.016, rr=0.004, R=R), 0.003, BASE_L)
    side = norm(np.cross(A, v3((0.0, 0.0, 1.0)) if abs(A[2]) < 0.9 else v3((1.0, 0.0, 0.0))))
    up = np.cross(A, side)
    for kk in range(4):
        a = math.pi / 4 + kk * math.pi / 2
        d = side * math.cos(a) + up * math.sin(a)
        fd.add(RoundCone(base + A * (CASE_L + 0.01) + d * (PROJ_R - 0.004), base + A * 0.372 + d * (PROJ_R - 0.004), 0.009, 0.009), 0.003, BASE_L)
    fd.add(RoundCone(base + A * 0.382, base + A * 0.44, PROJ_R - 0.002, 0.02), 0.006, STEEL_L)
    fd.add(RoundCone(base + A * 0.435, base + A * (SHELL_L - 0.007), 0.021, 0.007), 0.003, STEEL_L)


def core_into(fd, base, A, k=0.0):
    """The projectile's glowing core (inside the cage)."""
    A = norm(A)
    fd.add(capped_cone(base + A * (CASE_L + 0.002), base + A * 0.386, PROJ_R - 0.008, PROJ_R - 0.01, rr=0.008), k)


def shell_field():
    fd = Field("Shell")
    shell_into(fd, SH_BASE0, SH_A0)
    return fd


def shellglow_field():
    fd = Field("ShellGlow")
    core_into(fd, SH_BASE0, SH_A0)
    return fd


def case_field():
    """The spent case (gunmetal 9, open at its mouth; rest pose: in the chamber), scorched dark at the mouth (5)."""
    fd = Field("Case")
    base = bore_pt(S_CASE)
    R = rot_from_axes(z_axis=GD)
    fd.add(Cylinder(base + GD * 0.007, RIM_R, 0.014, rr=0.003, R=R), 0.0, GM_L)
    fd.add(capped_cone(base + GD * 0.01, base + GD * CASE_L, CASE_R + 0.001, CASE_R - 0.002, rr=0.005), 0.004, GM_L)
    fd.sub(Cylinder(base + GD * CASE_L, CASE_R - 0.008, 0.1, R=R), 0.003)
    fd.paint(Cylinder(base + GD * (CASE_L - 0.02), CASE_R + 0.01, 0.06, R=R), BLACK_L)
    fd.paint(Cylinder(base + GD * 0.12, CASE_R + 0.01, 0.024, R=R), AMB_L)
    return fd


# ======================================================================================= the barrel, block, lever
def barrel_field():
    """Gunmetal-black steel (0): the square breech ring (the block's slot through it, the chamber's mouth behind), a
    salvaged robot power cell strapped on its top (white 7, black 5 straps, its window's frame gunmetal 9), the jacket and
    its four copper coil collars (14), each grooved round its middle for its glowing band, cables (12) from the cell into
    the first collar, the long tube with weld beads (9), a lifting lug, the heavy muzzle brake (two ports a side) and the
    bore; amber paint (6) round the tube behind the brake, white stencils."""
    fd = Field("Barrel")
    sc = lambda P: F(0.0005) * NOISE(P * F(60))
    lo, hi = _bore_bounds(S_BR - 0.02, S_MUZ + 0.02, 0.2)
    rc = bore_pt(0.5 * (S_BR + S_RING))
    fd.add(RoundBox(rc, (RING_HALF[0], 0.5 * (S_RING - S_BR), RING_HALF[1]), 0.022, R=_rgd(), disp=sc, disp_amp=0.001), 0.0, BASE_L)
    fd.add(Cylinder(bore_pt(0.5 * (S_RING + S_J1)), R_J, S_J1 - S_RING + 0.02, rr=0.012, R=rot_from_axes(z_axis=GD)), 0.012, BASE_L)
    fd.add(capped_cone(bore_pt(S_J1 - 0.03), bore_pt(S_BRAKE + 0.02), TUBE_R[0], TUBE_R[1], rr=0.01), 0.014, BASE_L)
    fd.add(Cylinder(bore_pt(S_J1 + 0.01), TUBE_R[0] + 0.012, 0.03, rr=0.008, R=rot_from_axes(z_axis=GD)), 0.004, BASE_L)
    for s in (0.3, 0.62):                                                                # weld beads round the tube
        r = TUBE_R[0] + (TUBE_R[1] - TUBE_R[0]) * (s - S_J1) / (S_BRAKE - S_J1)
        fd.add(Torus(bore_pt(s), r + 0.001, 0.0065, R=rot_from_axes(z_axis=GD), disp=lambda P: F(0.0012) * NOISE(P * F(160)), disp_amp=0.0015), 0.003, GM_L)
    # the coil collars (copper) and the grooves their bands glow in
    for s in COIL_S:
        fd.add(Func(_ring_sd(s - COIL_HW, s + COIL_HW, R_J - 0.01, COIL_R, rr=0.008), lo, hi), 0.006, BRASS_L)
        fd.sub(Func(_ring_sd(s - BAND_HW - 0.002, s + BAND_HW + 0.002, GROOVE_R, COIL_R + 0.02, rr=0.0), lo, hi), 0.002)
        for e in (-1, 1):
            fd.add(Func(_ring_sd(s + e * (COIL_HW - 0.005) - 0.004, s + e * (COIL_HW - 0.005) + 0.004, COIL_R - 0.01, COIL_R + 0.004, rr=0.003), lo, hi), 0.002, GM_L)
    # the muzzle brake: a heavy block-like collar, two ports through each side
    fd.add(Cylinder(bore_pt(S_BRAKE + 0.085), BRAKE_R, 0.17, rr=0.018, R=rot_from_axes(z_axis=GD)), 0.01, BASE_L)
    fd.add(RoundBox(bore_pt(S_BRAKE + 0.085), (BRAKE_R + 0.014, 0.075, BRAKE_R - 0.02), 0.014, R=_rgd()), 0.008, BASE_L)
    for s in (S_BRAKE + 0.05, S_BRAKE + 0.115):
        fd.sub(RoundBox(bore_pt(s), (0.2, 0.019, 0.05), 0.008, R=_rgd()), 0.004)
    fd.sub(Cylinder(bore_pt(S_MUZ - 0.25), BORE_R, 0.52, R=rot_from_axes(z_axis=GD)), 0.004)
    fd.paint(Func(lambda P: np.maximum(np.sqrt(_bore_local(P)[0] ** 2 + _bore_local(P)[2] ** 2) - F(BORE_R + 0.01),
                                       F(S_MUZ - 0.5) - _bore_local(P)[1]), lo, hi), BLACK_L)
    fd.paint(Func(_ring_sd(S_BRAKE - 0.075, S_BRAKE - 0.035, TUBE_R[1] - 0.02, TUBE_R[1] + 0.03, rr=0.0), lo, hi), AMB_L)
    # the block's slot through the ring, the chamber's mouth behind it
    fd.sub(RoundBox(bore_pt(S_BLK), (0.32, BLK_HALF[1] + 0.003, BLK_HALF[2] + 0.003), 0.004, R=_rgd()), 0.003)
    fd.sub(Cylinder(bore_pt(S_BR + 0.03), RIM_R + 0.005, 0.08, R=rot_from_axes(z_axis=GD)), 0.004)
    fd.sub(Cylinder(bore_pt(S_CASE + 0.14), CASE_R + 0.004, 0.32, R=rot_from_axes(z_axis=GD)), 0.003)
    fd.paint(Cylinder(bore_pt(S_BR), RIM_R + 0.012, 0.03, R=rot_from_axes(z_axis=GD)), GM_L)
    # the power cell on the ring's top: a white robot cell (a captured part), black straps, the window's gunmetal frame
    cc = bore_pt(0.5 * (S_BR + S_RING), up=RING_HALF[1] + 0.036)
    fd.add(RoundBox(cc, (0.085, 0.075, 0.036), 0.014, R=_rgd()), 0.006, WHITE_L)
    fd.add(RoundBox(cc + GU * 0.034, (0.06, 0.05, 0.006), 0.004, R=_rgd()), 0.003, GM_L)
    fd.sub(RoundBox(cc + GU * 0.04, (0.046, 0.036, 0.008), 0.003, R=_rgd()), 0.002)
    for s in (-0.048, 0.048):                                                          # its straps
        fd.add(RoundBox(cc + GD * s, (0.09, 0.012, 0.04), 0.004, R=_rgd()), 0.003, BLACK_L)
    fd.paint(RoundBox(cc + GX_ * 0.07, (0.03, 0.08, 0.04), 0.002, R=_rgd()), AMB_L)                 # an amber slash on its side
    # its cables forward into the first coil collar
    for u in (-0.04, 0.04):
        a = cc + GD * 0.07 + GX_ * u + GU * 0.005
        e = bore_pt(COIL_S[0] - COIL_HW - 0.004, up=COIL_R - 0.03, side=u)
        mid = lerp(a, e, 0.5) + GU * 0.035
        fd.add(Chain([a, mid, e], [0.012, 0.012, 0.012], k=0.008), 0.004, RUBBER_L)
    # a lifting lug on the tube, stencils
    fd.add(Torus(bore_pt(0.12, up=TUBE_R[0] + 0.02), 0.026, 0.008, R=rot_from_axes(z_axis=GX_)), 0.004, GM_L)
    stencil(fd, "NOVA", bore_pt(0.2, up=TUBE_R[0] - 0.006 + 0.0), GD, -GX_, 0.04, WHITE_L, depth=0.012)
    return fd


def coils_field():
    """The coils' glowing bands, sunk in their grooves: one emissive mesh, scaled in across the bore to go dark."""
    fd = Field("Coils")
    lo, hi = _bore_bounds(COIL_S[0] - 0.05, COIL_S[-1] + 0.05, 0.18)
    for s in COIL_S:
        fd.add(Func(_ring_sd(s - BAND_HW, s + BAND_HW, BAND_R0, BAND_R1, rr=0.004), lo, hi), 0.0)
    return fd


def barrelglow_field():
    """What glows on the barrel all the time: the cell's window, the star-hot bore deep in the muzzle brake (it shows
    through the ports and the mouth)."""
    fd = Field("BarrelGlow")
    cc = bore_pt(0.5 * (S_BR + S_RING), up=RING_HALF[1] + 0.036)
    fd.add(RoundBox(cc + GU * 0.034, (0.046, 0.036, 0.004), 0.003, R=_rgd()), 0.0)
    fd.add(Cylinder(bore_pt(S_BRAKE + 0.04), BORE_R - 0.003, 0.18, rr=0.01, R=rot_from_axes(z_axis=GD)), 0.0)
    return fd


def block_field():
    """The sliding breech block: bright machined steel (10), a firing-pin boss on its back, a black grip on its far end."""
    fd = Field("Block")
    fd.add(RoundBox(BLK_C, BLK_HALF, 0.008, R=_rgd()), 0.0, STEEL_L)
    fd.add(Cylinder(BLK_C - GX_ * (BLK_HALF[0] - RING_HALF[0]) - GD * BLK_HALF[1], 0.026, 0.016, rr=0.004, R=rot_from_axes(z_axis=GD)), 0.003, STEEL_L)
    e = BLK_C + GX_ * BLK_HALF[0]
    fd.add(RoundBox(e + GX_ * 0.008, (0.012, 0.032, 0.055), 0.006, R=_rgd()), 0.003, BLACK_L)
    return fd


def lever_field():
    """The breech lever on the ring's near side: a flat gunmetal bar (9) from its pivot boss forward, an amber knob (6)."""
    fd = Field("Lever")
    Rx = rot_from_axes(z_axis=GX_)
    fd.add(Cylinder(LEV_P, 0.028, 0.026, rr=0.006, R=Rx), 0.0, GM_L)
    a, b = LEV_P, LEV_P + GD * LEV_L
    fd.add(RoundBox(lerp(a, b, 0.5), (0.009, LEV_L * 0.5, 0.014), 0.005, R=_rgd()), 0.006, GM_L)
    fd.add(Sphere(b + GX_ * -0.01, 0.024), 0.006, AMB_L)
    fd.add(Cylinder(LEV_P - GX_ * 0.015, 0.013, 0.01, rr=0.003, R=Rx), 0.002, STEEL_L)
    return fd


# ======================================================================================= the cradle (recoil sled)
def cradle_field():
    """Gunmetal-black (0): the sled's bed under the barrel with its side rails, the collar at its front, two recoil cylinders
    above the barrel (gunmetal 9, steel 10 rod ends), the trunnion block and pins; an amber line down the cylinders."""
    fd = Field("Cradle")
    s0, s1 = S_BED
    sm, sh = 0.5 * (s0 + s1), 0.5 * (s1 - s0)
    fd.add(RoundBox(bore_pt(sm, up=-TUBE_R[0] - 0.028), (0.08, sh, 0.02), 0.008, R=_rgd()), 0.0, BASE_L)
    for sx in (-1, 1):
        fd.add(RoundBox(bore_pt(sm, up=-TUBE_R[0] - 0.006, side=sx * 0.075), (0.013, sh, 0.026), 0.006, R=_rgd()), 0.004, BASE_L)
    lo, hi = _bore_bounds(s0 - 0.05, s1 + 0.05, 0.25)
    fd.add(Func(_ring_sd(s1 - 0.14, s1, TUBE_R[0] + 0.006, TUBE_R[0] + 0.045, rr=0.01), lo, hi), 0.008, BASE_L)
    for sx in (-1, 1):
        a, b = bore_pt(s0 - 0.03, up=0.152, side=sx * 0.074), bore_pt(s1 - 0.01, up=0.152, side=sx * 0.074)
        fd.add(capped_cone(a, b, 0.036, 0.034, rr=0.01), 0.008, GM_L)
        fd.add(Cylinder(a - GD * 0.004, 0.024, 0.02, rr=0.005, R=rot_from_axes(z_axis=GD)), 0.003, STEEL_L)
        fd.paint(Func(lambda P, sx=sx: np.maximum(np.abs(_bore_local(P)[0] - F(sx * 0.074)) - F(0.008),
                                                np.abs(_bore_local(P)[2] - F(0.152 + 0.034)) - F(0.012)), lo, hi), AMB_L)
        # the cylinders' brackets down to the collar and to the trunnion block
        for s in (s0 + 0.04, s1 - 0.07):
            fd.add(RoundBox(bore_pt(s, up=0.115, side=sx * 0.062), (0.018, 0.022, 0.032), 0.006, R=_rgd()), 0.006, BASE_L)
    fd.add(RoundBox(TRUN + GU * 0.0, (0.115, 0.12, 0.05), 0.016, R=_rgd()), 0.01, BASE_L)               # the trunnion block
    fd.add(Cylinder(TRUN, 0.04, 0.34, rr=0.006, R=rot_from_axes(z_axis=GX_)), 0.004, GM_L)
    return fd


# ======================================================================================= the carriage, trail and shield
SADDLE = [(-0.2, 0.36), (0.26, 0.36), (0.3, 0.5), (0.17, 0.86), (-0.12, 0.86), (-0.24, 0.6)]   # side profile (y from TY, z)
SADDLE_X, SADDLE_T = 0.168, 0.024
PLAT_C = v3((MX, TY + 0.02, 0.0))          # the firing platform's middle on the floor
PLAT_R = 0.31
TT_Z = (0.3, 0.37)                         # the turntable
TT_R = 0.23


def saddle_func(sx):
    xc = MX + sx * SADDLE_X
    p2 = poly2d(SADDLE)
    r = 0.01
    def fn(P):
        d2 = p2(P[:, 1] - F(TY), P[:, 2])
        disc = np.sqrt((P[:, 1] - F(TRUN[1])) ** 2 + (P[:, 2] - F(TRUN[2])) ** 2) - F(0.085)
        d2 = np.minimum(d2, disc)
        slot = np.maximum(np.abs(P[:, 1] - F(TY + 0.04)) - F(0.06), np.abs(P[:, 2] - F(0.56)) - F(0.08))
        d2 = np.maximum(d2, -(slot - F(0.014)))
        dx = np.abs(P[:, 0] - F(xc)) - F(SADDLE_T / 2)
        w0, w1 = d2 + F(r), dx + F(r)
        return np.minimum(np.maximum(w0, w1), F(0)) + np.sqrt(np.maximum(w0, 0) ** 2 + np.maximum(w1, 0) ** 2) - F(r)
    return Func(fn, (xc - 0.05, TY - 0.3, 0.3), (xc + 0.05, TY + 0.36, 0.95))


def beam_sd(A, B, w, h, r=0.012):
    """A box beam from A to B (its top on the line A-B), half widths w = (at A, at B), half heights h."""
    ax = B - A
    L = float(np.linalg.norm(ax))
    a = norm(ax)
    sd = norm(np.cross(a, v3((0, 0, 1))))
    up = np.cross(sd, a)
    def fn(P):
        q = P - A.astype(F)
        t = q @ a.astype(F)
        k = np.clip(t / F(L), 0, 1)
        ww = F(w[0]) + F(w[1] - w[0]) * k
        hh = F(h[0]) + F(h[1] - h[0]) * k
        dx = np.abs(q @ sd.astype(F)) - ww
        dz = np.abs(q @ up.astype(F) + hh) - hh
        dt = np.maximum(-t - F(0.05), t - F(L))
        qq = np.stack([dx + F(r), dz + F(r), dt + F(r)], 1)
        return np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0) - F(r)
    lo = np.minimum(A, B) - 0.2
    hi = np.maximum(A, B) + 0.2
    return Func(fn, lo, hi), a, sd, up, L


SH_Y = TY - 0.25                           # the shield's foot (y) ...
SH_Z0 = 0.42                               # ... and its height
SH_TILT = math.radians(10.0)               # leaning back
SH_N = v3((0.0, -math.cos(SH_TILT), math.sin(SH_TILT)))     # out of its face (forward)
SH_V = v3((0.0, math.sin(SH_TILT), math.cos(SH_TILT)))      # up its face
SH_P0 = v3((MX, SH_Y, SH_Z0))
SHIELD = [(-0.38, 0.0), (0.38, 0.0), (0.4, 0.5), (0.3, 0.76), (-0.3, 0.76), (-0.4, 0.5)]   # its outline (u across, v up)
SH_T = 0.026
SH_BOW = 0.35                              # its curve (the middle stands forward of its edges)


def _shield_axis_v():
    """Where the bore's axis crosses the shield (v up its face)."""
    o = TRUN + GU * BAR_UP
    s = float((SH_P0 - o) @ SH_N / (GD @ SH_N))
    p = o + GD * s
    return float((p - SH_P0) @ SH_V)


AP_V = _shield_axis_v()
APERTURE = (0.15, AP_V - 0.19, AP_V + 0.4)       # the barrel's notch: half width, from v up (open at the top)


def _shield_uv(P):
    q = P - SH_P0.astype(F)
    u = q @ GX_.astype(F)
    return u, q @ SH_V.astype(F), q @ SH_N.astype(F) - F(SH_BOW) * (F(0.16) - u * u) * F(0.5)


def _rrect(u, v, cu, cv, hu, hv, r):
    du, dv = np.abs(u - F(cu)) - F(hu - r), np.abs(v - F(cv)) - F(hv - r)
    return np.minimum(np.maximum(du, dv), F(0)) + np.sqrt(np.maximum(du, 0) ** 2 + np.maximum(dv, 0) ** 2) - F(r)


def shield_sd(P):
    u, v, w = _shield_uv(P)
    d2 = poly2d(SHIELD)(u, v)
    ap = _rrect(u, v, 0.0, 0.5 * (APERTURE[1] + APERTURE[2]), APERTURE[0], 0.5 * (APERTURE[2] - APERTURE[1]), 0.05)
    d2 = np.maximum(d2, -ap)
    dw = np.abs(w) - F(SH_T / 2)
    r = F(0.008)
    w0, w1 = d2 + r, dw + r
    return np.minimum(np.maximum(w0, w1), F(0)) + np.sqrt(np.maximum(w0, 0) ** 2 + np.maximum(w1, 0) ** 2) - r


def sh_pt(u, v, w=0.0):
    """A point on the shield's mid surface (its curve followed) at (u, v), w out of its face."""
    return SH_P0 + GX_ * u + SH_V * v + SH_N * (w + SH_BOW * (0.16 - u * u) * 0.5)


def shield_field():
    """The shield: a salvaged white robot panel (0 = robot white), curved, its raised rim and panel-line grooves, dents
    and bullet scars, scrapes down to the gunmetal (9), the bold amber Resistance chevron (6) sprayed across it with a
    little overspray, a black (5) stencilled serial left from the robot; its bolted gunmetal brackets (on its back)."""
    fd = Field("Shield")
    lo, hi = (MX - 0.5, SH_Y - 0.25, SH_Z0 - 0.06), (MX + 0.5, SH_Y + 0.25, SH_Z0 + 0.86)
    fd.add(Func(shield_sd, lo, hi), 0.0, BASE_L)
    out = SH_T / 2
    # a raised rim along its bottom and sides
    def rim(P):
        u, v, w = _shield_uv(P)
        d2 = poly2d(SHIELD)(u, v)
        return np.maximum(np.maximum(np.abs(d2 + F(0.02)) - F(0.016), np.abs(w - F(out)) - F(0.008)), v - F(0.58))
    fd.add(Func(rim, lo, hi), 0.004, BASE_L)
    # panel lines
    for (u0, v0), (u1, v1) in (((-0.3, 0.2), (-0.18, 0.2)), ((0.18, 0.2), (0.3, 0.2)), ((-0.25, 0.2), (-0.25, 0.62)),
                               ((0.25, 0.2), (0.25, 0.62))):
        fd.sub(RoundCone(sh_pt(u0, v0, out), sh_pt(u1, v1, out), 0.0045, 0.0045), 0.002)
    # dents and bullet scars
    for u, v, r in ((-0.2, 0.42, 0.03), (0.14, 0.12, 0.024), (0.3, 0.36, 0.016), (-0.32, 0.12, 0.014), (0.05, 0.3, 0.012),
                    (-0.08, 0.1, 0.01), (0.22, 0.56, 0.012)):
        fd.sub(Sphere(sh_pt(u, v, out + r * 0.72), r), 0.004)
    for u, v in ((-0.13, 0.32), (0.32, 0.22), (0.1, 0.5), (-0.28, 0.55)):
        fd.paint(Sphere(sh_pt(u, v, out), 0.012), GM_L)
    for (u0, v0), (u1, v1) in (((-0.36, 0.3), (-0.26, 0.24)), ((0.26, 0.08), (0.36, 0.14)), ((0.0, 0.05), (0.08, 0.02))):
        fd.paint(RoundCone(sh_pt(u0, v0, out), sh_pt(u1, v1, out), 0.006, 0.004), GM_L)
    # the amber chevron: a bold V point down under the notch, and a slash beside it
    vt = APERTURE[1] - 0.06
    for su in (-1, 1):
        fd.paint(RoundCone(sh_pt(su * 0.25, vt + 0.04, out), sh_pt(0.0, vt - 0.2, out), 0.045, 0.045), AMB_L)
    fd.paint(RoundCone(sh_pt(-0.33, 0.14, out), sh_pt(-0.27, 0.04, out), 0.012, 0.01), AMB_L)          # overspray
    stencil(fd, "UX-41", sh_pt(0.22, 0.66, out + 0.001), GX_, SH_V, 0.032, BLACK_L, depth=0.01)
    # its brackets on the back, down to the saddle plates
    for su in (-1, 1):
        a = sh_pt(su * 0.17, 0.18, -out)
        b = v3((MX + su * (SADDLE_X + 0.01), TY - 0.16, 0.5))
        fd.add(RoundCone(a, b, 0.02, 0.018), 0.006, GM_L)
        fd.add(Cylinder(a - SH_N * 0.004, 0.022, 0.012, rr=0.004, R=rot_from_axes(z_axis=SH_N)), 0.003, GM_L)
    return fd


def carriage_field():
    """Gunmetal-black (0): the firing platform on the floor (a round plate, four jack pads, bolts), the column and the
    turntable (a gunmetal (9) ring of teeth, an amber line), the saddle's two side plates carrying the trunnions (bearing
    caps, weld beads), the transom between them, the box trail back to its spade braced in the floor and two front legs splayed out to
    pads on the floor (rivets, amber bands near their ends); the firing grip on the near plate (black rubber 12, a
    gunmetal bracket, an amber trigger guard)."""
    fd = Field("Carriage")
    c0 = PLAT_C
    fd.add(Cylinder(c0 + v3((0, 0, 0.026)), PLAT_R, 0.052, rr=0.016), 0.0, BASE_L)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = v3((math.cos(a), math.sin(a), 0.0))
        fd.add(Cylinder(c0 + d * (PLAT_R + 0.02) + v3((0, 0, 0.018)), 0.055, 0.036, rr=0.01), 0.008, GM_L)
        fd.add(RoundBox(c0 + d * (PLAT_R - 0.03) + v3((0, 0, 0.06)), (0.05, 0.02, 0.03), 0.008, R=euler(0, 0, a)), 0.006, BASE_L)
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        fd.add(Cylinder(c0 + v3((math.cos(a) * (PLAT_R - 0.05), math.sin(a) * (PLAT_R - 0.05), 0.054)), 0.011, 0.01, rr=0.003), 0.002, GM_L)
    def plat_line(P):
        r = np.sqrt((P[:, 0] - F(c0[0])) ** 2 + (P[:, 1] - F(c0[1])) ** 2)
        return np.maximum(np.abs(r - F(PLAT_R - 0.016)) - F(0.012), P[:, 2] - F(0.06) + F(0.003))
    fd.paint(Func(plat_line, c0 - v3((0.4, 0.4, 0.0)), c0 + v3((0.4, 0.4, 0.1))), AMB_L)
    fd.add(Cylinder(c0 + v3((0, 0, (0.05 + TT_Z[0]) / 2)), 0.11, TT_Z[0] - 0.04, rr=0.012), 0.01, BASE_L)
    fd.add(Cylinder(c0 + v3((0, 0, (TT_Z[0] + TT_Z[1]) / 2)), TT_R, TT_Z[1] - TT_Z[0], rr=0.014), 0.006, BASE_L)
    for k in range(24):
        a = 2 * math.pi * k / 24
        fd.add(RoundBox(c0 + v3((math.cos(a) * (TT_R - 0.004), math.sin(a) * (TT_R - 0.004), TT_Z[0] - 0.006)),
                        (0.012, 0.012, 0.012), 0.003, R=euler(0, 0, a)), 0.002, GM_L)
    def tt_line(P):
        r = np.sqrt((P[:, 0] - F(c0[0])) ** 2 + (P[:, 1] - F(c0[1])) ** 2)
        return np.maximum(np.abs(P[:, 2] - F(TT_Z[1] - 0.02)) - F(0.008), F(TT_R - 0.02) - r)
    fd.paint(Func(tt_line, c0 - v3((0.4, 0.4, 0.0)), c0 + v3((0.4, 0.4, 0.5))), AMB_L)
    # the saddle plates, bearing caps, weld beads along their feet, the transom
    for sx in (-1, 1):
        fd.add(saddle_func(sx), 0.008, BASE_L)
        xc = MX + sx * (SADDLE_X + SADDLE_T / 2 + 0.008)
        fd.add(Cylinder(v3((xc, TRUN[1], TRUN[2])), 0.056, 0.03, rr=0.008, R=rot_from_axes(z_axis=GX_)), 0.004, GM_L)
        for k in range(6):
            a = 2 * math.pi * k / 6
            fd.add(Sphere(v3((xc + sx * 0.016, TRUN[1] + 0.04 * math.cos(a), TRUN[2] + 0.04 * math.sin(a))), 0.0065), 0.001, STEEL_L)
        pts = [v3((MX + sx * (SADDLE_X - SADDLE_T / 2 - 0.004), TY + y, TT_Z[1] + 0.006)) for y in (-0.18, 0.0, 0.2)]
        fd.add(Chain(pts, [0.007] * 3, k=0.004, disp=lambda P: F(0.0015) * NOISE(P * F(140)), disp_amp=0.002), 0.003, GM_L)
    fd.add(RoundBox(v3((MX, TY + 0.02, TT_Z[1] + 0.03)), (SADDLE_X + 0.012, 0.26, 0.03), 0.012), 0.008, BASE_L)
    # the box trail back to its spade braced in the floor (rivets, an amber band near its end, handspike sockets)
    beam, a, sd, up, L = beam_sd(TRAIL_A, TRAIL_B, (0.075, 0.058), (0.065, 0.045))
    fd.add(beam, 0.01, BASE_L)
    for k in range(9):
        t = 0.04 + (L - 0.1) * k / 8
        w = 0.075 + (0.058 - 0.075) * t / L
        for s2 in (-1, 1):
            fd.add(Sphere(TRAIL_A + a * t + sd * (s2 * (w + 0.002)) - up * 0.012, 0.0065), 0.002, BASE_L)
    def band(P, a=a, L=L):
        t = (P - TRAIL_A.astype(F)) @ a.astype(F)
        return np.abs(t - F(L - 0.17)) - F(0.035)
    fd.paint(Func(band, TRAIL_A - v3((0.3, 0.3, 0.5)), TRAIL_B + v3((0.3, 0.3, 0.3))), AMB_L)
    sp = TRAIL_B + a * 0.03 + v3((0.0, 0.0, -0.07))
    fd.add(RoundBox(sp, (0.15, 0.016, 0.085), 0.008, R=euler(-0.35, 0, 0)), 0.012, BASE_L)
    for s2 in (-1, 1):
        fd.add(RoundBox(sp + v3((s2 * 0.07, -0.05, 0.03)), (0.008, 0.05, 0.045), 0.004, R=euler(-0.35, 0, 0)), 0.006, BASE_L)
        h0 = TRAIL_A + a * (L * 0.62) + sd * (s2 * 0.07) - up * 0.03
        fd.add(Cylinder(h0 + sd * (s2 * 0.012), 0.018, 0.03, rr=0.005, R=rot_from_axes(z_axis=sd)), 0.004, GM_L)
    fd.add(Torus(TRAIL_B + a * 0.06 + v3((0, 0, 0.004)), 0.036, 0.01), 0.004, GM_L)
    # the front legs: box legs from the saddle's front corners splayed out to pads braced on the floor
    for sx in (-1, 1):
        A = v3((MX + sx * LEGS[0], TY + LEGS[2], 0.38))
        B = v3((MX + sx * LEGS[1], TY + LEGS[3], 0.07))
        beam, a, sd, up, L = beam_sd(A, B, (0.052, 0.04), (0.05, 0.036))
        fd.add(beam, 0.01, BASE_L)
        fd.add(Cylinder(B + v3((0, 0, -0.045)), 0.07, 0.03, rr=0.008), 0.01, GM_L)
        fd.add(Cylinder(A - a * 0.02 - up * 0.03, 0.028, 0.1, rr=0.008, R=rot_from_axes(z_axis=sd)), 0.006, GM_L)
        def lband(P, A=A, a=a, L=L):
            t = (P - A.astype(F)) @ a.astype(F)
            return np.abs(t - F(L - 0.1)) - F(0.025)
        fd.paint(Func(lband, np.minimum(A, B) - 0.2, np.maximum(A, B) + 0.2), AMB_L)
    # the firing grip: a bracket from the near side plate, the T-grip, an amber trigger guard
    xs = MX - SADDLE_X - SADDLE_T / 2
    b0 = v3((xs - 0.004, TY + 0.18, 0.62))
    gb = GRIP_C - GRIP_A * 0.08
    fd.add(Chain([b0, b0 + v3((-0.03, 0.02, 0.02)), gb + v3((0.0, 0.0, -0.03)), gb], [0.02, 0.019, 0.017, 0.017], k=0.012), 0.008, GM_L)
    fd.add(RoundCone(GRIP_C - GRIP_A * 0.065, GRIP_C + GRIP_A * 0.065, 0.023, 0.021), 0.008, RUBBER_L)
    fd.add(Sphere(GRIP_C + GRIP_A * 0.075, 0.026), 0.008, GM_L)
    fwd_g = norm(v3((0.0, -1.0, 0.25)))
    gd_pts = [GRIP_C + GRIP_A * 0.05 + fwd_g * 0.02, GRIP_C + GRIP_A * 0.02 + fwd_g * 0.065, GRIP_C - GRIP_A * 0.045 + fwd_g * 0.05,
              GRIP_C - GRIP_A * 0.06 + fwd_g * 0.018]
    fd.add(Chain(gd_pts, [0.0065] * 4, k=0.004), 0.003, AMB_L)
    fd.add(RoundBox(GRIP_C + GRIP_A * 0.02 + fwd_g * 0.03, (0.006, 0.01, 0.016), 0.003, R=rot_from_axes(z_axis=GRIP_A, y_axis=fwd_g)), 0.002, STEEL_L)
    return fd


# ======================================================================================= the ready rack
def rack_field():
    """The ready rack: a salvaged crate (gunmetal-black 0, an amber stencil band 6, gunmetal corners 9, black handles 5)
    under an open steel cradle frame (9) of three saddles; two shells lying in it, noses to the back (the third saddle his),
    a coiled cable (12) on the floor beside it."""
    fd = Field("Rack")
    c = RACK_C
    hx, hy, h = RACK_HALF
    fd.add(RoundBox(v3((c[0], c[1], h / 2)), (hx, hy, h / 2), 0.016), 0.0, BASE_L)
    fd.add(RoundBox(v3((c[0], c[1], h + 0.006)), (hx + 0.008, hy + 0.008, 0.012), 0.006), 0.004, GM_L)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(RoundBox(v3((c[0] + sx * hx, c[1] + sy * hy, h / 2)), (0.016, 0.016, h / 2 + 0.004), 0.005), 0.003, GM_L)
    fd.paint(RoundBox(v3((c[0] - hx, c[1], h * 0.55)), (0.02, hy - 0.04, 0.03), 0.002), AMB_L)
    for sy in (-1, 1):
        e = v3((c[0], c[1] + sy * (hy + 0.01), h * 0.62))
        fd.add(RoundBox(e, (0.05, 0.012, 0.012), 0.006), 0.004, BLACK_L)
    # the cradle frame: two cross bars with three saddles each, on four posts
    zt = SH_BASE0[2] - RIM_R - 0.004
    for yy in (-0.16, 0.15):
        bar_c = v3((c[0], c[1] + yy, zt - 0.012))
        fd.add(RoundBox(bar_c, (hx - 0.01, 0.018, 0.012), 0.004), 0.004, GM_L)
        for x in RACK_SHELLS:
            sc = v3((c[0] + x, c[1] + yy, SH_BASE0[2]))
            fd.add(Inter(RoundBox(v3((c[0] + x, c[1] + yy, zt + 0.008)), (0.06, 0.018, 0.03), 0.006),
                         Func(lambda P, sc=sc: -(np.sqrt((P[:, 0] - F(sc[0])) ** 2 + (P[:, 2] - F(sc[2])) ** 2) - F(CASE_R + 0.004)),
                              sc - 0.1, sc + 0.1), 0.004), 0.004, GM_L)
    for sx in (-1, 1):
        for yy in (-0.16, 0.15):
            fd.add(RoundCone(v3((c[0] + sx * (hx - 0.03), c[1] + yy, h + 0.01)), v3((c[0] + sx * (hx - 0.03), c[1] + yy, zt - 0.01)), 0.012, 0.012), 0.004, GM_L)
    for x in RACK_SHELLS[:-1]:
        shell_into(fd, SH_BASE0 + v3((x - RACK_SHELLS[-1], 0.0, 0.0)), SH_A0, k=0.002)
    # a coiled cable on the floor at its foot
    cc = v3((c[0] - 0.02, c[1] - hy - 0.12, 0.016))
    fd.add(Torus(cc, 0.075, 0.013), 0.004, RUBBER_L)
    fd.add(Torus(cc + v3((0.01, 0.004, 0.024)), 0.068, 0.013), 0.004, RUBBER_L)
    return fd


def rackglow_field():
    """The rack's shells' glowing cores (one emissive mesh)."""
    fd = Field("RackGlow")
    for x in RACK_SHELLS[:-1]:
        core_into(fd, SH_BASE0 + v3((x - RACK_SHELLS[-1], 0.0, 0.0)), SH_A0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.618)), 0.06, 0.85)]                                   # a weathered, ruddy nose
    for sx in (-1, 1):
        pts += [(hp((sx * 0.11, -0.15, 1.636)), 0.06, 0.7), (hp((sx * 0.18, 0.035, 1.664)), 0.05, 0.55),
                (hp((sx * 0.05, -0.18, 1.79)), 0.07, 0.25)]
    return pts


# ======================================================================================= build config
GLB_NAME = "nova_artillery"
ROOT_NAME = "NovaArtilleryHQ"
TEX_PREFIX = "nova_artillery"
MAT_NAME = "NovaArtilleryMat"
MESH_NAME = "NovaArtillery"
BASE_MODULE = "nova_artillery_base"
ANIM_MODULE = "anim_nova_artillery"
PARTS = ["Skin", "Eyes", "Whiskers", "Hair", "Bandana", "Goggles", "Shirt", "Plate", "Trousers", "Boots", "Gloves",
         "Barrel", "Coils", "BarrelGlow", "Block", "Lever", "Cradle", "Carriage", "Shield", "Shell", "ShellGlow", "Case",
         "Rack", "RackGlow"]
REGION_PARTS = ("Skin", "Bandana", "Goggles", "Shirt", "Plate", "Trousers", "Boots", "Barrel", "Block", "Lever", "Cradle",
                "Carriage", "Shield", "Shell", "Case", "Rack")
KIT = dict(red=AMBER_P, white=ROBOT_WHITE, olive=TEAL, gunmetal=GUNMETAL, steel=(0.62, 0.64, 0.68), glass=(0.32, 0.17, 0.04),
           rubber=(0.08, 0.08, 0.085), coyote=(0.9, 0.42, 0.1), black=(0.06, 0.06, 0.065), glass_hi=(1.0, 0.68, 0.25))
GREY = {"base": GREY_HAIR, "hi": (0.84, 0.83, 0.8), "low": (0.36, 0.35, 0.33), "streak": (0.5, 0.49, 0.47), "tint": (0.7, 0.68, 0.64)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_NaSkin", "base": (0.74, 0.52, 0.4), "ruddy": (0.76, 0.42, 0.33), "lips": (0.6, 0.36, 0.3),
                      "brow": ((0.5, 0.49, 0.46), (0.74, 0.72, 0.68)),
                      "extra": ((LASH, (0.2, 0.17, 0.14), 0.5), (STUBBLE, (0.6, 0.56, 0.52), 0.6, 0.5),
                                (SCAR, (0.88, 0.66, 0.58), 0.45, 0.85))}),
    "Whiskers": ("hair", dict(GREY, name="HQ_NaBeard")),
    "Hair": ("hair", dict(GREY, name="HQ_NaHair")),
    "Bandana": ("modern_kit", dict(KIT, name="HQ_NaBandana", base=TEAL, weave=1.0)),
    "Goggles": ("modern_kit", dict(KIT, name="HQ_NaGoggles", base=(0.08, 0.08, 0.085), weave=0.0)),
    "Shirt": ("uniform", {"name": "HQ_NaShirt", "base": CHARCOAL2, "facing": AMBER_P, "brass": (0.62, 0.64, 0.68),
                          "buff": (0.06, 0.06, 0.065), "black": (0.06, 0.06, 0.065)}),
    "Plate": ("modern_kit", dict(KIT, name="HQ_NaPlate", base=ROBOT_WHITE, weave=0.0, gloss=0.42)),
    "Trousers": ("uniform", {"name": "HQ_NaTrousers", "base": CHARCOAL, "facing": AMBER_P, "brass": (0.62, 0.64, 0.68),
                             "buff": (0.07, 0.07, 0.075), "black": (0.06, 0.06, 0.065)}),
    "Boots": ("leather_dyed", {"name": "HQ_NaBoots", "base": (0.07, 0.065, 0.065), "dyed": (0.05, 0.048, 0.048), "worn_c": (0.3, 0.29, 0.28)}),
    "Gloves": ("leather_dyed", {"name": "HQ_NaGloves", "base": (0.08, 0.08, 0.085), "dyed": (0.08, 0.08, 0.085), "worn_c": (0.28, 0.28, 0.29)}),
    "Barrel": ("modern_kit", dict(KIT, name="HQ_NaGun", base=ARMOUR, weave=0.0)),
    "Block": ("modern_kit", dict(KIT, name="HQ_NaGun", base=ARMOUR, weave=0.0)),
    "Lever": ("modern_kit", dict(KIT, name="HQ_NaGun", base=ARMOUR, weave=0.0)),
    "Cradle": ("modern_kit", dict(KIT, name="HQ_NaGun", base=ARMOUR, weave=0.0)),
    "Carriage": ("modern_kit", dict(KIT, name="HQ_NaGun", base=ARMOUR, weave=0.0)),
    "Shell": ("modern_kit", dict(KIT, name="HQ_NaGun", base=ARMOUR, weave=0.0)),
    "Case": ("modern_kit", dict(KIT, name="HQ_NaGun", base=ARMOUR, weave=0.0)),
    "Rack": ("modern_kit", dict(KIT, name="HQ_NaGun", base=ARMOUR, weave=0.0)),
    "Shield": ("modern_kit", dict(KIT, name="HQ_NaShield", base=ROBOT_WHITE, weave=0.0, gloss=0.42)),
}
GLOW = {"Coils": (AMBER, 1.3, 0.5), "BarrelGlow": (AMBER, 1.3, 0.5), "ShellGlow": (AMBER, 1.2, 0.5), "RackGlow": (AMBER, 1.1, 0.5)}
LOW_TARGETS = {"Skin": 4900, "Whiskers": 900, "Hair": 320, "Bandana": 1300, "Goggles": 520, "Shirt": 2900, "Plate": 1900,
               "Trousers": 1700, "Boots": 1000, "Gloves": 800, "Barrel": 2300, "Coils": 360, "BarrelGlow": 120, "Block": 160,
               "Lever": 200, "Cradle": 1000, "Carriage": 2800, "Shield": 900, "Shell": 340, "ShellGlow": 60, "Case": 150,
               "Rack": 1100, "RackGlow": 120}
AO_EXCLUDE = ["Shell", "Case", "Goggles", "Lever"]
GUN_PARTS = ["Barrel", "Block", "Lever", "Cradle", "Carriage", "Shield", "Shell", "Case", "Rack"]
# the gun and the rack are baked 6 m away from him (his rest pose stands in the breech)
BAKE_APART = (GUN_PARTS, (6.0, 0.0, 0.0))
YAW_PIVOT = (0.42, -0.3, 0.0)              # the tower turns about this point (keeps him, the gun and the rack on the base)


def prop_bones():
    return []                                # everything he handles is a free bone (extra_bones)


def extra_bones():
    """The gun's bones (none of them deform him): carriage (the platform, saddle, trail, cradle and shield: rocking about the
    spades at the shot), barrel (sliding back along the sled: from the trunnions to the muzzle's face), coils (child of the
    barrel, along the bore: the glowing bands, scaled in across the bore to go dark), mouth (child of the barrel: its head
    in the middle of the muzzle's face, its tail 0.1 out along the bore: where the game's shell leaves, and which way),
    block (sliding out to open the breech), lever (on the barrel, swinging up and back); the shell he loads (base -> nose)
    and the spent case; props (the ready rack, still)."""
    cb = bore_pt(S_CASE)
    return [
        ("carriage", KICK_P, KICK_P + v3((0, -0.4, 0)), None),
        ("barrel", TRUN, MUZZLE, None),
        ("coils", bore_pt(0.0), bore_pt(0.3), "barrel"),
        ("mouth", MUZZLE, MUZZLE + GD * 0.1, "barrel"),
        ("block", BLK_C, BLK_C + GX_ * 0.15, None),
        ("lever", LEV_P, LEV_P + GD * LEV_L, "barrel"),
        ("shell", SH_BASE0, SH_BASE0 + SH_A0 * SHELL_L, None),
        ("case", cb, cb + GD * CASE_L, None),
        ("props", RACK_C + v3((0, 0, 0.25)), RACK_C + v3((0, 0, 0.45)), None),
    ]


def weight_rules():
    body = TORSO | {"clavicle.R", "clavicle.L"}
    return {
        "Eyes": ("rigid", "head"), "Whiskers": ("rigid", "head"), "Hair": ("rigid", "head"), "Bandana": ("rigid", "head"),
        "Goggles": ("rigid", "head"),
        "Shirt": ("transfer", body | {"upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}, None),
        "Plate": ("transfer", body, None),
        "Trousers": ("custom", trousers_weights),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Barrel": ("rigid", "barrel"), "BarrelGlow": ("rigid", "barrel"), "Coils": ("rigid", "coils"),
        "Block": ("rigid", "block"), "Lever": ("rigid", "lever"),
        "Cradle": ("rigid", "carriage"), "Carriage": ("rigid", "carriage"), "Shield": ("rigid", "carriage"),
        "Shell": ("rigid", "shell"), "ShellGlow": ("rigid", "shell"), "Case": ("rigid", "case"),
        "Rack": ("rigid", "props"), "RackGlow": ("rigid", "props"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Whiskers") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.85
    if part in ("Carriage", "Rack"):
        return 0.72
    if part in ("Barrel", "Cradle"):
        return 0.85
    if part in ("Shell", "Case", "Lever", "Block"):
        return 0.9
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Whiskers", whiskers_field(), 0.0022 if fine else 0.003),
        ("Hair", hair_field(), 0.0022 if fine else 0.003),
        ("Bandana", bandana_field(), 0.0022 if fine else 0.0032),
        ("Goggles", goggles_field(), 0.0016 if fine else 0.0022),
        ("Shirt", shirt_field(), 0.0026 if fine else 0.0036),
        ("Plate", plate_field(), 0.0026 if fine else 0.0036),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Gloves", gloves_field(), 0.0018 if fine else 0.0026),
        ("Barrel", barrel_field(), 0.0026 if fine else 0.0036),
        ("Coils", coils_field(), 0.002 if fine else 0.0028),
        ("BarrelGlow", barrelglow_field(), 0.002 if fine else 0.0028),
        ("Block", block_field(), 0.002 if fine else 0.003),
        ("Lever", lever_field(), 0.0016 if fine else 0.0024),
        ("Cradle", cradle_field(), 0.0024 if fine else 0.0034),
        ("Carriage", carriage_field(), 0.003 if fine else 0.0044),
        ("Shield", shield_field(), 0.0026 if fine else 0.0036),
        ("Shell", shell_field(), 0.0016 if fine else 0.0024),
        ("ShellGlow", shellglow_field(), 0.0018 if fine else 0.0026),
        ("Case", case_field(), 0.0016 if fine else 0.0024),
        ("Rack", rack_field(), 0.0024 if fine else 0.0034),
        ("RackGlow", rackglow_field(), 0.0018 if fine else 0.0026),
    ]
