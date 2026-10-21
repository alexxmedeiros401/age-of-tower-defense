"""The Alchemist's clips (game: 24 fps).

Idle   : at her furnace, she holds the flask up to the light and swirls it, studies it over her spectacles, lowers it and
         looks about, raises it again; her left hand on her hip; the brew in the crucible heaves gently.
Combat : ready to pour: the flask held up over the crucible's near rim, her left hand on her hip, a slow swirl.
Attack : (33 frames, inside the 1.4 s cooldown) she swirls the flask, reaches over the crucible and tips it: a stream of
         green brew runs into the crucible (frames 6-10) and the brew erupts (ERUPT, frame 10: game.gd's acid cloud rolls
         out from the crucible and splashes the robots); she starts back, her left forearm up before her face, peeks
         out from behind it, and settles back to ready.

The flask is rigid in her right fist ("frame" aims: its neck along the fist's thumb axis). The furnace stands still
(its own bone); the brew's bone swells at the eruption; the stream's bone hangs from the flask's mouth, aimed down and
stretched to the brew's surface, hidden (scale 0) when she is not pouring."""
import math
from mathutils import Vector, Quaternion
import alchemist as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

_wrR, _fR, _nR, _tR = cm.hand_frame("R")
T_REST, F_REST = vec(_tR), vec(_fR)
FIST_OFF_R = vec(cm.fist_center("R") - _wrR)
NECK = cm.FLASK_NECK
BREW = vec(cm.FURN) + V(0.0, 0.0, cm.BREW_Z)

ERUPT = 10           # game.gd ATTACK_FRAME: the brew erupts
FR = 33


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def smooth_keys(keys, f, fn=ease):
    if f <= keys[0][0]:
        return keys[0][1]
    for (fa, a), (fb, b) in zip(keys, keys[1:]):
        if f <= fb:
            k = fn((f - fa) / float(fb - fa)) if fb > fa else 1.0
            return a.lerp(b, k) if isinstance(a, Vector) else a + (b - a) * k
    return keys[-1][1]


def flask_grip(arm, grip, axis, finger, pole):
    """Right fist centre at `grip`, the flask's neck along `axis` (from the bulb to the mouth), the knuckles toward
    `finger`."""
    ax = Vector(axis).normalized()
    R = frame_map(T_REST, ax, F_REST, Vector(finger))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF_R, pole=pole)
    aims["hand.R"] = ("frame", T_REST, ax, F_REST, Vector(finger))
    return aims


def mouth(grip, axis):
    return Vector(grip) + Vector(axis).normalized() * NECK


def legs(arm, lf=(0.15, 0.0), rf=(-0.17, 0.12), yaw=0.0):
    q = rz(yaw)
    aims = {}
    for side, (x, y) in (("L", lf), ("R", rf)):
        a = V(x, y, float(J["ankle_" + side][2]))
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * 0.5 + (-10 if side == "R" else 8)) @ rest_foot
    return aims


def torso(aims, yaw=0.0, lean=0.0, side=0.0, chest_tw=0.0, look=0.0, nod=0.0, tilt=0.0):
    """lean: + forward; look: head turned (radians, + to her left); nod: + chin up."""
    q = rz(yaw)
    aims["spine"] = (q @ V(side * 0.12, -0.22 * lean, 1.0), chest_tw * 0.4)
    aims["chest"] = (q @ V(side * 0.16, -0.34 * lean, 1.0), chest_tw * 0.6)
    aims["neck"] = (q @ V(0.0, -0.16 - 0.2 * lean + 0.3 * nod, 1.0), look * 0.35)
    aims["head"] = (q @ V(tilt, -0.06 + 0.5 * nod, 1.0), look * 0.65)
    aims["clavicle.L"] = q @ V(1.0, 0.0, 0.0)
    aims["clavicle.R"] = q @ V(-1.0, 0.0, 0.03)


def left_hip(arm, ro, br=0.0):
    hip = ROOT + ro + V(0.25, -0.02, 0.17 + 0.004 * br)
    return arm_aims(arm, "L", hip, pole=V(1.0, 0.5, 0.1), hand_dir=V(-0.35, 0.25, -1.0))


def stream(aims, sc, grip, axis, on):
    """The stream from the flask's mouth down to the brew; `on` 0..1 (its thickness)."""
    m = mouth(grip, axis)
    L = max(0.02, m.z - (BREW.z + 0.005))
    aims["stream"] = V(0.0, 0.0, -1.0)
    s = max(0.0, min(1.0, on))
    sc["stream"] = (s, L / cm.STREAM_L if s > 0 else 0.0, s)


def brew(sc, swell):
    sc["brew"] = (1.0 + 0.25 * swell, 1.0 + 0.8 * swell, 1.0 + 0.25 * swell)


# ----------------------------------------------------------------------------------------------- the poses
G_READY = V(-0.14, -0.27, 1.1)
T_READY = V(0.12, -0.16, 1.0)
F_READY = V(0.6, -0.8, -0.1)
POLE_R = V(-1.0, 0.3, -0.5)
G_POUR = V(-0.02, -0.45, 1.06)
T_POUR = V(0.05, -0.55, -0.83)
F_POUR = V(0.3, -0.2, 0.93)


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br = math.sin(w * 2)
        aims = legs(arm)
        ro = V(0.01 * math.sin(w), 0.0, -0.004 + 0.004 * br)
        # up to the light (0-0.4), down and a look round (0.45-0.85), up again
        up = 0.5 + 0.5 * math.cos(w)                                   # 1 at the start and end of the loop
        g_up = V(-0.12, -0.25, 1.52)
        g = G_READY.lerp(g_up, up) + V(0.012 * math.cos(w * 6), 0.012 * math.sin(w * 6), 0.0) * up
        ax = T_READY.lerp(V(0.08, -0.05, 1.0), up)
        look = (0.55 * math.sin(w * 2 + 1.0)) * (1.0 - up) - 0.18 * up
        torso(aims, lean=0.02, side=0.02 * math.sin(w), chest_tw=0.04 * math.sin(w), look=look, nod=0.12 * up - 0.05,
              tilt=0.08 * up)
        aims.update(flask_grip(arm, g, ax, F_READY, POLE_R))
        aims.update(left_hip(arm, ro, br))
        sc = {}
        stream(aims, sc, g, ax, 0.0)
        brew(sc, 0.04 * math.sin(w * 4))
        ch, _ = P.solve(aims, ro, Quaternion(), scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br = math.sin(w * 2)
        aims = legs(arm)
        ro = V(0.0, 0.0, -0.006 + 0.005 * br)
        torso(aims, lean=0.08, look=-0.05, nod=-0.12)
        g = G_READY + V(0.01 * math.cos(w * 2), 0.01 * math.sin(w * 2), 0.006 * br)
        aims.update(flask_grip(arm, g, T_READY, F_READY, POLE_R))
        aims.update(left_hip(arm, ro, br))
        sc = {}
        stream(aims, sc, g, T_READY, 0.0)
        brew(sc, 0.04 * math.sin(w * 2))
        ch, _ = P.solve(aims, ro, Quaternion(), scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# the attack: keyed values (frame, value)
K_G = [(0, G_READY), (3, G_READY + V(-0.02, 0.02, 0.07)), (6, G_POUR + V(0, 0.03, 0.05)), (ERUPT, G_POUR),
       (13, V(-0.2, -0.12, 1.28)), (18, V(-0.24, -0.08, 1.3)), (24, V(-0.2, -0.16, 1.22)), (FR, G_READY)]
K_T = [(0, T_READY), (3, V(0.2, -0.1, 1.0)), (6, V(0.1, -0.85, 0.2)), (8, T_POUR), (ERUPT, T_POUR), (13, V(0.1, 0.05, 1.0)),
       (FR, T_READY)]
K_F = [(0, F_READY), (6, V(0.5, -0.6, 0.6)), (8, F_POUR), (ERUPT, F_POUR), (13, F_READY), (FR, F_READY)]
K_RO = [(0, V(0, 0, -0.006)), (3, V(0, 0.01, 0.0)), (ERUPT, V(0.0, -0.04, -0.03)), (13, V(0.02, 0.07, -0.01)),
        (18, V(0.02, 0.06, -0.01)), (FR, V(0, 0, -0.006))]
K_LEAN = [(0, 0.08), (3, 0.04), (ERUPT, 0.32), (13, -0.14), (18, -0.08), (24, 0.0), (FR, 0.08)]
K_LOOK = [(0, -0.05), (ERUPT, 0.0), (13, 0.55), (17, 0.4), (20, 0.1), (FR, -0.05)]
K_NOD = [(0, -0.12), (ERUPT, -0.35), (13, 0.25), (18, 0.0), (FR, -0.12)]
K_SHIELD = [(0, 0.0), (ERUPT, 0.0), (12, 1.0), (19, 1.0), (24, 0.0), (FR, 0.0)]


def attack_pose(arm, f):
    g = smooth_keys(K_G, f)
    ax = smooth_keys(K_T, f).normalized()
    fing = smooth_keys(K_F, f)
    ro = smooth_keys(K_RO, f)
    aims = legs(arm)
    torso(aims, lean=smooth_keys(K_LEAN, f), look=smooth_keys(K_LOOK, f), nod=smooth_keys(K_NOD, f),
          chest_tw=0.12 * math.sin(math.pi * min(1.0, f / float(ERUPT))))
    if f <= 3:                                                            # a swirl first
        g = g + V(0.02 * math.cos(f * 2.1), 0.02 * math.sin(f * 2.1), 0.0)
    aims.update(flask_grip(arm, g, ax, fing, POLE_R))
    # the left arm: on her hip; up before her face as the brew erupts
    sh = smooth_keys(K_SHIELD, f)
    if sh <= 0.0:
        aims.update(left_hip(arm, ro))
    else:
        hip = ROOT + ro + V(0.25, -0.02, 0.17)
        guard = V(0.02, -0.3, 1.58) + V(0.0, 0.0, 0.01 * math.sin(f))
        aims.update(arm_aims(arm, "L", hip.lerp(guard, sh), pole=V(1.0, -0.2, -0.4).lerp(V(1.0, 0.2, -0.6), sh),
                             hand_dir=V(-0.35, 0.25, -1.0).lerp(V(-0.9, -0.15, 0.5), sh)))
    sc = {}
    on = smooth_keys([(0, 0.0), (6, 0.0), (7, 0.6), (8, 1.0), (ERUPT, 1.0), (11, 0.0), (FR, 0.0)], f, fn=lambda x: x)
    stream(aims, sc, g, ax, on)
    sw = 0.0
    if f >= ERUPT:
        k = f - ERUPT
        sw = math.exp(-k / 2.5) * (1.0 if k <= 1 else math.cos((k - 1) * 0.9))
    brew(sc, sw)
    return aims, ro, Quaternion(), sc


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, rr, sc = attack_pose(arm, f)
        ch, _ = P.solve(aims, ro, rr, scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
