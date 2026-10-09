## Presentation layer: draws the simulation in 3D, runs HUD, audio and touch/mouse input.
## All game rules live in Sim; this file only reads sim state and sends player commands.
extends Node3D

const TICK := Sim.TICK
const TOWER_ORDER := ["rock_slinger", "club_warrior", "boulder_catapult", "tar_shaman"]
const SIDEBAR_W := 380.0
const MAX_STEPS_PER_FRAME := 12
const PITCH := 54.0
const GROUND_RECT := Rect2(-21.0, -13.0, 40.0, 26.0)   # must match tools/gen_ground.py

const TOWER_SCENES := {
	"rock_slinger": preload("res://assets/towers/rock_slinger.glb"),
	"club_warrior": preload("res://assets/towers/club_warrior.glb"),
	"boulder_catapult": preload("res://assets/towers/boulder_catapult.glb"),
	"tar_shaman": preload("res://assets/towers/tar_shaman.glb"),
}
const TOWER_SCALE := {"rock_slinger": 0.56, "club_warrior": 0.56, "boulder_catapult": 0.58, "tar_shaman": 0.56}
## attack swing per tower: [wind-up offset, strike offset] in radians on the Arm pivot (+ = forward)
const SWING := {"rock_slinger": [-1.4, 0.9], "club_warrior": [-0.7, 1.6], "boulder_catapult": [-0.15, 2.0], "tar_shaman": [-0.5, 0.35]}
const ROBOT_SCENES := {
	"scout": preload("res://assets/robots/scout.glb"),
	"walker": preload("res://assets/robots/walker.glb"),
	"brute": preload("res://assets/robots/brute.glb"),
	"carrier": preload("res://assets/robots/carrier.glb"),
	"prime_walker": preload("res://assets/robots/prime_walker.glb"),
}
const ROBOT_SCALE := {"scout": 0.9, "walker": 0.9, "brute": 0.9, "carrier": 0.9, "prime_walker": 1.0}
const ROBOT_BAR_H := {"scout": 1.2, "walker": 1.45, "brute": 1.65, "carrier": 1.2, "prime_walker": 4.4}
const ICONS := {
	"rock_slinger": preload("res://assets/ui/icon_rock_slinger.png"),
	"club_warrior": preload("res://assets/ui/icon_club_warrior.png"),
	"boulder_catapult": preload("res://assets/ui/icon_boulder_catapult.png"),
	"tar_shaman": preload("res://assets/ui/icon_tar_shaman.png"),
}
const TEX_GROUND := preload("res://assets/textures/ground_mammoth_valley.png")
const ICON_GOLD := preload("res://assets/ui/icon_gold.png")
const ICON_LIVES := preload("res://assets/ui/icon_lives.png")
const ICON_WAVE := preload("res://assets/ui/icon_wave.png")
const ICON_PLAY := preload("res://assets/ui/icon_play.png")
const FONT := preload("res://assets/fonts/LilitaOne.woff2")
const SFX_NAMES := ["throw", "rock_hit", "club", "catapult", "boulder_land", "pulse", "robot_death", "boss_death", "coin",
	"place", "upgrade", "wave_horn", "life_lost", "boss_roar", "summon", "click", "error", "victory", "defeat"]

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

var placing := ""
var selected := -1
var ghost: Node3D
var ghost_range: MeshInstance3D
var ghost_foot: MeshInstance3D
var sel_range: MeshInstance3D

# audio
var sfx := {}
var sfx_players: Array = []
var sfx_last := {}
var music: AudioStreamPlayer
var muted := false

# HUD
var lbl_gold: Label
var lbl_lives: Label
var lbl_wave: Label
var btn_start: Button
var btn_speed: Button
var btn_mute: Button
var shop_box: VBoxContainer
var shop_buttons := {}
var tower_box: VBoxContainer
var tower_icon: TextureRect
var lbl_t_name: Label
var lbl_t_info: Label
var up_box: VBoxContainer
var btn_sell: Button
var toast: Label
var toast_t := 0.0
var banner: Label
var banner_t := 0.0
var overlay: Control
var lbl_overlay: Label
var lbl_overlay_sub: Label
var btn_endless: Button
var title_screen: Control
var demo := false


func _ready() -> void:
	defs = Defs.load_all()
	map = Defs.load_map("mammoth_valley")
	sim = Sim.new()
	sim.setup(defs, map)
	_build_world()
	_build_audio()
	_build_hud()
	demo = "--demo" in OS.get_cmdline_user_args()
	if demo:
		_run_demo()


# =================================================================== helpers
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


# =================================================================== world
func _build_world() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.12, 0.3, 0.1)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.82, 0.88, 1.0)
	env.ambient_light_energy = 0.36
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.glow_enabled = true
	env.glow_intensity = 0.32
	env.glow_strength = 1.0
	env.glow_bloom = 0.0
	env.glow_hdr_threshold = 1.25
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, -40, 0)
	sun.light_color = Color(1.0, 0.95, 0.86)
	sun.light_energy = 0.74
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
	gm.albedo_texture = TEX_GROUND
	gm.albedo_color = Color(0.9, 0.9, 0.88)
	gm.roughness = 1.0
	gm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mi(pm, gm, self, Vector3(GROUND_RECT.position.x + GROUND_RECT.size.x * 0.5, 0, GROUND_RECT.position.y + GROUND_RECT.size.y * 0.5))
	var far := PlaneMesh.new()
	far.size = Vector2(160, 120)
	_mi(far, _mat("far_ground", Color(0.13, 0.32, 0.1)), self, Vector3(0, -0.02, 0))

	_build_portal(sim.path[0])
	_build_cave(sim.path[sim.path.size() - 1])
	_build_decor()

	sel_range = _mi(_cyl(1, 1, 0.02, 48), _mat("range", Color(1, 1, 1, 0.16), {"unshaded": true}), self, Vector3(0, 0.12, 0))
	sel_range.visible = false
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


func _build_portal(p: Vector2) -> void:
	var n := Node3D.new()
	n.position = _v3(p + Vector2(1.3, 0), 0)
	n.rotation.y = PI * 0.5 - 0.65
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


func _build_cave(p: Vector2) -> void:
	var n := Node3D.new()
	n.position = _v3(p, 0)
	add_child(n)
	var rock := _mat("cave_rock", Color(0.46, 0.43, 0.4))
	var rock2 := _mat("cave_rock2", Color(0.36, 0.34, 0.32))
	_mi(_sph(1.7, 9), rock, n, Vector3(0.8, 0.2, 0), Vector3(0, 0.4, 0), Vector3(1, 0.95, 1.35))
	_mi(_sph(1.0, 8), rock2, n, Vector3(1.0, 0.9, -1.1), Vector3.ZERO, Vector3(1.1, 1.0, 1))
	_mi(_sph(0.95, 8), _mat("cave_mouth", Color(0.04, 0.03, 0.03)), n, Vector3(-0.6, 0.45, 0), Vector3.ZERO, Vector3(0.45, 0.85, 0.9))
	var fire := Node3D.new()
	fire.position = Vector3(-1.5, 0, 1.6)
	n.add_child(fire)
	for k in 3:
		_mi(_cyl(0.07, 0.07, 0.8, 5), _mat("wood", Color(0.45, 0.27, 0.12)), fire, Vector3(0, 0.1, 0), Vector3(PI * 0.5, k * 1.05, 0))
	var flame := _mi(_cyl(0.0, 0.32, 0.7, 6), _mat("flame", Color(1.0, 0.55, 0.1), {"emit": Color(1.0, 0.45, 0.05), "emit_e": 2.5}), fire, Vector3(0, 0.45, 0))
	var flame2 := _mi(_cyl(0.0, 0.18, 0.45, 5), _mat("flame2", Color(1.0, 0.9, 0.4), {"emit": Color(1.0, 0.8, 0.3), "emit_e": 2.5}), fire, Vector3(0, 0.35, 0))
	for k in 6:
		var a := TAU * k / 6.0
		_mi(_sph(0.12, 6), rock2, fire, Vector3(cos(a) * 0.45, 0.05, sin(a) * 0.45), Vector3.ZERO, Vector3(1, 0.6, 1))
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.6, 0.25)
	light.light_energy = 2.0
	light.omni_range = 4.0
	light.position = Vector3(0, 0.8, 0)
	fire.add_child(light)
	effects.append({"node": fire, "life": INF, "t": 0.0, "kind": "fire", "f1": flame, "f2": flame2, "light": light})


func _build_decor() -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 11
	var b: Array = map.bounds
	var trunk := _mat("trunk", Color(0.36, 0.22, 0.1))
	var pines := [_mat("pine1", Color(0.11, 0.36, 0.14)), _mat("pine2", Color(0.16, 0.44, 0.15))]
	var bush := [_mat("bush1", Color(0.22, 0.5, 0.15)), _mat("bush2", Color(0.3, 0.56, 0.18))]
	var placed := 0
	var tries := 0
	while placed < 95 and tries < 2000:
		tries += 1
		var x := r.randf_range(-19.5, 17.5)
		var z := r.randf_range(-12.0, 12.0)
		var inside: bool = x > b[0] - 0.8 and x < b[2] + 0.8 and z > b[1] - 0.8 and z < b[3] + 0.8
		if inside or sim.dist_to_path(Vector2(x, z)) < 2.2:
			continue
		placed += 1
		var t := Node3D.new()
		t.position = Vector3(x, 0, z)
		var s := r.randf_range(0.75, 1.35)
		t.scale = Vector3(s, s * r.randf_range(0.9, 1.2), s)
		t.rotation.y = r.randf() * TAU
		add_child(t)
		if r.randf() < 0.72:
			_mi(_cyl(0.12, 0.16, 0.6, 6), trunk, t, Vector3(0, 0.3, 0))
			var pm: Material = pines[r.randi() % 2]
			_mi(_cyl(0.0, 0.85, 1.3, 7), pm, t, Vector3(0, 1.05, 0))
			_mi(_cyl(0.0, 0.62, 1.0, 7), pines[(r.randi() + 1) % 2], t, Vector3(0, 1.65, 0))
			_mi(_cyl(0.0, 0.38, 0.7, 7), pm, t, Vector3(0, 2.15, 0))
		else:
			var bm: Material = bush[r.randi() % 2]
			_mi(_sph(0.55, 8), bm, t, Vector3(0, 0.35, 0), Vector3.ZERO, Vector3(1.2, 0.8, 1.1))
			_mi(_sph(0.4, 7), bush[(r.randi() + 1) % 2], t, Vector3(0.4, 0.3, 0.2), Vector3.ZERO, Vector3(1, 0.8, 1))
	for i in 22:
		var x2 := r.randf_range(-19.0, 17.0)
		var z2 := r.randf_range(-12.0, 12.0)
		var inside2: bool = x2 > b[0] and x2 < b[2] and z2 > b[1] and z2 < b[3]
		if inside2 or sim.dist_to_path(Vector2(x2, z2)) < 1.5:
			continue
		_mi(_sph(r.randf_range(0.3, 0.7), 7), _mat("boulder", Color(0.52, 0.5, 0.47)), self, Vector3(x2, 0.12, z2), Vector3(0, r.randf() * 3, 0), Vector3(1.25, 0.7, 1))


# =================================================================== audio
func _build_audio() -> void:
	for n in SFX_NAMES:
		sfx[n] = load("res://assets/audio/%s.wav" % n)
	for i in 14:
		var p := AudioStreamPlayer.new()
		add_child(p)
		sfx_players.append(p)
	music = AudioStreamPlayer.new()
	music.stream = load("res://assets/audio/music_stone_age.wav")
	music.volume_db = -9.0
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


# =================================================================== towers
func _make_tower_visual(type: String) -> Node3D:
	var root := Node3D.new()
	var model: Node3D = TOWER_SCENES[type].instantiate()
	model.scale = Vector3.ONE * float(TOWER_SCALE[type])
	root.add_child(model)
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
	return root


func _spawn_tower_node(t: Dictionary) -> void:
	var n := _make_tower_visual(t.type)
	n.position = _v3(t.pos)
	add_child(n)
	var deco := Node3D.new()
	deco.name = "Deco"
	n.add_child(deco)
	tower_nodes[t.id] = n
	_refresh_tower_node(t)
	_ring_fx(_v3(t.pos, 0.2), 1.1, Color(1, 0.9, 0.5), 0.4)
	_dust_fx(_v3(t.pos, 0.2), 8, 0.9)
	_sfx("place")
	# drop-in pop
	n.scale = Vector3(0.6, 1.4, 0.6)
	var tw := create_tween()
	tw.tween_property(n, "scale", Vector3.ONE * (1.0 + 0.04 * t.level), 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


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
	var r: float = float(TOWER_SCALE[t.type]) * 1.62
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
	var root := Node3D.new()
	var model: Node3D = ROBOT_SCENES[type].instantiate()
	model.scale = Vector3.ONE * float(ROBOT_SCALE[type])
	model.name = "Model"
	root.add_child(model)
	root.set_meta("legsA", model.find_children("LegA*", "", true, false))
	root.set_meta("legsB", model.find_children("LegB*", "", true, false))
	root.set_meta("body", model.find_child("Body", true, false))
	root.set_meta("punch", 0.0)
	var h: float = ROBOT_BAR_H[type]
	if type == "prime_walker":
		var tag := Label3D.new()
		tag.text = "PRIME WALKER"
		tag.font = FONT
		tag.font_size = 80
		tag.outline_size = 18
		tag.pixel_size = 0.011
		tag.modulate = Color(1, 0.35, 0.3)
		tag.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		tag.no_depth_test = true
		tag.position = Vector3(0, h + 0.6, 0)
		root.add_child(tag)
	var bar := Node3D.new()
	bar.name = "Bar"
	bar.position = Vector3(0, h, 0)
	root.add_child(bar)
	var bw := 2.0 if type == "prime_walker" else 0.8
	var q := QuadMesh.new()
	q.size = Vector2(bw, 0.22 if type == "prime_walker" else 0.12)
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


func _update_effects(dt: float) -> void:
	var keep := []
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
				fx.light.light_energy = 1.8 + 0.4 * sin(time_s * 11.0)
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
		if fx.t >= fx.life:
			n.queue_free()
		else:
			keep.append(fx)
	effects = keep


# =================================================================== loop
func _process(delta: float) -> void:
	time_s += delta
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
	cam.position = cam_base + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)) * shake * shake * 0.6


func _handle_events() -> void:
	for ev in sim.events:
		match ev.e:
			"place":
				_spawn_tower_node(sim.get_tower(ev.id))
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
					if e.type == "prime_walker":
						shake = 1.0
						_sfx("boss_roar", -6.0, 0.0)
						_banner("THE PRIME WALKER HAS ARRIVED", Color(1, 0.35, 0.3))
			"hit":
				if enemy_nodes.has(ev.id):
					enemy_nodes[ev.id].set_meta("punch", 1.0)
			"kill":
				if enemy_nodes.has(ev.id):
					var n2: Node3D = enemy_nodes[ev.id]
					var big: bool = ev.type == "prime_walker"
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
				var tf = sim.get_tower(ev.id)
				_sfx("catapult" if tf.type == "boulder_catapult" else "throw", -8.0, 0.15, 0.05)
			"slam":
				_animate_fire(ev.id)
				var t2 = sim.get_tower(ev.id)
				_ring_fx(_v3(t2.pos, 0.2), ev.radius, Color(1, 0.8, 0.45), 0.35)
				_dust_fx(_v3(t2.pos + t2.facing * 0.8, 0.2), 5, 0.7)
				_sfx("club", -4.0, 0.12, 0.05)
			"pulse":
				_animate_fire(ev.id)
				var t3 = sim.get_tower(ev.id)
				_ring_fx(_v3(t3.pos, 0.25), ev.radius, Color(1, 0.5, 0.1) if t3.branch == "B" else Color(0.4, 1.0, 0.5), 0.6)
				if tower_nodes[ev.id].has_meta("orb"):
					var orb: Node3D = tower_nodes[ev.id].get_meta("orb")
					orb.scale = Vector3.ONE * 2.2
				_sfx("pulse", -7.0, 0.1, 0.08)
			"proj":
				var p = _proj_by_id(ev.id)
				if p != null:
					var size := 0.11
					var col2 := Color(0.6, 0.58, 0.55)
					var opts := {}
					if p.kind == "lob":
						size = 0.26
					if p.src.dtype == "fire":
						col2 = Color(1, 0.5, 0.1)
						opts = {"emit": Color(1, 0.4, 0.05), "emit_e": 2.5}
					elif p.src.dtype == "blunt" and p.kind == "homing":
						size = 0.17
					var pn := _mi(_sph(size, 6), _mat("proj_%s" % col2.to_html(), col2, opts), self, _v3(p.pos, 1.3))
					proj_nodes[ev.id] = pn
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
				_toast("Wave %d cleared!  +%d gold" % [ev.wave, ev.bonus], C_GOLD)
				_sfx("coin", -4.0, 0.0)
			"victory":
				_show_overlay(true)
			"defeat":
				_show_overlay(false)
	sim.events.clear()


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
	var t = sim.get_tower(id)
	var arm: Node3D = n.get_meta("arm")
	var rest: float = arm.get_meta("rest")
	var sw: Array = SWING[t.type]
	var dur: float = clampf(float(t.stats.cooldown) * 0.7, 0.18, 0.6) / float(speed)
	var tw := create_tween()
	tw.tween_property(arm, "rotation:x", rest + sw[0], dur * 0.35).set_trans(Tween.TRANS_SINE)
	tw.tween_property(arm, "rotation:x", rest + sw[1], dur * 0.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_property(arm, "rotation:x", rest, dur * 0.45).set_trans(Tween.TRANS_SINE)


func _sync_visuals(alpha: float) -> void:
	for e in sim.enemies:
		if not enemy_nodes.has(e.id):
			continue
		var n: Node3D = enemy_nodes[e.id]
		var p: Vector2 = e.prev_pos.lerp(e.pos, alpha)
		n.position = _v3(p)
		var dir := sim.dir_at(e.dist)
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
			if e.type == "scout" or e.type == "carrier":
				bob = sin(time_s * 5.0 + e.id) * 0.08
			body.position.y = bob
			body.rotation.z = sin(time_s * 40.0) * 0.12 if stunned else 0.0
		var punch: float = n.get_meta("punch")
		if punch > 0.0:
			n.set_meta("punch", maxf(0.0, punch - 0.18))
			var model: Node3D = n.get_node("Model")
			var sc: float = float(ROBOT_SCALE[e.type]) * (1.0 + punch * 0.12)
			model.scale = Vector3(sc, sc * (1.0 - punch * 0.08), sc)
		var bar: Node3D = n.get_node("Bar")
		if e.hp < e.max_hp:
			bar.visible = true
			var fg: MeshInstance3D = bar.get_node("Fg")
			var f: float = clampf(e.hp / e.max_hp, 0.0, 1.0)
			fg.scale.x = maxf(f, 0.001)
			fg.position.x = -(1.0 - f) * (fg.mesh as QuadMesh).size.x * 0.5
	for p in sim.projectiles:
		if not proj_nodes.has(p.id):
			continue
		var pn: Node3D = proj_nodes[p.id]
		pn.rotation += Vector3(8, 5, 0) * get_process_delta_time()
		if p.kind == "lob":
			var k: float = clampf((p.t + alpha * TICK) / p.flight, 0.0, 1.0)
			pn.position = _v3(p.start.lerp(p.aim, k), 1.0 + 3.4 * 4.0 * k * (1.0 - k))
		else:
			pn.position = pn.position.lerp(_v3(p.pos, 1.1), 0.6)
	for t in sim.towers:
		if not tower_nodes.has(t.id):
			continue
		var tn: Node3D = tower_nodes[t.id]
		if tn.has_meta("yaw"):
			var yaw_node: Node3D = tn.get_meta("yaw")
			yaw_node.rotation.y = lerp_angle(yaw_node.rotation.y, _yaw(t.facing), 0.2)
		if tn.has_meta("orb"):
			var orb: Node3D = tn.get_meta("orb")
			orb.scale = orb.scale.lerp(Vector3.ONE * (1.0 + 0.1 * sin(time_s * 4.0)), 0.1)


# =================================================================== input
func _ground_point(screen: Vector2) -> Vector2:
	var o := cam.project_ray_origin(screen)
	var d := cam.project_ray_normal(screen)
	if absf(d.y) < 0.0001:
		return Vector2.INF
	var t := -o.y / d.y
	var p := o + d * t
	return Vector2(p.x, p.z)


func _unhandled_input(event: InputEvent) -> void:
	if not started:
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
		var t = sim.tower_at(gp)
		if t != null:
			_select(t.id)
			_sfx("click", -6.0)
		else:
			_deselect()
	elif event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_ESCAPE:
				_cancel_placing()
				_deselect()
			KEY_SPACE:
				_on_start_pressed()
			KEY_1, KEY_2, KEY_3, KEY_4:
				_begin_placing(TOWER_ORDER[event.keycode - KEY_1])


func _begin_placing(type: String) -> void:
	_sfx("click", -6.0)
	_deselect()
	if placing == type:
		_cancel_placing()
		return
	if sim.gold < int(defs.towers[type].cost):
		_toast("Not enough gold", Color(1, 0.45, 0.4))
		_sfx("error", -4.0, 0.0)
		return
	placing = type
	for c in ghost.get_children():
		if c != ghost_range and c != ghost_foot:
			c.queue_free()
	ghost.add_child(_make_tower_visual(type))
	var def: Dictionary = defs.towers[type]
	var r := float(def.base.range)
	ghost_range.scale = Vector3(r, 1, r)
	ghost_foot.scale = Vector3(float(def.radius), 1, float(def.radius))
	ghost.visible = true
	_move_ghost(Vector2(-1.0, 0.0))
	_update_shop_highlight()
	_toast("Tap the map to place %s" % def.name, C_TEXT)


func _move_ghost(p: Vector2) -> void:
	if p == Vector2.INF or placing == "":
		return
	ghost.position = _v3(p)
	var err := sim.placement_error(placing, p)
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
	_show_tower_panel(id)


func _deselect() -> void:
	selected = -1
	sel_range.visible = false
	tower_box.visible = false
	shop_box.visible = true


func _on_start_pressed() -> void:
	if not started:
		return
	if sim.start_wave():
		_sfx("click", -6.0)


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


func _button(text: String, col: Color, font := 28) -> Button:
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
	var theme := Theme.new()
	theme.default_font = FONT
	theme.default_font_size = 28
	var layer := CanvasLayer.new()
	add_child(layer)
	var root := Control.new()
	root.theme = theme
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(root)

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
	var era := _label("STONE AGE", 30, Color(1, 0.78, 0.45))
	era.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(era)
	var sub := _label("Mammoth Valley", 20, Color(0.85, 0.75, 0.6), 6)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(sub)

	shop_box = VBoxContainer.new()
	shop_box.add_theme_constant_override("separation", 10)
	shop_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	col.add_child(shop_box)
	for i in TOWER_ORDER.size():
		var type: String = TOWER_ORDER[i]
		var def: Dictionary = defs.towers[type]
		var c := Color(def.color[0], def.color[1], def.color[2])
		var b := _button("%s\n%d gold" % [def.name, int(def.cost)], c.lerp(Color(0.45, 0.3, 0.18), 0.35), 26)
		b.icon = ICONS[type]
		b.expand_icon = true
		b.add_theme_constant_override("icon_max_width", 92)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(0, 118)
		b.tooltip_text = "%s  [%d]\n%s" % [def.lineage, i + 1, def.desc]
		b.pressed.connect(_begin_placing.bind(type))
		shop_box.add_child(b)
		shop_buttons[type] = b

	tower_box = VBoxContainer.new()
	tower_box.add_theme_constant_override("separation", 8)
	tower_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tower_box.visible = false
	col.add_child(tower_box)
	var head := HBoxContainer.new()
	tower_box.add_child(head)
	tower_icon = _icon(ICONS["rock_slinger"], 84)
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
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tower_box.add_child(spacer)
	btn_sell = _button("", Color(0.62, 0.22, 0.16), 24)
	btn_sell.custom_minimum_size = Vector2(0, 64)
	btn_sell.pressed.connect(func():
		if selected != -1:
			sim.sell_tower(selected)
			_handle_events()
			_deselect())
	tower_box.add_child(btn_sell)

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
	btn_mute = _button("Sound", Color(0.32, 0.3, 0.36), 20)
	btn_mute.custom_minimum_size = Vector2(100, 46)
	btn_mute.pressed.connect(func():
		muted = not muted
		btn_mute.text = "Muted" if muted else "Sound"
		if muted:
			music.stop()
		else:
			music.play())
	small.add_child(btn_mute)
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
	again.pressed.connect(func(): get_tree().reload_current_scene())
	ob.add_child(again)
	btn_endless = _button("ENDLESS MODE", Color(0.5, 0.28, 0.6), 32)
	btn_endless.custom_minimum_size = Vector2(300, 96)
	btn_endless.pressed.connect(func():
		sim.endless = true
		sim.state = "ready"
		overlay.visible = false
		_banner("ENDLESS", Color(0.85, 0.6, 1))
		_toast("How long can you hold the cave?", Color(0.85, 0.6, 1)))
	ob.add_child(btn_endless)
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
	var t3 := _label("The machines came back through time to erase humanity.\nHold the cave.", 28, C_TEXT, 8)
	t3.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tb.add_child(t3)
	var t4 := _label("STONE AGE  -  MAMMOTH VALLEY", 26, Color(0.95, 0.7, 0.45), 8)
	t4.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tb.add_child(t4)
	var play := _button("PLAY", Color(0.2, 0.58, 0.18), 52)
	play.custom_minimum_size = Vector2(380, 120)
	play.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	play.pressed.connect(_start_game)
	tb.add_child(play)


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
	sb.set_content_margin_all(44)
	sb.shadow_size = 24
	panel.add_theme_stylebox_override("panel", sb)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_theme_constant_override("separation", 22)
	box.custom_minimum_size = Vector2(900, 0)
	panel.add_child(box)
	shade.set_meta("box", box)
	return shade


func _start_game() -> void:
	started = true
	title_screen.visible = false
	if not muted and not demo:
		music.play()
	_sfx("click")
	_toast("Pick a tower on the right, then tap the map to place it", C_TEXT)
	toast_t = 4.5


func _show_tower_panel(id: int) -> void:
	var t = sim.get_tower(id)
	if t == null:
		_deselect()
		return
	shop_box.visible = false
	tower_box.visible = true
	var def: Dictionary = defs.towers[t.type]
	tower_icon.texture = ICONS[t.type]
	lbl_t_name.text = sim.tower_display_name(t)
	var s: Dictionary = t.stats
	var rate := 1.0 / float(s.cooldown)
	var lines := "%s  -  Tier %d/5\n" % [def.lineage, t.level]
	lines += "Damage %s (%s)  Range %.1f\nAttacks %.1f/sec   Kills %d" % [str(snappedf(float(s.damage), 0.1)), s.dtype, float(s.range), rate, t.kills]
	if s.has("splash") and float(s.splash) > 0:
		lines += "\nSplash %.1f" % float(s.splash)
	if s.has("slow"):
		lines += "   Slow %d%%" % int(float(s.slow) * 100)
	if t.branch != "":
		lines += "\nPath %s: %s" % [t.branch, def.branches[t.branch].name]
	lbl_t_info.text = lines
	for c in up_box.get_children():
		c.queue_free()
	var opts := sim.upgrade_options(t)
	if opts.is_empty():
		up_box.add_child(_label("MAX TIER", 34, C_GOLD))
	for o in opts:
		var title: String = ("PATH %s: " % o.key) if o.get("branch_pick", false) else ""
		var bcol := Color(0.7, 0.36, 0.12) if o.key == "A" else (Color(0.14, 0.42, 0.62) if o.key == "B" else Color(0.26, 0.5, 0.2))
		var b := _button("%s%s  -  %d gold\n%s" % [title, o.name, o.cost, o.desc], bcol, 21)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(0, 104)
		b.set_meta("cost", o.cost)
		b.pressed.connect(func():
			if not sim.upgrade_tower(id, o.key):
				_toast("Not enough gold", Color(1, 0.45, 0.4))
				_sfx("error", -4.0, 0.0)
			_handle_events())
		up_box.add_child(b)
	if opts.size() == 2:
		up_box.add_child(_label("Choose one. The other path locks.", 20, Color(1, 0.72, 0.45), 6))
	btn_sell.text = "SELL  +%d gold" % sim.sell_value(t)
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


func _update_hud(delta: float) -> void:
	lbl_gold.text = str(sim.gold)
	lbl_lives.text = str(sim.lives)
	lbl_wave.text = ("%d/%d" % [sim.wave, sim.total_waves]) if not (sim.endless or sim.wave > sim.total_waves) else ("%d  ENDLESS" % sim.wave)
	for type in shop_buttons:
		shop_buttons[type].disabled = sim.gold < int(defs.towers[type].cost)
	for b in up_box.get_children():
		if b is Button:
			b.disabled = sim.gold < int(b.get_meta("cost"))
	if sim.can_start_wave():
		btn_start.disabled = false
		btn_start.text = ("START\nWAVE %d" if sim.enemies.is_empty() else "SEND\nWAVE %d") % (sim.wave + 1)
	else:
		btn_start.disabled = true
		btn_start.text = "WAVE %d" % sim.wave
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
		lbl_overlay.text = "VICTORY!"
		lbl_overlay.add_theme_color_override("font_color", C_GOLD)
		lbl_overlay_sub.text = "The Prime Walker is scrap metal. The cave stands.\n%d robots destroyed  -  %d lives left" % [sim.stats.kills, sim.lives]
		btn_endless.visible = true
	else:
		_sfx("defeat")
		lbl_overlay.text = "THE CAVE HAS FALLEN"
		lbl_overlay.add_theme_color_override("font_color", Color(1, 0.45, 0.4))
		lbl_overlay_sub.text = "You held out until wave %d.\n%d robots destroyed." % [sim.wave, sim.stats.kills]
		btn_endless.visible = false


# =================================================================== demo/screenshots
func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png("user://" + name)
	print("SHOT ", ProjectSettings.globalize_path("user://" + name))


func _wait_ticks(n: int) -> void:
	var target := sim.tick + n
	while sim.tick < target:
		await get_tree().process_frame


func _run_demo() -> void:
	for i in 3:
		await get_tree().process_frame
	await _shot("demo_0_title.png")
	_start_game()
	sim.gold += 5200
	var spots := {
		"rock_slinger": [Vector2(-6.0, 0.0), Vector2(0.5, 1.0), Vector2(7.3, 1.0), Vector2(13.0, 1.5)],
		"club_warrior": [Vector2(-6.0, 6.7), Vector2(0.5, -7.6)],
		"boulder_catapult": [Vector2(0.5, 6.8)],
		"tar_shaman": [Vector2(7.3, 7.0)],
	}
	var ids := []
	for type in spots:
		for p in spots[type]:
			ids.append(sim.place_tower(type, p))
	_handle_events()
	for k in 2:
		for id in ids:
			sim.upgrade_tower(id, "")
	sim.upgrade_tower(ids[1], "B")
	sim.upgrade_tower(ids[1], "B")
	sim.upgrade_tower(ids[6], "A")
	sim.upgrade_tower(ids[4], "A")
	_handle_events()
	speed = 3
	for w in 7:
		sim.start_wave()
		while not sim.can_start_wave() or not sim.enemies.is_empty():
			await get_tree().process_frame
	speed = 1
	sim.start_wave()   # wave 8
	await _wait_ticks(int(13.0 / TICK))
	await _shot("demo_1_battle.png")
	_select(ids[2])
	await _wait_ticks(8)
	await _shot("demo_2_branch_choice.png")
	_deselect()
	speed = 3
	while not sim.can_start_wave() or not sim.enemies.is_empty():
		await get_tree().process_frame
	sim.gold += 9000
	for id in ids:
		for k in 3:
			var t = sim.get_tower(id)
			if t != null and t.level < 5:
				sim.upgrade_tower(id, t.branch if t.branch != "" else "A")
	_handle_events()
	sim.wave = 19
	speed = 1
	sim.start_wave()   # wave 20: the boss
	await _wait_ticks(int(15.0 / TICK))
	await _shot("demo_3_boss.png")
	print("DEMO_DONE")
	get_tree().quit()
