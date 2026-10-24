"""Commander Vega's clips (keyed frame by frame; the .glb runs them at 24 fps, game.gd CLIP_FPS).

Idle    : (120) the pistol held up beside his right shoulder, its muzzle to the sky (his right fist at his shoulder, the
          elbow down), his left fist on his hip; he stands tall, shifts his weight and looks over his troops; once round
          the loop he swings his left fist forward and out before him ("move up!") and brings it back to his hip.
Combat  : (40) the one-handed aim: turned side-on, his right shoulder (the robot pauldron) toward the robots (right foot
          forward), his right arm out with the pistol level toward them (-y); his left fist on his hip; a slow sway.
Attack  : (FR = 18 frames, inside the 0.8 s cooldown) one heavy shot: the aim held to SHOT (frame 2: game.gd's plasma
          shot leaves the muzzle), the big kick (the muzzle thrown up, his fist driven back, his shoulders rocked) and
          the recoil settling; he is back on the aim (= Combat) by frame 15.
Ability : Killswitch (AB_FR = 68): he squares up to the front and lowers the pistol to his side (0-8), reaches back to his
          left hip and draws the killswitch (GRAB, frame 12), raises it high over his head, the button up (12-24), thumbs
          it (PRESS, frame 27: the button swells and burns), and slams it down before him in a deep crouch (28-34):
          SIGNAL (frame 34, held to 42: game.gd's pulse goes out round him; VEGA_SWITCH is the button, `switch` bone);
          he rises, hangs the killswitch back on his hip (44-58) and is back on the aim (58-68).
Cheer   : (CH_FR = 48) the rally: he punches his left fist up high and pumps it twice (a hop), the pistol raised beside
          his shoulder, his head up; then back down onto the aim.

Props are posed in world space: the pistol (parentless) by the rigid motion of its rest placement, his right fist put on
its grip by IK (the fist's length kept in line with the forearm, as Nova's); the killswitch (parentless) follows his hips
in its holder and his left fist once drawn, the rod through the fist along its thumb axis; the button (a child of the
killswitch) swells when pressed."""
import math
from mathutils import Vector, Quaternion, Matrix
import vega as cm
from rig import Poser, leg_aims, arm_aims, frame_map, bone_len, two_bone
from anim import new_action, finish_action

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
VV = lambda p: Vector((float(p[0]), float(p[1]), float(p[2])))
ROOT = VV(J["root"])

SHOT = 2               # game.gd: the plasma shot leaves the muzzle (the aim held to frame 2)
FR = 18                # the Attack's length (0.75 s at 24 fps)
GRAB = 12              # Killswitch: drawn from his hip
PRESS = 27             # ... thumbed overhead (the button swells)
SIGNAL = 34            # ... slammed down: the pulse (held to 42)
AB_FR = 68
CH_FR = 48
DEBUG = None

# ----------------------------------------------------------------------------------------------- rest-pose frames
G0, A0, U0 = VV(cm.GUN_G0), VV(cm.GUN_A0), VV(cm.GUN_U0)
GRIP_AX = VV(cm.grip_axis())
_sg, _sa, _su = cm.switch_rest()
SG0, SA0, SU0 = VV(_sg), VV(_sa), VV(_su)                     # (rest) the killswitch in its holder

HAND = {}
for _s in ("R", "L"):
    _wr, _f, _n, _t = cm.hand_frame(_s)
    HAND[_s] = {"wr": VV(_wr), "f": VV(_f), "n": VV(_n), "t": VV(_t), "off": VV(cm.fist_center(_s)) - VV(_wr)}

OUT = {s: VV(cm.forearm_frame(s)[2]) for s in ("R", "L")}     # (rest) the back of each forearm


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def seg(f, a, b):
    return smooth01((f - a) / float(b - a))


def rigid_T(G, A, U, g0, a0, u0):
    R = frame_map(a0, Vector(A).normalized(), u0, Vector(U))
    return Matrix.Translation(Vector(G)) @ R.to_4x4() @ Matrix.Translation(-g0)


def gun_T(G, A, U):
    """The pistol's rigid motion that puts its grip's middle at G, its muzzle along A, its top toward U."""
    return rigid_T(G, A, U, G0, A0, U0)


def sw_T(G, A, U):
    """The killswitch's rigid motion that puts its grip's middle at G, its button along A, its guard's side toward U."""
    return rigid_T(G, A, U, SG0, SA0, SU0)


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
    """From a through m to b (u 0..1): two eased legs, so a hand goes round (not through) his body."""
    if u <= 0.5:
        return Vector(a).lerp(Vector(m), smooth01(u * 2.0))
    return Vector(m).lerp(Vector(b), smooth01(u * 2.0 - 1.0))


def up_perp(A, ref=V(0, 0, 1)):
    A = Vector(A).normalized()
    u = Vector(ref) - A * Vector(ref).dot(A)
    if u.length < 1e-6:
        u = A.orthogonal()
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


ROLL = {"R": 0.5, "L": 0.4}      # how much of the hand's roll its forearm takes


def rolled(fore, side, n_hand):
    """The forearm's aim, turned about its own length so that its back faces (ROLL of the way) where the back of the
    hand faces (-n_hand): the wrist only bends, it does not wring."""
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
        return (d, ang * ROLL[side])
    return fn


_REST_INV = {}
_HINGE = {}


def _rest_hinge(arm, side):
    if side not in _HINGE:
        b = arm.data.bones
        u = (b["upperarm." + side].tail_local - b["upperarm." + side].head_local).normalized()
        f = (b["forearm." + side].tail_local - b["forearm." + side].head_local).normalized()
        _HINGE[side] = b["upperarm." + side].matrix_local.to_3x3().inverted() @ u.cross(f).normalized()
    return _HINGE[side]


def hinged_arm(arm, side, wrist, pole):
    """arm_aims (rig.py), but the upper arm is turned about its length so that the elbow's hinge lies across the plane
    of the bend (set by the pole): its roll never flips, however far the arm is raised."""
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


def solve(P_, arm, aims, ro, rr, holds, props, scales=None):
    """Solve the body, put the fists on their holds (callables of the solved pose), then the props on top."""
    ch, P = P_.solve(aims, ro, rr, scales=scales)
    hs = {side: fn(P) for side, fn in holds.items()}
    if DEBUG is not None:
        DEBUG.append({side: Vector(h[0]) for side, h in hs.items()})
    aims = dict(aims)
    aims.update(hands_aims(arm, P, hs))
    aims.update(props)
    return P_.solve(aims, ro, rr, scales=scales)


def on_gun(T, pole):
    """His right fist round the pistol's grip."""
    R = T.to_3x3()
    return lambda P: (T @ G0, R @ GRIP_AX, pole)


def on_switch(T, pole):
    """His left fist round the killswitch's grip (the rod along the fist's thumb axis, the button up past his thumb)."""
    R = T.to_3x3()
    return lambda P: (T @ SG0, R @ SA0, pole)


def fist_at(p, along, pole):
    return lambda P: (Vector(p), Vector(along), pole)


def root_delta(P_, P):
    return P["root"] @ P_.rest["root"].inverted()


def body_point(Dr, p):
    return Dr @ Vector(p)


def holstered_T(P_, P):
    """The killswitch in its holder on his left hip (following his hips)."""
    return root_delta(P_, P)


def props(P_, T_g, T_s=None, press=0.0):
    out = {"pistol": lambda P, b: ("world", T_g @ P_.rest["pistol"])}
    if T_s is not None:
        out["switch"] = lambda P, b: ("world", T_s @ P_.rest["switch"])
    return out


def scales_for(press):
    s = 1.0 + 0.7 * press
    return {"button": (s, s, s)}


# ----------------------------------------------------------------------------------------------- the aim
YAW = 46.0                          # turned side-on: his right shoulder toward the robots
REACH = 0.66                        # the shoulder to the grip
AIM_DOWN = 0.04
R_POLE = V(-0.25, 0.7, -1.0)        # his right elbow down and back
HIP_L = V(0.3, -0.035, 0.975)       # (body frame) his left fist on his hip (in front of the killswitch's holder)
HIP_ALONG = V(0.0, -1.0, 0.45)
HIP_POLE = V(1.0, 0.7, -0.2)


def aim_body(arm, br=0.0, sway=0.0, push=0.0, yaw=YAW, head_up=0.0, lean=0.0, crouch=0.0):
    aims = legs(arm, yaw, lf=(0.17, 0.12), rf=(-0.15, -0.13), turn_l=34.0, turn_r=-0.6 * yaw, open_feet=0.6)
    yc = yaw + 4.0 - 4.0 * push
    ro = rz(yaw) @ V(0.0, 0.012 * push, 0.0) + V(0.0, 0.0, -0.04 - 0.03 * crouch + 0.004 * br)
    rr = rz(yaw + 0.8 * sway)
    torso(aims, yc, lean=0.04 + lean - 0.06 * push, side=0.03, spine_tw=math.radians(2), chest_tw=math.radians(4),
          neck_tw=math.radians(-0.45 * yc), head_tw=math.radians(-0.52 * yc), head_tilt=0.06, head_up=-0.06 + head_up,
          neck_side=-0.04)
    aims["clavicle.R"] = rz(yc) @ V(-1.0, -0.22, 0.12 + 0.05 * push)
    aims["clavicle.L"] = rz(yc) @ V(1.0, -0.1, 0.0)
    return aims, ro, rr


def aim_T(P, kick=0.0, back=0.0, sway=0.0, br=0.0):
    """The pistol on the aim: the grip at arm's length before his right shoulder, the muzzle level toward the robots
    (-y), dipping a little; `kick` (radians) turns the muzzle up about the grip, `back` draws the fist back."""
    sh = P["upperarm.R"].translation
    A = V(0.012 * sway, -math.cos(AIM_DOWN), -math.sin(AIM_DOWN) + 0.004 * br).normalized()
    G = sh + A * (REACH - back) + V(0.0, 0.0, -0.04 + 0.3 * back)
    if kick:
        A = Quaternion(A.cross(V(0, 0, 1)).normalized(), kick) @ A
    return gun_T(G, A, up_perp(A))


def hip_hold(Dr, br=0.0):
    R = Dr.to_3x3()
    return fist_at(body_point(Dr, HIP_L + V(0, 0, 0.004 * br)), R @ HIP_ALONG, R @ HIP_POLE)


def combat_pose(arm, P_, t, kick=0.0, back=0.0, push=0.0):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    body, ro, rr = aim_body(arm, br, sw, push=push)
    _c, P0 = P_.solve(body, ro, rr)
    Dr = root_delta(P_, P0)
    T_g = aim_T(P0, kick, back, sw, br)
    holds = {"R": on_gun(T_g, R_POLE), "L": hip_hold(Dr, br)}
    return solve(P_, arm, body, ro, rr, holds, props(P_, T_g, holstered_T(P_, P0)), scales=scales_for(0.0))


def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        ch, _ = combat_pose(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def recoil(f):
    """(kick 0..1) of the shot: the aim held to SHOT (frame 2), the big kick (frames 2-5), settled back on the aim by
    frame 15."""
    if f <= SHOT:
        return 0.0
    if f <= SHOT + 3:
        return smooth01((f - SHOT) / 3.0) * 0.6 + 0.4 * min(1.0, (f - SHOT) / 1.0)
    return 1.0 - smooth01((f - SHOT - 3) / 10.0)


def make_attack(arm, frames=FR):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        k = recoil(f)
        ch, _ = combat_pose(arm, P_, 0.0, kick=0.42 * k, back=0.07 * k, push=k)
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- idle: the pistol up
UP_G = V(-0.3, -0.27, 1.43)                    # (body frame) the grip before his right shoulder ...
UP_A = V(-0.12, -0.1, 1.0).normalized()        # ... the muzzle to the sky
UP_U = V(0.05, 1.0, 0.1)                       # ... its top toward him
UP_POLE = V(-0.6, 0.3, -1.0)


def up_T(Dr, G=UP_G, A=UP_A, U=UP_U, lift=0.0):
    R = Dr.to_3x3()
    A_ = (R @ A).normalized()
    return gun_T(body_point(Dr, G + V(0, 0, lift)), A_, up_perp(A_, R @ U))


WAVE_FIST = V(0.34, -0.62, 1.32)               # (body frame) "move up!": his left fist swung forward and out
WAVE_ALONG = V(0.1, -0.2, 1.0)
WAVE_POLE = V(1.0, 0.0, -0.6)


def idle_pose(arm, P_, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    hip = math.sin(w)
    yaw = 8.0 + 3.0 * math.sin(w)
    wave = smooth01((t - 0.55) / 0.06) * (1.0 - smooth01((t - 0.74) / 0.08))
    aims = legs(arm, yaw, lf=(0.19 + 0.012 * hip, -0.02), rf=(-0.18 + 0.012 * hip, 0.04), open_feet=0.5, turn_l=12.0, turn_r=-14.0)
    ro = V(0.02 * hip, -0.01 * wave, -0.012 + 0.004 * br - 0.006 * abs(hip))
    rr = rz(yaw - 8.0 * wave) @ Quaternion(V(0, 1, 0), math.radians(2.5 * hip))
    look = (0.4 * math.sin(w + 0.4) + 0.12 * math.sin(w * 3)) * (1.0 - wave) - 0.1
    torso(aims, yaw - 10.0 * wave, lean=-0.03 + 0.08 * wave, side=-0.05 * hip, spine_tw=0.03 * math.sin(w), chest_tw=0.04 * math.sin(w),
          neck_tw=0.3 * look + 0.15 * wave, head_tw=0.62 * look + 0.25 * wave, head_tilt=0.04 + 0.04 * hip,
          head_up=0.1 + 0.03 * br + 0.05 * wave)
    q = rz(yaw)
    aims["clavicle.L"] = q @ V(1.0, -0.12 * wave, -0.02 + 0.1 * wave)
    aims["clavicle.R"] = q @ V(-1.0, -0.06, 0.08)
    ch, P = P_.solve(aims, ro, rr)
    Dr = root_delta(P_, P)
    T_g = up_T(Dr, lift=0.004 * br)
    R = Dr.to_3x3()
    hold_l = hip_hold(Dr, br)
    if wave > 0.0:
        a = hold_l(P)
        d = (body_point(Dr, WAVE_FIST), R @ WAVE_ALONG, R @ WAVE_POLE)
        mid = body_point(Dr, V(0.42, -0.3, 1.1))
        hold_l = fist_at(via(a[0], mid, d[0], wave) if wave < 1.0 else d[0], a[1].slerp(d[1], wave), a[2].lerp(d[2], wave))
    holds = {"R": on_gun(T_g, R @ UP_POLE), "L": hold_l}
    return solve(P_, arm, aims, ro, rr, holds, props(P_, T_g, holstered_T(P_, P)), scales=scales_for(0.0))


def make_idle(arm, frames=120):
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        ch, _ = idle_pose(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- Killswitch
LOW_G = V(-0.34, -0.1, 0.9)                 # (body frame) the pistol lowered at his right side, muzzle down and forward
LOW_A = V(-0.05, -0.45, -1.0)
LOW_U = V(0.0, -1.0, 0.3)
LOW_POLE = V(-1.0, 0.4, -0.3)
SKY_FIST = V(0.16, -0.1, 2.12)              # (body frame) the killswitch raised high over his head ...
SKY_ALONG = V(-0.1, 0.0, 1.0)               # ... the button up
SKY_POLE = V(1.0, 0.3, 0.2)
SLAM_FIST = V(0.1, -0.5, 0.66)             # ... slammed down before him (the deep crouch)
SLAM_ALONG = V(-0.05, -0.15, 1.0)
SLAM_POLE = V(1.0, 0.3, -0.3)


def make_ability(arm, frames=AB_FR):
    """Square up and lower the pistol (0-8), draw the killswitch (6-GRAB), raise it overhead (12-24), thumb it (PRESS),
    slam it down in a crouch (28-SIGNAL, held to 42), rise and hang it back on his hip (42-58), back on the aim (56-68)."""
    P_ = Poser(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        front = seg(f, 0, 8) * (1.0 - seg(f, 54, 64))
        yaw = YAW + (4.0 - YAW) * front
        up = seg(f, 14, 24) * (1.0 - seg(f, 28, 33))
        slam = seg(f, 28, SIGNAL) * (1.0 - seg(f, 44, 54))
        bounce = 0.25 * math.sin(math.pi * (f - SIGNAL) / 8.0) if SIGNAL <= f <= SIGNAL + 8 else 0.0
        press = seg(f, PRESS - 2, PRESS + 1) * (1.0 - seg(f, 44, 50))
        body, ro, rr = aim_body(arm, 0.0, 0.0, yaw=yaw, head_up=0.5 * up - 0.2 * slam, lean=-0.08 * up + 1.3 * slam,
                                crouch=-0.4 * up + (4.6 + bounce) * slam)
        yc = yaw + 4.0
        body["neck"] = (body["neck"][0], math.radians(-0.45 * yc * (1.0 - front)))
        body["head"] = (body["head"][0], math.radians(-0.52 * yc * (1.0 - front)))
        body["clavicle.L"] = rz(yc) @ V(1.0, -0.1, 0.35 * up)
        _c, P0 = P_.solve(body, ro, rr)
        Dr = root_delta(P_, P0)
        R = Dr.to_3x3()
        # the pistol: from the aim down to his side (0-8), held low, back on the aim (56-66)
        T_aim = aim_T(P0)
        T_low = gun_T(body_point(Dr, LOW_G), (R @ LOW_A).normalized(), up_perp(R @ LOW_A, R @ LOW_U))
        if f <= 8:
            T_g = path_T(f, [(0, T_aim), (8, T_low)], G0)
        elif f < 56:
            T_g = T_low
        else:
            T_g = path_T(f, [(56, T_low), (66, T_aim)], G0)
        hold_r = on_gun(T_g, (R @ LOW_POLE).lerp(R_POLE, 1.0 - front))
        # the killswitch and the left hand
        T_hol = holstered_T(P_, P0)
        hip = hip_hold(Dr)(P0)
        at_hol = (T_hol @ SG0, T_hol.to_3x3() @ SA0, R @ V(1.0, 0.2, -0.6))
        sky = (body_point(Dr, SKY_FIST + V(0, 0, 0.01 * math.sin(f * 0.9) * up)), R @ SKY_ALONG, R @ SKY_POLE)
        low = (body_point(Dr, SLAM_FIST), R @ SLAM_ALONG, R @ SLAM_POLE)
        T_s = None
        if f <= 6:
            hold_l = fist_at(*hip)
        elif f <= GRAB:
            u = seg(f, 6, GRAB)
            hold_l = fist_at(via(hip[0], body_point(Dr, V(0.36, 0.06, 1.02)), at_hol[0], u), hip[1].slerp(at_hol[1], u), hip[2].lerp(at_hol[2], u))
        elif f <= 24:
            u = seg(f, GRAB, 24)
            mid = body_point(Dr, V(0.42, -0.2, 1.5))
            hold_l = fist_at(via(at_hol[0], mid, sky[0], u), at_hol[1].slerp(sky[1], u), at_hol[2].lerp(sky[2], u))
        elif f <= 28:
            hold_l = fist_at(*sky)
        elif f <= SIGNAL:
            u = seg(f, 28, SIGNAL)
            u = u * u                                                        # (accelerating: a slam)
            hold_l = fist_at(sky[0].lerp(low[0], u), sky[1].slerp(low[1], u), sky[2].lerp(low[2], u))
        elif f <= 44:
            hold_l = fist_at(low[0] + V(0, 0, -0.012 * bounce), low[1], low[2])
        elif f <= 56:
            u = seg(f, 44, 56)
            mid = body_point(Dr, V(0.36, -0.2, 0.95))
            hold_l = fist_at(via(low[0], mid, at_hol[0], u), low[1].slerp(at_hol[1], u), low[2].lerp(at_hol[2], u))
        elif f <= 62:
            u = seg(f, 56, 62)
            hold_l = fist_at(via(at_hol[0], body_point(Dr, V(0.36, 0.06, 1.02)), hip[0], u), at_hol[1].slerp(hip[1], u), at_hol[2].lerp(hip[2], u))
        else:
            hold_l = fist_at(*hip)
        holds = {"R": hold_r, "L": hold_l}
        in_hand = GRAB <= f <= 56
        if not in_hand:
            T_s = T_hol
            ch, P = solve(P_, arm, body, ro, rr, holds, props(P_, T_g, T_s), scales=scales_for(press))
        else:
            ch, P = solve(P_, arm, body, ro, rr, holds, props(P_, T_g), scales=scales_for(press))
            T_s = switch_in_fist(P_, P)
            ch, P = solve(P_, arm, body, ro, rr, holds, props(P_, T_g, T_s), scales=scales_for(press))
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def switch_in_fist(P_, P):
    """The killswitch's rigid motion in his posed left fist: its grip's middle at the fist's middle, the rod along the
    fist's thumb axis, the guard's side toward the back of his hand."""
    M = P["hand.L"] @ P_.rest["hand.L"].inverted()
    H = HAND["L"]
    G = M @ (H["wr"] + H["off"])
    Rm = M.to_3x3()
    A = (Rm @ H["t"]).normalized()
    nb = -(Rm @ H["n"])
    U = (nb - A * nb.dot(A)).normalized()
    return sw_T(G, A, U)


# ----------------------------------------------------------------------------------------------- Cheer
CH_ALONG = V(-0.6, 0.6, 0.3)                  # his left fist punched up high (its thumb back, toward him)
CH_POLE = V(1.0, 0.0, -0.3)


def make_cheer(arm, frames=CH_FR):
    """The pistol raised beside his shoulder and his left fist punched up high (0-10), two pumps and a hop (10-32), back
    down onto the aim (34-46)."""
    P_ = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        front = seg(f, 0, 9) * (1.0 - seg(f, 34, 45))
        yaw = YAW + (6.0 - YAW) * front
        up = seg(f, 0, 10) * (1.0 - seg(f, 33, 44))
        pump = max(0.0, math.sin(math.pi * (f - 12) / 9.0)) if 12 <= f <= 30 else 0.0
        hop = max(0.0, math.sin(math.pi * (f - 13) / 7.0)) * 0.045 if 13 <= f <= 20 else 0.0
        shout = math.sin(math.pi * min(1.0, max(0.0, (f - 8) / 18.0)))
        body, ro, rr = aim_body(arm, 0.0, 0.0, yaw=yaw, head_up=0.25 * up + 0.3 * shout, lean=-0.08 * up - 0.05 * shout,
                                crouch=-0.3 * up)
        yc = yaw + 4.0
        body["neck"] = (body["neck"][0], math.radians(-0.45 * yc * (1.0 - front)))
        body["head"] = (body["head"][0], math.radians(-0.52 * yc * (1.0 - front)))
        body["clavicle.R"] = rz(yc) @ V(-1.0, -0.15 * (1 - up), 0.1 + 0.05 * up)
        body["clavicle.L"] = rz(yc) @ V(1.0, -0.1, 0.3 * up)
        ro = ro + V(0.0, 0.0, hop)
        _c, P0 = P_.solve(body, ro, rr)
        Dr = root_delta(P_, P0)
        R = Dr.to_3x3()
        T_aim = aim_T(P0)
        T_up = up_T(Dr, lift=0.02 * pump)
        T_g = path_T(f, [(0, T_aim), (9, T_up)], G0) if f <= 20 else path_T(f, [(34, T_up), (45, T_aim)], G0)
        hp_ = hip_hold(Dr)(P0)
        fist_lo = body_point(Dr, V(0.36, -0.32, 2.0))
        fist_hi = body_point(Dr, V(0.42, -0.2, 2.22))
        mid = body_point(Dr, V(0.44, -0.4, 1.4))
        al = R @ CH_ALONG
        top = fist_lo.lerp(fist_hi, pump) if f >= 10 else fist_hi
        pole_up = R @ CH_POLE
        if f <= 10:
            u = seg(f, 0, 10)
            pos, a_, pole = via(hp_[0], mid, fist_hi, u), hp_[1].slerp(al, u), hp_[2].lerp(pole_up, u)
        elif f < 34:
            pos, a_, pole = top, al, pole_up
        else:
            u = seg(f, 34, 45)
            pos, a_, pole = via(top, mid, hp_[0], u), al.slerp(hp_[1], u), pole_up.lerp(hp_[2], u)
        holds = {"R": on_gun(T_g, (R @ UP_POLE).lerp(R_POLE, 1.0 - up)), "L": fist_at(pos, a_, pole)}
        ch, P = solve(P_, arm, body, ro, rr, holds, props(P_, T_g, holstered_T(P_, P0)), scales=scales_for(0.0))
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
