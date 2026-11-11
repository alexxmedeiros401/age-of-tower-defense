# Re-pose an arm in given clips so it clears the head / body of a (Tripo) character.
# usage: python3 armclear.py IN.glb OUT.glb CFG.json
# CFG: {"mesh": "Caveman", "arms": [{"root": "upperarm.R", "clips": ["Throw","Whirl"], "loop": ["Whirl"],
#        "head": ["head","neck"], "torso": ["chest","spine","root"], "margin": 0.015,
#        "max_deg": 50, "lam": 0.004}], "halves": {"upperarm_half.R": "upperarm.R", ...}}
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

IN, OUT, CFG = sys.argv[1:4]
cfg = json.load(open(CFG))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
sc = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
me_ob = bpy.data.objects[cfg["mesh"]]
P = arm.pose.bones
mw = arm.matrix_world.copy()

def subtree(name):
    out = [name]
    for c in arm.data.bones[name].children:
        out += subtree(c.name)
    return out

# dominant bone per vertex
gname = {g.index: g.name for g in me_ob.vertex_groups}
nv = len(me_ob.data.vertices)
W = {}
dom = []
for v in me_ob.data.vertices:
    d = {}
    for g in v.groups:
        d[gname[g.group]] = d.get(gname[g.group], 0) + g.weight
    s = sum(d.values()) or 1
    d = {k: w / s for k, w in d.items()}
    W[v.index] = d
    dom.append(max(d, key=d.get) if d else "")
tris = [tuple(p.vertices) for p in me_ob.data.polygons]

def deformed():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = me_ob.evaluated_get(dg)
    m = ev.to_mesh()
    co = np.array([ (me_ob.matrix_world @ v.co)[:] for v in m.vertices ])
    ev.to_mesh_clear()
    return co

def rot(axis_angles):
    # world rotation: about X then Y then Z (degrees)
    ax, ay, az = [math.radians(a) for a in axis_angles]
    return (Matrix.Rotation(az, 3, 'Z') @ Matrix.Rotation(ay, 3, 'Y') @ Matrix.Rotation(ax, 3, 'X'))

report = {}
for A in cfg["arms"]:
    sub = set(subtree(A["root"]))
    upper_only = set(A.get("upper", [A["root"]]))
    movers = [i for i in range(nv) if sum(w for k, w in W[i].items() if k in sub) >= 0.9]
    mv_upper = [i for i in movers if dom[i] in upper_only]
    mv_lower = [i for i in movers if dom[i] not in upper_only]
    headset = set(A["head"]); torsoset = set(A["torso"])
    htris = [t for t in tris if all(dom[i] in headset for i in t)]
    ttris = [t for t in tris if all(dom[i] in torsoset for i in t)]
    rng = np.random.default_rng(0)
    samp_u = list(rng.choice(mv_upper, min(len(mv_upper), 500), replace=False)) if mv_upper else []
    samp_l = list(rng.choice(mv_lower, min(len(mv_lower), 1200), replace=False)) if mv_lower else []
    margin = A.get("margin", 0.015); hmargin = A.get("head_margin", margin); lam = A.get("lam", 0.004); mx = A.get("max_deg", 50)
    print("arm", A["root"], "movers", len(movers), "upper", len(mv_upper), "lower", len(mv_lower), "head tris", len(htris), "torso tris", len(ttris))

    def cost_of(co, S, R, bvh_h, bvh_t):
        tot = 0.0; worst = 0.0
        for idxs, bvhs in ((samp_u, (bvh_h,)), (samp_l, (bvh_h, bvh_t))):
            for i in idxs:
                p = Vector(co[i]) - S
                q = R @ p + S
                for b in bvhs:
                    hit = b.find_nearest(q, 0.12)
                    if hit[0] is None: continue
                    loc, n, _, dist = hit
                    sd = (q - loc).dot(n)
                    mg = hmargin if b is bvh_h else margin
                    if sd < mg:
                        pen = mg - sd if sd > -0.12 else 0
                        tot += pen; worst = max(worst, pen)
        return tot, worst

    for clip in A["clips"]:
        act = bpy.data.actions[clip]
        arm.animation_data.action = act
        f0, f1 = [int(x) for x in act.frame_range]
        frames = list(range(f0, f1 + 1))
        sol = {}
        prev = (0, 0, 0)
        lam2 = A.get('lam2', 0.01)
        for f in frames:
            sc.frame_set(f)
            co = deformed()
            S = mw @ P[A["root"]].head
            bvh_h = BVHTree.FromPolygons([Vector(c) for c in co], htris)
            bvh_t = BVHTree.FromPolygons([Vector(c) for c in co], ttris)
            base, bw = cost_of(co, S, Matrix.Identity(3), bvh_h, bvh_t)
            best = (base + lam2 * math.sqrt(sum(b * b for b in prev)), (0, 0, 0), bw)
            if base > 0:
                # coarse grid then refine
                step = 10
                grid = [prev] + [(x, y, z) for x in range(-mx, mx + 1, step) for y in range(-mx, mx + 1, step) for z in (-20, 0, 20)]
                for g in grid:
                    c, w = cost_of(co, S, rot(g), bvh_h, bvh_t)
                    c += lam * math.sqrt(sum(a * a for a in g)) + lam2 * math.sqrt(sum((a - b) ** 2 for a, b in zip(g, prev)))
                    if c < best[0]: best = (c, g, w)
                for step in (5, 2.5):
                    cx = best[1]
                    for dx in (-step, 0, step):
                        for dy in (-step, 0, step):
                            for dz in (-step, 0, step):
                                g = (cx[0] + dx, cx[1] + dy, cx[2] + dz)
                                c, w = cost_of(co, S, rot(g), bvh_h, bvh_t)
                                c += lam * math.sqrt(sum(a * a for a in g)) + lam2 * math.sqrt(sum((a - b) ** 2 for a, b in zip(g, prev)))
                                if c < best[0]: best = (c, g, w)
            sol[f] = best[1]; prev = best[1]
            print(clip, f, "pen %.3f worst %.3f -> %s worst %.3f" % (base, bw, best[1], best[2]), flush=True)
        # smooth rotation vectors
        rv = np.array([ (rot(sol[f]).to_quaternion().to_axis_angle()[0] * rot(sol[f]).to_quaternion().to_axis_angle()[1])[:] for f in frames ])
        n = len(frames); sig = A.get("smooth", 1.5)
        ker = np.exp(-0.5 * (np.arange(-4, 5) / sig) ** 2); ker /= ker.sum()
        loop = clip in A.get("loop", [])
        sm = np.zeros_like(rv)
        for k in range(n):
            acc = np.zeros(3)
            for j, wk in zip(range(-4, 5), ker):
                kk = (k + j) % (n - 1) if loop else min(max(k + j, 0), n - 1)
                acc += wk * rv[kk]
            sm[k] = acc
        # don't let smoothing reduce the needed correction too much: take the larger-magnitude of raw and smoothed per frame
        for k in range(n):
            if np.linalg.norm(rv[k]) > np.linalg.norm(sm[k]) * 1.3:
                sm[k] = sm[k] * 0.5 + rv[k] * 0.5
        report[clip + ":" + A["root"]] = {f: [round(x, 1) for x in sol[f]] for f in frames}
        # apply
        for k, f in enumerate(frames):
            sc.frame_set(f)
            v = Vector(sm[k]); ang = v.length
            if ang < 1e-5: continue
            Rw = Matrix.Rotation(ang, 4, v.normalized())
            S = mw @ P[A["root"]].head
            T = Matrix.Translation(S) @ Rw @ Matrix.Translation(-S)
            Mnew = mw.inverted() @ T @ mw @ P[A["root"]].matrix
            P[A["root"]].matrix = Mnew
            bpy.context.view_layer.update()
            pb = P[A["root"]]
            pb.keyframe_insert("rotation_quaternion", frame=f)
        # halves
        for h, src in cfg.get("halves", {}).items():
            for f in frames:
                sc.frame_set(f)
                P[h].rotation_quaternion = Quaternion().slerp(P[src].rotation_quaternion, 0.5)
                P[h].keyframe_insert("rotation_quaternion", frame=f)
json.dump(report, open(OUT + ".report.json", "w"), indent=0)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                          export_skins=True, export_tangents=True, export_apply=False, export_yup=True,
                          export_force_sampling=True, export_image_format="JPEG", export_jpeg_quality=93, export_materials="EXPORT")
print("wrote", OUT)
