"""Paint bone weights on the bind mesh (rs_rig.blend). usage: -- rs_rig.blend OUTPREFIX bone[,bone..] az[,az] [size cx cy cz]"""
import sys, os, math, bpy, mathutils, numpy as np
argv = sys.argv[sys.argv.index("--") + 1:]
blend, out, bones, azs = argv[0], argv[1], argv[2].split(','), [float(x) for x in argv[3].split(',')]
size, cx, cy, cz = [float(x) for x in argv[4:8]] if len(argv) > 7 else (3.0, 0, 0.06, 1.95)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
ob = bpy.data.objects['Caveman']; me = ob.data
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not ob: o.hide_render = True
ob.modifiers.clear()
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_cavity = True
sc.render.resolution_x = 560; sc.render.resolution_y = 560
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.55, 0.6, 0.65); sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size
ctr = mathutils.Vector((cx, cy, cz))
for bone in bones:
    gi = ob.vertex_groups[bone].index
    t = np.zeros(len(me.vertices))
    for v in me.vertices:
        for g in v.groups:
            if g.group == gi: t[v.index] = g.weight
    C = np.stack([np.clip(1.5 - np.abs(4 * t - 3), 0, 1), np.clip(1.5 - np.abs(4 * t - 2), 0, 1), np.clip(1.5 - np.abs(4 * t - 1), 0, 1)], 1)
    C[t <= 0.001] = (0.25, 0.25, 0.25)
    name = 'w_' + bone
    ca = me.color_attributes.get(name) or me.color_attributes.new(name, 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', np.concatenate([C, np.ones((len(C), 1))], 1).ravel())
    me.color_attributes.active_color = ca
    for az in azs:
        a = math.radians(az); e = math.radians(12); r = 20
        cam.location = ctr + mathutils.Vector((math.sin(a) * math.cos(e) * r, -math.cos(a) * math.cos(e) * r, math.sin(e) * r))
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = '%s_%s_az%03d.png' % (out, bone, int(az))
        bpy.ops.render.render(write_still=True)
