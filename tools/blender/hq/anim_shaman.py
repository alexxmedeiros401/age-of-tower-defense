"""Tar Pit Shaman clips (30 fps): Idle (leaning on his staff, stroking his beard, muttering), Combat (chanting: staff up,
his tarry left hand clawing over the pit, swaying) and Attack (he lifts the staff and slams its butt down: the spirit
stone flares, his left hand thrusts out at the robots).

The staff is rigid in his right fist, so the fist is posed by the staff's direction ("frame" aims); when the staff is
planted, the grip is placed so its butt sits on the ground. The spirit stone has its own bone ("orb") whose scale pulses."""
import math
from mathutils import Vector, Quaternion
import tar_shaman as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
T_REST = Vector(cm.staff_axis()[1])
_wr, _f, _n, _t = cm.hand_frame("R")
F_REST = Vector(_f)
FIST_OFF = Vector(cm.fist_center("R") - _wr)       # wrist -> grip centre, rest pose
BELOW = 1.1 + 0.03                                 # grip centre -> the staff's butt


def grip(arm, wrist, staff_dir, pole, finger=None):
    """Right arm to `wrist`, staff along `staff_dir`; fingers along the forearm unless `finger` is given."""
    aims = arm_aims(arm, "R", wrist, pole=pole)
    sd = Vector(staff_dir).normalized()
    def hand(P, base):
        fd = Vector(finger) if finger is not None else P["forearm.R"].col[1].xyz.normalized()
        return ("frame", T_REST, sd, F_REST, fd)
    aims["hand.R"] = hand
    return aims


def planted(arm, butt, staff_dir, finger, pole):
    """Staff planted with its butt at `butt`: the wrist goes wherever puts the grip on the staff."""
    sd = Vector(staff_dir).normalized()
    R = frame_map(T_REST, sd, F_REST, Vector(finger))
    g = Vector(butt) + sd * BELOW
    return grip(arm, g - R @ FIST_OFF, sd, pole, finger=finger)


def legs(arm, wide=1.0, bend=0.0):
    aR = J["ankle_R"] + V(-0.02 * wide, 0.05 * wide, 0)
    aL = J["ankle_L"] + V(0.02 * wide, -0.05 * wide, 0)
    aims = {}
    aims.update(leg_aims(arm, "R", aR, pole=V(-0.2, -1, 0.1)))
    aims.update(leg_aims(arm, "L", aL, pole=V(0.2, -1, 0.1)))
    return aims


def torso(aims, hunch=0.0, twist=0.0, side=0.0, head_up=0.0, look=0.0, tilt=0.0):
    aims["spine"] = (V(side * 0.12, -0.05 - 0.2 * hunch, 1.0), twist * 0.4)
    aims["chest"] = (V(side * 0.18, -0.38 - 0.35 * hunch, 1.0), twist)
    aims["neck"] = V(0.0 + tilt * 0.3, -0.62 + 0.6 * head_up, 1.0)
    aims["head"] = (V(tilt, -0.18 + 0.75 * head_up, 1.0), look)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm, wide=0.9)
    ro = V(0.0, 0.0, -0.012 + 0.006 * br)
    rr = Quaternion((0, 0, 1), math.radians(3 * math.sin(w)))
    mutter = 0.05 * math.sin(w * 6) * max(0.0, math.sin(w))          # nods while he mutters
    torso(aims, hunch=0.1, twist=0.05 * math.sin(w), head_up=-0.1 + mutter, look=0.3 * math.sin(w + 0.8), tilt=0.12 * math.sin(w * 0.5 + 1))
    aims["clavicle.R"] = V(-1.0, 0.0, 0.1)
    aims["clavicle.L"] = V(1.0, -0.1, 0.0)
    # leaning on the planted staff
    aims.update(planted(arm, V(-0.42, -0.34, 0.0), V(0.12, 0.1, 1.0), V(0.55, -0.8, 0.0), pole=V(-1.0, 0.6, -0.3)))
    # stroking his beard: the hand slides down it and goes back up
    s = (t * 2) % 1.0
    k = ease(min(1.0, s / 0.7)) if s < 0.7 else 1.0 - ease((s - 0.7) / 0.3)
    wl = lerp(V(0.08, -0.31, 1.33), V(0.06, -0.33, 1.13), k)
    aims.update(arm_aims(arm, "L", wl, pole=V(1.0, 0.0, -0.6), hand_dir=V(-0.45, -0.35, -1.0)))
    return aims, ro, rr, {"orb": 1.0 + 0.04 * math.sin(w * 3)}


def combat_pose(arm, t):
    w = 2 * math.pi * t
    sway = math.sin(w)
    aims = legs(arm, wide=1.15)
    ro = V(0.012 * sway, -0.02, -0.03 + 0.008 * math.sin(w * 2))
    rr = Quaternion((0, 0, 1), math.radians(6 * sway))
    torso(aims, hunch=0.25, twist=-0.1 * sway, side=0.15 * sway, head_up=0.1 + 0.05 * math.sin(w * 2), look=0.15 * sway, tilt=-0.15 * sway)
    aims["clavicle.R"] = V(-1.0, -0.1, 0.25)
    aims["clavicle.L"] = V(1.0, -0.3, 0.1)
    aims.update(grip(arm, V(-0.33, -0.3, 1.22 + 0.02 * math.sin(w * 2)), V(0.06, -0.12, 1.0), pole=V(-1.0, 0.3, -0.5)))
    # the tarry left hand claws over the pit in little circles
    cx, cz = 0.025 * math.cos(w * 2), 0.025 * math.sin(w * 2)
    aims.update(arm_aims(arm, "L", V(0.3 + cx, -0.62, 1.02 + cz), pole=V(1.0, 0.4, -0.5), hand_dir=V(0.05 + cx * 4, -1.0, -0.45)))
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


SLAM = 4


def make_attack(arm, frames=30):
    """Lift the staff (frames 0-2), slam its butt into the ground (SLAM): the stone flares, his left hand thrusts out;
    then he eases back into the chant."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    c_wr, c_sd = V(-0.33, -0.3, 1.22), V(0.06, -0.12, 1.0)
    up_wr, up_sd = V(-0.34, -0.36, 1.48), V(0.05, -0.2, 1.0)
    butt = V(-0.36, -0.5, 0.0)
    slam_sd = V(0.02, -0.1, 1.0).normalized()
    fing = V(0.5, -0.85, 0.0)
    for f in range(frames + 1):
        aims = legs(arm, wide=1.2)
        if f <= 2:
            k = ease(f / 2)
            hand = ("free", lerp(c_wr, up_wr, k), lerp(c_sd, up_sd, k))
            hunch, head, lean_l = lerp(0.25, 0.05, k), lerp(0.1, 0.3, k), 0.0
            orb = 1.0 + 0.15 * k
        elif f <= SLAM:
            k = ease((f - 2) / (SLAM - 2))
            hand = ("blend", up_wr, up_sd, k)
            hunch, head, lean_l = lerp(0.05, 0.45, k), lerp(0.3, 0.0, k), k
            orb = 1.15 + 0.75 * k
        elif f <= 12:
            k = (f - SLAM) / (12 - SLAM)
            hand = ("planted",)
            hunch, head, lean_l = 0.45 - 0.05 * k, 0.0 + 0.35 * ease(min(1.0, k * 2)), 1.0
            orb = 1.9 - 0.6 * ease(k)
        else:
            k = ease((f - 12) / (frames - 12))
            hand = ("unplant", k)
            hunch, head, lean_l = lerp(0.4, 0.25, k), lerp(0.35, 0.1, k), 1.0 - k
            orb = lerp(1.3, 1.0, k)
        ro = V(0.0, -0.05 * hunch, -0.03 - 0.05 * max(0.0, hunch - 0.25))
        rr = Quaternion((0, 0, 1), math.radians(-4))
        torso(aims, hunch=hunch, head_up=head, look=0.0)
        aims["clavicle.R"] = V(-1.0, -0.1, 0.25)
        aims["clavicle.L"] = V(1.0, -0.3, 0.1 + 0.15 * lean_l)
        if hand[0] == "free":
            aims.update(grip(arm, hand[1], hand[2], pole=V(-1.0, 0.3, -0.5)))
        elif hand[0] == "blend":
            # from the raised pose straight down until the butt meets the ground
            k = hand[3]
            sd = lerp(up_sd.normalized(), slam_sd, k).normalized()
            R = frame_map(T_REST, sd, F_REST, fing)
            g_end = butt + slam_sd * BELOW
            wr_end = g_end - R @ FIST_OFF
            aims.update(grip(arm, lerp(up_wr, wr_end, k), sd, pole=V(-1.0, 0.3, -0.5), finger=fing))
        elif hand[0] == "planted":
            aims.update(planted(arm, butt, slam_sd, fing, pole=V(-1.0, 0.3, -0.5)))
        else:
            k = hand[1]
            R = frame_map(T_REST, slam_sd, F_REST, fing)
            wr0 = butt + slam_sd * BELOW - R @ FIST_OFF
            aims.update(grip(arm, lerp(wr0, c_wr, k), lerp(slam_sd, c_sd.normalized(), k), pole=V(-1.0, 0.3, -0.5),
                             finger=lerp(fing, V(0.3, -0.9, 0.3), k)))
        # left hand: thrust forward, palm out, at the slam
        wl = lerp(V(0.3, -0.62, 1.02), V(0.34, -0.78, 1.2), lean_l)
        aims.update(arm_aims(arm, "L", wl, pole=V(1.0, 0.4, -0.5), hand_dir=lerp(V(0.05, -1.0, -0.45), V(0.1, -0.55, 1.0), lean_l).normalized()))
        ch, _ = P.solve(aims, ro, rr, scales={"orb": orb})
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
