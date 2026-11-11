"""Render the low mesh with per-vertex colours. usage: -- low.blend colors.npy OUTPREFIX [az,az,.. [elev [size cx cy cz]]]
colors.npy: (nverts, 3) or (nverts,) scalar (blue->red)."""
import sys, os, math, bpy, mathutils, numpy as np
argv = sys.argv[sys.argv.index("--") + 1:]
path, cpath, out = argv[:3]
azs = [float(x) for x in argv[3].split(',')] if len(argv) > 3 else [0, 90, 180, 270]
elev = float(argv[4]) if len(argv) > 4 else 5.0
size, cx, cy, cz = [float(x) for x in argv[5:9]] if len(argv) > 8 else (2.4, 0, 0, 1.05)
bpy.ops.wm.open_mainfile(filepath=path)
sc = bpy.context.scene
ob = bpy.data.objects['HeroLow']; me = ob.data
C = np.load(cpath)
if C.ndim == 1:
    t = np.clip(C, 0, 1)
    C = np.stack([np.clip(1.5 - np.abs(4 * t - 3), 0, 1), np.clip(1.5 - np.abs(4 * t - 2), 0, 1), np.clip(1.5 - np.abs(4 * t - 1), 0, 1)], 1)
    C[t <= 0.001] = (0.25, 0.25, 0.25)
ca = me.color_attributes.new('wcol', 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set('color', np.concatenate([C, np.ones((len(C), 1))], 1).ravel())
me.color_attributes.active_color = ca
try: me.color_attributes.render_color_index = list(me.color_attributes).index(ca)
except Exception: pass
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_cavity = True
sc.render.resolution_x = 700; sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.55, 0.6, 0.65)
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size
ctr = mathutils.Vector((cx, cy, cz))
for az in azs:
    a = math.radians(az); e = math.radians(elev); r = 20
    cam.location = ctr + mathutils.Vector((math.sin(a) * math.cos(e) * r, -math.cos(a) * math.cos(e) * r, math.sin(e) * r))
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = '%s_az%03d.png' % (out, int(az))
    bpy.ops.render.render(write_still=True)
