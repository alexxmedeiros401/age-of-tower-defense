"""The Steam Brawler (HQ tower, Industrial Age; Brute lineage, melee). Rest pose = A-pose, facing -Y, feet at z = 0;
right side = -X.

A huge, barrel-chested stoker turned prizefighter, cheerful and battered: a broad square jaw, a broken nose (a bump on
its bridge, its tip knocked to his left), a lumpy cauliflower left ear, small pale-blue eyes under heavy ginger brows,
a big bushy ginger moustache swept out over his cheeks into mutton-chop whiskers, a gap-toothed grin, a shaven chin
with a shadow of stubble, soot smeared on his nose and cheek. A flat cap of brown-grey tweed (a short stiff peak), a
pair of brass-rimmed goggles with green lenses pushed up onto its front, ginger hair cropped short under it. A grimy
off-white undershirt (short sleeves, a buttoned placket at the throat) under a sleeveless navy waistcoat buttoned in
brass; his huge arms bare from mid-biceps, soot on them; heavy brown trousers, a broad brown leather belt with a big
brass buckle plate; black hobnailed boots. Over his waistcoat the boiler's harness: two leather straps over his
shoulders and down his chest, a strap across it with a brass buckle.

On his back a small riveted boiler: a copper drum with brass bands and rivets, a soot-black domed top with a brass
steam dome, a short stack (the steam vent: the `vent` bone's head), a brass whistle, a pressure gauge (brass bezel,
cream dial, black needle, red mark) on a stalk over his right shoulder, a black firebox under the drum with its grated
door glowing at his back (its own glowing mesh, `Firebox`). Copper pipes from the dome to an outlet at each side, and
from each a ribbed black rubber hose behind his upper arm to a gauntlet.

The gauntlets (the silhouette): from just below each elbow a riveted iron housing over the forearm (a padded leather
roll at its elbow end, cut away at the crook, a brass band and a flange at its front, two brass piston cylinders along
its back, a copper inlet where the hose plugs in), and in front of it a huge iron fist (four fat curled fingers and a
thumb, brass studs on the knuckles, a brass knuckle-plate across the front) on a back plate carried by two steel piston
rods and a fat central steel ram running back into the housing. The housing is rigid with the forearm, the fist rides
the free bone `ram.R` / `ram.L` (its head at the knuckle-plate's front): the clips keep it on the forearm and drive it
out along the forearm's axis at the blow (the rods and the ram slide out of the cylinders and the housing). His hands
themselves are inside the housings (not modelled); the wrists stay straight (the hand bones are left at rest).

His body is the smith's (tarek.py: big and broad) with bigger biceps; his face is built like the smith's and the
grenadier's (marco.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp, project_to, grad
from ugo import _blend_add
from tarek import (J, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, foot,
                   torso_prims, traps, neck_prim, deltoid, upper_arm, _forearm, TORSO, TORSO_Z, torso_bones, curls)
from marco import neck_open, neck_dist, legs_hull, leg_prims, shin_hull, foot_hull, stubble_mask

SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, STUBBLE, SOOT = 0, 1, 2, 3, 4, 5, 8, 9, 10
# steamworks labels (mats.steamworks)
IRON, BRASS, COPPER, STEEL, RUBBER, LEATHER, ENAMEL, RED, BLACK_L, GLASS = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13

NAVY = (0.18, 0.22, 0.42)             # (the brief's navy, as the recipes take it: they read colours as sRGB)
GINGER = {"base": (0.5, 0.2, 0.07), "hi": (0.86, 0.5, 0.22), "low": (0.24, 0.08, 0.03), "streak": (0.66, 0.3, 0.11),
          "tint": (0.62, 0.28, 0.1)}
IRIS = ((0.2, 0.34, 0.5), (0.52, 0.68, 0.82))          # pale blue eyes


# ======================================================================================= the gauntlets' frame
def gframe(side):
    """The forearm's frame (rest pose): the wrist, A along the forearm (elbow -> wrist), W toward the thumb (the crook
    side: forward in the A-pose), M toward the palm (medial). -M is the back of the forearm."""
    sx = -1 if side == "R" else 1
    el, wr = J["elbow_" + side], J["wrist_" + side]
    A = norm(wr - el)
    m = v3((-sx, 0.0, 0.0))
    M = norm(m - A * (m @ A))
    W = norm(np.cross(A, M))
    if W[1] > 0:
        W = -W
    return wr, A, W, M


def gp(side, u, v, w):
    wr, A, W, M = gframe(side)
    return wr + A * u + W * v + M * w


def gdir(side, phi_deg):
    """The radial direction at angle phi round the forearm, from the thumb side (0) toward the back (90)."""
    wr, A, W, M = gframe(side)
    a = math.radians(phi_deg)
    return W * math.cos(a) - M * math.sin(a)


def _uvw(P, side):
    wr, A, W, M = gframe(side)
    q = P - wr.astype(F)
    return q @ A.astype(F), q @ W.astype(F), q @ M.astype(F)


FS = 1.5                    # the fist's scale (designed at 1.0 about the wrist plate U0)
U0 = 0.02
KN_U = 0.284                # the knuckle-plate's front (design u): the ram bone's head


FS_U = 1.22                 # (along the forearm it grows less: a squat, wide fist)


def fp(side, u, v, w):
    return gp(side, U0 + (u - U0) * FS_U, v * FS, w * FS)


def knuckle_point(side):
    return fp(side, KN_U, 0.0, 0.0)


H_FRONT = -0.006            # the housing's front end (u, from the wrist)
HR0, HR1 = 0.142, 0.162     # its radius at the elbow end and at the front
TILT = 0.55                 # its elbow end is cut on a slant: short at the crook, long over the elbow's point
PIST_PHI = (68.0, 112.0)    # the two piston cylinders, on the back of the forearm
PIST_R = HR1 + 0.026        # their axes' distance from the forearm's
INLET_PHI = 160.0           # the hose inlet: behind, near the elbow
RAM_MAX = 0.17              # how far the pistons drive the fist out at the blow


def h_rad(u):
    return F(HR0) + F(HR1 - HR0) * np.clip((u + F(0.26)) / F(0.26), 0, 1)


def h_back(v):
    return F(-0.225) + F(TILT) * v


def hose_inlet(side):
    """The copper inlet on the housing (its end, where the hose is clamped) and its direction."""
    e = gdir(side, INLET_PHI)
    wr, A, W, M = gframe(side)
    p0 = gp(side, -0.2, 0, 0) + e * (HR0 - 0.01)
    d = norm(e - A * 0.45)
    return p0 + d * 0.07, d


# ======================================================================================= head
def head(fd):
    """A broad, battered, good-humoured face: a broad square jaw, round cheeks bunched by his grin, heavy brows, a broken
    nose, a cauliflower left ear, a gap-toothed grin, soot on his nose and right cheek."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.05, 1.588), (0.166, 0.142, 0.132)), 0.07, SKIN)                         # a broad, square jaw
    fd.add(E((0, -0.14, 1.496), (0.1, 0.074, 0.072)), 0.05, SKIN)                           # a big chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.114, -0.126, 1.634), 0.057), 0.05, SKIN)                            # round cheeks
        fd.add(S((sx * 0.142, -0.04, 1.55), 0.058), 0.05, SKIN)                              # the jaw's corners
        pts = [hp((sx * 0.156, -0.055, 1.744)), hp((sx * 0.118, -0.136, 1.758)), hp((sx * 0.062, -0.18, 1.758)), hp((0.0, -0.19, 1.752))]
        fd.add(Chain(pts, [hr(0.014), hr(0.023), hr(0.026), hr(0.023)], k=hr(0.022)), hr(0.03), SKIN)     # a heavy brow ridge
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # heavy ginger brows, knitted low over his eyes, the left one a little higher
    tuft = lambda P: F(0.0024) * NOISE(P * F(150)) + F(0.001) * np.sin(P[:, 0] * F(380))
    for sx in (-1, 1):
        dz = 0.008 if sx > 0 else 0.0
        pts = [hp((sx * 0.024, -0.214, 1.786 + dz * 0.3)), hp((sx * 0.066, -0.21, 1.796 + dz)), hp((sx * 0.112, -0.188, 1.794 + dz)),
               hp((sx * 0.156, -0.148, 1.772 + dz * 0.5))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.013), hr(0.016), hr(0.014), hr(0.007)], k=hr(0.008),
                     disp=tuft, disp_amp=0.003), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.025), hr(0.028), hr(0.025), hr(0.014)], k=hr(0.01)), BROW)
    # small eyes, crinkled by his grin
    for sx in (-1, 1):
        ec = eye_c(sx)
        top = 0.015 if sx < 0 else 0.018
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(top))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0062)), Plane(ec + v3((0, 0, -hr(0.009))), (sx * -0.16, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(top - 0.003))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(2):                                                                      # laughter lines
            a = hp((sx * (0.11 + 0.004 * k), -0.128 + 0.006 * k, 1.68 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, -0.002 - 0.009 * k)), hr(0.002), hr(0.0014)), hr(0.003))
    # the broken nose: a bump where it broke, the bridge bent and its broad flattened tip knocked to his left
    fd.add(RoundCone(hp((0, -0.188, 1.728)), hp((0.016, -0.238, 1.636)), hr(0.02), hr(0.027)), hr(0.017), SKIN)
    fd.add(S((-0.004, -0.212, 1.69), 0.02), hr(0.012), SKIN)
    fd.add(Ellipsoid(hp((0.016, -0.238, 1.624)), v3((0.036, 0.027, 0.027)) * HS), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((0.012 + sx * 0.038, -0.214, 1.608), 0.025), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((0.012 + sx * 0.02, -0.234, 1.598)), v3((0.0095, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a wide grin, his teeth showing under the moustache; its corners up into his cheeks
    slot = [hp((-0.074, -0.157, 1.574)), hp((-0.043, -0.19, 1.549)), hp((0, -0.2, 1.54)), hp((0.043, -0.19, 1.549)), hp((0.074, -0.157, 1.574))]
    fd.sub(Chain(slot, [hr(0.005), hr(0.012), hr(0.015), hr(0.012), hr(0.005)], k=hr(0.004)), hr(0.004))
    fd.paint(Chain(slot, [hr(0.006), hr(0.0135), hr(0.0165), hr(0.0135), hr(0.006)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.06, -0.164, 1.561), (-0.033, -0.188, 1.531), (0, -0.194, 1.524), (0.033, -0.188, 1.531), (0.06, -0.164, 1.561)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0078), hr(0.0088), hr(0.0078), hr(0.004)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        fd.add(S((sx * 0.082, -0.15, 1.572), 0.009), hr(0.007), SKIN)
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.03, 0.052, 0.066)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.012, 0.032, 0.042)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
    for c, r in (((0.205, 0.02, 1.7), 0.016), ((0.21, 0.05, 1.672), 0.014), ((0.2, 0.034, 1.636), 0.013)):   # cauliflower ear
        fd.add(S(c, r), hr(0.008), SKIN)
    # soot on his nose and right cheek, a smear along his left jaw
    fd.paint(Ellipsoid(hp((-0.1, -0.165, 1.652)), v3((0.026, 0.016, 0.012)) * HS * 1.4, R=euler(0.2, 0.0, -0.45)), SOOT)
    fd.paint(Ellipsoid(hp((0.06, -0.19, 1.79)), v3((0.022, 0.012, 0.008)) * HS * 1.3, R=euler(0.2, 0.0, 0.3)), SOOT)


def biceps(side):
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    return Ellipsoid(lerp(sh, el, 0.52) + v3((0, -0.03, 0)), (0.112, 0.116, 0.142), R=rot_from_axes(z_axis=el - sh))


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
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
        # soot smudged on his upper arms
        c = lerp(sh, el, 0.62) + v3((0, -0.06, 0.0))
        fd.paint(Inter(Sphere(c, 0.075), Func(lambda P: F(0.01) - NOISE(P * F(14)) * F(0.05), c - 0.2, c + 0.2), 0.01), SOOT)
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
    """His upper teeth in the grin, one missing (his left upper front tooth)."""
    fd = Field("Teeth")
    for k in range(6):
        if k == 3:
            continue
        x = -0.05 + 0.02 * k
        y = -0.181 + 0.014 * (abs(x) / 0.05) ** 2
        fd.add(RoundBox(hp((x, y, 1.553 + 0.006 * (abs(x) / 0.05) ** 2)), v3((0.0092, 0.006, 0.009)) * HS, hr(0.003)), 0.002)
    return fd


# ======================================================================================= hair, whiskers
def skull():
    return Ellipsoid(HEAD_C, HEAD_RAD)


def head_hull():
    fd = Field("HeadHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    E = lambda c, r: Ellipsoid(hp(c), v3(r) * HS)
    fd.add(E((0, -0.05, 1.588), (0.166, 0.142, 0.132)), 0.07)
    fd.add(E((0, -0.14, 1.496), (0.1, 0.074, 0.072)), 0.05)
    for sx in (-1, 1):
        fd.add(Sphere(hp((sx * 0.114, -0.126, 1.634)), hr(0.057)), 0.05)
        fd.add(Sphere(hp((sx * 0.142, -0.04, 1.55)), hr(0.058)), 0.05)
    fd.add(neck_prim(), 0.05)
    return fd


BAND_F = v3((0.0, -0.175, 1.852))      # the cap's foot (design units): across his brow, above his eyebrows,
BAND_B = v3((0.0, 0.205, 1.7))         # lower behind, at the nape
_BAND_N = norm(v3((0, -(BAND_B[2] - BAND_F[2]) / (BAND_B[1] - BAND_F[1]), 1.0)))
CAP_IN = 0.026                         # the cap's inside, this far out from his skull


def band_d(P):
    """Height above the cap's foot plane (design units)."""
    return (hinv(P) - BAND_F.astype(F)) @ _BAND_N.astype(F)


def hair_field():
    """Ginger hair cropped short, showing under the cap at his sides and nape, sideburns down to the whiskers."""
    fd = Field("Hair")
    stub = lambda P: F(0.0022) * NOISE(P * np.array([70, 70, 26], F)) + F(0.001) * NOISE(P * F(140))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = band_d(P) - F(0.012)                                          # up under the cap
        nape = F(1.6) - z
        face = np.where(ax < F(0.13), F(-0.07) - y, F(-0.13) - y)          # (not over his forehead or face)
        side = np.where((ax > F(0.12)) & (y < F(0.0)), F(1.66) - z, F(-1.0))
        ear = np.where((ax > F(0.15)) & (z < F(1.735)) & (np.abs(y - F(0.035)) < F(0.06)), F(0.02), F(-1.0))
        return np.maximum(np.maximum(top, nape), np.maximum(face, side))
    fd.add(Inter(Shell(skull(), 0.006, 0.014, pad=0.06, disp=stub, disp_amp=0.003), Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.004), 0.0)
    return fd


def moustache_path(sx):
    """The moustache's middle line on one side (design units): from under his nose, out over the corner of the grin and
    up along the cheek into the whiskers."""
    return [(sx * 0.004, -0.236, 1.598), (sx * 0.046, -0.226, 1.589), (sx * 0.09, -0.202, 1.582), (sx * 0.132, -0.17, 1.588),
            (sx * 0.17, -0.138, 1.606), (sx * 0.198, -0.11, 1.63)]


def whisker_tex(P):
    """Bushy, wavy locks (positive pushes the surface in)."""
    x, z = P[:, 0], P[:, 2]
    ph = z / F(0.02) + F(0.4) * np.sin(x * F(60) + z * F(9))
    lock = np.abs(np.sin(ph * F(math.pi)))
    return F(0.002) - F(0.0042) * lock * lock + F(0.0012) * NOISE(P * np.array([90, 90, 30], F))


def moustache_field():
    """A big bushy ginger moustache swept out over his cheeks into mutton-chop whiskers that run up to his sideburns
    (his chin shaved)."""
    fd = Field("Moustache")
    hull = head_hull()
    def chops(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        inner = F(0.112) + F(0.02) * smoothstep(1.56, 1.48, z)
        front = F(-0.03) - F(0.9) * (F(1.7) - z)                          # the front edge: from the sideburn to the grin's corner
        return np.maximum(np.maximum(np.maximum(inner - ax, z - F(1.7)), F(1.48) - z), np.maximum(y - F(0.04), front - y))
    fd.add(Inter(Func(chops, HEAD_C - v3((0.4, 0.4, 0.4)), HEAD_C + v3((0.4, 0.3, 0.1))),
                 Shell(hull, 0.008, 0.026, pad=0.06, disp=lambda P: curls(P, 0.016, 0.006), disp_amp=0.007), 0.012), 0.0)
    strands = lambda P: F(0.0018) * NOISE(P * np.array([30, 90, 90], F)) + F(0.001) * np.sin(P[:, 2] * F(420))
    for sx in (-1, 1):
        pts = [hp(p) for p in moustache_path(sx)]
        n = len(pts)
        ws = [hr(w) for w in (0.022, 0.027, 0.026, 0.023, 0.019, 0.014)]
        ts = [hr(t) for t in (0.02, 0.024, 0.023, 0.02, 0.016, 0.012)]
        ns = [norm(v3((sx * (0.15 + 0.7 * i / (n - 1)), -1.0, 0.25))) for i in range(n)]
        fd.add(Lock(pts, ws, ts, ns, k=hr(0.008), disp=lambda P: curls(P, 0.012, 0.004) + strands(P) * F(0.5), disp_amp=0.005), hr(0.008))
    return fd


# ======================================================================================= the flat cap and goggles
PEAK_N = norm(v3((0.0, 0.28, 1.0)))     # the peak slopes down at its front


def cap_puff():
    return Ellipsoid(hp((0.0, -0.005, 1.905)), v3((0.214, 0.226, 0.07)) * HS, R=euler(0.22, 0, 0))


def cap_body(P):
    """The cap's crown: a soft, flat tweed crown over his skull, full and leaning forward over the peak; hollow over
    his head, its foot on the band plane."""
    sk = skull()
    pf = cap_puff()
    d_sk = sk(P)
    crown = smin(d_sk - F(CAP_IN + 0.016), pf(P), F(0.045))
    b = np.maximum(crown, -(d_sk - F(CAP_IN)))
    return np.maximum(b, -band_d(P) * F(HS) - F(0.004))


def peak_fn(P):
    """The stiff peak: a thin plate in front of the band, rounded at its front edge, sloping down."""
    Q = hinv(P)
    x, y = Q[:, 0], Q[:, 1]
    o = (np.sqrt((x / F(0.165)) ** 2 + ((y + F(0.14)) / F(0.14)) ** 2) - F(1.0)) * F(0.14)
    pl = (Q - np.array([0.0, -0.2, 1.848], F)) @ PEAK_N.astype(F)
    d = np.maximum(o, np.abs(pl) - F(0.0065))
    return d * F(HS)


CAP_LO, CAP_HI = HEAD_C + v3((-0.29, -0.36, -0.12)), HEAD_C + v3((0.29, 0.3, 0.32))


def cap_field():
    """Brown-grey tweed (label 0), the band round its foot a darker stripe (6)."""
    fd = Field("Cap")
    tweed = lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.0006) * NOISE(P * F(90))
    fd.add(Func(lambda P: smin(cap_body(P), peak_fn(P), F(0.022)), CAP_LO, CAP_HI, disp=tweed, disp_amp=0.0018), 0.0)
    sk = skull()
    fd.paint(Func(lambda P: np.maximum(band_d(P) * F(HS) - F(0.022), F(CAP_IN + 0.006) - sk(P)), CAP_LO, CAP_HI), 6)
    return fd


def cap_surface_point(x, z):
    """A point on the cap's front (design x, z), with the outward normal."""
    f = Func(lambda P: np.minimum(cap_body(P), peak_fn(P)), CAP_LO, CAP_HI)
    o = hp((x, -0.6, z))
    h, ok = ray_hit(f, [o], [v3((0, 1, 0))], tmax=0.6, step=0.001)
    p = h[0]
    e = 0.003
    g = np.array([(f(np.array([p + d], F))[0] - f(np.array([p - d], F))[0]) / (2 * e) for d in np.eye(3) * e])
    return p, norm(g)


LENS_X = 0.056
LENS_Z = 1.912
LENS_R = 0.036


def goggles_field():
    """Brass lens cups (5) with green glass (13), a brass bridge, a leather strap (9) round the cap's crown."""
    fd = Field("Goggles")
    cups = []
    for sx in (-1, 1):
        p, n = cap_surface_point(sx * LENS_X, LENS_Z)
        n = norm(n + v3((sx * 0.12, 0, 0)))
        R = rot_from_axes(z_axis=n)
        c = p + n * 0.012
        cups.append((c, n))
        fd.add(Cylinder(c, hr(LENS_R), 0.026, rr=0.006, R=R), 0.0 if sx < 0 else 0.0, BRASS)
        fd.add(Torus(c + n * 0.012, hr(LENS_R) - 0.002, 0.0055, R=R), 0.003, BRASS)
        fd.sub(Cylinder(c + n * 0.014, hr(LENS_R) - 0.008, 0.012, rr=0.002, R=R), 0.002)
        fd.add(Cylinder(c + n * 0.006, hr(LENS_R) - 0.007, 0.006, rr=0.002, R=R), 0.002, GLASS)
    (c0, n0), (c1, n1) = cups
    mid = (c0 + c1) / 2 + norm(n0 + n1) * 0.004
    fd.add(Chain([c0 + norm(c1 - c0) * 0.035, mid, c1 + norm(c0 - c1) * 0.035], [0.006, 0.0065, 0.006], k=0.003), 0.003, BRASS)
    # the strap: round the crown at the cups' height, lying on the cap
    hc = float(band_d(np.array([(c0 + c1) / 2], F))[0])
    def strap(P):
        return np.maximum(np.abs(cap_body(P) - F(0.004)) - F(0.0045), (np.abs(band_d(P) - F(hc)) - F(0.011)) * F(HS))
    fd.add(Func(strap, CAP_LO, CAP_HI), 0.004, LEATHER)
    return fd


# ======================================================================================= the clothes' bodies
def vest_hull():
    """His torso as the waistcoat and undershirt lie on it: the chest smoothed over (no pectorals), his belly."""
    b = Field("VestHull")
    tp = torso_prims()
    b.add(tp[0][0], 0.0)
    b.add(tp[1][0], tp[1][1])
    b.add(tp[4][0], tp[4][1])
    b.add(Ellipsoid((0, -0.06, 1.26), (0.28, 0.17, 0.2)), 0.06)
    b.add(traps(), 0.06)
    return b


def arms_hull(fd=None):
    af = fd or Field("Arms")
    for side in ("R", "L"):
        af.add(deltoid(side), 0.055 if af.ops else 0.0)
        af.add(upper_arm(side), 0.05)
        af.add(biceps(side), 0.04)
    return af


def shirt_hull():
    b = vest_hull()
    arms_hull(b)
    return b


SHIRT_OFF, SHIRT_T = 0.012, 0.01
VEST_OFF, VEST_T = 0.034, 0.014
VEST_OUT = VEST_OFF + VEST_T * 0.5          # the waistcoat's outer surface (from vest_hull)
SLEEVE_END = 0.13                           # the undershirt's sleeves end this far down the upper arm


def _sleeve_end(P):
    """> 0 past the sleeves' ends on his upper arms (only near each upper arm)."""
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        q = P - sh.astype(F)
        along = q @ ax.astype(F)
        off = np.sqrt(np.maximum((q * q).sum(1) - along ** 2, 0))
        cut = along - F(SLEEVE_END) - F(0.012) * np.sin(np.arctan2(q[:, 1], q[:, 2]) * F(3))
        out = np.maximum(out, np.where((off < F(0.2)) & (along > F(0.05)), cut, F(-1.0)))
    return out


def shirt_field():
    """A grimy off-white undershirt (label 0, grime: 5): short sleeves, a round neck with a buttoned placket, tucked into
    his trousers."""
    fd = Field("Shirt")
    sh = shirt_hull()
    folds = lambda P: F(0.0012) * NOISE(P * F(25)) + F(0.002) * NOISE(P * np.array([6, 6, 14], F))
    def keep(P):
        return np.maximum(np.maximum(neck_open(P, 0.128), F(0.95) - P[:, 2]), _sleeve_end(P))
    fd.add(Inter(Func(keep, (-0.75, -0.45, 0.93), (0.75, 0.5, 1.62)), Shell(sh, SHIRT_OFF, SHIRT_T, pad=0.1, disp=folds, disp_amp=0.003), 0.004), 0.0)
    # rolled hems at the sleeves' ends
    for side in ("R", "L"):
        s0, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - s0)
        c = s0 + ax * (SLEEVE_END - 0.012)
        arms = arms_hull()
        fd.add(Inter(Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.013), c - 0.25, c + 0.25),
                     Shell(arms, SHIRT_OFF + 0.006, 0.014, pad=0.08), 0.004), 0.004)
    # the placket: a strip down from his throat
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 0]) - F(0.022), P[:, 1] + F(0.05)), (-0.1, -0.5, 1.2), (0.1, 0.1, 1.6)), 6)
    # grime: sweat and soot on his chest and under his arms
    fd.paint(Func(lambda P: F(0.012) - NOISE(P * F(6)) * F(0.08) - F(0.03), (-0.75, -0.5, 0.9), (0.75, 0.5, 1.65)), 5)
    return fd


def placket_buttons():
    sh = shirt_hull()
    outer = Func(lambda P: sh.eval(P, margin=0.1) - F(SHIRT_OFF + SHIRT_T * 0.5 + 0.002), (-0.6, -0.6, 1.1), (0.6, 0.6, 1.6))
    pts = []
    for z in (1.4, 1.36, 1.32):
        h, ok = ray_hit(outer, [v3((0.0, -0.6, z))], [v3((0, 1, 0))], tmax=0.6)
        if ok[0]:
            pts.append(h[0])
    return pts


def vest_front_w(z):
    """Half the width of the waistcoat's V at height z (closed below 1.16)."""
    return F(0.118) * smoothstep(1.15, 1.43, z) + F(0.003)


def vest_hem(P):
    x = np.abs(P[:, 0])
    front = F(0.905) + F(0.04) * np.exp(-(x / F(0.028)) ** 2) + F(0.035) * smoothstep(0.12, 0.3, x)
    back = F(0.95)
    k = smoothstep(-0.12, 0.12, P[:, 1])
    return front * (F(1) - k) + back * k


ARMHOLE_R = 0.152


def _armhole(P):
    """> 0 inside the armholes (round each shoulder joint, along the upper arm)."""
    out = np.full(len(P), F(-1.0))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        a = J["shoulder_" + side] + v3((-sx * 0.02, 0.0, 0.0))
        b = J["elbow_" + side]
        ab = b - a
        q = P - a.astype(F)
        t = np.clip((q @ ab.astype(F)) / F(ab @ ab), 0, 1)
        d = np.sqrt(((q - t[:, None] * ab.astype(F)) ** 2).sum(1))
        out = np.maximum(out, np.where(P[:, 0] * F(sx) > F(0.17), F(ARMHOLE_R) - d, F(-1.0)))
    return out


def vest_field():
    """Navy wool (label 0), the lining showing at its edges (6: a darker navy), welt pockets (5)."""
    fd = Field("Vest")
    vh = vest_hull()
    folds = lambda P: F(0.0012) * NOISE(P * F(25)) + F(0.0015) * NOISE(P * np.array([5, 5, 12], F))
    def keep(P):
        z = P[:, 2]
        front = np.where(P[:, 1] < F(0.0), vest_front_w(z) - np.abs(P[:, 0]), F(-1.0))
        return np.maximum(np.maximum(np.maximum(vest_hem(P) - z, front), neck_open(P, 0.152)), _armhole(P))
    fd.add(Inter(Func(keep, (-0.5, -0.45, 0.86), (0.5, 0.5, 1.62)), Shell(vh, VEST_OFF, VEST_T, pad=0.1, disp=folds, disp_amp=0.002), 0.004), 0.0)
    # welt pockets: a slit on each side of his belly
    for sx in (-1, 1):
        c = v3((sx * 0.15, -0.3, 1.0))
        fd.paint(Func(lambda P, c=c: np.maximum(np.maximum(np.abs(P[:, 0] - F(c[0])) - F(0.05), np.abs(P[:, 2] - F(c[2]) - (P[:, 0] - F(c[0])) * F(0.15 * sx)) - F(0.006)),
                                               P[:, 1] + F(0.05)), (-0.5, -0.5, 0.9), (0.5, 0.0, 1.1)), 5)
    return fd


VEST_Z = (0.955, 1.01, 1.065, 1.12)


def vest_buttons():
    vh = vest_hull()
    outer = Func(lambda P: vh.eval(P, margin=0.1) - F(VEST_OUT + 0.002), (-0.6, -0.6, 0.8), (0.6, 0.6, 1.5))
    pts = []
    for z in VEST_Z:
        h, ok = ray_hit(outer, [v3((0.0, -0.6, z))], [v3((0, 1, 0))], tmax=0.6)
        if ok[0]:
            pts.append(h[0])
    return pts


# ======================================================================================= trousers, belt, boots
TROUSER_TOP = 1.0
CUFF_Z = 0.15


def trousers_field():
    """Heavy brown wool trousers from his waist to his boots, turned up at the bottoms (5: a darker band)."""
    fd = Field("Trousers")
    lh = legs_hull()
    folds = lambda P: F(0.0016) * NOISE(P * np.array([25, 25, 50], F)) + F(0.003) * NOISE(P * np.array([6, 6, 3], F))
    fd.add(Inter(Func(lambda P: np.maximum(F(CUFF_Z) - P[:, 2], P[:, 2] - F(TROUSER_TOP)), (-0.4, -0.32, CUFF_Z - 0.02), (0.4, 0.32, TROUSER_TOP + 0.03)),
                 Shell(lh, 0.026, 0.014, pad=0.08, disp=folds, disp_amp=0.004), 0.004), 0.0)
    for side in ("R", "L"):
        sh = shin_hull(side)
        an = J["ankle_" + side]
        blo, bhi = v3((an[0] - 0.2, -0.22, CUFF_Z - 0.02)), v3((an[0] + 0.2, 0.25, CUFF_Z + 0.08))
        fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(CUFF_Z + 0.025)) - F(0.025), blo, bhi), Shell(sh, 0.036, 0.016, pad=0.08), 0.004), 0.004, 5)
    return fd


BELT_Z = 0.895
BELT_HW = 0.03


def belt_base():
    b = Field("BeltBase")
    tp = torso_prims()
    b.add(tp[4][0], 0.0)
    b.add(tp[5][0], tp[5][1])
    return b


def boots_field():
    """Black leather work boots (label 12) to above the ankle, a toe cap, a thick sole studded with iron hobnails (0)."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        fh = foot_hull(side)
        fd.add(Inter(Func(lambda P: P[:, 2] - F(0.21), an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.2))),
                     Shell(fh, 0.012, 0.016, pad=0.06, disp=lambda P: F(0.0012) * NOISE(P * F(30)), disp_amp=0.0015), 0.004), 0.0, BLACK_L)
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.076 + v3((0, 0, -0.096)), (0.084, 0.166, 0.016), 0.01, R=Rz), 0.006, BLACK_L)      # the sole
        fd.add(RoundBox(an + fwd * -0.02 + v3((0, 0, -0.086)), (0.066, 0.054, 0.024), 0.01, R=Rz), 0.006, BLACK_L)      # the heel
        fd.add(Ellipsoid(an + fwd * 0.17 + v3((0, 0, -0.06)), (0.072, 0.07, 0.05), R=Rz), 0.02, BLACK_L)               # toe cap
        # a padded collar at the top
        sh = shin_hull(side)
        fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(0.2)) - F(0.016), an - 0.3, an + 0.3), Shell(sh, 0.03, 0.018, pad=0.08), 0.004), 0.004, BLACK_L)
        # hobnails round the sole's edge
        for k in range(14):
            a = 2 * math.pi * k / 14
            loc = v3((math.cos(a) * 0.078, math.sin(a) * 0.16, 0.0))
            p = an + Rz @ (v3((0, -0.076, 0)) + loc) + v3((0, 0, -0.096))
            fd.add(Sphere(p + (Rz @ norm(v3((math.cos(a) / 0.078, math.sin(a) / 0.16, 0.0)))) * 0.004, 0.0062), 0.002, IRON)
    return fd


# ======================================================================================= the boiler (rigid with his chest)
BX = v3((0.0, 0.49, 0.0))              # its axis (upright)
BR = 0.148                             # the drum's radius
DRUM_Z0, DRUM_Z1 = 1.07, 1.43
FIRE_Z0 = 0.915
DOOR_C = v3((0.0, BX[1] + 0.152, 0.99))
DOOR_R = 0.062
STACK_A = v3((0.07, 0.535, 1.44))
STACK_TOP = v3((0.082, 0.548, 1.74))
GAUGE_C = v3((-0.16, 0.39, 1.585))
GAUGE_N = norm(v3((-0.42, -0.55, 0.72)))
GAUGE_R = 0.05


def outlet(sx):
    """The copper outlet at each side of the boiler (the hose's end is clamped on it)."""
    return v3((sx * 0.205, 0.43, 1.33)), norm(v3((sx * 1.0, -0.25, -0.2)))


def boiler_field():
    """Copper (6) with brass bands and rivets (5); soot-black iron (0): the domed top, the firebox, the stack, the door's
    grate; a brass steam dome and whistle; the gauge: a brass bezel, a cream dial (10), a black needle, a red mark (11);
    copper pipes to the outlets."""
    fd = Field("Boiler")
    ax = v3((0, 0, 1))
    # the drum
    zc = (DRUM_Z0 + DRUM_Z1) / 2
    fd.add(Cylinder(v3((BX[0], BX[1], zc)), BR, DRUM_Z1 - DRUM_Z0, rr=0.018), 0.0, COPPER)
    for z in (1.15, 1.35):
        fd.add(Torus(v3((BX[0], BX[1], z)), BR + 0.001, 0.0085), 0.003, BRASS)
    for z in (DRUM_Z0 + 0.025, DRUM_Z1 - 0.025, 1.25):
        for k in range(16):
            a = 2 * math.pi * k / 16 + (0.2 if z == 1.25 else 0.0)
            fd.add(Sphere(v3((BX[0] + math.cos(a) * BR, BX[1] + math.sin(a) * BR, z)), 0.0075), 0.002, BRASS)
    # the domed top
    fd.add(Inter(Ellipsoid(v3((BX[0], BX[1], DRUM_Z1 - 0.01)), (BR - 0.004, BR - 0.004, 0.085)), Plane(v3((0, 0, DRUM_Z1 - 0.012)), (0, 0, -1)), 0.004), 0.008, IRON)
    sd = v3((-0.03, BX[1] + 0.01, 1.49))
    fd.add(Cylinder(sd, 0.05, 0.05, rr=0.01), 0.008, BRASS)
    fd.add(Inter(Sphere(sd + v3((0, 0, 0.022)), 0.05), Plane(sd + v3((0, 0, 0.022)), (0, 0, -1)), 0.003), 0.004, BRASS)
    # the firebox under it, its door at his back
    fd.add(Cylinder(v3((BX[0], BX[1], (FIRE_Z0 + DRUM_Z0) / 2 + 0.005)), BR + 0.006, DRUM_Z0 - FIRE_Z0 + 0.01, rr=0.02), 0.006, IRON)
    fd.add(Torus(v3((BX[0], BX[1], DRUM_Z0)), BR + 0.004, 0.009), 0.003, BRASS)
    dn = v3((0, 1, 0))
    Rd = rot_from_axes(z_axis=dn)
    fd.sub(Cylinder(DOOR_C, DOOR_R, 0.06, rr=0.006, R=Rd), 0.004)
    fd.add(Torus(DOOR_C + dn * 0.004, DOOR_R + 0.006, 0.011, R=Rd), 0.004, IRON)
    for k in range(-2, 3):                                                                   # the grate's bars
        z = DOOR_C[2] + k * 0.022
        w = math.sqrt(max(DOOR_R ** 2 - (k * 0.022) ** 2, 0.0)) + 0.004
        fd.add(RoundCone(DOOR_C + v3((-w, -0.004, k * 0.022)), DOOR_C + v3((w, -0.004, k * 0.022)), 0.0055, 0.0055), 0.002, IRON)
    fd.add(RoundCone(DOOR_C + v3((DOOR_R + 0.01, 0.006, 0.0)), DOOR_C + v3((DOOR_R + 0.045, 0.02, 0.0)), 0.007, 0.009), 0.003, BRASS)  # latch
    # the stack and its flared cap (the steam vent)
    fd.add(RoundCone(STACK_A, STACK_TOP - v3((0, 0, 0.02)), 0.034, 0.029), 0.008, IRON)
    fd.add(Torus(STACK_TOP - v3((0, 0, 0.012)), 0.034, 0.012), 0.004, BRASS)
    fd.sub(Cylinder(STACK_TOP, 0.022, 0.05, rr=0.003), 0.003)
    fd.add(Torus(STACK_A + v3((0.003, 0.003, 0.09)), 0.032, 0.006), 0.002, BRASS)
    # the whistle
    wb = v3((-0.075, BX[1] + 0.035, 1.47))
    fd.add(RoundCone(wb, wb + v3((0, 0, 0.07)), 0.011, 0.011), 0.006, BRASS)
    fd.add(Cylinder(wb + v3((0, 0, 0.1)), 0.02, 0.06, rr=0.006), 0.005, BRASS)
    fd.add(Sphere(wb + v3((0, 0, 0.135)), 0.012), 0.004, BRASS)
    # the gauge on its stalk, over his right shoulder
    st0 = v3((-0.1, BX[1] - 0.08, 1.47))
    fd.add(Chain([st0, st0 + v3((-0.03, -0.02, 0.06)), GAUGE_C - GAUGE_N * 0.02], [0.013, 0.012, 0.012], k=0.004), 0.006, COPPER)
    Rg = rot_from_axes(z_axis=GAUGE_N)
    fd.add(Cylinder(GAUGE_C, GAUGE_R, 0.026, rr=0.008, R=Rg), 0.004, BRASS)
    fd.sub(Cylinder(GAUGE_C + GAUGE_N * 0.013, GAUGE_R - 0.008, 0.014, rr=0.002, R=Rg), 0.002)
    face_c = GAUGE_C + GAUGE_N * 0.006
    fd.add(Cylinder(face_c, GAUGE_R - 0.008, 0.004, R=Rg), 0.001, ENAMEL)
    gx = norm(np.cross(GAUGE_N, v3((0, 0, 1))))
    gy = np.cross(GAUGE_N, gx)
    tip = face_c + GAUGE_N * 0.003 + (gx * math.cos(2.1) + gy * math.sin(2.1)) * 0.032
    fd.add(RoundCone(face_c + GAUGE_N * 0.003, tip, 0.0035, 0.0018), 0.001, IRON)
    def red_mark(P):
        q = P - face_c.astype(F)
        a = np.arctan2(q @ gy.astype(F), q @ gx.astype(F))
        r = np.sqrt((q @ gx.astype(F)) ** 2 + (q @ gy.astype(F)) ** 2)
        return np.maximum(np.maximum(np.abs(a - F(0.55)) * r - F(0.012), np.abs(r - F(0.033)) - F(0.006)), np.abs(q @ GAUGE_N.astype(F)) - F(0.01))
    fd.paint(Func(red_mark, face_c - 0.07, face_c + 0.07), RED)
    # copper pipes from the dome to the outlets
    for sx in (-1, 1):
        o, d = outlet(sx)
        p0 = v3((sx * 0.05, BX[1] - 0.03, 1.47))
        pts = [p0, p0 + v3((sx * 0.09, -0.005, 0.005)), v3((sx * 0.165, 0.45, 1.43)), v3((sx * 0.178, 0.44, 1.36)), o]
        fd.add(Chain(pts, [0.015] * len(pts), k=0.012), 0.006, COPPER)
        fd.add(Cylinder(o - d * 0.004, 0.022, 0.022, rr=0.005, R=rot_from_axes(z_axis=d)), 0.003, BRASS)
    # the iron frame it hangs on: two straps round the drum, a pad against his back
    for z in (1.12, 1.4):
        fd.add(Inter(Torus(v3((BX[0], BX[1], z)), BR + 0.004, 0.012), Plane(v3((0, BX[1] + 0.02, z)), (0, 1, 0)), 0.002), 0.003, IRON)
    return fd


def firebox_field():
    """The glowing fire behind the grate (its own emissive mesh)."""
    fd = Field("Firebox")
    fd.add(Cylinder(DOOR_C - v3((0, 0.022, 0)), DOOR_R + 0.002, 0.02, rr=0.006, R=rot_from_axes(z_axis=(0, 1, 0))), 0.0)
    return fd


# ======================================================================================= the harness and belt (leather)
def _on_vest(pts, lift=0.008):
    vh = vest_hull()
    hull = Field("VestOuter")
    hull.add(Func(lambda P: vh.eval(P, margin=0.1) - F(VEST_OUT + lift), (-0.7, -0.7, 0.7), (0.7, 0.7, 1.75)), 0.0)
    pp = project_to(hull, [v3(p) for p in pts], iters=4)
    ns = grad(hull, pp.astype(F)).astype(np.float64)
    return [v3(p) for p in pp], [v3(n) for n in ns]


def strap_path(sx):
    return [(sx * 0.12, 0.32, 1.42), (sx * 0.16, 0.22, 1.5), (sx * 0.17, 0.08, 1.53), (sx * 0.17, -0.07, 1.48), (sx * 0.165, -0.2, 1.36),
            (sx * 0.16, -0.27, 1.2), (sx * 0.15, -0.27, 1.05), (sx * 0.14, -0.25, 0.93)]


CHEST_Z = 1.235


def leather_field():
    """Brown leather (label 0) with brass (6): the harness straps over his shoulders and down his chest, the strap across
    his chest with its buckle, the belt with its big buckle plate."""
    fd = Field("Leather")
    for sx in (-1, 1):
        pts, ns = _on_vest(strap_path(sx))
        fd.add(Lock(pts, [0.036] * len(pts), [0.008] * len(pts), ns, k=0.006), 0.004)
    # the chest strap
    xs = np.linspace(-0.17, 0.17, 9)
    pts, ns = _on_vest([(x, -0.32, CHEST_Z) for x in xs], lift=0.017)
    fd.add(Lock(pts, [0.026] * len(pts), [0.007] * len(pts), ns, k=0.006), 0.004)
    c, n = pts[4], ns[4]
    R = rot_from_axes(z_axis=n, x_axis=(1, 0, 0))
    fd.add(RoundBox(c + n * 0.006, (0.032, 0.026, 0.005), 0.004, R=R), 0.003, 6)
    fd.sub(RoundBox(c + n * 0.011, (0.02, 0.014, 0.006), 0.003, R=R), 0.002)
    # the belt over his trousers, a big brass buckle plate in front
    bb = belt_base()
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(BELT_HW), (-0.5, -0.5, BELT_Z - 0.05), (0.5, 0.5, BELT_Z + 0.05)),
                 Shell(bb, 0.046, 0.012, pad=0.1), 0.004), 0.0)
    h, ok = ray_hit(Func(lambda P: bb.eval(P, margin=0.1) - F(0.052), (-0.6, -0.6, 0.7), (0.6, 0.6, 1.1)), [v3((0, -0.6, BELT_Z))], [v3((0, 1, 0))], tmax=0.6)
    bc = h[0]
    Rb = rot_from_axes(z_axis=(0, -1, 0), x_axis=(1, 0, 0))
    fd.add(RoundBox(bc + v3((0, -0.006, 0)), (0.075, 0.046, 0.008), 0.008, R=Rb), 0.004, 6)
    fd.sub(RoundBox(bc + v3((0, -0.016, 0)), (0.058, 0.03, 0.004), 0.003, R=Rb), 0.002)
    fd.add(RoundBox(bc + v3((0, -0.012, 0)), (0.04, 0.016, 0.004), 0.004, R=Rb), 0.002, 6)
    return fd


def brass_field():
    """Brass: the waistcoat's buttons, the undershirt's placket buttons."""
    fd = Field("Brass")
    for p in vest_buttons():
        fd.add(Cylinder(p, 0.0125, 0.008, rr=0.0036, R=rot_from_axes(z_axis=(0, -1, 0.15))), 0.0)
    for p in placket_buttons():
        fd.add(Cylinder(p, 0.008, 0.006, rr=0.0025, R=rot_from_axes(z_axis=(0, -1, 0.2))), 0.0)
    return fd


# ======================================================================================= the gauntlets
def _ring(side, u, rad, half, lo_hi=0.3):
    wr, A, W, M = gframe(side)
    c = gp(side, u, 0, 0)
    def fn(P):
        uu, v, w = _uvw(P, side)
        return np.maximum(np.abs(uu - F(u)) - F(half), np.abs(np.sqrt(v * v + w * w) - F(rad)) - F(0.006))
    return Func(fn, c - lo_hi, c + lo_hi)


def gauntlets_field():
    """The housings (rigid with the forearms): soot-black riveted iron (0), a brass band (5), the padded leather roll at
    the elbow end (9), two brass piston cylinders with iron glands, a copper inlet (6) with a brass nut."""
    fd = Field("Gauntlets")
    for side in ("R", "L"):
        wr, A, W, M = gframe(side)
        c = gp(side, -0.15, 0, 0)
        def tube(P, side=side):
            u, v, w = _uvw(P, side)
            rad = np.sqrt(v * v + w * w)
            dr = rad - h_rad(u)
            du = np.maximum(h_back(v) - u, u - F(H_FRONT))
            rr = F(0.014)
            qx, qy = dr + rr, du + rr
            return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - rr
        dent = lambda P: F(0.001) * NOISE(P * F(40))
        fd.add(Func(tube, c - 0.32, c + 0.32, disp=dent, disp_amp=0.0012), 0.0, IRON)
        # the front flange and a brass band behind it
        def flange(P, side=side):
            u, v, w = _uvw(P, side)
            return np.maximum(np.abs(u - F(H_FRONT - 0.01)) - F(0.009), np.sqrt(v * v + w * w) - (h_rad(u) + F(0.013)))
        fd.add(Func(flange, c - 0.32, c + 0.32), 0.004, IRON)
        def band(P, side=side):
            u, v, w = _uvw(P, side)
            return np.maximum(np.abs(u - F(-0.06)) - F(0.012), np.sqrt(v * v + w * w) - (h_rad(u) + F(0.007)))
        fd.add(Func(band, c - 0.32, c + 0.32), 0.003, BRASS)
        # the padded roll round its slanted elbow end
        def roll(P, side=side):
            u, v, w = _uvw(P, side)
            rad = np.sqrt(v * v + w * w)
            pl = (u - h_back(v)) / F(math.sqrt(1 + TILT * TILT))
            return np.sqrt((rad - h_rad(u) + F(0.002)) ** 2 + (pl - F(0.006)) ** 2) - F(0.024)
        fd.add(Func(roll, c - 0.34, c + 0.34, disp=lambda P: F(0.0015) * NOISE(P * F(30)), disp_amp=0.002), 0.006, LEATHER)
        # rivets: rings near each end, and rows along it
        for k in range(12):
            a = 2 * math.pi * k / 12
            e = W * math.cos(a) + M * math.sin(a)
            for u in (-0.03, -0.09):
                p = gp(side, u, 0, 0) + e * float(h_rad(np.array([u], F))[0])
                fd.add(Sphere(p, 0.0078), 0.002, IRON)
            vb = HR0 * math.cos(a)
            ub = -0.225 + TILT * vb + 0.04
            p = gp(side, ub, 0, 0) + e * float(h_rad(np.array([ub], F))[0])
            fd.add(Sphere(p, 0.0072), 0.002, IRON)
        for phi in (0.0, 180.0, 270.0):
            e = gdir(side, phi)
            for u in (-0.13, -0.17):
                if u < float(h_back(np.array([HR0 * math.cos(math.radians(phi))], F))[0]) + 0.03:
                    continue
                p = gp(side, u, 0, 0) + e * float(h_rad(np.array([u], F))[0])
                fd.add(Sphere(p, 0.0072), 0.002, IRON)
        # the piston cylinders along its back, on saddles
        for phi in PIST_PHI:
            e = gdir(side, phi)
            vb = PIST_R * math.cos(math.radians(phi))
            ua = float(h_back(np.array([vb], F))[0]) + 0.03
            ub = -0.034
            a, b = gp(side, ua, 0, 0) + e * PIST_R, gp(side, ub, 0, 0) + e * PIST_R
            R = rot_from_axes(z_axis=A)
            fd.add(Cylinder((a + b) / 2, 0.031, ub - ua, rr=0.009, R=R), 0.004, BRASS)
            fd.add(Cylinder(b + A * 0.006, 0.036, 0.02, rr=0.006, R=R), 0.003, IRON)                     # gland
            fd.add(Cylinder(a, 0.035, 0.018, rr=0.007, R=R), 0.003, IRON)                                  # end cap
            for u in (ua + 0.04, ub - 0.05):
                q = gp(side, u, 0, 0) + e * (PIST_R - 0.024)
                Rs = np.stack([norm(np.cross(A, e)), e, A], axis=1)
                fd.add(RoundBox(q, (0.016, 0.014, 0.012), 0.004, R=Rs), 0.004, IRON)
        # the copper inlet (the hose is clamped on its end)
        end, d = hose_inlet(side)
        e = gdir(side, INLET_PHI)
        p0 = gp(side, -0.2, 0, 0) + e * (HR0 - 0.01)
        fd.add(RoundCone(p0, end, 0.02, 0.018), 0.006, COPPER)
        fd.add(Cylinder(p0 + d * 0.03, 0.025, 0.016, rr=0.005, R=rot_from_axes(z_axis=d)), 0.003, BRASS)
    return fd


FINGER_V = (0.084, 0.028, -0.028, -0.084)           # index (thumb side) .. little finger


def fists_field():
    """The fists (on the ram bones): soot-black iron (0), brass studs and the knuckle-plate (5), the steel rods and ram
    (7) running back into the housing."""
    fd = Field("Fists")
    for side in ("R", "L"):
        wr, A, W, M = gframe(side)
        Rf = np.stack([A, W, M], axis=1)
        # the back plate and its brass rim
        bp = gp(side, 0.042, 0, 0)
        fd.add(Cylinder(bp, HR1 - 0.002, 0.036, rr=0.01, R=rot_from_axes(z_axis=A)), 0.0, IRON)
        fd.add(Torus(bp, HR1 - 0.004, 0.008, R=rot_from_axes(z_axis=A)), 0.003, BRASS)
        for k in range(10):
            a = 2 * math.pi * k / 10 + 0.3
            e = W * math.cos(a) + M * math.sin(a)
            fd.add(Sphere(bp + A * 0.018 + e * (HR1 - 0.03), 0.008), 0.002, IRON)
        # lugs for the piston rods, the rods, the central ram
        for phi in PIST_PHI:
            e = gdir(side, phi)
            Rl = np.stack([e, norm(np.cross(A, e)), A], axis=1)
            fd.add(RoundBox(gp(side, 0.04, 0, 0) + e * (PIST_R - 0.016), (0.035, 0.024, 0.018), 0.008, R=Rl), 0.006, IRON)
            fd.add(RoundCone(gp(side, -0.19, 0, 0) + e * PIST_R, gp(side, 0.03, 0, 0) + e * PIST_R, 0.0145, 0.0145), 0.003, STEEL)
        fd.add(RoundCone(gp(side, -0.19, 0, 0), gp(side, 0.03, 0, 0), 0.064, 0.064), 0.004, STEEL)
        fd.add(Torus(gp(side, 0.006, 0, 0), 0.066, 0.007, R=rot_from_axes(z_axis=A)), 0.002, BRASS)
        # the hand: a block of riveted plates, a lame over its back
        fd.add(RoundBox(fp(side, 0.112, 0.0, -0.012), v3((0.06 * FS_U, 0.112 * FS, 0.072 * FS)), 0.036 * FS_U, R=Rf), 0.012, IRON)
        fd.add(RoundBox(fp(side, 0.12, 0.0, -0.08), v3((0.066 * FS_U, 0.102 * FS, 0.012 * FS)), 0.01 * FS, R=Rf), 0.006, IRON)
        for v in (-0.06, 0.0, 0.06):
            fd.add(Sphere(fp(side, 0.075, v, -0.094), 0.0075 * FS), 0.002, BRASS)
        # four fat curled fingers
        for i, v in enumerate(FINGER_V):
            s = 0.9 if i == 3 else 1.0
            du = -0.012 if i == 3 else 0.0
            K1 = fp(side, 0.2 + du, v, -0.05)
            K2 = fp(side, 0.218 + du, v, 0.045)
            K3 = fp(side, 0.168 + du, v, 0.1)
            K4 = fp(side, 0.118 + du, v * 0.95, 0.076)
            rads = [r * FS * s for r in (0.036, 0.034, 0.03, 0.026)]
            fd.add(Chain([K1, K2, K3, K4], rads, k=0.008), 0.006, IRON)
            fd.add(Sphere(fp(side, 0.2 + du, v, -0.083), 0.019 * FS * s), 0.003, BRASS)               # knuckle studs
        # the thumb, wrapped over the fingers
        th = [fp(side, 0.07, 0.096, 0.024), fp(side, 0.125, 0.13, 0.074), fp(side, 0.185, 0.1, 0.108), fp(side, 0.212, 0.046, 0.114)]
        fd.add(Chain(th, [0.037 * FS, 0.034 * FS, 0.031 * FS, 0.027 * FS], k=0.008), 0.008, IRON)
        fd.add(Sphere(fp(side, 0.125, 0.162, 0.072), 0.016 * FS), 0.003, BRASS)
        # the brass knuckle-plate across the front of the fingers, four domed studs on it
        fd.add(RoundBox(fp(side, 0.258, 0.0, 0.0), v3((0.012 * FS_U, 0.118 * FS, 0.056 * FS)), 0.01 * FS, R=Rf), 0.006, BRASS)
        for v in FINGER_V:
            fd.add(Sphere(fp(side, 0.268, v, 0.0), 0.02 * FS), 0.004, BRASS)
    return fd


# ======================================================================================= the hoses
HOSE_R = 0.021


def hose_pts(side, n=24):
    """The hose's centre line (rest pose), from the boiler's outlet behind his upper arm to the gauntlet's inlet."""
    sx = -1 if side == "R" else 1
    o, od = outlet(sx)
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    back = v3((0, 1, 0))
    ctrl = [o + od * 0.012, o + od * 0.06 + v3((0, -0.01, -0.02)), lerp(sh, el, 0.3) + back * 0.165 + v3((sx * 0.02, 0, 0.02)),
            lerp(sh, el, 0.62) + back * 0.15 + v3((sx * 0.025, 0, 0)), lerp(sh, el, 0.92) + back * 0.15 + v3((sx * 0.03, 0, -0.01))]
    end, d = hose_inlet(side)
    ctrl += [end + d * 0.06, end - d * 0.004]
    # Catmull-Rom through the control points
    P = [ctrl[0]] + ctrl + [ctrl[-1]]
    out = []
    for i in range(1, len(P) - 2):
        for k in range(4):
            t = k / 4.0
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(ctrl[-1])
    return out


def hoses_field():
    """Ribbed black rubber (8), brass clamps (5) at each end."""
    fd = Field("Hoses")
    for side in ("R", "L"):
        pts = hose_pts(side)
        L = np.cumsum([0.0] + [float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(len(pts) - 1)])
        o = pts[0]
        ribs = lambda P, o=o: F(0.0016) * np.sin(np.sqrt(((P - o.astype(F)) ** 2).sum(1)) * F(260))
        fd.add(Chain(pts, [HOSE_R] * len(pts), k=0.004, disp=ribs, disp_amp=0.002), 0.0, RUBBER)
        for p, q in ((pts[1], pts[2]), (pts[-2], pts[-3])):
            d = norm(q - p)
            fd.add(Torus(p + d * 0.01, HOSE_R + 0.002, 0.0055, R=rot_from_axes(z_axis=d)), 0.002, BRASS)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.62)), 0.05, 0.6)]
    for sx in (-1, 1):
        sd = "R" if sx < 0 else "L"
        pts += [(hp((sx * 0.112, -0.15, 1.628)), 0.07, 0.75), (hp((sx * 0.18, 0.035, 1.664)), 0.06, 0.6),
                (J["elbow_" + sd] + v3((0, 0.025, 0)), 0.07, 0.35)]
    pts.append((hp((0.016, -0.24, 1.625)), 0.04, 0.6))
    return pts


# ======================================================================================= build config
GLB_NAME = "steam_brawler"
ROOT_NAME = "SteamBrawlerHQ"
TEX_PREFIX = "brawler"
MAT_NAME = "SteamBrawlerMat"
MESH_NAME = "SteamBrawler"
BASE_MODULE = "steam_brawler_base"
ANIM_MODULE = "anim_steam_brawler"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Moustache", "Cap", "Goggles", "Shirt", "Vest", "Trousers", "Leather", "Brass",
         "Boots", "Boiler", "Firebox", "Hoses", "Gauntlets", "Fists"]
REGION_PARTS = ("Skin", "Cap", "Goggles", "Shirt", "Vest", "Trousers", "Leather", "Boots", "Boiler", "Hoses", "Gauntlets", "Fists")
WORKS = {"name": "HQ_BrawlerSteam"}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_BrawlerSkin", "base": (0.86, 0.6, 0.46), "ruddy": (0.92, 0.45, 0.36), "lips": (0.72, 0.38, 0.33),
                      "brow": ((0.42, 0.16, 0.05), (0.7, 0.36, 0.14)),
                      "extra": ((LASH, (0.3, 0.12, 0.05), 0.5), (STUBBLE, (0.62, 0.42, 0.32), 0.55, 0.3),
                                (SOOT, (0.12, 0.105, 0.1), 0.6, 0.85))}),
    "Hair": ("hair", dict(GINGER, name="HQ_BrawlerHair")),
    "Moustache": ("hair", dict(GINGER, name="HQ_BrawlerWhiskers")),
    "Cap": ("wool", {"name": "HQ_BrawlerCap", "base": (0.33, 0.29, 0.24), "border": (0.2, 0.17, 0.14), "stripe": (0.2, 0.17, 0.14)}),
    "Goggles": ("steamworks", WORKS),
    "Shirt": ("linen", {"name": "HQ_BrawlerShirt", "base": (0.86, 0.82, 0.72), "border": (0.55, 0.5, 0.42), "stripe": (0.8, 0.76, 0.66)}),
    "Vest": ("wool", {"name": "HQ_BrawlerVest", "base": NAVY, "border": (0.1, 0.12, 0.25), "stripe": (0.12, 0.15, 0.3)}),
    "Trousers": ("wool", {"name": "HQ_BrawlerTrousers", "base": (0.36, 0.27, 0.19), "border": (0.27, 0.2, 0.14), "stripe": (0.27, 0.2, 0.14)}),
    "Leather": ("leather_dyed", {"name": "HQ_BrawlerLeather", "base": (0.4, 0.23, 0.12), "dyed": (0.4, 0.23, 0.12)}),
    "Brass": ("bronze", {"name": "HQ_BrawlerBrass", "base": (0.8, 0.58, 0.24), "hi": (1.0, 0.92, 0.6), "dark": (0.38, 0.25, 0.08),
                         "patina": (0.42, 0.44, 0.24)}),
    "Boots": ("steamworks", WORKS),
    "Boiler": ("steamworks", WORKS),
    "Firebox": ("glow_ball", {"name": "HQ_FireboxGlow", "col": (1.0, 0.45, 0.1)}),
    "Hoses": ("steamworks", WORKS),
    "Gauntlets": ("steamworks", WORKS),
    "Fists": ("steamworks", WORKS),
}
GLOW = {"Firebox": ((1.0, 0.42, 0.08), 1.2, 0.5)}
LOW_TARGETS = {"Skin": 5200, "Teeth": 90, "Hair": 500, "Moustache": 1300, "Cap": 1000, "Goggles": 500, "Shirt": 1300,
               "Vest": 1500, "Trousers": 1200, "Leather": 1000, "Brass": 250, "Boots": 900, "Boiler": 2500, "Firebox": 60,
               "Hoses": 700, "Gauntlets": 2300, "Fists": 2500}
AO_EXCLUDE = ["Fists", "Hoses", "Brass", "Goggles"]
# the fists are baked well away from the housings: the rods and the ram that slide out at the blow were inside them at
# rest, and would bake black
BAKE_APART = (["Fists"], (3.0, 0.0, 0.0))


def prop_bones():
    """The fists' rams (free bones the clips keep on the forearms and drive out along them; their heads at the knuckles)
    and the steam vent (on his chest: the boiler is rigid with it)."""
    out = []
    for side in ("R", "L"):
        wr, A, W, M = gframe(side)
        k = knuckle_point(side)
        out.append(("ram." + side, k, k + A * 0.1, None))
    out.append(("vent", STACK_TOP, STACK_TOP + v3((0, 0, 0.08)), "chest"))
    return out


BODY = {"root", "spine", "chest", "neck", "head", "clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R",
        "forearm.L", "thigh.R", "thigh.L", "shin.R", "shin.L", "foot.R", "foot.L"}
SHIRT_BONES = TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L"}


def _clear(ob, v):
    for g in list(ob.vertex_groups):
        g.remove([v.index])


def side_rigid(prefix):
    def fn(ob, skin_ob, arm):
        groups = {}
        for v in ob.data.vertices:
            _clear(ob, v)
            _blend_add(ob, groups, v.index, {prefix + ("R" if v.co.x < 0 else "L"): 1.0})
    return fn


def hose_weights(ob, skin_ob, arm):
    """Along each hose: rigid with his chest at the boiler, with the upper arm along it, into the forearm at the inlet."""
    groups = {}
    lines = {s: np.array(hose_pts(s)) for s in ("R", "L")}
    cum = {}
    for s, P in lines.items():
        L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        cum[s] = L / L[-1]
    for v in ob.data.vertices:
        s = "R" if v.co.x < 0 else "L"
        P = lines[s]
        i = int(np.argmin(np.linalg.norm(P - np.array(v.co), axis=1)))
        t = cum[s][i]
        if t < 0.2:
            w = {"chest": 1.0}
        elif t < 0.42:
            k = (t - 0.2) / 0.22
            k = k * k * (3 - 2 * k)
            w = {"chest": 1.0 - k, "upperarm." + s: k}
        elif t < 0.84:
            w = {"upperarm." + s: 1.0}
        else:
            k = min(1.0, (t - 0.84) / 0.12)
            k = k * k * (3 - 2 * k)
            w = {"upperarm." + s: 1.0 - k, "forearm." + s: k}
        _clear(ob, v)
        _blend_add(ob, groups, v.index, w)


def hair_weights(ob, skin_ob, arm):
    import rig
    rig.rigid_weights(ob, "head")


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Moustache": ("rigid", "head"),
        "Cap": ("rigid", "head"), "Goggles": ("rigid", "head"),
        "Shirt": ("transfer", SHIRT_BONES, None),
        "Vest": ("transfer", TORSO | {"clavicle.R", "clavicle.L"}, None),
        "Trousers": ("transfer", {"root", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Leather": ("transfer", TORSO | {"clavicle.R", "clavicle.L"}, None),
        "Brass": ("transfer", TORSO, None),
        "Boots": ("transfer", {"foot.R", "foot.L", "shin.R", "shin.L"}, None),
        "Boiler": ("rigid", "chest"), "Firebox": ("rigid", "chest"),
        "Hoses": ("custom", hose_weights),
        "Gauntlets": ("custom", side_rigid("forearm.")),
        "Fists": ("custom", side_rigid("ram.")),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Moustache") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part == "Skin" and (c.z < 1.3 and abs(c.x) < 0.42 or c.z < 0.9):
        return 0.3                  # (his body and legs, under his clothes; his forearms inside the housings)
    if part in ("Fists", "Goggles"):
        return 1.15
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Moustache", moustache_field(), 0.0018 if fine else 0.0026),
        ("Cap", cap_field(), 0.0024 if fine else 0.0034),
        ("Goggles", goggles_field(), 0.0015 if fine else 0.0022),
        ("Shirt", shirt_field(), 0.0026 if fine else 0.0036),
        ("Vest", vest_field(), 0.0026 if fine else 0.0036),
        ("Trousers", trousers_field(), 0.0028 if fine else 0.0038),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Brass", brass_field(), 0.0016 if fine else 0.0022),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Boiler", boiler_field(), 0.002 if fine else 0.003),
        ("Firebox", firebox_field(), 0.002),
        ("Hoses", hoses_field(), 0.0022 if fine else 0.003),
        ("Gauntlets", gauntlets_field(), 0.0022 if fine else 0.003),
        ("Fists", fists_field(), 0.0022 if fine else 0.003),
    ]
