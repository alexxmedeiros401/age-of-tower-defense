"""Blender side of the pose solver: key a solved pose on the armature."""
import numpy as np
from mathutils import Matrix
import rs_core


class Keyer:
    def __init__(self, arm):
        self.arm = arm
        self.rest = {b.name: np.array(b.matrix_local) for b in arm.data.bones}
        self.parents = {b.name: (b.parent.name if b.parent else '') for b in arm.data.bones}
        self.prev = {}

    def set_pose(self, P):
        B = rs_core.to_basis(P, self.rest, self.parents)
        for nme, M in B.items():
            pb = self.arm.pose.bones[nme]
            loc, rot, scl = Matrix(M.tolist()).decompose()
            if nme in self.prev and self.prev[nme].dot(rot) < 0:
                rot.negate()                                   # keep quaternions on one side (clean interpolation)
            self.prev[nme] = rot.copy()
            pb.rotation_quaternion = rot
            pb.location = loc if nme == 'root' else (0.0, 0.0, 0.0)
            if nme != 'root' and loc.length > 2e-4:
                raise RuntimeError('bone %s has a location (%.5f): the solver broke the chain' % (nme, loc.length))
            pb.scale = scl if nme == 'stone' else (1.0, 1.0, 1.0)

    def key(self, P, frame):
        self.set_pose(P)
        for nme in P:
            pb = self.arm.pose.bones[nme]
            pb.keyframe_insert('rotation_quaternion', frame=frame)
            if nme == 'root': pb.keyframe_insert('location', frame=frame)
            if nme == 'stone': pb.keyframe_insert('scale', frame=frame)


def new_action(arm, name):
    import bpy
    arm.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    return act


def finish_action(arm, act, f0, f1, cyclic):
    arm.animation_data.action = act
    act.frame_range = (f0, f1)
    try:
        act.use_frame_range = True
        act.use_cyclic = cyclic
    except Exception:
        pass
    trk = arm.animation_data.nla_tracks.new()
    trk.name = act.name
    trk.strips.new(act.name, int(f0), act)
    trk.mute = True
    arm.animation_data.action = None
