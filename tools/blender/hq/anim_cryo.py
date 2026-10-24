"""Cryo Field clips (game: 24 fps).

Idle   : the lever raised, the field idling (the coil bars half lit and breathing, the core pulsing softly); he stands easy,
         his right arm at his side, turns to the tank on his left, leans in and reads the near gauge, taps its glass
         twice with his knuckles (a small nod), pats the dome, turns back to the field and glances up at the projector.
Combat : his right fist on the lever's grip, his left fist on his hip, turned a little toward the pedestal, watching the
         robots.
Attack : (33 frames, inside the 1.4 s cooldown) the field charges (frames 0-8: the coil bars fill their windows, the core
         swells and flickers, the mast hums) while he hauls the lever up past its rest (anticipation, his shoulders up);
         he slams it down onto the panel: the pulse goes out at PULSE (frame 10, the lever held down to 13: the game draws
         the frost rings from the core there); the core flares, the bars drop to nothing, the mast shudders and rings down,
         the tank vents a puff of cold vapour from its stack, he ducks his head from the blast; then the bars creep back,
         he lets the lever ride back up under his fist and settles into the Combat pose.

The machine never moves (`machine`); the mast wobbles about its foot ("rot" aims), the core (`core`) scales, the bars
(`coils`, along their length), the lever turns about SW at its pivot, the vapour (`vapour`) grows from the vent's mouth.
His right fist is placed with a "frame" aim on the lever's grip (overhand: the thumb along the grip toward his left, the
palm down), the knuckles following the solved forearm."""
import math
from mathutils import Vector, Quaternion, Matrix
import cryo as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease
from anim_emp import rz, body_pt, smooth_keys, perp, feet, torso, grip, hip_l, solve_r

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

SN, SU, SW = vec(cm.SN), vec(cm.SU), vec(cm.SW)
LEV_PIV = vec(cm.LEV_PIV)
GAUGE = vec(cm.GAUGE_PTS[0])                 # the near gauge's dial (the one he taps)
GAUGE_N = vec(cm.GAUGE_N)
DOME = vec(cm.MAST_C) + vec(cm.GAUGE_D) * 0.12 + V(0, 0, cm.dome_z(0.12))

# ---------------------------------------------------------------------------------------------- timing (24 fps)
PULSE = 10         # game.gd ATTACK_FRAME: the lever hits the panel, the pulse goes out (held down to frame 13)
FR = 33            # <= 1.4 s
HIDE = 0.001       # the vapour's scale when it is not venting


def lever_pt(deg):
    """The grip's middle with the lever at `deg` up from the panel."""
    return LEV_PIV + vec(cm.lever_dir(deg)) * cm.LEV_L


# ---------------------------------------------------------------------------------------------- the machine
def machine_aims(aims, lever=cm.LEV_UP, wobble=(0.0, 0.0)):
    """lever: its angle up from the panel (deg); wobble: the mast's tilt (deg) about two horizontal axes."""
    aims["lever"] = ("rot", Quaternion(SW, math.radians(lever - cm.LEV_UP)))
    q = Quaternion((1, 0, 0), math.radians(wobble[0])) @ Quaternion((0, 1, 0), math.radians(wobble[1]))
    aims["mast"] = ("rot", q)


def machine_scales(bars=0.55, core=1.0, vapour=HIDE):
    v = max(HIDE, vapour)
    return {"coils": (1.0, max(0.05, bars), 1.0), "core": core, "vapour": (v * 0.9, v * 1.15, v * 0.9)}


def grip_solve(P, arm, aims, ro, rr, sc, deg, pole, left=None):
    """His right fist round the lever's grip at `deg` (overhand: the thumb along +SW, the palm down onto it)."""
    return solve_r(P, arm, aims, ro, rr, sc, lever_pt(deg), SW, pole, -SU, left=left)


# ---------------------------------------------------------------------------------------------- idle
I_FEET = ((0.17, 0.06), (-0.19, 0.01))
I_YAW = -8.0
I_RO = V(0.0, 0.0, -0.01)


def gauge_fist(t_in):
    """His left fist before the near gauge: t_in 0 (hovering) .. 1 (the knuckles on the glass)."""
    return GAUGE + GAUGE_N * (0.085 - 0.03 * t_in)


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br = math.sin(w * 3)
        turn = smooth_keys([(0.0, 0.0), (0.1, 0.0), (0.24, 1.0), (0.6, 1.0), (0.72, 0.0), (1.0, 0.0)], t)
        reach = smooth_keys([(0.0, 0.0), (0.14, 0.0), (0.28, 1.0), (0.5, 1.0), (0.56, 0.75), (0.6, 0.0), (1.0, 0.0)], t)
        pat = smooth_keys([(0.0, 0.0), (0.5, 0.0), (0.54, 1.0), (0.58, 1.0), (0.62, 0.0), (1.0, 0.0)], t)
        # two taps on the glass
        tap = 0.0
        for tc in (0.34, 0.42):
            if abs(t - tc) < 0.035:
                tap = max(tap, math.cos(math.pi * (t - tc) / 0.07) ** 2)
        up = smooth_keys([(0.0, 0.0), (0.76, 0.0), (0.83, 1.0), (0.91, 1.0), (0.97, 0.0), (1.0, 0.0)], t)
        nod = 0.06 * math.sin(math.pi * min(1.0, max(0.0, (t - 0.44) / 0.06))) if 0.44 < t < 0.5 else 0.0
        yaw = I_YAW + 26.0 * turn + 1.5 * math.sin(w)
        ro = I_RO + V(0.0, 0.0, 0.004 * br) + V(0.015, 0.01, -0.012) * turn
        aims = feet(arm, I_FEET[0], I_FEET[1], I_YAW)
        look = I_YAW - 4.0 + 4.0 * math.sin(w * 2) * (1 - turn) + 52.0 * turn + 40.0 * up
        torso(aims, yaw, bend=0.06 + 0.2 * turn, side=0.06 * turn, chest=8.0 * turn + 4.0 * up, look=look,
              pitch=0.02 - 0.42 * turn - nod + 0.42 * up + 0.015 * br, tilt=0.06 * turn + 0.06 * up, shrug=0.02 * br)
        # his right arm hangs easy at his side
        aims.update(arm_aims(arm, "R", body_pt(V(-0.4, -0.01, 0.9), ro, yaw), pole=rz(yaw) @ V(-1.0, 0.6, -0.2),
                             hand_dir=rz(yaw) @ V(-0.3, -0.1, -1.0)))
        # his left arm: at his side, up to the gauge (knuckles to the glass), a pat on the dome
        down = (rz(yaw) @ V(0.3, -0.1, -1.0)).normalized()
        fwd_t = rz(yaw) @ V(0.0, -1.0, 0.0)
        hang = body_pt(V(0.4, 0.0, 0.9), ro, yaw) + down * 0.11
        held = gauge_fist(tap).lerp(DOME + V(0, 0, 0.065), pat)
        k = ease(reach)
        fist = hang.lerp(held, k) + V(0, 0, 0.08 * math.sin(math.pi * reach))
        knuck = down.lerp((-GAUGE_N).lerp(V(0, 0, -1), pat).normalized(), k).normalized()
        thumb = perp(fwd_t, knuck)
        pole_l = (rz(yaw) @ V(1.0, 0.6, -0.2)).lerp(rz(yaw) @ V(1.0, 0.3, -0.6), k)
        aims.update(grip(arm, "L", fist, thumb, knuck, pole_l))
        machine_aims(aims)
        sc = machine_scales(bars=0.55 + 0.05 * math.sin(w * 6), core=1.0 + 0.04 * math.sin(w * 4))
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- combat
C_FEET = ((0.17, 0.08), (-0.24, -0.06))
C_YAW = -28.0
C_RO = V(0.0, -0.01, -0.03)
POLE_R = V(-1.0, 0.6, -0.5)


def combat_core(arm, br=0.0, sw=0.0):
    ro = C_RO + V(0.0, 0.0, 0.006 * br)
    aims = feet(arm, C_FEET[0], C_FEET[1], C_YAW)
    torso(aims, C_YAW + 1.5 * sw, bend=0.16 + 0.01 * br, side=-0.04, chest=-6.0, look=-10.0 + 5.0 * sw, pitch=0.05, tilt=0.06)
    return aims, ro


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br, sw = math.sin(w * 2), math.sin(w)
        aims, ro = combat_core(arm, br, sw)
        yaw = C_YAW + 1.5 * sw
        aims.update(hip_l(arm, ro, yaw))
        machine_aims(aims, lever=cm.LEV_UP)
        sc = machine_scales(bars=0.6 + 0.04 * math.sin(w * 3), core=1.0 + 0.05 * math.sin(w * 2))
        ch = grip_solve(P, arm, aims, ro, rz(yaw), sc, cm.LEV_UP, rz(C_YAW) @ POLE_R)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- attack
D = PULSE
UPL = cm.LEV_UP
K_LEV = [(0, UPL), (4, UPL + 10.0), (7, UPL + 14.0), (8, UPL + 8.0), (9, 30.0), (D, 6.0), (D + 3, 6.0), (D + 5, 9.0),
         (20, 34.0), (27, UPL + 2.0), (FR, UPL)]
K_BARS = [(0, 0.6), (2, 0.66), (8, 1.0), (D, 1.0), (D + 1, 0.08), (D + 6, 0.1), (FR, 0.6)]
K_CORE = [(0, 1.0), (8, 1.16), (D - 1, 1.2), (D, 1.7), (D + 1, 1.55), (D + 3, 0.78), (D + 8, 0.82), (FR, 1.0)]
K_VAP = [(0, 0.0), (D, 0.0), (D + 1, 0.3), (D + 3, 0.75), (D + 7, 1.1), (D + 12, 1.25), (D + 15, 1.1), (D + 18, 0.0), (FR, 0.0)]
K_RO = [(0, C_RO), (4, C_RO + V(0.008, 0.016, 0.02)), (7, C_RO + V(0.01, 0.02, 0.026)), (D, C_RO + V(-0.02, -0.02, -0.04)),
        (D + 2, C_RO + V(-0.018, -0.016, -0.045)), (D + 6, C_RO + V(0.016, 0.026, -0.02)), (D + 12, C_RO + V(0.0, 0.0, -0.01)), (FR, C_RO)]
K_YAW = [(0, C_YAW), (6, C_YAW + 6.0), (D, C_YAW - 5.0), (D + 5, C_YAW + 2.0), (24, C_YAW - 1.0), (FR, C_YAW)]
K_BEND = [(0, 0.16), (6, 0.04), (8, 0.06), (D, 0.34), (D + 2, 0.32), (D + 5, 0.12), (D + 10, 0.16), (FR, 0.16)]
K_PITCH = [(0, 0.05), (5, 0.12), (8, 0.1), (D, -0.12), (D + 2, -0.22), (D + 6, 0.12), (D + 12, 0.06), (FR, 0.05)]
K_LOOK = [(0, -10.0), (5, -4.0), (D, -16.0), (D + 4, -2.0), (D + 12, -8.0), (FR, -10.0)]
K_TILT = [(0, 0.06), (5, 0.02), (D + 1, 0.14), (D + 5, 0.0), (FR, 0.06)]
K_SHRUG = [(0, 0.0), (6, 0.12), (D, 0.0), (D + 2, 0.2), (D + 6, 0.06), (FR, 0.0)]


def hum(f):
    """The field's hum while it charges (a fine tremble growing to the pulse)."""
    if f >= D:
        return 0.0
    return (f / float(D)) ** 2 * math.sin(f * 2.9)


def ring(f):
    """The mast's ring-down after the pulse: a damped wobble."""
    if f < D:
        return 0.0
    t = f - D
    return math.exp(-t / 4.5) * math.sin(t * 1.9)


def attack_pose(arm, f):
    yaw = smooth_keys(K_YAW, f)
    ro = smooth_keys(K_RO, f)
    aims = feet(arm, C_FEET[0], C_FEET[1], C_YAW)
    torso(aims, yaw, bend=smooth_keys(K_BEND, f), side=-0.04 - 0.04 * ring(f), chest=-6.0 + 3.0 * ring(f + 0.5),
          look=smooth_keys(K_LOOK, f), pitch=smooth_keys(K_PITCH, f), tilt=smooth_keys(K_TILT, f) + 0.05 * ring(f + 1),
          shrug=smooth_keys(K_SHRUG, f))
    aims.update(hip_l(arm, ro, yaw))
    lev = smooth_keys(K_LEV, f)
    machine_aims(aims, lever=lev, wobble=(2.4 * ring(f) + 0.35 * hum(f), 1.3 * ring(f + 1.3) + 0.3 * hum(f + 1)))
    sc = machine_scales(bars=smooth_keys(K_BARS, f) + 0.04 * hum(f + 0.3), core=smooth_keys(K_CORE, f) + 0.05 * hum(f + 0.5),
                        vapour=smooth_keys(K_VAP, f))
    return aims, ro, yaw, sc, lev


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, yaw, sc, lev = attack_pose(arm, f)
        ch = grip_solve(P, arm, aims, ro, rz(yaw), sc, lev, rz(yaw) @ POLE_R)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
