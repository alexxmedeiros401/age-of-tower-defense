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
    "delta": dict(ground_a=C([0.34, 0.56, 0.18]), ground_b=C([0.48, 0.64, 0.22]), ground_alt=C([0.74, 0.68, 0.34]),
                  outside=C([0.26, 0.44, 0.15]), path_dark=C([0.62, 0.5, 0.32]), path=C([0.76, 0.64, 0.44]),
                  path_light=C([0.84, 0.74, 0.54]), lip=0.32),
    "desert": dict(ground_a=C([0.82, 0.66, 0.4]), ground_b=C([0.92, 0.78, 0.52]), ground_alt=C([0.76, 0.56, 0.33]),
                   outside=C([0.7, 0.52, 0.3]), path_dark=C([0.56, 0.5, 0.42]), path=C([0.68, 0.62, 0.52]),
                   path_light=C([0.76, 0.71, 0.6]), lip=0.3),
    "canyon": dict(ground_a=C([0.6, 0.33, 0.21]), ground_b=C([0.74, 0.44, 0.28]), ground_alt=C([0.5, 0.27, 0.19]),
                   outside=C([0.4, 0.21, 0.14]), path_dark=C([0.46, 0.33, 0.24]), path=C([0.58, 0.43, 0.3]),
                   path_light=C([0.66, 0.51, 0.36]), lip=0.38),
    "volcano": dict(ground_a=C([0.20, 0.17, 0.16]), ground_b=C([0.33, 0.27, 0.24]), ground_alt=C([0.42, 0.24, 0.17]),
                    outside=C([0.11, 0.09, 0.09]), path_dark=C([0.36, 0.32, 0.29]), path=C([0.50, 0.45, 0.39]),
                    path_light=C([0.62, 0.56, 0.48]), lip=0.4),
}
P = PALETTES[theme]

# ---- distance to every path (and distance travelled along it, for bridge planks / rail sleepers)
def poly_dist(polylines):
    dd = np.full(X.shape, 1e9)
    along = np.zeros(X.shape)
    for pts in polylines:
        pts = np.array(pts, dtype=np.float64)
        cum = 0.0
        for i in range(1, len(pts)):
            a, b = pts[i - 1], pts[i]
            ab = b - a
            L = np.hypot(*ab)
            t = np.clip(((X - a[0]) * ab[0] + (Z - a[1]) * ab[1]) / (L * L), 0, 1)
            d = np.hypot(X - (a[0] + t * ab[0]), Z - (a[1] + t * ab[1]))
            closer = d < dd
            dd = np.where(closer, d, dd)
            along = np.where(closer, cum + t * L, along)
            cum += L
    return dd, along


paths = m["paths"] if "paths" in m else [m["path"]]
dist, along = poly_dist(paths)
half = m["path_width"] / 2
rivers = m.get("rivers", [])
rdist = np.full(X.shape, 1e9)
rhalf = np.zeros(X.shape)

for rv in rivers:
    d_r, _a = poly_dist([rv["pts"]])
    wob = (noise(1.5, 3, 41) - 0.5) * 0.5
    closer = d_r < rdist
    rdist = np.where(closer, d_r + wob, rdist)
    rhalf = np.where(closer, rv["width"] / 2, rhalf)

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
if theme == "desert":
    ripple = np.sin((X * 0.6 + Z * 1.8 + noise(3, 2, 51) * 6.0) * 3.0)
    col *= (0.96 + 0.05 * ripple)[..., None]
if theme == "canyon":
    strata = np.sin(Z * 2.4 + noise(4, 3, 61) * 5.0)
    col = lerp(col, C([0.82, 0.55, 0.36]), np.clip(strata - 0.6, 0, 1) * 0.6)
    col = lerp(col, C([0.42, 0.22, 0.15]), np.clip(-strata - 0.75, 0, 1) * 0.8)
if theme == "snow":
    # wind-blown drift streaks
    streak = noise(0.9, 2, 31)
    col = lerp(col, C([1.0, 1.0, 1.0]), np.clip((streak - 0.6) * 2.5, 0, 1) * 0.5)

# ---- rivers (painted before the road so the road becomes a bridge where they cross)
if rivers:
    bank = np.clip(1 - (rdist - rhalf) / 0.5, 0, 1) * (rdist > rhalf - 0.1)
    col = lerp(col, C([0.52, 0.44, 0.3]), bank * 0.85)
    depth = np.clip((rhalf - rdist) / np.maximum(rhalf, 0.01), 0, 1)
    water = lerp(C([0.25, 0.62, 0.66]), C([0.1, 0.36, 0.55]), depth ** 0.8)
    rip = noise(0.4, 2, 71)
    water = lerp(water, C([0.7, 0.9, 0.92]), np.clip((rip - 0.7) * 4, 0, 1) * 0.5)
    col = lerp(col, water, np.clip((rhalf - rdist) / 0.12, 0, 1))

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
if theme == "desert":   # paved flagstone road
    stones = (np.sin(along * 5.5) > 0.9) | (np.abs(np.sin((dist - jag) * 6.0)) < 0.08)
    path_col = path_col * np.where(stones, 0.8, 1.0)[..., None]
col = lerp(col, path_col, inside)
edge_band = np.clip(1 - np.abs(pd - (half - 0.08)) / 0.1, 0, 1) * 0.3
col *= (1 - edge_band)[..., None]
if theme == "canyon":   # mine-cart rails down the middle of the road
    sleeper = (np.sin(along * 9.0) > 0.55) & (dist < 0.5)
    col = lerp(col, C([0.32, 0.2, 0.12]), (sleeper * inside).astype(float) * 0.8)
    rail = np.exp(-((dist - 0.32) ** 2) / (2 * 0.035 ** 2))
    col = lerp(col, C([0.3, 0.3, 0.32]), rail * inside * 0.95)
if rivers:   # wooden bridge where the road crosses water
    on_water = (rdist < rhalf + 0.15) & (dist < half + 0.1)
    plank = C([0.56, 0.38, 0.2]) * (0.85 + 0.15 * noise(0.3, 2, 81))[..., None]
    plank *= np.where(np.sin(along * 14.0) > 0.85, 0.6, 1.0)[..., None]
    rail_edge = np.abs(dist - half) < 0.09
    plank = np.where(rail_edge[..., None], C([0.3, 0.19, 0.1]), plank)
    col = np.where(on_water[..., None], plank, col)

# ---- no-build zones
for bl in m.get("blockers", []):
    bx, bz, br = bl[0], bl[1], bl[2]
    kind = bl[3] if len(bl) > 3 else {"snow": "lake", "volcano": "lava"}.get(theme, "rocks")
    wob = (noise(0.8, 2, int(bx * 7 + bz * 13) % 997) - 0.5) * 0.5
    d = np.hypot(X - bx, Z - bz) + wob
    core = np.clip((br - d) / 0.15, 0, 1)
    rim = np.clip(1 - np.abs(d - br) / 0.35, 0, 1)
    depth = np.clip(1 - d / br, 0, 1)
    if kind == "lake" and theme != "snow":   # fresh water pond
        water = lerp(C([0.25, 0.6, 0.62]), C([0.1, 0.34, 0.52]), depth ** 0.7)
        col = lerp(col, water, core)
        col = lerp(col, C([0.5, 0.42, 0.28]), rim * (1 - core) * 0.85)
    elif kind == "lake":
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
    elif kind == "ore":   # glowing copper-green ore pool
        ore = lerp(C([0.15, 0.75, 0.6]), C([0.55, 1.0, 0.8]), depth ** 1.5)
        col = lerp(col, ore, core)
        col = lerp(col, C([0.2, 0.12, 0.08]), rim * (1 - core) * 0.9)
    elif kind == "dune":  # sand mound, lit from the upper left
        shade = np.clip(1 - d / br, 0, 1) * (((X - bx) * -0.6 + (Z - bz) * -0.8) / br)
        col = lerp(col, C([0.98, 0.88, 0.66]), np.clip(shade, 0, 1) * core * 0.8)
        col = lerp(col, C([0.62, 0.44, 0.26]), np.clip(-shade, 0, 1) * core * 0.6)
    elif kind == "ruins":  # paved courtyard
        tiles = (np.abs(np.sin(X * 4.0)) < 0.12) | (np.abs(np.sin(Z * 4.0)) < 0.12)
        col = lerp(col, np.where(tiles[..., None], C([0.5, 0.44, 0.36]), C([0.74, 0.68, 0.58])), core)
    elif kind == "palms":  # oasis grass patch
        col = lerp(col, C([0.32, 0.55, 0.2]), core * 0.9)
    else:  # rocks / pillars: darker gravel bed under the 3D boulders
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
    if dist[i, j] <= half + 0.35 or blocked(i, j) or rdist[i, j] < rhalf[i, j] + 0.2:
        if theme == "delta" and rhalf[i, j] - 0.05 < rdist[i, j] < rhalf[i, j] + 0.7 and dist[i, j] > half + 0.3:
            for k in range(3):   # reeds along the banks
                a = rng.uniform(-0.35, 0.35)
                draw.line((j + k * 2, i, j + k * 2 + np.sin(a) * 10, i - np.cos(a) * 10), fill=(60, 100, 40, 255), width=2)
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
    elif theme == "delta":
        if rng.random() < 0.05 and edge[i, j] > 0:
            c = [(250, 240, 200), (240, 200, 90), (230, 150, 170)][rng.integers(0, 3)]
            draw.ellipse((j - 2.5, i - 2.5, j + 2.5, i + 2.5), fill=(*c, 255))
            continue
        ln = rng.uniform(4, 9); a = rng.uniform(-0.6, 0.6); sh = rng.uniform(0.7, 1.25)
        c = tuple(int(np.clip(v, 0, 1) * 255) for v in col[i, j] * sh)
        draw.line((j, i, j + np.sin(a) * ln, i - np.cos(a) * ln), fill=(*c, 230), width=2)
    elif theme == "desert":
        if rng.random() < 0.12:
            r = rng.uniform(1.5, 3.5)
            g = int(rng.uniform(140, 190))
            draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(g, int(g * 0.85), int(g * 0.65), 255))
        elif rng.random() < 0.03:   # dry scrub
            for k in range(4):
                a = rng.uniform(-1.2, 1.2)
                draw.line((j, i, j + np.sin(a) * 7, i - np.cos(a) * 7), fill=(120, 105, 60, 230), width=2)
    elif theme == "canyon":
        roll = rng.random()
        if roll < 0.06:   # copper flecks
            draw.ellipse((j - 2, i - 2, j + 2, i + 2), fill=(60, 200, 160, 230))
        elif roll < 0.35:
            r = rng.uniform(1.5, 4)
            g = rng.uniform(0.6, 1.0)
            draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(int(120 * g), int(64 * g), int(42 * g), 255))
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
