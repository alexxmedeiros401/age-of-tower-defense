"""Re-key a built character's clips (after editing its animation module) without re-baking anything.

    python3 reanim.py -- --character ugo --blend OUT/char_game.blend
    python3 build_game.py -- --character ugo --out OUT --stage export      # then re-export the GLB
"""
import sys, os, importlib
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import bpy

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d

import character
CH = character.use(arg("--character", "caveman"))
an = importlib.import_module(CH.ANIM_MODULE)
path = arg("--blend")
bpy.ops.wm.open_mainfile(filepath=path)
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
if arm.animation_data is not None:
    for t in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(t)
    arm.animation_data.action = None
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
for pb in arm.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.scale = (1, 1, 1)
acts = an.make_all(arm)
bpy.ops.wm.save_as_mainfile(filepath=path)
print("[reanim]", [a.name for a in acts])
