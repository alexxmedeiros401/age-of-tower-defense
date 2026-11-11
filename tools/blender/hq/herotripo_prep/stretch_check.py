"""Stretched-edge and torn-seam check of a rigged hero over its clips (Blender, light: no renders).

    python3 stretch_check.py -- --hero ID --model OUT/ID.glb|OUT/ID_hq.blend [--step 1] [--ratio 2.0] [--abs 0.03]
                                [--gap 0.01] [--clips Idle,Attack] [--json OUT/stretch.json] [--top 12]

For every frame of every clip (each `--step` frame), the character mesh (old.json's mesh name, else the skinned mesh
with most faces) is evaluated and each edge's world length is compared with the rest pose: an edge is STRETCHED when
it is more than `--ratio` times its rest length AND more than `--abs` (m) longer. Vertices that share a rest position
(split seams, a prop's bridge against its fist) are TORN when they drift more than `--gap` apart. The stretched edges
are grouped by the dominant bones of their two ends (e.g. "forearm.R|hand.R": an elbow or wrist) and printed per
clip: how many edges, the worst ratio, the frame it happens in and where (world xyz of the worst edge's middle).
Prints a verdict line per clip and "STRETCH OK" or "STRETCH N issues" at the end; --json writes it all.
Run it on the shipped GLB and on the fixed one to compare (the same frames, the same numbers).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from scipy.spatial import cKDTree
import common as C

HID = C.arg("--hero")
MODEL = C.arg("--model")
STEP = int(C.arg("--step", "1"))
RATIO = float(C.arg("--ratio", "2.0"))
ABS = float(C.arg("--abs", "0.03"))
GAP = float(C.arg("--gap", "0.01"))
TOP = int(C.arg("--top", "12"))
ONLY = C.arg("--clips")
CFG = C.load_cfg(HID) if HID else dict(C.DEFAULTS)
ARMN = CFG.get("armature") or "CavemanRig"

import old as oldmod
try:
    arm = oldmod.open_old(MODEL, ARMN)
except KeyError:                                   # (no hero id given for a robot: take its armature)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
info_p = os.path.join(C.work_dir(HID), "old.json") if HID else None
mesh_name = None
if info_p and os.path.exists(info_p):
    mesh_name = json.load(open(info_p)).get("mesh")
if mesh_name and mesh_name in bpy.data.objects:
    ob = bpy.data.objects[mesh_name]
else:
    sk = [o for o in bpy.data.objects if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)]
    ob = max(sk, key=lambda o: len(o.data.polygons))
me = ob.data
nv = len(me.vertices)
E = np.zeros(len(me.edges) * 2, np.int64)
me.edges.foreach_get("vertices", E)
E = E.reshape(-1, 2)
gn = [g.name for g in ob.vertex_groups]
Wd = np.zeros((nv, max(len(gn), 1)), np.float32)
for v in me.vertices:
    for g in v.groups:
        Wd[v.index, g.group] = g.weight
dom = np.array(gn)[Wd.argmax(1)] if gn else np.array(["?"] * nv)

sc = bpy.context.scene
arm.animation_data_create()
me.calc_loop_triangles()
TRI = np.array([t.vertices[:] for t in me.loop_triangles], np.int64)
Wn = Wd / np.maximum(Wd.sum(1, keepdims=True), 1e-9)
WF = Wn[TRI].mean(1)                                 # (a face's weights: its corners' mean)
gb = [arm.pose.bones.get(n) for n in gn]
FLIP = float(C.arg("--flip", "-0.2"))


def tri_normals(X):
    n = np.cross(X[TRI[:, 1]] - X[TRI[:, 0]], X[TRI[:, 2]] - X[TRI[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]


def bone_rots():
    """each vertex group's bone's turn from rest (world), identity for a group with no bone"""
    Mw = np.array(arm.matrix_world)[:3, :3]
    R = np.zeros((len(gn), 3, 3))
    for j, pb in enumerate(gb):
        R[j] = np.eye(3) if pb is None else Mw @ np.array(pb.matrix)[:3, :3] @ np.linalg.inv(np.array(pb.bone.matrix_local)[:3, :3]) @ np.linalg.inv(Mw)
    return R


def rest():
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    sc.frame_set(0)


def coords():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    X = np.zeros(len(m.vertices) * 3)
    m.vertices.foreach_get("co", X)
    ev.to_mesh_clear()
    X = X.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    return X @ M[:3, :3].T + M[:3, 3]


rest()
X0 = coords()
L0 = np.linalg.norm(X0[E[:, 0]] - X0[E[:, 1]], axis=1)
N0 = tri_normals(X0)
A0 = 0.5 * np.linalg.norm(np.cross(X0[TRI[:, 1]] - X0[TRI[:, 0]], X0[TRI[:, 2]] - X0[TRI[:, 0]]), axis=1)
fdom = np.array(gn)[WF.argmax(1)] if gn else np.array(["?"] * len(TRI))
# coincident rest vertices (pairs within 0.1 mm that are not one vertex)
pairs = np.array(sorted(cKDTree(X0).query_pairs(1e-4)), np.int64).reshape(-1, 2)
acts = {a.name.split("|")[-1]: a for a in bpy.data.actions}
clips = [c for c in (ONLY.split(",") if ONLY else (CFG.get("clips") or sorted(acts))) if c in acts]
report, issues = {}, 0
for c in clips:
    a = acts[c]
    arm.animation_data.action = a
    try:
        arm.animation_data.action_slot = a.slots[0]
    except Exception:
        pass
    f0, f1 = int(a.frame_range[0]), int(a.frame_range[1])
    groups, worst_gap, per_frame = {}, (0.0, None, None), {}
    flips = {}
    for f in range(f0, f1 + 1, STEP):
        sc.frame_set(f)
        X = coords()
        L = np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1)
        bad = np.nonzero((L > RATIO * L0) & (L - L0 > ABS))[0]
        per_frame[f] = int(len(bad))
        # FLIPPED faces: the posed normal against the rest normal turned by the face's blended bone turn (a limb that
        # collapses through itself when the hand twists: the faces turn inside out without stretching)
        Rf = np.einsum("fj,jab->fab", WF, bone_rots())
        ex = np.einsum("fab,fb->fa", Rf, N0)
        ex /= np.maximum(np.linalg.norm(ex, axis=1), 1e-12)[:, None]
        fl = np.nonzero(((ex * tri_normals(X)).sum(1) < FLIP) & (A0 > 2e-5))[0]
        for b_ in np.unique(fdom[fl]):
            k_ = fl[fdom[fl] == b_]
            g = flips.setdefault(b_, dict(faces=set(), area=0.0, frame=f, at=None))
            g["faces"].update(k_.tolist())
            ar = float(A0[k_].sum())
            if ar > g["area"]:
                g.update(area=ar, frame=f, at=[round(float(v), 3) for v in X[TRI[k_]].reshape(-1, 3).mean(0)])
        per_frame[f] += int(len(fl))
        for i in bad:
            k = "|".join(sorted({dom[E[i, 0]], dom[E[i, 1]]}))
            g = groups.setdefault(k, dict(edges=set(), worst=0.0, frame=f, at=None, grow=0.0))
            g["edges"].add(int(i))
            r = L[i] / max(L0[i], 1e-9)
            if r > g["worst"]:
                g.update(worst=float(r), frame=f, at=[round(float(v), 3) for v in (X[E[i, 0]] + X[E[i, 1]]) / 2],
                         grow=float(L[i] - L0[i]))
        if len(pairs):
            d = np.linalg.norm(X[pairs[:, 0]] - X[pairs[:, 1]], axis=1)
            j = int(d.argmax())
            if d[j] > worst_gap[0]:
                worst_gap = (float(d[j]), f, [round(float(v), 3) for v in X[pairs[j, 0]]], dom[pairs[j, 0]], dom[pairs[j, 1]])
    out = sorted(({"bones": k, "edges": len(g["edges"]), "worst_ratio": round(g["worst"], 2), "grow_m": round(g["grow"], 3),
                   "frame": g["frame"], "at": g["at"]} for k, g in groups.items()), key=lambda d: -d["edges"])
    n_e = sum(d["edges"] for d in out)
    fo = sorted(({"bone": k, "faces": len(g["faces"]), "area_cm2": round(g["area"] * 1e4, 1), "frame": g["frame"], "at": g["at"]}
                 for k, g in flips.items()), key=lambda d: -d["area_cm2"])
    fo = [d for d in fo if d["area_cm2"] >= float(C.arg("--flip_area", "4"))]     # (a few slivers: noise)
    n_f = sum(d["faces"] for d in fo)
    torn = worst_gap[0] > GAP
    issues += (n_e > 0) + torn + (n_f > 0)
    report[c] = dict(frames=[f0, f1], stretched=out, stretched_edges=n_e, flipped=fo, flipped_faces=n_f,
                     worst_frames=sorted(per_frame, key=lambda f: -per_frame[f])[:5] if n_e else [],
                     gap=dict(dist=round(worst_gap[0], 4), frame=worst_gap[1], at=worst_gap[2] if worst_gap[1] is not None else None,
                              bones=list(worst_gap[3:5]) if worst_gap[1] is not None else None))
    print("[stretch] %-8s frames %d-%d: %d stretched edges%s; seam gap max %.1f mm%s" % (
        c, f0, f1, n_e, (" (worst frames %s)" % report[c]["worst_frames"]) if n_e else "", worst_gap[0] * 1000,
        (" at f%d %s %s" % (worst_gap[1], worst_gap[2], "/".join(worst_gap[3:5]))) if torn else ""))
    for d in fo[:TOP]:
        print("    FLIPPED %-20s %4d faces  %.0f cm2 at once, f%d at %s" % (d["bone"], d["faces"], d["area_cm2"], d["frame"], d["at"]))
    for d in out[:TOP]:
        print("    %-28s %4d edges  worst x%.1f (+%.0f mm) f%d at %s" % (d["bones"], d["edges"], d["worst_ratio"],
                                                                         d["grow_m"] * 1000, d["frame"], d["at"]))
print("[stretch] %s: %d edges, %d verts, %d coincident pairs; thresholds x%.1f and +%.0f mm, gap %.0f mm" % (
    os.path.basename(MODEL), len(E), nv, len(pairs), RATIO, ABS * 1000, GAP * 1000))
print("STRETCH OK" if not issues else "STRETCH %d issues" % issues)
J = C.arg("--json")
if J:
    json.dump(dict(model=MODEL, ratio=RATIO, abs=ABS, gap=GAP, clips=report), open(J, "w"), indent=1)
