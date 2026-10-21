"""Sir Aldric's clips (keyed in frames, like the other heroes'; the game plays them at CLIP_FPS 24).

Idle    : standing easy, the heater shield carried at his left side, the longsword held point-down at his right; he
          breathes, shifts his weight, looks over the field, and once a loop lifts the sword and points it ahead, an
          order given.
Combat  : the guard: left foot forward, knees bent, the shield up before his chest, the sword raised over his right
          shoulder, its point up and back; a slow bob.
Attack  : (21 frames: inside the 0.7 s cooldown) from the guard he cocks the sword back (0-3) and cuts down and across
          past the shield's edge: the stroke lands at CUT (frame 7: game.gd's hit), follows through low on his left,
          and he recovers into the guard.
Ability : Holy Lance (50 frames): he raises the sword straight up to the sky and holds it there while the light gathers
          on it (GATHER, frame 16: game.gd's glint on the blade), then sweeps it down to point at the robots (STRIKE,
          frame 30: game.gd's lances of light fall on the strongest of them); he holds the point, and settles back into
          the guard.
Cheer   : (rank up) the sword thrust up overhead twice, the shield raised, a hop.

The sword and the shield are rigid in his fists ("frame" aims): the blade along the right fist's thumb axis, the shield's
grip (across its back behind the middle) in the left fist along its thumb axis, its face along the knuckles."""
import math
from mathutils import Vector, Quaternion
import aldric as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
ROOT = Vector(J["root"])

_G, _T, _E, _W = cm.sword_frame()
T_REST, E_REST = Vector(_T), Vector(_E)
_wr, _f, _n, _t = cm.hand_frame("R")
FIST_OFF_R = Vector(cm.fist_center("R") - _wr)       # wrist -> grip centre (rest)
_SG, _SN, _SU, _SS = cm.heater_frame()
G_REST, N_REST, U_REST = Vector(_SG), Vector(_SN), Vector(_SU)
WR_L_REST = Vector(J["wrist_L"])
CUT = 7                # game.gd ATTACK_FRAME: the stroke lands
GATHER = 16            # the light gathers on the raised blade (game.gd ALDRIC_GATHER)
STRIKE = 30            # the sword points at the robots: the lances fall (game.gd ALDRIC_STRIKE)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def sword_grip(arm, grip, blade_dir, edge, pole):
    """Right fist (its grip centre) at `grip`, the blade along `blade_dir`, its edge (the knuckles' side) toward `edge`."""
    sd = Vector(blade_dir).normalized()
    R = frame_map(T_REST, sd, E_REST, Vector(edge))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF_R, pole=pole)
    aims["hand.R"] = ("frame", T_REST, sd, E_REST, Vector(edge))
    return aims


def shield_hold(arm, fist, normal, across, pole):
    """Left fist at `fist` holding the shield's grip, its face toward `normal`, the grip (across the shield) along
    `across` (inward, toward his right, keeps the shield's top up)."""
    nrm = Vector(normal).normalized()
    R = frame_map(N_REST, nrm, U_REST, Vector(across))
    aims = arm_aims(arm, "L", Vector(fist) - R @ (G_REST - WR_L_REST), pole=pole)
    aims["hand.L"] = ("frame", N_REST, nrm, U_REST, Vector(across))
    return aims


def legs(arm, yaw, lf=(0.21, -0.1), rf=(-0.21, 0.13), lift_l=0.0, lift_r=0.0, open_feet=0.6):
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
SH_IDLE = V(0.46, -0.06, 0.84)
SH_IDLE_N, SH_IDLE_A = V(0.6, -0.8, 0.02), V(-0.8, -0.6, 0.0)          # (across inward: its top up)
SW_IDLE = V(-0.4, -0.12, 0.88)
SW_IDLE_D, SW_IDLE_E = V(-0.08, -0.25, -1.0), V(0.0, -1.0, 0.1)
SW_POINT, SW_POINT_D, SW_POINT_E = V(-0.34, -0.46, 1.3), V(0.05, -1.0, 0.18), V(0.0, -0.2, -1.0)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm, -5.0, lf=(0.2, -0.03), rf=(-0.2, 0.07), open_feet=0.3)
    ro = V(0.01 * math.sin(w), 0.0, -0.006 + 0.005 * br)
    rr = rz(-5.0 + 2.0 * math.sin(w))
    pt = math.sin(math.pi * smooth01((t - 0.5) / 0.3)) if 0.5 <= t <= 0.8 else 0.0
    pt = smooth01(pt * 1.6)
    look = (0.45 * math.sin(w) + 0.12 * math.sin(w * 3)) * (1.0 - pt)
    torso(aims, -5.0 + 6.0 * pt, lean=-0.02 + 0.04 * pt, side=0.02 * math.sin(w), spine_tw=0.03 * math.sin(w),
          chest_tw=0.05 * math.sin(w), neck_tw=0.3 * look, head_tw=0.7 * look, head_up=0.07 + 0.04 * br + 0.06 * pt)
    q = rz(-5.0)
    aims["clavicle.L"] = q @ V(1.0, 0.0, -0.02)
    aims["clavicle.R"] = q @ V(-1.0, 0.0, 0.03 + 0.12 * pt)
    g = SW_IDLE.lerp(SW_POINT, pt) + V(0, 0, 0.004 * br)
    aims.update(sword_grip(arm, g, mixd(SW_IDLE_D, SW_POINT_D, pt), mixd(SW_IDLE_E, SW_POINT_E, pt),
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


# ----------------------------------------------------------------------------------------------- the guard
YAW = -20.0
SH_FIST = V(0.18, -0.44, 1.08)             # the shield's grip before his chest
SH_NORMAL = V(0.1, -1.0, 0.05)
SH_ACROSS = V(-1.0, -0.1, 0.0)             # the grip runs across the shield, his fist palm down (its top up)
SH_POLE = V(1.0, 0.1, -0.5)
SW_GRIP = V(-0.36, -0.04, 1.52)            # the sword raised over his right shoulder...
SW_DIR = V(0.12, 0.32, 1.0)                # ...its point up and back
SW_EDGE = V(0.15, -1.0, 0.2)               # its edge forward
SW_POLE = V(-1.0, 0.2, -0.6)


def stance(arm, br=0.0, sway=0.0, lunge=0.0, crouch=0.0, chest=0.0, lift_l=0.0, lift_r=0.0, lf_fwd=0.0, head_up=0.0, lean=0.0):
    q = rz(YAW)
    aims = legs(arm, YAW, lf=(0.22, -0.2 - lf_fwd), rf=(-0.22, 0.2), lift_l=lift_l, lift_r=lift_r)
    ro = q @ V(0.0, -0.12 * lunge, 0.0) + V(0.0, 0.0, -0.05 - 0.03 * crouch - 0.05 * lunge + 0.004 * br)
    rr = rz(YAW + 1.5 * sway)
    torso(aims, YAW + chest, lean=0.08 + 0.18 * lunge + lean, side=0.02 * sway, spine_tw=math.radians(chest * 0.4),
          chest_tw=math.radians(chest * 0.6), neck_tw=math.radians(-0.4 * (YAW + chest)), head_tw=math.radians(-0.6 * (YAW + chest)),
          head_up=0.1 + 0.05 * lunge + head_up)
    qc = rz(YAW + chest)
    aims["clavicle.L"] = qc @ V(1.0, -0.15, 0.04)
    aims["clavicle.R"] = qc @ V(-1.0, 0.0, 0.12)
    return aims, ro, rr


RO0 = V(0.0, 0.0, -0.05)


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    aims, ro, rr = stance(arm, br, sw)
    bob = V(0.0, 0.0, 0.008 * br)
    aims.update(sword_grip(arm, SW_GRIP + bob, (SW_DIR + V(0.02 * sw, 0, 0)).normalized(), SW_EDGE, SW_POLE))
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


# ----------------------------------------------------------------------------------------------- the cut
def make_attack(arm, frames=21):
    """Cock (0-3), the cut down and across past the shield's edge (3-7, it lands at CUT), follow through (7-10),
    recover (10-21)."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    keys = [
        # frame, sword grip, blade dir, edge, shield offset, lunge, crouch, chest twist
        (0, SW_GRIP, SW_DIR, SW_EDGE, V(0, 0, 0), 0.0, 0.0, 0.0),
        (3, SW_GRIP + V(-0.04, 0.08, 0.06), V(0.2, 0.75, 0.6), V(0.1, -0.7, 0.7), V(0.0, 0.05, 0.0), -0.15, 0.25, -14.0),
        (CUT, V(-0.12, -0.62, 1.16), V(0.55, -0.82, -0.18), V(0.3, 0.1, -1.0), V(0.12, 0.06, -0.04), 1.0, 0.35, 16.0),
        (10, V(0.0, -0.5, 0.96), V(0.85, -0.3, -0.42), V(0.25, 0.2, -1.0), V(0.12, 0.06, -0.04), 0.9, 0.4, 22.0),
        (frames, SW_GRIP, SW_DIR, SW_EDGE, V(0, 0, 0), 0.0, 0.0, 0.0),
    ]
    for f in range(frames + 1):
        i = max(k for k in range(len(keys) - 1) if keys[k][0] <= f) if f < frames else len(keys) - 2
        a, b = keys[i], keys[i + 1]
        k = (f - a[0]) / float(b[0] - a[0])
        k = k * k if i == 1 else ease(k)                  # the cut accelerates into the stroke
        gg = a[1].lerp(b[1], k)
        gd = mixd(a[2], b[2], k)
        ge = mixd(a[3], b[3], k)
        sh_off = a[4].lerp(b[4], k)
        lunge, crouch, chest = lerp(a[5], b[5], k), lerp(a[6], b[6], k), lerp(a[7], b[7], k)
        step = math.sin(math.pi * min(1.0, max(0.0, (f - 2) / 5.0)))
        aims, ro, rr = stance(arm, 0.0, 0.0, lunge=lunge, crouch=crouch, chest=chest, lf_fwd=0.06 * lunge, lift_l=0.03 * step)
        body = rz(YAW) @ V(0.0, -0.12 * lunge, -0.05 * lunge)
        aims.update(sword_grip(arm, gg + body * 0.5, gd, ge, SW_POLE.lerp(V(-1.0, 0.5, -0.2), smooth01(lunge))))
        aims.update(shield_hold(arm, SH_FIST + body + sh_off, SH_NORMAL, SH_ACROSS, SH_POLE))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- ability: holy lance
A_FR = 50
UP_G, UP_D, UP_E = V(-0.28, -0.12, 2.02), V(0.02, -0.08, 1.0), V(0.0, -1.0, 0.0)          # the sword straight up at the sky
PT_G, PT_D, PT_E = V(-0.26, -0.6, 1.36), V(0.05, -1.0, 0.12), V(0.0, -0.1, -1.0)           # pointed at the robots
SH_LOW = V(0.3, -0.26, 0.96)                                                                 # the shield lowered a little


def ability_state(f):
    """(sword grip, blade dir, edge, shield fist, lunge, crouch, chest, head up, lean) at f."""
    if f <= 12:                                             # up to the sky
        k = ease(f / 12.0)
        return (SW_GRIP.lerp(UP_G, k), mixd(SW_DIR, UP_D, k), mixd(SW_EDGE, UP_E, k), SH_FIST.lerp(SH_LOW, k), 0.0,
                lerp(0.0, -0.4, k), lerp(0.0, 8.0, k), lerp(0.0, 0.7, k), lerp(0.0, -0.14, k))
    if f <= 24:                                             # held up while the light gathers
        sh = 0.006 * math.sin((f - 12) * 1.7)
        return (UP_G + V(0, 0, sh), UP_D, UP_E, SH_LOW, 0.0, -0.4, 8.0, 0.7, -0.14)
    if f <= STRIKE:                                         # swept down to point at them
        k = (f - 24) / float(STRIKE - 24)
        kk = k * k
        return (UP_G.lerp(PT_G, kk), mixd(UP_D, PT_D, kk), mixd(UP_E, PT_E, kk), SH_LOW, lerp(0.0, 0.8, kk), lerp(-0.4, 0.3, k),
                lerp(8.0, 14.0, k), lerp(0.7, 0.15, k), lerp(-0.14, 0.12, k))
    if f <= 38:                                             # holding the point
        sh = 0.006 * math.sin((f - STRIKE) * 2.4) * (1.0 - (f - STRIKE) / 8.0)
        return (PT_G + V(0, 0, sh), PT_D, PT_E, SH_LOW, 0.8, 0.3, 14.0, 0.15, 0.12)
    k = ease((f - 38) / float(A_FR - 38))                   # back into the guard
    return (PT_G.lerp(SW_GRIP, k), mixd(PT_D, SW_DIR, k), mixd(PT_E, SW_EDGE, k), SH_LOW.lerp(SH_FIST, k), lerp(0.8, 0.0, k),
            lerp(0.3, 0.0, k), lerp(14.0, 0.0, k), lerp(0.15, 0.0, k), lerp(0.12, 0.0, k))


def make_ability(arm, frames=A_FR):
    P = Poser(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        gg, gd, ge, shf, lunge, crouch, chest, hup, lean = ability_state(f)
        aims, ro, rr = stance(arm, 0.0, 0.0, lunge=lunge, crouch=crouch, chest=chest, head_up=hup, lean=lean,
                              lf_fwd=0.08 * lunge, lift_l=0.04 * math.sin(math.pi * min(1.0, max(0.0, (f - 25) / 6.0))))
        d = ro - RO0
        pole = SW_POLE.lerp(V(-1.0, 0.3, -0.2), smooth01(1.0 - abs(f - 18) / 10.0))
        aims.update(sword_grip(arm, gg + d * 0.7, gd, ge, pole))
        aims.update(shield_hold(arm, shf + d, SH_NORMAL, SH_ACROSS, SH_POLE))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- cheer
CH_G, CH_D, CH_E = V(-0.34, -0.06, 2.0), V(-0.05, -0.15, 1.0), V(0.1, -1.0, 0.1)
SH_CH, SH_CH_N, SH_CH_A = V(0.42, -0.24, 1.5), V(0.55, -0.8, 0.2), V(-0.82, -0.56, 0.0)


def make_cheer(arm, frames=40):
    """Rank up: the sword thrust up overhead twice, the shield raised, a hop."""
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
        g = SW_GRIP.lerp(CH_G + V(0.0, 0.0, 0.1 * pump - 0.06), up)
        aims.update(sword_grip(arm, g + d, mixd(SW_DIR, CH_D, up), mixd(SW_EDGE, CH_E, up), SW_POLE.lerp(V(-1.0, 0.3, -0.5), up)))
        shf = SH_FIST.lerp(SH_CH + V(0.0, 0.0, -0.06 + 0.05 * pump), up)
        aims.update(shield_hold(arm, shf + d, mixd(SH_NORMAL, SH_CH_N, up), mixd(SH_ACROSS, SH_CH_A, up), SH_POLE.lerp(V(1.0, 0.3, -0.2), up)))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
