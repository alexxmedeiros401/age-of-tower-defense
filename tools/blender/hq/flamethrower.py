"""The Flamethrower (HQ tower, Modern Age; Brute lineage, melee). Rest pose = A-pose, facing -Y, feet at z = 0; right
side = -X.

A big, tough flame trooper of the task force, cheerful and scorched: a broad square jaw dark with stubble, a strong
straight nose, a wide grin (his teeth showing, the corners up into his cheeks), dark brows, brown eyes crinkled by the
grin, soot streaked across his forehead and cheeks; short dark hair cropped close under his helmet. A heavy helmet
painted olive drab (a black rubber trim round its edge) with a smoked visor flipped up over its
front (a dark glass band in a black frame, hinged on bosses at his temples).

A fire suit of olive-drab cloth (label 0), a jacket to his upper thighs with a stand-up collar, reflective tan bands
(7) round his chest, his hem, his upper arms and his forearms and round his shins, charred grey (5) on his cuffs and
shins; trousers of the same cloth, black knee pads; heavy black gauntlet gloves (rubber pads on the knuckles) and high
black boots with thick lug soles. A coyote-tan harness: two shoulder straps from his tank frame over his shoulders and
down his chest to a padded hip belt, a sternum strap with a black buckle, pouches on his left hip; on the left strap at
his chest a pressure gauge (a brass bezel, a cream dial, a red sector) on its line from the tanks; a small red-and-white
unit patch on his left shoulder.

On his back the fuel unit: two gunmetal fuel tanks side by side (hazard bands of yellow and black round their tops,
steel straps, brass filler caps), an olive pressure sphere set behind between them with its regulator, a black frame
against his back, a manifold across the tanks' feet with the outlet valve on his right, and from it a black rubber hose
round his right hip to the gun.

The flamethrower (the `flamer` bone: from the bore above the rear grip to the nozzle's tip, along the bore): an olive
receiver with a black pistol grip and trigger at the back, a red valve wheel on top, the hose's brass fitting under its
rear; a gunmetal fuel tube to the nozzle, a black perforated heat shield over its front half (steel bands), a black
front grip on a clamp; the steel nozzle flared at its mouth; under it the brass igniter line to the igniter housing,
and at the nozzle's tip the pilot flame (`Pilot`, its own glowing mesh on the `pilot` bone, a child of `flamer`: the
clips scale it, low in the Idle, lit in Combat, swelling in the Attack).

His body is the smith's (tarek.py: big and broad) ; his face is
built like the Brawler's and the grenadier's (marco.py); both hands are fists (round the grips). The gun and its pilot
ride parentless / child bones posed in world space (anim_flamethrower.py), as Ada's launcher (ada.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp, project_to, grad
from ugo import _blend_add
from tarek import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, foot,
                   torso_prims, traps, neck_prim, deltoid, upper_arm, _forearm, TORSO, TORSO_Z, torso_bones, HAND_S,
                   fist_center)
from marco import neck_open, neck_dist, legs_hull, leg_prims, shin_hull, foot_hull, torso_hull


SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, STUBBLE, SOOT = 0, 1, 2, 3, 4, 5, 8, 9, 10
# cloth labels (mats.uniform): olive cloth, charred grey, (brass), reflective tan, black
CLOTH, CHAR, BRASS_C, TAN, BLACK_C = 0, 5, 6, 7, 8
# kit labels (mats.fieldgun): olive paint, gunmetal, brass, steel, black, -, -, copper, red (yellow on the tanks), white
OLIVE, GUNMETAL, BRASS, STEEL, BLACK, RED, WHITE = 0, 5, 6, 7, 8, 12, 13
# steamworks labels: rubber, black leather, enamel, red paint, glass
W_IRON, W_BRASS, W_STEEL, W_RUBBER, W_ENAMEL, W_RED, W_BLACK, W_GLASS = 0, 5, 7, 8, 10, 11, 12, 13

OLIVE_DRAB = (0.4, 0.42, 0.28)         # the task force's uniforms (the brief: recipes read colours as sRGB)
COYOTE = (0.6, 0.5, 0.36)
IRIS = ((0.26, 0.16, 0.08), (0.52, 0.36, 0.2))


# ======================================================================================= hands: two fists
CURLS = (1.45, 1.6, 1.2)


def hand(fd, side, s=HAND_S, label=SKIN, k_scale=1.0, inflate=0.0):
    """A fist (tarek.hand's fist, for either hand: both grip the gun). `inflate` thickens every shape (the glove)."""
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.077 * s
    e = inflate
    fd.add(RoundBox(c, v3((0.064, 0.034, 0.066)) * s + e, 0.03 * s + e, R=Rp), 0.028 * k_scale, label)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.036, 0.03, 0.052)) * s + e, R=Rp), 0.019 * k_scale, label)
    curl_ax = norm(np.cross(f, n))
    offs = (0.044, 0.0148, -0.0148, -0.044)
    lens = (0.96, 1.02, 0.96, 0.8)
    tips = []
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.022 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.052 * ls * s, 0.042 * ls * s, 0.034 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, CURLS[j] * (0.9 if i == 3 else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, [r + e for r in rads], k=0.006), 0.011 * k_scale, label)
        fd.add(Sphere(pts[0] - n * 0.011, 0.016 * s + e), 0.009 * k_scale, label)
        tips.append(pts)
    tb = wr + f * 0.045 * s + t * 0.052 * s + n * 0.011
    d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
    d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.026 * s + e, 0.023 * s + e, 0.02 * s + e], k=0.008), 0.018 * k_scale, label)
    return tips


# ======================================================================================= head
def stubble_mask(P):
    """His jaw, chin, cheeks below the cheekbones and upper lip (design coordinates): a heavy dark stubble."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.552) + F(0.072) * smoothstep(0.075, 0.14, ax) - F(0.05) * smoothstep(0.15, 0.19, ax)
    return np.maximum(np.maximum(z - top, F(1.43) - z), y - F(0.035))


def head(fd):
    """A broad, tough, good-humoured face: a broad square jaw dark with stubble, round cheeks bunched by his grin, dark
    brows set level on the brow ridge, brown eyes crinkled by the grin, a strong straight nose, a wide grin with his teeth
    showing, soot streaked across his brow and cheeks."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.05, 1.588), (0.164, 0.142, 0.132)), 0.07, SKIN)                         # a broad, square jaw
    fd.add(E((0, -0.14, 1.497), (0.098, 0.074, 0.072)), 0.05, SKIN)                         # a big square chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.114, -0.128, 1.636), 0.056), 0.05, SKIN)                            # round cheeks, bunched by the grin
        fd.add(S((sx * 0.14, -0.042, 1.552), 0.057), 0.05, SKIN)                             # the jaw's corners
        pts = [hp((sx * 0.156, -0.055, 1.744)), hp((sx * 0.118, -0.135, 1.757)), hp((sx * 0.062, -0.178, 1.756)), hp((0.0, -0.188, 1.752))]
        fd.add(Chain(pts, [hr(0.013), hr(0.021), hr(0.024), hr(0.022)], k=hr(0.022)), hr(0.03), SKIN)     # a heavy brow ridge
    fd.sub(RoundCone(hp((0, -0.212, 1.512)), hp((0, -0.204, 1.476)), hr(0.004), hr(0.0055)), hr(0.007))      # a cleft in his chin
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # dark brows, thick, set level on the brow ridge (the outer ends lifted a little: a grin, not a scowl)
    tuft = lambda P: F(0.0024) * NOISE(P * F(150)) + F(0.001) * np.sin(P[:, 0] * F(380))
    for sx in (-1, 1):
        pts = [hp((sx * 0.026, -0.212, 1.808)), hp((sx * 0.068, -0.207, 1.815)), hp((sx * 0.114, -0.186, 1.811)),
               hp((sx * 0.157, -0.146, 1.792))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.0105), hr(0.0125), hr(0.011), hr(0.0055)], k=hr(0.008),
                     disp=tuft, disp_amp=0.0025), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.02), hr(0.023), hr(0.021), hr(0.012)], k=hr(0.01)), BROW)
    # eyes crinkled by his grin
    for sx in (-1, 1):
        ec = eye_c(sx)
        top = 0.021
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(top))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0062)), Plane(ec + v3((0, 0, -hr(0.0105))), (sx * -0.16, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(top - 0.003))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(2):                                                                      # laughter lines
            a = hp((sx * (0.11 + 0.004 * k), -0.128 + 0.006 * k, 1.68 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, -0.002 - 0.009 * k)), hr(0.002), hr(0.0014)), hr(0.003))
    # a strong straight nose
    fd.add(RoundCone(hp((0, -0.186, 1.726)), hp((0, -0.24, 1.634)), hr(0.02), hr(0.026)), hr(0.017), SKIN)
    fd.add(S((0, -0.24, 1.622), 0.029), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.035, -0.217, 1.606), 0.024), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.019, -0.235, 1.596)), v3((0.0095, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a wide grin, teeth showing; its corners up into his cheeks
    slot = [hp((-0.084, -0.152, 1.584)), hp((-0.048, -0.19, 1.553)), hp((0, -0.201, 1.541)), hp((0.048, -0.19, 1.553)), hp((0.084, -0.152, 1.584))]
    fd.sub(Chain(slot, [hr(0.006), hr(0.015), hr(0.018), hr(0.015), hr(0.006)], k=hr(0.004)), hr(0.004))
    fd.paint(Chain(slot, [hr(0.007), hr(0.0165), hr(0.0195), hr(0.0165), hr(0.007)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.07, -0.16, 1.568), (-0.038, -0.188, 1.53), (0, -0.195, 1.522), (0.038, -0.188, 1.53), (0.07, -0.16, 1.568)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0078), hr(0.0088), hr(0.0078), hr(0.004)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(S((sx * 0.092, -0.146, 1.584), 0.01), hr(0.007), SKIN)                          # the grin's corners in his cheeks
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.028, 0.05, 0.064)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.012, 0.032, 0.042)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
    # soot: streaked across his brow, over both cheeks, a smear on his left jaw
    for c, r, rot in (((0.03, -0.205, 1.815), (0.07, 0.014, 0.011), (0.1, 0.0, 0.15)),
                      ((-0.112, -0.15, 1.655), (0.034, 0.016, 0.012), (0.2, 0.0, -0.5)),
                      ((-0.1, -0.16, 1.625), (0.022, 0.012, 0.009), (0.2, 0.0, -0.35)),
                      ((0.12, -0.148, 1.648), (0.028, 0.014, 0.011), (0.2, 0.0, 0.42)),
                      ((0.13, -0.09, 1.54), (0.024, 0.02, 0.012), (0.0, 0.3, 0.6))):
        fd.paint(Ellipsoid(hp(c), v3(r) * HS * 1.4, R=euler(*rot)), SOOT)


def biceps(side):
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    return Ellipsoid(lerp(sh, el, 0.5) + v3((0, -0.028, 0)), (0.1, 0.104, 0.134), R=rot_from_axes(z_axis=el - sh))


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        fd.add(upper_arm(side), 0.05, SKIN)
        fd.add(biceps(side), 0.04, SKIN)
        fd.add(_forearm(side), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.1, 0.09, 0.13), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


def eyes_field():
    fd = Field("Eyes")
    for sx in (-1, 1):
        fd.add(Sphere(eye_c(sx), EYE_R))
    return fd


def teeth_field():
    """His upper teeth in the grin."""
    fd = Field("Teeth")
    for k in range(6):
        x = -0.05 + 0.02 * k
        y = -0.184 + 0.014 * (abs(x) / 0.05) ** 2
        fd.add(RoundBox(hp((x, y, 1.55 + 0.007 * (abs(x) / 0.05) ** 2)), v3((0.0096, 0.006, 0.011)) * HS, hr(0.003)), 0.002)
    return fd


# ======================================================================================= the helmet
HELM_C = HEAD_C + v3((0.0, 0.006, 0.018))
HELM_OUT = HEAD_RAD + v3((0.052, 0.05, 0.05))      # the helmet's outer shell ...
HELM_IN = HEAD_RAD + v3((0.022, 0.022, 0.026))     # ... and its inside (clear of his skull)
EDGE_Z0, EDGE_TILT = 1.736, 0.1                     # its edge: high over his brow, low at his nape


def _phi(P):
    """Angle round the helmet's axis from straight ahead (0) to behind (+-pi), + toward his left."""
    return np.arctan2(P[:, 0], -(P[:, 1] - F(HELM_C[1])))


def edge_z(P):
    return F(EDGE_Z0) + F(EDGE_TILT) * np.cos(_phi(P))


def helm_outer():
    return Ellipsoid(HELM_C, HELM_OUT)


def on_helmet(phi, dz, off=0.0):
    """A point on the helmet's outer surface at angle phi (round its axis from the front) and dz above its edge, and the
    outward normal there."""
    z = EDGE_Z0 + EDGE_TILT * math.cos(phi) + dz
    d = v3((math.sin(phi), -math.cos(phi), 0.0))
    o = v3((HELM_C[0], HELM_C[1], z)) + d * 0.7
    h, ok = ray_hit(helm_outer(), [o], [-d], tmax=0.7, step=0.001)
    q = h[0]
    n = norm((q - HELM_C) / (HELM_OUT ** 2))
    return q + n * off, n


def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.05, 1.588), (0.164, 0.142, 0.132)), 0.07)
    fd.add(E((0, -0.14, 1.497), (0.098, 0.074, 0.072)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.114, -0.128, 1.636)), hr(0.056)), 0.05)
        fd.add(Sphere(hp((sx * 0.14, -0.042, 1.552)), hr(0.057)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


def helmet_field():
    """Olive-drab paint (fieldgun label 0) chipped to the steel on its edges; black (8): the rubber trim round its edge,
    bolts along its sides."""
    fd = Field("Helmet")
    out, inn = helm_outer(), Ellipsoid(HELM_C, HELM_IN)
    lo, hi = HELM_C - HELM_OUT - 0.03, HELM_C + HELM_OUT + 0.03
    dent = lambda P: F(0.0012) * NOISE(P * F(14)) + F(0.0005) * NOISE(P * F(60))

    def shell(P):
        return smax(np.maximum(out(P), -inn(P)), edge_z(P) - P[:, 2], F(0.006))
    fd.add(Func(shell, lo, hi, disp=dent, disp_amp=0.0016), 0.0, OLIVE)
    # the rubber trim: a roll round the edge
    def trim(P):
        d = np.abs(P[:, 2] - edge_z(P) - F(0.008)) - F(0.01)
        return np.maximum(d, np.abs(out(P) + F(0.012)) - F(0.017))
    fd.add(Func(trim, lo, hi), 0.004, BLACK)
    # bolts along each side (a rail for the visor's pivots)
    for sx in (-1, 1):
        for k in range(3):
            q, n = on_helmet(sx * math.radians(76 + 16 * k), 0.034)
            fd.add(Sphere(q, 0.008), 0.003, BLACK)
    return fd


VIS_OFF, VIS_T = 0.012, 0.009          # the visor: this far out from the helmet, this thick
VIS_PHI = math.radians(74)             # its half width (round the helmet)
VIS_LO, VIS_HI = 0.05, 0.135           # its band: from this far above the helmet's edge to this far (at the front)
PIVOT_PHI = math.radians(96)


def _vis_band(P):
    """> 0 outside the visor's outline (lying flipped up over the helmet's front)."""
    phi = _phi(P)
    h = P[:, 2] - edge_z(P)
    taper = F(0.02) * (np.abs(phi) / F(VIS_PHI)) ** 2
    return np.maximum((np.abs(phi) - F(VIS_PHI)) * F(0.24), np.maximum(F(VIS_LO) + taper - h, h - F(VIS_HI) + taper * F(1.5)))


def visor_field():
    """Smoked glass (steamworks 13) in a black frame (12): the visor flipped up over the helmet's front; black arms back
    to its pivots on bosses at his temples."""
    fd = Field("Visor")
    out = helm_outer()
    lo, hi = HELM_C - HELM_OUT - 0.05, HELM_C + HELM_OUT + 0.05

    def plate(P):
        return np.maximum(np.abs(out(P) - F(VIS_OFF)) - F(VIS_T / 2), _vis_band(P))
    fd.add(Func(plate, lo, hi), 0.0, W_GLASS)

    def frame(P):
        b = _vis_band(P)
        return np.maximum(np.maximum(np.abs(out(P) - F(VIS_OFF)) - F(VIS_T / 2 + 0.003), b - F(0.003)), F(-0.011) - b)
    fd.add(Func(frame, lo, hi), 0.003, W_BLACK)
    # the arms and pivots
    for sx in (-1, 1):
        piv, n = on_helmet(sx * PIVOT_PHI, 0.042, 0.006)
        fd.add(Cylinder(piv, 0.026, 0.014, rr=0.005, R=rot_from_axes(z_axis=n)), 0.003, W_BLACK)
        fd.add(Sphere(piv + n * 0.008, 0.009), 0.003, W_STEEL)
        end, n2 = on_helmet(sx * (VIS_PHI - math.radians(5)), (VIS_LO + VIS_HI) / 2 - 0.004, VIS_OFF)
        mp, n3 = on_helmet(sx * (VIS_PHI + PIVOT_PHI) / 2, 0.06, VIS_OFF)
        fd.add(Lock([end, mp, piv + n * 0.006], [0.02, 0.017, 0.017], [0.006, 0.006, 0.006], [n2, n3, n], k=0.004), 0.004, W_BLACK)
    return fd


# ======================================================================================= hair (cropped short under the helmet)
def skull():
    return Ellipsoid(HEAD_C, HEAD_RAD)


def hair_field():
    """Dark hair cropped close: showing under the helmet at his temples, over his ears and at his nape."""
    fd = Field("Hair")
    stub = lambda P: F(0.0018) * NOISE(P * np.array([70, 70, 26], F)) + F(0.0008) * NOISE(P * F(140))

    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        face = np.where(ax < F(0.13), F(-0.08) - y, F(-0.125) - y)
        side = np.where((ax > F(0.12)) & (y < F(0.0)), F(1.69) - z, F(-1.0))
        ear = np.where((ax > F(0.15)) & (z < F(1.735)) & (np.abs(y - F(0.035)) < F(0.06)), F(0.02), F(-1.0))
        nape = F(1.6) - z
        return np.maximum(np.maximum(face, side), np.maximum(ear, nape))
    fd.add(Inter(Shell(skull(), 0.005, 0.01, pad=0.06, disp=stub, disp_amp=0.0025), Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.004), 0.0)
    return fd


# ======================================================================================= the suit
def arms_hull(fd=None, fore=True):
    af = fd or Field("Arms")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        af.add(deltoid(side), 0.055 if af.ops else 0.0)
        af.add(upper_arm(side), 0.05)
        af.add(biceps(side), 0.04)
        if fore:
            af.add(_forearm(side), 0.035)
            af.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.1, 0.09, 0.13), R=rot_from_axes(z_axis=wr - el)), 0.04)
            af.add(Sphere(el + v3((0, 0.025, 0)), 0.06), 0.028)
    return af


def jacket_hull():
    b = torso_hull()
    arms_hull(b)
    return b


JK_OFF, JK_T = 0.03, 0.018
JK_OUT = JK_OFF + JK_T * 0.5            # the jacket's outer surface (from jacket_hull)
JK_HEM = 0.7
CUFF_BACK = 0.04                        # the sleeves end this far short of the wrist (under the gloves' cuffs)


def _arm_axis(P, side, a_key, b_key):
    a, b = J[a_key + side], J[b_key + side]
    ax = norm(b - a)
    q = P - a.astype(F)
    along = q @ ax.astype(F)
    off = np.sqrt(np.maximum((q * q).sum(1) - along ** 2, 0))
    return along, off, float(np.linalg.norm(b - a))


def _cuff_cut(P):
    """> 0 past the sleeves' ends (only near each forearm)."""
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        along, off, L = _arm_axis(P, side, "elbow_", "wrist_")
        out = np.maximum(out, np.where((off < F(0.2)) & (along > F(0.05)), along - F(L - CUFF_BACK), F(-1.0)))
    return out


def _arm_band(P, side, a_key, b_key, t, half):
    along, off, L = _arm_axis(P, side, a_key, b_key)
    sx = -1 if side == "R" else 1
    on_arm = (off < F(0.19)) & (P[:, 0] * F(sx) > F(0.4))
    return np.where(on_arm, np.abs(along - F(t)) - F(half), F(1.0))


def _off_arms(P):
    """> 0 well away from both arms (the torso's own bands stop at the sleeves)."""
    out = np.full(len(P), F(1.0))
    for side in ("R", "L"):
        for a, b in (("shoulder_", "elbow_"), ("elbow_", "wrist_")):
            along, off, L = _arm_axis(P, side, a, b)
            t = np.clip(along, 0, F(L))
            d = np.sqrt(np.maximum(off ** 2 + (along - t) ** 2, 0))
            out = np.minimum(out, d - F(0.17))
    return out


def suit_field():
    """The fire suit's jacket: olive-drab cloth (label 0), reflective tan bands (7), charred grey (5) on its cuffs; a
    stand-up collar; a black zip (8) down its front."""
    fd = Field("Suit")
    jh = jacket_hull()
    folds = lambda P: F(0.0014) * NOISE(P * F(22)) + F(0.0024) * NOISE(P * np.array([6, 6, 12], F))

    def keep(P):
        hem = np.where(np.abs(P[:, 0]) < F(0.5), F(JK_HEM) - P[:, 2] + F(0.012) * np.sin(P[:, 0] * F(9)), F(-1.0))
        return np.maximum(np.maximum(neck_open(P, 0.15), hem), _cuff_cut(P))
    fd.add(Inter(Func(keep, (-0.95, -0.5, JK_HEM - 0.05), (0.95, 0.55, 1.62)), Shell(jh, JK_OFF, JK_T, pad=0.1, disp=folds, disp_amp=0.004), 0.004), 0.0)
    # the stand-up collar round his neck (lower at the front, under his chin)
    def collar(P):
        nd = neck_dist(P)
        top = F(1.5) - F(0.05) * smoothstep(0.0, -0.12, P[:, 1] - F(0.04))
        return np.maximum(np.abs(nd - F(0.142)) - F(0.012), np.maximum(F(1.36) - P[:, 2], P[:, 2] - top))
    fd.add(Func(collar, (-0.3, -0.3, 1.3), (0.3, 0.4, 1.56)), 0.012, CLOTH)
    # rolled hems at the cuffs (charred)
    arms = arms_hull()
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        L = float(np.linalg.norm(wr - el))
        c = el + ax * (L - CUFF_BACK - 0.012)
        fd.add(Inter(Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.014), c - 0.25, c + 0.25),
                     Shell(arms, JK_OFF + 0.006, 0.016, pad=0.08), 0.004), 0.004, CHAR)
    lo, hi = (-0.95, -0.6, 0.6), (0.95, 0.6, 1.65)
    # reflective bands: round his chest, his hem, his upper arms and his forearms
    def torso_only(P):
        return -_off_arms(P)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(1.165)) - F(0.024), torso_only(P)), lo, hi), TAN)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(JK_HEM + 0.045)) - F(0.022), torso_only(P)), lo, hi), TAN)
    for side in ("R", "L"):
        Lu = float(np.linalg.norm(J["elbow_" + side] - J["shoulder_" + side]))
        Lf = float(np.linalg.norm(J["wrist_" + side] - J["elbow_" + side]))
        fd.paint(Func(lambda P, s=side, Lu=Lu: _arm_band(P, s, "shoulder_", "elbow_", Lu * 0.7, 0.022), lo, hi), TAN)
        fd.paint(Func(lambda P, s=side, Lf=Lf: _arm_band(P, s, "elbow_", "wrist_", Lf - CUFF_BACK - 0.075, 0.022), lo, hi), TAN)
        # charred grey round the cuffs, in patches
        fd.paint(Func(lambda P, s=side, Lf=Lf: np.maximum(_arm_band(P, s, "elbow_", "wrist_", Lf - CUFF_BACK - 0.02, 0.03),
                                                         F(0.012) - NOISE(P * F(16)) * F(0.06)), lo, hi), CHAR)
    # the zip down his front
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 0] + F(0.03)) - F(0.008), np.maximum(P[:, 1] + F(0.05), F(0.74) - P[:, 2])), lo, hi), BLACK_C)
    return fd


TROUSER_TOP, TROUSER_LOW = 0.98, 0.24


def trousers_field():
    """Trousers of the same cloth (0), tucked into his boots; reflective tan bands round his shins (7), charred grey
    above the boots (5); black knee pads (8) on straps."""
    fd = Field("Trousers")
    lh = legs_hull()
    folds = lambda P: F(0.0016) * NOISE(P * np.array([25, 25, 50], F)) + F(0.003) * NOISE(P * np.array([6, 6, 3], F))
    fd.add(Inter(Func(lambda P: np.maximum(F(TROUSER_LOW) - P[:, 2], P[:, 2] - F(TROUSER_TOP)), (-0.42, -0.34, TROUSER_LOW - 0.02), (0.42, 0.34, TROUSER_TOP + 0.03)),
                 Shell(lh, 0.026, 0.016, pad=0.08, disp=folds, disp_amp=0.004), 0.004), 0.0)
    lo, hi = (-0.42, -0.4, 0.2), (0.42, 0.4, 1.02)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(0.395)) - F(0.022), lo, hi), TAN)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(0.31)) - F(0.04), F(0.012) - NOISE(P * F(14)) * F(0.06)), lo, hi), CHAR)
    for side in ("R", "L"):
        kn = J["knee_" + side]
        c = kn + v3((0.0, -0.118, 0.0))
        R = rot_from_axes(z_axis=(0, 0, 1), x_axis=(1, 0, 0))
        fd.add(Inter(Ellipsoid(c + v3((0, -0.0, 0.0)), (0.088, 0.05, 0.1)), Shell(shin_hull(side), 0.05, 0.026, pad=0.1), 0.006), 0.008, BLACK_C)
        sh = shin_hull(side)
        for dz in (-0.075, 0.07):
            fd.add(Inter(Func(lambda P, z0=kn[2] + dz: np.abs(P[:, 2] - F(z0)) - F(0.011), kn - 0.25, kn + 0.25),
                         Shell(sh, 0.045, 0.012, pad=0.08), 0.003), 0.004, BLACK_C)
    return fd


def gloves_field():
    """Heavy black leather gauntlet gloves (steamworks 12) over his fists, rubber pads (8) over the knuckles, a flared cuff
    over the sleeve's end, a strap round each wrist."""
    fd = Field("Gloves")
    for side in ("R", "L"):
        hull = Field("Hand")
        tips = hand(hull, side)
        lo, hi = hull.bounds()
        fd.add(Func(lambda P, h=hull: h.eval(P, margin=0.02) - F(0.009), lo - 0.03, hi + 0.03,
                    disp=lambda P: F(0.0008) * NOISE(P * F(50)), disp_amp=0.001), 0.0 if not fd.ops else 0.0, W_BLACK)
        wr, f, n, t = hand_frame(side)
        el = J["elbow_" + side]
        ax = norm(wr - el)
        # the cuff: flared over the sleeve, open at its end
        c0, c1 = wr - ax * 0.11, wr + ax * 0.012
        fd.add(RoundCone(c0, c1, 0.112, 0.082), 0.02, W_BLACK)
        fd.sub(Cylinder(c0 - ax * 0.005, 0.098, 0.03, R=rot_from_axes(z_axis=ax)), 0.006)
        fd.add(Torus(wr - ax * 0.03, 0.094, 0.008, R=rot_from_axes(z_axis=ax)), 0.004, W_BLACK)
        # knuckle pads
        for pts in tips:
            k = pts[1]
            fd.add(Sphere(k - n * 0.006 + f * 0.004, 0.019), 0.006, W_RUBBER)
        fd.add(RoundBox(wr + f * 0.085 - n * 0.04, (0.062, 0.012, 0.04), 0.01, R=np.stack([t, n, f], axis=1)), 0.012, W_RUBBER)
    return fd


def boots_field():
    """High black leather boots (steamworks 12) to mid-shin, a padded collar, thick rubber lug soles (8), a toe cap."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        fh = foot_hull(side)
        sh = shin_hull(side)
        fd.add(Inter(Func(lambda P: P[:, 2] - F(0.2), an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.2))),
                     Shell(fh, 0.012, 0.016, pad=0.06, disp=lambda P: F(0.0012) * NOISE(P * F(30)), disp_amp=0.0015), 0.004), 0.0, W_BLACK)
        fd.add(Inter(Func(lambda P: np.maximum(F(0.11) - P[:, 2], P[:, 2] - F(0.3)), an - v3((0.25, 0.25, 0.1)), an + v3((0.25, 0.25, 0.3))),
                     Shell(sh, 0.044, 0.016, pad=0.08, disp=lambda P: F(0.001) * NOISE(P * F(30)), disp_amp=0.0015), 0.004), 0.012, W_BLACK)
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        lug = lambda P: F(0.0018) * np.sign(np.sin(P[:, 1] * F(160)))
        fd.add(RoundBox(an + fwd * 0.076 + v3((0, 0, -0.092)), (0.088, 0.17, 0.022), 0.012, R=Rz, disp=lug, disp_amp=0.002), 0.006, W_RUBBER)
        fd.add(RoundBox(an + fwd * -0.02 + v3((0, 0, -0.08)), (0.07, 0.058, 0.03), 0.012, R=Rz), 0.006, W_RUBBER)
        fd.add(Ellipsoid(an + fwd * 0.17 + v3((0, 0, -0.058)), (0.074, 0.072, 0.052), R=Rz), 0.02, W_BLACK)
        fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(0.3)) - F(0.016), an - 0.3, an + 0.3), Shell(sh, 0.054, 0.018, pad=0.08), 0.004), 0.004, W_BLACK)
        # laces up the front (a few crossings)
        for k in range(5):
            z = 0.14 + 0.035 * k
            c = an + fwd * (0.07 - 0.012 * k) + v3((0, 0, z - an[2]))
            h, ok = ray_hit(Func(lambda P, sh=sh, fh=fh: np.minimum(sh.eval(P, margin=0.1), fh.eval(P, margin=0.1)) - F(0.06), an - 0.4, an + 0.4),
                            [c + fwd * 0.3], [-fwd], tmax=0.4)
            if ok[0]:
                fd.add(RoundBox(h[0], (0.03, 0.004, 0.005), 0.003, R=Rz), 0.002, W_STEEL)
    return fd


# ======================================================================================= harness (coyote) and gauge
def jacket_outer(lift=0.0):
    jh = jacket_hull()
    hull = Field("JacketOuter")
    hull.add(Func(lambda P: jh.eval(P, margin=0.1) - F(JK_OUT + lift), (-0.75, -0.7, 0.6), (0.75, 0.7, 1.75)), 0.0)
    return hull


def _on_jacket(pts, lift=0.008):
    hull = jacket_outer(lift)
    pp = project_to(hull, [v3(p) for p in pts], iters=4)
    ns = grad(hull, pp.astype(F)).astype(np.float64)
    return [v3(p) for p in pp], [v3(n) for n in ns]


def strap_path(sx):
    return [(sx * 0.12, 0.33, 1.44), (sx * 0.155, 0.23, 1.52), (sx * 0.165, 0.08, 1.55), (sx * 0.168, -0.07, 1.5),
            (sx * 0.165, -0.2, 1.38), (sx * 0.16, -0.27, 1.22), (sx * 0.152, -0.28, 1.06), (sx * 0.145, -0.27, 0.93)]


STERNUM_Z = 1.275
BELT_Z = 0.885
BELT_HW = 0.036


def belt_base():
    b = Field("BeltBase")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    b.add(RoundCone((0, 0.035, 0.98), (0, 0.035, 0.6), 0.26, 0.335), 0.08)
    return b


def gauge_frame():
    """The pressure gauge on the left shoulder strap at his chest: its face's centre and outward normal."""
    pts, ns = _on_jacket([(0.166, -0.205, 1.36)], lift=0.02)
    n = norm(ns[0] + v3((0.0, -0.2, 0.75)))
    return pts[0] + ns[0] * 0.022, n


GAUGE_R = 0.044


def harness_field():
    """Coyote-tan webbing (uniform label 0) with black buckles (8): the shoulder straps, the sternum strap, the padded hip
    belt, two pouches on his left hip."""
    fd = Field("Harness")
    for sx in (-1, 1):
        pts, ns = _on_jacket(strap_path(sx))
        fd.add(Lock(pts, [0.042] * len(pts), [0.009] * len(pts), ns, k=0.006, disp=lambda P: F(0.0006) * NOISE(P * F(60)), disp_amp=0.0008), 0.004, CLOTH)
        # an adjuster buckle on each strap at his chest
        i = 5
        d = norm(pts[i + 1] - pts[i - 1])
        R = rot_from_axes(z_axis=ns[i], y_axis=d)
        fd.add(RoundBox(pts[i] + ns[i] * 0.009, (0.05, 0.016, 0.005), 0.004, R=R), 0.003, BLACK_C)
    # the sternum strap and its buckle
    xs = np.linspace(-0.17, 0.17, 9)
    pts, ns = _on_jacket([(x, -0.33, STERNUM_Z) for x in xs], lift=0.022)
    fd.add(Lock(pts, [0.026] * len(pts), [0.007] * len(pts), ns, k=0.006), 0.004, CLOTH)
    c, n = pts[4], ns[4]
    R = rot_from_axes(z_axis=n, x_axis=(1, 0, 0))
    fd.add(RoundBox(c + n * 0.008, (0.034, 0.024, 0.008), 0.006, R=R), 0.003, BLACK_C)
    # the hip belt (padded) over the jacket, its buckle in front
    bb = belt_base()
    off = JK_OUT + 0.012
    band = lambda P: np.abs(P[:, 2] - F(BELT_Z) - F(0.012) * smoothstep(-0.1, 0.25, P[:, 1])) - F(BELT_HW)
    fd.add(Inter(Func(band, (-0.6, -0.6, BELT_Z - 0.08), (0.6, 0.6, BELT_Z + 0.08)), Shell(bb, off + 0.01, 0.02, pad=0.1,
                 disp=lambda P: F(0.0008) * NOISE(P * F(50)), disp_amp=0.001), 0.006), 0.0, CLOTH)
    outer = Func(lambda P: bb.eval(P, margin=0.12) - F(off + 0.02), (-0.7, -0.7, 0.7), (0.7, 0.7, 1.1))
    h, ok = ray_hit(outer, [v3((0, -0.7, BELT_Z))], [v3((0, 1, 0))], tmax=0.7)
    bc = h[0]
    Rb = rot_from_axes(z_axis=(0, -1, 0), x_axis=(1, 0, 0))
    fd.add(RoundBox(bc + v3((0, -0.006, 0)), (0.05, 0.034, 0.012), 0.008, R=Rb), 0.004, BLACK_C)
    fd.sub(RoundBox(bc + v3((0, -0.018, 0)), (0.03, 0.016, 0.006), 0.003, R=Rb), 0.002)
    # pouches on his left hip (two), a flap over each
    for ang in (0.62, 1.12):
        d = v3((math.sin(ang), -math.cos(ang), 0.0))
        h, ok = ray_hit(outer, [v3((0, 0.035, BELT_Z - 0.02)) + d * 0.7], [-d], tmax=0.7)
        if not ok[0]:
            continue
        p = h[0] + d * 0.04
        R = rot_from_axes(z_axis=d, y_axis=(0, 0, 1))
        fd.add(RoundBox(p + v3((0, 0, -0.03)), (0.052, 0.07, 0.032), 0.014, R=R, disp=lambda P: F(0.0008) * NOISE(P * F(40)), disp_amp=0.001), 0.006, CLOTH)
        fd.add(RoundBox(p + d * 0.022 + v3((0, 0, 0.025)), (0.056, 0.026, 0.014), 0.008, R=R), 0.004, CLOTH)
        fd.add(RoundBox(p + d * 0.038 + v3((0, 0, 0.008)), (0.012, 0.014, 0.004), 0.003, R=R), 0.002, BLACK_C)
    return fd


def gauge_field():
    """The pressure gauge (steamworks): a brass bezel (5), a cream dial (10), a black needle (12), a red sector (11); its
    black rubber line (8) up the strap and over his shoulder; a black clip on the strap."""
    fd = Field("Gauge")
    c, n = gauge_frame()
    R = rot_from_axes(z_axis=n)
    fd.add(Cylinder(c, GAUGE_R, 0.028, rr=0.008, R=R), 0.0, W_BRASS)
    fd.sub(Cylinder(c + n * 0.014, GAUGE_R - 0.008, 0.014, rr=0.002, R=R), 0.002)
    face = c + n * 0.006
    fd.add(Cylinder(face, GAUGE_R - 0.008, 0.004, R=R), 0.001, W_ENAMEL)
    gx = norm(np.cross(n, v3((0, 0, 1))))
    gy = np.cross(n, gx)
    tip = face + n * 0.003 + (gx * math.cos(2.0) + gy * math.sin(2.0)) * 0.028
    fd.add(RoundCone(face + n * 0.003, tip, 0.0036, 0.0018), 0.001, W_BLACK)

    def red(P):
        q = P - face.astype(F)
        a = np.arctan2(q @ gy.astype(F), q @ gx.astype(F))
        r = np.sqrt((q @ gx.astype(F)) ** 2 + (q @ gy.astype(F)) ** 2)
        return np.maximum(np.maximum(np.abs(a - F(0.4)) * r - F(0.012), np.abs(r - F(0.029)) - F(0.006)), np.abs(q @ n.astype(F)) - F(0.01))
    fd.paint(Func(red, face - 0.07, face + 0.07), W_RED)
    # the line: from the gauge's back, up the strap, over his left shoulder to the tanks
    path = [(0.19, -0.2, 1.39), (0.195, -0.14, 1.47), (0.2, -0.04, 1.535), (0.2, 0.1, 1.57), (0.19, 0.24, 1.53), (0.16, 0.36, 1.47)]
    pts, ns = _on_jacket(path, lift=0.03)
    pts = [c - n * 0.012] + pts
    fd.add(Chain(pts, [0.011] * len(pts), k=0.008), 0.004, W_RUBBER)
    fd.add(RoundBox(pts[2] - ns[1] * 0.004, (0.02, 0.016, 0.006), 0.004, R=rot_from_axes(z_axis=ns[1], y_axis=norm(pts[3] - pts[1]))), 0.003, W_BLACK)
    return fd


def patch_field():
    """The unit patch on his left shoulder: red (uniform label 0) with a white bar (7) across it."""
    fd = Field("Patch")
    sh, el = J["shoulder_L"], J["elbow_L"]
    p0 = lerp(sh, el, 0.28) + v3((0.16, -0.01, 0.06))
    arms = arms_hull(fore=False)
    outer = Field("SleeveOuter")
    outer.add(Func(lambda P: arms.eval(P, margin=0.12) - F(JK_OUT + 0.004), np.minimum(sh, el) - 0.4, np.maximum(sh, el) + 0.4), 0.0)
    c = project_to(outer, [p0], iters=5)[0]
    nrm = grad(outer, np.array([c], F))[0].astype(np.float64)
    up = norm((sh - el) - nrm * ((sh - el) @ nrm))
    R = rot_from_axes(z_axis=nrm, y_axis=up)
    fd.add(RoundBox(c, (0.036, 0.05, 0.004), 0.004, R=R), 0.0)
    fd.paint(RoundBox(c, (0.05, 0.012, 0.02), 0.002, R=R), 7)
    return fd


# ======================================================================================= the fuel unit (rigid with his chest)
# drawn upright in its own frame, then tilted back at the foot (TK_TILT) about TK_PIV so it lies along his back
TANK_X, TANK_Y, TANK_R = 0.132, 0.478, 0.112
TANK_Z0, TANK_Z1 = 0.86, 1.44
SPHERE_C0 = (0.0, 0.612, 1.16)
SPHERE_R = 0.088
PLATE_Y = 0.35
TK_PIV = v3((0.0, 0.35, 1.16))
TK_TILT = 0.1
TK_R = euler(TK_TILT, 0.0, 0.0)
BAND_Z = (1.27, 1.335)


def tk(p):
    """A point of the fuel unit (drawn upright) where it is on his back."""
    return TK_PIV + TK_R @ (v3(p) - TK_PIV)


def tk_inv(P):
    return ((P - TK_PIV.astype(F)) @ TK_R.astype(F)) + TK_PIV.astype(F)


OUTLET = tk((-0.235, TANK_Y, 0.83))      # the outlet valve on his right (the hose's start)
OUTLET_D = norm(TK_R @ v3((-0.6, -0.1, -0.8)))


def tanks_field():
    """Fieldgun paint: gunmetal tanks (5) with hazard bands (12: yellow on these, with black (8) stripes), steel straps and
    lines (7), brass filler caps, regulator and outlet valve (6); the olive pressure sphere (0); the black frame (8)."""
    fd = Field("Tanks")
    up = TK_R @ v3((0, 0, 1))
    zc, hh = (TANK_Z0 + TANK_Z1) / 2, TANK_Z1 - TANK_Z0
    dent = lambda P: F(0.0008) * NOISE(P * F(20))
    for sx in (-1, 1):
        fd.add(Cylinder(tk((sx * TANK_X, TANK_Y, zc)), TANK_R, hh, rr=0.055, R=TK_R, disp=dent, disp_amp=0.001), 0.0, GUNMETAL)
        for z in (TANK_Z0 + 0.08, TANK_Z1 - 0.08):                                     # weld seams
            fd.add(Torus(tk((sx * TANK_X, TANK_Y, z)), TANK_R, 0.0045, R=TK_R), 0.002, GUNMETAL)
        fd.add(Cylinder(tk((sx * TANK_X, TANK_Y, TANK_Z1 + 0.008)), 0.03, 0.03, rr=0.008, R=TK_R), 0.008, BRASS)   # filler cap
        fd.add(Cylinder(tk((sx * TANK_X, TANK_Y, TANK_Z1 + 0.026)), 0.036, 0.012, rr=0.004, R=TK_R), 0.003, BRASS)
        for z in (TANK_Z0 + 0.17, TANK_Z1 - 0.21):                                     # steel straps
            fd.add(Torus(tk((sx * TANK_X, TANK_Y, z)), TANK_R + 0.005, 0.011, R=TK_R), 0.003, STEEL)
    # the hazard bands
    def band(P):
        Q = tk_inv(P)
        r = np.sqrt((np.abs(Q[:, 0]) - F(TANK_X)) ** 2 + (Q[:, 1] - F(TANK_Y)) ** 2)
        return np.maximum(np.abs(Q[:, 2] - F((BAND_Z[0] + BAND_Z[1]) / 2)) - F((BAND_Z[1] - BAND_Z[0]) / 2), r - F(TANK_R + 0.01))
    lo, hi = (-0.3, 0.25, 1.15), (0.3, 0.7, 1.42)
    fd.paint(Func(band, lo, hi), RED)

    def stripes(P):
        Q = tk_inv(P)
        a = np.arctan2(Q[:, 1] - F(TANK_Y), np.abs(Q[:, 0]) - F(TANK_X)) * F(TANK_R)
        s = np.sin((a + Q[:, 2]) * F(70))
        return np.maximum(band(P) + F(0.004), F(0.15) - s)
    fd.paint(Func(stripes, lo, hi), BLACK)
    # the pressure sphere set back between them, its regulator and the lines to the tanks
    sc = tk(SPHERE_C0)
    fd.add(Sphere(sc, SPHERE_R, disp=dent, disp_amp=0.001), 0.006, OLIVE)
    fd.add(Torus(sc, SPHERE_R, 0.005, R=TK_R @ rot_from_axes(z_axis=(1, 0, 0))), 0.002, OLIVE)
    rg = tk((0.0, 0.58, 1.44))
    fd.add(Chain([sc + up * SPHERE_R * 0.9, tk((0.0, 0.61, 1.33)), rg], [0.014] * 3, k=0.006), 0.004, STEEL)
    fd.add(RoundBox(rg, (0.032, 0.026, 0.024), 0.01, R=TK_R), 0.006, BRASS)
    fd.add(Cylinder(rg + up * 0.03, 0.012, 0.02, rr=0.004, R=TK_R), 0.003, BRASS)
    for sx in (-1, 1):
        fd.add(Chain([rg + TK_R @ v3((sx * 0.025, 0, 0)), tk((sx * 0.08, 0.56, 1.45)), tk((sx * TANK_X * 0.7, TANK_Y + 0.03, TANK_Z1 + 0.01))],
                     [0.01] * 3, k=0.005), 0.003, STEEL)
    # the manifold across the tanks' feet, the outlet valve on his right
    for sx in (-1, 1):
        fd.add(RoundCone(tk((sx * TANK_X, TANK_Y, TANK_Z0 + 0.02)), tk((sx * TANK_X, TANK_Y, TANK_Z0 - 0.04)), 0.018, 0.018), 0.004, STEEL)
    m0, m1 = tk((-TANK_X, TANK_Y, TANK_Z0 - 0.04)), tk((TANK_X, TANK_Y, TANK_Z0 - 0.04))
    fd.add(RoundCone(m0, m1, 0.017, 0.017), 0.004, STEEL)
    fd.add(Chain([m0, tk((-0.2, TANK_Y, TANK_Z0 - 0.045)), OUTLET], [0.017] * 3, k=0.01), 0.004, STEEL)
    fd.add(RoundBox(OUTLET - OUTLET_D * 0.005, (0.026, 0.026, 0.03), 0.008, R=rot_from_axes(z_axis=OUTLET_D)), 0.004, BRASS)
    wc = OUTLET + TK_R @ v3((0.0, 0.045, 0.03))
    fd.add(RoundCone(OUTLET, wc, 0.006, 0.006), 0.002, STEEL)
    fd.add(Torus(wc, 0.024, 0.006, R=rot_from_axes(z_axis=TK_R @ v3((0, 1, 0.3)))), 0.002, BLACK)
    # the frame against his back: a plate, two side rails, a cross bar at the top
    fd.add(RoundBox(tk((0.0, PLATE_Y, 1.16)), (0.19, 0.016, 0.31), 0.012, R=TK_R), 0.006, BLACK)
    for sx in (-1, 1):
        fd.add(RoundCone(tk((sx * 0.17, PLATE_Y + 0.012, 0.86)), tk((sx * 0.17, PLATE_Y + 0.02, 1.47)), 0.016, 0.016), 0.006, BLACK)
    fd.add(RoundCone(tk((-0.17, PLATE_Y + 0.02, 1.47)), tk((0.17, PLATE_Y + 0.02, 1.47)), 0.016, 0.016), 0.006, BLACK)
    return fd


# ======================================================================================= the flamethrower
GUN_G0 = v3((-0.34, -0.5, 0.9))         # rest: the rear grip's middle (floating before his right hip) ...
GUN_A0 = v3((0.0, -1.0, 0.0))           # ... the nozzle pointing ahead
GUN_U0 = v3((0.0, 0.0, 1.0))
GUN_S0 = np.cross(GUN_A0, GUN_U0)       # (his right: the gun's right side)
BORE_H = 0.1                            # the bore above the grip's middle
NOZZLE_U = 0.905                        # the nozzle's tip
FORE_U = 0.3                            # the front grip
PILOT_U = 0.918                         # the pilot flame's foot (just ahead of the igniter's spout, under the nozzle)
PILOT_H = 0.044


def gp(u, v=0.0, h=0.0):
    """A point of the gun (gun coordinates: u along the bore, v to its right, h up from the rear grip's middle), rest."""
    return GUN_G0 + GUN_A0 * u + GUN_S0 * v + GUN_U0 * h


def grip_axis():
    """The rear pistol grip's axis (from its foot up toward the receiver)."""
    return norm(GUN_U0 * 0.93 + GUN_A0 * 0.36)


def nozzle_tip():
    return gp(NOZZLE_U, 0.0, BORE_H)


def bore_rear():
    return gp(0.0, 0.0, BORE_H)


def pilot_base():
    return gp(PILOT_U, 0.0, PILOT_H)


def hose_inlet():
    """The hose's brass fitting under the receiver's rear: its end and the direction the hose leaves it."""
    return gp(-0.1, 0.0, 0.016), norm(-GUN_A0 * 0.55 - GUN_U0 * 0.85)


def gun_field():
    """Fieldgun paint: the olive receiver (0), gunmetal (5): the fuel tube, the rear cap, the clamps, the igniter housing;
    black polymer (8): the grips, the heat shield; bright steel (7): the nozzle, the shield's bands; brass (6): the
    igniter line and the hose fitting; the red valve wheel (12)."""
    fd = Field("Gun")
    A, U, S = GUN_A0, GUN_U0, GUN_S0
    Rg = np.stack([S, A, U], 1)
    RA = rot_from_axes(z_axis=A)
    poly = lambda P: F(0.0006) * NOISE(P * F(80))
    # the rear pistol grip and its trigger guard
    ga = grip_axis()
    gs = norm(np.cross(ga, S))
    Rgr = np.stack([S, gs, ga], 1)
    fd.add(RoundBox(gp(0.0, 0.0, -0.006), (0.021, 0.028, 0.064), 0.016, R=Rgr, disp=poly, disp_amp=0.001), 0.0, BLACK)
    for k in range(3):                                                                   # finger grooves
        fd.sub(RoundCone(gp(0.026, -0.03, -0.035 + 0.028 * k), gp(0.026, 0.03, -0.035 + 0.028 * k), 0.006, 0.006), 0.004)
    fd.add(Ellipsoid(gp(-0.012, 0.0, -0.072), (0.026, 0.032, 0.012), R=Rgr), 0.006, BLACK)
    fd.add(Chain([gp(0.03, 0.0, 0.056), gp(0.045, 0.0, 0.006), gp(0.1, 0.0, 0.004), gp(0.118, 0.0, 0.052)], [0.0055] * 4, k=0.003), 0.003, BLACK)
    fd.add(RoundCone(gp(0.062, 0.0, 0.054), gp(0.07, 0.0, 0.026), 0.007, 0.005), 0.002, STEEL)
    # the receiver: an olive block, a panel line and screws on its sides
    fd.add(RoundBox(gp(0.04, 0.0, 0.1), (0.054, 0.115, 0.062), 0.02, R=Rg), 0.012, OLIVE)
    for sv in (-1, 1):
        fd.sub(RoundBox(gp(0.04, sv * 0.055, 0.1), (0.004, 0.08, 0.04), 0.004, R=Rg), 0.002)
        for u in (-0.03, 0.11):
            fd.add(Sphere(gp(u, sv * 0.054, 0.1), 0.0075), 0.002, STEEL)
    # the rear cap and the hose fitting under it
    fd.add(Cylinder(gp(-0.078, 0.0, 0.1), 0.056, 0.03, rr=0.012, R=RA), 0.006, GUNMETAL)
    hi_, hd = hose_inlet()
    f0 = gp(-0.058, 0.0, 0.055)
    fd.add(RoundCone(f0, hi_, 0.02, 0.019), 0.006, BRASS)
    fd.add(Cylinder(lerp(f0, hi_, 0.45), 0.026, 0.022, rr=0.004, R=rot_from_axes(z_axis=norm(hi_ - f0))), 0.003, BRASS)
    # the valve wheel on top (red), its stem and gland
    vb = gp(0.02, 0.0, 0.163)
    fd.add(Cylinder(vb, 0.02, 0.018, rr=0.005, R=rot_from_axes(z_axis=U)), 0.004, GUNMETAL)
    fd.add(RoundCone(vb, vb + U * 0.045, 0.008, 0.008), 0.003, STEEL)
    wc = vb + U * 0.05
    fd.add(Torus(wc, 0.044, 0.01, R=rot_from_axes(z_axis=U)), 0.0, RED)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        e = S * math.cos(a) + A * math.sin(a)
        fd.add(RoundCone(wc, wc + e * 0.042, 0.0075, 0.007), 0.003, RED)
    fd.add(Sphere(wc, 0.014), 0.003, RED)
    # the fuel tube
    fd.add(RoundCone(gp(0.15, 0.0, BORE_H), gp(0.82, 0.0, BORE_H), 0.033, 0.033), 0.008, GUNMETAL)
    fd.add(Cylinder(gp(0.165, 0.0, BORE_H), 0.043, 0.032, rr=0.009, R=RA), 0.006, GUNMETAL)
    # the heat shield over its front half: black, perforated, steel bands at its ends
    s0, s1 = 0.48, 0.8
    fd.add(Cylinder(gp((s0 + s1) / 2, 0.0, BORE_H), 0.053, s1 - s0, rr=0.01, R=RA), 0.006, BLACK)
    for i, u in enumerate(np.linspace(s0 + 0.035, s1 - 0.035, 7)):
        for k in range(8):
            a = 2 * math.pi * (k + 0.5 * (i % 2)) / 8
            e = S * math.cos(a) + U * math.sin(a)
            fd.sub(Sphere(gp(u, 0.0, BORE_H) + e * 0.057, 0.0105), 0.002)
    for u in (s0, s1):
        fd.add(Torus(gp(u, 0.0, BORE_H), 0.054, 0.008, R=RA), 0.003, STEEL)
    # the nozzle, flared at its mouth
    fd.add(RoundCone(gp(0.81, 0.0, BORE_H), gp(NOZZLE_U - 0.005, 0.0, BORE_H), 0.038, 0.052), 0.006, STEEL)
    fd.add(Torus(gp(NOZZLE_U - 0.01, 0.0, BORE_H), 0.048, 0.009, R=RA), 0.003, STEEL)
    fd.sub(Cylinder(gp(NOZZLE_U, 0.0, BORE_H), 0.029, 0.07, rr=0.003, R=RA), 0.003)
    # the front grip on its clamp
    fd.add(RoundBox(gp(FORE_U, 0.0, 0.09), (0.046, 0.032, 0.05), 0.014, R=Rg), 0.006, GUNMETAL)
    fd.add(RoundCone(gp(FORE_U, 0.0, 0.06), gp(FORE_U - 0.008, 0.0, -0.07), 0.021, 0.024, disp=poly, disp_amp=0.001), 0.006, BLACK)
    fd.add(Ellipsoid(gp(FORE_U - 0.009, 0.0, -0.076), (0.027, 0.027, 0.012), R=Rg), 0.005, BLACK)
    # the igniter line under the tube, its clamps, the igniter housing under the nozzle and its spout
    fd.add(RoundCone(gp(0.13, 0.0, 0.035), gp(0.835, 0.0, 0.035), 0.0095, 0.0095), 0.003, BRASS)
    for u in (0.28, 0.6):
        fd.add(RoundBox(gp(u, 0.0, 0.06), (0.013, 0.013, 0.03), 0.005, R=Rg), 0.003, GUNMETAL)
    fd.add(RoundBox(gp(0.86, 0.0, 0.04), (0.026, 0.032, 0.022), 0.009, R=Rg), 0.006, GUNMETAL)
    fd.add(RoundCone(gp(0.885, 0.0, 0.04), gp(PILOT_U - 0.004, 0.0, PILOT_H), 0.009, 0.007), 0.002, STEEL)
    return fd


def pilot_field():
    """The pilot flame (its own glowing mesh on the `pilot` bone): a little teardrop flame licking forward and up from the
    igniter's spout under the nozzle's mouth."""
    fd = Field("Pilot")
    b = pilot_base()
    A, U = GUN_A0, GUN_U0
    pts = [b, b + A * 0.035 + U * 0.008, b + A * 0.068 + U * 0.03, b + A * 0.095 + U * 0.058]
    fd.add(Chain(pts, [0.024, 0.026, 0.017, 0.004], k=0.012), 0.0)
    return fd


# ======================================================================================= the hose (tanks -> gun)
HOSE_R = 0.022


def hose_pts(n=8):
    """The hose's centre line (rest pose): from the outlet valve on his right, down and round the outside of his right
    thigh, and up into the gun's fitting."""
    hi_, hd = hose_inlet()
    o = OUTLET + OUTLET_D * 0.03
    ctrl = [o, o + OUTLET_D * 0.06, v3((-0.4, 0.32, 0.7)), v3((-0.48, 0.12, 0.6)), v3((-0.5, -0.12, 0.6)),
            v3((-0.45, -0.3, 0.7)), hi_ + hd * 0.09, hi_ + hd * 0.012]
    P = [ctrl[0]] + ctrl + [ctrl[-1]]
    out = []
    for i in range(1, len(P) - 2):
        for k in range(n):
            t = k / float(n)
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(ctrl[-1])
    return out


def hose_field():
    """Ribbed black rubber (steamworks 8), a brass clamp (5) at each end."""
    fd = Field("Hose")
    pts = hose_pts()
    o = pts[0]
    ribs = lambda P: F(0.0016) * np.sin(np.sqrt(((P - o.astype(F)) ** 2).sum(1)) * F(240))
    fd.add(Chain(pts, [HOSE_R] * len(pts), k=0.004, disp=ribs, disp_amp=0.002), 0.0, W_RUBBER)
    for p, q in ((pts[1], pts[2]), (pts[-2], pts[-4])):
        d = norm(q - p)
        fd.add(Torus(p + d * 0.004, HOSE_R + 0.002, 0.0065, R=rot_from_axes(z_axis=d)), 0.002, W_BRASS)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.62)), 0.05, 0.55)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.112, -0.15, 1.63)), 0.065, 0.7), (hp((sx * 0.18, 0.035, 1.664)), 0.055, 0.6)]
    pts.append((hp((0.0, -0.24, 1.625)), 0.04, 0.55))
    return pts


# ======================================================================================= build config
GLB_NAME = "flamethrower"
ROOT_NAME = "FlamethrowerHQ"
TEX_PREFIX = "flame"
MAT_NAME = "FlamethrowerMat"
MESH_NAME = "Flamethrower"
BASE_MODULE = "flamethrower_base"
ANIM_MODULE = "anim_flamethrower"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Helmet", "Visor", "Suit", "Trousers", "Gloves", "Boots", "Harness", "Gauge",
         "Patch", "Tanks", "Hose", "Gun", "Pilot"]
REGION_PARTS = ("Skin", "Helmet", "Visor", "Suit", "Trousers", "Gloves", "Boots", "Harness", "Gauge", "Patch", "Tanks", "Hose",
                "Gun")
GEAR = {"name": "HQ_FlameGear", "glass": (0.2, 0.15, 0.1), "leather": (0.3, 0.2, 0.12)}
KIT = {"name": "HQ_FlameGun", "olive": (0.36, 0.38, 0.24), "grey": (0.27, 0.29, 0.31), "red": (0.74, 0.1, 0.07)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_FlameSkin", "base": (0.82, 0.58, 0.44), "ruddy": (0.86, 0.46, 0.36), "lips": (0.68, 0.38, 0.33),
                      "brow": ((0.08, 0.055, 0.04), (0.18, 0.12, 0.08)),
                      "extra": ((LASH, (0.08, 0.05, 0.035), 0.5), (STUBBLE, (0.44, 0.33, 0.27), 0.6, 0.45),
                                (SOOT, (0.11, 0.1, 0.095), 0.65, 0.8))}),
    "Hair": ("hair", {"name": "HQ_FlameHair", "base": (0.12, 0.085, 0.06), "hi": (0.3, 0.22, 0.16), "low": (0.05, 0.035, 0.025),
                      "streak": (0.08, 0.055, 0.04), "tint": (0.18, 0.12, 0.08)}),
    "Helmet": ("fieldgun", {"name": "HQ_FlameHelmet", "olive": OLIVE_DRAB}),
    "Visor": ("steamworks", GEAR),
    "Suit": ("uniform", {"name": "HQ_FlameSuit", "base": OLIVE_DRAB, "facing": (0.24, 0.235, 0.22), "buff": (0.8, 0.7, 0.5),
                         "black": (0.06, 0.055, 0.055)}),
    "Trousers": ("uniform", {"name": "HQ_FlameSuit", "base": OLIVE_DRAB, "facing": (0.24, 0.235, 0.22), "buff": (0.8, 0.7, 0.5),
                             "black": (0.06, 0.055, 0.055)}),
    "Gloves": ("steamworks", GEAR),
    "Boots": ("steamworks", GEAR),
    "Harness": ("uniform", {"name": "HQ_FlameHarness", "base": COYOTE, "black": (0.06, 0.055, 0.055)}),
    "Gauge": ("steamworks", GEAR),
    "Patch": ("uniform", {"name": "HQ_FlamePatch", "base": (0.7, 0.09, 0.07), "buff": (0.94, 0.92, 0.88)}),
    "Tanks": ("fieldgun", {"name": "HQ_FlameTanks", "olive": (0.36, 0.38, 0.24), "grey": (0.3, 0.32, 0.34), "red": (0.92, 0.7, 0.1)}),
    "Hose": ("steamworks", GEAR),
    "Gun": ("fieldgun", KIT),
    "Pilot": ("glow_ball", {"name": "HQ_PilotFlame", "col": (1.0, 0.6, 0.15)}),
}
GLOW = {"Pilot": ((1.0, 0.56, 0.12), 1.4, 0.5)}
LOW_TARGETS = {"Skin": 5000, "Teeth": 80, "Hair": 300, "Helmet": 1500, "Visor": 700, "Suit": 3600, "Trousers": 1500,
               "Gloves": 1500, "Boots": 1100, "Harness": 1900, "Gauge": 300, "Patch": 60, "Tanks": 2600, "Hose": 700,
               "Gun": 2700, "Pilot": 80}
AO_EXCLUDE = ["Gun", "Hose", "Patch", "Gauge", "Visor"]
# the gun floats before his right hip at rest: baked well away from him (no shadow of it on his jacket, nor of him on it)
BAKE_APART = (["Gun"], (3.0, 0.0, 0.0))


def prop_bones():
    """The gun rides a parentless bone (`flamer`: from the bore over the rear grip to the nozzle's tip, along the bore;
    every clip poses it in world space); the pilot flame a child of it (`pilot`, scaled by the clips)."""
    pb = pilot_base()
    return [("flamer", bore_rear(), nozzle_tip(), None),
            ("pilot", pb, pb + GUN_A0 * 0.06, "flamer")]


BODY_ARMS = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}


def _clear(ob, v):
    for g in list(ob.vertex_groups):
        g.remove([v.index])


def suit_weights(ob, skin_ob, arm):
    import rig
    rig.transfer_weights(skin_ob, ob, allowed=BODY_ARMS | {"thigh.R", "thigh.L"}, caps={"thigh.R": 0.45, "thigh.L": 0.45})


def hose_weights(ob, skin_ob, arm):
    """Along the hose: rigid with his chest at the tanks, with his hips round his thigh, with the gun at its fitting."""
    groups = {}
    P = np.array(hose_pts())
    L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    cum = L / L[-1]
    sm = lambda k: k * k * (3 - 2 * k)
    for v in ob.data.vertices:
        i = int(np.argmin(np.linalg.norm(P - np.array(v.co), axis=1)))
        t = cum[i]
        if t < 0.12:
            w = {"chest": 1.0}
        elif t < 0.36:
            k = sm((t - 0.12) / 0.24)
            w = {"chest": 1.0 - k, "root": k}
        elif t < 0.55:
            w = {"root": 1.0}
        elif t < 0.86:
            k = sm((t - 0.55) / 0.31)
            w = {"root": 1.0 - k, "flamer": k}
        else:
            w = {"flamer": 1.0}
        _clear(ob, v)
        _blend_add(ob, groups, v.index, w)


def gloves_weights(ob, skin_ob, arm):
    """The glove on the fist rides the hand; its cuff blends into the forearm."""
    groups = {}
    for v in ob.data.vertices:
        side = "R" if v.co.x < 0 else "L"
        wr, f, n, t = hand_frame(side)
        el = J["elbow_" + side]
        ax = norm(wr - el)
        a = float((np.array(v.co) - wr) @ ax)
        k = min(1.0, max(0.0, (a + 0.06) / 0.06))
        k = k * k * (3 - 2 * k)
        _clear(ob, v)
        _blend_add(ob, groups, v.index, {"hand." + side: k, "forearm." + side: 1.0 - k})


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"),
        "Helmet": ("rigid", "head"), "Visor": ("rigid", "head"),
        "Suit": ("custom", suit_weights),
        "Trousers": ("transfer", {"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Gloves": ("custom", gloves_weights),
        "Boots": ("transfer", {"foot.R", "foot.L", "shin.R", "shin.L"}, None),
        "Harness": ("transfer", TORSO | {"clavicle.R", "clavicle.L"}, None),
        "Gauge": ("transfer", TORSO | {"clavicle.R", "clavicle.L"}, None),
        "Patch": ("transfer", {"upperarm.L"}, None),
        "Tanks": ("rigid", "chest"),
        "Hose": ("custom", hose_weights),
        "Gun": ("rigid", "flamer"), "Pilot": ("rigid", "pilot"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 2.0
    if part == "Skin" and c.z < 1.42:
        return 0.15                 # (his body, arms, hands and legs: inside the suit, the gloves and the boots)
    if part in ("Gauge", "Patch"):
        return 1.4
    if part in ("Helmet", "Visor", "Gun"):
        return 1.1
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Helmet", helmet_field(), 0.0024 if fine else 0.0034),
        ("Visor", visor_field(), 0.0018 if fine else 0.0026),
        ("Suit", suit_field(), 0.0026 if fine else 0.0036),
        ("Trousers", trousers_field(), 0.0028 if fine else 0.0038),
        ("Gloves", gloves_field(), 0.0022 if fine else 0.003),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Harness", harness_field(), 0.0022 if fine else 0.003),
        ("Gauge", gauge_field(), 0.0014 if fine else 0.002),
        ("Patch", patch_field(), 0.0012 if fine else 0.0016),
        ("Tanks", tanks_field(), 0.0022 if fine else 0.003),
        ("Hose", hose_field(), 0.0022 if fine else 0.003),
        ("Gun", gun_field(), 0.0018 if fine else 0.0026),
        ("Pilot", pilot_field(), 0.0016),
    ]
