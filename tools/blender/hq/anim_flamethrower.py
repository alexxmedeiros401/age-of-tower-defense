"""Flamethrower clips (keyed frame by frame; the .glb runs them at 24 fps, game.gd CLIP_FPS):
- Idle (96 frames): an easy, wide stance, the gun carried in his right fist at his hip, its nozzle down toward the
  ground before him (the pilot flame turned low); his left fist on his belt. He breathes, looks about, and halfway
  through (GAUGE, frames 40-66) lifts his left hand to the pressure gauge on his chest strap, bends his head to read it
  and taps it twice with a knuckle, then drops the hand back to his belt.
- Combat (40 frames): braced, left foot forward, knees bent, turned side-on to his right; the gun levelled at his right
  hip, both fists on its grips, the nozzle toward the robots (-Y) a little below level, the pilot flame lit (it
  flickers); a slow sway as he tracks.
- Attack (24 frames, the 1.0 s cooldown): he braces lower and swings the nozzle out to his right (0-JET_ON); from
  JET_ON (frame 3) to JET_OFF (frame 17) he sweeps it across in front of him from SWEEP[0] (his right) to SWEEP[1]
  (his left), hips and shoulders turning with it, the gun shuddering a little and the pilot flame swelled: the game
  draws the jet of flame from the nozzle over these frames; then he eases off (the nozzle lifts a little) and comes
  back to the Combat pose (17-24).

The gun rides the parentless `flamer` bone (from the bore over the rear grip to the nozzle's tip), posed in world space
("world" aims: the rigid motion of its rest placement), as Ada's launcher (anim_ada.py); his fists are put on its grips
by IK, each fist's length kept in line with its forearm. The pilot flame's bone (`pilot`, a child of `flamer`) is
scaled: 0.55 in the Idle, about 1 in Combat, up to 1.35 in the jet."""
import math
from mathutils import Vector, Quaternion, Matrix
import flamethrower as cm
from rig import Poser, leg_aims, arm_aims, frame_map, bone_len, two_bone
from anim import new_action, finish_action

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
VV = lambda p: Vector((float(p[0]), float(p[1]), float(p[2])))
ROOT = VV(J["root"])
DEBUG = None           # (a list: the fists' targets of every solved frame, for checking the reach)

FR = 24                # the Attack's length (1.0 s at 24 fps: the cooldown)
JET_ON = 3             # the jet: from here ...
JET_OFF = 17           # ... to here (game.gd draws the flame from the nozzle over these frames)
SWEEP = (-32.0, 30.0)  # the nozzle's turn about the vertical through his hips (degrees, + = toward his left), jet on/off
GAUGE = (40, 66)       # (Idle) the gauge check

# ----------------------------------------------------------------------------------------------- rest-pose frames
G0, A0, U0 = VV(cm.GUN_G0), VV(cm.GUN_A0), VV(cm.GUN_U0)
S0 = A0.cross(U0)
gp = lambda *a: VV(cm.gp(*a))
GRIP_AX = VV(cm.grip_axis())
FORE_PT = gp(cm.FORE_U - 0.004, 0.0, -0.008)            # the left fist's middle on the front grip
TIP = VV(cm.nozzle_tip())
_gc, _gn = cm.gauge_frame()
GAUGE_C, GAUGE_N = VV(_gc), VV(_gn)

HAND = {}
for _s in ("R", "L"):
    _wr, _f, _n, _t = cm.hand_frame(_s)
    HAND[_s] = {"wr": VV(_wr), "f": VV(_f), "n": VV(_n), "t": VV(_t), "off": VV(cm.fist_center(_s)) - VV(_wr)}


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def seg(f, a, b):
    return smooth01((f - a) / float(b - a))


def gun_T(G, A, U):
    """The gun's rigid motion that puts its rear grip's middle at G, its bore along A, its top toward U."""
    R = frame_map(A0, Vector(A).normalized(), U0, Vector(U))
    return Matrix.Translation(Vector(G)) @ R.to_4x4() @ Matrix.Translation(-G0)


def up_perp(A, ref=V(0, 0, 1)):
    A = Vector(A).normalized()
    u = Vector(ref) - A * Vector(ref).dot(A)
    return u.normalized()


def turn_about(T, deg, pivot):
    """A rigid motion followed by a turn of `deg` about the vertical through `pivot`."""
    return Matrix.Translation(pivot) @ rz(deg).to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ T


# ----------------------------------------------------------------------------------------------- body
def feet(arm, yaw, lf=(0.22, -0.04), rf=(-0.22, 0.06), lift=(0.0, 0.0), turn=(10.0, -10.0)):
    """Ankles at the body-frame (x, y) lf / rf turned by yaw (planted: the hips turn over them); `lift` raises each heel."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by), up, tw in (("L", lf, lift[0], turn[0]), ("R", rf, lift[1], turn[1])):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + up)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = VV(J["toe_" + side]) - VV(J["ankle_" + side])
        aims["foot." + side] = rz(yaw + tw) @ (rest_foot + V(0, 0, -up * 0.6))
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0, shrug=(0.0, 0.0), reach=(0.0, 0.0)):
    """Spine and chest bent forward by `bend` radians and to his left by `side`, the chest turned `chest` degrees more;
    the head to the world heading `look` (degrees, 0 = the robots), pitched up by `pitch`; `shrug` (left, right) lifts
    each shoulder, `reach` brings it forward."""
    q = rz(yaw)
    qc = rz(yaw + chest)

    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(math.sin(roll) * 0.5, -0.12 - 0.2 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.04 + 0.6 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.03 - reach[0], 0.02 + shrug[0])
    aims["clavicle.R"] = qc @ V(-1.0, -0.03 - reach[1], 0.02 + shrug[1])


# ----------------------------------------------------------------------------------------------- fists on grips
def grip(side, fist, along, fdir):
    """The hand's "frame" aim and the wrist target that put the fist's grip centre at `fist`, its thumb axis along
    `along`, and its length (wrist to knuckles) as near `fdir` (the forearm) as the grip allows."""
    H = HAND[side]
    t = Vector(along).normalized()
    f = Vector(fdir) - t * Vector(fdir).dot(t)
    if f.length < 1e-6:
        f = t.orthogonal()
    f.normalize()
    n = t.cross(f) if side == "R" else f.cross(t)
    R = frame_map(H["t"], t, H["n"], n)
    return Vector(fist) - R @ H["off"], ("frame", H["t"], t, H["n"], n)


def hands_aims(arm, P, holds):
    aims = {}
    for side, (fist, along, pole) in holds.items():
        sh = P["upperarm." + side].translation.copy()
        la, lb = bone_len(arm, "upperarm." + side), bone_len(arm, "forearm." + side)
        fdir = Vector(fist) - sh
        wrist, fr = grip(side, fist, along, fdir)
        for it in range(3):
            el = two_bone(sh, wrist, la, lb, pole)
            wrist, fr = grip(side, fist, along, Vector(fist) - el)
        aims.update(arm_aims(arm, side, wrist, pole=pole))
        aims["hand." + side] = fr
    return aims


def solve(P_, arm, aims, ro, rr, holds, props, scales=None):
    """Solve the body, then put the fists on their grips (holds: {side: callable(P) -> (fist, along, pole)}), then the
    props (props: {bone: callable(P, base) -> aim}) on top."""
    ch, P = P_.solve(aims, ro, rr, scales=scales)
    hs = {side: fn(P) for side, fn in holds.items()}
    if DEBUG is not None:
        DEBUG.append({side: Vector(h[0]) for side, h in hs.items()})
    aims = dict(aims)
    aims.update(hands_aims(arm, P, hs))
    aims.update(props)
    return P_.solve(aims, ro, rr, scales=scales)


def on_gun(T, side, pole):
    """A fist on the gun: the right one round the rear pistol grip, the left one round the front grip (thumbs up)."""
    R = T.to_3x3()
    if side == "R":
        return lambda P: (T @ G0, R @ GRIP_AX, pole)
    return lambda P: (T @ FORE_PT, R @ U0, pole)


def fist_at(p, along, pole):
    return lambda P: (Vector(p), Vector(along), pole)


def root_delta(P_, P):
    return P["root"] @ P_.rest["root"].inverted()


def props(P_, T_g):
    return {"flamer": lambda P, b: ("world", T_g @ P_.rest["flamer"])}


# ----------------------------------------------------------------------------------------------- the braced stance
C_YAW = -30.0                     # turned side-on to his right, the gun at his right hip
C_CHEST = -12.0
C_FEET = dict(lf=(0.21, -0.2), rf=(-0.23, 0.17), turn=(14.0, -24.0))
C_CROUCH = 0.07
AIM_G = V(-0.28, -0.375, 0.98)    # the rear grip's middle (armature space), clear of his front
AIM_A = V(0.05, -1.0, -0.075).normalized()     # the bore: toward the robots, a little below level
R_POLE = V(-0.7, 0.8, -0.5)       # his right elbow back and out
L_POLE = V(0.7, -0.1, -1.0)       # his left elbow down and out
PIVOT = V(0.0, 0.03, 0.0)         # (the sweep turns the gun about the vertical through his hips)


def stance(arm, br=0.0, sway=0.0, crouch=0.0, bend=0.0, turn=0.0, look=None, pitch=0.0, lift=(0.0, 0.0)):
    """The braced stance, the hips and shoulders turned `turn` more degrees (the sweep: his whole body turns with the gun
    over his planted feet, so the gun keeps its place at his hip)."""
    yaw = C_YAW + turn
    aims = feet(arm, C_YAW, lift=lift, **C_FEET)
    ro = rz(C_YAW) @ V(0.0, -0.02, 0.0) + V(0.0, 0.0, -C_CROUCH - crouch + 0.004 * br)
    rr = rz(yaw + 1.2 * sway)
    torso(aims, yaw, bend=0.13 + bend, side=0.02 * sway, chest=C_CHEST, look=turn * 0.9 if look is None else look,
          pitch=-0.02 + pitch, reach=(0.15, 0.0))
    return aims, ro, rr


def aim_T(br=0.0, sway=0.0, turn=0.0, push=0.0, lift=0.0, shake=(0.0, 0.0), drop=0.0):
    """The gun on the aim, turned `turn` degrees about his hips' vertical; `push` shoves it back toward him (the jet's
    thrust), `lift` tips the nozzle up (easing off), `shake` jitters it (radians, about up and across)."""
    A = AIM_A
    if lift:
        A = Quaternion(A.cross(V(0, 0, 1)).normalized(), lift) @ A
    if shake[0] or shake[1]:
        A = rz(math.degrees(shake[0])) @ (Quaternion(A.cross(V(0, 0, 1)).normalized(), shake[1]) @ A)
    G = AIM_G + V(0.006 * sway, 0.0, 0.004 * br - drop) + V(0.0, 0.045, 0.0) * push
    T = gun_T(G, A, up_perp(A))
    return turn_about(T, turn, PIVOT) if turn else T


def flicker(f, base=1.0, amp=0.07):
    return base + amp * (0.6 * math.sin(f * 2.3) + 0.4 * math.sin(f * 5.1 + 1.0))


def combat_pose(arm, P_, t, f=0):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    body, ro, rr = stance(arm, br, sw, look=0.0)
    T_g = aim_T(br, sw)
    holds = {"R": on_gun(T_g, "R", R_POLE), "L": on_gun(T_g, "L", L_POLE)}
    return solve(P_, arm, body, ro, rr, holds, props(P_, T_g), scales={"pilot": flicker(f)})


def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        ch, _ = combat_pose(arm, P_, (f % frames) / frames, f % frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- Attack: the sweep
def sweep_at(f):
    """The nozzle's turn (degrees) at frame f: out to his right (0-JET_ON), across (JET_ON-JET_OFF, a steady sweep
    eased only at its very ends), back to the middle (JET_OFF-FR)."""
    a, b = SWEEP
    if f <= JET_ON:
        return a * smooth01(f / float(JET_ON))
    if f <= JET_OFF:
        k = (f - JET_ON) / float(JET_OFF - JET_ON)
        k = 0.85 * k + 0.15 * smooth01(k)
        return a + (b - a) * k
    return b * (1.0 - smooth01((f - JET_OFF) / float(FR - JET_OFF)))


def jet_on(f):
    """0..1: the jet's thrust (ramps in over a frame, holds, ramps out over a frame)."""
    return min(1.0, max(0.0, f - JET_ON + 1.0) / 1.5) * min(1.0, max(0.0, JET_OFF + 1.0 - f) / 1.5)


def attack_pose(arm, P_, f):
    turn = sweep_at(f)
    brace = seg(f, 0, JET_ON) * (1.0 - seg(f, JET_OFF, FR))        # down and in for the jet
    j = jet_on(f)
    ease_off = math.sin(math.pi * min(1.0, max(0.0, (f - JET_OFF) / float(FR - JET_OFF))))
    body, ro, rr = stance(arm, crouch=0.035 * brace, bend=0.05 * brace, turn=turn, pitch=0.02 * brace,
                          lift=(0.0, 0.025 * brace))
    shake = (0.012 * j * math.sin(f * 3.7), 0.01 * j * math.sin(f * 5.3 + 0.7))
    T_g = aim_T(turn=turn, push=0.2 * j, lift=0.11 * ease_off, shake=shake, drop=0.03 * brace)
    holds = {"R": on_gun(T_g, "R", R_POLE), "L": on_gun(T_g, "L", L_POLE)}
    pilot = flicker(f, 1.0 + 0.35 * j, 0.07)
    return solve(P_, arm, body, ro, rr, holds, props(P_, T_g), scales={"pilot": pilot})


def make_attack(arm, frames=FR):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        ch, _ = attack_pose(arm, P_, f)
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- Idle: the gauge check
I_YAW = -8.0
I_FEET = dict(lf=(0.24, -0.03), rf=(-0.25, 0.05), turn=(16.0, -18.0))
I_A = V(0.06, -0.62, -0.78).normalized()       # (body frame) the bore: nozzle down toward the ground before him
I_G = V(-0.38, -0.2, 0.86)                     # (body frame) the rear grip's middle, at his right hip
BELT_L = V(0.375, -0.04, 0.93)                  # (body frame) his left fist on his hip (on the belt)


def idle_pose(arm, P_, t, f):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    fr = t * 96.0
    g = seg(fr, GAUGE[0], GAUGE[0] + 6) * (1.0 - seg(fr, GAUGE[1] - 6, GAUGE[1]))       # the hand up at the gauge
    read = seg(fr, GAUGE[0] + 2, GAUGE[0] + 8) * (1.0 - seg(fr, GAUGE[1] - 8, GAUGE[1] - 1))   # his head bent to read it
    tap = 0.0
    for tf in (GAUGE[0] + 10, GAUGE[0] + 16):                                              # two knuckle taps
        tap = max(tap, math.exp(-((fr - tf) / 1.6) ** 2))
    yaw = I_YAW + 2.5 * sway
    aims = feet(arm, I_YAW, **I_FEET)
    ro = V(0.008 * sway, 0.0, -0.025 + 0.005 * br)
    look = (26.0 * math.sin(w + 0.5) + 6.0 * math.sin(w * 3)) * (1.0 - read) + 14.0 * read
    torso(aims, yaw, bend=0.05 + 0.04 * read, side=0.015 * sway, chest=2.0 * sway + 6.0 * g, look=look,
          pitch=0.03 + 0.02 * br - 0.62 * read, roll=-0.1 * read, shrug=(0.06 * g, 0.0))
    ch, P = P_.solve(aims, ro, rz(yaw))
    Dr = root_delta(P_, P)
    R = Dr.to_3x3()
    A = (R @ I_A).normalized()
    T_g = gun_T(Dr @ (I_G + V(0.0, 0.0, 0.004 * br)), A, up_perp(A, R @ V(0.0, -1.0, 0.0)))
    holds = {"R": on_gun(T_g, "R", R @ V(-1.0, 0.5, -0.3))}
    # the left fist: on his belt, or up at the gauge (the knuckles to its glass, tapping)
    belt = Dr @ BELT_L
    Cm = P["chest"] @ P_.rest["chest"].inverted()
    gc, gn = Cm @ GAUGE_C, (Cm.to_3x3() @ GAUGE_N).normalized()
    at_gauge = gc + gn * (0.075 - 0.03 * tap) + V(0.03, 0.0, -0.02)
    p = belt.lerp(at_gauge, g)
    along = (R @ V(0.0, -0.4, -1.0)).normalized().lerp(V(-0.2, -0.6, 0.75).normalized(), g).normalized()
    holds["L"] = fist_at(p, along, R @ V(1.0, 0.4 - 0.3 * g, -0.4 - 0.5 * g))
    return solve(P_, arm, aims, ro, rz(yaw), holds, props(P_, T_g), scales={"pilot": flicker(f, 0.55, 0.05)})


def make_idle(arm, frames=96):
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        ch, _ = idle_pose(arm, P_, (f % frames) / frames, f % frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
