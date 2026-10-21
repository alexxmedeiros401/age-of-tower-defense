"""Legionary clips (30 fps):
- Idle: standing easy, the shield carried low at his left side (its face out to the front), the gladius held down at his
  right side; he breathes, looks about, and once a loop rolls his sword wrist.
- Combat: the line's stance: left foot forward, knees bent, the scutum up before him from his knees to his eyes (its boss
  toward the robots), the gladius low at his right hip, point forward, ready to stab past the shield's edge; a slow bob.
- Attack (30 frames: the 1.0 s cooldown): he gathers (0-3), steps in and punches the shield's boss forward (BASH, frame
  6: game.gd's stun for the robots it hit), pulls the shield a little aside and drives the gladius forward past its right
  edge (STAB, frame 11: the blade's flash, the hit), holds, and recovers into the stance.

The gladius and the shield are rigid in his fists ("frame" aims): the gladius along the right fist's thumb axis, the
shield's grip (across its back behind the boss) in the left fist along its thumb axis, its face along the knuckles."""
import math
from mathutils import Vector, Quaternion
import legionary as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
ROOT = Vector(J["root"])

T_REST = Vector(cm.gladius_axis()[1])
_wr, _f, _n, _t = cm.hand_frame("R")
F_REST = Vector(_f)
FIST_OFF_R = Vector(cm.fist_center("R") - _wr)       # wrist -> grip centre (rest)
_G, _N, _U, _S = cm.scutum_frame()
G_REST, N_REST, U_REST = Vector(_G), Vector(_N), Vector(_U)
WR_L_REST = Vector(J["wrist_L"])
BASH = 6              # the shield's boss at full reach (game.gd LEGION_BASH)
STAB = 11             # the gladius at full reach (game.gd ATTACK_FRAME)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def sword_grip(arm, grip, blade_dir, finger, pole):
    """Right fist (its grip centre) at `grip`, the blade along `blade_dir`, the fist's knuckles toward `finger`."""
    sd = Vector(blade_dir).normalized()
    R = frame_map(T_REST, sd, F_REST, Vector(finger))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF_R, pole=pole)
    aims["hand.R"] = ("frame", T_REST, sd, F_REST, Vector(finger))
    return aims


def shield_hold(arm, fist, normal, across, pole):
    """Left fist at `fist` holding the shield's grip, its face toward `normal`, the grip (across the shield) along
    `across`."""
    nrm = Vector(normal).normalized()
    R = frame_map(N_REST, nrm, U_REST, Vector(across))
    aims = arm_aims(arm, "L", Vector(fist) - R @ (G_REST - WR_L_REST), pole=pole)
    aims["hand.L"] = ("frame", N_REST, nrm, U_REST, Vector(across))
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
def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm, -6.0, lf=(0.2, -0.03), rf=(-0.2, 0.08), open_feet=0.3)
    ro = V(0.0, 0.0, -0.008 + 0.005 * br)
    rr = rz(-6.0 + 2.0 * math.sin(w))
    look = 0.45 * math.sin(w) + 0.12 * math.sin(w * 3)
    torso(aims, -6.0, lean=-0.02, side=0.015 * math.sin(w), spine_tw=0.03 * math.sin(w), chest_tw=0.05 * math.sin(w),
          neck_tw=0.3 * look, head_tw=0.7 * look, head_up=0.05 + 0.04 * br)
    q = rz(-6.0)
    aims["clavicle.L"] = q @ V(1.0, 0.0, -0.02)
    aims["clavicle.R"] = q @ V(-1.0, 0.0, 0.03)
    # the gladius held down at his right side, point forward and down; once a loop he rolls his wrist
    roll = math.sin(min(1.0, max(0.0, (t - 0.55) / 0.2)) * math.pi)
    blade = (V(-0.05, -0.55, -1.0) + V(0.0, -0.6, 0.55) * roll).normalized()
    aims.update(sword_grip(arm, V(-0.36, -0.06, 0.86 + 0.004 * br + 0.04 * roll), blade, V(-0.2, -0.2, -1.0).lerp(V(0.2, -1.0, -0.2), roll),
                           pole=V(-1.0, 0.6, -0.3)))
    # the shield carried low at his left side, its face to the front and out, its grip across (front to back)
    aims.update(shield_hold(arm, V(0.42, -0.06, 0.79 + 0.005 * math.sin(w * 2 + 0.7)), V(0.62, -0.78, 0.02), V(-0.78, -0.62, 0.0),
                            pole=V(1.0, 0.5, -0.2)))
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


# ----------------------------------------------------------------------------------------------- the stance
YAW = -20.0
SH_FIST = V(0.12, -0.36, 1.0)              # the shield's grip: its middle before his chest
SH_NORMAL = V(0.1, -1.0, 0.04)
SH_ACROSS = V(-1.0, -0.1, 0.0)             # the grip runs across the shield (it stands upright; his fist palm down)
SH_POLE = V(1.0, 0.1, -0.5)
GL_GRIP = V(-0.3, -0.16, 0.98)             # the gladius low at his right hip
GL_DIR = V(0.06, -1.0, 0.18)
GL_FINGER = V(0.0, -0.15, -1.0)            # knuckles down: the blade's edge level
GL_POLE = V(-1.0, 0.5, -0.4)


def stance(arm, br=0.0, sway=0.0, lunge=0.0, crouch=0.0, chest=0.0, lift_l=0.0, lf_fwd=0.0):
    aims = legs(arm, YAW, lf=(0.2, -0.2 - lf_fwd), rf=(-0.2, 0.2), lift_l=lift_l)
    q = rz(YAW)
    ro = q @ V(0.0, -0.15 * lunge, 0.0) + V(0.0, 0.0, -0.06 - 0.03 * crouch - 0.04 * lunge + 0.004 * br)
    rr = rz(YAW + 1.5 * sway)
    torso(aims, YAW + chest, lean=0.1 + 0.16 * lunge, side=0.02 * sway, spine_tw=math.radians(chest * 0.4),
          chest_tw=math.radians(chest * 0.6), neck_tw=math.radians(-0.4 * (YAW + chest)), head_tw=math.radians(-0.6 * (YAW + chest)),
          head_up=0.08 + 0.05 * lunge)
    qc = rz(YAW + chest)
    aims["clavicle.L"] = qc @ V(1.0, -0.15, 0.04)
    aims["clavicle.R"] = qc @ V(-1.0, 0.0, 0.08)
    return aims, ro, rr


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    aims, ro, rr = stance(arm, br, sw)
    bob = V(0.0, 0.0, 0.008 * br)
    aims.update(sword_grip(arm, GL_GRIP + bob + V(0.004 * sw, 0, 0), (GL_DIR + V(0.02 * sw, 0, 0.01 * br)).normalized(), GL_FINGER, GL_POLE))
    aims.update(shield_hold(arm, SH_FIST + bob * 0.6, SH_NORMAL, SH_ACROSS, SH_POLE))
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


# ----------------------------------------------------------------------------------------------- bash and stab
def make_attack(arm, frames=30):
    """Gather (0-3), step in and punch the shield forward (BASH), pull it aside and stab past its edge (STAB), hold,
    recover (14-30)."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    keys = [
        # frame, shield fist, shield normal, sword grip, blade dir, lunge, crouch, chest twist, front foot forward
        (0, SH_FIST, SH_NORMAL, GL_GRIP, GL_DIR, 0.0, 0.0, 0.0, 0.0),
        (3, SH_FIST + V(0.0, 0.1, -0.02), SH_NORMAL, GL_GRIP + V(0.0, 0.08, 0.0), GL_DIR, -0.2, 0.35, 4.0, 0.0),
        (BASH, SH_FIST + V(0.02, -0.3, 0.04), V(0.06, -1.0, 0.0), GL_GRIP + V(0.02, -0.06, 0.0), GL_DIR, 0.9, 0.2, 8.0, 0.08),
        (8, SH_FIST + V(0.1, -0.24, 0.03), V(0.25, -1.0, 0.0), GL_GRIP + V(0.0, 0.06, 0.04), V(0.1, -1.0, 0.12), 0.85, 0.25, -4.0, 0.08),
        (STAB, SH_FIST + V(0.16, -0.2, 0.03), V(0.32, -1.0, 0.0), V(-0.24, -0.68, 1.1), V(0.05, -1.0, 0.04), 1.0, 0.25, -14.0, 0.08),
        (14, SH_FIST + V(0.16, -0.2, 0.03), V(0.32, -1.0, 0.0), V(-0.23, -0.66, 1.1), V(0.05, -1.0, 0.04), 1.0, 0.25, -14.0, 0.08),
        (frames, SH_FIST, SH_NORMAL, GL_GRIP, GL_DIR, 0.0, 0.0, 0.0, 0.0),
    ]
    for f in range(frames + 1):
        i = max(k for k in range(len(keys) - 1) if keys[k][0] <= f) if f < frames else len(keys) - 2
        a, b = keys[i], keys[i + 1]
        k = (f - a[0]) / float(b[0] - a[0])
        k = k * k if i in (1, 3) else ease(k)            # the bash and the stab accelerate into their reach
        sh = a[1].lerp(b[1], k)
        sn = a[2].normalized().lerp(b[2].normalized(), k).normalized()
        gg = a[3].lerp(b[3], k)
        gd = a[4].normalized().lerp(b[4].normalized(), k).normalized()
        lunge, crouch, chest, fwd = lerp(a[5], b[5], k), lerp(a[6], b[6], k), lerp(a[7], b[7], k), lerp(a[8], b[8], k)
        step = math.sin(math.pi * min(1.0, max(0.0, (f - 2) / 5.0)))
        aims, ro, rr = stance(arm, 0.0, 0.0, lunge=lunge, crouch=crouch, chest=chest, lf_fwd=fwd, lift_l=0.035 * step)
        body = rz(YAW) @ V(0.0, -0.15 * lunge, -0.04 * lunge)
        aims.update(sword_grip(arm, gg + body * 0.5, gd, GL_FINGER, GL_POLE))
        aims.update(shield_hold(arm, sh + body, sn, SH_ACROSS, SH_POLE))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
