"""Renders a portrait (assets/ui/icon_<robot>.png) for every robot GLB, framed on its bounding box.
Run: python3 tools/blender/robot_icons.py [robot ...]"""
import sys, os, math, json, bpy
from mathutils import Vector
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
robots = json.load(open(os.path.join(ROOT, "data", "enemies.json")))
names = [a for a in sys.argv[1:] if a in robots] or list(robots)
for name in names:
    path = os.path.join(ROOT, "assets", "robots", name + ".glb")
    if not os.path.exists(path):
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=path)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import icon_fix; icon_fix.srgb_vertex_colors()
    bpy.context.view_layer.update()
    lo = Vector((1e9, 1e9, 1e9)); hi = Vector((-1e9, -1e9, -1e9))
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
            hi = Vector((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    ctr = (lo + hi) / 2
    size = max((hi - lo).length, 0.5)
    wd = bpy.data.worlds.new("W"); sc.world = wd; wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.82, 1.0, 1)
    wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(45), math.radians(10), math.radians(-35)))
    bpy.context.object.data.energy = 3.2
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "Medium High Contrast"
    sc.render.film_transparent = True
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = size * 0.85
    d = Vector((0.7, -1.2, 0.6)).normalized()
    cam.location = ctr + d * 40
    cam.data.clip_end = 200
    cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = sc.render.resolution_y = 256
    sc.render.filepath = os.path.join(ROOT, "assets", "ui", "icon_%s.png" % name)
    bpy.ops.render.render(write_still=True)
    print("ICON", name)
