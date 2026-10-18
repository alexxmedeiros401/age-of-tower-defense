"""Cycles high->low baking into a texture atlas + texture composition."""
import os
import numpy as np
import bpy


def new_image(name, size, non_color=False, alpha=False):
    im = bpy.data.images.get(name)
    if im is not None:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, size, size, alpha=alpha, float_buffer=True)
    if non_color:
        im.colorspace_settings.name = "Non-Color"
    return im


def bake_material(low_ob, img):
    """A temporary material on the low-poly whose active node is the bake target image."""
    m = bpy.data.materials.new("BakeTarget_" + img.name)
    m.use_nodes = True
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.nodes.active = tex
    low_ob.data.materials.clear()
    low_ob.data.materials.append(m)
    return m


def bake(low_ob, hi_objs, img, kind, samples=4, margin=16, extrusion=0.012, maxdist=0.035, pass_filter=None):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.render.bake.use_selected_to_active = True
    sc.render.bake.cage_extrusion = extrusion
    sc.render.bake.max_ray_distance = maxdist
    sc.render.bake.margin = margin
    sc.render.bake.margin_type = "EXTEND"
    sc.render.bake.use_clear = True
    sc.render.bake.target = "IMAGE_TEXTURES"
    bake_material(low_ob, img)
    for o in sc.objects:
        o.select_set(False)
    for h in hi_objs:
        h.hide_set(False)
        h.hide_render = False
        h.select_set(True)
    low_ob.hide_set(False)
    low_ob.hide_render = False
    low_ob.select_set(True)
    bpy.context.view_layer.objects.active = low_ob
    vis = (low_ob.visible_camera, low_ob.visible_diffuse, low_ob.visible_glossy, low_ob.visible_shadow, low_ob.visible_transmission)
    low_ob.visible_camera = low_ob.visible_diffuse = low_ob.visible_glossy = low_ob.visible_shadow = low_ob.visible_transmission = False
    kw = dict(type=kind, use_selected_to_active=True, cage_extrusion=extrusion, max_ray_distance=maxdist, margin=margin,
              margin_type="EXTEND", use_clear=True)
    if kind == "DIFFUSE":
        kw["pass_filter"] = pass_filter or {"COLOR"}
    if kind == "NORMAL":
        kw["normal_space"] = "TANGENT"
    bpy.ops.object.bake(**kw)
    (low_ob.visible_camera, low_ob.visible_diffuse, low_ob.visible_glossy, low_ob.visible_shadow, low_ob.visible_transmission) = vis
    return img


def pixels(img):
    a = np.empty(len(img.pixels), np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def save_png(arr, path, srgb_encode=False):
    from PIL import Image
    a = np.clip(arr, 0, 1)
    if srgb_encode:
        a = np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1 / 2.4) - 0.055)
    a = (a[::-1] * 255 + 0.5).astype(np.uint8)
    mode = "RGBA" if a.shape[2] == 4 else "RGB"
    Image.fromarray(a, mode).save(path)
    return path


def srgb_to_lin(a):
    return np.where(a <= 0.04045, a / 12.92, np.power((a + 0.055) / 1.055, 2.4))


def blur(a, r=1.0):
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(a, sigma=(r, r, 0))


def compose(albedo_img, ao_img, rough_img, out_dir, prefix, ao_strength=0.72, extra_paint=None, sat=1.1, val=1.0):
    """albedo (sRGB bake) x AO -> albedo png; roughness -> ORM png (G=rough, B=metal 0); returns paths."""
    alb = pixels(albedo_img)[..., :3]           # float bake targets hold scene-linear values
    ao = blur(pixels(ao_img)[..., :3], 1.0)[..., :1]
    rough = pixels(rough_img)[..., :1]
    k = 1 - ao_strength + ao_strength * ao
    lin = alb * k
    if extra_paint is not None:
        lin = extra_paint(lin)
    os.makedirs(out_dir, exist_ok=True)
    pa = save_png(lin, os.path.join(out_dir, prefix + "_albedo.png"), srgb_encode=True)
    boost_png(pa, sat, val)
    orm = np.concatenate([np.ones_like(rough), rough, np.zeros_like(rough)], axis=2)
    po = save_png(orm, os.path.join(out_dir, prefix + "_orm.png"))
    return pa, po


def game_material(name, albedo_path, normal_path, orm_path, emission=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(albedo_path, check_existing=True)
    nt.links.new(ta.outputs["Color"], b.inputs["Base Color"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(normal_path, check_existing=True)
    tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = bpy.data.images.load(orm_path, check_existing=True)
    to.image.colorspace_settings.name = "Non-Color"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], b.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], b.inputs["Metallic"])
    b.inputs["Specular IOR Level"].default_value = 0.35
    return m


def flame_material(name="Flame", color=(1.0, 0.62, 0.16), strength=2.5):
    from mats import lin
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = lin(color)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def _group_object(joined, part_ids, name):
    """Copy of the joined low-poly keeping only faces whose 'part' is in part_ids (same UVs)."""
    import bmesh
    ob = joined.copy()
    ob.data = joined.data.copy()
    ob.name = name
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    ob.parent = None
    ob.matrix_world = joined.matrix_world.copy()
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    lay = bm.faces.layers.int.get("part")
    kill = [f for f in bm.faces if f[lay] not in part_ids]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def uv_mask(ob, size):
    from PIL import Image, ImageDraw
    im = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(im)
    uv = ob.data.uv_layers.active.data
    for p in ob.data.polygons:
        d.polygon([(uv[li].uv[0] * size, (1 - uv[li].uv[1]) * size) for li in p.loop_indices], fill=255, outline=255)   # outline: tiny faces still get pixels
    a = np.asarray(im)[::-1] > 0          # flip to Blender's bottom-up pixel order
    return a


def bake_groups(joined, groups, size, kinds, margin=10, extrusion=0.012, maxdist=0.035, ao_samples=32, ao_dist=0.18, all_hi=None, ao_exclude=()):
    """Per-part bakes composited into one atlas. groups: [(part_ids, [hi objects])].
    Surface lookups only see the part's own sculpt; AO still sees everything (all_hi stay visible)."""
    from scipy.ndimage import binary_dilation
    sc = bpy.context.scene
    if sc.world is None:
        sc.world = bpy.data.worlds.new("BakeWorld")
    sc.world.light_settings.distance = ao_dist
    out = {k: np.zeros((size, size, 4), np.float32) for k in kinds}
    covered = np.zeros((size, size), bool)
    joined.hide_render = True
    for gi, (pids, his) in enumerate(groups):
        tmp = _group_object(joined, set(pids), "BakeGroup_%d" % gi)
        if len(tmp.data.polygons) == 0:
            bpy.data.objects.remove(tmp)
            continue
        m = uv_mask(tmp, size)
        md = binary_dilation(m, iterations=margin) & ~covered
        for kind in kinds:
            hidden = []
            if kind == "AO":
                for x in ao_exclude:          # thin accessories must not leave baked shadows on what moves under them
                    if x not in his and not x.hide_render:
                        x.hide_render = True
                        hidden.append(x)
            img = new_image("grp_%s_%d" % (kind, gi), size, non_color=(kind != "DIFFUSE"))
            bake(tmp, his, img, kind, samples=(ao_samples if kind == "AO" else (2 if kind == "ROUGHNESS" else 4)),
                 margin=margin, extrusion=extrusion, maxdist=maxdist)
            px = pixels(img)
            o = out[kind]
            o[md] = px[md]
            o[m] = px[m]
            bpy.data.images.remove(img)
            for x in hidden:
                x.hide_render = False
        covered |= m
        bpy.data.objects.remove(tmp)
    joined.hide_render = False
    # anything never covered (empty atlas space): neutral values
    empty = ~binary_dilation(covered, iterations=margin)
    if "NORMAL" in out:
        out["NORMAL"][empty] = (0.5, 0.5, 1.0, 1.0)
    if "AO" in out:
        out["AO"][empty] = 1.0
    return out


def boost_png(path, sat=1.0, val=1.0):
    """Saturation/value lift in display space (the AO multiply dulls the bake a little)."""
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255.0
    l = (a.max(2, keepdims=True) + a.min(2, keepdims=True)) / 2
    out = np.clip((l + (a - l) * sat) * val, 0, 1)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(path)


def save_maps(maps, out_dir, prefix, ao_strength=0.72, extra_paint=None, sat=1.16, val=1.03):
    alb = maps["DIFFUSE"][..., :3]
    ao = blur(maps["AO"][..., :3], 1.0)[..., :1]
    rough = maps["ROUGHNESS"][..., :1]
    lin = alb * (1 - ao_strength + ao_strength * ao)
    if extra_paint is not None:
        lin = extra_paint(lin)
    os.makedirs(out_dir, exist_ok=True)
    pa = save_png(lin, os.path.join(out_dir, prefix + "_albedo.png"), srgb_encode=True)
    boost_png(pa, sat, val)
    po = save_png(np.concatenate([np.ones_like(rough), rough, np.zeros_like(rough)], axis=2), os.path.join(out_dir, prefix + "_orm.png"))
    pn = save_png(maps["NORMAL"][..., :3], os.path.join(out_dir, prefix + "_normal.png"))
    return pa, pn, po
