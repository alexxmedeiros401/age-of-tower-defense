"""Generic Tripo hero, step 8: review renders of the rebuilt hero (herotripo_rig.py's <id>_hq.blend) beside the old one.

    python3 herotripo_review.py -- --hero ugo --new OUT/ugo_hq.blend --out OUT [--res 512] [--samples 24]
                                   [--only turn,face,clips,cmp,close]
                                   [--az 32 --el 16 --frames Ability@8,Cheer@20 --name clips_back]   (other clip views)

turn.png: front, three-quarter, back, side in the rest pose; face.png: three head close-ups; clips.png: frames across
all five clips (cfg "review_frames" adds key frames, e.g. the attack frame and the ability's key frame); old_vs_new.png:
the old (cfg "old") and the new hero, same cameras, rest pose and two clip frames (cfg "cmp_frames"); closeups.png:
each prop's hand and each armour piece's bone close up in the clips' most extreme frames (the frames where the bone
is farthest from its rest-pose place, plus cfg "closeup_frames"). Cameras are framed on the scene's bounding box.
"""
import sys, os, math, json
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
sys.path.insert(0, os.path.join(HQ, "herotripo_prep"))
import numpy as np
import bpy
from mathutils import Vector
import common as C

HID = C.arg("--hero")
CFG = C.load_cfg(HID)
NEW = C.arg("--new")
OUT = C.arg("--out", "review")
RES, SPP = int(C.arg("--res", "512")), int(C.arg("--samples", "24"))
ONLY = C.arg("--only", "turn,face,clips,cmp,close").split(",")
os.makedirs(OUT, exist_ok=True)
WK = C.work_dir(HID)
INFO = json.load(open(os.path.join(WK, "old.json")))


def setup(path):
    import old as oldmod
    oldmod.open_old(path)
    for im in bpy.data.images:
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


def acts():
    """{clip name: action} (the glTF importer may name actions 'Idle' or 'CavemanRig|Idle')."""
    return {a.name.split("|")[-1]: a for a in bpy.data.actions}


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
    act = acts()[action]
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    bpy.context.scene.frame_set(frame)


def camera(sc, target, az, el, ortho, dist=8.0):
    t = Vector(target)
    a, e = math.radians(az), math.radians(el)
    cd = bpy.data.cameras.new("RC")
    cd.type = "ORTHO"
    cd.ortho_scale = ortho
    cd.clip_start = 0.01
    cd.clip_end = 100
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


def frame_box():
    """World bbox of the hero (rest) and of the whole scene's meshes."""
    hero = bpy.data.objects[INFO["mesh"]]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = hero.evaluated_get(dg)
    co = np.array([hero.matrix_world @ v.co for v in ev.to_mesh().vertices])
    ev.to_mesh_clear()
    return co.min(0), co.max(0)


def bone_world(arm, name, at=0.0):
    pb = arm.pose.bones[name]
    return arm.matrix_world @ (pb.head + (pb.tail - pb.head) * at)


CLIPS = [a for a in ("Idle", "Combat", "Whirl", "Attack", "Throw", "Ability", "Cheer") if a in INFO["actions"] or any(k.split("|")[-1] == a for k in INFO["actions"])]


def clip_frames():
    out = []
    rng = {k.split("|")[-1]: v for k, v in INFO["actions"].items()}
    extra = CFG.get("review_frames", {})
    for a in CLIPS:
        f0, f1 = rng[a]
        fr = sorted(set([int(round(f0 + (f1 - f0) * t)) for t in (0.0, 0.33, 0.66)] + [int(x) for x in extra.get(a, [])]))
        out += [(a, f) for f in fr]
    return out


def body_target(lo, hi):
    return ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)


if "turn" in ONLY:
    sc, arm = setup(NEW)
    pose(arm, None, 0)
    lo, hi = frame_box()
    tg, o = body_target(lo, hi), (hi[2] - lo[2]) * 1.12
    ps = []
    for k, az in enumerate((0, 35, 180, 90)):
        camera(sc, tg, az, 8, o)
        ps.append(shot(sc, os.path.join(OUT, "_t%d.png" % k)))
    sheet(ps, os.path.join(OUT, "turn.png"), 4, ["front", "three-quarter", "back", "side (his left)"])
if "face" in ONLY:
    sc, arm = setup(NEW)
    pose(arm, None, 0)
    hc = bone_world(arm, "head", 0.32)
    hl = (arm.pose.bones["head"].tail - arm.pose.bones["head"].head).length
    ps = []
    for k, (az, el) in enumerate(((0, 4), (-35, 6), (30, 18))):
        camera(sc, hc + Vector((0, -0.02, 0)), az, el, hl * 1.55)
        ps.append(shot(sc, os.path.join(OUT, "_f%d.png" % k)))
    sheet(ps, os.path.join(OUT, "face.png"), 3, ["front", "three-quarter right", "high three-quarter left"])
if "clips" in ONLY:
    sc, arm = setup(NEW)
    pose(arm, None, 0)
    lo, hi = frame_box()
    tg, o = body_target(lo, hi), (hi[2] - lo[2]) * 1.25
    ps, labels = [], []
    AZ, EL = float(C.arg("--az", "32")), float(C.arg("--el", "16"))
    FR = C.arg("--frames")                      # e.g. Ability@8,Ability@20 (instead of the default frames)
    frames = [(x.split("@")[0], int(x.split("@")[1])) for x in FR.split(",")] if FR else clip_frames()
    for k, (act, fr) in enumerate(frames):
        pose(arm, act, fr)
        camera(sc, tg, AZ, EL, o)
        ps.append(shot(sc, os.path.join(OUT, "_c%d.png" % k)))
        labels.append("%s %d" % (act, fr))
    sheet(ps, os.path.join(OUT, C.arg("--name", "clips") + ".png"), 5, labels)
if "cmp" in ONLY:
    ps, labels = [], []
    cmpf = [tuple(x) for x in CFG.get("cmp_frames", [])] or [clip_frames()[1], (CLIPS[-2], int(np.mean({k.split("|")[-1]: v for k, v in INFO["actions"].items()}[CLIPS[-2]])))]
    for nm, path in (("old", CFG["old"]), ("new", NEW)):
        sc, arm = setup(path)
        pose(arm, None, 0)
        lo, hi = frame_box()
        tg, o = body_target(lo, hi), (hi[2] - lo[2]) * 1.3
        for k, (act, fr, az, el) in enumerate(((None, 0, 0, 6), (cmpf[0][0], cmpf[0][1], 35, 25), (cmpf[1][0], cmpf[1][1], 35, 25))):
            pose(arm, act, fr)
            camera(sc, tg, az, el, o)
            ps.append(shot(sc, os.path.join(OUT, "_o%s%d.png" % (nm, k))))
            labels.append("%s: %s" % (nm, "rest" if act is None else "%s %d" % (act, fr)))
    sheet(ps, os.path.join(OUT, "old_vs_new.png"), 3, labels)
if "close" in ONLY:
    sc, arm = setup(NEW)
    pose(arm, None, 0)
    lo, hi = frame_box()
    H = hi[2] - lo[2]
    items = []                                   # (label, bone to look at, along, ortho)
    for p in CFG["props"]:
        if p.get("drop") or p.get("within"):
            continue
        b = p.get("bone", p["name"])
        hand = b
        while hand and not hand.startswith("hand"):
            hand = INFO["bones"][hand]["parent"]
        items.append((p["name"], (hand or b, b), 0.5, H * 0.42))
    for a in CFG["armour"]:
        items.append((a["name"], (list(a["bones"])[0],), 0.1, H * 0.35))
    ps, labels = [], []
    def look_at(bs, along):
        return sum((bone_world(arm, b_, along) for b_ in bs), Vector()) / len(bs)
    for nm, bone, along, o in items:
        # the frames where the bone strays farthest from its rest place (in the Yaw's frame), one per clip
        pose(arm, None, 0)
        r0 = look_at(bone, along)
        best = []
        for a in CLIPS:
            rng = {k.split("|")[-1]: v for k, v in INFO["actions"].items()}[a]
            dd = []
            for f in range(int(rng[0]), int(rng[1]) + 1, 2):
                pose(arm, a, f)
                dd.append(((look_at(bone, along) - r0).length, f))
            best.append((a, max(dd)[1]))
        frames = [(None, 0)] + best + [tuple(x) for x in CFG.get("closeup_frames", {}).get(nm, [])]
        for act, fr in frames:
            pose(arm, act, fr)
            c = look_at(bone, along)
            camera(sc, c, 30, 12, o)
            ps.append(shot(sc, os.path.join(OUT, "_x%d.png" % len(ps))))
            labels.append("%s: %s" % (nm, "rest" if act is None else "%s %d" % (act, fr)))
    if ps:
        sheet(ps, os.path.join(OUT, "closeups.png"), 6 if len(ps) > 8 else 4, labels)
print("[review] done", OUT)
