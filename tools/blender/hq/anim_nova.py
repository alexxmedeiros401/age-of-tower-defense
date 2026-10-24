"""Nova's clips (keyed frame by frame; the .glb runs them at 24 fps, game.gd CLIP_FPS).

Idle    : (120) the pistol held up beside her right shoulder, its emitter to the sky (her right fist at her shoulder, the
          elbow down), her left fist on her hip; she shifts her weight and looks about; once round the loop she lifts her
          left forearm and glances down at the holo-deck on it.
Combat  : (40) the one-handed aim: turned side-on, her right shoulder toward the robots (right foot forward), her right
          arm out with the pistol level toward them (-y); her left forearm raised across her front, the deck on it turned
          up; a slow sway.
Attack  : (FR = 18 frames, inside the 0.8 s cooldown) a double tap: the shots at SHOTS (frames 1 and 3: game.gd adds the
          beams at the emitter; the aim held at frame 1), each kicks the emitter up a little; the recoil settles and she
          is back on the aim (= Combat) by frame 14.
Ability : Orbital Laser (AB_FR = 70): she turns to the front and docks the pistol on her right thigh (0-10), raises her
          left forearm and taps commands into the deck with her right fist (12-30, four taps), then flings her left fist
          up at the sky, the deck to the satellite, looking up (SIGNAL, frame 38, held to 52: game.gd fires the orbital
          lasers; NOVA_SIGNAL is her raised fist); her right fist rests on her hip meanwhile; then her left arm comes down,
          her right hand draws the pistol (52-62) and she is back on the aim (70).
Cheer   : (CH_FR = 48) she thrusts the pistol up high (its emitter to the sky), hops with a whoop (her head thrown back),
          pumps her left fist twice overhead and comes back down onto the aim.

Props are posed in world space: the pistol (parentless) by the rigid motion of its rest placement, her right fist put on
its grip by IK (the fist's length kept in line with the forearm, as Maya's and Ada's); docked on her thigh it follows her
thigh. Each forearm takes most of its hand's roll (`rolled`), so the deck on her left forearm turns with her hand."""
import math
from mathutils import Vector, Quaternion, Matrix
import nova as cm
from rig import Poser, leg_aims, arm_aims, frame_map, bone_len, two_bone
from anim import new_action, finish_action

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
VV = lambda p: Vector((float(p[0]), float(p[1]), float(p[2])))
ROOT = VV(J["root"])

SHOTS = (1, 3)         # game.gd: the beams leave the emitter (the aim held at frame 1)
SHOT = SHOTS[0]
FR = 18                # the Attack's length (0.75 s at 24 fps)
TAPS = (16, 20, 24, 28)  # Orbital Laser: her right fist taps the deck
SIGNAL = 38            # ... her left fist flung up at the sky: the uplink (held to 52)
AB_FR = 70
CH_FR = 48
DEBUG = None

# ----------------------------------------------------------------------------------------------- rest-pose frames
G0, A0, U0 = VV(cm.GUN_G0), VV(cm.GUN_A0), VV(cm.GUN_U0)
S0 = A0.cross(U0)
GRIP_AX = VV(cm.grip_axis())

HAND = {}
for _s in ("R", "L"):
    _wr, _f, _n, _t = cm.hand_frame(_s)
    HAND[_s] = {"wr": VV(_wr), "f": VV(_f), "n": VV(_n), "t": VV(_t), "off": VV(cm.fist_center(_s)) - VV(_wr)}

OUT = {s: VV(cm.forearm_frame(s)[2]) for s in ("R", "L")}     # (rest) the back of each forearm
_dc, _dn, _da, _dt = cm.deck_frame()
DECK_C, DECK_N = VV(_dc), VV(_dn)                             # (rest) the deck's screen and its normal
_gd, _ad, _ud = cm.dock_gun()
DOCK_G, DOCK_A, DOCK_U = VV(_gd), VV(_ad), VV(_ud)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def seg(f, a, b):
    return smooth01((f - a) / float(b - a))


def gun_T(G, A, U):
    """The pistol's rigid motion that puts its grip's middle at G, its emitter along A, its top toward U."""
    R = frame_map(A0, Vector(A).normalized(), U0, Vector(U))
    return Matrix.Translation(Vector(G)) @ R.to_4x4() @ Matrix.Translation(-G0)


def mix_T(T0, T1, k, pivot):
    q = T0.to_quaternion().slerp(T1.to_quaternion(), k)
    p = (T0 @ pivot).lerp(T1 @ pivot, k)
    R = q.to_matrix()
    return Matrix.Translation(p - R @ pivot) @ R.to_4x4()


def path_T(f, keys, pivot):
    if f <= keys[0][0]:
        return keys[0][1]
    for (fa, Ta), (fb, Tb) in zip(keys, keys[1:]):
        if f <= fb:
            return mix_T(Ta, Tb, seg(f, fa, fb), pivot)
    return keys[-1][1]


def via(a, m, b, u):
    """From a through m to b (u 0..1): two eased legs, so a hand goes round (not through) her body."""
    if u <= 0.5:
        return Vector(a).lerp(Vector(m), smooth01(u * 2.0))
    return Vector(m).lerp(Vector(b), smooth01(u * 2.0 - 1.0))


def up_perp(A, ref=V(0, 0, 1)):
    A = Vector(A).normalized()
    u = Vector(ref) - A * Vector(ref).dot(A)
    return u.normalized()


# ----------------------------------------------------------------------------------------------- body
def legs(arm, yaw, lf=(0.18, -0.02), rf=(-0.18, 0.06), lift_l=0.0, lift_r=0.0, open_feet=0.6, turn_l=6.0, turn_r=-10.0):
    q = rz(yaw)
    aims = {}
    for side, (bx, by), lift, tw in (("L", lf, lift_l, turn_l), ("R", rf, lift_r, turn_r)):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + lift)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = VV(J["toe_" + side]) - VV(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * open_feet + tw) @ rest_foot
    return aims


def torso(aims, yaw_chest, lean=0.0, side=0.0, spine_tw=0.0, chest_tw=0.0, neck_tw=0.0, head_tw=0.0, head_tilt=0.0,
          head_up=0.0, neck_side=0.0):
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.22 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.32 * lean, 1.0), chest_tw)
    aims["neck"] = (V(neck_side, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


def grip(side, fist, along, fdir):
    H = HAND[side]
    t = Vector(along).normalized()
    f = Vector(fdir) - t * Vector(fdir).dot(t)
    if f.length < 1e-6:
        f = t.orthogonal()
    f.normalize()
    n = t.cross(f) if side == "R" else f.cross(t)
    R = frame_map(H["t"], t, H["n"], n)
    return Vector(fist) - R @ H["off"], ("frame", H["t"], t, H["n"], n), n


ROLL = {"R": 0.5, "L": 0.3}      # how much of the hand's roll its forearm takes


def rolled(fore, side, n_hand):
    """The forearm's aim, turned about its own length so that its back faces (ROLL of the way) where the back of the
    hand faces (-n_hand): the deck on her left forearm turns with her hand."""
    def fn(P, base):
        d = Vector(fore(P, base)).normalized()
        y0 = base.col[1].xyz.normalized()
        R0 = y0.rotation_difference(d).to_matrix() @ base.to_3x3()
        cur = R0 @ (_REST_INV[side] @ OUT[side])
        want = -Vector(n_hand)
        cur = (cur - d * cur.dot(d)).normalized()
        want = (want - d * want.dot(d))
        if want.length < 1e-6:
            return d
        want.normalize()
        ang = math.atan2(cur.cross(want).dot(d), cur.dot(want))
        if TWISTS is not None:
            TWISTS.append((side, math.degrees(ang)))
        return (d, ang * ROLL[side])
    return fn


_REST_INV = {}
_HINGE = {}


def _rest_hinge(arm, side):
    """The elbow's hinge axis at rest (the A-pose's slight bend), in the upper arm's own frame."""
    if side not in _HINGE:
        b = arm.data.bones
        u = (b["upperarm." + side].tail_local - b["upperarm." + side].head_local).normalized()
        f = (b["forearm." + side].tail_local - b["forearm." + side].head_local).normalized()
        _HINGE[side] = b["upperarm." + side].matrix_local.to_3x3().inverted() @ u.cross(f).normalized()
    return _HINGE[side]


def hinged_arm(arm, side, wrist, pole):
    """arm_aims (rig.py), but the upper arm is turned about its length so that the elbow's hinge lies across the plane
    of the bend (set by the pole): its roll never flips, however far the arm is raised (the plain shortest turn from the
    A-pose flips over when the arm goes up over her head)."""
    la, lb = bone_len(arm, "upperarm." + side), bone_len(arm, "forearm." + side)
    st = {}
    hr = _rest_hinge(arm, side)
    def upper(P, base):
        sh = base.translation
        el = two_bone(sh, wrist, la, lb, pole)
        st["el"] = el
        d = (el - sh).normalized()
        u = (Vector(wrist) - sh).normalized()
        pv = Vector(pole) - u * Vector(pole).dot(u)
        want = d.cross(-pv)
        if want.length < 1e-6:
            return d
        want.normalize()
        y0 = base.col[1].xyz.normalized()
        R0 = y0.rotation_difference(d).to_matrix() @ base.to_3x3()
        cur = R0 @ hr
        cur = (cur - d * cur.dot(d)).normalized()
        want = (want - d * want.dot(d)).normalized()
        return (d, math.atan2(cur.cross(want).dot(d), cur.dot(want)))
    def fore(P, base):
        return Vector(wrist) - st["el"]
    return {"upperarm." + side: upper, "forearm." + side: fore}
TWISTS = None


def hands_aims(arm, P, holds):
    aims = {}
    for side, (fist, along, pole) in holds.items():
        if side not in _REST_INV:
            _REST_INV[side] = arm.data.bones["forearm." + side].matrix_local.to_3x3().inverted()
        sh = P["upperarm." + side].translation.copy()
        la, lb = bone_len(arm, "upperarm." + side), bone_len(arm, "forearm." + side)
        fdir = Vector(fist) - sh
        wrist, fr, n = grip(side, fist, along, fdir)
        for it in range(3):
            el = two_bone(sh, wrist, la, lb, pole)
            wrist, fr, n = grip(side, fist, along, Vector(fist) - el)
        a = hinged_arm(arm, side, wrist, pole)
        a["forearm." + side] = rolled(a["forearm." + side], side, n)
        aims.update(a)
        aims["hand." + side] = fr
    return aims


def solve(P_, arm, aims, ro, rr, holds, props, scales=None, first=None):
    """Solve the body, put the fists on their holds (callables of the solved pose), then the props on top. `first`:
    sides whose holds are solved before the others' (the right fist taps the deck on the left forearm)."""
    ch, P = P_.solve(aims, ro, rr, scales=scales)
    if first:
        hs1 = {s: holds[s](P) for s in first}
        a1 = dict(aims)
        a1.update(hands_aims(arm, P, hs1))
        ch, P = P_.solve(a1, ro, rr, scales=scales)
    hs = {side: fn(P) for side, fn in holds.items()}
    if DEBUG is not None:
        DEBUG.append({side: Vector(h[0]) for side, h in hs.items()})
    aims = dict(aims)
    aims.update(hands_aims(arm, P, hs))
    aims.update(props)
    return P_.solve(aims, ro, rr, scales=scales)


def on_gun(T, pole):
    """Her right fist round the pistol's grip."""
    R = T.to_3x3()
    return lambda P: (T @ G0, R @ GRIP_AX, pole)


def fist_at(p, along, pole):
    return lambda P: (Vector(p), Vector(along), pole)


def root_delta(P_, P):
    return P["root"] @ P_.rest["root"].inverted()


def body_point(Dr, p):
    return Dr @ Vector(p)


def props(P_, T_g):
    return {"laser": lambda P, b: ("world", T_g @ P_.rest["laser"])}


def deck_now(P_, P):
    """Where the deck's screen is and which way it faces, in pose P."""
    M = P["forearm.L"] @ P_.rest["forearm.L"].inverted()
    return M @ DECK_C, (M.to_3x3() @ DECK_N).normalized()


def dock_T(P_, P):
    """The pistol docked on her right thigh (following the thigh)."""
    M = P["thigh.R"] @ P_.rest["thigh.R"].inverted()
    return M @ gun_T(DOCK_G, DOCK_A, DOCK_U)


# ----------------------------------------------------------------------------------------------- the aim
YAW = 48.0                          # turned side-on: her right shoulder toward the robots
REACH = 0.6                         # the shoulder to the grip
AIM_DOWN = 0.04
R_POLE = V(-0.25, 0.7, -1.0)        # her right elbow down and back
L_POLE = V(1.0, 0.25, -0.55)        # her left elbow out and down
DECK_FIST = V(-0.05, -0.33, 1.12)   # (body frame) her left fist before her, the forearm across her front ...
DECK_ALONG = V(0.0, 0.0, 1.0)       # ... thumb up: the forearm's thumb side (the deck) turned up
HIP_L = V(0.262, 0.0, 0.925)
HIP_R = V(-0.262, 0.0, 0.925)


def aim_body(arm, br=0.0, sway=0.0, push=0.0, yaw=YAW, head_up=0.0, lean=0.0, crouch=0.0):
    aims = legs(arm, yaw, lf=(0.17, 0.11), rf=(-0.15, -0.13), turn_l=34.0, turn_r=-0.6 * yaw, open_feet=0.6)
    yc = yaw + 4.0 - 3.0 * push
    ro = rz(yaw) @ V(0.0, 0.01 * push, 0.0) + V(0.0, 0.0, -0.045 - 0.03 * crouch + 0.004 * br)
    rr = rz(yaw + 0.8 * sway)
    torso(aims, yc, lean=0.06 + lean - 0.05 * push, side=0.03, spine_tw=math.radians(2), chest_tw=math.radians(4),
          neck_tw=math.radians(-0.45 * yc), head_tw=math.radians(-0.52 * yc), head_tilt=0.08, head_up=-0.08 + head_up,
          neck_side=-0.04)
    aims["clavicle.R"] = rz(yc) @ V(-1.0, -0.22, 0.12)
    aims["clavicle.L"] = rz(yc) @ V(1.0, -0.15, 0.02)
    return aims, ro, rr


def aim_T(P, kick=0.0, back=0.0, sway=0.0, br=0.0):
    """The pistol on the aim: the grip at arm's length before her right shoulder, the emitter level toward the robots
    (-y), dipping a little; `kick` (radians) turns the emitter up about the grip, `back` draws the fist back."""
    sh = P["upperarm.R"].translation
    A = V(0.012 * sway, -math.cos(AIM_DOWN), -math.sin(AIM_DOWN) + 0.004 * br).normalized()
    G = sh + A * (REACH - back) + V(0.0, 0.0, -0.035 + 0.25 * back)
    if kick:
        A = Quaternion(A.cross(V(0, 0, 1)).normalized(), kick) @ A
    return gun_T(G, A, up_perp(A))


def deck_hold(Dr, br=0.0, k=0.0, fist=DECK_FIST, along=DECK_ALONG):
    R = Dr.to_3x3()
    return fist_at(body_point(Dr, fist + V(0, 0, 0.004 * br + 0.01 * k)), R @ along, R @ L_POLE)


def combat_pose(arm, P_, t, kick=0.0, back=0.0, push=0.0):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    body, ro, rr = aim_body(arm, br, sw, push=push)
    _c, P0 = P_.solve(body, ro, rr)
    Dr = root_delta(P_, P0)
    T_g = aim_T(P0, kick, back, sw, br)
    holds = {"R": on_gun(T_g, R_POLE), "L": deck_hold(Dr, br)}
    return solve(P_, arm, body, ro, rr, holds, props(P_, T_g))


def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        ch, _ = combat_pose(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def recoil(f):
    """(kick 0..1, back) of the double tap: the first shot with the aim held (frame 1), the kick, the second shot (frame 3)
    from a little above the line, the bigger kick, settled back on the aim by frame 14."""
    if f <= SHOTS[0]:
        k = 0.0
    elif f <= 2:
        k = 0.55 * (f - SHOTS[0])
    elif f <= SHOTS[1]:
        k = 0.55 - 0.3 * (f - 2)
    elif f <= 5:
        k = 0.25 + 0.75 * smooth01((f - SHOTS[1]) / 2.0)
    else:
        k = 1.0 - smooth01((f - 5) / 9.0)
    return k, 0.035 * k


def make_attack(arm, frames=FR):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        k, back = recoil(f)
        ch, _ = combat_pose(arm, P_, 0.0, kick=0.17 * k, back=back, push=k)
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- idle: the pistol up
UP_G = V(-0.27, -0.25, 1.37)                  # (body frame) the grip before her right shoulder ...
UP_A = V(-0.12, -0.08, 1.0).normalized()       # ... the emitter to the sky
UP_U = V(0.05, 1.0, 0.1)                       # ... its top toward her


def up_T(Dr, G=UP_G, A=UP_A, U=UP_U, lift=0.0):
    R = Dr.to_3x3()
    A_ = (R @ A).normalized()
    return gun_T(body_point(Dr, G + V(0, 0, lift)), A_, up_perp(A_, R @ U))


def idle_pose(arm, P_, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    hip = math.sin(w)
    yaw = 8.0 + 3.0 * math.sin(w)
    aims = legs(arm, yaw, lf=(0.18 + 0.012 * hip, -0.02), rf=(-0.18 + 0.012 * hip, 0.04), open_feet=0.5, turn_l=12.0, turn_r=-14.0)
    ro = V(0.02 * hip, 0.0, -0.012 + 0.004 * br - 0.006 * abs(hip))
    rr = rz(yaw) @ Quaternion(V(0, 1, 0), math.radians(2.5 * hip))
    glance = smooth01((t - 0.55) / 0.07) * (1.0 - smooth01((t - 0.8) / 0.07))       # a look at her deck
    look = (0.4 * math.sin(w + 0.4) + 0.12 * math.sin(w * 3)) * (1.0 - glance) - 0.1
    torso(aims, yaw, lean=-0.02, side=-0.05 * hip, spine_tw=0.03 * math.sin(w), chest_tw=0.04 * math.sin(w),
          neck_tw=0.3 * look - 0.1 * glance, head_tw=0.62 * look - 0.25 * glance, head_tilt=0.06 + 0.04 * hip,
          head_up=0.1 + 0.03 * br - 0.42 * glance)
    q = rz(yaw)
    aims["clavicle.L"] = q @ V(1.0, -0.05 * glance, -0.03 + 0.06 * glance)
    aims["clavicle.R"] = q @ V(-1.0, -0.06, 0.08)
    ch, P = P_.solve(aims, ro, rr)
    Dr = root_delta(P_, P)
    T_g = up_T(Dr, lift=0.004 * br)
    R = Dr.to_3x3()
    hipL = fist_at(body_point(Dr, HIP_L), R @ V(0.0, -1.0, 0.5), R @ V(1.0, 0.6, -0.3))
    hold_l = hipL
    if glance > 0.0:
        a = hipL(P)
        d = deck_hold(Dr, 0.0, 0.0, fist=V(0.02, -0.32, 1.17), along=V(0.0, 0.25, 1.0))(P)
        hold_l = fist_at(a[0].lerp(d[0], glance), a[1].slerp(d[1], glance), a[2].lerp(d[2], glance))
    holds = {"R": on_gun(T_g, R @ V(-0.6, 0.3, -1.0)), "L": hold_l}
    return solve(P_, arm, aims, ro, rr, holds, props(P_, T_g))


def make_idle(arm, frames=120):
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        ch, _ = idle_pose(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- Orbital Laser
READ_FIST = V(0.0, -0.3, 1.2)              # (body frame) the left fist while she types: the deck before her chest
READ_ALONG = V(0.0, 0.0, 1.0)              # (the deck turned up toward her face)
SKY_FIST = V(0.3, -0.12, 2.16)             # (body frame) the uplink: her left fist flung up at the sky ...
SKY_ALONG = V(-0.7, -0.7, 0.0)             # ... the deck toward the front
SKY_POLE = V(0.3, 1.0, 0.0)                # (her elbow back)


def make_ability(arm, frames=AB_FR):
    """Turn to the front and dock the pistol (0-10), the deck up (4-12), four taps (14-30), the uplink (30-38, SIGNAL held
    to 52), the arm down and the pistol drawn (52-62), back on the aim (62-70)."""
    P_ = Poser(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        front = seg(f, 0, 9) * (1.0 - seg(f, 56, 66))
        yaw = YAW + (6.0 - YAW) * front
        up = seg(f, 30, SIGNAL) * (1.0 - seg(f, 52, 58))
        read = seg(f, 6, 13) * (1.0 - seg(f, 29, 34))
        body, ro, rr = aim_body(arm, 0.0, 0.0, yaw=yaw, head_up=-0.5 * read + 0.62 * up, lean=0.06 * read - 0.12 * up,
                                crouch=0.2 * read - 0.3 * up)
        # look down at the deck (her head turned to it) while she types, up at the sky at the uplink
        yc = yaw + 4.0
        body["neck"] = (body["neck"][0], math.radians(-0.45 * yc * (1.0 - front) + 4.0 * read))
        body["head"] = (body["head"][0], math.radians(-0.52 * yc * (1.0 - front) + 8.0 * read - 6.0 * up))
        body["clavicle.L"] = rz(yc) @ V(1.0, -0.12, 0.02 + 0.3 * up)
        _c, P0 = P_.solve(body, ro, rr)
        Dr = root_delta(P_, P0)
        R = Dr.to_3x3()
        # the pistol: from the aim down onto its dock (0-10), docked, drawn (54-62) and back on the aim (62-70)
        T_aim = aim_T(P0)
        T_dock = dock_T(P_, P0)
        if f <= 10:
            mid = gun_T(body_point(Dr, V(-0.3, -0.36, 1.02)), R @ V(-0.1, -0.3, -1.0), R @ V(0.0, -1.0, 0.2))
            T_g = path_T(f, [(0, T_aim), (5, mid), (10, T_dock)], G0)
        elif f < 54:
            T_g = T_dock
        else:
            mid = gun_T(body_point(Dr, V(-0.3, -0.36, 1.06)), R @ V(-0.1, -0.6, -0.6), R @ V(0.0, -0.8, 0.5))
            T_g = path_T(f, [(54, T_dock), (58, mid), (64, T_aim)], G0)
        # the left hand: the deck up before her, the uplink, back to the combat hold
        dk = deck_hold(Dr)(P0)
        rd = deck_hold(Dr, fist=READ_FIST, along=READ_ALONG)(P0)
        sky = (body_point(Dr, SKY_FIST + V(0, 0, 0.012 * math.sin((f - SIGNAL) * 1.1) * max(0.0, 1.0 - (f - SIGNAL) / 12.0) if f >= SIGNAL else 0.0)),
               R @ SKY_ALONG, R @ SKY_POLE)
        if f <= 13:
            u = seg(f, 4, 12)
            hold_l = fist_at(dk[0].lerp(rd[0], u), dk[1].slerp(rd[1], u), dk[2].lerp(rd[2], u))
        elif f <= 30:
            hold_l = fist_at(*rd)
        elif f <= SIGNAL:
            u = seg(f, 30, SIGNAL)
            mid = body_point(Dr, V(0.36, -0.36, 1.6))
            hold_l = fist_at(via(rd[0], mid, sky[0], u), rd[1].slerp(sky[1], u), rd[2].lerp(sky[2], u))
        elif f <= 52:
            hold_l = fist_at(*sky)
        else:
            u = seg(f, 52, 62)
            mid = body_point(Dr, V(0.38, -0.36, 1.5))
            hold_l = fist_at(via(sky[0], mid, dk[0], u), sky[1].slerp(dk[1], u), sky[2].lerp(dk[2], u))
        # the right hand: on the grip, taps, on her hip at the uplink, back to the dock and draws
        hipR = (body_point(Dr, HIP_R), R @ V(0.0, -1.0, 0.5), R @ V(-1.0, 0.6, -0.3))
        r_pole = R @ V(-1.0, 0.1, -0.6)
        def tap_hold(P, f=f):
            c, n = deck_now(P_, P)
            k = 0.0
            for tf in TAPS:
                k = max(k, 1.0 - min(1.0, abs(f - tf) / 2.0))
            side = (R @ V(-1.0, 0.0, 0.0))
            jit = side * (0.02 * math.sin(f * 1.7))
            fist = c + n * (0.075 - 0.032 * k) + jit
            return fist, (R @ V(0.0, -0.2, 1.0)), r_pole
        if f <= 10:
            hold_r = on_gun(T_g, R_POLE.lerp(R @ V(-1.0, 0.4, -0.6), seg(f, 0, 10)))
        elif f <= 14:
            g = on_gun(T_g, R @ V(-1.0, 0.4, -0.6))
            u = seg(f, 10, 14)
            def hold_r(P, g=g, u=u):
                a, b = g(P), tap_hold(P)
                return a[0].lerp(b[0], u) + V(0, 0, 0.05 * math.sin(math.pi * u)), a[1].slerp(b[1], u), a[2].lerp(b[2], u)
        elif f <= 30:
            hold_r = tap_hold
        elif f <= 36:
            u = seg(f, 30, 36)
            def hold_r(P, u=u):
                a = tap_hold(P)
                return a[0].lerp(hipR[0], u), a[1].slerp(hipR[1], u), a[2].lerp(hipR[2], u)
        elif f <= 50:
            hold_r = fist_at(*hipR)
        elif f <= 54:
            u = seg(f, 50, 54)
            g = on_gun(T_g, R @ V(-1.0, 0.4, -0.6))
            def hold_r(P, g=g, u=u):
                b = g(P)
                return hipR[0].lerp(b[0], u), hipR[1].slerp(b[1], u), hipR[2].lerp(b[2], u)
        else:
            hold_r = on_gun(T_g, (R @ V(-1.0, 0.4, -0.6)).lerp(R_POLE, seg(f, 56, 66)))
        holds = {"R": hold_r, "L": hold_l}
        first = ("L",) if 10 < f <= 36 else None
        ch, P = solve(P_, arm, body, ro, rr, holds, props(P_, T_g), first=first)
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- Cheer
HIGH_G = V(-0.34, -0.1, 1.96)                  # (body frame) the pistol thrust up high: its grip ...
HIGH_A = V(-0.1, -0.12, 1.0).normalized()
CH_ALONG = V(-0.7, 0.7, 0.0)                  # her left fist pumping overhead (its thumb back, toward her)
CH_POLE = V(1.0, 0.0, -0.3)
CH_RPOLE = V(-0.3, -1.0, 0.0)                 # (her right elbow forward under the raised pistol)


def make_cheer(arm, frames=CH_FR):
    """The pistol thrust up high (0-10), a hop with a whoop and two pumps of her left fist (10-34), back down onto the
    aim (34-46)."""
    P_ = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        front = seg(f, 0, 9) * (1.0 - seg(f, 34, 45))
        yaw = YAW + (4.0 - YAW) * front
        up = seg(f, 0, 10) * (1.0 - seg(f, 33, 44))
        pump = max(0.0, math.sin(math.pi * (f - 12) / 9.0)) if 12 <= f <= 30 else 0.0
        hop = max(0.0, math.sin(math.pi * (f - 13) / 7.0)) * 0.05 if 13 <= f <= 20 else 0.0
        whoop = math.sin(math.pi * min(1.0, max(0.0, (f - 9) / 16.0)))
        body, ro, rr = aim_body(arm, 0.0, 0.0, yaw=yaw, head_up=0.3 * up + 0.36 * whoop, lean=-0.1 * up - 0.06 * whoop,
                                crouch=-0.3 * up)
        yc = yaw + 4.0
        body["neck"] = (body["neck"][0], math.radians(-0.45 * yc * (1.0 - front)))
        body["head"] = (body["head"][0], math.radians(-0.52 * yc * (1.0 - front)))
        body["clavicle.R"] = rz(yc) @ V(-1.0, -0.1 * (1 - up), 0.12 + 0.25 * up)
        body["clavicle.L"] = rz(yc) @ V(1.0, -0.1, 0.25 * up)
        ro = ro + V(0.0, 0.0, hop)
        _c, P0 = P_.solve(body, ro, rr)
        Dr = root_delta(P_, P0)
        R = Dr.to_3x3()
        T_aim = aim_T(P0)
        T_hi = up_T(Dr, HIGH_G + V(0, 0, 0.03 * pump), HIGH_A)
        T_mid = up_T(Dr)
        T_g = path_T(f, [(0, T_aim), (5, T_mid), (10, T_hi)], G0) if f <= 20 else path_T(f, [(33, T_hi), (39, T_mid), (45, T_aim)], G0)
        dk = deck_hold(Dr)(P0)
        fist_lo = body_point(Dr, V(0.42, -0.2, 1.86))
        fist_hi = body_point(Dr, V(0.5, -0.22, 2.14))
        mid = body_point(Dr, V(0.4, -0.4, 1.4))
        al = R @ CH_ALONG
        top = fist_lo.lerp(fist_hi, pump)
        pole_up = R @ CH_POLE
        if f <= 10:
            u = seg(f, 0, 10)
            pos, a_, pole = via(dk[0], mid, top, u), dk[1].slerp(al, u), dk[2].lerp(pole_up, u)
        elif f < 34:
            pos, a_, pole = top, al, pole_up
        else:
            u = seg(f, 34, 45)
            pos, a_, pole = via(top, mid, dk[0], u), al.slerp(dk[1], u), pole_up.lerp(dk[2], u)
        holds = {"R": on_gun(T_g, (R @ CH_RPOLE).lerp(R_POLE, 1.0 - up)), "L": fist_at(pos, a_, pole)}
        ch, P = solve(P_, arm, body, ro, rr, holds, props(P_, T_g))
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
