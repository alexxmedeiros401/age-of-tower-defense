"""Render frames of a unit GLB's clips (workbench).
usage: python3 -I shots.py -- GLB OUTDIR "Clip:f0-f1[:step];Clip2:3,5,7" AZ[,AZ..] [--elev 25] [--zoom 1] [--cz 1.9] [--cx 0] [--cy 0]
       [--rx 480 --ry 600] [--nobase] [--bones] [--tag name] [--wire]
Frames may be fractional. The character faces -Y; az 0 looks at his front, 90 at his left side (+X), 180 his back.
"""
import sys, os, math, argparse
import bpy, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("glb"); ap.add_argument("out"); ap.add_argument("spec"); ap.add_argument("az")
ap.add_argument("--elev", type=float, default=25.0)
ap.add_argument("--zoom", type=float, default=1.0)
ap.add_argument("--cz", type=float, default=None); ap.add_argument("--cx", type=float, default=None); ap.add_argument("--cy", type=float, default=None)
ap.add_argument("--rx", type=int, default=480); ap.add_argument("--ry", type=int, default=600)
ap.add_argument("--nobase", action="store_true"); ap.add_argument("--bones", action="store_true")
ap.add_argument("--tag", default=""); ap.add_argument("--flat", action="store_true")
ap.add_argument("--size", type=float, default=None)
a = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.glb)
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'):
        bpy.data.objects.remove(o)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
if a.nobase:
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.find_armature() is None:
            o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT' if a.flat else 'STUDIO'; sh.color_type = 'TEXTURE'
sh.show_cavity = True; sh.cavity_type = 'BOTH'
sh.show_object_outline = False
sc.display.render_aa = '8'
sc.render.resolution_x = a.rx; sc.render.resolution_y = a.ry
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.55, 0.6, 0.65)
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
ch = [o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature() == arm]
pts = [o.matrix_world @ mathutils.Vector(c) for o in ch for c in o.bound_box]
lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
ctr = (lo + hi) / 2
size = (a.size if a.size else max(hi - lo) * 1.45) / a.zoom
if a.cz is not None: ctr.z = a.cz
if a.cx is not None: ctr.x = a.cx
if a.cy is not None: ctr.y = a.cy
cam.data.ortho_scale = size
cam.data.clip_end = 200
if arm.animation_data is None: arm.animation_data_create()
os.makedirs(a.out, exist_ok=True)

def frames_of(s, act):
    if '-' in s:
        r, *st = s.split(':')
        f0, f1 = r.split('-'); step = float(st[0]) if st else 1.0
        out = []; f = float(f0)
        while f <= float(f1) + 1e-6:
            out.append(f); f += step
        return out
    return [float(x) for x in s.split(',')]

for item in a.spec.split(';'):
    clip, fr = item.split(':', 1)
    if clip == 'REST':
        arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
        frs = [0.0]
    else:
        act = bpy.data.actions[clip]
        arm.animation_data.action = act
        # Blender 5 slotted actions: make sure a slot is bound
        try:
            if arm.animation_data.action_slot is None and act.slots:
                arm.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        frs = frames_of(fr, act)
    for f in frs:
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        for az in [float(x) for x in a.az.split(',')]:
            r = 30.0; aa = math.radians(az); e = math.radians(a.elev)
            cam.location = ctr + mathutils.Vector((math.sin(aa) * math.cos(e) * r, -math.cos(aa) * math.cos(e) * r, math.sin(e) * r))
            cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
            fs = ('%05.1f' % f).replace('.', 'p')
            sc.render.filepath = os.path.join(a.out, f"{a.tag}{clip}_az{int(az):03d}_{fs}.png")
            bpy.ops.render.render(write_still=True)
print("done")
