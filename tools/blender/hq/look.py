"""Hero lighting + Cycles settings (sun, sky fill, rim light), AgX look."""
import math
import bpy
import cycles_dev
from mathutils import Vector
from mats import lin


def setup(samples=128, res=(1200, 1200), transparent=True, denoise=True):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cycles_dev.use(sc)
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = denoise
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 2
    sc.cycles.transparent_max_bounces = 8
    sc.render.film_transparent = transparent
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except Exception:
        try:
            sc.view_settings.look = "Punchy"
        except Exception:
            pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    w = bpy.data.worlds.get("HQWorld") or bpy.data.worlds.new("HQWorld")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    mr.inputs["From Min"].default_value = 0.45
    mr.inputs["From Max"].default_value = 0.75
    fac = [s for s in mix.inputs if s.identifier == "Factor_Float"][0]
    a = [s for s in mix.inputs if s.identifier == "A_Color"][0]
    b = [s for s in mix.inputs if s.identifier == "B_Color"][0]
    nt.links.new(mr.outputs["Result"], fac)
    a.default_value = lin((0.55, 0.5, 0.42))        # warm ground bounce
    b.default_value = lin((0.62, 0.78, 1.0))        # sky
    res_out = [s for s in mix.outputs if s.identifier == "Result_Color"][0]
    nt.links.new(res_out, bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.55
    nt.links.new(bg.outputs[0], out.inputs[0])
    for n in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(n)
    def light(name, kind, energy, color, rot=None, loc=None, size=None, angle=None):
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = color
        if size is not None:
            ld.size = size
        if angle is not None:
            ld.angle = angle
        ob = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(ob)
        if rot is not None:
            ob.rotation_euler = rot
        if loc is not None:
            ob.location = loc
        return ob
    light("Key", "SUN", 4.2, (1.0, 0.93, 0.82), rot=(math.radians(48), math.radians(8), math.radians(-38)), angle=math.radians(3))
    rim = light("Rim", "AREA", 900.0, (1.0, 0.9, 0.78), loc=(2.5, 6.0, 5.2), size=3.0)
    rim.rotation_euler = (Vector((0, 0, 1.5)) - Vector(rim.location)).to_track_quat("-Z", "Y").to_euler()
    fill = light("Fill", "AREA", 260.0, (0.75, 0.85, 1.0), loc=(-6.0, -4.0, 3.0), size=5.0)
    fill.rotation_euler = (Vector((0, 0, 1.2)) - Vector(fill.location)).to_track_quat("-Z", "Y").to_euler()


def camera(target, dist, az_deg, el_deg, lens=60, name="HeroCam"):
    sc = bpy.context.scene
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        sc.collection.objects.link(cam)
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = Vector(target)
    pos = t + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
    cam.location = pos
    cam.rotation_euler = (t - pos).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.clip_start = 0.05
    sc.camera = cam
    return cam


def backdrop(png_in, png_out, top=(0.93, 0.9, 0.84), bottom=(0.74, 0.69, 0.6)):
    """Composite a transparent render over a soft vertical gradient with a contact shadow ellipse."""
    from PIL import Image, ImageFilter, ImageDraw
    im = Image.open(png_in).convert("RGBA")
    w, h = im.size
    bg = Image.new("RGBA", (w, h))
    px = bg.load()
    for y in range(h):
        t = y / (h - 1)
        c = tuple(int(255 * (top[k] * (1 - t) + bottom[k] * t)) for k in range(3)) + (255,)
        for x in range(w):
            px[x, y] = c
    # soft vignette
    vig = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(vig)
    d.ellipse((-w * 0.25, -h * 0.2, w * 1.25, h * 1.2), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(w * 0.12))
    dark = Image.new("RGBA", (w, h), (60, 50, 40, 255))
    bg = Image.composite(bg, dark, vig.point(lambda v: int(150 + v * 105 / 255)))
    bg.alpha_composite(im)
    bg.convert("RGB").save(png_out)
    return png_out
