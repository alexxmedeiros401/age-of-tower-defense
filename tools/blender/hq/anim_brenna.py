"""Brenna's clips (keyed as 30 fps; the .glb runs them at 24, game.gd CLIP_FPS).

Idle    : standing easy, the spear planted upright at her right side, the shield resting on her left arm; she breathes,
          shifts her weight and looks about.
Combat  : the shield wall's stance: left foot forward, knees bent, the shield up before her (her eyes over its rim), the
          spear overhand above her shoulder pointing at the robots; a slow bob.
Attack  : (21 frames: inside the 0.7 s cooldown) she draws the spear back (0-4) and drives a lunging overhand thrust past
          the shield's edge: full reach at THRUST (frame 6: game.gd's spear-flash for the robots it hits), a moment's
          hold, and she recovers into the stance.
Ability : War Cry (48 frames): she beats her spear's shaft on her shield twice (CLASH frames 11 and 19), then flings
          both up, the spear's point at the sky and the shield high, throws back her head and roars (ROAR, frame 26:
          game.gd's war cry rolls out over the towers); she settles back into the stance.
Cheer   : (rank up) the spear thrust up overhead twice, the shield raised, a hop.

The spear and the shield are rigid in her fists ("frame" aims): the spear along the right fist's thumb axis, the
shield's grip in the left fist with its face along the knuckles."""
import math
from mathutils import Vector, Quaternion
import brenna as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
ROOT = Vector(J["root"])

T_REST = Vector(cm.spear_axis()[1])
_wr, _f, _n, _t = cm.hand_frame("R")
F_REST = Vector(_f)
FIST_OFF_R = Vector(cm.fist_center("R") - _wr)
_G, _N, _U, _S = cm.shield_frame()
G_REST, N_REST, U_REST = Vector(_G), Vector(_N), Vector(_U)
WR_L_REST = Vector(J["wrist_L"])
BACK, FWD = cm.SPEAR_BACK, cm.SPEAR_FWD
THRUST = 6             # game.gd ATTACK_FRAME: the spear at full reach
CLASH = (11, 19)       # the shaft strikes the shield
ROAR = 26              # the war cry (game.gd BRENNA_ROAR)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def spear_grip(arm, grip, spear_dir, finger, pole):
    """Right fist (its grip centre) at `grip`, the spear along `spear_dir`, the fist's knuckles toward `finger`."""
    sd = Vector(spear_dir).normalized()
    R = frame_map(T_REST, sd, F_REST, Vector(finger))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF_R, pole=pole)
    aims["hand.R"] = ("frame", T_REST, sd, F_REST, Vector(finger))
    return aims


def shield_hold(arm, fist, normal, up, pole):
    """Left fist at `fist` holding the shield's grip, its face toward `normal`, the grip along `up`."""
    nrm = Vector(normal).normalized()
    R = frame_map(N_REST, nrm, U_REST, Vector(up))
    aims = arm_aims(arm, "L", Vector(fist) - R @ (G_REST - WR_L_REST), pole=pole)
    aims["hand.L"] = ("frame", N_REST, nrm, U_REST, Vector(up))
    return aims


def legs(arm, yaw, lf=(0.19, -0.1), rf=(-0.19, 0.13), lift_l=0.0, lift_r=0.0, open_feet=0.6):
    q = rz(yaw)
    aims = {}
    for side, (bx, by), lift in (("L", lf, lift_l), ("R", rf, lift_r)):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + lift)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = Vector(J["toe_" + side]) - Vector(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * open_feet + (-12 if side == "R" else 6)) @ rest_foot
    return aims


def torso(aims, yaw_chest, lean=0.0, side=0.0, spine_tw=0.0, chest_tw=0.0, neck_tw=0.0, head_tw=0.0, head_tilt=0.0,
          head_up=0.0):
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.22 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.32 * lean, 1.0), chest_tw)
    aims["neck"] = (V(0.0, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


def mixd(a, b, k):
    return a.normalized().lerp(b.normalized(), k).normalized()


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ----------------------------------------------------------------------------------------------- idle
BUTT_IDLE = V(-0.35, -0.1, 0.0)
SD_IDLE = V(-0.05, 0.03, 1.0)
SH_IDLE = V(0.42, -0.05, 0.86)
SH_IDLE_N, SH_IDLE_U = V(0.85, -0.45, 0.05), V(0.02, -0.12, 1.0)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm, -4.0, lf=(0.18, -0.02), rf=(-0.18, 0.07), open_feet=0.3)
    ro = V(0.012 * math.sin(w), 0.0, -0.006 + 0.005 * br)
    rr = rz(-4.0 + 2.0 * math.sin(w))
    look = 0.45 * math.sin(w) + 0.12 * math.sin(w * 3)
    torso(aims, -4.0, lean=-0.02, side=0.02 * math.sin(w), spine_tw=0.03 * math.sin(w), chest_tw=0.05 * math.sin(w),
          neck_tw=0.3 * look, head_tw=0.7 * look, head_up=0.06 + 0.04 * br)
    q = rz(-4.0)
    aims["clavicle.L"] = q @ V(1.0, 0.0, 0.0)
    aims["clavicle.R"] = q @ V(-1.0, 0.0, 0.04)
    sd = SD_IDLE.normalized()
    grip = BUTT_IDLE + sd * BACK
    aims.update(spear_grip(arm, grip + V(0, 0, 0.004 * br), sd, V(0.25, -1.0, -0.25), pole=V(-1.0, 0.5, -0.4)))
    aims.update(shield_hold(arm, SH_IDLE + V(0, 0, 0.006 * math.sin(w * 2 + 0.7)), SH_IDLE_N, SH_IDLE_U, pole=V(1.0, 0.4, -0.3)))
    return aims, ro, rr


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- the shield wall's stance
YAW = -22.0
STANCE_GRIP = V(-0.33, 0.07, 1.6)        # beside her head, above the right shoulder: the spear clear of her face
STANCE_DIR = V(-0.04, -1.0, -0.13)
STANCE_FINGER = V(0.25, -0.45, 0.85)
SPEAR_POLE = V(-1.0, 0.35, -0.25)
SH_FIST = V(0.18, -0.42, 1.06)
SH_NORMAL = V(0.12, -1.0, 0.08)
SH_UP = V(0.05, 0.08, 1.0)
SH_POLE = V(1.0, 0.1, -0.6)
RO0 = V(0.0, 0.0, -0.042)                # the stance's root offset (its grips are placed for it)


def stance(arm, br=0.0, sway=0.0, lunge=0.0, crouch=0.0, chest=0.0, lift_l=0.0, lf_fwd=0.0, head_up=0.0, lean=0.0):
    aims = legs(arm, YAW, lf=(0.2, -0.16 - lf_fwd), rf=(-0.2, 0.19), lift_l=lift_l)
    q = rz(YAW)
    ro = q @ V(0.0, -0.15 * lunge, 0.0) + V(0.0, 0.0, -0.042 - 0.03 * crouch - 0.05 * lunge + 0.004 * br)
    rr = rz(YAW + 1.5 * sway)
    torso(aims, YAW + chest, lean=0.12 + 0.18 * lunge + lean, side=0.02 * sway, spine_tw=math.radians(chest * 0.4),
          chest_tw=math.radians(chest * 0.6), neck_tw=math.radians(-0.4 * (YAW + chest)), head_tw=math.radians(-0.6 * (YAW + chest)),
          head_up=0.1 + 0.05 * lunge + head_up)
    qc = rz(YAW + chest)
    aims["clavicle.L"] = qc @ V(1.0, -0.15, 0.06)
    aims["clavicle.R"] = qc @ V(-1.0, 0.02, 0.24)
    return aims, ro, rr


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    aims, ro, rr = stance(arm, br, sw)
    bob = V(0.0, 0.0, 0.008 * br)
    aims.update(spear_grip(arm, STANCE_GRIP + bob + V(0.004 * sw, 0, 0), (STANCE_DIR + V(0.02 * sw, 0, 0.01 * br)).normalized(),
                           STANCE_FINGER, SPEAR_POLE))
    aims.update(shield_hold(arm, SH_FIST + bob * 0.6, SH_NORMAL, SH_UP, SH_POLE))
    return aims, ro, rr


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr = combat_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- the thrust
def make_attack(arm, frames=21):
    """Draw back (0-4), lunge and thrust (4-6, full reach at THRUST), hold (6-9), recover (9-21)."""
    P = Poser(arm)
    act = new_action(arm, "Attack")
    back_grip, back_dir = V(-0.34, 0.3, 1.66), V(-0.03, -1.0, -0.08)
    out_grip, out_dir = V(-0.22, -0.48, 1.45), V(0.0, -1.0, -0.17)
    keys = [
        (0, STANCE_GRIP, STANCE_DIR, 0.0, 0.0, 0.0, V(0, 0, 0), 0.0),
        (4, back_grip, back_dir, -0.25, 0.4, -12.0, V(0.0, -0.04, 0.0), 0.0),
        (THRUST, out_grip, out_dir, 1.0, 0.3, 10.0, V(0.1, 0.12, -0.04), 0.07),
        (9, out_grip + V(0.0, -0.03, -0.01), out_dir, 1.05, 0.3, 11.0, V(0.1, 0.12, -0.04), 0.07),
        (frames, STANCE_GRIP, STANCE_DIR, 0.0, 0.0, 0.0, V(0, 0, 0), 0.0),
    ]
    for f in range(frames + 1):
        i = max(k for k in range(len(keys) - 1) if keys[k][0] <= f) if f < frames else len(keys) - 2
        a, b = keys[i], keys[i + 1]
        k = (f - a[0]) / float(b[0] - a[0])
        k = k * k if i == 1 else ease(k)
        grip = a[1].lerp(b[1], k)
        sd = a[2].normalized().lerp(b[2].normalized(), k).normalized()
        lunge, crouch, chest = lerp(a[3], b[3], k), lerp(a[4], b[4], k), lerp(a[5], b[5], k)
        sh_off = a[6].lerp(b[6], k)
        fwd = lerp(a[7], b[7], k)
        aims, ro, rr = stance(arm, 0.0, 0.0, lunge=lunge, crouch=crouch, chest=chest, lf_fwd=fwd,
                              lift_l=0.03 * math.sin(math.pi * min(1.0, max(0.0, (f - 3) / 4.0))))
        body = rz(YAW) @ V(0.0, -0.15 * lunge, -0.05 * lunge)
        aims.update(spear_grip(arm, grip, sd, STANCE_FINGER.lerp(V(0.1, -0.85, 0.5), max(0.0, min(1.0, lunge))), SPEAR_POLE))
        aims.update(shield_hold(arm, SH_FIST + body + sh_off, SH_NORMAL, SH_UP, SH_POLE))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- ability: war cry
A_FR = 48
BEAT_UP_G, BEAT_UP_D = V(-0.36, -0.12, 1.62), V(0.35, -0.3, 0.89)       # the spear raised, its shaft cocked to strike
BEAT_G, BEAT_D = V(-0.24, -0.42, 1.2), V(0.88, -0.1, 0.46)              # the shaft across the shield's face
BEAT_FING_UP, BEAT_FING = V(0.2, -0.9, 0.3), V(0.0, -0.6, -0.8)
SH_BEAT, SH_BEAT_N, SH_BEAT_U = V(0.12, -0.36, 1.12), V(-0.2, -1.0, 0.12), V(0.05, 0.1, 1.0)
CRY_G, CRY_D, CRY_FING = V(-0.36, -0.04, 1.96), V(-0.06, -0.12, 1.0), V(0.15, -1.0, 0.1)   # the spear up at the sky
SH_CRY, SH_CRY_N, SH_CRY_U = V(0.42, -0.2, 1.64), V(0.6, -0.75, 0.25), V(0.2, 0.15, 1.0)  # the shield flung up high


def ability_state(f):
    """(grip, spear dir, fingers, shield fist, its normal, its up, lean, head up, crouch, chest twist) at frame f."""
    c1, c2 = CLASH
    if f <= 8:                                              # raise the spear, bring the shield across
        k = ease(f / 8.0)
        return (STANCE_GRIP.lerp(BEAT_UP_G, k), mixd(STANCE_DIR, BEAT_UP_D, k), mixd(STANCE_FINGER, BEAT_FING_UP, k),
                SH_FIST.lerp(SH_BEAT, k), mixd(SH_NORMAL, SH_BEAT_N, k), mixd(SH_UP, SH_BEAT_U, k), 0.0, 0.0, 0.0, lerp(0.0, -8.0, k))
    if f <= c2:                                             # two blows of the shaft on the shield
        if f <= c1:
            k = ((f - 8) / float(c1 - 8)) ** 2
        elif f <= c1 + 4:
            k = 1.0 - ease((f - c1) / 4.0)
        else:
            k = ((f - c1 - 4) / float(c2 - c1 - 4)) ** 2
        return (BEAT_UP_G.lerp(BEAT_G, k), mixd(BEAT_UP_D, BEAT_D, k), mixd(BEAT_FING_UP, BEAT_FING, k), SH_BEAT, SH_BEAT_N, SH_BEAT_U,
                0.08 * k, 0.0, 0.2 * k, lerp(-8.0, 6.0, k))
    if f <= ROAR:                                           # fling them both up, throw back her head
        k = ease((f - c2) / float(ROAR - c2))
        return (BEAT_G.lerp(CRY_G, k), mixd(BEAT_D, CRY_D, k), mixd(BEAT_FING, CRY_FING, k), SH_BEAT.lerp(SH_CRY, k),
                mixd(SH_BEAT_N, SH_CRY_N, k), mixd(SH_BEAT_U, SH_CRY_U, k), lerp(0.08, -0.22, k), lerp(0.0, 0.85, k), lerp(0.2, -0.3, k),
                lerp(6.0, 0.0, k))
    if f <= 38:                                             # the roar: held, shaking with it
        sh = 0.012 * math.sin((f - ROAR) * 2.4)
        return (CRY_G + V(0, 0, sh), CRY_D, CRY_FING, SH_CRY + V(0, 0, -sh), SH_CRY_N, SH_CRY_U, -0.22, 0.85, -0.3, 0.0)
    k = ease((f - 38) / float(A_FR - 38))                   # back into the stance
    return (CRY_G.lerp(STANCE_GRIP, k), mixd(CRY_D, STANCE_DIR, k), mixd(CRY_FING, STANCE_FINGER, k), SH_CRY.lerp(SH_FIST, k),
            mixd(SH_CRY_N, SH_NORMAL, k), mixd(SH_CRY_U, SH_UP, k), lerp(-0.22, 0.0, k), lerp(0.85, 0.0, k), lerp(-0.3, 0.0, k), 0.0)


def make_ability(arm, frames=A_FR):
    P = Poser(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        g, sd, fing, shf, shn, shu, lean, hup, crouch, chest = ability_state(f)
        aims, ro, rr = stance(arm, 0.0, 0.0, crouch=crouch, chest=chest, head_up=hup, lean=lean)
        d = ro - RO0
        aims.update(spear_grip(arm, g + d, sd, fing, SPEAR_POLE))
        aims.update(shield_hold(arm, shf + d, shn, shu, SH_POLE.lerp(V(1.0, 0.3, -0.2), smooth01((f - CLASH[1]) / 6.0))))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- cheer
def make_cheer(arm, frames=40):
    """Rank up: the spear thrust up overhead twice, the shield raised, a hop."""
    P = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        t = f / frames
        up = smooth01(t / 0.15) * (1 - smooth01((t - 0.82) / 0.18))
        pump = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.4)) * up
        hop = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.9)) * 0.04 * up
        aims, ro, rr = stance(arm, 0.0, 0.0, crouch=-0.4 * up, head_up=0.5 * up, lean=-0.1 * up)
        ro = ro + V(0.0, 0.0, hop)
        d = ro - RO0
        g = STANCE_GRIP.lerp(CRY_G + V(0.0, 0.0, 0.1 * pump - 0.06), up)
        aims.update(spear_grip(arm, g + d, mixd(STANCE_DIR, CRY_D, up), mixd(STANCE_FINGER, CRY_FING, up), SPEAR_POLE))
        shf = SH_FIST.lerp(SH_CRY + V(0.0, 0.0, -0.08 + 0.06 * pump), up)
        aims.update(shield_hold(arm, shf + d, mixd(SH_NORMAL, SH_CRY_N, up), mixd(SH_UP, SH_CRY_U, up), SH_POLE.lerp(V(1.0, 0.3, -0.2), up)))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
