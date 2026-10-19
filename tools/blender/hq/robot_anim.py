"""Clips for the HQ robots: a biped march with planted feet (two-bone IK), and a hover loop for drones.

Robots face -Y with Z up. A walk cycle covers two steps; in game the clip's playback speed follows the robot's real
ground speed (enemies.json "walk_speed" = the ground speed the clip matches at speed 1), so the feet don't slide.
"""
import math
import bpy
from mathutils import Vector, Quaternion, Matrix
from rig import Poser, two_bone, bone_len

V = lambda *a: Vector(a)


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
    trk.strips.new(act.name, 0, act)
    trk.mute = True
    ob.animation_data.action = None


def leg(arm, side, ankle, toe_dir, pole):
    """Thigh / shin aimed by two-bone IK at `ankle`; the foot points along `toe_dir` with its sole flat."""
    la, lb = bone_len(arm, "thigh." + side), bone_len(arm, "shin." + side)
    st = {}
    def thigh(P, base):
        hip = base.translation
        knee = two_bone(hip, ankle, la, lb, pole)
        st["knee"] = knee
        return knee - hip
    def shin(P, base):
        return Vector(ankle) - st["knee"]
    fb = arm.data.bones["foot." + side]
    rest = (fb.tail_local - fb.head_local).normalized()
    return {"thigh." + side: thigh, "shin." + side: shin, "foot." + side: ("frame", rest, Vector(toe_dir), V(0, 0, 1), V(0, 0, 1))}


def rot_dir(d, axis, ang):
    return Quaternion(Vector(axis), ang) @ Vector(d)


def walk(arm, J, name="Walk", frames=24, step=0.42, lift=0.08, bob=0.025, sway=0.02, arm_swing=0.45, lean=0.12,
         twist=0.12, heavy=0.0, head_lag=0.5, extra=None):
    """A two-step march. step: stride of one foot (model units); heavy > 0 gives a stompier gait (a dip at contact, a
    slower lift); extra(t, aims) may add bone aims (antenna wobble, back exhaust, a boss's swaying crest)."""
    P = Poser(arm)
    act = new_action(arm, name)
    rest = {b.name: b for b in arm.data.bones}
    for f in range(frames + 1):
        t = f / frames
        aims = {}
        for side, off in (("L", 0.0), ("R", 0.5)):
            ph = (t + off) % 1.0
            a0 = Vector(J["ankle_" + side])
            if ph < 0.5:                                            # stance: planted, sliding back under the body
                k = ph / 0.5
                y = -step / 2 + step * k
                z = 0.0
                pitch = 0.0
                if k > 0.8:                                         # heel off before the swing
                    pitch = -0.35 * (k - 0.8) / 0.2
                    z = 0.02 * (k - 0.8) / 0.2
            else:                                                   # swing: lifted, carried forward
                k = (ph - 0.5) / 0.5
                e = 0.5 - 0.5 * math.cos(math.pi * k)
                y = step / 2 - step * e
                lk = math.sin(math.pi * k)
                z = lift * (lk ** (1.0 + heavy))
                pitch = -0.35 * (1 - k) * (1 - k) + 0.25 * math.sin(math.pi * k) * (1 - k)
            ankle = a0 + V(0, y, z)
            toe = rot_dir(V(0, -1, 0), V(1, 0, 0), pitch)
            aims.update(leg(arm, side, ankle, toe, V(0, -1, 0.05)))
        # pelvis: lowest at each contact (t = 0, 0.5), sways over the stance foot
        c = math.cos(4 * math.pi * t)
        dip = -bob * c - (heavy * bob * max(0.0, c) ** 4)
        side_sh = sway * math.sin(2 * math.pi * t)
        root_off = V(side_sh, 0.0, dip + bob)
        root_rot = Quaternion(V(0, 0, 1), twist * 0.5 * math.sin(2 * math.pi * t)) @ Quaternion(V(1, 0, 0), -lean * 0.5)
        # chest counter-twists, leans forward
        aims["spine"] = (V(-side_sh * 0.4, -lean, 1.0), -twist * math.sin(2 * math.pi * t))
        # head stays steady (counters the bob a little) and looks ahead
        aims["head"] = V(0.0, -0.05 + 0.15 * head_lag * c * bob * 10, 1.0)
        # arms swing opposite to the legs, elbows bent more on the forward swing
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            s = math.sin(2 * math.pi * t) * sgn                     # +1: this arm forward
            sh, el, wr = Vector(J["shoulder_" + side]), Vector(J["elbow_" + side]), Vector(J["wrist_" + side])
            up = (el - sh).normalized()
            fo = (wr - el).normalized()
            up = rot_dir(up, V(1, 0, 0), arm_swing * s)
            fo = rot_dir(fo, V(1, 0, 0), arm_swing * s * 1.3 + 0.25 + 0.2 * max(0.0, s))
            aims["upperarm." + side] = up
            aims["forearm." + side] = fo
            if "hand." + side in rest:
                aims["hand." + side] = fo
        if extra is not None:
            extra(t, aims)
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def hover(arm, name="Fly", frames=48, bob=0.05, tilt=0.08, roll=0.05, spin_bones=(), spin_turns=6, extra=None):
    """A hovering drone: bobs, pitches forward and rolls gently; rotor bones spin (whole turns per loop)."""
    P = Poser(arm)
    act = new_action(arm, name)
    for f in range(frames + 1):
        t = f / frames
        aims = {}
        root_off = V(0, 0, bob * math.sin(2 * math.pi * t))
        root_rot = Quaternion(V(1, 0, 0), -tilt + 0.3 * tilt * math.sin(2 * math.pi * t + 1.0)) @ \
            Quaternion(V(0, 1, 0), roll * math.sin(2 * math.pi * t * 1.0 + 0.6))
        for i, b in enumerate(spin_bones):
            ang = (1 if i % 2 == 0 else -1) * 2 * math.pi * spin_turns * t
            aims[b] = (lambda a: (lambda P, base: ("rot", Quaternion(base.col[1].xyz.normalized(), a))))(ang)
        if extra is not None:
            extra(t, aims)
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act
