"""HQ ground for the Stone Age to Gunpowder Age maps: the map's ground as a real 3D surface, rendered straight down into
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
paving round the ruins and the statues (acropolis); Medieval Age: a patchwork of fields (pasture, ripe wheat and barley
in rows, ploughed furrows, hay meadows) between hedgerows on low banks, a rutted cart track with muddy puddles, poppies on
its verges (farmland); a dark forest floor of leaf litter, moss and ferns, needle beds under the trees, toadstools, a
rooty track (darkwood); trampled siege ground, churned mud, scorched earth and craters, arrows stuck in the turf, spent
catapult stones, a cobbled road (castle); Gunpowder Age: a jungle floor of dark soil under fallen leaves, moss, ferns
and broad-leaved seedlings, roots snaking across it, red and orange flowers, rutted red-clay tracks puddled red-brown
where they dip, the fast lanes old causeways of mossy stones, worn paving round the ruins (jungle); a tropical cove of
pale sand and dunes, sea grass and scrub inland, wet sand, shells, driftwood and rope by a clear turquoise inlet, teal in
its middle, with sandy shallows and surf at its edges, packed-sand roads planked where they run down to the water, plank
floors under the smugglers' crates (harbor); the field before a besieged star fort: trampled grass and churned mud,
zigzag siege trenches with their spoil heaped on the fort's side, bomb craters (the crater blockers too) scorched round,
gun-carriage ruts across the turf, spent cannonballs half sunk in it, straw by the supply dumps, gravel military roads,
meadow round the edges (fortress). For highland, bog, coast and harbor, --watersrc PATH also writes the exact
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
                                         "statue", "building", "tents", "crates", "crater")}
BLOCKERS = []
for bl in m.get("blockers", []):
    bx, bz, br = bl[0], bl[1], bl[2]
    kind = bl[3] if len(bl) > 3 else {"snow": "lake", "volcano": "lava"}.get(THEME, "rocks")
    kind = kind if kind in blk else "rocks"
    w2 = (fbm(0.8, 2, int(bx * 7 + bz * 13) % 997) - 0.5) * 0.5
    d = np.hypot(X - bx, Z - bz) + w2 - br                    # < 0 inside
    blk[kind] = np.minimum(blk[kind], d)
    BLOCKERS.append((bx, bz, br, kind))
def smooth_line(pts, sub=8):
    """A Catmull-Rom spline through a polyline's points (the harbour's inlet: banks that curve, not kinks at each point;
    it passes through every point, so it keeps within a few centimetres of the simulation's no-build water)."""
    P = np.asarray(pts, np.float64)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, sub, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return np.array(out).tolist()


# rivers (delta): distance to each river's centre line, its half width there
riv = np.full(X.shape, 1e9)
for rv in m.get("rivers", []):
    rdd, _ra = g.poly_dist([smooth_line(rv["pts"]) if THEME == "harbor" else rv["pts"]], margin=6.0)
    riv = np.minimum(riv, rdd + (fbm(1.5, 3, 41) - 0.5) * 0.4 - float(rv["width"]) / 2)     # < 0 in the water
log("masks", g.w, g.h)


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
sys.path.append(os.path.join(HERE, "hq"))
import cycles_dev                       # (the GPU when the PC runner asks for it)
cycles_dev.use(sc)
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
       "bog": (0.64, 0.72, 0.78), "olive": (0.66, 0.76, 0.95), "coast": (0.64, 0.77, 0.96), "acropolis": (0.66, 0.76, 0.95),
       "farmland": (0.62, 0.74, 0.95), "darkwood": (0.46, 0.56, 0.52), "castle": (0.62, 0.7, 0.86),
       "jungle": (0.5, 0.62, 0.55), "harbor": (0.64, 0.78, 0.97), "fortress": (0.62, 0.7, 0.86)}[THEME]
wd.node_tree.nodes["Background"].inputs["Color"].default_value = SKY + (1,)
wd.node_tree.nodes["Background"].inputs["Strength"].default_value = {"meadow": 1.05, "snow": 1.0, "volcano": 0.8, "delta": 1.05,
                                                                    "desert": 1.0, "canyon": 0.95, "highland": 1.0, "forge": 0.82,
                                                                    "bog": 0.98, "olive": 1.05, "coast": 1.05, "acropolis": 1.05,
                                                                    "farmland": 1.05, "darkwood": 0.85, "castle": 1.0,
                                                                    "jungle": 0.92, "harbor": 1.05, "fortress": 1.0}[THEME]
# the game's sun: Godot rotation (-52, -36, 0) -> light travelling (0.362, -0.788, -0.498) in Godot = (x, y_b, z_b)
# (0.362, 0.498, -0.788) in Blender (y_b = -z_godot)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = {"meadow": 2.7, "snow": 2.6, "volcano": 2.3, "delta": 2.7, "desert": 2.8, "canyon": 2.6, "highland": 2.6, "forge": 2.3,
                   "bog": 2.5, "olive": 2.8, "coast": 2.75, "acropolis": 2.8, "farmland": 2.75, "darkwood": 2.2, "castle": 2.6,
                   "jungle": 2.45, "harbor": 2.8, "fortress": 2.6}[THEME]
sun.data.angle = math.radians(8)
sun.data.color = {"meadow": (1.0, 0.95, 0.86), "snow": (1.0, 0.98, 0.96), "volcano": (1.0, 0.75, 0.55), "delta": (1.0, 0.95, 0.86),
                  "desert": (1.0, 0.94, 0.82), "canyon": (1.0, 0.9, 0.78), "highland": (1.0, 0.95, 0.87), "forge": (1.0, 0.8, 0.62),
                  "bog": (0.98, 0.96, 0.86), "olive": (1.0, 0.95, 0.84), "coast": (1.0, 0.96, 0.88), "acropolis": (1.0, 0.95, 0.85),
                  "farmland": (1.0, 0.95, 0.86), "darkwood": (0.92, 0.96, 0.82), "castle": (1.0, 0.93, 0.84),
                  "jungle": (1.0, 0.95, 0.8), "harbor": (1.0, 0.96, 0.88), "fortress": (1.0, 0.93, 0.83)}[THEME]
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


# ------------------------------------------------------------------------------------------------ Medieval fields, craters
# farmland: a patchwork of fields (Voronoi cells round seeds on a jittered grid, their borders warped), each sown with
# one crop (0 pasture, 1 wheat, 2 ploughed, 3 hay meadow, 4 barley), its rows / furrows running one way; hedgerows on low
# banks along the borders (never across the road: the track runs through gaps)
fld_wheat = fld_plough = fld_hay = fld_barley = fld_stripe = hedge = np.zeros(X.shape)
crater = np.zeros(X.shape)
crater_rim = np.zeros(X.shape)
if THEME == "farmland":
    fr = np.random.default_rng(29)
    seeds = []
    for gx in np.arange(G.X0 + 2.6, G.X0 + G.W, 6.6):
        for gz in np.arange(G.Z0 + 2.4, G.Z0 + G.H, 6.0):
            seeds.append((gx + fr.uniform(-2.2, 2.2), gz + fr.uniform(-2.0, 2.0)))
    seeds = np.array(seeds, np.float32)
    ftype = fr.choice([0, 1, 2, 3, 4], size=len(seeds), p=[0.28, 0.24, 0.2, 0.16, 0.12])
    for want in (2, 3, 4):                                             # (at least two fields of every crop)
        while (ftype == want).sum() < 2:
            ftype[fr.choice(np.flatnonzero(ftype == np.bincount(ftype, minlength=5).argmax()))] = want
    fang = fr.choice([0.0, math.pi / 2], size=len(seeds)) + fr.uniform(-0.28, 0.28, len(seeds))
    wx = (X + (fbm(1.6, 2, 141) - 0.5) * 1.0).astype(np.float32)
    wz = (Z + (fbm(1.6, 2, 142) - 0.5) * 1.0).astype(np.float32)
    dd = (wx[..., None] - seeds[:, 0]) ** 2 + (wz[..., None] - seeds[:, 1]) ** 2
    idx = np.argmin(dd, -1)
    part = np.sqrt(np.partition(dd, 1, -1)[..., :2])
    del dd
    border = (part[..., 1] - part[..., 0]) * 0.5                       # ~ distance to the field's edge
    ty = ftype[idx]
    ang = fang[idx]
    fld_stripe = 0.5 + 0.5 * np.sin((X * np.cos(ang) + Z * np.sin(ang)) * (2 * math.pi / 0.34))
    soft = np.clip((border - 0.12) / 0.2, 0, 1)                        # crops thin out at the field's edge
    fld_wheat = (ty == 1) * soft
    fld_plough = (ty == 2) * soft
    fld_hay = (ty == 3) * 1.0
    fld_barley = (ty == 4) * soft
    hedge = np.exp(-(border / 0.16) ** 2) * np.clip((dist - HALF - 0.35) / 0.25, 0, 1)
    for k in ("rocks", "trees", "building"):                           # (no hedge through a copse or a farmyard)
        hedge *= np.clip((blk[k] - 0.2) / 0.3, 0, 1)
    verge = np.clip((HALF + 0.75 - dist) / 0.3, 0, 1)                   # the track's grass verges: no crops
    for a_ in ("fld_wheat", "fld_plough", "fld_barley"):
        globals()[a_] = globals()[a_] * (1 - verge)
    log("fields", len(seeds), "by crop", np.bincount(ftype, minlength=5).tolist(), "plough px", int((fld_plough > 0.5).sum()))
if THEME == "castle":
    # the siege: craters where the defenders' stones fell, off the road
    cr = np.random.default_rng(37)
    n_cr = 0
    for _ in range(400):
        cx, cz = cr.uniform(G.X0 + 2, G.X0 + G.W - 2), cr.uniform(G.Z0 + 2, G.Z0 + G.H - 2)
        if n_cr >= 16:
            break
        r_ = cr.uniform(0.35, 0.7)
        d_ = np.hypot(X - cx, Z - cz)
        if dist[min(g.h - 1, max(0, int((cz - G.Z0) * MPX))), min(g.w - 1, max(0, int((cx - G.X0) * MPX)))] < HALF + r_ + 0.3:
            continue
        crater = np.maximum(crater, np.clip(1 - (d_ / r_) ** 2, 0, 1))
        crater_rim = np.maximum(crater_rim, np.exp(-((d_ - r_) / (0.25 * r_)) ** 2))
        n_cr += 1


# ------------------------------------------------------------------------------------------------ Gunpowder Age features
# mask8/mask9 carry each Gunpowder theme's own features:
#   jungle:   paving round the ruins, puddles in the tracks
#   harbor:   wet sand, plank decks, the inlet's depth, surf; the beach, the dunes' plant cover, distance along the road
#             (the planks' joints, drawn at full resolution in the material), the decks' edge beams
#   fortress: trenches, their spoil heaps, wheel ruts across the field, scorch round the craters
gp_a = gp_b = gp_c = gp_d = gp_e = gp_f = gp_g = gp_h = np.zeros(X.shape)
ROOTS = []                                    # jungle: (points (x, z), radius, a free root (True) or a tree's (False))
BLK_ANY = np.minimum.reduce(list(blk.values()))


def _at(arr, x, z):
    """Nearest lookup of a mask at one world point."""
    return arr[min(g.h - 1, max(0, int((z - G.Z0) * MPX))), min(g.w - 1, max(0, int((x - G.X0) * MPX)))]


def _in_tex(x, z, pad=1.0):
    return G.X0 + pad < x < G.X0 + G.W - pad and G.Z0 + pad < z < G.Z0 + G.H - pad


if THEME == "jungle":
    # worn paving round the ruins (the pyramid's foot): flagstones out past the blocker, broken off ragged at their edge
    gp_a = np.clip((0.62 + (fbm(0.45, 3, 181) - 0.5) * 0.8 - blk["ruins"]) / 0.08, 0, 1) * np.clip((dist - HALF - 0.12) / 0.12, 0, 1)
    # puddles where the tracks dip: hollows right across the road, and the ruts hold water a little more often
    dip = fbm(1.3, 3, 182) + (fbm(0.3, 2, 183) - 0.5) * 0.06
    inner = np.clip((HALF - 0.1 - dist) / 0.12, 0, 1) * (1 - lane)
    gp_b = np.clip(np.maximum((0.335 - dip) / 0.035, rut * (0.375 - dip) / 0.03), 0, 1) * inner
    # roots snaking across the floor: from each stand of trees, and from trees in the undergrowth; they stop at a road
    jr = np.random.default_rng(43)

    def _root(x, z, ang, length, r0, free):
        pts, turn = [(x, z)], 0.0
        for _ in range(int(length / 0.07)):
            turn = turn * 0.82 + jr.normal(0, 0.14)
            ang += turn * 0.3
            x, z = x + math.cos(ang) * 0.07, z + math.sin(ang) * 0.07
            if not _in_tex(x, z) or _at(dist, x, z) < HALF + 0.1:
                break
            pts.append((x, z))
        if len(pts) > 5:
            ROOTS.append((pts, r0, free))
        return pts

    for (bx, bz, br, kind) in BLOCKERS:
        if kind != "trees":
            continue
        n_r = int(jr.integers(7, 11))
        for k in range(n_r):
            a = 2 * math.pi * k / n_r + jr.uniform(-0.25, 0.25)
            pts = _root(bx + math.cos(a) * br * 0.35, bz + math.sin(a) * br * 0.35, a + jr.uniform(-0.3, 0.3),
                        jr.uniform(1.6, 3.4), jr.uniform(0.045, 0.065), False)
            if len(pts) > 14 and jr.random() < 0.7:
                i0 = int(len(pts) * jr.uniform(0.3, 0.6))
                _root(pts[i0][0], pts[i0][1], a + jr.choice([-1.0, 1.0]) * jr.uniform(0.5, 0.9), jr.uniform(0.7, 1.8), 0.03, False)
    n_free = 0
    for _ in range(3000):
        if n_free >= 64:
            break
        x, z = jr.uniform(G.X0 + 1.5, G.X0 + G.W - 1.5), jr.uniform(G.Z0 + 1.5, G.Z0 + G.H - 1.5)
        if _at(dist, x, z) < HALF + 0.7 or _at(BLK_ANY, x, z) < 0.2:
            continue
        a = jr.uniform(0, 2 * math.pi)
        pts = _root(x, z, a, jr.uniform(1.2, 3.2), jr.uniform(0.03, 0.046), True)
        if len(pts) > 16 and jr.random() < 0.5:
            i0 = int(len(pts) * jr.uniform(0.3, 0.7))
            _root(pts[i0][0], pts[i0][1], a + jr.choice([-1.0, 1.0]) * jr.uniform(0.5, 1.0), jr.uniform(0.6, 1.5), 0.024, True)
        n_free += 1
    log("jungle: roots", len(ROOTS), "paving px", int((gp_a > 0.5).sum()), "puddle px", int((gp_b > 0.5).sum()))
if THEME == "harbor":
    # the cove: wet sand along the waterline, the inlet's depth (sandy shallows to deep teal), surf at its edges, plank
    # decks where the roads run down to the water and over it, and plank floors under the smugglers' stacks of crates
    gp_a = np.clip(1 - riv / 0.4, 0, 1) * np.clip(riv / 0.03 + 1, 0, 1)                            # wet sand
    surf = np.exp(-((riv + 0.08 + (fbm(0.35, 2, 191) - 0.5) * 0.07) / 0.035) ** 2) * np.clip((fbm(0.22, 3, 192) - 0.32) / 0.22, 0, 1)
    surf2 = np.exp(-((riv + 0.32 + (fbm(0.5, 2, 194) - 0.5) * 0.16) / 0.03) ** 2) * np.clip((fbm(0.3, 3, 195) - 0.5) / 0.2, 0, 1)
    gp_d = np.maximum(surf, surf2 * 0.55)                                                          # surf, a fainter line beyond
    gp_c = np.clip(-riv / 0.95, 0, 1)                                                              # depth
    deck = np.clip((HALF - 0.06 - dist) / 0.03, 0, 1) * np.clip((1.3 - riv) / 0.04, 0, 1)            # boardwalks: straight-edged
    # (a floor of planks 0.2 wide running along x, each its own length and a little offset, now and then one missing; the
    # joints fall on multiples of 0.2 in z, where the material draws them)
    pads = np.zeros(X.shape)
    jz = np.floor(Z / 0.2)
    for (bx, bz, br, kind) in BLOCKERS:
        if kind != "crates":
            continue
        hsh = lambda k: np.abs(np.sin(jz * 12.9898 + bx * 78.233 + bz * 37.719 + k * 7.31) * 43758.5453) % 1.0
        hl = br * (0.78 + 0.32 * hsh(1))
        cxp = bx + (hsh(2) - 0.5) * 0.24
        on = (np.abs(Z - bz) < br * 0.82) & (np.abs(X - cxp) < hl) & (hsh(3) > 0.07)
        pads = np.maximum(pads, on.astype(np.float64))
    gp_b = np.maximum(deck, pads)
    gp_e = np.clip((1.7 + (fbm(0.9, 3, 197) - 0.5) * 1.3 - riv) / 0.5, 0, 1) * (riv > -0.05)        # the bare beach
    gp_f = np.clip((riv - 1.4) / 3.5, 0, 1) * np.clip((fbm(1.1, 4, 198) - 0.45) / 0.18, 0, 1)        # plant cover over the dunes
    gp_f = np.maximum(gp_f, outside * 0.75) * (1 - gp_e)
    gp_g = along                                                                                   # (the planks' joints)
    gp_h = np.exp(-((dist - (HALF - 0.12)) / 0.035) ** 2) * deck                                   # the decks' edge beams
    log("harbor: deck px", int((deck > 0.5).sum()), "pads px", int((pads > 0.5).sum()), "water px", int((riv < 0).sum()))
if THEME == "fortress":
    fr2 = np.random.default_rng(47)
    bnd = m["bounds"]

    def _blast(cx, cz, r_, d_):
        """Scorch round a crater: black inside, burnt out past its rim in a ragged star of blast rays."""
        ang = np.arctan2(Z - cz, X - cx)
        ph0 = fr2.uniform(0, 2 * math.pi)
        rays = 0.5 + 0.5 * np.sin(ang * int(fr2.integers(7, 12)) + ph0 + np.sin(ang * 3 + ph0) * 0.9)
        reach = r_ * (1.35 + 0.75 * rays ** 2)
        return np.clip((reach - d_) / (reach - r_ * 0.75), 0, 1) ** 0.8

    # bomb craters: the crater blockers, deep with raised rims, and smaller ones scattered over the field, off the road
    for (bx, bz, br, kind) in BLOCKERS:
        if kind != "crater":
            continue
        r_ = br * 0.86
        d_ = np.hypot(X - bx, Z - bz) + (fbm(0.6, 2, int(abs(bx * 7 + bz * 13)) % 997 + 500) - 0.5) * 0.25
        crater = np.maximum(crater, np.clip(1 - (d_ / r_) ** 2, 0, 1))
        crater_rim = np.maximum(crater_rim, np.exp(-((d_ - r_ * 1.02) / (0.22 * r_)) ** 2))
        gp_d = np.maximum(gp_d, _blast(bx, bz, r_, d_))
    n_cr = 0
    for _ in range(600):
        if n_cr >= 14:
            break
        cx, cz = fr2.uniform(bnd[0] + 0.8, bnd[2] - 0.8), fr2.uniform(bnd[1] + 0.8, bnd[3] - 0.8)
        r_ = fr2.uniform(0.32, 0.62)
        if _at(dist, cx, cz) < HALF + r_ + 0.35 or _at(BLK_ANY, cx, cz) < r_ + 0.5 or _at(crater, cx, cz) > 0.0:
            continue
        d_ = np.hypot(X - cx, Z - cz)
        crater = np.maximum(crater, np.clip(1 - (d_ / r_) ** 2, 0, 1))
        crater_rim = np.maximum(crater_rim, np.exp(-((d_ - r_) / (0.25 * r_)) ** 2))
        gp_d = np.maximum(gp_d, _blast(cx, cz, r_, d_) * 0.85)
        n_cr += 1
    # siege trenches: zigzag parallels through the open field, facing the fort (it is at the road's end, +x), the spoil
    # thrown up on that side; each sends a zigzag sap on toward the fort; all keep clear of roads, blockers and craters
    near_cr = np.maximum(crater, crater_rim)

    def _clear(x, z, road_m=0.85, blk_m=0.45):
        return (bnd[0] + 0.3 < x < bnd[2] - 0.3 and bnd[1] + 0.3 < z < bnd[3] - 0.3 and _at(dist, x, z) > HALF + road_m
                and _at(BLK_ANY, x, z) > blk_m and _at(near_cr, x, z) < 0.05)

    AMP, LEG = 0.42, 1.5
    zz = lambda z: AMP * (1 - 4 * abs(((z / (2 * LEG)) % 1) - 0.5))           # the zigzag's offset at depth z
    runs = []
    for x0 in np.arange(bnd[0] + 1.6, bnd[2] - 1.2, 0.25):
        zq = np.arange(bnd[1] + 0.5, bnd[3] - 0.5, 0.1)
        ok = np.array([_clear(x0 + zz(z), z) for z in zq])
        k = 0
        while k < len(zq):
            if not ok[k]:
                k += 1
                continue
            j = k
            while j + 1 < len(zq) and ok[j + 1]:
                j += 1
            if zq[j] - zq[k] >= 3.2:
                runs.append((zq[j] - zq[k], x0, zq[k] + 0.25, zq[j] - 0.25))
            k = j + 1
    runs.sort(key=lambda r: -r[0])
    chosen = []
    for L_, x0, z0, z1 in runs:
        if len(chosen) >= 4:
            break
        if any(abs(x0 - c_[1]) < 4.5 and min(z1, c_[3]) > max(z0, c_[2]) - 1.0 for c_ in chosen):
            continue
        chosen.append((L_, x0, z0, z1))
    par, saps = [], []
    for L_, x0, z0, z1 in chosen:
        zv = [z0] + [k_ * LEG for k_ in range(int(math.ceil(z0 / LEG)), int(math.floor(z1 / LEG)) + 1) if z0 < k_ * LEG < z1] + [z1]
        line = [(x0 + zz(z), z) for z in zv]
        par.append(line)
        sx, sz = line[len(line) // 2]
        sap = [(sx, sz)]
        for j in range(1, 6):
            q = (sx + j * 0.9, sz + (0.32 if j % 2 else -0.32))
            if not _clear(q[0], q[1], 0.75, 0.4):
                break
            sap.append(q)
        if len(sap) >= 3:
            saps.append(sap)
    td = np.full(X.shape, 1e9)
    if par:
        td, _tal, tsd = g.poly_dist(par, margin=1.2, signed=True)
        # (a parallel runs toward +z, so its +x side has a negative signed distance)
        gp_b = np.exp(-((td - 0.4) / 0.16) ** 2) * np.clip(-tsd / 0.1, 0, 1) + 0.3 * np.exp(-((td - 0.3) / 0.1) ** 2) * np.clip(tsd / 0.1, 0, 1)
    if saps:
        sd2, _sal = g.poly_dist(saps, margin=1.2)
        gp_b = np.maximum(gp_b, 0.55 * np.exp(-((sd2 - 0.34) / 0.12) ** 2) * np.clip((sd2 - 0.1) / 0.1, 0, 1))
        td = np.minimum(td, sd2)
    gp_a = np.clip((0.16 - td) / 0.05, 0, 1)
    gp_b = gp_b * (1 - gp_a)
    # wheel ruts across the field, where the besiegers dragged their guns: pairs of grooves along wandering curves
    tracks = []
    for _ in range(400):
        if len(tracks) >= 12:
            break
        x, z = fr2.uniform(bnd[0] + 0.5, bnd[2] - 0.5), fr2.uniform(bnd[1] + 0.5, bnd[3] - 0.5)
        if not _clear(x, z, 0.5, 0.3) or _at(td, x, z) < 0.7:
            continue
        a, bend = fr2.uniform(0, 2 * math.pi), fr2.uniform(-0.1, 0.1)
        pts = [(x, z)]
        for _s in range(int(fr2.uniform(45, 100))):
            a += bend * 0.1 + fr2.normal(0, 0.012)
            x, z = x + math.cos(a) * 0.1, z + math.sin(a) * 0.1
            if not _clear(x, z, 0.45, 0.3) or _at(td, x, z) < 0.6:
                break
            pts.append((x, z))
        if len(pts) < 36:
            continue
        P = np.array(pts)
        T = np.gradient(P, axis=0)
        T /= np.linalg.norm(T, axis=1, keepdims=True)
        Nn = np.stack([-T[:, 1], T[:, 0]], 1)
        tracks += [(P + Nn * 0.21).tolist(), (P - Nn * 0.21).tolist()]
    if tracks:
        wd_, _wa = g.poly_dist(tracks, margin=0.4)
        gp_c = np.exp(-(wd_ / 0.045) ** 2) * np.clip((dist - HALF - 0.1) / 0.2, 0, 1)
    log("fortress: craters", n_cr, "+ blockers; parallels", len(par), [(round(c_[1], 2), round(c_[2], 1), round(c_[3], 1)) for c_ in chosen],
        "saps", len(saps), "rut lines", len(tracks))
if arg("--watersrc") and THEME in ("highland", "bog", "coast", "harbor"):
    from PIL import Image as _Im
    _w = np.maximum(np.clip(-riv / 0.12, 0, 1), np.clip(-blk["lake"] / 0.15, 0, 1))
    if THEME == "harbor":
        _w = _w * (1 - gp_b)                  # (not under the plank decks: the planks don't ripple)
    _Im.fromarray((np.clip(_w, 0, 1) * 255).astype(np.uint8)).save(arg("--watersrc"))
    log("water source ->", arg("--watersrc"))


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
if THEME == "farmland":
    hf += (fbm(2.0, 4, 151) - 0.5) * 0.07 * (1 - road)                                             # gently rolling
    hf += fld_plough * (fld_stripe - 0.5) * 0.014 * (1 - road)                                       # ridge and furrow
    hf += hedge * 0.03                                                                              # the hedgerows' banks
    hf -= slow * (0.015 + (fbm(0.3, 2, 152) - 0.5) * 0.02)                                          # the muddy hollow
if THEME == "darkwood":
    hf += (fbm(1.3, 4, 161) - 0.5) * 0.08 * (1 - road) + (fbm(0.35, 2, 162) - 0.5) * 0.02 * (1 - road)   # hummocks, hollows
    hf += np.clip(-blk["trees"] / 1.2, 0, 1) * 0.04                                                 # roots heaved up round the trunks
if THEME == "castle":
    hf += (fbm(1.0, 4, 171) - 0.5) * 0.05 * (1 - road) + (fbm(0.25, 2, 172) - 0.5) * 0.02 * (1 - road)   # churned
    hf -= crater * 0.06
    hf += crater_rim * 0.02
    hf -= slow * 0.02
if THEME == "jungle":
    hf += (fbm(1.3, 4, 201) - 0.5) * 0.08 * (1 - road) + (fbm(0.35, 2, 202) - 0.5) * 0.025 * (1 - road)   # hummocks, hollows
    hf += np.clip(-blk["trees"] / 1.2, 0, 1) * 0.05                                                 # the trees' root plates
    hf += gp_a * 0.012                                                                              # the paving, proud of the soil
    hf += lane * (0.035 + rut * 0.008)                                                              # the causeway rides on the clay
    hf -= gp_b * 0.012                                                                              # the puddles' hollows
if THEME == "harbor":
    hf += (fbm(2.2, 4, 211) - 0.5) * 0.12 * (1 - road) * np.clip((riv - 0.6) / 2.5, 0, 1)          # dunes, flattening to the beach
    hf += (fbm(0.5, 2, 212) - 0.5) * 0.015 * (1 - road)
    hf = np.where((riv < 0) & (gp_b < 0.5), -0.1, hf)                                             # the inlet (not under the decks)
    hf -= np.exp(-((riv - 0.2) / 0.45) ** 2) * 0.035 * (1 - road)                                   # the beach shelving down to it
    hf += gp_b * (0.05 + rut * 0.02)                                                                # the decks and floors on joists
if THEME == "fortress":
    hf += (fbm(1.0, 4, 221) - 0.5) * 0.05 * (1 - road) + (fbm(0.25, 2, 222) - 0.5) * 0.02 * (1 - road)   # churned
    hf -= crater * 0.14
    hf += crater_rim * 0.045
    hf -= gp_a * 0.1                                                                                # the trenches
    hf += gp_b * 0.07                                                                               # their spoil heaps
    hf -= gp_c * 0.014                                                                              # wheel ruts across the field
    hf -= rut * 0.012                                                                               # (deeper in the military roads)
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
if THEME == "harbor":
    water_all = river_core * (1 - gp_b)                                     # (right up to the plank deck, not to the road's sand)
zone_a = np.clip(-blk["palms"] / 0.4, 0, 1) + np.clip(-blk["ruins"] / 0.3, 0, 1) + np.clip(-blk["stones"] / 0.5, 0, 1) + \
    np.clip(-blk["statue"] / 0.3, 0, 1) + np.clip(-blk["building"] / 0.4, 0, 1) + np.clip(-blk["tents"] / 0.4, 0, 1) + \
    np.clip(-blk["crates"] / 0.4, 0, 1)
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
img6 = to_image("mask6", np.stack([fld_wheat, fld_plough, fld_stripe, hedge], 2))
img7 = to_image("mask7", np.stack([fld_hay, fld_barley, crater, crater_rim], 2))
img8 = to_image("mask8", np.stack([gp_a, gp_b, gp_c, gp_d], 2))
img9 = to_image("mask9", np.stack([gp_e, gp_f, gp_g, gp_h], 2))


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
wheat_m, plough_m, stripe_m, hedge_m = nb.tex(img6)
hay_m, barley_m, crater_m, rim_m = nb.tex(img7)
gpa_m, gpb_m, gpc_m, gpd_m = nb.tex(img8)
gpe_m, gpf_m, gpg_m, gph_m = nb.tex(img9)
big = nb.noise(0.35, 4, 0.6)
mid = nb.noise(1.6, 4, 0.6)
fine = nb.noise(14.0, 2, 0.5)
bump_h = None                            # (a theme's own relief for the bump: stones' joints, planks, gravel)
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
elif THEME == "farmland":
    # pasture, hay meadow, ripe wheat and barley in rows, ploughed ridge and furrow; hedgerow banks; a rutted cart track
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.28, 0.48, 0.15), (0.4, 0.6, 0.2))                       # pasture
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.36, 0.24), 0.5), c, (0.22, 0.42, 0.13))
    c = nb.mix(nb.math("MULTIPLY", fine, 0.22), c, (0.48, 0.66, 0.26))
    hay = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.46, 0.58, 0.24), (0.58, 0.66, 0.3))                       # hay meadow: lighter, seeding
    hay = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.6, 0.75), 0.5), hay, (0.7, 0.72, 0.42))
    c = nb.mix(hay_m, c, hay)
    rows = nb.ramp(stripe_m, 0.25, 0.75)
    wheat = nb.mix(nb.ramp(big, 0.3, 0.7), (0.78, 0.6, 0.26), (0.88, 0.72, 0.34))                    # ripe wheat in rows
    wheat = nb.mix(nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, rows), 0.6), wheat, (0.56, 0.42, 0.18))
    wheat = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.62, 0.76), 0.4), wheat, (0.95, 0.84, 0.5))
    c = nb.mix(wheat_m, c, wheat)
    barley = nb.mix(nb.ramp(big, 0.3, 0.7), (0.66, 0.66, 0.38), (0.76, 0.74, 0.46))                  # barley, paler
    barley = nb.mix(nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, rows), 0.5), barley, (0.5, 0.52, 0.28))
    c = nb.mix(barley_m, c, barley)
    soil = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.3, 0.21, 0.13), (0.4, 0.28, 0.17))                      # ploughed: ridge and furrow
    soil = nb.mix(nb.math("MULTIPLY", rows, 0.7), soil, (0.48, 0.35, 0.22))
    soil = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(30.0, 2, 0.5), 0.62, 0.72), 0.4), soil, (0.22, 0.15, 0.09))   # clods
    c = nb.mix(plough_m, c, soil)
    bankc = nb.mix(nb.ramp(fine, 0.3, 0.7), (0.17, 0.27, 0.09), (0.27, 0.34, 0.12))                  # under the hedges
    c = nb.mix(nb.math("MULTIPLY", hedge_m, 0.95), c, bankc)
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.16, 0.3, 0.1), (0.24, 0.38, 0.13)))
    c = nb.mix(nb.math("MULTIPLY", trees_m, 0.85), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.2, 0.22, 0.1), (0.3, 0.3, 0.14)))
    yard = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.44, 0.36, 0.24), (0.56, 0.46, 0.32))  # trodden farmyards
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.8), c, yard)
    track = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.47, 0.36, 0.23), (0.59, 0.47, 0.31))                   # the cart track
    track = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(30.0, "Distance"), 0.22, 0.1), 0.3), track, (0.38, 0.3, 0.21))
    track = nb.mix(nb.math("MULTIPLY", rut_m, 0.7), track, (0.34, 0.25, 0.16))
    grassmid = nb.math("MULTIPLY", nb.ramp(nb.noise(4.0, 2, 0.5), 0.45, 0.7), nb.math("SUBTRACT", 1.0, nb.ramp(rut_m, 0.05, 0.3)))
    track = nb.mix(nb.math("MULTIPLY", grassmid, 0.55), track, (0.36, 0.48, 0.18))                  # grass down its middle
    mud = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.24, 0.18, 0.12), (0.32, 0.24, 0.16))                      # the muddy hollow
    mud = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.6, 3, 0.6), 0.58, 0.66), 0.8), mud, (0.36, 0.42, 0.46))   # puddles: the sky
    track = nb.mix(slow_m, track, mud)
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.55), c, (0.3, 0.38, 0.14))
    c = nb.mix(road_m, c, track)
    rough = nb.mixf(nb.math("MULTIPLY", slow_m, nb.ramp(nb.noise(1.6, 3, 0.6), 0.58, 0.66)), 0.9, 0.15)
elif THEME == "darkwood":
    # a dark forest floor: leaf litter, moss, dark soil; needle beds under the trees; a rooty, muddy track
    litter = nb.voronoi(26.0, "Color")
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.13, 0.1, 0.06), (0.2, 0.15, 0.09))                      # dark loam
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(litter, 0.6, 0.78), 0.4), c, (0.32, 0.19, 0.08))          # russet leaves
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(litter, 0.2, 0.08), 0.3), c, (0.34, 0.28, 0.13))          # yellowed leaves
    moss = nb.ramp(nb.noise(1.2, 4, 0.6, distort=0.4), 0.46, 0.6)
    c = nb.mix(nb.math("MULTIPLY", moss, 0.9), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.08, 0.17, 0.05), (0.16, 0.28, 0.08)))   # moss
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.34, 0.22), 0.6), c, (0.1, 0.08, 0.05))             # dark damp soil
    c = nb.mix(nb.math("MULTIPLY", fine, 0.15), c, (0.36, 0.3, 0.18))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.06, 0.08, 0.04), (0.1, 0.12, 0.06)))
    needles = nb.mix(nb.ramp(fine, 0.3, 0.7), (0.22, 0.13, 0.07), (0.32, 0.19, 0.1))                 # needle beds under the trees
    c = nb.mix(nb.math("MULTIPLY", trees_m, 0.9), c, needles)
    flag = nb.ramp(nb.voronoi(3.2, "Distance", "DISTANCE_TO_EDGE"), 0.02, 0.06)
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.75), c, nb.mix(nb.math("SUBTRACT", 1.0, flag), (0.44, 0.44, 0.38), (0.24, 0.26, 0.2)))   # the chapel's old paving
    track = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.26, 0.19, 0.12), (0.36, 0.27, 0.17))                   # a dark, muddy track
    track = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(30.0, "Distance"), 0.22, 0.1), 0.3), track, (0.2, 0.15, 0.1))
    track = nb.mix(nb.math("MULTIPLY", rut_m, 0.6), track, (0.17, 0.12, 0.08))
    track = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.8, 3, 0.6), 0.62, 0.7), 0.7), track, (0.22, 0.26, 0.26))   # puddles
    track = nb.mix(nb.math("MULTIPLY", nb.ramp(litter, 0.82, 0.92), 0.6), track, (0.46, 0.28, 0.1))   # leaves blown onto it
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.6), c, (0.16, 0.13, 0.08))
    c = nb.mix(road_m, c, track)
    rough = 0.9
elif THEME == "castle":
    # trampled siege ground: worn grass, churned mud, scorched earth and craters; a cobbled road; mud where it dips
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.33, 0.35, 0.2), (0.43, 0.44, 0.27))                    # worn, muddied grass
    churn = nb.ramp(nb.noise(1.1, 4, 0.6, distort=0.5), 0.5, 0.64)
    c = nb.mix(nb.math("MULTIPLY", churn, 0.85), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.26, 0.2, 0.13), (0.36, 0.28, 0.18)))   # mud
    scorch = nb.ramp(nb.noise(0.8, 3, 0.6), 0.64, 0.74)
    c = nb.mix(nb.math("MULTIPLY", scorch, 0.85), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.08, 0.07, 0.06), (0.2, 0.18, 0.16)))   # scorched
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.6, 0.72), 0.4), c, (0.5, 0.46, 0.3))                 # straw-coloured trampled grass
    c = nb.mix(nb.math("MULTIPLY", fine, 0.2), c, (0.42, 0.42, 0.26))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.2, 0.32, 0.11), (0.28, 0.4, 0.14)))       # unspoilt meadow round it
    crat = nb.mix(nb.ramp(fine, 0.3, 0.7), (0.18, 0.14, 0.1), (0.28, 0.22, 0.15))
    c = nb.mix(crater_m, c, crat)
    c = nb.mix(nb.math("MULTIPLY", rim_m, 0.7), c, (0.3, 0.24, 0.16))
    camp = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.4, 0.33, 0.22), (0.52, 0.44, 0.3))    # trodden ground in the camp
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.8), c, camp)
    cob = nb.ramp(nb.voronoi(7.5, "Distance", "DISTANCE_TO_EDGE"), 0.02, 0.07)
    stone = nb.mix(nb.ramp(nb.noise(6.0, 3, 0.6), 0.3, 0.7), (0.46, 0.45, 0.42), (0.6, 0.58, 0.54))   # the cobbled road
    stone = nb.mix(nb.math("SUBTRACT", 1.0, cob), stone, (0.26, 0.23, 0.19))
    stone = nb.mix(nb.math("MULTIPLY", rut_m, 0.4), stone, (0.36, 0.33, 0.3))
    mud = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.22, 0.17, 0.11), (0.3, 0.23, 0.15))                       # where the road dips: mud
    mud = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.6, 3, 0.6), 0.58, 0.66), 0.8), mud, (0.34, 0.38, 0.42))
    stone = nb.mix(slow_m, stone, mud)
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.55), c, (0.28, 0.24, 0.16))
    c = nb.mix(road_m, c, stone)
    rough = nb.mixf(nb.math("MULTIPLY", slow_m, nb.ramp(nb.noise(1.6, 3, 0.6), 0.58, 0.66)), 0.88, 0.15)
elif THEME == "jungle":
    # a dense jungle floor: rich dark soil under a carpet of fallen leaves, moss; red-clay tracks puddled red-brown where
    # they dip; the fast lanes old causeways of mossy stones; worn paving round the ruins
    litter = nb.voronoi(22.0, "Color")
    litter2 = nb.voronoi(9.0, "Color")
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.1, 0.07, 0.045), (0.16, 0.11, 0.065))                       # dark loam
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(litter, 0.5, 0.72), 0.6), c, (0.19, 0.27, 0.07))             # green leaves
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(litter, 0.3, 0.12), 0.55), c, (0.4, 0.3, 0.1))              # yellow-brown leaves
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(litter2, 0.66, 0.84), 0.5), c, (0.3, 0.16, 0.07))           # brown leaves
    moss = nb.ramp(nb.noise(1.1, 4, 0.6, distort=0.4), 0.5, 0.63)
    c = nb.mix(nb.math("MULTIPLY", moss, 0.85), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.12, 0.26, 0.05), (0.2, 0.38, 0.08)))   # moss
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.34, 0.22), 0.55), c, (0.08, 0.055, 0.035))           # dark damp soil
    c = nb.mix(nb.math("MULTIPLY", fine, 0.12), c, (0.3, 0.3, 0.12))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.05, 0.1, 0.035), (0.08, 0.15, 0.05)))       # the undergrowth beyond
    under = nb.mix(nb.ramp(fine, 0.3, 0.7), (0.13, 0.085, 0.045), (0.2, 0.13, 0.06))                    # rich litter under the trees
    c = nb.mix(nb.math("MULTIPLY", trees_m, 0.8), c, under)
    # the old paving round the ruins: big worn flags a shade apart, moss in their joints and creeping over them
    flag = nb.ramp(nb.voronoi(2.4, "Distance", "DISTANCE_TO_EDGE"), 0.015, 0.06)
    pv = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.42, 0.41, 0.34), (0.55, 0.53, 0.44))
    pv = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(2.4, "Color"), 0.6, 0.9), 0.35), pv, (0.36, 0.38, 0.3))
    pv = nb.mix(nb.math("SUBTRACT", 1.0, flag), pv, (0.12, 0.2, 0.05))
    pv = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.4, 3, 0.6), 0.56, 0.68), 0.75), pv, (0.18, 0.32, 0.08))
    c = nb.mix(nb.math("MULTIPLY", gpa_m, 0.95), c, pv)
    # the tracks: red clay, rutted, dry and crusted on top, wet in the ruts; red-brown puddles where they dip
    clay = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.46, 0.2, 0.1), (0.58, 0.28, 0.15))
    clay = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.55, 0.75), 0.35), clay, (0.66, 0.38, 0.22))
    clay = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(30.0, "Distance"), 0.22, 0.1), 0.25), clay, (0.36, 0.17, 0.09))
    clay = nb.mix(nb.math("MULTIPLY", rut_m, 0.75), clay, (0.32, 0.13, 0.07))
    clay = nb.mix(nb.math("MULTIPLY", nb.ramp(gpb_m, 0.0, 0.45), 0.8), clay, (0.3, 0.12, 0.06))         # wet clay round the puddles
    pud = nb.mix(nb.ramp(nb.noise(0.9, 3, 0.6), 0.3, 0.7), (0.3, 0.13, 0.07), (0.38, 0.18, 0.1))
    pud = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(0.5, 2, 0.5), 0.45, 0.75), 0.3), pud, (0.42, 0.3, 0.26))   # the sky in it
    clay = nb.mix(nb.ramp(gpb_m, 0.45, 0.65), clay, pud)
    # the causeway: old stones, warm and grey, moss in the joints and over them, worn smooth in the wheel tracks
    sj = nb.ramp(nb.voronoi(4.5, "Distance", "DISTANCE_TO_EDGE"), 0.015, 0.06)
    cs = nb.mix(nb.ramp(nb.noise(4.0, 3, 0.6), 0.3, 0.7), (0.38, 0.38, 0.32), (0.5, 0.49, 0.41))
    cs = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(4.5, "Color"), 0.55, 0.9), 0.4), cs, (0.46, 0.41, 0.32))
    cs = nb.mix(nb.math("SUBTRACT", 1.0, sj), cs, (0.1, 0.17, 0.05))
    cs = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.6, 3, 0.6, distort=0.4), 0.55, 0.68), 0.7), cs, (0.17, 0.3, 0.08))
    cs = nb.mix(nb.math("MULTIPLY", rut_m, 0.35), cs, (0.56, 0.53, 0.45))
    clay = nb.mix(lane_m, clay, cs)
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.6), c, (0.14, 0.08, 0.045))
    c = nb.mix(road_m, c, clay)
    rough = nb.mixf(nb.ramp(gpb_m, 0.45, 0.65), 0.9, 0.1)
    bump_h = nb.math("MULTIPLY", nb.math("ADD", nb.math("MULTIPLY", lane_m, sj), nb.math("MULTIPLY", gpa_m, flag)), 0.6)
elif THEME == "harbor":
    # a tropical cove: pale sand and dunes, sea grass and scrub inland, wet sand by the water; a clear turquoise inlet,
    # teal in its middle, sandy shallows and surf; packed-sand roads, planked where they run down to the water and over it
    rip = nb.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL")
    rip.inputs["Scale"].default_value = 3.4
    rip.inputs["Distortion"].default_value = 5.0
    rip.inputs["Detail"].default_value = 3.0
    nb.link(nb.uvn.outputs["Object"], rip.inputs["Vector"])
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.82, 0.73, 0.54), (0.9, 0.82, 0.63))                         # dune sand
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(rip.outputs["Fac"], 0.55, 0.85), 0.25), c, (0.76, 0.66, 0.47))   # wind ripples
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.6, 0.75), 0.3), c, (0.95, 0.9, 0.74))
    grass = nb.mix(nb.ramp(nb.noise(2.0, 3, 0.6), 0.3, 0.7), (0.5, 0.52, 0.27), (0.62, 0.62, 0.34))    # thin sea grass, the dunes
    grass = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.36, 0.24), 0.6), grass, (0.32, 0.42, 0.18))      # greener in the hollows
    c = nb.mix(nb.math("MULTIPLY", gpf_m, 0.8), c, grass)
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.38, 0.46, 0.22), (0.48, 0.54, 0.28)))       # greener inland, beyond
    beach = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.92, 0.86, 0.7), (0.98, 0.94, 0.8))      # the beach: pale, bare
    c = nb.mix(gpe_m, c, beach)
    wetc = nb.mix(nb.ramp(nb.noise(2.2, 3, 0.6), 0.3, 0.7), (0.66, 0.57, 0.41), (0.74, 0.65, 0.48))     # wet sand
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(gpa_m, 0.0, 0.5), 0.92), c, wetc)
    tide = nb.math("MULTIPLY", nb.ramp(gpa_m, 0.02, 0.1), nb.ramp(gpa_m, 0.22, 0.12))                  # the swash line
    c = nb.mix(nb.math("MULTIPLY", tide, 0.5), c, (0.6, 0.52, 0.38))
    camp = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.72, 0.62, 0.45), (0.8, 0.7, 0.52))      # trodden by the stashes
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.7), c, camp)
    track = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.74, 0.64, 0.47), (0.81, 0.71, 0.53))                     # the roads: packed sand
    track = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(30.0, "Distance"), 0.22, 0.1), 0.22), track, (0.64, 0.55, 0.4))
    track = nb.mix(nb.math("MULTIPLY", rut_m, 0.55), track, (0.64, 0.54, 0.38))
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.4), c, (0.8, 0.72, 0.55))
    c = nb.mix(road_m, c, track)
    # the inlet: sand under a film of water at its edge, turquoise shallows, teal in its middle; surf along its edges
    water = nb.mix(nb.ramp(gpc_m, 0.05, 0.55), (0.4, 0.8, 0.72), (0.12, 0.62, 0.63))
    water = nb.mix(nb.ramp(gpc_m, 0.5, 1.0), water, (0.03, 0.37, 0.45))
    water = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(0.8, 3, 0.6), 0.3, 0.7), 0.25), water, (0.06, 0.48, 0.52))
    bar = nb.math("MULTIPLY", nb.ramp(nb.noise(1.6, 3, 0.6), 0.55, 0.7), nb.ramp(gpc_m, 0.55, 0.15))   # sand bars showing through
    water = nb.mix(nb.math("MULTIPLY", bar, 0.5), water, (0.56, 0.82, 0.7))
    water = nb.mix(nb.math("MULTIPLY", nb.ramp(gpc_m, 0.16, 0.0), 0.75), water, (0.74, 0.8, 0.62))
    c = nb.mix(water_m, c, water)
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(gpd_m, 0.15, 0.7), 0.95), c, (0.95, 0.97, 0.96))           # surf
    # the plank decks (boards across the road) and the stashes' floors (boards along x): weathered boards, each its own
    # shade, dark joints (the water under a deck shows through them), the decks edged with beams
    ox = nb.n("ShaderNodeSeparateXYZ")
    nb.link(nb.uvn.outputs["Object"], ox.inputs["Vector"])

    def _boards(u, w):
        ph = nb.math("FRACT", nb.math("DIVIDE", u, w))
        wn = nb.n("ShaderNodeTexWhiteNoise", noise_dimensions="1D")
        nb.link(nb.math("FLOOR", nb.math("DIVIDE", u, w)), wn.inputs["W"])
        return nb.math("MULTIPLY", nb.ramp(ph, 0.0, 0.07), nb.ramp(ph, 1.0, 0.93)), wn.outputs["Value"]

    on_p, id_p = _boards(ox.outputs["Y"], 0.2)
    on_d, id_d = _boards(gpg_m, 0.24)
    onb = nb.mixf(road_m, on_p, on_d)
    wood = nb.mix(nb.mixf(road_m, id_p, id_d), (0.46, 0.37, 0.26), (0.62, 0.52, 0.38))
    wood = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(18.0, 3, 0.6), 0.3, 0.7), 0.35), wood, (0.4, 0.32, 0.22))
    wood = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(2.0, 3, 0.6), 0.6, 0.7), 0.4), wood, (0.62, 0.6, 0.54))   # bleached grey
    gapc = nb.mix(nb.ramp(gpc_m, 0.0, 0.15), (0.2, 0.15, 0.1), (0.03, 0.2, 0.22))
    wood = nb.mix(nb.math("SUBTRACT", 1.0, onb), wood, gapc)
    wood = nb.mix(gph_m, wood, (0.3, 0.22, 0.14))
    c = nb.mix(gpb_m, c, wood)
    rough = nb.mixf(nb.math("MULTIPLY", water_m, nb.math("SUBTRACT", 1.0, gpb_m)), 0.92, 0.1)
    bump_h = nb.math("MULTIPLY", gpb_m, nb.math("MULTIPLY", onb, 0.8))
elif THEME == "fortress":
    # the field before a besieged star fort: trampled grass and churned mud, trenches and their spoil heaps, bomb craters
    # scorched round, wheel ruts across the turf; gravel military roads; meadow round the edges
    c = nb.mix(nb.ramp(big, 0.35, 0.65), (0.33, 0.35, 0.19), (0.43, 0.44, 0.26))                        # trampled grass
    churn = nb.ramp(nb.noise(1.1, 4, 0.6, distort=0.5), 0.52, 0.66)
    c = nb.mix(nb.math("MULTIPLY", churn, 0.8), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.27, 0.2, 0.13), (0.37, 0.28, 0.18)))   # mud
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.6, 0.72), 0.4), c, (0.52, 0.47, 0.3))                 # beaten flat, straw-coloured
    c = nb.mix(nb.math("MULTIPLY", fine, 0.2), c, (0.44, 0.44, 0.27))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.21, 0.35, 0.12), (0.29, 0.43, 0.15)))       # meadow round it
    c = nb.mix(nb.math("MULTIPLY", gpc_m, 0.8), c, (0.25, 0.19, 0.12))                                  # wheel ruts
    spoil = nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.42, 0.31, 0.19), (0.52, 0.4, 0.25))    # fresh spoil
    spoil = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(30.0, 2, 0.5), 0.62, 0.72), 0.5), spoil, (0.3, 0.22, 0.14))   # clods
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(gpb_m, 0.05, 0.5), 0.92), c, spoil)
    ditch = nb.mix(nb.ramp(nb.noise(4.0, 3, 0.6), 0.3, 0.7), (0.17, 0.13, 0.09), (0.24, 0.18, 0.12))   # the trench floor
    c = nb.mix(gpa_m, c, ditch)
    crat = nb.mix(nb.ramp(fine, 0.3, 0.7), (0.15, 0.12, 0.09), (0.24, 0.18, 0.12))
    c = nb.mix(crater_m, c, crat)
    c = nb.mix(nb.math("MULTIPLY", rim_m, 0.6), c, (0.36, 0.28, 0.18))                                 # the thrown-up rim
    burnt = nb.mix(nb.ramp(nb.noise(6.0, 3, 0.6), 0.3, 0.7), (0.06, 0.055, 0.05), (0.17, 0.14, 0.11))  # scorched, sooty
    c = nb.mix(nb.math("MULTIPLY", gpd_m, 0.88), c, burnt)
    camp = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.4, 0.33, 0.22), (0.5, 0.42, 0.29))      # trodden by the dumps
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.8), c, camp)
    grav = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.5, 0.47, 0.41), (0.6, 0.57, 0.49))      # the gravel road
    peb = nb.voronoi(42.0, "Distance")
    grav = nb.mix(nb.math("MULTIPLY", nb.ramp(peb, 0.24, 0.1), 0.45), grav, (0.7, 0.67, 0.6))
    grav = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(17.0, "Distance"), 0.3, 0.12), 0.3), grav, (0.38, 0.35, 0.3))
    grav = nb.mix(nb.math("MULTIPLY", rut_m, 0.75), grav, (0.33, 0.27, 0.19))                           # muddy wheel ruts
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.55), c, (0.31, 0.28, 0.18))
    c = nb.mix(road_m, c, grav)
    rough = 0.9
    bump_h = nb.math("MULTIPLY", road_m, nb.math("MULTIPLY", nb.ramp(peb, 0.24, 0.1), 0.6))
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
bh = nb.math("ADD", fine, nb.math("MULTIPLY", nb.noise(40.0, 2, 0.5), 0.5))
nb.link(nb.math("ADD", bh, bump_h) if bump_h is not None else bh, bump.inputs["Height"])
nb.link(bump.outputs["Normal"], nb.b.inputs["Normal"])
me.materials.append(nb.m)


# ------------------------------------------------------------------------------------------------ scattered detail
def merged(name, template, xforms, mat):
    """One mesh of many transformed copies of a template (vertices Nx3, faces as index tuples)."""
    if not xforms:
        log("(no %s)" % name)
        return None
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


def simple_mat(name, col, rough=0.8, emit=None, strength=0.0, var=None, metal=0.0):
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    bb = mt.node_tree.nodes["Principled BSDF"]
    bb.inputs["Base Color"].default_value = lin(col)
    bb.inputs["Roughness"].default_value = rough
    bb.inputs["Metallic"].default_value = metal
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


def leaf_template(L=0.03, W=0.014):
    """A fallen leaf: a flat diamond, its tip curled up a little."""
    return [(0, -L, 0.004), (W, 0, 0.0), (0, L, 0.006), (-W, 0, 0.0), (0, 0, 0.002)], [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]


def arrow_template():
    """An arrow stuck in the turf at a slant: a thin shaft (two crossed strips) and three fletching vanes at its top."""
    V, F = [], []
    top = (0.12, 0.0, 0.34)
    for (px, py) in ((0.004, 0.0), (0.0, 0.004)):
        k = len(V)
        V += [(-px, -py, 0.0), (px, py, 0.0), (top[0] + px, top[1] + py, top[2]), (top[0] - px, top[1] - py, top[2])]
        F += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
    for j in range(3):
        a = 2 * math.pi * j / 3
        k = len(V)
        b = (top[0] * 0.78, top[1] * 0.78, top[2] * 0.78)
        V += [b, (b[0] + math.cos(a) * 0.016, b[1] + math.sin(a) * 0.016, b[2] + 0.01), top]
        F.append((k, k + 1, k + 2))
    return V, F


def frond_template(n=7, L=0.22, W=0.05, H=0.07, seg=5):
    """A fern: n arching fronds, each a rib with leaflets alternating down both sides (a saw-tooth outline from above)."""
    V, F = [], []
    for i in range(n):
        a = 2 * math.pi * i / n + RNG.uniform(-0.25, 0.25)
        ll = L * RNG.uniform(0.7, 1.1)
        ca, sa = math.cos(a), math.sin(a)
        rib = [(ca * ll * k / seg, sa * ll * k / seg, H * math.sin(math.pi * min(1.0, k / seg * 0.85)) + 0.004) for k in range(seg + 1)]
        for k in range(seg):
            w = W * (1 - (k + 0.5) / seg * 0.8) * (0.6 if k == 0 else 1.0)
            r0, r1 = rib[k], rib[k + 1]
            for s in (-1, 1):
                tip = ((r0[0] + r1[0]) / 2 - sa * w * s + ca * ll / seg * 0.4, (r0[1] + r1[1]) / 2 + ca * w * s + sa * ll / seg * 0.4,
                       (r0[2] + r1[2]) / 2 - 0.006)
                kk = len(V)
                V += [r0, r1, tip]
                F.append((kk, kk + 1, kk + 2) if s > 0 else (kk, kk + 2, kk + 1))
    return V, F


def seedling_template(n=4, L=0.07, W=0.03, H=0.045):
    """A broad-leaved seedling: a short stem and n broad pointed leaves spreading from its top, folded a little."""
    V, F = [(0.0, 0.0, 0.0), (0.004, 0.0, H), (-0.004, 0.0, H)], [(0, 1, 2)]
    for i in range(n):
        a = 2 * math.pi * i / n + RNG.uniform(-0.35, 0.35)
        ll = L * RNG.uniform(0.75, 1.15)
        ca, sa = math.cos(a), math.sin(a)
        k = len(V)
        V += [(0.0, 0.0, H), (ca * ll * 0.45 - sa * W, sa * ll * 0.45 + ca * W, H + 0.012), (ca * ll * 0.5, sa * ll * 0.5, H + 0.006),
              (ca * ll * 0.45 + sa * W, sa * ll * 0.45 - ca * W, H + 0.012), (ca * ll, sa * ll, H - 0.004)]
        F += [(k, k + 2, k + 1), (k, k + 3, k + 2), (k + 1, k + 2, k + 4), (k + 2, k + 3, k + 4)]
    return V, F


def tube_template(path, r, sides=5):
    """A tube of radius r along a path of (x, y) points lying on the ground (z = r): rope, a coil of it."""
    P = np.asarray(path, np.float64)
    T = np.gradient(P, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    V, F = [], []
    for (x, y), (tx, ty) in zip(P, T):
        for s in range(sides):
            b_ = 2 * math.pi * s / sides
            V.append((x - ty * math.cos(b_) * r, y + tx * math.cos(b_) * r, r + math.sin(b_) * r))
    for i in range(len(P) - 1):
        for s in range(sides):
            a0, a1 = i * sides + s, i * sides + (s + 1) % sides
            F.append((a0, a1, a1 + sides, a0 + sides))
    return V, F


def coil_template(R=0.06, r=0.011, turns=2.3):
    """A coil of rope dropped on the sand: a tube wound in a loose flat spiral."""
    n = int(turns * 16)
    return tube_template([(R * (0.5 + 0.5 * i / n) * math.cos(i / n * turns * 2 * math.pi),
                           R * (0.5 + 0.5 * i / n) * math.sin(i / n * turns * 2 * math.pi)) for i in range(n + 1)], r)


def rope_template(L=0.34, r=0.009):
    """A length of rope lying where it was dropped: a lazy S."""
    return tube_template([(L * (i / 16 - 0.5), 0.035 * math.sin(i / 16 * 2 * math.pi * 1.2)) for i in range(17)], r)


def stick_template(L=0.22, r=0.012):
    """A bit of driftwood: a thin, slightly bent rod, square in section, lying flat."""
    V, F = [], []
    for (x, y) in ((-L / 2, 0.0), (0.0, L * 0.07), (L / 2, -L * 0.02)):
        V += [(x, y - r, 0.0), (x, y + r, 0.0), (x, y + r, r * 1.5), (x, y - r, r * 1.5)]
    for s_ in (0, 4):
        for q in range(4):
            F.append((s_ + q, s_ + (q + 1) % 4, s_ + 4 + (q + 1) % 4, s_ + 4 + q))
    F += [(0, 3, 2, 1), (8, 9, 10, 11)]
    return V, F


def ball_template(sub=2):
    """A smooth ball (a cannonball): an icosphere without the blobs' lumps."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    V = [tuple(v.co) for v in bm.verts]
    F = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return V, F


def root_mesh(name, roots, mat, sides=6):
    """One mesh of roots lying on the ground along world polylines (x, z): a tree's root tapers from its start; a free
    root swells in its middle and dives under the soil at both ends. About half of each root shows above the ground."""
    if not roots:
        log("(no %s)" % name)
        return None
    V, F = [], []
    for pts, r0, free in roots:
        P = np.asarray(pts, np.float64)
        t = np.linspace(0, 1, len(P))
        if free:
            r = r0 * np.clip(np.sin(np.pi * t) * 1.5, 0.3, 1.0)
            vis = 0.15 + 0.45 * np.clip(np.sin(np.pi * t) * 2.0, 0, 1)
        else:
            r = r0 * (1 - 0.82 * t) ** 1.1 + 0.006
            vis = 0.62 - 0.4 * np.clip((t - 0.75) / 0.25, 0, 1)
        h = hgt(P[:, 0], P[:, 1])
        T = np.gradient(P, axis=0)
        T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
        base = len(V)
        for i in range(len(P)):
            cz = h[i] + r[i] * (2 * vis[i] - 1)
            for s in range(sides):
                b_ = 2 * math.pi * s / sides
                ox, oz = -T[i, 1] * math.cos(b_) * r[i], T[i, 0] * math.cos(b_) * r[i]
                V.append((P[i, 0] + ox, -(P[i, 1] + oz), cz + math.sin(b_) * r[i] * 0.85))
        for i in range(len(P) - 1):
            for s in range(sides):
                a0, a1 = base + i * sides + s, base + i * sides + (s + 1) % sides
                F.append((a0, a0 + sides, a1 + sides, a1))         # (outward: world z is Blender -y)
    me2 = bpy.data.meshes.new(name)
    me2.from_pydata(V, [], F)
    me2.update()
    for p in me2.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me2)
    sc.collection.objects.link(ob)
    me2.materials.append(mat)
    log(name, len(roots), "roots,", len(F), "quads")
    return ob


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
    pts = np.array(pts, np.float32).reshape(-1, 2)
    if len(pts) == 0:
        return []
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
elif THEME == "farmland":
    crop = lambda x, z: np.maximum.reduce([sample(fld_wheat, x, z), sample(fld_plough, x, z), sample(fld_barley, x, z)])
    nohedge = lambda x, z: sample(hedge, x, z) < 0.35
    blades = blade_mat("Blades", (0.24, 0.42, 0.12), (0.38, 0.58, 0.18), (0.62, 0.78, 0.32))
    pts = scatter(16000 if not PREVIEW else 2500, lambda x, z: (rd(x, z) > HALF + 0.1) & no_blk(x, z) & (crop(x, z) < 0.3) & nohedge(x, z))
    merged("Tufts", tuft_template(9, 0.12, 0.014), place_list(pts, 0.75, 1.45), blades)
    hayb = blade_mat("HayBlades", (0.32, 0.44, 0.14), (0.52, 0.6, 0.24), (0.8, 0.78, 0.44))
    pts = scatter(5000 if not PREVIEW else 800, lambda x, z: (sample(fld_hay, x, z) > 0.5) & (rd(x, z) > HALF + 0.4) & no_blk(x, z) & nohedge(x, z))
    merged("HayTufts", tuft_template(10, 0.19, 0.012), place_list(pts, 0.8, 1.3), hayb)
    ear = blade_mat("Wheat", (0.5, 0.36, 0.14), (0.78, 0.6, 0.26), (0.98, 0.86, 0.5))                 # wheat stalks along the rows
    pts = scatter(22000 if not PREVIEW else 3000, lambda x, z: (sample(fld_wheat, x, z) > 0.5) & (sample(fld_stripe, x, z) > 0.55) & no_blk(x, z))
    merged("Wheat", tuft_template(5, 0.17, 0.008), place_list(pts, 0.85, 1.2), ear)
    bar = blade_mat("Barley", (0.42, 0.42, 0.2), (0.62, 0.62, 0.32), (0.86, 0.84, 0.52))
    pts = scatter(9000 if not PREVIEW else 1500, lambda x, z: (sample(fld_barley, x, z) > 0.5) & (sample(fld_stripe, x, z) > 0.55) & no_blk(x, z))
    merged("Barley", tuft_template(6, 0.13, 0.008), place_list(pts, 0.85, 1.2), bar)
    clod = simple_mat("Clod", (0.3, 0.21, 0.13), 0.9, var=(0.42, 0.3, 0.19))
    pts = scatter(3500 if not PREVIEW else 500, lambda x, z: (sample(fld_plough, x, z) > 0.5) & (sample(fld_stripe, x, z) > 0.6))
    merged("Clods", blob_template(1), place_list(pts, 0.02, 0.05, sink=0.4), clod)
    hed = simple_mat("Hedge", (0.13, 0.26, 0.08), 0.85, var=(0.24, 0.38, 0.12))                       # hedgerows on their banks
    pts = scatter(5200 if not PREVIEW else 800, lambda x, z: (sample(hedge, x, z) > 0.55) & inside_pf(x, z) & no_blk(x, z))
    merged("Hedges", blob_template(2), [(p, y, s_, None) for (p, y, s_, t) in place_list(pts, 0.1, 0.19, sink=0.25)], hed)
    haw = simple_mat("Hawthorn", (0.96, 0.95, 0.9), 0.6, var=(0.98, 0.86, 0.9))
    pts = scatter(1600 if not PREVIEW else 300, lambda x, z: (sample(hedge, x, z) > 0.7) & inside_pf(x, z) & no_blk(x, z))
    merged("Blossom", blob_template(1), [((x, y, h + 0.17), yw, s_, None) for ((x, y, h), yw, s_, t) in place_list(pts, 0.02, 0.035)], haw)
    for k, (col, where) in enumerate([((0.86, 0.1, 0.08), "verge"), ((0.3, 0.42, 0.95), "verge"), ((1.0, 0.86, 0.2), "hay"),
                                       ((1.0, 1.0, 0.94), "hay"), ((0.86, 0.1, 0.08), "wheat")]):       # poppies, cornflowers, buttercups, daisies
        if where == "verge":
            acc = lambda x, z: (rd(x, z) > HALF + 0.25) & (rd(x, z) < HALF + 0.9) & no_blk(x, z) & nohedge(x, z)
        elif where == "hay":
            acc = lambda x, z: (sample(fld_hay, x, z) > 0.5) & (rd(x, z) > HALF + 0.4) & no_blk(x, z) & nohedge(x, z)
        else:
            acc = lambda x, z: (sample(fld_wheat, x, z) > 0.4) & (sample(fld_wheat, x, z) < 0.95) & no_blk(x, z)
        centres = scatter(60 if not PREVIEW else 15, acc)
        pts = []
        for cx, cz in centres:
            for _ in range(int(RNG.integers(3, 8))):
                pts.append((cx + RNG.normal(0, 0.12), cz + RNG.normal(0, 0.12)))
        merged("Flowers%d" % k, flower_template(5, 0.036), place_list(pts, 0.8, 1.25), simple_mat("Petal%d" % k, col, 0.45))
    peb = simple_mat("Pebble", (0.46, 0.4, 0.33), 0.8, var=(0.62, 0.56, 0.47))
    pts = scatter(2800 if not PREVIEW else 400, lambda x, z: (rd(x, z) < HALF + 0.15) & (sample(slow, x, z) < 0.3))
    merged("Pebbles", blob_template(1), place_list(pts, 0.014, 0.04, sink=0.35), peb)
    pts = scatter(120, lambda x, z: (np.abs(rd(x, z) - HALF - 0.3) < 0.3) & no_blk(x, z) & nohedge(x, z))
    merged("Stones", blob_template(2), place_list(pts, 0.05, 0.12, sink=0.45), simple_mat("Stone", (0.5, 0.49, 0.46), 0.8, var=(0.64, 0.62, 0.58)))
elif THEME == "darkwood":
    fern = blade_mat("Fern", (0.08, 0.18, 0.05), (0.18, 0.36, 0.1), (0.38, 0.56, 0.18))
    pts = scatter(4500 if not PREVIEW else 700, lambda x, z: (rd(x, z) > HALF + 0.3) & no_blk(x, z))
    merged("Ferns", tuft_template(9, 0.2, 0.03), place_list(pts, 0.7, 1.35), fern)
    gr = blade_mat("Grass", (0.14, 0.24, 0.08), (0.24, 0.36, 0.12), (0.42, 0.52, 0.2))
    pts = scatter(5000 if not PREVIEW else 800, lambda x, z: (rd(x, z) > HALF + 0.12) & no_blk(x, z) & (sample(PATCH, x, z) > 0.5))
    merged("Tufts", tuft_template(8, 0.1, 0.012), place_list(pts, 0.75, 1.3), gr)
    moss = simple_mat("Moss", (0.16, 0.3, 0.08), 0.9, var=(0.28, 0.42, 0.12))
    pts = scatter(1600 if not PREVIEW else 300, lambda x, z: (rd(x, z) > HALF + 0.2) & no_blk(x, z))
    merged("MossLumps", blob_template(2), [(p, y, s_, None) for (p, y, s_, t) in place_list(pts, 0.05, 0.12, sink=0.7)], moss)
    for k, (col, var) in enumerate([((0.4, 0.2, 0.07), (0.52, 0.28, 0.09)), ((0.46, 0.36, 0.12), (0.56, 0.44, 0.16)), ((0.24, 0.16, 0.08), (0.34, 0.22, 0.1))]):
        pts = scatter((1100, 700, 1600)[k] if not PREVIEW else 300, lambda x, z: (rd(x, z) > HALF - 0.2) & no_blk(x, z))
        merged("Leaves%d" % k, leaf_template(), place_list(pts, 0.7, 1.3, tilt=0.25), simple_mat("Leaf%d" % k, col, 0.75, var=var))
    cap = simple_mat("Toadstool", (0.78, 0.1, 0.06), 0.5, var=(0.9, 0.24, 0.1))
    centres = scatter(70 if not PREVIEW else 20, lambda x, z: (rd(x, z) > HALF + 0.4) & no_blk(x, z))
    pts = []
    for cx, cz in centres:
        for _ in range(int(RNG.integers(2, 6))):
            pts.append((cx + RNG.normal(0, 0.08), cz + RNG.normal(0, 0.08)))
    merged("Toadstools", blob_template(1), [((x, y, h + 0.035), yw, s_, None) for ((x, y, h), yw, s_, t) in place_list(pts, 0.016, 0.028)], cap)
    pale = simple_mat("Mushroom", (0.86, 0.8, 0.66), 0.6, var=(0.7, 0.58, 0.4))
    pts = scatter(400 if not PREVIEW else 100, lambda x, z: (rd(x, z) > HALF + 0.3) & no_blk(x, z))
    merged("Mushrooms", blob_template(1), [((x, y, h + 0.02), yw, s_, None) for ((x, y, h), yw, s_, t) in place_list(pts, 0.01, 0.02)], pale)
    stone = simple_mat("Stone", (0.36, 0.38, 0.34), 0.8, var=(0.46, 0.5, 0.4))
    pts = scatter(110, lambda x, z: (np.abs(rd(x, z) - HALF - 0.35) < 0.35) & no_blk(x, z))
    merged("Stones", blob_template(2), place_list(pts, 0.05, 0.13, sink=0.45, tilt=0.2), stone)
    peb = simple_mat("Pebble", (0.3, 0.26, 0.2), 0.8, var=(0.42, 0.36, 0.28))
    pts = scatter(1800 if not PREVIEW else 300, lambda x, z: rd(x, z) < HALF + 0.15)
    merged("Pebbles", blob_template(1), place_list(pts, 0.012, 0.035, sink=0.35), peb)
elif THEME == "castle":
    tram = blade_mat("Trampled", (0.27, 0.29, 0.15), (0.4, 0.42, 0.22), (0.56, 0.55, 0.34))
    pts = scatter(9000 if not PREVIEW else 1500, lambda x, z: (rd(x, z) > HALF + 0.15) & no_blk(x, z) & (sample(crater, x, z) < 0.2) &
                  (sample(PATCH, x, z) > 0.35))
    merged("Tufts", tuft_template(8, 0.1, 0.013), place_list(pts, 0.7, 1.35), tram)
    green = blade_mat("Meadow", (0.2, 0.34, 0.1), (0.32, 0.5, 0.16), (0.56, 0.7, 0.28))
    pts = scatter(5000 if not PREVIEW else 800, lambda x, z: (sample(outside, x, z) > 0.2) & no_blk(x, z))
    merged("MeadowTufts", tuft_template(9, 0.12, 0.014), place_list(pts, 0.75, 1.4), green)
    straw = blade_mat("Straw", (0.56, 0.46, 0.22), (0.76, 0.64, 0.32), (0.92, 0.82, 0.5))
    pts = scatter(1600 if not PREVIEW else 300, lambda x, z: (sample(blk["tents"], x, z) < 1.2) & (rd(x, z) > HALF + 0.1))
    merged("Straw", tuft_template(5, 0.07, 0.006), place_list(pts, 0.8, 1.4, tilt=1.2), straw)
    deb = simple_mat("Rubble", (0.44, 0.42, 0.39), 0.8, var=(0.58, 0.56, 0.52))
    pts = scatter(600 if not PREVIEW else 100, lambda x, z: ((sample(crater_rim, x, z) > 0.4) | (sample(PATCH, x, z) < 0.25)) & (rd(x, z) > HALF + 0.1) & no_blk(x, z))
    merged("Rubble", blob_template(1), place_list(pts, 0.025, 0.07, sink=0.3, tilt=0.5), deb)
    ball = simple_mat("Shot", (0.5, 0.49, 0.46), 0.7, var=(0.62, 0.6, 0.56))                              # spent catapult stones
    pts = scatter(40, lambda x, z: (sample(crater, x, z) > 0.3) | ((rd(x, z) > HALF + 1.0) & (sample(PATCH, x, z) < 0.3) & no_blk(x, z)))
    merged("Shot", blob_template(2), place_list(pts, 0.1, 0.16, sink=0.3), ball)
    arr = simple_mat("Arrow", (0.66, 0.54, 0.34), 0.7, var=(0.92, 0.9, 0.86))                            # volleys stuck in the turf
    centres = scatter(26, lambda x, z: (rd(x, z) > HALF + 0.3) & (rd(x, z) < HALF + 2.5) & no_blk(x, z))
    pts = []
    for cx, cz in centres:
        for _ in range(int(RNG.integers(5, 12))):
            pts.append((cx + RNG.normal(0, 0.25), cz + RNG.normal(0, 0.25)))
    merged("Arrows", arrow_template(), [(p, 1.1 + RNG.normal(0, 0.15), s_, t) for (p, y, s_, t) in place_list(pts, 0.85, 1.15, sink=0.25, tilt=0.12)], arr)
    soot = simple_mat("Charred", (0.07, 0.06, 0.05), 0.85, var=(0.16, 0.14, 0.12))
    pts = scatter(500 if not PREVIEW else 100, lambda x, z: (rd(x, z) > HALF + 0.2) & no_blk(x, z) & (sample(PATCH, x, z) < 0.3))
    merged("Charred", blob_template(1), place_list(pts, 0.02, 0.06, sink=0.4, tilt=0.6), soot)
    peb = simple_mat("Pebble", (0.42, 0.4, 0.36), 0.75, var=(0.56, 0.53, 0.48))
    pts = scatter(1500 if not PREVIEW else 300, lambda x, z: (rd(x, z) < HALF + 0.2) & (sample(slow, x, z) < 0.3))
    merged("Pebbles", blob_template(1), place_list(pts, 0.012, 0.03, sink=0.3), peb)
elif THEME == "jungle":
    off = lambda x, z, m_: (rd(x, z) > HALF + m_) & no_blk(x, z)
    nopave = lambda x, z: sample(gp_a, x, z) < 0.4
    dense = lambda x, z: (sample(outside, x, z) > 0.25) | (sample(PATCH, x, z) > 0.45)
    fern = blade_mat("Fern", (0.05, 0.14, 0.035), (0.14, 0.34, 0.07), (0.32, 0.56, 0.13), 0.65)
    pts = scatter(6500 if not PREVIEW else 900, lambda x, z: off(x, z, 0.3) & dense(x, z) & nopave(x, z))
    merged("Ferns", frond_template(7, 0.22, 0.05, 0.07), place_list(pts, 0.75, 1.4), fern)
    pts = scatter(2600 if not PREVIEW else 400, lambda x, z: off(x, z, 0.2) & nopave(x, z))
    merged("SmallFerns", frond_template(6, 0.13, 0.034, 0.045, 4), place_list(pts, 0.7, 1.3), fern)
    seed = simple_mat("Seedling", (0.17, 0.36, 0.07), 0.6, var=(0.3, 0.5, 0.12))
    pts = scatter(3600 if not PREVIEW else 500, lambda x, z: off(x, z, 0.2) & (sample(gp_a, x, z) < 0.7))
    merged("Seedlings", seedling_template(4, 0.07, 0.03, 0.045), place_list(pts, 0.7, 1.4), seed)
    broad = simple_mat("BroadLeaf", (0.1, 0.26, 0.06), 0.55, var=(0.2, 0.38, 0.09))
    pts = scatter(1300 if not PREVIEW else 200, lambda x, z: off(x, z, 0.35) & nopave(x, z))
    merged("BroadLeaves", seedling_template(5, 0.13, 0.055, 0.08), place_list(pts, 0.8, 1.3), broad)
    gr = blade_mat("Grass", (0.1, 0.2, 0.05), (0.2, 0.34, 0.09), (0.38, 0.52, 0.16))
    pts = scatter(3500 if not PREVIEW else 500, lambda x, z: off(x, z, 0.12) & (sample(PATCH, x, z) > 0.55))
    merged("Tufts", tuft_template(8, 0.1, 0.012), place_list(pts, 0.75, 1.3), gr)
    moss = simple_mat("Moss", (0.14, 0.3, 0.06), 0.9, var=(0.24, 0.42, 0.1))
    pts = scatter(1800 if not PREVIEW else 300, lambda x, z: off(x, z, 0.2))
    merged("MossLumps", blob_template(2), [(p, y, s_, None) for (p, y, s_, t) in place_list(pts, 0.05, 0.12, sink=0.7)], moss)
    pts = scatter(900 if not PREVIEW else 150, lambda x, z: (sample(gp_a, x, z) > 0.5) | ((sample(lane, x, z) > 0.5) & (rd(x, z) > 0.45)))
    merged("JointMoss", blob_template(1), [(p, y, s_, None) for (p, y, s_, t) in place_list(pts, 0.02, 0.045, sink=0.6)], moss)   # in the stones' joints
    for k, (col, var, n_, L_) in enumerate([((0.2, 0.3, 0.08), (0.3, 0.42, 0.1), 2600, 0.04), ((0.46, 0.34, 0.1), (0.56, 0.42, 0.14), 2000, 0.04),
                                           ((0.32, 0.17, 0.07), (0.42, 0.24, 0.09), 2400, 0.036), ((0.14, 0.22, 0.06), (0.2, 0.3, 0.08), 600, 0.075)]):
        pts = scatter(n_ if not PREVIEW else 300, lambda x, z: (rd(x, z) > HALF - 0.3) & no_blk(x, z) & (sample(gp_b, x, z) < 0.3) & (sample(lane, x, z) < 0.5))
        merged("Leaves%d" % k, leaf_template(L_, L_ * 0.48), place_list(pts, 0.7, 1.3, tilt=0.25), simple_mat("Leaf%d" % k, col, 0.7, var=var))
    for k, col in enumerate([(0.86, 0.1, 0.06), (1.0, 0.46, 0.06), (0.94, 0.2, 0.08)]):              # red and orange
        centres = scatter(55 if not PREVIEW else 15, lambda x, z: off(x, z, 0.5) & nopave(x, z))
        pts = []
        for cx, cz in centres:
            for _ in range(int(RNG.integers(3, 8))):
                pts.append((cx + RNG.normal(0, 0.11), cz + RNG.normal(0, 0.11)))
        merged("Flowers%d" % k, flower_template(5, 0.032), place_list(pts, 0.8, 1.25), simple_mat("Petal%d" % k, col, 0.45))
    root_mesh("Roots", ROOTS, simple_mat("Root", (0.27, 0.19, 0.12), 0.8, var=(0.38, 0.29, 0.19)))
    stone = simple_mat("Stone", (0.32, 0.36, 0.28), 0.8, var=(0.44, 0.48, 0.36))
    pts = scatter(100, lambda x, z: (np.abs(rd(x, z) - HALF - 0.35) < 0.35) & no_blk(x, z))
    merged("Stones", blob_template(2), place_list(pts, 0.05, 0.12, sink=0.45, tilt=0.2), stone)
    peb = simple_mat("Pebble", (0.42, 0.26, 0.18), 0.8, var=(0.54, 0.38, 0.27))
    pts = scatter(1000 if not PREVIEW else 200, lambda x, z: (rd(x, z) < HALF + 0.1) & (sample(lane, x, z) < 0.5) & (sample(gp_b, x, z) < 0.2))
    merged("Pebbles", blob_template(1), place_list(pts, 0.012, 0.032, sink=0.35), peb)
elif THEME == "harbor":
    land = lambda x, z: (sample(riv, x, z) > 0.25) & (sample(gp_b, x, z) < 0.1)
    cover = lambda x, z: RNG.random(np.shape(x)) < sample(gp_f, x, z)
    sg = blade_mat("SeaGrass", (0.36, 0.4, 0.18), (0.54, 0.58, 0.28), (0.82, 0.8, 0.5))
    pts = scatter(15000 if not PREVIEW else 2000, lambda x, z: (rd(x, z) > HALF + 0.12) & no_blk(x, z) & land(x, z) & cover(x, z))
    merged("SeaGrass", tuft_template(9, 0.17, 0.009), place_list(pts, 0.7, 1.4), sg)
    gg = blade_mat("Grass", (0.24, 0.36, 0.12), (0.36, 0.5, 0.17), (0.56, 0.66, 0.26))
    pts = scatter(5000 if not PREVIEW else 800, lambda x, z: (rd(x, z) > HALF + 0.2) & no_blk(x, z) & land(x, z) & (sample(gp_f, x, z) > 0.45) & cover(x, z))
    merged("Tufts", tuft_template(9, 0.1, 0.013), place_list(pts, 0.75, 1.3), gg)
    scrub = simple_mat("Scrub", (0.14, 0.27, 0.1), 0.85, var=(0.26, 0.38, 0.14))
    pts = scatter(1000 if not PREVIEW else 200, lambda x, z: (rd(x, z) > HALF + 0.5) & no_blk(x, z) & land(x, z) & (sample(gp_f, x, z) > 0.5))
    merged("Scrub", blob_template(2), [(p, y, s_, None) for (p, y, s_, t) in place_list(pts, 0.08, 0.17, sink=0.4)], scrub)
    for k, col in enumerate([(0.92, 0.46, 0.72), (1.0, 0.84, 0.22)]):                                # beach morning glory, sea daisies
        centres = scatter(35 if not PREVIEW else 10, lambda x, z: (rd(x, z) > HALF + 0.5) & inside_pf(x, z) & no_blk(x, z) & land(x, z) &
                          (sample(gp_f, x, z) > 0.35))
        pts = []
        for cx, cz in centres:
            for _ in range(int(RNG.integers(3, 7))):
                pts.append((cx + RNG.normal(0, 0.12), cz + RNG.normal(0, 0.12)))
        merged("Flowers%d" % k, flower_template(5, 0.034), place_list(pts, 0.8, 1.2), simple_mat("Petal%d" % k, col, 0.45))
    beachy = lambda x, z: (sample(gp_e, x, z) > 0.35) & (sample(riv, x, z) > 0.04) & (sample(gp_b, x, z) < 0.1) & (rd(x, z) > HALF)
    for k, (col, var) in enumerate([((0.98, 0.95, 0.9), (0.96, 0.86, 0.8)), ((0.96, 0.76, 0.7), (0.99, 0.88, 0.8)), ((0.92, 0.8, 0.6), (0.98, 0.92, 0.8))]):
        pts = scatter(420 if not PREVIEW else 80, beachy)
        merged("Shells%d" % k, blob_template(1), [(p, y, s_, None) for (p, y, s_, t) in place_list(pts, 0.012, 0.024, sink=0.5)],
               simple_mat("Shell%d" % k, col, 0.45, var=var))
    peb = simple_mat("Pebble", (0.6, 0.58, 0.54), 0.55, var=(0.84, 0.82, 0.76))
    pts = scatter(1700 if not PREVIEW else 300, lambda x, z: ((sample(gp_e, x, z) > 0.3) | (rd(x, z) < HALF + 0.1)) & (sample(riv, x, z) > 0.04) &
                  (sample(gp_b, x, z) < 0.1))
    merged("Pebbles", blob_template(1), place_list(pts, 0.012, 0.035, sink=0.35), peb)
    wrack = lambda x, z: (np.abs(sample(riv, x, z) - 0.75) < 0.4) & (sample(gp_b, x, z) < 0.1) & (rd(x, z) > HALF)   # the tide line
    drift = simple_mat("Driftwood", (0.62, 0.58, 0.5), 0.8, var=(0.78, 0.74, 0.66))
    pts = scatter(170 if not PREVIEW else 40, wrack)
    merged("Driftwood", stick_template(), place_list(pts, 0.6, 1.5, sink=0.2, tilt=0.06), drift)
    weed = simple_mat("Wrack", (0.15, 0.17, 0.07), 0.6, var=(0.27, 0.2, 0.09))
    pts = scatter(800 if not PREVIEW else 150, lambda x, z: wrack(x, z) & (np.abs(sample(riv, x, z) - 0.6) < 0.22))
    merged("Wrack", leaf_template(0.04, 0.018), place_list(pts, 0.7, 1.4, tilt=0.15), weed)
    rope = simple_mat("Rope", (0.6, 0.48, 0.3), 0.85, var=(0.7, 0.6, 0.4))
    stash = lambda x, z: (np.abs(sample(blk["crates"], x, z) + 0.05) < 0.45) | ((sample(gp_b, x, z) > 0.5) & (rd(x, z) > 0.45))
    pts = scatter(20 if not PREVIEW else 6, stash)
    merged("RopeCoils", coil_template(), place_list(pts, 0.85, 1.25), rope)
    pts = scatter(26 if not PREVIEW else 6, lambda x, z: stash(x, z) | (wrack(x, z) & (RNG.random(np.shape(x)) < 0.25)))
    merged("Ropes", rope_template(), place_list(pts, 0.8, 1.3), rope)
    rock = simple_mat("Rock", (0.36, 0.36, 0.36), 0.75, var=(0.5, 0.49, 0.47))
    pts = scatter(120, lambda x, z: (sample(blk["rocks"], x, z) < 0.9) & (sample(blk["rocks"], x, z) > -0.3))
    merged("Rocks", blob_template(2), place_list(pts, 0.04, 0.11, sink=0.4, tilt=0.3), rock)
elif THEME == "fortress":
    open_f = lambda x, z: (rd(x, z) > HALF + 0.15) & no_blk(x, z) & (sample(crater, x, z) < 0.1) & (sample(gp_a, x, z) < 0.1) & \
        (sample(gp_b, x, z) < 0.35)
    tram = blade_mat("Trampled", (0.27, 0.29, 0.15), (0.4, 0.42, 0.22), (0.56, 0.55, 0.34))
    pts = scatter(9000 if not PREVIEW else 1500, lambda x, z: open_f(x, z) & (sample(PATCH, x, z) > 0.35) & (sample(gp_d, x, z) < 0.3))
    merged("Tufts", tuft_template(8, 0.1, 0.013), place_list(pts, 0.7, 1.35), tram)
    green = blade_mat("Meadow", (0.2, 0.34, 0.1), (0.32, 0.5, 0.16), (0.56, 0.7, 0.28))
    pts = scatter(6500 if not PREVIEW else 1000, lambda x, z: (sample(outside, x, z) > 0.2) & no_blk(x, z))
    merged("MeadowTufts", tuft_template(9, 0.12, 0.014), place_list(pts, 0.75, 1.4), green)
    for k, col in enumerate([(1.0, 1.0, 0.94), (1.0, 0.84, 0.22)]):                                  # daisies, buttercups in the meadow
        centres = scatter(40 if not PREVIEW else 10, lambda x, z: (sample(outside, x, z) > 0.3) & no_blk(x, z))
        pts = []
        for cx, cz in centres:
            for _ in range(int(RNG.integers(3, 8))):
                pts.append((cx + RNG.normal(0, 0.12), cz + RNG.normal(0, 0.12)))
        merged("Flowers%d" % k, flower_template(5, 0.036), place_list(pts, 0.8, 1.25), simple_mat("Petal%d" % k, col, 0.45))
    straw = blade_mat("Straw", (0.56, 0.46, 0.22), (0.76, 0.64, 0.32), (0.92, 0.82, 0.5))
    pts = scatter(2200 if not PREVIEW else 400, lambda x, z: (rd(x, z) > HALF + 0.1) & (sample(gp_a, x, z) < 0.1) & (
        (sample(blk["crates"], x, z) < 1.3) | ((sample(outside, x, z) > 0.12) & (sample(outside, x, z) < 0.6) & (sample(PATCH, x, z) > 0.62))))
    merged("Straw", tuft_template(5, 0.07, 0.006), place_list(pts, 0.8, 1.4, tilt=1.2), straw)
    ball = simple_mat("Shot", (0.1, 0.1, 0.11), 0.42, var=(0.17, 0.16, 0.16), metal=0.55)            # spent cannonballs
    pts = scatter(26, lambda x, z: sample(crater, x, z) > 0.25) + \
        scatter(54, lambda x, z: open_f(x, z) & (rd(x, z) > HALF + 0.4))
    merged("Shot", ball_template(2), [(p, y, s_, None) for (p, y, s_, t) in place_list(pts, 0.05, 0.07, sink=0.45)], ball)
    clod = simple_mat("Clod", (0.34, 0.25, 0.16), 0.9, var=(0.46, 0.35, 0.22))
    pts = scatter(1100 if not PREVIEW else 200, lambda x, z: ((sample(crater_rim, x, z) > 0.3) | (sample(gp_b, x, z) > 0.45)) & (rd(x, z) > HALF + 0.1))
    merged("Clods", blob_template(1), place_list(pts, 0.025, 0.065, sink=0.3, tilt=0.5), clod)
    soot = simple_mat("Charred", (0.07, 0.06, 0.05), 0.85, var=(0.16, 0.14, 0.12))
    pts = scatter(500 if not PREVIEW else 100, lambda x, z: (sample(gp_d, x, z) > 0.4) & (rd(x, z) > HALF + 0.1))
    merged("Charred", blob_template(1), place_list(pts, 0.02, 0.05, sink=0.4, tilt=0.6), soot)
    grav = simple_mat("Gravel", (0.46, 0.44, 0.4), 0.8, var=(0.66, 0.63, 0.56))
    pts = scatter(5000 if not PREVIEW else 800, lambda x, z: rd(x, z) < HALF + 0.05)
    merged("Gravel", blob_template(1), place_list(pts, 0.01, 0.026, sink=0.35), grav)
    pts = scatter(100, lambda x, z: (np.abs(rd(x, z) - HALF - 0.3) < 0.3) & open_f(x, z))
    merged("Stones", blob_template(2), place_list(pts, 0.05, 0.12, sink=0.45), simple_mat("Stone", (0.48, 0.47, 0.44), 0.8, var=(0.62, 0.6, 0.56)))
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
          "bog": 0.33, "olive": 0.5, "coast": 0.53, "acropolis": 0.56, "farmland": 0.44, "darkwood": 0.26, "castle": 0.4,
          "jungle": 0.3, "harbor": 0.56, "fortress": 0.4}[THEME]
mask_in = (sample(outside, X, Z) < 0.5)
mi = np.asarray(Image.fromarray((mask_in * 255).astype(np.uint8)).resize((im.shape[1], im.shape[0]))) > 127
cur = im[mi].mean()
im = np.clip(im * (TARGET / max(cur, 1e-3)) ** 0.8, 0, 1)
import ground_fade                       # the outer band blends to one colour: no seam against the far-ground plane
im = ground_fade.fade(im, 1.6 * PX)
Image.fromarray((im * 255 + 0.5).astype(np.uint8)).save(OUT)
os.remove(OUT + ".raw.png")
log("wrote", OUT, im.shape, "mean %.3f -> %.3f" % (cur, im[mi].mean()))
