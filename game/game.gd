## Presentation layer: draws the simulation in 3D, runs HUD, audio and touch/mouse input.
## All game rules live in Sim; this file only reads sim state and sends player commands.
extends Node3D

const TICK := Sim.TICK
const SIDEBAR_W := 420.0
const MAX_STEPS_PER_FRAME := 12
const PITCH := 54.0
const GROUND_RECT := Rect2(-21.0, -13.0, 40.0, 26.0)   # must match tools/gen_ground.py
const HERO_PLACING := "__hero__"

const ICON_STAR := preload("res://assets/ui/icon_star.png")
const ICON_STAR_EMPTY := preload("res://assets/ui/icon_star_empty.png")
const ICON_LOCK := preload("res://assets/ui/icon_lock.png")
const ICON_GOLD := preload("res://assets/ui/icon_gold.png")
const ICON_LIVES := preload("res://assets/ui/icon_lives.png")
const ICON_WAVE := preload("res://assets/ui/icon_wave.png")
const ICON_PLAY := preload("res://assets/ui/icon_play.png")
const FONT := preload("res://assets/fonts/LilitaOne.woff2")

const THEMES := {
	"meadow": {"bg": Color(0.12, 0.3, 0.1), "far": Color(0.13, 0.32, 0.1), "ambient": Color(0.82, 0.88, 1.0), "ambient_e": 0.36,
		"sun": Color(1.0, 0.95, 0.86), "sun_e": 0.74, "rock": Color(0.52, 0.5, 0.47), "cave": Color(0.46, 0.43, 0.4), "base": ""},
	"snow": {"bg": Color(0.64, 0.72, 0.82), "far": Color(0.6, 0.68, 0.78), "ambient": Color(0.78, 0.86, 1.0), "ambient_e": 0.4,
		"sun": Color(0.9, 0.95, 1.05), "sun_e": 0.6, "rock": Color(0.5, 0.54, 0.6), "cave": Color(0.55, 0.58, 0.64), "base": "snow"},
	"volcano": {"bg": Color(0.07, 0.05, 0.05), "far": Color(0.09, 0.07, 0.07), "ambient": Color(0.86, 0.8, 0.78), "ambient_e": 0.34,
		"sun": Color(1.0, 0.86, 0.72), "sun_e": 0.78, "rock": Color(0.16, 0.14, 0.14), "cave": Color(0.22, 0.19, 0.18), "base": "volcano"},
	"delta": {"bg": Color(0.2, 0.36, 0.14), "far": Color(0.24, 0.42, 0.15), "ambient": Color(0.85, 0.9, 1.0), "ambient_e": 0.36,
		"sun": Color(1.0, 0.96, 0.86), "sun_e": 0.74, "rock": Color(0.66, 0.58, 0.44), "cave": Color(0.7, 0.5, 0.33), "base": ""},
	"desert": {"bg": Color(0.7, 0.53, 0.32), "far": Color(0.72, 0.55, 0.33), "ambient": Color(1.0, 0.92, 0.82), "ambient_e": 0.34,
		"sun": Color(1.0, 0.94, 0.8), "sun_e": 0.66, "rock": Color(0.78, 0.62, 0.42), "cave": Color(0.72, 0.55, 0.36), "base": "desert"},
	"canyon": {"bg": Color(0.36, 0.19, 0.13), "far": Color(0.4, 0.21, 0.14), "ambient": Color(1.0, 0.86, 0.76), "ambient_e": 0.34,
		"sun": Color(1.0, 0.9, 0.76), "sun_e": 0.76, "rock": Color(0.56, 0.3, 0.2), "cave": Color(0.62, 0.42, 0.28), "base": "canyon"},
}
const BASE_RECOLOR := {"snow": Color(0.9, 0.93, 0.98), "volcano": Color(0.3, 0.26, 0.24), "desert": Color(0.86, 0.7, 0.46),
	"canyon": Color(0.62, 0.36, 0.23)}
const SFX_NAMES := ["throw", "rock_hit", "club", "catapult", "boulder_land", "pulse", "robot_death", "boss_death", "coin",
	"place", "upgrade", "wave_horn", "life_lost", "boss_roar", "summon", "click", "error", "victory", "defeat",
	"arrow", "spear", "shield_up", "shield_break", "heal", "level_up", "hero_place", "ab_stone_rain", "ab_earthquake",
	"ab_solar_flare", "ab_forge_fury", "boss_roar_bronze"]

# palette
const C_PANEL := Color(0.17, 0.11, 0.07, 0.94)
const C_PANEL_EDGE := Color(0.46, 0.31, 0.17)
const C_TEXT := Color(1.0, 0.95, 0.85)
const C_GOLD := Color(1.0, 0.82, 0.22)

var defs: Dictionary
var map: Dictionary
var sim: Sim
var started := false
var speed := 1
var accum := 0.0
var time_s := 0.0
var cam: Camera3D
var cam_base := Vector3.ZERO
var shake := 0.0

var enemy_nodes := {}
var tower_nodes := {}
var proj_nodes := {}
var effects: Array = []
var mats := {}
var _res_cache := {}

var placing := ""
var selected := -1
var ghost: Node3D
var ghost_range: MeshInstance3D
var ghost_foot: MeshInstance3D
var sel_range: MeshInstance3D
var aura_range: MeshInstance3D

# audio
var sfx := {}
var sfx_players: Array = []
var sfx_last := {}
var music: AudioStreamPlayer
var muted := false
var world_env: Environment

# HUD
var lbl_gold: Label
var lbl_lives: Label
var lbl_wave: Label
var btn_start: Button
var btn_speed: Button
var btn_auto: Button
var btn_pause: Button
var ui_root: Control
var pause_menu: Control
var settings_panel: Control
var legacy_panel: Control
var paused := false
var auto_t := -1.0              # countdown to the next auto-started wave (-1 = idle)
var waves_cleared := 0
var xp_waves_awarded := 0
var xp_win_awarded := false
var first_clear := false
var modals: Array = []
var side_scroll: ScrollContainer
var tower_actions: VBoxContainer
var shop_box: VBoxContainer
var shop_buttons := {}
var tower_box: VBoxContainer
var tower_icon: TextureRect
var lbl_t_name: Label
var lbl_t_info: Label
var up_box: VBoxContainer
var btn_sell: Button
var btn_target: Button
var toast: Label
var toast_t := 0.0
var banner: Label
var banner_t := 0.0
var overlay: Control
var lbl_overlay: Label
var lbl_overlay_sub: Label
var btn_endless: Button
var title_screen: Control
var map_select: Control
var hero_card: PanelContainer
var lbl_hero_name: Label
var lbl_hero_level: Label
var hero_xp_fill: ColorRect
var btn_hero: Button
var demo := false
var map_id := "mammoth_valley"
var map_order: Array = []
var theme: Dictionary


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--map="):
			Progress.current_map = a.trim_prefix("--map=")
		if a.begins_with("--hero="):
			Progress.data.hero = a.trim_prefix("--hero=")
		if a.begins_with("--ui="):
			Progress.data.settings.ui_scale = float(a.trim_prefix("--ui="))
	map_order = []
	for m in Defs.map_list():
		map_order.append(m.id)
	if Progress.current_map != "":
		map_id = Progress.current_map
	map = Defs.load_map(map_id)
	defs = Defs.load_all(map)
	theme = THEMES[map.get("theme", "meadow")]
	sim = Sim.new()
	sim.setup(defs, map)
	var hid := Progress.hero()
	if not defs.heroes.heroes.has(hid) or not Progress.hero_unlocked(defs.heroes.heroes[hid]):
		hid = "ugo"
	sim.set_hero(hid)
	if not "--noperks" in OS.get_cmdline_user_args():
		sim.apply_perks(Progress.sim_perks())
		sim.hp_mult *= Progress.timeline_hp_mult()
	_build_world()
	_build_audio()
	_build_hud()
	_apply_settings()
	demo = "--demo" in OS.get_cmdline_user_args()
	if "--autowin" in OS.get_cmdline_user_args():
		_run_autowin()
	elif demo:
		_run_demo()
	elif Progress.open_legacy:
		Progress.open_legacy = false
		title_screen.visible = false
		map_select.visible = true
		_open_legacy()
	elif Progress.open_map_select:
		Progress.open_map_select = false
		title_screen.visible = false
		map_select.visible = true
	elif Progress.current_map != "":
		title_screen.visible = false
		_start_game()


# =================================================================== helpers
func _res(path: String) -> Resource:
	if not _res_cache.has(path):
		_res_cache[path] = load(path)
	return _res_cache[path]


func _icon_tex(id: String) -> Texture2D:
	return _res("res://assets/ui/icon_%s.png" % id)


func _mat(key: String, color: Color, opts: Dictionary = {}) -> StandardMaterial3D:
	if mats.has(key):
		return mats[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = opts.get("rough", 0.85)
	m.metallic = opts.get("metal", 0.0)
	if opts.has("emit"):
		m.emission_enabled = true
		m.emission = opts.emit
		m.emission_energy_multiplier = opts.get("emit_e", 1.5)
	if color.a < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	if opts.get("unshaded", false):
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if opts.get("billboard", false):
		m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		m.billboard_keep_scale = true
	if opts.get("nodepth", false):
		m.no_depth_test = true
		m.render_priority = 2
	mats[key] = m
	return m


func _mi(mesh: Mesh, m: Material, parent: Node, pos := Vector3.ZERO, rot := Vector3.ZERO, scl := Vector3.ONE) -> MeshInstance3D:
	var n := MeshInstance3D.new()
	n.mesh = mesh
	n.material_override = m
	n.position = pos
	n.rotation = rot
	n.scale = scl
	parent.add_child(n)
	return n


func _cyl(rt: float, rb: float, h: float, seg := 8) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = rt
	c.bottom_radius = rb
	c.height = h
	c.radial_segments = seg
	c.rings = 1
	return c


func _box(x: float, y: float, z: float) -> BoxMesh:
	var b := BoxMesh.new()
	b.size = Vector3(x, y, z)
	return b


func _sph(r: float, seg := 10) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	s.radial_segments = seg
	s.rings = maxi(seg / 2, 3)
	return s


func _v3(p: Vector2, y := 0.0) -> Vector3:
	return Vector3(p.x, y, p.y)


func _yaw(dir: Vector2) -> float:
	return atan2(dir.x, dir.y)


func _era() -> String:
	return str(map.get("era", "Stone Age"))


# =================================================================== world
func _build_world() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = theme.bg
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = theme.ambient
	env.ambient_light_energy = theme.ambient_e
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.glow_enabled = true
	env.glow_intensity = 0.32
	env.glow_strength = 1.0
	env.glow_bloom = 0.0
	env.glow_hdr_threshold = 1.25
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	world_env = env
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, -40, 0)
	sun.light_color = theme.sun
	sun.light_energy = theme.sun_e
	sun.shadow_enabled = true
	sun.shadow_blur = 1.5
	sun.directional_shadow_max_distance = 80.0
	add_child(sun)

	cam = Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = 20.0
	cam.near = 1.0
	cam.far = 200.0
	add_child(cam)
	_frame_camera()
	get_viewport().size_changed.connect(_frame_camera)

	# painted ground: one textured plane, painted from the same map file the sim uses
	var pm := PlaneMesh.new()
	pm.size = GROUND_RECT.size
	var gm := StandardMaterial3D.new()
	gm.albedo_texture = load("res://assets/textures/ground_%s.png" % map_id)
	gm.albedo_color = Color(0.9, 0.9, 0.88)
	gm.roughness = 1.0
	gm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mi(pm, gm, self, Vector3(GROUND_RECT.position.x + GROUND_RECT.size.x * 0.5, 0, GROUND_RECT.position.y + GROUND_RECT.size.y * 0.5))
	var far := PlaneMesh.new()
	far.size = Vector2(160, 120)
	_mi(far, _mat("far_ground", theme.far), self, Vector3(0, -0.02, 0))

	for P in sim.paths:
		var pts: PackedVector2Array = P.pts
		_build_portal(pts[0], (pts[1] - pts[0]).normalized())
	var end_pt := sim.path[sim.path.size() - 1]
	if str(map.get("base", "cave")) == "city":
		_build_city(end_pt)
	else:
		_build_cave(end_pt)
	_build_decor()
	_build_blockers()

	sel_range = _mi(_cyl(1, 1, 0.02, 48), _mat("range", Color(1, 1, 1, 0.16), {"unshaded": true}), self, Vector3(0, 0.12, 0))
	sel_range.visible = false
	aura_range = _mi(_cyl(1, 1, 0.02, 48), _mat("aura_range", Color(1, 0.8, 0.25, 0.14), {"unshaded": true}), self, Vector3(0, 0.11, 0))
	aura_range.visible = false
	ghost = Node3D.new()
	add_child(ghost)
	ghost.visible = false
	ghost_range = _mi(_cyl(1, 1, 0.02, 48), _mat("range_g", Color(1, 1, 1, 0.18), {"unshaded": true}), ghost, Vector3(0, 0.13, 0))
	ghost_foot = _mi(_cyl(1, 1, 0.03, 24), _mat("foot_ok", Color(0.2, 1, 0.3, 0.45), {"unshaded": true}), ghost, Vector3(0, 0.15, 0))


func _frame_camera() -> void:
	var vp := get_viewport().get_visible_rect().size
	var aspect := vp.x / maxf(vp.y, 1.0)
	var side_frac := SIDEBAR_W / maxf(vp.x, 1.0)
	var need_w := 31.0
	var need_h := 18.6 * sin(deg_to_rad(PITCH)) + 2.6
	cam.size = maxf(need_h, need_w / (aspect * (1.0 - side_frac)))
	var view_w := cam.size * aspect
	var target := Vector3(view_w * side_frac * 0.5, 0, 0.6)
	var back := Vector3(0, sin(deg_to_rad(PITCH)), cos(deg_to_rad(PITCH))) * 60.0
	cam.position = target + back
	cam.look_at(target, Vector3.UP)
	cam_base = cam.position


func _build_portal(p: Vector2, dir: Vector2) -> void:
	var n := Node3D.new()
	n.position = _v3(p + dir * 1.3, 0)
	n.rotation.y = _yaw(dir) - 0.65
	add_child(n)
	var tor := TorusMesh.new()
	tor.inner_radius = 0.95
	tor.outer_radius = 1.25
	tor.rings = 32
	tor.ring_segments = 8
	var ring := _mi(tor, _mat("portal", Color(1.0, 0.25, 0.15), {"emit": Color(1.0, 0.12, 0.05), "emit_e": 2.2}), n, Vector3(0, 1.3, 0), Vector3(PI * 0.5, 0, 0))
	var core := _mi(_cyl(0.95, 0.95, 0.04, 32), _mat("portal_core", Color(1.0, 0.45, 0.4, 0.5), {"emit": Color(1.0, 0.2, 0.1), "emit_e": 1.2, "unshaded": true}), n, Vector3(0, 1.3, 0), Vector3(PI * 0.5, 0, 0))
	for s in [-1, 1]:
		_mi(_box(0.4, 0.6, 0.4), _mat("steel", Color(0.45, 0.48, 0.55), {"metal": 0.6, "rough": 0.4}), n, Vector3(s * 1.2, 0.3, 0))
		_mi(_box(0.18, 0.12, 0.42), _mat("red_glow", Color(1, 0.1, 0.05), {"emit": Color(1, 0.08, 0.03), "emit_e": 2.0}), n, Vector3(s * 1.2, 0.55, 0))
	n.set_meta("spin", ring)
	n.set_meta("core", core)
	effects.append({"node": n, "life": INF, "t": 0.0, "kind": "portal"})


func _campfire(parent: Node3D, pos: Vector3, light_e := 2.0, scale_k := 1.0) -> void:
	var fire := Node3D.new()
	fire.position = pos
	fire.scale = Vector3.ONE * scale_k
	parent.add_child(fire)
	var flame := _mi(_cyl(0.0, 0.32, 0.7, 6), _mat("flame", Color(1.0, 0.55, 0.1), {"emit": Color(1.0, 0.45, 0.05), "emit_e": 2.5}), fire, Vector3(0, 0.45, 0))
	var flame2 := _mi(_cyl(0.0, 0.18, 0.45, 5), _mat("flame2", Color(1.0, 0.9, 0.4), {"emit": Color(1.0, 0.8, 0.3), "emit_e": 2.5}), fire, Vector3(0, 0.35, 0))
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.6, 0.25)
	light.light_energy = light_e
	light.omni_range = 4.0
	light.position = Vector3(0, 0.8, 0)
	fire.add_child(light)
	effects.append({"node": fire, "life": INF, "t": 0.0, "kind": "fire", "f1": flame, "f2": flame2, "light": light, "base_e": light_e})


func _build_cave(p: Vector2) -> void:
	var n := Node3D.new()
	n.position = _v3(p, 0)
	add_child(n)
	var rock := _mat("cave_rock", theme.cave)
	var rock2 := _mat("cave_rock2", theme.cave.darkened(0.22))
	if map.get("theme", "") == "snow":
		_mi(_sph(1.5, 9), _mat("snowcap", Color(0.95, 0.97, 1.0)), n, Vector3(0.9, 0.75, 0), Vector3(0, 0.4, 0), Vector3(1, 0.6, 1.3))
	_mi(_sph(1.7, 9), rock, n, Vector3(0.8, 0.2, 0), Vector3(0, 0.4, 0), Vector3(1, 0.95, 1.35))
	_mi(_sph(1.0, 8), rock2, n, Vector3(1.0, 0.9, -1.1), Vector3.ZERO, Vector3(1.1, 1.0, 1))
	_mi(_sph(0.95, 8), _mat("cave_mouth", Color(0.04, 0.03, 0.03)), n, Vector3(-0.6, 0.45, 0), Vector3.ZERO, Vector3(0.45, 0.85, 0.9))
	var fire_pos := Vector3(-1.5, 0, 1.6)
	for k in 3:
		_mi(_cyl(0.07, 0.07, 0.8, 5), _mat("wood", Color(0.45, 0.27, 0.12)), n, fire_pos + Vector3(0, 0.1, 0), Vector3(PI * 0.5, k * 1.05, 0))
	for k in 6:
		var a := TAU * k / 6.0
		_mi(_sph(0.12, 6), rock2, n, fire_pos + Vector3(cos(a) * 0.45, 0.05, sin(a) * 0.45), Vector3.ZERO, Vector3(1, 0.6, 1))
	_campfire(n, fire_pos)


## Bronze Age: the humans defend a walled mud-brick city instead of a cave.
func _build_city(p: Vector2) -> void:
	var n := Node3D.new()
	n.position = _v3(p, 0)
	add_child(n)
	var brick := _mat("mudbrick", Color(0.72, 0.52, 0.34))
	var brick_d := _mat("mudbrick_d", Color(0.56, 0.38, 0.24))
	var red := _mat("banner_red", Color(0.72, 0.14, 0.1))
	var lapis := _mat("lapis", Color(0.16, 0.28, 0.72), {"rough": 0.5})
	var wood := _mat("wood_dark", Color(0.3, 0.17, 0.08))
	for s in [-1, 1]:
		var tw := Vector3(0.7, 0, s * 1.55)
		_mi(_box(1.3, 2.3, 1.3), brick, n, tw + Vector3(0, 1.15, 0))
		for cx in [-0.45, 0.0, 0.45]:
			for cz in [-0.45, 0.45]:
				_mi(_box(0.26, 0.28, 0.26), brick, n, tw + Vector3(cx, 2.42, cz))
		_mi(_box(1.34, 0.12, 1.34), lapis, n, tw + Vector3(0, 1.85, 0))
		_mi(_box(0.04, 0.8, 0.5), red, n, tw + Vector3(-0.67, 1.3, 0))
		_mi(_box(0.9, 1.5, 4.2), brick_d, n, Vector3(1.0, 0.75, s * 4.3))           # wall
		for k in 7:
			_mi(_box(0.3, 0.25, 0.3), brick_d, n, Vector3(1.0, 1.62, s * (2.5 + k * 0.6)))
		_campfire(n, Vector3(-0.15, 0.0, s * 1.55), 1.4, 0.55)
		_mi(_cyl(0.07, 0.1, 0.5, 6), wood, n, Vector3(-0.15, 0.0, s * 1.55))
	_mi(_box(1.0, 0.45, 2.0), brick, n, Vector3(0.7, 2.05, 0))                      # gate lintel
	_mi(_box(0.12, 1.8, 1.8), wood, n, Vector3(1.0, 0.9, 0))                         # gate doors
	_mi(_box(0.14, 0.1, 1.8), _mat("bronze_band", Color(0.66, 0.38, 0.13), {"metal": 0.55, "rough": 0.4}), n, Vector3(0.95, 1.2, 0))
	# ziggurat and houses behind the walls
	for k in 4:
		var w := 3.2 - k * 0.7
		_mi(_box(w, 0.55, w), brick if k % 2 == 0 else brick_d, n, Vector3(4.0, 0.28 + k * 0.55, -2.5))
	_mi(_box(0.5, 0.5, 0.5), _mat("gold_top", Color(0.95, 0.7, 0.18), {"metal": 0.6, "rough": 0.3}), n, Vector3(4.0, 2.45, -2.5))
	for hp in [Vector3(3.0, 0, 2.2), Vector3(4.6, 0, 1.0), Vector3(2.6, 0, -5.2)]:
		_mi(_box(1.2, 0.9, 1.0), brick, n, hp + Vector3(0, 0.45, 0))
		_mi(_box(1.3, 0.1, 1.1), brick_d, n, hp + Vector3(0, 0.95, 0))


func _palm(parent: Node3D, pos: Vector3, s: float, r: RandomNumberGenerator) -> void:
	var t := Node3D.new()
	t.position = pos
	t.scale = Vector3.ONE * s
	t.rotation.y = r.randf() * TAU
	parent.add_child(t)
	var trunk := _mat("palm_trunk", Color(0.5, 0.36, 0.2))
	var lean := r.randf_range(-0.15, 0.15)
	for k in 5:
		_mi(_cyl(0.09, 0.11, 0.42, 6), trunk, t, Vector3(lean * k * 0.4, 0.21 + k * 0.4, 0), Vector3(0, 0, -lean))
	var top := Vector3(lean * 2.0, 2.05, 0)
	var leaf := [_mat("palm_leaf", Color(0.2, 0.5, 0.16)), _mat("palm_leaf2", Color(0.28, 0.58, 0.2))]
	for k in 7:
		var a := TAU * k / 7.0
		var fr := _mi(_box(0.22, 0.04, 1.1), leaf[k % 2], t, top + Vector3(sin(a) * 0.5, -0.12, cos(a) * 0.5), Vector3(0.45, a, 0))
	_mi(_sph(0.14, 6), _mat("coconut", Color(0.32, 0.22, 0.12)), t, top + Vector3(0, -0.1, 0))


func _build_decor() -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 11
	var th: String = map.get("theme", "meadow")
	var b: Array = map.bounds
	var trunk := _mat("trunk", Color(0.36, 0.22, 0.1))
	var pines := [_mat("pine1", Color(0.11, 0.36, 0.14)), _mat("pine2", Color(0.16, 0.44, 0.15))]
	var bush := [_mat("bush1", Color(0.22, 0.5, 0.15)), _mat("bush2", Color(0.3, 0.56, 0.18))]
	var snow := _mat("snow", Color(0.96, 0.98, 1.0))
	var dead := _mat("deadwood", Color(0.12, 0.1, 0.09))
	var ember := _mat("ember", Color(1, 0.4, 0.1), {"emit": Color(1, 0.35, 0.05), "emit_e": 2.0})
	var rockm := _mat("decor_rock", theme.rock)
	var placed := 0
	var tries := 0
	var target_count: int = {"desert": 55, "canyon": 60}.get(th, 95)
	while placed < target_count and tries < 2000:
		tries += 1
		var x := r.randf_range(-19.5, 17.5)
		var z := r.randf_range(-12.0, 12.0)
		var inside: bool = x > b[0] - 0.8 and x < b[2] + 0.8 and z > b[1] - 0.8 and z < b[3] + 0.8
		if inside or sim.dist_to_path(Vector2(x, z)) < 2.2:
			continue
		if x > 13.0 and absf(z - sim.path[sim.path.size() - 1].y) < 6.5 and map.get("base", "cave") == "city":
			continue   # keep the city clear
		placed += 1
		var roll := r.randf()
		var pos := Vector3(x, 0, z)
		match th:
			"delta":
				if roll < 0.55:
					_palm(self, pos, r.randf_range(0.8, 1.25), r)
				else:
					_mi(_sph(0.55, 8), bush[r.randi() % 2], self, pos + Vector3(0, 0.3, 0), Vector3.ZERO, Vector3(1.2, 0.75, 1.1))
				continue
			"desert":
				if roll < 0.3:
					_palm(self, pos, r.randf_range(0.75, 1.1), r)
				elif roll < 0.55:   # broken column
					_mi(_cyl(0.28, 0.3, r.randf_range(0.6, 1.8), 10), _mat("column", Color(0.88, 0.8, 0.64)), self, pos + Vector3(0, 0.5, 0))
				else:
					_mi(_sph(r.randf_range(0.4, 0.8), 6), rockm, self, pos + Vector3(0, 0.15, 0), Vector3(0, r.randf() * 3, 0), Vector3(1.3, 0.6, 1))
				continue
			"canyon":
				if roll < 0.45:   # mesa
					var h := r.randf_range(1.2, 3.2)
					_mi(_cyl(r.randf_range(0.7, 1.4), r.randf_range(1.0, 1.8), h, 7), rockm, self, pos + Vector3(0, h * 0.5, 0), Vector3(0, r.randf() * 3, 0))
					_mi(_cyl(0.9, 0.9, 0.08, 7), _mat("strata", Color(0.78, 0.5, 0.32)), self, pos + Vector3(0, h * 0.62, 0))
				elif roll < 0.6:  # mine timber frame
					for sx in [-0.5, 0.5]:
						_mi(_box(0.16, 1.4, 0.16), trunk, self, pos + Vector3(sx, 0.7, 0))
					_mi(_box(1.2, 0.16, 0.2), trunk, self, pos + Vector3(0, 1.45, 0))
				else:
					_mi(_sph(r.randf_range(0.3, 0.7), 6), rockm, self, pos + Vector3(0, 0.15, 0), Vector3(0, r.randf() * 3, 0), Vector3(1.2, 0.7, 1))
				continue
		var t := Node3D.new()
		t.position = pos
		var s := r.randf_range(0.75, 1.35)
		t.scale = Vector3(s, s * r.randf_range(0.9, 1.2), s)
		t.rotation.y = r.randf() * TAU
		add_child(t)
		if th == "volcano":
			if roll < 0.55:   # charred dead tree
				_mi(_cyl(0.08, 0.14, 1.6, 5), dead, t, Vector3(0, 0.8, 0))
				for k in 3:
					_mi(_cyl(0.03, 0.06, 0.7, 4), dead, t, Vector3(0, 0.9 + k * 0.25, 0), Vector3(0.9, k * 2.1, 0.0))
			else:             # basalt boulder with a glowing seam
				_mi(_sph(r.randf_range(0.4, 0.8), 6), rockm, t, Vector3(0, 0.2, 0), Vector3.ZERO, Vector3(1.2, 0.75, 1))
				if roll > 0.85:
					_mi(_box(0.5, 0.05, 0.06), ember, t, Vector3(0, 0.55, 0.3))
			continue
		if roll < 0.72:
			_mi(_cyl(0.12, 0.16, 0.6, 6), trunk, t, Vector3(0, 0.3, 0))
			var pm: Material = pines[r.randi() % 2]
			_mi(_cyl(0.0, 0.85, 1.3, 7), pm, t, Vector3(0, 1.05, 0))
			_mi(_cyl(0.0, 0.62, 1.0, 7), pines[(r.randi() + 1) % 2], t, Vector3(0, 1.65, 0))
			_mi(_cyl(0.0, 0.38, 0.7, 7), snow if th == "snow" else pm, t, Vector3(0, 2.15, 0))
			if th == "snow":
				_mi(_cyl(0.3, 0.7, 0.18, 7), snow, t, Vector3(0, 1.25, 0))
		elif th == "snow":
			_mi(_sph(0.6, 8), snow, t, Vector3(0, 0.15, 0), Vector3.ZERO, Vector3(1.4, 0.55, 1.1))
		else:
			var bm: Material = bush[r.randi() % 2]
			_mi(_sph(0.55, 8), bm, t, Vector3(0, 0.35, 0), Vector3.ZERO, Vector3(1.2, 0.8, 1.1))
			_mi(_sph(0.4, 7), bush[(r.randi() + 1) % 2], t, Vector3(0.4, 0.3, 0.2), Vector3.ZERO, Vector3(1, 0.8, 1))
	if th in ["meadow", "snow", "volcano", "delta"]:
		for i in 22:
			var x2 := r.randf_range(-19.0, 17.0)
			var z2 := r.randf_range(-12.0, 12.0)
			var inside2: bool = x2 > b[0] and x2 < b[2] and z2 > b[1] and z2 < b[3]
			if inside2 or sim.dist_to_path(Vector2(x2, z2)) < 1.5:
				continue
			_mi(_sph(r.randf_range(0.3, 0.7), 7), rockm, self, Vector3(x2, 0.12, z2), Vector3(0, r.randf() * 3, 0), Vector3(1.25, 0.7, 1))
	if th == "volcano":
		var v := Node3D.new()
		v.position = Vector3(-3.0, 0, -13.5)
		add_child(v)
		_mi(_cyl(1.6, 6.5, 4.2, 10), _mat("volcano", Color(0.15, 0.12, 0.12)), v, Vector3(0, 2.1, 0))
		_mi(_cyl(1.5, 1.5, 0.1, 10), _mat("crater", Color(1, 0.5, 0.1), {"emit": Color(1, 0.4, 0.05), "emit_e": 3.0, "unshaded": true}), v, Vector3(0, 4.22, 0))
		for k in 3:
			_mi(_box(0.35, 0.05, 2.8), _mat("lavaflow", Color(1, 0.45, 0.08), {"emit": Color(1, 0.35, 0.05), "emit_e": 2.0}), v,
				Vector3(-1.2 + k * 1.2, 2.3, 2.6 - k * 0.3), Vector3(-0.75, 0.3 - k * 0.3, 0))
		var vl := OmniLight3D.new()
		vl.light_color = Color(1, 0.5, 0.2)
		vl.light_energy = 3.0
		vl.omni_range = 9.0
		vl.position = Vector3(0, 5.0, 0)
		v.add_child(vl)
	if th == "desert":   # the citadel's step pyramid on the horizon
		var pyr := Node3D.new()
		pyr.position = Vector3(-2.0, 0, -14.0)
		add_child(pyr)
		for k in 5:
			var w := 9.0 - k * 1.7
			_mi(_box(w, 0.9, w * 0.7), _mat("pyr_%d" % (k % 2), Color(0.86, 0.72, 0.48) if k % 2 == 0 else Color(0.78, 0.62, 0.4)), pyr, Vector3(0, 0.45 + k * 0.9, 0))
		_mi(_box(1.2, 0.6, 0.9), _mat("gold_top", Color(0.95, 0.7, 0.18), {"metal": 0.6, "rough": 0.3}), pyr, Vector3(0, 4.8, 0))


## No-build zones: the ground texture paints them; these add depth and glow.
func _build_blockers() -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 5
	var th: String = map.get("theme", "meadow")
	for bl in map.get("blockers", []):
		var pos := Vector3(bl[0], 0, bl[1])
		var rad := float(bl[2])
		var kind: String = bl[3] if bl.size() > 3 else "rocks"
		var n := Node3D.new()
		n.position = pos
		add_child(n)
		match kind:
			"lake":
				if th == "snow":
					_mi(_cyl(rad * 0.95, rad * 0.95, 0.02, 32), _mat("ice", Color(0.75, 0.9, 1.0, 0.3), {"rough": 0.05, "metal": 0.3}), n, Vector3(0, 0.03, 0))
					for k in 7:
						var a := TAU * k / 7.0 + r.randf() * 0.4
						var h := r.randf_range(0.3, 0.7)
						_mi(_cyl(0.0, r.randf_range(0.12, 0.22), h, 5), _mat("shard", Color(0.7, 0.88, 1.0), {"emit": Color(0.4, 0.7, 1.0), "emit_e": 0.6, "rough": 0.1}), n,
							Vector3(cos(a) * rad, h * 0.5, sin(a) * rad), Vector3(r.randf_range(-0.3, 0.3), 0, r.randf_range(-0.3, 0.3)))
				else:
					_mi(_cyl(rad * 0.92, rad * 0.92, 0.02, 28), _mat("pond", Color(0.3, 0.6, 0.7, 0.35), {"rough": 0.05, "metal": 0.2}), n, Vector3(0, 0.03, 0))
					for k in 10:
						var a2 := TAU * k / 10.0 + r.randf() * 0.3
						_mi(_cyl(0.015, 0.03, r.randf_range(0.4, 0.7), 4), _mat("reed", Color(0.32, 0.5, 0.18)), n,
							Vector3(cos(a2) * rad, 0.25, sin(a2) * rad), Vector3(r.randf_range(-0.2, 0.2), 0, r.randf_range(-0.2, 0.2)))
			"lava", "ore":
				var lava := kind == "lava"
				var col := Color(1, 0.55, 0.15, 0.45) if lava else Color(0.3, 1.0, 0.8, 0.45)
				var emit := Color(1, 0.42, 0.05) if lava else Color(0.15, 0.9, 0.65)
				var pool := _mi(_cyl(rad * 0.85, rad * 0.85, 0.04, 28), _mat("pool_" + kind, col, {"emit": emit, "emit_e": 1.0, "unshaded": true}), n, Vector3(0, 0.04, 0))
				for k in 9:
					var a3 := TAU * k / 9.0 + r.randf() * 0.3
					_mi(_sph(r.randf_range(0.18, 0.32), 6), (_mat("crust", Color(0.08, 0.06, 0.06)) if lava else _mat("ore_rock", Color(0.42, 0.24, 0.16))), n,
						Vector3(cos(a3) * rad, 0.08, sin(a3) * rad), Vector3.ZERO, Vector3(1.3, 0.6, 1))
				if not lava:
					for k in 5:
						var a4 := TAU * k / 5.0 + 0.3
						_mi(_cyl(0.0, 0.14, r.randf_range(0.4, 0.8), 5), _mat("crystal", Color(0.3, 1.0, 0.75), {"emit": Color(0.2, 0.9, 0.6), "emit_e": 1.2}), n,
							Vector3(cos(a4) * rad * 0.55, 0.25, sin(a4) * rad * 0.55), Vector3(r.randf_range(-0.4, 0.4), 0, r.randf_range(-0.4, 0.4)))
				var ll := OmniLight3D.new()
				ll.light_color = Color(1, 0.45, 0.15) if lava else Color(0.3, 1.0, 0.7)
				ll.light_energy = 0.9
				ll.omni_range = rad * 2.2
				ll.position = Vector3(0, 0.8, 0)
				n.add_child(ll)
				effects.append({"node": n, "life": INF, "t": r.randf() * 5.0, "kind": "lava", "pool": pool, "light": ll})
			"dune":
				var dm := _mat("dune", Color(0.86, 0.66, 0.38))
				var dm2 := _mat("dune_crest", Color(0.93, 0.76, 0.48))
				var ry := r.randf() * 3
				_mi(_sph(rad, 14), dm, n, Vector3.ZERO, Vector3(0, ry, 0), Vector3(1.0, 0.42, 0.8))
				_mi(_sph(rad * 0.6, 12), dm2, n, Vector3(cos(ry) * rad * 0.25, rad * 0.18, -sin(ry) * rad * 0.25), Vector3(0, ry, 0), Vector3(1.2, 0.55, 0.7))
				for k in 3:
					var a7 := r.randf() * TAU
					_mi(_cyl(0.0, 0.05, 0.35, 4), _mat("dry_grass", Color(0.6, 0.5, 0.25)), n, Vector3(cos(a7) * rad * 0.85, 0.12, sin(a7) * rad * 0.7))
			"ruins":
				for k in 4:
					var a5 := TAU * k / 4.0 + 0.4
					var h2 := r.randf_range(0.5, 1.9)
					_mi(_cyl(0.24, 0.27, h2, 10), _mat("column", Color(0.88, 0.8, 0.64)), n, Vector3(cos(a5) * rad * 0.6, h2 * 0.5, sin(a5) * rad * 0.6))
					_mi(_box(0.62, 0.16, 0.62), _mat("column_cap", Color(0.78, 0.7, 0.55)), n, Vector3(cos(a5) * rad * 0.6, h2 + 0.08, sin(a5) * rad * 0.6))
				_mi(_box(1.1, 0.4, 0.55), _mat("column", Color(0.88, 0.8, 0.64)), n, Vector3(0.2, 0.2, -0.1), Vector3(0, 0.6, 0))
			"pillar":
				var h3 := r.randf_range(2.4, 3.4)
				_mi(_cyl(rad * 0.55, rad * 0.8, h3, 7), _mat("decor_rock", theme.rock), n, Vector3(0, h3 * 0.5, 0), Vector3(0, r.randf() * 3, 0))
				_mi(_cyl(rad * 0.6, rad * 0.6, 0.12, 7), _mat("strata", Color(0.78, 0.5, 0.32)), n, Vector3(0, h3 * 0.7, 0))
			"palms":
				for k in 3:
					var a6 := TAU * k / 3.0
					_palm(n, Vector3(cos(a6) * rad * 0.45, 0, sin(a6) * rad * 0.45), r.randf_range(0.8, 1.1), r)
			_:
				for k in 5:
					var off := Vector2(r.randf_range(-0.6, 0.6), r.randf_range(-0.6, 0.6)) * rad
					var sz := r.randf_range(0.35, 0.7) * rad
					var rock := _mi(_sph(sz, 6), _mat("outcrop", theme.rock), n, Vector3(off.x, sz * 0.4, off.y), Vector3(0, r.randf() * 3, 0), Vector3(1.1, 0.8, 1))
					if th == "snow":
						_mi(_sph(sz * 0.7, 6), _mat("snow", Color(0.96, 0.98, 1.0)), rock, Vector3(0, sz * 0.55, 0), Vector3.ZERO, Vector3(1, 0.45, 1))


# =================================================================== audio
func _bus(name: String) -> int:
	var i := AudioServer.get_bus_index(name)
	if i == -1:
		AudioServer.add_bus()
		i = AudioServer.bus_count - 1
		AudioServer.set_bus_name(i, name)
		AudioServer.set_bus_send(i, "Master")
	return i


func _build_audio() -> void:
	_bus("Music")
	_bus("SFX")
	for n in SFX_NAMES:
		sfx[n] = load("res://assets/audio/%s.wav" % n)
	for i in 14:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		sfx_players.append(p)
	music = AudioStreamPlayer.new()
	music.stream = load("res://assets/audio/music_bronze_age.wav" if _era() == "Bronze Age" else "res://assets/audio/music_stone_age.wav")
	music.volume_db = -9.0
	music.bus = "Music"
	add_child(music)
	music.finished.connect(func(): music.play())


func _sfx(name: String, vol_db := 0.0, pitch_var := 0.08, min_gap := 0.04) -> void:
	if muted or demo or not sfx.has(name):
		return
	var now := Time.get_ticks_msec() / 1000.0
	if now - float(sfx_last.get(name, -1.0)) < min_gap:
		return
	sfx_last[name] = now
	for p in sfx_players:
		if not p.playing:
			p.stream = sfx[name]
			p.volume_db = vol_db
			p.pitch_scale = 1.0 + randf_range(-pitch_var, pitch_var)
			p.play()
			return


# =================================================================== towers and hero
func _unit_def(u: Dictionary) -> Dictionary:
	if u.get("is_hero", false):
		return sim.hero_def
	return defs.towers[u.type]


func _rig_model(root: Node3D, model: Node3D) -> void:
	var yaw := model.find_child("Yaw", true, false)
	if yaw == null:
		yaw = model.find_child("Caveman", true, false)
	var arm := model.find_child("Arm", true, false)
	if arm == null:
		arm = model.find_child("Shoulder_R", true, false)
	if yaw != null:
		root.set_meta("yaw", yaw)
	if arm != null:
		root.set_meta("arm", arm)
		arm.set_meta("rest", arm.rotation.x)
	var orb := model.find_child("Orb", true, false)
	if orb != null:
		root.set_meta("orb", orb)


func _make_tower_visual(type: String) -> Node3D:
	var root := Node3D.new()
	var model: Node3D = (_res("res://assets/towers/%s.glb" % type) as PackedScene).instantiate()
	model.scale = Vector3.ONE * float(defs.towers[type].get("model_scale", 0.56))
	root.add_child(model)
	_rig_model(root, model)
	_retheme_base(model)
	return root


func _make_hero_visual(id: String) -> Node3D:
	var root := Node3D.new()
	var hd: Dictionary = defs.heroes.heroes[id]
	var model: Node3D = (_res("res://assets/heroes/%s.glb" % id) as PackedScene).instantiate()
	model.scale = Vector3.ONE * float(hd.get("model_scale", 0.55))
	root.add_child(model)
	_rig_model(root, model)
	return root


## Tower bases are modelled as grass; on other ground types repaint them to match.
func _retheme_base(model: Node) -> void:
	var key: String = theme.get("base", "")
	if key == "":
		return
	var m := _mat("base_" + key, BASE_RECOLOR[key], {"rough": 0.9})
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = mi.mesh
		if mesh == null:
			continue
		for si in mesh.get_surface_count():
			var sm := mesh.surface_get_material(si)
			if sm != null and sm.resource_name == "Grass":
				mi.set_surface_override_material(si, m)


func _add_unit_deco(n: Node3D) -> void:
	var deco := Node3D.new()
	deco.name = "Deco"
	n.add_child(deco)
	var buff := _mi(_sph(0.12, 4), _mat("buff", Color(1, 0.85, 0.3), {"emit": Color(1, 0.75, 0.2), "emit_e": 2.0, "unshaded": true}), n, Vector3(0, 2.15, 0))
	buff.name = "Buff"
	buff.visible = false


func _spawn_tower_node(t: Dictionary) -> void:
	var n := _make_tower_visual(t.type)
	n.position = _v3(t.pos)
	add_child(n)
	_add_unit_deco(n)
	tower_nodes[t.id] = n
	_refresh_tower_node(t)
	_ring_fx(_v3(t.pos, 0.2), 1.1, Color(1, 0.9, 0.5), 0.4)
	_dust_fx(_v3(t.pos, 0.2), 8, 0.9)
	_sfx("place")
	n.scale = Vector3(0.6, 1.4, 0.6)
	var tw := create_tween()
	tw.tween_property(n, "scale", Vector3.ONE * (1.0 + 0.04 * t.level), 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _spawn_hero_node() -> void:
	var h: Dictionary = sim.hero
	var n := _make_hero_visual(h.type)
	n.position = _v3(h.pos)
	add_child(n)
	_add_unit_deco(n)
	var tag := Label3D.new()
	tag.name = "Tag"
	tag.font = FONT
	tag.font_size = 54
	tag.outline_size = 14
	tag.pixel_size = 0.01
	tag.modulate = C_GOLD
	tag.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	tag.no_depth_test = true
	tag.position = Vector3(0, 2.0, 0)
	n.add_child(tag)
	tower_nodes[h.id] = n
	_refresh_hero_tag()
	_ring_fx(_v3(h.pos, 0.2), 1.6, C_GOLD, 0.6)
	_dust_fx(_v3(h.pos, 0.2), 10, 1.0)
	_sfx("hero_place", -2.0, 0.0)
	n.scale = Vector3(0.5, 1.6, 0.5)
	var tw := create_tween()
	tw.tween_property(n, "scale", Vector3.ONE, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _refresh_hero_tag() -> void:
	if sim.hero == null or not tower_nodes.has(sim.hero.id):
		return
	var tag: Label3D = tower_nodes[sim.hero.id].get_node("Tag")
	tag.text = "LV %d" % sim.hero.level


func _refresh_tower_node(t: Dictionary) -> void:
	var n: Node3D = tower_nodes[t.id]
	var s: float = 1.0 + 0.04 * t.level
	n.scale = Vector3(s, s, s)
	var deco: Node3D = n.get_node("Deco")
	for c in deco.get_children():
		c.queue_free()
	var col := C_GOLD
	if t.branch == "A":
		col = Color(1.0, 0.45, 0.15)
	elif t.branch == "B":
		col = Color(0.25, 0.8, 1.0)
	var r: float = float(defs.towers[t.type].get("model_scale", 0.56)) * 1.62
	if t.level >= 3:
		var tor := TorusMesh.new()
		tor.inner_radius = r - 0.06
		tor.outer_radius = r
		tor.rings = 28
		tor.ring_segments = 4
		_mi(tor, _mat("ring_" + t.branch, col, {"emit": col, "emit_e": 1.4}), deco, Vector3(0, 0.08, 0))
	for i in t.level:
		var a: float = PI * 0.5 + (i - (t.level - 1) * 0.5) * 0.3
		_mi(_sph(0.075, 8), _mat("pip_" + t.branch, col, {"emit": col, "emit_e": 1.6}), deco,
			Vector3(cos(a) * r, 0.16, sin(a) * r))


# =================================================================== robots
func _make_robot(type: String) -> Node3D:
	var d: Dictionary = defs.enemies[type]
	var root := Node3D.new()
	var model: Node3D = (_res("res://assets/robots/%s.glb" % type) as PackedScene).instantiate()
	model.scale = Vector3.ONE * float(d.get("model_scale", 0.9))
	model.name = "Model"
	root.add_child(model)
	root.set_meta("legsA", model.find_children("LegA*", "", true, false))
	root.set_meta("legsB", model.find_children("LegB*", "", true, false))
	root.set_meta("body", model.find_child("Body", true, false))
	root.set_meta("punch", 0.0)
	var h: float = float(d.get("bar_h", 1.4))
	if d.get("boss", false):
		var tag := Label3D.new()
		tag.text = str(d.name)
		tag.font = FONT
		tag.font_size = 80
		tag.outline_size = 18
		tag.pixel_size = 0.011
		tag.modulate = Color(1, 0.35, 0.3)
		tag.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		tag.no_depth_test = true
		tag.position = Vector3(0, h + 0.6, 0)
		root.add_child(tag)
	if d.has("shield"):
		var bm := StandardMaterial3D.new()
		bm.albedo_color = Color(0.4, 0.85, 1.0, 0.22)
		bm.emission_enabled = true
		bm.emission = Color(0.2, 0.7, 1.0)
		bm.emission_energy_multiplier = 0.8
		bm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		bm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		bm.cull_mode = BaseMaterial3D.CULL_DISABLED
		var br: float = 0.75 if not d.get("boss", false) else 2.2
		var bubble := _mi(_sph(br, 16), bm, root, Vector3(0, br * 0.85, 0))
		bubble.name = "Bubble"
	var mark := TorusMesh.new()
	mark.inner_radius = 0.28
	mark.outer_radius = 0.36
	mark.rings = 16
	mark.ring_segments = 4
	var mk := _mi(mark, _mat("expose_mark", Color(1, 0.8, 0.2), {"emit": Color(1, 0.7, 0.1), "emit_e": 2.0, "unshaded": true}), root, Vector3(0, h + 0.25, 0))
	mk.name = "Mark"
	mk.visible = false
	var bar := Node3D.new()
	bar.name = "Bar"
	bar.position = Vector3(0, h, 0)
	root.add_child(bar)
	var bw := 2.0 if d.get("boss", false) else 0.8
	var q := QuadMesh.new()
	q.size = Vector2(bw, 0.22 if d.get("boss", false) else 0.12)
	_mi(q, _mat("bar_bg", Color(0.08, 0.04, 0.04), {"unshaded": true, "billboard": true, "nodepth": true}), bar)
	var fg := _mi(q, _mat("bar_fg", Color(0.4, 1.0, 0.3), {"unshaded": true, "billboard": true, "nodepth": true}), bar, Vector3(0, 0, 0.01))
	fg.name = "Fg"
	bar.visible = false
	return root


# =================================================================== fx
func _ring_fx(pos: Vector3, radius: float, col: Color, life := 0.4) -> void:
	var tor := TorusMesh.new()
	tor.inner_radius = 0.86
	tor.outer_radius = 1.0
	tor.rings = 32
	tor.ring_segments = 4
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	var n := _mi(tor, m, self, pos, Vector3.ZERO, Vector3(0.2, 0.05, 0.2))
	effects.append({"node": n, "t": 0.0, "life": life, "kind": "ring", "r": radius, "mat": m})


func _float_text(pos: Vector3, text: String, col: Color, size := 56) -> void:
	if not Progress.setting("popups") and text.begins_with("+"):
		return
	var l := Label3D.new()
	l.text = text
	l.font = FONT
	l.font_size = size
	l.outline_size = 14
	l.outline_modulate = Color(0.15, 0.08, 0.02)
	l.pixel_size = 0.01
	l.modulate = col
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.position = pos
	add_child(l)
	effects.append({"node": l, "t": 0.0, "life": 0.9, "kind": "text"})


func _debris_fx(pos: Vector3, count: int, big := false) -> void:
	var cols := [Color(0.86, 0.88, 0.92), Color(0.5, 0.54, 0.6), Color(0.12, 0.13, 0.16)]
	for i in count:
		var col: Color = cols[i % 3]
		var sz := randf_range(0.08, 0.16) * (2.0 if big else 1.0)
		var c := _mi(_box(sz, sz, sz), _mat("debris_%d" % (i % 3), col, {"metal": 0.4, "rough": 0.4}), self, pos)
		var a := randf() * TAU
		var sp := randf_range(1.5, 3.5) * (1.8 if big else 1.0)
		effects.append({"node": c, "t": 0.0, "life": randf_range(0.5, 0.8), "kind": "debris",
			"v": Vector3(cos(a) * sp, randf_range(3, 6), sin(a) * sp)})
	for i in (count + 2):
		var s := _mi(_box(0.04, 0.04, 0.22), _mat("spark", Color(1, 0.3, 0.1), {"emit": Color(1, 0.25, 0.05), "emit_e": 3.0, "unshaded": true}), self, pos)
		var a2 := randf() * TAU
		var v := Vector3(cos(a2), randf_range(0.4, 1.4), sin(a2)) * randf_range(4, 7)
		s.look_at_from_position(pos, pos + v, Vector3.UP if absf(v.normalized().y) < 0.95 else Vector3.RIGHT)
		effects.append({"node": s, "t": 0.0, "life": 0.3, "kind": "spark", "v": v})
	var f := _mi(_sph(0.5, 10), _mat("flash", Color(1, 0.7, 0.4, 0.8), {"emit": Color(1, 0.5, 0.2), "emit_e": 3.0, "unshaded": true}), self, pos)
	effects.append({"node": f, "t": 0.0, "life": 0.18, "kind": "flash", "s": 1.6 if big else 0.8})


func _dust_fx(pos: Vector3, count: int, spread := 0.6) -> void:
	for i in count:
		var d := _mi(_sph(0.18, 6), _mat("dust", Color(0.78, 0.68, 0.5, 0.7), {"unshaded": true}), self, pos)
		var a := TAU * i / count + randf() * 0.4
		effects.append({"node": d, "t": 0.0, "life": randf_range(0.35, 0.6), "kind": "dust",
			"v": Vector3(cos(a), 0.6, sin(a)) * spread * randf_range(1.2, 2.2)})


func _boulder_drop_fx(target: Vector3, delay: float) -> void:
	var b := _mi(_sph(0.35, 6), _mat("drop_rock", Color(0.5, 0.48, 0.45)), self, target + Vector3(0, 9, 0))
	b.visible = false
	effects.append({"node": b, "t": -delay, "life": 0.45, "kind": "fall", "from": target + Vector3(0.6, 9, -0.4), "to": target + Vector3(0, 0.3, 0)})


func _update_effects(dt: float) -> void:
	var keep := []
	var landed := []
	for fx in effects:
		fx.t += dt
		var n: Node3D = fx.node
		var k: float = clampf(fx.t / fx.life, 0.0, 1.0) if fx.life != INF else 0.0
		match fx.kind:
			"portal":
				var ring: Node3D = n.get_meta("spin")
				ring.scale = Vector3.ONE * (1.0 + 0.05 * sin(time_s * 4.0))
				var core: Node3D = n.get_meta("core")
				core.rotation.y += dt * 2.0
			"fire":
				fx.f1.scale = Vector3(1, 1.0 + 0.15 * sin(time_s * 13.0), 1)
				fx.f2.scale = Vector3(1, 1.0 + 0.2 * sin(time_s * 17.0 + 1.0), 1)
				fx.light.light_energy = float(fx.base_e) * (0.9 + 0.2 * sin(time_s * 11.0))
			"lava":
				var pulse := 0.5 + 0.5 * sin((time_s + fx.t) * 2.2)
				fx.light.light_energy = 0.6 + 0.5 * pulse
				var pm: StandardMaterial3D = fx.pool.material_override
				pm.emission_energy_multiplier = 0.7 + 0.6 * pulse
				fx.t -= dt
			"ring":
				var r: float = fx.r * (0.3 + 0.7 * sqrt(k))
				n.scale = Vector3(r, 0.05, r)
				fx.mat.albedo_color.a = 1.0 - k
			"text":
				n.position.y += dt * 1.6
				n.scale = Vector3.ONE * (1.0 + 0.4 * maxf(0.0, 0.15 - fx.t) / 0.15)
				n.modulate.a = 1.0 - k * k
			"debris":
				fx.v.y -= 16.0 * dt
				n.position += fx.v * dt
				if n.position.y < 0.05:
					n.position.y = 0.05
					fx.v *= 0.4
				n.rotation += Vector3(9, 6, 4) * dt
				n.scale = Vector3.ONE * (1.0 - k * k)
			"spark":
				fx.v.y -= 10.0 * dt
				n.position += fx.v * dt
				n.scale = Vector3.ONE * (1.0 - k)
			"flash":
				n.scale = Vector3.ONE * fx.s * (0.6 + k * 1.2)
				n.visible = k < 0.95
			"dust":
				n.position += fx.v * dt
				fx.v *= 0.9
				n.scale = Vector3.ONE * (0.6 + k * 1.6)
				n.transparency = k
			"fall":
				n.visible = fx.t >= 0.0
				n.position = fx.from.lerp(fx.to, k * k)
				n.rotation += Vector3(5, 3, 2) * dt
				if fx.t >= fx.life:
					landed.append(fx.to)
		if fx.t >= fx.life:
			n.queue_free()
		else:
			keep.append(fx)
	effects = keep
	for p in landed:
		_dust_fx(p, 7, 1.0)
		shake = maxf(shake, 0.35)


# =================================================================== loop
func _process(delta: float) -> void:
	time_s += delta
	_fit_modals()
	if paused:
		_update_hud(0.0)
		return
	_auto_start(delta)
	if started and sim.state != "lost":
		accum += delta * speed
		var steps := 0
		while accum >= TICK and steps < MAX_STEPS_PER_FRAME:
			sim.step()
			accum -= TICK
			steps += 1
		if steps == MAX_STEPS_PER_FRAME:
			accum = 0.0
	_handle_events()
	_sync_visuals(clampf(accum / TICK, 0.0, 1.0))
	_update_effects(delta)
	_update_hud(delta)
	shake = maxf(0.0, shake - delta * 2.5)
	var sk := shake if Progress.setting("shake") else 0.0
	cam.position = cam_base + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)) * sk * sk * 0.6


## Once the player has started wave 1, later waves start by themselves (if Auto-start is on).
func _auto_start(delta: float) -> void:
	if not started or demo or sim.wave < 1 or overlay.visible or not Progress.setting("auto_start"):
		auto_t = -1.0
		return
	if sim.can_start_wave() and sim.enemies.is_empty() and (sim.wave < sim.total_waves or sim.endless):
		if auto_t < 0.0:
			auto_t = 2.0
		auto_t -= delta * speed
		if auto_t <= 0.0:
			auto_t = -1.0
			sim.start_wave()
	else:
		auto_t = -1.0


func _fire_sfx(u: Dictionary) -> void:
	var t: String = u.type
	if t in ["boulder_catapult", "torsion_catapult"]:
		_sfx("catapult", -8.0, 0.15, 0.05)
	elif t == "bronze_archer":
		_sfx("arrow", -6.0, 0.15, 0.05)
	else:
		_sfx("throw", -8.0, 0.15, 0.05)


func _handle_events() -> void:
	for ev in sim.events:
		match ev.e:
			"place":
				_spawn_tower_node(sim.get_tower(ev.id))
			"hero_place":
				_spawn_hero_node()
			"hero_level":
				_refresh_hero_tag()
				if sim.hero != null:
					_float_text(_v3(sim.hero.pos, 2.5), "LEVEL %d!" % ev.level, C_GOLD, 60)
					_ring_fx(_v3(sim.hero.pos, 0.3), 1.6, C_GOLD, 0.6)
					if sim.ability_unlocked() and ev.level == int(sim.hero_def.ability.get("unlock", 3)):
						_toast("%s unlocked!  Press the hero button to use it." % sim.hero_def.ability.name, C_GOLD)
						toast_t = 3.5
				_sfx("level_up", -4.0, 0.0, 0.3)
			"ability":
				_ability_fx(ev)
			"upgrade":
				var t = sim.get_tower(ev.id)
				_refresh_tower_node(t)
				_ring_fx(_v3(t.pos, 0.3), 1.4, C_GOLD, 0.5)
				_float_text(_v3(t.pos, 2.0), "UPGRADED!", C_GOLD, 50)
				_sfx("upgrade")
				if ev.id == selected:
					_show_tower_panel(ev.id)
			"sell":
				if tower_nodes.has(ev.id):
					_dust_fx(tower_nodes[ev.id].position + Vector3(0, 0.2, 0), 10, 1.0)
					tower_nodes[ev.id].queue_free()
					tower_nodes.erase(ev.id)
				_sfx("coin", -2.0)
			"spawn":
				var e = sim._enemy_by_id(ev.id)
				if e != null:
					var n := _make_robot(e.type)
					n.position = _v3(e.pos)
					add_child(n)
					enemy_nodes[ev.id] = n
					if e.boss:
						shake = 1.0
						_sfx("boss_roar_bronze" if e.type == "siege_crawler" else "boss_roar", -6.0, 0.0, 2.0)
						_banner("THE %s HAS ARRIVED" % str(defs.enemies[e.type].name), Color(1, 0.35, 0.3))
			"hit":
				if enemy_nodes.has(ev.id):
					enemy_nodes[ev.id].set_meta("punch", 1.0)
			"shield_break":
				if enemy_nodes.has(ev.id):
					_ring_fx(enemy_nodes[ev.id].position + Vector3(0, 0.7, 0), 1.0, Color(0.4, 0.9, 1.0), 0.3)
				_sfx("shield_break", -10.0, 0.1, 0.15)
			"shield_up":
				_sfx("shield_up", -16.0, 0.1, 0.5)
			"heal":
				if enemy_nodes.has(ev.id):
					_ring_fx(enemy_nodes[ev.id].position + Vector3(0, 0.3, 0), ev.radius, Color(0.3, 1.0, 0.4), 0.5)
				_sfx("heal", -12.0, 0.05, 0.4)
			"kill":
				if enemy_nodes.has(ev.id):
					var n2: Node3D = enemy_nodes[ev.id]
					var big: bool = defs.enemies[ev.type].get("boss", false)
					_debris_fx(n2.position + Vector3(0, 0.7 if not big else 2.0, 0), 14 if big else 5, big)
					_float_text(n2.position + Vector3(0, 1.5, 0), "+%d" % ev.bounty, C_GOLD, 46 if not big else 90)
					n2.queue_free()
					enemy_nodes.erase(ev.id)
					if big:
						shake = 1.3
						_sfx("boss_death", 0.0, 0.0)
					else:
						_sfx("robot_death", -4.0, 0.15, 0.03)
						_sfx("coin", -14.0, 0.05, 0.06)
			"leak":
				if enemy_nodes.has(ev.id):
					enemy_nodes[ev.id].queue_free()
					enemy_nodes.erase(ev.id)
				_toast("-%d lives!" % ev.lives, Color(1, 0.4, 0.35))
				_sfx("life_lost", -4.0, 0.0, 0.3)
				shake = maxf(shake, 0.45)
			"fire":
				_animate_fire(ev.id)
				var u = sim.get_unit(ev.id)
				if u != null:
					_fire_sfx(u)
			"slam":
				_animate_fire(ev.id)
				var u2 = sim.get_unit(ev.id)
				if u2 != null:
					_ring_fx(_v3(u2.pos, 0.2), ev.radius, Color(1, 0.8, 0.45), 0.35)
					_dust_fx(_v3(u2.pos + u2.facing * 0.8, 0.2), 5, 0.7)
					_sfx("spear" if u2.type in ["spear_guard", "kira"] else "club", -4.0, 0.12, 0.05)
			"pulse":
				_animate_fire(ev.id)
				var u3 = sim.get_unit(ev.id)
				if u3 != null:
					var pcol := Color(0.4, 1.0, 0.5)
					if u3.type == "sun_priest":
						pcol = Color(1.0, 0.85, 0.3)
					elif u3.type == "mara":
						pcol = Color(0.75, 0.5, 1.0)
					if u3.get("branch", "") == "B":
						pcol = Color(1, 0.5, 0.1)
					_ring_fx(_v3(u3.pos, 0.25), ev.radius, pcol, 0.6)
					if tower_nodes.has(ev.id) and tower_nodes[ev.id].has_meta("orb"):
						var orb: Node3D = tower_nodes[ev.id].get_meta("orb")
						orb.scale = Vector3.ONE * 2.2
				_sfx("pulse", -7.0, 0.1, 0.08)
			"proj":
				var p = _proj_by_id(ev.id)
				if p != null:
					proj_nodes[ev.id] = _make_projectile(p)
			"impact":
				if proj_nodes.has(ev.pid):
					proj_nodes[ev.pid].queue_free()
					proj_nodes.erase(ev.pid)
				if ev.splash > 0.0:
					_ring_fx(_v3(ev.pos, 0.2), ev.splash, Color(1, 0.65, 0.3), 0.3)
					_dust_fx(_v3(ev.pos, 0.2), 6, ev.splash)
					_sfx("boulder_land", -6.0, 0.15, 0.08)
					shake = maxf(shake, 0.18)
				else:
					_sfx("rock_hit", -10.0, 0.2, 0.05)
				if ev.crit:
					_float_text(_v3(ev.pos, 1.8), "CRIT!", Color(1, 0.35, 0.25), 44)
			"summon":
				var be = sim._enemy_by_id(ev.id)
				if be != null:
					_ring_fx(_v3(be.pos, 0.3), 2.8, Color(1, 0.2, 0.15), 0.6)
					_sfx("summon", -6.0, 0.05, 0.5)
			"wave_start":
				_banner("WAVE %d" % ev.wave, C_TEXT)
				_sfx("wave_horn", -3.0, 0.03, 0.5)
			"wave_clear":
				waves_cleared += 1
				_toast("Wave %d cleared!  +%d gold" % [ev.wave, ev.bonus], C_GOLD)
				_sfx("coin", -4.0, 0.0)
			"victory":
				_show_overlay(true)
			"defeat":
				_show_overlay(false)
	sim.events.clear()


func _make_projectile(p: Dictionary) -> Node3D:
	var src: Dictionary = p.src
	var u = sim.get_unit(int(src.get("tower_id", -1)))
	var utype: String = u.type if u != null else ""
	var dt: String = str(src.get("dtype", ""))
	var root := Node3D.new()
	root.position = _v3(p.pos, 1.3)
	add_child(root)
	if utype == "bronze_archer":
		var shaft := _mat("arrow_fire" if dt == "fire" else "arrow", Color(1, 0.5, 0.1) if dt == "fire" else Color(0.45, 0.3, 0.15),
			{"emit": Color(1, 0.4, 0.05), "emit_e": 2.0} if dt == "fire" else {})
		_mi(_box(0.05, 0.05, 0.6), shaft, root)
		_mi(_cyl(0.0, 0.06, 0.14, 4), _mat("arrow_tip", Color(0.7, 0.45, 0.18), {"metal": 0.5}), root, Vector3(0, 0, -0.34), Vector3(-PI * 0.5, 0, 0))
		root.set_meta("arrow", true)
		return root
	if utype == "tarek":
		_mi(_box(0.26, 0.16, 0.16), _mat("hot_hammer", Color(0.9, 0.45, 0.15), {"emit": Color(1, 0.4, 0.1), "emit_e": 1.2}), root)
		_mi(_box(0.05, 0.05, 0.3), _mat("wood_dark", Color(0.3, 0.17, 0.08)), root, Vector3(0, 0, 0.15))
		root.set_meta("spin", true)
		return root
	var size := 0.11
	var col := Color(0.6, 0.58, 0.55)
	var opts := {}
	if p.kind == "lob":
		size = 0.26
	if dt == "fire":
		col = Color(1, 0.5, 0.1)
		opts = {"emit": Color(1, 0.4, 0.05), "emit_e": 2.5}
	elif dt == "blunt" and p.kind == "homing":
		size = 0.17
	_mi(_sph(size, 6), _mat("proj_%s" % col.to_html(), col, opts), root)
	root.set_meta("spin", true)
	return root


func _ability_fx(ev: Dictionary) -> void:
	var hp := _v3(ev.pos, 0.3)
	match str(ev.ability):
		"stone_rain":
			var i := 0
			for p in ev.hits:
				_boulder_drop_fx(_v3(p), i * 0.06)
				i += 1
			_banner("STONE RAIN!", Color(0.9, 0.8, 0.6))
			_sfx("ab_stone_rain", 0.0, 0.0, 0.5)
		"earthquake":
			_ring_fx(hp, 26.0, Color(0.75, 0.55, 0.3), 1.0)
			_ring_fx(hp, 14.0, Color(0.85, 0.65, 0.35), 0.7)
			for e in sim.enemies:
				_dust_fx(_v3(e.pos, 0.2), 3, 0.6)
			shake = 1.4
			_banner("EARTHQUAKE!", Color(0.85, 0.6, 1.0))
			_sfx("ab_earthquake", 0.0, 0.0, 0.5)
		"solar_flare":
			_ring_fx(hp, float(ev.radius), Color(1, 0.85, 0.3), 0.7)
			_ring_fx(hp, float(ev.radius) * 0.6, Color(1, 0.95, 0.6), 0.5)
			var f := _mi(_sph(1.0, 12), _mat("flare", Color(1, 0.85, 0.4, 0.6), {"emit": Color(1, 0.8, 0.3), "emit_e": 3.0, "unshaded": true}), self, hp + Vector3(0, 1.0, 0))
			effects.append({"node": f, "t": 0.0, "life": 0.35, "kind": "flash", "s": 2.5})
			shake = 0.7
			_banner("SOLAR FLARE!", C_GOLD)
			_sfx("ab_solar_flare", 0.0, 0.0, 0.5)
		"forge_fury":
			for t in sim.towers:
				_ring_fx(_v3(t.pos, 0.3), 1.3, Color(1, 0.5, 0.15), 0.6)
			_banner("FORGE FURY!", Color(1, 0.6, 0.2))
			_sfx("ab_forge_fury", 0.0, 0.0, 0.5)


func _proj_by_id(id: int):
	for p in sim.projectiles:
		if p.id == id:
			return p
	return null


func _animate_fire(id: int) -> void:
	if not tower_nodes.has(id):
		return
	var n: Node3D = tower_nodes[id]
	if not n.has_meta("arm"):
		return
	var u = sim.get_unit(id)
	if u == null:
		return
	var arm: Node3D = n.get_meta("arm")
	var rest: float = arm.get_meta("rest")
	var sw: Array = _unit_def(u).get("swing", [-0.6, 1.0])
	var dur: float = clampf(float(u.stats.cooldown) * 0.7, 0.18, 0.6) / float(speed)
	var tw := create_tween()
	tw.tween_property(arm, "rotation:x", rest + float(sw[0]), dur * 0.35).set_trans(Tween.TRANS_SINE)
	tw.tween_property(arm, "rotation:x", rest + float(sw[1]), dur * 0.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_property(arm, "rotation:x", rest, dur * 0.45).set_trans(Tween.TRANS_SINE)


func _sync_visuals(alpha: float) -> void:
	for e in sim.enemies:
		if not enemy_nodes.has(e.id):
			continue
		var n: Node3D = enemy_nodes[e.id]
		var p: Vector2 = e.prev_pos.lerp(e.pos, alpha)
		n.position = _v3(p)
		var dir := sim.dir_at(e.dist, e.pi)
		n.rotation.y = lerp_angle(n.rotation.y, _yaw(dir), 0.25)
		var stunned: bool = sim.tick < e.stun_until
		var slowed: bool = sim.tick < e.slow_until
		var rate: float = 0.0 if stunned else (5.0 if slowed else 10.0) * float(e.speed) / 1.8
		var ph: float = time_s * maxf(rate, 0.001) * 1.6 + e.id
		var swing: float = 0.0 if stunned else sin(ph) * 0.55
		for l in n.get_meta("legsA"):
			l.rotation.x = swing
		for l in n.get_meta("legsB"):
			l.rotation.x = -swing
		var body = n.get_meta("body")
		if body != null:
			var bob: float = absf(sin(ph)) * 0.05
			if e.type in ["scout", "carrier", "repair_drone"]:
				bob = sin(time_s * 5.0 + e.id) * 0.08
			body.position.y = bob
			body.rotation.z = sin(time_s * 40.0) * 0.12 if stunned else 0.0
		var punch: float = n.get_meta("punch")
		if punch > 0.0:
			n.set_meta("punch", maxf(0.0, punch - 0.18))
			var model: Node3D = n.get_node("Model")
			var sc: float = float(defs.enemies[e.type].get("model_scale", 0.9)) * (1.0 + punch * 0.12)
			model.scale = Vector3(sc, sc * (1.0 - punch * 0.08), sc)
		var bubble: MeshInstance3D = n.get_node_or_null("Bubble")
		if bubble != null:
			bubble.visible = e.shield > 0.0
			if bubble.visible:
				var bmat: StandardMaterial3D = bubble.material_override
				bmat.albedo_color.a = 0.1 + 0.2 * clampf(e.shield / maxf(e.max_shield, 1.0), 0.0, 1.0)
		var mark: Node3D = n.get_node("Mark")
		mark.visible = sim.tick < e.expose_until
		if mark.visible:
			mark.rotation.y = time_s * 3.0
		var bar: Node3D = n.get_node("Bar")
		if e.hp < e.max_hp:
			bar.visible = true
			var fg: MeshInstance3D = bar.get_node("Fg")
			var f: float = clampf(e.hp / e.max_hp, 0.0, 1.0)
			fg.scale.x = maxf(f, 0.001)
			fg.position.x = -(1.0 - f) * (fg.mesh as QuadMesh).size.x * 0.5
	var pdt := get_process_delta_time()
	for p in sim.projectiles:
		if not proj_nodes.has(p.id):
			continue
		var pn: Node3D = proj_nodes[p.id]
		var newp: Vector3
		if p.kind == "lob":
			var k: float = clampf((p.t + alpha * TICK) / p.flight, 0.0, 1.0)
			newp = _v3(p.start.lerp(p.aim, k), 1.0 + 3.4 * 4.0 * k * (1.0 - k))
		else:
			newp = pn.position.lerp(_v3(p.pos, 1.1), 0.6)
		var dv := newp - pn.position
		pn.position = newp
		if pn.has_meta("arrow"):
			var dn := dv.normalized()
			if dv.length_squared() > 0.000001 and absf(dn.y) < 0.98:
				pn.look_at(newp + dv, Vector3.UP)
		elif pn.has_meta("spin"):
			pn.rotation += Vector3(8, 5, 0) * pdt
	var units: Array = sim.towers.duplicate()
	if sim.hero != null:
		units.append(sim.hero)
	for t in units:
		if not tower_nodes.has(t.id):
			continue
		var tn: Node3D = tower_nodes[t.id]
		if tn.has_meta("yaw"):
			var yaw_node: Node3D = tn.get_meta("yaw")
			yaw_node.rotation.y = lerp_angle(yaw_node.rotation.y, _yaw(t.facing), 0.2)
		if tn.has_meta("orb"):
			var orb: Node3D = tn.get_meta("orb")
			orb.scale = orb.scale.lerp(Vector3.ONE * (1.0 + 0.1 * sin(time_s * 4.0)), 0.1)
		var buff: Node3D = tn.get_node("Buff")
		buff.visible = t.get("buffed", false) and not t.get("is_hero", false)
		if buff.visible:
			buff.rotation.y = time_s * 2.5
			buff.position.y = 2.15 + 0.08 * sin(time_s * 3.0 + t.id)


# =================================================================== input
func _ground_point(screen: Vector2) -> Vector2:
	var o := cam.project_ray_origin(screen)
	var d := cam.project_ray_normal(screen)
	if absf(d.y) < 0.0001:
		return Vector2.INF
	var t := -o.y / d.y
	var p := o + d * t
	return Vector2(p.x, p.z)


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST or what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		if started and overlay != null and not overlay.visible and not paused and not demo:
			_set_paused(true)


func _unhandled_input(event: InputEvent) -> void:
	if not started:
		return
	if event is InputEventKey and event.pressed and not event.echo and event.keycode in [KEY_ESCAPE, KEY_P]:
		if paused:
			if settings_panel.visible:
				settings_panel.visible = false
			else:
				_set_paused(false)
		elif event.keycode == KEY_ESCAPE and (placing != "" or selected != -1):
			_cancel_placing()
			_deselect()
		elif not overlay.visible:
			_set_paused(true)
		return
	if paused:
		return
	if event is InputEventMouseMotion and placing != "":
		_move_ghost(_ground_point(event.position))
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			_cancel_placing()
			_deselect()
			return
		if event.button_index != MOUSE_BUTTON_LEFT:
			return
		var gp := _ground_point(event.position)
		if placing == HERO_PLACING:
			_move_ghost(gp)
			var herr := sim.hero_placement_error(gp)
			if herr == "":
				sim.place_hero(gp)
				_cancel_placing()
				_handle_events()
				_select(sim.hero.id)
			else:
				_toast(herr, Color(1, 0.45, 0.4))
				_sfx("error", -4.0, 0.0)
			return
		if placing != "":
			_move_ghost(gp)
			var err := sim.placement_error(placing, gp)
			if err == "":
				var id := sim.place_tower(placing, gp)
				_cancel_placing()
				_handle_events()
				_select(id)
			else:
				_toast(err, Color(1, 0.45, 0.4))
				_sfx("error", -4.0, 0.0)
			return
		if sim.hero != null and sim.hero.pos.distance_to(gp) <= 0.8:
			_select(sim.hero.id)
			_sfx("click", -6.0)
			return
		var t = sim.tower_at(gp)
		if t != null:
			_select(t.id)
			_sfx("click", -6.0)
		else:
			_deselect()
	elif event is InputEventKey and event.pressed:
		var types := sim.tower_types()
		match event.keycode:
			KEY_SPACE:
				_on_start_pressed()
			KEY_Q:
				_on_hero_button()
			KEY_1, KEY_2, KEY_3, KEY_4:
				var i: int = event.keycode - KEY_1
				if i < types.size():
					_begin_placing(types[i])


func _begin_placing(type: String) -> void:
	_sfx("click", -6.0)
	_deselect()
	if placing == type:
		_cancel_placing()
		return
	var r := 0.0
	var foot := 0.0
	if type == HERO_PLACING:
		r = float(sim.hero_def.base.range)
		foot = Sim.HERO_RADIUS
	else:
		if sim.gold < sim.tower_cost(type):
			_toast("Not enough gold", Color(1, 0.45, 0.4))
			_sfx("error", -4.0, 0.0)
			return
		r = float(defs.towers[type].base.range)
		foot = float(defs.towers[type].radius)
	placing = type
	for c in ghost.get_children():
		if c != ghost_range and c != ghost_foot:
			c.queue_free()
	ghost.add_child(_make_hero_visual(sim.hero_id) if type == HERO_PLACING else _make_tower_visual(type))
	ghost_range.scale = Vector3(r, 1, r)
	ghost_foot.scale = Vector3(foot, 1, foot)
	ghost.visible = true
	_move_ghost(Vector2(-1.0, 0.0))
	_update_shop_highlight()
	_toast("Tap the map to place %s" % (str(sim.hero_def.name) if type == HERO_PLACING else str(defs.towers[type].name)), C_TEXT)


func _move_ghost(p: Vector2) -> void:
	if p == Vector2.INF or placing == "":
		return
	ghost.position = _v3(p)
	var err := sim.hero_placement_error(p) if placing == HERO_PLACING else sim.placement_error(placing, p)
	ghost_foot.material_override = _mat("foot_ok", Color(0.2, 1, 0.3, 0.45), {"unshaded": true}) if err == "" \
		else _mat("foot_bad", Color(1, 0.2, 0.2, 0.55), {"unshaded": true})
	ghost_range.material_override = _mat("range_g", Color(1, 1, 1, 0.18), {"unshaded": true}) if err == "" \
		else _mat("range_bad", Color(1, 0.3, 0.3, 0.16), {"unshaded": true})


func _cancel_placing() -> void:
	placing = ""
	ghost.visible = false
	_update_shop_highlight()


func _select(id: int) -> void:
	_cancel_placing()
	selected = id
	side_scroll.scroll_vertical = 0
	_show_tower_panel(id)


func _deselect() -> void:
	selected = -1
	sel_range.visible = false
	aura_range.visible = false
	tower_box.visible = false
	tower_actions.visible = false
	shop_box.visible = true


func _on_start_pressed() -> void:
	if not started:
		return
	if sim.start_wave():
		_sfx("click", -6.0)


func _on_hero_button() -> void:
	if not started:
		return
	if sim.hero == null:
		_begin_placing(HERO_PLACING)
	elif sim.ability_ready():
		sim.use_ability()
		_handle_events()
	elif not sim.ability_unlocked():
		_toast("%s unlocks at hero level %d" % [sim.hero_def.ability.name, int(sim.hero_def.ability.get("unlock", 3))], C_TEXT)
	else:
		_toast("%s is recharging" % sim.hero_def.ability.name, C_TEXT)


# =================================================================== HUD
func _style(col: Color, radius := 16, border := Color(0, 0, 0, 0), bw := 4) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = col
	sb.set_corner_radius_all(radius)
	sb.set_content_margin_all(12)
	if border.a > 0:
		sb.set_border_width_all(bw)
		sb.border_color = border
	sb.shadow_color = Color(0, 0, 0, 0.35)
	sb.shadow_size = 6
	sb.shadow_offset = Vector2(0, 4)
	return sb


## Small text is bumped up so it stays readable on phones.
func _fs(size: int) -> int:
	if size <= 22:
		return size + 4
	if size <= 26:
		return size + 3
	return size


func _button(text: String, col: Color, font := 28) -> Button:
	font = _fs(font)
	var b := Button.new()
	b.text = text
	b.add_theme_font_size_override("font_size", font)
	var normal := _style(col, 18, col.darkened(0.45), 4)
	normal.border_width_bottom = 9
	var hover := _style(col.lightened(0.1), 18, col.darkened(0.4), 4)
	hover.border_width_bottom = 9
	var pressed := _style(col.darkened(0.08), 18, col.darkened(0.45), 4)
	pressed.border_width_bottom = 4
	pressed.content_margin_top = 17
	var dis := _style(Color(0.3, 0.26, 0.22), 18, Color(0.2, 0.17, 0.14), 4)
	dis.border_width_bottom = 9
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("disabled", dis)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.add_theme_color_override("font_color", Color.WHITE)
	b.add_theme_color_override("font_hover_color", Color.WHITE)
	b.add_theme_color_override("font_pressed_color", Color.WHITE)
	b.add_theme_color_override("font_disabled_color", Color(0.62, 0.58, 0.52))
	b.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.55))
	b.add_theme_constant_override("outline_size", 6)
	if "autowrap_mode" in b:
		b.set("autowrap_mode", TextServer.AUTOWRAP_WORD_SMART)
	return b


func _label(text: String, size := 28, col := C_TEXT, outline := 9) -> Label:
	size = _fs(size)
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color(0.12, 0.06, 0.02, 0.95))
	l.add_theme_constant_override("outline_size", outline)
	return l


func _icon(tex: Texture2D, size := 52) -> TextureRect:
	var r := TextureRect.new()
	r.texture = tex
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	r.custom_minimum_size = Vector2(size, size)
	return r


func _build_hud() -> void:
	var ui_theme := Theme.new()
	ui_theme.default_font = FONT
	ui_theme.default_font_size = 28
	for sbn in ["VScrollBar", "HScrollBar"]:
		var track := _style(Color(0.08, 0.05, 0.03, 0.9), 10)
		track.set_content_margin_all(11)
		track.shadow_size = 0
		var grab := _style(Color(0.78, 0.6, 0.3), 10)
		grab.set_content_margin_all(11)
		grab.shadow_size = 0
		var grab_h := _style(Color(0.95, 0.75, 0.38), 10)
		grab_h.set_content_margin_all(11)
		grab_h.shadow_size = 0
		ui_theme.set_stylebox("scroll", sbn, track)
		ui_theme.set_stylebox("scroll_focus", sbn, track)
		ui_theme.set_stylebox("grabber", sbn, grab)
		ui_theme.set_stylebox("grabber_highlight", sbn, grab_h)
		ui_theme.set_stylebox("grabber_pressed", sbn, grab_h)
	var layer := CanvasLayer.new()
	add_child(layer)
	var root := Control.new()
	root.theme = ui_theme
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(root)
	ui_root = root

	# --- top-left stat bar
	var top := PanelContainer.new()
	top.add_theme_stylebox_override("panel", _style(Color(0.14, 0.09, 0.05, 0.82), 22, C_PANEL_EDGE, 4))
	top.position = Vector2(20, 16)
	root.add_child(top)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 14)
	top.add_child(hb)
	hb.add_child(_icon(ICON_GOLD))
	lbl_gold = _label("", 40, C_GOLD)
	lbl_gold.custom_minimum_size.x = 120
	hb.add_child(lbl_gold)
	hb.add_child(_icon(ICON_LIVES))
	lbl_lives = _label("", 40, Color(1, 0.55, 0.5))
	lbl_lives.custom_minimum_size.x = 82
	hb.add_child(lbl_lives)
	hb.add_child(_icon(ICON_WAVE))
	lbl_wave = _label("", 40, Color(0.88, 0.94, 1))
	hb.add_child(lbl_wave)

	# --- pause button (top-right of the play area)
	btn_pause = _button("II", Color(0.36, 0.28, 0.2), 34)
	btn_pause.anchor_left = 1.0
	btn_pause.anchor_right = 1.0
	btn_pause.offset_left = -SIDEBAR_W - 108
	btn_pause.offset_right = -SIDEBAR_W - 20
	btn_pause.offset_top = 16
	btn_pause.offset_bottom = 100
	btn_pause.tooltip_text = "Pause (Esc)"
	btn_pause.pressed.connect(func():
		_sfx("click", -6.0)
		_set_paused(true))
	root.add_child(btn_pause)

	# --- right sidebar
	var side := PanelContainer.new()
	var side_sb := _style(C_PANEL, 0, C_PANEL_EDGE, 0)
	side_sb.border_width_left = 6
	side_sb.shadow_size = 12
	side_sb.set_content_margin_all(14)
	side.add_theme_stylebox_override("panel", side_sb)
	side.anchor_left = 1.0
	side.anchor_right = 1.0
	side.anchor_bottom = 1.0
	side.offset_left = -SIDEBAR_W
	side.clip_contents = true
	root.add_child(side)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 10)
	side.add_child(col)
	var era := _label(_era().to_upper() + "  -  " + str(map.name) + ("   T%d" % Progress.timeline() if Progress.timeline() > 1 else ""), 26, Color(1, 0.78, 0.45))
	era.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(era)

	# hero card
	hero_card = PanelContainer.new()
	hero_card.add_theme_stylebox_override("panel", _style(Color(0.26, 0.18, 0.1), 16, C_GOLD.darkened(0.3), 3))
	col.add_child(hero_card)
	var hrow := HBoxContainer.new()
	hrow.add_theme_constant_override("separation", 10)
	hero_card.add_child(hrow)
	hrow.add_child(_icon(_icon_tex(sim.hero_id), 72))
	var hcol := VBoxContainer.new()
	hcol.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hcol.add_theme_constant_override("separation", 2)
	hrow.add_child(hcol)
	lbl_hero_name = _label(str(sim.hero_def.name).get_slice(" ", 0), 22, C_GOLD, 6)
	lbl_hero_name.clip_text = true
	hcol.add_child(lbl_hero_name)
	lbl_hero_level = _label("", 18, C_TEXT, 5)
	hcol.add_child(lbl_hero_level)
	var xp_bg := ColorRect.new()
	xp_bg.color = Color(0.1, 0.06, 0.03)
	xp_bg.custom_minimum_size = Vector2(130, 10)
	hcol.add_child(xp_bg)
	hero_xp_fill = ColorRect.new()
	hero_xp_fill.color = C_GOLD
	hero_xp_fill.size = Vector2(0, 10)
	xp_bg.add_child(hero_xp_fill)
	btn_hero = _button("", Color(0.2, 0.55, 0.2), 20)
	btn_hero.custom_minimum_size = Vector2(118, 72)
	btn_hero.pressed.connect(_on_hero_button)
	hrow.add_child(btn_hero)

	# the middle of the sidebar scrolls (shop, or the selected tower's stats and upgrades)
	side_scroll = ScrollContainer.new()
	side_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	side_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	side_scroll.scroll_deadzone = 12
	col.add_child(side_scroll)
	var mid := VBoxContainer.new()
	mid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mid.add_theme_constant_override("separation", 10)
	side_scroll.add_child(mid)
	shop_box = VBoxContainer.new()
	shop_box.add_theme_constant_override("separation", 10)
	shop_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mid.add_child(shop_box)
	var types := sim.tower_types()
	for i in types.size():
		var type: String = types[i]
		var def: Dictionary = defs.towers[type]
		var c := Color(def.color[0], def.color[1], def.color[2])
		var b := _button("%s\n%d gold" % [def.name, sim.tower_cost(type)], c.lerp(Color(0.45, 0.3, 0.18), 0.35), 26)
		b.icon = _icon_tex(type)
		b.expand_icon = true
		b.add_theme_constant_override("icon_max_width", 92)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(0, 112)
		b.tooltip_text = "%s  [%d]\n%s" % [def.lineage, i + 1, def.desc]
		b.pressed.connect(_begin_placing.bind(type))
		shop_box.add_child(b)
		shop_buttons[type] = b

	tower_box = VBoxContainer.new()
	tower_box.add_theme_constant_override("separation", 8)
	tower_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tower_box.visible = false
	mid.add_child(tower_box)
	var head := HBoxContainer.new()
	tower_box.add_child(head)
	tower_icon = _icon(_icon_tex(types[0]), 84)
	head.add_child(tower_icon)
	lbl_t_name = _label("", 30, Color(1, 0.88, 0.55))
	lbl_t_name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_t_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_t_name.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	head.add_child(lbl_t_name)
	var close := _button("X", Color(0.42, 0.3, 0.22), 26)
	close.custom_minimum_size = Vector2(60, 60)
	close.pressed.connect(func():
		_sfx("click", -6.0)
		_deselect())
	head.add_child(close)
	lbl_t_info = _label("", 21, Color(0.95, 0.9, 0.82), 6)
	lbl_t_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tower_box.add_child(lbl_t_info)
	up_box = VBoxContainer.new()
	up_box.add_theme_constant_override("separation", 10)
	tower_box.add_child(up_box)
	tower_actions = VBoxContainer.new()
	tower_actions.add_theme_constant_override("separation", 8)
	tower_actions.visible = false
	col.add_child(tower_actions)
	btn_target = _button("", Color(0.3, 0.3, 0.42), 22)
	btn_target.custom_minimum_size = Vector2(0, 56)
	btn_target.tooltip_text = "First: closest to your base. Strong: toughest robot (use for bosses). Close: nearest. Last: furthest back."
	btn_target.pressed.connect(func():
		if selected != -1:
			sim.cycle_target(selected)
			_sfx("click", -6.0)
			_show_tower_panel(selected))
	tower_actions.add_child(btn_target)
	btn_sell = _button("", Color(0.62, 0.22, 0.16), 24)
	btn_sell.custom_minimum_size = Vector2(0, 64)
	btn_sell.pressed.connect(func():
		if selected != -1 and sim.get_tower(selected) != null:
			sim.sell_tower(selected)
			_handle_events()
			_deselect())
	tower_actions.add_child(btn_sell)

	var ctrl := HBoxContainer.new()
	ctrl.add_theme_constant_override("separation", 8)
	col.add_child(ctrl)
	var small := VBoxContainer.new()
	small.add_theme_constant_override("separation", 8)
	ctrl.add_child(small)
	btn_speed = _button("1x", Color(0.24, 0.36, 0.58), 28)
	btn_speed.custom_minimum_size = Vector2(100, 58)
	btn_speed.pressed.connect(func():
		_sfx("click", -6.0)
		speed = 1 if speed == 3 else speed + 1
		btn_speed.text = "%dx" % speed)
	small.add_child(btn_speed)
	btn_auto = _button("", Color(0.32, 0.3, 0.36), 18)
	btn_auto.custom_minimum_size = Vector2(100, 46)
	btn_auto.tooltip_text = "Auto-start: after you start wave 1, the next waves start on their own."
	btn_auto.pressed.connect(func():
		_sfx("click", -6.0)
		Progress.set_setting("auto_start", not Progress.setting("auto_start"))
		_refresh_auto_button())
	small.add_child(btn_auto)
	btn_start = _button("START\nWAVE 1", Color(0.2, 0.58, 0.18), 30)
	btn_start.icon = ICON_PLAY
	btn_start.expand_icon = true
	btn_start.add_theme_constant_override("icon_max_width", 40)
	btn_start.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_start.custom_minimum_size = Vector2(0, 112)
	btn_start.pressed.connect(_on_start_pressed)
	ctrl.add_child(btn_start)

	# --- toast + banner
	toast = _label("", 36, C_TEXT)
	toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	toast.anchor_right = 1.0
	toast.offset_right = -SIDEBAR_W
	toast.offset_top = 120
	toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(toast)
	banner = _label("", 92, C_TEXT, 18)
	banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	banner.anchor_right = 1.0
	banner.anchor_bottom = 1.0
	banner.offset_right = -SIDEBAR_W
	banner.offset_bottom = -260
	banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	banner.pivot_offset = Vector2(700, 300)
	root.add_child(banner)

	# --- victory/defeat overlay
	overlay = _modal(root)
	var ov: VBoxContainer = overlay.get_meta("box")
	lbl_overlay = _label("", 84, C_GOLD, 16)
	lbl_overlay.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ov.add_child(lbl_overlay)
	lbl_overlay_sub = _label("", 30, C_TEXT, 8)
	lbl_overlay_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_overlay_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ov.add_child(lbl_overlay_sub)
	var ob := HBoxContainer.new()
	ob.alignment = BoxContainer.ALIGNMENT_CENTER
	ob.add_theme_constant_override("separation", 24)
	ov.add_child(ob)
	var again := _button("PLAY AGAIN", Color(0.24, 0.4, 0.62), 32)
	again.custom_minimum_size = Vector2(300, 96)
	again.pressed.connect(func():
		Progress.current_map = map_id
		get_tree().reload_current_scene())
	ob.add_child(again)
	btn_endless = _button("ENDLESS MODE", Color(0.5, 0.28, 0.6), 32)
	btn_endless.custom_minimum_size = Vector2(300, 96)
	btn_endless.pressed.connect(func():
		sim.endless = true
		sim.state = "ready"
		overlay.visible = false
		_banner("ENDLESS", Color(0.85, 0.6, 1))
		_toast("How long can you hold out?", Color(0.85, 0.6, 1)))
	ob.add_child(btn_endless)
	var ob2 := HBoxContainer.new()
	ob2.alignment = BoxContainer.ALIGNMENT_CENTER
	ob2.add_theme_constant_override("separation", 24)
	ov.add_child(ob2)
	var to_select := _button("MAP SELECT", Color(0.42, 0.3, 0.2), 28)
	to_select.custom_minimum_size = Vector2(300, 80)
	to_select.pressed.connect(func():
		Progress.current_map = ""
		Progress.open_map_select = true
		get_tree().reload_current_scene())
	ob2.add_child(to_select)
	var nm := Progress.next_map(map_id, map_order)
	var btn_next := _button("NEXT MAP", Color(0.2, 0.58, 0.18), 28)
	btn_next.custom_minimum_size = Vector2(300, 80)
	btn_next.pressed.connect(func():
		Progress.current_map = nm
		get_tree().reload_current_scene())
	btn_next.visible = false
	ob2.add_child(btn_next)
	overlay.set_meta("next", btn_next)
	var btn_tl := _button("BEGIN A NEW TIMELINE", Color(0.5, 0.2, 0.62), 30)
	btn_tl.custom_minimum_size = Vector2(624, 90)
	btn_tl.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	btn_tl.pressed.connect(func():
		_sfx("click")
		_confirm_new_timeline())
	btn_tl.visible = false
	ov.add_child(btn_tl)
	overlay.set_meta("timeline", btn_tl)
	overlay.visible = false

	# --- title screen
	title_screen = _modal(root, 0.55)
	var tb: VBoxContainer = title_screen.get_meta("box")
	var t1 := _label("AGE OF", 54, Color(1, 0.8, 0.5), 12)
	t1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tb.add_child(t1)
	var t2 := _label("TOWER DEFENSE", 104, C_GOLD, 22)
	t2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tb.add_child(t2)
	var t3 := _label("The machines came back through time to erase humanity.\nHold the line in every age.", 28, C_TEXT, 8)
	t3.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tb.add_child(t3)
	var play := _button("PLAY", Color(0.2, 0.58, 0.18), 52)
	play.custom_minimum_size = Vector2(380, 120)
	play.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_build_map_select(root)
	play.pressed.connect(func():
		_sfx("click")
		title_screen.visible = false
		map_select.visible = true)
	tb.add_child(play)
	var legacy_badge := _label("", 30, Color(0.6, 0.9, 1.0), 8)
	legacy_badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	legacy_badge.text = _legacy_badge_text()
	tb.add_child(legacy_badge)
	var trow := HBoxContainer.new()
	trow.alignment = BoxContainer.ALIGNMENT_CENTER
	trow.add_theme_constant_override("separation", 20)
	tb.add_child(trow)
	var t_legacy := _button("LEGACY", Color(0.18, 0.42, 0.6), 30)
	t_legacy.custom_minimum_size = Vector2(280, 80)
	t_legacy.pressed.connect(func():
		_sfx("click")
		_open_legacy())
	trow.add_child(t_legacy)
	var t_set := _button("SETTINGS", Color(0.36, 0.32, 0.4), 30)
	t_set.custom_minimum_size = Vector2(280, 80)
	t_set.pressed.connect(func():
		_sfx("click")
		_open_settings())
	trow.add_child(t_set)

	_build_pause_menu(root)
	settings_panel = _modal(root, 0.5)
	settings_panel.visible = false
	legacy_panel = _modal(root, 0.6)
	legacy_panel.visible = false


func _eras() -> Array:
	var out := []
	for m in Defs.map_list():
		if not str(m.era) in out:
			out.append(str(m.era))
	return out


func _build_map_select(root: Control) -> void:
	map_select = _modal(root, 0.6)
	var box: VBoxContainer = map_select.get_meta("box")
	box.set_meta("want_w", 1300.0)
	box.add_theme_constant_override("separation", 14)
	if Progress.timeline() > 1:
		var tl := _label("TIMELINE %d   -   robots +%d%% tougher   -   +%d%% Legacy XP" % [Progress.timeline(),
			int(round((Progress.timeline_hp_mult() - 1.0) * 100)), int(round((Progress.timeline_xp_mult() - 1.0) * 100))], 26, Color(0.85, 0.6, 1.0), 7)
		tl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		box.add_child(tl)
	# era tabs
	var tabs := HBoxContainer.new()
	tabs.alignment = BoxContainer.ALIGNMENT_CENTER
	tabs.add_theme_constant_override("separation", 16)
	box.add_child(tabs)
	var rows := {}
	var tab_buttons := {}
	var default_tab := str(Progress.data.get("tab", ""))
	for era_name in _eras():
		var row := HBoxContainer.new()
		row.alignment = BoxContainer.ALIGNMENT_CENTER
		row.add_theme_constant_override("separation", 26)
		box.add_child(row)
		rows[era_name] = row
		var era_open := false
		for m in Defs.map_list():
			if str(m.era) != era_name:
				continue
			era_open = era_open or Progress.is_unlocked(m.id)
			_map_card(row, m)
		if era_open and default_tab == "":
			pass
		var tbtn := _button(era_name.to_upper() if era_open else era_name.to_upper() + "  (LOCKED)", Color(0.45, 0.32, 0.2), 30)
		tbtn.custom_minimum_size = Vector2(320, 70)
		tabs.add_child(tbtn)
		tab_buttons[era_name] = tbtn
		if era_open:
			if default_tab == "" or not Progress.is_unlocked(_first_map_of(default_tab)):
				default_tab = era_name
	var show_tab := func(era_name: String) -> void:
		for k in rows:
			rows[k].visible = k == era_name
			var b: Button = tab_buttons[k]
			b.modulate = Color(1.25, 1.2, 0.95) if k == era_name else Color(0.7, 0.7, 0.7)
		Progress.data.tab = era_name
	for era_name in tab_buttons:
		tab_buttons[era_name].pressed.connect(func():
			_sfx("click")
			show_tab.call(era_name))
	if default_tab == "":
		default_tab = _eras()[0]
	show_tab.call(default_tab)
	# hero select
	var hhead := _label("CHOOSE YOUR HERO", 30, C_GOLD, 8)
	hhead.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(hhead)
	var hrow := HFlowContainer.new()
	hrow.alignment = FlowContainer.ALIGNMENT_CENTER
	hrow.add_theme_constant_override("h_separation", 14)
	hrow.add_theme_constant_override("v_separation", 14)
	box.add_child(hrow)
	var hblurb := _label("", 20, Color(0.92, 0.86, 0.76), 5)
	hblurb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hblurb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hblurb.custom_minimum_size = Vector2(0, 60)
	var hero_buttons := {}
	var pick := func(hid: String) -> void:
		Progress.set_hero(hid)
		for k in hero_buttons:
			hero_buttons[k].modulate = Color(1.2, 1.15, 0.9) if k == hid else Color(0.62, 0.62, 0.62)
		var hd: Dictionary = defs.heroes.heroes[hid]
		hblurb.text = "%s, %s (%s).  %s\nAbility: %s. %s" % [hd.name, hd.title, hd.era, hd.blurb, hd.ability.name, hd.ability.desc]
	for hid in defs.heroes.heroes:
		var hd2: Dictionary = defs.heroes.heroes[hid]
		var open := Progress.hero_unlocked(hd2)
		var hname := str(hd2.name).split(" ")[0]
		var hb := _button(hname if open else "%s\nLEGACY LV %d" % [hname, int(hd2.get("legacy_unlock", 1))],
			Color(hd2.color[0], hd2.color[1], hd2.color[2]).lerp(Color(0.3, 0.2, 0.12), 0.45 if open else 0.8), 24 if open else 20)
		hb.icon = _icon_tex(hid)
		hb.expand_icon = true
		hb.add_theme_constant_override("icon_max_width", 64)
		hb.custom_minimum_size = Vector2(250, 84)
		hb.pressed.connect(func():
			_sfx("click")
			if Progress.hero_unlocked(hd2):
				pick.call(hid)
			else:
				hblurb.text = "%s, %s.  Reach Legacy level %d to unlock.\nEarn Legacy XP by playing any map: every wave you clear counts." % [hd2.name, hd2.title, int(hd2.get("legacy_unlock", 1))])
		hrow.add_child(hb)
		hero_buttons[hid] = hb
	box.add_child(hblurb)
	var start_hero := Progress.hero()
	if not defs.heroes.heroes.has(start_hero) or not Progress.hero_unlocked(defs.heroes.heroes[start_hero]):
		start_hero = "ugo"
	pick.call(start_hero)
	var hint := _label("Beat a map to unlock the next.  Stars: 1 = win, 2 = lose 50 lives or fewer, 3 = lose 10 or fewer.  Your hero joins every match for free.", 18, Color(0.85, 0.78, 0.68), 5)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(hint)
	var brow := HBoxContainer.new()
	brow.alignment = BoxContainer.ALIGNMENT_CENTER
	brow.add_theme_constant_override("separation", 18)
	box.add_child(brow)
	var pts := Progress.points_free()
	var m_legacy := _button("LEGACY  LV %d%s" % [Progress.legacy_level(), ("   (%d POINT%s!)" % [pts, "" if pts == 1 else "S"]) if pts > 0 else ""],
		Color(0.18, 0.42, 0.6), 22)
	m_legacy.custom_minimum_size = Vector2(420, 60)
	if pts > 0:
		m_legacy.set_meta("pulse", true)
	m_legacy.pressed.connect(func():
		_sfx("click")
		_open_legacy())
	brow.add_child(m_legacy)
	var m_set := _button("SETTINGS", Color(0.36, 0.32, 0.4), 22)
	m_set.custom_minimum_size = Vector2(220, 60)
	m_set.pressed.connect(func():
		_sfx("click")
		_open_settings())
	brow.add_child(m_set)
	if Progress.can_new_timeline(map_order):
		var m_tl := _button("NEW TIMELINE", Color(0.5, 0.2, 0.62), 22)
		m_tl.custom_minimum_size = Vector2(260, 60)
		m_tl.pressed.connect(func():
			_sfx("click")
			_confirm_new_timeline())
		brow.add_child(m_tl)
	if OS.is_debug_build():
		var dev := _button("UNLOCK ALL MAPS (test)", Color(0.35, 0.3, 0.45), 18)
		dev.custom_minimum_size = Vector2(320, 60)
		dev.pressed.connect(func():
			Progress.unlock_all(map_order)
			Progress.current_map = ""
			Progress.open_map_select = true
			get_tree().reload_current_scene())
		brow.add_child(dev)
	box.move_child(brow, 0)   # keep Legacy / Settings / New Timeline visible without scrolling
	map_select.visible = false


func _first_map_of(era_name: String) -> String:
	for m in Defs.map_list():
		if str(m.era) == era_name:
			return m.id
	return ""


func _map_card(row: HBoxContainer, m: Dictionary) -> void:
	var mid: String = m.id
	var unlocked := Progress.is_unlocked(mid)
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", _style(Color(0.24, 0.16, 0.1) if unlocked else Color(0.16, 0.13, 0.11), 20,
		C_PANEL_EDGE if unlocked else Color(0.3, 0.25, 0.2), 4))
	card.custom_minimum_size = Vector2(390, 0)
	row.add_child(card)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	card.add_child(v)
	var thumb_holder := Control.new()
	thumb_holder.custom_minimum_size = Vector2(362, 180)
	v.add_child(thumb_holder)
	var at := AtlasTexture.new()
	at.atlas = load("res://assets/textures/ground_%s.png" % mid)
	at.region = Rect2(312, 234, 1560, 884)
	var thumb := TextureRect.new()
	thumb.texture = at
	thumb.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	thumb.stretch_mode = TextureRect.STRETCH_SCALE
	thumb.set_anchors_preset(Control.PRESET_FULL_RECT)
	thumb.modulate = Color.WHITE if unlocked else Color(0.35, 0.35, 0.35)
	thumb_holder.add_child(thumb)
	if not unlocked:
		var cc := CenterContainer.new()
		cc.set_anchors_preset(Control.PRESET_FULL_RECT)
		thumb_holder.add_child(cc)
		cc.add_child(_icon(ICON_LOCK, 90))
	v.add_child(_label(str(m.name), 32, C_TEXT if unlocked else Color(0.6, 0.55, 0.5), 8))
	var dc := {"Normal": Color(0.55, 0.9, 0.45), "Hard": Color(1, 0.7, 0.3), "Brutal": Color(1, 0.4, 0.35)}
	v.add_child(_label(str(m.difficulty).to_upper(), 20, dc.get(m.difficulty, C_TEXT), 6))
	var bl := _label(str(m.blurb), 17, Color(0.9, 0.85, 0.78), 5)
	bl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	bl.custom_minimum_size = Vector2(362, 60)
	v.add_child(bl)
	var stars := HBoxContainer.new()
	for k in 3:
		stars.add_child(_icon(ICON_STAR if k < Progress.stars(mid) else ICON_STAR_EMPTY, 36))
	v.add_child(stars)
	var go := _button("PLAY" if unlocked else "LOCKED", Color(0.2, 0.58, 0.18) if unlocked else Color(0.3, 0.27, 0.24), 28)
	go.disabled = not unlocked
	go.custom_minimum_size = Vector2(0, 66)
	go.pressed.connect(func():
		_sfx("click")
		Progress.save()
		Progress.current_map = mid
		get_tree().reload_current_scene())
	v.add_child(go)


func _modal(root: Control, dim := 0.45) -> Control:
	var shade := ColorRect.new()
	shade.color = Color(0.05, 0.03, 0.02, dim)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.add_child(center)
	var panel := PanelContainer.new()
	var sb := _style(Color(0.16, 0.1, 0.06, 0.95), 30, C_PANEL_EDGE, 6)
	sb.set_content_margin_all(30)
	sb.shadow_size = 24
	panel.add_theme_stylebox_override("panel", sb)
	center.add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.scroll_deadzone = 12
	panel.add_child(scroll)
	var box := VBoxContainer.new()
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_theme_constant_override("separation", 22)
	box.set_meta("want_w", 900.0)
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(box)
	shade.set_meta("box", box)
	shade.set_meta("scroll", scroll)
	modals.append(shade)
	return shade


## Keeps every open dialog inside the screen: narrower when the UI is scaled up, scrollable when too tall.
func _fit_modals() -> void:
	if ui_root == null:
		return
	var vp := ui_root.size
	for m in modals:
		if not is_instance_valid(m) or not m.visible:
			continue
		var box: VBoxContainer = m.get_meta("box")
		var scroll: ScrollContainer = m.get_meta("scroll")
		var w := minf(float(box.get_meta("want_w", 900.0)), vp.x - 120.0)
		box.custom_minimum_size.x = w
		var need := box.get_combined_minimum_size().y
		var bar := 26.0 if need > vp.y - 110.0 else 0.0
		scroll.custom_minimum_size = Vector2(w + bar, minf(need, vp.y - 110.0))


func _start_game() -> void:
	started = true
	title_screen.visible = false
	map_select.visible = false
	if not demo:
		music.play()
	_sfx("click")
	_toast("Place your hero (free), then pick towers on the right", C_TEXT)
	toast_t = 4.5


func _show_tower_panel(id: int) -> void:
	var t = sim.get_unit(id)
	if t == null:
		_deselect()
		return
	shop_box.visible = false
	tower_box.visible = true
	tower_actions.visible = true
	for c in up_box.get_children():
		c.queue_free()
	var s: Dictionary = sim._effective_stats(t)
	var rate := 1.0 / float(s.cooldown)
	var lines := ""
	if t.get("is_hero", false):
		var hd: Dictionary = sim.hero_def
		tower_icon.texture = _icon_tex(sim.hero_id)
		lbl_t_name.text = str(hd.name)
		var nxt := "MAX" if t.level >= sim.hero_levels.size() else "%d/%d XP" % [int(t.xp), int(sim.hero_levels[t.level])]
		lines = "%s  -  Level %d  (%s)\n" % [hd.title, t.level, nxt]
		lines += "Damage %s  Range %.1f  Attacks %.1f/sec\nKills %d\n" % [str(snappedf(float(s.damage), 0.1)), float(s.range), rate, t.kills]
		var au: Dictionary = hd.get("aura", {})
		lines += "Aura: %s\nAbility (level %d): %s. %s" % [hd.blurb, int(hd.ability.get("unlock", 3)), hd.ability.name, hd.ability.desc]
		btn_sell.visible = false
		aura_range.position = _v3(t.pos, 0.11)
		aura_range.scale = Vector3(sim.aura_radius(), 1, sim.aura_radius())
		aura_range.visible = not au.is_empty()
	else:
		var def: Dictionary = defs.towers[t.type]
		tower_icon.texture = _icon_tex(t.type)
		lbl_t_name.text = sim.tower_display_name(t)
		lines = "%s  -  Tier %d/5\n" % [def.lineage, t.level]
		lines += "Damage %s (%s)  Range %.1f\nAttacks %.1f/sec   Kills %d" % [str(snappedf(float(s.damage), 0.1)), s.dtype, float(s.range), rate, t.kills]
		if s.has("shots") and int(s.shots) > 1:
			lines += "\nArrows per volley %d" % int(s.shots)
		if s.has("splash") and float(s.splash) > 0:
			lines += "\nSplash %.1f" % float(s.splash)
		if s.has("slow"):
			lines += "   Slow %d%%" % int(float(s.slow) * 100)
		if s.has("armor_pierce"):
			lines += "\nPierces %d armor" % int(s.armor_pierce)
		if s.has("shred"):
			lines += "\nStrips %d armor per hit" % int(s.shred)
		if s.has("expose"):
			lines += "\nMarked robots take +%d%% damage" % int(float(s.expose) * 100)
		if t.buffed:
			lines += "\nBoosted by your hero!"
		if t.branch != "":
			lines += "\nPath %s: %s" % [t.branch, def.branches[t.branch].name]
		var opts := sim.upgrade_options(t)
		if opts.is_empty():
			up_box.add_child(_label("MAX TIER", 34, C_GOLD))
		for o in opts:
			var title: String = ("PATH %s: " % o.key) if o.get("branch_pick", false) else ""
			var bcol := Color(0.7, 0.36, 0.12) if o.key == "A" else (Color(0.14, 0.42, 0.62) if o.key == "B" else Color(0.26, 0.5, 0.2))
			var b := _button("%s%s\n%d gold  -  %s" % [title, o.name, o.cost, o.desc], bcol, 21)
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b.custom_minimum_size = Vector2(0, 110)
			b.set_meta("cost", o.cost)
			b.pressed.connect(func():
				if not sim.upgrade_tower(id, o.key):
					_toast("Not enough gold", Color(1, 0.45, 0.4))
					_sfx("error", -4.0, 0.0)
				_handle_events())
			up_box.add_child(b)
		if opts.size() == 2:
			up_box.add_child(_label("Choose one. The other path locks.", 20, Color(1, 0.72, 0.45), 6))
		btn_sell.visible = true
		btn_sell.text = "SELL  +%d gold" % sim.sell_value(t)
		aura_range.visible = false
	lbl_t_info.text = lines
	btn_target.visible = s.kind != "pulse"
	btn_target.text = "TARGET: %s" % str(t.target).to_upper()
	sel_range.position = _v3(t.pos, 0.12)
	sel_range.scale = Vector3(float(s.range), 1, float(s.range))
	sel_range.visible = true


func _update_shop_highlight() -> void:
	for type in shop_buttons:
		var b: Button = shop_buttons[type]
		b.modulate = Color(1.3, 1.3, 1.05) if type == placing else Color.WHITE


func _toast(text: String, col: Color) -> void:
	toast.text = text
	toast.add_theme_color_override("font_color", col)
	toast_t = 2.4


func _banner(text: String, col: Color) -> void:
	banner.text = text
	banner.add_theme_color_override("font_color", col)
	banner_t = 1.6


func _update_hero_card() -> void:
	var ab: Dictionary = sim.hero_def.ability
	if sim.hero == null:
		lbl_hero_level.text = "Ready to deploy"
		hero_xp_fill.size.x = 0
		btn_hero.text = "PLACE\nFREE"
		btn_hero.disabled = false
		btn_hero.modulate = Color(1.15, 1.15, 1.0) if placing == HERO_PLACING else Color.WHITE
		return
	btn_hero.modulate = Color.WHITE
	lbl_hero_level.text = "Level %d" % sim.hero.level
	hero_xp_fill.size.x = 130.0 * sim.hero_xp_progress()
	if not sim.ability_unlocked():
		btn_hero.text = "%s\nLVL %d" % [str(ab.name).to_upper(), int(ab.get("unlock", 3))]
		btn_hero.disabled = true
	elif sim.hero.ability_cd > 0.0:
		btn_hero.text = "%s\n%ds" % [str(ab.name).to_upper(), int(ceil(sim.hero.ability_cd))]
		btn_hero.disabled = true
	else:
		btn_hero.text = "%s\nREADY!" % str(ab.name).to_upper()
		btn_hero.disabled = false
		btn_hero.modulate = Color(1.0, 1.0, 1.0).lerp(Color(1.35, 1.25, 0.9), 0.5 + 0.5 * sin(time_s * 6.0))


func _update_hud(delta: float) -> void:
	lbl_gold.text = str(sim.gold)
	lbl_lives.text = str(sim.lives)
	lbl_wave.text = ("%d/%d" % [sim.wave, sim.total_waves]) if not (sim.endless or sim.wave > sim.total_waves) else ("%d  ENDLESS" % sim.wave)
	for type in shop_buttons:
		shop_buttons[type].disabled = sim.gold < sim.tower_cost(type)
	for b in up_box.get_children():
		if b is Button:
			b.disabled = sim.gold < int(b.get_meta("cost"))
	if sim.can_start_wave():
		btn_start.disabled = false
		btn_start.text = ("START\nWAVE %d" if sim.enemies.is_empty() else "SEND\nWAVE %d") % (sim.wave + 1)
		if auto_t >= 0.0:
			btn_start.text = "WAVE %d\nIN %d..." % [sim.wave + 1, int(ceil(auto_t / float(speed)))]
	else:
		btn_start.disabled = true
		btn_start.text = "WAVE %d" % sim.wave
	_update_hero_card()
	if toast_t > 0.0:
		toast_t -= delta
		toast.modulate.a = clampf(toast_t / 0.4, 0.0, 1.0)
	if banner_t > 0.0:
		banner_t -= delta
		var k := 1.6 - banner_t
		banner.modulate.a = clampf(minf(k / 0.15, banner_t / 0.4), 0.0, 1.0)
		banner.scale = Vector2.ONE * (1.0 + 0.25 * maxf(0.0, 0.15 - k) / 0.15)
	else:
		banner.modulate.a = 0.0


func _show_overlay(won: bool) -> void:
	overlay.visible = true
	_cancel_placing()
	if won:
		_sfx("victory")
		var earned := 0
		var newly := ""
		if not demo:
			var res: Array = Progress.record_win(map_id, sim.start_lives - sim.lives, map_order)
			earned = res[0]
			newly = res[1]
			first_clear = res[2]
			if newly != "":
				for m in Defs.map_list():
					if str(m.id) == newly:
						Progress.data.tab = str(m.era)
				Progress.save()
		var nb: Button = overlay.get_meta("next")
		nb.visible = Progress.next_map(map_id, map_order) != ""
		lbl_overlay.text = "VICTORY!"
		if earned > 0:
			lbl_overlay.text = "VICTORY!  %d/3 STARS" % earned
		lbl_overlay.add_theme_color_override("font_color", C_GOLD)
		var boss_name := str(defs.enemies[str(map.get("boss", "prime_walker"))].name).capitalize()
		lbl_overlay_sub.text = "The %s is scrap metal.\n%d robots destroyed  -  %d lives left" % [boss_name, sim.stats.kills, sim.lives]
		if newly != "":
			var nm_era := ""
			for m in Defs.map_list():
				if m.id == newly:
					nm_era = str(m.era)
			if nm_era != _era():
				lbl_overlay_sub.text += "\nNEW ERA UNLOCKED: %s!" % nm_era.to_upper()
				nb.text = "ENTER THE %s" % nm_era.to_upper()
		if not nb.visible:
			lbl_overlay_sub.text += "\nYou beat every map in this timeline! More ages are coming in future updates."
		(overlay.get_meta("timeline") as Button).visible = not demo and Progress.can_new_timeline(map_order)
		lbl_overlay_sub.text += _award_xp(true)
		btn_endless.visible = true
	else:
		_sfx("defeat")
		lbl_overlay.text = "THE CITY HAS FALLEN" if str(map.get("base", "cave")) == "city" else "THE CAVE HAS FALLEN"
		lbl_overlay.add_theme_color_override("font_color", Color(1, 0.45, 0.4))
		lbl_overlay_sub.text = "You held out until wave %d.\n%d robots destroyed." % [sim.wave, sim.stats.kills]
		lbl_overlay_sub.text += _award_xp(false)
		btn_endless.visible = false


# =================================================================== pause, settings, legacy
func _set_paused(on: bool) -> void:
	paused = on
	pause_menu.visible = on
	if on:
		_cancel_placing()
		var lbl: Label = pause_menu.get_meta("sub")
		lbl.text = "%s  -  %s\nWave %d of %d   -   %d lives" % [_era(), str(map.name), sim.wave, sim.total_waves, sim.lives]
	else:
		settings_panel.visible = false


func _build_pause_menu(root: Control) -> void:
	pause_menu = _modal(root, 0.55)
	var box: VBoxContainer = pause_menu.get_meta("box")
	box.set_meta("want_w", 620.0)
	box.add_theme_constant_override("separation", 16)
	var t := _label("PAUSED", 84, C_GOLD, 16)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(t)
	var sub := _label("", 26, C_TEXT, 7)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(sub)
	pause_menu.set_meta("sub", sub)
	var items := [
		["RESUME", Color(0.2, 0.58, 0.18), func(): _set_paused(false)],
		["SETTINGS", Color(0.36, 0.32, 0.4), func(): _open_settings()],
		["RESTART MAP", Color(0.24, 0.4, 0.62), func():
			_award_xp(false)
			Progress.current_map = map_id
			get_tree().reload_current_scene()],
		["QUIT TO MAP SELECT", Color(0.55, 0.26, 0.18), func():
			_award_xp(false)
			Progress.current_map = ""
			Progress.open_map_select = true
			get_tree().reload_current_scene()],
	]
	for it in items:
		var b := _button(it[0], it[1], 34)
		b.custom_minimum_size = Vector2(0, 92)
		var cb: Callable = it[2]
		b.pressed.connect(func():
			_sfx("click")
			cb.call())
		box.add_child(b)
	var note := _label("Waves you cleared still earn Legacy XP if you restart or quit.", 19, Color(0.85, 0.78, 0.68), 5)
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(note)
	pause_menu.visible = false


func _apply_settings() -> void:
	for pair in [["Music", "music"], ["SFX", "sfx"]]:
		var i := _bus(pair[0])
		var v := float(Progress.setting(pair[1]))
		AudioServer.set_bus_mute(i, v <= 0.01)
		AudioServer.set_bus_volume_db(i, linear_to_db(maxf(v, 0.01)))
	if world_env != null:
		world_env.glow_enabled = bool(Progress.setting("glow"))
	var sc := clampf(float(Progress.setting("ui_scale")), 0.8, 1.6)
	if not is_equal_approx(get_tree().root.content_scale_factor, sc):
		get_tree().root.content_scale_factor = sc
		if cam != null:
			_frame_camera()
	_refresh_auto_button()


func _refresh_auto_button() -> void:
	if btn_auto == null:
		return
	var on := bool(Progress.setting("auto_start"))
	btn_auto.text = "AUTO ON" if on else "AUTO OFF"
	btn_auto.modulate = Color(0.75, 1.35, 0.75) if on else Color.WHITE


func _toggle_button(key: String) -> Button:
	var b := _button("", Color(0.3, 0.3, 0.3), 24)
	b.custom_minimum_size = Vector2(160, 60)
	var paint := func():
		var on := bool(Progress.setting(key))
		b.text = "ON" if on else "OFF"
		b.modulate = Color(0.7, 1.5, 0.7) if on else Color(1.0, 0.85, 0.85)
	paint.call()
	b.pressed.connect(func():
		_sfx("click", -6.0)
		Progress.data.settings[key] = not bool(Progress.setting(key))
		paint.call()
		_apply_settings())
	return b


func _scale_picker() -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	var names := ["NORMAL", "LARGE", "HUGE"]
	var btns := []
	for i in Progress.UI_SCALES.size():
		var v: float = Progress.UI_SCALES[i]
		var b := _button(names[i], Color(0.3, 0.3, 0.36), 20)
		b.custom_minimum_size = Vector2(120, 60)
		btns.append(b)
		row.add_child(b)
		b.pressed.connect(func():
			_sfx("click", -6.0)
			Progress.data.settings.ui_scale = v
			_apply_settings()
			for j in btns.size():
				btns[j].modulate = Color(0.7, 1.5, 0.7) if j == i else Color.WHITE)
	for j in btns.size():
		btns[j].modulate = Color(0.7, 1.5, 0.7) if is_equal_approx(float(Progress.setting("ui_scale")), Progress.UI_SCALES[j]) else Color.WHITE
	return row


func _slider(key: String) -> HSlider:
	var sl := HSlider.new()
	sl.min_value = 0.0
	sl.max_value = 1.0
	sl.step = 0.05
	sl.value = float(Progress.setting(key))
	sl.custom_minimum_size = Vector2(320, 48)
	sl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var track := _style(Color(0.1, 0.06, 0.03), 8, C_PANEL_EDGE, 2)
	track.set_content_margin_all(6)
	track.shadow_size = 0
	sl.add_theme_stylebox_override("slider", track)
	var fill := _style(C_GOLD.darkened(0.15), 8)
	fill.set_content_margin_all(6)
	fill.shadow_size = 0
	sl.add_theme_stylebox_override("grabber_area", fill)
	sl.add_theme_stylebox_override("grabber_area_highlight", fill)
	sl.value_changed.connect(func(v: float):
		Progress.data.settings[key] = v
		_apply_settings())
	return sl


func _open_settings() -> void:
	var box: VBoxContainer = settings_panel.get_meta("box")
	for c in box.get_children():
		c.queue_free()
	box.set_meta("want_w", 760.0)
	box.add_theme_constant_override("separation", 16)
	var t := _label("SETTINGS", 64, C_GOLD, 14)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(t)
	var rows := [
		["Text and button size", _scale_picker()],
		["Music volume", _slider("music")],
		["Sound effects", _slider("sfx")],
		["Auto-start waves", _toggle_button("auto_start")],
		["Screen shake", _toggle_button("shake")],
		["Gold popups", _toggle_button("popups")],
		["Glow effects (turn off on slow phones)", _toggle_button("glow")],
	]
	for r in rows:
		var hb := HBoxContainer.new()
		hb.add_theme_constant_override("separation", 20)
		var l := _label(r[0], 28, C_TEXT, 7)
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		hb.add_child(l)
		hb.add_child(r[1])
		box.add_child(hb)
	var note := _label("Auto-start: after you start wave 1, each next wave starts 2 seconds after the last one is cleared.", 18, Color(0.85, 0.78, 0.68), 5)
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(note)
	var done := _button("DONE", Color(0.2, 0.58, 0.18), 34)
	done.custom_minimum_size = Vector2(0, 84)
	done.pressed.connect(func():
		_sfx("click")
		Progress.save()
		settings_panel.visible = false)
	box.add_child(done)
	settings_panel.get_parent().move_child(settings_panel, -1)
	settings_panel.visible = true


func _confirm_new_timeline() -> void:
	var dlg := _modal(ui_root, 0.7)
	var box: VBoxContainer = dlg.get_meta("box")
	box.set_meta("want_w", 1000.0)
	box.add_theme_constant_override("separation", 18)
	var nxt := Progress.timeline() + 1
	var lt: Dictionary = Progress.legacy.timeline
	var t := _label("BEGIN TIMELINE %d?" % nxt, 64, Color(0.85, 0.6, 1.0), 14)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(t)
	var story := _label("You won. But the machine you built to destroy the Data Center has already gone back in time to hunt humanity again. The war starts over in the Stone Age.", 26, C_TEXT, 6)
	story.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	story.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(story)
	var keep := _label("YOU KEEP:  your Legacy level, every perk you bought, and all unlocked heroes.", 26, Color(0.6, 1.0, 0.6), 6)
	keep.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(keep)
	var gain := _label("YOU GAIN:  +%d Legacy points, every perk can go %d rank higher, and +%d%% Legacy XP from every match." % [
		int(lt.bonus_points_per), int(lt.max_rank_per), int(round(float(lt.xp_per) * 100))], 26, C_GOLD, 6)
	gain.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(gain)
	var lose := _label("RESETS:  map unlocks and stars. Robots in the new timeline are %d%% tougher." % int(round(float(lt.robot_hp_per) * 100)), 26, Color(1, 0.6, 0.55), 6)
	lose.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(lose)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 24)
	box.add_child(row)
	var no := _button("NOT YET", Color(0.42, 0.3, 0.2), 32)
	no.custom_minimum_size = Vector2(300, 90)
	no.pressed.connect(func():
		_sfx("click")
		dlg.queue_free())
	row.add_child(no)
	var yes := _button("BEGIN TIMELINE %d" % nxt, Color(0.5, 0.2, 0.62), 32)
	yes.custom_minimum_size = Vector2(420, 90)
	yes.pressed.connect(func():
		_sfx("level_up")
		Progress.start_new_timeline(map_order)
		Progress.current_map = ""
		Progress.open_map_select = true
		get_tree().reload_current_scene())
	row.add_child(yes)


func _legacy_badge_text() -> String:
	var pr := Progress.legacy_progress()
	var t := "Legacy Level %d   -   %d / %d XP" % [Progress.legacy_level(), pr[0], pr[1]]
	if Progress.timeline() > 1:
		t = "Timeline %d   -   " % Progress.timeline() + t
	if Progress.points_free() > 0:
		t += "   -   %d point%s to spend!" % [Progress.points_free(), "" if Progress.points_free() == 1 else "s"]
	return t


func _map_meta() -> Dictionary:
	for m in Defs.map_list():
		if str(m.id) == map_id:
			return m
	return {}


## Grants Legacy XP for waves cleared since the last award (and the win bonus once). Returns text for the result screen.
func _award_xp(won: bool) -> String:
	if demo:
		return ""
	var meta := _map_meta()
	var xp := 0
	var new_waves := waves_cleared - xp_waves_awarded
	if new_waves > 0:
		xp += Progress.match_xp(meta, new_waves, false, false)
	xp_waves_awarded = waves_cleared
	if won and not xp_win_awarded:
		xp_win_awarded = true
		xp += Progress.match_xp(meta, 0, true, first_clear)
	if xp <= 0:
		return ""
	var lv: Array = Progress.add_xp(xp)
	var txt := "\n+%d LEGACY XP" % xp
	if first_clear and won:
		txt += " (first clear bonus!)"
	if lv[1] > lv[0]:
		txt += "\nLEGACY LEVEL %d!  +%d point%s for the Legacy tree" % [lv[1], lv[1] - lv[0], "" if lv[1] - lv[0] == 1 else "s"]
		for hid in defs.heroes.heroes:
			var u := int(defs.heroes.heroes[hid].get("legacy_unlock", 1))
			if u > lv[0] and u <= lv[1]:
				txt += "\nNEW HERO UNLOCKED: %s!" % str(defs.heroes.heroes[hid].name)
		_sfx("level_up", 0.0, 0.0, 0.0)
	return txt


func _open_legacy() -> void:
	_build_legacy_contents()
	legacy_panel.get_parent().move_child(legacy_panel, -1)
	legacy_panel.visible = true


func _build_legacy_contents() -> void:
	var box: VBoxContainer = legacy_panel.get_meta("box")
	for c in box.get_children():
		c.queue_free()
	box.set_meta("want_w", 1560.0)
	box.add_theme_constant_override("separation", 12)
	# header
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 30)
	box.add_child(head)
	head.add_child(_label("LEGACY", 64, C_GOLD, 14))
	var lvbox := VBoxContainer.new()
	lvbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lvbox.add_theme_constant_override("separation", 4)
	head.add_child(lvbox)
	var pr := Progress.legacy_progress()
	lvbox.add_child(_label("LEVEL %d" % Progress.legacy_level(), 36, Color(0.6, 0.9, 1.0), 8))
	var bar := ColorRect.new()
	bar.color = Color(0.08, 0.05, 0.03)
	bar.custom_minimum_size = Vector2(460, 18)
	lvbox.add_child(bar)
	var fill := ColorRect.new()
	fill.color = Color(0.4, 0.8, 1.0)
	fill.size = Vector2(460.0 * clampf(float(pr[0]) / maxf(float(pr[1]), 1.0), 0.0, 1.0), 18)
	bar.add_child(fill)
	lvbox.add_child(_label("%d / %d XP to the next level" % [pr[0], pr[1]], 19, Color(0.85, 0.85, 0.9), 5))
	var pts := Progress.points_free()
	var plbl := _label("%d POINT%s TO SPEND" % [pts, "" if pts == 1 else "S"], 36, C_GOLD if pts > 0 else Color(0.7, 0.65, 0.6), 9)
	plbl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(plbl)
	var intro_t := "Every battle adds to humanity's legacy. Each Legacy level gives 1 point. Bonuses carry into every map, every age and every new timeline."
	if Progress.timeline() > 1:
		intro_t += "\nTimeline %d bonus: +%d points, and every perk can go %d rank%s higher." % [Progress.timeline(), Progress.timeline_bonus_points(),
			Progress.timeline() - 1, "" if Progress.timeline() == 2 else "s"]
	var intro := _label(intro_t, 22, Color(0.92, 0.86, 0.76), 5)
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(intro)
	# branches
	var cols := HFlowContainer.new()
	cols.alignment = FlowContainer.ALIGNMENT_CENTER
	cols.add_theme_constant_override("h_separation", 20)
	cols.add_theme_constant_override("v_separation", 20)
	box.add_child(cols)
	for br in Progress.legacy.branches:
		var bc := Color(br.color[0], br.color[1], br.color[2])
		var col := VBoxContainer.new()
		col.add_theme_constant_override("separation", 8)
		col.custom_minimum_size = Vector2(500, 0)
		cols.add_child(col)
		var bl := _label(str(br.name), 32, bc.lightened(0.3), 8)
		bl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		col.add_child(bl)
		for p in br.perks:
			col.add_child(_perk_card(p, bc))
	# hero unlocks
	var hrow := HFlowContainer.new()
	hrow.alignment = FlowContainer.ALIGNMENT_CENTER
	hrow.add_theme_constant_override("h_separation", 22)
	box.add_child(hrow)
	hrow.add_child(_label("HERO UNLOCKS:", 22, C_GOLD, 6))
	for hid in defs.heroes.heroes:
		var hd: Dictionary = defs.heroes.heroes[hid]
		var open := Progress.hero_unlocked(hd)
		hrow.add_child(_icon(_icon_tex(hid), 44))
		hrow.add_child(_label("%s  LV %d%s" % [str(hd.name).split(" ")[0], int(hd.get("legacy_unlock", 1)), "  - READY" if open else ""], 20,
			Color(0.6, 1.0, 0.6) if open else Color(0.7, 0.66, 0.6), 5))
	# footer
	var foot := HBoxContainer.new()
	foot.alignment = BoxContainer.ALIGNMENT_CENTER
	foot.add_theme_constant_override("separation", 20)
	box.add_child(foot)
	var reset := _button("RESET POINTS (free)", Color(0.5, 0.28, 0.2), 22)
	reset.custom_minimum_size = Vector2(320, 70)
	reset.disabled = Progress.points_spent() == 0
	reset.pressed.connect(func():
		_sfx("coin")
		Progress.reset_perks()
		_build_legacy_contents())
	foot.add_child(reset)
	if OS.is_debug_build():
		var cheat := _button("+1000 XP (test)", Color(0.35, 0.3, 0.45), 20)
		cheat.custom_minimum_size = Vector2(240, 70)
		cheat.pressed.connect(func():
			Progress.add_xp(1000)
			_sfx("level_up")
			_build_legacy_contents())
		foot.add_child(cheat)
	var done := _button("DONE", Color(0.2, 0.58, 0.18), 30)
	done.custom_minimum_size = Vector2(320, 70)
	done.pressed.connect(func():
		_sfx("click")
		legacy_panel.visible = false
		if not started:
			# rebuild menus so hero locks and point counts refresh
			Progress.current_map = ""
			Progress.open_map_select = map_select.visible
			get_tree().reload_current_scene())
	foot.add_child(done)
	box.move_child(foot, 1)   # buttons right under the header so DONE never needs scrolling


func _perk_card(p: Dictionary, bc: Color) -> Control:
	var id: String = p.id
	var rank := Progress.perk_rank(id)
	var mx := Progress.perk_max(id)
	var card := PanelContainer.new()
	var sb := _style(Color(0.22, 0.15, 0.09) if rank == 0 else bc.darkened(0.62), 14, bc.darkened(0.2) if rank > 0 else Color(0.36, 0.27, 0.18), 3)
	sb.set_content_margin_all(10)
	sb.shadow_size = 0
	card.add_theme_stylebox_override("panel", sb)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 10)
	card.add_child(hb)
	var info := VBoxContainer.new()
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.add_theme_constant_override("separation", 0)
	hb.add_child(info)
	var top := HBoxContainer.new()
	info.add_child(top)
	var nm := _label(str(p.name), 24, C_TEXT, 6)
	nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(nm)
	top.add_child(_label("%d/%d" % [rank, mx], 22, C_GOLD if rank > 0 else Color(0.7, 0.65, 0.6), 6))
	var now_txt := ("Now: " + Progress.perk_text(id, rank)) if rank > 0 else str(p.desc)
	info.add_child(_label(now_txt, 17, Color(0.95, 0.9, 0.8) if rank > 0 else Color(0.8, 0.75, 0.68), 4))
	info.add_child(_label(("Next: " + Progress.perk_text(id, rank + 1)) if rank < mx else "MAXED", 17,
		Color(0.6, 0.95, 0.6) if rank < mx else C_GOLD, 4))
	var plus := _button("+", Color(0.2, 0.55, 0.2), 34)
	plus.custom_minimum_size = Vector2(64, 64)
	plus.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	plus.disabled = rank >= mx or Progress.points_free() < 1
	plus.pressed.connect(func():
		if Progress.buy_perk(id):
			_sfx("upgrade")
			_build_legacy_contents())
	hb.add_child(plus)
	return card


# =================================================================== test harness (screenshots, win-flow test)
func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png("user://" + name)
	print("SHOT ", ProjectSettings.globalize_path("user://" + name))


func _wait_ticks(n: int) -> void:
	var target := sim.tick + n
	while sim.tick < target:
		await get_tree().process_frame


func _demo_spot(type: String, hero_spot := false) -> Vector2:
	var r: float = float(sim.hero_def.base.range) if hero_spot else float(defs.towers[type].base.range)
	var best := Vector2.INF
	var best_score := -1
	var x := -14.0
	while x <= 14.0:
		var z := -7.5
		while z <= 7.5:
			var p := Vector2(x, z)
			var err := sim.hero_placement_error(p) if hero_spot else sim.placement_error(type, p)
			if err == "" or err == "Not enough gold":
				var sc := 0
				for pi in sim.paths.size():
					var d := 0.0
					while d < sim.paths[pi].length:
						if sim.pos_at(d, pi).distance_to(p) <= r:
							sc += 1
						d += 0.5
				if sc > best_score:
					best_score = sc
					best = p
			z += 0.75
		x += 0.75
	return best


func _demo_build(gold: int) -> Array:
	sim.gold += gold
	sim.place_hero(_demo_spot("", true))
	var types := sim.tower_types()
	var ids := []
	for i in [2, 0, 1, 3, 0, 0, 1, 2]:
		var type: String = types[i]
		var spot := _demo_spot(type)
		if spot != Vector2.INF:
			var id := sim.place_tower(type, spot)
			if id != -1:
				ids.append(id)
	for k in 3:
		for i in ids.size():
			var t = sim.get_tower(ids[i])
			sim.upgrade_tower(ids[i], "" if t.level < 2 else ("A" if i % 2 == 0 else "B"))
	_handle_events()
	return ids


## Plays the current map like a real player (one wave at a time) and reports the win flow.
func _run_autowin() -> void:
	await get_tree().process_frame
	_start_game()
	var ids := _demo_build(20000)
	for id in ids:
		for k in 3:
			var t = sim.get_tower(id)
			if t != null and t.level < 5:
				sim.upgrade_tower(id, t.branch if t.branch != "" else "A")
		sim.cycle_target(id)
	_handle_events()
	speed = 10
	var frames := 0
	while not overlay.visible and frames < 80000:
		if btn_start.disabled == false and sim.enemies.is_empty():
			btn_start.emit_signal("pressed")
		if sim.ability_ready() and sim.enemies.size() > 6:
			_on_hero_button()
		await get_tree().process_frame
		frames += 1
	print("AUTOWIN map=%s state=%s wave=%d lives=%d overlay=%s title=%s sub=%s next_visible=%s hero_lvl=%d" % [map_id, sim.state, sim.wave, sim.lives,
		overlay.visible, lbl_overlay.text, lbl_overlay_sub.text.replace("\n", " | "), (overlay.get_meta("next") as Button).visible, sim.hero.level if sim.hero != null else 0])
	print("AUTOWIN save=", JSON.stringify(Progress.data))
	get_tree().quit()


func _run_demo() -> void:
	var tag := map_id
	var args := OS.get_cmdline_user_args()
	for i in 3:
		await get_tree().process_frame
	if "--shoot-legacy" in args or "--shoot-settings" in args or "--shoot-title" in args:
		Progress.data.legacy_xp = 2650
		Progress.data.perks = {"start_gold": 2, "bounty": 1, "damage": 2, "hero_level": 1}
		map_select.queue_free()
		_build_map_select(title_screen.get_parent())
		if "--shoot-legacy" in args:
			title_screen.visible = false
			map_select.visible = true
			_open_legacy()
		elif "--shoot-settings" in args:
			_open_settings()
		for i in 3:
			await get_tree().process_frame
		await _shot("demo_menu.png")
		get_tree().quit()
		return
	if "--shoot-pause" in args:
		_start_game()
		_demo_build(3000)
		sim.start_wave()
		await _wait_ticks(int(6.0 / TICK))
		_set_paused(true)
		for i in 3:
			await get_tree().process_frame
		await _shot("demo_pause.png")
		_set_paused(false)
		demo = false   # let auto-start run like a real match
		while not sim.can_start_wave() or not sim.enemies.is_empty():
			await get_tree().process_frame
		await _wait_ticks(int(0.6 / TICK))
		await _shot("demo_autostart.png")
		print("AUTO wave=", sim.wave, " auto_t=", auto_t)
		await _wait_ticks(int(2.0 / TICK))
		print("AUTO after wait wave=", sim.wave)
		get_tree().quit()
		return
	if "--shoot-timeline" in args:
		Progress.data.cleared = map_order.duplicate()
		map_select.queue_free()
		_build_map_select(title_screen.get_parent())
		title_screen.visible = false
		map_select.visible = true
		_confirm_new_timeline()
		for i in 3:
			await get_tree().process_frame
		await _shot("demo_menu.png")
		get_tree().quit()
		return
	if "--shoot-select" in args:
		Progress.data.merge({"unlocked": ["mammoth_valley", "glacier_pass", "volcano_ridge", "river_delta"], "stars": {"mammoth_valley": 3, "glacier_pass": 2, "volcano_ridge": 1},
			"hero": "kira", "tab": "Bronze Age"}, true)
		map_select.queue_free()
		_build_map_select(title_screen.get_parent())
		title_screen.visible = false
		map_select.visible = true
		for i in 3:
			await get_tree().process_frame
		await _shot("demo_select.png")
		get_tree().quit()
		return
	_start_game()
	var ids := _demo_build(6000)
	speed = 3
	for w in 7:
		sim.start_wave()
		while not sim.can_start_wave() or not sim.enemies.is_empty():
			if sim.ability_ready() and sim.enemies.size() > 10:
				sim.use_ability()
			await get_tree().process_frame
	speed = 1
	sim.start_wave()   # wave 8
	await _wait_ticks(int(9.0 / TICK))
	_select(ids[1])
	await _wait_ticks(int(2.0 / TICK))
	await _shot("demo_%s_battle.png" % tag)
	_deselect()
	if "--ability" in args:
		sim.hero.ability_cd = 0.0
		sim.hero.level = maxi(sim.hero.level, 3)
		_select(sim.hero.id)
		sim.use_ability()
		await _wait_ticks(8)
		await _shot("demo_%s_ability.png" % tag)
		_deselect()
	if "--boss" in args:
		speed = 3
		while not sim.can_start_wave() or not sim.enemies.is_empty():
			await get_tree().process_frame
		sim.wave = sim.total_waves - 1
		speed = 1
		sim.start_wave()
		await _wait_ticks(int(14.0 / TICK))
		await _shot("demo_%s_boss.png" % tag)
	print("DEMO_DONE")
	get_tree().quit()
