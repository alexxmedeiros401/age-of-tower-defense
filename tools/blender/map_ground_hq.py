"""HQ ground for the Stone Age to Modern Age maps: the map's ground as a real 3D surface, rendered straight down into
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
meadow round the edges (fortress); Industrial Age: a foundry district of cinder and slag-black earth, old yards of
cracked flagstones and cobbles, riveted iron floor plates round the machines and in loading bays, brick aprons round the
mills, rust stains, oily puddles, coke and scrap, rail spurs on cinder ballast ending at buffer stops, granite-sett roads
whose fast lanes are laid with steel plates (factory); a railway yard of cinder, weeds and coal dust, tracks on sleepers
and ballast with turnouts, buffer stops and a turntable whose stalls fan out, level crossings boarded where the tracks
cross the packed-cinder roads, granite setts on the fast lanes, flagged goods platforms under the crates (railyard); a
smoky Victorian city of sett streets between granite kerbs and flagged pavements, gully grates and manholes, yards
(flags, cobbles, brick, earth, waste ground) between low brick walls, back lanes, dock pools behind coping stones in a
quay with a flush tramway (smog). Sleepers, rails, buffer stops, walls and bollards are 3D. Modern Age: an airbase of
mown olive turf, a runway 09/27 between the service roads (thresholds, numbers, touchdown and aiming-point bars, tyre
rubber, edge lights), taxiways with yellow centre and edge lines and hold-short bars, an apron of concrete slabs with
parking stands, hazard-striped pads under the machines, the crates' pad, a helipad, a hangar hardstand, craters blasted
in and scorched round (military); a city centre of asphalt avenues with double yellow lines, red bus lanes on the speed
lanes, a brick table over the crossroads, zebra crossings, granite kerbs, sidewalks with tree pits, drains and
manholes, its blocks cut into lots (granite tiles, concrete, brick, slate, parking, lawns with planted beds), a plaza
with an inlaid compass and planters, polished plinths under the buildings (metro); a suburb of striped lawns, curving
streets with a yellow centre line, kerbs, verges and sidewalks, two cul-de-sacs, driveways, garden paths, flower beds,
patios, a park with a playground, and backyard swimming pools (the lake zones) with travertine decks (suburb). Their
markings are painted at the render's resolution (PIL), so they stay crisp. Digital Age: a cleanroom hall of white epoxy,
anti-static tile and raised-floor bays between yellow safety lines, green walkways, floor grates, covered cable
trenches, marked equipment bays, steel plinths under the machines, frost-ringed drain pads with pipe stubs under the
tanks, the robots' lanes dark service tracks with steel edges, hazard-striped borders, guide lines and fiducial tags,
decontamination grilles on the slow stretches (lab); a high-desert ground station of red-brown sand, ripples, desert
pavement and stones, packed gravel access roads with tyre ruts and a worn painted edge, reflector posts, concrete dish
foundations ringed with anchor bolts, gravel beds with footings and covered cable trenches under the solar arrays, a
fenced concrete compound and its gravel spur, mast pads (satellite); a cyberpunk district of dark wet asphalt with cyan
edge lines and magenta centre dashes, data lanes on the fast stretches, steel kerbs with light strips, deck-plate
sidewalks with grates, hex-tiled plazas, gridded slabs, parking, scorched pylon bases, glowing data pits, the neon's
glow and reflections painted into the wet ground (neon). Their rift ends get gate plates (violet in, cyan out), and their
crisp shapes (road edges, pads, plinths, pits, hex tiles) are distance fields at the render's own resolution. The Data
Center (built on the Digital Age's tools): the robots' frozen coolant halls, steel deck plates, bar grates and riveted
panels rimed with frost, coolant channels of pale blue coolant with pipes laid beside them, ice crusts and frozen spills,
condensation streaks, hazard lines, round frozen drain pads under the ice, chiller plinths with fan grilles under the
machines, the robots' lanes heated service tracks of dark steel (less frost, meltwater, guide lines, heat traces), an
ice sheet over the slow stretch, induction plates on the fast one (cooling); an endless server hall of raised-floor
tiles, perforated vent tiles in the cold aisles between rows of rack footprints, blue cold-aisle and amber hot-aisle
markings, the racks' status lights reflected on the floor, covered cable trenches with some covers off, the robots'
lanes dark service aisles edged with guide lights, rack plinths and heavy mainframe pads under the zones (server); the
heart of the machine, a dark polished floor of big panels and hex tiles with glowing cyan and red circuit traces that
branch and converge toward its centre, energy conduits from the pillars' sockets (glowing rings), scorch marks, cracks,
oil and debris of the battle, scorched craters under the wrecks, the robots' lanes bright data highways (core). For highland, bog, coast, harbor, smog and
suburb, --watersrc PATH also writes the exact water mask (the stream, its fords, the lochans, the bog pools, the inlet,
the dock pools, the swimming pools) for tools/water_mask.py --src PATH. --maskdump DIR writes the Industrial themes' feature
masks without rendering; --dry builds the scene without rendering.
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
                                         "statue", "building", "tents", "crates", "crater", "machine", "coal", "tank", "dish",
                                         "panels", "pylon", "pit", "ice", "rack", "wreck")}
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
       "jungle": (0.5, 0.62, 0.55), "harbor": (0.64, 0.78, 0.97), "fortress": (0.62, 0.7, 0.86),
       "factory": (0.6, 0.57, 0.55), "railyard": (0.62, 0.66, 0.72), "smog": (0.6, 0.6, 0.56),
       "military": (0.64, 0.74, 0.92), "metro": (0.6, 0.66, 0.8), "suburb": (0.62, 0.75, 0.96),
       "lab": (0.86, 0.9, 0.96), "satellite": (0.62, 0.68, 0.82), "neon": (0.42, 0.36, 0.6),
       "cooling": (0.8, 0.88, 0.98), "server": (0.6, 0.66, 0.8), "core": (0.46, 0.38, 0.5)}[THEME]
wd.node_tree.nodes["Background"].inputs["Color"].default_value = SKY + (1,)
wd.node_tree.nodes["Background"].inputs["Strength"].default_value = {"meadow": 1.05, "snow": 1.0, "volcano": 0.8, "delta": 1.05,
                                                                    "desert": 1.0, "canyon": 0.95, "highland": 1.0, "forge": 0.82,
                                                                    "bog": 0.98, "olive": 1.05, "coast": 1.05, "acropolis": 1.05,
                                                                    "farmland": 1.05, "darkwood": 0.85, "castle": 1.0,
                                                                    "jungle": 0.92, "harbor": 1.05, "fortress": 1.0,
                                                                    "factory": 0.92, "railyard": 0.98, "smog": 0.95,
                                                                    "military": 1.0, "metro": 0.95, "suburb": 1.05,
                                                                    "lab": 1.35, "satellite": 1.0, "neon": 0.7,
                                                                    "cooling": 1.2, "server": 0.95, "core": 0.7}[THEME]
# the game's sun: Godot rotation (-52, -36, 0) -> light travelling (0.362, -0.788, -0.498) in Godot = (x, y_b, z_b)
# (0.362, 0.498, -0.788) in Blender (y_b = -z_godot)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = {"meadow": 2.7, "snow": 2.6, "volcano": 2.3, "delta": 2.7, "desert": 2.8, "canyon": 2.6, "highland": 2.6, "forge": 2.3,
                   "bog": 2.5, "olive": 2.8, "coast": 2.75, "acropolis": 2.8, "farmland": 2.75, "darkwood": 2.2, "castle": 2.6,
                   "jungle": 2.45, "harbor": 2.8, "fortress": 2.6, "factory": 2.4, "railyard": 2.55, "smog": 2.2,
                   "military": 2.7, "metro": 2.5, "suburb": 2.75, "lab": 1.7, "satellite": 2.6, "neon": 1.9,
                   "cooling": 1.8, "server": 1.8, "core": 1.9}[THEME]
sun.data.angle = math.radians({"lab": 35, "cooling": 30, "server": 30}.get(THEME, 8))    # (indoor halls: soft light)
sun.data.color = {"meadow": (1.0, 0.95, 0.86), "snow": (1.0, 0.98, 0.96), "volcano": (1.0, 0.75, 0.55), "delta": (1.0, 0.95, 0.86),
                  "desert": (1.0, 0.94, 0.82), "canyon": (1.0, 0.9, 0.78), "highland": (1.0, 0.95, 0.87), "forge": (1.0, 0.8, 0.62),
                  "bog": (0.98, 0.96, 0.86), "olive": (1.0, 0.95, 0.84), "coast": (1.0, 0.96, 0.88), "acropolis": (1.0, 0.95, 0.85),
                  "farmland": (1.0, 0.95, 0.86), "darkwood": (0.92, 0.96, 0.82), "castle": (1.0, 0.93, 0.84),
                  "jungle": (1.0, 0.95, 0.8), "harbor": (1.0, 0.96, 0.88), "fortress": (1.0, 0.93, 0.83),
                  "factory": (1.0, 0.88, 0.74), "railyard": (1.0, 0.92, 0.8), "smog": (1.0, 0.9, 0.74),
                  "military": (1.0, 0.95, 0.86), "metro": (1.0, 0.96, 0.9), "suburb": (1.0, 0.96, 0.88),
                  "lab": (0.96, 0.98, 1.0), "satellite": (1.0, 0.94, 0.86), "neon": (0.86, 0.84, 1.0),
                  "cooling": (0.9, 0.95, 1.0), "server": (0.88, 0.92, 1.0), "core": (1.0, 0.86, 0.9)}[THEME]
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
    if zf["fast"]:      # the causeway spans the whole road (no strip of clay down its sides); its end is ragged
        lane = np.maximum(lane, road * np.clip((HALF + 0.25 + (fbm(0.3, 2, 184) - 0.5) * 0.4 - fd) / 0.05, 0, 1))
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
                        jr.uniform(1.6, 3.4), jr.uniform(0.065, 0.09), False)
            if len(pts) > 14 and jr.random() < 0.7:
                i0 = int(len(pts) * jr.uniform(0.3, 0.6))
                _root(pts[i0][0], pts[i0][1], a + jr.choice([-1.0, 1.0]) * jr.uniform(0.5, 0.9), jr.uniform(0.7, 1.8), 0.042, False)
    n_free = 0
    for _ in range(3000):
        if n_free >= 64:
            break
        x, z = jr.uniform(G.X0 + 1.5, G.X0 + G.W - 1.5), jr.uniform(G.Z0 + 1.5, G.Z0 + G.H - 1.5)
        if _at(dist, x, z) < HALF + 0.7 or _at(BLK_ANY, x, z) < 0.2:
            continue
        a = jr.uniform(0, 2 * math.pi)
        pts = _root(x, z, a, jr.uniform(1.2, 3.2), jr.uniform(0.042, 0.06), True)
        if len(pts) > 16 and jr.random() < 0.5:
            i0 = int(len(pts) * jr.uniform(0.3, 0.7))
            _root(pts[i0][0], pts[i0][1], a + jr.choice([-1.0, 1.0]) * jr.uniform(0.5, 1.0), jr.uniform(0.6, 1.5), 0.032, True)
        n_free += 1
    log("jungle: roots", len(ROOTS), "paving px", int((gp_a > 0.5).sum()), "puddle px", int((gp_b > 0.5).sum()))
if THEME == "harbor":
    # the cove: wet sand along the waterline, the inlet's depth (sandy shallows to deep teal), surf at its edges, plank
    # decks where the roads run down to the water and over it, and plank floors under the smugglers' stacks of crates
    gp_a = np.clip(1 - riv / (0.22 + 0.42 * fbm(0.7, 3, 199)), 0, 1) * np.clip(riv / 0.03 + 1, 0, 1)   # wet sand, a ragged band
    surf = np.exp(-((riv + 0.08 + (fbm(0.35, 2, 191) - 0.5) * 0.07) / 0.042) ** 2) * np.clip((fbm(0.22, 3, 192) - 0.24) / 0.18, 0, 1)
    surf2 = np.exp(-((riv + 0.32 + (fbm(0.5, 2, 194) - 0.5) * 0.16) / 0.03) ** 2) * np.clip((fbm(0.3, 3, 195) - 0.5) / 0.2, 0, 1)
    gp_d = np.maximum(surf, surf2 * 0.35)                                                          # surf, a fainter line beyond
    gp_c = np.clip(-riv / 0.95, 0, 1)                                                              # depth
    # boardwalks: where a road crosses the inlet it is planked from bank to bank and a way up each beach, the deck ending
    # square across the road on a whole plank, a sill at each end and a beam down each side, straight-edged inside the
    # road's sand (a road that only runs near the water, down to a tunnel's mouth, stays sand)
    deck = np.zeros(X.shape)
    gp_h = np.zeros(X.shape)
    for lg in legs:
        P = np.asarray(lg, np.float64)
        cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        s_ = np.arange(0.0, cum[-1], 0.04)
        cx_, cz_ = np.interp(s_, cum, P[:, 0]), np.interp(s_, cum, P[:, 1])
        rv_ = riv[np.clip(((cz_ - G.Z0) * MPX).astype(int), 0, g.h - 1), np.clip(((cx_ - G.X0) * MPX).astype(int), 0, g.w - 1)]
        wet_ = np.concatenate([[False], rv_ < 1.0, [False]]).astype(int)          # (its ends on the straight, clear of a bend)
        for i0, i1 in zip(np.flatnonzero(np.diff(wet_) == 1), np.flatnonzero(np.diff(wet_) == -1) - 1):
            if rv_[i0:i1 + 1].min() > 0.0:
                continue
            a0, a1 = math.floor(s_[i0] / 0.24) * 0.24, math.ceil(s_[i1] / 0.24) * 0.24
            dl, al = g.poly_dist([lg], margin=2.0)
            this = np.clip((HALF - 0.06 - dl) / 0.03, 0, 1) * ((al >= a0) & (al <= a1) & (dl <= dist + 1e-6))
            deck = np.maximum(deck, this)
            gp_h = np.maximum(gp_h, (np.exp(-((dl - (HALF - 0.12)) / 0.035) ** 2) + np.exp(-((al - a0 - 0.06) / 0.03) ** 2) +
                                     np.exp(-((al - a1 + 0.06) / 0.03) ** 2)) * this)
    gp_h = np.clip(gp_h, 0, 1)
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
    log("harbor: deck px", int((deck > 0.5).sum()), "pads px", int((pads > 0.5).sum()), "water px", int((riv < 0).sum()))
if THEME == "fortress":
    fr2 = np.random.default_rng(47)
    bnd = m["bounds"]

    def _blast(cx, cz, r_, d_):
        """Scorch round a crater: sooty over its rim and burnt out past it in a ragged star of blast rays, less so down in
        the bowl (raw earth thrown up and fallen back)."""
        ang = np.arctan2(Z - cz, X - cx)
        ph0 = fr2.uniform(0, 2 * math.pi)
        rays = 0.5 + 0.5 * np.sin(ang * int(fr2.integers(7, 12)) + ph0 + np.sin(ang * 3 + ph0) * 0.9)
        reach = r_ * (1.4 + 0.9 * rays ** 2)
        return np.clip((reach - d_) / (reach - r_ * 0.9), 0, 1) ** 0.8 * (0.5 + 0.5 * np.clip((d_ - r_ * 0.35) / (r_ * 0.5), 0, 1))

    # bomb craters: the crater blockers, deep with raised rims, and smaller ones scattered over the field, off the road
    for (bx, bz, br, kind) in BLOCKERS:
        if kind != "crater":
            continue
        r_ = br * 0.86
        d_ = np.hypot(X - bx, Z - bz) + (fbm(0.6, 2, int(abs(bx * 7 + bz * 13)) % 997 + 500) - 0.5) * 0.4
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
        d_ = np.hypot(X - cx, Z - cz) + (fbm(0.3, 2, 600 + n_cr) - 0.5) * 0.5 * r_        # (a lumpy outline, not a disc)
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
        gp_b = np.exp(-((td - 0.46) / 0.18) ** 2) * np.clip(-tsd / 0.1, 0, 1) + 0.3 * np.exp(-((td - 0.34) / 0.1) ** 2) * np.clip(tsd / 0.1, 0, 1)
    if saps:
        sd2, _sal = g.poly_dist(saps, margin=1.2)
        gp_b = np.maximum(gp_b, 0.55 * np.exp(-((sd2 - 0.38) / 0.12) ** 2) * np.clip((sd2 - 0.14) / 0.1, 0, 1))
        td = np.minimum(td, sd2)
    gp_a = np.clip((0.2 - td) / 0.05, 0, 1)
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
    if tracks:          # (each groove fades out here and there, where the turf took the wheels)
        wd_, _wa = g.poly_dist(tracks, margin=0.4)
        gp_c = np.exp(-(wd_ / 0.06) ** 2) * np.clip((dist - HALF - 0.1) / 0.2, 0, 1) * np.clip((fbm(0.7, 3, 223) - 0.3) / 0.15, 0, 1)
    log("fortress: craters", n_cr, "+ blockers; parallels", len(par), [(round(c_[1], 2), round(c_[2], 1), round(c_[3], 1)) for c_ in chosen],
        "saps", len(saps), "rut lines", len(tracks))

# ------------------------------------------------------------------------------------------------ Industrial Age features
# IND holds each Industrial theme's own feature masks (they go to the material in mask11..mask14, named per theme below);
# rc_al / rc_sd are the road's own coordinates (distance along it, signed distance across it), so setts, flags and kerbs
# follow the road round its bends; TRACKS is the railway (railyard, factory): each track's centre line, its sleepers and
# rails built in 3D further down; tk_* the distance to the nearest track, along it and across it.
DC_T = THEME in ("cooling", "server", "core")                 # (The Data Center: built on the Digital Age's tools)
DIG_T = THEME in ("lab", "satellite", "neon") or DC_T         # (the Digital Age: built on the Modern Age's tools)
IND_T = THEME in ("factory", "railyard", "smog", "military", "metro", "suburb") or DIG_T
MOD_T = THEME in ("military", "metro", "suburb")              # (the Modern Age: its own features further down)
IND = {}
TRACKS = []                # {"pts": N x 2 world (x, z) 0.05 apart, "buf": a buffer stop at its end}
TURNTABLE = None           # (x, z, radius, the bridge's angle in degrees)
WALLS = []                 # smog: the yards' low brick walls, runs of (x, z) points
POOLS = []                 # smog: the dock pools (x, z, half width, half height, corner radius)
MANHOLES = []
rc_al = rc_sd = tk_al = tk_sd = np.zeros(X.shape)
tk_d = np.full(X.shape, 1e9)


def _trk(x, z, a_deg, *ops, buf=False, flush=False, step=0.05):
    """A track's centre line from (x, z) heading a_deg (0 = +x, 90 = +z), built of ("L", length), ("A", radius, degrees;
    + turns toward +z when heading +x), ("X", x) / ("Z", z) (straight on until x / z reaches that value)."""
    a = math.radians(a_deg)
    pts = [(x, z)]
    for op in ops:
        if op[0] in ("L", "X", "Z"):
            L = op[1] if op[0] == "L" else ((op[1] - x) / math.cos(a) if op[0] == "X" else (op[1] - z) / math.sin(a))
            n = max(1, int(abs(L) / step))
            for _ in range(n):
                x, z = x + math.cos(a) * L / n, z + math.sin(a) * L / n
                pts.append((x, z))
        else:
            R, da = op[1], math.radians(op[2])
            n = max(2, int(abs(da) * R / step))
            for _ in range(n):
                a += da / n / 2
                x, z = x + math.cos(a) * abs(da) * R / n, z + math.sin(a) * abs(da) * R / n
                a += da / n / 2
                pts.append((x, z))
    TRACKS.append({"pts": np.array(pts), "buf": buf, "flush": flush})
    return x, z


def _scurve(R, off):
    """The angle (degrees) of each of the two arcs of radius R of an S-curve that shifts a track sideways by off."""
    return math.degrees(math.acos(1 - abs(off) / (2 * R)))


def _rrect(cx, cz, hw, hh, rc):
    """Signed distance to a rounded rectangle (< 0 inside)."""
    qx, qz = np.abs(X - cx) - (hw - rc), np.abs(Z - cz) - (hh - rc)
    return np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - rc


if IND_T:
    # (the road's coordinates from its legs smoothed through their points, so the setts follow a bend in an even fan
    # instead of jumping at each of its points; across it the true distance, signed)
    def _round(lg, step=0.1, it=3):
        P = np.asarray(lg, np.float64)
        cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        t_ = np.linspace(0, cum[-1], max(2, int(cum[-1] / step) + 1))
        P = np.stack([np.interp(t_, cum, P[:, 0]), np.interp(t_, cum, P[:, 1])], 1)
        for _ in range(it):                                            # (Chaikin's corner cutting, the ends kept)
            Q = np.empty((2 * len(P) - 2, 2))
            Q[0::2] = 0.75 * P[:-1] + 0.25 * P[1:]
            Q[1::2] = 0.25 * P[:-1] + 0.75 * P[1:]
            P = np.vstack([P[:1], Q, P[-1:]])
        return P.tolist()

    _rd, rc_al, rc_sd = g.poly_dist([_round(lg) for lg in legs], margin=1.8, signed=True)
    rc_sd = np.where(rc_sd < 0, -1.0, 1.0) * np.minimum(dist, _rd)
    rd_hard = np.clip((HALF - dist) / 0.03, 0, 1)                      # the road itself, a crisp edge (no wobble)
    if THEME in ("factory", "smog") or MOD_T or DIG_T:                # (paved roads: straight edges, kerbs)
        road = rd_hard
        edge = np.exp(-((dist - HALF) / 0.1) ** 2)
        rut = np.exp(-((dist - 0.36) / 0.09) ** 2) * road
    S12 = _scurve(5.0, 1.2)                                            # (sidings 1.2 apart)
    if zf["fast"]:                                                     # (the fast lanes end square across the road)
        lane = lane * ((fd - np.abs(fsd)) < 0.02)
if THEME == "railyard":
    # the yard: a running line along its top; two goods sidings off it to the crates, a third from the east; a coal road
    # past two coal heaps to a staithe at the third; a line right across the yard (level crossings over both roads) to a
    # turntable whose stalls fan out toward the bottom-right corner (for the engine shed); a siding to the crates bottom
    # left, a dead-end siding along the right edge
    _trk(-21.5, -7.75, 0, ("X", 19.5))
    _trk(-6.0, -7.75, 0, ("A", 5.0, S12), ("A", 5.0, -S12), ("X", 6.85), buf=True)
    _trk(-0.9, -6.55, 0, ("A", 5.0, S12), ("A", 5.0, -S12), ("X", 6.45), buf=True)
    _trk(15.6, -7.75, 180, ("A", 5.0, -S12), ("A", 5.0, S12), ("X", 9.6), buf=True)
    _trk(19.5, -4.3, 180, ("X", 9.8), buf=True)
    _trk(-21.5, -3.6, 0, ("X", -0.62), buf=True)
    TURNTABLE = (10.6, 4.0, 1.3, 28.0)
    _trk(-21.5, 4.0, 0, ("X", TURNTABLE[0] - TURNTABLE[2] - 0.02))
    _trk(-19.6, 4.0, 0, ("A", 5.0, S12), ("A", 5.0, -S12), ("X", -10.9), buf=True)
    _trk(19.5, 0.1, 180, ("X", 5.7), buf=True)
    for ang in (-28, 0, 28, 56, 84):
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        r0 = TURNTABLE[2] + 0.04
        _trk(TURNTABLE[0] + ca * r0, TURNTABLE[1] + sa * r0, ang, ("L", {84: 3.9, 56: 4.0}.get(ang, 3.6)), buf=True)
if THEME == "factory":
    # rail spurs: along the top to the machine, turning down the middle of the second bend; from the east to the
    # machine's other side; along the bottom to the last mill; from the east between the two mills
    _trk(-21.5, -7.8, 0, ("X", 5.0), buf=True)
    _trk(-6.6, -7.8, 0, ("A", 2.6, 90), ("Z", 3.3), buf=True)
    _trk(19.5, -6.4, 180, ("X", 9.1), buf=True)
    _trk(-21.5, 7.85, 0, ("X", 10.4), buf=True)
    _trk(19.5, 4.15, 180, ("X", 10.45), buf=True)
if THEME == "smog":
    # a dockside tramway between the two basins: rails set flush in the quay's setts, a buffer stop at its landward end
    _trk(19.5, 0.05, 180, ("X", 6.75), buf=True, flush=True)
if any(not t["flush"] for t in TRACKS):
    tk_d, tk_al, tk_sd = g.poly_dist([t["pts"][::2] for t in TRACKS if not t["flush"]], margin=1.8, signed=True)
    log("tracks", len(TRACKS), "length %.1f" % sum(float(np.hypot(*np.diff(t["pts"], axis=0).T).sum()) for t in TRACKS))
if IND_T:
    on_road = np.clip((HALF + 0.08 - dist) / 0.06, 0, 1)
    wob_t = (fbm(0.5, 3, 401) - 0.5) * 0.22
    IND["ballast"] = np.clip((0.7 + wob_t - tk_d) / 0.08, 0, 1) * (1 - on_road)
    puddle_n = fbm(1.1, 3, 402) + (fbm(0.25, 2, 403) - 0.5) * 0.08
    pud_t = lambda q: np.quantile(puddle_n, q)
if THEME == "factory":
    # a foundry district's ground: cinder and slag-black earth; patches of cracked flagstones and of cobbles (old yards);
    # iron floor plates round the machines and in loading bays; brick aprons under the mills; rust stains; oily puddles;
    # drifts of coke dust; the rail spurs' cinder ballast
    fr3 = np.random.default_rng(61)
    off_rd = np.clip((dist - HALF - 0.3) / 0.15, 0, 1)
    clear = off_rd * np.clip((BLK_ANY - 0.15) / 0.2, 0, 1) * (1 - IND["ballast"])
    fn1, fn2 = fbm(3.2, 3, 411) + (fbm(0.3, 2, 412) - 0.5) * 0.1, fbm(3.0, 3, 413) + (fbm(0.3, 2, 414) - 0.5) * 0.1
    IND["flags"] = np.clip((fn1 - np.quantile(fn1, 0.85)) / 0.015, 0, 1) * clear
    IND["cobble"] = np.clip((fn2 - np.quantile(fn2, 0.87)) / 0.015, 0, 1) * clear * (1 - IND["flags"])
    plates = np.zeros(X.shape)
    for (bx, bz, br, kind) in BLOCKERS:              # the machines stand on iron floors (square, on the plate grid)
        if kind == "machine":
            h_ = math.ceil((br + 0.2) / 0.35) * 0.35
            x0_, z0_ = round((bx - h_) / 0.35) * 0.35, round((bz - h_) / 0.35) * 0.35
            plates = np.maximum(plates, ((X > x0_) & (X < x0_ + 2 * h_) & (Z > z0_) & (Z < z0_ + 2 * h_)).astype(float))
    n_pl = 0
    for _ in range(400):                             # loading bays: a few more plate floors, off the roads and spurs
        if n_pl >= 7:
            break
        w_, h_ = fr3.integers(2, 5) * 0.7, fr3.integers(2, 4) * 0.7
        x0_, z0_ = round(fr3.uniform(-15, 15 - w_) / 0.7) * 0.7, round(fr3.uniform(-8.5, 8.5 - h_) / 0.7) * 0.7
        sub = (X > x0_ - 0.4) & (X < x0_ + w_ + 0.4) & (Z > z0_ - 0.4) & (Z < z0_ + h_ + 0.4)
        if dist[sub].min() < HALF + 0.35 or tk_d[sub].min() < 0.75 or BLK_ANY[sub].min() < 0.1 or plates[sub].max() > 0:
            continue
        plates = np.maximum(plates, ((X > x0_) & (X < x0_ + w_) & (Z > z0_) & (Z < z0_ + h_)).astype(float))
        n_pl += 1
    IND["plates"] = plates * (1 - on_road)
    IND["flags"] *= 1 - plates
    IND["cobble"] *= 1 - plates
    apron = np.zeros(X.shape)
    for (bx, bz, br, kind) in BLOCKERS:              # brick aprons round the mills (a rounded square inside the zone)
        if kind == "building":
            apron = np.maximum(apron, np.clip(-_rrect(bx, bz, br * 0.84 + 0.12, br * 0.84 + 0.12, 0.45) / 0.03, 0, 1))
    IND["apron"] = apron * (1 - on_road)
    IND["puddle"] = np.clip((pud_t(0.035) - puddle_n) / 0.02, 0, 1) * (1 - IND["ballast"]) * (1 - apron) * np.clip(BLK_ANY / 0.2, 0, 1)
    IND["rust"] = np.clip((fbm(0.7, 3, 415) - 0.6) / 0.1, 0, 1)
    IND["slag"] = np.clip((fbm(1.2, 4, 416) - 0.64) / 0.04, 0, 1) * off_rd * (1 - plates) * (1 - apron)
    IND["coke"] = np.clip((fbm(0.9, 3, 417) - 0.6) / 0.08, 0, 1) * (1 - on_road)
    for (bx, bz, br, kind) in BLOCKERS:              # coke and soot dust round the machines
        if kind == "machine":
            IND["coke"] = np.maximum(IND["coke"], np.clip((1.2 + (fbm(0.4, 2, 418) - 0.5) * 0.8 - blk["machine"]) / 0.8, 0, 1) * (1 - plates) * (1 - on_road))
    log("factory: plate bays", n_pl, "flags px", int((IND["flags"] > 0.5).sum()), "cobble px", int((IND["cobble"] > 0.5).sum()),
        "puddle px", int((IND["puddle"] > 0.5).sum()))
if THEME == "railyard":
    tt = TURNTABLE
    dtt = np.hypot(X - tt[0], Z - tt[1])
    IND["pit"] = np.clip((tt[2] - dtt) / 0.03, 0, 1)
    IND["coping"] = np.clip((tt[2] + 0.16 - dtt) / 0.03, 0, 1) * (1 - IND["pit"])
    IND["ballast"] *= 1 - np.clip((tt[2] + 0.12 - dtt) / 0.05, 0, 1)
    IND["xing"] = road * np.clip((0.6 - tk_d) / 0.03, 0, 1)                            # the level crossings' boards
    IND["tt_u"] = (np.arctan2(Z - tt[1], X - tt[0]) / (2 * math.pi) + 0.5) * 24       # (the coping's 24 stones)
    coal = np.clip((fbm(1.0, 3, 421) - 0.68) / 0.08, 0, 1) * 0.45
    for (bx, bz, br, kind) in BLOCKERS:
        if kind == "coal":
            coal = np.maximum(coal, np.clip((0.35 + (fbm(0.3, 2, 422) - 0.5) * 0.7 - blk["coal"]) / 0.45, 0, 1) ** 1.5)
    IND["coal"] = coal * (1 - rd_hard) * (1 - IND["pit"])
    pads = np.zeros(X.shape)
    for (bx, bz, br, kind) in BLOCKERS:              # the goods platforms under the crates: flagged, kerbed with stone
        if kind == "crates":
            pads = np.maximum(pads, np.clip(-_rrect(bx, bz, br * 0.86, br * 0.8, 0.3) / 0.2, 0, 1))
    IND["pads"] = pads
    IND["weeds"] = np.clip((fbm(0.9, 4, 423) - 0.56) / 0.12, 0, 1)
    IND["drip"] = np.exp(-(tk_sd / 0.07) ** 2) * IND["ballast"]                          # oil dripped down the track's middle
    IND["puddle"] = np.clip((pud_t(0.08) - puddle_n) / 0.02, 0, 1) * np.clip((rut * 1.2 + 0.4) * rd_hard, 0, 1) * (1 - IND["xing"])
    log("railyard: ballast px", int((IND["ballast"] > 0.5).sum()), "crossing px", int((IND["xing"] > 0.5).sum()))
if THEME == "smog":
    # a smog-choked Victorian city: the streets' carriageways of setts between granite kerbs and flagged pavements; the
    # ground between them cut into little yards (flagged, cobbled, brick-paved, bare earth, cinder waste ground) by low
    # brick walls, back lanes between some of them; dock pools (the lake zones) edged with coping stones in a quay
    sr = np.random.default_rng(53)
    RL = []                                          # the streets' straight runs: (axis, value, lo, hi)
    for sp in specs:
        P_ = sp["pts"]
        for (a0, b0), (a1, b1) in zip(P_[:-1], P_[1:]):
            if abs(a0 - a1) < 1e-6 and abs(b1 - b0) > 0.3:
                RL.append((0, a0, min(b0, b1), max(b0, b1)))
            elif abs(b0 - b1) < 1e-6 and abs(a1 - a0) > 0.3:
                RL.append((1, b0, min(a0, a1), max(a0, a1)))
    LEAVES = []

    def _split(x0, z0, x1, z1, depth):
        w, h = x1 - x0, z1 - z0
        if max(w, h) < 2.3 or (max(w, h) < 3.6 and sr.random() < 0.4):
            LEAVES.append((x0, z0, x1, z1, 0))
            return
        axes = [0, 1] if abs(w - h) < 0.8 else ([0] if w > h else [1])
        for ax in sr.permutation(axes):
            lo, hi = (x0, x1) if ax == 0 else (z0, z1)
            plo, phi = (z0, z1) if ax == 0 else (x0, x1)
            cands = sorted((-(min(hg, phi) - max(l, plo)), v) for (a, v, l, hg) in RL
                           if a == ax and lo + 0.9 < v < hi - 0.9 and min(hg, phi) - max(l, plo) > min(1.6, 0.45 * (phi - plo)))
            if cands:                               # a street runs along here: split the block on its centre line
                s, lane = cands[0][1], False
                break
            s = None
            for _ in range(40 if hi - lo > 2.4 else 0):
                q = sr.uniform(lo + 1.1, hi - 1.1)
                if all(abs(q - v) > HALF + 1.2 for (a, v, l, hg) in RL if a == ax and min(hg, phi) > max(l, plo) - 0.5):
                    s = q
                    break
            if s is not None:
                lane = depth <= 4 and phi - plo > 2.6 and sr.random() < 0.5
                break
        else:
            LEAVES.append((x0, z0, x1, z1, 0))
            return
        if s is None:
            LEAVES.append((x0, z0, x1, z1, 0))
            return
        lw = 0.22 if lane else 0.0
        if ax == 0:
            _split(x0, z0, s - lw, z1, depth + 1)
            if lane:
                LEAVES.append((s - lw, z0, s + lw, z1, 1))
            _split(s + lw, z0, x1, z1, depth + 1)
        else:
            _split(x0, z0, x1, s - lw, depth + 1)
            if lane:
                LEAVES.append((x0, s - lw, x1, s + lw, 1))
            _split(x0, s + lw, x1, z1, depth + 1)

    _split(G.X0, G.Z0, G.X0 + G.W, G.Z0 + G.H, 0)
    # the dock pools in the lake zones: rounded rectangles of water inside a ring of coping stones, all inside the zone
    lakes = [(bx, bz, br) for (bx, bz, br, kind) in BLOCKERS if kind == "lake"]
    pool_d = np.full(X.shape, 1e9)
    cope_u = np.zeros(X.shape)
    for k, (bx, bz, br) in enumerate(lakes):
        hw, hh = (0.84 * br, 0.74 * br) if k % 2 == 0 else (0.74 * br, 0.84 * br)
        POOLS.append((bx, bz, hw, hh, 0.36 * br))
        d_ = _rrect(bx, bz, hw, hh, 0.36 * br)
        side_x = np.abs(X - bx) / hw > np.abs(Z - bz) / hh          # (nearer a side that runs along z)
        cope_u = np.where(d_ < pool_d, np.where(side_x, Z, X), cope_u)
        pool_d = np.minimum(pool_d, d_)
    in_dock = lambda x0, z0, x1, z1: any(max(x0 - bx, 0, bx - x1) ** 2 + max(z0 - bz, 0, bz - z1) ** 2 < (br + 1.6) ** 2 for (bx, bz, br) in lakes)
    kinds = np.zeros(X.shape, np.int8)               # 0 flags, 1 cobbles, 2 cinder waste, 3 brick, 4 earth, 5 quay setts, 9 lane
    pid = np.zeros(X.shape, np.float32)
    lane_c = np.zeros(X.shape)
    for (x0, z0, x1, z1, is_lane) in LEAVES:
        j0, j1 = int(round((x0 - G.X0) * MPX)), int(round((x1 - G.X0) * MPX))
        i0, i1 = int(round((z0 - G.Z0) * MPX)), int(round((z1 - G.Z0) * MPX))
        if is_lane:
            kinds[i0:i1, j0:j1] = 9
            if x1 - x0 < z1 - z0:
                lane_c[i0:i1, j0:j1] = np.clip(1 - np.abs(X[i0:i1, j0:j1] - (x0 + x1) / 2) / 0.22, 0, 1)
            else:
                lane_c[i0:i1, j0:j1] = np.clip(1 - np.abs(Z[i0:i1, j0:j1] - (z0 + z1) / 2) / 0.22, 0, 1)
            continue
        kinds[i0:i1, j0:j1] = 5 if in_dock(x0, z0, x1, z1) else sr.choice([0, 1, 2, 3, 4], p=[0.27, 0.22, 0.2, 0.14, 0.17])
        pid[i0:i1, j0:j1] = sr.random()
    # walls: each leaf's left and top edges (every inner border is one of those), not along a lane's ends, broken off at
    # the pavements, the docks and here and there
    segs = []
    for (x0, z0, x1, z1, is_lane) in LEAVES:
        long_x = (x1 - x0) > (z1 - z0)
        if x0 > G.X0 + 0.01 and not (is_lane and long_x):
            segs.append(((x0, z0), (x0, z1)))
        if z0 > G.Z0 + 0.01 and not (is_lane and not long_x):
            segs.append(((x0, z0), (x1, z0)))
    lake_far = np.min([np.hypot(X - bx, Z - bz) - br for (bx, bz, br) in lakes], axis=0) if lakes else np.full(X.shape, 1e9)
    gap_n = fbm(0.6, 2, 431)
    for (a_, b_) in segs:
        L_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
        n_ = max(2, int(L_ / 0.05))
        run = []
        for t_ in np.linspace(0, 1, n_):
            x_, z_ = a_[0] + (b_[0] - a_[0]) * t_, a_[1] + (b_[1] - a_[1]) * t_
            ok_ = (_in_tex(x_, z_, 0.1) and _at(dist, x_, z_) > HALF + 0.56 and _at(lake_far, x_, z_) > 1.9 and _at(gap_n, x_, z_) > 0.3
                   and _at(kinds, x_ + 0.12, z_ + 0.12) != 5 and _at(kinds, x_ - 0.12, z_ - 0.12) != 5)      # (no walls on the quay)
            if ok_:
                run.append((x_, z_))
            elif len(run) > 3:
                WALLS.append(run)
                run = []
            else:
                run = []
        if len(run) > 3:
            WALLS.append(run)
    wall_d = g.poly_dist(WALLS, margin=0.5)[0] if WALLS else np.full(X.shape, 1e9)
    street = np.clip((HALF + 0.5 - dist) / 0.03, 0, 1)                     # carriageway and pavement
    pave = street * (1 - rd_hard)
    IND["kerb"] = np.clip(1 - np.abs(dist - HALF - 0.04) / 0.055, 0, 1)
    IND["pave"] = pave
    IND["gutter"] = rd_hard * np.clip(1 - np.abs(dist - (HALF - 0.1)) / 0.07, 0, 1)
    gph = np.abs((rc_al % 2.7) - 1.35)
    IND["grate"] = ((gph < 0.15) & (dist > HALF - 0.22) & (dist < HALF - 0.02)).astype(float)
    IND["lane"] = lane_c * (1 - street)
    lane_any = (kinds == 9) * (1 - street)
    for k_, nm in enumerate(("y_flags", "y_cobble", "y_waste", "y_brick", "y_earth", "y_quay")):
        IND[nm] = (kinds == k_) * (1 - street) * (1 - lane_any)
    IND["pid"] = pid
    IND["wall"] = np.clip((0.09 - wall_d) / 0.03, 0, 1)
    IND["water"] = np.clip(-(pool_d + 0.2) / 0.3, 0, 1)                # (0 at the coping's inner edge, 1 well out)
    IND["coping"] = np.clip(-pool_d / 0.2, 0, 1) * (pool_d > -0.2)     # (0 at its outer edge, 1 at the water)
    IND["cope_u"] = cope_u
    quay = np.clip(-(lake_far - 0.15) / 0.05, 0, 1) * (pool_d > 0)
    IND["y_quay"] = np.maximum(IND["y_quay"], quay * (1 - street))
    for k_ in ("y_flags", "y_cobble", "y_waste", "y_brick", "y_earth"):
        IND[k_] = IND[k_] * (1 - quay) * (pool_d > 0)
    # manhole covers: down the middle of the streets now and then, a few in the yards
    mh = np.zeros(X.shape)
    for lg in legs:
        P_ = np.asarray(lg, np.float64)
        cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P_, axis=0).T))])
        for s_ in np.arange(sr.uniform(1.5, 4.0), cum[-1] - 1.0, 6.3):
            cx_, cz_ = np.interp(s_, cum, P_[:, 0]), np.interp(s_, cum, P_[:, 1])
            if _in_tex(cx_, cz_, 1.0):
                MANHOLES.append((cx_ + sr.uniform(-0.25, 0.25), cz_ + sr.uniform(-0.25, 0.25), 0.15))
    for _ in range(14):
        x_, z_ = sr.uniform(-15, 15), sr.uniform(-8.5, 8.5)
        if _at(dist, x_, z_) > HALF + 0.8 and _at(BLK_ANY, x_, z_) > 0.4 and _at(wall_d, x_, z_) > 0.4:
            MANHOLES.append((x_, z_, 0.12))
    for (mx_, mz_, mr_) in MANHOLES:
        mh = np.maximum(mh, np.clip(1 - np.hypot(X - mx_, Z - mz_) / mr_, 0, 1))
    IND["manhole"] = mh
    IND["puddle"] = np.clip((pud_t(0.05) - puddle_n) / 0.02, 0, 1) * (pool_d > 0.05) * (1 - mh) * \
        np.clip(1 - IND["kerb"] * 2, 0, 1) * (rd_hard * np.clip(1 - np.abs(dist - HALF + 0.12) / 0.3, 0, 1) * 1.4 +
                                             (1 - street) * (IND["y_flags"] + IND["y_cobble"] + IND["y_earth"]) * 0.8)
    IND["puddle"] = np.clip(IND["puddle"], 0, 1)
    IND["soot"] = np.clip((fbm(0.8, 4, 432) - 0.5) / 0.15, 0, 1)
    log("smog: plots", len(LEAVES), "lanes", sum(l[4] for l in LEAVES), "wall runs", len(WALLS), "pools", len(POOLS),
        "manholes", len(MANHOLES))
# ------------------------------------------------------------------------------------------------ Modern Age features
# The Modern Age's grounds are paved and painted. Their areas (the runway, aprons and pads; sidewalks, plazas and lots;
# lawns, driveways and pools) are masks in IND like the Industrial themes'. Their painted markings are drawn with PIL at
# the render's own resolution into PAINT (white, yellow, red, and a dark channel for joints, tyre rubber and grates),
# supersampled, so a centre line, a zebra crossing or a runway number stays crisp. A road's lines follow its legs
# (smoothed through their points) and stop where another road joins or crosses it; a stretch of street that two legs
# (or two passes of one leg) share is painted once. ped: the signed distance to the edge of the paved carriageway (its
# inner corners filleted), < 0 on it; sidewalks, kerbs and verges are bands of it.
PAINT = None
LIGHTS = []                # military: edge lights (x, z, kind: 0 white, 1 blue, 2 green, 3 red)
SMALL_CR = []              # military: the small craters (x, z, radius) besides the crater blockers
HOUSES = []                # suburb: houses (x, z of the front's centre, the way it faces (radians, from +x toward +z))
POOLS_S = []               # suburb: each pool's water (x, z, half width, half height, corner radius)
ped = dist - HALF
GLYPH = {"0": [[(0, 0), (1, 0), (1, 2), (0, 2), (0, 0)]], "1": [[(0.2, 1.6), (0.55, 2), (0.55, 0)], [(0.1, 0), (1, 0)]],
         "2": [[(0, 2), (1, 2), (1, 1), (0, 1), (0, 0), (1, 0)]], "3": [[(0, 2), (1, 2), (1, 0), (0, 0)], [(0.25, 1), (1, 1)]],
         "4": [[(0, 2), (0, 0.8), (1, 0.8)], [(0.75, 1.5), (0.75, 0)]], "5": [[(1, 2), (0, 2), (0, 1), (1, 1), (1, 0), (0, 0)]],
         "6": [[(1, 2), (0, 2), (0, 0), (1, 0), (1, 1), (0, 1)]], "7": [[(0, 2), (1, 2), (0.35, 0)]],
         "8": [[(0, 0), (1, 0), (1, 2), (0, 2), (0, 0)], [(0, 1), (1, 1)]], "9": [[(1, 1), (0, 1), (0, 2), (1, 2), (1, 0), (0, 0)]],
         "S": [[(1, 2), (0, 2), (0, 1), (1, 1), (1, 0), (0, 0)]], "O": [[(0, 0), (1, 0), (1, 2), (0, 2), (0, 0)]],
         "T": [[(0, 2), (1, 2)], [(0.5, 2), (0.5, 0)]], "P": [[(0, 0), (0, 2), (1, 2), (1, 1), (0, 1)]],
         "H": [[(0, 0), (0, 2)], [(1, 0), (1, 2)], [(0, 1), (1, 1)]], "L": [[(0, 2), (0, 0), (1, 0)]],
         "A": [[(0, 0), (0, 2), (1, 2), (1, 0)], [(0, 1), (1, 1)]], "W": [[(0, 2), (0.15, 0), (0.5, 1.1), (0.85, 0), (1, 2)]],
         "X": [[(0, 0), (1, 2)], [(0, 2), (1, 0)]], "B": [[(0, 0), (0, 2), (0.8, 2), (0.8, 1), (0, 1)], [(0.8, 1), (1, 1), (1, 0), (0, 0)]],
         "U": [[(0, 2), (0, 0), (1, 0), (1, 2)]], "C": [[(1, 2), (0, 2), (0, 0), (1, 0)]], "E": [[(1, 2), (0, 2), (0, 0), (1, 0)], [(0, 1), (0.75, 1)]],
         "R": [[(0, 0), (0, 2), (1, 2), (1, 1), (0, 1), (1, 0)]], "Y": [[(0, 2), (0.5, 1), (1, 2)], [(0.5, 1), (0.5, 0)]],
         "N": [[(0, 0), (0, 2), (1, 0), (1, 2)]], "I": [[(0.5, 0), (0.5, 2)]], "K": [[(0, 0), (0, 2)], [(1, 2), (0, 1), (1, 0)]]}
if MOD_T or DIG_T:
    from PIL import Image as _PIm, ImageDraw as _PId
    from scipy.spatial import cKDTree
    from scipy.ndimage import gaussian_filter, distance_transform_edt

    class Painter:
        """Paint on the ground at the render's resolution (drawn at twice it, then averaged down): channels w (white),
        y (yellow), r (red), k (dark: joints, rubber, slots)."""
        CH = ("w", "y", "r", "k")

        def __init__(self, px, ss=2, ch=None):
            self.CH = tuple(ch or self.CH)
            self.s = float(px * ss)
            self.out = (int(round(G.W * px)), int(round(G.H * px)))
            self.im = {c: _PIm.new("L", (self.out[0] * ss, self.out[1] * ss), 0) for c in self.CH}
            self.dr = {c: _PId.Draw(self.im[c]) for c in self.CH}

        def P(self, x, z):
            return ((x - G.X0) * self.s, (z - G.Z0) * self.s)

        def poly(self, ch, pts, v=255):
            self.dr[ch].polygon([self.P(x, z) for x, z in pts], fill=v)

        def disc(self, ch, x, z, r, v=255):
            (a, b), (c, d) = self.P(x - r, z - r), self.P(x + r, z + r)
            self.dr[ch].ellipse([a, b, c, d], fill=v)

        def ring(self, ch, x, z, r, w, v=255):
            (a, b), (c, d) = self.P(x - r - w / 2, z - r - w / 2), self.P(x + r + w / 2, z + r + w / 2)
            self.dr[ch].ellipse([a, b, c, d], outline=v, width=max(1, int(round(w * self.s))))

        def rect(self, ch, cx, cz, L, W, ang=0.0, v=255):
            """A rectangle L long (along ang, radians from +x toward +z) and W wide, centred on (cx, cz)."""
            u, n = (math.cos(ang), math.sin(ang)), (-math.sin(ang), math.cos(ang))
            self.poly(ch, [(cx + u[0] * a * L / 2 + n[0] * b * W / 2, cz + u[1] * a * L / 2 + n[1] * b * W / 2)
                           for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))], v)

        def seg(self, ch, a, b, w, v=255):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L > 1e-6:
                self.rect(ch, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, L, w, math.atan2(b[1] - a[1], b[0] - a[0]), v)

        def line(self, ch, pts, w, v=255):
            pts = [tuple(p) for p in np.asarray(pts, np.float64)]
            for a, b in zip(pts[:-1], pts[1:]):
                self.seg(ch, a, b, w, v)
            for p in pts[1:-1]:
                self.disc(ch, p[0], p[1], w / 2, v)

        def dashed(self, ch, pts, w, dash, gap, v=255):
            P = np.asarray(pts, np.float64)
            cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
            s = 0.0
            while s < cum[-1]:
                t = np.arange(s, min(s + dash, cum[-1]) + 1e-9, 0.03)
                if len(t) >= 2:
                    self.line(ch, np.stack([np.interp(t, cum, P[:, 0]), np.interp(t, cum, P[:, 1])], 1), w, v)
                s += dash + gap

        def text(self, ch, s, cx, cz, h, ang, w=None, gap=0.35, v=255):
            """Block letters h tall, their up pointing along ang (so they read from that way round), centred on (cx, cz)."""
            U, R = (math.cos(ang), math.sin(ang)), (-math.sin(ang), math.cos(ang))
            w = w or h * 0.12
            cw = h * 0.52
            tot = len(s) * cw + (len(s) - 1) * gap * cw
            for i, ch_ in enumerate(s):
                x0 = -tot / 2 + i * cw * (1 + gap)
                for stroke in GLYPH.get(ch_, []):
                    pts = []
                    for gx, gy in stroke:
                        a_ = x0 + w / 2 + gx * (cw - w)
                        b_ = -h / 2 + w / 2 + gy / 2 * (h - w)
                        pts.append((cx + R[0] * a_ + U[0] * b_, cz + R[1] * a_ + U[1] * b_))
                    self.line(ch, pts, w, v)
                    for p in (pts[0], pts[-1]):
                        self.disc(ch, p[0], p[1], w / 2, v)

        def arrays(self):
            return {c: np.asarray(self.im[c].resize(self.out, _PIm.BOX), np.float32) / 255.0 for c in self.CH}

    PAINT = Painter(PX if not PREVIEW else 16, ch=("w", "y", "r", "k", "c", "m", "g", "hz") if DIG_T else None)

    def _smp(arr, x, z):
        """Bilinear lookup of a mask at world (x, z) (as sample() further down)."""
        fx = np.clip((np.asarray(x) - G.X0) * MPX - 0.5, 0, g.w - 1.001)
        fz = np.clip((np.asarray(z) - G.Z0) * MPX - 0.5, 0, g.h - 1.001)
        i0, j0 = fz.astype(int), fx.astype(int)
        tz, tx = fz - i0, fx - j0
        return (arr[i0, j0] * (1 - tx) + arr[i0, j0 + 1] * tx) * (1 - tz) + (arr[i0 + 1, j0] * (1 - tx) + arr[i0 + 1, j0 + 1] * tx) * tz

    def _res(P, step=0.03):
        P = np.asarray(P, np.float64)
        cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        s_ = np.arange(0.0, cum[-1] + 1e-9, step)
        Q = np.stack([np.interp(s_, cum, P[:, 0]), np.interp(s_, cum, P[:, 1])], 1)
        T = np.gradient(Q, axis=0)
        T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
        return Q, T, s_

    RS = [_res(_round(lg)) for lg in legs]
    _aP = np.vstack([r[0] for r in RS])
    _aT = np.vstack([r[1] for r in RS])
    _aL = np.concatenate([np.full(len(r[0]), i) for i, r in enumerate(RS)])
    _aS = np.concatenate([r[2] for r in RS])
    _tree = cKDTree(_aP)

    def _on_other(Q, T, li, S_, r):
        """True where a point of a line drawn along leg li lies on another road that joins or crosses it (not one
        running along it), within r of that road's centre line."""
        out = np.zeros(len(Q), bool)
        for i, nb_ in enumerate(_tree.query_ball_point(Q, r)):
            if nb_:
                nb_ = np.asarray(nb_)
                far = (_aL[nb_] != li) | (np.abs(_aS[nb_] - S_[i]) > 3.0)
                if DIG_T:                        # (another path's copy of this same stretch is not a road joining it)
                    far &= _own[li].query(_aP[nb_])[0] > 0.1
                out[i] = bool(np.any(far & (np.abs(_aT[nb_] @ T[i]) < 0.8)))
        return out

    def _dup(P, T, li, S_):
        out = np.zeros(len(P), bool)
        for i, nb_ in enumerate(_tree.query_ball_point(P, 0.12)):
            if nb_:
                nb_ = np.asarray(nb_)
                earlier = (_aL[nb_] < li) | ((_aL[nb_] == li) & (_aS[nb_] < S_[i] - 3.0))
                out[i] = bool(np.any(earlier & (np.abs(_aT[nb_] @ T[i]) > 0.9)))
        return out

    DUP = [_dup(P, T, li, S_) for li, (P, T, S_) in enumerate(RS)]
    _own = [cKDTree(P) for (P, T, S_) in RS]

    def _runs(k):
        idx = np.flatnonzero(np.diff(np.concatenate([[0], k.astype(np.int8), [0]])))
        return list(zip(idx[::2], idx[1::2]))

    def road_line(ch, off, w, dash=0.0, gap=0.0, skip=None, r=HALF - 0.03, v=255):
        """A line along every road, off to the side of its centre line (+ = left of the way it runs)."""
        for li, (P, T, S_) in enumerate(RS):
            Q = P + np.stack([-T[:, 1], T[:, 0]], 1) * off
            k = ~DUP[li] & ~_on_other(Q, T, li, S_, r)
            if skip is not None:
                k &= ~skip(Q[:, 0], Q[:, 1])
            if DIG_T and abs(off) > 0.3:         # (an edge line stays at its distance from the road's edge: none cut
                k &= _smp(ped, Q[:, 0], Q[:, 1]) > abs(off) - HALF - 0.16    # across where the road kinks sharply)
            if dash > 0:
                k &= (S_ % (dash + gap)) < dash
            for a, b in _runs(k):
                if b - a >= 2:
                    PAINT.line(ch, Q[a:b], w, v)

    def road_ticks(ch, off0, off1, step, w, skip=None, v=255, r=HALF + 0.6):
        """Short strokes across each road's side from off0 to off1 out from its centre line, every step along it (the
        joints between a sidewalk's slabs), both sides."""
        for li, (P, T, S_) in enumerate(RS):
            Nn = np.stack([-T[:, 1], T[:, 0]], 1)
            k = ~DUP[li] & (np.abs((S_ + step / 2) % step - step / 2) < 0.016)
            for sg in (-1, 1):
                A_, B_ = P + Nn * off0 * sg, P + Nn * off1 * sg
                kk = k & ~_on_other((A_ + B_) / 2, T, li, S_, r)
                if skip is not None:
                    kk &= ~skip(A_[:, 0], A_[:, 1]) & ~skip(B_[:, 0], B_[:, 1])
                for i in np.flatnonzero(kk):
                    PAINT.seg(ch, A_[i], B_[i], w, v)

    def zebra(cx, cz, ang, L=0.5, bar=0.1, gap=0.1, half=HALF - 0.1, ch="w"):
        """A zebra crossing at (cx, cz) across a road heading ang: bars along the road, spaced across it."""
        n_ = (-math.sin(ang), math.cos(ang))
        k = -half + bar / 2
        while k <= half - bar / 2 + 1e-6:
            PAINT.rect(ch, cx + n_[0] * k, cz + n_[1] * k, L, bar, ang)
            k += bar + gap

    def stop_bar(cx, cz, ang, side, w=0.07, ch="w"):
        """A stop line across one lane (side +1: the right of ang as seen from above, the lane a car heading ang drives
    in; -1: the other) of a road heading ang."""
        n_ = (-math.sin(ang), math.cos(ang))
        PAINT.rect(ch, cx + n_[0] * side * HALF / 2, cz + n_[1] * side * HALF / 2, w, HALF - 0.08, ang)

    def _fillet(mask, rad):
        """Round a paved area's inner corners (where two streets meet) without moving its straight edges."""
        return np.maximum(mask, np.clip((gaussian_filter(mask.astype(np.float32), rad * MPX) - 0.5) / 0.12 + 0.5, 0, 1))

    def _sdist(mask):
        """Signed distance (world units) to the edge of a mask's area, < 0 inside."""
        m_ = mask > 0.5
        return (distance_transform_edt(~m_) - distance_transform_edt(m_)) / MPX

    def _box(cx, cz, hw, hh, ang, rc=0.0):
        """Signed distance to a rotated rounded rectangle (hw along ang)."""
        ca, sa = math.cos(ang), math.sin(ang)
        u, v_ = (X - cx) * ca + (Z - cz) * sa, -(X - cx) * sa + (Z - cz) * ca
        qx, qz = np.abs(u) - (hw - rc), np.abs(v_) - (hh - rc)
        return np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - rc

    def _arc(cx, cz, R, a0, a1, n=20):
        return [(cx + R * math.cos(a), cz + R * math.sin(a)) for a in np.linspace(a0, a1, n)]

    def _scorch(cx, cz, r_, d_, rng):
        """Scorch round a crater: dark over its rim, burnt out past it in a ragged star of blast rays."""
        ang = np.arctan2(Z - cz, X - cx)
        ph0 = rng.uniform(0, 2 * math.pi)
        rays = 0.5 + 0.5 * np.sin(ang * int(rng.integers(7, 12)) + ph0 + np.sin(ang * 3 + ph0) * 0.9)
        reach = r_ * (1.45 + 1.0 * rays ** 2)
        return np.clip((reach - d_) / (reach - r_ * 0.9), 0, 1) ** 0.8 * (0.45 + 0.55 * np.clip((d_ - r_ * 0.35) / (r_ * 0.5), 0, 1))

    road_c = road = _fillet(rd_hard, 0.42) if THEME != "military" else rd_hard
    ped = _sdist(road)
    on_road = np.clip((0.06 - ped) / 0.06, 0, 1)
    tbl = np.zeros(X.shape)
    if zf["slow"]:          # (the slow stretches, square-ended, the whole road's width there: the intersection too)
        _sd, _sal, _ssd = g.poly_dist(zf["slow"], signed=True)
        tbl = road * ((_sd < HALF + 0.6) & ((_sd - np.abs(_ssd)) < 0.02))
    bus = road * np.clip(lane * 2, 0, 1)
    pr_ = np.random.default_rng(97)

if DIG_T:
    # The Digital Age's crisp shapes are fields at the render's own resolution (HD: signed distances and coordinates
    # that the material turns into edges, so a kerb, a pad's rim or a hex tile's seam stays sharp): the road's signed
    # distance (its inner corners filleted like the Modern streets'), the slow and fast stretches, and a gate plate at
    # each rift end (the game stands its rift ring over it: 0 where the robots go in, violet; 1 where they come out, cyan).
    from scipy.ndimage import map_coordinates
    HPX = PX if not PREVIEW else 16
    gH = G.Grid(HPX)
    HX, HZ = gH.X.astype(np.float32), gH.Z.astype(np.float32)
    HD = {}

    def _hsd(mask):
        """Signed distance (world units, < 0 inside) to the edge of a hi-res mask's area, exact to the half pixel."""
        m_ = mask > 0.5
        a_, b_ = distance_transform_edt(~m_), distance_transform_edt(m_)
        return (np.where(m_, 0.5 - b_, a_ - 0.5) / HPX).astype(np.float32)

    def _down(a):
        """A hi-res field sampled at the mask grid's pixel centres (bilinear)."""
        return map_coordinates(a, [(Z - G.Z0) * HPX - 0.5, (X - G.X0) * HPX - 0.5], order=1, mode="nearest").astype(np.float64)

    def _rr_h(cx, cz, hw, hh, rc=0.0):
        """Signed distance to a rounded rectangle on the hi-res grid."""
        qx, qz = np.abs(HX - cx) - (hw - rc), np.abs(HZ - cz) - (hh - rc)
        return np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - rc

    _dh = gH.poly_dist(legs, margin=2.0)[0]
    _rh = np.clip((HALF - _dh) * HPX + 0.5, 0, 1).astype(np.float32)
    del _dh
    _rh = np.maximum(_rh, np.clip((gaussian_filter(_rh, 0.42 * HPX) - 0.5) / 0.12 + 0.5, 0, 1))
    HD["ped"] = np.clip(_hsd(_rh), -2.0, 4.0)
    del _rh
    ped = _down(HD["ped"])                                             # (the coarse masks follow the crisp road)
    road = road_c = np.clip(0.5 - ped * MPX, 0, 1)
    on_road = np.clip((0.06 - ped) / 0.06, 0, 1)

    def _zone_h(zl):
        """A slow or fast stretch on the hi-res grid: the road's whole width there, square-ended."""
        if not zl:
            return np.zeros(HX.shape, np.float32)
        sd_, _a, ssd_ = gH.poly_dist(zl, margin=1.5, signed=True)
        if not DC_T:
            return ((sd_ < HALF + 0.7) & ((sd_ - np.abs(ssd_)) < 0.005) & (HD["ped"] < 0)).astype(np.float32)
        m_ = (sd_ < HALF + 0.7) & (HD["ped"] < 0)          # (cut square only at each stretch's two ends: a curving
        for P_ in zl:                                        # stretch keeps the outside of its bends)
            P_ = np.asarray(P_, np.float64)
            for e_, f_ in ((P_[0], P_[1]), (P_[-1], P_[-2])):
                t_ = (f_ - e_) / max(np.hypot(*(f_ - e_)), 1e-9)
                m_ &= ~((((HX - e_[0]) * t_[0] + (HZ - e_[1]) * t_[1]) < 0) & (np.hypot(HX - e_[0], HZ - e_[1]) < HALF + 0.8))
        return m_.astype(np.float32)

    HD["sl"] = _zone_h(zf["slow"])
    HD["fl"] = _zone_h(zf["fast"])
    tbl, bus = _down(HD["sl"]), _down(HD["fl"])
    GATES = []                                                         # (x, z, the road's heading there, 0 in / 1 out)
    for sp in specs:
        P_ = sp["pts"]
        for i in sp.get("rift", []):
            for (x_, z_), (ax_, az_), k_ in ((P_[i - 1], P_[max(0, i - 2)], 0), (P_[i], P_[min(len(P_) - 1, i + 1)], 1)):
                if any(math.hypot(x_ - a_, z_ - b_) < 0.2 for a_, b_, _h, _k in GATES):
                    continue
                hd_ = math.atan2(z_ - az_, x_ - ax_) if k_ == 0 else math.atan2(az_ - z_, ax_ - x_)
                GATES.append((float(x_), float(z_), hd_, k_))
    gt_r = np.full(HX.shape, 9.0, np.float32)
    gt_k = np.zeros(HX.shape, np.float32)
    for (x_, z_, _h, k_) in GATES:
        d_ = np.hypot(HX - x_, HZ - z_) / 0.86
        gt_k = np.where(d_ < gt_r, float(k_), gt_k)
        gt_r = np.minimum(gt_r, d_)
    HD["gt_r"], HD["gt_k"] = gt_r, gt_k
    gate_m = np.clip((1.0 - _down(gt_r)) * 20, 0, 1)
    _tl = []                                                           # (the game's tunnel ramps: keep walkways and tags off)
    for sp in specs:
        cum = G.spec_cum(sp)
        for z_ in sp.get("zones", []):
            if z_["k"] == "tunnel":
                _tl += G.sub_polylines(sp, cum[z_["a"]] - 0.9, cum[z_["b"]] + 0.9)
    tun_m = (g.poly_dist(_tl, margin=2.0)[0] < HALF + 0.7).astype(float) if _tl else np.zeros(X.shape)
    LANDMARKS = []                                                     # (what, x, z, size): spots left for the kits
    log("digital: gates", [(round(a_, 2), round(b_, 2), k_) for a_, b_, _h, k_ in GATES])

if THEME == "military":
    # an airbase: a runway between the service roads (09/27, thresholds, numbers, touchdown and aiming-point bars, rubber
    # in the touchdown zones, edge lights), taxiways (yellow centre lines, edge lines, hold-short bars where they leave
    # the runway, blue edge lights), an apron of concrete slabs with parking stands, concrete pads under the machines
    # and the crates, a helipad, a hangar hardstand; grass between; craters blasted in, scorched round
    RWZ, RWH, RX0, RX1 = -4.0, 1.05, -14.3, 7.0
    TXZ = -0.05                                      # the apron's taxi lane
    rwy = ((np.abs(Z - RWZ) < RWH) & (X > RX0) & (X < RX1)).astype(float)
    blast = ((np.abs(Z - RWZ) < RWH) & (X > RX0 - 1.3) & (X <= RX0)).astype(float)
    TW = []                                          # taxiways: (centre line, half width, edge lines and lights)
    for x0 in (-4.5, 4.0):                           # turn-offs south across the service road to the apron
        TW.append(([(x0 - 2.4, RWZ)] + _arc(x0 - 1.2, RWZ + 1.2, 1.2, -math.pi / 2, 0) + [(x0, TXZ)], 0.48, False))
    T3 = [(-12.3, RWZ)] + _arc(-12.5, RWZ + 1.2, 1.2, -math.pi / 2, -math.pi) + [(-13.7, 3.2)]
    TW.append((T3, 0.48, True))                      # from the runway's west end down to the west machine's pad
    T4 = [(-12.9, 4.9)] + _arc(-12.1, 5.2, 0.8, math.pi, math.pi / 2) + [(4.2, 6.0)]
    TW.append((T4, 0.42, True))                      # from that pad east between the two roads
    twy = np.zeros(X.shape)
    for pts, hw_, _e in TW:
        d_, _a = g.poly_dist([pts], margin=1.0)
        twy = np.maximum(twy, np.clip((hw_ - d_) / 0.02, 0, 1))
    apron = np.clip(-_rrect(0.7, 1.5, 7.65, 1.95, 0.5) / 0.02, 0, 1)
    pads = np.zeros(X.shape)
    haz = np.zeros(X.shape)
    PADS = []
    for (bx, bz, br, kind) in BLOCKERS:
        if kind == "machine":
            h_ = br + 0.2
            PADS.append((bx, bz, h_))
            dp = _rrect(bx, bz, h_, h_, 0.12)
            pads = np.maximum(pads, np.clip(-dp / 0.02, 0, 1))
            haz = np.maximum(haz, ((dp < -0.06) & (dp > -0.22)).astype(float))
        elif kind == "crates":
            pads = np.maximum(pads, np.clip(-_rrect(bx, bz, br + 0.15, br + 0.15, 0.12) / 0.02, 0, 1))
    HELI = (12.4, -7.35)
    heli = np.clip(-_rrect(HELI[0], HELI[1], 0.95, 0.95, 0.1) / 0.02, 0, 1)
    hard = np.clip(-_rrect(13.2, 9.3, 5.8, 3.65, 0.4) / 0.02, 0, 1)
    conc = np.clip(np.maximum.reduce([apron, twy, pads, heli, hard]) * (1 - rd_hard) * (1 - rwy) * (1 - blast), 0, 1)
    IND["conc"] = conc
    IND["rwy"] = rwy * (1 - rd_hard)
    IND["blast"] = blast * (1 - rd_hard)
    IND["haz"] = haz
    # craters: the crater blockers, deep with raised rims, and smaller ones off the roads and pavements
    for (bx, bz, br, kind) in BLOCKERS:
        if kind != "crater":
            continue
        r_ = br * 0.82
        d_ = np.hypot(X - bx, Z - bz) + (fbm(0.6, 2, int(abs(bx * 7 + bz * 13)) % 997 + 500) - 0.5) * 0.35
        crater = np.maximum(crater, np.clip(1 - (d_ / r_) ** 2, 0, 1))
        crater_rim = np.maximum(crater_rim, np.exp(-((d_ - r_ * 1.02) / (0.2 * r_)) ** 2))
        gp_d = np.maximum(gp_d, _scorch(bx, bz, r_, d_, pr_))
    paved = np.maximum.reduce([conc, rwy, blast])
    paved_b = gaussian_filter(paved, 0.3 * MPX)
    for _ in range(800):
        if len(SMALL_CR) >= 5:
            break
        cx, cz = pr_.uniform(-14.5, 14.5), pr_.uniform(-8.2, 8.2)
        r_ = pr_.uniform(0.3, 0.5)
        if (_at(dist, cx, cz) < HALF + r_ + 0.4 or _at(BLK_ANY, cx, cz) < r_ + 0.6 or _at(crater, cx, cz) > 0
                or any(math.hypot(cx - a_, cz - b_) < 4.0 for a_, b_, _r in SMALL_CR)
                or _at(np.maximum(pads, heli), cx, cz) > 0 or _at(_rrect(HELI[0], HELI[1], 1.6, 1.6, 0.2), cx, cz) < 0):
            continue
        if _at(paved_b, cx, cz) > 0.02:
            continue                                 # (in the turf)
        SMALL_CR.append((cx, cz, r_))
        d_ = np.hypot(X - cx, Z - cz) + (fbm(0.3, 2, 600 + len(SMALL_CR)) - 0.5) * 0.45 * r_
        crater = np.maximum(crater, np.clip(1 - (d_ / r_) ** 2, 0, 1))
        crater_rim = np.maximum(crater_rim, np.exp(-((d_ - r_) / (0.25 * r_)) ** 2))
        gp_d = np.maximum(gp_d, _scorch(cx, cz, r_, d_, pr_) * 0.85)
    gp_d *= 1 - rd_hard
    IND["crater"], IND["rim"], IND["scorch"] = crater * (1 - rd_hard), crater_rim * (1 - rd_hard), gp_d
    # oil and fuel stains on the concrete: under the parked aircraft, and here and there
    oil = np.clip((fbm(0.5, 3, 471) - 0.74) / 0.04, 0, 1) * 0.5
    STANDS = (-5.2, -2.6, 3.0, 5.8)
    for sx in STANDS:
        for _ in range(3):
            ox, oz = sx + pr_.normal(0, 0.35), 1.9 + pr_.normal(0, 0.3)
            oil = np.maximum(oil, np.clip((pr_.uniform(0.12, 0.26) - np.hypot((X - ox) * 1.0, (Z - oz) * 1.4) +
                                           (fbm(0.15, 2, 472) - 0.5) * 0.12) / 0.06, 0, 1) * pr_.uniform(0.6, 0.9))
    IND["oil"] = oil * conc
    IND["mow"] = 0.5 + 0.5 * np.sin(Z * 2 * math.pi / 1.3 + (fbm(2.0, 2, 473) - 0.5) * 1.2)
    # paint: the runway
    for sg in (-1, 1):
        PAINT.rect("w", (RX0 + RX1) / 2, RWZ + sg * (RWH - 0.08), RX1 - RX0 - 0.1, 0.06)
    for xe, dr_ in ((RX0, 1), (RX1, -1)):
        PAINT.rect("w", xe + dr_ * 0.06, RWZ, 0.06, 2 * RWH - 0.2, 0.0)                         # threshold bar
        for k in range(4):                                                                     # piano keys
            for sg in (-1, 1):
                PAINT.rect("w", xe + dr_ * 0.68, RWZ + sg * (0.16 + k * 0.215), 1.0, 0.11)
        PAINT.text("w", "09" if dr_ > 0 else "27", xe + dr_ * 1.95, RWZ, 0.95, 0.0 if dr_ > 0 else math.pi, gap=0.45)
        for dd_, nbar, L_, W_, off0 in ((3.1, 3, 0.55, 0.07, 0.3), (4.5, 1, 1.15, 0.2, 0.5), (5.9, 2, 0.55, 0.07, 0.3), (7.0, 1, 0.55, 0.07, 0.3)):
            for k in range(nbar):
                for sg in (-1, 1):
                    PAINT.rect("w", xe + dr_ * (dd_ + L_ / 2), RWZ + sg * (off0 + k * 0.12), L_, W_)
        for _ in range(140):                                                                   # rubber where they land
            x_ = xe + dr_ * pr_.uniform(2.4, 7.8)
            z_ = RWZ + pr_.choice([-1, 1]) * pr_.uniform(0.12, 0.42) + pr_.normal(0, 0.05)
            PAINT.rect("k", x_, z_, pr_.uniform(0.3, 1.3), pr_.uniform(0.012, 0.045), pr_.normal(0, 0.012), int(pr_.uniform(50, 130)))
    PAINT.dashed("w", [(RX0 + 2.7, RWZ), (RX1 - 2.7, RWZ)], 0.07, 0.75, 0.5)                 # centre line
    for xa in (RX0 - 1.22, RX0 - 0.82, RX0 - 0.42):                                          # the blast pad's chevrons
        PAINT.line("y", [(xa, RWZ - 0.95), (xa + 0.38, RWZ), (xa, RWZ + 0.95)], 0.08)
    # taxiways: centre lines, double edge lines (not where they meet other paving), hold-short bars
    other = np.maximum.reduce([rwy, blast, apron, pads, heli, hard, rd_hard])
    other = np.clip(gaussian_filter(other, 0.06 * MPX) * 2, 0, 1)
    for pts, hw_, edges in TW:
        Q, T, S_ = _res(pts, 0.03)
        PAINT.line("y", Q, 0.05)
        if edges:
            Nn = np.stack([-T[:, 1], T[:, 0]], 1)
            for sg in (-1, 1):
                for off in (hw_ - 0.05, hw_ - 0.11):
                    E_ = Q + Nn * off * sg
                    k = _smp(other, E_[:, 0], E_[:, 1]) < 0.3
                    for a, b in _runs(k):
                        if b - a >= 2:
                            PAINT.line("y", E_[a:b], 0.025)
                E_ = Q + Nn * (hw_ + 0.08) * sg
                for i in range(0, len(Q), 33):
                    if _smp(other, E_[i, 0], E_[i, 1]) < 0.3 and _smp(dist, E_[i, 0], E_[i, 1]) > HALF + 0.12:
                        LIGHTS.append((E_[i, 0], E_[i, 1], 1))
    for x0 in (-4.5, 4.0):                            # hold-short: solid on the taxiway's side, dashed on the runway's
        for zz_, dsh in ((-2.73, True), (-2.66, True), (-2.55, False), (-2.48, False)):
            if dsh:
                for k in range(4):
                    PAINT.rect("y", x0 - 0.36 + k * 0.24, zz_, 0.13, 0.025)
            else:
                PAINT.rect("y", x0, zz_, 0.9, 0.025)
    # the apron: a taxi lane, four stands (lead-in lines, stop bars, numbers, red safety lines)
    PAINT.line("y", [(-6.6, TXZ), (8.0, TXZ)], 0.05)
    for k, sx in enumerate(STANDS):
        PAINT.line("y", [(sx, TXZ), (sx, 2.85)], 0.05)
        PAINT.rect("y", sx, 2.88, 0.08, 0.5, 0.0)
        PAINT.text("y", str(k + 1), sx, 3.2, 0.32, -math.pi / 2)
        for a_, b_ in (((sx - 1.15, 0.75), (sx - 1.15, 3.35)), ((sx + 1.15, 0.75), (sx + 1.15, 3.35)), ((sx - 1.15, 3.35), (sx + 1.15, 3.35))):
            PAINT.dashed("r", [a_, b_], 0.03, 0.22, 0.14)
    # the crates' pad: a yellow outline and pallet bays; the helipad: a white ring and an H, a yellow border
    for (bx, bz, br, kind) in BLOCKERS:
        if kind == "crates":
            h_ = br + 0.03
            PAINT.line("y", [(bx - h_, bz - h_), (bx + h_, bz - h_), (bx + h_, bz + h_), (bx - h_, bz + h_), (bx - h_, bz - h_)], 0.05)
            for k in range(1, 4):
                PAINT.line("y", [(bx - h_ + k * h_ / 2, bz - h_), (bx - h_ + k * h_ / 2, bz + h_)], 0.025)
    PAINT.line("y", [(7.8, 6.45), (19.0, 6.45)], 0.05)                        # the hardstand: a taxi lane, three stands
    for sx in (9.6, 12.2, 14.8):
        PAINT.line("y", [(sx, 6.45), (sx, 8.6)], 0.05)
        PAINT.rect("y", sx, 8.62, 0.08, 0.5, 0.0)
        for a_, b_ in (((sx - 1.2, 7.0), (sx - 1.2, 9.4)), ((sx + 1.2, 7.0), (sx + 1.2, 9.4))):
            PAINT.dashed("r", [a_, b_], 0.03, 0.22, 0.14)
    PAINT.ring("w", HELI[0], HELI[1], 0.66, 0.06)
    PAINT.text("w", "H", HELI[0], HELI[1], 0.72, -math.pi / 2, w=0.1)
    hh_ = 0.87
    PAINT.line("y", [(HELI[0] - hh_, HELI[1] - hh_), (HELI[0] + hh_, HELI[1] - hh_), (HELI[0] + hh_, HELI[1] + hh_),
                     (HELI[0] - hh_, HELI[1] + hh_), (HELI[0] - hh_, HELI[1] - hh_)], 0.04)
    # the roads: white edge lines, a yellow dashed centre line (not on the speed lane: its arrows are painted there);
    # stop lines where the turn-offs cross the service road
    road_line("w", HALF - 0.1, 0.04)
    road_line("w", -(HALF - 0.1), 0.04)
    road_line("y", 0.0, 0.045, 0.5, 0.45, skip=lambda x, z: _smp(bus, x, z) > 0.5)
    for x0 in (-4.5, 4.0):
        stop_bar(x0 + 0.78, -1.5, math.pi, 1)
        stop_bar(x0 - 0.78, -1.5, 0.0, 1)
    # edge lights: white along the runway, green across its west threshold, red across its east end
    for x_ in np.arange(RX0 + 0.2, RX1 - 0.1, 1.2):
        for sg in (-1, 1):
            LIGHTS.append((x_, RWZ + sg * (RWH + 0.1), 0))
    for z_ in np.arange(RWZ - 0.95, RWZ + 0.96, 0.27):
        LIGHTS.append((RX0 - 0.1, z_, 2))
        LIGHTS.append((RX1 + 0.1, z_, 3))
    log("military: lights", len(LIGHTS), "small craters", len(SMALL_CR), "concrete px", int((conc > 0.5).sum()))

if THEME == "metro":
    # a city centre: asphalt avenues (double yellow centre lines, red bus lanes on the speed lanes, a raised table of
    # brick pavers over the crossroads where the slow stretches are), zebra crossings with stop lines, granite kerbs,
    # concrete sidewalks with tree pits, storm drains and manholes; the blocks cut into lots (granite tiles, concrete
    # slabs, brick pavers, parking with white bays, a lawn with planted beds, slate), a plaza where avenue B ends,
    # polished plinths under the buildings, small parks with planted beds round the trees
    SW = 0.5
    sidewalk = ((ped >= 0) & (ped < SW)).astype(float)
    BLOCKS = [(-21, -13, 2.65, -3.35), (5.35, -13, 19, -3.35), (10.35, -3.35, 19, 4.65), (-12.35, -0.65, -1.2, 4.65),
              (-21, -0.65, -12.35, 13), (-12.35, 7.35, 19, 13)]
    PLAZA = (-1.2, -0.65, 7.65, 4.65)
    LOTS = []

    def _cut(x0, z0, x1, z1, depth=0):
        w, h = x1 - x0, z1 - z0
        if max(w, h) < 3.4 or (max(w, h) < 5.0 and depth > 0 and mr_.random() < 0.35):
            LOTS.append((x0, z0, x1, z1))
            return
        ax = 0 if w >= h else 1
        lo, hi = (x0, x1) if ax == 0 else (z0, z1)
        for _try in range(30):                   # (not through a blocker zone: a building's plinth, a park)
            s = lo + (hi - lo) * mr_.uniform(0.34, 0.66)
            if all(abs(s - (bx if ax == 0 else bz)) > br + 0.35 for (bx, bz, br, k_) in BLOCKERS
                   if x0 - br < bx < x1 + br and z0 - br < bz < z1 + br):
                break
        else:
            LOTS.append((x0, z0, x1, z1))
            return
        if ax == 0:
            _cut(x0, z0, s, z1, depth + 1)
            _cut(s, z0, x1, z1, depth + 1)
        else:
            _cut(x0, z0, x1, s, depth + 1)
            _cut(x0, s, x1, z1, depth + 1)

    mr_ = np.random.default_rng(89)
    for bl_ in BLOCKS:
        _cut(*bl_)
    # each lot one surface: 0 granite tiles, 1 concrete slabs, 2 brick pavers, 3 parking, 4 lawn and beds, 5 slate
    lk = np.full(X.shape, -1, np.int8)
    pid = np.zeros(X.shape, np.float32)
    lot_e = np.full(X.shape, 9.0)
    kinds_ = []
    for i, (x0, z0, x1, z1) in enumerate(LOTS):
        has = [k_ for (bx, bz, br, k_) in BLOCKERS if x0 - 0.3 < bx < x1 + 0.3 and z0 - 0.3 < bz < z1 + 0.3]
        if "trees" in has:
            kd = 4
        elif "building" in has:
            kd = int(mr_.choice([0, 5]))
        else:
            kd = int(mr_.choice([0, 1, 2, 3, 4, 5], p=[0.24, 0.22, 0.16, 0.18, 0.1, 0.1]))
            if kd == 3 and min(x1 - x0, z1 - z0) < 2.3:
                kd = 1
        kinds_.append(kd)
        sel = (X >= x0) & (X < x1) & (Z >= z0) & (Z < z1)
        lk[sel] = kd
        pid[sel] = mr_.uniform(0.0, 0.42) + (0.58 if mr_.random() < 0.5 else 0.0)   # (clear of the swap at 0.5)
        lot_e[sel] = np.minimum.reduce([X[sel] - x0, x1 - X[sel], Z[sel] - z0, z1 - Z[sel]])
    plaza = np.clip(-_rrect((PLAZA[0] + PLAZA[2]) / 2, (PLAZA[1] + PLAZA[3]) / 2, (PLAZA[2] - PLAZA[0]) / 2,
                             (PLAZA[3] - PLAZA[1]) / 2, 0.3) / 0.02, 0, 1)
    block = np.clip((ped - SW) / 0.02, 0, 1)
    IND["plaza"] = plaza * block
    nonpl = block * (1 - plaza)
    for k_, nm in enumerate(("l_tile", "l_conc", "l_brick", "l_lot", "l_lawn", "l_slate")):
        IND[nm] = (lk == k_) * nonpl
    IND["pid"] = pid
    IND["lotb"] = np.clip(1 - np.abs(lot_e - 0.04) / 0.045, 0, 1) * nonpl * (lot_e < 8)
    for (bx, bz, br, kind) in BLOCKERS:                  # (no lot border across a building's plinth or a park)
        IND["lotb"] *= np.clip((np.hypot(X - bx, Z - bz) - br - 0.1) / 0.05, 0, 1)
    # plinths under the buildings; parks round the trees: a lawn, planted beds edged with low granite kerbs, a path
    plinth = np.zeros(X.shape)
    beds = np.zeros(X.shape)
    for (bx, bz, br, kind) in BLOCKERS:
        if kind == "building":
            plinth = np.maximum(plinth, np.clip(-_rrect(bx, bz, br * 0.97, br * 0.97, 0.18) / 0.02, 0, 1))
        if kind == "trees":
            beds = np.maximum(beds, np.clip((br * 0.9 + (fbm(0.5, 2, 481) - 0.5) * 0.4 - np.hypot(X - bx, Z - bz)) / 0.03, 0, 1))
    lpath = np.zeros(X.shape)
    for i, (x0, z0, x1, z1) in enumerate(LOTS):          # the lawn lots: a bed along one side, islands, a path across
        if kinds_[i] != 4:
            continue
        sd_ = int(mr_.integers(0, 4))
        bx0, bz0, bx1, bz1 = x0 + 0.18, z0 + 0.18, x1 - 0.18, z1 - 0.18
        if sd_ == 0:
            bx1 = bx0 + 0.42
        elif sd_ == 1:
            bx0 = bx1 - 0.42
        elif sd_ == 2:
            bz1 = bz0 + 0.42
        else:
            bz0 = bz1 - 0.42
        beds = np.maximum(beds, np.clip(-_rrect((bx0 + bx1) / 2, (bz0 + bz1) / 2, (bx1 - bx0) / 2, (bz1 - bz0) / 2, 0.15) / 0.02, 0, 1))
        hb = [(bx, bz, br) for (bx, bz, br, k_) in BLOCKERS if k_ == "trees" and x0 < bx < x1 and z0 < bz < z1]
        for _k in range(0 if (hb or min(x1 - x0, z1 - z0) < 2.0) else int(mr_.integers(1, 3))):
            cx_, cz_ = mr_.uniform(x0 + 0.9, x1 - 0.9), mr_.uniform(z0 + 0.9, z1 - 0.9)
            rr_ = mr_.uniform(0.22, 0.4)
            beds = np.maximum(beds, np.clip((rr_ * (1 + 0.15 * np.sin(np.arctan2(Z - cz_, X - cx_) * 5 + _k)) - np.hypot((X - cx_) / 1.3, Z - cz_)) / 0.03, 0, 1))
        if (x1 - x0) > 2.2 and (z1 - z0) > 2.2:          # a path of pavers right across, the long way
            if (x1 - x0) >= (z1 - z0):
                zp = mr_.uniform(z0 + 0.8, z1 - 0.8)
                pts_ = [(x0, zp), (x1, zp + mr_.uniform(-0.5, 0.5))]
            else:
                xp = mr_.uniform(x0 + 0.8, x1 - 0.8)
                pts_ = [(xp, z0), (xp + mr_.uniform(-0.5, 0.5), z1)]
            d_, _a = g.poly_dist([pts_], margin=0.5)
            lpath = np.maximum(lpath, np.clip((0.15 - d_) / 0.02, 0, 1) * (X >= x0) * (X < x1) * (Z >= z0) * (Z < z1))
    for (bx, bz, br, kind) in BLOCKERS:
        lpath *= np.clip((np.hypot(X - bx, Z - bz) - br - 0.1) / 0.05, 0, 1)
    beds *= nonpl * (1 - plinth) * (1 - lpath)
    IND["plinth"] = plinth * block
    IND["lpath"] = lpath * nonpl
    IND["beds"] = beds
    IND["bedk"] = np.clip(1 - np.abs(_sdist(beds) - 0.02) / 0.035, 0, 1) * block            # their granite edging
    # the plaza: big pale stone slabs with dark granite bands, a round inlaid motif, two raised planters
    PLM = (0.9, 2.0, 1.05)
    dm = np.hypot(X - PLM[0], Z - PLM[1])
    IND["pl_r"] = np.where(dm < PLM[2] * 1.18, np.clip(dm / PLM[2], 0, 1.2) / 1.2, 1.0)      # (1 outside it)
    IND["pl_a"] = (np.arctan2(Z - PLM[1], X - PLM[0]) / (2 * math.pi) + 0.5)
    planter = np.zeros(X.shape)
    for (px_, pz_) in ((6.3, 0.75), (6.3, 3.55), (-0.2, 4.05)):
        planter = np.maximum(planter, np.clip(-_rrect(px_, pz_, 0.55, 0.32, 0.08) / 0.12, 0, 1))      # (0 at its rim's edge)
    IND["planter"] = planter * IND["plaza"]
    # sidewalks, kerbs, the slow table and the bus lanes, drains, tree pits, manholes
    IND["side"] = sidewalk
    IND["kerb"] = np.clip(1 - np.abs(ped - 0.035) / 0.04, 0, 1)
    IND["tbl"] = tbl
    IND["bus"] = bus * (1 - tbl)
    pits = np.zeros(X.shape)
    PITS = []
    for li, (P, T, S_) in enumerate(RS):
        for s_ in np.arange(1.2, S_[-1] - 0.6, 2.6):
            i = int(s_ / 0.03)
            if i >= len(P) or DUP[li][i]:
                continue
            for sg in (-1, 1):
                q = P[i] + np.array([-T[i, 1], T[i, 0]]) * (HALF + 0.29) * sg
                if (_at(ped, q[0], q[1]) < 0.18 or _at(ped, q[0], q[1]) > 0.42 or not _in_tex(q[0], q[1], 0.5)
                        or _at(tbl, q[0], q[1]) > 0 or _at(plaza, q[0], q[1]) > 0.5):
                    continue
                if any(math.hypot(q[0] - a_, q[1] - b_) < 1.6 for a_, b_, _ in PITS):
                    continue
                PITS.append((q[0], q[1], math.atan2(T[i, 1], T[i, 0])))
    for (qx, qz, a_) in PITS:
        pits = np.maximum(pits, (_box(qx, qz, 0.15, 0.15, a_) < 0).astype(float))
    IND["pit"] = pits
    mh = np.zeros(X.shape)
    for li, (P, T, S_) in enumerate(RS):
        for s_ in np.arange(mr_.uniform(1.0, 3.0), S_[-1] - 0.5, 5.7):
            i = int(s_ / 0.03)
            if i < len(P) and not DUP[li][i] and _in_tex(P[i, 0], P[i, 1], 1.0):
                q = P[i] + np.array([-T[i, 1], T[i, 0]]) * mr_.choice([-0.32, 0.32])
                mh = np.maximum(mh, np.clip(1 - np.hypot(X - q[0], Z - q[1]) / 0.14, 0, 1))
    IND["mh"] = mh * (1 - tbl)
    # paint: double yellow centre lines (none on the bus lanes or the brick table), zebra crossings and stop lines,
    # storm drains' slots, sidewalk joints, the parking bays
    nolines = lambda x, z: (_smp(bus, x, z) > 0.5) | (_smp(tbl, x, z) > 0.5)
    road_line("y", 0.045, 0.035, skip=nolines)
    road_line("y", -0.045, 0.035, skip=nolines)
    road_ticks("k", HALF + 0.07, HALF + SW - 0.02, 0.5, 0.018, v=150, skip=lambda x, z: _smp(plaza, x, z) > 0.5)
    road_line("k", HALF + 0.075, 0.016, v=120)
    road_line("k", -(HALF + 0.075), 0.016, v=120)
    XW = [(2.3, -2.0, 0.0), (5.7, -2.0, 0.0), (4.0, -3.7, math.pi / 2), (4.0, -0.3, math.pi / 2), (-9.0, -2.0, 0.0),
          (-4.0, 6.0, 0.0), (7.55, 6.0, 0.0), (11.3, 6.0, 0.0), (9.0, 3.65, math.pi / 2), (4.0, -7.2, math.pi / 2), (2.2, 6.0, 0.0)]
    for (cx, cz, a_) in XW:
        zebra(cx, cz, a_)
        if _at(tbl, cx, cz) < 0.5:              # (stop lines before the crossings out on the avenues, both ways)
            for sg in (-1, 1):
                stop_bar(cx - math.cos(a_) * sg * 0.45, cz - math.sin(a_) * sg * 0.45, a_ if sg > 0 else a_ + math.pi, 1)
    for li, (P, T, S_) in enumerate(RS):       # storm drains in the gutters: a grate of slots by the kerb
        for s_ in np.arange(2.0, S_[-1] - 0.5, 3.9):
            i = int(s_ / 0.03)
            if i >= len(P) or DUP[li][i]:
                continue
            for sg in (-1, 1):
                q = P[i] + np.array([-T[i, 1], T[i, 0]]) * (HALF - 0.08) * sg
                if _at(ped, q[0], q[1]) > -0.03 or _at(ped, q[0], q[1]) < -0.2 or _at(tbl, q[0], q[1]) > 0 or not _in_tex(q[0], q[1], 0.5):
                    continue
                a_ = math.atan2(T[i, 1], T[i, 0])
                PAINT.rect("k", q[0], q[1], 0.3, 0.12, a_, 200)
                for k in range(5):
                    PAINT.rect("w", q[0] + math.cos(a_) * (k - 2) * 0.055, q[1] + math.sin(a_) * (k - 2) * 0.055, 0.02, 0.09, a_ + 0.0, 60)
    for i, (x0, z0, x1, z1) in enumerate(LOTS):  # parking: bays along both long sides of an aisle
        if kinds_[i] != 3:
            continue
        x0, z0, x1, z1 = x0 + 0.2, z0 + 0.2, x1 - 0.2, z1 - 0.2
        along_x = (x1 - x0) >= (z1 - z0)
        a0, a1, b0, b1 = (x0, x1, z0, z1) if along_x else (z0, z1, x0, x1)
        rows = [(b0, 1), (b1, -1)] if b1 - b0 > 2.5 else [(b0, 1)]
        for b_, sg in rows:
            for k in range(int((a1 - a0) / 0.55) + 1):
                a_ = a0 + k * 0.55
                p0, p1 = (a_, b_), (a_, b_ + sg * 0.95)
                PAINT.seg("w", p0 if along_x else p0[::-1], p1 if along_x else p1[::-1], 0.035, 200)
            q0, q1 = (a0, b_ + sg * 0.95), (a0 + int((a1 - a0) / 0.55) * 0.55, b_ + sg * 0.95)
            PAINT.seg("w", q0 if along_x else q0[::-1], q1 if along_x else q1[::-1], 0.035, 200)
    oil = np.clip((fbm(0.4, 3, 482) - 0.62) / 0.06, 0, 1) * IND["l_lot"]
    IND["oil"] = oil
    IND["grime"] = np.clip((fbm(0.9, 4, 483) - 0.45) / 0.25, 0, 1)
    log("metro: lots", len(LOTS), "by kind", np.bincount(kinds_, minlength=6).tolist(), "pits", len(PITS), "crossings", len(XW))

if THEME == "suburb":
    # an American suburb: curving asphalt streets with a yellow dashed centre line, concrete kerbs, a grass verge and a
    # concrete sidewalk each side; cul-de-sacs; houses' lots of lawn mown in stripes, each with a concrete driveway to
    # the street, a garden path to the sidewalk and flower beds along its front; a park in the loop with a playground,
    # a sandpit and paths; the lake zones are backyard pools (turquoise water inside a tiled coping, a pool deck)
    CUL = [([(4.0, -2.0), (7.6, -2.0)], (7.8, -2.0, 1.05)), ([(11.0, 1.8), (14.0, 1.8)], (14.2, 1.8, 1.05))]
    cul = np.zeros(X.shape)
    for stem, (bx, bz, R) in CUL:
        sd_, _a = g.poly_dist([stem], margin=1.5)
        cul = np.maximum(cul, np.clip((0.62 - sd_) / 0.02, 0, 1))
        cul = np.maximum(cul, np.clip((R - np.hypot(X - bx, Z - bz)) / 0.02, 0, 1))
    pav = _fillet(np.maximum(road, cul), 0.42)
    cul = np.clip(pav - road, 0, 1)
    ped = _sdist(pav)
    on_road = np.clip((0.06 - ped) / 0.06, 0, 1)
    HS = [(x_, -6.35, math.pi / 2) for x_ in (-13.4, -10.2, -7.0, -3.8, -0.6, 2.4)]
    HS += [(5.52, -6.14, math.atan2(4.0, -3.3)),                                  # (the building zone: faces the bend)
           (6.0, -3.7, math.pi / 2), (7.8, -4.1, math.pi / 2), (7.8, 0.15, -math.pi / 2),    # round the first cul-de-sac
           (13.0, 0.2, math.pi / 2), (14.7, -0.1, math.pi / 2), (14.7, 3.7, -math.pi / 2),   # round the second
           (12.75, 4.9, math.pi), (12.6, 6.4, math.pi),
           (-2.75, 7.9, 0.0), (2.0, 7.75, -math.pi / 2), (5.2, 7.75, -math.pi / 2), (8.4, 7.75, -math.pi / 2),
           (-12.65, 1.1, 0.0), (-12.2, -1.7, 0.0), (-8.3, 5.0, -math.pi / 2), (-5.4, 5.0, -math.pi / 2),
           (10.9, -4.6, math.pi / 2)]
    drive = np.zeros(X.shape)
    patio = np.zeros(X.shape)
    veg = np.zeros(X.shape)
    gpath = np.zeros(X.shape)
    fbed = np.zeros(X.shape)
    lot_a = np.full(X.shape, 0.35)
    lot_id = np.zeros(X.shape, np.int16)
    best = np.full(X.shape, 1e9)
    for hi_, (fx, fz, fa) in enumerate(HS):
        f_, p_ = np.array([math.cos(fa), math.sin(fa)]), np.array([-math.sin(fa), math.cos(fa)])
        side = 1 if hi_ % 2 == 0 else -1
        gx, gz = np.array([fx, fz]) + p_ * 0.38 * side
        end = None
        for t_ in np.arange(0.1, 5.0, 0.04):
            q = np.array([gx, gz]) + f_ * t_
            if _at(ped, q[0], q[1]) < -0.15:
                end = q
                break
        HOUSES.append((fx, fz, fa))
        if end is not None:
            d_, _a = g.poly_dist([[(gx, gz), tuple(end)]], margin=0.6)
            drive = np.maximum(drive, np.clip((0.22 - d_) / 0.02, 0, 1))
        dx_, dz_ = np.array([fx, fz]) - p_ * 0.28 * side
        end = None
        for t_ in np.arange(0.1, 4.0, 0.04):
            q = np.array([dx_, dz_]) + f_ * t_
            if _at(ped, q[0], q[1]) < 0.45:
                end = q
                break
        if end is not None:
            d_, _a = g.poly_dist([[(dx_, dz_), tuple(end)]], margin=0.4)
            gpath = np.maximum(gpath, np.clip((0.08 - d_) / 0.02, 0, 1))
        fbed = np.maximum(fbed, np.clip(-_box(fx + f_[0] * 0.17, fz + f_[1] * 0.17, 0.7, 0.13, fa + math.pi / 2, 0.06) / 0.02, 0, 1))
        bk = np.array([fx, fz]) - f_ * 1.62                                      # a patio behind the house
        if all(math.hypot(bk[0] - bx, bk[1] - bz) > br + 0.95 for (bx, bz, br, k_) in BLOCKERS):
            patio = np.maximum(patio, np.clip(-_box(bk[0] + p_[0] * 0.2 * side, bk[1] + p_[1] * 0.2 * side, 0.42, 0.26, fa + math.pi / 2, 0.03) / 0.02, 0, 1))
        if hi_ % 3 == 1:                                                         # and now and then a vegetable bed
            vb = bk - p_ * 0.55 * side - f_ * 0.2
            veg = np.maximum(veg, np.clip(-_box(vb[0], vb[1], 0.3, 0.17, fa, 0.02) / 0.02, 0, 1))
        dh = np.hypot(X - (fx - f_[0] * 0.6), Z - (fz - f_[1] * 0.6))
        closer = dh < best
        best = np.where(closer, dh, best)
        lot_a = np.where(closer & (dh < 3.6), fa, lot_a)
        lot_id = np.where(closer, hi_, lot_id)
    # the pools: water in a rounded rectangle, a coping of tiles round it, a pool deck round that
    pool_d = np.full(X.shape, 1e9)
    deck_d = np.full(X.shape, 1e9)
    pdepth = np.zeros(X.shape)
    for k, (bx, bz, br, kind) in enumerate([b_ for b_ in BLOCKERS if b_[3] == "lake"]):
        hw, hh = (1.02, 0.62) if k % 2 == 0 else (0.62, 1.02)
        POOLS_S.append((bx, bz, hw, hh, 0.3))
        d_ = _rrect(bx, bz, hw, hh, 0.3)
        pool_d = np.minimum(pool_d, d_)
        deck_d = np.minimum(deck_d, _rrect(bx, bz, hw + 0.48, hh + 0.48, 0.22))
        u_ = ((X - bx) / hw) if hw > hh else ((Z - bz) / hh)                   # -1 shallow end .. 1 deep end
        pdepth = np.where(d_ < 0.1, np.clip(0.5 + 0.5 * u_, 0, 1), pdepth)
    IND["water"] = np.clip(-(pool_d + 0.07) / 0.02, 0, 1)
    IND["wline"] = np.clip(1 + (pool_d + 0.07) / 0.07, 0, 1) * IND["water"]               # (1 at the water's edge)
    IND["coping"] = np.clip(-pool_d / 0.02, 0, 1) * (1 - IND["water"])
    patio *= np.clip((BLK_ANY - 0.1) / 0.05, 0, 1)
    IND["deck"] = np.maximum(np.clip(-deck_d / 0.02, 0, 1) * (pool_d > 0), patio * (ped > 0.55))
    IND["veg"] = veg * (ped > 0.55) * (1 - IND["deck"])
    IND["pdepth"] = pdepth
    # the park in the loop: a ring path with paths out to the sidewalks, a playground in the middle, a sandpit, beds
    PK = (-6.5, -0.5)
    dk = np.hypot(X - PK[0], Z - PK[1])
    ppath = np.clip((0.11 - np.abs(dk - 1.45)) / 0.02, 0, 1)
    for a_ in (0, math.pi / 2, math.pi, -math.pi / 2):
        d_, _a = g.poly_dist([[(PK[0] + math.cos(a_) * 1.45, PK[1] + math.sin(a_) * 1.45), (PK[0] + math.cos(a_) * 3.0, PK[1] + math.sin(a_) * 3.0)]], margin=0.5)
        ppath = np.maximum(ppath, np.clip((0.11 - d_) / 0.02, 0, 1))
    play = np.clip((1.12 - dk) / 0.02, 0, 1)
    IND["play"] = play
    IND["pk_r"] = np.clip(dk / 1.12, 0, 1)
    IND["playb"] = np.clip(1 - np.abs(dk - 1.15) / 0.05, 0, 1)                   # its timber edging
    sand = np.clip(-_rrect(-8.05, 1.05, 0.42, 0.34, 0.1) / 0.02, 0, 1)
    IND["sand"] = sand
    fbed = np.maximum(fbed, np.clip((0.36 - np.hypot(X + 4.95, Z + 2.05)) / 0.02, 0, 1))
    fbed = np.maximum(fbed, np.clip(-_rrect(-8.05, -2.0, 0.42, 0.25, 0.1) / 0.02, 0, 1))
    for (bx, bz, br, kind) in BLOCKERS:              # mulch under the trees zone; a bed round the building zone's house
        if kind == "trees":
            fbed = np.maximum(fbed, np.clip((br * 0.62 + (fbm(0.4, 2, 491) - 0.5) * 0.3 - np.hypot(X - bx, Z - bz)) / 0.03, 0, 1))
    sw_ = ((ped >= 0.2) & (ped < 0.5)).astype(float)
    hard_ = np.maximum.reduce([drive, gpath * (1 - sw_), IND["deck"], IND["coping"], IND["water"]])
    IND["drive"] = drive * (ped > 0.0)
    IND["gpath"] = np.maximum(gpath, ppath) * (ped > 0.5) * (1 - drive)
    IND["side"] = sw_ * (1 - drive)
    IND["kerb"] = np.clip(1 - np.abs(ped - 0.03) / 0.035, 0, 1)
    IND["cul"] = cul
    IND["fbed"] = fbed * (ped > 0.55) * (1 - hard_) * (1 - IND["gpath"]) * (1 - play) * (1 - sand)
    hard_ = np.maximum(hard_, IND["deck"])
    lawn = (ped > 0.06) * (1 - IND["side"]) * (1 - hard_) * (1 - IND["gpath"]) * (1 - IND["fbed"]) * (1 - play) * (1 - sand) * (1 - IND["veg"])
    IND["lawn"] = lawn
    IND["mca"], IND["msa"] = 0.5 + 0.5 * np.cos(lot_a), 0.5 + 0.5 * np.sin(lot_a)      # (the shader draws the stripes)
    IND["lshade"] = np.where(best < 3.6, (np.sin(lot_id * 12.9898) * 43758.5453) % 1.0, 0.5)
    IND["bus"] = bus
    # paint: a yellow dashed centre line (not on the speed lane), stop lines and STOP at the cul-de-sacs' mouths, two
    # zebra crossings by the park, sidewalk joints
    road_line("y", 0.0, 0.045, 0.5, 0.4, skip=lambda x, z: _smp(bus, x, z) > 0.5)
    road_ticks("k", HALF + 0.21, HALF + 0.49, 0.32, 0.016, v=140, skip=lambda x, z: (_smp(drive, x, z) > 0.5) | (_smp(cul, x, z) > 0.3))
    for stem, (bx, bz, R) in CUL:
        a_ = math.atan2(stem[1][1] - stem[0][1], stem[1][0] - stem[0][0])
        mx, mz = stem[0][0] + math.cos(a_) * (HALF + 0.3), stem[0][1] + math.sin(a_) * (HALF + 0.3)
        hx_, hz_ = math.sin(a_) * 0.31, -math.cos(a_) * 0.31          # (the right of a car heading out: a_ + pi)
        PAINT.rect("w", mx + hx_, mz + hz_, 0.08, 0.56, a_)
        PAINT.text("w", "STOP", mx + hx_ + math.cos(a_) * 0.55, mz + hz_ + math.sin(a_) * 0.55, 0.3, a_ + math.pi, w=0.035, gap=0.25)
        L_ = math.hypot(stem[1][0] - stem[0][0], stem[1][1] - stem[0][1])      # the cul-de-sac's sidewalk joints
        n_ = (-math.sin(a_), math.cos(a_))
        for s_ in np.arange(HALF + 0.6, L_, 0.32):
            for sg in (-1, 1):
                q0 = (stem[0][0] + math.cos(a_) * s_ + n_[0] * sg * 0.83, stem[0][1] + math.sin(a_) * s_ + n_[1] * sg * 0.83)
                q1 = (q0[0] + n_[0] * sg * 0.28, q0[1] + n_[1] * sg * 0.28)
                if _at(drive, q0[0], q0[1]) < 0.5 and _at(drive, q1[0], q1[1]) < 0.5 and _at(ped, q0[0], q0[1]) > 0.1:
                    PAINT.seg("k", q0, q1, 0.016, 140)
        for th in np.arange(0, 2 * math.pi, 0.32 / (R + 0.35)):
            q0 = (bx + math.cos(th) * (R + 0.21), bz + math.sin(th) * (R + 0.21))
            q1 = (bx + math.cos(th) * (R + 0.49), bz + math.sin(th) * (R + 0.49))
            if _at(drive, q0[0], q0[1]) < 0.5 and _at(ped, q0[0], q0[1]) > 0.1 and _at(ped, q1[0], q1[1]) < 0.55:
                PAINT.seg("k", q0, q1, 0.016, 140)
    for cx in (PK[0],):
        zebra(cx, -4.0, 0.0, L=0.45)
        zebra(cx, 3.0, 0.0, L=0.45)
    log("suburb: houses", len(HOUSES), "pools", len(POOLS_S), "drive px", int((drive > 0.5).sum()))
if THEME == "lab":
    # a cleanroom hall: its floor cut into bays on the 0.6 tile grid (white epoxy, anti-static tile, raised floor with
    # vent panels, blue ESD epoxy) between painted yellow safety lines; green walkways across it, crossing the tracks on
    # zebras between yellow bollards; floor grates, covered cable trenches from the machines and the tanks; marked
    # equipment bays (for the kit's racks and partitions); steel plinths under the machines; drain pads ringed with frost
    # under the tanks; the robots' lanes dark service tracks (a steel edge, a hazard-striped border, white lane lines, a
    # yellow guide line with fiducial tags), decontamination grilles across the slow stretches
    lr_ = np.random.default_rng(131)
    TL = 0.6
    BAYS, CUTS = [], []

    def _cutb(x0, z0, x1, z1, depth=0):
        w, h = x1 - x0, z1 - z0
        if max(w, h) < 4.3 or (max(w, h) < 7.5 and depth > 1 and lr_.random() < 0.4):
            BAYS.append((x0, z0, x1, z1))
            return
        ax = 0 if w >= h else 1
        lo, hi = (x0, x1) if ax == 0 else (z0, z1)
        for _try in range(40):
            s = round((lo + (hi - lo) * lr_.uniform(0.3, 0.7)) / TL) * TL
            if all(abs(s - (bx if ax == 0 else bz)) > br + 0.5 for (bx, bz, br, k_) in BLOCKERS
                   if x0 - br < bx < x1 + br and z0 - br < bz < z1 + br):
                break
        else:
            BAYS.append((x0, z0, x1, z1))
            return
        if ax == 0:
            CUTS.append([(s, z0), (s, z1)])
            _cutb(x0, z0, s, z1, depth + 1)
            _cutb(s, z0, x1, z1, depth + 1)
        else:
            CUTS.append([(x0, s), (x1, s)])
            _cutb(x0, z0, x1, s, depth + 1)
            _cutb(x0, s, x1, z1, depth + 1)

    _cutb(-21.0, -13.2, 19.2, 13.2)
    bk = np.zeros(X.shape, np.int8)
    bid = np.zeros(X.shape, np.float32)
    for (x0, z0, x1, z1) in BAYS:
        sel = (X >= x0) & (X < x1) & (Z >= z0) & (Z < z1)
        bk[sel] = lr_.choice([0, 1, 2, 3], p=[0.34, 0.3, 0.2, 0.16])
        bid[sel] = lr_.random()
    for k_, nm in ((1, "b_tile"), (2, "b_raised"), (3, "b_esd")):
        IND[nm] = (bk == k_).astype(float)
    IND["bid"] = bid
    # machine plinths (square steel plinths, a hazard border), the tanks' drain pads (round), the equipment bays
    PLIN = [(bx, bz, br + 0.2) for (bx, bz, br, k_) in BLOCKERS if k_ == "machine"]
    TANK = [(bx, bz, br * 0.92) for (bx, bz, br, k_) in BLOCKERS if k_ == "tank"]
    pl_d = np.full(HX.shape, 9.0, np.float32)
    for (bx, bz, h_) in PLIN:
        pl_d = np.minimum(pl_d, _rr_h(bx, bz, h_, h_, 0.1))
    HD["pl_d"] = pl_d
    tk_r = np.full(HX.shape, 9.0, np.float32)
    tk_a = np.zeros(HX.shape, np.float32)
    for (bx, bz, R) in TANK:
        d_ = np.hypot(HX - bx, HZ - bz) / R
        tk_a = np.where(d_ < tk_r, np.arctan2(HZ - bz, HX - bx) / (2 * math.pi) + 0.5, tk_a)
        tk_r = np.minimum(tk_r, d_)
    HD["tk_r"], HD["tk_a"] = tk_r, tk_a
    tkm = np.full(X.shape, 9.0)
    for (bx, bz, R) in TANK:
        tkm = np.minimum(tkm, np.hypot(X - bx, Z - bz) - R)
    EQ_C = [(-4.8, -5.4, 1.8, 1.2), (-11.4, 6.6, 1.8, 1.2), (12.6, 4.8, 1.2, 1.8), (7.5, 1.8, 0.9, 1.8), (2.4, 2.4, 1.2, 1.2)]
    EQ = []
    for (cx, cz, hw, hh) in EQ_C:
        sub = (np.abs(X - cx) < hw) & (np.abs(Z - cz) < hh)
        sub2 = (np.abs(X - cx) < hw + 0.3) & (np.abs(Z - cz) < hh + 0.3)
        if ped[sub].min() > 0.35 and BLK_ANY[sub2].min() > 0.2:
            EQ.append((cx, cz, hw, hh))
            LANDMARKS.append(("equipment bay", cx, cz, "%.1f x %.1f" % (2 * hw, 2 * hh)))
        else:
            log("lab: equipment bay too close to a road or a zone, dropped", (cx, cz))
    eq_d = np.full(HX.shape, 9.0, np.float32)
    for (cx, cz, hw, hh) in EQ:
        eq_d = np.minimum(eq_d, _rr_h(cx, cz, hw, hh, 0.04))
    HD["eq_d"] = eq_d
    eqm = np.full(X.shape, 9.0)
    for (cx, cz, hw, hh) in EQ:
        eqm = np.minimum(eqm, _rrect(cx, cz, hw, hh, 0.04))
    for (bx, bz, h_) in PLIN:
        LANDMARKS.append(("machine plinth", bx, bz, "%.2f square" % (2 * h_)))
    for (bx, bz, R) in TANK:
        LANDMARKS.append(("tank drain pad", bx, bz, "r %.2f" % R))
    # walkways: straight lanes 0.72 wide along the tile grid, as long as the floor allows, clear of the machines, the
    # tanks and the equipment bays; they cross the tracks (never run along one) on zebras
    keep = np.minimum.reduce([BLK_ANY, eqm, tkm])
    WALKS = []
    cands = []
    for ax in (0, 1):
        vals = np.arange(-6.6, 6.61, TL) if ax == 0 else np.arange(-13.2, 13.21, TL)
        for v in vals:
            t_ = np.arange(-16.5, 16.5, 0.05) if ax == 0 else np.arange(-10.0, 10.0, 0.05)
            ok = np.ones(len(t_), bool)
            onr = np.zeros(len(t_), bool)
            for off in (-0.42, 0.0, 0.42):
                xs_, zs_ = (t_, np.full(len(t_), v + off)) if ax == 0 else (np.full(len(t_), v + off), t_)
                ok &= (_smp(keep, xs_, zs_) > 0.45) & (_smp(tun_m, xs_, zs_) < 0.5)
                onr |= _smp(ped, xs_, zs_) < 0.3
            for a, b in _runs(ok):
                L_ = (b - a) * 0.05
                if L_ < 6.0:
                    continue
                o_ = onr[a:b]
                stretch = max([(e_ - s_) * 0.05 for s_, e_ in _runs(o_)] + [0.0])
                if o_.mean() > 0.3 or stretch > 2.9:
                    continue
                cands.append((L_ - 4.0 * o_.mean(), ax, round(v, 2), t_[a], t_[b - 1]))
    cands.sort(key=lambda c_: -c_[0])
    for sc_, ax, v, lo, hi in cands:
        if sum(1 for w_ in WALKS if w_[0] == ax) >= 2:
            continue
        if any(w_[0] == ax and abs(w_[1] - v) < 4.0 for w_ in WALKS):
            continue
        WALKS.append((ax, v, lo, hi))
    BOLL = []                                                          # yellow bollards where the walkways meet a track
    XINGS = []
    wk_d = np.full(X.shape, 9.0)
    for (ax, v, lo, hi) in WALKS:
        t_ = np.arange(lo, hi, 0.03)
        xs_, zs_ = (t_, np.full(len(t_), v)) if ax == 0 else (np.full(len(t_), v), t_)
        pmin = np.minimum.reduce([_smp(ped, xs_ + (0 if ax == 0 else o_), zs_ + (o_ if ax == 0 else 0)) for o_ in (-0.4, 0.0, 0.4)])
        off = pmin > 0.17
        ang = 0.0 if ax == 0 else math.pi / 2
        for a, b in _runs(off):
            if b - a < 6:
                continue
            p0, p1 = (xs_[a], zs_[a]), (xs_[b - 1], zs_[b - 1])
            PAINT.seg("g", p0, p1, 0.72)
            n_ = (-math.sin(ang), math.cos(ang))
            for sg in (-1, 1):
                PAINT.seg("w", (p0[0] + n_[0] * 0.33 * sg, p0[1] + n_[1] * 0.33 * sg), (p1[0] + n_[0] * 0.33 * sg, p1[1] + n_[1] * 0.33 * sg), 0.035)
            for (q_, at_) in ((p0, a), (p1, b - 1)):
                if 0 < at_ < len(t_) - 1:                              # (an end at a track, not at the floor's edge)
                    for sg in (-1, 1):
                        BOLL.append((q_[0] + n_[0] * 0.46 * sg, q_[1] + n_[1] * 0.46 * sg))
        d_, _a = g.poly_dist([[(xs_[0], zs_[0]), (xs_[-1], zs_[-1])]], margin=1.0)
        wk_d = np.minimum(wk_d, d_ - 0.36)
        cen = _smp(ped, xs_, zs_) < 0.0
        for a, b in _runs(cen):
            if b - a < 10:
                continue
            m_ = (a + b) // 2
            XINGS.append((xs_[m_], zs_[m_], ang + math.pi / 2))
    for (cx, cz, ra) in XINGS:
        zebra(cx, cz, ra, L=0.62, bar=0.1, gap=0.1, half=HALF - 0.14)
    BOLL = [p_ for p_ in BOLL if _at(ped, p_[0], p_[1]) > 0.2]
    # cable trenches: from the sides of each machine's plinth and from each tank pad straight out across the floor until
    # a track, a zone or the hall's edge (the longest two per machine, one per tank)
    TRN = []                                                           # (axis, centre line, lo, hi)

    def _trench_from(x_, z_, dx, dz, start_free):
        pts_, t = [], 0.0
        while t < 14.0:
            px_, pz_ = x_ + dx * t, z_ + dz * t
            if not (-16.0 < px_ < 16.0 and -9.6 < pz_ < 9.6):
                break
            q = [(px_ - dz * o_, pz_ + dx * o_) for o_ in (-0.2, 0.2)]
            if any(_at(ped, a_, b_) < 0.35 for a_, b_ in q):
                break
            if t > start_free and (any(_at(BLK_ANY, a_, b_) < 0.15 for a_, b_ in q) or _at(eqm, px_, pz_) < 0.2
                                   or _at(tkm, px_, pz_) < 0.2):
                break
            pts_.append((px_, pz_))
            t += 0.05
        return pts_

    for (bx, bz, h_) in PLIN:
        runs_ = []
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v_ = round((bz if dx else bx) / 0.3) * 0.3
            sx_, sz_ = (bx + dx * (h_ - 0.05), v_) if dx else (v_, bz + dz * (h_ - 0.05))
            p_ = _trench_from(sx_, sz_, dx, dz, 0.6)
            if len(p_) * 0.05 > 2.2:
                runs_.append((len(p_), p_))
        for _n, p_ in sorted(runs_, key=lambda r: -r[0])[:2]:
            TRN.append(p_)
    for (bx, bz, R) in TANK:
        runs_ = []
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sx_, sz_ = bx + dx * (R - 0.05), bz + dz * (R - 0.05)
            p_ = _trench_from(sx_, sz_, dx, dz, 0.6)
            if len(p_) * 0.05 > 2.0:
                runs_.append((len(p_), p_))
        for _n, p_ in sorted(runs_, key=lambda r: -r[0])[:1]:
            TRN.append(p_)
    tr_d = np.full(HX.shape, 9.0, np.float32)
    tr_u = np.zeros(HX.shape, np.float32)
    trm = np.full(X.shape, 9.0)
    for p_ in TRN:
        (x0, z0), (x1, z1) = p_[0], p_[-1]
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        along_x = abs(x1 - x0) > abs(z1 - z0)
        hw, hh = (abs(x1 - x0) / 2, 0.18) if along_x else (0.18, abs(z1 - z0) / 2)
        d_ = _rr_h(cx, cz, hw, hh, 0.0)
        tr_u = np.where(d_ < tr_d, HX if along_x else HZ, tr_u)
        tr_d = np.minimum(tr_d, d_)
        trm = np.minimum(trm, _rrect(cx, cz, hw, hh, 0.0))
    HD["tr_d"], HD["tr_u"] = tr_d, tr_u
    # floor grates: bar gratings on the tile grid, in the bays
    GRT = []
    gr_d = np.full(HX.shape, 9.0, np.float32)
    grm = np.full(X.shape, 9.0)
    for _ in range(600):
        if len(GRT) >= 11:
            break
        w_, h_ = [(1.2, 0.6), (0.6, 1.2), (1.2, 1.2), (1.8, 0.6)][int(lr_.integers(0, 4))]
        x0_ = round(lr_.uniform(-15.5, 15.5 - w_) / TL) * TL
        z0_ = round(lr_.uniform(-9.0, 9.0 - h_) / TL) * TL
        sub = (X > x0_ - 0.45) & (X < x0_ + w_ + 0.45) & (Z > z0_ - 0.45) & (Z < z0_ + h_ + 0.45)
        if (ped[sub].min() < 0.4 or BLK_ANY[sub].min() < 0.3 or eqm[sub].min() < 0.1 or tkm[sub].min() < 0.3
                or trm[sub].min() < 0.1 or wk_d[sub].min() < 0.1 or grm[sub].min() < 0.6):
            continue
        GRT.append((x0_ + w_ / 2, z0_ + h_ / 2, w_ / 2, h_ / 2))
        gr_d = np.minimum(gr_d, _rr_h(x0_ + w_ / 2, z0_ + h_ / 2, w_ / 2 - 0.02, h_ / 2 - 0.02, 0.02))
        grm = np.minimum(grm, _rrect(x0_ + w_ / 2, z0_ + h_ / 2, w_ / 2, h_ / 2, 0.02))
    HD["gr_d"] = gr_d
    # frost round the tanks' pads: a ragged ring of rime, creeping in over the pad's rim
    frost = np.zeros(X.shape)
    for k_, (bx, bz, R) in enumerate(TANK):
        d_ = np.hypot(X - bx, Z - bz)
        reach = R + 0.3 + (fbm(0.5, 3, 621 + k_) - 0.5) * 0.32
        frost = np.maximum(frost, np.clip((reach - d_) / 0.18, 0, 1) * np.clip((d_ - R * 0.68) / 0.2, 0, 1))
    IND["frost"] = frost * np.clip((ped - 0.2) / 0.2, 0, 1)
    IND["scuff"] = np.clip((fbm(0.7, 3, 622) - 0.55) / 0.2, 0, 1)
    # paint: the bays' yellow safety lines (under everything else), the equipment bays' dashed outlines and white corner
    # marks; on the tracks white lane lines, the yellow guide line, fiducial tags every 2.4, hazard bars across the
    # ends of the decontamination grilles
    for (a_, b_) in CUTS:
        PAINT.seg("y", a_, b_, 0.06)
    for (cx, cz, hw, hh) in EQ:
        for (p0, p1) in (((cx - hw + 0.1, cz - hh + 0.1), (cx + hw - 0.1, cz - hh + 0.1)), ((cx + hw - 0.1, cz - hh + 0.1), (cx + hw - 0.1, cz + hh - 0.1)),
                         ((cx + hw - 0.1, cz + hh - 0.1), (cx - hw + 0.1, cz + hh - 0.1)), ((cx - hw + 0.1, cz + hh - 0.1), (cx - hw + 0.1, cz - hh + 0.1))):
            PAINT.dashed("r", [p0, p1], 0.05, 0.3, 0.2)
        for sx in (-1, 1):
            for sz in (-1, 1):
                q = (cx + sx * (hw - 0.2), cz + sz * (hh - 0.2))
                PAINT.seg("w", q, (q[0] - sx * 0.35, q[1]), 0.06)
                PAINT.seg("w", q, (q[0], q[1] - sz * 0.35), 0.06)
    on_sl = lambda x, z: (_smp(tbl, x, z) > 0.3) | (_smp(gate_m, x, z) > 0.3)
    road_line("w", HALF - 0.2, 0.03, skip=on_sl)
    road_line("w", -(HALF - 0.2), 0.03, skip=on_sl)
    road_line("r", 0.0, 0.05, skip=on_sl)
    n_tag = 0
    for li, (P, T, S_) in enumerate(RS):
        for s_ in np.arange(1.2, S_[-1] - 0.6, 2.4):
            i = int(s_ / 0.03)
            if i >= len(P) or DUP[li][i] or not _in_tex(P[i, 0], P[i, 1], 0.8):
                continue
            q, a_ = P[i], math.atan2(T[i, 1], T[i, 0])
            if _on_other(P[i:i + 1], T[i:i + 1], li, S_[i:i + 1], HALF + 0.3)[0] or on_sl(q[0], q[1]) or _at(tun_m, q[0], q[1]) > 0.5:
                continue
            if any(math.hypot(q[0] - gx, q[1] - gz) < 1.4 for gx, gz, _h, _k in GATES):
                continue
            PAINT.rect("w", q[0], q[1], 0.17, 0.17, a_)
            u_, n2 = (math.cos(a_), math.sin(a_)), (-math.sin(a_), math.cos(a_))
            bits = lr_.random(9) < 0.5
            bits[0] = bits[2] = bits[6] = True                         # (three corners set: which way it reads)
            bits[8] = False
            for bi in range(9):
                if bits[bi]:
                    a2, b2 = (bi % 3 - 1) * 0.042, (bi // 3 - 1) * 0.042
                    PAINT.rect("k", q[0] + u_[0] * a2 + n2[0] * b2, q[1] + u_[1] * a2 + n2[1] * b2, 0.038, 0.038, a_)
            n_tag += 1
    for zl in zf["slow"]:
        P_ = np.asarray(zl, np.float64)
        for (e_, f_) in ((P_[0], P_[1]), (P_[-1], P_[-2])):
            d_ = (f_ - e_) / max(np.hypot(*(f_ - e_)), 1e-9)
            c_ = e_ + d_ * 0.09
            PAINT.rect("hz", c_[0], c_[1], 0.16, 2 * HALF, math.atan2(d_[1], d_[0]))
    STUBS = []                                                         # pipe stubs at the tanks' pads
    for (bx, bz, R) in TANK:
        a0 = lr_.uniform(0, 2 * math.pi)
        for k_ in range(6):
            a_ = a0 + k_ * math.pi / 3
            q = (bx + math.cos(a_) * (R + 0.14), bz + math.sin(a_) * (R + 0.14))
            if _at(ped, q[0], q[1]) > 0.5 and _at(trm, q[0], q[1]) > 0.15 and len([s for s in STUBS if s[2] == (bx, bz)]) < 3:
                STUBS.append((q[0], q[1], (bx, bz)))
    log("lab: bays", len(BAYS), "walkways", WALKS, "crossings", len(XINGS), "trenches", len(TRN), "grates", len(GRT),
        "tags", n_tag, "stubs", len(STUBS), "equipment bays", len(EQ))

if THEME == "satellite":
    # a ground station on a high desert plateau: red-brown sand rippled by the wind, patches of dark desert pavement and
    # pale caliche, stones; the access roads (the robots' road) packed gravel with tyre ruts, a loose berm along each
    # side, a worn white edge line, sand drifting across them, reflector posts; concrete foundations under the dishes
    # (a ring of anchor bolts, the mount's grout ring); gravel beds under the solar arrays (rows of footings, covered
    # cable trenches between the rows); covered cable trenches from the dishes to the arrays; a fenced concrete compound
    # off the road with a gravel spur to it (the control building's lot); small concrete pads for masts
    sr_ = np.random.default_rng(151)
    DISH = [(bx, bz, br * 0.97) for (bx, bz, br, k_) in BLOCKERS if k_ == "dish"]
    PANL = [(bx, bz, br) for (bx, bz, br, k_) in BLOCKERS if k_ == "panels"]
    pd_r = np.full(HX.shape, 9.0, np.float32)
    pd_a = np.zeros(HX.shape, np.float32)
    for (bx, bz, R) in DISH:
        d_ = np.hypot(HX - bx, HZ - bz) / R
        pd_a = np.where(d_ < pd_r, np.arctan2(HZ - bz, HX - bx) / (2 * math.pi) + 0.5, pd_a)
        pd_r = np.minimum(pd_r, d_)
        LANDMARKS.append(("dish foundation", bx, bz, "r %.2f" % R))
    HD["pd_r"], HD["pd_a"] = pd_r, pd_a
    pdm = np.full(X.shape, 9.0)
    for (bx, bz, R) in DISH:
        pdm = np.minimum(pdm, np.hypot(X - bx, Z - bz) - R)
    gb_d = np.full(HX.shape, 9.0, np.float32)
    gbm = np.full(X.shape, 9.0)
    BEDS = []
    for (bx, bz, br) in PANL:
        hw, hh = br + 0.3, br + 0.08
        BEDS.append((bx, bz, hw, hh))
        gb_d = np.minimum(gb_d, _rr_h(bx, bz, hw, hh, 0.15))
        gbm = np.minimum(gbm, _rrect(bx, bz, hw, hh, 0.15))
        LANDMARKS.append(("solar array gravel bed", bx, bz, "%.2f x %.2f" % (2 * hw, 2 * hh)))
    HD["gb_d"] = gb_d
    # the compound: a concrete apron in the top-left corner, fenced, a gate on its east side, a gravel spur to the road
    APR = (-10.7, -7.05, 3.5, 1.75)
    HD["ap_d"] = _rr_h(APR[0], APR[1], APR[2], APR[3], 0.12)
    apm = _rrect(APR[0], APR[1], APR[2], APR[3], 0.12)
    LANDMARKS.append(("compound apron (control building)", APR[0], APR[1], "%.1f x %.1f" % (2 * APR[2], 2 * APR[3])))
    GATE_Z = (-7.35, -6.05)
    SPUR = [(APR[0] + APR[2] - 0.2, -6.7), (-3.2, -6.7)]
    sp_d, sp_al = gH.poly_dist([SPUR], margin=1.0)
    HD["sp_d"] = (sp_d - 0.48).astype(np.float32)
    spm = g.poly_dist([SPUR], margin=1.0)[0] - 0.48
    MASTS = [(13.8, -1.8), (-5.4, 7.8), (9.0, -7.8)]
    mp_d = np.full(HX.shape, 9.0, np.float32)
    mpm = np.full(X.shape, 9.0)
    for (cx, cz) in MASTS:
        mp_d = np.minimum(mp_d, _rr_h(cx, cz, 0.6, 0.6, 0.06))
        mpm = np.minimum(mpm, _rrect(cx, cz, 0.6, 0.6, 0.06))
        LANDMARKS.append(("mast pad", cx, cz, "1.2 square"))
    HD["mp_d"] = mp_d
    for (cx, cz) in MASTS + [(APR[0], APR[1])]:
        if _at(ped, cx, cz) < 1.0:
            log("satellite: a pad is close to the road!", (cx, cz), round(float(_at(ped, cx, cz)), 2))
    # paint: footings in rows across the beds ("c"), trench lids ("m") with joints ("k"), the road's worn edge line
    # ("w"), the apron's parking bays ("y") and a hatched keep-clear box ("r")
    for (bx, bz, hw, hh) in BEDS:
        for k_ in (-1, 0, 1):
            zr = bz + k_ * 0.8
            for x_ in np.arange(bx - hw + 0.35, bx + hw - 0.3, 0.55):
                PAINT.rect("c", x_, zr, 0.15, 0.15)
                PAINT.rect("k", x_, zr, 0.05, 0.05, v=200)
    TRS = []                                                           # covered cable trenches: polylines
    for (bx, bz, hw, hh) in BEDS:
        for zz_ in (bz - 0.4, bz + 0.4):
            TRS.append([(bx - hw + 0.12, zz_), (bx + hw - 0.12, zz_)])
    TRS.append([(APR[0] - 0.7, APR[1] + APR[3] - 0.05), (APR[0] - 0.7, -4.5)])                       # compound -> array A
    (d1x, d1z, d1r), (d2x, d2z, d2r), (d3x, d3z, d3r) = sorted(DISH, key=lambda d_: d_[0])
    TRS.append([(d1x, d1z - d1r + 0.05), (d1x, APR[1] + APR[3] - 0.05)])                              # west dish -> compound
    TRS.append([(d2x - d2r + 0.05, d2z), (d1x, d2z), (d1x, d1z + d1r - 0.05)])                        # dish -> west dish
    BB = max(BEDS, key=lambda b_: b_[0])
    TRS.append([(d3x + d3r - 0.05, d3z), (BB[0] + 0.8, d3z), (BB[0] + 0.8, BB[1] - BB[3] + 0.05)])    # centre dish -> array B
    trn_m = np.zeros(X.shape)
    for tr_ in TRS:
        Q, T_, S_ = _res(tr_, 0.03)
        ok = (_smp(ped, Q[:, 0], Q[:, 1]) > 0.42) & (_smp(pdm, Q[:, 0], Q[:, 1]) > -0.06) & (_smp(apm, Q[:, 0], Q[:, 1]) > -0.06)
        ok &= _smp(mpm, Q[:, 0], Q[:, 1]) > 0.1
        for a, b in _runs(ok):
            if b - a < 4:
                continue
            PAINT.line("m", Q[a:b], 0.28)
            for i in range(a, b):
                if (S_[i] % 0.5) < 0.03:
                    Nn = np.array([-T_[i, 1], T_[i, 0]])
                    PAINT.seg("k", Q[i] - Nn * 0.14, Q[i] + Nn * 0.14, 0.018, v=170)
            d_, _a = g.poly_dist([Q[a:b]], margin=0.5)
            trn_m = np.maximum(trn_m, np.clip((0.15 - d_) / 0.03, 0, 1))
    road_line("w", HALF - 0.12, 0.06, skip=lambda x, z: _smp(gate_m, x, z) > 0.2)
    road_line("w", -(HALF - 0.12), 0.06, skip=lambda x, z: _smp(gate_m, x, z) > 0.2)
    for k_ in range(6):                                                 # parking bays along the apron's north side
        x_ = APR[0] - APR[2] + 0.5 + k_ * 0.85
        PAINT.seg("y", (x_, APR[1] - APR[3] + 0.15), (x_, APR[1] - APR[3] + 1.25), 0.045)
    PAINT.seg("y", (APR[0] - APR[2] + 0.5, APR[1] - APR[3] + 1.25), (APR[0] - APR[2] + 0.5 + 5 * 0.85, APR[1] - APR[3] + 1.25), 0.045)
    hx0, hx1, hz0, hz1 = APR[0] + APR[2] - 1.5, APR[0] + APR[2] - 0.25, -7.3, -6.1                    # keep clear: inside the gate
    PAINT.line("r", [(hx0, hz0), (hx1, hz0), (hx1, hz1), (hx0, hz1), (hx0, hz0)], 0.05)
    for k_ in np.arange(-1.2, 1.4, 0.2):
        a_, b_ = (hx0 + k_, hz0), (hx0 + k_ + 1.2, hz1)
        t0 = max(0.0, (hx0 - a_[0]) / 1.2, 0.0)
        t1 = min(1.0, (hx1 - a_[0]) / 1.2)
        if t1 > t0:
            PAINT.seg("r", (a_[0] + 1.2 * t0, hz0 + 1.2 * t0), (a_[0] + 1.2 * t1, hz0 + 1.2 * t1), 0.04)
    # the fence: posts every 0.5 round the apron (0.15 out from it), a gap for the gate
    FENCE = []
    x0f, x1f, z0f, z1f = APR[0] - APR[2] - 0.15, APR[0] + APR[2] + 0.15, APR[1] - APR[3] - 0.15, APR[1] + APR[3] + 0.15
    per = [((x0f, z0f), (x1f, z0f)), ((x1f, z0f), (x1f, z1f)), ((x1f, z1f), (x0f, z1f)), ((x0f, z1f), (x0f, z0f))]
    for (a_, b_) in per:
        L_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
        n_ = max(1, int(round(L_ / 0.5)))
        run = []
        for t_ in np.linspace(0, 1, n_ + 1):
            q = (a_[0] + (b_[0] - a_[0]) * t_, a_[1] + (b_[1] - a_[1]) * t_)
            if abs(q[0] - x1f) < 0.01 and GATE_Z[0] < q[1] < GATE_Z[1]:
                if len(run) > 1:
                    FENCE.append(run)
                run = []
                continue
            run.append(q)
        if len(run) > 1:
            FENCE.append(run)
    # the desert itself
    IND["pave"] = np.clip((fbm(1.4, 4, 631) - 0.6) / 0.06, 0, 1) * np.clip((ped - 0.4) / 0.3, 0, 1)
    IND["cal"] = np.clip((fbm(2.2, 3, 632) - 0.62) / 0.08, 0, 1) * (1 - IND["pave"])
    dn = np.clip((fbm(1.4, 3, 633) - 0.6) / 0.1, 0, 1)                   # (drifts here and there, tongues over the edge)
    IND["drift"] = dn * np.clip((0.1 - ped + (fbm(0.6, 2, 634) - 0.5) * 0.35) / 0.25, 0, 1) * np.clip((ped + 0.75) / 0.2, 0, 1) * (1 - gate_m)
    IND["berm"] = np.clip(1 - np.abs(ped - 0.17) / 0.17, 0, 1) * (spm > 0.0)
    IND["stain"] = np.clip((fbm(0.45, 3, 635) - 0.62) / 0.08, 0, 1)
    IND["trn"] = trn_m
    RPOST = []                                                          # reflector posts along the road's edges
    for li, (P, T, S_) in enumerate(RS):
        for k_, s_ in enumerate(np.arange(1.0, S_[-1] - 0.5, 3.2)):
            i = int(s_ / 0.03)
            if i >= len(P) or DUP[li][i]:
                continue
            sg = 1 if k_ % 2 == 0 else -1
            q = P[i] + np.array([-T[i, 1], T[i, 0]]) * (HALF + 0.3) * sg
            if (not _in_tex(q[0], q[1], 0.6) or _at(ped, q[0], q[1]) < 0.2 or _at(pdm, q[0], q[1]) < 0.2 or _at(gbm, q[0], q[1]) < 0.2
                    or _at(apm, q[0], q[1]) < 0.3 or _at(spm, q[0], q[1]) < 0.15 or _at(gate_m, q[0], q[1]) > 0.0):
                continue
            RPOST.append((q[0], q[1], math.atan2(T[i, 1], T[i, 0])))
    sat_clear = np.minimum.reduce([pdm, gbm, apm, spm, mpm])
    log("satellite: dishes", len(DISH), "beds", len(BEDS), "trenches", len(TRS), "fence runs", len(FENCE), "reflector posts", len(RPOST))

if THEME == "neon":
    # a cyberpunk district at night, wet: the streets dark asphalt with cyan edge lines and magenta centre dashes, data
    # lanes (dark glass with cyan seams) on the fast stretches, cyan zebras; steel kerbs with a cyan light strip; deck-
    # plate sidewalks with grates, a magenta line along their outer edge; the blocks cut into lots (hex-tiled plazas,
    # dark slabs in a cyan grid, deck plates, parking with magenta bays, dark pavers) between dark steel bands; four
    # big hex plazas kept for the kit's stalls and billboards; the pylons' scorched hex bases with magenta conduits; the
    # data pits (a dark shaft, cyan light inside its rim, a hazard ring); the neon's glow and its reflections painted
    # into the wet ground, puddles
    nr_ = np.random.default_rng(171)
    LOTS_N, CUTS = [], []

    def _cutn(x0, z0, x1, z1, depth=0):
        w, h = x1 - x0, z1 - z0
        if max(w, h) < 3.6 or (max(w, h) < 5.5 and depth > 1 and nr_.random() < 0.4):
            LOTS_N.append((x0, z0, x1, z1))
            return
        ax = 0 if w >= h else 1
        lo, hi = (x0, x1) if ax == 0 else (z0, z1)
        for _try in range(40):
            s = round((lo + (hi - lo) * nr_.uniform(0.3, 0.7)) / 0.3) * 0.3
            if all(abs(s - (bx if ax == 0 else bz)) > br + 0.5 for (bx, bz, br, k_) in BLOCKERS
                   if x0 - br < bx < x1 + br and z0 - br < bz < z1 + br):
                break
        else:
            LOTS_N.append((x0, z0, x1, z1))
            return
        if ax == 0:
            CUTS.append([(s, z0), (s, z1)])
            _cutn(x0, z0, s, z1, depth + 1)
            _cutn(s, z0, x1, z1, depth + 1)
        else:
            CUTS.append([(x0, s), (x1, s)])
            _cutn(x0, z0, x1, s, depth + 1)
            _cutn(x0, s, x1, z1, depth + 1)

    _cutn(-21.0, -13.2, 19.2, 13.2)
    lk = np.zeros(X.shape, np.int8)
    pid = np.zeros(X.shape, np.float32)
    kinds_ = []
    for (x0, z0, x1, z1) in LOTS_N:
        sel = (X >= x0) & (X < x1) & (Z >= z0) & (Z < z1)
        kd = int(nr_.choice([0, 1, 2, 3, 4], p=[0.14, 0.3, 0.2, 0.14, 0.22]))
        if kd == 3 and min(x1 - x0, z1 - z0) < 2.2:
            kd = 1
        kinds_.append(kd)
        lk[sel] = kd
        pid[sel] = nr_.random()
    # the plazas kept for the kit: hex tiles in a steel border
    PLZ = [(-11.0, -2.6, 3.0, 1.2), (-13.2, 5.6, 1.4, 2.4), (13.2, 4.3, 1.4, 2.3), (-0.6, -6.6, 2.4, 1.2)]
    pz_d = np.full(HX.shape, 9.0, np.float32)
    pzm = np.full(X.shape, 9.0)
    for (cx, cz, hw, hh) in PLZ:
        sub = (np.abs(X - cx) < hw) & (np.abs(Z - cz) < hh)
        if ped[sub].min() < 0.7 or BLK_ANY[sub].min() < 0.25:
            log("neon: plaza too close to a road or a zone", (cx, cz), round(float(ped[sub].min()), 2), round(float(BLK_ANY[sub].min()), 2))
        pz_d = np.minimum(pz_d, _rr_h(cx, cz, hw, hh, 0.25))
        pzm = np.minimum(pzm, _rrect(cx, cz, hw, hh, 0.25))
        LANDMARKS.append(("hex plaza", cx, cz, "%.1f x %.1f" % (2 * hw, 2 * hh)))
    HD["pz_d"] = pz_d
    SW = 0.65
    blockm = (ped > SW).astype(float)
    nonpl = blockm * (pzm > 0)
    for k_, nm in enumerate(("l_hex", "l_grid", "l_deck", "l_park", "l_paver")):
        IND[nm] = (lk == k_) * nonpl
    IND["pid"] = pid
    # hex tiles everywhere (the material shows them on the plazas): flat-topped, 0.26 across the corners
    s_ = 0.15
    q_ = (2.0 / 3.0 * HX) / s_
    r_ = (-1.0 / 3.0 * HX + math.sqrt(3) / 3.0 * HZ) / s_
    cx_, cz_, cy_ = np.round(q_), np.round(r_), np.round(-q_ - r_)
    dx_, dz_, dy_ = np.abs(cx_ - q_), np.abs(cz_ - r_), np.abs(cy_ + q_ + r_)
    fx_ = (dx_ > dz_) & (dx_ > dy_)
    fz_ = ~fx_ & (dz_ > dy_)
    cx_ = np.where(fx_, -cz_ - cy_, cx_)
    cz_ = np.where(fz_, -cx_ - cy_, cz_)
    hx_c, hz_c = s_ * 1.5 * cx_, s_ * math.sqrt(3) * (cz_ + cx_ / 2)
    ux_, uz_ = np.abs(HX - hx_c), np.abs(HZ - hz_c)
    HD["hx_e"] = (s_ * math.sqrt(3) / 2 - np.maximum(uz_, ux_ * math.sqrt(3) / 2 + uz_ / 2)).astype(np.float32)
    HD["hx_id"] = (np.abs(np.sin(cx_ * 12.9898 + cz_ * 78.233) * 43758.5453) % 1.0).astype(np.float32)
    del q_, r_, cx_, cz_, cy_, dx_, dz_, dy_, fx_, fz_, hx_c, hz_c, ux_, uz_
    # pylon bases: steel hexagons (pointy side to the road), scorched round
    PYL = [(bx, bz, br) for (bx, bz, br, k_) in BLOCKERS if k_ == "pylon"]
    py_d = np.full(HX.shape, 9.0, np.float32)
    py_r = np.full(HX.shape, 9.0, np.float32)
    py_a = np.zeros(HX.shape, np.float32)
    scorch = np.zeros(X.shape)
    CONDUITS = []
    for (bx, bz, br) in PYL:
        Rb = br * 0.86
        ux_, uz_ = np.abs(HX - bx), np.abs(HZ - bz)
        hexd = np.maximum(uz_, ux_ * math.sqrt(3) / 2 + uz_ / 2) - Rb * math.sqrt(3) / 2
        rr_ = np.hypot(HX - bx, HZ - bz) / Rb
        py_a = np.where(rr_ < py_r, np.arctan2(HZ - bz, HX - bx) / (2 * math.pi) + 0.5, py_a)
        py_r = np.minimum(py_r, rr_)
        py_d = np.minimum(py_d, hexd)
        d_ = np.hypot(X - bx, Z - bz) + (fbm(0.5, 2, int(abs(bx * 7 + bz * 13)) % 997 + 700) - 0.5) * 0.35
        scorch = np.maximum(scorch, _scorch(bx, bz, Rb * 1.0, d_, nr_))
        a0 = nr_.uniform(0, 2 * math.pi)
        n_c = 0
        for k_ in range(12):
            a_ = a0 + k_ * 2 * math.pi / 12
            p0 = (bx + math.cos(a_) * Rb * 0.9, bz + math.sin(a_) * Rb * 0.9)
            p1 = (bx + math.cos(a_) * (Rb + 1.5), bz + math.sin(a_) * (Rb + 1.5))
            if _at(ped, p1[0], p1[1]) > 0.75 and _at(ped, (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2) > 0.75 and n_c < 3 and \
                    all(abs(math.remainder(a_ - c_[2], 2 * math.pi)) > 1.4 for c_ in CONDUITS if c_[3] == (bx, bz)):
                CONDUITS.append((p0, p1, a_, (bx, bz)))
                n_c += 1
        LANDMARKS.append(("pylon base (hexagon)", bx, bz, "r %.2f" % Rb))
    HD["py_d"], HD["py_r"], HD["py_a"] = py_d, py_r, py_a
    IND["scorch"] = scorch * (_down(py_d) > 0.0)
    # data pits: a shaft (the material lights its rim from inside), a steel rim, a hazard ring
    PIT = [(bx, bz, br * 0.78) for (bx, bz, br, k_) in BLOCKERS if k_ == "pit"]
    pt_r = np.full(HX.shape, 9.0, np.float32)
    pt_a = np.zeros(HX.shape, np.float32)
    for (bx, bz, R) in PIT:
        d_ = np.hypot(HX - bx, HZ - bz) / R
        pt_a = np.where(d_ < pt_r, np.arctan2(HZ - bz, HX - bx) / (2 * math.pi) + 0.5, pt_a)
        pt_r = np.minimum(pt_r, d_)
        LANDMARKS.append(("data pit (shaft r, rim to 1.3 r)", bx, bz, "r %.2f" % R))
    HD["pt_r"], HD["pt_a"] = pt_r, pt_a
    ptm = np.full(X.shape, 9.0)
    for (bx, bz, R) in PIT:
        ptm = np.minimum(ptm, np.hypot(X - bx, Z - bz) / R)
    # paint: road lines (cyan edges, magenta centre dashes, the data lanes' inner cyan lines and seams, cyan zebras),
    # grates in the sidewalks, the lots' borders (a dark band, now and then a neon line in it), the grid slabs' cyan
    # grid, the parking bays' magenta lines, the pylons' conduits
    nogate = lambda x, z: _smp(gate_m, x, z) > 0.2
    road_line("c", HALF - 0.1, 0.045, skip=nogate)
    road_line("c", -(HALF - 0.1), 0.045, skip=nogate)
    road_line("m", 0.0, 0.06, 0.55, 0.45, skip=lambda x, z: (_smp(bus, x, z) > 0.3) | nogate(x, z))
    for sg in (-1, 1):
        road_line("c", sg * (HALF - 0.2), 0.025, skip=lambda x, z: (_smp(bus, x, z) < 0.5) | nogate(x, z))
    XW = []
    for li, (P, T, S_) in enumerate(RS):
        for s_ in np.arange(4.2, S_[-1] - 2.0, 7.3):
            i = int(s_ / 0.03)
            if i >= len(P) or DUP[li][i] or not _in_tex(P[i, 0], P[i, 1], 3.0):
                continue
            j0, j1 = max(0, i - 25), min(len(P) - 1, i + 25)
            if abs(T[j0] @ T[j1]) < 0.995 or np.any(_on_other(P[j0:j1:5], T[j0:j1:5], li, S_[j0:j1:5], HALF + 0.8)):
                continue
            if _smp(bus, P[i, 0], P[i, 1]) > 0.3 or any(math.hypot(P[i, 0] - gx, P[i, 1] - gz) < 2.0 for gx, gz, _h, _k in GATES):
                continue
            if any(math.hypot(P[i, 0] - a_, P[i, 1] - b_) < 3.0 for a_, b_, _c in XW):
                continue
            XW.append((P[i, 0], P[i, 1], math.atan2(T[i, 1], T[i, 0])))
    for (cx, cz, a_) in XW:
        zebra(cx, cz, a_, L=0.5, bar=0.1, gap=0.1, half=HALF - 0.16, ch="c")
    for li, (P, T, S_) in enumerate(RS):                               # grates in the sidewalks
        for s_ in np.arange(1.3, S_[-1] - 0.5, 2.7):
            i = int(s_ / 0.03)
            if i >= len(P) or DUP[li][i]:
                continue
            for sg in (-1, 1):
                q = P[i] + np.array([-T[i, 1], T[i, 0]]) * (HALF + 0.38) * sg
                if not _in_tex(q[0], q[1], 0.5) or _at(ped, q[0], q[1]) < 0.3 or _at(ped, q[0], q[1]) > 0.46 or _at(gate_m, q[0], q[1]) > 0:
                    continue
                a_ = math.atan2(T[i, 1], T[i, 0])
                PAINT.rect("k", q[0], q[1], 0.42, 0.24, a_, 230)
                for k in range(7):
                    PAINT.rect("w", q[0] + math.cos(a_) * (k - 3) * 0.055, q[1] + math.sin(a_) * (k - 3) * 0.055, 0.018, 0.17, a_, 70)
    # (the lots' layer, under the sidewalks and the streets: "g" the borders' dark steel bands, "y" cyan and "r" magenta
    # lines in it; the streets' own lines are "c" and "m")
    for (a_, b_) in CUTS:                                               # the lots' borders
        PAINT.seg("g", a_, b_, 0.1, 210)
        if nr_.random() < 0.4:
            PAINT.seg("r" if nr_.random() < 0.5 else "y", a_, b_, 0.022)
    for i, (x0, z0, x1, z1) in enumerate(LOTS_N):
        if kinds_[i] == 1:                                              # the grid slabs: cyan lines every 1.2
            for x_ in np.arange(math.ceil((x0 + 0.1) / 1.2) * 1.2, x1 - 0.1, 1.2):
                PAINT.seg("y", (x_, z0 + 0.06), (x_, z1 - 0.06), 0.02, 200)
            for z_ in np.arange(math.ceil((z0 + 0.1) / 1.2) * 1.2, z1 - 0.1, 1.2):
                PAINT.seg("y", (x0 + 0.06, z_), (x1 - 0.06, z_), 0.02, 200)
        if kinds_[i] == 3:                                              # parking: magenta bays along both sides
            x0, z0, x1, z1 = x0 + 0.25, z0 + 0.25, x1 - 0.25, z1 - 0.25
            along_x = (x1 - x0) >= (z1 - z0)
            a0, a1, b0, b1 = (x0, x1, z0, z1) if along_x else (z0, z1, x0, x1)
            rows = [(b0, 1), (b1, -1)] if b1 - b0 > 2.3 else [(b0, 1)]
            for b_, sg in rows:
                n_ = int((a1 - a0) / 0.55)
                for k in range(n_ + 1):
                    a_ = a0 + k * 0.55
                    p0, p1 = (a_, b_), (a_, b_ + sg * 0.9)
                    PAINT.seg("r", p0 if along_x else p0[::-1], p1 if along_x else p1[::-1], 0.03, 220)
    for (p0, p1, a_, _b) in CONDUITS:
        PAINT.seg("g", p0, p1, 0.13, 230)
        PAINT.seg("r", p0, p1, 0.045)
        PAINT.rect("g", p1[0], p1[1], 0.2, 0.2, a_, 240)
        PAINT.rect("r", p1[0], p1[1], 0.08, 0.08, a_)
    # wet: puddles (on the streets more than off them), grime
    pn = fbm(0.9, 3, 641) + (fbm(0.22, 2, 642) - 0.5) * 0.08
    IND["pud"] = np.clip((np.quantile(pn, 0.12) - pn) / 0.02, 0, 1) * (ptm > 1.4) * (_down(py_d) > 0.1)
    IND["grime"] = np.clip((fbm(0.8, 4, 643) - 0.45) / 0.25, 0, 1)
    log("neon: lots", len(LOTS_N), "by kind", np.bincount(kinds_, minlength=5).tolist(), "crossings", len(XW), "conduits", len(CONDUITS))
if DC_T:
    # The Data Center's shared tools: the floor cut into bays on a grid (never through a zone), straight runs across the
    # floor until a road, a zone or the hall's edge, the clearest free spots (pads and plazas left for the kits' landmarks)
    def _bsp(rng, q, big, small, p_leaf, rect=(-21.0, -13.2, 19.2, 13.2)):
        leaves, cuts = [], []

        def _c(x0, z0, x1, z1, depth):
            w, h = x1 - x0, z1 - z0
            if max(w, h) < small or (max(w, h) < big and depth > 1 and rng.random() < p_leaf):
                leaves.append((x0, z0, x1, z1))
                return
            ax = 0 if w >= h else 1
            lo, hi = (x0, x1) if ax == 0 else (z0, z1)
            for _try in range(40):
                s = round((lo + (hi - lo) * rng.uniform(0.3, 0.7)) / q) * q
                if all(abs(s - (bx if ax == 0 else bz)) > br + 0.5 for (bx, bz, br, k_) in BLOCKERS
                       if x0 - br < bx < x1 + br and z0 - br < bz < z1 + br):
                    break
            else:
                leaves.append((x0, z0, x1, z1))
                return
            if ax == 0:
                cuts.append([(s, z0), (s, z1)])
                _c(x0, z0, s, z1, depth + 1)
                _c(s, z0, x1, z1, depth + 1)
            else:
                cuts.append([(x0, s), (x1, s)])
                _c(x0, z0, x1, s, depth + 1)
                _c(x0, s, x1, z1, depth + 1)

        _c(*rect, 0)
        return leaves, cuts

    def _ray(x_, z_, dx, dz, hw, stop, start_free=0.6, maxlen=14.0, road_m=0.35):
        """A straight run from (x_, z_) along (dx, dz), hw to each side of its centre line, until a road (or a tunnel's
        ramp), the hall's edge or (past start_free) wherever stop(points) says."""
        pts_, t = [], 0.0
        while t < maxlen:
            px_, pz_ = x_ + dx * t, z_ + dz * t
            if not (-16.0 < px_ < 16.0 and -9.6 < pz_ < 9.6):
                break
            q = [(px_ - dz * o_, pz_ + dx * o_) for o_ in (-hw, 0.0, hw)]
            if any(_at(ped, a_, b_) < road_m or _at(tun_m, a_, b_) > 0.5 for a_, b_ in q):
                break
            if t > start_free and stop(q):
                break
            pts_.append((px_, pz_))
            t += 0.05
        return pts_

    def _spots(n, hw, hh, clear_r, clear_b, spacing, avoid=None, xr=(-13.8, 13.8), zr=(-7.5, 7.5), taken=None):
        """Up to n rectangles (hw x hh half sizes) on the 0.6 grid, the clearest first: clear_r from every road, clear_b
        from every zone (and from avoid, a distance field < 0 inside), spacing apart."""
        out = list(taken or [])
        cl = np.minimum(ped - clear_r, BLK_ANY - clear_b)
        if avoid is not None:
            cl = np.minimum(cl, avoid - 0.2)
        cands = []
        for cx in np.arange(xr[0], xr[1] + 0.01, 0.6):
            for cz in np.arange(zr[0], zr[1] + 0.01, 0.6):
                j0, j1 = int((cx - hw - G.X0) * MPX), int((cx + hw - G.X0) * MPX) + 1
                i0, i1 = int((cz - hh - G.Z0) * MPX), int((cz + hh - G.Z0) * MPX) + 1
                v = float(cl[i0:i1, j0:j1].min())
                if v > 0:
                    cands.append((v, round(cx, 2), round(cz, 2)))
        cands.sort(key=lambda c_: -c_[0])
        new = []
        for v, cx, cz in cands:
            if len(new) >= n:
                break
            if all(math.hypot(cx - a_, cz - b_) > spacing for a_, b_ in out):
                out.append((cx, cz))
                new.append((cx, cz))
        return new

    def _ring_field(pads):
        """Distance from the nearest pad's centre / its radius, and the angle round it (0..1), on the hi-res grid."""
        r_ = np.full(HX.shape, 9.0, np.float32)
        a_ = np.zeros(HX.shape, np.float32)
        for (bx, bz, R) in pads:
            d_ = np.hypot(HX - bx, HZ - bz) / R
            a_ = np.where(d_ < r_, np.arctan2(HZ - bz, HX - bx) / (2 * math.pi) + 0.5, a_)
            r_ = np.minimum(r_, d_)
        return r_, a_

    def _seg_field(segs, hw, rc):
        """Signed distance to axis-aligned strips (centre lines (x0, z0, x1, z1), hw to each side, rounded ends rc), and
        the coordinate along each, on the hi-res grid; and the coarse distance."""
        d_h = np.full(HX.shape, 9.0, np.float32)
        u_h = np.zeros(HX.shape, np.float32)
        d_c = np.full(X.shape, 9.0)
        for (x0, z0, x1, z1) in segs:
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            ax_ = abs(x1 - x0) >= abs(z1 - z0)
            a_, b_ = (abs(x1 - x0) / 2 + hw, hw) if ax_ else (hw, abs(z1 - z0) / 2 + hw)
            d_ = _rr_h(cx, cz, a_, b_, rc)
            u_h = np.where(d_ < d_h, HX if ax_ else HZ, u_h)
            d_h = np.minimum(d_h, d_)
            d_c = np.minimum(d_c, _rrect(cx, cz, a_, b_, rc))
        return d_h.astype(np.float32), u_h.astype(np.float32), d_c

    PIPES = []                 # pipes lying on the floor: (points (x, z), radius)
    DEBRIS = []                # (x, z, kind)
if THEME == "cooling":
    # the robots' coolant vaults: a floor of steel deck plates (bays of diamond tread, bar grating and riveted panels
    # between steel seam beams) rimed with frost; coolant channels (pale blue coolant in a steel-lipped trench) from the
    # ice pads and the chillers out across the floor, pipes laid beside them; ice crusts and frozen spills; condensation;
    # round frozen drain pads under the ice; square chiller plinths with a fan grille under the machines; valve-station
    # pads for the kit; the robots' lanes heated service tracks (dark steel, less frost, meltwater, white edge lines and a
    # cyan guide line, a hazard-striped border), an ice sheet over the slow stretch, induction plates on the fast one
    cr_ = np.random.default_rng(181)
    BAYS_C, CUTS = _bsp(cr_, 0.6, 7.5, 4.3, 0.4)
    bk = np.zeros(X.shape, np.int8)
    bid = np.zeros(X.shape, np.float32)
    for (x0, z0, x1, z1) in BAYS_C:
        sel = (X >= x0) & (X < x1) & (Z >= z0) & (Z < z1)
        bk[sel] = cr_.choice([0, 1, 2], p=[0.45, 0.25, 0.3])
        bid[sel] = cr_.random()
    IND["b_grate"] = (bk == 1).astype(float)
    IND["b_panel"] = (bk == 2).astype(float)
    IND["bid"] = bid
    # the ice pads (round frozen drain pads) and the chillers' plinths (square, a fan grille)
    ICE = [(bx, bz, br * 0.94) for (bx, bz, br, k_) in BLOCKERS if k_ == "ice"]
    PLIN = [(bx, bz, br + 0.15) for (bx, bz, br, k_) in BLOCKERS if k_ == "machine"]
    HD["ic_r"], HD["ic_a"] = _ring_field(ICE)
    HD["fn_r"], HD["fn_a"] = _ring_field([(bx, bz, h_ * 0.8) for (bx, bz, h_) in PLIN])
    pl_d = np.full(HX.shape, 9.0, np.float32)
    plm = np.full(X.shape, 9.0)
    for (bx, bz, h_) in PLIN:
        pl_d = np.minimum(pl_d, _rr_h(bx, bz, h_, h_, 0.12))
        plm = np.minimum(plm, _rrect(bx, bz, h_, h_, 0.12))
        LANDMARKS.append(("chiller plinth (fan grille r %.2f)" % (h_ * 0.8), bx, bz, "%.2f square" % (2 * h_)))
    HD["pl_d"] = pl_d
    icm = np.full(X.shape, 9.0)
    for (bx, bz, R) in ICE:
        icm = np.minimum(icm, np.hypot(X - bx, Z - bz) - R)
        LANDMARKS.append(("frozen drain pad", bx, bz, "r %.2f" % R))
    # coolant channels: from each ice pad (the longest run) and each chiller (the longest two) straight out on the 0.6
    # grid, then the longest free runs across the open floor, until a track, a zone or the hall's edge
    CHW = 0.17
    pads_m = np.minimum(icm, plm)
    CH = []
    chm = np.full(X.shape, 9.0)

    def _free(q, own=None):
        return any(_at(BLK_ANY, a_, b_) < 0.15 or _at(pads_m, a_, b_) < 0.15 or _at(chm, a_, b_) < 0.5 for a_, b_ in q)

    def _add(p_):
        global chm
        (x0, z0), (x1, z1) = p_[0], p_[-1]
        CH.append((x0, z0, x1, z1))
        _d, _u, dc_ = _seg_field([(x0, z0, x1, z1)], CHW, CHW)
        chm = np.minimum(chm, dc_)

    for (bx, bz, R, n_) in [(bx, bz, R, 1) for (bx, bz, R) in ICE] + [(bx, bz, h_, 2) for (bx, bz, h_) in PLIN]:
        runs_ = []
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v_ = round((bz if dx else bx) / 0.6) * 0.6
            if abs(v_ - (bz if dx else bx)) > R * 0.5:
                v_ = bz if dx else bx
            sx_, sz_ = (bx + dx * R * 0.8, v_) if dx else (v_, bz + dz * R * 0.8)
            p_ = _ray(sx_, sz_, dx, dz, CHW + 0.05, lambda q: any(_at(BLK_ANY, a_, b_) < 0.15 or _at(chm, a_, b_) < 0.4 for a_, b_ in q)
                      or (_at(np.hypot(X - bx, Z - bz), q[1][0], q[1][1]) > R + 0.3 and _at(pads_m, q[1][0], q[1][1]) < 0.15),
                      start_free=R * 0.4 + 0.35, road_m=0.4)
            if len(p_) * 0.05 > 2.0:
                runs_.append((len(p_), p_))
        for _n, p_ in sorted(runs_, key=lambda r: -r[0])[:n_]:
            _add(p_)
    n_free = 0
    for _ in range(3):
        best = None
        for ax in (0, 1):
            for v in (np.arange(-7.8, 7.81, 0.6) if ax == 0 else np.arange(-14.4, 14.41, 0.6)):
                t_ = np.arange(-16.0, 16.0, 0.05) if ax == 0 else np.arange(-9.6, 9.6, 0.05)
                ok = np.ones(len(t_), bool)
                for off in (-CHW - 0.1, 0.0, CHW + 0.1):
                    xs_, zs_ = (t_, np.full(len(t_), v + off)) if ax == 0 else (np.full(len(t_), v + off), t_)
                    ok &= (_smp(ped, xs_, zs_) > 0.45) & (_smp(tun_m, xs_, zs_) < 0.5) & (_smp(BLK_ANY, xs_, zs_) > 0.4) & \
                        (_smp(pads_m, xs_, zs_) > 0.3) & (_smp(chm, xs_, zs_) > 1.2)
                for a, b in _runs(ok):
                    L_ = (b - a) * 0.05
                    if L_ > 4.5 and (best is None or L_ > best[0]):
                        best = (L_, ax, v, t_[a], t_[b - 1])
        if best is None:
            break
        L_, ax, v, lo, hi = best
        _add([(lo, v), (hi, v)] if ax == 0 else [(v, lo), (v, hi)])
        n_free += 1
    HD["ch_d"], HD["ch_u"], _chc = _seg_field(CH, CHW, CHW)
    # pipes beside the channels: one or two lying along one side of each longer channel, where the floor is clear
    for (x0, z0, x1, z1) in CH:
        L_ = math.hypot(x1 - x0, z1 - z0)
        if L_ < 2.6 or cr_.random() < 0.25:
            continue
        d_ = np.array([x1 - x0, z1 - z0]) / L_
        n_ = np.array([-d_[1], d_[0]])
        sg = cr_.choice([-1, 1])
        for off, r_ in ((0.36, 0.055), (0.5, 0.04))[:1 + int(cr_.random() < 0.6)]:
            t_ = np.arange(0.15, L_ - 0.15, 0.05)
            Q = np.array([x0, z0]) + np.outer(t_, d_) + n_ * off * sg
            ok = (_smp(ped, Q[:, 0], Q[:, 1]) > 0.3) & (_smp(BLK_ANY, Q[:, 0], Q[:, 1]) > 0.1) & (_smp(pads_m, Q[:, 0], Q[:, 1]) > 0.1) & \
                (_smp(_chc, Q[:, 0], Q[:, 1]) > 0.08) & (_smp(tun_m, Q[:, 0], Q[:, 1]) < 0.5)
            for a, b in _runs(ok):
                if (b - a) * 0.05 > 1.2:
                    PIPES.append((Q[a:b], r_))
    pp_m = np.full(X.shape, 9.0)
    if PIPES:
        pp_m = g.poly_dist([P_[::4] for P_, r_ in PIPES], margin=1.0)[0]
    # the valve stations: pads of bar grating with hazard corners, left for the kit's valves and pumps
    VS = _spots(3, 0.9, 0.9, 0.9, 0.9, 6.0, avoid=np.minimum(_chc - 0.3, pp_m - 0.3))
    vs_d = np.full(HX.shape, 9.0, np.float32)
    vsm = np.full(X.shape, 9.0)
    for (cx, cz) in VS:
        vs_d = np.minimum(vs_d, _rr_h(cx, cz, 0.9, 0.9, 0.08))
        vsm = np.minimum(vsm, _rrect(cx, cz, 0.9, 0.9, 0.08))
        LANDMARKS.append(("valve station pad", cx, cz, "1.8 square"))
    HD["vs_d"] = vs_d
    # frost: rime over the whole floor in patches, thick round the ice pads, the channels and the chillers; the heated
    # tracks keep only a ragged fringe at their edges
    near_ch = gaussian_filter((_chc < 0).astype(np.float32), 0.35 * MPX) * 2.5
    frost = np.clip((fbm(1.1, 4, 701) - 0.38) / 0.3, 0, 1) * 0.7
    frost = np.maximum(frost, np.clip(near_ch, 0, 1) * 0.85)
    for (bx, bz, R) in ICE:
        frost = np.maximum(frost, np.clip((R + 1.7 + (fbm(0.6, 3, 702) - 0.5) * 1.0 - np.hypot(X - bx, Z - bz)) / 1.0, 0, 1))
    for (bx, bz, h_) in PLIN:
        frost = np.maximum(frost, 0.8 * np.clip((h_ + 1.0 + (fbm(0.6, 3, 703) - 0.5) * 0.8 - np.hypot(X - bx, Z - bz)) / 0.9, 0, 1))
    edge_f = np.clip((ped + 0.16 + (fbm(0.25, 2, 704) - 0.5) * 0.22) / 0.14, 0, 1)
    IND["frost"] = np.clip(frost, 0, 1) * edge_f
    # ice crusts: a ragged ring of ice out past each pad's rim, frozen spills where the channels end on the floor and
    # here and there along them, a frozen flood out over the floor beside the slow stretch (its ice sheet is on the track)
    ice = np.zeros(X.shape)
    for k_, (bx, bz, R) in enumerate(ICE):
        d_ = np.hypot(X - bx, Z - bz)
        ice = np.maximum(ice, np.clip((R * 1.2 + 0.15 + (fbm(0.35, 3, 711 + k_) - 0.5) * 0.7 - d_) / 0.06, 0, 1))
    SPILL = []
    for (x0, z0, x1, z1) in CH:
        for (ex, ez) in ((x0, z0), (x1, z1)):
            if _at(pads_m, ex, ez) > 0.3 and cr_.random() < 0.8:
                SPILL.append((ex, ez, cr_.uniform(0.35, 0.6)))
        L_ = math.hypot(x1 - x0, z1 - z0)
        for _k in range(int(L_ / 4.0)):
            t_ = cr_.uniform(0.2, 0.8)
            SPILL.append((x0 + (x1 - x0) * t_ + cr_.normal(0, 0.15), z0 + (z1 - z0) * t_ + cr_.normal(0, 0.15), cr_.uniform(0.25, 0.45)))
    for k_, (sx, sz, r_) in enumerate(SPILL):
        d_ = np.hypot(X - sx, Z - sz) + (fbm(0.25, 2, 720 + k_ % 40) - 0.5) * r_ * 1.4
        ice = np.maximum(ice, np.clip((r_ - d_) / 0.05, 0, 1))
    if zf["slow"]:
        _sd2 = g.poly_dist(zf["slow"], margin=2.0)[0]
        flood = np.clip((HALF + 0.35 + (fbm(0.3, 3, 731) - 0.5) * 0.6 - _sd2) / 0.06, 0, 1)
        ice = np.maximum(ice, flood * (ped > 0.03))
    IND["ice"] = ice * np.clip((ped - 0.04) / 0.04, 0, 1) * (vsm > 0.05)
    # condensation: where the cold meets the air (round the chillers, the pipes, the channels), streaks of wet running
    # one way down the plates; meltwater puddled on the heated tracks
    wet = np.clip(near_ch * 0.6, 0, 1)
    for (bx, bz, h_) in PLIN:
        wet = np.maximum(wet, np.clip((h_ + 1.4 - np.hypot(X - bx, Z - bz)) / 0.8, 0, 1))
    wet = np.maximum(wet, np.clip((0.5 - pp_m) / 0.3, 0, 1))
    IND["wet"] = np.clip(wet * np.clip((fbm(0.7, 3, 741) - 0.3) / 0.3, 0, 1) + 0.25 * np.clip((fbm(1.4, 3, 742) - 0.55) / 0.2, 0, 1), 0, 1)
    pn_ = fbm(0.8, 3, 743) + (fbm(0.2, 2, 744) - 0.5) * 0.1
    IND["melt"] = np.clip((np.quantile(pn_, 0.2) - pn_) / 0.025, 0, 1) * np.clip((-ped - 0.1) / 0.1, 0, 1) * (1 - tbl)
    # paint: the bays' seam beams ("g"), dashed yellow keep-clear rings round the ice pads ("y"), the tracks' white edge
    # lines and cyan guide line, hazard bars across the slow stretch's ends
    for (a_, b_) in CUTS:
        PAINT.seg("g", a_, b_, 0.1)
    for (bx, bz, R) in ICE:
        rr_ = R * 1.2 + 0.4
        PAINT.dashed("y", _arc(bx, bz, rr_, 0, 2 * math.pi, 120), 0.06, 0.32, 0.22)
    on_sl = lambda x, z: (_smp(tbl, x, z) > 0.3) | (_smp(gate_m, x, z) > 0.3)
    road_line("w", HALF - 0.2, 0.035, skip=lambda x, z: _smp(gate_m, x, z) > 0.3)
    road_line("w", -(HALF - 0.2), 0.035, skip=lambda x, z: _smp(gate_m, x, z) > 0.3)
    road_line("c", 0.0, 0.05, 0.42, 0.3, skip=lambda x, z: on_sl(x, z) | (_smp(bus, x, z) > 0.3))
    for zl in zf["slow"]:
        P_ = np.asarray(zl, np.float64)
        for (e_, f_) in ((P_[0], P_[1]), (P_[-1], P_[-2])):
            d_ = (f_ - e_) / max(np.hypot(*(f_ - e_)), 1e-9)
            if _smp(tbl, e_[0] - d_[0] * 0.3, e_[1] - d_[1] * 0.3) > 0.5:
                continue                         # (another path's slow stretch goes on past this end: no bar inside the ice)
            c_ = e_ + d_ * 0.09
            PAINT.rect("hz", c_[0], c_[1], 0.16, 2 * HALF, math.atan2(d_[1], d_[0]))
    log("cooling: bays", len(BAYS_C), "channels", len(CH), "(free %d)" % n_free, "pipes", len(PIPES), "spills", len(SPILL),
        "valve stations", VS)
if THEME == "server":
    # an endless server hall: raised-floor tiles on the 0.6 grid; rows of rack footprints along x, every 4.8: a rack row,
    # a cold aisle of perforated tiles (blue lines along the racks' fronts), the facing row, a hot aisle (amber lines
    # along the backs, a covered cable trench down it, some covers off); the racks' status lights reflected on the floor;
    # rack plinths under the rack zones, heavy mainframe pads under the machines; open bays where racks were pulled out
    # (left for the kit); the robots' lanes dark service aisles edged with guide lights, a blue light strip and arrows on
    # the fast stretches
    sv_ = np.random.default_rng(191)
    RP = [(bx, bz, br + 0.15, br * 0.78) for (bx, bz, br, k_) in BLOCKERS if k_ == "rack"]
    MF = [(bx, bz, br + 0.2) for (bx, bz, br, k_) in BLOCKERS if k_ == "machine"]
    rp_d = np.full(HX.shape, 9.0, np.float32)
    rpm = np.full(X.shape, 9.0)
    for (bx, bz, hw, hh) in RP:
        rp_d = np.minimum(rp_d, _rr_h(bx, bz, hw, hh, 0.1))
        rpm = np.minimum(rpm, _rrect(bx, bz, hw, hh, 0.1))
        LANDMARKS.append(("rack plinth (two rows of four racks, back to back, along x)", bx, bz, "%.2f x %.2f" % (2 * hw, 2 * hh)))
    mf_d = np.full(HX.shape, 9.0, np.float32)
    mfm = np.full(X.shape, 9.0)
    for (bx, bz, h_) in MF:
        mf_d = np.minimum(mf_d, _rr_h(bx, bz, h_, h_, 0.15))
        mfm = np.minimum(mfm, _rrect(bx, bz, h_, h_, 0.15))
        LANDMARKS.append(("mainframe pad", bx, bz, "%.2f square" % (2 * h_)))
    HD["rp_d"], HD["mf_d"] = rp_d, mf_d
    zon = np.minimum(rpm, mfm)
    # the open bays (racks pulled out): kept clear of racks, hatched round
    OB = _spots(3, 1.2, 0.9, 0.7, 0.7, 7.0, avoid=zon)
    ob_d = np.full(HX.shape, 9.0, np.float32)
    obm = np.full(X.shape, 9.0)
    for (cx, cz) in OB:
        ob_d = np.minimum(ob_d, _rr_h(cx, cz, 1.2, 0.9, 0.05))
        obm = np.minimum(obm, _rrect(cx, cz, 1.2, 0.9, 0.05))
        LANDMARKS.append(("open bay (racks pulled out)", cx, cz, "2.4 x 1.8"))
    HD["ob_d"] = ob_d
    # the rows: rack footprints 0.6 x 1.2 where the floor is clear, in runs of three or more
    PER, Z0R = 4.8, -1.2
    clear_ = np.minimum.reduce([ped - 0.32, BLK_ANY - 0.35, zon - 0.3, obm - 0.25, 1.0 - tun_m * 9])
    RUNS = []                                                          # (row z0, x0, x1, front side +1 / -1)
    rk_d = np.full(HX.shape, 9.0, np.float32)
    rkm = np.full(X.shape, 9.0)
    for k_ in range(-4, 5):
        za = Z0R + k_ * PER
        for z0, front in ((za, 1), (za + 2.4, -1)):
            if z0 < -10.2 or z0 + 1.2 > 10.2:
                continue
            xs_ = np.arange(-16.2, 16.2, 0.6)
            ok = np.array([min(_at(clear_, x_ + a_, z0 + b_) for a_ in (0.03, 0.3, 0.57) for b_ in (0.03, 0.6, 1.17)) > 0 for x_ in xs_])
            for a, b in _runs(ok):
                if b - a >= 3:
                    RUNS.append((z0, xs_[a], xs_[b - 1] + 0.6, front))
    for (z0, x0, x1, fr) in RUNS:
        rk_d = np.minimum(rk_d, _rr_h((x0 + x1) / 2, z0 + 0.6, (x1 - x0) / 2 - 0.02, 0.58, 0.03))
        rkm = np.minimum(rkm, _rrect((x0 + x1) / 2, z0 + 0.6, (x1 - x0) / 2, 0.6, 0.03))
    HD["rk_d"] = rk_d
    # perforated tiles: the cold aisles between two rows (where either has racks), a few loose ones elsewhere
    pf = np.zeros(X.shape)
    for (z0, x0, x1, fr) in RUNS:
        if fr > 0:
            pf = np.maximum(pf, ((X > x0) & (X < x1) & (Z > z0 + 1.2) & (Z < z0 + 2.4)).astype(float))
        else:
            pf = np.maximum(pf, ((X > x0) & (X < x1) & (Z > z0 - 1.2) & (Z < z0)).astype(float))
    IND["perf"] = pf * (ped > 0.05) * (zon > 0.05) * (obm > 0.0)
    # cable trenches down the hot aisles' middles where the floor is clear for 3 or more, and two across the hall
    TRN = []
    for k_ in range(-4, 5):
        zc = Z0R + k_ * PER + 4.2
        if abs(zc) > 9.0:
            continue
        t_ = np.arange(-16.0, 16.0, 0.05)
        ok = np.ones(len(t_), bool)
        for off in (-0.3, 0.0, 0.3):
            ok &= (_smp(ped, t_, np.full(len(t_), zc + off)) > 0.4) & (_smp(np.minimum(zon, obm), t_, np.full(len(t_), zc + off)) > 0.2) & \
                (_smp(BLK_ANY, t_, np.full(len(t_), zc + off)) > 0.3) & (_smp(tun_m, t_, np.full(len(t_), zc + off)) < 0.5)
        for a, b in _runs(ok):
            if (b - a) * 0.05 > 3.0:
                TRN.append((round(t_[a] / 0.6) * 0.6 + 0.3, zc, round(t_[b - 1] / 0.6) * 0.6 - 0.3, zc))
    HD["tr_d"], HD["tr_u"], trm = _seg_field(TRN, 0.18, 0.0)
    # status lights reflected on the floor: little dots just off the racks' fronts (green mostly, some blue, amber, red)
    n_led = 0
    for (z0, x0, x1, fr) in RUNS:
        zf_ = z0 + 1.2 + 0.06 if fr > 0 else z0 - 0.06
        for x_ in np.arange(x0 + 0.08, x1 - 0.06, 0.6):
            for _k in range(int(sv_.integers(1, 4))):
                xx = x_ + sv_.uniform(0.0, 0.44)
                ch_ = sv_.choice(["g", "m", "r"], p=[0.62, 0.26, 0.12])
                PAINT.disc(ch_, xx, zf_ + fr * sv_.uniform(0.0, 0.03), sv_.uniform(0.018, 0.03))
                n_led += 1
    # paint: the rows' aisle lines (blue along the fronts, amber dashes along the backs), the open bays' hatched
    # outlines, the service aisles' guide lights (white dots along both edges), hazard bars at the gates
    for (z0, x0, x1, fr) in RUNS:
        zfr, zbk = (z0 + 1.2 + 0.05, z0 - 0.05) if fr > 0 else (z0 - 0.05, z0 + 1.2 + 0.05)
        PAINT.seg("c", (x0, zfr), (x1, zfr), 0.05)
        PAINT.dashed("y", [(x0, zbk), (x1, zbk)], 0.05, 0.3, 0.2)
    for (cx, cz) in OB:
        hw, hh = 1.2 - 0.06, 0.9 - 0.06
        PAINT.line("y", [(cx - hw, cz - hh), (cx + hw, cz - hh), (cx + hw, cz + hh), (cx - hw, cz + hh), (cx - hw, cz - hh)], 0.05)
    n_gl = 0
    for li, (P, T, S_) in enumerate(RS):
        Nn = np.stack([-T[:, 1], T[:, 0]], 1)
        for sg in (-1, 1):
            Q = P + Nn * (HALF - 0.1) * sg
            k = ~DUP[li] & ~_on_other(Q, T, li, S_, HALF - 0.03) & (np.abs((S_ + 0.15) % 0.3 - 0.15) < 0.016)
            k &= _smp(ped, Q[:, 0], Q[:, 1]) > -0.16
            for i in np.flatnonzero(k):
                if _smp(gate_m, Q[i, 0], Q[i, 1]) > 0.2:
                    continue
                PAINT.disc("w", Q[i, 0], Q[i, 1], 0.026)
                n_gl += 1
    road_line("k", 0.0, 0.03, 0.6, 0.6, skip=lambda x, z: (_smp(bus, x, z) > 0.3) | (_smp(gate_m, x, z) > 0.2), v=150)
    for (bx, bz, hw, hh) in RP:                                        # the plinths' rack outlines: two rows of four
        for row in (-1, 1):
            for k in range(4):
                x_, z_ = bx + (k - 1.5) * 0.62, bz + row * 0.42
                PAINT.line("k", [(x_ - 0.28, z_ - 0.38), (x_ + 0.28, z_ - 0.38), (x_ + 0.28, z_ + 0.38), (x_ - 0.28, z_ + 0.38), (x_ - 0.28, z_ - 0.38)], 0.025)
    for (bx, bz, h_) in MF:                                            # the mainframe pads: cable entry slots in a ring
        for k in range(12):
            a_ = 2 * math.pi * k / 12
            PAINT.rect("k", bx + math.cos(a_) * (h_ - 0.62), bz + math.sin(a_) * (h_ - 0.62), 0.2, 0.06, a_, 230)
    IND["scuff"] = np.clip((fbm(0.7, 3, 801) - 0.55) / 0.2, 0, 1)
    IND["dust"] = np.clip((fbm(1.2, 3, 802) - 0.5) / 0.25, 0, 1)
    log("server: rack runs", len(RUNS), "racks", int(sum(round((x1 - x0) / 0.6) for _z, x0, x1, _f in RUNS)), "trenches", len(TRN),
        "status lights", n_led, "guide lights", n_gl, "open bays", OB)
if THEME == "core":
    # the heart of the machine: a dark polished floor of big panels; circuit traces (cyan, some red) routed on the 45-degree
    # grid toward the centre, branching and joining, a via at each free end; energy conduits from the pillars' sockets
    # toward the centre; hex-tiled plazas (left for the kit); the pillars' sockets (a steel ring, a glowing ring, radial
    # slots); scorched craters under the wrecks (oil in the bowl, the floor cracked and burnt round them), smaller blast
    # scorches over the floor, debris; the robots' lanes bright data highways
    co_ = np.random.default_rng(211)
    CC = (0.0, 0.0)
    SOCK = [(bx, bz, br * 0.92) for (bx, bz, br, k_) in BLOCKERS if k_ == "pillar"]
    WRK = [(bx, bz, br * 0.85) for (bx, bz, br, k_) in BLOCKERS if k_ == "wreck"]
    HD["so_r"], HD["so_a"] = _ring_field(SOCK)
    som = np.full(X.shape, 9.0)
    for (bx, bz, R) in SOCK:
        som = np.minimum(som, np.hypot(X - bx, Z - bz) - R)
        LANDMARKS.append(("pillar socket (glowing ring)", bx, bz, "r %.2f" % R))
    # conduits: up to three from each socket, along the 45-degree directions nearest the way to the centre
    CON = []
    for (bx, bz, R) in SOCK:
        a_c = math.atan2(CC[1] - bz, CC[0] - bx)
        cand = sorted(range(8), key=lambda k: abs(math.remainder(k * math.pi / 4 - a_c, 2 * math.pi)))
        n_ = 0
        for k in cand:
            if n_ >= 3 or abs(math.remainder(k * math.pi / 4 - a_c, 2 * math.pi)) > 1.9:
                break
            dx, dz = math.cos(k * math.pi / 4), math.sin(k * math.pi / 4)
            p_ = _ray(bx + dx * R * 0.95, bz + dz * R * 0.95, dx, dz, 0.2, lambda q: any(_at(BLK_ANY, a_, b_) < 0.3 for a_, b_ in q),
                      start_free=0.6, road_m=0.4)
            if len(p_) * 0.05 > 1.5:
                CON.append(p_)
                n_ += 1
    if CON:
        _cd, HD["cd_u"] = gH.poly_dist([[p_[0], p_[-1]] for p_ in CON], margin=1.0)
        HD["cd_d"] = (_cd - 0.13).astype(np.float32)
        HD["cd_u"] = HD["cd_u"].astype(np.float32)
        cdm = g.poly_dist([[p_[0], p_[-1]] for p_ in CON], margin=1.0)[0] - 0.13
    else:
        HD["cd_d"], HD["cd_u"], cdm = np.full(HX.shape, 9.0, np.float32), np.zeros(HX.shape, np.float32), np.full(X.shape, 9.0)
    # hex plazas, clear of the sockets and the conduits
    PLZ = _spots(2, 1.05, 0.85, 0.5, 0.5, 7.0, avoid=np.minimum(som - 0.4, cdm - 0.3), xr=(-13.2, 13.2), zr=(-7.5, 7.5))
    PLZ += _spots(3 - len(PLZ), 1.05, 0.85, 0.5, 0.5, 7.0, avoid=np.minimum(som - 0.4, cdm - 0.3), xr=(-14.4, 14.4), zr=(-8.1, 8.1), taken=PLZ)
    pz_d = np.full(HX.shape, 9.0, np.float32)
    pzm = np.full(X.shape, 9.0)
    for (cx, cz) in PLZ:
        pz_d = np.minimum(pz_d, _rr_h(cx, cz, 1.05, 0.85, 0.25))
        pzm = np.minimum(pzm, _rrect(cx, cz, 1.05, 0.85, 0.25))
        LANDMARKS.append(("hex plaza", cx, cz, "2.1 x 1.7"))
    HD["pz_d"] = pz_d
    s_ = 0.15                                                          # (hex tiles, as Neon Grid's)
    q_ = (2.0 / 3.0 * HX) / s_
    r_ = (-1.0 / 3.0 * HX + math.sqrt(3) / 3.0 * HZ) / s_
    cx_, cz_, cy_ = np.round(q_), np.round(r_), np.round(-q_ - r_)
    dx_, dz_, dy_ = np.abs(cx_ - q_), np.abs(cz_ - r_), np.abs(cy_ + q_ + r_)
    fx_ = (dx_ > dz_) & (dx_ > dy_)
    fz_ = ~fx_ & (dz_ > dy_)
    cx_ = np.where(fx_, -cz_ - cy_, cx_)
    cz_ = np.where(fz_, -cx_ - cy_, cz_)
    hx_c, hz_c = s_ * 1.5 * cx_, s_ * math.sqrt(3) * (cz_ + cx_ / 2)
    ux_, uz_ = np.abs(HX - hx_c), np.abs(HZ - hz_c)
    HD["hx_e"] = (s_ * math.sqrt(3) / 2 - np.maximum(uz_, ux_ * math.sqrt(3) / 2 + uz_ / 2)).astype(np.float32)
    HD["hx_id"] = (np.abs(np.sin(cx_ * 12.9898 + cz_ * 78.233) * 43758.5453) % 1.0).astype(np.float32)
    del q_, r_, cx_, cz_, cy_, dx_, dz_, dy_, fx_, fz_, hx_c, hz_c, ux_, uz_
    # craters under the wrecks, smaller blast scorches over the floor; oil; cracks
    crater = np.zeros(X.shape)
    rim = np.zeros(X.shape)
    scorch = np.zeros(X.shape)
    oil = np.zeros(X.shape)
    for k_, (bx, bz, R) in enumerate(WRK):
        d_ = np.hypot(X - bx, Z - bz) + (fbm(0.5, 2, 821 + k_) - 0.5) * 0.35
        crater = np.maximum(crater, np.clip(1 - (d_ / R) ** 2, 0, 1))
        rim = np.maximum(rim, np.exp(-((d_ - R * 1.0) / (0.18 * R)) ** 2))
        scorch = np.maximum(scorch, _scorch(bx, bz, R * 1.05, d_, co_))
        for _j in range(4):
            ox, oz = bx + co_.normal(0, R * 0.35), bz + co_.normal(0, R * 0.35)
            oil = np.maximum(oil, np.clip((co_.uniform(0.25, 0.5) - np.hypot(X - ox, (Z - oz) * 1.2) + (fbm(0.2, 2, 830 + _j) - 0.5) * 0.2) / 0.05, 0, 1))
        LANDMARKS.append(("scorched crater (wreck)", bx, bz, "r %.2f" % R))
    BLAST = []
    for _ in range(900):
        if len(BLAST) >= 8:
            break
        x_, z_, r2 = co_.uniform(-14.5, 14.5), co_.uniform(-8.2, 8.2), co_.uniform(0.28, 0.5)
        if (_at(ped, x_, z_) < r2 + 0.5 or _at(BLK_ANY, x_, z_) < r2 + 0.6 or _at(pzm, x_, z_) < r2 + 0.3 or _at(cdm, x_, z_) < 0.2
                or any(math.hypot(x_ - a_, z_ - b_) < 3.5 for a_, b_, _r in BLAST)):
            continue
        BLAST.append((x_, z_, r2))
        d_ = np.hypot(X - x_, Z - z_) + (fbm(0.25, 2, 840 + len(BLAST)) - 0.5) * 0.3 * r2
        scorch = np.maximum(scorch, _scorch(x_, z_, r2, d_, co_) * 0.9)
        crater = np.maximum(crater, np.clip(1 - (d_ / (r2 * 0.6)) ** 2, 0, 1) * 0.35)
        if co_.random() < 0.5:
            oil = np.maximum(oil, np.clip((r2 * 0.8 - np.hypot(X - x_ - r2, Z - z_)) / 0.05, 0, 1))
    IND["crater"], IND["rim"] = crater * (ped > 0.05), rim * (ped > 0.05)
    IND["scorch"] = scorch * np.clip(ped / 0.1, 0, 1)
    IND["oil"] = oil * np.clip(ped / 0.1, 0, 1) * (_down(HD["so_r"]) > 1.05)
    IND["crack"] = np.clip(scorch * 1.4 + np.clip((fbm(1.3, 3, 852) - 0.72) / 0.08, 0, 1) * 0.6, 0, 1) * np.clip(ped / 0.1, 0, 1)
    IND["grime"] = np.clip((fbm(0.9, 4, 853) - 0.45) / 0.25, 0, 1)
    # circuit traces on a 0.1 grid: from free points toward the centre, a run of steps in one of the eight directions,
    # turning 45 degrees at a time toward the centre; a trace that meets another joins it (the trees converge), one that
    # meets a highway, a socket, a conduit, a plaza, a crater or the hall's edge ends there on a via
    TG = 0.1
    gx0, gz0, nX, nZ = -20.6, -12.6, 392, 252
    cxs = gx0 + (np.arange(nX) + 0.5) * TG
    czs = gz0 + (np.arange(nZ) + 0.5) * TG
    CXg, CZg = np.meshgrid(cxs, czs)
    blocked = (_smp(ped, CXg, CZg) < 0.24) | (_smp(BLK_ANY, CXg, CZg) < 0.3) | (_smp(som, CXg, CZg) < 0.25) | \
        (_smp(cdm, CXg, CZg) < 0.12) | (_smp(pzm, CXg, CZg) < 0.12) | (_smp(tun_m, CXg, CZg) > 0.5) | (_smp(crater, CXg, CZg) > 0.05)
    occ = np.zeros((nZ, nX), np.int32)
    DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    TR = []                                                            # (cells [(i, j)...], how it ends, joined trace id)
    tcz, tcx = int((CC[1] - gz0) / TG), int((CC[0] - gx0) / TG)
    for _try in range(4000):
        if len(TR) >= 330:
            break
        i, j = int(co_.integers(1, nZ - 1)), int(co_.integers(1, nX - 1))
        if blocked[max(0, i - 2):i + 3, max(0, j - 2):j + 3].any() or (occ[max(0, i - 3):i + 4, max(0, j - 3):j + 4] > 0).any():
            continue
        tid = len(TR) + 1
        a_c = math.atan2(tcz - i, tcx - j)
        d = int(round(a_c / (math.pi / 4))) % 8
        cells, end, join, run = [(i, j)], "edge", 0, int(co_.integers(3, 22))
        occ[i, j] = tid
        for _s in range(700):
            if run <= 0:
                a_c = math.atan2(tcz - i, tcx - j)
                best = min((d - 1) % 8, d, (d + 1) % 8, key=lambda k: abs(math.remainder(k * math.pi / 4 - a_c, 2 * math.pi)) + co_.uniform(0, 0.5))
                d, run = best, int(co_.integers(3, 26))
            dj, di = DIRS[d]
            ni, nj = i + di, j + dj
            if not (0 <= ni < nZ and 0 <= nj < nX):
                end = "edge"
                break
            hit = 0
            for (ai, aj) in ((ni, nj), (ni + 1, nj), (ni - 1, nj), (ni, nj + 1), (ni, nj - 1), (i + di, j), (i, j + dj)):
                if 0 <= ai < nZ and 0 <= aj < nX and occ[ai, aj] not in (0, tid):
                    hit = (ai, aj)
                    break
            if hit:
                cells.append(hit)
                end, join = "join", int(occ[hit])
                break
            if blocked[ni, nj]:
                end = "block"
                break
            if abs(ni - tcz) + abs(nj - tcx) < 3:
                end = "centre"
                break
            i, j = ni, nj
            cells.append((i, j))
            occ[i, j] = tid
            run -= 1
        if len(cells) < 6:
            for (a_, b_) in cells[:-1] if end == "join" else cells:
                if occ[a_, b_] == tid:
                    occ[a_, b_] = 0
            continue
        TR.append((cells, end, join))
    # colours (each tree its own: a joining trace takes its trunk's), widths (trunks wider), then paint
    col = {}
    wid = {}
    for k, (cells, end, join) in enumerate(TR):
        tid = k + 1
        if end != "join":
            col[tid] = "r" if co_.random() < 0.28 else "c"
            wid[tid] = co_.choice([0.05, 0.065, 0.08])
        else:
            col[tid] = col.get(join, "c")
            wid[tid] = max(0.035, wid.get(join, 0.06) * co_.uniform(0.65, 0.95))
    TRACES = []
    for k, (cells, end, join) in enumerate(TR):
        tid = k + 1
        P_ = np.array([(gx0 + (b_ + 0.5) * TG, gz0 + (a_ + 0.5) * TG) for a_, b_ in cells])
        keep = [0] + [m for m in range(1, len(P_) - 1) if abs((P_[m, 0] - P_[m - 1, 0]) * (P_[m + 1, 1] - P_[m, 1]) - (P_[m, 1] - P_[m - 1, 1]) * (P_[m + 1, 0] - P_[m, 0])) > 1e-9] + [len(P_) - 1]
        Q_ = P_[keep]
        w_, c_ = float(wid[tid]), col[tid]
        PAINT.line(c_, Q_, w_)
        TRACES.append((Q_, w_, c_))
        PAINT.disc(c_, Q_[0, 0], Q_[0, 1], w_ * 1.7)                     # a via at its free end
        PAINT.disc("k", Q_[0, 0], Q_[0, 1], w_ * 0.75)
        if end in ("block", "edge", "centre"):
            PAINT.disc(c_, Q_[-1, 0], Q_[-1, 1], w_ * 1.5)
            PAINT.disc("w", Q_[-1, 0], Q_[-1, 1], w_ * 0.6)
        else:
            PAINT.disc(c_, Q_[-1, 0], Q_[-1, 1], w_ * 0.9)
    # the highways' and conduits' edges, the sockets' rings: their glow is added with the traces' further down
    log("core: traces", len(TR), "by end", {e_: sum(1 for t in TR if t[1] == e_) for e_ in ("join", "block", "edge", "centre")},
        "red", sum(1 for v in col.values() if v == "r"), "conduits", len(CON), "plazas", PLZ, "blasts", len(BLAST))
if MOD_T or DIG_T:
    PNT = PAINT.arrays()
    log("paint", {k_: round(float(v_.mean()), 4) for k_, v_ in PNT.items()})
if DIG_T:
    if THEME == "server":
        # the guide lights' and the status lights' glow on the floor, a longer smear toward the camera (the reflection)
        for nm_, src_, k_ in (("hw", PNT["w"], 1.0), ("hg", PNT["g"], 1.3), ("hb", PNT["m"], 1.3), ("hr", PNT["r"], 1.3)):
            near_ = gaussian_filter(src_, 0.05 * HPX)
            far_ = gaussian_filter(src_, (0.3 * HPX, 0.1 * HPX))
            HD[nm_] = np.clip((near_ * 3.0 + far_ * 6.0) * k_, 0, 1).astype(np.float32)
        log("glow", {k_: round(float(HD[k_].mean()), 4) for k_ in ("hw", "hg", "hb", "hr")})
    if THEME == "core":
        # the lights' glow on the polished floor: the traces, the conduits, the sockets' rings, the highways' edges
        _p = HD["ped"]
        _edge = np.clip(1 - np.abs(_p + 0.057) / 0.02, 0, 1) * (gt_r > 1.0)
        _cd = np.clip((-HD["cd_d"] - 0.03) / 0.03, 0, 1)
        _so = np.clip(1 - np.abs(HD["so_r"] - 0.74) / 0.06, 0, 1)
        for nm_, src_, k_ in (("hc", np.maximum.reduce([PNT["c"], _edge * 0.7, _cd, _so]), 1.0), ("hr", PNT["r"], 1.1)):
            near_ = gaussian_filter(src_, 0.06 * HPX)
            far_ = gaussian_filter(src_, (0.36 * HPX, 0.12 * HPX))
            HD[nm_] = np.clip((near_ * 2.4 + far_ * 3.0) * k_, 0, 1).astype(np.float32)
        del _p, _edge, _cd, _so, near_, far_
        log("glow", {k_: round(float(HD[k_].mean()), 4) for k_ in ("hc", "hr")})
    if THEME == "neon":
        # the neon's glow on the wet ground: each light's halo, and a longer smear toward the camera (its reflection)
        _p = HD["ped"]
        _src_c = np.maximum.reduce([PNT["c"], np.clip(1 - np.abs(_p - 0.05) / 0.016, 0, 1) * (gt_r > 1.0),
                                    np.clip((HD["pt_r"] - 0.78) / 0.12, 0, 1) * (HD["pt_r"] < 1.0)])
        _src_m = np.maximum(PNT["m"], np.clip(1 - np.abs(_p - (SW - 0.02)) / 0.016, 0, 1) * (HD["pz_d"] > 0))
        for nm_, src_ in (("hc", _src_c), ("hm", _src_m)):
            near_ = gaussian_filter(src_, 0.07 * HPX)
            far_ = gaussian_filter(src_, (0.42 * HPX, 0.14 * HPX))
            HD[nm_] = np.clip(near_ * 3.2 + far_ * 4.5, 0, 1).astype(np.float32)
        del _src_c, _src_m, near_, far_
        log("glow", {k_: round(float(HD[k_].mean()), 4) for k_ in ("hc", "hm")})
    PNT.update(HD)
    for (what_, x_, z_, size_) in LANDMARKS:
        log("landmark: %s at (%.2f, %.2f), %s" % (what_, x_, z_, size_))
if arg("--maskdump"):                    # quick look at the masks (no render): python3 map_ground_hq.py MAP --maskdump DIR
    from PIL import Image as _Im
    os.makedirs(arg("--maskdump"), exist_ok=True)
    _extra = [("paint_" + k_, v_) for k_, v_ in PNT.items()] if (MOD_T or DIG_T) else []
    for k_, v_ in list(IND.items()) + [("road", road), ("tk_d", np.clip(1 - tk_d / 2, 0, 1)), ("outside", outside)] + _extra:
        v_ = np.asarray(v_, np.float64)
        if v_.max() > 1.01 or v_.min() < -0.01:
            v_ = (v_ - v_.min()) / max(1e-6, v_.max() - v_.min())
        _Im.fromarray((np.clip(v_, 0, 1) * 255).astype(np.uint8)).save(os.path.join(arg("--maskdump"), k_ + ".png"))
    if DIG_T:                            # (the raw fields, a quarter of the render's resolution)
        _q = 1 if PREVIEW else 4         # (whole, at a preview's resolution)
        np.savez_compressed(os.path.join(arg("--maskdump"), "fields.npz"), **{k_: np.asarray(v_, np.float32)[::_q, ::_q] for k_, v_ in PNT.items()})
    log("masks dumped ->", arg("--maskdump"))
    sys.exit(0)
if arg("--watersrc") and THEME in ("highland", "bog", "coast", "harbor", "smog", "suburb"):
    from PIL import Image as _Im
    _w = np.maximum(np.clip(-riv / 0.12, 0, 1), np.clip(-blk["lake"] / 0.15, 0, 1))
    if THEME == "harbor":
        _w = _w * (1 - gp_b)                  # (not under the plank decks: the planks don't ripple)
    if THEME == "smog":
        _w = np.clip(-(pool_d + 0.2) / 0.03, 0, 1)    # (the dock pools inside their coping, not the whole lake zone)
    if THEME == "suburb":
        _w = IND["water"]                     # (the swimming pools inside their coping)
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
    shelf = np.clip((0.25 - riv) / 0.65, 0, 1)
    shelf = shelf * shelf * (3 - 2 * shelf)                         # 0 a little way up the beach, 1 well out in the water
    hf = np.where(gp_b < 0.5, hf * (1 - shelf) - 0.1 * shelf, hf)   # the beach shelving smoothly under the inlet (no step)
    hf += gp_b * (0.05 + rut * 0.02)                                                                # the decks and floors on joists
if THEME == "fortress":
    hf += (fbm(1.0, 4, 221) - 0.5) * 0.05 * (1 - road) + (fbm(0.25, 2, 222) - 0.5) * 0.02 * (1 - road)   # churned
    hf -= crater * 0.28
    hf += crater_rim * 0.07
    hf -= gp_a * 0.1                                                                                # the trenches
    hf += gp_b * 0.07                                                                               # their spoil heaps
    hf -= gp_c * 0.014                                                                              # wheel ruts across the field
    hf -= rut * 0.012                                                                               # (deeper in the military roads)
if THEME == "factory":
    hf += (fbm(0.6, 3, 441) - 0.5) * 0.04 * (1 - road) + (fbm(0.2, 2, 442) - 0.5) * 0.012 * (1 - road)   # lumpy cinder
    hf += IND["slag"] * (0.012 + (fbm(0.22, 2, 443) - 0.5) * 0.04)                                      # slag crusts
    hf += IND["plates"] * 0.012 + (IND["flags"] + IND["cobble"]) * 0.006 + IND["apron"] * 0.014
    hf -= IND["puddle"] * 0.012
    hf += np.clip((0.95 - tk_d) / 0.4, 0, 1) * 0.025 * (1 - on_road)                                    # the spurs' ballast
if THEME == "railyard":
    hf += (fbm(0.5, 3, 451) - 0.5) * 0.03 * (1 - road)
    hf += np.clip((0.95 - tk_d + wob_t * 0.5) / 0.35, 0, 1) ** 0.8 * 0.035 * (1 - on_road)             # the ballast beds
    hf += np.clip(IND["pads"] / 0.15, 0, 1) * 0.03                                                       # goods platforms
    hf = np.where(IND["pit"] > 0.5, -0.11, hf) + IND["coping"] * 0.012                                  # the turntable pit
if THEME == "smog":
    hf += rut * 0.017                                                                                   # (setts: hardly rutted)
    hf += (fbm(0.5, 3, 461) - 0.5) * 0.025 * (IND["y_waste"] + IND["y_earth"])                           # waste ground
    hf -= IND["puddle"] * 0.008 + IND["gutter"] * 0.008
    hf = np.where(pool_d < -0.2, -0.09, hf) + (pool_d < 0) * (pool_d >= -0.2) * 0.014                    # the dock pools
if THEME == "military":
    pv_ = np.maximum.reduce([IND["conc"], IND["rwy"], IND["blast"]])
    hf += road * 0.015 + rut * 0.017                                                                    # (asphalt: hardly rutted)
    hf = hf * (1 - 0.85 * pv_) + pv_ * 0.004                                                            # the pavements, flat
    hf -= IND["crater"] * 0.3
    hf += IND["rim"] * 0.07
if THEME == "metro":                     # all paved and flat: the carriageway a kerb's height down, the brick table up
    hf = (fbm(1.6, 3, 501) - 0.5) * 0.008 - road * 0.04 + tbl * 0.028
    hf += (fbm(0.8, 3, 502) - 0.5) * 0.03 * (IND["l_lawn"] + IND["beds"]) + IND["beds"] * 0.012
    hf += (IND["planter"] > 0.02) * 0.05 + IND["plinth"] * 0.012 - IND["pit"] * 0.012
if THEME == "suburb":                    # gently rolling lawns; the streets a kerb's height down; the pools sunk in
    pav_ = np.maximum(road, IND["cul"])
    lawny = np.clip(IND["lawn"] + IND["fbed"], 0, 1)
    hf = (fbm(1.8, 4, 511) - 0.5) * 0.06 * lawny + (fbm(0.4, 2, 512) - 0.5) * 0.006 - pav_ * 0.034
    hf += IND["fbed"] * 0.012 - IND["play"] * 0.004 - IND["sand"] * 0.008
    hf = np.where(IND["water"] > 0.5, -0.09, hf) + IND["coping"] * 0.008
if THEME == "lab":                       # a flat hall floor: the plinths raised, the grates and the drain sunk
    hf = (fbm(1.6, 3, 601) - 0.5) * 0.004
    hf += np.clip(-_down(HD["pl_d"]) / 0.02, 0, 1) * 0.035
    tkr_ = _down(HD["tk_r"])
    hf += (tkr_ < 1.0) * 0.012 - (tkr_ < 0.18) * 0.012
    hf -= np.clip(-_down(HD["gr_d"]) / 0.02, 0, 1) * 0.012 + np.clip(-_down(HD["tr_d"]) / 0.02, 0, 1) * 0.003
    hf += gate_m * 0.006
if THEME == "satellite":                 # rolling sand; the roads cut in a little, a berm of loose gravel each side; the pads
    pe_ = np.clip((ped - 0.3) / 1.2, 0, 1)
    hf = (fbm(2.0, 4, 611) - 0.5) * 0.11 * pe_ + (fbm(0.5, 2, 612) - 0.5) * 0.018 * pe_ + (fbm(0.25, 2, 613) - 0.5) * 0.006
    hf -= road * 0.028 + rut * 0.012
    hf += IND["berm"] * 0.014 + IND["drift"] * road * 0.01
    hs_ = gaussian_filter(hf, 1.6 * MPX)                         # (the pads sit level on the ground round them)
    for (n_, h_) in (("pd_r", 0.04), ("gb_d", 0.012), ("ap_d", 0.022), ("mp_d", 0.03)):
        m_ = np.clip((1.0 - _down(HD["pd_r"])) * 30, 0, 1) if n_ == "pd_r" else np.clip(-_down(HD[n_]) / 0.03, 0, 1)
        hf = hf * (1 - m_) + m_ * (hs_ + h_)
    hf -= np.clip(-_down(HD["sp_d"]) / 0.03, 0, 1) * 0.008
    hf += IND["trn"] * 0.004
if THEME == "neon":                      # flat: the streets a kerb's height down, the pylons' bases up, the pits' shafts
    hf = (fbm(1.6, 3, 641) - 0.5) * 0.006 - road * 0.035 - IND["pud"] * 0.003
    hf += np.clip(-_down(HD["pz_d"]) / 0.03, 0, 1) * 0.008 + np.clip(-_down(HD["py_d"]) / 0.03, 0, 1) * 0.04
    ptr_ = _down(HD["pt_r"])
    hf = np.where(ptr_ < 1.0, -0.3, hf) + ((ptr_ >= 1.0) & (ptr_ < 1.16)) * 0.015
if THEME == "cooling":                   # a flat steel floor: the grates and the channels sunk, the plinths and the pads up
    hf = (fbm(1.6, 3, 751) - 0.5) * 0.004 - road * 0.004
    hf -= IND["b_grate"] * 0.006 * (ped > 0.1)
    hf -= np.clip(-_down(HD["ch_d"]) / 0.03, 0, 1) * 0.03
    hf += np.clip(-_down(HD["pl_d"]) / 0.02, 0, 1) * 0.035 + np.clip(-_down(HD["vs_d"]) / 0.02, 0, 1) * 0.008
    icr_ = _down(HD["ic_r"])
    hf += (icr_ < 1.0) * 0.016 + np.clip(1 - icr_, 0, 1) * 0.012
    hf += IND["ice"] * (0.008 + (fbm(0.2, 2, 752) - 0.5) * 0.01)
if THEME == "server":                    # the raised floor; the service aisles a step down, the open bays down to the subfloor,
    hf = (fbm(1.6, 3, 811) - 0.5) * 0.003 - road * 0.035                          # the plinths and pads up
    hf -= np.clip(-_down(HD["tr_d"]) / 0.02, 0, 1) * 0.006 + np.clip(-_down(HD["ob_d"]) / 0.02, 0, 1) * 0.03
    hf += np.clip(-_down(HD["rp_d"]) / 0.02, 0, 1) * 0.03 + np.clip(-_down(HD["mf_d"]) / 0.02, 0, 1) * 0.045
if THEME == "core":                      # a polished flat floor; the highways and the conduits sunk a little, the sockets'
    hf = (fbm(1.6, 3, 861) - 0.5) * 0.003 - road * 0.03                                     # rims up, the craters blasted in
    hf -= np.clip(-_down(HD["cd_d"]) / 0.02, 0, 1) * 0.015
    sor_ = _down(HD["so_r"])
    hf += ((sor_ >= 0.84) & (sor_ < 1.0)) * 0.022 + (sor_ < 0.84) * 0.01 + np.clip(-_down(HD["pz_d"]) / 0.02, 0, 1) * 0.008
    hf -= IND["crater"] * 0.22
    hf += IND["rim"] * 0.05 + IND["scorch"] * (fbm(0.2, 2, 862) - 0.5) * 0.012
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
# Industrial Age: the road's and the tracks' own coordinates, then each theme's feature masks four to an image
img10 = to_image("mask10", np.stack([rc_al, rc_sd, tk_al, tk_sd], 2))
INDN = {"factory": ["flags", "cobble", "plates", "puddle", "rust", "slag", "apron", "ballast", "coke"],
        "railyard": ["ballast", "xing", "coal", "pit", "coping", "pads", "weeds", "drip", "puddle", "tt_u"],
        "smog": ["y_flags", "y_cobble", "y_waste", "y_brick", "y_earth", "y_quay", "lane", "wall", "pave", "kerb", "gutter", "grate",
                 "water", "coping", "cope_u", "manhole", "puddle", "soot", "pid"],
        "military": ["conc", "rwy", "blast", "haz", "crater", "rim", "scorch", "oil", "mow"],
        "metro": ["l_tile", "l_conc", "l_brick", "l_lot", "l_lawn", "l_slate", "pid", "lotb", "plinth", "beds", "bedk", "plaza",
                  "pl_r", "pl_a", "planter", "side", "kerb", "tbl", "bus", "pit", "mh", "oil", "grime", "lpath"],
        "suburb": ["water", "wline", "coping", "deck", "pdepth", "play", "playb", "sand", "drive", "gpath", "side", "kerb", "cul",
                   "fbed", "lawn", "mca", "msa", "lshade", "bus", "veg", "pk_r"],
        "lab": ["b_tile", "b_raised", "b_esd", "bid", "frost", "scuff"],
        "satellite": ["pave", "cal", "drift", "berm", "stain", "trn"],
        "neon": ["l_hex", "l_grid", "l_deck", "l_park", "l_paver", "pid", "pud", "scorch", "grime"],
        "cooling": ["b_grate", "b_panel", "bid", "frost", "ice", "wet", "melt"],
        "server": ["perf", "scuff", "dust"],
        "core": ["crater", "rim", "scorch", "oil", "crack", "grime"]}.get(THEME, [])
IND_IMGS = []
PNT_IMGS = []                            # the paint and (Digital) the hi-res fields, four to an image
if MOD_T or DIG_T:
    _pn = list(PNT.keys())
    for k_ in range(0, len(_pn), 4):
        grp = _pn[k_:k_ + 4]
        PNT_IMGS.append((grp, to_image("paint%d" % k_, np.stack([np.asarray(PNT[n_], np.float32) for n_ in grp] +
                                                                  [np.zeros(PNT[grp[0]].shape, np.float32)] * (4 - len(grp)), 2))))
    log("paint images", len(PNT_IMGS), PNT_IMGS[0][1].size[:])
for k_ in range(0, len(INDN), 4):
    grp = INDN[k_:k_ + 4]
    IND_IMGS.append((grp, to_image("ind%d" % k_, np.stack([np.asarray(IND[n_], np.float64) for n_ in grp] +
                                                          [np.zeros(X.shape)] * (4 - len(grp)), 2))))


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

    def vec(self, x, y, z=0.0):
        nd = self.n("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            if isinstance(v, (int, float)):
                nd.inputs[i].default_value = v
            else:
                self.link(v, nd.inputs[i])
        return nd.outputs[0]

    def xyz(self):
        """Object coordinates as (x, y) sockets (y = -world z)."""
        sp = self.n("ShaderNodeSeparateXYZ")
        self.link(self.uvn.outputs["Object"], sp.inputs[0])
        return sp.outputs[0], sp.outputs[1]

    def brick(self, vec, w, h, mortar=0.012, smooth=0.2, offset=0.5, freq=2):
        """Bricks, setts, flags or plates on the coordinates vec (x across a brick's width, y across its rows): returns
        (the joints, 1 in the mortar; a random value per brick in 0..1)."""
        nd = self.n("ShaderNodeTexBrick", offset=offset, offset_frequency=freq)
        nd.inputs["Color1"].default_value = (0.0, 0.0, 0.0, 1.0)
        nd.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1.0)
        nd.inputs["Mortar"].default_value = (0.5, 0.5, 0.5, 1.0)
        nd.inputs["Scale"].default_value = 1.0
        nd.inputs["Mortar Size"].default_value = mortar
        nd.inputs["Mortar Smooth"].default_value = smooth
        nd.inputs["Bias"].default_value = 0.0
        nd.inputs["Brick Width"].default_value = w
        nd.inputs["Row Height"].default_value = h
        self.link(vec, nd.inputs["Vector"])
        sep = self.n("ShaderNodeSeparateColor")
        self.link(nd.outputs["Color"], sep.inputs["Color"])
        return nd.outputs["Fac"], sep.outputs["Red"]

    def cramp(self, x, stops):
        """A colour ramp: stops [(position, colour)...]."""
        nd = self.n("ShaderNodeValToRGB")
        els = nd.color_ramp.elements
        els[0].position, els[0].color = stops[0][0], lin(stops[0][1])
        els[1].position, els[1].color = stops[-1][0], lin(stops[-1][1])
        for p_, col in stops[1:-1]:
            e = els.new(p_)
            e.color = lin(col)
        self.link(x, nd.inputs["Fac"])
        return nd.outputs["Color"]

    def noise_v(self, vec, scale, detail=3.0, rough=0.55):
        nd = self.n("ShaderNodeTexNoise")
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Detail"].default_value = detail
        nd.inputs["Roughness"].default_value = rough
        self.link(vec, nd.inputs["Vector"])
        return nd.outputs["Fac"]

    def voronoi_v(self, vec, scale, out="Distance", feature="F1"):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature)
        nd.inputs["Scale"].default_value = scale
        self.link(vec, nd.inputs["Vector"])
        return nd.outputs[out]

    def seam(self, v, p):
        """Distance from v to the nearest multiple of p."""
        f = self.math("FRACT", self.math("DIVIDE", v, p))
        return self.math("MULTIPLY", self.math("SUBTRACT", 0.5, self.math("ABSOLUTE", self.math("SUBTRACT", f, 0.5))), p)

    def dots(self, u, v, pu, pv, off, r):
        """Bolt heads: 1 in a dot of radius r set in by off from each corner of a pu x pv grid on (u, v)."""
        du = self.math("SUBTRACT", self.seam(u, pu), off)
        dv = self.math("SUBTRACT", self.seam(v, pv), off)
        d = self.math("SQRT", self.math("ADD", self.math("MULTIPLY", du, du), self.math("MULTIPLY", dv, dv)))
        return self.ramp(d, r, r * 0.6)


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
I = {}                                   # Industrial Age: the theme's feature masks by name
if IND_T:
    ral, rsd, tal, tsd = nb.tex(img10)
    for grp, im_ in IND_IMGS:
        for n_, o_ in zip(grp, nb.tex(im_)):
            I[n_] = o_
    Pn = {}
    for grp, im_ in PNT_IMGS:
        for n_, o_ in zip(grp, nb.tex(im_)):
            Pn[n_] = o_
    if MOD_T or DIG_T:
        pw_m, py_m, pr_m, pk_m = Pn["w"], Pn["y"], Pn["r"], Pn["k"]
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
    pv = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.36, 0.36, 0.3), (0.47, 0.46, 0.38))
    pv = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(2.4, "Color"), 0.6, 0.9), 0.35), pv, (0.3, 0.32, 0.25))
    pv = nb.mix(nb.math("SUBTRACT", 1.0, flag), pv, (0.1, 0.17, 0.045))
    pv = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.4, 3, 0.6), 0.52, 0.66), 0.8), pv, (0.16, 0.29, 0.07))
    c = nb.mix(nb.math("MULTIPLY", gpa_m, 0.95), c, pv)
    # the tracks: red clay, rutted, dry and crusted on top, darker and wet in the ruts and the low spots; puddles of
    # red-brown water where they dip, the sky's sheen on them, a bright rim at the water's edge and wet clay round it
    clay = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.4, 0.19, 0.1), (0.5, 0.26, 0.15))
    clay = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.55, 0.75), 0.3), clay, (0.56, 0.34, 0.21))
    clay = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.2, 3, 0.6), 0.6, 0.72), 0.45), clay, (0.33, 0.15, 0.08))
    clay = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(30.0, "Distance"), 0.22, 0.1), 0.25), clay, (0.32, 0.16, 0.09))
    clay = nb.mix(nb.math("MULTIPLY", rut_m, nb.mixf(nb.ramp(nb.noise(2.5, 2, 0.6), 0.3, 0.7), 0.25, 0.55)), clay, (0.33, 0.15, 0.08))
    clay = nb.mix(nb.math("MULTIPLY", nb.ramp(gpb_m, 0.0, 0.45), 0.85), clay, (0.27, 0.11, 0.05))       # wet clay round the puddles
    pud = nb.mix(nb.ramp(nb.noise(0.9, 3, 0.6), 0.3, 0.7), (0.32, 0.14, 0.075), (0.4, 0.19, 0.1))
    pud = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(0.45, 2, 0.5), 0.45, 0.85), 0.25), pud, (0.5, 0.34, 0.28))   # the sky's sheen
    pud = nb.mix(nb.math("MULTIPLY", nb.math("MULTIPLY", nb.ramp(gpb_m, 0.45, 0.52), nb.ramp(gpb_m, 0.66, 0.56)), 0.45), pud, (0.58, 0.4, 0.32))
    clay = nb.mix(nb.ramp(gpb_m, 0.45, 0.6), clay, pud)
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
    ripz = nb.math("MULTIPLY", nb.ramp(nb.noise(0.8, 3, 0.6), 0.45, 0.65), 0.16)                       # (in patches)
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(rip.outputs["Fac"], 0.55, 0.85), ripz), c, (0.76, 0.66, 0.47))   # wind ripples
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(fine, 0.6, 0.75), 0.3), c, (0.95, 0.9, 0.74))
    grass = nb.mix(nb.ramp(nb.noise(2.0, 3, 0.6), 0.3, 0.7), (0.5, 0.52, 0.27), (0.62, 0.62, 0.34))    # thin sea grass, the dunes
    grass = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.36, 0.24), 0.6), grass, (0.32, 0.42, 0.18))      # greener in the hollows
    c = nb.mix(nb.math("MULTIPLY", gpf_m, 0.8), c, grass)
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.38, 0.46, 0.22), (0.48, 0.54, 0.28)))       # greener inland, beyond
    beach = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.92, 0.86, 0.7), (0.98, 0.94, 0.8))      # the beach: pale, bare
    c = nb.mix(gpe_m, c, beach)
    wetc = nb.mix(nb.ramp(nb.noise(2.2, 3, 0.6), 0.3, 0.7), (0.72, 0.64, 0.48), (0.8, 0.72, 0.56))      # wet sand, darker
    wetc = nb.mix(nb.ramp(gpa_m, 0.6, 1.0), wetc, (0.66, 0.58, 0.43))                                  # toward the water
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(gpa_m, 0.0, 0.7), 0.88), c, wetc)
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
    wood = nb.mix(nb.mixf(road_m, id_p, id_d), (0.54, 0.44, 0.32), (0.68, 0.58, 0.43))
    wood = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(18.0, 3, 0.6), 0.3, 0.7), 0.3), wood, (0.46, 0.37, 0.26))
    wood = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(2.0, 3, 0.6), 0.55, 0.68), 0.45), wood, (0.7, 0.68, 0.62))   # bleached grey
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
    c = nb.mix(nb.math("MULTIPLY", gpc_m, 0.55), c, (0.28, 0.21, 0.13))                                 # wheel ruts
    spoil = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.4, 0.3, 0.19), (0.49, 0.37, 0.24))     # fresh spoil
    spoil = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(22.0, 2, 0.5), 0.64, 0.74), 0.35), spoil, (0.31, 0.23, 0.15))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(gpb_m, 0.05, 0.45), 0.9), c, spoil)
    wall = nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.36, 0.27, 0.17), (0.44, 0.33, 0.21))     # the trench: cut earth walls
    c = nb.mix(nb.ramp(gpa_m, 0.0, 0.35), c, wall)
    ditch = nb.mix(nb.ramp(nb.noise(4.0, 3, 0.6), 0.3, 0.7), (0.17, 0.13, 0.09), (0.23, 0.17, 0.11))   # its floor, trodden and wet
    c = nb.mix(nb.ramp(gpa_m, 0.6, 0.95), c, ditch)
    # a crater: raw earth darkening down into the bowl, a ring of earth thrown up round it, the blast's soot in rays beyond
    # (and in patches over the rim)
    burnt = nb.mix(nb.ramp(nb.noise(6.0, 3, 0.6), 0.3, 0.7), (0.09, 0.08, 0.07), (0.21, 0.18, 0.14))   # scorched, sooty
    soot = nb.math("MULTIPLY", gpd_m, nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", rim_m, 0.55)),
                                              nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", crater_m, 0.8))))
    c = nb.mix(nb.math("MULTIPLY", soot, 0.88), c, burnt)
    crat = nb.mix(nb.ramp(crater_m, 0.0, 0.7), (0.34, 0.26, 0.16), (0.15, 0.11, 0.08))
    crat = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(5.0, 3, 0.6), 0.55, 0.7), 0.35), crat, (0.1, 0.085, 0.07))   # soot in it
    c = nb.mix(nb.ramp(crater_m, 0.0, 0.12), c, crat)
    rimc = nb.mix(nb.ramp(nb.noise(8.0, 3, 0.6), 0.3, 0.7), (0.4, 0.3, 0.19), (0.5, 0.39, 0.25))       # the thrown-up rim
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(rim_m, 0.25, 0.75), nb.math("SUBTRACT", 0.9, nb.math("MULTIPLY", gpd_m, 0.4))), c, rimc)
    camp = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.4, 0.33, 0.22), (0.5, 0.42, 0.29))      # trodden by the dumps
    c = nb.mix(nb.math("MULTIPLY", zonea_m, 0.8), c, camp)
    grav = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.47, 0.42, 0.34), (0.57, 0.51, 0.41))    # the gravel road
    peb = nb.voronoi(42.0, "Distance")
    grav = nb.mix(nb.math("MULTIPLY", nb.ramp(peb, 0.24, 0.1), 0.42), grav, (0.66, 0.61, 0.52))
    grav = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(17.0, "Distance"), 0.3, 0.12), 0.3), grav, (0.36, 0.32, 0.26))
    grav = nb.mix(nb.math("MULTIPLY", rut_m, nb.mixf(nb.ramp(nb.noise(2.2, 2, 0.6), 0.3, 0.7), 0.3, 0.55)), grav, (0.36, 0.3, 0.21))   # ruts
    grav = nb.mix(nb.math("MULTIPLY", nb.math("MULTIPLY", rut_m, nb.ramp(nb.noise(1.5, 3, 0.6), 0.62, 0.7)), 0.6), grav, (0.27, 0.23, 0.17))   # wet
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.55), c, (0.31, 0.28, 0.18))
    c = nb.mix(road_m, c, grav)
    rough = 0.9
    bump_h = nb.math("MULTIPLY", road_m, nb.math("MULTIPLY", nb.ramp(peb, 0.24, 0.1), 0.6))
elif THEME == "factory":
    # a foundry district: cinder and slag-black earth, ash grains and black clinker in it, rusty patches; old yards of
    # cracked flagstones and of cobbles; riveted iron floor plates round the machines and in loading bays; brick aprons
    # round the mills; oily puddles; coke dust; the rail spurs' cinder ballast. The roads granite setts edged with a
    # course of long stones, the fast lanes laid with worn riveted steel plates
    obj = nb.uvn.outputs["Object"]
    ox_, oy_ = nb.xyz()
    c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.14, 0.125, 0.115), (0.21, 0.185, 0.165))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.6, 0.74), 0.35), c, (0.22, 0.17, 0.13))                # browner earth
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(34.0, "Distance"), 0.24, 0.07), 0.4), c, (0.36, 0.33, 0.3))   # ash grains
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(15.0, "Color"), 0.8, 0.97), 0.55), c, (0.06, 0.055, 0.05))    # black clinker
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.11, 0.1, 0.095), (0.16, 0.145, 0.13)))
    c = nb.mix(nb.math("MULTIPLY", I["coke"], 0.75), c, nb.mix(nb.ramp(fine, 0.3, 0.7), (0.045, 0.045, 0.045), (0.1, 0.095, 0.09)))
    slagc = nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.04, 0.045, 0.05), (0.09, 0.1, 0.11))
    slagc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(2.0, 2, 0.5, distort=1.5), 0.62, 0.72), 0.55), slagc, (0.13, 0.19, 0.21))
    c = nb.mix(nb.math("MULTIPLY", I["slag"], 0.92), c, slagc)                                            # glassy slag crusts
    rustc = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.27, 0.15, 0.08), (0.4, 0.22, 0.11))
    c = nb.mix(nb.math("MULTIPLY", I["rust"], nb.math("MULTIPLY", nb.ramp(nb.noise(7.0, 3, 0.6), 0.35, 0.65), 0.45)), c, rustc)
    # old yards: big flagstones (some cracked, a few gone), cobbles; soot ground into both
    fj, fr_ = nb.brick(obj, 0.62, 0.44, 0.013, 0.15)
    fl = nb.mix(fr_, (0.27, 0.26, 0.24), (0.42, 0.4, 0.36))
    fl = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(4.0, 3, 0.6), 0.45, 0.75), 0.65), fl, (0.13, 0.12, 0.11))
    fl = nb.mix(nb.math("MULTIPLY", I["rust"], 0.25), fl, (0.34, 0.21, 0.13))
    crack = nb.math("MULTIPLY", nb.ramp(nb.voronoi(3.4, "Distance", "DISTANCE_TO_EDGE"), 0.012, 0.0), nb.ramp(fr_, 0.5, 0.62))
    fl = nb.mix(nb.math("MAXIMUM", fj, crack), fl, (0.07, 0.065, 0.06))
    flm = nb.math("MULTIPLY", I["flags"], nb.ramp(fr_, 0.05, 0.08))                                      # (a few flags gone)
    c = nb.mix(flm, c, fl)
    cbd = nb.voronoi(9.5, "Distance", "DISTANCE_TO_EDGE")
    cob = nb.mix(nb.ramp(nb.voronoi(9.5, "Color"), 0.2, 0.8), (0.28, 0.27, 0.26), (0.44, 0.42, 0.39))
    cob = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(3.0, 3, 0.6), 0.5, 0.75), 0.5), cob, (0.16, 0.15, 0.14))
    cob = nb.mix(nb.ramp(cbd, 0.06, 0.015), cob, (0.06, 0.055, 0.05))
    c = nb.mix(I["cobble"], c, cob)
    # iron floor plates: a grid of 0.7 plates, each its own shade, rust blooms on some, oil stains, a tread of lozenges,
    # dark seams, a bolt near each corner
    pj, prd = nb.brick(obj, 0.7, 0.7, 0.01, 0.1, offset=0.0, freq=1)
    plc = nb.mix(prd, (0.16, 0.16, 0.17), (0.27, 0.27, 0.28))
    bloom = nb.math("MULTIPLY", nb.ramp(prd, 0.55, 0.85), nb.ramp(nb.noise(6.0, 3, 0.6), 0.4, 0.65))
    plc = nb.mix(nb.math("MULTIPLY", bloom, 0.6), plc, (0.33, 0.19, 0.1))
    plc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.5, 3, 0.6), 0.6, 0.72), 0.6), plc, (0.06, 0.06, 0.065))
    tread = nb.ramp(nb.math("ABSOLUTE", nb.math("MULTIPLY", nb.math("SINE", nb.math("MULTIPLY", nb.math("ADD", ox_, oy_), 52.0)),
                                                     nb.math("SINE", nb.math("MULTIPLY", nb.math("SUBTRACT", ox_, oy_), 52.0)))), 0.72, 0.95)
    plc = nb.mix(nb.math("MULTIPLY", tread, 0.22), plc, (0.38, 0.38, 0.39))
    plc = nb.mix(pj, plc, (0.04, 0.04, 0.045))
    bolts = nb.dots(ox_, oy_, 0.7, 0.7, 0.07, 0.022)
    plc = nb.mix(bolts, plc, (0.44, 0.42, 0.4))
    c = nb.mix(I["plates"], c, plc)
    # brick aprons round the mills, sooty
    aj, ar = nb.brick(obj, 0.24, 0.08, 0.008, 0.2)
    apc = nb.mix(ar, (0.22, 0.13, 0.095), (0.34, 0.19, 0.13))
    apc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(3.0, 3, 0.6), 0.4, 0.7), 0.7), apc, (0.11, 0.085, 0.075))
    apc = nb.mix(aj, apc, (0.11, 0.095, 0.085))
    c = nb.mix(I["apron"], c, apc)
    # the spurs' ballast: cinder and broken stone
    bsd = nb.voronoi(30.0, "Distance", "DISTANCE_TO_EDGE")
    bal = nb.mix(nb.ramp(nb.voronoi(30.0, "Color"), 0.2, 0.8), (0.19, 0.18, 0.17), (0.33, 0.31, 0.29))
    bal = nb.mix(nb.ramp(bsd, 0.05, 0.01), bal, (0.06, 0.055, 0.05))
    bal = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.math("ABSOLUTE", tsd), 0.14, 0.04), 0.5), bal, (0.08, 0.07, 0.065))   # oil drips
    c = nb.mix(I["ballast"], c, bal)
    # oily puddles: wet dark earth round them, black water with a rainbow sheen of oil on it
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(I["puddle"], 0.0, 0.45), 0.6), c, (0.07, 0.065, 0.06))
    film = nb.cramp(nb.noise(1.3, 3, 0.6, distort=2.0), [(0.0, (0.15, 0.16, 0.18)), (0.4, (0.24, 0.17, 0.26)), (0.47, (0.14, 0.24, 0.24)),
                                                         (0.54, (0.27, 0.24, 0.13)), (0.62, (0.15, 0.16, 0.18)), (1.0, (0.14, 0.15, 0.17))])
    pud = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(2.2, 2, 0.5), 0.35, 0.65), 0.6), (0.15, 0.16, 0.18), film)      # sky, oil
    pud = nb.mix(nb.math("MULTIPLY", nb.ramp(I["puddle"], 0.62, 0.5), 0.8), pud, (0.07, 0.065, 0.06))
    pmask = nb.ramp(I["puddle"], 0.45, 0.6)
    c = nb.mix(pmask, c, pud)
    # the roads: granite setts in courses across the road, polished where the wheels run, sooty toward the edges, a
    # course of long edge stones each side
    rvec = nb.vec(rsd, ral)
    sj, sr_ = nb.brick(rvec, 0.21, 0.115, 0.014, 0.35)
    ars = nb.math("ABSOLUTE", rsd)
    st = nb.mix(sr_, (0.34, 0.33, 0.33), (0.5, 0.48, 0.47))
    st = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(30.0, 2, 0.5), 0.55, 0.75), 0.25), st, (0.58, 0.56, 0.54))
    st = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(3.0, 3, 0.6), 0.5, 0.75), 0.4), st, (0.2, 0.19, 0.18))      # soot
    st = nb.mix(nb.math("MULTIPLY", rut_m, 0.4), st, (0.58, 0.58, 0.58))
    st = nb.mix(nb.math("MULTIPLY", nb.ramp(ars, HALF - 0.45, HALF - 0.05), 0.45), st, (0.2, 0.19, 0.18))
    kj, kr = nb.brick(nb.vec(ral, ars), 0.42, 10.0, 0.014, 0.3, offset=0.0, freq=1)
    kst = nb.mix(kr, (0.42, 0.41, 0.4), (0.55, 0.54, 0.52))
    kst = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(4.0, 3, 0.6), 0.5, 0.75), 0.45), kst, (0.24, 0.23, 0.22))
    kmask = nb.ramp(ars, HALF - 0.17, HALF - 0.15)
    st = nb.mix(kmask, st, kst)
    sjo = nb.math("MAXIMUM", nb.mixf(kmask, sj, kj), nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", ars, HALF - 0.16)), 0.014, 0.004))
    st = nb.mix(sjo, st, (0.09, 0.085, 0.08))
    # the fast lanes: steel plates right across the road (two to a width), worn bright, rust at their seams, bolted
    lu = nb.math("ADD", rsd, HALF)
    lj, lr = nb.brick(nb.vec(lu, ral), HALF, 0.8, 0.012, 0.1, offset=0.0, freq=1)
    lc = nb.mix(lr, (0.25, 0.26, 0.28), (0.36, 0.36, 0.38))
    lc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.math("MINIMUM", nb.seam(lu, HALF), nb.seam(ral, 0.8)), 0.07, 0.02), 0.35), lc, (0.3, 0.18, 0.1))
    lc = nb.mix(nb.math("MULTIPLY", rut_m, 0.45), lc, (0.5, 0.5, 0.52))                                  # polished in the wheel tracks
    ltr = nb.ramp(nb.math("ABSOLUTE", nb.math("MULTIPLY", nb.math("SINE", nb.math("MULTIPLY", nb.math("ADD", lu, ral), 52.0)),
                                                   nb.math("SINE", nb.math("MULTIPLY", nb.math("SUBTRACT", lu, ral), 52.0)))), 0.72, 0.95)
    lc = nb.mix(nb.math("MULTIPLY", ltr, 0.3), lc, (0.5, 0.5, 0.51))
    lc = nb.mix(lj, lc, (0.06, 0.06, 0.065))
    lc = nb.mix(nb.dots(lu, ral, HALF, 0.8, 0.07, 0.024), lc, (0.62, 0.6, 0.56))
    st = nb.mix(lane_m, st, lc)
    st = nb.mix(nb.math("MULTIPLY", nb.ramp(I["puddle"], 0.45, 0.6), nb.math("SUBTRACT", 1.0, lane_m)), st, pud)     # puddles on the setts
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.45), c, (0.07, 0.065, 0.06))
    c = nb.mix(road_m, c, st)
    rough = nb.mixf(pmask, nb.mixf(nb.math("MULTIPLY", road_m, lane_m), nb.mixf(I["plates"], nb.mixf(I["slag"], 0.92, 0.4), 0.6), 0.45), 0.06)
    bump_h = nb.math("ADD", nb.math("MULTIPLY", road_m, nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, nb.mixf(lane_m, sjo, lj)), 0.7)),
                     nb.math("ADD", nb.math("MULTIPLY", flm, nb.math("SUBTRACT", 1.0, nb.math("MAXIMUM", fj, crack))),
                             nb.math("ADD", nb.math("MULTIPLY", I["cobble"], nb.ramp(cbd, 0.0, 0.07)),
                                     nb.math("MULTIPLY", I["plates"], nb.math("SUBTRACT", nb.math("MULTIPLY", tread, 0.3), pj)))))
    bump_h = nb.math("MULTIPLY", bump_h, nb.math("SUBTRACT", 1.0, pmask))
elif THEME == "railyard":
    # a railway yard: cinder ground with ash grains and clinker, weeds in patches, black coal dust round the staithes;
    # ballast beds under the tracks (the oil drips down their middle, rust beside the rails); flagged goods platforms
    # under the crates; a turntable pit ringed with coping stones; the roads packed ash and cinder, rutted, puddled in
    # the ruts, planked across where the tracks cross them, the fast lanes cobbled with granite setts
    obj = nb.uvn.outputs["Object"]
    c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.19, 0.175, 0.16), (0.27, 0.245, 0.22))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.6, 0.74), 0.45), c, (0.3, 0.25, 0.19))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(34.0, "Distance"), 0.24, 0.07), 0.4), c, (0.4, 0.37, 0.33))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(15.0, "Color"), 0.82, 0.97), 0.5), c, (0.08, 0.075, 0.07))
    c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.15, 0.14, 0.13), (0.21, 0.19, 0.17)))
    wc = nb.mix(nb.ramp(nb.noise(6.0, 3, 0.6), 0.3, 0.7), (0.17, 0.19, 0.09), (0.28, 0.3, 0.14))
    wc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(14.0, 2, 0.6), 0.55, 0.7), 0.6), wc, (0.24, 0.21, 0.15))   # (dead stems)
    c = nb.mix(nb.math("MULTIPLY", I["weeds"], nb.math("MULTIPLY", nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.6), 0.75)), c, wc)
    coalc = nb.mix(nb.ramp(fine, 0.3, 0.7), (0.035, 0.035, 0.04), (0.09, 0.09, 0.095))
    c = nb.mix(nb.math("MULTIPLY", I["coal"], 0.93), c, coalc)
    # ballast: broken stone, each its own shade, dark between; oil down the middle; rust along the rails; weeds
    bsd = nb.voronoi(28.0, "Distance", "DISTANCE_TO_EDGE")
    bal = nb.mix(nb.ramp(nb.voronoi(28.0, "Color"), 0.2, 0.8), (0.33, 0.31, 0.28), (0.52, 0.49, 0.45))
    bal = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(2.0, 3, 0.6), 0.5, 0.7), 0.4), bal, (0.25, 0.22, 0.19))
    bal = nb.mix(nb.ramp(bsd, 0.05, 0.01), bal, (0.12, 0.11, 0.1))
    bal = nb.mix(nb.math("MULTIPLY", I["drip"], 0.75), bal, (0.09, 0.08, 0.075))
    rr = nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("ABSOLUTE", tsd), 0.31)), 0.09, 0.02)
    bal = nb.mix(nb.math("MULTIPLY", rr, 0.45), bal, (0.36, 0.2, 0.12))
    bal = nb.mix(nb.math("MULTIPLY", I["weeds"], 0.35), bal, wc)
    bal = nb.mix(nb.math("MULTIPLY", I["coal"], 0.6), bal, coalc)
    c = nb.mix(I["ballast"], c, bal)
    # goods platforms: big flags, a kerb of long stones round their edge
    pj_, pr_ = nb.brick(obj, 0.5, 0.42, 0.012, 0.2)
    pdc = nb.mix(pr_, (0.4, 0.38, 0.34), (0.52, 0.49, 0.44))
    pdc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(3.0, 3, 0.6), 0.5, 0.75), 0.45), pdc, (0.22, 0.2, 0.18))
    pdc = nb.mix(pj_, pdc, (0.1, 0.095, 0.09))
    pdc = nb.mix(nb.ramp(I["pads"], 0.62, 0.55), pdc, (0.58, 0.56, 0.52))
    pdc = nb.mix(nb.ramp(I["pads"], 0.1, 0.03), pdc, (0.1, 0.095, 0.09))
    c = nb.mix(nb.ramp(I["pads"], 0.0, 0.06), c, pdc)
    # the turntable: dressed coping stones round a dark wet pit
    cj, cr_ = nb.brick(nb.vec(I["tt_u"], 0.5), 1.0, 10.0, 0.04, 0.2, offset=0.0, freq=1)
    cpc = nb.mix(cr_, (0.46, 0.44, 0.4), (0.58, 0.55, 0.5))
    cpc = nb.mix(cj, cpc, (0.12, 0.11, 0.1))
    c = nb.mix(I["coping"], c, cpc)
    pitc = nb.mix(nb.ramp(nb.noise(4.0, 3, 0.6), 0.3, 0.7), (0.08, 0.075, 0.07), (0.14, 0.13, 0.12))
    c = nb.mix(I["pit"], c, pitc)
    # the roads: packed ash and cinder, gravel in it, rutted; puddles in the ruts
    trk = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.4, 0.38, 0.35), (0.49, 0.46, 0.42))
    trk = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(32.0, "Distance"), 0.22, 0.08), 0.35), trk, (0.27, 0.25, 0.23))
    trk = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(13.0, "Color"), 0.85, 0.97), 0.4), trk, (0.56, 0.53, 0.48))
    trk = nb.mix(nb.math("MULTIPLY", rut_m, nb.mixf(nb.ramp(nb.noise(2.2, 2, 0.6), 0.3, 0.7), 0.35, 0.6)), trk, (0.29, 0.27, 0.24))
    pmask = nb.ramp(I["puddle"], 0.45, 0.6)
    trk = nb.mix(nb.math("MULTIPLY", nb.ramp(I["puddle"], 0.0, 0.45), 0.6), trk, (0.22, 0.2, 0.18))
    pud = nb.mix(nb.ramp(nb.noise(0.8, 2, 0.5), 0.3, 0.7), (0.19, 0.2, 0.22), (0.29, 0.3, 0.33))         # (the sky in them)
    pud = nb.mix(nb.math("MULTIPLY", nb.ramp(I["puddle"], 0.62, 0.5), 0.8), pud, (0.12, 0.11, 0.1))
    trk = nb.mix(pmask, trk, pud)
    # the fast lanes: granite setts
    sj, sr_ = nb.brick(nb.vec(rsd, ral), 0.21, 0.115, 0.014, 0.35)
    st = nb.mix(sr_, (0.4, 0.4, 0.41), (0.55, 0.54, 0.53))
    st = nb.mix(nb.math("MULTIPLY", rut_m, 0.4), st, (0.6, 0.6, 0.6))
    st = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.math("ABSOLUTE", rsd), HALF - 0.4, HALF), 0.4), st, (0.22, 0.21, 0.2))
    st = nb.mix(sj, st, (0.1, 0.095, 0.09))
    trk = nb.mix(lane_m, trk, st)
    # level crossings: timber boards laid along the track, inside and outside the rails
    bj, br2 = nb.brick(nb.vec(tal, nb.math("ADD", tsd, 0.065)), 2.6, 0.13, 0.01, 0.1)
    bdc = nb.mix(br2, (0.3, 0.24, 0.18), (0.45, 0.37, 0.28))
    bdc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(3.0, 3, 0.6), 0.5, 0.72), 0.5), bdc, (0.5, 0.47, 0.42))
    bdc = nb.mix(bj, bdc, (0.08, 0.07, 0.06))
    trk = nb.mix(I["xing"], trk, bdc)
    c = nb.mix(nb.math("MULTIPLY", edge_m, 0.5), c, (0.13, 0.12, 0.11))
    c = nb.mix(road_m, c, trk)
    rough = nb.mixf(nb.math("MULTIPLY", pmask, road_m), nb.mixf(I["pit"], 0.9, 0.5), 0.08)
    bump_h = nb.math("ADD", nb.math("MULTIPLY", I["ballast"], nb.ramp(bsd, 0.0, 0.06)),
                     nb.math("ADD", nb.math("MULTIPLY", nb.math("MULTIPLY", road_m, lane_m), nb.math("SUBTRACT", 1.0, sj)),
                             nb.math("MULTIPLY", I["xing"], nb.math("SUBTRACT", 1.0, bj))))
elif THEME == "smog":
    # a smog-choked Victorian city: setts between granite kerbs, flagged pavements, gully grates in the gutters, manhole
    # covers; yards (flags, cobbles, brick paving, bare earth, cinder waste ground with weeds) between low brick walls;
    # back lanes cobbled with a gutter down the middle; dock pools of murky water behind coping stones in a quay of
    # setts; soot over everything, puddles
    obj = nb.uvn.outputs["Object"]
    ox_, oy_ = nb.xyz()
    pid = I["pid"]
    swap = nb.ramp(pid, 0.49, 0.51)                                  # (half the yards laid the other way)
    pv = nb.vec(nb.math("ADD", nb.mixf(swap, ox_, oy_), nb.math("MULTIPLY", pid, 7.3)),
                nb.math("ADD", nb.mixf(swap, oy_, ox_), nb.math("MULTIPLY", pid, 3.1)))
    grime = nb.ramp(nb.noise(3.5, 3, 0.6), 0.45, 0.75)
    # waste ground: cinder, rubble, weeds
    c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.17, 0.16, 0.15), (0.24, 0.22, 0.2))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(34.0, "Distance"), 0.24, 0.07), 0.35), c, (0.36, 0.33, 0.3))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.6, 3, 0.6), 0.55, 0.68), 0.7), c,
               nb.mix(nb.ramp(nb.noise(7.0, 3, 0.6), 0.3, 0.7), (0.17, 0.21, 0.09), (0.27, 0.31, 0.13)))   # weeds
    # flagged yards
    fj, fr_ = nb.brick(pv, 0.56, 0.42, 0.012, 0.2)
    flc = nb.mix(fr_, (0.29, 0.27, 0.24), (0.46, 0.43, 0.38))
    flc = nb.mix(nb.math("MULTIPLY", grime, 0.65), flc, (0.15, 0.14, 0.13))
    crk = nb.math("MULTIPLY", nb.ramp(nb.voronoi(3.4, "Distance", "DISTANCE_TO_EDGE"), 0.012, 0.0), nb.ramp(fr_, 0.55, 0.65))
    fj = nb.math("MAXIMUM", fj, crk)
    flc = nb.mix(fj, flc, (0.07, 0.065, 0.06))
    c = nb.mix(I["y_flags"], c, flc)
    # cobbled yards
    cbd = nb.voronoi(10.0, "Distance", "DISTANCE_TO_EDGE")
    cbc = nb.mix(nb.ramp(nb.voronoi(10.0, "Color"), 0.2, 0.8), (0.26, 0.25, 0.25), (0.4, 0.38, 0.36))
    cbc = nb.mix(nb.math("MULTIPLY", grime, 0.45), cbc, (0.15, 0.14, 0.13))
    cbc = nb.mix(nb.ramp(cbd, 0.06, 0.015), cbc, (0.07, 0.065, 0.06))
    c = nb.mix(I["y_cobble"], c, cbc)
    # brick-paved yards
    bj_, br_ = nb.brick(pv, 0.23, 0.08, 0.008, 0.2)
    bkc = nb.mix(br_, (0.23, 0.13, 0.095), (0.35, 0.19, 0.13))
    bkc = nb.mix(nb.math("MULTIPLY", grime, 0.75), bkc, (0.12, 0.09, 0.08))
    bkc = nb.mix(bj_, bkc, (0.13, 0.11, 0.1))
    c = nb.mix(I["y_brick"], c, bkc)
    # bare trodden earth
    ec = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.24, 0.2, 0.16), (0.32, 0.27, 0.21))
    ec = nb.mix(nb.math("MULTIPLY", grime, 0.5), ec, (0.14, 0.12, 0.1))
    c = nb.mix(I["y_earth"], c, ec)
    # quays: granite setts, square to the world
    qj, qr = nb.brick(obj, 0.15, 0.12, 0.011, 0.4)
    qc = nb.mix(qr, (0.27, 0.27, 0.28), (0.46, 0.45, 0.44))
    qc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(30.0, 2, 0.5), 0.55, 0.75), 0.25), qc, (0.55, 0.54, 0.52))
    qc = nb.mix(nb.math("MULTIPLY", grime, 0.6), qc, (0.15, 0.145, 0.14))
    qc = nb.mix(qj, qc, (0.09, 0.085, 0.08))
    c = nb.mix(I["y_quay"], c, qc)
    # back lanes: small cobbles, a gutter of setts down the middle
    lnd = nb.voronoi(13.0, "Distance", "DISTANCE_TO_EDGE")
    lnc = nb.mix(nb.ramp(nb.voronoi(13.0, "Color"), 0.2, 0.8), (0.26, 0.25, 0.24), (0.38, 0.36, 0.34))
    lnc = nb.mix(nb.ramp(lnd, 0.06, 0.015), lnc, (0.07, 0.065, 0.06))
    lnc = nb.mix(nb.ramp(I["lane"], 0.8, 0.86), lnc, (0.14, 0.135, 0.13))
    c = nb.mix(nb.ramp(I["lane"], 0.0, 0.04), c, lnc)
    c = nb.mix(nb.math("MULTIPLY", I["wall"], 0.45), c, (0.08, 0.075, 0.07))                    # soot at the walls' feet
    # the docks: coping stones round murky water
    cop = I["coping"]
    cj, cr_ = nb.brick(nb.vec(I["cope_u"], 0.5), 0.46, 10.0, 0.016, 0.2, offset=0.0, freq=1)
    cpc = nb.mix(cr_, (0.52, 0.5, 0.45), (0.64, 0.61, 0.55))
    cpc = nb.mix(nb.math("MULTIPLY", grime, 0.3), cpc, (0.34, 0.32, 0.29))
    cpc = nb.mix(nb.math("MAXIMUM", cj, nb.ramp(cop, 0.12, 0.04)), cpc, (0.08, 0.075, 0.07))       # joints, the outer joint
    cpc = nb.mix(nb.ramp(cop, 0.84, 0.95), cpc, (0.2, 0.19, 0.17))                                  # its rounded inner edge
    c = nb.mix(nb.ramp(cop, 0.0, 0.03), c, cpc)
    wat = nb.mix(nb.ramp(nb.noise(1.2, 3, 0.6), 0.3, 0.7), (0.1, 0.15, 0.14), (0.16, 0.22, 0.2))
    wat = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(2.5, 2, 0.5, distort=2.0), 0.62, 0.72), 0.35), wat, (0.26, 0.24, 0.28))   # oil on it
    wat = nb.mix(nb.math("MULTIPLY", nb.ramp(I["water"], 0.35, 0.0), 0.7), wat, (0.04, 0.06, 0.055))            # the wall's shadow
    c = nb.mix(nb.ramp(I["water"], 0.0, 0.02), c, wat)
    # the streets: granite kerbs, flagged pavements (rows parallel to the kerb), setts, the gutter and its grates
    ars = nb.math("ABSOLUTE", rsd)
    pj, pr2 = nb.brick(nb.vec(ral, nb.math("SUBTRACT", ars, 0.15)), 0.52, 0.4, 0.012, 0.2)
    pvc = nb.mix(pr2, (0.44, 0.42, 0.38), (0.56, 0.53, 0.48))
    pvc = nb.mix(nb.math("MULTIPLY", grime, 0.45), pvc, (0.26, 0.25, 0.23))
    pvc = nb.mix(pj, pvc, (0.12, 0.115, 0.11))
    c = nb.mix(I["pave"], c, pvc)
    kj, kr = nb.brick(nb.vec(ral, ars), 0.62, 10.0, 0.012, 0.2, offset=0.0, freq=1)
    kbc = nb.mix(kr, (0.55, 0.54, 0.51), (0.64, 0.62, 0.58))
    kbc = nb.mix(kj, kbc, (0.18, 0.17, 0.16))
    c = nb.mix(nb.ramp(I["kerb"], 0.3, 0.5), c, kbc)
    sj, sr_ = nb.brick(nb.vec(rsd, ral), 0.2, 0.11, 0.013, 0.35)
    st = nb.mix(sr_, (0.3, 0.29, 0.29), (0.43, 0.41, 0.4))
    st = nb.mix(nb.math("MULTIPLY", rut_m, 0.35), st, (0.46, 0.45, 0.44))
    st = nb.mix(nb.math("MULTIPLY", grime, 0.4), st, (0.16, 0.15, 0.15))
    st = nb.mix(sj, st, (0.07, 0.065, 0.06))
    st = nb.mix(nb.math("MULTIPLY", I["gutter"], 0.6), st, (0.13, 0.125, 0.12))
    grc = nb.mix(nb.ramp(nb.seam(ral, 0.05), 0.012, 0.006), (0.05, 0.05, 0.055), (0.2, 0.2, 0.21))
    st = nb.mix(I["grate"], st, grc)
    c = nb.mix(road_m, c, st)
    # manhole covers: an iron disc, rings cast in it, a dark rim
    mh = I["manhole"]
    mhc = nb.mix(nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", mh, 4.0)), 0.5)), 0.12, 0.25),
                 (0.24, 0.24, 0.25), (0.12, 0.12, 0.13))
    mhc = nb.mix(nb.ramp(mh, 0.12, 0.06), mhc, (0.05, 0.05, 0.05))
    c = nb.mix(nb.ramp(mh, 0.0, 0.03), c, mhc)
    # soot and puddles over everything
    c = nb.mix(nb.math("MULTIPLY", I["soot"], 0.5), c, (0.05, 0.05, 0.05))
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(0.5, 3, 0.6), 0.5, 0.7), 0.3), c, (0.09, 0.09, 0.08))   # smoke-darkened
    pmask = nb.ramp(I["puddle"], 0.45, 0.6)
    c = nb.mix(nb.math("MULTIPLY", nb.ramp(I["puddle"], 0.0, 0.45), 0.5), c, (0.1, 0.1, 0.1))
    pud = nb.mix(nb.ramp(nb.noise(0.8, 2, 0.5), 0.3, 0.7), (0.17, 0.18, 0.19), (0.27, 0.28, 0.3))      # (the sky in them)
    pud = nb.mix(nb.math("MULTIPLY", nb.ramp(I["puddle"], 0.62, 0.5), 0.8), pud, (0.1, 0.1, 0.1))
    c = nb.mix(pmask, c, pud)
    wmask = nb.ramp(I["water"], 0.0, 0.02)
    rough = nb.mixf(nb.math("MAXIMUM", pmask, wmask), nb.mixf(I["manhole"], 0.88, 0.5), 0.07)
    bump_h = nb.math("ADD", nb.math("MULTIPLY", road_m, nb.math("SUBTRACT", 1.0, sj)),
                     nb.math("ADD", nb.math("MULTIPLY", I["pave"], nb.math("SUBTRACT", 1.0, pj)),
                             nb.math("ADD", nb.math("MULTIPLY", I["y_flags"], nb.math("SUBTRACT", 1.0, fj)),
                                     nb.math("ADD", nb.math("MULTIPLY", I["y_cobble"], nb.ramp(cbd, 0.0, 0.07)),
                                             nb.math("MULTIPLY", I["y_quay"], nb.math("SUBTRACT", 1.0, qj))))))
    bump_h = nb.math("MULTIPLY", bump_h, nb.math("SUBTRACT", 1.0, nb.math("MAXIMUM", pmask, wmask)))
elif MOD_T or DIG_T:
    obj = nb.uvn.outputs["Object"]
    ox_, oy_ = nb.xyz()

    def asphalt(lo, hi, wear=0.3):
        """Asphalt: aggregate speckled through it, the wheel tracks worn paler, cracks sealed with black tar."""
        a_ = nb.mix(nb.ramp(mid, 0.3, 0.7), lo, hi)
        a_ = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(42.0, "Distance"), 0.2, 0.07), 0.35), a_, tuple(min(1, v * 1.55) for v in hi))
        a_ = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(30.0, 2, 0.5), 0.6, 0.75), 0.3), a_, tuple(v * 0.7 for v in lo))
        a_ = nb.mix(nb.math("MULTIPLY", rut_m, wear), a_, tuple(min(1, v * 1.22) for v in hi))
        seal = nb.math("MULTIPLY", nb.ramp(nb.voronoi(1.1, "Distance", "DISTANCE_TO_EDGE"), 0.011, 0.002),
                       nb.ramp(nb.noise(1.8, 3, 0.6), 0.56, 0.64))
        return nb.mix(nb.math("MULTIPLY", seal, 0.85), a_, (0.06, 0.06, 0.065)), seal

    def paint(c_, white=(0.9, 0.9, 0.88), yellow=(0.9, 0.7, 0.12), red=(0.72, 0.13, 0.1), worn=0.35):
        wear = nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", nb.ramp(nb.noise(7.0, 3, 0.6), 0.5, 0.78), worn))
        c_ = nb.mix(pk_m, c_, (0.05, 0.05, 0.055))
        c_ = nb.mix(nb.math("MULTIPLY", pw_m, wear), c_, white)
        c_ = nb.mix(nb.math("MULTIPLY", py_m, wear), c_, yellow)
        return nb.mix(nb.math("MULTIPLY", pr_m, wear), c_, red)

    if THEME == "military":
        # an airbase: olive airfield turf mown in stripes; concrete slabs (apron, taxiways, pads, hardstands) with sealed
        # joints, patched slabs, cracks and oil; the runway paler, its slabs long, grooved across; asphalt roads; paint;
        # hazard stripes round the machines' pads; craters of raw earth, the turf and concrete scorched round them
        c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.33, 0.39, 0.17), (0.42, 0.47, 0.22))
        c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.62, 0.76), 0.55), c, (0.52, 0.5, 0.28))           # dry straw patches
        c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.36, 0.24), 0.45), c, (0.27, 0.35, 0.14))         # lush hollows
        c = nb.mix(nb.math("MULTIPLY", I["mow"], 0.3), c, (0.5, 0.55, 0.28))                          # mower stripes
        clover = nb.ramp(nb.voronoi(9.0, "Distance"), 0.17, 0.07)
        c = nb.mix(nb.math("MULTIPLY", clover, nb.math("MULTIPLY", nb.ramp(big, 0.55, 0.7), 0.3)), c, (0.3, 0.42, 0.16))
        c = nb.mix(nb.math("MULTIPLY", fine, 0.2), c, (0.5, 0.52, 0.3))
        c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.3, 0.35, 0.16), (0.38, 0.42, 0.2)))
        c = nb.mix(nb.math("MULTIPLY", edge_m, 0.35), c, (0.3, 0.3, 0.2))
        sj, sr_ = nb.brick(obj, 1.0, 1.0, 0.012, 0.25, offset=0.0, freq=1)
        cc = nb.mix(sr_, (0.5, 0.5, 0.48), (0.61, 0.6, 0.57))
        cc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(3.5, 3, 0.6), 0.5, 0.75), 0.4), cc, (0.41, 0.4, 0.37))
        cc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(28.0, 2, 0.5), 0.55, 0.75), 0.22), cc, (0.7, 0.69, 0.66))
        cc = nb.mix(nb.math("MULTIPLY", nb.ramp(sr_, 0.93, 0.95), 0.75), cc, (0.43, 0.43, 0.42))      # patched slabs
        crack = nb.math("MULTIPLY", nb.ramp(nb.voronoi(1.2, "Distance", "DISTANCE_TO_EDGE"), 0.009, 0.0), nb.ramp(sr_, 0.1, 0.07))
        cj = nb.math("MAXIMUM", sj, crack)
        cc = nb.mix(cj, cc, (0.16, 0.16, 0.16))
        cc = nb.mix(nb.math("MULTIPLY", I["oil"], nb.ramp(nb.noise(6.0, 3, 0.6), 0.25, 0.6)), cc, (0.17, 0.165, 0.16))
        c = nb.mix(I["conc"], c, cc)
        rj, rr_ = nb.brick(obj, 1.5, 0.35, 0.007, 0.2, offset=0.0, freq=1)
        rc = nb.mix(rr_, (0.57, 0.57, 0.55), (0.64, 0.63, 0.6))
        rc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(3.0, 3, 0.6), 0.5, 0.75), 0.35), rc, (0.48, 0.47, 0.45))
        groove = nb.ramp(nb.math("ABSOLUTE", nb.math("SINE", nb.math("MULTIPLY", ox_, 95.0))), 0.85, 1.0)
        rc = nb.mix(nb.math("MULTIPLY", groove, 0.12), rc, (0.42, 0.42, 0.41))
        rc = nb.mix(rj, rc, (0.25, 0.25, 0.25))
        c = nb.mix(I["rwy"], c, rc)
        asp, seal = asphalt((0.16, 0.16, 0.17), (0.23, 0.23, 0.24))
        c = nb.mix(I["blast"], c, asp)
        c = nb.mix(road_m, c, asp)
        hz = nb.ramp(nb.math("SINE", nb.math("MULTIPLY", nb.math("ADD", ox_, oy_), math.pi / 0.11)), -0.08, 0.08)
        c = nb.mix(I["haz"], c, nb.mix(hz, (0.07, 0.07, 0.07), (0.86, 0.66, 0.1)))
        c = paint(c)
        c = nb.mix(nb.math("MULTIPLY", nb.ramp(I["scorch"], 0.0, 0.7), 0.94), c, nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.035, 0.03, 0.028), (0.1, 0.085, 0.07)))
        bowl = nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.15, 0.11, 0.08), (0.26, 0.2, 0.14))
        bowl = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(18.0, "Distance"), 0.2, 0.08), 0.45), bowl, (0.4, 0.33, 0.25))
        c = nb.mix(nb.math("MULTIPLY", I["rim"], 0.75), c, (0.33, 0.27, 0.19))
        c = nb.mix(nb.ramp(I["crater"], 0.02, 0.2), c, bowl)
        pave = nb.math("MAXIMUM", I["conc"], nb.math("MAXIMUM", I["rwy"], road_m))
        rough = nb.mixf(pave, 0.92, nb.mixf(nb.math("MULTIPLY", I["oil"], I["conc"]), 0.78, 0.35))
        bump_h = nb.math("ADD", nb.math("MULTIPLY", I["conc"], nb.math("SUBTRACT", 1.0, cj)),
                         nb.math("ADD", nb.math("MULTIPLY", I["rwy"], nb.math("SUBTRACT", 1.0, rj)),
                                 nb.math("MULTIPLY", road_m, nb.math("SUBTRACT", 0.0, seal))))
    elif THEME == "metro":
        # a city centre at night (kept light enough to read): lots of granite tiles, concrete slabs, brick pavers,
        # parking, lawns with planted beds, slate; dark granite bands between them; polished plinths under the buildings;
        # the plaza's pale stone in a grid of dark granite bands, its round inlaid motif and raised planters; sidewalks of
        # concrete slabs with tree pits, granite kerbs; asphalt avenues, red bus lanes, a brick table at the crossroads,
        # manholes; paint
        pid = I["pid"]
        swap = nb.ramp(pid, 0.49, 0.51)
        pv = nb.vec(nb.math("ADD", nb.mixf(swap, ox_, oy_), nb.math("MULTIPLY", pid, 7.3)),
                    nb.math("ADD", nb.mixf(swap, oy_, ox_), nb.math("MULTIPLY", pid, 3.1)))
        grime = nb.math("MULTIPLY", nb.ramp(nb.noise(3.5, 3, 0.6), 0.45, 0.75), nb.mixf(I["grime"], 0.4, 1.0))
        c = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.47, 0.47, 0.45), (0.55, 0.55, 0.52))                    # (plain concrete)
        tj, tr_ = nb.brick(pv, 0.5, 0.5, 0.01, 0.2)
        tc = nb.mix(tr_, (0.55, 0.55, 0.53), (0.66, 0.65, 0.62))
        tc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(40.0, 2, 0.5), 0.55, 0.72), 0.35), tc, (0.42, 0.42, 0.42))   # speckle
        tc = nb.mix(nb.math("MULTIPLY", grime, 0.35), tc, (0.42, 0.41, 0.39))
        tc = nb.mix(tj, tc, (0.3, 0.3, 0.3))
        c = nb.mix(I["l_tile"], c, tc)
        cj_, cr_ = nb.brick(pv, 1.0, 1.0, 0.01, 0.2, offset=0.0, freq=1)
        ccn = nb.mix(cr_, (0.5, 0.5, 0.48), (0.58, 0.57, 0.54))
        ccn = nb.mix(nb.math("MULTIPLY", grime, 0.45), ccn, (0.38, 0.37, 0.35))
        ccn = nb.mix(cj_, ccn, (0.27, 0.27, 0.27))
        c = nb.mix(I["l_conc"], c, ccn)
        bj, br_ = nb.brick(pv, 0.2, 0.1, 0.008, 0.2)
        bc = nb.mix(br_, (0.42, 0.25, 0.19), (0.54, 0.34, 0.25))
        bc = nb.mix(nb.math("MULTIPLY", grime, 0.4), bc, (0.33, 0.22, 0.17))
        bc = nb.mix(bj, bc, (0.3, 0.26, 0.22))
        c = nb.mix(I["l_brick"], c, bc)
        lot_asp, _s = asphalt((0.2, 0.2, 0.21), (0.27, 0.27, 0.28), 0.0)
        lot_asp = nb.mix(nb.math("MULTIPLY", I["oil"], 0.5), lot_asp, (0.12, 0.12, 0.12))
        c = nb.mix(I["l_lot"], c, lot_asp)
        sj_, sr2 = nb.brick(pv, 0.6, 0.3, 0.008, 0.2)
        slc = nb.mix(sr2, (0.29, 0.3, 0.32), (0.37, 0.38, 0.4))
        slc = nb.mix(sj_, slc, (0.18, 0.18, 0.19))
        c = nb.mix(I["l_slate"], c, slc)
        grass = nb.mix(nb.ramp(nb.noise(2.0, 3, 0.6), 0.3, 0.7), (0.25, 0.4, 0.15), (0.34, 0.5, 0.2))
        grass = nb.mix(nb.math("MULTIPLY", fine, 0.25), grass, (0.4, 0.55, 0.24))
        c = nb.mix(I["l_lawn"], c, grass)
        pj_, pr3 = nb.brick(obj, 0.3, 0.3, 0.012, 0.2)
        lpc = nb.mix(pr3, (0.55, 0.53, 0.5), (0.65, 0.62, 0.58))
        lpc = nb.mix(pj_, lpc, (0.32, 0.36, 0.22))
        c = nb.mix(I["lpath"], c, lpc)
        mulch = nb.mix(nb.ramp(nb.voronoi(40.0, "Color"), 0.2, 0.8), (0.17, 0.1, 0.06), (0.3, 0.19, 0.11))
        mulch = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(5.0, 3, 0.6), 0.55, 0.7), 0.6), mulch, (0.24, 0.32, 0.13))   # ground cover
        c = nb.mix(I["beds"], c, mulch)
        c = nb.mix(nb.math("MULTIPLY", I["bedk"], 0.85), c, (0.6, 0.6, 0.58))
        c = nb.mix(nb.math("MULTIPLY", I["lotb"], 0.9), c, (0.36, 0.36, 0.37))
        plj, plr = nb.brick(obj, 0.8, 0.8, 0.006, 0.2, offset=0.0, freq=1)
        pc = nb.mix(plr, (0.16, 0.16, 0.18), (0.24, 0.24, 0.27))
        pc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(12.0, 3, 0.5), 0.55, 0.7), 0.4), pc, (0.34, 0.34, 0.37))
        pc = nb.mix(plj, pc, (0.42, 0.42, 0.44))
        c = nb.mix(I["plinth"], c, pc)
        # the plaza: pale limestone slabs, a band of dark granite every fourth joint, the round motif, planters
        qj, qr = nb.brick(obj, 0.6, 0.6, 0.008, 0.2, offset=0.0, freq=1)
        qc = nb.mix(qr, (0.66, 0.63, 0.57), (0.75, 0.72, 0.66))
        qc = nb.mix(nb.math("MULTIPLY", grime, 0.25), qc, (0.56, 0.53, 0.48))
        qc = nb.mix(qj, qc, (0.45, 0.43, 0.4))
        band = nb.math("MAXIMUM", nb.ramp(nb.seam(nb.math("ADD", ox_, 0.9), 2.4), 0.07, 0.055), nb.ramp(nb.seam(nb.math("ADD", oy_, 0.0), 2.4), 0.07, 0.055))
        qc = nb.mix(band, qc, (0.25, 0.25, 0.27))
        rr4 = I["pl_r"]
        ringc = nb.mix(nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", rr4, 4.8)), 0.5)), 0.2, 0.26),
                       (0.28, 0.27, 0.3), (0.8, 0.77, 0.7))
        fa8 = nb.math("FRACT", nb.math("MULTIPLY", I["pl_a"], 8.0))
        star = nb.math("ABSOLUTE", nb.math("SUBTRACT", fa8, 0.5))          # 0 down each point's middle, 0.5 between
        starm = nb.ramp(nb.math("SUBTRACT", rr4, nb.math("ADD", 0.12, nb.math("MULTIPLY", nb.math("SUBTRACT", 0.5, star), 1.15))), 0.012, -0.012)
        ringc = nb.mix(starm, ringc, nb.mix(nb.ramp(fa8, 0.49, 0.51), (0.62, 0.43, 0.25), (0.33, 0.31, 0.35)))
        qc = nb.mix(nb.ramp(rr4, 0.83, 0.82), qc, ringc)
        pl_rim = nb.ramp(I["planter"], 0.0, 0.5)
        qc = nb.mix(pl_rim, qc, (0.3, 0.3, 0.32))
        c = nb.mix(I["plaza"], c, qc)
        c = nb.mix(nb.math("MULTIPLY", I["planter"], nb.ramp(I["planter"], 0.6, 0.95)), c, mulch)
        # sidewalks and kerbs, tree pits with iron grates
        sc_ = nb.mix(nb.ramp(nb.noise(2.5, 3, 0.6), 0.3, 0.7), (0.56, 0.56, 0.54), (0.64, 0.64, 0.61))
        sc_ = nb.mix(nb.math("MULTIPLY", grime, 0.3), sc_, (0.45, 0.45, 0.43))
        gum = nb.ramp(nb.voronoi(14.0, "Distance"), 0.035, 0.02)
        sc_ = nb.mix(nb.math("MULTIPLY", gum, nb.math("MULTIPLY", nb.ramp(nb.noise(3.0, 2, 0.5), 0.5, 0.7), 0.6)), sc_, (0.33, 0.33, 0.33))
        c = nb.mix(I["side"], c, sc_)
        grate = nb.mix(nb.ramp(nb.math("MINIMUM", nb.seam(ox_, 0.045), nb.seam(oy_, 0.045)), 0.008, 0.004), (0.1, 0.07, 0.05), (0.2, 0.2, 0.21))
        c = nb.mix(I["pit"], c, grate)
        c = nb.mix(I["kerb"], c, nb.mix(nb.ramp(nb.noise(8.0, 2, 0.5), 0.3, 0.7), (0.6, 0.6, 0.59), (0.72, 0.72, 0.7)))
        # the carriageway: asphalt, red bus lanes, the brick table, manholes, paint
        asp, seal = asphalt((0.17, 0.17, 0.18), (0.24, 0.24, 0.25))
        busc = nb.mix(nb.ramp(nb.noise(2.0, 3, 0.6), 0.3, 0.7), (0.33, 0.13, 0.115), (0.41, 0.165, 0.14))
        busc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(6.0, 3, 0.6), 0.6, 0.75), 0.6), busc, asp)       # worn through
        busc = nb.mix(nb.math("MULTIPLY", rut_m, 0.35), busc, (0.3, 0.13, 0.11))
        asp = nb.mix(I["bus"], asp, busc)
        hj, hr = nb.brick(obj, 0.22, 0.11, 0.009, 0.2)
        hc = nb.mix(hr, (0.44, 0.24, 0.17), (0.56, 0.33, 0.23))
        hc = nb.mix(nb.math("MULTIPLY", rut_m, 0.3), hc, (0.36, 0.24, 0.19))
        hc = nb.mix(hj, hc, (0.27, 0.22, 0.19))
        asp = nb.mix(I["tbl"], asp, hc)
        mh = I["mh"]
        mhc = nb.mix(nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", mh, 5.0)), 0.5)), 0.12, 0.25),
                     (0.27, 0.27, 0.28), (0.13, 0.13, 0.14))
        asp = nb.mix(nb.ramp(mh, 0.0, 0.04), asp, nb.mix(nb.ramp(mh, 0.12, 0.06), mhc, (0.06, 0.06, 0.06)))
        c = nb.mix(road_m, c, asp)
        c = paint(c, worn=0.25)
        rough = nb.mixf(I["plinth"], nb.mixf(road_m, 0.86, 0.7), 0.3)
        bump_h = nb.math("ADD", nb.math("MULTIPLY", I["l_tile"], nb.math("SUBTRACT", 1.0, tj)),
                         nb.math("ADD", nb.math("MULTIPLY", I["l_brick"], nb.math("SUBTRACT", 1.0, bj)),
                                 nb.math("ADD", nb.math("MULTIPLY", I["plaza"], nb.math("SUBTRACT", 1.0, qj)),
                                         nb.math("ADD", nb.math("MULTIPLY", I["tbl"], nb.math("SUBTRACT", 1.0, hj)),
                                                 nb.math("MULTIPLY", road_m, nb.math("SUBTRACT", 0.0, seal))))))
    elif THEME == "suburb":
        # an American suburb: lawns mown in stripes, flower beds of bark mulch, concrete sidewalks, kerbs, driveways and
        # garden paths of flagstones; asphalt streets with tar-sealed cracks; travertine pool decks round a tiled coping
        # and turquoise water (its floor shallow to deep, caustics on it); the park's playground of rubber safety
        # surfacing in a timber edging, a sandpit
        c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.26, 0.45, 0.14), (0.35, 0.55, 0.19))
        c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.64, 0.76), 0.45), c, (0.45, 0.52, 0.22))         # sunburnt patches
        mca = nb.math("SUBTRACT", nb.math("MULTIPLY", I["mca"], 2.0), 1.0)
        msa = nb.math("SUBTRACT", nb.math("MULTIPLY", I["msa"], 2.0), 1.0)
        wz_ = nb.math("MULTIPLY", oy_, -1.0)                                     # (world z)
        mow = nb.ramp(nb.math("SINE", nb.math("MULTIPLY", nb.math("ADD", nb.math("MULTIPLY", ox_, mca), nb.math("MULTIPLY", wz_, msa)),
                                               2 * math.pi / 0.62)), -0.25, 0.25)
        c = nb.mix(nb.math("MULTIPLY", I["lshade"], 0.35), c, (0.4, 0.5, 0.17))                         # each lot its own
        c = nb.mix(nb.math("MULTIPLY", mow, 0.24), c, (0.43, 0.63, 0.25))                               # mower stripes
        c = nb.mix(nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, mow), 0.12), c, (0.2, 0.38, 0.11))
        clover = nb.ramp(nb.voronoi(10.0, "Distance"), 0.16, 0.07)
        c = nb.mix(nb.math("MULTIPLY", clover, nb.math("MULTIPLY", nb.ramp(big, 0.5, 0.7), 0.3)), c, (0.26, 0.48, 0.17))
        c = nb.mix(nb.math("MULTIPLY", fine, 0.18), c, (0.42, 0.6, 0.24))
        c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.22, 0.38, 0.13), (0.29, 0.45, 0.16)))
        mulch = nb.mix(nb.ramp(nb.voronoi(45.0, "Color"), 0.2, 0.8), (0.2, 0.11, 0.06), (0.36, 0.21, 0.11))
        mulch = nb.mix(nb.ramp(nb.voronoi(45.0, "Distance", "DISTANCE_TO_EDGE"), 0.05, 0.015), mulch, (0.12, 0.07, 0.04))
        c = nb.mix(I["fbed"], c, mulch)
        vrow = nb.ramp(nb.math("ABSOLUTE", nb.math("SINE", nb.math("MULTIPLY", nb.math("ADD", ox_, oy_), 28.0))), 0.55, 0.8)
        vegc = nb.mix(vrow, (0.3, 0.2, 0.12), nb.mix(nb.ramp(nb.noise(20.0, 2, 0.5), 0.4, 0.6), (0.2, 0.42, 0.12), (0.35, 0.58, 0.2)))
        c = nb.mix(I["veg"], c, nb.mix(nb.ramp(I["veg"], 0.2, 0.0), vegc, (0.55, 0.42, 0.28)))   # (a timber edge)
        conc = lambda lo, hi: nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(25.0, 2, 0.5), 0.55, 0.75), 0.25),
                                     nb.mix(nb.ramp(nb.noise(2.5, 3, 0.6), 0.3, 0.7), lo, hi), tuple(v * 0.85 for v in lo))
        dj, dr_ = nb.brick(obj, 1.0, 1.0, 0.008, 0.2, offset=0.0, freq=1)
        dc = conc((0.58, 0.57, 0.54), (0.66, 0.65, 0.62))
        dc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.4, 3, 0.6), 0.62, 0.72), 0.5), dc, (0.4, 0.39, 0.37))   # oil drips
        dc = nb.mix(nb.math("MULTIPLY", dj, 0.7), dc, (0.33, 0.33, 0.32))
        c = nb.mix(I["drive"], c, dc)
        c = nb.mix(I["side"], c, conc((0.62, 0.61, 0.58), (0.7, 0.69, 0.66)))
        fl_ = nb.voronoi(7.0, "Distance", "DISTANCE_TO_EDGE")
        flc = nb.mix(nb.ramp(nb.voronoi(7.0, "Color"), 0.2, 0.8), (0.52, 0.47, 0.4), (0.66, 0.6, 0.5))
        flc = nb.mix(nb.ramp(fl_, 0.05, 0.02), flc, (0.32, 0.4, 0.2))
        c = nb.mix(I["gpath"], c, flc)
        c = nb.mix(I["kerb"], c, (0.74, 0.73, 0.7))
        tj, tr_ = nb.brick(obj, 0.36, 0.24, 0.008, 0.2)
        tvc = nb.mix(tr_, (0.74, 0.68, 0.57), (0.84, 0.78, 0.67))
        tvc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(18.0, 2, 0.5), 0.55, 0.75), 0.35), tvc, (0.66, 0.59, 0.48))
        tvc = nb.mix(tj, tvc, (0.6, 0.56, 0.5))
        c = nb.mix(I["deck"], c, tvc)
        c = nb.mix(I["coping"], c, (0.9, 0.9, 0.87))
        cau = nb.ramp(nb.voronoi_v(nb.vec(nb.math("ADD", ox_, nb.math("MULTIPLY", nb.noise(1.5, 2, 0.5), 0.3)), oy_), 6.0, "Distance", "DISTANCE_TO_EDGE"), 0.045, 0.0)
        wfl = nb.mix(I["pdepth"], (0.42, 0.82, 0.84), (0.1, 0.48, 0.62))
        wfl = nb.mix(nb.math("MULTIPLY", cau, 0.4), wfl, (0.75, 0.97, 0.96))
        wfl = nb.mix(nb.ramp(I["wline"], 0.45, 0.55), wfl, (0.08, 0.36, 0.55))        # the waterline tiles
        c = nb.mix(I["water"], c, wfl)
        pkr = I["pk_r"]
        rub = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", pkr, 0.72)), 0.1, 0.08), 1.0), (0.66, 0.3, 0.2), (0.2, 0.42, 0.66))
        rub = nb.mix(nb.ramp(pkr, 0.36, 0.34), rub, (0.32, 0.58, 0.26))
        rub = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", pkr, 0.72)), 0.1, 0.08),
                             nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", nb.math("ADD", ox_, oy_), 1.6)), 0.5)), 0.2, 0.22)), rub, (0.95, 0.8, 0.2))
        rub = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(60.0, 2, 0.5), 0.5, 0.7), 0.3), rub, (0.2, 0.2, 0.2))
        c = nb.mix(I["play"], c, rub)
        c = nb.mix(I["playb"], c, nb.mix(nb.ramp(nb.noise(9.0, 3, 0.6), 0.3, 0.7), (0.38, 0.26, 0.15), (0.5, 0.36, 0.22)))
        c = nb.mix(I["sand"], c, nb.mix(nb.ramp(nb.noise(12.0, 3, 0.6), 0.3, 0.7), (0.78, 0.68, 0.48), (0.88, 0.8, 0.6)))
        asp, seal = asphalt((0.19, 0.19, 0.2), (0.26, 0.26, 0.27), 0.25)
        c = nb.mix(nb.math("ADD", road_m, I["cul"]), c, asp)
        c = paint(c, worn=0.3)
        wm = I["water"]
        rough = nb.mixf(wm, nb.mixf(nb.math("MAXIMUM", I["lawn"], I["fbed"]), 0.8, 0.92), 0.08)
        bump_h = nb.math("ADD", nb.math("MULTIPLY", I["deck"], nb.math("SUBTRACT", 1.0, tj)),
                         nb.math("ADD", nb.math("MULTIPLY", I["gpath"], nb.ramp(fl_, 0.0, 0.05)),
                                 nb.math("MULTIPLY", nb.math("MAXIMUM", road_m, I["cul"]), nb.math("SUBTRACT", 0.0, seal))))
        bump_h = nb.math("MULTIPLY", bump_h, nb.math("SUBTRACT", 1.0, wm))
    elif DIG_T:
        # (the Digital Age: shapes from the hi-res fields in Pn, edges antialiased over about a render pixel)
        ped_ = Pn["ped"]
        AA = 0.008
        ins = lambda d_, aa=AA: nb.ramp(d_, aa, -aa)

        def band(x, a, b, aa=AA):
            return nb.math("MULTIPLY", nb.ramp(x, a - aa, a + aa), nb.ramp(x, b + aa, b - aa))

        def ring_dots(t, a, R, t0, n, r):
            """n bolts round a ring at t0 of a disc of radius R (t: distance / R, a: angle / 2pi + 0.5)."""
            du = nb.math("MULTIPLY", nb.math("SUBTRACT", t, t0), R)
            dv = nb.math("MULTIPLY", nb.seam(a, 1.0 / n), 2 * math.pi * R * t0)
            return nb.ramp(nb.math("SQRT", nb.math("ADD", nb.math("MULTIPLY", du, du), nb.math("MULTIPLY", dv, dv))), r, r * 0.6)

        def stripes(c0, c1, period=0.22):
            st = nb.ramp(nb.math("SINE", nb.math("MULTIPLY", nb.math("ADD", ox_, oy_), 2 * math.pi / period)), -0.1, 0.1)
            return nb.mix(st, c0, c1)

        tread = nb.ramp(nb.math("ABSOLUTE", nb.math("MULTIPLY", nb.math("SINE", nb.math("MULTIPLY", nb.math("ADD", ox_, oy_), 60.0)),
                                                         nb.math("SINE", nb.math("MULTIPLY", nb.math("SUBTRACT", ox_, oy_), 60.0)))), 0.7, 0.95)
        em = nb.rgb((0.0, 0.0, 0.0))
        GIN, GOUT = (0.75, 0.3, 1.0), (0.25, 0.9, 1.0)

        def gate_plate(c_, em_, base, rim):
            """The rift ends' plates: concentric grooves, a ring lit in the rift's colour, a bright rim."""
            t = Pn["gt_r"]
            colg = nb.mix(Pn["gt_k"], GIN, GOUT)
            pl = nb.mix(nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", t, 7.0)), 0.5)), 0.08, 0.14),
                        tuple(v * 0.6 for v in base), base)
            pl = nb.mix(band(t, 0.9, 1.0, 0.01), pl, rim)
            lit = band(t, 0.7, 0.8, 0.01)
            pl = nb.mix(lit, pl, colg)
            on = ins(nb.math("SUBTRACT", t, 1.0), 0.01)
            return nb.mix(on, c_, pl), nb.mix(nb.math("MULTIPLY", lit, on), nb.mix(on, em_, (0.0, 0.0, 0.0)), colg)

        if THEME == "lab":
            # a cleanroom hall, lit indoors: bays of white epoxy, anti-static tile (conductive chips, fine seams), raised
            # floor (vent panels among the plain ones) and blue ESD epoxy between yellow safety lines; equipment bays of
            # dark tile; bar grates; checker-plate trench covers; steel plinths with hazard borders; drain pads ringed
            # with frost; green walkways; the robots' tracks: dark graphite with anti-slip grit and fine ribs, worn paler
            # where the wheels run, a steel edge, a hazard-striped border, blue-lit decontamination grilles
            YEL = (0.96, 0.76, 0.1)
            hazc = stripes((0.07, 0.07, 0.075), (0.96, 0.74, 0.08))
            sx_, sy_ = nb.seam(ox_, 0.6), nb.seam(oy_, 0.6)
            c = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.85, 0.86, 0.87), (0.91, 0.915, 0.92))
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(5.0, 3, 0.6), 0.55, 0.75), 0.3), c, (0.8, 0.81, 0.82))
            scuff = nb.math("MULTIPLY", nb.ramp(nb.noise_v(nb.vec(ox_, nb.math("MULTIPLY", oy_, 7.0)), 2.5, 3, 0.6), 0.68, 0.78), I["scuff"])
            c = nb.mix(nb.math("MULTIPLY", scuff, 0.35), c, (0.7, 0.71, 0.72))
            tj, tr_ = nb.brick(obj, 0.6, 0.6, 0.004, 0.1, offset=0.0, freq=1)
            chips = nb.ramp(nb.noise(110.0, 1, 0.5), 0.73, 0.77)
            tc = nb.mix(tr_, (0.79, 0.8, 0.81), (0.86, 0.865, 0.87))
            tc = nb.mix(nb.math("MULTIPLY", chips, 0.55), tc, (0.4, 0.41, 0.43))
            tc = nb.mix(tj, tc, (0.56, 0.57, 0.59))
            c = nb.mix(I["b_tile"], c, tc)
            rj, rr_ = nb.brick(obj, 0.6, 0.6, 0.008, 0.1, offset=0.0, freq=1)
            rc = nb.mix(rr_, (0.75, 0.76, 0.775), (0.81, 0.82, 0.83))
            vent = nb.math("MULTIPLY", nb.ramp(rr_, 0.87, 0.89), nb.ramp(nb.math("MINIMUM", sx_, sy_), 0.045, 0.055))
            holes = nb.dots(ox_, oy_, 0.045, 0.045, 0.0225, 0.012)
            rc = nb.mix(vent, rc, nb.mix(holes, (0.62, 0.64, 0.66), (0.17, 0.18, 0.21)))
            rc = nb.mix(rj, rc, (0.4, 0.41, 0.43))
            c = nb.mix(I["b_raised"], c, rc)
            ec = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.6, 0.68, 0.77), (0.66, 0.73, 0.82))
            ec = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(80.0, 1, 0.5), 0.72, 0.77), 0.5), ec, (0.84, 0.88, 0.92))
            c = nb.mix(I["b_esd"], c, ec)
            c = nb.mix(py_m, c, YEL)                                                                     # the bays' lines
            eqd = Pn["eq_d"]
            eqc = nb.mix(tr_, (0.5, 0.52, 0.56), (0.56, 0.58, 0.62))
            eqc = nb.mix(nb.math("MULTIPLY", chips, 0.4), eqc, (0.32, 0.33, 0.36))
            eqc = nb.mix(tj, eqc, (0.38, 0.39, 0.42))
            c = nb.mix(ins(eqd), c, eqc)
            gd = Pn["gr_d"]
            bars = nb.ramp(nb.seam(oy_, 0.034), 0.009, 0.005)
            grc = nb.mix(bars, (0.13, 0.14, 0.16), (0.62, 0.64, 0.67))
            grc = nb.mix(nb.ramp(gd, -0.05, -0.04), grc, (0.56, 0.58, 0.61))
            grc = nb.mix(band(gd, -0.014, 0.0), grc, (0.32, 0.33, 0.35))
            c = nb.mix(ins(gd), c, grc)
            trd, tru = Pn["tr_d"], Pn["tr_u"]
            trc = nb.mix(nb.math("MULTIPLY", tread, 0.45), (0.58, 0.6, 0.63), (0.73, 0.75, 0.78))
            slot = nb.math("MULTIPLY", nb.ramp(nb.seam(nb.math("ADD", tru, 0.3), 0.6), 0.04, 0.03), nb.ramp(trd, -0.13, -0.14))
            trc = nb.mix(slot, trc, (0.15, 0.15, 0.17))
            trc = nb.mix(nb.ramp(nb.seam(tru, 0.6), 0.009, 0.004), trc, (0.22, 0.22, 0.24))
            trc = nb.mix(band(trd, -0.03, 0.0), trc, (0.47, 0.49, 0.52))
            c = nb.mix(ins(trd), c, trc)
            pld = Pn["pl_d"]
            pj, prd = nb.brick(obj, 0.6, 0.6, 0.006, 0.1, offset=0.0, freq=1)
            plc = nb.mix(prd, (0.37, 0.39, 0.43), (0.45, 0.47, 0.51))
            plc = nb.mix(nb.math("MULTIPLY", tread, 0.3), plc, (0.56, 0.58, 0.61))
            plc = nb.mix(pj, plc, (0.2, 0.21, 0.23))
            plc = nb.mix(nb.dots(ox_, oy_, 0.6, 0.6, 0.06, 0.018), plc, (0.7, 0.72, 0.74))
            plc = nb.mix(band(pld, -0.25, -0.09), plc, hazc)
            plc = nb.mix(band(pld, -0.03, 0.0), plc, (0.64, 0.66, 0.7))
            c = nb.mix(ins(pld), c, plc)
            tk, ta = Pn["tk_r"], Pn["tk_a"]
            pdc = nb.mix(nb.ramp(nb.noise(6.0, 3, 0.6), 0.3, 0.7), (0.6, 0.63, 0.67), (0.68, 0.71, 0.75))
            pdc = nb.mix(nb.math("MAXIMUM", band(tk, 0.39, 0.41, 0.006), band(tk, 0.69, 0.71, 0.006)), pdc, (0.34, 0.36, 0.4))
            drn = nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", tk, 45.0)), 0.5)), 0.2, 0.3)
            pdc = nb.mix(nb.ramp(tk, 0.2, 0.19), pdc, nb.mix(drn, (0.08, 0.09, 0.1), (0.5, 0.52, 0.56)))
            pdc = nb.mix(band(tk, 0.94, 1.0, 0.006), pdc, (0.48, 0.5, 0.54))
            pdc = nb.mix(ring_dots(tk, ta, 1.2, 0.86, 16, 0.03), pdc, (0.78, 0.8, 0.83))
            c = nb.mix(ins(nb.math("SUBTRACT", tk, 1.0), 0.006), c, pdc)
            cry = nb.ramp(nb.voronoi(24.0, "Distance", "DISTANCE_TO_EDGE"), 0.035, 0.0)
            frc = nb.mix(cry, (0.8, 0.88, 0.96), (0.98, 0.99, 1.0))
            fr = nb.math("MULTIPLY", nb.ramp(I["frost"], 0.0, 0.8), nb.ramp(nb.noise(9.0, 3, 0.6), 0.25, 0.5))
            c = nb.mix(nb.math("MULTIPLY", fr, 0.95), c, frc)
            wkc = nb.mix(nb.ramp(nb.noise(4.0, 3, 0.6), 0.3, 0.7), (0.21, 0.55, 0.35), (0.26, 0.62, 0.41))
            c = nb.mix(Pn["g"], c, wkc)
            tkc = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.2, 0.21, 0.23), (0.25, 0.26, 0.28))
            tkc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(120.0, 1, 0.5), 0.7, 0.75), 0.5), tkc, (0.38, 0.39, 0.42))
            tkc = nb.mix(nb.math("MULTIPLY", rut_m, 0.3), tkc, (0.31, 0.32, 0.34))
            rib = nb.ramp(nb.seam(ral, 0.15), 0.008, 0.003)
            tkc = nb.mix(nb.math("MULTIPLY", rib, 0.6), tkc, (0.13, 0.135, 0.15))
            gb = nb.ramp(nb.seam(ral, 0.05), 0.013, 0.008)
            slc = nb.mix(gb, (0.5, 0.68, 0.88), (0.6, 0.62, 0.66))
            slc = nb.mix(nb.ramp(nb.seam(rsd, 0.42), 0.012, 0.006), slc, (0.42, 0.44, 0.48))
            tkc = nb.mix(Pn["sl"], tkc, slc)
            tkc = nb.mix(band(ped_, -0.075, 0.0), tkc, (0.66, 0.68, 0.72))
            tkc = nb.mix(band(ped_, -0.088, -0.072, 0.004), tkc, (0.1, 0.1, 0.11))
            c = nb.mix(ins(ped_), c, tkc)
            c = nb.mix(nb.math("MAXIMUM", band(ped_, 0.0, 0.15), Pn["hz"]), c, hazc)
            c = nb.mix(pr_m, c, YEL)
            c = nb.mix(pw_m, c, (0.95, 0.95, 0.94))
            c = nb.mix(pk_m, c, (0.05, 0.05, 0.06))
            c, em = gate_plate(c, em, (0.42, 0.44, 0.48), (0.7, 0.72, 0.76))
            stl = nb.math("MAXIMUM", ins(pld), nb.math("MAXIMUM", ins(trd), ins(gd)))
            rough = nb.mixf(stl, nb.mixf(ins(ped_), 0.5, 0.75), 0.38)
            bump_h = nb.math("ADD", nb.math("MULTIPLY", I["b_tile"], nb.math("SUBTRACT", 0.0, tj)),
                             nb.math("ADD", nb.math("MULTIPLY", I["b_raised"], nb.math("SUBTRACT", 0.0, nb.math("MAXIMUM", rj, nb.math("MULTIPLY", vent, holes)))),
                                     nb.math("ADD", nb.math("MULTIPLY", ins(gd), bars),
                                             nb.math("MULTIPLY", nb.math("MAXIMUM", ins(trd), ins(pld)), nb.math("MULTIPLY", tread, 0.4)))))
        elif THEME == "satellite":
            # a high desert at night (kept light enough to read): red-brown sand in wind ripples, dark desert pavement,
            # pale caliche; packed gravel roads with tyre ruts and tread marks, a loose berm each side, a worn white edge
            # line, sand drifting over; concrete dish foundations (grout ring, joints, a ring of anchor bolts); gravel
            # beds with a curb, footings, trench lids; the compound's concrete slabs, parking lines, a hatched box
            rip = nb.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL")
            rip.inputs["Scale"].default_value = 2.2
            rip.inputs["Distortion"].default_value = 7.0
            rip.inputs["Detail"].default_value = 3.0
            nb.link(nb.uvn.outputs["Object"], rip.inputs["Vector"])
            rp_ = rip.outputs["Fac"]
            c = nb.mix(nb.ramp(big, 0.3, 0.7), (0.5, 0.3, 0.2), (0.6, 0.38, 0.25))
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.6, 0.75), 0.45), c, (0.66, 0.46, 0.31))
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.36, 0.24), 0.4), c, (0.42, 0.24, 0.16))
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(rp_, 0.55, 0.85), 0.17), c, (0.42, 0.25, 0.16))
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(rp_, 0.15, 0.0), 0.12), c, (0.7, 0.49, 0.33))
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(45.0, "Distance"), 0.2, 0.08), 0.28), c, (0.3, 0.18, 0.12))
            pvc = nb.mix(nb.ramp(nb.voronoi(22.0, "Color"), 0.2, 0.8), (0.2, 0.13, 0.1), (0.42, 0.3, 0.22))
            pvc = nb.mix(nb.ramp(nb.voronoi(22.0, "Distance", "DISTANCE_TO_EDGE"), 0.05, 0.015), pvc, (0.5, 0.31, 0.21))
            c = nb.mix(nb.math("MULTIPLY", I["pave"], 0.85), c, pvc)
            c = nb.mix(nb.math("MULTIPLY", I["cal"], nb.ramp(nb.noise(6.0, 3, 0.6), 0.35, 0.6)), c, (0.72, 0.6, 0.47))
            c = nb.mix(out_m, c, nb.mix(nb.ramp(mid, 0.3, 0.7), (0.4, 0.24, 0.16), (0.48, 0.3, 0.2)))
            rdc = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.54, 0.45, 0.36), (0.62, 0.53, 0.43))
            rdc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(40.0, "Distance"), 0.22, 0.08), 0.4), rdc, (0.38, 0.3, 0.24))
            rdc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(60.0, 1, 0.5), 0.7, 0.75), 0.35), rdc, (0.74, 0.66, 0.56))
            tyre = nb.ramp(nb.seam(ral, 0.08), 0.016, 0.009)
            rdc = nb.mix(nb.math("MULTIPLY", rut_m, 0.6), rdc, (0.45, 0.36, 0.29))
            rdc = nb.mix(nb.math("MULTIPLY", rut_m, nb.math("MULTIPLY", tyre, nb.math("MULTIPLY", nb.ramp(nb.noise(2.0, 2, 0.5), 0.45, 0.65), 0.18))), rdc, (0.38, 0.3, 0.24))
            spd = Pn["sp_d"]
            c = nb.mix(ins(spd, 0.012), c, nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(4.0, 3, 0.6), 0.5, 0.7), 0.4), rdc, (0.5, 0.36, 0.26)))
            berm = nb.mix(nb.ramp(nb.voronoi(30.0, "Distance"), 0.25, 0.1), (0.52, 0.39, 0.29), (0.33, 0.23, 0.17))
            c = nb.mix(nb.math("MULTIPLY", I["berm"], 0.75), c, berm)
            c = nb.mix(ins(ped_), c, rdc)
            wear = nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", nb.ramp(nb.noise(5.0, 3, 0.6), 0.45, 0.75), 0.75))
            c = nb.mix(nb.math("MULTIPLY", pw_m, wear), c, (0.9, 0.88, 0.82))
            dc_ = nb.mix(nb.ramp(rp_, 0.3, 0.8), (0.62, 0.41, 0.28), (0.53, 0.33, 0.22))
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(I["drift"], 0.15, 0.7), 0.95), c, dc_)
            conc = nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.6, 0.58, 0.54), (0.68, 0.66, 0.62))
            conc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(30.0, 2, 0.5), 0.6, 0.72), 0.3), conc, (0.5, 0.48, 0.45))
            conc = nb.mix(nb.math("MULTIPLY", I["stain"], 0.35), conc, (0.46, 0.4, 0.34))
            pr_d, pa_d = Pn["pd_r"], Pn["pd_a"]
            pc = nb.mix(nb.ramp(pr_d, 0.4, 0.38), conc, (0.64, 0.63, 0.6))
            jt = nb.math("MULTIPLY", nb.ramp(nb.math("MULTIPLY", nb.seam(pa_d, 0.125), nb.math("MULTIPLY", pr_d, 7.5)), 0.012, 0.006),
                         nb.ramp(pr_d, 0.42, 0.45))
            pc = nb.mix(nb.math("MAXIMUM", jt, band(pr_d, 0.38, 0.42, 0.006)), pc, (0.36, 0.34, 0.31))
            pc = nb.mix(band(pr_d, 0.95, 1.0, 0.006), pc, (0.5, 0.48, 0.45))
            pc = nb.mix(ring_dots(pr_d, pa_d, 1.2, 0.8, 16, 0.05), pc, (0.2, 0.19, 0.18))
            pc = nb.mix(ring_dots(pr_d, pa_d, 1.2, 0.8, 16, 0.028), pc, (0.62, 0.6, 0.58))
            c = nb.mix(ins(nb.math("SUBTRACT", pr_d, 1.0), 0.007), c, pc)
            gbd = Pn["gb_d"]
            gvc = nb.mix(nb.ramp(nb.voronoi(32.0, "Color"), 0.2, 0.8), (0.52, 0.52, 0.5), (0.7, 0.69, 0.66))
            gvc = nb.mix(nb.ramp(nb.voronoi(32.0, "Distance", "DISTANCE_TO_EDGE"), 0.05, 0.015), gvc, (0.32, 0.3, 0.28))
            gvc = nb.mix(band(gbd, -0.07, 0.0), gvc, (0.63, 0.62, 0.59))
            c = nb.mix(ins(gbd), c, gvc)
            c = nb.mix(Pn["c"], c, (0.72, 0.71, 0.68))
            c = nb.mix(Pn["m"], c, nb.mix(nb.ramp(nb.noise(8.0, 3, 0.6), 0.3, 0.7), (0.6, 0.59, 0.56), (0.7, 0.69, 0.66)))
            c = nb.mix(pk_m, c, (0.22, 0.21, 0.2))
            apd = Pn["ap_d"]
            aj, ar_ = nb.brick(obj, 1.0, 1.0, 0.006, 0.2, offset=0.0, freq=1)
            apc = nb.mix(ar_, (0.55, 0.54, 0.51), (0.64, 0.63, 0.6))
            apc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(1.6, 3, 0.6), 0.62, 0.72), 0.5), apc, (0.36, 0.35, 0.33))
            apc = nb.mix(aj, apc, (0.32, 0.31, 0.3))
            apc = nb.mix(band(apd, -0.05, 0.0), apc, (0.46, 0.45, 0.42))
            c = nb.mix(ins(apd), c, apc)
            c = nb.mix(nb.math("MULTIPLY", py_m, wear), c, (0.92, 0.74, 0.12))
            c = nb.mix(nb.math("MULTIPLY", pr_m, wear), c, (0.76, 0.15, 0.1))
            mpd = Pn["mp_d"]
            mpc = nb.mix(nb.dots(ox_, oy_, 1.2, 1.2, 0.15, 0.035), conc, (0.22, 0.21, 0.2))
            mpc = nb.mix(band(mpd, -0.04, 0.0), mpc, (0.5, 0.48, 0.45))
            c = nb.mix(ins(mpd), c, mpc)
            c, em = gate_plate(c, em, (0.5, 0.49, 0.47), (0.66, 0.65, 0.62))
            rough = 0.9
            bump_h = nb.math("ADD", nb.math("MULTIPLY", I["pave"], nb.ramp(nb.voronoi(22.0, "Distance", "DISTANCE_TO_EDGE"), 0.0, 0.05)),
                             nb.math("ADD", nb.math("MULTIPLY", ins(gbd), nb.ramp(nb.voronoi(32.0, "Distance", "DISTANCE_TO_EDGE"), 0.0, 0.05)),
                                     nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, ins(ped_)), nb.math("MULTIPLY", nb.ramp(rp_, 0.3, 0.9), 0.5))))
        elif THEME == "cooling":
            # the coolant vaults, lit indoors: steel deck plates (diamond tread, bolts), riveted panels and bar grating
            # (a dim blue glow under some) between seam beams; rime frost over it all, thick round the cold; condensation
            # streaks; coolant channels (a steel lip, pale blue coolant glowing faintly, ice at its edges and frozen in
            # places); ice crusts and spills (cracked, white at the cracks); frozen drain pads (an ice sheet in a bolted
            # steel rim); chiller plinths (tread plate, a hazard border, a round fan grille, blades under it); valve-
            # station grates; the heated tracks (dark steel plates, ribs, polished where the robots walk, meltwater, a
            # steel edge and a hazard-striped border), the slow stretch's ice sheet, the fast one's induction plates
            YEL, CYG, COOL = (0.95, 0.74, 0.1), (0.3, 0.88, 1.0), (0.5, 0.86, 1.0)
            hazc = stripes((0.07, 0.07, 0.08), YEL)
            bid = I["bid"]
            swap = nb.ramp(bid, 0.49, 0.51)
            pu, pw = nb.mixf(swap, ox_, oy_), nb.mixf(swap, oy_, ox_)

            def rivets(u, v, Lu, Lv, sp, off, r):
                """Rivets in rows along the edges of Lu x Lv panels on (u, v), sp apart, off in from the edge."""
                sq = lambda x_: nb.math("MULTIPLY", x_, x_)
                a1 = nb.math("SQRT", nb.math("ADD", sq(nb.seam(u, sp)), sq(nb.math("SUBTRACT", nb.seam(v, Lv), off))))
                a2 = nb.math("SQRT", nb.math("ADD", sq(nb.seam(v, sp)), sq(nb.math("SUBTRACT", nb.seam(u, Lu), off))))
                return nb.ramp(nb.math("MINIMUM", a1, a2), r, r * 0.6)

            dj, dr_ = nb.brick(obj, 1.2, 1.2, 0.006, 0.1, offset=0.0, freq=1)
            c = nb.mix(dr_, (0.4, 0.45, 0.5), (0.5, 0.55, 0.6))
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(mid, 0.55, 0.8), 0.45), c, (0.33, 0.37, 0.42))
            c = nb.mix(nb.math("MULTIPLY", tread, 0.35), c, (0.62, 0.67, 0.72))
            bolts = nb.dots(ox_, oy_, 1.2, 1.2, 0.08, 0.022)
            c = nb.mix(bolts, c, (0.68, 0.72, 0.77))
            c = nb.mix(dj, c, (0.13, 0.15, 0.18))
            pj, pr2 = nb.brick(nb.vec(pu, pw), 2.4, 1.2, 0.006, 0.1, offset=0.0, freq=1)
            pc = nb.mix(pr2, (0.46, 0.5, 0.55), (0.55, 0.59, 0.64))
            pc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(4.0, 3, 0.6), 0.5, 0.75), 0.35), pc, (0.4, 0.44, 0.48))
            rv = rivets(pu, pw, 2.4, 1.2, 0.2, 0.07, 0.018)
            pc = nb.mix(rv, pc, (0.66, 0.7, 0.75))
            pc = nb.mix(pj, pc, (0.14, 0.16, 0.19))
            c = nb.mix(I["b_panel"], c, pc)
            gbar = nb.math("MAXIMUM", nb.ramp(nb.seam(pw, 0.05), 0.011, 0.007), nb.ramp(nb.seam(pu, 0.3), 0.009, 0.005))
            glo = nb.math("MULTIPLY", nb.ramp(bid, 0.55, 0.6), nb.ramp(nb.noise(1.5, 2, 0.5), 0.35, 0.65))
            under = nb.mix(glo, (0.03, 0.045, 0.06), (0.1, 0.3, 0.42))
            grc = nb.mix(gbar, under, (0.5, 0.55, 0.61))
            gfj, _gr = nb.brick(obj, 1.2, 1.2, 0.03, 0.1, offset=0.0, freq=1)
            grc = nb.mix(gfj, grc, (0.36, 0.4, 0.45))
            grm = I["b_grate"]
            c = nb.mix(grm, c, grc)
            c = nb.mix(Pn["g"], c, nb.mix(nb.ramp(nb.noise(6.0, 2, 0.5), 0.3, 0.7), (0.26, 0.29, 0.33), (0.32, 0.35, 0.39)))
            # the heated tracks (under the frost: it keeps a ragged fringe at their edges), their border
            c = nb.mix(band(ped_, 0.0, 0.12), c, hazc)
            tkc = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.16, 0.18, 0.21), (0.21, 0.23, 0.26))
            tkc = nb.mix(nb.math("MULTIPLY", rut_m, 0.45), tkc, (0.28, 0.3, 0.34))
            rib = nb.ramp(nb.seam(ral, 0.12), 0.012, 0.005)
            tkc = nb.mix(nb.math("MULTIPLY", rib, 0.55), tkc, (0.09, 0.1, 0.12))
            tj_ = nb.ramp(nb.seam(ral, 1.2), 0.012, 0.005)
            tkc = nb.mix(tj_, tkc, (0.06, 0.07, 0.08))
            melt = nb.ramp(I["melt"], 0.3, 0.6)
            tkc = nb.mix(nb.math("MULTIPLY", melt, 0.8), tkc, nb.mix(nb.ramp(nb.noise(2.0, 2, 0.5), 0.3, 0.7), (0.08, 0.11, 0.15), (0.13, 0.17, 0.22)))
            sheet = nb.mix(nb.ramp(nb.noise(1.6, 3, 0.6), 0.3, 0.7), (0.66, 0.84, 0.95), (0.8, 0.93, 1.0))
            scr = nb.math("MULTIPLY", nb.ramp(nb.noise_v(nb.vec(nb.math("MULTIPLY", ral, 1.0), nb.math("MULTIPLY", rsd, 25.0)), 3.0, 2, 0.5), 0.62, 0.7), 0.6)
            sheet = nb.mix(scr, sheet, (0.92, 0.97, 1.0))
            scrk = nb.ramp(nb.voronoi(2.2, "Distance", "DISTANCE_TO_EDGE"), 0.012, 0.0)
            sheet = nb.mix(nb.math("MULTIPLY", scrk, 0.8), sheet, (0.98, 1.0, 1.0))
            sheet = nb.mix(nb.math("MULTIPLY", rut_m, 0.35), sheet, (0.55, 0.72, 0.84))
            tkc = nb.mix(Pn["sl"], tkc, sheet)
            fl_ = Pn["fl"]
            ars = nb.math("ABSOLUTE", rsd)
            chev = nb.math("MULTIPLY", nb.ramp(nb.seam(nb.math("SUBTRACT", ral, nb.math("MULTIPLY", ars, 0.75)), 0.9), 0.07, 0.04),
                           nb.ramp(ars, HALF - 0.28, HALF - 0.32))
            ipl = nb.mix(nb.ramp(nb.seam(ral, 0.3), 0.02, 0.012), (0.12, 0.2, 0.28), (0.04, 0.07, 0.1))
            ipl = nb.mix(chev, ipl, CYG)
            tkc = nb.mix(fl_, tkc, ipl)
            tkc = nb.mix(band(ped_, -0.07, 0.0), tkc, (0.5, 0.53, 0.58))
            tkc = nb.mix(band(ped_, -0.085, -0.07, 0.004), tkc, (0.08, 0.08, 0.09))
            c = nb.mix(ins(ped_), c, tkc)
            # rime frost: speckled where thin, a white crust where thick (on a grating only on its bars); condensation
            fr_a = nb.math("MULTIPLY", I["frost"], nb.math("ADD", 0.6, nb.math("MULTIPLY", nb.noise(3.0, 3, 0.6), 0.6)))
            spk = nb.noise(38.0, 2, 0.6)
            cover = nb.ramp(nb.math("SUBTRACT", fr_a, nb.math("MULTIPLY", spk, 0.55)), 0.05, 0.3)
            cover = nb.math("MULTIPLY", cover, nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", grm, nb.math("SUBTRACT", 1.0, gbar))))
            cover = nb.math("MULTIPLY", cover, nb.math("SUBTRACT", 1.0, Pn["sl"]))
            rime = nb.mix(nb.ramp(nb.voronoi(26.0, "Distance"), 0.35, 0.05), (0.76, 0.85, 0.93), (0.94, 0.97, 1.0))
            rime = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(90.0, 1, 0.5), 0.7, 0.74), 0.7), rime, (1.0, 1.0, 1.0))
            c = nb.mix(cover, c, rime)
            strk = nb.ramp(nb.noise_v(nb.vec(nb.math("MULTIPLY", ox_, 16.0), nb.math("MULTIPLY", oy_, 0.9)), 1.4, 3, 0.6), 0.5, 0.68)
            wetm = nb.math("MULTIPLY", nb.math("MULTIPLY", I["wet"], strk), nb.math("SUBTRACT", 1.0, ins(ped_)))
            c = nb.mix(nb.math("MULTIPLY", wetm, 0.55), c, (0.17, 0.22, 0.28))
            # paint on the floor and the tracks
            c = nb.mix(Pn["hz"], c, hazc)
            c = nb.mix(py_m, c, YEL)
            c = nb.mix(pw_m, c, (0.9, 0.93, 0.95))
            c = nb.mix(Pn["c"], c, CYG)
            # coolant channels
            chd, chu = Pn["ch_d"], Pn["ch_u"]
            flow = nb.ramp(nb.noise_v(nb.vec(nb.math("MULTIPLY", chu, 1.5), nb.math("MULTIPLY", chd, 12.0)), 2.5, 3, 0.6), 0.45, 0.75)
            chc = nb.mix(nb.ramp(chd, -0.03, -0.15), (0.32, 0.62, 0.78), (0.52, 0.85, 0.98))
            chc = nb.mix(nb.math("MULTIPLY", flow, 0.5), chc, (0.75, 0.95, 1.0))
            frz = nb.ramp(nb.noise_v(nb.vec(nb.math("MULTIPLY", chu, 0.7), 0.0), 1.0, 2, 0.5), 0.6, 0.64)
            crust = nb.math("MAXIMUM", frz, nb.ramp(chd, -0.075, -0.045))
            crust = nb.math("MAXIMUM", crust, nb.math("MULTIPLY", nb.ramp(nb.noise(12.0, 2, 0.6), 0.55, 0.62), nb.ramp(chd, -0.1, -0.06)))
            chc = nb.mix(crust, chc, nb.mix(nb.ramp(nb.noise(20.0, 2, 0.5), 0.3, 0.7), (0.8, 0.92, 0.98), (0.96, 0.99, 1.0)))
            chc = nb.mix(band(chd, -0.045, 0.0), chc, (0.55, 0.6, 0.66))
            chc = nb.mix(band(chd, -0.012, 0.0, 0.004), chc, (0.75, 0.79, 0.84))
            onch = ins(chd)
            c = nb.mix(onch, c, chc)
            coolem = nb.math("MULTIPLY", nb.math("MULTIPLY", ins(nb.math("ADD", chd, 0.045)), nb.math("SUBTRACT", 1.0, crust)), nb.mixf(flow, 0.45, 0.8))
            # ice crusts and frozen spills
            icm_ = I["ice"]
            icc = nb.mix(nb.ramp(nb.noise(4.0, 3, 0.6), 0.3, 0.7), (0.62, 0.82, 0.93), (0.8, 0.93, 1.0))
            icc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(3.5, "Distance", "DISTANCE_TO_EDGE"), 0.012, 0.0), 0.75), icc, (0.97, 1.0, 1.0))
            icc = nb.mix(nb.math("SUBTRACT", nb.ramp(icm_, 0.15, 0.4), nb.ramp(icm_, 0.5, 0.85)), icc, (0.94, 0.98, 1.0))
            icv = nb.ramp(icm_, 0.15, 0.3)
            c = nb.mix(icv, c, icc)
            # the frozen drain pads
            t, ta = Pn["ic_r"], Pn["ic_a"]
            pdc = nb.mix(nb.ramp(t, 0.1, 0.85), (0.9, 0.97, 1.0), (0.62, 0.81, 0.93))
            rings = nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", t, 6.0)), 0.5)), 0.42, 0.5)
            pdc = nb.mix(nb.math("MULTIPLY", rings, 0.35), pdc, (0.96, 0.99, 1.0))
            pdc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(2.6, "Distance", "DISTANCE_TO_EDGE"), 0.014, 0.0), 0.8), pdc, (1.0, 1.0, 1.0))
            pdc = nb.mix(band(t, 0.88, 1.0, 0.006), pdc, (0.48, 0.53, 0.59))
            pdc = nb.mix(band(t, 0.88, 0.9, 0.004), pdc, (0.2, 0.22, 0.25))
            pdc = nb.mix(ring_dots(t, ta, 1.3, 0.94, 24, 0.022), pdc, (0.78, 0.82, 0.87))
            c = nb.mix(ins(nb.math("SUBTRACT", t, 1.0), 0.006), c, pdc)
            # the chillers' plinths: tread plate, a hazard border, a round fan grille with the blades under it
            pld = Pn["pl_d"]
            fr_, fa_ = Pn["fn_r"], Pn["fn_a"]
            plc = nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.36, 0.4, 0.45), (0.44, 0.48, 0.53))
            plc = nb.mix(nb.math("MULTIPLY", tread, 0.35), plc, (0.56, 0.6, 0.65))
            plc = nb.mix(band(pld, -0.24, -0.08), plc, hazc)
            plc = nb.mix(band(pld, -0.035, 0.0), plc, (0.6, 0.64, 0.69))
            blade = nb.ramp(nb.math("SINE", nb.math("ADD", nb.math("MULTIPLY", fa_, 2 * math.pi * 5.0), nb.math("MULTIPLY", fr_, 2.2))), 0.2, 0.5)
            fan = nb.mix(nb.math("MULTIPLY", blade, nb.ramp(fr_, 0.22, 0.3)), (0.04, 0.05, 0.06), (0.2, 0.23, 0.27))
            grl = nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", fr_, 9.0)), 0.5)), 0.4, 0.47)
            spoke = nb.ramp(nb.math("MULTIPLY", nb.seam(fa_, 0.125), nb.math("MULTIPLY", fr_, 7.0)), 0.035, 0.02)
            fan = nb.mix(nb.math("MAXIMUM", grl, spoke), fan, (0.62, 0.66, 0.71))
            fan = nb.mix(nb.ramp(fr_, 0.2, 0.19), fan, (0.5, 0.54, 0.59))
            fan = nb.mix(band(fr_, 0.96, 1.04, 0.006), fan, (0.58, 0.62, 0.67))
            plc = nb.mix(ins(nb.math("SUBTRACT", fr_, 1.04), 0.006), plc, fan)
            plfr = nb.math("MULTIPLY", nb.math("MULTIPLY", I["frost"], nb.ramp(nb.noise(9.0, 3, 0.6), 0.45, 0.62)), 0.7)
            plc = nb.mix(plfr, plc, (0.88, 0.93, 0.98))
            c = nb.mix(ins(pld), c, plc)
            # the valve stations' grates: a bolted frame, a hazard-striped border
            vsd = Pn["vs_d"]
            vbar = nb.math("MAXIMUM", nb.ramp(nb.seam(ox_, 0.05), 0.011, 0.007), nb.ramp(nb.seam(oy_, 0.3), 0.009, 0.005))
            vsc = nb.mix(vbar, (0.04, 0.08, 0.1), (0.52, 0.56, 0.62))
            vsc = nb.mix(band(vsd, -0.2, -0.06), vsc, hazc)
            vsc = nb.mix(band(vsd, -0.06, 0.0), vsc, (0.46, 0.5, 0.55))
            vsc = nb.mix(nb.math("MULTIPLY", band(vsd, -0.06, 0.0), nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", nb.math("ADD", ox_, oy_), 3.3)), 0.5)), 0.44, 0.48)), vsc, (0.75, 0.78, 0.82))
            c = nb.mix(ins(vsd), c, vsc)
            for f_, col_ in ((nb.math("MULTIPLY", coolem, onch), (0.25, 0.62, 0.85)), (nb.math("MULTIPLY", Pn["c"], 0.8), CYG),
                             (nb.math("MULTIPLY", nb.math("MULTIPLY", chev, fl_), 0.9), CYG),
                             (nb.math("MULTIPLY", nb.math("MULTIPLY", grm, nb.math("SUBTRACT", 1.0, gbar)), nb.math("MULTIPLY", glo, 0.5)), (0.15, 0.45, 0.65))):
                em = nb.mix(f_, em, col_)
            c, em = gate_plate(c, em, (0.42, 0.46, 0.51), (0.68, 0.72, 0.77))
            iceish = nb.math("MAXIMUM", nb.math("MAXIMUM", icv, ins(nb.math("SUBTRACT", t, 0.88), 0.006)), Pn["sl"])
            rough = nb.mixf(nb.math("MAXIMUM", cover, plfr), nb.mixf(ins(ped_), 0.5, 0.42), 0.85)
            rough = nb.mixf(nb.math("MAXIMUM", wetm, nb.math("MULTIPLY", melt, ins(ped_))), rough, 0.2)
            rough = nb.mixf(nb.math("MAXIMUM", iceish, onch), rough, 0.12)
            bump_h = nb.math("ADD", nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, ins(ped_)), nb.math("SUBTRACT", nb.math("MULTIPLY", tread, 0.25), dj)),
                             nb.math("ADD", nb.math("MULTIPLY", grm, nb.math("SUBTRACT", gbar, 1.0)),
                                     nb.math("ADD", nb.math("MULTIPLY", I["b_panel"], nb.math("SUBTRACT", rv, pj)),
                                             nb.math("MULTIPLY", ins(ped_), nb.math("SUBTRACT", 0.0, nb.math("MAXIMUM", rib, tj_))))))
            bump_h = nb.math("ADD", nb.math("MULTIPLY", bump_h, nb.math("SUBTRACT", 1.0, nb.math("MAXIMUM", cover, iceish))),
                             nb.math("MULTIPLY", cover, nb.math("MULTIPLY", spk, 0.6)))
        elif THEME == "server":
            # a server hall, lit indoors (kept light enough to read): raised-floor tiles (speckled vinyl, a pale trim, dark
            # seams), perforated vent tiles in the cold aisles; rack footprints (clean darker tiles, dark outlines, a cable
            # grommet and levelling feet each); covered cable trenches (checker plate, some covers off: bundles of cables);
            # the open bays (tiles lifted: the subfloor, pedestals, cables); rack plinths and mainframe pads; the racks'
            # status lights and their reflections; the service aisles (dark, worn paler down the middle, a steel trim,
            # guide lights glowing along both edges), a blue light strip and arrows on the fast stretches
            BLU, AMB, GRN, RED = (0.28, 0.62, 1.0), (1.0, 0.62, 0.16), (0.3, 1.0, 0.45), (1.0, 0.3, 0.14)
            hazc = stripes((0.07, 0.07, 0.08), (0.95, 0.74, 0.1))
            sx_, sy_ = nb.seam(ox_, 0.6), nb.seam(oy_, 0.6)
            sm_ = nb.math("MINIMUM", sx_, sy_)
            tj, tr_ = nb.brick(obj, 0.6, 0.6, 0.006, 0.1, offset=0.0, freq=1)
            c = nb.mix(tr_, (0.34, 0.36, 0.4), (0.41, 0.43, 0.47))
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(45.0, 2, 0.5), 0.55, 0.75), 0.3), c, (0.48, 0.5, 0.54))
            scuff = nb.math("MULTIPLY", nb.ramp(nb.noise_v(nb.vec(ox_, nb.math("MULTIPLY", oy_, 6.0)), 2.5, 3, 0.6), 0.66, 0.78), I["scuff"])
            c = nb.mix(nb.math("MULTIPLY", scuff, 0.3), c, (0.27, 0.28, 0.31))
            c = nb.mix(nb.math("MULTIPLY", I["dust"], 0.18), c, (0.44, 0.43, 0.41))
            c = nb.mix(nb.ramp(sm_, 0.026, 0.016), c, (0.52, 0.54, 0.58))                              # the tiles' trim
            holes = nb.dots(ox_, oy_, 0.05, 0.05, 0.025, 0.011)
            pfc = nb.mix(holes, (0.46, 0.49, 0.53), (0.08, 0.09, 0.11))
            pfc = nb.mix(nb.ramp(sm_, 0.05, 0.04), (0.5, 0.52, 0.56), pfc)
            loose = nb.ramp(tr_, 0.935, 0.94)
            perf = nb.math("MAXIMUM", I["perf"], loose)
            c = nb.mix(perf, c, pfc)
            c = nb.mix(tj, c, (0.14, 0.15, 0.17))
            # rack footprints
            rkd = Pn["rk_d"]
            fpc = nb.mix(tr_, (0.27, 0.28, 0.31), (0.31, 0.32, 0.35))
            fpc = nb.mix(nb.ramp(sm_, 0.026, 0.016), fpc, (0.38, 0.4, 0.43))
            fpc = nb.mix(tj, fpc, (0.12, 0.13, 0.15))
            grom = nb.dots(nb.math("ADD", ox_, 0.3), nb.math("ADD", oy_, 0.6), 0.6, 1.2, 0.0, 0.07)
            fpc = nb.mix(grom, fpc, (0.03, 0.03, 0.04))
            fpc = nb.mix(nb.dots(ox_, oy_, 0.6, 1.2, 0.07, 0.022), fpc, (0.62, 0.64, 0.68))
            fpc = nb.mix(nb.math("MULTIPLY", nb.ramp(sx_, 0.014, 0.006), nb.ramp(rkd, -0.02, -0.03)), fpc, (0.07, 0.07, 0.08))
            fpc = nb.mix(band(rkd, -0.035, 0.0), fpc, (0.06, 0.06, 0.07))
            c = nb.mix(ins(rkd), c, fpc)
            # cable trenches: checker-plate covers, some off (cable bundles in the trench)
            trd, tru = Pn["tr_d"], Pn["tr_u"]
            cell = nb.math("FRACT", nb.math("MULTIPLY", nb.math("SINE", nb.math("MULTIPLY", nb.math("FLOOR", nb.math("DIVIDE", tru, 0.6)), 12.9898)), 43758.55))
            opn = nb.ramp(cell, 0.2, 0.19)
            trc = nb.mix(nb.math("MULTIPLY", tread, 0.45), (0.46, 0.48, 0.52), (0.6, 0.62, 0.66))
            trc = nb.mix(nb.ramp(nb.seam(tru, 0.6), 0.01, 0.004), trc, (0.17, 0.18, 0.2))
            cab = nb.cramp(nb.math("FRACT", nb.math("MULTIPLY", trd, 9.0)),
                           [(0.0, (0.1, 0.25, 0.75)), (0.25, (0.85, 0.75, 0.15)), (0.45, (0.55, 0.57, 0.6)), (0.65, (0.75, 0.2, 0.15)),
                            (0.85, (0.15, 0.55, 0.3)), (1.0, (0.1, 0.25, 0.75))])
            cab = nb.mix(nb.ramp(nb.math("ABSOLUTE", nb.math("SINE", nb.math("MULTIPLY", trd, 110.0))), 0.25, 0.0), cab, (0.03, 0.03, 0.035))
            cab = nb.mix(nb.ramp(trd, -0.03, -0.01), cab, (0.04, 0.04, 0.045))
            trc = nb.mix(opn, trc, cab)
            trc = nb.mix(band(trd, -0.025, 0.0), trc, (0.62, 0.64, 0.68))
            c = nb.mix(ins(trd), c, trc)
            # the open bays: tiles lifted, the subfloor with its pedestals and cables
            obd = Pn["ob_d"]
            obc = nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.17, 0.17, 0.18), (0.23, 0.22, 0.22))
            obc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise_v(nb.vec(nb.math("MULTIPLY", ox_, 0.25), nb.math("MULTIPLY", oy_, 8.0)), 1.5, 2, 0.5), 0.62, 0.7), 0.9),
                         obc, nb.mix(nb.ramp(nb.noise(3.0, 2, 0.5), 0.4, 0.6), (0.12, 0.3, 0.7), (0.7, 0.62, 0.15)))
            obc = nb.mix(nb.dots(ox_, oy_, 0.6, 0.6, 0.0, 0.05), obc, (0.62, 0.64, 0.68))
            obc = nb.mix(nb.dots(ox_, oy_, 0.6, 0.6, 0.0, 0.028), obc, (0.3, 0.31, 0.34))
            c = nb.mix(ins(obd), c, obc)
            # rack plinths and mainframe pads
            rpd, mfd = Pn["rp_d"], Pn["mf_d"]
            rpc = nb.mix(nb.math("MULTIPLY", tread, 0.4), (0.26, 0.28, 0.32), (0.36, 0.38, 0.42))
            rpc = nb.mix(band(rpd, -0.2, -0.07), rpc, hazc)
            rpc = nb.mix(band(rpd, -0.035, 0.0), rpc, (0.55, 0.57, 0.62))
            c = nb.mix(ins(rpd), c, rpc)
            mfc = nb.mix(nb.math("MULTIPLY", tread, 0.4), (0.2, 0.21, 0.24), (0.29, 0.3, 0.33))
            mfc = nb.mix(band(mfd, -0.36, -0.2), mfc, hazc)
            mfc = nb.mix(band(mfd, -0.2, 0.0), mfc, nb.mix(nb.ramp(nb.noise(8.0, 2, 0.5), 0.3, 0.7), (0.44, 0.46, 0.5), (0.5, 0.52, 0.56)))
            mfc = nb.mix(nb.math("MULTIPLY", nb.dots(ox_, oy_, 0.3, 0.3, 0.0, 0.025), band(mfd, -0.15, -0.05)), mfc, (0.75, 0.77, 0.8))
            mfc = nb.mix(band(mfd, -0.45, -0.4), mfc, AMB)
            c = nb.mix(ins(mfd), c, mfc)
            # paint on the floor: the rows' blue and amber lines, outlines ("k"), the bays' hatching
            c = nb.mix(pk_m, c, (0.06, 0.06, 0.07))
            c = nb.mix(Pn["c"], c, BLU)
            c = nb.mix(py_m, c, AMB)
            # the service aisles
            ars = nb.math("ABSOLUTE", rsd)
            asl = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.1, 0.11, 0.13), (0.135, 0.145, 0.165))
            asl = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(60.0, 1, 0.5), 0.68, 0.74), 0.4), asl, (0.2, 0.21, 0.24))
            asl = nb.mix(nb.math("MULTIPLY", nb.ramp(ars, 0.55, 0.0), 0.45), asl, (0.19, 0.2, 0.23))
            asl = nb.mix(nb.ramp(nb.seam(ral, 1.2), 0.008, 0.003), asl, (0.06, 0.06, 0.07))
            asl = nb.mix(nb.math("MULTIPLY", pk_m, 1.0), asl, (0.36, 0.38, 0.42))
            fl_ = Pn["fl"]
            chev = nb.math("MULTIPLY", nb.ramp(nb.seam(nb.math("SUBTRACT", ral, nb.math("MULTIPLY", ars, 0.7)), 1.2), 0.08, 0.05),
                           nb.math("MULTIPLY", nb.ramp(ars, 0.22, 0.18), nb.ramp(ars, HALF - 0.3, HALF - 0.34)))
            strip = nb.ramp(ars, 0.09, 0.07)
            fsc = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.08, 0.11, 0.18), (0.1, 0.14, 0.22))
            fsc = nb.mix(nb.math("MAXIMUM", chev, strip), fsc, BLU)
            asl = nb.mix(fl_, asl, fsc)
            asl = nb.mix(band(ped_, -0.05, 0.0), asl, (0.42, 0.44, 0.48))
            c = nb.mix(ins(ped_), c, asl)
            # light: the guide lights and the status lights, their glow on the floor
            hw_, hg_, hb_, hr_ = Pn["hw"], Pn["hg"], Pn["hb"], Pn["hr"]
            c = nb.mix(nb.math("MULTIPLY", hw_, 0.55), c, (0.55, 0.85, 1.0))
            c = nb.mix(nb.math("MULTIPLY", hg_, 0.6), c, GRN)
            c = nb.mix(nb.math("MULTIPLY", hb_, 0.6), c, BLU)
            c = nb.mix(nb.math("MULTIPLY", hr_, 0.6), c, RED)
            c = nb.mix(pw_m, c, (0.85, 0.97, 1.0))
            c = nb.mix(Pn["g"], c, GRN)
            c = nb.mix(Pn["m"], c, BLU)
            c = nb.mix(pr_m, c, RED)
            for f_, col_ in ((pw_m, (0.7, 0.95, 1.0)), (nb.math("MULTIPLY", hw_, 0.35), (0.4, 0.75, 1.0)), (Pn["g"], GRN), (Pn["m"], BLU), (pr_m, RED),
                             (nb.math("MULTIPLY", hg_, 0.3), GRN), (nb.math("MULTIPLY", hb_, 0.3), BLU), (nb.math("MULTIPLY", hr_, 0.3), RED),
                             (nb.math("MULTIPLY", nb.math("MAXIMUM", chev, strip), fl_), BLU), (nb.math("MULTIPLY", Pn["c"], 0.35), BLU),
                             (nb.math("MULTIPLY", band(mfd, -0.45, -0.4), 0.8), AMB)):
                em = nb.mix(f_, em, col_)
            c, em = gate_plate(c, em, (0.3, 0.32, 0.36), (0.55, 0.58, 0.63))
            stl = nb.math("MAXIMUM", nb.math("MAXIMUM", ins(rpd), ins(mfd)), nb.math("MULTIPLY", ins(trd), nb.math("SUBTRACT", 1.0, opn)))
            rough = nb.mixf(stl, nb.mixf(ins(ped_), 0.55, 0.42), 0.38)
            bump_h = nb.math("ADD", nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, ins(ped_)), nb.math("SUBTRACT", 0.0, nb.math("MAXIMUM", tj, nb.math("MULTIPLY", perf, holes)))),
                             nb.math("MULTIPLY", stl, nb.math("MULTIPLY", tread, 0.4)))
        elif THEME == "core":
            # the heart of the machine, neon-dark: big polished panels of near-black blue-violet (a bevelled rim, corner
            # marks, a faint sheen of the lights); hex-tiled plazas; the traces glowing cyan and red with their halo, vias;
            # energy conduits (a steel channel, light pulsing down it); the pillars' sockets (bolted rim, hazard ring,
            # a glowing ring, lit radial slots, a hub); scorch, cracks (some glowing red), oil with a sheen, the craters'
            # charred bowls and torn rims; the highways of dark glass with bright edges and lanes of data streaming down
            CY, RD, WH, HZO = (0.2, 0.95, 1.0), (1.0, 0.17, 0.22), (0.85, 1.0, 1.0), (1.0, 0.45, 0.1)
            pj, pr2 = nb.brick(obj, 1.2, 1.2, 0.005, 0.1, offset=0.0, freq=1)
            sx_, sy_ = nb.seam(ox_, 1.2), nb.seam(oy_, 1.2)
            sm_ = nb.math("MINIMUM", sx_, sy_)
            c = nb.mix(pr2, (0.07, 0.07, 0.095), (0.105, 0.1, 0.135))
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise_v(nb.vec(nb.math("ADD", ox_, oy_), nb.math("SUBTRACT", ox_, oy_)), 0.9, 2, 0.5), 0.55, 0.8), 0.5),
                       c, (0.15, 0.145, 0.19))                                                          # (the sheen)
            grime = nb.math("MULTIPLY", nb.ramp(nb.noise(3.5, 3, 0.6), 0.45, 0.75), nb.mixf(I["grime"], 0.3, 1.0))
            c = nb.mix(nb.math("MULTIPLY", grime, 0.4), c, (0.045, 0.045, 0.055))
            c = nb.mix(band(sm_, 0.004, 0.022, 0.003), c, (0.17, 0.17, 0.22))
            c = nb.mix(nb.dots(ox_, oy_, 1.2, 1.2, 0.09, 0.018), c, (0.3, 0.31, 0.38))
            c = nb.mix(pj, c, (0.02, 0.02, 0.03))
            he, hid = Pn["hx_e"], Pn["hx_id"]
            pzd = Pn["pz_d"]
            onpz = ins(pzd)
            hexc = nb.mix(hid, (0.08, 0.08, 0.11), (0.15, 0.15, 0.2))
            lit = nb.math("MULTIPLY", nb.ramp(hid, 0.95, 0.952), nb.ramp(he, 0.012, 0.02))
            litc = nb.mix(nb.ramp(nb.math("FRACT", nb.math("MULTIPLY", hid, 37.0)), 0.69, 0.71), CY, RD)
            hexc = nb.mix(lit, hexc, litc)
            hseam = nb.ramp(he, 0.01, 0.004)
            hexc = nb.mix(hseam, hexc, (0.08, 0.42, 0.5))
            hexc = nb.mix(band(pzd, -0.08, 0.0), hexc, (0.3, 0.31, 0.38))
            hexc = nb.mix(band(pzd, -0.055, -0.035, 0.004), hexc, CY)
            c = nb.mix(onpz, c, hexc)
            # the glow of the lights on the polished floor, then the traces
            hc_, hr_ = Pn["hc"], Pn["hr"]
            c = nb.mix(nb.math("MULTIPLY", hc_, 0.6), c, (0.1, 0.55, 0.65))
            c = nb.mix(nb.math("MULTIPLY", hr_, 0.6), c, (0.6, 0.08, 0.12))
            c = nb.mix(Pn["c"], c, CY)
            c = nb.mix(pr_m, c, RD)
            c = nb.mix(pw_m, c, WH)
            c = nb.mix(pk_m, c, (0.02, 0.02, 0.03))
            # conduits
            cdd, cdu = Pn["cd_d"], Pn["cd_u"]
            pulse = nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", cdu, 0.8)), 0.5)), 0.12, 0.3)
            cdc = nb.mix(nb.ramp(cdd, -0.035, -0.11), (0.08, 0.5, 0.62), CY)
            cdc = nb.mix(nb.math("MULTIPLY", pulse, nb.ramp(cdd, -0.05, -0.1)), cdc, WH)
            cdc = nb.mix(band(cdd, -0.035, 0.0), cdc, (0.3, 0.32, 0.38))
            cdc = nb.mix(band(cdd, -0.012, 0.0, 0.004), cdc, (0.5, 0.52, 0.58))
            oncd = ins(cdd)
            c = nb.mix(oncd, c, cdc)
            # the pillars' sockets
            t, ta = Pn["so_r"], Pn["so_a"]
            soc = nb.mix(nb.ramp(nb.noise(6.0, 3, 0.6), 0.3, 0.7), (0.05, 0.05, 0.07), (0.08, 0.08, 0.11))
            slot = nb.math("MULTIPLY", nb.ramp(nb.math("MULTIPLY", nb.seam(ta, 1.0 / 12.0), nb.math("MULTIPLY", t, 7.5)), 0.035, 0.022), band(t, 0.3, 0.62, 0.008))
            soc = nb.mix(slot, soc, (0.12, 0.75, 0.85))
            soc = nb.mix(band(t, 0.0, 0.2, 0.006), soc, (0.32, 0.33, 0.4))
            soc = nb.mix(band(t, 0.13, 0.16, 0.004), soc, RD)
            ring = band(t, 0.68, 0.8, 0.006)
            soc = nb.mix(ring, soc, CY)
            soc = nb.mix(band(t, 0.72, 0.76, 0.004), soc, WH)
            soc = nb.mix(band(t, 0.86, 1.0, 0.006), soc, (0.27, 0.28, 0.34))
            soc = nb.mix(ring_dots(t, ta, 1.3, 0.93, 24, 0.022), soc, (0.55, 0.57, 0.64))
            hzr = nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", ta, 36.0)), 0.5)), 0.24, 0.26)
            soc = nb.mix(band(t, 1.0, 1.1, 0.006), soc, nb.mix(hzr, (0.05, 0.05, 0.06), HZO))
            onso = ins(nb.math("SUBTRACT", t, 1.1), 0.006)
            c = nb.mix(onso, c, soc)
            # the battle: scorch, cracks (the deep ones glowing red), oil, the craters
            scm = nb.math("MULTIPLY", nb.ramp(I["scorch"], 0.0, 0.7), 0.95)
            c = nb.mix(scm, c, nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.015, 0.012, 0.014), (0.06, 0.045, 0.05)))
            ck = nb.math("MULTIPLY", nb.ramp(nb.voronoi(2.4, "Distance", "DISTANCE_TO_EDGE"), 0.012, 0.0), nb.ramp(I["crack"], 0.3, 0.6))
            hot = nb.math("MULTIPLY", ck, nb.math("MULTIPLY", nb.ramp(I["scorch"], 0.45, 0.8), nb.ramp(nb.noise(1.2, 2, 0.5), 0.45, 0.6)))
            c = nb.mix(ck, c, (0.01, 0.01, 0.012))
            c = nb.mix(hot, c, (1.0, 0.25, 0.1))
            sheen = nb.cramp(nb.noise(5.0, 3, 0.7), [(0.0, (0.03, 0.03, 0.04)), (0.35, (0.12, 0.05, 0.16)), (0.5, (0.04, 0.1, 0.12)),
                                                      (0.62, (0.12, 0.1, 0.03)), (0.8, (0.02, 0.02, 0.03)), (1.0, (0.03, 0.03, 0.04))])
            oilm = nb.ramp(I["oil"], 0.35, 0.6)
            bowl = nb.mix(nb.ramp(nb.noise(6.0, 3, 0.6), 0.3, 0.7), (0.03, 0.025, 0.03), (0.09, 0.07, 0.07))
            bowl = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(9.0, "Distance", "DISTANCE_TO_EDGE"), 0.03, 0.0), 0.8), bowl, (0.2, 0.19, 0.22))
            c = nb.mix(nb.math("MULTIPLY", I["rim"], 0.7), c, (0.2, 0.19, 0.23))
            c = nb.mix(nb.ramp(I["crater"], 0.05, 0.3), c, bowl)
            c = nb.mix(oilm, c, sheen)
            # the highways
            ars = nb.math("ABSOLUTE", rsd)
            hw_ = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.025, 0.04, 0.06), (0.04, 0.06, 0.085))
            lnf = nb.math("DIVIDE", nb.math("ADD", rsd, HALF), 0.28)
            lid = nb.math("FLOOR", lnf)
            lc = nb.math("MULTIPLY", nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", lnf), 0.5)), 0.28)
            hw_ = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.math("SUBTRACT", 0.14, lc), 0.006, 0.0), nb.ramp(ars, HALF - 0.12, HALF - 0.14)), hw_, (0.06, 0.12, 0.16))
            pk_ = nb.noise_v(nb.vec(nb.math("MULTIPLY", ral, 0.45), nb.math("MULTIPLY", lid, 3.7)), 4.0, 1, 0.5)
            pkt = nb.math("MULTIPLY", nb.ramp(pk_, 0.6, 0.63), nb.math("MULTIPLY", nb.ramp(lc, 0.03, 0.018), nb.ramp(ars, HALF - 0.16, HALF - 0.2)))
            pkc = nb.mix(nb.ramp(nb.noise_v(nb.vec(nb.math("MULTIPLY", ral, 0.2), nb.math("MULTIPLY", lid, 5.1)), 3.0, 1, 0.5), 0.62, 0.64), CY, RD)
            pkc = nb.mix(nb.ramp(pk_, 0.7, 0.74), pkc, WH)
            hw_ = nb.mix(pkt, hw_, pkc)
            fl_ = Pn["fl"]
            chev = nb.math("MULTIPLY", nb.ramp(nb.seam(nb.math("SUBTRACT", ral, nb.math("MULTIPLY", ars, 0.8)), 1.0), 0.06, 0.035), nb.ramp(ars, HALF - 0.24, HALF - 0.28))
            hw_ = nb.mix(nb.math("MULTIPLY", fl_, 0.6), hw_, nb.mix(chev, (0.04, 0.1, 0.16), WH))
            estrip = band(ped_, -0.075, -0.04, 0.005)
            hw_ = nb.mix(estrip, hw_, CY)
            hw_ = nb.mix(band(ped_, -0.04, 0.0, 0.004), hw_, (0.3, 0.32, 0.4))
            c = nb.mix(ins(ped_), c, hw_)
            onhw = ins(ped_)
            burnt = nb.math("SUBTRACT", 1.0, nb.math("MULTIPLY", nb.math("MAXIMUM", scm, nb.ramp(I["crater"], 0.05, 0.3)), 0.92))
            emf = nb.math("SUBTRACT", 1.0, onhw)
            for f_, col_ in ((nb.math("MULTIPLY", nb.math("MULTIPLY", Pn["c"], emf), burnt), CY), (nb.math("MULTIPLY", nb.math("MULTIPLY", pr_m, emf), burnt), RD),
                             (nb.math("MULTIPLY", nb.math("MULTIPLY", pw_m, emf), burnt), WH),
                             (nb.math("MULTIPLY", nb.math("MULTIPLY", hc_, 0.3), nb.math("MULTIPLY", emf, burnt)), CY),
                             (nb.math("MULTIPLY", nb.math("MULTIPLY", hr_, 0.3), nb.math("MULTIPLY", emf, burnt)), RD),
                             (nb.math("MULTIPLY", nb.math("MULTIPLY", oncd, nb.ramp(cdd, -0.035, -0.06)), emf), nb.mix(pulse, CY, WH)),
                             (nb.math("MULTIPLY", nb.math("MAXIMUM", ring, nb.math("MULTIPLY", slot, 0.7)), onso), CY),
                             (nb.math("MULTIPLY", band(t, 0.13, 0.16, 0.004), onso), RD),
                             (nb.math("MULTIPLY", nb.math("MULTIPLY", lit, onpz), emf), litc), (nb.math("MULTIPLY", nb.math("MULTIPLY", hseam, onpz), 0.35), CY),
                             (nb.math("MULTIPLY", hot, 0.9), (1.0, 0.25, 0.08)),
                             (nb.math("MULTIPLY", estrip, onhw), CY), (nb.math("MULTIPLY", pkt, onhw), pkc),
                             (nb.math("MULTIPLY", nb.math("MULTIPLY", chev, fl_), onhw), WH)):
                em = nb.mix(f_, em, col_)
            c, em = gate_plate(c, em, (0.16, 0.17, 0.21), (0.36, 0.38, 0.45))
            rough = nb.mixf(oilm, nb.mixf(scm, nb.mixf(onhw, 0.22, 0.08), 0.85), 0.06)
            bump_h = nb.math("ADD", nb.math("MULTIPLY", nb.math("SUBTRACT", 1.0, onhw), nb.math("SUBTRACT", 0.0, nb.math("MAXIMUM", pj, ck))),
                             nb.math("MULTIPLY", onpz, nb.math("SUBTRACT", 0.0, hseam)))
        elif THEME == "neon":
            # a cyberpunk district at night, wet: dark pavers, slabs, deck plates, parking and hex tiles in the lots;
            # deck-plate sidewalks, steel kerbs with a cyan light strip, a magenta line at the sidewalks' outer edge;
            # dark wet asphalt with the streets' cyan and magenta lines, data lanes of dark glass with cyan seams; the
            # pylons' scorched hex bases (a magenta ring, bolts, hazard stripes); the data pits (a dark shaft, cyan light
            # rising up its wall to a bright lip, a steel rim, a striped ring); the neon's glow and reflections; puddles
            CY, MG = (0.15, 0.95, 1.0), (1.0, 0.22, 0.86)
            pid = I["pid"]
            swap = nb.ramp(pid, 0.49, 0.51)
            pv = nb.vec(nb.math("ADD", nb.mixf(swap, ox_, oy_), nb.math("MULTIPLY", pid, 7.3)),
                        nb.math("ADD", nb.mixf(swap, oy_, ox_), nb.math("MULTIPLY", pid, 3.1)))
            grime = nb.math("MULTIPLY", nb.ramp(nb.noise(3.5, 3, 0.6), 0.45, 0.75), nb.mixf(I["grime"], 0.3, 1.0))
            pj, pr2 = nb.brick(pv, 0.3, 0.15, 0.006, 0.2)
            c = nb.mix(pr2, (0.085, 0.085, 0.105), (0.135, 0.13, 0.155))
            c = nb.mix(pj, c, (0.035, 0.035, 0.045))
            gj, gr2 = nb.brick(obj, 1.2, 1.2, 0.004, 0.2, offset=0.0, freq=1)
            gc = nb.mix(gr2, (0.1, 0.1, 0.125), (0.15, 0.15, 0.18))
            gc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(60.0, 1, 0.5), 0.7, 0.76), 0.4), gc, (0.22, 0.22, 0.26))
            c = nb.mix(I["l_grid"], c, gc)
            dj, dr_ = nb.brick(obj, 0.6, 0.6, 0.006, 0.1, offset=0.0, freq=1)
            dc = nb.mix(dr_, (0.15, 0.16, 0.19), (0.21, 0.22, 0.26))
            dc = nb.mix(nb.math("MULTIPLY", tread, 0.35), dc, (0.27, 0.28, 0.32))
            dc = nb.mix(dj, dc, (0.05, 0.05, 0.06))
            dc = nb.mix(nb.dots(ox_, oy_, 0.6, 0.6, 0.05, 0.016), dc, (0.36, 0.37, 0.42))
            c = nb.mix(I["l_deck"], c, dc)
            pkc = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.07, 0.07, 0.085), (0.1, 0.1, 0.12))
            pkc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(42.0, "Distance"), 0.2, 0.07), 0.3), pkc, (0.16, 0.16, 0.19))
            c = nb.mix(I["l_park"], c, pkc)
            he, hid = Pn["hx_e"], Pn["hx_id"]
            pzd = Pn["pz_d"]
            onpz = ins(pzd)
            hexc = nb.mix(hid, (0.1, 0.1, 0.14), (0.2, 0.2, 0.26))
            hexc = nb.mix(nb.math("MULTIPLY", grime, 0.3), hexc, (0.06, 0.06, 0.08))
            litc = nb.mix(nb.ramp(nb.math("FRACT", nb.math("MULTIPLY", hid, 37.0)), 0.49, 0.51), CY, MG)
            lit = nb.math("MULTIPLY", nb.ramp(hid, 0.982, 0.984), nb.ramp(he, 0.012, 0.02))
            hexc = nb.mix(lit, hexc, litc)
            hseam = nb.ramp(he, 0.01, 0.004)
            hexc = nb.mix(hseam, hexc, nb.mix(onpz, (0.03, 0.03, 0.04), (0.08, 0.38, 0.45)))
            hexm = nb.math("MAXIMUM", I["l_hex"], onpz)
            c = nb.mix(I["l_hex"], c, hexc)
            c = nb.mix(nb.math("MULTIPLY", grime, 0.35), c, (0.03, 0.03, 0.035))
            c = nb.mix(Pn["g"], c, (0.05, 0.05, 0.06))                                                  # the lots' borders
            c = nb.mix(pr_m, c, MG)
            c = nb.mix(py_m, c, CY)
            c = nb.mix(onpz, c, hexc)                                                                   # the plazas over them
            pzrim = band(pzd, -0.09, 0.0)
            pzline = band(pzd, -0.06, -0.035, 0.005)
            c = nb.mix(pzrim, c, (0.26, 0.27, 0.32))
            c = nb.mix(pzline, c, MG)
            ars = nb.math("ABSOLUTE", rsd)
            sj_, sr_ = nb.brick(nb.vec(ral, nb.math("SUBTRACT", ars, HALF + 0.1)), 0.6, 0.275, 0.006, 0.1, offset=0.5, freq=2)
            swc = nb.mix(sr_, (0.16, 0.17, 0.2), (0.22, 0.23, 0.27))
            swc = nb.mix(nb.math("MULTIPLY", tread, 0.35), swc, (0.29, 0.3, 0.34))
            swc = nb.mix(sj_, swc, (0.05, 0.05, 0.06))
            swc = nb.mix(nb.math("MULTIPLY", grime, 0.3), swc, (0.09, 0.09, 0.1))
            c = nb.mix(band(ped_, 0.1, SW), c, swc)
            c = nb.mix(band(ped_, 0.0, 0.1), c, nb.mix(nb.ramp(nb.noise(8.0, 2, 0.5), 0.3, 0.7), (0.28, 0.29, 0.34), (0.36, 0.37, 0.42)))
            strip = nb.math("MULTIPLY", band(ped_, 0.035, 0.065, 0.005), nb.ramp(Pn["gt_r"], 1.0, 1.02))
            c = nb.mix(strip, c, CY)
            sedge = nb.math("MULTIPLY", band(ped_, SW - 0.035, SW - 0.005, 0.005), nb.ramp(pzd, 0.0, 0.02))
            c = nb.mix(sedge, c, MG)
            asp = nb.mix(nb.ramp(mid, 0.3, 0.7), (0.055, 0.055, 0.07), (0.085, 0.085, 0.105))
            asp = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.voronoi(42.0, "Distance"), 0.2, 0.07), 0.3), asp, (0.15, 0.15, 0.18))
            asp = nb.mix(nb.math("MULTIPLY", rut_m, 0.3), asp, (0.1, 0.1, 0.125))
            asp = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise_v(nb.vec(nb.math("MULTIPLY", ox_, 4.0), oy_), 1.2, 3, 0.6), 0.6, 0.75), 0.35), asp, (0.12, 0.11, 0.17))
            fseam = nb.ramp(nb.seam(ral, 0.6), 0.012, 0.006)
            flc = nb.mix(nb.ramp(nb.noise(3.0, 3, 0.6), 0.3, 0.7), (0.03, 0.08, 0.13), (0.05, 0.12, 0.18))
            flc = nb.mix(fseam, flc, (0.1, 0.6, 0.75))
            asp = nb.mix(Pn["fl"], asp, flc)
            c = nb.mix(ins(ped_), c, asp)
            c = nb.mix(nb.math("MULTIPLY", nb.ramp(I["scorch"], 0.0, 0.7), 0.92), c, nb.mix(nb.ramp(nb.noise(5.0, 3, 0.6), 0.3, 0.7), (0.015, 0.012, 0.02), (0.07, 0.04, 0.08)))
            pyd, pyr, pya = Pn["py_d"], Pn["py_r"], Pn["py_a"]
            pyc = nb.mix(nb.ramp(nb.noise(6.0, 3, 0.6), 0.3, 0.7), (0.2, 0.21, 0.25), (0.27, 0.28, 0.33))
            pyc = nb.mix(nb.math("MULTIPLY", tread, 0.3), pyc, (0.33, 0.34, 0.39))
            pjn = nb.math("MULTIPLY", nb.ramp(nb.math("MULTIPLY", nb.seam(pya, 1.0 / 6.0), nb.math("MULTIPLY", pyr, 7.0)), 0.012, 0.006), nb.ramp(pyr, 0.5, 0.53))
            pyc = nb.mix(nb.math("MAXIMUM", pjn, band(pyr, 0.5, 0.53, 0.004)), pyc, (0.08, 0.08, 0.1))
            pring = band(pyr, 0.38, 0.45, 0.006)
            pyc = nb.mix(pring, pyc, MG)
            pyc = nb.mix(ring_dots(pyr, pya, 1.15, 0.7, 12, 0.03), pyc, (0.5, 0.51, 0.56))
            pyc = nb.mix(band(pyd, -0.17, -0.07), pyc, stripes((0.04, 0.04, 0.05), (0.9, 0.2, 0.75)))
            pyc = nb.mix(nb.math("MULTIPLY", nb.ramp(nb.noise(4.0, 3, 0.6), 0.5, 0.7), 0.5), pyc, (0.05, 0.04, 0.06))   # soot on it
            c = nb.mix(ins(pyd), c, pyc)
            t, ta = Pn["pt_r"], Pn["pt_a"]
            glow = nb.math("POWER", nb.ramp(t, 0.5, 0.97), 2.0)
            pit = nb.mix(glow, (0.01, 0.015, 0.025), (0.12, 0.85, 0.95))
            data = nb.math("MULTIPLY", nb.math("MULTIPLY", nb.dots(ox_, oy_, 0.09, 0.09, 0.045, 0.012), nb.ramp(nb.noise(14.0, 2, 0.5), 0.55, 0.6)),
                           nb.ramp(t, 0.75, 0.55))
            pit = nb.mix(nb.math("MULTIPLY", data, 0.8), pit, (0.1, 0.6, 0.7))
            lip = band(t, 0.93, 1.0, 0.008)
            pit = nb.mix(lip, pit, (0.75, 1.0, 1.0))
            pit = nb.mix(band(t, 1.0, 1.16, 0.008), pit, (0.3, 0.31, 0.36))
            pit = nb.mix(ring_dots(t, ta, 1.0, 1.08, 20, 0.022), pit, (0.55, 0.56, 0.6))
            hzr = nb.ramp(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", ta, 28.0)), 0.5)), 0.24, 0.26)
            pit = nb.mix(band(t, 1.17, 1.3, 0.008), pit, nb.mix(hzr, (0.04, 0.04, 0.05), (0.9, 0.2, 0.75)))
            onpit = ins(nb.math("SUBTRACT", t, 1.3), 0.008)
            c = nb.mix(onpit, c, pit)
            notpit = nb.math("SUBTRACT", 1.0, ins(nb.math("SUBTRACT", t, 1.0), 0.008))
            dry = nb.math("MULTIPLY", notpit, nb.math("SUBTRACT", 1.0, ins(pyd)))
            pud = nb.ramp(I["pud"], 0.45, 0.6)
            c = nb.mix(nb.math("MULTIPLY", pud, 0.7), c, nb.mix(nb.ramp(nb.noise(1.5, 2, 0.5), 0.3, 0.7), (0.035, 0.035, 0.05), (0.09, 0.07, 0.14)))
            hk = nb.math("MULTIPLY", dry, nb.mixf(pud, 0.5, 0.95))
            c = nb.mix(nb.math("MULTIPLY", Pn["hc"], hk), c, CY)
            c = nb.mix(nb.math("MULTIPLY", Pn["hm"], hk), c, MG)
            c = nb.mix(pk_m, c, (0.02, 0.02, 0.025))
            c = nb.mix(pw_m, c, (0.34, 0.35, 0.4))
            c = nb.mix(Pn["c"], c, CY)
            c = nb.mix(Pn["m"], c, MG)
            for f_, col_ in ((Pn["c"], CY), (Pn["m"], MG), (strip, CY), (sedge, MG), (nb.math("MULTIPLY", lit, hexm), litc),
                             (pzline, MG), (pring, MG), (nb.math("MULTIPLY", fseam, Pn["fl"]), CY), (nb.math("MULTIPLY", nb.math("MULTIPLY", pr_m, 0.7), nb.math("SUBTRACT", 1.0, onpz)), MG),
                             (nb.math("MULTIPLY", nb.math("MULTIPLY", py_m, 0.6), nb.math("SUBTRACT", 1.0, onpz)), CY), (nb.math("MULTIPLY", nb.math("MULTIPLY", hseam, onpz), 0.4), CY)):
                em = nb.mix(f_, em, col_)
            em = nb.mix(nb.math("MULTIPLY", onpit, nb.math("MAXIMUM", nb.math("MULTIPLY", glow, nb.ramp(t, 1.0, 0.99)), lip)), em, (0.2, 1.0, 1.0))
            c, em = gate_plate(c, em, (0.2, 0.21, 0.25), (0.4, 0.42, 0.48))
            rough = nb.mixf(nb.math("MAXIMUM", ins(ped_), pud), 0.62, 0.2)
            bump_h = nb.math("ADD", nb.math("MULTIPLY", hexm, nb.math("SUBTRACT", 0.0, hseam)),
                             nb.math("ADD", nb.math("MULTIPLY", I["l_deck"], nb.math("SUBTRACT", nb.math("MULTIPLY", tread, 0.3), dj)),
                                     nb.math("MULTIPLY", band(ped_, 0.1, SW), nb.math("SUBTRACT", nb.math("MULTIPLY", tread, 0.3), sj_))))
            bump_h = nb.math("MULTIPLY", bump_h, nb.math("SUBTRACT", 1.0, pud))
        nb.link(em, nb.b.inputs["Emission Color"])
        nb.b.inputs["Emission Strength"].default_value = {"lab": 1.6, "satellite": 2.0, "neon": 1.1, "cooling": 1.0, "server": 1.2,
                                                          "core": 1.3}[THEME]
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


def _mesh_obj(name, V, F, mat):
    me2 = bpy.data.meshes.new(name)
    me2.from_pydata([tuple(v) for v in V], [], [tuple(int(i) for i in f) for f in F])
    me2.update()
    bm = bmesh.new()
    bm.from_mesh(me2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me2)
    bm.free()
    ob = bpy.data.objects.new(name, me2)
    sc.collection.objects.link(ob)
    me2.materials.append(mat)
    return ob


def boxes_mesh(name, boxes, mat):
    """Boxes on the ground, one mesh: (x, z, yaw (world: from +x toward +z), length (along yaw), width, height, the
    height of its bottom)."""
    if not boxes:
        log("(no %s)" % name)
        return None
    B = np.asarray(boxes, np.float64)
    cx, cz, yaw, L, W, Hh, b0 = B.T
    ca, sa = np.cos(yaw)[:, None], np.sin(yaw)[:, None]
    u = np.array([-1, 1, 1, -1, -1, 1, 1, -1])[None] * 0.5 * L[:, None]
    v = np.array([-1, -1, 1, 1, -1, -1, 1, 1])[None] * 0.5 * W[:, None]
    hh = b0[:, None] + np.array([0, 0, 0, 0, 1, 1, 1, 1])[None] * Hh[:, None]
    V = np.stack([cx[:, None] + u * ca - v * sa, -(cz[:, None] + u * sa + v * ca), hh], -1).reshape(-1, 3)
    F0 = np.array([(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    F = (F0[None] + 8 * np.arange(len(B))[:, None, None]).reshape(-1, 4)
    log(name, len(B), "boxes")
    return _mesh_obj(name, V, F, mat)


def strip_mesh(name, strips, mat):
    """Bars along world paths (rails): (points N x 2 (x, z), half width, bottom heights N, top heights N)."""
    if not strips:
        log("(no %s)" % name)
        return None
    V, F = [], []
    for P, w, bot, top in strips:
        P = np.asarray(P, np.float64)
        T = np.gradient(P, axis=0)
        T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
        Nn = np.stack([-T[:, 1], T[:, 0]], 1)
        k0 = len(V)
        for (x, z), (nx_, nz_), b_, t_ in zip(P, Nn, bot, top):
            V += [(x + nx_ * w, -(z + nz_ * w), b_), (x + nx_ * w, -(z + nz_ * w), t_), (x - nx_ * w, -(z - nz_ * w), t_),
                  (x - nx_ * w, -(z - nz_ * w), b_)]
        for i in range(len(P) - 1):
            a_, b2 = k0 + i * 4, k0 + (i + 1) * 4
            F += [(a_ + 1, a_ + 2, b2 + 2, b2 + 1), (a_, a_ + 1, b2 + 1, b2), (a_ + 2, a_ + 3, b2 + 3, b2 + 2)]
        e_ = k0 + (len(P) - 1) * 4
        F += [(k0, k0 + 1, k0 + 2, k0 + 3), (e_, e_ + 1, e_ + 2, e_ + 3)]
    log(name, len(strips), "strips")
    return _mesh_obj(name, V, F, mat)


def tube_mesh(name, runs, mat, sides=10):
    """Tubes lying along world polylines (x, z): (points N x 2, radius, the height of its axis over the ground)."""
    if not runs:
        log("(no %s)" % name)
        return None
    V, F = [], []
    for P, r, lift in runs:
        P = np.asarray(P, np.float64)
        T = np.gradient(P, axis=0)
        T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
        h = hgt(P[:, 0], P[:, 1])
        base = len(V)
        for i in range(len(P)):
            for s in range(sides):
                b_ = 2 * math.pi * s / sides
                ox, oz = -T[i, 1] * math.cos(b_) * r, T[i, 0] * math.cos(b_) * r
                V.append((P[i, 0] + ox, -(P[i, 1] + oz), h[i] + lift + math.sin(b_) * r))
        for i in range(len(P) - 1):
            for s in range(sides):
                a0, a1 = base + i * sides + s, base + i * sides + (s + 1) % sides
                F.append((a0, a0 + sides, a1 + sides, a1))
        e0, e1 = base, base + (len(P) - 1) * sides                    # (the ends capped)
        F.append(tuple(range(e0, e0 + sides)))
        F.append(tuple(range(e1, e1 + sides)))
    log(name, len(runs), "tubes")
    return _mesh_obj(name, V, F, mat)


def box_template(lx, ly, lz):
    V = [(sx * lx / 2, sy * ly / 2, h * lz) for h in (0, 1) for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return V, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def cyl_template(r, h, sides=10, cap=1.25):
    """A bollard: a short post with a wider cap on its top."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=r, radius2=r, depth=h * 0.8)
    bmesh.ops.translate(bm, vec=(0, 0, h * 0.4), verts=bm.verts[:])
    m2 = bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=r * cap, radius2=r * cap * 0.8, depth=h * 0.25)
    bmesh.ops.translate(bm, vec=(0, 0, h * 0.86), verts=m2["verts"])
    V = [tuple(v.co) for v in bm.verts]
    F = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return V, F


def build_tracks(sl_col, sl_var, gauge=0.31, sl_len=1.02, sl_gap=0.27):
    """The railway in 3D: sleepers (laid long under both tracks where a turnout's tracks run close, the branch's own
    sleepers starting where they part; none on a road, where the rails run flush in the crossing's boards), rails with
    bright heads, a buffer stop at each dead end, the turntable's bridge, race rail and pivot."""
    if not TRACKS:
        return
    td = []
    for t in TRACKS:
        P = t["pts"]
        T = np.gradient(P, axis=0)
        T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
        cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        td.append((P, T, np.stack([-T[:, 1], T[:, 0]], 1), cum))
    sl, rails, heads, beams, posts = [], [], [], [], []
    tr = np.random.default_rng(71)
    for k, (P, T, Nn, cum) in enumerate(td):
        for s_ in np.arange(sl_gap * 0.5, cum[-1] - 0.04, sl_gap):
            c_ = np.array([np.interp(s_, cum, P[:, 0]), np.interp(s_, cum, P[:, 1])])
            t_ = np.array([np.interp(s_, cum, T[:, 0]), np.interp(s_, cum, T[:, 1])])
            t_ /= np.linalg.norm(t_)
            n_ = np.array([-t_[1], t_[0]])
            if _at(dist, c_[0], c_[1]) < HALF + 0.2 or TRACKS[k]["flush"]:
                continue
            if TURNTABLE and math.hypot(c_[0] - TURNTABLE[0], c_[1] - TURNTABLE[1]) < TURNTABLE[2] + 0.25:
                continue
            lo, hi, skip = -sl_len / 2, sl_len / 2, False
            for j, (Pj, Tj, Nj, cj) in enumerate(td):
                if j == k:
                    continue
                v_ = Pj - c_
                al_, sd_ = v_ @ t_, v_ @ n_
                sel = np.flatnonzero((np.abs(al_) < 0.04) & (np.abs(sd_) < 1.0))
                if not len(sel):
                    continue
                i_ = sel[np.argmin(np.abs(al_[sel]))]
                sv = sd_[i_]
                if abs(Tj[i_] @ t_) > 0.82:
                    if abs(sv) < 0.95:
                        if j < k:
                            skip = True
                            break
                        lo, hi = min(lo, sv - sl_len / 2), max(hi, sv + sl_len / 2)
                elif abs(sv) < 0.55 and j < k:
                    skip = True
                    break
            if skip:
                continue
            mid_ = c_ + n_ * (lo + hi) / 2 + t_ * tr.normal(0, 0.008)
            yaw = math.atan2(n_[1], n_[0]) + tr.normal(0, 0.025)
            sl.append((mid_[0], mid_[1], yaw, hi - lo, 0.13, 0.04, float(hgt(mid_[0], mid_[1])) - 0.012))
        hc = hgt(P[:, 0], P[:, 1])
        rr = np.clip(sample(on_road, P[:, 0], P[:, 1]) * 1.5, 0, 1) if not TRACKS[k]["flush"] else np.ones(len(P))
        bot = hc + 0.026 * (1 - rr) - 0.03 * rr
        top = bot + 0.046 - 0.008 * rr
        for sg in (-1, 1):
            Q = P + Nn * gauge * sg
            rails.append((Q, 0.024, bot, top))
            heads.append((Q, 0.012, top - 0.004, top + 0.004))
        if TRACKS[k]["buf"]:
            e_, te = P[-1], T[-1]
            ne = np.array([-te[1], te[0]])
            h_ = float(hgt(e_[0], e_[1]))
            yaw = math.atan2(ne[1], ne[0])
            b_ = e_ + te * 0.12
            beams.append((b_[0], b_[1], yaw, 0.88, 0.1, 0.075, h_ + 0.075))
            for sg in (-1, 1):
                q_ = e_ + te * 0.14 + ne * gauge * sg
                posts.append((q_[0], q_[1], yaw, 0.08, 0.08, 0.16, h_ - 0.01))
                q_ = e_ - te * 0.14 + ne * gauge * sg                   # (the struts behind, leaning on the rails)
                posts.append((q_[0], q_[1], yaw + 1.5708, 0.3, 0.05, 0.05, h_ + 0.05))
    boxes_mesh("Sleepers", sl, simple_mat("Sleeper", sl_col, 0.85, var=sl_var))
    iron = simple_mat("RailSide", (0.24, 0.15, 0.1), 0.6, var=(0.32, 0.2, 0.12), metal=0.3)
    strip_mesh("Rails", rails, iron)
    strip_mesh("RailHeads", heads, simple_mat("RailHead", (0.62, 0.62, 0.64), 0.28, metal=0.85))
    boxes_mesh("BufferBeams", beams, simple_mat("BufferBeam", (0.62, 0.11, 0.07), 0.6, var=(0.7, 0.16, 0.1)))
    boxes_mesh("BufferPosts", posts, simple_mat("BufferPost", (0.2, 0.16, 0.12), 0.8, var=(0.28, 0.22, 0.16)))
    if TURNTABLE:
        cx_, cz_, R_, ang = TURNTABLE
        a_ = math.radians(ang)
        d_, n_ = np.array([math.cos(a_), math.sin(a_)]), np.array([-math.sin(a_), math.cos(a_)])
        floor = float(hgt(cx_, cz_))
        gnd = float(np.mean([hgt(cx_ + math.cos(q) * (R_ + 0.4), cz_ + math.sin(q) * (R_ + 0.4)) for q in np.linspace(0, 6.28, 12)]))
        th = np.linspace(0, 2 * math.pi, 97)
        ring = np.stack([cx_ + np.cos(th) * (R_ - 0.1), cz_ + np.sin(th) * (R_ - 0.1)], 1)
        dk = gnd + 0.02
        strip_mesh("TTRace", [(ring, 0.022, np.full(97, floor), np.full(97, floor + 0.04))], iron)
        boxes_mesh("TTDeck", [(cx_, cz_, a_, 2 * R_ - 0.1, 0.66, dk - floor, floor)],
                   simple_mat("TTDeck", (0.3, 0.24, 0.18), 0.85, var=(0.42, 0.35, 0.27)))
        gird = [(cx_ + n_[0] * 0.37 * sg, cz_ + n_[1] * 0.37 * sg, a_, 2 * R_ - 0.06, 0.08, dk + 0.045 - floor, floor) for sg in (-1, 1)]
        gird.append((cx_, cz_, a_, 0.2, 0.2, dk + 0.012 - floor, floor))
        boxes_mesh("TTGirders", gird, simple_mat("TTIron", (0.16, 0.16, 0.17), 0.5, var=(0.22, 0.2, 0.19), metal=0.5))
        line = np.array([cx_, cz_]) + np.outer(np.linspace(-R_ + 0.06, R_ - 0.06, 40), d_)
        br_ = []
        for sg in (-1, 1):
            Q = line + n_ * 0.31 * sg
            br_.append((Q, 0.012, np.full(40, dk + 0.04), np.full(40, dk + 0.05)))
            strip_mesh("TTRail%d" % sg, [(Q, 0.024, np.full(40, dk), np.full(40, dk + 0.045))], iron)
        strip_mesh("TTRailHeads", br_, simple_mat("TTHead", (0.62, 0.62, 0.64), 0.28, metal=0.85))


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
    dense = lambda x, z: (sample(outside, x, z) > 0.35) | (sample(PATCH, x, z) > 0.58)
    fern = blade_mat("Fern", (0.04, 0.11, 0.03), (0.1, 0.25, 0.05), (0.21, 0.42, 0.09), 0.65)
    pts = scatter(2600 if not PREVIEW else 500, lambda x, z: off(x, z, 0.3) & dense(x, z) & nopave(x, z))
    merged("Ferns", frond_template(7, 0.22, 0.05, 0.07), place_list(pts, 0.75, 1.4), fern)
    pts = scatter(1300 if not PREVIEW else 250, lambda x, z: off(x, z, 0.2) & nopave(x, z))
    merged("SmallFerns", frond_template(6, 0.13, 0.034, 0.045, 4), place_list(pts, 0.7, 1.3), fern)
    seed = simple_mat("Seedling", (0.15, 0.32, 0.06), 0.6, var=(0.26, 0.45, 0.1))
    pts = scatter(2200 if not PREVIEW else 400, lambda x, z: off(x, z, 0.2) & (sample(gp_a, x, z) < 0.7))
    merged("Seedlings", seedling_template(4, 0.07, 0.03, 0.045), place_list(pts, 0.7, 1.4), seed)
    broad = simple_mat("BroadLeaf", (0.08, 0.22, 0.05), 0.55, var=(0.16, 0.32, 0.07))
    pts = scatter(900 if not PREVIEW else 150, lambda x, z: off(x, z, 0.35) & nopave(x, z))
    merged("BroadLeaves", seedling_template(5, 0.13, 0.055, 0.08), place_list(pts, 0.8, 1.3), broad)
    gr = blade_mat("Grass", (0.1, 0.2, 0.05), (0.2, 0.34, 0.09), (0.38, 0.52, 0.16))
    pts = scatter(3500 if not PREVIEW else 500, lambda x, z: off(x, z, 0.12) & (sample(PATCH, x, z) > 0.55))
    merged("Tufts", tuft_template(8, 0.1, 0.012), place_list(pts, 0.75, 1.3), gr)
    moss = simple_mat("Moss", (0.14, 0.3, 0.06), 0.9, var=(0.24, 0.42, 0.1))
    pts = scatter(1800 if not PREVIEW else 300, lambda x, z: off(x, z, 0.2))
    merged("MossLumps", blob_template(2), [(p, y, s_, None) for (p, y, s_, t) in place_list(pts, 0.05, 0.12, sink=0.7)], moss)
    pts = scatter(900 if not PREVIEW else 150, lambda x, z: (sample(gp_a, x, z) > 0.5) | ((sample(lane, x, z) > 0.5) & (rd(x, z) > 0.45)))
    merged("JointMoss", blob_template(1), [(p, y, s_, None) for (p, y, s_, t) in place_list(pts, 0.02, 0.045, sink=0.6)], moss)   # in the stones' joints
    for k, (col, var, n_, L_) in enumerate([((0.2, 0.3, 0.08), (0.3, 0.42, 0.1), 4500, 0.046), ((0.5, 0.38, 0.12), (0.6, 0.46, 0.16), 4500, 0.046),
                                           ((0.34, 0.18, 0.07), (0.44, 0.25, 0.09), 4500, 0.042), ((0.14, 0.24, 0.06), (0.22, 0.32, 0.08), 1000, 0.08),
                                           ((0.5, 0.2, 0.07), (0.6, 0.3, 0.09), 1400, 0.042)]):          # green, yellow-brown, brown, broad, rust
        pts = scatter(n_ if not PREVIEW else 300, lambda x, z: (rd(x, z) > HALF - 0.3) & no_blk(x, z) & (sample(gp_b, x, z) < 0.3) & (sample(lane, x, z) < 0.5))
        merged("Leaves%d" % k, leaf_template(L_, L_ * 0.48), place_list(pts, 0.7, 1.3, tilt=0.25), simple_mat("Leaf%d" % k, col, 0.7, var=var))
    for k, col in enumerate([(0.86, 0.1, 0.06), (1.0, 0.46, 0.06), (0.94, 0.2, 0.08)]):              # red and orange
        centres = scatter(55 if not PREVIEW else 15, lambda x, z: off(x, z, 0.5) & nopave(x, z))
        pts = []
        for cx, cz in centres:
            for _ in range(int(RNG.integers(3, 8))):
                pts.append((cx + RNG.normal(0, 0.11), cz + RNG.normal(0, 0.11)))
        merged("Flowers%d" % k, flower_template(5, 0.032), place_list(pts, 0.8, 1.25), simple_mat("Petal%d" % k, col, 0.45))
    root_mesh("Roots", ROOTS, simple_mat("Root", (0.28, 0.21, 0.14), 0.75, var=(0.38, 0.3, 0.2)))
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
    centres = scatter(50 if not PREVIEW else 12, lambda x, z: wrack(x, z) & (np.abs(sample(riv, x, z) - 0.6) < 0.2))
    pts = []
    for cx, cz in centres:                                                                         # (in clumps where it washed up)
        for _ in range(int(RNG.integers(3, 9))):
            pts.append((cx + RNG.normal(0, 0.09), cz + RNG.normal(0, 0.09)))
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
    pts = scatter(22, lambda x, z: sample(crater, x, z) > 0.25) + \
        scatter(90, lambda x, z: open_f(x, z) & (rd(x, z) > HALF + 0.4) & (sample(gp_d, x, z) < 0.5))
    merged("Shot", ball_template(2), [(p, y, s_, None) for (p, y, s_, t) in place_list(pts, 0.065, 0.085, sink=0.4)], ball)
    clod = simple_mat("Clod", (0.27, 0.2, 0.13), 0.9, var=(0.36, 0.27, 0.17))
    pts = scatter(650 if not PREVIEW else 150, lambda x, z: (sample(crater_rim, x, z) > 0.35) & (rd(x, z) > HALF + 0.1)) + \
        scatter(250 if not PREVIEW else 50, lambda x, z: (sample(gp_b, x, z) > 0.5) & (rd(x, z) > HALF + 0.1))
    merged("Clods", blob_template(1), place_list(pts, 0.025, 0.06, sink=0.35, tilt=0.5), clod)
    soot = simple_mat("Charred", (0.07, 0.06, 0.05), 0.85, var=(0.16, 0.14, 0.12))
    pts = scatter(500 if not PREVIEW else 100, lambda x, z: (sample(gp_d, x, z) > 0.4) & (rd(x, z) > HALF + 0.1))
    merged("Charred", blob_template(1), place_list(pts, 0.02, 0.05, sink=0.4, tilt=0.6), soot)
    grav = simple_mat("Gravel", (0.46, 0.44, 0.4), 0.8, var=(0.66, 0.63, 0.56))
    pts = scatter(5000 if not PREVIEW else 800, lambda x, z: rd(x, z) < HALF + 0.05)
    merged("Gravel", blob_template(1), place_list(pts, 0.01, 0.026, sink=0.35), grav)
    pts = scatter(100, lambda x, z: (np.abs(rd(x, z) - HALF - 0.3) < 0.3) & open_f(x, z))
    merged("Stones", blob_template(2), place_list(pts, 0.05, 0.12, sink=0.45), simple_mat("Stone", (0.48, 0.47, 0.44), 0.8, var=(0.62, 0.6, 0.56)))
elif THEME == "factory":
    build_tracks((0.15, 0.12, 0.1), (0.26, 0.22, 0.18))
    offr = lambda x, z, m_: (rd(x, z) > HALF + m_) & (sample(BLK_ANY, x, z) > 0.1) & (sample(IND["puddle"], x, z) < 0.3)
    rnd = lambda x: RNG.random(np.shape(x))
    pts = scatter(3200 if not PREVIEW else 500, lambda x, z: offr(x, z, 0.08) & (rnd(x) < 0.12 + 0.88 * sample(IND["coke"], x, z)) &
                  (sample(IND["plates"], x, z) < 0.5))
    merged("Coke", blob_template(1), place_list(pts, 0.018, 0.045, sink=0.3, tilt=0.5),
           simple_mat("Coke", (0.06, 0.06, 0.065), 0.5, var=(0.15, 0.15, 0.16), metal=0.25))
    pts = scatter(3500 if not PREVIEW else 500, lambda x, z: offr(x, z, 0.05) & (sample(IND["plates"], x, z) < 0.5) &
                  (sample(IND["flags"], x, z) < 0.5))
    merged("Cinders", blob_template(1), place_list(pts, 0.01, 0.028, sink=0.3),
           simple_mat("Cinder", (0.13, 0.12, 0.11), 0.85, var=(0.32, 0.29, 0.26)))
    pts = scatter(700 if not PREVIEW else 120, lambda x, z: offr(x, z, 0.1) & (sample(IND["slag"], x, z) > 0.4))
    merged("Slag", blob_template(2), place_list(pts, 0.03, 0.085, sink=0.45, tilt=0.4),
           simple_mat("SlagLump", (0.05, 0.055, 0.065), 0.3, var=(0.12, 0.17, 0.19), metal=0.2))
    # scrap in heaps near the machines, the mills and the plate floors: rusty bars, offcuts of plate, hoops
    centres = scatter(55, lambda x, z: offr(x, z, 0.5) & ((sample(BLK_ANY, x, z) < 1.4) | (sample(IND["plates"], x, z) > 0.5) | (rnd(x) < 0.2)))
    pts = []
    for cx, cz in centres:
        for _ in range(int(RNG.integers(3, 9))):
            pts.append((cx + RNG.normal(0, 0.16), cz + RNG.normal(0, 0.16)))
    pts = [p_ for p_ in pts if _at(dist, p_[0], p_[1]) > HALF + 0.15 and _at(BLK_ANY, p_[0], p_[1]) > 0.05]
    rusty = simple_mat("Scrap", (0.33, 0.16, 0.07), 0.7, var=(0.5, 0.28, 0.12), metal=0.3)
    third = len(pts) // 3
    merged("ScrapBars", stick_template(0.34, 0.016), place_list(pts[:third], 0.8, 1.3, tilt=0.05), rusty)
    merged("ScrapPlate", box_template(0.18, 0.13, 0.012), place_list(pts[third:2 * third], 0.7, 1.4, tilt=0.15), rusty)
    merged("ScrapHoops", tube_template([(0.075 * math.cos(q), 0.075 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 17)], 0.01),
           place_list(pts[2 * third:], 0.8, 1.3, tilt=0.1), simple_mat("Hoop", (0.2, 0.19, 0.19), 0.5, var=(0.4, 0.22, 0.1), metal=0.5))
    dry = blade_mat("DryWeed", (0.17, 0.17, 0.08), (0.3, 0.3, 0.12), (0.5, 0.47, 0.24))
    pts = scatter(2200 if not PREVIEW else 300, lambda x, z: offr(x, z, 0.12) & (sample(IND["plates"], x, z) < 0.3) &
                  ((sample(IND["flags"], x, z) + sample(IND["cobble"], x, z) + sample(IND["ballast"], x, z) + sample(IND["apron"], x, z) > 0.3) |
                   (rnd(x) < 0.3)) & (sample(IND["slag"], x, z) < 0.3))
    merged("Weeds", tuft_template(7, 0.08, 0.01), place_list(pts, 0.6, 1.2), dry)
    pts = scatter(2600 if not PREVIEW else 400, lambda x, z: sample(IND["ballast"], x, z) > 0.4)
    merged("Ballast", blob_template(1), place_list(pts, 0.012, 0.026, sink=0.35),
           simple_mat("BallastStone", (0.2, 0.19, 0.18), 0.85, var=(0.38, 0.36, 0.33)))
    pts = scatter(260 if not PREVIEW else 60, lambda x, z: (rd(x, z) < HALF - 0.1) & (sample(lane, x, z) < 0.5))
    merged("RoadCoke", blob_template(1), place_list(pts, 0.012, 0.03, sink=0.35),
           simple_mat("RoadCoke", (0.06, 0.06, 0.065), 0.5, var=(0.15, 0.15, 0.16)))
elif THEME == "railyard":
    build_tracks((0.2, 0.15, 0.11), (0.38, 0.33, 0.28))
    rnd = lambda x: RNG.random(np.shape(x))
    tt_out = lambda x, z: np.hypot(x - TURNTABLE[0], z - TURNTABLE[1]) > TURNTABLE[2] + 0.2
    pts = scatter(9000 if not PREVIEW else 1500, lambda x, z: (sample(IND["ballast"], x, z) > 0.35) & tt_out(x, z))
    merged("Ballast", blob_template(1), place_list(pts, 0.012, 0.027, sink=0.35),
           simple_mat("BallastStone", (0.32, 0.3, 0.27), 0.85, var=(0.56, 0.53, 0.48)))
    wd_ = blade_mat("Weeds", (0.17, 0.22, 0.08), (0.3, 0.4, 0.13), (0.52, 0.58, 0.26))
    pts = scatter(5500 if not PREVIEW else 800, lambda x, z: (rd(x, z) > HALF + 0.08) & (sample(BLK_ANY, x, z) > 0.15) & tt_out(x, z) &
                  (rnd(x) < 0.08 + 0.92 * sample(IND["weeds"], x, z)) & (sample(IND["coal"], x, z) < 0.4) & (sample(IND["pads"], x, z) < 0.01))
    merged("Weeds", tuft_template(8, 0.1, 0.011), place_list(pts, 0.6, 1.3), wd_)
    # rosebay willowherb, the railway weed: tall tufts in clumps at the yard's margins, pink spikes in them
    centres = scatter(70 if not PREVIEW else 20, lambda x, z: (rd(x, z) > HALF + 0.4) & (sample(IND["ballast"], x, z) < 0.2) & tt_out(x, z) &
                      (sample(BLK_ANY, x, z) > 0.4) & (sample(IND["weeds"], x, z) > 0.3) & (sample(IND["pads"], x, z) < 0.01))
    pts, fl_ = [], []
    for cx, cz in centres:
        for _ in range(int(RNG.integers(4, 10))):
            pts.append((cx + RNG.normal(0, 0.12), cz + RNG.normal(0, 0.12)))
            if RNG.random() < 0.6:
                fl_.append((pts[-1][0] + RNG.normal(0, 0.02), pts[-1][1] + RNG.normal(0, 0.02)))
    merged("Willowherb", tuft_template(10, 0.17, 0.012), place_list(pts, 0.8, 1.2), wd_)
    merged("WillowFlowers", flower_template(6, 0.03), [((p_[0], p_[1], p_[2] + 0.06), y, s_, t) for (p_, y, s_, t) in place_list(fl_, 0.8, 1.2)],
           simple_mat("Willow", (0.85, 0.33, 0.6), 0.5, var=(0.95, 0.45, 0.72)))
    coalm = simple_mat("Coal", (0.035, 0.035, 0.04), 0.3, var=(0.11, 0.11, 0.12), metal=0.2)
    pts = scatter(2200 if not PREVIEW else 300, lambda x, z: (rd(x, z) > HALF) & (sample(blk["coal"], x, z) > -0.25) & tt_out(x, z) &
                  (rnd(x) < np.clip(sample(IND["coal"], x, z) * 1.2, 0, 1) * 0.9))
    merged("Coal", blob_template(1), place_list(pts, 0.016, 0.042, sink=0.3, tilt=0.5), coalm)
    pts = scatter(4000 if not PREVIEW else 600, lambda x, z: (rd(x, z) < HALF - 0.05) & (sample(lane, x, z) < 0.5) & (sample(IND["xing"], x, z) < 0.2))
    merged("Gravel", blob_template(1), place_list(pts, 0.01, 0.024, sink=0.35),
           simple_mat("Gravel", (0.4, 0.38, 0.34), 0.8, var=(0.6, 0.57, 0.52)))
    # spare rails and old sleepers lying beside the tracks
    spares, stack = [], []
    tr2 = np.random.default_rng(73)
    for t in TRACKS:
        P = t["pts"]
        if len(P) < 120:
            continue
        for _ in range(2):
            i_ = int(tr2.integers(30, len(P) - 60))
            d_ = P[i_ + 20] - P[i_]
            d_ /= np.linalg.norm(d_)
            n_ = np.array([-d_[1], d_[0]]) * tr2.choice([-1, 1])
            q_ = P[i_] + n_ * 0.85
            if _at(dist, q_[0], q_[1]) < HALF + 1.5 or _at(BLK_ANY, q_[0], q_[1]) < 0.6 or _at(tk_d, q_[0], q_[1]) < 0.75:
                continue
            yaw = math.atan2(d_[1], d_[0])
            if tr2.random() < 0.5:
                for sg in (-1, 1):
                    spares.append((q_[0] + n_[0] * 0.05 * sg, q_[1] + n_[1] * 0.05 * sg, yaw + tr2.normal(0, 0.02), 2.2, 0.045, 0.04,
                                   float(hgt(q_[0], q_[1])) - 0.005))
            else:
                for lay in range(int(tr2.integers(1, 3))):
                    for k_ in range(int(tr2.integers(3, 6))):
                        o_ = (k_ - 2) * 0.14
                        stack.append((q_[0] + d_[0] * o_, q_[1] + d_[1] * o_, yaw + 1.5708 + tr2.normal(0, 0.05) + lay * 0.0, 0.95, 0.12, 0.04,
                                      float(hgt(q_[0], q_[1])) - 0.005 + lay * 0.04))
    boxes_mesh("SpareRails", spares, simple_mat("SpareRail", (0.3, 0.16, 0.08), 0.6, var=(0.42, 0.24, 0.12), metal=0.3))
    boxes_mesh("OldSleepers", stack, simple_mat("OldSleeper", (0.24, 0.19, 0.14), 0.85, var=(0.4, 0.35, 0.29)))
elif THEME == "smog":
    build_tracks((0.2, 0.15, 0.11), (0.38, 0.33, 0.28))
    rnd = lambda x: RNG.random(np.shape(x))
    wr = np.random.default_rng(79)
    walls, cope = [], []
    for run in WALLS:
        P = np.asarray(run)
        a_, b_ = P[0], P[-1]
        L_ = float(np.hypot(*(b_ - a_)))
        if L_ < 0.15:
            continue
        mid_ = (a_ + b_) / 2
        yaw = math.atan2(b_[1] - a_[1], b_[0] - a_[0])
        base = float(hgt(P[:, 0], P[:, 1]).min()) - 0.01
        hw_ = wr.uniform(0.055, 0.085)
        walls.append((mid_[0], mid_[1], yaw, L_ + 0.075, 0.075, hw_, base))
        cope.append((mid_[0], mid_[1], yaw, L_ + 0.09, 0.095, 0.014, base + hw_))
    boxes_mesh("Walls", walls, simple_mat("WallBrick", (0.27, 0.15, 0.11), 0.85, var=(0.4, 0.23, 0.16)))
    boxes_mesh("WallCoping", cope, simple_mat("WallCoping", (0.3, 0.28, 0.26), 0.8, var=(0.44, 0.41, 0.37)))
    bol = []
    for (bx, bz, hw, hh, rc) in POOLS:                               # bollards round the dock pools
        for k_ in range(10):
            q = 2 * math.pi * k_ / 10 + 0.3
            dx, dz = math.cos(q), math.sin(q)
            sx_ = hw + 0.17
            sz_ = hh + 0.17
            t_ = min(sx_ / max(abs(dx), 1e-6), sz_ / max(abs(dz), 1e-6))
            x_, z_ = bx + dx * t_ * 0.97, bz + dz * t_ * 0.97
            if math.hypot(x_ - bx, z_ - bz) < hw + 0.6 and _at(dist, x_, z_) > HALF + 0.6:
                bol.append((x_, z_))
    merged("Bollards", cyl_template(0.045, 0.1), place_list(bol, 1.0, 1.0), simple_mat("Bollard", (0.06, 0.06, 0.07), 0.45, metal=0.4))
    yard = lambda x, z: (sample(IND["pave"], x, z) < 0.1) & (rd(x, z) > HALF + 0.5) & (sample(BLK_ANY, x, z) > 0.15) & \
        (sample(IND["water"], x, z) < 0.1) & (sample(IND["coping"], x, z) < 0.1)
    wd_ = blade_mat("Weeds", (0.13, 0.17, 0.07), (0.25, 0.32, 0.11), (0.44, 0.48, 0.22))
    pts = scatter(3200 if not PREVIEW else 500, lambda x, z: yard(x, z) & (sample(IND["y_waste"], x, z) > 0.5) & (sample(IND["wall"], x, z) < 0.5))
    merged("Weeds", tuft_template(8, 0.1, 0.011), place_list(pts, 0.6, 1.3), wd_)
    pts = scatter(1600 if not PREVIEW else 300, lambda x, z: yard(x, z) & (np.abs(sample(IND["wall"], x, z) - 0.25) < 0.2) &
                  (sample(IND["y_quay"], x, z) < 0.5))
    merged("WallWeeds", tuft_template(6, 0.07, 0.009), place_list(pts, 0.6, 1.2), wd_)
    pts = scatter(700 if not PREVIEW else 150, lambda x, z: yard(x, z) & ((sample(IND["y_flags"], x, z) + sample(IND["y_cobble"], x, z) +
                                                                          sample(IND["lane"], x, z)) > 0.5) & (rnd(x) < 0.5))
    merged("CrackWeeds", tuft_template(5, 0.05, 0.008), place_list(pts, 0.6, 1.1), wd_)
    pts = scatter(650 if not PREVIEW else 120, lambda x, z: yard(x, z) & (sample(IND["y_waste"], x, z) > 0.5))
    merged("Bricks", box_template(0.07, 0.034, 0.024), place_list(pts, 0.7, 1.3, sink=0.2, tilt=0.4),
           simple_mat("Brickbat", (0.32, 0.16, 0.11), 0.85, var=(0.48, 0.26, 0.17)))
    pts = scatter(900 if not PREVIEW else 150, lambda x, z: (yard(x, z) & (rnd(x) < 0.5)) | ((sample(IND["gutter"], x, z) > 0.4) & (rnd(x) < 0.4)))
    merged("Soot", blob_template(1), place_list(pts, 0.01, 0.026, sink=0.35),
           simple_mat("SootLump", (0.05, 0.05, 0.055), 0.6, var=(0.14, 0.14, 0.15)))
    pts = scatter(350 if not PREVIEW else 60, lambda x, z: yard(x, z) & (sample(IND["y_waste"], x, z) + sample(IND["y_earth"], x, z) > 0.5))
    merged("Stones", blob_template(1), place_list(pts, 0.02, 0.05, sink=0.4, tilt=0.3),
           simple_mat("Stone", (0.3, 0.29, 0.27), 0.8, var=(0.46, 0.44, 0.4)))
elif THEME == "military":
    rnd = lambda x: RNG.random(np.shape(x))
    pv_s = np.maximum.reduce([IND["conc"], IND["rwy"], IND["blast"], rd_hard])
    edgeb = gaussian_filter(pv_s, 0.12 * MPX)
    turf = lambda x, z: (sample(pv_s, x, z) < 0.03) & (sample(IND["crater"], x, z) < 0.05)
    turf_b = blade_mat("Turf", (0.32, 0.37, 0.15), (0.42, 0.47, 0.2), (0.58, 0.59, 0.32))
    pts = scatter(9000 if not PREVIEW else 1500, lambda x, z: turf(x, z) & (rnd(x) < 0.35 + 0.65 * sample(IND["mow"], x, z)))
    merged("Tufts", tuft_template(8, 0.07, 0.011), place_list(pts, 0.7, 1.3), turf_b)
    pts = scatter(5000 if not PREVIEW else 700, lambda x, z: turf(x, z) & (sample(edgeb, x, z) > 0.06))
    merged("EdgeTufts", tuft_template(7, 0.09, 0.012), place_list(pts, 0.8, 1.3), turf_b)
    pts = scatter(700 if not PREVIEW else 100, lambda x, z: (sample(IND["conc"], x, z) > 0.5) & (rnd(x) < 0.5) & (sample(IND["haz"], x, z) < 0.1))
    merged("JointWeeds", tuft_template(5, 0.04, 0.008), place_list(pts, 0.7, 1.2), turf_b)
    # round the craters: broken concrete and asphalt where they blew through paving, clods and charred lumps elsewhere
    near_c = lambda x, z: (sample(IND["rim"], x, z) > 0.25) | ((sample(IND["scorch"], x, z) > 0.45) & (rnd(x) < 0.25))
    pts = scatter(700 if not PREVIEW else 120, lambda x, z: near_c(x, z) & (sample(pv_s, x, z) > 0.5) & (rd(x, z) > HALF + 0.05))
    merged("Rubble", box_template(0.09, 0.07, 0.035), place_list(pts, 0.5, 1.5, sink=0.01, tilt=0.5),
           simple_mat("Rubble", (0.42, 0.41, 0.39), 0.85, var=(0.6, 0.59, 0.56)))
    pts = scatter(800 if not PREVIEW else 150, lambda x, z: near_c(x, z) & (sample(pv_s, x, z) < 0.5))
    merged("Clods", blob_template(1), place_list(pts, 0.025, 0.055, sink=0.35, tilt=0.5),
           simple_mat("Clod", (0.22, 0.16, 0.11), 0.9, var=(0.34, 0.26, 0.18)))
    pts = scatter(500 if not PREVIEW else 80, lambda x, z: (sample(IND["scorch"], x, z) > 0.35) & (rd(x, z) > HALF + 0.05))
    merged("Charred", blob_template(1), place_list(pts, 0.015, 0.04, sink=0.4, tilt=0.6),
           simple_mat("Charred", (0.06, 0.05, 0.045), 0.85, var=(0.14, 0.12, 0.1)))
    # the edge lights: a short grey post, a coloured glass cap
    posts, caps = [], {0: [], 1: [], 2: [], 3: []}
    for (x_, z_, k_) in LIGHTS:
        h_ = float(hgt(x_, z_))
        posts.append(((x_, -z_, h_), 0.0, 1.0, None))
        caps[k_].append(((x_, -z_, h_ + 0.05), 0.0, 0.02, None))
    merged("LightPosts", cyl_template(0.016, 0.05, 8, 1.2), posts, simple_mat("LightPost", (0.3, 0.31, 0.32), 0.5, metal=0.4))
    for k_, (col, em) in {0: ((0.95, 0.93, 0.8), (1.0, 0.95, 0.75)), 1: ((0.2, 0.4, 1.0), (0.25, 0.45, 1.0)),
                          2: ((0.2, 0.9, 0.35), (0.2, 1.0, 0.4)), 3: ((0.95, 0.15, 0.1), (1.0, 0.15, 0.1))}.items():
        merged("LightCaps%d" % k_, ball_template(1), caps[k_], simple_mat("LightCap%d" % k_, col, 0.3, emit=em, strength=1.5))
elif THEME == "metro":
    rnd = lambda x: RNG.random(np.shape(x))
    soil = lambda x, z: (sample(IND["beds"], x, z) > 0.5) | (sample(IND["planter"], x, z) > 0.65)
    pts = scatter(1400 if not PREVIEW else 200, soil)
    merged("Shrubs", blob_template(2), place_list(pts, 0.05, 0.11, sink=0.3, tilt=0.2),
           simple_mat("Shrub", (0.16, 0.3, 0.12), 0.8, var=(0.28, 0.45, 0.18)))
    for k, col in enumerate([(0.95, 0.95, 0.9), (0.95, 0.75, 0.2), (0.85, 0.3, 0.45), (0.6, 0.45, 0.85)]):
        centres = scatter(28 if not PREVIEW else 8, soil)
        fl_ = [(cx + RNG.normal(0, 0.07), cz + RNG.normal(0, 0.07)) for cx, cz in centres for _ in range(int(RNG.integers(5, 12)))]
        fl_ = [p_ for p_ in fl_ if _at(IND["beds"], p_[0], p_[1]) > 0.5 or _at(IND["planter"], p_[0], p_[1]) > 0.65]
        merged("Flowers%d" % k, flower_template(5, 0.024), place_list(fl_, 0.8, 1.2), simple_mat("Fl%d" % k, col, 0.6))
    gr_ = blade_mat("Grass", (0.2, 0.33, 0.12), (0.32, 0.48, 0.18), (0.5, 0.64, 0.28))
    pts = scatter(3500 if not PREVIEW else 500, lambda x, z: (sample(IND["l_lawn"], x, z) > 0.5) & (sample(IND["beds"], x, z) < 0.2) &
                  (sample(IND["lpath"], x, z) < 0.2))
    merged("Tufts", tuft_template(7, 0.06, 0.01), place_list(pts, 0.7, 1.2), gr_)
    pts = scatter(260 if not PREVIEW else 40, lambda x, z: sample(IND["pit"], x, z) > 0.5)
    merged("PitWeeds", tuft_template(5, 0.05, 0.008), place_list(pts, 0.7, 1.1), gr_)
    pts = scatter(500 if not PREVIEW else 80, lambda x, z: ((sample(IND["side"], x, z) > 0.5) | (sample(IND["plaza"], x, z) > 0.5)) & (rnd(x) < 0.4))
    merged("Leaves", leaf_template(0.025, 0.012), place_list(pts, 0.8, 1.3), simple_mat("Leaf", (0.42, 0.33, 0.12), 0.7, var=(0.55, 0.4, 0.15)))
elif THEME == "suburb":
    rnd = lambda x: RNG.random(np.shape(x))
    bed = lambda x, z: (sample(IND["fbed"], x, z) > 0.5)
    pts = scatter(1500 if not PREVIEW else 250, bed)
    merged("Shrubs", blob_template(2), place_list(pts, 0.045, 0.1, sink=0.3, tilt=0.2),
           simple_mat("Shrub", (0.15, 0.32, 0.11), 0.8, var=(0.28, 0.5, 0.17)))
    for k, col in enumerate([(0.97, 0.97, 0.94), (1.0, 0.82, 0.2), (0.95, 0.35, 0.55), (0.92, 0.22, 0.16), (0.62, 0.48, 0.92), (1.0, 0.55, 0.15)]):
        centres = scatter(45 if not PREVIEW else 10, bed)
        fl_ = [(cx + RNG.normal(0, 0.06), cz + RNG.normal(0, 0.06)) for cx, cz in centres for _ in range(int(RNG.integers(6, 14)))]
        fl_ = [p_ for p_ in fl_ if _at(IND["fbed"], p_[0], p_[1]) > 0.5]
        merged("Flowers%d" % k, flower_template(5, 0.026), place_list(fl_, 0.8, 1.25), simple_mat("Fl%d" % k, col, 0.6))
    lawn_b = blade_mat("Lawn", (0.18, 0.36, 0.1), (0.3, 0.52, 0.16), (0.48, 0.7, 0.26))
    lw = lambda x, z: sample(IND["lawn"], x, z) > 0.6
    edgel = gaussian_filter(1 - IND["lawn"], 0.1 * MPX)
    pts = scatter(6000 if not PREVIEW else 900, lambda x, z: lw(x, z) & (sample(edgel, x, z) > 0.1))
    merged("EdgeTufts", tuft_template(7, 0.06, 0.01), place_list(pts, 0.7, 1.2), lawn_b)
    pts = scatter(7000 if not PREVIEW else 1000, lambda x, z: lw(x, z) & (rnd(x) < 0.5))
    merged("Tufts", tuft_template(6, 0.04, 0.009), place_list(pts, 0.7, 1.2), lawn_b)
    toys = scatter(14, lambda x, z: lw(x, z) & (sample(edgel, x, z) < 0.05) & (rd(x, z) > HALF + 1.2))
    for k, col in enumerate([(0.9, 0.15, 0.12), (0.15, 0.4, 0.9), (1.0, 0.8, 0.1)]):
        merged("Ball%d" % k, ball_template(2), [((x_, -z_, float(hgt(x_, z_)) + 0.03), 0.0, 0.03, None) for (x_, z_) in toys[k::3]],
               simple_mat("Ball%d" % k, col, 0.35))
elif THEME == "lab":
    # pipe stubs at the tanks' pads (a flanged steel stub, capped), yellow bollards where the walkways meet a track
    merged("PipeStubs", cyl_template(0.06, 0.13, 12, 1.45), place_list([(x_, z_) for x_, z_, _t in STUBS], 1.0, 1.0),
           simple_mat("PipeStub", (0.62, 0.65, 0.7), 0.3, metal=0.8))
    merged("PipeCaps", cyl_template(0.03, 0.17, 10, 1.0), place_list([(x_, z_) for x_, z_, _t in STUBS], 1.0, 1.0),
           simple_mat("PipeCap", (0.2, 0.5, 0.85), 0.35))
    merged("Bollards", cyl_template(0.045, 0.24, 12, 1.15), place_list(BOLL, 1.0, 1.0),
           simple_mat("Bollard", (0.95, 0.72, 0.08), 0.4))
elif THEME == "satellite":
    rnd = lambda x: RNG.random(np.shape(x))
    open_ = lambda x, z, m_: (sample(ped, x, z) > m_) & (sample(sat_clear, x, z) > 0.12) & (sample(IND["trn"], x, z) < 0.2) & \
        (sample(gate_m, x, z) < 0.05)
    pts = scatter(1800 if not PREVIEW else 300, lambda x, z: open_(x, z, 0.35) & (rnd(x) < 0.25 + 0.75 * sample(IND["pave"], x, z)))
    merged("Pebbles", blob_template(1), place_list(pts, 0.014, 0.034, sink=0.35, tilt=0.4),
           simple_mat("Pebble", (0.26, 0.17, 0.12), 0.7, var=(0.48, 0.36, 0.27)))
    pts = scatter(420 if not PREVIEW else 80, lambda x, z: open_(x, z, 0.5))
    merged("Stones", blob_template(2), place_list(pts, 0.04, 0.09, sink=0.4, tilt=0.4),
           simple_mat("Stone", (0.36, 0.22, 0.15), 0.75, var=(0.55, 0.42, 0.32)))
    pts = scatter(60, lambda x, z: open_(x, z, 0.9))
    merged("Rocks", blob_template(2), place_list(pts, 0.1, 0.2, sink=0.45, tilt=0.3),
           simple_mat("Rock", (0.4, 0.26, 0.18), 0.7, var=(0.56, 0.42, 0.32)))
    pts = scatter(900 if not PREVIEW else 150, lambda x, z: (np.abs(sample(ped, x, z) - 0.15) < 0.14) & (sample(gate_m, x, z) < 0.05) &
                  (sample(sat_clear, x, z) > 0.05))
    merged("BermGravel", blob_template(1), place_list(pts, 0.012, 0.026, sink=0.3, tilt=0.4),
           simple_mat("BermGravel", (0.42, 0.33, 0.26), 0.8, var=(0.6, 0.5, 0.4)))
    scrub = blade_mat("Scrub", (0.24, 0.22, 0.13), (0.38, 0.36, 0.22), (0.56, 0.54, 0.38))
    centres = scatter(140 if not PREVIEW else 30, lambda x, z: open_(x, z, 0.8) & (sample(IND["pave"], x, z) < 0.3))
    pts = [(cx + RNG.normal(0, 0.12), cz + RNG.normal(0, 0.12)) for cx, cz in centres for _ in range(int(RNG.integers(2, 7)))]
    pts = [p_ for p_ in pts if _at(ped, p_[0], p_[1]) > 0.6 and _at(sat_clear, p_[0], p_[1]) > 0.15]
    merged("Scrub", tuft_template(9, 0.09, 0.012), place_list(pts, 0.7, 1.4), scrub)
    # the compound's fence: posts, a top rail and a mid rail between them; reflector posts along the roads
    posts, rails = [], []
    for run in FENCE:
        P = np.asarray(run)
        for (x_, z_) in P:
            posts.append((x_, z_, 0.0, 0.045, 0.045, 0.34, float(hgt(x_, z_)) - 0.01))
        for a_, b_ in zip(P[:-1], P[1:]):
            m_, L_ = (a_ + b_) / 2, float(np.hypot(*(b_ - a_)))
            yaw = math.atan2(b_[1] - a_[1], b_[0] - a_[0])
            h_ = float(hgt(m_[0], m_[1]))
            rails.append((m_[0], m_[1], yaw, L_, 0.022, 0.022, h_ + 0.31))
            rails.append((m_[0], m_[1], yaw, L_, 0.014, 0.014, h_ + 0.16))
    boxes_mesh("FencePosts", posts, simple_mat("FencePost", (0.5, 0.52, 0.55), 0.45, metal=0.6))
    boxes_mesh("FenceRails", rails, simple_mat("FenceRail", (0.62, 0.64, 0.67), 0.4, metal=0.7))
    rp_ = [(x_, z_, a_ + math.pi / 2, 0.04, 0.04, 0.2, float(hgt(x_, z_)) - 0.01) for (x_, z_, a_) in RPOST]
    boxes_mesh("ReflectorPosts", rp_, simple_mat("ReflectorPost", (0.9, 0.9, 0.88), 0.5))
    rc_ = [(x_, z_, a_ + math.pi / 2, 0.046, 0.046, 0.045, float(hgt(x_, z_)) + 0.15) for (x_, z_, a_) in RPOST]
    boxes_mesh("Reflectors", rc_, simple_mat("Reflector", (0.95, 0.35, 0.12), 0.3, emit=(1.0, 0.4, 0.1), strength=1.5))
elif THEME == "cooling":
    # pipes along the channels (frosted steel, flanges every 1.2, saddles under them), ice chunks on the crusts and
    # spills, frost lumps on the pads' rims
    pipe_m = simple_mat("Pipe", (0.6, 0.66, 0.72), 0.35, var=(0.86, 0.91, 0.96), metal=0.55)
    tube_mesh("Pipes", [(P_, r_, r_) for P_, r_ in PIPES], pipe_m)
    fl_, sd_ = [], []
    for P_, r_ in PIPES:
        cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P_, axis=0).T))])
        for s_ in list(np.arange(0.15, cum[-1] - 0.1, 1.2)) + [cum[-1] - 0.04]:
            x_, z_ = np.interp(s_, cum, P_[:, 0]), np.interp(s_, cum, P_[:, 1])
            i_ = min(len(P_) - 2, int(np.searchsorted(cum, s_)))
            a_ = math.atan2(P_[i_ + 1, 1] - P_[i_, 1], P_[i_ + 1, 0] - P_[i_, 0])
            fl_.append((x_, z_, a_, 0.04, r_ * 2.7, r_ * 2.7, float(hgt(x_, z_)) - r_ * 0.35))
            if s_ + 0.6 < cum[-1]:
                x2, z2 = np.interp(s_ + 0.6, cum, P_[:, 0]), np.interp(s_ + 0.6, cum, P_[:, 1])
                sd_.append((x2, z2, a_, 0.06, r_ * 3.0, r_ * 0.8, float(hgt(x2, z2)) - 0.005))
    boxes_mesh("PipeFlanges", fl_, simple_mat("Flange", (0.5, 0.55, 0.6), 0.4, var=(0.8, 0.86, 0.92), metal=0.6))
    boxes_mesh("PipeSaddles", sd_, simple_mat("Saddle", (0.2, 0.22, 0.25), 0.6, metal=0.4))
    ice_m = simple_mat("IceChunk", (0.74, 0.9, 1.0), 0.08, var=(0.92, 0.98, 1.0))
    off_rd = lambda x, z: (sample(ped, x, z) > 0.12) & (sample(vsm, x, z) > 0.05) & (sample(pp_m, x, z) > 0.12)
    pts = scatter(900 if not PREVIEW else 150, lambda x, z: off_rd(x, z) & (sample(IND["ice"], x, z) > 0.6))
    merged("IceChunks", blob_template(1), place_list(pts, 0.018, 0.05, sink=0.45, tilt=0.5), ice_m)
    pts = scatter(260 if not PREVIEW else 50, lambda x, z: off_rd(x, z) & (sample(IND["ice"], x, z) > 0.6))
    merged("IceShards", box_template(0.05, 0.03, 0.06), place_list(pts, 0.6, 1.4, sink=0.25, tilt=0.7), ice_m)
    pts = scatter(700 if not PREVIEW else 120, lambda x, z: off_rd(x, z) & (sample(IND["frost"], x, z) > 0.75) & (sample(IND["ice"], x, z) < 0.3)
                  & (sample(BLK_ANY, x, z) > 0.1) & (RNG.random(np.shape(x)) < 0.4))
    merged("Frost", blob_template(1), place_list(pts, 0.01, 0.025, sink=0.55, tilt=0.3), simple_mat("Rime", (0.88, 0.93, 0.98), 0.85))
elif THEME == "server":
    # in the open bays: a stack of lifted floor tiles in a corner, cables lying across the subfloor
    st_, cb_ = [], {0: [], 1: [], 2: []}
    for k_, (cx, cz) in enumerate(OB):
        for j in range(4):
            x_, z_ = cx + 0.72 + RNG.normal(0, 0.02), cz - 0.42 + RNG.normal(0, 0.02)
            st_.append((x_, z_, RNG.normal(0, 0.12), 0.58, 0.58, 0.028, float(hgt(cx + 0.72, cz - 0.42)) + j * 0.03))
        for j in range(3):
            zz = cz - 0.5 + j * 0.42 + RNG.uniform(-0.08, 0.08)
            xs_ = np.linspace(cx - 1.12, cx + 1.12, 40)
            P_ = np.stack([xs_, zz + 0.05 * np.sin(xs_ * RNG.uniform(1.5, 3.0) + RNG.uniform(0, 6))], 1)
            cb_[j].append((P_, 0.018, 0.018))
    boxes_mesh("LiftedTiles", st_, simple_mat("LiftedTile", (0.4, 0.42, 0.46), 0.6, var=(0.46, 0.48, 0.52)))
    for j, col in enumerate([(0.12, 0.3, 0.8), (0.85, 0.72, 0.15), (0.55, 0.57, 0.6)]):
        tube_mesh("Cables%d" % j, cb_[j], simple_mat("Cable%d" % j, col, 0.5), sides=6)
elif THEME == "core":
    # the battle's debris round the craters and the blast scorches: shards of dark metal, white robot armour plates,
    # lumps of slag, a few cables
    near_b = lambda x, z: ((sample(IND["rim"], x, z) > 0.3) | (sample(IND["scorch"], x, z) > 0.35) | (sample(IND["crater"], x, z) > 0.4)) & \
        (sample(ped, x, z) > 0.1) & (sample(_down(HD["so_r"]), x, z) > 1.15) & (sample(pzm, x, z) > 0.05)
    pts = scatter(900 if not PREVIEW else 150, near_b)
    merged("Shards", box_template(0.08, 0.035, 0.006), place_list(pts, 0.6, 1.6, sink=0.1, tilt=0.6),
           simple_mat("Shard", (0.12, 0.12, 0.14), 0.4, var=(0.3, 0.3, 0.34), metal=0.7))
    pts = scatter(220 if not PREVIEW else 40, near_b)
    merged("Plates", box_template(0.13, 0.09, 0.012), place_list(pts, 0.6, 1.4, sink=0.1, tilt=0.5),
           simple_mat("RobotPlate", (0.82, 0.83, 0.85), 0.35, var=(0.62, 0.62, 0.64)))
    pts = scatter(60 if not PREVIEW else 12, near_b)
    merged("HazardPlates", box_template(0.11, 0.07, 0.012), place_list(pts, 0.7, 1.3, sink=0.1, tilt=0.5),
           simple_mat("HazardPlate", (0.95, 0.45, 0.1), 0.45))
    pts = scatter(400 if not PREVIEW else 80, near_b)
    merged("Slag", blob_template(1), place_list(pts, 0.015, 0.04, sink=0.35, tilt=0.4),
           simple_mat("Slag", (0.05, 0.05, 0.06), 0.5, var=(0.16, 0.15, 0.17), metal=0.5))
    cb_ = []
    for (bx, bz, R) in WRK:
        for _k in range(5):
            a_ = RNG.uniform(0, 2 * math.pi)
            r0, r1 = R * RNG.uniform(0.3, 0.7), R * RNG.uniform(1.1, 1.5)
            t_ = np.linspace(0, 1, 30)
            P_ = np.stack([bx + np.cos(a_ + 0.3 * np.sin(t_ * 5)) * (r0 + (r1 - r0) * t_), bz + np.sin(a_ + 0.3 * np.sin(t_ * 5)) * (r0 + (r1 - r0) * t_)], 1)
            if sample(ped, P_[:, 0], P_[:, 1]).min() > 0.15:
                cb_.append((P_, 0.016, 0.016))
    tube_mesh("Cables", cb_, simple_mat("Cable", (0.08, 0.08, 0.09), 0.5), sides=6)
elif THEME == "neon":
    rnd = lambda x: RNG.random(np.shape(x))
    lot = lambda x, z: (sample(ped, x, z) > 0.2) & (sample(ptm, x, z) > 1.4) & (sample(BLK_ANY, x, z) > 0.2)
    pts = scatter(260 if not PREVIEW else 50, lambda x, z: lot(x, z) & (rnd(x) < 0.5))
    third = len(pts) // 3
    for k_, (col, em_) in enumerate((((0.9, 0.2, 0.75), (1.0, 0.25, 0.85)), ((0.15, 0.85, 0.95), (0.2, 0.9, 1.0)), ((0.85, 0.85, 0.9), None))):
        sub_ = pts[k_ * third:(k_ + 1) * third]
        merged("Flyers%d" % k_, box_template(0.07, 0.05, 0.002), place_list(sub_, 0.8, 1.3),
               simple_mat("Flyer%d" % k_, col, 0.6, emit=em_, strength=0.4 if em_ else 0.0))
    pts = scatter(140 if not PREVIEW else 30, lambda x, z: lot(x, z))
    merged("Cans", cyl_template(0.018, 0.05, 8, 1.0), place_list(pts, 0.9, 1.1, tilt=1.5),
           simple_mat("Can", (0.6, 0.62, 0.68), 0.3, var=(0.8, 0.2, 0.5), metal=0.7))
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
if "--dry" in A:                         # (build the scene only: a quick check that it builds, no render)
    sys.exit(0)

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
          "jungle": 0.3, "harbor": 0.56, "fortress": 0.4, "factory": 0.31, "railyard": 0.36, "smog": 0.31,
          "military": 0.42, "metro": 0.37, "suburb": 0.42, "lab": 0.62, "satellite": 0.42, "neon": 0.2,
          "cooling": 0.5, "server": 0.3, "core": 0.17}[THEME]
mask_in = (sample(outside, X, Z) < 0.5)
mi = np.asarray(Image.fromarray((mask_in * 255).astype(np.uint8)).resize((im.shape[1], im.shape[0]))) > 127
cur = im[mi].mean()
im = np.clip(im * (TARGET / max(cur, 1e-3)) ** 0.8, 0, 1)
import ground_fade                       # the outer band blends to one colour: no seam against the far-ground plane
im = ground_fade.fade(im, 1.6 * PX)
Image.fromarray((im * 255 + 0.5).astype(np.uint8)).save(OUT)
os.remove(OUT + ".raw.png")
log("wrote", OUT, im.shape, "mean %.3f -> %.3f" % (cur, im[mi].mean()))
