"""Tesla Coil clips (game: 24 fps).

Idle   : the switch standing open; he stands by his console holding his lapel, gazes proudly up at the toroid, then
         turns and leans to the gauge board, peers at a gauge, taps its glass twice with his knuckles, nods and
         straightens, his hand back on his lapel.
Combat : his right fist on the open switch's handle, his left on his hip, leaning in eagerly, watching the robots.
Attack : (33 frames, inside the 1.4 s cooldown) he rises a little and pushes the handle back (anticipation), then
         hauls the switch down and closed, sinking into it, the blades slam into the jaws at DISCHARGE (frame 8, held to
         10: the game's lightning leaves the toroid there); the jolt runs through him: his shoulders jump, his left arm
         flies up, his head snaps back and his hair stands out on end (the `hair` bone swells), he shivers; then he pushes
         the switch open again (frames 16-23), steps back and settles into the Combat pose.

The coil and the console never move (`machine`); the switch's blades and handle turn about the hinge pin (`switch`, a
"rot" aim about SWING_AX); his right fist grips the handle (a "frame" aim: the thumb along the handle toward the knob,
the knuckles following the solved forearm)."""
import math
from mathutils import Vector, Quaternion, Matrix
import tesla as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

_wrR, _fR, _nR, _tR = cm.hand_frame("R")
WR_R, T_R, F_R, N_R = vec(_wrR), vec(_tR), vec(_fR), vec(_nR)
FIST_R = vec(cm.fist_center("R"))
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
WR_L, T_L, F_L, N_L = vec(_wrL), vec(_tL), vec(_fL), vec(_nL)
FIST_L = vec(cm.fist_center("L"))
SHOULDER_R = vec(J["shoulder_R"])

HINGE, GRIP0, SN = vec(cm.HINGE), vec(cm.GRIP_REST), vec(cm.SN)
SWING = vec(cm.SWING_AX)
OPEN = cm.OPEN_DEG
GAUGES = [vec(g) for g in cm.gauge_centres()]
BOARD_N, BOARD_UP = vec(cm.BOARD_N), vec(cm.BOARD_UP)
TOR = vec(cm.TOR_C)

# ---------------------------------------------------------------------------------------------- timing (24 fps)
DISCHARGE = 8      # game.gd ATTACK_FRAME: the blades hit the jaws, the coil fires (held to frame 10)
FR = 33            # <= 1.4 s


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def fwd(yaw):
    return rz(yaw) @ V(0.0, -1.0, 0.0)


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


def perp(v, ax):
    v = Vector(v) - ax * Vector(v).dot(ax)
    return v.normalized() if v.length > 1e-6 else ax.orthogonal().normalized()


# ---------------------------------------------------------------------------------------------- the switch
def swing_q(deg):
    return Quaternion(SWING, math.radians(deg))


def switch_grip(deg):
    """The fist's centre on the handle and the handle's direction (toward the knob) with the switch at deg."""
    q = swing_q(deg)
    return HINGE + q @ (GRIP0 - HINGE), (q @ SN).normalized()


# ---------------------------------------------------------------------------------------------- body
def feet(arm, lf, rf, yaw, lift_l=0.0, lift_r=0.0):
    aims = {}
    q = rz(yaw)
    for side, p, lift in (("L", lf, lift_l), ("R", rf, lift_r)):
        z = float(J["ankle_" + side][2]) + lift
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims.update(leg_aims(arm, side, V(p[0], p[1], z), pole=pole))
        aims["foot." + side] = rz(yaw + (-10 if side == "R" else 10)) @ rest_foot
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, tilt=0.0, shrug=0.0):
    """bend: + forward; side: + to his left; chest: the chest's extra turn (deg); look: the head's heading (deg, world);
    pitch: + chin up; tilt: + head to his left; shrug: + shoulders up."""
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tl(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tl(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tl(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(tilt * 0.3, -0.16 - 0.25 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(tilt, -0.06 + 0.55 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.04, 0.02 + shrug)
    aims["clavicle.R"] = qc @ V(-1.0, -0.04, 0.02 + shrug)


def grip_r(arm, fist, thumb, finger, pole):
    """His right fist (its middle) at `fist`, the thumb along `thumb`, the knuckles toward `finger`."""
    t = Vector(thumb).normalized()
    R = frame_map(T_R, t, F_R, perp(finger, t))
    aims = arm_aims(arm, "R", fist - R @ (FIST_R - WR_R), pole=pole)
    aims["hand.R"] = ("frame", T_R, R @ T_R, F_R, R @ F_R)
    return aims


def solve_grip(P, arm, aims, ro, rr, sc, fist, thumb, pole, finger0=None):
    """Solve with his right fist round a handle along `thumb`, three times: each time the knuckles follow the solved
    forearm (square to the handle), so the wrist bends as little as the grip allows."""
    t = Vector(thumb).normalized()
    if finger0 is None:
        reach = fist - SHOULDER_R + V(0.0, -0.1, -0.25)
        finger0 = perp(reach, t)
    finger = finger0
    for it in range(3):
        a2 = dict(aims)
        a2.update(grip_r(arm, fist, t, finger, pole))
        ch, Pm = P.solve(a2, ro, rr, scales=sc)
        fa = Pm["forearm.R"].col[1].xyz.normalized()
        finger = perp(fa, t)
    return ch


def hip_l(arm, ro, yaw):
    """His left fist on his hip, the elbow out."""
    wrist = body_pt(V(0.3, -0.005, 1.0), ro, yaw)
    return arm_aims(arm, "L", wrist, pole=rz(yaw) @ V(1.0, 0.45, 0.1), hand_dir=rz(yaw) @ V(-0.4, 0.25, -1.0))


def lapel_r(arm, ro, yaw):
    """(fist, thumb, finger, pole): his right fist holding the coat's right lapel at his chest."""
    fist = body_pt(V(-0.105, -0.255, 1.2), ro, yaw)
    return fist, rz(yaw) @ V(0.05, -0.1, 1.0), rz(yaw) @ V(0.45, 1.0, -0.1), rz(yaw) @ V(-1.0, 0.4, -0.9)


# ---------------------------------------------------------------------------------------------- idle
I_FEET = ((0.17, 0.06), (-0.18, 0.05))
I_YAW = -8.0


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    q_open = ("rot", swing_q(OPEN))
    g = GAUGES[1]                                                      # the nearer gauge
    tap_fist = g + BOARD_N * 0.072
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br = math.sin(w * 3)
        # 0: standing proud (gazing up at the toroid), 1: leaning to the gauge board
        lean = smooth_keys([(0.0, 0.0), (0.24, 0.0), (0.36, 1.0), (0.7, 1.0), (0.84, 0.0), (1.0, 0.0)], t)
        tap = 0.0
        for tc in (0.43, 0.5):
            tap = max(tap, math.exp(-((t - tc) / 0.018) ** 2))
        hand_k = smooth_keys([(0.0, 0.0), (0.26, 0.0), (0.37, 1.0), (0.66, 1.0), (0.8, 0.0), (1.0, 0.0)], t)
        yaw = I_YAW - 14.0 * lean
        ro = V(-0.03 * lean, -0.02 * lean, -0.008 + 0.004 * br - 0.03 * lean)
        aims = feet(arm, I_FEET[0], I_FEET[1], I_YAW)
        look_up = math.sin(math.pi * min(1.0, max(0.0, t / 0.24))) * (1.0 - lean)
        nod = 0.08 * math.sin(math.pi * min(1.0, max(0.0, (t - 0.56) / 0.12))) if 0.56 < t < 0.68 else 0.0
        torso(aims, yaw, bend=0.08 + 0.3 * lean, side=-0.16 * lean, chest=-16.0 * lean + 3.0 * math.sin(w),
              look=I_YAW + 34.0 * look_up - 40.0 * lean + 6.0 * math.sin(w * 2) * (1 - lean),
              pitch=0.02 + 0.32 * look_up - 0.38 * lean - nod + 0.02 * br, tilt=0.12 * look_up - 0.1 * lean)
        aims.update(hip_l(arm, ro, yaw))
        aims["switch"] = q_open
        sc = {"hair": 1.0}
        lf, lt, lfi, lp = lapel_r(arm, ro, yaw)
        if hand_k <= 1e-4:
            aims.update(grip_r(arm, lf, lt, lfi, lp))
            ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        else:
            k = hand_k
            fist = lf.lerp(tap_fist - BOARD_N * (0.03 * tap), k) + V(0.0, 0.0, 0.07 * math.sin(math.pi * k)) * (1.0 if k < 0.999 else 0.0)
            thumb = lt.lerp(BOARD_UP, k).normalized()
            finger = lfi.lerp(-BOARD_N, k)
            aims.update(grip_r(arm, fist, thumb, finger, lp.lerp(rz(yaw) @ V(-1.0, 0.2, -0.5), k)))
            ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- combat
C_FEET = ((0.15, 0.06), (-0.22, -0.1))
C_YAW = -26.0
C_RO = V(-0.04, -0.035, -0.035)
POLE_GRIP = V(-1.0, 0.35, -0.7)


def combat_core(arm, br=0.0, sw=0.0):
    ro = C_RO + V(0.0, 0.0, 0.006 * br)
    aims = feet(arm, C_FEET[0], C_FEET[1], C_YAW)
    torso(aims, C_YAW + 1.5 * sw, bend=0.16 + 0.01 * br, side=-0.04, chest=-8.0, look=-4.0 + 4.0 * sw, pitch=0.02, tilt=-0.04)
    aims.update(hip_l(arm, ro, C_YAW))
    return aims, ro


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br, sw = math.sin(w * 2), math.sin(w)
        aims, ro = combat_core(arm, br, sw)
        deg = OPEN + 1.2 * math.sin(w * 2)
        aims["switch"] = ("rot", swing_q(deg))
        G, h = switch_grip(deg)
        ch = solve_grip(P, arm, aims, ro, rz(C_YAW), {"hair": 1.0}, G, h, rz(C_YAW) @ POLE_GRIP)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- attack
K_DEG = [(0, OPEN), (3, OPEN + 6.0), (5, OPEN - 6.0), (6, 62.0), (7, 22.0), (DISCHARGE, 0.0), (16, 0.0), (19, 40.0),
         (22, OPEN + 3.0), (24, OPEN), (FR, OPEN)]
K_RO = [(0, C_RO), (3, C_RO + V(0.01, 0.0, 0.015)), (5, C_RO + V(-0.02, -0.02, 0.0)), (DISCHARGE, C_RO + V(-0.01, 0.03, -0.075)),
        (10, C_RO + V(0.0, 0.05, -0.05)), (13, C_RO + V(0.0, 0.04, -0.06)), (16, C_RO + V(-0.01, 0.03, -0.055)),
        (20, C_RO + V(-0.04, -0.03, -0.04)), (24, C_RO + V(-0.03, -0.02, -0.03)), (29, C_RO + V(0.01, 0.04, -0.02)), (FR, C_RO)]
K_YAW = [(0, C_YAW), (3, C_YAW + 4.0), (DISCHARGE, C_YAW - 10.0), (12, C_YAW - 6.0), (20, C_YAW - 2.0), (27, C_YAW + 4.0), (FR, C_YAW)]
K_BEND = [(0, 0.16), (3, 0.24), (5, 0.2), (DISCHARGE, -0.06), (10, -0.18), (14, -0.1), (17, 0.06), (21, 0.24), (25, 0.18),
          (FR, 0.16)]
K_PITCH = [(0, 0.02), (3, -0.08), (6, -0.05), (DISCHARGE, 0.1), (10, 0.42), (13, 0.25), (17, 0.05), (22, 0.0), (FR, 0.02)]
K_LOOK = [(0, -4.0), (3, -8.0), (DISCHARGE, 10.0), (11, 30.0), (16, 22.0), (22, -6.0), (FR, -4.0)]
K_SHRUG = [(0, 0.0), (DISCHARGE, 0.05), (9, 0.3), (11, 0.24), (14, 0.08), (18, 0.0), (FR, 0.0)]
K_HAIR = [(0, 1.0), (DISCHARGE, 1.0), (9, 1.2), (11, 1.26), (13, 1.18), (15, 1.22), (18, 1.08), (22, 1.0), (FR, 1.0)]
K_ARM_L = [(0, 0.0), (DISCHARGE, 0.0), (10, 1.0), (14, 0.85), (20, 0.0), (FR, 0.0)]    # his left arm flung up
# feet: (frame, left (x, y), right (x, y)): the right foot steps in for the haul, and back at the end
K_FEET = [(0, C_FEET[0], C_FEET[1]), (3, C_FEET[0], C_FEET[1]), (6, C_FEET[0], (-0.26, -0.17)), (24, C_FEET[0], (-0.26, -0.17)),
          (29, C_FEET[0], C_FEET[1]), (FR, C_FEET[0], C_FEET[1])]


def feet_at(f):
    for (fa, la, ra), (fb, lb, rb) in zip(K_FEET, K_FEET[1:]):
        if fa <= f <= fb:
            k = ease((f - fa) / float(fb - fa)) if fb > fa else 1.0
            lf = (lerp(la[0], lb[0], k), lerp(la[1], lb[1], k))
            rf = (lerp(ra[0], rb[0], k), lerp(ra[1], rb[1], k))
            dr = math.hypot(rb[0] - ra[0], rb[1] - ra[1])
            return lf, rf, 0.0, min(0.06, dr * 0.6) * math.sin(math.pi * k)
    e = K_FEET[-1]
    return e[1], e[2], 0.0, 0.0


def shiver(f):
    """The jolt's shiver: a fast decaying tremble after the discharge."""
    if f <= DISCHARGE:
        return 0.0
    t = f - DISCHARGE
    return math.exp(-t / 4.0) * math.sin(t * 2.6)


def attack_pose(arm, f):
    yaw = smooth_keys(K_YAW, f) + 3.0 * shiver(f)
    ro = smooth_keys(K_RO, f) + V(0.006 * shiver(f), 0.0, 0.004 * shiver(f + 1))
    lf, rf, ll, rl = feet_at(f)
    aims = feet(arm, lf, rf, C_YAW, lift_r=rl)
    torso(aims, yaw, bend=smooth_keys(K_BEND, f), side=-0.04 + 0.05 * shiver(f), chest=-8.0 + 4.0 * shiver(f + 0.5),
          look=smooth_keys(K_LOOK, f), pitch=smooth_keys(K_PITCH, f), tilt=-0.04 + 0.12 * shiver(f + 1), shrug=smooth_keys(K_SHRUG, f))
    up = smooth_keys(K_ARM_L, f)
    if up < 1e-3:
        aims.update(hip_l(arm, ro, yaw))
    else:
        hip = body_pt(V(0.3, -0.005, 1.0), ro, yaw)
        high = body_pt(V(0.46, -0.08, 1.56 + 0.04 * shiver(f)), ro, yaw)
        wrist = hip.lerp(high, up)
        hd = (rz(yaw) @ V(-0.4, 0.25, -1.0)).lerp(rz(yaw) @ V(0.25, -0.2, 1.0), up)
        aims.update(arm_aims(arm, "L", wrist, pole=rz(yaw) @ V(1.0, 0.45, 0.1 - 0.6 * up), hand_dir=hd))
    deg = smooth_keys(K_DEG, f)
    aims["switch"] = ("rot", swing_q(deg))
    sc = {"hair": smooth_keys(K_HAIR, f)}
    return aims, ro, yaw, sc, deg


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, yaw, sc, deg = attack_pose(arm, f)
        G, h = switch_grip(deg)
        ch = solve_grip(P, arm, aims, ro, rz(yaw), sc, G, h, rz(yaw) @ POLE_GRIP)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
