"""Paints a map's ground texture from its JSON, so the art always matches the simulation's paths and no-build zones.
Original themes: meadow | snow | volcano | delta | desert | canyon (their code paths below are frozen: changing them
changes the committed textures). Era themes (iron .. datacenter, see tools/era_spec.py THEMES) use the *_new painters:
their own palette, ground pattern, road style (PATH_STYLE), water and blocker footprints.
Blockers: [x, z, r, kind].
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
OLD_THEMES = set(PALETTES)


def _pal(ga, gb, alt, outs, pd, p, pl, lip):
    return dict(ground_a=C(ga), ground_b=C(gb), ground_alt=C(alt), outside=C(outs),
                path_dark=C(pd), path=C(p), path_light=C(pl), lip=lip)


# era themes (tools/era_spec.py THEMES): ground_a/ground_b/ground_alt/outside, path_dark/path/path_light, lip shadow
PALETTES.update({
    # Iron Age
    "highland": _pal([0.27, 0.50, 0.20], [0.40, 0.62, 0.25], [0.50, 0.56, 0.30], [0.17, 0.33, 0.15],
                     [0.46, 0.34, 0.21], [0.64, 0.50, 0.33], [0.75, 0.63, 0.45], 0.36),
    "forge": _pal([0.16, 0.14, 0.13], [0.27, 0.24, 0.22], [0.36, 0.22, 0.15], [0.08, 0.07, 0.07],
                  [0.40, 0.36, 0.33], [0.54, 0.49, 0.44], [0.64, 0.58, 0.51], 0.42),
    "bog": _pal([0.23, 0.31, 0.16], [0.35, 0.41, 0.21], [0.42, 0.37, 0.23], [0.15, 0.21, 0.12],
                [0.47, 0.32, 0.17], [0.64, 0.46, 0.27], [0.73, 0.56, 0.35], 0.48),
    # Classical
    "olive": _pal([0.72, 0.60, 0.30], [0.85, 0.74, 0.42], [0.86, 0.79, 0.62], [0.56, 0.47, 0.25],
                  [0.55, 0.53, 0.50], [0.71, 0.69, 0.65], [0.82, 0.80, 0.76], 0.34),
    "coast": _pal([0.86, 0.73, 0.49], [0.94, 0.84, 0.62], [0.82, 0.82, 0.80], [0.74, 0.63, 0.44],
                  [0.78, 0.80, 0.84], [0.92, 0.93, 0.96], [0.99, 0.99, 1.0], 0.46),
    "acropolis": _pal([0.38, 0.56, 0.24], [0.49, 0.65, 0.29], [0.56, 0.62, 0.32], [0.28, 0.44, 0.20],
                      [0.80, 0.80, 0.83], [0.92, 0.92, 0.94], [0.99, 0.99, 1.0], 0.42),
    # Medieval
    "farmland": _pal([0.35, 0.58, 0.21], [0.46, 0.68, 0.26], [0.60, 0.66, 0.30], [0.23, 0.41, 0.16],
                     [0.49, 0.35, 0.21], [0.68, 0.53, 0.34], [0.78, 0.65, 0.46], 0.36),
    "castle": _pal([0.37, 0.51, 0.23], [0.47, 0.59, 0.27], [0.52, 0.47, 0.33], [0.25, 0.36, 0.18],
                   [0.38, 0.38, 0.40], [0.55, 0.55, 0.57], [0.66, 0.66, 0.68], 0.40),
    "darkwood": _pal([0.15, 0.21, 0.11], [0.23, 0.29, 0.14], [0.31, 0.24, 0.14], [0.08, 0.11, 0.07],
                     [0.44, 0.33, 0.21], [0.60, 0.47, 0.30], [0.70, 0.57, 0.39], 0.45),
    # Gunpowder
    "harbor": _pal([0.45, 0.62, 0.27], [0.57, 0.70, 0.33], [0.86, 0.78, 0.56], [0.35, 0.49, 0.22],
                   [0.43, 0.30, 0.17], [0.58, 0.42, 0.25], [0.68, 0.51, 0.32], 0.42),
    "fortress": _pal([0.42, 0.52, 0.24], [0.52, 0.60, 0.29], [0.64, 0.52, 0.34], [0.33, 0.36, 0.20],
                     [0.62, 0.49, 0.32], [0.77, 0.64, 0.44], [0.85, 0.74, 0.54], 0.40),
    "jungle": _pal([0.11, 0.37, 0.14], [0.19, 0.50, 0.18], [0.27, 0.44, 0.13], [0.05, 0.22, 0.08],
                   [0.55, 0.31, 0.17], [0.71, 0.45, 0.26], [0.81, 0.57, 0.36], 0.42),
    # Industrial
    "railyard": _pal([0.50, 0.45, 0.38], [0.60, 0.55, 0.46], [0.57, 0.44, 0.30], [0.33, 0.30, 0.26],
                     [0.32, 0.31, 0.31], [0.42, 0.41, 0.40], [0.49, 0.48, 0.47], 0.40),
    "factory": _pal([0.60, 0.58, 0.54], [0.70, 0.68, 0.64], [0.68, 0.42, 0.32], [0.40, 0.36, 0.34],
                    [0.27, 0.26, 0.26], [0.39, 0.37, 0.37], [0.47, 0.45, 0.44], 0.38),
    "smog": _pal([0.35, 0.32, 0.27], [0.46, 0.42, 0.35], [0.42, 0.42, 0.42], [0.22, 0.20, 0.18],
                 [0.50, 0.48, 0.46], [0.64, 0.62, 0.58], [0.73, 0.71, 0.67], 0.42),
    # Modern
    "suburb": _pal([0.34, 0.62, 0.23], [0.43, 0.72, 0.27], [0.50, 0.70, 0.30], [0.26, 0.50, 0.19],
                   [0.19, 0.20, 0.22], [0.26, 0.27, 0.29], [0.31, 0.32, 0.34], 0.30),
    "military": _pal([0.62, 0.60, 0.34], [0.72, 0.68, 0.42], [0.83, 0.75, 0.55], [0.47, 0.45, 0.27],
                     [0.21, 0.21, 0.21], [0.28, 0.28, 0.28], [0.33, 0.33, 0.33], 0.32),
    "metro": _pal([0.66, 0.65, 0.62], [0.74, 0.73, 0.70], [0.60, 0.62, 0.64], [0.45, 0.45, 0.46],
                  [0.17, 0.18, 0.20], [0.24, 0.25, 0.27], [0.29, 0.30, 0.32], 0.30),
    # Digital
    "neon": _pal([0.07, 0.07, 0.11], [0.11, 0.11, 0.16], [0.13, 0.10, 0.18], [0.03, 0.03, 0.06],
                 [0.15, 0.16, 0.23], [0.21, 0.22, 0.31], [0.27, 0.29, 0.39], 0.30),
    "satellite": _pal([0.86, 0.78, 0.62], [0.94, 0.88, 0.74], [0.80, 0.70, 0.54], [0.74, 0.64, 0.48],
                      [0.50, 0.51, 0.53], [0.63, 0.64, 0.66], [0.72, 0.73, 0.75], 0.42),
    "lab": _pal([0.86, 0.88, 0.90], [0.93, 0.95, 0.97], [0.84, 0.89, 0.93], [0.66, 0.70, 0.74],
                [0.40, 0.44, 0.49], [0.52, 0.56, 0.61], [0.60, 0.64, 0.69], 0.36),
    # Data Center
    "server": _pal([0.06, 0.07, 0.09], [0.10, 0.11, 0.14], [0.08, 0.10, 0.15], [0.02, 0.02, 0.03],
                   [0.34, 0.36, 0.40], [0.45, 0.47, 0.51], [0.54, 0.56, 0.60], 0.30),
    "cooling": _pal([0.55, 0.67, 0.78], [0.69, 0.79, 0.88], [0.86, 0.92, 0.97], [0.34, 0.44, 0.54],
                    [0.28, 0.32, 0.38], [0.38, 0.42, 0.48], [0.46, 0.50, 0.56], 0.40),
    "core": _pal([0.05, 0.04, 0.06], [0.10, 0.07, 0.10], [0.14, 0.06, 0.08], [0.02, 0.01, 0.02],
                 [0.15, 0.14, 0.17], [0.21, 0.20, 0.24], [0.27, 0.26, 0.30], 0.30),
})
# road look per era theme (era_spec THEMES[theme]["path"])
PATH_STYLE = {
    "highland": "dirt", "forge": "cinder", "bog": "planks", "olive": "flagstone", "coast": "marble",
    "acropolis": "marble", "farmland": "dirt", "castle": "cobble", "darkwood": "dirt", "harbor": "plank",
    "fortress": "dirt", "jungle": "dirt", "railyard": "rails", "factory": "cobble", "smog": "cobble",
    "suburb": "asphalt", "military": "asphalt", "metro": "asphalt", "neon": "neon", "satellite": "concrete",
    "lab": "steel", "server": "steel", "cooling": "steel", "core": "circuit",
}
P = PALETTES.get(theme, PALETTES["meadow"])
NEW = theme not in OLD_THEMES
style = PATH_STYLE.get(theme, "dirt")


# ---- small vector helpers for the era painters
def hash2(a, b, s=0.0):
    """Deterministic pseudo-random value in [0,1) per integer cell (a, b)."""
    v = np.sin(a * 127.1 + b * 311.7 + s * 74.7) * 43758.5453
    return v - np.floor(v)


def gline(d, w):
    """Soft line profile: 1 on the line, falling off over width w."""
    return np.exp(-(d / w) ** 2)


def gridd(u, period):
    """Distance from u to the nearest multiple of period."""
    f = u / period
    return np.abs(f - np.round(f)) * period


def at(arr, x, z):
    """Sample a full-res array at world coords (x, z)."""
    j = np.clip(((x - X0) * PX).astype(int), 0, w_px - 1)
    i = np.clip(((z - Z0) * PX).astype(int), 0, h_px - 1)
    return arr[i, j]


def tiles(sx, sz, offset=0.0, seed=0.0):
    """Tile grid: (distance to nearest seam, per-tile random, tile centre x, tile centre z)."""
    iz = np.floor(Z / sz)
    sh = (iz % 2) * sx * offset
    xo = X + sh
    ix = np.floor(xo / sx)
    fx, fz = xo / sx - ix, Z / sz - iz
    sd = np.minimum(np.minimum(fx, 1 - fx) * sx, np.minimum(fz, 1 - fz) * sz)
    return sd, hash2(ix, iz, seed), (ix + 0.5) * sx - sh, (iz + 0.5) * sz


def sqd(bx, bz, p=4.0):
    """Rounded-square distance (superellipse) around (bx, bz), for building / machine pads."""
    return (np.abs(X - bx) ** p + np.abs(Z - bz) ** p) ** (1.0 / p)


def manhattan(g, p_on, w, seed):
    """Circuit-board traces on a grid of pitch g: returns (core line, halo, via pads)."""
    k = np.round(Z / g); dz = np.abs(Z - k * g)
    kx = np.round(X / g); dx = np.abs(X - kx * g)
    onh = hash2(k, np.floor(X / g), seed) < p_on
    onv = hash2(kx, np.floor(Z / g), seed + 3) < p_on * 0.8
    core = np.maximum(gline(dz, w) * onh, gline(dx, w) * onv)
    halo = np.maximum(gline(dz, w * 5) * onh, gline(dx, w * 5) * onv)
    nd = np.hypot(X - kx * g, Z - k * g)
    via = (hash2(kx, k, seed + 7) < 0.3) * np.clip(1 - np.abs(nd - 0.07) / 0.03, 0, 1)
    return core, halo, via


MASK = {}   # per-theme masks the scatter pass reuses (heather, sand, tarmac, ...)

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
if theme not in OLD_THEMES:
    # measure "along" on polylines stretched 4 units past both ends, so plank/slab/rail patterns keep going
    # through the round end caps instead of collapsing to a single seam there
    def _stretch(pts):
        pts = np.array(pts, dtype=np.float64)
        d0 = (pts[0] - pts[1]) / np.hypot(*(pts[0] - pts[1]))
        d1 = (pts[-1] - pts[-2]) / np.hypot(*(pts[-1] - pts[-2]))
        return np.vstack([pts[0] + d0 * 4.0, pts, pts[-1] + d1 * 4.0])
    _d, along = poly_dist([_stretch(p) for p in paths])
    # outer corner wedges (closest road point is a vertex): "along" is constant there, so seams across the
    # road would smear into a solid wedge; cornr masks them out
    cornr = np.zeros(X.shape)
    for p in paths:
        for vx, vz in p[1:-1]:
            dv = np.hypot(X - vx, Z - vz)
            cornr = np.maximum(cornr, np.clip(1 - (dv - dist) / 0.03, 0, 1) * (dv > 0.02))
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
off_road = np.clip((dist - half - 0.3) / 0.5, 0, 1)   # keeps ground effects from bleeding under the road edge


def ground_new(col):
    """Era-theme ground pattern, painted over the palette noise before the outside-of-bounds darkening."""
    t = theme
    if t == "highland":   # heather patches + a few rocky outcrops
        heather = np.clip((noise(1.6, 3, 101) - 0.56) * 5, 0, 1)
        MASK["heather"] = heather
        hc = lerp(C([0.46, 0.30, 0.50]), C([0.62, 0.42, 0.64]), noise(0.3, 2, 102))
        col = lerp(col, hc, heather * 0.8)
        rock = np.clip((noise(1.1, 3, 103) - 0.74) * 6, 0, 1)
        col = lerp(col, C([0.56, 0.56, 0.52]) * (0.85 + 0.3 * n3)[..., None], rock * 0.7)
    elif t == "forge":    # coal dust drifts, rusty slag, faint ember cracks
        coal = np.clip((noise(2.2, 3, 104) - 0.55) * 4, 0, 1)
        col = lerp(col, C([0.05, 0.05, 0.05]), coal * 0.7)
        nc = noise(1.8, 3, 105)
        crack = np.exp(-((nc - 0.5) / 0.01) ** 2) * np.clip((noise(3.5, 2, 106) - 0.5) * 4, 0, 1)
        col = lerp(col, C([1.0, 0.45, 0.1]), np.clip(crack, 0, 1) * off_road * 0.75)
    elif t == "bog":      # moss cushions and dark peat puddles
        moss = np.clip((noise(1.4, 3, 107) - 0.55) * 4, 0, 1)
        col = lerp(col, C([0.40, 0.53, 0.18]) * (0.85 + 0.3 * n3)[..., None], moss * 0.7)
        pn = noise(2.0, 3, 108)
        pud = np.clip((pn - 0.68) * 14, 0, 1) * off_road
        MASK["puddle"] = pud
        water = lerp(C([0.24, 0.30, 0.22]), C([0.13, 0.19, 0.15]), np.clip((pn - 0.68) * 6, 0, 1))
        water = lerp(water, C([0.52, 0.62, 0.58]), np.clip((noise(0.3, 2, 109) - 0.72) * 5, 0, 1) * 0.5)
        col = lerp(col, C([0.20, 0.24, 0.12]), np.clip(1 - np.abs(pn - 0.675) / 0.02, 0, 1) * off_road * 0.6)
        col = lerp(col, water, pud)
    elif t == "olive":    # pale dirt clearings + sun-bleached streaks
        dirt = np.clip((noise(2.0, 3, 110) - 0.58) * 4, 0, 1)
        col = lerp(col, C([0.88, 0.80, 0.62]) * (0.92 + 0.16 * n3)[..., None], dirt * 0.8)
        streak = np.sin((X * 1.3 + Z * 0.4 + noise(3, 2, 111) * 5) * 4.0)
        col *= (0.97 + 0.04 * streak)[..., None]
    elif t == "coast":    # pale rock shelves on the sand
        rn = noise(1.0, 3, 112)
        rock = np.clip((rn - 0.70) * 8, 0, 1)
        rc = C([0.80, 0.80, 0.78]) * (0.86 + 0.28 * noise(0.35, 2, 113))[..., None]
        col = lerp(col, C([0.62, 0.56, 0.44]), np.clip(1 - np.abs(rn - 0.69) / 0.02, 0, 1) * 0.5)
        col = lerp(col, rc, rock)
        ripple = np.sin((X * 0.5 + Z * 1.6 + noise(3, 2, 114) * 5.0) * 3.2)
        col *= (0.97 + 0.035 * ripple)[..., None]
    elif t == "acropolis":   # weathered travertine paving, grass in the joints and where slabs are gone
        sd, h, cx, cz = tiles(1.3, 0.9, 0.37, 1)
        cover = at(noise(3.0, 3, 115), cx, cz) + (hash2(np.floor(cx), np.floor(cz), 2) - 0.5) * 0.25
        paved = (cover > 0.47) & (h > 0.12)
        slab = lerp(C([0.80, 0.73, 0.58]), C([0.88, 0.83, 0.70]), h) * (0.94 + 0.12 * n3)[..., None]
        slab = lerp(slab, C([0.64, 0.58, 0.46]), np.clip((noise(0.5, 2, 116) - 0.6) * 3, 0, 1) * 0.6)
        slab *= (0.84 + 0.16 * np.clip(sd / 0.09, 0, 1))[..., None]
        joint = np.clip(1 - (sd - 0.035) / 0.04, 0, 1)
        slab = lerp(slab, col * 0.85, joint)
        MASK["paved"] = paved
        col = np.where(paved[..., None], slab, col)
    elif t == "farmland":    # patchwork of fields edged by hedgerows
        ca, sa = np.cos(0.22), np.sin(0.22)
        warp = (noise(3, 2, 117) - 0.5) * 0.9
        u = X * ca + Z * sa + warp
        v = -X * sa + Z * ca + warp * 0.6
        iu = np.floor(u / 5.4)
        iv = np.floor((v + (iu % 2) * 1.9) / 3.9)
        fu, fv = u / 5.4 - iu, (v + (iu % 2) * 1.9) / 3.9 - iv
        h = hash2(iu, iv, 2)
        stripe_u = np.sin(v * 9.0)
        stripe_v = np.sin(u * 9.0)
        stripes = np.where(hash2(iu, iv, 3) < 0.5, stripe_u, stripe_v)
        pasture = C([0.38, 0.62, 0.23])
        light = C([0.52, 0.72, 0.30])
        wheat = C([0.88, 0.75, 0.36])
        plow = C([0.55, 0.40, 0.24])
        fc = np.where((h < 0.3)[..., None], pasture, np.where((h < 0.52)[..., None], light,
                      np.where((h < 0.78)[..., None], wheat, plow)))
        amp = np.where(h < 0.52, 0.03, np.where(h < 0.78, 0.06, 0.12))
        fc = fc * (1 + amp * stripes)[..., None] * (0.93 + 0.14 * n3)[..., None]
        MASK["wheat"] = (h >= 0.52) & (h < 0.78)
        col = lerp(col, fc, np.full(X.shape, 0.9))
        bd = np.minimum(np.minimum(fu, 1 - fu) * 5.4, np.minimum(fv, 1 - fv) * 3.9)
        hedge = np.clip(1 - (bd - 0.07 - noise(0.3, 2, 118) * 0.1) / 0.05, 0, 1)
        col = lerp(col, C([0.16, 0.34, 0.12]) * (0.8 + 0.4 * n3)[..., None], hedge * 0.9)
        col *= (1 - 0.25 * np.clip(1 - np.abs(bd - 0.22) / 0.08, 0, 1) * (1 - hedge))[..., None]
    elif t == "castle":      # worn cobbled yards in the trampled grass
        cob = np.clip((noise(2.6, 3, 119) - 0.6) * 5, 0, 1)
        sd, h, cx, cz = tiles(0.34, 0.28, 0.5, 4)
        stone = C([0.55, 0.54, 0.50]) * (0.88 + 0.18 * h)[..., None]
        stone = lerp(stone, col * 0.8, np.clip(1 - (sd - 0.015) / 0.035, 0, 1))
        cob *= np.clip((noise(0.4, 2, 151) - 0.25) * 3, 0, 1)    # stones missing here and there
        MASK["cobble"] = cob
        col = lerp(col, stone, cob * 0.75)
        mud = np.clip((noise(1.5, 3, 120) - 0.6) * 4, 0, 1)
        col = lerp(col, C([0.42, 0.34, 0.22]), mud * 0.45)
    elif t == "darkwood":    # leaf litter, moss and roots
        litter = noise(0.45, 2, 121)
        col = lerp(col, C([0.33, 0.22, 0.11]), np.clip((litter - 0.55) * 3, 0, 1) * 0.55)
        moss = np.clip((noise(1.3, 3, 122) - 0.6) * 4, 0, 1)
        col = lerp(col, C([0.22, 0.36, 0.13]), moss * 0.5)
        rn = noise(1.4, 3, 123)
        root = np.exp(-((rn - 0.5) / 0.012) ** 2) * np.clip((noise(2.5, 2, 124) - 0.45) * 4, 0, 1)
        col = lerp(col, C([0.20, 0.13, 0.07]), np.clip(root, 0, 1) * off_road * 0.85)
    elif t == "harbor":      # sandy grass, more sand towards the sea
        sea_near = np.clip(1 - (rdist - rhalf) / 4.0, 0, 1) if rivers else np.zeros(X.shape)
        sand = np.clip((noise(1.6, 3, 125) - 0.62 + sea_near * 0.45) * 4, 0, 1)
        MASK["sand"] = sand
        col = lerp(col, C([0.88, 0.80, 0.58]) * (0.92 + 0.16 * n3)[..., None], sand * 0.9)
    elif t == "fortress":    # packed dirt and trampled grass
        dirt = np.clip((noise(2.0, 3, 126) - 0.5) * 3.5, 0, 1)
        MASK["dirt"] = dirt
        col = lerp(col, C([0.60, 0.48, 0.31]) * (0.9 + 0.2 * n3)[..., None], dirt * 0.85)
        track = np.sin((X * 0.3 - Z * 1.0 + noise(3, 2, 127) * 4) * 6.0)
        col *= (1 - 0.05 * np.clip(track - 0.6, 0, 1) * dirt)[..., None]
    elif t == "jungle":      # big leaf mottling and dark undergrowth
        leaf = noise(0.6, 3, 128)
        col = lerp(col, C([0.30, 0.58, 0.20]), np.clip((leaf - 0.6) * 4, 0, 1) * 0.45)
        under = np.clip((noise(1.8, 3, 129) - 0.58) * 4, 0, 1)
        col = lerp(col, C([0.05, 0.22, 0.08]), under * 0.6)
        mud = np.clip((noise(2.2, 3, 130) - 0.7) * 5, 0, 1)
        col = lerp(col, C([0.40, 0.28, 0.16]), mud * 0.5)
    elif t == "railyard":    # ballast gravel, dirt, oil stains
        grit = noise(0.07, 1, 131)
        col *= (0.86 + 0.28 * grit)[..., None]
        on = noise(1.3, 3, 132)
        oil = np.clip((on - 0.72) * 9, 0, 1) * off_road
        col = lerp(col, C([0.62, 0.40, 0.52]), np.clip(1 - np.abs(on - 0.715) / 0.012, 0, 1) * off_road * 0.25)
        col = lerp(col, C([0.10, 0.09, 0.10]), oil * 0.85)
        dirt = np.clip((noise(2.4, 3, 133) - 0.55) * 4, 0, 1)
        col = lerp(col, C([0.52, 0.40, 0.27]), dirt * 0.4)
    elif t == "factory":     # cracked concrete slabs and brick dust
        sd, h, cx, cz = tiles(2.6, 2.6, 0.0, 5)
        col *= (0.94 + 0.1 * h)[..., None]
        col *= (1 - 0.45 * gline(sd, 0.025))[..., None]
        dust = np.clip((noise(1.8, 3, 134) - 0.56) * 4, 0, 1)
        col = lerp(col, C([0.66, 0.38, 0.28]) * (0.9 + 0.2 * n3)[..., None], dust * 0.65)
        cn = noise(0.9, 3, 135)
        crack = np.exp(-((cn - 0.5) / 0.008) ** 2) * np.clip((noise(2, 2, 136) - 0.5) * 4, 0, 1)
        col *= (1 - 0.55 * np.clip(crack, 0, 1) * off_road)[..., None]
    elif t == "smog":        # soot-dark mud and grey puddles
        soot = np.clip((noise(2.0, 3, 137) - 0.58) * 4, 0, 1)
        col = lerp(col, C([0.20, 0.18, 0.16]), soot * 0.55)
        pn = noise(1.2, 3, 138)
        pud = np.clip((pn - 0.69) * 14, 0, 1) * off_road
        MASK["puddle"] = pud
        water = lerp(C([0.48, 0.50, 0.52]), C([0.30, 0.31, 0.33]), np.clip((pn - 0.69) * 6, 0, 1))
        water = lerp(water, C([0.70, 0.72, 0.74]), np.clip((noise(0.4, 2, 139) - 0.7) * 4, 0, 1) * 0.4)
        col = lerp(col, C([0.20, 0.17, 0.14]), np.clip(1 - np.abs(pn - 0.685) / 0.025, 0, 1) * off_road * 0.6)
        col = lerp(col, water, pud)
    elif t == "suburb":      # mown lawns: each lot striped its own way
        iu, iv = np.floor((X + 0.3) / 5.2), np.floor((Z + 0.2) / 4.3)
        hz = hash2(iu, iv, 6)
        stripe = np.where(hz < 0.5, np.sin(X * np.pi / 0.7), np.sin(Z * np.pi / 0.7))
        col *= (1 + 0.035 * np.sign(stripe) * np.clip(np.abs(stripe) * 4, 0, 1))[..., None]
        col *= (0.96 + 0.08 * hz)[..., None]
    elif t == "military":    # dry grass, sand and old tarmac slabs
        sand = np.clip((noise(2.0, 3, 140) - 0.55) * 4, 0, 1)
        col = lerp(col, C([0.84, 0.76, 0.56]) * (0.92 + 0.16 * n3)[..., None], sand * 0.75)
        bi, bj = np.floor((X + 2.0) / 5.0), np.floor((Z + 1.0) / 3.6)   # old concrete aprons
        fx, fz = (X + 2.0) / 5.0 - bi, (Z + 1.0) / 3.6 - bj
        bd = np.minimum(np.minimum(fx, 1 - fx) * 5.0, np.minimum(fz, 1 - fz) * 3.6)
        tar = (hash2(bi, bj, 8) < 0.22) & (bd > 0.35) & (edge > -1.0)
        sd, h, cx, cz = tiles(1.25, 1.2, 0.0, 7)
        tc = C([0.50, 0.50, 0.47]) * (0.95 + 0.06 * h)[..., None] * (0.92 + 0.16 * n3)[..., None]
        tc = lerp(tc, C([0.30, 0.30, 0.29]), np.clip((noise(0.6, 2, 141) - 0.6) * 3, 0, 1) * 0.5)
        tc *= (1 - 0.35 * gline(sd, 0.02))[..., None]
        tc *= (1 - 0.3 * gline(bd - 0.35, 0.04))[..., None]
        tc = lerp(tc, C([0.92, 0.78, 0.25]), gline(np.abs(fz - 0.5) * 3.6, 0.03) * (bd > 0.7) * 0.8)
        MASK["tarmac"] = tar
        col = np.where(tar[..., None], tc, col)
    elif t == "metro":       # plaza paving with small parks
        sd, h, cx, cz = tiles(1.5, 1.5, 0.0, 9)
        col *= (0.95 + 0.07 * h)[..., None]
        col *= (1 - 0.3 * gline(sd, 0.02))[..., None]
        bi, bj = np.floor((X + 1.0) / 4.5), np.floor((Z + 0.5) / 3.5)
        fx, fz = (X + 1.0) / 4.5 - bi, (Z + 0.5) / 3.5 - bj
        bd = np.minimum(np.minimum(fx, 1 - fx) * 4.5, np.minimum(fz, 1 - fz) * 3.5)
        park = hash2(bi, bj, 10) < 0.28
        grass = lerp(C([0.33, 0.56, 0.22]), C([0.44, 0.66, 0.27]), noise(0.8, 2, 142)) * (0.92 + 0.16 * n3)[..., None]
        pc = np.where((bd > 0.32)[..., None], grass, C([0.80, 0.79, 0.76]))
        pc = np.where((bd < 0.18)[..., None], col, pc)
        MASK["park"] = park & (bd > 0.32)
        col = np.where(park[..., None], pc, col)
    elif t == "neon":        # asphalt grain; the glowing grid is added after the outside fade
        col *= (0.9 + 0.2 * noise(0.08, 1, 143))[..., None]
    elif t == "satellite":   # pale desert with long sand ripples
        ripple = np.sin((X * 1.6 + Z * 0.5 + noise(3, 2, 144) * 6.0) * 3.0)
        col *= (0.965 + 0.045 * ripple)[..., None]
        hard = np.clip((noise(2.4, 3, 145) - 0.6) * 4, 0, 1)
        col = lerp(col, C([0.82, 0.72, 0.58]), hard * 0.5)
    elif t == "lab":         # white tiles, faint light seams
        sd, h, cx, cz = tiles(1.25, 1.25, 0.0, 11)
        col = lerp(P["ground_b"], P["ground_a"], np.clip(h * 0.6 + n1 * 0.4 - 0.2, 0, 1))
        col *= (0.98 + 0.03 * n3)[..., None]
        col = lerp(col, C([0.70, 0.76, 0.82]), gline(sd, 0.018) * 0.8)
    elif t == "server":      # black tiles, perforated vent tiles
        sd, h, cx, cz = tiles(1.25, 1.25, 0.0, 12)
        col = lerp(P["ground_a"], P["ground_b"], np.clip(h * 0.7 + n1 * 0.5 - 0.2, 0, 1))
        vent = (h < 0.16) & (sd > 0.1)
        dots = (gridd(X, 0.14) < 0.035) & (gridd(Z, 0.14) < 0.035)
        col = np.where((vent & dots)[..., None], C([0.20, 0.23, 0.28]), col)
        col *= (1 - 0.6 * gline(sd, 0.03))[..., None]
    elif t == "cooling":     # steel floor grating, frosted over in drifts
        bars = (gridd(X, 0.24) < 0.045) | (gridd(Z, 0.24) < 0.045)
        col = col * np.where(bars, 1.05, 0.86)[..., None]
        frame = np.minimum(gridd(X, 2.4), gridd(Z, 2.4))
        col = lerp(col, C([0.52, 0.60, 0.70]), np.clip(1 - (frame - 0.05) / 0.03, 0, 1) * 0.9)
        frost = np.clip((noise(1.5, 3, 146) - 0.5) * 3, 0, 1)
        col = lerp(col, C([0.90, 0.95, 0.99]) * (0.95 + 0.1 * n3)[..., None], frost * 0.65)
        MASK["frost"] = frost
    elif t == "core":        # dark glass with reflections; traces added after the outside fade
        sd, h, cx, cz = tiles(2.0, 2.0, 0.0, 13)
        col *= (0.85 + 0.3 * h)[..., None]
        sheen = np.clip(np.sin((X * 0.45 + Z * 0.8) * 1.4 + noise(4, 2, 147) * 2), 0, 1) ** 6
        col = lerp(col, C([0.24, 0.20, 0.28]), sheen * 0.35)
        col *= (1 - 0.5 * gline(sd, 0.02))[..., None]
    return col


def glow_new(col):
    """Light-emitting ground detail (neon grid, circuit traces), added after the outside fade."""
    fade = (1 - outside * 0.75)[..., None]
    if theme == "neon":
        gl = np.minimum(gridd(X, 2.0), gridd(Z, 2.0))
        mag = (gridd(X, 8.0) < 0.1) | (gridd(Z, 8.0) < 0.1)
        hue = np.where(mag[..., None], C([1.0, 0.25, 0.85]), C([0.15, 0.85, 1.0]))
        k = (0.55 + 0.45 * noise(5, 2, 148))
        col = col + hue * (gline(gl, 0.022) * 0.8 + gline(gl, 0.14) * 0.18)[..., None] * k[..., None] * fade
    elif theme == "core":
        core, halo, via = manhattan(1.1, 0.33, 0.025, 20)
        k = (0.5 + 0.5 * noise(4, 2, 149)) * off_road
        col = col + C([0.9, 0.08, 0.06]) * (core * 0.55 + halo * 0.12 + via * 0.6)[..., None] * k[..., None] * fade
    elif theme == "server":
        sd, h, cx, cz = tiles(1.25, 1.25, 0.0, 12)
        lit = (hash2(np.floor(X / 5), np.floor(Z / 5), 14) < 0.55)
        k = np.where(lit, 1.0, 0.35) * (0.6 + 0.4 * noise(3, 2, 150))
        col = col + C([0.15, 0.45, 1.0]) * (gline(sd, 0.018) * 0.55 + gline(sd, 0.1) * 0.1)[..., None] * k[..., None] * fade
    elif theme == "lab":
        sd, h, cx, cz = tiles(5.0, 5.0, 0.0, 15)
        col = col + C([0.10, 0.30, 0.34]) * (gline(sd, 0.03) * 0.6)[..., None] * fade
    return col


if NEW:
    col = ground_new(col)
    keep = {"lab": 0.55, "server": 0.6, "neon": 0.6, "core": 0.6, "cooling": 0.45, "metro": 0.4,
            "factory": 0.35, "farmland": 0.3}.get(theme, 0.0)
    out_col = P["outside"] * (0.85 + 0.3 * n2)[..., None]
    out_col = lerp(out_col, col * 0.62, np.full(X.shape, keep))
    col = lerp(col, out_col, outside)
    col = glow_new(col)
else:
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
# era themes: (shallow, deep, bank, bank width, foam) -- sea inlets get a sandy beach and surf
WATER = {
    "highland": (C([0.42, 0.62, 0.66]), C([0.14, 0.32, 0.46]), C([0.50, 0.49, 0.44]), 0.55, 0.35),
    "coast": (C([0.30, 0.82, 0.80]), C([0.06, 0.44, 0.66]), C([0.80, 0.70, 0.50]), 1.0, 0.7),
    "harbor": (C([0.26, 0.72, 0.74]), C([0.05, 0.30, 0.55]), C([0.86, 0.77, 0.55]), 1.1, 0.7),
}
if rivers and NEW:
    shallow, deep, bank_c, bank_w, foam_k = WATER.get(theme, WATER["highland"])
    bank = np.clip(1 - (rdist - rhalf) / bank_w, 0, 1) * (rdist > rhalf - 0.1)
    col = lerp(col, bank_c * (0.9 + 0.2 * n3)[..., None], np.clip(bank * 1.4, 0, 1) * 0.9)
    wet = np.clip(1 - (rdist - rhalf) / 0.3, 0, 1) * (rdist > rhalf - 0.1)
    col *= (1 - 0.18 * wet)[..., None]
    depth = np.clip((rhalf - rdist) / np.maximum(rhalf, 0.01), 0, 1)
    water = lerp(shallow, deep, depth ** 0.7)
    rip = noise(0.4, 2, 71)
    water = lerp(water, C([0.75, 0.93, 0.95]), np.clip((rip - 0.68) * 4, 0, 1) * 0.45)
    if theme == "highland":   # cold stream: pebbles showing through the shallows
        peb = noise(0.12, 1, 72)
        water = lerp(water, C([0.56, 0.62, 0.60]), np.clip((peb - 0.6) * 4, 0, 1) * (1 - depth) * 0.5)
    foam = gline(rdist - rhalf + 0.1 + (noise(0.5, 2, 73) - 0.5) * 0.15, 0.07) * foam_k
    water = lerp(water, C([0.96, 0.98, 1.0]), np.clip(foam, 0, 1))
    col = lerp(col, water, np.clip((rhalf - rdist) / 0.12, 0, 1))
elif rivers:
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


def road_new(col, path_col):
    """Era road surfaces. Returns (ground col with any kerb painted, road surface colour)."""
    pc = path_col
    if style in ("asphalt", "neon", "steel", "circuit", "concrete", "marble"):   # crisp man-made edge, no jag
        global inside, shadow
        inside = np.clip((half - dist) / 0.05, 0, 1)
        shadow = np.clip(1 - np.abs(dist - half) / 0.2, 0, 1) * P["lip"]
    if style == "dirt":       # wheel ruts
        rut = gline(dist - 0.42 + (noise(1.0, 2, 160) - 0.5) * 0.1, 0.08)
        pc = pc * (1 - 0.16 * rut)[..., None]
        if theme == "farmland":
            pc = lerp(pc, C([0.45, 0.60, 0.26]), gline(dist, 0.1) * np.clip((noise(0.6, 2, 161) - 0.35) * 2, 0, 1) * 0.6)
    elif style == "cinder":   # dark grit with glints
        grit = noise(0.06, 1, 162)
        pc = pc * (0.82 + 0.36 * grit)[..., None]
        pc = lerp(pc, C([0.24, 0.21, 0.19]), np.clip((noise(0.5, 2, 163) - 0.6) * 3, 0, 1) * 0.5)
    elif style == "planks":   # boardwalk: planks laid across, stringers along the sides
        pw = 0.34
        pid = np.floor(along / pw)
        fa = along / pw - pid
        hp_ = hash2(pid, 0, 21)
        wood = pc * (0.82 + 0.3 * hp_)[..., None]
        grain = np.sin(dist * 38 + hp_ * 20 + noise(0.5, 2, 164) * 6)
        wood *= (0.96 + 0.04 * grain)[..., None]
        wood *= (1 - 0.55 * np.clip(1 - np.minimum(fa, 1 - fa) * pw / 0.035, 0, 1) * (1 - cornr))[..., None]
        nail = gline(np.hypot((fa - 0.5) * pw, np.abs(dist - (half - 0.2))), 0.025) * (1 - cornr)
        wood = lerp(wood, C([0.22, 0.18, 0.15]), nail * 0.8)
        side = np.clip((dist - (half - 0.12)) / 0.03, 0, 1)
        pc = lerp(wood, C([0.36, 0.24, 0.13]), side)
    elif style == "plank":    # dock: boards run along the road, staggered end joints
        bw = 0.3
        bi = np.floor(dist / bw)
        fl = dist / bw - bi
        off = hash2(bi, 1, 22) * 3.0
        bj = np.floor((along + off) / 2.4)
        fa = (along + off) / 2.4 - bj
        hb = hash2(bi, bj, 23)
        wood = pc * (0.84 + 0.28 * hb)[..., None]
        wood *= (0.97 + 0.03 * np.sin(along * 30 + hb * 30))[..., None]
        seam = np.clip(1 - np.minimum(fl, 1 - fl) * bw / 0.03, 0, 1) * (dist > 0.05)
        joint = np.clip(1 - np.minimum(fa, 1 - fa) * 2.4 / 0.03, 0, 1) * (1 - cornr)
        pc = wood * (1 - 0.6 * np.maximum(seam, joint))[..., None]
    elif style == "flagstone":
        rw = 0.43
        ri = np.floor(dist / rw)
        fl = dist / rw - ri
        sl = 0.62
        u = along + ri * 0.31 + (noise(0.8, 2, 165) - 0.5) * 0.12
        si = np.floor(u / sl)
        fa = u / sl - si
        hs = hash2(si, ri, 24)
        sd = np.minimum(np.minimum(fa, 1 - fa) * sl + cornr, np.where(ri > 0, np.minimum(fl, 1 - fl) * rw, (1 - fl) * rw))
        stone = pc * (0.86 + 0.24 * hs)[..., None] * (0.9 + 0.1 * np.clip(sd / 0.1, 0, 1))[..., None]
        stone = lerp(stone, C([0.68, 0.62, 0.48]), np.clip(hs - 0.75, 0, 1) * 1.2)
        pc = lerp(stone, P["path_dark"] * 0.7, np.clip(1 - (sd - 0.012) / 0.03, 0, 1))
    elif style == "marble":   # big polished slabs, veined, with a darker kerb
        sl = 1.1
        u = along + (dist > 0.42) * 0.55
        si = np.floor(u / sl)
        fa = u / sl - si
        lane = np.floor(dist / 0.42)
        hs = hash2(si, lane, 25)
        slab = pc * (0.95 + 0.08 * hs)[..., None]
        vn = noise(0.7, 3, 166)
        slab = lerp(slab, C([0.64, 0.64, 0.70]), np.exp(-((vn - 0.5) / 0.01) ** 2) * 0.35)
        sd = np.minimum(np.minimum(fa, 1 - fa) * sl + cornr, gridd(dist, 0.42))
        slab *= (1 - 0.3 * np.clip(1 - (sd - 0.01) / 0.025, 0, 1))[..., None]
        kerb = C([0.70, 0.66, 0.58]) if theme == "acropolis" else C([0.66, 0.70, 0.76])
        pc = lerp(slab, kerb, np.clip((dist - (half - 0.16)) / 0.02, 0, 1))
    elif style == "cobble":
        cs = 0.27
        li = np.floor(dist / cs)
        fl = dist / cs - li
        u = along + li * cs * 0.5
        ai = np.floor(u / cs)
        fa = u / cs - ai
        hc = hash2(ai, li, 26)
        r = np.hypot(fa - 0.5, fl - 0.5) * 2
        stone = pc * (0.8 + 0.35 * hc)[..., None] * (1.06 - 0.3 * r ** 2)[..., None]
        if theme == "factory":   # granite setts with a hint of brick
            stone = lerp(stone, C([0.45, 0.30, 0.26]), (hc > 0.8) * 0.5)
        mortar = P["path_dark"] * 0.55
        pc = lerp(stone, mortar, np.clip((r - 0.86) / 0.12, 0, 1))
    elif style == "rails":
        grit = noise(0.06, 1, 167)
        pc = pc * (0.8 + 0.4 * grit)[..., None]
    elif style == "asphalt":
        pc = pc * (0.9 + 0.2 * noise(0.07, 1, 168))[..., None]
        patch = np.clip((noise(1.5, 3, 169) - 0.65) * 5, 0, 1)
        pc = lerp(pc, P["path_dark"] * 0.85, patch * 0.5)
        if theme in ("suburb", "metro"):   # concrete sidewalk / kerb just outside the road
            sw = 0.3 if theme == "metro" else 0.22
            walk = np.clip((half + sw - dist) / 0.03, 0, 1) * (dist > half - 0.02)
            slab = C([0.80, 0.79, 0.76]) * (1 - 0.25 * gline(gridd(along, 0.6) + cornr, 0.015))[..., None]
            slab = slab * (0.95 + 0.08 * noise(0.3, 2, 170))[..., None]
            col = lerp(col, slab, walk)
            col = lerp(col, C([0.62, 0.61, 0.59]), gline(dist - half, 0.025) * 0.8)
    elif style == "neon":
        pc = pc * (0.9 + 0.2 * noise(0.07, 1, 171))[..., None]
        pc = lerp(pc, C([0.30, 0.34, 0.46]), gline(gridd(along, 1.0) + cornr, 0.015) * 0.6 * (dist < half - 0.2))
    elif style == "concrete":
        sl = 1.4
        si = np.floor(along / sl)
        hs = hash2(si, np.floor(dist / 0.42), 27)
        pc = pc * (0.94 + 0.1 * hs)[..., None] * (0.95 + 0.08 * noise(0.4, 2, 172))[..., None]
        jt = np.minimum(gridd(along, sl) + cornr, gridd(dist, 0.85))
        pc *= (1 - 0.35 * gline(jt, 0.018))[..., None]
        pc = lerp(pc, C([0.80, 0.80, 0.80]), np.clip((dist - (half - 0.12)) / 0.02, 0, 1) * 0.8)
    elif style == "steel":    # riveted diamond-plate panels
        sl = 1.0
        si = np.floor(along / sl)
        hs = hash2(si, np.floor(dist / 0.42), 28)
        plate = pc * (0.93 + 0.12 * hs)[..., None]
        diamond = np.sin(along * 26 + dist * 26) * np.sin(along * 26 - dist * 26)
        plate *= (1 + 0.05 * np.clip(diamond * 3 - 2, 0, 1))[..., None]
        sd = np.minimum(gridd(along, sl) + cornr, gridd(dist, 0.85))
        plate *= (1 - 0.5 * gline(sd, 0.02))[..., None]
        rv = np.minimum(gridd(along + 0.12, sl), gridd(along - 0.12, sl)) + cornr   # rivets either side of each seam
        rivet = gline(np.hypot(rv, gridd(dist, 0.85) - 0.12), 0.03)
        plate = lerp(plate, P["path_light"] * 1.25, rivet * 0.8)
        if theme == "cooling":
            fr = np.clip((noise(0.6, 3, 173) - 0.55) * 3, 0, 1) * np.clip((dist - 0.3) / 0.4, 0, 1)
            plate = lerp(plate, C([0.82, 0.90, 0.97]), fr * 0.6)
        kerb = {"lab": C([0.86, 0.88, 0.90]), "server": C([0.20, 0.22, 0.26]),
                "cooling": C([0.24, 0.28, 0.34])}.get(theme, C([0.3, 0.3, 0.3]))
        pc = lerp(plate, kerb, np.clip((dist - (half - 0.1)) / 0.02, 0, 1))
    elif style == "circuit":
        pc = pc * (0.9 + 0.2 * noise(0.08, 1, 174))[..., None]
        sd = gridd(along, 1.6) + cornr
        pc *= (1 - 0.4 * gline(sd, 0.02))[..., None]
    return col, pc


def road_overlay_new(col):
    """Road markings drawn after the road edge band: rails, painted lines, glowing strips."""
    ins = inside[..., None]
    if style == "rails":      # sleepers + two steel rails
        sp = 0.42
        sid = np.floor(along / sp)
        fa = along / sp - sid
        sleeper = (fa < 0.42) & (dist < 0.62) & (cornr < 0.5)
        wood = C([0.38, 0.26, 0.16]) * (0.8 + 0.35 * hash2(sid, 2, 29))[..., None]
        col = lerp(col, wood, (sleeper * inside).astype(float) * 0.92)
        col *= (1 - 0.35 * (gline(dist - 0.62, 0.03) * (fa < 0.42)) * inside)[..., None]
        for off in (0.34,):
            rd = dist - off
            col *= (1 - 0.4 * gline(rd - 0.06, 0.03) * inside)[..., None]   # rail shadow
            col = lerp(col, C([0.50, 0.52, 0.55]), gline(rd, 0.045) * inside * 0.95)
            col = lerp(col, C([0.88, 0.89, 0.92]), gline(rd + 0.012, 0.014) * inside * 0.9)
    elif style == "asphalt":
        dash = (gridd(along, 1.0) > 0.25) * 1.0
        cl = C([0.96, 0.80, 0.22]) if theme == "suburb" else C([0.95, 0.95, 0.92])
        wear = np.clip(noise(0.3, 2, 175) * 1.6 - 0.2, 0.4, 1)
        col = lerp(col, cl, gline(dist, 0.035) * dash * inside * wear * 0.95)
        el = C([0.95, 0.95, 0.92]) if theme != "military" else C([0.95, 0.82, 0.25])
        col = lerp(col, el, gline(dist - (half - 0.13), 0.022) * inside * wear * 0.85)
    elif style == "neon":
        e = gline(dist - (half - 0.1), 0.025)
        halo = gline(dist - (half - 0.1), 0.16)
        spill = gline(np.maximum(dist - half, 0), 0.35) * (dist > half)
        col = col + C([0.15, 0.85, 1.0]) * (e * 0.9 + halo * 0.3 + spill * 0.2)[..., None]
        col = lerp(col, C([1.0, 1.0, 1.0]), e * 0.45)
        dash = (gridd(along, 1.2) < 0.22) * 1.0
        col = col + C([1.0, 0.2, 0.85]) * (gline(dist, 0.035) * dash * 0.9 + gline(dist, 0.12) * dash * 0.2)[..., None]
    elif style == "steel" and theme in ("lab", "server"):   # LED edge strips
        lc = C([0.20, 0.85, 1.0]) if theme == "lab" else C([0.20, 0.50, 1.0])
        e = gline(dist - (half - 0.2), 0.02)
        dash = np.clip(np.sin(along * np.pi / 0.25) * 3, 0, 1) if theme == "server" else 1.0
        col = lerp(col, lc, e * dash * inside * 0.9)
        col = col + lc * (gline(dist - (half - 0.2), 0.12) * 0.15 * dash * inside)[..., None]
    elif style == "circuit":
        red = C([1.0, 0.16, 0.08])
        e = gline(dist - (half - 0.1), 0.022)
        col = col + red * (e * 0.9 + gline(dist - (half - 0.1), 0.15) * 0.25)[..., None]
        col = lerp(col, C([1.0, 0.75, 0.6]), e * 0.4)
        for lane, off in enumerate((0.0, 0.42)):
            seg = np.floor(along / 1.3 + lane * 0.37)
            fa = along / 1.3 + lane * 0.37 - seg
            on = (hash2(seg, lane, 30) < 0.7) & (fa > 0.08) & (fa < 0.92)
            tr = gline(dist - off, 0.022) * on
            col = col + red * (tr * 0.75 + gline(dist - off, 0.1) * on * 0.15)[..., None] * ins
            pad = gline(np.hypot(np.minimum(np.abs(fa - 0.08), np.abs(fa - 0.92)) * 1.3 + cornr, dist - off), 0.05) * (hash2(seg, lane, 30) < 0.7)
            col = lerp(col, C([1.0, 0.55, 0.35]), pad * inside * 0.9)
    return col


if NEW:
    col, path_col = road_new(col, path_col)
col *= (1 - shadow * (1 - inside))[..., None]
if theme == "desert":   # paved flagstone road
    stones = (np.sin(along * 5.5) > 0.9) | (np.abs(np.sin((dist - jag) * 6.0)) < 0.08)
    path_col = path_col * np.where(stones, 0.8, 1.0)[..., None]
col = lerp(col, path_col, inside)
edge_band = np.clip(1 - np.abs(pd - (half - 0.08)) / 0.1, 0, 1) * 0.3
if NEW and style in ("asphalt", "neon", "steel", "circuit", "concrete", "marble"):
    edge_band = np.clip(1 - np.abs(dist - (half - 0.04)) / 0.06, 0, 1) * 0.3
col *= (1 - edge_band)[..., None]
if NEW:
    col = road_overlay_new(col)
if theme == "canyon":   # mine-cart rails down the middle of the road
    sleeper = (np.sin(along * 9.0) > 0.55) & (dist < 0.5)
    col = lerp(col, C([0.32, 0.2, 0.12]), (sleeper * inside).astype(float) * 0.8)
    rail = np.exp(-((dist - 0.32) ** 2) / (2 * 0.035 ** 2))
    col = lerp(col, C([0.3, 0.3, 0.32]), rail * inside * 0.95)
if rivers:   # wooden bridge where the road crosses water
    on_water = (rdist < rhalf + 0.15) & (dist < half + 0.1)
    if NEW:   # the bridge spans the full road width: grow the water mask by the road half-width first
        k = 2
        wet = (rdist < rhalf + 0.15)[::k, ::k]
        grown = wet.copy()
        for s_ in range(1, int((half + 0.1) * PX / k) + 1):
            grown[:, s_:] |= wet[:, :-s_]
            grown[:, :-s_] |= wet[:, s_:]
        wet = grown.copy()
        for s_ in range(1, int((half + 0.1) * PX / k) + 1):
            grown[s_:, :] |= wet[:-s_, :]
            grown[:-s_, :] |= wet[s_:, :]
        grown = np.repeat(np.repeat(grown, k, 0), k, 1)[:h_px, :w_px]
        on_water = grown & (dist < half + 0.1)
        if len(paths) == 1:   # square the bridge ends off: bridge every road slice whose centre touches water
            bins = np.floor(along / 0.05).astype(int)
            wet_bins = np.zeros(bins.max() + 2, bool)
            wet_bins[bins[grown & (dist < 0.1)]] = True
            on_water = wet_bins[bins] & (dist < half + 0.1)
    plank = C([0.56, 0.38, 0.2]) * (0.85 + 0.15 * noise(0.3, 2, 81))[..., None]
    plank *= np.where(np.sin(along * 14.0) > 0.85, 0.6, 1.0)[..., None]
    rail_edge = np.abs(dist - half) < 0.09
    plank = np.where(rail_edge[..., None], C([0.3, 0.19, 0.1]), plank)
    col = np.where(on_water[..., None], plank, col)


# ---- no-build zones
def ring(d, r, w):
    return np.clip(1 - np.abs(d - r) / w, 0, 1)


def hazard(bx, bz, d, r, w):
    """Yellow/black diagonal hazard stripes on a band of width w at distance r."""
    band = np.clip(1 - np.abs(d - r) / w, 0, 1) > 0.3
    stripe = np.sin((X - bx + Z - bz) * np.pi / 0.18) > 0
    return band, stripe


def blocker_new(col, kind, bx, bz, br, d, core, rim, depth):
    """Footprint painted under the 3D blocker props of the era themes."""
    t = theme
    if kind == "lake":
        if t == "suburb":     # backyard swimming pool
            dq = sqd(bx, bz, 5.0) / 1.0
            r0 = br * 0.82
            water = lerp(C([0.36, 0.84, 0.95]), C([0.12, 0.56, 0.86]), np.clip(1 - dq / r0, 0, 1) ** 0.6)
            cn = noise(0.35, 2, int(bx * 11 + 300) % 991)
            water = lerp(water, C([0.85, 0.97, 1.0]), np.exp(-((cn - 0.5) / 0.02) ** 2) * 0.55)
            water = lerp(water, C([0.10, 0.42, 0.70]), ring(dq, r0 - 0.08, 0.05) * 0.6)
            col = lerp(col, C([0.90, 0.89, 0.84]), np.clip((r0 + 0.32 - dq) / 0.03, 0, 1))
            col *= (1 - 0.25 * ring(dq, r0 + 0.33, 0.06))[..., None]
            return lerp(col, water, np.clip((r0 - dq) / 0.03, 0, 1))
        if t == "smog":       # oily grey puddle
            water = lerp(C([0.46, 0.47, 0.49]), C([0.24, 0.25, 0.27]), depth ** 0.7)
            sheen = noise(0.5, 2, int(bx * 5 + 310) % 991)
            water = lerp(water, C([0.55, 0.42, 0.60]), np.exp(-((sheen - 0.5) / 0.03) ** 2) * 0.35)
            water = lerp(water, C([0.42, 0.62, 0.55]), np.exp(-((sheen - 0.62) / 0.03) ** 2) * 0.25)
            col = lerp(col, C([0.20, 0.17, 0.14]), rim * (1 - core) * 0.85)
            return lerp(col, water, core)
        if t == "bog":        # black peat pool with duckweed
            water = lerp(C([0.22, 0.28, 0.18]), C([0.08, 0.13, 0.10]), depth ** 0.7)
            weed = np.clip((noise(0.25, 2, int(bx * 7 + 320) % 991) - 0.62) * 5, 0, 1) * (1 - depth ** 0.5)
            water = lerp(water, C([0.45, 0.60, 0.20]), weed * 0.8)
            col = lerp(col, C([0.26, 0.30, 0.14]), rim * (1 - core) * 0.85)
            return lerp(col, water, core)
        water = lerp(C([0.36, 0.60, 0.66]), C([0.10, 0.28, 0.44]), depth ** 0.7)   # cold hill tarn
        col = lerp(col, C([0.48, 0.47, 0.42]), rim * (1 - core) * 0.9)
        return lerp(col, water, core)
    if kind == "lava":        # molten slag pool with drifting crust
        lava = lerp(C([1.0, 0.48, 0.08]), C([1.0, 0.90, 0.45]), depth ** 1.4)
        crust = noise(0.4, 2, int(bz * 5 + 330) % 983)
        lava = lerp(lava, C([0.22, 0.10, 0.06]), np.clip((crust - 0.6) * 6, 0, 1) * 0.85 * (1 - depth))
        col = lerp(col, C([0.06, 0.04, 0.04]), rim * (1 - core) * 0.95)
        heat = np.clip(1 - (d - br) / 1.0, 0, 1) * (1 - core)
        col = lerp(col, C([0.75, 0.25, 0.06]), heat * 0.35)
        return lerp(col, lava, core)
    if kind == "slag":        # glassy black slag heap with rust and ember veins
        sn = noise(0.35, 2, int(bx * 3 + 340) % 991)
        slag = lerp(C([0.10, 0.09, 0.09]), C([0.30, 0.18, 0.12]), np.clip((sn - 0.5) * 3, 0, 1))
        vein = np.exp(-((sn - 0.42) / 0.015) ** 2) * depth
        slag = lerp(slag, C([1.0, 0.5, 0.12]), vein * 0.8)
        return lerp(col, slag, core * 0.95)
    if kind == "pit":         # neon: dark hole with a glowing rim
        hole = lerp(C([0.05, 0.04, 0.08]), C([0.0, 0.0, 0.0]), depth ** 0.5)
        col = lerp(col, hole, core)
        g = ring(d, br, 0.06)
        col = col + C([1.0, 0.25, 0.85]) * (g * 0.9 + ring(d, br, 0.35) * 0.25)[..., None]
        return col + C([0.15, 0.85, 1.0]) * (ring(d, br - 0.25, 0.04) * 0.6)[..., None] * core[..., None]
    if kind == "ice":         # frost bloom
        ice = lerp(C([0.86, 0.94, 1.0]), C([0.62, 0.82, 0.96]), depth ** 0.8)
        cr = noise(0.5, 2, int(bx * 3 + 350) % 991)
        ice = lerp(ice, C([1.0, 1.0, 1.0]), np.exp(-((cr - 0.5) / 0.01) ** 2) * 0.9)
        halo = np.clip(1 - (d - br) / 0.7, 0, 1) * (1 - core)
        col = lerp(col, C([0.92, 0.97, 1.0]), halo * 0.55)
        return lerp(col, ice, core)
    if kind == "crater":      # scorched ring with a raised dirt lip
        col = lerp(col, C([0.16, 0.13, 0.10]), np.clip(1 - (d - br) / 0.9, 0, 1) * (1 - core) * 0.45 *
                   (0.6 + 0.4 * np.abs(np.sin(np.arctan2(Z - bz, X - bx) * 7))))
        inner = lerp(C([0.36, 0.28, 0.20]), C([0.12, 0.10, 0.08]), depth ** 0.6)
        col = lerp(col, inner, core)
        return lerp(col, C([0.62, 0.50, 0.34]), ring(d, br * 0.92, 0.22) * 0.8)
    if kind == "coal":        # coal heap bed
        cn = noise(0.12, 1, int(bx * 5 + 360) % 991)
        coal = C([0.07, 0.07, 0.08]) * (0.7 + 0.8 * cn)[..., None]
        return lerp(col, coal, core * 0.95)
    if kind == "trees":       # shaded ground-cover under the canopy
        if t == "metro":      # tree planter: kerb + soil
            dq = sqd(bx, bz)
            col = lerp(col, C([0.70, 0.70, 0.68]), np.clip((br * 0.9 - dq) / 0.03, 0, 1))
            soil = C([0.30, 0.22, 0.15]) * (0.85 + 0.3 * n3)[..., None]
            soil = lerp(soil, C([0.30, 0.48, 0.18]), np.clip((noise(0.4, 2, 370) - 0.5) * 3, 0, 1) * 0.6)
            return lerp(col, soil, np.clip((br * 0.9 - 0.18 - dq) / 0.03, 0, 1))
        if t == "suburb":     # mulch ring
            mulch = C([0.42, 0.26, 0.15]) * (0.8 + 0.4 * noise(0.1, 1, 371))[..., None]
            return lerp(col, mulch, np.clip((br * 0.75 - d) / 0.1, 0, 1))
        shade = {"darkwood": C([0.07, 0.10, 0.06]), "jungle": C([0.04, 0.17, 0.06]),
                 "bog": C([0.18, 0.22, 0.10]), "olive": C([0.48, 0.42, 0.24])}.get(t, col * 0.0 + P["outside"])
        litter = (0.8 + 0.4 * noise(0.2, 2, int(bx * 9 + 380) % 991))[..., None]
        return lerp(col, shade * litter, core * 0.8)
    if kind in ("rocks", "stones"):
        bed = {"coast": C([0.78, 0.77, 0.74]), "olive": C([0.70, 0.66, 0.56]), "castle": C([0.44, 0.42, 0.40]),
               "harbor": C([0.40, 0.40, 0.42]), "highland": C([0.46, 0.46, 0.42])}.get(t, P["outside"])
        grav = (0.75 + 0.5 * noise(0.16, 2, int(bz * 9 + 390) % 991))[..., None]
        if kind == "stones":   # stone circle: trampled ring around a gravel heart
            col = lerp(col, C([0.62, 0.56, 0.40]), ring(d, br * 0.8, 0.3) * 0.7)
            return lerp(col, bed * grav, np.clip((br * 0.55 - d) / 0.1, 0, 1) * 0.8)
        return lerp(col, bed * grav, core * 0.85)
    if kind in ("ruins", "statue"):   # paved floor; marble for classical, mossy stone elsewhere
        if t in ("olive", "coast", "acropolis"):
            sd, h, cx, cz = tiles(0.7, 0.7, 0.5, 31)
            fl = C([0.90, 0.87, 0.80]) * (0.9 + 0.12 * h)[..., None]
            seam = C([0.52, 0.50, 0.42]) if t != "acropolis" else C([0.62, 0.60, 0.58])
            if t == "acropolis":
                fl = C([0.96, 0.95, 0.93]) * (0.93 + 0.07 * h)[..., None]
                col = lerp(col, C([0.55, 0.50, 0.42]), ring(d, br, 0.12) * 0.8)
        else:
            sd, h, cx, cz = tiles(0.6, 0.6, 0.5, 32)
            fl = C([0.46, 0.47, 0.44]) * (0.85 + 0.25 * h)[..., None]
            fl = lerp(fl, C([0.24, 0.40, 0.14]), np.clip((noise(0.5, 2, 400) - 0.5) * 3, 0, 1) * 0.6)
            seam = C([0.16, 0.24, 0.10])
        fl = lerp(fl, seam, np.clip(1 - (sd - 0.015) / 0.03, 0, 1))
        if kind == "statue":   # round plinth plaza with a ring of darker stone
            fl = lerp(fl, fl * 0.7, ring(d, br * 0.7, 0.07))
        broken = np.clip((noise(0.6, 2, int(bx * 5 + 410) % 991) - 0.66) * 6, 0, 1) * (d > br * 0.6)
        return lerp(col, fl, core * (1 - broken))
    if kind == "tents":       # trampled mud and straw
        mud = C([0.46, 0.36, 0.24]) * (0.85 + 0.3 * noise(0.2, 2, 420))[..., None]
        mud = lerp(mud, C([0.82, 0.70, 0.36]), np.clip((noise(0.15, 1, 421) - 0.7) * 4, 0, 1) * 0.6)
        return lerp(col, mud, core * 0.9)
    # square pads: buildings, machines, racks, crates, dishes, panels, tanks, pylons, pillars, wrecks
    dq = sqd(bx, bz) if kind in ("building", "machine", "rack", "crates", "panels") else d
    r0 = br * 0.92
    fill = np.clip((r0 - dq) / 0.04, 0, 1)
    if kind == "wreck":       # scorched debris field
        sc = C([0.08, 0.06, 0.07]) * (0.7 + 0.6 * noise(0.2, 2, int(bx * 5 + 430) % 991))[..., None]
        col = lerp(col, sc, core * 0.9)
        emb = np.clip((noise(0.15, 1, int(bz * 5 + 431) % 991) - 0.78) * 8, 0, 1) * core
        return col + C([1.0, 0.25, 0.05]) * (emb * 0.8)[..., None]
    if kind == "crates":
        if t == "harbor":     # dock planking
            wood = C([0.55, 0.40, 0.24]) * (0.85 + 0.25 * hash2(np.floor(Z / 0.3), 3, 33))[..., None]
            wood *= (1 - 0.5 * gline(gridd(Z, 0.3), 0.02))[..., None]
            col *= (1 - 0.35 * np.clip(1 - np.abs(dq - r0 - 0.06) / 0.1, 0, 1))[..., None]
            return lerp(col, wood, fill)
        yard = {"railyard": C([0.40, 0.34, 0.27]), "fortress": C([0.54, 0.44, 0.30]),
                "military": C([0.62, 0.56, 0.42])}.get(t, P["path_dark"])
        return lerp(col, yard * (0.88 + 0.24 * n3)[..., None], fill * 0.9)
    pads = {   # (fill colour, border colour, glow colour or None, hazard stripes)
        "factory": (C([0.50, 0.46, 0.44]), C([0.36, 0.30, 0.28]), None, True),
        "smog": (C([0.30, 0.28, 0.27]), C([0.20, 0.18, 0.17]), None, False),
        "suburb": (C([0.78, 0.77, 0.74]), C([0.62, 0.61, 0.58]), None, False),
        "metro": (C([0.52, 0.53, 0.55]), C([0.38, 0.39, 0.41]), None, False),
        "farmland": (C([0.56, 0.45, 0.30]), C([0.44, 0.34, 0.22]), None, False),
        "military": (C([0.56, 0.56, 0.54]), C([0.40, 0.40, 0.39]), None, True),
        "satellite": (C([0.76, 0.76, 0.75]), C([0.56, 0.56, 0.56]), None, False),
        "lab": (C([0.76, 0.80, 0.84]), C([0.60, 0.64, 0.70]), C([0.2, 0.85, 1.0]), False),
        "server": (C([0.14, 0.15, 0.18]), C([0.24, 0.26, 0.30]), C([0.2, 0.5, 1.0]), False),
        "cooling": (C([0.42, 0.48, 0.56]), C([0.28, 0.33, 0.40]), C([0.5, 0.85, 1.0]), False),
        "neon": (C([0.10, 0.10, 0.15]), C([0.05, 0.05, 0.08]), C([0.15, 0.85, 1.0]), False),
        "core": (C([0.10, 0.08, 0.10]), C([0.05, 0.03, 0.05]), C([1.0, 0.15, 0.08]), False),
    }
    fc, bc, glow, haz = pads.get(t, (P["path"], P["path_dark"], None, False))
    pad = fc * (0.9 + 0.2 * n3)[..., None]
    if kind == "panels":      # gravel bed for the solar array
        pad = C([0.62, 0.60, 0.56]) * (0.75 + 0.5 * noise(0.07, 1, 440))[..., None]
    if kind in ("building", "rack"):   # floor slabs
        pad *= (1 - 0.3 * gline(np.minimum(gridd(X - bx, 0.6), gridd(Z - bz, 0.6)), 0.015))[..., None]
    col *= (1 - 0.35 * np.clip(1 - np.abs(dq - r0 - 0.06) / 0.12, 0, 1))[..., None]   # drop shadow
    col = lerp(col, pad, fill)
    col = lerp(col, bc, ring(dq, r0 - 0.07, 0.06) * fill)
    if haz:
        band, stripe = hazard(bx, bz, dq, r0 - 0.16, 0.1)
        col = np.where((band & (fill > 0.5))[..., None], np.where(stripe[..., None], C([0.95, 0.75, 0.10]), C([0.12, 0.12, 0.12])), col)
    if kind == "dish":        # concrete pad with a painted ring
        col = lerp(col, C([0.95, 0.95, 0.95]), ring(d, br * 0.6, 0.05) * fill)
    if glow is not None:
        g = ring(dq, r0 - 0.2, 0.03) * fill
        col = col + glow * (g * 0.9 + ring(dq, r0 - 0.2, 0.15) * fill * 0.15)[..., None]
    return col


for bl in m.get("blockers", []):
    bx, bz, br = bl[0], bl[1], bl[2]
    kind = bl[3] if len(bl) > 3 else {"snow": "lake", "volcano": "lava"}.get(theme, "rocks")
    wob = (noise(0.8, 2, int(bx * 7 + bz * 13) % 997) - 0.5) * 0.5
    d = np.hypot(X - bx, Z - bz) + wob
    core = np.clip((br - d) / 0.15, 0, 1)
    rim = np.clip(1 - np.abs(d - br) / 0.35, 0, 1)
    depth = np.clip(1 - d / br, 0, 1)
    if NEW:
        col = blocker_new(col, kind, bx, bz, br, d, core, rim, depth)
    elif kind == "lake" and theme != "snow":   # fresh water pond
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
        tiles_ = (np.abs(np.sin(X * 4.0)) < 0.12) | (np.abs(np.sin(Z * 4.0)) < 0.12)
        col = lerp(col, np.where(tiles_[..., None], C([0.5, 0.44, 0.36]), C([0.74, 0.68, 0.58])), core)
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


def blade(draw, i, j, c, ln, a, w=2, alpha=230):
    draw.line((j, i, j + np.sin(a) * ln, i - np.cos(a) * ln), fill=(*c, alpha), width=w)


def tint(i, j, sh):
    return tuple(int(np.clip(v, 0, 1) * 255) for v in col[i, j] * sh)


def scatter_new(draw):
    """Surface detail for the era themes: small sprites stamped on the open ground."""
    t = theme
    near_path = style in ("dirt", "cinder", "rails")
    for _ in range(900 if near_path else 0):   # loose stones on and near unpaved roads
        i = rng.integers(0, h_px); j = rng.integers(0, w_px)
        if dist[i, j] < half + 0.25 and not (rivers and (rdist[i, j] < rhalf[i, j] + 0.15 or on_water[i, j])):
            r = rng.uniform(2, 5)
            g = int(rng.uniform(40, 80)) if t == "forge" else int(rng.uniform(115, 170))
            draw.ellipse((j - r + 1.5, i - r * 0.7 + 2, j + r + 1.5, i + r * 0.7 + 2), fill=(30, 22, 15, 90))
            draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(g, g - 4, max(g - 10, 0), 255))
    n = {"lab": 300, "server": 500, "neon": 700, "core": 900, "suburb": 2600, "metro": 2200,
         "satellite": 2200, "cooling": 3800}.get(t, 5200)
    for _ in range(n):
        i = rng.integers(0, h_px); j = rng.integers(0, w_px)
        roll = rng.random()
        if dist[i, j] <= half + 0.35 or blocked(i, j):
            continue
        if rivers and rdist[i, j] < rhalf[i, j] + 0.2:
            continue
        if rivers and rdist[i, j] < rhalf[i, j] + 0.8:   # shoreline: reeds by the stream, shells on the beach
            if t == "highland":
                for k in range(3):
                    blade(draw, i, j + k * 2, (70, 105, 50), 10, rng.uniform(-0.35, 0.35))
            elif roll < 0.4:
                c = [(250, 236, 224), (240, 200, 190), (220, 220, 210)][rng.integers(0, 3)]
                draw.ellipse((j - 2.5, i - 2, j + 2.5, i + 2), fill=(*c, 255))
            continue
        if t in ("highland", "acropolis", "farmland", "castle", "harbor", "fortress"):
            if t == "acropolis" and MASK["paved"][i, j]:
                if roll < 0.05:
                    draw.ellipse((j - 2, i - 1.5, j + 2, i + 1.5), fill=(250, 248, 240, 255))
                continue
            if t == "farmland" and MASK["wheat"][i, j]:
                if roll < 0.03:   # poppies in the wheat
                    draw.ellipse((j - 2.5, i - 2.5, j + 2.5, i + 2.5), fill=(220, 40, 30, 255))
                elif roll < 0.4:
                    blade(draw, i, j, (236, 204, 110), 7, rng.uniform(-0.3, 0.3))
                continue
            if t == "harbor" and MASK["sand"][i, j] > 0.5:
                if roll < 0.12:
                    g = int(rng.uniform(150, 200))
                    draw.ellipse((j - 2, i - 1.5, j + 2, i + 1.5), fill=(g, int(g * 0.9), int(g * 0.75), 255))
                elif roll < 0.16:
                    c = [(250, 236, 224), (240, 200, 190)][rng.integers(0, 2)]
                    draw.ellipse((j - 2.5, i - 2, j + 2.5, i + 2), fill=(*c, 255))
                continue
            if t == "fortress" and MASK["dirt"][i, j] > 0.5:
                if roll < 0.15:
                    r = rng.uniform(1.5, 3)
                    g = int(rng.uniform(110, 160))
                    draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(g, int(g * 0.85), int(g * 0.65), 255))
                continue
            if t == "castle" and MASK["cobble"][i, j] > 0.5:
                continue
            if t == "highland" and MASK["heather"][i, j] > 0.4 and roll < 0.5:   # heather sprigs
                c = [(150, 90, 170), (190, 120, 200), (120, 70, 140)][rng.integers(0, 3)]
                blade(draw, i, j, (70, 90, 50), 6, rng.uniform(-0.4, 0.4))
                for k in range(4):
                    oy, ox = rng.uniform(-6, 0), rng.uniform(-2.5, 2.5)
                    draw.ellipse((j + ox - 1.6, i + oy - 1.6, j + ox + 1.6, i + oy + 1.6), fill=(*c, 255))
                continue
            if roll < 0.04 and t in ("acropolis", "farmland", "harbor"):
                c = [(250, 250, 240), (255, 220, 70), (240, 140, 200)][rng.integers(0, 3)]
                draw.ellipse((j - 2.5, i - 2.5, j + 2.5, i + 2.5), fill=(*c, 255))
                continue
            if roll < 0.06 and t == "castle":   # straw
                blade(draw, i, j, (220, 190, 110), 7, rng.uniform(-1.4, 1.4))
                continue
            if roll < 0.05 and t == "highland":
                r = rng.uniform(2, 4)
                draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(140, 140, 132, 255))
                continue
            blade(draw, i, j, tint(i, j, rng.uniform(0.65, 1.25)), rng.uniform(4, 9), rng.uniform(-0.6, 0.6))
        elif t == "forge":
            if roll < 0.08:
                r = rng.uniform(1.5, 2.5)
                draw.ellipse((j - r, i - r, j + r, i + r), fill=(255, int(rng.uniform(100, 180)), 40, 230))
            elif roll < 0.3:
                r = rng.uniform(2, 4.5)
                draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(16, 15, 16, 255))
            else:
                g = int(rng.uniform(70, 120))
                draw.ellipse((j - 1.5, i - 1.5, j + 1.5, i + 1.5), fill=(g, g - 6, g - 10, 150))
        elif t == "bog":
            if MASK["puddle"][i, j] > 0.3:
                if roll < 0.3:
                    for k in range(4):
                        blade(draw, i, j + k * 2, (70, 95, 45), rng.uniform(8, 13), rng.uniform(-0.3, 0.3))
                continue
            if roll < 0.08:   # reed tufts
                for k in range(4):
                    blade(draw, i, j + k * 2, (110, 120, 60), rng.uniform(7, 12), rng.uniform(-0.4, 0.4))
            elif roll < 0.18:
                draw.ellipse((j - 2.5, i - 2, j + 2.5, i + 2), fill=(90, 130, 40, 230))
            else:
                blade(draw, i, j, tint(i, j, rng.uniform(0.7, 1.25)), rng.uniform(4, 8), rng.uniform(-0.6, 0.6))
        elif t == "olive":
            if roll < 0.03:
                c = [(250, 250, 240), (190, 150, 220)][rng.integers(0, 2)]
                draw.ellipse((j - 2, i - 2, j + 2, i + 2), fill=(*c, 255))
            elif roll < 0.12:
                r = rng.uniform(1.5, 3.5)
                g = int(rng.uniform(170, 215))
                draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(g, int(g * 0.95), int(g * 0.85), 255))
            else:
                c = (225, 195, 110) if rng.random() < 0.5 else tint(i, j, rng.uniform(0.75, 1.15))
                blade(draw, i, j, c, rng.uniform(4, 8), rng.uniform(-0.7, 0.7))
        elif t == "coast":
            if roll < 0.05:
                c = [(250, 236, 224), (240, 196, 186), (230, 230, 220)][rng.integers(0, 3)]
                draw.ellipse((j - 2.5, i - 2, j + 2.5, i + 2), fill=(*c, 255))
            elif roll < 0.18:
                r = rng.uniform(1.5, 3)
                g = int(rng.uniform(150, 210))
                draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(g, g, int(g * 0.95), 255))
            elif roll < 0.21:   # beach grass
                for k in range(3):
                    blade(draw, i, j + k * 2, (140, 150, 80), 8, rng.uniform(-0.5, 0.5))
        elif t == "darkwood":
            if roll < 0.01:   # toadstool
                draw.ellipse((j - 3, i - 2.5, j + 3, i + 2.5), fill=(200, 40, 30, 255))
                draw.ellipse((j - 1, i - 1, j + 1, i + 1), fill=(250, 240, 230, 255))
            elif roll < 0.5:
                c = [(120, 70, 30), (150, 90, 30), (90, 60, 30), (110, 40, 25), (80, 85, 35)][rng.integers(0, 5)]
                a = rng.uniform(0, np.pi)
                r = rng.uniform(2, 3.5)
                draw.ellipse((j - r, i - r * 0.6, j + r, i + r * 0.6), fill=(*c, 220))
            elif roll < 0.58:
                blade(draw, i, j, (50, 35, 20), rng.uniform(6, 12), rng.uniform(-1.5, 1.5))
        elif t == "jungle":
            if roll < 0.04:
                c = [(240, 50, 60), (255, 150, 30), (230, 60, 200), (255, 230, 60)][rng.integers(0, 4)]
                draw.ellipse((j - 3, i - 3, j + 3, i + 3), fill=(*c, 255))
                draw.ellipse((j - 1, i - 1, j + 1, i + 1), fill=(255, 240, 120, 255))
            elif roll < 0.14:   # fern fan
                base_a = rng.uniform(-0.5, 0.5)
                c = tint(i, j, rng.uniform(1.1, 1.5))
                for k in range(5):
                    blade(draw, i, j, c, 10, base_a + (k - 2) * 0.35)
            else:
                blade(draw, i, j, tint(i, j, rng.uniform(0.7, 1.35)), rng.uniform(4, 9), rng.uniform(-0.7, 0.7))
        elif t == "railyard":
            if roll < 0.03:
                draw.ellipse((j - 2, i - 2, j + 2, i + 2), fill=(150, 80, 40, 230))   # rusty bolt
            elif roll < 0.07:
                r = rng.uniform(1.5, 3)
                draw.ellipse((j - r, i - r, j + r, i + r), fill=(25, 24, 26, 240))   # coal bit
            elif roll < 0.4:
                r = rng.uniform(1.2, 2.5)
                g = int(rng.uniform(90, 175))
                draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(g, g, g - 6, 255))
        elif t == "factory":
            if roll < 0.08:   # brick fragment
                c = (int(rng.uniform(150, 190)), int(rng.uniform(60, 80)), 50)
                draw.rectangle((j - 3, i - 1.5, j + 3, i + 1.5), fill=(*c, 255))
            elif roll < 0.11:   # rust stain
                draw.ellipse((j - 4, i - 3, j + 4, i + 3), fill=(140, 80, 40, 80))
            elif roll < 0.25:
                g = int(rng.uniform(110, 160))
                draw.ellipse((j - 1.5, i - 1.5, j + 1.5, i + 1.5), fill=(g, g - 4, g - 8, 200))
        elif t == "smog":
            if MASK["puddle"][i, j] > 0.3:
                continue
            if roll < 0.08:
                draw.ellipse((j - 4, i - 2.5, j + 4, i + 2.5), fill=(30, 26, 24, 120))   # soot
            elif roll < 0.1:
                draw.rectangle((j - 2, i - 1.5, j + 2, i + 1.5), fill=(225, 220, 205, 230))   # litter
            elif roll < 0.35:
                g = int(rng.uniform(60, 110))
                draw.ellipse((j - 1.5, i - 1.2, j + 1.5, i + 1.2), fill=(g, g - 6, g - 12, 220))
        elif t == "suburb":
            if roll < 0.06:
                draw.ellipse((j - 2, i - 2, j + 2, i + 2), fill=(250, 250, 245, 255))
                draw.ellipse((j - 0.8, i - 0.8, j + 0.8, i + 0.8), fill=(255, 210, 40, 255))
            elif roll < 0.1:
                draw.ellipse((j - 2, i - 2, j + 2, i + 2), fill=(255, 220, 40, 255))
        elif t == "military":
            if MASK["tarmac"][i, j]:
                if roll < 0.08:   # crack
                    a = rng.uniform(0, np.pi)
                    blade(draw, i, j, (40, 40, 40), rng.uniform(6, 14), a, 1, 200)
                continue
            if roll < 0.12:
                r = rng.uniform(1.5, 3)
                g = int(rng.uniform(140, 190))
                draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(g, int(g * 0.9), int(g * 0.7), 255))
            elif roll < 0.5:
                c = (200, 180, 110) if rng.random() < 0.5 else tint(i, j, rng.uniform(0.75, 1.15))
                blade(draw, i, j, c, rng.uniform(4, 8), rng.uniform(-0.7, 0.7))
        elif t == "metro":
            if MASK["park"][i, j]:
                if roll < 0.06:
                    c = [(250, 250, 240), (255, 220, 70), (240, 120, 160)][rng.integers(0, 3)]
                    draw.ellipse((j - 2, i - 2, j + 2, i + 2), fill=(*c, 255))
                else:
                    blade(draw, i, j, tint(i, j, rng.uniform(0.75, 1.25)), rng.uniform(4, 7), rng.uniform(-0.6, 0.6))
            elif roll < 0.06:
                draw.ellipse((j - 1.5, i - 1.5, j + 1.5, i + 1.5), fill=(70, 70, 72, 200))   # gum spot
        elif t == "neon":
            c = (40, 220, 255) if roll < 0.6 else (255, 60, 220)
            draw.ellipse((j - 1.2, i - 1.2, j + 1.2, i + 1.2), fill=(*c, 160))
        elif t == "satellite":
            if roll < 0.25:
                r = rng.uniform(1.5, 3)
                g = int(rng.uniform(150, 200))
                draw.ellipse((j - r, i - r * 0.7, j + r, i + r * 0.7), fill=(g, int(g * 0.88), int(g * 0.7), 255))
            elif roll < 0.29:
                for k in range(4):
                    blade(draw, i, j, (130, 115, 70), 6, rng.uniform(-1.2, 1.2))
        elif t == "lab":
            draw.ellipse((j - 3, i - 1, j + 3, i + 1), fill=(170, 175, 185, 70))   # scuff
        elif t == "server":
            c = (60, 140, 255) if roll < 0.75 else (60, 255, 140)
            draw.ellipse((j - 1.3, i - 1.3, j + 1.3, i + 1.3), fill=(*c, 200))
        elif t == "cooling":
            if roll < 0.08:   # ice crystal
                for k in range(3):
                    a = k * np.pi / 3
                    draw.line((j - np.cos(a) * 4, i - np.sin(a) * 4, j + np.cos(a) * 4, i + np.sin(a) * 4),
                              fill=(240, 250, 255, 230), width=1)
            else:
                c = (255, 255, 255, 210) if roll < 0.7 else (170, 205, 235, 170)
                draw.ellipse((j - 1.3, i - 1.3, j + 1.3, i + 1.3), fill=c)
        elif t == "core":
            if roll < 0.3:
                draw.ellipse((j - 1.2, i - 1.2, j + 1.2, i + 1.2), fill=(255, 60, 40, 200))
            else:
                draw.ellipse((j - 0.8, i - 0.8, j + 0.8, i + 0.8), fill=(200, 190, 220, 120))


if NEW:
    scatter_new(draw)
else:
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
