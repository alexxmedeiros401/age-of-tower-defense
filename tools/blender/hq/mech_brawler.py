"""The Mech Brawler (HQ tower, Digital Age; Brute lineage, melee). Rest pose = an A-pose, facing -Y, feet at z = 0;
right side = -X.

A compact, chunky piloted exo-mech of the Digital Age's tech corps (about 2.3 m to the top of its roll bar): short
thick legs, a squat pelvis on a rubber-booted waist actuator, a broad armoured chest with the open cockpit in it, big
shoulders under domed pauldrons, long gorilla arms ending in two huge armoured fists. Graphite armour plates (label 0
of the material) with midnight-navy panels (8), black panel lines (5), gunmetal frames and joints (9), bright steel
piston rods (10), black rubber (12), small white stencils (7) and a violet painted pinstripe (6). Its light strips glow
magenta-violet (their own emissive meshes): a strip under the cockpit's front rim and two down the chest plate, the
dashboard screen (`GlowChest`); a ring round each forearm housing's front and a strip along its outer side (`GlowArmR`,
`GlowArmL`); the energy fists' knuckle plates (`GlowKnuckleR`, `GlowKnuckleL`).

The pilot sits in the open cockpit in its chest, his head where the mech's head would be: a cheerful, cocky young pilot
(a warm tan face, a lopsided grin with his teeth showing, his left brow cocked, bright brown eyes, dark hair cropped
short), in a slim graphite flight helmet (a navy stripe over its crown with a violet pinstripe each side) with its
smoked visor flipped up over its front, the headset's ear cups built into its sides and a boom mic from the left cup to
the corner of his mouth; a high-collared midnight-navy flight suit with a graphite chest plate, black gloves on the two
control sticks. Behind him the seat's headrest and a roll bar arching over his head; before him the dashboard.

Machines don't bend: every mech part rides one bone (as the robots, robot_*.py). The mech is the rig: root = pelvis,
spine = the waist actuator, chest = the hull, cockpit and pilot, clavicles = the shoulder actuators, the arms and legs
as a man's; the pilot's neck and head are the rig's neck and head (he looks about). Each fist rides its hand bone (the
wrist stays straight), its four fingers one block on `fingers.R` / `fingers.L` (children of the hands, hinged across the
knuckles: the clips open and clench them), the knuckle plates' front = the knuckle point. Parts that hold pieces of
several bones (Armour, Frame, Fists) are `MultiField`s: each piece meshed on its own (they pass through each other at
the joints, as a machine's do), each mesh island weighted 100% to the bone of the piece it came from."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp

# ======================================================================================= labels
SKIN, NAIL, LIP, MOUTH, BROW, LASH = 0, 1, 2, 3, 4, 8
# modern_kit labels: graphite (0), black (5), violet paint (6, its `red`), white (7), navy (8, its `olive`), gunmetal (9),
# steel (10), smoked glass (11), rubber (12), hazard yellow (13, its `coyote`)
GRAPH, BLACK, VIOLET, WHITE, NAVY, GUN, STEEL, GLASS, RUBBER, HAZARD = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13

GRAPHITE = (0.16, 0.17, 0.2)          # the corps' armour (the brief: the recipes read colours as sRGB)
MIDNIGHT = (0.12, 0.16, 0.3)
VIOLET_GLOW = (0.85, 0.25, 0.95)
IRIS = ((0.3, 0.17, 0.07), (0.6, 0.38, 0.16))          # bright warm brown eyes (prep.paint_eyes)

# ======================================================================================= the skeleton (the mech's joints)
J = {
    "root": (0.0, 0.03, 1.0),
    "head_end": (0.0, -0.03, 2.16),
}
for _s, _x in (("R", -1), ("L", 1)):
    J["shoulder_" + _s] = (_x * 0.6, 0.06, 1.56)
    J["elbow_" + _s] = (_x * 0.76, 0.12, 1.12)
    J["wrist_" + _s] = (_x * 0.82, 0.02, 0.72)
    J["hip_" + _s] = (_x * 0.26, 0.04, 0.95)
    J["knee_" + _s] = (_x * 0.29, -0.05, 0.58)
    J["ankle_" + _s] = (_x * 0.3, 0.05, 0.21)
    J["toe_" + _s] = (_x * 0.31, -0.3, 0.06)
J = {k: v3(v) for k, v in J.items()}
TORSO = {"root", "spine", "chest", "neck"}
TORSO_Z = (0.9, 1.0, 1.15, 1.55)
CLAV_Z = 1.56


def torso_bones():
    return {
        "spine": ((0, 0.03, 1.0), (0, 0.03, 1.2)),
        "chest": ((0, 0.03, 1.2), (0, 0.04, 1.55)),
        "neck": ((0, 0.01, 1.6), (0, -0.01, 1.77)),
        "head": ((0, -0.01, 1.77), (0, -0.03, 2.16)),
        "clavicle_z": CLAV_Z,
    }


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


# ======================================================================================= the pilot's head space
# His head is designed in the same coordinates as the other heroes' (tarek.py / flamethrower.py: the head's centre at
# (0, 0.03, 1.73)) and placed in the cockpit by hp(): design -> world, scaled by PS.
PS = 0.9
D_HC = v3((0.0, 0.03, 1.73))
W_HC = v3((0.0, -0.02, 1.98))
HS = PS


def hp(p):
    return W_HC + (v3(p) - D_HC) * PS


def hr(r):
    return r * PS


def hinv(P):
    return (P - W_HC.astype(F)) / F(PS) + D_HC.astype(F)


HEAD_C = hp(D_HC)
HEAD_RAD = v3((0.176, 0.19, 0.186)) * PS
EYE_R = hr(0.039)


def eye_c(sx):
    return hp((sx * 0.07, -0.146, 1.674))


# ======================================================================================= the arms' frame (as steam_brawler.py)
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


FU, FS = 1.18, 1.3           # the fist's scale (designed at 1.0 about the wrist): along the forearm, across it


def fp(side, u, v, w):
    return gp(side, u * FU, v * FS, w * FS)


def gR(side):
    """Rotation whose local x, y, z are the frame's W, M, A (a box's half sizes given as (v, w, u))."""
    wr, A, W, M = gframe(side)
    return np.stack([W, M, A], axis=1)


def hand_frame(side):
    wr, A, W, M = gframe(side)
    return wr, A, M, W


KN_U = 0.354                # the knuckle plates' front (u, from the wrist): the knuckle point
KN_W = -0.012
HINGE_U, HINGE_W = 0.205, -0.02     # the fingers' hinge (across the knuckles)
FINGER_V = (0.117, 0.039, -0.039, -0.117)           # index (thumb side) .. little finger


def knuckle_point(side):
    return fp(side, KN_U, 0.0, KN_W)


def finger_hinge(side):
    return fp(side, HINGE_U, 0.0, HINGE_W)


H_FRONT = -0.03             # the forearm housing's front end (u, from the wrist)
HR0, HR1 = 0.142, 0.178     # its radius at the elbow end and at the front
TILT = 0.5                  # its elbow end is cut on a slant


def h_rad(u):
    return F(HR0) + F(HR1 - HR0) * np.clip((u + F(0.34)) / F(0.3), 0, 1)


def h_back(v):
    return F(-0.355) + F(TILT) * v


# ======================================================================================= MultiField: rigid pieces in one part
class MultiField(Field):
    """Several rigid pieces in one part, each (bone, Field) meshed on its own: pieces of different bones may pass
    through each other at the joints (a machine's do), and each mesh island rides one bone (`island_weights`)."""

    def __init__(self, name, subs):
        super().__init__(name)
        self.subs = [(b, f) for b, f in subs if f.ops]
        self.ops = [op for b, f in self.subs for op in f.ops]

    def mesh(self, voxel, lo=None, hi=None, chunk=24, verbose=True):
        V, Fc, n = [], [], 0
        for b, f in self.subs:
            v, fc = f.mesh(voxel, chunk=chunk, verbose=verbose)
            V.append(v)
            Fc.append(fc + n)
            n += len(v)
        return np.concatenate(V), np.concatenate(Fc)

    def owners(self, P):
        P = np.asarray(P, dtype=F)
        D = np.stack([np.abs(f.eval(P)) for b, f in self.subs], 1)
        return np.argmin(D, 1)

    def eval(self, P, labels=False, margin=0.0):
        P = np.asarray(P, dtype=F)
        res = [f.eval(P, labels=True, margin=margin) for b, f in self.subs]
        D = np.stack([r[0] for r in res], 1)
        d = D.min(1)
        if not labels:
            return d
        own = np.argmin(np.abs(D), 1)
        L = np.stack([r[1] for r in res], 1)
        return d, L[np.arange(len(P)), own]

    def paint_dist(self, P, band=0.004):
        P = np.asarray(P, dtype=F)
        own = self.owners(P)
        out = {}
        for i, (b, f) in enumerate(self.subs):
            pd = f.paint_dist(P, band)
            for L, d in pd.items():
                o = out.setdefault(L, np.full(len(P), F(1.0)))
                o[own == i] = d[own == i]
        return out


def _islands(me):
    """Connected components of a mesh's faces: an island id per vertex."""
    n = len(me.vertices)
    par = np.arange(n)

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for p in me.polygons:
        vs = list(p.vertices)
        r0 = find(vs[0])
        for v in vs[1:]:
            r = find(v)
            if r != r0:
                par[r] = r0
    return np.array([find(i) for i in range(n)])


def island_weights(builder):
    """Weights for a MultiField part: every mesh island rides the bone of the piece it lies on (the piece whose
    surface its vertices are nearest to, by a vote of its vertices)."""
    def fn(ob, skin_ob, arm):
        mf = builder()
        me = ob.data
        P = np.zeros(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", P)
        P = P.reshape(-1, 3) + np.array(ob.location, np.float32)
        isl = _islands(me)
        own = mf.owners(P)
        bones = [b for b, f in mf.subs]
        for g in list(ob.vertex_groups):
            ob.vertex_groups.remove(g)
        groups = {}
        for r in np.unique(isl):
            idx = np.nonzero(isl == r)[0]
            votes = np.bincount(own[idx], minlength=len(bones))
            b = bones[int(np.argmax(votes))]
            g = groups.get(b) or ob.vertex_groups.new(name=b)
            groups[b] = g
            g.add([int(i) for i in idx], 1.0, "REPLACE")
    return fn


# ======================================================================================= small helpers
def seg_box(a, b, half_xy, r, side_ref=(1, 0, 0), along_pad=0.0, **kw):
    """A rounded box along a -> b (local z), `half_xy` across it; local x toward side_ref."""
    a, b = v3(a), v3(b)
    z = norm(b - a)
    x = norm(v3(side_ref) - z * (v3(side_ref) @ z))
    R = np.stack([x, np.cross(z, x), z], axis=1)
    L = np.linalg.norm(b - a) / 2 + along_pad
    return RoundBox((a + b) / 2, (half_xy[0], half_xy[1], L), r, R=R, **kw)


def dent(amp=0.0008, s=30.0):
    return lambda P: F(amp) * NOISE(P * F(s))


# ======================================================================================= the pilot: head
def head(fd):
    """A cheerful, cocky young face: a firm jaw, round cheeks lifted by his grin, level dark brows (the left cocked up),
    warm brown eyes crinkled by the grin, a straight nose, a wide lopsided grin with his teeth showing (its left corner
    higher)."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.05, 1.59), (0.155, 0.14, 0.128)), hr(0.07), SKIN)                          # the jaw
    fd.add(E((0, -0.138, 1.5), (0.088, 0.07, 0.066)), hr(0.05), SKIN)                          # a firm chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.128, 1.638), 0.054), hr(0.05), SKIN)                           # round cheeks
        fd.add(S((sx * 0.134, -0.044, 1.556), 0.054), hr(0.05), SKIN)                           # the jaw's corners
        pts = [hp((sx * 0.154, -0.055, 1.744)), hp((sx * 0.116, -0.134, 1.758)), hp((sx * 0.062, -0.176, 1.757)), hp((0.0, -0.186, 1.752))]
        fd.add(Chain(pts, [hr(0.012), hr(0.019), hr(0.022), hr(0.02)], k=hr(0.022)), hr(0.03), SKIN)    # the brow ridge
    # dark brows, level on the brow ridge; his left one cocked up (the cocky look), the right a touch lower
    tuft = lambda P: F(0.0022) * NOISE(P * F(150)) + F(0.001) * np.sin(P[:, 0] * F(380))
    for sx in (-1, 1):
        up = (0.0, 0.012, 0.019, 0.012) if sx > 0 else (0.0, -0.002, -0.002, -0.004)
        pts = [hp((sx * 0.026, -0.21, 1.806 + up[0])), hp((sx * 0.068, -0.205, 1.814 + up[1])), hp((sx * 0.112, -0.185, 1.811 + up[2])),
               hp((sx * 0.154, -0.146, 1.792 + up[3]))]
        fd.add(Chain([p + v3((0, 0.006 * PS, 0)) for p in pts], [hr(0.0105), hr(0.0125), hr(0.011), hr(0.0055)], k=hr(0.008),
                     disp=tuft, disp_amp=0.0022), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.02), hr(0.023), hr(0.021), hr(0.012)], k=hr(0.01)), BROW)
    # eyes crinkled by the grin (the left a little wider under its cocked brow)
    for sx in (-1, 1):
        ec = eye_c(sx)
        top = 0.022 if sx < 0 else 0.026
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        lid = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(top))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(lid, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0062)), Plane(ec + v3((0, 0, -hr(0.0105))), (sx * -0.16, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(top - 0.003))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(2):                                                                      # laughter lines
            a = hp((sx * (0.108 + 0.004 * k), -0.128 + 0.006 * k, 1.68 - 0.012 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.02, 0.011, -0.002 - 0.008 * k)) * PS, hr(0.002), hr(0.0014)), hr(0.003))
    # a straight nose
    fd.add(RoundCone(hp((0, -0.186, 1.722)), hp((0, -0.228, 1.64)), hr(0.017), hr(0.022)), hr(0.017), SKIN)
    fd.add(S((0, -0.228, 1.628), 0.025), hr(0.015), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.033, -0.214, 1.608), 0.022), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.018, -0.232, 1.598)), v3((0.009, 0.0105, 0.0065)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # the lopsided grin, teeth showing; its left corner pulled higher into his cheek
    slot = [hp((-0.082, -0.154, 1.58)), hp((-0.047, -0.19, 1.553)), hp((0, -0.201, 1.543)), hp((0.048, -0.19, 1.558)),
            hp((0.086, -0.151, 1.593))]
    fd.sub(Chain(slot, [hr(0.006), hr(0.015), hr(0.0175), hr(0.015), hr(0.006)], k=hr(0.004)), hr(0.004))
    fd.paint(Chain(slot, [hr(0.007), hr(0.0165), hr(0.019), hr(0.0165), hr(0.007)], k=hr(0.004)), MOUTH)
    lo_lip = [(-0.068, -0.161, 1.565), (-0.037, -0.188, 1.531), (0, -0.195, 1.524), (0.038, -0.188, 1.535), (0.072, -0.159, 1.578)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0076), hr(0.0086), hr(0.0076), hr(0.004)], k=hr(0.007)), hr(0.008), LIP)
    for sx in (-1, 1):
        cz = 1.596 if sx > 0 else 1.582
        fd.add(S((sx * 0.092, -0.146, cz), 0.01), hr(0.007), SKIN)                             # the grin's corners in his cheeks
        fd.add(Ellipsoid(hp((sx * 0.176, 0.035, 1.664)), v3((0.026, 0.048, 0.062)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.196, 0.028, 1.668)), v3((0.011, 0.03, 0.04)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))


def neck_prim():
    return RoundCone(hp((0, 0.045, 1.47)), hp((0, 0.07, 1.27)), hr(0.074), hr(0.084))


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


def teeth_field():
    """His upper teeth in the grin."""
    fd = Field("Teeth")
    for k in range(6):
        x = -0.05 + 0.02 * k
        y = -0.184 + 0.014 * (abs(x) / 0.05) ** 2
        lift = 0.004 * max(0.0, x) / 0.05
        fd.add(RoundBox(hp((x, y, 1.552 + lift + 0.007 * (abs(x) / 0.05) ** 2)), v3((0.0094, 0.006, 0.0105)) * HS, hr(0.003)), 0.002)
    return fd


# ======================================================================================= hair (cropped under the helmet)
def skull():
    return Ellipsoid(HEAD_C, HEAD_RAD)


def hair_field():
    """Dark hair cropped close: under the helmet at his temples and nape, a tuft over his brow."""
    fd = Field("Hair")
    stub = lambda P: F(0.0016) * NOISE(P * np.array([70, 70, 26], F)) + F(0.0008) * NOISE(P * F(140))

    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        face = np.where(ax < F(0.13), F(-0.09) - y, F(-0.125) - y)
        side = np.where((ax > F(0.12)) & (y < F(0.0)), F(1.7) - z, F(-1.0))
        ear = np.where((ax > F(0.15)) & (z < F(1.735)) & (np.abs(y - F(0.035)) < F(0.065)), F(0.02), F(-1.0))
        nape = F(1.6) - z
        return np.maximum(np.maximum(face, side), np.maximum(ear, nape))
    fd.add(Inter(Shell(skull(), 0.004, 0.009 * PS, pad=0.06, disp=stub, disp_amp=0.002), Func(keep, HEAD_C - 0.4, HEAD_C + 0.4), 0.004), 0.0)
    return fd


# ======================================================================================= the helmet (design space)
HELM_C = HEAD_C + v3((0.0, 0.004, 0.014))
HELM_OUT = HEAD_RAD + v3((0.034, 0.034, 0.034))     # the shell's outside ...
HELM_IN = HEAD_RAD + v3((0.014, 0.014, 0.016))      # ... and inside (clear of his skull)
# its edge (design z): high over his brow (EF), down over his ears at the sides (ES), low at the nape (EB)
EF, ES, EB = 1.862, 1.635, 1.655


def _phi(P):
    """Angle round the helmet's axis from straight ahead (0) to behind (+-pi), + toward his left."""
    return np.arctan2(P[:, 0], -(P[:, 1] - F(HELM_C[1])))


def edge_d(P):
    """Design-space height of the helmet's edge round its axis."""
    ph = _phi(P)
    a = ((EF + EB) / 2 + ES) / 2
    c = ((EF + EB) / 2 - ES) / 2
    b = (EF - EB) / 2
    return F(a) + F(b) * np.cos(ph) + F(c) * np.cos(2 * ph)


def above_edge(P):
    """> 0 above the helmet's edge (world units)."""
    return (hinv(P)[:, 2] - edge_d(P)) * F(PS)


def helm_outer():
    return Ellipsoid(HELM_C, HELM_OUT)


def on_helmet(phi, zd, off=0.0):
    """A point on the helmet's outer surface at angle phi round its axis and design height zd, the outward normal."""
    z = hp((0, 0, zd))[2]
    d = v3((math.sin(phi), -math.cos(phi), 0.0))
    o = v3((HELM_C[0], HELM_C[1], z)) + d * 0.6
    h, ok = ray_hit(helm_outer(), [o], [-d], tmax=0.6, step=0.0008)
    q = h[0]
    n = norm((q - HELM_C) / (HELM_OUT ** 2))
    return q + n * off, n


EAR_D = (0.188, 0.03, 1.666)            # the ear cups' middle (design)


def helmet_field():
    """A slim graphite flight helmet (0): a navy stripe over its crown (8) with a violet pinstripe each side (6), a black
    rubber trim round its edge (5); the headset's ear cups built into its sides (black, a navy cap with a white rim
    line); a boom mic from the left cup to the corner of his mouth (black, a steel band)."""
    fd = Field("Helmet")
    out, inn = helm_outer(), Ellipsoid(HELM_C, HELM_IN)
    lo, hi = HELM_C - HELM_OUT - 0.03, HELM_C + HELM_OUT + 0.03

    def shell(P):
        return smax(np.maximum(out(P), -inn(P)), -above_edge(P), F(0.005))
    fd.add(Func(shell, lo, hi, disp=dent(0.0006, 30), disp_amp=0.0008), 0.0, GRAPH)

    def trim(P):
        d = np.abs(above_edge(P) - F(0.006)) - F(0.0075)
        return np.maximum(d, np.abs(out(P) + F(0.01)) - F(0.013))
    fd.add(Func(trim, lo, hi), 0.003, BLACK)
    # the crown stripe and pinstripes (painted: across x, over the crown from the brow to the nape)
    def stripe(P, half):
        return np.maximum(np.abs(P[:, 0] - F(HELM_C[0])) - F(half), F(0.004) - above_edge(P))
    fd.paint(Func(lambda P: stripe(P, 0.042), lo, hi), NAVY)
    fd.paint(Func(lambda P: np.maximum(np.abs(np.abs(P[:, 0]) - F(0.05)) - F(0.0045), F(0.004) - above_edge(P)), lo, hi), VIOLET)
    # the ear cups
    for sx in (-1, 1):
        c = hp((sx * EAR_D[0], EAR_D[1], EAR_D[2]))
        n = norm(v3((sx * 1.0, 0.05, 0.0)))
        R = rot_from_axes(z_axis=n)
        fd.add(Cylinder(c + n * 0.012, hr(0.064), 0.05, rr=0.014, R=R), 0.008, BLACK)
        fd.add(Cylinder(c + n * 0.034, hr(0.05), 0.016, rr=0.006, R=R), 0.003, NAVY)
        fd.paint(Torus(c + n * 0.042, hr(0.04), 0.0035, R=R), WHITE)
    # the boom mic: from the left cup's front, along his cheek to the corner of his mouth
    pts = [hp((0.19, -0.02, 1.632)), hp((0.172, -0.1, 1.582)), hp((0.13, -0.165, 1.548)), hp((0.098, -0.192, 1.536))]
    fd.add(Chain(pts, [hr(0.009), hr(0.0075), hr(0.007), hr(0.007)], k=0.004), 0.004, BLACK)
    fd.add(Sphere(hp((0.093, -0.196, 1.535)), hr(0.015)), 0.004, BLACK)
    fd.paint(Sphere(hp((0.172, -0.1, 1.582)), hr(0.012)), STEEL)
    return fd


VIS_OFF, VIS_T = 0.01, 0.008           # the visor: this far out from the helmet, this thick
VIS_PHI = math.radians(70)             # its half width (round the helmet)
VIS_LO, VIS_HI = 1.885, 1.952          # its band (design z) over the helmet's front, flipped up
PIVOT_PHI = math.radians(92)


def _vis_band(P):
    """> 0 outside the visor's outline (lying flipped up over the helmet's front)."""
    phi = _phi(P)
    z = hinv(P)[:, 2]
    taper = F(0.035) * (np.abs(phi) / F(VIS_PHI)) ** 2
    return np.maximum((np.abs(phi) - F(VIS_PHI)) * F(0.2), np.maximum(F(VIS_LO) - taper - z, z - F(VIS_HI) + taper * F(0.4)) * F(PS))


def visor_field():
    """Smoked glass (11) in a black frame (5): the visor flipped up over the helmet's front; its arms back to pivots on
    the helmet's sides, a violet dot on each pivot (6)."""
    fd = Field("Visor")
    out = helm_outer()
    lo, hi = HELM_C - HELM_OUT - 0.05, HELM_C + HELM_OUT + 0.05

    def plate(P):
        return np.maximum(np.abs(out(P) - F(VIS_OFF)) - F(VIS_T / 2), _vis_band(P))
    fd.add(Func(plate, lo, hi), 0.0, GLASS)

    def frame(P):
        b = _vis_band(P)
        return np.maximum(np.maximum(np.abs(out(P) - F(VIS_OFF)) - F(VIS_T / 2 + 0.0025), b - F(0.0025)), F(-0.009) - b)
    fd.add(Func(frame, lo, hi), 0.003, BLACK)
    for sx in (-1, 1):
        piv, n = on_helmet(sx * PIVOT_PHI, 1.79, 0.004)
        fd.add(Cylinder(piv, 0.021, 0.012, rr=0.004, R=rot_from_axes(z_axis=n)), 0.003, BLACK)
        fd.paint(Sphere(piv + n * 0.007, 0.008), VIOLET)
        end, n2 = on_helmet(sx * (VIS_PHI - math.radians(6)), (VIS_LO + VIS_HI) / 2 - 0.03, VIS_OFF)
        mp, n3 = on_helmet(sx * (VIS_PHI + PIVOT_PHI) / 2, 1.83, VIS_OFF * 0.7)
        fd.add(Lock([end, mp, piv + n * 0.004], [0.016, 0.014, 0.014], [0.005, 0.005, 0.005], [n2, n3, n], k=0.004), 0.004, BLACK)
    return fd


# ======================================================================================= the pilot's body (rigid with the hull)
P_SH = {"R": v3((-0.19, 0.07, 1.6)), "L": v3((0.19, 0.07, 1.6))}
P_EL = {"R": v3((-0.24, 0.07, 1.41)), "L": v3((0.24, 0.07, 1.41))}
GRIP = {"R": v3((-0.17, -0.13, 1.41)), "L": v3((0.17, -0.13, 1.41))}    # the control grips (he holds them)
STICK_FOOT = {s: GRIP[s] - v3((0, -0.01, 0.1)) for s in GRIP}


def pilot_field():
    """His flight suit: midnight navy (8) with black (5) under-suit panels, a graphite chest plate (0) with a violet
    pinstripe (6), a high collar, small graphite shoulder pads, black gloves round the control grips."""
    fd = Field("Pilot")
    fold = lambda P: F(0.0012) * NOISE(P * F(22)) + F(0.002) * NOISE(P * np.array([6, 6, 12], F))
    fd.add(Ellipsoid((0, 0.08, 1.44), (0.19, 0.125, 0.2), disp=fold, disp_amp=0.003), 0.0, NAVY)          # torso
    fd.add(Ellipsoid((0, 0.07, 1.565), (0.215, 0.13, 0.085)), 0.06, NAVY)                                   # shoulders
    fd.add(RoundBox((0, 0.03, 1.3), (0.17, 0.15, 0.06), 0.05), 0.04, BLACK)                                 # lap (under the dash)
    # the high collar round his neck (open at the front)
    def collar(P):
        q = P - np.array([0.0, 0.02, 0.0], F)
        r = np.sqrt(q[:, 0] ** 2 + (q[:, 1] * F(1.15)) ** 2)
        front = F(1.69) - F(0.04) * smoothstep(0.0, -0.1, q[:, 1])
        return np.maximum(np.abs(r - F(0.095)) - F(0.014), np.maximum(F(1.58) - P[:, 2], P[:, 2] - front))
    fd.add(Func(collar, (-0.2, -0.2, 1.55), (0.2, 0.25, 1.72)), 0.012, NAVY)
    # the chest plate
    fd.add(RoundBox((0, -0.03, 1.49), (0.13, 0.03, 0.09), 0.035, R=euler(-0.25, 0, 0)), 0.02, GRAPH)
    fd.paint(RoundBox((0, -0.08, 1.5), (0.11, 0.06, 0.005), 0.003), VIOLET)
    for side, sx in (("R", -1), ("L", 1)):
        sh, el, gr = P_SH[side], P_EL[side], GRIP[side]
        fd.add(Ellipsoid(sh + v3((sx * 0.02, 0.0, 0.03)), (0.075, 0.08, 0.06)), 0.03, GRAPH)              # shoulder pad
        fd.add(RoundCone(sh, el, 0.062, 0.055), 0.04, NAVY)                                                  # upper arm
        wr = gr + v3((sx * 0.005, 0.07, 0.0))
        fd.add(RoundCone(el, wr, 0.052, 0.044), 0.03, NAVY)                                                  # forearm
        fd.add(RoundCone(lerp(el, wr, 0.75), wr, 0.05, 0.047), 0.01, BLACK)                                 # glove cuff
        fd.add(Ellipsoid(gr + v3((0, 0.012, 0.012)), (0.045, 0.052, 0.05)), 0.02, BLACK)                    # gloved fist on the grip
        for k in range(4):
            fd.add(Sphere(gr + v3((sx * -0.005, -0.03, 0.04 - 0.024 * k)), 0.018), 0.008, BLACK)
    return fd


# ======================================================================================= the cockpit (rigid with the hull)
TUB_C = v3((0.0, 0.03, 1.66))
TUB_H = (0.285, 0.235, 0.4)                # the cockpit's well (half sizes of the cut)
RIM_P = v3((0.0, 0.0, 1.647))              # the rim's plane (raked: lower at the front)
RIM_N = norm(v3((0.0, -0.14, 1.0)))
HOOP_Y = 0.33
HOOP_TOP = 2.3


def rim_z(x, y):
    return RIM_P[2] - (RIM_N[1] * (y - RIM_P[1]) + RIM_N[0] * x) / RIM_N[2]


def hoop_pts(n=11):
    """The roll bar's centre line: from the hull's back corners up over his head."""
    out = []
    for i in range(n):
        t = math.pi * i / (n - 1)
        x = -0.3 * math.cos(t)
        z0 = rim_z(0.3, HOOP_Y) - 0.06
        z = z0 + (HOOP_TOP - z0) * math.sin(t) ** 0.8
        out.append(v3((x * (1.0 - 0.12 * math.sin(t) ** 2), HOOP_Y - 0.02 * math.sin(t), z)))
    return out


def cockpit_field():
    """The seat (black (5), its cushions quilted) with a tall headrest, the dashboard before his belly (gunmetal (9)
    with a black face and white (7) marks; the screen glows: GlowChest), the two control sticks (steel (10), black rubber
    grips (12) with a violet button (6)), the roll bar arching over his head (gunmetal, black grips) with a white stencil."""
    fd = Field("Cockpit")
    quilt = lambda P: F(0.0018) * np.abs(np.sin(P[:, 2] * F(60))) + F(0.0008) * NOISE(P * F(30))
    fd.add(RoundBox((0, 0.215, 1.5), (0.19, 0.035, 0.24), 0.03, R=euler(0.1, 0, 0), disp=quilt, disp_amp=0.002), 0.0, BLACK)   # seat back
    fd.add(RoundBox((0, 0.245, 1.98), (0.13, 0.032, 0.085), 0.03, R=euler(0.06, 0, 0), disp=quilt, disp_amp=0.002), 0.0, BLACK)  # headrest
    for sx in (-1, 1):
        fd.add(RoundCone(v3((sx * 0.08, 0.255, 1.72)), v3((sx * 0.08, 0.258, 1.92)), 0.014), 0.004, GUN)
    fd.add(RoundBox((0, 0.06, 1.265), (0.2, 0.17, 0.03), 0.025), 0.0, BLACK)                                 # seat pan
    # the dashboard
    Rd = euler(0.55, 0, 0)
    fd.add(RoundBox((0, -0.16, 1.33), (0.26, 0.06, 0.085), 0.03, R=Rd), 0.0, GUN)
    fd.add(RoundBox((0, -0.175, 1.385), (0.2, 0.05, 0.012), 0.008, R=Rd), 0.006, BLACK)
    for k in range(5):
        x = -0.15 + 0.075 * k
        fd.paint(RoundBox((x, -0.22, 1.36), (0.012, 0.06, 0.004), 0.002, R=Rd), WHITE)
    # the control sticks
    for side in ("R", "L"):
        gr, ft = GRIP[side], STICK_FOOT[side]
        fd.add(Cylinder(ft - v3((0, 0, 0.01)), 0.03, 0.03, rr=0.008), 0.004, RUBBER)
        fd.add(RoundCone(ft, gr - v3((0, 0, 0.03)), 0.012), 0.004, STEEL)
        fd.add(RoundCone(gr - v3((0, 0, 0.035)), gr + v3((0, 0.0, 0.045)), 0.022, 0.02), 0.006, RUBBER)
        fd.paint(Sphere(gr + v3((0, -0.02, 0.05)), 0.012), VIOLET)
    # the roll bar
    pts = hoop_pts()
    fd.add(Chain(pts, [0.03] * len(pts), k=0.01), 0.0, GUN)
    for i in (2, len(pts) - 3):
        p, q = pts[i], pts[i + 1] if i < len(pts) // 2 else pts[i - 1]
        fd.add(RoundCone(p, lerp(p, q, 0.9), 0.036), 0.004, RUBBER)
    fd.paint(Sphere(pts[len(pts) // 2] + v3((0, 0.02, 0.0)), 0.03), WHITE)
    # a brace from the bar's top down to the headrest
    fd.add(RoundCone(pts[len(pts) // 2], v3((0, 0.27, 2.04)), 0.016), 0.006, GUN)
    return fd


# ======================================================================================= the armour (graphite and navy plates)
def chest_shell(fd):
    """The hull: a broad armoured chest, the cockpit's well cut into it, its rim raked low at the front."""
    fd.add(RoundBox((0, 0.04, 1.31), (0.33, 0.27, 0.13), 0.1), 0.0, GRAPH)
    fd.add(RoundBox((0, 0.04, 1.49), (0.44, 0.34, 0.18), 0.12), 0.08, GRAPH)
    fd.sub(RoundBox(TUB_C, TUB_H, 0.07), 0.02)
    fd.inter(Plane(RIM_P, RIM_N), 0.02)
    # the rim's bead round the well (navy)
    def bead(P):
        q = P - TUB_C.astype(F)
        hx, hy, rc = F(TUB_H[0] + 0.012), F(TUB_H[1] + 0.012), F(0.08)
        dx = np.abs(q[:, 0]) - (hx - rc)
        dy = np.abs(q[:, 1]) - (hy - rc)
        d2 = np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dy, 0) ** 2) + np.minimum(np.maximum(dx, dy), 0) - rc
        dz = (P - RIM_P.astype(F)) @ RIM_N.astype(F)
        return np.sqrt(d2 * d2 + dz * dz) - F(0.03)
    fd.add(Func(bead, (-0.5, -0.4, 1.5), (0.5, 0.45, 1.8)), 0.012, NAVY)
    # the chest plate (navy) on its front, between the light strips' channels
    Rf = euler(0.12, 0, 0)
    fd.add(RoundBox((0, -0.355, 1.42), (0.17, 0.035, 0.13), 0.04, R=Rf), 0.015, NAVY)
    for sx in (-1, 1):
        fd.sub(RoundBox((sx * 0.235, -0.385, 1.42), (0.017, 0.05, 0.12), 0.012, R=Rf), 0.006)       # the strips' channels
    fd.sub(RoundBox((0, -0.39, 1.585), (0.25, 0.05, 0.014), 0.01, R=euler(0.14, 0, 0)), 0.005)       # the channel under the rim
    # side vents
    for sx in (-1, 1):
        for k in range(3):
            fd.sub(RoundBox((sx * 0.45, 0.02 + 0.07 * k, 1.36), (0.03, 0.022, 0.07), 0.01), 0.005)
    # panel lines and stencils
    lo, hi = (-0.6, -0.5, 1.1), (0.6, 0.5, 1.75)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(1.25)) - F(0.004), F(-0.1) - np.abs(P[:, 0]) + F(0.0)), lo, hi), BLACK)
    for sx in (-1, 1):
        fd.paint(Func(lambda P, sx=sx: np.maximum(np.abs(P[:, 0] - F(sx * 0.3)) - F(0.004), F(1.26) - P[:, 2]), lo, hi), BLACK)
    # the unit number "07" on its left breast (white stencil blocks)
    c = v3((0.33, -0.36, 1.5))
    fd.paint(Torus(c + v3((-0.025, 0, 0)), 0.017, 0.0055, R=rot_from_axes(z_axis=(0, 1, 0))), WHITE)
    fd.paint(Chain([c + v3((0.008, 0, 0.019)), c + v3((0.04, 0, 0.019)), c + v3((0.016, 0, -0.021))], [0.0055] * 3), WHITE)
    # the back: plates round the power pack
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(1.2)) - F(0.012), np.abs(P[:, 0]) - F(0.36)), lo, hi), NAVY)


def pelvis_armour(fd):
    """A broad hip ring (graphite), a navy plate before it, two side plates over the hips."""
    fd.add(RoundBox((0, 0.04, 1.03), (0.3, 0.21, 0.06), 0.05), 0.0, GRAPH)
    fd.add(RoundBox((0, -0.16, 0.95), (0.15, 0.035, 0.1), 0.035, R=euler(-0.18, 0, 0)), 0.01, NAVY)
    fd.add(RoundBox((0, 0.23, 0.97), (0.17, 0.03, 0.085), 0.03, R=euler(0.18, 0, 0)), 0.01, GRAPH)
    fd.paint(RoundBox((0, -0.2, 0.95), (0.012, 0.05, 0.08), 0.004), VIOLET)


def pauldron(fd, side):
    """A big angular pauldron over the shoulder (graphite, a navy plate over its crown, a black rim seam, a white
    stencil bar), its edge flared out and down."""
    sx = -1 if side == "R" else 1
    sh = J["shoulder_" + side]
    c = sh + v3((sx * 0.07, 0.0, 0.085))
    R = euler(0, sx * 0.32, 0)
    fd.add(RoundBox(c, (0.2, 0.235, 0.12), 0.1, R=R), 0.0, GRAPH)
    fd.add(RoundBox(c + R @ v3((sx * 0.02, 0, -0.07)), (0.215, 0.25, 0.04), 0.035, R=R), 0.025, GRAPH)
    fd.sub(RoundBox(c + R @ v3((0, 0, -0.14)), (0.17, 0.2, 0.1), 0.06, R=R), 0.015)
    fd.add(RoundBox(c + R @ v3((0, 0, 0.1)), (0.13, 0.17, 0.035), 0.03, R=R), 0.02, NAVY)
    fd.paint(RoundBox(c + R @ v3((0, 0, -0.07)), (0.4, 0.4, 0.006), 0.0, R=R), BLACK)
    fd.paint(RoundBox(c + R @ v3((sx * 0.12, -0.18, 0.04)), (0.035, 0.08, 0.016), 0.005, R=R), WHITE)


def upperarm_armour(fd, side):
    sx = -1 if side == "R" else 1
    sh, el = J["shoulder_" + side], J["elbow_" + side]
    a, b = lerp(sh, el, 0.28), lerp(sh, el, 0.82)
    fd.add(seg_box(a + v3((sx * 0.025, 0, 0)), b + v3((sx * 0.02, 0, 0)), (0.105, 0.11), 0.05, side_ref=(1, 0, 0)), 0.0, NAVY)
    fd.paint(seg_box(lerp(a, b, 0.5), lerp(a, b, 0.5) + norm(b - a) * 0.01, (0.3, 0.3), 0.0), BLACK)


def forearm_armour(fd, side):
    """The forearm housing (navy): a tapered tube cut on a slant at the elbow, a graphite flange at its front, an elbow
    guard (graphite) over the elbow's point, a groove along its outer side for the light strip, panel lines."""
    wr, A, W, M = gframe(side)
    c = gp(side, -0.18, 0, 0)

    def tube(P, side=side):
        u, v, w = _uvw(P, side)
        rad = np.sqrt(v * v + w * w)
        dr = rad - h_rad(u)
        du = np.maximum(h_back(v) - u, u - F(H_FRONT))
        rr = F(0.03)
        qx, qy = dr + rr, du + rr
        return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - rr
    fd.add(Func(tube, c - 0.36, c + 0.36, disp=dent(0.0006, 30), disp_amp=0.0008), 0.0, NAVY)

    def flange(P, side=side):
        u, v, w = _uvw(P, side)
        return np.maximum(np.abs(u - F(H_FRONT - 0.03)) - F(0.022), np.sqrt(v * v + w * w) - (h_rad(u) + F(0.016)))
    fd.add(Func(flange, c - 0.36, c + 0.36), 0.008, GRAPH)
    # the strip's groove (the strip itself glows: GlowArm)
    e = gdir(side, STRIP_PHI)
    fd.sub(RoundCone(gp(side, -0.29, 0, 0) + e * (HR0 + 0.012), gp(side, -0.09, 0, 0) + e * (HR1 + 0.004), 0.021), 0.006)
    # the elbow guard
    el = J["elbow_" + side]
    eg = gp(side, -0.38, 0, 0) - W * 0.0 + gdir(side, 150) * 0.06
    fd.add(Ellipsoid(eg, (0.12, 0.1, 0.09), R=gR(side)), 0.03, GRAPH)
    # panel lines
    lo, hi = c - 0.36, c + 0.36
    fd.paint(Func(lambda P, side=side: np.abs(_uvw(P, side)[0] + F(0.16)) - F(0.004), lo, hi), BLACK)
    fd.paint(Func(lambda P, side=side: np.maximum(np.abs(_uvw(P, side)[0] + F(0.08)) - F(0.012), np.abs(_uvw(P, side)[1]) - F(0.4)), lo, hi), GRAPH)


STRIP_PHI = 62.0            # the forearm's light strip: between the front (thumb side) and the outer side


def thigh_armour(fd, side):
    sx = -1 if side == "R" else 1
    hp_, kn = J["hip_" + side], J["knee_" + side]
    a, b = lerp(hp_, kn, 0.15), lerp(hp_, kn, 0.82)
    off = v3((sx * 0.03, -0.045, 0))
    fd.add(seg_box(a + off, b + off, (0.145, 0.1), 0.06, side_ref=(1, 0, 0)), 0.0, NAVY)
    fd.add(seg_box(a + v3((sx * 0.1, 0.0, 0.02)), lerp(a, b, 0.55) + v3((sx * 0.11, 0.0, 0)), (0.04, 0.12), 0.03, side_ref=(1, 0, 0)), 0.02, GRAPH)
    fd.paint(seg_box(lerp(a, b, 0.55) + off, lerp(a, b, 0.55) + off + norm(b - a) * 0.01, (0.3, 0.3), 0.0), BLACK)


def shin_armour(fd, side):
    """A knee cap (graphite) and a big shin guard (navy, a white stencil bar, a violet pinstripe)."""
    sx = -1 if side == "R" else 1
    kn, an = J["knee_" + side], J["ankle_" + side]
    fd.add(Ellipsoid(kn + v3((0, -0.11, 0.025)), (0.12, 0.075, 0.11)), 0.0, GRAPH)
    a, b = lerp(kn, an, 0.18), lerp(kn, an, 0.9)
    fd.add(seg_box(a + v3((0, -0.03, 0)), b + v3((0, -0.01, 0)), (0.165, 0.15), 0.07, side_ref=(1, 0, 0)), 0.02, NAVY)
    fd.add(seg_box(lerp(a, b, 0.1) + v3((0, -0.14, 0)), lerp(a, b, 0.85) + v3((0, -0.12, 0)), (0.1, 0.035), 0.03, side_ref=(1, 0, 0)), 0.02, NAVY)
    fd.paint(seg_box(lerp(a, b, 0.25) + v3((0, -0.17, 0)), lerp(a, b, 0.5) + v3((0, -0.17, 0)), (0.006, 0.1), 0.0, side_ref=(1, 0, 0)), VIOLET)
    fd.paint(RoundBox(lerp(a, b, 0.72) + v3((sx * 0.11, -0.15, 0)), (0.04, 0.1, 0.012), 0.004), WHITE)


def foot_armour(fd, side):
    """A broad armoured foot (graphite): a wedge with a toe cap (hazard chevrons on its nose), a heel block."""
    sx = -1 if side == "R" else 1
    an = J["ankle_" + side]
    fd.add(RoundBox(an + v3((0, -0.07, -0.135)), (0.15, 0.25, 0.06), 0.045), 0.0, GRAPH)
    fd.add(RoundBox(an + v3((0, -0.2, -0.13)), (0.14, 0.12, 0.05), 0.045, R=euler(0.12, 0, 0)), 0.02, GRAPH)
    fd.add(RoundBox(an + v3((0, -0.06, -0.075)), (0.11, 0.15, 0.05), 0.04, R=euler(0.25, 0, 0)), 0.03, NAVY)
    fd.add(RoundBox(an + v3((0, 0.15, -0.13)), (0.12, 0.06, 0.06), 0.035), 0.02, GRAPH)
    # hazard chevrons on the toe's nose (yellow and black)
    toe = an + v3((0, -0.31, -0.13))
    for k in range(4):
        d = 0.03 * k
        fd.paint(Func(lambda P, d=d, toe=toe: np.maximum(np.abs(np.abs(P[:, 0] - F(toe[0])) * F(0.7) + (P[:, 1] - F(toe[1])) * F(-1.0) - F(d) - F(0.02)) - F(0.0075),
                                                        np.maximum(P[:, 1] - F(toe[1] + 0.07), np.abs(P[:, 2] - F(toe[2])) - F(0.08))),
                      toe - 0.25, toe + 0.25), HAZARD if k % 2 == 0 else BLACK)


def armour_field():
    subs = [("root", Field("ArmourPelvis")), ("chest", Field("ArmourHull"))]
    pelvis_armour(subs[0][1])
    chest_shell(subs[1][1])
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
    return MultiField("Armour", subs)


# ======================================================================================= the frame (gunmetal joints, struts)
def frame_field():
    subs = []
    f = Field("FramePelvis")
    f.add(RoundBox((0, 0.04, 0.97), (0.21, 0.16, 0.1), 0.05), 0.0, GUN)
    for sx in (-1, 1):
        h = J["hip_R" if sx < 0 else "hip_L"]
        f.add(Sphere(h, 0.1), 0.02, GUN)
        f.add(Cylinder(h + v3((sx * 0.02, 0, 0)), 0.085, 0.13, rr=0.02, R=rot_from_axes(z_axis=(1, 0, 0))), 0.01, BLACK)
    subs.append(("root", f))
    f = Field("FrameWaist")
    f.add(Cylinder((0, 0.04, 1.13), 0.15, 0.14, rr=0.02), 0.0, RUBBER)
    for z in (1.085, 1.125, 1.165):
        f.add(Torus((0, 0.04, z), 0.152, 0.018), 0.008, RUBBER)
    subs.append(("spine", f))
    f = Field("FrameHull")
    # the power pack on its back: a gunmetal block, cooling fins, two exhausts, the umbilical socket
    f.add(RoundBox((0, 0.43, 1.42), (0.27, 0.09, 0.19), 0.05), 0.0, GUN)
    for k in range(7):
        x = -0.18 + 0.06 * k
        f.add(RoundBox((x, 0.53, 1.44), (0.01, 0.03, 0.15), 0.006), 0.004, GUN)
    for sx in (-1, 1):
        f.add(Cylinder((sx * 0.18, 0.47, 1.64), 0.045, 0.08, rr=0.012), 0.008, BLACK)
        f.sub(Cylinder((sx * 0.18, 0.47, 1.68), 0.03, 0.06, rr=0.004), 0.004)
    f.add(Cylinder((0.0, 0.52, 1.27), 0.045, 0.05, rr=0.01, R=rot_from_axes(z_axis=(0, 1, 0))), 0.006, BLACK)
    f.paint(Torus((0.0, 0.545, 1.27), 0.03, 0.006, R=rot_from_axes(z_axis=(0, 1, 0))), HAZARD)
    f.paint(RoundBox((0, 0.53, 1.58), (0.2, 0.05, 0.012), 0.004), WHITE)
    subs.append(("chest", f))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        f = Field("FrameShoulder" + side)                     # the shoulder actuator (on the clavicle)
        f.add(Cylinder(sh + v3((-sx * 0.07, 0, 0)), 0.13, 0.16, rr=0.035, R=rot_from_axes(z_axis=(1, 0, 0))), 0.0, GUN)
        f.add(Torus(sh + v3((-sx * 0.0, 0, 0)), 0.11, 0.02, R=rot_from_axes(z_axis=(1, 0, 0))), 0.005, BLACK)
        subs.append(("clavicle." + side, f))
        f = Field("FrameUpper" + side)
        f.add(Sphere(sh, 0.115), 0.0, GUN)
        f.add(RoundCone(sh, el, 0.075, 0.07), 0.02, GUN)
        hz = norm(np.cross(norm(el - sh), norm(wr - el)))
        f.add(Cylinder(el, 0.1, 0.17, rr=0.03, R=rot_from_axes(z_axis=hz)), 0.01, GUN)
        f.add(Cylinder(el, 0.065, 0.2, rr=0.015, R=rot_from_axes(z_axis=hz)), 0.004, BLACK)
        # a piston along its back (steel rod, black cylinder)
        back = norm(v3((0, 1, 0)) - norm(el - sh) * (v3((0, 1, 0)) @ norm(el - sh)))
        p0, p1 = lerp(sh, el, 0.15) + back * 0.09, lerp(sh, el, 0.85) + back * 0.085
        f.add(RoundCone(p0, lerp(p0, p1, 0.55), 0.028), 0.006, BLACK)
        f.add(RoundCone(lerp(p0, p1, 0.5), p1, 0.014), 0.004, STEEL)
        subs.append(("upperarm." + side, f))
        f = Field("FrameFore" + side)                         # the forearm's core, out of the housing's back end
        f.add(RoundCone(gp(side, -0.42, 0, 0), gp(side, -0.25, 0, 0), 0.07), 0.0, GUN)
        subs.append(("forearm." + side, f))
        hp_, kn, an, to = (J[k + "_" + side] for k in ("hip", "knee", "ankle", "toe"))
        f = Field("FrameThigh" + side)
        f.add(RoundCone(hp_, kn, 0.085, 0.08), 0.0, GUN)
        f.add(Cylinder(kn, 0.1, 0.2, rr=0.03, R=rot_from_axes(z_axis=(1, 0, 0))), 0.01, GUN)
        f.add(Cylinder(kn, 0.06, 0.23, rr=0.015, R=rot_from_axes(z_axis=(1, 0, 0))), 0.004, BLACK)
        p0, p1 = lerp(hp_, kn, 0.2) + v3((0, 0.085, 0)), lerp(hp_, kn, 0.85) + v3((0, 0.09, 0))
        f.add(RoundCone(p0, lerp(p0, p1, 0.55), 0.03), 0.006, BLACK)
        f.add(RoundCone(lerp(p0, p1, 0.5), p1, 0.015), 0.004, STEEL)
        subs.append(("thigh." + side, f))
        f = Field("FrameShin" + side)
        f.add(RoundCone(kn, an, 0.075, 0.07), 0.0, GUN)
        f.add(Sphere(an, 0.085), 0.01, GUN)
        p0, p1 = lerp(kn, an, 0.15) + v3((0, 0.11, 0)), lerp(kn, an, 0.85) + v3((0, 0.1, 0))
        f.add(RoundCone(p0, lerp(p0, p1, 0.55), 0.03), 0.006, BLACK)
        f.add(RoundCone(lerp(p0, p1, 0.5), p1, 0.015), 0.004, STEEL)
        subs.append(("shin." + side, f))
        f = Field("FrameFoot" + side)
        f.add(RoundBox(an + v3((0, -0.06, -0.19)), (0.155, 0.265, 0.022), 0.015), 0.0, RUBBER)     # the sole
        f.add(Cylinder(an, 0.07, 0.24, rr=0.02, R=rot_from_axes(z_axis=(1, 0, 0))), 0.0, BLACK)    # the ankle's cross pin
        subs.append(("foot." + side, f))
    return MultiField("Frame", subs)


# ======================================================================================= the fists
def _bx(v, w, u):
    """Half sizes (across, thick, along) of a fist piece scaled as the fist."""
    return (v * FS, w * FS, u * FU)


def fist_hand(fd, side):
    """The fist's body on the hand bone: the wrist cuff (gunmetal), the back-of-hand armour (graphite, a navy plate,
    a black seam), the palm block (gunmetal), the armoured thumb wrapped over the fingers."""
    R = gR(side)
    fd.add(Cylinder(fp(side, 0.018, 0, 0), 0.128 * FS, 0.07 * FU, rr=0.024, R=rot_from_axes(z_axis=gframe(side)[1])), 0.0, GUN)
    fd.add(RoundBox(fp(side, 0.12, 0.0, -0.035), _bx(0.165, 0.075, 0.095), 0.055, R=R), 0.025, GRAPH)
    fd.add(RoundBox(fp(side, 0.13, 0.0, -0.1), _bx(0.12, 0.02, 0.07), 0.022, R=R), 0.014, NAVY)
    fd.add(RoundBox(fp(side, 0.115, 0.0, 0.055), _bx(0.15, 0.06, 0.085), 0.05, R=R), 0.025, GUN)
    th = [fp(side, 0.06, 0.15, 0.03), fp(side, 0.13, 0.19, 0.085), fp(side, 0.21, 0.15, 0.13), fp(side, 0.25, 0.08, 0.14)]
    fd.add(Chain(th, [r * FS for r in (0.052, 0.048, 0.044, 0.04)], k=0.012), 0.025, GRAPH)
    fd.add(Sphere(fp(side, 0.13, 0.215, 0.085), 0.032 * FS), 0.008, GUN)
    fd.paint(RoundBox(fp(side, 0.12, 0.0, -0.13), _bx(0.13, 0.006, 0.08), 0.0, R=R), BLACK)


def fist_fingers(fd, side):
    """The four fingers (one block on the fingers bone): fat curled segments (gunmetal) under armoured backs
    (graphite), the knuckle guard (a graphite bar with four sockets for the glowing knuckle plates)."""
    R = gR(side)
    for i, v in enumerate(FINGER_V):
        s = 0.92 if i == 3 else 1.0
        du = -0.014 if i == 3 else 0.0
        K1 = fp(side, 0.215 + du, v, -0.055)
        K2 = fp(side, 0.29 + du, v, 0.0)
        K3 = fp(side, 0.272 + du, v, 0.085)
        K4 = fp(side, 0.205 + du, v * 0.96, 0.115)
        fd.add(Chain([K1, K2, K3, K4], [r * s * FS for r in (0.046, 0.044, 0.041, 0.036)], k=0.008), 0.008, GUN)
        fd.add(RoundBox(fp(side, 0.275 + du, v, 0.06), _bx(0.032 * s, 0.024, 0.03), 0.018, R=R), 0.01, GRAPH)
    # the knuckle guard across the fingers' front
    fd.add(RoundBox(fp(side, 0.305, 0.0, KN_W), _bx(0.172, 0.068, 0.03), 0.028, R=R), 0.012, GRAPH)
    for v in FINGER_V:
        fd.sub(RoundBox(fp(side, 0.338, v, KN_W), _bx(0.032, 0.048, 0.02), 0.015, R=R), 0.005)
    fd.paint(RoundBox(fp(side, 0.305, 0.0, KN_W - 0.068), _bx(0.2, 0.006, 0.03), 0.0, R=R), WHITE)


def fists_field():
    subs = []
    for side in ("R", "L"):
        f = Field("FistHand" + side)
        fist_hand(f, side)
        subs.append(("hand." + side, f))
        f = Field("FistFingers" + side)
        fist_fingers(f, side)
        subs.append(("fingers." + side, f))
    return MultiField("Fists", subs)


# ======================================================================================= the glows
def knuckle_glow(side):
    """The energy fist's four knuckle plates (their own glowing mesh, on the fingers bone)."""
    fd = Field("Knuckle" + side)
    R = gR(side)
    for v in FINGER_V:
        fd.add(RoundBox(fp(side, 0.338, v, KN_W), _bx(0.029, 0.045, 0.016), 0.015, R=R), 0.0)
    return fd


def arm_glow(side):
    """The forearm's light strip (in its groove along the outer side) and the ring round its housing's front."""
    fd = Field("Arm" + side)
    e = gdir(side, STRIP_PHI)
    fd.add(RoundCone(gp(side, -0.285, 0, 0) + e * (HR0 + 0.006), gp(side, -0.095, 0, 0) + e * (HR1 - 0.002), 0.0135), 0.0)
    wr, A, W, M = gframe(side)
    fd.add(Torus(gp(side, H_FRONT + 0.012, 0, 0), HR1 + 0.004, 0.011, R=rot_from_axes(z_axis=A)), 0.004)
    return fd


def chest_glow():
    """The hull's light strips (two down the chest plate's sides, one under the cockpit's front rim) and the dashboard
    screen."""
    fd = Field("Chest")
    Rf = euler(0.12, 0, 0)
    for sx in (-1, 1):
        fd.add(RoundBox((sx * 0.235, -0.37, 1.42), (0.011, 0.03, 0.11), 0.009, R=Rf), 0.0)
    fd.add(RoundBox((0, -0.375, 1.585), (0.235, 0.03, 0.008), 0.007, R=euler(0.14, 0, 0)), 0.0)
    fd.add(RoundBox((0, -0.172, 1.393), (0.11, 0.03, 0.006), 0.004, R=euler(0.55, 0, 0)), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.24, 1.62)), hr(0.05), 0.55)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.11, -0.15, 1.628)), hr(0.07), 0.7), (hp((sx * 0.176, 0.035, 1.664)), hr(0.06), 0.55)]
    return pts


# ======================================================================================= build config
GLB_NAME = "mech_brawler"
ROOT_NAME = "MechBrawlerHQ"
TEX_PREFIX = "mech"
MAT_NAME = "MechBrawlerMat"
MESH_NAME = "MechBrawler"
BASE_MODULE = "mech_brawler_base"
ANIM_MODULE = "anim_mech_brawler"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Helmet", "Visor", "Pilot", "Cockpit", "Armour", "Frame", "Fists",
         "KnuckleR", "KnuckleL", "ArmR", "ArmL", "Chest"]
REGION_PARTS = ("Skin", "Helmet", "Visor", "Pilot", "Cockpit", "Armour", "Frame", "Fists")
KIT = dict(weave=0.0, black=(0.05, 0.05, 0.058), red=(0.62, 0.2, 0.74), white=(0.9, 0.9, 0.92), olive=MIDNIGHT,
           gunmetal=(0.22, 0.23, 0.26), steel=(0.62, 0.64, 0.68), glass=(0.05, 0.06, 0.09), rubber=(0.07, 0.07, 0.075),
           coyote=(0.92, 0.72, 0.14))
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_PilotSkin", "base": (0.8, 0.56, 0.4), "ruddy": (0.84, 0.46, 0.34), "lips": (0.66, 0.36, 0.3),
                      "brow": ((0.07, 0.05, 0.04), (0.16, 0.11, 0.08)),
                      "extra": ((LASH, (0.07, 0.045, 0.03), 0.5),)}),
    "Hair": ("hair", {"name": "HQ_PilotHair", "base": (0.1, 0.07, 0.05), "hi": (0.27, 0.19, 0.13), "low": (0.04, 0.03, 0.02),
                      "streak": (0.07, 0.05, 0.035), "tint": (0.15, 0.1, 0.07)}),
    "Helmet": ("modern_kit", dict(KIT, name="HQ_MechHelmet", base=GRAPHITE)),
    "Visor": ("modern_kit", dict(KIT, name="HQ_MechHelmet", base=GRAPHITE)),
    "Pilot": ("modern_kit", dict(KIT, name="HQ_MechPilot", base=GRAPHITE, weave=1.0)),
    "Cockpit": ("modern_kit", dict(KIT, name="HQ_MechKit", base=GRAPHITE)),
    "Armour": ("modern_kit", dict(KIT, name="HQ_MechArmour", base=GRAPHITE)),
    "Frame": ("modern_kit", dict(KIT, name="HQ_MechKit", base=GRAPHITE)),
    "Fists": ("modern_kit", dict(KIT, name="HQ_MechArmour", base=GRAPHITE)),
    "KnuckleR": ("glow_ball", {"name": "HQ_MechGlow", "col": VIOLET_GLOW}),
    "KnuckleL": ("glow_ball", {"name": "HQ_MechGlow", "col": VIOLET_GLOW}),
    "ArmR": ("glow_ball", {"name": "HQ_MechGlow", "col": VIOLET_GLOW}),
    "ArmL": ("glow_ball", {"name": "HQ_MechGlow", "col": VIOLET_GLOW}),
    "Chest": ("glow_ball", {"name": "HQ_MechGlow", "col": VIOLET_GLOW}),
}
_G = (VIOLET_GLOW, 1.25, 0.5)
GLOW = {"KnuckleR": _G, "KnuckleL": _G, "ArmR": _G, "ArmL": _G, "Chest": _G}
LOW_TARGETS = {"Skin": 2600, "Teeth": 80, "Hair": 380, "Helmet": 1400, "Visor": 500, "Pilot": 1300, "Cockpit": 1500,
               "Armour": 7600, "Frame": 3600, "Fists": 3800, "KnuckleR": 120, "KnuckleL": 120, "ArmR": 140, "ArmL": 140,
               "Chest": 120}
AO_EXCLUDE = ["Visor", "Helmet"]


def prop_bones():
    """The fingers' blocks (children of the hands, hinged across the knuckles; their tails toward the knuckle plates)."""
    out = []
    for side in ("R", "L"):
        h = finger_hinge(side)
        out.append(("fingers." + side, h, h + gframe(side)[1] * 0.12, "hand." + side))
    return out


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Helmet": ("rigid", "head"),
        "Visor": ("rigid", "head"), "Pilot": ("rigid", "chest"), "Cockpit": ("rigid", "chest"),
        "Armour": ("custom", island_weights(armour_field)),
        "Frame": ("custom", island_weights(frame_field)),
        "Fists": ("custom", island_weights(fists_field)),
        "KnuckleR": ("rigid", "fingers.R"), "KnuckleL": ("rigid", "fingers.L"),
        "ArmR": ("rigid", "forearm.R"), "ArmL": ("rigid", "forearm.L"), "Chest": ("rigid", "chest"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < -0.05:
        return 2.2
    if part in ("Skin", "Teeth", "Hair"):
        return 1.2
    if part == "Pilot":
        return 0.7
    if part in ("Helmet", "Visor"):
        return 1.4
    if part == "Frame":
        return 0.7
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.0026 if fine else 0.004),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0011),
        ("Hair", hair_field(), 0.0022 if fine else 0.0032),
        ("Helmet", helmet_field(), 0.0022 if fine else 0.0032),
        ("Visor", visor_field(), 0.0018 if fine else 0.0026),
        ("Pilot", pilot_field(), 0.0035 if fine else 0.005),
        ("Cockpit", cockpit_field(), 0.003 if fine else 0.0045),
        ("Armour", armour_field(), 0.0042 if fine else 0.006),
        ("Frame", frame_field(), 0.0038 if fine else 0.0055),
        ("Fists", fists_field(), 0.0032 if fine else 0.0048),
        ("KnuckleR", knuckle_glow("R"), 0.003),
        ("KnuckleL", knuckle_glow("L"), 0.003),
        ("ArmR", arm_glow("R"), 0.003),
        ("ArmL", arm_glow("L"), 0.003),
        ("Chest", chest_glow(), 0.003),
    ]
