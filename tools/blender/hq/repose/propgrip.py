# Held-prop check and fix over the clips (Blender).
#   python3 propgrip.py IN.glb                 report: per parentless prop bone and clip, the hand it rides (nearest
#                                              in most frames) and frames where its hand-relative pose jumps
#                                              (> --mm mm or > --deg deg from both neighbours' average): a prop that
#                                              pops out of the fist for a frame or two.
#   python3 propgrip.py IN.glb OUT.glb FIX     FIX = "prop:clip:f0-f1:side;..." re-keys the prop in frames f0..f1 at the
#                                              hand-relative pose blended (slerp/lerp) between frame f0-1 and f1+1.
import bpy, sys, math
from mathutils import Matrix
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
IN = a[0]; OUT = a[1] if len(a) > 2 else None; FIX = a[2] if len(a) > 2 else None
MM = 25.0; DEG = 20.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
sc = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); P = arm.pose.bones; B = arm.data.bones
arm.animation_data_create()
PROPS = [b.name for b in B if b.parent is None and b.name != 'root']
def rel(f, p, s):
    sc.frame_set(f); return P['hand.' + s].matrix.inverted() @ P[p].matrix
if not FIX:
    for act in bpy.data.actions:
        arm.animation_data.action = act
        f0, f1 = [int(round(x)) for x in act.frame_range]
        for p in PROPS:
            dist = {s: [] for s in 'RL'}; R = {s: {} for s in 'RL'}
            for f in range(f0, f1 + 1):
                sc.frame_set(f)
                for s in 'RL':
                    dist[s].append((P[p].head - P['hand.' + s].head).length)
                    R[s][f] = P['hand.' + s].matrix.inverted() @ P[p].matrix
            s = min('RL', key=lambda s: sorted(dist[s])[len(dist[s]) // 2])
            med = sorted(dist[s])[len(dist[s]) // 2]
            if med > 0.25: continue
            bad = []
            for f in range(f0 + 1, f1):
                m0, m, m1 = R[s][f - 1], R[s][f], R[s][f + 1]
                mid = m0.translation.lerp(m1.translation, 0.5); dmm = (m.translation - mid).length * 1000
                q = m0.to_quaternion().slerp(m1.to_quaternion(), 0.5); dg = math.degrees(q.rotation_difference(m.to_quaternion()).angle)
                if dg > 180: dg = 360 - dg
                dn = (m0.translation - m1.translation).length * 1000
                if (dmm > MM and dmm > dn) or dg > DEG: bad.append((f, round(dmm), round(dg)))
            print(f"{act.name:8s} {p:14s} hand.{s} median {med*100:.0f} cm  jumps(frame, mm, deg): {bad}")
else:
    for it in FIX.split(';'):
        p, clip, fr, s = it.split(':'); fa, fb = [int(x) for x in fr.split('-')]
        arm.animation_data.action = bpy.data.actions[clip]
        A = rel(fa - 1, p, s); Bm = rel(fb + 1, p, s)
        for f in range(fa, fb + 1):
            t = (f - fa + 1) / (fb - fa + 2)
            loc = A.translation.lerp(Bm.translation, t); q = A.to_quaternion().slerp(Bm.to_quaternion(), t)
            sca = A.to_scale().lerp(Bm.to_scale(), t)
            m = Matrix.Translation(loc) @ q.to_matrix().to_4x4() @ Matrix.Diagonal(sca).to_4x4()
            sc.frame_set(f); P[p].matrix = P['hand.' + s].matrix @ m; bpy.context.view_layer.update()
            for path in ('location', 'rotation_quaternion', 'scale'): P[p].keyframe_insert(path, frame=f)
            print('fixed', p, clip, f)
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                              export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                              export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
    print('wrote', OUT)
