"""Water mask for a map's painted ground: the rivers, lakes and ponds the ground painted, and which way each river
flows, for the ground shader that makes them move (game/shaders/ground_water.gdshader).

    python3 tools/water_mask.py river_delta      -> assets/textures/ground_river_delta_water.png (half resolution)
    python3 tools/water_mask.py mirefen_bog --src MASK.png    (the water from the ground tool's mask, not its colour)

R = how much of the pixel is water (the painted water: blue to teal, bluer than it is red or green);
G, B = the flow direction (world x, z, as 0.5 + 0.5 * d): along the nearest river, from its first point to its last;
       still water (lakes, ponds, wide pools away from any river) has no flow (0.5, 0.5);
A = 255.
Re-run it whenever the ground is re-rendered (the mask follows the painted water, not the map file)."""
import json
import sys
import numpy as np
from PIL import Image, ImageFilter

X0, Z0, W, H = -21.0, -13.0, 40.0, 26.0          # the ground's world rectangle (game.gd GROUND_RECT)

mid = sys.argv[1] if len(sys.argv) > 1 else "river_delta"
src = "assets/textures/ground_%s.png" % mid
m = json.load(open("data/map_%s.json" % mid))
img = Image.open(src).convert("RGB")
w2, h2 = img.width // 2, img.height // 2
im = np.asarray(img.resize((w2, h2), Image.LANCZOS)).astype(np.float32) / 255.0
R, G, B = im[..., 0], im[..., 1], im[..., 2]
water = np.clip((B - R - 0.14) / 0.16, 0, 1) * np.clip((B - G + 0.1) / 0.12, 0, 1)
if "--src" in sys.argv:                  # the ground tool's own water mask (map_ground_hq.py --watersrc): peaty bog water
    srcm = Image.open(sys.argv[sys.argv.index("--src") + 1]).convert("L").resize((w2, h2), Image.BILINEAR)   # isn't blue
    water = np.asarray(srcm).astype(np.float32) / 255.0

xs = X0 + (np.arange(w2) + 0.5) / w2 * W
zs = Z0 + (np.arange(h2) + 0.5) / h2 * H
X, Z = np.meshgrid(xs, zs)
best = np.full(X.shape, 1e9, np.float32)
fx = np.zeros(X.shape, np.float32)
fz = np.zeros(X.shape, np.float32)
reach = np.zeros(X.shape, np.float32)
for rv in m.get("rivers", []):
    pts = np.array(rv["pts"], np.float32)
    half = float(rv.get("width", 2.0)) * 0.5
    for a, b in zip(pts[:-1], pts[1:]):
        ab = b - a
        L2 = float(ab @ ab) or 1e-6
        t = np.clip(((X - a[0]) * ab[0] + (Z - a[1]) * ab[1]) / L2, 0, 1)
        d = np.hypot(X - (a[0] + ab[0] * t), Z - (a[1] + ab[1] * t))
        closer = d < best
        best = np.where(closer, d, best)
        u = ab / np.sqrt(L2)
        fx = np.where(closer, u[0], fx)
        fz = np.where(closer, u[1], fz)
        reach = np.where(closer, half, reach)
# the flow fades out past a river's banks (still water beyond: a lake it runs into, a pond)
k = np.clip(1.0 - (best - reach) / 1.2, 0, 1)
fx *= k
fz *= k
for bl in m.get("blockers", []):
    if len(bl) > 3 and str(bl[3]) in ("lake", "pond"):
        d = np.hypot(X - bl[0], Z - bl[1])
        still = np.clip((float(bl[2]) + 0.4 - d) / 0.4, 0, 1)
        fx *= 1 - still
        fz *= 1 - still
out = np.stack([water, 0.5 + 0.5 * fx, 0.5 + 0.5 * fz, np.ones_like(water)], -1)
res = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), "RGBA")
r, g, b, a = res.split()
r = r.filter(ImageFilter.GaussianBlur(0.7))
# (the flow turns smoothly round each bend: a hard change of direction at a joint shows as a seam in the moving water)
g = g.filter(ImageFilter.GaussianBlur(9))
b = b.filter(ImageFilter.GaussianBlur(9))
res = Image.merge("RGBA", (r, g, b, a))
dst = "assets/textures/ground_%s_water.png" % mid
res.save(dst)
print(dst, res.size, "water %.1f%%" % (100.0 * float((water > 0.1).mean())), "flowing %.1f%%" % (100.0 * float(((water > 0.1) & (np.hypot(fx, fz) > 0.3)).mean())))
