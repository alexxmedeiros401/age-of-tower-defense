"""Spear Guard clips (30 fps):
- Idle: standing guard, the spear planted upright at his right side, the shield resting on his left arm; he breathes and
  looks about.
- Combat: the phalanx stance: left foot forward, knees bent, the shield up before him (his eyes over its rim), the spear
  overhand above his shoulder pointing at the robots; a slow bob.
- Attack: he draws the spear back (0-4), then drives a lunging overhand thrust past the shield's edge: the spear is at
  full reach at THRUST (frame 6), when the game's spear-flash leaves its point for every robot hit; holds a moment and
  recovers into the stance (the clip ends in the Combat pose).

The spear and the shield are rigid in his fists ("frame" aims): the spear lies along the right fist's thumb axis, the
shield's grip in the left fist with its face along the knuckles."""
import math
from mathutils import Vector, Quaternion
import spear as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
ROOT = Vector(J["root"])

T_REST = Vector(cm.spear_axis()[1])
_wr, _f, _n, _t = cm.hand_frame("R")
F_REST = Vector(_f)
FIST_OFF_R = Vector(cm.fist_center("R") - _wr)       # wrist -> grip centre (rest)
_G, _N, _U, _S = cm.shield_frame()
G_REST, N_REST, U_REST = Vector(_G), Vector(_N), Vector(_U)
WR_L_REST = Vector(J["wrist_L"])
BACK, FWD = cm.SPEAR_BACK, cm.SPEAR_FWD
THRUST = 6            # the frame the spear is at full reach (game.gd ATTACK_FRAME)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def spear_grip(arm, grip, spear_dir, finger, pole):
    """Right fist (its grip centre) at `grip`, the spear along `spear_dir`, the fist's knuckles toward `finger`."""
    sd = Vector(spear_dir).normalized()
    R = frame_map(T_REST, sd, F_REST, Vector(finger))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF_R, pole=pole)
    aims["hand.R"] = ("frame", T_REST, sd, F_REST, Vector(finger))
    return aims


def shield_hold(arm, fist, normal, up, pole):
    """Left fist at `fist` holding the shield's grip, its face toward `normal`, the grip along `up`."""
    nrm = Vector(normal).normalized()
    R = frame_map(N_REST, nrm, U_REST, Vector(up))
    aims = arm_aims(arm, "L", Vector(fist) - R @ (G_REST - WR_L_REST), pole=pole)
    aims["hand.L"] = ("frame", N_REST, nrm, U_REST, Vector(up))
    return aims


def legs(arm, yaw, lf=(0.2, -0.1), rf=(-0.2, 0.14), lift_l=0.0, open_feet=0.6):
    """Feet planted under the turned hips: lf / rf are the left and right ankles in the body's own frame."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by), lift in (("L", lf, lift_l), ("R", rf, 0.0)):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + lift)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = Vector(J["toe_" + side]) - Vector(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * open_feet + (-12 if side == "R" else 6)) @ rest_foot
    return aims


def torso(aims, yaw_chest, lean=0.0, side=0.0, spine_tw=0.0, chest_tw=0.0, neck_tw=0.0, head_tw=0.0, head_tilt=0.0,
          head_up=0.0):
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.22 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.32 * lean, 1.0), chest_tw)
    aims["neck"] = (V(0.0, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


# ----------------------------------------------------------------------------------------------- idle
BUTT_IDLE = V(-0.38, -0.1, 0.0)
SD_IDLE = V(-0.05, 0.03, 1.0)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm, -4.0, lf=(0.19, -0.02), rf=(-0.19, 0.08), open_feet=0.3)
    ro = V(0.0, 0.0, -0.006 + 0.005 * br)
    rr = rz(-4.0 + 2.0 * math.sin(w))
    look = 0.45 * math.sin(w) + 0.12 * math.sin(w * 3)
    torso(aims, -4.0, lean=-0.02, side=0.015 * math.sin(w), spine_tw=0.03 * math.sin(w), chest_tw=0.05 * math.sin(w),
          neck_tw=0.3 * look, head_tw=0.7 * look, head_up=0.06 + 0.04 * br)
    q = rz(-4.0)
    aims["clavicle.L"] = q @ V(1.0, 0.0, 0.0)
    aims["clavicle.R"] = q @ V(-1.0, 0.0, 0.04)
    sd = SD_IDLE.normalized()
    grip = BUTT_IDLE + sd * BACK
    aims.update(spear_grip(arm, grip + V(0, 0, 0.004 * br), sd, V(0.25, -1.0, -0.25), pole=V(-1.0, 0.5, -0.4)))
    aims.update(shield_hold(arm, V(0.44, -0.04, 0.9 + 0.006 * math.sin(w * 2 + 0.7)), V(0.85, -0.45, 0.05), V(0.02, -0.12, 1.0),
                            pole=V(1.0, 0.4, -0.3)))
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


# ----------------------------------------------------------------------------------------------- the phalanx stance
YAW = -22.0
STANCE_GRIP = V(-0.37, 0.08, 1.66)       # beside his head, above the right shoulder: the spear clear of his face
STANCE_DIR = V(-0.04, -1.0, -0.13)
STANCE_FINGER = V(0.25, -0.45, 0.85)
SPEAR_POLE = V(-1.0, 0.35, -0.25)
SH_FIST = V(0.2, -0.44, 1.1)
SH_NORMAL = V(0.12, -1.0, 0.08)
SH_UP = V(0.05, 0.08, 1.0)
SH_POLE = V(1.0, 0.1, -0.6)


def stance(arm, br=0.0, sway=0.0, lunge=0.0, crouch=0.0, chest=0.0, lift_l=0.0, lf_fwd=0.0):
    aims = legs(arm, YAW, lf=(0.21, -0.17 - lf_fwd), rf=(-0.21, 0.2), lift_l=lift_l)
    q = rz(YAW)
    ro = q @ V(0.0, -0.16 * lunge, 0.0) + V(0.0, 0.0, -0.045 - 0.03 * crouch - 0.05 * lunge + 0.004 * br)
    rr = rz(YAW + 1.5 * sway)
    torso(aims, YAW + chest, lean=0.12 + 0.18 * lunge, side=0.02 * sway, spine_tw=math.radians(chest * 0.4),
          chest_tw=math.radians(chest * 0.6), neck_tw=math.radians(-0.4 * (YAW + chest)), head_tw=math.radians(-0.6 * (YAW + chest)),
          head_up=0.1 + 0.05 * lunge)
    qc = rz(YAW + chest)
    aims["clavicle.L"] = qc @ V(1.0, -0.15, 0.06)
    aims["clavicle.R"] = qc @ V(-1.0, 0.02, 0.24)
    return aims, ro, rr


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    aims, ro, rr = stance(arm, br, sw)
    bob = V(0.0, 0.0, 0.008 * br)
    aims.update(spear_grip(arm, STANCE_GRIP + bob + V(0.004 * sw, 0, 0), (STANCE_DIR + V(0.02 * sw, 0, 0.01 * br)).normalized(),
                           STANCE_FINGER, SPEAR_POLE))
    aims.update(shield_hold(arm, SH_FIST + bob * 0.6, SH_NORMAL, SH_UP, SH_POLE))
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


# ----------------------------------------------------------------------------------------------- the thrust
def make_attack(arm, frames=30):
    """Draw back (0-4), lunge and thrust (4-6, full reach at THRUST), hold (6-10), recover (10-30)."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    back_grip, back_dir = V(-0.38, 0.32, 1.72), V(-0.03, -1.0, -0.08)
    out_grip, out_dir = V(-0.25, -0.5, 1.5), V(0.0, -1.0, -0.17)
    keys = [
        # frame, grip, spear dir, lunge, crouch, chest twist, shield fist offset, front foot forward
        (0, STANCE_GRIP, STANCE_DIR, 0.0, 0.0, 0.0, V(0, 0, 0), 0.0),
        (4, back_grip, back_dir, -0.25, 0.4, -12.0, V(0.0, -0.04, 0.0), 0.0),
        (THRUST, out_grip, out_dir, 1.0, 0.3, 10.0, V(0.1, 0.12, -0.04), 0.07),
        (10, out_grip + V(0.0, -0.03, -0.01), out_dir, 1.05, 0.3, 11.0, V(0.1, 0.12, -0.04), 0.07),
        (frames, STANCE_GRIP, STANCE_DIR, 0.0, 0.0, 0.0, V(0, 0, 0), 0.0),
    ]
    for f in range(frames + 1):
        i = max(k for k in range(len(keys) - 1) if keys[k][0] <= f) if f < frames else len(keys) - 2
        a, b = keys[i], keys[i + 1]
        k = (f - a[0]) / float(b[0] - a[0])
        if i == 1:
            k = k * k                                   # the thrust accelerates into its reach
        elif i == 3:
            k = ease(k)
        else:
            k = ease(k)
        grip = a[1].lerp(b[1], k)
        sd = a[2].normalized().lerp(b[2].normalized(), k).normalized()
        lunge, crouch, chest = lerp(a[3], b[3], k), lerp(a[4], b[4], k), lerp(a[5], b[5], k)
        sh_off = a[6].lerp(b[6], k)
        fwd = lerp(a[7], b[7], k)
        aims, ro, rr = stance(arm, 0.0, 0.0, lunge=lunge, crouch=crouch, chest=chest, lf_fwd=fwd,
                              lift_l=0.03 * math.sin(math.pi * min(1.0, max(0.0, (f - 3) / 4.0))))
        body = rz(YAW) @ V(0.0, -0.16 * lunge, -0.05 * lunge)
        aims.update(spear_grip(arm, grip, sd, STANCE_FINGER.lerp(V(0.1, -0.85, 0.5), max(0.0, min(1.0, lunge))), SPEAR_POLE))
        aims.update(shield_hold(arm, SH_FIST + body + sh_off, SH_NORMAL, SH_UP, SH_POLE))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
