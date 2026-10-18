"""Ugo's clips (30 fps): Idle (fist on hip, sling swaying), Whirl, Throw, Ability (Stone Rain call) and Cheer (rank up).
The sabertooth cape hangs from two bones that are aimed in world space, so it trails the body's motion."""
import math
import bpy
from mathutils import Vector, Quaternion
import ugo as cm
from rig import Poser, leg_aims, arm_aims
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J

TILT = math.radians(34)
U_AX = Vector((math.cos(TILT), 0.0, math.sin(TILT)))
V_AX = Vector((0.0, 1.0, 0.0))
WR_UP = Vector((-0.72, 0.06, 1.86))         # sling wrist while whirling
WR_POINT_L = Vector((0.41, -0.55, 1.46))    # left hand pointing at the target
REV = 16


def sling_dir(phi):
    return (U_AX * math.cos(phi) + V_AX * math.sin(phi)).normalized()


def cape_aims(back=0.0, side=0.0, wave=0.0):
    """World-space aims for the two cape bones: hanging, pushed back by `back`, swung by `side`, rippling by `wave`."""
    return {"cape.1": Vector((side * 0.6, 0.16 + back, -1.0)),
            "cape.2": Vector((side + wave * 0.12, 0.1 + back * 1.3 + abs(wave) * 0.05, -1.0))}


def stance(arm, wide=1.0, crouch=0.0):
    aR = Vector(J["ankle_R"]) + Vector((-0.03 * wide, 0.1 * wide, 0.0))
    aL = Vector(J["ankle_L"]) + Vector((0.03 * wide, -0.08 * wide, 0.0))
    aims = {}
    aims.update(leg_aims(arm, "R", aR, pole=Vector((-0.2, -1, 0.1))))
    aims.update(leg_aims(arm, "L", aL, pole=Vector((0.2, -1, 0.1))))
    return aims


def key_constant(act, path_part):
    """Make every key on curves whose data path contains `path_part` constant (stone pops in and out)."""
    done = False
    try:
        for fc in act.fcurves:
            if path_part in fc.data_path:
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
                        if path_part in fc.data_path:
                            for kp in fc.keyframe_points:
                                kp.interpolation = "CONSTANT"


# ---------------------------------------------------------------------------------------------- poses
def whirl_pose(arm, phi, breathe=0.0, coil=0.0, lean=0.0):
    aims = stance(arm)
    root_off = Vector((0.0, 0.0, -0.04 + 0.006 * breathe))
    root_rot = Quaternion((0, 0, 1), math.radians(-6 + 12 * coil))
    aims["spine"] = Vector((0.0, 0.05 - 0.25 * lean, 1.0))
    aims["chest"] = (Vector((0.04, -0.04 - 0.3 * lean, 1.0)), math.radians(10 * coil))
    aims["neck"] = Vector((0.0, -0.3, 1.0))
    aims["head"] = (Vector((0.0, -0.1, 1.0)), math.radians(-14 * coil))
    aims["clavicle.R"] = Vector((-1.0, 0.02, 0.24))
    aims["clavicle.L"] = Vector((1.0, -0.15, 0.08))
    aims.update(arm_aims(arm, "R", WR_UP, pole=Vector((-1.0, 0.25, -0.25)), hand_dir=Vector((0.15, 0.0, 1.0))))
    aims.update(arm_aims(arm, "L", WR_POINT_L, pole=Vector((1.0, 0.2, -0.6)), hand_dir=Vector((0.25, -1.0, 0.05))))
    aims["sling"] = sling_dir(phi)
    return aims, root_off, root_rot


def idle_pose(arm, t):
    """Heroic idle: wide stance, left fist on his hip, sling swaying from the right hand, looking around."""
    w = 2 * math.pi * t
    aims = {}
    aims.update(leg_aims(arm, "R", Vector(J["ankle_R"]) + Vector((-0.035, 0.03, 0)), pole=Vector((-0.2, -1, 0.1))))
    aims.update(leg_aims(arm, "L", Vector(J["ankle_L"]) + Vector((0.035, -0.02, 0)), pole=Vector((0.2, -1, 0.1))))
    br = math.sin(w * 2)
    root_off = Vector((0.0, 0.0, -0.014 + 0.007 * br))
    root_rot = Quaternion((0, 0, 1), math.radians(4 * math.sin(w)))
    aims["spine"] = Vector((0.0, 0.03, 1.0))
    aims["chest"] = Vector((0.0, 0.0 + 0.03 * br, 1.0))            # chest out
    look = math.sin(w) * 0.85 + 0.25 * math.sin(w * 3)
    aims["neck"] = Vector((0.0, -0.2, 1.0))
    aims["head"] = (Vector((0.0, -0.12 + 0.03 * br, 1.0)), math.radians(18 * look))
    aims["clavicle.R"] = Vector((-1.0, 0.0, 0.02))
    aims["clavicle.L"] = Vector((1.0, 0.02, 0.04))
    aims.update(arm_aims(arm, "R", Vector((-0.56, -0.07, 1.02 + 0.006 * br)), pole=Vector((-0.6, 1.0, 0.0)),
                         hand_dir=Vector((-0.1, -0.35, -1.0))))
    aims.update(arm_aims(arm, "L", Vector((0.33, -0.02, 1.06)), pole=Vector((1.0, 0.45, 0.1)),
                         hand_dir=Vector((-0.35, 0.25, -1.0))))        # fist planted on the hip
    sw = math.radians(14) * math.sin(w * 2)
    aims["sling"] = Vector((math.sin(sw) * 0.25, -math.sin(sw), -1.0))
    aims.update(cape_aims(back=0.02 + 0.015 * br, side=0.02 * math.sin(w), wave=0.6 * math.sin(w * 2 + 1.0)))
    return aims, root_off, root_rot


# ---------------------------------------------------------------------------------------------- clips
def make_idle(arm, frames=90):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_whirl(arm, frames=32):
    P = Poser(arm)
    act = new_action(arm, "Whirl")
    for f in range(frames + 1):
        t = (f % frames) / frames
        phi = 2 * math.pi * f / REV
        aims, ro, rr = whirl_pose(arm, phi, breathe=math.sin(2 * math.pi * t), coil=0.15 * math.sin(4 * math.pi * t))
        aims.update(cape_aims(back=0.07 + 0.02 * math.sin(4 * math.pi * t), side=0.05 * math.sin(4 * math.pi * t + 0.8),
                              wave=math.sin(4 * math.pi * t)))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_throw(arm, frames=24, release=3):
    """From the whirl pose (phi=0): whip the sling forward (stone leaves at `release`), follow through, reload from the
    hip pouch and come back up into the whirl."""
    P = Poser(arm)
    act = new_action(arm, "Throw")
    wr_up = WR_UP.copy()
    wr_rel = Vector((-0.38, -0.45, 1.8))
    wr_thru = Vector((0.0, -0.45, 1.13))
    wr_bag = Vector((-0.38, -0.24, 0.99))
    wl0 = WR_POINT_L.copy()
    for f in range(frames + 1):
        sc = {}
        if f <= release:
            k = ease(f / release)
            wr = lerp(wr_up, wr_rel, k)
            sd = sling_dir(lerp(0.0, -math.pi * 0.55, k))
            sdir = lerp(sd, Vector((0.0, -0.75, 0.66)).normalized(), k).normalized()
            coil, lean = lerp(0.5, -0.6, k), lerp(0.0, 0.5, k)
            wrL = lerp(wl0, Vector((0.38, -0.12, 1.28)), k)
            cb = lerp(0.07, 0.16, k)
        elif f <= 9:
            k = ease((f - release) / (9 - release))
            wr = lerp(wr_rel, wr_thru, k)
            sdir = lerp(Vector((0.0, -0.75, 0.66)), Vector((0.4, 0.3, -0.85)), k).normalized()
            coil, lean = lerp(-0.6, -0.8, k), lerp(0.5, 0.75, k)
            wrL = lerp(Vector((0.38, -0.12, 1.28)), Vector((0.46, 0.05, 1.07)), k)
            cb = lerp(0.16, 0.2, k)
        elif f <= 15:
            k = ease((f - 9) / 6.0)
            wr = lerp(wr_thru, wr_bag, k)
            sdir = Vector((0.1, -0.15, -1.0))
            coil, lean = lerp(-0.8, -0.2, k), lerp(0.75, 0.35, k)
            wrL = lerp(Vector((0.46, 0.05, 1.07)), Vector((0.42, -0.3, 1.28)), k)
            cb = lerp(0.2, 0.1, k)
        else:
            k = ease((f - 15) / (frames - 15))
            wr = lerp(wr_bag, wr_up, k)
            sdir = lerp(Vector((0.1, -0.15, -1.0)), sling_dir(2 * math.pi), k).normalized()
            coil, lean = lerp(-0.2, 0.0, k), lerp(0.35, 0.0, k)
            wrL = lerp(Vector((0.42, -0.3, 1.28)), wl0, k)
            cb = lerp(0.1, 0.07, k)
        aims, ro, rr = whirl_pose(arm, 0.0, coil=coil, lean=lean)
        pole = Vector((-1.0, 0.3, 0.1)) if f <= 9 else Vector((-1.0, 0.6, -0.4))
        aims.update(arm_aims(arm, "R", wr, pole=pole, hand_dir=(wr - Vector((-0.5, 0.05, 1.55))).normalized()))
        aims.update(arm_aims(arm, "L", wrL, pole=Vector((1.0, 0.2, -0.6)), hand_dir=Vector((0.25, -1.0, 0.05))))
        aims["sling"] = sdir
        aims.update(cape_aims(back=cb, side=-0.06 * lean, wave=0.8 * math.sin(f / frames * 2 * math.pi)))
        ro = ro + Vector((0.0, -0.045 * lean, -0.016 * lean))
        sc["stone"] = 0.0 if release <= f < 15 else 1.0
        ch, _ = P.solve(aims, ro, rr, scales=sc)
        P.key(ch, f)
    key_constant(act, 'pose.bones["stone"].scale')
    finish_action(arm, act, frames, False)
    return act


def make_ability(arm, frames=48):
    """Stone Rain: crouch, spring up with the sling whirled high over his head and roar at the sky (the boulders
    fall), then sweep the sling arm down at the enemy and settle back into his stance."""
    P = Poser(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        t = f / frames
        aims = {}
        if f <= 8:                                    # anticipation: crouch, arms drawn in
            k = ease(f / 8)
            crouch, lift = lerp(0.0, 0.11, k), 0.0
            wr = lerp(Vector((-0.56, -0.07, 1.02)), Vector((-0.5, -0.2, 1.1)), k)
            wl = lerp(Vector((0.33, -0.02, 1.06)), Vector((0.45, -0.18, 1.1)), k)
            head_up, back, lean = lerp(0.0, -0.2, k), 0.04, lerp(0.0, 0.3, k)
            sdir = Vector((0.0, -0.1, -1.0))
        elif f <= 14:                                 # spring up, arms thrown up
            k = ease((f - 8) / 6)
            crouch, lift = lerp(0.11, -0.03, k), lerp(0.0, 0.05, k)
            wr = lerp(Vector((-0.5, -0.2, 1.1)), Vector((-0.42, -0.08, 2.1)), k)
            wl = lerp(Vector((0.45, -0.18, 1.1)), Vector((0.52, -0.1, 1.98)), k)
            head_up, back, lean = lerp(-0.2, 0.5, k), lerp(0.04, 0.32, k), lerp(0.3, -0.25, k)
            sdir = lerp(Vector((0.0, -0.1, -1.0)), Vector((0.3, 0.2, 1.0)), k).normalized()
        elif f <= 30:                                 # roar at the sky, sling whirling high
            k = (f - 14) / 16
            crouch, lift = -0.03 + 0.02 * math.sin(k * math.pi), 0.05 * (1 - k)
            shake = 0.015 * math.sin(f * 2.6)
            wr = Vector((-0.4 + shake, -0.08, 2.1))
            wl = Vector((0.52 - shake, -0.1, 1.98))
            head_up, back, lean = 0.5, 0.3 - 0.1 * k, -0.25
            phi = 2 * math.pi * (f - 14) / 8
            sdir = (Vector((math.cos(phi), math.sin(phi), 0.25))).normalized()
        elif f <= 38:                                 # sweep down at the enemy
            k = ease((f - 30) / 8)
            crouch, lift = lerp(-0.01, 0.06, k), 0.0
            wr = lerp(Vector((-0.4, -0.08, 2.1)), Vector((-0.3, -0.62, 1.38)), k)
            wl = lerp(Vector((0.52, -0.1, 1.98)), Vector((0.42, -0.2, 1.12)), k)
            head_up, back, lean = lerp(0.5, -0.05, k), lerp(0.2, 0.16, k), lerp(-0.25, 0.45, k)
            sdir = lerp(Vector((1.0, 0.0, 0.25)).normalized(), Vector((0.0, -0.8, -0.6)), k).normalized()
        else:                                         # settle back into the idle stance
            k = ease((f - 38) / (frames - 38))
            crouch, lift = lerp(0.06, 0.014, k), 0.0
            wr = lerp(Vector((-0.3, -0.62, 1.38)), Vector((-0.56, -0.07, 1.02)), k)
            wl = lerp(Vector((0.42, -0.2, 1.12)), Vector((0.33, -0.02, 1.06)), k)
            head_up, back, lean = lerp(-0.05, 0.0, k), lerp(0.16, 0.035, k), lerp(0.45, 0.0, k)
            sdir = lerp(Vector((0.0, -0.8, -0.6)), Vector((0.0, 0.0, -1.0)), k).normalized()
        aims.update(stance(arm, wide=1.15))
        root_off = Vector((0.0, -0.04 * lean, -crouch + lift))
        root_rot = Quaternion((0, 0, 1), math.radians(-5))
        aims["spine"] = Vector((0.0, 0.05 - 0.28 * lean, 1.0))
        aims["chest"] = Vector((0.0, -0.02 - 0.32 * lean, 1.0))
        aims["neck"] = Vector((0.0, -0.3 + 0.55 * head_up, 1.0))
        aims["head"] = Vector((0.0, -0.12 + 0.75 * head_up, 1.0))
        aims["clavicle.R"] = Vector((-1.0, 0.0, 0.05 + 0.3 * max(0.0, wr.z - 1.4)))
        aims["clavicle.L"] = Vector((1.0, 0.0, 0.05 + 0.3 * max(0.0, wl.z - 1.4)))
        aims.update(arm_aims(arm, "R", wr, pole=Vector((-1.0, 0.4, -0.3)), hand_dir=(wr - Vector((-0.45, 0.07, 1.5))).normalized()))
        aims.update(arm_aims(arm, "L", wl, pole=Vector((1.0, 0.4, -0.3)), hand_dir=(wl - Vector((0.45, 0.07, 1.5))).normalized()))
        aims["sling"] = sdir
        aims.update(cape_aims(back=back, side=0.04 * math.sin(t * 6.0), wave=math.sin(t * 9.0)))
        ch, _ = P.solve(aims, root_off, root_rot)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_cheer(arm, frames=40):
    """Rank up: two fist pumps with a little hop, head thrown back laughing."""
    P = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        t = f / frames
        pump = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.4)) * (1 - max(0.0, (t - 0.8) / 0.2))
        hop = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.9)) * 0.045 * (1 - max(0.0, (t - 0.75) / 0.25))
        settle = ease(max(0.0, (t - 0.8) / 0.2))
        aims = {}
        aims.update(leg_aims(arm, "R", Vector(J["ankle_R"]) + Vector((-0.035, 0.03, hop * 0.6)), pole=Vector((-0.2, -1, 0.1))))
        aims.update(leg_aims(arm, "L", Vector(J["ankle_L"]) + Vector((0.035, -0.02, hop * 0.6)), pole=Vector((0.2, -1, 0.1))))
        root_off = Vector((0.0, 0.0, -0.03 + hop + 0.016 * settle))
        root_rot = Quaternion((0, 0, 1), math.radians(6 * math.sin(t * math.pi)))
        aims["spine"] = Vector((0.0, 0.05 + 0.08 * pump, 1.0))
        aims["chest"] = Vector((0.0, 0.04 + 0.1 * pump, 1.0))
        aims["neck"] = Vector((0.0, -0.1 + 0.3 * pump, 1.0))
        aims["head"] = (Vector((0.0, 0.1 + 0.45 * pump, 1.0)), math.radians(8 * math.sin(t * 9)))
        wl = lerp(Vector((0.46, -0.12, 1.5)), Vector((0.5, -0.08, 2.15)), pump)
        wl = lerp(wl, Vector((0.33, -0.02, 1.06)), settle)
        aims["clavicle.R"] = Vector((-1.0, 0.0, 0.02))
        aims["clavicle.L"] = Vector((1.0, 0.0, 0.05 + 0.35 * pump))
        aims.update(arm_aims(arm, "L", wl, pole=Vector((1.0, 0.3, -0.5)), hand_dir=(wl - Vector((0.45, 0.07, 1.5))).normalized()))
        wr = lerp(Vector((-0.58, -0.12, 1.12)), Vector((-0.56, -0.07, 1.02)), settle)
        aims.update(arm_aims(arm, "R", wr, pole=Vector((-0.6, 1.0, 0.0)), hand_dir=Vector((-0.1, -0.35, -1.0))))
        sw = math.radians(25) * math.sin(t * 2 * math.pi * 2)
        aims["sling"] = Vector((math.sin(sw) * 0.3, -math.sin(sw), -1.0))
        aims.update(cape_aims(back=0.04 + 0.12 * hop / 0.045, side=0.03 * math.sin(t * 7), wave=math.sin(t * 12)))
        ch, _ = P.solve(aims, root_off, root_rot)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_whirl(arm), make_throw(arm), make_ability(arm), make_cheer(arm)]
