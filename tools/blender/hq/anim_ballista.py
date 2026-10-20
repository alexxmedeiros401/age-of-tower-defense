"""Ballista clips (30 fps).

Idle   : the ballista drawn and loaded; he stands back from it with the mallet resting on his shoulder, his left fist on
         his hip, breathes, shifts his weight and looks about.
Combat : ready to shoot: squared up to the back of the stock with the mallet raised over his right shoulder, his left
         hand on his thigh.
Attack : (66 frames = the 2.2 s cooldown) he brings the mallet down on the knob of the claw's lever (RELEASE): the claw
         tips open, the string snaps forward and the arms slam against the frame; the bolt is gone (LAUNCH: game.gd flies
         it from the groove) and the whole engine rocks forward onto its front feet. He shoulders the mallet, turns to
         the stock and shoves the slider forward along it until the claw drops over the string (HOOK), steps back to the
         windlass and winds it all back (the arms draw back with the string), turns to the bundle of bolts behind him,
         stoops for the top one, carries it round and lays it in the groove (PLACE), and raises the mallet again.

The ballista's bones are posed directly: frame (the stand and stock: it rocks about its front feet), arm_n / arm_f (on
their skeins), str_n / str_f (each half of the string, from its arm's tip: aimed at the string's middle and stretched to
reach it), slider (run along the stock: a parentless bone posed by its whole matrix), trigger (the claw, on its pin),
winch (drum and crank, turned about their axle), haul (the rope from the drum to the claw block: aimed and stretched),
bolt (in the groove), carry (the bolt he carries: posed by its whole matrix)."""
import math
from mathutils import Vector, Quaternion, Matrix
import ballista as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
Z = V(0.0, 0.0, 1.0)

_G, _T, _Fv = cm.mallet_frame()
M_T, M_F = vec(_T), vec(_Fv)
_wrR, _fR, _nR, _tR = cm.hand_frame("R")
FIST_OFF_R = vec(cm.fist_center("R") - _wrR)
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
T_L, F_L, N_L = vec(_tL), vec(_fL), vec(_nL)
FIST_OFF_L = vec(cm.fist_center("L") - _wrL)
ML = cm.MALLET_L
HL = cm.MALLET_HEAD[1]

RELEASE = 3        # the mallet lands on the claw's lever: the claw tips open
LAUNCH = 4         # the string has driven the bolt out of the groove (game.gd flies it from here)
SNAP = 5           # the arms hit the frame
PUSH0, HOOK = 12, 20          # he shoves the slider forward; the claw drops over the string
CRANK0, CRANK1 = 25, 41       # winding back
GRAB = 45          # his hand closes on the top bolt of the bundle
LIFT = 49          # ... lifted off it, standing up
PRE = 52           # the bolt over the groove, its point in the frame's window
PLACE = 57         # the bolt in the groove
FR = 66            # = the 2.2 s cooldown


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


# ---------------------------------------------------------------------------------------------- the ballista
STR_REST = (vec(cm.claw_pt()) - vec(cm.arm_tip(-1, cm.COCKED))).length      # a string half's rest length
HAUL_REST = (vec(cm.haul_end()) - vec(cm.haul_start())).length
KP = vec(cm.KICK_P)


def kick_rot(deg):
    return Matrix.Rotation(math.radians(deg), 3, "X")


def drum_for(claw):
    """Radians the drum has paid out (from drawn) when the claw is at y = claw."""
    return ((vec(cm.haul_end(claw)) - vec(cm.haul_start())).length - HAUL_REST) / cm.DRUM_R


DRUM_MAX = drum_for(cm.CLAW_LOOSE)


def claw_for_drum(dr):
    """The claw's y when the drum has paid out dr radians (bisection: the rope grows as the claw goes forward)."""
    lo, hi = cm.CLAW_LOOSE - 0.05, cm.CLAW_COCK + 0.05
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if drum_for(m) > dr:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def machine(th, mid, slide, drum, trig_deg=0.0, kick_deg=0.0):
    """Aims and scales for the ballista: the arms at sweep th, the string's middle at y = mid, the slider's claw at
    y = slide, the drum turned by `drum` radians from drawn (+ = paying out), the claw tipped open by trig_deg, the whole
    rocked forward onto its front feet by kick_deg. The slider's aim is ('slide', transform): solve_world() turns it
    into a 'world' aim on the bone's rest matrix."""
    K = kick_rot(kick_deg)
    aims, sc = {}, {}
    aims["frame"] = ("rot", K.to_quaternion())
    world = lambda p: KP + K @ (vec(p) - KP)
    m = world(cm.claw_pt(mid))
    for side, nm in ((-1, "n"), (1, "f")):
        aims["arm_" + nm] = K @ vec(cm.arm_dir(side, th))
        tip = world(cm.arm_tip(side, th))
        aims["str_" + nm] = m - tip
        sc["str_" + nm] = (1.0, (m - tip).length / STR_REST, 1.0)
    aims["slider"] = ("slide", Matrix.Translation(KP) @ K.to_4x4() @ Matrix.Translation(-KP)
                      @ Matrix.Translation(V(0.0, slide - cm.CLAW_COCK, 0.0)))
    aims["trigger"] = K @ (Matrix.Rotation(math.radians(-trig_deg), 3, "X") @ V(0.0, 0.11, 0.075))
    h0 = world(cm.haul_start())
    h1 = world(cm.haul_end(slide))
    aims["haul"] = h1 - h0
    sc["haul"] = (1.0, (h1 - h0).length / HAUL_REST, 1.0)
    # the winch bone points along -X: a twist t about it turns the drum by -t about +X; paying out turns it by +drum
    # (the rope leaves the drum's top toward the slider, so the top rolls forward)
    aims["winch"] = (K @ V(-1.0, 0.0, 0.0), -drum)
    return aims, sc


def solve_world(P, aims):
    """'slide' aims (a transform applied to the bone's rest matrix) -> 'world' aims."""
    for nm, a in list(aims.items()):
        if isinstance(a, tuple) and a and a[0] == "slide":
            aims[nm] = ("world", a[1] @ P.rest[nm])


def crank_grip(drum):
    """Where his left fist holds the crank handle (its middle) when the drum has paid out `drum` radians."""
    h0, h1 = cm.crank_handle(cm.CRANK_PHI + drum)
    return vec(h0).lerp(vec(h1), 0.55)


def machine_drawn(aims, sc):
    m, s = machine(cm.COCKED, cm.CLAW_COCK, cm.CLAW_COCK, 0.0)
    aims.update(m)
    sc.update(s)


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


def left_wrist(grip, td, fd):
    return Vector(grip) - frame_map(T_L, Vector(td), F_L, Vector(fd)) @ FIST_OFF_L


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


# the blow: an overhead swing in the vertical plane through his right shoulder and the knob on the claw's lever; at
# the blow the handle is a little below level and the head's face comes down on the knob
SH_S = V(0.18, -0.37, 1.3)                     # his right shoulder squared up to the stock (strike stance)
TAIL = vec(cm.TRIG_P) + V(0.0, 0.11, 0.075)    # the knob
H_S = V(TAIL.x - SH_S.x, TAIL.y - SH_S.y, 0.0).normalized()
SWING_AX = H_S.cross(Z).normalized()           # (his right) turning the handle about it (+) lifts the head up and back
DELTA = math.radians(14.0)
HD_HIT = (H_S * math.cos(DELTA) - Z * math.sin(DELTA)).normalized()
FACE_HIT = HD_HIT.cross(SWING_AX).normalized()  # down (and a little back toward him): the way the blow goes
HEAD_HIT = TAIL - FACE_HIT * (HL + 0.017)
GRIP_HIT = HEAD_HIT - HD_HIT * ML
RAISE = math.radians(145.0)
GRIP_UP = SH_S + H_S * 0.1 + Z * 0.26 + SWING_AX * 0.04


def swing(t):
    """t = 0: raised (the head up behind his right shoulder), 1: on the knob. Returns grip, hd, face."""
    R = Matrix.Rotation(RAISE * (1.0 - t), 3, SWING_AX)
    hd = R @ HD_HIT
    face = hd.cross(SWING_AX).normalized()
    g = GRIP_UP.lerp(GRIP_HIT, t) + (Z * 0.05 + H_S * 0.04) * math.sin(math.pi * t)
    return g, hd, face


# ---------------------------------------------------------------------------------------------- body
def feet(arm, lf, rf, yaw, lift_l=0.0, lift_r=0.0, foot_yaw=None):
    """Ankles at world (x, y) lf / rf."""
    q = rz(yaw)
    fy = yaw if foot_yaw is None else foot_yaw
    aims = {}
    for side, p, lift in (("L", lf, lift_l), ("R", rf, lift_r)):
        z = float(J["ankle_" + side][2]) + lift
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        fdir = rz(fy + (-10 if side == "R" else 10)) @ rest_foot
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
    aims["chest"] = (qc @ tilt(bend + 0.01 * br, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(0.0, -0.16 - 0.25 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(0.0, -0.06 + 0.55 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.04, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.04, 0.02)


# ---------------------------------------------------------------------------------------------- idle / combat
STAND_RO = V(-0.1, 0.02, 0.0)
STAND_YAW = 30.0
STAND_LF = (0.06, 0.18)
STAND_RF = (-0.26, -0.08)
S_RO = V(0.12, -0.03, -0.06)        # squared up to the stock (the blow, and the windlass)
S_YAW = 80.0
S_BEND = 0.25
S_LF = (0.27, 0.17)
S_RF = (-0.01, -0.17)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = STAND_YAW + 4.0 * sway
    ro = STAND_RO + V(0.012 * sway, 0.0, -0.006 + 0.005 * br)
    aims = feet(arm, STAND_LF, STAND_RF, STAND_YAW)
    look = yaw + 35.0 * math.sin(w) + 10.0 * math.sin(w * 3)
    torso(aims, yaw, bend=0.02, side=0.03 * sway, chest=2.0 * sway, look=look, pitch=0.05 + 0.03 * br, br=br)
    g, hd, face = shoulder_rest(ro, yaw, br)
    aims.update(mallet_grip(arm, g, hd, face, pole=rz(yaw) @ V(-1.0, 0.3, -0.6)))
    hip = body_pt(V(0.27, 0.0, 0.94), ro, yaw)
    aims.update(arm_aims(arm, "L", hip + V(0, 0, 0.004 * br), pole=rz(yaw) @ V(1.0, 0.5, 0.1),
                         hand_dir=rz(yaw) @ V(-0.35, 0.25, -1.0)))
    return aims, ro, rz(yaw), {}


def hip_pt(ro, yaw):
    return body_pt(V(0.27, 0.0, 0.94), ro, yaw)


def left_on_hip(arm, ro, yaw, br=0.0):
    return arm_aims(arm, "L", hip_pt(ro, yaw) + V(0, 0, 0.004 * br), pole=rz(yaw) @ V(1.0, 0.5, 0.1),
                    hand_dir=rz(yaw) @ V(-0.35, 0.25, -1.0))


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    yaw = S_YAW + 1.5 * sw
    ro = S_RO + V(0.0, 0.0, 0.007 * br)
    aims = feet(arm, S_LF, S_RF, S_YAW)
    torso(aims, yaw, bend=S_BEND, chest=4.0, look=S_YAW + 6.0, pitch=-0.25 + 0.02 * br, br=br)
    aims.update(left_on_hip(arm, ro, yaw, br))
    g, hd, face = swing(0.0)
    aims.update(mallet_grip(arm, g + V(0.0, 0.0, 0.008 * br), hd, face, pole=SWING_AX + V(0, 0, -0.4)))
    return aims, ro, rz(yaw), {}


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr, sc = idle_pose(arm, (f % frames) / frames)
        machine_drawn(aims, sc)
        solve_world(P, aims)
        ch, _ = P.solve(aims, ro, rr, scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr, sc = combat_pose(arm, (f % frames) / frames)
        machine_drawn(aims, sc)
        solve_world(P, aims)
        ch, _ = P.solve(aims, ro, rr, scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- the attack: the engine
def slide_at(f):
    """The claw's y on the slider: drawn until he shoves it forward to the string (PUSH0-HOOK), then wound back by the
    windlass (from the drum's turn)."""
    if f <= PUSH0:
        return cm.CLAW_COCK
    if f <= HOOK:
        k = ease((f - PUSH0) / float(HOOK - PUSH0))
        return lerp(cm.CLAW_COCK, cm.CLAW_LOOSE, k)
    return claw_for_drum(drum_turn(f))


def drum_turn(f):
    """Radians the drum has paid out (0 = drawn)."""
    if f <= PUSH0:
        return 0.0
    if f <= HOOK:
        return drum_for(slide_at(f))
    if f < CRANK0:
        return DRUM_MAX
    if f >= CRANK1:
        return 0.0
    k = (f - CRANK0) / float(CRANK1 - CRANK0)
    k = k * k * (3 - 2 * k) * 0.35 + k * 0.65                 # steady cranking, easing in and out a little
    return DRUM_MAX * (1.0 - k)


def string_mid(f):
    """The string's middle: on the claw until RELEASE, snapping forward until it is straight (SNAP), on the claw again
    from HOOK."""
    if f <= RELEASE:
        return cm.CLAW_COCK
    if f <= SNAP:
        k = (f - RELEASE) / float(SNAP - RELEASE)
        return lerp(cm.CLAW_COCK, cm.CLAW_LOOSE, k * k)
    if f < HOOK:
        return cm.CLAW_LOOSE
    return slide_at(f)


def arm_sweep(f):
    """The arms follow the string; they quiver a moment against the frame after the shot."""
    th = cm.arm_for_claw(string_mid(f))
    if SNAP < f < 12:
        k = (f - SNAP) / float(12 - SNAP)
        th = cm.LOOSE - math.radians(4.0) * math.sin(k * math.pi * 2.5) * (1.0 - k)
    return th


def trig(f):
    """The claw: tipped open by the blow, closing over the string as the slider reaches it."""
    if f < RELEASE:
        return 0.0
    if f <= RELEASE + 1:
        return 48.0 * (f - RELEASE + 1) / 2.0
    if f < HOOK - 2:
        return 48.0
    if f <= HOOK:
        return 48.0 * (HOOK - f) / 2.0
    return 0.0


def kick(f):
    if f < SNAP - 1:
        return 0.0
    k = f - (SNAP - 1)
    if k <= 2:
        return 2.2 * k / 2.0
    if k <= 5:
        return 2.2 * (1.0 - (k - 2) / 3.0)
    if k <= 8:
        return 0.6 * math.sin((k - 5) / 3.0 * math.pi)
    return 0.0


# ---------------------------------------------------------------------------------------------- the attack: him
K_RO = [(0, S_RO), (RELEASE, V(0.17, -0.05, -0.12)), (7, V(0.13, -0.03, -0.07)), (PUSH0, V(0.2, -0.18, -0.1)),
        (HOOK, V(0.2, -0.35, -0.13)), (CRANK0, V(0.1, -0.01, -0.1)), (CRANK1, V(0.1, -0.01, -0.1)),
        (GRAB, V(0.0, -0.08, -0.34)), (GRAB + 1, V(0.0, -0.08, -0.34)), (LIFT, V(0.08, -0.1, -0.1)),
        (PRE, V(0.2, -0.33, -0.1)), (PLACE, V(0.22, -0.36, -0.14)), (61, V(0.15, -0.12, -0.07)), (FR, S_RO)]
K_YAW = [(0, S_YAW), (RELEASE, 86.0), (7, 80.0), (PUSH0, 20.0), (HOOK, 15.0), (CRANK0, 90.0), (CRANK1, 90.0),
         (GRAB, 125.0), (GRAB + 1, 125.0), (LIFT, 75.0), (PRE, 25.0), (PLACE, 22.0), (61, 60.0), (FR, S_YAW)]
K_BEND = [(0, S_BEND), (RELEASE, 0.45), (7, 0.2), (PUSH0, 0.3), (HOOK, 0.45), (CRANK0, 0.3), (CRANK1, 0.3),
          (GRAB, 1.0), (GRAB + 1, 1.0), (LIFT, 0.35), (PRE, 0.3), (PLACE, 0.45), (61, 0.2), (FR, S_BEND)]
# feet: (frame, left ankle (x, y), right ankle (x, y)); one foot steps (lifts) at a time
K_FEET = [(0, S_LF, S_RF), (7, S_LF, S_RF),
          (11, (0.34, -0.14), S_RF), (15, (0.34, -0.14), (0.04, -0.3)), (HOOK, (0.37, -0.42), (0.04, -0.3)),
          (23, (0.3, 0.06), (0.04, -0.3)), (CRANK0, (0.3, 0.06), (-0.02, -0.16)), (CRANK1, (0.3, 0.06), (-0.02, -0.16)),
          (43, (-0.06, 0.14), (-0.02, -0.16)), (GRAB, (-0.06, 0.14), (0.08, -0.24)), (GRAB + 1, (-0.06, 0.14), (0.08, -0.24)),
          (LIFT, (0.2, -0.12), (0.08, -0.24)), (PRE, (0.2, -0.12), (0.0, -0.32)), (PLACE, (0.36, -0.36), (0.0, -0.32)),
          (61, (0.36, -0.36), S_RF), (FR, S_LF, S_RF)]


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


# his left hand on the claw block (shoving it), on the crank, round the bolt
PUSH_TD, PUSH_FD = V(0.0, -0.3, 1.0), V(1.0, 0.0, -0.25)
CRANK_TD, CRANK_FD = V(1.0, 0.0, 0.0), V(0.0, -0.3, -1.0)
BOLT_FD = V(0.0, 0.0, -1.0)


def push_grip(slide):
    """His left fist round the near cheek of the claw block (the slider's claw at y = slide)."""
    return V(cm.MX - cm.SLW - 0.04, cm.slider_back(slide) - 0.026, cm.SL_TOP + 0.02)


PILE_MID = vec(cm.CARRY_C)                      # the top bolt's middle, lying along +X
GROOVE_MID = vec(cm.bolt_nock()) + V(0.0, -cm.BOLT_L * 0.5, 0.0)


def bolt_axis(pitch_deg):
    """Along -Y (toward the frame), its point dipped by pitch_deg."""
    p = math.radians(pitch_deg)
    return V(0.0, -math.cos(p), -math.sin(p))


NOCK_PRE = vec(cm.bolt_nock()) + V(0.0, 0.2, 0.14)          # the bolt over the groove, its point dipped into the window
PITCH_PRE = math.degrees(math.asin(0.11 / cm.BOLT_L))
NOCK_IN = vec(cm.bolt_nock()) + V(0.0, -0.02, 0.06)          # slid forward, the nock just in front of the claw
PITCH_IN = math.degrees(math.asin(0.05 / cm.BOLT_L))
BOLT_KEYS = [(GRAB + 1, PILE_MID, V(1.0, 0.0, 0.0)),
             (LIFT, PILE_MID + V(0.12, -0.12, 0.5), V(0.7, -0.7, 0.1).normalized()),
             (PRE, NOCK_PRE + bolt_axis(PITCH_PRE) * (cm.BOLT_L * 0.5), bolt_axis(PITCH_PRE)),
             (PLACE - 2, NOCK_IN + bolt_axis(PITCH_IN) * (cm.BOLT_L * 0.5), bolt_axis(PITCH_IN)),
             (PLACE, GROOVE_MID, bolt_axis(0.0))]
HOLD = 0.045                                                 # his fist's centre above the bolt's axis


def bolt_path(f):
    """The carried bolt's middle and axis (GRAB-PLACE): lifted off the bundle as he stands, swung round over the
    stock, its point put through the frame's window, then slid forward and down into the groove."""
    if f <= BOLT_KEYS[0][0]:
        return BOLT_KEYS[0][1], BOLT_KEYS[0][2]
    for (fa, ma, aa), (fb, mb, ab) in zip(BOLT_KEYS, BOLT_KEYS[1:]):
        if f <= fb:
            k = ease((f - fa) / float(fb - fa))
            return ma.lerp(mb, k), aa.lerp(ab, k).normalized()
    return BOLT_KEYS[-1][1], BOLT_KEYS[-1][2]


def hold_pt(mid, axis):
    """His fist's centre holding the bolt (from above) by its middle."""
    up = Z - Vector(axis) * Z.dot(Vector(axis))
    return Vector(mid) + up.normalized() * HOLD


def bolt_world(arm, mid, axis):
    """The carry bone's pose matrix: the bolt (its rest along +X, its middle at PILE_MID) moved to `mid`, along `axis`."""
    R = Vector(axis).normalized().to_track_quat("X", "Z").to_matrix().to_4x4()
    M = Matrix.Translation(Vector(mid)) @ R @ Matrix.Translation(-PILE_MID)
    return ("world", M @ arm.data.bones["carry"].matrix_local)


def attack_pose(arm, f):
    ro = smooth_keys(K_RO, f)
    yaw = smooth_keys(K_YAW, f)
    bend = smooth_keys(K_BEND, f)
    lf, rf, ll, rl = feet_at(f)
    crank = CRANK0 <= f <= CRANK1
    if crank:                                                       # heaving with each half turn
        ro = ro + rz(yaw) @ V(0.0, -0.02, 0.01) * math.sin(drum_turn(f) * 2.0)
    aims = feet(arm, lf, rf, yaw, lift_l=ll, lift_r=rl)
    # where he looks: the knob, the shot going, the slider, the windlass, the bundle, the groove, the field again
    look = smooth_keys([(0, S_YAW + 6.0), (RELEASE, 90.0), (6, 10.0), (10, 0.0), (PUSH0, 30.0), (HOOK, 20.0),
                        (CRANK0, 96.0), (CRANK1, 96.0), (GRAB, 130.0), (LIFT, 60.0), (PRE, 30.0), (PLACE, 26.0),
                        (61, 40.0), (FR, S_YAW + 6.0)], f)
    pitch = smooth_keys([(0, -0.25), (RELEASE, -0.5), (6, 0.1), (9, 0.3), (PUSH0, -0.3), (HOOK, -0.3), (CRANK0, -0.3),
                         (CRANK1, -0.3), (GRAB, -0.5), (LIFT, -0.2), (PRE, -0.35), (PLACE, -0.45), (61, 0.0), (FR, -0.25)], f)
    torso(aims, yaw, bend=bend, chest=smooth_keys([(0, 4.0), (RELEASE, 10.0), (8, 0.0), (61, 0.0), (FR, 4.0)], f),
          look=look, pitch=pitch)
    sc = {}
    q = rz(yaw)
    # ---- right hand: the mallet
    if f <= RELEASE + 2:                                            # the blow (holding on the knob a moment)
        t = min(1.0, f / float(RELEASE))
        g, hd, face = swing(t * t)
        pole = SWING_AX + V(0, 0, -0.4)
    elif f <= 9:                                                    # onto his shoulder
        k = ease((f - RELEASE - 2) / (9.0 - RELEASE - 2))
        g1, hd1, face1 = shoulder_rest(ro, yaw)
        g0, hd0, face0 = swing(1.0)
        g = g0.lerp(g1, k) + Z * (0.1 * math.sin(math.pi * k))
        hd = hd0.lerp(hd1, k).normalized()
        face = perp(face0.lerp(face1, k), hd)
        pole = (SWING_AX + V(0, 0, -0.4)).lerp(q @ V(-1.0, 0.2, -0.5), k)
    elif f < 60:                                                    # on his shoulder while he works
        g, hd, face = shoulder_rest(ro, yaw)
        pole = q @ V(-1.0, 0.2, -0.5)
    else:                                                           # raise it, ready for the next shot
        k = ease((f - 60) / float(FR - 60))
        g1, hd1, face1 = shoulder_rest(ro, yaw)
        g0, hd0, face0 = swing(0.0)
        g = g1.lerp(g0, k)
        hd = hd1.lerp(hd0, k).normalized()
        face = perp(face1.lerp(face0, k), hd)
        pole = (q @ V(-1.0, 0.2, -0.5)).lerp(SWING_AX + V(0, 0, -0.4), k)
    aims.update(mallet_grip(arm, g, hd, face, pole))
    # ---- left hand: his hip, the claw block, the crank, the bolt
    if f < 7:
        aims.update(left_on_hip(arm, ro, yaw))
    elif f < PUSH0:                                                 # reach for the claw block
        k = ease((f - 7) / float(PUSH0 - 7))
        wr = hip_pt(ro, yaw).lerp(left_wrist(push_grip(cm.CLAW_COCK), PUSH_TD, PUSH_FD), k)
        aims.update(arm_aims(arm, "L", wr + Z * (0.08 * math.sin(math.pi * k)), pole=q @ V(1.0, 0.4, -0.3)))
        aims["hand.L"] = ("frame", T_L, PUSH_TD, F_L, PUSH_FD) if k > 0.5 else q @ V(-0.35, 0.25, -1.0)
    elif f <= HOOK:                                                 # shoving the slider along to the string
        aims.update(left_grip(arm, push_grip(slide_at(f)), PUSH_TD, PUSH_FD, pole=q @ V(1.0, 0.4, -0.3)))
    elif f < CRANK0:                                                # to the crank
        k = ease((f - HOOK) / float(CRANK0 - HOOK))
        wa = left_wrist(push_grip(cm.CLAW_LOOSE), PUSH_TD, PUSH_FD)
        wb = left_wrist(crank_grip(DRUM_MAX), CRANK_TD, CRANK_FD)
        aims.update(arm_aims(arm, "L", wa.lerp(wb, k) + Z * (0.1 * math.sin(math.pi * k)), pole=q @ V(1.0, 0.4, -0.3)))
        aims["hand.L"] = ("frame", T_L, PUSH_TD.lerp(CRANK_TD, k).normalized(), F_L, PUSH_FD.lerp(CRANK_FD, k))
    elif f <= CRANK1:                                               # winding
        aims.update(left_grip(arm, crank_grip(drum_turn(f)), CRANK_TD, CRANK_FD, pole=V(0.0, 1.0, -0.6)))
    elif f <= GRAB:                                                 # let go, reach down for the bundle
        k = ease((f - CRANK1) / float(GRAB - CRANK1))
        wa = left_wrist(crank_grip(0.0), CRANK_TD, CRANK_FD)
        over = hold_pt(PILE_MID, V(1.0, 0.0, 0.0)) + Z * (0.1 * (1.0 - ease(max(0.0, (k - 0.6) / 0.4))))
        wb = left_wrist(over, V(1.0, 0.0, 0.0), BOLT_FD)
        aims.update(arm_aims(arm, "L", wa.lerp(wb, min(1.0, k / 0.8)), pole=q @ V(1.0, 0.3, -0.4)))
        aims["hand.L"] = ("frame", T_L, CRANK_TD.lerp(V(1.0, 0.0, 0.0), k).normalized(), F_L, CRANK_FD.lerp(BOLT_FD, k))
    elif f <= PLACE:                                                # the bolt in his fist
        mid, ax = bolt_path(f)
        aims.update(left_grip(arm, hold_pt(mid, ax), ax, BOLT_FD, pole=q @ V(1.0, 0.3, -0.4)))
        if f > GRAB + 1:
            aims["carry"] = bolt_world(arm, mid, ax)
    else:                                                           # back to his hip
        k = ease((f - PLACE) / float(FR - PLACE))
        if f < PLACE + 2:                                           # (hidden: it stays in the groove)
            aims["carry"] = bolt_world(arm, GROOVE_MID, bolt_axis(0.0))
        wa = left_wrist(hold_pt(GROOVE_MID, bolt_axis(0.0)) + Z * 0.04, bolt_axis(0.0), BOLT_FD)
        aims.update(arm_aims(arm, "L", wa.lerp(hip_pt(ro, yaw), k) + Z * (0.06 * math.sin(math.pi * k)),
                             pole=q @ V(1.0, 0.5, 0.1), hand_dir=q @ V(-0.35, 0.25, -1.0)))
    # ---- the ballista
    m, s = machine(arm_sweep(f), string_mid(f), slide_at(f), drum_turn(f), trig(f), kick(f))
    aims.update(m)
    sc.update(s)
    sc["bolt"] = 1.0 if (f < LAUNCH or f >= PLACE) else 0.0
    sc["carry"] = 0.0 if PLACE <= f < PLACE + 2 else 1.0
    return aims, ro, rz(yaw), sc


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, rr, sc = attack_pose(arm, f)
        solve_world(P, aims)
        ch, _ = P.solve(aims, ro, rr, scales=sc)
        P.key(ch, f)
    from anim_ugo import key_constant
    key_constant(act, 'pose.bones["bolt"].scale')
    key_constant(act, 'pose.bones["carry"].scale')
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
