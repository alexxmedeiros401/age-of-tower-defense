"""Stone Age tower #1: Rock Slinger. Builds, animates, renders and exports a low-poly tower."""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector

OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "/home/claude/out"
os.makedirs(OUT, exist_ok=True)
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- materials ----------
def mat(name, rgb, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m

M = {
    "grass": mat("Grass", (0.20, 0.52, 0.10)),
    "dirt": mat("Dirt", (0.42, 0.28, 0.16)),
    "wood": mat("Wood", (0.50, 0.27, 0.09)),
    "wood_dark": mat("WoodDark", (0.30, 0.17, 0.08)),
    "stone": mat("Stone", (0.52, 0.52, 0.50)),
    "stone_dark": mat("StoneDark", (0.36, 0.36, 0.35)),
    "skin": mat("Skin", (0.78, 0.45, 0.28)),
    "fur": mat("Fur", (0.72, 0.38, 0.10)),
    "fur_spot": mat("FurSpot", (0.25, 0.15, 0.07)),
    "hair": mat("Hair", (0.16, 0.09, 0.05)),
    "bone": mat("Bone", (0.93, 0.89, 0.78), 0.6),
    "leather": mat("Leather", (0.36, 0.22, 0.12)),
    "eye": mat("Eye", (0.02, 0.02, 0.02), 0.3),
}

def finish(o, material, parent=None):
    o.data.materials.append(material)
    for p in o.data.polygons:
        p.use_smooth = False
    if parent:
        o.parent = parent
    return o

def jitter(o, amt):
    for v in o.data.vertices:
        v.co += Vector((random.uniform(-amt, amt), random.uniform(-amt, amt), random.uniform(-amt, amt)))

def cyl(r, d, loc, verts=8, rot=(0, 0, 0), r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=d, location=loc, rotation=rot)
    return bpy.context.object

def ico(r, loc, sub=1, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object
    o.scale = scale
    return o

root = bpy.data.objects.new("RockSlinger", None)
scene.collection.objects.link(root)

# ---------- base ----------
g = finish(cyl(1.55, 0.25, (0, 0, 0.125), verts=7), M["grass"], root); jitter(g, 0.04); g.name = "Base_Grass"
d = finish(cyl(1.6, 0.3, (0, 0, -0.1), verts=7), M["dirt"], root); jitter(d, 0.05); d.name = "Base_Dirt"

# palisade of sharpened stakes around the back half
for i in range(11):
    a = math.radians(70 + i * 22)
    r = 1.35
    h = random.uniform(0.75, 1.05)
    s = finish(cyl(0.09, h, (r * math.cos(a), r * math.sin(a), 0.25 + h / 2), verts=6), M["wood"], root)
    s.rotation_euler = (random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), random.uniform(0, 1))
    tip = finish(cyl(0.09, 0.22, (r * math.cos(a), r * math.sin(a), 0.25 + h + 0.11), verts=6, r2=0.0), M["wood_dark"], root)
    tip.rotation_euler = s.rotation_euler
# lashing rope band
band = finish(cyl(1.37, 0.06, (0, 0, 0.62), verts=24), M["leather"], root)
bm = bmesh.new(); bm.from_mesh(band.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z) > 0.5], context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if math.degrees(math.atan2(v.co.y, v.co.x)) % 360 < 65 or math.degrees(math.atan2(v.co.y, v.co.x)) % 360 > 295], context="VERTS")
bm.to_mesh(band.data); bm.free()

# mammoth tusk arch at the front
for side in (-1, 1):
    bpy.ops.curve.primitive_bezier_curve_add()
    c = bpy.context.object
    sp = c.data.splines[0]
    p0, p1 = sp.bezier_points
    p0.co = Vector((side * 0.95, -1.15, 0.25)); p0.handle_left = p0.co + Vector((0, 0, -0.3)); p0.handle_right = p0.co + Vector((side * 0.45, -0.2, 1.1))
    p1.co = Vector((side * 0.12, -1.25, 2.05)); p1.handle_left = p1.co + Vector((side * 0.75, -0.05, 0.1)); p1.handle_right = p1.co + Vector((-side * 0.2, 0, 0.1))
    c.data.bevel_depth = 0.11
    c.data.bevel_resolution = 1
    c.data.resolution_u = 6
    c.data.use_fill_caps = True
    # taper toward the tip
    bpy.ops.curve.primitive_bezier_curve_add()
    taper = bpy.context.object
    tp = taper.data.splines[0].bezier_points
    tp[0].co = Vector((0, 1, 0)); tp[0].handle_left = Vector((-0.2, 1, 0)); tp[0].handle_right = Vector((0.3, 1, 0))
    tp[1].co = Vector((1, 0.15, 0)); tp[1].handle_left = Vector((0.7, 0.4, 0)); tp[1].handle_right = Vector((1.2, 0.1, 0))
    c.data.taper_object = taper
    bpy.context.view_layer.objects.active = c
    c.select_set(True)
    bpy.ops.object.convert(target="MESH")
    c = bpy.context.object
    c.name = f"Tusk_{'L' if side < 0 else 'R'}"
    finish(c, M["bone"], root)
    bpy.data.objects.remove(taper)

# ---------- raised log platform ----------
plat_z = 0.95
for x, y in ((-0.5, -0.45), (0.5, -0.45), (-0.5, 0.45), (0.5, 0.45)):
    finish(cyl(0.1, plat_z, (x, y, 0.25 + plat_z / 2 - 0.05), verts=6), M["wood_dark"], root)
for i in range(6):
    log = finish(cyl(0.1, 1.35, (0, -0.55 + i * 0.22, 0.25 + plat_z), verts=7, rot=(0, math.radians(90), 0)), M["wood"], root)
    log.rotation_euler.x = random.uniform(-0.3, 0.3)
    log.location.x = random.uniform(-0.05, 0.05)
# ladder
for side in (-1, 1):
    finish(cyl(0.05, 1.25, (side * 0.18, -0.95, 0.75), verts=5, rot=(math.radians(-25), 0, 0)), M["wood_dark"], root)
for k in range(4):
    z = 0.42 + k * 0.24
    finish(cyl(0.035, 0.42, (0, -1.08 + k * 0.11, z), verts=5, rot=(0, math.radians(90), 0)), M["leather"], root)

# rock ammo pile
pile = []
for i in range(9):
    r = random.uniform(0.11, 0.17)
    o = finish(ico(r, (0.45 + random.uniform(-0.18, 0.18), 0.32 + random.uniform(-0.15, 0.15), 0.25 + plat_z + 0.15 + (0.12 if i > 5 else 0)), sub=1,
                   scale=(1, random.uniform(0.8, 1.1), random.uniform(0.7, 0.9))), M["stone" if i % 3 else "stone_dark"], root)
    jitter(o, r * 0.18)
# boulders on the grass
for x, y, r in ((1.0, 0.25, 0.28), (1.15, -0.45, 0.2), (-1.05, -0.6, 0.24)):
    o = finish(ico(r, (x, y, 0.3), sub=1, scale=(1.2, 1, 0.75)), M["stone_dark"], root); jitter(o, 0.04)

# ---------- caveman ----------
deck = 0.25 + plat_z + 0.1
man = bpy.data.objects.new("Caveman", None); scene.collection.objects.link(man); man.parent = root
man.location = (-0.1, -0.05, deck)
man.scale = (1.3, 1.3, 1.3)

def part(o, material, name):
    o.name = name
    return finish(o, material, man)

for side in (-1, 1):
    part(cyl(0.085, 0.42, (side * 0.13, 0, 0.21), verts=6), M["skin"], f"Leg_{side}")
    part(ico(0.11, (side * 0.13, -0.04, 0.03), sub=1, scale=(1, 1.4, 0.55)), M["leather"], f"Foot_{side}")
torso = part(ico(0.3, (0, 0, 0.68), sub=2, scale=(1.0, 0.82, 1.08)), M["skin"], "Torso")
tunic = part(cyl(0.34, 0.5, (0, 0, 0.52), verts=7, r2=0.27), M["fur"], "Tunic")
jitter(tunic, 0.035)
for sx, sz in ((0.2, 0.55), (-0.15, 0.42), (0.05, 0.7)):
    part(ico(0.07, (sx, -0.3, sz), sub=1, scale=(1.3, 0.4, 1)), M["fur_spot"], "Spot")
strap = part(cyl(0.05, 0.85, (0, -0.02, 0.75), verts=5, rot=(0, math.radians(38), 0)), M["fur"], "Strap")
belt = part(cyl(0.355, 0.07, (0, 0, 0.33), verts=7), M["leather"], "Belt")
head = part(ico(0.22, (0, -0.03, 1.15), sub=2, scale=(1, 0.95, 1.05)), M["skin"], "Head")
part(ico(0.11, (0, -0.2, 1.24), sub=1, scale=(2.0, 0.6, 0.45)), M["skin"], "Brow")
part(ico(0.065, (0, -0.24, 1.13), sub=1, scale=(0.8, 1, 1.0)), M["skin"], "Nose")
for side in (-1, 1):
    part(ico(0.032, (side * 0.085, -0.205, 1.18), sub=1), M["eye"], f"Eye_{side}")
hair = part(ico(0.25, (0, 0.07, 1.21), sub=2, scale=(1.08, 0.98, 0.82)), M["hair"], "Hair"); jitter(hair, 0.04)
beard = part(ico(0.17, (0, -0.15, 1.0), sub=1, scale=(1.15, 0.7, 1.0)), M["hair"], "Beard"); jitter(beard, 0.03)
part(cyl(0.035, 0.14, (0.12, -0.22, 1.37), verts=4, r2=0.0, rot=(0.3, 0.5, 0)), M["bone"], "HairBone")

# left arm hangs, right arm is a pivot group so we can animate the throw
part(cyl(0.075, 0.5, (0.36, 0, 0.72), verts=6, rot=(0, math.radians(-12), 0)), M["skin"], "Arm_L")
part(ico(0.085, (0.4, -0.02, 0.45), sub=1), M["skin"], "Hand_L")
shoulder = bpy.data.objects.new("Shoulder_R", None); scene.collection.objects.link(shoulder)
shoulder.parent = man; shoulder.location = (-0.33, 0, 0.92)
arm = finish(cyl(0.075, 0.5, (0, 0, 0.25), verts=6), M["skin"], shoulder); arm.name = "Arm_R"
hand = finish(ico(0.085, (0, 0, 0.52), sub=1), M["skin"], shoulder); hand.name = "Hand_R"
sling_rock = finish(ico(0.12, (0, -0.02, 0.66), sub=1, scale=(1, 1, 0.85)), M["stone"], shoulder); jitter(sling_rock, 0.02); sling_rock.name = "Held_Rock"

# ---------- animation: idle bob + overhead throw (frames 1-24 loop) ----------
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 24
def key(obj, f, **kw):
    for attr, val in kw.items():
        setattr(obj, attr, val)
        obj.keyframe_insert(attr, frame=f)
key(shoulder, 1, rotation_euler=(math.radians(-35), 0, math.radians(-10)))
key(shoulder, 9, rotation_euler=(math.radians(-150), 0, math.radians(-15)))   # wind up behind head
key(shoulder, 13, rotation_euler=(math.radians(40), 0, math.radians(-5)))     # release
key(shoulder, 24, rotation_euler=(math.radians(-35), 0, math.radians(-10)))
key(man, 1, rotation_euler=(0, 0, 0), location=(-0.1, -0.05, deck))
key(man, 9, rotation_euler=(math.radians(-8), 0, math.radians(-12)), location=(-0.1, 0.0, deck))
key(man, 13, rotation_euler=(math.radians(10), 0, math.radians(8)), location=(-0.1, -0.1, deck - 0.03))
key(man, 24, rotation_euler=(0, 0, 0), location=(-0.1, -0.05, deck))
sling_rock.scale = (1, 1, 0.85)
for f, s in ((1, 1), (12, 1), (13, 0.001), (20, 0.001), (21, 1), (24, 1)):
    sling_rock.scale = (s, s, s * 0.85); sling_rock.keyframe_insert("scale", frame=f)
# thrown projectile flies forward
proj = finish(ico(0.12, (0, 0, 0), sub=1, scale=(1, 1, 0.85)), M["stone"], root); proj.name = "Projectile"; jitter(proj, 0.02)
for f, pos, s in ((12, (-0.4, -0.3, 2.6), 0.001), (13, (-0.4, -0.35, 2.55), 1), (17, (-0.6, -1.9, 2.4), 1), (21, (-0.8, -3.6, 1.6), 1), (22, (-0.8, -3.8, 1.5), 0.001)):
    proj.location = pos; proj.scale = (s, s, s); proj.keyframe_insert("location", frame=f); proj.keyframe_insert("scale", frame=f)
for o in (shoulder, man, sling_rock, proj):
    if o.animation_data and o.animation_data.action:
        try:
            for fc in o.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"
        except AttributeError:
            pass  # Blender 5 layered actions: default interpolation is fine

# ---------- stats ----------
mesh_objs = [o for o in scene.objects if o.type == "MESH"]
deps = bpy.context.evaluated_depsgraph_get()
tris = sum(sum(len(p.vertices) - 2 for p in o.evaluated_get(deps).data.polygons) for o in mesh_objs)
print(f"STATS meshes={len(mesh_objs)} tris={tris}")

# ---------- export GLB for Unity ----------
if "--export-only" in sys.argv:
    bpy.data.objects.remove(proj)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "rock_slinger.glb"), export_format="GLB", export_animations=True,
                              export_animation_mode="SCENE", export_apply=True)
    sys.exit(0)
if "--hero-only" not in sys.argv: bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "rock_slinger.glb"), export_format="GLB", export_animations=True, export_apply=True)

# ---------- scene, lights, camera ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.25))
floor = bpy.context.object; floor.name = "Floor"; finish(floor, mat("Floor", (0.30, 0.45, 0.20)))
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.72, 0.84, 1.0, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), math.radians(10), math.radians(-35)))
sun = bpy.context.object; sun.data.energy = 3.2; sun.data.angle = math.radians(8)

bpy.ops.object.camera_add()
cam = bpy.context.object; scene.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 4.6
def aim(cam, pos, target=(0, -0.3, 0.95)):
    cam.location = pos
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()

engines = [e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items]
scene.render.engine = "CYCLES" if "CYCLES" in engines else "BLENDER_EEVEE"
if scene.render.engine == "CYCLES":
    scene.cycles.device = "CPU"; scene.cycles.samples = 24; scene.render.threads_mode = "FIXED"; scene.render.threads = 2; scene.cycles.use_denoising = True
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.render.film_transparent = False
print("ENGINE", scene.render.engine)

def render(path, res, frame):
    scene.frame_set(frame)
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

aim(cam, (6.5, -7.5, 6.2), target=(0, -0.3, 1.35)); cam.data.ortho_scale = 5.5
render(os.path.join(OUT, "hero.png"), (1000, 1000), 1)
if "--hero-only" in sys.argv:
    sys.exit(0)
cam.data.ortho_scale = 4.6
aim(cam, (-7.0, -6.0, 6.5))
render(os.path.join(OUT, "angle2.png"), (640, 640), 9)
# top-down-ish gameplay camera, the angle players actually see on a 2D map
aim(cam, (0.01, -3.0, 10.0), target=(0, -0.2, 0.5)); cam.data.ortho_scale = 5.0
render(os.path.join(OUT, "gameplay_view.png"), (640, 640), 1)

# throw animation frames for a GIF
aim(cam, (6.5, -7.5, 6.2)); cam.data.ortho_scale = 5.6
if scene.render.engine == "CYCLES":
    scene.cycles.samples = 8
os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)
for f in range(1, 25, 2):
    render(os.path.join(OUT, "frames", f"f{f:02d}.png"), (360, 360), f)
print("DONE")
