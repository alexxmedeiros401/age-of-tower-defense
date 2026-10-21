"""HQ ground for the Stone Age, Bronze Age and Iron Age maps: the map's ground as a real 3D surface, rendered straight down into
its ground texture, so it always matches the simulation's road, lanes and no-build zones.

    python3 tools/blender/map_ground_hq.py <map_id> [--px 64] [--samples 32] [--out PATH] [--preview]

The road is sunk into the ground with wheel ruts and a lip, and every theme gets scattered 3D detail lit by the game's
own sun direction: grass tufts, flowers, pebbles and stones (meadow); snow lumps, frozen ponds with cracks, polished ice
lanes and deep drifts (snow); basalt, ash, cinders and glowing fissures, molten pools (volcano); lush grass, a river in
its channel with sandy banks, reeds and a lake (delta, v0.9.28: game/shaders/ground_water.gdshader makes the water
move, tools/water_mask.py finds it); rippled sand, a paved road, gravel and drifts (desert); red rock with strata and
cracks, a mine railway down the road, copper-green flecks (canyon); heather moor and bracken, a cold stream with stony
banks forded by a cobbled track, peaty lochans (highland); soot, cinders and rusty ore earth, glassy slag heaps, a
packed-cinder road with a clay wallow, lava pools and glowing fissures (forge); a marsh of sedge, red and green
sphagnum and peat, plank trackways laid across the road, a sucking mud wallow where they meet, black bog pools with scum
at their edges (bog); Classical Age (v0.9.48): a dry Mediterranean hillside of golden grass, red earth and limestone,
tilled red earth under the olive groves, a dusty track scuffed smooth on the downhill runs and loose scree on the climbs
(olive); coastal scrub on sandy ground, white beaches and a turquoise inlet the Roman road bridges, its flagstones in
the aqueducts' shadow (coast); a hill of pale limestone, its crevices grassy, the road paved with marble slabs, marble
paving round the ruins and the statues (acropolis). For highland, bog and coast, --watersrc PATH also writes the exact
water mask (the stream, its fords, the lochans, the bog pools, the inlet) for tools/water_mask.py --src PATH.
Output: assets/textures/ground_<map_id>.png (same coverage as tools/gen_ground.py: x -21..19, z -13..13).
"""
import sys, os, math, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import numpy as np
import bpy, bmesh
from mathutils import Vector, Euler
import map_geo as G

A = sys.argv
MAP = A[1]
def arg(n, d=None):
    return A[A.index(n) + 1] if n in A else d
PX = int(arg("--px", "64"))
SAMPLES = int(arg("--samples", "32"))
OUT = arg("--out", os.path.join(ROOT, "assets", "textures", "ground_%s.png" % MAP))
PREVIEW = "--preview" in A
T0 = time.time()
m, specs = G.load(MAP, ROOT)
THEME = m.get("theme", "meadow")
HALF = m["path_width"] / 2.0
RNG = np.random.default_rng(17)


def log(*a):
    print("[ground %.0fs]" % (time.time() - T0), *a, flush=True)


# ------------------------------------------------------------------------------------------------ masks
MPX = 24                                   # mask resolution (px per unit)
g = G.Grid(MPX)
X, Z = g.X, g.Z
legs = [lg for sp in specs for lg in G.visible_legs(sp)]
dist, along = g.poly_dist(legs)
zf = G.zones(specs)


def fbm(scale, octaves=4, seed=0):
    """Value-noise fBm on the mask grid (scale in world units)."""
    r = np.random.default_rng(seed)
    acc = np.zeros(X.shape)
    amp, tot, s = 1.0, 0.0, scale
    from PIL import Image
    for o in range(octaves):
        gw, gh = max(2, int(G.W / s) + 3), max(2, int(G.H / s) + 3)
        grid = r.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((grid * 255).astype(np.uint8)).resize((g.w, g.h), Image.BICUBIC)
        acc += amp * (np.asarray(im, np.float32) / 255.0)
        tot += amp
        amp *= 0.5
        s *= 0.5
    return acc / tot


wob = (fbm(1.2, 3, 5) - 0.5) * 0.16
road = np.clip((HALF + wob - dist) / 0.06, 0, 1)                       # 1 on the road
edge = np.exp(-((dist - HALF - wob) / 0.12) ** 2)                      # the road's lip
rut = np.zeros(X.shape)
for off in (-0.36, 0.36):
    rut = np.maximum(rut, np.exp(-((dist - abs(off)) / 0.09) ** 2))
rut *= road
b = m["bounds"]
inb = np.minimum.reduce([X - b[0], b[2] - X, Z - b[1], b[3] - Z]) + (fbm(2.5, 3, 9) - 0.5) * 2.2
outside = np.clip((-inb + 0.6) / 1.6, 0, 1)
lane = np.zeros(X.shape)
lane_u = np.zeros(X.shape)
lane_s = np.zeros(X.shape)
if zf["fast"]:
    fd, fal, fsd = g.poly_dist(zf["fast"], signed=True)
    lane = np.clip((HALF - 0.02 - fd) / 0.05, 0, 1)
    lane_u = fal + np.abs(fsd) * 0.65
    lane_s = np.abs(fsd)
slow = np.zeros(X.shape)
if zf["slow"]:
    sd_, sal, ssd = g.poly_dist(zf["slow"], signed=True)
    slow = np.clip((HALF + 0.14 + (fbm(0.45, 3, 311) - 0.5) * 0.3 - sd_) / 0.08, 0, 1)
tun = np.zeros(X.shape)
tun_al = np.zeros(X.shape)
if zf["tunnel"]:
    td, tun_al = g.poly_dist(zf["tunnel"])
    tun = np.exp(-(td / 0.3) ** 2) * np.clip((dist - HALF - 0.1) / 0.1, 0, 1)
blk = {k: np.full(X.shape, 1e9) for k in ("lake", "lava", "rocks", "palms", "dune", "ruins", "pillar", "ore", "trees", "stones", "slag",
                                         "statue")}
BLOCKERS = []
for bl in m.get("blockers", []):
    bx, bz, br = bl[0], bl[1], bl[2]
    kind = bl[3] if len(bl) > 3 else {"snow": "lake", "volcano": "lava"}.get(THEME, "rocks")
    kind = kind if kind in blk else "rocks"
    w2 = (fbm(0.8, 2, int(bx * 7 + bz * 13) % 997) - 0.5) * 0.5
    d = np.hypot(X - bx, Z - bz) + w2 - br                    # < 0 inside
    blk[kind] = np.minimum(blk[kind], d)
    BLOCKERS.append((bx, bz, br, kind))
# rivers (delta): distance to each river's centre line, its half width there
riv = np.full(X.shape, 1e9)
for rv in m.get("rivers", []):
    rdd, _ra = g.poly_dist([rv["pts"]], margin=6.0)
    riv = np.minimum(riv, rdd + (fbm(1.5, 3, 41) - 0.5) * 0.4 - float(rv["width"]) / 2)     # < 0 in the water
log("masks", g.w, g.h)
if arg("--watersrc") and THEME in ("highland", "bog", "coast"):
    from PIL import Image as _Im
    _w = np.maximum(np.clip(-riv / 0.12, 0, 1), np.clip(-blk["lake"] / 0.15, 0, 1))
    _Im.fromarray((np.clip(_w, 0, 1) * 255).astype(np.uint8)).save(arg("--watersrc"))
    log("water source ->", arg("--watersrc"))


def to_image(name, arr, color=False):
    """numpy (rows from Z0 down) -> Blender float image (rows from the bottom)."""
    h, w = arr.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=True, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    px = np.ones((h, w, 4), np.float32)
    if arr.ndim == 2:
        px[..., 0] = px[..., 1] = px[..., 2] = arr
    else:
        px[..., :arr.shape[2]] = arr
    im.pixels.foreach_set(px[::-1].ravel())
    im.pack()
    return im


# ------------------------------------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES if not PREVIEW else 8
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
sc.render.resolution_x = int(G.W * (PX if not PREVIEW else 16))
sc.render.resolution_y = int(G.H * (PX if not PREVIEW else 16))
sc.view_settings.view_transform = "Standard"
sc.render.film_transparent = False
wd = bpy.data.worlds.new("Sky")
sc.world = wd
wd.use_nodes = True
SKY = {"meadow": (0.62, 0.74, 0.95), "snow": (0.66, 0.78, 1.0), "volcano": (0.6, 0.38, 0.3), "delta": (0.62, 0.76, 0.95),
       "desert": (0.72, 0.78, 0.92), "canyon": (0.74, 0.7, 0.72), "highland": (0.62, 0.72, 0.9), "forge": (0.56, 0.42, 0.36),
       "bog": (0.64, 0.72, 0.78), "olive": (0.66, 0.76, 0.95), "coast": (0.64, 0.77, 0.96), "acropolis": (0.66, 0.76, 0.95)}[THEME]
wd.node_tree.nodes["Background"].inputs["Color"].default_value = SKY + (1,)
wd.node_tree.nodes["Background"].inputs["Strength"].default_value = {"meadow": 1.05, "snow": 1.0, "volcano": 0.8, "delta": 1.05,
                                                                    "desert": 1.0, "canyon": 0.95, "highland": 1.0, "forge": 0.82,
                                                                    "bog": 0.98, "olive": 1.05, "coast": 1.05, "acropolis": 1.05}[THEME]
# the game's sun: Godot rotation (-52, -36, 0) -> light travelling (0.362, -0.788, -0.498) in Godot = (x, y_b, z_b)
# (0.362, 0.498, -0.788) in Blender (y_b = -z_godot)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = {"meadow": 2.7, "snow": 2.6, "volcano": 2.3, "delta": 2.7, "desert": 2.8, "canyon": 2.6, "highland": 2.6, "forge": 2.3,
                   "bog": 2.5, "olive": 2.8, "coast": 2.75, "acropolis": 2.8}[THEME]
sun.data.angle = math.radians(8)
sun.data.color = {"meadow": (1.0, 0.95, 0.86), "snow": (1.0, 0.98, 0.96), "volcano": (1.0, 0.75, 0.55), "delta": (1.0, 0.95, 0.86),
                  "desert": (1.0, 0.94, 0.82), "canyon": (1.0, 0.9, 0.78), "highland": (1.0, 0.95, 0.87), "forge": (1.0, 0.8, 0.62),
                  "bog": (0.98, 0.96, 0.86), "olive": (1.0, 0.95, 0.84), "coast": (1.0, 0.96, 0.88), "acropolis": (1.0, 0.95, 0.85)}[THEME]
d = Vector((0.362, 0.498, -0.788))
sun.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(sun)
cd = bpy.data.cameras.new("Top")
cd.type = "ORTHO"
cd.ortho_scale = G.W
cam = bpy.data.objects.new("Top", cd)
sc.collection.objects.link(cam)
cam.location = (G.X0 + G.W / 2, 0.0, 20.0)
cam.rotation_euler = (0, 0, 0)
sc.camera = cam
cd.clip_end = 50


# ------------------------------------------------------------------------------------------------ terrain
MESH_STEP = 0.05 if not PREVIEW else 0.12
nx, nz = int(G.W / MESH_STEP) + 1, int(G.H / MESH_STEP) + 1
xs = np.linspace(G.X0, G.X0 + G.W, nx)
zs = np.linspace(G.Z0, G.Z0 + G.H, nz)
MX, MZ = np.meshgrid(xs, zs)


def sample(arr, x, z):
    """Bilinear lookup of a mask at world (x, z)."""
    fx = np.clip((x - G.X0) * MPX - 0.5, 0, g.w - 1.001)
    fz = np.clip((z - G.Z0) * MPX - 0.5, 0, g.h - 1.001)
    i0, j0 = fz.astype(int), fx.astype(int)
    tz, tx = fz - i0, fx - j0
    a = arr[i0, j0] * (1 - tx) + arr[i0, j0 + 1] * tx
    c = arr[i0 + 1, j0] * (1 - tx) + arr[i0 + 1, j0 + 1] * tx
    return a * (1 - tz) + c * tz


hf = (fbm(1.6, 4, 21) - 0.5) * 0.09 + (fbm(0.35, 2, 22) - 0.5) * 0.025
hf += outside * (fbm(1.0, 3, 23) - 0.3) * 0.2
hf -= road * 0.045 + rut * 0.02
hf += edge * 0.012 * (1 - road)
if THEME == "snow":
    hf += (fbm(0.9, 3, 24) - 0.5) * 0.09 * (1 - road) + (fbm(0.3, 2, 27) - 0.5) * 0.03 * (1 - road)
    hf += slow * (0.05 + (fbm(0.3, 2, 25) - 0.5) * 0.06)
    lk = blk["lake"]
    hf = np.where(lk < 0, -0.035 + 0 * hf, hf) + np.exp(-((lk - 0.1) / 0.18) ** 2) * 0.05
if THEME == "volcano":
    lv = blk["lava"]
    hf = np.where(lv < 0, -0.05, hf) + np.exp(-((lv - 0.12) / 0.2) ** 2) * 0.07
    hf += (fbm(0.5, 3, 26) - 0.5) * 0.05 * (1 - road)
if THEME == "delta":
    hf = np.where((riv < 0) & (road < 0.5), -0.07, hf)                                             # the river's channel (not under the bridge)
    hf += np.exp(-((riv - 0.12) / 0.22) ** 2) * 0.03 * (1 - road)                                   # its banks
    lk = blk["lake"]
    hf = np.where(lk < 0, -0.06, hf) + np.exp(-((lk - 0.1) / 0.2) ** 2) * 0.03
if THEME == "desert":
    dunes = (fbm(3.0, 3, 61) - 0.5) * 0.22 + (fbm(0.9, 2, 62) - 0.5) * 0.05
    hf += dunes * (1 - road) * np.clip((dist - HALF) / 1.2, 0, 1)
    hf += np.clip(-blk["dune"] / 1.6, 0, 1) * 0.12
if THEME == "canyon":
    hf += (fbm(1.0, 4, 71) - 0.5) * 0.08 * (1 - road)
    hf += np.clip(-blk["pillar"] / 0.9, 0, 1) * 0.08
    hf = np.where(blk["ore"] < 0, -0.05, hf) + np.exp(-((blk["ore"] - 0.12) / 0.2) ** 2) * 0.05
if THEME == "highland":
    hf += (fbm(1.2, 4, 81) - 0.5) * 0.06 * (1 - road)                                             # the rolling moor
    hf = np.where((riv < 0) & (road < 0.5), -0.08, hf)                                             # the stream's channel
    hf = np.where((riv < 0) & (road >= 0.5), -0.03, hf)                                            # the fords: the track dips in
    hf += np.exp(-((riv - 0.12) / 0.22) ** 2) * 0.03 * (1 - road)                                   # its stony banks
    lk = blk["lake"]
    hf = np.where(lk < 0, -0.06, hf) + np.exp(-((lk - 0.1) / 0.2) ** 2) * 0.03
    hf += np.clip(-blk["stones"] / 0.9, 0, 1) * 0.05                                               # a low rise under each stone ring
if THEME == "forge":
    hf += (fbm(0.6, 3, 91) - 0.5) * 0.05 * (1 - road)
    lv = blk["lava"]
    hf = np.where(lv < 0, -0.05, hf) + np.exp(-((lv - 0.12) / 0.2) ** 2) * 0.07
    hf += np.clip(-blk["slag"] / 1.1, 0, 1) ** 0.7 * 0.12 + np.clip(-blk["slag"] / 1.1, 0, 1) * (fbm(0.3, 2, 92) - 0.5) * 0.08
    hf -= slow * 0.02                                                                              # the clay wallow
if THEME == "bog":
    hf += (fbm(0.7, 3, 101) - 0.5) * 0.05 * (1 - road) + (fbm(0.25, 2, 102) - 0.5) * 0.02 * (1 - road)   # hummocks and hollows
    lk = blk["lake"]
    hf = np.where(lk < 0, -0.055, hf) + np.exp(-((lk - 0.08) / 0.16) ** 2) * 0.02
    hf += road * 0.03 * (1 - slow) - slow * 0.025                                                  # the trackway rides on the marsh; mud sinks
if THEME == "olive":
    hf += (fbm(1.8, 4, 111) - 0.5) * 0.08 * (1 - road)                                             # the rolling hillside
    hf += slow * (0.012 + (fbm(0.22, 2, 112) - 0.5) * 0.05)                                          # loose scree on the climbs
    hf += np.clip(-blk["trees"] / 1.0, 0, 1) * 0.02                                                 # the groves' low terraces
if THEME == "coast":
    hf += (fbm(1.4, 4, 121) - 0.5) * 0.06 * (1 - road)
    hf = np.where((riv < 0) & (road < 0.5), -0.09, hf)                                             # the inlet (not under the bridge)
    hf -= np.exp(-((riv - 0.15) / 0.35) ** 2) * 0.03 * (1 - road)                                   # its beaches shelving down to it
if THEME == "acropolis":
    hf += (fbm(0.9, 4, 131) - 0.5) * 0.06 * (1 - road)
    hf += np.clip((fbm(0.6, 3, 132) - 0.55) / 0.2, 0, 1) * 0.04 * (1 - road)                       # ledges of bare limestone
    hf += np.clip(-blk["statue"] / 0.6, 0, 1) * 0.02                                                # the statues' paved plinths
rk = blk["rocks"]
hf += np.clip(-rk / 0.8, 0, 1) * 0.06
H_MESH = sample(hf, MX, MZ)
verts = np.stack([MX.ravel(), -MZ.ravel(), H_MESH.ravel()], 1).astype(np.float32)
ii = np.arange(nx * nz).reshape(nz, nx)
quads = np.stack([ii[:-1, :-1].ravel(), ii[:-1, 1:].ravel(), ii[1:, 1:].ravel(), ii[1:, :-1].ravel()], 1)
me = bpy.data.meshes.new("Ground")
me.vertices.add(len(verts))
me.vertices.foreach_set("co", verts.ravel())
me.loops.add(len(quads) * 4)
me.loops.foreach_set("vertex_index", quads[:, ::-1].ravel().astype(np.int32))
me.polygons.add(len(quads))
me.polygons.foreach_set("loop_start", np.arange(0, len(quads) * 4, 4, dtype=np.int32))
me.polygons.foreach_set("loop_total", np.full(len(quads), 4, np.int32))
me.update(calc_edges=True)
uv = me.uv_layers.new(name="UVMap")
lv_idx = quads[:, ::-1].ravel()
uvs = np.stack([(verts[lv_idx, 0] - G.X0) / G.W, (verts[lv_idx, 1] + 13.0) / G.H], 1)
uv.data.foreach_set("uv", uvs.ravel().astype(np.float32))
me.polygons.foreach_set("use_smooth", np.ones(len(quads), bool))
ground = bpy.data.objects.new("Ground", me)
sc.collection.objects.link(ground)
log("terrain", len(verts), "verts")

# masks as images: R road, G edge, B rut, A outside / second image: lane, slow, tunnel, blocker field
img1 = to_image("mask1", np.stack([road, edge, rut, outside], 2))
lake_core = np.clip(-blk["lake"] / 0.15, 0, 1)
lava_core = np.clip(-blk["lava"] / 0.15, 0, 1)
rock_core = np.clip(-blk["rocks"] / 0.5, 0, 1)
chev = np.zeros(X.shape)
if zf["fast"]:
    gd = np.abs(lane_u / 1.15 - np.round(lane_u / 1.15)) * 1.15
    chev = np.exp(-(gd / 0.075) ** 2) * (lane_s < HALF - 0.18) * lane
dash = np.zeros(X.shape)
if zf["tunnel"]:
    gd2 = np.abs(tun_al / 1.3 - np.round(tun_al / 1.3)) * 1.3
    dash = tun * (gd2 > 0.4)
img2 = to_image("mask2", np.stack([lane, slow, np.maximum(tun * 0.5, dash), chev], 2))
img3 = to_image("mask3", np.stack([lake_core, lava_core, rock_core, np.clip(1 - (blk["lava"]) / 1.2, 0, 1) * (1 - lava_core)], 2))
# Bronze Age themes: water (rivers and lakes), banks, the theme's own zones (palm oases, ruins' paving, dunes, pillars,
# copper pools), and the canyon's mine railway (sleepers across the road, two rails)
river_core = np.clip(-riv / 0.12, 0, 1)
bank = np.clip(1 - np.abs(riv - 0.18) / 0.32, 0, 1) * (1 - river_core)
lake_bank = np.clip(1 - np.abs(blk["lake"] - 0.15) / 0.3, 0, 1) * (1 - lake_core)
water_all = np.maximum(river_core, lake_core) * (1 - road)
if THEME == "highland":
    water_all = np.maximum(river_core, lake_core)                                                  # (the stream runs over its fords)
zone_a = np.clip(-blk["palms"] / 0.4, 0, 1) + np.clip(-blk["ruins"] / 0.3, 0, 1) + np.clip(-blk["stones"] / 0.5, 0, 1) + \
    np.clip(-blk["statue"] / 0.3, 0, 1)
zone_b = np.clip(-blk["dune"] / 0.6, 0, 1) + np.clip(-blk["pillar"] / 0.5, 0, 1) + np.clip(-blk["ore"] / 0.12, 0, 1) + \
    np.clip(-blk["slag"] / 0.5, 0, 1)
trees_z = np.clip(-blk["trees"] / 0.5, 0, 1)
sleeper = np.zeros(X.shape)
rail = np.zeros(X.shape)
if THEME == "canyon":
    ph = np.abs(along / 0.42 - np.round(along / 0.42)) * 0.42
    sleeper = (ph < 0.075).astype(np.float32) * (dist < HALF * 0.78) * road
    for off in (0.24,):
        rail = np.maximum(rail, np.exp(-((dist - off) / 0.022) ** 2) * road)
img4 = to_image("mask4", np.stack([water_all, np.maximum(bank, lake_bank) * (1 - road), np.clip(zone_a, 0, 1), np.clip(zone_b, 0, 1)], 2))
if THEME == "bog":                       # the trackways: planks laid across the road, dark gaps between them
    ph = np.abs(along / 0.27 - np.round(along / 0.27)) * 0.27
    sleeper = np.clip((ph - 0.012) / 0.012, 0, 1) * np.clip((HALF + 0.06 + (fbm(0.3, 2, 103) - 0.5) * 0.12 - dist) / 0.04, 0, 1)
    sleeper *= (1 - slow)
if THEME == "acropolis":                 # the marble slabs: joints across the road and one down its middle
    ph = np.abs(along / 0.62 - np.round(along / 0.62)) * 0.62
    sleeper = np.maximum(np.exp(-(ph / 0.014) ** 2), np.exp(-(dist / 0.014) ** 2)) * np.clip((HALF - 0.04 - dist) / 0.04, 0, 1)
img5 = to_image("mask5", np.stack([sleeper, rail, np.clip(-blk["ore"] / 0.12, 0, 1), trees_z], 2))


# ------------------------------------------------------------------------------------------------ ground material
def lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c[:3]) + (1.0,)


class NB:
    def __init__(self, name):
        self.m = bpy.data.materials.new(name)
        self.m.use_nodes = True
        self.nt = self.m.node_tree
        self.b = self.nt.nodes["Principled BSDF"]
        self.uvn = self.nt.nodes.new("ShaderNodeTexCoord")

    def n(self, t, **kw):
        nd = self.nt.nodes.new(t)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    def link(self, a, b):
        self.nt.links.new(a, b)

    def tex(self, img):
        t = self.n("ShaderNodeTexImage", image=img, interpolation="Linear", extension="EXTEND")
        self.link(self.uvn.outputs["UV"], t.inputs["Vector"])
        sep = self.n("ShaderNodeSeparateColor")
        self.link(t.outputs["Color"], sep.inputs["Color"])
        return sep.outputs["Red"], sep.outputs["Green"], sep.outputs["Blue"], t.outputs["Alpha"]

    def rgb(self, c):
        nd = self.n("ShaderNodeRGB")
        nd.outputs[0].default_value = lin(c)
        return nd.outputs[0]

    def noise(self, scale, detail=3.0, rough=0.55, coord="Object", distort=0.0):
        nd = self.n("ShaderNodeTexNoise")
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Detail"].default_value = detail
        nd.inputs["Roughness"].default_value = rough
        nd.inputs["Distortion"].default_value = distort
        self.link(self.uvn.outputs[coord], nd.inputs["Vector"])
        return nd.outputs["Fac"]

    def voronoi(self, scale, out="Distance", feature="F1"):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature)
        nd.inputs["Scale"].default_value = scale
        self.link(self.uvn.outputs["Object"], nd.inputs["Vector"])
        return nd.outputs[out]

    def math(self, op, a, b=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                nd.inputs[i].default_value = v
            else:
                self.link(v, nd.inputs[i])
        return nd.outputs[0]

    def ramp(self, x, lo, hi):
        nd = self.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
        self.link(x, nd.inputs["Value"])
        nd.inputs["From Min"].default_value = lo
        nd.inputs["From Max"].default_value = hi
        return nd.outputs["Result"]

    def mix(self, f, a, b):
        nd = self.n("ShaderNodeMix", data_type="RGBA", clamp_factor=True)
        for sock, v in (("Factor", f), ("A", a), ("B", b)):
            s_ = [s for s in nd.inputs if s.name == sock and (sock == "Factor" and s.type == "VALUE" or sock != "Factor" and s.type == "RGBA")][0]
            if isinstance(v, (int, float)):
                s_.default_value = v
            elif isinstance(v, tuple):
                s_.default_value = lin(v)
            else:
                self.link(v, s_)
        return [s for s in nd.outputs if s.type == "RGBA"][0]

    def mixf(self, f, a, b):
        nd = self.n("ShaderNodeMix", data_type="FLOAT", clamp_factor=True)
        ins = [s for s in nd.inputs if s.type == "VALUE"]
        for s_, v in zip(ins, (f, a, b)):
            if isinstance(v, (int, float)):
                s_.default_value = v
            else:
                self.link(v, s_)
        return [s for s in nd.outputs if s.type == "VALUE"][0]


nb = NB("GroundMat")
road_m, edge_m, rut_m, out_m = nb.tex(img1)
lane_m, slow_m, tun_m, chev_m = nb.tex(img2)
lake_m, lava_m, rock_m, heat_m = nb.tex(img3)
water_m, bank_m, zonea_m, zoneb_m = nb.tex(img4)
sleep_m, rail_m, ore_m, trees_m = nb.tex(img5)
big = nb.noise(0.35, 4, 0.6)
mid = nb.noise(1.6, 4, 0.6)
fine = nb.noise(14.0, 2, 0.5)
if THEME == "meadow":
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.27, 0.52, 0.14), (0.42, 0.66, 0.2))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.58, 0.72), 0.55), c, (0.55, 0.64, 0.22))       # dry yellow-green patches
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.38, 0.26), 0.5), c, (0.2, 0.44, 0.13))         # lush dark patches
    clover = nb.ramp(nb.voronoi(9.0, "Distance"), 0.18, 0.08)
    c = nb.mix(nb.math("MULTIPLY", clover, nb.math("MULTIPLY", nb.ramp(big, 0.55, 0.7), 0.35)), c, (0.32, 0.6, 0.2))
    c = nb.mix(nb.math("MULTIPLY", fine, 0.25), c, (0.5, 0.7, 0.26))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.13, 0.32, 0.1), (0.2, 0.4, 0.12)))     # wild ground outside
    dirt = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.5, 0.36, 0.21), (0.62, 0.47, 0.29))
    dirt = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.5, 0.75), 0.4), dirt, (0.72, 0.6, 0.42))
    dirt = nb.mix(nb.math("MULTIPLY", rut_m, 0.55), dirt, (0.42, 0.3, 0.18))
    grav = nb.ramp(nb.voronoi(38.0, "Distance"), 0.22, 0.1)
    dirt = nb.mix(nb.math("MULTIPLY", grav, 0.3), dirt, (0.4, 0.33, 0.25))
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.55), c, (0.36, 0.42, 0.16))                          # trampled grass at the edge
    c = nb.mix(road_m, c, dirt)
    rough = 0.9
elif THEME == "snow":
    c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.76, 0.83, 0.94), (0.93, 0.95, 1.0))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.58, 0.74), 0.7), c, (0.66, 0.76, 0.92))
    rip = nb.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL")
    rip.inputs["Scale"].default_value = 2.2
    rip.inputs["Distortion"].default_value = 6.0
    rip.inputs["Detail"].default_value = 3.0
    nb.link(nb.uvn.outputs["Object"], rip.inputs["Vector"])
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(rip.outputs["Fac"], 0.55, 0.85), 0.35), c, (0.7, 0.79, 0.94))
    sp = nb.ramp(nb.noise(60.0, 1, 0.5), 0.72, 0.78)
    c = nb.mix(nb.math("MULTIPLY", sp, 0.6), c, (1.0, 1.0, 1.0))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.66, 0.74, 0.86), (0.78, 0.84, 0.94)))
    trod = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.6, 0.58, 0.58), (0.74, 0.74, 0.76))
    trod = nb.mix(nb.math("MULTIPLY", rut_m, 0.8), trod, (0.44, 0.4, 0.38))                        # slushy ruts
    trod = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.55, 0.7), 0.5), trod, (0.88, 0.9, 0.94))
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.5), c, (0.86, 0.9, 0.97))
    c = nb.mix(road_m, c, trod)
    ice = nb.mix(nb.ramp(nb.noise(0.8, 3, 0.6), 0.2, 0.8), (0.62, 0.82, 0.96), (0.88, 0.96, 1.0))
    c = nb.mix(nb.math("MULTIPLY", lane_m, 0.95), c, ice)                                          # polished ice lane
    c = nb.mix(nb.math("MULTIPLY", chev_m, 0.9), c, (1.0, 1.0, 1.0))
    drift = nb.mix(nb.ramp(fine, 0.3, 0.7), (0.86, 0.91, 0.98), (1.0, 1.0, 1.0))
    c = nb.mix(slow_m, c, drift)
    crack = nb.ramp(nb.voronoi(2.4, "Distance", "DISTANCE_TO_EDGE"), 0.03, 0.0)
    lake = nb.mix(nb.ramp(nb.noise(0.6, 3, 0.6), 0.3, 0.7), (0.34, 0.6, 0.82), (0.55, 0.78, 0.93))
    lake = nb.mix(nb.math("MULTIPLY", crack, 0.8), lake, (0.92, 0.97, 1.0))
    c = nb.mix(lake_m, c, lake)
    rough = nb.mixf(nb.math("MAXIMUM", lane_m, lake_m), 0.55, 0.12)
elif THEME == "delta":
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.25, 0.52, 0.14), (0.4, 0.66, 0.19))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.6, 0.74), 0.5), c, (0.52, 0.66, 0.22))        # sunny dry patches
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.38, 0.26), 0.55), c, (0.17, 0.42, 0.13))      # lush dark patches
    c = nb.mix(nb.math("MULTIPLY", fine, 0.22), c, (0.48, 0.7, 0.25))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.12, 0.32, 0.1), (0.19, 0.4, 0.12)))
    dirt = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.56, 0.42, 0.26), (0.68, 0.53, 0.34))                 # river-silt road
    dirt = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.5, 0.75), 0.4), dirt, (0.76, 0.64, 0.46))
    dirt = nb.mix(nb.math("MULTIPLY", rut_m, 0.55), dirt, (0.46, 0.33, 0.2))
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.5), c, (0.36, 0.44, 0.17))
    c = nb.mix(road_m, c, dirt)
    sand = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.66, 0.56, 0.36), (0.8, 0.7, 0.48))
    c = nb.mix(nb.math("MULTIPLY", bank_m, 0.9), c, sand)                                          # sandy banks
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.7), c, sand)                                         # the palm grove's sand
    water = nb.mix(nb.ramp(nb.noise(0.7, 3, 0.6), 0.3, 0.7), (0.07, 0.36, 0.52), (0.14, 0.5, 0.62))
    water = nb.mix(nb.math("MULTIPLY", nb.ramp(water_m, 0.4, 0.0), 1.0), water, (0.24, 0.62, 0.66))   # shallows at the edge
    c = nb.mix(water_m, c, water)
    rough = nb.mixf(water_m, 0.9, 0.2)
elif THEME == "desert":
    c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.84, 0.68, 0.45), (0.94, 0.8, 0.56))
    rip = nb.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL")
    rip.inputs["Scale"].default_value = 3.0
    rip.inputs["Distortion"].default_value = 5.0
    rip.inputs["Detail"].default_value = 3.0
    nb.link(nb.uvn.outputs["Object"], rip.inputs["Vector"])
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(rip.outputs["Fac"], 0.55, 0.85), 0.32), c, (0.74, 0.58, 0.38))     # wind ripples
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.62, 0.76), 0.55), c, (0.66, 0.52, 0.36))        # gravel flats
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.62, 0.74), 0.35), c, (0.98, 0.88, 0.66))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.64, 0.5, 0.32), (0.76, 0.6, 0.4)))
    flag = nb.ramp(nb.voronoi(3.2, "Distance", "DISTANCE_TO_EDGE"), 0.02, 0.06)                   # a paved road: flags and grout
    pave = nb.mix(nb.ramp(nb.noise(2.5, 3, 0.6), 0.3, 0.7), (0.66, 0.6, 0.5), (0.78, 0.72, 0.6))
    pave = nb.mix(nb.math("SUBTRACT", 1.0, flag), pave, (0.46, 0.4, 0.32))
    pave = nb.mix(nb.math("MULTIPLY", rut_m, 0.35), pave, (0.56, 0.5, 0.42))
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.6), c, (0.6, 0.5, 0.36))
    c = nb.mix(road_m, c, pave)
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.75), c, nb.mix(nb.math("SUBTRACT", 1.0, flag), (0.74, 0.66, 0.52), (0.5, 0.43, 0.34)))   # the ruins' paving
    rough = 0.92
elif THEME == "canyon":
    c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.56, 0.28, 0.16), (0.7, 0.38, 0.21))
    strata = nb.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
    strata.inputs["Scale"].default_value = 0.9
    strata.inputs["Distortion"].default_value = 4.0
    strata.inputs["Detail"].default_value = 2.0
    nb.link(nb.uvn.outputs["Object"], strata.inputs["Vector"])
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(strata.outputs["Fac"], 0.6, 0.9), 0.35), c, (0.78, 0.48, 0.28))   # pale strata
    crack = nb.ramp(nb.voronoi(1.6, "Distance", "DISTANCE_TO_EDGE"), 0.025, 0.0)
    c = nb.mix(nb.math("MULTIPLY", crack, 0.6), c, (0.3, 0.14, 0.08))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.62, 0.74), 0.35), c, (0.82, 0.55, 0.34))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.34, 0.16, 0.09), (0.44, 0.22, 0.12)))
    dust = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.62, 0.42, 0.28), (0.72, 0.52, 0.36))                 # the road: packed dust
    dust = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(30.0, "Distance"), 0.22, 0.1), 0.35), dust, (0.42, 0.3, 0.22))   # ballast
    dust = nb.mix(sleep_m, dust, nb.mix(nb.ramp(nb.noise(8.0, 2, 0.6), 0.3, 0.7), (0.26, 0.17, 0.11), (0.36, 0.24, 0.15)))   # sleepers
    dust = nb.mix(rail_m, dust, nb.mix(nb.ramp(nb.noise(20.0, 2, 0.5), 0.3, 0.7), (0.42, 0.42, 0.44), (0.7, 0.7, 0.72)))        # rails
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.55), c, (0.44, 0.24, 0.14))
    c = nb.mix(road_m, c, dust)
    ore = nb.mix(nb.ramp(nb.noise(1.2, 3, 0.6), 0.3, 0.7), (0.06, 0.3, 0.28), (0.1, 0.48, 0.4))    # the copper pools' basins
    c = nb.mix(ore_m, c, ore)
    mal = nb.math("MULTIPLY", nb.ramp(nb.noise(24.0, 2, 0.5), 0.74, 0.8), nb.math("SUBTRACT", 1.0, road_m))    # malachite flecks
    c = nb.mix(nb.math("MULTIPLY", mal, 0.8), c, (0.18, 0.6, 0.42))
    rough = nb.mixf(rail_m, 0.9, 0.3)
elif THEME == "highland":
    # moorland: short grass, purple heather, brown bracken, dark damp hollows; a forest floor of needles under the pines
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.3, 0.42, 0.16), (0.43, 0.53, 0.22))
    heather = nb.ramp(nb.noise(0.9, 4, 0.6), 0.55, 0.65)
    c = nb.mix(nb.math("MULTIPLY", heather, 0.85), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.36, 0.18, 0.36), (0.56, 0.3, 0.54)))
    bracken = nb.ramp(nb.noise(1.3, 3, 0.6, distort=0.5), 0.66, 0.74)
    c = nb.mix(nb.math("MULTIPLY", bracken, 0.6), c, (0.52, 0.38, 0.2))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.36, 0.24), 0.5), c, (0.2, 0.33, 0.13))
    c = nb.mix(nb.math("MULTIPLY", fine, 0.22), c, (0.48, 0.62, 0.26))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.14, 0.28, 0.1), (0.22, 0.36, 0.14)))
    c = nb.mix(nb.math("MULTIPLY", trees_m, 0.85), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.24, 0.19, 0.11), (0.34, 0.27, 0.15)))
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.5), c, nb.mix(nb.ramp(nb.voronoi(16.0, "Distance"), 0.3, 0.1), (0.42, 0.44, 0.3), (0.56, 0.55, 0.5)))
    track = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.44, 0.36, 0.26), (0.56, 0.47, 0.34))                 # a stony track
    cobble = nb.ramp(nb.voronoi(9.0, "Distance"), 0.3, 0.12)
    track = nb.mix(nb.math("MULTIPLY", cobble, 0.55), track, (0.58, 0.56, 0.52))
    track = nb.mix(nb.math("MULTIPLY", rut_m, 0.6), track, (0.34, 0.27, 0.19))
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.5), c, (0.34, 0.4, 0.18))
    c = nb.mix(road_m, c, track)
    bankc = nb.mix(nb.ramp(nb.voronoi(18.0, "Distance"), 0.35, 0.1), (0.4, 0.4, 0.38), (0.62, 0.6, 0.56))
    c = nb.mix(nb.math("MULTIPLY", bank_m, 0.9), c, bankc)                                        # stony banks
    water = nb.mix(nb.ramp(nb.noise(0.7, 3, 0.6), 0.3, 0.7), (0.1, 0.27, 0.33), (0.18, 0.39, 0.45))
    water = nb.mix(nb.math("MULTIPLY", nb.ramp(water_m, 0.4, 0.0), 1.0), water, (0.3, 0.46, 0.44))  # shallows at the edges
    water = nb.mix(nb.math("MULTIPLY", nb.math("MULTIPLY", road_m, cobble), 0.6), water, (0.46, 0.5, 0.48))   # the ford's cobbles
    water = nb.mix(nb.math("MULTIPLY", road_m, 0.25), water, (0.36, 0.42, 0.4))
    c = nb.mix(water_m, c, water)
    rough = nb.mixf(water_m, 0.9, 0.2)
elif THEME == "forge":
    # soot, cinders and rusty ore earth; glassy slag heaps; a packed-cinder road with a clay wallow; lava pools, fissures
    c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.13, 0.11, 0.1), (0.22, 0.18, 0.15))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.6, 0.74), 0.6), c, (0.4, 0.22, 0.11))            # rusty ore earth
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.34, 0.22), 0.6), c, (0.07, 0.065, 0.06))          # charcoal
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.6, 0.75), 0.35), c, (0.34, 0.28, 0.24))
    fiss = nb.ramp(nb.voronoi(0.8, "Distance", "DISTANCE_TO_EDGE"), 0.014, 0.0)
    fiss = nb.math("MULTIPLY", fiss, nb.ramp(nb.noise(0.5, 2, 0.5), 0.62, 0.7))
    fiss = nb.math("MULTIPLY", fiss, nb.math("SUBTRACT", 1.0, nb.math("MAXIMUM", road_m, edge_m)))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.08, 0.07, 0.06), (0.15, 0.12, 0.1)))
    slagc = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.09, 0.09, 0.11), (0.17, 0.16, 0.19))
    slagc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(9.0, 2, 0.5), 0.66, 0.74), 0.6), slagc, (0.16, 0.26, 0.26))   # glassy sheen
    c = nb.mix(zoneb_m, c, slagc)
    cind = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.33, 0.29, 0.26), (0.44, 0.38, 0.33))                  # the road: packed cinder
    cind = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(30.0, "Distance"), 0.22, 0.1), 0.35), cind, (0.22, 0.2, 0.19))
    cind = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(26.0, 2, 0.5), 0.72, 0.78), 0.5), cind, (0.5, 0.3, 0.16))       # iron flakes
    cind = nb.mix(nb.math("MULTIPLY", rut_m, 0.7), cind, (0.24, 0.21, 0.19))
    clay = nb.mix(nb.ramp(nb.noise(2.5, 3, 0.6), 0.3, 0.7), (0.3, 0.2, 0.13), (0.4, 0.27, 0.17))     # the wallow: wet clay
    clay = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.4, 3, 0.6), 0.62, 0.7), 0.7), clay, (0.18, 0.12, 0.08))
    cind = nb.mix(slow_m, cind, clay)
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.6), c, (0.12, 0.1, 0.09))
    c = nb.mix(road_m, c, cind)
    c = nb.mix(nb.math("MULTIPLY", heat_m, 0.45), c, (0.55, 0.18, 0.05))                          # heat glow round the lava
    lava = nb.mix(nb.ramp(nb.noise(0.9, 4, 0.6, distort=1.5), 0.35, 0.7), (1.0, 0.42, 0.06), (1.0, 0.85, 0.35))
    crust = nb.ramp(nb.voronoi(2.0, "Distance", "DISTANCE_TO_EDGE"), 0.08, 0.16)
    lava = nb.mix(nb.math("MULTIPLY", crust, 0.75), lava, (0.16, 0.07, 0.05))
    c = nb.mix(lava_m, c, lava)
    em = nb.mix(lava_m, nb.mix(fiss, (0, 0, 0), (1.0, 0.42, 0.08)), lava)
    nb.link(em, nb.b.inputs["Emission Color"])
    nb.b.inputs["Emission Strength"].default_value = 1.6
    rough = nb.mixf(nb.math("MAXIMUM", zoneb_m, nb.math("MULTIPLY", slow_m, road_m)), 0.88, 0.35)
elif THEME == "bog":
    # a marsh: sedge, red and green sphagnum, peat; plank trackways, a mud wallow where they meet, black bog pools
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.25, 0.3, 0.12), (0.36, 0.38, 0.16))
    red = nb.ramp(nb.noise(1.1, 4, 0.6), 0.56, 0.66)
    c = nb.mix(nb.math("MULTIPLY", red, 0.8), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.46, 0.2, 0.12), (0.62, 0.32, 0.17)))   # red sphagnum
    green = nb.ramp(nb.noise(1.7, 3, 0.6, distort=0.4), 0.64, 0.72)
    c = nb.mix(nb.math("MULTIPLY", green, 0.7), c, (0.46, 0.54, 0.18))                              # bright moss
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.42, 0.26), 0.7), c, (0.15, 0.12, 0.08))           # wet peat hollows
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(0.6, 3, 0.6), 0.6, 0.66), 0.45), c, (0.48, 0.44, 0.24))   # dry tawny grass
    c = nb.mix(nb.math("MULTIPLY", fine, 0.2), c, (0.4, 0.48, 0.2))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.11, 0.16, 0.07), (0.17, 0.22, 0.1)))
    c = nb.mix(nb.math("MULTIPLY", trees_m, 0.8), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.18, 0.16, 0.09), (0.27, 0.23, 0.13)))
    mud = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.24, 0.18, 0.12), (0.32, 0.24, 0.15))                    # mud under and round the planks
    mud = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.8, 3, 0.6), 0.6, 0.68), 0.7), mud, (0.12, 0.1, 0.07))    # puddles
    plank = nb.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    plank.inputs["Scale"].default_value = 40.0
    plank.inputs["Distortion"].default_value = 3.0
    plank.inputs["Detail"].default_value = 2.0
    nb.link(nb.uvn.outputs["Object"], plank.inputs["Vector"])
    wood = nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.4, 0.29, 0.18), (0.52, 0.39, 0.25))
    wood = nb.mix(nb.math("MULTIPLY", nb.ramp(plank.outputs["Fac"], 0.6, 0.9), 0.3), wood, (0.32, 0.22, 0.13))   # grain
    wood = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.0, 3, 0.6), 0.62, 0.7), 0.5), wood, (0.26, 0.24, 0.16))  # weathered grey-green
    trk = nb.mix(sleep_m, mud, wood)
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.6), c, (0.2, 0.17, 0.1))
    c = nb.mix(road_m, c, trk)
    pool = nb.mix(nb.ramp(nb.noise(0.8, 3, 0.6), 0.3, 0.7), (0.11, 0.12, 0.08), (0.2, 0.2, 0.13))   # dark peaty water
    pool = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(0.5, 2, 0.5), 0.4, 0.7), 0.35), pool, (0.3, 0.36, 0.38))   # the sky in it
    pool = nb.mix(nb.math("MULTIPLY", nb.ramp(water_m, 0.7, 0.2), 1.0), pool, (0.32, 0.38, 0.14))    # green scum at the edges
    pool = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(6.0, 2, 0.5), 0.66, 0.72), nb.ramp(water_m, 0.9, 0.4)), pool, (0.42, 0.48, 0.18))
    c = nb.mix(water_m, c, pool)
    rough = nb.mixf(nb.math("MAXIMUM", water_m, nb.math("MULTIPLY", road_m, nb.math("SUBTRACT", 1.0, sleep_m))), 0.88, 0.22)
elif THEME == "olive":
    # a dry hillside: golden grass, greener hollows, red earth and limestone showing through; red earth under the olives
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.6, 0.52, 0.26), (0.74, 0.64, 0.34))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.36, 0.24), 0.6), c, (0.42, 0.46, 0.2))
    terra = nb.ramp(nb.noise(1.1, 4, 0.6, distort=0.4), 0.62, 0.72)
    c = nb.mix(nb.math("MULTIPLY", terra, 0.75), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.52, 0.3, 0.18), (0.64, 0.4, 0.24)))
    lime = nb.ramp(nb.noise(2.2, 3, 0.6), 0.7, 0.76)
    c = nb.mix(nb.math("MULTIPLY", lime, 0.6), c, (0.8, 0.77, 0.68))
    c = nb.mix(nb.math("MULTIPLY", fine, 0.2), c, (0.82, 0.72, 0.42))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.36, 0.34, 0.18), (0.46, 0.42, 0.22)))
    grove = nb.mix(nb.ramp(fine, 0.3, 0.7), (0.5, 0.32, 0.2), (0.6, 0.4, 0.26))
    grove = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(30.0, 2, 0.5), 0.66, 0.72), 0.6), grove, (0.56, 0.6, 0.46))   # fallen leaves
    c = nb.mix(nb.math("MULTIPLY", trees_m, 0.85), c, grove)
    flag = nb.ramp(nb.voronoi(3.2, "Distance", "DISTANCE_TO_EDGE"), 0.02, 0.06)
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.75), c, nb.mix(nb.math("SUBTRACT", 1.0, flag), (0.84, 0.82, 0.76), (0.56, 0.52, 0.46)))
    track = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.66, 0.54, 0.38), (0.77, 0.66, 0.49))                  # a dusty track
    track = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(30.0, "Distance"), 0.22, 0.1), 0.35), track, (0.52, 0.44, 0.34))
    track = nb.mix(nb.math("MULTIPLY", rut_m, 0.55), track, (0.56, 0.44, 0.3))
    run = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.8, 0.7, 0.54), (0.88, 0.8, 0.64))     # the downhill runs: scuffed smooth
    run = nb.mix(nb.math("MULTIPLY", chev_m, 0.75), run, (0.96, 0.92, 0.8))
    track = nb.mix(lane_m, track, run)
    scree = nb.mix(nb.ramp(nb.voronoi(14.0, "Distance"), 0.35, 0.08), (0.48, 0.45, 0.4), (0.74, 0.72, 0.66))    # the climbs: scree
    track = nb.mix(slow_m, track, scree)
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.5), c, (0.56, 0.48, 0.26))
    c = nb.mix(road_m, c, track)
    rough = 0.9
elif THEME == "coast":
    # coastal scrub on sandy ground, limestone, white beaches, a turquoise inlet; a Roman road of flagstones
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.72, 0.64, 0.44), (0.83, 0.74, 0.53))
    maq = nb.ramp(nb.noise(1.3, 4, 0.6, distort=0.4), 0.56, 0.66)
    c = nb.mix(nb.math("MULTIPLY", maq, 0.8), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.26, 0.36, 0.16), (0.36, 0.46, 0.2)))
    lime = nb.ramp(nb.noise(2.0, 3, 0.6), 0.7, 0.77)
    c = nb.mix(nb.math("MULTIPLY", lime, 0.6), c, (0.88, 0.86, 0.8))
    c = nb.mix(nb.math("MULTIPLY", fine, 0.2), c, (0.9, 0.82, 0.6))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.4, 0.4, 0.26), (0.5, 0.48, 0.32)))
    flag = nb.ramp(nb.voronoi(3.2, "Distance", "DISTANCE_TO_EDGE"), 0.02, 0.06)
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.75), c, nb.mix(nb.math("SUBTRACT", 1.0, flag), (0.86, 0.84, 0.78), (0.58, 0.54, 0.48)))
    pave = nb.mix(nb.ramp(nb.noise(2.5, 3, 0.6), 0.3, 0.7), (0.6, 0.58, 0.54), (0.73, 0.71, 0.65))   # the flagstones
    pflag = nb.ramp(nb.voronoi(2.8, "Distance", "DISTANCE_TO_EDGE"), 0.02, 0.055)
    pave = nb.mix(nb.math("SUBTRACT", 1.0, pflag), pave, (0.36, 0.34, 0.3))
    pave = nb.mix(nb.math("MULTIPLY", rut_m, 0.3), pave, (0.5, 0.48, 0.44))
    pave = nb.mix(nb.math("MULTIPLY", tun_m, 0.6), pave, (0.32, 0.31, 0.3))                            # in the aqueducts' shadow
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.5), c, (0.6, 0.56, 0.42))
    c = nb.mix(road_m, c, pave)
    beach = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.88, 0.82, 0.64), (0.96, 0.91, 0.76))
    beach = nb.mix(nb.math("MULTIPLY", nb.ramp(bank_m, 0.5, 1.0), 0.6), beach, (0.7, 0.62, 0.46))   # wet sand by the water
    c = nb.mix(nb.math("MULTIPLY", bank_m, 0.95), c, beach)
    water = nb.mix(nb.ramp(nb.noise(0.7, 3, 0.6), 0.3, 0.7), (0.05, 0.3, 0.44), (0.1, 0.42, 0.55))
    water = nb.mix(nb.math("MULTIPLY", nb.ramp(water_m, 0.5, 0.0), 1.0), water, (0.24, 0.66, 0.68))   # turquoise shallows
    c = nb.mix(water_m, c, water)
    rough = nb.mixf(water_m, 0.9, 0.18)
elif THEME == "acropolis":
    # a hill of pale limestone, its crevices grassy, pockets of red earth; a road of marble slabs
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.68, 0.64, 0.56), (0.8, 0.76, 0.68))
    crev = nb.ramp(nb.voronoi(1.4, "Distance", "DISTANCE_TO_EDGE"), 0.03, 0.0)
    c = nb.mix(nb.math("MULTIPLY", crev, 0.7), c, (0.4, 0.38, 0.28))
    gr = nb.ramp(nb.noise(1.2, 4, 0.6, distort=0.4), 0.58, 0.68)
    c = nb.mix(nb.math("MULTIPLY", gr, 0.75), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.52, 0.5, 0.26), (0.66, 0.6, 0.32)))   # dry grass
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.32, 0.22), 0.6), c, (0.36, 0.42, 0.2))                                  # scrub
    terra = nb.ramp(nb.noise(2.4, 3, 0.6), 0.7, 0.76)
    c = nb.mix(nb.math("MULTIPLY", terra, 0.6), c, (0.6, 0.36, 0.22))
    c = nb.mix(nb.math("MULTIPLY", fine, 0.2), c, (0.88, 0.84, 0.76))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.46, 0.42, 0.34), (0.56, 0.52, 0.42)))
    flag = nb.ramp(nb.voronoi(3.2, "Distance", "DISTANCE_TO_EDGE"), 0.02, 0.06)
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.8), c, nb.mix(nb.math("SUBTRACT", 1.0, flag), (0.9, 0.88, 0.82), (0.6, 0.56, 0.5)))
    marble = nb.mix(nb.ramp(nb.noise(2.2, 3, 0.6), 0.3, 0.7), (0.84, 0.82, 0.76), (0.93, 0.91, 0.86))
    vein = nb.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL")
    vein.inputs["Scale"].default_value = 1.6
    vein.inputs["Distortion"].default_value = 12.0
    vein.inputs["Detail"].default_value = 4.0
    nb.link(nb.uvn.outputs["Object"], vein.inputs["Vector"])
    marble = nb.mix(nb.math("MULTIPLY", nb.ramp(vein.outputs["Fac"], 0.9, 0.98), 0.4), marble, (0.62, 0.62, 0.64))
    marble = nb.mix(sleep_m, marble, (0.5, 0.47, 0.42))                                                  # the slabs' joints
    marble = nb.mix(nb.math("MULTIPLY", rut_m, 0.2), marble, (0.72, 0.7, 0.64))
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.55), c, (0.6, 0.56, 0.48))
    c = nb.mix(road_m, c, marble)
    rough = nb.mixf(road_m, 0.9, 0.55)
else:   # volcano
    c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.13, 0.11, 0.11), (0.24, 0.2, 0.18))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.6, 0.74), 0.6), c, (0.36, 0.22, 0.15))         # rusty ash
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.6, 0.75), 0.4), c, (0.32, 0.29, 0.27))
    fiss = nb.ramp(nb.voronoi(0.7, "Distance", "DISTANCE_TO_EDGE"), 0.016, 0.0)
    fiss = nb.math("MULTIPLY", fiss, nb.ramp(nb.noise(0.45, 2, 0.5), 0.56, 0.66))
    fiss = nb.math("MULTIPLY", fiss, nb.math("SUBTRACT", 1.0, nb.math("MAXIMUM", road_m, edge_m)))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.07, 0.06, 0.06), (0.14, 0.11, 0.1)))
    ashroad = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.36, 0.32, 0.29), (0.47, 0.42, 0.37))
    ashroad = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(30.0, "Distance"), 0.22, 0.1), 0.3), ashroad, (0.26, 0.23, 0.21))
    ashroad = nb.mix(nb.math("MULTIPLY", rut_m, 0.75), ashroad, (0.26, 0.23, 0.21))
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.6), c, (0.1, 0.08, 0.08))
    c = nb.mix(road_m, c, ashroad)
    c = nb.mix(nb.math("MULTIPLY", tun_m, 0.5), c, (0.12, 0.1, 0.09))
    c = nb.mix(nb.math("MULTIPLY", heat_m, 0.45), c, (0.55, 0.16, 0.05))                          # heat glow round lava
    lava = nb.mix(nb.ramp(nb.noise(0.9, 4, 0.6, distort=1.5), 0.35, 0.7), (1.0, 0.42, 0.06), (1.0, 0.85, 0.35))
    crust = nb.ramp(nb.voronoi(2.0, "Distance", "DISTANCE_TO_EDGE"), 0.08, 0.16)
    lava = nb.mix(nb.math("MULTIPLY", crust, 0.75), lava, (0.16, 0.07, 0.05))
    c = nb.mix(lava_m, c, lava)
    em = nb.mix(lava_m, nb.mix(fiss, (0, 0, 0), (1.0, 0.42, 0.08)), lava)
    nb.link(em, nb.b.inputs["Emission Color"])
    nb.b.inputs["Emission Strength"].default_value = 1.6
    rough = 0.85
rk_c = nb.mix(nb.ramp(nb.voronoi(14.0, "Distance"), 0.3, 0.05), (0.36, 0.36, 0.38), (0.6, 0.59, 0.57))
c = nb.mix(nb.math("MULTIPLY", rock_m, 0.6), c, rk_c)
nb.link(c, nb.b.inputs["Base Color"])
if isinstance(rough, float):
    nb.b.inputs["Roughness"].default_value = rough
else:
    nb.link(rough, nb.b.inputs["Roughness"])
bump = nb.n("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.35
bump.inputs["Distance"].default_value = 0.02
nb.link(nb.math("ADD", fine, nb.math("MULTIPLY", nb.noise(40.0, 2, 0.5), 0.5)), bump.inputs["Height"])
nb.link(bump.outputs["Normal"], nb.b.inputs["Normal"])
me.materials.append(nb.m)


# ------------------------------------------------------------------------------------------------ scattered detail
def merged(name, template, xforms, mat):
    """One mesh of many transformed copies of a template (vertices Nx3, faces as index tuples)."""
    tv, tf = template
    tv = np.asarray(tv, np.float32)
    n = len(xforms)
    allv = np.empty((n * len(tv), 3), np.float32)
    for i, (pos, yaw, s, tilt) in enumerate(xforms):
        c, s_ = math.cos(yaw), math.sin(yaw)
        R = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]], np.float32)
        if tilt:
            tx, ty = tilt
            Rx = np.array([[1, 0, 0], [0, math.cos(tx), -math.sin(tx)], [0, math.sin(tx), math.cos(tx)]], np.float32)
            Ry = np.array([[math.cos(ty), 0, math.sin(ty)], [0, 1, 0], [-math.sin(ty), 0, math.cos(ty)]], np.float32)
            R = R @ Rx @ Ry
        allv[i * len(tv):(i + 1) * len(tv)] = (tv * s) @ R.T + np.asarray(pos, np.float32)
    faces = [tuple(int(k) + i * len(tv) for k in f) for i in range(n) for f in tf]
    me2 = bpy.data.meshes.new(name)
    me2.from_pydata(allv.tolist(), [], faces)
    me2.update()
    zt = tv[:, 2] / max(float(tv[:, 2].max()), 1e-6)            # 0 at the root of a blade, 1 at its tip
    at = me2.attributes.new("tip", "FLOAT", "POINT")
    at.data.foreach_set("value", np.tile(np.clip(zt, 0, 1), n).astype(np.float32))
    for p in me2.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me2)
    sc.collection.objects.link(ob)
    me2.materials.append(mat)
    return ob


def blade_mat(name, root, mid, tip, rough=0.7):
    """Grass blades: dark at the root, bright at the tip (attribute 'tip'), varied in patches."""
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    nt = mt.node_tree
    bb = nt.nodes["Principled BSDF"]
    att = nt.nodes.new("ShaderNodeAttribute")
    att.attribute_name = "tip"
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = lin(root)
    rp.color_ramp.elements[1].color = lin(tip)
    e = rp.color_ramp.elements.new(0.45)
    e.color = lin(mid)
    nt.links.new(att.outputs["Fac"], rp.inputs["Fac"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.5
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    hue = nt.nodes.new("ShaderNodeHueSaturation")
    nt.links.new(rp.outputs["Color"], hue.inputs["Color"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.78
    mr.inputs["To Max"].default_value = 1.18
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], hue.inputs["Value"])
    nt.links.new(hue.outputs["Color"], bb.inputs["Base Color"])
    bb.inputs["Roughness"].default_value = rough
    return mt


def simple_mat(name, col, rough=0.8, emit=None, strength=0.0, var=None):
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    bb = mt.node_tree.nodes["Principled BSDF"]
    bb.inputs["Base Color"].default_value = lin(col)
    bb.inputs["Roughness"].default_value = rough
    if emit is not None:
        bb.inputs["Emission Color"].default_value = lin(emit)
        bb.inputs["Emission Strength"].default_value = strength
    if var is not None:      # per-object-random colour variation via object coords noise
        nt = mt.node_tree
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 3.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.inputs["A"].default_value = lin(col)
        mx.inputs["B"].default_value = lin(var)
        nt.links.new(nz.outputs["Fac"], mx.inputs["Factor"])
        nt.links.new(mx.outputs["Result"], bb.inputs["Base Color"])
    return mt


def tuft_template(n_bl=7, h=0.11, w=0.012):
    V, F = [], []
    for i in range(n_bl):
        a = 2 * math.pi * i / n_bl + RNG.uniform(-0.3, 0.3)
        hh = h * RNG.uniform(0.6, 1.15)
        lean = RNG.uniform(0.25, 0.6)
        bx, by = 0.012 * math.cos(a), 0.012 * math.sin(a)
        px, py = -math.sin(a) * w, math.cos(a) * w
        tip = (bx + math.cos(a) * hh * lean, by + math.sin(a) * hh * lean, hh)
        k = len(V)
        V += [(bx - px, by - py, 0.0), (bx + px, by + py, 0.0), tip]
        F.append((k, k + 1, k + 2))
    return V, F


def blob_template(sub=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in bm.verts:
        v.co *= RNG.uniform(0.82, 1.12)
    V = [tuple(v.co) for v in bm.verts]
    F = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return V, F


def flower_template(petals=5, r=0.03):
    V = [(0, 0, 0.06)]
    F = []
    for i in range(petals * 2):
        a = 2 * math.pi * i / (petals * 2)
        rr = r if i % 2 == 0 else r * 0.45
        V.append((rr * math.cos(a), rr * math.sin(a), 0.06))
    for i in range(petals * 2):
        F.append((0, 1 + i, 1 + (i + 1) % (petals * 2)))
    return V, F


def scatter(n, accept, jitter_seed=0):
    """n positions (x, z) in the ground rect where accept(x, z) (vectorised) is true."""
    out = []
    tries = 0
    while len(out) < n and tries < 30:
        tries += 1
        xs_ = RNG.uniform(G.X0, G.X0 + G.W, n * 2)
        zs_ = RNG.uniform(G.Z0, G.Z0 + G.H, n * 2)
        ok = accept(xs_, zs_)
        for x, z in zip(xs_[ok], zs_[ok]):
            out.append((x, z))
            if len(out) >= n:
                break
    return out


def hgt(x, z):
    return sample(hf, np.asarray(x), np.asarray(z))


def place_list(pts, s_lo, s_hi, sink=0.0, tilt=0.0):
    pts = np.array(pts)
    hs = hgt(pts[:, 0], pts[:, 1])
    out = []
    for (x, z), h in zip(pts, hs):
        s = RNG.uniform(s_lo, s_hi)
        out.append(((x, -z, h - sink * s), RNG.uniform(0, 2 * math.pi), s,
                    (RNG.uniform(-tilt, tilt), RNG.uniform(-tilt, tilt)) if tilt else None))
    return out


rd = lambda x, z: sample(dist, x, z)
inside_pf = lambda x, z: sample(outside, x, z) < 0.5
BLK_ALL = np.minimum.reduce([blk[k] for k in ("palms", "dune", "ruins", "pillar", "ore", "slag", "statue")])
PATCH = fbm(0.9, 4, 0)                   # where heather (highland) and rushes (bog) grow thick
no_blk = lambda x, z: (sample(blk["lake"], x, z) > 0.2) & (sample(blk["lava"], x, z) > 0.3) & (sample(blk["rocks"], x, z) > 0.1) & \
    (sample(BLK_ALL, x, z) > 0.15)

if THEME == "meadow":
    blades = blade_mat("Blades", (0.3, 0.53, 0.15), (0.44, 0.68, 0.21), (0.68, 0.86, 0.36))
    pts = scatter(22000 if not PREVIEW else 3000, lambda x, z: (rd(x, z) > HALF + 0.1) & no_blk(x, z))
    merged("Tufts", tuft_template(9, 0.12, 0.014), place_list(pts, 0.75, 1.5), blades)
    pts = scatter(2600 if not PREVIEW else 400, lambda x, z: (rd(x, z) > HALF + 0.3) & no_blk(x, z))
    merged("BigTufts", tuft_template(12, 0.2, 0.018), place_list(pts, 0.8, 1.3), blades)
    pts = scatter(3500 if not PREVIEW else 500, lambda x, z: (np.abs(rd(x, z) - HALF - 0.04) < 0.09))      # grass over the road edge
    merged("EdgeTufts", tuft_template(6, 0.08, 0.012), place_list(pts, 0.8, 1.3),
           blade_mat("EdgeBlades", (0.2, 0.36, 0.1), (0.38, 0.56, 0.17), (0.64, 0.76, 0.32)))
    # flowers in little clusters
    for k, col in enumerate([(1.0, 1.0, 0.94), (1.0, 0.84, 0.22), (0.96, 0.52, 0.78), (0.58, 0.68, 1.0)]):
        centres = scatter(70 if not PREVIEW else 20, lambda x, z: (rd(x, z) > HALF + 0.5) & inside_pf(x, z) & no_blk(x, z))
        pts = []
        for cx, cz in centres:
            for _ in range(int(RNG.integers(3, 8))):
                pts.append((cx + RNG.normal(0, 0.12), cz + RNG.normal(0, 0.12)))
        merged("Flowers%d" % k, flower_template(5, 0.04), place_list(pts, 0.8, 1.25), simple_mat("Petal%d" % k, col, 0.45))
    peb = simple_mat("Pebble", (0.42, 0.37, 0.32), 0.8, var=(0.6, 0.55, 0.48))
    pts = scatter(3400 if not PREVIEW else 500, lambda x, z: rd(x, z) < HALF + 0.15)
    merged("Pebbles", blob_template(1), place_list(pts, 0.015, 0.045, sink=0.35), peb)
    pts = scatter(140, lambda x, z: (np.abs(rd(x, z) - HALF - 0.2) < 0.3) & inside_pf(x, z))
    merged("Stones", blob_template(2), place_list(pts, 0.05, 0.13, sink=0.45), simple_mat("Stone", (0.52, 0.52, 0.5), 0.8, var=(0.68, 0.66, 0.62)))
elif THEME == "snow":
    snow = simple_mat("Lump", (0.93, 0.95, 1.0), 0.6)
    pts = scatter(1600 if not PREVIEW else 300, lambda x, z: (rd(x, z) > HALF + 0.15) & no_blk(x, z))
    merged("Lumps", blob_template(2), [(p, y, s, None) for (p, y, s, t) in place_list(pts, 0.04, 0.12, sink=0.55)], snow)
    peb = simple_mat("Pebble", (0.42, 0.42, 0.45), 0.7, var=(0.58, 0.58, 0.62))
    pts = scatter(1100 if not PREVIEW else 200, lambda x, z: (rd(x, z) < HALF + 0.2) & (sample(lane, x, z) < 0.5))
    merged("Pebbles", blob_template(1), place_list(pts, 0.012, 0.03, sink=0.3), peb)
    pts = scatter(70, lambda x, z: (np.abs(rd(x, z) - HALF - 0.35) < 0.3) & no_blk(x, z))
    merged("Stones", blob_template(2), place_list(pts, 0.05, 0.12, sink=0.4), simple_mat("Stone", (0.48, 0.5, 0.54), 0.8, var=(0.62, 0.64, 0.68)))
    dry = simple_mat("DryGrass", (0.55, 0.48, 0.3), 0.8, var=(0.68, 0.6, 0.4))
    pts = scatter(700 if not PREVIEW else 150, lambda x, z: (rd(x, z) > HALF + 0.5) & no_blk(x, z) & (sample(slow, x, z) < 0.1))
    merged("DryTufts", tuft_template(6, 0.1, 0.01), place_list(pts, 0.7, 1.3), dry)
elif THEME == "delta":
    wet = lambda x, z: (sample(water_all, x, z) < 0.05)
    blades = blade_mat("Blades", (0.26, 0.5, 0.13), (0.4, 0.66, 0.19), (0.64, 0.86, 0.33))
    pts = scatter(20000 if not PREVIEW else 3000, lambda x, z: (rd(x, z) > HALF + 0.1) & no_blk(x, z) & wet(x, z) & (sample(bank, x, z) < 0.5))
    merged("Tufts", tuft_template(9, 0.12, 0.014), place_list(pts, 0.75, 1.5), blades)
    pts = scatter(2400 if not PREVIEW else 400, lambda x, z: (rd(x, z) > HALF + 0.3) & no_blk(x, z) & wet(x, z))
    merged("BigTufts", tuft_template(12, 0.2, 0.018), place_list(pts, 0.8, 1.3), blades)
    reeds = blade_mat("Reeds", (0.2, 0.36, 0.12), (0.34, 0.54, 0.18), (0.62, 0.7, 0.32))
    pts = scatter(2600 if not PREVIEW else 400, lambda x, z: ((np.abs(sample(riv, x, z) - 0.05) < 0.22) | (np.abs(sample(blk["lake"], x, z) - 0.05) < 0.25)) & (rd(x, z) > HALF + 0.2))
    merged("Reeds", tuft_template(8, 0.34, 0.012), place_list(pts, 0.7, 1.3), reeds)                       # reeds along the water
    pts = scatter(3000 if not PREVIEW else 500, lambda x, z: (np.abs(rd(x, z) - HALF - 0.04) < 0.09) & wet(x, z))
    merged("EdgeTufts", tuft_template(6, 0.08, 0.012), place_list(pts, 0.8, 1.3),
           blade_mat("EdgeBlades", (0.2, 0.36, 0.1), (0.38, 0.56, 0.17), (0.64, 0.76, 0.32)))
    for k, col in enumerate([(1.0, 1.0, 0.94), (0.98, 0.62, 0.8), (0.48, 0.62, 1.0), (1.0, 0.84, 0.22)]):
        centres = scatter(60 if not PREVIEW else 20, lambda x, z: (rd(x, z) > HALF + 0.5) & inside_pf(x, z) & no_blk(x, z) & wet(x, z))
        pts = []
        for cx, cz in centres:
            for _ in range(int(RNG.integers(3, 8))):
                pts.append((cx + RNG.normal(0, 0.12), cz + RNG.normal(0, 0.12)))
        merged("Flowers%d" % k, flower_template(5, 0.04), place_list(pts, 0.8, 1.25), simple_mat("Petal%d" % k, col, 0.45))
    peb = simple_mat("Pebble", (0.46, 0.4, 0.33), 0.8, var=(0.64, 0.58, 0.5))
    pts = scatter(3000 if not PREVIEW else 500, lambda x, z: rd(x, z) < HALF + 0.15)
    merged("Pebbles", blob_template(1), place_list(pts, 0.015, 0.045, sink=0.35), peb)
    pts = scatter(900 if not PREVIEW else 150, lambda x, z: sample(bank, x, z) > 0.4)
    merged("BankStones", blob_template(1), place_list(pts, 0.02, 0.05, sink=0.4), simple_mat("BankStone", (0.6, 0.55, 0.46), 0.8, var=(0.74, 0.68, 0.56)))
elif THEME == "desert":
    dry = simple_mat("DryGrass", (0.6, 0.5, 0.28), 0.8, var=(0.74, 0.62, 0.36))
    pts = scatter(1500 if not PREVIEW else 300, lambda x, z: (rd(x, z) > HALF + 0.4) & no_blk(x, z) & (sample(blk["ruins"], x, z) > 0.2))
    merged("DryTufts", tuft_template(7, 0.11, 0.011), place_list(pts, 0.7, 1.3), dry)
    peb = simple_mat("Pebble", (0.6, 0.5, 0.38), 0.8, var=(0.76, 0.66, 0.5))
    pts = scatter(2400 if not PREVIEW else 400, lambda x, z: (rd(x, z) > HALF + 0.05) & no_blk(x, z))
    merged("Pebbles", blob_template(1), place_list(pts, 0.012, 0.035, sink=0.35), peb)
    pts = scatter(160, lambda x, z: (np.abs(rd(x, z) - HALF - 0.3) < 0.35) & inside_pf(x, z))
    merged("Stones", blob_template(2), place_list(pts, 0.05, 0.12, sink=0.45), simple_mat("Stone", (0.66, 0.58, 0.46), 0.8, var=(0.8, 0.72, 0.58)))
    sand = simple_mat("Drift", (0.9, 0.76, 0.52), 0.9, var=(0.96, 0.84, 0.6))
    pts = scatter(700 if not PREVIEW else 150, lambda x, z: (rd(x, z) > HALF + 0.2) & (rd(x, z) < HALF + 0.9))
    merged("Drifts", blob_template(2), [(p, y, s, None) for (p, y, s, t) in place_list(pts, 0.08, 0.2, sink=0.75)], sand)
elif THEME == "canyon":
    peb = simple_mat("Pebble", (0.5, 0.27, 0.16), 0.8, var=(0.66, 0.38, 0.22))
    pts = scatter(3200 if not PREVIEW else 500, lambda x, z: (rd(x, z) > HALF + 0.05) & no_blk(x, z))
    merged("Pebbles", blob_template(1), place_list(pts, 0.012, 0.04, sink=0.3), peb)
    pts = scatter(180, lambda x, z: (np.abs(rd(x, z) - HALF - 0.4) < 0.4) & no_blk(x, z))
    merged("Rocks", blob_template(2), place_list(pts, 0.06, 0.16, sink=0.4, tilt=0.3), simple_mat("Rock", (0.5, 0.26, 0.15), 0.8, var=(0.66, 0.36, 0.2)))
    dry = simple_mat("Scrub", (0.42, 0.38, 0.2), 0.8, var=(0.56, 0.5, 0.26))
    pts = scatter(700 if not PREVIEW else 150, lambda x, z: (rd(x, z) > HALF + 0.5) & no_blk(x, z))
    merged("Scrub", tuft_template(8, 0.09, 0.012), place_list(pts, 0.8, 1.4), dry)
    ore = simple_mat("Malachite", (0.12, 0.5, 0.36), 0.5, var=(0.24, 0.66, 0.48))
    pts = scatter(260 if not PREVIEW else 60, lambda x, z: (rd(x, z) > HALF + 0.3) & no_blk(x, z))
    merged("Ore", blob_template(1), place_list(pts, 0.012, 0.03, sink=0.25), ore)
elif THEME == "highland":
    dry_w = lambda x, z: (sample(water_all, x, z) < 0.05)
    blades = blade_mat("Blades", (0.26, 0.42, 0.13), (0.4, 0.56, 0.19), (0.64, 0.74, 0.32))
    pts = scatter(18000 if not PREVIEW else 3000, lambda x, z: (rd(x, z) > HALF + 0.1) & no_blk(x, z) & dry_w(x, z) & (sample(bank, x, z) < 0.5))
    merged("Tufts", tuft_template(9, 0.11, 0.014), place_list(pts, 0.75, 1.4), blades)
    heath = blade_mat("Heather", (0.22, 0.26, 0.12), (0.38, 0.26, 0.34), (0.66, 0.42, 0.66))
    pts = scatter(5200 if not PREVIEW else 800, lambda x, z: (rd(x, z) > HALF + 0.25) & no_blk(x, z) & dry_w(x, z) &
                  (sample(PATCH, x, z) > 0.55))
    merged("Heather", tuft_template(11, 0.09, 0.016), place_list(pts, 0.8, 1.4), heath)
    brack = blade_mat("Bracken", (0.3, 0.26, 0.12), (0.48, 0.36, 0.18), (0.66, 0.5, 0.26))
    pts = scatter(1500 if not PREVIEW else 300, lambda x, z: (rd(x, z) > HALF + 0.5) & no_blk(x, z) & dry_w(x, z))
    merged("Bracken", tuft_template(7, 0.17, 0.022), place_list(pts, 0.8, 1.3), brack)
    reeds = blade_mat("Reeds", (0.2, 0.34, 0.12), (0.34, 0.5, 0.18), (0.6, 0.66, 0.32))
    pts = scatter(1400 if not PREVIEW else 300, lambda x, z: (np.abs(sample(blk["lake"], x, z) - 0.05) < 0.25) & (rd(x, z) > HALF + 0.2))
    merged("Reeds", tuft_template(8, 0.3, 0.012), place_list(pts, 0.7, 1.3), reeds)
    for k, col in enumerate([(1.0, 0.86, 0.24), (1.0, 1.0, 0.94), (0.62, 0.5, 0.96)]):          # tormentil, eyebright, harebells
        centres = scatter(55 if not PREVIEW else 15, lambda x, z: (rd(x, z) > HALF + 0.5) & inside_pf(x, z) & no_blk(x, z) & dry_w(x, z))
        pts = []
        for cx, cz in centres:
            for _ in range(int(RNG.integers(3, 7))):
                pts.append((cx + RNG.normal(0, 0.12), cz + RNG.normal(0, 0.12)))
        merged("Flowers%d" % k, flower_template(5, 0.035), place_list(pts, 0.8, 1.2), simple_mat("Petal%d" % k, col, 0.45))
    peb = simple_mat("Pebble", (0.46, 0.44, 0.4), 0.8, var=(0.62, 0.6, 0.55))
    pts = scatter(3200 if not PREVIEW else 500, lambda x, z: (rd(x, z) < HALF + 0.15) & dry_w(x, z))
    merged("Pebbles", blob_template(1), place_list(pts, 0.015, 0.045, sink=0.35), peb)
    stone = simple_mat("BankStone", (0.5, 0.5, 0.48), 0.75, var=(0.68, 0.67, 0.63))
    pts = scatter(1300 if not PREVIEW else 200, lambda x, z: (sample(bank, x, z) > 0.35) & (rd(x, z) > HALF))
    merged("BankStones", blob_template(1), place_list(pts, 0.025, 0.07, sink=0.4), stone)
    pts = scatter(240 if not PREVIEW else 60, lambda x, z: (sample(riv, x, z) < 0.0) & (rd(x, z) < HALF - 0.1))
    merged("FordStones", blob_template(2), [(p, y, s, None) for (p, y, s, t) in place_list(pts, 0.06, 0.11, sink=0.7)], stone)   # stepping stones
    pts = scatter(90, lambda x, z: (np.abs(rd(x, z) - HALF - 0.35) < 0.35) & no_blk(x, z) & dry_w(x, z))
    merged("Stones", blob_template(2), place_list(pts, 0.05, 0.13, sink=0.45), simple_mat("Stone", (0.52, 0.52, 0.5), 0.8, var=(0.66, 0.65, 0.62)))
elif THEME == "forge":
    cinder = simple_mat("Cinder", (0.17, 0.14, 0.12), 0.8, var=(0.3, 0.25, 0.21))
    pts = scatter(2600 if not PREVIEW else 500, lambda x, z: (rd(x, z) > HALF + 0.05) & no_blk(x, z))
    merged("Cinders", blob_template(1), place_list(pts, 0.015, 0.05, sink=0.3), cinder)
    slag = simple_mat("Slag", (0.1, 0.1, 0.12), 0.3, var=(0.18, 0.2, 0.22))
    pts = scatter(900 if not PREVIEW else 200, lambda x, z: (sample(blk["slag"], x, z) < 0.25) & (rd(x, z) > HALF + 0.1))
    merged("SlagLumps", blob_template(2), place_list(pts, 0.03, 0.1, sink=0.35, tilt=0.4), slag)
    ore = simple_mat("Ore", (0.36, 0.18, 0.09), 0.8, var=(0.5, 0.26, 0.12))
    pts = scatter(700 if not PREVIEW else 150, lambda x, z: (rd(x, z) > HALF + 0.2) & no_blk(x, z) & (sample(blk["slag"], x, z) > 0.3))
    merged("Ore", blob_template(1), place_list(pts, 0.02, 0.05, sink=0.3), ore)
    peb = simple_mat("Pebble", (0.4, 0.36, 0.32), 0.75, var=(0.52, 0.47, 0.42))
    pts = scatter(1600 if not PREVIEW else 300, lambda x, z: (rd(x, z) < HALF + 0.2) & (sample(slow, x, z) < 0.3))
    merged("Pebbles", blob_template(1), place_list(pts, 0.012, 0.03, sink=0.3), peb)
    ember = simple_mat("Ember", (0.3, 0.1, 0.05), 0.6, emit=(1.0, 0.4, 0.08), strength=3.0)
    pts = scatter(240 if not PREVIEW else 60, lambda x, z: (rd(x, z) > HALF + 0.3) & no_blk(x, z))
    merged("Embers", blob_template(1), place_list(pts, 0.012, 0.028, sink=0.2), ember)
    dead = simple_mat("DeadGrass", (0.32, 0.27, 0.18), 0.85, var=(0.42, 0.36, 0.24))
    pts = scatter(500 if not PREVIEW else 100, lambda x, z: (sample(outside, x, z) > 0.3) & no_blk(x, z))
    merged("DeadTufts", tuft_template(7, 0.09, 0.011), place_list(pts, 0.7, 1.2), dead)
elif THEME == "bog":
    wet = lambda x, z: (sample(water_all, x, z) < 0.05)
    sedge = blade_mat("Sedge", (0.2, 0.28, 0.1), (0.34, 0.44, 0.16), (0.58, 0.62, 0.3))
    pts = scatter(20000 if not PREVIEW else 3000, lambda x, z: (rd(x, z) > HALF + 0.12) & no_blk(x, z) & wet(x, z))
    merged("Tufts", tuft_template(9, 0.14, 0.012), place_list(pts, 0.75, 1.5), sedge)
    rush = blade_mat("Rushes", (0.14, 0.24, 0.08), (0.24, 0.36, 0.12), (0.4, 0.48, 0.18))
    pts = scatter(3400 if not PREVIEW else 500, lambda x, z: (rd(x, z) > HALF + 0.2) & wet(x, z) &
                  ((np.abs(sample(blk["lake"], x, z) - 0.05) < 0.4) | (sample(PATCH, x, z) > 0.6)))
    merged("Rushes", tuft_template(10, 0.3, 0.009), place_list(pts, 0.7, 1.3), rush)
    cotton = simple_mat("Cotton", (0.96, 0.95, 0.9), 0.6)
    centres = scatter(160 if not PREVIEW else 40, lambda x, z: (rd(x, z) > HALF + 0.3) & no_blk(x, z) & wet(x, z))
    pts = []
    for cx, cz in centres:
        for _ in range(int(RNG.integers(4, 10))):
            pts.append((cx + RNG.normal(0, 0.15), cz + RNG.normal(0, 0.15)))
    merged("Cotton", blob_template(1), [((x, y, h + 0.14 * s / 0.03), yw, s, None) for ((x, y, h), yw, s, t) in place_list(pts, 0.02, 0.032)], cotton)
    moss = simple_mat("Moss", (0.34, 0.44, 0.14), 0.9, var=(0.5, 0.26, 0.14))
    pts = scatter(900 if not PREVIEW else 150, lambda x, z: (rd(x, z) > HALF + 0.15) & no_blk(x, z) & wet(x, z))
    merged("MossLumps", blob_template(2), [(p, y, s, None) for (p, y, s, t) in place_list(pts, 0.05, 0.12, sink=0.7)], moss)
elif THEME in ("olive", "coast", "acropolis"):
    dry_w = lambda x, z: (sample(water_all, x, z) < 0.05) & (sample(bank, x, z) < 0.4)
    gold = blade_mat("DryGrass", (0.42, 0.38, 0.18), (0.62, 0.55, 0.28), (0.86, 0.78, 0.5))
    n_dry = {"olive": 15000, "coast": 9000, "acropolis": 6000}[THEME]
    acc = (lambda x, z: (rd(x, z) > HALF + 0.1) & no_blk(x, z) & dry_w(x, z)) if THEME != "acropolis" else \
        (lambda x, z: (rd(x, z) > HALF + 0.1) & no_blk(x, z) & (sample(PATCH, x, z) > 0.45))
    pts = scatter(n_dry if not PREVIEW else 2000, acc)
    merged("Tufts", tuft_template(9, 0.12, 0.013), place_list(pts, 0.75, 1.45), gold)
    green = blade_mat("GreenGrass", (0.24, 0.36, 0.12), (0.38, 0.5, 0.18), (0.6, 0.68, 0.3))
    pts = scatter(3000 if not PREVIEW else 400, lambda x, z: (rd(x, z) > HALF + 0.3) & no_blk(x, z) & dry_w(x, z) & (sample(PATCH, x, z) < 0.4))
    merged("GreenTufts", tuft_template(9, 0.1, 0.013), place_list(pts, 0.75, 1.3), green)
    # thyme, sage and lentisk cushions; the coast's maquis and the hill's scrub as bigger rounded bushes
    herb = simple_mat("Herb", (0.38, 0.44, 0.3), 0.85, var=(0.5, 0.42, 0.52))
    pts = scatter(1400 if not PREVIEW else 200, lambda x, z: (rd(x, z) > HALF + 0.35) & no_blk(x, z) & dry_w(x, z))
    merged("Herbs", blob_template(1), [(p, y, s, None) for (p, y, s, t) in place_list(pts, 0.035, 0.07, sink=0.45)], herb)
    if THEME in ("coast", "acropolis"):
        bush = simple_mat("Maquis", (0.18, 0.28, 0.12), 0.85, var=(0.3, 0.38, 0.16))
        pts = scatter((700 if THEME == "coast" else 300) if not PREVIEW else 100,
                      lambda x, z: (rd(x, z) > HALF + 0.6) & no_blk(x, z) & dry_w(x, z))
        merged("Maquis", blob_template(2), [(p, y, s, None) for (p, y, s, t) in place_list(pts, 0.08, 0.16, sink=0.4)], bush)
    flowers = {"olive": [(0.86, 0.12, 0.1), (1.0, 0.84, 0.22), (1.0, 1.0, 0.94)], "coast": [(1.0, 0.84, 0.22), (0.9, 0.5, 0.74), (1.0, 1.0, 0.94)],
               "acropolis": [(0.86, 0.12, 0.1), (1.0, 0.84, 0.22)]}[THEME]                   # poppies, broom, chamomile, sea pinks
    for k, col in enumerate(flowers):
        centres = scatter(55 if not PREVIEW else 15, lambda x, z: (rd(x, z) > HALF + 0.5) & inside_pf(x, z) & no_blk(x, z) & dry_w(x, z))
        pts = []
        for cx, cz in centres:
            for _ in range(int(RNG.integers(3, 8))):
                pts.append((cx + RNG.normal(0, 0.12), cz + RNG.normal(0, 0.12)))
        merged("Flowers%d" % k, flower_template(5, 0.038), place_list(pts, 0.8, 1.25), simple_mat("Petal%d" % k, col, 0.45))
    lime = simple_mat("Limestone", (0.72, 0.7, 0.64), 0.8, var=(0.86, 0.84, 0.78))
    if THEME != "acropolis":
        pts = scatter(2600 if not PREVIEW else 400, lambda x, z: (rd(x, z) < HALF + 0.15) & dry_w(x, z))
        merged("Pebbles", blob_template(1), place_list(pts, 0.014, 0.04, sink=0.35), lime)
    pts = scatter(150, lambda x, z: (np.abs(rd(x, z) - HALF - 0.35) < 0.35) & no_blk(x, z) & dry_w(x, z))
    merged("Stones", blob_template(2), place_list(pts, 0.05, 0.13, sink=0.45, tilt=0.2), lime)
    if THEME == "olive":
        pts = scatter(900 if not PREVIEW else 150, lambda x, z: (sample(slow, x, z) > 0.5))
        merged("Scree", blob_template(1), place_list(pts, 0.02, 0.06, sink=0.3, tilt=0.4), lime)                # the climbs' loose stones
    if THEME == "coast":
        sand = simple_mat("BeachStone", (0.7, 0.66, 0.58), 0.6, var=(0.86, 0.82, 0.74))
        pts = scatter(1100 if not PREVIEW else 200, lambda x, z: (sample(bank, x, z) > 0.4) & (rd(x, z) > HALF))
        merged("BeachStones", blob_template(1), place_list(pts, 0.015, 0.045, sink=0.4), sand)
        shell = simple_mat("Shell", (0.98, 0.94, 0.88), 0.5, var=(0.94, 0.78, 0.7))
        pts = scatter(500 if not PREVIEW else 100, lambda x, z: (sample(bank, x, z) > 0.3) & (rd(x, z) > HALF))
        merged("Shells", blob_template(1), [(p, y, s, None) for (p, y, s, t) in place_list(pts, 0.012, 0.022, sink=0.5)], shell)
    if THEME == "acropolis":
        marb = simple_mat("Rubble", (0.86, 0.84, 0.78), 0.6, var=(0.94, 0.92, 0.86))
        pts = scatter(500 if not PREVIEW else 100, lambda x, z: ((sample(blk["ruins"], x, z) < 0.6) | (sample(blk["statue"], x, z) < 0.5)) &
                      (rd(x, z) > HALF + 0.2))
        merged("Rubble", blob_template(1), place_list(pts, 0.03, 0.09, sink=0.3, tilt=0.5), marb)
        pts = scatter(1200 if not PREVIEW else 200, lambda x, z: (rd(x, z) > HALF + 0.1) & no_blk(x, z))
        merged("Chips", blob_template(1), place_list(pts, 0.012, 0.035, sink=0.3), lime)
else:
    cinder = simple_mat("Cinder", (0.16, 0.13, 0.12), 0.8, var=(0.3, 0.25, 0.22))
    pts = scatter(2600 if not PREVIEW else 500, lambda x, z: (rd(x, z) > HALF + 0.05) & no_blk(x, z))
    merged("Cinders", blob_template(1), place_list(pts, 0.015, 0.05, sink=0.3), cinder)
    peb = simple_mat("Pebble", (0.42, 0.38, 0.34), 0.75, var=(0.55, 0.5, 0.45))
    pts = scatter(1600 if not PREVIEW else 300, lambda x, z: rd(x, z) < HALF + 0.2)
    merged("Pebbles", blob_template(1), place_list(pts, 0.012, 0.03, sink=0.3), peb)
    ember = simple_mat("Ember", (0.3, 0.1, 0.05), 0.6, emit=(1.0, 0.4, 0.08), strength=3.0)
    pts = scatter(260 if not PREVIEW else 60, lambda x, z: (rd(x, z) > HALF + 0.3) & no_blk(x, z))
    merged("Embers", blob_template(1), place_list(pts, 0.012, 0.028, sink=0.2), ember)
    pts = scatter(110, lambda x, z: (np.abs(rd(x, z) - HALF - 0.4) < 0.4) & no_blk(x, z))
    merged("Basalt", blob_template(2), place_list(pts, 0.06, 0.16, sink=0.4, tilt=0.3), simple_mat("Basalt", (0.12, 0.11, 0.11), 0.6, var=(0.22, 0.19, 0.18)))
log("scatter done")

if arg("--crop"):        # test renders: x0,y0,x1,y1 as fractions of the frame (y from the bottom)
    c0 = [float(v) for v in arg("--crop").split(",")]
    sc.render.use_border = True
    sc.render.use_crop_to_border = True
    sc.render.border_min_x, sc.render.border_min_y, sc.render.border_max_x, sc.render.border_max_y = c0
    sc.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    log("crop ->", OUT)
    sys.exit(0)
sc.render.filepath = OUT + ".raw.png"
bpy.ops.render.render(write_still=True)
log("rendered")
from PIL import Image
im = np.asarray(Image.open(OUT + ".raw.png").convert("RGB")).astype(np.float32) / 255.0
# brightness: the game lights this plane again, so bring the playfield's mean to the old painted level
TARGET = {"meadow": 0.41, "snow": 0.84, "volcano": 0.27, "delta": 0.43, "desert": 0.6, "canyon": 0.4, "highland": 0.4, "forge": 0.26,
          "bog": 0.33, "olive": 0.5, "coast": 0.53, "acropolis": 0.56}[THEME]
mask_in = (sample(outside, X, Z) < 0.5)
mi = np.asarray(Image.fromarray((mask_in * 255).astype(np.uint8)).resize((im.shape[1], im.shape[0]))) > 127
cur = im[mi].mean()
im = np.clip(im * (TARGET / max(cur, 1e-3)) ** 0.8, 0, 1)
import ground_fade                       # the outer band blends to one colour: no seam against the far-ground plane
im = ground_fade.fade(im, 1.6 * PX)
Image.fromarray((im * 255 + 0.5).astype(np.uint8)).save(OUT)
os.remove(OUT + ".raw.png")
log("wrote", OUT, im.shape, "mean %.3f -> %.3f" % (cur, im[mi].mean()))
