"""Ada's clips (keyed frame by frame; the .glb runs them at 24 fps, game.gd CLIP_FPS).

Idle    : (120) the launcher propped on her right hip, its butt on her belt and its muzzle up in the air, her right fist
          on its grip; her left fist on her left hip; she shifts her weight, looks about, glances at her gauntlet (its gear
          ticks round a quarter turn over the loop).
Combat  : (40) the hip aim: turned side-on to her right, left foot forward, knees bent; the launcher level at her right hip,
          her right fist on the pistol grip, her left on the fore-grip, the muzzle toward the robots (-y); a slow sway.
Attack  : (FR = 19 frames, inside the 0.8 s cooldown) the shot at SHOT (frame 1: the aim held over frames 0-1; game.gd adds
          the flash, the steam and the bolt at the muzzle), the kick throws the muzzle up and the launcher back (2-4), the
          pan magazine turns on one bolt (4-9) while the tank hisses (the game's steam), and she settles back on the aim
          (= Combat) by frame 16.
Ability : Overdrive (AB_FR = 68): her right hand lets go and her left carries the launcher low at her left side (0-8); she
          draws the big spanner from her right hip (8-16), twirls it twice before her while the gauntlet's gear spins up
          (16-30), and thrusts it high overhead (30-36): at SIGNAL (frame 36, held to 46) the gear whirls and the core blazes
          (game.gd sends out the Overdrive burst from the spanner's jaw, ADA_SIGNAL); then the spanner goes back in its loop
          (46-56), her right hand takes the grip again and she is back on the aim (56-68).
Cheer   : (CH_FR = 48) she swings the launcher up overhead in both fists, hops with a whoop (her head thrown back), pumps it
          twice, the gear spinning, and comes back down onto the aim.

Props are posed in world space (their bones are parentless: every frame aims them, "world"): the launcher by the rigid
motion of its rest placement (the clips decide where it is; her fists are put on its grips by IK, each fist's length kept
in line with its forearm, as the Musketeer's); the spanner in its loop (following her hips) or in her right fist. The
pan magazine (`drum`, a child of the launcher's bone) and the gauntlet's gear (`gear`, a child of her right forearm's) are
turned about their own axes ("rot" aims); the core's bone (`core`) is scaled up in the Ability."""
import math
from mathutils import Vector, Quaternion, Matrix
import ada as cm
from rig import Poser, leg_aims, arm_aims, frame_map, bone_len, two_bone
from anim import new_action, finish_action

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
VV = lambda p: Vector((float(p[0]), float(p[1]), float(p[2])))
ROOT = VV(J["root"])

SHOT = 1               # game.gd ATTACK_FRAME: the bolt leaves the muzzle (the aim held over frames 0-1)
FR = 19                # the Attack's length (0.79 s at 24 fps)
SIGNAL = 36            # Overdrive: the spanner held high, the gauntlet blazing (held to frame 46)
AB_FR = 68
CH_FR = 48
DEBUG = None           # (a list: the fists' targets of every solved frame, for checking the reach)

# ----------------------------------------------------------------------------------------------- rest-pose frames
G0, A0, U0 = VV(cm.GUN_G0), VV(cm.GUN_A0), VV(cm.GUN_U0)
S0 = A0.cross(U0)


gl = lambda *a: VV(cm.gl(*a))                          # (a point of the launcher at rest, its drawing coordinates)


GRIP_AX = VV(cm.grip_axis())
FORE_PT = gl(cm.FORE_U - 0.006, 0.0, -0.05)            # the left fist's middle on the fore-grip
BUTT_PT = gl(-0.13, 0.0, 0.1)                            # the butt cap's end
_wg, _wa, _we, _wn = cm.wrench_rest()
WG0, WA0, WE0, WN0 = VV(_wg), VV(_wa), VV(_we), VV(_wn)

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
    """0..1 eased progress of frame f through [a, b]."""
    return smooth01((f - a) / float(b - a))


def gun_T(G, A, U):
    """The launcher's rigid motion that puts its grip's middle at G, its barrel along A, its top toward U."""
    R = frame_map(A0, Vector(A).normalized(), U0, Vector(U))
    return Matrix.Translation(Vector(G)) @ R.to_4x4() @ Matrix.Translation(-G0)


def gun_at(point_rest, point_t, A, U):
    """The launcher's motion laying it along A (its top toward U) with its rest-pose point `point_rest` at point_t."""
    R = frame_map(A0, Vector(A).normalized(), U0, Vector(U))
    return Matrix.Translation(Vector(point_t) - R @ Vector(point_rest)) @ R.to_4x4()


def wrench_T(G, A, E):
    R = frame_map(WA0, Vector(A).normalized(), WE0, Vector(E))
    return Matrix.Translation(Vector(G)) @ R.to_4x4() @ Matrix.Translation(-WG0)


def mix_T(T0, T1, k, pivot):
    """Blend two rigid motions: slerp the turn, lerp where they put `pivot` (a rest-pose point)."""
    q = T0.to_quaternion().slerp(T1.to_quaternion(), k)
    p = (T0 @ pivot).lerp(T1 @ pivot, k)
    R = q.to_matrix()
    return Matrix.Translation(p - R @ pivot) @ R.to_4x4()


def path_T(f, keys, pivot):
    """Piecewise eased blend through [(frame, T), ...]."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (fa, Ta), (fb, Tb) in zip(keys, keys[1:]):
        if f <= fb:
            return mix_T(Ta, Tb, seg(f, fa, fb), pivot)
    return keys[-1][1]


def up_perp(A, ref=V(0, 0, 1)):
    A = Vector(A).normalized()
    u = Vector(ref) - A * Vector(ref).dot(A)
    return u.normalized()


# ----------------------------------------------------------------------------------------------- body
def legs(arm, yaw, lf=(0.18, -0.02), rf=(-0.18, 0.06), lift_l=0.0, lift_r=0.0, open_feet=0.6, turn_l=6.0, turn_r=-10.0):
    """Feet planted under the turned hips: lf / rf are the ankles in the body's own frame."""
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
          head_up=0.0):
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.22 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.32 * lean, 1.0), chest_tw)
    aims["neck"] = (V(0.0, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


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
    """A fist on the launcher: the right one round the pistol grip, the left one round the fore-grip (thumbs up)."""
    R = T.to_3x3()
    if side == "R":
        return lambda P: (T @ G0, R @ GRIP_AX, pole)
    return lambda P: (T @ FORE_PT, R @ U0, pole)


def on_wrench(Tw, pole):
    return lambda P: (Tw @ WG0, Tw.to_3x3() @ WA0, pole)


def fist_at(p, along, pole):
    return lambda P: (Vector(p), Vector(along), pole)


def root_delta(P_, P):
    return P["root"] @ P_.rest["root"].inverted()


def mid_T(Dr):
    R = Dr.to_3x3()
    A = (R @ MID_A).normalized()
    return gun_at(FORE_PT, body_point(Dr, MID_FIST), A, up_perp(A, R @ V(0.1, -0.6, 0.8)))


def body_point(Dr, p):
    """A point given where it is with her body at rest (armature space) -> where her hips' motion takes it."""
    return Dr @ Vector(p)


def props(P_, T_g, T_w=None, drum=0.0, gear=0.0, spin_w=None):
    """The props' aims: the launcher and the spanner (T_w None: in its loop, following her hips; spin_w = (angle): turned
    about its flat's normal through its grip, a twirl), the pan magazine and the gear turned about their own axes."""
    out = {"launcher": lambda P, b: ("world", T_g @ P_.rest["launcher"])}
    def wr(P, b):
        T = T_w if T_w is not None else root_delta(P_, P)
        if spin_w:
            n = P["forearm.R"].col[1].xyz.normalized()           # (spun about her forearm's line: clear of her arm)
            c = T @ WG0
            T = Matrix.Translation(c) @ Quaternion(n, spin_w).to_matrix().to_4x4() @ Matrix.Translation(-c) @ T
        return ("world", T @ P_.rest["wrench"])
    out["wrench"] = wr
    out["drum"] = lambda P, b: ("rot", Quaternion(b.col[1].xyz.normalized(), drum))
    out["gear"] = lambda P, b: ("rot", Quaternion(b.col[1].xyz.normalized(), gear))
    return out


# ----------------------------------------------------------------------------------------------- the hip aim
YAW = -42.0                                  # turned side-on to her right, the launcher at her right hip
CHEST = -14.0                                # (her shoulders turned further, her left one toward the robots)
AIM_A = V(0.0, -1.0, -0.06).normalized()     # the barrel's line (the robots straight ahead, a little below)
AIM_G = V(-0.29, -0.17, 0.99)                # the pistol grip's middle (armature space), clear of her front
R_POLE = V(-0.5, 1.0, -0.4)                  # her right elbow back and out
L_POLE = V(0.9, 0.1, -1.0)                   # her left elbow down and out


def stance(arm, br=0.0, sway=0.0, lean=0.0, crouch=0.0, chest=CHEST, head_up=0.0, lift_l=0.0, lift_r=0.0, yaw=YAW, head_side=0.0):
    q = rz(yaw)
    aims = legs(arm, yaw, lf=(0.2, -0.17), rf=(-0.2, 0.12), lift_l=lift_l, lift_r=lift_r, turn_l=10.0, turn_r=-22.0)
    ro = q @ V(0.0, -0.02, 0.0) + V(0.0, 0.0, -0.05 - 0.035 * crouch + 0.004 * br)
    rr = rz(yaw + 1.2 * sway)
    yc = yaw + chest
    torso(aims, yc, lean=0.14 + lean, side=0.02 * sway, spine_tw=math.radians(chest * 0.4), chest_tw=math.radians(chest * 0.6),
          neck_tw=math.radians(-0.5 * yc), head_tw=math.radians(-0.55 * yc), head_tilt=-0.05 + head_side, head_up=-0.05 + head_up)
    qc = rz(yc)
    aims["clavicle.L"] = qc @ V(1.0, -0.12, 0.0)
    aims["clavicle.R"] = qc @ V(-1.0, 0.05, 0.08)
    return aims, ro, rr


def aim_T(kick=0.0, br=0.0, sway=0.0, back=0.0):
    """The launcher on the aim; `kick` (0..1) turns the muzzle up about the grip and shoves it back."""
    A = AIM_A
    if kick:
        A = Quaternion(A.cross(V(0, 0, 1)).normalized(), math.radians(14.0) * kick) @ A
    G = AIM_G + V(0.006 * sway, 0.0, 0.004 * br) + V(0.0, 0.05, 0.015) * kick + V(0, back, 0)
    return gun_T(G, A, up_perp(A))


def combat_pose(arm, P_, t, kick=0.0, drum=0.0):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    body, ro, rr = stance(arm, br, sw, lean=-0.07 * kick, head_up=0.03 * kick)
    T_g = aim_T(kick, br, sw)
    holds = {"R": on_gun(T_g, "R", R_POLE), "L": on_gun(T_g, "L", L_POLE)}
    return solve(P_, arm, body, ro, rr, holds, props(P_, T_g, drum=drum))


def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        ch, _ = combat_pose(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def kick_curve(f):
    """The recoil: nothing until the bolt has left (frame 1), up fast by 3, eased back down to the aim by 15."""
    if f <= SHOT:
        return 0.0
    if f <= 3:
        return smooth01((f - SHOT) / 2.0)
    return 1.0 - smooth01((f - 3) / 12.0)


def make_attack(arm, frames=FR):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    step = 2 * math.pi / cm.N_BOLTS
    for f in range(frames + 1):
        drum = -step * seg(f, 4, 9)                     # the pan turns on one bolt (a full step: the clip loops cleanly)
        ch, _ = combat_pose(arm, P_, 0.0, kick=kick_curve(f), drum=drum)
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- idle
IDLE_A = V(-0.28, -0.42, 0.86).normalized()      # (body frame) the launcher propped on her hip, its muzzle up, out and ahead
IDLE_BUTT = V(-0.32, -0.06, 0.93)                 # (body frame) its butt on her belt at her right hip


def idle_pose(arm, P_, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    hip = math.sin(w)                                  # her weight from hip to hip
    yaw = -8.0 + 3.0 * math.sin(w)
    aims = legs(arm, yaw, lf=(0.17 + 0.012 * hip, -0.03), rf=(-0.19 + 0.012 * hip, 0.05), open_feet=0.5, turn_l=12.0, turn_r=-16.0)
    ro = V(0.02 * hip, 0.0, -0.012 + 0.004 * br - 0.006 * abs(hip))
    rr = rz(yaw) @ Quaternion(V(0, 1, 0), math.radians(2.5 * hip))
    glance = smooth01((t - 0.55) / 0.06) * (1.0 - smooth01((t - 0.75) / 0.06))     # a look at her gauntlet
    look = (0.42 * math.sin(w + 0.6) + 0.12 * math.sin(w * 3)) * (1.0 - glance)
    torso(aims, yaw, lean=-0.02, side=-0.05 * hip, spine_tw=0.03 * math.sin(w), chest_tw=0.04 * math.sin(w),
          neck_tw=0.3 * look + 0.25 * glance, head_tw=0.65 * look + 0.45 * glance, head_tilt=0.04 * hip - 0.08 * glance,
          head_up=0.06 + 0.03 * br - 0.28 * glance)
    q = rz(yaw)
    aims["clavicle.L"] = q @ V(1.0, 0.0, -0.03)
    aims["clavicle.R"] = q @ V(-1.0, -0.02, 0.06)
    ch, P = P_.solve(aims, ro, rr)
    Dr = root_delta(P_, P)
    A = (Dr.to_3x3() @ IDLE_A).normalized()
    U = up_perp(A, Dr.to_3x3() @ V(0.0, -1.0, 0.0))
    T_g = gun_at(BUTT_PT, body_point(Dr, IDLE_BUTT) + V(0, 0, 0.002 * br), A, U)
    hipL = Dr @ V(0.265, 0.0, 0.925)
    holds = {"R": on_gun(T_g, "R", V(-1.0, 0.4, -0.5)),
             "L": fist_at(hipL, Dr.to_3x3() @ V(0.0, -0.4, -1.0), V(1.0, 0.6, -0.3))}
    gear = -(math.pi / 2) * t                         # ticks a quarter turn round the loop
    return solve(P_, arm, aims, ro, rr, holds, props(P_, T_g, gear=gear))


def make_idle(arm, frames=120):
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        ch, _ = idle_pose(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- Overdrive
CARRY_FIST = V(0.35, -0.19, 1.2)                  # (body frame) the left fist on the fore-grip before her left shoulder ...
CARRY_A = V(0.12, 0.55, 0.83).normalized()        # (body frame) ... the barrel shouldered, up and back over it
MID_FIST = V(0.08, -0.62, 1.2)                    # (body frame) on the way: before her, clear of her front
MID_A = V(0.35, -0.55, 0.75).normalized()
HIGH_W = V(-0.22, -0.12, 2.16)                    # (body frame) the spanner thrust high: its grip ...
HIGH_A = V(-0.12, -0.18, 1.0).normalized()        # ... its jaw up
FRONT_W = V(-0.08, -0.4, 1.28)                    # (body frame) where she twirls it: before her chest
FRONT_A = V(0.1, -0.35, 1.0).normalized()


def carry_T(Dr, br=0.0):
    R = Dr.to_3x3()
    A = (R @ CARRY_A).normalized()
    U = up_perp(A, R @ V(1.0, -0.35, 0.0))        # (its top, the pan, turned out to her left)
    return gun_at(FORE_PT, body_point(Dr, CARRY_FIST) + V(0, 0, 0.003 * br), A, U)


def wrench_slid(Dr, s):
    """The spanner slid `s` up out of its loop (following her hips)."""
    return Dr @ Matrix.Translation(WA0 * s)


def make_ability(arm, frames=AB_FR):
    """Overdrive: let go and carry (0-8), to the spanner (6-11), draw (11-16), up before her and twirl (16-30), thrust high
    (30-36), SIGNAL held (36-46), down to the hip (46-52), into the loop (52-56), the grip again (56-60), the aim (58-68)."""
    P_ = Poser(arm)
    act = new_action(arm, "Ability")
    k = {"free": 4, "grab": 11, "out": 16, "front": 21, "twirl": 30, "high": SIGNAL, "hold": 46, "down": 52, "in": 56,
         "pgrab": 60, "aim": 66}
    gear_ang = 0.0
    for f in range(frames + 1):
        front = seg(f, 0, 10) * (1.0 - seg(f, 56, 66))          # turned to the front while she signals
        yaw = YAW + (2.0 - YAW) * front
        up = seg(f, k["twirl"], k["high"]) * (1.0 - seg(f, k["hold"], k["down"]))
        reach = seg(f, k["free"], k["grab"]) * (1.0 - seg(f, k["grab"] + 1, k["out"] + 1)) + \
            seg(f, k["hold"] + 2, k["down"]) * (1.0 - seg(f, k["in"], k["pgrab"]))
        body, ro, rr = stance(arm, 0.0, 0.0, lean=-0.14 * up + 0.12 * reach, head_up=0.42 * up - 0.12 * reach,
                              crouch=-0.25 * up + 0.4 * reach, chest=CHEST * (1.0 - front) - 10.0 * reach + 6.0 * up, yaw=yaw, head_side=-0.06 * reach)
        _c, P0 = P_.solve(body, ro, rr)
        Dr = root_delta(P_, P0)
        T_aim = aim_T()
        T_car = carry_T(Dr)
        # the launcher: from the aim down to the carry, and back
        T_mid = mid_T(Dr)
        if f <= k["free"] + 4:
            T_g = path_T(f, [(0, T_aim), (4, T_mid), (k["free"] + 4, T_car)], FORE_PT)
        elif f < k["pgrab"] - 4:
            T_g = T_car
        else:
            T_g = path_T(f, [(k["pgrab"] - 4, T_car), (k["pgrab"] + 1, T_mid), (k["aim"], T_aim)], FORE_PT)
        # the spanner and her right hand
        T_w, spin = None, 0.0
        H_hip = wrench_slid(Dr, 0.0)
        H_out = wrench_slid(Dr, 0.15)
        G_f, A_f = body_point(Dr, FRONT_W), (Dr.to_3x3() @ FRONT_A)
        E_f = (Dr.to_3x3() @ V(-1.0, 0.0, 0.0))
        T_front = wrench_T(G_f, A_f, E_f - A_f * E_f.dot(A_f))
        G_h, A_h = body_point(Dr, HIGH_W), (Dr.to_3x3() @ HIGH_A)
        E_h = (Dr.to_3x3() @ V(-1.0, 0.0, 0.0))
        T_high = wrench_T(G_h, A_h, E_h - A_h * E_h.dot(A_h))
        r_pole = V(-1.0, 0.4, -0.6)
        if f <= k["free"]:
            hold_r = on_gun(T_g, "R", R_POLE)
        elif f <= k["grab"]:
            # the hand from the grip to the spanner's grip in its loop
            u = seg(f, k["free"], k["grab"])
            Ta = T_g
            src = (Ta @ G0, (Ta.to_3x3() @ GRIP_AX).normalized())
            dst = (H_hip @ WG0, (H_hip.to_3x3() @ WA0).normalized())
            hold_r = fist_at(src[0].lerp(dst[0], u) + V(0, 0, 0.06 * math.sin(math.pi * u)), src[1].slerp(dst[1], u), R_POLE.lerp(r_pole, u))
        elif f <= k["out"]:
            T_w = wrench_slid(Dr, 0.15 * seg(f, k["grab"], k["out"]))
            hold_r = on_wrench(T_w, r_pole)
        elif f <= k["front"]:
            T_w = mix_T(H_out, T_front, seg(f, k["out"], k["front"]), WG0)
            hold_r = on_wrench(T_w, r_pole)
        elif f <= k["twirl"]:
            T_w = T_front @ Matrix.Identity(4)
            bob = math.sin(math.pi * (f - k["front"]) / (k["twirl"] - k["front"]))
            T_w = Matrix.Translation(V(0, 0, 0.03 * bob)) @ T_w
            hold_r = on_wrench(T_w, r_pole)
            spin = -4 * math.pi * seg(f, k["front"], k["twirl"])      # two turns
        elif f <= k["high"]:
            T_w = mix_T(T_front, T_high, seg(f, k["twirl"], k["high"]), WG0)
            hold_r = on_wrench(T_w, V(-1.0, 0.2, -0.3))
        elif f <= k["hold"]:
            sh = 0.012 * math.sin((f - k["high"]) * 1.1) * (1.0 - (f - k["high"]) / 12.0)
            T_w = Matrix.Translation(V(0, 0, sh)) @ T_high
            hold_r = on_wrench(T_w, V(-1.0, 0.2, -0.3))
        elif f <= k["down"]:
            T_w = path_T(f, [(k["hold"], T_high), (k["hold"] + 3, T_front), (k["down"], H_out)], WG0)
            hold_r = on_wrench(T_w, r_pole)
        elif f <= k["in"]:
            T_w = wrench_slid(Dr, 0.15 * (1.0 - seg(f, k["down"], k["in"])))
            hold_r = on_wrench(T_w, r_pole)
            if f == k["in"]:
                T_w = None
        else:
            u = seg(f, k["in"], k["pgrab"])
            src = (H_hip @ WG0, (H_hip.to_3x3() @ WA0).normalized())
            dst = (T_g @ G0, (T_g.to_3x3() @ GRIP_AX).normalized())
            if f < k["pgrab"]:
                hold_r = fist_at(src[0].lerp(dst[0], u) + V(0, 0, 0.05 * math.sin(math.pi * u)), src[1].slerp(dst[1], u), r_pole.lerp(R_POLE, u))
            else:
                hold_r = on_gun(T_g, "R", R_POLE)
        # the left hand: on the fore-grip all through
        l_pole = L_POLE.lerp(V(1.0, 0.3, -0.2), seg(f, 0, 8) * (1.0 - seg(f, 58, 66)))
        holds = {"R": hold_r, "L": on_gun(T_g, "L", l_pole)}
        # the gear spins up from the twirl to the signal and runs down after; the core swells at the signal
        rate = 0.05 + 0.75 * seg(f, k["front"], k["high"]) * (1.0 - seg(f, k["hold"], k["in"] + 6))
        gear_ang -= rate
        glow = 1.0 + 0.7 * seg(f, k["twirl"], k["high"]) * (1.0 - seg(f, k["hold"], k["in"])) + \
            0.12 * math.sin((f - k["high"]) * 1.4) * (1.0 if k["high"] <= f <= k["hold"] else 0.0)
        pr = props(P_, T_g, T_w, gear=gear_ang, spin_w=spin)
        ch, P = solve(P_, arm, body, ro, rr, holds, pr, scales={"core": glow})
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- Cheer
OVER_G = V(-0.17, -0.06, 2.0)                     # (body frame, facing front) the launcher overhead: its grip ...
OVER_A = V(1.0, 0.0, 0.08).normalized()           # ... its muzzle to her left
PRESENT_G = V(-0.14, -0.46, 1.3)                  # (body frame) on the way: held up before her chest
PRESENT_A = V(0.7, -0.25, 0.65).normalized()


def make_cheer(arm, frames=CH_FR):
    """Up overhead (0-10), a hop with a whoop and two pumps (10-32), back down onto the aim (32-46)."""
    P_ = Poser(arm)
    act = new_action(arm, "Cheer")
    gear_ang = 0.0
    for f in range(frames + 1):
        front = seg(f, 0, 9) * (1.0 - seg(f, 34, 45))
        yaw = YAW + (0.0 - YAW) * front
        up = seg(f, 0, 10) * (1.0 - seg(f, 33, 44))
        pump = max(0.0, math.sin(math.pi * (f - 12) / 9.0)) if 12 <= f <= 30 else 0.0
        hop = max(0.0, math.sin(math.pi * (f - 13) / 7.0)) * 0.05 if 13 <= f <= 20 else 0.0
        whoop = math.sin(math.pi * min(1.0, max(0.0, (f - 9) / 16.0)))
        body, ro, rr = stance(arm, 0.0, 0.0, lean=-0.16 * up - 0.06 * whoop, head_up=0.35 * up + 0.4 * whoop,
                              crouch=-0.4 * up, chest=CHEST * (1.0 - front), yaw=yaw)
        ro = ro + V(0.0, 0.0, hop)
        _c, P0 = P_.solve(body, ro, rr)
        Dr = root_delta(P_, P0)
        R = Dr.to_3x3()
        A_o = (R @ OVER_A).normalized()
        T_over = gun_T(body_point(Dr, OVER_G + V(0, 0, 0.1 * pump)), A_o, up_perp(A_o))
        T_aim = aim_T()
        Ap = (R @ PRESENT_A).normalized()
        T_pres = gun_T(body_point(Dr, PRESENT_G), Ap, up_perp(Ap, R @ V(0.0, -1.0, 0.3)))
        T_g = path_T(f, [(0, T_aim), (4, T_pres), (10, T_over)], G0) if f <= 20 else \
            path_T(f, [(33, T_over), (39, T_pres), (45, T_aim)], G0)
        holds = {"R": on_gun(T_g, "R", R_POLE.lerp(V(-1.0, 0.2, -0.2), up)), "L": on_gun(T_g, "L", L_POLE.lerp(V(1.0, 0.2, -0.2), up))}
        gear_ang -= 0.06 + 0.3 * up
        ch, P = solve(P_, arm, body, ro, rr, holds, props(P_, T_g, gear=gear_ang))
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
