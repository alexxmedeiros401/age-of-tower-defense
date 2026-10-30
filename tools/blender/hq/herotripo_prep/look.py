"""Quick looks at the Tripo model in game units (numpy point splats of the 2M faces, no Blender), with a grid to read
coordinates off for the config's cut seeds and boxes.

    python3 look.py -- --hero ugo [--views front,back,left,right,top] [--crop x0,x1,y0,y1,z0,z1] [--px 900]
                       [--labels] [--mask file.npy] [--out NAME]

Views (orthographic, game axes; he faces -Y): front (camera at -Y), back, left (camera at -X: his right side), right
(camera at +X), top. Grid lines every 0.1 (labels in metres, game/armature units); with --crop every 0.05.
--labels colours the cut pieces (labels.npz: body grey-tinted, props in strong colours, dropped faces magenta);
--mask paints a face mask (a .npy of booleans) red. Writes <work>/look_<out>.png.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import common as C

PAL = np.array([[0.75, 0.75, 0.75], [0.1, 0.45, 1.0], [0.1, 0.85, 0.2], [1.0, 0.75, 0.0], [0.6, 0.2, 0.9],
                [0.0, 0.85, 0.85], [1.0, 0.4, 0.1], [0.5, 0.3, 0.1]])
VIEWS = {"front": ((0, 2), (1, -1), -1), "back": ((0, 2), (1, 1), -1), "left": ((1, 2), (0, -1), 1),
         "right": ((1, 2), (0, 1), 1), "top": ((0, 1), (2, 1), 1)}
# per view: (image axes (u, v)), (depth axis, sign: larger depth*sign = nearer the camera), flip u


def face_colours(W, I, UV, tex_path):
    tex = np.asarray(Image.open(tex_path).convert("RGB"))
    S = tex.shape[0]
    uvc = UV[I].mean(1)
    return tex[np.clip((uvc[:, 1] * S).astype(int), 0, S - 1), np.clip((uvc[:, 0] * S).astype(int), 0, S - 1)].astype(np.float32) / 255


def render(Cg, N, col, view, px, crop=None):
    (ua, va), (da, ds), fl = VIEWS[view]
    m = np.ones(len(Cg), bool)
    if crop is not None:
        m = C.box(Cg, crop)
    X = Cg[m]
    u, v, d = X[:, ua] * (-1 if (view in ("back", "left")) else 1), X[:, va], X[:, da] * ds
    if view == "top":
        v = X[:, 1] * -1
    lo_u, hi_u = u.min(), u.max()
    lo_v, hi_v = v.min(), v.max()
    span = max(hi_u - lo_u, hi_v - lo_v) * 1.04
    cu, cv = (lo_u + hi_u) / 2, (lo_v + hi_v) / 2
    sc = px / span
    iu = ((u - cu) * sc + px / 2).astype(int)
    iv = (px / 2 - (v - cv) * sc).astype(int)
    ok = (iu >= 0) & (iu < px) & (iv >= 0) & (iv < px)
    order = np.argsort(d[ok])                       # far first, near last wins
    idx = np.nonzero(ok)[0][order]
    light = np.array([0.35, -0.6, 0.7])
    light /= np.linalg.norm(light)
    sh = 0.45 + 0.55 * np.clip(N[m] @ light, 0, 1)
    c = np.clip(col[m] * sh[:, None], 0, 1)
    img = np.full((px, px, 3), 0.82, np.float32)
    for du in (0, 1):
        for dv in (0, 1):
            img[np.clip(iv[idx] + dv, 0, px - 1), np.clip(iu[idx] + du, 0, px - 1)] = c[idx]
    im = Image.fromarray((img * 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    step = 0.05 if crop is not None else 0.1
    sgn_u = -1 if view in ("back", "left") else 1
    for g in np.arange(np.floor((cu - span / 2) / step) * step, cu + span / 2, step):
        x = int((g - cu) * sc + px / 2)
        dr.line([(x, 0), (x, px)], fill=(120, 120, 160) if abs(round(g / step) % 2) else (60, 60, 200), width=1)
        dr.text((x + 2, 2), "%.2f" % (g * sgn_u), fill=(0, 0, 120))
    for g in np.arange(np.floor((cv - span / 2) / step) * step, cv + span / 2, step):
        y = int(px / 2 - (g - cv) * sc)
        dr.line([(0, y), (px, y)], fill=(120, 120, 160) if abs(round(g / step) % 2) else (60, 60, 200), width=1)
        dr.text((2, y + 2), "%.2f" % (g * (-1 if view == "top" else 1)), fill=(0, 0, 120))
    axn = "xyz"
    dr.text((px - 230, px - 16), "%s: right=%s%s up=%s%s" % (view, "+-"[sgn_u < 0], axn[ua], "+-"[int(view == "top")], axn[va]), fill=(0, 0, 0))
    return im


def main():
    hid = C.arg("--hero")
    cfg = C.load_cfg(hid)
    W = C.work_dir(hid)
    xf = C.load_xf(W, fitted=False)
    t = np.load(os.path.join(W, "topo.npz"))
    z = np.load(os.path.join(W, "tripo_np.npz"))
    Cg = C.to_game(t["C"], xf)
    N = t["N"] @ C.rotz(xf["yaw"]).T
    col = face_colours(None, z["I"], z["UV"], C.tex_path(W, "base"))
    if "--labels" in sys.argv:
        lab = np.load(os.path.join(W, "labels.npz"))["lab"]
        tint = PAL[np.clip(lab, 0, len(PAL) - 1)]
        tint[lab == 255] = (1.0, 0.0, 1.0)
        col = np.where((lab == 0)[:, None], col * 0.6 + 0.4 * tint, tint)
    mk = C.arg("--mask")
    if mk:
        m = np.load(mk)
        col[m] = (1.0, 0.1, 0.1)
    crop = C.arg("--crop")
    crop = np.array([float(v) for v in crop.split(",")]).reshape(3, 2).tolist() if crop else None
    px = int(C.arg("--px", "900"))
    views = C.arg("--views", "front,left,back,right").split(",")
    ims = [render(Cg, N, col, v, px, crop) for v in views]
    M = Image.new("RGB", (px * len(ims), px))
    for i, im in enumerate(ims):
        M.paste(im, (i * px, 0))
    out = os.path.join(W, "look_%s.png" % C.arg("--out", "all"))
    M.save(out)
    print("[look]", out)


main()
