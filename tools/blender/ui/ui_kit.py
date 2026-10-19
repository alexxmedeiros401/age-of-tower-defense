"""Shared setup for rendered UI art (menu medallions, plaques, 3D icons, scrap): Cycles on a transparent film, a studio
HDRI for reflections plus a warm key and a cool rim light, an orthographic or perspective camera, and a few
materials (polished gold, glossy enamel, painted and bare metal). post() adds the cartoon outline and drop shadow
the game's icons share.
"""
import math, os
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, Euler

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
UI = os.path.join(ROOT, "assets", "ui")


def lin(c):
    out = []
    for x in c[:3]:
        out.append(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92)
    return (out[0], out[1], out[2], 1.0)


def reset(res=512, samples=48, hdri="studio.exr", hdri_strength=1.0, hdri_rot=0.0, w=None, h=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.glossy_bounces = 4
    sc.cycles.transparent_max_bounces = 4
    sc.render.film_transparent = True
    sc.render.resolution_x = w or res
    sc.render.resolution_y = h or res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    wd = bpy.data.worlds.new("UIWorld")
    sc.world = wd
    wd.use_nodes = True
    nt = wd.node_tree
    bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    path = os.path.join(bpy.utils.system_resource("DATAFILES"), "studiolights", "world", hdri)
    env.image = bpy.data.images.load(path, check_existing=True)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, hdri_rot)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = hdri_strength
    return sc


def camera(loc, target, ortho=None, lens=85.0):
    cd = bpy.data.cameras.new("Cam")
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.clip_start = 0.01
    cd.clip_end = 100
    cam = bpy.data.objects.new("Cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def light(kind, loc, target=(0, 0, 0), energy=3.0, color=(1, 1, 1), size=1.0, spot=None):
    ld = bpy.data.lights.new("L", kind)
    ld.energy = energy
    ld.color = color
    if kind == "AREA":
        ld.size = size
    elif kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = size
    elif kind == "SUN":
        ld.angle = size
    if spot:
        ld.spot_size = spot
    ob = bpy.data.objects.new("L", ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def studio(key=4.0, rim=3.0, fill=0.6, scale=1.0, key_col=(1.0, 0.95, 0.86), rim_col=(0.75, 0.88, 1.0)):
    """Key light from the top left (the light direction of every icon), a cool rim from behind, a soft fill."""
    s = scale
    light("SUN", (-2 * s, -3 * s, 4 * s), (0, 0, 0), energy=key, color=key_col, size=math.radians(6))
    light("AREA", (2.5 * s, 3.0 * s, 2.0 * s), (0, 0, 0.3 * s), energy=rim * 40 * s * s, color=rim_col, size=1.5 * s)
    light("AREA", (3.0 * s, -2.5 * s, 0.6 * s), (0, 0, 0.3 * s), energy=fill * 40 * s * s, color=(1, 1, 1), size=3.0 * s)


# --------------------------------------------------------------------------------------------- materials
def _mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
    return m, m.node_tree.nodes["Principled BSDF"], m.node_tree


def gold(name="UIGold", col=(1.0, 0.74, 0.3), rough=0.2):
    m, b, nt = _mat(name)
    b.inputs["Base Color"].default_value = lin(col)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    return m


def metal(name, col, rough=0.3, metallic=1.0, noise=0.0, noise_scale=40.0):
    m, b, nt = _mat(name)
    b.inputs["Base Color"].default_value = lin(col)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if noise > 0:
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise_scale
        n.inputs["Detail"].default_value = 6
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = rough - noise
        mr.inputs["To Max"].default_value = rough + noise
        nt.links.new(n.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    return m


def paint(name, col, rough=0.35, coat=0.0):
    m, b, nt = _mat(name)
    b.inputs["Base Color"].default_value = lin(col)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = rough
    if coat > 0:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.05
    return m


def emit(name, col, strength=4.0):
    m, b, nt = _mat(name)
    b.inputs["Base Color"].default_value = lin(col)
    b.inputs["Emission Color"].default_value = lin(col)
    b.inputs["Emission Strength"].default_value = strength
    return m


def gem(name, col, rough=0.03):
    """Glassy jewel: coloured, mostly reflective, a little transmission."""
    m, b, nt = _mat(name)
    b.inputs["Base Color"].default_value = lin(col)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.02
    b.inputs["Transmission Weight"].default_value = 0.35
    b.inputs["IOR"].default_value = 1.6
    return m


def matte(name, col):
    m, b, nt = _mat(name)
    b.inputs["Base Color"].default_value = lin(col)
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Specular IOR Level"].default_value = 0.1
    return m


# --------------------------------------------------------------------------------------------- geometry
def link(me, name, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), smooth=True):
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(loc)
    ob.rotation_euler = Euler(rot)
    ob.scale = Vector(scale)
    if mat is not None:
        me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def bevel(ob, width=0.02, segments=3, angle=30, harden=True):
    m = ob.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = harden
    m.miter_outer = "MITER_ARC"
    if harden:
        ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
    return m


def subsurf(ob, levels=2):
    m = ob.modifiers.new("Sub", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    return m


def revolve(name, profile, segments=128, mat=None, loc=(0, 0, 0)):
    """Surface of revolution about Z from a profile [(r, z), ...] (open polyline, bottom to top)."""
    bm = bmesh.new()
    rings = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for r, z in profile])
    for i in range(segments):
        r0, r1 = rings[i], rings[(i + 1) % segments]
        for j in range(len(profile) - 1):
            bm.faces.new((r0[j], r1[j], r1[j + 1], r0[j + 1]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(me, name, mat, loc)


def prism(name, pts2d, z0, z1, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), holes=()):
    """Extruded polygon (convex or not), optional round holes [(cx, cy, r, n)] cut by boolean."""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts2d]
    top = [bm.verts.new((x, y, z1)) for x, y in pts2d]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    n = len(pts2d)
    for i in range(n):
        bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(me, name, mat, loc, rot, smooth=False)
    for (cx, cy, r, nseg) in holes:
        cut = cylinder(name + "_cut", r, (z1 - z0) * 3, nseg, loc=(cx, cy, (z0 + z1) / 2))
        cut.parent = ob                      # the cutter moves with the object it cuts
        b = ob.modifiers.new("Hole", "BOOLEAN")
        b.operation = "DIFFERENCE"
        b.object = cut
        b.solver = "EXACT"
        cut.hide_render = True
        cut.hide_viewport = True
    return ob


def cylinder(name, r, h, n=48, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), r_top=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r, radius2=r if r_top is None else r_top, depth=h)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(me, name, mat, loc, rot, smooth=False)


def sphere(name, r, mat=None, loc=(0, 0, 0), scale=(1, 1, 1), seg=48, rings=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(me, name, mat, loc, scale=scale)


def torus(name, R, r, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), seg=96, mseg=24):
    bm = bmesh.new()
    vs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(mseg):
            b = 2 * math.pi * j / mseg
            rr = R + r * math.cos(b)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), r * math.sin(b))))
        vs.append(ring)
    for i in range(seg):
        for j in range(mseg):
            bm.faces.new((vs[i][j], vs[(i + 1) % seg][j], vs[(i + 1) % seg][(j + 1) % mseg], vs[i][(j + 1) % mseg]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(me, name, mat, loc, rot)


def curve_tube(name, pts, radius, mat=None, res=12, closed=False):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = radius
    cd.bevel_resolution = res // 2
    cd.use_fill_caps = True
    sp = cd.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    sp.use_cyclic_u = closed
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    if mat is not None:
        cd.materials.append(mat)
    return ob


def text3d(name, body, size=1.0, extrude=0.08, bevel_depth=0.02, mat=None, font=None, loc=(0, 0, 0), rot=(0, 0, 0),
           align="CENTER"):
    cd = bpy.data.curves.new(name, "FONT")
    cd.body = body
    cd.size = size
    cd.extrude = extrude
    cd.bevel_depth = bevel_depth
    cd.bevel_resolution = 3
    cd.align_x = align
    cd.align_y = "CENTER"
    if font:
        cd.font = bpy.data.fonts.load(font, check_existing=True)
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(loc)
    ob.rotation_euler = Euler(rot)
    if mat is not None:
        cd.materials.append(mat)
    return ob


# --------------------------------------------------------------------------------------------- output
def render(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def post(src, dst, size=None, outline=0.0, outline_col=(10, 12, 24), shadow=0.0, shadow_off=(0.0, 0.03),
         shadow_alpha=0.45, pad=0.0):
    """Cartoon outline (alpha dilated by `outline` x width) and a soft drop shadow, then resize to `size`."""
    from PIL import Image, ImageFilter
    im = Image.open(src).convert("RGBA")
    W, H = im.size
    if pad > 0:
        p = int(W * pad)
        big = Image.new("RGBA", (W + 2 * p, H + 2 * p), (0, 0, 0, 0))
        big.alpha_composite(im, (p, p))
        im = big
        W, H = im.size
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = im.split()[3]
    if shadow > 0:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sa = a.point(lambda v: int(v * shadow_alpha))
        sh.putalpha(sa)
        sh = sh.filter(ImageFilter.GaussianBlur(W * shadow))
        out.alpha_composite(sh, (int(W * shadow_off[0]), int(H * shadow_off[1])))
    if outline > 0:
        r = max(1, int(round(W * outline)))
        arr = np.asarray(a).astype(np.float32) / 255.0
        from scipy.ndimage import grey_dilation
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
        fp = (xx * xx + yy * yy) <= r * r
        dil = grey_dilation(arr, footprint=fp)
        ol = Image.new("RGBA", (W, H), outline_col + (0,))
        ol.putalpha(Image.fromarray((np.clip(dil, 0, 1) * 255).astype(np.uint8)))
        ol = ol.filter(ImageFilter.GaussianBlur(0.6))
        out.alpha_composite(ol)
    out.alpha_composite(im)
    if size:
        out = out.resize((size, size) if isinstance(size, int) else size, Image.LANCZOS)
    out.save(dst)
    return dst


def fit_ortho(cam, margin=0.06, objs=None):
    """Orthographic framing: centre the camera on everything visible and size it to fit with a margin."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    inv = cam.matrix_world.inverted()
    xs, ys = [], []
    for o in (objs or bpy.context.scene.objects):
        if o.type not in ("MESH", "CURVE", "FONT") or o.hide_render:
            continue
        ev = o.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except RuntimeError:
            continue
        if me is None:
            continue
        M = inv @ ev.matrix_world
        for v in me.vertices:
            p = M @ v.co
            xs.append(p.x)
            ys.append(p.y)
        ev.to_mesh_clear()
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sc = bpy.context.scene
    aspect = sc.render.resolution_x / sc.render.resolution_y
    w, h = x1 - x0, y1 - y0
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(w, h * aspect) * (1 + 2 * margin) if aspect >= 1 else max(w / aspect, h) * (1 + 2 * margin)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cam.location = cam.matrix_world @ Vector((cx, cy, 0))
    return cam


def weathered(name, base, patch, amount=0.4, scale=6.0, base_metal=1.0, patch_metal=0.0, rough=0.28, patch_rough=0.75,
              coat=0.0):
    """Metal with patches (bronze patina, rust): a noise mask mixes colour, metalness and roughness."""
    m, b, nt = _mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 8
    n.inputs["Roughness"].default_value = 0.62
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.66 - amount * 0.2
    ramp.inputs["From Max"].default_value = 0.69 - amount * 0.2
    nt.links.new(n.outputs["Fac"], ramp.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(ramp.outputs["Result"], mix.inputs["Factor"])
    mix.inputs["A"].default_value = lin(base)
    mix.inputs["B"].default_value = lin(patch)
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    for sock, a, c in (("Metallic", base_metal, patch_metal), ("Roughness", rough, patch_rough)):
        mf = nt.nodes.new("ShaderNodeMix")
        mf.data_type = "FLOAT"
        nt.links.new(ramp.outputs["Result"], mf.inputs["Factor"])
        mf.inputs["A"].default_value = a
        mf.inputs["B"].default_value = c
        nt.links.new(mf.outputs["Result"], b.inputs[sock])
    if coat > 0:
        b.inputs["Coat Weight"].default_value = coat
    return m


def toon_gold(name="ToonGold", top=(1.0, 0.92, 0.45), bottom=(0.95, 0.5, 0.08), axis="Z", rough=0.25, coat=0.8,
              metallic=0.25):
    """Bright 'game logo' gold: a glossy paint graded from yellow at the top to orange at the bottom along an axis of the
    object's bounding box (no dark reflections on faces that look straight at the camera)."""
    m, b, nt = _mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = lin(bottom)
    ramp.color_ramp.elements[1].color = lin(top)
    ramp.color_ramp.elements[0].position = 0.15
    ramp.color_ramp.elements[1].position = 0.85
    nt.links.new(sep.outputs[axis], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.05
    return m
