"""Same camera + light for v1 (original), v2 (current) and the HQ model; composited side by side."""
import sys, os, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
sys.path.insert(0, os.path.dirname(HQ))
import bpy
from mathutils import Vector
import look

ARGS = sys.argv[sys.argv.index("--") + 1:]
V1, V2, HQBLEND, OUTDIR = ARGS[:4]
RES = int(ARGS[4]) if len(ARGS) > 4 else 700
SPP = int(ARGS[5]) if len(ARGS) > 5 else 64
HQ_SCALE = 0.64 / 0.56
os.makedirs(OUTDIR, exist_ok=True)


def cam_shot(path, height):
    sc = bpy.context.scene
    look.setup(samples=SPP, res=(RES, int(RES * 1.15)), transparent=True)
    t = (0.0, 0.1, height * 0.46)
    look.camera(t, 11.5, 24, 16, lens=55)
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
    pts = [o.matrix_world @ Vector(c) for o in bpy.context.scene.objects if o.type == "MESH" for c in o.bound_box]
    cam_shot(out, 3.3)


glb(V1, os.path.join(OUTDIR, "v1.png"))
glb(V2, os.path.join(OUTDIR, "v2.png"))
bpy.ops.wm.open_mainfile(filepath=HQBLEND)
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
arm.animation_data.action = bpy.data.actions["Whirl"]
bpy.context.scene.frame_set(6)
root = bpy.data.objects.get("RockSlingerHQ")
if root is not None:
    root.scale = (HQ_SCALE, HQ_SCALE, HQ_SCALE)      # same in-game size as the others (model_scale 0.64 vs 0.56)
cam_shot(os.path.join(OUTDIR, "v3.png"), 3.3)
