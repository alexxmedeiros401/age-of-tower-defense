"""Idle / Whirl / Throw clips for the Rock Slinger (30 fps)."""
import math
import bpy
from mathutils import Vector, Quaternion, Matrix
import caveman as cm
from rig import Poser, leg_aims, arm_aims, bone_len

FPS = 30
J = cm.J
Vv = lambda *a: Vector(a)

# whirl plane: tilted so the pouch rises over the head and dips on the outside
TILT = math.radians(34)
U_AX = Vector((math.cos(TILT), 0.0, math.sin(TILT)))     # toward the head (+X) and up
V_AX = Vector((0.0, 1.0, 0.0))


WR_UP = Vector((-0.64, 0.06, 1.72))      # sling wrist while whirling: elbow out at shoulder height, fist up


def sling_dir(phi):
    return (U_AX * math.cos(phi) + V_AX * math.sin(phi)).normalized()


def stance(arm, wide=1.0):
    aR = Vector(J["ankle_R"]) + Vector((-0.02 * wide, 0.1 * wide, 0.0))
    aL = Vector(J["ankle_L"]) + Vector((0.02 * wide, -0.08 * wide, 0.0))
    aims = {}
    aims.update(leg_aims(arm, "R", aR, pole=Vector((-0.15, -1, 0.1))))
    aims.update(leg_aims(arm, "L", aL, pole=Vector((0.15, -1, 0.1))))
    return aims


def new_action(ob, name):
    ob.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    ob.animation_data.action = act
    return act


def finish_action(ob, act, frames, cyclic):
    ob.animation_data.action = act
    act.frame_range = (0, frames)
    try:
        act.use_frame_range = True
        act.use_cyclic = cyclic
    except Exception:
        pass
    trk = ob.animation_data.nla_tracks.new()
    trk.name = act.name
    strip = trk.strips.new(act.name, 0, act)
    trk.mute = True
    ob.animation_data.action = None


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------------------------- poses
def whirl_pose(arm, phi, breathe=0.0, coil=0.0, lean=0.0):
    """Combat stance: left arm points at the target, right fist up beside the head, sling whirling."""
    aims = stance(arm)
    root_off = Vector((0.0, 0.0, -0.035 + 0.006 * breathe))
    root_rot = Quaternion((0, 0, 1), math.radians(-6 + 12 * coil))
    aims["spine"] = Vector((0.0, 0.05 - 0.25 * lean, 1.0))
    aims["chest"] = (Vector((0.04, -0.05 - 0.3 * lean, 1.0)), math.radians(10 * coil))
    aims["neck"] = Vector((0.0, -0.32, 1.0))
    aims["head"] = (Vector((0.0, -0.12, 1.0)), math.radians(-14 * coil))
    aims["clavicle.R"] = Vector((-1.0, 0.02, 0.22))
    aims["clavicle.L"] = Vector((1.0, -0.15, 0.08))
    aims.update(arm_aims(arm, "R", WR_UP, pole=Vector((-1.0, 0.25, -0.25)), hand_dir=Vector((0.15, 0.0, 1.0))))
    aims.update(arm_aims(arm, "L", Vector((0.36, -0.5, 1.36)), pole=Vector((1.0, 0.2, -0.6)), hand_dir=Vector((0.25, -1.0, 0.05))))
    aims["sling"] = sling_dir(phi)
    return aims, root_off, root_rot


def idle_pose(arm, t):
    """t in [0,1) over the loop."""
    w = 2 * math.pi * t
    aims = {}
    aims.update(leg_aims(arm, "R", Vector(J["ankle_R"]), pole=Vector((-0.1, -1, 0.1))))
    aims.update(leg_aims(arm, "L", Vector(J["ankle_L"]), pole=Vector((0.1, -1, 0.1))))
    br = math.sin(w * 2)
    root_off = Vector((0.0, 0.0, -0.012 + 0.006 * br))
    root_rot = Quaternion((0, 0, 1), math.radians(3 * math.sin(w)))
    aims["spine"] = Vector((0.0, 0.02, 1.0))
    aims["chest"] = Vector((0.0, -0.04 + 0.025 * br, 1.0))
    look = math.sin(w) * 0.9 + 0.2 * math.sin(w * 3)
    aims["neck"] = Vector((0.0, -0.25, 1.0))
    aims["head"] = (Vector((0.0, -0.18, 1.0)), math.radians(16 * look))
    aims["clavicle.R"] = Vector((-1.0, 0.0, 0.0))
    aims["clavicle.L"] = Vector((1.0, 0.0, 0.0))
    aims.update(arm_aims(arm, "R", Vector((-0.5, -0.06, 0.95)), pole=Vector((-0.6, 1.0, 0.0)), hand_dir=Vector((-0.1, -0.35, -1.0))))
    aims.update(arm_aims(arm, "L", Vector((0.33, 0.02, 0.9)), pole=Vector((1.0, 0.6, 0.0)), hand_dir=Vector((-0.55, -0.2, -0.8))))
    sw = math.radians(12) * math.sin(w * 2)
    aims["sling"] = Vector((math.sin(sw) * 0.25, -math.sin(sw), -1.0))
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


REV = 16          # frames per sling revolution while whirling


def make_whirl(arm, frames=32):
    P = Poser(arm)
    act = new_action(arm, "Whirl")
    for f in range(frames + 1):
        t = (f % frames) / frames
        phi = 2 * math.pi * f / REV
        aims, ro, rr = whirl_pose(arm, phi, breathe=math.sin(2 * math.pi * t), coil=0.15 * math.sin(4 * math.pi * t))
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_throw(arm, frames=24, release=3):
    """Starts from the whirl pose (phi=0), whips the sling forward (stone leaves at `release`),
    follows through, reloads from the hip bag and comes back up to whirl."""
    P = Poser(arm)
    act = new_action(arm, "Throw")
    wr_up = WR_UP.copy()
    wr_rel = Vector((-0.34, -0.42, 1.7))
    wr_thru = Vector((0.02, -0.42, 1.05))
    wr_bag = Vector((-0.36, -0.2, 0.9))
    for f in range(frames + 1):
        aims, ro, rr = whirl_pose(arm, 0.0)
        sc = {}
        if f <= release:                                   # whip: arm comes over, sling swings forward
            k = ease(f / release)
            wr = lerp(wr_up, wr_rel, k)
            phi = lerp(0.0, -math.pi * 0.55, k)
            sd = sling_dir(phi)
            fwd = Vector((0.0, -0.75, 0.66)).normalized()
            sdir = lerp(sd, fwd, k).normalized()
            coil = lerp(0.5, -0.6, k)
            lean = lerp(0.0, 0.5, k)
            wrL = lerp(Vector((0.36, -0.5, 1.36)), Vector((0.34, -0.12, 1.2)), k)
        elif f <= 9:                                       # follow through across the body
            k = ease((f - release) / (9 - release))
            wr = lerp(wr_rel, wr_thru, k)
            sdir = lerp(Vector((0.0, -0.75, 0.66)), Vector((0.4, 0.3, -0.85)), k).normalized()
            coil = lerp(-0.6, -0.8, k)
            lean = lerp(0.5, 0.75, k)
            wrL = lerp(Vector((0.34, -0.12, 1.2)), Vector((0.42, 0.05, 1.0)), k)
        elif f <= 15:                                      # reload from the hip bag
            k = ease((f - 9) / 6.0)
            wr = lerp(wr_thru, wr_bag, k)
            sdir = Vector((0.1, -0.15, -1.0))
            coil = lerp(-0.8, -0.2, k)
            lean = lerp(0.75, 0.35, k)
            wrL = lerp(Vector((0.42, 0.05, 1.0)), Vector((0.38, -0.3, 1.2)), k)
        else:                                              # back up into the whirl
            k = ease((f - 15) / (frames - 15))
            wr = lerp(wr_bag, wr_up, k)
            sdir = lerp(Vector((0.1, -0.15, -1.0)), sling_dir(2 * math.pi), k).normalized()
            coil = lerp(-0.2, 0.0, k)
            lean = lerp(0.35, 0.0, k)
            wrL = lerp(Vector((0.38, -0.3, 1.2)), Vector((0.36, -0.5, 1.36)), k)
        aims, ro, rr = whirl_pose(arm, 0.0, coil=coil, lean=lean)
        pole = Vector((-1.0, 0.3, 0.1)) if f <= 9 else Vector((-1.0, 0.6, -0.4))
        aims.update(arm_aims(arm, "R", wr, pole=pole, hand_dir=(wr - Vector((-0.45, 0.05, 1.45))).normalized()))
        aims.update(arm_aims(arm, "L", wrL, pole=Vector((1.0, 0.2, -0.6)), hand_dir=Vector((0.25, -1.0, 0.05))))
        aims["sling"] = sdir
        ro = ro + Vector((0.0, -0.04 * lean, -0.015 * lean))
        sc["stone"] = 0.0 if release <= f < 15 else 1.0
        ch, _ = P.solve(aims, ro, rr, scales=sc)
        P.key(ch, f)
    # stone pops instantly (constant interpolation on its scale)
    fc_ok = False
    try:
        for fc in act.fcurves:
            if 'pose.bones["stone"].scale' in fc.data_path:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
                fc_ok = True
    except Exception:
        pass
    if not fc_ok:
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        if 'pose.bones["stone"].scale' in fc.data_path:
                            for kp in fc.keyframe_points:
                                kp.interpolation = "CONSTANT"
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    acts = [make_idle(arm), make_whirl(arm), make_throw(arm)]
    return acts
