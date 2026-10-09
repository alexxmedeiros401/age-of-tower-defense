"""Paints a map's ground texture from its JSON, so the art always matches the simulation's paths and no-build zones.
Themes: meadow | snow | volcano.  Blockers: [x, z, r, kind] with kind lake | rocks | lava.
Run: python3 gen_ground.py data/map_<id>.json assets/textures/ground_<id>.png
World coverage: x in [X0, X0+W], z in [Z0, Z0+H]; image row 0 = z=Z0 (top of screen)."""
import json, sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

X0, Z0, W, H = -21.0, -13.0, 40.0, 26.0
PX = 52  # pixels per world unit
rng = np.random.default_rng(7)

m = json.load(open(sys.argv[1]))
out = sys.argv[2]
theme = m.get("theme", "meadow")
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
    a = np.asarray(a, dtype=np.float64)
    return a + (np.asarray(b, dtype=np.float64) - a) * t[..., None]


C = np.array  # shorthand for colors

PALETTES = {
    "meadow": dict(ground_a=C([0.30, 0.56, 0.16]), ground_b=C([0.42, 0.66, 0.20]), ground_alt=C([0.56, 0.62, 0.24]),
                   outside=C([0.15, 0.36, 0.11]), path_dark=C([0.46, 0.32, 0.18]), path=C([0.66, 0.50, 0.31]),
                   path_light=C([0.76, 0.62, 0.42]), lip=0.35),
    "snow": dict(ground_a=C([0.80, 0.86, 0.94]), ground_b=C([0.95, 0.97, 1.0]), ground_alt=C([0.70, 0.78, 0.88]),
                 outside=C([0.62, 0.70, 0.80]), path_dark=C([0.50, 0.46, 0.44]), path=C([0.64, 0.60, 0.58]),
                 path_light=C([0.80, 0.80, 0.82]), lip=0.22),
    "volcano": dict(ground_a=C([0.20, 0.17, 0.16]), ground_b=C([0.33, 0.27, 0.24]), ground_alt=C([0.42, 0.24, 0.17]),
                    outside=C([0.11, 0.09, 0.09]), path_dark=C([0.36, 0.32, 0.29]), path=C([0.50, 0.45, 0.39]),
                    path_light=C([0.62, 0.56, 0.48]), lip=0.4),
}
P = PALETTES[theme]

# ---- distance to every path
paths = m["paths"] if "paths" in m else [m["path"]]
dist = np.full(X.shape, 1e9)
for pts in paths:
    pts = np.array(pts, dtype=np.float64)
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        ab = b - a
        L = np.hypot(*ab)
        t = np.clip(((X - a[0]) * ab[0] + (Z - a[1]) * ab[1]) / (L * L), 0, 1)
        d = np.hypot(X - (a[0] + t * ab[0]), Z - (a[1] + t * ab[1]))
        dist = np.minimum(dist, d)
half = m["path_width"] / 2

# ---- base ground
n1 = noise(6, 4, 1)
n2 = noise(1.2, 3, 2)
n3 = noise(0.25, 2, 3)
col = lerp(P["ground_a"], P["ground_b"], np.clip(n1 * 1.6 - 0.3, 0, 1))
col = lerp(col, P["ground_alt"], np.clip((n2 - 0.62) * 3.0, 0, 1) * 0.55)
col *= (0.92 + 0.16 * n3)[..., None]

b = m["bounds"]
edge = np.minimum.reduce([X - b[0], b[2] - X, Z - b[1], b[3] - Z])
edge_soft = edge + (noise(2.5, 3, 9) - 0.5) * 2.2
outside = np.clip((-edge_soft + 0.6) / 1.4, 0, 1)
col = lerp(col, P["outside"] * (0.85 + 0.3 * n2)[..., None], outside)

if theme == "volcano":
    # glowing fissures in the basalt (kept off the road)
    nc = noise(2.2, 3, 21)
    crack = np.exp(-((nc - 0.5) / 0.012) ** 2) * np.clip((noise(4, 2, 22) - 0.45) * 4, 0, 1)
    crack *= np.clip((dist - half - 0.6) / 0.6, 0, 1)
    col = lerp(col, C([1.0, 0.42, 0.08]), np.clip(crack, 0, 1) * 0.9)
if theme == "snow":
    # wind-blown drift streaks
    streak = noise(0.9, 2, 31)
    col = lerp(col, C([1.0, 1.0, 1.0]), np.clip((streak - 0.6) * 2.5, 0, 1) * 0.5)

# ---- path
jag = (noise(0.7, 3, 4) - 0.5) * 0.28
pd = dist - jag
dn = noise(0.9, 4, 5)
path_col = lerp(P["path_dark"], P["path"], np.clip(dn * 1.4 - 0.1, 0, 1))
center = np.exp(-(dist ** 2) / (2 * 0.32 ** 2))
path_col = lerp(path_col, P["path_light"], center * 0.5)
inside = np.clip((half - pd) / 0.12, 0, 1)
shadow = np.clip(1 - np.abs(pd - half) / 0.22, 0, 1) * P["lip"]
col *= (1 - shadow * (1 - inside))[..., None]
col = lerp(col, path_col, inside)
edge_band = np.clip(1 - np.abs(pd - (half - 0.08)) / 0.1, 0, 1) * 0.3
col *= (1 - edge_band)[..., None]

# ---- no-build zones
for bl in m.get("blockers", []):
    bx, bz, br = bl[0], bl[1], bl[2]
    kind = bl[3] if len(bl) > 3 else {"snow": "lake", "volcano": "lava"}.get(theme, "rocks")
    wob = (noise(0.8, 2, int(bx * 7 + bz * 13) % 997) - 0.5) * 0.5
    d = np.hypot(X - bx, Z - bz) + wob
    core = np.clip((br - d) / 0.15, 0, 1)
    rim = np.clip(1 - np.abs(d - br) / 0.35, 0, 1)
    depth = np.clip(1 - d / br, 0, 1)
    if kind == "lake":
        ice = lerp(C([0.66, 0.85, 0.95]), C([0.40, 0.64, 0.84]), depth ** 0.7)
        cr = noise(0.6, 2, int(bx * 3 + 50) % 991)
        ice = lerp(ice, C([0.92, 0.97, 1.0]), np.exp(-((cr - 0.5) / 0.01) ** 2) * 0.8)
        col = lerp(col, ice, core)
        col = lerp(col, C([0.98, 0.99, 1.0]), rim * (1 - core) * 0.9)
    elif kind == "lava":
        lava = lerp(C([1.0, 0.42, 0.06]), C([1.0, 0.86, 0.35]), depth ** 1.5)
        swirl = noise(0.5, 2, int(bz * 5 + 70) % 983)
        lava = lerp(lava, C([0.75, 0.18, 0.04]), np.clip((swirl - 0.62) * 4, 0, 1) * 0.7)
        col = lerp(col, lava, core)
        col = lerp(col, C([0.08, 0.05, 0.05]), rim * (1 - core) * 0.95)
        heat = np.clip(1 - (d - br) / 1.2, 0, 1) * (1 - core)
        col = lerp(col, C([0.55, 0.16, 0.05]), heat * 0.35)
    else:  # rocks: darker gravel bed under the 3D boulders
        col = lerp(col, P["outside"] * 0.8, core * 0.85)

img = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8), "RGB")
draw = ImageDraw.Draw(img, "RGBA")


def blocked(i, j):
    x, z = X0 + j / PX, Z0 + i / PX
    for bl in m.get("blockers", []):
        if np.hypot(x - bl[0], z - bl[1]) < bl[2] + 0.2:
            return True
    return False


# pebbles on and near the path
for _ in range(900):
    i = rng.integers(0, h_px); j = rng.integers(0, w_px)
    if dist[i, j] < half + 0.25:
        r = rng.uniform(2, 6)
        g = int(rng.uniform(120, 175)) if theme != "volcano" else int(rng.uniform(40, 80))
        draw.ellipse((j - r + 1.5, i - r * 0.7 + 2, j + r + 1.5, i + r * 0.7 + 2), fill=(30, 22, 15, 90))
        draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(g, g - 4, max(g - 10, 0), 255))
# surface detail
for _ in range(5200):
    i = rng.integers(0, h_px); j = rng.integers(0, w_px)
    if dist[i, j] <= half + 0.35 or blocked(i, j):
        continue
    if theme == "meadow":
        if rng.random() < 0.12 and edge[i, j] > 0:
            c = [(250, 250, 240), (255, 220, 70), (240, 140, 200), (170, 190, 255)][rng.integers(0, 4)]
            r = rng.uniform(2, 3.5)
            draw.ellipse((j - r, i - r, j + r, i + r), fill=(*c, 255))
            draw.ellipse((j - 1, i - 1, j + 1, i + 1), fill=(255, 200, 40, 255))
            continue
        ln = rng.uniform(4, 9); a = rng.uniform(-0.6, 0.6); sh = rng.uniform(0.6, 1.25)
        c = tuple(int(np.clip(v, 0, 1) * 255) for v in col[i, j] * sh)
        draw.line((j, i, j + np.sin(a) * ln, i - np.cos(a) * ln), fill=(*c, 230), width=2)
    elif theme == "snow":
        roll = rng.random()
        if roll < 0.06:   # dry grass tuft poking through the snow
            for k in range(3):
                a = rng.uniform(-0.5, 0.5)
                draw.line((j + k * 2, i, j + k * 2 + np.sin(a) * 7, i - np.cos(a) * 7), fill=(150, 125, 80, 220), width=2)
        elif roll < 0.12:  # small dark stone
            r = rng.uniform(2, 4)
            draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(95, 100, 110, 255))
        else:              # snow sparkle / shadow dimple
            c = (255, 255, 255, 200) if rng.random() < 0.6 else (175, 195, 220, 160)
            draw.ellipse((j - 1.5, i - 1.5, j + 1.5, i + 1.5), fill=c)
    else:  # volcano
        roll = rng.random()
        if roll < 0.08:   # embers
            r = rng.uniform(1.5, 2.5)
            draw.ellipse((j - r, i - r, j + r, i + r), fill=(255, int(rng.uniform(90, 170)), 30, 230))
        elif roll < 0.3:  # obsidian chips
            r = rng.uniform(2, 4.5)
            draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(20, 18, 20, 255))
        else:             # ash speckle
            g = int(rng.uniform(80, 130))
            draw.ellipse((j - 1.5, i - 1.5, j + 1.5, i + 1.5), fill=(g, g - 5, g - 8, 160))
img = img.filter(ImageFilter.SMOOTH)
img.save(out)
print("ground", theme, img.size, out)
