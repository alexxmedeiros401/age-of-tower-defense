"""Shared bits of the generic Tripo-hero pipeline: the per-hero config, the work folder, the Tripo GLB reader and the
Tripo -> game transform. (No Blender here: the prep steps are numpy/scipy only.)

Config: ../herotripo_cfg/<id>.json (see README.md for every key and its default). Work folder: $HEROTRIPO_WORK/<id>/prep
(default /home/claude/work/herotripo/<id>/prep), or --work DIR.
"""
import json, os, struct, sys
import numpy as np

HQ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HQ)))
CFG_DIR = os.path.join(HQ, "herotripo_cfg")

DEFAULTS = {
    "old": None,                    # the old scene: a .blend (CavemanRig + mesh + clips) or a shipped .glb
    "mesh": None,                   # the old character mesh (default: the skinned mesh on CavemanRig with most faces)
    "material": None,               # its material (default: the mesh's first)
    "tripo": None,                  # the Tripo GLB (plain floats; see heroglb/tool/decode.mjs)
    "yaw": "auto",                  # degrees about +Z that turn the Tripo model to face -Y (auto: from the feet)
    "scale": "auto",                # Tripo -> game scale (auto: least-squares fit, started from the heights)
    "tris": 24500,                  # the character's triangle budget (body + props)
    "head_share": 0.25,             # the share of the body's triangles above the neck
    "face_boost": 2.2,              # texel density of the face (the rest of the head 1.5, props 1.2, feet 0.65)
    "tex": 2048,
    "props": [],                    # see README.md
    "armour": [],                   # see README.md
    "glows": {},                    # glow meshes on prop bones to rebuild: {"GlowOrb": {"prop": "orb", ...}}
    "body_patch": "rim",            # colour of the body's hole patches: rim (interpolated) | dark (the rim's dark half)
    "head_rigid_above": None,       # z (game, rest) above which the head bone takes all weight (default: chin level)
    "fit_reg": 0.05,
}


def arg(name, default=None, argv=None):
    a = argv if argv is not None else sys.argv
    if "--" in a:
        a = a[a.index("--") + 1:]
    return a[a.index(name) + 1] if name in a else default


def load_cfg(hid):
    p = os.path.join(CFG_DIR, hid + ".json")
    c = dict(DEFAULTS)
    c.update(json.load(open(p)))
    c["id"] = hid
    if c["tripo"] is None:
        c["tripo"] = "/home/claude/work/heroglb/plain/%s.glb" % hid
    if c["old"] is None:
        c["old"] = os.path.join(REPO, "assets", "heroes", hid + ".glb")
    for k in ("old", "tripo"):
        if not os.path.isabs(c[k]):
            c[k] = os.path.join(REPO, c[k])
    return c


def work_dir(hid, argv=None):
    w = arg("--work", None, argv) or os.path.join(os.environ.get("HEROTRIPO_WORK", "/home/claude/work/herotripo"), hid, "prep")
    os.makedirs(w, exist_ok=True)
    return w


def read_glb(path, tex_out=None):
    """The Tripo GLB: one mesh, one primitive, three images (base colour, roughness-metal (ORM), normal).
    Returns positions in Blender axes (Z up), UVs, triangle corner indices; writes the images into tex_out."""
    b = open(path, "rb").read()
    off, chunks = 12, []
    while off < len(b):
        cl, ct = struct.unpack("<II", b[off:off + 8])
        chunks.append(b[off + 8:off + 8 + cl])
        off += 8 + cl
    js, bin_ = json.loads(chunks[0]), chunks[1]
    CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
    NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    def acc(i):
        a = js["accessors"][i]
        bv = js["bufferViews"][a["bufferView"]]
        o = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        dt = np.dtype(CT[a["componentType"]])
        nc = NC[a["type"]]
        st = bv.get("byteStride", 0)
        if st and st != dt.itemsize * nc:             # interleaved (gltf-transform writes POSITION/NORMAL/UV so)
            raw = np.frombuffer(bin_, np.uint8, st * (a["count"] - 1) + dt.itemsize * nc, o)
            idx = (np.arange(a["count"]) * st)[:, None] + np.arange(dt.itemsize * nc)[None]
            return raw[idx].copy().view(dt).reshape(a["count"], nc)
        return np.frombuffer(bin_, dt, a["count"] * nc, o).reshape(a["count"], -1)
    prim = js["meshes"][0]["primitives"][0]
    P = acc(prim["attributes"]["POSITION"]).astype(np.float64)
    UV = acc(prim["attributes"]["TEXCOORD_0"]).astype(np.float32)
    I = acc(prim["indices"]).reshape(-1, 3).astype(np.int64)
    # a node transform on the mesh (Tripo exports none, but be safe)
    for nd in js.get("nodes", []):
        if nd.get("mesh") == 0 and ("matrix" in nd or "scale" in nd or "rotation" in nd or "translation" in nd):
            print("WARNING: the Tripo mesh node has a transform; it is ignored", nd)
    if tex_out:
        mat = js["materials"][prim.get("material", 0)]
        pbr = mat.get("pbrMetallicRoughness", {})
        roles = {"base": pbr.get("baseColorTexture", {}).get("index"),
                 "rm": pbr.get("metallicRoughnessTexture", {}).get("index"),
                 "normal": mat.get("normalTexture", {}).get("index")}
        for role, ti in roles.items():
            if ti is None:
                continue
            im = js["images"][js["textures"][ti]["source"]]
            bv = js["bufferViews"][im["bufferView"]]
            ext = ".png" if "png" in im.get("mimeType", "") else ".jpg"
            o = bv.get("byteOffset", 0)
            for e in (".png", ".jpg"):
                p = os.path.join(tex_out, "tex_%s%s" % (role, e))
                if os.path.exists(p) and e != ext:
                    os.remove(p)
            open(os.path.join(tex_out, "tex_%s%s" % (role, ext)), "wb").write(bin_[o:o + bv["byteLength"]])
    PB = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1)         # glTF Y-up -> Blender Z-up
    return PB, UV, I


def tex_path(work, role):
    for e in (".jpg", ".png"):
        p = os.path.join(work, "tex_%s%s" % (role, e))
        if os.path.exists(p):
            return p
    raise FileNotFoundError("tex_%s in %s" % (role, work))


def rotz(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])


def load_xf(work, fitted=True):
    """The Tripo -> game transform: X_game = s * Rz(yaw) X_tripo + t. xf.json (the load step's guess) is refined by
    the fit (fit.json's 'xf') when that exists. The config's boxes and seeds are in the load step's frame (fitted=False:
    what look.py draws and cut.py reads), so they stay valid when the fit is run again."""
    p = os.path.join(work, "fit.json")
    if fitted and os.path.exists(p):
        f = json.load(open(p))
        if "xf" in f:
            return f["xf"]
    return json.load(open(os.path.join(work, "xf.json")))


def to_game(X, xf):
    return xf["s"] * (np.asarray(X, float) @ rotz(xf["yaw"]).T) + np.array(xf["t"])


def from_game(X, xf):
    return ((np.asarray(X, float) - np.array(xf["t"])) / xf["s"]) @ rotz(xf["yaw"])


def box(C, b):
    """b: [[x0,x1],[y0,y1],[z0,z1]] (game units) or {"c": [x,y,z], "r": r} (a ball)."""
    if isinstance(b, dict):
        if "r" in b:
            return np.linalg.norm(C - np.array(b["c"]), axis=1) < b["r"]
        raise ValueError(b)
    (x0, x1), (y0, y1), (z0, z1) = b
    return (C[:, 0] > x0) & (C[:, 0] < x1) & (C[:, 1] > y0) & (C[:, 1] < y1) & (C[:, 2] > z0) & (C[:, 2] < z1)


def shapes(C, spec, col=None):
    """A face mask from a list of shapes (boxes / balls), each optionally with a colour test:
    {"box": [[..],[..],[..]], "col": {"min": [r,g,b], "max": [r,g,b]}} or a bare box/ball. Union of all."""
    m = np.zeros(len(C), bool)
    for s in spec or []:
        if isinstance(s, dict) and ("box" in s or "ball" in s):
            mm = box(C, s["box"]) if "box" in s else box(C, s["ball"])
            if "col" in s and col is not None:
                lo = np.array(s["col"].get("min", [0, 0, 0]), float)
                hi = np.array(s["col"].get("max", [1, 1, 1]), float)
                mm &= (col >= lo).all(1) & (col <= hi).all(1)
            if s.get("not"):
                m &= ~mm
                continue
        else:
            mm = box(C, s)
        m |= mm
    return m
