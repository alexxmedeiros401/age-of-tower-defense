"""_dc_views.py -- BLEND OUTDIR ACTION:f0,f1,step[:az,el] ...   frames of clips from a chosen camera, one sheet per spec.
(the frame box is fixed per sheet: the union over its frames, so motion reads)"""
import sys, os, math
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import bpy
from mathutils import Vector
import look
A = sys.argv[sys.argv.index("--") + 1:]
BLEND, OUT = A[0], A[1]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
look.relink(BLEND)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.clip_end = 200
look.setup(samples=20, res=(380, 380), transparent=False)
from PIL import Image
for spec in A[2:]:
    p = spec.split(":")
    act = p[0]
    f0, f1, st = [int(x) for x in p[1].split(",")]
    az, el = [float(x) for x in p[2].split(",")] if len(p) > 2 else (-30.0, 45.0)
    arm.animation_data.action = bpy.data.actions[act]
    try:
        arm.animation_data.action_slot = bpy.data.actions[act].slots[0]
    except Exception:
        pass
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = Vector((0, 0, 1.0)) + d * 40
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    inv = cam.matrix_world.inverted()
    frames = list(range(f0, f1 + 1, st))
    xs, ys = [], []
    for f in frames:
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        for o in sc.objects:
            if o.type != "MESH":
                continue
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            M = inv @ ev.matrix_world
            vs = me.vertices
            for i in range(0, len(vs), 7):
                q = M @ vs[i].co
                xs.append(q.x); ys.append(q.y)
            ev.to_mesh_clear()
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    cam.data.ortho_scale = max(w, h) * 1.1
    cam.location = cam.matrix_world @ Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0))
    tiles = []
    for f in frames:
        sc.frame_set(f)
        pth = os.path.join(OUT, "%s_%03d.png" % (act, f))
        sc.render.filepath = pth
        bpy.ops.render.render(write_still=True)
        tiles.append(Image.open(pth).convert("RGB"))
        os.remove(pth)
    cols = min(8, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (380 * cols, 380 * rows))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 380, (i // cols) * 380))
    sheet.save(os.path.join(OUT, "sheet_%s_%d_%d.png" % (act, int(az), int(el))))
    print("SHEET", act, frames)
