"""Trebuchet clips (game: 24 fps).

Idle   : the engine cocked and loaded; he stands by the trigger with the mallet on his shoulder, his left fist on his hip,
         breathes, shifts his weight and looks about.
Combat : ready to shoot: facing the trigger peg, the mallet raised over his shoulder, his left hand on his thigh.
Attack : (68 frames = the 2.86 s cooldown) he brings the mallet down on the trigger peg (RELEASE): the hook kicks back
         out of the ring, the counterweight drops (swinging on its hinge) and the arm flies up, dragging the sling along
         the trough until the pouch lifts and whips round over the tip: the stone flies at THROW (game.gd launches it
         there; the frame hops). The windlass wheel spins as its rope pays out. The arm swings past upright and settles,
         the empty sling flopping over and hanging from the tip. He watches the shot, kneels at the wheel with the mallet
         propped by his knee and hauls the arm back down, three pulls on the wheel's pegs with his left hand (the arm
         comes down in jerks, the pouch swinging forward into the trough), the hook drops over the ring again; he gets
         up, takes a stone from the heap behind him, leans over the sill and lays it in the pouch, and goes back to the
         trigger raising the mallet.

The engine's bones are posed directly: frame (rocking about its front end), arm (on the axle), weight (hanging from the
hinge pin: plumb, swinging after the drop), sling (from the prong to the pouch), stone (in the pouch), haul (the windlass
rope: aimed at the arm's ring and stretched to reach it), winch (the drum and its wheel, turned about their axle),
trigger (the hook), carry (the stone he lifts: a free bone moved by offsets)."""
import math
from mathutils import Vector, Quaternion, Matrix
import trebuchet as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
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
BALL_IN_L = F_L * 0.1 + N_L * (0.03 + cm.BALL_R * 0.9)
ML = cm.MALLET_L
MHL = cm.MALLET_HEAD[1]           # the head's half length: its faces are its ends (along M_F)

RELEASE = 3        # the mallet knocks the peg down: the hook kicks back out of the ring
THROW = 10         # the sling has whipped over the tip: the stone flies (game.gd launches it here)
SETTLE = 22        # the arm hangs upright, still
CRANK0 = 24        # the first pull on the wheel
PULL, REGRIP = 5, 2
PULLS = 3
CRANK1 = CRANK0 + PULLS * (PULL + REGRIP)       # 45: the arm is down, the hook drops over the ring
PICK = 52          # his left hand closes on the stone on the heap
PLACE = 59         # the stone goes into the pouch
FR = 68            # = the 2.86 s cooldown
UP = math.radians(90.0)       # the arm at rest after the throw: the counterweight hanging straight down
PHI_COCK = math.radians(30.0)   # the wheel's angle when cocked (its pegs at 30, 120, 210, 300 degrees)
W_TOT = PULLS * math.pi / 2     # the wheel turns this much as the rope pays out (and back, three quarter turns)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def smooth_keys(keys, f, fn=ease):
    if f <= keys[0][0]:
        return keys[0][1]
    for (fa, a), (fb, b) in zip(keys, keys[1:]):
        if f <= fb:
            k = fn((f - fa) / float(fb - fa)) if fb > fa else 1.0
            return a.lerp(b, k) if isinstance(a, Vector) else a + (b - a) * k
    return keys[-1][1]


# ---------------------------------------------------------------------------------------------- the engine
def _rope_len(a):
    return (vec(cm.ring_pt(a)) - vec(cm.haul_start())).length


L_COCK = _rope_len(cm.COCK)
L_UP = _rope_len(UP)


def arm_for_len(L):
    lo, hi = cm.COCK - 0.2, UP + 0.4
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if _rope_len(m) < L:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def wound(f):
    """How many of the three pulls are done (fractional) at frame f."""
    w = 0.0
    for i in range(PULLS):
        s = CRANK0 + i * (PULL + REGRIP)
        w += ease(min(1.0, max(0.0, (f - s) / float(PULL))))
    return w


def arm_angle(f):
    """The arm: cocked until RELEASE, flying up past upright by THROW, swinging past and back, upright by SETTLE; hauled
    down by the windlass in three jerks (from the rope wound in)."""
    if f <= RELEASE:
        return cm.COCK
    if f <= THROW:
        k = (f - RELEASE) / float(THROW - RELEASE)
        return lerp(cm.COCK, UP + math.radians(8.0), k * k)
    if f < CRANK0:
        k = min(1.0, (f - THROW) / float(SETTLE - THROW))
        d = 1.0 - k
        return UP + math.radians(8.0) * math.cos(k * 2.5 * math.pi) * d ** 1.5 + math.radians(10.0) * math.sin(k * 2.5 * math.pi) * d ** 2
    if f >= CRANK1:
        return cm.COCK
    return arm_for_len(L_UP - (L_UP - L_COCK) * wound(f) / PULLS)


def paid(f):
    """How much of the rope is paid out (0 = cocked, 1 = the arm upright)."""
    if f <= RELEASE or f >= CRANK1:
        return 0.0
    if f < CRANK0:
        return (_rope_len(arm_angle(f)) - L_COCK) / (L_UP - L_COCK)
    return 1.0 - wound(f) / PULLS


def wheel_phi(f):
    """The wheel's angle (about +X): it spins back as the rope pays out, and is hauled round again by its pegs."""
    return PHI_COCK + W_TOT * paid(f)


def hook(f):
    """The trigger hook (degrees about +X): kicked back out of the ring at RELEASE, dropping over it again at CRANK1."""
    if f < RELEASE:
        return 0.0
    if f <= RELEASE + 1:
        return -50.0 * (f - RELEASE + 1) / 2.0
    if f < CRANK1:
        return -50.0
    if f < CRANK1 + 3:
        return -50.0 * (1.0 - ease((f - CRANK1) / 3.0))
    return 0.0


def kick(f):
    """The frame hops at the throw: its back lifts a little (rotating about its front end) and drops again."""
    if f < THROW - 2:
        return 0.0
    k = f - (THROW - 2)
    if k <= 2:
        return 1.6 * k / 2.0
    if k <= 6:
        return 1.6 * (1.0 - (k - 2) / 4.0)
    if k <= 10:
        return -0.4 * math.sin((k - 6) / 4.0 * math.pi)
    return 0.0


def weight_swing(f):
    """The counterweight's swing on its hinge pin (degrees; + = its bottom toward the front, -Y): it lags as it drops,
    swings through and dies away."""
    if f <= RELEASE or f >= CRANK0:
        return 0.0
    t = f - RELEASE
    return 24.0 * math.sin(t / 13.0 * 2 * math.pi) * math.exp(-t / 7.0)


# the sling: its angle in the arm's plane (degrees: 0 = toward the back, +Y; 90 = up; 180 = forward; 270 = down), kept
# continuous (it goes round once as it whips: 194 in the trough -> 495 at the release -> 630 hanging)
_D0 = vec(cm.SLING_REST) - vec(cm.hook_pt(cm.COCK))
TH0 = math.degrees(math.atan2(_D0.z, _D0.y)) % 360.0
TH_THROW = 135.0 + 360.0
TH_HANG = 270.0 + 360.0
POUCH_Z = float(cm.SLING_REST[2])


def pouch_floor(y):
    """What the dragged pouch slides on: the trough, then up over the windlass drum and the trigger post behind it."""
    k = min(1.0, max(0.0, (y - 0.64) / 0.16))
    return POUCH_Z + 0.165 * k * k * (3 - 2 * k)


def _drag_angle(a):
    """While the pouch is still dragged along: the angle that keeps it on what it slides on, a sling's length from the
    prong (None once the prong is high enough for it to swing free)."""
    H = vec(cm.hook_pt(a))
    L = cm.SLING_L
    g = lambda y: (H.y - y) ** 2 + (H.z - pouch_floor(y)) ** 2 - L * L
    if g(H.y) >= 0.0:
        return None
    lo, hi = H.y - L - 0.01, H.y
    for _ in range(50):
        m = 0.5 * (lo + hi)
        if g(m) > 0.0:
            lo = m
        else:
            hi = m
    y = 0.5 * (lo + hi)
    return math.degrees(math.atan2(pouch_floor(y) - H.z, y - H.y)) % 360.0


def _liftoff():
    for f in range(RELEASE, THROW + 1):
        if _drag_angle(arm_angle(f)) is None:
            return f - 1
    return THROW - 2


LIFT = _liftoff()


def sling_angle(f):
    a = arm_angle(f)
    if f <= RELEASE:
        return TH0
    if f <= LIFT:
        return _drag_angle(a)
    if f <= THROW:
        a0 = _drag_angle(arm_angle(LIFT))
        k = (f - LIFT) / float(THROW - LIFT)
        return a0 + (TH_THROW - a0) * k ** 1.7
    if f < CRANK0:                                         # flopping over the top and down, a bounce, then hanging
        keys = [(THROW, TH_THROW), (THROW + 1, 560.0), (THROW + 2, 608.0), (THROW + 3, 642.0), (THROW + 4, 655.0),
                (THROW + 5, 650.0), (THROW + 6, 636.0), (THROW + 7, 626.0), (THROW + 9, 632.0), (THROW + 11, TH_HANG)]
        return smooth_keys(keys, f, fn=lambda x: x)
    if f >= CRANK1:
        return TH0 + 360.0
    # hauled down: the hanging pouch swings forward and settles into the trough as the tip comes down
    s = (UP - a) / (UP - cm.COCK)
    return TH_HANG - (TH_HANG - (TH0 + 360.0)) * min(1.0, max(0.0, s))


def sling_dir(f):
    th = math.radians(sling_angle(f))
    return V(0.0, math.cos(th), math.sin(th))


KP = vec(cm.KICK_P)


def machine(f, a=None):
    """Aims and scales for the engine at frame f."""
    a = arm_angle(f) if a is None else a
    K = Matrix.Rotation(math.radians(kick(f)), 3, "X")
    aims, sc = {}, {}
    aims["frame"] = ("rot", K.to_quaternion())
    aims["arm"] = K @ vec(cm.arm_dir(a))
    ws = math.radians(weight_swing(f))
    aims["weight"] = V(0.0, -math.sin(ws), -math.cos(ws))
    aims["sling"] = K @ sling_dir(f)
    h0 = KP + K @ (vec(cm.haul_start()) - KP)
    h1 = KP + K @ (vec(cm.ring_pt(a)) - KP)
    aims["haul"] = h1 - h0
    sc["haul"] = (1.0, (h1 - h0).length / L_COCK, 1.0)
    # the winch bone points along -X: a twist t about it turns the wheel by -t about +X
    aims["winch"] = (K @ V(-1.0, 0.0, 0.0), -wheel_phi(f))
    ht = vec(cm.hook_tip()) - vec(cm.TRIG_P)
    aims["trigger"] = K @ (Matrix.Rotation(math.radians(hook(f)), 3, "X") @ ht)
    return aims, sc


def peg(phi_deg):
    """Where his fist takes a peg standing at angle phi_deg on the wheel (the frame is still while he winds)."""
    return vec(cm.wheel_handle(math.radians(phi_deg), 0))


# ---------------------------------------------------------------------------------------------- hands
def mallet_grip(arm, grip, hd, face, pole):
    hd = Vector(hd).normalized()
    R = frame_map(M_T, hd, M_F, Vector(face))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF_R, pole=pole)
    aims["hand.R"] = ("frame", M_T, hd, M_F, Vector(face))
    return aims


def left_grip(arm, grip, td, fd, pole):
    R = frame_map(T_L, Vector(td), F_L, Vector(fd))
    aims = arm_aims(arm, "L", Vector(grip) - R @ FIST_OFF_L, pole=pole)
    aims["hand.L"] = ("frame", T_L, Vector(td), F_L, Vector(fd))
    return aims


def left_ball(arm, ball, td, fd, pole):
    R = frame_map(T_L, Vector(td), F_L, Vector(fd))
    aims = arm_aims(arm, "L", Vector(ball) - R @ BALL_IN_L, pole=pole)
    aims["hand.L"] = ("frame", T_L, Vector(td), F_L, Vector(fd))
    return aims


def perp(face, hd):
    hd = Vector(hd).normalized()
    f = Vector(face) - hd * Vector(face).dot(hd)
    return f.normalized()


def shoulder_rest(ro, yaw, br=0.0):
    """The mallet resting on his right shoulder, its head behind him."""
    q = rz(yaw)
    grip = body_pt(J["shoulder_R"], ro, yaw) + q @ V(0.11, -0.22, -0.16 + 0.004 * br)
    hd = q @ V(-0.12, 0.72, 0.68)
    face = q @ V(1.0, 0.0, 0.0)
    return grip, hd, face


# the blow: the mallet's face comes down flat on the peg's head, its handle level
PEG = vec(cm.PIN_TOP)
HD_HIT = V(1.0, 0.0, -0.06).normalized()
FACE_HIT = V(0.0, 0.0, -1.0)
HEAD_HIT = PEG + V(0.0, 0.0, MHL + 0.018)
GRIP_HIT = HEAD_HIT - HD_HIT * ML
G_UP = V(0.16, 0.9, 1.42)                 # raised: his fist above his right shoulder, the head up and back


def swing(t):
    """t = 0: raised (the handle pointing up and back), 1: the face on the peg. Returns grip, hd, face."""
    phi = math.radians(-125.0) * (1.0 - t)
    R = Matrix.Rotation(phi, 3, "Y")
    hd = R @ HD_HIT
    face = R @ FACE_HIT
    g = G_UP.lerp(GRIP_HIT, t) + V(0.05, 0.0, 0.1) * math.sin(math.pi * t)
    return g, hd, face


def propped(ro, yaw):
    """Kneeling: the mallet stood on its face beside his right knee, his fist on the end of the handle."""
    q = rz(yaw)
    head = body_pt(V(-0.05, -0.26, 0.0), ro, yaw)
    head.z = MHL + 0.004
    hd = V(0.0, 0.0, -1.0)
    return head - hd * ML, hd, q @ V(1.0, 0.0, 0.0)


# ---------------------------------------------------------------------------------------------- body
def feet(arm, lf, rf, yaw, lift_l=0.0, lift_r=0.0, kneel_r=0.0, foot_yaw=None):
    """Feet at world (x, y); kneel_r puts his right knee down (the foot behind it on its toes)."""
    q = rz(yaw)
    fy = yaw if foot_yaw is None else foot_yaw
    aims = {}
    for side, p, lift in (("L", lf, lift_l), ("R", rf, lift_r)):
        z = float(J["ankle_" + side][2]) + lift
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        fdir = rz(fy + (-10 if side == "R" else 10)) @ rest_foot
        if side == "R" and kneel_r > 0.0:
            z = lerp(z, 0.13, kneel_r)
            pole = (q @ V(0.0, -1.0, -0.35)).lerp(pole, 1.0 - kneel_r)
            fdir = fdir.lerp(q @ V(0.0, 0.35, -1.0) * fdir.length, kneel_r)
        aims.update(leg_aims(arm, side, V(p[0], p[1], z), pole=pole))
        aims["foot." + side] = fdir
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, br=0.0):
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend + 0.01 * br, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(0.0, -0.16 - 0.25 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(0.0, -0.06 + 0.55 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.04, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.04, 0.02)


def wroot(p):
    """A world position for his root -> the root offset."""
    return V(p[0], p[1], p[2]) - ROOT


# ---------------------------------------------------------------------------------------------- idle / combat
C_YAW = 90.0                       # facing the trigger peg (+X)
C_RO = wroot((0.25, 1.1, 0.76))
C_LF, C_RF = (0.4, 1.25), (0.12, 0.97)
I_YAW = 76.0
I_RO = wroot((0.2, 1.07, 0.79))
I_LF, I_RF = (0.34, 1.25), (0.05, 0.96)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = I_YAW + 4.0 * sway
    ro = I_RO + V(0.012 * sway, 0.0, 0.005 * br)
    aims = feet(arm, I_LF, I_RF, I_YAW)
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
    torso(aims, yaw, bend=0.16, side=0.0, chest=-4.0, look=C_YAW - 4.0, pitch=-0.3 + 0.02 * br, br=br)
    lthigh = body_pt(V(0.21, -0.14, 0.76), ro, yaw)
    aims.update(arm_aims(arm, "L", lthigh + V(0, 0, 0.004 * br), pole=rz(yaw) @ V(1.0, 0.4, 0.2),
                         hand_dir=rz(yaw) @ V(-0.2, -0.3, -1.0)))
    return aims, ro, yaw


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    aims, ro, yaw = combat_core(arm, br, sw)
    g, hd, face = swing(0.0)
    aims.update(mallet_grip(arm, g + V(0.0, 0.0, 0.008 * br), hd, face, pole=rz(yaw) @ V(-1.0, 0.4, -0.3)))
    return aims, ro, rz(yaw), {}, {}


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr, sc, offs = idle_pose(arm, (f % frames) / frames)
        m, s = machine(0)
        aims.update(m)
        sc.update(s)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr, sc, offs = combat_pose(arm, (f % frames) / frames)
        m, s = machine(0)
        aims.update(m)
        sc.update(s)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- the attack
KNEEL_RO = wroot((0.25, 0.5, 0.47))
PICK_RO = wroot((0.14, 0.86, 0.54))
LOAD_RO = wroot((0.4, 0.8, 0.56))
K_RO = [(0, C_RO), (RELEASE, wroot((0.3, 1.1, 0.6))), (8, wroot((0.22, 1.07, 0.78))), (13, wroot((0.2, 1.0, 0.8))),
        (17, wroot((0.22, 0.74, 0.74))), (21, wroot((0.25, 0.54, 0.52))), (CRANK0, KNEEL_RO), (CRANK1, KNEEL_RO),
        (48, wroot((0.2, 0.66, 0.74))), (PICK, PICK_RO), (55, wroot((0.26, 0.86, 0.72))), (PLACE, LOAD_RO),
        (63, wroot((0.3, 0.98, 0.76))), (FR, C_RO)]
K_YAW = [(0, C_YAW), (RELEASE, 92.0), (8, 66.0), (13, 40.0), (17, 70.0), (21, 90.0), (CRANK0, 90.0), (CRANK1, 90.0),
         (48, 165.0), (PICK, 268.0), (55, 320.0), (PLACE, 358.0), (63, 420.0), (FR, C_YAW + 360.0)]
K_BEND = [(0, 0.16), (RELEASE, 0.35), (8, 0.1), (13, 0.0), (17, 0.15), (21, 0.45), (CRANK0, 0.55), (CRANK1, 0.55),
          (48, 0.3), (PICK, 0.8), (55, 0.25), (PLACE, 0.85), (63, 0.25), (FR, 0.16)]
K_SIDE = [(0, 0.0), (55, 0.0), (PLACE, 0.18), (63, 0.0), (FR, 0.0)]
# feet: (frame, left (x, y), right (x, y), right knee down 0..1)
K_FEET = [(0, C_LF, C_RF, 0.0), (RELEASE, C_LF, C_RF, 0.0), (8, C_LF, (0.08, 0.98), 0.0), (13, (0.3, 1.16), (0.08, 0.98), 0.0),
          (17, (0.36, 0.84), (0.1, 0.7), 0.0), (21, (0.48, 0.62), (0.0, 0.36), 0.6), (CRANK0, (0.48, 0.62), (-0.04, 0.34), 1.0),
          (CRANK1, (0.48, 0.62), (-0.04, 0.34), 1.0), (48, (0.34, 0.66), (0.1, 0.56), 0.0), (PICK, (0.035, 0.71), (0.195, 1.0), 0.0),
          (55, (0.35, 0.68), (0.22, 0.98), 0.0), (PLACE, (0.56, 0.64), (0.26, 0.92), 0.0), (63, (0.45, 1.1), (0.18, 0.95), 0.0),
          (FR, C_LF, C_RF, 0.0)]


def feet_at(f):
    for (fa, la, ra, ka), (fb, lb, rb, kb) in zip(K_FEET, K_FEET[1:]):
        if fa <= f <= fb:
            k = ease((f - fa) / float(fb - fa)) if fb > fa else 1.0
            lf = (lerp(la[0], lb[0], k), lerp(la[1], lb[1], k))
            rf = (lerp(ra[0], rb[0], k), lerp(ra[1], rb[1], k))
            ll = 0.07 * math.sin(math.pi * k) if la != lb else 0.0
            rl = 0.07 * math.sin(math.pi * k) if (ra != rb and ka == 0.0 and kb == 0.0) else 0.0
            return lf, rf, ll, rl, lerp(ka, kb, k)
    e = K_FEET[-1]
    return e[1], e[2], 0.0, 0.0, e[3]


PEG_FROM, PEG_TO = 122.0, 32.0        # each pull takes a peg from up near the top round to the back


def pull_state(f):
    """(pulling, k, i): pull i; k = 0..1 through the pull, or through the re-grip after it."""
    t = f - CRANK0
    cyc = PULL + REGRIP
    i = min(PULLS - 1, int(t // cyc))
    u = t - i * cyc
    if u <= PULL:
        return True, u / float(PULL), i
    return False, (u - PULL) / float(REGRIP), i


def attack_pose(arm, f):
    ro = smooth_keys(K_RO, f)
    yaw = smooth_keys(K_YAW, f)
    bend = smooth_keys(K_BEND, f)
    side = smooth_keys(K_SIDE, f)
    lf, rf, ll, rl, kn = feet_at(f)
    crank = CRANK0 <= f <= CRANK1
    if crank:
        pulling, k, _ = pull_state(f)
        heave = math.sin(math.pi * k) if pulling else 0.0
        ro = ro + rz(yaw) @ V(0.0, 0.03 * heave, -0.015 * heave)
        bend = bend - 0.12 * heave
    aims = feet(arm, lf, rf, yaw, lift_l=ll, lift_r=rl, kneel_r=kn, foot_yaw=yaw if f > 14 else C_YAW)
    look = smooth_keys([(0, C_YAW - 4.0), (RELEASE, 90.0), (7, 40.0), (THROW, 10.0), (14, -10.0), (18, 40.0),
                        (CRANK0, 92.0), (CRANK1, 92.0), (48, 190.0), (PICK, 262.0), (55, 330.0), (PLACE, 372.0),
                        (63, 425.0), (FR, C_YAW + 356.0)], f)
    pitch = smooth_keys([(0, -0.3), (RELEASE, -0.6), (7, 0.2), (THROW, 0.75), (14, 0.35), (18, 0.0), (CRANK0, -0.3),
                         (CRANK1, -0.25), (48, -0.3), (PICK, -0.6), (55, -0.1), (PLACE, -0.55), (63, -0.1), (FR, -0.3)], f)
    torso(aims, yaw, bend=bend, side=side, chest=smooth_keys([(0, -4.0), (RELEASE, 8.0), (8, 0.0), (FR, -4.0)], f),
          look=look, pitch=pitch)
    sc, offs = {}, {}
    q = rz(yaw)
    # ---- right hand: the mallet. The blow; on his shoulder while he watches and walks; propped by his knee while he
    # winds; on his shoulder again while he fetches and loads; raised.
    if f <= RELEASE:
        t = f / float(RELEASE)
        g, hd, face = swing(t * t)
        pole = q @ V(-1.0, 0.3, -0.4)
    elif f < 19:
        k = ease(min(1.0, (f - RELEASE) / 7.0))
        g0, hd0, face0 = swing(1.0)
        g1, hd1, face1 = shoulder_rest(ro, yaw)
        g = g0.lerp(g1, k) + V(0, 0, 0.12 * math.sin(math.pi * k))
        hd = hd0.lerp(hd1, k).normalized()
        face = perp(face0.lerp(face1, k), hd)
        pole = q @ V(-1.0, 0.2, -0.5)
    elif f < CRANK0:
        k = ease((f - 19) / float(CRANK0 - 19))
        g0, hd0, face0 = shoulder_rest(ro, yaw)
        g1, hd1, face1 = propped(ro, yaw)
        g = g0.lerp(g1, k)
        hd = hd0.lerp(hd1, k).normalized()
        face = perp(face0.lerp(face1, k), hd)
        pole = q @ V(-1.0, 0.1, -0.3)
    elif f <= CRANK1:
        g, hd, face = propped(ro, yaw)
        pole = q @ V(-1.0, 0.1, -0.3)
    elif f < 48:
        k = ease((f - CRANK1) / float(48 - CRANK1))
        g0, hd0, face0 = propped(ro, yaw)
        g1, hd1, face1 = shoulder_rest(ro, yaw)
        g = g0.lerp(g1, k)
        hd = hd0.lerp(hd1, k).normalized()
        face = perp(face0.lerp(face1, k), hd)
        pole = q @ V(-1.0, 0.2, -0.5)
    elif f < 63:
        g, hd, face = shoulder_rest(ro, yaw)
        pole = q @ V(-1.0, 0.2, -0.5)
    else:
        k = ease((f - 63) / float(FR - 63))
        g0, hd0, face0 = shoulder_rest(ro, yaw)
        g1, hd1, face1 = swing(0.0)
        g = g0.lerp(g1, k)
        hd = hd0.lerp(hd1, k).normalized()
        face = perp(face0.lerp(face1, k), hd)
        pole = q @ V(-1.0, 0.4, -0.3)
    aims.update(mallet_grip(arm, g, hd, face, pole))
    # ---- left hand: his thigh; the wheel's pegs; the stone
    lthigh = body_pt(V(0.21, -0.14, 0.76), ro, yaw)
    lhip = body_pt(V(0.3, -0.12, 0.86), ro, yaw)
    td_peg, fd_peg = V(-1.0, 0.0, 0.0), V(0.0, -0.25, -1.0)
    if f < 15:
        aims.update(arm_aims(arm, "L", lthigh, pole=q @ V(1.0, 0.4, 0.2), hand_dir=q @ V(-0.2, -0.3, -1.0)))
    elif f < CRANK0:                                                 # reaching for the first peg
        k = ease((f - 15) / float(CRANK0 - 15))
        tgt = peg(PEG_FROM)
        R = frame_map(T_L, td_peg, F_L, fd_peg)
        wr_t = tgt - R @ FIST_OFF_L
        aims.update(arm_aims(arm, "L", lthigh.lerp(wr_t, k), pole=V(0.2, 1.0, -0.4)))
        if k > 0.5:
            aims["hand.L"] = ("frame", T_L, td_peg, F_L, fd_peg)
        else:
            aims["hand.L"] = (q @ V(-0.2, -0.3, -1.0)).lerp(V(0.6, 0.0, -0.8), k * 2)
    elif f <= CRANK1:
        pulling, k, i = pull_state(f)
        if pulling:                                                  # hauling a peg round
            ang = PEG_FROM + (PEG_TO - PEG_FROM) * ease(k)
            aims.update(left_grip(arm, peg(ang), td_peg, fd_peg, pole=V(0.2, 1.0, -0.4)))
        else:                                                        # letting go, back up to the next peg
            p0, p1 = peg(PEG_TO), peg(PEG_FROM)
            g = p0.lerp(p1, ease(k)) + V(-0.06, 0.0, 0.06) * math.sin(math.pi * k)
            aims.update(left_grip(arm, g, td_peg, fd_peg, pole=V(0.2, 1.0, -0.4)))
    elif f <= PICK:                                                  # letting go of the peg; down to the heap
        top = vec(cm.CARRY_C)
        td_b, fd_b = q @ V(-1.0, 0.0, 0.0), q @ V(0.0, -1.0, -0.4)  # palm down, fingers ahead (his thumb to his right)
        if f <= 48:
            k = ease((f - CRANK1) / float(48 - CRANK1))
            R0 = frame_map(T_L, td_peg, F_L, fd_peg)
            wr = (peg(PEG_TO) - R0 @ FIST_OFF_L).lerp(lhip, k)
            aims.update(arm_aims(arm, "L", wr, pole=q @ V(1.0, 0.3, -0.2), hand_dir=q @ V(-0.2, -0.3, -1.0)))
        else:
            k = ease((f - 48) / float(PICK - 48))
            Rb = frame_map(T_L, td_b, F_L, fd_b)
            wr = lhip.lerp(top - Rb @ BALL_IN_L, k)
            aims.update(arm_aims(arm, "L", wr, pole=q @ V(1.0, 0.3, -0.4)))
            aims["hand.L"] = ("frame", T_L, td_b, F_L, fd_b)
    elif f <= PLACE:                                                 # carrying it to the pouch
        top = vec(cm.CARRY_C)
        cup = vec(cm.SLING_REST) + V(0.0, 0.0, 0.01)
        k = ease((f - PICK) / float(PLACE - PICK))
        b = top.lerp(cup, k) + V(0, 0, 0.42 * math.sin(math.pi * k))
        # the hand turns with him: palm down throughout, fingers from ahead to his left side
        td = (q @ V(-1.0, 0.0, 0.0)).lerp(q @ V(0.0, -1.0, 0.0), k)
        fd = (q @ V(0.0, -1.0, -0.4)).lerp(q @ V(1.0, 0.0, -0.4), k)
        aims.update(left_ball(arm, b, td, fd, pole=q @ V(1.0, 0.3, -0.4)))
        offs["carry"] = b - top
    else:                                                            # lifting his hand out, back to his thigh
        cup = vec(cm.SLING_REST)
        td, fd = q @ V(0.0, -1.0, 0.0), q @ V(1.0, 0.0, -0.4)
        Rb = frame_map(T_L, td, F_L, fd)
        wr_a = cup + V(0, 0, 0.06) - Rb @ BALL_IN_L
        if f <= PLACE + 3:
            k = ease((f - PLACE) / 3.0)
            wr = wr_a.lerp(lhip, k) + V(0, 0, 0.12 * math.sin(math.pi * k))
            aims.update(arm_aims(arm, "L", wr, pole=q @ V(1.0, 0.4, 0.2)))
            aims["hand.L"] = ("frame", T_L, td, F_L, fd) if k < 0.5 else q @ V(-0.2, -0.3, -1.0)
        else:
            k = ease((f - PLACE - 3) / float(FR - PLACE - 3))
            aims.update(arm_aims(arm, "L", lhip.lerp(lthigh, k), pole=q @ V(1.0, 0.4, 0.2), hand_dir=q @ V(-0.2, -0.3, -1.0)))
        if f < PLACE + 2:
            offs["carry"] = cup - vec(cm.CARRY_C)
    # ---- the engine
    m, s = machine(f)
    aims.update(m)
    sc.update(s)
    sc["stone"] = 1.0 if (f < THROW or f >= PLACE) else 0.0
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
