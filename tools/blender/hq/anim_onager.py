"""Onager clips (30 fps).

Idle   : the engine wound and loaded; he stands by it with the mallet resting on his shoulder, his left fist on his hip,
         breathes, shifts his weight and looks about.
Combat : ready to shoot: turned toward the trigger pin with the mallet raised over his shoulder, his left hand on his
         thigh, a slow bob.
Attack : (66 frames = the 2.2 s cooldown) he brings the mallet down on the trigger pin (RELEASE); the pawl jumps out of
         the ratchet, the drum spins free and the arm whips up into the buffer (SLAM), dragging the sling off the back
         board: it trails, then whips over the arm's tip and the stone flies (the frame kicks up at the back). The empty
         sling swings over and drops to hang from the tip. He watches the shot, kneels at the windlass with the mallet
         propped by his foot and winds the arm back down with the crank, the pawl riding the teeth (the pouch lands on
         the board again as the tip comes down); then he gets up, takes a stone from the heap behind him in his left
         hand, lays it in the pouch and raises the mallet again.

The engine's bones are posed directly: frame (rocking about its front end), arm (on the skein), sling (from the arm's
prong to the pouch: aimed at where the pouch is), stone (in the pouch), haul (the windlass rope: aimed at the arm's ring
and stretched to reach it), winch (the drum and crank, turned about their axle), trigger (the pawl), carry (the stone
he lifts: a free bone moved by offsets)."""
import math
from mathutils import Vector, Quaternion, Matrix
import onager as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

_G, _T, _Fv = cm.mallet_frame()
M_T, M_F = vec(_T), vec(_Fv)
_wrR, _fR, _nR, _tR = cm.hand_frame("R")
FIST_OFF_R = vec(cm.fist_center("R") - _wrR)
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
T_L, F_L, N_L = vec(_tL), vec(_fL), vec(_nL)
FIST_OFF_L = vec(cm.fist_center("L") - _wrL)
BALL_IN_L = F_L * 0.1 + N_L * (0.03 + cm.BALL_R * 0.9)          # the ball's centre from the left wrist (rest pose)
ML = cm.MALLET_L
MH = cm.MALLET_HEAD[0]

RELEASE = 3        # the mallet knocks the pin out: the drum runs free
SLAM = 7           # the arm hits the buffer: the sling has whipped over and the stone flies (game.gd launches it here)
FR = 66            # = the 2.2 s cooldown
CRANK0, CRANK1 = 16, 42      # winding
PLACE = 57         # the ball goes into the cup


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    """A rest-pose body point carried by the root offset and turn (no spine bend)."""
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def smooth_keys(keys, f, fn=ease):
    """Piecewise interpolation of (frame, value) keys; values: float or Vector."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (fa, a), (fb, b) in zip(keys, keys[1:]):
        if f <= fb:
            k = fn((f - fa) / float(fb - fa)) if fb > fa else 1.0
            return a.lerp(b, k) if isinstance(a, Vector) else a + (b - a) * k
    return keys[-1][1]


# ---------------------------------------------------------------------------------------------- the engine
def _rope_len(a):
    return (vec(cm.haul_point(a)) - vec(cm.haul_start())).length


L_COCK = _rope_len(cm.COCK)
L_FIRED = _rope_len(cm.FIRED)
TURNS = (L_FIRED - L_COCK) / cm.DRUM_R            # radians the drum turns between wound and fired


def arm_for_len(L):
    """The arm's angle at which the rope from the drum to its ring is L long (monotonic: bisection)."""
    lo, hi = cm.COCK - 0.3, cm.FIRED + 0.3
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if _rope_len(m) < L:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def kick_rot(deg):
    return Matrix.Rotation(math.radians(deg), 3, "X")


KP = vec(cm.KICK_P)


SL = cm.SLING_L
REST_Z = float(cm.SLING_LEFT[2])         # the pouch's centre lying on the back board
D0 = (vec(cm.SLING_LEFT) - vec(cm.hook_pt(cm.COCK))).normalized()
TH0 = math.atan2(D0.z, D0.y)             # the sling's angle at rest (in the frame's y-z plane: 0 = toward the back)


HANG_A = math.radians(50.0)              # from this arm angle down the empty sling swings back toward the board
DRAPE = math.radians(211.0)              # hanging behind the raised arm: (the arm's angle +) this, clear of its back


def sling_rest_or_hang(a):
    """The sling's direction (frame space) when it is at rest under the arm at angle a: draped behind the arm while the
    arm is up, swinging back as it comes down so the pouch lands on the back board (clear of the drum) when wound."""
    t = max(0.0, min(1.0, (HANG_A - a) / (HANG_A - cm.COCK)))
    th = (a + DRAPE) + (TH0 + 2.0 * math.pi - (a + DRAPE)) * ease(t)
    return V(0.0, math.cos(th), math.sin(th))


TH_THROW = cm.FIRED + math.radians(62.0)  # whipped over the tip, forward and up: the stone leaves


def sling_angle(f, a):
    """The sling's angle (frame y-z plane, 0 = toward the back, + = up) through the shot: on the board until the arm
    flies, trailing behind the rising arm, whipping over its tip (the stone leaves at SLAM); then, its loop off the
    prong, it flops back over the tip and drops behind the arm."""
    if f <= RELEASE:
        return TH0
    if f <= SLAM:
        t = (f - RELEASE) / float(SLAM - RELEASE)
        return TH0 + (TH_THROW - TH0) * t ** 2.5
    t = min(1.0, (f - SLAM) / 8.0)
    end = a + DRAPE - 2.0 * math.pi
    over = math.radians(12.0)                                     # it swings a little past, then settles
    k1 = ease(min(1.0, t / 0.75))
    k2 = ease(max(0.0, (t - 0.6) / 0.4))
    return TH_THROW + (end - over - TH_THROW) * k1 + over * k2


def sling_dir(f, a):
    """The sling's direction (frame space) at frame f with the arm at angle a."""
    if f > SLAM + 8:
        return sling_rest_or_hang(a)
    th = sling_angle(f, a)
    return V(0.0, math.cos(th), math.sin(th))


def machine(a, drum, pawl_deg=0.0, kick_deg=0.0, sling=None):
    """Aims and scales for the engine: arm angle a, drum turned by `drum` radians from wound (+ = paying out), pawl
    lifted by pawl_deg, frame rocked up at the back by kick_deg, the sling along `sling` (frame space; default: at rest
    or hanging)."""
    K = kick_rot(kick_deg)
    aims, sc = {}, {}
    aims["frame"] = ("rot", K.to_quaternion())
    aims["arm"] = K @ vec(cm.arm_dir(a))
    aims["sling"] = K @ (sling if sling is not None else sling_rest_or_hang(a))
    h0 = KP + K @ (vec(cm.haul_start()) - KP)
    h1 = KP + K @ (vec(cm.haul_point(a)) - KP)
    aims["haul"] = h1 - h0
    sc["haul"] = (1.0, (h1 - h0).length / L_COCK, 1.0)
    # the winch bone points along -X; a twist t about it turns the crank by -t about +X (paying out turns it back)
    aims["winch"] = (K @ V(-1.0, 0.0, 0.0), drum)
    pt = vec(cm.pawl_tip()) - vec(cm.PAWL_P)
    aims["trigger"] = K @ (Matrix.Rotation(math.radians(pawl_deg), 3, "X") @ pt)
    return aims, sc


def crank_phi(drum):
    """The crank handle's angle (as in torsion.crank_handle) when the drum has paid out `drum` radians."""
    return cm.CRANK_PHI - drum


def crank_grip(drum):
    """Where his left fist holds the crank handle (its middle)."""
    h0, h1 = cm.crank_handle(crank_phi(drum))
    return vec(h0).lerp(vec(h1), 0.55)


# ---------------------------------------------------------------------------------------------- hands
def mallet_grip(arm, grip, hd, face, pole):
    """Right fist (its grip) at `grip`, the handle toward the head along hd, the head's face along `face`."""
    hd = Vector(hd).normalized()
    R = frame_map(M_T, hd, M_F, Vector(face))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF_R, pole=pole)
    aims["hand.R"] = ("frame", M_T, hd, M_F, Vector(face))
    return aims


def left_grip(arm, grip, td, fd, pole):
    """Left fist centre at `grip`, its thumb axis along td, its knuckles toward fd."""
    R = frame_map(T_L, Vector(td), F_L, Vector(fd))
    aims = arm_aims(arm, "L", Vector(grip) - R @ FIST_OFF_L, pole=pole)
    aims["hand.L"] = ("frame", T_L, Vector(td), F_L, Vector(fd))
    return aims


def left_ball(arm, ball, td, fd, pole):
    """Left hand holding a ball (its centre at `ball`) palm on it."""
    R = frame_map(T_L, Vector(td), F_L, Vector(fd))
    aims = arm_aims(arm, "L", Vector(ball) - R @ BALL_IN_L, pole=pole)
    aims["hand.L"] = ("frame", T_L, Vector(td), F_L, Vector(fd))
    return aims


def shoulder_rest(ro, yaw, br=0.0):
    """Mallet resting on his right shoulder: the fist in front of the shoulder, the head behind it."""
    q = rz(yaw)
    grip = body_pt(J["shoulder_R"], ro, yaw) + q @ V(0.11, -0.22, -0.16 + 0.004 * br)
    hd = q @ V(-0.12, 0.72, 0.68)
    face = q @ V(1.0, 0.0, 0.0)
    return grip, hd, face


def perp(face, hd):
    hd = Vector(hd).normalized()
    f = Vector(face) - hd * Vector(face).dot(hd)
    return f.normalized()


# the strike: the mallet's head lands on the trigger pin; the swing is in a vertical plane through the handle
PIN = vec(cm.PIN_TOP)
HD_HIT = V(0.75, -0.38, -0.45).normalized()
HEAD_HIT = PIN + V(0, 0, MH + 0.004)
GRIP_HIT = HEAD_HIT - HD_HIT * ML
SWING_AX = HD_HIT.cross(V(0, 0, 1)).normalized()          # rotating hd about this lifts the head up and back


def swing(t):
    """t = 0: raised (head up and back over his shoulder), 1: on the pin. Returns grip, hd, face."""
    ang = math.radians(150.0) * (1.0 - t)
    R = Matrix.Rotation(-ang, 3, SWING_AX)
    hd = R @ HD_HIT
    face = SWING_AX.cross(hd).normalized()                     # toward the motion: down at the hit
    # the fist travels on an arc from over his right shoulder to above the pin
    g0 = V(-0.2, 0.08, 1.58)
    g = g0.lerp(GRIP_HIT, t) + V(0, 0, 0.16 * math.sin(math.pi * t))
    return g, hd, face


# ---------------------------------------------------------------------------------------------- body
def feet(arm, lf, rf, yaw, lift_l=0.0, lift_r=0.0, kneel_l=0.0, foot_yaw=None):
    """Ankles at world (x, y) lf / rf; kneel_l (0-1) drops the left knee to the ground, the foot on its toes behind."""
    q = rz(yaw)
    fy = yaw if foot_yaw is None else foot_yaw
    aims = {}
    for side, p, lift in (("L", lf, lift_l), ("R", rf, lift_r)):
        z = float(J["ankle_" + side][2]) + lift
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        fdir = rz(fy + (-10 if side == "R" else 10)) @ rest_foot
        if side == "L" and kneel_l > 0.0:
            z = lerp(z, 0.13, kneel_l)
            pole = (q @ V(0.0, -1.0, -0.35)).lerp(pole, 1.0 - kneel_l)
            fdir = fdir.lerp(q @ V(0.0, 0.35, -1.0) * fdir.length, kneel_l)
        aims.update(leg_aims(arm, side, V(p[0], p[1], z), pole=pole))
        aims["foot." + side] = fdir
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, br=0.0):
    """Spine and chest bent forward by `bend` radians (toward the facing) and to his left by `side` radians, the chest
    turned `chest` degrees more; the head turned to the world heading `look` (degrees, 0 = -Y) and pitched up by
    `pitch` (the neck and head aim in world space, so they stay upright however far he bends)."""
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend + 0.01 * br, side), math.radians(chest * 0.6))          # (world aims: the chest's
                                                                                               # tilt is the whole bend)
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(0.0, -0.16 - 0.25 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(0.0, -0.06 + 0.55 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.04, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.04, 0.02)


# ---------------------------------------------------------------------------------------------- idle / combat
STAND_RO = V(-0.14, 0.04, 0.0)
STAND_LF = (0.08, 0.12)
STAND_RF = (-0.34, -0.02)
C_YAW = 30.0
C_RO = V(-0.08, 0.05, -0.05)
C_LF = (0.2, -0.12)
C_RF = (-0.3, 0.12)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = 8.0 + 4.0 * sway
    ro = STAND_RO + V(0.012 * sway, 0.0, -0.006 + 0.005 * br)
    aims = feet(arm, STAND_LF, STAND_RF, 8.0)
    look = yaw + 35.0 * math.sin(w) + 10.0 * math.sin(w * 3)
    torso(aims, yaw, bend=0.02, side=0.03 * sway, chest=2.0 * sway, look=look, pitch=0.05 + 0.03 * br, br=br)
    g, hd, face = shoulder_rest(ro, yaw, br)
    aims.update(mallet_grip(arm, g, hd, face, pole=rz(yaw) @ V(-1.0, 0.3, -0.6)))
    hip = body_pt(V(0.27, 0.0, 0.94), ro, yaw)
    aims.update(arm_aims(arm, "L", hip + V(0, 0, 0.004 * br), pole=rz(yaw) @ V(1.0, 0.5, 0.1),
                         hand_dir=rz(yaw) @ V(-0.35, 0.25, -1.0)))
    return aims, ro, rz(yaw), {}, {}


def combat_core(arm, br=0.0, sw=0.0):
    yaw = C_YAW + 1.5 * sw
    ro = C_RO + V(0.0, 0.0, 0.007 * br)
    aims = feet(arm, C_LF, C_RF, C_YAW)
    torso(aims, yaw, bend=0.18, side=0.0, chest=6.0, look=C_YAW + 22.0, pitch=-0.05 + 0.02 * br, br=br)
    lthigh = body_pt(V(0.2, -0.16, 0.62), ro, yaw)
    aims.update(arm_aims(arm, "L", lthigh + V(0, 0, 0.004 * br), pole=rz(yaw) @ V(1.0, 0.4, 0.2),
                         hand_dir=rz(yaw) @ V(-0.2, -0.3, -1.0)))
    return aims, ro, yaw


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    aims, ro, yaw = combat_core(arm, br, sw)
    g, hd, face = swing(0.0)
    aims.update(mallet_grip(arm, g + V(0.0, 0.0, 0.008 * br), hd, face, pole=V(-1.0, 0.4, -0.3)))
    return aims, ro, rz(yaw), {}, {}


def machine_wound(aims, sc):
    m, s = machine(cm.COCK, 0.0)
    aims.update(m)
    sc.update(s)


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr, sc, offs = idle_pose(arm, (f % frames) / frames)
        machine_wound(aims, sc)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr, sc, offs = combat_pose(arm, (f % frames) / frames)
        machine_wound(aims, sc)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- the attack
def arm_angle(f):
    """The throwing arm: wound until RELEASE, whips up into the buffer by SLAM, rebounds and settles; wound back down
    by the crank (from the drum's turn)."""
    if f <= RELEASE:
        return cm.COCK
    if f <= SLAM:
        k = (f - RELEASE) / float(SLAM - RELEASE)
        return lerp(cm.COCK, cm.FIRED + 0.03, k * k)
    if f <= 14:
        k = (f - SLAM) / 7.0
        return cm.FIRED - 0.13 * math.sin(k * math.pi) * (1.0 - k) + 0.03 * (1.0 - k)
    if f < CRANK0:
        return cm.FIRED
    return arm_for_len(L_COCK + drum_turn(f) * cm.DRUM_R)


def drum_turn(f):
    """Radians the drum has paid out (0 = wound)."""
    if f <= RELEASE:
        return 0.0
    if f < CRANK0:
        a = arm_angle(f)
        return (_rope_len(a) - L_COCK) / cm.DRUM_R
    if f >= CRANK1:
        return 0.0
    k = (f - CRANK0) / float(CRANK1 - CRANK0)
    k = k * k * (3 - 2 * k) * 0.35 + k * 0.65                 # steady cranking, easing in and out a little
    return TURNS * (1.0 - k)


def pawl(f):
    if f < RELEASE:
        return 0.0
    if f <= RELEASE + 1:
        return 26.0 * (f - RELEASE + 1) / 2.0
    if f < CRANK0:
        return 26.0
    if f < CRANK1:
        return 7.0 + 4.0 * abs(math.sin(drum_turn(f) * 5.0))  # riding over the ratchet's teeth
    if f < CRANK1 + 2:
        return 7.0 * (1.0 - (f - CRANK1) / 2.0)
    return 0.0


def kick(f):
    if f < SLAM:
        return 0.0
    k = f - SLAM
    if k <= 2:
        return 2.6 * k / 2.0
    if k <= 5:
        return 2.6 * (1.0 - (k - 2) / 3.0)
    if k <= 8:
        return 0.7 * math.sin((k - 5) / 3.0 * math.pi)
    return 0.0


# body keys for the attack: frame -> (root offset, yaw, lean, crouch)
K_RO = [(0, C_RO), (RELEASE, V(0.08, -0.1, -0.2)), (6, V(0.06, -0.08, -0.15)), (10, V(-0.06, 0.0, -0.05)),
        (14, V(-0.1, -0.14, -0.22)), (CRANK0, V(-0.13, -0.2, -0.45)), (CRANK1, V(-0.13, -0.2, -0.45)),
        (46, V(-0.04, 0.02, -0.1)), (50, V(-0.04, 0.08, -0.4)), (53, V(0.04, 0.1, -0.12)), (PLACE, V(0.16, 0.14, -0.3)),
        (60, V(0.08, 0.1, -0.06)), (FR, C_RO)]
K_YAW = [(0, C_YAW), (RELEASE, 44.0), (6, 40.0), (10, 18.0), (14, 70.0), (CRANK0, 88.0), (CRANK1, 88.0), (46, 150.0),
         (50, 168.0), (53, 130.0), (PLACE, 96.0), (60, 70.0), (FR, C_YAW)]
K_BEND = [(0, 0.18), (RELEASE, 0.72), (6, 0.55), (10, 0.08), (14, 0.3), (CRANK0, 0.62), (CRANK1, 0.62), (46, 0.3),
          (50, 1.05), (53, 0.3), (PLACE, 0.9), (60, 0.2), (FR, 0.18)]
# feet: (frame, left ankle (x, y), right ankle (x, y)); a foot that moves between keys steps (lifts). (The near side
# beam's outer face is at x = 0.4: no foot goes past it.)
K_FEET = [(0, C_LF, C_RF), (RELEASE, (0.24, -0.16), C_RF), (10, (0.24, -0.16), C_RF),
          (CRANK0, (-0.34, -0.12), (0.06, -0.46)), (CRANK1, (-0.34, -0.12), (0.06, -0.46)),
          (46, (0.04, 0.1), (-0.26, -0.12)), (50, (0.06, 0.12), (-0.3, -0.04)), (PLACE, (0.28, 0.32), (0.02, 0.04)),
          (62, C_LF, (0.02, 0.04)), (FR, C_LF, C_RF)]


def feet_at(f):
    for (fa, la, ra), (fb, lb, rb) in zip(K_FEET, K_FEET[1:]):
        if fa <= f <= fb:
            k = ease((f - fa) / float(fb - fa))
            lf = (lerp(la[0], lb[0], k), lerp(la[1], lb[1], k))
            rf = (lerp(ra[0], rb[0], k), lerp(ra[1], rb[1], k))
            ll = 0.07 * math.sin(math.pi * k) if la != lb else 0.0
            rl = 0.07 * math.sin(math.pi * k) if ra != rb else 0.0
            return lf, rf, ll, rl
    return K_FEET[-1][1], K_FEET[-1][2], 0.0, 0.0


def kneel(f):
    return smooth_keys([(10, 0.0), (CRANK0, 1.0), (CRANK1, 1.0), (46, 0.0)], f)


def attack_pose(arm, f):
    ro = smooth_keys(K_RO, f)
    yaw = smooth_keys(K_YAW, f)
    bend = smooth_keys(K_BEND, f)
    lf, rf, ll, rl = feet_at(f)
    kn = kneel(f)
    crank = CRANK0 <= f <= CRANK1
    effort = math.sin(drum_turn(f) * 2.0) if crank else 0.0           # heaving with each half turn
    if crank:
        ro = ro + rz(yaw) @ V(0.0, -0.025 * effort, 0.012 * effort)
    aims = feet(arm, lf, rf, yaw, lift_l=ll, lift_r=rl, kneel_l=kn, foot_yaw=yaw if f > 12 else C_YAW)
    # where he looks: the pin, then the shot flying off, the crank, the heap, the cup, the field again
    look = smooth_keys([(0, C_YAW + 22.0), (RELEASE, 58.0), (6, 30.0), (10, 0.0), (14, 40.0), (CRANK0, 92.0),
                        (CRANK1, 92.0), (46, 150.0), (PLACE, 112.0), (60, 60.0), (FR, C_YAW + 22.0)], f)
    pitch = smooth_keys([(0, -0.05), (RELEASE, -0.5), (6, 0.05), (9, 0.35), (13, 0.2), (CRANK0, -0.35), (CRANK1, -0.3),
                         (46, -0.4), (50, -0.6), (53, -0.1), (PLACE, -0.4), (60, 0.0), (FR, -0.05)], f)
    torso(aims, yaw, bend=bend, side=0.0, chest=smooth_keys([(0, 6.0), (RELEASE, 14.0), (8, 0.0), (FR, 6.0)], f),
          look=look, pitch=pitch)
    sc, offs = {}, {}
    # ---- right hand: the mallet
    if f <= RELEASE + 2:                                            # the blow (holding on the pin a moment)
        t = min(1.0, f / float(RELEASE))
        g, hd, face = swing(t * t)
        pole = V(-1.0, 0.3, -0.4)
    elif f <= 10:                                                   # lift it onto his shoulder
        k = ease((f - RELEASE - 2) / (10.0 - RELEASE - 2))
        g1, hd1, face1 = shoulder_rest(ro, yaw)
        g0, hd0, face0 = swing(1.0)
        g = g0.lerp(g1, k) + V(0, 0, 0.12 * math.sin(math.pi * k))
        hd = hd0.lerp(hd1, k).normalized()
        face = perp(face0.lerp(face1, k), hd)
        pole = V(-1.0, 0.2, -0.5)
    elif f < 44:                                                    # propped head-down by his right foot while he winds
        k = ease(min(1.0, (f - 10) / 6.0)) if f < CRANK0 else (1.0 - ease(min(1.0, (f - CRANK1) / 2.0)) if f > CRANK1 else 1.0)
        g1, hd1, face1 = shoulder_rest(ro, yaw)
        q = rz(yaw)
        head = V(rf[0], rf[1], 0.0) + q @ V(-0.16, -0.06, 0.0) + V(0, 0, MH + 0.004)
        hd2 = V(0, 0, -1.0)
        g2 = head - hd2 * ML
        face2 = q @ V(1.0, 0.0, 0.0)
        g = g1.lerp(g2, k)
        hd = hd1.lerp(hd2, k).normalized()
        face = perp(face1.lerp(face2, k), hd)
        pole = rz(yaw) @ V(-1.0, 0.0, -0.3)
    elif f < 60:                                                    # back on his shoulder while he loads
        k = ease(min(1.0, (f - 44) / 4.0))
        q = rz(yaw)
        g1, hd1, face1 = shoulder_rest(ro, yaw)
        head = V(K_FEET[4][2][0], K_FEET[4][2][1], 0.0) + rz(88.0) @ V(-0.16, -0.06, 0.0) + V(0, 0, MH + 0.004)
        hd2 = V(0, 0, -1.0)
        g2 = head - hd2 * ML
        face2 = rz(88.0) @ V(1.0, 0.0, 0.0)
        g = g2.lerp(g1, k)
        hd = hd2.lerp(hd1, k).normalized()
        face = perp(face2.lerp(face1, k), hd)
        pole = rz(yaw) @ V(-1.0, 0.2, -0.5)
    else:                                                           # raise it, ready for the next shot
        k = ease((f - 60) / float(FR - 60))
        g1, hd1, face1 = shoulder_rest(ro, yaw)
        g0, hd0, face0 = swing(0.0)
        g = g1.lerp(g0, k)
        hd = hd1.lerp(hd0, k).normalized()
        face = perp(face1.lerp(face0, k), hd)
        pole = V(-1.0, 0.4, -0.3)
    aims.update(mallet_grip(arm, g, hd, face, pole))
    # ---- left hand: thigh, the crank, the ball
    q = rz(yaw)
    lthigh = body_pt(V(0.2, -0.16, 0.62), ro, yaw)
    if f < 12:
        aims.update(arm_aims(arm, "L", lthigh, pole=q @ V(1.0, 0.4, 0.2), hand_dir=q @ V(-0.2, -0.3, -1.0)))
    elif f < CRANK0:                                                # reach for the handle
        k = ease((f - 12) / float(CRANK0 - 12))
        tgt = crank_grip(drum_turn(CRANK0))
        R0 = lthigh
        R = frame_map(T_L, V(1, 0, 0), F_L, V(0, -0.3, -1.0))
        wr_t = tgt - R @ FIST_OFF_L
        aims.update(arm_aims(arm, "L", R0.lerp(wr_t, k), pole=V(0.0, 1.0, -0.6), hand_dir=q @ V(-0.2, -0.3, -1.0) if k < 0.6 else None))
        if k >= 0.6:
            aims["hand.L"] = ("frame", T_L, V(1, 0, 0), F_L, V(0, -0.3, -1.0))
    elif f <= CRANK1:                                               # winding
        tgt = crank_grip(drum_turn(f))
        aims.update(left_grip(arm, tgt, V(1, 0, 0), V(0, -0.3, -1.0), pole=V(0.0, 1.0, -0.6)))
    elif f < 47:                                                    # let go, reach back for the heap
        k = ease((f - CRANK1) / (47.0 - CRANK1))
        top = vec(cm.CARRY_C)
        wr_a = crank_grip(0.0) - frame_map(T_L, V(1, 0, 0), F_L, V(0, -0.3, -1.0)) @ FIST_OFF_L
        Rb = frame_map(T_L, q @ V(0.0, -1.0, 0.0), F_L, V(0, 0, -1.0))
        wr_b = top + V(0, 0, 0.12) - Rb @ BALL_IN_L
        aims.update(arm_aims(arm, "L", wr_a.lerp(wr_b, k), pole=q @ V(1.0, 0.3, -0.4)))
        aims["hand.L"] = ("frame", T_L, q @ V(0.0, -1.0, 0.0), F_L, V(0, 0, -1.0))
    elif f <= PLACE:                                                # the stone: grip it on the heap, lift, lay it in the pouch
        top = vec(cm.CARRY_C)
        cup = vec(cm.ball_c(cm.COCK))
        if f <= 50:
            b = top + V(0, 0, 0.12 * (1.0 - ease((f - 47) / 3.0)))
            carried = False
        else:
            k = ease((f - 50) / float(PLACE - 50))
            b = top.lerp(cup, k) + V(0, 0, 0.3 * math.sin(math.pi * k))
            carried = True
        aims.update(left_ball(arm, b, q @ V(0.0, -1.0, 0.0), V(0, 0, -1.0), pole=q @ V(1.0, 0.3, -0.4)))
        if carried:
            offs["carry"] = b - top
    else:                                                           # back to his thigh
        k = ease((f - PLACE) / float(FR - PLACE))
        cup = vec(cm.ball_c(cm.COCK))
        if f < PLACE + 2:                                           # (hidden, it stays in the pouch: no slide back to the heap)
            offs["carry"] = cup - vec(cm.CARRY_C)
        Rb = frame_map(T_L, q @ V(0.0, -1.0, 0.0), F_L, V(0, 0, -1.0))
        wr_a = cup + V(0, 0, 0.05) - Rb @ BALL_IN_L
        aims.update(arm_aims(arm, "L", wr_a.lerp(lthigh, k), pole=q @ V(1.0, 0.4, 0.2), hand_dir=q @ V(-0.2, -0.3, -1.0)))
    # ---- the engine
    a = arm_angle(f)
    m, s = machine(a, drum_turn(f), pawl(f), kick(f), sling_dir(f, a))
    aims.update(m)
    sc.update(s)
    sc["stone"] = 1.0 if (f < SLAM or f >= PLACE) else 0.0
    sc["carry"] = 0.0 if PLACE <= f < PLACE + 2 else 1.0
    return aims, ro, rz(yaw), sc, offs


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, rr, sc, offs = attack_pose(arm, f)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    from anim_ugo import key_constant
    key_constant(act, 'pose.bones["stone"].scale')
    key_constant(act, 'pose.bones["carry"].scale')
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
