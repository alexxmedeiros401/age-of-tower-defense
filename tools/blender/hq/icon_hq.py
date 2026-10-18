"""Shop icon for an HQ tower, framed like tools/blender/icons.py (ortho, same angle), posed mid-whirl."""
import sys, os, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import bpy
from mathutils import Vector
import look

ARGS = sys.argv[sys.argv.index("--") + 1:]
BLEND, OUT = ARGS[0], ARGS[1]
ACTION = ARGS[2] if len(ARGS) > 2 and not ARGS[2].startswith("--") else "Whirl"
FRAME = int(ARGS[3]) if len(ARGS) > 3 and not ARGS[3].startswith("--") else 4
ZOOM = float(ARGS[ARGS.index("--zoom") + 1]) if "--zoom" in ARGS else 4.5
TZ = float(ARGS[ARGS.index("--tz") + 1]) if "--tz" in ARGS else 1.35
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
arm.animation_data.action = bpy.data.actions[ACTION]
sc.frame_set(FRAME)
look.setup(samples=96, res=(512, 512), transparent=True)
cam = bpy.data.objects.new("IconCam", bpy.data.cameras.new("IconCam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = ZOOM
t = Vector((0, -0.1, TZ))
d = Vector((0.7, -1.2, 0.75)).normalized()
cam.location = t + d * 20
cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_end = 100
sc.render.filepath = OUT + ".hi.png"
bpy.ops.render.render(write_still=True)
from PIL import Image
Image.open(OUT + ".hi.png").resize((256, 256), Image.LANCZOS).save(OUT)
os.remove(OUT + ".hi.png")
print("ICON", OUT)
