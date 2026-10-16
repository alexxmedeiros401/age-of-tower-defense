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
	"emp", "explosion", "flame", "freeze", "javelin", "laser", "missile", "musket", "plasma", "rifle", "shell", "steam", "swing", "zap"]

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
	if not defs.heroes.heroes.has(hid) or not (test_mode or Progress.hero_unlocked(defs.heroes.heroes[hid])):
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
	_mi(pm, gm, self, Vector3(GROUND_RECT.position.x + GROUND_RECT.size.x * 0.5, 0, GROUND_RECT.position.y + GROUND_RECT.size.y * 0.5))
	var far := PlaneMesh.new()
	far.size = Vector2(160, 120)
	_mi(far, _mat("far_ground", _edge_color(gm.albedo_texture, theme.far), {"rough": 1.0}), self, Vector3(0, -0.02, 0))

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
	elif _style2() and DECOR_V2.has(str(map.get("theme", "meadow"))):
		_build_cave_v2(end_pt)
	else:
		_build_cave(end_pt)
	_build_decor()
	_build_blockers()
	_decor_roots = get_children().slice(d0)
	if "--export-decor" not in OS.get_cmdline_user_args():
		_swap_baked_decor()
		if not DECOR_V2.has(str(map.get("theme", ""))):
			_ambient_fx(Vector3.INF)

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
	# scorched launch pad with hazard ring
	_mi(_cyl(2.3, 2.5, 0.12, 24), dark, n, Vector3(0, 0.06, 0))
	_mi(_cyl(2.05, 2.05, 0.03, 24), _mat("portal_pad_glow", Color(0.3, 0.8, 1.0, 0.55), {"emit": Color(0.2, 0.7, 1.0), "emit_e": 1.6, "unshaded": true}), n, Vector3(0, 0.13, 0))
	_mi(_cyl(1.8, 1.8, 0.04, 24), steel, n, Vector3(0, 0.14, 0))
	# swirl on the pad too, so the portal reads from the top-down game camera
	var gq := QuadMesh.new()
	gq.size = Vector2(3.5, 3.5)
	var gsw := _mi(gq, _glow_mat("vortex_ground", Color(0.45, 0.3, 1.0, 0.9), _swirl_tex()), n, Vector3(0, 0.17, 0), Vector3(-PI * 0.5, 0, 0))
	var gsw2 := _mi(gq, _glow_mat("vortex_ground2", Color(0.2, 0.9, 1.0, 0.6), _swirl_tex()), n, Vector3(0, 0.18, 0), Vector3(-PI * 0.5, 0, 0), Vector3.ONE * 0.7)
	for k in 8:
		var aa := TAU * k / 8.0
		_mi(_box(0.5, 0.05, 0.16), _mat("portal_hazard", Color(1.0, 0.75, 0.1), {"emit": Color(1.0, 0.6, 0.05), "emit_e": 0.8}), n,
			Vector3(cos(aa) * 2.15, 0.14, sin(aa) * 2.15), Vector3(0, -aa, 0))
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
	var lights := Node3D.new()
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
	var layers := [gsw, gsw2]
	var cols := [Color(0.35, 0.2, 1.0, 0.95), Color(0.2, 0.9, 1.0, 0.8), Color(1.0, 0.3, 0.9, 0.55), Color(1, 1, 1, 0.5)]
	for i in 4:
		var l := _mi(q, _glow_mat("vortex_%d" % i, cols[i], _swirl_tex()), vortex, Vector3(0, 0, -0.06 * i + 0.09), Vector3.ZERO, Vector3.ONE * (1.0 - 0.12 * i))
		layers.append(l)
	var back := _mi(_cyl(1.36, 1.36, 0.02, 32), _mat("vortex_back", Color(0.05, 0.02, 0.15)), vortex, Vector3(0, 0, 0.16), Vector3(PI * 0.5, 0, 0))
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
	light.position = Vector3(0, hz, -0.6)
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


## Decor goes in the ring around the playable area (outside map.bounds), clear of roads and the base.
func _decor_free(p: Vector2, clearance := 0.0) -> bool:
	var b: Array = map.bounds
	var inside: bool = p.x > b[0] - 0.8 - clearance and p.x < b[2] + 0.8 + clearance and p.y > b[1] - 0.8 - clearance and p.y < b[3] + 0.8 + clearance
	if inside or sim.dist_to_path(p) < 2.2 + clearance:
		return false
	var end_pt: Vector2 = sim.path[sim.path.size() - 1]
	if p.x > 13.0 and absf(p.y - end_pt.y) < 6.5:
		return false
	return true


func _build_decor() -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 11
	var th: String = map.get("theme", "meadow")
	if EraDecor.handles(th):
		EraDecor.build_decor(self, th, _decor_free)
		return
	if _style2() and DECOR_V2.has(th):
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
}
var _decor_lib := {}


func _decor_theme() -> Dictionary:
	return DECOR_V2.get(str(map.get("theme", "meadow")), {})


func _decor_mesh(name: String) -> Mesh:
	if _decor_lib.is_empty():
		var src := _inst("res://assets/decor/%s.glb" % str(_decor_theme().get("kit", "stone_decor")))
		for mi in src.find_children("*", "MeshInstance3D", true, false):
			_decor_lib[str(mi.name)] = (mi as MeshInstance3D).mesh
		src.free()
	return _decor_lib.get(name)


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
	var taken := []      # [Vector2, radius] of landmarks so scatter keeps clear of them
	for mk in dt.marks:
		var p: Vector2 = mk[1]
		var ok := false
		for tries in 30:
			if _decor_free(p, 0.6) or mk[0] == "Volcano":
				ok = true
				break
			p = mk[1] + Vector2(r.randf_range(-2.5, 2.5), r.randf_range(-1.2, 1.2))
		if ok:
			var n := _decor_single(mk[0], _v3(p), r.randf_range(-0.5, 0.5) + (PI if p.y > 0 else 0.0), mk[2])
			taken.append([p, float(mk[3])])
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
	# ground cover inside the playfield, off the road and clear of no-build zones
	for i in int(dt.cover_n):
		var p3 := Vector2(r.randf_range(b[0], b[2]), r.randf_range(b[1], b[3]))
		if sim.dist_to_path(p3) < float(map.get("path_width", 1.7)) * 0.5 + 0.5:
			continue
		var in_block := false
		for bl in map.get("blockers", []):
			if p3.distance_to(Vector2(bl[0], bl[1])) < float(bl[2]) + 0.4:
				in_block = true
		if in_block:
			continue
		put.call(_pick_weighted(dt.cover, r), p3, r.randf_range(0.8, 1.3) * (0.6 if dt.kit != "stone_decor" else 1.0), r.randf() * TAU)
	for nm in batches:
		_decor_batch(nm, batches[nm], not (nm in ["Tuft", "Flowers"]))


func _build_cave_v2(p: Vector2) -> void:
	var n := _decor_single("Cave", _v3(p) + Vector3(0.1, 0, 0), 0.0, 0.95)
	var fire_pos := Vector3(-1.6, 0, 1.75)
	var wood := _mat("wood", Color(0.45, 0.27, 0.12))
	var rock2 := _mat("cave_rock2", Color(0.32, 0.31, 0.3))
	for k in 3:
		_mi(_cyl(0.07, 0.07, 0.8, 5), wood, n, fire_pos + Vector3(0, 0.1, 0), Vector3(PI * 0.5, k * 1.05, 0))
	for k in 6:
		var a := TAU * k / 6.0
		_mi(_sph(0.12, 6), rock2, n, fire_pos + Vector3(cos(a) * 0.45, 0.05, sin(a) * 0.45), Vector3.ZERO, Vector3(1, 0.6, 1))
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
	if not _style2() or DECOR_V2.has(str(map.get("theme", ""))):
		return
	var path := "res://assets/decor/maps/%s.glb" % map_id
	if not ResourceLoader.exists(path):
		return
	var list := _decor_static()
	var baked := _inst(path)
	var want := -1
	for c in [baked] + baked.get_children():
		if str(c.name).begins_with("Decor_"):
			want = int(str(c.name).trim_prefix("Decor_").get_slice(".", 0).get_slice("_", 0))
	if want != list.size():
		push_warning("baked decor for %s is stale (%d meshes, now %d): keeping runtime scenery" % [map_id, want, list.size()])
		baked.free()
		return
	for mi in list:
		(mi as Node).queue_free()
	for ol in baked.find_children("*_Outline", "MeshInstance3D", true, false):
		(ol as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		(ol as MeshInstance3D).visible = Progress.gfx_level() < 2
	add_child(baked)


func _export_decor(path: String) -> void:
	var list := _decor_static()
	var sc := Node3D.new()
	sc.name = "Decor_%d" % list.size()
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
		if _style2() and DECOR_V2.has(th):
			if _blocker_v2(kind, n, rad, r):
				continue
			if kind == "lava":
				var lava2 := _mi(_cyl(rad * 0.85, rad * 0.85, 0.04, 28), _mat("pool_lava", Color(1, 0.55, 0.15, 0.45), {"emit": Color(1, 0.42, 0.05), "emit_e": 1.0, "unshaded": true}), n, Vector3(0, 0.04, 0))
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
	_rig_extras(root, model)


## v2 art: Spin* nodes whirl (slings, rotors, orbiting stones), Flicker* nodes flicker (fires),
## *_Outline meshes are the baked cartoon outline shells (no shadows; off on MINIMAL graphics).
func _rig_extras(root: Node3D, model: Node3D) -> void:
	var spins := model.find_children("Spin*", "Node3D", true, false)
	if not spins.is_empty():
		root.set_meta("spins", spins)
	var flick := model.find_children("Flicker*", "Node3D", true, false)
	if not flick.is_empty():
		root.set_meta("flicker", flick)
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
	var want: Material = _flash_mats[lvl] if lvl >= 0 else null
	if want == null:
		n.remove_meta("flash_on")
	else:
		n.set_meta("flash_on", true)
	for mi in n.get_meta("body_mis", []):
		(mi as MeshInstance3D).material_overlay = want


func _spin_flicker(n: Node3D, dt: float, rate := 9.0) -> void:
	if n.has_meta("spins"):
		for sp in n.get_meta("spins"):
			(sp as Node3D).rotation.y += dt * rate
	if n.has_meta("flicker"):
		var i := 0
		for f in n.get_meta("flicker"):
			var k := 1.0 + 0.14 * sin(time_s * 13.0 + i * 2.1) + 0.06 * sin(time_s * 29.0 + i)
			(f as Node3D).scale = Vector3(2.0 - k, k, 2.0 - k)
			i += 1


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
	var model: Node3D = _inst("res://assets/robots/%s.glb" % type)
	model.scale = Vector3.ONE * float(d.get("model_scale", 0.9))
	model.name = "Model"
	root.add_child(model)
	root.set_meta("legsA", model.find_children("LegA*", "", true, false))
	root.set_meta("legsB", model.find_children("LegB*", "", true, false))
	root.set_meta("body", model.find_child("Body", true, false))
	root.set_meta("punch", 0.0)
	_rig_extras(root, model)
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
					mats[key] = gm
				swaps.append([mi, si, mats[key]])
		root.set_meta("ghost", swaps)
	var flame := _mi(_cyl(0.0, 0.22, 0.55, 6), _mat("burn_flame", Color(1, 0.55, 0.1, 0.85), {"emit": Color(1, 0.45, 0.05), "emit_e": 2.5, "unshaded": true}),
		root, Vector3(0, h * 0.55, 0))
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
				_fx_meshes[key] = _sph(0.5, 10)
			"dust":
				_fx_meshes[key] = _sph(0.18, 6)
			"pebble":
				_fx_meshes[key] = _sph(0.5, 4)
			"disc":
				_fx_meshes[key] = _cyl(1, 1, 0.02, 16)
			"mote":
				var q := QuadMesh.new()
				q.size = Vector2(0.09, 0.09)
				_fx_meshes[key] = q
	return _fx_meshes[key]


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
	var f := _mi(_fx_mesh("flash"), _mat("flash", Color(1, 0.7, 0.4, 0.8), {"emit": Color(1, 0.5, 0.2), "emit_e": 3.0, "unshaded": true}), self, pos)
	effects.append({"node": f, "t": 0.0, "life": 0.18, "kind": "flash", "s": 1.6 if big else 0.8})


func _dust_fx(pos: Vector3, count: int, spread := 0.6, col := Color(0.78, 0.68, 0.5, 0.7)) -> void:
	if not _fx_room(count):
		count = mini(count, 2)
		if not _fx_room(count):
			return
	var key := "dust_%s" % col.to_html()
	for i in count:
		var d := _mi(_fx_mesh("dust"), _mat(key, col, {"unshaded": true}), self, pos)
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


## v2 robot death: white armor plates fly, red sparks, a smoke puff and a scorch mark that fades.
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
	_dust_fx(pos + Vector3(0, 0.3, 0), 4 if big else 3, 0.5 if not big else 1.4, Color(0.25, 0.25, 0.27, 0.7))
	var sc := _mi(_fx_mesh("disc"), _mat("scorch", Color(0.05, 0.04, 0.03, 0.45), {"unshaded": true}), self,
		Vector3(pos.x, 0.035, pos.z), Vector3(0, randf() * TAU, 0), Vector3(1.0, 1.0, 1.0) * (1.6 if big else 0.42))
	sc.material_override = (sc.material_override as StandardMaterial3D).duplicate()
	effects.append({"node": sc, "t": 0.0, "life": 2.6, "kind": "scorch"})


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
	for i in int(spec.n):
		var m := _mi(_fx_mesh("mote"), _mat("mote_" + th, spec.col, {"unshaded": true, "billboard": true}), holder,
			Vector3(randf_range(b[0] - 3.0, b[2] + 3.0), randf_range(0.2, 6.0) if spec.vy != 0.0 else randf_range(0.4, 1.6), randf_range(b[1] - 3.0, b[3] + 3.0)),
			Vector3.ZERO, Vector3.ONE * float(spec.s) * randf_range(0.7, 1.3))
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		m.set_meta("seed", randf() * 100.0)


func _boulder_drop_fx(target: Vector3, delay: float) -> void:
	var b := _mi(_sph(0.35, 6), _mat("drop_rock", Color(0.5, 0.48, 0.45)), self, target + Vector3(0, 9, 0))
	b.visible = false
	effects.append({"node": b, "t": -delay, "life": 0.45, "kind": "fall", "from": target + Vector3(0.6, 9, -0.4), "to": target + Vector3(0, 0.3, 0)})


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
	for p in landed:
		_dust_fx(p, 7, 1.0)
		shake = maxf(shake, 0.35)


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
				var sz: float = float(fx.get("s", 1.0)) * (1.0 - k * k)
				n.scale = Vector3(sz, sz * 0.25, sz) if fx.get("flat", false) else Vector3.ONE * sz
			"scorch":
				(n.material_override as StandardMaterial3D).albedo_color.a = 0.45 * (1.0 - k * k)
			"ambient":
				fx.smoke_t = float(fx.smoke_t) - dt
				if fx.smoke_t <= 0.0 and fx.fire != Vector3.INF:
					fx.smoke_t = 0.35
					if _fx_room(1):
						var pf := _mi(_fx_mesh("dust"), _mat("smoke", Color(0.6, 0.6, 0.62, 0.45), {"unshaded": true}), self, fx.fire + Vector3(0, 1.0, 0))
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
				n.transparency = 0.35 + 0.65 * k
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
	return fx.t < fx.life


# =================================================================== loop
func _process(delta: float) -> void:
	time_s += delta
	_drag_scroll_tick(delta)
	_fit_modals()
	if paused or (started and detail_open > 0):
		_update_hud(0.0)
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
	for ev in sim.events:
		match ev.e:
			"place":
				_spawn_tower_node(sim.get_tower(ev.id))
			"hero_place":
				_spawn_hero_node()
			"hero_level":
				_refresh_hero_tag()
				if sim.hero != null:
					_float_text(_v3(sim.hero.pos, 2.5), "RANK %d!" % ev.level, C_GOLD, 60)
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
					_ring_fx(_v3(u2.pos, 0.2), ev.radius, Color(1, 0.8, 0.45) if u2.type != "flamethrower" else Color(1, 0.5, 0.1), 0.35)
					_dust_fx(_v3(u2.pos + u2.facing * 0.8, 0.2), 5, 0.7)
					if _style2():
						_pebble_fx(_v3(u2.pos + u2.facing * 1.0, 0.3), 3)
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
				if u3 != null:
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
					proj_nodes[ev.id] = _make_projectile(p)
			"impact":
				if proj_nodes.has(ev.pid):
					proj_nodes[ev.pid].queue_free()
					proj_nodes.erase(ev.pid)
				if ev.splash > 0.0:
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
			_mi(_sph(0.2, 8), _mat("cannonball", Color(0.12, 0.12, 0.13), {"metal": 0.5, "rough": 0.4}), root)
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
			_mi(_sph(0.22, 10), _mat("plasma", Color(1.0, 0.4, 0.95), {"emit": Color(1.0, 0.3, 0.9), "emit_e": 4.0, "unshaded": true}), root)
			_mi(_sph(0.34, 10), _mat("plasma_glow", Color(1.0, 0.5, 1.0, 0.3), {"unshaded": true}), root)
		"arc":
			_mi(_sph(0.16, 8), _mat("arc_ball", Color(0.75, 0.9, 1.0), {"emit": Color(0.5, 0.8, 1.0), "emit_e": 4.0, "unshaded": true}), root)
			root.set_meta("spin", true)
		_:
			_mi(_sph(0.15, 6), _mat("proj_default", Color(0.6, 0.58, 0.55)), root)


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


func _ability_fx(ev: Dictionary) -> void:
	var hp := _v3(ev.pos, 0.3)
	var aname := str(sim.hero_def.ability.name).to_upper() + "!"
	match str(ev.get("type", "")):
		"rain":
			var i := 0
			for p in ev.hits:
				_boulder_drop_fx(_v3(p), i * 0.06)
				i += 1
			_banner(aname, Color(0.9, 0.8, 0.6))
			_sfx("ab_stone_rain" if _era_index() < 4 else "airstrike", 0.0, 0.0, 0.5)
			return
		"quake":
			_ring_fx(hp, 26.0, Color(0.75, 0.55, 0.3), 1.0)
			_ring_fx(hp, 14.0, Color(0.85, 0.65, 0.35), 0.7)
			for e in sim.enemies:
				_dust_fx(_v3(e.pos, 0.2), 3, 0.6)
			shake = 1.4
			_banner(aname, Color(0.85, 0.6, 1.0))
			_sfx("ab_earthquake", 0.0, 0.0, 0.5)
			return
		"flare":
			_ring_fx(hp, float(ev.radius), Color(1, 0.6, 0.25), 0.7)
			_ring_fx(hp, float(ev.radius) * 0.6, Color(1, 0.9, 0.5), 0.5)
			var f := _mi(_sph(1.0, 12), _mat("flare", Color(1, 0.85, 0.4, 0.6), {"emit": Color(1, 0.8, 0.3), "emit_e": 3.0, "unshaded": true}), self, hp + Vector3(0, 1.0, 0))
			effects.append({"node": f, "t": 0.0, "life": 0.35, "kind": "flash", "s": 2.5})
			shake = 0.7
			_banner(aname, C_GOLD)
			_sfx("ab_solar_flare" if str(ev.ability) == "solar_flare" else "explosion", 0.0, 0.0, 0.5)
			return
		"fury":
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
		if n.has_meta("emerge"):
			# grows out of the vortex over its first steps
			var ek := clampf((float(e.dist) - Sim.SPAWN_DIST) / 1.0, 0.0, 1.0)
			ek = ek * ek * (3.0 - 2.0 * ek)
			n.scale = Vector3.ONE * lerpf(0.05, 1.0, ek)
			n.position.y += (1.0 - ek) * 1.0
			if ek >= 1.0:
				n.remove_meta("emerge")
				n.scale = Vector3.ONE
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
		_spin_flicker(n, get_process_delta_time(), 0.0 if stunned else 24.0)
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
		var bubble: MeshInstance3D = n.get_node_or_null("Bubble")
		if bubble != null:
			bubble.visible = e.shield > 0.0
			if bubble.visible:
				var bmat: StandardMaterial3D = bubble.material_override
				bmat.albedo_color.a = 0.1 + 0.2 * clampf(e.shield / maxf(e.max_shield, 1.0), 0.0, 1.0)
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
		if e.hp < e.max_hp:
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
		_spin_flicker(tn, pdt, 0.0 if sim.tick < int(t.get("stun_until", 0)) else 9.0)
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
	l.add_theme_color_override("font_outline_color", Color(0.02, 0.04, 0.1, 0.95))
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
		var track := _style(Color(0.03, 0.05, 0.09, 0.9), 10)
		track.set_content_margin_all(11)
		track.shadow_size = 0
		var grab := _style(Color(0.31, 0.47, 0.74), 10)
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
	tower_icon = _icon(_icon_tex(types[0]), 84)
	head.add_child(tower_icon)
	lbl_t_name = _label("", 30, Color(1, 0.88, 0.55))
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
	btn_details = _button("DETAILS", Color(0.3, 0.36, 0.5), 22)
	btn_details.custom_minimum_size = Vector2(0, 56)
	btn_details.pressed.connect(func():
		var tt = sim.get_unit(selected) if selected != -1 else null
		if tt != null and not tt.get("is_hero", false):
			_sfx("click")
			_tower_detail(str(tt.type))
		elif tt != null:
			_sfx("click")
			_hero_detail(sim.hero_id, VBoxContainer.new()))
	tower_actions.add_child(btn_details)
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

	# --- end-of-match results (a sequence of pages, built when the match ends)
	overlay = _modal(root)
	_on_close(overlay, func():
		_sfx("click")
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


const MENU_GOLD := Color(0.5, 0.86, 1.0)


## Big round menu button with an icon and a banner label underneath (and an optional "!" badge).
func _round_button(icon: Texture2D, text: String, col: Color, size: float, cb: Callable, badge := false, icon_frac := 0.66) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_END
	v.add_theme_constant_override("separation", -14)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var b := Button.new()
	b.custom_minimum_size = Vector2(size, size)
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	b.pivot_offset = Vector2(size, size) * 0.5
	for st in ["normal", "hover", "pressed"]:
		var c := col
		if st == "hover":
			c = col.lightened(0.15)
		elif st == "pressed":
			c = col.darkened(0.15)
		var sb := StyleBoxFlat.new()
		sb.bg_color = c
		sb.set_corner_radius_all(int(size * 0.5))
		sb.set_border_width_all(int(size * 0.06))
		sb.border_color = MENU_GOLD.darkened(0.1)
		sb.shadow_color = Color(0, 0, 0, 0.45)
		sb.shadow_size = 10
		sb.shadow_offset = Vector2(0, 6)
		sb.anti_aliasing = true
		b.add_theme_stylebox_override(st, sb)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.icon = icon
	b.expand_icon = true
	b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	b.vertical_icon_alignment = VERTICAL_ALIGNMENT_CENTER
	b.add_theme_constant_override("icon_max_width", int(size * icon_frac))
	b.mouse_entered.connect(func():
		var tw := b.create_tween()
		tw.tween_property(b, "scale", Vector2.ONE * 1.08, 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT))
	b.mouse_exited.connect(func():
		var tw := b.create_tween()
		tw.tween_property(b, "scale", Vector2.ONE, 0.12))
	b.pressed.connect(func():
		_sfx("click")
		var tw := b.create_tween()
		tw.tween_property(b, "scale", Vector2.ONE * 0.92, 0.05)
		tw.tween_property(b, "scale", Vector2.ONE, 0.1)
		cb.call())
	v.add_child(b)
	if badge:
		var bd := Label.new()
		bd.text = "!"
		bd.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		bd.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		bd.add_theme_font_size_override("font_size", int(size * 0.26))
		bd.add_theme_color_override("font_color", Color.WHITE)
		var bsb := _style(Color(0.9, 0.15, 0.1), int(size * 0.17), Color.WHITE, 4)
		bsb.set_content_margin_all(0)
		bd.add_theme_stylebox_override("normal", bsb)
		bd.size = Vector2(size * 0.34, size * 0.34)
		bd.position = Vector2(size * 0.72, -size * 0.04)
		bd.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.add_child(bd)
		var tw2 := bd.create_tween().set_loops()
		tw2.tween_property(bd, "position:y", -size * 0.1, 0.45).set_trans(Tween.TRANS_SINE)
		tw2.tween_property(bd, "position:y", -size * 0.04, 0.45).set_trans(Tween.TRANS_SINE)
	if text != "":
		var ban := PanelContainer.new()
		var bsb2 := _style(Color(0.11, 0.18, 0.29), 14, MENU_GOLD.darkened(0.25), 4)
		bsb2.content_margin_left = 16
		bsb2.content_margin_right = 16
		bsb2.content_margin_top = 2
		bsb2.content_margin_bottom = 4
		ban.add_theme_stylebox_override("panel", bsb2)
		ban.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		ban.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var l := _label(text, 26 if size < 170 else 34, Color.WHITE, 8)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		ban.add_child(l)
		v.add_child(ban)
	v.set_meta("button", b)
	return v


## Rounded "pill" showing a currency, with an optional + button.
func _currency_pill(icon: Texture2D, text: String, col: Color, plus_cb := Callable()) -> PanelContainer:
	var pill := PanelContainer.new()
	var sb := _style(Color(0.04, 0.06, 0.1, 0.85), 30, MENU_GOLD.darkened(0.3), 4)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	pill.add_theme_stylebox_override("panel", sb)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	pill.add_child(h)
	h.add_child(_icon(icon, 54))
	var l := _label(text, 32, col, 8)
	l.custom_minimum_size = Vector2(110, 0)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	h.add_child(l)
	if plus_cb.is_valid():
		var pb := TextureButton.new()
		pb.texture_normal = _res("res://assets/ui/menu_plus.png")
		pb.ignore_texture_size = true
		pb.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
		pb.custom_minimum_size = Vector2(54, 54)
		pb.pressed.connect(func():
			_sfx("click")
			plus_cb.call())
		h.add_child(pb)
	return pill


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
	# ---- top left: profile (hero face, level star, XP bar)
	var prof := Control.new()
	prof.position = Vector2(24, 18)
	prof.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(prof)
	var face_frame := PanelContainer.new()
	var ffs := _style(Color(0.25, 0.45, 0.8), 18, MENU_GOLD, 6)
	ffs.set_content_margin_all(4)
	face_frame.add_theme_stylebox_override("panel", ffs)
	face_frame.custom_minimum_size = Vector2(118, 118)
	prof.add_child(face_frame)
	var hid := Progress.hero()
	if not defs.heroes.heroes.has(hid):
		hid = "ugo"
	var face := _icon(_face_tex(hid), 106)
	face_frame.add_child(face)
	var barbg := PanelContainer.new()
	var bbs := _style(Color(0.07, 0.1, 0.17, 0.95), 14, MENU_GOLD.darkened(0.3), 4)
	bbs.set_content_margin_all(5)
	barbg.add_theme_stylebox_override("panel", bbs)
	barbg.position = Vector2(150, 18)
	barbg.custom_minimum_size = Vector2(330, 50)
	prof.add_child(barbg)
	var pr := Progress.hero_level_progress(hid)
	var hmax := Progress.hero_level(hid) >= int(Progress.workshop.hero_levels.max)
	var pb := ProgressBar.new()
	pb.show_percentage = false
	pb.max_value = maxf(float(pr[1]), 1.0)
	pb.value = float(pr[0])
	pb.custom_minimum_size = Vector2(320, 38)
	var fill := _style(Color(0.3, 0.7, 1.0), 10)
	fill.shadow_size = 0
	var bgs := _style(Color(0.05, 0.08, 0.12), 10)
	bgs.shadow_size = 0
	pb.add_theme_stylebox_override("fill", fill)
	pb.add_theme_stylebox_override("background", bgs)
	barbg.add_child(pb)
	var xpl := _label("MAX LEVEL" if hmax else "%d / %d XP" % [pr[0], pr[1]], 22, Color.WHITE, 7)
	xpl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	xpl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	xpl.set_anchors_preset(Control.PRESET_FULL_RECT)
	pb.add_child(xpl)
	var star := _icon(_res("res://assets/ui/menu_star.png") as Texture2D, 104)
	star.position = Vector2(110, -6)
	prof.add_child(star)
	var lvl := _label(str(Progress.hero_level(hid)), 38, Color(0.07, 0.11, 0.19), 0)
	lvl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lvl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lvl.position = Vector2(110, 6)
	lvl.size = Vector2(104, 92)
	prof.add_child(lvl)
	var who := "%s  -  HERO LEVEL" % _short_name(str(defs.heroes.heroes[hid].name)).to_upper() + ("   -   TIMELINE %d" % Progress.timeline() if Progress.timeline() > 1 else "")
	var whol := _label(who, 24, MENU_GOLD, 8)
	whol.position = Vector2(210, 74)
	prof.add_child(whol)
	# ---- top centre: title
	var tbox := VBoxContainer.new()
	tbox.anchor_left = 0.5
	tbox.anchor_right = 0.5
	tbox.offset_left = -330
	tbox.offset_right = 330
	tbox.offset_top = 8
	tbox.add_theme_constant_override("separation", -18)
	tbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(tbox)
	var t1 := _label("AGE OF", 40, Color(1, 0.85, 0.6), 12)
	t1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tbox.add_child(t1)
	var t2 := _label("TOWER DEFENSE", 70, MENU_GOLD, 20)
	t2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	t2.add_theme_color_override("font_shadow_color", Color(0.5, 0.15, 0.0, 0.9))
	t2.add_theme_constant_override("shadow_offset_y", 6)
	tbox.add_child(t2)
	var bob := tbox.create_tween().set_loops()
	bob.tween_property(tbox, "offset_top", 16.0, 1.6).set_trans(Tween.TRANS_SINE)
	bob.tween_property(tbox, "offset_top", 8.0, 1.6).set_trans(Tween.TRANS_SINE)
	# ---- top right: currencies
	var cur := VBoxContainer.new()
	cur.anchor_left = 1.0
	cur.anchor_right = 1.0
	cur.offset_left = -330
	cur.offset_right = -24
	cur.offset_top = 20
	cur.add_theme_constant_override("separation", 10)
	cur.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(cur)
	cur.add_child(_currency_pill(ICON_SHARD, str(Progress.shards()), Color(0.85, 0.78, 1.0), func(): _open_heroes()))
	cur.add_child(_currency_pill(_icon_tex(str(Progress.era_towers(era_now)[0])) if not Progress.era_towers(era_now).is_empty() else ICON_GOLD,
		str(Progress.scrap(era_now)), Color(0.8, 0.9, 1.0), func(): _open_workshop("")))
	var sl := _label("%s SCRAP" % era_now.to_upper(), 16, Color(0.68, 0.73, 0.8), 5)
	sl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	cur.add_child(sl)
	# ---- left column: settings, quit
	var lcol := VBoxContainer.new()
	lcol.anchor_top = 0.5
	lcol.anchor_bottom = 0.5
	lcol.offset_left = 26
	lcol.offset_top = -170
	lcol.add_theme_constant_override("separation", 18)
	lcol.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(lcol)
	lcol.add_child(_round_button(_res("res://assets/ui/menu_gear.png"), "", Color(0.3, 0.42, 0.6), 108, func(): _open_settings()))
	if OS.has_feature("pc"):
		lcol.add_child(_round_button(_res("res://assets/ui/menu_door.png"), "", Color(0.16, 0.26, 0.43), 108, func(): get_tree().quit()))
	# ---- right column: age badge, new timeline
	var rcol := VBoxContainer.new()
	rcol.anchor_left = 1.0
	rcol.anchor_right = 1.0
	rcol.anchor_top = 0.5
	rcol.anchor_bottom = 0.5
	rcol.offset_left = -250
	rcol.offset_right = -26
	rcol.offset_top = -170
	rcol.alignment = BoxContainer.ALIGNMENT_BEGIN
	rcol.add_theme_constant_override("separation", 18)
	rcol.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_screen.add_child(rcol)
	var stars := 0
	for mid in map_order:
		stars += Progress.stars(mid)
	var age := PanelContainer.new()
	var asb := _style(Color(0.04, 0.06, 0.1, 0.85), 22, MENU_GOLD.darkened(0.3), 4)
	asb.set_content_margin_all(12)
	age.add_theme_stylebox_override("panel", asb)
	var av := VBoxContainer.new()
	av.add_theme_constant_override("separation", 2)
	age.add_child(av)
	var al1 := _label(era_now.to_upper(), 24, MENU_GOLD, 7)
	al1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	av.add_child(al1)
	var al2 := _label("Age %d of %d" % [_eras().find(era_now) + 1, _eras().size()], 20, C_TEXT, 5)
	al2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	av.add_child(al2)
	var srow := HBoxContainer.new()
	srow.alignment = BoxContainer.ALIGNMENT_CENTER
	srow.add_child(_icon(ICON_STAR, 34))
	srow.add_child(_label("%d / %d" % [stars, map_order.size() * 3], 22, C_COIN, 6))
	av.add_child(srow)
	rcol.add_child(age)
	if Progress.can_new_timeline(map_order):
		rcol.add_child(_round_button(_res("res://assets/ui/menu_portal.png"), "NEW TIMELINE", Color(0.42, 0.18, 0.6), 120, func(): _confirm_new_timeline(), true))
	# ---- bottom row: the big buttons
	var row := HBoxContainer.new()
	row.anchor_left = 0.5
	row.anchor_right = 0.5
	row.anchor_top = 1.0
	row.anchor_bottom = 1.0
	row.offset_left = -560
	row.offset_right = 560
	row.offset_top = -290
	row.offset_bottom = -18
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 30)
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
		_round_button(_icon_tex(str(et[0])) if not et.is_empty() else ICON_GOLD, "TOWERS", Color(0.2, 0.33, 0.54), 150, func(): _open_workshop(""), tower_badge, 0.8),
		_round_button(_face_tex(hid), "HEROS", Color(0.6, 0.25, 0.45), 150, func(): _open_heroes(), hero_badge, 0.78),
		_round_button(ICON_PLAY, "PLAY", Color(0.25, 0.72, 0.18), 196, func():
			Progress.current_map = cm
			get_tree().reload_current_scene(), false, 0.5),
		_round_button(_res("res://assets/ui/menu_upgrade.png"), "UPGRADES", Color(0.18, 0.42, 0.72), 150, func(): _open_legacy(), Progress.points_free() > 0),
		_round_button(_res("res://assets/ui/menu_map.png"), "MAPS", Color(0.25, 0.5, 0.4), 150, func():
			title_screen.visible = false
			map_select.visible = true),
	]
	for c in bot:
		c.size_flags_vertical = Control.SIZE_SHRINK_END
		row.add_child(c)
	# PLAY breathes, and says which map it starts
	var play: Button = bot[2].get_meta("button")
	var pulse := play.create_tween().set_loops()
	pulse.tween_property(play, "scale", Vector2.ONE * 1.06, 0.7).set_trans(Tween.TRANS_SINE)
	pulse.tween_property(play, "scale", Vector2.ONE, 0.7).set_trans(Tween.TRANS_SINE)
	var nm := _label("%s  -  Map %d" % [str(cme.get("name", "")), map_order.find(cm) + 1], 20, Color(0.85, 1.0, 0.8), 7)
	nm.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	(bot[2] as VBoxContainer).add_child(nm)
	var ver := _label("v%s" % str(ProjectSettings.get_setting("application/config/version", "")), 16, Color(0.62, 0.67, 0.75), 4)
	ver.anchor_top = 1.0
	ver.anchor_bottom = 1.0
	ver.offset_left = 16
	ver.offset_top = -34
	title_screen.add_child(ver)


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
	box.add_theme_constant_override("separation", 14)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 24)
	box.add_child(head)
	var ttl := _label("TOWERS  -  %s" % era.to_upper(), 52, C_GOLD, 12)
	ttl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(ttl)
	head.add_child(_label("SCRAP: %d" % Progress.scrap(era), 40, Color(0.75, 0.85, 0.95), 9))
	var done := _button("DONE", Color(0.2, 0.58, 0.18), 30)
	done.custom_minimum_size = Vector2(200, 70)
	done.pressed.connect(func():
		_sfx("click")
		dlg.queue_free()
		_refresh_menus())
	head.add_child(done)
	_close_with(dlg, done)
	var intro := _label("Each age has its own Scrap and its own towers. You start with one tower; unlock the rest in order, weakest to strongest, with Scrap from this age's maps. Every wave you clear pays, even when you lose. Every tower you unlock also gives ALL your towers in this age +%d%% damage. Scrap doesn't carry into the next age." % int(round(float(Progress.workshop.get("tech_bonus", 0.0)) * 100)) + "", 22, Color(0.78, 0.83, 0.9), 5)
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(intro)
	# era switcher (only ages the player has reached)
	var tabs := HFlowContainer.new()
	tabs.alignment = FlowContainer.ALIGNMENT_CENTER
	tabs.add_theme_constant_override("h_separation", 8)
	tabs.add_theme_constant_override("v_separation", 8)
	box.add_child(tabs)
	for en in _eras():
		if not Progress.is_unlocked(_first_map_of(en)):
			continue
		var tb := _button(en.to_upper(), Color(0.18, 0.28, 0.46), 18)
		tb.custom_minimum_size = Vector2(210, 50)
		tb.modulate = Color(1.25, 1.2, 0.95) if en == era else Color(0.75, 0.75, 0.75)
		tb.pressed.connect(func():
			_sfx("click")
			_open_workshop(en, dlg))
		tabs.add_child(tb)
	var cards := HFlowContainer.new()
	cards.alignment = FlowContainer.ALIGNMENT_CENTER
	cards.add_theme_constant_override("h_separation", 18)
	cards.add_theme_constant_override("v_separation", 18)
	box.add_child(cards)
	var rank := 0
	for tid in Progress.era_towers(era):
		rank += 1
		var def: Dictionary = defs.towers[tid]
		var own := Progress.tower_unlocked(tid)
		var cost := Progress.tower_scrap_cost(tid)
		var card := PanelContainer.new()
		card.add_theme_stylebox_override("panel", _style(Color(0.09, 0.15, 0.25) if own else Color(0.09, 0.13, 0.18), 18, C_GOLD.darkened(0.3) if own else C_PANEL_EDGE, 3))
		card.custom_minimum_size = Vector2(330, 0)
		cards.add_child(card)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 6)
		card.add_child(v)
		var ic := _icon(_icon_tex(tid), 150)
		ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		ic.modulate = Color.WHITE if own else Color(0.55, 0.55, 0.55)
		v.add_child(ic)
		var nm := _label("%d. %s" % [rank, str(def.name)], 30, C_TEXT, 7)
		nm.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(nm)
		var ln := _label("%s  -  %d gold to build" % [str(def.lineage), int(def.cost)], 18, Color(1, 0.8, 0.5), 5)
		ln.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(ln)
		var ds := _label(str(def.desc), 18, Color(0.78, 0.83, 0.9), 4)
		ds.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		ds.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		ds.custom_minimum_size = Vector2(290, 56)
		v.add_child(ds)
		var dbt := _button("DETAILS", Color(0.3, 0.36, 0.5), 20)
		dbt.custom_minimum_size = Vector2(0, 54)
		dbt.pressed.connect(func():
			_sfx("click")
			_tower_detail(tid))
		v.add_child(dbt)
		if own:
			var ok := _label("FREE" if cost == 0 else "UNLOCKED", 26, Color(0.6, 1.0, 0.6), 6)
			ok.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			v.add_child(ok)
		elif Progress.next_unlock(era) != tid:
			var lk := _label("UNLOCK #%d FIRST  -  %d SCRAP" % [rank - 1, cost], 20, Color(0.6, 0.66, 0.75), 5)
			lk.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			v.add_child(lk)
		else:
			var ub := _button("UNLOCK  -  %d SCRAP" % cost, Color(0.2, 0.55, 0.2), 22)
			ub.custom_minimum_size = Vector2(0, 64)
			ub.disabled = Progress.scrap(era) < cost
			ub.pressed.connect(func():
				if Progress.unlock_tower(tid):
					_sfx("upgrade")
					_open_workshop(era, dlg))
			v.add_child(ub)
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
		if not owned:
			hb.add_theme_color_override("icon_normal_color", Color(0.45, 0.45, 0.5))
			hb.add_theme_color_override("icon_hover_color", Color(0.55, 0.55, 0.6))
			var lk := _icon(ICON_LOCK, 40)
			lk.position = Vector2(104, 6)
			lk.mouse_filter = Control.MOUSE_FILTER_IGNORE
			hb.add_child(lk)
		hb.pressed.connect(func():
			_sfx("click")
			_hero_detail(hid, box))
		hrow.add_child(hb)
	var hd2: Dictionary = defs.heroes.heroes[cur]
	var now := _label("Playing as: %s, %s" % [hd2.name, hd2.title], 22, C_GOLD, 6)
	now.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(now)
	var tip := _label("Tap a hero to see what they do.", 18, Color(0.68, 0.75, 0.85), 5)
	tip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(tip)


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
	var model: Node3D = _inst(path)
	pivot.add_child(model)
	var box := AABB()
	var first := true
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var m3 := mi as MeshInstance3D
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
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.75, 0.72, 0.8)
	env.environment.ambient_light_energy = 0.7
	env.environment.background_mode = Environment.BG_CLEAR_COLOR
	vp.add_child(env)
	var tw := pivot.create_tween().set_loops()
	tw.tween_property(pivot, "rotation:y", TAU, 9.0).from(0.0)
	return svc


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
func _robot_roster(mid: String) -> void:
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
	_on_close(dlg, func():
		_sfx("click")
		dlg.queue_free())
	var ttl := _label("ROBOTS  -  %s" % str(me.get("name", mid)).to_upper(), 48, Color(1.0, 0.55, 0.5), 12)
	ttl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(ttl)
	var sub := _label("%s   -   Map %d of %d   -   20 waves. Stats are for this map." % [str(me.get("era", "")), map_order.find(mid) + 1, map_order.size()], 22, C_TEXT, 6)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(sub)
	var grid := HFlowContainer.new()
	grid.alignment = FlowContainer.ALIGNMENT_CENTER
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 14)
	box.add_child(grid)
	for pair in _map_robots(mid):
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
		h.add_child(ic)
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
	var back := _button("CLOSE", Color(0.3, 0.36, 0.5), 28)
	back.custom_minimum_size = Vector2(260, 80)
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	back.pressed.connect(func():
		_sfx("click")
		dlg.queue_free())
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
	# upgrade paths
	box.add_child(_label("UPGRADES", 30, C_GOLD, 8))
	var shared := ""
	for tr in d.get("tiers", []):
		shared += "%s (%d gold): %s.   " % [tr.name, int(tr.cost), tr.desc]
	var sl := _label("Tiers 1-2:  " + shared, 19, C_TEXT, 5)
	sl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(sl)
	var paths := HBoxContainer.new()
	paths.add_theme_constant_override("separation", 18)
	box.add_child(paths)
	for key in ["A", "B"]:
		if not d.branches.has(key):
			continue
		var br: Dictionary = d.branches[key]
		var bp := PanelContainer.new()
		var bcol := Color(0.7, 0.36, 0.12) if key == "A" else Color(0.14, 0.42, 0.62)
		bp.add_theme_stylebox_override("panel", _style(bcol.darkened(0.55), 16, bcol, 3))
		bp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		paths.add_child(bp)
		var bv := VBoxContainer.new()
		bv.add_theme_constant_override("separation", 3)
		bp.add_child(bv)
		bv.add_child(_label("PATH %s: %s" % [key, str(br.name).to_upper()], 24, bcol.lightened(0.45), 6))
		var bd := _label(str(br.desc), 18, C_TEXT, 4)
		bd.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		bv.add_child(bd)
		var ti := 3
		for tr in br.tiers:
			var tl := _label("Tier %d  %s (%d gold): %s" % [ti, tr.name, int(tr.cost), tr.desc], 17, Color(0.81, 0.85, 0.91), 4)
			tl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			bv.add_child(tl)
			ti += 1
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
		var locked := _button("LOCKED", Color(0.3, 0.3, 0.3), 30)
		locked.icon = ICON_LOCK
		locked.expand_icon = false
		locked.add_theme_constant_override("icon_max_width", 40)
		locked.custom_minimum_size = Vector2(260, 92)
		locked.disabled = true
		btns.add_child(locked)
		var cost := Progress.hero_cost(hd, defs.heroes.heroes)
		var avail := Progress.hero_available(hd)
		var have := Progress.shards()
		var buy_txt := "BUY  %d" % cost
		if not avail:
			buy_txt = "REACH THE %s" % str(hd.era).to_upper()
		var buy := _button(buy_txt, Color(0.45, 0.25, 0.75), 30)
		if avail:
			buy.icon = ICON_SHARD
			buy.add_theme_constant_override("icon_max_width", 48)
		buy.custom_minimum_size = Vector2(420, 92)
		buy.disabled = not avail or have < cost
		buy.pressed.connect(func():
			if Progress.buy_hero(hd, defs.heroes.heroes):
				_sfx("level_up")
				Progress.set_hero(hid)
				_toast("%s joins you!" % hd.name, C_GOLD)
				dlg.queue_free()
				_refresh_hero_pickers(picker_box)
				_hero_detail(hid, picker_box))
		btns.add_child(buy)
		var wallet := _label("You have %d Time Shards.%s" % [have, ("  Need %d more: earn them by playing maps and leveling up heros." % (cost - have)) if avail and have < cost else ""], 20, Color(0.8, 0.72, 1.0), 5)
		wallet.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		wallet.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(wallet)
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


func _update_hud(delta: float) -> void:
	hud_top.visible = started
	hud_side.visible = started
	btn_pause.visible = started
	lbl_gold.text = str(sim.gold)
	lbl_lives.text = str(sim.lives)
	lbl_wave.text = ("%d/%d" % [sim.wave, sim.total_waves]) if not (sim.endless or sim.wave > sim.total_waves) else ("%d  ENDLESS" % sim.wave)
	for type in shop_buttons:
		shop_buttons[type].disabled = _tower_open(type) and sim.gold < sim.tower_cost(type)
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
		out.append({"title": "SCRAP", "icon": _res("res://assets/ui/icon_scrap.png"), "amount": "+%d" % scrap, "col": Color(0.8, 0.88, 1.0),
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
		for i in results_pages.size():
			for f in 6:
				await get_tree().process_frame
			await _shot("results_%d.png" % i)
			results_page = mini(results_page + 1, results_pages.size() - 1)
			_show_results_page()
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
# not just on the bar. A drag that starts on a button cancels that button's tap.
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
