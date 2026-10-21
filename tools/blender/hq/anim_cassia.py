"""Cassia's clips (keyed as 30 fps, like the other heroes'):

Idle    : standing tall, the oval shield carried at her left side (its face out to the front), the gladius held low at her
          right side; she breathes, shifts her weight, looks over the field, and once a loop lifts the gladius and points
          it ahead, an order given.
Combat  : the legion's stance: left foot forward, knees bent, the shield up before her (her eyes over its rim), the
          gladius at her right hip, point forward, ready to stab past the shield's edge; a slow bob.
Attack  : (21 frames: inside the 0.7 s cooldown) she draws the gladius back (0-4) and drives it forward past the
          shield's right edge in a lunge: full reach at THRUST (frame 6: game.gd's hit), a moment's hold, and she
          recovers into the stance.
Ability : Shield Charge (52 frames): she thrusts the gladius up and forward over her head, the order to charge (ORDER,
          frame 12: game.gd's horn), drops behind the shield, and charges: two driving steps and the shield's boss
          slammed forward (SLAM, frame 31: game.gd's charge rolls out over the field and every robot is stunned); she
          holds the line a moment and settles back into the stance.
Cheer   : (rank up) the gladius thrust up overhead twice, the shield raised, a hop.

The gladius and the shield are rigid in her fists ("frame" aims): the gladius along the right fist's thumb axis, the
shield's grip (across its back behind the boss: it stands upright with her fist palm down) in the left fist along its
thumb axis, its face along the knuckles."""
import math
from mathutils import Vector, Quaternion
import cassia as cm
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
_G, _N, _U, _S = cm.shield_frame()
G_REST, N_REST, U_REST = Vector(_G), Vector(_N), Vector(_U)
WR_L_REST = Vector(J["wrist_L"])
THRUST = 6             # game.gd ATTACK_FRAME: the gladius at full reach
ORDER = 12             # the gladius thrust up: the order to charge (game.gd CASSIA_ORDER)
SLAM = 31              # the shield's boss slammed forward (game.gd CASSIA_SLAM)


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


def legs(arm, yaw, lf=(0.19, -0.1), rf=(-0.19, 0.13), lift_l=0.0, lift_r=0.0, open_feet=0.6):
    """Feet planted under the turned hips: lf / rf are the left and right ankles in the body's own frame."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by), lift in (("L", lf, lift_l), ("R", rf, lift_r)):
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


def mixd(a, b, k):
    return a.normalized().lerp(b.normalized(), k).normalized()


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ----------------------------------------------------------------------------------------------- idle
SH_IDLE = V(0.4, -0.06, 0.84)
SH_IDLE_N, SH_IDLE_A = V(0.6, -0.8, 0.02), V(-0.8, -0.6, 0.0)
GL_IDLE = V(-0.36, -0.08, 0.86)
GL_IDLE_D, GL_IDLE_F = V(-0.05, -0.55, -1.0), V(-0.2, -0.2, -1.0)
GL_POINT, GL_POINT_D, GL_POINT_F = V(-0.3, -0.42, 1.24), V(0.05, -1.0, 0.16), V(0.0, -0.2, -1.0)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm, -5.0, lf=(0.18, -0.03), rf=(-0.18, 0.07), open_feet=0.3)
    ro = V(0.01 * math.sin(w), 0.0, -0.006 + 0.005 * br)
    rr = rz(-5.0 + 2.0 * math.sin(w))
    # once a loop (t 0.5-0.8) she raises the gladius and points it ahead, looking where it points
    pt = math.sin(math.pi * smooth01((t - 0.5) / 0.3)) if 0.5 <= t <= 0.8 else 0.0
    pt = smooth01(pt * 1.6)
    look = (0.45 * math.sin(w) + 0.12 * math.sin(w * 3)) * (1.0 - pt)
    torso(aims, -5.0 + 6.0 * pt, lean=-0.02 + 0.04 * pt, side=0.02 * math.sin(w), spine_tw=0.03 * math.sin(w),
          chest_tw=0.05 * math.sin(w), neck_tw=0.3 * look, head_tw=0.7 * look, head_up=0.07 + 0.04 * br + 0.06 * pt)
    q = rz(-5.0)
    aims["clavicle.L"] = q @ V(1.0, 0.0, -0.02)
    aims["clavicle.R"] = q @ V(-1.0, 0.0, 0.03 + 0.12 * pt)
    g = GL_IDLE.lerp(GL_POINT, pt) + V(0, 0, 0.004 * br)
    aims.update(sword_grip(arm, g, mixd(GL_IDLE_D, GL_POINT_D, pt), mixd(GL_IDLE_F, GL_POINT_F, pt),
                           pole=V(-1.0, 0.6, -0.3).lerp(V(-1.0, 0.2, -0.6), pt)))
    aims.update(shield_hold(arm, SH_IDLE + V(0, 0, 0.005 * math.sin(w * 2 + 0.7)), SH_IDLE_N, SH_IDLE_A, pole=V(1.0, 0.5, -0.2)))
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


# ----------------------------------------------------------------------------------------------- the legion's stance
YAW = -20.0
SH_FIST = V(0.15, -0.4, 1.06)              # the shield's grip: its middle before her chest
SH_NORMAL = V(0.1, -1.0, 0.05)
SH_ACROSS = V(-1.0, -0.1, 0.0)             # the grip runs across the shield (it stands upright; her fist palm down)
SH_POLE = V(1.0, 0.1, -0.5)
GL_GRIP = V(-0.32, -0.2, 1.02)             # the gladius at her right hip
GL_DIR = V(0.06, -1.0, 0.16)
GL_FINGER = V(0.0, -0.15, -1.0)            # knuckles down: the blade's edges level
GL_POLE = V(-1.0, 0.5, -0.4)
RO0 = V(0.0, 0.0, -0.05)                   # the stance's root offset (its grips are placed for it)


def stance(arm, br=0.0, sway=0.0, lunge=0.0, crouch=0.0, chest=0.0, lift_l=0.0, lift_r=0.0, lf_fwd=0.0, head_up=0.0, lean=0.0,
           fwd=0.0):
    """`fwd`: the whole stance carried forward (the charge's steps), along her facing."""
    q = rz(YAW)
    aims = legs(arm, YAW, lf=(0.2, -0.18 - lf_fwd - fwd), rf=(-0.2, 0.19 - fwd), lift_l=lift_l, lift_r=lift_r)
    ro = q @ V(0.0, -0.15 * lunge - fwd, 0.0) + V(0.0, 0.0, -0.05 - 0.03 * crouch - 0.05 * lunge + 0.004 * br)
    rr = rz(YAW + 1.5 * sway)
    torso(aims, YAW + chest, lean=0.1 + 0.18 * lunge + lean, side=0.02 * sway, spine_tw=math.radians(chest * 0.4),
          chest_tw=math.radians(chest * 0.6), neck_tw=math.radians(-0.4 * (YAW + chest)), head_tw=math.radians(-0.6 * (YAW + chest)),
          head_up=0.1 + 0.05 * lunge + head_up)
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


# ----------------------------------------------------------------------------------------------- the thrust
def make_attack(arm, frames=21):
    """Draw back (0-4), lunge and thrust past the shield's edge (4-6, full reach at THRUST), hold (6-9), recover (9-21)."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    keys = [
        # frame, shield fist offset, shield normal, gladius grip, blade dir, lunge, crouch, chest twist, front foot forward
        (0, V(0, 0, 0), SH_NORMAL, GL_GRIP, GL_DIR, 0.0, 0.0, 0.0, 0.0),
        (4, V(0.0, 0.06, 0.0), SH_NORMAL, GL_GRIP + V(-0.02, 0.16, 0.02), V(0.02, -1.0, 0.12), -0.2, 0.35, -10.0, 0.0),
        (THRUST, V(0.12, -0.04, 0.03), V(0.35, -1.0, 0.0), V(-0.2, -0.66, 1.12), V(0.04, -1.0, 0.02), 1.0, 0.3, 12.0, 0.08),
        (9, V(0.12, -0.04, 0.03), V(0.35, -1.0, 0.0), V(-0.2, -0.69, 1.11), V(0.04, -1.0, 0.02), 1.05, 0.3, 13.0, 0.08),
        (frames, V(0, 0, 0), SH_NORMAL, GL_GRIP, GL_DIR, 0.0, 0.0, 0.0, 0.0),
    ]
    for f in range(frames + 1):
        i = max(k for k in range(len(keys) - 1) if keys[k][0] <= f) if f < frames else len(keys) - 2
        a, b = keys[i], keys[i + 1]
        k = (f - a[0]) / float(b[0] - a[0])
        k = k * k if i == 1 else ease(k)              # the thrust accelerates into its reach
        sh_off = a[1].lerp(b[1], k)
        sn = mixd(a[2], b[2], k)
        gg = a[3].lerp(b[3], k)
        gd = mixd(a[4], b[4], k)
        lunge, crouch, chest, fwd = lerp(a[5], b[5], k), lerp(a[6], b[6], k), lerp(a[7], b[7], k), lerp(a[8], b[8], k)
        step = math.sin(math.pi * min(1.0, max(0.0, (f - 3) / 4.0)))
        aims, ro, rr = stance(arm, 0.0, 0.0, lunge=lunge, crouch=crouch, chest=chest, lf_fwd=fwd, lift_l=0.03 * step)
        body = rz(YAW) @ V(0.0, -0.15 * lunge, -0.05 * lunge)
        aims.update(sword_grip(arm, gg + body * 0.5, gd, GL_FINGER, GL_POLE))
        aims.update(shield_hold(arm, SH_FIST + body + sh_off, sn, SH_ACROSS, SH_POLE))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- ability: shield charge
A_FR = 52
UP_G, UP_D, UP_F = V(-0.3, -0.24, 1.86), V(0.04, -0.62, 0.78), V(0.0, -0.75, -0.65)      # the gladius up and forward: "charge!"
LOW_G, LOW_D = V(-0.3, -0.06, 0.98), V(0.05, -1.0, 0.1)                                   # drawn back behind the shield
SH_LOW, SH_LOW_N = V(0.14, -0.34, 1.02), V(0.05, -1.0, 0.0)                               # tucked in, crouched behind it
SH_SLAM, SH_SLAM_N = V(0.1, -0.56, 1.0), V(0.0, -1.0, -0.06)                              # driven forward, arm locked
STEP1, STEP2 = 25, 29                                                                      # the charge's footfalls


def ability_state(f):
    """(shield fist, its normal, gladius grip, blade dir, knuckles, lunge, crouch, chest, head up, lean, forward) at f."""
    base = (SH_FIST, SH_NORMAL, GL_GRIP, GL_DIR, GL_FINGER, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    if f <= ORDER:                                          # the gladius thrust up and forward, the shield lowered a little
        k = ease(f / float(ORDER))
        return (SH_FIST.lerp(SH_FIST + V(0.04, 0.06, -0.06), k), SH_NORMAL, GL_GRIP.lerp(UP_G, k), mixd(GL_DIR, UP_D, k),
                mixd(GL_FINGER, UP_F, k), 0.0, lerp(0.0, -0.3, k), lerp(0.0, 10.0, k), lerp(0.0, 0.5, k), lerp(0.0, -0.12, k), 0.0)
    if f <= 18:                                             # held: the order rings out
        sh = 0.01 * math.sin((f - ORDER) * 2.2)
        return (SH_FIST + V(0.04, 0.06, -0.06), SH_NORMAL, UP_G + V(0, 0, sh), UP_D, UP_F, 0.0, -0.3, 10.0, 0.5, -0.12, 0.0)
    if f <= 23:                                             # down behind the shield, the gladius drawn back
        k = ease((f - 18) / 5.0)
        return ((SH_FIST + V(0.04, 0.06, -0.06)).lerp(SH_LOW, k), mixd(SH_NORMAL, SH_LOW_N, k), UP_G.lerp(LOW_G, k), mixd(UP_D, LOW_D, k),
                mixd(UP_F, GL_FINGER, k), lerp(0.0, 0.1, k), lerp(-0.3, 0.6, k), lerp(10.0, -6.0, k), lerp(0.5, 0.1, k),
                lerp(-0.12, 0.12, k), 0.0)
    if f <= SLAM:                                           # the charge: two driving steps, the boss slammed forward
        k = (f - 23) / float(SLAM - 23)
        kk = k * k
        return (SH_LOW.lerp(SH_SLAM, kk), mixd(SH_LOW_N, SH_SLAM_N, kk), LOW_G, LOW_D, GL_FINGER, lerp(0.1, 1.0, kk), lerp(0.6, 0.45, k),
                lerp(-6.0, -12.0, k), 0.1, lerp(0.12, 0.2, k), 0.34 * ease(k))
    if f <= 38:                                             # holding the line
        sh = 0.008 * math.sin((f - SLAM) * 2.6) * (1.0 - (f - SLAM) / 7.0)
        return (SH_SLAM + V(0, 0, sh), SH_SLAM_N, LOW_G, LOW_D, GL_FINGER, 1.0, 0.45, -12.0, 0.1, 0.2, 0.34)
    k = ease((f - 38) / float(A_FR - 38))                   # back into the stance (she steps back to her post)
    return (SH_SLAM.lerp(SH_FIST, k), mixd(SH_SLAM_N, SH_NORMAL, k), LOW_G.lerp(GL_GRIP, k), mixd(LOW_D, GL_DIR, k), GL_FINGER,
            lerp(1.0, 0.0, k), lerp(0.45, 0.0, k), lerp(-12.0, 0.0, k), lerp(0.1, 0.0, k), lerp(0.2, 0.0, k), lerp(0.34, 0.0, k))


def make_ability(arm, frames=A_FR):
    P = Poser(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        shf, shn, gg, gd, gf, lunge, crouch, chest, hup, lean, fwd = ability_state(f)
        lift_l = 0.06 * math.sin(math.pi * min(1.0, max(0.0, (f - (STEP1 - 3)) / 4.0)))
        lift_r = 0.06 * math.sin(math.pi * min(1.0, max(0.0, (f - (STEP2 - 3)) / 4.0)))
        back = 0.05 * math.sin(math.pi * min(1.0, max(0.0, (f - 40) / 8.0)))
        aims, ro, rr = stance(arm, 0.0, 0.0, lunge=lunge, crouch=crouch, chest=chest, head_up=hup, lean=lean, fwd=fwd,
                              lift_l=lift_l + back, lift_r=lift_r + back * 0.6)
        d = ro - RO0
        body = rz(YAW) @ V(0.0, -0.15 * lunge, 0.0)
        aims.update(sword_grip(arm, gg + d * 0.7 + body * 0.3, gd, gf, GL_POLE.lerp(V(-1.0, 0.3, -0.7), smooth01(1.0 - abs(f - ORDER) / 8.0))))
        aims.update(shield_hold(arm, shf + d, shn, SH_ACROSS, SH_POLE))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- cheer
CH_G, CH_D, CH_F = V(-0.3, -0.06, 1.94), V(-0.05, -0.15, 1.0), V(0.1, -1.0, 0.1)            # the gladius up at the sky
SH_CH, SH_CH_N, SH_CH_A = V(0.38, -0.24, 1.5), V(0.55, -0.8, 0.2), V(-0.82, -0.56, 0.0)     # the shield raised high


def make_cheer(arm, frames=40):
    """Rank up: the gladius thrust up overhead twice, the shield raised, a hop."""
    P = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        t = f / frames
        up = smooth01(t / 0.15) * (1 - smooth01((t - 0.82) / 0.18))
        pump = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.4)) * up
        hop = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.9)) * 0.04 * up
        aims, ro, rr = stance(arm, 0.0, 0.0, crouch=-0.4 * up, head_up=0.5 * up, lean=-0.1 * up)
        ro = ro + V(0.0, 0.0, hop)
        d = ro - RO0
        g = GL_GRIP.lerp(CH_G + V(0.0, 0.0, 0.1 * pump - 0.06), up)
        aims.update(sword_grip(arm, g + d, mixd(GL_DIR, CH_D, up), mixd(GL_FINGER, CH_F, up), GL_POLE.lerp(V(-1.0, 0.3, -0.5), up)))
        shf = SH_FIST.lerp(SH_CH + V(0.0, 0.0, -0.06 + 0.05 * pump), up)
        aims.update(shield_hold(arm, shf + d, mixd(SH_NORMAL, SH_CH_N, up), mixd(SH_ACROSS, SH_CH_A, up), SH_POLE.lerp(V(1.0, 0.3, -0.2), up)))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
