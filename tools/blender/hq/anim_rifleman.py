"""Rifleman clips (game: 24 fps):
- Idle (120 frames): at the order: the rifle upright at his right side, its butt on the ground by his right foot, his
  right hand round it at the upper band; his left hand hangs easy. He breathes, shifts his weight and looks about.
- Combat (40 frames): on the aim, standing: left foot forward, his body turned side-on, the butt in his right shoulder,
  his cheek down on the stock, his left hand under the fore-stock; a slow sway as he tracks.
- Attack (14 frames = 0.58 s, inside the 0.6 s cooldown): the shot at SHOT (frame 1: the muzzle has not moved yet:
  game.gd spawns the flash, the smoke and the bullet at the muzzle there), the kick (2-3); his right hand leaves the grip
  for the bolt's knob (4), lifts it (5), draws it back (6-7), runs it home (8-9) and turns it down (10), and goes back
  to the grip (11-12); he settles on the aim (13) and is aimed again on the last frame (= the Combat pose).

The rifle and its bolt are bones without a parent, posed each frame by the whole matrix ("world" aims): the rigid
motion of their rest-pose placement (the bolt: the rifle's motion, then its own turn about the bore and its slide along
it). His fists are put on their grips by IK, each fist's length kept in line with its forearm (no broken wrists)."""
import math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
import rifleman as cm
from rig import Poser, leg_aims, arm_aims, frame_map, bone_len, two_bone
from anim import new_action, finish_action, ease

FPS = 24
DEBUG = None              # (a list: the fists' targets of every solved frame, for checking the reach)
SHOT = 1                  # the shot: the muzzle still on the aim (game.gd ATTACK_FRAME)
J = cm.J
V = lambda *a: Vector(a)
VV = lambda p: Vector((float(p[0]), float(p[1]), float(p[2])))
ROOT = VV(J["root"])

# ---------------------------------------------------------------------------------------------- the rifle (rest pose)
_G, _A, _U, _S = cm.RIFLE_FRAME()
G_M, A_M, U_M, S_M = VV(_G), VV(_A), VV(_U), VV(_S)


def mloc(u, v=0.0, h=0.0):
    """A point of the rifle (rifle coordinates), where it is in the rest pose."""
    return G_M + A_M * u + S_M * v + U_M * h


MUZZLE = mloc(cm.MUZZLE_U, 0.0, cm.BAR_H)
BORE0 = mloc(0.0, 0.0, cm.BAR_H)
KNOB = mloc(*cm.KNOB)
_hb, _ht, _w = (float(x[0]) for x in cm.stock_profile(np.array([cm.FORE_GRIP_U], np.float32)))
FORE = mloc(cm.FORE_GRIP_U, 0.0, (_hb + _ht) / 2 - 0.006)
BUTT_END = mloc(cm.BUTT_U, 0.0, -0.045)
LIFT = math.radians(80)                    # the bolt's turn up (radians)
DRAW = 0.085                               # how far it slides back

HAND = {}
for _s in ("R", "L"):
    _wr, _f, _n, _t = cm.hand_frame(_s)
    HAND[_s] = {"wr": VV(_wr), "f": VV(_f), "n": VV(_n), "t": VV(_t), "off": VV(cm.fist_center(_s)) - VV(_wr)}


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def rifle_at(point_rest, point_t, A_t, U_t):
    """The rifle's motion that lays it along A_t (its top toward U_t) with its rest-pose point `point_rest` at point_t."""
    R = frame_map(A_M, Vector(A_t).normalized(), U_M, Vector(U_t))
    return Matrix.Translation(Vector(point_t) - R @ Vector(point_rest)) @ R.to_4x4()


def rot_of(T):
    return T.to_3x3()


def lerp_T(T0, T1, k, pivot_rest):
    """Blend two rigid motions: slerp the turn, lerp where they put `pivot_rest`."""
    q = T0.to_quaternion().slerp(T1.to_quaternion(), k)
    p = (T0 @ pivot_rest).lerp(T1 @ pivot_rest, k)
    R = q.to_matrix()
    return Matrix.Translation(p - R @ pivot_rest) @ R.to_4x4()


def bolt_motion(lift=0.0, draw=0.0):
    """The bolt's own motion (rest-pose rifle coordinates): turned up by `lift` about the bore, slid back `draw`."""
    q = Quaternion(A_M, -lift)
    return (Matrix.Translation(-A_M * draw) @ Matrix.Translation(BORE0) @ q.to_matrix().to_4x4()
            @ Matrix.Translation(-BORE0))


# ---------------------------------------------------------------------------------------------- body
def legs(arm, yaw, lf=(0.19, -0.12), rf=(-0.19, 0.14), open_feet=0.6):
    q = rz(yaw)
    aims = {}
    for side, (bx, by) in (("L", lf), ("R", rf)):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]))
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = VV(J["toe_" + side]) - VV(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * open_feet + (-14 if side == "R" else 6)) @ rest_foot
    return aims


def torso(aims, yaw_chest, lean=0.0, side=0.0, spine_tw=0.0, chest_tw=0.0, neck_tw=0.0, head_tw=0.0, head_tilt=0.0,
          head_up=0.0, neck_side=0.0):
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.22 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.32 * lean, 1.0), chest_tw)
    aims["neck"] = (V(neck_side, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


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
    """holds: {side: (fist, along, pole)}; P: a solved pose (for the shoulders)."""
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


def prop_world(P_, name, T):
    return ("world", T @ P_.rest[name])


def solve(P_, arm, aims, ro, rr, holds, props, extra=None):
    """Solve the body, then put the fists on their grips (holds: {side: callable(P) -> (fist, along, pole)}), then the
    props (props: {bone: callable(P) -> aim}) on top; `extra`: more aims (a free hand) for the second pass."""
    ch, P = P_.solve(aims, ro, rr)
    hs = {side: fn(P) for side, fn in holds.items()}
    if DEBUG is not None:
        DEBUG.append({side: Vector(h[0]) for side, h in hs.items()})
    aims = dict(aims)
    aims.update(hands_aims(arm, P, hs))
    if extra:
        aims.update(extra)
    for nm, fn in props.items():
        aims[nm] = (lambda f: (lambda PP, base: f(PP)))(fn)
    return P_.solve(aims, ro, rr)


def on_rifle(T_m, p_rest, pole, along=None):
    """A hold on the rifle: the fist round its (rest-pose) point p_rest, the thumb along the barrel."""
    return lambda P: (T_m @ p_rest, (rot_of(T_m) @ (along or A_M)).normalized(), pole)


def rifle_props(P_, T_m, lift=0.0, draw=0.0):
    return {"rifle": lambda P: prop_world(P_, "rifle", T_m),
            "bolt": lambda P: prop_world(P_, "bolt", T_m @ bolt_motion(lift, draw))}


# ---------------------------------------------------------------------------------------------- the aim
YAW = -32.0
POCKET = (0.05, 0.08, 0.03)         # the butt's place: ahead of his right shoulder joint, in toward his chest, up
AIM_DOWN = 0.05                     # (radians: the barrel dips a little toward the robots)
L_POLE = V(0.25, -0.1, -1.0)        # his left elbow under the fore-stock
R_POLE = V(-0.7, 0.5, -0.6)         # his right elbow out and down
AIM_BODY = {"yaw": YAW, "lean": 0.2, "side": -0.04, "head_tilt": -0.33, "head_up": -0.42, "neck_side": -0.22,
            "neck_tw": -0.45 * YAW + 4, "head_tw": -0.55 * YAW + 2, "clav_r": 0.16}


def body(arm, br=0.0, sway=0.0, head_up=0.0, push=0.0):
    """The body on the aim; `push`: the recoil rocking him back (0..1)."""
    b = AIM_BODY
    aims = legs(arm, YAW, lf=(0.2, -0.24), rf=(-0.19, 0.2))
    yc = b["yaw"] + 2.5 * push
    ro = rz(YAW) @ V(0.0, -0.025 + 0.025 * push, 0.0) + V(0.0, 0.0, -0.055 + 0.004 * br)
    rr = rz(YAW + (yc - YAW) * 0.45 + 0.8 * sway)
    torso(aims, yc, lean=b["lean"] - 0.08 * push, side=b["side"], spine_tw=math.radians(-3), chest_tw=math.radians(-6),
          neck_tw=math.radians(b["neck_tw"]), head_tw=math.radians(b["head_tw"]), head_tilt=b["head_tilt"],
          head_up=b["head_up"] + head_up, neck_side=b["neck_side"])
    aims["clavicle.L"] = rz(yc) @ V(1.0, -0.25, 0.06)
    aims["clavicle.R"] = rz(yc) @ V(-1.0, 0.05, b["clav_r"] + 0.06 * push)
    return aims, ro, rr


def aim_rifle(P, kick=0.0, sway=0.0, br=0.0, cant=0.0, drop=0.0):
    """The rifle on the aim: the butt plate in his right shoulder's pocket, the barrel level toward the robots (-y),
    dipping a little; `kick` turns the muzzle up about his cheek (radians) and shoves it back; `cant` rolls it a little
    onto its right side (the bolt up into view while he works it); `drop` lowers it from his cheek and out a little
    (while he works the bolt, his hand clear of his face)."""
    sh = P["upperarm.R"].translation
    C = P["chest"].to_3x3()
    fwd = C @ V(0, 0, 1)
    fwd.z = 0.0
    fwd.normalize()
    medial = C @ V(1, 0, 0)
    pocket = sh + fwd * POCKET[0] + medial * POCKET[1] + V(0, 0, POCKET[2])
    A_t = V(0.012 * sway, -math.cos(AIM_DOWN), -math.sin(AIM_DOWN) + 0.004 * br).normalized()
    if kick:
        A_t = Quaternion(A_t.cross(V(0, 0, 1)).normalized(), kick) @ A_t
    U_t = V(0, 0, 1) - A_t * A_t.z
    if cant:
        U_t = Quaternion(A_t, -cant) @ U_t
    pocket = pocket + (V(0, 0, -DROP[0]) - medial * DROP[1]) * drop
    return rifle_at(BUTT_END, pocket + V(0, 0.3 * kick, -0.2 * kick), A_t, U_t)


def aim_holds(T_m, r_hold=None):
    holds = {"L": on_rifle(T_m, FORE, L_POLE)}
    holds["R"] = r_hold or on_rifle(T_m, G_M, R_POLE)
    return holds


# ---------------------------------------------------------------------------------------------- Idle
def idle_frame(arm, P_, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    shift = 0.5 - 0.5 * math.cos(w)
    aims = legs(arm, -4.0, lf=(0.18, -0.03), rf=(-0.18, 0.04), open_feet=0.3)
    ro = V(0.012 * shift - 0.006, 0.0, -0.008 + 0.005 * br)
    rr = rz(-4.0 + 2.5 * math.sin(w))
    look = 0.55 * math.sin(w) + 0.18 * math.sin(w * 3 + 0.4)
    torso(aims, -4.0, lean=-0.02, side=0.02 * (shift - 0.5), spine_tw=0.03 * math.sin(w), chest_tw=0.05 * math.sin(w),
          neck_tw=0.32 * look, head_tw=0.6 * look, head_up=0.05 + 0.04 * br, head_tilt=0.03 * math.sin(w * 2 + 1))
    q = rz(-4.0)
    aims["clavicle.L"] = q @ V(1.0, 0.0, -0.02)
    aims["clavicle.R"] = q @ V(-1.0, 0.04, 0.02)
    # the rifle at the order: upright by his right foot, its trigger guard to the front, the bolt outward
    butt = q @ V(-0.35, -0.13, 0.0) + V(0, 0, -0.004)
    A_t = (q @ V(-0.02, -0.03, 1.0)).normalized()
    U_t = q @ V(0.0, 1.0, 0.0)
    T_m = rifle_at(BUTT_END, butt, A_t, U_t)
    hold_u = 0.45 + 0.004 * br
    hb, ht, w_ = (float(x[0]) for x in cm.stock_profile(np.array([hold_u], np.float32)))
    holds = {"R": on_rifle(T_m, mloc(hold_u, 0.0, (hb + ht) / 2 - 0.004), V(-0.5, 0.6, -0.2))}
    # his left hand hangs easy by his thigh
    extra = arm_aims(arm, "L", q @ V(0.335, 0.02, 0.83 + 0.004 * br), pole=q @ V(0.4, 0.8, -0.3),
                     hand_dir=q @ V(0.05, -0.05, -1.0))
    return solve(P_, arm, aims, ro, rr, holds, rifle_props(P_, T_m), extra=extra)


def make_idle(arm, frames=120):
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        ch, _ = idle_frame(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- Combat
def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        w = 2 * math.pi * (f % frames) / frames
        br, sw = math.sin(w * 2), math.sin(w)
        aims, ro, rr = body(arm, br, sw)
        ch, P = P_.solve(aims, ro, rr)
        T_m = aim_rifle(P, sway=sw, br=br)
        ch, _ = solve(P_, arm, aims, ro, rr, aim_holds(T_m), rifle_props(P_, T_m))
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- Attack: the shot, the bolt
# per frame: (kick, cant, push, bolt lift 0..1, bolt draw 0..1, right hand: "grip" | "knob" | blend 0..1 grip->knob,
# drop 0..1)
ATTACK = {
    0: (0.0, 0.0, 0.0, 0.0, 0.0, "grip", 0.0),
    1: (0.0, 0.0, 0.0, 0.0, 0.0, "grip", 0.0),          # SHOT
    2: (0.13, 0.0, 1.0, 0.0, 0.0, "grip", 0.0),         # the kick
    3: (0.06, 0.08, 0.6, 0.0, 0.0, 0.5, 0.45),
    4: (0.025, 0.18, 0.3, 0.0, 0.0, "knob", 0.85),      # on the knob, the butt dropped from his cheek
    5: (0.012, 0.24, 0.15, 1.0, 0.0, "knob", 1.0),      # up
    6: (0.006, 0.26, 0.05, 1.0, 0.55, "knob", 1.0),     # back
    7: (0.0, 0.26, 0.0, 1.0, 1.0, "knob", 1.0),
    8: (0.0, 0.26, 0.0, 1.0, 0.45, "knob", 1.0),        # home
    9: (0.0, 0.24, 0.0, 1.0, 0.0, "knob", 1.0),
    10: (0.0, 0.17, 0.0, 0.0, 0.0, "knob", 0.85),       # down
    11: (0.0, 0.08, 0.0, 0.0, 0.0, 0.5, 0.5),           # back to the grip, up to his cheek
    12: (0.0, 0.02, 0.0, 0.0, 0.0, "grip", 0.15),
    13: (0.0, 0.0, 0.0, 0.0, 0.0, "grip", 0.0),
    14: (0.0, 0.0, 0.0, 0.0, 0.0, "grip", 0.0),
}
KNOB_OFF = (0.0, 0.026, 0.012)               # the fist's grip centre from the knob (rifle axes: along, right, up)
DROP = (0.06, 0.035)                         # the rifle's drop from his cheek while he works the bolt (down, out)
R_KNOB_POLE = V(-0.8, 0.3, -0.5)


def knob_hold(T_m, lift, draw):
    """The fist pinching the bolt's knob: just out to its right and over it, the thumb along the barrel."""
    M = T_m @ bolt_motion(lift, draw)
    R = rot_of(M)
    p = M @ KNOB + R @ (A_M * KNOB_OFF[0] + S_M * KNOB_OFF[1] + U_M * KNOB_OFF[2])
    return p, (rot_of(T_m) @ A_M).normalized()


def make_attack(arm, frames=14):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        kick, cant, push, lift, draw, rh, drop = ATTACK[f]
        aims, ro, rr = body(arm, push=push, head_up=0.12 * drop)
        ch, P = P_.solve(aims, ro, rr)
        T_m = aim_rifle(P, kick=kick, cant=cant, drop=drop)
        li, dr = LIFT * lift, DRAW * draw
        grip_p = lambda P, T_m=T_m: (T_m @ G_M, (rot_of(T_m) @ A_M).normalized(), R_POLE)
        if rh == "grip":
            r_hold = grip_p
        elif rh == "knob":
            def r_hold(P, T_m=T_m, li=li, dr=dr):
                p, al = knob_hold(T_m, li, dr)
                return (p, al, R_KNOB_POLE)
        else:
            def r_hold(P, T_m=T_m, li=li, dr=dr, k=float(rh)):
                p0, al, _ = grip_p(P)
                p1, _ = knob_hold(T_m, li, dr)
                return (p0.lerp(p1, k) + V(0, 0, 0.02) * math.sin(k * math.pi), al, R_POLE.lerp(R_KNOB_POLE, k))
        ch, _ = solve(P_, arm, aims, ro, rr, aim_holds(T_m, r_hold), rifle_props(P_, T_m, li, dr))
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
