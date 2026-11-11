# Render every frame of the given clips (workbench, game-like camera) for a before/after video.
# usage: python3 frames.py GLB OUTDIR "Clip,Clip.." AZ[,AZ] [ELEV]   -> OUTDIR/<Clip>_az<AZ>_<f:03d>.png
# RX/RY env: size; ZOOM env: frame the upper body (1 = whole unit)
import bpy, sys, math, os, mathutils
glb, out, clips, azs = sys.argv[1:5]
elev = float(sys.argv[5]) if len(sys.argv) > 5 else 35
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
for o in bpy.data.objects:
    if o.type == 'MESH' and o.find_armature() is None and o.parent and o.parent.type != 'ARMATURE':
        if o.name.startswith(('Base', 'Flowers', 'GrassBlades', 'Flame', 'Flicker')): o.hide_render = True
    if o.name.startswith('Icosphere'): o.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.show_cavity = True
sc.render.resolution_x = int(os.environ.get("RX", "360")); sc.render.resolution_y = int(os.environ.get("RY", "480"))
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.55, 0.6, 0.65)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
arm.animation_data_create()
ch = [o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature() == arm]
pts = [o.matrix_world @ mathutils.Vector(c) for o in ch for c in o.bound_box]
lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
ctr = (lo + hi) / 2; size = max(hi - lo) * 1.35
z = float(os.environ.get("ZOOM", "1"))
if z != 1:
    ctr.z = lo.z + (hi.z - lo.z) * 0.68; size = size / z
cam.data.ortho_scale = size
for clip in clips.split(','):
    act = bpy.data.actions[clip]; arm.animation_data.action = act
    f0, f1 = [int(round(x)) for x in act.frame_range]
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for az in [float(a) for a in azs.split(',')]:
            r = size * 3; a = math.radians(az); e = math.radians(elev)
            cam.location = ctr + mathutils.Vector((math.sin(a) * math.cos(e) * r, -math.cos(a) * math.cos(e) * r, math.sin(e) * r))
            cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f"{out}/{clip}_az{int(az)}_{f:03d}.png"
            bpy.ops.render.render(write_still=True)
