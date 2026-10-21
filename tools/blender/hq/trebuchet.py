"""The Trebuchet (HQ tower, Medieval Age): a counterweight trebuchet on its timber frame, and the master engineer who
works it. Rest pose: he stands in an A-pose facing -Y (the way it shoots), feet at z = 0, the engine on his left (+X); it
is cocked (the long end of its arm hauled down at the back and hooked to the trigger, the counterweight up in front, the
stone in the sling's pouch lying in the trough under the frame).

Him: the Bronze Age engineer's broad body and face (torsion.py: big, barrel-chested, a hooked nose, bushy brows), grown
old: a short grey beard, grey brows; a red wool hood (a chaperon) over his head and shoulders, its cape cut in dags, its
long tail hanging down his back; a brown wool tunic to the knee with a green border, a leather apron over it from his
chest to his knees with a pocket of tools, a belt with a pouch, leather wrist wraps, grey hose and leather boots. A
wooden mallet with iron bands, rigid in his right fist.

The engine: two long sills on the ground joined by cross beams; on each sill an A-frame trestle (two raking legs and a
post, a cross-tie, braces) carrying the iron-bound axle; the throwing arm on the axle (thick at the axle, tapering to its
long end, iron bands, an iron cap and the release prong at the tip); at its short end, on a hinge pin, the counterweight:
a great box of planks bound with iron, heaped with stones; the sling: two ropes from the tip to a leather pouch with the
stone, lying in a plank trough between the sills; at the back the windlass (rope on the drum, a spoked wheel on his side)
and the trigger post, its iron hook over a ring on the arm's tip, held shut by a pin he knocks out with the mallet.
Behind him a heap of stone balls on a straw mat.

Painted labels on the engine (material `siege`, iron fittings): 0 wood with the grain along Y, 10 along X, 11 along Z;
5 red paint; 7 blue paint; 6 iron; 8 rope; 9 leather."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import torsion as _t
from torsion import (J, SKIN, NAIL, LIP, MOUTH, BROW, PAINT, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD,
                     EYE_R, eye_c, smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, traps, neck_prim,
                     deltoid, upper_arm, eyes_field, teeth_field, skull, _forearm, mallet_frame, MALLET_L, MALLET_BUTT,
                     MALLET_HEAD, tbeam, GRAIN, box, stone_ball, torso_prims, body_parts, head_hull, TORSO, TORSO_Z,
                     torso_bones)

GX, GZ, RED, BLUE, IRON, ROPE, HIDE = 10, 11, 5, 7, 6, 8, 9          # engine labels (wood grain Y is 0)


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


# ======================================================================================= short grey beard
def beard_field():
    """A short grey beard trimmed close round his jaw and chin, a grey moustache."""
    fd = Field("Beard")
    hull = head_hull()
    hairs = lambda P: F(0.0018) * NOISE(P * np.array([80, 80, 28], F)) + F(0.001) * NOISE(P * F(160))
    def mask(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        top = F(1.556) + F(0.08) * smoothstep(0.05, 0.15, ax)
        lips = (x / F(0.066)) ** 2 + ((y + F(0.18)) / F(0.07)) ** 2 + ((z - F(1.545)) / F(0.026)) ** 2 - F(1.0)
        return np.maximum(np.maximum(np.maximum(z - top, y - F(0.06)), -lips * F(0.03)), F(1.43) - z)
    fd.add(Inter(Shell(hull, 0.005, 0.016, pad=0.06, disp=hairs, disp_amp=0.003), Func(mask, HEAD_C - 0.45, HEAD_C + 0.3), 0.005), 0.0)
    fd.add(Ellipsoid(hp((0.0, -0.152, 1.48)), v3((0.075, 0.05, 0.055)) * HS, disp=hairs, disp_amp=0.003), hr(0.02))
    strands = lambda P: F(0.002) * NOISE(P * np.array([80, 80, 30], F))
    for sx in (-1, 1):
        pts = [hp((sx * 0.006, -0.23, 1.586)), hp((sx * 0.044, -0.215, 1.572)), hp((sx * 0.068, -0.194, 1.548))]
        fd.add(Lock(pts, [hr(0.014), hr(0.017), hr(0.009)], [hr(0.01), hr(0.011), hr(0.006)], [norm(v3((sx * 0.3, -1, 0.15)))] * 3,
                    k=hr(0.006), disp=strands, disp_amp=0.003), hr(0.006))
    return fd


# ======================================================================================= the chaperon (hood, dagged cape, tail)
def hood_hull():
    b = Field("HoodHull")
    b.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    b.add(Ellipsoid(hp((0, 0.02, 1.79)), v3((0.165, 0.175, 0.12)) * HS), 0.08)
    for sx in (-1, 1):
        b.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.029, 0.052, 0.066)) * HS), 0.03)
        b.add(Sphere(hp((sx * 0.13, -0.045, 1.556)), hr(0.052)), 0.05)
    b.add(neck_prim(), 0.06)
    return b


def cape_hull():
    b = Field("CapeHull")
    b.add(Ellipsoid((0, 0.06, 1.24), (0.3, 0.24, 0.26), R=euler(-0.1, 0, 0)), 0.0)
    b.add(traps(), 0.06)
    b.add(neck_prim(), 0.05)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.06)
    return b


def hood_open(P):
    """< 0 inside the face opening (front only): from the brow to under the chin, cheek to cheek."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    e = np.sqrt((x / F(0.135)) ** 2 + ((z - F(1.64)) / F(0.19)) ** 2) - F(1.0)
    return np.maximum(e * F(0.12), y + F(0.02))


def cape_hem(P):
    """The cape's dagged hem: a row of rounded tongues round his shoulders."""
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.06)))
    dags = F(0.04) * np.clip(np.sin(a * F(14)), 0, 1) ** 0.5
    return F(1.2) - F(0.05) * np.abs(np.sin(a)) - dags


TAIL = [v3((0.0, 0.2, 1.86)), v3((0.0, 0.27, 1.72)), v3((0.01, 0.3, 1.5)), v3((0.03, 0.31, 1.3)), v3((0.05, 0.32, 1.12))]


def hood_field():
    """Red wool (label 0) lined with green at the face (5): the hood, its dagged shoulder cape, the long tail down his
    back."""
    fd = Field("Hood")
    hh = hood_hull()
    ch = cape_hull()
    nap = lambda P: F(0.0015) * NOISE(P * F(30))
    lo, hi = v3((-0.6, -0.5, 0.9)), v3((0.6, 0.6, 2.1))
    shape = Field("HoodShape")
    shape.add(Shell(hh, 0.02, 0.016, pad=0.08, disp=nap, disp_amp=0.002), 0.0)
    shape.add(Inter(Shell(ch, 0.05, 0.014, pad=0.12, disp=nap, disp_amp=0.002), Func(lambda P: P[:, 2] - F(1.6), lo, hi), 0.02), 0.03)
    def keep(P):
        return np.maximum(-hood_open(P), cape_hem(P) - P[:, 2])
    fd.add(Inter(Func(lambda P: shape.eval(P), lo, hi), Func(keep, lo, hi), 0.004), 0.0)
    def rim(P):
        return np.maximum(np.abs(hood_open(P) + F(0.008)) - F(0.01), hinv(P)[:, 1] - F(0.05))
    fd.add(Inter(Shell(hh, 0.026, 0.018, pad=0.08), Func(rim, lo, hi), 0.003), 0.004, 5)
    fd.add(Lock(TAIL, [0.05, 0.045, 0.04, 0.036, 0.03], [0.02, 0.018, 0.016, 0.014, 0.012], [v3((0, 1, 0.1))] * 5, k=0.012,
                disp=nap, disp_amp=0.002), 0.02)
    return fd


# ======================================================================================= tunic, apron, leather, hose
def tunic_base():
    b = Field("TunicBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        b.add(deltoid(side), 0.055)
        b.add(upper_arm(side), 0.05)
        b.add(RoundCone(J["elbow_" + side], J["wrist_" + side], 0.08, 0.06), 0.035)
        b.add(Sphere(J["elbow_" + side] + v3((0, 0.025, 0)), 0.06), 0.028)
    b.add(RoundCone((0, 0.03, 0.92), (0, 0.03, 0.45), 0.26, 0.33), 0.09)
    return b


def _cuff(P, side):
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    sx = -1 if side == "R" else 1
    return np.where(P[:, 0] * F(sx) > F(0.45), (P - wr.astype(F)) @ ax.astype(F) + F(0.03), F(-1.0))


def tunic_hem(P):
    a = np.arctan2(P[:, 0], -(P[:, 1] - F(0.03)))
    return F(0.48) + F(0.015) * np.clip(np.cos(a), 0, 1) + F(0.006) * NOISE(P * F(8))


def tunic_field():
    """Brown wool (label 0) to the knee with long sleeves; a green border (5) round the hem and the cuffs."""
    fd = Field("Tunic")
    base = tunic_base()
    folds = lambda P: F(0.005) * np.sin(np.arctan2(P[:, 0], -(P[:, 1] - F(0.03))) * F(13) + F(0.7) * NOISE(P * F(3))) \
        * smoothstep(0.9, 0.7, P[:, 2]) + F(0.0015) * NOISE(P * F(25))
    def keep(P):
        k = np.maximum(tunic_hem(P) - P[:, 2], _t._neck_cut(P))
        return np.maximum(np.maximum(k, _cuff(P, "R")), _cuff(P, "L"))
    fd.add(Inter(Shell(base, 0.024, 0.022, pad=0.1, disp=folds, disp_amp=0.006), Func(keep, (-1, -1, 0.3), (1, 1, 1.6)), 0.005), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - (tunic_hem(P) + F(0.04)), (-1, -1, 0.3), (1, 1, 0.7)), 5)
    for side in ("R", "L"):
        fd.paint(Func(lambda P, side=side: np.where(_cuff(P, side) > F(-0.5), np.abs(_cuff(P, side) + F(0.022)) - F(0.022), F(1.0)),
                      (-1, -1, 0.5), (1, 1, 1.4)), 5)
    return fd


BELT_Z = 0.97


def apron_field():
    """A leather apron (label 0) from his chest to his knees, its bib held by a strap round his neck, a pocket on its
    front with a hammer's haft and a pair of tongs in it (6: iron), scorch marks (5)."""
    fd = Field("Apron")
    base = tunic_base()
    def keep(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        half = F(0.2) + F(0.05) * smoothstep(1.05, 0.8, z)
        return np.maximum(np.maximum(np.abs(x) - half, y + F(0.02)), np.maximum(F(0.5) - z, z - F(1.3)))
    stiff = lambda P: F(0.0015) * NOISE(P * F(20))
    fd.add(Inter(Shell(base, 0.058, 0.012, pad=0.1, disp=stiff, disp_amp=0.002), Func(keep, (-0.6, -0.8, 0.4), (0.6, 0.2, 1.4)), 0.004), 0.0)
    # the neck strap
    pts = [v3((-0.14, -0.21, 1.3)), v3((-0.15, -0.08, 1.46)), v3((0.0, 0.1, 1.5)), v3((0.15, -0.08, 1.46)), v3((0.14, -0.21, 1.3))]
    fd.add(Chain(pts, [0.012] * 5, k=0.004), 0.004)
    # the pocket, with tools standing in it
    outer = Func(lambda P: base.eval(P, margin=0.1) - F(0.07), (-0.6, -0.8, 0.4), (0.6, 0.2, 1.4))
    h, ok = ray_hit(outer, [v3((0.06, -0.8, 0.78))], [v3((0, 1, 0))], tmax=0.9)
    pc = h[0] if ok[0] else v3((0.06, -0.3, 0.78))
    fd.add(RoundBox(pc + v3((0, -0.004, 0)), (0.085, 0.012, 0.07), 0.01), 0.004)
    fd.add(Chain([pc + v3((-0.035, -0.01, 0.0)), pc + v3((-0.04, -0.012, 0.16))], [0.009, 0.008], k=0.002), 0.003)
    fd.add(RoundBox(pc + v3((-0.04, -0.012, 0.17)), (0.035, 0.014, 0.014), 0.005), 0.003, 6)
    for dx in (0.02, 0.04):
        fd.add(Chain([pc + v3((dx, -0.008, 0.0)), pc + v3((dx + 0.004, -0.01, 0.13))], [0.005, 0.005], k=0.002), 0.003, 6)
    rs = np.random.RandomState(4)
    for k in range(4):
        fd.paint(Sphere(pc + v3((rs.uniform(-0.15, 0.15), -0.01, rs.uniform(-0.2, 0.3))), rs.uniform(0.02, 0.035)), 5)
    return fd


def leather_field():
    """The belt (label 0) with an iron buckle (6), a pouch at his left hip, wrist wraps, boots to the ankle with thick
    soles."""
    fd = Field("Leather")
    bb = _t.belt_base()
    fd.add(Inter(Shell(bb, 0.07, 0.022, pad=0.1), Func(lambda P: np.abs(P[:, 2] - F(BELT_Z)) - F(0.026), (-1, -1, 0.8), (1, 1, 1.2)), 0.005), 0.0)
    pp = v3((0.27, -0.12, BELT_Z - 0.09))
    fd.add(RoundBox(pp, (0.055, 0.03, 0.06), 0.02, R=euler(0, 0, 0.5)), 0.004)
    fd.add(RoundBox(pp + v3((0, 0, 0.045)), (0.058, 0.034, 0.018), 0.012, R=euler(0, 0, 0.5)), 0.003)
    for side in ("L", "R"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = lerp(el, wr, 0.86)
        fd.add(Inter(Shell(_forearm(side), 0.03, 0.014, pad=0.06), Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.045), c - 0.25, c + 0.25), 0.004), 0.0)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an, kn = J["ankle_" + side], J["knee_" + side]
        ft = Field("BootHull")
        foot(ft, side)
        ft.add(RoundCone(kn, an, 0.088, 0.058), 0.03)
        fd.add(Inter(Shell(ft, 0.012, 0.012, pad=0.06, disp=lambda P: F(0.0015) * NOISE(P * F(26)), disp_amp=0.002),
                     Func(lambda P: P[:, 2] - F(0.2), an - v3((0.3, 0.4, 0.3)), an + v3((0.3, 0.3, 0.3))), 0.004), 0.0)
        Rz = euler(0, 0, sx * 0.12)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(RoundBox(an + fwd * 0.075 + v3((0, 0, -0.098)), (0.08, 0.16, 0.014), 0.01, R=Rz), 0.006)
    return fd


def hose_field():
    """Grey wool hose from under the tunic into the boots (label 0)."""
    fd = Field("Hose")
    for side in ("R", "L"):
        hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        lb = Field("Leg")
        lb.add(RoundCone(hip, kn, 0.14, 0.092), 0.0)
        lb.add(Sphere(kn + v3((0, -0.03, 0.0)), 0.072), 0.038)
        lb.add(RoundCone(kn, an, 0.088, 0.058), 0.038)
        lb.add(Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.1, 0.097, 0.145), R=rot_from_axes(z_axis=an - kn)), 0.043)
        fd.add(Inter(Shell(lb, 0.006, 0.008, pad=0.06), Func(lambda P: np.maximum(F(0.15) - P[:, 2], P[:, 2] - F(0.62)), kn - 0.5, kn + 0.4), 0.004), 0.004)
    return fd


def mallet_field():
    """Hard wood (label 0), two iron bands round the head and an iron collar (6), a leather grip (9)."""
    fd = Field("Mallet")
    G, T, Fv = mallet_frame()
    fd.add(RoundCone(G - T * MALLET_BUTT, G + T * (MALLET_L - 0.04), 0.019, 0.016, disp=GRAIN, disp_amp=0.002), 0.0)
    fd.add(Sphere(G - T * MALLET_BUTT, 0.022), 0.006)
    hc = G + T * MALLET_L
    r, hl = MALLET_HEAD
    fd.add(Cylinder(hc, r, hl * 2, rr=0.012, R=rot_from_axes(z_axis=Fv), disp=GRAIN, disp_amp=0.002), 0.008, GX)
    for s in (-1, 1):
        fd.add(Cylinder(hc + Fv * s * (hl - 0.022), r + 0.004, 0.018, rr=0.004, R=rot_from_axes(z_axis=Fv)), 0.002, IRON)
    fd.add(Cylinder(hc - T * (r + 0.004), 0.025, 0.02, rr=0.005, R=rot_from_axes(z_axis=T)), 0.006, IRON)
    for k in range(6):
        fd.add(Torus(G + T * (-0.05 + 0.02 * k), 0.019, 0.0045, R=rot_from_axes(z_axis=T)), 0.002, HIDE)
    return fd


# ======================================================================================= the engine (layout)
MX = 1.05                     # the frame's centre line (x); it shoots toward -Y
SW = 0.3                      # the sills' centre offset from MX
SILL_HW, SILL_HH = 0.062, 0.075
LEG_Y = 0.45                  # the trestle's raking legs' feet on the sills (y = +-)
TIE_Y = 0.32                  # the trestle's cross-tie's half length
Y0, Y1 = -0.75, 1.05          # the sills' front and back ends
AXLE = v3((MX, 0.0, 1.3))     # the arm turns about it
LONG = 1.5                    # axle -> the release prong at the long end's tip
SHORT = 0.4                   # axle -> the counterweight's hinge pin at the short end
COCK = math.radians(-40.0)    # the long end's angle from level, toward the back (+Y): hauled down
W0, D0, W1, D1 = 0.05, 0.068, 0.034, 0.04       # the arm's half width / half depth at the axle and at the long tip
BOX_HW, BOX_HD, BOX_HH = 0.2, 0.16, 0.15        # the counterweight box's half sizes (x, y, z)
HANG = 0.16                   # hinge pin -> the box's top (its heaped stones clear of the arm)
BALL_R = 0.075
SLING_L = 0.74                # prong -> the stone's centre
TROUGH_Z = 0.13               # the trough's floor
DRUM = v3((MX, 0.86, 0.2))                         # (low: the sling passes over it)
DRUM_R = 0.065
WHEEL_X = MX - SW - 0.13      # the spoked wheel's plane (his side)
WHEEL_R = 0.16
TRIG = v3((MX, Y1 - 0.03, 0.0))   # the trigger post's foot (its top under the ring)
PIN_TOP = v3((MX - SW + 0.06, Y1 - 0.03, 0.44))     # the trigger pin's head, on the trigger bar (he knocks it down from his side)
PILE = v3((-0.15, 0.62, 0.0))                       # the heap of stone balls (behind him at the wheel, clear of his feet)
YAW_PIVOT = (0.62, 0.14, 0.0)                       # the tower turns about this point (keeps it all on the base)


def arm_dir(a):
    return v3((0.0, math.cos(a), math.sin(a)))


def arm_up(a):
    return v3((0.0, -math.sin(a), math.cos(a)))


def arm_pt(s, a=COCK, up=0.0):
    """A point along the arm (s > 0 toward the long end) at arm angle a, `up` across it."""
    return AXLE + arm_dir(a) * s + arm_up(a) * up


def arm_depth(s):
    t = max(0.0, min(1.0, s / LONG)) if s > 0 else 0.0
    return D0 + (D1 - D0) * t


def tip_pt(a=COCK):
    return arm_pt(LONG, a)


def hook_pt(a=COCK):
    """The release prong on the long end's top (the sling's loop rides on it)."""
    return arm_pt(LONG - 0.03, a, arm_depth(LONG) + 0.014)


def hinge_pt(a=COCK):
    return arm_pt(-SHORT, a)


def box_c(a=COCK):
    """The counterweight box hangs plumb from the hinge pin."""
    return hinge_pt(a) - v3((0, 0, HANG + BOX_HH))


def sling_rest():
    """The stone's centre in the pouch at rest: in the trough, toward the front, a sling's length from the prong."""
    H = hook_pt(COCK)
    dz = H[2] - (TROUGH_Z + 0.012 + BALL_R)
    dy = math.sqrt(max(SLING_L ** 2 - dz ** 2, 0.0))
    return v3((MX, H[1] - dy, TROUGH_Z + 0.012 + BALL_R))


SLING_REST = sling_rest()


def ring_pt(a=COCK):
    """The ring under the arm near its tip: the windlass rope and the trigger's hook take it."""
    return arm_pt(LONG - 0.12, a, -arm_depth(LONG - 0.12) - 0.016)


def haul_start():
    d = norm(ring_pt(COCK) - DRUM)
    return DRUM + d * (DRUM_R + 0.01)


PEG_L = 0.1                   # the grip pegs stick out from the spokes' ends toward him (-X)


def spoke_end(phi, k):
    """The k-th spoke's end on the spoked wheel at wheel angle phi (radians, about +X: 0 = toward +Y, pi/2 = up)."""
    a = phi + k * math.pi / 2
    return v3((WHEEL_X, DRUM[1] + WHEEL_R * math.cos(a), DRUM[2] + WHEEL_R * math.sin(a)))


def wheel_handle(phi, k):
    """The middle of the k-th spoke's grip peg (where his fist takes it)."""
    return spoke_end(phi, k) - v3((PEG_L * 0.55, 0.0, 0.0))


def pile_balls():
    m = 0.012
    out = []
    for k in range(3):
        a = math.radians(30 + 120 * k)
        out.append((PILE + v3((math.cos(a) * 0.084, math.sin(a) * 0.084, m + BALL_R)), "props"))
    out.append((PILE + v3((0, 0, m + BALL_R + math.sqrt((2 * BALL_R) ** 2 - 0.084 ** 2) + 0.009)), "carry"))
    out.append((PILE + v3((-0.15, -0.1, BALL_R)), "props"))
    return out


CARRY_C = pile_balls()[3][0]
TRIG_P = v3((MX, Y1 - 0.03, 0.28))        # the hook's pivot on the trigger post's top (under the arm's ring)


def hook_tip():
    """Where the hook's bill passes through the ring (cocked)."""
    return ring_pt(COCK)


# ======================================================================================= the engine (sculpt)
def frame_field():
    """Sills, cross beams, the trestles (raking legs, posts, cross-ties, braces), the axle's iron bearings, the plank
    trough the sling lies in, the windlass's bearing posts, the trigger post and its pin."""
    fd = Field("Frame")
    zb = SILL_HH
    top = 2 * SILL_HH
    for sx in (-1, 1):
        x = MX + sx * SW
        fd.add(box((x, (Y0 + Y1) / 2, zb), (SILL_HW, (Y1 - Y0) / 2, SILL_HH)), 0.0, 0)
        for ye, sgn in ((Y0, -1), (Y1, 1)):                                   # iron shoes on the sill ends
            fd.add(Inter(RoundBox(v3((x, ye - sgn * 0.03, zb)), (SILL_HW + 0.006, 0.04, SILL_HH + 0.006), 0.012),
                         Func(lambda P, ye=ye, sgn=sgn: (F(ye) - P[:, 1]) * F(sgn) - F(0.075), (x - 0.12, ye - 0.12, -0.05), (x + 0.12, ye + 0.12, 0.25)), 0.002), 0.003, IRON)
        fd.paint(Func(lambda P, x=x, sx=sx: np.maximum(np.maximum(np.abs(P[:, 2] - F(zb)) - F(0.035), (F(x) - P[:, 0]) * F(sx) + F(0.02)),
                                                     np.abs(P[:, 1] - F((Y0 + Y1) / 2)) - F((Y1 - Y0) / 2 - 0.1)),
                      (x - 0.12, Y0, -0.05), (x + 0.12, Y1, 0.25)), BLUE)
        # the trestle: two raking legs, the post, a cross-tie, two braces from the legs to the post
        apex = v3((x, 0.0, AXLE[2] - 0.07))
        for yl in (-LEG_Y, LEG_Y):
            fd.add(tbeam((x, yl, top - 0.02), apex + v3((0, 0.05 * np.sign(yl), 0)), (1, 0, 0), 0.05, 0.05, 0.044, 0.044, disp=GRAIN, disp_amp=0.002), 0.012, GZ)
        fd.add(box((x, 0.0, (top + AXLE[2] - 0.05) / 2), (0.052, 0.052, (AXLE[2] - 0.05 - top) / 2 + 0.01)), 0.01, GZ)
        fd.add(box((x, 0.0, 0.62), (0.045, TIE_Y, 0.04)), 0.01, 0)
        for s in (-1, 1):
            fd.add(tbeam((x, s * (TIE_Y - 0.08), 0.62), (x, s * 0.05, 1.0), (1, 0, 0), 0.034, 0.034, disp=GRAIN, disp_amp=0.002), 0.01, GZ)
        # the axle's bearing on the trestle's top: an iron cap over the axle
        fd.add(RoundBox(v3((x, 0.0, AXLE[2] - 0.05)), (0.07, 0.08, 0.03), 0.01), 0.004, IRON)
        fd.add(Inter(Shell(Cylinder(AXLE + v3((sx * SW, 0, 0)), 0.05, 0.12, R=rot_from_axes(z_axis=(1, 0, 0))), 0.01, 0.014, pad=0.04),
                     Func(lambda P: F(AXLE[2] - 0.03) - P[:, 2], AXLE - 0.5, AXLE + 0.5), 0.002), 0.004, IRON)
        for yb in (-LEG_Y, LEG_Y, DRUM[1] - 0.12):
            fd.add(Inter(Shell(RoundBox(v3((x, yb, zb)), (SILL_HW, 0.2, SILL_HH), 0.012), 0.005, 0.008, pad=0.05),
                         Func(lambda P, yb=yb: np.abs(P[:, 1] - F(yb)) - F(0.022), (x - 0.12, yb - 0.1, -0.05), (x + 0.12, yb + 0.1, 0.3)), 0.002), 0.003, IRON)
    for yc in (Y0 + 0.07, 0.0, Y1 - 0.06):                                    # cross beams
        fd.add(box((MX, yc, top - 0.04), (SW - 0.03, 0.05, 0.045)), 0.006, GX)
    # the trough: a plank channel between the sills, from the middle to the front, its floor at TROUGH_Z
    ty0, ty1 = Y0 + 0.12, 0.62
    fd.add(box((MX, (ty0 + ty1) / 2, TROUGH_Z - 0.014), (0.13, (ty1 - ty0) / 2, 0.014)), 0.004, 0)
    for s in (-1, 1):
        fd.add(box((MX + s * 0.14, (ty0 + ty1) / 2, TROUGH_Z + 0.03), (0.012, (ty1 - ty0) / 2, 0.045)), 0.004, 0)
    # the windlass's bearing posts, the trigger post
    for sx in (-1, 1):
        fd.add(box((MX + sx * SW, DRUM[1], (top + DRUM[2] + 0.07) / 2), (0.058, 0.064, (DRUM[2] + 0.07 - top) / 2 + 0.01)), 0.008, GZ)
        fd.add(RoundBox(v3((MX + sx * SW, DRUM[1], DRUM[2] + 0.07)), (0.064, 0.068, 0.012), 0.005), 0.003, IRON)
    fd.add(box((MX, TRIG[1], (top + TRIG_P[2] + 0.02) / 2), (0.05, 0.05, (TRIG_P[2] + 0.02 - top) / 2 + 0.01)), 0.008, GZ)
    fd.add(box((MX - SW / 2, TRIG[1], 0.27), (SW / 2 + 0.03, 0.035, 0.03)), 0.006, GX)       # (its top level with the post's)
    fd.add(box((MX - SW, TRIG[1], (top + 0.24) / 2), (0.04, 0.035, (0.24 - top) / 2 + 0.01)), 0.006, GZ)
    fd.add(Cylinder(PIN_TOP - v3((0, 0, 0.08)), 0.011, 0.16, rr=0.003), 0.003, IRON)
    fd.add(Ellipsoid(PIN_TOP, (0.03, 0.03, 0.017)), 0.004, IRON)
    return fd


def arm_field():
    """The throwing arm (cocked): a tapered beam on the axle (thickest there), iron bands, the axle's hub, the hinge pin at
    the short end, an iron cap and the release prong at the long end's tip, the ring underneath near the tip."""
    fd = Field("Arm")
    d, up = arm_dir(COCK), arm_up(COCK)
    a0, a1 = arm_pt(-SHORT - 0.06), arm_pt(LONG + 0.02)
    fd.add(tbeam(a0, AXLE, up, W0 * 0.9, D0 * 0.9, W0, D0, r=0.016, disp=GRAIN, disp_amp=0.002), 0.0, 0)
    fd.add(tbeam(AXLE, a1, up, W0, D0, W1, D1, r=0.016, disp=GRAIN, disp_amp=0.002), 0.01, 0)
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    fd.add(Cylinder(AXLE, 0.055, 2 * SW + 0.16, rr=0.01, R=Rx, disp=GRAIN, disp_amp=0.002), 0.006, GX)    # the axle
    for sx in (-1, 1):
        fd.add(Cylinder(AXLE + v3((sx * (SW + 0.085), 0, 0)), 0.062, 0.025, rr=0.006, R=Rx), 0.003, IRON)
    def band(s0, w, extra=0.008):
        c = arm_pt(s0)
        dd = d.astype(F)
        lo_s, hi_s = (a0, AXLE) if s0 < 0 else (AXLE, a1)
        ww0, dd0, ww1, dd1 = (W0 * 0.9, D0 * 0.9, W0, D0) if s0 < 0 else (W0, D0, W1, D1)
        fd.add(Inter(tbeam(lo_s, hi_s, up, ww0 + extra, dd0 + extra, ww1 + extra, dd1 + extra, r=0.018),
                     Func(lambda P: np.abs((P - c.astype(F)) @ dd) - F(w), c - 0.25, c + 0.25), 0.002), 0.003, IRON)
    for s in (-SHORT + 0.06, -0.12, 0.13, 0.5, 0.95, LONG - 0.04):
        band(s, 0.02 if abs(s - (LONG - 0.04)) > 0.01 else 0.045)
    # the hinge pin through the short end (the counterweight's straps hang from its ends)
    hc = hinge_pt(COCK)
    fd.add(Cylinder(hc, 0.016, 2 * BOX_HW + 0.04, rr=0.004, R=Rx), 0.004, IRON)
    for sx in (-1, 1):
        fd.add(Sphere(hc + v3((sx * (BOX_HW + 0.024), 0, 0)), 0.022), 0.004, IRON)
    # the prong and the ring
    h0 = arm_pt(LONG - 0.04, up=arm_depth(LONG) - 0.004)
    fd.add(Chain([h0, h0 + up * 0.032 + d * 0.012, h0 + up * 0.046 - d * 0.014], [0.011, 0.009, 0.007], k=0.004), 0.004, IRON)
    rp = ring_pt(COCK)
    fd.add(Torus(rp, 0.022, 0.0065, R=rot_from_axes(z_axis=(0, 1, 0))), 0.003, IRON)
    fd.add(RoundBox(arm_pt(LONG - 0.12, up=-arm_depth(LONG - 0.12) + 0.004), (0.04, 0.014, 0.012), 0.004, R=rot_from_axes(z_axis=up, y_axis=d)), 0.004, IRON)
    return fd


def weight_field():
    """The counterweight: a box of planks (wood, grain across: 10) bound with iron straps and corners (6), heaped with
    rough stones; two iron straps from its sides up to the hinge pin."""
    fd = Field("Weight")
    c = box_c(COCK)
    fd.add(box(c, (BOX_HW, BOX_HD, BOX_HH), r=0.014), 0.0, GX)
    fd.sub(RoundBox(c + v3((0, 0, BOX_HH)), (BOX_HW - 0.022, BOX_HD - 0.022, 0.06), 0.01), 0.004)
    for zz in (-BOX_HH + 0.03, BOX_HH - 0.03):
        fd.add(Inter(Shell(RoundBox(c, (BOX_HW, BOX_HD, BOX_HH), 0.014), 0.004, 0.008, pad=0.05),
                     Func(lambda P, zz=zz: np.abs(P[:, 2] - F(c[2] + zz)) - F(0.02), c - 0.4, c + 0.4), 0.002), 0.003, IRON)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(Inter(Shell(RoundBox(c, (BOX_HW, BOX_HD, BOX_HH), 0.014), 0.004, 0.008, pad=0.05),
                         Func(lambda P, sx=sx, sy=sy: np.maximum(np.abs(P[:, 0] - F(c[0] + sx * BOX_HW)) - F(0.03),
                                                                 np.abs(P[:, 1] - F(c[1] + sy * BOX_HD)) - F(0.03)), c - 0.4, c + 0.4), 0.002), 0.003, IRON)
    hc = hinge_pt(COCK)
    for sx in (-1, 1):
        a = hc + v3((sx * (BOX_HW + 0.012), 0, 0))
        b = c + v3((sx * (BOX_HW + 0.008), 0, BOX_HH - 0.04))
        fd.add(tbeam(a, b, (1, 0, 0), 0.006, 0.03, r=0.004), 0.003, IRON)
        fd.add(Torus(a, 0.024, 0.008, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, IRON)
    rs = np.random.RandomState(21)
    for k in range(9):                                                                # the stones heaped in it
        p = c + v3((rs.uniform(-BOX_HW + 0.06, BOX_HW - 0.06), rs.uniform(-BOX_HD + 0.06, BOX_HD - 0.06), BOX_HH - 0.02 + rs.uniform(0, 0.03)))
        fd.add(Ellipsoid(p, (rs.uniform(0.05, 0.075), rs.uniform(0.045, 0.065), rs.uniform(0.035, 0.05)), R=euler(0, 0, rs.uniform(0, 3)),
                         disp=lambda P: F(0.006) * NOISE(P * F(14)), disp_amp=0.007), 0.012, 11)
    return fd


def sling_field():
    """The sling (cocked): two ropes from the arm's tip (one tied round it, one looped over the prong) to the ends of a
    leather pouch cradling the stone in the trough."""
    fd = Field("Sling")
    H = hook_pt(COCK)
    tip = arm_pt(LONG - 0.01)
    S = SLING_REST
    ax = norm(S - H)
    side = v3((1.0, 0.0, 0.0))
    third = norm(np.cross(ax, side))
    Rp = np.stack([side, third, ax], axis=1)
    pouch = Ellipsoid(S + ax * 0.012, (0.1, 0.09, 0.07), R=Rp)
    leather = lambda P: F(0.0015) * NOISE(P * F(40))
    fd.add(Inter(Shell(pouch, 0.0, 0.014, pad=0.04, disp=leather, disp_amp=0.002),
                 Func(lambda P: -(((P - S.astype(F)) @ ax.astype(F)) + F(0.025)), S - 0.25, S + 0.25), 0.006), 0.0, HIDE)
    tw = lambda P: F(0.0012) * NOISE(P * F(120))
    for sx in (-1, 1):
        e = S + side * (sx * 0.095) - ax * 0.01
        a = H + side * (sx * 0.006) if sx > 0 else tip + side * (sx * 0.03)
        fd.add(RoundCone(a, e, 0.008, 0.008, disp=tw, disp_amp=0.0015), 0.004, ROPE)
        fd.add(Sphere(e, 0.014), 0.004, HIDE)
    fd.add(Torus(H, 0.016, 0.0055, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, ROPE)
    fd.add(Torus(tip, W1 + 0.012, 0.007, R=rot_from_axes(z_axis=arm_dir(COCK))), 0.003, ROPE)
    return fd


def winch_field():
    """The windlass: the drum with rope on it and iron rims, its axle, the spoked wheel on his side (four spokes with
    round grips; it turns with the 'winch' bone)."""
    fd = Field("Winch")
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    L = 2 * (SW - 0.06)
    fd.add(Cylinder(DRUM, DRUM_R, L, rr=0.008, R=Rx, disp=GRAIN, disp_amp=0.002), 0.0, GX)
    for sx in (-1, 1):
        fd.add(Torus(DRUM + v3((sx * (L / 2 - 0.012), 0, 0)), DRUM_R + 0.004, 0.011, R=Rx), 0.003, IRON)
    for k in range(7):
        fd.add(Torus(DRUM + v3((-0.075 + 0.025 * k, 0, 0)), DRUM_R + 0.006, 0.009, R=Rx), 0.002, ROPE)
    ax0, ax1 = v3((MX + SW + 0.08, DRUM[1], DRUM[2])), v3((WHEEL_X - 0.03, DRUM[1], DRUM[2]))
    fd.add(Cylinder((ax0 + ax1) / 2, 0.026, float(np.linalg.norm(ax1 - ax0)), rr=0.006, R=Rx), 0.004, IRON)
    hub = v3((WHEEL_X, DRUM[1], DRUM[2]))
    fd.add(Cylinder(hub, 0.05, 0.06, rr=0.01, R=Rx), 0.004, GX)
    for k in range(4):
        g = spoke_end(0.0, k)
        fd.add(tbeam(hub, g, (1, 0, 0), 0.02, 0.018, 0.016, 0.015, r=0.006, disp=GRAIN, disp_amp=0.0015), 0.004, GZ)
        fd.add(RoundCone(g + v3((0.012, 0, 0)), g - v3((PEG_L, 0, 0)), 0.017, 0.015, disp=GRAIN, disp_amp=0.0012), 0.004, 10)
        fd.add(Sphere(g - v3((PEG_L, 0, 0)), 0.022), 0.004, 10)
    fd.add(Torus(hub, WHEEL_R, 0.014, R=Rx), 0.004, GZ)                              # the rim
    return fd


def trigger_field():
    """The trigger: an iron hook pivoted on the post's top; it rises behind the ring under the arm's tip and its bill
    passes through the ring and curls down in front of it."""
    fd = Field("Trigger")
    r = hook_tip()
    fd.add(Cylinder(TRIG_P, 0.024, 0.07, rr=0.006, R=rot_from_axes(z_axis=(1, 0, 0))), 0.0, IRON)
    pts = [TRIG_P, TRIG_P + v3((0, 0.035, 0.045)), r + v3((0, 0.034, 0.0)), r, r + v3((0, -0.03, 0.0)), r + v3((0, -0.042, -0.022))]
    fd.add(Chain(pts, [0.016, 0.014, 0.011, 0.009, 0.009, 0.008], k=0.005), 0.004, IRON)
    return fd


def haul_field():
    """The windlass rope, cocked: from the drum up to the ring under the arm."""
    fd = Field("Haul")
    a, b = haul_start(), ring_pt(COCK)
    tw = lambda P: F(0.0015) * np.sin(((P - a.astype(F)) @ norm(b - a).astype(F)) * F(420) + P[:, 0] * F(300))
    fd.add(RoundCone(a, b + norm(a - b) * 0.014, 0.0095, 0.0095, disp=tw, disp_amp=0.002), 0.0)
    return fd


def stones_field():
    """The stone in the sling's pouch and the heap behind him (the top one is the one he lifts)."""
    fd = Field("Stones")
    fd.add(stone_ball(SLING_REST, BALL_R, 3), 0.0)
    for i, (c, bone) in enumerate(pile_balls()):
        fd.add(stone_ball(c, BALL_R, 10 + i), 0.0)
    return fd


def stone_centres():
    return [(SLING_REST, "stone")] + [(c, b) for c, b in pile_balls()]


def mat_field():
    """A straw mat under the heap of stones."""
    fd = Field("Mat")
    fib = lambda P: F(0.0015) * np.sin(P[:, 0] * F(400)) + F(0.001) * NOISE(P * F(60))
    fd.add(RoundBox(PILE + v3((-0.04, -0.03, 0.006)), (0.2, 0.16, 0.006), 0.005, R=euler(0, 0, 0.25), disp=fib, disp_amp=0.002), 0.0)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.24, 1.622)), 0.05, 0.6)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.11, -0.13, 1.63)), 0.055, 0.5)]
    for side in ("R", "L"):
        wr, f, n, t = hand_frame(side)
        for o in (0.044, 0.0148, -0.0148, -0.044):
            pts.append((wr + f * 0.14 + t * o - n * 0.012, 0.032, 0.45))
    return pts


# ======================================================================================= build config
GLB_NAME = "trebuchet"
ROOT_NAME = "TrebuchetHQ"
TEX_PREFIX = "treb"
MAT_NAME = "TrebuchetMat"
MESH_NAME = "Trebuchet"
BASE_MODULE = "trebuchet_base"
ANIM_MODULE = "anim_trebuchet"
PARTS = ["Skin", "Eyes", "Teeth", "Beard", "Hood", "Tunic", "Apron", "Leather", "Hose", "Mallet", "Frame", "Arm", "Weight",
         "Sling", "Winch", "Trigger", "Haul", "Stones", "Mat"]
REGION_PARTS = ("Skin", "Hood", "Tunic", "Apron", "Leather", "Mallet", "Frame", "Arm", "Weight", "Sling", "Winch", "Trigger")
SIEGE = {"name": "HQ_Trebuchet", "wood": (0.54, 0.37, 0.22), "wood2": (0.38, 0.25, 0.14), "red": (0.66, 0.12, 0.08),
         "blue": (0.14, 0.27, 0.6), "metal": "iron"}
GREY_HAIR = {"name": "HQ_EngineerBeard", "base": (0.62, 0.6, 0.57), "hi": (0.88, 0.87, 0.84), "low": (0.36, 0.34, 0.32),
             "streak": (0.5, 0.48, 0.46), "tint": (0.7, 0.66, 0.6)}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_EngineerSkin", "base": (0.82, 0.58, 0.44), "ruddy": (0.86, 0.47, 0.37), "lips": (0.68, 0.39, 0.34),
                      "brow": ((0.55, 0.53, 0.5), (0.78, 0.76, 0.72)),
                      "extra": ((LASH, (0.2, 0.17, 0.15), 0.5), (STUBBLE, (0.6, 0.55, 0.5), 0.55, 0.35))}),
    "Beard": ("hair", GREY_HAIR),
    "Hood": ("wool", {"name": "HQ_Chaperon", "base": (0.66, 0.12, 0.08), "border": (0.2, 0.36, 0.18), "stripe": (0.3, 0.06, 0.04)}),
    "Tunic": ("wool", {"name": "HQ_EngineerTunic", "base": (0.42, 0.28, 0.16), "border": (0.2, 0.36, 0.18), "stripe": (0.2, 0.36, 0.18)}),
    "Apron": ("leather_dyed", {"name": "HQ_Apron", "base": (0.36, 0.22, 0.12), "dyed": (0.14, 0.09, 0.06)}),
    "Leather": ("leather_dyed", {"name": "HQ_EngineerLeather", "base": (0.3, 0.19, 0.11)}),
    "Hose": ("wool", {"name": "HQ_EngineerHose", "base": (0.44, 0.44, 0.42)}),
    "Mallet": ("siege", SIEGE),
    "Frame": ("siege", SIEGE), "Arm": ("siege", SIEGE), "Weight": ("siege", SIEGE), "Sling": ("siege", SIEGE),
    "Winch": ("siege", SIEGE), "Trigger": ("siege", SIEGE),
    "Haul": ("cord", {}),
    "Stones": ("limestone", {"name": "HQ_TrebStones"}),
    "Mat": ("reed", {"name": "HQ_StrawMat", "base": (0.72, 0.62, 0.34)}),
}
LOW_TARGETS = {"Skin": 6400, "Teeth": 60, "Beard": 900, "Hood": 2000, "Tunic": 1700, "Apron": 1100, "Leather": 1300,
               "Hose": 600, "Mallet": 380, "Frame": 6200, "Arm": 1100, "Weight": 1300, "Sling": 520, "Winch": 800,
               "Trigger": 200, "Haul": 80, "Stones": 900, "Mat": 220}
AO_EXCLUDE = ["Arm", "Weight", "Sling", "Winch", "Trigger", "Haul", "Stones", "Mallet"]
BAKE_APART = (["Frame", "Arm", "Weight", "Sling", "Winch", "Trigger", "Haul", "Stones", "Mat"], (6.0, 0.0, 0.0))


def prop_bones():
    return []                       # the mallet is rigid in his right fist


KICK_P = v3((MX, Y0, 0.0))          # the frame rocks about its front end at the throw


def extra_bones():
    """The engine's bones (none of them deform him): frame (it rocks at the throw), arm (turns on the axle), weight (the
    counterweight, hanging plumb from the hinge pin), sling (from the prong to the stone: it trails and whips over as the
    arm flies), stone (in the pouch), haul (the windlass rope, stretched toward the arm's ring), winch (drum and wheel),
    trigger (the hook), carry (the stone he lifts from the heap) and props (the heap and its mat: still)."""
    h0, h1 = haul_start(), ring_pt(COCK)
    H = hook_pt(COCK)
    hc = hinge_pt(COCK)
    return [
        ("frame", KICK_P, KICK_P + v3((0, 0.4, 0)), None),
        ("arm", AXLE, AXLE + arm_dir(COCK) * 0.6, "frame"),
        ("weight", hc, hc - v3((0, 0, 0.3)), "arm"),
        ("sling", H, SLING_REST, "arm"),
        ("stone", SLING_REST, SLING_REST + v3((0, 0, 0.15)), "sling"),
        ("haul", h0, h1, "frame"),
        ("winch", v3((MX + SW, DRUM[1], DRUM[2])), v3((WHEEL_X, DRUM[1], DRUM[2])), "frame"),
        ("trigger", TRIG_P, hook_tip(), "frame"),
        ("carry", CARRY_C, CARRY_C + v3((0, 0, 0.15)), None),
        ("props", PILE, PILE + v3((0, 0, 0.3)), None),
    ]


def stones_weights(ob, skin_ob, arm):
    """Each stone (mesh island) goes rigidly to the bone of the stone whose centre is nearest its own centre."""
    import bmesh
    cs = stone_centres()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    seen, groups = set(), {}
    for v0 in bm.verts:
        if v0.index in seen:
            continue
        stack, isl = [v0], []
        seen.add(v0.index)
        while stack:
            v = stack.pop()
            isl.append(v.index)
            for e in v.link_edges:
                w = e.other_vert(v)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
        cen = np.mean([np.array(bm.verts[i].co) for i in isl], axis=0)
        bone = min(cs, key=lambda c: np.linalg.norm(cen - c[0]))[1]
        for i in isl:
            _blend_add(ob, groups, i, {bone: 1.0})
    bm.free()


def hood_weights(ob, skin_ob, arm):
    """The hood with the head; the cape from the neck to the shoulders; the tail down his back from the head to the
    chest."""
    groups = {}
    z1 = hp((0, 0, 1.62))[2]
    for v in ob.data.vertices:
        p = v.co
        if p.z >= z1:
            w = {"head": 1.0}
        elif p.y > 0.2 and abs(p.x) < 0.12:                           # the tail
            t = max(0.0, min(1.0, (z1 - p.z) / 0.5))
            w = {"head": max(0.0, 1.0 - 1.5 * t), "neck": 0.5 * (1.0 - abs(2 * t - 1.0)), "chest": max(0.0, 1.5 * t - 0.5)}
        else:
            t = max(0.0, min(1.0, (z1 - p.z) / 0.3))
            sd = "R" if p.x < 0 else "L"
            out = max(0.0, min(1.0, (abs(p.x) - 0.2) / 0.15))
            w = {"head": 1.0 - t, "neck": 0.5 * t, "chest": 0.5 * t * (1 - out), "clavicle." + sd: 0.5 * t * out}
        _blend_add(ob, groups, v.index, w)


def weight_rules():
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Beard": ("rigid", "head"),
        "Hood": ("custom", hood_weights),
        "Tunic": ("transfer", TORSO | {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L",
                                       "thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Apron": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.4, "thigh.L": 0.4}),
        "Leather": ("transfer", TORSO | {"forearm.R", "forearm.L", "hand.R", "hand.L", "thigh.R", "thigh.L", "shin.R", "shin.L",
                                         "foot.R", "foot.L"}, {"thigh.R": 0.25, "thigh.L": 0.25}),
        "Hose": ("transfer", {"root", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Mallet": ("rigid", "hand.R"),
        "Frame": ("rigid", "frame"), "Arm": ("rigid", "arm"), "Weight": ("rigid", "weight"), "Sling": ("rigid", "sling"),
        "Winch": ("rigid", "winch"), "Trigger": ("rigid", "trigger"), "Haul": ("rigid", "haul"),
        "Stones": ("custom", stones_weights), "Mat": ("rigid", "props"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Beard") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.8
    if part in ("Frame", "Winch", "Mat"):
        return 0.7
    if part in ("Arm", "Weight", "Stones", "Trigger", "Haul", "Sling"):
        return 0.85
    if part == "Mallet":
        return 0.9
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Beard", beard_field(), 0.0022 if fine else 0.003),
        ("Hood", hood_field(), 0.0026 if fine else 0.0036),
        ("Tunic", tunic_field(), 0.0026 if fine else 0.0036),
        ("Apron", apron_field(), 0.0024 if fine else 0.0034),
        ("Leather", leather_field(), 0.0022 if fine else 0.003),
        ("Hose", hose_field(), 0.0024 if fine else 0.0034),
        ("Mallet", mallet_field(), 0.002 if fine else 0.003),
        ("Frame", frame_field(), 0.0036 if fine else 0.005),
        ("Arm", arm_field(), 0.003 if fine else 0.0042),
        ("Weight", weight_field(), 0.003 if fine else 0.0042),
        ("Sling", sling_field(), 0.0022 if fine else 0.003),
        ("Winch", winch_field(), 0.0026 if fine else 0.0036),
        ("Trigger", trigger_field(), 0.0018 if fine else 0.0026),
        ("Haul", haul_field(), 0.0016 if fine else 0.0022),
        ("Stones", stones_field(), 0.0026 if fine else 0.0036),
        ("Mat", mat_field(), 0.0022 if fine else 0.003),
    ]
