"""Same camera + light for v1 (original), v2 (previous) and the HQ model; rendered as v1.png, v2.png, v3.png.

    python3 compare.py -- V1.glb V2.glb HQ.blend OUTDIR [RES] [SPP] [--root RockSlingerHQ] [--scale 1.143]
                          [--action Whirl] [--frame 6] [--height 3.3]
--scale = HQ model_scale / old model_scale, so all three stand at their in-game size."""
import sys, os, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
sys.path.insert(0, os.path.dirname(HQ))
import bpy
from mathutils import Vector
import look

ARGS = sys.argv[sys.argv.index("--") + 1:]
POS = [a for i, a in enumerate(ARGS) if not a.startswith("--") and (i == 0 or not ARGS[i - 1].startswith("--"))]
V1, V2, HQBLEND, OUTDIR = POS[:4]
RES = int(POS[4]) if len(POS) > 4 else 700
SPP = int(POS[5]) if len(POS) > 5 else 64
def opt(n, d):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d
ROOT = opt("--root", "RockSlingerHQ")
HQ_SCALE = float(opt("--scale", str(0.64 / 0.56)))
ACTION, FRAME = opt("--action", "Whirl"), int(opt("--frame", "6"))
HEIGHT = float(opt("--height", "3.3"))
os.makedirs(OUTDIR, exist_ok=True)


def cam_shot(path, height):
    sc = bpy.context.scene
    look.setup(samples=SPP, res=(RES, int(RES * 1.15)), transparent=True)
    t = (0.0, 0.1, height * 0.46)
    look.camera(t, 11.5 * height / 3.3, 24, 16, lens=55)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def glb(path, out):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    import icon_fix
    icon_fix.srgb_vertex_colors()
    for o in list(bpy.context.scene.objects):        # in-game outline shells need backface culling (not in Cycles)
        if o.name.endswith("_Outline"):
            o.hide_render = True
    cam_shot(out, HEIGHT)


glb(V1, os.path.join(OUTDIR, "v1.png"))
glb(V2, os.path.join(OUTDIR, "v2.png"))
bpy.ops.wm.open_mainfile(filepath=HQBLEND)
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
arm.animation_data.action = bpy.data.actions[ACTION]
bpy.context.scene.frame_set(FRAME)
root = bpy.data.objects.get(ROOT)
if root is not None:
    root.scale = (HQ_SCALE, HQ_SCALE, HQ_SCALE)      # same in-game size as the others
cam_shot(os.path.join(OUTDIR, "v3.png"), HEIGHT)
