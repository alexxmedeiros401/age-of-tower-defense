"""Axe Warrior clips (keyed as 30 fps frames; the .glb runs them at 24, game.gd CLIP_FPS).

Idle    : leaning on his axe: its head on the ground in front of him, both fists on the haft's end; he breathes, looks
          about, and once a loop rolls his head on his shoulders.
Combat  : the ready stance: feet wide, knees bent, turned a little to his right, the axe cocked up behind his right
          shoulder in both fists; he sways with it.
Attack  : (26 frames) he winds up (0-4), then sweeps the axe round in front of him at waist height (the blade leading),
          through the robots at HIT (frame 7: game.gd's cleave arc and its sparks), follows through to his left and
          swings it back up over his shoulder into the ready stance.

The axe is rigid on the `axe` bone in his right fist (his lower hand); his left fist closes on the haft above it
(LEFT_ON along the haft), placed every frame from the axe's pose."""
import math
from mathutils import Vector, Quaternion
import axe as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
_G, _A, _B = cm.axe_frame()
A_REST, B_REST = vec(_A), vec(_B)
_wr, _f, _n, _t = cm.hand_frame("R")
FIST_OFF_R = vec(_G - _wr)
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
TL_REST, FL_REST = vec(_tL), vec(_fL)
FIST_OFF_L = vec(cm.fist_center("L") - _wrL)
LEFT_ON = 0.22         # his left fist this far up the haft from his right
HIT = 7                # the blade passes through the robots in front of him (game.gd ATTACK_FRAME)
FR = 26


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def mixd(a, b, k):
    return a.normalized().lerp(b.normalized(), k).normalized()


def bez_d(a, b, c, k):
    return mixd(mixd(a, b, k), mixd(b, c, k), k)


def bez_p(a, b, c, k):
    return a.lerp(b, k).lerp(b.lerp(c, k), k)


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def two_hands(arm, grip, haft, edge, ro, yaw, left_on=LEFT_ON):
    """Both fists on the haft: the right at `grip` (the axe's haft along `haft`, its edge toward `edge`), the left
    `left_on` along the haft from it, each wrist kept straight (its fingers along the line from its shoulder)."""
    hd = Vector(haft).normalized()
    R = frame_map(A_REST, hd, B_REST, Vector(edge))
    sh_r = body_pt(J["shoulder_R"], ro, yaw)
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF_R, pole=rz(yaw) @ V(-0.9, 0.2, -0.6))
    aims["hand.R"] = ("frame", A_REST, hd, B_REST, Vector(edge))
    gl = Vector(grip) + hd * left_on
    sh_l = body_pt(J["shoulder_L"], ro, yaw)
    fl = gl - sh_l
    fl = fl - hd * fl.dot(hd)
    if fl.length < 1e-4:
        fl = rz(yaw) @ V(0.0, -1.0, 0.0)
    RL = frame_map(TL_REST, hd, FL_REST, fl)
    aims.update(arm_aims(arm, "L", gl - RL @ FIST_OFF_L, pole=rz(yaw) @ V(0.9, 0.2, -0.6)))
    aims["hand.L"] = ("frame", TL_REST, hd, FL_REST, fl)
    return aims


def feet(arm, yaw, lf=(0.21, -0.06), rf=(-0.21, 0.06), lift=(0.0, 0.0), turn=(10.0, -10.0)):
    q = rz(yaw)
    aims = {}
    for side, (bx, by), up, tw in (("L", lf, lift[0], turn[0]), ("R", rf, lift[1], turn[1])):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + up)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw + tw) @ (rest_foot + V(0, 0, -up * 0.6))
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0):
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(math.sin(roll) * 0.5, -0.1 - 0.2 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.04 + 0.7 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.03, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.03, 0.02)


# ---------------------------------------------------------------------------------------------- idle: leaning on it
IDLE_G = V(-0.04, -0.36, 1.02)          # his right fist on the haft (the robots' frame); the head on the ground below
IDLE_HAFT = V(0.0, -0.06, -1.0)
IDLE_EDGE = V(0.0, -1.0, 0.0)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = 3.0 * sway
    ro = V(0.0, -0.02, -0.02 + 0.006 * br)
    aims = feet(arm, 0.0, lf=(0.22, -0.02), rf=(-0.22, 0.04), turn=(14.0, -14.0))
    # once a loop (t 0.55-0.8) he rolls his head round on his shoulders
    rl = smooth01((t - 0.55) / 0.05) * (1.0 - smooth01((t - 0.75) / 0.05))
    ph = (t - 0.55) / 0.2 * 2 * math.pi
    look = (22.0 * math.sin(w + 0.5) + 6.0 * math.sin(w * 3)) * (1.0 - rl)
    torso(aims, yaw, bend=0.1, side=-0.02 * sway, look=look + rl * 25.0 * math.cos(ph), pitch=0.0 + 0.02 * br - 0.1 * rl * math.sin(ph),
          roll=0.25 * rl * math.sin(ph))
    g = IDLE_G + V(0.0, 0.0, 0.004 * br)
    aims.update(two_hands(arm, g, IDLE_HAFT, IDLE_EDGE, ro, yaw, left_on=-0.17))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- combat: ready
C_YAW = -35.0
C_FEET = dict(lf=(0.24, -0.16), rf=(-0.24, 0.16), turn=(-4.0, -24.0))
COCK_G = V(-0.18, -0.12, 1.28)          # (the robots' frame)
COCK_HAFT = V(-0.35, 0.4, 0.85)         # up and back over his right shoulder
COCK_EDGE = V(-0.4, -0.85, -0.3)


def combat_pose(arm, t):
    w = 2 * math.pi * t
    bob = math.sin(w * 2)
    sway = math.sin(w)
    ro = V(0.0, 0.0, -0.08 + 0.012 * bob)
    aims = feet(arm, C_YAW, **C_FEET)
    torso(aims, C_YAW + 2.0 * sway, bend=0.14, chest=-6.0, look=0.0, pitch=0.06)
    g = COCK_G + ro + V(0.006 * sway, 0.0, 0.01 * bob)
    aims.update(two_hands(arm, g, (COCK_HAFT + V(0.03 * sway, 0, 0)).normalized(), COCK_EDGE, ro, C_YAW + 2.0 * sway))
    return aims, ro, rz(C_YAW + 2.0 * sway)


# ---------------------------------------------------------------------------------------------- attack: the sweep
WIND_G, WIND_HAFT, WIND_EDGE = V(-0.2, -0.02, 1.32), V(-0.6, 0.55, 0.58), V(-0.75, -0.6, -0.2)
HIT_G, HIT_HAFT, HIT_EDGE = V(-0.15, -0.2, 1.12), V(0.45, -0.89, -0.05), V(0.97, 0.24, 0.0)
FOL_G, FOL_HAFT, FOL_EDGE = V(0.12, -0.25, 1.05), V(0.85, -0.3, -0.25), V(0.3, 0.9, 0.0)
UP_G, UP_HAFT, UP_EDGE = V(-0.05, -0.3, 1.45), V(0.1, -0.2, 0.97), V(-0.2, -0.95, 0.2)


def sweep_state(f):
    """(body yaw, chest twist, bend, crouch, grip, haft, edge, heel lift L, heel lift R) at frame f, robots' frame."""
    if f <= 4:                                                # the wind-up: further round, the axe drawn back
        k = ease(f / 4.0)
        return (lerp(C_YAW, -50.0, k), lerp(-6.0, -14.0, k), lerp(0.14, 0.1, k), lerp(0.08, 0.1, k), COCK_G.lerp(WIND_G, k),
                mixd(COCK_HAFT, WIND_HAFT, k), mixd(COCK_EDGE, WIND_EDGE, k), 0.0, 0.0)
    if f <= HIT:                                              # the sweep: round in front of him, the blade leading
        k = ((f - 4) / float(HIT - 4)) ** 1.2
        g = bez_p(WIND_G, V(-0.32, -0.18, 1.18), HIT_G, k)
        return (lerp(-50.0, -5.0, k), lerp(-14.0, 6.0, k), lerp(0.1, 0.22, k), lerp(0.1, 0.14, k), g,
                bez_d(WIND_HAFT, V(-0.75, -0.6, 0.05), HIT_HAFT, k), bez_d(WIND_EDGE, V(0.3, -0.95, 0.0), HIT_EDGE, k), 0.0, 0.03 * k)
    if f <= 11:                                               # on through to his left
        k = ease((f - HIT) / float(11 - HIT))
        return (lerp(-5.0, 35.0, k), lerp(6.0, 12.0, k), lerp(0.22, 0.28, k), lerp(0.14, 0.15, k), HIT_G.lerp(FOL_G, k),
                mixd(HIT_HAFT, FOL_HAFT, k), mixd(HIT_EDGE, FOL_EDGE, k), 0.0, lerp(0.03, 0.06, k))
    if f <= 18:                                               # up in front of him
        k = ease((f - 11) / 7.0)
        return (lerp(35.0, 0.0, k), lerp(12.0, 0.0, k), lerp(0.28, 0.1, k), lerp(0.15, 0.09, k), FOL_G.lerp(UP_G, k),
                mixd(FOL_HAFT, UP_HAFT, k), mixd(FOL_EDGE, UP_EDGE, k), 0.0, lerp(0.06, 0.0, k))
    k = ease((f - 18) / float(FR - 18))                       # and back over his shoulder
    return (lerp(0.0, C_YAW, k), lerp(0.0, -6.0, k), lerp(0.1, 0.14, k), lerp(0.09, 0.08, k), UP_G.lerp(COCK_G, k),
            mixd(UP_HAFT, COCK_HAFT, k), mixd(UP_EDGE, COCK_EDGE, k), 0.0, 0.0)


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        yaw, chest, bend, crouch, g, haft, edge, hl, hr_ = sweep_state(f)
        ro = V(0.0, -0.05 * math.sin(math.pi * min(1.0, max(0.0, (f - 3) / 9.0))), -crouch)
        aims = feet(arm, C_YAW, lift=(hl, hr_), **C_FEET)
        torso(aims, yaw, bend=bend, chest=chest, look=0.0, pitch=0.06 - 0.08 * (bend - 0.14))
        aims.update(two_hands(arm, g + ro, haft, edge, ro, yaw))
        ch, _ = P.solve(aims, ro, rz(yaw))
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr = combat_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
