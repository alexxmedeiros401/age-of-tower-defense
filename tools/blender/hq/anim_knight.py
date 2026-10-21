"""Knight clips (game: 24 fps):
- Idle: the great sword planted before him, point on the ground, both fists stacked on its hilt; he breathes, looks
  about, and once a loop shifts his weight.
- Combat: the high guard ("from the roof"): left foot forward, the sword held up by his right shoulder in both hands,
  blade up and back, edge to the robots; a slow sway.
- Attack (24 frames, the 1.0 s cooldown): he coils, the blade drawn further back (0-4), cleaves down and across from
  his right shoulder to his left hip, the blade level through the robots before him at HIT (frame 9: game.gd's hit and
  the swing's arc), follows through low on his left (9-13) and climbs back into the guard (13-24).

The sword is rigid in his right fist (the blade along the thumb axis, its edge toward the knuckles, "frame" aims); his
left fist takes the grip below it, the palm turned the other way."""
import math
from mathutils import Vector, Quaternion
import knight as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
ROOT = Vector(J["root"])

_G, _T, _E, _W = cm.sword_frame()
G_REST, T_REST, E_REST = Vector(_G), Vector(_T), Vector(_E)
WR_R_REST = Vector(J["wrist_R"])
_wr, _f, _n, _t = cm.hand_frame("R")
N_R_REST = Vector(_n)
_wrl, _fl, _nl, _tl = cm.hand_frame("L")
WR_L_REST, T_L_REST, N_L_REST = Vector(_wrl), Vector(_tl), Vector(_nl)
FIST_L_OFF = Vector(cm.fist_center("L")) - WR_L_REST
HIT = 9               # the blade level through the robots (game.gd ATTACK_FRAME)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def _ortho(e, t):
    e = Vector(e) - Vector(t) * Vector(e).dot(Vector(t))
    return e.normalized() if e.length > 1e-4 else Vector(t).orthogonal().normalized()


def sword_hold(arm, G_t, T_t, E_t, pole_r, pole_l):
    """Right fist (the sword's grip under the guard) at G_t, the blade along T_t, its edge toward E_t; the left fist on
    the grip below it."""
    T_t = Vector(T_t).normalized()
    E_t = _ortho(E_t, T_t)
    R = frame_map(T_REST, T_t, E_REST, E_t)
    aims = arm_aims(arm, "R", Vector(G_t) - R @ (G_REST - WR_R_REST), pole=pole_r)
    aims["hand.R"] = ("frame", T_REST, T_t, E_REST, E_t)
    palm_l = -(R @ N_R_REST)
    palm_l = _ortho(palm_l, T_t)
    RL = frame_map(T_L_REST, T_t, N_L_REST, palm_l)
    lg = Vector(G_t) - T_t * cm.LEFT_DOWN
    aims.update(arm_aims(arm, "L", lg - RL @ FIST_L_OFF, pole=pole_l))
    aims["hand.L"] = ("frame", T_L_REST, T_t, N_L_REST, palm_l)
    return aims


def legs(arm, yaw, lf=(0.2, -0.12), rf=(-0.2, 0.14), lift_l=0.0, open_feet=0.6):
    q = rz(yaw)
    aims = {}
    for side, (bx, by), lift in (("L", lf, lift_l), ("R", rf, 0.0)):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + lift)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = Vector(J["toe_" + side]) - Vector(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * open_feet + (-14 if side == "R" else 6)) @ rest_foot
    return aims


def torso(aims, yaw_chest, lean=0.0, side=0.0, spine_tw=0.0, chest_tw=0.0, neck_tw=0.0, head_tw=0.0, head_tilt=0.0,
          head_up=0.0):
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.22 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.32 * lean, 1.0), chest_tw)
    aims["neck"] = (V(0.0, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


# ----------------------------------------------------------------------------------------------- idle: on guard duty
def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    shift = 0.5 - 0.5 * math.cos(w)
    aims = legs(arm, 0.0, lf=(0.21, 0.0), rf=(-0.21, 0.04), open_feet=0.2)
    ro = V(0.012 * (shift - 0.5), 0.0, -0.012 + 0.005 * br)
    rr = rz(1.5 * math.sin(w))
    look = 0.4 * math.sin(w) + 0.1 * math.sin(w * 3)
    torso(aims, 0.0, lean=0.04, side=0.015 * (shift - 0.5), spine_tw=0.02 * math.sin(w), chest_tw=0.03 * math.sin(w),
          neck_tw=0.3 * look, head_tw=0.6 * look, head_up=0.02 + 0.03 * br)
    aims["clavicle.L"] = V(1.0, -0.05, -0.02)
    aims["clavicle.R"] = V(-1.0, -0.05, -0.02)
    T_t = V(0.0, -0.24, -1.0).normalized()
    tip = V(0.0, -0.56, 0.03)
    G_t = tip - T_t * (cm.GUARD_UP + 0.012 + cm.BLADE_LEN) + V(0.0, 0.0, 0.004 * br)
    aims.update(sword_hold(arm, G_t, T_t, V(1.0, 0.0, 0.0), pole_r=V(-1.0, 0.3, -0.4), pole_l=V(1.0, 0.3, -0.4)))
    return aims, ro, rr


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- the high guard
YAW = -22.0
G_GUARD = V(-0.2, -0.06, 1.46)
T_GUARD = V(-0.12, 0.42, 1.0).normalized()
E_GUARD = V(0.0, -1.0, 0.4)
POLE_R = V(-1.0, 0.2, -0.3)
POLE_L = V(0.8, -0.2, -0.6)


def stance(arm, br=0.0, sway=0.0, crouch=0.0, chest=0.0, lunge=0.0, lean=0.0):
    aims = legs(arm, YAW, lf=(0.2, -0.22 - 0.06 * lunge), rf=(-0.2, 0.2))
    q = rz(YAW)
    ro = q @ V(0.0, -0.08 * lunge, 0.0) + V(0.0, 0.0, -0.05 - 0.05 * crouch + 0.004 * br)
    rr = rz(YAW + 1.2 * sway)
    yc = YAW + chest
    torso(aims, yc, lean=0.08 + lean, side=0.02 * sway, spine_tw=math.radians(chest * 0.4),
          chest_tw=math.radians(chest * 0.6), neck_tw=math.radians(-0.4 * yc), head_tw=math.radians(-0.6 * yc),
          head_up=0.04)
    qc = rz(yc)
    aims["clavicle.L"] = qc @ V(1.0, -0.1, 0.04)
    aims["clavicle.R"] = qc @ V(-1.0, 0.0, 0.1)
    return aims, ro, rr


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    aims, ro, rr = stance(arm, br, sw)
    G_t = G_GUARD + V(0.006 * sw, 0.0, 0.006 * br)
    T_t = (T_GUARD + V(0.03 * sw, 0.0, 0.0)).normalized()
    aims.update(sword_hold(arm, G_t, T_t, E_GUARD, POLE_R, POLE_L))
    return aims, ro, rr


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr = combat_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- the cleave
#      frame, right fist,              blade direction,              edge toward,            chest, crouch, lunge
KEYS = [(0, G_GUARD, T_GUARD, E_GUARD, 0.0, 0.0, 0.0),
        (4, V(-0.26, 0.02, 1.54), V(-0.3, 0.75, 0.6), V(0.1, -0.4, 1.0), -14.0, 0.2, 0.0),
        (7, V(-0.16, -0.36, 1.36), V(-0.55, -0.62, 0.55), V(0.55, -0.35, -0.75), 2.0, 0.4, 0.6),
        (HIT, V(0.02, -0.44, 1.1), V(0.5, -0.86, -0.06), V(0.25, 0.1, -1.0), 16.0, 0.55, 1.0),
        (12, V(0.2, -0.26, 0.96), V(0.62, 0.1, -0.78), V(-0.3, 0.9, -0.3), 26.0, 0.55, 0.9),
        (16, V(0.04, -0.22, 1.2), V(0.25, 0.25, 0.92), V(-0.3, -1.0, 0.2), 10.0, 0.3, 0.4),
        (24, G_GUARD, T_GUARD, E_GUARD, 0.0, 0.0, 0.0)]


def _catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def key_at(f):
    i = max(k for k in range(len(KEYS) - 1) if KEYS[k][0] <= f) if f < KEYS[-1][0] else len(KEYS) - 2
    a, b = KEYS[i], KEYS[i + 1]
    k = (f - a[0]) / float(b[0] - a[0])
    if i == 1:
        k = k * k                                          # the cut accelerates into the robots
    elif i == 2:
        k = 1 - (1 - k) * (1 - k)
    else:
        k = ease(k)
    p0 = KEYS[max(i - 1, 0)][1]
    p3 = KEYS[min(i + 2, len(KEYS) - 1)][1]
    G = _catmull(p0, a[1], b[1], p3, k)
    T = a[2].normalized().slerp(b[2].normalized(), k) if a[2].normalized().dot(b[2].normalized()) > -0.99 else a[2].lerp(b[2], k)
    E = Vector(a[3]).normalized().lerp(Vector(b[3]).normalized(), k)
    return G, T.normalized(), E, lerp(a[4], b[4], k), lerp(a[5], b[5], k), lerp(a[6], b[6], k)


def make_attack(arm, frames=24):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        G_t, T_t, E_t, chest, crouch, lunge = key_at(f)
        step = math.sin(math.pi * min(1.0, max(0.0, (f - 5) / 6.0)))
        aims, ro, rr = stance(arm, 0.0, 0.0, crouch=crouch, chest=chest, lunge=lunge, lean=0.12 * lunge)
        aims.update(legs(arm, YAW, lf=(0.2, -0.22 - 0.06 * lunge), rf=(-0.2, 0.2), lift_l=0.035 * step))
        aims.update(sword_hold(arm, G_t, T_t, E_t, POLE_R, POLE_L))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
