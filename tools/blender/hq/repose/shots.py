# usage: python3 shots.py GLB OUTPREFIX "Clip:f1,f2,..;Clip2:..." az1,az2 [elev]
import bpy, sys, math, mathutils
glb, out, spec, azs = sys.argv[1:5]
elev = float(sys.argv[5]) if len(sys.argv) > 5 else 35
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
for o in bpy.data.objects:
    if o.type == 'MESH' and o.find_armature() is None and o.parent and o.parent.type != 'ARMATURE':
        if o.name.startswith(('Base','Flowers','GrassBlades','Flame','Flicker')): o.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
sc.display.shading.show_cavity = True
sc.render.resolution_x = int(__import__("os").environ.get("RX","360")); sc.render.resolution_y = int(__import__("os").environ.get("RY","480"))
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.55, 0.6, 0.65)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
if arm.animation_data is None: arm.animation_data_create()
# bbox of character mesh at rest
ch = [o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature() == arm]
pts = [o.matrix_world @ mathutils.Vector(c) for o in ch for c in o.bound_box]
lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
ctr = (lo + hi) / 2; size = max(hi - lo) * 1.35
Z = float(__import__('os').environ.get('ZOOM', '1'))
if Z != 1:
    ctr.z = lo.z + (hi.z - lo.z) * 0.68; size = size / Z
cam.data.ortho_scale = size
for item in spec.split(';'):
    clip, fr = item.split(':')
    arm.animation_data.action = bpy.data.actions[clip]
    for f in [int(x) for x in fr.split(',')]:
        sc.frame_set(f)
        FB = __import__('os').environ.get('FOCUS')
        if FB:     # close-up: centre on a bone (FOCUS=forearm.R:0.8 = 80% along it), ortho size FSIZE
            bn, _, t = FB.partition(':'); pb = arm.pose.bones[bn]; t = float(t or 0.5)
            ctr = arm.matrix_world @ (pb.head + (pb.tail - pb.head) * t); size = float(__import__('os').environ.get('FSIZE', '0.5'))
            cam.data.ortho_scale = size
        for az in [float(a) for a in azs.split(',')]:
            r = size * 3; a = math.radians(az); e = math.radians(elev)
            cam.location = ctr + mathutils.Vector((math.sin(a) * math.cos(e) * r, -math.cos(a) * math.cos(e) * r, math.sin(e) * r))
            cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f"{out}_{clip}_{f:02d}_az{int(az)}.png"
            bpy.ops.render.render(write_still=True)
