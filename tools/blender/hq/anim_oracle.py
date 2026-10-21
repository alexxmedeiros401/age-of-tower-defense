"""Oracle clips (keyed as frames; the .glb runs them at 24 fps, game.gd CLIP_FPS).

Idle   : she stands by the tripod in her trance, the laurel held upright before her breast; her left hand wafts the
         vapours rising from the cauldron to her face in slow circles; she breathes them in, sways, lifts her face and
         lets it sink again.
Combat : turned to the robots, the laurel raised before her toward them, her left hand open over the cauldron, palm up;
         her face lifted, a slow sway.
Attack : (42 frames) she draws the laurel back to her shoulder and bows over the cauldron, wafting the vapour to her
         face (0-8); straightens and throws her head back, the vision taking her (8-13); sweeps the laurel out at the
         robots, her left hand flung open toward them (SEE, frame 14: game.gd's vision rolls out from the cauldron);
         holds (14-22) and sinks back into the combat pose (22-42).

The laurel is rigid in her right fist ("frame" aims: the sprig along the fist's thumb axis, the knuckles toward
`finger`)."""
import math
from mathutils import Vector, Quaternion
import oracle as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
T_REST = vec(cm.laurel_axis()[1])
_wr, _f, _n, _t = cm.hand_frame("R")
F_REST = vec(_f)
FIST_OFF = vec(cm.fist_center("R") - _wr)
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
SEE = 14            # the laurel sweeps out at the robots: the vision rolls out (game.gd ATTACK_FRAME)
FR = 42
BOWL = vec(cm.TRIPOD) + V(0.0, 0.0, cm.BOWL_Z)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def laurel_grip(arm, grip, sprig, finger, pole):
    """Right fist (its centre) at `grip`, the sprig along `sprig`, the knuckles facing `finger`."""
    sd = Vector(sprig).normalized()
    R = frame_map(T_REST, sd, F_REST, Vector(finger))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF, pole=pole)
    aims["hand.R"] = ("frame", T_REST, sd, F_REST, Vector(finger))
    return aims


def open_hand(arm, wrist, palm, fingers, pole):
    """Left hand: wrist at `wrist`, palm facing `palm`, fingers pointing along `fingers`."""
    aims = arm_aims(arm, "L", wrist, pole=pole)
    aims["hand.L"] = ("frame", vec(_fL), Vector(fingers), vec(_nL), Vector(palm))
    return aims


def feet(arm, yaw, lf=(0.15, -0.02), rf=(-0.15, 0.06)):
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


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0):
    """Bend forward by `bend`, to her left by `side` (radians); the chest turned `chest` degrees more; the head to the
    world heading `look`, pitched up by `pitch`, rolled by `roll` (radians, the trance's tilt)."""
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(0.0, -0.1 - 0.2 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.04 + 0.8 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.03, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.03, 0.02)


# ---------------------------------------------------------------------------------------------- idle
I_YAW = 18.0


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = I_YAW + 3.0 * sway
    ro = V(0.01 * sway, 0.0, -0.01 + 0.004 * br)
    aims = feet(arm, I_YAW)
    # she bows over the cauldron to breathe the vapour in, then lifts her face (twice a loop)
    inhale = 0.5 + 0.5 * math.sin(w * 2 - 1.2)
    torso(aims, yaw, bend=0.06 + 0.12 * inhale, side=0.04 * sway, chest=6.0, look=yaw + 18.0 * (1.0 - inhale) + 22.0 * inhale,
          pitch=0.12 - 0.4 * inhale, roll=0.08 * sway)
    q = rz(yaw)
    grip = body_pt(V(-0.1, -0.22, 1.18), ro, yaw) + V(0, 0, 0.006 * br)
    aims.update(laurel_grip(arm, grip, q @ V(0.08, -0.25, 1.0), q @ V(0.6, -0.8, 0.0), pole=q @ V(-1.0, 0.3, -0.5)))
    # the left hand wafts in slow circles over the bowl, palm toward her face
    a = w * 2
    wr = BOWL + V(-0.06 + 0.06 * math.cos(a), 0.06 + 0.05 * math.sin(a), 0.2 + 0.03 * math.sin(a))
    face = body_pt(V(0.0, -0.2, 1.62), ro, yaw)
    palm = (face - wr).normalized()
    aims.update(open_hand(arm, wr, palm, V(0.3, -0.6, 0.6), pole=V(1.0, 0.4, -0.4)))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- combat
C_YAW = 6.0
GRIP_C = V(-0.16, -0.38, 1.3)              # the laurel raised before her toward the robots
SPRIG_C = V(-0.05, -0.85, 0.6)
FIN_C = V(0.2, -0.3, -1.0)
L_C = (V(0.38, -0.36, 1.16), V(0.0, 0.0, 1.0), V(0.45, -0.85, 0.15))   # left hand open over the bowl, palm up


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    ro = V(0.0, -0.02, -0.02 + 0.006 * br)
    aims = feet(arm, C_YAW)
    torso(aims, C_YAW, bend=0.04, chest=-4.0 + 2.0 * sw, look=C_YAW + 2.0, pitch=0.08 + 0.02 * br, roll=0.05 * sw)
    aims.update(laurel_grip(arm, GRIP_C + V(0, 0, 0.01 * br), SPRIG_C, FIN_C, pole=V(-1.0, 0.2, -0.5)))
    wl, palm, fing = L_C
    aims.update(open_hand(arm, wl + V(0.0, 0.0, 0.012 * br), palm, fing, pole=V(1.0, 0.2, -0.5)))
    return aims, ro, rz(C_YAW)


# ---------------------------------------------------------------------------------------------- attack
def make_attack(arm, frames=FR):
    """Draw the laurel back and bow over the cauldron, wafting the vapour up (0-8); straighten, head thrown back (8-13);
    sweep the laurel out at the robots, the left hand flung open toward them (SEE); hold (14-22); settle (22-42)."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    keys = [
        # frame, laurel grip, sprig dir, knuckles, (left wrist, palm, fingers), bend, chest, pitch, root offset
        (0, GRIP_C, SPRIG_C, FIN_C, L_C, 0.04, -4.0, 0.08, V(0.0, -0.02, -0.02)),
        (8, V(-0.3, 0.04, 1.42), V(-0.1, 0.3, 1.0), V(0.3, -0.9, -0.2), (V(0.42, -0.4, 1.12), V(-0.5, 0.6, 0.6), V(0.3, -0.7, 0.6)),
         0.3, 10.0, -0.25, V(0.03, -0.05, -0.06)),
        (12, V(-0.26, 0.02, 1.5), V(-0.15, 0.2, 1.0), V(0.3, -0.9, -0.2), (V(0.48, -0.16, 1.42), V(-0.3, -0.4, 0.85), V(0.4, -0.4, 0.8)),
         -0.14, 4.0, 0.55, V(0.0, 0.02, 0.0)),
        (SEE, V(-0.2, -0.5, 1.36), V(-0.05, -1.0, 0.28), V(0.2, -0.2, -1.0), (V(0.36, -0.5, 1.32), V(0.0, -1.0, 0.3), V(0.3, -0.8, 0.5)),
         0.12, -8.0, 0.12, V(0.0, -0.07, -0.03)),
        (22, V(-0.2, -0.5, 1.36), V(-0.05, -1.0, 0.26), V(0.2, -0.2, -1.0), (V(0.36, -0.5, 1.3), V(0.0, -1.0, 0.3), V(0.3, -0.8, 0.5)),
         0.1, -7.0, 0.1, V(0.0, -0.06, -0.03)),
        (frames, GRIP_C, SPRIG_C, FIN_C, L_C, 0.04, -4.0, 0.08, V(0.0, -0.02, -0.02)),
    ]
    for f in range(frames + 1):
        i = max(j for j in range(len(keys) - 1) if keys[j][0] <= f) if f < frames else len(keys) - 2
        a, b = keys[i], keys[i + 1]
        k = (f - a[0]) / float(b[0] - a[0])
        k = k * k if i == 2 else ease(k)                      # the sweep accelerates out
        grip = a[1].lerp(b[1], k)
        sd = a[2].normalized().lerp(b[2].normalized(), k).normalized()
        fdir = a[3].lerp(b[3], k)
        wl, palm, fing = (a[4][j].lerp(b[4][j], k) for j in range(3))
        bend = lerp(a[5], b[5], k)
        chest = lerp(a[6], b[6], k)
        pitch = lerp(a[7], b[7], k)
        ro = a[8].lerp(b[8], k)
        aims = feet(arm, C_YAW)
        torso(aims, C_YAW, bend=bend, chest=chest, look=C_YAW + 2.0, pitch=pitch)
        aims.update(laurel_grip(arm, grip, sd, fdir, pole=V(-1.0, 0.2, -0.5)))
        aims.update(open_hand(arm, wl, palm.normalized(), fing.normalized(), pole=V(1.0, 0.2, -0.5)))
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
