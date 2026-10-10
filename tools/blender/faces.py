"""Renders head-and-shoulders portraits (assets/ui/face_<id>.png) for every hero GLB.
Heroes are built by lp.person / eras_a.figure, whose head sits at Body-local (0, -0.02, 1.16) facing -Y.
Run: python3 tools/blender/faces.py [hero ...]"""
import sys, os, math, json, bpy
from mathutils import Vector
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
heroes = json.load(open(os.path.join(ROOT, "data", "heroes.json")))["heroes"]
names = [a for a in sys.argv[1:] if a in heroes] or list(heroes)
for name in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "assets", "heroes", name + ".glb"))
    body = [o for o in bpy.data.objects if o.name.startswith("Body")][0]
    bpy.context.view_layer.update()
    mw = body.matrix_world
    head = mw @ Vector((0, -0.02, 1.15))
    rad = (mw.to_3x3() @ Vector((0, 0, 0.21))).length
    fwd = (mw.to_3x3() @ Vector((0, -1, 0)))
    fwd.z = 0
    fwd.normalize()
    side = fwd.cross(Vector((0, 0, 1))).normalized()
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.8, 0.85, 1.0, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    sun.data.energy = 3.4
    ld = -(fwd * 1.0 + side * 0.6 + Vector((0, 0, 1.1)))
    sun.rotation_euler = ld.to_track_quat("-Z", "Y").to_euler()
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "Medium High Contrast"
    sc.render.film_transparent = True
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = rad * 3.3
    t = head + Vector((0, 0, -rad * 0.12))
    d = (fwd + side * 0.35 + Vector((0, 0, 0.18))).normalized()
    cam.location = t + d * 30
    cam.data.clip_end = 100
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = sc.render.resolution_y = 256
    sc.render.filepath = os.path.join(ROOT, "assets", "ui", f"face_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("FACE", name)
