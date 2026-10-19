"""HQ robots: a hard-surface distance-field sculpt -> rigid-skinned, animated, texture-baked game GLB.

    python3 robot_build.py -- --robot walker --out DIR [--stage sculpt|game|export|all] [--fine] [--tex 2048]
                              [--ao 24] [--shots DIR]

A robot is built from rigid parts (plates, joints, pistons), each sculpted as its own distance field and owned by one
bone, so it moves like a machine: every part is weighted 100% to its bone. The robot module (robot_walker.py, ...) gives:
  ROOT_NAME, GLB_NAME, TEX_PREFIX          root node / file / texture names
  BONES: [(bone, head, tail, parent)]      armature, Z up, the robot faces -Y
  parts(fine) -> [(part, Field, voxel, bone, material key)]
  MATS: {material key: (recipe in robot_mats, kwargs)}
  LOW_TARGETS: {part: triangles}           game-mesh budget per part
  GLOW: {part: (colour, strength[, albedo factor])}   eyes, cores, thrusters: shipped as emissive meshes, not baked
  clips(arm_ob)                            keys the actions (Walk or Fly, and any one-shots such as Summon)
Stages: sculpt (high-poly + optional clay/material shots), game (materials, low-poly, UVs, bakes, rig, clips), export.
"""
import sys, os, time, math, importlib
HQ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HQ)
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d

RB = importlib.import_module("robot_" + arg("--robot", "walker"))
import sdf, mats, prep, robot_mats as rm
import lowpoly as lp
import bake as bk

OUT = arg("--out", "out_" + RB.GLB_NAME)
STAGE = arg("--stage", "all")
TEX = int(arg("--tex", "2048"))
AO_SPP = int(arg("--ao", "24"))
FINE = "--fine" in ARGS
os.makedirs(OUT, exist_ok=True)
HI = os.path.join(OUT, "robot_hi.blend")
GAME = os.path.join(OUT, "robot_game.blend")


def log(*a):
    print("[robot]", *a, flush=True)


def glow_material(name, col, strength, base=1.0):
    gm = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    gm.use_nodes = True
    b = gm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = mats.lin(tuple(c * base for c in col))
    b.inputs["Roughness"].default_value = 0.25
    b.inputs["Emission Color"].default_value = mats.lin(col)
    b.inputs["Emission Strength"].default_value = strength
    return gm


def materials():
    cache = {}
    for key, (fn, kw) in RB.MATS.items():
        cache[key] = getattr(rm, fn)(**kw)
    return cache


def assign(objs):
    cache = materials()
    for o in objs:
        key = o.get("mat")
        if key in cache:
            o.data.materials.clear()
            o.data.materials.append(cache[key])


# ------------------------------------------------------------------------------------------------ sculpt
def sculpt_stage():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    T = time.time()
    for name, f, vx, bone, mkey in RB.parts(FINE):
        V, Fc = f.mesh(vx)
        V, Fc = sdf.clean_islands(V, Fc, min_tris=20)
        ob = sdf.to_blender(name, V, Fc)
        ob["bone"] = bone
        ob["mat"] = mkey
        if any(op[0] == "paint" for op in f.ops):
            d, lab = f.eval(V.astype(np.float32), labels=True)
            a = ob.data.attributes.new("region", "INT", "POINT")
            a.data.foreach_set("value", lab.astype(np.int32))
            for L, dd in f.paint_dist(V.astype(np.float32)).items():
                pa = ob.data.attributes.new("p%d" % L, "FLOAT", "POINT")
                pa.data.foreach_set("value", np.clip(0.5 - dd / 0.004, -2.0, 3.0).astype(np.float32))
    log("sculpted in %.0fs" % (time.time() - T))
    bpy.ops.wm.save_as_mainfile(filepath=HI)
    if arg("--shots"):
        shots(arg("--shots"))


def shots(D, game=False):
    """Material preview renders of the high-poly (or of the game mesh) from four sides."""
    os.makedirs(D, exist_ok=True)
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not game:
        for o in objs:
            sdf.fix_winding(o)
            prep.region_masks(o)
        assign(objs)
        for nm, spec in getattr(RB, "GLOW", {}).items():
            o = bpy.data.objects.get(nm)
            if o is not None:
                o.data.materials.clear()
                o.data.materials.append(glow_material("Glow" + nm, *spec))
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.render.film_transparent = False
    sc.render.resolution_x, sc.render.resolution_y = 640, 760
    sc.view_settings.view_transform = "Standard"
    wd = bpy.data.worlds.new("W")
    sc.world = wd
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.5, 0.6, 1)
    wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    lo = np.array([1e9] * 3)
    hi = -lo
    for o in objs:
        for c in o.bound_box:
            w = np.array(o.matrix_world @ Vector(c))
            lo, hi = np.minimum(lo, w), np.maximum(hi, w)
    ctr = Vector(((lo + hi) / 2).tolist())
    size = float(np.max(hi - lo))
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
    sc.collection.objects.link(sun)
    cd = bpy.data.cameras.new("C")
    cd.lens = 70
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    from PIL import Image
    ims = []
    for i, az in enumerate((-25, 35, 120, 200)):
        a = math.radians(az)
        d = size * 3.2
        cam.location = ctr + Vector((math.sin(a) * d, -math.cos(a) * d, d * 0.35))
        cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(D, "shot_%d.png" % i)
        bpy.ops.render.render(write_still=True)
        ims.append(Image.open(sc.render.filepath))
    sheet = Image.new("RGB", (640 * 4, 760))
    for i, im in enumerate(ims):
        sheet.paste(im, (i * 640, 0))
    sheet.save(os.path.join(D, "sheet.png"))
    log("shots ->", D)


# ------------------------------------------------------------------------------------------------ game mesh
def build_armature():
    arm = bpy.data.armatures.new(RB.ROOT_NAME + "Rig")
    ob = bpy.data.objects.new(RB.ROOT_NAME + "Rig", arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    for nm, h, t, par in RB.BONES:
        eb = arm.edit_bones.new(nm)
        eb.head = Vector(h)
        eb.tail = Vector(t)
        if par:
            eb.parent = arm.edit_bones[par]
            eb.use_connect = False
        d = (eb.tail - eb.head).normalized()
        eb.align_roll(Vector((0, -1, 0)) if abs(d.y) < 0.9 else Vector((0, 0, 1)))
    bpy.ops.object.mode_set(mode="OBJECT")
    for b in arm.bones:
        b.use_deform = True
    for pb in ob.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return ob


def rigid(ob, bone):
    g = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
    g.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")


def game_stage():
    T = time.time()
    bpy.ops.wm.open_mainfile(filepath=HI)
    hi = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
    for o in hi.values():
        sdf.fix_winding(o)
        prep.region_masks(o)
    assign(list(hi.values()))
    glow = getattr(RB, "GLOW", {})
    names = [n for n in hi if n not in glow]
    pid = {n: i for i, n in enumerate(names)}
    low = {}
    for n in names:
        lo_ob = lp.decimated_copy(hi[n], RB.LOW_TARGETS.get(n, 600), n + "_low")
        lp.tag_part(lo_ob, pid[n])
        rigid(lo_ob, hi[n]["bone"])
        low[n] = lo_ob
    log("lowpoly", {k: len(v.data.polygons) for k, v in low.items()}, "%.0fs" % (time.time() - T))
    robot = lp.join(list(low.values()), "Robot")
    robot.data.validate(clean_customdata=False)
    lp.unwrap(robot, margin=0.004)
    log("uv done %.0fs" % (time.time() - T))
    groups = [([pid[n]], [hi[n]]) for n in names]
    maps = bk.bake_groups(robot, groups, TEX, ["DIFFUSE", "NORMAL", "ROUGHNESS", "AO"], ao_samples=AO_SPP, ao_dist=0.1,
                          extrusion=0.01, maxdist=0.03)
    log("bakes %.0fs" % (time.time() - T))
    pa, pn, po = bk.save_maps(maps, OUT, RB.TEX_PREFIX, ao_strength=0.65, sat=1.08, val=1.02)
    robot.data.materials.clear()
    robot.data.materials.append(bk.game_material(RB.ROOT_NAME + "Mat", pa, pn, po))
    robot.name = robot.data.name = RB.ROOT_NAME + "Mesh"
    arm = build_armature()
    glow_obs = []
    for n, spec in glow.items():
        if n not in hi:
            continue
        g = lp.decimated_copy(hi[n], RB.LOW_TARGETS.get(n, 300), "Glow" + n)
        rigid(g, hi[n]["bone"])
        g.data.materials.clear()
        g.data.materials.append(glow_material("Glow" + n, *spec))
        for p in g.data.polygons:
            p.use_smooth = True
        glow_obs.append(g)
    for o in [robot] + glow_obs:
        for m in list(o.modifiers):
            o.modifiers.remove(m)
        m = o.modifiers.new("Armature", "ARMATURE")
        m.object = arm
        o.parent = arm
    RB.clips(arm)
    for o in hi.values():
        bpy.data.objects.remove(o)
    for me in [me for me in bpy.data.meshes if me.users == 0]:
        bpy.data.meshes.remove(me)
    bpy.ops.wm.save_as_mainfile(filepath=GAME)
    log("game done %.0fs, tris %d + glow %d" % (time.time() - T, len(robot.data.polygons), sum(len(g.data.polygons) for g in glow_obs)))


def export_stage():
    bpy.ops.wm.open_mainfile(filepath=GAME)
    sc = bpy.context.scene
    root = bpy.data.objects.new(RB.ROOT_NAME, None)
    sc.collection.objects.link(root)
    for o in sc.objects:
        if o.parent is None and o is not root:
            o.parent = root
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, RB.GLB_NAME + "_hq.blend"))
    path = os.path.join(OUT, RB.GLB_NAME + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                              export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                              export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
    log("exported", path, os.path.getsize(path))


if STAGE in ("sculpt", "all"):
    sculpt_stage()
if STAGE in ("game", "all"):
    game_stage()
if STAGE in ("export", "all"):
    export_stage()
if STAGE == "shots":
    bpy.ops.wm.open_mainfile(filepath=HI)
    shots(arg("--shots", os.path.join(OUT, "shots")))
