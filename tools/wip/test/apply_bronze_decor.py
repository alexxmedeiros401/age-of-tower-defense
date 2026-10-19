"""Game code for the HQ Bronze Age map kits (v0.9.28): python3 apply_bronze_decor.py game.gd
- DECOR_V2 kits for the delta, desert and canyon themes (used once their GLB is in assets/decor/), with the theme's
  ambient motes kept, papyrus and reeds along the river banks, decor kept out of the rivers, landmarks that can be
  forced into place and turned (the pyramid, the reed boats, the shaduf), and a ground-cover scale per theme;
- their no-build zones: papyrus round the delta's lake (its water moves in the ground), palm groves, sand dunes,
  ruined columns, red-rock pillars, and the copper pools (moving turquoise shader) ringed with malachite;
- the sculpted Bronze city (bronze_city.glb) in place of the box city, fires burning in its braziers;
- reed boats bob on the river; the smelter's furnace burns."""
import sys

p = sys.argv[1]
s = open(p).read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (c, a[:160])
    s = s.replace(a, b)


# ---------------------------------------------------------------- which themes use their kit
rep('''	elif _style2() and DECOR_V2.has(str(map.get("theme", "meadow"))):
		_build_cave_v2(end_pt)''', '''	elif _v2_kit(str(map.get("theme", "meadow"))):
		_build_cave_v2(end_pt)''')
rep('''		if not DECOR_V2.has(str(map.get("theme", ""))):
			_ambient_fx(Vector3.INF)''', '''		if not _v2_kit(str(map.get("theme", ""))) or bool(_decor_theme().get("ambient", false)):
			_ambient_fx(Vector3.INF)''')
rep('''	if _style2() and DECOR_V2.has(th):
		_build_decor_v2()
		return''', '''	if _v2_kit(th):
		_build_decor_v2()
		return''')
rep('''	if not _style2() or DECOR_V2.has(str(map.get("theme", ""))):
		return
	var path := "res://assets/decor/maps/%s.glb" % map_id''', '''	if not _style2() or _v2_kit(str(map.get("theme", ""))):
		return
	var path := "res://assets/decor/maps/%s.glb" % map_id''')
rep('''		if _style2() and DECOR_V2.has(th):
			if _blocker_v2(kind, n, rad, r):''', '''		if _v2_kit(th):
			if _blocker_v2(kind, n, rad, r):''')

# ---------------------------------------------------------------- the kits
rep('''	"volcano": {"kit": "stone_decor_volcano", "count": 85,
		"scatter": [["Dead_A", 14], ["Dead_B", 14], ["Rock_A", 12], ["Rock_B", 12], ["Rock_C", 10], ["Obsidian", 6], ["Stump", 3]],
		"cover": [["Tuft", 1]], "cover_n": 50,
		"marks": [["Volcano", Vector2(5.5, -12.4), 0.56, 4.2], ["Mammoth", Vector2(10.5, 10.8), 0.8, 2.6],
			["Obsidian", Vector2(-17.6, 1.0), 1.6, 1.4], ["Obsidian", Vector2(-9.0, 11.2), 1.3, 1.2]]},
}''', '''	"volcano": {"kit": "stone_decor_volcano", "count": 85,
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
	return best''')

# decor stays out of the water
rep('''	var end_pt: Vector2 = sim.path[sim.path.size() - 1]
	if p.x > 13.0 and absf(p.y - end_pt.y) < 6.5:
		return false
	return true''', '''	var end_pt: Vector2 = sim.path[sim.path.size() - 1]
	if p.x > 13.0 and absf(p.y - end_pt.y) < 6.5:
		return false
	if _river_gap(p) < 0.7 + clearance:               # (v0.9.28: not in a river)
		return false
	return true''')

# landmarks: forced placement and a set yaw
rep('''	for mk in dt.marks:
		var p: Vector2 = mk[1]
		var ok := false
		for tries in 30:
			if _decor_free(p, 0.6) or mk[0] == "Volcano":
				ok = true
				break
			p = mk[1] + Vector2(r.randf_range(-2.5, 2.5), r.randf_range(-1.2, 1.2))
		if ok:
			var n := _decor_single(mk[0], _v3(p), r.randf_range(-0.5, 0.5) + (PI if p.y > 0 else 0.0), mk[2])
			taken.append([p, float(mk[3])])''', '''	for mk in dt.marks:
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
				_campfire(n, Vector3(0, 1.22, 0), 1.6, 0.36)''')

# papyrus and reeds along the river banks
rep('''		placed += 1
		var nm := _pick_weighted(dt.scatter, r)
		var s := r.randf_range(0.75, 1.25) * (0.9 if nm.begins_with("Rock") else 1.0)
		put.call(nm, p2, s, r.randf() * TAU)''', '''		placed += 1
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
					rd += r.randf_range(0.9, 1.5)''')
rep('''	var dt := _decor_theme()
	var r := RandomNumberGenerator.new()
	r.seed = 11
	var b: Array = map.bounds
	var taken := []      # [Vector2, radius] of landmarks so scatter keeps clear of them''', '''	var dt := _decor_theme()
	var r := RandomNumberGenerator.new()
	r.seed = 11
	var b: Array = map.bounds
	var b0: Array = b
	var taken := []      # [Vector2, radius] of landmarks so scatter keeps clear of them''')
# ground cover: not in the water, scaled per theme
rep('''		var in_block := false
		for bl in map.get("blockers", []):
			if p3.distance_to(Vector2(bl[0], bl[1])) < float(bl[2]) + 0.4:
				in_block = true
		if in_block:
			continue
		put.call(_pick_weighted(dt.cover, r), p3, r.randf_range(0.8, 1.3) * (0.6 if dt.kit != "stone_decor" else 1.0), r.randf() * TAU)''',
    '''		var in_block := false
		for bl in map.get("blockers", []):
			if p3.distance_to(Vector2(bl[0], bl[1])) < float(bl[2]) + 0.4:
				in_block = true
		if in_block or _river_gap(p3) < 0.25:
			continue
		var cs: float = float(dt.get("cover_s", 0.6 if dt.kit != "stone_decor" else 1.0))
		put.call(_pick_weighted(dt.cover, r), p3, r.randf_range(0.8, 1.3) * cs, r.randf() * TAU)''')

# ---------------------------------------------------------------- no-build zones
rep('''		"lake":
			if th != "snow":
				return false
			_mi(_cyl(rad * 0.95, rad * 0.95, 0.02, 32), _mat("ice", Color(0.75, 0.9, 1.0, 0.3), {"rough": 0.05, "metal": 0.3}), n, Vector3(0, 0.03, 0))''',
    '''		"lake":
			if th == "delta":             # v0.9.28: its water moves in the ground; papyrus and reeds round the shore
				for k in 9:
					var a0 := TAU * k / 9.0 + r.randf() * 0.4
					var rr := rad + r.randf_range(0.05, 0.3)
					_decor_single(["Papyrus", "Reeds", "Papyrus"][k % 3], Vector3(cos(a0) * rr, 0, sin(a0) * rr), r.randf() * TAU, r.randf_range(0.5, 0.72), n)
				return true
			if th != "snow":
				return false
			_mi(_cyl(rad * 0.95, rad * 0.95, 0.02, 32), _mat("ice", Color(0.75, 0.9, 1.0, 0.3), {"rough": 0.05, "metal": 0.3}), n, Vector3(0, 0.03, 0))''')
rep('''		"rocks":
			for k in 4:
				var off := Vector2(r.randf_range(-0.5, 0.5), r.randf_range(-0.5, 0.5)) * rad
				_decor_single(["Rock_C", "Rock_A", "Rock_B", "Rock_A"][k], Vector3(off.x, 0, off.y), r.randf() * TAU, r.randf_range(0.7, 1.0) * rad * 0.8, n)
			return true
	return false''', '''		"rocks":
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
	return false''')

# ---------------------------------------------------------------- the city
rep('''func _build_city(p: Vector2) -> void:
	var n := Node3D.new()''', '''func _build_city(p: Vector2) -> void:
	if _city_kit(p):
		return
	var n := Node3D.new()''')
rep('''func _palm(parent: Node3D, pos: Vector3, s: float, r: RandomNumberGenerator) -> void:''',
    '''## v0.9.28: the sculpted Bronze city (bronze_city.glb): gate towers, gateway, walls, the ziggurat and town houses, one
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


func _palm(parent: Node3D, pos: Vector3, s: float, r: RandomNumberGenerator) -> void:''')

# ---------------------------------------------------------------- boats bob
rep('''			"lava":
				var pulse := 0.5 + 0.5 * sin((time_s + fx.t) * 2.2)''', '''			"bob":                                     # v0.9.28: a boat rocking on the river
				n.position.y = float(fx.y0) + 0.025 * sin(fx.t * 1.4)
				n.rotation.x = 0.035 * sin(fx.t * 1.1 + 0.6)
				n.rotation.z = 0.025 * sin(fx.t * 0.8)
			"lava":
				var pulse := 0.5 + 0.5 * sin((time_s + fx.t) * 2.2)''')

open(p, "w").write(s)
print("bronze decor code applied to", p)
