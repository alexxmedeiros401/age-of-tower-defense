"""Cycles renders of the finished game asset (the exact meshes/textures/animation that ship)."""
import sys, os, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import bpy
from mathutils import Vector
import look, mats

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d
BLEND = arg("--blend")
OUTDIR = arg("--out")
MODE = arg("--mode", "hero")
RES = int(arg("--res", "1200"))
SPP = int(arg("--spp", "96"))
ACTION = arg("--action", "Whirl")
FRAME = int(arg("--frame", "5"))
os.makedirs(OUTDIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
outline = mats.outline_mat()


def add_outline(ob, width):
    ob.data.materials.append(outline)
    m = ob.modifiers.new("Outline", "SOLIDIFY")
    m.thickness = width
    m.offset = 1.0
    m.use_flip_normals = True
    m.use_rim = False
    m.material_offset = len(ob.data.materials) - 1


if "--outline" in ARGS:
    for o in sc.objects:
        if o.type == "MESH" and o.name in ("Caveman", "Ugo", "Base"):
            add_outline(o, 0.016 if o.name == "Base" else 0.012)
    # the flame should glow, not be outlined
look.setup(samples=SPP, res=(RES, int(RES * 1.12)) if MODE != "turntable" else (RES, RES))
yaw = bpy.data.objects.get("Yaw")
TOP = yaw.location.z if yaw is not None else 0.9          # where the character stands
TZ = float(arg("--tz", "1.55"))


def pose(action, frame):
    arm.animation_data.action = bpy.data.actions[action]
    sc.frame_set(frame)


def render(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    look.backdrop(path, path.replace(".png", "_bg.png"))


if MODE == "hero":
    pose(ACTION, FRAME)
    look.camera((0.0, 0.15, TZ), float(arg("--dist", "10.0")), float(arg("--az", "24")), float(arg("--el", "15")), lens=60)
    render(os.path.join(OUTDIR, "hero_%s_%d.png" % (ACTION, FRAME)))
elif MODE == "closeup":
    pose(ACTION, FRAME)
    look.camera((-0.1, 0.0, TOP + float(arg("--head", "1.55"))), float(arg("--dist", "4.0")), float(arg("--az", "22")), float(arg("--el", "9")), lens=80)
    render(os.path.join(OUTDIR, "close_%s_%d.png" % (ACTION, FRAME)))
elif MODE == "game":
    pose(ACTION, FRAME)
    look.camera((0.0, 0.0, 1.0), 14.0, 0, 62, lens=50)
    render(os.path.join(OUTDIR, "gameview_%s_%d.png" % (ACTION, FRAME)))
elif MODE == "frames":
    # animation strip: every Nth frame of the action
    step = int(arg("--step", "1"))
    start, end = [int(x) for x in arg("--range", "0,24").split(",")]
    look.camera((0.0, 0.15, float(arg("--tz", "1.6"))), float(arg("--dist", "10.5")), float(arg("--az", "24")), float(arg("--el", "15")), lens=60)
    for f in range(start, end + 1, step):
        pose(ACTION, f)
        sc.render.filepath = os.path.join(OUTDIR, "f_%s_%03d.png" % (ACTION, f))
        bpy.ops.render.render(write_still=True)
