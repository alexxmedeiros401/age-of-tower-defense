"""Optional step after fit.py (Blender, light): props taken from the OLD hero's mesh instead of the Tripo model.

    python3 oldprop.py -- --hero wren

For each prop with "source": "old" in the config (e.g. Wren's arrow: the Tripo model has none in her hand, only a
quiver of fletchings): the old mesh's faces that ride the prop's bone (all three vertices > 0.5 on it), coloured per
vertex from the old hero albedo / ORM at their UVs, posed with the fitted pose and put into the Tripo model's frame,
are appended to patches.pkl as a patch of that prop (cut.py leaves the prop's label empty). The bake then decimates
and bakes it like any prop (base colour and roughness-metal from those vertex colours, normal and AO from the shape),
and "place": "fit" in the rig puts it back exactly where the old prop was, on its bone. Run it after every patches.py
(which rewrites patches.pkl) and after fit.py.
"""
import sys, os, json, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from scipy.spatial.transform import Rotation as Rot
import common as C
import old as oldmod


def fitted_skin(W, bone):
    o = np.load(os.path.join(W, "old.npz"))
    fit = json.load(open(os.path.join(W, "fit.json")))
    bn = [str(b) for b in o["bn"]]
    rest = {n: m for n, m in zip(bn, o["bm"])}
    par = {n: (bn[p] if p >= 0 else None) for n, p in zip(bn, o["bp"])}
    posed = {}
    def pz(n):
        if n in posed:
            return posed[n]
        R = np.eye(4)
        if n in fit["rotvec"]:
            R[:3, :3] = Rot.from_rotvec(fit["rotvec"][n]).as_matrix()
        p = par[n]
        posed[n] = rest[n] @ R if p is None else pz(p) @ np.linalg.inv(rest[p]) @ rest[n] @ R
        return posed[n]
    return pz(bone) @ np.linalg.inv(rest[bone]), fit["xf"]


def image_pixels(im):
    im.reload() if not im.has_data else None
    w, h = im.size
    px = np.array(im.pixels[:], np.float32).reshape(h, w, im.channels)[..., :3]
    if im.colorspace_settings.name == "sRGB" and im.is_float:
        px = np.where(px <= 0.0031308, px * 12.92, 1.055 * np.power(np.clip(px, 0, None), 1 / 2.4) - 0.055)
    return px


def sample(px, uv):
    h, w = px.shape[:2]
    x = np.clip((uv[:, 0] * w).astype(int), 0, w - 1)
    y = np.clip((uv[:, 1] * h).astype(int), 0, h - 1)     # (Blender's pixels run from the bottom row up)
    return px[y, x]


def main():
    hid = C.arg("--hero")
    cfg = C.load_cfg(hid)
    W = C.work_dir(hid)
    props = [p for p in cfg["props"] if p.get("source") == "old"]
    if not props:
        print("[oldprop] no props with source old")
        return
    info = json.load(open(os.path.join(W, "old.json")))
    arm = oldmod.open_old(cfg["old"])
    ob = bpy.data.objects[info["mesh"]]
    me = ob.data
    to_arm = np.array(arm.matrix_world.inverted() @ ob.matrix_world)
    mat = me.materials[0]
    ims = [n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image]
    def find(key):
        for im in ims:
            if key in im.name.lower():
                return im
        return None
    alb = find("albedo") or find("base") or (ims[0] if ims else None)
    orm = find("orm")
    pa = image_pixels(alb)
    po = image_pixels(orm) if orm else None
    me.calc_loop_triangles()
    uvl = me.uv_layers.active.data
    pk = os.path.join(W, "patches.pkl")
    out = pickle.load(open(pk, "rb"))
    for p in props:
        bone = p.get("bone") or p["name"]
        g = ob.vertex_groups[bone].index
        wv = np.zeros(len(me.vertices))
        for v in me.vertices:
            for gg in v.groups:
                if gg.group == g:
                    wv[v.index] = gg.weight
        tris = [t for t in me.loop_triangles if all(wv[i] > 0.5 for i in t.vertices)]
        vs = sorted({i for t in tris for i in t.vertices})
        idx = {v: k for k, v in enumerate(vs)}
        X = np.array([(to_arm @ np.r_[me.vertices[v].co, 1.0])[:3] for v in vs])
        col = np.zeros((len(vs), 3))
        rmv = np.tile([1.0, 0.6, 0.0], (len(vs), 1))
        cnt = np.zeros(len(vs))
        rsum = np.zeros((len(vs), 3))
        for t in tris:
            for li, vi in zip(t.loops, t.vertices):
                uv = np.array(uvl[li].uv)[None]
                col[idx[vi]] += sample(pa, uv)[0]
                if po is not None:
                    rsum[idx[vi]] += sample(po, uv)[0]
                cnt[idx[vi]] += 1
        col /= np.maximum(cnt, 1)[:, None]
        if po is not None:
            rmv = rsum / np.maximum(cnt, 1)[:, None]
            rmv[:, 0] = 1.0
        T = np.array([[idx[i] for i in t.vertices] for t in tris])
        S, xf = fitted_skin(W, bone)
        Xf = (np.c_[X, np.ones(len(X))] @ S.T)[:, :3]
        raw = C.from_game(Xf, xf)
        out.setdefault(p["name"], [])
        out[p["name"]] = [r for r in out[p["name"]] if len(r[0]) > 0]       # (a re-run replaces its own entry)
        out[p["name"]].append((np.zeros(0, np.int64), raw, T, np.clip(col, 0, 1), np.clip(rmv, 0, 1)))
        print("[oldprop] %s: %d old faces on %s, %d verts, colour %s, rest bbox %s .. %s" % (
            p["name"], len(T), bone, len(vs), (col.mean(0) * 255).round(), X.min(0).round(3), X.max(0).round(3)))
    pickle.dump(out, open(pk, "wb"))


main()
