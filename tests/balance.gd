## Headless balance test: bots play all 20 waves of a map with different strategies,
## with and without heroes. Plans are written with Stone Age ids and translated to the
## map's era by lineage (rock_slinger -> bronze_archer, etc.).
## Run: godot --headless --path . --script res://tests/balance.gd -- <map_id>
extends SceneTree

const STONE := {"rock_slinger": "Ranged", "club_warrior": "Brute", "boulder_catapult": "Siege", "tar_shaman": "Control"}

var defs: Dictionary
var map: Dictionary
var samples := PackedVector2Array()
var era_ids := {}   # lineage -> tower id for this map's era
var max_perks := {}  # every Evolution perk at max rank


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var map_id: String = args[0] if args.size() > 0 else "mammoth_valley"
	map = Defs.load_map(map_id)
	defs = Defs.load_all(map)
	print("=== ", map.name, " [", map.get("era", "Stone Age"), "] (hp x", map.get("hp_mult", 1.0), ", start gold ", map.start_gold, ")")
	var s := Sim.new()
	s.setup(defs, map)
	for id in s.tower_types():
		era_ids[defs.towers[id].lineage] = id
	for pi in s.paths.size():
		var d := 0.0
		while d < s.paths[pi].length:
			samples.append(s.pos_at(d, pi))
			d += 0.25
	var era_heroes := []
	for h in defs.heroes.heroes:
		if str(defs.heroes.heroes[h].era) == str(map.get("era", "Stone Age")):
			era_heroes.append(h)

	var runs := [
		["lazy (2 ranged, no upgrades)", [["place", "rock_slinger"], ["place", "rock_slinger"]], false, ""],
		["ranged spam (no upgrades)", _repeat([["place", "rock_slinger"]], 40), false, ""],
		["balanced", _balanced(), true, ""],
		["siege heavy", _siege(), true, ""],
	]
	for h in era_heroes:
		runs.append(["balanced + " + h, _balanced(), true, h])
	if not era_heroes.is_empty():
		runs.append(["siege heavy + " + era_heroes[0], _siege(), true, era_heroes[0]])
	for r in runs:
		_run(r[0], r[1], r[2], r[3])
	# a fully evolved player (every Evolution perk maxed) for comparison
	var evo = JSON.parse_string(FileAccess.get_file_as_string("res://data/evolution.json"))
	for br in evo.branches:
		for pk in br.perks:
			max_perks[pk.id] = float(pk.per_rank) * int(pk.max)
	var mid := {}
	for k in max_perks:
		mid[k] = 0.0
	for k in ["start_gold", "damage", "speed", "cost", "lives"]:
		mid[k] = max_perks[k] * 0.6   # 3 ranks each = 15 points, about Evolution level 16
	var keep := max_perks
	max_perks = mid
	_run("balanced + MID evolution", _balanced(), true, "")
	max_perks = keep
	_run("balanced + MAX evolution", _balanced(), true, "")
	if not era_heroes.is_empty():
		_run("balanced + %s + MAX evolution" % era_heroes[0], _balanced(), true, era_heroes[0])
	quit()


func _t(stone_id: String) -> String:
	return era_ids[STONE[stone_id]]


func _repeat(a: Array, n: int) -> Array:
	var out := []
	for i in n:
		out.append_array(a)
	return out


func _balanced() -> Array:
	# indexes refer to the order towers were placed
	return [
		["place", "rock_slinger"], ["place", "rock_slinger"], ["up", 0, ""], ["place", "club_warrior"],
		["up", 1, ""], ["place", "tar_shaman"], ["up", 0, ""], ["up", 0, "A"],
		["place", "boulder_catapult"], ["up", 2, ""], ["up", 2, ""], ["up", 4, ""],
		["place", "rock_slinger"], ["up", 1, ""], ["up", 1, "B"], ["up", 4, ""], ["up", 4, "A"],
		["up", 3, ""], ["up", 2, "A"], ["place", "club_warrior"], ["up", 0, "A"], ["up", 1, "B"],
		["up", 5, ""], ["up", 5, ""], ["up", 5, "B"], ["up", 4, "A"], ["up", 3, ""], ["up", 3, "A"],
		["place", "boulder_catapult"], ["up", 7, ""], ["up", 7, ""], ["up", 7, "B"], ["up", 2, "A"],
		["up", 6, ""], ["up", 6, ""], ["up", 6, "B"], ["up", 0, "A"], ["up", 1, "B"], ["up", 4, "A"],
		["up", 7, "B"], ["up", 6, "B"], ["up", 5, "B"], ["up", 7, "B"],
	]


func _siege() -> Array:
	return [
		["place", "rock_slinger"], ["place", "rock_slinger"], ["place", "boulder_catapult"],
		["up", 2, ""], ["up", 2, ""], ["place", "boulder_catapult"], ["up", 2, "A"], ["up", 3, ""], ["up", 3, ""],
		["up", 3, "B"], ["place", "tar_shaman"], ["up", 2, "A"], ["up", 3, "B"], ["place", "boulder_catapult"],
		["up", 6, ""], ["up", 6, ""], ["up", 6, "A"], ["up", 2, "A"], ["up", 6, "A"], ["up", 3, "B"], ["up", 6, "A"],
	]


## After the opening plan: buy the cheapest affordable upgrade, otherwise add another tower.
func _spend_greedy(sim: Sim, placed: Array) -> void:
	var best_id := -1
	var best_key := ""
	var best_cost := 1 << 30
	for i in placed.size():
		var t = sim.get_tower(placed[i])
		if t == null:
			continue
		for o in sim.upgrade_options(t):
			var want: String = "A" if i % 2 == 0 else "B"
			if o.get("branch_pick", false) and o.key != want:
				continue
			if o.cost < best_cost:
				best_cost = o.cost
				best_id = t.id
				best_key = o.key
	var order := ["boulder_catapult", "rock_slinger", "club_warrior", "tar_shaman"]
	var type: String = _t(order[placed.size() % order.size()])
	var tcost := sim.tower_cost(type)
	# upgrade when it's affordable and not wildly pricier than a fresh tower; otherwise expand
	if best_id != -1 and sim.gold >= best_cost and (best_cost <= tcost * 6 or placed.size() >= 14):
		sim.upgrade_tower(best_id, best_key)
		return
	if placed.size() < 14:
		if sim.gold >= tcost:
			var spot := _best_spot(sim, type)
			if spot != Vector2.INF:
				var id := sim.place_tower(type, spot)
				if id != -1:
					placed.append(id)


func _coverage(p: Vector2, r: float) -> int:
	var c := 0
	for s in samples:
		if s.distance_to(p) <= r:
			c += 1
	return c


func _best_spot(sim: Sim, type: String, hero_spot := false) -> Vector2:
	var r: float = float(sim.hero_def.base.range) if hero_spot else float(defs.towers[type].base.range)
	var best := Vector2.INF
	var best_score := -1
	var x := -14.5
	while x <= 14.5:
		var z := -8.0
		while z <= 8.0:
			var p := Vector2(x, z)
			var err := sim.hero_placement_error(p) if hero_spot else sim.placement_error(type, p)
			if err == "" or err == "Not enough gold":
				var sc := _coverage(p, r)
				if sc > best_score:
					best_score = sc
					best = p
			z += 0.5
		x += 0.5
	return best


func _run(name: String, plan: Array, keep_spending: bool, hero_id: String) -> void:
	var sim := Sim.new()
	sim.setup(defs, map)
	if name.ends_with("MAX evolution") or name.ends_with("MID evolution"):
		sim.apply_perks(max_perks)
	if hero_id != "":
		sim.set_hero(hero_id)
		sim.place_hero(_best_spot(sim, "", true))
	var placed := []
	var step := 0
	var lives_log := []
	var last_wave := 0
	var lives_at_wave := sim.lives
	var safety := 0
	var abilities := 0
	while sim.state != "won" and sim.state != "lost" and safety < 30 * 60 * 60:
		safety += 1
		while step < plan.size():
			var it: Array = plan[step]
			var ok := false
			if it[0] == "place":
				var type := _t(it[1])
				if sim.gold >= sim.tower_cost(type):
					var spot := _best_spot(sim, type)
					var id := sim.place_tower(type, spot)
					if id != -1:
						placed.append(id)
						ok = true
					else:
						step += 1
						continue
			else:
				if it[1] >= placed.size():
					step += 1
					continue
				var t = sim.get_tower(placed[it[1]])
				var opts := sim.upgrade_options(t)
				if opts.is_empty():
					step += 1
					continue
				var key: String = it[2]
				if t.level >= 3:
					key = t.branch
				var cost := -1
				for o in opts:
					if o.key == key:
						cost = o.cost
				if cost == -1:
					step += 1
					continue
				if sim.gold >= cost:
					ok = sim.upgrade_tower(t.id, key)
			if ok:
				step += 1
			else:
				break
		if keep_spending and step >= mini(plan.size(), 12) and sim.tick % 15 == 0:
			step = plan.size()
			_spend_greedy(sim, placed)
		if sim.ability_ready():
			var boss := false
			for e in sim.enemies:
				boss = boss or e.boss
			if boss or sim.enemies.size() >= 8:
				sim.use_ability()
				abilities += 1
		if sim.can_start_wave() and sim.enemies.is_empty():
			if sim.wave > last_wave:
				lives_log.append(lives_at_wave - sim.lives)
			last_wave = sim.wave
			lives_at_wave = sim.lives
			if sim.wave + 1 == sim.total_waves and keep_spending:
				for t in sim.towers:
					t.target = "strong"   # a competent player retargets for the boss
				if sim.hero != null:
					sim.hero.target = "strong"
			sim.start_wave()
		sim.step()
		for ev in sim.events:
			if ev.e == "leak" and defs.enemies[ev.type].get("boss", false):
				print("    BOSS LEAKED wave %d with %d/%d hp left" % [sim.wave, int(ev.hp), int(ev.max_hp)])
		sim.events.clear()
	lives_log.append(lives_at_wave - sim.lives)
	var hero_txt := ""
	if sim.hero != null:
		hero_txt = " hero_lvl=%d abilities=%d" % [sim.hero.level, abilities]
	print("%-30s result=%-5s wave=%2d lives=%3d kills=%4d towers=%d gold_left=%d%s" % [
		name, sim.state, sim.wave, sim.lives, sim.stats.kills, sim.towers.size(), sim.gold, hero_txt])
	print("    lives lost per wave: ", lives_log)
