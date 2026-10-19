"""Sun Priest clips (30 fps).

Idle   : the sun staff planted at his right side, his left hand open at his waist; he breathes, looks about and now and
         then lifts his face to the sun.
Combat : the staff lifted before him, the disc toward the robots, his left hand raised palm out: a priest commanding.
Attack : (42 frames = the 1.4 s cooldown) he sweeps the staff up overhead (the disc blazing) and drives it forward at
         the robots, flinging his left hand open after it; at RELEASE (frame 10) beams of sunlight leave the disc for
         every robot the pulse hit (game.gd draws them); he holds the pose a moment and settles back.

The staff is rigid in his right fist ("frame" aims: the staff along the fist's thumb axis, the disc facing along the
knuckles)."""
import math
from mathutils import Vector, Quaternion
import sunpriest as cm
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
RELEASE = 10        # the beams leave the disc (game.gd ATTACK_FRAME)
FR = 42


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def staff_grip(arm, grip, staff_dir, finger, pole):
    """Right fist (its grip centre) at `grip`, the staff along `staff_dir` (toward the disc), the disc facing `finger`."""
    sd = Vector(staff_dir).normalized()
    R = frame_map(T_REST, sd, F_REST, Vector(finger))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF, pole=pole)
    aims["hand.R"] = ("frame", T_REST, sd, F_REST, Vector(finger))
    return aims


def planted(arm, butt, staff_dir, finger, pole):
    sd = Vector(staff_dir).normalized()
    return staff_grip(arm, Vector(butt) + sd * cm.STAFF_BACK, sd, finger, pole)


def feet(arm, yaw, lf=(0.17, -0.02), rf=(-0.17, 0.08), ro=V(0, 0, 0)):
    q = rz(yaw)
    aims = {}
    for side, (bx, by) in (("L", lf), ("R", rf)):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + ro.x * 0.0 + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]))
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
BUTT_IDLE = V(-0.38, -0.1, 0.0)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    yaw = 3.0 * math.sin(w)
    ro = V(0.0, 0.0, -0.006 + 0.004 * br)
    aims = feet(arm, 0.0)
    sun_up = max(0.0, math.sin(w - 0.6)) ** 3                       # once a loop he lifts his face to the sun
    look = 30.0 * math.sin(w) * (1.0 - sun_up) + 8.0 * math.sin(w * 3)
    torso(aims, yaw, bend=-0.02 - 0.04 * sun_up, look=look, pitch=0.04 + 0.5 * sun_up + 0.02 * br)
    sd = V(-0.03, -0.02, 1.0)
    aims.update(planted(arm, BUTT_IDLE, sd, V(0.1, -1.0, 0.0), pole=V(-1.0, 0.4, -0.5)))
    wr = body_pt(V(0.35, 0.0, 0.93), ro, yaw) + V(0.0, 0.01 * math.sin(w), 0.004 * br)     # hanging easy at his side
    aims.update(open_hand(arm, wr, V(-1.0, 0.1, 0.0), V(0.08, -0.12, -1.0), pole=V(0.3, 1.0, -0.1)))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- combat
C_YAW = -6.0


def combat_core(arm, br=0.0, sw=0.0):
    ro = V(0.0, -0.02, -0.03 + 0.006 * br)
    aims = feet(arm, C_YAW, lf=(0.19, -0.14), rf=(-0.17, 0.14))
    torso(aims, C_YAW, bend=0.06, chest=-4.0 + 2.0 * sw, look=C_YAW + 4.0, pitch=0.02 + 0.02 * br)
    return aims, ro


def combat_staff(t=0.0, br=0.0):
    """The staff held up before him, the disc toward the robots."""
    grip = V(-0.3, -0.24, 1.2 + 0.01 * br)
    sd = V(0.2, -0.38, 1.0)                      # (its foot goes down past his right hip, clear of the robe)
    return grip, sd, V(0.0, -1.0, -0.15)


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    aims, ro = combat_core(arm, br, sw)
    g, sd, fd = combat_staff(t, br)
    aims.update(staff_grip(arm, g, sd, fd, pole=V(-1.0, 0.3, -0.4)))
    wr = V(0.3, -0.42, 1.32 + 0.012 * br)
    aims.update(open_hand(arm, wr, V(0.05, -1.0, 0.1), V(0.0, -0.2, 1.0), pole=V(1.0, 0.2, -0.5)))
    return aims, ro, rz(C_YAW)


# ---------------------------------------------------------------------------------------------- attack
def _smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def make_attack(arm, frames=FR):
    """Sweep the staff up overhead, winding his chest back (0-7); drive it forward and down at the robots, the chest
    unwinding and the left foot stepping in (7-10: the beams leave at RELEASE), the left hand flung open after it; hold
    (10-18); settle back into the commanding pose (18-42)."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    g0, sd0, fd0 = combat_staff()
    L0 = (V(0.3, -0.42, 1.32), V(0.05, -1.0, 0.1), V(0.0, -0.2, 1.0))
    keys = [
        # frame, grip, staff dir, disc facing, (left wrist, palm, fingers), bend, chest, root offset
        (0, g0, sd0, fd0, L0, 0.06, -4.0, V(0.0, -0.02, -0.03)),
        # (the staff is two metres long, held a metre from its foot: overhead its foot hangs out past his right side, in
        # the thrust it trails back past his right hip, never through him)
        (7, V(-0.36, 0.0, 1.78), V(0.28, 0.12, 1.0), V(0.0, -1.0, 0.1), (V(0.16, -0.2, 1.12), V(-0.3, -0.2, 0.9), V(0.2, -0.9, 0.3)),
         -0.06, -12.0, V(0.0, 0.03, 0.0)),
        (RELEASE, V(-0.33, -0.48, 1.45), V(0.24, -0.75, 0.6), V(0.0, -0.62, -0.78), (V(0.36, -0.55, 1.22), V(0.0, -1.0, 0.25), V(0.05, -0.3, 1.0)),
         0.22, 6.0, V(0.0, -0.08, -0.06)),
        (18, V(-0.33, -0.5, 1.43), V(0.24, -0.78, 0.56), V(0.0, -0.58, -0.81), (V(0.37, -0.56, 1.21), V(0.0, -1.0, 0.25), V(0.05, -0.3, 1.0)),
         0.24, 7.0, V(0.0, -0.09, -0.07)),
        (frames, g0, sd0, fd0, L0, 0.06, -4.0, V(0.0, -0.02, -0.03)),
    ]
    for f in range(frames + 1):
        i = max(j for j in range(len(keys) - 1) if keys[j][0] <= f) if f < frames else len(keys) - 2
        a, b = keys[i], keys[i + 1]
        k = (f - a[0]) / float(b[0] - a[0])
        k = k * k if i == 1 else ease(k)                    # the strike accelerates into RELEASE
        grip = a[1].lerp(b[1], k) + (V(0, 0, 0.08 * math.sin(math.pi * k)) if i == 0 else V(0, 0, 0))
        sd = a[2].normalized().lerp(b[2].normalized(), k).normalized()
        fdir = a[3].lerp(b[3], k)
        wl, palm, fing = (a[4][j].lerp(b[4][j], k) for j in range(3))
        bend = lerp(a[5], b[5], k)
        chest = lerp(a[6], b[6], k)
        ro = a[7].lerp(b[7], k)
        step = _smooth01((f - 6) / 4.0) * (1.0 - _smooth01((f - 22) / 12.0))
        aims = feet(arm, C_YAW, lf=(0.19, -0.14 - 0.07 * step), rf=(-0.17, 0.14))
        torso(aims, C_YAW, bend=bend, chest=chest, look=C_YAW + 4.0,
              pitch=0.02 + (0.16 * math.sin(math.pi * min(1.0, f / 7.0)) if f <= 7 else 0.0))
        aims.update(staff_grip(arm, grip, sd, fdir, pole=V(-1.0, 0.3, -0.4)))
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
