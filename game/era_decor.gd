## World dressing for eras 3-10 (Iron Age .. The Data Center): lighting/colors per theme,
## scattered props, the 3D look of no-build zones ("blockers") and the human base at the end of the road.
## Called from game.gd. `g` is the game node; use its helpers g._mat, g._mi, g._box, g._cyl, g._sph,
## g._palm, g._campfire and g.effects (animated things). Everything here is visual only.
class_name EraDecor
extends RefCounted

const OLD_THEMES := ["meadow", "snow", "volcano", "delta", "desert", "canyon"]

## theme -> [far ground (matches the painted ground's outer border), ambient, ambient energy, sun, sun energy, rock]
const ENV := {
	"highland": [Color(0.159, 0.297, 0.147), Color(0.82, 0.88, 1.0), 0.36, Color(1.0, 0.95, 0.86), 0.74, Color(0.55, 0.56, 0.54)],
	"forge": [Color(0.072, 0.062, 0.061), Color(0.86, 0.8, 0.78), 0.36, Color(1.0, 0.86, 0.72), 0.78, Color(0.2, 0.18, 0.17)],
	"bog": [Color(0.133, 0.187, 0.103), Color(0.8, 0.9, 0.85), 0.38, Color(0.98, 0.96, 0.84), 0.68, Color(0.36, 0.38, 0.3)],
	"olive": [Color(0.498, 0.418, 0.218), Color(1.0, 0.94, 0.84), 0.34, Color(1.0, 0.94, 0.8), 0.7, Color(0.78, 0.74, 0.64)],
	"coast": [Color(0.640, 0.558, 0.391), Color(0.9, 0.94, 1.0), 0.36, Color(1.0, 0.96, 0.88), 0.66, Color(0.86, 0.85, 0.8)],
	"acropolis": [Color(0.247, 0.389, 0.172), Color(0.9, 0.92, 1.0), 0.36, Color(1.0, 0.95, 0.84), 0.72, Color(0.8, 0.78, 0.72)],
	"farmland": [Color(0.235, 0.352, 0.140), Color(0.85, 0.9, 1.0), 0.36, Color(1.0, 0.96, 0.86), 0.74, Color(0.56, 0.54, 0.5)],
	"castle": [Color(0.220, 0.317, 0.154), Color(0.82, 0.88, 1.0), 0.36, Color(1.0, 0.95, 0.86), 0.72, Color(0.52, 0.51, 0.5)],
	"darkwood": [Color(0.073, 0.098, 0.060), Color(0.72, 0.82, 1.0), 0.36, Color(0.85, 0.9, 1.0), 0.62, Color(0.3, 0.33, 0.3)],
	"harbor": [Color(0.314, 0.438, 0.209), Color(0.85, 0.92, 1.0), 0.36, Color(1.0, 0.96, 0.88), 0.72, Color(0.42, 0.42, 0.44)],
	"fortress": [Color(0.291, 0.318, 0.172), Color(0.88, 0.9, 0.95), 0.36, Color(1.0, 0.94, 0.82), 0.72, Color(0.5, 0.46, 0.38)],
	"jungle": [Color(0.043, 0.194, 0.068), Color(0.8, 0.95, 0.85), 0.38, Color(1.0, 0.96, 0.84), 0.72, Color(0.42, 0.46, 0.38)],
	"railyard": [Color(0.292, 0.265, 0.225), Color(0.92, 0.9, 0.88), 0.36, Color(1.0, 0.92, 0.8), 0.7, Color(0.4, 0.37, 0.33)],
	"factory": [Color(0.347, 0.313, 0.287), Color(0.95, 0.9, 0.86), 0.36, Color(1.0, 0.9, 0.78), 0.7, Color(0.5, 0.46, 0.44)],
	"smog": [Color(0.194, 0.176, 0.155), Color(0.86, 0.82, 0.76), 0.38, Color(0.96, 0.88, 0.74), 0.6, Color(0.36, 0.34, 0.32)],
	"suburb": [Color(0.229, 0.442, 0.163), Color(0.85, 0.92, 1.0), 0.36, Color(1.0, 0.97, 0.9), 0.76, Color(0.6, 0.6, 0.58)],
	"military": [Color(0.416, 0.398, 0.233), Color(0.92, 0.92, 0.9), 0.36, Color(1.0, 0.95, 0.84), 0.72, Color(0.56, 0.52, 0.42)],
	"metro": [Color(0.374, 0.384, 0.358), Color(0.88, 0.92, 1.0), 0.38, Color(1.0, 0.97, 0.92), 0.72, Color(0.6, 0.6, 0.62)],
	"neon": [Color(0.043, 0.045, 0.071), Color(0.66, 0.66, 1.0), 0.42, Color(0.7, 0.72, 1.0), 0.55, Color(0.16, 0.16, 0.22)],
	"satellite": [Color(0.655, 0.566, 0.414), Color(1.0, 0.94, 0.86), 0.34, Color(1.0, 0.95, 0.84), 0.66, Color(0.8, 0.68, 0.5)],
	"lab": [Color(0.535, 0.557, 0.566), Color(0.9, 0.95, 1.0), 0.42, Color(0.96, 0.98, 1.04), 0.62, Color(0.8, 0.82, 0.86)],
	"server": [Color(0.033, 0.038, 0.050), Color(0.62, 0.72, 1.0), 0.4, Color(0.78, 0.85, 1.0), 0.56, Color(0.18, 0.19, 0.22)],
	"cooling": [Color(0.336, 0.409, 0.468), Color(0.78, 0.88, 1.0), 0.4, Color(0.88, 0.94, 1.04), 0.62, Color(0.55, 0.62, 0.7)],
	"core": [Color(0.039, 0.024, 0.036), Color(0.92, 0.72, 0.78), 0.38, Color(1.0, 0.8, 0.8), 0.52, Color(0.14, 0.11, 0.13)],
}

## theme -> [prop count, [[kind, weight, footprint radius], ...]]
const DECOR := {
	"highland": [64, [["pine", 4.0, 0.7], ["birch", 3.0, 0.6], ["heather", 3.0, 0.5], ["boulder", 2.0, 0.6], ["stone", 1.2, 0.4], ["roundhouse", 0.6, 1.2]]],
	"forge": [56, [["forge_hut", 1.0, 1.2], ["anvil", 1.2, 0.5], ["ore_cart", 1.0, 0.6], ["dead_tree", 2.6, 0.5], ["slag", 2.0, 0.8], ["boulder", 1.6, 0.6]]],
	"bog": [66, [["willow", 2.6, 0.9], ["reeds", 4.0, 0.4], ["log", 2.0, 0.7], ["boardwalk", 1.2, 0.8], ["mist", 2.0, 1.0], ["dead_tree", 1.0, 0.5], ["bush", 1.4, 0.5]]],
	"olive": [60, [["olive", 4.0, 0.8], ["cypress", 3.0, 0.4], ["column", 1.4, 0.4], ["amphora", 1.2, 0.4], ["wall", 1.4, 0.9], ["bush", 1.6, 0.5], ["boulder", 1.0, 0.5]]],
	"coast": [56, [["cypress", 3.0, 0.4], ["boulder", 3.0, 0.6], ["shrine", 0.8, 0.8], ["boat", 0.8, 0.8], ["bush", 1.6, 0.5], ["column", 0.8, 0.4], ["amphora", 0.8, 0.4]]],
	"acropolis": [56, [["column", 2.5, 0.4], ["statue", 1.4, 0.5], ["brazier", 1.0, 0.4], ["cypress", 2.2, 0.4], ["temple_small", 0.5, 1.4], ["bush", 1.4, 0.5], ["amphora", 0.8, 0.4]]],
	"farmland": [60, [["oak", 4.0, 0.8], ["haystack", 2.4, 0.6], ["fence", 2.0, 0.8], ["cottage", 1.0, 1.1], ["bush", 1.6, 0.5]]],
	"castle": [56, [["stone_wall", 1.5, 1.0], ["banner", 1.4, 0.3], ["siege_debris", 1.0, 0.9], ["tent_med", 1.4, 0.9], ["barrels", 2.0, 0.5], ["oak", 2.0, 0.8], ["boulder", 1.0, 0.5]]],
	"darkwood": [74, [["pine", 5.0, 0.7], ["gnarled", 2.6, 0.6], ["mushrooms", 2.0, 0.4], ["fog", 2.0, 1.1], ["boulder", 1.0, 0.5], ["shrine_ruin", 0.4, 1.0]]],
	"harbor": [52, [["palm", 1.4, 0.7], ["crates", 2.0, 0.6], ["barrels", 2.0, 0.5], ["anchor", 1.0, 0.6], ["bush", 2.0, 0.5], ["boulder", 1.0, 0.5]]],
	"fortress": [56, [["cannon", 1.5, 0.7], ["gabions", 1.5, 0.7], ["earthwork", 1.5, 1.2], ["kegs", 1.5, 0.5], ["tent", 1.2, 0.9], ["flag", 1.0, 0.3], ["bush", 1.5, 0.5]]],
	"jungle": [54, [["jungle_tree", 4.0, 0.9], ["fern", 3.0, 0.5], ["flowers", 2.0, 0.5], ["vine_ruin", 1.0, 0.7], ["palm", 0.6, 0.7]]],
	"railyard": [50, [["rail_car", 1.6, 1.4], ["coal", 1.0, 0.8], ["signal", 1.5, 0.3], ["crates", 2.0, 0.6], ["barrels", 1.5, 0.5], ["water_tower", 0.4, 0.9], ["lamp", 1.2, 0.3]]],
	"factory": [50, [["factory_bldg", 1.2, 1.5], ["pipes", 1.5, 1.0], ["gear", 1.0, 0.6], ["lamp", 1.5, 0.3], ["barrels", 1.5, 0.5], ["crates", 1.5, 0.6]]],
	"smog": [54, [["terrace", 1.2, 1.6], ["lamp", 2.0, 0.3], ["barrels", 1.5, 0.5], ["dead_tree", 2.0, 0.5], ["crates", 1.0, 0.6], ["pipes", 0.8, 1.0]]],
	"suburb": [56, [["house", 1.5, 1.2], ["hedge", 2.0, 0.7], ["car", 1.2, 0.8], ["mailbox", 1.0, 0.25], ["round_tree", 3.0, 0.8], ["hoop", 0.6, 0.4], ["bush", 1.5, 0.5]]],
	"military": [50, [["hangar", 0.8, 1.6], ["jeep", 1.2, 0.7], ["sandbags", 2.0, 0.7], ["drums", 1.5, 0.5], ["fence_mil", 1.5, 0.9], ["radar", 0.5, 0.7], ["crates", 1.5, 0.6]]],
	"metro": [50, [["street_light", 2.0, 0.3], ["car", 2.0, 0.8], ["planter_tree", 2.0, 0.6], ["billboard", 1.0, 1.0], ["hydrant", 1.0, 0.2]]],
	"neon": [50, [["neon_pylon", 2.0, 0.4], ["holo_board", 1.2, 0.9], ["holo_cube", 1.5, 0.4], ["light_pole", 2.0, 0.3]]],
	"satellite": [46, [["dish", 1.5, 0.9], ["solar", 2.5, 0.9], ["mast", 1.0, 0.4], ["dome", 0.8, 1.0], ["crates", 1.0, 0.6], ["boulder", 1.0, 0.5]]],
	"lab": [46, [["tube", 1.5, 0.4], ["console", 1.5, 0.5], ["robot_arm", 1.0, 0.6], ["lab_crate", 1.5, 0.5], ["potted", 2.0, 0.3]]],
	"server": [46, [["rack_row", 3.0, 1.2], ["cables", 2.0, 0.9], ["cooling_unit", 1.2, 0.7]]],
	"cooling": [46, [["big_pipe", 2.0, 1.6], ["ice", 2.0, 0.6], ["fan", 1.2, 0.8], ["valve", 1.5, 0.4]]],
	"core": [46, [["energy_pillar", 2.0, 0.5], ["data_spire", 2.0, 0.5], ["broken_robot", 2.0, 0.7], ["cables", 1.5, 0.9]]],
}

## man-made themes: props are aligned to the grid instead of randomly turned
const GRID_THEMES := ["server", "lab", "cooling", "metro", "factory", "smog", "suburb", "military", "railyard"]

const TRUNK := Color(0.36, 0.22, 0.1)
const WOOD := Color(0.5, 0.33, 0.18)
const WOOD_D := Color(0.3, 0.18, 0.09)
const IRON := Color(0.17, 0.17, 0.19)
const MARBLE := Color(0.86, 0.84, 0.79)
const TERRACOTTA := Color(0.74, 0.36, 0.2)
const BRICK := Color(0.6, 0.27, 0.19)
const CONCRETE := Color(0.62, 0.62, 0.6)
const WHITE_PANEL := Color(0.93, 0.95, 0.97)
const CYAN := Color(0.2, 0.9, 1.0)
const MAGENTA := Color(1.0, 0.25, 0.85)
const ORANGE_PAINT := Color(0.95, 0.45, 0.1)
const OLIVE_DRAB := Color(0.36, 0.4, 0.22)


static func handles(theme_id: String) -> bool:
	return not theme_id in OLD_THEMES


## Same keys as game.gd THEMES: bg, far, ambient, ambient_e, sun, sun_e, rock, cave, base ("" = no recolor).
static func env(theme_id: String) -> Dictionary:
	var e: Array = ENV.get(theme_id, ENV["highland"])
	var far: Color = e[0]
	var rock: Color = e[5]
	return {"bg": far.darkened(0.08), "far": far, "ambient": e[1], "ambient_e": e[2], "sun": e[3], "sun_e": e[4],
		"rock": rock, "cave": rock.darkened(0.1), "base": ""}


# ================================================================== helpers
static func _m(g: Node3D, key: String, c: Color, opts: Dictionary = {}) -> StandardMaterial3D:
	var m: StandardMaterial3D = g._mat("ed_" + key, c, opts)
	return m


static func _glow(g: Node3D, key: String, c: Color, e := 2.0) -> StandardMaterial3D:
	return _m(g, key, c, {"emit": c, "emit_e": e})


static func _n(parent: Node3D, pos: Vector3, yaw := 0.0, s := 1.0) -> Node3D:
	var t := Node3D.new()
	t.position = pos
	t.rotation.y = yaw
	t.scale = Vector3.ONE * s
	parent.add_child(t)
	return t


static func _bx(g: Node3D, p: Node3D, m: Material, pos: Vector3, sz: Vector3, rot := Vector3.ZERO) -> MeshInstance3D:
	var mesh: BoxMesh = g._box(sz.x, sz.y, sz.z)
	var mi: MeshInstance3D = g._mi(mesh, m, p, pos, rot)
	return mi


static func _cy(g: Node3D, p: Node3D, m: Material, pos: Vector3, rt: float, rb: float, h: float, seg := 8, rot := Vector3.ZERO, scl := Vector3.ONE) -> MeshInstance3D:
	var mesh: CylinderMesh = g._cyl(rt, rb, h, seg)
	var mi: MeshInstance3D = g._mi(mesh, m, p, pos, rot, scl)
	return mi


static func _sp(g: Node3D, p: Node3D, m: Material, pos: Vector3, rad: float, scl := Vector3.ONE, seg := 8, rot := Vector3.ZERO) -> MeshInstance3D:
	var mesh: SphereMesh = g._sph(rad, seg)
	var mi: MeshInstance3D = g._mi(mesh, m, p, pos, rot, scl)
	return mi


## Triangular prism (gable roof): triangle in the x-y plane, ridge along z.
static func _pr(g: Node3D, p: Node3D, m: Material, pos: Vector3, sz: Vector3, rot := Vector3.ZERO, ltr := 0.5) -> MeshInstance3D:
	var mesh := PrismMesh.new()
	mesh.size = sz
	mesh.left_to_right = ltr
	var mi: MeshInstance3D = g._mi(mesh, m, p, pos, rot)
	return mi


static func _tor(g: Node3D, p: Node3D, m: Material, pos: Vector3, r_in: float, r_out: float, rot := Vector3.ZERO, rings := 16) -> MeshInstance3D:
	var mesh := TorusMesh.new()
	mesh.inner_radius = r_in
	mesh.outer_radius = r_out
	mesh.rings = rings
	mesh.ring_segments = 6
	var mi: MeshInstance3D = g._mi(mesh, m, p, pos, rot)
	return mi


static func _cap(g: Node3D, p: Node3D, m: Material, pos: Vector3, rad: float, h: float, rot := Vector3.ZERO) -> MeshInstance3D:
	var mesh := CapsuleMesh.new()
	mesh.radius = rad
	mesh.height = h
	mesh.radial_segments = 8
	mesh.rings = 2
	var mi: MeshInstance3D = g._mi(mesh, m, p, pos, rot)
	return mi


## Spins `rotor` about its local y axis (game.gd "spin" effect). `breathe` also pulses its scale.
static func _spin(g: Node3D, holder: Node3D, rotor: Node3D, breathe := false) -> void:
	if breathe:
		holder.set_meta("spin", rotor)
	else:
		var dummy := Node3D.new()
		holder.add_child(dummy)
		holder.set_meta("spin", dummy)
	holder.set_meta("core", rotor)
	g.effects.append({"node": holder, "life": INF, "t": 0.0, "kind": "spin"})


## Pulses the emission of mi's (shared) material once per material (reuses the "lava" effect, light hidden).
static func _pulse(g: Node3D, mi: MeshInstance3D, phase := 0.0) -> void:
	var m := mi.material_override as StandardMaterial3D
	if m == null or m.has_meta("ed_pulse"):
		return
	m.set_meta("ed_pulse", true)
	var l := OmniLight3D.new()
	l.visible = false
	l.light_energy = 0.0
	mi.add_child(l)
	g.effects.append({"node": mi, "life": INF, "t": phase, "kind": "lava", "pool": mi, "light": l})


## Flickering flame (game.gd campfire). light_e <= 0 hides the light so it costs nothing.
static func _flame(g: Node3D, p: Node3D, pos: Vector3, k := 1.0, light_e := 0.0) -> void:
	g._campfire(p, pos, maxf(light_e, 0.0), k)
	if light_e <= 0.0:
		var fire := p.get_child(p.get_child_count() - 1) as Node3D
		if fire != null and fire.get_child_count() > 2:
			var l := fire.get_child(2) as OmniLight3D
			if l != null:
				l.visible = false


static func _light(p: Node3D, pos: Vector3, col: Color, e: float, rng: float) -> void:
	var l := OmniLight3D.new()
	l.light_color = col
	l.light_energy = e
	l.omni_range = rng
	l.position = pos
	p.add_child(l)


## Rising smoke puffs that slowly swirl.
static func _smoke(g: Node3D, p: Node3D, pos: Vector3, k := 1.0, col := Color(0.55, 0.55, 0.56, 0.55)) -> void:
	var holder := _n(p, pos)
	var rotor := Node3D.new()
	holder.add_child(rotor)
	var m := _m(g, "smoke_" + col.to_html(), col, {"rough": 1.0})
	var offs := [Vector3(0.08, 0.25, 0.0), Vector3(-0.16, 0.7, 0.1), Vector3(0.18, 1.2, -0.08)]
	for i in 3:
		var mi := _sp(g, rotor, m, offs[i] * k, (0.28 + i * 0.1) * k, Vector3.ONE, 7)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_spin(g, holder, rotor, true)


static func _no_shadow(mi: MeshInstance3D) -> MeshInstance3D:
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi


static func _river_d(g: Node3D, p: Vector2) -> float:
	var mp: Dictionary = g.map
	var best := INF
	for rv in mp.get("rivers", []):
		var pts: Array = rv.get("pts", [])
		var hw: float = float(rv.get("width", 2.0)) * 0.5
		for i in pts.size() - 1:
			var a := Vector2(float(pts[i][0]), float(pts[i][1]))
			var b := Vector2(float(pts[i + 1][0]), float(pts[i + 1][1]))
			best = minf(best, Geometry2D.get_closest_point_to_segment(p, a, b).distance_to(p) - hw)
	return best


## x of the (first) river's centre line at depth z, or NAN when the map has no river.
static func _river_x(g: Node3D, z: float) -> float:
	var mp: Dictionary = g.map
	var rivers: Array = mp.get("rivers", [])
	if rivers.is_empty():
		return NAN
	var pts: Array = rivers[0].get("pts", [])
	for i in pts.size() - 1:
		var z0 := float(pts[i][1])
		var z1 := float(pts[i + 1][1])
		if z >= minf(z0, z1) and z <= maxf(z0, z1):
			var k := (z - z0) / maxf(z1 - z0, 0.001)
			return lerpf(float(pts[i][0]), float(pts[i + 1][0]), k)
	return float(pts[0][0])


static func _ok(g: Node3D, free: Callable, p: Vector2, rad: float, occ: Array) -> bool:
	if not free.call(p, rad * 0.4):
		return false
	if _river_d(g, p) < rad + 0.25:
		return false
	for o in occ:
		var q: Vector3 = o
		if Vector2(q.x, q.y).distance_to(p) < (q.z + rad) * 0.85:
			return false
	return true


# ================================================================== decor
## Scatter props around the map, away from the road, blockers and the base.
## free(p: Vector2, clearance: float) -> bool tells whether a ground spot is clear.
static func build_decor(g: Node3D, theme_id: String, free: Callable) -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 7919 + theme_id.hash() % 100000
	var occ: Array = []
	_landmarks(g, theme_id, free, r, occ)
	var spec: Array = DECOR.get(theme_id, DECOR["highland"])
	var target: int = spec[0]
	var kinds: Array = spec[1]
	var total := 0.0
	for k in kinds:
		total += float(k[1])
	var placed := 0
	var tries := 0
	while placed < target and tries < 2500:
		tries += 1
		var x := r.randf_range(-17.6, 16.8) if r.randf() < 0.85 else r.randf_range(-19.5, 17.5)
		var z := r.randf_range(-12.8, 12.6)
		var pick := r.randf() * total
		var kind: Array = kinds[0]
		for k in kinds:
			pick -= float(k[1])
			if pick <= 0.0:
				kind = k
				break
		var rad: float = kind[2]
		var p := Vector2(x, z)
		if not _ok(g, free, p, rad, occ):
			continue
		occ.append(Vector3(x, z, rad))
		placed += 1
		var yaw := r.randf() * TAU
		if theme_id == "satellite":
			yaw = r.randf_range(-0.08, 0.08)
		elif theme_id in GRID_THEMES:
			yaw = (r.randi() % 4) * PI * 0.5
		var t := _n(g, Vector3(x, 0, z), yaw, r.randf_range(0.85, 1.15))
		_prop(g, theme_id, str(kind[0]), t, r)


static func _prop(g: Node3D, th: String, kind: String, t: Node3D, r: RandomNumberGenerator) -> void:
	match kind:
		"pine": _pine(g, t, th)
		"birch": _birch(g, t)
		"heather": _heather(g, t, r)
		"boulder": _boulder(g, t, th, r)
		"stone": _standing_stone(g, t, r, r.randf_range(1.2, 1.9))
		"roundhouse": _roundhouse(g, t, false)
		"forge_hut": _roundhouse(g, t, true)
		"anvil": _anvil(g, t)
		"ore_cart": _ore_cart(g, t)
		"dead_tree": _dead_tree(g, t, th)
		"gnarled": _dead_tree(g, t, "darkwood")
		"slag": _slag_heap(g, t, r)
		"willow": _willow(g, t)
		"reeds": _reeds(g, t, r)
		"log": _log(g, t, th)
		"boardwalk": _boardwalk(g, t)
		"mist": _mist(g, t, 1.0)
		"fog": _mist(g, t, 1.4)
		"bush": _bush(g, t, th)
		"olive": _olive(g, t)
		"cypress": _cypress(g, t)
		"column": _column(g, t, r.randf_range(0.5, 1.7))
		"amphora": _amphorae(g, t)
		"wall": _low_wall(g, t)
		"shrine": _shrine(g, t)
		"boat": _boat(g, t)
		"statue": _statue(g, t)
		"brazier": _brazier(g, t, 0.0)
		"temple_small": _temple_front(g, t, 0.55)
		"oak": _round_tree(g, t, Color(0.16, 0.38, 0.12), Color(0.22, 0.46, 0.15), "oak", 1.0)
		"round_tree": _round_tree(g, t, Color(0.26, 0.56, 0.18), Color(0.34, 0.64, 0.22), "sub_tree", 0.9)
		"haystack": _haystack(g, t, r)
		"fence": _fence(g, t)
		"cottage": _cottage(g, t)
		"stone_wall": _stone_wall(g, t)
		"banner": _banner(g, t, Color(0.75, 0.12, 0.1) if r.randf() < 0.5 else Color(0.16, 0.26, 0.62))
		"siege_debris": _siege_debris(g, t)
		"tent_med": _tent_med(g, t, r)
		"barrels": _barrels(g, t, WOOD, "wood")
		"kegs": _barrels(g, t, Color(0.24, 0.17, 0.11), "keg")
		"drums": _drums(g, t, r.randi() % 3)
		"mushrooms": _mushrooms(g, t, r)
		"shrine_ruin": _ruin_arch(g, t, true)
		"vine_ruin": _ruin_arch(g, t, false)
		"palm": g._palm(t, Vector3.ZERO, 1.0, r)
		"crates": _crates(g, t, th, r)
		"lab_crate": _crates(g, t, "lab", r)
		"anchor": _anchor(g, t)
		"cannon": _cannon(g, t)
		"gabions": _gabions(g, t)
		"earthwork": _earthwork(g, t)
		"tent": _tent(g, t, Color(0.86, 0.82, 0.7), "canvas")
		"flag": _flag(g, t, Color(0.14, 0.22, 0.52))
		"jungle_tree": _jungle_tree(g, t)
		"fern": _fern(g, t)
		"flowers": _flowers(g, t, r)
		"rail_car": _rail_car(g, t, r)
		"coal": _coal(g, t, 1.0)
		"signal": _signal(g, t)
		"water_tower": _water_tower(g, t)
		"factory_bldg": _factory_bldg(g, t, r)
		"pipes": _pipes(g, t, th)
		"gear": _gear(g, t)
		"lamp": _lamp(g, t, Color(1.0, 0.78, 0.4))
		"terrace": _terrace(g, t, r)
		"house": _house(g, t, r)
		"hedge": _bx(g, t, _m(g, "hedge", Color(0.18, 0.42, 0.14)), Vector3(0, 0.28, 0), Vector3(1.4, 0.56, 0.45))
		"car": _car(g, t, r, th)
		"mailbox": _mailbox(g, t)
		"hoop": _hoop(g, t)
		"hangar": _hangar(g, t)
		"jeep": _jeep(g, t)
		"sandbags": _sandbags(g, t)
		"fence_mil": _fence_mil(g, t)
		"radar": _radar(g, t, 1.0)
		"street_light": _street_light(g, t)
		"planter_tree": _planter_tree(g, t)
		"billboard": _billboard(g, t, r)
		"hydrant": _hydrant(g, t)
		"neon_pylon": _neon_pylon(g, t, r, 1.0)
		"holo_board": _holo_board(g, t, r)
		"holo_cube": _holo_cube(g, t, r)
		"light_pole": _light_pole(g, t, r)
		"dish": _dish(g, t, 1.0)
		"solar": _solar_row(g, t, 2)
		"mast": _mast(g, t, 3.0)
		"dome": _dome(g, t)
		"tube": _tube(g, t, 1.0)
		"console": _console(g, t)
		"robot_arm": _robot_arm(g, t)
		"potted": _potted(g, t)
		"rack_row": _rack_row(g, t, 3, r)
		"cables": _cables(g, t, th)
		"cooling_unit": _cooling_unit(g, t)
		"big_pipe": _big_pipe(g, t)
		"ice": _ice(g, t, r, 1.0)
		"fan": _fan(g, t)
		"valve": _valve(g, t)
		"energy_pillar": _energy_pillar(g, t, 1.0)
		"data_spire": _data_spire(g, t, r)
		"broken_robot": _broken_robot(g, t, r)
		_:
			_boulder(g, t, th, r)


# ------------------------------------------------------------------ nature
static func _pine(g: Node3D, t: Node3D, th: String) -> void:
	var dark := th == "darkwood"
	var a := _m(g, "pine_a_" + th, Color(0.05, 0.17, 0.1) if dark else Color(0.11, 0.34, 0.15))
	var b := _m(g, "pine_b_" + th, Color(0.08, 0.23, 0.12) if dark else Color(0.16, 0.42, 0.17))
	_cy(g, t, _m(g, "trunk", TRUNK), Vector3(0, 0.3, 0), 0.1, 0.15, 0.6, 6)
	_cy(g, t, a, Vector3(0, 1.05, 0), 0.0, 0.85, 1.3, 7)
	_cy(g, t, b, Vector3(0, 1.65, 0), 0.0, 0.62, 1.0, 7)
	_cy(g, t, a, Vector3(0, 2.15, 0), 0.0, 0.38, 0.7, 7)


static func _birch(g: Node3D, t: Node3D) -> void:
	_cy(g, t, _m(g, "birch_bark", Color(0.9, 0.88, 0.82)), Vector3(0, 0.8, 0), 0.06, 0.1, 1.6, 6)
	_bx(g, t, _m(g, "birch_band", Color(0.15, 0.14, 0.13)), Vector3(0, 0.55, 0), Vector3(0.17, 0.05, 0.17))
	_sp(g, t, _m(g, "birch_leaf", Color(0.46, 0.66, 0.26)), Vector3(0, 1.8, 0), 0.55, Vector3(1, 1.3, 1), 7)
	_sp(g, t, _m(g, "birch_leaf2", Color(0.56, 0.74, 0.3)), Vector3(0.28, 1.45, 0.12), 0.36, Vector3.ONE, 6)


static func _round_tree(g: Node3D, t: Node3D, a: Color, b: Color, key: String, h: float) -> void:
	_cy(g, t, _m(g, "trunk", TRUNK), Vector3(0, 0.45 * h, 0), 0.1, 0.15, 0.9 * h, 6)
	_sp(g, t, _m(g, key + "_a", a), Vector3(0, 0.9 * h + 0.45, 0), 0.72, Vector3(1, 0.9, 1), 8)
	_sp(g, t, _m(g, key + "_b", b), Vector3(0.35, 0.75 * h + 0.35, 0.25), 0.46, Vector3.ONE, 7)


static func _cypress(g: Node3D, t: Node3D) -> void:
	_cy(g, t, _m(g, "trunk", TRUNK), Vector3(0, 0.2, 0), 0.06, 0.08, 0.4, 5)
	_sp(g, t, _m(g, "cypress", Color(0.1, 0.27, 0.13)), Vector3(0, 1.3, 0), 0.32, Vector3(1, 3.3, 1), 7)


static func _olive(g: Node3D, t: Node3D) -> void:
	var bark := _m(g, "olive_bark", Color(0.42, 0.36, 0.28))
	_cy(g, t, bark, Vector3(0.06, 0.38, 0), 0.07, 0.13, 0.8, 5, Vector3(0, 0, 0.25))
	_cy(g, t, bark, Vector3(-0.14, 0.55, 0.05), 0.04, 0.07, 0.6, 5, Vector3(0.2, 0, -0.55))
	var la := _m(g, "olive_leaf", Color(0.46, 0.55, 0.34))
	var lb := _m(g, "olive_leaf2", Color(0.56, 0.62, 0.42))
	_sp(g, t, la, Vector3(0.2, 1.0, 0), 0.45, Vector3(1, 0.7, 1), 7)
	_sp(g, t, lb, Vector3(-0.32, 0.95, 0.15), 0.38, Vector3(1, 0.7, 1), 7)
	_sp(g, t, la, Vector3(0, 1.22, -0.2), 0.36, Vector3(1, 0.7, 1), 7)


static func _willow(g: Node3D, t: Node3D) -> void:
	_cy(g, t, _m(g, "willow_bark", Color(0.3, 0.24, 0.16)), Vector3(0, 0.55, 0), 0.12, 0.2, 1.1, 6)
	_cy(g, t, _m(g, "willow_skirt", Color(0.27, 0.38, 0.15)), Vector3(0, 0.95, 0), 0.62, 1.02, 1.25, 9)
	_sp(g, t, _m(g, "willow_top", Color(0.33, 0.45, 0.17)), Vector3(0, 1.6, 0), 0.75, Vector3(1, 0.5, 1), 9)


static func _dead_tree(g: Node3D, t: Node3D, th: String) -> void:
	var c := Color(0.12, 0.1, 0.09) if th == "forge" else (Color(0.16, 0.13, 0.11) if th == "smog" else Color(0.26, 0.2, 0.15))
	var m := _m(g, "deadwood_" + th, c)
	_cy(g, t, m, Vector3(0, 0.75, 0), 0.06, 0.14, 1.5, 5)
	for k in 3:
		var a := k * 2.1 + 0.3
		var tilt := 0.9
		var dir := Vector3(sin(a) * sin(tilt), cos(tilt), cos(a) * sin(tilt))
		_cy(g, t, m, Vector3(0, 0.85 + k * 0.22, 0) + dir * 0.3, 0.025, 0.05, 0.65, 4, Vector3(tilt, a, 0))


static func _bush(g: Node3D, t: Node3D, th: String) -> void:
	var cols: Array = {
		"olive": [Color(0.42, 0.46, 0.24), Color(0.5, 0.52, 0.28)], "coast": [Color(0.44, 0.5, 0.28), Color(0.52, 0.56, 0.32)],
		"bog": [Color(0.24, 0.34, 0.14), Color(0.3, 0.4, 0.16)], "harbor": [Color(0.24, 0.48, 0.18), Color(0.32, 0.56, 0.2)],
		"suburb": [Color(0.2, 0.5, 0.16), Color(0.28, 0.58, 0.2)],
	}.get(th, [Color(0.22, 0.48, 0.15), Color(0.3, 0.55, 0.18)])
	_sp(g, t, _m(g, "bush_a_" + th, cols[0]), Vector3(0, 0.3, 0), 0.55, Vector3(1.2, 0.75, 1.1), 7)
	_sp(g, t, _m(g, "bush_b_" + th, cols[1]), Vector3(0.4, 0.25, 0.2), 0.38, Vector3(1, 0.8, 1), 6)


static func _heather(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var a := _m(g, "heather_a", Color(0.58, 0.32, 0.58))
	var b := _m(g, "heather_b", Color(0.46, 0.26, 0.5))
	_sp(g, t, a, Vector3(0, 0.12, 0), r.randf_range(0.3, 0.42), Vector3(1.3, 0.55, 1.1), 6)
	_sp(g, t, b, Vector3(0.38, 0.1, 0.18), r.randf_range(0.22, 0.3), Vector3(1.2, 0.6, 1), 6)


static func _boulder(g: Node3D, t: Node3D, th: String, r: RandomNumberGenerator) -> void:
	var e: Array = ENV.get(th, ENV["highland"])
	var rock := _m(g, "rock_" + th, e[5])
	var sz := r.randf_range(0.4, 0.75)
	_sp(g, t, rock, Vector3(0, sz * 0.25, 0), sz, Vector3(1.25, 0.7, 1), 6, Vector3(0, r.randf() * 3, 0))
	if r.randf() < 0.5:
		_sp(g, t, rock, Vector3(sz * 0.9, 0.08, sz * 0.3), sz * 0.45, Vector3(1.2, 0.7, 1), 5)
	if th in ["bog", "darkwood", "jungle"]:
		_sp(g, t, _m(g, "moss", Color(0.24, 0.4, 0.14)), Vector3(0, sz * 0.62, 0), sz * 0.7, Vector3(1.2, 0.3, 1), 6)


static func _standing_stone(g: Node3D, t: Node3D, r: RandomNumberGenerator, h: float) -> void:
	_bx(g, t, _m(g, "menhir", Color(0.56, 0.57, 0.55)), Vector3(0, h * 0.5 - 0.05, 0), Vector3(0.42, h, 0.28),
		Vector3(r.randf_range(-0.08, 0.08), 0, r.randf_range(-0.08, 0.08)))


static func _reeds(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var m := _m(g, "reed", Color(0.44, 0.54, 0.22))
	for k in 3:
		var a := TAU * k / 3.0 + r.randf() * 0.5
		_cy(g, t, m, Vector3(cos(a) * 0.14, 0.38, sin(a) * 0.14), 0.0, 0.05, r.randf_range(0.7, 1.0), 4,
			Vector3(r.randf_range(-0.25, 0.25), 0, r.randf_range(-0.25, 0.25)))
	_cy(g, t, m, Vector3(0, 0.4, 0), 0.015, 0.02, 0.8, 4)
	_cy(g, t, _m(g, "cattail", Color(0.4, 0.24, 0.12)), Vector3(0, 0.86, 0), 0.05, 0.05, 0.2, 5)


static func _log(g: Node3D, t: Node3D, th: String) -> void:
	_cy(g, t, _m(g, "log", Color(0.36, 0.27, 0.17)), Vector3(0, 0.16, 0), 0.16, 0.16, 1.4, 7, Vector3(0, 0, PI * 0.5))
	if th != "forge":
		_bx(g, t, _m(g, "moss", Color(0.24, 0.4, 0.14)), Vector3(0.1, 0.3, 0), Vector3(0.8, 0.05, 0.18))


static func _boardwalk(g: Node3D, t: Node3D) -> void:
	var w := _m(g, "plank", Color(0.5, 0.36, 0.22))
	_bx(g, t, w, Vector3(0, 0.24, 0), Vector3(0.65, 0.06, 1.7))
	_cy(g, t, _m(g, "post", WOOD_D), Vector3(0.28, 0.14, 0.7), 0.05, 0.05, 0.36, 5)
	_cy(g, t, _m(g, "post", WOOD_D), Vector3(-0.28, 0.14, -0.7), 0.05, 0.05, 0.36, 5)


static func _mist(g: Node3D, t: Node3D, k: float) -> void:
	_no_shadow(_sp(g, t, _m(g, "mist", Color(0.9, 0.94, 0.92, 0.13), {"rough": 1.0}), Vector3(0, 0.08, 0), k, Vector3(1.4, 0.16, 1.0), 10))


static func _mushrooms(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var stem := _m(g, "shroom_stem", Color(0.88, 0.84, 0.74))
	var caps := [_m(g, "shroom_red", Color(0.82, 0.16, 0.12)), _glow(g, "shroom_glow", Color(0.3, 0.85, 0.8), 1.3)]
	for k in 2:
		var h := r.randf_range(0.18, 0.34)
		var off := Vector3(k * 0.3 - 0.15, 0, r.randf_range(-0.15, 0.15))
		_cy(g, t, stem, off + Vector3(0, h * 0.5, 0), 0.04, 0.05, h, 5)
		_sp(g, t, caps[(k + r.randi()) % 2], off + Vector3(0, h, 0), 0.15, Vector3(1, 0.55, 1), 7)


static func _fern(g: Node3D, t: Node3D) -> void:
	var m := _m(g, "fern", Color(0.2, 0.55, 0.2))
	for k in 4:
		var a := TAU * k / 4.0 + 0.4
		_bx(g, t, m, Vector3(sin(a) * 0.3, 0.2, cos(a) * 0.3), Vector3(0.16, 0.03, 0.7), Vector3(-0.5, a, 0))


static func _jungle_tree(g: Node3D, t: Node3D) -> void:
	_cy(g, t, _m(g, "jtrunk", Color(0.42, 0.32, 0.2)), Vector3(0, 1.1, 0), 0.1, 0.17, 2.2, 6)
	_sp(g, t, _m(g, "jcanopy", Color(0.08, 0.38, 0.13)), Vector3(0, 2.3, 0), 0.7, Vector3(1.3, 0.6, 1.3), 8)
	var leaf := _m(g, "jleaf", Color(0.16, 0.54, 0.18))
	for k in 4:
		var a := TAU * k / 4.0 + 0.7
		_bx(g, t, leaf, Vector3(sin(a) * 0.75, 2.05, cos(a) * 0.75), Vector3(0.5, 0.04, 1.2), Vector3(0.35, a, 0))


static func _flowers(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	_sp(g, t, _m(g, "jbush", Color(0.12, 0.42, 0.14)), Vector3(0, 0.28, 0), 0.5, Vector3(1.2, 0.7, 1.1), 7)
	var cols := [Color(1.0, 0.2, 0.3), Color(1.0, 0.8, 0.1), Color(0.95, 0.3, 0.9), Color(1.0, 0.5, 0.1)]
	for k in 3:
		var a := TAU * k / 3.0 + r.randf()
		var c: Color = cols[(k + r.randi()) % 4]
		_sp(g, t, _m(g, "flower_" + c.to_html(), c, {"emit": c, "emit_e": 0.25}), Vector3(cos(a) * 0.35, 0.52, sin(a) * 0.3), 0.12, Vector3.ONE, 6)


# ------------------------------------------------------------------ iron age
static func _roundhouse(g: Node3D, t: Node3D, forge: bool) -> void:
	var wall := _m(g, "wattle_forge" if forge else "wattle", Color(0.3, 0.26, 0.24) if forge else Color(0.62, 0.5, 0.34))
	var thatch := _m(g, "thatch_dark" if forge else "thatch", Color(0.36, 0.27, 0.16) if forge else Color(0.78, 0.64, 0.32))
	_cy(g, t, wall, Vector3(0, 0.36, 0), 0.9, 0.92, 0.72, 10)
	_cy(g, t, thatch, Vector3(0, 1.22, 0), 0.0, 1.15, 1.05, 10)
	if forge:
		_bx(g, t, _glow(g, "furnace_glow", Color(1.0, 0.45, 0.1), 2.6), Vector3(0, 0.3, 0.9), Vector3(0.5, 0.4, 0.06))
		_bx(g, t, _m(g, "stone_dark", Color(0.28, 0.26, 0.25)), Vector3(0.55, 1.2, -0.35), Vector3(0.32, 1.6, 0.32))
		_smoke(g, t, Vector3(0.55, 2.05, -0.35), 0.8, Color(0.22, 0.2, 0.2, 0.6))
	else:
		_bx(g, t, _m(g, "door_dark", Color(0.12, 0.08, 0.05)), Vector3(0, 0.27, 0.88), Vector3(0.4, 0.54, 0.08))


static func _anvil(g: Node3D, t: Node3D) -> void:
	var iron := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
	_cy(g, t, _m(g, "log", Color(0.36, 0.27, 0.17)), Vector3(0, 0.18, 0), 0.2, 0.23, 0.36, 7)
	_bx(g, t, iron, Vector3(0, 0.44, 0), Vector3(0.45, 0.16, 0.22))
	_cy(g, t, iron, Vector3(0.33, 0.46, 0), 0.0, 0.08, 0.26, 5, Vector3(0, 0, -PI * 0.5))
	_bx(g, t, _glow(g, "hot_iron", Color(1.0, 0.5, 0.12), 2.2), Vector3(-0.05, 0.54, 0), Vector3(0.3, 0.04, 0.06))


static func _ore_cart(g: Node3D, t: Node3D) -> void:
	_bx(g, t, _m(g, "cart_wood", WOOD), Vector3(0, 0.42, 0), Vector3(0.75, 0.4, 0.52))
	var iron := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
	for s in [-1, 1]:
		_cy(g, t, iron, Vector3(s * 0.24, 0.15, 0), 0.15, 0.15, 0.62, 8, Vector3(PI * 0.5, 0, 0))
	_sp(g, t, _m(g, "ore", Color(0.55, 0.3, 0.2)), Vector3(0, 0.64, 0), 0.32, Vector3(1, 0.5, 0.75), 6)


static func _slag_heap(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var slag := _m(g, "slag", Color(0.12, 0.1, 0.1), {"rough": 0.4, "metal": 0.2})
	var h := r.randf_range(0.5, 0.9)
	_cy(g, t, slag, Vector3(0, h * 0.5, 0), 0.12, 0.9, h, 7)
	_bx(g, t, _glow(g, "ember", Color(1.0, 0.4, 0.1), 2.0), Vector3(0, h * 0.4, 0.5), Vector3(0.5, 0.05, 0.06), Vector3(0, 0.2, 0.3))


# ------------------------------------------------------------------ classical
static func _column(g: Node3D, t: Node3D, h: float) -> void:
	var m := _m(g, "marble", MARBLE)
	_bx(g, t, m, Vector3(0, 0.08, 0), Vector3(0.62, 0.16, 0.62))
	_cy(g, t, m, Vector3(0, 0.16 + h * 0.5, 0), 0.22, 0.25, h, 9)
	if h > 1.4:
		_bx(g, t, m, Vector3(0, 0.24 + h, 0), Vector3(0.56, 0.16, 0.56))
	else:
		_cy(g, t, m, Vector3(0.55, 0.22, 0.2), 0.22, 0.22, 0.5, 9, Vector3(0, 0.4, PI * 0.5))


static func _amphorae(g: Node3D, t: Node3D) -> void:
	var m := _m(g, "terracotta", TERRACOTTA)
	_sp(g, t, m, Vector3(0, 0.3, 0), 0.2, Vector3(1, 1.4, 1), 7)
	_cy(g, t, m, Vector3(0, 0.62, 0), 0.07, 0.09, 0.16, 6)
	_sp(g, t, m, Vector3(0.38, 0.17, 0.12), 0.17, Vector3(1.4, 1, 1), 7, Vector3(0, 0.5, 0))
	_bx(g, t, _m(g, "pot_band", Color(0.15, 0.1, 0.08)), Vector3(0, 0.36, 0), Vector3(0.36, 0.05, 0.36))


static func _low_wall(g: Node3D, t: Node3D) -> void:
	var m := _m(g, "drystone", Color(0.72, 0.68, 0.58))
	_bx(g, t, m, Vector3(0, 0.22, 0), Vector3(1.7, 0.44, 0.36))
	_bx(g, t, m, Vector3(0.95, 0.12, 0.15), Vector3(0.4, 0.24, 0.3), Vector3(0, 0.5, 0))


static func _shrine(g: Node3D, t: Node3D) -> void:
	var m := _m(g, "marble", MARBLE)
	_bx(g, t, m, Vector3(0, 0.1, 0), Vector3(1.0, 0.2, 0.85))
	_bx(g, t, m, Vector3(0, 0.6, -0.3), Vector3(0.9, 0.8, 0.12))
	for s in [-1, 1]:
		_cy(g, t, m, Vector3(s * 0.36, 0.6, 0.25), 0.07, 0.08, 0.8, 7)
	_pr(g, t, _m(g, "roof_tile", TERRACOTTA), Vector3(0, 1.17, 0), Vector3(1.1, 0.34, 0.95))
	_sp(g, t, _m(g, "gold", Color(0.95, 0.72, 0.2), {"metal": 0.6, "rough": 0.3}), Vector3(0, 0.38, -0.12), 0.12, Vector3(1, 1.3, 1), 6)


static func _boat(g: Node3D, t: Node3D) -> void:
	_pr(g, t, _m(g, "hull_red", Color(0.55, 0.24, 0.14)), Vector3(0, 0.16, 0), Vector3(0.62, 0.32, 1.5), Vector3(0, 0, PI))
	_bx(g, t, _m(g, "hull_inner", Color(0.72, 0.56, 0.36)), Vector3(0, 0.31, 0), Vector3(0.46, 0.02, 1.3))
	_bx(g, t, _m(g, "post", WOOD_D), Vector3(0, 0.34, 0.1), Vector3(0.5, 0.05, 0.14))


static func _statue(g: Node3D, t: Node3D) -> void:
	var m := _m(g, "marble", MARBLE)
	_bx(g, t, _m(g, "plinth", Color(0.8, 0.77, 0.7)), Vector3(0, 0.25, 0), Vector3(0.62, 0.5, 0.62))
	_cy(g, t, m, Vector3(0, 0.92, 0), 0.13, 0.21, 0.85, 7)
	_sp(g, t, m, Vector3(0, 1.45, 0), 0.13, Vector3.ONE, 7)
	_bx(g, t, m, Vector3(0.2, 1.3, 0), Vector3(0.08, 0.5, 0.08), Vector3(0, 0, -0.45))


static func _brazier(g: Node3D, t: Node3D, light_e: float) -> void:
	var bronze := _m(g, "bronze", Color(0.66, 0.42, 0.16), {"metal": 0.6, "rough": 0.4})
	_cy(g, t, bronze, Vector3(0, 0.32, 0), 0.04, 0.12, 0.64, 6)
	_cy(g, t, bronze, Vector3(0, 0.7, 0), 0.3, 0.12, 0.18, 8)
	_flame(g, t, Vector3(0, 0.6, 0), 0.55, light_e)


static func _temple_front(g: Node3D, t: Node3D, k: float) -> void:
	var m := _m(g, "marble", MARBLE)
	_bx(g, t, m, Vector3(0, 0.12, 0) * k, Vector3(3.0, 0.24, 1.8) * k)
	for i in 4:
		_cy(g, t, m, Vector3(-1.1 + i * 0.73, 1.14, 0.55) * k, 0.15 * k, 0.18 * k, 1.8 * k, 8)
	_bx(g, t, m, Vector3(0, 2.18, 0.15) * k, Vector3(2.9, 0.3, 1.2) * k)
	_pr(g, t, _m(g, "roof_tile", TERRACOTTA), Vector3(0, 2.6, 0.15) * k, Vector3(3.0, 0.55, 1.25) * k)


# ------------------------------------------------------------------ medieval
static func _haystack(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var hay := _m(g, "hay", Color(0.88, 0.74, 0.36))
	if r.randf() < 0.5:
		_cy(g, t, hay, Vector3(0, 0.3, 0), 0.5, 0.56, 0.6, 9)
		_cy(g, t, _m(g, "hay2", Color(0.8, 0.66, 0.3)), Vector3(0, 0.82, 0), 0.06, 0.55, 0.45, 9)
	else:   # round bales
		_cy(g, t, hay, Vector3(0, 0.36, 0), 0.36, 0.36, 0.55, 10, Vector3(PI * 0.5, 0, 0))
		_cy(g, t, hay, Vector3(0.75, 0.36, 0.1), 0.36, 0.36, 0.55, 10, Vector3(PI * 0.5, 0.3, 0))


static func _fence(g: Node3D, t: Node3D) -> void:
	var w := _m(g, "fence_wood", Color(0.56, 0.42, 0.26))
	for s in [-1, 1]:
		_bx(g, t, w, Vector3(s * 0.75, 0.3, 0), Vector3(0.1, 0.6, 0.1))
	_bx(g, t, w, Vector3(0, 0.24, 0), Vector3(1.6, 0.08, 0.05))
	_bx(g, t, w, Vector3(0, 0.48, 0), Vector3(1.6, 0.08, 0.05))


static func _cottage(g: Node3D, t: Node3D) -> void:
	_bx(g, t, _m(g, "plaster", Color(0.93, 0.87, 0.72)), Vector3(0, 0.43, 0), Vector3(1.1, 0.86, 1.4))
	_bx(g, t, _m(g, "beam", WOOD_D), Vector3(0, 0.84, 0), Vector3(1.14, 0.08, 1.44))
	_pr(g, t, _m(g, "thatch", Color(0.78, 0.64, 0.32)), Vector3(0, 1.23, 0), Vector3(1.45, 0.78, 1.62))
	_bx(g, t, _m(g, "door_dark", Color(0.12, 0.08, 0.05)), Vector3(0.56, 0.27, 0.2), Vector3(0.05, 0.54, 0.34))
	_bx(g, t, _m(g, "stone_grey", Color(0.5, 0.49, 0.47)), Vector3(-0.25, 1.45, -0.4), Vector3(0.24, 0.6, 0.24))


static func _stone_wall(g: Node3D, t: Node3D) -> void:
	var m := _m(g, "castle_stone", Color(0.58, 0.57, 0.55))
	_bx(g, t, m, Vector3(0, 0.45, 0), Vector3(1.9, 0.9, 0.45))
	for i in 3:
		_bx(g, t, m, Vector3(-0.7 + i * 0.7, 1.02, 0), Vector3(0.36, 0.26, 0.45))


static func _banner(g: Node3D, t: Node3D, c: Color) -> void:
	_cy(g, t, _m(g, "post", WOOD_D), Vector3(0, 1.1, 0), 0.04, 0.05, 2.2, 5)
	_bx(g, t, _m(g, "banner_" + c.to_html(), c), Vector3(0.22, 1.55, 0), Vector3(0.42, 0.85, 0.03))
	_bx(g, t, _m(g, "gold", Color(0.95, 0.72, 0.2), {"metal": 0.6, "rough": 0.3}), Vector3(0.22, 1.95, 0), Vector3(0.5, 0.05, 0.05))


static func _siege_debris(g: Node3D, t: Node3D) -> void:
	var w := _m(g, "cart_wood", WOOD)
	_bx(g, t, w, Vector3(0, 0.15, 0.4), Vector3(1.4, 0.16, 0.16))
	_bx(g, t, w, Vector3(0, 0.15, -0.4), Vector3(1.4, 0.16, 0.16), Vector3(0, 0.15, 0))
	_bx(g, t, w, Vector3(0, 0.15, 0), Vector3(0.16, 0.16, 0.95))
	_bx(g, t, w, Vector3(0.2, 0.33, 0.05), Vector3(1.5, 0.14, 0.14), Vector3(0, 0.5, 0.12))
	_cy(g, t, _m(g, "post", WOOD_D), Vector3(-0.85, 0.06, 0.6), 0.32, 0.32, 0.08, 8, Vector3(0.12, 0, 0.1))


static func _tent_med(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var c := Color(0.75, 0.15, 0.12) if r.randf() < 0.5 else Color(0.18, 0.28, 0.62)
	_cy(g, t, _m(g, "tent_white", Color(0.92, 0.9, 0.84)), Vector3(0, 0.35, 0), 0.75, 0.8, 0.7, 8)
	_cy(g, t, _m(g, "tent_" + c.to_html(), c), Vector3(0, 1.05, 0), 0.0, 0.85, 0.7, 8)
	_cy(g, t, _m(g, "post", WOOD_D), Vector3(0, 1.55, 0), 0.02, 0.02, 0.4, 4)
	_bx(g, t, _m(g, "banner_" + c.to_html(), c), Vector3(0.14, 1.66, 0), Vector3(0.26, 0.14, 0.02))


static func _drums(g: Node3D, t: Node3D, i: int) -> void:
	_barrels(g, t, [OLIVE_DRAB, Color(0.2, 0.32, 0.55), Color(0.6, 0.16, 0.12)][i], "drum%d" % i)


static func _rng(sd: int) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = sd
	return r


static func _barrels(g: Node3D, t: Node3D, c: Color, key: String) -> void:
	var m := _m(g, "barrel_" + key, c, {"rough": 0.7})
	_cy(g, t, m, Vector3(0, 0.27, 0), 0.22, 0.22, 0.54, 8)
	_cy(g, t, m, Vector3(0.46, 0.27, 0.12), 0.22, 0.22, 0.54, 8)
	_cy(g, t, m, Vector3(0.1, 0.22, 0.5), 0.22, 0.22, 0.54, 8, Vector3(0, 0.6, PI * 0.5))


static func _ruin_arch(g: Node3D, t: Node3D, dark: bool) -> void:
	var m := _m(g, "ruin_dark" if dark else "ruin_jungle", Color(0.36, 0.38, 0.36) if dark else Color(0.5, 0.52, 0.44))
	_bx(g, t, m, Vector3(-0.55, 0.65, 0), Vector3(0.32, 1.3, 0.32))
	_bx(g, t, m, Vector3(0.55, 0.42, 0), Vector3(0.32, 0.84, 0.32))
	_bx(g, t, m, Vector3(-0.15, 1.4, 0), Vector3(1.0, 0.24, 0.34), Vector3(0, 0, -0.12))
	_bx(g, t, m, Vector3(0.45, 0.14, 0.5), Vector3(0.5, 0.28, 0.32), Vector3(0, 0.6, 0))
	_bx(g, t, _m(g, "vine", Color(0.18, 0.46, 0.16)), Vector3(-0.55, 0.9, 0.17), Vector3(0.28, 0.9, 0.03))


# ------------------------------------------------------------------ gunpowder
static func _crates(g: Node3D, t: Node3D, th: String, r: RandomNumberGenerator) -> void:
	var c: Color = {"military": Color(0.38, 0.42, 0.24), "lab": Color(0.85, 0.87, 0.9), "satellite": Color(0.75, 0.72, 0.66),
		"server": Color(0.3, 0.32, 0.36)}.get(th, Color(0.62, 0.46, 0.26))
	var m := _m(g, "crate_" + th, c)
	_bx(g, t, m, Vector3(0, 0.26, 0), Vector3(0.52, 0.52, 0.52))
	_bx(g, t, m, Vector3(0.56, 0.22, 0.1), Vector3(0.44, 0.44, 0.44), Vector3(0, 0.4, 0))
	if r.randf() < 0.6:
		_bx(g, t, m, Vector3(0.05, 0.72, 0.02), Vector3(0.4, 0.4, 0.4), Vector3(0, 0.3, 0))
	if th == "lab":
		_bx(g, t, _glow(g, "cyan_strip", CYAN, 1.8), Vector3(0, 0.3, 0.265), Vector3(0.44, 0.05, 0.02))


static func _anchor(g: Node3D, t: Node3D) -> void:
	var iron := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
	_cy(g, t, iron, Vector3(0, 0.07, 0), 0.05, 0.05, 1.0, 6, Vector3(PI * 0.5, 0, 0))
	_bx(g, t, iron, Vector3(0, 0.07, -0.35), Vector3(0.6, 0.08, 0.08))
	_tor(g, t, iron, Vector3(0, 0.06, 0.45), 0.2, 0.28, Vector3.ZERO, 10)
	_tor(g, t, _m(g, "rope", Color(0.75, 0.64, 0.42)), Vector3(0.55, 0.06, -0.3), 0.12, 0.24, Vector3.ZERO, 10)


static func _cannon(g: Node3D, t: Node3D) -> void:
	var w := _m(g, "cart_wood", WOOD)
	var iron := _m(g, "cannon_iron", Color(0.12, 0.12, 0.13), {"metal": 0.6, "rough": 0.35})
	_bx(g, t, w, Vector3(0, 0.24, 0), Vector3(0.48, 0.24, 0.75))
	_cy(g, t, iron, Vector3(0, 0.46, 0.15), 0.09, 0.14, 1.05, 8, Vector3(PI * 0.5 - 0.12, 0, 0))
	for s in [-1, 1]:
		_cy(g, t, _m(g, "wheel", WOOD_D), Vector3(s * 0.3, 0.24, 0.12), 0.24, 0.24, 0.08, 10, Vector3(0, 0, PI * 0.5))


static func _gabions(g: Node3D, t: Node3D) -> void:
	var m := _m(g, "wicker", Color(0.58, 0.45, 0.27))
	var dirt := _m(g, "earth", Color(0.45, 0.36, 0.22))
	for i in 3:
		_cy(g, t, m, Vector3(-0.6 + i * 0.6, 0.32, 0), 0.28, 0.28, 0.64, 8)
	_bx(g, t, dirt, Vector3(0, 0.66, 0), Vector3(1.6, 0.06, 0.45))


static func _earthwork(g: Node3D, t: Node3D) -> void:
	_sp(g, t, _m(g, "berm", Color(0.4, 0.4, 0.22)), Vector3(0, 0.0, 0), 1.0, Vector3(1.6, 0.42, 0.7), 9)
	for i in 4:
		_cy(g, t, _m(g, "post", WOOD_D), Vector3(-0.9 + i * 0.6, 0.5, -0.35), 0.0, 0.06, 0.5, 4, Vector3(-0.5, 0, 0))


static func _tent(g: Node3D, t: Node3D, c: Color, key: String) -> void:
	_pr(g, t, _m(g, "tent_" + key, c), Vector3(0, 0.45, 0), Vector3(1.1, 0.9, 1.5))
	_bx(g, t, _m(g, "door_dark", Color(0.12, 0.08, 0.05)), Vector3(0, 0.25, 0.75), Vector3(0.36, 0.48, 0.02))


static func _flag(g: Node3D, t: Node3D, c: Color) -> void:
	_cy(g, t, _m(g, "pole", Color(0.85, 0.85, 0.82)), Vector3(0, 1.2, 0), 0.03, 0.05, 2.4, 5)
	_bx(g, t, _m(g, "flag_" + c.to_html(), c), Vector3(0.36, 2.1, 0), Vector3(0.7, 0.42, 0.03))
	_bx(g, t, _m(g, "flag_white", Color(0.95, 0.95, 0.92)), Vector3(0.36, 2.1, 0), Vector3(0.72, 0.1, 0.035))


# ------------------------------------------------------------------ industrial
static func _rail_car(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var steel := _m(g, "rail", Color(0.5, 0.5, 0.52), {"metal": 0.6, "rough": 0.4})
	for s in [-1, 1]:
		_bx(g, t, steel, Vector3(s * 0.36, 0.04, 0), Vector3(0.07, 0.08, 3.0))
	_bx(g, t, _m(g, "bogie", Color(0.12, 0.12, 0.13)), Vector3(0, 0.24, 0), Vector3(0.8, 0.3, 2.0))
	if r.randf() < 0.55:
		var c: Color = [Color(0.55, 0.2, 0.12), Color(0.24, 0.3, 0.42), Color(0.32, 0.4, 0.22)][r.randi() % 3]
		_bx(g, t, _m(g, "boxcar_" + c.to_html(), c), Vector3(0, 0.82, 0), Vector3(0.96, 0.9, 2.2))
		_bx(g, t, _m(g, "boxcar_roof", Color(0.3, 0.28, 0.27)), Vector3(0, 1.3, 0), Vector3(1.02, 0.08, 2.26))
	else:
		_bx(g, t, _m(g, "hopper", Color(0.22, 0.22, 0.24), {"metal": 0.4}), Vector3(0, 0.66, 0), Vector3(0.96, 0.6, 2.1))
		_sp(g, t, _m(g, "coal", Color(0.07, 0.07, 0.08), {"rough": 0.5}), Vector3(0, 0.96, 0), 0.5, Vector3(0.9, 0.35, 2.0), 6)


static func _coal(g: Node3D, t: Node3D, k: float) -> void:
	var m := _m(g, "coal", Color(0.11, 0.11, 0.12), {"rough": 0.45})
	_cy(g, t, m, Vector3(0, 0.25 * k, 0), 0.12 * k, 0.75 * k, 0.5 * k, 7)
	_sp(g, t, m, Vector3(0.7, 0.1, 0.3) * k, 0.3 * k, Vector3(1.2, 0.6, 1), 5)


static func _signal(g: Node3D, t: Node3D) -> void:
	var dark := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
	_cy(g, t, dark, Vector3(0, 0.9, 0), 0.04, 0.06, 1.8, 6)
	_bx(g, t, dark, Vector3(0, 1.78, 0), Vector3(0.24, 0.5, 0.18))
	_pulse(g, _sp(g, t, _glow(g, "sig_red", Color(1.0, 0.15, 0.1), 2.5), Vector3(0, 1.88, 0.1), 0.07, Vector3.ONE, 6))
	_sp(g, t, _glow(g, "sig_green", Color(0.2, 1.0, 0.35), 1.5), Vector3(0, 1.68, 0.1), 0.07, Vector3.ONE, 6)


static func _water_tower(g: Node3D, t: Node3D) -> void:
	var w := _m(g, "tower_wood", Color(0.46, 0.32, 0.2))
	var iron := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
	for k in 4:
		var a := TAU * k / 4.0 + PI * 0.25
		_bx(g, t, iron, Vector3(cos(a) * 0.45, 0.8, sin(a) * 0.45), Vector3(0.1, 1.6, 0.1))
	_cy(g, t, w, Vector3(0, 2.05, 0), 0.65, 0.65, 0.9, 10)
	_cy(g, t, _m(g, "slate", Color(0.28, 0.28, 0.32)), Vector3(0, 2.7, 0), 0.0, 0.74, 0.42, 10)


static func _factory_bldg(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	_bx(g, t, _m(g, "brick", BRICK), Vector3(0, 0.7, 0), Vector3(2.2, 1.4, 1.5))
	var slate := _m(g, "slate", Color(0.28, 0.28, 0.32))
	for i in 2:
		_pr(g, t, slate, Vector3(-0.55 + i * 1.1, 1.62, 0), Vector3(1.1, 0.45, 1.5), Vector3.ZERO, 0.0)
	_bx(g, t, _glow(g, "furnace_win", Color(1.0, 0.6, 0.2), 1.8), Vector3(0, 0.85, 0.76), Vector3(1.8, 0.22, 0.02))
	_cy(g, t, _m(g, "brick_dark", BRICK.darkened(0.3)), Vector3(0.75, 1.9, -0.45), 0.16, 0.22, 2.6, 8)
	if r.randf() < 0.7:
		_smoke(g, t, Vector3(0.75, 3.2, -0.45), 0.8, Color(0.4, 0.38, 0.37, 0.55))


static func _pipes(g: Node3D, t: Node3D, th: String) -> void:
	var c := Color(0.72, 0.42, 0.22) if th != "smog" else Color(0.3, 0.3, 0.32)
	var m := _m(g, "pipe_" + th, c, {"metal": 0.6, "rough": 0.35})
	_cy(g, t, m, Vector3(0, 0.62, 0), 0.12, 0.12, 2.2, 8, Vector3(0, 0, PI * 0.5))
	_cy(g, t, m, Vector3(1.1, 0.4, 0), 0.12, 0.12, 0.6, 8)
	var iron := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
	for s in [-1, 1]:
		_bx(g, t, iron, Vector3(s * 0.55, 0.28, 0), Vector3(0.1, 0.56, 0.2))


static func _gear(g: Node3D, t: Node3D) -> void:
	var holder := _n(t, Vector3(0, 0.55, 0), 0.0)
	holder.rotation.x = PI * 0.5 - 0.3
	var iron := _m(g, "gear_iron", Color(0.3, 0.28, 0.27), {"metal": 0.6, "rough": 0.4})
	_cy(g, t, _m(g, "crate_factory", Color(0.62, 0.46, 0.26)), Vector3(0, 0.1, 0.3), 0.3, 0.3, 0.2, 6)
	_cy(g, holder, iron, Vector3.ZERO, 0.5, 0.5, 0.12, 12)
	for i in 3:
		_bx(g, holder, iron, Vector3.ZERO, Vector3(1.2, 0.1, 0.14), Vector3(0, i * PI / 3.0, 0))
	_cy(g, holder, _m(g, "brass", Color(0.8, 0.62, 0.25), {"metal": 0.7, "rough": 0.3}), Vector3.ZERO, 0.14, 0.14, 0.2, 8)


static func _lamp(g: Node3D, t: Node3D, c: Color) -> void:
	var iron := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
	_cy(g, t, iron, Vector3(0, 0.85, 0), 0.04, 0.07, 1.7, 6)
	_bx(g, t, _glow(g, "lamp_" + c.to_html(), c, 2.4), Vector3(0, 1.8, 0), Vector3(0.18, 0.26, 0.18))
	_cy(g, t, iron, Vector3(0, 1.98, 0), 0.0, 0.17, 0.14, 6)


static func _terrace(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var c: Color = [Color(0.48, 0.28, 0.22), Color(0.42, 0.3, 0.26), Color(0.52, 0.34, 0.24)][r.randi() % 3]
	_bx(g, t, _m(g, "terrace_" + c.to_html(), c), Vector3(0, 0.66, 0), Vector3(3.0, 1.32, 1.0))
	_pr(g, t, _m(g, "slate", Color(0.28, 0.28, 0.32)), Vector3(0, 1.6, 0), Vector3(1.1, 0.56, 3.05), Vector3(0, PI * 0.5, 0))
	var brick := _m(g, "brick_dark", BRICK.darkened(0.3))
	for i in 3:
		_bx(g, t, brick, Vector3(-1.0 + i * 1.0, 1.85, 0), Vector3(0.22, 0.5, 0.26))
	_bx(g, t, _glow(g, "window_warm", Color(1.0, 0.75, 0.35), 1.6), Vector3(0, 0.88, 0.51), Vector3(2.7, 0.16, 0.02))


# ------------------------------------------------------------------ modern
static func _house(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var walls := [Color(0.95, 0.92, 0.82), Color(0.74, 0.84, 0.95), Color(0.96, 0.84, 0.68), Color(0.82, 0.93, 0.8), Color(0.98, 0.98, 0.96)]
	var roofs := [Color(0.56, 0.24, 0.18), Color(0.3, 0.32, 0.38), Color(0.4, 0.3, 0.24)]
	var wc: Color = walls[r.randi() % walls.size()]
	var rc: Color = roofs[r.randi() % roofs.size()]
	_bx(g, t, _m(g, "house_" + wc.to_html(), wc), Vector3(0, 0.5, 0), Vector3(1.6, 1.0, 1.3))
	_pr(g, t, _m(g, "roof_" + rc.to_html(), rc), Vector3(0, 1.32, 0), Vector3(1.8, 0.66, 1.46), Vector3(0, PI * 0.5, 0))
	_bx(g, t, _m(g, "door_white", Color(0.98, 0.98, 0.98)), Vector3(0.35, 0.3, 0.66), Vector3(0.3, 0.6, 0.04))
	_bx(g, t, _m(g, "window_blue", Color(0.55, 0.75, 0.9), {"rough": 0.2}), Vector3(-0.35, 0.58, 0.66), Vector3(0.4, 0.32, 0.04))


static func _car(g: Node3D, t: Node3D, r: RandomNumberGenerator, th: String) -> void:
	var cols := [Color(0.8, 0.15, 0.12), Color(0.15, 0.35, 0.75), Color(0.92, 0.92, 0.9), Color(0.2, 0.2, 0.22), Color(0.3, 0.6, 0.35)]
	if th == "metro":
		cols.append(Color(1.0, 0.8, 0.1))
		cols.append(Color(1.0, 0.8, 0.1))
	var c: Color = cols[r.randi() % cols.size()]
	_bx(g, t, _m(g, "car_" + c.to_html(), c, {"rough": 0.35, "metal": 0.2}), Vector3(0, 0.32, 0), Vector3(0.72, 0.3, 1.45))
	_bx(g, t, _m(g, "car_glass", Color(0.2, 0.26, 0.32), {"rough": 0.15}), Vector3(0, 0.6, -0.05), Vector3(0.62, 0.26, 0.76))
	var tire := _m(g, "tire", Color(0.07, 0.07, 0.08))
	for s in [-1, 1]:
		_cy(g, t, tire, Vector3(0, 0.16, s * 0.45), 0.16, 0.16, 0.76, 8, Vector3(0, 0, PI * 0.5))


static func _mailbox(g: Node3D, t: Node3D) -> void:
	_bx(g, t, _m(g, "post_white", Color(0.95, 0.95, 0.93)), Vector3(0, 0.3, 0), Vector3(0.06, 0.6, 0.06))
	_bx(g, t, _m(g, "mailbox", Color(0.2, 0.3, 0.55)), Vector3(0, 0.66, 0), Vector3(0.16, 0.16, 0.32))


static func _hoop(g: Node3D, t: Node3D) -> void:
	_cy(g, t, _m(g, "steel_grey", Color(0.5, 0.52, 0.55), {"metal": 0.5}), Vector3(0, 0.9, 0), 0.04, 0.05, 1.8, 6)
	_bx(g, t, _m(g, "post_white", Color(0.95, 0.95, 0.93)), Vector3(0, 1.8, 0.05), Vector3(0.6, 0.4, 0.04))
	_tor(g, t, _m(g, "hoop_orange", Color(1.0, 0.45, 0.1)), Vector3(0, 1.66, 0.2), 0.11, 0.14, Vector3.ZERO, 10)


static func _hangar(g: Node3D, t: Node3D) -> void:
	_cy(g, t, _m(g, "hangar", Color(0.56, 0.58, 0.54), {"metal": 0.4, "rough": 0.5}), Vector3.ZERO, 1.35, 1.35, 2.6, 10, Vector3(PI * 0.5, 0, 0))
	_bx(g, t, _m(g, "hangar_door", Color(0.2, 0.21, 0.22)), Vector3(0, 0.5, 1.3), Vector3(1.6, 1.0, 0.04))


static func _jeep(g: Node3D, t: Node3D) -> void:
	var od := _m(g, "olive_drab", OLIVE_DRAB)
	_bx(g, t, od, Vector3(0, 0.36, 0), Vector3(0.68, 0.3, 1.15))
	_bx(g, t, _m(g, "car_glass", Color(0.2, 0.26, 0.32), {"rough": 0.15}), Vector3(0, 0.64, 0.12), Vector3(0.62, 0.26, 0.04), Vector3(-0.3, 0, 0))
	var tire := _m(g, "tire", Color(0.07, 0.07, 0.08))
	for s in [-1, 1]:
		_cy(g, t, tire, Vector3(0, 0.18, s * 0.38), 0.18, 0.18, 0.74, 8, Vector3(0, 0, PI * 0.5))
	_cy(g, t, tire, Vector3(0, 0.45, -0.62), 0.17, 0.17, 0.1, 8, Vector3(PI * 0.5, 0, 0))


static func _sandbags(g: Node3D, t: Node3D) -> void:
	var m := _m(g, "sandbag", Color(0.72, 0.64, 0.46))
	_cap(g, t, m, Vector3(-0.36, 0.14, 0), 0.15, 0.72, Vector3(0, 0, PI * 0.5))
	_cap(g, t, m, Vector3(0.36, 0.14, 0), 0.15, 0.72, Vector3(0, 0, PI * 0.5))
	_cap(g, t, m, Vector3(0, 0.38, 0), 0.15, 0.72, Vector3(0, 0, PI * 0.5))


static func _fence_mil(g: Node3D, t: Node3D) -> void:
	var steel := _m(g, "steel_grey", Color(0.5, 0.52, 0.55), {"metal": 0.5})
	for s in [-1, 1]:
		_cy(g, t, steel, Vector3(s * 0.85, 0.5, 0), 0.03, 0.03, 1.0, 5)
	_no_shadow(_bx(g, t, _m(g, "chainlink", Color(0.7, 0.72, 0.75, 0.35)), Vector3(0, 0.5, 0), Vector3(1.7, 0.9, 0.02)))


static func _radar(g: Node3D, t: Node3D, k: float) -> void:
	var steel := _m(g, "steel_grey", Color(0.5, 0.52, 0.55), {"metal": 0.5})
	_bx(g, t, _m(g, "olive_drab", OLIVE_DRAB), Vector3(0, 0.25, 0) * k, Vector3(0.7, 0.5, 0.7) * k)
	_cy(g, t, steel, Vector3(0, 0.75, 0) * k, 0.05 * k, 0.07 * k, 0.5 * k, 6)
	var holder := _n(t, Vector3(0, 1.0, 0) * k)
	var rotor := _n(holder, Vector3.ZERO)
	_bx(g, rotor, _m(g, "radar_white", Color(0.9, 0.9, 0.88)), Vector3(0, 0.2, 0) * k, Vector3(1.3, 0.4, 0.06) * k, Vector3(-0.25, 0, 0))
	_spin(g, holder, rotor)


static func _street_light(g: Node3D, t: Node3D) -> void:
	var steel := _m(g, "steel_dark", Color(0.3, 0.32, 0.34), {"metal": 0.5})
	_cy(g, t, steel, Vector3(0, 1.1, 0), 0.04, 0.06, 2.2, 6)
	_bx(g, t, steel, Vector3(0.3, 2.18, 0), Vector3(0.6, 0.06, 0.08))
	_bx(g, t, _glow(g, "street_lamp", Color(1.0, 0.95, 0.8), 2.0), Vector3(0.55, 2.12, 0), Vector3(0.24, 0.06, 0.14))


static func _planter_tree(g: Node3D, t: Node3D) -> void:
	_bx(g, t, _m(g, "concrete", CONCRETE), Vector3(0, 0.18, 0), Vector3(0.8, 0.36, 0.8))
	_cy(g, t, _m(g, "trunk", TRUNK), Vector3(0, 0.75, 0), 0.06, 0.08, 0.9, 6)
	_sp(g, t, _m(g, "sub_tree_a", Color(0.26, 0.56, 0.18)), Vector3(0, 1.45, 0), 0.55, Vector3(1, 0.9, 1), 8)


static func _billboard(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var steel := _m(g, "steel_dark", Color(0.3, 0.32, 0.34), {"metal": 0.5})
	for s in [-1, 1]:
		_bx(g, t, steel, Vector3(s * 0.6, 0.8, 0), Vector3(0.1, 1.6, 0.1))
	_bx(g, t, _m(g, "board_back", Color(0.2, 0.2, 0.22)), Vector3(0, 1.9, -0.02), Vector3(1.9, 0.9, 0.08))
	var c: Color = [Color(1.0, 0.35, 0.2), Color(0.2, 0.6, 1.0), Color(1.0, 0.8, 0.15)][r.randi() % 3]
	_bx(g, t, _glow(g, "ad_" + c.to_html(), c, 0.8), Vector3(0, 1.9, 0.03), Vector3(1.76, 0.76, 0.02))


static func _hydrant(g: Node3D, t: Node3D) -> void:
	var m := _m(g, "hydrant", Color(0.85, 0.15, 0.12))
	_cy(g, t, m, Vector3(0, 0.22, 0), 0.1, 0.12, 0.44, 7)
	_sp(g, t, m, Vector3(0, 0.45, 0), 0.1, Vector3.ONE, 6)


# ------------------------------------------------------------------ digital
static func _neon_c(r: RandomNumberGenerator) -> Color:
	return CYAN if r.randf() < 0.55 else MAGENTA


static func _neon_pylon(g: Node3D, t: Node3D, r: RandomNumberGenerator, k: float) -> void:
	var c := _neon_c(r)
	var dark := _m(g, "carbon", Color(0.08, 0.08, 0.1), {"metal": 0.4, "rough": 0.4})
	var glow := _glow(g, "neon_" + c.to_html(), c, 2.4)
	var h := 2.4 * k
	_bx(g, t, dark, Vector3(0, h * 0.5, 0), Vector3(0.3, h, 0.3) * Vector3(k, 1, k))
	for s in [-1, 1]:
		_bx(g, t, glow, Vector3(s * 0.16 * k, h * 0.5, 0.16 * k), Vector3(0.05, h * 0.92, 0.05))
	_sp(g, t, glow, Vector3(0, h + 0.15 * k, 0), 0.16 * k, Vector3.ONE, 6)


static func _holo_board(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var c := _neon_c(r)
	_cy(g, t, _m(g, "carbon", Color(0.08, 0.08, 0.1), {"metal": 0.4, "rough": 0.4}), Vector3(0, 0.6, 0), 0.06, 0.08, 1.2, 6)
	_bx(g, t, _glow(g, "neon_" + c.to_html(), c, 2.4), Vector3(0, 1.2, 0), Vector3(1.5, 0.05, 0.08))
	_no_shadow(_bx(g, t, _m(g, "holo_" + c.to_html(), Color(c.r, c.g, c.b, 0.35), {"emit": c, "emit_e": 1.2, "unshaded": true}),
		Vector3(0, 1.7, 0), Vector3(1.5, 0.9, 0.03)))


static func _holo_cube(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var c := _neon_c(r)
	_cy(g, t, _m(g, "carbon", Color(0.08, 0.08, 0.1), {"metal": 0.4, "rough": 0.4}), Vector3(0, 0.15, 0), 0.3, 0.36, 0.3, 8)
	_cy(g, t, _glow(g, "neon_" + c.to_html(), c, 2.4), Vector3(0, 0.31, 0), 0.24, 0.24, 0.03, 8)
	var holder := _n(t, Vector3(0, 0.85, 0))
	var rotor := _n(holder, Vector3.ZERO)
	_no_shadow(_bx(g, rotor, _m(g, "holo_" + c.to_html(), Color(c.r, c.g, c.b, 0.35), {"emit": c, "emit_e": 1.2, "unshaded": true}),
		Vector3.ZERO, Vector3(0.42, 0.42, 0.42), Vector3(0.62, 0, 0.62)))
	_spin(g, holder, rotor)


static func _light_pole(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var c := _neon_c(r)
	_cy(g, t, _m(g, "carbon", Color(0.08, 0.08, 0.1), {"metal": 0.4, "rough": 0.4}), Vector3(0, 0.9, 0), 0.04, 0.06, 1.8, 6)
	_bx(g, t, _glow(g, "neon_" + c.to_html(), c, 2.4), Vector3(0, 1.4, 0), Vector3(0.08, 1.0, 0.08))


static func _dish(g: Node3D, t: Node3D, k: float) -> void:
	var white := _m(g, "dish_white", Color(0.86, 0.87, 0.86))
	_cy(g, t, _m(g, "concrete", CONCRETE), Vector3(0, 0.2, 0) * k, 0.3 * k, 0.4 * k, 0.4 * k, 8)
	_cy(g, t, _m(g, "steel_grey", Color(0.5, 0.52, 0.55), {"metal": 0.5}), Vector3(0, 0.75, 0) * k, 0.07 * k, 0.09 * k, 0.8 * k, 6)
	var head := _n(t, Vector3(0, 1.25, 0) * k)
	head.rotation.x = 0.75
	_cy(g, head, white, Vector3.ZERO, 0.95 * k, 0.18 * k, 0.32 * k, 12)
	_cy(g, head, _m(g, "dish_inner", Color(0.56, 0.6, 0.66), {"metal": 0.3, "rough": 0.5}), Vector3(0, 0.165, 0) * k, 0.8 * k, 0.8 * k, 0.02 * k, 12)
	_cy(g, head, _m(g, "feed", Color(0.3, 0.3, 0.32)), Vector3(0, 0.45, 0) * k, 0.03 * k, 0.04 * k, 0.75 * k, 4)
	_cy(g, head, _m(g, "feed", Color(0.3, 0.3, 0.32)), Vector3(0, 0.85, 0) * k, 0.1 * k, 0.06 * k, 0.14 * k, 6)


static func _solar_row(g: Node3D, t: Node3D, n: int) -> void:
	var panel := _m(g, "solar", Color(0.12, 0.2, 0.45), {"metal": 0.4, "rough": 0.25})
	var steel := _m(g, "steel_grey", Color(0.5, 0.52, 0.55), {"metal": 0.5})
	for i in n:
		var x := (i - (n - 1) * 0.5) * 1.5
		_bx(g, t, steel, Vector3(x, 0.25, 0), Vector3(0.08, 0.5, 0.08))
		_bx(g, t, panel, Vector3(x, 0.55, 0), Vector3(1.4, 0.05, 0.85), Vector3(-0.5, 0, 0))


static func _mast(g: Node3D, t: Node3D, h: float) -> void:
	var steel := _m(g, "steel_grey", Color(0.5, 0.52, 0.55), {"metal": 0.5})
	_cy(g, t, steel, Vector3(0, h * 0.5, 0), 0.03, 0.09, h, 5)
	_bx(g, t, steel, Vector3(0, h * 0.6, 0), Vector3(0.6, 0.04, 0.04))
	_bx(g, t, steel, Vector3(0, h * 0.8, 0), Vector3(0.04, 0.04, 0.45))
	_pulse(g, _sp(g, t, _glow(g, "warn_red", Color(1.0, 0.12, 0.08), 3.0), Vector3(0, h + 0.05, 0), 0.08, Vector3.ONE, 6))


static func _dome(g: Node3D, t: Node3D) -> void:
	_sp(g, t, _m(g, "dish_white", Color(0.86, 0.87, 0.86)), Vector3.ZERO, 0.95, Vector3(1, 0.85, 1), 10)
	_bx(g, t, _m(g, "door_grey", Color(0.4, 0.42, 0.45)), Vector3(0, 0.25, 0.9), Vector3(0.3, 0.5, 0.1))


static func _tube(g: Node3D, t: Node3D, k: float) -> void:
	var white := _m(g, "lab_white", WHITE_PANEL)
	_cy(g, t, white, Vector3(0, 0.1, 0) * k, 0.36 * k, 0.4 * k, 0.2 * k, 10)
	_no_shadow(_cy(g, t, _m(g, "lab_liquid", Color(0.3, 0.95, 0.85, 0.55), {"emit": Color(0.2, 0.9, 0.8), "emit_e": 1.2}), Vector3(0, 0.72, 0) * k, 0.25 * k, 0.25 * k, 1.0 * k, 10))
	_no_shadow(_cy(g, t, _m(g, "glass", Color(0.8, 0.95, 1.0, 0.25), {"rough": 0.05, "metal": 0.2}), Vector3(0, 0.9, 0) * k, 0.31 * k, 0.31 * k, 1.4 * k, 10))
	_cy(g, t, white, Vector3(0, 1.66, 0) * k, 0.36 * k, 0.36 * k, 0.14 * k, 10)


static func _console(g: Node3D, t: Node3D) -> void:
	_bx(g, t, _m(g, "lab_white", WHITE_PANEL), Vector3(0, 0.32, 0), Vector3(0.9, 0.64, 0.5))
	_bx(g, t, _glow(g, "screen_cyan", Color(0.3, 0.85, 1.0), 1.4), Vector3(0, 0.66, 0.05), Vector3(0.8, 0.04, 0.36), Vector3(0.35, 0, 0))
	_bx(g, t, _m(g, "carbon", Color(0.08, 0.08, 0.1), {"metal": 0.4, "rough": 0.4}), Vector3(0, 0.95, -0.22), Vector3(0.7, 0.5, 0.05))


static func _robot_arm(g: Node3D, t: Node3D) -> void:
	var orange := _m(g, "arm_orange", Color(1.0, 0.55, 0.12))
	var grey := _m(g, "steel_dark", Color(0.3, 0.32, 0.34), {"metal": 0.5})
	_cy(g, t, grey, Vector3(0, 0.14, 0), 0.32, 0.36, 0.28, 10)
	_bx(g, t, orange, Vector3(0.14, 0.7, 0), Vector3(0.18, 0.95, 0.18), Vector3(0, 0, -0.3))
	_sp(g, t, grey, Vector3(0.28, 1.15, 0), 0.14, Vector3.ONE, 7)
	_bx(g, t, orange, Vector3(0.0, 1.32, 0), Vector3(0.14, 0.7, 0.14), Vector3(0, 0, 1.1))
	_bx(g, t, grey, Vector3(-0.32, 1.48, 0), Vector3(0.12, 0.2, 0.24))


static func _potted(g: Node3D, t: Node3D) -> void:
	_cy(g, t, _m(g, "lab_white", WHITE_PANEL), Vector3(0, 0.16, 0), 0.2, 0.15, 0.32, 8)
	_sp(g, t, _m(g, "sub_tree_a", Color(0.26, 0.56, 0.18)), Vector3(0, 0.52, 0), 0.3, Vector3(1, 1.2, 1), 7)


# ------------------------------------------------------------------ data center
static func _rack_row(g: Node3D, t: Node3D, n: int, r: RandomNumberGenerator) -> void:
	var w := 0.62 * n
	_bx(g, t, _m(g, "rack", Color(0.08, 0.09, 0.11), {"metal": 0.5, "rough": 0.4}), Vector3(0, 0.95, 0), Vector3(w, 1.9, 0.8))
	var blue := _glow(g, "led_blue", Color(0.25, 0.55, 1.0), 2.4)
	var green := _glow(g, "led_green", Color(0.2, 1.0, 0.5), 2.0)
	for i in 3:
		var mi := _bx(g, t, blue if i != 1 else green, Vector3(0, 0.5 + i * 0.5, 0.41), Vector3(w - 0.12, 0.05, 0.02))
		if i < 2:
			_pulse(g, mi, r.randf() * 3.0)
	_bx(g, t, _m(g, "rack_top", Color(0.2, 0.22, 0.26), {"metal": 0.5}), Vector3(0, 1.92, 0), Vector3(w + 0.06, 0.06, 0.86))


static func _cables(g: Node3D, t: Node3D, th: String) -> void:
	var cols := [Color(0.1, 0.1, 0.12), Color(0.15, 0.3, 0.7), Color(0.9, 0.7, 0.1)]
	if th == "core":
		cols = [Color(0.08, 0.06, 0.07), Color(0.12, 0.1, 0.11), Color(0.9, 0.12, 0.08)]
	for i in 3:
		var c: Color = cols[i]
		var m := _m(g, "cable_" + c.to_html(), c, {"emit": c, "emit_e": 1.5} if c.r > 0.8 and th == "core" else {})
		_cy(g, t, m, Vector3(-0.15 + i * 0.15, 0.06, (i - 1) * 0.1), 0.05, 0.05, 1.8, 6, Vector3(PI * 0.5, (i - 1) * 0.15, 0))


static func _cooling_unit(g: Node3D, t: Node3D) -> void:
	_bx(g, t, _m(g, "unit_grey", Color(0.5, 0.53, 0.57), {"metal": 0.4}), Vector3(0, 0.35, 0), Vector3(1.0, 0.7, 1.0))
	_cy(g, t, _m(g, "carbon", Color(0.08, 0.08, 0.1), {"metal": 0.4, "rough": 0.4}), Vector3(0, 0.71, 0), 0.38, 0.38, 0.04, 12)
	var holder := _n(t, Vector3(0, 0.75, 0))
	var rotor := _n(holder, Vector3.ZERO)
	var blade := _m(g, "fan_blade", Color(0.7, 0.72, 0.75), {"metal": 0.5})
	_bx(g, rotor, blade, Vector3.ZERO, Vector3(0.7, 0.03, 0.12))
	_bx(g, rotor, blade, Vector3.ZERO, Vector3(0.12, 0.03, 0.7))
	_spin(g, holder, rotor)


static func _big_pipe(g: Node3D, t: Node3D) -> void:
	var steel := _m(g, "pipe_steel", Color(0.62, 0.68, 0.74), {"metal": 0.6, "rough": 0.35})
	_cy(g, t, steel, Vector3(0, 0.5, 0), 0.32, 0.32, 3.0, 10, Vector3(0, 0, PI * 0.5))
	for s in [-1, 1]:
		_cy(g, t, steel, Vector3(s * 1.0, 0.5, 0), 0.4, 0.4, 0.12, 10, Vector3(0, 0, PI * 0.5))
		_bx(g, t, _m(g, "steel_dark", Color(0.3, 0.32, 0.34), {"metal": 0.5}), Vector3(s * 1.0, 0.1, 0), Vector3(0.2, 0.2, 0.7))
	_bx(g, t, _m(g, "frost", Color(0.92, 0.96, 1.0)), Vector3(0.2, 0.8, 0), Vector3(1.6, 0.05, 0.36))


static func _ice(g: Node3D, t: Node3D, r: RandomNumberGenerator, k: float) -> void:
	var m := _m(g, "ice", Color(0.72, 0.9, 1.0, 0.8), {"emit": Color(0.4, 0.7, 1.0), "emit_e": 0.5, "rough": 0.1})
	for i in 3:
		var a := TAU * i / 3.0 + r.randf() * 0.6
		var h := r.randf_range(0.5, 1.0) * k
		_cy(g, t, m, Vector3(cos(a) * 0.22 * k, h * 0.45, sin(a) * 0.22 * k), 0.0, r.randf_range(0.14, 0.24) * k, h, 5,
			Vector3(r.randf_range(-0.35, 0.35), 0, r.randf_range(-0.35, 0.35)))


static func _fan(g: Node3D, t: Node3D) -> void:
	_bx(g, t, _m(g, "unit_grey", Color(0.5, 0.53, 0.57), {"metal": 0.4}), Vector3(0, 0.12, 0), Vector3(1.3, 0.24, 1.3))
	_cy(g, t, _m(g, "carbon", Color(0.08, 0.08, 0.1), {"metal": 0.4, "rough": 0.4}), Vector3(0, 0.25, 0), 0.55, 0.55, 0.04, 12)
	var holder := _n(t, Vector3(0, 0.3, 0))
	var rotor := _n(holder, Vector3.ZERO)
	var blade := _m(g, "fan_blade", Color(0.7, 0.72, 0.75), {"metal": 0.5})
	_bx(g, rotor, blade, Vector3.ZERO, Vector3(1.0, 0.03, 0.16))
	_bx(g, rotor, blade, Vector3.ZERO, Vector3(0.16, 0.03, 1.0))
	_spin(g, holder, rotor)


static func _valve(g: Node3D, t: Node3D) -> void:
	var steel := _m(g, "pipe_steel", Color(0.62, 0.68, 0.74), {"metal": 0.6, "rough": 0.35})
	_cy(g, t, steel, Vector3(0, 0.45, 0), 0.12, 0.12, 0.9, 8)
	_cy(g, t, steel, Vector3(0, 0.25, 0), 0.1, 0.1, 0.9, 8, Vector3(PI * 0.5, 0, 0))
	_tor(g, t, _m(g, "valve_red", Color(0.85, 0.15, 0.1)), Vector3(0, 0.95, 0), 0.16, 0.22, Vector3.ZERO, 12)


static func _energy_pillar(g: Node3D, t: Node3D, k: float) -> void:
	var dark := _m(g, "core_black", Color(0.08, 0.06, 0.08), {"metal": 0.6, "rough": 0.25})
	_cy(g, t, dark, Vector3(0, 0.15, 0) * k, 0.42 * k, 0.52 * k, 0.3 * k, 6)
	var core := _cy(g, t, _glow(g, "core_red", Color(1.0, 0.15, 0.08), 3.0), Vector3(0, 1.35, 0) * k, 0.16 * k, 0.2 * k, 2.1 * k, 6)
	_pulse(g, core, 0.0)
	_no_shadow(_cy(g, t, _m(g, "core_sheath", Color(1.0, 0.25, 0.15, 0.22), {"emit": Color(1.0, 0.2, 0.1), "emit_e": 0.8, "unshaded": true}),
		Vector3(0, 1.3, 0) * k, 0.3 * k, 0.34 * k, 2.0 * k, 6))
	_cy(g, t, dark, Vector3(0, 2.6, 0) * k, 0.0, 0.3 * k, 0.45 * k, 6)


static func _data_spire(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var h := r.randf_range(2.2, 3.4)
	_cy(g, t, _m(g, "spire_glass", Color(0.16, 0.13, 0.18), {"metal": 0.6, "rough": 0.2}), Vector3(0, h * 0.5, 0), 0.0, 0.42, h, 4)
	var red := _glow(g, "core_red2", Color(1.0, 0.2, 0.1), 2.2)
	_cy(g, t, red, Vector3(0, h * 0.25, 0), 0.32, 0.34, 0.08, 4)
	_cy(g, t, red, Vector3(0, h * 0.55, 0), 0.19, 0.21, 0.06, 4)


static func _broken_robot(g: Node3D, t: Node3D, r: RandomNumberGenerator) -> void:
	var white := _m(g, "robot_white", Color(0.86, 0.86, 0.88), {"metal": 0.3, "rough": 0.5})
	var grey := _m(g, "steel_dark", Color(0.3, 0.32, 0.34), {"metal": 0.5})
	_bx(g, t, white, Vector3(0, 0.26, 0), Vector3(0.6, 0.5, 0.42), Vector3(0, 0, 1.2))
	_bx(g, t, white, Vector3(0.55, 0.16, 0.25), Vector3(0.32, 0.3, 0.3), Vector3(0.4, 0.5, 0))
	_bx(g, t, _m(g, "eye_dead", Color(0.25, 0.05, 0.04)), Vector3(0.6, 0.2, 0.41), Vector3(0.2, 0.06, 0.02), Vector3(0, 0.5, 0))
	_cy(g, t, grey, Vector3(-0.5, 0.08, 0.35), 0.07, 0.08, 0.7, 6, Vector3(PI * 0.5, r.randf(), 0))
	_bx(g, t, _m(g, "robot_orange", Color(0.95, 0.45, 0.12)), Vector3(-0.1, 0.48, 0.1), Vector3(0.2, 0.06, 0.3), Vector3(0, 0, 1.2))


# ================================================================== landmarks
static func _landmarks(g: Node3D, th: String, free: Callable, r: RandomNumberGenerator, occ: Array) -> void:
	match th:
		"highland":   # stone circle on the far hill
			var n := _n(g, Vector3(1.5, 0, -10.9))
			for k in 8:
				var a := TAU * k / 8.0
				var s := _n(n, Vector3(cos(a) * 1.7, 0, sin(a) * 1.25), a)
				_standing_stone(g, s, r, r.randf_range(1.3, 2.0))
			_bx(g, n, _m(g, "menhir", Color(0.56, 0.57, 0.55)), Vector3(0, 0.35, 0), Vector3(1.0, 0.7, 0.5))
			occ.append(Vector3(1.5, -10.9, 2.2))
			var h := _n(g, Vector3(10.0, 0, -11.0), 0.3, 1.1)
			_roundhouse(g, h, false)
			_flame(g, g, Vector3(8.6, 0, -10.2), 0.6, 0.0)
			occ.append(Vector3(9.6, -10.8, 1.8))
		"forge":   # a row of smoking forge chimneys
			for i in 4:
				var x := -1.5 + i * 3.6
				var c := _n(g, Vector3(x, 0, -10.8 - (i % 2) * 0.5))
				_bx(g, c, _m(g, "stone_dark", Color(0.28, 0.26, 0.25)), Vector3(0, 0.4, 0), Vector3(1.5, 0.8, 1.2))
				_bx(g, c, _glow(g, "furnace_glow", Color(1.0, 0.45, 0.1), 2.6), Vector3(0, 0.35, 0.61), Vector3(0.6, 0.4, 0.02))
				_cy(g, c, _m(g, "stone_dark", Color(0.28, 0.26, 0.25)), Vector3(0.2, 2.0, -0.1), 0.26, 0.4, 2.6, 7)
				_smoke(g, c, Vector3(0.2, 3.4, -0.1), 1.1, Color(0.2, 0.18, 0.18, 0.6))
				occ.append(Vector3(x, -10.8, 1.3))
		"bog":   # stilt hut on a boardwalk
			var n := _n(g, Vector3(3.0, 0, -10.9))
			var post := _m(g, "post", WOOD_D)
			for k in 4:
				var a := TAU * k / 4.0 + PI * 0.25
				_cy(g, n, post, Vector3(cos(a) * 0.75, 0.4, sin(a) * 0.75), 0.07, 0.07, 0.8, 5)
			_bx(g, n, _m(g, "plank", Color(0.5, 0.36, 0.22)), Vector3(0, 0.82, 0), Vector3(1.9, 0.08, 1.9))
			_cy(g, n, _m(g, "wattle", Color(0.62, 0.5, 0.34)), Vector3(0, 1.2, 0), 0.7, 0.72, 0.7, 9)
			_cy(g, n, _m(g, "thatch", Color(0.78, 0.64, 0.32)), Vector3(0, 1.95, 0), 0.0, 0.95, 0.85, 9)
			for i in 3:
				var b := _n(g, Vector3(4.8 + i * 1.6, 0, -10.5), PI * 0.5)
				_boardwalk(g, b)
			occ.append(Vector3(3.0, -10.9, 1.4))
			occ.append(Vector3(6.4, -10.5, 2.2))
		"olive":   # ruined temple up the hill, lined with cypresses
			var n := _n(g, Vector3(3.0, 0, -11.0))
			_temple_front(g, n, 0.95)
			occ.append(Vector3(3.0, -11.0, 1.9))
			for x in [-0.2, 0.6, 5.4, 6.2]:
				_cypress(g, _n(g, Vector3(x, 0, -11.6), 0.0, 1.15))
				occ.append(Vector3(x, -11.6, 0.4))
		"coast":   # lighthouse by the inlet and moored boats
			var lx := _river_x(g, -10.6)
			var px := (lx - 2.6) if not is_nan(lx) else 8.0
			var n := _n(g, Vector3(px, 0, -10.8))
			var m := _m(g, "marble", MARBLE)
			_bx(g, n, m, Vector3(0, 0.5, 0), Vector3(1.6, 1.0, 1.6))
			_bx(g, n, m, Vector3(0, 1.75, 0), Vector3(1.1, 1.5, 1.1))
			_cy(g, n, m, Vector3(0, 3.0, 0), 0.38, 0.45, 1.0, 8)
			_flame(g, n, Vector3(0, 3.5, 0), 0.6, 0.0)
			occ.append(Vector3(px, -10.8, 1.2))
			if not is_nan(lx):
				for z in [-11.6, 10.4, 11.8]:
					var bx := _river_x(g, z)
					var b := _n(g, Vector3(bx + r.randf_range(-0.3, 0.3), 0.02, z), r.randf_range(-0.3, 0.3), 0.9)
					_boat(g, b)
		"acropolis":   # the great temple on the hill
			_parthenon(g, Vector3(4.0, 0, -11.0))
			occ.append(Vector3(4.0, -11.0, 3.6))
		"farmland":   # windmill
			_windmill(g, Vector3(4.0, 0, -10.9))
			occ.append(Vector3(4.0, -10.9, 1.4))
		"castle":   # a trebuchet aimed at the robots
			_trebuchet(g, Vector3(3.0, 0, -10.9))
			occ.append(Vector3(3.0, -10.9, 1.6))
		"darkwood":   # ruined watchtower
			var n := _n(g, Vector3(4.0, 0, -10.8))
			var m := _m(g, "ruin_dark", Color(0.36, 0.38, 0.36))
			_cy(g, n, m, Vector3(0, 1.3, 0), 0.75, 0.9, 2.6, 9)
			for k in 4:
				var a := TAU * k / 4.0
				_bx(g, n, m, Vector3(cos(a) * 0.65, 2.75 - (k % 2) * 0.15, sin(a) * 0.65), Vector3(0.36, 0.3 + (k % 2) * 0.2, 0.36), Vector3(0, a, 0))
			_bx(g, n, _m(g, "vine", Color(0.18, 0.46, 0.16)), Vector3(0.2, 1.2, 0.85), Vector3(0.5, 1.6, 0.04))
			_flame(g, n, Vector3(0, 2.6, 0), 0.4, 0.0)
			occ.append(Vector3(4.0, -10.8, 1.2))
		"harbor":   # a tall ship anchored in the channel, docks along the banks
			var sx := _river_x(g, -10.6)
			if not is_nan(sx):
				_tall_ship(g, Vector3(sx, 0, -10.6))
				for z in [-9.9, 10.2]:
					var dx := _river_x(g, z)
					for s in [-1, 1]:
						var d := _n(g, Vector3(dx + s * 1.55, 0, z), 0.0)
						_dock(g, d)
						occ.append(Vector3(dx + s * 1.55, z, 1.0))
		"fortress":   # a redoubt line with guns
			var n := _n(g, Vector3(4.0, 0, -10.9))
			_sp(g, n, _m(g, "berm", Color(0.4, 0.4, 0.22)), Vector3.ZERO, 1.0, Vector3(4.2, 0.6, 1.0), 10)
			for i in 2:
				var c := _n(n, Vector3(-1.4 + i * 2.8, 0.45, 0.45), 0.0, 1.1)
				_cannon(g, c)
			for i in 5:
				_cy(g, n, _m(g, "wicker", Color(0.58, 0.45, 0.27)), Vector3(-3.2 + i * 1.6, 0.55, -0.2), 0.26, 0.26, 0.6, 8)
			_flag(g, _n(n, Vector3(0, 0.5, -0.3)), Color(0.14, 0.22, 0.52))
			occ.append(Vector3(2.0, -10.9, 2.2))
			occ.append(Vector3(6.0, -10.9, 2.2))
		"jungle":   # vine-covered step pyramid
			_pyramid(g, Vector3(4.0, 0, -11.5))
			occ.append(Vector3(4.0, -11.5, 3.4))
		"railyard":   # a track across the top with a locomotive and a water tower
			_train(g, Vector3(4.0, 0, -11.2))
			_water_tower(g, _n(g, Vector3(11.4, 0, -9.95)))
			for k in 6:
				occ.append(Vector3(-13.0 + k * 5.0, -11.2, 2.6))
			occ.append(Vector3(11.4, -9.95, 0.9))
		"factory", "smog":   # row of tall smoking chimneys
			var cnt := 5 if th == "factory" else 3
			for i in cnt:
				var x := -1.0 + i * (3.0 if th == "factory" else 5.5)
				var z := -10.9 - (i % 2) * 0.6
				var c := _n(g, Vector3(x, 0, z))
				var h := 4.2 + (i % 3) * 0.5
				_bx(g, c, _m(g, "brick", BRICK), Vector3(0, 0.3, 0), Vector3(1.1, 0.6, 1.1))
				_cy(g, c, _m(g, "brick_dark", BRICK.darkened(0.3)), Vector3(0, h * 0.5, 0), 0.3, 0.45, h, 8)
				_cy(g, c, _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45}), Vector3(0, h, 0), 0.36, 0.36, 0.15, 8)
				_smoke(g, c, Vector3(0, h + 0.3, 0), 1.3, Color(0.36, 0.34, 0.33, 0.55))
				occ.append(Vector3(x, z, 0.9))
			if th == "smog":   # gasometer
				var n := _n(g, Vector3(7.25, 0, -11.4))
				_cy(g, n, _m(g, "gas_tank", Color(0.38, 0.42, 0.36), {"metal": 0.3}), Vector3(0, 0.9, 0), 1.3, 1.3, 1.8, 12)
				var iron := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
				for k in 6:
					var a := TAU * k / 6.0
					_bx(g, n, iron, Vector3(cos(a) * 1.4, 1.25, sin(a) * 1.4), Vector3(0.1, 2.5, 0.1))
				_tor(g, n, iron, Vector3(0, 2.45, 0), 1.33, 1.45, Vector3.ZERO, 16)
				occ.append(Vector3(7.25, -11.4, 1.6))
		"suburb":   # town water tower
			var n := _n(g, Vector3(4.0, 0, -10.9))
			var steel := _m(g, "post_white", Color(0.95, 0.95, 0.93))
			_cy(g, n, steel, Vector3(0, 1.5, 0), 0.25, 0.35, 3.0, 8)
			_sp(g, n, _m(g, "wt_blue", Color(0.4, 0.66, 0.9)), Vector3(0, 3.4, 0), 1.0, Vector3(1, 0.8, 1), 10)
			occ.append(Vector3(4.0, -10.9, 1.2))
		"military":   # control tower and a parked jet
			var n := _n(g, Vector3(2.0, 0, -10.9))
			_bx(g, n, _m(g, "concrete", CONCRETE), Vector3(0, 1.3, 0), Vector3(1.0, 2.6, 1.0))
			_bx(g, n, _m(g, "tower_glass", Color(0.3, 0.55, 0.65), {"rough": 0.15, "metal": 0.3}), Vector3(0, 2.9, 0), Vector3(1.5, 0.6, 1.5))
			_bx(g, n, _m(g, "concrete", CONCRETE), Vector3(0, 3.27, 0), Vector3(1.6, 0.14, 1.6))
			_mast(g, _n(n, Vector3(0.4, 3.34, 0.4)), 1.0)
			_radar(g, _n(n, Vector3(-0.4, 3.34, -0.3)), 0.6)
			occ.append(Vector3(2.0, -10.9, 1.1))
			_jet(g, Vector3(6.5, 0, -10.9))
			occ.append(Vector3(6.5, -10.9, 2.0))
		"metro":   # skyline
			var cols := [Color(0.42, 0.55, 0.68), Color(0.6, 0.64, 0.68), Color(0.3, 0.42, 0.55), Color(0.72, 0.7, 0.64)]
			var x := -13.0
			var i := 0
			while x < 13.5:
				var w := r.randf_range(1.6, 2.4)
				var h := r.randf_range(3.6, 6.5)
				var z := -11.0 - r.randf_range(0.0, 0.9)
				if free.call(Vector2(x, z), 0.0):
					_tower_block(g, Vector3(x, 0, z), w, h, cols[i % cols.size()], i % 3 == 0)
					occ.append(Vector3(x, z, w * 0.75))
				x += w + r.randf_range(0.5, 1.4)
				i += 1
		"neon":   # dark towers with neon edges
			var x := -12.5
			var i := 0
			while x < 13.0:
				var w := r.randf_range(1.4, 2.2)
				var h := r.randf_range(3.0, 5.5)
				var z := -11.0 - r.randf_range(0.0, 0.8)
				var n := _n(g, Vector3(x, 0, z))
				var c := CYAN if i % 2 == 0 else MAGENTA
				_bx(g, n, _m(g, "carbon", Color(0.08, 0.08, 0.1), {"metal": 0.4, "rough": 0.4}), Vector3(0, h * 0.5, 0), Vector3(w, h, w))
				var gm := _glow(g, "neon_" + c.to_html(), c, 2.4)
				for s in [-1, 1]:
					_bx(g, n, gm, Vector3(s * w * 0.5, h * 0.5, w * 0.5), Vector3(0.06, h, 0.06))
				_bx(g, n, gm, Vector3(0, h, w * 0.5), Vector3(w, 0.06, 0.06))
				occ.append(Vector3(x, z, w * 0.75))
				x += w + r.randf_range(0.8, 1.6)
				i += 1
		"satellite":   # the big dish
			var n := _n(g, Vector3(3.0, 0, -11.1), 0.0, 2.4)
			_dish(g, n, 1.0)
			occ.append(Vector3(3.0, -11.1, 2.4))
			_mast(g, _n(g, Vector3(7.5, 0, -11.0)), 3.6)
			occ.append(Vector3(7.5, -11.0, 0.4))
		"lab":   # the lab's outer wall with a viewing window
			var n := _n(g, Vector3(0, 0, -10.7))
			_bx(g, n, _m(g, "lab_white", WHITE_PANEL), Vector3(0, 1.0, 0), Vector3(31.0, 2.0, 0.5))
			_bx(g, n, _m(g, "glass", Color(0.8, 0.95, 1.0, 0.25), {"rough": 0.05, "metal": 0.2}), Vector3(0, 1.15, 0.27), Vector3(24.0, 0.8, 0.02))
			_bx(g, n, _glow(g, "cyan_strip", CYAN, 1.8), Vector3(0, 0.28, 0.27), Vector3(31.0, 0.06, 0.02))
			_bx(g, n, _glow(g, "cyan_strip", CYAN, 1.8), Vector3(0, 2.0, 0.27), Vector3(31.0, 0.06, 0.02))
			_bx(g, n, _m(g, "door_grey", Color(0.4, 0.42, 0.45)), Vector3(4.0, 0.8, 0.28), Vector3(1.2, 1.6, 0.04))
			occ.append(Vector3(0, -10.7, 0.6))
		"server":   # a wall of server racks
			var x := -13.0
			while x < 13.5:
				if free.call(Vector2(x, -10.8), 0.0):
					var n := _n(g, Vector3(x, 0, -10.8), 0.0, 1.25)
					_rack_row(g, n, 4, r)
				x += 3.4
			occ.append(Vector3(0, -10.8, 0.8))
		"cooling":   # cooling towers
			for i in 3:
				var x := -1.0 + i * 5.0
				var z := -11.3 + (i % 2) * 0.4
				var n := _n(g, Vector3(x, 0, z))
				var c := _m(g, "cooling_tower", Color(0.66, 0.7, 0.75))
				_cy(g, n, c, Vector3(0, 1.0, 0), 1.05, 1.5, 2.0, 12)
				_cy(g, n, c, Vector3(0, 2.6, 0), 1.2, 1.05, 1.2, 12)
				_cy(g, n, _m(g, "tower_mouth", Color(0.12, 0.14, 0.18)), Vector3(0, 3.21, 0), 1.1, 1.1, 0.02, 12)
				_cy(g, n, _glow(g, "cyan_strip", CYAN, 1.8), Vector3(0, 2.2, 0), 1.08, 1.08, 0.12, 12)
				_smoke(g, n, Vector3(0, 3.3, 0), 1.2, Color(0.95, 0.97, 1.0, 0.3))
				occ.append(Vector3(x, z, 1.6))
		"core":
			_the_core(g, Vector3(3.5, 0, -11.2))
			occ.append(Vector3(3.5, -11.2, 3.0))


static func _parthenon(g: Node3D, pos: Vector3) -> void:
	var n := _n(g, pos)
	var m := _m(g, "marble", MARBLE)
	_bx(g, n, m, Vector3(0, 0.15, 0), Vector3(7.2, 0.3, 2.8))
	_bx(g, n, m, Vector3(0, 0.42, 0), Vector3(6.8, 0.24, 2.5))
	for i in 7:
		_cy(g, n, m, Vector3(-3.0 + i * 1.0, 1.64, 1.0), 0.2, 0.24, 2.2, 8)
	_bx(g, n, _m(g, "plaster", Color(0.93, 0.87, 0.72)), Vector3(0, 1.64, -0.3), Vector3(5.6, 2.2, 1.4))
	_bx(g, n, m, Vector3(0, 2.92, 0.1), Vector3(6.9, 0.36, 2.4))
	_bx(g, n, _m(g, "frieze_red", Color(0.7, 0.16, 0.12)), Vector3(0, 2.84, 0.1), Vector3(6.92, 0.1, 2.42))
	_pr(g, n, _m(g, "roof_tile", TERRACOTTA), Vector3(0, 3.42, 0.1), Vector3(7.0, 0.66, 2.5))
	_pr(g, n, m, Vector3(0, 3.41, 1.33), Vector3(6.8, 0.62, 0.06))
	_sp(g, n, _m(g, "gold", Color(0.95, 0.72, 0.2), {"metal": 0.6, "rough": 0.3}), Vector3(0, 3.8, 0.1), 0.18, Vector3.ONE, 6)


static func _windmill(g: Node3D, pos: Vector3) -> void:
	var n := _n(g, pos)
	_cy(g, n, _m(g, "plaster", Color(0.93, 0.87, 0.72)), Vector3(0, 1.3, 0), 0.55, 0.85, 2.6, 9)
	_cy(g, n, _m(g, "thatch", Color(0.78, 0.64, 0.32)), Vector3(0, 2.95, 0), 0.0, 0.72, 0.75, 9)
	_bx(g, n, _m(g, "door_dark", Color(0.12, 0.08, 0.05)), Vector3(0, 0.35, 0.8), Vector3(0.38, 0.7, 0.08))
	var axle := _n(n, Vector3(0, 2.45, 0.8))
	axle.rotation.x = PI * 0.5
	var rotor := _n(axle, Vector3.ZERO)
	var sail := _m(g, "sail_cloth", Color(0.92, 0.9, 0.84))
	_bx(g, rotor, sail, Vector3(0.85, 0, 0), Vector3(1.5, 0.04, 0.3))
	_bx(g, rotor, sail, Vector3(-0.85, 0, 0), Vector3(1.5, 0.04, 0.3))
	_bx(g, rotor, sail, Vector3(0, 0, 0.85), Vector3(0.3, 0.04, 1.5))
	_bx(g, rotor, sail, Vector3(0, 0, -0.85), Vector3(0.3, 0.04, 1.5))
	_sp(g, rotor, _m(g, "post", WOOD_D), Vector3.ZERO, 0.14, Vector3.ONE, 6)
	_spin(g, axle, rotor)


static func _trebuchet(g: Node3D, pos: Vector3) -> void:
	var n := _n(g, pos, 0.35)
	var w := _m(g, "cart_wood", WOOD)
	var d := _m(g, "post", WOOD_D)
	for s in [-1, 1]:
		_bx(g, n, w, Vector3(0, 0.1, s * 0.5), Vector3(2.4, 0.18, 0.18))
		_bx(g, n, w, Vector3(-0.35, 0.95, s * 0.5), Vector3(0.16, 1.9, 0.16), Vector3(0, 0, -0.35))
		_bx(g, n, w, Vector3(0.35, 0.95, s * 0.5), Vector3(0.16, 1.9, 0.16), Vector3(0, 0, 0.35))
	_cy(g, n, _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45}), Vector3(0, 1.8, 0), 0.06, 0.06, 1.2, 6, Vector3(PI * 0.5, 0, 0))
	_bx(g, n, d, Vector3(-0.6, 2.25, 0), Vector3(2.6, 0.12, 0.12), Vector3(0, 0, -0.35))
	_bx(g, n, _m(g, "castle_stone", Color(0.58, 0.57, 0.55)), Vector3(0.65, 1.3, 0), Vector3(0.55, 0.55, 0.55))


static func _tall_ship(g: Node3D, pos: Vector3) -> void:
	var n := _n(g, pos, 0.0, 0.85)
	var hull := _m(g, "ship_hull", Color(0.36, 0.22, 0.12))
	_bx(g, n, hull, Vector3(0, 0.25, 0), Vector3(1.0, 0.55, 3.2))
	_pr(g, n, hull, Vector3(0, 0.25, 1.95), Vector3(1.0, 0.55, 0.7), Vector3(PI * 0.5, 0, 0))
	_bx(g, n, hull, Vector3(0, 0.75, -1.25), Vector3(1.0, 0.5, 0.75))
	_bx(g, n, _m(g, "ship_stripe", Color(0.85, 0.7, 0.25)), Vector3(0, 0.45, 0), Vector3(1.04, 0.07, 3.22))
	var mast := _m(g, "post", WOOD_D)
	var sail := _m(g, "sail_cloth", Color(0.96, 0.95, 0.9))
	var hs: Array[float] = [3.2, 3.8, 2.8]
	for i in 3:
		var z := 1.0 - i * 1.0
		_cy(g, n, mast, Vector3(0, hs[i] * 0.5, z), 0.05, 0.07, hs[i], 5)
		_bx(g, n, sail, Vector3(0, hs[i] * 0.55, z + 0.08), Vector3(1.5 - i * 0.1, 1.0, 0.05))
		_bx(g, n, sail, Vector3(0, hs[i] * 0.82, z + 0.06), Vector3(1.1, 0.6, 0.05))
	_bx(g, n, _m(g, "flag_navy", Color(0.14, 0.22, 0.52)), Vector3(0.2, 3.95, 0.0), Vector3(0.4, 0.22, 0.02))


static func _dock(g: Node3D, t: Node3D) -> void:
	_bx(g, t, _m(g, "plank", Color(0.5, 0.36, 0.22)), Vector3(0, 0.2, 0), Vector3(1.1, 0.08, 1.4))
	var post := _m(g, "post", WOOD_D)
	for s in [-1, 1]:
		_cy(g, t, post, Vector3(s * 0.48, 0.25, 0.62), 0.07, 0.07, 0.5, 5)
	_barrels(g, _n(t, Vector3(-0.15, 0.24, -0.3), 0.0, 0.6), WOOD, "wood")


static func _pyramid(g: Node3D, pos: Vector3) -> void:
	var n := _n(g, pos)
	var a := _m(g, "ruin_jungle", Color(0.5, 0.52, 0.44))
	var b := _m(g, "ruin_jungle2", Color(0.44, 0.46, 0.38))
	for k in 4:
		var w := 6.0 - k * 1.3
		_bx(g, n, a if k % 2 == 0 else b, Vector3(0, 0.4 + k * 0.8, 0), Vector3(w, 0.8, w * 0.7))
	_bx(g, n, a, Vector3(0, 3.65, 0), Vector3(1.4, 0.9, 1.1))
	_bx(g, n, _m(g, "door_dark", Color(0.12, 0.08, 0.05)), Vector3(0, 3.55, 0.56), Vector3(0.5, 0.6, 0.02))
	_bx(g, n, b, Vector3(0, 1.6, 1.75), Vector3(1.0, 0.1, 2.8), Vector3(0.75, 0, 0))
	var vine := _m(g, "vine", Color(0.18, 0.46, 0.16))
	_bx(g, n, vine, Vector3(-1.9, 0.9, 2.05), Vector3(0.6, 1.4, 0.05))
	_bx(g, n, vine, Vector3(1.4, 1.6, 1.6), Vector3(0.5, 1.2, 0.05))


static func _train(g: Node3D, pos: Vector3) -> void:
	var n := _n(g, pos)
	var steel := _m(g, "rail", Color(0.5, 0.5, 0.52), {"metal": 0.6, "rough": 0.4})
	_bx(g, n, _m(g, "ballast", Color(0.3, 0.27, 0.24)), Vector3(0, 0.02, 0), Vector3(30.0, 0.04, 1.2))
	for s in [-1, 1]:
		_bx(g, n, steel, Vector3(0, 0.07, s * 0.36), Vector3(30.0, 0.07, 0.07))
	# locomotive facing +x
	var loco := _n(n, Vector3(2.2, 0, 0))
	var black := _m(g, "loco_black", Color(0.12, 0.12, 0.13), {"metal": 0.4, "rough": 0.4})
	_bx(g, loco, black, Vector3(0, 0.3, 0), Vector3(3.0, 0.3, 0.9))
	_cy(g, loco, _m(g, "loco_green", Color(0.16, 0.36, 0.22), {"metal": 0.3}), Vector3(0.3, 0.75, 0), 0.4, 0.4, 2.0, 10, Vector3(0, 0, PI * 0.5))
	_bx(g, loco, _m(g, "loco_cab", Color(0.55, 0.16, 0.1)), Vector3(-1.0, 0.95, 0), Vector3(0.9, 1.0, 1.0))
	_bx(g, loco, black, Vector3(-1.0, 1.5, 0), Vector3(1.1, 0.08, 1.15))
	_cy(g, loco, black, Vector3(1.0, 1.35, 0), 0.16, 0.12, 0.5, 8)
	_bx(g, loco, _m(g, "brass", Color(0.8, 0.62, 0.25), {"metal": 0.7, "rough": 0.3}), Vector3(1.32, 0.75, 0), Vector3(0.05, 0.82, 0.82))
	_smoke(g, loco, Vector3(1.0, 1.75, 0), 1.0, Color(0.85, 0.85, 0.86, 0.55))
	# wagons behind it
	var cols := [Color(0.55, 0.2, 0.12), Color(0.24, 0.3, 0.42)]
	for i in 2:
		var c: Color = cols[i]
		var x := -1.4 - i * 2.6
		_bx(g, n, _m(g, "bogie", Color(0.12, 0.12, 0.13)), Vector3(x, 0.24, 0), Vector3(2.2, 0.3, 0.8))
		_bx(g, n, _m(g, "boxcar_" + c.to_html(), c), Vector3(x, 0.82, 0), Vector3(2.3, 0.9, 0.96))


static func _jet(g: Node3D, pos: Vector3) -> void:
	var n := _n(g, pos, PI * 0.5 + 0.3)
	var grey := _m(g, "jet_grey", Color(0.55, 0.58, 0.62), {"metal": 0.4, "rough": 0.4})
	_cap(g, n, grey, Vector3(0, 0.55, 0), 0.32, 3.4, Vector3(PI * 0.5, 0, 0))
	_pr(g, n, grey, Vector3(0, 0.5, -0.2), Vector3(3.0, 2.0, 0.06), Vector3(PI * 0.5, 0, 0))
	_pr(g, n, grey, Vector3(0, 0.95, -1.3), Vector3(0.9, 0.8, 0.06), Vector3(0, PI * 0.5, 0), 0.0)
	_bx(g, n, _m(g, "car_glass", Color(0.2, 0.26, 0.32), {"rough": 0.15}), Vector3(0, 0.82, 0.9), Vector3(0.3, 0.2, 0.7))
	var tire := _m(g, "tire", Color(0.07, 0.07, 0.08))
	for p in [Vector3(0, 0.12, 1.1), Vector3(0.5, 0.12, -0.3), Vector3(-0.5, 0.12, -0.3)]:
		_cy(g, n, tire, p, 0.12, 0.12, 0.1, 8, Vector3(0, 0, PI * 0.5))


static func _tower_block(g: Node3D, pos: Vector3, w: float, h: float, c: Color, antenna: bool) -> void:
	var n := _n(g, pos)
	_bx(g, n, _m(g, "glass_" + c.to_html(), c, {"rough": 0.2, "metal": 0.3}), Vector3(0, h * 0.5, 0), Vector3(w, h, w))
	var band := _m(g, "concrete", CONCRETE)
	var k := 1
	while k * 1.2 < h - 0.3:
		_bx(g, n, band, Vector3(0, k * 1.2, 0), Vector3(w + 0.04, 0.14, w + 0.04))
		k += 2
	_bx(g, n, band, Vector3(0, h + 0.15, 0), Vector3(w * 0.6, 0.3, w * 0.6))
	if antenna:
		_cy(g, n, _m(g, "steel_grey", Color(0.5, 0.52, 0.55), {"metal": 0.5}), Vector3(0, h + 0.8, 0), 0.02, 0.04, 1.0, 4)
		_pulse(g, _sp(g, n, _glow(g, "warn_red", Color(1.0, 0.12, 0.08), 3.0), Vector3(0, h + 1.32, 0), 0.08, Vector3.ONE, 6))


static func _the_core(g: Node3D, pos: Vector3) -> void:
	var n := _n(g, pos)
	var black := _m(g, "core_glass", Color(0.06, 0.05, 0.08), {"metal": 0.7, "rough": 0.15})
	var red := _glow(g, "core_red", Color(1.0, 0.15, 0.08), 3.0)
	_cy(g, n, black, Vector3(0, 0.9, 0), 0.8, 2.2, 1.8, 6)
	for s in [-1, 1]:
		_bx(g, n, red, Vector3(s * 0.85, 0.9, 1.15), Vector3(0.06, 1.7, 0.06), Vector3(0.55, 0, s * -0.45))
	_sp(g, n, black, Vector3(0, 3.0, 0), 1.3, Vector3.ONE, 12)
	var look := Vector3(0, sin(deg_to_rad(54.0)), cos(deg_to_rad(54.0)))   # towards the camera
	var eye := _sp(g, n, _glow(g, "core_eye", Color(1.0, 0.1, 0.05), 4.0), Vector3(0, 3.0, 0) + look * 1.12, 0.55, Vector3(1, 1, 0.4), 10, Vector3(-deg_to_rad(54.0), 0, 0))
	_pulse(g, eye, 0.0)
	_sp(g, n, _glow(g, "core_pupil", Color(1.0, 0.85, 0.6), 3.0), Vector3(0, 3.0, 0) + look * 1.3, 0.16, Vector3(1, 1, 0.5), 8, Vector3(-deg_to_rad(54.0), 0, 0))
	var holder := _n(n, Vector3(0, 3.0, 0))
	var rotor := _n(holder, Vector3.ZERO)
	_tor(g, rotor, _m(g, "core_ring", Color(0.25, 0.22, 0.27), {"metal": 0.7, "rough": 0.3}), Vector3.ZERO, 1.8, 1.96, Vector3(0.35, 0, 0.2), 24)
	_tor(g, rotor, red, Vector3.ZERO, 2.2, 2.27, Vector3(-0.3, 0, -0.25), 24)
	_spin(g, holder, rotor)
	var pm := _m(g, "core_beam", Color(1.0, 0.2, 0.1, 0.25), {"emit": Color(1.0, 0.15, 0.08), "emit_e": 1.5, "unshaded": true})
	_no_shadow(_cy(g, n, pm, Vector3(0, 6.0, 0), 0.25, 0.4, 4.6, 8))


# ================================================================== blockers
## One no-build zone. `n` is already positioned at the zone center; `rad` is its radius.
static func build_blocker(g: Node3D, theme_id: String, kind: String, n: Node3D, rad: float, r: RandomNumberGenerator) -> void:
	var th := theme_id
	match kind:
		"stones":   # stone circle
			for k in 6:
				var a := TAU * k / 6.0 + 0.3
				_standing_stone(g, _n(n, Vector3(cos(a), 0, sin(a)) * rad * 0.72, a), r, r.randf_range(0.9, 1.5))
			_bx(g, n, _m(g, "menhir", Color(0.56, 0.57, 0.55)), Vector3(0, 0.2, 0), Vector3(0.8, 0.4, 0.45), Vector3(0, 0.4, 0))
		"lake":
			if th == "suburb":   # backyard pool: ladder, diving board, float
				var steel := _m(g, "steel_bright", Color(0.85, 0.87, 0.9), {"metal": 0.8, "rough": 0.2})
				for s in [-1, 1]:
					_tor(g, n, steel, Vector3(rad * 0.82, 0.3, s * 0.18), 0.2, 0.24, Vector3(PI * 0.5, 0, 0), 10)
				_bx(g, n, _m(g, "post_white", Color(0.95, 0.95, 0.93)), Vector3(-rad * 0.7, 0.25, 0), Vector3(1.0, 0.06, 0.32))
				_bx(g, n, _m(g, "concrete", CONCRETE), Vector3(-rad * 1.05, 0.12, 0), Vector3(0.3, 0.24, 0.4))
				_tor(g, n, _m(g, "float_pink", Color(1.0, 0.45, 0.65)), Vector3(0.2, 0.06, 0.25), 0.15, 0.3, Vector3.ZERO, 12)
			elif th == "smog":   # oily puddle with a sunken barrel
				_cy(g, n, _m(g, "barrel_rust", Color(0.45, 0.25, 0.15)), Vector3(rad * 0.4, 0.1, -rad * 0.2), 0.22, 0.22, 0.54, 8, Vector3(0.3, 0.5, 1.2))
			else:
				var reed := _m(g, "reed", Color(0.44, 0.54, 0.22))
				for k in 8:
					var a := TAU * k / 8.0 + r.randf() * 0.3
					_cy(g, n, reed, Vector3(cos(a) * rad, 0.3, sin(a) * rad), 0.0, 0.05, r.randf_range(0.5, 0.85), 4,
						Vector3(r.randf_range(-0.2, 0.2), 0, r.randf_range(-0.2, 0.2)))
				if th == "bog":
					var pad := _m(g, "lilypad", Color(0.32, 0.55, 0.2))
					for k in 3:
						var a := r.randf() * TAU
						_cy(g, n, pad, Vector3(cos(a), 0, sin(a)) * rad * 0.45 + Vector3(0, 0.03, 0), 0.2, 0.2, 0.02, 8)
					_dead_tree(g, _n(n, Vector3(rad * 0.3, 0, -rad * 0.3), r.randf() * TAU, 0.8), th)
		"trees":
			for k in 3:
				var a := TAU * k / 3.0 + r.randf() * 0.5
				var t := _n(n, Vector3(cos(a), 0, sin(a)) * rad * 0.42, r.randf() * TAU, r.randf_range(0.85, 1.1))
				match th:
					"highland":
						if k == 1:
							_birch(g, t)
						else:
							_pine(g, t, th)
					"bog": _willow(g, t)
					"olive": _olive(g, t)
					"farmland", "castle": _round_tree(g, t, Color(0.16, 0.38, 0.12), Color(0.22, 0.46, 0.15), "oak", 1.0)
					"darkwood":
						if k == 2:
							_dead_tree(g, t, "darkwood")
						else:
							_pine(g, t, th)
					"jungle":
						if k != 2:
							_jungle_tree(g, t)
						else:
							_fern(g, t)
					"suburb": _round_tree(g, t, Color(0.26, 0.56, 0.18), Color(0.34, 0.64, 0.22), "sub_tree", 0.9)
					"metro":
						if k == 0:
							t.position = Vector3.ZERO
							_cy(g, t, _m(g, "trunk", TRUNK), Vector3(0, 0.55, 0), 0.08, 0.11, 1.1, 6)
							_sp(g, t, _m(g, "sub_tree_a", Color(0.26, 0.56, 0.18)), Vector3(0, 1.55, 0), 0.75, Vector3(1, 0.9, 1), 8)
							_bx(g, n, _m(g, "bench", WOOD), Vector3(0, 0.22, rad * 0.62), Vector3(1.0, 0.08, 0.3))
					_: _pine(g, t, th)
		"slag":
			for k in 3:
				var a := TAU * k / 3.0 + r.randf()
				_slag_heap(g, _n(n, Vector3(cos(a), 0, sin(a)) * rad * 0.35, r.randf() * TAU, rad * (0.85 if k == 0 else 0.55)), r)
		"lava":
			var pool := _cy(g, n, _m(g, "pool_lava", Color(1, 0.55, 0.15, 0.45), {"emit": Color(1, 0.42, 0.05), "emit_e": 1.0, "unshaded": true}),
				Vector3(0, 0.04, 0), rad * 0.85, rad * 0.85, 0.04, 20)
			_no_shadow(pool)
			var crust := _m(g, "crust", Color(0.08, 0.06, 0.06))
			for k in 7:
				var a := TAU * k / 7.0 + r.randf() * 0.3
				_sp(g, n, crust, Vector3(cos(a) * rad, 0.08, sin(a) * rad), r.randf_range(0.18, 0.3), Vector3(1.3, 0.6, 1), 6)
			var ll := OmniLight3D.new()
			ll.light_color = Color(1, 0.45, 0.15)
			ll.light_energy = 0.9
			ll.omni_range = rad * 2.2
			ll.position = Vector3(0, 0.8, 0)
			n.add_child(ll)
			g.effects.append({"node": n, "life": INF, "t": r.randf() * 5.0, "kind": "lava", "pool": pool, "light": ll})
		"ruins":
			if th in ["olive", "coast", "acropolis"]:
				for k in 4:
					var a := TAU * k / 4.0 + 0.4
					_column(g, _n(n, Vector3(cos(a), 0, sin(a)) * rad * 0.6, a), r.randf_range(0.6, 1.9))
				_bx(g, n, _m(g, "marble", MARBLE), Vector3(0.1, 0.18, -0.1), Vector3(1.0, 0.36, 0.5), Vector3(0, 0.6, 0))
			else:
				_ruin_arch(g, _n(n, Vector3.ZERO, r.randf() * TAU, rad * 0.9), th == "darkwood")
				if th == "darkwood":
					_mushrooms(g, _n(n, Vector3(rad * 0.5, 0, rad * 0.3)), r)
				else:
					_fern(g, _n(n, Vector3(rad * 0.5, 0, rad * 0.35)))
		"statue":
			var m := _m(g, "marble", MARBLE)
			_cy(g, n, _m(g, "plinth", Color(0.8, 0.77, 0.7)), Vector3(0, 0.3, 0), rad * 0.5, rad * 0.55, 0.6, 10)
			_cy(g, n, m, Vector3(0, 1.25, 0), 0.2, 0.32, 1.3, 8)
			_sp(g, n, m, Vector3(0, 2.05, 0), 0.19, Vector3.ONE, 8)
			_sp(g, n, _m(g, "bronze", Color(0.66, 0.42, 0.16), {"metal": 0.6, "rough": 0.4}), Vector3(0, 2.18, 0), 0.2, Vector3(1, 0.6, 1.2), 7)
			_cy(g, n, _m(g, "bronze", Color(0.66, 0.42, 0.16), {"metal": 0.6, "rough": 0.4}), Vector3(0.36, 1.6, 0), 0.025, 0.025, 2.2, 4, Vector3(0, 0, 0.12))
			_cy(g, n, _m(g, "bronze", Color(0.66, 0.42, 0.16), {"metal": 0.6, "rough": 0.4}), Vector3(-0.32, 1.25, 0.12), 0.32, 0.32, 0.06, 10, Vector3(0, 0, PI * 0.5))
		"rocks":
			var e: Array = ENV.get(th, ENV["highland"])
			var rock := _m(g, "rock_" + th, e[5])
			for k in 4:
				var off := Vector2(r.randf_range(-0.55, 0.55), r.randf_range(-0.55, 0.55)) * rad
				var sz := r.randf_range(0.35, 0.65) * rad
				_sp(g, n, rock, Vector3(off.x, sz * 0.35, off.y), sz, Vector3(1.1, 0.8, 1), 6, Vector3(0, r.randf() * 3, 0))
			if th == "castle":   # rubble with a broken cart wheel
				_cy(g, n, _m(g, "post", WOOD_D), Vector3(rad * 0.5, 0.05, rad * 0.4), 0.32, 0.32, 0.08, 8)
		"building":
			match th:
				"farmland":   # red barn
					var t := _n(n, Vector3.ZERO, r.randf_range(-0.3, 0.3))
					_bx(g, t, _m(g, "barn_red", Color(0.66, 0.18, 0.12)), Vector3(0, 0.6, 0), Vector3(rad * 1.3, 1.2, rad * 1.1))
					_pr(g, t, _m(g, "slate", Color(0.28, 0.28, 0.32)), Vector3(0, 1.55, 0), Vector3(rad * 1.45, 0.7, rad * 1.2))
					_bx(g, t, _m(g, "post_white", Color(0.95, 0.95, 0.93)), Vector3(0, 0.45, rad * 0.56), Vector3(0.7, 0.9, 0.03))
					_bx(g, t, _m(g, "door_dark", Color(0.12, 0.08, 0.05)), Vector3(0, 0.42, rad * 0.565), Vector3(0.58, 0.8, 0.03))
				"factory":   # brick shed with a short chimney
					_bx(g, n, _m(g, "brick", BRICK), Vector3(0, 0.6, 0), Vector3(rad * 1.3, 1.2, rad * 1.3))
					_pr(g, n, _m(g, "slate", Color(0.28, 0.28, 0.32)), Vector3(0, 1.45, 0), Vector3(rad * 1.35, 0.5, rad * 1.35), Vector3.ZERO, 0.0)
					_cy(g, n, _m(g, "brick_dark", BRICK.darkened(0.3)), Vector3(rad * 0.4, 1.7, -rad * 0.4), 0.15, 0.2, 1.4, 8)
					_bx(g, n, _glow(g, "furnace_win", Color(1.0, 0.6, 0.2), 1.8), Vector3(0, 0.8, rad * 0.66), Vector3(rad * 1.0, 0.2, 0.02))
				"smog":   # sooty tenement
					var c := Color(0.42, 0.3, 0.26)
					_bx(g, n, _m(g, "terrace_" + c.to_html(), c), Vector3(0, 0.9, 0), Vector3(rad * 1.3, 1.8, rad * 1.2))
					_bx(g, n, _m(g, "slate", Color(0.28, 0.28, 0.32)), Vector3(0, 1.84, 0), Vector3(rad * 1.36, 0.1, rad * 1.26))
					var win := _glow(g, "window_warm", Color(1.0, 0.75, 0.35), 1.6)
					_bx(g, n, win, Vector3(0, 0.7, rad * 0.61), Vector3(rad * 1.0, 0.14, 0.02))
					_bx(g, n, win, Vector3(0, 1.3, rad * 0.61), Vector3(rad * 1.0, 0.14, 0.02))
					_bx(g, n, _m(g, "brick_dark", BRICK.darkened(0.3)), Vector3(rad * 0.4, 2.1, 0), Vector3(0.25, 0.5, 0.3))
				"suburb":
					_house(g, _n(n, Vector3.ZERO, r.randf_range(-0.3, 0.3), rad * 0.85), r)
				"metro":   # low office block
					var t := _n(n, Vector3.ZERO)
					_bx(g, t, _m(g, "glass_office", Color(0.42, 0.55, 0.68), {"rough": 0.2, "metal": 0.3}), Vector3(0, 1.0, 0), Vector3(rad * 1.3, 2.0, rad * 1.3))
					_bx(g, t, _m(g, "concrete", CONCRETE), Vector3(0, 1.0, 0), Vector3(rad * 1.34, 0.14, rad * 1.34))
					_bx(g, t, _m(g, "concrete", CONCRETE), Vector3(0, 2.05, 0), Vector3(rad * 1.36, 0.12, rad * 1.36))
					_bx(g, t, _m(g, "unit_grey", Color(0.5, 0.53, 0.57), {"metal": 0.4}), Vector3(rad * 0.3, 2.3, -rad * 0.2), Vector3(0.5, 0.36, 0.5))
				_:
					_cottage(g, _n(n, Vector3.ZERO, r.randf() * TAU, rad * 0.8))
		"tents":
			_tent_med(g, _n(n, Vector3(-rad * 0.35, 0, -rad * 0.2), 0.0, rad * 0.75), r)
			_tent_med(g, _n(n, Vector3(rad * 0.4, 0, rad * 0.3), 0.0, rad * 0.6), r)
			_banner(g, _n(n, Vector3(rad * 0.5, 0, -rad * 0.5)), Color(0.75, 0.12, 0.1))
			_barrels(g, _n(n, Vector3(-rad * 0.45, 0, rad * 0.5), 0.0, 0.7), WOOD, "wood")
		"crates":
			_crates(g, _n(n, Vector3(-rad * 0.25, 0, -rad * 0.15), r.randf() * TAU, 1.1), th, r)
			if th == "military":
				_barrels(g, _n(n, Vector3(rad * 0.4, 0, rad * 0.35), r.randf() * TAU, 1.0), OLIVE_DRAB, "drum0")
				_sandbags(g, _n(n, Vector3(0, 0, rad * 0.75)))
			else:
				_barrels(g, _n(n, Vector3(rad * 0.4, 0, rad * 0.35), r.randf() * TAU, 1.0), WOOD if th != "fortress" else Color(0.24, 0.17, 0.11), "wood" if th != "fortress" else "keg")
				if th == "harbor":
					_anchor(g, _n(n, Vector3(rad * 0.25, 0, -rad * 0.55), 0.8))
				else:
					_crates(g, _n(n, Vector3(rad * 0.45, 0, -rad * 0.4), r.randf() * TAU, 0.8), th, r)
		"crater":   # dirt clods and debris around the rim
			var dirt := _m(g, "clod", Color(0.42, 0.34, 0.24))
			for k in 6:
				var a := TAU * k / 6.0 + r.randf() * 0.4
				_sp(g, n, dirt, Vector3(cos(a) * rad * 0.95, 0.05, sin(a) * rad * 0.95), r.randf_range(0.18, 0.3), Vector3(1.3, 0.55, 1), 6)
			if th == "military":
				_bx(g, n, _m(g, "steel_dark", Color(0.3, 0.32, 0.34), {"metal": 0.5}), Vector3(rad * 0.2, 0.15, -rad * 0.1), Vector3(0.7, 0.08, 0.3), Vector3(0.4, 0.7, 0.3))
				_smoke(g, n, Vector3(0, 0.2, 0), 0.8, Color(0.3, 0.3, 0.3, 0.45))
			else:
				var ball := _m(g, "cannon_iron", Color(0.12, 0.12, 0.13), {"metal": 0.6, "rough": 0.35})
				_sp(g, n, ball, Vector3(rad * 0.15, 0.14, rad * 0.1), 0.15, Vector3.ONE, 8)
				_bx(g, n, _m(g, "cart_wood", WOOD), Vector3(-rad * 0.3, 0.06, -rad * 0.2), Vector3(0.8, 0.08, 0.14), Vector3(0, 0.8, 0.1))
		"coal":
			_coal(g, n, rad * 1.05)
			var iron := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
			_bx(g, n, iron, Vector3(-rad * 0.6, 0.45, rad * 0.5), Vector3(0.05, 0.9, 0.05), Vector3(0.3, 0, 0.3))
			_bx(g, n, iron, Vector3(-rad * 0.66, 0.06, rad * 0.62), Vector3(0.22, 0.04, 0.26), Vector3(0, 0.3, 0))
		"machine":
			match th:
				"factory":   # steam engine
					var t := _n(n, Vector3.ZERO, r.randf() * TAU)
					_cy(g, t, _m(g, "loco_green", Color(0.16, 0.36, 0.22), {"metal": 0.3}), Vector3(0, 0.6, 0), 0.5, 0.5, rad * 1.3, 10, Vector3(0, 0, PI * 0.5))
					_bx(g, t, _m(g, "bogie", Color(0.12, 0.12, 0.13)), Vector3(0, 0.15, 0), Vector3(rad * 1.4, 0.3, 1.0))
					_cy(g, t, _m(g, "brass", Color(0.8, 0.62, 0.25), {"metal": 0.7, "rough": 0.3}), Vector3(-rad * 0.3, 1.25, 0), 0.12, 0.14, 0.6, 8)
					_gear(g, _n(t, Vector3(rad * 0.6, 0, 0.4), 0.0, 0.9))
					_smoke(g, t, Vector3(-rad * 0.3, 1.6, 0), 0.6, Color(0.9, 0.9, 0.92, 0.5))
				"military":   # generator trailer with a spinning radar
					var t := _n(n, Vector3.ZERO, r.randf() * TAU)
					_bx(g, t, _m(g, "olive_drab", OLIVE_DRAB), Vector3(0, 0.45, 0), Vector3(rad * 1.2, 0.7, 0.9))
					var tire := _m(g, "tire", Color(0.07, 0.07, 0.08))
					_cy(g, t, tire, Vector3(0, 0.18, 0), 0.18, 0.18, 1.0, 8, Vector3(PI * 0.5, 0, 0))
					_radar(g, _n(t, Vector3(rad * 0.3, 0.8, 0), 0.0, 0.8), 1.0)
					_bx(g, t, _m(g, "hazard", Color(0.95, 0.75, 0.1)), Vector3(-rad * 0.3, 0.6, 0.46), Vector3(0.6, 0.1, 0.02))
				"lab":   # white machine with a glowing core and an arm
					_bx(g, n, _m(g, "lab_white", WHITE_PANEL), Vector3(0, 0.5, 0), Vector3(rad * 1.2, 1.0, rad * 1.0))
					_bx(g, n, _glow(g, "cyan_strip", CYAN, 1.8), Vector3(0, 0.75, rad * 0.51), Vector3(rad * 1.0, 0.06, 0.02))
					var core := _cy(g, n, _glow(g, "lab_core", Color(0.3, 0.95, 1.0), 2.5), Vector3(0, 1.25, 0), 0.25, 0.25, 0.5, 10)
					_pulse(g, core, 0.0)
					_robot_arm(g, _n(n, Vector3(rad * 0.4, 1.0, -rad * 0.2), 2.5, 0.6))
				"server", "cooling":   # chiller block with fans
					var c := Color(0.5, 0.53, 0.57) if th == "cooling" else Color(0.14, 0.15, 0.18)
					_bx(g, n, _m(g, "chiller_" + th, c, {"metal": 0.4}), Vector3(0, 0.6, 0), Vector3(rad * 1.3, 1.2, rad * 1.0))
					for s in [-1, 1]:
						var f := _n(n, Vector3(s * rad * 0.32, 1.2, 0), 0.0, 0.6)
						_fan(g, f)
					var blue := _glow(g, "led_blue", Color(0.25, 0.55, 1.0), 2.4)
					_bx(g, n, blue, Vector3(0, 0.4, rad * 0.51), Vector3(rad * 1.0, 0.05, 0.02))
				_:
					_bx(g, n, _m(g, "unit_grey", Color(0.5, 0.53, 0.57), {"metal": 0.4}), Vector3(0, 0.5, 0), Vector3(rad, 1.0, rad))
		"pylon":
			_neon_pylon(g, n, r, 1.25)
			var c := CYAN if r.randf() < 0.5 else MAGENTA
			_tor(g, n, _glow(g, "neon_" + c.to_html(), c, 2.4), Vector3(0, 0.08, 0), rad * 0.55, rad * 0.62, Vector3.ZERO, 20)
		"pit":   # a shaft of light rising from the hole
			_no_shadow(_cy(g, n, _m(g, "pit_beam", Color(1.0, 0.3, 0.9, 0.18), {"emit": MAGENTA, "emit_e": 1.0, "unshaded": true}),
				Vector3(0, 0.8, 0), rad * 0.75, rad * 0.85, 1.6, 16))
		"dish":
			_dish(g, _n(n, Vector3.ZERO, r.randf_range(-0.6, 0.6), rad * 1.0), 1.0)
		"panels":
			for k in 2:
				_solar_row(g, _n(n, Vector3(0, 0, (k - 0.5) * rad * 0.9), 0.0, rad * 0.7), 2)
		"tank":
			_tube(g, n, rad * 1.1)
		"rack":
			for k in 2:
				_rack_row(g, _n(n, Vector3(0, 0, (k - 0.5) * rad * 1.0), 0.0, 0.85), 3, r)
		"ice":
			_ice(g, n, r, rad * 1.1)
			_ice(g, _n(n, Vector3(rad * 0.45, 0, rad * 0.3), 1.0, 0.6), r, 1.0)
		"pillar":
			_energy_pillar(g, n, rad * 0.9)
		"wreck":
			_broken_robot(g, _n(n, Vector3(-rad * 0.2, 0, -rad * 0.1), r.randf() * TAU, 1.1), r)
			_broken_robot(g, _n(n, Vector3(rad * 0.4, 0, rad * 0.35), r.randf() * TAU, 0.8), r)
			_smoke(g, n, Vector3(0, 0.3, 0), 0.7, Color(0.25, 0.2, 0.22, 0.5))
		_:
			var rock := _m(g, "rock_" + th, env(th).rock)
			for k in 4:
				var off := Vector2(r.randf_range(-0.6, 0.6), r.randf_range(-0.6, 0.6)) * rad
				var sz := r.randf_range(0.35, 0.7) * rad
				_sp(g, n, rock, Vector3(off.x, sz * 0.4, off.y), sz, Vector3(1.1, 0.8, 1), 6, Vector3(0, r.randf() * 3, 0))


# ================================================================== bases
## The humans' base where the road ends (p = road end point, robots arrive from -x).
## base_id: hillfort | temple | castle | fort | factory | bunker | lab | camp
static func build_base(g: Node3D, base_id: String, p: Vector2) -> void:
	var n := Node3D.new()
	n.position = Vector3(p.x, 0, p.y)
	g.add_child(n)
	match base_id:
		"hillfort": _base_hillfort(g, n)
		"temple": _base_temple(g, n)
		"castle": _base_castle(g, n)
		"fort": _base_fort(g, n)
		"factory": _base_factory(g, n)
		"bunker": _base_bunker(g, n)
		"lab": _base_lab(g, n)
		"camp": _base_camp(g, n)
		_: _base_hillfort(g, n)


static func _base_hillfort(g: Node3D, n: Node3D) -> void:
	var berm := _m(g, "berm", Color(0.4, 0.4, 0.22))
	var logm := _m(g, "palisade", Color(0.5, 0.36, 0.2))
	for s in [-1, 1]:
		_sp(g, n, berm, Vector3(1.0, 0.0, s * 3.0), 1.0, Vector3(0.9, 0.45, 2.1), 8)
		for i in 9:
			var hh := 1.6 + (i % 3) * 0.15
			_cy(g, n, logm, Vector3(0.7 + (i % 2) * 0.05, hh * 0.5, s * (1.2 + i * 0.42)), 0.1, 0.17, hh, 6)
			_cy(g, n, logm, Vector3(0.7 + (i % 2) * 0.05, hh + 0.15, s * (1.2 + i * 0.42)), 0.0, 0.1, 0.3, 6)
	var post := _m(g, "post", WOOD_D)
	for s in [-1, 1]:
		_cy(g, n, post, Vector3(0.7, 1.15, s * 0.95), 0.14, 0.16, 2.3, 6)
		_bx(g, n, logm, Vector3(1.05, 0.7, s * 0.6), Vector3(0.7, 1.3, 0.08), Vector3(0, s * 0.9, 0))
	_bx(g, n, post, Vector3(0.7, 2.25, 0), Vector3(0.28, 0.24, 2.3))
	_bx(g, n, _m(g, "woad_blue", Color(0.2, 0.34, 0.7)), Vector3(0.52, 1.75, 0), Vector3(0.04, 0.7, 0.5))
	_sp(g, n, _m(g, "skull", Color(0.92, 0.9, 0.84)), Vector3(0.7, 2.48, 0), 0.13, Vector3.ONE, 6)
	_roundhouse(g, _n(n, Vector3(3.3, 0, -2.4), 0.5, 1.3), false)
	_roundhouse(g, _n(n, Vector3(4.0, 0, 2.1), 1.9, 1.1), false)
	var fire := Vector3(2.2, 0, 0.1)
	var stone := _m(g, "stone_grey", Color(0.5, 0.49, 0.47))
	for k in 5:
		var a := TAU * k / 5.0
		_sp(g, n, stone, fire + Vector3(cos(a) * 0.42, 0.05, sin(a) * 0.42), 0.12, Vector3(1, 0.6, 1), 5)
	_flame(g, n, fire, 0.9, 1.6)
	_banner(g, _n(n, Vector3(1.6, 0, -1.4)), Color(0.2, 0.42, 0.25))


static func _base_temple(g: Node3D, n: Node3D) -> void:
	var m := _m(g, "marble", MARBLE)
	for k in 3:
		_bx(g, n, m, Vector3(3.0, 0.1 + k * 0.2, 0), Vector3(4.2 - k * 0.3, 0.2, 5.4 - k * 0.3))
	for i in 4:
		var z := -1.8 + i * 1.2
		_cy(g, n, m, Vector3(1.5, 1.7, z), 0.2, 0.24, 2.2, 9)
		_bx(g, n, m, Vector3(1.5, 2.86, z), Vector3(0.5, 0.14, 0.5))
	for s in [-1, 1]:
		for x in [2.9, 4.3]:
			_cy(g, n, m, Vector3(x, 1.7, s * 2.1), 0.2, 0.24, 2.2, 9)
	_bx(g, n, _m(g, "plaster", Color(0.93, 0.87, 0.72)), Vector3(3.7, 1.7, 0), Vector3(2.2, 2.2, 3.0))
	_bx(g, n, m, Vector3(3.0, 3.1, 0), Vector3(3.8, 0.36, 4.8))
	_bx(g, n, _m(g, "frieze_red", Color(0.7, 0.16, 0.12)), Vector3(3.0, 2.98, 0), Vector3(3.82, 0.1, 4.82))
	_pr(g, n, _m(g, "roof_tile", TERRACOTTA), Vector3(3.0, 3.72, 0), Vector3(4.9, 0.9, 4.0), Vector3(0, PI * 0.5, 0))
	_pr(g, n, m, Vector3(1.02, 3.71, 0), Vector3(4.7, 0.86, 0.06), Vector3(0, PI * 0.5, 0))
	_sp(g, n, _m(g, "gold", Color(0.95, 0.72, 0.2), {"metal": 0.6, "rough": 0.3}), Vector3(1.05, 4.25, 0), 0.2, Vector3.ONE, 6)
	var crimson := _m(g, "banner_crimson", Color(0.72, 0.1, 0.12))
	for s in [-1, 1]:
		_bx(g, n, crimson, Vector3(1.32, 2.1, s * 1.2), Vector3(0.03, 1.2, 0.5))
	_brazier(g, _n(n, Vector3(0.5, 0, -2.4)), 1.4)
	_brazier(g, _n(n, Vector3(0.5, 0, 2.4)), 0.0)
	_cypress(g, _n(n, Vector3(2.0, 0, -4.4), 0.0, 1.1))
	_cypress(g, _n(n, Vector3(2.0, 0, 4.4), 0.0, 1.1))


static func _base_castle(g: Node3D, n: Node3D) -> void:
	var stone := _m(g, "castle_stone", Color(0.58, 0.57, 0.55))
	var stone2 := _m(g, "castle_stone2", Color(0.66, 0.65, 0.62))
	var blue := _m(g, "roof_blue", Color(0.18, 0.28, 0.65))
	var red := _m(g, "banner_red", Color(0.75, 0.12, 0.1))
	var gold := _m(g, "gold", Color(0.95, 0.72, 0.2), {"metal": 0.6, "rough": 0.3})
	for s in [-1, 1]:
		_bx(g, n, stone, Vector3(1.3, 0.9, s * 3.3), Vector3(0.9, 1.8, 3.0))
		for i in 4:
			_bx(g, n, stone, Vector3(1.3, 1.95, s * (2.1 + i * 0.75)), Vector3(0.9, 0.3, 0.32))
		_cy(g, n, stone2, Vector3(1.0, 1.45, s * 1.5), 0.82, 0.92, 2.9, 10)
		_cy(g, n, blue, Vector3(1.0, 3.5, s * 1.5), 0.0, 1.0, 1.3, 10)
		_sp(g, n, gold, Vector3(1.0, 4.2, s * 1.5), 0.1, Vector3.ONE, 6)
		_bx(g, n, red, Vector3(0.16, 1.85, s * 1.5), Vector3(0.03, 1.0, 0.5))
		_bx(g, n, gold, Vector3(0.15, 1.85, s * 1.5), Vector3(0.03, 0.12, 0.52))
		_cy(g, n, stone2, Vector3(1.3, 1.2, s * 4.9), 0.5, 0.55, 2.4, 8)
		_cy(g, n, blue, Vector3(1.3, 2.75, s * 4.9), 0.0, 0.62, 0.8, 8)
	_bx(g, n, stone, Vector3(1.2, 1.85, 0), Vector3(1.0, 0.9, 1.6))
	for i in 3:
		_bx(g, n, stone, Vector3(1.2, 2.45, -0.55 + i * 0.55), Vector3(1.0, 0.3, 0.3))
	_bx(g, n, _m(g, "door_dark", Color(0.12, 0.08, 0.05)), Vector3(0.7, 0.7, 0), Vector3(0.06, 1.4, 1.1))
	_bx(g, n, _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45}), Vector3(0.68, 1.25, 0), Vector3(0.06, 0.3, 1.1))
	# the keep
	_bx(g, n, stone2, Vector3(4.2, 1.9, 0), Vector3(2.4, 3.8, 2.4))
	for k in 4:
		var a := TAU * k / 4.0 + PI * 0.25
		_bx(g, n, stone2, Vector3(4.2 + cos(a) * 1.0, 3.95, sin(a) * 1.0), Vector3(0.45, 0.4, 0.45))
	_banner(g, _n(n, Vector3(4.2, 3.8, 0)), Color(0.18, 0.28, 0.65))
	var iron2 := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
	for s in [-1, 1]:
		_bx(g, n, iron2, Vector3(0.32, 0.82, s * 0.85), Vector3(0.2, 0.06, 0.06))
	_flame(g, n, Vector3(0.25, 0.9, -0.85), 0.35, 1.2)
	_flame(g, n, Vector3(0.25, 0.9, 0.85), 0.35, 0.0)


static func _base_fort(g: Node3D, n: Node3D) -> void:
	var wall := _m(g, "fort_stone", Color(0.66, 0.6, 0.46))
	var grass := _m(g, "fort_grass", Color(0.36, 0.5, 0.22))
	for s in [-1, 1]:
		_bx(g, n, wall, Vector3(1.6, 0.6, s * 1.5), Vector3(0.9, 1.2, 1.4))
		_bx(g, n, wall, Vector3(1.8, 0.6, s * 3.4), Vector3(2.1, 1.2, 2.1), Vector3(0, PI * 0.25, 0))
		_bx(g, n, grass, Vector3(1.8, 1.22, s * 3.4), Vector3(1.8, 0.06, 1.8), Vector3(0, PI * 0.25, 0))
		_cannon(g, _n(n, Vector3(1.0, 1.25, s * 3.4), -PI * 0.5 + s * 0.25, 0.95))
		_bx(g, n, wall, Vector3(1.6, 1.38, s * 1.5), Vector3(0.9, 0.36, 0.3))
	_bx(g, n, wall, Vector3(1.75, 1.5, 0), Vector3(0.6, 0.6, 1.8))
	_bx(g, n, _m(g, "door_dark", Color(0.12, 0.08, 0.05)), Vector3(1.4, 0.6, 0), Vector3(0.06, 1.2, 1.0))
	_flag(g, _n(n, Vector3(3.4, 0, 0), 0.0, 1.4), Color(0.14, 0.22, 0.52))
	var roof := _m(g, "roof_tile", TERRACOTTA)
	_bx(g, n, _m(g, "plaster", Color(0.93, 0.87, 0.72)), Vector3(4.4, 0.5, -1.7), Vector3(1.4, 1.0, 2.0))
	_pr(g, n, roof, Vector3(4.4, 1.3, -1.7), Vector3(1.6, 0.6, 2.1))
	_bx(g, n, wall, Vector3(4.3, 0.45, 2.0), Vector3(1.2, 0.9, 1.2))
	_pr(g, n, roof, Vector3(4.3, 1.1, 2.0), Vector3(1.3, 0.4, 1.3))
	_barrels(g, _n(n, Vector3(2.9, 0, 1.4), 0.0, 0.8), Color(0.24, 0.17, 0.11), "keg")
	var ball := _m(g, "cannon_iron", Color(0.12, 0.12, 0.13), {"metal": 0.6, "rough": 0.35})
	for p in [Vector3(2.8, 0.13, -0.9), Vector3(3.06, 0.13, -0.9), Vector3(2.93, 0.33, -0.9)]:
		_sp(g, n, ball, p, 0.13, Vector3.ONE, 7)


static func _base_factory(g: Node3D, n: Node3D) -> void:
	var brick := _m(g, "brick", BRICK)
	_bx(g, n, brick, Vector3(3.3, 1.0, 0), Vector3(3.6, 2.0, 5.2))
	var slate := _m(g, "slate", Color(0.28, 0.28, 0.32))
	for i in 3:
		_pr(g, n, slate, Vector3(2.1 + i * 1.2, 2.3, 0), Vector3(1.2, 0.6, 5.2), Vector3.ZERO, 0.0)
	_bx(g, n, _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45}), Vector3(1.48, 0.75, 0), Vector3(0.06, 1.5, 1.8))
	var glow := _glow(g, "furnace_win", Color(1.0, 0.6, 0.2), 1.8)
	for s in [-1, 1]:
		_bx(g, n, glow, Vector3(1.48, 1.45, s * 1.75), Vector3(0.04, 0.5, 1.1))
	var dark := _m(g, "brick_dark", BRICK.darkened(0.3))
	var iron := _m(g, "iron", IRON, {"metal": 0.5, "rough": 0.45})
	for i in 3:
		var p := Vector3(3.2 + (i % 2) * 1.1, 0, -1.8 + i * 1.8)
		_cy(g, n, dark, p + Vector3(0, 2.2, 0), 0.26, 0.36, 4.4, 8)
		_cy(g, n, iron, p + Vector3(0, 4.4, 0), 0.32, 0.32, 0.14, 8)
		if i != 1:
			_smoke(g, n, p + Vector3(0, 4.7, 0), 1.2, Color(0.36, 0.34, 0.33, 0.55))
	_cy(g, n, _m(g, "pipe_factory", Color(0.72, 0.42, 0.22), {"metal": 0.6, "rough": 0.35}), Vector3(1.55, 1.9, 0), 0.1, 0.1, 5.0, 8, Vector3(PI * 0.5, 0, 0))
	_coal(g, _n(n, Vector3(0.9, 0, 3.2), 0.0, 0.8), 1.0)
	_light(n, Vector3(0.6, 1.2, 0), Color(1.0, 0.6, 0.25), 1.2, 3.5)


static func _base_bunker(g: Node3D, n: Node3D) -> void:
	var bag := _m(g, "sandbag", Color(0.72, 0.64, 0.46))
	for s in [-1, 1]:
		for i in 3:
			_cap(g, n, bag, Vector3(0.45, 0.16, s * (1.5 + i * 1.1)), 0.17, 1.2, Vector3(PI * 0.5, 0, 0))
		for i in 2:
			_cap(g, n, bag, Vector3(0.45, 0.44, s * (2.05 + i * 1.1)), 0.17, 1.2, Vector3(PI * 0.5, 0, 0))
	var con := _m(g, "concrete", CONCRETE)
	_bx(g, n, con, Vector3(3.0, 0.75, 0), Vector3(3.0, 1.5, 4.2))
	_bx(g, n, con, Vector3(3.0, 1.62, 0), Vector3(3.4, 0.26, 4.6))
	_pr(g, n, con, Vector3(1.2, 0.5, 0), Vector3(0.7, 1.0, 4.2), Vector3.ZERO, 1.0)
	_bx(g, n, _m(g, "slit", Color(0.05, 0.05, 0.06)), Vector3(1.49, 1.1, 0), Vector3(0.04, 0.2, 3.0))
	_bx(g, n, _m(g, "hazard", Color(0.95, 0.75, 0.1)), Vector3(1.5, 0.55, 1.5), Vector3(0.04, 1.1, 0.9))
	_bx(g, n, _m(g, "hangar_door", Color(0.2, 0.21, 0.22)), Vector3(1.53, 0.5, 1.5), Vector3(0.04, 0.95, 0.72))
	_radar(g, _n(n, Vector3(3.6, 1.75, 1.0)), 1.1)
	_mast(g, _n(n, Vector3(2.4, 1.75, -1.4)), 2.2)
	_bx(g, n, _m(g, "camo", OLIVE_DRAB), Vector3(3.6, 1.82, -0.6), Vector3(1.6, 0.12, 1.6))
	_crates(g, _n(n, Vector3(1.0, 0, -2.6 + 0.0), 0.3, 0.9), "military", _rng(3))
	_jeep(g, _n(n, Vector3(5.2, 0, 2.6), 0.4))


static func _base_lab(g: Node3D, n: Node3D) -> void:
	var white := _m(g, "lab_white", WHITE_PANEL)
	var cyan := _glow(g, "cyan_strip", CYAN, 1.8)
	_bx(g, n, _m(g, "carbon", Color(0.08, 0.08, 0.1), {"metal": 0.4, "rough": 0.4}), Vector3(3.0, 0.06, 0), Vector3(5.0, 0.12, 6.4))
	_bx(g, n, white, Vector3(1.9, 0.85, 0), Vector3(1.6, 1.7, 3.8))
	_bx(g, n, cyan, Vector3(1.9, 1.3, 0), Vector3(1.62, 0.07, 3.82))
	_bx(g, n, _glow(g, "lab_door", Color(0.5, 0.95, 1.0), 1.2), Vector3(1.09, 0.55, 0), Vector3(0.03, 1.1, 1.0))
	_cy(g, n, white, Vector3(4.0, 1.15, 0), 2.0, 2.1, 2.3, 14)
	_cy(g, n, cyan, Vector3(4.0, 1.7, 0), 2.03, 2.03, 0.08, 14)
	_cy(g, n, _glow(g, "magenta_strip", MAGENTA, 1.8), Vector3(4.0, 0.5, 0), 2.11, 2.11, 0.06, 14)
	_no_shadow(_sp(g, n, _m(g, "glass", Color(0.8, 0.95, 1.0, 0.25), {"rough": 0.05, "metal": 0.2}), Vector3(4.0, 2.3, 0), 1.6, Vector3(1, 0.55, 1), 12))
	_dish(g, _n(n, Vector3(1.9, 1.7, -1.2), -0.6, 0.7), 1.0)
	var holder := _n(n, Vector3(4.0, 3.4, 0))
	var rotor := _n(holder, Vector3.ZERO)
	_no_shadow(_bx(g, rotor, _m(g, "holo_" + CYAN.to_html(), Color(CYAN.r, CYAN.g, CYAN.b, 0.35), {"emit": CYAN, "emit_e": 1.2, "unshaded": true}),
		Vector3.ZERO, Vector3(0.5, 0.5, 0.5), Vector3(0.62, 0, 0.62)))
	_spin(g, holder, rotor)
	for s in [-1, 1]:
		_bx(g, n, white, Vector3(0.5, 0.7, s * 1.3), Vector3(0.3, 1.4, 0.3))
		_bx(g, n, cyan, Vector3(0.34, 0.7, s * 1.3), Vector3(0.03, 1.2, 0.08))


static func _base_camp(g: Node3D, n: Node3D) -> void:
	var orange := _m(g, "scrap_orange", ORANGE_PAINT, {"metal": 0.3, "rough": 0.6})
	var scrap := _m(g, "scrap_grey", Color(0.42, 0.44, 0.46), {"metal": 0.5, "rough": 0.5})
	var tire := _m(g, "tire", Color(0.07, 0.07, 0.08))
	for s in [-1, 1]:
		for i in 3:
			var z: float = s * (1.3 + i * 1.15)
			_bx(g, n, orange if (i + (1 if s > 0 else 0)) % 2 == 0 else scrap, Vector3(0.55 + (i % 2) * 0.2, 0.55, z), Vector3(0.12, 1.1, 1.2), Vector3(0, 0.25 * s * (1 - i), 0.12 * (i - 1)))
		_tor(g, n, tire, Vector3(0.9, 0.12, s * 4.6), 0.14, 0.32, Vector3.ZERO, 12)
		_tor(g, n, tire, Vector3(0.9, 0.3, s * 4.6), 0.14, 0.32, Vector3.ZERO, 12)
		_bx(g, n, scrap, Vector3(0.9, 0.3, s * 0.95), Vector3(0.6, 0.6, 0.4), Vector3(0, 0.4, 0))
	_tent(g, _n(n, Vector3(3.0, 0, -2.5), 0.2, 1.3), OLIVE_DRAB, "olive")
	_tent(g, _n(n, Vector3(4.2, 0, 1.8), -0.3, 1.1), Color(0.8, 0.5, 0.25), "patched")
	_bx(g, n, orange, Vector3(2.65, 0.75, -2.15), Vector3(0.36, 0.3, 0.02), Vector3(0, 0.2, 0))
	var gen := _n(n, Vector3(2.3, 0, 2.2), 0.4)
	_bx(g, gen, _m(g, "generator", Color(0.85, 0.65, 0.12)), Vector3(0, 0.35, 0), Vector3(0.9, 0.7, 0.6))
	_cy(g, gen, scrap, Vector3(0.3, 0.9, 0), 0.05, 0.05, 0.5, 6)
	_smoke(g, gen, Vector3(0.3, 1.2, 0), 0.45, Color(0.3, 0.3, 0.3, 0.5))
	var lamp := _glow(g, "flood", Color(1.0, 0.95, 0.8), 3.0)
	for s in [-1, 1]:
		var fp := Vector3(1.7, 0, s * 3.2)
		_cy(g, n, scrap, fp + Vector3(0, 1.2, 0), 0.04, 0.06, 2.4, 6)
		_bx(g, n, lamp, fp + Vector3(-0.1, 2.4, 0), Vector3(0.12, 0.28, 0.45), Vector3(0, 0, 0.5))
	_light(n, Vector3(1.0, 2.2, 0), Color(1.0, 0.92, 0.75), 1.1, 6.0)
	_cy(g, n, _m(g, "barrel_rust", Color(0.45, 0.25, 0.15)), Vector3(1.8, 0.3, 0.2), 0.24, 0.24, 0.6, 8)
	_flame(g, n, Vector3(1.8, 0.55, 0.2), 0.5, 1.0)
	_crates(g, _n(n, Vector3(3.6, 0, -0.2), 0.5), "server", _rng(3))
	_mast(g, _n(n, Vector3(5.2, 0, -1.0)), 3.0)
	_bx(g, n, orange, Vector3(5.45, 2.6, -1.0), Vector3(0.5, 0.3, 0.02))
