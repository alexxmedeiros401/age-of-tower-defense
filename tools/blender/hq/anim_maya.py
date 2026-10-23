"""Maya's clips (keyed frame by frame; the .glb runs them at 24 fps, game.gd CLIP_FPS).

Idle    : (120) the rifle held across her body at a relaxed port: her right fist on the pistol grip at her right hip, her
          left on the foregrip before her left shoulder, the muzzle up past her left shoulder; she shifts her weight and
          looks about; once round the loop her left hand leaves the foregrip and presses her headset (a radio check).
Combat  : (40) on the aim, standing: turned side-on to her right, left foot forward, the butt in her right shoulder,
          her cheek down to the stock behind the red dot, her left fist on the vertical foregrip; a slow sway.
Attack  : (FR = 18 frames, inside the 0.8 s cooldown) a three-round burst: the shots at SHOTS (frames 1, 2, 3: game.gd
          adds the flash and the bullets at the muzzle; the aim held at frame 1, each shot kicks the muzzle up a little
          and shoves the rifle back), the recoil settles (4-7) and she is back on the aim (= Combat) by frame 15.
Ability : Airstrike (AB_FR = 70): the rifle comes down off her shoulder into her right fist, upright at her right side
          (0-8); she turns to the front, her left hand takes the red-topped smoke grenade from its pouch (8-12), draws it
          back over her shoulder (12-18) and throws it overhand (RELEASE, frame 21); it arcs out ahead and lands (LAND,
          frame 33: game.gd can start the red smoke there); she presses her headset to call it in (27-38) and flings
          her left arm up at the sky over the target, looking up as the jets come in (SIGNAL, frame 45, held to 56: the
          call is made, game.gd sends the jets from MAYA_SIGNAL, her raised fist); then she shoulders the rifle again
          (56-70). The grenade lies where it landed until frame 60, then is gone (scale 0, constant keys) and is back in
          its pouch on the last frame.
Cheer   : (CH_FR = 48) she thrusts the rifle up one-handed (upright in her right fist, high at her right side), hops
          with a whoop (her head thrown back), pumps her left fist twice overhead and comes back down onto the aim.

Props are posed in world space: the rifle (parentless) by the rigid motion of its rest placement, her fists put on its
grips by IK (each fist's length kept in line with its forearm, as Ada's and the Rifleman's); the smoke grenade (a child
of her chest: it rides its pouch unless a clip poses it) carried in her left fist by her hand's motion, then flown on
its own arc."""
import math
from mathutils import Vector, Quaternion, Matrix
import maya as cm
from rig import Poser, leg_aims, arm_aims, frame_map, bone_len, two_bone
from anim import new_action, finish_action

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
VV = lambda p: Vector((float(p[0]), float(p[1]), float(p[2])))
ROOT = VV(J["root"])

SHOTS = (1, 2, 3)      # game.gd: the burst's bullets leave the muzzle (the first with the aim held, frame 1)
SHOT = SHOTS[0]
FR = 18                # the Attack's length (0.75 s at 24 fps)
RELEASE = 21           # Airstrike: the smoke grenade leaves her hand
LAND = 33              # ... and lands out ahead (the red smoke can start here)
SIGNAL = 45            # ... her fist flung up at the sky: the call is made (held to 56)
AB_FR = 70
CH_FR = 48
GROUND_Z = -0.2        # where the grenade lands: the map's ground, below the stand (her feet at 0, maya_base.TOP_Z)
DEBUG = None

# ----------------------------------------------------------------------------------------------- rest-pose frames
G0, A0, U0 = VV(cm.GUN_G0), VV(cm.GUN_A0), VV(cm.GUN_U0)
S0 = A0.cross(U0)
gl = lambda *a: VV(cm.gl(*a))
GRIP_AX = VV(cm.grip_axis())
FORE_AX = VV(cm.fore_axis())
FORE_PT = gl(cm.FORE_U, 0.0, cm.BAR_H - 0.03) - FORE_AX * 0.058          # the left fist's middle on the foregrip
BUTT_PT = gl(cm.BUTT_U, 0.0, 0.075)                                       # the butt pad's middle

_nb, _na = cm.nade_rest()
NADE_B, NADE_AX = VV(_nb), VV(_na)
NADE_MID = NADE_B + NADE_AX * (cm.NADE_L * 0.5)

HAND = {}
for _s in ("R", "L"):
    _wr, _f, _n, _t = cm.hand_frame(_s)
    HAND[_s] = {"wr": VV(_wr), "f": VV(_f), "n": VV(_n), "t": VV(_t), "off": VV(cm.fist_center(_s)) - VV(_wr)}

_cc, _cax = cm.cup_frame(1)
CUP_L = VV(_cc) + VV(_cax) * 0.1                                          # (rest) the left fist pressed to her earcup


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def seg(f, a, b):
    return smooth01((f - a) / float(b - a))


def gun_T(G, A, U):
    """The rifle's rigid motion that puts its grip's middle at G, its barrel along A, its top toward U."""
    R = frame_map(A0, Vector(A).normalized(), U0, Vector(U))
    return Matrix.Translation(Vector(G)) @ R.to_4x4() @ Matrix.Translation(-G0)


def gun_at(point_rest, point_t, A, U):
    R = frame_map(A0, Vector(A).normalized(), U0, Vector(U))
    return Matrix.Translation(Vector(point_t) - R @ Vector(point_rest)) @ R.to_4x4()


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


def path_v(f, keys):
    """Piecewise eased blend of vectors through [(frame, v), ...]."""
    if f <= keys[0][0]:
        return Vector(keys[0][1])
    for (fa, a), (fb, b) in zip(keys, keys[1:]):
        if f <= fb:
            return Vector(a).lerp(Vector(b), seg(f, fa, fb))
    return Vector(keys[-1][1])


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
    ch, P = P_.solve(aims, ro, rr, scales=scales)
    hs = {side: fn(P) for side, fn in holds.items()}
    if DEBUG is not None:
        DEBUG.append({side: Vector(h[0]) for side, h in hs.items()})
    aims = dict(aims)
    aims.update(hands_aims(arm, P, hs))
    aims.update(props)
    return P_.solve(aims, ro, rr, scales=scales)


def on_gun(T, side, pole):
    """A fist on the rifle: the right one round the pistol grip, the left one round the vertical foregrip."""
    R = T.to_3x3()
    if side == "R":
        return lambda P: (T @ G0, R @ GRIP_AX, pole)
    return lambda P: (T @ FORE_PT, R @ FORE_AX, pole)


def fist_at(p, along, pole):
    return lambda P: (Vector(p), Vector(along), pole)


def root_delta(P_, P):
    return P["root"] @ P_.rest["root"].inverted()


def body_point(Dr, p):
    return Dr @ Vector(p)


def props(P_, T_g, smoke=None):
    """The props' aims: the rifle (world), the smoke grenade (None: in its pouch; a callable(P) -> its rigid motion)."""
    out = {"rifle": lambda P, b: ("world", T_g @ P_.rest["rifle"])}
    if smoke is not None:
        out["smoke"] = lambda P, b: ("world", smoke(P) @ P_.rest["smoke"])
    return out


def _nade_in_fist():
    """The grenade's motion from its pouch into her left fist (rest pose): its middle at the fist's grip centre, its axis
    along the thumb."""
    H = HAND["L"]
    t = H["t"].normalized()
    R = frame_map(NADE_AX, t, V(0, 1, 0), H["f"])
    fc = H["wr"] + H["off"]
    return Matrix.Translation(fc - R @ NADE_MID) @ R.to_4x4()


NADE_FIST = _nade_in_fist()


def nade_in_hand(P_):
    return lambda P: (P["hand.L"] @ P_.rest["hand.L"].inverted()) @ NADE_FIST


def nade_free(pos, rot):
    """The grenade's motion putting its middle at `pos`, turned by `rot` (a 3x3) from its rest placement."""
    return Matrix.Translation(Vector(pos) - rot @ NADE_MID) @ rot.to_4x4()


# ----------------------------------------------------------------------------------------------- the aim
YAW = -32.0
POCKET = (0.05, 0.1, 0.1)          # the butt's place: ahead of her right shoulder joint, in toward her chest, up
AIM_DOWN = 0.05
L_POLE = V(0.3, -0.2, -1.0)         # her left elbow under the handguard
R_POLE = V(-0.8, 0.4, -0.5)         # her right elbow out and down
AIM_BODY = {"lean": 0.18, "side": -0.04, "head_tilt": -0.3, "head_up": -0.3, "neck_side": -0.2,
            "neck_tw": -0.45 * YAW + 4, "head_tw": -0.55 * YAW + 2}


def aim_body(arm, br=0.0, sway=0.0, push=0.0, head_up=0.0):
    b = AIM_BODY
    aims = legs(arm, YAW, lf=(0.2, -0.22), rf=(-0.19, 0.19), turn_l=8.0, turn_r=-18.0)
    yc = YAW + 2.5 * push
    ro = rz(YAW) @ V(0.0, -0.025 + 0.025 * push, 0.0) + V(0.0, 0.0, -0.05 + 0.004 * br)
    rr = rz(YAW + 0.8 * sway)
    torso(aims, yc, lean=b["lean"] - 0.06 * push, side=b["side"], spine_tw=math.radians(-3), chest_tw=math.radians(-6),
          neck_tw=math.radians(b["neck_tw"]), head_tw=math.radians(b["head_tw"]), head_tilt=b["head_tilt"],
          head_up=b["head_up"] + head_up, neck_side=b["neck_side"])
    aims["clavicle.L"] = rz(yc) @ V(1.0, -0.28, 0.04)
    aims["clavicle.R"] = rz(yc) @ V(-1.0, 0.05, 0.2 + 0.05 * push)
    return aims, ro, rr


def aim_T(P, kick=0.0, back=0.0, sway=0.0, br=0.0):
    """The rifle on the aim: the butt pad in her right shoulder's pocket, the barrel level toward the robots (-y),
    dipping a little; `kick` (radians) turns the muzzle up about the butt, `back` shoves it back."""
    sh = P["upperarm.R"].translation
    C = P["chest"].to_3x3()
    fwd = C @ V(0, 0, 1)
    fwd.z = 0.0
    fwd.normalize()
    medial = C @ V(1, 0, 0)
    pocket = sh + fwd * POCKET[0] + medial * POCKET[1] + V(0, 0, POCKET[2])
    A = V(0.012 * sway, -math.cos(AIM_DOWN), -math.sin(AIM_DOWN) + 0.004 * br).normalized()
    if kick:
        A = Quaternion(A.cross(V(0, 0, 1)).normalized(), kick) @ A
    return gun_at(BUTT_PT, pocket + V(0, back, 0.3 * back), A, up_perp(A))


def combat_pose(arm, P_, t, kick=0.0, back=0.0, push=0.0):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    body, ro, rr = aim_body(arm, br, sw, push=push)
    _c, P0 = P_.solve(body, ro, rr)
    T_g = aim_T(P0, kick, back, sw, br)
    holds = {"R": on_gun(T_g, "R", R_POLE), "L": on_gun(T_g, "L", L_POLE)}
    return solve(P_, arm, body, ro, rr, holds, props(P_, T_g))


def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        ch, _ = combat_pose(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def burst(f):
    """(kick, back, push) of the burst: each shot (frames 1, 2, 3) kicks the muzzle up a little more and shoves the
    rifle back; the recoil peaks at frame 4 and settles back onto the aim by frame 15."""
    if f <= SHOT:
        return 0.0, 0.0, 0.0
    if f <= 4:
        k = (f - SHOT) / 3.0
        return 0.06 * k, 0.012 * (f - SHOT), 0.6 * k
    s = 1.0 - smooth01((f - 4) / 11.0)
    return 0.06 * s, 0.036 * s, 0.6 * s


def make_attack(arm, frames=FR):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        kick, back, push = burst(f)
        ch, _ = combat_pose(arm, P_, 0.0, kick=kick, back=back, push=push)
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- idle: a relaxed port
PORT_G = V(-0.13, -0.26, 1.0)                        # (body frame) the pistol grip at her right hip, before her
PORT_A = V(0.5, -0.17, 0.85).normalized()            # (body frame) the muzzle up past her left shoulder


def port_T(Dr, br=0.0, k=0.0):
    R = Dr.to_3x3()
    A = (R @ PORT_A).normalized()
    U = up_perp(A, R @ V(0.0, -1.0, 0.25))           # (its top, the red dot, toward the front)
    return gun_T(body_point(Dr, PORT_G + V(0, 0, 0.003 * br + 0.01 * k)), A, U)


def idle_pose(arm, P_, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    hip = math.sin(w)
    yaw = -8.0 + 3.0 * math.sin(w)
    aims = legs(arm, yaw, lf=(0.17 + 0.012 * hip, -0.03), rf=(-0.19 + 0.012 * hip, 0.05), open_feet=0.5, turn_l=12.0, turn_r=-16.0)
    ro = V(0.02 * hip, 0.0, -0.012 + 0.004 * br - 0.006 * abs(hip))
    rr = rz(yaw) @ Quaternion(V(0, 1, 0), math.radians(2.5 * hip))
    check = smooth01((t - 0.55) / 0.07) * (1.0 - smooth01((t - 0.78) / 0.07))       # the radio check
    look = (0.42 * math.sin(w + 0.6) + 0.12 * math.sin(w * 3)) * (1.0 - check)
    torso(aims, yaw, lean=-0.02, side=-0.05 * hip, spine_tw=0.03 * math.sin(w), chest_tw=0.04 * math.sin(w),
          neck_tw=0.3 * look + 0.12 * check, head_tw=0.65 * look + 0.2 * check, head_tilt=0.04 * hip - 0.12 * check,
          head_up=0.06 + 0.03 * br - 0.1 * check)
    q = rz(yaw)
    aims["clavicle.L"] = q @ V(1.0, 0.0, -0.03 + 0.12 * check)
    aims["clavicle.R"] = q @ V(-1.0, -0.02, 0.04)
    ch, P = P_.solve(aims, ro, rr)
    Dr = root_delta(P_, P)
    T_g = port_T(Dr, br, check)
    hold_l = on_gun(T_g, "L", V(1.0, -0.2, -0.8))
    if check > 0.0:
        Hd = P["head"] @ P_.rest["head"].inverted()
        ear = Hd @ CUP_L
        g = on_gun(T_g, "L", V(1.0, -0.2, -0.8))(P)
        hold_l = fist_at(g[0].lerp(ear, check), g[1].slerp((Hd.to_3x3() @ V(0.0, -0.3, 1.0)).normalized(), check),
                         V(1.0, -0.2, -0.8).lerp(V(1.0, 0.3, -0.3), check))
    holds = {"R": on_gun(T_g, "R", V(-1.0, 0.4, -0.5)), "L": hold_l}
    return solve(P_, arm, aims, ro, rr, holds, props(P_, T_g))


def make_idle(arm, frames=120):
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        ch, _ = idle_pose(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- one-hand holds
UP_G = V(-0.3, -0.2, 1.06)                          # (body frame) the rifle upright in her right fist at her right side
UP_A = V(-0.04, -0.12, 1.0).normalized()
HIGH_G = V(-0.3, -0.1, 1.62)                        # (body frame) ... thrust up high (the Cheer)
HIGH_A = V(-0.08, -0.05, 1.0).normalized()


def upright_T(Dr, G=UP_G, A=UP_A):
    R = Dr.to_3x3()
    A_ = (R @ A).normalized()
    U = up_perp(A_, R @ V(0.0, -1.0, 0.0))
    return gun_T(body_point(Dr, G), A_, U)


def _set_constant(act, bone, path="scale"):
    key = 'pose.bones["%s"].%s' % (bone, path)
    done = False
    try:
        for fc in act.fcurves:
            if key in fc.data_path:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
                done = True
    except Exception:
        pass
    if not done:
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        if key in fc.data_path:
                            for kp in fc.keyframe_points:
                                kp.interpolation = "CONSTANT"


# ----------------------------------------------------------------------------------------------- Airstrike
# the left fist's path (body frame): (frame, fist, thumb axis, elbow pole)
_POUCH = None


def _pouch_fist():
    """(body frame) the fist round the grenade's middle in its pouch."""
    return NADE_MID + V(0.0, 0.0, 0.03)


THROW_KEYS = [
    (8, V(0.34, -0.12, 1.06), V(0.0, -0.3, 1.0), V(1.0, 0.3, -0.6)),     # reaching to the pouch
    (12, None, V(0.0, -0.2, 1.0), V(1.0, 0.3, -0.6)),                     # (on the grenade: its pouch)
    (15, V(0.36, -0.02, 1.32), V(0.2, -0.2, 1.0), V(1.0, 0.2, -0.3)),    # lifted
    (18, V(0.38, 0.2, 1.58), V(0.1, -0.5, 0.8), V(0.8, 0.6, 0.0)),       # drawn back over her shoulder
    (21, V(0.2, -0.4, 1.66), V(0.0, -0.6, 0.8), V(0.9, 0.2, -0.2)),      # RELEASE: high before her shoulder
    (25, V(0.08, -0.42, 1.18), V(-0.4, -0.5, 0.6), V(1.0, 0.2, -0.6)),   # follow-through across her
]


def make_ability(arm, frames=AB_FR):
    P_ = Poser(arm)
    act = new_action(arm, "Ability")
    rel = {}
    tumble_ax = V(1.0, 0.0, 0.0)
    for f in range(frames + 1):
        front = seg(f, 0, 9) * (1.0 - seg(f, 58, 68))
        yaw = YAW + (-4.0 - YAW) * front
        wind = seg(f, 12, 18) * (1.0 - seg(f, 18, 21))
        throw = seg(f, 18, 22) * (1.0 - seg(f, 24, 30))
        call = seg(f, 26, 31) * (1.0 - seg(f, 39, 43))
        up = seg(f, 40, SIGNAL) * (1.0 - seg(f, 56, 62))
        q = rz(yaw)
        aims = legs(arm, yaw, lf=(0.19 - 0.03 * throw, -0.06 - 0.12 * throw), rf=(-0.19, 0.08), turn_l=10.0, turn_r=-18.0)
        ro = q @ V(0.0, -0.02 * throw + 0.02 * wind, 0.0) + V(0.0, 0.0, -0.03 - 0.02 * throw + 0.008 * up)
        rr = rz(yaw + 14.0 * wind - 16.0 * throw)
        yc = yaw + 22.0 * wind - 26.0 * throw
        torso(aims, yc, lean=0.04 - 0.12 * wind + 0.2 * throw - 0.1 * up, side=0.06 * wind - 0.08 * up,
              neck_tw=math.radians(-0.4 * (yc - yaw) + 6.0 * call), head_tw=math.radians(-0.5 * (yc - yaw) + 10.0 * call),
              head_tilt=0.12 * call, head_up=0.1 * throw + 0.05 * call + 0.55 * up - 0.05 * wind)
        aims["clavicle.L"] = rz(yc) @ V(1.0, -0.05 + 0.2 * wind, 0.0 + 0.25 * up + 0.15 * wind)
        aims["clavicle.R"] = rz(yc) @ V(-1.0, 0.0, 0.04)
        _c, P0 = P_.solve(aims, ro, rr)
        Dr = root_delta(P_, P0)
        R = Dr.to_3x3()
        # the rifle: from the aim down into her right fist, upright at her right side, and back up to the aim
        T_aim = aim_T(P0) if f <= 8 or f >= 58 else None
        T_up = upright_T(Dr)
        if f <= 8:
            T_g = path_T(f, [(0, aim_T(P0)), (8, T_up)], G0)
        elif f < 58:
            T_g = T_up
        else:
            T_g = path_T(f, [(58, T_up), (68, T_aim)], G0)
        hold_r = on_gun(T_g, "R", V(-1.0, 0.3, -0.5))
        # the left hand
        smoke = None
        if f <= 4:
            hold_l = on_gun(T_g, "L", L_POLE)
        elif f <= 8:
            g = on_gun(T_g, "L", L_POLE)(P0)
            k0 = THROW_KEYS[0]
            u = seg(f, 4, 8)
            hold_l = fist_at(g[0].lerp(body_point(Dr, k0[1]), u), g[1].slerp(R @ k0[2], u), L_POLE.lerp(k0[3], u))
        elif f <= 25:
            keys = []
            for (kf, p, al, pole) in THROW_KEYS:
                pp = body_point(Dr, _pouch_fist()) if p is None else body_point(Dr, p)
                keys.append((kf, pp, R @ al, R @ pole))
            pos = path_v(f, [(k[0], k[1]) for k in keys])
            al = path_v(f, [(k[0], k[2]) for k in keys])
            pole = path_v(f, [(k[0], k[3]) for k in keys])
            hold_l = fist_at(pos, al, pole)
            if 12 <= f <= RELEASE:
                smoke = nade_in_hand(P_)
        else:
            # to her headset (27-31), held there (calling it in), then flung up at the sky (40-45), held, back down (56-62)
            Hd = P0["head"] @ P_.rest["head"].inverted()
            ear = Hd @ CUP_L
            ear_al = (Hd.to_3x3() @ V(0.0, -0.3, 1.0)).normalized()
            sky = body_point(Dr, V(0.27, -0.3, 1.9))
            sky_al = R @ V(0.0, -0.9, -0.3)
            fol = body_point(Dr, THROW_KEYS[-1][1])
            if f <= 31:
                u = seg(f, 25, 31)
                pos, al, pole = fol.lerp(ear, u), (R @ THROW_KEYS[-1][2]).slerp(ear_al, u), V(1.0, 0.2, -0.6).lerp(V(1.0, 0.4, -0.2), u)
            elif f <= 40:
                bob = 0.006 * math.sin((f - 31) * 1.3)
                pos, al, pole = ear + V(0, 0, bob), ear_al, V(1.0, 0.4, -0.2)
            elif f <= 56:
                u = seg(f, 40, SIGNAL)
                shake = 0.012 * math.sin((f - SIGNAL) * 1.2) * (1.0 - min(1.0, max(0.0, (f - SIGNAL) / 10.0))) if f >= SIGNAL else 0.0
                pos, al, pole = ear.lerp(sky, u) + V(0, 0, shake), ear_al.slerp(sky_al, u), V(1.0, 0.4, -0.2).lerp(V(1.0, 0.3, 0.2), u)
            else:
                g = on_gun(T_g, "L", L_POLE)(P0)
                u = seg(f, 56, 66)
                pos, al, pole = sky.lerp(g[0], u), sky_al.slerp(g[1], u), V(1.0, 0.3, 0.2).lerp(L_POLE, u)
                if f >= 66:
                    pos, al, pole = g
            hold_l = fist_at(pos, al, pole)
        # the grenade in flight: an arc from where it left her hand out to the ground ahead, tumbling
        if RELEASE < f:
            p0, R0 = rel["p"], rel["R"]
            p1 = body_point(Dr, V(0.22, -2.4, GROUND_Z + cm.NADE_R)) if "p1" not in rel else rel["p1"]
            rel["p1"] = p1
            u = min(1.0, (f - RELEASE) / float(LAND - RELEASE))
            pos = p0.lerp(p1, u) + V(0, 0, 0.75 * 4 * u * (1 - u))
            if f < LAND:
                rot = Quaternion(R0 @ tumble_ax, -2.6 * math.pi * u).to_matrix() @ R0
            else:
                ax_side = (p1 - p0)
                ax_side.z = 0.0
                ax_side.normalize()
                lie = frame_map(NADE_AX, ax_side, V(0, 0, 1), V(0, 0, 1))      # lying on its side, pointing on
                rot = lie
                pos = p1 + V(0, 0, 0.0)
            T_n = nade_free(pos, rot)
            smoke = (lambda T: (lambda P: T))(T_n)
        holds = {"R": hold_r, "L": hold_l}
        sc = {"smoke": 0.0 if 60 <= f < frames else 1.0}
        ch, P = solve(P_, arm, aims, ro, rr, holds, props(P_, T_g, smoke), scales=sc)
        if f == RELEASE:
            M = (P["hand.L"] @ P_.rest["hand.L"].inverted()) @ NADE_FIST
            rel["p"] = M @ NADE_MID
            rel["R"] = M.to_3x3()
        P_.key(ch, f)
    _set_constant(act, "smoke")
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- Cheer
def make_cheer(arm, frames=CH_FR):
    """The rifle thrust up high in her right fist (0-10), a hop with a whoop and two pumps of her left fist (10-34),
    back down onto the aim (34-46)."""
    P_ = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        front = seg(f, 0, 9) * (1.0 - seg(f, 34, 45))
        yaw = YAW + (-2.0 - YAW) * front
        up = seg(f, 0, 10) * (1.0 - seg(f, 33, 44))
        pump = max(0.0, math.sin(math.pi * (f - 12) / 9.0)) if 12 <= f <= 30 else 0.0
        hop = max(0.0, math.sin(math.pi * (f - 13) / 7.0)) * 0.05 if 13 <= f <= 20 else 0.0
        whoop = math.sin(math.pi * min(1.0, max(0.0, (f - 9) / 16.0)))
        q = rz(yaw)
        aims = legs(arm, yaw, lf=(0.19, -0.08 + 0.06 * front), rf=(-0.19, 0.12 - 0.06 * front), turn_l=10.0, turn_r=-18.0)
        ro = q @ V(0.0, -0.02, 0.0) + V(0.0, 0.0, -0.05 + 0.03 * up + hop)
        rr = rz(yaw)
        torso(aims, yaw, lean=0.12 * (1 - up) - 0.12 * up - 0.06 * whoop, side=0.0,
              head_up=-0.1 * (1 - up) + 0.3 * up + 0.4 * whoop, head_tw=math.radians(-0.3 * yaw * (1 - front)))
        aims["clavicle.L"] = rz(yaw) @ V(1.0, -0.1, 0.2 * up)
        aims["clavicle.R"] = rz(yaw) @ V(-1.0, 0.0, 0.25 * up)
        _c, P0 = P_.solve(aims, ro, rr)
        Dr = root_delta(P_, P0)
        R = Dr.to_3x3()
        T_aim = aim_T(P0)
        T_hi = upright_T(Dr, HIGH_G + V(0, 0, 0.04 * pump), HIGH_A)
        T_mid = upright_T(Dr)
        T_g = path_T(f, [(0, T_aim), (5, T_mid), (10, T_hi)], G0) if f <= 20 else path_T(f, [(33, T_hi), (39, T_mid), (45, T_aim)], G0)
        g = on_gun(T_g, "L", L_POLE)(P0)
        fist_lo = body_point(Dr, V(0.3, -0.16, 1.62))
        fist_hi = body_point(Dr, V(0.28, -0.12, 1.98))
        al = R @ V(0.0, -0.4, 1.0)
        top = fist_lo.lerp(fist_hi, pump)
        if f <= 10:
            u = seg(f, 0, 10)
            pos, a_, pole = g[0].lerp(top, u), g[1].slerp(al, u), L_POLE.lerp(V(1.0, 0.2, -0.3), u)
        elif f < 34:
            pos, a_, pole = top, al, V(1.0, 0.2, -0.3)
        else:
            u = seg(f, 34, 45)
            pos, a_, pole = top.lerp(g[0], u), al.slerp(g[1], u), V(1.0, 0.2, -0.3).lerp(L_POLE, u)
        holds = {"R": on_gun(T_g, "R", V(-1.0, 0.3, -0.4).lerp(R_POLE, 1.0 - up)), "L": fist_at(pos, a_, pole)}
        ch, P = solve(P_, arm, aims, ro, rr, holds, props(P_, T_g))
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
