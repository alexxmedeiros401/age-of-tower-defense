"""Musketeer clips (game: 24 fps):
- Idle (120 frames): standing easy, the musket on his right shoulder (his right hand on the wrist of the stock, the
  barrel sloping up behind him), the rest upright in his left hand like a staff, its spike on the ground by his left
  foot; he breathes, shifts his weight and looks about.
- Combat (40 frames): the aim: left foot forward, knees bent, his body turned side-on, the rest planted ahead with the
  barrel laid in its fork, the butt at his right shoulder and his cheek down on the stock; a slow sway.
- Attack (28 frames = 1.17 s, inside the 1.2 s cooldown): the shot at SHOT (frame 1: the serpentine dips the match into
  the pan; the muzzle has not moved yet: game.gd spawns the flash, the smoke and the bullet at MUZZLE there), the kick
  (2-3); his left hand takes the barrel at the fork and swings the musket upright, its butt to the ground before him
  (3-8), while his right hand fetches the charge (an apostle) from his bandolier and tips it into the muzzle (6-10); he
  draws the ramrod from under the barrel, arm high (11-15), turns it into the muzzle and drives it home twice (15-20),
  draws it again and slides it back into its pipes (20-23); then the musket swings back up, the butt to his shoulder,
  the barrel down into the fork (23-27), and he is aimed again on the last frame (= the Combat pose).

The musket, its ramrod, the rest and the charge are bones without a parent, posed each frame by the whole matrix
("world" aims): the rigid motion of their rest-pose placement. His fists are put on their grips by IK, each fist's
length kept in line with its forearm (no broken wrists). The serpentine is the musket's bone, turned about its pivot."""
import math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
import musketeer as cm
from rig import Poser, leg_aims, arm_aims, frame_map, bone_len, two_bone
from anim import new_action, finish_action, ease

FPS = 24
DEBUG = None              # (a list: the fists' targets of every solved frame, for checking the reach)
SHOT = 1                  # the match in the pan, the muzzle still on the aim (game.gd ATTACK_FRAME)
J = cm.J
V = lambda *a: Vector(a)
VV = lambda p: Vector((float(p[0]), float(p[1]), float(p[2])))
ROOT = VV(J["root"])

# ---------------------------------------------------------------------------------------------- the props (rest pose)
_G, _A, _U, _S = cm.musket_frame()
G_M, A_M, U_M, S_M = VV(_G), VV(_A), VV(_U), VV(_S)


def mloc(u, v=0.0, h=0.0):
    """A point of the musket (musket coordinates), where it is in the rest pose."""
    return G_M + A_M * u + S_M * v + U_M * h


_K, _RA, _RW, _RX = cm.rest_frame()
K_R, A_R, W_R = VV(_K), VV(_RA), VV(_RW)


def rloc(s, w=0.0):
    return K_R + A_R * s + W_R * w


_hb, _ht, _w = (float(x[0]) for x in cm.stock_profile(np.array([0.1], np.float32)))
MUZZLE = mloc(cm.MUZZLE_U, 0.0, cm.BAR_H)
REST_LEN = cm.REST_CROTCH - cm.REST_FOOT
_cap, _sp, _hz = cm.charge_spot()
CHG_CAP = VV(_cap)
CHG_MID = CHG_CAP - V(0, 0, cm.FLASK_H * 0.55)
RAM_GRIP_U = cm.RAM_U[1] - 0.035          # where his fist takes the ramrod, near its brass tip
DIP = 0.77                                # the serpentine's turn that puts the match in the pan (radians)

HAND = {}
for _s in ("R", "L"):
    _wr, _f, _n, _t = cm.hand_frame(_s)
    HAND[_s] = {"wr": VV(_wr), "f": VV(_f), "n": VV(_n), "t": VV(_t), "off": VV(cm.fist_center(_s)) - VV(_wr)}


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def rigid(p0, a0, b0, p1, a1, b1):
    """The rigid motion taking a point p0 to p1, the direction a0 to a1 and the plane (a0, b0) to the plane (a1, b1)."""
    R = frame_map(a0, a1, b0, b1)
    return Matrix.Translation(Vector(p1)) @ R.to_4x4() @ Matrix.Translation(-Vector(p0))


def musket_at(point_rest, point_t, A_t, U_t):
    """The musket's motion that lays it along A_t (its top toward U_t) with its rest-pose point `point_rest` at point_t."""
    R = frame_map(A_M, Vector(A_t).normalized(), U_M, Vector(U_t))
    return Matrix.Translation(Vector(point_t) - R @ Vector(point_rest)) @ R.to_4x4()


def rest_at(foot_t, up_t, spread_t):
    """The rest's motion: its spike's tip at foot_t, the staff along up_t, the fork's prongs spread along spread_t."""
    return rigid(rloc(cm.REST_FOOT), A_R, W_R, Vector(foot_t), Vector(up_t).normalized(), Vector(spread_t))


def rot_of(T):
    return T.to_3x3()


def lerp_T(T0, T1, k, pivot_rest):
    """Blend two rigid motions: slerp the turn, lerp where they put `pivot_rest`."""
    q = T0.to_quaternion().slerp(T1.to_quaternion(), k)
    p = (T0 @ pivot_rest).lerp(T1 @ pivot_rest, k)
    R = q.to_matrix()
    return Matrix.Translation(p - R @ pivot_rest) @ R.to_4x4()


# ---------------------------------------------------------------------------------------------- body
def legs(arm, yaw, lf=(0.19, -0.12), rf=(-0.19, 0.14), lift_l=0.0, open_feet=0.6):
    q = rz(yaw)
    aims = {}
    for side, (bx, by), lift in (("L", lf, lift_l), ("R", rf, 0.0)):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + lift)
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
    """holds: {side: (fist, along, pole)}; P: a solved pose (for the shoulders). Two passes put the wrist where the
    forearm, from the IK elbow, runs into the fist."""
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


# ---------------------------------------------------------------------------------------------- the props' bones
def prop_world(P_, name, T):
    """("world", M) for a prop bone moved by the rigid motion T from its rest placement."""
    return ("world", T @ P_.rest[name])


def serp_aim(T_m, dip):
    S_w = (rot_of(T_m) @ S_M).normalized()
    return ("rot", Quaternion(S_w, -dip))


# ---------------------------------------------------------------------------------------------- the aim
YAW = -32.0
AIM_DOWN = 0.05                     # (radians: the barrel dips a little toward the robots)
FORK_U = 0.56                       # where the barrel lies in the fork
L_GRIP_S = cm.REST_CROTCH - 0.14    # his left fist on the staff, under the fork
L_POLE = V(0.7, 0.1, -1.0)
R_POLE = V(-0.6, 0.6, -1.0)

# the body on the aim (k = 0) and loading (k = 1): his feet stay planted, he turns square and straightens
AIM_BODY = {"yaw": YAW, "lean": 0.2, "side": -0.04, "crouch": 0.0, "head_tilt": -0.26, "head_up": -0.42, "neck_side": -0.1,
            "neck_tw": -0.45 * YAW + 4, "head_tw": -0.55 * YAW + 2, "clav_r": 0.16}
LOAD_BODY = {"yaw": 7.0, "lean": 0.12, "side": 0.02, "crouch": 0.25, "head_tilt": 0.0, "head_up": -0.3, "neck_side": 0.0,
             "neck_tw": -4.0, "head_tw": -8.0, "clav_r": 0.12}


def body(arm, k=0.0, br=0.0, sway=0.0, head_up=0.0, clav_r=0.0, extra_yaw=0.0):
    """The body between the aim (k = 0) and the loading stance (k = 1)."""
    b = {n: AIM_BODY[n] + (LOAD_BODY[n] - AIM_BODY[n]) * k for n in AIM_BODY}
    aims = legs(arm, YAW, lf=(0.2, -0.24), rf=(-0.19, 0.2))
    yc = b["yaw"] + extra_yaw
    ro = rz(YAW) @ V(0.0, -0.025, 0.0) + V(0.0, 0.0, -0.055 - 0.05 * b["crouch"] + 0.004 * br)
    rr = rz(YAW + (yc - YAW) * 0.45 + 0.8 * sway)
    torso(aims, yc, lean=b["lean"], side=b["side"], spine_tw=math.radians(-3), chest_tw=math.radians(-6),
          neck_tw=math.radians(b["neck_tw"]), head_tw=math.radians(b["head_tw"]), head_tilt=b["head_tilt"],
          head_up=b["head_up"] + head_up, neck_side=b["neck_side"])
    aims["clavicle.L"] = rz(yc) @ V(1.0, -0.25, 0.06)
    aims["clavicle.R"] = rz(yc) @ V(-1.0, 0.05, b["clav_r"] + clav_r)
    return aims, ro, rr


def aim_musket(P, kick=0.0, sway=0.0, br=0.0):
    """The musket on the aim: the butt plate in his right shoulder's pocket, the barrel level toward the robots
    (-y), dipping a little; `kick` turns the muzzle up about the butt (radians) and shoves it back."""
    sh = P["upperarm.R"].translation
    fwd = P["chest"].to_3x3() @ V(0, -1, 0)
    fwd.z = 0.0
    fwd.normalize()
    pocket = sh + fwd * 0.07 + V(0.035, 0.0, 0.035)
    A_t = V(0.012 * sway, -math.cos(AIM_DOWN), -math.sin(AIM_DOWN) + 0.004 * br).normalized()
    if kick:
        A_t = Quaternion(A_t.cross(V(0, 0, 1)).normalized(), kick) @ A_t
    U_t = V(0, 0, 1) - A_t * A_t.z
    butt = mloc(cm.BUTT_U + 0.02, 0.0, -0.055)
    return musket_at(butt, pocket + V(0, 0.35 * kick, 0.0), A_t, U_t)


def aim_rest(T_m):
    """The rest planted ahead, the barrel's underside in the crotch of its fork."""
    under = T_m @ mloc(FORK_U, 0.0, cm.BAR_H - float(cm.barrel_r(np.array([FORK_U], np.float32))[0]) - 0.003)
    A_t = (rot_of(T_m) @ A_M).normalized()
    spread = V(0, 0, 1).cross(A_t).normalized()
    h = under.z + 0.012
    dxy = math.sqrt(max(REST_LEN ** 2 - h * h, 0.0))
    away = V(0.25, -1.0, 0.0).normalized()
    foot = V(under.x, under.y, -0.012) + away * dxy
    return rest_at(foot, under - foot, spread)


# ---------------------------------------------------------------------------------------------- solving a frame
def solve(P_, arm, aims, ro, rr, holds, props, scales=None):
    """Solve the body, then put the fists on their grips (holds: {side: callable(P) -> (fist, along, pole)}), then the
    props (props: {bone: callable(P) -> aim}) on top."""
    ch, P = P_.solve(aims, ro, rr, scales=scales)
    hs = {side: fn(P) for side, fn in holds.items()}
    if DEBUG is not None:
        DEBUG.append({side: Vector(h[0]) for side, h in hs.items()})
    aims = dict(aims)
    aims.update(hands_aims(arm, P, hs))
    for nm, fn in props.items():
        aims[nm] = (lambda f: (lambda PP, base: f(PP)))(fn)
    return P_.solve(aims, ro, rr, scales=scales)


def on_musket(T_m, u, v=0.0, h=0.0, pole=None):
    """A hold on the musket: the fist round its point (u, v, h), the thumb along the barrel."""
    return lambda P: (T_m @ mloc(u, v, h), rot_of(T_m) @ A_M, pole)


def on_rest(T_r, s, pole):
    return lambda P: (T_r @ rloc(s), rot_of(T_r) @ A_R, pole)


def hand_motion(P_, P, side):
    """The rigid motion of a hand from its rest pose (for what it carries)."""
    return P["hand." + side] @ P_.rest["hand." + side].inverted()


def body_motion(P_, P, bone="spine"):
    return P[bone] @ P_.rest[bone].inverted()


def _fist_hold(side, p_rest, a_rest, b_rest):
    """The motion taking a prop from its rest placement into the rest-pose fist (its point p_rest at the fist's grip
    centre, a_rest along the thumb axis, b_rest toward the palm)."""
    H = HAND[side]
    return rigid(p_rest, a_rest, b_rest, H["wr"] + H["off"], H["t"], H["n"])


CHARGE_IN_FIST = _fist_hold("R", CHG_MID, V(0, 0, 1), V(1, 0, 0))                 # the flask's cap toward his thumb
RAM_IN_FIST = _fist_hold("R", mloc(RAM_GRIP_U, 0.0, cm.RAM_H), A_M, U_M)            # the rod along his thumb axis


def base_props(P_, T_m, T_r, dip=0.0):
    return {"musket": lambda P: prop_world(P_, "musket", T_m), "rest": lambda P: prop_world(P_, "rest", T_r),
            "ramrod": lambda P: prop_world(P_, "ramrod", T_m),
            "charge": lambda P: prop_world(P_, "charge", body_motion(P_, P)),
            "serpentine": lambda P: serp_aim(T_m, dip)}


# ---------------------------------------------------------------------------------------------- Idle
def idle_frame(arm, P_, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    shift = 0.5 - 0.5 * math.cos(w)
    aims = legs(arm, -6.0, lf=(0.2, -0.05), rf=(-0.19, 0.07), open_feet=0.3)
    ro = V(0.012 * shift - 0.006, 0.0, -0.008 + 0.005 * br)
    rr = rz(-6.0 + 2.5 * math.sin(w))
    look = 0.5 * math.sin(w) + 0.15 * math.sin(w * 3 + 0.4)
    torso(aims, -6.0, lean=0.0, side=0.02 * (shift - 0.5), spine_tw=0.03 * math.sin(w), chest_tw=0.05 * math.sin(w),
          neck_tw=0.32 * look, head_tw=0.6 * look, head_up=0.06 + 0.04 * br, head_tilt=0.03 * math.sin(w * 2 + 1))
    q = rz(-6.0)
    aims["clavicle.L"] = q @ V(1.0, 0.0, -0.02)
    aims["clavicle.R"] = q @ V(-1.0, 0.05, 0.1)
    ch, P = P_.solve(aims, ro, rr)
    # the musket on his right shoulder: the stock just ahead of the lock lies on the shoulder, sloping up behind him
    sh = P["upperarm.R"].translation
    A_t = V(-0.16, 0.56, 0.81).normalized()
    up = V(0, 0, 1) - A_t * A_t.z
    T_m = musket_at(mloc(0.27, 0.0, -0.024), sh + V(-0.005, 0.02, 0.135 + 0.003 * br), A_t, up)
    # the rest upright in his left hand, its spike by his left foot
    foot = q @ V(0.37, -0.16, 0.0) + V(0, 0, -0.012)
    T_r = rest_at(foot, V(0.02, -0.03, 1.0), V(1, 0, 0))
    holds = {"R": on_musket(T_m, -0.02, pole=V(-0.4, 0.4, -1.0)),
             "L": on_rest(T_r, cm.REST_FOOT + 1.14 + 0.004 * br, V(1.0, 0.3, -0.5))}
    return solve(P_, arm, aims, ro, rr, holds, base_props(P_, T_m, T_r))


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
        aims, ro, rr = body(arm, 0.0, br, sw)
        ch, P = P_.solve(aims, ro, rr)
        T_m = aim_musket(P, sway=sw, br=br)
        T_r = aim_rest(T_m)
        holds = {"R": on_musket(T_m, 0.0, pole=R_POLE), "L": on_rest(T_r, L_GRIP_S, L_POLE)}
        ch, _ = solve(P_, arm, aims, ro, rr, holds, base_props(P_, T_m, T_r))
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- Attack: shot and reload
LOAD_BUTT = V(0.3, -0.44, -0.004)         # the butt's heel on the ground before him, a little to his left
LOAD_MUZZLE = V(-0.17, -0.42, 1.44)       # the muzzle before his right shoulder (he loads standing it there)
L_LOAD_U = 0.62                           # his left fist on the barrel (from the fork on)
RAM_CLEAR = cm.MUZZLE_U + 0.025 - cm.RAM_U[0]      # how far the rod slides to clear the muzzle
RAM_DEEP = 0.34                           # how far it goes down the bore at a stroke
R_LOAD_POLE = V(-0.8, 0.5, -0.6)


def load_musket():
    butt = mloc(cm.BUTT_U, 0.0, -0.06)
    A_t = (LOAD_MUZZLE - LOAD_BUTT).normalized()
    U_t = V(0, -1, 0) - A_t * A_t.y                 # (its top away from him: the ramrod toward him)
    return musket_at(butt, LOAD_BUTT, A_t, U_t)


def rod_T(T_m, along=0.0, over=0.0):
    """The ramrod slid `along` the barrel from its pipes and moved `over` toward the bore's line (0..1)."""
    return T_m @ Matrix.Translation(A_M * along + U_M * (over * (cm.BAR_H - cm.RAM_H)))


# the ramrod's slide (along the barrel from its pipes) and move toward the bore's line, frames 12-23
RAM_KEYS = {12: (0.0, 0.0), 13: (RAM_CLEAR * 0.3, 0.0), 14: (RAM_CLEAR * 0.75, 0.0), 15: (RAM_CLEAR, 0.0),
            16: (RAM_CLEAR - 0.03, 1.0), 17: (RAM_CLEAR - 0.03 - RAM_DEEP * 0.6, 1.0), 18: (RAM_CLEAR - 0.03 - RAM_DEEP, 1.0),
            19: (RAM_CLEAR - 0.03 - RAM_DEEP * 0.45, 1.0), 20: (RAM_CLEAR - 0.03 - RAM_DEEP, 1.0), 21: (RAM_CLEAR - 0.01, 0.55),
            22: (RAM_CLEAR * 0.5, 0.0), 23: (0.0, 0.0)}
# the body between the aim and the loading stance
LOAD_K = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.08, 4: 0.3, 5: 0.6, 6: 0.85, 7: 1.0, 22: 1.0, 23: 0.9, 24: 0.65, 25: 0.35, 26: 0.12,
          27: 0.0, 28: 0.0}
# the musket's swing (0 = on the aim, 1 = stood before him), about his left fist on the barrel
SWING = {3: 0.0, 4: 0.1, 5: 0.35, 6: 0.65, 7: 0.9, 8: 1.0, 22: 1.0, 23: 0.88, 24: 0.65, 25: 0.38, 26: 0.13, 27: 0.0}


def _key(table, f, default=0.0):
    ks = sorted(table)
    if f <= ks[0]:
        return table[ks[0]] if f >= ks[0] or default is None else default
    for a, b in zip(ks, ks[1:]):
        if a <= f <= b:
            t = (f - a) / float(b - a)
            va, vb = table[a], table[b]
            return va + (vb - va) * t if not isinstance(va, tuple) else tuple(x + (y - x) * t for x, y in zip(va, vb))
    return table[ks[-1]]


def make_attack(arm, frames=28):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    T_load = load_musket()
    pivot = mloc(L_LOAD_U, 0.0, cm.BAR_H)
    mz_load = T_load @ MUZZLE
    A_load = (rot_of(T_load) @ A_M).normalized()
    chg_released = None
    let_go = None
    for f in range(frames + 1):
        dip = {1: DIP, 2: DIP * 0.55, 3: DIP * 0.2}.get(f, 0.0)
        kick = {2: 0.1, 3: 0.045}.get(f, 0.0)
        kload = _key(LOAD_K, f)
        head_up = 0.32 * (1.0 if 13 <= f <= 15 else 0.0) + 0.15 * (1.0 if f in (12, 16) else 0.0)
        clav = 0.45 if f in (14, 15, 16, 21) else (0.25 if f in (13, 17, 19, 22) else (0.1 if f in (12, 18, 20) else 0.0))
        aims, ro, rr = body(arm, kload, head_up=head_up, clav_r=clav)
        ch, P = P_.solve(aims, ro, rr)
        # the aim as it stands this frame (the musket, the rest planted where the aim puts it)
        aims0, ro0, rr0 = body(arm, 0.0)
        ch0, P0 = P_.solve(aims0, ro0, rr0)
        T_aim = aim_musket(P0, kick=kick)
        T_r = aim_rest(aim_musket(P0))
        sw = _key(SWING, f) if 3 <= f <= 27 else 0.0
        if 8 < f < 22:
            sw = 1.0
        T_lift = Matrix.Translation(V(0, 0.0, 0.05)) @ T_aim
        T_m = T_aim if sw <= 0.0 else lerp_T(T_lift, T_load, sw, pivot)
        props = base_props(P_, T_m, T_r, dip)
        holds = {}
        # his left hand: on the rest's staff, on the barrel through the reload, back to the staff
        if f <= 2 or f >= 27:
            holds["L"] = on_rest(T_r, L_GRIP_S, L_POLE)
        elif f == 3:
            def l_hold(P, T_m=T_m, T_r=T_r):
                a = T_r @ rloc(L_GRIP_S)
                b = T_m @ mloc(L_LOAD_U, 0.0, 0.0)
                return (a.lerp(b, 0.55), (rot_of(T_r) @ A_R).lerp(rot_of(T_m) @ A_M, 0.55), L_POLE)
            holds["L"] = l_hold
        else:
            holds["L"] = on_musket(T_m, L_LOAD_U - 0.08 * (1.0 - min(1.0, sw / 0.6)) if f <= 8 else L_LOAD_U, 0.0, 0.0, pole=L_POLE)
        # his right hand
        if f <= 4 or f >= 26:
            holds["R"] = on_musket(T_m, 0.0, pole=R_POLE)
        elif f <= 8:                                                     # to the charge on his bandolier
            kk = ease((f - 4) / 4.0)
            def r_hold(P, kk=kk):
                a, al0 = let_go
                b = body_motion(P_, P) @ CHG_MID
                al = al0.lerp(body_motion(P_, P).to_3x3() @ V(0, 0, 1), kk)
                return (a.lerp(b, kk) + V(0.0, -0.08, 0.05) * math.sin(kk * math.pi), al, R_LOAD_POLE)
            holds["R"] = r_hold
        elif f <= 10:                                                    # up to the muzzle and tipped into it
            def r_hold(P, f=f):
                b = body_motion(P_, P) @ CHG_MID
                if f == 9:
                    return (b.lerp(mz_load + A_load * 0.1, 0.65) + V(0, -0.04, 0.04), V(0.25, -0.35, 0.9).normalized(), R_LOAD_POLE)
                return (mz_load + A_load * (cm.FLASK_H * 0.55 + 0.012) + V(0.0, 0.004, 0.0), -A_load, R_LOAD_POLE)
            holds["R"] = r_hold
        elif f == 11:                                                    # let go: down to the ramrod's tip
            holds["R"] = on_musket(T_load, cm.RAM_U[1] + 0.03, 0.0, cm.RAM_H - 0.01, pole=R_LOAD_POLE)
        elif f <= 23:                                                    # the ramrod
            along, over = _key(RAM_KEYS, f)
            T_rod = rod_T(T_load, along, over)
            holds["R"] = (lambda Tr: (lambda P: (Tr @ mloc(RAM_GRIP_U, 0.0, cm.RAM_H), rot_of(Tr) @ A_M, R_LOAD_POLE)))(T_rod)
            if 13 <= f <= 22:
                props["ramrod"] = lambda P: ("world", hand_motion(P_, P, "R") @ RAM_IN_FIST @ P_.rest["ramrod"])
        else:                                                            # down to the stock's wrist as it comes up
            def r_hold(P, T_m=T_m, f=f):
                a = T_load @ mloc(cm.RAM_U[1], 0.0, cm.RAM_H - 0.02)
                b = T_m @ mloc(0.0)
                k = 0.45 if f == 24 else 0.8
                return (a.lerp(b, k), (rot_of(T_m) @ A_M), R_POLE)
            holds["R"] = r_hold
        # the charge: in his fist (frames 8-10), then dropped, swinging back to its place on the bandolier
        if 8 <= f <= 10:
            props["charge"] = lambda P: ("world", hand_motion(P_, P, "R") @ CHARGE_IN_FIST @ P_.rest["charge"])
        elif 11 <= f <= 13 and chg_released is not None:
            k = {11: 0.35, 12: 0.75, 13: 0.95}[f]
            def chg(P, k=k):
                home = body_motion(P_, P)
                M = lerp_T(chg_released, home, k, CHG_MID)
                return ("world", Matrix.Translation(V(0, -0.025, 0) * math.sin(k * math.pi)) @ M @ P_.rest["charge"])
            props["charge"] = chg
        ch, P = solve(P_, arm, aims, ro, rr, holds, props)
        if f == 4:
            let_go = (T_m @ mloc(0.0), rot_of(T_m) @ A_M)
        if f == 10:
            chg_released = hand_motion(P_, P, "R") @ CHARGE_IN_FIST
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def _constant(act, bones):
    """(Constant interpolation on these bones' channels, for anything that must jump.)"""
    if not bones:
        return
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
        if any(('pose.bones["%s"]' % b) in fc.data_path for b in bones):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
