"""Renders of a finished HQ robot (the shipped meshes, textures and clips).

    python3 robot_icon.py -- BLEND OUT.png [--action Walk] [--frame 6] [--size 256] [--margin 0.06]   portrait icon
    python3 robot_icon.py -- BLEND DIR --strip [--action Walk] [--every 3]                 animation strip (side view)
"""
import sys, os, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import bpy
from mathutils import Vector
import look

ARGS = sys.argv[sys.argv.index("--") + 1:]
BLEND, OUT = ARGS[0], ARGS[1]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d
ACTION = arg("--action")
FRAME = int(arg("--frame", "6"))
SIZE = int(arg("--size", "256"))

bpy.ops.wm.open_mainfile(filepath=BLEND)

import look as _look

_look.relink(BLEND)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
if ACTION is None:
    ACTION = "Walk" if "Walk" in bpy.data.actions else "Fly"
arm.animation_data.action = bpy.data.actions[ACTION]
for slot in getattr(arm.animation_data, "action_suitable_slots", [])[:1]:
    arm.animation_data.action_slot = slot


def frame_box(cam, margin=0.05):
    """Ortho framing on the posed meshes, as seen by `cam`."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    inv = cam.matrix_world.inverted()
    xs, ys = [], []
    for o in sc.objects:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        M = inv @ ev.matrix_world
        for v in me.vertices:
            p = M @ v.co
            xs.append(p.x)
            ys.append(p.y)
        ev.to_mesh_clear()
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    cam.data.ortho_scale = max(w, h) * (1 + 2 * margin)
    cam.location = cam.matrix_world @ Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0))


cam = bpy.data.objects.new("IconCam", bpy.data.cameras.new("IconCam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.clip_end = 200
if "--strip" in ARGS:
    os.makedirs(OUT, exist_ok=True)
    look.setup(samples=24, res=(420, 520), transparent=False)
    every = int(arg("--every", "3"))
    act = bpy.data.actions[ACTION]
    f0, f1 = [int(x) for x in act.frame_range]
    from PIL import Image
    tiles = []
    for f in range(f0, f1, every):
        sc.frame_set(f)
        d = Vector((1.0, -0.35, 0.25)).normalized()
        cam.location = Vector((0, 0, 0.8)) + d * 30
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        frame_box(cam, 0.12)
        p = os.path.join(OUT, "f_%03d.png" % f)
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        tiles.append(Image.open(p).convert("RGB"))
    sheet = Image.new("RGB", (420 * len(tiles), 520))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * 420, 0))
    sheet.save(os.path.join(OUT, "strip_%s.png" % ACTION))
    print("STRIP", OUT)
else:
    sc.frame_set(FRAME)
    look.setup(samples=96, res=(512, 512), transparent=True)
    d = Vector((0.7, -1.2, 0.6)).normalized()
    cam.location = Vector((0, 0, 0.8)) + d * 30
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    frame_box(cam, float(arg("--margin", "0.06")))
    sc.render.filepath = OUT + ".hi.png"
    bpy.ops.render.render(write_still=True)
    from PIL import Image
    Image.open(OUT + ".hi.png").resize((SIZE, SIZE), Image.LANCZOS).save(OUT)
    os.remove(OUT + ".hi.png")
    print("ICON", OUT)
