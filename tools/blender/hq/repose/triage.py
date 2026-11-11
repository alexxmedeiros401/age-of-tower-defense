# Triage (detection only): per clip and frame, how deep arm/hand/weapon vertices sit inside the head/neck and the
# torso, plus the arm joint numbers (upper-arm roll, forearm twist, wrist, elbow) and the chest-relative wrist
# positions (a reference for authoring).
# usage: python3 triage.py GLB OUT.json [MESH] [STEP]
#   MESH: the character mesh (default: the biggest mesh skinned to the rig); STEP: frame step (default 1)
import bpy, sys, json, math
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree

GLB, OUT = sys.argv[1:3]
MESH = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != '-' else None
STEP = int(sys.argv[4]) if len(sys.argv) > 4 else 1
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
P = arm.pose.bones; B = arm.data.bones
AW = arm.matrix_world.copy()
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature() == arm]
me = bpy.data.objects[MESH] if MESH else max(meshes, key=lambda o: len(o.data.vertices))

def subtree(n):
    out = [n]
    for c in B[n].children: out += subtree(c.name)
    return out

gname = {g.index: g.name for g in me.vertex_groups}
W = []; dom = []
for v in me.data.vertices:
    d = {}
    for g in v.groups:
        if g.weight > 0: d[gname[g.group]] = d.get(gname[g.group], 0) + g.weight
    s = sum(d.values()) or 1
    d = {k: w / s for k, w in d.items()}
    W.append(d); dom.append(max(d, key=d.get) if d else '')
tris = [tuple(p.vertices) for p in me.data.polygons]
HEAD = {'head', 'neck'} | {b.name for b in B if b.parent and b.parent.name == 'head'}
TORSO = {'chest', 'spine', 'root'}
htris = [t for t in tris if all(dom[i] in HEAD for i in t)]
ttris = [t for t in tris if all(dom[i] in TORSO for i in t)]
rng = np.random.default_rng(0)
SIDES = {}
for s in ('R', 'L'):
    sub = set(subtree('upperarm.' + s))
    upper = {'upperarm.' + s, 'upperarm_half.' + s, 'forearm_half.' + s}
    mv = [i for i in range(len(W)) if sum(w for k, w in W[i].items() if k in sub) >= 0.9]
    up = [i for i in mv if dom[i] in upper]
    lo = [i for i in mv if dom[i] not in upper]
    # the far part only for the torso test (near the shoulder the arm touches the torso by construction)
    SIDES[s] = (list(rng.choice(up, min(len(up), 400), replace=False)) if up else [],
                list(rng.choice(lo, min(len(lo), 1500), replace=False)) if lo else [])

def deformed():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = me.evaluated_get(dg); m = ev.to_mesh()
    co = [me.matrix_world @ v.co for v in m.vertices]
    ev.to_mesh_clear(); return co

def pen(co, idxs, bvh):
    worst = 0.0; n = 0
    for i in idxs:
        hit = bvh.find_nearest(co[i], 0.15)
        if hit[0] is None: continue
        dv = co[i] - hit[0]; sd = dv.dot(hit[1])
        # inside only when the nearest point is on a face interior (the offset runs along the normal): points
        # beside an open rim (the neck seam) are not inside
        if -0.15 < sd < -0.002 and dv.normalized().dot(hit[1]) < -0.8:
            worst = max(worst, -sd); n += 1 if -sd > 0.01 else 0
    return worst, n

# vertices that already sit inside the head/torso in the bind pose (sleeves and cloak layers over the shoulder) are
# not arm penetration: leave them out
def _rest_inside():
    arm.animation_data.action = None
    for pb in P: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    co = deformed()
    bh = BVHTree.FromPolygons(co, htris) if htris else None; bt = BVHTree.FromPolygons(co, ttris) if ttris else None
    bad = set()
    for s in ('R', 'L'):
        for i in SIDES[s][0] + SIDES[s][1]:
            for b in (bh, bt):
                if b is None: continue
                hit = b.find_nearest(co[i], 0.15)
                if hit[0] is None: continue
                dv = co[i] - hit[0]
                if dv.dot(hit[1]) < -0.002: bad.add(i)
    for s in ('R', 'L'):
        SIDES[s] = ([i for i in SIDES[s][0] if i not in bad], [i for i in SIDES[s][1] if i not in bad])
    print('bind-pose overlaps left out:', len(bad))
_rest_inside()

def twist(q):
    sw, tw = q.to_swing_twist('Y'); return math.degrees(tw), math.degrees(sw.angle)

chest_rest = B['chest'].matrix_local.copy()
res = {'mesh': me.name, 'clips': {}}
for act in bpy.data.actions:
    arm.animation_data.action = act
    f0, f1 = [int(x) for x in act.frame_range]
    rows = []
    for f in list(range(f0, f1 + 1, STEP)) + ([f1] if (f1 - f0) % STEP else []):
        sc.frame_set(f)
        co = deformed()
        bh = BVHTree.FromPolygons(co, htris) if htris else None
        bt = BVHTree.FromPolygons(co, ttris) if ttris else None
        cm = P['chest'].matrix @ chest_rest.inverted()
        row = {'f': f}
        for s in ('R', 'L'):
            up, lo = SIDES[s]
            ph = pen(co, lo, bh)[0] if bh else 0   # forearm/hand/weapon (shoulder skin under hair and headdresses is not counted)
            ptor = pen(co, lo, bt)[0] if bt else 0
            ut, _ = twist(P['upperarm.' + s].rotation_quaternion)
            ft, el = twist(P['forearm.' + s].rotation_quaternion)
            if ('forearm_twist.' + s) in P: ft += twist(P['forearm_twist.' + s].rotation_quaternion)[0]
            wr = math.degrees(P['hand.' + s].rotation_quaternion.angle)
            w = cm.inverted() @ P['hand.' + s].head
            hm = cm.inverted().to_3x3() @ P['hand.' + s].matrix.to_3x3() @ B['hand.' + s].matrix_local.to_3x3().inverted()
            hd = (hm @ B['hand.' + s].matrix_local.to_3x3().col[1]).normalized()
            ep = cm.inverted() @ P['forearm.' + s].head
            row[s] = dict(head=round(ph * 100, 1), torso=round(ptor * 100, 1), roll=round(ut), ftw=round(ft), wrist=round(wr), elbow=round(el),
                          wpos=[round(x, 3) for x in w], hdir=[round(x, 3) for x in hd], epos=[round(x, 3) for x in ep], hm=[[round(x, 4) for x in r_] for r_ in hm])
        rows.append(row)
    res['clips'][act.name] = rows
    def mx(k, s): return max(r[s][k] for r in rows)
    print(act.name, f0, f1, ' '.join('%s: head %.1fcm torso %.1fcm roll %d..%d ftw %d..%d wrist<=%d' % (
        s, mx('head', s), mx('torso', s), min(r[s]['roll'] for r in rows), mx('roll', s), min(r[s]['ftw'] for r in rows), mx('ftw', s), mx('wrist', s)) for s in ('R', 'L')), flush=True)
json.dump(res, open(OUT, 'w'))
