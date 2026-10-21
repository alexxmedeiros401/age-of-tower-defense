"""Crossbowman clips (game: 24 fps):
- Idle: standing easy, the crossbow at the low ready across his body (the left hand under the fore-stock, the right on
  the stock's wrist, its nose down and to his left); he breathes and looks about, and once a loop shifts his weight.
- Combat: the aim: left foot forward, knees a little bent, the butt at his right cheek, the stock level before his eye,
  pointed at the robots; a slow sway as he tracks.
- Attack (22 frames, inside the 0.96 s cooldown): the shot at RELEASE (frame 1: the string snaps forward, the bolt
  leaves the groove: game.gd's bolt flies from XBOW_TIP), the kick (1-3); he drops the nose to his hip, takes the string
  in his right hand and hauls it back onto the nut (7-12), takes a bolt from the quiver at his hip and lays it in the
  groove (12-17), and raises the crossbow to the aim again (the last frame = the Combat pose).

The crossbow is rigid in his left fist (a "frame" aim: the stock along A, its top along U); his right fist holds the
stock's wrist from below to shoot (its thumb axis along the stock, the palm up). The string is two bones from the prod's
tips to its middle, aimed at the nut, the braced line or his right fist and stretched to reach; the bolt's bone hides it
(scale 0) from the shot until it is laid in the groove."""
import math
from mathutils import Vector, Quaternion
import crossbowman as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
ROOT = Vector(J["root"])

_G, _A, _U, _S = cm.xbow_frame()
G_REST, A_REST, U_REST = Vector(_G), Vector(_A), Vector(_U)
WR_L_REST = Vector(J["wrist_L"])
_wr, _f, _n, _t = cm.hand_frame("R")
WR_R_REST, T_R_REST, N_R_REST = Vector(_wr), Vector(_t), Vector(_n)
FIST_OFF_R = Vector(cm.fist_center("R")) - WR_R_REST
GRIP_REST = Vector(cm.grip_point())
NUT_REST = Vector(cm.nut_point())
BRACED_REST = Vector(cm.braced_point())
_t1, _t2 = cm.prod_tips()
TIP_R_REST, TIP_L_REST = Vector(_t1), Vector(_t2)
Q_TOP = Vector(cm.Q_TOP)
RELEASE = 1           # the bolt leaves the groove (game.gd ATTACK_FRAME)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def xrot(A_t, U_t):
    return frame_map(A_REST, Vector(A_t).normalized(), U_REST, Vector(U_t))


def xpoint(G_t, A_t, U_t, p_rest):
    """Where a point of the crossbow (rest pose) is when the left fist holds it at G_t, pointed along A_t, top up U_t."""
    return Vector(G_t) + xrot(A_t, U_t) @ (Vector(p_rest) - G_REST)


def left_hold(arm, G_t, A_t, U_t, pole):
    R = xrot(A_t, U_t)
    aims = arm_aims(arm, "L", Vector(G_t) - R @ (G_REST - WR_L_REST), pole=pole)
    aims["hand.L"] = ("frame", A_REST, Vector(A_t).normalized(), U_REST, Vector(U_t))
    return aims


def right_grip(arm, fist, along, palm, pole):
    """Right fist (its grip centre) at `fist`, its thumb axis along `along`, the palm facing `palm`."""
    R = frame_map(T_R_REST, Vector(along).normalized(), N_R_REST, Vector(palm))
    aims = arm_aims(arm, "R", Vector(fist) - R @ FIST_OFF_R, pole=pole)
    aims["hand.R"] = ("frame", T_R_REST, Vector(along).normalized(), N_R_REST, Vector(palm))
    return aims


def string_to(aims, scales, P, mid):
    """Aim the two string bones from their (posed) heads at the prod's tips to `mid` and stretch them to reach it."""
    for nm, tip_rest in (("string_r", TIP_R_REST), ("string_l", TIP_L_REST)):
        head = P[nm].translation
        aims[nm] = (lambda m: (lambda PP, base: m - base.translation))(Vector(mid))
        rest_len = (NUT_REST - tip_rest).length
        scales[nm] = (1.0, max(0.2, (Vector(mid) - head).length / rest_len), 1.0)


def solve2(P_, aims, ro, rr, scales, mid):
    ch, P = P_.solve(aims, ro, rr, scales=scales)
    string_to(aims, scales, P, mid)
    return P_.solve(aims, ro, rr, scales=scales)


def legs(arm, yaw, lf=(0.2, -0.12), rf=(-0.2, 0.14), lift_l=0.0, open_feet=0.6):
    q = rz(yaw)
    aims = {}
    for side, (bx, by), lift in (("L", lf, lift_l), ("R", rf, 0.0)):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + lift)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = Vector(J["toe_" + side]) - Vector(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * open_feet + (-14 if side == "R" else 6)) @ rest_foot
    return aims


def torso(aims, yaw_chest, lean=0.0, side=0.0, spine_tw=0.0, chest_tw=0.0, neck_tw=0.0, head_tw=0.0, head_tilt=0.0,
          head_up=0.0):
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.22 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.32 * lean, 1.0), chest_tw)
    aims["neck"] = (V(0.0, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


# ----------------------------------------------------------------------------------------------- idle: the low ready
def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    shift = 0.5 - 0.5 * math.cos(w)
    aims = legs(arm, -8.0, lf=(0.2, -0.05), rf=(-0.2, 0.08), open_feet=0.3)
    ro = V(0.012 * shift, 0.0, -0.01 + 0.005 * br)
    rr = rz(-8.0 + 3.0 * math.sin(w))
    look = 0.45 * math.sin(w) + 0.12 * math.sin(w * 3)
    torso(aims, -8.0, lean=0.02, side=0.02 * (shift - 0.5), spine_tw=0.03 * math.sin(w), chest_tw=0.05 * math.sin(w),
          neck_tw=0.3 * look, head_tw=0.7 * look, head_up=0.03 + 0.04 * br)
    q = rz(-8.0)
    aims["clavicle.L"] = q @ V(1.0, 0.0, -0.02)
    aims["clavicle.R"] = q @ V(-1.0, 0.0, 0.02)
    A_t = (q @ V(0.42, -1.0, -0.5)).normalized()                  # the nose down and to his left
    U_t = (V(0, 0, 1) - A_t * A_t.z).normalized()
    G_t = V(0.12, -0.36, 0.93 + 0.006 * br)
    aims.update(left_hold(arm, G_t, A_t, U_t, pole=V(1.0, 0.2, -0.6)))
    grip = xpoint(G_t, A_t, U_t, GRIP_REST)
    aims.update(right_grip(arm, grip, A_t, U_t, pole=V(-1.0, 0.4, -0.4)))
    return aims, ro, rr, xpoint(G_t, A_t, U_t, NUT_REST)


def make_idle(arm, frames=120):
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr, mid = idle_pose(arm, (f % frames) / frames)
        sc = {"bolt": 1.0}
        ch, _ = solve2(P_, aims, ro, rr, sc, mid)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- the aim
YAW = -24.0
A_AIM = V(0.0, -1.0, 0.0)
U_AIM = V(0.0, 0.0, 1.0)
BUTT_AIM = V(-0.16, -0.05, 1.46)                       # the butt's end at his right cheek
G_AIM = BUTT_AIM + A_AIM * cm.BUTT_BACK
L_POLE = V(0.6, 0.1, -1.0)
R_POLE = V(-1.0, 0.4, -0.6)


def stance(arm, br=0.0, sway=0.0, crouch=0.0, lean_back=0.0, chest=0.0):
    aims = legs(arm, YAW, lf=(0.2, -0.2), rf=(-0.2, 0.2))
    q = rz(YAW)
    ro = q @ V(0.0, 0.03 * lean_back, 0.0) + V(0.0, 0.0, -0.05 - 0.04 * crouch + 0.004 * br)
    rr = rz(YAW + 1.2 * sway)
    yc = YAW + chest
    torso(aims, yc, lean=0.12 - 0.3 * lean_back, side=0.02 * sway, spine_tw=math.radians(chest * 0.4 - 4),
          chest_tw=math.radians(chest * 0.6 - 8), neck_tw=math.radians(-0.4 * yc + 6), head_tw=math.radians(-0.6 * yc + 4),
          head_tilt=-0.1, head_up=-0.05 + 0.1 * lean_back)
    qc = rz(yc)
    aims["clavicle.L"] = qc @ V(1.0, -0.2, 0.08)
    aims["clavicle.R"] = qc @ V(-1.0, 0.0, 0.1)
    return aims, ro, rr


def aim_holds(arm, G_t, A_t, U_t):
    aims = left_hold(arm, G_t, A_t, U_t, pole=L_POLE)
    aims.update(right_grip(arm, xpoint(G_t, A_t, U_t, GRIP_REST), A_t, U_t, pole=R_POLE))
    return aims


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    aims, ro, rr = stance(arm, br, sw)
    A_t = (A_AIM + V(0.03 * sw, 0.0, 0.006 * br)).normalized()
    G_t = G_AIM + V(0.004 * sw, 0.0, 0.004 * br)
    aims.update(aim_holds(arm, G_t, A_t, U_AIM))
    return aims, ro, rr, xpoint(G_t, A_t, U_AIM, NUT_REST)


def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr, mid = combat_pose(arm, (f % frames) / frames)
        sc = {"bolt": 1.0}
        ch, _ = solve2(P_, aims, ro, rr, sc, mid)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- shoot and span
G_LOW = V(-0.04, -0.44, 1.06)                           # the crossbow at his hip, nose down, for the spanning
A_LOW = V(0.08, -1.0, -0.42).normalized()


def _u_for(A_t):
    return (V(0, 0, 1) - A_t * A_t.z).normalized()


def _dir_lerp(a, b, k):
    return Vector(a).normalized().slerp(Vector(b).normalized(), k)


def make_attack(arm, frames=22):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        sc = {"bolt": 1.0}
        crouch, lean_back, chest = 0.0, 0.0, 0.0
        if f == 0:
            G_t, A_t = G_AIM, A_AIM
        elif f <= 3:                                                   # the kick: the nose jumps, settles a little
            kick = math.sin(min(1.0, (f - 0.4) / 2.6) * math.pi)
            G_t = G_AIM + V(0.0, 0.025 * kick, 0.012 * kick)
            A_t = (A_AIM + V(0.0, 0.0, 0.12 * kick)).normalized()
        elif f <= 7:                                                   # down to the hip
            k = ease((f - 3) / 4.0)
            G_t = G_AIM.lerp(G_LOW, k)
            A_t = _dir_lerp(A_AIM, A_LOW, k)
            crouch = 0.4 * k
            chest = 6.0 * k
        elif f <= 12:                                                  # haul the string back onto the nut
            k = ease((f - 7) / 5.0)
            G_t = G_LOW + V(0.0, -0.03 * k, 0.0)
            A_t = A_LOW
            crouch, lean_back, chest = 0.4, 0.5 * k, 6.0 + 4.0 * k
        elif f <= 17:                                                  # a bolt from the quiver into the groove
            k = ease((f - 12) / 5.0)
            G_t = G_LOW + V(0.0, -0.03, 0.0)
            A_t = A_LOW
            crouch, lean_back, chest = 0.4 * (1 - 0.3 * k), 0.5 * (1 - k), 10.0 - 4.0 * k
        else:                                                          # up to the aim again
            k = ease((f - 17) / float(frames - 17))
            G_t = (G_LOW + V(0.0, -0.03, 0.0)).lerp(G_AIM, k)
            A_t = _dir_lerp(A_LOW, A_AIM, k)
            crouch, chest = 0.28 * (1 - k), 6.0 * (1 - k)
        U_t = _u_for(A_t)
        aims, ro, rr = stance(arm, 0.0, 0.0, crouch=crouch, lean_back=lean_back, chest=chest)
        aims.update(left_hold(arm, G_t, A_t, U_t, pole=L_POLE))
        grip = xpoint(G_t, A_t, U_t, GRIP_REST)
        nut = xpoint(G_t, A_t, U_t, NUT_REST)
        braced = xpoint(G_t, A_t, U_t, BRACED_REST)
        side = (A_t.cross(U_t)).normalized()                           # the stock's right side
        if f == 0:
            mid = nut
            aims.update(right_grip(arm, grip, A_t, U_t, pole=R_POLE))
        elif f <= 7:                                                   # the string loose at the braced line
            mid = braced
            sc["bolt"] = 0.0
            if f <= 3:
                aims.update(right_grip(arm, grip, A_t, U_t, pole=R_POLE))
            else:                                                      # the right hand off the grip, forward to the string
                k = ease((f - 3) / 4.0)
                hook = grip.lerp(braced + U_t * 0.05 + side * 0.03, k) + U_t * (0.08 * math.sin(k * math.pi))
                aims.update(right_grip(arm, hook, side * -1.0, (U_t * -0.4 + A_t * -1.0).normalized(), pole=R_POLE))
        elif f <= 12:                                                  # hauling: the string's middle in his fist
            k = ease((f - 7) / 5.0)
            hook = (braced + U_t * 0.05 + side * 0.03).lerp(nut + U_t * 0.05 + side * 0.03, k)
            mid = hook - U_t * 0.05 - side * 0.03
            sc["bolt"] = 0.0
            aims.update(right_grip(arm, hook, side * -1.0, (U_t * -0.4 + A_t * -1.0).normalized(), pole=R_POLE))
        elif f <= 17:                                                  # to the quiver, and the bolt to the groove
            mid = nut
            k = (f - 12) / 5.0
            qmouth = ROOT + ro + rr @ (Q_TOP - ROOT) + V(0.0, 0.0, 0.07)       # (the quiver is rigid on the root)
            groove = xpoint(G_t, A_t, U_t, NUT_REST) + A_t * 0.12 + U_t * 0.05 + side * 0.04
            if k < 0.5:
                kk = ease(k / 0.5)
                hand_at = (nut + U_t * 0.05 + side * 0.03).lerp(qmouth, kk)
            else:
                kk = ease((k - 0.5) / 0.5)
                hand_at = qmouth.lerp(groove, kk) + V(0, 0, 0.1 * math.sin(kk * math.pi))
            sc["bolt"] = 1.0 if f >= 17 else 0.0
            aims.update(right_grip(arm, hand_at, (A_t + V(0, 0, 0.3)).normalized(), side * -1.0, pole=R_POLE))
        else:                                                          # back to the grip
            mid = nut
            k = ease((f - 17) / float(frames - 17))
            groove = nut + A_t * 0.12 + U_t * 0.05 + side * 0.04
            hand_at = groove.lerp(grip, k)
            along = _dir_lerp((A_t + V(0, 0, 0.3)), A_t, k)
            palm = _dir_lerp(side * -1.0, U_t, k)
            aims.update(right_grip(arm, hand_at, along, palm, pole=R_POLE))
        ch, _ = solve2(P_, aims, ro, rr, sc, mid)
        P_.key(ch, f)
    _constant_scale(act, "bolt")
    finish_action(arm, act, frames, False)
    return act


def _constant_scale(act, bone):
    """The bolt appears / vanishes at once (constant interpolation on the bone's scale)."""
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
