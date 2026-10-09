## Headless balance test: bots play all 20 waves with different strategies.
## Run: godot --headless --script res://tests/balance.gd
extends SceneTree

var defs: Dictionary
var map: Dictionary
var samples := PackedVector2Array()


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var map_id: String = args[0] if args.size() > 0 else "mammoth_valley"
	map = Defs.load_map(map_id)
	defs = Defs.load_all(map)
	print("=== ", map.name, " (hp x", map.get("hp_mult", 1.0), ", start gold ", map.start_gold, ")")
	var s := Sim.new()
	s.setup(defs, map)
	for pi in s.paths.size():
		var d := 0.0
		while d < s.paths[pi].length:
			samples.append(s.pos_at(d, pi))
			d += 0.25

	var strategies := {
		"lazy (2 slingers, no upgrades)": [["place", "rock_slinger"], ["place", "rock_slinger"]],
		"slinger spam (no upgrades)": _repeat([["place", "rock_slinger"]], 40),
		"balanced": _balanced(),
		"siege heavy": _siege(),
	}
	for name in strategies:
		_run(name, strategies[name], name == "balanced" or name == "siege heavy")
	quit()


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
	var type: String = order[placed.size() % order.size()]
	var tcost := int(defs.towers[type].cost)
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


func _best_spot(sim: Sim, type: String) -> Vector2:
	var def: Dictionary = defs.towers[type]
	var r := float(def.base.range)
	var best := Vector2.INF
	var best_score := -1
	var x := -14.5
	while x <= 14.5:
		var z := -8.0
		while z <= 8.0:
			var p := Vector2(x, z)
			var err := sim.placement_error(type, p)
			if err == "" or err == "Not enough gold":
				var sc := _coverage(p, r)
				if sc > best_score:
					best_score = sc
					best = p
			z += 0.5
		x += 0.5
	return best


func _run(name: String, plan: Array, keep_spending := false) -> void:
	var sim := Sim.new()
	sim.setup(defs, map)
	var placed := []
	var step := 0
	var lives_log := []
	var last_wave := 0
	var lives_at_wave := sim.lives
	var safety := 0
	while sim.state != "won" and sim.state != "lost" and safety < 30 * 60 * 60:
		safety += 1
		# try next intent
		while step < plan.size():
			var it: Array = plan[step]
			var ok := false
			if it[0] == "place":
				if sim.gold >= int(defs.towers[it[1]].cost):
					var spot := _best_spot(sim, it[1])
					var id := sim.place_tower(it[1], spot)
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
		if sim.can_start_wave() and sim.enemies.is_empty():
			if sim.wave > last_wave:
				lives_log.append(lives_at_wave - sim.lives)
			last_wave = sim.wave
			lives_at_wave = sim.lives
			if sim.wave >= sim.total_waves:
				break
			if sim.wave + 1 == sim.total_waves and keep_spending:
				for t in sim.towers:
					t.target = "strong"   # a competent player retargets for the boss
			sim.start_wave()
		sim.step()
		for ev in sim.events:
			if ev.e == "leak" and ev.type == "prime_walker":
				print("    BOSS LEAKED wave %d with %d/%d hp left" % [sim.wave, int(ev.hp), int(ev.max_hp)])
		sim.events.clear()
	lives_log.append(lives_at_wave - sim.lives)
	print("%-32s result=%-5s wave=%2d lives=%3d kills=%4d towers=%d spent_plan=%d/%d gold_left=%d" % [
		name, sim.state, sim.wave, sim.lives, sim.stats.kills, sim.towers.size(), step, plan.size(), sim.gold])
	print("    lives lost per wave: ", lives_log)
