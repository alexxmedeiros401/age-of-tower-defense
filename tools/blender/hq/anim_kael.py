"""Kael Hillwarden's clips (keyed as 30 fps frames; the .glb runs them at 24, game.gd CLIP_FPS).

He has the Javelin Thrower's build, so his Idle, Combat and Attack are the Javelin Thrower's (anim_javelin.py), with his
cloak hanging from two bones aimed in world space: it hangs behind him whichever way he turns, and swings out behind
him as he whips round into a throw.

Ability : Javelin Storm (54 frames). From the poised stance he leans back and hurls his javelin almost straight up into
          the sky (it leaves his hand at A_RELEASE: game.gd sends one up from there, then the storm comes down on the
          robots), watches it climb, flings his left arm up after it and sweeps it down at the robots; then draws a
          fresh javelin from the case and swings it round into the poised stance again.
Cheer   : (rank up) the javelin thrust up overhead and shaken, his left fist pumping, a little hop, head back."""
import math
from mathutils import Vector, Quaternion
import javelin as cm
import anim_javelin as AJ
from anim_javelin import (V, vec, rz, body_pt, jav_grip, open_hand, feet, torso, smooth01, mixd, bez_d, bez_p, key_constant,
                          C_YAW, C_FEET, POISE_G, JDIR, POISE_FING, POISE_POLE, AIM_L, AIM_PALM, AIM_FING, GRAB, CASE_AX,
                          CASE_FING, PULL, RELEASE, FRESH, FR, throw_state, idle_pose, combat_pose)
from rig import Poser, leg_aims, arm_aims
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J


def cape_aims(q, back=0.08, side=0.0, wave=0.0):
    """World-space aims for the cloak's bones (`q`: the body's yaw): hanging behind him, pushed out by `back`, swung
    sideways by `side`, rippling by `wave`."""
    return {"cape.1": q @ V(side * 0.6, 0.1 + back, -1.0),
            "cape.2": q @ V(side + wave * 0.1, 0.06 + back * 1.3 + abs(wave) * 0.04, -1.0)}


# ---------------------------------------------------------------------------------------------- idle, combat
def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        t = (f % frames) / frames
        aims, ro, rr = idle_pose(arm, t)
        w = 2 * math.pi * t
        aims.update(cape_aims(rr, back=0.05 + 0.01 * math.sin(w * 2), side=0.02 * math.sin(w), wave=0.4 * math.sin(w * 3 + 0.5)))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        t = (f % frames) / frames
        aims, ro, rr = combat_pose(arm, t)
        w = 2 * math.pi * t
        aims.update(cape_aims(rr, back=0.1 + 0.015 * math.sin(w * 2), side=0.015 * math.sin(w), wave=0.35 * math.sin(w * 2 + 0.8)))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- attack: the throw
def throw_yaw(f):
    return throw_state(min(max(f, 0), FR), V(0, 0, 0))[0]


def make_attack(arm, frames=FR):
    """The Javelin Thrower's throw; the cloak lags the turn and flies out behind him as he whips round."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        crouch = throw_state(f, V(0, 0, 0))[3]
        ro = V(0.0, -0.06 * smooth01(f / 4.0) * (1 - smooth01((f - 9) / 8.0)), -crouch)
        yaw, chest, bend, _c, g, jd, fing, pole, wl, heel = throw_state(f, ro)
        aims = feet(arm, C_YAW, lift=(0.0, heel), **C_FEET)
        torso(aims, yaw, bend=bend, chest=chest, look=0.0 if f < 10 or f > 19 else lerp(0.0, -30.0, math.sin(math.pi * (f - 10) / 9.0)),
              pitch=0.04 - 0.1 * bend)
        aims.update(jav_grip(arm, g, jd, fing, pole))
        lk = smooth01((f - RELEASE) / 4.0) * (1.0 - smooth01((f - 18) / 6.0))
        aims.update(open_hand(arm, wl, mixd(AIM_PALM, V(-0.9, 0.2, -0.3), lk), mixd(AIM_FING, V(0.1, -0.4, -0.9), lk),
                              pole=V(0.9, 0.2, -0.6)))
        lag = throw_yaw(f - 2)                                    # the cloak follows the turn a beat late
        spin = abs(yaw - throw_yaw(f - 1))
        fly = min(1.0, spin / 14.0)
        side = max(-1.0, min(1.0, (yaw - lag) / 30.0)) * -0.35
        aims.update(cape_aims(rz(lag), back=0.1 + 0.3 * fly + 0.12 * bend, side=side, wave=0.5 * math.sin(f * 0.6)))
        sc = {"javelin": 0.0 if RELEASE <= f < FRESH else 1.0}
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    key_constant(act, 'pose.bones["javelin"].scale')
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- ability: javelin storm
A_FR = 54
A_WIND = 12            # leaning back, the javelin tilted up at the sky
A_RELEASE = 15         # it leaves his hand, going up
A_FOL = 22
A_UP = 30              # his left arm flung up after it
A_SWEEP = 36           # ...and swept down at the robots
A_GRAB = 42            # a fresh javelin in his hand at the case's mouth
A_DRAW = 46
W_G = V(-0.36, 0.5, 1.46)                   # wound up: the grip low behind his head, the javelin pointing up
W_DIR = V(0.04, -0.42, 0.9)
W_FING = V(0.1, 0.55, 0.85)
UP_G = V(-0.2, -0.12, 2.0)                  # the release: high above him
UP_DIR = V(0.0, -0.3, 0.95)
UP_FING = V(0.0, -0.1, 1.0)
FOLA_G = V(-0.12, -0.42, 1.36)              # the follow-through, down in front of him
FOLA_FING = V(0.3, -0.2, -0.9)
SKY_L = V(0.2, -0.3, 1.9)                   # his left arm up at the sky
SKY_PALM, SKY_FING = V(0.0, -0.6, 0.0), V(0.05, -0.3, 1.0)


def ability_state(f, ro):
    """(yaw, chest twist, bend, crouch, grip, javelin dir, fingers, arm pole, left wrist, left palm, left fingers,
    head pitch) at frame f (the robots' frame)."""
    reach_l = (AIM_L, AIM_PALM, AIM_FING)
    if f <= A_WIND:                                       # lean back, the javelin tilts up; his left arm rises
        k = ease(f / float(A_WIND))
        return (lerp(C_YAW, -55.0, k), lerp(-14.0, -20.0, k), lerp(-0.04, -0.2, k), lerp(0.06, 0.1, k), POISE_G.lerp(W_G, k) + ro,
                mixd(JDIR, W_DIR, k), mixd(POISE_FING, W_FING, k), POISE_POLE.lerp(V(-0.6, 0.6, -0.5), k),
                AIM_L.lerp(SKY_L, k * 0.7) + ro, mixd(AIM_PALM, SKY_PALM, k), mixd(AIM_FING, SKY_FING, k), lerp(0.04, 0.4, k))
    if f <= A_RELEASE:                                    # the whip: up and over, the javelin leaves his hand going up
        k = ((f - A_WIND) / float(A_RELEASE - A_WIND)) ** 1.3
        g = W_G.lerp(UP_G, k) + V(0, -0.06 * math.sin(math.pi * k), 0.05 * math.sin(math.pi * k)) + ro
        return (lerp(-55.0, -5.0, k), lerp(-20.0, 6.0, k), lerp(-0.2, -0.06, k), lerp(0.1, 0.04, k), g, mixd(W_DIR, UP_DIR, k),
                mixd(W_FING, UP_FING, k), V(-0.6, 0.6, -0.5).lerp(V(-0.8, -0.1, -0.6), k), SKY_L.lerp(V(0.36, -0.1, 1.34), k) + ro,
                mixd(SKY_PALM, V(-0.6, 0.0, -0.8), k), mixd(SKY_FING, V(0.2, -0.6, -0.6), k), lerp(0.4, 0.6, k))
    if f <= A_FOL:                                        # follow through; he watches it climb
        k = ease((f - A_RELEASE) / float(A_FOL - A_RELEASE))
        return (lerp(-5.0, 8.0, k), lerp(6.0, 10.0, k), lerp(-0.06, 0.06, k), lerp(0.04, 0.07, k), (UP_G + ro).lerp(FOLA_G + ro, k),
                mixd(UP_DIR, V(0.3, -0.8, -0.5), k), mixd(UP_FING, FOLA_FING, k), V(-0.8, -0.1, -0.6).lerp(V(-0.6, -0.5, -0.5), k),
                V(0.36, -0.1, 1.34) + ro, V(-0.6, 0.0, -0.8), V(0.2, -0.6, -0.6), lerp(0.6, 0.75, k))
    if f <= A_UP:                                         # his left arm flung up after it
        k = ease((f - A_FOL) / float(A_UP - A_FOL))
        return (lerp(8.0, -20.0, k), lerp(10.0, -6.0, k), lerp(0.06, -0.08, k), lerp(0.07, 0.04, k), FOLA_G.lerp(V(-0.34, -0.12, 1.08), k) + ro,
                V(0.3, -0.8, -0.5), mixd(FOLA_FING, V(0.2, -0.5, -0.8), k), V(-0.6, -0.5, -0.5).lerp(V(-0.8, 0.3, -0.4), k),
                V(0.36, -0.1, 1.34).lerp(SKY_L + V(0.04, 0.0, 0.08), k) + ro, mixd(V(-0.6, 0.0, -0.8), SKY_PALM, k),
                mixd(V(0.2, -0.6, -0.6), SKY_FING, k), lerp(0.75, 0.55, k))
    if f <= A_SWEEP:                                      # ...and swept down at the robots: the storm comes down on them
        k = ease((f - A_UP) / float(A_SWEEP - A_UP))
        mid = V(0.24, -0.62, 1.86)
        return (lerp(-20.0, C_YAW, k), lerp(-6.0, -10.0, k), lerp(-0.08, 0.1, k), lerp(0.04, 0.09, k), V(-0.34, -0.12, 1.08) + ro,
                V(0.3, -0.8, -0.5), V(0.2, -0.5, -0.8), V(-0.8, 0.3, -0.4), bez_p(SKY_L + V(0.04, 0.0, 0.08), mid, AIM_L + V(0, -0.04, -0.06), k) + ro,
                mixd(SKY_PALM, AIM_PALM, k), mixd(SKY_FING, AIM_FING, k), lerp(0.55, 0.02, k))
    yaw_r = -10.0
    grab = body_pt(GRAB, ro, yaw_r)
    case_d = rz(yaw_r) @ CASE_AX
    case_f = rz(yaw_r) @ CASE_FING
    case_pole = rz(yaw_r) @ V(0.1, -0.6, 1.0)
    lw = AIM_L + V(0, -0.04, -0.06)
    if f <= A_GRAB:                                       # reach back over his shoulder to the case
        k = ease((f - A_SWEEP) / float(A_GRAB - A_SWEEP))
        g = bez_p(V(-0.34, -0.12, 1.08) + ro, V(-0.42, -0.1, 1.5) + ro, grab, k)
        return (lerp(C_YAW, yaw_r, k), lerp(-10.0, 0.0, k), lerp(0.1, 0.06, k), lerp(0.09, 0.05, k), g, mixd(V(0.3, -0.8, -0.5), case_d, k),
                mixd(V(0.2, -0.5, -0.8), case_f, k), V(-0.8, 0.3, -0.4).lerp(case_pole, k), lw.lerp(V(0.3, -0.34, 1.3), k) + ro,
                AIM_PALM, AIM_FING, lerp(0.02, 0.0, k))
    if f <= A_DRAW:                                       # draw it up out of the case
        k = ease((f - A_GRAB) / float(A_DRAW - A_GRAB))
        return (yaw_r, 0.0, 0.06, 0.05, grab + case_d * (PULL * k), case_d, case_f, case_pole, V(0.3, -0.34, 1.3) + ro,
                AIM_PALM, AIM_FING, 0.0)
    k = ease((f - A_DRAW) / float(A_FR - A_DRAW))         # swing it round over his head into the poised stance
    top = grab + case_d * PULL
    g = bez_p(top, V(-0.32, 0.3, 1.86) + ro, POISE_G + ro, k)
    return (lerp(yaw_r, C_YAW, k), lerp(0.0, -14.0, k), lerp(0.06, -0.04, k), lerp(0.05, 0.06, k), g,
            bez_d(case_d, V(0.0, -0.35, 1.0), JDIR, k), bez_d(case_f, V(0.1, 0.9, 0.4), POISE_FING, k),
            case_pole.lerp(POISE_POLE, k), V(0.3, -0.34, 1.3).lerp(AIM_L, k) + ro, AIM_PALM, AIM_FING, lerp(0.0, 0.04, k))


def ability_yaw(f):
    return ability_state(min(max(f, 0), A_FR), V(0, 0, 0))[0]


def make_ability(arm, frames=A_FR):
    P = Poser(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        crouch = ability_state(f, V(0, 0, 0))[3]
        ro = V(0.0, 0.05 * smooth01(f / 10.0) * (1 - smooth01((f - A_WIND) / 3.0)), -crouch)
        yaw, chest, bend, _c, g, jd, fing, pole, wl, lpalm, lfing, pitch = ability_state(f, ro)
        heel = 0.05 * smooth01((f - A_WIND) / 3.0) * (1 - smooth01((f - A_FOL) / 6.0))
        aims = feet(arm, C_YAW, lift=(0.0, heel), **C_FEET)
        torso(aims, yaw, bend=bend, chest=chest, look=lerp(0.0, -20.0, smooth01((f - A_RELEASE) / 6.0)) if f < A_SWEEP else 0.0,
              pitch=pitch)
        aims.update(jav_grip(arm, g, jd, fing, pole))
        aims.update(open_hand(arm, wl, lpalm, lfing, pole=V(0.9, 0.2, -0.6)))
        lag = ability_yaw(f - 2)
        spin = abs(yaw - ability_yaw(f - 1))
        fly = min(1.0, spin / 14.0)
        side = max(-1.0, min(1.0, (yaw - lag) / 30.0)) * -0.35
        aims.update(cape_aims(rz(lag), back=0.08 + 0.3 * fly + 0.1 * max(0.0, bend) + 0.08 * max(0.0, -bend), side=side,
                              wave=0.5 * math.sin(f * 0.5)))
        sc = {"javelin": 0.0 if A_RELEASE <= f < A_GRAB else 1.0}
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    key_constant(act, 'pose.bones["javelin"].scale')
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- cheer
CHEER_G = V(-0.36, -0.08, 1.98)              # the javelin thrust up overhead in his right fist


def make_cheer(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        t = f / frames
        up = smooth01(t / 0.18) * (1 - smooth01((t - 0.82) / 0.18))
        pump = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.4)) * up
        hop = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.9)) * 0.04 * up
        yaw = -6.0 + 6.0 * math.sin(t * math.pi)
        ro = V(0.0, 0.0, -0.02 + hop)
        aims = feet(arm, yaw, lf=(0.2, -0.04), rf=(-0.19, 0.05), turn=(10.0, -12.0), lift=(hop * 0.5, hop * 0.5))
        torso(aims, yaw, bend=-0.04 - 0.06 * pump, side=0.03 * up, chest=4.0 * math.sin(t * 2 * math.pi * 2), look=yaw,
              pitch=0.04 + 0.45 * up * (0.6 + 0.4 * pump))
        idle_aims, idle_ro, idle_rr = idle_pose(arm, 0.0)
        g0 = body_pt(AJ.IDLE_G, ro, yaw)
        shake = 0.05 * math.sin(t * 2 * math.pi * 4) * up
        g = g0.lerp(CHEER_G + ro + V(0, 0, shake), up)
        jd = mixd(rz(yaw) @ AJ.IDLE_DIR, V(0.05, -0.15, 1.0), up)
        fing = mixd(rz(yaw) @ AJ.IDLE_FING, V(0.1, -1.0, 0.1), up)
        aims.update(jav_grip(arm, g, jd, fing, pole=rz(yaw) @ V(-0.8, 0.5, -0.4).lerp(V(-1.0, 0.3, -0.2), up)))
        wl = body_pt(AJ.HIP_L, ro, yaw).lerp(V(0.44, -0.1, 1.42 + 0.42 * pump), up)
        aims.update(open_hand(arm, wl, mixd(rz(yaw) @ V(-1.0, 0.15, 0.0), V(-0.2, -1.0, 0.0), up),
                              mixd(rz(yaw) @ V(0.05, -0.5, -0.86), V(0.0, 0.2, 1.0), up), pole=V(1.0, 0.3, -0.5)))
        aims.update(cape_aims(rz(yaw), back=0.06 + 0.1 * hop / 0.04, side=0.03 * math.sin(t * 7), wave=0.6 * math.sin(t * 12)))
        ch, _ = P.solve(aims, ro, rz(yaw))
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
