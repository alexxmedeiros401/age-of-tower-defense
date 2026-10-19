"""Bronze Archer clips (30 fps):
- Idle: the bow hangs at his left side, his right fist on his belt, no arrow nocked; he breathes and looks about.
- Combat: at full draw, side-on to the target (straight ahead, -Y), sighting down the arrow; breathing, a slight sway.
- Attack: RELEASE at frame 1: the arrows leave the string (the game's arrows fly from the bow), the string snaps
  back, the bow kicks forward in his fist and his drawing hand flies back past his ear. He reaches over his right
  shoulder into the quiver, pulls a fresh pair of arrows, swings them over to the bow, nocks them and draws again,
  ending in the Combat pose (so the clip loops straight back into Combat or into the next shot).

The bow is rigid in his left fist: a "frame" aim stands its axis upright and turns its back toward the target. The
string is two bones from the tips to the nocking point, aimed at the drawing fingers and stretched along their length.
The nocked pair of arrows rides a bone in his right hand, aimed through the arrow rest on the bow; its scale hides
them between the release and the reload."""
import math
from mathutils import Vector, Quaternion, Matrix
import archer as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
Z = V(0, 0, 1)

# ----------------------------------------------------------------------------------------------- rest-pose geometry
_G, _A, _B, _S = cm.bow_frame()
G_REST, A_REST, B_REST = Vector(_G), Vector(_A), Vector(_B)
WR_L_REST = Vector(J["wrist_L"])
_t1, _t2 = cm.bow_tips()
TIP1_REST, TIP2_REST = Vector(_t1), Vector(_t2)
MID_REST = Vector(cm.string_mid())
_wr, _f, _n, _t = cm.hand_frame("R")
WR_R_REST, F_R, N_R, T_R = Vector(_wr), Vector(_f), Vector(_n), Vector(_t)
DRAW_REST = Vector(cm.draw_point())
_p0, _ax = cm.arrow_axis()
AX_REST = Vector(_ax)
_up = AX_REST.cross(N_R).normalized()                         # as in archer.arrows_field: up = ax x n
SIDE_REST = AX_REST.cross(_up).normalized()                    # the nocked pair sits side by side along this
Q_BOT, Q_TOP = Vector(cm.Q_BOT), Vector(cm.Q_TOP)
ROOT = Vector(J["root"])

RELEASE = 1           # the frame the arrows leave the string (game.gd spawns them then)
DRAW_LEN = 0.6        # grip to nocking point at full draw


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


# ----------------------------------------------------------------------------------------------- body
def legs(arm, yaw, spread=1.0, drop=0.0, open_feet=0.75):
    """Feet planted under the turned hips (left foot toward the target), toes turned with the body, knees soft."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by) in (("L", (0.19 * spread, -0.02)), ("R", (-0.19 * spread, 0.1))):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]))
        pole = q @ V(0.12 if side == "L" else -0.12, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = Vector(J["toe_" + side]) - Vector(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * open_feet) @ rest_foot
    return aims


def torso(aims, yaw_chest, lean=0.0, side=0.0, spine_tw=0.0, chest_tw=0.0, neck_tw=0.0, head_tw=0.0, head_tilt=0.0,
          head_up=0.0):
    """Lean / side bend are in the body's own frame (turned by yaw_chest); twists turn each bone about its axis."""
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.2 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.3 * lean, 1.0), chest_tw)
    aims["neck"] = (V(0.0, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


# ----------------------------------------------------------------------------------------------- props
def bow_rot(A_t, B_t):
    """World rotation of the bow (and the left fist) taking its rest axes to A_t (along the bow) and B_t (its back)."""
    return frame_map(A_REST, A_t, B_REST, B_t)


def bow_hand(arm, G_t, A_t, B_t, pole):
    """Left arm aims putting the fist (the bow's grip) at G_t with the bow standing along A_t, its back toward B_t."""
    R = bow_rot(A_t, B_t)
    wrist = G_t - R @ (G_REST - WR_L_REST)
    aims = arm_aims(arm, "L", wrist, pole=pole)
    aims["hand.L"] = ("frame", A_REST, Vector(A_t), B_REST, Vector(B_t))
    return aims


def bow_points(G_t, A_t, B_t):
    """Posed tips and string rest point of a bow held at G_t."""
    R = bow_rot(A_t, B_t)
    return (G_t + R @ (TIP1_REST - G_REST), G_t + R @ (TIP2_REST - G_REST), G_t + R @ (MID_REST - G_REST))


def draw_hand(arm, D_t, f_t, n_t, pole):
    """Right arm aims putting the drawing fingers' hook (where the string sits) at D_t, the hand's long axis along f_t
    and its palm facing n_t."""
    R = frame_map(F_R, f_t, N_R, n_t)
    wrist = D_t - R @ (DRAW_REST - WR_R_REST)
    aims = arm_aims(arm, "R", wrist, pole=pole)
    aims["hand.R"] = ("frame", F_R, Vector(f_t), N_R, Vector(n_t))
    return aims


def hand_q(f_t, n_t):
    return frame_map(F_R, f_t, N_R, n_t).to_quaternion()


def draw_hand_q(arm, D_t, q, pole):
    """As draw_hand, with the hand's world rotation given as a quaternion (for slerps between key orientations)."""
    R = q.to_matrix()
    wrist = D_t - R @ (DRAW_REST - WR_R_REST)
    aims = arm_aims(arm, "R", wrist, pole=pole)
    f_t = R @ F_R
    n_t = R @ N_R
    aims["hand.R"] = ("frame", F_R, f_t, N_R, n_t)
    return aims


def string_to(aims, scales, P, nock):
    """Aim the two string bones from their (posed) tips to the nocking point and stretch them to reach it."""
    for nm, tip_rest in (("string_top", TIP1_REST), ("string_bot", TIP2_REST)):
        head = P[nm].translation
        aims[nm] = (lambda n: (lambda PP, base: n - base.translation))(Vector(nock))
        rest_len = (MID_REST - tip_rest).length
        scales[nm] = (1.0, max(0.2, (Vector(nock) - head).length / rest_len), 1.0)


def arrow_aim(aims, d_t, side_t):
    aims["arrow"] = ("frame", AX_REST, Vector(d_t).normalized(), SIDE_REST, Vector(side_t))


def solve2(P_, aims, ro, rr, scales, nock=None):
    """Solve, then (when the string is drawn) aim and stretch the string bones at the posed tips and solve again."""
    ch, P = P_.solve(aims, ro, rr, scales=scales)
    if nock is not None:
        string_to(aims, scales, P, nock)
        ch, P = P_.solve(aims, ro, rr, scales=scales)
    return ch, P


# ----------------------------------------------------------------------------------------------- the drawn pose
YAW_ROOT = -50.0
SPINE_TW, CHEST_TW = -6.0, -12.0
YAW_CHEST = YAW_ROOT + SPINE_TW + CHEST_TW       # the way his chest faces
NECK_TW, HEAD_TW = 27.0, 41.0                    # ... and his head turned back to the target (-Y)
ARROW_X, ARROW_Z = -0.03, 1.41                   # under-chin anchor: the arrow just under his beard, a little right
ANCHOR_Y = -0.12
A_AIM = V(-0.12, 0.0, 1.0).normalized()          # the bow stands nearly upright, its top canted a little to his right
B_AIM = V(0.0, -1.0, 0.0)
F_AIM = V(0.55, -0.83, -0.03).normalized()       # drawing hand: knuckles toward the bow, the hand upright (thumb up),
N_AIM = V(0.83, 0.55, 0.0).normalized()          # palm toward his jaw
REST_UP, REST_SIDE = 0.042, 0.022                # the arrow rest on the bow: above the grip, on its left side
DRAW_POLE = V(-0.45, 1.0, 0.3)                   # drawing elbow: back along the arrow's line, out and up
BOW_POLE = V(0.6, 0.1, -1.0)
BOW_REACH = 0.95                                 # shoulder-to-wrist distance of the bow arm / its full length


def body_aims(arm, breathe=0.0, sway=0.0):
    aims = legs(arm, YAW_ROOT, spread=1.15)
    ro = V(0.0, 0.0, -0.022 + 0.003 * breathe)
    rr = rz(YAW_ROOT + 1.2 * sway)
    torso(aims, YAW_CHEST, lean=0.04, side=-0.05, spine_tw=math.radians(SPINE_TW), chest_tw=math.radians(CHEST_TW),
          neck_tw=math.radians(NECK_TW), head_tw=math.radians(HEAD_TW), head_tilt=-0.08, head_up=0.06)
    q = rz(YAW_CHEST)
    aims["clavicle.L"] = q @ V(1.0, -0.1, 0.1)
    aims["clavicle.R"] = q @ V(-1.0, 0.05, 0.22)
    return aims, ro, rr


def aim_geometry(arm, P_, breathe=0.0, sway=0.0, A=None):
    """Anchor (the nocking point at full draw), grip and bow axes: the arrow lies along -Y on the line through the
    anchor; the grip slides along it until the bow arm is almost straight."""
    aims, ro, rr = body_aims(arm, breathe, sway)
    _ch, P = P_.solve(aims, ro, rr)
    shoulder = P["upperarm.L"].translation
    dz = 0.004 * breathe
    anchor = V(ARROW_X + 0.002 * sway, ANCHOR_Y, ARROW_Z + dz)
    A = A_AIM if A is None else A
    B = B_AIM
    R = bow_rot(A, B)
    c = -(R @ (G_REST - WR_L_REST))
    L = BOW_REACH * (rest_len(arm, "upperarm.L") + rest_len(arm, "forearm.L"))
    g0 = V(anchor.x, 0.0, anchor.z) - A * REST_UP - V(1, 0, 0) * REST_SIDE
    w0 = g0 + c - shoulder
    disc = w0.y * w0.y - w0.length_squared + L * L
    y = -w0.y - math.sqrt(max(disc, 0.0))
    G = g0 + V(0, y, 0)
    return anchor, G, A, B


def rest_len(arm, nm):
    b = arm.data.bones[nm]
    return (b.tail_local - b.head_local).length


def drawn_pose(arm, P_, breathe=0.0, sway=0.0):
    """Full draw: the body side-on, the bow arm out to the target, the string at his chin."""
    anchor, G, A, B = aim_geometry(arm, P_, breathe, sway)
    aims, ro, rr = body_aims(arm, breathe, sway)
    aims.update(bow_hand(arm, G, A, B, pole=BOW_POLE))
    aims.update(draw_hand(arm, anchor, F_AIM, N_AIM, pole=DRAW_POLE))
    rest_pt = G + A * REST_UP + V(1, 0, 0) * REST_SIDE
    arrow_aim(aims, rest_pt - anchor, A)
    return aims, ro, rr, anchor


# ----------------------------------------------------------------------------------------------- clips
def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm, -8.0, spread=0.95, open_feet=0.5)
    ro = V(0.0, 0.0, -0.008 + 0.005 * br)
    rr = rz(-8.0 + 3.0 * math.sin(w))
    look = 0.4 * math.sin(w) + 0.12 * math.sin(w * 3)
    torso(aims, -8.0, lean=0.0, side=0.02 * math.sin(w), spine_tw=0.03 * math.sin(w), chest_tw=0.05 * math.sin(w),
          neck_tw=0.3 * look, head_tw=0.7 * look, head_up=0.05 + 0.04 * br)
    q = rz(-8.0)
    aims["clavicle.L"] = q @ V(1.0, 0.0, 0.0)
    aims["clavicle.R"] = q @ V(-1.0, 0.0, 0.03)
    # the bow hangs at his left side, upright, its back turned forward and out, the string toward his leg
    G = V(0.45, -0.1, 0.86 + 0.012 * math.sin(w * 2 + 0.6))
    A = V(0.08, -0.22, 1.0).normalized()
    B = V(0.92, -0.38, 0.0)                    # its back turned out to his left: the bow's curve shows from the front
    B = (B - A * B.dot(A)).normalized()
    aims.update(bow_hand(arm, G, A, B, pole=V(1.0, 0.4, -0.3)))
    # right fist resting on his belt
    aims.update(arm_aims(arm, "R", V(-0.3, -0.06, 0.98 + 0.004 * br), pole=V(-1.0, 0.6, 0.2), hand_dir=V(0.35, -0.35, -0.85)))
    return aims, ro, rr


def make_idle(arm, frames=120):
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames)
        sc = {"arrow": 0.0}
        ch, _ = P_.solve(aims, ro, rr, scales=sc)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def combat_state(t):
    w = 2 * math.pi * t
    return math.sin(w * 2), 0.6 * math.sin(w)


def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        br, sw = combat_state((f % frames) / frames)
        aims, ro, rr, nock = drawn_pose(arm, P_, breathe=br, sway=sw)
        sc = {"arrow": 1.0}
        ch, _ = solve2(P_, aims, ro, rr, sc, nock=nock)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def _slerp(a, b, k):
    return a.slerp(b, k)


def _dir_slerp(a, b, k):
    a, b = Vector(a).normalized(), Vector(b).normalized()
    return a.slerp(b, k) if a.dot(b) > -0.999 else a.lerp(b, k).normalized()


def make_attack(arm, frames=24):
    """Release at frame 1, the follow-through (1-4), the reach over his right shoulder to the quiver (4-10), a fresh
    pair of arrows in his fingers at frame 10, pulled out and swung over to the bow (10-16), nocked (16), drawn to his
    jaw by the last frame (= the Combat pose)."""
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    br0, sw0 = combat_state(0.0)
    anchor, G0, A0, B0 = aim_geometry(arm, P_, br0, sw0)
    # the quiver, as it sits on his turned back (it is rigid on the chest bone; posed below from the solved chest)
    q_chest = rz(YAW_CHEST)
    keys = {}
    hq_draw = hand_q(F_AIM, N_AIM)
    # drawing hand after the release: flung back past his ear, fingers open (palm turned out a little)
    D_follow = anchor + V(-0.06, 0.13, 0.02)
    hq_follow = hand_q(V(0.25, -0.9, 0.2), V(0.6, 0.3, 0.75))
    for f in range(frames + 1):
        sc = {"arrow": 1.0}
        nock = None
        aims, ro, rr, _n = drawn_pose(arm, P_, breathe=br0, sway=sw0)
        # posed chest -> where the quiver's mouth is now (first solve without the right arm's changes)
        _ch, P = P_.solve(aims, ro, rr, scales=sc)
        chest_m = P["chest"] @ arm.data.bones["chest"].matrix_local.inverted()
        q_top = chest_m @ Q_TOP
        q_bot = chest_m @ Q_BOT
        q_ax = (q_top - q_bot).normalized()
        D_grab = q_top + q_ax * 0.07                       # fingers on the fletching just above the quiver's mouth
        D_pull = q_top + q_ax * 0.34 + V(0.0, -0.06, 0.02)
        hq_grab = hand_q(-q_ax, (q_chest @ V(0.0, -1.0, 0.0)))
        hq_pull = hand_q((-q_ax).lerp(V(0, 0, 1), 0.3).normalized(), q_chest @ V(0.2, -1.0, 0.0))
        t1, t2, mid_rest = bow_points(G0, A0, B0)
        D_nock = mid_rest
        hq_nock = hand_q(F_AIM, N_AIM)
        G_off = V(0, 0, 0)
        A_t = A0
        if f == 0:
            D, hq, nock, arrow_on, adir = anchor, hq_draw, anchor, True, None
        elif f <= 4:                                       # release and follow-through
            k = ease((f - 1) / 3.0)
            D = anchor.lerp(D_follow, 0.55 + 0.45 * k)
            hq = _slerp(hq_draw, hq_follow, 0.6 + 0.4 * k)
            arrow_on, adir = False, None
            kick = math.sin(min(1.0, (f - 0.5) / 3.0) * math.pi)
            A_t = (A0 + V(0, -0.22, 0) * kick).normalized()
            G_off = V(0, -0.015 * kick, -0.02 * kick)
        elif f <= 10:                                      # reach over the shoulder into the quiver
            k = ease((f - 4) / 6.0)
            D = D_follow.lerp(D_grab, k) + V(0, 0, 0.1 * math.sin(k * math.pi))
            hq = _slerp(hq_follow, hq_grab, k)
            arrow_on = f == 10
            adir = -q_ax
            A_t = A0
            G_off = V(0, 0.02, -0.06) * math.sin(k * math.pi * 0.5)
        elif f <= 13:                                      # pull the pair up out of the quiver
            k = ease((f - 10) / 3.0)
            D = D_grab.lerp(D_pull, k)
            hq = _slerp(hq_grab, hq_pull, k)
            arrow_on = True
            adir = -q_ax
            G_off = V(0, 0.02, -0.06)
        elif f <= 16:                                      # swing them over to the bow, tips up and over, and nock
            k = ease((f - 13) / 3.0)
            D = D_pull.lerp(D_nock, k) + V(0, 0, 0.12 * math.sin(k * math.pi))
            hq = _slerp(hq_pull, hq_nock, k)
            arrow_on = True
            fwd = (G0 + A0 * REST_UP + V(1, 0, 0) * REST_SIDE - D_nock).normalized()
            # the tips swing out of the quiver backward, up over his head and down onto the bow (never through him)
            path = [-q_ax, (q_chest @ V(0.0, 1.0, 0.25)).normalized(), V(0.0, 0.25, 1.0).normalized(),
                    V(0.0, -0.7, 0.7).normalized(), fwd]
            u = k * (len(path) - 1)
            i = min(int(u), len(path) - 2)
            adir = _dir_slerp(path[i], path[i + 1], u - i)
            G_off = V(0, 0.02, -0.06).lerp(V(0, 0, 0), k)
            if f == 16:
                nock = D_nock
        else:                                              # draw to the anchor
            k = ease((f - 16) / float(frames - 16))
            D = D_nock.lerp(anchor, k)
            hq = hq_nock
            arrow_on = True
            adir = None
            nock = D
        sc["arrow"] = 1.0 if arrow_on else 0.0
        aims.update(draw_hand_q(arm, D, hq, pole=DRAW_POLE if f <= 2 or f >= 15 else q_chest @ V(-0.3, -0.6, 0.8)))
        if A_t is not A0 or G_off.length > 0:
            aims.update(bow_hand(arm, G0 + G_off, A_t, B0, pole=BOW_POLE))
        if adir is None:
            rest_pt = G0 + A0 * REST_UP + V(1, 0, 0) * REST_SIDE
            arrow_aim(aims, rest_pt - D, A0)
        else:
            side = Vector(adir).cross(V(1, 0, 0))
            if side.length < 1e-3:
                side = V(0, 0, 1)
            arrow_aim(aims, adir, side.normalized())
        if nock is not None:
            ch, P = P_.solve(aims, ro, rr, scales=sc)
            string_to(aims, sc, P, nock)
        else:
            aims.pop("string_top", None)
            aims.pop("string_bot", None)
            sc.pop("string_top", None)
            sc.pop("string_bot", None)
        ch, _ = P_.solve(aims, ro, rr, scales=sc)
        P_.key(ch, f)
    _constant_scale(act, "arrow")
    finish_action(arm, act, frames, False)
    return act


def _constant_scale(act, bone):
    """The arrows appear / vanish at once (constant interpolation on the bone's scale)."""
    path = 'pose.bones["%s"].scale' % bone
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
