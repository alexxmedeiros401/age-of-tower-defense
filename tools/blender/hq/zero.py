"""Unit Zero, Reprogrammed Titan (HQ hero, The Data Center; lobs shells). Rest pose = an A-pose, facing -Y, feet at
z = 0; right side = -X.

The first robot to switch sides: a big, hulking titan (about 2.15 m to the top of his head, 1.75 m across his
pauldrons) that marched with the invaders and now fights for the Resistance. He is still built as one of them: white
robot armour plates (label 13 of the android material) with the invaders' hazard-orange trim (14), gunmetal joints and
frames (5), charcoal plates (6), black rubber (15), steel (10); but the Resistance has made him theirs: big amber
chevrons sprayed over his plates (16), a charcoal "0" stencilled on his chest, a ragged amber Resistance scarf tied
round his left arm, and his red robot eye now glows a warm amber. He has been through things: a dented hull, welded
steel patches over old wounds, scuffed edges.

His head: a rounded white robot helmet sunk forward and low between his shoulders (a gentle giant's stoop), the
invaders' orange stripe over its crown with an amber chevron sprayed over its front; a broad dark-glass visor across
his face with one big round amber eye in it (its own glowing mesh, `GlowEye`): a dark pupil (`Pupil`), a white
catchlight (`GlowSpark`), and its lower edge lifted by a curve, so the eye smiles. The eye rides the `eye` bone (a
child of the head: the clips blink it, scaled flat); for the Cheer a happy arc eye (`GlowSmile`, on `smile`, scaled to
0 elsewhere) takes its place. Under the visor a gunmetal jaw with a grille curved into a smile; steel ear discs, a short
antenna with an amber tip on his right side, a dent and a weld on his crown.

His body: a barrel hull (white, its lower rim in hazard orange, a big amber double chevron over his belly), a charcoal
power pack on his back with two exhaust stacks and an amber chevron, his core in the middle of his chest (an amber
glow in a steel bezel, `GlowCore`, with a brighter, bigger flare over it on the `flare` bone that Overload swells and
bursts: `GlowFlare`), the "0" on his left breast, a welded patch over a crack on his right. Great domed pauldrons
(white, an orange rim band, two amber chevrons over each), white plates on his upper arms, armoured forearm housings
(white, an orange band at the front, an amber slash along the outside). His right arm ends in a stubby shell launcher
(on `hand.R`: a charcoal breech, a drum magazine on its outer side, a gunmetal jacket; the barrel and its muzzle brake
on `barrel`, a child of the hand from the breech to the muzzle, scaled shorter along its length to recoil; the bore
glows amber deep inside, `GlowBore`). His left arm ends in a big three-fingered hand (the palm and thumb on `hand.L`,
the fingers one block on `fingers.L`, hinged across the knuckles). A charcoal pelvis with a white front plate (an amber
chevron), white tassets over the hips; short thick legs: white thigh plates (an amber slash), charcoal knee caps, big
white shin guards (an orange band at the top), charcoal boots with white toe caps and rubber soles.

Machines don't bend: every armour piece rides one bone (as the robots and the Mech Brawler, mech_brawler.py: parts
that hold pieces of several bones are `MultiField`s, each mesh island rigid on its piece's bone). His inner frame (the
"Skin" part: gunmetal limb cores, ball joints, rubber boots round his waist and neck) is skinned from the sculpt, so
it flexes at the joints."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from mech_brawler import MultiField, island_weights, seg_box, dent, smoothstep

# ======================================================================================= labels (mats.android)
FRAME, CHAR, SEAM, CLOTH, TAPE, STEEL, GLASS, FACE, WHITE, ORANGE, RUBBER, AMBER = 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16
AMBER_GLOW = (1.0, 0.62, 0.15)
FLARE_GLOW = (1.0, 0.8, 0.42)

# ======================================================================================= the skeleton
J = {"root": (0.0, 0.03, 0.96)}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.6, 0.06, 1.6)
    J["elbow_" + _s] = (_x * 0.76, 0.13, 1.18)
    J["wrist_" + _s] = (_x * 0.82, 0.04, 0.78)
    J["hip_" + _s] = (_x * 0.25, 0.04, 0.9)
    J["knee_" + _s] = (_x * 0.28, -0.04, 0.53)
    J["ankle_" + _s] = (_x * 0.29, 0.04, 0.18)
    J["toe_" + _s] = (_x * 0.3, -0.3, 0.05)
J = {k: v3(v) for k, v in J.items()}
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.88, 1.05, 1.18, 1.62)
CLAV_Z = 1.6


def torso_bones():
    return {
        "spine": ((0, 0.03, 0.96), (0, 0.03, 1.16)),
        "chest": ((0, 0.03, 1.16), (0, 0.05, 1.6)),
        "neck": ((0, 0.0, 1.62), (0, -0.07, 1.8)),
        "head": ((0, -0.07, 1.8), (0, -0.11, 2.16)),
        "clavicle_z": CLAV_Z,
    }


# ======================================================================================= head space
# (the shared tools place head close-ups at hp((0, 0, 1.7)): design point (0, 0, 1.7) = the middle of his head)
HC = v3((0.0, -0.11, 1.95))
D_HC = v3((0.0, 0.0, 1.7))
HS = 1.0


def hp(p):
    return HC + (v3(p) - D_HC)


def hr(r):
    return r


def hinv(P):
    return P - (HC - D_HC).astype(F)


HEAD_C = HC
EYE_R = 0.06


# ======================================================================================= the arms' frame (as mech_brawler.py)
def gframe(side):
    """The forearm's frame (rest pose): the wrist, A along the forearm (elbow -> wrist), W toward the thumb (forward in
    the A-pose), M toward the palm (medial). -M is the back of the hand (outward)."""
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


def gR(side):
    """Rotation whose local x, y, z are the frame's W, M, A (a box's half sizes given as (v, w, u))."""
    wr, A, W, M = gframe(side)
    return np.stack([W, M, A], axis=1)


def hand_frame(side):
    wr, A, W, M = gframe(side)
    return wr, A, M, W


def eye_c(sx=1):
    return eye_frame()[0]


# ======================================================================================= head (rigid on `head`)
def _head_base():
    """The helmet's shapes (no detail): what the visor, the eye and the paint are placed on."""
    fd = Field("HeadBase")
    fd.add(RoundBox(HC + v3((0, 0.01, -0.005)), (0.222, 0.2, 0.168), 0.14), 0.0, WHITE)
    fd.add(Ellipsoid(HC + v3((0, 0.02, 0.06)), (0.222, 0.205, 0.165)), 0.05, WHITE)
    # the jaw: a gunmetal block under the face, a little forward
    fd.add(RoundBox(HC + v3((0, -0.04, -0.14)), (0.165, 0.15, 0.06), 0.052, R=euler(-0.12, 0, 0)), 0.04, FRAME)
    return fd


_HB = []


def head_base():
    if not _HB:
        _HB.append(_head_base())
    return _HB[0]


def _surf_n(fn, p, h=0.0015):
    p = v3(p)
    g = []
    for i in range(3):
        e = np.zeros(3)
        e[i] = h
        vals = fn(np.array([p + e, p - e], F))
        g.append(float(vals[0] - vals[1]) / (2 * h))
    return norm(v3(g))


def _hit(fn, origin, d, tmax=0.9):
    """First hit of a ray on a distance function (Field or callable) and the normal there."""
    h, ok = ray_hit(fn, [v3(origin)], [v3(d)], tmax=tmax, step=0.001)
    if not ok[0]:
        raise ValueError("ray misses: %s %s" % (origin, d))
    f = fn.eval if isinstance(fn, Field) else fn
    return v3(h[0]), _surf_n(f, h[0])


def _frame(n, up=(0, 0, 1)):
    """Columns (side, up, n): a frame on a surface with normal n."""
    n = norm(n)
    u = norm(v3(up) - n * float(v3(up) @ n))
    s = norm(np.cross(u, n))
    return np.stack([s, u, n], 1)


FACE_N = norm(v3((0.0, -1.0, 0.16)))     # the face looks a little up (it reads from the high camera)
VIS_Z = 1.952                            # the visor's middle (height), its half sizes and corner radius
VIS_H = (0.172, 0.09)
VIS_RC = 0.055
EYE_Z = 1.952
EYE_RAD = 0.08                          # the eye's radius


def face_pt(x, z, lift=0.0):
    """A point on the helmet's face in front of (x, z) (a ray along -FACE_N), lifted `lift` along its normal."""
    o = v3((x, HC[1], z)) + FACE_N * 0.6
    p, n = _hit(head_base(), o, -FACE_N, tmax=0.9)
    return p + n * lift, n


def _face_axes():
    """(side, up, out) of the face plane."""
    return _frame(FACE_N)


def _vis2d(P, grow=0.0):
    """2D rounded-rectangle distance of the visor's outline (projected along FACE_N)."""
    R = _face_axes()
    c = v3((0.0, HC[1], VIS_Z))
    q = (P - c.astype(F)) @ R.astype(F)
    hx, hz = F(VIS_H[0] + grow), F(VIS_H[1] + grow)
    rc = F(VIS_RC)
    dx = np.abs(q[:, 0]) - (hx - rc)
    dz = np.abs(q[:, 1]) - (hz - rc)
    return np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dz, 0) ** 2) + np.minimum(np.maximum(dx, dz), 0) - rc


VIS_DEPTH = 0.02


def eye_frame():
    """(the eye's middle on the visor's floor, frame (side, up, out))."""
    p, n = face_pt(0.0, EYE_Z)
    R = _face_axes()
    return p - R[:, 2] * VIS_DEPTH, R


def _cheek():
    """The ellipsoid that lifts the eye's lower edge (a smiling eye)."""
    p, R = eye_frame()
    return Ellipsoid(p - R[:, 1] * 0.106, (0.092, 0.058, 0.093), R=R)


def _eye_shape(grow=1.0, out=0.0, depth=0.014, smile=True):
    p, R = eye_frame()
    e = Ellipsoid(p + R[:, 2] * out, v3((EYE_RAD * grow, EYE_RAD * 1.06 * grow, depth)), R=R)
    if not smile:
        return e
    return Inter(e, Func(lambda P, c=_cheek(): -c(P), p - 0.25, p + 0.25), 0.003)


def head_field():
    """The white helmet (13): the invaders' orange stripe over its crown (14), an amber chevron (16) sprayed over its
    front; the visor (a recess, dark glass 11) across the face; the gunmetal jaw (5) with a grille (slits curved into a
    smile); steel ear discs (10) with orange rings; the antenna on his right (an amber tip); a dent and a welded steel
    patch."""
    fd = Field("Head")
    hb = head_base()
    for op in hb.ops:
        fd.ops.append(op)
    lo, hi = HC - 0.32, HC + 0.32
    R = _face_axes()
    # the visor: the face's outer 2 cm taken out inside the outline, its floor dark glass
    def recess(P):
        return np.maximum(_vis2d(P), -(hb.eval(P, margin=0.05) + F(VIS_DEPTH)))
    fd.sub(Func(recess, lo, hi), 0.004)
    fd.paint(Func(lambda P: _vis2d(P, 0.004), lo, hi), GLASS)
    # a steel rim round the visor
    def rim(P):
        d = hb.eval(P, margin=0.05)
        return np.maximum(np.abs(_vis2d(P, 0.01)) - F(0.0065), np.abs(d - F(0.001)) - F(0.006))
    fd.add(Func(rim, lo, hi), 0.004, CHAR)
    # the crown's orange stripe (front to back over the top), the amber chevron sprayed over its front
    def stripe(P):
        return np.maximum(np.abs(P[:, 0]) - F(0.042), F(HC[2] + 0.085) - P[:, 2])
    fd.paint(Func(stripe, lo, hi), ORANGE)
    def chevron(P):
        q = (P - v3((0.0, HC[1], 2.075)).astype(F)) @ R.astype(F)
        c = np.abs(q[:, 1] - np.abs(q[:, 0]) * F(0.62) + F(0.01)) - F(0.024)
        return np.maximum(np.maximum(c, np.abs(q[:, 0]) - F(0.15)), F(-0.02) - q[:, 2] - F(0.2))
    fd.paint(Func(chevron, lo, hi), AMBER)
    # the smile: a slot across the jaw curved up at its ends (its light bar is GlowMouth), grille vents beside it
    pts = mouth_points()
    fd.sub(Chain(pts, [0.006, 0.008, 0.0095, 0.0095, 0.0095, 0.0095, 0.0095, 0.008, 0.006], k=0.003), 0.002)
    fd.paint(Chain(pts, [0.011, 0.013, 0.0145, 0.0145, 0.0145, 0.0145, 0.0145, 0.013, 0.011], k=0.003), CHAR)
    for sx in (-1, 1):
        for k in range(3):
            a, _ = face_pt(sx * (0.118 + 0.014 * k), 1.83 + 0.004 * k)
            b, _ = face_pt(sx * (0.118 + 0.014 * k), 1.795 + 0.004 * k)
            fd.sub(RoundCone(a, b, 0.0035, 0.0035), 0.0015)
    # cheek bolts beside the jaw
    for sx in (-1, 1):
        q, n = face_pt(sx * 0.14, 1.855)
        fd.add(Cylinder(q, 0.014, 0.012, rr=0.004, R=rot_from_axes(z_axis=n)), 0.003, STEEL)
    # ear discs (steel, an orange ring) and the antenna on his right
    for sx in (-1, 1):
        c = HC + v3((sx * 0.226, 0.02, -0.005))
        ax = v3((sx, 0.0, 0.0))
        Rr = rot_from_axes(z_axis=ax)
        fd.add(Cylinder(c, 0.07, 0.05, rr=0.014, R=Rr), 0.012, STEEL)
        fd.sub(Torus(c + ax * 0.025, 0.046, 0.005, R=Rr), 0.002)
        fd.add(Cylinder(c + ax * 0.022, 0.026, 0.02, rr=0.006, R=Rr), 0.003, CHAR)
        fd.paint(Torus(c + ax * 0.024, 0.058, 0.007, R=Rr), ORANGE)
    a0 = HC + v3((-0.236, 0.05, 0.035))
    a1 = a0 + v3((-0.035, 0.04, 0.16))
    a2 = a1 + v3((0.005, 0.03, 0.06))
    fd.add(Chain([a0, a1, a2], [0.016, 0.011, 0.009], k=0.01), 0.006, FRAME)
    fd.add(Sphere(a2 + v3((0, 0.004, 0.012)), 0.022), 0.004, AMBER)
    # a dent on his crown (left), a welded patch on its right side, behind the ear
    fd.sub(Sphere(HC + v3((0.11, 0.02, 0.225 + 0.045)), 0.06), 0.03)
    p, n = _hit(hb, HC + v3((-0.6, 0.1, 0.07)), (1, 0, 0))
    Rp = _frame(n)
    fd.add(RoundBox(p + n * 0.002, (0.05, 0.04, 0.007), 0.005, R=Rp), 0.004, STEEL)
    def weld(P, p=p, Rp=Rp):
        q = (P - p.astype(F)) @ Rp.astype(F)
        dx = np.abs(q[:, 0]) - F(0.05)
        dz = np.abs(q[:, 1]) - F(0.04)
        ring = np.abs(np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dz, 0) ** 2) + np.minimum(np.maximum(dx, dz), 0))
        bead = F(0.0006) * NOISE(P * F(260))
        return np.sqrt(ring * ring + (q[:, 2] - F(0.004)) ** 2) - F(0.0055) + bead
    fd.add(Func(weld, p - 0.1, p + 0.1), 0.003, STEEL)
    return fd


MOUTH_Z, MOUTH_W = 1.79, 0.09


def mouth_points(lift=0.0):
    pts = []
    for x in np.linspace(-MOUTH_W, MOUTH_W, 9):
        q, n = face_pt(x, MOUTH_Z + 3.6 * x * x, lift)
        pts.append(q)
    return pts


def mouth_field():
    """The smile's light bar (GlowMouth), in its slot."""
    fd = Field("Mouth")
    pts = mouth_points(-0.003)
    fd.add(Chain(pts, [0.004, 0.0058, 0.0068, 0.007, 0.007, 0.007, 0.0068, 0.0058, 0.004], k=0.002), 0.0)
    return fd


def eye_field():
    """His eye: a domed amber lens on the visor's floor, its lower edge lifted (it smiles)."""
    fd = Field("Eye")
    fd.add(_eye_shape(1.0, 0.002, 0.016), 0.0)
    return fd


def pupil_field():
    """The eye's dark pupil (dark glass 11), on the lens."""
    fd = Field("Pupil")
    p, R = eye_frame()
    fd.add(Ellipsoid(p + R[:, 2] * 0.014 + R[:, 1] * 0.006, (0.031, 0.034, 0.006), R=R), 0.0, GLASS)
    return fd


def spark_field():
    """A white catchlight high on his left of the eye (over the lens and the pupil's edge)."""
    fd = Field("Spark")
    p, R = eye_frame()
    fd.add(Ellipsoid(p + R[:, 1] * 0.032 + R[:, 0] * 0.026 + R[:, 2] * 0.0185, (0.017, 0.019, 0.004), R=R), 0.0)
    fd.add(Ellipsoid(p - R[:, 1] * 0.008 - R[:, 0] * 0.03 + R[:, 2] * 0.017, (0.007, 0.007, 0.003), R=R), 0.0)
    return fd


def smile_field():
    """The happy eye (the Cheer): an arc, open downward (^), glowing amber."""
    fd = Field("Smile")
    p, R = eye_frame()
    pts = []
    for a in np.linspace(math.radians(18), math.radians(162), 9):
        pts.append(p + R[:, 0] * (0.064 * math.cos(a)) + R[:, 1] * (0.058 * math.sin(a) - 0.03) + R[:, 2] * 0.006)
    fd.add(Chain(pts, [0.011, 0.014, 0.016, 0.017, 0.017, 0.017, 0.016, 0.014, 0.011], k=0.006), 0.0)
    return fd


def eye_bone():
    p, R = eye_frame()
    return p, p + R[:, 2] * 0.08


# ======================================================================================= the hull ("Hull")
CORE_Z = 1.38


def _hull_base():
    fd = Field("HullBase")
    fd.add(Ellipsoid((0, 0.04, 1.47), (0.47, 0.33, 0.29)), 0.0, WHITE)
    fd.add(RoundBox((0, 0.05, 1.25), (0.31, 0.24, 0.11), 0.08), 0.12, WHITE)
    fd.add(Ellipsoid((0, -0.1, 1.42), (0.36, 0.23, 0.26)), 0.08, WHITE)
    fd.add(RoundBox((0, 0.17, 1.66), (0.33, 0.18, 0.11), 0.1), 0.1, WHITE)
    return fd


_HUB = []


def hull_base():
    if not _HUB:
        _HUB.append(_hull_base())
    return _HUB[0]


def hull_pt(x, z, front=True, lift=0.0):
    d = v3((0, -1, 0)) if front else v3((0, 1, 0))
    p, n = _hit(hull_base(), v3((x, 0.05, z)) + d * 0.8, -d)
    return p + n * lift, n


def core_frame():
    p, n = hull_pt(0.0, CORE_Z)
    return p, _frame(n)


def _chev2d(q0, q1, apex, slope, w, half):
    """A chevron pointing down (-q1) in 2D: its apex at q1 = apex, arms rising `slope` per unit out, `w` half thick."""
    c = np.abs(q1 - F(apex) - np.abs(q0) * F(slope)) - F(w)
    return np.maximum(c, np.abs(q0) - F(half))


def hull_chest(fd):
    """The barrel hull (white 13): the chest bulge, a cowl rising behind the head, the neck's opening; its lower rim in
    hazard orange (14); the core's steel bezel (10) and its vents; the amber double chevron (16) over his belly; the "0"
    stencilled in charcoal (6) on his left breast; a welded steel patch over a crack on his right breast; dents."""
    hb = hull_base()
    for op in hb.ops:
        fd.ops.append(op)
    lo, hi = v3((-0.6, -0.5, 1.0)), v3((0.6, 0.6, 1.9))
    # the neck's opening (the head sits forward, low in it)
    fd.sub(Ellipsoid((0, -0.06, 1.8), (0.2, 0.2, 0.13)), 0.05)
    # the lower rim in hazard orange, a seam over it
    fd.paint(Func(lambda P: np.maximum(P[:, 2] - F(1.225), F(1.0) - P[:, 2]), lo, hi), ORANGE)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(1.231)) - F(0.004), lo, hi), SEAM)
    # side panel lines, a seam round the cowl
    for sx in (-1, 1):
        fd.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 0] - F(sx * 0.33)) - F(0.004), np.maximum(P[:, 2] - F(1.6), F(1.24) - P[:, 2])), lo, hi), SEAM)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 1] - F(0.03)) - F(0.004), F(1.6) - P[:, 2]), lo, hi), SEAM)
    # the core's bezel: a raised steel ring round a recess, six short vents round it
    p, R = core_frame()
    n = R[:, 2]
    fd.add(Torus(p + n * 0.006, 0.108, 0.022, R=R), 0.008, STEEL)
    fd.sub(Ellipsoid(p - n * 0.01, (0.092, 0.092, 0.05), R=R), 0.006)
    fd.paint(Ellipsoid(p - n * 0.01, (0.1, 0.1, 0.07), R=R), CHAR)
    for k in range(6):
        a = math.radians(30 + 60 * k)
        d = R[:, 0] * math.cos(a) + R[:, 1] * math.sin(a)
        fd.sub(RoundCone(p + d * 0.16, p + d * 0.2, 0.011, 0.011), 0.003)
        fd.paint(RoundCone(p + d * 0.16, p + d * 0.2, 0.017, 0.017), SEAM)
    # the amber double chevron over his belly (pointing down)
    def belly(P):
        q = P[:, 0], P[:, 2]
        a = _chev2d(q[0], q[1], 1.235, 0.55, 0.026, 0.25)
        b = _chev2d(q[0], q[1], 1.165, 0.55, 0.022, 0.25)
        return np.maximum(np.minimum(a, b), P[:, 1] - F(-0.05))
    fd.paint(Func(belly, lo, hi), AMBER)
    # the "0" on his left breast (a stencil: two bridges)
    zc = hull_pt(0.215, 1.535)[0]
    def zero(P):
        x = (P[:, 0] - F(zc[0])) / F(0.058)
        z = (P[:, 2] - F(zc[2])) / F(0.088)
        r = np.sqrt(x * x + z * z)
        ring = np.abs(r - F(1.0)) * F(0.07) - F(0.0165)
        bridge = F(0.009) - np.abs(P[:, 0] - F(zc[0]))
        ring = np.where(np.abs(z) > F(0.6), np.maximum(ring, bridge), ring)
        return np.maximum(ring, P[:, 1] - F(zc[1] + 0.12))
    fd.paint(Func(zero, zc - 0.2, zc + 0.2), CHAR)
    # a welded patch over a crack on his right breast
    p2, n2 = hull_pt(-0.25, 1.49)
    R2 = _frame(n2) @ euler(0, 0, 0.18)
    crack = [p2 + R2 @ v3((x, z, -0.001)) for x, z in ((-0.12, -0.09), (-0.08, -0.05), (-0.09, -0.02), (-0.04, 0.0),
                                                        (0.0, 0.03), (0.04, 0.02), (0.08, 0.06), (0.12, 0.08))]
    fd.sub(Chain(crack, [0.004] * len(crack), k=0.002), 0.002)
    fd.paint(Chain(crack, [0.008] * len(crack), k=0.003), SEAM)
    fd.add(RoundBox(p2 + n2 * 0.003, (0.065, 0.05, 0.008), 0.006, R=R2), 0.005, STEEL)
    def weld(P, p=p2, Rp=R2):
        q = (P - p.astype(F)) @ Rp.astype(F)
        dx = np.abs(q[:, 0]) - F(0.065)
        dz = np.abs(q[:, 1]) - F(0.05)
        ring = np.abs(np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dz, 0) ** 2) + np.minimum(np.maximum(dx, dz), 0))
        bead = F(0.0007) * NOISE(P * F(240))
        return np.sqrt(ring * ring + (q[:, 2] - F(0.006)) ** 2) - F(0.0065) + bead
    fd.add(Func(weld, p2 - 0.12, p2 + 0.12), 0.003, STEEL)
    for sx in (-1, 1):
        for sz in (-1, 1):
            fd.add(Sphere(p2 + R2 @ v3((sx * 0.044, sz * 0.03, 0.011)), 0.008), 0.002, STEEL)
    # dents
    for c, r in (((0.3, -0.33, 1.27), 0.07), ((-0.12, -0.36, 1.6), 0.05), ((0.4, 0.2, 1.5), 0.08)):
        q, nq = hull_pt(c[0], c[2]) if c[1] < 0 else _hit(hull_base(), v3((0.9, c[1], c[2])), (-1, 0, 0))
        fd.sub(Sphere(q + nq * (r * 0.82), r), 0.03)


def back_pack(fd):
    """The power pack on his back (charcoal 6): cooling fins, two exhaust stacks (gunmetal 5, black bores), an amber
    chevron (16) sprayed over it; the cowl's hazard band."""
    fd.add(RoundBox((0, 0.4, 1.44), (0.27, 0.1, 0.2), 0.06), 0.03, CHAR)
    for k in range(6):
        fd.add(RoundBox((-0.15 + 0.06 * k, 0.5, 1.38), (0.012, 0.03, 0.11), 0.008), 0.004, CHAR)
    for sx in (-1, 1):
        fd.add(Cylinder((sx * 0.17, 0.44, 1.7), 0.055, 0.22, rr=0.015), 0.012, FRAME)
        fd.sub(Cylinder((sx * 0.17, 0.44, 1.78), 0.035, 0.1, rr=0.005), 0.004)
        fd.paint(Cylinder((sx * 0.17, 0.44, 1.77), 0.04, 0.1), SEAM)
        fd.paint(Torus((sx * 0.17, 0.44, 1.75), 0.057, 0.008), ORANGE)
    lo, hi = v3((-0.4, 0.3, 1.2)), v3((0.4, 0.6, 1.7))
    fd.paint(Func(lambda P: np.maximum(_chev2d(P[:, 0], P[:, 2], 1.5, 0.6, 0.03, 0.22), F(0.47) - P[:, 1]), lo, hi), AMBER)


def collar(fd):
    """A gunmetal collar ring round the neck's opening."""
    fd.add(Torus((0, -0.06, 1.71), 0.155, 0.03, R=euler(-0.25, 0, 0)), 0.01, FRAME)


def pelvis(fd):
    """The charcoal pelvis (6), a white front plate (13) with an amber chevron, white tassets over the hips."""
    fd.add(RoundBox((0, 0.04, 0.96), (0.33, 0.22, 0.085), 0.06), 0.0, CHAR)
    Rf = euler(-0.18, 0, 0)
    c = v3((0, -0.19, 0.91))
    fd.add(RoundBox(c, (0.15, 0.04, 0.1), 0.04, R=Rf), 0.01, WHITE)
    fd.paint(Func(lambda P: np.maximum(_chev2d(P[:, 0], P[:, 2], 0.885, 0.6, 0.022, 0.12), P[:, 1] + F(0.18)), c - 0.3, c + 0.3), AMBER)
    for sx in (-1, 1):
        t = v3((sx * 0.39, 0.02, 0.9))
        fd.add(RoundBox(t, (0.06, 0.15, 0.1), 0.045, R=euler(0, sx * 0.25, 0)), 0.01, WHITE)
        fd.paint(RoundBox(t + v3((0, 0, -0.08)), (0.2, 0.3, 0.025), 0.0), ORANGE)


def waist_plates(fd):
    """Two charcoal bands round the waist's rubber boot."""
    for z in (1.07, 1.13):
        fd.add(Torus((0, 0.04, z), 0.2, 0.026, R=np.diag([1.0, 0.85, 1.0])), 0.0, CHAR)


def hull_field():
    subs = [("root", Field("HullPelvis")), ("spine", Field("HullWaist")), ("chest", Field("HullChest"))]
    pelvis(subs[0][1])
    waist_plates(subs[1][1])
    hull_chest(subs[2][1])
    back_pack(subs[2][1])
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        f = Field("HullShoulder" + side)                          # the shoulder actuator (on the clavicle)
        sh = J["shoulder_" + side]
        f.add(Cylinder(sh + v3((-sx * 0.1, 0, 0)), 0.13, 0.14, rr=0.035, R=rot_from_axes(z_axis=(1, 0, 0))), 0.0, FRAME)
        f.add(Torus(sh + v3((-sx * 0.03, 0, 0)), 0.11, 0.018, R=rot_from_axes(z_axis=(1, 0, 0))), 0.005, CHAR)
        subs.append(("clavicle." + side, f))
    return MultiField("Hull", subs)


def core_field():
    """The core's glow (GlowCore): an amber dome in the bezel."""
    fd = Field("Core")
    p, R = core_frame()
    fd.add(Ellipsoid(p - R[:, 2] * 0.008, (0.088, 0.088, 0.034), R=R), 0.0)
    return fd


def flare_field():
    """The core's flare (GlowFlare, Overload): a bigger, brighter dome over the core (on `flare`, 0 elsewhere)."""
    fd = Field("Flare")
    p, R = core_frame()
    fd.add(Ellipsoid(p + R[:, 2] * 0.012, (0.13, 0.13, 0.04), R=R), 0.0)
    return fd


def flare_bone():
    p, R = core_frame()
    return p, p + R[:, 2] * 0.1


# ======================================================================================= arms ("Arms")
def pauldron_c(side):
    sx = -1 if side == "R" else 1
    return J["shoulder_" + side] + v3((sx * 0.05, 0.0, 0.1))


PD = (0.25, 0.27, 0.21)


def pauldron(fd, side):
    """A great domed pauldron (white 13) over the shoulder, its edge flared out with a charcoal lip (6); an orange band
    (14) round it above the lip; two amber chevrons (16) over its crown, pointing out along the arm."""
    sx = -1 if side == "R" else 1
    c = pauldron_c(side)
    cut = norm(v3((sx * 0.35, 0.0, 1.0)))
    lo, hi = c - 0.4, c + 0.4
    def cap(P, c=c, cut=cut):
        return F(-0.11) - (P - c.astype(F)) @ cut.astype(F)
    fd.add(Inter(Ellipsoid(c, PD), Func(cap, lo, hi), 0.02), 0.0, WHITE)
    def lip(P, c=c, cut=cut):
        s = (P - c.astype(F)) @ cut.astype(F)
        return np.maximum(np.abs(s + F(0.1)) - F(0.022), Ellipsoid(c, v3(PD) + 0.022)(P))
    fd.add(Func(lip, lo, hi), 0.008, CHAR)
    fd.paint(Func(lambda P, c=c, cut=cut: np.abs((P - c.astype(F)) @ cut.astype(F) + F(0.045)) - F(0.022), lo, hi), ORANGE)
    def chev(P, c=c):
        a = (P[:, 0] - F(c[0])) * F(sx)
        b = P[:, 1] - F(c[1])
        d = np.minimum(np.abs(a - F(0.02) + np.abs(b) * F(0.75)) - F(0.03), np.abs(a - F(0.115) + np.abs(b) * F(0.75)) - F(0.026))
        return np.maximum(np.maximum(d, np.abs(b) - F(0.2)), F(c[2] + 0.02) - P[:, 2])
    fd.paint(Func(chev, lo, hi), AMBER)
    if side == "L":                                   # a dent in the left one
        fd.sub(Sphere(c + norm(v3((0.5, -0.6, 0.65))) * 0.27, 0.06), 0.03)


def upperarm_plate(fd, side):
    sx = -1 if side == "R" else 1
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    a, b = lerp(sh, el, 0.3), lerp(sh, el, 0.9)
    fd.add(seg_box(a + v3((sx * 0.025, 0, 0)), b + v3((sx * 0.02, 0, 0)), (0.135, 0.145), 0.06, side_ref=(1, 0, 0)), 0.0, WHITE)
    fd.paint(seg_box(lerp(a, b, 0.92), lerp(a, b, 0.92) + norm(b - a) * 0.01, (0.3, 0.3), 0.0), SEAM)


H_FRONT = -0.03             # the forearm housing's front end (u, from the wrist)
HR0, HR1 = 0.16, 0.19      # its radius at the elbow end and at the front


def h_rad(u):
    return F(HR0) + F(HR1 - HR0) * np.clip((u + F(0.34)) / F(0.3), 0, 1)


def forearm_housing(fd, side):
    """The forearm housing (white): a tapered tube cut on a slant at the elbow, a charcoal flange at its front with an
    orange band behind it, an amber slash along its outer side, a charcoal elbow guard."""
    wr, A, W, M = gframe(side)
    c = gp(side, -0.18, 0, 0)

    def tube(P, side=side):
        u, v, w = _uvw(P, side)
        rad = np.sqrt(v * v + w * w)
        dr = rad - h_rad(u)
        du = np.maximum(F(-0.36) + F(0.45) * v - u, u - F(H_FRONT))
        rr = F(0.03)
        qx, qy = dr + rr, du + rr
        return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - rr
    fd.add(Func(tube, c - 0.36, c + 0.36, disp=dent(0.0006, 30), disp_amp=0.0008), 0.0, WHITE)

    def flange(P, side=side):
        u, v, w = _uvw(P, side)
        return np.maximum(np.abs(u - F(H_FRONT - 0.025)) - F(0.02), np.sqrt(v * v + w * w) - (h_rad(u) + F(0.014)))
    fd.add(Func(flange, c - 0.36, c + 0.36), 0.008, CHAR)
    lo, hi = c - 0.36, c + 0.36
    fd.paint(Func(lambda P, side=side: np.abs(_uvw(P, side)[0] + F(0.105)) - F(0.03), lo, hi), ORANGE)
    # the amber slash along the outer side (the back of the hand's side, -M), on a slant
    def slash(P, side=side):
        u, v, w = _uvw(P, side)
        return np.maximum(np.maximum(np.abs(v - (u + F(0.22)) * F(0.5)) - F(0.03), np.abs(u + F(0.22)) - F(0.085)), w + F(0.06))
    fd.paint(Func(slash, lo, hi), AMBER)
    eg = gp(side, -0.38, 0, 0) + gdir(side, 150) * 0.05
    fd.add(Ellipsoid(eg, (0.12, 0.1, 0.09), R=gR(side)), 0.03, CHAR)


def arms_field():
    subs = []
    for side in ("R", "L"):
        f = Field("ArmsPauldron" + side)
        pauldron(f, side)
        subs.append(("clavicle." + side, f))
        f = Field("ArmsUpper" + side)
        upperarm_plate(f, side)
        subs.append(("upperarm." + side, f))
        f = Field("ArmsFore" + side)
        forearm_housing(f, side)
        subs.append(("forearm." + side, f))
    return MultiField("Arms", subs)


# ======================================================================================= the shell launcher (right arm)
BARREL_U0, MUZZLE_U = 0.05, 0.43          # the barrel: from inside the jacket to the muzzle (u, from the wrist)
BORE_R = 0.064
DRUM_DIR = 60.0                           # the drum magazine: this far round from the thumb side toward the back


def launcher_body(fd):
    """On `hand.R`: a gunmetal wrist cuff (5), the charcoal breech block (6) with an amber band (16) and a white stencil,
    the drum magazine on its outer side (charcoal, steel bolts, an orange hazard rim), a gunmetal jacket the barrel
    slides in, cables from the housing into the breech (rubber 15)."""
    side = "R"
    wr, A, W, M = gframe(side)
    R = gR(side)
    fd.add(Cylinder(gp(side, 0.0, 0, 0), 0.15, 0.07, rr=0.02, R=rot_from_axes(z_axis=A)), 0.0, FRAME)
    fd.add(RoundBox(gp(side, 0.09, 0, 0), (0.15, 0.15, 0.075), 0.055, R=R), 0.02, CHAR)
    fd.paint(Func(lambda P: np.abs(_uvw(P, side)[0] - F(0.09)) - F(0.022), gp(side, 0.09, 0, 0) - 0.3, gp(side, 0.09, 0, 0) + 0.3), AMBER)
    fd.add(Cylinder(gp(side, 0.2, 0, 0), 0.112, 0.15, rr=0.02, R=rot_from_axes(z_axis=A)), 0.01, FRAME)
    fd.add(Torus(gp(side, 0.272, 0, 0), 0.112, 0.013, R=rot_from_axes(z_axis=A)), 0.004, CHAR)
    # the drum magazine
    e = gdir(side, DRUM_DIR)
    dc = gp(side, 0.1, 0, 0) + e * 0.18
    Rd = rot_from_axes(z_axis=A)
    fd.add(Cylinder(dc, 0.095, 0.15, rr=0.025, R=Rd), 0.02, CHAR)
    fd.add(Cylinder(dc + A * 0.08, 0.06, 0.02, rr=0.006, R=Rd), 0.004, FRAME)
    fd.paint(Func(lambda P: np.abs(np.sqrt(((P - dc.astype(F)) ** 2).sum(1) - ((P - dc.astype(F)) @ A.astype(F)) ** 2) - F(0.095)) - F(0.012)
                  + np.maximum(np.abs((P - dc.astype(F)) @ A.astype(F)) - F(0.06), 0), dc - 0.2, dc + 0.2), ORANGE)
    for k in range(5):
        a = 2 * math.pi * k / 5
        b = norm(np.cross(A, e))
        q = dc + A * 0.078 + (e * math.cos(a) + b * math.sin(a)) * 0.074
        fd.add(Sphere(q, 0.01), 0.002, STEEL)
    # a sight block on its top (the thumb side)
    fd.add(RoundBox(gp(side, 0.13, 0.135, 0), (0.025, 0.02, 0.05), 0.01, R=R), 0.008, FRAME)
    # cables from the housing's front into the breech
    for k, ph in enumerate((200.0, 250.0)):
        d = gdir(side, ph)
        pts = [gp(side, -0.06, 0, 0) + d * 0.16, gp(side, -0.01, 0, 0) + d * 0.2, gp(side, 0.05, 0, 0) + d * 0.155]
        fd.add(Chain(pts, [0.018] * 3, k=0.01), 0.006, RUBBER)


def barrel(fd):
    """On `barrel`: the gunmetal barrel (5) and the charcoal muzzle brake (6, two side ports), the bore dark inside."""
    side = "R"
    wr, A, W, M = gframe(side)
    Ra = rot_from_axes(z_axis=A)
    c = gp(side, (BARREL_U0 + MUZZLE_U - 0.06) / 2, 0, 0)
    fd.add(Cylinder(c, 0.088, MUZZLE_U - 0.06 - BARREL_U0, rr=0.012, R=Ra), 0.0, FRAME)
    fd.add(Cylinder(gp(side, MUZZLE_U - 0.045, 0, 0), 0.12, 0.09, rr=0.024, R=Ra), 0.012, CHAR)
    for s in (-1, 1):
        fd.sub(RoundBox(gp(side, MUZZLE_U - 0.045, 0, s * 0.115), (0.05, 0.03, 0.022), 0.01, R=gR(side)), 0.004)
    fd.sub(Cylinder(gp(side, MUZZLE_U - 0.05, 0, 0), BORE_R, 0.24, rr=0.004, R=Ra), 0.006)
    fd.paint(Cylinder(gp(side, MUZZLE_U - 0.05, 0, 0), BORE_R + 0.004, 0.24, R=Ra), SEAM)


def launcher_field():
    subs = [("hand.R", Field("LauncherBody")), ("barrel", Field("LauncherBarrel"))]
    launcher_body(subs[0][1])
    barrel(subs[1][1])
    return MultiField("Launcher", subs)


def bore_field():
    """The bore's glow (GlowBore): an amber disc deep inside the barrel."""
    fd = Field("Bore")
    wr, A, W, M = gframe("R")
    fd.add(Ellipsoid(gp("R", MUZZLE_U - 0.09, 0, 0), (BORE_R - 0.004, BORE_R - 0.004, 0.012), R=rot_from_axes(z_axis=A)), 0.0)
    return fd


def barrel_bone():
    return gp("R", BARREL_U0, 0, 0), gp("R", MUZZLE_U, 0, 0)


def muzzle_point():
    return gp("R", MUZZLE_U, 0, 0)


# ======================================================================================= the big hand (left arm)
FINGER_V = (0.088, 0.0, -0.088)            # index (thumb side) .. ring
HINGE_U, HINGE_W = 0.19, -0.02


def finger_hinge(side="L"):
    return gp(side, HINGE_U, 0.0, HINGE_W)


def hand_palm(fd):
    """On `hand.L`: a gunmetal wrist cuff (5), the hand's white back plate (13, an orange edge) over a gunmetal palm,
    the armoured thumb."""
    side = "L"
    wr, A, W, M = gframe(side)
    R = gR(side)
    fd.add(Cylinder(gp(side, 0.01, 0, 0), 0.135, 0.07, rr=0.02, R=rot_from_axes(z_axis=A)), 0.0, FRAME)
    fd.add(RoundBox(gp(side, 0.11, 0.0, 0.015), (0.14, 0.06, 0.095), 0.048, R=R), 0.02, FRAME)
    fd.add(RoundBox(gp(side, 0.105, 0.0, -0.045), (0.145, 0.032, 0.1), 0.03, R=R), 0.02, WHITE)
    fd.paint(Func(lambda P: np.maximum(np.abs(_uvw(P, side)[0] - F(0.03)) - F(0.016), _uvw(P, side)[2] + F(0.02)),
                  gp(side, 0.1, 0, 0) - 0.3, gp(side, 0.1, 0, 0) + 0.3), ORANGE)
    th = [gp(side, 0.05, 0.12, 0.03), gp(side, 0.12, 0.18, 0.07), gp(side, 0.19, 0.17, 0.1), gp(side, 0.235, 0.125, 0.11)]
    fd.add(Chain(th, [0.052, 0.049, 0.045, 0.04], k=0.012), 0.02, FRAME)
    fd.add(RoundBox(gp(side, 0.13, 0.18, 0.05), (0.04, 0.034, 0.055), 0.02, R=R @ euler(0, 0, -0.3)), 0.012, WHITE)


def hand_fingers(fd):
    """On `fingers.L`: three thick fingers, gently curled (gunmetal segments 5, white plates on their backs 13, rubber
    pads 15)."""
    side = "L"
    R = gR(side)
    for i, v in enumerate(FINGER_V):
        s = 0.94 if i == 2 else 1.0
        du = -0.012 if i == 2 else 0.0
        K1 = gp(side, 0.195 + du, v, -0.02)
        K2 = gp(side, 0.29 + du, v, -0.005)
        K3 = gp(side, 0.36 + du, v * 1.02, 0.035)
        K4 = gp(side, 0.385 + du, v * 1.03, 0.085)
        fd.add(Chain([K1, K2, K3, K4], [r * s for r in (0.047, 0.045, 0.041, 0.036)], k=0.01), 0.008, FRAME)
        fd.add(RoundBox(gp(side, 0.27 + du, v, -0.038), (0.04 * s, 0.02, 0.055), 0.015, R=R), 0.01, WHITE)
        fd.add(Sphere(gp(side, 0.372 + du, v * 1.03, 0.092), 0.031 * s), 0.008, RUBBER)
    fd.add(RoundBox(gp(side, 0.205, 0.0, -0.032), (0.14, 0.045, 0.032), 0.026, R=R), 0.012, CHAR)


def hand_field():
    subs = [("hand.L", Field("HandPalm")), ("fingers.L", Field("HandFingers"))]
    hand_palm(subs[0][1])
    hand_fingers(subs[1][1])
    return MultiField("Hand", subs)


# ======================================================================================= legs ("Legs")
def thigh_plate(fd, side):
    sx = -1 if side == "R" else 1
    hp_, kn = J["hip_" + side], J["knee_" + side]
    a, b = lerp(hp_, kn, 0.08), lerp(hp_, kn, 0.84)
    off = v3((sx * 0.03, -0.05, 0))
    fd.add(seg_box(a + off, b + off, (0.19, 0.145), 0.07, side_ref=(1, 0, 0)), 0.0, WHITE)
    fd.add(seg_box(a + v3((sx * 0.04, 0.06, 0)), lerp(a, b, 0.8) + v3((sx * 0.04, 0.06, 0)), (0.14, 0.1), 0.05, side_ref=(1, 0, 0)), 0.03, CHAR)
    m = lerp(a, b, 0.5) + off
    def slash(P, m=m):
        return np.maximum(np.maximum(np.abs((P[:, 2] - F(m[2])) - (P[:, 0] - F(m[0])) * F(-sx * 0.8)) - F(0.028),
                                     np.abs(P[:, 0] - F(m[0])) - F(0.12)), P[:, 1] - F(m[1] - 0.04))
    fd.paint(Func(slash, m - 0.3, m + 0.3), AMBER)
    if side == "L":                                   # a welded patch on the left thigh's outer side
        p = lerp(a, b, 0.4) + off + v3((0.195, 0.0, 0.0))
        fd.add(RoundBox(p, (0.008, 0.05, 0.06), 0.005), 0.004, STEEL)
        fd.add(Torus(p + v3((0.004, 0, 0)), 0.055, 0.0055, R=rot_from_axes(z_axis=(1, 0, 0)),
                     disp=lambda P: F(0.0007) * NOISE(P * F(240)), disp_amp=0.001), 0.003, STEEL)


def shin_guard(fd, side):
    """A charcoal knee cap, a big white shin guard (an orange band at its top, a front ridge)."""
    sx = -1 if side == "R" else 1
    kn, an = J["knee_" + side], J["ankle_" + side]
    fd.add(Ellipsoid(kn + v3((0, -0.125, 0.02)), (0.15, 0.09, 0.13)), 0.0, CHAR)
    a, b = lerp(kn, an, 0.12), lerp(kn, an, 0.95)
    fd.add(seg_box(a + v3((0, -0.03, 0)), b + v3((0, -0.01, 0)), (0.2, 0.175), 0.08, side_ref=(1, 0, 0)), 0.02, WHITE)
    fd.add(seg_box(lerp(a, b, 0.1) + v3((0, -0.14, 0)), lerp(a, b, 0.85) + v3((0, -0.12, 0)), (0.06, 0.03), 0.025, side_ref=(1, 0, 0)), 0.03, WHITE)
    zt = lerp(a, b, 0.12)[2]
    fd.paint(Func(lambda P, zt=zt: np.abs(P[:, 2] - F(zt)) - F(0.03), a - 0.3, b + 0.3), ORANGE)
    if side == "R":
        fd.sub(Sphere(lerp(a, b, 0.6) + v3((-0.06, -0.24, 0)), 0.06), 0.03)


def boot(fd, side):
    """A charcoal boot, a white toe cap with an amber stripe, a rubber sole."""
    an = J["ankle_" + side]
    fd.add(RoundBox(an + v3((0, -0.07, -0.11)), (0.175, 0.26, 0.065), 0.05), 0.0, CHAR)
    fd.add(RoundBox(an + v3((0, -0.235, -0.11)), (0.165, 0.11, 0.065), 0.045, R=euler(0.1, 0, 0)), 0.02, WHITE)
    fd.add(RoundBox(an + v3((0, 0.13, -0.11)), (0.13, 0.07, 0.07), 0.04), 0.02, CHAR)
    fd.add(RoundBox(an + v3((0, -0.06, -0.162)), (0.18, 0.28, 0.02), 0.012), 0.008, RUBBER)
    c = an + v3((0, -0.26, -0.08))
    fd.paint(Func(lambda P, c=c: np.maximum(np.abs(P[:, 0] - F(c[0])) - F(0.03), P[:, 2] - F(c[2] + 0.1)), c - 0.2, c + 0.2), AMBER)


def legs_field():
    subs = []
    for side in ("R", "L"):
        f = Field("LegsThigh" + side)
        thigh_plate(f, side)
        subs.append(("thigh." + side, f))
        f = Field("LegsShin" + side)
        shin_guard(f, side)
        subs.append(("shin." + side, f))
        f = Field("LegsFoot" + side)
        boot(f, side)
        subs.append(("foot." + side, f))
    return MultiField("Legs", subs)


# ======================================================================================= the inner frame ("Skin")
def skin_field():
    """Gunmetal limb cores and ball joints (5), rubber boots (15) round the waist and the neck."""
    fd = Field("Skin")
    fd.add(RoundBox((0, 0.04, 0.95), (0.22, 0.15, 0.075), 0.05), 0.0, FRAME)
    fd.add(Cylinder((0, 0.04, 1.1), 0.17, 0.17, rr=0.03), 0.0, RUBBER)
    for z in (1.04, 1.1, 1.16):
        fd.add(Torus((0, 0.04, z), 0.17, 0.02), 0.01, RUBBER)
    na, nb = v3((0, 0.0, 1.6)), v3((0, -0.07, 1.82))
    fd.add(RoundCone(na, nb, 0.105, 0.095), 0.0, RUBBER)
    for t in (0.3, 0.55, 0.8):
        fd.add(Torus(lerp(na, nb, t), 0.1, 0.014, R=rot_from_axes(z_axis=norm(nb - na))), 0.006, RUBBER)
    for side in ("R", "L"):
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        hp_, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        fd.add(Sphere(sh, 0.13), 0.0, FRAME)
        fd.add(RoundCone(lerp(sh, el, 0.15), el, 0.1, 0.09), 0.02, FRAME)
        hz = norm(np.cross(norm(el - sh), norm(wr - el)))
        fd.add(Cylinder(el, 0.11, 0.2, rr=0.035, R=rot_from_axes(z_axis=hz)), 0.01, FRAME)
        fd.add(RoundCone(lerp(el, wr, 0.1), lerp(el, wr, 0.75), 0.075, 0.07), 0.01, FRAME)
        fd.add(Sphere(wr, 0.085), 0.0, FRAME)
        fd.add(Sphere(hp_, 0.11), 0.0, FRAME)
        fd.add(RoundCone(lerp(hp_, kn, 0.1), kn, 0.115, 0.1), 0.02, FRAME)
        fd.add(Cylinder(kn, 0.11, 0.24, rr=0.035, R=rot_from_axes(z_axis=(1, 0, 0))), 0.01, FRAME)
        fd.add(RoundCone(lerp(kn, an, 0.1), an, 0.1, 0.09), 0.01, FRAME)
        fd.add(Sphere(an, 0.1), 0.0, FRAME)
    return fd


# ======================================================================================= the Resistance scarf ("Cloth")
SCARF_T = 0.6


def _ua_hull():
    side = "L"
    f = Field("UAHull")
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    a, b = lerp(sh, el, 0.3), lerp(sh, el, 0.9)
    f.add(seg_box(a + v3((0.025, 0, 0)), b + v3((0.02, 0, 0)), (0.135, 0.145), 0.06, side_ref=(1, 0, 0)), 0.0)
    f.add(RoundCone(lerp(sh, el, 0.15), el, 0.085, 0.075), 0.02)
    return f


def _seg(P, a, b):
    ab = (b - a).astype(F)
    t = ((P - a.astype(F)) @ ab) / F(ab @ ab)
    tc = np.clip(t, 0, 1)
    return np.sqrt((((a.astype(F) + tc[:, None] * ab) - P) ** 2).sum(1)), t


def scarf_knot():
    sh, el = J["shoulder_L"], J["elbow_L"]
    ax = norm(el - sh)
    out = norm(v3((0.75, -0.6, 0.0)) - ax * float(v3((0.75, -0.6, 0.0)) @ ax))
    c = lerp(sh, el, SCARF_T)
    p, n = _hit(lambda P: _ua_hull().eval(P, margin=0.1) - F(0.04), c + out * 0.5, -out)
    return p, n, ax


def cloth_field():
    """Amber cloth (8): the scarf wound twice round his left upper arm over its plate, knotted at the front-outside, two
    ragged tails hanging from the knot."""
    fd = Field("Cloth")
    sh, el = J["shoulder_L"], J["elbow_L"]
    ua = _ua_hull()
    folds = lambda P: F(0.0022) * NOISE(P * F(26)) + F(0.001) * NOISE(P * F(70))
    for t0, w in ((SCARF_T - 0.035, 0.05), (SCARF_T + 0.06, 0.042)):
        def band(P, t0=t0, w=w):
            d, t = _seg(P, sh, el)
            return np.maximum(np.abs(t - F(t0)) * F(np.linalg.norm(el - sh)) - F(w), d - F(0.25))
        fd.add(Inter(Func(band, sh - 0.35, el + 0.35), Shell(ua, 0.026, 0.024, pad=0.06, disp=folds, disp_amp=0.003), 0.006), 0.006, CLOTH)
    k, kn, ax = scarf_knot()
    Rk = _frame(kn, up=-ax)
    fd.add(Ellipsoid(k + kn * 0.006, (0.045, 0.036, 0.034), R=Rk @ euler(0, 0, 0.5), disp=lambda P: F(0.002) * NOISE(P * F(30)),
                     disp_amp=0.003), 0.012, CLOTH)
    rag = lambda P: F(0.002) * NOISE(P * F(26))
    side_dir = norm(np.cross(ax, kn))
    for s, L, sp in ((1, 0.2, 0.35), (-1, 0.16, -0.25)):
        pts, nrm = [], []
        for i in range(5):
            t = i / 4.0
            q = k + kn * (0.012 + 0.03 * t * t) + ax * (0.02 + L * t) + side_dir * (sp * 0.12 * t + s * 0.012)
            pts.append(q)
            nrm.append(kn)
        fd.add(Lock(pts, list(np.linspace(0.05, 0.062, 5)), [0.011] * 5, nrm, k=0.01, overlap=1.9, disp=rag, disp_amp=0.002), 0.008, CLOTH)
        e, e0 = pts[-1], pts[-2]
        d = norm(e - e0)
        Rn = rot_from_axes(z_axis=d, y_axis=kn)
        for j, o in enumerate((-0.6, 0.05, 0.62)):
            fd.sub(Ellipsoid(e + d * (0.004 + 0.01 * (j % 2)) + Rn[:, 0] * (o * 0.062), (0.012, 0.03, 0.026), R=Rn), 0.003)
    # a dark stripe near each tail's end
    fd.paint(Func(lambda P: np.abs((P - k.astype(F)) @ ax.astype(F) - F(0.15)) - F(0.012), k - 0.4, k + 0.4), CHAR)
    return fd


# ======================================================================================= painting
def warm_points():
    return []


# ======================================================================================= build config
GLB_NAME = "zero"
ROOT_NAME = "HeroZeroHQ"
TEX_PREFIX = "hero"
MAT_NAME = "ZeroMat"
MESH_NAME = "Zero"
BASE_MODULE = "zero_base"
ANIM_MODULE = "anim_zero"
PARTS = ["Skin", "Head", "Hull", "Arms", "Launcher", "Hand", "Legs", "Cloth", "Pupil",
         "Eye", "Spark", "Smile", "Mouth", "Core", "Flare", "Bore"]
REGION_PARTS = ("Skin", "Head", "Hull", "Arms", "Launcher", "Hand", "Legs", "Cloth", "Pupil")
MAT_KW = dict(suit=(0.12, 0.12, 0.14), graphite=(0.22, 0.23, 0.25), navy=(0.13, 0.13, 0.15), violet=(0.92, 0.55, 0.12),
              steel=(0.56, 0.58, 0.62), white=(0.88, 0.88, 0.85), orange=(0.95, 0.36, 0.07), yellow=(1.0, 0.64, 0.14),
              wear=1.4)
MAT_OVERRIDES = {nm: ("android", dict(MAT_KW, name="HQ_Zero" + nm)) for nm in REGION_PARTS}
GLOW = {"Eye": (AMBER_GLOW, 1.3, 0.55), "Mouth": (AMBER_GLOW, 1.2, 0.55), "Spark": ((1.0, 0.97, 0.9), 1.0, 0.95), "Smile": (AMBER_GLOW, 1.3, 0.55),
        "Core": (AMBER_GLOW, 1.3, 0.5), "Flare": (FLARE_GLOW, 1.5, 0.7), "Bore": (AMBER_GLOW, 1.3, 0.5)}
LOW_TARGETS = {"Skin": 2600, "Head": 2800, "Hull": 5000, "Arms": 4200, "Launcher": 2200, "Hand": 2000, "Legs": 4000,
               "Cloth": 900, "Pupil": 80, "Eye": 300, "Spark": 60, "Smile": 160, "Mouth": 120, "Core": 160, "Flare": 160, "Bore": 80}
AO_EXCLUDE = ["Cloth"]


def prop_bones():
    """The fingers' block (a child of the left hand, hinged across the knuckles); the barrel (a child of the right hand,
    from inside the jacket to the muzzle: scaled along its length it slides back, the recoil); the eye and the happy eye
    (children of the head, their heads at the eye's middle); the core's flare (a child of the chest)."""
    out = []
    h = finger_hinge("L")
    out.append(("fingers.L", h, h + gframe("L")[1] * 0.12, "hand.L"))
    a, b = barrel_bone()
    out.append(("barrel", a, b, "hand.R"))
    a, b = eye_bone()
    out.append(("eye", a, b, "head"))
    out.append(("smile", a, b, "head"))
    a, b = flare_bone()
    out.append(("flare", a, b, "chest"))
    return out


def weight_rules():
    return {
        "Head": ("rigid", "head"), "Pupil": ("rigid", "eye"), "Eye": ("rigid", "eye"), "Spark": ("rigid", "eye"),
        "Smile": ("rigid", "smile"), "Mouth": ("rigid", "head"), "Core": ("rigid", "chest"), "Flare": ("rigid", "flare"), "Bore": ("rigid", "barrel"),
        "Hull": ("custom", island_weights(hull_field)),
        "Arms": ("custom", island_weights(arms_field)),
        "Launcher": ("custom", island_weights(launcher_field)),
        "Hand": ("custom", island_weights(hand_field)),
        "Legs": ("custom", island_weights(legs_field)),
        "Cloth": ("rigid", "upperarm.L"),
    }


def uv_boost(c, part):
    if part == "Head":
        return 1.6 if c.y < HC[1] else 1.2
    if part == "Pupil":
        return 1.5
    if part == "Hull" and c.y < 0.0 and c.z > 1.2:
        return 1.25
    if part == "Skin":
        return 0.7
    if part == "Legs":
        return 0.85
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.0035 if fine else 0.005),
        ("Head", head_field(), 0.0022 if fine else 0.003),
        ("Hull", hull_field(), 0.0036 if fine else 0.0052),
        ("Arms", arms_field(), 0.0034 if fine else 0.005),
        ("Launcher", launcher_field(), 0.0026 if fine else 0.0038),
        ("Hand", hand_field(), 0.0026 if fine else 0.0038),
        ("Legs", legs_field(), 0.0036 if fine else 0.0052),
        ("Cloth", cloth_field(), 0.0024 if fine else 0.0034),
        ("Pupil", pupil_field(), 0.0012 if fine else 0.0016),
        ("Eye", eye_field(), 0.0016 if fine else 0.002),
        ("Spark", spark_field(), 0.001 if fine else 0.0013),
        ("Smile", smile_field(), 0.0016 if fine else 0.002),
        ("Mouth", mouth_field(), 0.0012 if fine else 0.0016),
        ("Core", core_field(), 0.002 if fine else 0.0026),
        ("Flare", flare_field(), 0.002 if fine else 0.0026),
        ("Bore", bore_field(), 0.0016 if fine else 0.002),
    ]
