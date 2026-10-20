"""Druid clips (keyed as frames; the .glb runs them at 24 fps, game.gd CLIP_FPS).

Idle   : leaning on his staff planted at his right side; he breathes, looks about, and once a loop strokes his beard down
         with his left hand.
Combat : the staff planted before him at his right, the stone toward the robots; his left hand held out low over the
         ground, palm down, fingers spread: calling to the roots.
Attack : (42 frames = 1.75 s at 24 fps; the game plays it at length / cooldown, so 1.25x for the 1.4 s cooldown) he
         heaves the staff up (0-7) and drives its foot down into the earth before him (HIT, frame 10): the stone flares
         and roots burst up under the robots the pulse hit (game.gd); his left hand sweeps up, palm up, lifting them
         (10-18); he holds a moment and settles back (18-42).

The staff is rigid in his right fist ("frame" aims: the staff along the fist's thumb axis, the stone toward the
knuckles' side)."""
import math
from mathutils import Vector, Quaternion
import druid as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
T_REST = vec(cm.staff_axis()[1])
_wr, _f, _n, _t = cm.hand_frame("R")
F_REST = vec(_f)
FIST_OFF = vec(cm.fist_center("R") - _wr)
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
HIT = 10            # the staff's foot strikes the earth: the roots burst up (game.gd ATTACK_FRAME)
FR = 42


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def staff_grip(arm, grip, staff_dir, finger, pole):
    """Right fist (its grip centre) at `grip`, the staff along `staff_dir` (toward the stone), the knuckles facing
    `finger`."""
    sd = Vector(staff_dir).normalized()
    R = frame_map(T_REST, sd, F_REST, Vector(finger))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF, pole=pole)
    aims["hand.R"] = ("frame", T_REST, sd, F_REST, Vector(finger))
    return aims


def planted(arm, butt, staff_dir, finger, pole):
    sd = Vector(staff_dir).normalized()
    return staff_grip(arm, Vector(butt) + sd * cm.STAFF_BACK, sd, finger, pole)


def feet(arm, yaw, lf=(0.17, -0.02), rf=(-0.17, 0.08)):
    q = rz(yaw)
    aims = {}
    for side, (bx, by) in (("L", lf), ("R", rf)):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]))
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * 0.6 + (-8 if side == "R" else 8)) @ rest_foot
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0):
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(0.0, -0.1 - 0.2 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(0.0, -0.04 + 0.8 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.03, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.03, 0.02)


def open_hand(arm, wrist, palm, fingers, pole):
    """Left hand: wrist at `wrist`, palm facing `palm`, fingers pointing along `fingers`."""
    aims = arm_aims(arm, "L", wrist, pole=pole)
    aims["hand.L"] = ("frame", vec(_fL), Vector(fingers), vec(_nL), Vector(palm))
    return aims


# ---------------------------------------------------------------------------------------------- idle
BUTT_IDLE = V(-0.4, -0.08, 0.0)
BEARD_MID = V(0.0, -0.27, 1.36)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    yaw = 3.0 * math.sin(w)
    ro = V(-0.02, 0.0, -0.012 + 0.004 * br)
    aims = feet(arm, 0.0)
    # once a loop (t 0.55-0.85) he strokes his beard down, looking off into the distance
    k = max(0.0, min(1.0, (t - 0.55) / 0.3))
    stroke = math.sin(math.pi * k) if 0.0 < k < 1.0 else 0.0
    slide = k                                                          # his hand slides down the beard as he strokes it
    look = 28.0 * math.sin(w) * (1.0 - stroke) + 8.0 * math.sin(w * 3)
    torso(aims, yaw, bend=0.08 + 0.03 * stroke, side=-0.03, look=look, pitch=0.02 + 0.02 * br + 0.1 * stroke)
    sd = V(-0.03, 0.06, 1.0)
    aims.update(planted(arm, BUTT_IDLE, sd, V(-0.2, -1.0, 0.0), pole=V(-1.0, 0.4, -0.5)))
    rest = body_pt(V(0.33, -0.02, 0.92), ro, yaw) + V(0.0, 0.01 * math.sin(w), 0.004 * br)
    beard = BEARD_MID + V(0.06, 0.02, 0.06 - 0.16 * slide)
    wr = rest.lerp(beard, stroke)
    palm = V(-1.0, 0.1, 0.0).lerp(V(-0.3, 1.0, 0.1), stroke)
    fing = V(0.08, -0.12, -1.0).lerp(V(-0.9, -0.2, -0.5), stroke)
    aims.update(open_hand(arm, wr, palm, fing, pole=V(0.4, 1.0, -0.3)))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- combat
C_YAW = -8.0
C_LF, C_RF = (0.18, -0.1), (-0.17, 0.1)
BUTT_C = V(-0.34, -0.42, 0.0)
SD_C = V(-0.04, 0.16, 1.0)
FIN_C = V(-0.3, -1.0, 0.05)
# left hand held out low over the ground, palm down, fingers spread toward the robots
L_C = (V(0.38, -0.38, 1.0), V(0.1, -0.15, -1.0), V(0.35, -1.0, -0.2))


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    ro = V(0.0, -0.02, -0.03 + 0.006 * br)
    aims = feet(arm, C_YAW, lf=C_LF, rf=C_RF)
    torso(aims, C_YAW, bend=0.1, chest=-3.0 + 2.0 * sw, look=C_YAW + 4.0, pitch=-0.06 + 0.02 * br)
    aims.update(planted(arm, BUTT_C, SD_C, FIN_C, pole=V(-1.0, 0.3, -0.4)))
    wl, palm, fing = L_C
    aims.update(open_hand(arm, wl + V(0.0, 0.0, 0.012 * br), palm, fing + V(0.0, 0.0, 0.08 * sw), pole=V(1.0, 0.2, -0.5)))
    return aims, ro, rz(C_YAW)


# ---------------------------------------------------------------------------------------------- attack
def _smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def make_attack(arm, frames=FR):
    """Heave the staff up, leaning back, the left hand dropping to his hip palm up (0-7); drive its foot down into the
    earth before him, leaning in (7-10: HIT); the left hand sweeps up and out palm up (10-16), held (16-20); settle back
    into the calling pose (20-42)."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    keys = [
        # frame, butt, staff dir, knuckles, (left wrist, palm, fingers), bend, chest, root offset
        (0, BUTT_C, SD_C, FIN_C, L_C, 0.1, -3.0, V(0.0, -0.02, -0.03)),
        (7, V(-0.38, -0.3, 0.3), V(-0.06, 0.28, 1.0), V(-0.3, -1.0, 0.1), (V(0.3, -0.14, 0.9), V(0.0, -0.3, 1.0), V(0.3, -1.0, 0.1)),
         -0.06, -10.0, V(0.0, 0.03, 0.0)),
        (HIT, V(-0.3, -0.56, -0.02), V(-0.02, 0.32, 1.0), V(-0.3, -1.0, -0.05), (V(0.33, -0.3, 0.98), V(0.0, -0.3, 1.0), V(0.3, -1.0, 0.2)),
         0.3, 6.0, V(0.0, -0.06, -0.08)),
        (16, V(-0.3, -0.56, -0.02), V(-0.02, 0.3, 1.0), V(-0.3, -1.0, -0.05), (V(0.44, -0.44, 1.38), V(0.05, -0.5, 0.85), V(0.25, -0.7, 0.9)),
         0.18, 4.0, V(0.0, -0.05, -0.05)),
        (20, V(-0.3, -0.56, -0.02), V(-0.02, 0.3, 1.0), V(-0.3, -1.0, -0.05), (V(0.45, -0.45, 1.4), V(0.05, -0.5, 0.85), V(0.25, -0.7, 0.9)),
         0.17, 4.0, V(0.0, -0.05, -0.05)),
        (frames, BUTT_C, SD_C, FIN_C, L_C, 0.1, -3.0, V(0.0, -0.02, -0.03)),
    ]
    for f in range(frames + 1):
        i = max(j for j in range(len(keys) - 1) if keys[j][0] <= f) if f < frames else len(keys) - 2
        a, b = keys[i], keys[i + 1]
        k = (f - a[0]) / float(b[0] - a[0])
        k = k * k if i == 1 else ease(k)                    # the thrust accelerates into the earth
        butt = a[1].lerp(b[1], k)
        sd = a[2].normalized().lerp(b[2].normalized(), k).normalized()
        fdir = a[3].lerp(b[3], k)
        wl, palm, fing = (a[4][j].lerp(b[4][j], k) for j in range(3))
        bend = lerp(a[5], b[5], k)
        chest = lerp(a[6], b[6], k)
        ro = a[7].lerp(b[7], k)
        step = _smooth01((f - 6) / 4.0) * (1.0 - _smooth01((f - 24) / 12.0))
        aims = feet(arm, C_YAW, lf=(C_LF[0], C_LF[1] - 0.08 * step), rf=C_RF)
        torso(aims, C_YAW, bend=bend, chest=chest, look=C_YAW + 4.0,
              pitch=-0.06 + (0.12 * math.sin(math.pi * min(1.0, f / 7.0)) if f <= 7 else -0.1 * _smooth01((f - 7) / 3.0)
                             * (1.0 - _smooth01((f - 20) / 10.0))))
        aims.update(planted(arm, butt, sd, fdir, pole=V(-1.0, 0.3, -0.4)))
        aims.update(open_hand(arm, wl, palm, fing, pole=V(1.0, 0.2, -0.5)))
        ch, _ = P.solve(aims, ro, rz(C_YAW))
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
