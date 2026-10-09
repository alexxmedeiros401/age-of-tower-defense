"""Shared low-poly toolkit for Age of Tower Defense assets.

Conventions:
- Units are Godot meters. Front of every model faces Blender -Y (becomes +Z in Godot).
- Child objects are positioned in their parent's LOCAL space.
- Animated parts hang under named Empties ("pivots") that the game rotates in code:
  LegA_* / LegB_* (opposite gait phases), Yaw (turns to face target), Arm (attack swing), Orb, Top.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector

_mats = {}


def reset(seed=1):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    random.seed(seed)


def mat(name, rgb, rough=0.6, metal=0.0, emit=None, strength=4.0):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    _mats[name] = m
    return m


def _link(o, material, parent, smooth=False):
    if material is not None:
        o.data.materials.clear()
        o.data.materials.append(material)
    if o.type == "MESH":
        for p in o.data.polygons:
            p.use_smooth = smooth
    if parent is not None:
        o.parent = parent
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    if parent is not None:
        e.parent = parent
    return e


def cyl(r, h, loc, material, parent=None, verts=8, rot=(0, 0, 0), r2=None, name=None, smooth=False):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=h, location=loc, rotation=rot)
    o = bpy.context.object
    if name:
        o.name = name
    return _link(o, material, parent, smooth)


def ico(r, loc, material, parent=None, sub=1, scale=(1, 1, 1), name=None, smooth=False):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object
    o.scale = scale
    if name:
        o.name = name
    return _link(o, material, parent, smooth)


def uvs(r, loc, material, parent=None, seg=12, rings=8, scale=(1, 1, 1), name=None, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc)
    o = bpy.context.object
    o.scale = scale
    if name:
        o.name = name
    return _link(o, material, parent, smooth)


def box(size, loc, material, parent=None, bevel=0.0, rot=(0, 0, 0), name=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        md = o.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = 1
        md.limit_method = "NONE"
    if name:
        o.name = name
    return _link(o, material, parent)


def torus(R, r, loc, material, parent=None, rot=(0, 0, 0), major=16, minor=6, name=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=major, minor_segments=minor,
                                     location=loc, rotation=rot)
    o = bpy.context.object
    if name:
        o.name = name
    return _link(o, material, parent)


def jitter(o, amt):
    for v in o.data.vertices:
        v.co += Vector((random.uniform(-amt, amt), random.uniform(-amt, amt), random.uniform(-amt, amt)))
    return o


def hierarchy(root):
    out = [root]
    for c in root.children:
        out += hierarchy(c)
    return out


def tri_count(root):
    deps = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in hierarchy(root):
        if o.type == "MESH":
            ev = o.evaluated_get(deps)
            n += sum(len(p.vertices) - 2 for p in ev.data.polygons)
    return n


def export_glb(root, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in hierarchy(root):
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True,
                              export_animations=False)
    print(f"EXPORT {os.path.basename(path)} tris={tri_count(root)}")


def stage(bg=(0.30, 0.46, 0.22)):
    """Ground, sky and sun for preview renders."""
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    _link(bpy.context.object, mat("_floor", bg, 0.9), None)
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.7, 0.82, 1.0, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), math.radians(10), math.radians(-35)))
    bpy.context.object.data.energy = 3.0
    bpy.context.object.data.angle = math.radians(8)
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "Medium High Contrast"
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    sc.camera = cam
    cam.data.type = "ORTHO"
    return cam


def shoot(cam, path, target, scale, res=512, pos_dir=(1, -1.15, 0.95), dist=20):
    t = Vector(target)
    d = Vector(pos_dir).normalized()
    cam.location = t + d * dist
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = scale
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def person(parent, loc, skin, top, bottom, hair, scale=1.0, burly=1.0, beard=None, helmet=None,
           hair_style="short", belt=None, crest=None, eye=None, sandal=None):
    """Chunky low-poly human facing -Y. Returns (body, arm) where arm is an empty at the right
    shoulder ("Arm") that the caller hangs a forearm and weapon on (+Z up, -Y forward)."""
    body = empty("Body", loc, parent)
    body.scale = (scale * burly, scale, scale)
    eye = eye or mat("Eye", (0.02, 0.02, 0.02), 0.3)
    sandal = sandal or mat("Sandal", (0.38, 0.24, 0.13), 0.8)
    for s in (-1, 1):
        cyl(0.085, 0.42, (s * 0.13, 0, 0.21), skin, body, verts=6)
        ico(0.1, (s * 0.13, -0.05, 0.03), sandal, body, sub=1, scale=(1, 1.4, 0.5))
    cyl(0.33, 0.42, (0, 0, 0.5), bottom, body, verts=8, r2=0.25)
    ico(0.27, (0, 0, 0.8), top, body, sub=2, scale=(1.0, 0.78, 1.05))
    if belt is not None:
        cyl(0.3, 0.07, (0, 0, 0.6), belt, body, verts=8)
    cyl(0.08, 0.12, (0, -0.01, 1.03), skin, body, verts=6)
    ico(0.21, (0, -0.02, 1.16), skin, body, sub=2, scale=(1, 0.95, 1.05))
    ico(0.055, (0, -0.22, 1.13), skin, body, sub=1, scale=(0.8, 1, 1))
    for s in (-1, 1):
        ico(0.03, (s * 0.08, -0.195, 1.19), eye, body, sub=1)
    if helmet is None:
        if hair_style in ("short", "long", "pony"):
            ico(0.225, (0, 0.03, 1.22), hair, body, sub=2, scale=(1.05, 1.0, 0.78))
        if hair_style == "long":
            box((0.36, 0.12, 0.42), (0, 0.13, 1.02), hair, body, bevel=0.04)
        if hair_style == "pony":
            cyl(0.07, 0.45, (0, 0.24, 1.08), hair, body, verts=6, rot=(math.radians(-25), 0, 0))
    else:
        cyl(0.235, 0.2, (0, 0.0, 1.27), helmet, body, verts=10, r2=0.2)
        ico(0.2, (0, 0.0, 1.33), helmet, body, sub=2, scale=(1.08, 1.08, 0.7))
        box((0.04, 0.09, 0.14), (0, -0.2, 1.19), helmet, body)  # nose guard
        if crest is not None:
            box((0.06, 0.42, 0.16), (0, 0.04, 1.5), crest, body, bevel=0.03)
    if beard is not None:
        ico(0.15, (0, -0.15, 1.03), beard, body, sub=1, scale=(1.1, 0.7, 1.0))
    # left arm hangs; hand position is returned for props
    cyl(0.07, 0.45, (0.34, 0, 0.76), skin, body, verts=6, rot=(0, math.radians(-10), 0))
    ico(0.08, (0.37, -0.02, 0.52), skin, body, sub=1)
    arm = empty("Arm", (-0.31, 0, 0.96), body)
    return body, arm


def stone_base(parent, top_mat, side_mat, r=1.5, h=0.32):
    """Square-ish cut-stone platform used by Bronze Age towers."""
    cyl(r + 0.05, h, (0, 0, h / 2 - 0.12), side_mat, parent, verts=8)
    cyl(r - 0.05, 0.08, (0, 0, h - 0.08), top_mat, parent, verts=8)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        box((0.05, 0.42, 0.09), (math.cos(a) * (r - 0.35), math.sin(a) * (r - 0.35), h - 0.05), side_mat, parent,
            rot=(0, 0, a))


def arc(parent, material, center, radius, thick, a0, a1, segs=8, plane="yz", verts=6):
    """Curved rod built from short cylinders (bows, sickle blades). Angle 0 points toward -Y
    (plane yz, bulging forward) or +X (plane xz); angles in degrees."""
    c = Vector(center)
    pts = []
    for i in range(segs + 1):
        a = math.radians(a0 + (a1 - a0) * i / segs)
        if plane == "yz":
            pts.append(c + Vector((0, -radius * math.cos(a), radius * math.sin(a))))
        else:
            pts.append(c + Vector((radius * math.cos(a), 0, radius * math.sin(a))))
    parts = []
    for i in range(segs):
        p0, p1 = pts[i], pts[i + 1]
        d = p1 - p0
        o = cyl(thick, d.length * 1.08, tuple((p0 + p1) / 2), material, parent, verts=verts)
        o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        parts.append(o)
    return parts
