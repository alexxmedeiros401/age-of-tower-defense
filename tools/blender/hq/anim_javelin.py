"""Javelin Thrower clips (keyed as 30 fps frames; the .glb runs them at 24, game.gd CLIP_FPS).

Idle    : at ease, the javelin held upright at his right side, his left hand on his hip; he shifts his weight, looks
          about, and once a loop hefts the javelin and sights along it.
Combat  : side-on to the robots, his left foot forward and his left arm pointing at them, the javelin poised back
          beside his head; he rocks on the balls of his feet.
Attack  : (24 frames, inside the 0.8 s cooldown) the throw: from the poised stance he turns and his arm whips over, the
          javelin leaves his hand at RELEASE (frame 3: game.gd launches the flying javelin from there and the one in his
          hand vanishes), he follows through down across his body, reaches back over his shoulder to the case, where a
          fresh javelin appears in his hand (FRESH), draws it out and swings it round into the poised stance.

The javelin is rigid on the `javelin` bone in his right fist ("frame" aims: it lies along the fist's thumb axis, the
fingers along the fist's forward axis); the bone's scale hides it while the thrown one flies."""
import math
from mathutils import Vector, Quaternion
import javelin as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
_a0, _ax = cm.javelin_axis()
T_REST = vec(_ax)
_wr, _f, _n, _t = cm.hand_frame("R")
F_REST = vec(_f)
FIST_OFF = vec(_a0 - _wr)
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
RELEASE = 3         # the javelin leaves his hand
FRESH = 14          # a fresh one appears in his hand at the case's mouth
FR = 24
CASE_AX = vec(cm.norm(cm.Q_TOP - cm.Q_BOT))
GRAB = vec(cm.Q_TOP) + CASE_AX * 0.1          # where he takes hold of the next javelin (body space)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def jav_grip(arm, grip, jdir, finger, pole):
    """Right fist (its grip centre) at `grip`, the javelin along `jdir`, the fist's fingers toward `finger`."""
    jd = Vector(jdir).normalized()
    R = frame_map(T_REST, jd, F_REST, Vector(finger))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF, pole=pole)
    aims["hand.R"] = ("frame", T_REST, jd, F_REST, Vector(finger))
    return aims


def open_hand(arm, wrist, palm, fingers, pole):
    aims = arm_aims(arm, "L", wrist, pole=pole)
    aims["hand.L"] = ("frame", vec(_fL), Vector(fingers), vec(_nL), Vector(palm))
    return aims


def feet(arm, yaw, lf=(0.19, -0.02), rf=(-0.19, 0.04), lift=(0.0, 0.0), turn=(8.0, -8.0)):
    """Feet planted round the root (body space offsets, turned with `yaw`); `lift` raises each heel a little."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by), up, tw in (("L", lf, lift[0], turn[0]), ("R", rf, lift[1], turn[1])):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + up)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw + tw) @ (rest_foot + V(0, 0, -up * 0.6))
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0):
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(0.0, -0.1 - 0.2 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.04 + 0.7 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.03, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.03, 0.02)


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mixd(a, b, k):
    return a.normalized().lerp(b.normalized(), k).normalized()


def bez_d(a, b, c, k):
    return mixd(mixd(a, b, k), mixd(b, c, k), k)


def bez_p(a, b, c, k):
    return a.lerp(b, k).lerp(b.lerp(c, k), k)


# ---------------------------------------------------------------------------------------------- idle
IDLE_G = V(-0.33, -0.15, 1.0)              # the grip at his right side, the javelin upright
IDLE_DIR = V(-0.06, 0.05, 1.0)
IDLE_FING = V(0.22, -1.0, -0.2)
HIP_L = V(0.31, 0.0, 1.0)                  # his left hand on his hip


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = -6.0 + 3.0 * sway
    ro = V(0.012 * sway, 0.0, -0.01 + 0.004 * br)
    aims = feet(arm, -6.0, lf=(0.2, -0.04), rf=(-0.19, 0.05), turn=(10.0, -12.0))
    # once a loop (t 0.5-0.8) he hefts the javelin to his shoulder and sights along it at the robots
    heft = smooth01((t - 0.5) / 0.08) * (1.0 - smooth01((t - 0.74) / 0.08))
    look = (26.0 * math.sin(w + 0.4) + 6.0 * math.sin(w * 3)) * (1.0 - heft)
    torso(aims, yaw, bend=0.02, side=-0.03 * sway, look=look, pitch=0.04 + 0.02 * br + 0.04 * heft)
    g0 = body_pt(IDLE_G + V(0, 0, 0.006 * br), ro, yaw)
    g1 = V(-0.3, 0.22, 1.56) + ro                                       # (the robots' frame: sighting straight ahead)
    g = g0.lerp(g1, heft) + V(0.0, 0.0, 0.06 * math.sin(math.pi * heft))
    jd = bez_d(rz(yaw) @ IDLE_DIR, V(0.0, -0.4, 1.0), V(0.02, -1.0, 0.1), heft)
    fing = mixd(rz(yaw) @ IDLE_FING, V(0.05, 0.25, 1.0), heft)
    aims.update(jav_grip(arm, g, jd, fing, pole=rz(yaw) @ V(-0.8, 0.5, -0.4).lerp(V(-0.6, 0.6, -0.7), heft)))
    wl = body_pt(HIP_L, ro, yaw)
    aims.update(open_hand(arm, wl, rz(yaw) @ V(-1.0, 0.15, 0.0), rz(yaw) @ V(0.05, -0.5, -0.86), pole=rz(yaw) @ V(1.0, 0.4, -0.2)))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- combat (poised)
C_YAW = -45.0          # side-on to the robots: his left shoulder toward them, his throwing arm back
POISE_G = V(-0.3, 0.48, 1.6)               # the grip up beside his head, drawn back (the robots' frame)
JDIR = V(0.03, -1.0, 0.15)                 # at the robots, a little up
POISE_FING = V(0.05, 0.3, 1.0)
POISE_POLE = V(-0.5, 0.6, -0.7)
AIM_L = V(0.1, -0.66, 1.42)                # his left arm out, pointing at the robots
AIM_PALM, AIM_FING = V(0.0, 0.15, -1.0), V(-0.05, -1.0, 0.06)
C_FEET = dict(lf=(0.2, -0.2), rf=(-0.18, 0.18), turn=(-6.0, -25.0))


def combat_pose(arm, t):
    w = 2 * math.pi * t
    bob = math.sin(w * 2)
    ro = V(0.0, 0.0, -0.06 + 0.012 * bob)
    aims = feet(arm, C_YAW, **C_FEET)
    torso(aims, C_YAW, bend=-0.04, chest=-14.0, look=0.0, pitch=0.04)
    aims.update(jav_grip(arm, POISE_G + ro + V(0, 0, 0.008 * bob), JDIR, POISE_FING, POISE_POLE))
    aims.update(open_hand(arm, AIM_L + ro + V(0, 0, 0.008 * bob), AIM_PALM, AIM_FING, pole=V(0.9, 0.2, -0.6)))
    return aims, ro, rz(C_YAW)


# ---------------------------------------------------------------------------------------------- attack: the throw
REL_G = V(-0.24, -0.3, 1.78)               # the release: in front of him above his head, the forearm up
REL_FING = V(0.0, -0.25, 1.0)
FOL_G = V(0.1, -0.42, 1.02)                # the follow-through, down across his body
FOL_DIR, FOL_FING = V(0.4, -0.85, -0.35), V(0.5, 0.2, -0.85)
FOL_L = V(0.36, 0.12, 1.08)                # his left hand pulled back to his hip
CASE_FING = V(0.3, 0.95, 0.0)              # reaching over his shoulder: the fingers back, round the javelin
PULL = 0.3                                 # how far he draws it up out of the case


def throw_state(f, ro):
    """(body yaw, chest twist, bend, crouch, grip, javelin dir, fingers, arm pole, left wrist, right heel lift) at frame
    f, in the robots' frame."""
    if f <= RELEASE:                                         # the whip: he turns into it and his arm comes over the top
        k = (f / float(RELEASE)) ** 1.4
        yaw = lerp(C_YAW, 5.0, k)
        g = POISE_G.lerp(REL_G, k) + V(0, 0, 0.08 * math.sin(math.pi * k)) + ro
        return (yaw, lerp(-14.0, 8.0, k), lerp(-0.04, 0.12, k), lerp(0.06, 0.07, k), g, JDIR, mixd(POISE_FING, REL_FING, k),
                POISE_POLE.lerp(V(-0.8, -0.2, -0.6), k), AIM_L.lerp(V(0.3, -0.3, 1.2), k) + ro, 0.04 * k)
    if f <= 9:                                               # follow through, down across his body (the javelin is gone)
        k = ease((f - RELEASE) / float(9 - RELEASE))
        return (lerp(5.0, 25.0, k), lerp(8.0, 14.0, k), lerp(0.12, 0.38, k), lerp(0.07, 0.13, k), (REL_G + ro).lerp(FOL_G + ro, k),
                mixd(JDIR, FOL_DIR, k), mixd(REL_FING, FOL_FING, k), V(-0.8, -0.2, -0.6).lerp(V(-0.6, -0.6, -0.4), k),
                V(0.3, -0.3, 1.2).lerp(FOL_L, k) + ro, lerp(0.04, 0.07, k))
    yaw_r = -10.0
    grab = body_pt(GRAB, ro, yaw_r)
    case_d = rz(yaw_r) @ CASE_AX
    case_f = rz(yaw_r) @ CASE_FING
    case_pole = rz(yaw_r) @ V(0.1, -0.6, 1.0)
    if f <= FRESH:                                           # straighten up, reach back over his shoulder to the case
        k = ease((f - 9) / float(FRESH - 9))
        g = bez_p(FOL_G + ro, V(-0.36, -0.2, 1.56) + ro, grab, k)
        return (lerp(25.0, yaw_r, k), lerp(14.0, 0.0, k), lerp(0.38, 0.06, k), lerp(0.13, 0.05, k), g, mixd(FOL_DIR, case_d, k),
                mixd(FOL_FING, case_f, k), V(-0.6, -0.6, -0.4).lerp(case_pole, k), FOL_L.lerp(V(0.3, -0.34, 1.3), k) + ro,
                lerp(0.07, 0.0, k))
    if f <= 18:                                              # draw it up out of the case
        k = ease((f - FRESH) / float(18 - FRESH))
        return (yaw_r, 0.0, 0.06, 0.05, grab + case_d * (PULL * k), case_d, case_f, case_pole, V(0.3, -0.34, 1.3) + ro, 0.0)
    k = ease((f - 18) / float(FR - 18))                      # swing it round over his head into the poised stance
    top = grab + case_d * PULL
    g = bez_p(top, V(-0.32, 0.3, 1.86) + ro, POISE_G + ro, k)
    return (lerp(yaw_r, C_YAW, k), lerp(0.0, -14.0, k), lerp(0.06, -0.04, k), lerp(0.05, 0.06, k), g,
            bez_d(case_d, V(0.0, -0.35, 1.0), JDIR, k), bez_d(case_f, V(0.1, 0.9, 0.4), POISE_FING, k),
            case_pole.lerp(POISE_POLE, k), V(0.3, -0.34, 1.3).lerp(AIM_L, k) + ro, 0.0)


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        crouch = throw_state(f, V(0, 0, 0))[3]
        ro = V(0.0, -0.06 * smooth01(f / 4.0) * (1 - smooth01((f - 9) / 8.0)), -crouch)
        yaw, chest, bend, _c, g, jd, fing, pole, wl, heel = throw_state(f, ro)
        aims = feet(arm, C_YAW, lift=(0.0, heel), **C_FEET)
        torso(aims, yaw, bend=bend, chest=chest, look=0.0 if f < 10 or f > 19 else lerp(0.0, -30.0, math.sin(math.pi * (f - 10) / 9.0)),
              pitch=0.04 - 0.1 * bend)
        aims.update(jav_grip(arm, g, jd, fing, pole))
        lk = smooth01((f - RELEASE) / 4.0) * (1.0 - smooth01((f - 18) / 6.0))      # his left hand: pulled in, then out again
        aims.update(open_hand(arm, wl, mixd(AIM_PALM, V(-0.9, 0.2, -0.3), lk), mixd(AIM_FING, V(0.1, -0.4, -0.9), lk),
                              pole=V(0.9, 0.2, -0.6)))
        sc = {"javelin": 0.0 if RELEASE <= f < FRESH else 1.0}
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    key_constant(act, 'pose.bones["javelin"].scale')
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


def key_constant(act, path):
    """Make every key on the curve `path` constant (the javelin pops out of / into his hand)."""
    fcs = []
    try:
        fcs = [fc for fc in act.fcurves]
    except Exception:
        pass
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                fcs += list(cb.fcurves)
    for fc in fcs:
        if fc.data_path == path:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
