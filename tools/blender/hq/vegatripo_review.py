"""Review renders of the Tripo Vega (vegatripo_rig.py's vega_hq.blend) beside the old one.

    python3 vegatripo_review.py -- --new NEW_hq.blend --old OLD_hq.blend --out DIR [--res 512] [--samples 24] [--only turn,clips,face,cmp]

turn.png: front, three-quarter, back, side in the rest pose; clips.png: frames of the five clips (Attack 2, Ability 27
and 34 among them); face.png: the head close up; old_vs_new.png: the old and the new Vega on the base, same cameras.
"""
import sys, os, math
import numpy as np
import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d

NEW, OLD, OUT = arg("--new"), arg("--old"), arg("--out", "review")
RES, SPP = int(arg("--res", "512")), int(arg("--samples", "24"))
ONLY = arg("--only", "turn,clips,face,cmp").split(",")
os.makedirs(OUT, exist_ok=True)
CLIPS_ARG = arg("--clips")
CLIPS = [("Idle", 0), ("Idle", 60), ("Combat", 0), ("Combat", 20), ("Attack", 0), ("Attack", 2), ("Attack", 5), ("Attack", 10),
         ("Ability", 8), ("Ability", 18), ("Ability", 27), ("Ability", 34), ("Ability", 50), ("Cheer", 12), ("Cheer", 24), ("Cheer", 36)]


if CLIPS_ARG:
    CLIPS = [(c.split("@")[0], int(c.split("@")[1])) for c in CLIPS_ARG.split(",")]
CAM = [float(v) for v in arg("--cam", "0,-0.15,1.21,32,16,3.0").split(",")]


def setup(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    for im in bpy.data.images:            # (a build's blend points at the runner's paths: look beside the blend)
        if im.source == "FILE" and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)):
            alt = os.path.join(os.path.dirname(os.path.abspath(path)), os.path.basename(im.filepath))
            if os.path.exists(alt):
                im.filepath = alt
                im.reload()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SPP
    sc.cycles.use_denoising = True
    sc.cycles.device = "CPU"
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("RW")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.66, 0.72, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    sun = bpy.data.objects.new("RSun", bpy.data.lights.new("RSun", "SUN"))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(42), 0, math.radians(-35))
    sc.collection.objects.link(sun)
    return sc, bpy.data.objects["CavemanRig"]


def pose(arm, action, frame):
    arm.animation_data_create()
    if action is None:
        arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.location = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.scale = (1, 1, 1)
        bpy.context.scene.frame_set(0)
        return
    act = bpy.data.actions[action]
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    bpy.context.scene.frame_set(frame)


def camera(sc, target, az, el, dist=6.0, ortho=None, lens=60):
    t = Vector(target)
    a, e = math.radians(az), math.radians(el)
    cd = bpy.data.cameras.new("RC")
    cd.lens = lens
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    cd.clip_start = 0.01
    co = bpy.data.objects.new("RC", cd)
    sc.collection.objects.link(co)
    co.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    co.rotation_euler = (t - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    return co


def shot(sc, path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def sheet(paths, out, cols, labels=None):
    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    M = Image.new("RGB", (w * cols, h * rows), (30, 30, 30))
    d = ImageDraw.Draw(M)
    for i, im in enumerate(ims):
        M.paste(im, ((i % cols) * w, (i // cols) * h))
        if labels:
            d.text(((i % cols) * w + 8, (i // cols) * h + 6), labels[i], fill=(255, 255, 255))
    M.save(out)
    for p in paths:
        os.remove(p)


Z0 = 0.16                     # (the Yaw node: he stands on the base's top)
if "turn" in ONLY:
    sc, arm = setup(NEW)
    pose(arm, None, 0)
    ps = []
    for k, az in enumerate((0, 35, 180, 90)):
        camera(sc, (0, 0, Z0 + 1.0), az, 8, ortho=2.5)
        ps.append(shot(sc, os.path.join(OUT, "_t%d.png" % k)))
    sheet(ps, os.path.join(OUT, "turn.png"), 4, ["front", "three-quarter", "back", "side (his left)"])
if "face" in ONLY:
    sc, arm = setup(NEW)
    pose(arm, None, 0)
    hb = arm.pose.bones["head"]
    hc = arm.matrix_world @ (hb.head + (hb.tail - hb.head) * 0.32)
    ps = []
    for k, (az, el) in enumerate(((0, 4), (-35, 6), (30, 18))):
        camera(sc, hc + Vector((0, -0.02, 0)), az, el, ortho=0.62)
        ps.append(shot(sc, os.path.join(OUT, "_f%d.png" % k)))
    sheet(ps, os.path.join(OUT, "face.png"), 3, ["front", "three-quarter right", "high three-quarter left"])
if "clips" in ONLY:
    sc, arm = setup(NEW)
    ps, labels = [], []
    for k, (act, fr) in enumerate(CLIPS):
        pose(arm, act, fr)
        camera(sc, tuple(CAM[:3]), CAM[3], CAM[4], ortho=CAM[5])
        ps.append(shot(sc, os.path.join(OUT, "_c%d.png" % k)))
        labels.append("%s %d" % (act, fr))
    sheet(ps, os.path.join(OUT, "clips.png"), 4, labels)
if "cmp" in ONLY:
    ps, labels = [], []
    for nm, path in (("old", OLD), ("new", NEW)):
        sc, arm = setup(path)
        for k, (act, fr, az, el, o) in enumerate(((None, 0, 0, 6, 3.0), ("Idle", 0, 35, 30, 3.0), ("Attack", 2, 35, 30, 3.0))):
            pose(arm, act, fr)
            camera(sc, (0, 0, Z0 + 0.9), az, el, ortho=o)
            ps.append(shot(sc, os.path.join(OUT, "_o%s%d.png" % (nm, k))))
            labels.append("%s: %s" % (nm, "rest" if act is None else "%s %d" % (act, fr)))
    sheet(ps, os.path.join(OUT, "old_vs_new.png"), 3, labels)
print("[review] done", OUT)
