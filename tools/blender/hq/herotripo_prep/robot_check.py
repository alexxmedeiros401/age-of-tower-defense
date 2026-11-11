"""Rigid-robot check of a rigged model over its clips (Blender, light: no renders).

    python3 robot_check.py -- --hero ID --model OUT/ID.glb|OUT/ID_hq.blend [--step 1] [--clips Walk] [--island 40]
                              [--gap 0.004] [--json OUT/robot_check.json] [--top 10]

For a machine rigged with `hard_weights` + `hard_split: "faces"` every face should ride one bone. Reports:
- MIXED faces: faces whose corners do not all ride the same single bone 100% (they stretch when the parts turn),
  grouped by bone pair, with the worst stretch over the clips (edge length / rest length);
- SHARDS: patches of one bone (faces joined by shared rest positions) of fewer than `--island` faces, with the
  bone(s) around them and how far they drift from their neighbours over the clips (a shard that rides the wrong bone
  flies off its part);
- GAPS: rest-coincident vertices on different bones (the part lines of a split mesh), per bone pair: the widest they
  open over the clips, the frame and where (a joint that cracks open);
- LOOSE pieces (connected by rest position) smaller than `--island` faces.
Prints "ROBOT OK" when no face stretches and no shard drifts more than `--gap`; joint gaps are listed for review
(rigid parts always open a little at their joints: compare the shipped and the fixed model).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import common as C

HID = C.arg("--hero")
MODEL = C.arg("--model")
STEP = int(C.arg("--step", "1"))
ISL = int(C.arg("--island", "40"))
GAP = float(C.arg("--gap", "0.004"))
TOP = int(C.arg("--top", "10"))
ONLY = C.arg("--clips")
CFG = C.load_cfg(HID)
import old as oldmod
arm = oldmod.open_old(MODEL, CFG.get("armature") or "CavemanRig")
info = json.load(open(os.path.join(C.work_dir(HID), "old.json")))
ob = bpy.data.objects[info["mesh"]]
me = ob.data
nv, nf = len(me.vertices), len(me.polygons)
ls = np.zeros(nf, np.int64); lt = np.zeros(nf, np.int64)
me.polygons.foreach_get("loop_start", ls); me.polygons.foreach_get("loop_total", lt)
li = np.zeros(len(me.loops), np.int64); me.loops.foreach_get("vertex_index", li)
assert (lt == 3).all() or True
FV = [li[a:a + n] for a, n in zip(ls, lt)]
gn = [g.name for g in ob.vertex_groups]
Wd = np.zeros((nv, len(gn)), np.float32)
for v in me.vertices:
    for g in v.groups:
        Wd[v.index, g.group] = g.weight
dom = Wd.argmax(1)
pure = Wd.max(1) > 0.999
sc = bpy.context.scene
arm.animation_data_create()


def rest():
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    sc.frame_set(0)


def coords():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    X = np.zeros(len(m.vertices) * 3); m.vertices.foreach_get("co", X)
    ev.to_mesh_clear()
    M = np.array(ob.matrix_world)
    return X.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]


rest()
X0 = coords()
# weld by rest position
q = np.round(X0 / 1e-4).astype(np.int64)
_, wid = np.unique(q, axis=0, return_inverse=True)
wid = wid.ravel()
# hard_caps faces (all corners on one UV point) close the parts' rims: not part of the shard / patch analysis
uvd = np.zeros(len(me.loops) * 2); me.uv_layers.active.data.foreach_get("uv", uvd); uvd = uvd.reshape(-1, 2)
capf = np.array([np.ptp(uvd[a:a + n], 0).max() < 1e-7 for a, n in zip(ls, lt)])
# face bone (all corners pure on one bone) or -1 (mixed)
fb = np.array([dom[f[0]] if (pure[f].all() and (dom[f] == dom[f[0]]).all()) else -1 for f in FV])
mixed = np.nonzero(fb < 0)[0]
# face adjacency through welded edges
ek = {}
rows, cols = [], []
for i, f in enumerate(FV):
    w = wid[f]
    for a, b in zip(w, np.roll(w, -1)):
        k = (min(a, b), max(a, b))
        j = ek.get(k)
        if j is None:
            ek[k] = i
        else:
            rows.append(i); cols.append(j)
rows, cols = np.array(rows), np.array(cols)
A = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(nf, nf))
ncomp, comp = connected_components(A, directed=False)
same = (fb[rows] == fb[cols]) & ~capf[rows] & ~capf[cols]
As = coo_matrix((np.ones(same.sum()), (rows[same], cols[same])), shape=(nf, nf))
_, patch = connected_components(As, directed=False)
psz = np.bincount(patch)
small = [p for p in np.nonzero(psz < ISL)[0]]
# neighbours of each small patch: bones of faces across its border
shards = []
for p in small:
    fs = np.nonzero(patch == p)[0]
    if fb[fs[0]] < 0 or capf[fs].all():
        continue
    m = (patch[rows] == p) ^ (patch[cols] == p)
    other = np.r_[cols[m & (patch[rows] == p)], rows[m & (patch[cols] == p)]]
    nb = np.where(capf[other], -1, fb[other])
    nb = nb[(nb >= 0) & (nb != fb[fs[0]])]
    if not len(nb):
        continue
    nbb = np.bincount(nb).argmax()
    vs = np.unique(np.concatenate([FV[i] for i in fs]))
    shards.append(dict(faces=len(fs), bone=gn[fb[fs[0]]], around=gn[nbb], verts=vs, nbbone=nbb,
                       at=[round(float(v), 3) for v in X0[vs].mean(0)]))
csz = np.bincount(comp)
loose = [dict(faces=int(csz[c]), at=[round(float(v), 3) for v in X0[np.unique(np.concatenate([FV[i] for i in np.nonzero(comp == c)[0]]))].mean(0)])
         for c in np.nonzero(csz < ISL)[0]]
# coincident pairs on different bones (part lines)
pairs = np.array(sorted(cKDTree(X0).query_pairs(1e-4)), np.int64).reshape(-1, 2)
pairs = pairs[dom[pairs[:, 0]] != dom[pairs[:, 1]]]
pk = ["|".join(sorted((gn[dom[a]], gn[dom[b]]))) for a, b in pairs]
acts = {a.name.split("|")[-1]: a for a in bpy.data.actions}
clips = [c for c in (ONLY.split(",") if ONLY else (CFG.get("clips") or sorted(acts))) if c in acts]
E = np.array([(f[i], f[(i + 1) % len(f)]) for k in mixed for f in [FV[k]] for i in range(len(f))], np.int64).reshape(-1, 2)
L0 = np.linalg.norm(X0[E[:, 0]] - X0[E[:, 1]], axis=1) if len(E) else np.zeros(0)
# a shard's drift: its verts moved rigidly with the neighbour bone vs where they are
bone_names = gn
gaps, mix_worst, shard_drift = {}, 0.0, np.zeros(len(shards))
stretched = np.zeros(len(E), bool)
grow = np.zeros(len(E))
Ef = np.repeat(mixed, [len(FV[k]) for k in mixed]) if len(mixed) else np.zeros(0, np.int64)
for c in clips:
    a = acts[c]
    arm.animation_data.action = a
    try:
        arm.animation_data.action_slot = a.slots[0]
    except Exception:
        pass
    f0, f1 = int(a.frame_range[0]), int(a.frame_range[1])
    for f in range(f0, f1 + 1, STEP):
        sc.frame_set(f)
        X = coords()
        if len(E):
            Lx = np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1)
            r = Lx / np.maximum(L0, 1e-9)
            st = (r > 1.5) & (Lx - L0 > 0.005)
            stretched[st] = True
            grow = np.maximum(grow, Lx - L0)
            mix_worst = max(mix_worst, float(r[st].max()) if st.any() else 0.0)
        if len(pairs):
            d = np.linalg.norm(X[pairs[:, 0]] - X[pairs[:, 1]], axis=1)
            for k in set(pk):
                sel = np.array([x == k for x in pk])
                j = int(np.argmax(np.where(sel, d, -1)))
                g = gaps.setdefault(k, dict(gap=0.0, clip=None, frame=None, at=None, n=int(sel.sum())))
                if d[j] > g["gap"]:
                    g.update(gap=float(d[j]), clip=c, frame=f, at=[round(float(v), 3) for v in X[pairs[j, 0]]])
        for i, s in enumerate(shards):
            pb = arm.pose.bones[bone_names[s["nbbone"]]]
            AW = np.array(arm.matrix_world)
            M = AW @ np.array(pb.matrix) @ np.linalg.inv(np.array(pb.bone.matrix_local)) @ np.linalg.inv(AW)
            Y = X0[s["verts"]] @ M[:3, :3].T + M[:3, 3]
            shard_drift[i] = max(shard_drift[i], float(np.linalg.norm(X[s["verts"]] - Y, axis=1).max()))
for s, dr in zip(shards, shard_drift):
    s["drift"] = round(float(dr), 4)
    del s["verts"], s["nbbone"]
bad_sh = [s for s in shards if s["drift"] > GAP]
print("[robot] %s: %d faces (%d joint caps), %d verts; %d pieces; clips %s" % (os.path.basename(MODEL), nf, capf.sum(), nv, ncomp, clips))
smix = np.unique(Ef[stretched]) if len(E) else np.zeros(0, np.int64)
print("[robot] mixed faces: %d, %d of them stretched (an edge > x1.5 and > 5 mm longer), worst x%.2f, +%.0f mm" % (
    len(mixed), len(smix), mix_worst, (grow.max() if len(grow) else 0) * 1000))
if len(mixed):
    mk = {}
    gf = {}
    for e_, k in enumerate(Ef):
        gf[k] = max(gf.get(k, 0.0), grow[e_])
    for k in mixed:
        b = "|".join(sorted({gn[dom[v]] for v in FV[k]}))
        n_, s_, g_ = mk.get(b, (0, 0, 0.0))
        mk[b] = (n_ + 1, s_ + int(k in set(smix.tolist())), max(g_, gf.get(k, 0.0)))
    for k, v in sorted(mk.items(), key=lambda kv: -kv[1][1])[:TOP]:
        print("    %-30s %4d faces, %4d stretched, +%.0f mm" % (k, v[0], v[1], v[2] * 1000))
print("[robot] shards (< %d faces, another bone around): %d, %d drift > %.0f mm" % (ISL, len(shards), len(bad_sh), GAP * 1000))
for s in sorted(shards, key=lambda s: -s["drift"])[:TOP]:
    print("    %3d faces on %-12s in %-12s drift %5.1f mm at %s" % (s["faces"], s["bone"], s["around"], s["drift"] * 1000, s["at"]))
print("[robot] loose pieces < %d faces: %d %s" % (ISL, len(loose), [l["faces"] for l in loose][:20]))
print("[robot] joint gaps (rest-coincident verts on two bones), widest over the clips:")
for k, g in sorted(gaps.items(), key=lambda kv: -kv[1]["gap"])[:TOP]:
    print("    %-30s %4d pairs  %5.1f mm  %s f%s at %s" % (k, g["n"], g["gap"] * 1000, g["clip"], g["frame"], g["at"]))
ok = not len(smix) and not bad_sh
print("ROBOT OK" if ok else "ROBOT %d stretched faces, %d drifting shards" % (len(smix), len(bad_sh)))
J = C.arg("--json")
if J:
    json.dump(dict(model=MODEL, mixed=int(len(mixed)), stretched=int(len(smix)), mix_worst=mix_worst, shards=shards, loose=loose, gaps=gaps), open(J, "w"), indent=1)
