"""Head-and-shoulders portrait (assets/ui/face_<id>.png) of an HQ hero, rendered from its *_hq.blend.

    python3 face_hq.py -- HQ_BLEND OUT.png [--action Idle] [--frame 0] [--target X,Y,Z] [--scale 0.8] [--az 22] [--el 6]
"""
import sys, os, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import bpy
from mathutils import Vector
import look

ARGS = sys.argv[sys.argv.index("--") + 1:]
BLEND, OUT = ARGS[0], ARGS[1]
def opt(n, d):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d
ACTION, FRAME = opt("--action", "Idle"), int(opt("--frame", "0"))
TGT = Vector([float(x) for x in opt("--target", "0,0.0,2.2").split(",")])
SCALE = float(opt("--scale", "0.8"))
AZ, EL = float(opt("--az", "22")), float(opt("--el", "6"))
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
arm.animation_data.action = bpy.data.actions[ACTION]
sc.frame_set(FRAME)
look.setup(samples=128, res=(512, 512), transparent=True)
FILL = float(opt("--fill", "2.0"))
for o in bpy.data.objects:                      # portraits read best with a softer, brighter fill
    if o.type == "LIGHT" and o.name == "Fill":
        o.data.energy *= FILL
cam = bpy.data.objects.new("FaceCam", bpy.data.cameras.new("FaceCam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = SCALE
az, el = math.radians(AZ), math.radians(EL)
d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
cam.location = TGT + d * 20
cam.rotation_euler = (TGT - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_end = 100
sc.render.filepath = OUT + ".hi.png"
bpy.ops.render.render(write_still=True)
from PIL import Image, ImageFilter
im = Image.open(OUT + ".hi.png").convert("RGBA")
if "--no-outline" not in ARGS:                 # dark cartoon outline round the silhouette, like the other portraits
    a = im.split()[3].point(lambda v: 255 if v > 40 else 0)
    ring = a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.2))
    bg = Image.new("RGBA", im.size, (24, 18, 14, 0))
    bg.putalpha(ring)
    bg.alpha_composite(im)
    im = bg
im.resize((256, 256), Image.LANCZOS).save(OUT)
os.remove(OUT + ".hi.png")
print("FACE", OUT)
