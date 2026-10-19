"""Where a point carried rigidly by a bone is at some frames, in the Yaw node's local frame, Godot axes (what game.gd
multiplies the Yaw node's global transform by). The point is given in the rest pose (character / armature space).
    blender -b --python prop_point.py -- BLEND ACTION BONE FRAMES X,Y,Z [X,Y,Z ...]
(or python3 with bpy as a module: python3 prop_point.py BLEND ...)"""
import sys
import bpy
from mathutils import Vector

A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
blend, action, bone, frames = A[0], A[1], A[2], [int(f) for f in A[3].split(",")]
pts = [Vector([float(x) for x in s.split(",")]) for s in A[4:]]
bpy.ops.wm.open_mainfile(filepath=blend)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
yaw = bpy.data.objects.get("Yaw")
act = bpy.data.actions[action]
arm.animation_data_create()
for t in arm.animation_data.nla_tracks:
    t.mute = True
arm.animation_data.action = act
try:
    if act.slots and arm.animation_data.action_slot is None:
        arm.animation_data.action_slot = act.slots[0]
except Exception:
    pass
rest = arm.data.bones[bone].matrix_local
for f in frames:
    bpy.context.scene.frame_set(f)
    pose = arm.pose.bones[bone].matrix
    for p in pts:
        a = pose @ rest.inverted() @ p                       # armature space, posed
        w = arm.matrix_world @ a
        y = (yaw.matrix_world.inverted() @ w) if yaw else w   # Yaw-local, Blender axes
        print("frame %3d  %s -> yaw-local Blender (%.3f, %.3f, %.3f)  Godot Vector3(%.3f, %.3f, %.3f)" %
              (f, tuple(round(x, 3) for x in p), y.x, y.y, y.z, y.x, y.z, -y.y))
