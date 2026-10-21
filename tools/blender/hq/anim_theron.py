"""Theron's clips (keyed as 30 fps, like the other heroes'):

Idle    : leaning on his staff planted at his right side; he breathes and looks about, and once a loop lifts his left hand,
          palm up, at shoulder height and turns his head to it, feeling the air (what is coming).
Combat  : the staff planted before him at his right, the sun toward the robots; his left hand raised before his face,
          palm out, fingers spread: he reads them; a slow sway.
Attack  : (32 frames: inside the 1.1 s cooldown) he lifts the staff (0-6) and strikes its foot down before him (HIT,
          frame 9: game.gd's golden pulse rings out from the sun), the left hand sweeping out palm forward (9-14); he
          holds a moment and settles back (14-32).
Ability : Prophecy (58 frames): he raises the staff high overhead, his head thrown back, his left hand spread to the
          sky (0-16); the vision comes (VISION, frame 20: the sun's eye blazes, game.gd opens the great eye above him);
          he brings the staff down level, the sun pointed at the robots (FLARE, frame 34: they burn); holds, and settles
          back (40-58).
Cheer   : (rank up) he thumps the staff down twice and lifts it high, laughing, his left fist raised.

The staff is rigid in his right fist (the Druid's grip: anim_druid's helpers, the same build)."""
import math
from mathutils import Vector, Quaternion
import theron as cm
from rig import Poser
from anim import new_action, finish_action, lerp, ease
from anim_druid import (V, vec, ROOT, rz, body_pt, staff_grip, planted, feet, torso, open_hand, _smooth01 as smooth01)

FPS = 30
J = cm.J
HIT = 9              # the staff's foot strikes: the pulse (game.gd ATTACK_FRAME)
VISION = 20          # the sun's eye blazes (game.gd THERON_VISION)
FLARE = 34           # the sun pointed at the robots: they burn (game.gd THERON_FLARE)


def mixd(a, b, k):
    return a.normalized().lerp(b.normalized(), k).normalized()


# ---------------------------------------------------------------------------------------------- idle
BUTT_IDLE = V(-0.4, -0.08, 0.0)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    yaw = 3.0 * math.sin(w)
    ro = V(-0.02, 0.0, -0.012 + 0.004 * br)
    aims = feet(arm, 0.0)
    k = smooth01((t - 0.5) / 0.1) * (1.0 - smooth01((t - 0.78) / 0.12))          # the hand up (t 0.5-0.9)
    look = 26.0 * math.sin(w) * (1.0 - k) + 8.0 * math.sin(w * 3) * (1.0 - k) + 34.0 * k
    torso(aims, yaw, bend=0.08 - 0.04 * k, side=-0.03, look=look, pitch=0.02 + 0.02 * br + 0.12 * k)
    aims.update(planted(arm, BUTT_IDLE, V(-0.03, 0.06, 1.0), V(-0.2, -1.0, 0.0), pole=V(-1.0, 0.4, -0.5)))
    rest = body_pt(V(0.33, -0.02, 0.92), ro, yaw) + V(0.0, 0.01 * math.sin(w), 0.004 * br)
    up = body_pt(V(0.46, -0.3, 1.36), ro, yaw) + V(0.01 * math.sin(w * 6) * k, 0.0, 0.0)
    wr = rest.lerp(up, k)
    palm = V(-1.0, 0.1, 0.0).lerp(V(0.1, -0.2, 1.0), k)
    fing = V(0.08, -0.12, -1.0).lerp(V(0.5, -0.85, 0.15), k)
    aims.update(open_hand(arm, wr, palm, fing, pole=V(0.4, 1.0, -0.3).lerp(V(1.0, 0.3, -0.6), k)))
    return aims, ro, rz(yaw)


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- combat
C_YAW = -8.0
C_LF, C_RF = (0.18, -0.1), (-0.17, 0.1)
BUTT_C = V(-0.34, -0.42, 0.0)
SD_C = V(-0.04, 0.16, 1.0)
FIN_C = V(-0.3, -1.0, 0.05)
# the left hand raised before his face, palm out, fingers spread up
L_C = (V(0.3, -0.42, 1.42), V(0.1, -1.0, 0.1), V(0.2, -0.2, 1.0))


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    ro = V(0.0, -0.02, -0.03 + 0.006 * br)
    aims = feet(arm, C_YAW, lf=C_LF, rf=C_RF)
    torso(aims, C_YAW, bend=0.06, chest=-3.0 + 2.0 * sw, look=C_YAW + 4.0, pitch=-0.02 + 0.02 * br)
    aims.update(planted(arm, BUTT_C, SD_C, FIN_C, pole=V(-1.0, 0.3, -0.4)))
    wl, palm, fing = L_C
    aims.update(open_hand(arm, wl + V(0.01 * sw, 0.0, 0.012 * br), palm, fing + V(0.06 * sw, 0.0, 0.0), pole=V(1.0, 0.2, -0.6)))
    return aims, ro, rz(C_YAW)


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr = combat_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- attack
def _keyed(keys, f, frames, accel=(1,)):
    i = max(j for j in range(len(keys) - 1) if keys[j][0] <= f) if f < frames else len(keys) - 2
    a, b = keys[i], keys[i + 1]
    k = (f - a[0]) / float(b[0] - a[0])
    k = k * k if i in accel else ease(k)
    return a, b, k


def make_attack(arm, frames=32):
    """Lift the staff (0-6), strike its foot down (6-9: HIT), the left hand sweeping out palm forward (9-14), held
    (14-17), settle back (17-32)."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    keys = [
        # frame, butt, staff dir, knuckles, (left wrist, palm, fingers), bend, chest, root offset
        (0, BUTT_C, SD_C, FIN_C, L_C, 0.06, -3.0, V(0.0, -0.02, -0.03)),
        (6, V(-0.36, -0.32, 0.26), V(-0.06, 0.24, 1.0), V(-0.3, -1.0, 0.1), (V(0.3, -0.2, 1.12), V(0.0, -0.4, 1.0), V(0.3, -1.0, 0.1)),
         -0.06, -9.0, V(0.0, 0.03, 0.0)),
        (HIT, V(-0.32, -0.46, -0.02), V(-0.06, -0.06, 1.0), V(-0.3, -1.0, -0.05), (V(0.32, -0.36, 1.2), V(0.1, -1.0, 0.1), V(0.2, -0.3, 1.0)),
         0.26, 5.0, V(0.0, -0.06, -0.07)),
        (14, V(-0.32, -0.46, -0.02), V(-0.05, -0.04, 1.0), V(-0.3, -1.0, -0.05), (V(0.42, -0.52, 1.34), V(0.15, -1.0, 0.2), V(0.25, -0.35, 1.0)),
         0.16, 4.0, V(0.0, -0.05, -0.05)),
        (17, V(-0.32, -0.46, -0.02), V(-0.05, -0.04, 1.0), V(-0.3, -1.0, -0.05), (V(0.43, -0.53, 1.35), V(0.15, -1.0, 0.2), V(0.25, -0.35, 1.0)),
         0.15, 4.0, V(0.0, -0.05, -0.05)),
        (frames, BUTT_C, SD_C, FIN_C, L_C, 0.06, -3.0, V(0.0, -0.02, -0.03)),
    ]
    for f in range(frames + 1):
        a, b, k = _keyed(keys, f, frames)
        butt = a[1].lerp(b[1], k)
        sd = mixd(a[2], b[2], k)
        fdir = a[3].lerp(b[3], k)
        wl, palm, fing = (a[4][j].lerp(b[4][j], k) for j in range(3))
        bend, chest, ro = lerp(a[5], b[5], k), lerp(a[6], b[6], k), a[7].lerp(b[7], k)
        step = smooth01((f - 5) / 4.0) * (1.0 - smooth01((f - 20) / 10.0))
        aims = feet(arm, C_YAW, lf=(C_LF[0], C_LF[1] - 0.07 * step), rf=C_RF)
        torso(aims, C_YAW, bend=bend, chest=chest, look=C_YAW + 4.0,
              pitch=-0.02 + (0.1 * math.sin(math.pi * min(1.0, f / 6.0)) if f <= 6 else -0.08 * smooth01((f - 6) / 3.0)
                             * (1.0 - smooth01((f - 17) / 10.0))))
        aims.update(planted(arm, butt, sd, fdir, pole=V(-1.0, 0.3, -0.4)))
        aims.update(open_hand(arm, wl, palm, fing, pole=V(1.0, 0.2, -0.6)))
        ch, _ = P.solve(aims, ro, rz(C_YAW))
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- ability: prophecy
A_FR = 58
UP_G, UP_D, UP_F = V(-0.3, -0.12, 1.92), V(0.02, -0.18, 1.0), V(-0.2, -1.0, 0.1)          # the staff raised high, upright
POINT_G, POINT_D, POINT_F = V(-0.26, -0.56, 1.3), V(0.05, -1.0, 0.08), V(0.0, -0.1, 1.0)  # brought down level, the sun forward
L_SKY = (V(0.42, -0.2, 1.62), V(0.1, -0.4, 1.0), V(0.35, -0.3, 1.0))                     # left hand spread to the sky
L_POINT = (V(0.4, -0.44, 1.3), V(0.1, -1.0, 0.0), V(0.3, -0.6, 0.6))


def ability_state(f):
    """(grip, staff dir, knuckles, (left wrist, palm, fingers), bend, pitch, root offset) at frame f."""
    g0 = BUTT_C + SD_C.normalized() * cm.STAFF_BACK
    base = (g0, SD_C.normalized(), FIN_C, L_C, 0.06, -0.02, V(0.0, -0.02, -0.03))
    if f <= 16:                                              # raise the staff high, head back, hand to the sky
        k = ease(f / 16.0)
        return (g0.lerp(UP_G, k), mixd(SD_C, UP_D, k), FIN_C.lerp(UP_F, k), tuple(L_C[j].lerp(L_SKY[j], k) for j in range(3)),
                lerp(0.06, -0.1, k), lerp(-0.02, 0.55, k), V(0.0, -0.02, -0.03).lerp(V(0.0, 0.03, 0.01), k))
    if f <= 26:                                              # the vision: held, trembling
        sh = 0.008 * math.sin((f - 16) * 2.3) * smooth01((f - 17) / 3.0)
        return (UP_G + V(0, 0, sh), UP_D, UP_F, (L_SKY[0] + V(0, 0, -sh), L_SKY[1], L_SKY[2]), -0.1, 0.55, V(0.0, 0.03, 0.01))
    if f <= FLARE:                                           # bring it down level, the sun at the robots
        k = (f - 26) / float(FLARE - 26)
        k = k * k
        return (UP_G.lerp(POINT_G, k), mixd(UP_D, POINT_D, k), UP_F.lerp(POINT_F, k), tuple(L_SKY[j].lerp(L_POINT[j], k) for j in range(3)),
                lerp(-0.1, 0.22, k), lerp(0.55, -0.08, k), V(0.0, 0.03, 0.01).lerp(V(0.0, -0.06, -0.05), k))
    if f <= 40:                                              # held
        sh = 0.006 * math.sin((f - FLARE) * 2.6) * (1.0 - (f - FLARE) / 6.0)
        return (POINT_G + V(0, 0, sh), POINT_D, POINT_F, L_POINT, 0.22, -0.08, V(0.0, -0.06, -0.05))
    k = ease((f - 40) / float(A_FR - 40))                    # settle back into the stance
    return (POINT_G.lerp(g0, k), mixd(POINT_D, SD_C, k), POINT_F.lerp(FIN_C, k), tuple(L_POINT[j].lerp(L_C[j], k) for j in range(3)),
            lerp(0.22, 0.06, k), lerp(-0.08, -0.02, k), V(0.0, -0.06, -0.05).lerp(V(0.0, -0.02, -0.03), k))


def make_ability(arm, frames=A_FR):
    P = Poser(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        g, sd, fin, (wl, palm, fing), bend, pitch, ro = ability_state(f)
        aims = feet(arm, C_YAW, lf=C_LF, rf=C_RF)
        torso(aims, C_YAW, bend=bend, chest=-3.0, look=C_YAW + 4.0, pitch=pitch)
        aims.update(staff_grip(arm, g, sd, fin, pole=V(-1.0, 0.3, -0.4).lerp(V(-1.0, 0.1, -0.8), smooth01(1.0 - abs(f - 20) / 14.0))))
        aims.update(open_hand(arm, wl, palm, fing, pole=V(1.0, 0.2, -0.6)))
        ch, _ = P.solve(aims, ro, rz(C_YAW))
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- cheer
def make_cheer(arm, frames=40):
    """Rank up: two thumps of the staff, then he lifts it high, laughing, his left fist raised."""
    P = Poser(arm)
    act = new_action(arm, "Cheer")
    g0 = BUTT_C + SD_C.normalized() * cm.STAFF_BACK
    for f in range(frames + 1):
        t = f / frames
        thump = max(0.0, math.sin(t * 2 * math.pi * 2.5)) * (1.0 - smooth01((t - 0.35) / 0.1))
        up = smooth01((t - 0.4) / 0.2) * (1.0 - smooth01((t - 0.85) / 0.15))
        g = g0 + V(0.0, 0.0, 0.08 * thump)
        g = g.lerp(UP_G + V(0.0, 0.0, -0.06 + 0.03 * math.sin(t * 20)), up)
        sd = mixd(SD_C, UP_D, up)
        fin = FIN_C.lerp(UP_F, up)
        aims = feet(arm, C_YAW, lf=C_LF, rf=C_RF)
        torso(aims, C_YAW, bend=0.06 - 0.12 * up, chest=-3.0, look=C_YAW + 4.0, pitch=-0.02 + 0.4 * up + 0.04 * math.sin(t * 30) * up)
        aims.update(staff_grip(arm, g, sd, fin, pole=V(-1.0, 0.3, -0.4).lerp(V(-1.0, 0.1, -0.8), up)))
        wl = L_C[0].lerp(V(0.4, -0.16, 1.7), up)
        aims.update(open_hand(arm, wl, L_C[1].lerp(V(0.0, -1.0, 0.2), up), L_C[2].lerp(V(0.2, 0.0, 1.0), up), pole=V(1.0, 0.2, -0.6)))
        ch, _ = P.solve(aims, V(0.0, -0.02, -0.03), rz(C_YAW))
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
