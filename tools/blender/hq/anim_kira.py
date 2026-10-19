"""Kira's clips (keyed as 30 fps; the .glb runs them at 24, game.gd CLIP_FPS).

Idle    : the khopesh resting on her right shoulder, her left fist on her hip; she shifts her weight and looks about.
Combat  : a duellist's stance, right foot forward and side-on, the sword raised before her with its point toward the
          robots, her left hand back and up for balance; she bobs on her toes and the point circles.
Attack  : (21 frames = the 0.7 s cooldown) the whirlwind: she coils to her right, drawing the sword back, then spins a
          full turn on the balls of her feet with the blade swept round at arm's length, the cut crossing the front at
          HIT (frame 11: game.gd draws the slashes), and settles back into her stance.
Ability : Solar Flare: she crouches with the sword held point-up before her face, the sun-stone gathering light, then
          springs up and thrusts it at the sky, her left hand flung open (FLARE, frame 18: the burst), holds, and sweeps
          it down into her stance.
Cheer   : the sword thrust overhead, a twirl of it, a fist pump and a hop.

The sword is rigid in her right fist ("frame" aims: along the fist's thumb axis, its edge along the knuckles)."""
import math
from mathutils import Vector, Quaternion
import kira as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
_ax = cm.sword_axis()
T_REST, F_REST = vec(_ax[1]), vec(_ax[2])
_wr, _f, _n, _t = cm.hand_frame("R")
FIST_OFF = vec(cm.fist_center("R") - _wr)
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
HIT = 11            # the whirl's cut crosses the front (game.gd ATTACK_FRAME)
FLARE = 18          # Solar Flare bursts from the raised sword (game.gd times the burst to it)
FR = 21


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def dirz(deg):
    """Horizontal direction at `deg` counterclockwise from her front (-Y), seen from above."""
    a = math.radians(deg)
    return V(math.sin(a), -math.cos(a), 0.0)


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def sword_grip(arm, grip, sword_dir, edge, pole):
    """Right fist (its grip centre) at `grip`, the sword along `sword_dir`, its edge toward `edge`."""
    sd = Vector(sword_dir).normalized()
    R = frame_map(T_REST, sd, F_REST, Vector(edge))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF, pole=pole)
    aims["hand.R"] = ("frame", T_REST, sd, F_REST, Vector(edge))
    return aims


def open_hand(arm, wrist, palm, fingers, pole):
    aims = arm_aims(arm, "L", wrist, pole=pole)
    aims["hand.L"] = ("frame", vec(_fL), Vector(fingers), vec(_nL), Vector(palm))
    return aims


def feet(arm, yaw, lf=(0.16, -0.02), rf=(-0.16, 0.06), lift=(0.0, 0.0), ro=V(0, 0, 0)):
    """Feet planted round the root (body space offsets, turned with `yaw`); `lift` raises each heel a little."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by), up in (("L", lf, lift[0]), ("R", rf, lift[1])):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + up)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw + (-8 if side == "R" else 8)) @ (rest_foot + V(0, 0, -up * 0.6))
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
    aims["head"] = (rz(look) @ V(0.0, -0.04 + 0.7 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.03, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.03, 0.02)


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------------------------------------- idle
def idle_pose(arm, t):
    """The khopesh on her right shoulder (its blade hooked behind it), her left fist on her hip."""
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = 4.0 * sway
    ro = V(0.012 * sway, 0.0, -0.008 + 0.004 * br)
    aims = feet(arm, 0.0, lf=(0.17, -0.03), rf=(-0.17, 0.05))
    look = 28.0 * math.sin(w + 0.4) + 6.0 * math.sin(w * 3)
    torso(aims, yaw, bend=0.0, side=-0.04 * sway, look=look, pitch=0.03 + 0.02 * br)
    g = body_pt(V(-0.22, -0.17, 1.2 + 0.006 * br), ro, yaw)
    sd = rz(yaw) @ V(-0.16, 0.55, 0.82)
    edge = rz(yaw) @ V(-0.5, -0.35, 0.6)
    aims.update(sword_grip(arm, g, sd, edge, pole=rz(yaw) @ V(-1.0, -0.2, -0.6)))
    wl = body_pt(V(0.29, 0.0, 0.98), ro, yaw)
    aims.update(open_hand(arm, wl, rz(yaw) @ V(-1.0, 0.15, 0.0), rz(yaw) @ V(0.05, -0.55, -0.83), pole=rz(yaw) @ V(1.0, 0.4, 0.0)))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- combat
C_YAW = 20.0           # turned so her sword side leads


def stance_sword(yaw, ro, t=0.0, bob=0.0):
    """Grip, sword direction and edge for the duelling stance, the point circling a little."""
    c = 2 * math.pi * t
    g = body_pt(V(-0.2, -0.36, 1.24 + 0.012 * bob), ro, yaw)
    sd = rz(yaw) @ (V(0.12, -0.72, 0.62) + V(0.05 * math.cos(c), 0.0, 0.05 * math.sin(c)))
    edge = rz(yaw) @ V(0.0, -0.62, -0.72)
    return g, sd, edge


def combat_pose(arm, t):
    w = 2 * math.pi * t
    bob = math.sin(w * 2)
    ro = V(0.0, 0.0, -0.06 + 0.012 * bob)
    aims = feet(arm, C_YAW, lf=(0.18, 0.15), rf=(-0.13, -0.17), lift=(0.012 * max(0.0, bob), 0.012 * max(0.0, -bob)))
    torso(aims, C_YAW, bend=0.12, chest=-6.0, look=C_YAW - 20.0, pitch=0.0)
    g, sd, edge = stance_sword(C_YAW, ro, t, bob)
    aims.update(sword_grip(arm, g, sd, edge, pole=rz(C_YAW) @ V(-1.0, 0.3, -0.5)))
    wl = body_pt(V(0.42, 0.2, 1.3 + 0.01 * bob), ro, C_YAW)
    aims.update(open_hand(arm, wl, rz(C_YAW) @ V(0.0, 0.2, -1.0), rz(C_YAW) @ V(0.5, 0.6, 0.5), pole=rz(C_YAW) @ V(0.6, 1.0, -0.4)))
    return aims, ro, rz(C_YAW)


# ---------------------------------------------------------------------------------------------- attack: the whirlwind
def whirl_state(f):
    """(yaw, the sword's angle from her front, its height, crouch, hop) at frame f."""
    if f <= 3:                                              # coil to her right, the sword drawn back
        k = ease(f / 3.0)
        return lerp(C_YAW, C_YAW - 45.0, k), lerp(-18.0, -140.0, k), lerp(1.3, 1.2, k), lerp(0.06, 0.12, k), 0.0
    if f <= 12:                                             # spin a full turn, the blade swept round
        k = (f - 3) / 9.0
        ks = k * k * (3 - 2 * k)
        yaw = lerp(C_YAW - 45.0, C_YAW + 360.0, ks)
        rel = lerp(-140.0, 12.0, k ** 1.4)
        return yaw, rel, lerp(1.2, 1.16, k), lerp(0.12, 0.1, k), 0.045 * math.sin(math.pi * min(1.0, k * 1.15))
    k = ease((f - 12) / float(FR - 12))                     # settle back into the stance
    return C_YAW + 360.0, lerp(12.0, -18.0, k), lerp(1.16, 1.3, k), lerp(0.1, 0.06, k), 0.0


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        yaw, rel, h, crouch, hop = whirl_state(f)
        ro = V(0.0, 0.0, -crouch + hop)
        settle = smooth01((f - 12) / float(FR - 12)) if f > 12 else 0.0
        aims = feet(arm, yaw, lf=(0.18, 0.15), rf=(-0.13, -0.17), lift=(0.02 * (hop > 0), 0.03 * (hop > 0)))
        torso(aims, yaw, bend=0.14, side=0.06 * (1 - settle) if 3 < f <= 12 else 0.0, chest=lerp(-25.0, -6.0, settle) if f > 3 else -6.0 - 19.0 * ease(f / 3.0),
              look=yaw - 20.0 + (20.0 if 3 < f <= 12 else 0.0), pitch=0.0)
        if f > 12:
            # back to the stance: blend the swept-round sword into the stance's
            g0 = body_pt(V(-0.12, 0.0, h) + dirz(rel) * 0.5, ro, yaw)
            sd0 = rz(yaw) @ (dirz(rel - 6.0) + V(0, 0, 0.05))
            e0 = rz(yaw) @ dirz(rel + 84.0)
            g1, sd1, e1 = stance_sword(yaw, ro, 0.0, 0.0)
            g = g0.lerp(g1, settle)
            sd = sd0.normalized().lerp(sd1.normalized(), settle).normalized()
            edge = e0.lerp(e1, settle)
        else:
            g = body_pt(V(-0.12, 0.0, h) + dirz(rel) * 0.5, ro, yaw)
            sd = rz(yaw) @ (dirz(rel - 6.0) + V(0, 0, 0.05))
            edge = rz(yaw) @ dirz(rel + 84.0)                  # the edge leads the sweep
        aims.update(sword_grip(arm, g, sd, edge, pole=rz(yaw) @ V(-0.6, 0.8, -0.6)))
        # her left arm flung out for balance through the spin
        spin = 1.0 if 3 < f <= 12 else (ease(f / 3.0) if f <= 3 else 1.0 - settle)
        wl = body_pt(V(0.42, 0.2, 1.3).lerp(V(0.56, 0.06, 1.26), spin), ro, yaw)
        aims.update(open_hand(arm, wl, rz(yaw) @ V(0.0, 0.2, -1.0), rz(yaw) @ V(0.6, 0.4, 0.3), pole=rz(yaw) @ V(0.6, 1.0, -0.4)))
        ch, _ = P.solve(aims, ro, rz(yaw))
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- ability: Solar Flare
def make_ability(arm, frames=54):
    P = Poser(arm)
    act = new_action(arm, "Ability")
    yaw0 = C_YAW
    for f in range(frames + 1):
        g1, sd1, e1 = stance_sword(yaw0, V(0, 0, -0.06), 0.0, 0.0)
        if f <= 10:                                         # crouch, the sword point-up before her face, both hands on it
            k = ease(f / 10.0)
            crouch, yaw = lerp(0.06, 0.2, k), lerp(yaw0, 0.0, k)
            ro = V(0, 0, -crouch)
            g = body_pt(V(-0.06, -0.24, 1.12), ro, yaw).lerp(g1, 1 - k) if k < 1 else body_pt(V(-0.06, -0.24, 1.12), ro, yaw)
            sd = (rz(yaw) @ V(0.04, -0.12, 1.0)).lerp(sd1, 1 - k).normalized()
            edge = (rz(yaw) @ V(0.0, -1.0, 0.0)).lerp(e1, 1 - k)
            wl = body_pt(V(0.06, -0.28, 1.0), ro, yaw)
            palm, fing = V(-0.9, -0.2, 0.3), V(-0.2, -0.4, 0.9)
            bend, pitch = lerp(0.12, 0.3, k), lerp(0.0, -0.1, k)
            lf, rf = (0.2, 0.12), (-0.18, -0.08)
        elif f <= FLARE:                                    # spring up, the sword thrust at the sky
            k = (f - 10) / float(FLARE - 10)
            k = k * k * (3 - 2 * k)
            crouch, yaw = lerp(0.2, -0.03, k), 0.0
            ro = V(0, 0, -crouch)
            g = body_pt(V(-0.06, -0.24, 1.12).lerp(V(-0.2, -0.08, 2.02), k), ro, yaw)
            sd = V(0.04, -0.12, 1.0).lerp(V(0.06, -0.08, 1.0), k).normalized()
            edge = V(0.0, -1.0, 0.0)
            wl = body_pt(V(0.06, -0.28, 1.0).lerp(V(0.62, -0.1, 1.42), k), ro, yaw)
            palm, fing = V(-0.9, -0.2, 0.3).lerp(V(0.2, -0.3, 0.95), k), V(-0.2, -0.4, 0.9).lerp(V(0.95, 0.0, 0.3), k)
            bend, pitch = lerp(0.3, -0.08, k), lerp(-0.1, 0.45, k)
            lf, rf = (0.2, 0.12), (-0.18, -0.08)
        elif f <= 34:                                       # hold while the burst rolls out
            k = (f - FLARE) / float(34 - FLARE)
            crouch, yaw = -0.03 + 0.01 * k, 0.0
            ro = V(0, 0, -crouch)
            tr = 0.004 * math.sin(f * 2.7)
            g = body_pt(V(-0.2 + tr, -0.08, 2.02), ro, yaw)
            sd, edge = V(0.06, -0.08, 1.0).normalized(), V(0.0, -1.0, 0.0)
            wl = body_pt(V(0.62, -0.1, 1.42 + 0.01 * math.sin(k * math.pi)), ro, yaw)
            palm, fing = V(0.2, -0.3, 0.95), V(0.95, 0.0, 0.3)
            bend, pitch = -0.08, 0.45
            lf, rf = (0.2, 0.12), (-0.18, -0.08)
        else:                                               # sweep it down into her stance
            k = ease((f - 34) / float(frames - 34))
            yaw = lerp(0.0, yaw0, k)
            ro = V(0, 0, lerp(0.02, -0.06, k))
            g1, sd1, e1 = stance_sword(yaw, ro, 0.0, 0.0)
            arc = math.sin(k * math.pi) * 0.25
            g = body_pt(V(-0.2, -0.08, 2.02), ro, 0.0).lerp(g1, k) + V(-arc, -arc * 0.5, 0.0)
            sd = V(0.06, -0.08, 1.0).normalized().lerp(sd1.normalized(), k).normalized()
            edge = V(0.0, -1.0, 0.0).lerp(e1, k)
            wl = body_pt(V(0.62, -0.1, 1.42).lerp(V(0.42, 0.2, 1.3), k), ro, yaw)
            palm, fing = V(0.2, -0.3, 0.95).lerp(rz(yaw) @ V(0.0, 0.2, -1.0), k), V(0.95, 0.0, 0.3).lerp(rz(yaw) @ V(0.5, 0.6, 0.5), k)
            bend, pitch = lerp(-0.08, 0.12, k), lerp(0.45, 0.0, k)
            lf = (lerp(0.2, 0.18, k), lerp(0.12, 0.15, k))
            rf = (lerp(-0.18, -0.13, k), lerp(-0.08, -0.17, k))
        aims = feet(arm, yaw, lf=lf, rf=rf)
        torso(aims, yaw, bend=bend, chest=0.0, look=yaw, pitch=pitch)
        aims.update(sword_grip(arm, g, sd, edge, pole=rz(yaw) @ V(-1.0, 0.2, -0.4)))
        aims.update(open_hand(arm, wl, palm, fing, pole=rz(yaw) @ V(0.8, 0.6, -0.4)))
        ch, _ = P.solve(aims, ro, rz(yaw))
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- cheer
def make_cheer(arm, frames=40):
    """Rank up: the sword thrust overhead and twirled about its own axis, a fist pump and a hop."""
    P = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        t = f / frames
        up = ease(min(1.0, t / 0.15)) * (1 - ease(max(0.0, (t - 0.8) / 0.2)))
        pump = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.4)) * (1 - max(0.0, (t - 0.8) / 0.2))
        hop = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.9)) * 0.04 * (1 - max(0.0, (t - 0.75) / 0.25))
        yaw = 0.0
        ro = V(0.0, 0.0, -0.02 + hop)
        aims = feet(arm, yaw, lf=(0.17, -0.02), rf=(-0.17, 0.05), lift=(hop * 0.5, hop * 0.5))
        torso(aims, yaw, bend=-0.05 * pump, look=6.0 * math.sin(t * 9), pitch=0.1 + 0.3 * pump)
        g_idle = body_pt(V(-0.22, -0.17, 1.2), ro, yaw)
        g = g_idle.lerp(body_pt(V(-0.28, -0.06, 2.0), ro, yaw), up)
        sd = V(-0.16, 0.55, 0.82).normalized().lerp(V(-0.08, -0.05, 1.0).normalized(), up).normalized()
        twirl = 360.0 * smooth01((t - 0.2) / 0.35)          # the sword spun about its own axis
        e_up = Quaternion(sd, math.radians(twirl)) @ V(0.0, -1.0, 0.0)
        edge = V(-0.5, -0.35, 0.6).lerp(e_up, up)
        aims.update(sword_grip(arm, g, sd, edge, pole=V(-1.0, 0.3, -0.3)))
        wl = V(0.29, 0.0, 0.98).lerp(V(0.44, -0.12, 1.45).lerp(V(0.46, -0.08, 1.95), pump), up)
        aims.update(open_hand(arm, wl, V(-1.0, 0.0, 0.0).lerp(V(-0.6, -0.6, 0.2), up), V(0.05, -0.55, -0.83).lerp(V(0.1, 0.0, 1.0), up),
                              pole=V(1.0, 0.3, -0.5)))
        ch, _ = P.solve(aims, ro, rz(yaw))
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
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
