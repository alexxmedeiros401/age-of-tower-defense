# Re-author the Rock Slinger's arm motion (Whirl, Throw) with IK hand paths designed around the Tripo body.
# usage: python3 author_rs.py IN.glb OUT.glb
import bpy, sys, math
from mathutils import Vector, Matrix, Quaternion

IN, OUT = sys.argv[1:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
sc = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
P = arm.pose.bones
B = arm.data.bones
AW = arm.matrix_world.copy()
chest_rest = B['chest'].matrix_local.copy()

def V(*a): return Vector(a)

# ---- key poses (armature space, rest chest frame; front is -Y, the character's right is -X) ----
# hand (wrist) targets and elbow poles for the right (sling) arm
READY_R = V(-0.70, -0.06, 0.92)        # hand by the hip, a little forward
POLE_DOWN_R = V(-0.95, 0.35, 1.05)     # elbow out and back
THROW_R = [  # frame, hand, pole
    (0,  READY_R,                 POLE_DOWN_R),
    (4,  V(-0.80, -0.02, 1.30),   V(-1.05, 0.30, 1.05)),   # lift out to the side
    (8,  V(-0.80, 0.18, 1.72),    V(-1.05, 0.25, 1.20)),   # high beside the head, cocked back
    (10, V(-0.74, 0.22, 1.80),    V(-1.05, 0.30, 1.30)),   # top of the wind-up
    (13, V(-0.64, -0.38, 1.66),   V(-1.10, 0.10, 1.40)),   # release: whip forward, still outside the hair
    (16, V(-0.52, -0.48, 1.28),   V(-1.05, 0.05, 1.20)),   # follow through forward-down
    (19, V(-0.58, -0.40, 1.02),   V(-1.00, 0.20, 1.05)),
    (24, READY_R,                 POLE_DOWN_R),
]
READY_L = V(0.70, -0.04, 0.92)
POLE_L = V(0.95, 0.35, 1.05)
THROW_L = [
    (0,  READY_L,                 POLE_L),
    (5,  V(0.52, -0.42, 1.30),    V(0.95, 0.10, 1.15)),    # point at the target
    (13, V(0.50, -0.46, 1.34),    V(0.95, 0.10, 1.15)),
    (17, V(0.62, -0.18, 1.05),    V(0.95, 0.30, 1.05)),
    (24, READY_L,                 POLE_L),
]
def whirl_r(f, n=32):
    a = 2 * math.pi * f / n
    return V(-0.74 + 0.05 * math.cos(a), -0.10 + 0.07 * math.sin(a), 1.00 + 0.05 * math.sin(a)), POLE_DOWN_R
def whirl_l(f, n=32):
    return READY_L + V(0, 0, 0.012 * math.sin(2 * math.pi * f / n)), POLE_L

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
act0 = bpy.data.actions['Throw']; arm.animation_data.action = act0
for side in ('R', 'L'):
    c = add_ik(side, tR if side == 'R' else tL, pR if side == 'R' else pL, 0)
    best = None
    for ang in range(-180, 180, 15):
        c.pole_angle = math.radians(ang)
        score = 0
        for f in (0, 8, 13):
            sc.frame_set(f)
            hk, pk = interp(THROW_R if side == 'R' else THROW_L, f)
            place(side, hk, pk, f); bpy.context.view_layer.update()
            score += elbow_off_plane(side)
        if best is None or score > best[0]: best = (score, ang)
    # refine
    for ang in [best[1] + d for d in range(-14, 15, 2)]:
        c.pole_angle = math.radians(ang); score = 0
        for f in (0, 8, 13):
            sc.frame_set(f); hk, pk = interp(THROW_R if side == 'R' else THROW_L, f)
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
results['Throw'] = bake('Throw', lambda f: interp(THROW_R, f), lambda f: interp(THROW_L, f))
results['Whirl'] = bake('Whirl', whirl_r, whirl_l, loop=True)

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
