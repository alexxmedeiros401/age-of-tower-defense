"""Renders transparent shop-card portraits for each tower GLB. Run: python3 icons.py --src DIR --out DIR"""
import sys, os, math, bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[sys.argv.index("--src") + 1]
OUT = sys.argv[sys.argv.index("--out") + 1]
os.makedirs(OUT, exist_ok=True)
NAMES = sys.argv[sys.argv.index("--names") + 1].split(",") if "--names" in sys.argv else ["rock_slinger", "club_warrior", "boulder_catapult", "tar_shaman"]
for name in NAMES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, name + ".glb"))
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.82, 1.0, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(45), math.radians(10), math.radians(-35)))
    bpy.context.object.data.energy = 3.2
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "Medium High Contrast"
    sc.render.film_transparent = True
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
    ZOOM = float(sys.argv[sys.argv.index("--zoom") + 1]) if "--zoom" in sys.argv else 4.5
    TZ = float(sys.argv[sys.argv.index("--tz") + 1]) if "--tz" in sys.argv else 1.35
    cam.data.type = "ORTHO"; cam.data.ortho_scale = ZOOM
    t = Vector((0, -0.1, TZ)); d = Vector((0.7, -1.2, 0.75)).normalized()
    cam.location = t + d * 20
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = sc.render.resolution_y = 256
    sc.render.filepath = os.path.join(OUT, f"icon_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("ICON", name)
