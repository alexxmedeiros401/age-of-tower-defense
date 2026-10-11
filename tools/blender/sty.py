"""Stylized model pipeline ("option 3"), shared by every v2 asset script.

What every model gets:
- soft bevels with hardened normals (chunky, toy-like edges)
- per-part color variation and optional per-vertex color gradients
- ambient occlusion baked into vertex colors (glTF COLOR_0), so the shading costs nothing at
  runtime and survives Godot's GL Compatibility renderer
- static parts merged into one mesh per rig node (towers ~10 meshes instead of ~80)
- an inverted-hull outline shell per mesh: a slightly grown, decimated, inside-out copy with an
  unlit darkened color. It draws a cartoon silhouette line on any renderer, no shaders needed.

Conventions (same as lp.py): Godot meters, the model's front faces Blender -Y, animated parts hang
under named Empties that game.gd rotates in code (Yaw, Arm, Orb, Body, LegA_*, LegB_*).

Usage in a model script:
    import sty; from sty import P
    sty.reset(seed)
    root = sty.empty("RockSlinger")
    sty.reg(sty.cyl(...), P["wood"], parent=root, bevel=0.02)
    ...
    sty.finish(out_path, outline=0.06)
"""
import bpy, bmesh, math, random, sys, os, colorsys
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree

scene = None
PARTS = []          # (object, color fn)
MAT = {}
AO_K = [1.0]        # ambient-occlusion factor for parts registered now (characters use a softer one)
POST = [None]       # optional theme filter: fn(color, world_pos, world_normal, obj) -> color (snow caps, scorching)


class soft_ao:
    """with sty.soft_ao(): ... -> parts built inside get gentler, shorter-range AO (skin stays clean)."""
    def __init__(self, k=0.45):
        self.k = k
    def __enter__(self):
        AO_K.append(self.k)
    def __exit__(self, *a):
        AO_K.pop()

# ---------- shared palette (linear RGB) ----------
P = dict(
    # nature
    grass=(0.20, 0.48, 0.09), grass_hi=(0.44, 0.64, 0.12), grass_dark=(0.09, 0.26, 0.05),
    dirt=(0.40, 0.25, 0.13), dirt_dark=(0.17, 0.10, 0.05),
    wood=(0.48, 0.26, 0.10), wood_dark=(0.27, 0.14, 0.06), wood_cut=(0.86, 0.62, 0.34),
    rope=(0.64, 0.49, 0.26), wicker=(0.70, 0.52, 0.24),
    stone=(0.52, 0.51, 0.48), stone_dark=(0.33, 0.32, 0.31), stone_light=(0.70, 0.69, 0.66),
    moss=(0.28, 0.42, 0.10), pine=(0.07, 0.30, 0.10), pine_hi=(0.16, 0.46, 0.14),
    # people
    skin=(0.80, 0.46, 0.29), nose=(0.86, 0.42, 0.27), skin_tan=(0.62, 0.34, 0.19),
    fur=(0.76, 0.41, 0.12), fur_hi=(0.95, 0.62, 0.25), fur_dark=(0.30, 0.17, 0.07),
    fur_grey=(0.55, 0.52, 0.48), fur_white=(0.88, 0.86, 0.80),
    hair=(0.13, 0.075, 0.04), hair_red=(0.45, 0.13, 0.04),
    bone=(0.94, 0.89, 0.74), bone_old=(0.52, 0.42, 0.28), leather=(0.38, 0.22, 0.11),
    hide=(0.74, 0.55, 0.33), ochre=(0.62, 0.10, 0.04), paint_blue=(0.10, 0.25, 0.65),
    eye=(0.02, 0.02, 0.02), white=(0.95, 0.95, 0.92), mouth=(0.22, 0.04, 0.03),
    tar=(0.025, 0.025, 0.03), spirit=(0.3, 1.0, 0.45),
    flame=(1.0, 0.62, 0.10), flame_tip=(0.85, 0.12, 0.02),
    # robots: cold gunmetal and white plating, cyan/red energy
    plate=(0.78, 0.80, 0.84), plate_dark=(0.30, 0.33, 0.38), gunmetal=(0.12, 0.13, 0.16),
    steel=(0.50, 0.53, 0.58), joint=(0.06, 0.06, 0.08), hazard=(0.95, 0.55, 0.05),
    cyan=(0.25, 0.95, 1.0), red_glow=(1.0, 0.12, 0.08), magenta=(0.95, 0.15, 0.85),
)


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def mul(c, k):
    return tuple(x * k for x in c)


def vary(c, v):
    h, s, val = colorsys.rgb_to_hsv(*c)
    h = (h + random.uniform(-v, v) * 0.12) % 1.0
    val *= random.uniform(1 - v, 1 + v)
    s = min(1.0, s * random.uniform(1 - v * 0.5, 1 + v * 0.5))
    return colorsys.hsv_to_rgb(h, s, val)


# ---------- materials: color lives in vertex colors ("Col"), materials only set the finish ----------
def _make_mat(name, rough, metal=0.0, emit=None, emit_e=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    nt.links.new(vc.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_e
    return m


def _make_unlit(name):
    """Unlit vertex-color material (exports as KHR_materials_unlit, Godot: unshaded)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bg = nt.nodes.new("ShaderNodeBackground")
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    nt.links.new(vc.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    m.use_backface_culling = True
    return m


def reset(seed=1):
    global scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    PARTS.clear()
    MAT.clear()
    random.seed(seed)
    MAT.update(
        # "Grass" keeps its own name: game.gd _retheme_base() swaps it on non-grass maps
        grass=_make_mat("Grass", 0.9), matte=_make_mat("Matte", 0.85), satin=_make_mat("Satin", 0.5),
        gloss=_make_mat("Gloss", 0.2), metal=_make_mat("Metal", 0.38, 0.35),
        flame=_make_mat("Flame", 0.6, emit=(1.0, 0.38, 0.04), emit_e=0.8),
        glow_cyan=_make_mat("GlowCyan", 0.4, emit=(0.25, 0.95, 1.0), emit_e=1.1),
        glow_red=_make_mat("GlowRed", 0.4, emit=(1.0, 0.1, 0.05), emit_e=0.9),
        glow_green=_make_mat("GlowGreen", 0.4, emit=(0.3, 1.0, 0.45), emit_e=0.7),
        glow_orange=_make_mat("GlowOrange", 0.4, emit=(1.0, 0.5, 0.08), emit_e=0.9),
        outline=_make_unlit("Outline"),
    )


def empty(name, loc=(0, 0, 0), parent=None, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    scene.collection.objects.link(e)
    e.parent = parent
    e.location = loc
    e.rotation_euler = rot
    return e


def reg(o, col, matk="matte", parent=None, bevel=None, smooth=True, var=0.06, name=None, colfn=None,
        noao=False, noocc=False, keep=False, no_outline=False, segments=1, nopost=False):
    """Register a part: material, parent, optional bevel, base color (or per-vertex color fn).
    keep=True: never merged (for meshes animated on their own, e.g. a held rock)."""
    if name:
        o.name = name
    if tuple(o.scale) != (1, 1, 1):          # bake scale so bevels stay uniform
        s = o.scale.copy()
        for v in o.data.vertices:
            v.co = Vector((v.co.x * s.x, v.co.y * s.y, v.co.z * s.z))
        o.scale = (1, 1, 1)
        if s.x * s.y * s.z < 0:              # a mirrored part: keep its faces pointing outwards
            o.data.flip_normals()
    o.data.materials.clear()
    o.data.materials.append(MAT[matk])
    o.parent = parent
    for p in o.data.polygons:
        p.use_smooth = smooth
    if bevel:
        m = o.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = segments
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(40)
        m.harden_normals = True
    o["ao_k"] = AO_K[-1]
    for flag, on in (("noao", noao), ("noocc", noocc), ("keep", keep), ("no_outline", no_outline), ("nopost", nopost)):
        if on:
            o[flag] = 1
    c = vary(col, var) if var else col
    PARTS.append((o, colfn if colfn else (lambda p, n, c=c: c)))
    return o


# ---------- primitives (world/parent-local coords; parent via reg) ----------
def cyl(r, d, loc, verts=8, rot=(0, 0, 0), r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=d, location=loc, rotation=rot)
    return bpy.context.object


def ico(r, loc, sub=2, scale=(1, 1, 1), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = scale
    return o


def uvs(r, loc, seg=12, rings=8, scale=(1, 1, 1), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = scale
    return o


def torus(R, r, loc, rot=(0, 0, 0), maj=10, mi=4):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=maj, minor_segments=mi,
                                     location=loc, rotation=rot)
    return bpy.context.object


def box(size, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    return o


def rod(a, b, r, verts=6, r2=None):
    """Cylinder (or cone, r2 at b) from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = cyl(r, d.length, (a + b) / 2, verts=verts, r2=r2)
    o.rotation_euler = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return o


def point_at(o, direction):
    o.rotation_euler = Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized()).to_euler()
    return o


def jitter(o, amt, top_only=False):
    for v in o.data.vertices:
        if top_only and v.co.z <= 0:
            continue
        v.co += Vector((random.uniform(-amt, amt), random.uniform(-amt, amt), random.uniform(-amt, amt)))
    return o


def mesh_from(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    return o


# ---------- common sub-assemblies ----------
def grass_base(root, r=1.56, tufts=10, cobbles=18, seed_rim=True):
    """Earth chunk with a grass cap, a cobble rim and grass tufts (the Stone Age tower footprint)."""
    pl = cyl(r - 0.18, 0.40, (0, 0, -0.08), verts=12, r2=r + 0.06)
    jitter(pl, 0.03)
    reg(pl, P["dirt"], parent=root, bevel=0.03, var=0, name="Base_Earth",
        colfn=lambda p, n: lerp(P["dirt_dark"], P["dirt"], (p.z + 0.28) / 0.38))
    cap = cyl(r, 0.10, (0, 0, 0.16), verts=12)
    jitter(cap, 0.012)
    reg(cap, P["grass"], matk="grass", parent=root, bevel=0.04, var=0, name="Base_Grass",
        colfn=lambda p, n: lerp(P["grass"], P["grass_hi"], 0.5 + 0.9 * noise.noise(p * 1.6)))
    for i in range(cobbles):
        a = math.radians(i * 360 / cobbles + random.uniform(-6, 6))
        cr = random.uniform(0.12, 0.17)
        c = ico(cr, ((r - 0.06) * math.cos(a), (r - 0.06) * math.sin(a), 0.2), sub=1, scale=(1.25, 1.0, 0.62), rot=(0, 0, a))
        jitter(c, cr * 0.15)
        reg(c, P["stone"] if i % 3 else P["stone_dark"], parent=root, smooth=False, var=0.12, name="Cobble")
    for _ in range(tufts * 3):
        if tufts <= 0:
            break
        a = random.uniform(0, math.tau)
        rr = random.uniform(0.75, r - 0.2)
        x, y = rr * math.cos(a), rr * math.sin(a)
        if abs(x) < 0.7 and abs(y) < 0.7:
            continue
        tuft(root, x, y, random.uniform(0.8, 1.2))
        tufts -= 1


def tuft(root, x, y, s=1.0, z=0.2):
    for k in range(3):
        ang = random.uniform(0, math.tau)
        lean = random.uniform(0.15, 0.45)
        h = random.uniform(0.16, 0.26) * s
        b = cyl(0.035 * s, h, (x + 0.03 * math.cos(ang), y + 0.03 * math.sin(ang), z + h / 2), verts=4, r2=0.0)
        b.rotation_euler = (lean * math.cos(ang + 1.57), lean * math.sin(ang + 1.57), ang)
        base = vary(P["grass"], 0.1)
        reg(b, P["grass"], matk="grass", parent=root, var=0, name="Tuft", noocc=True, no_outline=True,
            colfn=lambda p, n, base=base, z=z: lerp(base, P["grass_hi"], (p.z - z) / 0.22))


def caveman_head(parent, c, hair=None, beard=True, beard_col=None, angry=True, scale=1.0, skin=None):
    """A readable stylized head centred at c (parent-local). Faces -Y."""
    hair = hair or P["hair"]
    skin = skin or P["skin"]
    beard_col = beard_col or hair
    s = scale
    cx, cy, cz = c
    reg(ico(0.27 * s, (cx, cy, cz), sub=3, scale=(1, 0.95, 1.0)), skin, parent=parent, var=0.03, name="Head")
    for side in (-1, 1):
        reg(ico(0.07 * s, (cx + side * 0.265 * s, cy + 0.02 * s, cz), scale=(0.5, 0.8, 1.0)), skin, parent=parent, var=0.03, name="Ear")
    reg(ico(0.13 * s, (cx, cy - 0.185 * s, cz + 0.09 * s), scale=(1.9, 0.6, 0.45)), skin, parent=parent, var=0.03, name="Brow")
    reg(ico(0.075 * s, (cx, cy - 0.255 * s, cz - 0.03 * s), scale=(0.95, 1.0, 0.85)), P["nose"], parent=parent, var=0.03, name="Nose")
    for side in (-1, 1):
        reg(ico(0.047 * s, (cx + side * 0.092 * s, cy - 0.212 * s, cz + 0.03 * s), scale=(1.0, 0.5, 1.2)), P["white"],
            matk="gloss", parent=parent, var=0, name="Eye")
        reg(ico(0.027 * s, (cx + side * 0.088 * s, cy - 0.238 * s, cz + 0.025 * s)), P["eye"], matk="gloss", parent=parent, var=0, name="Pupil")
        tilt = -side * 0.32 if angry else side * 0.15
        reg(box((0.12 * s, 0.035 * s, 0.034 * s), (cx + side * 0.095 * s, cy - 0.242 * s, cz + 0.105 * s), rot=(0, tilt, 0)),
            hair, parent=parent, bevel=0.01 * s, var=0.04, name="Eyebrow")
    if beard:
        b = reg(ico(0.2 * s, (cx, cy - 0.12 * s, cz - 0.15 * s), scale=(1.15, 0.75, 0.95)), beard_col, parent=parent, var=0.04, name="Beard")
        jitter(b, 0.02 * s)
        for x, y, z, r in ((-0.11, -0.17, -0.28, 0.08), (0.11, -0.17, -0.28, 0.08), (0, -0.19, -0.32, 0.085),
                           (-0.18, -0.09, -0.23, 0.07), (0.18, -0.09, -0.23, 0.07)):
            t = reg(ico(r * s, (cx + x * s, cy + y * s, cz + z * s), sub=1, scale=(1, 0.9, 1.25)), beard_col, parent=parent, var=0.04, name="BeardTuft")
            jitter(t, 0.012 * s)
        reg(ico(0.042 * s, (cx, cy - 0.248 * s, cz - 0.105 * s), scale=(1.7, 0.45, 0.65)), P["mouth"], parent=parent, var=0, name="Mouth")
        reg(box((0.085 * s, 0.02 * s, 0.024 * s), (cx, cy - 0.263 * s, cz - 0.102 * s)), P["white"], parent=parent, var=0, bevel=0.005 * s, name="Teeth")
    else:
        reg(ico(0.04 * s, (cx, cy - 0.252 * s, cz - 0.12 * s), scale=(1.5, 0.45, 0.5)), P["mouth"], parent=parent, var=0, name="Mouth")
    h = reg(ico(0.285 * s, (cx, cy + 0.08 * s, cz + 0.09 * s), scale=(1.07, 1.0, 0.8)), hair, parent=parent, var=0.04, name="Hair")
    jitter(h, 0.03 * s)


# ---------- bake: apply modifiers, AO + color into vertex colors ----------
def bake(ao_dist=0.5, ao_strength=0.82, outline_w=0.06, ground=None, rays=20, ray_offset=0.006, ao_floor=0.0):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    for o, _ in PARTS:
        if o.modifiers:
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            o.modifiers.clear()
            o.data = me
    bpy.context.view_layer.update()
    verts, polys = [], []
    for o, _ in PARTS:
        if o.get("noocc") or o.get("keep"):
            continue
        mw = o.matrix_world
        base = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    if ground is not None:        # a big ground plane at z = ground: contact shadows under every prop
        base = len(verts)
        verts += [Vector((-80, -80, ground)), Vector((80, -80, ground)), Vector((80, 80, ground)), Vector((-80, 80, ground))]
        polys.append([base, base + 1, base + 2, base + 3])
    bvh = BVHTree.FromPolygons(verts, polys) if polys else None
    N = rays
    dirs = []
    for i in range(N):
        z = 1 - (i + 0.5) / N
        r = math.sqrt(max(0.0, 1 - z * z))
        phi = i * 2.399963
        dirs.append(Vector((r * math.cos(phi), r * math.sin(phi), z)))
    wsum = sum(d.z for d in dirs)
    up = Vector((0, 0, 1))
    for o, fn in PARTS:
        me = o.data
        mw = o.matrix_world
        nm = mw.to_3x3().inverted().transposed()
        attr = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        for v in me.vertices:
            p = mw @ v.co
            n = (nm @ v.normal).normalized()
            ao = 1.0
            if bvh and not o.get("noao"):
                q = up.rotation_difference(n)
                occ = 0.0
                k = float(o.get("ao_k", 1.0))
                dist = ao_dist * (0.5 if k < 1.0 else 1.0)
                for d in dirs:
                    if bvh.ray_cast(p + n * ray_offset, q @ d, dist)[0] is not None:
                        occ += d.z
                ao = max(ao_floor, 1.0 - ao_strength * k * occ / wsum)
            sky = 0.94 + 0.12 * max(0.0, n.z)
            c = fn(p, n)
            if POST[0] is not None and not o.get("nopost"):
                c = POST[0](c, p, n, o)
            attr.data[v.index].color = (c[0] * ao * sky, c[1] * ao * sky, c[2] * ao * sky, 1.0)
        me.color_attributes.active_color = attr
        # parts thinner than a few outline widths get no outline shell (ropes, pupils, teeth...)
        dims = [max(v.co[i] for v in me.vertices) - min(v.co[i] for v in me.vertices) for i in range(3)] if len(me.vertices) else [0, 0, 0]
        dims = [d * s for d, s in zip(dims, o.matrix_world.to_scale())]
        nol = 1 if (o.get("no_outline") or sorted(dims)[1] < 2.6 * outline_w) else 0
        fa = me.attributes.new("nol", "INT", "FACE")
        for d in fa.data:
            d.value = nol


def merge(names=None):
    """Join registered parts that share a parent into one mesh (except keep=True parts)."""
    names = names or {}
    groups = {}
    for o, _ in PARTS:
        if o.get("keep"):
            continue
        groups.setdefault(o.parent.name if o.parent else "", []).append(o)
    merged = []
    for pname, objs in groups.items():
        if len(objs) > 1:
            bpy.ops.object.select_all(action="DESELECT")
            for o in objs:
                o.select_set(True)
            bpy.context.view_layer.objects.active = objs[0]
            bpy.ops.object.join()
        objs[0].name = names.get(pname, (pname or "Root") + "_Mesh")
        merged.append(objs[0])
    return merged


def outline(width=0.06, ratio=0.5, darkness=0.16, skip_mats=("Flame", "Grass")):
    """Inverted-hull outline shell for every mesh. Parts using skip_mats get no shell."""
    for o in [ob for ob in scene.objects if ob.type == "MESH"]:
        if o.name.endswith("_Outline"):
            continue
        me = o.data.copy()
        bm = bmesh.new()
        bm.from_mesh(me)
        skip_idx = {i for i, m in enumerate(me.materials) if m and m.name in skip_mats}
        nl = bm.faces.layers.int.get("nol")
        drop = [f for f in bm.faces if f.material_index in skip_idx or (nl is not None and f[nl] == 1)]
        if drop:
            bmesh.ops.delete(bm, geom=drop, context="FACES")
        if not bm.faces:
            bm.free()
            continue
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.003)
        bm.to_mesh(me)
        bm.free()
        hull = bpy.data.objects.new(o.name + "_Outline", me)
        scene.collection.objects.link(hull)
        hull.parent = o.parent
        hull.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        # copy the whole transform: imported (glTF) objects rotate by quaternion, not euler
        hull.rotation_mode = o.rotation_mode
        hull.location, hull.scale = o.location.copy(), o.scale.copy()
        hull.rotation_euler = o.rotation_euler.copy()
        hull.rotation_quaternion = o.rotation_quaternion.copy()
        # simplify first, THEN inflate, so the shell never dips back inside the surface
        if ratio < 1.0 and len(me.polygons) > 60:
            dm = hull.modifiers.new("Dec", "DECIMATE")
            dm.ratio = ratio
            dm.use_collapse_triangulate = True
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            nme = bpy.data.meshes.new_from_object(hull.evaluated_get(dg))
            hull.modifiers.clear()
            hull.data = nme
            me = nme
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.normal_update()
        sc = hull.matrix_world.to_scale()
        k = width / max(1e-6, (sc.x + sc.y + sc.z) / 3)
        for v in bm.verts:
            v.co += v.normal * k
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.materials.clear()
        me.materials.append(MAT["outline"])
        for p in me.polygons:
            p.use_smooth = True
            p.material_index = 0
        ca = me.color_attributes.get("Col")
        if ca:
            for d in ca.data:
                c = d.color
                d.color = (c[0] * darkness, c[1] * darkness, c[2] * darkness, 1.0)


def stats(tag=""):
    meshes = [o for o in scene.objects if o.type == "MESH"]
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    otris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes if o.name.endswith("_Outline"))
    print(f"STATS {tag} meshes={len(meshes)} tris={tris} (outline {otris})")
    return tris


def merge_outlines():
    """Join per-part outline shells that share a parent into one mesh per parent."""
    groups = {}
    for o in [x for x in scene.objects if x.type == "MESH" and x.name.endswith("_Outline")]:
        groups.setdefault(o.parent.name if o.parent else "", []).append(o)
    for pname, objs in groups.items():
        if len(objs) > 1:
            bpy.ops.object.select_all(action="DESELECT")
            for o in objs:
                o.select_set(True)
            bpy.context.view_layer.objects.active = objs[0]
            bpy.ops.object.join()
        objs[0].name = "M_" + (pname or "Root") + "_Outline"


def finish(out_glb, outline_w=0.06, outline_ratio=0.5, names=None, export=True, ao_dist=0.5, ray_offset=0.006, ao_floor=0.0,
           per_part_outline=False):
    bake(ao_dist=ao_dist, outline_w=outline_w or 0.06, ray_offset=ray_offset, ao_floor=ao_floor)
    if per_part_outline and outline_w:
        # shells are made (and simplified) part by part, so simplification can never bridge two parts
        outline(outline_w, outline_ratio)
        merge(names)
        merge_outlines()
    else:
        merge(names)
        if outline_w:
            outline(outline_w, outline_ratio)
    stats(os.path.basename(out_glb))
    if export:
        os.makedirs(os.path.dirname(out_glb) or ".", exist_ok=True)
        bpy.ops.export_scene.gltf(filepath=out_glb, export_format="GLB", export_animations=False, export_apply=True)


# ---------- preview renders (same studio setup as stone_slinger.py) ----------
def studio(floor=True):
    def plain(name, rgb):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
        return m
    if floor:
        bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.25))
        bpy.context.object.data.materials.append(plain("Floor", (0.30, 0.45, 0.20)))
    w = bpy.data.worlds.new("W")
    scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.72, 0.84, 1.0, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), math.radians(10), math.radians(-35)))
    bpy.context.object.data.energy = 3.2
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    scene.camera = cam
    cam.data.type = "ORTHO"
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    return cam


def shoot(cam, path, pos=(6.5, -7.5, 6.2), target=(0, -0.3, 1.2), ortho=5.5, res=(700, 700), frame=1):
    cam.location = pos
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = ortho
    scene.frame_set(frame)
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
