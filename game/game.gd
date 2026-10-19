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
const PULSE_COLORS := {"druid": Color(0.5, 1.0, 0.4), "oracle": Color(1.0, 0.9, 0.5), "alchemist": Color(0.6, 1.0, 0.3),
	"war_drummer": Color(1.0, 0.85, 0.6), "tesla_coil": Color(0.6, 0.85, 1.0), "emp_tower": Color(0.4, 0.75, 1.0),
	"cryo_field": Color(0.7, 0.95, 1.0), "firewall": Color(1.0, 0.55, 0.15), "theron": Color(1.0, 0.9, 0.4), "ken": Color(0.95, 0.9, 0.3)}
const PULSE_SFX := {"tesla_coil": "zap", "emp_tower": "emp", "cryo_field": "freeze", "war_drummer": "drum", "firewall": "zap", "ken": "zap"}
const PROJ_SFX := {"javelin": "javelin", "bolt": "bolt", "bullet": "rifle", "cannonball": "cannon", "shell": "shell", "missile": "missile",
	"laser": "laser", "plasma": "plasma", "arc": "zap", "arrow": "arrow"}
const SFX_NAMES := ["portal_warp", "throw", "rock_hit", "club", "catapult", "boulder_land", "pulse", "robot_death", "boss_death", "coin",
	"place", "upgrade", "wave_horn", "life_lost", "boss_roar", "summon", "click", "error", "victory", "defeat",
	"arrow", "spear", "shield_up", "shield_break", "heal", "level_up", "hero_place", "ab_stone_rain", "ab_earthquake",
	"ab_solar_flare", "ab_forge_fury", "boss_roar_bronze", "airstrike", "bolt", "boss_roar_mech", "cannon", "cloak", "drum",
	"emp", "explosion", "flame", "freeze", "javelin", "laser", "missile", "musket", "plasma", "rifle", "shell", "steam", "swing", "zap",
	"anvil", "hammer_hit"]

# palette
const C_PANEL := Color(0.07, 0.09, 0.15, 0.96)
const C_PANEL_EDGE := Color(0.25, 0.52, 0.8)
const C_TEXT := Color(0.94, 0.97, 1.0)
const C_GOLD := Color(0.45, 0.9, 1.0)        # accent (titles, highlights): time-portal cyan
const C_COIN := Color(1.0, 0.82, 0.22)        # gold money only

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
var results_pages: Array = []    # Callables, one per results page
var results_page := 0
var results_summary := ""         # one line for the autowin test log
var hero_xp_awarded := 0.0
var title_screen: Control
var map_select: Control
var hero_card: PanelContainer
var lbl_hero_name: Label
var lbl_hero_level: Label
var hero_xp_fill: ColorRect
var btn_hero: Button
var demo := false
var attract := false          # main-menu background: the newest era map plays itself
var test_mode := false        # --demo / --autowin: every hero and tower available
var lbl_scrap: Label
var hud_top: Control
var hud_side: Control
var heroes_panel: Control
var map_id := "mammoth_valley"
var map_order: Array = []
var theme: Dictionary


func _ready() -> void:
	get_tree().node_added.connect(_no_scrollbar)
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
	else:
		map_id = _menu_map()
	map = Defs.load_map(map_id)
	defs = Defs.load_all(map)
	var th_id: String = map.get("theme", "meadow")
	theme = THEMES[th_id] if THEMES.has(th_id) else EraDecor.env(th_id)
	sim = Sim.new()
	sim.setup(defs, map)
	var hid := Progress.hero()
	test_mode = "--demo" in OS.get_cmdline_user_args() or "--autowin" in OS.get_cmdline_user_args()
	var forced_hero := ""
	for ua in OS.get_cmdline_user_args():
		if ua.begins_with("--hero="):
			forced_hero = ua.trim_prefix("--hero=")          # screenshot runs: play as this hero
	if forced_hero != "" and defs.heroes.heroes.has(forced_hero):
		hid = forced_hero
	elif not defs.heroes.heroes.has(hid) or not (test_mode or Progress.hero_unlocked(defs.heroes.heroes[hid])):
		hid = "ugo"
	sim.set_hero(hid)
	sim.hero_plevel = 1 if (demo or test_mode) else Progress.hero_level(hid)
	if not "--noperks" in OS.get_cmdline_user_args():
		sim.apply_perks(Progress.sim_perks())
		sim.hp_mult *= Progress.timeline_hp_mult()
	_apply_tech()
	_build_world()
	_build_audio()
	_build_hud()
	_build_confirm_bar()
	_apply_settings()
	demo = "--demo" in OS.get_cmdline_user_args()
	if Progress.current_map == "" and not demo and not "--autowin" in OS.get_cmdline_user_args():
		_start_attract()
	if "--shoot-menu" in OS.get_cmdline_user_args():
		_shoot_menu()
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


## Instantiates a model GLB. v2 art bakes its colors (and ambient occlusion) into vertex colors,
## which Godot's glTF importer doesn't route to albedo on its own: switch that on for every
## surface that carries vertex colors (shared materials, so this runs once per model file).
var _vc_done := {}
func _inst(path: String) -> Node3D:
	var model: Node3D = (_res(path) as PackedScene).instantiate()
	if not _vc_done.has(path):
		_vc_done[path] = true
		for mi in model.find_children("*", "MeshInstance3D", true, false):
			var mesh := (mi as MeshInstance3D).mesh as ArrayMesh
			if mesh == null:
				continue
			for si in mesh.get_surface_count():
				var m := mesh.surface_get_material(si) as BaseMaterial3D
				if m != null and (mesh.surface_get_format(si) & Mesh.ARRAY_FORMAT_COLOR) != 0:
					m.vertex_color_use_as_albedo = true
	return model


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


## Spheres for things spawned over and over (projectiles): one shared mesh per size, not a new one per shot.
var _sph_cache := {}
func _sph_c(r: float, seg := 10) -> SphereMesh:
	var key := "%.3f_%d" % [r, seg]
	if not _sph_cache.has(key):
		_sph_cache[key] = _sph(r, seg)
	return _sph_cache[key]


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


## "Captain Isla Reyes" -> "Isla", "Big Jim Coalfoot" -> "Jim", "Cassia the Legate" -> "Cassia".
func _short_name(full: String) -> String:
	var w := full.split(" ")
	if w.size() > 1 and w[0] in ["Captain", "Sir", "Sgt.", "Dr.", "Commander", "Big", "Unit"]:
		return w[1]
	return w[0]


func _era_index() -> int:
	return maxi(0, _eras().find(_era()))


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
	sun.shadow_enabled = Progress.gfx_level() == 0
	sun.shadow_blur = 1.5
	sun.directional_shadow_max_distance = 80.0
	add_child(sun)

	if _style2():
		_style2_env(env, sun)

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
	var gmat: Material = gm
	var lava_path := "res://assets/textures/ground_%s_lava.png" % map_id
	if ResourceLoader.exists(lava_path):
		# v0.9.21: the painted lava (cracks, molten pools) glows and flows (tools/lava_mask.py makes the mask)
		var lg := ShaderMaterial.new()
		lg.shader = load("res://game/shaders/ground_lava.gdshader")
		lg.set_shader_parameter("ground", gm.albedo_texture)
		lg.set_shader_parameter("lava_mask", load(lava_path))
		lg.set_shader_parameter("tint", gm.albedo_color)
		gmat = lg
	var water_path := "res://assets/textures/ground_%s_water.png" % map_id
	if ResourceLoader.exists(water_path):
		# v0.9.28: the painted rivers, lakes and ponds move (tools/water_mask.py makes the mask and the flow map)
		var wg := ShaderMaterial.new()
		wg.shader = load("res://game/shaders/ground_water.gdshader")
		wg.set_shader_parameter("ground", gm.albedo_texture)
		wg.set_shader_parameter("water_mask", load(water_path))
		wg.set_shader_parameter("tint", gm.albedo_color)
		gmat = wg
	_mi(pm, gmat, self, Vector3(GROUND_RECT.position.x + GROUND_RECT.size.x * 0.5, 0, GROUND_RECT.position.y + GROUND_RECT.size.y * 0.5))
	var far := PlaneMesh.new()
	far.size = Vector2(160, 120)
	# (the ground's albedo tint applies to the far plane too, so the two meet without a step in brightness)
	var fc := _edge_color(gm.albedo_texture, theme.far)
	if gm.albedo_texture != null:
		fc = Color(fc.r * gm.albedo_color.r, fc.g * gm.albedo_color.g, fc.b * gm.albedo_color.b)
	_mi(far, _mat("far_ground", fc, {"rough": 1.0}), self, Vector3(0, -0.02, 0))

	for P in sim.paths:
		var pts: PackedVector2Array = P.pts
		var ppi := sim.paths.find(P)
		_build_portal(sim.pos_at(Sim.SPAWN_DIST, ppi), sim.dir_at(Sim.SPAWN_DIST, ppi), ppi)
	var end_pt := sim.path[sim.path.size() - 1]
	var d0 := get_child_count()
	var base_id := str(map.get("base", "cave"))
	if base_id == "city":
		_build_city(end_pt)
	elif base_id != "cave":
		EraDecor.build_base(self, base_id, end_pt)
	elif _v2_kit(str(map.get("theme", "meadow"))):
		_build_cave_v2(end_pt)
	else:
		_build_cave(end_pt)
	_build_decor()
	_build_blockers()
	_decor_roots = get_children().slice(d0)
	if "--export-decor" not in OS.get_cmdline_user_args():
		_swap_baked_decor()
		if not _v2_kit(str(map.get("theme", ""))) or bool(_decor_theme().get("ambient", false)):
			_ambient_fx(Vector3.INF)
	_build_path_features()
	if not attract and (_era_index() == 0 or str(sim.hero_id) in ["ugo", "mara"]):
		_prewarm_attack_fx()
	_prewarm_arrows()                            # (the menu's demo match too: the Bronze Age shoots arrows and lances)

	sel_range = _mi(_cyl(1, 1, 0.02, 48), _mat("range", Color(1, 1, 1, 0.16), {"unshaded": true}), self, Vector3(0, 0.12, 0))
	sel_range.visible = false
	aura_range = _mi(_cyl(1, 1, 0.02, 48), _mat("aura_range", Color(1, 0.8, 0.25, 0.14), {"unshaded": true}), self, Vector3(0, 0.11, 0))
	aura_range.visible = false
	ghost = Node3D.new()
	add_child(ghost)
	ghost.visible = false
	ghost_range = _mi(_cyl(1, 1, 0.02, 48), _mat("range_g", Color(1, 1, 1, 0.18), {"unshaded": true}), ghost, Vector3(0, 0.13, 0))
	ghost_foot = _mi(_cyl(1, 1, 0.03, 24), _mat("foot_ok", Color(0.2, 1, 0.3, 0.45), {"unshaded": true}), ghost, Vector3(0, 0.15, 0))


## v2 art pass (rolling out era by era; Stone Age first).
func _style2() -> bool:
	return true


## v2 look: a real sky (seen from the menu hub camera), warm key light against a cool fill,
## filmic tone curve and a gentle grade. Works in the Compatibility renderer.
## v2 sky per theme: [sky top, horizon, ground horizon, ground bottom]. Seen from the menu hub camera and
## at the edges of tall screens. Indoor themes get a dark "ceiling" sky.
const SKY_V2 := {
	"day": [Color(0.3, 0.55, 0.92), Color(0.8, 0.88, 0.96), Color(0.55, 0.66, 0.5), Color(0.18, 0.3, 0.14)],
	"snow": [Color(0.42, 0.56, 0.78), Color(0.86, 0.9, 0.96), Color(0.82, 0.86, 0.92), Color(0.6, 0.66, 0.74)],
	"volcano": [Color(0.14, 0.08, 0.08), Color(0.62, 0.26, 0.1), Color(0.3, 0.14, 0.08), Color(0.06, 0.04, 0.04)],
	"desert": [Color(0.35, 0.58, 0.9), Color(0.96, 0.86, 0.68), Color(0.8, 0.66, 0.44), Color(0.5, 0.38, 0.22)],
	"dusk": [Color(0.22, 0.24, 0.42), Color(0.9, 0.55, 0.36), Color(0.36, 0.3, 0.24), Color(0.12, 0.1, 0.08)],
	"forge": [Color(0.12, 0.07, 0.06), Color(0.55, 0.22, 0.1), Color(0.2, 0.1, 0.06), Color(0.05, 0.03, 0.03)],
	"mist": [Color(0.42, 0.5, 0.5), Color(0.78, 0.82, 0.78), Color(0.45, 0.5, 0.42), Color(0.16, 0.2, 0.14)],
	"night": [Color(0.04, 0.05, 0.12), Color(0.22, 0.26, 0.4), Color(0.12, 0.14, 0.18), Color(0.03, 0.03, 0.05)],
	"smog": [Color(0.4, 0.38, 0.3), Color(0.76, 0.66, 0.46), Color(0.42, 0.38, 0.3), Color(0.14, 0.12, 0.1)],
	"neon": [Color(0.05, 0.02, 0.12), Color(0.45, 0.1, 0.5), Color(0.1, 0.06, 0.18), Color(0.02, 0.01, 0.04)],
	"indoor": [Color(0.04, 0.06, 0.09), Color(0.14, 0.2, 0.26), Color(0.1, 0.14, 0.18), Color(0.03, 0.04, 0.05)],
}
const THEME_SKY := {"snow": "snow", "volcano": "volcano", "desert": "desert", "canyon": "desert", "coast": "day", "olive": "desert",
	"forge": "forge", "bog": "mist", "darkwood": "night", "jungle": "mist", "smog": "smog", "factory": "smog", "railyard": "dusk",
	"neon": "neon", "lab": "indoor", "server": "indoor", "cooling": "indoor", "core": "neon", "satellite": "night", "metro": "dusk"}


## v2 look: a real sky, warm key light against a cool fill, filmic tone curve and a gentle grade, built on
## each theme's own light levels (so dark interiors stay dark). Works in the Compatibility renderer.
func _style2_env(env: Environment, sun: DirectionalLight3D) -> void:
	var th := str(map.get("theme", "meadow"))
	var sk: Array = SKY_V2[THEME_SKY.get(th, "day")]
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = sk[0]
	sky_mat.sky_horizon_color = sk[1]
	sky_mat.ground_horizon_color = sk[2]
	sky_mat.ground_bottom_color = sk[3]
	sky_mat.sun_angle_max = 25.0
	var sky := Sky.new()
	sky.sky_material = sky_mat
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = (theme.ambient as Color).lerp(Color(0.7, 0.8, 1.0), 0.35)
	env.ambient_light_energy = float(theme.ambient_e) * 1.22
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.12
	env.tonemap_white = 5.0
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.07
	env.adjustment_saturation = 1.14
	sun.light_color = (theme.sun as Color).lerp(Color(1.0, 0.91, 0.78), 0.4)
	sun.light_energy = float(theme.sun_e) * 1.25
	if th == "snow":
		env.ambient_light_color = Color(0.72, 0.82, 1.0)
		env.ambient_light_energy = 0.5
		env.tonemap_exposure = 1.0
		sun.light_color = Color(0.98, 0.96, 1.0)
		sun.light_energy = float(theme.sun_e) * 1.15
	elif th == "volcano":
		env.ambient_light_color = Color(1.0, 0.7, 0.55)
		env.ambient_light_energy = 0.42
		env.adjustment_saturation = 1.2
		sun.light_color = Color(1.0, 0.72, 0.5)
		sun.light_energy = float(theme.sun_e) * 1.15
	elif th == "meadow":
		env.ambient_light_color = Color(0.7, 0.8, 1.0)
		env.ambient_light_energy = 0.44
		sun.light_color = Color(1.0, 0.91, 0.78)
	sun.rotation_degrees = Vector3(-52, -36, 0)
	sun.shadow_opacity = 0.8


## Main-menu hub: a low perspective shot in front of the time portal, robots marching out at you.
func _hub_camera() -> void:
	var pn: Node3D = portal_nodes[0]
	var pp := pn.global_position
	var fwd := -pn.global_transform.basis.z
	var side := pn.global_transform.basis.x
	var sway := sin(time_s * 0.16) * 0.22
	var off := (fwd * cos(sway) + side * sin(sway)).normalized()
	cam.projection = Camera3D.PROJECTION_PERSPECTIVE
	cam.fov = 46
	cam.position = pp + off * 10.5 + side * 1.2 + Vector3(0, 4.6 + 0.4 * sin(time_s * 0.23), 0)
	cam.look_at(pp + fwd * 3.2 + Vector3(0, 1.0, 0), Vector3.UP)


func _frame_camera() -> void:
	if attract and portal_nodes.has(0):
		_hub_camera()
		return
	var vp := get_viewport().get_visible_rect().size
	var aspect := vp.x / maxf(vp.y, 1.0)
	var side_frac := SIDEBAR_W / maxf(vp.x, 1.0)
	if attract:
		side_frac = 600.0 / maxf(vp.x, 1.0)    # the main-menu column sits on the left
	var need_w := 33.4   # road start (-15.6) to just past the base gate (~17.8)
	var need_h := 18.6 * sin(deg_to_rad(PITCH)) + 2.6
	cam.size = maxf(need_h, need_w / (aspect * (1.0 - side_frac)))
	var view_w := cam.size * aspect
	var target := Vector3(view_w * side_frac * 0.5 + 1.1, 0, 0.6)
	if attract:
		target.x = -view_w * side_frac * 0.5 + 1.1
	var back := Vector3(0, sin(deg_to_rad(PITCH)), cos(deg_to_rad(PITCH))) * 60.0
	cam.position = target + back
	cam.look_at(target, Vector3.UP)
	cam_base = cam.position


## Average color of the ground texture's outer rows, so the plane beyond it blends in on tall screens.
func _edge_color(tex: Texture2D, fallback: Color) -> Color:
	if tex == null:
		return fallback
	var img := tex.get_image()
	if img == null:
		return fallback
	if img.is_compressed():
		img.decompress()
	var acc := Vector3.ZERO
	var n := 0
	var w := img.get_width()
	var h := img.get_height()
	for x in range(0, w, 16):
		for y in [1, 4, h - 2, h - 5]:
			var c := img.get_pixel(x, y)
			acc += Vector3(c.r, c.g, c.b)
			n += 1
	acc /= float(maxi(n, 1))
	return Color(acc.x, acc.y, acc.z)


var portal_nodes := {}      # path index -> portal root
var btn_details: Button
var detail_open := 0        # detail cards open during a match pause the action
var _swirl: ImageTexture = null


## Spiral "time vortex" texture, drawn once.
func _swirl_tex() -> ImageTexture:
	if _swirl != null:
		return _swirl
	var sz := 160
	var img := Image.create(sz, sz, false, Image.FORMAT_RGBA8)
	for y in sz:
		for x in sz:
			var u := (x + 0.5) / sz * 2.0 - 1.0
			var v := (y + 0.5) / sz * 2.0 - 1.0
			var r := sqrt(u * u + v * v)
			if r >= 1.0:
				img.set_pixel(x, y, Color(1, 1, 1, 0))
				continue
			var ang := atan2(v, u)
			var arms := pow(0.5 + 0.5 * sin(ang * 4.0 + r * 11.0), 2.2)
			var core := pow(1.0 - r, 3.0)
			var edge := clampf((1.0 - r) / 0.18, 0.0, 1.0)
			var it := clampf(arms * (0.25 + 0.75 * r) * edge + core * 1.2, 0.0, 1.0)
			img.set_pixel(x, y, Color(1, 1, 1, it))
	img.generate_mipmaps()
	_swirl = ImageTexture.create_from_image(img)
	return _swirl


func _glow_mat(key: String, col: Color, tex: Texture2D = null) -> StandardMaterial3D:
	if mats.has(key):
		return mats[key]
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.albedo_color = col
	m.albedo_texture = tex
	m.disable_receive_shadows = true
	mats[key] = m
	return m


## The time machine portal the robots step out of. It stands right on the start of the path,
## facing down it, so every robot visibly emerges from the vortex.
func _build_portal(p: Vector2, dir: Vector2, pi := 0) -> Node3D:
	var n := Node3D.new()
	n.position = _v3(p)
	add_child(n)
	n.transform.basis = Basis.looking_at(Vector3(dir.x, 0, dir.y))   # -Z points down the path
	var steel := _mat("portal_steel", Color(0.22, 0.24, 0.3), {"metal": 0.8, "rough": 0.35})
	var dark := _mat("portal_dark", Color(0.1, 0.1, 0.13), {"metal": 0.5, "rough": 0.5})
	var cyan := _mat("portal_cyan", Color(0.4, 0.95, 1.0), {"emit": Color(0.25, 0.85, 1.0), "emit_e": 3.0})
	var mag := _mat("portal_mag", Color(1.0, 0.3, 0.9), {"emit": Color(1.0, 0.2, 0.85), "emit_e": 3.0})
	var hz := 1.55          # ring centre height
	# (no pad or swirl on the ground: only the standing portal, v0.9.12)
	var lights := Node3D.new()
	var hq := _portal_kit()
	if not hq.is_empty():
		# v0.9.18: the sculpted, baked portal (armoured ring, pylons, coils, beacons); its light strips turn
		var body := MeshInstance3D.new()
		body.mesh = hq["Portal"]
		n.add_child(body)
		lights.position = Vector3(0, hz, 0)
		n.add_child(lights)
		var lm := MeshInstance3D.new()
		lm.mesh = hq["PortalLights"]
		lm.position = Vector3(0, -hz, 0)
		lm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		lights.add_child(lm)
	else:
		# the frame: a thick torus with armoured segments and running lights
		var frame := Node3D.new()
		frame.position = Vector3(0, hz, 0)
		n.add_child(frame)
		var tor := TorusMesh.new()
		tor.inner_radius = 1.35
		tor.outer_radius = 1.7
		tor.rings = 40
		tor.ring_segments = 10
		_mi(tor, steel, frame, Vector3.ZERO, Vector3(PI * 0.5, 0, 0))
		var inner := TorusMesh.new()
		inner.inner_radius = 1.28
		inner.outer_radius = 1.38
		inner.rings = 40
		inner.ring_segments = 6
		_mi(inner, cyan, frame, Vector3.ZERO, Vector3(PI * 0.5, 0, 0))
		frame.add_child(lights)
		for k in 12:
			var aa := TAU * k / 12.0
			var seg_pos := Vector3(cos(aa) * 1.55, sin(aa) * 1.55, 0)
			_mi(_box(0.34, 0.26, 0.5), dark, frame, seg_pos, Vector3(0, 0, aa))
			_mi(_box(0.14, 0.1, 0.54), mag if k % 2 == 0 else cyan, lights, Vector3(cos(aa) * 1.72, sin(aa) * 1.72, 0), Vector3(0, 0, aa))
		# legs / pylons holding the ring, with glowing coils
		for sgn in [-1, 1]:
			var lx := float(sgn) * 1.55
			_mi(_box(0.5, 0.9, 0.7), steel, n, Vector3(lx, 0.45, 0))
			_mi(_cyl(0.16, 0.2, 1.3, 8), dark, n, Vector3(lx * 1.18, 0.95, 0.0), Vector3(0, 0, float(sgn) * 0.25))
			for c in 3:
				_mi(_cyl(0.24, 0.24, 0.07, 10), cyan, n, Vector3(lx * 1.18 + float(sgn) * (0.06 + 0.1 * c), 0.6 + 0.28 * c, 0), Vector3(0, 0, float(sgn) * 0.25))
			var tip := _mi(_sph(0.17, 10), mag, n, Vector3(lx * 1.33, 1.7, 0))
			tip.set_meta("tip", true)
	# the vortex: stacked additive spiral discs turning against each other
	var vortex := Node3D.new()
	vortex.position = Vector3(0, hz, 0)
	n.add_child(vortex)
	var q := QuadMesh.new()
	q.size = Vector2(2.7, 2.7)
	var layers := []
	var cols := [Color(0.35, 0.2, 1.0, 0.95), Color(0.2, 0.9, 1.0, 0.8), Color(1.0, 0.3, 0.9, 0.55), Color(1, 1, 1, 0.5)]
	# a dark disc in the middle of the ring, with the same swirl stacked on both faces (v0.9.18: from behind, as on
	# maps whose path comes in from the bottom edge, the portal used to show only the black back of the disc)
	for side in [-1.0, 1.0]:
		for i in 4:
			var l := _mi(q, _glow_mat("vortex_%d" % i, cols[i], _swirl_tex()), vortex, Vector3(0, 0, side * (0.07 + 0.06 * i)), Vector3.ZERO,
				Vector3.ONE * (1.0 - 0.12 * i))
			l.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			layers.append(l)
	var back := _mi(_cyl(1.36, 1.36, 0.02, 32), _mat("vortex_back", Color(0.05, 0.02, 0.15)), vortex, Vector3.ZERO, Vector3(PI * 0.5, 0, 0))
	back.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# sparks being pulled into the vortex
	var sp := CPUParticles3D.new()
	sp.amount = 40
	sp.lifetime = 1.1
	sp.local_coords = true
	sp.emission_shape = CPUParticles3D.EMISSION_SHAPE_RING
	sp.emission_ring_axis = Vector3(0, 0, 1)
	sp.emission_ring_radius = 1.9
	sp.emission_ring_inner_radius = 1.5
	sp.emission_ring_height = 0.2
	sp.direction = Vector3.ZERO
	sp.spread = 0.0
	sp.gravity = Vector3.ZERO
	sp.radial_accel_min = -6.0
	sp.radial_accel_max = -3.5
	sp.tangential_accel_min = 4.0
	sp.tangential_accel_max = 6.0
	sp.scale_amount_min = 0.5
	sp.scale_amount_max = 1.0
	var spm := _sph(0.05, 4)
	spm.material = _glow_mat("portal_spark", Color(0.6, 0.95, 1.0, 1.0))
	sp.mesh = spm
	if Progress.gfx_level() < 2:
		vortex.add_child(sp)
	else:
		sp.free()
	# light that washes the ground in time-energy colours
	var light := OmniLight3D.new()
	light.light_color = Color(0.55, 0.6, 1.0)
	light.light_energy = 2.2
	light.omni_range = 6.0
	light.position = Vector3(0, hz, 0.0)          # (in the ring: it washes the ground on both sides)
	n.add_child(light)
	light.visible = Progress.gfx_level() < 2
	n.set_meta("lights", lights)
	n.set_meta("vortex", vortex)
	n.set_meta("layers", layers)
	n.set_meta("light", light)
	n.set_meta("flash", 0.0)
	n.set_meta("arc_t", 0.0)
	n.set_meta("hz", hz)
	portal_nodes[pi] = n
	effects.append({"node": n, "life": INF, "t": 0.0, "kind": "portal"})
	return n


## The HQ time portal (tools/blender/hq/decor_build.py --theme portal): meshes "Portal" and "PortalLights".
var _portal_lib := {}
func _portal_kit() -> Dictionary:
	if _portal_lib.is_empty() and ResourceLoader.exists("res://assets/decor/time_portal.glb"):
		var src := _inst("res://assets/decor/time_portal.glb")
		for mi in src.find_children("*", "MeshInstance3D", true, false):
			_portal_lib[str(mi.name)] = _kit_outline((mi as MeshInstance3D).mesh, false)
		src.free()
	return _portal_lib if _portal_lib.has("Portal") and _portal_lib.has("PortalLights") else {}


## A robot comes through: the vortex flares and a shockwave rolls out.
func _portal_flash(pi: int, big := false) -> void:
	if not portal_nodes.has(pi):
		return
	var n: Node3D = portal_nodes[pi]
	n.set_meta("flash", 1.6 if big else 1.0)
	var wave := TorusMesh.new()
	wave.inner_radius = 1.1
	wave.outer_radius = 1.3
	wave.rings = 32
	wave.ring_segments = 6
	var w := _mi(wave, _glow_mat("portal_wave", Color(0.6, 0.85, 1.0, 0.9)).duplicate(), n, Vector3(0, float(n.get_meta("hz")), 0), Vector3(PI * 0.5, 0, 0))
	effects.append({"node": w, "life": 0.45, "t": 0.0, "kind": "portal_wave", "big": big})


# ---------------------------------------------------------------- path features (layout v2)
## Tunnel mouths, time-rift pads and moving arrows on speed lanes. Built after the scenery bake swap, so they
## stay live nodes. Paths that share a stretch share its features (deduped by position).
var lane_arrows: Array = []      # [{node, pi, d0, d1, off}] chevrons gliding down speed lanes
var preview: Dictionary = {}     # the path-flow preview while it runs
var rift_nodes := {}             # snapped position -> rift pad node
var preview_spots: Array = []    # where preview labels already sit


func _build_path_features() -> void:
	var seen := {}
	for pi in sim.paths.size():
		var P: Dictionary = sim.paths[pi]
		for z in P.zones:
			var key := "%s|%s|%s" % [z.k, str(sim.pos_at(float(z.d0), pi).snapped(Vector2(0.1, 0.1))), str(sim.pos_at(float(z.d1), pi).snapped(Vector2(0.1, 0.1)))]
			if seen.has(key):
				continue
			seen[key] = true
			if z.k == "tunnel":
				_tunnel_mouth(sim.pos_at(float(z.d0) + 0.55, pi), sim.dir_at(float(z.d0) + 0.3, pi), true)
				_tunnel_mouth(sim.pos_at(float(z.d1) - 0.55, pi), sim.dir_at(float(z.d1) - 0.3, pi), false)
			elif z.k == "fast":
				_lane_arrows(pi, float(z.d0), float(z.d1))
		for rf in P.rifts:
			var key2 := "rift|%s" % str((rf.from as Vector2).snapped(Vector2(0.1, 0.1)))
			if seen.has(key2):
				continue
			seen[key2] = true
			_rift_pad(rf.from, sim.dir_at(float(rf.d) - 0.05, pi), true)
			_rift_pad(rf.to, sim.dir_at(float(rf.d) + 0.05, pi), false)


## Where a robot is drawn hidden: inside a tunnel, past the mouth arch (flyers stay visible above).
func _tunnel_hides(e: Dictionary) -> bool:
	if e.flying:
		return false
	for z in sim.paths[e.pi].zones:
		if z.k == "tunnel" and float(e.dist) > float(z.d0) + 0.55 and float(e.dist) < float(z.d1) - 0.55:
			return true
	return false


func _tunnel_look() -> Array:
	## [arch colour, trim colour, style] by era: rock cave, cut stone, brick, concrete, tech
	match sim.era():
		"Stone Age":
			return [Color(0.46, 0.43, 0.40), Color(0.34, 0.31, 0.28), "rock"]
		"Bronze Age", "Classical Age":
			return [Color(0.82, 0.70, 0.50), Color(0.66, 0.54, 0.36), "stone"]
		"Iron Age", "Medieval Age":
			return [Color(0.55, 0.55, 0.57), Color(0.40, 0.40, 0.43), "stone"]
		"Gunpowder Age", "Industrial Age":
			return [Color(0.58, 0.30, 0.22), Color(0.40, 0.38, 0.36), "brick"]
		"Modern Age":
			return [Color(0.66, 0.66, 0.64), Color(0.95, 0.75, 0.15), "concrete"]
	return [Color(0.20, 0.22, 0.28), Color(0.25, 0.85, 1.0), "tech"]


## A tunnel mouth, made to read from the top-down camera: a dark hole sloping into the ground, framed by low
## walls, under a small arch. `entry` = robots walk in here (the hole lies ahead of the arch), else they come out.
func _tunnel_mouth(p: Vector2, dir: Vector2, entry: bool) -> void:
	var look := _tunnel_look()
	var n := Node3D.new()
	n.position = _v3(p)
	add_child(n)
	n.transform.basis = Basis.looking_at(Vector3(dir.x, 0, dir.y))      # -Z points down the path
	var body := _mat("tun_%s" % look[2], look[0], {"rough": 0.9})
	var trim := _mat("tun_trim_%s" % look[2], look[1], {"rough": 0.6, "emit": look[1] if look[2] == "tech" else Color(0, 0, 0), "emit_e": 1.5 if look[2] == "tech" else 0.0})
	var dark := _mat("tun_dark", Color(0.03, 0.025, 0.03), {"unshaded": true})
	var fade := _mat("tun_fade", Color(0.03, 0.025, 0.03, 0.55), {"unshaded": true})
	var inward := -1.0 if entry else 1.0          # local z of the tunnel side: ahead (-Z) of an entry, behind an exit
	# the hole: solid dark where the road goes under, with a soft lip where it starts
	_mi(_box(1.7, 0.02, 1.5), dark, n, Vector3(0, 0.03, inward * 0.95))
	_mi(_box(1.7, 0.02, 0.35), fade, n, Vector3(0, 0.03, inward * 0.05))
	# low retaining walls either side of the ramp and a back wall over the hole
	for sgn in [-1.0, 1.0]:
		_mi(_box(0.32, 0.42, 1.9), body, n, Vector3(sgn * 1.0, 0.21, inward * 0.75))
		_mi(_box(0.36, 0.1, 1.94), trim, n, Vector3(sgn * 1.0, 0.45, inward * 0.75))
	_mi(_box(2.32, 0.55, 0.4), body, n, Vector3(0, 0.27, inward * 1.75))
	# the arch over the mouth
	var r := 0.98
	var segs := 7
	for k in segs:
		var a := PI * (float(k) + 0.5) / float(segs)
		var w := 0.44 if look[2] != "rock" else 0.56
		_mi(_box(w, 0.3, 0.5), body if (k % 2 == 0 or look[2] == "concrete") else trim, n,
			Vector3(cos(a) * r, sin(a) * r * 0.85, inward * 0.25), Vector3(0, 0, a - PI * 0.5),
			Vector3.ONE * (1.0 + (0.14 * sin(float(k) * 1.7) if look[2] == "rock" else 0.0)))
	if look[2] == "tech" or look[2] == "concrete":
		_mi(_box(1.9, 0.06, 0.06), trim, n, Vector3(0, 0.98, inward * 0.25 - 0.27 * inward))
	var q := QuadMesh.new()                        # darkness inside the arch
	q.size = Vector2(1.7, 0.9)
	_mi(q, dark, n, Vector3(0, 0.45, inward * 0.45), Vector3(0, 0 if inward < 0 else PI, 0))


## A time rift: a small standing portal ring. Robots walk into the purple one and out of the cyan one.
func _rift_pad(p: Vector2, dir: Vector2, entry: bool) -> void:
	var n := Node3D.new()
	n.position = _v3(p)
	add_child(n)
	n.transform.basis = Basis.looking_at(Vector3(dir.x, 0, dir.y))
	var col := Color(0.75, 0.3, 1.0) if entry else Color(0.25, 0.9, 1.0)
	var layers := []                       # standing ring only: nothing on the ground
	var ring := Node3D.new()
	ring.position = Vector3(0, 1.05, 0)
	n.add_child(ring)
	var tor := TorusMesh.new()
	tor.inner_radius = 0.8
	tor.outer_radius = 0.95
	tor.rings = 28
	tor.ring_segments = 6
	_mi(tor, _mat("rift_ring_%s" % entry, col, {"emit": col, "emit_e": 2.5}), ring, Vector3.ZERO, Vector3(PI * 0.5, 0, 0))
	var vq := QuadMesh.new()
	vq.size = Vector2(1.7, 1.7)
	layers.append(_mi(vq, _glow_mat("rift_vortex_%s" % entry, Color(col.r, col.g, col.b, 0.85), _swirl_tex()), ring, Vector3.ZERO))
	layers.append(_mi(vq, _glow_mat("rift_vortex_w", Color(1, 1, 1, 0.45), _swirl_tex()), ring, Vector3(0, 0, 0.03), Vector3.ZERO, Vector3.ONE * 0.6))
	for sgn in [-1.0, 1.0]:
		_mi(_box(0.18, 0.6, 0.3), _mat("rift_post", Color(0.2, 0.2, 0.26), {"metal": 0.7, "rough": 0.4}), n, Vector3(sgn * 0.95, 0.3, 0))
	n.set_meta("layers", layers)
	n.set_meta("ring", ring)
	n.set_meta("flash", 0.0)
	rift_nodes[str(p.snapped(Vector2(0.1, 0.1)))] = n
	effects.append({"node": n, "life": INF, "t": 0.0, "kind": "rift"})


## Glowing chevrons that glide down a speed lane, faster than robots walk, so the lane reads as "fast".
func _lane_arrows(pi: int, d0: float, d1: float) -> void:
	var length := d1 - d0
	var count := maxi(2, int(length / 2.4))
	var acc := Color(1.0, 0.9, 0.35, 0.75)
	if sim.era() in ["Digital Age", "The Data Center"]:
		acc = Color(0.3, 1.0, 1.0, 0.8)
	elif str(map.get("theme", "")) == "snow":
		acc = Color(1, 1, 1, 0.8)
	var m := _glow_mat("lane_arrow_%s" % acc.to_html(), acc)
	for i in count:
		var c := Node3D.new()
		add_child(c)
		for sgn in [-1.0, 1.0]:      # a V made of two bars, tip leading
			_mi(_box(0.09, 0.02, 0.62), m, c, Vector3(sgn * 0.2, 0.0, 0.2), Vector3(0, sgn * 0.75, 0))
		lane_arrows.append({"node": c, "pi": pi, "d0": d0, "d1": d1, "off": float(i) / float(count)})


func _tick_lanes(dt: float) -> void:
	for la in lane_arrows:
		var length: float = la.d1 - la.d0
		la.off = fmod(float(la.off) + dt * 3.6 / maxf(length, 0.1), 1.0)
		var d: float = la.d0 + la.off * length
		var n: Node3D = la.node
		n.position = _v3(sim.pos_at(d, la.pi), 0.07)
		var dir := sim.dir_at(d, la.pi)
		n.rotation.y = atan2(-dir.x, -dir.y)
		var edge := minf(la.off, 1.0 - la.off) * length
		n.scale = Vector3.ONE * clampf(edge / 0.8, 0.0, 1.0)


## BTD6-style path flow: glowing runners travel every path from its portal to your base, speeding up on
## lanes, slowing in mud, ducking into tunnels and blinking through rifts. Labels name each mechanic.
## With loop = true (every map start) the runners keep going round and the labels stay up until the first
## round starts, then it all fades out.
func _path_preview(loop := false) -> void:
	_end_preview()
	if attract or sim == null:
		return
	var runners := []
	var mk := _glow_mat("preview_runner", Color(1.0, 0.95, 0.5, 0.95))
	var mk2 := _glow_mat("preview_trail", Color(1.0, 0.75, 0.25, 0.6))
	for wave_i in 2:
		for pi in sim.paths.size():
			for j in 7:
				var n := _mi(_sph(0.24 if j == 0 else 0.17 - j * 0.012, 8), mk if j == 0 else mk2, self, _v3(sim.pos_at(0.0, pi), 0.45))
				n.visible = false
				runners.append({"node": n, "pi": pi, "d": -float(j) * 0.55, "d0": -float(j) * 0.55,
					"delay": wave_i * 1.6, "delay0": wave_i * 1.6, "done": false})
	var labels := []
	var seen := {}
	preview_spots.clear()
	for pi in sim.paths.size():
		var P: Dictionary = sim.paths[pi]
		for z in P.zones:
			var txt: String = {"fast": "SPEED LANE", "slow": "SLOW GROUND", "tunnel": "TUNNEL: can't be hit"}.get(z.k, "")
			var at_d: float = (float(z.d0) + float(z.d1)) * 0.5
			if txt != "":
				labels.append(_preview_label(sim.pos_at(at_d, pi), txt, {"fast": Color(1, 0.9, 0.35), "slow": Color(0.95, 0.65, 0.4), "tunnel": Color(0.8, 0.85, 0.95)}[z.k]))
		for rf in P.rifts:
			var key2 := str((rf.from as Vector2).snapped(Vector2(0.5, 0.5)))
			if not seen.has(key2):
				seen[key2] = true
				labels.append(_preview_label(rf.from, "RIFT IN", Color(0.85, 0.5, 1.0)))
				labels.append(_preview_label(rf.to, "RIFT OUT", Color(0.4, 0.95, 1.0)))
		if sim.paths.size() > 1:
			labels.append(_preview_label(sim.pos_at(3.2, pi), "PORTAL %d" % (pi + 1), Color(0.6, 0.9, 1.0)))
	preview = {"runners": runners, "labels": labels.filter(func(x): return x != null), "t": 0.0, "loop": loop, "gap": 0.0}


func _preview_label(p: Vector2, text: String, col: Color) -> Label3D:
	var hw := 0.2 * float(text.length()) + 0.3     # rough half width of the text in world units
	for o in preview_spots:                        # the same note twice close together: show it once
		if o[1] == text and (o[0] as Vector2).distance_to(p) < 4.0:
			return null
	for _k in 6:                                   # overlapping another label: move up the screen until clear
		var hit := false
		for o in preview_spots:
			var q: Vector2 = o[0]
			if absf(q.x - p.x) < hw + float(o[2]) and absf(q.y - p.y) < 0.95:
				hit = true
		if not hit:
			break
		p.y -= 1.0
	preview_spots.append([p, text, hw])
	var l := Label3D.new()
	l.text = text
	l.font = FONT
	l.font_size = 72
	l.outline_size = 18
	l.outline_modulate = Color(0.04, 0.06, 0.12)
	l.pixel_size = 0.01
	l.modulate = Color(col.r, col.g, col.b, 0.0)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.position = _v3(p, 1.9)
	add_child(l)
	return l


func _end_preview() -> void:
	for r in preview.get("runners", []):
		if is_instance_valid(r.node):
			(r.node as Node).queue_free()
	for l in preview.get("labels", []):
		if is_instance_valid(l):
			(l as Node).queue_free()
	preview = {}


func _tick_preview(dt: float) -> void:
	if preview.is_empty():
		return
	preview.t = float(preview.t) + dt
	var loop: bool = preview.get("loop", false)
	if loop and sim.wave >= 1 and not preview.has("end_t"):
		preview.end_t = preview.t          # the first round started: fade it all out
	var alive := false
	for r in preview.runners:
		if r.done:
			continue
		alive = true
		if r.delay > 0.0:
			r.delay = float(r.delay) - dt
			continue
		var P: Dictionary = sim.paths[r.pi]
		var zn := sim.zone_at(maxf(float(r.d), 0.0), r.pi)
		var before: float = r.d
		r.d = float(r.d) + dt * 9.0 * float(zn[0])
		var n: MeshInstance3D = r.node
		if float(r.d) >= float(P.length):
			r.done = true
			n.visible = false
			continue
		n.visible = r.d >= 0.0
		n.position = _v3(sim.pos_at(maxf(float(r.d), 0.0), r.pi), 0.45)
		_fade(n, 0.75 if bool(zn[1]) else 0.0)                  # dim while underground
		for rf in P.rifts:
			if before <= float(rf.d) and float(r.d) > float(rf.d) and n.mesh is SphereMesh and (n.mesh as SphereMesh).radius > 0.2:
				_ring_fx(_v3(rf.from, 0.3), 1.2, Color(0.8, 0.4, 1.0, 0.9), 0.35)
				_ring_fx(_v3(rf.to, 0.3), 1.2, Color(0.3, 0.95, 1.0, 0.9), 0.35)
	var t: float = preview.t
	if loop and not alive and not preview.has("end_t"):
		preview.gap = float(preview.gap) + dt          # a short breath, then the runners set off again
		if float(preview.gap) > 0.6:
			preview.gap = 0.0
			for r in preview.runners:
				r.d = r.d0
				r.delay = r.delay0
				r.done = false
	var a := clampf(t / 0.4, 0.0, 1.0)
	if preview.has("end_t"):
		a *= clampf(1.0 - (t - float(preview.end_t)) / 0.6, 0.0, 1.0)
		for r in preview.runners:
			var rn: MeshInstance3D = r.node
			_fade(rn, maxf(float(rn.get_meta("fade_k", 0.0)), 1.0 - a))
	elif not loop:
		a *= clampf((7.5 - t) / 0.8, 0.0, 1.0)
	for l in preview.labels:
		if is_instance_valid(l):
			(l as Label3D).modulate.a = a
	if preview.has("end_t"):
		if t - float(preview.end_t) > 0.6:
			_end_preview()
	elif not loop and ((not alive and t > 2.0) or t > 8.5):
		_end_preview()


func _campfire(parent: Node3D, pos: Vector3, light_e := 2.0, scale_k := 1.0) -> void:
	var fire := Node3D.new()
	fire.position = pos
	fire.scale = Vector3.ONE * scale_k
	parent.add_child(fire)
	# v0.9.18: billboard flame sprites (a teardrop texture) and a soft glow, instead of two low-poly emissive cones that
	# read as flat yellow pentagons from the game camera
	var glow := _mi(_fx_mesh("flash"), _campfire_mat("glow"), fire, Vector3(0, 0.3, 0), Vector3.ZERO, Vector3.ONE * 1.1)
	glow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var flame := _mi(_flame_quad(0.62, 0.9), _campfire_mat("outer"), fire, Vector3(0, 0.05, 0))
	var flame2 := _mi(_flame_quad(0.36, 0.55), _campfire_mat("inner"), fire, Vector3(0, 0.05, 0))
	flame2.sorting_offset = 0.2
	for f in [flame, flame2]:
		(f as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.6, 0.25)
	light.light_energy = light_e
	light.omni_range = 4.0
	light.position = Vector3(0, 0.8, 0)
	light.visible = light_e > 0.0          # unlit flames (era braziers) cost no light at all
	fire.add_child(light)
	effects.append({"node": fire, "life": INF, "t": 0.0, "kind": "fire", "f1": flame, "f2": flame2, "light": light, "base_e": light_e})


## Campfire sprites: a teardrop flame texture drawn once (white-hot core, orange body, red tip fading out).
var _flame_tex: ImageTexture
var _campfire_mats := {}
var _flame_quads := {}
func _flame_quad(w: float, h: float) -> QuadMesh:
	var key := "%.2f_%.2f" % [w, h]
	if not _flame_quads.has(key):
		var q := QuadMesh.new()
		q.size = Vector2(w, h)
		q.center_offset = Vector3(0, h * 0.5, 0)      # the flame's foot sits on the logs
		_flame_quads[key] = q
	return _flame_quads[key]


func _campfire_mat(kind: String) -> StandardMaterial3D:
	if _campfire_mats.has(kind):
		return _campfire_mats[kind]
	if _flame_tex == null:
		var w := 64
		var h := 96
		var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
		for y in h:
			var v := 1.0 - (y + 0.5) / h                       # 0 at the foot, 1 at the tip
			var t := acos(clampf(v * 2.0 - 1.0, -1.0, 1.0))    # teardrop: x = sin(t) sin(t/2)^1.6
			var half := sin(t) * pow(sin(t * 0.5), 1.6) * 0.98
			for x in w:
				var u := absf((x + 0.5) / w * 2.0 - 1.0)
				var d := u / maxf(half, 0.001)
				var a := clampf((1.0 - d) / 0.22, 0.0, 1.0) * clampf((1.0 - v) / 0.25, 0.0, 1.0)
				var core := clampf(1.0 - d * 1.3, 0.0, 1.0) * clampf(1.0 - v * 1.25, 0.0, 1.0)
				var c := Color(1.0, 0.42, 0.08).lerp(Color(1.0, 0.86, 0.45), core).lerp(Color(1.0, 0.98, 0.85), core * core)
				img.set_pixel(x, y, Color(c.r, c.g, c.b, a))
		_flame_tex = ImageTexture.create_from_image(img)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.billboard_keep_scale = true
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.disable_receive_shadows = true
	match kind:
		"glow":
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.albedo_texture = _mote_tex()
			m.albedo_color = Color(1.0, 0.45, 0.1, 0.55)
		"inner":
			m.albedo_texture = _flame_tex
			m.albedo_color = Color(1.0, 0.95, 0.8, 1.0)
		_:
			m.albedo_texture = _flame_tex
			m.albedo_color = Color(1.0, 0.8, 0.7, 0.95)
	_campfire_mats[kind] = m
	return m


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
	if _city_kit(p):
		return
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


## v0.9.28: the sculpted Bronze city (bronze_city.glb): gate towers, gateway, walls, the ziggurat and town houses, one
## baked mesh with the HQ outline; fires burn in the bronze braziers before the towers.
func _city_kit(p: Vector2) -> bool:
	var path := "res://assets/decor/bronze_city.glb"
	if not _style2() or not ResourceLoader.exists(path):
		return false
	var src := _inst(path)
	var mi := src.find_child("City", true, false) as MeshInstance3D
	var mesh: Mesh = _kit_outline(mi.mesh, false) if mi != null else null
	src.free()
	if mesh == null:
		return false
	var n := Node3D.new()
	n.position = _v3(p, 0)
	add_child(n)
	var body := MeshInstance3D.new()
	body.mesh = mesh
	n.add_child(body)
	for sd in [-1, 1]:
		_campfire(n, Vector3(-0.15, 0.6, sd * 1.55), 1.4, 0.42)
	return true


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


## Decor goes in the ring around the playable area (outside map.bounds), clear of roads and the base.
func _decor_free(p: Vector2, clearance := 0.0) -> bool:
	var b: Array = map.bounds
	var inside: bool = p.x > b[0] - 0.8 - clearance and p.x < b[2] + 0.8 + clearance and p.y > b[1] - 0.8 - clearance and p.y < b[3] + 0.8 + clearance
	if inside or sim.dist_to_path(p) < 2.2 + clearance:
		return false
	var end_pt: Vector2 = sim.path[sim.path.size() - 1]
	if p.x > 13.0 and absf(p.y - end_pt.y) < 6.5:
		return false
	if _river_gap(p) < 0.7 + clearance:               # (v0.9.28: not in a river)
		return false
	return true


func _build_decor() -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 11
	var th: String = map.get("theme", "meadow")
	if EraDecor.handles(th):
		EraDecor.build_decor(self, th, _decor_free)
		return
	if _v2_kit(th):
		_build_decor_v2()
		return
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


# ---------------------------------------------------------------- v2 decor (Stone Age)
## Per theme: the decor kit file, weighted scatter (prop names, weight), playfield ground cover and the landmarks
## that ring the map ([prop, approx position, scale, keep-clear radius]).
const DECOR_V2 := {
	"meadow": {"kit": "stone_decor", "count": 105,
		"scatter": [["Pine_A", 21], ["Pine_B", 21], ["Pine_C", 20], ["Bush_A", 9], ["Bush_B", 9], ["Rock_A", 4], ["Rock_B", 4], ["Rock_C", 4], ["Stump", 5], ["Log", 3]],
		"cover": [["Tuft", 3], ["Flowers", 1]], "cover_n": 140,
		"marks": [["Mammoth", Vector2(4.0, -10.3), 0.85, 2.6], ["Dolmen", Vector2(-9.0, 11.0), 0.8, 1.8],
			["BoneHut", Vector2(10.5, 10.8), 0.85, 1.6], ["BoneHut", Vector2(-17.5, -10.5), 0.75, 1.4], ["Dolmen", Vector2(-17.6, 2.5), 0.6, 1.4]]},
	"snow": {"kit": "stone_decor_snow", "count": 100,
		"scatter": [["Pine_A", 20], ["Pine_B", 20], ["Pine_C", 16], ["Rock_A", 6], ["Rock_B", 6], ["Rock_C", 5], ["Mound_A", 10], ["Mound_B", 10], ["Ice_A", 3], ["Ice_B", 3], ["Stump", 3], ["Log", 2]],
		"cover": [["Mound_B", 1]], "cover_n": 14,
		"marks": [["Mammoth", Vector2(3.0, -10.4), 0.85, 2.6], ["BoneHut", Vector2(-9.5, 10.9), 0.85, 1.6],
			["Dolmen", Vector2(10.5, 10.8), 0.8, 1.8], ["BoneHut", Vector2(-17.5, -10.5), 0.75, 1.4], ["Ice_A", Vector2(-17.8, 3.0), 1.5, 1.2]]},
	"volcano": {"kit": "stone_decor_volcano", "count": 85,
		"scatter": [["Dead_A", 14], ["Dead_B", 14], ["Rock_A", 12], ["Rock_B", 12], ["Rock_C", 10], ["Obsidian", 6], ["Stump", 3]],
		"cover": [["Tuft", 1]], "cover_n": 50,
		"marks": [["Volcano", Vector2(5.5, -12.4), 0.56, 4.2], ["Mammoth", Vector2(10.5, 10.8), 0.8, 2.6],
			["Obsidian", Vector2(-17.6, 1.0), 1.6, 1.4], ["Obsidian", Vector2(-9.0, 11.2), 1.3, 1.2]]},
	# v0.9.28: the Bronze Age kits. "ambient": keep the theme's drifting motes; "shore": clumps along the river banks;
	# a landmark's optional 5th entry: {"force": placed even where decor may not go (the boats on the river), "yaw"}
	"delta": {"kit": "bronze_decor_delta", "count": 95, "ambient": true,
		"scatter": [["Palm_A", 16], ["Palm_B", 13], ["Palm_C", 12], ["Papyrus", 4], ["Reeds", 4], ["Bush_A", 9], ["Bush_B", 7], ["Rock_A", 3], ["Rock_B", 3]],
		"shore": [["Papyrus", 3], ["Reeds", 2]],
		"cover": [["Tuft", 4], ["Flowers", 1]], "cover_n": 120, "cover_s": 1.0,
		"marks": [["House", Vector2(-8.0, 10.9), 0.8, 1.8], ["House", Vector2(10.5, -10.8), 0.75, 1.7], ["Granary", Vector2(-16.6, 11.0), 0.8, 1.4],
			["Shaduf", Vector2(3.7, -11.0), 0.85, 1.4, {"yaw": PI}], ["Boat", Vector2(1.55, -11.9), 0.85, 1.2, {"force": true, "yaw": PI * 0.5 - 0.1}],
			["Boat", Vector2(-1.25, 11.8), 0.8, 1.2, {"force": true, "yaw": PI * 0.5 + 0.08}]]},
	"desert": {"kit": "bronze_decor_desert", "count": 80, "ambient": true,
		"scatter": [["Palm_A", 7], ["Palm_B", 5], ["Acacia_A", 6], ["Acacia_B", 6], ["Scrub_A", 10], ["Scrub_B", 10], ["Dune_A", 9], ["Dune_B", 9],
			["Rock_A", 6], ["Rock_B", 6], ["Rock_C", 4], ["Column_A", 4], ["Column_C", 4], ["Blocks", 4]],
		"cover": [["Tuft", 1]], "cover_n": 45, "cover_s": 0.75,
		"marks": [["Pyramid", Vector2(-2.0, -14.6), 1.0, 5.2, {"force": true, "yaw": 0.0}], ["Obelisk", Vector2(4.6, -10.7), 0.9, 1.0, {"yaw": 0.0}],
			["Obelisk", Vector2(-8.6, -10.7), 0.9, 1.0, {"yaw": 0.0}], ["Ruin", Vector2(-9.0, 11.0), 0.8, 2.3], ["Ruin", Vector2(6.0, 11.2), 0.75, 2.3]]},
	"canyon": {"kit": "bronze_decor_canyon", "count": 75, "ambient": true,
		"scatter": [["Mesa_A", 8], ["Mesa_B", 9], ["Mesa_C", 5], ["Hoodoo", 6], ["Rock_A", 9], ["Rock_B", 9], ["Rock_C", 7], ["Scrub_A", 8],
			["Dead_A", 5], ["Ore_A", 3], ["Ore_B", 3], ["Cart", 2], ["Timbers", 3]],
		"cover": [["Tuft", 1]], "cover_n": 40, "cover_s": 0.7,
		"marks": [["Mine", Vector2(-6.0, -11.0), 0.9, 2.7], ["Smelter", Vector2(-12.0, 10.8), 0.9, 1.9], ["Mesa_C", Vector2(12.0, -11.6), 1.6, 2.2],
			["Mine", Vector2(4.0, 11.4), 0.8, 2.7]]},
}


## v0.9.28: a theme's HQ kit is used once its GLB is in the game.
func _v2_kit(th: String) -> bool:
	return _style2() and DECOR_V2.has(th) and ResourceLoader.exists("res://assets/decor/%s.glb" % str(DECOR_V2[th].kit))


## How far p is from the nearest river's bank (negative: in the water).
func _river_gap(p: Vector2) -> float:
	var best := INF
	for rv in map.get("rivers", []):
		var pts: Array = rv.pts
		for i in pts.size() - 1:
			var a := Vector2(pts[i][0], pts[i][1])
			var b := Vector2(pts[i + 1][0], pts[i + 1][1])
			var ab := b - a
			var t := clampf((p - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
			best = minf(best, p.distance_to(a + ab * t) - float(rv.get("width", 2.0)) * 0.5)
	return best
var _decor_lib := {}


func _decor_theme() -> Dictionary:
	return DECOR_V2.get(str(map.get("theme", "meadow")), {})


func _decor_mesh(name: String) -> Mesh:
	if _decor_lib.is_empty():
		var src := _inst("res://assets/decor/%s.glb" % str(_decor_theme().get("kit", "stone_decor")))
		var hq := src.find_child("*_Outline", true, false) == null      # v0.9.18 HQ kits: baked atlas, outline pass
		for mi in src.find_children("*", "MeshInstance3D", true, false):
			var mesh: Mesh = (mi as MeshInstance3D).mesh
			if hq and mesh != null:
				mesh = _kit_outline(mesh, str(mi.name) in ["Tuft", "Flowers"])
				mesh = _kit_lava(mesh, str(mi.name) == "Volcano")
			_decor_lib[str(mi.name)] = mesh
		src.free()
	return _decor_lib.get(name)


## HQ map kits share one baked material: props get the cartoon outline pass (as HQ units do), grass and flowers (thin
## blades) a copy without it. Glowing surfaces (lava) are left alone.
var _kit_mats := {}
func _kit_outline(mesh: Mesh, thin: bool) -> Mesh:
	if Progress.gfx_level() >= 2:
		return mesh
	var m2: Mesh = mesh.duplicate()
	for si in m2.get_surface_count():
		var mat := m2.surface_get_material(si) as BaseMaterial3D
		if mat == null or mat.emission_enabled:
			continue
		var key := "%d_%s" % [mat.get_instance_id(), "thin" if thin else "solid"]
		if not _kit_mats.has(key):
			var mc: BaseMaterial3D = mat.duplicate()
			if not thin:
				if _hq_outline_mat == null:
					_hq_outline_mat = ShaderMaterial.new()
					_hq_outline_mat.shader = Shader.new()
					_hq_outline_mat.shader.code = HQ_OUTLINE_SHADER
				mc.next_pass = _hq_outline_mat
			_kit_mats[key] = mc
		m2.surface_set_material(si, _kit_mats[key])
	return m2


## v0.9.21: lava never stands still. The kit's flat glowing lava gets a shader where molten streaks slide down slopes and
## (on the volcano) crust plates drift on the crater pool; lava pools on the map get a molten surface with drifting
## crust, glowing cracks and bubbles that swell and burst (game/shaders/).
var _lava_mats := {}
func _kit_lava(mesh: Mesh, plates: bool) -> Mesh:
	var m2: Mesh = null
	for si in mesh.get_surface_count():
		var mat := mesh.surface_get_material(si)
		if mat == null or not str(mat.resource_name).begins_with("Glow_glow_lava"):
			continue
		var key := "flow_plates" if plates else "flow"
		if not _lava_mats.has(key):
			var lm := ShaderMaterial.new()
			lm.shader = load("res://game/shaders/lava_flow.gdshader")
			lm.set_shader_parameter("plates", plates)
			_lava_mats[key] = lm
		if m2 == null:
			m2 = mesh.duplicate()
		m2.surface_set_material(si, _lava_mats[key])
	return m2 if m2 != null else mesh


func _lava_pool_mat(radius: float, seed: float) -> ShaderMaterial:
	var lm := ShaderMaterial.new()
	lm.shader = load("res://game/shaders/lava_pool.gdshader")
	lm.set_shader_parameter("radius", radius)
	lm.set_shader_parameter("seed", seed)
	return lm


## One MultiMesh (one draw call) per prop type, plus one for its outline shell.
func _decor_batch(name: String, xforms: Array, shadow := true) -> void:
	if xforms.is_empty():
		return
	for part in [name, name + "_Outline"]:
		var mesh := _decor_mesh(part)
		if mesh == null:
			continue
		if part.ends_with("_Outline") and Progress.gfx_level() >= 2:
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = xforms.size()
		for i in xforms.size():
			mm.set_instance_transform(i, xforms[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		var cast: bool = shadow and not part.ends_with("_Outline")
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cast else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mmi)


func _decor_single(name: String, pos: Vector3, yaw := 0.0, s := 1.0, parent: Node3D = null) -> Node3D:
	var n := Node3D.new()
	n.position = pos
	n.rotation.y = yaw
	n.scale = Vector3.ONE * s
	(parent if parent != null else self).add_child(n)
	for part in [name, name + "_Outline"]:
		var mesh := _decor_mesh(part)
		if mesh == null or (part.ends_with("_Outline") and Progress.gfx_level() >= 2):
			continue
		var mi := MeshInstance3D.new()
		mi.mesh = mesh
		if part.ends_with("_Outline"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		n.add_child(mi)
	return n


func _pick_weighted(list: Array, r: RandomNumberGenerator) -> String:
	var tot := 0
	for it in list:
		tot += int(it[1])
	var x := r.randi() % maxi(tot, 1)
	for it in list:
		x -= int(it[1])
		if x < 0:
			return str(it[0])
	return str(list[0][0])


func _build_decor_v2() -> void:
	var dt := _decor_theme()
	var r := RandomNumberGenerator.new()
	r.seed = 11
	var b: Array = map.bounds
	var b0: Array = b
	var taken := []      # [Vector2, radius] of landmarks so scatter keeps clear of them
	for mk in dt.marks:
		var p: Vector2 = mk[1]
		var ok := false
		var opt: Dictionary = mk[4] if mk.size() > 4 else {}
		var jit := r.randf_range(-0.5, 0.5)
		for tries in 30:
			if _decor_free(p, 0.6) or mk[0] == "Volcano" or bool(opt.get("force", false)):
				ok = true
				break
			p = mk[1] + Vector2(r.randf_range(-2.5, 2.5), r.randf_range(-1.2, 1.2))
		if ok:
			var yaw: float = float(opt.yaw) if opt.has("yaw") else jit + (PI if p.y > 0 else 0.0)
			var n := _decor_single(mk[0], _v3(p), yaw, mk[2])
			taken.append([p, float(mk[3])])
			if mk[0] == "Boat":                   # (rocking gently on the current)
				effects.append({"node": n, "t": r.randf() * 6.0, "life": INF, "kind": "bob", "y0": n.position.y})
			elif mk[0] == "Smelter":              # (its furnace burns)
				_campfire(n, Vector3(0, 1.22, 0), 1.6, 0.36)
			if mk[0] == "Volcano":
				n.rotation.y = 0.0
				var vl := OmniLight3D.new()
				vl.light_color = Color(1, 0.5, 0.2)
				vl.light_energy = 3.0
				vl.omni_range = 9.0
				vl.position = Vector3(0, 5.0, 0)
				n.add_child(vl)
	var batches := {}
	var put := func(nm: String, p: Vector2, s: float, yaw: float) -> void:
		if not batches.has(nm):
			batches[nm] = []
		(batches[nm] as Array).append(Transform3D(Basis(Vector3.UP, yaw).scaled(Vector3.ONE * s), _v3(p)))
	var placed := 0
	var tries2 := 0
	while placed < int(dt.count) and tries2 < 3000:
		tries2 += 1
		var p2 := Vector2(r.randf_range(-19.5, 17.5), r.randf_range(-12.0, 12.0))
		if not _decor_free(p2):
			continue
		var clear := true
		for tk in taken:
			if p2.distance_to(tk[0]) < float(tk[1]) + 0.9:
				clear = false
				break
		if not clear:
			continue
		placed += 1
		var nm := _pick_weighted(dt.scatter, r)
		var s := r.randf_range(0.75, 1.25) * (0.9 if nm.begins_with("Rock") else 1.0)
		put.call(nm, p2, s, r.randf() * TAU)
	if dt.has("shore"):                               # v0.9.28: clumps along the river banks, outside the playfield
		for rv in map.get("rivers", []):
			var rpts: Array = rv.pts
			var rhalf := float(rv.get("width", 2.0)) * 0.5
			for i in rpts.size() - 1:
				var ra := Vector2(rpts[i][0], rpts[i][1])
				var rb := Vector2(rpts[i + 1][0], rpts[i + 1][1])
				var rlen := ra.distance_to(rb)
				var rn := (rb - ra).normalized().orthogonal()
				var rd := 0.0
				while rd < rlen:
					for side in [-1.0, 1.0]:
						var rq: Vector2 = ra + (rb - ra) * (rd / rlen) + rn * float(side) * (rhalf + r.randf_range(0.0, 0.35))
						var rin: bool = rq.x > b0[0] - 0.4 and rq.x < b0[2] + 0.4 and rq.y > b0[1] - 0.4 and rq.y < b0[3] + 0.4
						if not rin and sim.dist_to_path(rq) > 2.0 and r.randf() < 0.8:
							put.call(_pick_weighted(dt.shore, r), rq, r.randf_range(0.6, 1.0), r.randf() * TAU)
					rd += r.randf_range(0.9, 1.5)
	# ground cover inside the playfield, off the road and clear of no-build zones
	for i in int(dt.cover_n):
		var p3 := Vector2(r.randf_range(b[0], b[2]), r.randf_range(b[1], b[3]))
		if sim.dist_to_path(p3) < float(map.get("path_width", 1.7)) * 0.5 + 0.5:
			continue
		var in_block := false
		for bl in map.get("blockers", []):
			if p3.distance_to(Vector2(bl[0], bl[1])) < float(bl[2]) + 0.4:
				in_block = true
		if in_block or _river_gap(p3) < 0.25:
			continue
		var cs: float = float(dt.get("cover_s", 0.6 if dt.kit != "stone_decor" else 1.0))
		put.call(_pick_weighted(dt.cover, r), p3, r.randf_range(0.8, 1.3) * cs, r.randf() * TAU)
	for nm in batches:
		_decor_batch(nm, batches[nm], not (nm in ["Tuft", "Flowers"]))


func _build_cave_v2(p: Vector2) -> void:
	var n := _decor_single("Cave", _v3(p) + Vector3(0.1, 0, 0), 0.0, 0.95)
	var fire_pos := Vector3(-1.6, 0, 1.75)
	# the hearth: three kit logs crossed in a ring of kit stones
	for k in 3:
		var lg := _decor_single("Log", fire_pos + Vector3(0, 0.02, 0), k * 1.05, 0.5, n)
		lg.rotation.z = 0.12
	for k in 7:
		var a := TAU * k / 7.0
		_decor_single("Rock_B", fire_pos + Vector3(cos(a) * 0.46, 0.0, sin(a) * 0.46), a * 1.7, 0.16, n)
	_campfire(n, fire_pos)
	_ambient_fx(n.position + fire_pos)


# ---------------------------------------------------------------- baked scenery (eras 2-10)
# The base, decor and no-build zones of every map outside the Stone Age are built here at runtime
# (game.gd / era_decor.gd), then the static parts are swapped for a baked version made offline:
#   godot -- --demo --export-decor --map=<id>     exports the static meshes  (tools/bake_decor.sh)
#   tools/blender/bake_decor.py                    bevels, bakes ambient occlusion (props on props and on
#                                                  the ground), adds outlines, merges into a few meshes
#   assets/decor/maps/<id>.glb                     loaded here; its root is named "Decor_<n>" (n = mesh count)
# Animated parts (spinners, fires, pulsing glows, smoke, water, lights) stay live. If the code that builds
# the scenery changes and the count no longer matches, the runtime scenery is kept (rebake to update).
var _decor_roots: Array = []


func _decor_static() -> Array:
	var anim := {}
	for fx in effects:
		for k in ["node", "pool", "f1", "f2"]:
			if fx.has(k) and fx[k] is Node:
				anim[fx[k]] = true
	var out := []
	for r in _decor_roots:
		_decor_collect(r as Node, anim, out)
	return out


func _decor_collect(n: Node, anim: Dictionary, out: Array) -> void:
	if anim.has(n) or n is Light3D:
		return
	if n is MeshInstance3D and n.get_child_count() == 0:
		var mi := n as MeshInstance3D
		var m := mi.material_override as BaseMaterial3D
		if m == null and mi.mesh != null and mi.mesh.get_surface_count() > 0:
			m = mi.mesh.surface_get_material(0) as BaseMaterial3D
		if mi.mesh is PrimitiveMesh and mi.visible and m != null and m.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED \
				and m.billboard_mode == BaseMaterial3D.BILLBOARD_DISABLED and not m.has_meta("ed_pulse") \
				and mi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
			out.append(mi)
		return
	for c in n.get_children():
		_decor_collect(c, anim, out)


func _swap_baked_decor() -> void:
	if not _style2() or _v2_kit(str(map.get("theme", ""))):
		return
	var path := "res://assets/decor/maps/%s.glb" % map_id
	if not ResourceLoader.exists(path):
		return
	var list := _decor_static()
	var baked := _inst(path)
	var want := -1
	var sig := -1
	for c in [baked] + baked.get_children():
		if str(c.name).begins_with("Decor_"):
			var tag := str(c.name).trim_prefix("Decor_").get_slice(".", 0)
			want = int(tag.get_slice("_", 0))
			if tag.get_slice_count("_") > 1:
				sig = int(tag.get_slice("_", 1))
	if want != list.size() or sig != _decor_sig(list):
		push_warning("baked decor for %s is stale (%d meshes / sig %d, now %d / %d): keeping runtime scenery" % [map_id, want, sig, list.size(), _decor_sig(list)])
		baked.free()
		return
	for mi in list:
		(mi as Node).queue_free()
	for ol in baked.find_children("*_Outline", "MeshInstance3D", true, false):
		(ol as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		(ol as MeshInstance3D).visible = Progress.gfx_level() < 2
	add_child(baked)


## Fingerprint of where the static scenery sits, so a bake made for an older layout is never swapped in.
func _decor_sig(list: Array) -> int:
	var h := 0
	for mi in list:
		var p: Vector3 = (mi as MeshInstance3D).global_position
		h = (h * 31 + int(round(p.x * 10.0)) * 7 + int(round(p.z * 10.0)) * 13) % 1000003
	return absi(h)


func _export_decor(path: String) -> void:
	var list := _decor_static()
	var sc := Node3D.new()
	sc.name = "Decor_%d_%d" % [list.size(), _decor_sig(list)]
	var cache := {}
	for mi in list:
		var src := (mi as MeshInstance3D).mesh
		var mat: Material = (mi as MeshInstance3D).material_override
		var key := "%d_%d" % [src.get_instance_id(), mat.get_instance_id() if mat != null else 0]
		if not cache.has(key):
			var am := ArrayMesh.new()
			for si in src.get_surface_count():
				am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, src.surface_get_arrays(si))
				am.surface_set_material(si, mat if mat != null else src.surface_get_material(si))
			cache[key] = am
		var m2 := MeshInstance3D.new()
		m2.mesh = cache[key]
		m2.transform = (mi as MeshInstance3D).global_transform
		sc.add_child(m2)
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	doc.append_from_scene(sc, st)
	var err := doc.write_to_filesystem(st, path)
	sc.free()


## v2 no-build zones: ice lakes ringed with snow and crystals, rock outcrops, lava pools ringed with
## glowing basalt. The ground texture still paints the zone itself.
func _blocker_v2(kind: String, n: Node3D, rad: float, r: RandomNumberGenerator) -> bool:
	var th := str(map.get("theme", "meadow"))
	match kind:
		"lake":
			if th == "delta":             # v0.9.28: its water moves in the ground; papyrus and reeds round the shore
				for k in 9:
					var a0 := TAU * k / 9.0 + r.randf() * 0.4
					var rr := rad + r.randf_range(0.05, 0.3)
					_decor_single(["Papyrus", "Reeds", "Papyrus"][k % 3], Vector3(cos(a0) * rr, 0, sin(a0) * rr), r.randf() * TAU, r.randf_range(0.5, 0.72), n)
				return true
			if th != "snow":
				return false
			_mi(_cyl(rad * 0.95, rad * 0.95, 0.02, 32), _mat("ice", Color(0.75, 0.9, 1.0, 0.3), {"rough": 0.05, "metal": 0.3}), n, Vector3(0, 0.03, 0))
			for k in 7:
				var a := TAU * k / 7.0 + r.randf() * 0.4
				var nm := "Ice_B" if k % 3 else "Mound_B"
				_decor_single(nm, Vector3(cos(a) * rad, 0, sin(a) * rad), r.randf() * TAU, r.randf_range(0.5, 0.8), n)
			return true
		"lava":
			for k in 7:
				var a2 := TAU * k / 7.0 + r.randf() * 0.4
				_decor_single(["Rock_A", "Rock_B"][k % 2], Vector3(cos(a2) * rad * 0.95, 0, sin(a2) * rad * 0.95), r.randf() * TAU, r.randf_range(0.45, 0.65), n)
			return false     # keep the old glowing pool, light and pulse on top of the new rim
		"rocks":
			for k in 4:
				var off := Vector2(r.randf_range(-0.5, 0.5), r.randf_range(-0.5, 0.5)) * rad
				_decor_single(["Rock_C", "Rock_A", "Rock_B", "Rock_A"][k], Vector3(off.x, 0, off.y), r.randf() * TAU, r.randf_range(0.7, 1.0) * rad * 0.8, n)
			return true
		"palms":                          # v0.9.28: a grove of date palms on its patch of sand
			for k in 3:
				var a6 := TAU * k / 3.0 + r.randf() * 0.5
				_decor_single(["Palm_A", "Palm_B", "Palm_C"][k], Vector3(cos(a6) * rad * 0.45, 0, sin(a6) * rad * 0.45), r.randf() * TAU, r.randf_range(0.75, 0.95), n)
			return true
		"dune":
			_decor_single("Dune_A", Vector3.ZERO, r.randf() * TAU, rad / 1.15, n)
			_decor_single("Scrub_B", Vector3(rad * 0.55, 0, -rad * 0.35), r.randf() * TAU, 0.85, n)
			return true
		"ruins":
			var spots := [["Column_B", Vector2(-0.45, -0.3), 0.85], ["Column_A", Vector2(0.42, -0.42), 0.9], ["Column_C", Vector2(0.15, 0.45), 1.0],
				["Blocks", Vector2(-0.35, 0.42), 0.8]]
			for sp in spots:
				var o2: Vector2 = sp[1] * rad
				_decor_single(sp[0], Vector3(o2.x, 0, o2.y), r.randf() * TAU, sp[2], n)
			return true
		"pillar":
			_decor_single("Pillar", Vector3.ZERO, r.randf() * TAU, rad / 1.5, n)
			return true
		"ore":                            # a copper pool (moving, turquoise) ringed with malachite
			var pm2 := _lava_pool_mat(rad * 0.85, r.randf() * 10.0)
			pm2.set_shader_parameter("hot", Color(0.72, 1.0, 0.92))
			pm2.set_shader_parameter("warm", Color(0.1, 0.78, 0.62))
			pm2.set_shader_parameter("crust", Color(0.05, 0.15, 0.14))
			pm2.set_shader_parameter("glow", 1.6)
			var pool := _mi(_cyl(rad * 0.85, rad * 0.85, 0.04, 28), pm2, n, Vector3(0, 0.04, 0))
			pool.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			for k in 6:
				var a4 := TAU * k / 6.0 + r.randf() * 0.4
				_decor_single(["Ore_A", "Ore_B"][k % 2], Vector3(cos(a4) * rad * 0.95, 0, sin(a4) * rad * 0.95), r.randf() * TAU, r.randf_range(0.6, 0.85), n)
			var ll := OmniLight3D.new()
			ll.light_color = Color(0.3, 1.0, 0.7)
			ll.light_energy = 0.9
			ll.omni_range = rad * 2.2
			ll.position = Vector3(0, 0.8, 0)
			n.add_child(ll)
			effects.append({"node": n, "life": INF, "t": r.randf() * 5.0, "kind": "lava", "pool": pool, "light": ll})
			return true
	return false


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
		if EraDecor.handles(th):
			EraDecor.build_blocker(self, th, kind, n, rad, r)
			continue
		if _v2_kit(th):
			if _blocker_v2(kind, n, rad, r):
				continue
			if kind == "lava":
				var lava2 := _mi(_cyl(rad * 0.85, rad * 0.85, 0.04, 28), _lava_pool_mat(rad * 0.85, r.randf() * 10.0), n, Vector3(0, 0.04, 0))
				lava2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				var ll2 := OmniLight3D.new()
				ll2.light_color = Color(1, 0.45, 0.15)
				ll2.light_energy = 0.9
				ll2.omni_range = rad * 2.2
				ll2.position = Vector3(0, 0.8, 0)
				n.add_child(ll2)
				effects.append({"node": n, "t": r.randf() * 5.0, "life": INF, "kind": "lava", "pool": lava2, "light": ll2})
				continue
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
				# v0.9.28: these pools move too: the lava-pool shader (drifting crust, glowing cracks, bubbles), in turquoise for
				# the copper pools
				var pm2 := _lava_pool_mat(rad * 0.85, r.randf() * 10.0)
				if not lava:
					pm2.set_shader_parameter("hot", Color(0.72, 1.0, 0.92))
					pm2.set_shader_parameter("warm", Color(0.1, 0.78, 0.62))
					pm2.set_shader_parameter("crust", Color(0.05, 0.15, 0.14))
					pm2.set_shader_parameter("glow", 1.6)
				var pool := _mi(_cyl(rad * 0.85, rad * 0.85, 0.04, 28), pm2, n, Vector3(0, 0.04, 0))
				pool.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
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
	var mfile: String = {"Stone Age": "music_stone_age.wav", "Bronze Age": "music_bronze_age.wav", "Iron Age": "music_iron.ogg",
		"Classical Age": "music_classical.ogg", "Medieval Age": "music_medieval.ogg", "Gunpowder Age": "music_gunpowder.ogg",
		"Industrial Age": "music_industrial.ogg", "Modern Age": "music_modern.ogg", "Digital Age": "music_digital.ogg",
		"The Data Center": "music_datacenter.ogg"}.get(_era(), "music_stone_age.wav")
	music.stream = load("res://assets/audio/" + mfile)
	music.volume_db = -9.0
	music.bus = "Music"
	add_child(music)
	music.finished.connect(func(): music.play())


func _sfx(name: String, vol_db := 0.0, pitch_var := 0.08, min_gap := 0.04) -> void:
	if attract and not name in ["click", "upgrade", "level_up", "coin"]:
		return
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


## A named part of a model; Blender's duplicate suffixes arrive as "Yaw_004", "Arm_005" (Bronze Age units), so those count too.
func _find_part(model: Node, nm: String) -> Node:
	var n := model.find_child(nm, true, false)
	if n == null:
		n = model.find_child(nm + "_0*", true, false)
	return n


func _rig_model(root: Node3D, model: Node3D) -> void:
	var yaw := _find_part(model, "Yaw")
	if yaw == null:
		yaw = model.find_child("Caveman", true, false)
	var arm := _find_part(model, "Arm")
	if arm == null:
		arm = model.find_child("Shoulder_R", true, false)
	if yaw != null:
		root.set_meta("yaw", yaw)
	if arm != null:
		root.set_meta("arm", arm)
		arm.set_meta("rest", arm.rotation.x)
	var orb := _find_part(model, "Orb")
	if orb != null:
		root.set_meta("orb", orb)
	var ap := model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if ap != null and ap.has_animation("Idle"):
		_hq_anim_setup(root, ap)
		_hq_outline(model)
	_rig_extras(root, model)


## HQ models (sculpted, texture-baked, skinned) ship an Idle loop, a combat loop and an attack clip: idle when nothing
## is in range, the combat loop while fighting, the attack on every shot. Slingers call them Whirl / Throw, the other
## towers Combat / Attack. The clip speed follows the game speed, and the attack speeds up to fit the fire rate.
## HQ heroes add one-shot showpieces: Ability (their special) and Cheer (rank up).
const HQ_LOOPS := ["Idle", "Whirl", "Combat"]
const HQ_ONESHOTS := ["Throw", "Attack", "Ability", "Cheer"]
func _hq_anim_setup(root: Node3D, ap: AnimationPlayer) -> void:
	for nm in HQ_LOOPS:
		if ap.has_animation(nm):
			ap.get_animation(nm).loop_mode = Animation.LOOP_LINEAR
	root.set_meta("anim", ap)
	root.set_meta("last_fire", -100.0)
	root.set_meta("clip_combat", "Combat" if ap.has_animation("Combat") else "Whirl")
	root.set_meta("clip_attack", "Attack" if ap.has_animation("Attack") else "Throw")
	ap.play("Idle")
	ap.seek(randf() * ap.current_animation_length, true)


func _hq_anim_tick(tn: Node3D, stunned: bool) -> void:
	var ap: AnimationPlayer = tn.get_meta("anim")
	var cur := ap.current_animation
	var rate: float = float(tn.get_meta("throw_rate", 1.0)) if cur == tn.get_meta("clip_attack") else 1.0
	ap.speed_scale = 0.0 if stunned else float(speed) * rate
	if cur in HQ_ONESHOTS and ap.is_playing():
		return
	var hold: float = float(tn.get_meta("combat_hold", 2.2))
	var want: String = tn.get_meta("clip_combat") if time_s - float(tn.get_meta("last_fire", -100.0)) < hold else "Idle"
	if cur != want:
		ap.play(want, 0.25)


## Plays a one-shot clip (Ability, Cheer) on an HQ model; false when the unit's model has no such clip.
func _hq_play(id: int, clip: String) -> bool:
	if not tower_nodes.has(id):
		return false
	var n: Node3D = tower_nodes[id]
	if not n.has_meta("anim"):
		return false
	var ap: AnimationPlayer = n.get_meta("anim")
	if not ap.has_animation(clip):
		return false
	ap.play(clip, 0.12)
	ap.seek(0.0, true)
	ap.speed_scale = float(speed)
	return true


func _hq_anim_freeze() -> void:
	for n in tower_nodes.values():
		if (n as Node3D).has_meta("anim"):
			((n as Node3D).get_meta("anim") as AnimationPlayer).speed_scale = 0.0
	for n in enemy_nodes.values():
		if is_instance_valid(n) and (n as Node3D).has_meta("anim"):
			((n as Node3D).get_meta("anim") as AnimationPlayer).speed_scale = 0.0


## Cartoon outline for HQ models: a second pass that pushes the surface out along its normals and draws only the
## back faces (works with skinning; no duplicate geometry in the file). Off on MINIMAL graphics.
## The shell is also pushed a few centimetres away from the camera, so it only shows round the silhouette and no
## longer pokes through as dark dashes in tight creases (eyes, brows, hair grooves).
const HQ_OUTLINE_SHADER := """
shader_type spatial;
render_mode unshaded, cull_front, depth_draw_opaque;
uniform float grow = 0.022;
uniform float push = 0.05;
uniform vec3 color : source_color = vec3(0.09, 0.065, 0.05);
void vertex() {
	vec4 v = MODELVIEW_MATRIX * vec4(VERTEX + NORMAL * grow, 1.0);
	v.z -= push;
	POSITION = PROJECTION_MATRIX * v;
}
void fragment() {
	ALBEDO = color;
}
"""
var _hq_outline_mat: ShaderMaterial
func _hq_outline(model: Node3D) -> void:
	if Progress.gfx_level() >= 2:
		return
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh == null or str(m.name) in ["FlickerTorch", "GrassBlades", "Flowers"] or str(m.name).begins_with("Glow") or str(m.name).begins_with("Bubble"):
			continue
		for si in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(si) as BaseMaterial3D
			if mat == null or mat.next_pass != null:
				continue
			if _hq_outline_mat == null:
				_hq_outline_mat = ShaderMaterial.new()
				_hq_outline_mat.shader = Shader.new()
				_hq_outline_mat.shader.code = HQ_OUTLINE_SHADER
			mat.next_pass = _hq_outline_mat


## v2 art: Spin* nodes whirl (slings, rotors, orbiting stones), Flicker* nodes flicker (fires),
## *_Outline meshes are the baked cartoon outline shells (no shadows; off on MINIMAL graphics).
func _rig_extras(root: Node3D, model: Node3D) -> void:
	var spins := model.find_children("Spin*", "Node3D", true, false)
	if not spins.is_empty():
		root.set_meta("spins", spins)
	var flick := model.find_children("Flicker*", "Node3D", true, false)
	if not flick.is_empty():
		root.set_meta("flicker", flick)
	var bub := model.find_children("Bubble*", "Node3D", true, false)
	if not bub.is_empty():
		root.set_meta("bubbles", bub)
	var body_mis := []
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		if not str(mi.name).ends_with("_Outline"):
			body_mis.append(mi)
	root.set_meta("body_mis", body_mis)
	var outlines := []
	for mi in model.find_children("*_Outline", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		m.visible = Progress.gfx_level() < 2
		outlines.append(m)
	if not outlines.is_empty():
		root.set_meta("outlines", outlines)


## A tarred robot that takes a hit: the tar coat with the white flash drawn over it (cached pairs).
var _coat_flash_mats := {}
func _coat_flash(coat: Material, lvl: int) -> Material:
	var key := "%d_%d" % [coat.get_instance_id(), lvl]
	if not _coat_flash_mats.has(key):
		var c2: Material = coat.duplicate()
		c2.next_pass = _flash_mats[lvl]
		_coat_flash_mats[key] = c2
	return _coat_flash_mats[key]


## A robot that takes a hit flashes white for a moment (three shared overlay strengths, no per-robot materials).
var _flash_mats: Array = []
func _hit_flash(n: Node3D) -> void:
	var f: float = n.get_meta("flash", 0.0)
	if f <= 0.0 and not n.has_meta("flash_on"):
		return
	if _flash_mats.is_empty():
		for a in [0.6, 0.35, 0.15]:
			var m := StandardMaterial3D.new()
			m.albedo_color = Color(1, 1, 1, a)
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			_flash_mats.append(m)
	var lvl := -1
	if f > 0.0:
		lvl = 0 if f > 0.66 else (1 if f > 0.33 else 2)
		n.set_meta("flash", maxf(0.0, f - get_process_delta_time() * 7.0))
	var coat: Material = n.get_meta("tar_mat") if n.has_meta("tar_mat") else null
	var want: Material = coat
	if lvl >= 0:
		want = _flash_mats[lvl] if coat == null else _coat_flash(coat, lvl)
	if lvl < 0:
		n.remove_meta("flash_on")
	else:
		n.set_meta("flash_on", true)
	for mi in n.get_meta("body_mis", []):
		(mi as MeshInstance3D).material_overlay = want


func _spin_flicker(n: Node3D, dt: float, rate := 9.0) -> void:
	if n.has_meta("spins"):
		for sp in n.get_meta("spins"):
			(sp as Node3D).rotation.y += dt * rate * (0.22 if str(sp.name).begins_with("SpinSlow") else 1.0)
	if n.has_meta("flicker"):
		var i := 0
		for f in n.get_meta("flicker"):
			var k := 1.0 + 0.14 * sin(time_s * 13.0 + i * 2.1) + 0.06 * sin(time_s * 29.0 + i)
			(f as Node3D).scale = Vector3(2.0 - k, k, 2.0 - k)
			i += 1
	if n.has_meta("bubbles") and rate > 0.0:
		# tar bubbles: each swells slowly, then pops and starts again
		var j := 0
		for b in n.get_meta("bubbles"):
			var ph := fmod(time_s * 0.45 + j * 0.37 + float(n.get_instance_id() % 97) * 0.013, 1.0)
			var sc := 0.0
			if ph < 0.8:
				var g := ph / 0.8
				sc = g * g * (3.0 - 2.0 * g)
			elif ph < 0.86:
				sc = 1.15 * (1.0 - (ph - 0.8) / 0.06)
			(b as Node3D).scale = Vector3.ONE * maxf(sc, 0.001)
			j += 1


func _make_tower_visual(type: String) -> Node3D:
	var root := Node3D.new()
	var model: Node3D = _inst("res://assets/towers/%s.glb" % type)
	model.scale = Vector3.ONE * float(defs.towers[type].get("model_scale", 0.56))
	root.add_child(model)
	_rig_model(root, model)
	_retheme_base(model)
	return root


func _make_hero_visual(id: String) -> Node3D:
	var root := Node3D.new()
	var hd: Dictionary = defs.heroes.heroes[id]
	var model: Node3D = _inst("res://assets/heroes/%s.glb" % id)
	model.scale = Vector3.ONE * float(hd.get("model_scale", 0.55))
	root.add_child(model)
	_rig_model(root, model)
	_retheme_base(model)
	return root


## Tower bases are modelled as grass; on other ground types repaint them to match.
func _retheme_base(model: Node) -> void:
	var key: String = theme.get("base", "")
	if key == "" or not BASE_RECOLOR.has(key):
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
	# a small round portrait of the hero boosting this unit; shown while the unit is selected
	var buff := Sprite3D.new()
	buff.name = "Buff"
	var bp := "res://assets/ui/badge_%s.png" % (sim.hero_id if sim != null else "")
	buff.texture = _res(bp) if ResourceLoader.exists(bp) else null
	buff.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	buff.no_depth_test = true
	buff.render_priority = 2
	buff.pixel_size = 0.0055
	buff.position = Vector3(0, 2.3, 0)
	buff.visible = false
	n.add_child(buff)


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
	tower_nodes[h.id] = n
	_ring_fx(_v3(h.pos, 0.2), 1.6, C_GOLD, 0.6)
	_dust_fx(_v3(h.pos, 0.2), 10, 1.0)
	_sfx("hero_place", -2.0, 0.0)
	n.scale = Vector3(0.5, 1.6, 0.5)
	var tw := create_tween()
	tw.tween_property(n, "scale", Vector3.ONE, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


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
	if t.type == "torsion_catapult" and n.has_meta("anim"):
		_torsion_ammo(n, str(t.stats.get("dtype", "")) == "fire")
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
	var model: Node3D = _inst("res://assets/robots/%s.glb" % type)
	model.scale = Vector3.ONE * float(d.get("model_scale", 0.9))
	model.name = "Model"
	root.add_child(model)
	root.set_meta("legsA", model.find_children("LegA*", "", true, false))
	root.set_meta("legsB", model.find_children("LegB*", "", true, false))
	root.set_meta("body", _find_part(model, "Body"))
	root.set_meta("punch", 0.0)
	_rig_extras(root, model)
	# HQ robots (v0.9.18+) are skinned and animated: a Walk (or Fly) loop whose playback follows their real ground speed
	# (enemies.json walk_speed = the speed the clip matches at 1x, so the feet don't slide), plus one-shots (Summon)
	var ap := model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if ap != null and (ap.has_animation("Walk") or ap.has_animation("Fly")):
		var loop := "Walk" if ap.has_animation("Walk") else "Fly"
		ap.get_animation(loop).loop_mode = Animation.LOOP_LINEAR
		ap.play(loop)
		ap.seek(randf() * ap.current_animation_length, true)
		root.set_meta("anim", ap)
		root.set_meta("loop", loop)
		_hq_outline(model)
		var panel := model.find_child("GlowShieldPanel", true, false) as MeshInstance3D
		if panel != null:              # v0.9.27: the HQ Shield Bot's energy shield: see-through, and down with its shield
			panel.material_override = _atk_mat("shield_panel")
			panel.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			root.set_meta("shield_panel", panel)
	var h: float = float(d.get("bar_h", 1.4))
	if d.get("flying", false):
		model.position.y = 0.9           # flyers hover above the road (only some towers can reach them)
		h += 0.9
		var sh := _mi(_cyl(0.32, 0.32, 0.01, 12), _mat("fly_shadow", Color(0, 0, 0, 0.3), {"unshaded": true}), root, Vector3(0, 0.03, 0))
		sh.scale = Vector3.ONE * float(d.get("size", 0.5)) * 2.0
	if d.get("cloak", false):
		# see-through "ghost" copies of every surface material, swapped in while the robot is hidden
		var swaps := []
		for mi in model.find_children("*", "MeshInstance3D", true, false):
			var mesh: Mesh = (mi as MeshInstance3D).mesh
			if mesh == null or str(mi.name).ends_with("_Outline"):
				continue
			for si in mesh.get_surface_count():
				var sm := mesh.surface_get_material(si) as BaseMaterial3D
				if sm == null:
					continue
				var key := "ghost_%d" % sm.get_instance_id()
				if not mats.has(key):
					var gm: BaseMaterial3D = sm.duplicate()
					gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
					gm.albedo_color.a = 0.22
					gm.emission_enabled = true
					gm.emission = Color(0.3, 0.9, 1.0)
					gm.emission_energy_multiplier = 0.25
					gm.next_pass = null          # (no opaque HQ outline round a cloaked robot)
					mats[key] = gm
				swaps.append([mi, si, mats[key]])
		root.set_meta("ghost", swaps)
	# burning: the campfire's flame sprite over the robot (v0.9.18; was a six-sided emissive cone)
	var flame := _mi(_flame_quad(0.46, 0.66), _campfire_mat("outer"), root, Vector3(0, h * 0.3, 0))
	flame.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	flame.name = "Burn"
	flame.visible = false
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
	if d.has("shield") and not root.has_meta("shield_panel"):   # (the HQ Shield Bot shows its shield on its panel)
		# v0.9.27: a glowing rim instead of a milky sphere, so the robot inside stays readable
		var bm := ShaderMaterial.new()
		bm.shader = load("res://game/shaders/shield_bubble.gdshader")
		var boss: bool = d.get("boss", false)
		var br: float = 0.75 if not boss else 2.2
		var bubble := _mi(_sph(br, 24), bm, root, Vector3(0, br * 0.85, 0))
		if boss and root.has_meta("anim"):         # (an HQ boss: a dome hugging its body, not a ball over it)
			bubble.scale = Vector3(1.0, 0.62, 1.0)
			bubble.position.y = 0.95
		bubble.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
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
	var fgm := _mat("bar_fg", Color(0.4, 1.0, 0.3), {"unshaded": true, "billboard": true, "nodepth": true})
	fgm.render_priority = 3      # always on top of its dark background (same depth = flicker)
	var fg := _mi(q, fgm, bar, Vector3.ZERO)
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
	if attract:
		return
	if not Progress.setting("popups") and text.begins_with("+"):
		return
	var l := Label3D.new()
	l.text = text
	l.font = FONT
	l.font_size = size
	l.outline_size = 14
	l.outline_modulate = Color(0.05, 0.08, 0.13)
	l.pixel_size = 0.01
	l.modulate = col
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.position = pos
	add_child(l)
	effects.append({"node": l, "t": 0.0, "life": 0.9, "kind": "text"})


# Effects share cached meshes (one per shape, scaled per node) and respect a live-effect cap,
# so heavy fights can't pile up nodes and resources (the Pixel 10 PowerVR lesson).
var _fx_meshes := {}


func _fx_mesh(key: String) -> Mesh:
	if not _fx_meshes.has(key):
		match key:
			"cube":
				_fx_meshes[key] = _box(1, 1, 1)
			"spark":
				_fx_meshes[key] = _box(0.04, 0.04, 0.22)
			"flash":
				var fq := QuadMesh.new()             # a soft glowing billboard burst (v0.9.18; was a 10-sided sphere)
				fq.size = Vector2(1.3, 1.3)
				_fx_meshes[key] = fq
			"dust":
				var dq := QuadMesh.new()            # a soft round billboard puff (v0.9.18; was a 6-sided sphere)
				dq.size = Vector2(0.55, 0.55)
				_fx_meshes[key] = dq
			"pebble":
				_fx_meshes[key] = _sph(0.5, 4)
			"disc":
				_fx_meshes[key] = _cyl(1, 1, 0.02, 16)
			"mote":
				var q := QuadMesh.new()
				q.size = Vector2(0.16, 0.16)
				_fx_meshes[key] = q
	return _fx_meshes[key]


var _mote_texture: Texture2D
func _mote_tex() -> Texture2D:
	if _mote_texture == null:
		var gt := GradientTexture2D.new()
		gt.width = 64
		gt.height = 64
		gt.fill = GradientTexture2D.FILL_RADIAL
		gt.fill_from = Vector2(0.5, 0.5)
		gt.fill_to = Vector2(1.0, 0.5)
		var gr := Gradient.new()
		gr.offsets = PackedFloat32Array([0.0, 0.35, 1.0])
		gr.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.55), Color(1, 1, 1, 0)])
		gt.gradient = gr
		_mote_texture = gt
	return _mote_texture


func _fx_room(need := 1) -> bool:
	var cap: int = [240, 150, 80][clampi(Progress.gfx_level(), 0, 2)]
	return effects.size() + need <= cap


func _debris_fx(pos: Vector3, count: int, big := false) -> void:
	if not _fx_room(count * 2 + 3):
		count = mini(count, 2)
		if not _fx_room(3):
			return
	var cols := [Color(0.86, 0.88, 0.92), Color(0.5, 0.54, 0.6), Color(0.12, 0.13, 0.16)]
	for i in count:
		var col: Color = cols[i % 3]
		var sz := randf_range(0.08, 0.16) * (2.0 if big else 1.0)
		var c := _mi(_fx_mesh("cube"), _mat("debris_%d" % (i % 3), col, {"metal": 0.4, "rough": 0.4}), self, pos, Vector3.ZERO, Vector3.ONE * sz)
		var a := randf() * TAU
		var sp := randf_range(1.5, 3.5) * (1.8 if big else 1.0)
		effects.append({"node": c, "t": 0.0, "life": randf_range(0.5, 0.8), "kind": "debris", "s": sz,
			"v": Vector3(cos(a) * sp, randf_range(3, 6), sin(a) * sp)})
	for i in (count + 2):
		var s := _mi(_fx_mesh("spark"), _mat("spark", Color(1, 0.3, 0.1), {"emit": Color(1, 0.25, 0.05), "emit_e": 3.0, "unshaded": true}), self, pos)
		var a2 := randf() * TAU
		var v := Vector3(cos(a2), randf_range(0.4, 1.4), sin(a2)) * randf_range(4, 7)
		s.look_at_from_position(pos, pos + v, Vector3.UP if absf(v.normalized().y) < 0.95 else Vector3.RIGHT)
		effects.append({"node": s, "t": 0.0, "life": 0.3, "kind": "spark", "v": v})
	if _flash_mat == null:
		_flash_mat = StandardMaterial3D.new()
		_flash_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_flash_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		_flash_mat.billboard_keep_scale = true          # (the burst grows with its node's scale)
		_flash_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_flash_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		_flash_mat.albedo_color = Color(1.0, 0.62, 0.28, 1.0)
		_flash_mat.albedo_texture = _mote_tex()
	var f := _mi(_fx_mesh("flash"), _flash_mat, self, pos)
	f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.append({"node": f, "t": 0.0, "life": 0.18, "kind": "flash", "s": 1.6 if big else 0.8})


var _flash_mat: StandardMaterial3D


## Dust and smoke puffs: soft round billboards (the radial mote texture), one cached material per colour.
var _dust_mats := {}
func _puff_mat(col: Color) -> StandardMaterial3D:
	var key := col.to_html()
	if not _dust_mats.has(key):
		var dm := StandardMaterial3D.new()
		dm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		dm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		dm.billboard_keep_scale = true                   # (puffs grow with their node's scale)
		dm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		dm.albedo_color = col
		dm.albedo_texture = _mote_tex()
		_dust_mats[key] = dm
	return _dust_mats[key]


func _dust_fx(pos: Vector3, count: int, spread := 0.6, col := Color(0.78, 0.68, 0.5, 0.7)) -> void:
	if not _fx_room(count):
		count = mini(count, 2)
		if not _fx_room(count):
			return
	var dmat := _puff_mat(col)
	for i in count:
		var d := _mi(_fx_mesh("dust"), dmat, self, pos)
		d.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var a := TAU * i / count + randf() * 0.4
		effects.append({"node": d, "t": 0.0, "life": randf_range(0.35, 0.6), "kind": "dust",
			"v": Vector3(cos(a), 0.6, sin(a)) * spread * randf_range(1.2, 2.2)})


## v2: a rock or club hit kicks up a puff of dust and a couple of pebbles.
func _pebble_fx(pos: Vector3, count := 2) -> void:
	if not _fx_room(count + 2):
		return
	_dust_fx(pos, 2, 0.35)
	for i in count:
		var sz := randf_range(0.06, 0.1)
		var c := _mi(_fx_mesh("pebble"), _mat("pebble_%d" % (i % 2), [Color(0.55, 0.53, 0.5), Color(0.4, 0.3, 0.2)][i % 2]), self, pos,
			Vector3.ZERO, Vector3.ONE * sz)
		var a := randf() * TAU
		effects.append({"node": c, "t": 0.0, "life": 0.5, "kind": "debris", "s": sz,
			"v": Vector3(cos(a) * 1.6, randf_range(2.5, 4.0), sin(a) * 1.6)})


# ---------------------------------------------------------------- Stone Age attacks (v0.9.20)
# The pulse and melee units used to draw an expanding ring. Now their hits land on the robots they hit (the sim's
# "pulse" and "slam" events list them): the Tar Pit Shaman flings tar globs that splat and leave puddles, Mara makes
# stone and quartz spikes burst up under them, the Club Warrior's smash sends a shock of dirt out to each one, and
# boulders smash into dust, flying rock and a crater. Timed to the units' clips (the RELEASE / SMASH frames in
# tools/blender/hq/anim_shaman.py, anim_mara.py, anim_club.py).
# The frame of each unit's Attack clip its hit leaves at, in the clip's own frames. The HQ .glb clips run at CLIP_FPS
# (Blender's 24 fps; Godot re-samples them at 30 Hz on import), so a frame inside a held pose is picked where there is one
# (the spear's full reach holds over frames 6-10: 7; the Sun Priest's strike over 10-18: 11), where the 30 Hz samples
# either side of it agree.
const CLIP_FPS := 24.0
const ATTACK_FRAME := {"tar_shaman": 8, "mara": 10, "club_warrior": 4, "spear_guard": 7, "kira": 11, "tarek": 2, "torsion_catapult": 7, "sun_priest": 11}
var _fx_queue: Array = []
var _atk_cache: Dictionary = Progress.fx_cache    # meshes, materials, textures: built once per app run (kept in the
                                                 # autoload, so they outlive scene reloads and are freed cleanly at exit)
var _hide_bars := false                      # test captures only
var _atk_pending := {}                       # robot id -> true: a delayed hit is coming this frame's events
var _doomed := {}                            # robot id -> its kill event, held until the hit lands


## Whether unit `id` has its HQ model (with clips): only then do the Bronze Age attacks time their effects to the clip.
func _hq_clips(id: int) -> bool:
	return tower_nodes.has(id) and is_instance_valid(tower_nodes[id]) and (tower_nodes[id] as Node3D).has_meta("anim")


## Real seconds until frame `frame` of the attack clip that just started on unit `id` (0 for models without clips).
func _clip_delay(id: int, frame: int) -> float:
	if not tower_nodes.has(id) or not (tower_nodes[id] as Node3D).has_meta("anim"):
		return 0.0
	var rate := float((tower_nodes[id] as Node3D).get_meta("throw_rate", 1.0)) * float(speed)
	return float(frame) / CLIP_FPS / maxf(rate, 0.01)

## Runs `fn` on the frame the attack clip that just started on unit `uid` reaches clip frame `frame` (_on_clip: a timer
## set now runs a frame ahead of a clip restarted at the end of its last attack, and drifts if the game speed changes
## mid-clip). A model without clips runs it after `fallback` real seconds. Returns how long that is at 1x, which no game
## speed makes longer in real seconds: the hold for the robots it will hit (_hold_hit).
func _at_attack_frame(uid: int, frame: float, fallback: float, fn: Callable) -> float:
	if not _hq_clips(uid):
		_fx_after(fallback, fn)
		return fallback
	var tn: Node3D = tower_nodes[uid]
	var clip := str(tn.get_meta("clip_attack", "Attack"))
	var rate := maxf(float(tn.get_meta("throw_rate", 1.0)), 0.01)
	var at := frame / CLIP_FPS
	_fx_after(0.0, func() -> void: _on_clip(uid, clip, at, at / rate, fn))
	return at / rate


## A pulse unit turns to fling at the robots it hits (it faces the camera again a moment after its last attack).
func _face_targets(id: int, u: Dictionary, targets: Array) -> void:
	if not tower_nodes.has(id):
		return
	for tid in targets:
		var e = sim._enemy_by_id(int(tid))
		if e != null:
			var d: Vector2 = (e.pos as Vector2) - (u.pos as Vector2)
			if d.length() > 0.05:
				(tower_nodes[id] as Node3D).set_meta("face_to", d.normalized())
				(tower_nodes[id] as Node3D).set_meta("face_t", time_s)
			return


## Where robot `tid` is now (its model if it has one, else the sim), lifted by `up`; INF when it's gone.
func _robot_point(tid: int, up: float) -> Vector3:
	if enemy_nodes.has(tid) and is_instance_valid(enemy_nodes[tid]):
		return (enemy_nodes[tid] as Node3D).position + Vector3(0, up, 0)
	var e = sim._enemy_by_id(tid)
	return _v3(e.pos, up) if e != null else Vector3.INF


func _atk_mat(key: String) -> StandardMaterial3D:
	if _atk_cache.has(key):
		return _atk_cache[key]
	var m := StandardMaterial3D.new()
	match key:
		"tar":                                       # glossy black tar
			m.albedo_color = Color(0.05, 0.038, 0.03)
			m.roughness = 0.2
			m.metallic_specular = 0.75
		"tar_hot":                                   # burning tar (Path B): red-hot, glowing
			m.albedo_color = Color(0.22, 0.06, 0.02)
			m.roughness = 0.25
			m.emission_enabled = true
			m.emission = Color(1.0, 0.33, 0.05)
			m.emission_energy_multiplier = 0.9
		"puddle", "puddle_hot":
			# painted, not lit: a lit glossy plane mirrors the sky at the game's low angles and reads as a pale patch
			m.albedo_texture = _puddle_tex(key == "puddle_hot")
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		"crack", "crater":
			m.albedo_texture = _crack_tex(key == "crater")
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.albedo_color = Color(0.17, 0.12, 0.08, 0.9)
			m.roughness = 1.0
		"spike_stone":
			m.albedo_color = Color(0.56, 0.46, 0.36)
			m.roughness = 0.9
			m.vertex_color_use_as_albedo = true
		"spike_quartz":
			m.albedo_color = Color(0.72, 0.5, 1.0)
			m.roughness = 0.25
			m.vertex_color_use_as_albedo = true
			m.emission_enabled = true
			m.emission = Color(0.45, 0.2, 0.85)
			m.emission_energy_multiplier = 0.55
		"chunk":
			m.albedo_color = Color(0.55, 0.52, 0.48)
			m.roughness = 0.95
		"stone_ball":                                # the Torsion Catapult's dressed limestone ball (v0.9.23)
			m.albedo_color = Color(0.86, 0.8, 0.68)
			m.roughness = 0.9
		"pot":                                       # its pitch pots: fired clay, black bands, straw (vertex colours)
			m.vertex_color_use_as_albedo = true
			m.roughness = 0.75
		"shard":
			m.albedo_color = Color(0.7, 0.36, 0.2)
			m.roughness = 0.8
		"clod":                                      # earth thrown up by a smash
			m.albedo_color = Color(0.42, 0.31, 0.21)
			m.roughness = 1.0
		"arrow_spark":                               # a bronze arrowhead striking steel (v0.9.21)
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.albedo_color = Color(1.0, 0.9, 0.55)
		"lance":                                     # the Spear Guard's lance of light (vertex colours fade it to the tail)
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.vertex_color_use_as_albedo = true
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.cull_mode = BaseMaterial3D.CULL_DISABLED
			m.albedo_color = Color(1.0, 0.86, 0.5)
		"lance_flash":                               # where it strikes
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
			m.billboard_keep_scale = true
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.albedo_color = Color(1.0, 0.9, 0.6)
			m.albedo_texture = _mote_tex()
		"fury_wave", "fury_ring":                      # Forge Fury's wave of heat and the glow under each tower
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.vertex_color_use_as_albedo = true
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.cull_mode = BaseMaterial3D.CULL_DISABLED
			m.albedo_color = Color(1.0, 0.5, 0.16) if key == "fury_wave" else Color(1.0, 0.42, 0.1)
		"shield_panel", "shield_shard":               # the Shield Bot's energy shield, and its shards when it breaks
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.cull_mode = BaseMaterial3D.CULL_DISABLED
			m.albedo_color = Color(0.3, 0.85, 1.0, 0.5) if key == "shield_panel" else Color(0.5, 0.95, 1.0, 0.9)
		"heal_mote":                                  # green motes off a mended robot
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
			m.billboard_keep_scale = true
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.albedo_color = Color(0.4, 1.0, 0.5)
			m.albedo_texture = _mote_tex()
		"hammer_spark":                               # sparks off the red-hot hammer and the anvil
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.albedo_color = Color(1.0, 0.74, 0.32)
		"hammer_hot":                                 # the hammer's red-hot striking face
			m.albedo_color = Color(1.0, 0.46, 0.14)
			m.emission_enabled = true
			m.emission = Color(1.0, 0.4, 0.08)
			m.emission_energy_multiplier = 1.6
		"hammer_bronze":
			m.albedo_color = Color(0.8, 0.52, 0.24)
			m.metallic = 0.5
			m.roughness = 0.35
		"hammer_wood":
			m.albedo_color = Color(0.54, 0.37, 0.21)
			m.roughness = 0.8
		"hammer_cord":
			m.albedo_color = Color(0.62, 0.12, 0.07)
			m.roughness = 0.9
		"slash", "flare_wave":                         # Kira's cuts and her flare's wave (vertex colours fade them)
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.vertex_color_use_as_albedo = true
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.cull_mode = BaseMaterial3D.CULL_DISABLED
			m.albedo_color = Color(1.0, 0.86, 0.46) if key == "slash" else Color(1.0, 0.74, 0.3)
		"sun_beam", "sun_beam_white", "sun_beam_hot":    # the Sun Priest's beams (vertex colours fade their edges)
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.vertex_color_use_as_albedo = true
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.cull_mode = BaseMaterial3D.CULL_DISABLED
			m.albedo_color = {"sun_beam": Color(1.0, 0.84, 0.42), "sun_beam_white": Color(1.0, 0.98, 0.9),
				"sun_beam_hot": Color(1.0, 0.48, 0.14)}[key]
		"sun_flash", "sun_flash_white", "sun_glint":  # the disc flaring, the burst where a beam strikes, motes of light
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
			m.billboard_keep_scale = true
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.albedo_color = {"sun_flash": Color(1.0, 0.8, 0.36), "sun_flash_white": Color(1.0, 0.97, 0.86),
				"sun_glint": Color(1.0, 0.9, 0.55)}[key]
			m.albedo_texture = _mote_tex()
		"ember", "fire_flash":                       # a burning arrow's embers and the burst where it lands
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
			m.billboard_keep_scale = true
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			m.albedo_color = Color(1.0, 0.5, 0.12) if key == "ember" else Color(1.0, 0.56, 0.2)
			m.albedo_texture = _mote_tex()
	_atk_cache[key] = m
	return m


## A tar puddle, painted: a black pool with a few satellite drops, a brown rim and a glossy highlight. The burning
## kind (Path B) is darker red-black with glowing embers and a hot rim.
func _puddle_tex(hot: bool) -> Texture2D:
	var key := "tex_puddle_hot" if hot else "tex_puddle"
	if _atk_cache.has(key):
		return _atk_cache[key]
	var w := 64
	var img := Image.create(w, w, false, Image.FORMAT_RGBA8)
	var drops := [Vector3(0.62, 0.2, 0.09), Vector3(-0.55, 0.45, 0.07), Vector3(0.1, -0.7, 0.08), Vector3(-0.3, -0.62, 0.05)]
	var r := RandomNumberGenerator.new()
	r.seed = 5
	var embers := []
	for i in 22:
		embers.append(Vector3(r.randf_range(-0.48, 0.48), r.randf_range(-0.48, 0.48), r.randf_range(0.025, 0.06)))
	var body := Color(0.075, 0.03, 0.015) if hot else Color(0.04, 0.032, 0.027)
	var rimc := Color(1.0, 0.45, 0.1) if hot else Color(0.16, 0.115, 0.075)
	for y in w:
		for x in w:
			var px := (x + 0.5) / w * 2.0 - 1.0
			var py := (y + 0.5) / w * 2.0 - 1.0
			var rr := sqrt(px * px + py * py)
			var a := atan2(py, px)
			var edge := 0.6 + 0.08 * sin(a * 3.0 + 1.0) + 0.06 * sin(a * 5.0 + 2.3) + 0.03 * sin(a * 9.0)
			var cov := clampf((edge - rr) / 0.05, 0.0, 1.0)
			var inner := edge - rr                             # distance inside the main pool
			var col := body
			var rim := clampf(1.0 - absf(inner - 0.04) / 0.035, 0.0, 1.0) * (0.85 if hot else 0.7)
			col = col.lerp(rimc, rim * cov)
			for d in drops:
				var dr := Vector2(px - d.x, py - d.y).length()
				var dv := clampf((d.z - dr) / 0.025, 0.0, 1.0)
				if dv > cov:
					cov = dv
					col = body.lerp(rimc, 0.35)
			if hot:
				for e in embers:
					var ev := clampf((e.z - Vector2(px - e.x, py - e.y).length()) / 0.02, 0.0, 1.0)
					col = col.lerp(Color(1.0, 0.62, 0.18), ev * cov)
			else:
				# a glossy crescent of reflected sky near one side
				var hl := Vector2(px + 0.2, py + 0.22)
				var hv := clampf((0.17 - hl.length()) / 0.05, 0.0, 1.0) * clampf((Vector2(px + 0.14, py + 0.16).length() - 0.12) / 0.04, 0.0, 1.0)
				col = col.lerp(Color(0.55, 0.52, 0.5), hv * 0.75 * cov)
			img.set_pixel(x, y, Color(col.r, col.g, col.b, cov * 0.96))
	img.generate_mipmaps()
	var t := ImageTexture.create_from_image(img)
	_atk_cache[key] = t
	return t


## Ground cracks radiating from a point (a club smash); `crater` adds a dark dished centre (a boulder's landing).
func _crack_tex(crater: bool) -> Texture2D:
	var key := "tex_crater" if crater else "tex_crack"
	if _atk_cache.has(key):
		return _atk_cache[key]
	var w := 128
	var img := Image.create(w, w, false, Image.FORMAT_RGBA8)
	img.fill(Color(1, 1, 1, 0))
	var r := RandomNumberGenerator.new()
	r.seed = 7 if crater else 3
	var stamp := func(cx: float, cy: float, rad: float, a: float) -> void:
		for yy in range(int(cy - rad) - 1, int(cy + rad) + 2):
			for xx in range(int(cx - rad) - 1, int(cx + rad) + 2):
				if xx < 0 or yy < 0 or xx >= w or yy >= w:
					continue
				var dd := Vector2(xx + 0.5 - cx, yy + 0.5 - cy).length()
				var v := clampf((rad - dd) / 0.8, 0.0, 1.0) * a
				if v > img.get_pixel(xx, yy).a:
					img.set_pixel(xx, yy, Color(1, 1, 1, v))
	var arms := 8 if crater else 7
	for i in arms:
		var ang := TAU * i / arms + r.randf_range(-0.3, 0.3)
		var p := Vector2(w * 0.5, w * 0.5)
		var length := r.randf_range(0.32, 0.46) * w
		var steps := int(length / 1.5)
		for st in steps:
			ang += r.randf_range(-0.35, 0.35)
			p += Vector2(cos(ang), sin(ang)) * 1.5
			var f := float(st) / steps
			stamp.call(p.x, p.y, lerpf(2.4, 0.6, f), 1.0 - 0.4 * f)
			if r.randf() < 0.06:              # a short branch
				var bp := p
				var ba := ang + r.randf_range(-1.2, 1.2)
				for bs in 8:
					bp += Vector2(cos(ba), sin(ba)) * 1.5
					stamp.call(bp.x, bp.y, 0.8, 0.7)
	if crater:
		for yy in w:
			for xx in w:
				var dd := Vector2(xx + 0.5 - w * 0.5, yy + 0.5 - w * 0.5).length() / (w * 0.5)
				var v := clampf((0.3 - dd) / 0.12, 0.0, 1.0) * 0.85
				if v > img.get_pixel(xx, yy).a:
					img.set_pixel(xx, yy, Color(1, 1, 1, v))
	img.generate_mipmaps()
	var t := ImageTexture.create_from_image(img)
	_atk_cache[key] = t
	return t


## Builds the attack effects' textures, meshes and materials while the map loads, and draws each material once out of
## sight (under the ground, for two frames, including the tar coat on a robot) so their shaders are compiled before the
## first shot instead of hitching it.
func _prewarm_attack_fx() -> void:
	var holder := Node3D.new()
	holder.position = Vector3(GROUND_RECT.position.x + GROUND_RECT.size.x * 0.5, -0.6, GROUND_RECT.position.y + GROUND_RECT.size.y * 0.5)
	add_child(holder)
	if not _atk_cache.has("plane"):
		var pm := PlaneMesh.new()
		pm.size = Vector2(1, 1)
		_atk_cache["plane"] = pm
	var q: Mesh = _atk_cache["plane"]
	for key in ["tar", "tar_hot", "puddle", "puddle_hot", "crack", "crater", "spike_stone", "spike_quartz", "chunk", "clod"]:
		var mi := _mi(q, _atk_mat(key), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for v in 3:
		_spike_mesh(v)
	if not defs.enemies.has("walker"):
		return
	var bot := _make_robot("walker")
	holder.add_child(bot)
	var coats: Array = _tar_mats(false) + _tar_mats(true)
	var mis: Array = bot.get_meta("body_mis", [])
	for i in mis.size():
		(mis[i] as MeshInstance3D).material_overlay = coats[i % coats.size()]
	_fx_after(0.12, func() -> void:
		if is_instance_valid(holder):
			holder.queue_free())


## The arrows (v0.9.21), the Spear Guard's lance (v0.9.22), the Torsion Catapult's balls, pots and shards (v0.9.23): any
## map can have their units (archers include the Cretan Archer and heroes that shoot arrows), so their meshes and
## materials are drawn once under the ground at load, like the Stone Age attacks'.
func _prewarm_arrows() -> void:
	var holder := Node3D.new()
	holder.position = Vector3(GROUND_RECT.position.x + GROUND_RECT.size.x * 0.5, -0.6, GROUND_RECT.position.y + GROUND_RECT.size.y * 0.5)
	add_child(holder)
	for fire in [false, true]:
		_mi(_arrow_mesh(fire), null, holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
	for key in ["arrow_spark", "ember", "fire_flash", "lance_flash", "sun_flash", "sun_flash_white", "sun_glint"]:
		var mi := _mi(_fx_mesh("mote"), _atk_mat(key), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_mi(_lance_mesh(), _atk_mat("lance"), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
	for key in ["sun_beam", "sun_beam_white", "sun_beam_hot"]:
		_mi(_beam_mesh(), _atk_mat(key), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
	_mi(_slash_mesh(), _atk_mat("slash"), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
	_mi(_wave_mesh(), _atk_mat("flare_wave"), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
	for key in ["fury_wave", "fury_ring"]:
		_mi(_wave_mesh(), _atk_mat(key), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
	_mi(_fx_mesh("spark"), _atk_mat("hammer_spark"), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
	var hm := Node3D.new()
	hm.scale = Vector3.ONE * 0.05
	holder.add_child(hm)
	_hammer_model(hm)
	_mi(_pot_mesh(), _atk_mat("pot"), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
	_mi(_sph_c(0.17, 14), _atk_mat("stone_ball"), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
	_mi(_fx_mesh("cube"), _atk_mat("shard"), holder, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.05)
	_fx_after(0.12, func() -> void:
		if is_instance_valid(holder):
			holder.queue_free())


## A flat decal lying on the ground (puddle, cracks, crater) that pops in and fades.
func _ground_decal(pos: Vector3, key: String, size: float, life: float, delay := 0.0) -> void:
	if not _fx_room(1):
		return
	if not _atk_cache.has("plane"):
		var pm := PlaneMesh.new()
		pm.size = Vector2(1, 1)
		_atk_cache["plane"] = pm
	var d := _mi(_atk_cache["plane"], _atk_mat(key), self, Vector3(pos.x, 0.025 + randf() * 0.01, pos.z), Vector3(0, randf() * TAU, 0))
	d.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	d.visible = false
	effects.append({"node": d, "t": -delay, "life": life, "kind": "decal", "size": Vector3(size, 1.0, size)})


## Jagged stone spikes (flat-shaded, a few shapes), base radius 1 and height 1; scaled per use.
func _spike_mesh(v: int) -> Mesh:
	var key := "spike_%d" % v
	if _atk_cache.has(key):
		return _atk_cache[key]
	var r := RandomNumberGenerator.new()
	r.seed = 11 + v * 7
	var n := 5
	var base := []
	var mid := []
	for i in n:
		var a := TAU * i / n + r.randf_range(-0.2, 0.2)
		var rr := r.randf_range(0.8, 1.1)
		base.append(Vector3(cos(a) * rr, -0.1, sin(a) * rr))
		var a2 := a + PI / n
		var rm := r.randf_range(0.45, 0.6)
		mid.append(Vector3(cos(a2) * rm, r.randf_range(0.4, 0.5), sin(a2) * rm))
	var tip := Vector3(r.randf_range(-0.12, 0.12), 1.0, r.randf_range(-0.12, 0.12))
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_smooth_group(-1)                          # flat faces: chipped stone
	for i in n:
		var j := (i + 1) % n
		for tri in [[base[i], base[j], mid[i]], [base[j], mid[j], mid[i]], [mid[i], mid[j], tip]]:
			for vtx in tri:
				var sh := lerpf(0.55, 1.0, clampf((vtx as Vector3).y, 0.0, 1.0))     # darker at the root
				st.set_color(Color(sh, sh, sh))
				st.add_vertex(vtx)
	st.generate_normals()
	var m := st.commit()
	_atk_cache[key] = m
	return m


## One spike bursting out of the ground at `pos` after `delay`: up fast, holds, sinks back. `lean` is a flat vector:
## its direction is where the tip leans, its length the angle (radians). A `burst` spike throws dust and pebbles and
## lands the hit on robot `tid` (flash, knock-up, its death if the pulse killed it).
func _spike(pos: Vector3, delay: float, w: float, h: float, quartz: bool, hold: float, lean := Vector3.ZERO, burst := false,
		tid := -1) -> void:
	if not _fx_room(1):
		if tid >= 0:
			_fx_after(delay, func() -> void: _land_hit(tid, 0.3))
		return
	var sp := _mi(_spike_mesh(randi() % 3), _atk_mat("spike_quartz" if quartz else "spike_stone"), self, Vector3(pos.x, 0.0, pos.z))
	var b := Basis(Vector3.UP, randf() * TAU)
	lean.y = 0.0
	if lean.length() > 0.001:
		b = Basis(Vector3.UP.cross(lean.normalized()).normalized(), lean.length()) * b
	sp.basis = b
	sp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if Progress.gfx_level() >= 1 else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	sp.visible = false
	sp.scale = Vector3(w, 0.01, w)
	effects.append({"node": sp, "t": -delay, "life": 0.07 + hold + 0.2, "kind": "spike", "w": w, "h": h, "hold": hold, "burst": burst,
		"tid": tid})


func _tick_spike(fx: Dictionary, n: Node3D) -> void:
	n.visible = fx.t >= 0.0
	if fx.t < 0.0:
		return
	if fx.burst and not fx.get("fired", false):
		fx.fired = true
		var at: Vector3 = n.position
		var tid := int(fx.get("tid", -1))
		_fx_queue.append(func() -> void:
			_dust_fx(at + Vector3(0, 0.2, 0), 3, 0.7)
			_pebble_fx(at + Vector3(0, 0.35, 0), 2)
			if tid >= 0:
				_land_hit(tid, 0.3))
	var hold: float = fx.hold
	var y: float
	if fx.t < 0.07:
		var a: float = fx.t / 0.07
		y = a * (2.0 - a)
	elif fx.t < 0.07 + hold:
		y = 1.0
	else:
		var b: float = clampf((fx.t - 0.07 - hold) / 0.2, 0.0, 1.0)
		y = 1.0 - b * b
	n.scale = Vector3(fx.w, maxf(float(fx.h) * y, 0.01), fx.w)


## Tar Pit Shaman: he thrusts his spirit stone and it spits tar; a glob arcs onto every robot the pulse hit (capped).
## The robots' hits are held now; the tar leaves the stone as his clip reaches the thrust.
func _tar_volley(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	var lead := _at_attack_frame(uid, ATTACK_FRAME.tar_shaman, 0.0, func() -> void: _tar_spit(uid, targets))
	var i := 0
	for tid in targets:
		var to := _robot_point(int(tid), 0.55)
		if to == Vector3.INF:
			continue
		var dist := _v3(u.pos, 0.0).distance_to(Vector3(to.x, 0.0, to.z))
		_hold_hit(int(tid), lead + 0.04 * i + 0.26 + dist * 0.045)
		i += 1


func _tar_spit(uid: int, targets: Array) -> void:
	var u = sim.get_unit(uid)
	if u == null:                                     # (sold mid-thrust)
		for tid in targets:
			_land_hit(int(tid))
		return
	var hot := str(u.get("branch", "")) == "B"
	var cap: int = [8, 5, 3][clampi(Progress.gfx_level(), 0, 2)]
	var face: Vector2 = u.facing
	if tower_nodes.has(uid) and (tower_nodes[uid] as Node3D).has_meta("face_to"):
		face = (tower_nodes[uid] as Node3D).get_meta("face_to")      # (he turned to face it as he wound up)
	var from := _orb_point(u, face)
	var i := 0
	var rest := []
	var last := 0.0
	for tid in targets:
		if i >= cap or not _fx_room(2):               # (past the cap: hit as the last glob lands, no glob of its own)
			rest.append(int(tid))
			continue
		var to := _robot_point(int(tid), 0.55)
		if to == Vector3.INF:
			continue
		var g := Node3D.new()
		add_child(g)
		g.position = from
		g.visible = false
		var gs := randf_range(0.75, 1.0) if i > 0 else 1.05
		g.scale = Vector3.ONE * gs
		var tm := _atk_mat("tar_hot" if hot else "tar")
		var core := _mi(_sph_c(0.1, 12), tm, g)
		core.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		g.set_meta("core", core)
		# a string of shrinking beads trailing behind it (local +Z points back along the flight): sticky tar
		for k in 3:
			var dm := _mi(_sph_c(0.1, 8), tm, g, Vector3(0, 0.0, 0.11 + 0.085 * k + 0.01 * k * k), Vector3.ZERO,
				Vector3.ONE * (0.52 - 0.14 * k))
			dm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if hot:
			_fire_halo(g, 0.6)
		var dist := _v3(u.pos, 0.0).distance_to(Vector3(to.x, 0.0, to.z))
		var dur := 0.26 + dist * 0.045
		effects.append({"node": g, "t": -0.04 * i, "life": dur, "kind": "glob", "src": uid, "tid": int(tid),
			"from": from, "to": to, "dur": dur, "arc": (0.4 + dist * 0.12) * randf_range(0.8, 1.2), "hot": hot})
		last = maxf(last, 0.04 * i + dur)
		i += 1
	if i > 0:
		_orb_spit(uid, from, hot)
	if not rest.is_empty():
		_fx_after(last, func() -> void:
			for rt in rest:
				_land_hit(int(rt)))


func _tick_glob(fx: Dictionary, n: Node3D) -> void:
	n.visible = fx.t >= 0.0
	if fx.t < 0.0:
		return
	var live := _robot_point(int(fx.tid), 0.55)
	if live != Vector3.INF:
		fx.to = live
	var k: float = clampf(fx.t / float(fx.dur), 0.0, 1.0)
	var p: Vector3 = (fx.from as Vector3).lerp(fx.to, k) + Vector3(0, float(fx.arc) * 4.0 * k * (1.0 - k), 0)
	var vel := p - n.position
	n.position = p
	if vel.length_squared() > 0.000001 and absf(vel.normalized().y) < 0.97:
		n.look_at(p + vel, Vector3.UP)              # -Z leads, so the beads (local +Z) trail behind
	var dt := maxf(get_process_delta_time(), 0.001)
	var st := 1.0 + clampf(vel.length() / dt * 0.07, 0.0, 0.6)        # stretched by its speed, like a blob of goo
	var wob := 0.09 * sin(float(fx.t) * 38.0)
	if n.has_meta("core"):
		(n.get_meta("core") as Node3D).scale = Vector3((1.0 + wob) / sqrt(st), (1.0 - wob) / sqrt(st), st)
	if fx.t + get_process_delta_time() >= float(fx.life) and not fx.get("landed", false):
		fx.landed = true
		var at: Vector3 = fx.to
		var hot: bool = fx.hot
		var tid := int(fx.tid)
		_fx_queue.append(func() -> void:
			_tar_splat(Vector3(at.x, 0.0, at.z), at.y, hot)
			_tar_mark(tid, hot)
			_land_hit(tid))


func _splits_on_death(type: String) -> bool:
	var d: Dictionary = defs.enemies.get(type, {})
	return d.has("on_death") or bool((d.get("emp", {}) as Dictionary).get("on_death", false))


## A robot is destroyed: its parts fly, the bounty pops up.
func _robot_killed(ev: Dictionary) -> void:
	if not enemy_nodes.has(ev.id):
		return
	var n2: Node3D = enemy_nodes[ev.id]
	var big: bool = defs.enemies[ev.type].get("boss", false)
	if _style2():
		_robot_death_fx(n2.position + Vector3(0, 0.7 if not big else 2.0, 0), big)
	else:
		_debris_fx(n2.position + Vector3(0, 0.7 if not big else 2.0, 0), 14 if big else 5, big)
	_float_text(n2.position + Vector3(0, 1.5, 0), "+%d" % ev.bounty, C_COIN, 46 if not big else 90)
	n2.queue_free()
	enemy_nodes.erase(ev.id)
	if big:
		shake = 1.3
		_sfx("boss_death", 0.0, 0.0)
	else:
		_sfx("robot_death", -4.0, 0.15, 0.03)
		_sfx("coin", -14.0, 0.05, 0.06)


## A doomed robot's hit arrived (or never will): now it blows up.
func _resolve_doom(tid: int) -> void:
	if _doomed.has(tid):
		var ev: Dictionary = _doomed[tid]
		_doomed.erase(tid)
		_robot_killed(ev)


## The pulse already hurt robot `tid`; keep its hit flash for when the tar (or spike, or shock) reaches it.
## `eta`: real seconds until it lands. A robot the hit destroyed (doomed) blows up then, or a moment later at most.
func _hold_hit(tid: int, eta: float) -> void:
	if enemy_nodes.has(tid) and is_instance_valid(enemy_nodes[tid]):
		var n: Node3D = enemy_nodes[tid]
		n.set_meta("flash", 0.0)
		if float(n.get_meta("punch", 0.0)) > 0.0:
			n.set_meta("punch", 0.0)
			var e = sim._enemy_by_id(tid)
			if e != null:
				(n.get_node("Model") as Node3D).scale = Vector3.ONE * float(defs.enemies[e.type].get("model_scale", 0.9))
	if _doomed.has(tid):
		_fx_after(eta + 0.4, func() -> void: _resolve_doom(tid))


func _land_hit(tid: int, hop := 0.0) -> void:
	if enemy_nodes.has(tid) and is_instance_valid(enemy_nodes[tid]):
		(enemy_nodes[tid] as Node3D).set_meta("flash", 1.0)
		(enemy_nodes[tid] as Node3D).set_meta("punch", 1.0)
		if hop > 0.0:
			(enemy_nodes[tid] as Node3D).set_meta("hop", time_s)       # thrown up a little (spikes, a club's ripple)
			(enemy_nodes[tid] as Node3D).set_meta("hop_h", hop)
			(enemy_nodes[tid] as Node3D).set_meta("hop_y0", (enemy_nodes[tid] as Node3D).position.y)
	if hop > 0.0 and _doomed.has(tid):
		_fx_after(0.16, func() -> void: _resolve_doom(tid))            # blows up at the top of the throw
	else:
		_resolve_doom(tid)


## Where the shaman's spirit stone is when he thrusts at `face` (in front of him, at his right side).
func _orb_point(u: Dictionary, face: Vector2) -> Vector3:
	var fwd := Vector3(face.x, 0.0, face.y).normalized() if face.length() > 0.01 else Vector3(0, 0, 1)
	var right := Vector3(-fwd.z, 0.0, fwd.x)
	return _v3(u.pos, 0.0) + fwd * 0.57 + right * 0.34 + Vector3(0, 1.25, 0)


## The spirit stone spits: a few drops of tar spray off it as the volley leaves (not if he was sold meanwhile).
func _orb_spit(uid: int, at: Vector3, hot: bool) -> void:
	if sim.get_unit(uid) == null:
		return
	var drops: int = [4, 2, 0][clampi(Progress.gfx_level(), 0, 2)]
	if drops == 0 or not _fx_room(drops):
		return
	for i in drops:
		var sz := randf_range(0.035, 0.06)
		var dp := _mi(_sph_c(0.5, 6), _atk_mat("tar_hot" if hot else "tar"), self, at, Vector3.ZERO, Vector3.ONE * sz)
		dp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var a := randf() * TAU
		effects.append({"node": dp, "t": 0.0, "life": randf_range(0.3, 0.45), "kind": "debris", "s": sz,
			"v": Vector3(cos(a) * randf_range(0.6, 1.4), randf_range(0.8, 2.0), sin(a) * randf_range(0.6, 1.4))})


## A robot a glob hit wears the tar (glossy black splotches and drips oozing down it) until its slow wears off.
func _tar_mark(tid: int, hot: bool) -> void:
	var e = sim._enemy_by_id(tid)
	if e == null or not enemy_nodes.has(tid) or not is_instance_valid(enemy_nodes[tid]):
		return
	var n: Node3D = enemy_nodes[tid]
	n.set_meta("tar_until", maxi(int(e.slow_until), sim.tick + int(0.6 / TICK)))
	n.set_meta("tar_hot", hot)


const TAR_COAT_SHADER := """
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_back, specular_schlick_ggx;
uniform float thr = 0.5;
uniform vec3 tint : source_color = vec3(0.06, 0.042, 0.03);
uniform vec3 glow : source_color = vec3(0.0);
uniform float scale = 5.0;
varying vec3 op;
void vertex() {
	op = VERTEX;
}
float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}
float noise(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}
void fragment() {
	vec3 p = op * scale;
	float up = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).y;              // tar lands from above and runs down
	float blobs = noise(p) * 0.6 + noise(p * 2.3 + 7.1) * 0.4;
	float c = blobs * 0.55 + 0.3 * smoothstep(-0.1, 0.8, up);
	float drips = noise(vec3(p.x * 2.6, p.y * 0.32 + TIME * 0.22, p.z * 2.6));   // tall streaks oozing down the sides
	c = max(c, drips * 0.92 - 0.06 + 0.1 * smoothstep(0.0, 0.6, up));
	float a = smoothstep(thr, thr + 0.035, c);
	ALBEDO = tint;
	ROUGHNESS = 0.28;
	SPECULAR = 0.6;
	EMISSION = glow * (1.0 - smoothstep(thr + 0.02, thr + 0.12, c));
	ALPHA = a * 0.97;
}
"""


## Shared tar-coat overlays: full, wearing off, almost gone (and the burning set for Path B).
func _tar_mats(hot: bool) -> Array:
	var key := "coat_hot" if hot else "coat"
	if _atk_cache.has(key):
		return _atk_cache[key]
	if not _atk_cache.has("coat_shader"):
		var sh := Shader.new()
		sh.code = TAR_COAT_SHADER
		_atk_cache["coat_shader"] = sh
	var arr := []
	for thr in [0.5, 0.58, 0.66]:
		var m := ShaderMaterial.new()
		m.shader = _atk_cache["coat_shader"]
		m.set_shader_parameter("thr", thr)
		if hot:
			m.set_shader_parameter("tint", Color(0.16, 0.05, 0.02))
			m.set_shader_parameter("glow", Color(1.0, 0.35, 0.06))
		arr.append(m)
	_atk_cache[key] = arr
	return arr


## Called every frame for each robot: picks its tar overlay (none once the slow is over). The hit flash wins while it lasts.
func _tar_coat(n: Node3D, gl: int) -> void:
	var want: Material = null
	if n.has_meta("tar_until"):
		var left := float(int(n.get_meta("tar_until")) - sim.tick) * TICK
		if left <= 0.0:
			n.remove_meta("tar_until")
		elif gl < 2:
			want = _tar_mats(bool(n.get_meta("tar_hot", false)))[0 if left > 0.5 else (1 if left > 0.25 else 2)]
	var had: Material = n.get_meta("tar_mat") if n.has_meta("tar_mat") else null
	if had == want:
		return
	if want == null:
		n.remove_meta("tar_mat")
	else:
		n.set_meta("tar_mat", want)
	if not n.has_meta("flash_on"):
		for mi in n.get_meta("body_mis", []):
			(mi as MeshInstance3D).material_overlay = want


## A glob hits: black drops fly, a dark splash, and a puddle of tar spreads on the ground and fades.
func _tar_splat(ground: Vector3, h: float, hot: bool) -> void:
	_ground_decal(ground, "puddle_hot" if hot else "puddle", randf_range(0.8, 1.05), 1.7)
	var drops: int = [6, 4, 2][clampi(Progress.gfx_level(), 0, 2)]
	if _fx_room(drops):
		for i in drops:
			var sz := randf_range(0.05, 0.09)
			var dp := _mi(_sph_c(0.5, 6), _atk_mat("tar_hot" if hot else "tar"), self, ground + Vector3(0, minf(h, 0.6), 0), Vector3.ZERO,
				Vector3.ONE * sz)
			dp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var a := randf() * TAU
			effects.append({"node": dp, "t": 0.0, "life": randf_range(0.35, 0.55), "kind": "debris", "s": sz,
				"v": Vector3(cos(a) * randf_range(1.2, 2.4), randf_range(1.5, 3.0), sin(a) * randf_range(1.2, 2.4))})
	_dust_fx(ground + Vector3(0, 0.3, 0), 2, 0.5, Color(0.12, 0.1, 0.08, 0.55))
	if hot and _fx_room(1):
		var fl := _mi(_flame_quad(0.4, 0.58), _campfire_mat("outer"), self, ground + Vector3(0, 0.02, 0))
		fl.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		fl.visible = false
		effects.append({"node": fl, "t": 0.0, "life": 0.6, "kind": "pop", "s": 1.0})


## Mara: she lifts her palm and the earth answers. A fissure of spikes races out from her to the first few robots hit,
## then three stone and quartz spikes burst up round every robot hit, leaning in over it, and throw it up a little.
## The robots' hits are held now; the earth answers as her clip reaches the cast.
func _earth_spikes(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	var lead := _at_attack_frame(uid, ATTACK_FRAME.mara, 0.0, func() -> void: _earth_answers(uid, targets))
	var fissures: int = [3, 2, 1][clampi(Progress.gfx_level(), 0, 2)]
	var origin := _v3(u.pos, 0.0)
	var i := 0
	for tid in targets:
		var tp := _robot_point(int(tid), 0.0)
		if tp == Vector3.INF:
			continue
		tp.y = 0.0
		_hold_hit(int(tid), lead + (0.16 if i < fissures and tp.distance_to(origin) > 1.3 else 0.0) + 0.03)
		i += 1


func _earth_answers(uid: int, targets: Array) -> void:
	var u = sim.get_unit(uid)
	if u == null:
		for tid in targets:
			_land_hit(int(tid))
		return
	var gl := clampi(Progress.gfx_level(), 0, 2)
	var cap: int = [6, 4, 2][gl]
	var fissures: int = [3, 2, 1][gl]
	var origin := _v3(u.pos, 0.0)
	var i := 0
	var rest := []
	var last := 0.0
	for tid in targets:
		if i >= cap:                                  # (past the cap: hit as the last spikes burst, none of its own)
			rest.append(int(tid))
			continue
		var tp := _robot_point(int(tid), 0.0)
		if tp == Vector3.INF:
			continue
		tp.y = 0.0
		var dv := tp - origin
		var dist := dv.length()
		var dn := dv / maxf(dist, 0.01)
		var side := Vector3(-dn.z, 0, dn.x)
		var travel := 0.0
		if i < fissures and dist > 1.3:
			# from the edge of her dais to just short of the robot
			var run := dist - 1.05
			var steps := clampi(int(run / 0.45), 1, 4)
			for st in steps:
				var f := (st + 0.5) / steps
				var at0 := origin + dn * (0.75 + run * f) + side * randf_range(-0.09, 0.09)
				_spike(at0, f * 0.16, randf_range(0.1, 0.13), randf_range(0.4, 0.52), st % 2 == 1, 0.12,
					Vector3(randf_range(-0.2, 0.2), 0, randf_range(-0.2, 0.2)))
			travel = 0.16
		_spike_cluster(tp, travel + 0.03, int(tid))
		last = maxf(last, travel + 0.03)
		i += 1
	if not rest.is_empty():
		_fx_after(last, func() -> void:
			for rt in rest:
				_land_hit(int(rt)))


## Three spikes burst up round a point, tips leaning in over it, on a patch of cracked ground. The first one lands the
## hit on robot `tid` (if any).
func _spike_cluster(c: Vector3, delay: float, tid := -1, k := 1.0) -> void:
	var a0 := randf() * TAU
	var q := randi() % 3
	for j in 3:
		var a := a0 + TAU * j / 3.0 + randf_range(-0.3, 0.3)
		var off := Vector3(cos(a), 0, sin(a)) * randf_range(0.45, 0.52) * k
		_spike(c + off, delay + j * 0.025, randf_range(0.19, 0.23) * k, randf_range(0.95, 1.2) * k, j == q, 0.26,
			-off.normalized() * randf_range(0.18, 0.28), j == 0, tid if j == 0 else -1)
	_ground_decal(c, "crack", 1.3 * k, 1.1, delay)


## Club Warrior: the club smashes the ground in front of him (cracks, dust, flying clods) and a ripple of bursting
## earth races out to every robot it hit; each one is bounced up off the ground when it arrives. The robots' hits are
## held now; the club lands as his clip reaches the smash.
func _club_smash(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	var lead := _at_attack_frame(uid, ATTACK_FRAME.club_warrior, 0.12, func() -> void: _club_lands(uid, targets))
	var hit := _v3(u.pos, 0.0) + Vector3(u.facing.x, 0.0, u.facing.y) * 0.72
	for tid in targets:
		var tp := _robot_point(int(tid), 0.0)
		if tp != Vector3.INF:
			tp.y = 0.0
			_hold_hit(int(tid), lead + 0.03 * (clampi(int(tp.distance_to(hit) / 0.32), 0, 5) + 1))


func _club_lands(uid: int, targets: Array) -> void:
	var u = sim.get_unit(uid)
	if u == null:                                     # (sold mid-swing)
		for tid in targets:
			_land_hit(int(tid))
		return
	var origin := _v3(u.pos, 0.0)
	var fwd := Vector3(u.facing.x, 0.0, u.facing.y)
	var hit := origin + fwd * 0.72
	_ground_decal(hit, "crack", 1.25, 1.2)
	_dust_fx(hit + Vector3(0, 0.15, 0), 5, 0.9)
	_pebble_fx(hit + Vector3(0, 0.3, 0), 3)
	_clods(hit, 4, 1.0)
	shake = maxf(shake, 0.12)
	var cap: int = [5, 4, 2][clampi(Progress.gfx_level(), 0, 2)]
	var i := 0
	var rest := []
	var last := 0.0
	for tid in targets:
		if i >= cap:                                  # (past the cap: hit as the last ripple arrives, none of its own)
			rest.append(int(tid))
			continue
		var tp := _robot_point(int(tid), 0.0)
		if tp == Vector3.INF:
			continue
		tp.y = 0.0
		var dv := tp - hit
		var steps := clampi(int(dv.length() / 0.32), 0, 5)
		for st in steps:
			var f := (st + 1.0) / (steps + 1.0)
			var at := hit + dv * f
			_fx_after(0.03 * (st + 1), func() -> void:
				_clods(at, 2 if i == 0 else 1, 0.75)
				_dust_fx(at + Vector3(0, 0.12, 0), 1, 0.4))
		var htid := int(tid)
		_fx_after(0.03 * (steps + 1), func() -> void:
			_dust_fx(tp + Vector3(0, 0.2, 0), 3, 0.7)
			_pebble_fx(tp + Vector3(0, 0.3, 0), 2)
			_clods(tp, 2, 1.0)
			_land_hit(htid, 0.18))
		_ground_decal(tp, "crack", 0.75, 0.9, 0.03 * (steps + 1))
		last = maxf(last, 0.03 * (steps + 1))
		i += 1
	if not rest.is_empty():
		_fx_after(last, func() -> void:
			for rt in rest:
				_land_hit(int(rt)))


## Clods of earth thrown up from the ground at `at` (a club's ripple, a smash).
func _clods(at: Vector3, n: int, force: float) -> void:
	if not _fx_room(n):
		return
	for i in n:
		var sz := randf_range(0.07, 0.12) * (0.8 + 0.3 * force)
		var c := _mi(_sph_c(0.5, 5), _atk_mat("clod"), self, Vector3(at.x, 0.08, at.z) + Vector3(randf_range(-0.08, 0.08), 0, randf_range(-0.08, 0.08)),
			Vector3(randf(), randf(), randf()) * 3.0, Vector3.ONE * sz)
		c.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var a := randf() * TAU
		effects.append({"node": c, "t": 0.0, "life": randf_range(0.35, 0.5), "kind": "debris", "s": sz,
			"v": Vector3(cos(a) * randf_range(0.4, 1.0), randf_range(2.2, 3.4) * force, sin(a) * randf_range(0.4, 1.0))})


## Runs `fn` after `sec` real seconds (game time paused while the match is paused). No node, and not counted against the
## effects cap, so many timers never crowd out the visible effects.
var _timers: Array = []                      # [[seconds left, Callable], ...]
func _fx_after(sec: float, fn: Callable) -> void:
	_timers.append([sec, fn])


## A boulder lands: a crater with cracks, a burst of dust and rock chunks flying out.
func _boulder_impact(ground: Vector3, r: float, rock := true) -> void:
	var gl := clampi(Progress.gfx_level(), 0, 2)
	_ground_decal(ground, "crater", 1.25 * r + 0.3, 1.8)
	_dust_fx(ground + Vector3(0, 0.25, 0), [7, 4, 2][gl], 0.9 * r)      # (alpha-blended puffs cost a lot on PowerVR)
	var chunks: int = [6, 4, 2][gl] if rock else 0                   # (a pitch pot's clay shards stand in for the rock)
	if chunks > 0 and _fx_room(chunks):
		for i in chunks:
			var sz := randf_range(0.08, 0.15) * (0.7 + 0.3 * r)
			var c := _mi(_sph_c(0.5, 5), _atk_mat("chunk"), self, ground + Vector3(0, 0.25, 0), Vector3(randf(), randf(), randf()) * 3.0,
				Vector3.ONE * sz)
			c.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var a := randf() * TAU
			effects.append({"node": c, "t": 0.0, "life": randf_range(0.5, 0.8), "kind": "debris", "s": sz,
				"v": Vector3(cos(a) * randf_range(1.8, 3.2), randf_range(3.0, 5.0), sin(a) * randf_range(1.8, 3.2))})


## A burning boulder (Fire Pot) bursts: flames leap up round the crater for a moment and embers fly.
func _fire_splash(ground: Vector3, r: float) -> void:
	var n: int = [4, 3, 1][clampi(Progress.gfx_level(), 0, 2)]
	if not _fx_room(n + 4):
		return
	for i in n:
		var a := TAU * i / n + randf() * 0.8
		var at := ground + Vector3(cos(a), 0, sin(a)) * (0.25 + randf() * 0.35) * r + Vector3(0, 0.02, 0)
		var fl := _mi(_flame_quad(0.45, 0.7), _campfire_mat("outer"), self, at)
		fl.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		fl.visible = false
		effects.append({"node": fl, "t": -0.03 * i, "life": randf_range(0.5, 0.8), "kind": "pop", "s": randf_range(0.8, 1.2) * r})
	for i in 4:
		var sz := randf_range(0.04, 0.07)
		var e := _mi(_sph_c(0.5, 6), _atk_mat("tar_hot"), self, ground + Vector3(0, 0.3, 0), Vector3.ZERO, Vector3.ONE * sz)
		e.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var a2 := randf() * TAU
		effects.append({"node": e, "t": 0.0, "life": randf_range(0.4, 0.6), "kind": "debris", "s": sz,
			"v": Vector3(cos(a2) * randf_range(1.0, 2.2), randf_range(2.5, 4.0), sin(a2) * randf_range(1.0, 2.2))})


## v2 robot death: white armor plates fly and red sparks burst. Nothing is left on the ground.
func _robot_death_fx(pos: Vector3, big: bool) -> void:
	_debris_fx(pos, 14 if big else 5, big)
	if not _fx_room(6):
		return
	for i in (6 if big else 3):
		var sz := randf_range(0.14, 0.24) * (2.2 if big else 1.0)
		var c := _mi(_fx_mesh("cube"), _mat("plate_chunk", Color(0.86, 0.88, 0.92), {"rough": 0.4}), self, pos,
			Vector3(randf(), randf(), randf()) * 3.0, Vector3(sz, sz * 0.25, sz))
		var a := randf() * TAU
		effects.append({"node": c, "t": 0.0, "life": randf_range(0.7, 1.0), "kind": "debris", "s": sz, "flat": true,
			"v": Vector3(cos(a) * 3.0, randf_range(4, 7), sin(a) * 3.0) * (1.4 if big else 1.0)})
	# (v0.9.10: the gray smoke puff and the ground scorch disc were removed — they read as leftover gray circles)


## v2 ambience: smoke rising off the cave fire, pollen drifting over the meadow.
func _ambient_fx(fire_pos: Vector3) -> void:
	var holder := Node3D.new()
	add_child(holder)
	effects.append({"node": holder, "t": 0.0, "life": INF, "kind": "ambient", "fire": fire_pos, "smoke_t": 0.0})
	if Progress.gfx_level() >= 2:
		return
	var b: Array = map.bounds
	var th := str(map.get("theme", "meadow"))
	# meadow: drifting pollen; snow: falling snowflakes; volcano: rising embers
	var kinds := {
		"pollen": {"n": 16, "col": Color(1.0, 0.97, 0.75, 0.75), "vy": 0.0, "s": 1.0},
		"snow": {"n": 60, "col": Color(1, 1, 1, 0.9), "vy": -0.9, "s": 0.8},
		"embers": {"n": 34, "col": Color(1.0, 0.55, 0.15, 0.95), "vy": 0.7, "s": 0.7},
		"fireflies": {"n": 26, "col": Color(0.85, 1.0, 0.4, 0.95), "vy": 0.0, "s": 0.75},
		"dust": {"n": 30, "col": Color(0.95, 0.85, 0.65, 0.55), "vy": 0.0, "s": 1.3},
		"soot": {"n": 40, "col": Color(0.3, 0.3, 0.32, 0.7), "vy": -0.35, "s": 0.9},
		"frost": {"n": 40, "col": Color(0.75, 0.95, 1.0, 0.85), "vy": -0.25, "s": 0.7},
		"data": {"n": 34, "col": Color(0.3, 0.95, 1.0, 0.9), "vy": 0.45, "s": 0.6},
		"datam": {"n": 34, "col": Color(1.0, 0.3, 0.9, 0.9), "vy": 0.45, "s": 0.6},
	}
	var kind_of := {"meadow": "pollen", "snow": "snow", "volcano": "embers", "forge": "embers", "bog": "fireflies", "jungle": "fireflies",
		"darkwood": "fireflies", "desert": "dust", "canyon": "dust", "olive": "dust", "smog": "soot", "factory": "soot", "railyard": "soot",
		"cooling": "frost", "lab": "data", "server": "data", "satellite": "data", "neon": "datam", "core": "datam"}
	var spec: Dictionary = kinds[kind_of.get(th, "pollen")]
	holder.set_meta("vy", float(spec.vy))
	holder.set_meta("box", [b[0] - 3.0, b[1] - 3.0, b[2] + 3.0, b[3] + 3.0])
	# soft round motes (a radial-gradient texture), not flat squares
	var mm := StandardMaterial3D.new()
	mm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mm.billboard_keep_scale = true
	mm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mm.albedo_color = spec.col
	mm.albedo_texture = _mote_tex()
	for i in int(spec.n):
		var m := _mi(_fx_mesh("mote"), mm, holder,
			Vector3(randf_range(b[0] - 3.0, b[2] + 3.0), randf_range(0.2, 6.0) if spec.vy != 0.0 else randf_range(0.4, 1.6), randf_range(b[1] - 3.0, b[3] + 3.0)),
			Vector3.ZERO, Vector3.ONE * float(spec.s) * randf_range(0.7, 1.3))
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		m.set_meta("seed", randf() * 100.0)


func _boulder_drop_fx(target: Vector3, delay: float, tid := -1) -> void:
	var b := _mi(_sph_c(0.35, 16), _mat("proj_boulder", Color(0.56, 0.54, 0.5), {"rough": 0.95}), self, target + Vector3(0, 9, 0))
	b.scale = Vector3(1.08, 0.86, 0.97)
	b.visible = false
	effects.append({"node": b, "t": -delay, "life": 0.45, "kind": "fall", "from": target + Vector3(0.6, 9, -0.4), "to": target + Vector3(0, 0.3, 0),
		"tid": tid})


func _update_effects(dt: float) -> void:
	var keep := []
	var landed := []
	for fx in effects:
		# each effect ticks in its own call: if one ever errors, only that effect is dropped
		if _tick_effect(fx, dt, landed):
			keep.append(fx)
		elif is_instance_valid(fx.node):
			(fx.node as Node).queue_free()
	effects = keep
	if not _timers.is_empty():
		var later := []
		for tm in _timers:
			tm[0] = float(tm[0]) - dt
			if float(tm[0]) <= 0.0:
				_fx_queue.append(tm[1])
			else:
				later.append(tm)
		_timers = later
	for p in landed:
		_boulder_impact(Vector3(p.x, 0.0, p.z), 1.0)
		shake = maxf(shake, 0.35)
	# effects that spawn effects (a tar glob landing, a spike bursting up) queue them here, after the loop
	if not _fx_queue.is_empty():
		var q := _fx_queue
		_fx_queue = []
		for c in q:
			(c as Callable).call()


## Fades a mesh: k = 0 as made, 1 gone. The Compatibility renderer ignores GeometryInstance3D.transparency, so it swaps
## between cached alpha steps of the mesh's own material (10 steps; one material per step, shared by every user).
var _fade_mats := {}
func _fade(n: Node, k: float) -> void:
	var gi := n as GeometryInstance3D
	if gi == null:
		return
	gi.set_meta("fade_k", k)
	var base: BaseMaterial3D = gi.get_meta("fade0") if gi.has_meta("fade0") else gi.material_override as BaseMaterial3D
	if base == null:
		return
	if not gi.has_meta("fade0"):
		gi.set_meta("fade0", base)
	var lvl := clampi(int(round(k * 10.0)), 0, 10)
	if lvl >= 10:
		gi.visible = false
		return
	var key := "%d_%d" % [base.get_instance_id(), lvl]
	if not _fade_mats.has(key):
		if lvl == 0:
			_fade_mats[key] = base
		else:
			var m: BaseMaterial3D = base.duplicate()
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.albedo_color.a = base.albedo_color.a * (1.0 - lvl / 10.0)
			_fade_mats[key] = m
	if gi.material_override != _fade_mats[key]:
		gi.material_override = _fade_mats[key]


## Advances one effect; returns false when it's finished (or broke) and its node should go.
func _tick_effect(fx: Dictionary, dt: float, landed: Array) -> bool:
	fx.t += dt
	if not is_instance_valid(fx.node):
		return false
	var n: Node3D = fx.node
	var k: float = clampf(fx.t / fx.life, 0.0, 1.0) if fx.life != INF else 0.0
	if true:
		match fx.kind:
			"spin":
				var ring: Node3D = n.get_meta("spin")
				ring.scale = Vector3.ONE * (1.0 + 0.05 * sin(time_s * 4.0))
				var core: Node3D = n.get_meta("core")
				core.rotation.y += dt * 2.0
			"portal":
				var fl: float = n.get_meta("flash")
				if fl > 0.0:
					fl = maxf(0.0, fl - dt * 2.5)
					n.set_meta("flash", fl)
				var layers: Array = n.get_meta("layers")
				for li in layers.size():
					var lyr: Node3D = layers[li]
					lyr.rotation.z += dt * (2.6 if li % 2 == 0 else -1.7) * (1.0 + fl * 2.0)
				var vx: Node3D = n.get_meta("vortex")
				vx.scale = Vector3.ONE * (1.0 + 0.04 * sin(time_s * 5.0) + 0.22 * fl)
				(n.get_meta("lights") as Node3D).rotation.z -= dt * 0.8
				var pl: OmniLight3D = n.get_meta("light")
				pl.light_energy = 2.0 + 0.5 * sin(time_s * 7.0) + 5.0 * fl
				var at: float = float(n.get_meta("arc_t")) - dt
				if at <= 0.0:
					at = randf_range(0.15, 0.6)
					var a0 := randf() * TAU
					var a1 := a0 + randf_range(0.6, 1.6)
					var hz2: float = n.get_meta("hz")
					var p0 := n.global_transform * Vector3(cos(a0) * 1.4, hz2 + sin(a0) * 1.4, 0)
					var p1 := n.global_transform * Vector3(cos(a1) * 1.4, hz2 + sin(a1) * 1.4, 0)
					_portal_arc(p0, p1)
				n.set_meta("arc_t", at)
			"rift":
				var rfl: float = n.get_meta("flash")
				if rfl > 0.0:
					rfl = maxf(0.0, rfl - dt * 3.0)
					n.set_meta("flash", rfl)
				var rl: Array = n.get_meta("layers")
				for li in rl.size():
					(rl[li] as Node3D).rotation.z += dt * (3.2 if li % 2 == 0 else -2.2) * (1.0 + rfl * 2.0)
				var rr: Node3D = n.get_meta("ring")
				rr.position.y = 1.05 + 0.06 * sin(time_s * 2.5 + n.position.x)
				rr.scale = Vector3.ONE * (1.0 + 0.25 * rfl)
			"portal_wave":
				var sc := 1.0 + k * (2.4 if fx.get("big", false) else 1.6)
				n.scale = Vector3(sc, sc, 1.0 + k)
				(n.material_override as StandardMaterial3D).albedo_color.a = 0.9 * (1.0 - k)
			"portal_arc":
				n.visible = int(fx.t * 30.0) % 2 == 0
			"fire":
				fx.f1.scale = Vector3(1, 1.0 + 0.15 * sin(time_s * 13.0), 1)
				fx.f2.scale = Vector3(1, 1.0 + 0.2 * sin(time_s * 17.0 + 1.0), 1)
				fx.light.light_energy = float(fx.base_e) * (0.9 + 0.2 * sin(time_s * 11.0))
			"bob":                                     # v0.9.28: a boat rocking on the river
				n.position.y = float(fx.y0) + 0.025 * sin(fx.t * 1.4)
				n.rotation.x = 0.035 * sin(fx.t * 1.1 + 0.6)
				n.rotation.z = 0.025 * sin(fx.t * 0.8)
			"lava":
				var pulse := 0.5 + 0.5 * sin((time_s + fx.t) * 2.2)
				fx.light.light_energy = 0.6 + 0.5 * pulse
				var pm := (fx.pool as GeometryInstance3D).material_override as StandardMaterial3D
				if pm != null:                  # (a lava-pool shader animates itself)
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
				var sz: float = float(fx.get("s", 1.0)) * (1.0 - k * k)
				n.scale = Vector3(sz, sz * 0.25, sz) if fx.get("flat", false) else Vector3.ONE * sz
			"scorch":
				(n.material_override as StandardMaterial3D).albedo_color.a = 0.45 * (1.0 - k * k)
			"ambient":
				fx.smoke_t = float(fx.smoke_t) - dt
				if fx.smoke_t <= 0.0 and fx.fire != Vector3.INF:
					fx.smoke_t = 0.35
					if _fx_room(1):
						var pf := _mi(_fx_mesh("dust"), _puff_mat(Color(0.6, 0.6, 0.62, 0.45)), self, fx.fire + Vector3(0, 1.0, 0))
						pf.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
						effects.append({"node": pf, "t": 0.0, "life": 2.4, "kind": "smoke", "v": Vector3(randf_range(-0.1, 0.25), 0.9, randf_range(-0.15, 0.15))})
				var vy: float = n.get_meta("vy", 0.0)
				var bx: Array = n.get_meta("box", [-20, -12, 20, 12])
				for m in n.get_children():
					var sd: float = m.get_meta("seed")
					m.position += Vector3(sin(time_s * 0.4 + sd) * 0.25, sin(time_s * 0.7 + sd * 2.0) * 0.12 + vy * (0.7 + 0.3 * sin(sd)), cos(time_s * 0.3 + sd) * 0.2) * dt
					if vy < 0.0 and m.position.y < 0.05:
						m.position = Vector3(randf_range(bx[0], bx[2]), 6.0, randf_range(bx[1], bx[3]))
					elif vy > 0.0 and m.position.y > 6.0:
						m.position = Vector3(randf_range(bx[0], bx[2]), 0.1, randf_range(bx[1], bx[3]))
			"smoke":
				n.position += fx.v * dt
				n.scale = Vector3.ONE * (0.8 + k * 2.6)
				_fade(n, 0.35 + 0.65 * k)
			"spark":
				fx.v.y -= 10.0 * dt
				n.position += fx.v * dt
				n.scale = Vector3.ONE * (1.0 - k)
			"flash":
				n.scale = Vector3.ONE * fx.s * (0.6 + k * 1.2)
				_fade(n, k * k)
				n.visible = k < 0.95
			"dust":
				n.visible = fx.t >= 0.0             # (a puff can wait for its moment: a shock of dirt running out)
				n.position += fx.v * dt
				fx.v *= 0.9
				n.scale = Vector3.ONE * (0.6 + k * 1.6)
				_fade(n, k)
			"glob":
				_tick_glob(fx, n)
			"spike":
				_tick_spike(fx, n)
			"stuck":
				_tick_stuck(fx, n)
			"beam":
				_tick_beam(fx, n)
			"hammer":
				_tick_hammer(fx, n)
			"javelin":
				_tick_javelin(fx, n)
			"fury":
				_tick_fury(fx, n)
			"slash":
				var sb: Basis = fx.b0
				n.basis = (sb * Basis(Vector3.UP, deg_to_rad(lerpf(38.0, -42.0, k)))).scaled(Vector3.ONE * (0.9 + 0.3 * k))
				_fade(n, k * k)
			"wave":
				var wr := minf(FLARE_R0 + float(fx.speed) * fx.t, float(fx.r))
				n.scale = Vector3(wr, 1.0, wr)
				_fade(n, clampf((wr / float(fx.r) - 0.7) / 0.3, 0.0, 1.0) if fx.t < fx.life - 0.12 else 1.0)
			"glint":
				n.position += fx.v * dt
				fx.v *= pow(0.92, dt * 60.0)
				n.scale = Vector3.ONE * float(fx.s) * (1.0 - k * k)
			"lance":
				var lk := clampf(fx.t / float(fx.travel), 0.0, 1.0)
				if fx.t <= float(fx.travel):                 # (it homes in on the robot as it walks)
					var live := _robot_point(int(fx.tid), float(fx.h))
					if live != Vector3.INF:
						fx.to = live
				var lp: Vector3 = (fx.from as Vector3).lerp(fx.to, lk)
				var ld: Vector3 = (fx.to as Vector3) - (fx.from as Vector3)
				if ld.length() > 0.05:
					n.look_at_from_position(lp, lp + ld, Vector3.UP if absf(ld.normalized().y) < 0.98 else Vector3.RIGHT)
				else:
					n.position = lp
				n.scale = Vector3(1.0, 1.0, lerpf(0.5, 1.3, lk))
				if fx.t > fx.travel:
					_fade(n, clampf((fx.t - fx.travel) / maxf(fx.life - fx.travel, 0.01), 0.0, 1.0))
			"decal":
				n.visible = fx.t >= 0.0
				var dk: float = clampf(fx.t / 0.08, 0.0, 1.0)
				n.scale = fx.size * (0.55 + 0.45 * dk * (2.0 - dk))
				_fade(n, clampf((k - 0.6) / 0.4, 0.0, 1.0))
			"pop":
				n.visible = fx.t >= 0.0
				n.scale = Vector3.ONE * float(fx.s) * sin(clampf(k, 0.0, 1.0) * PI)
			"fall":
				n.visible = fx.t >= 0.0
				n.position = fx.from.lerp(fx.to, k * k)
				n.rotation += Vector3(5, 3, 2) * dt
				if fx.t >= fx.life:
					landed.append(fx.to)
					if int(fx.get("tid", -1)) >= 0:
						var ltid := int(fx.tid)
						_fx_queue.append(func() -> void: _land_hit(ltid))
	return fx.t < fx.life


# =================================================================== loop
func _process(delta: float) -> void:
	time_s += delta
	_tick_viewers(delta)
	_drag_scroll_tick(delta)
	_fit_modals()
	if paused or (started and detail_open > 0):
		_update_hud(0.0)
		_hq_anim_freeze()
		return
	_auto_start(delta)
	_attract_tick()
	if (started or attract) and sim.state != "lost":
		accum += delta * speed
		var steps := 0
		while accum >= TICK and steps < MAX_STEPS_PER_FRAME:
			sim.step()
			accum -= TICK
			steps += 1
		if steps == MAX_STEPS_PER_FRAME:
			accum = 0.0
	_handle_events()
	_confirm_bar_tick()
	_sync_visuals(clampf(accum / TICK, 0.0, 1.0))
	_tick_lanes(delta)
	_tick_preview(delta)
	_update_effects(delta)
	_update_hud(delta)
	shake = maxf(0.0, shake - delta * 2.5)
	var sk := shake if Progress.setting("shake") else 0.0
	if attract:
		if portal_nodes.has(0):
			_hub_camera()
		else:
			cam.position = cam_base + Vector3(sin(time_s * 0.12) * 1.6, 0, cos(time_s * 0.09) * 0.8)
		return
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
	var pj: String = str(u.stats.get("proj", ""))
	if t == "musketeer" or t == "isla":
		_sfx("musket", -7.0, 0.12, 0.05)
	elif PROJ_SFX.has(pj):
		_sfx(PROJ_SFX[pj], -7.0, 0.15, 0.05)
	elif t in ["boulder_catapult", "torsion_catapult", "onager", "trebuchet", "ballista"]:
		_sfx("catapult", -8.0, 0.15, 0.05)
	elif t == "bronze_archer":
		_sfx("arrow", -6.0, 0.15, 0.05)
	else:
		_sfx("throw", -8.0, 0.15, 0.05)


func _handle_events() -> void:
	# robots that a tar glob, earth spike or club shock will reach a moment from now (their death waits for it)
	_atk_pending.clear()
	for ev0 in sim.events:
		if ev0.e in ["pulse", "slam"] and not (ev0.get("targets", []) as Array).is_empty():
			var u0 = sim.get_unit(ev0.id)
			if u0 != null and (u0.type in ["tar_shaman", "mara", "club_warrior"] or (u0.type in ["spear_guard", "sun_priest", "kira"]
					and _hq_clips(ev0.id))):
				for t0 in ev0.targets:
					_atk_pending[int(t0)] = true
		elif ev0.e == "ability" and (str(ev0.get("type", "")) in ["rain", "quake"] or (str(ev0.get("type", "")) == "flare"
				and sim.hero != null and _hq_clips(sim.hero.id))):
			for t0 in ev0.get("ids", []):                # Stone Rain's boulders and the Earthquake's spikes
				_atk_pending[int(t0)] = true
		elif ev0.e == "impact" and _javs.has(int(ev0.pid)) and not bool(_javs[int(ev0.pid)].landed):
			if int(ev0.get("eid", -1)) >= 0:              # an HQ javelin, still in the air
				_atk_pending[int(ev0.eid)] = true
		elif ev0.e == "impact" and _hammers.has(int(ev0.pid)) and not bool(_hammers[int(ev0.pid)].landed):
			if int(ev0.get("eid", -1)) >= 0:              # Tarek's hammer, still in the air
				_atk_pending[int(ev0.eid)] = true
			for ev1 in sim.events:                       # (and what its splash destroyed)
				if ev1.e == "kill" and (ev1.pos as Vector2).distance_to(ev0.pos) <= float(ev0.get("splash", 0.0)) + 0.3:
					_atk_pending[int(ev1.id)] = true
	for ev in sim.events:
		match ev.e:
			"place":
				_spawn_tower_node(sim.get_tower(ev.id))
			"hero_place":
				_spawn_hero_node()
			"hero_level":
				if sim.hero != null:
					var hn = tower_nodes.get(sim.hero.id)
					if hn == null or not is_instance_valid(hn) or not (hn as Node3D).has_meta("anim") \
							or ((hn as Node3D).get_meta("anim") as AnimationPlayer).current_animation != "Ability":
						_hq_play(sim.hero.id, "Cheer")             # (a rank-up doesn't cut her ability short)
					_float_text(_v3(sim.hero.pos, 2.5), "RANK %d!" % ev.level, C_GOLD, 60)
					_ring_fx(_v3(sim.hero.pos, 0.3), 1.6, C_GOLD, 0.6)
					if sim.ability_unlocked() and ev.level == int(sim.hero_def.ability.get("unlock", 3)):
						_toast("%s unlocked!  Press the hero button to use it." % sim.hero_def.ability.name, C_GOLD)
						toast_t = 3.5
				_sfx("level_up", -4.0, 0.0, 0.3)
			"ability":
				if sim.hero != null:
					_hq_play(sim.hero.id, "Ability")
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
					if absf(float(e.dist) - Sim.SPAWN_DIST) < 0.05:
						n.set_meta("emerge", true)
						n.scale = Vector3.ONE * 0.05
						_portal_flash(int(e.pi), bool(e.boss))
						_sfx("portal_warp", -10.0 if not e.boss else -2.0, 0.12)
					if e.boss:
						shake = 1.0
						var roar := "boss_roar"
						if e.type == "siege_crawler":
							roar = "boss_roar_bronze"
						elif e.type != "prime_walker":
							roar = "boss_roar_mech"
						_sfx(roar, -6.0, 0.0, 2.0)
						_banner("THE %s HAS ARRIVED" % str(defs.enemies[e.type].name), Color(1, 0.35, 0.3))
			"hit":
				if enemy_nodes.has(ev.id):
					enemy_nodes[ev.id].set_meta("punch", 1.0)
					enemy_nodes[ev.id].set_meta("flash", 1.0)
			"shield_break":
				if enemy_nodes.has(ev.id):
					_ring_fx(enemy_nodes[ev.id].position + Vector3(0, 0.7, 0), 1.0, Color(0.4, 0.9, 1.0), 0.3)
					if (enemy_nodes[ev.id] as Node3D).has_meta("shield_panel"):
						_shield_shatter(enemy_nodes[ev.id])
				_sfx("shield_break", -10.0, 0.1, 0.15)
			"shield_up":
				_sfx("shield_up", -16.0, 0.1, 0.5)
			"heal":
				if enemy_nodes.has(ev.id):
					_ring_fx(enemy_nodes[ev.id].position + Vector3(0, 0.3, 0), ev.radius, Color(0.3, 1.0, 0.4), 0.5)
					if (enemy_nodes[ev.id] as Node3D).has_meta("anim"):
						_drone_heal(int(ev.id), float(ev.radius))
				_sfx("heal", -12.0, 0.05, 0.4)
			"warp":
				for wp in [ev.from, ev.to]:
					var rn = rift_nodes.get(str((wp as Vector2).snapped(Vector2(0.1, 0.1))))
					if rn != null:
						(rn as Node3D).set_meta("flash", 1.0)
				_ring_fx(_v3(ev.to, 0.4), 1.3, Color(0.4, 0.95, 1.0, 0.9), 0.35)
				_sfx("cloak", -16.0, 0.1, 0.15)
			"kill":
				if _atk_pending.has(int(ev.id)) and enemy_nodes.has(ev.id) and not _splits_on_death(str(ev.type)):
					# killed by a tar glob / spike / shock that is still on its way: it freezes and blows up when that
					# lands (the effect's _hold_hit sets the time; 4 s is only a safety net). Robots that burst into
					# others or blast an EMP when they die go at once, so nothing comes out of an intact robot.
					_doomed[int(ev.id)] = ev
					var dn: Node3D = enemy_nodes[ev.id]
					if dn.has_meta("anim"):
						(dn.get_meta("anim") as AnimationPlayer).speed_scale = 0.0
					(dn.get_node("Bar") as Node3D).visible = false
					var did := int(ev.id)
					_fx_after(4.0, func() -> void: _resolve_doom(did))
				else:
					_robot_killed(ev)
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
				if u2 != null and u2.type == "club_warrior":
					_club_smash(u2, ev.get("targets", []))      # v0.9.20: the smash lands on the robots, no ring
				elif u2 != null and u2.type == "spear_guard" and _hq_clips(ev.id):
					_spear_thrust(u2, ev.get("targets", []))    # v0.9.22: a lance of light from the spear's point
				elif u2 != null and u2.type == "kira" and _hq_clips(ev.id):
					_kira_slash(u2, ev.get("targets", []))      # v0.9.25: golden cuts as her whirl sweeps through
				elif u2 != null:
					_ring_fx(_v3(u2.pos, 0.2), ev.radius, Color(1, 0.8, 0.45) if u2.type != "flamethrower" else Color(1, 0.5, 0.1), 0.35)
					_dust_fx(_v3(u2.pos + u2.facing * 0.8, 0.2), 5, 0.7)
					if _style2():
						_pebble_fx(_v3(u2.pos + u2.facing * 1.0, 0.3), 3)
				if u2 != null:
					var slam_col := Color(1, 0.8, 0.45)
					var ss := "club"
					if u2.type in ["spear_guard", "kira", "brenna", "cassia", "legionary"]:
						ss = "spear"
					elif u2.type in ["axe_warrior", "knight", "halberdier", "aldric", "glitch"]:
						ss = "swing"
					elif u2.type == "steam_brawler" or u2.type == "jim":
						ss = "steam"
					elif u2.type == "flamethrower":
						ss = "flame"
						slam_col = Color(1, 0.5, 0.1)
					elif u2.type in ["mech_brawler", "titan_mech"]:
						slam_col = Color(0.9, 0.4, 1.0)
					_sfx(ss, -4.0, 0.12, 0.05)
					if u2.type == "flamethrower":
						_dust_fx(_v3(u2.pos + u2.facing * 1.2, 0.5), 4, 0.9)
			"pulse":
				_animate_fire(ev.id)
				var u3 = sim.get_unit(ev.id)
				var tg3: Array = ev.get("targets", [])
				if u3 != null and u3.type in ["tar_shaman", "mara"] and not tg3.is_empty():
					# v0.9.20: real attacks instead of a ring: tar globs / stone spikes on the robots hit
					_face_targets(ev.id, u3, tg3)
					if u3.type == "tar_shaman":
						_tar_volley(u3, tg3)
					else:
						_earth_spikes(u3, tg3)
				elif u3 != null and u3.type == "sun_priest" and not tg3.is_empty() and _hq_clips(ev.id):
					_face_targets(ev.id, u3, tg3)
					_sun_beams(u3, tg3)                         # v0.9.24: beams of sunlight from the disc on his staff
				elif u3 != null:
					var pcol := Color(0.4, 1.0, 0.5)
					if u3.type == "sun_priest":
						pcol = Color(1.0, 0.85, 0.3)
					elif u3.type == "mara":
						pcol = Color(0.75, 0.5, 1.0)
					elif PULSE_COLORS.has(u3.type):
						pcol = PULSE_COLORS[u3.type]
					if u3.get("branch", "") == "B":
						pcol = Color(1, 0.5, 0.1)
					_ring_fx(_v3(u3.pos, 0.25), ev.radius, pcol, 0.6)
					if tower_nodes.has(ev.id) and tower_nodes[ev.id].has_meta("orb"):
						var orb: Node3D = tower_nodes[ev.id].get_meta("orb")
						orb.scale = Vector3.ONE * 2.2
				var ps := "pulse"
				var u3b = sim.get_unit(ev.id)
				if u3b != null:
					ps = PULSE_SFX.get(u3b.type, "pulse")
				_sfx(ps, -7.0, 0.1, 0.08)
			"proj":
				var p = _proj_by_id(ev.id)
				if p != null:
					if _tarek_hq(p):
						_tarek_throw(p)                     # v0.9.26: his red-hot hammer flies from his hand (an effect)
					elif _jav_hq(p):
						_jav_throw(p)                       # v0.9.29: the javelin flies from his hand when his clip throws it
					else:
						proj_nodes[ev.id] = _make_projectile(p)
			"impact":
				if _hammers.has(int(ev.pid)):
					_tarek_impact(ev)                       # it strikes when the flying hammer gets there
					continue
				if _javs.has(int(ev.pid)):
					_jav_impact(ev)                         # it strikes when the flying javelin gets there
					continue
				if _tarek_unseen(ev) or _jav_unseen(ev):
					continue
				var boulder := false
				var hot_b := false
				var pot := false
				var arrow := false
				if proj_nodes.has(ev.pid):
					var pnode: Node3D = proj_nodes[ev.pid]
					boulder = pnode.has_meta("boulder")
					hot_b = pnode.has_meta("hot")
					pot = pnode.has_meta("pot")
					if pnode.has_meta("arrow_hq"):
						arrow = true
						_arrow_hit(pnode, ev)
					pnode.queue_free()
					proj_nodes.erase(ev.pid)
				else:                                   # (it flew and landed within one frame: no node was made)
					var su = sim.get_unit(int(ev.get("tower", -1)))
					if su != null and (su.type in ["boulder_catapult", "torsion_catapult"] or (su.type == "rock_slinger" and float(ev.splash) > 0.0)):
						boulder = true
						hot_b = su.type in ["boulder_catapult", "torsion_catapult"] and str(ev.get("dtype", "")) == "fire"
						pot = hot_b and su.type == "torsion_catapult"
					elif su != null and (su.type == "bronze_archer" or str(su.stats.get("proj", "")) == "arrow"):
						arrow = true
						_arrow_hit_unseen(su, ev)
				if arrow:
					_sfx("rock_hit", -12.0, 0.25, 0.05)
					if float(ev.splash) > 0.0 and str(ev.get("dtype", "")) != "fire":
						_dust_fx(_v3(ev.pos, 0.2), 4, ev.splash)
				elif boulder:
					# v0.9.20: the catapult's (and the Boulder Hurler's) boulder smashes down: crater, dust, flying rock
					_boulder_impact(_v3(ev.pos, 0.0), clampf(float(ev.splash), 0.6, 1.6), not pot)
					if hot_b:
						_fire_splash(_v3(ev.pos, 0.0), clampf(float(ev.splash), 0.6, 1.6))
					if pot:
						_pot_shards(_v3(ev.pos, 0.0))
					_sfx("boulder_land", -8.0, 0.15, 0.08)
					shake = maxf(shake, 0.2)
				elif ev.splash > 0.0:
					_ring_fx(_v3(ev.pos, 0.2), ev.splash, Color(1, 0.65, 0.3), 0.3)
					_dust_fx(_v3(ev.pos, 0.2), 6, ev.splash)
					_sfx("explosion" if _era_index() >= 5 else "boulder_land", -8.0, 0.15, 0.08)
					shake = maxf(shake, 0.18)
				else:
					_sfx("rock_hit", -10.0, 0.2, 0.05)
					if _era_index() < 5:      # thrown rocks, arrows and bolts kick up dirt; bullets and beams don't
						_pebble_fx(_v3(ev.pos, 0.9))
				if ev.crit:
					_float_text(_v3(ev.pos, 1.8), "CRIT!", Color(1, 0.35, 0.25), 44)
			"emp":
				_ring_fx(_v3(ev.pos, 0.3), float(ev.radius), Color(0.45, 0.85, 1.0), 0.6)
				_ring_fx(_v3(ev.pos, 0.3), float(ev.radius) * 0.6, Color(0.7, 0.95, 1.0), 0.45)
				_sfx("emp", -4.0, 0.05, 0.3)
				shake = maxf(shake, 0.4)
			"chain":
				_chain_fx(ev.pts)
				_sfx("zap", -10.0, 0.15, 0.06)
			"enrage":
				if enemy_nodes.has(ev.id):
					var en: Node3D = enemy_nodes[ev.id]
					_float_text(en.position + Vector3(0, 3.5, 0), "ENRAGED!", Color(1, 0.3, 0.2), 80)
					_ring_fx(en.position + Vector3(0, 0.3, 0), 3.0, Color(1, 0.3, 0.2), 0.6)
				_sfx("steam", 0.0, 0.0, 1.0)
				shake = 0.8
			"reveal":
				if enemy_nodes.has(ev.id):
					_ring_fx(enemy_nodes[ev.id].position + Vector3(0, 0.3, 0), 0.9, Color(0.6, 1.0, 0.8), 0.35)
				_sfx("cloak", -12.0, 0.1, 0.4)
			"summon":
				var be = sim._enemy_by_id(ev.id)
				if be != null and enemy_nodes.has(ev.id) and (enemy_nodes[ev.id] as Node3D).has_meta("anim"):
					var bap: AnimationPlayer = (enemy_nodes[ev.id] as Node3D).get_meta("anim")
					if bap.has_animation("Summon"):
						bap.play("Summon", 0.15)
				if be != null:
					_ring_fx(_v3(be.pos, 0.3), 2.8, Color(1, 0.2, 0.15), 0.6)
					_sfx("summon", -6.0, 0.05, 0.5)
			"wave_start":
				_banner("WAVE %d" % ev.wave, C_TEXT)
				_sfx("wave_horn", -3.0, 0.03, 0.5)
			"wave_clear":
				waves_cleared += 1
				_toast("Wave %d cleared!  +%d gold" % [ev.wave, ev.bonus], C_COIN)
				_sfx("coin", -4.0, 0.0)
			"victory":
				if not attract:
					_show_overlay(true)
			"defeat":
				if not attract:
					_show_overlay(false)
	sim.events.clear()


# ---------------------------------------------------------------- Bronze Age attacks (v0.9.21)
# The Bronze Archer looses his arrows from the bow of his HQ model (wherever it is as he lets go). They fly in a
# shallow arc and stick in the robot they hit, quivering, then drop away (an arrow whose robot died on the way sticks
# in the ground), and the bronze head strikes sparks. Fire Archer (Path A) arrows burn in flight, trailing embers, and
# burst into flame where they land. The arrows leave the string at RELEASE in tools/blender/hq/anim_archer.py.
const ARCHER_BOW := Vector3(-0.03, 1.41, 1.12)    # the nocked arrows' tips at full draw (model units, Godot axes, Yaw node)
const ARROW_LEN := 0.78


## A real arrow (one cached mesh): a reed shaft, a leaf-shaped bronze head, red and white fletching. The tip is at the
## origin and the arrow lies along +Z, so a node looking along its flight (-Z) carries it point first.
func _arrow_mesh(fire: bool) -> ArrayMesh:
	var key := "arrow_mesh_fire" if fire else "arrow_mesh"
	if _atk_cache.has(key):
		return _atk_cache[key]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_smooth_group(-1)
	var w := 0.019
	_arrow_prism(st, 0.11, ARROW_LEN - 0.03, w, Color(0.8, 0.62, 0.36))            # reed shaft
	_arrow_prism(st, 0.09, 0.135, w * 1.3, Color(0.36, 0.14, 0.08))                # sinew binding behind the head
	_arrow_prism(st, ARROW_LEN - 0.035, ARROW_LEN, w * 1.3, Color(0.3, 0.1, 0.06))  # nock
	for i in 3:                                                                    # fletching: two red vanes, one white
		var a := TAU * i / 3.0 + 0.4
		var r := Vector3(cos(a), sin(a), 0.0)
		var col := Color(0.96, 0.94, 0.88) if i == 0 else Color(0.84, 0.15, 0.08)
		var z0 := ARROW_LEN - 0.22
		var z1 := ARROW_LEN - 0.045
		var q := [r * w + Vector3(0, 0, z0), r * 0.046 + Vector3(0, 0, z0 + 0.08), r * 0.066 + Vector3(0, 0, z1), r * w + Vector3(0, 0, z1)]
		for tri in [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]:
			for v in tri:
				st.set_color(col)
				st.add_vertex(v)
	st.generate_normals()
	var m := st.commit()
	var sm := StandardMaterial3D.new()
	sm.vertex_color_use_as_albedo = true
	sm.roughness = 0.75
	sm.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.surface_set_material(0, sm)
	var st2 := SurfaceTool.new()                       # the head: a flat leaf-shaped point with a raised midrib
	st2.begin(Mesh.PRIMITIVE_TRIANGLES)
	st2.set_smooth_group(-1)
	var back := Vector3(0, 0, 0.12)
	var ring := [Vector3(0.046, 0, 0.068), Vector3(0, 0.016, 0.06), Vector3(-0.046, 0, 0.068), Vector3(0, -0.016, 0.06)]
	for i in 4:
		var j := (i + 1) % 4
		for tri in [[Vector3.ZERO, ring[i], ring[j]], [ring[j], ring[i], back]]:
			for v in tri:
				st2.add_vertex(v)
	st2.generate_normals()
	st2.commit(m)
	var hm := StandardMaterial3D.new()
	if fire:
		hm.albedo_color = Color(1.0, 0.55, 0.15)
		hm.emission_enabled = true
		hm.emission = Color(1.0, 0.42, 0.06)
		hm.emission_energy_multiplier = 2.5
	else:
		hm.albedo_color = Color(0.92, 0.66, 0.3)
		hm.metallic = 0.7
		hm.roughness = 0.3
	hm.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.surface_set_material(1, hm)
	_atk_cache[key] = m
	return m


func _arrow_prism(st: SurfaceTool, z0: float, z1: float, w: float, col: Color) -> void:
	var c := [Vector2(w, 0), Vector2(0, w), Vector2(-w, 0), Vector2(0, -w)]
	for i in 4:
		var a: Vector2 = c[i]
		var b: Vector2 = c[(i + 1) % 4]
		var q := [Vector3(a.x, a.y, z0), Vector3(b.x, b.y, z0), Vector3(b.x, b.y, z1), Vector3(a.x, a.y, z1)]
		for tri in [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]:
			for v in tri:
				st.set_color(col)
				st.add_vertex(v)


## Height of a robot's middle (where an arrow strikes it).
func _hit_height(e) -> float:
	return _hit_height_of(str(e.type) if e != null else "")


func _hit_height_of(type: String) -> float:
	if not defs.enemies.has(type):
		return 0.75
	var d: Dictionary = defs.enemies[type]
	return float(d.get("bar_h", 1.4)) * 0.5 + (0.9 if d.get("flying", false) else 0.0)


## The robot type behind robot id `eid`, also for one already destroyed whose blow-up is held back (`_doomed`).
func _robot_type(eid: int) -> String:
	var e = sim._enemy_by_id(eid)
	if e != null:
		return str(e.type)
	if _doomed.has(eid):
		return str(_doomed[eid].get("type", ""))
	return ""


## An arrow in flight. From the HQ Bronze Archer it starts at his bow and settles onto the sim's projectile as it flies
## (see _arrow_flight); other archers' arrows start above their tower as before.
func _arrow_proj(root: Node3D, p: Dictionary, u, dt: String) -> void:
	var fire := dt == "fire"
	_mi(_arrow_mesh(fire), null, root)
	root.set_meta("arrow", true)
	root.set_meta("arrow_hq", true)
	if fire:
		_fire_halo(root, 0.34)
		root.set_meta("fire", true)
	var e = sim._enemy_by_id(int(p.get("target", -1)))
	var hit_h := _hit_height(e)
	var launch := root.position
	if u != null and u.type == "bronze_archer" and tower_nodes.has(u.id) and (tower_nodes[u.id] as Node3D).has_meta("anim") \
			and (tower_nodes[u.id] as Node3D).has_meta("yaw"):
		var yaw: Node3D = (tower_nodes[u.id] as Node3D).get_meta("yaw")
		launch = yaw.global_transform * ARCHER_BOW
	root.position = launch
	var aim: Vector2 = p.aim
	root.set_meta("h0", launch.y)
	root.set_meta("hit_h", hit_h)
	root.set_meta("off", Vector3(launch.x, 0.0, launch.z) - _v3(p.pos, 0.0))
	root.set_meta("d0", maxf((aim - (p.pos as Vector2)).length(), 0.5))
	var tp := _v3(aim, hit_h)
	var dv := tp - launch
	if dv.length() > 0.01 and absf(dv.normalized().y) < 0.98:
		root.look_at(tp, Vector3.UP)


## Where an HQ arrow is this frame: on the sim's projectile (moved on by the frame's share of a tick), plus what is
## left of its offset from the bow, from the bow's height down to the robot's middle, in a shallow arc.
func _arrow_flight(pn: Node3D, p: Dictionary, alpha: float) -> Vector3:
	var aim: Vector2 = p.aim
	var pos: Vector2 = p.pos
	pos += (aim - pos).limit_length(float(p.speed) * TICK * alpha)
	var d0: float = pn.get_meta("d0")
	var k := clampf(1.0 - (aim - pos).length() / d0, 0.0, 1.0)
	var off: Vector3 = pn.get_meta("off")
	var y := lerpf(float(pn.get_meta("h0")), float(pn.get_meta("hit_h")), k) + 0.5 * k * (1.0 - k) * minf(d0 / 6.0, 1.0)
	return _v3(pos, y) + off * (1.0 - k)


## A burning arrow trails embers (FULL graphics): about 25 a second while it flies (none once the match has stopped).
func _arrow_embers(pn: Node3D, moved: float, dt: float) -> void:
	if Progress.gfx_level() > 0 or moved < 0.004:
		return
	var acc: float = float(pn.get_meta("ember_t", 0.0)) + dt
	if acc < 0.04:
		pn.set_meta("ember_t", acc)
		return
	pn.set_meta("ember_t", acc - 0.04)
	if not _fx_room(1):
		return
	var at := pn.global_transform * Vector3(randf_range(-0.02, 0.02), randf_range(-0.02, 0.02), randf_range(0.05, 0.2))
	var em := _mi(_fx_mesh("mote"), _atk_mat("ember"), self, at, Vector3.ZERO, Vector3.ONE * randf_range(0.5, 0.9))
	em.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.append({"node": em, "t": 0.0, "life": randf_range(0.25, 0.4), "kind": "spark",
		"v": Vector3(randf_range(-0.4, 0.4), randf_range(0.6, 1.4), randf_range(-0.4, 0.4))})


## An arrow lands: it sticks in the robot it hit (quivering, then it sinks away) or, when that robot is gone, in the
## ground. The bronze head strikes a few sparks; a burning arrow bursts into flame (and sets the ground alight where
## the Fire Archer's arrows splash).
func _arrow_hit(pn: Node3D, ev: Dictionary) -> void:
	_arrow_hit_at(-pn.global_transform.basis.z, pn.has_meta("fire"), ev)


## The same for an arrow that flew and landed within one frame (no node was made): it came from its tower.
func _arrow_hit_unseen(su: Dictionary, ev: Dictionary) -> void:
	var d := _v3(ev.pos, 0.0) - _v3(su.pos, 0.0)
	var flat := Vector3(d.x, 0.0, d.z).normalized() if d.length() > 0.01 else Vector3.FORWARD
	_arrow_hit_at((flat + Vector3(0, -0.12, 0)).normalized(), str(ev.get("dtype", "")) == "fire", ev)


func _arrow_hit_at(dir: Vector3, fire: bool, ev: Dictionary) -> void:
	var gl := clampi(Progress.gfx_level(), 0, 2)
	if dir.length() < 0.5:
		dir = Vector3.FORWARD
	dir = dir.normalized()
	var life: float = [1.1, 0.75, 0.0][gl]
	var eid := int(ev.get("eid", -1))
	var at := _v3(ev.pos, 0.0)
	var flat := Vector3(dir.x, 0.0, dir.z)
	flat = flat.normalized() if flat.length() > 0.01 else Vector3.FORWARD
	if eid >= 0 and enemy_nodes.has(eid) and is_instance_valid(enemy_nodes[eid]):
		var en: Node3D = enemy_nodes[eid]
		var etype := _robot_type(eid)
		var size := float(defs.enemies[etype].get("size", 0.5)) if defs.enemies.has(etype) else 0.5
		var side := flat.cross(Vector3.UP)
		at = en.global_position + Vector3(0, _hit_height_of(etype) + randf_range(-0.12, 0.12), 0) - flat * size * 0.15 \
			+ side * randf_range(-0.12, 0.12)
		# (not into a robot still growing out of the portal: the arrow would grow with it; nor into one that cloaks:
		# its ghost materials don't cover the arrow, which would give it away)
		if life > 0.0 and int(en.get_meta("arrows", 0)) < 3 and not en.has_meta("emerge") and not en.has_meta("ghost") \
				and _fx_room(1):
			var d := (dir + Vector3(randf_range(-0.15, 0.15), randf_range(-0.1, 0.1), randf_range(-0.15, 0.15))).normalized()
			var a := _mi(_arrow_mesh(fire), null, en)
			a.global_transform = Transform3D(Basis.looking_at(d, Vector3.UP if absf(d.y) < 0.98 else Vector3.RIGHT), at)
			a.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			en.set_meta("arrows", int(en.get_meta("arrows", 0)) + 1)
			effects.append({"node": a, "t": 0.0, "life": life, "kind": "stuck", "b0": a.transform.basis, "en": en})
	else:
		at.y = 0.0
		if life > 0.0 and _fx_room(1):
			var gd := (flat * 0.7 + Vector3(0, -0.72, 0)).normalized()
			var g := _mi(_arrow_mesh(fire), null, self)
			g.global_transform = Transform3D(Basis.looking_at(gd, Vector3.UP), at + gd * 0.12)
			g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			effects.append({"node": g, "t": 0.0, "life": life * 1.3, "kind": "stuck", "b0": g.transform.basis})
		_dust_fx(at + Vector3(0, 0.08, 0), 2, 0.3)
	var n: int = [3, 2, 1][gl]
	if _fx_room(n):
		for i in n:
			var sp := _mi(_fx_mesh("spark"), _atk_mat("arrow_spark"), self, at - dir * 0.08)
			sp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var v := (-dir + Vector3(randf_range(-0.8, 0.8), randf_range(0.3, 1.1), randf_range(-0.8, 0.8))).normalized() * randf_range(2.5, 4.5)
			sp.look_at_from_position(sp.position, sp.position + v, Vector3.UP if absf(v.normalized().y) < 0.95 else Vector3.RIGHT)
			effects.append({"node": sp, "t": 0.0, "life": 0.2, "kind": "spark", "v": v})
	if fire:
		if _fx_room(1):
			var f := _mi(_fx_mesh("flash"), _atk_mat("fire_flash"), self, at)
			f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			effects.append({"node": f, "t": 0.0, "life": 0.22, "kind": "flash", "s": 0.6})
		if float(ev.get("splash", 0.0)) > 0.0:
			_fire_splash(_v3(ev.pos, 0.0), clampf(float(ev.splash), 0.5, 1.2))


## A stuck arrow quivers (pivoting on its embedded tip), holds, then sinks away into what it hit.
func _tick_stuck(fx: Dictionary, n: Node3D) -> void:
	var t: float = fx.t
	var b0: Basis = fx.b0
	var q := 0.16 * sin(t * 60.0) * exp(-t * 9.0)
	var k := clampf((t - fx.life * 0.8) / (fx.life * 0.2), 0.0, 1.0)
	n.transform.basis = (b0 * Basis(Vector3.RIGHT, q)).scaled(Vector3.ONE * (1.0 - k))
	if t >= fx.life and fx.has("en") and is_instance_valid(fx.en):
		(fx.en as Node3D).set_meta("arrows", maxi(0, int((fx.en as Node3D).get_meta("arrows", 1)) - 1))


# ---------------------------------------------------------------- Spear Guard (v0.9.22)
# At full reach (THRUST in tools/blender/hq/anim_spear.py) a narrow golden lance of light flies on from the spear's point
# to every robot the thrust hit, strikes sparks off it and jolts it back; a robot it destroys blows up when it lands.
const GUARD_TIP := Vector3(-0.25, 1.272, 1.841)    # the spear's point at full reach (model units, Godot axes, Yaw node)


## The lance: a long thin double cone, bright at its head, fading to nothing at its tail (head at the origin, along +Z).
func _lance_mesh() -> ArrayMesh:
	if _atk_cache.has("lance_mesh"):
		return _atk_cache["lance_mesh"]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var head := Vector3.ZERO
	var tail := Vector3(0, 0, 0.95)
	var ring := []
	for i in 4:
		var a := TAU * i / 4.0 + PI / 4.0
		ring.append(Vector3(cos(a) * 0.045, sin(a) * 0.045, 0.13))
	var c_head := Color(1.0, 1.0, 0.9, 1.0)
	var c_ring := Color(1.0, 0.85, 0.42, 0.85)
	var c_tail := Color(1.0, 0.62, 0.18, 0.0)
	for i in 4:
		var j := (i + 1) % 4
		for tri in [[head, ring[i], ring[j]], [ring[j], ring[i], tail]]:
			for v in tri:
				st.set_color(c_head if v == head else (c_tail if v == tail else c_ring))
				st.add_vertex(v)
	var m := st.commit()
	_atk_cache["lance_mesh"] = m
	return m


func _spear_thrust(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	# (the robots' hits are held now; the lances leave the spear's point as his clip reaches full reach)
	var lead := _at_attack_frame(uid, ATTACK_FRAME.spear_guard, 0.08, func() -> void: _spear_reach(uid, targets))
	for tid in targets:
		if _robot_point(int(tid), 0.0) != Vector3.INF:
			_hold_hit(int(tid), lead + 0.14)


## Full reach: a lance from the spear's point to each robot hit (capped: the rest are hit at once, no lance).
func _spear_reach(uid: int, targets: Array) -> void:
	var cap: int = [6, 4, 2][clampi(Progress.gfx_level(), 0, 2)]
	var i := 0
	for tid in targets:
		var t := int(tid)
		if _robot_point(t, 0.0) == Vector3.INF:      # (gone already, e.g. split on death: no lance for it)
			continue
		if i >= cap:
			_land_hit(t, 0.05)
			continue
		if i == 0:
			_spear_lance(uid, t)
		else:
			_fx_after(0.01 * i, func() -> void: _spear_lance(uid, t))
		i += 1


## Launched at full reach: from the spear's point (where the turning model holds it now) to the robot.
func _spear_lance(uid: int, tid: int) -> void:
	var from := Vector3.INF
	if tower_nodes.has(uid) and is_instance_valid(tower_nodes[uid]) and (tower_nodes[uid] as Node3D).has_meta("yaw"):
		from = ((tower_nodes[uid] as Node3D).get_meta("yaw") as Node3D).global_transform * GUARD_TIP
	if from == Vector3.INF:
		var u = sim.get_unit(uid)
		if u == null:                                 # (sold mid-thrust)
			_land_hit(tid, 0.05)
			return
		from = _v3(u.pos, 1.0)
	var h := _hit_height_of(_robot_type(tid))
	var to := _robot_point(tid, h)
	if to == Vector3.INF:
		_land_hit(tid)
		return
	var d := to - from
	var travel := clampf(d.length() / 24.0, 0.03, 0.13)
	if _fx_room(1) and d.length() > 0.05:
		var ln := _mi(_lance_mesh(), _atk_mat("lance"), self, from, Vector3.ZERO, Vector3(1.0, 1.0, 0.5))
		ln.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		ln.look_at(to, Vector3.UP if absf(d.normalized().y) < 0.98 else Vector3.RIGHT)
		effects.append({"node": ln, "t": 0.0, "life": travel + 0.12, "kind": "lance", "from": from, "to": to, "travel": travel,
			"tid": tid, "h": h})
	_fx_after(travel, func() -> void: _lance_hit(tid, to, from, h))


## The lance strikes: sparks and a flash where the robot is now (`at0` if it's gone), and the hit lands.
func _lance_hit(tid: int, at0: Vector3, from: Vector3, h: float) -> void:
	var at := _robot_point(tid, h)
	if at == Vector3.INF:
		at = at0
	var dir := (at - from).normalized() if at.distance_to(from) > 0.01 else Vector3.FORWARD
	var gl := clampi(Progress.gfx_level(), 0, 2)
	var n: int = [4, 3, 1][gl]
	if _fx_room(n + 1):
		for k in n:
			var sp := _mi(_fx_mesh("spark"), _atk_mat("arrow_spark"), self, at - dir * 0.12)
			sp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var v := (-dir * 0.6 + Vector3(randf_range(-0.9, 0.9), randf_range(0.2, 1.1), randf_range(-0.9, 0.9))).normalized() * randf_range(2.5, 5.0)
			sp.look_at_from_position(sp.position, sp.position + v, Vector3.UP if absf(v.normalized().y) < 0.95 else Vector3.RIGHT)
			effects.append({"node": sp, "t": 0.0, "life": 0.22, "kind": "spark", "v": v})
		var f := _mi(_fx_mesh("flash"), _atk_mat("lance_flash"), self, at - dir * 0.1)
		f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		effects.append({"node": f, "t": 0.0, "life": 0.16, "kind": "flash", "s": 0.55})
	_land_hit(tid, 0.07)


# ---------------------------------------------------------------- Sun Priest (v0.9.24)
# At RELEASE (tools/blender/hq/anim_sunpriest.py) he drives the sun staff at the robots: the disc on it flares and a beam
# of sunlight strikes from it to every robot the pulse hit (the sim slows and marks them): golden, white-hot on the High
# Priest's path (A), burning orange on the Solar Lance's (B). Where a beam strikes: a burst of light and motes (embers on
# Path B). A robot the pulse destroys blows up when its beam lands.
const SUN_DISC := Vector3(-0.087, 2.05, 1.242)     # the disc as he drives the staff at the robots (model units, Godot axes, Yaw node)
const BEAM_GROW := 0.06                           # seconds for a beam to reach its robot


## A beam of light: three crossed strips from the origin along +Z (length 1), bright down the middle and fading to
## nothing at their edges, a little wider at the far end.
func _beam_mesh() -> ArrayMesh:
	if _atk_cache.has("beam_mesh"):
		return _atk_cache["beam_mesh"]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var core0 := Color(1.0, 0.97, 0.86, 0.8)
	var core1 := Color(1.0, 0.97, 0.86, 1.0)
	var edge := Color(1.0, 0.72, 0.28, 0.0)
	for i in 3:
		var a := PI * i / 3.0
		var s := Vector3(cos(a), sin(a), 0.0)
		for side in [-1.0, 1.0]:
			var c0 := Vector3.ZERO
			var c1 := Vector3(0, 0, 1)
			var e0: Vector3 = s * 0.05 * side
			var e1: Vector3 = s * 0.085 * side + Vector3(0, 0, 1)
			for v in [[c0, core0], [e0, edge], [e1, edge], [c0, core0], [e1, edge], [c1, core1]]:
				st.set_color(v[1])
				st.add_vertex(v[0])
	var m := st.commit()
	_atk_cache["beam_mesh"] = m
	return m


## 0 golden, 1 white-hot (High Priest, Path A), 2 burning (Solar Lance, Path B).
func _sun_kind(u: Dictionary) -> int:
	match str(u.get("branch", "")):
		"A":
			return 1
		"B":
			return 2
	return 0


func _sun_beams(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	# his strike pose holds ~9 clip frames past RELEASE, 0.3 s at 1x: at 3x/10x or on a fast Solar Lance the beams' timing
	# shrinks with it, so they are gone before he swings back and winds up again
	var ts := clampf(_clip_delay(uid, 9) / 0.3, 0.25, 1.0)
	var kind := _sun_kind(u)
	# (the robots' hits are held now; the beams leave the disc as his clip reaches RELEASE)
	var lead := _at_attack_frame(uid, ATTACK_FRAME.sun_priest, 0.08, func() -> void: _sun_release(uid, targets, kind, ts))
	var cap: int = [8, 5, 3][clampi(Progress.gfx_level(), 0, 2)]
	var i := 0
	for tid in targets:
		var t := int(tid)
		if _robot_point(t, 0.0) != Vector3.INF:
			_hold_hit(t, lead + (0.012 * mini(i, cap - 1) + BEAM_GROW) * ts + 0.02)
			i += 1


## RELEASE: the disc flares and a beam reaches each robot hit (capped: the rest are hit with the last beam).
func _sun_release(uid: int, targets: Array, kind: int, ts: float) -> void:
	var cap: int = [8, 5, 3][clampi(Progress.gfx_level(), 0, 2)]
	_sun_flare(uid, kind)
	var i := 0
	var rest := []
	for tid in targets:
		var t := int(tid)
		if _robot_point(t, 0.0) == Vector3.INF:      # (gone already, e.g. split on death: no beam for it)
			continue
		if i >= cap:                                  # (past the cap: hit as the beams strike, no beam)
			rest.append(t)
			continue
		if i == 0:
			_sun_beam(uid, t, kind, ts)
		else:
			_fx_after(0.012 * i * ts, func() -> void: _sun_beam(uid, t, kind, ts))
		i += 1
	if not rest.is_empty():
		# (with the last beam's hit: robots blowing up before the beams leave would use up the effects budget)
		_fx_after((0.012 * maxi(i - 1, 0) + BEAM_GROW) * ts, func() -> void:
			for rt in rest:
				_land_hit(int(rt)))


## Where the disc is now (the turning model holds it there at RELEASE); INF without the model.
func _sun_disc(uid: int) -> Vector3:
	if tower_nodes.has(uid) and is_instance_valid(tower_nodes[uid]) and (tower_nodes[uid] as Node3D).has_meta("yaw"):
		return ((tower_nodes[uid] as Node3D).get_meta("yaw") as Node3D).global_transform * SUN_DISC
	return Vector3.INF


func _sun_flare(uid: int, kind: int) -> void:
	var at := _sun_disc(uid)
	if at == Vector3.INF or not _fx_room(1):
		return
	var f := _mi(_fx_mesh("flash"), _atk_mat(["sun_flash", "sun_flash_white", "fire_flash"][kind]), self, at)     # (orange on Solar Lance, as its beams)
	f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.append({"node": f, "t": 0.0, "life": 0.3, "kind": "flash", "s": 0.55})


func _sun_beam(uid: int, tid: int, kind: int, ts := 1.0) -> void:
	var from := _sun_disc(uid)
	if from == Vector3.INF:
		var u = sim.get_unit(uid)
		if u == null:                                 # (sold mid-swing)
			_land_hit(tid)
			return
		from = _v3(u.pos, 1.4)
	var up := _hit_height_of(_robot_type(tid))
	var to := _robot_point(tid, up)
	if to == Vector3.INF:
		_land_hit(tid)
		return
	var fx := {"to": to}
	if _fx_room(1) and from.distance_to(to) > 0.05:
		var bm := _mi(_beam_mesh(), _atk_mat(["sun_beam", "sun_beam_white", "sun_beam_hot"][kind]), self, from)
		bm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		fx = {"node": bm, "t": 0.0, "life": 0.36 * ts, "kind": "beam", "from": from, "to": to, "tid": tid, "up": up,
			"hold": 0.16 * ts, "grow": BEAM_GROW * ts, "uid": uid}
		effects.append(fx)
		_tick_beam(fx, bm)                            # aimed before it is first drawn
	_fx_after(BEAM_GROW * ts, func() -> void: _sun_hit(tid, from, fx.to, up, kind))     # (fx.to: where the beam ends now)


## A beam reaches out from the disc to its robot (following it as it walks), shimmers, and fades.
func _tick_beam(fx: Dictionary, n: Node3D) -> void:
	if not fx.has("gone"):
		var live := _robot_point(int(fx.tid), float(fx.up))
		if live != Vector3.INF:
			fx.to = live
		else:
			fx.gone = true                            # (blown up or leaked: it stays where it was)
	var src := _sun_disc(int(fx.uid))                 # (stays on the disc while he turns)
	if src != Vector3.INF:
		fx.from = src
	var from: Vector3 = fx.from
	var d: Vector3 = (fx.to as Vector3) - from
	var L := d.length()
	if L < 0.05:
		n.visible = false
		return
	var t: float = fx.t
	var grow := clampf(t / float(fx.grow), 0.04, 1.0)
	var fade := clampf((t - float(fx.hold)) / maxf(float(fx.life) - float(fx.hold), 0.01), 0.0, 1.0)
	var w := (1.0 + 0.2 * sin(t * 70.0)) * (1.0 - 0.55 * fade)
	var b := Basis.looking_at(-d / L, Vector3.UP if absf(d.y / L) < 0.98 else Vector3.RIGHT)
	n.transform = Transform3D(Basis(b.x * w, b.y * w, b.z * L * grow), from)
	if fade > 0.0:
		_fade(n, fade)


func _sun_hit(tid: int, from: Vector3, to: Vector3, up: float, kind: int) -> void:
	var at := _robot_point(tid, up)
	if at == Vector3.INF:
		at = to
	var dir := (at - from).normalized() if at.distance_to(from) > 0.01 else Vector3.FORWARD
	var gl := clampi(Progress.gfx_level(), 0, 2)
	var n: int = [4, 3, 1][gl]
	if _fx_room(n + 1):
		var f := _mi(_fx_mesh("flash"), _atk_mat(["sun_flash", "sun_flash_white", "fire_flash"][kind]), self, at - dir * 0.1)
		f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		effects.append({"node": f, "t": 0.0, "life": 0.22, "kind": "flash", "s": [0.5, 0.7, 0.55][kind]})
		for k in n:
			var mo := _mi(_fx_mesh("mote"), _atk_mat("ember" if kind == 2 else "sun_glint"), self,
				at + Vector3(randf_range(-0.15, 0.15), randf_range(-0.1, 0.15), randf_range(-0.15, 0.15)))
			mo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			effects.append({"node": mo, "t": 0.0, "life": randf_range(0.35, 0.55), "kind": "glint", "s": randf_range(0.6, 1.0),
				"v": Vector3(randf_range(-0.7, 0.7), randf_range(0.9, 1.8), randf_range(-0.7, 0.7))})
	_land_hit(tid)


# ---------------------------------------------------------------- Kira Sunblade (v0.9.25)
# The whirlwind (tools/blender/hq/anim_kira.py): her khopesh sweeps round at arm's length and its cut crosses the front
# at HIT (ATTACK_FRAME.kira): a golden crescent slashes across each robot hit, with sparks and a flash. Solar Flare: she
# thrusts the sword at the sky (FLARE) and it blazes, a wave of sunlight rolls out over the ground, and each robot in
# reach bursts into flame as the wave reaches it (one the flare destroyed blows up then).
const KIRA_FLARE := 18                              # anim_kira.py FLARE
const KIRA_SKY := Vector3(-0.175, 2.582, 0.055)     # the raised blade at FLARE (model units, Godot axes, Yaw node)
const FLARE_SPEED := 11.0                           # world units per second the wave rolls out
const FLARE_R0 := 0.4                               # the wave's radius as it starts (under her dais)


## Calls `fn` on the frame unit `uid`'s clip `clip` reaches `at` (seconds of the clip's own time), so an effect keeps in
## step with the model whatever the game speed (changed mid-clip too) or a player that only starts moving the frame after
## it was told to play (one that had stopped at the end of its last clip). `left`: the game seconds that takes at the
## clip's rate; if the clip isn't playing (a showpiece took over, the model is gone) it goes when they have passed, and
## it never waits more than a frame and a half past them (a clip restarted or held still). Checked once a frame, from the
## effect timers (so it waits while the match is paused).
func _on_clip(uid: int, clip: String, at: float, left: float, fn: Callable, last := -1.0) -> void:
	var step := get_process_delta_time() * float(speed)
	left -= step
	var due := left <= 0.0
	var pos := -1.0
	var tn = tower_nodes.get(uid)
	if tn != null and is_instance_valid(tn) and (tn as Node3D).has_meta("anim"):
		var ap: AnimationPlayer = (tn as Node3D).get_meta("anim")
		if ap.is_playing() and ap.current_animation == clip:
			pos = ap.current_animation_position
			# (the player moves on after this, in this frame; its time, summed frame by frame, can land a hair short of a
			# frame it reaches: 14 x 1/30 + 1/30 < 0.5 put Forge Fury's first sparks a frame after the blow)
			due = pos + get_process_delta_time() * ap.speed_scale >= at - 0.001 or pos < last or left <= -maxf(0.1, 1.5 * step)
	if due:
		fn.call()
	else:
		_fx_after(0.0, func() -> void: _on_clip(uid, clip, at, left, fn, pos))


## A cut: a crescent ribbon in the XZ plane round the origin (radius 0.6, 150 degrees, its middle on -Z), thickest in
## its middle and tapering to points, its outer edge bright and its inner edge fading, brightest at its leading end.
func _slash_mesh() -> ArrayMesh:
	if _atk_cache.has("slash_mesh"):
		return _atk_cache["slash_mesh"]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 18
	var r := 0.6                                        # (0.46 x 0.085 read as a 2-3 px hairline at the game's zoom)
	var prev := []
	for i in n + 1:
		var u := float(i) / n
		var a := deg_to_rad(lerpf(-75.0, 75.0, u))
		var w := 0.17 * sin(PI * u)
		var d := Vector3(sin(a), 0.0, -cos(a))
		var lead := pow(u, 1.3)
		var o := [d * (r + w * 0.35), Color(1.0, 0.97, 0.8, lead)]
		var inn := [d * (r - w), Color(1.0, 0.68, 0.22, 0.0)]
		if i > 0:
			for v in [prev[0], prev[1], o, prev[1], inn, o]:
				st.set_color(v[1])
				st.add_vertex(v[0])
		prev = [o, inn]
	var m := st.commit()
	_atk_cache["slash_mesh"] = m
	return m


## The flare's wave: a flat ring on the ground (radius 1 at scale 1), its rim bright, fading inward.
func _wave_mesh() -> ArrayMesh:
	if _atk_cache.has("wave_mesh"):
		return _atk_cache["wave_mesh"]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 48
	for i in n:
		var a0 := TAU * i / n
		var a1 := TAU * (i + 1) / n
		var o0 := Vector3(cos(a0), 0.0, sin(a0))
		var o1 := Vector3(cos(a1), 0.0, sin(a1))
		var cr := Color(1.0, 0.9, 0.6, 0.9)
		var ci := Color(1.0, 0.6, 0.18, 0.0)
		for v in [[o0, cr], [o1, cr], [o0 * 0.78, ci], [o1, cr], [o1 * 0.78, ci], [o0 * 0.78, ci]]:
			st.set_color(v[1])
			st.add_vertex(v[0])
	var m := st.commit()
	_atk_cache["wave_mesh"] = m
	return m


func _kira_slash(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	var tn: Node3D = tower_nodes[uid]
	var clip := str(tn.get_meta("clip_attack", "Attack"))
	var rate := maxf(float(tn.get_meta("throw_rate", 1.0)), 0.01)
	var i := 0
	for tid in targets:
		var t := int(tid)
		if _robot_point(t, 0.0) == Vector3.INF:      # (gone already)
			continue
		# its cut lands as the clip reaches HIT (half a frame later for the second robot); the hit is held for as long
		# as that takes at 1x (the game speed may change before it lands)
		var at := (float(ATTACK_FRAME.kira) + 0.5 * i) / CLIP_FPS
		_hold_hit(t, at / rate + 0.02)
		_fx_after(0.0, func() -> void: _on_clip(uid, clip, at, at / rate, func() -> void: _kira_cut(uid, t)))
		i += 1


func _kira_cut(uid: int, tid: int) -> void:
	var h := _hit_height_of(_robot_type(tid))
	var at := _robot_point(tid, h)
	if at == Vector3.INF:
		_land_hit(tid)
		return
	var u = sim.get_unit(uid)
	var to_her := (_v3(u.pos, h) - at) if u != null else Vector3(0, 0, 1)
	to_her.y = 0.0
	to_her = to_her.normalized() if to_her.length() > 0.05 else Vector3(0, 0, 1)
	var gl := clampi(Progress.gfx_level(), 0, 2)
	var n: int = [4, 3, 1][gl]
	if _fx_room(n + 2):
		var sl := _mi(_slash_mesh(), _atk_mat("slash"), self, at + to_her * 0.1)
		sl.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# the crescent's middle (local -Z) toward her, tilted into a diagonal cut
		var b := Basis.looking_at(to_her, Vector3.UP) * Basis(Vector3(0, 0, 1), deg_to_rad(randf_range(-24.0, 24.0)))
		sl.basis = b
		effects.append({"node": sl, "t": 0.0, "life": 0.2, "kind": "slash", "b0": b})
		var f := _mi(_fx_mesh("flash"), _atk_mat("lance_flash"), self, at + to_her * 0.12)
		f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		effects.append({"node": f, "t": 0.0, "life": 0.14, "kind": "flash", "s": 0.5})
		for k in n:
			var sp := _mi(_fx_mesh("spark"), _atk_mat("arrow_spark"), self, at + to_her * 0.12)
			sp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var side := to_her.cross(Vector3.UP)
			var v := (side * randf_range(-1.0, 1.0) + to_her * 0.4 + Vector3(0, randf_range(0.3, 1.0), 0)).normalized() * randf_range(2.5, 4.5)
			sp.look_at_from_position(sp.position, sp.position + v, Vector3.UP if absf(v.normalized().y) < 0.95 else Vector3.RIGHT)
			effects.append({"node": sp, "t": 0.0, "life": 0.2, "kind": "spark", "v": v})
	_land_hit(tid, 0.04)


func _kira_flare(ev: Dictionary, hp: Vector3) -> void:
	var hid := int(sim.hero.id) if sim.hero != null else -1
	var R := float(ev.get("radius", 5.5))
	var at_flare := float(KIRA_FLARE) / CLIP_FPS
	var ids := []
	for tid in ev.get("ids", []):
		var t := int(tid)
		var at := _robot_point(t, 0.0)
		if at == Vector3.INF:
			continue
		# held for as long as the windup and the wave can take at 1x (the game speed may change before it lands)
		_hold_hit(t, at_flare + Vector2(at.x - hp.x, at.z - hp.z).length() / FLARE_SPEED)
		ids.append(t)
	_fx_after(0.0, func() -> void: _on_clip(hid, "Ability", at_flare, at_flare, func() -> void: _flare_burst(hid, hp, R, ids)))


## The raised blade blazes and the wave rolls out from her feet; each robot hit burns as the wave's rim reaches it.
func _flare_burst(hid: int, hp: Vector3, R: float, ids: Array) -> void:
	var sky := hp + Vector3(0, 2.2, 0)
	if tower_nodes.has(hid) and is_instance_valid(tower_nodes[hid]) and (tower_nodes[hid] as Node3D).has_meta("yaw"):
		sky = ((tower_nodes[hid] as Node3D).get_meta("yaw") as Node3D).global_transform * KIRA_SKY
	var spd := FLARE_SPEED * maxf(float(speed), 0.01)       # (the wave keeps this pace, whatever the speed does next)
	# the ability's own burst is always drawn (three nodes, once a cast): the effects cap only thins out the burns
	for s2 in [1.6, 0.9]:
		var f := _mi(_fx_mesh("flash"), _atk_mat("sun_flash_white" if s2 < 1.0 else "sun_flash"), self, sky)
		f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		effects.append({"node": f, "t": 0.0, "life": 0.45, "kind": "flash", "s": s2})
	var w := _mi(_wave_mesh(), _atk_mat("flare_wave"), self, Vector3(hp.x, 0.12, hp.z), Vector3.ZERO, Vector3(FLARE_R0, 1.0, FLARE_R0))
	w.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.append({"node": w, "t": 0.0, "life": R / spd + 0.15, "kind": "wave", "r": R, "speed": spd})
	for t in ids:
		var tid := int(t)
		var at := _robot_point(tid, 0.0)
		var d := Vector2(at.x - hp.x, at.z - hp.z).length() if at != Vector3.INF else 0.0
		_fx_after(maxf(d - FLARE_R0, 0.0) / spd, func() -> void: _flare_burn(tid))
	shake = maxf(shake, 0.6)


## The wave reaches a robot: it bursts into flame.
func _flare_burn(tid: int) -> void:
	var at := _robot_point(tid, _hit_height_of(_robot_type(tid)))
	if at != Vector3.INF:
		var gl := clampi(Progress.gfx_level(), 0, 2)
		var n: int = [3, 2, 1][gl]
		if _fx_room(n + 1):
			var f := _mi(_fx_mesh("flash"), _atk_mat("fire_flash"), self, at)
			f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			effects.append({"node": f, "t": 0.0, "life": 0.26, "kind": "flash", "s": 0.7})
			for k in n:
				var em := _mi(_fx_mesh("mote"), _atk_mat("ember"), self, at + Vector3(randf_range(-0.2, 0.2), randf_range(-0.2, 0.2), randf_range(-0.2, 0.2)))
				em.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				effects.append({"node": em, "t": 0.0, "life": randf_range(0.4, 0.6), "kind": "glint", "s": randf_range(0.7, 1.0),
					"v": Vector3(randf_range(-0.6, 0.6), randf_range(1.0, 1.8), randf_range(-0.6, 0.6))})
	_land_hit(tid, 0.08)


# ---------------------------------------------------------------- Javelin Thrower (v0.9.29)
# The throw (tools/blender/hq/anim_javelin.py): from the poised stance his arm whips over and the javelin leaves his hand
# on the clip frame where the one in his fist vanishes (its bone's scale, as Tarek's hammer). It flies point first in a
# shallow arc at the robot (following it as it walks), strikes sparks off it and sticks in it, quivering, a moment; the
# sim's hit waits for it (a robot it destroys blows up then). The Spear Hunter's (Path A) javelins are bigger.
const JAV_LEN := 1.2                                 # javelin.py JAV_FWD + JAV_BACK (model units)
const JAV_FWD := 0.74                                # its grip -> its point (model units)
const JAV_FLY := 1.15                                # the flying javelin's size (of the one in his hand)
var _javs := {}                                      # sim projectile id -> its flying javelin (an effect)


## Is this sim projectile a javelin from an HQ Javelin Thrower?
func _jav_hq(p: Dictionary) -> bool:
	var uid := int((p.get("src", {}) as Dictionary).get("tower_id", -1))
	var u = sim.get_unit(uid)
	if u == null or str(u.type) != "javelin_thrower":
		return false
	return _hq_clips(uid) and (tower_nodes[uid] as Node3D).has_meta("yaw")


## A javelin (one cached mesh, model units): an ash shaft, a leather binding, an iron butt cap and a long-socketed,
## leaf-shaped iron head. The point is at the origin and it lies along +Z, so a node looking along its flight carries it
## point first.
func _jav_mesh() -> ArrayMesh:
	if _atk_cache.has("jav_mesh"):
		return _atk_cache["jav_mesh"]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_smooth_group(-1)
	var w := 0.017
	_arrow_prism(st, 0.17, JAV_LEN - 0.035, w, Color(0.74, 0.58, 0.38))           # ash shaft
	_arrow_prism(st, 0.19, 0.25, w * 1.4, Color(0.36, 0.22, 0.12))                # leather binding below the head
	_arrow_prism(st, JAV_LEN - 0.04, JAV_LEN, w * 1.3, Color(0.32, 0.32, 0.34))   # iron butt cap
	st.generate_normals()
	var m := st.commit()
	var sm := StandardMaterial3D.new()
	sm.vertex_color_use_as_albedo = true
	sm.roughness = 0.75
	sm.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.surface_set_material(0, sm)
	var st2 := SurfaceTool.new()                       # the head: a flat leaf with a raised midrib on a long socket
	st2.begin(Mesh.PRIMITIVE_TRIANGLES)
	st2.set_smooth_group(-1)
	var back := Vector3(0, 0, 0.2)
	var ring := [Vector3(0.034, 0, 0.075), Vector3(0, 0.013, 0.068), Vector3(-0.034, 0, 0.075), Vector3(0, -0.013, 0.068)]
	for i in 4:
		var j := (i + 1) % 4
		for tri in [[Vector3.ZERO, ring[i], ring[j]], [ring[j], ring[i], back]]:
			for v in tri:
				st2.add_vertex(v)
	st2.generate_normals()
	st2.commit(m)
	var hm := StandardMaterial3D.new()
	hm.albedo_color = Color(0.64, 0.66, 0.7)
	hm.metallic = 0.75
	hm.roughness = 0.32
	hm.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.surface_set_material(1, hm)
	_atk_cache["jav_mesh"] = m
	return m


## The javelin in his fist (world): its grip, and its direction along the basis' Y (scaled with the model). Carried by
## his right hand, so it is right even while the javelin itself is scaled away.
func _jav_in_hand(tn: Node3D) -> Transform3D:
	if not tn.has_meta("jav_rel"):
		var sk := tn.find_child("Skeleton3D", true, false) as Skeleton3D
		var rel := Transform3D()
		var ok := sk != null and sk.find_bone("javelin") >= 0 and sk.find_bone("hand.R") >= 0
		if ok:
			rel = sk.get_bone_global_rest(sk.find_bone("hand.R")).affine_inverse() * sk.get_bone_global_rest(sk.find_bone("javelin"))
		tn.set_meta("jav_rel", rel)
		tn.set_meta("jav_sk", sk if ok else null)
	var sk2 = tn.get_meta("jav_sk")
	if sk2 == null or not is_instance_valid(sk2):
		return Transform3D(Basis(), tn.global_position + Vector3(0, 1.4, 0))
	var s: Skeleton3D = sk2
	return s.global_transform * s.get_bone_global_pose(s.find_bone("hand.R")) * (tn.get_meta("jav_rel") as Transform3D)


## How big the javelin in his fist is drawn now (its bone's scale: 0 while his clip has it thrown).
func _jav_fist(tn: Node3D) -> float:
	if not tn.has_meta("jav_sk"):
		_jav_in_hand(tn)
	var sk = tn.get_meta("jav_sk")
	if sk == null or not is_instance_valid(sk):
		return 0.0
	var s: Skeleton3D = sk
	return s.get_bone_pose_scale(s.find_bone("javelin")).x


func _jav_throw(p: Dictionary) -> void:
	var root := Node3D.new()
	add_child(root)
	var mi := _mi(_jav_mesh(), null, root)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.visible = false
	var tid := int(p.get("target", -1))
	var e = sim._enemy_by_id(tid)
	var h := _hit_height(e)
	var to := _robot_point(tid, h)
	var uid := int((p.get("src", {}) as Dictionary).get("tower_id", -1))
	var u = sim.get_unit(uid)
	var big := 1.3 if u != null and str(u.get("branch", "")) == "A" and int(u.get("level", 0)) >= 3 else 1.0
	var fx := {"node": root, "t": 0.0, "life": INF, "kind": "javelin", "pid": int(p.id), "tid": tid, "h": h, "uid": uid,
		"launched": false, "landed": false, "impact": {}, "ids": [], "t0": 0.0, "dur": 0.2, "from": Vector3.ZERO,
		"to": to if to != Vector3.INF else _v3(p.aim, h), "s": 0.7, "big": big}
	effects.append(fx)
	_javs[int(p.id)] = fx


## The javelin's flight: in his fist (hidden) until his clip throws the one in his fist (_jav_release), then point first
## at its robot (following it as it walks), as long as the sim's shot has left to fly (at least 0.1 s; the hit waits).
func _tick_javelin(fx: Dictionary, n: Node3D) -> void:
	if not bool(fx.launched):
		if not bool(fx.get("asked", false)):        # (judged once this frame's animation is applied)
			fx.asked = true
			_jav_release.call_deferred(fx)
		return
	if bool(fx.landed):
		if float(fx.t) - float(fx.t0) - float(fx.dur) > 0.5:
			_javs.erase(int(fx.pid))                    # (no hit came for it)
			fx.life = 0.0
		return
	var k := clampf((float(fx.t) - float(fx.t0)) / float(fx.dur), 0.0, 1.0)
	var live := _robot_point(int(fx.tid), float(fx.h))
	if live != Vector3.INF:
		fx.to = live
	_jav_pose(fx, n, k)
	if k >= 1.0:
		fx.landed = true
		if not (fx.impact as Dictionary).is_empty():
			_jav_strike(fx)
			fx.life = 0.0
		else:
			n.visible = false                           # (the sim's hit is a moment behind: _jav_impact strikes then)


## Where the flying javelin's point is at `k` of its flight: a shallow arc from `from` to `to`, the javelin along the
## arc (nose up as it leaves, nose down as it strikes).
func _jav_pose(fx: Dictionary, n: Node3D, k: float) -> void:
	var from: Vector3 = fx.from
	var to: Vector3 = fx.to
	var d := to - from
	var arc := 0.32 * minf(d.length() / 5.0, 1.0)
	n.position = from.lerp(to, k) + Vector3(0, arc * 4.0 * k * (1.0 - k), 0)
	var tg := d + Vector3(0, arc * 4.0 * (1.0 - 2.0 * k), 0)
	if tg.length() > 0.01:
		var tn := tg.normalized()
		n.basis = Basis.looking_at(tn, Vector3.UP if absf(tn.y) < 0.98 else Vector3.RIGHT).scaled(Vector3.ONE * float(fx.s))


## Deferred from _tick_javelin, so it runs after this frame's animation is applied: the javelin leaves his hand on the
## frame his clip hides the one in his fist and starts where that one's point is drawn. If his clip isn't the throw or
## 0.45 s have passed, it goes at once (see _tarek_release).
func _jav_release(fx: Dictionary) -> void:
	fx.asked = false
	if bool(fx.launched) or float(fx.life) <= 0.0 or not is_instance_valid(fx.node):
		return
	var n: Node3D = fx.node
	var uid := int(fx.uid)
	var go := float(fx.t) >= 0.45 / maxf(float(speed), 0.01)
	if _hq_clips(uid):
		var tn: Node3D = tower_nodes[uid]
		var ap: AnimationPlayer = tn.get_meta("anim")
		go = go or ap.current_animation != str(tn.get_meta("clip_attack")) or _jav_fist(tn) < 0.5
		if go:
			var hand := _jav_in_hand(tn)
			var ax := hand.basis.y
			fx.s = JAV_FLY * ax.length() * float(fx.big)
			fx.from = hand.origin + ax * JAV_FWD
	else:
		go = true
		fx.from = (fx.to as Vector3) + Vector3(0, 1.0, 0)
	if not go:
		return
	fx.launched = true
	fx.t0 = fx.t
	var rem := 0.0
	var sp = _proj_by_id(int(fx.pid))
	if sp != null:
		rem = ((sp.aim as Vector2) - (sp.pos as Vector2)).length() / maxf(float(sp.speed), 0.1) / maxf(float(speed), 0.01)
	fx.dur = maxf(rem, 0.1)
	n.visible = true
	_jav_pose(fx, n, 0.0)


## The sim's javelin hit: the robot takes it when the flying javelin gets there; at once if it is already there.
func _jav_impact(ev: Dictionary) -> void:
	var fx: Dictionary = _javs[int(ev.pid)]
	var eid := int(ev.get("eid", -1))
	fx.impact = ev
	fx.ids = [eid] if eid >= 0 else []
	if bool(fx.landed):
		_jav_strike(fx)
		fx.life = 0.0
		return
	var eta := float(fx.dur) - (float(fx.t) - float(fx.t0)) if bool(fx.launched) else 0.2 / maxf(float(speed), 0.01) + 0.1
	if eid >= 0:
		_hold_hit(eid, maxf(eta, 0.0) + 0.02)


## A javelin the sim threw and landed between two frames (10x, or a robot right at his feet): it strikes at once.
func _jav_unseen(ev: Dictionary) -> bool:
	var su = sim.get_unit(int(ev.get("tower", -1)))
	if su == null or str(su.type) != "javelin_thrower" or not _hq_clips(int(su.id)):
		return false
	var eid := int(ev.get("eid", -1))
	var h := _hit_height_of(_robot_type(eid))
	var live := _robot_point(eid, h) if eid >= 0 else Vector3.INF
	var s := JAV_FLY * float(defs.towers.javelin_thrower.get("model_scale", 0.64))
	_jav_strike({"pid": int(ev.pid), "from": _v3(su.pos, 1.3), "to": live if live != Vector3.INF else _v3(ev.pos, h), "impact": ev,
		"ids": [eid] if live != Vector3.INF else [], "s": s})
	return true


## The javelin strikes: sparks off the robot's plating and a clank, and it sticks in the robot (quivering, then it sinks
## away) or, when that robot is gone, in the ground; the hit lands.
func _jav_strike(fx: Dictionary) -> void:
	_javs.erase(int(fx.pid))
	var ev: Dictionary = fx.impact
	var eid := int(ev.get("eid", -1))
	var at: Vector3 = fx.to
	var dir: Vector3 = at - (fx.from as Vector3)
	dir = dir.normalized() if dir.length() > 0.01 else Vector3.FORWARD
	var s := float(fx.s)
	var gl := clampi(Progress.gfx_level(), 0, 2)
	var life: float = [1.2, 0.8, 0.0][gl]
	if eid >= 0 and enemy_nodes.has(eid) and is_instance_valid(enemy_nodes[eid]):
		var en: Node3D = enemy_nodes[eid]
		if life > 0.0 and int(en.get_meta("arrows", 0)) < 3 and not en.has_meta("emerge") and not en.has_meta("ghost") and _fx_room(1):
			var d := (dir + Vector3(randf_range(-0.08, 0.08), randf_range(-0.05, 0.05), randf_range(-0.08, 0.08))).normalized()
			var a := _mi(_jav_mesh(), null, en)
			a.global_transform = Transform3D(Basis.looking_at(d, Vector3.UP if absf(d.y) < 0.98 else Vector3.RIGHT).scaled(Vector3.ONE * s),
				at + d * 0.16 * s)
			a.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			en.set_meta("arrows", int(en.get_meta("arrows", 0)) + 1)
			effects.append({"node": a, "t": 0.0, "life": life, "kind": "stuck", "b0": a.transform.basis, "en": en})
	else:
		at.y = 0.0
		if life > 0.0 and _fx_room(1):
			var flat := Vector3(dir.x, 0.0, dir.z)
			flat = flat.normalized() if flat.length() > 0.01 else Vector3.FORWARD
			var gd := (flat * 0.6 + Vector3(0, -0.8, 0)).normalized()
			var g := _mi(_jav_mesh(), null, self)
			g.global_transform = Transform3D(Basis.looking_at(gd, Vector3.UP).scaled(Vector3.ONE * s), at + gd * 0.12 * s)
			g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			effects.append({"node": g, "t": 0.0, "life": life * 1.3, "kind": "stuck", "b0": g.transform.basis})
		_dust_fx(at + Vector3(0, 0.08, 0), 2, 0.3)
	var n: int = [5, 3, 2][gl]
	if _fx_room(n):
		for i in n:
			var sp := _mi(_fx_mesh("spark"), _atk_mat("arrow_spark"), self, at - dir * 0.1)
			sp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var v := (-dir + Vector3(randf_range(-0.9, 0.9), randf_range(0.3, 1.2), randf_range(-0.9, 0.9))).normalized() * randf_range(2.6, 4.8)
			sp.look_at_from_position(sp.position, sp.position + v, Vector3.UP if absf(v.normalized().y) < 0.95 else Vector3.RIGHT)
			effects.append({"node": sp, "t": 0.0, "life": 0.22, "kind": "spark", "v": v})
	_sfx("rock_hit", -11.0, 0.25, 0.05)
	for t in fx.get("ids", []):
		_land_hit(int(t), 0.0)


# ---------------------------------------------------------------- Tarek the Smith (v0.9.26)
# The throw (tools/blender/hq/anim_tarek.py): from the cocked stance his arm whips over and the red-hot hammer leaves his
# hand on the clip frame where the one in his fist vanishes (TAREK_THROW_T). It flies end over end at the robot, trailing
# embers, and strikes in a burst of sparks; the sim's hit waits for it (a robot it destroys blows up then).
# Forge Fury: he turns to his anvil and strikes the red-hot bar on it three times (sparks fountain up at each blow); the
# third sends a wave of heat over the field and every tower it reaches glows like a forge until the fury ends.
const TAREK_THROW_T := 0.1                          # anim_tarek.py RELEASE (frame 2 at 24 fps) on the importer's 30 Hz grid
const TAREK_HEAD := 0.42                            # the hammer's head: this far along its bone from his grip (tarek.py)
const TAREK_STRIKES := [12, 22, 36]                 # anim_tarek.py STRIKES (clip frames of the blows on the anvil)
const TAREK_AB_LEN := 66                            # anim_tarek.py AB_FR
const TAREK_TURN := 9.0 / CLIP_FPS                  # anim_tarek.py: squared up to the anvil by frame 9 of the Ability
const TAREK_ANVIL := Vector3(-0.495, 0.889, 0.523)  # the red-hot bar on his anvil (model units, Godot axes, model root)
const TAREK_ANVIL_DIR := Vector2(-0.7071, 0.7071)   # from where he stands to the anvil (world x, z: the model isn't turned)
const TAREK_FLY := 1.3                              # the flying hammer's size (of the one in his hand)
const FURY_SPEED := 14.0                            # world units per second the wave of heat rolls out
var _hammers := {}                                  # sim projectile id -> its flying hammer (an effect)


## Is this sim projectile a hammer from HQ Tarek?
func _tarek_hq(p: Dictionary) -> bool:
	var src: Dictionary = p.get("src", {})
	if not bool(src.get("hero", false)) or sim.hero == null or str(sim.hero.type) != "tarek":
		return false
	return _hq_clips(int(sim.hero.id)) and (tower_nodes[sim.hero.id] as Node3D).has_meta("yaw")


## The thrown hammer: an ash handle bound with red cord and a bronze head, its striking face red-hot and glowing.
## Its handle runs along +Y from the butt (-0.36) to the head (+0.12), the hot face toward -Z.
func _hammer_model(root: Node3D) -> void:
	if not _atk_cache.has("hammer_parts"):                 # (built once: five new meshes a throw before)
		_atk_cache["hammer_parts"] = [_cyl(0.022, 0.024, 0.46, 8), _cyl(0.027, 0.027, 0.12, 8), _box(0.1, 0.09, 0.16),
			_cyl(0.034, 0.046, 0.05, 8), _box(0.106, 0.096, 0.06)]
	var pm: Array = _atk_cache["hammer_parts"]
	for part in [[pm[0], "hammer_wood", Vector3(0, -0.13, 0), Vector3.ZERO],
			[pm[1], "hammer_cord", Vector3(0, -0.27, 0), Vector3.ZERO],
			[pm[2], "hammer_bronze", Vector3(0, 0.12, 0.03), Vector3.ZERO],
			[pm[3], "hammer_bronze", Vector3(0, 0.12, 0.13), Vector3(PI * 0.5, 0, 0)],
			[pm[4], "hammer_hot", Vector3(0, 0.12, -0.075), Vector3.ZERO]]:
		var mi := _mi(part[0], _atk_mat(part[1]), root, part[2], part[3])
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var glow := Node3D.new()
	glow.position = Vector3(0, 0.12, -0.08)
	root.add_child(glow)
	_fire_halo(glow, 0.45)


## Where the head of the hammer in his fist is now (world): carried by his right hand, so it is right even while the
## hammer itself is scaled away. The hand-to-head offset comes from the rest pose (bone +Y runs along the hammer).
func _tarek_head(tn: Node3D) -> Vector3:
	if not tn.has_meta("hammer_off"):
		var sk := tn.find_child("Skeleton3D", true, false) as Skeleton3D
		var off := Vector3.INF
		if sk != null and sk.find_bone("hammer") >= 0 and sk.find_bone("hand.R") >= 0:
			var hr := sk.get_bone_global_rest(sk.find_bone("hand.R"))
			var mr := sk.get_bone_global_rest(sk.find_bone("hammer"))
			off = hr.affine_inverse() * (mr.origin + mr.basis.y.normalized() * TAREK_HEAD)
		tn.set_meta("hammer_off", off)
		tn.set_meta("hammer_sk", sk)
	var off2: Vector3 = tn.get_meta("hammer_off")
	var sk2 := tn.get_meta("hammer_sk") as Skeleton3D
	if off2 == Vector3.INF or sk2 == null or not is_instance_valid(sk2):
		return tn.global_position + Vector3(0, 1.4, 0)
	return sk2.global_transform * (sk2.get_bone_global_pose(sk2.find_bone("hand.R")) * off2)


func _tarek_throw(p: Dictionary) -> void:
	var root := Node3D.new()
	add_child(root)
	_hammer_model(root)
	root.visible = false
	var tid := int(p.get("target", -1))
	var e = sim._enemy_by_id(tid)
	var h := _hit_height(e)
	var to := _robot_point(tid, h)
	var fx := {"node": root, "t": 0.0, "life": INF, "kind": "hammer", "pid": int(p.id), "tid": tid, "h": h,
		"hid": int(sim.hero.id), "launched": false, "landed": false, "impact": {}, "ids": [], "t0": 0.0, "dur": 0.2,
		"from": Vector3.ZERO, "to": to if to != Vector3.INF else _v3(p.aim, h), "s": TAREK_FLY * 0.7, "ember_t": 0.0}
	effects.append(fx)
	_hammers[int(p.id)] = fx


## The hammer's flight: in his fist (hidden) until the clip hides the one in his fist (_tarek_release), then end over end at
## its robot (following it as it walks), as long as the sim's shot has left to fly (at least 0.12 s; the hit waits for it).
func _tick_hammer(fx: Dictionary, n: Node3D) -> void:
	if not bool(fx.launched):
		if not bool(fx.get("asked", false)):        # (judged once this frame's animation is applied)
			fx.asked = true
			_tarek_release.call_deferred(fx)
		return
	if bool(fx.landed):
		if float(fx.t) - float(fx.t0) - float(fx.dur) > 0.5:
			_hammers.erase(int(fx.pid))                 # (no hit came for it)
			fx.life = 0.0
		return
	var k := clampf((float(fx.t) - float(fx.t0)) / float(fx.dur), 0.0, 1.0)
	var live := _robot_point(int(fx.tid), float(fx.h))
	if live != Vector3.INF:
		fx.to = live
	_hammer_pose(fx, n, k)
	_hammer_embers(fx, n)
	if k >= 1.0:
		fx.landed = true
		if not (fx.impact as Dictionary).is_empty():
			_hammer_strike(fx)
			fx.life = 0.0
		else:
			n.visible = false                           # (the sim's hit is a moment behind: _tarek_impact strikes then)


## Where the flying hammer is at `k` of its flight: an arc from `from` to `to`, head up and its hot face leading as it
## leaves, tumbling forward to strike head first.
func _hammer_pose(fx: Dictionary, n: Node3D, k: float) -> void:
	var from: Vector3 = fx.from
	var to: Vector3 = fx.to
	var d := to - from
	n.position = from.lerp(to, k) + Vector3(0, 0.4 * minf(d.length() / 4.0, 1.0) * 4.0 * k * (1.0 - k), 0)
	var fl := Vector3(d.x, 0.0, d.z)
	fl = fl.normalized() if fl.length() > 0.01 else Vector3(0, 0, 1)
	n.basis = (Basis.looking_at(fl, Vector3.UP) * Basis(Vector3.RIGHT, -TAU * 1.25 * k)).scaled(Vector3.ONE * float(fx.s))


## How big the hammer in his fist is drawn now (its bone's scale: 0 while his clip has it thrown).
func _tarek_fist(tn: Node3D) -> float:
	if not tn.has_meta("hammer_sk"):
		_tarek_head(tn)                                 # (finds his skeleton)
	var sk := tn.get_meta("hammer_sk") as Skeleton3D
	if sk == null or not is_instance_valid(sk) or sk.find_bone("hammer") < 0:
		return 0.0
	return sk.get_bone_pose_scale(sk.find_bone("hammer")).x


## Deferred from _tick_hammer, so it runs after this frame's animation is applied: the thrown hammer leaves his hand on
## the frame his clip hides the one in his fist (the `hammer` bone's scale key at RELEASE) and starts where that one's
## head is drawn this frame. Judged from the pose, not the clip's clock (TAREK_THROW_T): the pose read while the game
## runs is last frame's (the flying one started up to 0.7 behind it at 2x), a clip restarted after it had stopped holds
## its first pose a frame or two (two hammers at 3x), and a clip time summed frame by frame lands a hair short of the key
## (no hammer at all for a frame at 60 fps). If his clip isn't the throw (a showpiece took over) or 0.45 s have passed,
## it goes at once.
func _tarek_release(fx: Dictionary) -> void:
	fx.asked = false
	if bool(fx.launched) or float(fx.life) <= 0.0 or not is_instance_valid(fx.node):
		return
	var n: Node3D = fx.node
	var hid := int(fx.hid)
	var go := float(fx.t) >= 0.45 / maxf(float(speed), 0.01)             # (never later than this)
	if _hq_clips(hid):
		var tn: Node3D = tower_nodes[hid]
		var ap: AnimationPlayer = tn.get_meta("anim")
		if ap.is_playing() and ap.current_animation in ["Ability", "Cheer"]:
			_tarek_still(fx, n, tn)
			return
		go = go or ap.current_animation != str(tn.get_meta("clip_attack")) or _tarek_fist(tn) < 0.5
		if go:
			fx.s = TAREK_FLY * ((tn.get_meta("yaw") as Node3D).global_transform.basis.get_scale().x)
			# (its head, 0.12 up its handle from the node, where the one in his fist had its head)
			fx.from = _tarek_head(tn) - Vector3(0, 0.12 * float(fx.s), 0)
	else:
		go = true
		fx.from = (fx.to as Vector3) + Vector3(0, 1.2, 0)
	if not go:
		return
	fx.launched = true
	fx.t0 = fx.t
	var rem := 0.0
	var sp = _proj_by_id(int(fx.pid))
	if sp != null:
		rem = ((sp.aim as Vector2) - (sp.pos as Vector2)).length() / maxf(float(sp.speed), 0.1) / maxf(float(speed), 0.01)
	fx.dur = maxf(rem, 0.12)
	n.visible = true
	_hammer_pose(fx, n, 0.0)


## The hot head trails embers (FULL graphics).
func _hammer_embers(fx: Dictionary, n: Node3D) -> void:
	if Progress.gfx_level() > 0:
		return
	var acc: float = float(fx.ember_t) + get_process_delta_time()
	if acc < 0.03:
		fx.ember_t = acc
		return
	fx.ember_t = acc - 0.03
	if not _fx_room(1):
		return
	var at := n.global_transform * Vector3(randf_range(-0.04, 0.04), 0.12, randf_range(-0.1, -0.06))
	var em := _mi(_fx_mesh("mote"), _atk_mat("ember"), self, at, Vector3.ZERO, Vector3.ONE * randf_range(0.5, 0.85))
	em.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.append({"node": em, "t": 0.0, "life": randf_range(0.25, 0.4), "kind": "glint", "s": randf_range(0.6, 0.9),
		"v": Vector3(randf_range(-0.3, 0.3), randf_range(0.5, 1.2), randf_range(-0.3, 0.3))})


## A throw while a showpiece has his hammer (Forge Fury's blows on the anvil, a rank-up Cheer): the clip keeps the hammer
## in his fist, so none leaves it (one flew out of the very hammer he was striking the anvil with); the hit lands on the
## robot in a burst of sparks when the sim's does (_tarek_impact).
func _tarek_still(fx: Dictionary, n: Node3D, tn: Node3D) -> void:
	fx.launched = true
	fx.landed = true
	fx.still = true
	fx.t0 = fx.t
	fx.from = tn.global_position + Vector3(0, 1.2, 0)       # (its sparks fly back toward him)
	var sp = _proj_by_id(int(fx.pid))                       # (the wait for the sim's hit counts from when it lands)
	fx.dur = ((sp.aim as Vector2) - (sp.pos as Vector2)).length() / maxf(float(sp.speed), 0.1) / maxf(float(speed), 0.01) if sp != null else 0.0
	n.visible = false
	if not (fx.impact as Dictionary).is_empty():            # (the sim's hit came already)
		_tarek_impact(fx.impact)


## A hammer the sim threw and landed between two frames (10x, or a robot right at his feet) was never drawn flying: it
## strikes with its sparks and clang (it fell through to the generic shell burst and boulder thud).
func _tarek_unseen(ev: Dictionary) -> bool:
	if sim.hero == null or int(ev.get("tower", -1)) != int(sim.hero.id) or str(sim.hero.type) != "tarek" or not _hq_clips(int(sim.hero.id)):
		return false
	var eid := int(ev.get("eid", -1))
	var h := _hit_height_of(_robot_type(eid))
	var live := _robot_point(eid, h) if eid >= 0 else Vector3.INF
	_hammer_strike({"pid": int(ev.pid), "from": _v3(sim.hero.pos, 1.2), "to": live if live != Vector3.INF else _v3(ev.pos, h), "impact": ev,
		"ids": [eid] if live != Vector3.INF else []})
	return true


## The sim's hammer hit: the robots it hurt (and the ones its splash destroyed, held back) take it when the flying hammer
## gets there; at once if it is already there.
func _tarek_impact(ev: Dictionary) -> void:
	var fx: Dictionary = _hammers[int(ev.pid)]
	var ids := []
	var eid := int(ev.get("eid", -1))
	if eid >= 0:
		ids.append(eid)
	var sp := float(ev.get("splash", 0.0))
	if sp > 0.0:
		var at: Vector2 = ev.pos
		for e in sim.enemies:
			if e.alive and int(e.id) != eid and (e.pos as Vector2).distance_to(at) <= sp + 0.05:
				ids.append(int(e.id))
		for did in _doomed.keys():
			if int(did) != eid and not ids.has(int(did)) and (_doomed[did].pos as Vector2).distance_to(at) <= sp + 0.3:
				ids.append(int(did))
	fx.impact = ev
	fx.ids = ids
	if bool(fx.landed):
		if bool(fx.get("still", false)):                 # (not drawn flying: it strikes where the robot is now)
			var live := _robot_point(eid, float(fx.h)) if eid >= 0 else Vector3.INF
			fx.to = live if live != Vector3.INF else _v3(ev.pos, float(fx.h))
		_hammer_strike(fx)
		fx.life = 0.0
		return
	var eta := float(fx.dur) - (float(fx.t) - float(fx.t0)) if bool(fx.launched) else TAREK_THROW_T / maxf(float(speed), 0.01) + 0.12
	for t in ids:
		_hold_hit(int(t), maxf(eta, 0.0) + 0.02)


## The hammer strikes: a flash, a spray of sparks thrown back off the robot, embers, a clang; the hits land.
func _hammer_strike(fx: Dictionary) -> void:
	_hammers.erase(int(fx.pid))
	var at: Vector3 = fx.to
	var ev: Dictionary = fx.impact
	var gl := clampi(Progress.gfx_level(), 0, 2)
	var n: int = [9, 6, 3][gl]
	if _fx_room(n + 4):
		var f := _mi(_fx_mesh("flash"), _atk_mat("fire_flash"), self, at)
		f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		effects.append({"node": f, "t": 0.0, "life": 0.22, "kind": "flash", "s": 0.8})
		var back: Vector3 = (fx.from as Vector3) - at
		back.y = 0.0
		back = back.normalized() if back.length() > 0.05 else Vector3(0, 0, 1)
		for i in n:
			var sk := _mi(_fx_mesh("spark"), _atk_mat("hammer_spark"), self, at + back * 0.12)
			sk.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var v := (Vector3(randf_range(-1.0, 1.0), randf_range(0.2, 1.3), randf_range(-1.0, 1.0)) + back * 0.7).normalized() * randf_range(2.6, 5.0)
			sk.look_at_from_position(sk.position, sk.position + v, Vector3.UP if absf(v.normalized().y) < 0.95 else Vector3.RIGHT)
			effects.append({"node": sk, "t": 0.0, "life": randf_range(0.2, 0.34), "kind": "spark", "v": v})
		for i in [3, 2, 1][gl]:
			var em := _mi(_fx_mesh("mote"), _atk_mat("ember"), self, at + Vector3(randf_range(-0.15, 0.15), randf_range(-0.1, 0.15), randf_range(-0.15, 0.15)))
			em.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			effects.append({"node": em, "t": 0.0, "life": randf_range(0.4, 0.6), "kind": "glint", "s": randf_range(0.7, 1.0),
				"v": Vector3(randf_range(-0.6, 0.6), randf_range(1.0, 1.8), randf_range(-0.6, 0.6))})
	if not ev.is_empty() and float(ev.get("splash", 0.0)) > 0.0:
		_dust_fx(Vector3(at.x, 0.2, at.z), [4, 3, 2][gl], 0.5)
	_sfx("hammer_hit", -6.0, 0.12, 0.05)
	shake = maxf(shake, 0.12)
	for t in fx.ids:
		_land_hit(int(t), 0.06)


## Forge Fury: he turns to his anvil (the clip has it straight in front of him) and the three blows land on its clip
## frames; the third sends the wave of heat out.
func _tarek_fury() -> void:
	var hid := int(sim.hero.id)
	var tn: Node3D = tower_nodes[hid]
	# the turn follows his clip (_clip_face): squared up to the anvil as the clip squares his body up to it (TAREK_TURN)
	# and facing it while the clip plays, at any game speed and through a pause (a lock timed in real seconds ran out
	# mid-clip after a pause or a slow-down, and a turn at the fixed per-frame rate was still 59 degrees off at 3x)
	tn.set_meta("clip_face", ["Ability", (tn.get_meta("yaw") as Node3D).rotation.y, _yaw(TAREK_ANVIL_DIR), TAREK_TURN])
	for i in TAREK_STRIKES.size():
		var big: bool = i == TAREK_STRIKES.size() - 1
		var at := float(TAREK_STRIKES[i]) / CLIP_FPS
		# on the frame his clip reaches the blow, whatever the game speed does meanwhile (_on_clip)
		_fx_after(0.0, func() -> void: _on_clip(hid, "Ability", at, at, func() -> void: _anvil_strike(hid, big)))


## A unit turning with one of its clips (Tarek to his anvil in Forge Fury): from the yaw it had to the clip's own, done
## `turn` seconds into the clip by the clip's clock (so right at any game speed and through a pause); it lets go when the
## clip ends.
func _clip_face(tn: Node3D, yaw_node: Node3D) -> void:
	var cf: Array = tn.get_meta("clip_face")
	var ap: AnimationPlayer = tn.get_meta("anim") if tn.has_meta("anim") else null
	if ap == null or not ap.is_playing() or ap.current_animation != str(cf[0]):
		tn.remove_meta("clip_face")
		return
	yaw_node.rotation.y = lerp_angle(float(cf[1]), float(cf[2]), smoothstep(0.0, float(cf[3]), ap.current_animation_position))


## Where the red-hot bar on his anvil is (world).
func _tarek_anvil(tn: Node3D) -> Vector3:
	var model := (tn.get_meta("yaw") as Node3D).get_parent() as Node3D
	return model.global_transform * TAREK_ANVIL


## A blow on the anvil: a flash, a fountain of sparks, embers; the last one is twice the size and sends out the fury.
func _anvil_strike(hid: int, big: bool) -> void:
	if not tower_nodes.has(hid) or not is_instance_valid(tower_nodes[hid]) or not (tower_nodes[hid] as Node3D).has_meta("yaw"):
		return
	var at := _tarek_anvil(tower_nodes[hid])
	var gl := clampi(Progress.gfx_level(), 0, 2)
	var n: int = ([18, 11, 5] if big else [10, 6, 3])[gl]
	var ne: int = ([4, 3, 1] if big else [2, 1, 1])[gl]
	# the blow itself is always drawn (its flash and three sparks; three blows a cast): the effects cap dropped it whole
	# on a busy field and now only thins out the rest of the fountain
	while n > 3 and not _fx_room(n + ne + 1):
		n -= 1
	if not _fx_room(n + ne + 1):
		ne = 0
	var f := _mi(_fx_mesh("flash"), _atk_mat("fire_flash"), self, at)
	f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.append({"node": f, "t": 0.0, "life": 0.3 if big else 0.2, "kind": "flash", "s": 1.3 if big else 0.7})
	for i in n:
		var sk := _mi(_fx_mesh("spark"), _atk_mat("hammer_spark"), self, at)
		sk.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var a := randf() * TAU
		var v := Vector3(cos(a) * randf_range(0.6, 2.2), randf_range(2.4, 4.6) * (1.25 if big else 1.0), sin(a) * randf_range(0.6, 2.2))
		sk.look_at_from_position(sk.position, sk.position + v, Vector3.UP if absf(v.normalized().y) < 0.95 else Vector3.RIGHT)
		effects.append({"node": sk, "t": 0.0, "life": randf_range(0.3, 0.5), "kind": "spark", "v": v})
	for i in ne:
		var em := _mi(_fx_mesh("mote"), _atk_mat("ember"), self, at + Vector3(randf_range(-0.1, 0.1), 0.05, randf_range(-0.1, 0.1)))
		em.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		effects.append({"node": em, "t": 0.0, "life": randf_range(0.5, 0.8), "kind": "glint", "s": randf_range(0.7, 1.0),
			"v": Vector3(randf_range(-0.4, 0.4), randf_range(1.2, 2.0), randf_range(-0.4, 0.4))})
	_sfx("anvil", -3.0 if big else -7.0, 0.05, 0.05)
	shake = maxf(shake, 0.5 if big else 0.14)
	if big:
		_sfx("ab_forge_fury", -2.0, 0.0, 0.5)
		_fury_wave(at)


## The wave of heat rolls out over the whole field from the anvil; each tower glows as it reaches it.
func _fury_wave(at: Vector3) -> void:
	var spd := maxf(float(speed), 0.01)
	var R := 24.0
	for t in sim.towers:                                    # (out past the farthest tower: it glows as the wave gets there)
		R = maxf(R, Vector2(float(t.pos.x) - at.x, float(t.pos.y) - at.z).length() + 1.0)
	# always drawn (one node, once a cast; the effects cap dropped it on a busy field)
	var w := _mi(_wave_mesh(), _atk_mat("fury_wave"), self, Vector3(at.x, 0.12, at.z), Vector3.ZERO, Vector3(0.4, 1.0, 0.4))
	w.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.append({"node": w, "t": 0.0, "life": R / FURY_SPEED / spd + 0.15, "kind": "wave", "r": R, "speed": FURY_SPEED * spd})
	for t in sim.towers:
		var tid := int(t.id)
		var tp := _v3(t.pos, 0.0)
		_fx_after(Vector2(tp.x - at.x, tp.z - at.z).length() / FURY_SPEED / spd, func() -> void: _fury_glow(tid))


## A tower the wave reached glows like a forge (a hot ring round its feet, embers rising) until the fury ends.
func _fury_glow(tid: int) -> void:
	if not tower_nodes.has(tid) or not is_instance_valid(tower_nodes[tid]) or sim.tick >= sim.fury_until:
		return
	var tn: Node3D = tower_nodes[tid]
	if tn.has_meta("fury_fx"):
		return
	var t = sim.get_tower(tid)
	var r := 0.95
	if t != null:
		r = float(defs.footprints.get("towers", {}).get(str(t.type), 0.95)) if defs.has("footprints") else 0.95
	var g := _mi(_wave_mesh(), _atk_mat("fury_ring"), tn, Vector3(0, 0.08, 0), Vector3.ZERO, Vector3(r, 1.0, r))
	g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	tn.set_meta("fury_fx", true)
	effects.append({"node": g, "t": 0.0, "life": INF, "kind": "fury", "tid": tid, "r": r, "ember_t": randf() * 0.3})
	if _fx_room(3):
		var f := _mi(_fx_mesh("flash"), _atk_mat("fire_flash"), self, tn.global_position + Vector3(0, 0.5, 0))
		f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		effects.append({"node": f, "t": 0.0, "life": 0.25, "kind": "flash", "s": 0.8})


func _tick_fury(fx: Dictionary, n: Node3D) -> void:
	var tid := int(fx.tid)
	if sim.tick >= sim.fury_until or not tower_nodes.has(tid):
		if tower_nodes.has(tid) and is_instance_valid(tower_nodes[tid]):
			(tower_nodes[tid] as Node3D).remove_meta("fury_fx")
		fx.life = 0.0
		return
	var pz := 0.88 + 0.12 * sin(time_s * 6.0 + float(tid))
	n.scale = Vector3(float(fx.r) * pz, 1.0, float(fx.r) * pz)
	if Progress.gfx_level() > 0:
		return
	fx.ember_t = float(fx.ember_t) + get_process_delta_time()
	if float(fx.ember_t) < 0.3 or not _fx_room(1):
		return
	fx.ember_t = 0.0
	var a := randf() * TAU
	var at := n.global_position + Vector3(cos(a), 0.0, sin(a)) * float(fx.r) * randf_range(0.4, 0.9) + Vector3(0, 0.1, 0)
	var em := _mi(_fx_mesh("mote"), _atk_mat("ember"), self, at, Vector3.ZERO, Vector3.ONE * randf_range(0.5, 0.9))
	em.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.append({"node": em, "t": 0.0, "life": randf_range(0.6, 0.9), "kind": "glint", "s": randf_range(0.6, 0.9),
		"v": Vector3(randf_range(-0.2, 0.2), randf_range(0.8, 1.4), randf_range(-0.2, 0.2))})


# ---------------------------------------------------------------- Bronze Age robots (v0.9.27)
## The Shield Bot's shield breaks: its panel bursts into cyan shards that tumble down.
func _shield_shatter(n: Node3D) -> void:
	var spn: MeshInstance3D = n.get_meta("shield_panel")
	var at: Vector3 = spn.global_transform * Vector3.ZERO if is_instance_valid(spn) else n.position + Vector3(0, 0.8, 0)
	var k: int = [8, 5, 2][clampi(Progress.gfx_level(), 0, 2)]
	if not _fx_room(k):
		return
	for i in k:
		var sh := _mi(_fx_mesh("cube"), _atk_mat("shield_shard"), self, at + Vector3(randf_range(-0.2, 0.2), randf_range(-0.25, 0.25), randf_range(-0.1, 0.1)),
			Vector3(randf(), randf(), randf()) * 3.0, Vector3(randf_range(0.06, 0.12), randf_range(0.06, 0.14), 0.012))
		sh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		effects.append({"node": sh, "t": 0.0, "life": randf_range(0.4, 0.6), "kind": "debris", "s": 0.1,
			"v": Vector3(randf_range(-1.6, 1.6), randf_range(1.0, 2.6), randf_range(-1.6, 1.6))})


## A Repair Drone's heal pulse: its lens flashes, green motes lift off the robots round it.
func _drone_heal(did: int, radius: float) -> void:
	var dn: Node3D = enemy_nodes[did]
	var gl := clampi(Progress.gfx_level(), 0, 2)
	if _fx_room(2):
		var f := _mi(_fx_mesh("flash"), _atk_mat("heal_mote"), self, dn.position + Vector3(0, 0.55, 0))
		f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		effects.append({"node": f, "t": 0.0, "life": 0.3, "kind": "flash", "s": 0.7})
	var per: int = [3, 2, 0][gl]
	if per == 0:
		return
	var de = sim._enemy_by_id(did)
	if de == null:
		return
	var shown := 0
	for e in sim.enemies:
		if shown >= 6 or not _fx_room(per):
			break
		if e.alive and int(e.id) != did and (e.pos as Vector2).distance_to(de.pos) <= radius and enemy_nodes.has(e.id):
			shown += 1
			var base := (enemy_nodes[e.id] as Node3D).position
			for j in per:
				var m := _mi(_fx_mesh("mote"), _atk_mat("heal_mote"), self, base + Vector3(randf_range(-0.3, 0.3), randf_range(0.3, 1.0), randf_range(-0.3, 0.3)))
				m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				effects.append({"node": m, "t": 0.0, "life": randf_range(0.5, 0.8), "kind": "glint", "s": randf_range(0.6, 0.9),
					"v": Vector3(0, randf_range(0.8, 1.4), 0)})


## The Torsion Catapult (v0.9.23): its HQ engineer knocks out the trigger pin, the arm whips up and the shot leaves the
## cup at the top of the swing (ATTACK_FRAME): it flies from there in a high arc and lands when the sim's shot does.
## Path A throws burning pitch pots (riding on the balls in the cup and the heap too) that shatter where they land.
const TORSION_BALL := Vector3(0.301, 1.58, 0.354)  # the ball at the top of the arm's swing (model units, Godot axes, Yaw node)
const TORSION_BALL_R := 0.078                       # its radius (model units: torsion.py BALL_R)
const TORSION_FLY := 0.75                           # the shot's size in flight (of its 0.17 mesh)


func _torsion_proj(root: Node3D, p: Dictionary, u, dt: String) -> void:
	if dt == "fire":
		_mi(_pot_mesh(), _atk_mat("pot"), root)
		_fire_halo(root, 0.62)
		root.set_meta("hot", true)
		root.set_meta("pot", true)
		root.set_meta("fire", true)
	else:
		var bm := _mi(_sph_c(0.17, 14), _atk_mat("stone_ball"), root)
		bm.rotation = Vector3(0.4, 0.9, 0.2)
	root.set_meta("spin", true)
	root.set_meta("boulder", true)
	root.set_meta("lob_from", root.position)
	root.set_meta("lob_cap", float(p.flight) * 0.6)          # thrown by then at the latest (sim seconds into its flight)
	# it leaves the cup the size it was in it (the ball, or the pot riding on it at 0.56), and grows to its flight size
	root.set_meta("lob_size", 0.56 if dt == "fire" else TORSION_BALL_R / 0.17)
	if u != null and _hq_clips(int(u.id)) and (tower_nodes[u.id] as Node3D).has_meta("yaw"):
		root.set_meta("lob_tid", int(u.id))                  # in the cup until its clip reaches the release (_torsion_flight)
		root.visible = false
	else:
		root.set_meta("lob_delay", float(p.t))


## The cup empties at this clip time in the imported Attack clip: Blender frame 7 (0.292 s) lands on the importer's
## 30 Hz sample at 0.300 s.
const TORSION_THROW_T := 0.3


## Where a Torsion Catapult shot is this frame: still in the cup (hidden) until the swing throws it, then on its arc.
func _torsion_flight(pn: Node3D, p: Dictionary, alpha: float) -> Vector3:
	var t: float = float(p.t) + alpha * TICK
	if not pn.has_meta("lob_delay"):
		# still in the cup: it leaves on the frame the clip reaches the release (whatever the clip's rate, the game speed
		# or a pause), from where the cup is then (the engine turns toward its target as it swings)
		var tid := int(pn.get_meta("lob_tid", -1))
		var go := t >= float(pn.get_meta("lob_cap"))
		if _hq_clips(tid):
			var tn: Node3D = tower_nodes[tid]
			var ap: AnimationPlayer = tn.get_meta("anim")
			# (the clip moves on after this, in this frame: by the step _hq_anim_tick gives it)
			var step := get_process_delta_time() * float(speed) * float(tn.get_meta("throw_rate", 1.0))
			go = go or ap.current_animation != str(tn.get_meta("clip_attack")) \
				or ap.current_animation_position + step >= TORSION_THROW_T
			if go:
				var yt := (tn.get_meta("yaw") as Node3D).global_transform
				pn.set_meta("lob_from", yt * TORSION_BALL)
				pn.set_meta("s0", float(pn.get_meta("lob_size")) * yt.basis.get_scale().x)
				# the pot lay along the throw in the cup (the stone bone's +Y = the Yaw node's +Z): it leaves that way
				if pn.has_meta("pot"):
					pn.basis = yt.basis.orthonormalized() * Basis(Vector3.RIGHT, PI * 0.5)
		else:
			go = true                                        # (sold before the throw: it leaves now, in the sale's dust)
		if not go:
			pn.visible = false
			return pn.position
		pn.set_meta("lob_delay", t)
		pn.position = pn.get_meta("lob_from")
	var d0: float = pn.get_meta("lob_delay")
	var from: Vector3 = pn.get_meta("lob_from")
	pn.visible = true
	var k := clampf((t - d0) / maxf(float(p.flight) - d0, 0.05), 0.0, 1.0)
	pn.scale = Vector3.ONE * lerpf(float(pn.get_meta("s0", TORSION_FLY)), TORSION_FLY, smoothstep(0.0, 0.3, k))
	var to := _v3(p.aim, 0.2)
	var h := 2.4 * minf(from.distance_to(to) / 6.0, 1.0) + 0.7
	return from.lerp(to, k) + Vector3(0, h * 4.0 * k * (1.0 - k), 0)


## A pitch pot: a round-bellied jar of fired clay with black bands and a straw plug (vertex colours), radius ~0.17.
func _pot_mesh() -> ArrayMesh:
	if _atk_cache.has("pot_mesh"):
		return _atk_cache["pot_mesh"]
	# (two profile points inside each black band, so the band's own strip is painted)
	var prof := [Vector2(0.0, -0.15), Vector2(0.09, -0.145), Vector2(0.15, -0.08), Vector2(0.154, -0.064), Vector2(0.156, -0.056),
		Vector2(0.168, -0.01), Vector2(0.166, 0.0), Vector2(0.162, 0.02), Vector2(0.155, 0.06), Vector2(0.135, 0.082),
		Vector2(0.129, 0.088), Vector2(0.1, 0.12), Vector2(0.058, 0.15), Vector2(0.066, 0.175), Vector2(0.05, 0.19),
		Vector2(0.034, 0.215), Vector2(0.0, 0.225)]
	var nrm := []                                       # the profile's outward normals (radius, height)
	for i in prof.size():
		var tg: Vector2 = prof[mini(i + 1, prof.size() - 1)] - prof[maxi(i - 1, 0)]
		nrm.append(Vector2(tg.y, -tg.x).normalized())
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var seg := 14
	for i in prof.size() - 1:
		for j in seg:
			var q := [[i, TAU * j / seg], [i + 1, TAU * j / seg], [i + 1, TAU * (j + 1) / seg], [i, TAU * (j + 1) / seg]]
			for tri in [[0, 2, 1], [0, 3, 2]]:              # clockwise seen from outside (Godot's front faces)
				for k in tri:
					var ix: int = q[k][0]
					var an: float = q[k][1]
					var pr: Vector2 = prof[ix]
					var nr: Vector2 = nrm[ix]
					var col := Color(0.72, 0.37, 0.2)
					if absf(pr.y - 0.01) < 0.016 or absf(pr.y + 0.06) < 0.008 or absf(pr.y - 0.085) < 0.006:
						col = Color(0.12, 0.08, 0.06)
					elif pr.y > 0.18:
						col = Color(0.86, 0.72, 0.4)
					st.set_color(col)
					st.set_normal(Vector3(cos(an) * nr.x, nr.y, sin(an) * nr.x))
					st.add_vertex(Vector3(cos(an) * pr.x, pr.y, sin(an) * pr.x))
	var m := st.commit()
	_atk_cache["pot_mesh"] = m
	return m


## A pitch pot shatters: shards of fired clay fly (the fire and the crater come with them).
func _pot_shards(ground: Vector3) -> void:
	var n: int = [6, 4, 2][clampi(Progress.gfx_level(), 0, 2)]
	if not _fx_room(n):
		return
	for i in n:
		var sz := randf_range(0.07, 0.12)
		var c := _mi(_fx_mesh("cube"), _atk_mat("shard"), self, ground + Vector3(0, 0.3, 0), Vector3(randf(), randf(), randf()) * 3.0,
			Vector3(sz, sz * 0.3, sz * 0.8))
		c.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var a := randf() * TAU
		effects.append({"node": c, "t": 0.0, "life": randf_range(0.5, 0.75), "kind": "debris", "s": sz, "flat": true,
			"v": Vector3(cos(a) * randf_range(2.0, 3.5), randf_range(2.5, 4.5), sin(a) * randf_range(2.0, 3.5))})


## Path A's pitch pots in the HQ model: a pot rides on the ball in the cup and on the one he lifts from the heap (they
## share those bones, so it leaves with the shot and comes back when he loads).
func _torsion_ammo(n: Node3D, hot: bool) -> void:
	if not hot or n.has_meta("pots"):
		return
	var sks := n.find_children("*", "Skeleton3D", true, false)
	if sks.is_empty():
		return
	var sk := sks[0] as Skeleton3D
	var pots := []
	for bone in ["stone", "carry"]:
		if sk.find_bone(bone) < 0:
			continue
		var ba := BoneAttachment3D.new()
		ba.bone_name = bone
		sk.add_child(ba)
		_mi(_pot_mesh(), _atk_mat("pot"), ba, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * 0.56)
		pots.append(ba)
	n.set_meta("pots", pots)


func _make_projectile(p: Dictionary) -> Node3D:
	var src: Dictionary = p.src
	var u = sim.get_unit(int(src.get("tower_id", -1)))
	var utype: String = u.type if u != null else ""
	var dt: String = str(src.get("dtype", ""))
	var root := Node3D.new()
	root.position = _v3(p.pos, 1.3)
	add_child(root)
	var pj: String = str(src.get("proj", ""))
	if pj != "" and pj != "arrow" and pj != "rock":
		_proj_model(root, pj, dt)
		return root
	if utype == "bronze_archer" or pj == "arrow":
		_arrow_proj(root, p, u, dt)            # v0.9.21: a real arrow, loosed from the HQ archer's bow
		return root
	if utype == "torsion_catapult":
		_torsion_proj(root, p, u, dt)          # v0.9.23: a dressed stone ball (or a burning pitch pot) from the cup
		return root
	if utype == "tarek":
		_mi(_box(0.26, 0.16, 0.16), _mat("hot_hammer", Color(0.9, 0.45, 0.15), {"emit": Color(1, 0.4, 0.1), "emit_e": 1.2}), root)
		_mi(_box(0.05, 0.05, 0.3), _mat("wood_dark", Color(0.3, 0.17, 0.08)), root, Vector3(0, 0, 0.15))
		root.set_meta("spin", true)
		return root
	if utype == "boulder_catapult":
		# the HQ catapult's boulder: a smooth, slightly lumpy grey stone (the faceted ball looked cheap next to it);
		# Path A's burning boulder glows from inside, in a soft halo (it used to be a flat yellow hexagon)
		var hot := dt == "fire"
		var bmat := _mat("proj_boulder_fire", Color(0.22, 0.12, 0.08), {"rough": 0.9, "emit": Color(1.0, 0.3, 0.04), "emit_e": 0.5}) \
			if hot else _mat("proj_boulder", Color(0.56, 0.54, 0.5), {"rough": 0.95})
		var bm := _mi(_sph_c(0.21, 16), bmat, root)
		bm.scale = Vector3(1.08, 0.86, 0.97)
		bm.rotation = Vector3(0.4, 0.9, 0.2)
		if hot:
			_fire_halo(root, 0.7)
			root.set_meta("hot", true)
		root.set_meta("spin", true)
		root.set_meta("boulder", true)
		return root
	if utype == "rock_slinger" and float(src.get("splash", 0.0)) > 0.0:
		# Boulder Hurler (Path A): a heavy lumpy rock that smashes down like the catapult's (crater, dust, no ring)
		var rm := _mi(_sph_c(0.16, 12), _mat("proj_boulder", Color(0.56, 0.54, 0.5), {"rough": 0.95}), root)
		rm.scale = Vector3(1.1, 0.85, 0.95)
		root.set_meta("spin", true)
		root.set_meta("boulder", true)
		return root
	var size := 0.11
	var col := Color(0.6, 0.58, 0.55)
	var opts := {}
	if p.kind == "lob":
		size = 0.26
	if dt == "fire":
		col = Color(0.95, 0.42, 0.1)
		opts = {"emit": Color(1, 0.38, 0.05), "emit_e": 1.2}
		_fire_halo(root, size * 4.0)
	elif dt == "blunt" and p.kind == "homing":
		size = 0.17
	_mi(_sph_c(size, 12), _mat("proj_%s" % col.to_html(), col, opts), root)
	root.set_meta("spin", true)
	return root


## A soft additive glow round a burning shot (billboard, radial texture).
var _halo_mat: StandardMaterial3D
func _fire_halo(root: Node3D, s: float) -> void:
	if Progress.gfx_level() >= 2:
		return
	if _halo_mat == null:
		_halo_mat = StandardMaterial3D.new()
		_halo_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_halo_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		_halo_mat.billboard_keep_scale = true
		_halo_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_halo_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		_halo_mat.albedo_color = Color(1.0, 0.36, 0.06, 0.8)
		_halo_mat.albedo_texture = _mote_tex()
	var h := _mi(_fx_mesh("flash"), _halo_mat, root, Vector3.ZERO, Vector3.ZERO, Vector3.ONE * s)
	h.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


## Projectile looks for the later eras (src.proj): oriented ones get the "arrow" meta so they face their flight.
func _proj_model(root: Node3D, pj: String, dt: String) -> void:
	match pj:
		"javelin":
			_mi(_box(0.05, 0.05, 1.0), _mat("javelin", Color(0.5, 0.36, 0.2)), root)
			_mi(_cyl(0.0, 0.07, 0.2, 4), _mat("iron_tip", Color(0.42, 0.44, 0.48), {"metal": 0.6}), root, Vector3(0, 0, -0.58), Vector3(-PI * 0.5, 0, 0))
			root.set_meta("arrow", true)
		"bolt":
			var bm := _mat("bolt_fire", Color(1, 0.5, 0.1), {"emit": Color(1, 0.4, 0.05), "emit_e": 2.0}) if dt == "fire" else _mat("bolt", Color(0.35, 0.24, 0.14))
			_mi(_box(0.08, 0.08, 0.7), bm, root)
			_mi(_cyl(0.0, 0.1, 0.18, 4), _mat("iron_tip", Color(0.42, 0.44, 0.48), {"metal": 0.6}), root, Vector3(0, 0, -0.42), Vector3(-PI * 0.5, 0, 0))
			root.set_meta("arrow", true)
		"bullet":
			_mi(_box(0.05, 0.05, 0.45), _mat("tracer", Color(1, 0.9, 0.5), {"emit": Color(1, 0.8, 0.3), "emit_e": 3.0, "unshaded": true}), root)
			root.set_meta("arrow", true)
		"cannonball":
			_mi(_sph_c(0.2, 8), _mat("cannonball", Color(0.12, 0.12, 0.13), {"metal": 0.5, "rough": 0.4}), root)
		"shell":
			_mi(_cyl(0.1, 0.1, 0.32, 8), _mat("shell", Color(0.72, 0.6, 0.3), {"metal": 0.6}), root, Vector3.ZERO, Vector3(PI * 0.5, 0, 0))
			_mi(_cyl(0.0, 0.1, 0.14, 8), _mat("shell_tip", Color(0.35, 0.37, 0.38), {"metal": 0.5}), root, Vector3(0, 0, -0.22), Vector3(-PI * 0.5, 0, 0))
			root.set_meta("arrow", true)
		"missile":
			_mi(_cyl(0.07, 0.07, 0.6, 8), _mat("missile", Color(0.92, 0.92, 0.9)), root, Vector3.ZERO, Vector3(PI * 0.5, 0, 0))
			_mi(_cyl(0.0, 0.07, 0.16, 8), _mat("missile_tip", Color(0.85, 0.15, 0.1)), root, Vector3(0, 0, -0.38), Vector3(-PI * 0.5, 0, 0))
			_mi(_cyl(0.07, 0.0, 0.35, 6), _mat("exhaust", Color(1, 0.7, 0.2, 0.9), {"emit": Color(1, 0.55, 0.1), "emit_e": 3.0, "unshaded": true}), root,
				Vector3(0, 0, 0.45), Vector3(-PI * 0.5, 0, 0))
			root.set_meta("arrow", true)
		"laser":
			_mi(_box(0.07, 0.07, 1.1), _mat("laser_beam", Color(0.4, 1.0, 1.0), {"emit": Color(0.2, 0.9, 1.0), "emit_e": 4.0, "unshaded": true}), root)
			root.set_meta("arrow", true)
		"plasma":
			_mi(_sph_c(0.22, 10), _mat("plasma", Color(1.0, 0.4, 0.95), {"emit": Color(1.0, 0.3, 0.9), "emit_e": 4.0, "unshaded": true}), root)
			_mi(_sph_c(0.34, 10), _mat("plasma_glow", Color(1.0, 0.5, 1.0, 0.3), {"unshaded": true}), root)
		"arc":
			_mi(_sph_c(0.16, 8), _mat("arc_ball", Color(0.75, 0.9, 1.0), {"emit": Color(0.5, 0.8, 1.0), "emit_e": 4.0, "unshaded": true}), root)
			root.set_meta("spin", true)
		_:
			_mi(_sph_c(0.15, 6), _mat("proj_default", Color(0.6, 0.58, 0.55)), root)


## A jagged lightning line through the chain-hit robots.
## Crackling arc of energy jumping across the portal frame (world positions).
func _portal_arc(a: Vector3, b: Vector3) -> void:
	var m := _glow_mat("portal_arc", Color(0.75, 0.95, 1.0, 1.0))
	var pts := [a]
	for i in range(1, 4):
		var t := float(i) / 4.0
		pts.append(a.lerp(b, t) + Vector3(randf_range(-0.18, 0.18), randf_range(-0.18, 0.18), randf_range(-0.18, 0.18)))
	pts.append(b)
	for i in range(1, pts.size()):
		var p0: Vector3 = pts[i - 1]
		var p1: Vector3 = pts[i]
		var L := p0.distance_to(p1)
		if L < 0.01:
			continue
		var bolt := _mi(_box(0.05, 0.05, L), m, self, (p0 + p1) * 0.5)
		bolt.look_at((p0 + p1) * 0.5 + (p1 - p0), Vector3.UP if absf((p1 - p0).normalized().y) < 0.95 else Vector3.RIGHT)
		effects.append({"node": bolt, "t": 0.0, "life": 0.16, "kind": "portal_arc"})


func _chain_fx(pts: Array) -> void:
	var m := _mat("chain_bolt", Color(0.7, 0.95, 1.0), {"emit": Color(0.5, 0.85, 1.0), "emit_e": 4.0, "unshaded": true})
	for i in range(1, pts.size()):
		var a := _v3(pts[i - 1], 1.0)
		var b := _v3(pts[i], 1.0)
		var mid := (a + b) * 0.5 + Vector3(randf_range(-0.25, 0.25), randf_range(0.0, 0.4), randf_range(-0.25, 0.25))
		for seg in [[a, mid], [mid, b]]:
			var p0: Vector3 = seg[0]
			var p1: Vector3 = seg[1]
			var L := p0.distance_to(p1)
			if L < 0.01:
				continue
			var bolt := _mi(_box(0.06, 0.06, L), m, self, (p0 + p1) * 0.5)
			bolt.look_at((p0 + p1) * 0.5 + (p1 - p0), Vector3.UP if absf((p1 - p0).normalized().y) < 0.95 else Vector3.RIGHT)
			effects.append({"node": bolt, "t": 0.0, "life": 0.15, "kind": "flash", "s": 1.0})


## Earthquake (v0.9.20; was two big rings): cracks open round the hero and the quake rolls out across the map,
## bursting a spike (and dust) under every robot as it passes.
## Earthquake: the ground cracks round Mara and the quake rolls out across the map; spikes burst up round every robot
## (the nearest first) and each one is hit as the quake reaches it.
func _quake_fx(hp: Vector3, ids: Array) -> void:
	var ground := Vector3(hp.x, 0.0, hp.z)
	_ground_decal(ground, "crack", 3.2, 2.2)
	_ground_decal(ground, "crack", 2.0, 2.2, 0.08)
	var cap: int = [12, 8, 4][clampi(Progress.gfx_level(), 0, 2)]
	var hits := []
	for t in ids:
		var p := _robot_point(int(t), 0.0)
		if p != Vector3.INF:
			p.y = 0.0
			hits.append([p.distance_to(ground), p, int(t)])
	hits.sort_custom(func(a, b): return a[0] < b[0])
	var i := 0
	for h in hits:
		var d: float = float(h[0]) / 14.0                 # the quake rolls out at 14 units a second
		var p: Vector3 = h[1]
		var eid: int = h[2]
		_hold_hit(eid, d)
		if i < cap:
			_spike_cluster(p, d, eid, 1.1)
			i += 1
		else:
			_fx_after(d, func() -> void:
				_dust_fx(p + Vector3(0, 0.2, 0), 2, 0.6)
				_land_hit(eid))


func _ability_fx(ev: Dictionary) -> void:
	var hp := _v3(ev.pos, 0.3)
	var aname := str(sim.hero_def.ability.name).to_upper() + "!"
	match str(ev.get("type", "")):
		"rain":
			var i := 0
			var ids: Array = ev.get("ids", [])
			for p in ev.hits:
				var rid := int(ids[i]) if i < ids.size() else -1
				_boulder_drop_fx(_v3(p), i * 0.06, rid)
				if rid >= 0:
					_hold_hit(rid, i * 0.06 + 0.45)
				i += 1
			_banner(aname, Color(0.9, 0.8, 0.6))
			_sfx("ab_stone_rain" if _era_index() < 4 else "airstrike", 0.0, 0.0, 0.5)
			return
		"quake":
			_quake_fx(hp, ev.get("ids", []))
			shake = 1.4
			_banner(aname, Color(0.85, 0.6, 1.0))
			_sfx("ab_earthquake", 0.0, 0.0, 0.5)
			return
		"flare":
			if sim.hero != null and _hq_clips(sim.hero.id):
				_kira_flare(ev, hp)                         # v0.9.25: the raised sword blazes, a wave of sunlight rolls out
				_banner(aname, C_GOLD)
				# the sound swells to its peak 0.45 s in: start it so the peak lands on the burst
				var snd := "ab_solar_flare" if str(ev.ability) == "solar_flare" else "explosion"
				var hid := int(sim.hero.id)
				_fx_after(0.0, func() -> void: _on_clip(hid, "Ability", maxf(float(KIRA_FLARE) / CLIP_FPS - 0.45 * float(speed), 0.0),
					maxf(float(KIRA_FLARE) / CLIP_FPS - 0.45 * float(speed), 0.0), func() -> void: _sfx(snd, 0.0, 0.0, 0.5)))
				return
			_ring_fx(hp, float(ev.radius), Color(1, 0.6, 0.25), 0.7)
			_ring_fx(hp, float(ev.radius) * 0.6, Color(1, 0.9, 0.5), 0.5)
			var f := _mi(_sph(1.0, 12), _mat("flare", Color(1, 0.85, 0.4, 0.6), {"emit": Color(1, 0.8, 0.3), "emit_e": 3.0, "unshaded": true}), self, hp + Vector3(0, 1.0, 0))
			effects.append({"node": f, "t": 0.0, "life": 0.35, "kind": "flash", "s": 2.5})
			shake = 0.7
			_banner(aname, C_GOLD)
			_sfx("ab_solar_flare" if str(ev.ability) == "solar_flare" else "explosion", 0.0, 0.0, 0.5)
			return
		"fury":
			if sim.hero != null and str(sim.hero.type) == "tarek" and _hq_clips(sim.hero.id):
				_tarek_fury()                               # v0.9.26: three blows on the anvil, a wave of heat, glowing towers
				_banner(aname, Color(1, 0.6, 0.2))
				return
			for t in sim.towers:
				_ring_fx(_v3(t.pos, 0.3), 1.3, Color(1, 0.5, 0.15), 0.6)
			_banner(aname, Color(1, 0.6, 0.2))
			_sfx("ab_forge_fury", 0.0, 0.0, 0.5)
			return
		"strike":
			var beam_m := _mat("strike_beam", Color(1.0, 0.95, 0.7, 0.8), {"emit": Color(1.0, 0.85, 0.5), "emit_e": 4.0, "unshaded": true})
			for p in ev.hits:
				var at := _v3(p, 0.0)
				var beam := _mi(_cyl(0.35, 0.35, 14.0, 10), beam_m, self, at + Vector3(0, 7.0, 0))
				effects.append({"node": beam, "t": 0.0, "life": 0.35, "kind": "flash", "s": 1.0})
				_ring_fx(at + Vector3(0, 0.2, 0), 1.8, Color(1, 0.8, 0.4), 0.5)
				_debris_fx(at + Vector3(0, 0.5, 0), 6, true)
			shake = 1.2
			_banner(aname, Color(1, 0.85, 0.5))
			_sfx("airstrike", 0.0, 0.0, 0.5)
			return
		"freeze":
			_ring_fx(hp, 30.0, Color(0.6, 0.9, 1.0), 1.2)
			for p in ev.hits:
				_ring_fx(_v3(p, 0.3), 0.8, Color(0.75, 0.95, 1.0), 0.8)
			_banner(aname, Color(0.6, 0.9, 1.0))
			_sfx("freeze", 0.0, 0.0, 0.5)
			return
		"emp":
			_ring_fx(hp, float(ev.radius), Color(0.45, 0.85, 1.0), 0.7)
			_ring_fx(hp, float(ev.radius) * 0.55, Color(0.8, 0.95, 1.0), 0.5)
			for p in ev.hits:
				_chain_fx([ev.pos, p])
			shake = 0.8
			_banner(aname, Color(0.5, 0.85, 1.0))
			_sfx("emp", 0.0, 0.0, 0.5)
			return
	match str(ev.ability):
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
	if n.has_meta("anim"):
		var uu = sim.get_unit(id)
		var ap: AnimationPlayer = n.get_meta("anim")
		n.set_meta("last_fire", time_s)
		if ap.current_animation in ["Ability", "Cheer"] and ap.is_playing():
			return                      # let the showpiece finish; the shot still happens
		var cd: float = float(uu.stats.cooldown) if uu != null else 0.85
		var clip: String = n.get_meta("clip_attack")
		# play the whole attack between two shots (speed it up when the tower fires faster than the clip)
		n.set_meta("throw_rate", clampf(ap.get_animation(clip).length / maxf(cd, 0.1), 1.0, 3.0))
		n.set_meta("combat_hold", maxf(2.2, cd * 1.25 + 0.3))
		# (Tarek's throw cuts straight in from his Combat stance, its first pose: a cross-fade also kept Combat's own blend
		# in, still running from his last throw, and so that throw's end pose, a full-size fresh hammer in his fist, mixed
		# into the release for 0.2 s while the thrown one flew)
		ap.play(clip, 0.0 if uu != null and str(uu.type) == "tarek" else 0.05)
		ap.seek(0.0, true)
		ap.speed_scale = float(speed) * float(n.get_meta("throw_rate"))
		return
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


## HQ robot clips: the walk plays as fast as the robot really moves (slowed in mud, stopped when stunned, sped up with
## the game); a stunned robot shakes; a one-shot (the boss's Summon) plays through, then the loop resumes.
func _robot_anim_tick(n: Node3D, e: Dictionary, stunned: bool) -> void:
	var ap: AnimationPlayer = n.get_meta("anim")
	var model: Node3D = n.get_node("Model")
	var loop: String = n.get_meta("loop")
	if ap.current_animation == "" or not ap.is_playing():
		ap.play(loop, 0.2)
	var ws := float(defs.enemies[e.type].get("walk_speed", 0.0))
	if stunned:
		ap.speed_scale = 0.0
		model.rotation.z = sin(time_s * 40.0) * 0.1
		return
	model.rotation.z = 0.0
	if ap.current_animation != loop:         # a one-shot (the boss's Summon) plays at game speed, not at the gait's
		ap.speed_scale = float(speed)
		return
	if ws > 0.0 and loop == "Walk":
		var v: float = (e.pos as Vector2).distance_to(e.prev_pos) / Sim.TICK * float(speed)
		var g := lerpf(float(n.get_meta("gait", v)), v, 0.15)
		n.set_meta("gait", g)
		ap.speed_scale = clampf(g / ws, 0.15, 4.0)
	else:
		ap.speed_scale = float(speed)


func _sync_visuals(alpha: float) -> void:
	var gl_now := Progress.gfx_level()
	for did in _doomed:                          # a doomed robot (frozen, waiting for its hit) still flashes and is thrown up
		if not enemy_nodes.has(did):
			continue
		var dn: Node3D = enemy_nodes[did]
		_hit_flash(dn)
		if dn.has_meta("hop"):
			var dk := clampf((time_s - float(dn.get_meta("hop"))) / 0.34, 0.0, 1.0)
			dn.position.y = float(dn.get_meta("hop_y0", 0.0)) + float(dn.get_meta("hop_h", 0.3)) * sin(PI * dk)
	for e in sim.enemies:
		if not enemy_nodes.has(e.id) or not e.alive or _doomed.has(e.id):
			continue
		var n: Node3D = enemy_nodes[e.id]
		var p: Vector2 = e.prev_pos.lerp(e.pos, alpha)
		n.position = _v3(p)
		n.visible = not _tunnel_hides(e)
		if n.has_meta("emerge"):
			# grows out of the vortex over its first steps
			var ek := clampf((float(e.dist) - Sim.SPAWN_DIST) / 1.0, 0.0, 1.0)
			ek = ek * ek * (3.0 - 2.0 * ek)
			n.scale = Vector3.ONE * lerpf(0.05, 1.0, ek)
			n.position.y += (1.0 - ek) * 1.0
			if ek >= 1.0:
				n.remove_meta("emerge")
				n.scale = Vector3.ONE
		if n.has_meta("hop"):
			var hk := (time_s - float(n.get_meta("hop"))) / 0.34
			if hk >= 1.0 or hk < 0.0:
				n.remove_meta("hop")
			else:
				n.position.y += float(n.get_meta("hop_h", 0.3)) * sin(PI * hk)
		var dir := sim.dir_at(e.dist, e.pi)
		n.rotation.y = lerp_angle(n.rotation.y, _yaw(dir), 0.25)
		var stunned: bool = sim.tick < e.stun_until
		if n.has_meta("anim"):
			_robot_anim_tick(n, e, stunned)
		var slowed: bool = sim.tick < e.slow_until
		var rate: float = 0.0 if stunned else (5.0 if slowed else 10.0) * float(e.speed) / 1.8
		var ph: float = time_s * maxf(rate, 0.001) * 1.6 + e.id
		var swing: float = 0.0 if stunned else sin(ph) * 0.55
		for l in n.get_meta("legsA"):
			l.rotation.x = swing
		for l in n.get_meta("legsB"):
			l.rotation.x = -swing
		_spin_flicker(n, get_process_delta_time(), 0.0 if stunned else 24.0)
		_tar_coat(n, gl_now)
		_hit_flash(n)
		var body = n.get_meta("body")
		if body != null:
			var bob: float = absf(sin(ph)) * 0.05
			if e.type in ["scout", "carrier", "repair_drone"] or e.flying:
				bob = sin(time_s * 5.0 + e.id) * 0.08
			body.position.y = bob
			body.rotation.z = sin(time_s * 40.0) * 0.12 if stunned else 0.0
		var punch: float = n.get_meta("punch")
		if punch > 0.0:
			n.set_meta("punch", maxf(0.0, punch - 0.18))
			var model: Node3D = n.get_node("Model")
			var sc: float = float(defs.enemies[e.type].get("model_scale", 0.9)) * (1.0 + punch * 0.12)
			model.scale = Vector3(sc, sc * (1.0 - punch * 0.08), sc)
		if n.has_meta("shield_panel"):
			var spn: MeshInstance3D = n.get_meta("shield_panel")
			var held: bool = e.shield > 0.0
			if spn.visible != held:
				spn.visible = held
		var bubble: MeshInstance3D = n.get_node_or_null("Bubble")
		if bubble != null:
			bubble.visible = e.shield > 0.0
			if bubble.visible:
				var bmat := bubble.material_override as ShaderMaterial
				bmat.set_shader_parameter("strength", 0.45 + 0.55 * clampf(e.shield / maxf(e.max_shield, 1.0), 0.0, 1.0))
		if e.cloak:
			var want := 0.78 if sim.tick >= e.revealed_until else 0.0
			if float(n.get_meta("cloak_t", -1.0)) != want:
				n.set_meta("cloak_t", want)
				for sw in n.get_meta("ghost"):
					(sw[0] as MeshInstance3D).set_surface_override_material(int(sw[1]), sw[2] if want > 0.0 else null)
				for ol in n.get_meta("outlines", []):
					(ol as MeshInstance3D).visible = want <= 0.0 and Progress.gfx_level() < 2
		var burn: Node3D = n.get_node("Burn")
		burn.visible = sim.tick < e.burn_until
		if burn.visible:
			burn.scale = Vector3(1, 0.8 + 0.4 * absf(sin(time_s * 13.0 + e.id)), 1)
		var mark: Node3D = n.get_node("Mark")
		mark.visible = sim.tick < e.expose_until
		if mark.visible:
			mark.rotation.y = time_s * 3.0
		var bar: Node3D = n.get_node("Bar")
		if e.hp < e.max_hp and not attract and not _hide_bars:
			bar.visible = true
			bar.global_rotation = Vector3.ZERO     # don't swing around when the robot turns a corner
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
		if pn.has_meta("off"):
			newp = _arrow_flight(pn, p, alpha)
			if pn.has_meta("fire"):
				_arrow_embers(pn, newp.distance_to(pn.position), pdt)
		elif pn.has_meta("lob_from"):
			newp = _torsion_flight(pn, p, alpha)
			if pn.has_meta("fire") and pn.visible:
				_arrow_embers(pn, newp.distance_to(pn.position), pdt)
		elif p.kind == "lob":
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
			var fdir: Vector2 = t.facing
			if tn.has_meta("face_to") and time_s - float(tn.get_meta("face_t", -99.0)) < 2.5:
				fdir = tn.get_meta("face_to")           # a pulse unit faces what it's flinging at, then the camera again
			yaw_node.rotation.y = lerp_angle(yaw_node.rotation.y, _yaw(fdir), 0.2)
			if tn.has_meta("clip_face"):
				_clip_face(tn, yaw_node)
		_spin_flicker(tn, pdt, 0.0 if sim.tick < int(t.get("stun_until", 0)) else 9.0)
		if tn.has_meta("anim"):
			_hq_anim_tick(tn, sim.tick < int(t.get("stun_until", 0)))
		if tn.has_meta("orb"):
			var orb: Node3D = tn.get_meta("orb")
			orb.scale = orb.scale.lerp(Vector3.ONE * (1.0 + 0.1 * sin(time_s * 4.0)), 0.1)
		var zap: Node3D = tn.get_node_or_null("Zap")
		var emp_on: bool = sim.tick < int(t.get("stun_until", 0))
		if emp_on and zap == null:
			zap = Node3D.new()
			zap.name = "Zap"
			tn.add_child(zap)
			for k in 3:
				_mi(_box(0.05, 0.05, 0.7), _mat("zap_arc", Color(0.5, 0.85, 1.0), {"emit": Color(0.4, 0.8, 1.0), "emit_e": 3.0, "unshaded": true}),
					zap, Vector3(0, 1.0 + k * 0.35, 0), Vector3(0.3 * k, k * 1.2, 0.5))
		if zap != null:
			zap.visible = emp_on
			if emp_on:
				zap.rotation.y = time_s * 9.0
				zap.scale = Vector3.ONE * (0.8 + 0.3 * absf(sin(time_s * 23.0)))
		var buff: Sprite3D = tn.get_node("Buff")
		buff.visible = t.get("buffed", false) and not t.get("is_hero", false) and t.id == selected and buff.texture != null
		if buff.visible:
			buff.position.y = 2.3 + 0.06 * sin(time_s * 3.0)


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
		if _place_mode() == 2:
			# CONFIRM: the ghost follows the pointer until a spot is picked, then only while dragging it
			if _pc_pos == Vector2.INF or _pc_drag:
				var gp2 := _ground_point(event.position)
				_move_ghost(gp2)
				if _pc_drag:
					_pc_pos = gp2
		else:
			_move_ghost(_ground_point(event.position))
	elif event is InputEventMouseButton and not event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_pc_drag = false
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			_cancel_placing()
			_deselect()
			return
		if event.button_index != MOUSE_BUTTON_LEFT:
			return
		var gp := _ground_point(event.position)
		if placing != "" and _place_mode() == 2:
			_move_ghost(gp)
			_pc_pos = gp
			_pc_drag = true
			_sfx("click", -10.0)
			return
		if placing != "":
			_move_ghost(gp)
			_commit_place(gp)
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


## Workshop tech: every unlocked tower of this era makes all towers hit harder.
func _apply_tech() -> void:
	var full := 1.0 + float(Progress.workshop.get("tech_bonus", 0.0)) * 3.0
	sim.tech_mult = full if (test_mode or attract) else Progress.tech_mult(_era())
	for t in sim.towers:
		t.stats = sim._compute_stats(t)


func _tower_open(type: String) -> bool:
	return test_mode or attract or Progress.tower_unlocked(type)


## Shop buttons: price for unlocked towers, Scrap cost for locked ones.
func _refresh_shop() -> void:
	for type in shop_buttons:
		var b: Button = shop_buttons[type]
		var def: Dictionary = defs.towers[type]
		if _tower_open(type):
			b.text = "%s\n%d gold" % [def.name, sim.tower_cost(type)]
			b.self_modulate = Color.WHITE
		elif Progress.next_unlock(_era()) == type:
			b.text = "%s\nUNLOCK: %d scrap" % [def.name, Progress.tower_scrap_cost(type)]
			b.self_modulate = Color(0.55, 0.55, 0.6)
		else:
			b.text = "%s\nLOCKED" % def.name
			b.self_modulate = Color(0.4, 0.4, 0.45)
	if lbl_scrap != null:
		lbl_scrap.text = "SCRAP: %d    TECH: +%d%% DAMAGE" % [Progress.scrap(_era()), int(round((sim.tech_mult - 1.0) * 100))]
		lbl_scrap.visible = not test_mode


func _try_unlock(type: String) -> void:
	var cost := Progress.tower_scrap_cost(type)
	var nxt := Progress.next_unlock(_era())
	if nxt != type and nxt != "":
		_sfx("error", -4.0, 0.0)
		_toast("Unlock the %s first (towers unlock weakest to strongest)." % str(defs.towers[nxt].name), Color(1, 0.6, 0.45))
		toast_t = 3.5
		return
	if Progress.unlock_tower(type):
		_sfx("upgrade")
		_apply_tech()
		_toast("%s unlocked! All towers now +%d%% damage." % [str(defs.towers[type].name), int(round((sim.tech_mult - 1.0) * 100))], C_GOLD)
		_refresh_shop()
	else:
		_sfx("error", -4.0, 0.0)
		_toast("Needs %d scrap (you have %d). Play %s maps to earn scrap." % [cost, Progress.scrap(_era()), _era()], Color(1, 0.6, 0.45))
		toast_t = 3.5


func _begin_placing(type: String) -> void:
	if Time.get_ticks_msec() < _pd_block_until:
		return
	if type != HERO_PLACING and not _tower_open(type):
		_try_unlock(type)
		return
	_sfx("click", -6.0)
	_deselect()
	if placing == type:
		_cancel_placing()
		return
	var r := 0.0
	var foot := 0.0
	if type == HERO_PLACING:
		r = float(sim.hero_def.base.range)
		foot = sim.hero_footprint()
	else:
		if sim.gold < sim.tower_cost(type):
			_toast("Not enough gold", Color(1, 0.45, 0.4))
			_sfx("error", -4.0, 0.0)
			return
		r = float(defs.towers[type].base.range)
		foot = sim.footprint_of(type)
	placing = type
	for c in ghost.get_children():
		if c != ghost_range and c != ghost_foot:
			c.queue_free()
	ghost.add_child(_make_hero_visual(sim.hero_id) if type == HERO_PLACING else _make_tower_visual(type))
	ghost_range.scale = Vector3(r, 1, r)
	ghost_foot.scale = Vector3(foot, 1, foot)
	ghost.visible = true
	_pc_pos = Vector2.INF
	_pc_drag = false
	_move_ghost(Vector2(-1.0, 0.0))
	_update_shop_highlight()
	var nm := str(sim.hero_def.name) if type == HERO_PLACING else str(defs.towers[type].name)
	match _place_mode():
		1:
			if not _pd_active:
				_toast("Drag %s onto the map (or tap a spot)" % nm, C_TEXT)
		2:
			_toast("Tap a spot for %s, then BUILD" % nm, C_TEXT)
		_:
			_toast("Tap the map to place %s" % nm, C_TEXT)


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
	_pc_pos = Vector2.INF
	_pc_drag = false
	if _pc_bar != null:
		_pc_bar.visible = false
	_update_shop_highlight()


# ---------------------------------------------------------------- placement modes (Settings > Tower placement)
## 0 TAP:     tap a card, then tap the map. Builds right away.
## 1 DRAG:    drag a card onto the map and let go to build (a plain tap on the card falls back to TAP).
## 2 CONFIRM: tap a card, tap (or drag) a spot on the map; the ghost waits there with its range shown,
##            then BUILD builds and X cancels. Nothing is built by accident.
var _pd_type := ""             # DRAG: card the finger went down on
var _pd_start := Vector2.ZERO
var _pd_active := false
var _pd_block_until := 0       # ms: swallow the card's own "pressed" right after a drag ends on it
var _pc_pos := Vector2.INF     # CONFIRM: chosen spot
var _pc_drag := false
var _pc_bar: Control = null
var _pc_build: Button = null


func _place_mode() -> int:
	return clampi(int(Progress.setting("place_mode")), 0, 2)


## Lifts the dragged ghost above the finger on touch screens so the finger doesn't hide it.
func _drag_lift() -> Vector2:
	return Vector2(0, -90) if DisplayServer.is_touchscreen_available() else Vector2.ZERO


func _over_ui(pos: Vector2) -> bool:
	if hud_side != null and hud_side.is_visible_in_tree() and hud_side.get_global_rect().has_point(pos):
		return true
	if btn_pause != null and btn_pause.is_visible_in_tree() and btn_pause.get_global_rect().has_point(pos):
		return true
	return _pc_bar != null and _pc_bar.visible and _pc_bar.get_global_rect().has_point(pos)


## The tower (or hero) card under the pointer that can start a drag, else "".
func _card_at(pos: Vector2) -> String:
	if shop_box == null or not shop_box.is_visible_in_tree():
		return ""
	for type in shop_buttons:
		var b: Button = shop_buttons[type]
		if b.is_visible_in_tree() and b.get_global_rect().has_point(pos) and _tower_open(type) and sim.gold >= sim.tower_cost(type):
			# the "?" info button on the card keeps working
			for c in b.get_children():
				if c is Button and (c as Button).get_global_rect().has_point(pos):
					return ""
			return type
	if sim.hero == null and btn_hero != null and btn_hero.is_visible_in_tree() and btn_hero.get_global_rect().has_point(pos):
		return HERO_PLACING
	return ""


## Builds the current placement at gp. Returns true if it was built.
func _commit_place(gp: Vector2) -> bool:
	if placing == "" or gp == Vector2.INF:
		return false
	if placing == HERO_PLACING:
		var herr := sim.hero_placement_error(gp)
		if herr == "":
			sim.place_hero(gp)
			_cancel_placing()
			_handle_events()
			_select(sim.hero.id)
			return true
		_toast(herr, Color(1, 0.45, 0.4))
		_sfx("error", -4.0, 0.0)
		return false
	var err := sim.placement_error(placing, gp)
	if err == "":
		var id := sim.place_tower(placing, gp)
		_cancel_placing()
		_handle_events()
		_select(id)
		return true
	_toast(err, Color(1, 0.45, 0.4))
	_sfx("error", -4.0, 0.0)
	return false


## DRAG mode, seen in _input before the GUI: press on a card arms it, moving past a few pixels picks the
## tower up, letting go over the map builds it (over the sidebar cancels).
func _place_drag_input(event: InputEvent) -> bool:
	if not started or paused or _place_mode() != 1:
		return false
	if event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			_pd_type = _card_at(mb.position)
			_pd_start = mb.position
			_pd_active = false
			return _pd_type != ""        # no drag-scrolling the sidebar from a tower card
		if _pd_type == "":
			return false
		var was := _pd_active
		_pd_type = ""
		_pd_active = false
		if not was:
			return false                 # a plain tap: the card's own button handles it
		_pd_block_until = Time.get_ticks_msec() + 150
		if _over_ui(mb.position):
			_cancel_placing()
			_sfx("click", -10.0)
		else:
			var gp := _ground_point(mb.position + _drag_lift())
			_move_ghost(gp)
			if not _commit_place(gp):
				_cancel_placing()
		return true
	if event is InputEventMouseMotion and _pd_type != "":
		var mm := event as InputEventMouseMotion
		if not _pd_active and mm.position.distance_to(_pd_start) > 16.0:
			_pd_active = true
			_cancel_placing()
			_deselect()
			_begin_placing(_pd_type)
			if placing == "":
				_pd_type = ""
				_pd_active = false
				return false
		if _pd_active:
			var over := _over_ui(mm.position)
			ghost.visible = not over
			if not over:
				_move_ghost(_ground_point(mm.position + _drag_lift()))
			return true
	return false


## CONFIRM mode: the floating BUILD / X bar over the waiting ghost.
func _build_confirm_bar() -> void:
	_pc_bar = HBoxContainer.new()
	_pc_bar.add_theme_constant_override("separation", 14)
	_pc_bar.visible = false
	_pc_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_pc_build = _button("BUILD", Color(0.2, 0.62, 0.25), 30)
	_pc_build.custom_minimum_size = Vector2(150, 72)
	_pc_build.pressed.connect(func():
		if _pc_pos != Vector2.INF:
			_commit_place(_pc_pos))
	var x := _button("X", Color(0.75, 0.2, 0.18), 30)
	x.custom_minimum_size = Vector2(72, 72)
	x.pressed.connect(func():
		_sfx("click", -6.0)
		_cancel_placing())
	_pc_bar.add_child(_pc_build)
	_pc_bar.add_child(x)
	ui_root.add_child(_pc_bar)


func _confirm_bar_tick() -> void:
	if _pc_bar == null:
		return
	var show := started and not paused and detail_open == 0 and placing != "" and _place_mode() == 2 and _pc_pos != Vector2.INF
	_pc_bar.visible = show
	if not show:
		return
	var err := sim.hero_placement_error(_pc_pos) if placing == HERO_PLACING else sim.placement_error(placing, _pc_pos)
	_pc_build.modulate = Color.WHITE if err == "" else Color(1, 0.55, 0.55)
	_pc_build.text = "BUILD" if err == "" else "CAN'T"
	var sp := cam.unproject_position(_v3(_pc_pos, 2.4))
	var vp := get_viewport().get_visible_rect().size
	var sz := _pc_bar.get_combined_minimum_size()
	var side_w := hud_side.get_global_rect().size.x if hud_side != null else 0.0
	_pc_bar.size = sz
	_pc_bar.global_position = Vector2(clampf(sp.x - sz.x * 0.5, 8.0, vp.x - side_w - sz.x - 8.0), clampf(sp.y - sz.y - 30.0, 90.0, vp.y - sz.y - 8.0))


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
	if not started or Time.get_ticks_msec() < _pd_block_until:
		return
	if sim.hero == null:
		_begin_placing(HERO_PLACING)
	elif sim.ability_ready():
		sim.use_ability()
		_handle_events()
	elif not sim.ability_unlocked():
		_toast("%s unlocks at rank %d (your hero ranks up during the match)" % [sim.hero_def.ability.name, int(sim.hero_def.ability.get("unlock", 3))], C_TEXT)
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
	var dis := _style(Color(0.19, 0.24, 0.32), 18, Color(0.13, 0.16, 0.22), 4)
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
	b.add_theme_color_override("font_outline_color", Color(0.02, 0.04, 0.1, 0.9))
	b.add_theme_constant_override("outline_size", _outline_for(font))
	if "autowrap_mode" in b:
		b.set("autowrap_mode", TextServer.AUTOWRAP_WORD_SMART)
	return b


## Every label gets a dark outline thick enough to read over anything (outline 0 = deliberately none,
## e.g. dark text on a bright badge). Smaller numbers are raised to a floor that scales with the font.
func _label(text: String, size := 28, col := C_TEXT, outline := 9) -> Label:
	size = _fs(size)
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color(0.02, 0.04, 0.1, 1.0))
	l.add_theme_constant_override("outline_size", 0 if outline == 0 else maxi(outline, _outline_for(size)))
	return l


func _outline_for(font_px: int) -> int:
	return clampi(int(round(float(font_px) * 0.3)), 6, 18)


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
	for tn in ["Label", "Button", "CheckBox", "CheckButton", "OptionButton", "LinkButton", "LineEdit", "RichTextLabel", "MenuButton"]:
		ui_theme.set_color("font_outline_color", tn, Color(0.02, 0.04, 0.1, 0.95))     # outlined text everywhere
		ui_theme.set_constant("outline_size", tn, 8)
	for sbn in ["VScrollBar", "HScrollBar"]:          # no scroll bars anywhere: areas scroll by drag or wheel
		for k in ["scroll", "scroll_focus", "grabber", "grabber_highlight", "grabber_pressed"]:
			ui_theme.set_stylebox(k, sbn, StyleBoxEmpty.new())
	var layer := CanvasLayer.new()
	add_child(layer)
	var root := Control.new()
	root.theme = ui_theme
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS     # rendered UI art is shown well below its size
	layer.add_child(root)
	ui_root = root

	# --- top-left stat bar
	var top := PanelContainer.new()
	hud_top = top
	top.add_theme_stylebox_override("panel", _style(Color(0.06, 0.09, 0.15, 0.82), 22, C_PANEL_EDGE, 4))
	top.position = Vector2(20, 16)
	root.add_child(top)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 14)
	top.add_child(hb)
	hb.add_child(_icon(ICON_GOLD))
	lbl_gold = _label("", 40, C_COIN)
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
	btn_pause = _button("II", Color(0.18, 0.25, 0.37), 34)
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
	hud_side = side
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
	var era := _label(_era().to_upper() + "  -  " + str(map.name) + ("   T%d" % Progress.timeline() if Progress.timeline() > 1 else ""), 22, C_GOLD)
	era.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	era.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	era.custom_minimum_size.x = 10
	col.add_child(era)

	# hero card
	hero_card = PanelContainer.new()
	hero_card.add_theme_stylebox_override("panel", _style(Color(0.1, 0.16, 0.26), 16, C_GOLD.darkened(0.3), 3))
	col.add_child(hero_card)
	var hrow := HBoxContainer.new()
	hrow.add_theme_constant_override("separation", 10)
	hero_card.add_child(hrow)
	hrow.add_child(_icon(_face_tex(sim.hero_id), 72))
	var hcol := VBoxContainer.new()
	hcol.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hcol.add_theme_constant_override("separation", 2)
	hrow.add_child(hcol)
	lbl_hero_name = _label(_short_name(str(sim.hero_def.name)), 22, C_GOLD, 6)
	lbl_hero_name.clip_text = true
	hcol.add_child(lbl_hero_name)
	lbl_hero_level = _label("", 18, C_TEXT, 5)
	hcol.add_child(lbl_hero_level)
	var xp_bg := ColorRect.new()
	xp_bg.color = Color(0.04, 0.06, 0.1)
	xp_bg.custom_minimum_size = Vector2(130, 10)
	hcol.add_child(xp_bg)
	hero_xp_fill = ColorRect.new()
	hero_xp_fill.color = C_GOLD
	hero_xp_fill.size = Vector2(0, 10)
	xp_bg.add_child(hero_xp_fill)
	btn_hero = _button("", Color(0.2, 0.55, 0.2), 16)
	btn_hero.custom_minimum_size = Vector2(136, 72)
	btn_hero.clip_text = true
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
	lbl_scrap = _label("", 22, Color(0.75, 0.85, 0.95), 6)
	lbl_scrap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	shop_box.add_child(lbl_scrap)
	var types := sim.tower_types()
	for i in types.size():
		var type: String = types[i]
		var def: Dictionary = defs.towers[type]
		var c := Color(def.color[0], def.color[1], def.color[2])
		var b := _button("", c.lerp(Color(0.17, 0.27, 0.45), 0.35), 26)
		b.set_meta("col", c.lerp(Color(0.1, 0.16, 0.3), 0.45))
		b.icon = _icon_tex(type)
		b.expand_icon = true
		b.add_theme_constant_override("icon_max_width", 92)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(0, 112)
		b.tooltip_text = "%s  [%d]\n%s" % [def.lineage, i + 1, def.desc]
		b.pressed.connect(_begin_placing.bind(type))
		shop_box.add_child(b)
		shop_buttons[type] = b
		var info := _button("?", Color(0.3, 0.36, 0.5), 26)
		info.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
		info.offset_left = -64
		info.offset_right = -10
		info.offset_top = -27
		info.offset_bottom = 27
		info.pressed.connect(func():
			_sfx("click")
			_tower_detail(type))
		b.add_child(info)
	_refresh_shop()

	tower_box = VBoxContainer.new()
	tower_box.add_theme_constant_override("separation", 8)
	tower_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tower_box.visible = false
	mid.add_child(tower_box)
	var head := HBoxContainer.new()
	tower_box.add_child(head)
	tower_icon = _icon(_icon_tex(types[0]), 66)
	head.add_child(tower_icon)
	lbl_t_name = _label("", 27, Color(1, 0.88, 0.55))
	lbl_t_name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_t_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_t_name.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	head.add_child(lbl_t_name)
	var close := _button("X", Color(0.2, 0.28, 0.43), 26)
	close.custom_minimum_size = Vector2(60, 60)
	close.pressed.connect(func():
		_sfx("click", -6.0)
		_deselect())
	head.add_child(close)
	lbl_t_info = _label("", 21, Color(0.84, 0.88, 0.93), 6)
	lbl_t_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tower_box.add_child(lbl_t_info)
	up_box = VBoxContainer.new()
	up_box.add_theme_constant_override("separation", 8)
	tower_box.add_child(up_box)
	tower_box.move_child(up_box, 1)        # upgrades first, stats underneath
	tower_actions = VBoxContainer.new()
	tower_actions.add_theme_constant_override("separation", 8)
	tower_actions.visible = false
	col.add_child(tower_actions)
	var act_row := HBoxContainer.new()          # TARGET and DETAILS share a row, so the upgrades get the room
	act_row.add_theme_constant_override("separation", 8)
	tower_actions.add_child(act_row)
	btn_target = _button("", Color(0.3, 0.3, 0.42), 22)
	btn_target.custom_minimum_size = Vector2(0, 56)
	btn_target.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_target.tooltip_text = "First: closest to your base. Strong: toughest robot (use for bosses). Close: nearest. Last: furthest back."
	btn_target.pressed.connect(func():
		if selected != -1:
			sim.cycle_target(selected)
			_sfx("click", -6.0)
			_show_tower_panel(selected))
	act_row.add_child(btn_target)
	btn_details = _button("DETAILS", Color(0.3, 0.36, 0.5), 22)
	btn_details.custom_minimum_size = Vector2(150, 56)
	btn_details.pressed.connect(func():
		var tt = sim.get_unit(selected) if selected != -1 else null
		if tt != null and not tt.get("is_hero", false):
			_sfx("click")
			_tower_detail(str(tt.type))
		elif tt != null:
			_sfx("click")
			_hero_detail(sim.hero_id, VBoxContainer.new()))
	act_row.add_child(btn_details)
	btn_sell = _button("", Color(0.62, 0.22, 0.16), 24)
	btn_sell.custom_minimum_size = Vector2(0, 58)
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

	# --- end-of-match results (a sequence of pages, built when the match ends)
	overlay = _modal(root)
	_on_close(overlay, func():
		_sfx("click")
		if results_page < results_pages.size() - 1:   # mid-rewards: skip ahead to "What next?" instead of leaving
			results_page = results_pages.size() - 1
			_show_results_page()
			return
		Progress.current_map = ""
		Progress.open_map_select = false
		get_tree().reload_current_scene())
	overlay.visible = false

	# --- main menu (title): the newest era plays itself in the background
	_build_map_select(root)
	_build_main_menu(root)

	_build_pause_menu(root)
	settings_panel = _modal(root, 0.5)
	settings_panel.visible = false
	legacy_panel = _modal(root, 0.6)
	legacy_panel.set_meta("full_h", true)
	legacy_panel.visible = false


# =================================================================== main menu, workshop, heroes
## The newest map the player has unlocked: it plays itself behind the main menu.
func _menu_map() -> String:
	var best := "mammoth_valley"
	for mid in map_order:
		if Progress.is_unlocked(mid):
			best = mid
	return best


## Next map to play: the first unlocked map not beaten yet in this timeline, else the newest one.
func _continue_map() -> String:
	for mid in map_order:
		if Progress.is_unlocked(mid) and not mid in Progress.data.get("cleared", []):
			return mid
	return _menu_map()


func _map_entry(mid: String) -> Dictionary:
	for m in Defs.map_list():
		if str(m.id) == mid:
			return m
	return {}


func _start_attract() -> void:
	attract = true
	_apply_tech()
	sim.lives = 999999
	_demo_build(30000)
	_frame_camera()
	if music != null:
		music.play()


func _attract_tick() -> void:
	if not attract or started:
		return
	if sim.can_start_wave() and sim.enemies.is_empty():
		if sim.wave >= sim.total_waves - 2:
			sim.wave = 2       # loop the mid-game waves forever; never reach the victory screen
		sim.start_wave()


func _menu_button(text: String, col: Color, cb: Callable, h := 78, font := 30) -> Button:
	var b := _button(text, col, font)
	b.custom_minimum_size = Vector2(0, h)
	b.pressed.connect(func():
		_sfx("click")
		cb.call())
	return b


# ---------------------------------------------------------------- main menu art (v0.9.18)
# Buttons are gold medallions: a shader-drawn enamel disc (any colour, glossy dome, a shine that sweeps across now and
# then), the 3D icon (it may pop out over the rim), the rendered gold rim on top, and a plaque for the label. The art is
# rendered in Blender (tools/blender/ui/menu_art.py -> assets/ui/mm_*.png).
const MEDALLION_SHADER := """
shader_type canvas_item;
uniform vec4 c_top : source_color = vec4(0.45, 0.78, 1.0, 1.0);
uniform vec4 c_bot : source_color = vec4(0.1, 0.3, 0.7, 1.0);
uniform float phase = 0.0;
uniform float period = 5.0;
uniform float glow = 0.0;
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float aa = fwidth(r) * 1.5;
	float a = 1.0 - smoothstep(1.0 - aa, 1.0, r);
	vec3 c = mix(c_top.rgb, c_bot.rgb, smoothstep(-0.95, 0.95, p.y));
	float ang = atan(p.y, p.x);
	c *= 1.0 + 0.07 * sin(ang * 14.0) * (1.0 - r);
	c *= 1.0 - 0.38 * smoothstep(0.62, 1.0, r) * (0.55 + 0.45 * smoothstep(-0.2, -1.0, p.y));
	c += c_top.rgb * 0.35 * smoothstep(0.55, 0.98, r) * smoothstep(0.2, 0.95, p.y);
	vec2 hp = (p - vec2(0.0, -0.48)) / vec2(0.74, 0.4);
	c = mix(c, vec3(1.0), (1.0 - smoothstep(0.5, 1.0, length(hp))) * 0.3);
	float t = fract(TIME / period + phase);
	float s = (p.x * 0.8 + p.y * 0.6) - (t * 9.0 - 4.5);
	c += vec3(1.0) * exp(-s * s * 14.0) * 0.32;
	c += c_top.rgb * glow * (1.0 - r) * 0.5;
	COLOR = vec4(c, a);
}
"""
const MASK_SHADER := """
shader_type canvas_item;
uniform float radius = 0.5;
void fragment() {
	vec4 t = texture(TEXTURE, UV);
	float r = length(UV - 0.5);
	float aa = fwidth(r) * 1.5;
	t.a *= 1.0 - smoothstep(radius - aa, radius, r);
	COLOR = t;
}
"""
const FILL_SHADER := """
shader_type canvas_item;
uniform vec4 c_top : source_color = vec4(0.55, 0.9, 1.0, 1.0);
uniform vec4 c_bot : source_color = vec4(0.12, 0.45, 0.95, 1.0);
uniform vec2 size_px = vec2(200.0, 22.0);
void fragment() {
	vec3 c = mix(c_top.rgb, c_bot.rgb, smoothstep(0.1, 0.95, UV.y));
	c = mix(c, vec3(1.0), (1.0 - smoothstep(0.08, 0.42, UV.y)) * 0.45);
	float t = fract(TIME * 0.35);
	float s = UV.x - (t * 1.6 - 0.3);
	c += vec3(1.0) * exp(-s * s * 220.0) * 0.35;
	// capsule mask (rounded ends), anti-aliased
	vec2 p = UV * size_px;
	float r = size_px.y * 0.5;
	vec2 q = vec2(clamp(p.x, r, size_px.x - r), r);
	float d = length(p - q) - r;
	COLOR = vec4(c, 1.0 - smoothstep(-1.0, 0.5, d));
}
"""
var _shaders := {}


func _shader_mat(code: String) -> ShaderMaterial:
	if not _shaders.has(code):
		var sh := Shader.new()
		sh.code = code
		_shaders[code] = sh
	var m := ShaderMaterial.new()
	m.shader = _shaders[code]
	return m


## A rendered 9-patch shown smaller than its texture: the patch is laid out at texture scale and scaled down as a whole,
## so the rounded ends and corners shrink with it instead of overflowing. margins: [left, top, right, bottom] in
## texture pixels; k = screen pixels per texture pixel.
func _nine(path: String, margins: Array, size: Vector2, k: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size = size
	c.size = size
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var np := NinePatchRect.new()
	np.texture = _res(path)
	np.patch_margin_left = int(margins[0])
	np.patch_margin_top = int(margins[1])
	np.patch_margin_right = int(margins[2])
	np.patch_margin_bottom = int(margins[3])
	np.size = size / k
	np.scale = Vector2(k, k)
	np.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.add_child(np)
	c.resized.connect(func(): np.size = c.size / k)
	return c


## A label on the gold-framed navy plaque (stretches to the text).
func _plaque(text: String, font_size: int, min_w := 0.0) -> Control:
	var h := font_size * 1.75
	var w := maxf(min_w, FONT.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x + font_size * 1.7)
	var pq := _nine("res://assets/ui/mm_plaque.png", [76, 0, 76, 0], Vector2(w, h), h / 160.0)
	var l := _label(text, font_size, Color(1, 0.97, 0.9), maxi(6, font_size / 4))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.set_anchors_preset(Control.PRESET_FULL_RECT)
	l.offset_top = -3
	pq.add_child(l)
	pq.set_meta("label", l)
	return pq




## A menu medallion button. opts: icon_frac (icon size / medallion), icon_dy (shift, fraction of size; negative pops the
## icon up over the rim), face (mask the icon to the disc, for portraits), badge (a red "!" gem), rim (texture),
## phase (shine timing), label_size, sub (a second line under the plaque), play (sunburst and glow behind it).
func _medallion(icon: Texture2D, text: String, c_top: Color, c_bot: Color, size: float, cb: Callable, opts := {}) -> Control:
	var label_size: int = int(opts.get("label_size", int(size * 0.19)))
	var plaque_h := label_size * 1.75 if text != "" else 0.0
	var root := Control.new()
	root.custom_minimum_size = Vector2(size, size + plaque_h * 0.62 + (label_size * 1.1 if opts.has("sub") else 0.0))
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var body := Control.new()
	body.size = Vector2(size, size)
	body.pivot_offset = Vector2(size, size) * 0.5
	body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(body)
	if opts.get("play", false):
		var rays := TextureRect.new()
		rays.texture = _res("res://assets/ui/mm_rays.png")
		rays.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		rays.size = Vector2(size, size) * 1.9
		rays.position = Vector2(size, size) * -0.45
		rays.pivot_offset = rays.size * 0.5
		rays.mouse_filter = Control.MOUSE_FILTER_IGNORE
		rays.modulate = Color(1, 1, 1, 0.85)
		body.add_child(rays)
		var rt := rays.create_tween().set_loops()
		rt.tween_property(rays, "rotation", TAU, 24.0).from(0.0)
	# soft drop shadow
	var sh := TextureRect.new()
	var gt := GradientTexture2D.new()
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.5)
	gt.fill_to = Vector2(1.0, 0.5)
	var gr := Gradient.new()
	gr.set_color(0, Color(0, 0, 0, 0.55))
	gr.set_color(1, Color(0, 0, 0, 0.0))
	gt.gradient = gr
	sh.texture = gt
	sh.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	sh.size = Vector2(size * 1.12, size * 1.12)
	sh.position = Vector2(-size * 0.06, size * 0.02)
	sh.mouse_filter = Control.MOUSE_FILTER_IGNORE
	body.add_child(sh)
	# enamel disc (inside the rim)
	var disc := ColorRect.new()
	var dm := _shader_mat(MEDALLION_SHADER)
	dm.set_shader_parameter("c_top", c_top)
	dm.set_shader_parameter("c_bot", c_bot)
	dm.set_shader_parameter("phase", float(opts.get("phase", randf())))
	disc.material = dm
	var inset := size * 0.1
	disc.position = Vector2(inset, inset)
	disc.size = Vector2(size - 2 * inset, size - 2 * inset)
	disc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	body.add_child(disc)
	root.set_meta("disc", dm)
	# icon
	if icon != null:
		var ic := TextureRect.new()
		ic.texture = icon
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		var isz: float = size * float(opts.get("icon_frac", 0.62))
		ic.size = Vector2(isz, isz)
		ic.position = Vector2((size - isz) * 0.5, (size - isz) * 0.5 + size * float(opts.get("icon_dy", 0.0)))
		ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
		if opts.get("face", false):
			var mm := _shader_mat(MASK_SHADER)
			mm.set_shader_parameter("radius", 0.5 * (size - 2 * inset) / isz)
			ic.material = mm
			ic.position = Vector2((size - isz) * 0.5, (size - isz) * 0.5 + size * float(opts.get("icon_dy", 0.0)))
		var rim_first: bool = not opts.get("face", false) and float(opts.get("icon_dy", 0.0)) < -0.01
		if not rim_first:
			body.add_child(ic)
		var rim := TextureRect.new()
		rim.texture = _res(str(opts.get("rim", "res://assets/ui/mm_rim.png")))
		rim.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		rim.size = Vector2(size, size)
		rim.mouse_filter = Control.MOUSE_FILTER_IGNORE
		body.add_child(rim)
		if rim_first:
			body.add_child(ic)              # pops out over the rim
		root.set_meta("icon", ic)
	if opts.get("badge", false):
		var bd := TextureRect.new()
		bd.texture = _res("res://assets/ui/mm_badge.png")
		bd.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		bd.size = Vector2(size, size) * 0.3
		bd.position = Vector2(size * 0.74, -size * 0.02)
		bd.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var bl := _label("!", int(size * 0.2), Color.WHITE, 6)
		bl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		bl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		bl.set_anchors_preset(Control.PRESET_FULL_RECT)
		bl.offset_top = -2
		bd.add_child(bl)
		body.add_child(bd)
		var bt := bd.create_tween().set_loops()
		bt.tween_property(bd, "position:y", -size * 0.08, 0.45).set_trans(Tween.TRANS_SINE)
		bt.tween_property(bd, "position:y", -size * 0.02, 0.45).set_trans(Tween.TRANS_SINE)
	# the label plaque, overlapping the bottom of the rim
	if text != "":
		var pq := _plaque(text, label_size, size * 0.72)
		pq.position = Vector2((size - pq.size.x) * 0.5, size - plaque_h * 0.38)
		root.add_child(pq)
		root.set_meta("plaque", pq)
		if opts.has("sub"):
			var sl := _label(str(opts.sub), int(label_size * 0.62), Color(0.88, 1.0, 0.82), 7)
			sl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			sl.size = Vector2(size * 1.6, label_size)
			sl.position = Vector2(-size * 0.3, size - plaque_h * 0.38 + plaque_h + 2)
			root.add_child(sl)
	# input: an invisible button over the disc
	var b := Button.new()
	for st in ["normal", "hover", "pressed", "focus", "disabled", "hover_pressed"]:
		b.add_theme_stylebox_override(st, StyleBoxEmpty.new())
	b.size = Vector2(size, size + plaque_h * 0.62)
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	root.add_child(b)
	root.set_meta("button", b)
	b.mouse_entered.connect(func():
		body.create_tween().tween_property(body, "scale", Vector2.ONE * 1.06, 0.14).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT))
	b.mouse_exited.connect(func():
		body.create_tween().tween_property(body, "scale", Vector2.ONE, 0.14))
	b.button_down.connect(func():
		body.create_tween().tween_property(body, "scale", Vector2.ONE * 0.9, 0.06))
	b.button_up.connect(func():
		body.create_tween().tween_property(body, "scale", Vector2.ONE, 0.22).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT))
	b.pressed.connect(func():
		_sfx("click")
		cb.call())
	# idle: a gentle float, each button on its own beat
	var ph := float(opts.get("phase", randf()))
	var fl := body.create_tween().set_loops()
	fl.tween_interval(ph * 1.2)
	fl.tween_property(body, "position:y", -size * 0.025, 1.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	fl.tween_property(body, "position:y", size * 0.012, 1.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	return root


## Scrap of an age: the same salvage pile, recoloured, with one piece of that age.
const SCRAP_KEYS := {"Stone Age": "stone", "Bronze Age": "bronze", "Iron Age": "iron", "Classical Age": "classical",
	"Medieval Age": "medieval", "Gunpowder Age": "gunpowder", "Industrial Age": "industrial", "Modern Age": "modern",
	"Digital Age": "digital", "The Data Center": "datacenter"}
func _scrap_tex(era: String) -> Texture2D:
	var path := "res://assets/ui/scrap_%s.png" % str(SCRAP_KEYS.get(era, "stone"))
	return _res(path if ResourceLoader.exists(path) else "res://assets/ui/icon_scrap.png") as Texture2D


## Currency in a gold-framed glass pill: the icon pops out on the left, a green gem "+" on the right.
func _currency_pill(icon: Texture2D, text: String, col: Color, plus_cb := Callable()) -> Control:
	var root := Control.new()
	root.custom_minimum_size = Vector2(310, 70)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var np := _nine("res://assets/ui/mm_pill.png", [64, 0, 64, 0], Vector2(288, 62), 62.0 / 128.0)
	np.position = Vector2(22, 5)
	root.add_child(np)
	var ic := TextureRect.new()
	ic.texture = icon
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.size = Vector2(84, 84)
	ic.position = Vector2(-8, -6)
	ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(ic)
	var l := _label(text, 34, col, 8)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.position = Vector2(84, 6)
	l.size = Vector2(150, 58)
	root.add_child(l)
	if plus_cb.is_valid():
		var pb := TextureButton.new()
		pb.texture_normal = _res("res://assets/ui/mm_plus.png")
		pb.ignore_texture_size = true
		pb.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
		pb.size = Vector2(60, 60)
		pb.position = Vector2(250, 6)
		pb.pivot_offset = Vector2(30, 30)
		pb.pressed.connect(func():
			_sfx("click")
			var tw := pb.create_tween()
			tw.tween_property(pb, "scale", Vector2.ONE * 0.85, 0.05)
			tw.tween_property(pb, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			plus_cb.call())
		root.add_child(pb)
	return root


func _build_main_menu(root: Control) -> void:
	title_screen = Control.new()
	title_screen.set_anchors_preset(Control.PRESET_FULL_RECT)
	title_screen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(title_screen)
	# dark bands top and bottom so the UI reads over the living 3D hub
	for top in [true, false]:
		var gt := GradientTexture2D.new()
		var gr := Gradient.new()
		gr.set_color(0, Color(0.04, 0.02, 0.06, 0.78))
		gr.set_color(1, Color(0.04, 0.02, 0.06, 0.0))
		gt.gradient = gr
		gt.fill_from = Vector2(0, 0) if top else Vector2(0, 1)
		gt.fill_to = Vector2(0, 1) if top else Vector2(0, 0)
		var tr := TextureRect.new()
		tr.texture = gt
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_SCALE
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		tr.anchor_right = 1.0
		if top:
			tr.offset_bottom = 230
		else:
			tr.anchor_top = 1.0
			tr.anchor_bottom = 1.0
			tr.offset_top = -330
		title_screen.add_child(tr)
	var era_now := str(_map_entry(_menu_map()).get("era", "Stone Age"))
	var hid := Progress.hero()
	if not defs.heroes.heroes.has(hid):
		hid = "ugo"
	var hcol: Color = _hero_color(hid)
	# ---- top left: profile (hero portrait medallion, level star, XP bar, name)
	var prof := Control.new()
	prof.position = Vector2(18, 12)
	prof.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(prof)
	var pr := Progress.hero_level_progress(hid)
	var hmax := Progress.hero_level(hid) >= int(Progress.workshop.hero_levels.max)
	var xbar := _nine("res://assets/ui/mm_xpbar.png", [48, 0, 48, 0], Vector2(352, 56), 56.0 / 96.0)
	xbar.position = Vector2(116, 26)
	prof.add_child(xbar)
	var fill_w := 352.0 - 2.0 * 30.0
	var frac := 1.0 if hmax else clampf(float(pr[0]) / maxf(float(pr[1]), 1.0), 0.0, 1.0)
	if frac > 0.0:
		var fill := ColorRect.new()        # rounded glossy fill inside the groove
		var fm := _shader_mat(FILL_SHADER)
		fill.material = fm
		fill.position = Vector2(146, 43)
		fill.size = Vector2(maxf(fill_w * frac, 24.0), 22)
		fm.set_shader_parameter("size_px", fill.size)
		fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
		prof.add_child(fill)
	var xpl := _label("MAX LEVEL" if hmax else "%d / %d XP" % [pr[0], pr[1]], 23, Color.WHITE, 8)
	xpl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	xpl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	xpl.position = Vector2(146, 26)
	xpl.size = Vector2(fill_w, 54)
	prof.add_child(xpl)
	var who := _short_name(str(defs.heroes.heroes[hid].name)).to_upper() + "  -  HERO LEVEL" + ("   -   TIMELINE %d" % Progress.timeline() if Progress.timeline() > 1 else "")
	var whol := _label(who, 23, Color(1.0, 0.86, 0.5), 8)
	whol.position = Vector2(156, 82)
	prof.add_child(whol)
	var portrait := _medallion(_face_tex(hid), "", hcol.lightened(0.25), hcol.darkened(0.45), 136, func(): _open_heroes(),
		{"face": true, "icon_frac": 0.96, "icon_dy": 0.0, "phase": 0.1})
	prof.add_child(portrait)
	var star := TextureRect.new()
	star.texture = _res("res://assets/ui/mm_star.png")
	star.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	star.size = Vector2(70, 70)
	star.position = Vector2(88, 80)
	star.mouse_filter = Control.MOUSE_FILTER_IGNORE
	prof.add_child(star)
	var lvl := _label(str(Progress.hero_level(hid)), 30, Color(0.36, 0.14, 0.02), 0)
	lvl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lvl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lvl.position = Vector2(88, 84)
	lvl.size = Vector2(70, 66)
	prof.add_child(lvl)
	# ---- top centre: the title
	var logo := TextureRect.new()
	logo.texture = _res("res://assets/ui/mm_logo.png")
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.anchor_left = 0.5
	logo.anchor_right = 0.5
	logo.offset_left = -330
	logo.offset_right = 330
	logo.offset_top = 0
	logo.offset_bottom = 264
	logo.pivot_offset = Vector2(330, 132)
	logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(logo)
	var bob := logo.create_tween().set_loops()
	bob.tween_property(logo, "offset_top", 10.0, 1.8).set_trans(Tween.TRANS_SINE)
	bob.parallel().tween_property(logo, "offset_bottom", 274.0, 1.8).set_trans(Tween.TRANS_SINE)
	bob.tween_property(logo, "offset_top", 0.0, 1.8).set_trans(Tween.TRANS_SINE)
	bob.parallel().tween_property(logo, "offset_bottom", 264.0, 1.8).set_trans(Tween.TRANS_SINE)
	# ---- top right: currencies
	var cur := VBoxContainer.new()
	cur.anchor_left = 1.0
	cur.anchor_right = 1.0
	cur.offset_left = -336
	cur.offset_right = -20
	cur.offset_top = 16
	cur.add_theme_constant_override("separation", 8)
	cur.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(cur)
	cur.add_child(_currency_pill(ICON_SHARD, str(Progress.shards()), Color(0.9, 0.82, 1.0), func(): _open_heroes()))
	cur.add_child(_currency_pill(_scrap_tex(era_now), str(Progress.scrap(era_now)), Color(0.86, 0.94, 1.0), func(): _open_workshop("")))
	var sl := _label("%s SCRAP" % era_now.to_upper(), 17, Color(0.82, 0.86, 0.92), 6)
	sl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	cur.add_child(sl)
	# ---- left column: settings, quit
	var lcol := VBoxContainer.new()
	lcol.anchor_top = 0.5
	lcol.anchor_bottom = 0.5
	lcol.offset_left = 22
	lcol.offset_top = -150
	lcol.add_theme_constant_override("separation", 14)
	lcol.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(lcol)
	lcol.add_child(_medallion(_res("res://assets/ui/mm_gear.png"), "", Color(0.5, 0.62, 0.8), Color(0.16, 0.24, 0.4), 112,
		func(): _open_settings(), {"icon_frac": 0.66, "phase": 0.3}))
	if OS.has_feature("pc"):
		lcol.add_child(_medallion(_res("res://assets/ui/mm_door.png"), "", Color(0.45, 0.55, 0.72), Color(0.12, 0.17, 0.3), 112,
			func(): get_tree().quit(), {"icon_frac": 0.62, "phase": 0.6}))
	# ---- right column: age badge, new timeline
	var rcol := VBoxContainer.new()
	rcol.anchor_left = 1.0
	rcol.anchor_right = 1.0
	rcol.anchor_top = 0.5
	rcol.anchor_bottom = 0.5
	rcol.offset_left = -262
	rcol.offset_right = -22
	rcol.offset_top = -160
	rcol.alignment = BoxContainer.ALIGNMENT_BEGIN
	rcol.add_theme_constant_override("separation", 14)
	rcol.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(rcol)
	var stars := 0
	for mid in map_order:
		stars += Progress.stars(mid)
	var age := _nine("res://assets/ui/mm_panel.png", [60, 60, 60, 60], Vector2(240, 150), 0.62)
	var av := VBoxContainer.new()
	av.set_anchors_preset(Control.PRESET_FULL_RECT)
	av.alignment = BoxContainer.ALIGNMENT_CENTER
	av.add_theme_constant_override("separation", 0)
	age.add_child(av)
	var al1 := _label(era_now.to_upper(), 28, Color(1.0, 0.86, 0.45), 8)
	al1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	av.add_child(al1)
	var al2 := _label("Age %d of %d" % [_eras().find(era_now) + 1, _eras().size()], 22, Color(0.92, 0.95, 1.0), 6)
	al2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	av.add_child(al2)
	var srow := HBoxContainer.new()
	srow.alignment = BoxContainer.ALIGNMENT_CENTER
	srow.add_child(_icon(_res("res://assets/ui/mm_star.png") as Texture2D, 38))
	srow.add_child(_label("%d / %d" % [stars, map_order.size() * 3], 25, C_COIN, 7))
	av.add_child(srow)
	rcol.add_child(age)
	if Progress.can_new_timeline(map_order):
		var tl := _medallion(_res("res://assets/ui/menu_portal.png"), "NEW TIMELINE", Color(0.75, 0.45, 1.0), Color(0.25, 0.08, 0.45), 124,
			func(): _confirm_new_timeline(), {"badge": true, "icon_frac": 0.7, "label_size": 22, "phase": 0.8})
		tl.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		rcol.add_child(tl)
	# ---- bottom row: the big buttons
	var row := HBoxContainer.new()
	row.anchor_left = 0.5
	row.anchor_right = 0.5
	row.anchor_top = 1.0
	row.anchor_bottom = 1.0
	row.offset_left = -660
	row.offset_right = 660
	row.offset_top = -350
	row.offset_bottom = -6
	row.grow_vertical = Control.GROW_DIRECTION_BEGIN
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 58)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(row)
	var et: Array = Progress.era_towers(era_now)
	var nxt := Progress.next_unlock(era_now)
	var tower_badge := nxt != "" and Progress.scrap(era_now) >= Progress.tower_scrap_cost(nxt)
	var hero_badge := false
	for h in defs.heroes.heroes:
		var hdx: Dictionary = defs.heroes.heroes[h]
		if not Progress.hero_owned(h) and Progress.hero_available(hdx) and Progress.shards() >= Progress.hero_cost(hdx, defs.heroes.heroes):
			hero_badge = true
	var cm := _continue_map()
	var cme := _map_entry(cm)
	var bot := [
		_medallion(_icon_tex(str(et[0])) if not et.is_empty() else ICON_GOLD, "TOWERS", Color(0.42, 0.7, 1.0), Color(0.08, 0.22, 0.55), 166,
			func(): _open_workshop(""), {"badge": tower_badge, "icon_frac": 0.98, "icon_dy": -0.12, "phase": 0.0}),
		_medallion(_face_tex(hid), "HEROS", hcol.lightened(0.3), hcol.darkened(0.45), 166,
			func(): _open_heroes(), {"badge": hero_badge, "face": true, "icon_frac": 0.94, "phase": 0.2}),
		_medallion(_res("res://assets/ui/mm_play.png"), "PLAY", Color(0.55, 0.95, 0.3), Color(0.08, 0.45, 0.06), 236,
			func():
				Progress.current_map = cm
				get_tree().reload_current_scene(),
			{"rim": "res://assets/ui/mm_rim_play.png", "icon_frac": 0.5, "icon_dy": 0.0, "play": true, "label_size": 40, "phase": 0.4,
			"sub": "%s  -  Map %d" % [str(cme.get("name", "")), map_order.find(cm) + 1]}),
		_medallion(_res("res://assets/ui/mm_upgrade.png"), "UPGRADES", Color(0.45, 0.85, 1.0), Color(0.06, 0.3, 0.62), 166,
			func(): _open_legacy(), {"badge": Progress.points_free() > 0, "icon_frac": 0.66, "icon_dy": -0.06, "phase": 0.6}),
		_medallion(_res("res://assets/ui/mm_map.png"), "MAPS", Color(0.45, 0.88, 0.62), Color(0.06, 0.38, 0.3), 166,
			func():
				title_screen.visible = false
				map_select.visible = true,
			{"icon_frac": 0.72, "icon_dy": -0.03, "phase": 0.8}),
	]
	for c in bot:
		c.size_flags_vertical = Control.SIZE_SHRINK_END
		row.add_child(c)
	# PLAY breathes
	var pbody: Control = (bot[2] as Control).get_child(0)
	var pulse := pbody.create_tween().set_loops()
	pulse.tween_property(pbody, "scale", Vector2.ONE * 1.05, 0.8).set_trans(Tween.TRANS_SINE)
	pulse.tween_property(pbody, "scale", Vector2.ONE, 0.8).set_trans(Tween.TRANS_SINE)
	var ver := _label("v%s" % str(ProjectSettings.get_setting("application/config/version", "")), 16, Color(0.62, 0.67, 0.75), 4)
	ver.anchor_top = 1.0
	ver.anchor_bottom = 1.0
	ver.offset_left = 16
	ver.offset_top = -34
	title_screen.add_child(ver)


## A hero's colour (heroes.json), for their portrait medallions.
func _hero_color(hid: String) -> Color:
	var c: Array = defs.heroes.heroes.get(hid, {}).get("color", [0.5, 0.4, 0.7])
	return Color(float(c[0]), float(c[1]), float(c[2]))


## Workshop: spend an era's Scrap to unlock that era's towers. Each era's Scrap starts at 0.
func _open_workshop(era: String, reuse: Control = null) -> void:
	if era == "":
		era = str(Progress.data.get("tab", ""))
	if era == "" or not Progress.is_unlocked(_first_map_of(era)):
		era = str(_map_entry(_menu_map()).get("era", "Stone Age"))
	var dlg: Control = reuse if reuse != null and is_instance_valid(reuse) else _modal(ui_root, 0.6)
	var box: VBoxContainer = dlg.get_meta("box")
	_clear_box(box)
	dlg.set_meta("full_h", true)
	box.set_meta("want_w", 1500.0)
	box.add_theme_constant_override("separation", 10)
	# header: everything here keeps its place whichever age tab is open
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 24)
	box.add_child(head)
	var ttl := _label("TOWERS  -  %s" % era.to_upper(), 44, C_GOLD, 12)
	ttl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ttl.clip_text = true
	head.add_child(ttl)
	var sc := HBoxContainer.new()
	sc.custom_minimum_size = Vector2(230, 0)
	sc.alignment = BoxContainer.ALIGNMENT_END
	sc.add_child(_icon(_scrap_tex(era), 60))
	var scl := _label(str(Progress.scrap(era)), 40, Color(0.75, 0.85, 0.95), 9)
	scl.custom_minimum_size = Vector2(120, 0)
	sc.add_child(scl)
	head.add_child(sc)
	var done := _button("DONE", Color(0.2, 0.58, 0.18), 30)
	done.custom_minimum_size = Vector2(200, 62)
	done.pressed.connect(func():
		_sfx("click")
		dlg.queue_free()
		_refresh_menus())
	head.add_child(done)
	_close_with(dlg, done)
	var intro := _label("Unlock towers in order with this age's Scrap. Every unlock gives ALL towers in this age +%d%% damage." % int(round(float(Progress.workshop.get("tech_bonus", 0.0)) * 100)), 19, Color(0.78, 0.83, 0.9), 5)
	intro.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(intro)
	# every age has a tab; ages you haven't reached stay locked
	var tabs := GridContainer.new()
	tabs.columns = 5
	tabs.add_theme_constant_override("h_separation", 8)
	tabs.add_theme_constant_override("v_separation", 8)
	tabs.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	box.add_child(tabs)
	for en in _eras():
		var open := Progress.is_unlocked(_first_map_of(en))
		var tb := _button(en.to_upper() if open else "LOCKED", Color(0.2, 0.36, 0.6) if en == era else (Color(0.16, 0.24, 0.38) if open else Color(0.12, 0.14, 0.18)), 17)
		tb.custom_minimum_size = Vector2(230, 44)
		tb.clip_text = true
		if not open:
			tb.disabled = true
			tb.icon = ICON_LOCK
			tb.add_theme_constant_override("icon_max_width", 26)
		elif en == era:
			tb.add_theme_color_override("font_color", C_GOLD)
		tb.pressed.connect(func():
			if en == era:
				return
			_sfx("click")
			Progress.data.tab = en
			_open_workshop(en, dlg))
		tabs.add_child(tb)
	# four identical, fixed-size cards
	var cards := HFlowContainer.new()
	cards.alignment = FlowContainer.ALIGNMENT_CENTER
	cards.add_theme_constant_override("h_separation", 16)
	cards.add_theme_constant_override("v_separation", 16)
	box.add_child(cards)
	var rank := 0
	for tid in Progress.era_towers(era):
		rank += 1
		var def: Dictionary = defs.towers[tid]
		var own := Progress.tower_unlocked(tid)
		var cost := Progress.tower_scrap_cost(tid)
		var card := PanelContainer.new()
		card.add_theme_stylebox_override("panel", _style(Color(0.09, 0.15, 0.25) if own else Color(0.09, 0.13, 0.18), 18, C_GOLD.darkened(0.3) if own else C_PANEL_EDGE, 3))
		card.custom_minimum_size = Vector2(300, 430)
		cards.add_child(card)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 4)
		card.add_child(v)
		var ic := _icon(_icon_tex(tid), 112)
		ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		ic.modulate = Color.WHITE if own else Color(0.55, 0.55, 0.55)
		v.add_child(ic)
		var nm := _label("%d. %s" % [rank, str(def.name)], 26, C_TEXT, 7)
		nm.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		nm.clip_text = true
		nm.custom_minimum_size = Vector2(270, 0)
		v.add_child(nm)
		var ln := _label("%s  -  %d gold" % [str(def.lineage), int(def.cost)], 18, Color(1, 0.8, 0.5), 5)
		ln.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(ln)
		var ds := _label(str(def.desc), 18, Color(0.78, 0.83, 0.9), 4)
		ds.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		ds.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		ds.vertical_alignment = VERTICAL_ALIGNMENT_TOP
		ds.max_lines_visible = 3
		ds.custom_minimum_size = Vector2(270, 78)
		ds.size_flags_vertical = Control.SIZE_EXPAND_FILL
		v.add_child(ds)
		var dbt := _button("DETAILS", Color(0.3, 0.36, 0.5), 20)
		dbt.custom_minimum_size = Vector2(0, 50)
		dbt.pressed.connect(func():
			_sfx("click")
			_tower_detail(tid))
		v.add_child(dbt)
		# status slot: always the same height
		var slot := CenterContainer.new()
		slot.custom_minimum_size = Vector2(0, 72)
		v.add_child(slot)
		if own:
			slot.add_child(_label("FREE" if cost == 0 else "UNLOCKED", 26, Color(0.6, 1.0, 0.6), 6))
		elif Progress.next_unlock(era) != tid:
			var lk := _button("UNLOCK #%d FIRST" % (rank - 1), Color(0.14, 0.16, 0.2), 19)
			lk.disabled = true
			lk.custom_minimum_size = Vector2(270, 56)
			slot.add_child(lk)
		else:
			var ub := _button("UNLOCK  %d" % cost, Color(0.2, 0.55, 0.2), 22)
			ub.icon = _scrap_tex(era)
			ub.add_theme_constant_override("icon_max_width", 40)
			ub.custom_minimum_size = Vector2(270, 56)
			ub.disabled = Progress.scrap(era) < cost
			ub.pressed.connect(func():
				if Progress.unlock_tower(tid):
					_sfx("upgrade")
					_open_workshop(era, dlg))
			slot.add_child(ub)
	if OS.is_debug_build():
		var cheat := _button("+300 SCRAP (test)", Color(0.35, 0.3, 0.45), 18)
		cheat.custom_minimum_size = Vector2(260, 52)
		cheat.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		cheat.pressed.connect(func():
			Progress.add_scrap(era, 300)
			_open_workshop(era, dlg))
		box.add_child(cheat)
	dlg.get_parent().move_child(dlg, -1)


## Hero roster: pick the hero that joins every match.
const ICON_SHARD := preload("res://assets/ui/icon_shard.png")


func _face_tex(id: String) -> Texture2D:
	return _res("res://assets/ui/face_%s.png" % id)


## Grid of hero faces. Tapping one opens its detail card (play as / buy).
func _hero_picker(parent: VBoxContainer) -> VBoxContainer:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(box)
	_fill_hero_picker(box)
	return box


func _fill_hero_picker(box: VBoxContainer) -> void:
	var wallet := HBoxContainer.new()
	wallet.alignment = BoxContainer.ALIGNMENT_CENTER
	wallet.add_theme_constant_override("separation", 8)
	wallet.add_child(_icon(ICON_SHARD, 40))
	wallet.add_child(_label("%d TIME SHARDS" % Progress.shards(), 26, Color(0.82, 0.74, 1.0), 7))
	box.add_child(wallet)
	var hrow := HFlowContainer.new()
	hrow.alignment = FlowContainer.ALIGNMENT_CENTER
	hrow.add_theme_constant_override("h_separation", 14)
	hrow.add_theme_constant_override("v_separation", 14)
	box.add_child(hrow)
	var cur := Progress.hero()
	if not defs.heroes.heroes.has(cur) or not Progress.hero_owned(cur):
		cur = "ugo"
		Progress.set_hero(cur)
	for hid in defs.heroes.heroes:
		var hd: Dictionary = defs.heroes.heroes[hid]
		var owned := Progress.hero_owned(hid)
		var col := Color(hd.color[0], hd.color[1], hd.color[2])
		var hb := _button(("%s  Lv%d" % [_short_name(str(hd.name)), Progress.hero_level(hid)]) if owned else _short_name(str(hd.name)), col.lerp(Color(0.12, 0.18, 0.3), 0.35 if owned else 0.75), 20)
		hb.icon = _face_tex(hid)
		hb.expand_icon = true
		hb.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		hb.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		hb.add_theme_constant_override("icon_max_width", 104)
		hb.custom_minimum_size = Vector2(150, 168)
		hb.clip_text = true
		if hid == cur:
			var sel := _style(col.lerp(Color(1, 0.85, 0.3), 0.35), 18, Color(1, 0.85, 0.3), 6)
			sel.border_width_bottom = 9
			hb.add_theme_stylebox_override("normal", sel)
			hb.add_theme_stylebox_override("hover", sel)
		var avail := owned or Progress.hero_available(hd)
		if not owned:
			# not owned: the face stays shaded; the lock only shows until the hero's age is reached
			hb.add_theme_color_override("icon_normal_color", Color(0.45, 0.45, 0.5))
			hb.add_theme_color_override("icon_hover_color", Color(0.55, 0.55, 0.6))
			if not avail:
				var lk := _icon(ICON_LOCK, 40)
				lk.position = Vector2(104, 6)
				lk.mouse_filter = Control.MOUSE_FILTER_IGNORE
				hb.add_child(lk)
		hb.pressed.connect(func():
			_sfx("click")
			_hero_detail(hid, box))
		var tile := VBoxContainer.new()
		tile.add_theme_constant_override("separation", 6)
		tile.add_child(hb)
		tile.add_child(_hero_price_button(hd, box, Vector2(150, 52), 20))
		hrow.add_child(tile)
	var hd2: Dictionary = defs.heroes.heroes[cur]
	var now := _label("Playing as: %s, %s" % [hd2.name, hd2.title], 22, C_GOLD, 6)
	now.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(now)
	var tip := _label("Tap a hero to see what they do.", 18, Color(0.68, 0.75, 0.85), 5)
	tip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(tip)


## Shard-price button under a hero. Owned: a quiet label. Age not reached: a greyed button you
## can't press showing the price. Age reached: the same button lights up and buys the hero.
func _hero_price_button(hd: Dictionary, picker_box: VBoxContainer, size: Vector2, font: int) -> Control:
	var hid := str(hd.id)
	if Progress.hero_owned(hid):
		var c := CenterContainer.new()
		c.custom_minimum_size = size
		var cur := Progress.hero() == hid
		c.add_child(_label("PLAYING" if cur else "OWNED", font - 2, C_GOLD if cur else Color(0.6, 0.68, 0.8), 5))
		return c
	var cost := Progress.hero_cost(hd, defs.heroes.heroes)
	var avail := Progress.hero_available(hd)
	var b := _button(str(cost), Color(0.5, 0.28, 0.85) if avail else Color(0.16, 0.16, 0.2), font)
	b.icon = ICON_SHARD
	b.expand_icon = false
	b.add_theme_constant_override("icon_max_width", int(size.y * 0.62))
	b.custom_minimum_size = size
	b.disabled = not avail
	b.tooltip_text = "Reach the %s to unlock" % str(hd.era) if not avail else "Buy for %d Time Shards" % cost
	if avail:
		var glow := b.create_tween().set_loops()
		glow.tween_property(b, "modulate", Color(1.25, 1.2, 1.35), 0.7).set_trans(Tween.TRANS_SINE)
		glow.tween_property(b, "modulate", Color.WHITE, 0.7).set_trans(Tween.TRANS_SINE)
	b.pressed.connect(func():
		if Progress.buy_hero(hd, defs.heroes.heroes):
			_sfx("level_up")
			Progress.set_hero(hid)
			_toast("%s joins you!" % str(hd.name), C_GOLD)
			for m in modals:
				if is_instance_valid(m) and m.has_meta("hero_detail"):
					m.queue_free()
			_refresh_hero_pickers(picker_box)
		else:
			_sfx("error", -4.0, 0.0)
			_toast("Need %d more Time Shards. Earn them from maps and hero level-ups." % (cost - Progress.shards()), Color(0.85, 0.7, 1.0))
			toast_t = 3.5)
	return b


## Rebuilds every open hero picker (after picking or buying).
func _refresh_hero_pickers(box: VBoxContainer) -> void:
	if not is_instance_valid(box):
		return
	for c in box.get_children():
		box.remove_child(c)
		c.queue_free()
	_fill_hero_picker(box)


func _hero_pros_cons(hd: Dictionary) -> Array:
	var pros := []
	var cons := []
	var b: Dictionary = hd.base
	var a: Dictionary = hd.aura
	var ab: Dictionary = hd.ability
	match str(b.kind):
		"projectile":
			pros.append("Long reach: hits robots %.1f tiles away" % float(b.range))
			if float(b.get("splash", 0.0)) > 0.0:
				pros.append("Shots splash nearby robots")
			else:
				cons.append("Hits one robot per shot")
		"melee":
			pros.append("Huge hits that punch through armor")
			if int(b.get("max_targets", 1)) > 1:
				pros.append("Hits %d robots with every swing" % int(b.max_targets))
			cons.append("Short range: place it right beside the path")
		"pulse":
			pros.append("Hits every robot around it and slows them")
			cons.append("Short range and small hits")
		"lob":
			pros.append("Explosive shells blast whole groups")
			pros.append("Longest range of any hero (%.1f tiles)" % float(b.range))
			cons.append("Slow to fire; shells can miss fast robots")
	if b.has("shred"):
		pros.append("Strips armor off robots it hits")
	var boost := ""
	if a.has("speed"):
		boost = "+%d%% attack speed" % int(round(float(a.speed) * 100))
	elif a.has("damage"):
		boost = "+%d%% damage" % int(round(float(a.damage) * 100))
	elif a.has("range"):
		boost = "+%d%% range" % int(round(float(a.range) * 100))
	if str(a.lineage) == "":
		pros.append("Aura: nearby towers get %s" % boost)
	else:
		pros.append("Aura: nearby %s towers get %s" % [a.lineage, boost])
		cons.append("Aura only helps %s towers" % a.lineage)
	pros.append("Spots cloaked robots and can hit flying ones")
	if float(ab.cooldown) >= 60:
		cons.append("Ability has a long cooldown (%ds)" % int(ab.cooldown))
	if cons.size() < 2:
		cons.append("Ability unlocks at rank %d each match" % int(ab.get("unlock", 3)))
	return [pros, cons]


## A turning 3D model of a hero for menus.
func _hero_viewer(hid: String, size: Vector2) -> SubViewportContainer:
	return _model_viewer("res://assets/heroes/%s.glb" % hid, size)


func _model_viewer(path: String, size: Vector2) -> SubViewportContainer:
	var svc := SubViewportContainer.new()
	svc.stretch = true
	svc.custom_minimum_size = size
	svc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var vp := SubViewport.new()
	vp.own_world_3d = true
	vp.transparent_bg = true
	vp.msaa_3d = Viewport.MSAA_4X if (Progress.gfx_level() == 0 and not OS.has_feature("mobile")) else Viewport.MSAA_DISABLED
	svc.add_child(vp)
	var pivot := Node3D.new()
	vp.add_child(pivot)
	# the model is set up as in game: HQ clips and outline, spinning / flickering / bubbling parts, turning and swinging
	var holder := Node3D.new()
	pivot.add_child(holder)
	var model: Node3D = _inst(path)
	holder.add_child(model)
	_rig_model(holder, model)
	var box := AABB()
	var first := true
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var m3 := mi as MeshInstance3D
		if str(m3.name).ends_with("_Outline"):
			continue
		var xf := Transform3D.IDENTITY
		var n: Node = m3
		while n != null and n != model:
			if n is Node3D:
				xf = (n as Node3D).transform * xf
			n = n.get_parent()
		var bb: AABB = xf * m3.get_aabb()
		box = bb if first else box.merge(bb)
		first = false
	model.position = -Vector3(box.get_center().x, box.position.y, box.get_center().z)
	var h := maxf(box.size.y, maxf(box.size.x, box.size.z) * 0.8)
	var cam := Camera3D.new()
	cam.fov = 30
	vp.add_child(cam)
	cam.transform = Transform3D(Basis(), Vector3(0, h * 0.62, h * 2.35)).looking_at(Vector3(0, h * 0.47, 0))
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-40, 30, 0)
	sun.light_energy = 1.25
	vp.add_child(sun)
	var rim := DirectionalLight3D.new()            # cool rim light from behind: a showcase look
	rim.rotation_degrees = Vector3(-25, 200, 0)
	rim.light_energy = 0.8
	rim.light_color = Color(0.75, 0.85, 1.0)
	vp.add_child(rim)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.75, 0.72, 0.8)
	env.environment.ambient_light_energy = 0.7
	env.environment.background_mode = Environment.BG_CLEAR_COLOR
	vp.add_child(env)
	# turns to and fro, mostly facing you, instead of spinning its back to the camera half the time
	holder.set_meta("viewer_seed", randf() * 10.0)
	_viewers.append(holder)
	var tw := pivot.create_tween().set_loops()
	tw.tween_property(pivot, "rotation:y", 0.65, 4.5).from(-0.65).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(pivot, "rotation:y", -0.65, 4.5).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	return svc


## Card model viewers come alive: HQ models play their Idle (and now and then their combat loop), the others breathe,
## look around and lift their arm; spinning, flickering and bubbling parts move as in game.
var _viewers: Array = []
func _tick_viewers(delta: float) -> void:
	if _viewers.is_empty():
		return
	var keep := []
	for h in _viewers:
		if not is_instance_valid(h) or not (h as Node).is_inside_tree():
			continue
		keep.append(h)
		var n: Node3D = h
		_spin_flicker(n, delta, 9.0)
		var t: float = time_s + float(n.get_meta("viewer_seed", 0.0))
		if n.has_meta("anim"):
			var ap: AnimationPlayer = n.get_meta("anim")
			ap.speed_scale = 1.0
			# every ~9 s show the combat loop for a few seconds
			var want: String = n.get_meta("clip_combat") if fmod(t, 9.0) > 6.0 else "Idle"
			if ap.current_animation != want and not (ap.current_animation in HQ_ONESHOTS and ap.is_playing()):
				ap.play(want, 0.4)
			continue
		if n.has_meta("yaw"):
			(n.get_meta("yaw") as Node3D).rotation.y = 0.32 * sin(t * 0.55) + 0.12 * sin(t * 1.7)
		if n.has_meta("arm"):
			var arm: Node3D = n.get_meta("arm")
			arm.rotation.x = float(arm.get_meta("rest", 0.0)) - 0.22 * (0.5 + 0.5 * sin(t * 1.25))
		if n.has_meta("orb"):
			(n.get_meta("orb") as Node3D).scale = Vector3.ONE * (1.0 + 0.1 * sin(t * 4.0))
		var body: Node3D = n.get_meta("viewer_body") if n.has_meta("viewer_body") else null
		if body == null and not n.has_meta("viewer_body"):
			var y: Node3D = n.get_meta("yaw") if n.has_meta("yaw") else null
			body = (y.get_child(0) as Node3D) if y != null and y.get_child_count() > 0 and y.get_child(0) is Node3D else y
			n.set_meta("viewer_body", body)
		if body != null:
			body.scale = Vector3(1.0 - 0.008 * sin(t * 2.2), 1.0 + 0.018 * sin(t * 2.2), 1.0 - 0.008 * sin(t * 2.2))
	_viewers = keep


func _tower_pros_cons(d: Dictionary) -> Array:
	var b: Dictionary = d.base
	var pros := []
	var cons := []
	var single := int(b.get("chain", 0)) == 0 and float(b.get("splash", 0.0)) <= 0.0 and int(b.get("shots", 1)) <= 1
	match str(b.kind):
		"projectile":
			pros.append("Long reach (%.1f tiles)" % float(b.range) if float(b.range) >= 4.5 else "Fast, reliable single-target damage")
			if single:
				cons.append("Hits one robot per shot")
		"melee":
			pros.append("Heavy hits up close")
			cons.append("Short range: build it right beside the path")
		"pulse":
			pros.append("Hits every robot in range at once")
			cons.append("Small hits; shines with upgrades and combos")
		"lob":
			pros.append("Explosive splash hits whole groups")
			pros.append("Long range (%.1f tiles)" % float(b.range))
			cons.append("Shells fly slowly and can miss fast robots")
	if float(b.get("slow", 0.0)) > 0.0:
		pros.append("Slows robots by %d%%" % int(float(b.slow) * 100))
	if float(b.get("stun", 0.0)) > 0.0:
		pros.append("Stuns robots")
	if float(b.get("burn", 0.0)) > 0.0:
		pros.append("Sets robots on fire")
	if int(b.get("chain", 0)) > 0:
		pros.append("Lightning jumps to %d more robots" % int(b.chain))
	if float(b.get("shield_break", 0.0)) > 0.0:
		pros.append("Knocks out robot shields")
	if float(b.get("armor_pierce", 0.0)) > 0.0:
		pros.append("Punches through armor")
	if float(b.get("shred", 0.0)) > 0.0:
		pros.append("Strips armor off robots")
	if float(b.get("expose", 0.0)) > 0.0:
		pros.append("Marked robots take +%d%% damage" % int(float(b.expose) * 100))
	if int(b.get("shots", 1)) > 1:
		pros.append("Fires %d shots per volley" % int(b.shots))
	if float(b.get("crit_chance", 0.0)) > 0.0:
		pros.append("%d%% chance of critical hits" % int(float(b.crit_chance) * 100))
	if float(b.get("knockback", 0.0)) > 0.0:
		pros.append("Knocks robots backward")
	if str(b.get("dtype", "")) == "energy":
		pros.append("Energy damage cuts through armor")
	if float(b.get("anti_air", 0.0)) > 0.0:
		pros.append("Extra damage to flying robots")
	if float(b.get("detect", 0.0)) > 0.0 or str(b.kind) == "pulse":
		pros.append("Spots cloaked robots for your other towers")
	else:
		cons.append("Can't see cloaked robots on its own")
	if not sim.can_hit_air(b):
		cons.append("Can't hit flying robots")
	if float(b.cooldown) >= 2.0:
		cons.append("Slow to fire")
	if int(d.cost) >= 500:
		cons.append("Expensive to build (%d gold)" % int(d.cost))
	return [pros, cons]


## Every robot type a map sends (including ones that split off or get summoned), in order of first appearance.
func _map_robots(mid: String) -> Array:
	var mp := Defs.load_map(mid)
	var wf: Dictionary = Defs._load("res://data/" + str(mp.get("waves_file", "waves.json")))
	var first := {}
	var order := []
	var add := func(t: String, w: int) -> void:
		if not defs.enemies.has(t) or first.has(t):
			return
		first[t] = w
		order.append(t)
	var wi := 0
	for wave in wf.waves:
		wi += 1
		for g in wave:
			add.call(str(g.type), wi)
	var i := 0
	while i < order.size():           # children: split-on-death and summons
		var d: Dictionary = defs.enemies[order[i]]
		if d.has("on_death") and d.on_death is Dictionary and d.on_death.has("type"):
			add.call(str(d.on_death.type), first[order[i]])
		if d.has("summon"):
			add.call(str(d.summon.type), first[order[i]])
		i += 1
	var out := []
	for t in order:
		out.append([t, first[t]])
	return out


## Robot card for a map: who comes, from which wave, how tough they are there, and how to beat them.
## intro = the automatic popup on a map's first visit: NEW! over robots never met, then they count as seen.
func _robot_roster(mid: String, intro := false) -> void:
	var robots := _map_robots(mid)
	var fresh := {}
	if intro:
		var ts := []
		for pair in robots:
			ts.append(pair[0])
			if not Progress.robot_seen(str(pair[0])):
				fresh[pair[0]] = true
		Progress.mark_seen(mid, ts)
	var mp := Defs.load_map(mid)
	var me := _map_entry(mid)
	var hpm := float(mp.get("hp_mult", 1.0)) * Progress.timeline_hp_mult()
	var bossm := float(mp.get("boss_hp_mult", 1.0))
	var arm := float(mp.get("armor_mult", 1.0))
	var dlg := _modal(ui_root, 0.7)
	var box: VBoxContainer = dlg.get_meta("box")
	box.set_meta("want_w", 1500.0)
	box.add_theme_constant_override("separation", 12)
	detail_open += 1
	dlg.tree_exiting.connect(func(): detail_open = maxi(0, detail_open - 1))
	var close := func():
		_sfx("click")
		dlg.queue_free()
		if intro:
			_toast("Place your hero (free), then pick towers on the right", C_TEXT)
			toast_t = 4.5
			_path_preview(true)
	_on_close(dlg, close)
	var ttl := _label(("INCOMING!  -  %s" if intro else "ROBOTS  -  %s") % str(me.get("name", mid)).to_upper(), 48, Color(1.0, 0.55, 0.5), 12)
	ttl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(ttl)
	var sub_txt := "%s   -   Map %d of %d   -   20 waves. Stats are for this map." % [str(me.get("era", "")), map_order.find(mid) + 1, map_order.size()]
	if intro:
		sub_txt = "These robots attack on this map. " + ("NEW! marks robots you haven't faced yet." if not fresh.is_empty() else "You've faced all of them before.")
	var sub := _label(sub_txt, 22, C_TEXT, 6)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(sub)
	var grid := HFlowContainer.new()
	grid.alignment = FlowContainer.ALIGNMENT_CENTER
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 14)
	box.add_child(grid)
	for pair in robots:
		var t: String = pair[0]
		var d: Dictionary = defs.enemies[t]
		var boss := bool(d.get("boss", false))
		var card := PanelContainer.new()
		var cc := Color(0.55, 0.15, 0.15) if boss else Color(0.25, 0.32, 0.45)
		card.add_theme_stylebox_override("panel", _style(Color(0.08, 0.09, 0.13), 18, cc, 4 if boss else 3))
		card.custom_minimum_size = Vector2(440, 0)
		grid.add_child(card)
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 12)
		card.add_child(h)
		var ic := _icon(_res("res://assets/ui/icon_%s.png" % t) as Texture2D if ResourceLoader.exists("res://assets/ui/icon_%s.png" % t) else ICON_WAVE, 120)
		var holder := Control.new()          # portrait with room on top for the NEW! sign over its head
		holder.custom_minimum_size = Vector2(120, 150)
		holder.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(holder)
		holder.add_child(ic)
		ic.position = Vector2(0, 30)
		ic.size = Vector2(120, 120)
		if fresh.has(t):
			card.add_theme_stylebox_override("panel", _style(Color(0.08, 0.09, 0.13), 18, Color(1.0, 0.8, 0.15), 4))
			var badge := PanelContainer.new()
			var bs := _style(Color(1.0, 0.82, 0.12), 12, Color(0.55, 0.3, 0.0), 3)
			bs.set_content_margin_all(4)
			bs.content_margin_left = 12
			bs.content_margin_right = 12
			badge.add_theme_stylebox_override("panel", bs)
			badge.add_child(_label("NEW!", 26, Color(0.75, 0.05, 0.05), 0))
			holder.add_child(badge)
			badge.rotation = -0.12
			badge.resized.connect(func(): badge.position = Vector2((120.0 - badge.size.x) * 0.5, 0.0))
			badge.pivot_offset = Vector2(45, 18)
			var bt: Tween = badge.create_tween().set_loops()
			bt.tween_property(badge, "scale", Vector2(1.12, 1.12), 0.45).set_trans(Tween.TRANS_SINE)
			bt.tween_property(badge, "scale", Vector2.ONE, 0.45).set_trans(Tween.TRANS_SINE)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 2)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(v)
		var nm := _label(("BOSS: " if boss else "") + str(d.name), 26, Color(1, 0.5, 0.45) if boss else C_TEXT, 7)
		nm.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(nm)
		v.add_child(_label("First seen: wave %d" % int(pair[1]), 17, Color(0.75, 0.8, 0.9), 4))
		var hp := float(d.hp) * hpm * (bossm if boss else 1.0)
		var sp := float(d.speed)
		var spd := "slow" if sp < 0.9 else ("fast" if sp > 1.7 else "normal")
		var stats := "HP %s   Armor %s   Speed %s (%s)" % [_short_num(hp), str(snappedf(float(d.armor) * arm, 0.1)), str(snappedf(sp, 0.01)), spd]
		if float(d.get("shield", 0.0)) > 0.0:
			stats += "\nShield %s (recharges)" % _short_num(float(d.shield) * hpm * (bossm if boss else 1.0))
		stats += "\nCosts you %d %s if it gets through   -   %d gold" % [int(d.leak), "life" if int(d.leak) == 1 else "lives", int(d.bounty)]
		var sl := _label(stats, 18, Color(0.85, 0.88, 0.92), 4)
		sl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(sl)
		for tip in _robot_traits(d):
			var tl := _label("-  " + str(tip), 17, Color(1.0, 0.8, 0.55), 4)
			tl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			v.add_child(tl)
	var note := _label("Armor takes a flat chunk off every hit, so small fast hits struggle against armored robots.", 18, Color(0.75, 0.8, 0.9), 4)
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(note)
	var back := _button("LET'S GO!" if intro else "CLOSE", Color(0.2, 0.6, 0.3) if intro else Color(0.3, 0.36, 0.5), 28)
	back.custom_minimum_size = Vector2(300 if intro else 260, 80)
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	back.pressed.connect(close)
	box.add_child(back)
	dlg.get_parent().move_child(dlg, -1)


func _short_num(x: float) -> String:
	if x >= 10000.0:
		return "%.1fk" % (x / 1000.0)
	return str(int(round(x)))


func _robot_traits(d: Dictionary) -> Array:
	var out := []
	if d.get("flying", false):
		out.append("Flies: only shooting and pulse towers, anti-air and heros can hit it")
	if d.get("cloak", false):
		out.append("Cloaked: a Control tower, a spotter or your hero must reveal it")
	if float(d.get("shield", 0.0)) > 0.0:
		out.append("Shield recharges if left alone: burst it or use shield breakers")
	if d.has("heal"):
		out.append("Repairs robots around it: kill it first")
	if float(d.get("regen", 0.0)) > 0.0:
		out.append("Regenerates health over time")
	if d.has("on_death") and d.on_death is Dictionary and d.on_death.has("type"):
		var ct := str(d.on_death.type)
		out.append("Splits into %d %s when destroyed: splash damage helps" % [int(d.on_death.get("count", 1)), str(defs.enemies[ct].name) if defs.enemies.has(ct) else ct])
	if d.has("summon"):
		var st := str(d.summon.type)
		out.append("Calls in %s every %ds" % [str(defs.enemies[st].name) if defs.enemies.has(st) else st, int(d.summon.every)])
	if d.has("emp"):
		if d.emp.get("on_death", false):
			out.append("EMP blast when destroyed knocks out nearby towers")
		else:
			out.append("EMP knocks out towers within %.1f tiles for %.1fs: spread out" % [float(d.emp.radius), float(d.emp.duration)])
	if d.has("enrage"):
		out.append("Enrages below %d%% health and speeds up" % int(float(d.enrage.below) * 100))
	if float(d.armor) >= 4.0:
		out.append("Heavily armored: use big hits, Siege or armor piercing")
	return out


# ---------------------------------------------------------------- upgrade art, cards and trees (v0.9.12)
## Every upgrade gets a picture: its path colour, a soft glow, the tower's portrait and an emblem for what the
## upgrade mainly does (tools/blender/upgrade_emblems.py renders assets/ui/emblem_<kind>.png).
const EMBLEM_BY_MOD := [["chain", "chain"], ["burn", "flame"], ["slow", "slow"], ["stun", "stun"], ["crit_chance", "crit"],
	["shred", "shred"], ["expose", "expose"], ["armor_pierce", "pierce"], ["knockback", "push"], ["anti_air", "air"],
	["air_mult", "air"], ["boss_mult", "boss"], ["shots", "volley"], ["max_targets", "multi"]]
const EMBLEM_BY_DTYPE := {"fire": "flame", "blunt": "hammer", "energy": "energy", "pierce": "spear"}
const ROMAN := ["", "I", "II", "III", "IV", "V"]
var _radial: GradientTexture2D = null


func _tier_def(tid: String, key: String, tier: int) -> Dictionary:
	var d: Dictionary = defs.towers[tid]
	if tier <= 2:
		return d.tiers[tier - 1]
	return d.branches[key].tiers[tier - 3]


func _upgrade_emblem(u: Dictionary) -> String:
	var m: Dictionary = u.get("mods", {})
	for pr in EMBLEM_BY_MOD:
		if m.has(pr[0]):
			return pr[1]
	if m.has("dtype"):
		return str(EMBLEM_BY_DTYPE.get(str(m.dtype), "damage"))
	for pr in [["splash", "splash"], ["damage", "damage"], ["cooldown_mult", "speed"], ["range", "range"]]:
		if m.has(pr[0]):
			return pr[1]
	return "damage"


func _path_color(key: String, tier: int) -> Color:
	if tier <= 2:
		return Color(0.14, 0.52, 0.46)
	return Color(0.82, 0.42, 0.1) if key == "A" else Color(0.18, 0.44, 0.9)


func _radial_tex() -> GradientTexture2D:
	if _radial == null:
		var g := Gradient.new()
		g.set_color(0, Color(1, 1, 1, 0.9))
		g.set_color(1, Color(1, 1, 1, 0.0))
		_radial = GradientTexture2D.new()
		_radial.gradient = g
		_radial.fill = GradientTexture2D.FILL_RADIAL
		_radial.fill_from = Vector2(0.62, 0.38)
		_radial.fill_to = Vector2(1.15, 1.0)
		_radial.width = 128
		_radial.height = 128
	return _radial


func _ignore_mouse(c: Control) -> void:
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for ch in c.get_children():
		if ch is Control:
			_ignore_mouse(ch)


## state: open | owned | next (buy it now) | locked (a later tier) | blocked (the other path was chosen)
func _upgrade_art(tid: String, key: String, tier: int, sz: int, state := "open") -> Control:
	var u := _tier_def(tid, key, tier)
	var pc := _path_color(key, tier)
	var root := Control.new()
	root.custom_minimum_size = Vector2(sz, sz)
	var bg := Panel.new()
	var border := C_GOLD if state in ["owned", "next"] else pc.lightened(0.35)
	bg.add_theme_stylebox_override("panel", _style(pc.darkened(0.5), int(sz * 0.16), border, maxi(3, int(sz * (0.055 if state == "next" else 0.035)))))
	bg.position = Vector2.ZERO
	bg.size = Vector2(sz, sz)
	root.add_child(bg)
	var glow := TextureRect.new()
	glow.texture = _radial_tex()
	glow.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	glow.modulate = Color(pc.lightened(0.6).r, pc.lightened(0.6).g, pc.lightened(0.6).b, 0.5)
	glow.position = Vector2(sz * 0.05, sz * 0.05)
	glow.size = Vector2(sz * 0.9, sz * 0.9)
	root.add_child(glow)
	var ic := _icon(_icon_tex(tid), int(sz * 0.78))
	ic.position = Vector2(-sz * 0.02, sz * 0.25)
	ic.size = Vector2(sz * 0.78, sz * 0.72)
	root.add_child(ic)
	var em := _icon(_res("res://assets/ui/emblem_%s.png" % _upgrade_emblem(u)) as Texture2D, int(sz * 0.64))
	em.position = Vector2(sz * 0.38, sz * 0.0)
	em.size = Vector2(sz * 0.64, sz * 0.64)
	root.add_child(em)
	var num := _label(ROMAN[tier], maxi(14, int(sz * 0.2)), Color(1, 0.95, 0.8), 0)
	num.add_theme_constant_override("outline_size", maxi(6, int(sz * 0.08)))
	num.position = Vector2(sz * 0.07, sz * 0.02)
	root.add_child(num)
	if state == "locked":
		root.modulate = Color(0.6, 0.6, 0.66)
	elif state == "blocked":
		root.modulate = Color(0.36, 0.36, 0.4)
		var lk := _icon(ICON_LOCK, int(sz * 0.42))
		lk.position = Vector2(sz * 0.29, sz * 0.29)
		lk.size = Vector2(sz * 0.42, sz * 0.42)
		root.add_child(lk)
	_ignore_mouse(root)
	return root


## The five tiers of a placed tower as a row of small pictures: bought ones lit, the next one framed in gold.
func _tier_track(t: Dictionary) -> Control:
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 6)
	var lvl := int(t.level)
	var br := str(t.branch)
	for tier in range(1, 6):
		if tier > 2 and br == "":
			var q := PanelContainer.new()            # path not chosen yet
			q.custom_minimum_size = Vector2(52, 52)
			q.add_theme_stylebox_override("panel", _style(Color(0.1, 0.12, 0.17), 10, Color(0.3, 0.34, 0.42), 2))
			var ql := _label("A/B" if tier == 3 else ROMAN[tier], 17, Color(0.6, 0.65, 0.75))
			ql.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			ql.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			q.add_child(ql)
			row.add_child(q)
			continue
		var st := "owned" if tier <= lvl else ("next" if tier == lvl + 1 else "locked")
		row.add_child(_upgrade_art(str(t.type), br, tier, 52, st))
	return row


## A buyable upgrade, BTD6 style: its picture, name, what it does, and the price (red when you can't afford it).
func _upgrade_card(tid: String, o: Dictionary, tier: int, tower_id: int, tall := false) -> Button:
	var key := str(o.key)
	var pc := _path_color(key, tier)
	var b := Button.new()
	for stn in ["normal", "disabled"]:
		b.add_theme_stylebox_override(stn, _style(pc.darkened(0.55), 16, pc, 3))
	b.add_theme_stylebox_override("hover", _style(pc.darkened(0.4), 16, pc.lightened(0.3), 3))
	b.add_theme_stylebox_override("pressed", _style(pc.darkened(0.3), 16, C_GOLD, 3))
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.custom_minimum_size = Vector2(0, 104)
	b.clip_contents = true
	var hb: BoxContainer = VBoxContainer.new() if tall else HBoxContainer.new()   # tall: the two path choices side by side
	hb.set_anchors_preset(Control.PRESET_TOP_WIDE)        # full width; the card grows to fit the text
	hb.offset_left = 8
	hb.offset_top = 8
	hb.offset_right = -8
	hb.add_theme_constant_override("separation", 4 if tall else 10)
	b.add_child(hb)
	var art := _upgrade_art(tid, key, tier, 76 if tall else 88, "next")
	art.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	art.size_flags_horizontal = Control.SIZE_SHRINK_CENTER if tall else Control.SIZE_FILL
	hb.add_child(art)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 0)
	hb.add_child(v)
	# top line: which tier / path, and the price (always visible, red when you can't afford it)
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 4)
	v.add_child(top)
	var head := ("PATH %s" % key) if tall else (("PATH %s  -  TIER %s" % [key, ROMAN[tier]]) if tier > 2 else ("TIER %s" % ROMAN[tier]))
	var hl := _label(head, 15, pc.lightened(0.5))
	hl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hl.clip_text = true
	top.add_child(hl)
	top.add_child(_icon(ICON_GOLD, 22 if tall else 24))
	var cl := _label(str(int(o.cost)), 20 if tall else 22, Color(0.75, 1.0, 0.6))
	top.add_child(cl)
	var nm := _label(str(o.name), 19 if tall else 22, C_GOLD)
	nm.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(nm)
	var ds := _label(str(o.desc), 14 if tall else 16, Color(0.86, 0.9, 0.95))
	ds.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(ds)
	var fit := func():                                     # wrap first, then grow the card to fit
		b.custom_minimum_size.y = maxf(104.0, hb.get_combined_minimum_size().y + 16.0)
	hb.minimum_size_changed.connect(fit)
	hb.resized.connect(fit)
	_ignore_mouse(hb)
	b.set_meta("cost", int(o.cost))
	b.set_meta("cost_lbl", cl)
	b.pressed.connect(func():
		if not sim.upgrade_tower(tower_id, key):
			_toast("Not enough gold", Color(1, 0.45, 0.4))
			_sfx("error", -4.0, 0.0)
		_handle_events())
	return b


## One node of an upgrade tree: picture, name, price and what it does (fixed size, so trees line up).
func _tree_node(tid: String, key: String, tier: int, sz: int, state: String) -> Control:
	var u := _tier_def(tid, key, tier)
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(sz + 78, 0)
	v.add_theme_constant_override("separation", 2)
	var art := _upgrade_art(tid, key, tier, sz, state)
	art.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(art)
	v.set_meta("art", art)
	var nm := _label(str(u.name), 16, C_GOLD if state != "blocked" else Color(0.6, 0.6, 0.65))
	nm.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	nm.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	nm.custom_minimum_size = Vector2(sz + 78, 22)
	v.add_child(nm)
	var cr := HBoxContainer.new()
	cr.alignment = BoxContainer.ALIGNMENT_CENTER
	cr.add_theme_constant_override("separation", 4)
	cr.add_child(_icon(ICON_GOLD, 20))
	cr.add_child(_label(str(int(u.cost)), 17, Color(0.95, 0.85, 0.45)))
	v.add_child(cr)
	var ds := _label(str(u.desc), 14, Color(0.82, 0.86, 0.92))
	ds.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ds.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ds.custom_minimum_size = Vector2(sz + 78, 38)
	v.add_child(ds)
	return v


## Arrow from the middle of one node's picture to the next (or, for the fork, to both paths).
func _tree_link(w: float, from_node: Control, to_nodes: Array, col := Color(0.85, 0.88, 0.95, 0.85)) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(w, 0)
	c.size_flags_vertical = Control.SIZE_EXPAND_FILL
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.draw.connect(func():
		var inv := c.get_global_transform().affine_inverse()
		var fa: Control = from_node.get_meta("art")
		var p0: Vector2 = inv * (fa.get_global_rect().get_center())
		p0.x = 2.0
		for tn in to_nodes:
			var ta: Control = (tn as Control).get_meta("art")
			var p1: Vector2 = inv * (ta.get_global_rect().get_center())
			p1.x = c.size.x - 4.0
			var mid_x := c.size.x * 0.45
			var pts := PackedVector2Array([p0, Vector2(mid_x, p0.y), Vector2(mid_x, p1.y), p1 - Vector2(10, 0)])
			c.draw_polyline(pts, Color(0.02, 0.04, 0.1, 0.9), 9.0, true)
			c.draw_polyline(pts, col, 5.0, true)
			c.draw_colored_polygon(PackedVector2Array([p1, p1 + Vector2(-14, -9), p1 + Vector2(-14, 9)]), col))
	return c


## A tower's whole upgrade tree: tiers I and II, then the fork into Path A and Path B (tiers III to V).
## With `t` (a placed tower) it shows what's bought, what's next and which path is locked.
func _upgrade_tree(tid: String, sz: int, t = null) -> Control:
	var d: Dictionary = defs.towers[tid]
	var lvl := int(t.level) if t != null else 0
	var br := str(t.branch) if t != null else ""
	var st := func(key: String, tier: int) -> String:
		if t == null:
			return "open"
		if tier > 2 and br != "" and key != br:
			return "blocked"
		if tier <= lvl:
			return "owned"
		if tier == lvl + 1:
			return "next"
		return "locked"
	var root := HBoxContainer.new()
	root.alignment = BoxContainer.ALIGNMENT_CENTER
	root.add_theme_constant_override("separation", 0)
	var n1 := _tree_node(tid, "", 1, sz, st.call("", 1))
	var n2 := _tree_node(tid, "", 2, sz, st.call("", 2))
	for n in [n1, n2]:
		n.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	root.add_child(n1)
	root.add_child(_tree_link(34, n1, [n2]))
	root.add_child(n2)
	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 6)
	var firsts := []
	var links := []
	for key in ["A", "B"]:
		var pc := _path_color(key, 3)
		var hdr := _label("PATH %s:  %s" % [key, str(d.branches[key].name).to_upper()], 18, pc.lightened(0.45))
		hdr.custom_minimum_size = Vector2(0, 26)
		rows.add_child(hdr)
		var r := HBoxContainer.new()
		r.add_theme_constant_override("separation", 0)
		rows.add_child(r)
		var prev: Control = null
		for tier in [3, 4, 5]:
			var nd := _tree_node(tid, key, tier, sz, st.call(key, tier))
			if prev != null:
				var lk := _tree_link(34, prev, [nd], pc.lightened(0.35))
				r.add_child(lk)
				links.append(lk)
			r.add_child(nd)
			if tier == 3:
				firsts.append(nd)
			prev = nd
	var fork := _tree_link(56, n2, firsts)
	root.add_child(fork)
	root.add_child(rows)
	links.append(fork)
	var redraw := func():
		for l in links:
			if is_instance_valid(l):
				(l as Control).queue_redraw()
	rows.resized.connect(redraw)
	root.resized.connect(redraw)
	for dly in [0.05, 0.2, 0.5]:                 # once the dialog has settled its layout
		get_tree().create_timer(dly).timeout.connect(redraw)
	return root


## TECH TREE: every tower's full upgrade tree, age by age. Ages you haven't reached stay locked. Since v0.9.18 it has no
## button (each tower's tree shows on its details card in the Towers screen); kept for --shoot-tech.
func _open_techtree(era: String, tid: String, reuse: Control = null) -> void:
	if era == "" or not Progress.is_unlocked(_first_map_of(era)):
		era = str(_map_entry(_menu_map()).get("era", "Stone Age"))
	var towers: Array = Progress.era_towers(era)
	if tid == "" or not (tid in towers):
		tid = str(towers[0])
	var dlg: Control = reuse if reuse != null and is_instance_valid(reuse) else _modal(ui_root, 0.6)
	var box: VBoxContainer = dlg.get_meta("box")
	_clear_box(box)
	dlg.set_meta("full_h", true)
	box.set_meta("want_w", 1500.0)
	box.add_theme_constant_override("separation", 10)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 24)
	box.add_child(head)
	var ttl := _label("TECH TREE  -  %s" % era.to_upper(), 44, C_GOLD, 12)
	ttl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ttl.clip_text = true
	head.add_child(ttl)
	var done := _button("DONE", Color(0.2, 0.58, 0.18), 30)
	done.custom_minimum_size = Vector2(200, 62)
	done.pressed.connect(func():
		_sfx("click")
		dlg.queue_free())
	head.add_child(done)
	_close_with(dlg, done)
	var tabs := HBoxContainer.new()             # one row of short age names keeps the whole tree on screen
	tabs.add_theme_constant_override("separation", 6)
	tabs.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_child(tabs)
	for en in _eras():
		var open := Progress.is_unlocked(_first_map_of(en))
		var short: String = str(en).to_upper().replace(" AGE", "").replace("THE ", "")
		var tb := _button(short if open else "", Color(0.2, 0.36, 0.6) if en == era else (Color(0.16, 0.24, 0.38) if open else Color(0.12, 0.14, 0.18)), 15)
		tb.custom_minimum_size = Vector2(126, 46)
		tb.clip_text = true
		if not open:
			tb.disabled = true
			tb.icon = ICON_LOCK
			tb.add_theme_constant_override("icon_max_width", 26)
		elif en == era:
			tb.add_theme_color_override("font_color", C_GOLD)
		tb.pressed.connect(func():
			if en == era:
				return
			_sfx("click")
			_open_techtree(en, "", dlg))
		tabs.add_child(tb)
	# the age's four towers: pick one to see its tree
	var picks := HBoxContainer.new()
	picks.alignment = BoxContainer.ALIGNMENT_CENTER
	picks.add_theme_constant_override("separation", 14)
	box.add_child(picks)
	for ot in towers:
		var sel: bool = ot == tid
		var pb := _button("", Color(0.22, 0.4, 0.66) if sel else Color(0.14, 0.2, 0.3), 18)
		pb.custom_minimum_size = Vector2(300, 72)
		var ph := HBoxContainer.new()
		ph.set_anchors_preset(Control.PRESET_FULL_RECT)
		ph.offset_left = 8
		ph.offset_right = -8
		ph.add_theme_constant_override("separation", 8)
		pb.add_child(ph)
		ph.add_child(_icon(_icon_tex(str(ot)), 60))
		var pv := VBoxContainer.new()
		pv.alignment = BoxContainer.ALIGNMENT_CENTER
		pv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		ph.add_child(pv)
		var pn := _label(str(defs.towers[ot].name), 20, C_GOLD if sel else C_TEXT)
		pn.clip_text = true
		pv.add_child(pn)
		var lin := str(defs.towers[ot].lineage)
		pv.add_child(_label(lin + ("" if Progress.tower_unlocked(str(ot)) else "  (locked)"), 15, Color(0.7, 0.76, 0.86)))
		_ignore_mouse(ph)
		pb.pressed.connect(func():
			if sel:
				return
			_sfx("click")
			_open_techtree(era, str(ot), dlg))
		picks.add_child(pb)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _style(Color(0.06, 0.08, 0.12), 18, Color(0.22, 0.3, 0.44), 3))
	panel.custom_minimum_size = Vector2(0, 470)
	box.add_child(panel)
	var pv2 := VBoxContainer.new()
	pv2.add_theme_constant_override("separation", 6)
	panel.add_child(pv2)
	var d: Dictionary = defs.towers[tid]
	var th := _label("%s  -  %s   Tiers I-II, then Path A or B (the other locks)." % [str(d.name).to_upper(), str(d.desc)], 19, C_TEXT)
	th.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	th.clip_text = true
	pv2.add_child(th)
	var tree := _upgrade_tree(tid, 84)
	tree.size_flags_vertical = Control.SIZE_EXPAND_FILL
	pv2.add_child(tree)


## Tower card: model, attack stats, specials, upgrade paths, pros and cons.
func _tower_detail(tid: String) -> void:
	var d: Dictionary = defs.towers[tid]
	var b: Dictionary = d.base
	var dlg := _modal(ui_root, 0.7)
	var box: VBoxContainer = dlg.get_meta("box")
	box.set_meta("want_w", 1350.0)
	box.add_theme_constant_override("separation", 12)
	detail_open += 1
	dlg.tree_exiting.connect(func(): detail_open = maxi(0, detail_open - 1))
	_on_close(dlg, func():
		_sfx("click")
		dlg.queue_free())
	var col := Color(d.color[0], d.color[1], d.color[2])
	var ttl := _label(str(d.name).to_upper(), 52, col.lightened(0.4), 12)
	ttl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(ttl)
	var roles := {"Ranged": "single-target damage", "Control": "slows, stuns and spotting", "Brute": "close-range area damage", "Siege": "splash and long range"}
	var sub := _label("%s tower (%s)   -   %s   -   %d gold" % [d.lineage, roles.get(str(d.lineage), ""), d.era, int(d.cost)], 24, C_GOLD, 7)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(sub)
	var row := HFlowContainer.new()
	row.alignment = FlowContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("h_separation", 26)
	box.add_child(row)
	var stage := PanelContainer.new()
	var ssb := _style(Color(col.darkened(0.6), 0.85), 24, col.darkened(0.2), 5)
	stage.add_theme_stylebox_override("panel", ssb)
	row.add_child(stage)
	stage.add_child(_model_viewer("res://assets/towers/%s.glb" % tid, Vector2(360, 400)))
	var info := VBoxContainer.new()
	info.custom_minimum_size = Vector2(760, 0)
	info.add_theme_constant_override("separation", 6)
	row.add_child(info)
	var ds := _label(str(d.desc), 24, C_TEXT, 6)
	ds.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_child(ds)
	# attack stats as chips
	var kinds := {"projectile": "Shoots", "melee": "Melee", "pulse": "Pulse (hits all around it)", "lob": "Lobs explosive shells"}
	var chips := HFlowContainer.new()
	chips.add_theme_constant_override("h_separation", 10)
	chips.add_theme_constant_override("v_separation", 8)
	info.add_child(chips)
	var tech := Progress.tech_mult(str(d.era)) if not test_mode else 1.0
	var stats := [
		["ATTACK", str(kinds.get(str(b.kind), b.kind))],
		["DAMAGE", "%s %s" % [str(snappedf(float(b.damage) * tech, 0.1)), str(b.get("dtype", "")).capitalize()]],
		["RANGE", "%.1f tiles" % float(b.range)],
		["SPEED", "%.1f attacks/sec" % (1.0 / maxf(0.05, float(b.cooldown)))],
		["FLYING", "Can hit" if sim.can_hit_air(b) else "Can't hit"],
		["CLOAKED", "Spots them" if (float(b.get("detect", 0.0)) > 0.0 or str(b.kind) == "pulse") else "Needs a spotter"],
	]
	if float(b.get("splash", 0.0)) > 0.0:
		stats.append(["SPLASH", "%.1f tiles" % float(b.splash)])
	if int(b.get("max_targets", 0)) > 1:
		stats.append(["TARGETS", "%d per hit" % int(b.max_targets)])
	for st in stats:
		var chip := PanelContainer.new()
		var csb := _style(Color(0.05, 0.07, 0.11), 12, col.darkened(0.3), 3)
		csb.content_margin_left = 12
		csb.content_margin_right = 12
		csb.content_margin_top = 4
		csb.content_margin_bottom = 4
		chip.add_theme_stylebox_override("panel", csb)
		var cv := VBoxContainer.new()
		cv.add_theme_constant_override("separation", -4)
		chip.add_child(cv)
		cv.add_child(_label(str(st[0]), 15, Color(0.6, 0.66, 0.75), 4))
		cv.add_child(_label(str(st[1]), 21, Color.WHITE, 5))
		chips.add_child(chip)
	if tech > 1.0:
		info.add_child(_label("Damage includes your +%d%% tech bonus for this age." % int(round((tech - 1.0) * 100)), 17, Color(0.6, 0.9, 1.0), 4))
	var pc := _tower_pros_cons(d)
	var pcrow := HBoxContainer.new()
	pcrow.add_theme_constant_override("separation", 24)
	info.add_child(pcrow)
	var pv := VBoxContainer.new()
	pv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pcrow.add_child(pv)
	pv.add_child(_label("PROS", 24, Color(0.55, 1.0, 0.5), 7))
	for t in pc[0]:
		var l := _label("+  " + str(t), 19, Color(0.8, 1.0, 0.78), 5)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		pv.add_child(l)
	var cv2 := VBoxContainer.new()
	cv2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pcrow.add_child(cv2)
	cv2.add_child(_label("CONS", 24, Color(1.0, 0.5, 0.45), 7))
	for t in pc[1]:
		var l2 := _label("-  " + str(t), 19, Color(1.0, 0.82, 0.78), 5)
		l2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		cv2.add_child(l2)
	# upgrade tree: tiers I-II, then Path A or Path B
	box.add_child(_label("UPGRADE TREE", 30, C_GOLD, 8))
	var tree_p := PanelContainer.new()
	tree_p.add_theme_stylebox_override("panel", _style(Color(0.06, 0.08, 0.12), 18, Color(0.22, 0.3, 0.44), 3))
	box.add_child(tree_p)
	tree_p.add_child(_upgrade_tree(tid, 88))
	var note := _label("At tier 3 you pick Path A or Path B. The other path locks for that tower.", 17, Color(1, 0.75, 0.5), 4)
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(note)
	var back := _button("CLOSE", Color(0.18, 0.27, 0.43), 28)
	back.custom_minimum_size = Vector2(260, 80)
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	back.pressed.connect(func():
		_sfx("click")
		dlg.queue_free())
	box.add_child(back)
	dlg.get_parent().move_child(dlg, -1)


## Hero card: model, story, pros and cons, then PLAY AS (owned) or LOCKED + BUY (not owned yet).
func _hero_detail(hid: String, picker_box: VBoxContainer) -> void:
	var hd: Dictionary = defs.heroes.heroes[hid]
	var dlg := _modal(ui_root, 0.7)
	var box: VBoxContainer = dlg.get_meta("box")
	box.set_meta("want_w", 1250.0)
	box.add_theme_constant_override("separation", 14)
	_on_close(dlg, func():
		_sfx("click")
		dlg.queue_free())
	detail_open += 1
	dlg.tree_exiting.connect(func(): detail_open = maxi(0, detail_open - 1))
	dlg.set_meta("hero_detail", hid)
	var col := Color(hd.color[0], hd.color[1], hd.color[2])
	var ttl := _label(str(hd.name).to_upper(), 52, col.lightened(0.35), 12)
	ttl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(ttl)
	var sub := _label("%s   -   %s" % [hd.title, hd.era], 26, C_GOLD, 7)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(sub)
	# persistent hero level
	var hl := Progress.hero_level(hid)
	var hmx := hl >= int(Progress.workshop.hero_levels.max)
	var hpr := Progress.hero_level_progress(hid)
	var lrow := HBoxContainer.new()
	lrow.alignment = BoxContainer.ALIGNMENT_CENTER
	lrow.add_theme_constant_override("separation", 14)
	box.add_child(lrow)
	lrow.add_child(_label("LEVEL %d / %d" % [hl, int(Progress.workshop.hero_levels.max)], 28, Color(0.6, 0.9, 1.0), 7))
	var lpb := ProgressBar.new()
	lpb.show_percentage = false
	lpb.custom_minimum_size = Vector2(320, 26)
	lpb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	lpb.max_value = maxf(float(hpr[1]), 1.0)
	lpb.value = float(hpr[0]) if not hmx else lpb.max_value
	var lfill := _style(Color(0.3, 0.75, 1.0), 9)
	lfill.shadow_size = 0
	var lbg := _style(Color(0.04, 0.07, 0.12), 9)
	lbg.shadow_size = 0
	lpb.add_theme_stylebox_override("fill", lfill)
	lpb.add_theme_stylebox_override("background", lbg)
	lrow.add_child(lpb)
	lrow.add_child(_label("MAX" if hmx else "%d / %d XP" % [hpr[0], hpr[1]], 20, Color(0.8, 0.86, 0.95), 5))
	var lb := _label("Level bonus: %s%s" % [Progress.hero_level_bonus_text(hl), "" if hmx else ".  Next level: " + Progress.hero_level_bonus_text(hl + 1)], 19, Color(0.7, 0.85, 1.0), 4)
	lb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(lb)
	var row := HFlowContainer.new()
	row.alignment = FlowContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("h_separation", 28)
	box.add_child(row)
	var stage := PanelContainer.new()
	var ssb := _style(col.darkened(0.55), 24, col.darkened(0.2), 5)
	ssb.bg_color = Color(col.darkened(0.6), 0.85)
	stage.add_theme_stylebox_override("panel", ssb)
	row.add_child(stage)
	stage.add_child(_hero_viewer(hid, Vector2(380, 430)))
	var info := VBoxContainer.new()
	info.custom_minimum_size = Vector2(700, 0)
	info.add_theme_constant_override("separation", 8)
	row.add_child(info)
	var blurb := _label(str(hd.blurb), 24, C_TEXT, 6)
	blurb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_child(blurb)
	var ab: Dictionary = hd.ability
	var abl := _label("ABILITY: %s  (every %ds, from rank %d in a match)\n%s" % [str(ab.name).to_upper(), int(ab.cooldown), int(ab.get("unlock", 3)), ab.desc], 21, Color(0.75, 0.88, 1.0), 6)
	abl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_child(abl)
	var pc := _hero_pros_cons(hd)
	info.add_child(_label("PROS", 24, Color(0.55, 1.0, 0.5), 7))
	for t in pc[0]:
		var l := _label("+  " + str(t), 20, Color(0.8, 1.0, 0.78), 5)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		info.add_child(l)
	info.add_child(_label("CONS", 24, Color(1.0, 0.5, 0.45), 7))
	for t in pc[1]:
		var l2 := _label("-  " + str(t), 20, Color(1.0, 0.82, 0.78), 5)
		l2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		info.add_child(l2)
	var note := _label("Every hero fights at full strength in any age. Heros gain XP only from robots they destroy themselves.", 18, Color(0.68, 0.75, 0.85), 5)
	info.add_child(note)
	var btns := HBoxContainer.new()
	btns.alignment = BoxContainer.ALIGNMENT_CENTER
	btns.add_theme_constant_override("separation", 24)
	box.add_child(btns)
	var owned := Progress.hero_owned(hid)
	if started:
		var close := _button("BACK TO THE FIGHT", Color(0.2, 0.58, 0.18), 30)
		close.custom_minimum_size = Vector2(420, 88)
		close.pressed.connect(func():
			_sfx("click")
			dlg.queue_free())
		btns.add_child(close)
	elif owned:
		var is_cur := Progress.hero() == hid
		var play := _button("PLAYING AS %s" % _short_name(str(hd.name)).to_upper() if is_cur else "PLAY AS %s" % _short_name(str(hd.name)).to_upper(), Color(0.2, 0.58, 0.18), 32)
		play.custom_minimum_size = Vector2(460, 92)
		play.disabled = is_cur
		play.pressed.connect(func():
			_sfx("level_up")
			Progress.set_hero(hid)
			dlg.queue_free()
			_refresh_hero_pickers(picker_box))
		btns.add_child(play)
		var back := _button("BACK", Color(0.18, 0.27, 0.43), 30)
		back.custom_minimum_size = Vector2(240, 92)
		back.pressed.connect(func():
			_sfx("click")
			dlg.queue_free())
		btns.add_child(back)
	else:
		var cost := Progress.hero_cost(hd, defs.heroes.heroes)
		var avail := Progress.hero_available(hd)
		var have := Progress.shards()
		btns.add_child(_hero_price_button(hd, picker_box, Vector2(420, 92), 32))
		var back2 := _button("BACK", Color(0.24, 0.3, 0.44), 30)
		back2.custom_minimum_size = Vector2(240, 92)
		back2.pressed.connect(func():
			_sfx("click")
			dlg.queue_free())
		btns.add_child(back2)
		var why := "Reach the %s to unlock %s. " % [str(hd.era), _short_name(str(hd.name))] if not avail else ""
		var wallet := _label("%sYou have %d Time Shards.%s" % [why, have, ("  Need %d more: earn them by playing maps and leveling up heros." % (cost - have)) if avail and have < cost else ""], 20, Color(0.8, 0.72, 1.0), 5)
		wallet.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		wallet.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(wallet)
	# action buttons (PLAY AS / buy) sit right under the level bar so they never need scrolling
	box.move_child(btns, lb.get_index() + 1)
	if box.get_child(box.get_child_count() - 1) is Label and btns.get_index() < box.get_child_count() - 1:
		box.move_child(box.get_child(box.get_child_count() - 1), btns.get_index() + 1)
	dlg.get_parent().move_child(dlg, -1)


func _open_heroes() -> void:
	if heroes_panel != null and is_instance_valid(heroes_panel):
		heroes_panel.queue_free()
	heroes_panel = _modal(ui_root, 0.6)
	heroes_panel.set_meta("full_h", true)
	var box: VBoxContainer = heroes_panel.get_meta("box")
	box.set_meta("want_w", 1350.0)
	box.add_theme_constant_override("separation", 14)
	var head := HBoxContainer.new()
	box.add_child(head)
	var ttl := _label("HEROS", 60, C_GOLD, 14)
	ttl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(ttl)
	var done := _button("DONE", Color(0.2, 0.58, 0.18), 30)
	done.custom_minimum_size = Vector2(200, 70)
	done.pressed.connect(func():
		_sfx("click")
		heroes_panel.queue_free()
		_refresh_menus())
	head.add_child(done)
	_close_with(heroes_panel, done)
	var intro := _label("Your hero joins every match for free. Each age brings new heros to buy with Time Shards, which you earn from maps and hero level-ups. Every hero levels up (to 10) from the robots it destroys itself.", 22, Color(0.78, 0.83, 0.9), 5)
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(intro)
	var picker := _hero_picker(box)
	var grant := _button("+%d SHARDS (test)" % int(Progress.workshop.shards.test_grant), Color(0.36, 0.26, 0.5), 18)
	grant.custom_minimum_size = Vector2(240, 60)
	grant.pressed.connect(func():
		_sfx("click")
		Progress.add_shards(int(Progress.workshop.shards.test_grant))
		_refresh_hero_pickers(picker))
	head.add_child(grant)
	head.move_child(grant, 1)
	heroes_panel.get_parent().move_child(heroes_panel, -1)


func _eras() -> Array:
	var out := []
	for m in Defs.map_list():
		if not str(m.era) in out:
			out.append(str(m.era))
	return out


func _build_map_select(root: Control) -> void:
	map_select = _modal(root, 0.6)
	map_select.set_meta("full_h", true)
	var box: VBoxContainer = map_select.get_meta("box")
	box.set_meta("want_w", 1300.0)
	box.add_theme_constant_override("separation", 14)
	if Progress.timeline() > 1:
		var tl := _label("TIMELINE %d   -   robots +%d%% tougher" % [Progress.timeline(),
			int(round((Progress.timeline_hp_mult() - 1.0) * 100))], 26, Color(0.85, 0.6, 1.0), 7)
		tl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		box.add_child(tl)
	# era tabs
	var tabs := HFlowContainer.new()
	tabs.alignment = FlowContainer.ALIGNMENT_CENTER
	tabs.add_theme_constant_override("h_separation", 10)
	tabs.add_theme_constant_override("v_separation", 10)
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
		var tbtn := _button(era_name.to_upper(), Color(0.18, 0.28, 0.46) if era_open else Color(0.18, 0.21, 0.27), 20)
		tbtn.custom_minimum_size = Vector2(244, 58)
		tbtn.set_meta("open", era_open)
		tabs.add_child(tbtn)
		tab_buttons[era_name] = tbtn
		if era_open:
			if default_tab == "" or not Progress.is_unlocked(_first_map_of(default_tab)):
				default_tab = era_name
	var show_tab := func(era_name: String) -> void:
		for k in rows:
			rows[k].visible = k == era_name
			var b: Button = tab_buttons[k]
			b.modulate = Color(1.25, 1.2, 0.95) if k == era_name else (Color(0.8, 0.8, 0.8) if b.get_meta("open") else Color(0.55, 0.55, 0.55))
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
	_hero_picker(box)
	var hint := _label("Beat a map to unlock the next.  Stars: 1 = win, 2 = lose 50 lives or fewer, 3 = lose 10 or fewer.  Your hero joins every match for free.", 18, Color(0.68, 0.75, 0.85), 5)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(hint)
	var brow := HFlowContainer.new()
	brow.alignment = FlowContainer.ALIGNMENT_CENTER
	brow.add_theme_constant_override("h_separation", 14)
	brow.add_theme_constant_override("v_separation", 10)
	box.add_child(brow)
	var m_back := _button("BACK", Color(0.2, 0.28, 0.43), 22)
	m_back.custom_minimum_size = Vector2(160, 60)
	m_back.pressed.connect(func():
		_sfx("click")
		map_select.visible = false
		title_screen.visible = true)
	brow.add_child(m_back)
	_close_with(map_select, m_back)
	var m_work := _button("TOWERS", Color(0.18, 0.28, 0.47), 22)
	m_work.custom_minimum_size = Vector2(220, 60)
	m_work.pressed.connect(func():
		_sfx("click")
		_open_workshop(""))
	brow.add_child(m_work)
	var pts := Progress.points_free()
	var m_legacy := _button("UPGRADES%s" % [("  (%d!)" % pts) if pts > 0 else ""],
		Color(0.18, 0.42, 0.6), 22)
	m_legacy.custom_minimum_size = Vector2(300, 60)
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
	card.add_theme_stylebox_override("panel", _style(Color(0.09, 0.15, 0.25) if unlocked else Color(0.1, 0.13, 0.18), 20,
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
	v.add_child(_label(str(m.name), 32, C_TEXT if unlocked else Color(0.43, 0.51, 0.63), 8))
	v.add_child(_label("MAP %d OF %d" % [map_order.find(str(m.id)) + 1, map_order.size()], 20, Color(0.63, 0.71, 0.82), 6))
	var bl := _label(str(m.blurb), 17, Color(0.78, 0.83, 0.9), 5)
	bl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	bl.custom_minimum_size = Vector2(362, 60)
	v.add_child(bl)
	var stars := HBoxContainer.new()
	for k in 3:
		stars.add_child(_icon(ICON_STAR if k < Progress.stars(mid) else ICON_STAR_EMPTY, 36))
	v.add_child(stars)
	var rb := _button("ROBOTS", Color(0.55, 0.2, 0.22), 20)
	rb.custom_minimum_size = Vector2(0, 52)
	var rmid := str(m.id)
	rb.pressed.connect(func():
		_sfx("click")
		_robot_roster(rmid))
	v.add_child(rb)
	var go := _button("PLAY" if unlocked else "LOCKED", Color(0.2, 0.58, 0.18) if unlocked else Color(0.21, 0.25, 0.32), 28)
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
	var sb := _style(Color(0.06, 0.1, 0.17, 1.0), 30, C_PANEL_EDGE, 6)
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
	shade.set_meta("panel", panel)
	# red X in the corner: every dialog can be closed (its action is set with _on_close)
	var xb := _button("X", Color(0.8, 0.12, 0.1), 36)
	xb.custom_minimum_size = Vector2(76, 76)
	xb.size = Vector2(76, 76)
	xb.visible = false
	shade.add_child(xb)
	xb.pressed.connect(func():
		var cb: Callable = shade.get_meta("on_close", Callable())
		if cb.is_valid():
			cb.call())
	shade.set_meta("x", xb)
	modals.append(shade)
	_reveal(shade)
	return shade


## Dialogs stay invisible for a few frames while their size settles, then fade in:
## no visible jump or shake when they open or when a tab rebuilds them.
func _reveal(shade: Control) -> void:
	shade.modulate.a = 0.0
	shade.set_meta("age", 0)


func _clear_box(box: Node) -> void:
	for c in box.get_children():
		box.remove_child(c)
		c.queue_free()


## Rebuild the main-menu screens in place (after buying/unlocking) instead of reloading the
## whole scene: no freeze, the 3D hub keeps running.
func _refresh_menus() -> void:
	if started or title_screen == null or not is_instance_valid(title_screen):
		return
	var root := title_screen.get_parent()
	var ti := title_screen.get_index()
	var mi := map_select.get_index() if map_select != null and is_instance_valid(map_select) else -1
	var title_vis := title_screen.visible
	var ms_vis := map_select.visible if mi != -1 else false
	title_screen.queue_free()
	if mi != -1:
		modals.erase(map_select)
		map_select.queue_free()
	_build_main_menu(root)
	root.move_child(title_screen, ti)
	_build_map_select(root)
	if mi != -1:
		root.move_child(map_select, mi)
	title_screen.visible = title_vis
	map_select.visible = ms_vis


## What the dialog's red X does (usually: the same as its DONE / BACK button).
func _on_close(shade: Control, cb: Callable) -> void:
	shade.set_meta("on_close", cb)
	(shade.get_meta("x") as Button).visible = true


func _close_with(shade: Control, b: Button) -> void:
	_on_close(shade, func(): b.pressed.emit())


## Keeps every open dialog inside the screen: narrower when the UI is scaled up, scrollable when too tall.
func _fit_modals() -> void:
	if ui_root == null:
		return
	var vp := ui_root.size
	if Engine.get_process_frames() % 30 == 0:
		modals = modals.filter(func(x): return is_instance_valid(x))
	for m in modals:
		if not is_instance_valid(m) or not m.visible:
			continue
		var box: VBoxContainer = m.get_meta("box")
		var scroll: ScrollContainer = m.get_meta("scroll")
		var w := minf(float(box.get_meta("want_w", 900.0)), vp.x - 120.0)
		box.custom_minimum_size.x = w
		var need := box.get_combined_minimum_size().y
		if bool(m.get_meta("full_h", false)):
			need = vp.y - 110.0          # big screens keep one size, so switching tabs can't make them jump
		var bar := 26.0 if need >= vp.y - 110.0 else 0.0
		scroll.custom_minimum_size = Vector2(w + bar, minf(need, vp.y - 110.0))
		var age := int(m.get_meta("age", 99))
		if age < 99:
			age += 1
			m.set_meta("age", age)
			if age == 3:
				var tw: Tween = (m as Node).create_tween()
				tw.tween_property(m, "modulate:a", 1.0, 0.12)
				m.set_meta("age", 99)
		var xb: Button = m.get_meta("x")
		if xb.visible:
			var pr := (m.get_meta("panel") as Control).get_rect()
			var cc := (m.get_meta("panel") as Control).get_parent() as Control
			pr.position += cc.position
			xb.position = Vector2(pr.end.x - 56.0, pr.position.y - 20.0)


func _start_game() -> void:
	started = true
	title_screen.visible = false
	map_select.visible = false
	if not demo:
		music.play()
	_sfx("click")
	if not demo and _first_visit():
		_robot_roster(map_id, true)
		return
	_toast("Place your hero (free), then pick towers on the right", C_TEXT)
	toast_t = 4.5
	if not demo:
		_path_preview(true)


## True the first time this map is entered. Old saves first count robots from maps already beaten as met.
func _first_visit() -> bool:
	if not Progress.seen_ready():
		for m in map_order:
			if Progress.stars(m) > 0 or m in Progress.data.get("cleared", []):
				var ts := []
				for pair in _map_robots(m):
					ts.append(pair[0])
				Progress.mark_seen(m, ts, false)
		Progress.mark_seen("", [])
	return not Progress.map_seen(map_id)


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
		tower_icon.texture = _face_tex(sim.hero_id)
		lbl_t_name.text = str(hd.name)
		var nxt := "MAX" if t.level >= sim.hero_levels.size() else "%d/%d XP" % [int(t.xp), int(sim.hero_levels[t.level])]
		lines = "%s  -  Hero Level %d  -  Rank %d (%s)\n" % [hd.title, sim.hero_plevel, t.level, nxt]
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
		if int(s.get("chain", 0)) > 0:
			lines += "\nJumps to %d more robots" % int(s.chain)
		if float(s.get("burn", 0.0)) > 0.0:
			lines += "\nBurns for %s damage/sec" % str(snappedf(float(s.burn), 0.1))
		if float(s.get("shield_break", 0.0)) > 0.0:
			lines += "\nKnocks out robot shields"
		if float(s.get("detect", 0.0)) > 0.0 or s.kind == "pulse":
			lines += "\nSpots cloaked robots"
		if not sim.can_hit_air(s):
			lines += "\nCan't hit flying robots"
		elif float(s.get("anti_air", 0.0)) > 0.0:
			lines += "\nHits flying robots"
		if t.buffed:
			lines += "\nBoosted by your hero!"
		if t.branch != "":
			lines += "\nPath %s: %s" % [t.branch, def.branches[t.branch].name]
		up_box.add_child(_tier_track(t))
		var opts := sim.upgrade_options(t)
		if opts.is_empty():
			var mx := _label("FULLY UPGRADED", 30, C_GOLD)
			mx.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			up_box.add_child(mx)
		if opts.size() == 2:                    # the path choice: both paths side by side
			var ch := _label("PICK A PATH  -  the other one locks", 17, Color(1, 0.78, 0.45))
			ch.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			ch.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			up_box.add_child(ch)
			var pair := HBoxContainer.new()
			pair.add_theme_constant_override("separation", 8)
			up_box.add_child(pair)
			for o in opts:
				var tc := _upgrade_card(str(t.type), o, int(t.level) + 1, id, true)
				tc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				pair.add_child(tc)
		else:
			for o in opts:
				up_box.add_child(_upgrade_card(str(t.type), o, int(t.level) + 1, id))
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
	if attract:
		return
	toast.text = text
	toast.add_theme_color_override("font_color", col)
	toast_t = 2.4


func _banner(text: String, col: Color) -> void:
	if attract:
		return
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
	lbl_hero_level.text = "Rank %d" % sim.hero.level
	hero_xp_fill.size.x = 130.0 * sim.hero_xp_progress()
	_fit_hero_button(str(ab.name).to_upper())
	if not sim.ability_unlocked():
		btn_hero.text = "%s\nRANK %d" % [str(ab.name).to_upper(), int(ab.get("unlock", 3))]
		btn_hero.disabled = true
	elif sim.hero.ability_cd > 0.0:
		btn_hero.text = "%s\n%ds%s" % [str(ab.name).to_upper(), int(ceil(sim.hero.ability_cd)), "" if sim.wave_active() else " (paused)"]
		btn_hero.disabled = true
	else:
		btn_hero.text = "%s\nREADY!" % str(ab.name).to_upper()
		btn_hero.disabled = false
		btn_hero.modulate = Color(1.0, 1.0, 1.0).lerp(Color(1.35, 1.25, 0.9), 0.5 + 0.5 * sin(time_s * 6.0))


## Long ability names ("EARTHQUAKE") get a smaller font so they stay on one line instead of breaking mid-word.
func _fit_hero_button(ab_name: String) -> void:
	if str(btn_hero.get_meta("fit_for", "")) == ab_name:
		return
	btn_hero.set_meta("fit_for", ab_name)
	var font: Font = btn_hero.get_theme_font("font")
	var room: float = btn_hero.custom_minimum_size.x - 36.0      # 12 px content margin + 4 px border each side, + outline
	var fsz := _fs(16)
	while fsz > 10 and font.get_string_size(ab_name, HORIZONTAL_ALIGNMENT_LEFT, -1, fsz).x > room:
		fsz -= 1
	btn_hero.add_theme_font_size_override("font_size", fsz)
	btn_hero.add_theme_constant_override("outline_size", _outline_for(fsz))


func _update_hud(delta: float) -> void:
	hud_top.visible = started
	hud_side.visible = started
	btn_pause.visible = started
	lbl_gold.text = str(sim.gold)
	lbl_lives.text = str(sim.lives)
	lbl_wave.text = ("%d/%d" % [sim.wave, sim.total_waves]) if not (sim.endless or sim.wave > sim.total_waves) else ("%d  ENDLESS" % sim.wave)
	for type in shop_buttons:
		shop_buttons[type].disabled = _tower_open(type) and sim.gold < sim.tower_cost(type)
	var cards: Array = []
	for c in up_box.get_children():
		cards.append(c)
		if c is HBoxContainer:
			cards.append_array(c.get_children())
	for b in cards:
		if b is Button and b.has_meta("cost"):
			var poor: bool = sim.gold < int(b.get_meta("cost"))
			b.disabled = poor
			b.modulate = Color(0.72, 0.72, 0.78) if poor else Color.WHITE
			(b.get_meta("cost_lbl") as Label).add_theme_color_override("font_color", Color(1.0, 0.4, 0.35) if poor else Color(0.75, 1.0, 0.6))
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
	_cancel_placing()
	var earned := 0
	var newly := ""
	if won:
		_sfx("victory")
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
	else:
		_sfx("defeat")
	var rewards := _award(won)
	results_pages = [func(box: VBoxContainer): _results_summary_page(box, won, earned)]
	for r in rewards:
		results_pages.append(func(box: VBoxContainer): _results_reward_page(box, r))
	if newly != "":
		results_pages.append(func(box: VBoxContainer): _results_unlock_page(box, newly))
	results_pages.append(func(box: VBoxContainer): _results_actions_page(box, won, newly))
	results_summary = "%s stars=%d rewards=%d newly=%s" % ["won" if won else "lost", earned, rewards.size(), newly]
	results_page = 0
	overlay.visible = true
	_show_results_page()


func _show_results_page() -> void:
	var box: VBoxContainer = overlay.get_meta("box")
	_clear_box(box)
	box.set_meta("want_w", 1100.0)
	box.add_theme_constant_override("separation", 18)
	(results_pages[results_page] as Callable).call(box)
	if results_page < results_pages.size() - 1:
		var dots := _label("%d / %d" % [results_page + 1, results_pages.size()], 18, Color(0.6, 0.68, 0.8), 4)
		dots.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		box.add_child(dots)
		var nxt := _button("NEXT", Color(0.2, 0.58, 0.18), 34)
		nxt.custom_minimum_size = Vector2(360, 92)
		nxt.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		nxt.pressed.connect(func():
			_sfx("click")
			results_page += 1
			_show_results_page())
		box.add_child(nxt)
	_reveal(overlay)


func _results_title(box: VBoxContainer, text: String, col: Color, size := 76) -> void:
	var t := _label(text, size, col, 16)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(t)


## Page 1: win or lose, the match stats, and the best tower of the match.
func _results_summary_page(box: VBoxContainer, won: bool, stars: int) -> void:
	if won:
		box.add_theme_constant_override("separation", 10)
		_results_title(box, "THE CORE IS DESTROYED!" if map.get("final", false) else "VICTORY!", C_GOLD, 62)
		if stars > 0 or not demo:
			var srow := HBoxContainer.new()
			srow.alignment = BoxContainer.ALIGNMENT_CENTER
			var have := Progress.stars(map_id) if not demo else 3
			for i in 3:
				srow.add_child(_icon(ICON_STAR if i < have else ICON_STAR_EMPTY, 56))
			box.add_child(srow)
		var line := "The %s is scrap metal." % str(defs.enemies[str(map.get("boss", "prime_walker"))].name).capitalize()
		if map.get("final", false):
			line = "The machines are finished... but the AI you built to win this war is already slipping back through time."
		var sl := _label(line, 26, C_TEXT, 6)
		sl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		sl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(sl)
	else:
		box.add_theme_constant_override("separation", 10)
		_results_title(box, "THE CITY HAS FALLEN" if str(map.get("base", "cave")) == "city" else "DEFEAT", Color(1, 0.45, 0.4), 62)
		var sl2 := _label("You held out until wave %d of %d. Every wave you cleared still paid out." % [sim.wave, sim.total_waves], 26, C_TEXT, 6)
		sl2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		sl2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(sl2)
	var grid := HFlowContainer.new()
	grid.alignment = FlowContainer.ALIGNMENT_CENTER
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 14)
	box.add_child(grid)
	var cells := [
		["WAVES", "%d / %d" % [mini(waves_cleared, sim.total_waves), sim.total_waves]],
		["ROBOTS DESTROYED", str(sim.stats.kills)],
		["LIVES LEFT", str(maxi(0, sim.lives))],
		["GOLD EARNED", str(sim.stats.gold_earned)],
		["TOWERS BUILT", str(sim.stats.built)],
		["HERO KILLS", str(sim.hero.kills if sim.hero != null else 0)],
	]
	for c in cells:
		var cell := PanelContainer.new()
		cell.add_theme_stylebox_override("panel", _style(Color(0.08, 0.12, 0.2), 14, C_PANEL_EDGE.darkened(0.2), 3))
		cell.custom_minimum_size = Vector2(300, 0)
		var cv := VBoxContainer.new()
		cv.add_theme_constant_override("separation", -2)
		cell.add_child(cv)
		var k := _label(str(c[0]), 17, Color(0.62, 0.72, 0.86), 4)
		k.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		cv.add_child(k)
		var v := _label(str(c[1]), 30, Color.WHITE, 7)
		v.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		cv.add_child(v)
		grid.add_child(cell)
	var best := sim.best_tower()
	if not best.is_empty():
		var bp := PanelContainer.new()
		bp.add_theme_stylebox_override("panel", _style(Color(0.1, 0.16, 0.27), 18, C_GOLD, 4))
		bp.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		box.add_child(bp)
		var bh := HBoxContainer.new()
		bh.add_theme_constant_override("separation", 18)
		bp.add_child(bh)
		bh.add_child(_icon(_icon_tex(str(best.type)), 96))
		var bv := VBoxContainer.new()
		bv.alignment = BoxContainer.ALIGNMENT_CENTER
		bh.add_child(bv)
		bv.add_child(_label("BEST TOWER", 20, C_GOLD, 5))
		bv.add_child(_label(str(best.name), 32, Color.WHITE, 8))
		bv.add_child(_label("%s damage  -  %d robots destroyed  -  tier %d" % [_short_num(float(best.dealt)), int(best.kills), int(best.level)], 21, Color(0.8, 0.86, 0.95), 5))


## One reward per page: a big picture, the amount, and what it's for.
func _results_reward_page(box: VBoxContainer, r: Dictionary) -> void:
	_results_title(box, str(r.title), r.get("col", C_GOLD), 60)
	var ic := _icon(r.icon, 210)
	ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	ic.pivot_offset = Vector2(105, 105)
	ic.scale = Vector2.ONE * 0.4
	box.add_child(ic)
	var tw := ic.create_tween()
	tw.tween_property(ic, "scale", Vector2.ONE, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	var amt := _label(str(r.amount), 56, Color.WHITE, 14)
	amt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(amt)
	if r.has("bar"):
		var pb := ProgressBar.new()
		pb.show_percentage = false
		pb.custom_minimum_size = Vector2(560, 30)
		pb.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		pb.max_value = maxf(float(r.bar[1]), 1.0)
		pb.value = float(r.bar[0])
		var fill := _style(Color(0.3, 0.75, 1.0), 10)
		fill.shadow_size = 0
		var bg := _style(Color(0.04, 0.07, 0.12), 10)
		bg.shadow_size = 0
		pb.add_theme_stylebox_override("fill", fill)
		pb.add_theme_stylebox_override("background", bg)
		box.add_child(pb)
	var ex := _label(str(r.text), 26, Color(0.82, 0.88, 0.96), 6)
	ex.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ex.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(ex)
	if r.get("fanfare", false):
		_sfx("level_up", 0.0, 0.0, 0.0)
	else:
		_sfx("coin", -2.0)


func _results_unlock_page(box: VBoxContainer, newly: String) -> void:
	var me := _map_entry(newly)
	var new_era := str(me.get("era", "")) != _era()
	_results_title(box, "NEW AGE UNLOCKED!" if new_era else "NEW MAP UNLOCKED!", Color(0.6, 1.0, 0.6), 60)
	var tex = load("res://assets/textures/ground_%s.png" % newly)
	if tex != null:
		var tr := TextureRect.new()
		tr.texture = tex
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		tr.custom_minimum_size = Vector2(560, 300)
		tr.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		box.add_child(tr)
	var nm := _label("%s  -  Map %d of %d" % [str(me.get("name", newly)), map_order.find(newly) + 1, map_order.size()], 40, Color.WHITE, 9)
	nm.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(nm)
	var txt := "Welcome to the %s: new towers to unlock, new heros to recruit and new robots coming through the portal. Scrap starts fresh here." % str(me.get("era", "")) if new_era else "The next map is open. It's tougher than this one, so unlock towers with your Scrap if you need more firepower."
	var ex := _label(txt, 24, Color(0.82, 0.88, 0.96), 6)
	ex.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ex.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(ex)
	_sfx("upgrade")


## Last page: where to go next.
func _results_actions_page(box: VBoxContainer, won: bool, newly: String) -> void:
	_results_title(box, "WHAT NEXT?", C_GOLD, 60)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 20)
	grid.add_theme_constant_override("v_separation", 20)
	grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	box.add_child(grid)
	var add := func(text: String, col: Color, cb: Callable) -> void:
		var b := _button(text, col, 30)
		b.custom_minimum_size = Vector2(420, 96)
		b.pressed.connect(func():
			_sfx("click")
			cb.call())
		grid.add_child(b)
	var nm := Progress.next_map(map_id, map_order)
	if won and nm != "":
		var ne := str(_map_entry(nm).get("era", "")) != _era()
		add.call("ENTER THE %s" % str(_map_entry(nm).get("era", "")).to_upper() if ne else "NEXT MAP", Color(0.2, 0.58, 0.18), func():
			Progress.current_map = nm
			get_tree().reload_current_scene())
	add.call("PLAY AGAIN", Color(0.24, 0.4, 0.62), func():
		Progress.current_map = map_id
		get_tree().reload_current_scene())
	if won:
		add.call("ENDLESS MODE", Color(0.5, 0.28, 0.6), func():
			sim.endless = true
			sim.state = "ready"
			overlay.visible = false
			_banner("ENDLESS", Color(0.85, 0.6, 1))
			_toast("How long can you hold out?", Color(0.85, 0.6, 1)))
	add.call("MAIN MENU", Color(0.24, 0.3, 0.44), func():
		Progress.current_map = ""
		Progress.open_map_select = false
		get_tree().reload_current_scene())
	if won and not demo and Progress.can_new_timeline(map_order):
		add.call("BEGIN A NEW TIMELINE", Color(0.5, 0.2, 0.62), func(): _confirm_new_timeline())


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
	_on_close(pause_menu, func():
		_sfx("click")
		_set_paused(false))
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
		["ROBOTS ON THIS MAP", Color(0.55, 0.2, 0.22), func(): _robot_roster(map_id)],
		["RESTART MAP", Color(0.24, 0.4, 0.62), func():
			_award(false)
			Progress.current_map = map_id
			get_tree().reload_current_scene()],
		["QUIT TO MAIN MENU", Color(0.55, 0.26, 0.18), func():
			_award(false)
			Progress.current_map = ""
			Progress.open_map_select = false
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
	var note := _label("Waves you cleared still earn Scrap and Time Shards if you restart or quit, and your hero keeps its XP.", 19, Color(0.68, 0.75, 0.85), 5)
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
		world_env.glow_enabled = bool(Progress.setting("glow")) and Progress.gfx_level() == 0
	# MSAA leaks memory in the Compatibility renderer on some Android GPUs (godot#97967): off on phones
	var aa := Viewport.MSAA_2X if (Progress.gfx_level() == 0 and not OS.has_feature("mobile")) else Viewport.MSAA_DISABLED
	if get_viewport().msaa_3d != aa:
		get_viewport().msaa_3d = aa
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


func _gfx_picker() -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	var btns := []
	for i in 3:
		var b := _button(Progress.GFX_NAMES[i], Color(0.3, 0.3, 0.36), 17)
		b.custom_minimum_size = Vector2(120, 60)
		btns.append(b)
		row.add_child(b)
		b.pressed.connect(func():
			_sfx("click", -6.0)
			Progress.data.settings.gfx = i
			Progress.save()
			_apply_settings()
			_toast("Graphics: %s (fully applies on the next map load)" % Progress.GFX_NAMES[i], C_GOLD)
			for j in btns.size():
				btns[j].modulate = Color(0.7, 1.5, 0.7) if j == i else Color.WHITE)
	for j in btns.size():
		btns[j].modulate = Color(0.7, 1.5, 0.7) if j == Progress.gfx_level() else Color.WHITE
	return row


const PLACE_HELP := ["TAP: tap a tower, then tap the map. Fastest.",
	"DRAG: drag a tower from the right onto the map and let go. Drop it back on the list to cancel.",
	"CONFIRM: tap a tower, tap a spot to preview its range, then press BUILD. No misplaced towers."]


func _place_picker() -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	var btns := []
	for i in 3:
		var b := _button(Progress.PLACE_MODES[i], Color(0.3, 0.3, 0.36), 17)
		b.custom_minimum_size = Vector2(120, 60)
		b.tooltip_text = PLACE_HELP[i]
		btns.append(b)
		row.add_child(b)
		b.pressed.connect(func():
			_sfx("click", -6.0)
			Progress.data.settings.place_mode = i
			Progress.save()
			_cancel_placing()
			_toast(PLACE_HELP[i], C_GOLD)
			toast_t = 4.0
			for j in btns.size():
				btns[j].modulate = Color(0.7, 1.5, 0.7) if j == i else Color.WHITE)
	for j in btns.size():
		btns[j].modulate = Color(0.7, 1.5, 0.7) if j == _place_mode() else Color.WHITE
	return row


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
	var track := _style(Color(0.04, 0.06, 0.1), 8, C_PANEL_EDGE, 2)
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
	_reveal(settings_panel)
	_clear_box(box)
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
		["Graphics (Safe or Minimal if the game crashes)", _gfx_picker()],
		["Tower placement", _place_picker()],
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
	var note := _label("Auto-start: after you start wave 1, each next wave starts 2 seconds after the last one is cleared.", 18, Color(0.68, 0.75, 0.85), 5)
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(note)
	if Progress.crash_recovered:
		var cr := _label("The game closed unexpectedly last time, so graphics were lowered to %s." % Progress.GFX_NAMES[Progress.gfx_level()], 18, Color(1, 0.75, 0.5), 5)
		cr.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(cr)
	var reset := _button("RESET TO NEW PLAYER (test)", Color(0.62, 0.2, 0.18), 22)
	reset.custom_minimum_size = Vector2(0, 64)
	reset.pressed.connect(func():
		_sfx("click")
		if not reset.has_meta("armed"):
			reset.set_meta("armed", true)
			reset.text = "TAP AGAIN: WIPE ALL PROGRESS?"
			return
		Progress.reset_progress()
		Progress.current_map = ""
		Progress.open_map_select = false
		get_tree().paused = false
		get_tree().reload_current_scene())
	box.add_child(reset)
	var done := _button("DONE", Color(0.2, 0.58, 0.18), 34)
	done.custom_minimum_size = Vector2(0, 84)
	done.pressed.connect(func():
		_sfx("click")
		Progress.save()
		settings_panel.visible = false)
	box.add_child(done)
	_close_with(settings_panel, done)
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
	var keep := _label("YOU KEEP:  every perk you bought, all your heros and their levels, and your Time Shards.", 26, Color(0.6, 1.0, 0.6), 6)
	keep.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(keep)
	var gain := _label("YOU GAIN:  +%d Upgrade Points, and every perk can go %d rank higher." % [
		int(lt.bonus_points_per), int(lt.max_rank_per)], 26, C_GOLD, 6)
	gain.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(gain)
	var lose := _label("RESETS:  map unlocks and stars. Robots in the new timeline are %d%% tougher." % int(round(float(lt.robot_hp_per) * 100)), 26, Color(1, 0.6, 0.55), 6)
	lose.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(lose)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 24)
	box.add_child(row)
	var no := _button("NOT YET", Color(0.18, 0.27, 0.43), 32)
	no.custom_minimum_size = Vector2(300, 90)
	no.pressed.connect(func():
		_sfx("click")
		dlg.queue_free())
	row.add_child(no)
	_close_with(dlg, no)
	var yes := _button("BEGIN TIMELINE %d" % nxt, Color(0.5, 0.2, 0.62), 32)
	yes.custom_minimum_size = Vector2(420, 90)
	yes.pressed.connect(func():
		_sfx("level_up")
		Progress.start_new_timeline(map_order)
		Progress.current_map = ""
		Progress.open_map_select = true
		get_tree().reload_current_scene())
	row.add_child(yes)


func _map_meta() -> Dictionary:
	for m in Defs.map_list():
		if str(m.id) == map_id:
			return m
	return {}


## Grants Legacy XP for waves cleared since the last award (and the win bonus once). Returns text for the result screen.
## Pays out Scrap, Time Shards and hero XP for whatever hasn't been paid yet this match
## (also used when restarting or quitting). Returns the rewards to show, one page each.
func _award(won: bool) -> Array:
	var out := []
	if demo:
		return out
	var meta := _map_meta()
	var scrap := 0
	var shards := 0
	var new_waves := waves_cleared - xp_waves_awarded
	if new_waves > 0 and not sim.endless:
		scrap += Progress.match_scrap(meta, new_waves, false, false)
		shards += Progress.match_shards(meta, new_waves, false, false)
	xp_waves_awarded = waves_cleared
	var fc := false
	if won and not xp_win_awarded:
		xp_win_awarded = true
		fc = first_clear
		scrap += Progress.match_scrap(meta, 0, true, first_clear)
		shards += Progress.match_shards(meta, 0, true, first_clear)
	# hero XP: only from robots the hero destroyed itself
	var hxp := int(sim.hero_kill_xp - hero_xp_awarded)
	hero_xp_awarded = sim.hero_kill_xp
	var hid := sim.hero_id
	var hname := _short_name(str(sim.hero_def.get("name", hid)))
	var lv := [Progress.hero_level(hid), Progress.hero_level(hid), 0]
	if hxp > 0 and hid != "":
		lv = Progress.add_hero_xp(hid, hxp)
	if scrap > 0:
		Progress.add_scrap(_era(), scrap)
		out.append({"title": "SCRAP", "icon": _scrap_tex(_era()), "amount": "+%d" % scrap, "col": Color(0.8, 0.88, 1.0),
			"text": "Salvaged robot parts from the %s. Spend Scrap on the TOWERS screen to unlock this age's next tower. You now have %d. Each age has its own Scrap." % [_era(), Progress.scrap(_era())]})
	if hid != "" and (hxp > 0 or won):
		var pr := Progress.hero_level_progress(hid)
		var up: bool = lv[1] > lv[0]
		var t := "%s destroyed robots worth %d hero XP. Heros only learn from robots they destroy themselves." % [hname, hxp] if hxp > 0 else "%s didn't destroy any robots this time. Heros only earn XP from their own kills: place them where the robots are." % hname
		if up:
			t = "%s reached LEVEL %d!  %s.  Level-up bonus: +%d Time Shards." % [hname, lv[1], Progress.hero_level_bonus_text(lv[1]), lv[2]]
		var mx: bool = int(lv[1]) >= int(Progress.workshop.hero_levels.max)
		out.append({"title": "%s  -  LEVEL %d%s" % [hname.to_upper(), lv[1], "  (MAX)" if mx else ""], "icon": _face_tex(hid), "amount": "+%d HERO XP" % hxp,
			"text": t, "bar": [pr[0], pr[1]] if not mx else [1, 1], "fanfare": up, "col": Color(0.6, 0.9, 1.0)})
	if shards > 0:
		Progress.add_shards(shards)
		out.append({"title": "TIME SHARDS", "icon": ICON_SHARD, "amount": "+%d" % shards, "col": Color(0.82, 0.74, 1.0),
			"text": "Crystals from the time rift%s. Spend them on new heros on the HEROS screen. They never reset. You now have %d." % [" (includes the first-clear bonus)" if fc else "", Progress.shards()]})
	return out


func _open_legacy() -> void:
	_reveal(legacy_panel)
	_build_legacy_contents()
	legacy_panel.get_parent().move_child(legacy_panel, -1)
	legacy_panel.visible = true


func _build_legacy_contents() -> void:
	var box: VBoxContainer = legacy_panel.get_meta("box")
	_clear_box(box)
	box.set_meta("want_w", 1560.0)
	box.add_theme_constant_override("separation", 12)
	# header
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 30)
	box.add_child(head)
	head.add_child(_label("UPGRADES", 64, C_GOLD, 14))
	var gap := Control.new()
	gap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(gap)
	var pts := Progress.points_free()
	var plbl := _label("%d UPGRADE POINT%s TO SPEND" % [pts, "" if pts == 1 else "S"], 36, C_GOLD if pts > 0 else Color(0.6, 0.64, 0.7), 9)
	plbl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(plbl)
	var intro_t := "Upgrade Points are earned only by starting a New Timeline. The perks you buy carry into every map and every timeline after that. (Heros level up on their own: each hero gets stronger from the robots it destroys.)"
	if Progress.timeline() > 1:
		intro_t += "\nTimeline %d bonus: +%d points, and every perk can go %d rank%s higher." % [Progress.timeline(), Progress.timeline_bonus_points(),
			Progress.timeline() - 1, "" if Progress.timeline() == 2 else "s"]
	var intro := _label(intro_t, 22, Color(0.78, 0.83, 0.9), 5)
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
	# footer
	var foot := HBoxContainer.new()
	foot.alignment = BoxContainer.ALIGNMENT_CENTER
	foot.add_theme_constant_override("separation", 20)
	box.add_child(foot)
	var reset := _button("RESET POINTS (free)", Color(0.19, 0.3, 0.5), 22)
	reset.custom_minimum_size = Vector2(320, 70)
	reset.disabled = Progress.points_spent() == 0
	reset.pressed.connect(func():
		_sfx("coin")
		Progress.reset_perks()
		_build_legacy_contents())
	foot.add_child(reset)
	var done := _button("DONE", Color(0.2, 0.58, 0.18), 30)
	done.custom_minimum_size = Vector2(320, 70)
	done.pressed.connect(func():
		_sfx("click")
		legacy_panel.visible = false
		_refresh_menus())
	foot.add_child(done)
	_close_with(legacy_panel, done)
	box.move_child(foot, 1)   # buttons right under the header so DONE never needs scrolling


func _perk_card(p: Dictionary, bc: Color) -> Control:
	var id: String = p.id
	var rank := Progress.perk_rank(id)
	var mx := Progress.perk_max(id)
	var card := PanelContainer.new()
	var sb := _style(Color(0.09, 0.14, 0.23) if rank == 0 else bc.darkened(0.62), 14, bc.darkened(0.2) if rank > 0 else Color(0.16, 0.24, 0.37), 3)
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
	top.add_child(_label("%d/%d" % [rank, mx], 22, C_GOLD if rank > 0 else Color(0.6, 0.64, 0.7), 6))
	var now_txt := ("Now: " + Progress.perk_text(id, rank)) if rank > 0 else str(p.desc)
	info.add_child(_label(now_txt, 17, Color(0.83, 0.87, 0.92) if rank > 0 else Color(0.68, 0.73, 0.8), 4))
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
	Progress.mark_seen(Progress.current_map, [], false)    # (no first-visit robot popup: it would pause the match)
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
	print("AUTOWIN map=%s state=%s wave=%d lives=%d overlay=%s results=%s pages=%d hero_rank=%d" % [map_id, sim.state, sim.wave, sim.lives,
		overlay.visible, results_summary, results_pages.size(), sim.hero.level if sim.hero != null else 0])
	print("AUTOWIN save=", JSON.stringify(Progress.data))
	get_tree().quit()


## Screenshot of the main menu with the attract-mode background (and the workshop / heroes screens).
func _shoot_menu() -> void:
	await get_tree().create_timer(8.0).timeout
	await _shot("menu_main.png")
	_open_workshop("")
	for i in 4:
		await get_tree().process_frame
	await _shot("menu_workshop.png")
	if "--test-refresh" in OS.get_cmdline_user_args():
		var t0 := Time.get_ticks_msec()
		for k in 3:
			for c in modals.duplicate():
				if is_instance_valid(c) and c.visible and c.has_meta("on_close") and c != map_select:
					(c.get_meta("on_close") as Callable).call()
			await get_tree().process_frame
			_open_heroes()
			await get_tree().process_frame
			(heroes_panel.get_meta("on_close") as Callable).call()
			await get_tree().process_frame
			_open_legacy()
			await get_tree().process_frame
			(legacy_panel.get_meta("on_close") as Callable).call()
			await get_tree().process_frame
		print("REFRESH ok title_valid=%s ms=%d modals=%d" % [is_instance_valid(title_screen), Time.get_ticks_msec() - t0, modals.size()])
		await _shot("menu_after_refresh.png")
		get_tree().quit()
		return
	if "--shoot-newbots" in OS.get_cmdline_user_args():
		Progress.data.erase("seen_robots")
		Progress.data.erase("seen_maps")
		map_id = "railyard"
		print("NEWBOTS first_visit=%s seen_before=%s" % [_first_visit(), Progress.data.seen_robots])
		Progress.data.seen_robots = Progress.data.seen_robots.slice(0, 3)
		Progress.data.seen_maps.erase("railyard")
		print("NEWBOTS first_visit_after_trim=%s" % _first_visit())
		_robot_roster("railyard", true)
		print("NEWBOTS marked=%s" % Progress.map_seen("railyard"))
		await get_tree().create_timer(1.0).timeout
		await _shot("menu_newbots.png")
		get_tree().quit()
		return
	if "--shoot-tech" in OS.get_cmdline_user_args():
		_open_techtree("", "")
		await get_tree().create_timer(1.0).timeout
		await _shot("menu_tech.png")
		get_tree().quit()
		return
	if "--shoot-robots" in OS.get_cmdline_user_args():
		_robot_roster("railyard")
		await get_tree().create_timer(1.0).timeout
		await _shot("menu_robots.png")
		_open_settings()
		await get_tree().create_timer(0.5).timeout
		await _shot("menu_settings.png")
		get_tree().quit()
		return
	if "--shoot-tower" in OS.get_cmdline_user_args():
		_tower_detail(str(Progress.era_towers("Bronze Age")[1]))
		await get_tree().create_timer(1.0).timeout
		await _shot("menu_tower_detail.png")
		get_tree().quit()
		return
	if "--shoot-tabs" in OS.get_cmdline_user_args():
		for c in modals.duplicate():
			if is_instance_valid(c) and c.visible and c != map_select and c.has_meta("full_h") and c != heroes_panel and c != legacy_panel:
				c.queue_free()
		_open_workshop("Stone Age")
		await get_tree().create_timer(0.6).timeout
		await _shot("tabs_stone.png")
		for c in modals:
			if is_instance_valid(c) and c.visible and c.has_meta("full_h") and c != map_select and c != heroes_panel and c != legacy_panel:
				_open_workshop("Bronze Age", c)
		await get_tree().create_timer(0.6).timeout
		await _shot("tabs_bronze.png")
		_open_heroes()
		await get_tree().create_timer(0.6).timeout
		await _shot("menu_heroes.png")
		_hero_detail("brenna", VBoxContainer.new())
		await get_tree().create_timer(0.8).timeout
		await _shot("hero_locked.png")
		_hero_detail("tarek", VBoxContainer.new())
		await get_tree().create_timer(0.8).timeout
		await _shot("hero_buyable.png")
		get_tree().quit()
		return
	if "--shoot-previews" in OS.get_cmdline_user_args():
		# card model viewers: two moments of each, to see them move (HQ and v2 heroes and towers, Bronze Age included)
		var cards := [["hero", "ugo"], ["hero", "mara"], ["hero", "kira"], ["hero", "tarek"], ["tower", "boulder_catapult"],
			["tower", "tar_shaman"], ["tower", "spear_guard"], ["tower", "torsion_catapult"], ["tower", "knight"]]
		for c in cards:
			if c[0] == "hero":
				_hero_detail(str(c[1]), VBoxContainer.new())
			else:
				_tower_detail(str(c[1]))
			await get_tree().create_timer(0.7).timeout
			await _shot("prev_%s_%s_a.png" % [c[0], c[1]])
			await get_tree().create_timer(1.3).timeout
			await _shot("prev_%s_%s_b.png" % [c[0], c[1]])
			for m in modals:
				if is_instance_valid(m):
					(m as Node).queue_free()
			await get_tree().process_frame
		get_tree().quit()
		return
	if "--shoot-heroes" in OS.get_cmdline_user_args():
		_open_heroes()
		for i in 4:
			await get_tree().process_frame
		await _shot("menu_heroes.png")
		_hero_detail("ugo", VBoxContainer.new())
		await get_tree().create_timer(1.0).timeout
		await _shot("menu_hero_owned.png")
		_hero_detail("nova", VBoxContainer.new())
		await get_tree().create_timer(1.0).timeout
		await _shot("menu_hero_locked.png")
		get_tree().quit()
		return
	if "--test-drag" in OS.get_cmdline_user_args():
		_open_legacy()
		for i in 4:
			await get_tree().process_frame
		await _test_drag()
	get_tree().quit()


## Places a tower in each placement mode with simulated pointer input and reports what got built.
func _test_place() -> void:
	_start_game()
	sim.gold += 9000
	for i in 4:
		await get_tree().process_frame
	var type: String = sim.tower_types()[0]
	var results := []
	for mode in 3:
		Progress.data.settings.place_mode = mode
		_cancel_placing()
		_deselect()
		for i in 3:
			await get_tree().process_frame
		var before := sim.towers.size()
		var spot := _demo_spot(type)
		var target := cam.unproject_position(_v3(spot))
		var card: Button = shop_buttons[type]
		var cpos := card.get_global_rect().get_center() - Vector2(card.size.x * 0.2, 0)
		match mode:
			0:
				await _tap(cpos)
				await _tap(target)
			1:
				await _press(cpos, true)
				for k in 12:
					await _drag_to(cpos.lerp(target, (k + 1) / 12.0))
				await _press(target, false)
			2:
				await _tap(cpos)
				await _tap(target)
				var mid := sim.towers.size()
				await _shot("place_confirm_preview.png")
				results.append("confirm_before_build=%d" % (mid - before))
				await _tap(_pc_build.get_global_rect().get_center())
		for i in 3:
			await get_tree().process_frame
		results.append("%s=%d" % [Progress.PLACE_MODES[mode], sim.towers.size() - before])
	# drag released over the sidebar must cancel
	Progress.data.settings.place_mode = 1
	_deselect()
	var n0 := sim.towers.size()
	var c2: Button = shop_buttons[type]
	var p2 := c2.get_global_rect().get_center() - Vector2(c2.size.x * 0.2, 0)
	await _press(p2, true)
	for k in 6:
		await _drag_to(p2 + Vector2(-10.0 * (k + 1), 40.0 * (k + 1)))
	await _press(p2 + Vector2(-60, 240), false)
	results.append("drag_cancel=%d placing=%s" % [sim.towers.size() - n0, placing])
	# hero in DRAG mode
	if sim.hero == null:
		var hb := btn_hero.get_global_rect().get_center()
		var ht := cam.unproject_position(_v3(_demo_spot("", true)))
		await _press(hb, true)
		for k in 12:
			await _drag_to(hb.lerp(ht, (k + 1) / 12.0))
		await _press(ht, false)
		results.append("hero_drag=%s" % str(sim.hero != null))
	print("PLACETEST ", " ".join(results))


func _press(p: Vector2, down: bool) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = down
	e.position = p
	e.global_position = p
	if down:
		e.button_mask = MOUSE_BUTTON_MASK_LEFT
	get_viewport().push_input(e, true)
	await get_tree().process_frame
	await get_tree().process_frame


func _drag_to(p: Vector2) -> void:
	var m := InputEventMouseMotion.new()
	m.position = p
	m.global_position = p
	m.button_mask = MOUSE_BUTTON_MASK_LEFT
	get_viewport().push_input(m, true)
	await get_tree().process_frame


func _tap(p: Vector2) -> void:
	await _press(p, true)
	await _press(p, false)


## Drags the open dialog starting ON a button: it should scroll and the button must not fire.
func _test_drag() -> void:
	var sc := _scroll_under(ui_root.size * 0.5)
	var fired := [0]
	var btn: Button = null
	for n in sc.find_children("*", "Button", true, false):
		var b := n as Button
		if b.is_visible_in_tree() and sc.get_global_rect().encloses(b.get_global_rect()):
			btn = b
			break
	btn.pressed.connect(func(): fired[0] += 1)
	var p0 := btn.get_global_rect().get_center()
	print("DRAG before scroll=", sc.scroll_vertical, " max=", sc.get_v_scroll_bar().max_value, " page=", sc.get_v_scroll_bar().page, " btn=", btn.text)
	var ev := InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.position = p0
	ev.global_position = p0
	get_viewport().push_input(ev, true)
	await get_tree().process_frame
	for i in 12:
		var mm := InputEventMouseMotion.new()
		mm.position = p0 - Vector2(0, 25 * (i + 1))
		mm.global_position = mm.position
		mm.button_mask = MOUSE_BUTTON_MASK_LEFT
		get_viewport().push_input(mm, true)
		await get_tree().process_frame
	var up := InputEventMouseButton.new()
	up.button_index = MOUSE_BUTTON_LEFT
	up.pressed = false
	up.position = p0 - Vector2(0, 300)
	up.global_position = up.position
	get_viewport().push_input(up, true)
	for i in 30:
		await get_tree().process_frame
	print("DRAG after scroll=", sc.scroll_vertical, " button_fired=", fired[0])
	await _shot("menu_drag.png")
	var w := InputEventMouseButton.new()
	w.button_index = MOUSE_BUTTON_WHEEL_UP
	w.pressed = true
	w.position = p0
	w.global_position = p0
	get_viewport().push_input(w, true)
	await get_tree().process_frame
	print("WHEEL after scroll=", sc.scroll_vertical)
	# a plain tap on a button still works
	var tb := btn
	var q := tb.get_global_rect().get_center()
	for pr in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_LEFT
		e.pressed = pr
		e.position = q
		e.global_position = q
		get_viewport().push_input(e, true)
	print("TAP button_fired=", fired[0])
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
	if "--shoot-results" in args:
		_start_game()
		_demo_build(4000)
		sim.start_wave()
		for i in int(40.0 / TICK):
			sim.step()
			if sim.can_start_wave():
				sim.start_wave()
		_handle_events()
		demo = false
		waves_cleared = 20
		sim.hero_kill_xp = 900.0
		_show_overlay(true)
		if "--test-results-x" in args:
			await get_tree().process_frame
			(overlay.get_meta("on_close") as Callable).call()
			await get_tree().process_frame
			print("RESULTSX page=%d of %d overlay=%s scene_ok=%s" % [results_page + 1, results_pages.size(), overlay.visible, is_instance_valid(overlay)])
			await _shot("results_after_x.png")
			get_tree().quit()
			return
		for i in results_pages.size():
			for f in 6:
				await get_tree().process_frame
			await _shot("results_%d.png" % i)
			results_page = mini(results_page + 1, results_pages.size() - 1)
			_show_results_page()
		get_tree().quit()
		return
	if "--shoot-upgrade" in args:
		_start_game()
		sim.gold += 9000
		var tt: String = sim.tower_types()[0]
		var uid := sim.place_tower(tt, _demo_spot(tt))
		sim.upgrade_tower(uid, "")
		_handle_events()
		_select(uid)
		await get_tree().create_timer(0.8).timeout
		await _shot("upgrade_tier2.png")
		sim.gold = 100
		_show_tower_panel(uid)
		await get_tree().create_timer(0.5).timeout
		await _shot("upgrade_poor.png")
		sim.gold += 9000
		sim.upgrade_tower(uid, "")
		sim.gold = 145
		_handle_events()
		_show_tower_panel(uid)
		await get_tree().create_timer(0.6).timeout
		await _shot("upgrade_pick.png")
		sim.gold += 9000
		sim.upgrade_tower(uid, "A")
		_handle_events()
		_show_tower_panel(uid)
		await get_tree().create_timer(0.5).timeout
		await _shot("upgrade_pathA.png")
		_tower_detail(tt)
		await get_tree().create_timer(1.0).timeout
		await _shot("upgrade_detail.png")
		get_tree().quit()
		return
	if "--shoot-paths" in args:
		_start_game()
		_path_preview(true)
		await get_tree().create_timer(1.2).timeout
		await _shot("paths_preview_a.png")
		await get_tree().create_timer(1.8).timeout
		await _shot("paths_preview_b.png")
		await get_tree().create_timer(9.0).timeout       # still going round long after one pass
		print("PATHS looping=%s t=%.1f" % [not preview.is_empty(), float(preview.get("t", 0.0))])
		await _shot("paths_preview_loop.png")
		_demo_build(3000)
		sim.start_wave()
		await get_tree().create_timer(1.0).timeout
		print("PATHS ended_after_round1=%s" % preview.is_empty())
		await _wait_ticks(int(8.0 / TICK))
		await _shot("paths_play.png")
		get_tree().quit()
		return
	if "--shoot-portal" in args:
		_start_game()
		sim.start_wave()
		await _wait_ticks(int(1.4 / TICK))
		var pn: Node3D = portal_nodes[0]
		var pp := pn.global_position
		await _shot("demo_portal_wide.png")
		cam.projection = Camera3D.PROJECTION_PERSPECTIVE
		cam.fov = 40
		var fwd := -pn.global_transform.basis.z
		var side := pn.global_transform.basis.x
		cam.global_position = pp + fwd * 7.5 + side * 2.5 + Vector3(0, 3.5, 0)
		cam.look_at(pp + Vector3(0, 1.3, 0))
		set_process(false)
		for i in 40:
			sim.step()
			_handle_events()
			_sync_visuals(1.0)
			_update_effects(TICK)
			await get_tree().process_frame
		await _shot("demo_portal_close.png")
		cam.global_position = pp - fwd * 7.5 - side * 2.5 + Vector3(0, 3.5, 0)      # and from behind
		cam.look_at(pp + Vector3(0, 1.3, 0))
		for i in 3:
			_update_effects(TICK)
			await get_tree().process_frame
		await _shot("demo_portal_back.png")
		get_tree().quit()
		return
	if "--shoot-cloak" in args:
		_start_game()
		sim.wave = 1
		sim.wave_remaining[1] = 6
		for i in 3:
			sim._spawn_enemy("cloaker", 1, 3.0 + i * 1.2)
		sim._spawn_enemy("hover_drone", 1, 12.0)
		sim._spawn_enemy("stealth_jet", 1, 14.0)
		var e0: Dictionary = sim.enemies[0]
		e0.revealed_until = 999999
		for i in 6:
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
	if "--export-decor" in args:
		var outp := "/tmp/decor_%s.glb" % map_id
		for a2 in args:
			if a2.begins_with("--decor-out="):
				outp = a2.trim_prefix("--decor-out=")
		_export_decor(outp)
		get_tree().quit()
		return
	if "--test-place" in args:
		await _test_place()
		get_tree().quit()
		return
	if "--shoot-attacks" in args:
		# Stone Age attacks (v0.9.20): one unit (--unit=tar_shaman|club_warrior|boulder_catapult|rock_slinger) or the hero
		# (--hero=mara|ugo with --unit=hero) against a stream of robots; frames of its next attack from a camera beside
		# it (--frames=N, one per frame). Run Godot with --fixed-fps 30 so frames are evenly spaced in game time.
		# --high films from higher up, --wide keeps the game camera, --focus frames the unit itself up close,
		# --branch=A|B upgrades a tower fully down a path,
		# --ability (hero) casts the hero's ability instead and films the whole field.
		var unit := "tar_shaman"
		var nframes := 16
		var skip := 1                               # attacks to let pass first (the placement puff, robots still emerging)
		var branch := ""
		for a5 in args:
			if a5.begins_with("--unit="):
				unit = a5.trim_prefix("--unit=")
			elif a5.begins_with("--frames="):
				nframes = int(a5.trim_prefix("--frames="))
			elif a5.begins_with("--skip="):
				skip = int(a5.trim_prefix("--skip="))
			elif a5.begins_with("--branch="):
				branch = a5.trim_prefix("--branch=")
		_start_game()
		_end_preview()
		sim.gold += 20000
		var uid := -1
		if unit == "hero":
			sim.place_hero(_demo_spot("", true))
			uid = sim.hero.id
		else:
			uid = sim.place_tower(unit, _demo_spot(unit))
			if branch != "":
				# fully upgraded down one path (--branch=A|B), to see that path's look
				for k5 in 8:
					if not sim.upgrade_tower(uid, ""):
						sim.upgrade_tower(uid, branch)
				var tu = sim.get_unit(uid)
				print("ATTACKS branch=%s level=%d" % [str(tu.get("branch", "")), int(tu.level)])
		_handle_events()
		toast_t = 0.0
		toast.modulate.a = 0.0
		_hide_bars = true
		sim.wave = 2
		var akinds := ["walker", "walker", "brute", "walker", "walker", "carrier", "walker", "walker", "brute", "walker", "walker", "walker"]
		sim.wave_remaining[2] = akinds.size()
		for i in akinds.size():
			sim._spawn_enemy(akinds[i], 2, 2.0 + i * 0.9, i % sim.paths.size())
		_handle_events()
		var an: Node3D = tower_nodes[uid]
		var waited := 0
		for sk in skip + 1:
			var lf0 := float(an.get_meta("last_fire", -100.0))
			while float(an.get_meta("last_fire", -100.0)) == lf0 and waited < 900:
				await get_tree().process_frame
				waited += 1
		var ab_mode := "--ability" in args and unit == "hero"
		if ab_mode:
			sim.hero.ability_cd = 0.0
			sim.hero.level = maxi(int(sim.hero.level), int(sim.hero_def.ability.get("unlock", 3)))
			sim.use_ability()
			_handle_events()
		var u5 = sim.get_unit(uid)
		# frame the unit and the robots in its reach from the side
		var upos := _v3(u5.pos, 0.0) if u5 != null else an.global_position
		var cen := Vector3.ZERO
		var nin := 0
		var far_shot := u5 != null and str(u5.stats.kind) in ["lob", "projectile"]
		var lead = null
		for e5 in sim.enemies:
			if u5 != null and (ab_mode or (e5.pos as Vector2).distance_to(u5.pos) <= float(u5.stats.range) + 0.3):
				cen += _v3(e5.pos, 0.0)
				nin += 1
				if lead == null or float(e5.dist) > float(lead.dist):
					lead = e5
		if far_shot and lead != null:
			cen = _v3(lead.pos, 0.0) * float(nin)       # a shooter: frame it and the robot it's aiming at
		var tdir := Vector3(0, 0, 1)
		if nin > 0:
			cen /= nin
			tdir = cen - upos
		elif u5 != null:
			tdir = Vector3(u5.facing.x, 0, u5.facing.y)
		tdir.y = 0.0
		var span := clampf(tdir.length(), 1.2, 7.0 if ab_mode else 4.0)
		tdir = tdir.normalized()
		var sidev := tdir.cross(Vector3.UP).normalized()
		if (sidev.z < 0.0):
			sidev = -sidev                          # stay on the camera's usual (south) side of the action
		var mid := upos + tdir * span * 0.5
		if "--focus" in args:                       # --focus: the unit itself up close (a siege engine's whole throw)
			span = 1.6
			mid = upos + tdir * 0.35
		if not "--wide" in args:                    # --wide keeps the game's own camera
			cam.projection = Camera3D.PROJECTION_PERSPECTIVE
			cam.fov = 40
			var hi := 1.0 if ("--high" in args or ab_mode) else 0.0     # --high: from above, nearer the game's own angle
			cam.global_position = mid + sidev * (3.2 + span * 0.9 - hi * 1.2) + Vector3(0, 2.4 + span * 0.35 + hi * 2.6, 0) - tdir * 0.4
			cam.look_at(mid + Vector3(0, 0.75, 0))
		cam_base = cam.position
		shake = 0.0
		for i in nframes:
			cam.global_position = cam_base
			await _shot("atk_%s_%02d.png" % [unit, i])
			await get_tree().process_frame
		print("ATTACKS unit=%s waited=%d frames" % [unit, waited])
		get_tree().quit()
		return
	if "--shoot-lava" in args:
		# moving lava and water (v0.9.21): frames of the whole map from the game camera, then of the first pool and of the
		# volcano up close (--frames=N per view, a shot every --every=K frames; run Godot with --fixed-fps 30)
		var lframes := 12
		var every := 6
		for a6 in args:
			if a6.begins_with("--frames="):
				lframes = int(a6.trim_prefix("--frames="))
			elif a6.begins_with("--every="):
				every = int(a6.trim_prefix("--every="))
		_start_game()
		_end_preview()
		toast_t = 0.0
		toast.modulate.a = 0.0
		var views := [["wide", Vector3.INF, 0.0]]
		for bl in map.get("blockers", []):
			if bl.size() > 3 and str(bl[3]) in ["lava", "lake", "pond"]:
				views.append(["pool", Vector3(bl[0], 0, bl[1]), float(bl[2])])
				break
		for mk in _decor_theme().get("marks", []):
			if str(mk[0]) == "Volcano":
				views.append(["volcano", Vector3(mk[1].x, 0, mk[1].y), 4.0])
		for v in views:
			if v[1] != Vector3.INF:
				cam.projection = Camera3D.PROJECTION_PERSPECTIVE
				cam.fov = 40
				var rr: float = maxf(float(v[2]), 1.0)
				cam.global_position = (v[1] as Vector3) + Vector3(0, rr * 2.6 + 1.5, rr * 2.4 + 2.0)
				cam.look_at((v[1] as Vector3) + Vector3(0, 0.5 if v[0] != "volcano" else 1.5, 0))
				cam_base = cam.position
			for i in lframes:
				for k6 in every:
					await get_tree().process_frame
				await _shot("lava_%s_%02d.png" % [v[0], i])
		print("LAVA views=%d" % views.size())
		get_tree().quit()
		return
	if "--shoot-hq" in args:
		# HQ model check: a few towers fighting (--tower=<id>, or --towers=a,b,c for a mix; Rock Slingers by default),
		# a battle shot, a close-up of the first one and an optional frame sequence
		_start_game()
		sim.gold += 20000
		var hq_types: Array = ["rock_slinger", "rock_slinger", "rock_slinger"]
		for a3 in args:
			if a3.begins_with("--tower="):
				var tt := a3.trim_prefix("--tower=")
				hq_types = [tt, tt, tt]
			elif a3.begins_with("--towers="):
				hq_types = Array(a3.trim_prefix("--towers=").split(","))
		var hq_ids := []
		for tt2 in hq_types:
			var spot := _demo_spot(tt2)
			if spot != Vector2.INF:
				var hid := sim.place_tower(tt2, spot)
				if hid != -1:
					hq_ids.append(hid)
		_handle_events()
		sim.wave = 2
		var hq_kinds := ["walker", "scout", "walker", "brute", "walker", "scout", "walker", "walker", "scout", "walker"]
		sim.wave_remaining[2] = hq_kinds.size()
		for i in hq_kinds.size():
			sim._spawn_enemy(hq_kinds[i], 2, 3.0 + i * 1.5, i % sim.paths.size())
		_handle_events()
		await _wait_ticks(int(3.2 / TICK))
		await _shot("hq_battle.png")
		var hq_idx := 0
		var hq_off := Vector3(3.2, 3.0, 4.6)
		for a4 in args:
			if a4.begins_with("--hq-idx="):
				hq_idx = clampi(int(a4.trim_prefix("--hq-idx=")), 0, hq_ids.size() - 1)
			elif a4.begins_with("--hq-cam="):
				var cc := a4.trim_prefix("--hq-cam=").split(",")
				if cc.size() == 3:
					hq_off = Vector3(float(cc[0]), float(cc[1]), float(cc[2]))
		var htn: Node3D = tower_nodes[hq_ids[hq_idx]]
		cam.projection = Camera3D.PROJECTION_PERSPECTIVE
		cam.fov = 30
		cam.global_position = htn.global_position + hq_off
		cam.look_at(htn.global_position + Vector3(0, 0.95, 0))
		cam_base = cam.position
		shake = 0.0
		for i in 4:
			await get_tree().process_frame
		await _shot("hq_close.png")
		if "--gif" in args:
			for i in 72:
				await _shot("hq_gif_%03d.png" % i)
		get_tree().quit()
		return
	if "--shoot-bots" in args:
		# HQ robots: a mixed column marching, then a close-up of each Stone Age robot (from the front, three-quarters)
		_start_game()
		_end_preview()
		sim.wave = 2
		var kinds := ["walker", "scout", "brute", "carrier", "walker", "walker", "scout", "brute", "walker", "prime_walker"]
		var gap := 2.4
		for a in args:
			if str(a).begins_with("--bots="):
				kinds = Array(str(a).trim_prefix("--bots=").split(","))
				gap = 1.0                         # (closer: a Repair Drone mends the robots near it)
		var close := []
		for kd in kinds:
			if not kd in close:
				close.append(kd)
		sim.wave_remaining[2] = kinds.size()
		for i in kinds.size():
			sim._spawn_enemy(kinds[i], 2, 3.0 + i * gap, i % sim.paths.size())
		_handle_events()
		await _wait_ticks(int(2.5 / TICK))
		await _shot("bots_battle.png")
		var frames_dir := "--gif" in args
		for type in close:
			var be = null
			for e in sim.enemies:
				if e.type == type:
					be = e
					break
			if be == null or not enemy_nodes.has(be.id):
				continue
			var bn: Node3D = enemy_nodes[be.id]
			var fwd: Vector3 = bn.global_transform.basis.z
			fwd.y = 0.0
			fwd = fwd.normalized()
			var side := fwd.cross(Vector3.UP)
			var big := 2.4 if type in ["prime_walker", "siege_crawler"] else 1.0
			cam.projection = Camera3D.PROJECTION_PERSPECTIVE
			cam.fov = 30
			for k in (6 if frames_dir else 1):
				cam.global_position = bn.global_position + (fwd * 4.2 + side * 2.0 + Vector3(0, 2.2, 0)) * big
				cam.look_at(bn.global_position + Vector3(0, 0.75 * big, 0))
				cam_base = cam.position
				shake = 0.0
				await _wait_ticks(2 if k == 0 else 3)
				await _shot("bots_close_%s%s.png" % [type, ("_%d" % k) if frames_dir else ""])
			if type == "shield_bot":              # v0.9.27: its shield shatters
				sim._damage(be, 1.0, "pierce", {"shield_break": 1.0})
				_handle_events()
				for k in 3:
					await _wait_ticks(2)
					await _shot("bots_shield_break_%d.png" % k)
			if type == "repair_drone":            # v0.9.27: it mends the robots round it
				for o in sim.enemies:
					if o.alive and o.id != be.id and not o.boss and (o.pos as Vector2).distance_to(be.pos) < 4.0:
						o.hp = o.max_hp * 0.5
				for k in 10:                          # (a pulse comes within its heal period)
					cam.global_position = bn.global_position + (fwd * 4.2 + side * 2.0 + Vector3(0, 3.2, 0)) * 1.4
					cam.look_at(bn.global_position + Vector3(0, 0.6, 0))
					cam_base = cam.position
					await _wait_ticks(int(0.35 / TICK))
					await _shot("bots_heal_%d.png" % k)
		get_tree().quit()
		return
	if "--shoot-buff" in args:
		# buff badge: a Rock Slinger next to the hero, selected (badge over it), then not selected (no badge)
		_start_game()
		sim.gold += 8000
		sim.place_hero(_demo_spot("", true))
		var hp: Vector2 = sim.hero.pos
		var spot := Vector2.INF
		for k in 24:
			var c := hp + Vector2.from_angle(TAU * k / 24.0) * (sim.hero_footprint() + sim.footprint_of("rock_slinger") + 0.15)
			if sim.placement_error("rock_slinger", c) == "":
				spot = c
				break
		sim.place_tower("rock_slinger", spot)
		_handle_events()
		await _wait_ticks(10)
		var tw: Dictionary = sim.towers[sim.towers.size() - 1]
		print("BUFF buffed=%s spot=%s" % [tw.get("buffed", false), spot])
		_select(tw.id)
		cam.projection = Camera3D.PROJECTION_PERSPECTIVE
		cam.fov = 30
		var tn: Node3D = tower_nodes[tw.id]
		cam.global_position = tn.global_position + Vector3(0, 6.0, 8.0)
		cam.look_at(tn.global_position + Vector3(0, 1.2, 0))
		cam_base = cam.position
		shake = 0.0
		await _wait_ticks(4)
		await _shot("hero_buff_selected.png")
		_deselect()
		await _wait_ticks(4)
		await _shot("hero_buff_unselected.png")
		get_tree().quit()
		return
	if "--shoot-hero-hq" in args:
		# HQ hero check: Ugo + two Rock Slingers fighting, close-up, rank-up cheer, Stone Rain (+ optional frames)
		_start_game()
		sim.gold += 8000
		sim.place_hero(_demo_spot("", true))
		for k in 2:
			var spot := _demo_spot("rock_slinger")
			if spot != Vector2.INF:
				sim.place_tower("rock_slinger", spot)
		_handle_events()
		sim.wave = 2
		var kinds := ["walker", "scout", "walker", "brute", "walker", "scout", "walker", "walker", "scout", "walker", "walker", "brute"]
		sim.wave_remaining[2] = kinds.size()
		for i in kinds.size():
			sim._spawn_enemy(kinds[i], 2, 3.0 + i * 1.3, i % sim.paths.size())
		_handle_events()
		await _wait_ticks(int(3.4 / TICK))
		await _shot("hero_battle.png")
		var hn: Node3D = tower_nodes[sim.hero.id]
		var fwd := Vector3(0, 0, 1)
		if hn.has_meta("yaw"):
			fwd = (hn.get_meta("yaw") as Node3D).global_transform.basis.z
		fwd.y = 0.0
		fwd = fwd.normalized()
		cam.projection = Camera3D.PROJECTION_PERSPECTIVE
		cam.fov = 30
		cam.global_position = hn.global_position + fwd * 4.0 + fwd.cross(Vector3.UP) * 1.6 + Vector3(0, 2.3, 0)
		cam.look_at(hn.global_position + Vector3(0, 1.0, 0))
		cam_base = cam.position
		shake = 0.0
		for i in 4:
			await get_tree().process_frame
		await _shot("hero_close.png")
		sim._hero_gain_xp(float(sim.hero_levels[2]) - float(sim.hero.xp) + 1.0)
		_handle_events()
		await _wait_ticks(int(0.85 / TICK))          # second fist pump of the Cheer
		await _shot("hero_cheer.png")
		await _wait_ticks(int(1.2 / TICK))
		sim.use_ability()
		_handle_events()
		if "--gif" in args:
			for i in 60:
				await _shot("hero_gif_%03d.png" % i)
		else:
			await _wait_ticks(int(0.6 / TICK))
			await _shot("hero_ability.png")
		get_tree().quit()
		return
	if "--shoot-showcase" in args:
		_start_game()
		var sids := _demo_build(6000)
		sim.wave = 3
		# this map's own robots (most recent ones first), plus its boss
		var roster := []
		var boss_t := str(map.get("boss", "prime_walker"))
		for it in _map_robots(map_id):
			if not defs.enemies[it[0]].get("boss", false) and not (it[0] in roster):
				roster.append(it[0])
		roster.reverse()
		var kinds := []
		for i in 10:
			kinds.append(roster[i % mini(roster.size(), 5)] if not roster.is_empty() else "walker")
		sim.wave_remaining[3] = kinds.size() + 1
		for i in kinds.size():
			sim._spawn_enemy(kinds[i], 3, 4.0 + i * 2.3, i % sim.paths.size())
		if "--boss" in args:
			sim._spawn_enemy(boss_t, 3, 9.0, 0)
		_handle_events()
		await _wait_ticks(int(2.2 / TICK))
		await _shot("showcase_%s_battle.png" % tag)
		print("PERF %s primitives=%d draw_calls=%d objects=%d" % [map_id, Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)])
		if "--gif" in args:
			for i in 48:
				await _shot("showcase_gif_%03d.png" % i)
		set_process(false)
		var tn: Node3D = tower_nodes[sids[0]]
		cam.projection = Camera3D.PROJECTION_PERSPECTIVE
		cam.fov = 34
		cam.global_position = tn.global_position + Vector3(5.0, 5.2, 7.5)
		cam.look_at(tn.global_position + Vector3(-0.6, 0.6, 0))
		for i in 4:
			_sync_visuals(1.0)
			await get_tree().process_frame
		await _shot("showcase_%s_close.png" % tag)
		if portal_nodes.has(0):
			_hub_camera()
			for i in 4:
				await get_tree().process_frame
			await _shot("showcase_%s_hub.png" % tag)
		if "--city" in args:                         # (the city at the end of the road, from up the road)
			var ce := _v3(sim.path[sim.path.size() - 1], 0.0)
			cam.global_position = ce + Vector3(-7.5, 5.5, 4.5)
			cam.look_at(ce + Vector3(0.5, 0.8, 0))
			for i in 4:
				await get_tree().process_frame
			await _shot("showcase_%s_city.png" % tag)
		for a6 in args:                              # (--look=x,z: a landmark from the south)
			if a6.begins_with("--look="):
				var xz := a6.trim_prefix("--look=").split(",")
				var lp := Vector3(float(xz[0]), 0.0, float(xz[1]))
				cam.global_position = lp + Vector3(0.0, 6.0, 8.5)
				cam.look_at(lp + Vector3(0, 1.0, 0))
				for i in 4:
					await get_tree().process_frame
				await _shot("showcase_%s_look.png" % tag)
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


# ---------------------------------------------------------------- drag scrolling
# Every scroll area can be dragged (finger or mouse) or wheel-scrolled from anywhere inside it,
# with no scroll bar shown. A drag that starts on a button cancels that button's tap.


## Scroll areas scroll by drag or wheel, with no bar drawn (and no room kept for one).
func _no_scrollbar(n: Node) -> void:
	if n is ScrollContainer:
		var sc := n as ScrollContainer
		if sc.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
			sc.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
		if sc.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
			sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER

const DRAG_SCROLL_START := 14.0
var _ds_sc: ScrollContainer = null
var _ds_start := Vector2.ZERO
var _ds_scroll0 := 0.0
var _ds_active := false
var _ds_vel := 0.0
var _ds_prev_y := 0.0
var _ds_prev_t := 0.0
var _ds_fling: ScrollContainer = null


func _now() -> float:
	return Time.get_ticks_msec() / 1000.0


func _scroll_under(pos: Vector2) -> ScrollContainer:
	if ui_root == null:
		return null
	# the topmost open dialog wins; nothing underneath it can be scrolled
	var root: Node = ui_root
	for m in modals:
		if is_instance_valid(m) and (m as Control).is_visible_in_tree():
			if root == ui_root or (m as Node).is_greater_than(root):
				root = m
	var best: ScrollContainer = null
	for n in root.find_children("*", "ScrollContainer", true, false):
		var sc := n as ScrollContainer
		if sc.is_visible_in_tree() and sc.get_global_rect().has_point(pos):
			if best == null or sc.is_greater_than(best):
				best = sc
	return best


func _input(event: InputEvent) -> void:
	if _place_drag_input(event):
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			var wsc := _scroll_under(mb.position)
			if wsc != null:
				_ds_fling = null
				var dir := -1.0 if mb.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0
				wsc.scroll_vertical = int(wsc.scroll_vertical + dir * 90.0 * maxf(1.0, mb.factor))
				get_viewport().set_input_as_handled()
			return
		if mb.button_index != MOUSE_BUTTON_LEFT:
			return
		if mb.pressed:
			_ds_fling = null
			_ds_sc = _scroll_under(mb.position)
			_ds_active = false
			if _ds_sc != null:
				_ds_start = mb.position
				_ds_scroll0 = float(_ds_sc.scroll_vertical)
				_ds_prev_y = mb.position.y
				_ds_prev_t = _now()
				_ds_vel = 0.0
		else:
			if _ds_active and is_instance_valid(_ds_sc) and absf(_ds_vel) > 120.0 and _now() - _ds_prev_t < 0.12:
				_ds_fling = _ds_sc
			_ds_sc = null
			_ds_active = false
	elif event is InputEventMouseMotion and _ds_sc != null:
		var mm := event as InputEventMouseMotion
		if not is_instance_valid(_ds_sc) or not (mm.button_mask & MOUSE_BUTTON_MASK_LEFT):
			_ds_sc = null
			_ds_active = false
			return
		var d := mm.position - _ds_start
		if not _ds_active:
			if absf(d.y) < DRAG_SCROLL_START or absf(d.y) < absf(d.x):
				return
			_ds_active = true
			_ds_start = mm.position
			_ds_scroll0 = float(_ds_sc.scroll_vertical)
			d = Vector2.ZERO
			# cancel the tap on whatever button the drag started on
			for n in _ds_sc.find_children("*", "BaseButton", true, false):
				var b := n as BaseButton
				if not b.disabled and not b.toggle_mode and b.get_draw_mode() in [BaseButton.DRAW_PRESSED, BaseButton.DRAW_HOVER_PRESSED]:
					b.disabled = true
					b.disabled = false
		_ds_sc.scroll_vertical = int(_ds_scroll0 - d.y)
		var dt := maxf(0.016, _now() - _ds_prev_t)
		var v := (_ds_prev_y - mm.position.y) / dt
		_ds_vel = lerpf(_ds_vel, v, 0.6)
		_ds_prev_y = mm.position.y
		_ds_prev_t = _now()
		get_viewport().set_input_as_handled()


func _drag_scroll_tick(delta: float) -> void:
	if _ds_fling == null:
		return
	if not is_instance_valid(_ds_fling) or not _ds_fling.is_visible_in_tree() or absf(_ds_vel) < 30.0:
		_ds_fling = null
		return
	var before := _ds_fling.scroll_vertical
	_ds_fling.scroll_vertical = int(_ds_fling.scroll_vertical + _ds_vel * delta)
	if _ds_fling.scroll_vertical == before:
		_ds_fling = null
		return
	_ds_vel *= pow(0.05, delta)
