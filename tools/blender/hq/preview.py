"""Fast clay/sculpt review renders (Workbench) and contact sheets."""
import math, os
import bpy
from mathutils import Vector


def setup(bg=(0.16, 0.17, 0.19)):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "OBJECT"
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.cavity_ridge_factor = 1.0
    sh.cavity_valley_factor = 1.3
    sh.show_shadows = True
    sh.shadow_intensity = 0.45
    sh.show_specular_highlight = True
    sc.display.shadow_focus = 0.2
    sc.render.film_transparent = False
    w = sc.world or bpy.data.worlds.new("W")
    sc.world = w
    w.color = bg
    sh.background_type = "WORLD"
    sc.render.image_settings.file_format = "PNG"
    if "PreviewCam" not in bpy.data.objects:
        cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
        sc.collection.objects.link(cam)
    cam = bpy.data.objects["PreviewCam"]
    sc.camera = cam
    return cam


def shot(path, target, dist, az_deg, el_deg, lens=85, res=(700, 700), ortho=None):
    sc = bpy.context.scene
    cam = setup() if sc.camera is None or sc.camera.name != "PreviewCam" else sc.camera
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = Vector(target)
    # az 0 = in front of the character (camera on -Y looking +Y)
    pos = t + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
    cam.location = pos
    cam.rotation_euler = (t - pos).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lens
    cam.data.clip_start = 0.01
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def sheet(paths, out, cols=None, label=None):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths]
    cols = cols or len(ims)
    rows = (len(ims) + cols - 1) // cols
    w, h = ims[0].size
    S = Image.new("RGB", (w * cols, h * rows), (20, 20, 22))
    for i, im in enumerate(ims):
        S.paste(im, ((i % cols) * w, (i // cols) * h))
    S.save(out)
    return out
