"""Paints a map's ground texture from its JSON, so art and simulation paths always match.
Run: python3 gen_ground.py data/map_mammoth_valley.json assets/textures/ground_mammoth_valley.png
World coverage: x in [X0, X0+W], z in [Z0, Z0+H]; image row 0 = z=Z0 (top of screen)."""
import json, sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

X0, Z0, W, H = -21.0, -13.0, 40.0, 26.0
PX = 52  # pixels per world unit
rng = np.random.default_rng(7)

m = json.load(open(sys.argv[1]))
out = sys.argv[2]
w_px, h_px = int(W * PX), int(H * PX)
xs = X0 + (np.arange(w_px) + 0.5) / PX
zs = Z0 + (np.arange(h_px) + 0.5) / PX
X, Z = np.meshgrid(xs, zs)


def noise(scale_units, octaves=4, seed=0):
    r = np.random.default_rng(seed)
    acc = np.zeros((h_px, w_px))
    amp, tot = 1.0, 0.0
    s = scale_units
    for o in range(octaves):
        gw, gh = max(2, int(W / s) + 2), max(2, int(H / s) + 2)
        g = r.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w_px, h_px), Image.BICUBIC)
        acc += amp * (np.asarray(im, dtype=np.float32) / 255.0)
        tot += amp
        amp *= 0.5
        s *= 0.5
    return acc / tot


def lerp(a, b, t):
    return a + (b - a) * t[..., None]


# ---- distance to path
pts = np.array(m["path"], dtype=np.float64)
dist = np.full(X.shape, 1e9)
along = np.zeros(X.shape)
cum = 0.0
for i in range(1, len(pts)):
    a, b = pts[i - 1], pts[i]
    ab = b - a
    L = np.hypot(*ab)
    t = np.clip(((X - a[0]) * ab[0] + (Z - a[1]) * ab[1]) / (L * L), 0, 1)
    px, pz = a[0] + t * ab[0], a[1] + t * ab[1]
    d = np.hypot(X - px, Z - pz)
    closer = d < dist
    dist = np.where(closer, d, dist)
    along = np.where(closer, cum + t * L, along)
    cum += L
half = m["path_width"] / 2

# ---- grass
n1 = noise(6, 4, 1)
n2 = noise(1.2, 3, 2)
n3 = noise(0.25, 2, 3)
grass_a = np.array([0.30, 0.56, 0.16])
grass_b = np.array([0.42, 0.66, 0.20])
grass_dry = np.array([0.56, 0.62, 0.24])
col = lerp(grass_a, grass_b, np.clip(n1 * 1.6 - 0.3, 0, 1))
col = lerp(col, grass_dry, np.clip((n2 - 0.62) * 3.0, 0, 1) * 0.55)
col *= (0.9 + 0.2 * n3)[..., None]

# forest floor outside the buildable meadow
b = m["bounds"]
edge = np.minimum.reduce([X - b[0], b[2] - X, Z - b[1], b[3] - Z])
edge_soft = edge + (noise(2.5, 3, 9) - 0.5) * 2.2
outside = np.clip((-edge_soft + 0.6) / 1.4, 0, 1)
forest = np.array([0.15, 0.36, 0.11]) * (0.85 + 0.3 * n2)[..., None]
col = lerp(col, forest, outside)
# soft darker lip at the meadow edge


# ---- path
jag = (noise(0.7, 3, 4) - 0.5) * 0.28
pd = dist - jag
dirt_dark = np.array([0.46, 0.32, 0.18])
dirt = np.array([0.66, 0.50, 0.31])
dirt_light = np.array([0.76, 0.62, 0.42])
dn = noise(0.9, 4, 5)
path_col = lerp(dirt_dark, dirt, np.clip(dn * 1.4 - 0.1, 0, 1))
center = np.exp(-(dist ** 2) / (2 * 0.32 ** 2))
path_col = lerp(path_col, dirt_light, center * 0.5)

inside = np.clip((half - pd) / 0.12, 0, 1)
shadow = np.clip(1 - np.abs(pd - half) / 0.22, 0, 1) * 0.35  # grass lip shadow
col *= (1 - shadow * (1 - inside))[..., None]
col = lerp(col, path_col, inside)
edge_band = np.clip(1 - np.abs(pd - (half - 0.08)) / 0.1, 0, 1) * 0.3
col *= (1 - edge_band)[..., None]

img = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8), "RGB")
draw = ImageDraw.Draw(img, "RGBA")


def to_px(x, z):
    return ((x - X0) * PX, (z - Z0) * PX)


# pebbles on and near the path
for _ in range(900):
    i = rng.integers(0, h_px); j = rng.integers(0, w_px)
    if dist[i, j] < half + 0.25:
        r = rng.uniform(2, 6)
        g = int(rng.uniform(120, 175))
        draw.ellipse((j - r + 1.5, i - r * 0.7 + 2, j + r + 1.5, i + r * 0.7 + 2), fill=(40, 28, 15, 90))
        draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(g, g - 4, g - 10, 255))
# flowers and grass strokes in the meadow
for _ in range(5200):
    i = rng.integers(0, h_px); j = rng.integers(0, w_px)
    if dist[i, j] > half + 0.35:
        if rng.random() < 0.12 and edge[i, j] > 0:
            c = [(250, 250, 240), (255, 220, 70), (240, 140, 200), (170, 190, 255)][rng.integers(0, 4)]
            r = rng.uniform(2, 3.5)
            draw.ellipse((j - r, i - r, j + r, i + r), fill=(*c, 255))
            draw.ellipse((j - 1, i - 1, j + 1, i + 1), fill=(255, 200, 40, 255))
        else:
            ln = rng.uniform(4, 9)
            a = rng.uniform(-0.6, 0.6)
            sh = rng.uniform(0.6, 1.25)
            base = col[i, j] * sh
            c = tuple(int(np.clip(v, 0, 1) * 255) for v in base)
            draw.line((j, i, j + np.sin(a) * ln, i - np.cos(a) * ln), fill=(*c, 230), width=2)
img = img.filter(ImageFilter.SMOOTH)
img.save(out)
print("ground", img.size, out)
