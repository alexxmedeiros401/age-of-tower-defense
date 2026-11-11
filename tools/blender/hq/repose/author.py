# Re-author the Rock Slinger's arm motion (Whirl, Throw) with IK hand paths designed around the Tripo body.
# usage: python3 author_rs.py IN.glb OUT.glb
import bpy, sys, math
from mathutils import Vector, Matrix, Quaternion

IN, OUT, CFGPY = sys.argv[1:4]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
sc = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
P = arm.pose.bones
B = arm.data.bones
AW = arm.matrix_world.copy()
chest_rest = B['chest'].matrix_local.copy()

def V(*a): return Vector(a)

import importlib.util
_sp = importlib.util.spec_from_file_location('cfg', CFGPY); C = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(C)
def interp(keys, f):
    # Catmull-Rom through the keys (clamped at the ends)
    fs = [k[0] for k in keys]
    if f <= fs[0]: return keys[0][1], keys[0][2]
    if f >= fs[-1]: return keys[-1][1], keys[-1][2]
    i = max(j for j in range(len(fs)) if fs[j] <= f)
    t = (f - fs[i]) / (fs[i + 1] - fs[i])
    def cr(idx):
        p0 = keys[max(i - 1, 0)][idx]; p1 = keys[i][idx]; p2 = keys[i + 1][idx]; p3 = keys[min(i + 2, len(keys) - 1)][idx]
        t2, t3 = t * t, t * t * t
        return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
    return cr(1), cr(2)

# ---- IK setup ----
def mk_empty(name):
    e = bpy.data.objects.new(name, None); sc.collection.objects.link(e); return e
tR, pR, tL, pL = mk_empty('tR'), mk_empty('pR'), mk_empty('tL'), mk_empty('pL')
def add_ik(side, t, p, angle):
    c = P['forearm.' + side].constraints.new('IK')
    c.target = t; c.pole_target = p; c.chain_count = 2; c.pole_angle = math.radians(angle); c.use_tail = True
    return c

ARM_BONES = ['clavicle.R', 'upperarm.R', 'forearm.R', 'hand.R', 'clavicle.L', 'upperarm.L', 'forearm.L', 'hand.L']

def place(side, hand, pole, f):
    # chest-relative -> current pose
    cm = P['chest'].matrix @ chest_rest.inverted()
    t = AW @ (cm @ hand); p = AW @ (cm @ pole)
    (tR if side == 'R' else tL).location = t
    (pR if side == 'R' else pL).location = p

def elbow_off_plane(side):
    # signed distance of the elbow from the shoulder-hand-pole plane (want ~0, on the pole side)
    s = AW @ P['upperarm.' + side].head; e = AW @ P['forearm.' + side].head; h = AW @ P['forearm.' + side].tail
    pole = (pR if side == 'R' else pL).location
    mid = (s + h) / 2
    return (e - mid).normalized().dot((pole - mid).normalized())

# pick the pole angle per side (Blender's pole angle depends on the bone roll)
best_angle = {}
act0 = bpy.data.actions[C.ATTACK]; arm.animation_data.action = act0
for side in ('R', 'L'):
    c = add_ik(side, tR if side == 'R' else tL, pR if side == 'R' else pL, 0)
    best = None
    for ang in range(-180, 180, 15):
        c.pole_angle = math.radians(ang)
        score = 0
        for f in (0, 8, 13):
            sc.frame_set(f)
            hk, pk = interp(C.ATK_R if side == 'R' else C.ATK_L, f)
            place(side, hk, pk, f); bpy.context.view_layer.update()
            score += elbow_off_plane(side)
        if best is None or score > best[0]: best = (score, ang)
    # refine
    for ang in [best[1] + d for d in range(-14, 15, 2)]:
        c.pole_angle = math.radians(ang); score = 0
        for f in (0, 8, 13):
            sc.frame_set(f); hk, pk = interp(C.ATK_R if side == 'R' else C.ATK_L, f)
            place(side, hk, pk, f); bpy.context.view_layer.update(); score += elbow_off_plane(side)
        if score > best[0]: best = (score, ang)
    best_angle[side] = best[1]; c.pole_angle = math.radians(best[1])
    print('pole angle', side, best)

def sling_lag(frames, hand_pos):
    # sling hangs from the hand and trails its motion
    n = len(frames)
    dirs = []
    for k in range(n):
        v = hand_pos[min(k + 1, n - 1)] - hand_pos[max(k - 1, 0)]
        d = Vector((0, 0, -1)) - v * 6.0
        dirs.append(d.normalized())
    return dirs

def bake(clip, rkeys, lkeys, loop=False):
    act = bpy.data.actions[clip]; arm.animation_data.action = act
    f0, f1 = [int(x) for x in act.frame_range]
    frames = list(range(f0, f1 + 1))
    mats = {}
    hand_pos = []
    for f in frames:
        sc.frame_set(f)
        hr, pr = rkeys(f); hl, pl = lkeys(f)
        place('R', hr, pr, f); place('L', hl, pl, f)
        bpy.context.view_layer.update()
        mats[f] = {b: P[b].matrix.copy() for b in ['upperarm.R', 'forearm.R', 'upperarm.L', 'forearm.L']}
        hand_pos.append(AW @ P['forearm.R'].tail)
    return act, frames, mats, hand_pos

results = {}
results[C.ATTACK] = bake(C.ATTACK, lambda f: interp(C.ATK_R, f), lambda f: interp(C.ATK_L, f))
results[C.LOOP] = bake(C.LOOP, C.loop_r, C.loop_l, loop=True)

# remove the IK and write the baked arm keys
for side in ('R', 'L'):
    for c in list(P['forearm.' + side].constraints): P['forearm.' + side].constraints.remove(c)
for clip, (act, frames, mats, hand_pos) in results.items():
    arm.animation_data.action = act
    dirs = sling_lag(frames, hand_pos)
    for k, f in enumerate(frames):
        sc.frame_set(f)
        for side in ('R', 'L'):
            # straight wrist, clavicle as authored
            P['hand.' + side].rotation_quaternion = Quaternion()
            for b in ('upperarm.' + side, 'forearm.' + side):
                P[b].matrix = mats[f][b]
                bpy.context.view_layer.update()
            for b in ('upperarm.' + side, 'forearm.' + side, 'hand.' + side):
                P[b].keyframe_insert('rotation_quaternion', frame=f)
            P['upperarm_half.' + side].rotation_quaternion = Quaternion().slerp(P['upperarm.' + side].rotation_quaternion, 0.5)
            P['forearm_half.' + side].rotation_quaternion = Quaternion().slerp(P['forearm.' + side].rotation_quaternion, 0.5)
            P['upperarm_half.' + side].keyframe_insert('rotation_quaternion', frame=f)
            P['forearm_half.' + side].keyframe_insert('rotation_quaternion', frame=f)
        bpy.context.view_layer.update()
        if getattr(C, 'club_dir', None):
            want = C.club_dir(clip, f)
            hb = P['hand.R']; m = AW @ hb.matrix
            cm = P['chest'].matrix @ chest_rest.inverted()
            want_w = (AW.to_3x3() @ cm.to_3x3() @ want).normalized()
            d0 = (m.to_3x3() @ (B['hand.R'].matrix_local.to_3x3().inverted() @ C.CLUB_AXIS)).normalized()
            q = d0.rotation_difference(want_w); head = m.translation.copy()
            hb.matrix = AW.inverted() @ (Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ m)
            bpy.context.view_layer.update()
            hb.keyframe_insert('rotation_quaternion', frame=f)
        if not getattr(C, 'SLING', False):
            continue
        # sling: point its axis along the lag direction
        sl = P['sling']
        m = AW @ sl.matrix
        y = m.to_3x3().col[1].normalized()
        q = y.rotation_difference(dirs[k])
        head = m.translation.copy()
        nm = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ m
        sl.matrix = AW.inverted() @ nm
        bpy.context.view_layer.update()
        sl.keyframe_insert('rotation_quaternion', frame=f)

for o in (tR, pR, tL, pL): bpy.data.objects.remove(o)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                          export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                          export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
print('wrote', OUT)
