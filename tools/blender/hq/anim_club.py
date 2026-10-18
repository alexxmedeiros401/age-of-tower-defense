"""Club Warrior clips (30 fps): Idle (club on his shoulder, rolling his neck), Combat (club cocked high, bouncing on his
feet, left fist out) and Attack (an overhead smash into the ground in front of him, then back up).

The club is rigid in his right fist, so the fist's orientation is posed directly ("frame" aims): the club's direction
plus the direction his fingers point (which follows the forearm, so the wrist stays natural)."""
import math
from mathutils import Vector, Quaternion
import club_warrior as cm
from rig import Poser, leg_aims, arm_aims
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
T_REST = Vector(cm.club_axis()[1])          # the club's direction in the rest pose (along the fist)
F_REST = Vector(cm.hand_frame("R")[1])      # the fingers' direction in the rest pose
V = lambda *a: Vector(a)


def grip(arm, wrist, club_dir, pole, finger=None):
    """Right arm to `wrist`, club pointing along `club_dir`; fingers along the forearm unless `finger` is given."""
    aims = arm_aims(arm, "R", wrist, pole=pole)
    cd = Vector(club_dir).normalized()
    def hand(P, base):
        fd = Vector(finger) if finger is not None else P["forearm.R"].col[1].xyz.normalized()
        return ("frame", T_REST, cd, F_REST, fd)
    aims["hand.R"] = hand
    return aims


def fist_L(arm, wrist, pole, fdir=None):
    return arm_aims(arm, "L", wrist, pole=pole, hand_dir=fdir)


def legs(arm, wide=1.0, shift=0.0, lift_R=0.0, lift_L=0.0, fwd_L=0.0):
    aR = J["ankle_R"] + V(-0.05 * wide + shift * 0.3, 0.1 * wide, lift_R)
    aL = J["ankle_L"] + V(0.05 * wide + shift * 0.3, -0.1 * wide - fwd_L, lift_L)
    aims = {}
    aims.update(leg_aims(arm, "R", aR, pole=V(-0.3, -1, 0.1)))
    aims.update(leg_aims(arm, "L", aL, pole=V(0.3, -1, 0.1)))
    return aims


def torso(aims, lean=0.0, twist=0.0, side=0.0, head_up=0.0, look=0.0, breathe=0.0):
    """lean > 0 = forward; twist (rad) turns the chest to his left; head_up > 0 lifts the chin; look turns the head."""
    aims["spine"] = (V(side * 0.15, 0.06 - 0.3 * lean, 1.0), twist * 0.4)
    aims["chest"] = (V(side * 0.2, 0.03 - 0.36 * lean + 0.03 * breathe, 1.0), twist)
    aims["neck"] = V(0.0, -0.42 + 0.5 * head_up + 0.2 * lean, 1.0)
    aims["head"] = (V(0.0, -0.2 + 0.7 * head_up + 0.15 * lean, 1.0), look)


# ---------------------------------------------------------------------------------------------- poses
REST_WR = V(-0.4, -0.3, 1.24)             # idle: fist in front of his right shoulder, club over it
REST_CLUB = V(-0.12, 0.7, 0.7)
COCK_WR = V(-0.5, 0.02, 1.86)             # combat: club cocked high over his right shoulder
COCK_CLUB = V(0.18, 0.55, 0.82)
HIT_WR = V(-0.16, -0.5, 0.8)              # attack: fist low in front, club head on the ground
HIT_CLUB = V(0.1, -0.62, -0.78)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    shift = 0.5 * math.sin(w)
    aims = legs(arm, wide=0.9, shift=shift)
    ro = V(0.012 * shift, 0.0, -0.02 + 0.008 * br)
    rr = Quaternion((0, 0, 1), math.radians(5 * math.sin(w)))
    # a neck roll in the second half of the loop
    roll = max(0.0, math.sin(w - 0.6)) ** 2
    look = 0.4 * math.sin(w) + 0.25 * math.sin(w * 3 + 0.4)
    torso(aims, lean=0.1, twist=0.06 * math.sin(w), side=-0.05 * shift, head_up=0.05 * br + 0.15 * roll, look=look, breathe=br)
    aims["clavicle.R"] = V(-1.0, -0.05, 0.12)
    aims["clavicle.L"] = V(1.0, 0.0, 0.0 + 0.04 * br)
    tap = 0.02 * max(0.0, math.sin(w * 3)) ** 4                 # taps the club on his shoulder now and then
    aims.update(grip(arm, REST_WR + V(0.0, 0.0, tap), REST_CLUB + V(0.0, 0.0, -tap * 3), pole=V(-1.0, -0.1, -0.6)))
    aims.update(fist_L(arm, V(0.62, -0.06, 0.86 + 0.01 * br), pole=V(1.0, 0.6, 0.0), fdir=V(0.15, -0.2, -1.0)))
    return aims, ro, rr


def combat_pose(arm, t, k_bounce=1.0):
    w = 2 * math.pi * t
    b = math.sin(w * 2)
    aims = legs(arm, wide=1.25, fwd_L=0.06)
    ro = V(0.0, -0.03, -0.075 + 0.014 * b * k_bounce)
    rr = Quaternion((0, 0, 1), math.radians(-14))
    torso(aims, lean=0.22, twist=0.25, head_up=0.05, look=-0.22, breathe=b)
    aims["clavicle.R"] = V(-1.0, 0.05, 0.4)
    aims["clavicle.L"] = V(1.0, -0.2, 0.08)
    aims.update(grip(arm, COCK_WR + V(0, 0, 0.012 * b), COCK_CLUB, pole=V(-1.0, 0.4, 0.2)))
    aims.update(fist_L(arm, V(0.44, -0.52, 1.24 + 0.01 * b), pole=V(1.0, 0.0, -0.8), fdir=V(0.1, -1.0, 0.1)))
    return aims, ro, rr


# ---------------------------------------------------------------------------------------------- clips
def make_idle(arm, frames=90):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=32):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr = combat_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


SMASH = 4          # frame the club hits the ground


def make_attack(arm, frames=24):
    """From the combat pose: a short extra wind-up, then the club comes over the top and down into the ground in front
    (impact at SMASH), a bounce, and he hauls it back up."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    up_wr, up_cl = COCK_WR + V(0.02, 0.12, 0.08), COCK_CLUB + V(0.05, 0.25, -0.05)
    for f in range(frames + 1):
        if f <= 1:                                           # wind-up: further back, rising
            k = ease(f / 1)
            wr, cl = lerp(COCK_WR, up_wr, k), lerp(COCK_CLUB.normalized(), up_cl.normalized(), k)
            lean, crouch, twist, head = lerp(0.22, 0.05, k), lerp(0.075, 0.04, k), lerp(0.25, 0.35, k), lerp(0.05, 0.15, k)
            wl = lerp(V(0.44, -0.52, 1.24), V(0.5, -0.45, 1.36), k)
        elif f <= SMASH:                                     # the smash: over the top and down
            k = (f - 1) / (SMASH - 1)
            k = k * k
            mid_wr, mid_cl = V(-0.36, -0.42, 1.62), V(0.12, -0.72, 0.45)
            if k < 0.5:
                kk = ease(k / 0.5)
                wr, cl = lerp(up_wr, mid_wr, kk), lerp(up_cl.normalized(), mid_cl.normalized(), kk)
            else:
                kk = ease((k - 0.5) / 0.5)
                wr, cl = lerp(mid_wr, HIT_WR, kk), lerp(mid_cl.normalized(), HIT_CLUB.normalized(), kk)
            lean, crouch, twist, head = lerp(0.05, 0.7, k), lerp(0.04, 0.17, k), lerp(0.35, -0.12, k), lerp(0.15, -0.05, k)
            wl = lerp(V(0.5, -0.45, 1.36), V(0.55, 0.12, 1.02), k)
        elif f <= 9:                                         # impact: shudder and a small bounce of the club
            k = (f - SMASH) / (9 - SMASH)
            bounce = math.sin(k * math.pi) * 0.06
            wr, cl = HIT_WR + V(0, 0.02, bounce), (HIT_CLUB.normalized() + V(0, 0, bounce * 2.5)).normalized()
            lean, crouch, twist, head = 0.7 - 0.05 * k, 0.17 + 0.01 * math.sin(k * math.pi), -0.12, -0.05 + 0.08 * k
            wl = V(0.55, 0.12, 1.02)
        else:                                                # haul it back up into the cocked pose
            k = ease((f - 9) / (frames - 9))
            mid_wr, mid_cl = V(-0.48, -0.25, 1.35), V(-0.25, -0.1, 0.96)
            if k < 0.45:
                kk = ease(k / 0.45)
                wr, cl = lerp(HIT_WR, mid_wr, kk), lerp(HIT_CLUB.normalized(), mid_cl.normalized(), kk)
            else:
                kk = ease((k - 0.45) / 0.55)
                wr, cl = lerp(mid_wr, COCK_WR, kk), lerp(mid_cl.normalized(), COCK_CLUB.normalized(), kk)
            lean, crouch, twist, head = lerp(0.65, 0.22, k), lerp(0.17, 0.075, k), lerp(-0.12, 0.25, k), lerp(0.03, 0.05, k)
            wl = lerp(V(0.55, 0.12, 1.02), V(0.44, -0.52, 1.24), k)
        aims = legs(arm, wide=1.25, fwd_L=0.06)
        ro = V(0.0, -0.03 - 0.08 * max(0.0, lean - 0.22), -crouch)
        rr = Quaternion((0, 0, 1), math.radians(-14 + 30 * max(0.0, 0.25 - twist)))
        torso(aims, lean=lean, twist=twist, head_up=head, look=-0.22 * (1 - min(1.0, lean)))
        aims["clavicle.R"] = V(-1.0, -0.1 * lean, 0.4 * max(0.0, wr.z - 1.2))
        aims["clavicle.L"] = V(1.0, -0.2, 0.08)
        pole = V(-1.0, 0.4, 0.2) if wr.z > 1.3 else V(-1.0, 0.3, -0.4)
        aims.update(grip(arm, wr, cl, pole=pole))
        aims.update(fist_L(arm, wl, pole=V(1.0, 0.2, -0.6), fdir=(wl - V(0.5, 0.1, 1.45)).normalized()))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
