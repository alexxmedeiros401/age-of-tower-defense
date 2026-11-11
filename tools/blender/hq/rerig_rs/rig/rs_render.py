"""Workbench renders of the rigged scene (review tool)."""
import math
import bpy, mathutils


def setup(sc, rx=480, ry=600, nobase=True, flat=False):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'FLAT' if flat else 'STUDIO'; sh.color_type = 'TEXTURE'
    sh.show_cavity = True; sh.cavity_type = 'BOTH'
    sc.display.render_aa = '8'
    sc.render.resolution_x = rx; sc.render.resolution_y = ry
    if sc.world is None: sc.world = bpy.data.worlds.new('w')
    sc.world.color = (0.55, 0.6, 0.65)
    sc.view_settings.view_transform = 'Standard'
    cam = bpy.data.objects.get('rs_cam')
    if cam is None:
        cam = bpy.data.objects.new('rs_cam', bpy.data.cameras.new('rs_cam')); sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.clip_end = 200
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.find_armature() is None:
            o.hide_render = nobase
    return cam


def shoot(sc, cam, path, az, elev=25.0, size=3.0, ctr=(0.0, 0.06, 1.95)):
    """az 0 = from his front, 90 = from his left; ctr in world space (the armature sits at z = 0.9)."""
    cam.data.ortho_scale = size
    c = mathutils.Vector(ctr); a = math.radians(az); e = math.radians(elev); r = 30.0
    cam.location = c + mathutils.Vector((math.sin(a) * math.cos(e) * r, -math.cos(a) * math.cos(e) * r, math.sin(e) * r))
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
