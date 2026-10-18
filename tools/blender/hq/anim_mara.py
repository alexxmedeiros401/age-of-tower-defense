"""Mara's clips (30 fps): Idle (staff planted at her side, her left hand turned palm-down to feel the earth), Combat
(staff up, her left hand reaching out over the ground, calling), Attack (a thump of the staff: the amber orb flares),
Ability (Earthquake: both hands raise the staff high, she drives it into the ground in a deep crouch) and Cheer (rank up:
staff thrust overhead, a fist pump and a hop).

The staff is rigid in her right fist ("frame" aims, as for the Tar Shaman); the orb has its own bone whose scale pulses."""
import math
from mathutils import Vector, Quaternion
import mara as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
T_REST = Vector(cm.staff_axis()[1])
_wr, _f, _n, _t = cm.hand_frame("R")
F_REST = Vector(_f)
FIST_OFF = Vector(cm.fist_center("R") - _wr)
BELOW = 1.12 + 0.03


def grip(arm, wrist, staff_dir, pole, finger=None):
    aims = arm_aims(arm, "R", wrist, pole=pole)
    sd = Vector(staff_dir).normalized()
    def hand(P, base):
        fd = Vector(finger) if finger is not None else P["forearm.R"].col[1].xyz.normalized()
        return ("frame", T_REST, sd, F_REST, fd)
    aims["hand.R"] = hand
    return aims


def planted_wrist(butt, staff_dir, finger):
    sd = Vector(staff_dir).normalized()
    R = frame_map(T_REST, sd, F_REST, Vector(finger))
    return Vector(butt) + sd * BELOW - R @ FIST_OFF


def planted(arm, butt, staff_dir, finger, pole):
    return grip(arm, planted_wrist(butt, staff_dir, finger), staff_dir, pole, finger=finger)


def staff_point(butt, staff_dir, s):
    """A point on a planted staff, s up from the grip."""
    sd = Vector(staff_dir).normalized()
    return Vector(butt) + sd * (BELOW + s)


def legs(arm, wide=1.0, hop=0.0):
    aR = J["ankle_R"] + V(-0.03 * wide, 0.05 * wide, hop)
    aL = J["ankle_L"] + V(0.03 * wide, -0.05 * wide, hop)
    aims = {}
    aims.update(leg_aims(arm, "R", aR, pole=V(-0.2, -1, 0.1)))
    aims.update(leg_aims(arm, "L", aL, pole=V(0.2, -1, 0.1)))
    return aims


def torso(aims, lean=0.0, twist=0.0, side=0.0, head_up=0.0, look=0.0):
    aims["spine"] = (V(side * 0.15, 0.03 - 0.25 * lean, 1.0), twist * 0.4)
    aims["chest"] = (V(side * 0.2, 0.02 - 0.35 * lean, 1.0), twist)
    aims["neck"] = V(side * 0.05, -0.22 + 0.4 * head_up + 0.2 * lean, 1.0)
    aims["head"] = (V(0.0, -0.1 + 0.6 * head_up + 0.2 * lean, 1.0), look)


BUTT_IDLE = V(-0.4, -0.12, 0.0)
SD_IDLE = V(0.03, 0.02, 1.0)
FING = V(0.4, -0.9, 0.0)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm, wide=0.9)
    ro = V(0.0, 0.0, -0.01 + 0.006 * br)
    rr = Quaternion((0, 0, 1), math.radians(3 * math.sin(w)))
    torso(aims, lean=0.0, twist=0.04 * math.sin(w), head_up=0.04 * br, look=0.35 * math.sin(w) + 0.12 * math.sin(w * 3))
    aims["clavicle.R"] = V(-1.0, 0.0, 0.05)
    aims["clavicle.L"] = V(1.0, 0.0, 0.0)
    aims.update(planted(arm, BUTT_IDLE, SD_IDLE, FING, pole=V(-1.0, 0.5, -0.3)))
    wl = V(0.4, -0.12, 0.9 + 0.02 * math.sin(w * 2 + 0.5))
    aims.update(arm_aims(arm, "L", wl, pole=V(1.0, 0.3, -0.2), hand_dir=V(0.6, -0.4, -0.25)))
    return aims, ro, rr, {"orb": 1.0 + 0.04 * math.sin(w * 3)}


def combat_pose(arm, t):
    w = 2 * math.pi * t
    sway = math.sin(w)
    aims = legs(arm, wide=1.15)
    ro = V(0.01 * sway, -0.02, -0.035 + 0.008 * math.sin(w * 2))
    rr = Quaternion((0, 0, 1), math.radians(-6 + 4 * sway))
    torso(aims, lean=0.15, twist=-0.15, side=0.08 * sway, head_up=0.08, look=0.15)
    aims["clavicle.R"] = V(-1.0, -0.1, 0.2)
    aims["clavicle.L"] = V(1.0, -0.25, 0.1)
    aims.update(grip(arm, V(-0.36, -0.22, 1.18 + 0.015 * math.sin(w * 2)), V(0.05, -0.1, 1.0), pole=V(-1.0, 0.3, -0.5)))
    cx, cz = 0.02 * math.cos(w * 2), 0.02 * math.sin(w * 2)
    aims.update(arm_aims(arm, "L", V(0.3 + cx, -0.56, 1.05 + cz), pole=V(1.0, 0.4, -0.5), hand_dir=V(0.05, -1.0, -0.4)))
    return aims, ro, rr, {"orb": 1.0 + 0.08 * math.sin(w * 2)}


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr, sc = idle_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr, scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr, sc = combat_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr, scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_attack(arm, frames=30, slam=4):
    """Lift the staff, thump it down (the orb flares, her left hand pushes down at the ground), ease back."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    c_wr, c_sd = V(-0.36, -0.22, 1.18), V(0.05, -0.1, 1.0)
    up_wr, up_sd = V(-0.37, -0.28, 1.42), V(0.04, -0.16, 1.0)
    butt = V(-0.38, -0.42, 0.0)
    sd_s = V(0.02, -0.08, 1.0).normalized()
    for f in range(frames + 1):
        aims = legs(arm, wide=1.15)
        if f <= 2:
            k = ease(f / 2)
            aims.update(grip(arm, lerp(c_wr, up_wr, k), lerp(c_sd, up_sd, k), pole=V(-1.0, 0.3, -0.5)))
            lean, push, orb = lerp(0.15, 0.0, k), 0.0, 1.0 + 0.15 * k
        elif f <= slam:
            k = ease((f - 2) / (slam - 2))
            sd = lerp(up_sd.normalized(), sd_s, k).normalized()
            aims.update(grip(arm, lerp(up_wr, planted_wrist(butt, sd_s, FING), k), sd, pole=V(-1.0, 0.3, -0.5), finger=FING))
            lean, push, orb = lerp(0.0, 0.35, k), k, 1.15 + 0.7 * k
        elif f <= 12:
            k = (f - slam) / (12 - slam)
            aims.update(planted(arm, butt, sd_s, FING, pole=V(-1.0, 0.3, -0.5)))
            lean, push, orb = 0.35 - 0.05 * k, 1.0, 1.85 - 0.6 * ease(k)
        else:
            k = ease((f - 12) / (frames - 12))
            aims.update(grip(arm, lerp(planted_wrist(butt, sd_s, FING), c_wr, k), lerp(sd_s, c_sd.normalized(), k), pole=V(-1.0, 0.3, -0.5),
                             finger=lerp(FING, V(0.3, -0.9, 0.3), k)))
            lean, push, orb = lerp(0.3, 0.15, k), 1.0 - k, lerp(1.25, 1.0, k)
        ro = V(0.0, -0.04 * lean, -0.035 - 0.06 * max(0.0, lean - 0.15))
        rr = Quaternion((0, 0, 1), math.radians(-6))
        torso(aims, lean=lean, twist=-0.15, head_up=0.08 - 0.1 * push, look=0.15)
        aims["clavicle.R"] = V(-1.0, -0.1, 0.2)
        aims["clavicle.L"] = V(1.0, -0.25, 0.1)
        wl = lerp(V(0.3, -0.56, 1.05), V(0.32, -0.6, 0.82), push)
        aims.update(arm_aims(arm, "L", wl, pole=V(1.0, 0.4, -0.5), hand_dir=lerp(V(0.05, -1.0, -0.4), V(0.1, -0.5, -1.0), push).normalized()))
        ch, _ = P.solve(aims, ro, rr, scales={"orb": orb})
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_ability(arm, frames=54):
    """Earthquake: both hands raise the staff high over her head, a breath, then she drives its butt into the ground
    in a deep crouch (frame 22) and holds while the earth shakes, then rises."""
    P = Poser(arm)
    act = new_action(arm, "Ability")
    hi_wr, hi_sd = V(-0.12, -0.1, 1.98), V(0.02, -0.12, 1.0)
    butt = V(-0.12, -0.5, 0.0)
    sd_s = V(0.0, -0.05, 1.0).normalized()
    idle_wr = planted_wrist(BUTT_IDLE, SD_IDLE, FING)
    for f in range(frames + 1):
        if f <= 14:                                           # raise it high with both hands, rise on her toes
            k = ease(f / 14)
            wr = lerp(idle_wr, hi_wr, k)
            sd = lerp(SD_IDLE.normalized(), hi_sd.normalized(), k).normalized()
            crouch, lean, head, orb, hop = lerp(0.0, -0.02, k), lerp(0.0, -0.18, k), lerp(0.0, 0.45, k), 1.0 + 0.3 * k, 0.0
        elif f <= 19:                                         # hold, the orb gathering light
            k = (f - 14) / 5
            wr, sd = hi_wr + V(0, 0, 0.01 * math.sin(k * math.pi)), hi_sd.normalized()
            crouch, lean, head, orb, hop = -0.02, -0.18, 0.45, 1.3 + 0.3 * k, 0.0
        elif f <= 22:                                         # drive it down
            k = (f - 19) / 3
            k = k * k
            wr = lerp(hi_wr, planted_wrist(butt, sd_s, FING), k)
            sd = lerp(hi_sd.normalized(), sd_s, k).normalized()
            crouch, lean, head, orb, hop = lerp(-0.02, 0.2, k), lerp(-0.18, 0.5, k), lerp(0.45, -0.1, k), 1.6 + 0.6 * k, 0.0
        elif f <= 34:                                         # hold low while the ground shakes
            k = (f - 22) / 12
            wr, sd = planted_wrist(butt, sd_s, FING) + V(0.01 * math.sin(f * 2.3), 0, 0), sd_s
            crouch, lean, head, orb, hop = 0.2 - 0.02 * k, 0.5 - 0.05 * k, -0.1 + 0.1 * k, 2.2 - 0.8 * k, 0.0
        else:                                                 # rise back to her idle stance
            k = ease((f - 34) / (frames - 34))
            wr = lerp(planted_wrist(butt, sd_s, FING), idle_wr, k)
            sd = lerp(sd_s, SD_IDLE.normalized(), k).normalized()
            crouch, lean, head, orb, hop = lerp(0.18, 0.0, k), lerp(0.45, 0.0, k), lerp(0.0, 0.0, k), lerp(1.4, 1.0, k), 0.0
        aims = legs(arm, wide=1.25)
        ro = V(0.0, -0.05 * max(0.0, lean), -crouch)
        rr = Quaternion((0, 0, 1), math.radians(-4))
        torso(aims, lean=lean, head_up=head)
        aims["clavicle.R"] = V(-1.0, 0.0, 0.05 + 0.4 * max(0.0, wr.z - 1.4))
        aims["clavicle.L"] = V(1.0, 0.0, 0.05 + 0.4 * max(0.0, wr.z - 1.4))
        aims.update(grip(arm, wr, sd, pole=V(-1.0, 0.4, -0.3), finger=FING if f > 19 else None))
        # left hand on the staff above the right (both hands), sliding off to the ground at the slam
        sdv = Vector(sd).normalized()
        g = wr + FIST_OFF.length * 0 * sdv
        on_staff = g + sdv * 0.22 + V(0.06, 0.0, 0.0)
        if f <= 19:
            wl = on_staff
            hd = (on_staff - V(0.4, 0.05, 1.4)).normalized()
        elif f <= 34:
            k = min(1.0, (f - 19) / 3)
            wl = lerp(on_staff, V(0.34, -0.5, 0.35 - 0.02 * (f - 22) / 12), k)
            hd = lerp((on_staff - V(0.4, 0.05, 1.4)).normalized(), V(0.0, -0.4, -1.0), k).normalized()
        else:
            k = ease((f - 34) / (frames - 34))
            wl = lerp(V(0.34, -0.5, 0.33), V(0.4, -0.12, 0.9), k)
            hd = lerp(V(0.0, -0.4, -1.0), V(0.6, -0.4, -0.25), k).normalized()
        aims.update(arm_aims(arm, "L", wl, pole=V(1.0, 0.3, -0.4), hand_dir=hd))
        ch, _ = P.solve(aims, ro, rr, scales={"orb": orb})
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_cheer(arm, frames=40):
    """Rank up: the staff thrust overhead, two pumps of her left fist, a hop."""
    P = Poser(arm)
    act = new_action(arm, "Cheer")
    idle_wr = planted_wrist(BUTT_IDLE, SD_IDLE, FING)
    for f in range(frames + 1):
        t = f / frames
        pump = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.4)) * (1 - max(0.0, (t - 0.8) / 0.2))
        hop = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.9)) * 0.04 * (1 - max(0.0, (t - 0.75) / 0.25))
        up = ease(min(1.0, t / 0.15)) * (1 - ease(max(0.0, (t - 0.8) / 0.2)))
        aims = legs(arm, wide=0.95, hop=hop * 0.6)
        ro = V(0.0, 0.0, -0.02 + hop)
        rr = Quaternion((0, 0, 1), math.radians(5 * math.sin(t * math.pi)))
        torso(aims, lean=-0.05 * pump, head_up=0.1 + 0.35 * pump, look=math.radians(6 * math.sin(t * 9)))
        aims["clavicle.R"] = V(-1.0, 0.0, 0.05 + 0.35 * up)
        aims["clavicle.L"] = V(1.0, 0.0, 0.05 + 0.3 * pump)
        wr = lerp(idle_wr, V(-0.3, -0.06, 1.95), up)
        sd = lerp(SD_IDLE.normalized(), V(-0.1, -0.05, 1.0).normalized(), up).normalized()
        aims.update(grip(arm, wr, sd, pole=V(-1.0, 0.3, -0.3)))
        wl = lerp(V(0.42, -0.12, 1.42), V(0.46, -0.08, 1.98), pump)
        wl = lerp(V(0.4, -0.12, 0.9), wl, up)
        aims.update(arm_aims(arm, "L", wl, pole=V(1.0, 0.3, -0.5), hand_dir=(wl - V(0.4, 0.06, 1.38)).normalized()))
        ch, _ = P.solve(aims, ro, rr, scales={"orb": 1.0 + 0.4 * pump})
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
