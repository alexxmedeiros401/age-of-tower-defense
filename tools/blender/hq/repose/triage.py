# Triage (detection only) of a unit's arm motion over its clips, per frame:
#   pen_<side>_head / pen_<side>_torso : how deep (m) forearm / hand / held-weapon points (and, for the head, upper-arm
#       points) sit inside the head (with hair, beard, helmet: everything the head/neck bones carry) or the torso;
#   near_<side>_head : how close (m) the hand / weapon comes to the head when it is outside (crossing the face);
#   <side>_psi / _fortw / _elbow / _wrist : upper-arm roll, forearm twist (+ its twist bone), elbow bend, wrist angle.
# The body is voxelized at rest (1 cm, holes closed and filled) and every voxel labelled with the bone that carries the
# nearest rest vertex; a posed point is taken back to rest through the head / chest / spine / root bone and looked up.
# Points that are already inside at rest (a shoulder under the hair) count only by how much deeper they go.
# usage: python3 triage.py IN.glb OUT.json [CLIP,CLIP..|all] [STEP]
# Parentless prop bones (pistols, cutlass, rifle: posed every frame in armature space) count for the hand that holds
# them that frame (grip within 0.25 of the hand), else not at all (tucked / sheathed).
import bpy, sys, json, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
from scipy import ndimage
from scipy.spatial import cKDTree

IN, OUT = sys.argv[1:3]
CLIPS = sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] not in ('', 'all') else None
STEP = int(sys.argv[4]) if len(sys.argv) > 4 else 1
VOX = 0.01
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
sc = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
P = arm.pose.bones; B = arm.data.bones
AW = arm.matrix_world.copy()
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature() == arm]

def subtree(n):
    out = [n]
    for c in B[n].children: out += subtree(c.name)
    return out
HEAD = set(subtree('neck'))
TB = ['chest', 'spine', 'root']
ARMB = {s: set(subtree('clavicle.' + s)) | {b.name for b in B if b.name.endswith('_half.' + s)} for s in 'RL'}
UPPER = {s: {'upperarm.' + s, 'upperarm_half.' + s, 'clavicle.' + s} for s in 'RL'}
PROPS = [b.name for b in B if b.parent is None and b.name != 'root']

info = []
for o in meshes:
    gname = {g.index: g.name for g in o.vertex_groups}
    dom = []
    for v in o.data.vertices:
        best = ('', 0)
        for g in v.groups:
            if g.weight > best[1]: best = (gname[g.group], g.weight)
        dom.append(best[0])
    o.data.calc_loop_triangles()
    tris = np.array([t.vertices[:] for t in o.data.loop_triangles])
    info.append((o, np.array(dom, dtype=object), tris))

def posed_coords():
    dg = bpy.context.evaluated_depsgraph_get(); cos = []
    for o, dom, tris in info:
        ev = o.evaluated_get(dg); m = ev.to_mesh()
        a = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', a); a = a.reshape(-1, 3)
        M = np.array(o.matrix_world); cos.append(a @ M[:3, :3].T + M[:3, 3]); ev.to_mesh_clear()
    return cos

# ---- rest pose
arm.animation_data_create(); arm.animation_data.action = None
for pb in P: pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
sc.frame_set(0); bpy.context.view_layer.update()
rest = posed_coords()
allv = np.vstack(rest); alld = np.concatenate([d for _, d, _ in info])
lo = allv.min(0) - 0.05; hi = allv.max(0) + 0.05
shape = np.ceil((hi - lo) / VOX).astype(int) + 1
occ = np.zeros(shape, bool)
for (o, dom, tris), co in zip(info, rest):
    if not len(tris): continue
    a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    L = np.maximum(np.linalg.norm(b - a, axis=1), np.maximum(np.linalg.norm(c - a, axis=1), np.linalg.norm(c - b, axis=1)))
    n = np.clip(np.ceil(L / (VOX * 0.5)).astype(int), 1, 60)
    for k in np.unique(n):
        sel = n == k
        u, v = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = (u + v) <= k
        u = u[m] / k; v = v[m] / k
        pts = a[sel][:, None] * (1 - u - v)[None, :, None] + b[sel][:, None] * u[None, :, None] + c[sel][:, None] * v[None, :, None]
        ij = np.round((pts.reshape(-1, 3) - lo) / VOX).astype(int)
        occ[ij[:, 0], ij[:, 1], ij[:, 2]] = True
occ = ndimage.binary_closing(occ, iterations=2)
solid = ndimage.binary_fill_holes(occ)
print('voxels', shape, 'surface', occ.sum(), 'solid', solid.sum(), flush=True)
kd = cKDTree(allv)
idx = np.argwhere(solid)
_, nn = kd.query(lo + idx * VOX)
CLASS = {}
lab = np.zeros(shape, np.int8)       # 0 out, 1 head, 2 torso (chest/spine/root/cape...), 3 arm, 4 legs/other
dn = alld[nn]
cls = np.full(len(dn), 4, np.int8)
cls[np.isin(dn, list(HEAD))] = 1
cls[np.isin(dn, TB) | np.array([str(x).startswith(('cape', 'belly', 'skirt', 'flare')) for x in dn])] = 2
cls[np.isin(dn, list(ARMB['R'] | ARMB['L']) + PROPS)] = 3
lab[idx[:, 0], idx[:, 1], idx[:, 2]] = cls
depth = ndimage.distance_transform_edt(solid) * VOX           # depth below the body's surface
head_d = ndimage.distance_transform_edt(lab != 1) * VOX         # distance to the head volume
REST = {b: (AW @ B[b].matrix_local) for b in ['head'] + TB}

def look(pts_rest):
    ij = np.round((pts_rest - lo) / VOX).astype(int)
    ok = np.all((ij >= 0) & (ij < shape), axis=1)
    ij = np.clip(ij, 0, shape - 1)
    L = np.where(ok, lab[ij[:, 0], ij[:, 1], ij[:, 2]], 0)
    D = np.where(ok, depth[ij[:, 0], ij[:, 1], ij[:, 2]], 0)
    H = np.where(ok, head_d[ij[:, 0], ij[:, 1], ij[:, 2]], 1.0)
    return L, D, H

def to_rest(b, pts):
    M = np.array(REST[b] @ (AW @ P[b].matrix).inverted())
    return pts @ M[:3, :3].T + M[:3, 3]

def measure(pts):
    """per point: head penetration depth, torso penetration depth, distance to head (outside)"""
    L, D, H = look(to_rest('head', pts))
    ph = np.where(L == 1, D, 0.0)
    pt = np.zeros(len(pts))
    for b in TB:
        L2, D2, _ = look(to_rest(b, pts))
        pt = np.maximum(pt, np.where(L2 == 2, D2, 0.0))
    return ph, pt, H

rng = np.random.default_rng(0)
samples = []
for mi, (o, dom, tris) in enumerate(info):
    for s in 'RL':
        up = np.where(np.isin(dom, list(UPPER[s] - {'clavicle.' + s})))[0]
        lw = np.where(np.isin(dom, list(ARMB[s] - UPPER[s])))[0]
        if len(up): samples.append((mi, rng.choice(up, min(len(up), 600), replace=False), s, 'upper'))
        if len(lw): samples.append((mi, rng.choice(lw, min(len(lw), 2500), replace=False), s, 'lower'))
    for pb in PROPS:
        pv = np.where(dom == pb)[0]
        if len(pv): samples.append((mi, rng.choice(pv, min(len(pv), 1500), replace=False), pb, 'prop'))
BASE = []
for mi, ids, who, kind in samples:
    ph, pt, _ = measure(rest[mi][ids])
    BASE.append((ph, pt))

def wrapd(a):
    return (a + 180) % 360 - 180

res = {}
for act in bpy.data.actions:
    if CLIPS and act.name not in CLIPS: continue
    arm.animation_data.action = act
    f0, f1 = [int(round(x)) for x in act.frame_range]
    rows = []
    for f in sorted(set(list(range(f0, f1 + 1, STEP)) + [f1])):
        sc.frame_set(f)
        cos = posed_coords()
        hands = {s: AW @ P['hand.' + s].head for s in 'RL'}
        row = {'f': f}
        for k, (mi, ids, who, kind) in enumerate(samples):
            side = who
            if kind == 'prop':
                ph_ = AW @ P[who].head
                d = {s: (ph_ - hands[s]).length for s in 'RL'}
                side = min(d, key=d.get)
                if d[side] > 0.25: continue
            ph, pt, H = measure(cos[mi][ids])
            ph = np.maximum(0, ph - BASE[k][0] - 0.005); pt = np.maximum(0, pt - BASE[k][1] - 0.005)
            hk = 'pen_%s_%s' % (side, 'shoulder_head' if kind == 'upper' else 'head')
            row[hk] = round(max(row.get(hk, 0), float(ph.max())), 3)
            if kind != 'upper':
                row['pen_%s_torso' % side] = round(max(row.get('pen_%s_torso' % side, 0), float(pt.max())), 3)
                row['near_%s_head' % side] = round(min(row.get('near_%s_head' % side, 9), float(H.min())), 3)
        for s in 'RL':
            u = P['upperarm.' + s].rotation_quaternion; fq = P['forearm.' + s].rotation_quaternion
            sw_u, tw_u = u.to_swing_twist('Y'); sw_f, tw_f = fq.to_swing_twist('Y')
            row[s + '_psi'] = round(wrapd(math.degrees(tw_u)), 1)
            hq = P['hand.' + s].rotation_quaternion
            if ('forearm_twist.' + s) in B:      # the twist lives in the hand (its twist bone shares it): report it as the forearm's
                hsw, htw = hq.to_swing_twist('Y')
                row[s + '_fortw'] = round(wrapd(math.degrees(tw_f) + math.degrees(htw)), 1)
                a = math.degrees(Quaternion(hsw).angle)
            else:
                row[s + '_fortw'] = round(wrapd(math.degrees(tw_f)), 1)
                a = math.degrees(hq.angle)
            row[s + '_elbow'] = round(math.degrees(sw_f.angle), 1)
            row[s + '_wrist'] = round(min(a, 360 - a), 1)
        rows.append(row)
    summ = {}
    for s in 'RL':
        for j in ('psi', 'fortw', 'elbow', 'wrist'):
            vals = [r[s + '_' + j] for r in rows]
            dl = [abs(wrapd(b - a)) for a, b in zip(vals, vals[1:])]
            summ[s + '_' + j] = [min(vals), max(vals), round(max(dl), 1) if dl else 0]
    for k in sorted({k for r in rows for k in r if k.startswith('pen')}):
        v = [(r.get(k, 0), r['f']) for r in rows]
        summ[k] = [max(v)[0], [f for x, f in v if x > 0.01]]
    for k in sorted({k for r in rows for k in r if k.startswith('near')}):
        v = [(r.get(k, 9), r['f']) for r in rows]
        summ[k] = [min(v)[0], [f for x, f in v if x <= 0.02]]
    res[act.name] = {'summary': summ, 'rows': rows}
    print('SUMMARY', act.name, json.dumps(summ), flush=True)
json.dump(res, open(OUT, 'w'))
