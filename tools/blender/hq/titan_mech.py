"""The Titan Mech (HQ tower, The Data Center; Brute lineage, melee). Rest pose = an A-pose, facing -Y, feet at z = 0;
right side = -X.

A captured robot war machine turned against its makers: a hulking titan (about 2.5 m to the top of its head, 2.2 m
across its pauldrons), heavier than the Digital Age's Mech Brawler: short thick legs on broad feet, a squat pelvis on a
rubber-booted waist actuator, a huge armoured hull, enormous shoulders under domed pauldrons, long gorilla arms ending
in two huge armoured fists with welded steel knuckle bars. The robots' white armour plating (label 13 of the `android`
material) with their hazard-orange trim (14), graphite joints and plates (5), black panel lines (7); but clearly the
Resistance's now: big ember-amber slashes and chevrons spray-painted over the plates (16), charcoal patch plates (6)
welded over holes, dents, weld beads (10), teal-grey webbing straps (9).

The cockpit: a crude hatch torched into the front of its hull, open at the top, its edges ragged, framed by welded
gunmetal bars; the two halves of the cut-out plate re-hung on hinges at the opening's sides and folded back flat against
the hull either side of it, their charcoal inner faces sprayed with amber slashes (together a big amber V with the pilot
in it). A Resistance pilot rides in it, his head and shoulders showing: a grim, determined man (a square jaw dark with
stubble, a scar through his left brow, level brows drawn down at their inner ends, steady grey-blue eyes, a firm mouth),
in a dark leather flying cap with ear flaps and his goggles pushed up on its front, a charcoal jacket with teal-grey
shoulder pads, an amber scarf round his neck, black gloves on the two grips at the hatch's rim.

Above and behind him, on the hull's top, the robot's own small armoured head: its big red eye smashed (a few red shards
left in the socket) and an amber work lamp bolted into it (`GlowLamp`), a bent antenna with an amber rag tied to it,
the other snapped off. On its back the robot's power pack (an amber-lit core window, `GlowCore`), two exhaust stacks,
a jerrycan and coiled cable strapped on. The forearm housings' front rings glow amber (`GlowArmR`, `GlowArmL`); the
cockpit's dash screen and two lamps on the hatch frame too (`GlowChest`).

Machines don't bend: every mech part rides one bone (as the Mech Brawler's, mech_brawler.py). root = pelvis, spine =
the waist actuator, chest = the hull, cockpit and pilot; the rig's neck and head are the pilot's (he looks about); the
robot's head rides its own bone `mhead` (a child of the chest). Each fist rides its hand bone, its four fingers one
block on `fingers.R` / `fingers.L` (hinged across the knuckles). Armour, Frame and Fists are `MultiField`s: each piece
meshed on its own, each mesh island weighted 100% to the bone of the piece it came from."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from mech_brawler import MultiField, island_weights, seg_box, dent, smoothstep


class PaintedMulti(MultiField):
    """A MultiField whose painted labels may also be shape labels in other pieces (robot white is added on the
    pauldrons and painted on the hatch's halves): where a piece doesn't paint a label, its own shape labels decide
    (mech_brawler.MultiField leaves them unpainted, and the plates came out the material's dark under-suit)."""

    def paint_dist(self, P, band=0.004):
        P = np.asarray(P, dtype=F)
        own = self.owners(P)
        per = [f.paint_dist(P, band) for b, f in self.subs]
        labels = set()
        for d in per:
            labels |= set(d)
        out = {L: np.full(len(P), F(band)) for L in labels}
        for i, (b, f) in enumerate(self.subs):
            m = own == i
            if not m.any():
                continue
            lab = None
            for L in labels:
                if L in per[i]:
                    out[L][m] = per[i][L][m]
                else:
                    if lab is None:
                        lab = f.eval(P[m], labels=True)[1]
                    out[L][m] = np.where(lab == L, F(-band), F(band))
        return out

# ======================================================================================= labels
SKIN, NAIL, LIP, MOUTH, BROW, SCAR, SOOT, LASH, STUBBLE = 0, 1, 2, 3, 4, 6, 7, 8, 9
# android (the plates): 5 graphite, 6 charcoal (its `navy`), 7 panel lines, 8 amber cloth (its `violet`), 9 teal-grey
# webbing (its `tape`), 10 steel, 11 dark glass, 13 robot white, 14 hazard orange, 15 rubber, 16 amber paint (its `yellow`)
GRAPH, CHAR, PANEL, RAG, STRAP, STEEL, GLASS, WHITE, ORANGE, RUBBER, AMBER = 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16
# modern_kit (frame, cockpit, pilot, cap): 0 charcoal, 5 black, 6 robot red, 7 white, 8 teal-grey, 9 gunmetal, 10 steel,
# 11 glass, 12 rubber, 13 amber (its `coyote`), 14 brass
K_BASE, K_BLACK, K_RED, K_WHITE, K_TEAL, K_GUN, K_STEEL, K_GLASS, K_RUBBER, K_AMBER, K_BRASS = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14

CHARCOAL = (0.13, 0.13, 0.15)
GUNMETAL = (0.22, 0.23, 0.25)
TEAL = (0.2, 0.27, 0.28)
AMBER_PAINT = (0.98, 0.6, 0.13)
AMBER_GLOW = (1.0, 0.62, 0.15)
ROBOT_WHITE = (0.9, 0.9, 0.87)
HAZARD = (1.0, 0.45, 0.1)
IRIS = ((0.17, 0.23, 0.27), (0.36, 0.46, 0.5))          # steady grey-blue eyes (prep.paint_eyes)

# ======================================================================================= the skeleton (the mech's joints)
J = {"root": (0.0, 0.04, 1.08)}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.76, 0.08, 1.84)
    J["elbow_" + _s] = (_x * 0.94, 0.15, 1.34)
    J["wrist_" + _s] = (_x * 1.0, 0.05, 0.88)
    J["hip_" + _s] = (_x * 0.3, 0.05, 1.0)
    J["knee_" + _s] = (_x * 0.34, -0.06, 0.6)
    J["ankle_" + _s] = (_x * 0.36, 0.06, 0.24)
    J["toe_" + _s] = (_x * 0.37, -0.32, 0.07)
J = {k: v3(v) for k, v in J.items()}
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (1.0, 1.1, 1.3, 1.85)
CLAV_Z = 1.84

# ======================================================================================= the pilot's head space
# His head is designed in the same coordinates as the other heroes' (missile.py / mech_brawler.py: the head's centre at
# (0, 0.03, 1.73)) and placed in the cockpit by hp(): design -> world, scaled by PS.
PS = 0.86
D_HC = v3((0.0, 0.03, 1.73))
W_HC = v3((0.0, -0.1, 1.72))
HS = PS


def hp(p):
    return W_HC + (v3(p) - D_HC) * PS


def hr(r):
    return r * PS


def hinv(P):
    return (P - W_HC.astype(F)) / F(PS) + D_HC.astype(F)


HEAD_C = hp(D_HC)
HEAD_RAD = v3((0.18, 0.19, 0.186)) * PS
EYE_R = hr(0.036)


def eye_c(sx):
    return hp((sx * 0.07, -0.148, 1.674))


def torso_bones():
    return {
        "spine": ((0, 0.04, 1.08), (0, 0.04, 1.3)),
        "chest": ((0, 0.04, 1.3), (0, 0.06, 1.86)),
        "neck": (tuple(hp((0, 0.05, 1.27))), tuple(hp((0, 0.02, 1.5)))),
        "head": (tuple(hp((0, 0.02, 1.5))), tuple(hp((0, 0.0, 1.93)))),
        "clavicle_z": CLAV_Z,
    }


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


FU, FS = 1.4, 1.55           # the fist's scale (designed at 1.0 about the wrist, as the Mech Brawler's): along, across


def fp(side, u, v, w):
    return gp(side, u * FU, v * FS, w * FS)


def gR(side):
    """Rotation whose local x, y, z are the frame's W, M, A (a box's half sizes given as (v, w, u))."""
    wr, A, W, M = gframe(side)
    return np.stack([W, M, A], axis=1)


def hand_frame(side):
    wr, A, W, M = gframe(side)
    return wr, A, M, W


KN_U = 0.36                 # the knuckle bar's front (u, from the wrist, design): the knuckle point
KN_W = -0.012
HINGE_U, HINGE_W = 0.205, -0.02     # the fingers' hinge (across the knuckles)
FINGER_V = (0.117, 0.039, -0.039, -0.117)           # index (thumb side) .. little finger


def knuckle_point(side):
    return fp(side, KN_U, 0.0, KN_W)


def finger_hinge(side):
    return fp(side, HINGE_U, 0.0, HINGE_W)


H_FRONT = -0.035            # the forearm housing's front end (u, from the wrist)
HR0, HR1 = 0.165, 0.205     # its radius at the elbow end and at the front
TILT = 0.5


def h_rad(u):
    return F(HR0) + F(HR1 - HR0) * np.clip((u + F(0.38)) / F(0.34), 0, 1)


def h_back(v):
    return F(-0.4) + F(TILT) * v


# ======================================================================================= small helpers
def _stroke_sd(a, b, w, n, depth):
    """A flat band from a to b, `w` wide in the surface, `depth` deep along the normal n (crisp sides)."""
    a, b, n = a.astype(F), b.astype(F), n.astype(F)
    ab = b - a
    L2 = max(float(ab @ ab), 1e-12)

    def fn(P):
        t = np.clip(((P - a) @ ab) / F(L2), 0, 1)
        q = P - (a + t[:, None] * ab)
        dn = q @ n
        inplane = np.sqrt(np.maximum((q * q).sum(1) - dn * dn, 0))
        return np.maximum(inplane - F(w), np.abs(dn) - F(depth))
    return fn


def spray(fd, pts, w, nrm, label=AMBER, depth=0.05, rag=0.006):
    """Spray-paint a stroke along the polyline `pts` (w wide, through the surface along `nrm`), its edges ragged."""
    nrm = norm(v3(nrm))
    pts = [v3(p) for p in pts]
    for a, b in zip(pts[:-1], pts[1:]):
        fn = _stroke_sd(a, b, w, nrm, depth)
        pad = depth + w + rag + 0.01
        fd.paint(Func(lambda P, fn=fn: fn(P) + F(rag) * NOISE(P * F(55)), np.minimum(a, b) - pad, np.maximum(a, b) + pad), label)


def weld(fd, pts, r=0.011, label=STEEL):
    """A weld bead along a polyline: a row of overlapping lumps."""
    pts = [v3(p) for p in pts]
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(2, int(np.linalg.norm(b - a) / (r * 1.3)))
        for i in range(n + 1):
            fd.add(Sphere(lerp(a, b, i / n), r * (0.85 + 0.25 * ((i * 7919) % 5) / 4)), r * 0.6, label)


def dents(fd, spots):
    """Dents knocked into a plate: (centre on the surface, outward normal, radius)."""
    for c, n, r in spots:
        fd.sub(Sphere(v3(c) + norm(v3(n)) * (r * 0.78), r), r * 0.4)


def bolt_row(fd, pts, n, r=0.012, label=STEEL):
    n = norm(v3(n))
    for p in pts:
        fd.add(Cylinder(v3(p), r, 0.012, rr=0.004, R=rot_from_axes(z_axis=n)), 0.003, label)


def plate_frame(c, n, up):
    """A frame on a surface: c, right, up, normal (right = up x n)."""
    n = norm(v3(n))
    up = norm(v3(up) - n * (v3(up) @ n))
    r = np.cross(up, n)
    return v3(c), r, up, n


# ======================================================================================= the pilot: head
JAW = ((0.0, -0.058, 1.585), (0.148, 0.132, 0.127))
CHIN = ((0.0, -0.138, 1.5), (0.086, 0.068, 0.068))


def cheekbone(sx):
    return (sx * 0.104, -0.128, 1.642), 0.04


def jaw_corner(sx):
    return (sx * 0.126, -0.04, 1.552), 0.05


def stubble_mask(P):
    """Cheeks below the cheekbones, the jaw, chin and upper lip (design coordinates): a dark stubble."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.602) + F(0.01) * smoothstep(0.05, 0.12, ax) - F(0.012) * smoothstep(0.06, 0.0, ax) * smoothstep(-0.16, -0.2, y)
    lips = np.sqrt((x / F(0.058)) ** 2 + ((y + F(0.19)) / F(0.05)) ** 2 + ((z - F(1.551)) / F(0.015)) ** 2) - F(1.0)
    back = y - F(0.06) + F(0.04) * smoothstep(1.58, 1.5, z)
    # no stubble over the upper lip (a dark patch there reads as a little moustache at a distance)
    lip = np.sqrt((x / F(0.085)) ** 2 + ((y + F(0.2)) / F(0.07)) ** 2 + ((z - F(1.58)) / F(0.04)) ** 2) - F(1.0)
    return np.maximum(np.maximum(np.maximum(z - top, F(1.43) - z), back), np.maximum(-lips * F(0.02), -lip * F(0.02)))


BROW_D = [(0.022, -0.214, 1.741), (0.064, -0.21, 1.756), (0.108, -0.19, 1.765), (0.152, -0.148, 1.761)]


def brow_pts(sx):
    return [hp((sx * x, y, z)) for x, y, z in BROW_D]


def head(fd):
    """A grim, determined face (missile.py's square-jawed head): a square jaw and chin, cheekbones over flat cheeks, a
    straight nose, thick level brows drawn down a little at their inner ends, steady open eyes under them, a firm closed
    mouth, its corners level; a pale scar through his left brow (a gap in it) and on down his cheek. (No ears: the cap's flaps cover them.)"""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E(*JAW), hr(0.07), SKIN)
    fd.add(E(*CHIN), hr(0.05), SKIN)
    fd.add(E((0.0, -0.171, 1.49), (0.048, 0.026, 0.028)), hr(0.03), SKIN)                     # the chin's square point
    for sx in (-1, 1):
        c, r = cheekbone(sx)
        fd.add(S(c, r), hr(0.05), SKIN)
        c, r = jaw_corner(sx)
        fd.add(S(c, r), hr(0.05), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.114, -0.114, 1.582)), v3((0.022, 0.016, 0.024)) * HS, R=euler(0, 0, sx * -0.5)), hr(0.02))
        pts = [hp((sx * 0.154, -0.055, 1.744)), hp((sx * 0.116, -0.133, 1.754)), hp((sx * 0.061, -0.177, 1.75)), hp((0.0, -0.187, 1.746))]
        fd.add(Chain(pts, [hr(0.01), hr(0.017), hr(0.021), hr(0.019)], k=hr(0.02)), hr(0.026), SKIN)     # brow ridge
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # thick level brows, the inner ends drawn down a touch (determined, not scowling)
    tuft = lambda P: F(0.0018) * NOISE(P * F(150)) + F(0.0008) * np.sin(P[:, 0] * F(380) + P[:, 2] * F(80))
    for sx in (-1, 1):
        pts = brow_pts(sx)
        fd.add(Chain([p + v3((0, 0.005, 0)) for p in pts], [hr(0.012), hr(0.0145), hr(0.013), hr(0.007)], k=hr(0.008),
                     disp=tuft, disp_amp=0.0025), hr(0.008), BROW)
        fd.paint(Chain(pts, [hr(0.021), hr(0.024), hr(0.021), hr(0.013)], k=hr(0.01)), BROW)
    # eyes open and steady, the upper lids a little lower (a hard, level look)
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.021))), (sx * 0.1, 0.08, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.006)), Plane(ec + v3((0, 0, -hr(0.0205))), (sx * -0.08, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.019))), (sx * 0.1, 0.08, -1.0)), hr(0.002)), LASH)
        a = hp((sx * 0.112, -0.132, 1.684))
        fd.sub(RoundCone(a, a + v3((sx * 0.022, 0.012, 0.0)) * PS, hr(0.0018), hr(0.0012)), hr(0.003))           # a crease
    # a straight nose
    fd.add(RoundCone(hp((0, -0.19, 1.728)), hp((0, -0.238, 1.638)), hr(0.015), hr(0.02)), hr(0.016), SKIN)
    fd.add(S((0, -0.24, 1.618), 0.023), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.031, -0.222, 1.602), 0.02), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.016, -0.238, 1.592)), v3((0.009, 0.011, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # a firm closed mouth, its corners level
    slot = [hp(p) for p in ((-0.05, -0.176, 1.55), (-0.026, -0.197, 1.549), (0.0, -0.203, 1.549), (0.026, -0.197, 1.549), (0.05, -0.176, 1.55))]
    fd.sub(Chain(slot, [hr(0.002), hr(0.0026), hr(0.0028), hr(0.0026), hr(0.002)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0038), hr(0.004), hr(0.0038), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.046, -0.178, 1.555), (-0.022, -0.197, 1.558), (0.0, -0.202, 1.559), (0.022, -0.197, 1.558), (0.046, -0.178, 1.555)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0056), hr(0.006), hr(0.0056), hr(0.003)], k=hr(0.005)), hr(0.006), LIP)
    lo_lip = [(-0.044, -0.176, 1.542), (-0.022, -0.194, 1.534), (0, -0.199, 1.532), (0.022, -0.194, 1.534), (0.044, -0.176, 1.542)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0072), hr(0.008), hr(0.0072), hr(0.004)], k=hr(0.006)), hr(0.007), LIP)
    fd.add(RoundCone(hp((0.0, -0.215, 1.594)), hp((0.0, -0.205, 1.566)), hr(0.007), hr(0.006)), hr(0.008), SKIN)      # philtrum
    # the scar: through his left brow (a gap in it) and on down his cheek below the eye
    for k, (a, b) in enumerate((((0.09, -0.21, 1.8), (0.104, -0.196, 1.728)), ((0.112, -0.165, 1.648), (0.13, -0.135, 1.592)))):
        pa, pb = hp(a), hp(b)
        if k == 0:
            fd.sub(RoundCone(pa, pb, hr(0.0025)), hr(0.002))
        fd.paint(RoundCone(pa + v3((0, -0.01, 0)), pb + v3((0, -0.01, 0)), hr(0.0055)), SCAR)


def neck_prim():
    return RoundCone(hp((0, 0.045, 1.47)), hp((0, 0.07, 1.27)), hr(0.078), hr(0.088))


def skin_field():
    fd = Field("Skin")
    fd.add(neck_prim(), 0.0, SKIN)
    head(fd)
    return fd


def eyes_field():
    fd = Field("Eyes")
    for sx in (-1, 1):
        fd.add(Sphere(eye_c(sx), EYE_R))
    return fd


def skull():
    return Ellipsoid(HEAD_C, HEAD_RAD)


# ======================================================================================= the flying cap and goggles
CAP_OFF, CAP_T = 0.017, 0.018             # the cap's shell over the skull (world)
# its edge (design z): over his brow (EF), down over his ears at the sides (the ear flaps, ES), at the nape (EB)
EF, ES, EB = 1.795, 1.555, 1.6


def _phi(P):
    """Angle round the head's axis from straight ahead (0) to behind (+-pi), + toward his left."""
    return np.arctan2(P[:, 0], -(P[:, 1] - F(HEAD_C[1])))


def edge_d(P):
    ph = _phi(P)
    a = ((EF + EB) / 2 + ES) / 2
    c = ((EF + EB) / 2 - ES) / 2
    b = (EF - EB) / 2
    return F(a) + F(b) * np.cos(ph) + F(c) * np.cos(2 * ph)


def above_edge(P):
    return (hinv(P)[:, 2] - edge_d(P)) * F(PS)


def cap_outer():
    sk = skull()
    return Func(lambda P: sk(P) - F(CAP_OFF + CAP_T / 2), HEAD_C - 0.3, HEAD_C + 0.3)


def on_cap(phi, zd, off=0.0):
    """A point on the cap's outer surface at angle phi round the head and design height zd; its outward normal."""
    z = hp((0, 0, zd))[2]
    d = v3((math.sin(phi), -math.cos(phi), 0.0))
    o = v3((HEAD_C[0], HEAD_C[1], z)) + d * 0.5
    h, ok = ray_hit(cap_outer(), [o], [-d], tmax=0.5, step=0.0008)
    q = h[0]
    n = norm((q - HEAD_C) / ((HEAD_RAD + CAP_OFF + CAP_T / 2) ** 2))
    return q + n * off, n


GOG_PHI, GOG_Z = 0.36, 1.868              # the goggles' lens cups (round the head, design height), pushed up on the cap


def cap_field():
    """A dark leather flying cap (modern_kit 0, smooth): seams over the crown (black 5), ear flaps over his ears, a
    teal-grey fleece rim round its edge (8); the goggles pushed up on its front: a black rubber strap (12) round the cap,
    two lens cups (gunmetal 9, brass rims 14) with dark amber-sheened lenses (11), a bridge between them."""
    fd = Field("Cap")
    sk = skull()
    lo, hi = HEAD_C - 0.3, HEAD_C + 0.3
    wrinkle = lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.0008) * NOISE(P * F(90))
    fd.add(Inter(Shell(sk, CAP_OFF, CAP_T, pad=0.06, disp=wrinkle, disp_amp=0.002), Func(lambda P: -above_edge(P), lo, hi), 0.006), 0.0, K_BASE)
    # the fleece rim round its edge
    def rim(P):
        d = np.abs(above_edge(P) - F(0.008)) - F(0.009)
        return np.maximum(d, np.abs(sk(P) - F(CAP_OFF + 0.006)) - F(0.016))
    fd.add(Func(rim, lo, hi, disp=lambda P: F(0.002) * NOISE(P * F(120)), disp_amp=0.003), 0.004, K_TEAL)
    # seams: one over the crown, one round the side panels
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 0] - F(HEAD_C[0])) - F(0.0035), F(0.03) - above_edge(P)), lo, hi), K_BLACK)
    for sx in (-1, 1):
        fd.paint(Func(lambda P, sx=sx: np.maximum(np.abs(_phi(P) - F(sx * 1.05)) * F(0.15) - F(0.0035), F(0.02) - above_edge(P)), lo, hi), K_BLACK)
    # the goggle strap round the cap (sloping down to the back)
    def strap(P):
        ph = _phi(P)
        zc = F(GOG_Z) - F(0.06) * (np.abs(ph) / F(math.pi)) ** 1.3
        dz = np.abs(hinv(P)[:, 2] - zc) * F(PS) - F(0.011)
        return np.maximum(dz, np.abs(sk(P) - F(CAP_OFF + CAP_T / 2 + 0.003)) - F(0.006))
    fd.add(Func(strap, lo, hi), 0.002, K_RUBBER)
    # the lens cups, tilted up a little (they sit on his forehead), and the bridge
    cups = []
    for sx in (-1, 1):
        q, n = on_cap(sx * GOG_PHI, GOG_Z, 0.0)
        n2 = norm(n + v3((0, 0, 0.15)))
        R = rot_from_axes(z_axis=n2)
        fd.add(Cylinder(q + n2 * 0.012, hr(0.042), 0.03, rr=0.008, R=R), 0.004, K_GUN)
        fd.add(Torus(q + n2 * 0.027, hr(0.036), 0.0055, R=R), 0.002, K_BRASS)
        fd.add(Cylinder(q + n2 * 0.026, hr(0.033), 0.006, rr=0.002, R=R), 0.001, K_GLASS)
        cups.append(q + n2 * 0.014)
    fd.add(RoundCone(cups[0], cups[1], 0.008), 0.004, K_GUN)
    return fd


# ======================================================================================= the pilot's body (rigid with the hull)
P_SH = {"R": v3((-0.19, -0.02, 1.42)), "L": v3((0.19, -0.02, 1.42))}
P_EL = {"R": v3((-0.25, 0.02, 1.22)), "L": v3((0.25, 0.02, 1.22))}
GRIP = {"R": v3((-0.205, -0.33, 1.4)), "L": v3((0.205, -0.33, 1.4))}    # the grips at the hatch's rim (he holds them)


def scarf_ring():
    """The scarf's wrap round his neck (a tilted ring, lower at the front)."""
    return hp((0, 0.04, 1.44)), norm(v3((0, 0.32, 1.0)))


def pilot_field():
    """His jacket: charcoal (0) with teal-grey shoulder pads (8), a black harness (5), an amber armband on his left arm
    (13); the amber scarf (13) wrapped round his neck, knotted at his left, a tail down his chest; black gloves (5) on the
    grips."""
    fd = Field("Pilot")
    fold = lambda P: F(0.0014) * NOISE(P * F(22)) + F(0.0025) * NOISE(P * np.array([6, 6, 12], F))
    fd.add(Ellipsoid((0, 0.02, 1.27), (0.2, 0.13, 0.2), disp=fold, disp_amp=0.003), 0.0, K_BASE)          # torso
    fd.add(Ellipsoid((0, 0.0, 1.39), (0.225, 0.13, 0.09)), 0.06, K_BASE)                                  # shoulders
    fd.add(RoundCone(hp((0, 0.06, 1.3)), hp((0, 0.07, 1.45)), hr(0.11)), 0.03, K_BASE)                    # collar under the scarf
    for side, sx in (("R", -1), ("L", 1)):
        sh, el, gr = P_SH[side], P_EL[side], GRIP[side]
        fd.add(Ellipsoid(sh + v3((sx * 0.015, 0.0, 0.035)), (0.085, 0.09, 0.055)), 0.03, K_TEAL)          # shoulder pad
        fd.add(RoundCone(sh, el, 0.066, 0.058), 0.04, K_BASE)                                                # upper arm
        wr = gr + v3((sx * 0.01, 0.075, -0.01))
        fd.add(RoundCone(el, wr, 0.055, 0.046), 0.03, K_BASE)                                                # forearm
        fd.add(RoundCone(lerp(el, wr, 0.78), wr, 0.051, 0.048), 0.01, K_BLACK)                               # glove cuff
        fd.add(Ellipsoid(gr + v3((0, 0.012, 0.0)), (0.046, 0.052, 0.05)), 0.02, K_BLACK)                    # gloved fist
        for k in range(4):
            fd.add(Sphere(gr + v3((sx * -0.006, -0.032, 0.036 - 0.024 * k)), 0.018), 0.008, K_BLACK)
        # the harness strap over each shoulder
        fd.add(Chain([sh + v3((-sx * 0.06, -0.09, -0.02)), sh + v3((-sx * 0.07, -0.135, -0.12)), v3((sx * 0.07, -0.13, 1.18))],
                     [0.014, 0.014, 0.014], k=0.01), 0.006, K_BLACK)
    m, ax = lerp(P_SH["L"], P_EL["L"], 0.5), norm(P_EL["L"] - P_SH["L"])
    def band(P):
        q = P - m.astype(F)
        t = q @ ax.astype(F)
        rad = np.sqrt(np.maximum((q * q).sum(1) - t * t, 0))
        return np.maximum(np.abs(t) - F(0.022), rad - F(0.085))
    fd.paint(Func(band, m - 0.15, m + 0.15), K_AMBER)
    # the scarf: a thick wrap round his neck, a knot at his left, a tail down his chest
    c, ax = scarf_ring()
    R = rot_from_axes(z_axis=ax)
    lump = lambda P: F(0.005) * NOISE(P * F(26)) + F(0.003) * np.sin(P[:, 2] * F(160) + P[:, 0] * F(40))
    fd.add(Torus(c, hr(0.105), hr(0.04), R=R, disp=lump, disp_amp=0.006), 0.0, K_AMBER)
    fd.add(Torus(c + ax * hr(0.035) + v3((0, 0.0, 0.0)), hr(0.098), hr(0.033), R=R, disp=lump, disp_amp=0.006), 0.02, K_AMBER)
    knot = hp((0.075, -0.115, 1.43))
    fd.add(Ellipsoid(knot, (hr(0.04), hr(0.03), hr(0.036)), disp=lump, disp_amp=0.005), 0.02, K_AMBER)
    tail = [knot + v3((0, -0.01, -0.02)), knot + v3((0.02, -0.04, -0.09)), knot + v3((0.03, -0.05, -0.17)), knot + v3((0.045, -0.045, -0.24))]
    fd.add(Lock(tail, [0.045, 0.05, 0.052, 0.05], [0.014, 0.013, 0.012, 0.011], [v3((0, -1, 0.2))] * 4, k=0.01), 0.012, K_AMBER)
    return fd


# ======================================================================================= the hull and its cockpit
HULL_C = v3((0.0, 0.07, 1.64))
HULL_H = (0.56, 0.42, 0.3)
HULL_R = 0.17
FRONT_Y = HULL_C[1] - HULL_H[1]           # -0.35: the hull's flat front
CUT_X = 0.25                             # the hatch: x +-0.25, from CUT_Z0 up through the hull's top, back to CUT_Y1
CUT_Z0 = 1.34
CUT_Y1 = 0.2
CUT_C = v3((0.0, (FRONT_Y - 0.3 + CUT_Y1) / 2, CUT_Z0 + 0.45))
CUT_H = (CUT_X, (CUT_Y1 - FRONT_Y + 0.3) / 2, 0.45)
BAR_X = CUT_X + 0.026                    # the welded frame bars round the hatch
BAR_Y = FRONT_Y - 0.02
BAR_TOP = 1.92
DOOR_X = (0.29, 0.5)                     # the hatch's halves, folded back flat against the hull either side of it
DOOR_Z = (1.37, 1.86)
DOOR_T = 0.024
DOOR_Y = FRONT_Y - 0.012 - DOOR_T / 2


def torch(P):
    """Ragged torch-cut edges round the hatch's mouth (fading out inside it)."""
    k = smoothstep(FRONT_Y + 0.08, FRONT_Y + 0.0, P[:, 1])
    return (F(0.005) * NOISE(P * F(22)) + F(0.0025) * NOISE(P * F(70))) * (F(0.1) + F(0.9) * k)


DOOR_TURN = 0.2                          # each half turned back about its hinge, lying on the hull's rounded front


def door_frame(sx):
    """A hatch half's frame: centre, right (outward for both), up, normal (out of its painted inner face)."""
    hw = (DOOR_X[1] - DOOR_X[0]) / 2
    r = v3((sx * math.cos(DOOR_TURN), math.sin(DOOR_TURN), 0.0))
    u = v3((0, 0, 1))
    n = sx * np.cross(r, u)
    c = v3((sx * DOOR_X[0], DOOR_Y, (DOOR_Z[0] + DOOR_Z[1]) / 2)) + r * hw
    return c, r, u, n


def chest_shell(fd):
    """The hull: a huge armoured chest (robot white 13), the hatch torched into its front (open at the top, ragged
    edges, charcoal inside (6)), the hatch's two halves folded back flat against the hull either side of it (charcoal
    inner faces sprayed with amber slashes), a hazard-orange band round its lower edge (14), panel lines (7), dents, a
    charcoal patch plate welded over a hole on its right side, a welded crack on its left breast, amber slashes."""
    fd.add(RoundBox((0, 0.05, 1.33), (0.42, 0.32, 0.15), 0.1, disp=dent(0.0008, 22), disp_amp=0.001), 0.0, WHITE)  # belly
    fd.add(RoundBox(HULL_C, HULL_H, HULL_R, disp=dent(0.0008, 22), disp_amp=0.001), 0.1, WHITE)
    # a raised collar behind the hatch, round the head's neck
    fd.add(RoundBox((0, 0.3, 1.92), (0.3, 0.17, 0.06), 0.05), 0.06, WHITE)
    # a keel plate down the belly's front, under the hatch
    fd.add(RoundBox((0, FRONT_Y + 0.04, 1.22), (0.2, 0.05, 0.11), 0.04, R=euler(-0.25, 0, 0)), 0.03, GRAPH)
    # the hatch (torched: ragged edges)
    fd.sub(RoundBox(CUT_C, CUT_H, 0.07, disp=torch, disp_amp=0.009), 0.012)
    fd.paint(RoundBox((0, (FRONT_Y + 0.012 + CUT_Y1 + 0.05) / 2, CUT_Z0 + 0.5), (CUT_X + 0.015, (CUT_Y1 + 0.05 - FRONT_Y - 0.012) / 2, 0.5), 0.05), CHAR)
    # the hazard band round the lower hull, panel lines
    lo, hi = (-0.8, -0.6, 1.0), (0.8, 0.7, 2.2)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(1.235)) - F(0.03), lo, hi), ORANGE)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(1.49)) - F(0.0045), F(CUT_X + 0.03) - np.abs(P[:, 0])), lo, hi), PANEL)
    for sx in (-1, 1):
        fd.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 0] - F(sx * 0.42)) - F(0.0045), np.maximum(F(1.5) - P[:, 2], P[:, 1] - F(0.3))), lo, hi), PANEL)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 1] - F(0.16)) - F(0.0045), F(1.3) - P[:, 2]), lo, hi), PANEL)
    # the hatch's halves, folded back: hinges at the opening's sides
    for sx in (-1, 1):
        c, r, u, n = door_frame(sx)
        hw, hh = (DOOR_X[1] - DOOR_X[0]) / 2, (DOOR_Z[1] - DOOR_Z[0]) / 2
        Rd = np.stack([r, -n, u], 1)
        fd.add(RoundBox(c, (hw, DOOR_T / 2, hh), 0.012, R=Rd, disp=dent(0.0012, 18), disp_amp=0.0015), 0.008, CHAR)
        fd.paint(RoundBox(c - n * (DOOR_T * 0.45), (hw + 0.02, DOOR_T * 0.42, hh + 0.02), 0.0, R=Rd), WHITE)     # its outer (white) face
        # two amber slashes on each half: together the halves make a big double V round the pilot
        for k, dz in enumerate((0.12, -0.08)):
            a = c + r * (-hw + 0.02) + u * (dz - 0.11)
            b = c + r * (hw - 0.03) + u * (dz + 0.12)
            spray(fd, [a, b], 0.03 if k == 0 else 0.024, n, AMBER, depth=DOOR_T, rag=0.006)
        # its bolts round the edge, a pull bar
        bolt_row(fd, [c + r * (hw - 0.025) * s1 + u * (hh - 0.03) * s2 + n * (DOOR_T / 2) for s1 in (-1, 1) for s2 in (-1, 1)], n, 0.011, STEEL)
    # dents
    dents(fd, [((0.36, FRONT_Y, 1.28), (0, -1, 0), 0.05), ((-0.52, -0.1, 1.55), (-1, 0, 0), 0.06), ((0.55, 0.2, 1.7), (1, 0, 0), 0.045),
               ((-0.3, 0.1, 1.95), (0, 0, 1), 0.05), ((0.2, 0.47, 1.4), (0, 1, 0), 0.05), ((-0.22, FRONT_Y + 0.02, 1.25), (0, -1, 0), 0.04)])
    # a charcoal patch plate welded over a hole on its right side, bolts at its corners
    c, r, u, n = plate_frame((-0.62, 0.02, 1.58), (-1, 0, 0), (0, 0, 1))
    Rp = np.stack([r, u, n], 1) @ euler(0, 0, 0.12)
    fd.add(RoundBox(c + n * 0.008, (0.11, 0.09, 0.012), 0.008, R=Rp), 0.006, CHAR)
    bolt_row(fd, [c + Rp @ v3((s1 * 0.085, s2 * 0.065, 0.02)) for s1 in (-1, 1) for s2 in (-1, 1)], n, 0.012, STEEL)
    # a welded crack on its left breast
    weld(fd, [(0.36, FRONT_Y - 0.004, 1.8), (0.4, FRONT_Y - 0.004, 1.74), (0.37, FRONT_Y - 0.004, 1.67), (0.43, FRONT_Y + 0.0, 1.6)], 0.012, STEEL)
    # amber Resistance slashes: across the belly's front and down each side
    spray(fd, [(-0.36, FRONT_Y + 0.03, 1.16), (-0.08, FRONT_Y + 0.0, 1.31)], 0.035, (0, -1, 0), AMBER, depth=0.08)
    spray(fd, [(0.08, FRONT_Y + 0.0, 1.31), (0.36, FRONT_Y + 0.03, 1.16)], 0.035, (0, -1, 0), AMBER, depth=0.08)
    for sx in (-1, 1):
        spray(fd, [(sx * 0.62, -0.18, 1.42), (sx * 0.62, 0.22, 1.8)], 0.04, (sx, 0, 0), AMBER, depth=0.1)
        spray(fd, [(sx * 0.62, -0.06, 1.38), (sx * 0.62, 0.3, 1.72)], 0.025, (sx, 0, 0), AMBER, depth=0.1)
    # the robots' unit number on its back (black stencil bars), crossed out with an amber X
    for k in range(3):
        fd.paint(RoundBox((-0.12 + 0.12 * k, 0.5, 1.72), (0.03, 0.06, 0.07), 0.01), PANEL)
    spray(fd, [(-0.24, 0.5, 1.6), (0.24, 0.5, 1.84)], 0.03, (0, 1, 0), AMBER, depth=0.1)
    spray(fd, [(-0.24, 0.5, 1.84), (0.24, 0.5, 1.6)], 0.03, (0, 1, 0), AMBER, depth=0.1)


def pelvis_armour(fd):
    """A broad hip ring (white), a front plate (white, a hazard-orange chevron, an amber slash), side plates."""
    fd.add(RoundBox((0, 0.05, 1.07), (0.36, 0.25, 0.07), 0.055), 0.0, WHITE)
    fd.add(RoundBox((0, -0.19, 0.97), (0.17, 0.04, 0.11), 0.04, R=euler(-0.18, 0, 0)), 0.012, WHITE)
    fd.add(RoundBox((0, 0.29, 0.99), (0.19, 0.035, 0.09), 0.03, R=euler(0.18, 0, 0)), 0.012, GRAPH)
    fd.paint(Func(lambda P: np.maximum(np.abs(np.abs(P[:, 0]) * F(0.8) - (P[:, 2] - F(0.9)) * F(1.0)) - F(0.02), P[:, 1] + F(0.12)),
                  (-0.3, -0.4, 0.8), (0.3, 0.0, 1.2)), ORANGE)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(1.07)) - F(0.012), (-0.5, -0.4, 1.0), (0.5, 0.4, 1.15)), PANEL)


def pauldron(fd, side):
    """A huge domed pauldron over the shoulder (white), its flared rim banded in hazard orange, a big amber chevron
    sprayed over its crown, dents, a weld bead along a crack, a charcoal patch."""
    sx = -1 if side == "R" else 1
    sh = J["shoulder_" + side]
    c = sh + v3((sx * 0.08, 0.0, 0.1))
    R = euler(0, sx * 0.34, 0)
    fd.add(RoundBox(c, (0.25, 0.28, 0.14), 0.13, R=R, disp=dent(0.0008, 20), disp_amp=0.001), 0.0, WHITE)
    fd.add(RoundBox(c + R @ v3((sx * 0.02, 0, -0.085)), (0.27, 0.3, 0.045), 0.04, R=R), 0.03, WHITE)
    fd.sub(RoundBox(c + R @ v3((0, 0, -0.18)), (0.22, 0.25, 0.11), 0.07, R=R), 0.02)
    fd.paint(RoundBox(c + R @ v3((0, 0, -0.088)), (0.5, 0.5, 0.034), 0.0, R=R), ORANGE)
    fd.paint(RoundBox(c + R @ v3((0, 0, -0.04)), (0.5, 0.5, 0.004), 0.0, R=R), PANEL)
    # the amber chevron over its crown, pointing outward
    top = c + R @ v3((0, 0, 0.14))
    n = R @ v3((0, 0, 1))
    xo = R @ v3((sx, 0, 0))
    yo = v3((0, 1, 0))
    for k, o in enumerate((-0.06, 0.07)):
        a = top + xo * (o - 0.07) + yo * 0.2
        m = top + xo * (o + 0.09)
        b = top + xo * (o - 0.07) - yo * 0.2
        spray(fd, [a, m, b], 0.034 if k == 0 else 0.026, n, AMBER, depth=0.12)
    dents(fd, [(c + R @ v3((sx * 0.12, -0.2, 0.12)), R @ v3((0, -0.3, 1)), 0.05), (c + R @ v3((sx * -0.08, 0.22, 0.13)), R @ v3((0, 0.3, 1)), 0.04)])
    weld(fd, [c + R @ v3((sx * 0.05, -0.29, 0.06)), c + R @ v3((sx * 0.09, -0.29, -0.02)), c + R @ v3((sx * 0.06, -0.3, -0.06))], 0.011, STEEL)


def upperarm_armour(fd, side):
    sx = -1 if side == "R" else 1
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    a, b = lerp(sh, el, 0.3), lerp(sh, el, 0.82)
    fd.add(seg_box(a + v3((sx * 0.03, 0, 0)), b + v3((sx * 0.025, 0, 0)), (0.12, 0.13), 0.06, side_ref=(1, 0, 0)), 0.0, WHITE)
    fd.paint(seg_box(lerp(a, b, 0.5), lerp(a, b, 0.5) + norm(b - a) * 0.01, (0.3, 0.3), 0.0), PANEL)
    mid = lerp(a, b, 0.7) + v3((sx * 0.15, 0, 0))
    spray(fd, [mid + v3((0, -0.12, 0.06)), mid + v3((0, 0.12, -0.06))], 0.03, (sx, 0, 0), AMBER, depth=0.08)


STRIP_U = (-0.3, -0.11)     # the forearm's amber strap band (u range)


def forearm_armour(fd, side):
    """The forearm housing (white): a tapered tube cut on a slant at the elbow, a graphite flange at its front with a
    hazard-orange band behind it, a teal-grey webbing strap wound round it (9), an amber slash, an elbow guard
    (graphite)."""
    wr, A, W, M = gframe(side)
    c = gp(side, -0.2, 0, 0)

    def tube(P, side=side):
        u, v, w = _uvw(P, side)
        rad = np.sqrt(v * v + w * w)
        dr = rad - h_rad(u)
        du = np.maximum(h_back(v) - u, u - F(H_FRONT))
        rr = F(0.035)
        qx, qy = dr + rr, du + rr
        return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - rr
    fd.add(Func(tube, c - 0.42, c + 0.42, disp=dent(0.0008, 24), disp_amp=0.001), 0.0, WHITE)

    def flange(P, side=side):
        u, v, w = _uvw(P, side)
        return np.maximum(np.abs(u - F(H_FRONT - 0.035)) - F(0.026), np.sqrt(v * v + w * w) - (h_rad(u) + F(0.018)))
    fd.add(Func(flange, c - 0.42, c + 0.42), 0.008, GRAPH)
    lo, hi = c - 0.42, c + 0.42
    fd.paint(Func(lambda P, side=side: np.abs(_uvw(P, side)[0] - F(H_FRONT - 0.1)) - F(0.025), lo, hi), ORANGE)
    # the webbing strap, wound round it twice
    def strap(P, side=side):
        u, v, w = _uvw(P, side)
        rad = np.sqrt(v * v + w * w)
        ang = np.arctan2(w, v)
        uc = F(-0.26) + F(0.03) * np.sin(ang)
        return np.maximum(np.abs(u - uc) - F(0.028), np.abs(rad - h_rad(u) - F(0.004)) - F(0.008))
    fd.add(Func(strap, lo, hi), 0.004, STRAP)
    e = gdir(side, 100)
    spray(fd, [gp(side, -0.2, 0, 0) + e * 0.19 + A * 0.06 - W * 0.06, gp(side, -0.2, 0, 0) + e * 0.19 - A * 0.06 + W * 0.06], 0.026, e, AMBER, depth=0.06)
    # the elbow guard
    eg = gp(side, -0.43, 0, 0) + gdir(side, 150) * 0.07
    fd.add(Ellipsoid(eg, (0.135, 0.115, 0.1), R=gR(side)), 0.03, GRAPH)
    fd.paint(Func(lambda P, side=side: np.abs(_uvw(P, side)[0] + F(0.18)) - F(0.0045), lo, hi), PANEL)


def thigh_armour(fd, side):
    sx = -1 if side == "R" else 1
    hp_, kn = J["hip_" + side], J["knee_" + side]
    a, b = lerp(hp_, kn, 0.15), lerp(hp_, kn, 0.82)
    off = v3((sx * 0.035, -0.05, 0))
    fd.add(seg_box(a + off, b + off, (0.16, 0.115), 0.065, side_ref=(1, 0, 0)), 0.0, WHITE)
    fd.add(seg_box(a + v3((sx * 0.115, 0.0, 0.02)), lerp(a, b, 0.55) + v3((sx * 0.125, 0.0, 0)), (0.045, 0.13), 0.03, side_ref=(1, 0, 0)), 0.02, GRAPH)
    fd.paint(seg_box(lerp(a, b, 0.55) + off, lerp(a, b, 0.55) + off + norm(b - a) * 0.01, (0.3, 0.3), 0.0), PANEL)
    fd.paint(seg_box(lerp(a, b, 0.25) + off, lerp(a, b, 0.25) + off + norm(b - a) * 0.05, (0.3, 0.3), 0.0), ORANGE)


def shin_armour(fd, side):
    """A knee cap (graphite) and a big shin guard (white, hazard-orange stripes, an amber slash, a dent)."""
    sx = -1 if side == "R" else 1
    kn, an = J["knee_" + side], J["ankle_" + side]
    fd.add(Ellipsoid(kn + v3((0, -0.12, 0.025)), (0.13, 0.085, 0.12)), 0.0, GRAPH)
    a, b = lerp(kn, an, 0.18), lerp(kn, an, 0.9)
    fd.add(seg_box(a + v3((0, -0.03, 0)), b + v3((0, -0.01, 0)), (0.18, 0.165), 0.075, side_ref=(1, 0, 0)), 0.02, WHITE)
    fd.add(seg_box(lerp(a, b, 0.1) + v3((0, -0.155, 0)), lerp(a, b, 0.85) + v3((0, -0.135, 0)), (0.11, 0.04), 0.03, side_ref=(1, 0, 0)), 0.02, WHITE)
    for k in range(3):
        fd.paint(seg_box(lerp(a, b, 0.62 + 0.09 * k) + v3((sx * 0.17, -0.06, 0)), lerp(a, b, 0.62 + 0.09 * k) + v3((sx * 0.17, -0.06, 0.03)),
                         (0.05, 0.2), 0.0, side_ref=(1, 0, 0)), ORANGE)
    m = lerp(a, b, 0.42) + v3((0, -0.2, 0))
    spray(fd, [m + v3((-0.09, 0, -0.08)), m + v3((0.09, 0, 0.1))], 0.028, (0, -1, 0), AMBER, depth=0.08)
    dents(fd, [(lerp(a, b, 0.7) + v3((sx * -0.06, -0.19, 0)), (0, -1, 0), 0.04)])


def foot_armour(fd, side):
    """A broad armoured foot (graphite): a wedge with a toe cap (hazard chevrons on its nose), a heel block."""
    an = J["ankle_" + side]
    fd.add(RoundBox(an + v3((0, -0.08, -0.15)), (0.18, 0.29, 0.07), 0.05), 0.0, GRAPH)
    fd.add(RoundBox(an + v3((0, -0.23, -0.15)), (0.17, 0.14, 0.06), 0.05, R=euler(0.12, 0, 0)), 0.02, GRAPH)
    fd.add(RoundBox(an + v3((0, -0.07, -0.085)), (0.13, 0.17, 0.055), 0.045, R=euler(0.25, 0, 0)), 0.03, WHITE)
    fd.add(RoundBox(an + v3((0, 0.17, -0.15)), (0.14, 0.07, 0.065), 0.04), 0.02, GRAPH)
    toe = an + v3((0, -0.36, -0.15))
    for k in range(4):
        d = 0.034 * k
        fd.paint(Func(lambda P, d=d, toe=toe: np.maximum(np.abs(np.abs(P[:, 0] - F(toe[0])) * F(0.7) + (P[:, 1] - F(toe[1])) * F(-1.0) - F(d) - F(0.02)) - F(0.0085),
                                                        np.maximum(P[:, 1] - F(toe[1] + 0.08), np.abs(P[:, 2] - F(toe[2])) - F(0.09))),
                      toe - 0.28, toe + 0.28), ORANGE if k % 2 == 0 else PANEL)


# ======================================================================================= the robot's head (on `mhead`)
MHEAD_C = v3((0.0, 0.26, 2.12))
EYE_M = MHEAD_C + v3((0.0, -0.165, 0.0))         # the smashed eye's socket (front of the face)
EYE_MR = 0.058


def mhead_armour(fd):
    """The robot's head: a squat armoured helmet (white), a jutting brow, a hazard-orange stripe over its crown, graphite
    cheek guards and jaw, the big round eye socket in its face (the eye smashed: the lamp is bolted in, Frame), ear pods
    with orange rings, a dent."""
    c = MHEAD_C
    fd.add(RoundBox(c, (0.16, 0.15, 0.11), 0.075, disp=dent(0.0008, 24), disp_amp=0.001), 0.0, WHITE)
    fd.add(RoundBox(c + v3((0, -0.03, 0.075)), (0.17, 0.13, 0.04), 0.035), 0.03, WHITE)
    fd.add(RoundBox(c + v3((0, -0.14, 0.065)), (0.175, 0.035, 0.028), 0.022, R=euler(-0.35, 0, 0)), 0.015, WHITE)    # the brow
    fd.paint(RoundBox(c + v3((0, 0.0, 0.12)), (0.032, 0.3, 0.1), 0.0), ORANGE)
    fd.add(RoundBox(c + v3((0, -0.1, -0.08)), (0.13, 0.065, 0.045), 0.03), 0.02, GRAPH)                                # jaw
    for sx in (-1, 1):
        fd.add(RoundBox(c + v3((sx * 0.12, -0.11, -0.015)), (0.035, 0.05, 0.06), 0.025), 0.015, GRAPH)                  # cheek guards
        pc = c + v3((sx * 0.175, 0.01, 0.0))
        fd.add(Cylinder(pc, 0.06, 0.05, rr=0.015, R=rot_from_axes(z_axis=(1, 0, 0))), 0.01, GRAPH)
        fd.paint(Torus(pc + v3((sx * 0.024, 0, 0)), 0.045, 0.008, R=rot_from_axes(z_axis=(1, 0, 0))), ORANGE)
    # the eye socket
    fd.sub(Cylinder(EYE_M, EYE_MR + 0.006, 0.09, rr=0.01, R=rot_from_axes(z_axis=(0, 1, 0))), 0.008)
    fd.paint(Cylinder(EYE_M + v3((0, 0.02, 0)), EYE_MR + 0.02, 0.07, rr=0.0, R=rot_from_axes(z_axis=(0, 1, 0))), GRAPH)
    fd.paint(RoundBox(c + v3((0, -0.16, 0.035)), (0.2, 0.05, 0.004), 0.0), PANEL)
    dents(fd, [(c + v3((-0.09, -0.06, 0.12)), (0, -0.3, 1), 0.035)])


# ======================================================================================= armour (all its plates)
def armour_field():
    subs = [("root", Field("ArmourPelvis")), ("chest", Field("ArmourHull")), ("mhead", Field("ArmourHead"))]
    pelvis_armour(subs[0][1])
    chest_shell(subs[1][1])
    mhead_armour(subs[2][1])
    for side in ("R", "L"):
        f = Field("ArmourUpper" + side)
        pauldron(f, side)
        upperarm_armour(f, side)
        subs.append(("upperarm." + side, f))
        f = Field("ArmourFore" + side)
        forearm_armour(f, side)
        subs.append(("forearm." + side, f))
        f = Field("ArmourThigh" + side)
        thigh_armour(f, side)
        subs.append(("thigh." + side, f))
        f = Field("ArmourShin" + side)
        shin_armour(f, side)
        subs.append(("shin." + side, f))
        f = Field("ArmourFoot" + side)
        foot_armour(f, side)
        subs.append(("foot." + side, f))
    return PaintedMulti("Armour", subs)


# ======================================================================================= the frame, salvage and the head's lamp
PACK_C = v3((0.0, 0.56, 1.58))


def back_pack(f):
    """The robot's power pack on its back (gunmetal 9): cooling fins, the core's window (glows: GlowCore), two exhaust
    stacks rising behind its shoulders; strapped on: a teal-grey jerrycan (8, black straps 5), a coil of black cable
    (12); hazard stripes (13 amber? no: the robots' orange is on the plates), a white stencil."""
    f.add(RoundBox(PACK_C, (0.36, 0.12, 0.27), 0.06), 0.0, K_GUN)
    for k in range(8):
        x = -0.245 + 0.07 * k
        if abs(x) < 0.09:
            continue
        f.add(RoundBox((x, PACK_C[1] + 0.12, PACK_C[2] + 0.02), (0.012, 0.035, 0.2), 0.007), 0.004, K_GUN)
    f.add(RoundBox((0, PACK_C[1] + 0.115, PACK_C[2] + 0.02), (0.075, 0.03, 0.13), 0.025), 0.01, K_BLACK)      # the core's window frame
    f.sub(RoundBox((0, PACK_C[1] + 0.15, PACK_C[2] + 0.02), (0.055, 0.03, 0.11), 0.02), 0.006)
    for sx in (-1, 1):
        base = v3((sx * 0.27, PACK_C[1] + 0.02, PACK_C[2] + 0.2))
        f.add(Cylinder(base + v3((0, 0, 0.12)), 0.055, 0.32, rr=0.015), 0.01, K_GUN)
        f.add(Cylinder(base + v3((0, 0, 0.29)), 0.065, 0.05, rr=0.012), 0.006, K_BLACK)
        f.sub(Cylinder(base + v3((0, 0, 0.32)), 0.042, 0.08, rr=0.005), 0.004)
        for z in (0.06, 0.16):
            f.add(Torus(base + v3((0, 0, z)), 0.057, 0.008), 0.003, K_STEEL)
    # the jerrycan, strapped on its back's left
    jc = v3((0.25, PACK_C[1] + 0.2, PACK_C[2] - 0.08))
    f.add(RoundBox(jc, (0.09, 0.06, 0.15), 0.02), 0.0, K_TEAL)
    f.add(RoundBox(jc + v3((0, 0, 0.17)), (0.07, 0.03, 0.02), 0.01), 0.006, K_TEAL)
    f.sub(RoundBox(jc + v3((0, 0, 0.17)), (0.05, 0.05, 0.012), 0.005), 0.003)
    f.add(Cylinder(jc + v3((-0.05, 0, 0.17)), 0.02, 0.04, rr=0.005), 0.004, K_BLACK)
    for dz in (-0.06, 0.06):
        f.add(RoundBox(jc + v3((0, -0.01, dz)), (0.105, 0.075, 0.014), 0.008), 0.004, K_BLACK)
    f.paint(Func(lambda P: np.maximum(np.abs(np.abs(P[:, 0] - F(jc[0])) - (P[:, 2] - F(jc[2])) * F(0.6)) - F(0.012), np.abs(P[:, 2] - F(jc[2])) - F(0.12)),
                 jc - 0.2, jc + 0.2), K_BLACK)
    # a coil of cable hung on its back's right
    cc = v3((-0.24, PACK_C[1] + 0.16, PACK_C[2] - 0.12))
    for k in range(3):
        f.add(Torus(cc + v3((0.0, 0.012 * k, 0.0)), 0.085 - 0.004 * k, 0.017, R=rot_from_axes(z_axis=(0.15, 1, 0.1))), 0.006, K_RUBBER)
    f.add(RoundBox(cc + v3((0, -0.01, 0.08)), (0.03, 0.04, 0.03), 0.01), 0.006, K_BLACK)
    f.paint(RoundBox(PACK_C + v3((0, 0.12, 0.22)), (0.2, 0.05, 0.015), 0.004), K_WHITE)
    # a strap round the hull's middle holding it on (teal webbing)
    def belt(P):
        q = P - np.array([0.0, 0.07, 0.0], F)
        bx, by = F(0.58), F(0.44)
        d2 = np.sqrt(np.maximum(np.abs(q[:, 0]) - bx + F(0.17), 0) ** 2 + np.maximum(np.abs(q[:, 1]) - by + F(0.17), 0) ** 2) - F(0.17)
        return np.maximum(np.maximum(np.abs(d2) - F(0.012), np.abs(P[:, 2] - F(1.44)) - F(0.03)), F(-0.1) - q[:, 1])
    f.add(Func(belt, (-0.75, -0.2, 1.38), (0.75, 0.75, 1.5)), 0.004, K_TEAL)


def head_kit(f):
    """On the robot's head: the socket's gunmetal ring with red shards of the smashed eye still in it (6), the amber work
    lamp bolted into it (gunmetal housing, a steel cage, black clamp; its lens glows: GlowLamp), a bent antenna with an
    amber rag tied to it (13), the other antenna snapped off, a cable from the lamp down the head's back."""
    ax = v3((0, -1, 0))
    R = rot_from_axes(z_axis=ax)
    f.add(Torus(EYE_M + ax * 0.005, EYE_MR + 0.004, 0.012, R=R), 0.0, K_GUN)
    rs = np.random.RandomState(5)
    for k in range(7):
        a = 2 * math.pi * k / 7 + rs.uniform(-0.3, 0.3)
        e = v3((math.cos(a), 0.0, math.sin(a)))
        L = rs.uniform(0.012, 0.022)
        p = EYE_M + e * (EYE_MR - L * 0.6) + ax * 0.0
        f.add(RoundBox(p, (0.012, 0.004, L), 0.002, R=rot_from_axes(z_axis=e, y_axis=ax) @ euler(0, 0, rs.uniform(-0.4, 0.4))), 0.002, K_RED)
    # the lamp
    f.add(Cylinder(EYE_M + ax * 0.02, 0.043, 0.07, rr=0.01, R=R), 0.006, K_GUN)
    f.add(Torus(EYE_M + ax * 0.055, 0.04, 0.008, R=R), 0.003, K_GUN)
    for k in range(3):
        a = math.pi * k / 3
        e = v3((math.cos(a), 0.0, math.sin(a)))
        f.add(RoundCone(EYE_M + ax * 0.062 + e * 0.04, EYE_M + ax * 0.062 - e * 0.04, 0.004), 0.002, K_STEEL)
    f.add(Torus(EYE_M + ax * 0.0, 0.05, 0.007, R=R), 0.003, K_BLACK)
    for sx in (-1, 1):
        f.add(Cylinder(EYE_M + v3((sx * 0.062, 0.002, 0.0)), 0.009, 0.014, rr=0.003, R=R), 0.002, K_STEEL)
    # the cable from the lamp, round the head's side and down its back
    c = MHEAD_C
    pts = [EYE_M + v3((0.05, 0.02, -0.03)), c + v3((0.15, -0.07, -0.08)), c + v3((0.16, 0.08, -0.1)), c + v3((0.1, 0.17, -0.13)), c + v3((0.05, 0.16, -0.2))]
    f.add(Chain(pts, [0.011] * len(pts), k=0.01), 0.004, K_RUBBER)
    # the antennae: the left bent, a rag tied on it; the right snapped off
    base = c + v3((0.12, 0.07, 0.13))
    ant = [base, base + v3((0.01, 0.0, 0.12)), base + v3((0.03, 0.01, 0.2)), base + v3((0.1, 0.03, 0.26))]
    f.add(Cylinder(base, 0.02, 0.03, rr=0.006), 0.004, K_GUN)
    f.add(Chain(ant, [0.009, 0.008, 0.007, 0.006], k=0.006), 0.003, K_STEEL)
    knot = base + v3((0.02, 0.005, 0.17))
    f.add(Ellipsoid(knot, (0.022, 0.018, 0.018)), 0.006, K_AMBER)
    for k, (d, L) in enumerate(((v3((0.0, 0.9, -0.3)), 0.11), (v3((0.25, 0.8, -0.45)), 0.09))):
        d = norm(d)
        pts = [knot, knot + d * L * 0.5 + v3((0, 0, -0.01)), knot + d * L]
        f.add(Lock(pts, [0.03, 0.028, 0.024], [0.006, 0.005, 0.004], [v3((1, 0, 0))] * 3, k=0.006), 0.006, K_AMBER)
    b2 = c + v3((-0.12, 0.07, 0.13))
    f.add(Cylinder(b2, 0.02, 0.03, rr=0.006), 0.004, K_GUN)
    f.add(RoundCone(b2, b2 + v3((-0.01, 0.0, 0.055)), 0.009, 0.008), 0.003, K_STEEL)


def frame_field():
    subs = []
    f = Field("FramePelvis")
    f.add(RoundBox((0, 0.05, 0.99), (0.23, 0.17, 0.11), 0.05), 0.0, K_GUN)
    for sx in (-1, 1):
        h = J["hip_R" if sx < 0 else "hip_L"]
        f.add(Sphere(h, 0.11), 0.02, K_GUN)
        f.add(Cylinder(h + v3((sx * 0.02, 0, 0)), 0.095, 0.14, rr=0.02, R=rot_from_axes(z_axis=(1, 0, 0))), 0.01, K_BLACK)
    subs.append(("root", f))
    f = Field("FrameWaist")
    f.add(Cylinder((0, 0.05, 1.18), 0.17, 0.17, rr=0.02), 0.0, K_RUBBER)
    for z in (1.125, 1.17, 1.215):
        f.add(Torus((0, 0.05, z), 0.172, 0.02), 0.008, K_RUBBER)
    subs.append(("spine", f))
    f = Field("FrameHull")
    back_pack(f)
    f.add(Cylinder((0, 0.26, 1.98), 0.085, 0.12, rr=0.02), 0.0, K_RUBBER)          # the head's neck (a rubber boot)
    for z in (1.95, 1.99):
        f.add(Torus((0, 0.26, z), 0.086, 0.012), 0.005, K_RUBBER)
    subs.append(("chest", f))
    f = Field("FrameHead")
    head_kit(f)
    subs.append(("mhead", f))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        f = Field("FrameShoulder" + side)
        f.add(Cylinder(sh + v3((-sx * 0.08, 0, 0)), 0.15, 0.18, rr=0.04, R=rot_from_axes(z_axis=(1, 0, 0))), 0.0, K_GUN)
        f.add(Torus(sh, 0.125, 0.022, R=rot_from_axes(z_axis=(1, 0, 0))), 0.005, K_BLACK)
        subs.append(("clavicle." + side, f))
        f = Field("FrameUpper" + side)
        f.add(Sphere(sh, 0.13), 0.0, K_GUN)
        f.add(RoundCone(sh, el, 0.085, 0.08), 0.02, K_GUN)
        hz = norm(np.cross(norm(el - sh), norm(wr - el)))
        f.add(Cylinder(el, 0.115, 0.19, rr=0.035, R=rot_from_axes(z_axis=hz)), 0.01, K_GUN)
        f.add(Cylinder(el, 0.075, 0.225, rr=0.015, R=rot_from_axes(z_axis=hz)), 0.004, K_BLACK)
        back = norm(v3((0, 1, 0)) - norm(el - sh) * (v3((0, 1, 0)) @ norm(el - sh)))
        p0, p1 = lerp(sh, el, 0.15) + back * 0.1, lerp(sh, el, 0.85) + back * 0.095
        f.add(RoundCone(p0, lerp(p0, p1, 0.55), 0.032), 0.006, K_BLACK)
        f.add(RoundCone(lerp(p0, p1, 0.5), p1, 0.016), 0.004, K_STEEL)
        # a cable strapped down the upper arm's outside (salvage wiring)
        out = v3((sx, 0, 0))
        cpts = [lerp(sh, el, 0.2) + out * 0.13 + v3((0, -0.03, 0)), lerp(sh, el, 0.5) + out * 0.15 + v3((0, -0.06, 0)), lerp(sh, el, 0.9) + out * 0.11 + v3((0, -0.06, 0))]
        f.add(Chain(cpts, [0.016] * 3, k=0.01), 0.006, K_RUBBER)
        subs.append(("upperarm." + side, f))
        f = Field("FrameFore" + side)
        f.add(RoundCone(gp(side, -0.47, 0, 0), gp(side, -0.28, 0, 0), 0.08), 0.0, K_GUN)
        subs.append(("forearm." + side, f))
        hp_, kn, an = (J[k + "_" + side] for k in ("hip", "knee", "ankle"))
        f = Field("FrameThigh" + side)
        f.add(RoundCone(hp_, kn, 0.095, 0.09), 0.0, K_GUN)
        f.add(Cylinder(kn, 0.11, 0.22, rr=0.03, R=rot_from_axes(z_axis=(1, 0, 0))), 0.01, K_GUN)
        f.add(Cylinder(kn, 0.065, 0.255, rr=0.015, R=rot_from_axes(z_axis=(1, 0, 0))), 0.004, K_BLACK)
        p0, p1 = lerp(hp_, kn, 0.2) + v3((0, 0.095, 0)), lerp(hp_, kn, 0.85) + v3((0, 0.1, 0))
        f.add(RoundCone(p0, lerp(p0, p1, 0.55), 0.034), 0.006, K_BLACK)
        f.add(RoundCone(lerp(p0, p1, 0.5), p1, 0.017), 0.004, K_STEEL)
        subs.append(("thigh." + side, f))
        f = Field("FrameShin" + side)
        f.add(RoundCone(kn, an, 0.085, 0.08), 0.0, K_GUN)
        f.add(Sphere(an, 0.095), 0.01, K_GUN)
        p0, p1 = lerp(kn, an, 0.15) + v3((0, 0.12, 0)), lerp(kn, an, 0.85) + v3((0, 0.11, 0))
        f.add(RoundCone(p0, lerp(p0, p1, 0.55), 0.034), 0.006, K_BLACK)
        f.add(RoundCone(lerp(p0, p1, 0.5), p1, 0.017), 0.004, K_STEEL)
        subs.append(("shin." + side, f))
        f = Field("FrameFoot" + side)
        f.add(RoundBox(an + v3((0, -0.07, -0.215)), (0.185, 0.3, 0.025), 0.016), 0.0, K_RUBBER)     # the sole (bottom at z = 0)
        f.add(Cylinder(an, 0.08, 0.27, rr=0.02, R=rot_from_axes(z_axis=(1, 0, 0))), 0.0, K_BLACK)
        subs.append(("foot." + side, f))
    return PaintedMulti("Frame", subs)


# ======================================================================================= the cockpit (rigid with the hull)
def cockpit_field():
    """The seat (black (5), quilted) and its headrest at the hatch's back wall, cables and a pipe on the walls; the welded
    frame bars round the hatch (gunmetal 9, weld beads 10, steel bolts) with the hinges of its halves; the two grips at
    the rim (rubber 12) he holds; the small dash under the rim (gunmetal, a black face; the screen glows: GlowChest)."""
    fd = Field("Cockpit")
    quilt = lambda P: F(0.0018) * np.abs(np.sin(P[:, 2] * F(60))) + F(0.0008) * NOISE(P * F(30))
    fd.add(RoundBox((0, 0.175, 1.52), (0.2, 0.03, 0.24), 0.03, disp=quilt, disp_amp=0.002), 0.0, K_BLACK)
    fd.add(RoundBox((0, 0.17, 1.8), (0.13, 0.032, 0.085), 0.03, R=euler(0.08, 0, 0), disp=quilt, disp_amp=0.002), 0.0, K_BLACK)
    for sx in (-1, 1):
        fd.add(RoundCone(v3((sx * 0.08, 0.19, 1.7)), v3((sx * 0.08, 0.19, 1.76)), 0.013), 0.004, K_GUN)
        # cables down the hatch's side walls
        fd.add(Chain([v3((sx * (CUT_X - 0.005), 0.12, 1.92)), v3((sx * (CUT_X - 0.012), 0.05, 1.7)), v3((sx * (CUT_X - 0.008), 0.0, 1.45)),
                      v3((sx * (CUT_X - 0.003), -0.05, 1.3))], [0.012] * 4, k=0.01), 0.004, K_RUBBER if sx < 0 else K_AMBER)
    # the welded frame round the hatch: two upright bars and a sill, bolted, weld beads at the joints
    for sx in (-1, 1):
        a, b = v3((sx * BAR_X, BAR_Y, CUT_Z0 - 0.03)), v3((sx * BAR_X, BAR_Y + 0.02, BAR_TOP))
        fd.add(seg_box(a, b, (0.024, 0.022), 0.008, side_ref=(1, 0, 0)), 0.0, K_GUN)
        for z in (1.46, 1.62, 1.78):
            fd.add(Cylinder(v3((sx * (BAR_X + 0.006), BAR_Y - 0.022, z)), 0.011, 0.012, rr=0.004, R=rot_from_axes(z_axis=(0, -1, 0))), 0.003, K_STEEL)
        # the hinges of the hatch's halves (three knuckles on the bar's outer edge)
        for z in (1.45, 1.62, 1.79):
            fd.add(Cylinder(v3((sx * (BAR_X + 0.028), DOOR_Y, z)), 0.017, 0.07, rr=0.005), 0.004, K_GUN)
            fd.add(RoundBox(v3((sx * (BAR_X + 0.05), DOOR_Y - 0.004, z)), (0.03, 0.006, 0.03), 0.004), 0.004, K_GUN)
        weld(fd, [v3((sx * (BAR_X - 0.03), BAR_Y - 0.012, CUT_Z0 - 0.02)), v3((sx * (BAR_X + 0.02), BAR_Y - 0.012, CUT_Z0 - 0.02))], 0.01, K_STEEL)
        weld(fd, [v3((sx * BAR_X, BAR_Y - 0.004, BAR_TOP - 0.01)), v3((sx * BAR_X, BAR_Y + 0.05, BAR_TOP + 0.005))], 0.01, K_STEEL)
    fd.add(seg_box(v3((-BAR_X, BAR_Y, CUT_Z0 - 0.03)), v3((BAR_X, BAR_Y, CUT_Z0 - 0.03)), (0.024, 0.026), 0.008, side_ref=(0, 0, 1)), 0.004, K_GUN)
    # the grips at the rim
    for side in ("R", "L"):
        gr = GRIP[side]
        fd.add(RoundCone(gr - v3((0, 0, 0.07)), gr + v3((0, 0, 0.05)), 0.02, 0.019), 0.004, K_RUBBER)
        fd.add(RoundCone(gr - v3((0, 0, 0.07)), gr + v3((0, 0.06, -0.08)), 0.012), 0.004, K_STEEL)
    # the dash under the rim
    Rd = euler(0.7, 0, 0)
    fd.add(RoundBox((0, FRONT_Y + 0.11, CUT_Z0 + 0.02), (0.13, 0.05, 0.05), 0.02, R=Rd), 0.0, K_GUN)
    fd.add(RoundBox((0, FRONT_Y + 0.085, CUT_Z0 + 0.05), (0.1, 0.03, 0.008), 0.006, R=Rd), 0.004, K_BLACK)
    return fd


# ======================================================================================= the fists
def _bx(v, w, u):
    return (v * FS, w * FS, u * FU)


def fist_hand(fd, side):
    """The fist's body on the hand bone: the wrist cuff (graphite), the back-of-hand armour (white, a hazard-orange edge,
    an amber slash), the palm block (graphite), the armoured thumb (white) wrapped over the fingers."""
    R = gR(side)
    wr, A, W, M = gframe(side)
    fd.add(Cylinder(fp(side, 0.018, 0, 0), 0.128 * FS, 0.07 * FU, rr=0.026, R=rot_from_axes(z_axis=A)), 0.0, GRAPH)
    fd.add(RoundBox(fp(side, 0.12, 0.0, -0.035), _bx(0.165, 0.075, 0.095), 0.06, R=R), 0.025, WHITE)
    fd.add(RoundBox(fp(side, 0.115, 0.0, 0.055), _bx(0.15, 0.06, 0.085), 0.05, R=R), 0.025, GRAPH)
    th = [fp(side, 0.06, 0.15, 0.03), fp(side, 0.13, 0.19, 0.085), fp(side, 0.21, 0.15, 0.13), fp(side, 0.25, 0.08, 0.14)]
    fd.add(Chain(th, [r * FS for r in (0.052, 0.048, 0.044, 0.04)], k=0.012), 0.025, WHITE)
    fd.add(Sphere(fp(side, 0.13, 0.215, 0.085), 0.032 * FS), 0.008, GRAPH)
    fd.paint(RoundBox(fp(side, 0.12, 0.0, -0.035), _bx(0.2, 0.2, 0.012), 0.0, R=R), PANEL)
    fd.paint(RoundBox(fp(side, 0.19, 0.0, -0.035), _bx(0.3, 0.2, 0.012), 0.0, R=R), ORANGE)
    n = -M
    c = fp(side, 0.115, 0.0, -0.11)
    spray(fd, [c - A * 0.07 + W * 0.15, c + A * 0.07 - W * 0.15], 0.032, n, AMBER, depth=0.07)
    dents(fd, [(fp(side, 0.08, -0.08, -0.11), n, 0.035)])


def fist_fingers(fd, side):
    """The four fingers (one block on the fingers bone): fat curled segments (graphite) under armoured backs (white), and
    the Resistance's welded knuckle bar across their front (bare battered steel 10, four studs, weld beads)."""
    R = gR(side)
    wr, A, W, M = gframe(side)
    for i, v in enumerate(FINGER_V):
        s = 0.92 if i == 3 else 1.0
        du = -0.014 if i == 3 else 0.0
        K1 = fp(side, 0.215 + du, v, -0.055)
        K2 = fp(side, 0.29 + du, v, 0.0)
        K3 = fp(side, 0.272 + du, v, 0.085)
        K4 = fp(side, 0.205 + du, v * 0.96, 0.115)
        fd.add(Chain([K1, K2, K3, K4], [r * s * FS for r in (0.046, 0.044, 0.041, 0.036)], k=0.008), 0.008, GRAPH)
        fd.add(RoundBox(fp(side, 0.275 + du, v, 0.06), _bx(0.032 * s, 0.024, 0.03), 0.018, R=R), 0.01, WHITE)
    # the knuckle bar
    fd.add(RoundBox(fp(side, 0.31, 0.0, KN_W), _bx(0.178, 0.072, 0.034), 0.024, R=R, disp=dent(0.0015, 30), disp_amp=0.002), 0.012, STEEL)
    for v in FINGER_V:
        fd.add(Cylinder(fp(side, 0.345, v, KN_W), 0.03 * FS, 0.025 * FU, rr=0.012, R=rot_from_axes(z_axis=A)), 0.006, STEEL)
    for sw in (-1, 1):
        weld(fd, [fp(side, 0.29, -0.17, KN_W + sw * 0.07), fp(side, 0.29, 0.17, KN_W + sw * 0.07)], 0.011, STEEL)


def fists_field():
    subs = []
    for side in ("R", "L"):
        f = Field("FistHand" + side)
        fist_hand(f, side)
        subs.append(("hand." + side, f))
        f = Field("FistFingers" + side)
        fist_fingers(f, side)
        subs.append(("fingers." + side, f))
    return PaintedMulti("Fists", subs)


# ======================================================================================= the glows
def lamp_glow():
    """The amber work lamp's lens in the smashed eye's socket (on `mhead`)."""
    fd = Field("Lamp")
    fd.add(Cylinder(EYE_M + v3((0, -0.056, 0)), 0.035, 0.012, rr=0.005, R=rot_from_axes(z_axis=(0, 1, 0))), 0.0)
    return fd


def arm_glow(side):
    """The amber ring round the forearm housing's front."""
    fd = Field("Arm" + side)
    wr, A, W, M = gframe(side)
    fd.add(Torus(gp(side, H_FRONT + 0.014, 0, 0), HR1 + 0.005, 0.012, R=rot_from_axes(z_axis=A)), 0.0)
    return fd


def chest_glow():
    """The dash's screen under the rim, two lamps on the hatch frame's tops."""
    fd = Field("Chest")
    fd.add(RoundBox((0, FRONT_Y + 0.078, CUT_Z0 + 0.055), (0.085, 0.03, 0.006), 0.004, R=euler(0.7, 0, 0)), 0.0)
    for sx in (-1, 1):
        fd.add(Sphere(v3((sx * BAR_X, BAR_Y - 0.03, BAR_TOP - 0.05)), 0.016), 0.0)
    return fd


def core_glow():
    """The power pack's core, behind its window on the mech's back."""
    fd = Field("Core")
    fd.add(RoundBox((0, PACK_C[1] + 0.12, PACK_C[2] + 0.02), (0.055, 0.02, 0.11), 0.02), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.62)), hr(0.05), 0.5)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.11, -0.15, 1.628)), hr(0.07), 0.55)]
    return pts


# ======================================================================================= build config
GLB_NAME = "titan_mech"
ROOT_NAME = "TitanMechHQ"
TEX_PREFIX = "titan"
MAT_NAME = "TitanMechMat"
MESH_NAME = "TitanMech"
BASE_MODULE = "titan_mech_base"
ANIM_MODULE = "anim_titan_mech"
PARTS = ["Skin", "Eyes", "Cap", "Pilot", "Cockpit", "Armour", "Frame", "Fists", "Lamp", "ArmR", "ArmL", "Chest", "Core"]
REGION_PARTS = ("Skin", "Cap", "Pilot", "Cockpit", "Armour", "Frame", "Fists")
PLATES = dict(suit=(0.1, 0.1, 0.11), graphite=GUNMETAL, navy=CHARCOAL, violet=(0.92, 0.56, 0.14), tape=TEAL,
              steel=(0.56, 0.58, 0.62), glass=(0.03, 0.035, 0.045), white=ROBOT_WHITE, orange=HAZARD,
              rubber=(0.085, 0.085, 0.09), yellow=AMBER_PAINT, wear=1.3)
KIT = dict(weave=0.0, base=CHARCOAL, black=(0.05, 0.05, 0.058), red=(0.72, 0.07, 0.05), white=(0.88, 0.88, 0.86), olive=TEAL,
           gunmetal=(0.26, 0.27, 0.3), steel=(0.66, 0.68, 0.72), glass=(0.06, 0.05, 0.04), rubber=(0.07, 0.07, 0.075),
           coyote=(0.95, 0.6, 0.15), glass_hi=(0.95, 0.62, 0.2))
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_TitanPilotSkin", "base": (0.8, 0.59, 0.46), "ruddy": (0.8, 0.5, 0.4), "lips": (0.6, 0.37, 0.32),
                      "brow": ((0.06, 0.045, 0.035), (0.14, 0.1, 0.075)),
                      "extra": ((LASH, (0.05, 0.035, 0.03), 0.5), (STUBBLE, (0.42, 0.33, 0.28), 0.6, 0.45),
                                (SCAR, (0.86, 0.6, 0.52), 0.45))}),
    "Cap": ("modern_kit", dict(KIT, name="HQ_TitanCap", base=(0.17, 0.135, 0.11))),
    "Pilot": ("modern_kit", dict(KIT, name="HQ_TitanPilot", weave=1.0)),
    "Cockpit": ("modern_kit", dict(KIT, name="HQ_TitanKit")),
    "Armour": ("android", dict(PLATES, name="HQ_TitanPlates")),
    "Frame": ("modern_kit", dict(KIT, name="HQ_TitanKit")),
    "Fists": ("android", dict(PLATES, name="HQ_TitanPlates")),
    "Lamp": ("glow_ball", {"name": "HQ_TitanGlow", "col": AMBER_GLOW}),
    "ArmR": ("glow_ball", {"name": "HQ_TitanGlow", "col": AMBER_GLOW}),
    "ArmL": ("glow_ball", {"name": "HQ_TitanGlow", "col": AMBER_GLOW}),
    "Chest": ("glow_ball", {"name": "HQ_TitanGlow", "col": AMBER_GLOW}),
    "Core": ("glow_ball", {"name": "HQ_TitanGlow", "col": AMBER_GLOW}),
}
_G = (AMBER_GLOW, 1.2, 0.5)
GLOW = {"Lamp": (AMBER_GLOW, 1.35, 0.5), "ArmR": _G, "ArmL": _G, "Chest": _G, "Core": _G}
LOW_TARGETS = {"Skin": 2600, "Cap": 1300, "Pilot": 1500, "Cockpit": 1500, "Armour": 8600, "Frame": 4600, "Fists": 4000,
               "Lamp": 80, "ArmR": 140, "ArmL": 140, "Chest": 120, "Core": 60}
AO_EXCLUDE = ["Cap"]
MHEAD_BONE = (v3((0.0, 0.26, 1.96)), v3((0.0, 0.26, 2.2)))


def prop_bones():
    """The fingers' blocks (children of the hands, hinged across the knuckles; their tails toward the knuckle bar)."""
    out = []
    for side in ("R", "L"):
        h = finger_hinge(side)
        out.append(("fingers." + side, h, h + gframe(side)[1] * 0.12, "hand." + side))
    return out


def extra_bones():
    """The robot's own head (`mhead`, a child of the hull: it turns a little on its neck)."""
    return [("mhead", MHEAD_BONE[0], MHEAD_BONE[1], "chest")]


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Cap": ("rigid", "head"), "Pilot": ("rigid", "chest"), "Cockpit": ("rigid", "chest"),
        "Armour": ("custom", island_weights(armour_field)),
        "Frame": ("custom", island_weights(frame_field)),
        "Fists": ("custom", island_weights(fists_field)),
        "Lamp": ("rigid", "mhead"), "ArmR": ("rigid", "forearm.R"), "ArmL": ("rigid", "forearm.L"),
        "Chest": ("rigid", "chest"), "Core": ("rigid", "chest"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part == "Skin" and c.z > face_z and c.y < W_HC[1] - 0.05:
        return 2.4
    if part == "Skin":
        return 1.2
    if part == "Pilot":
        return 0.8
    if part == "Cap":
        return 1.4
    if part == "Frame":
        return 0.7
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.0024 if fine else 0.0036),
        ("Eyes", eyes_field(), 0.0015),
        ("Cap", cap_field(), 0.0022 if fine else 0.0032),
        ("Pilot", pilot_field(), 0.0034 if fine else 0.005),
        ("Cockpit", cockpit_field(), 0.0032 if fine else 0.0048),
        ("Armour", armour_field(), 0.0046 if fine else 0.0066),
        ("Frame", frame_field(), 0.004 if fine else 0.006),
        ("Fists", fists_field(), 0.0036 if fine else 0.0052),
        ("Lamp", lamp_glow(), 0.003),
        ("ArmR", arm_glow("R"), 0.003),
        ("ArmL", arm_glow("L"), 0.003),
        ("Chest", chest_glow(), 0.003),
        ("Core", core_glow(), 0.003),
    ]
