## Deterministic tower-defense simulation. No rendering, no Node dependencies.
## Fixed 30 Hz tick, seeded RNG, ordered arrays: the same inputs always produce
## the same game, which is what co-op and replays will be built on later.
class_name Sim
extends RefCounted

const TICK := 1.0 / 30.0
const SELL_RATE := 0.7

var defs: Dictionary
var map: Dictionary
var path := PackedVector2Array()
var cum_len := PackedFloat32Array()
var path_length := 0.0
var path_half_width := 0.85

var tick := 0
var gold := 0
var lives := 0
var wave := 0
var total_waves := 0
var state := "ready"            # ready | running | won | lost
var endless := false
var rng := RandomNumberGenerator.new()

var enemies: Array = []
var towers: Array = []
var projectiles: Array = []
var spawn_queue: Array = []     # sorted by tick
var wave_remaining := {}        # wave -> enemies pending or alive
var events: Array = []
var stats := {"kills": 0, "leaked": 0, "gold_earned": 0}
var _next_id := 1


func setup(p_defs: Dictionary, p_map: Dictionary, seed_value: int = 1337) -> void:
	defs = p_defs
	map = p_map
	rng.seed = seed_value
	gold = int(map.start_gold)
	lives = int(map.start_lives)
	path_half_width = float(map.path_width) * 0.5
	total_waves = defs.waves.size()
	path.clear()
	for p in map.path:
		path.append(Vector2(p[0], p[1]))
	cum_len = PackedFloat32Array([0.0])
	path_length = 0.0
	for i in range(1, path.size()):
		path_length += path[i].distance_to(path[i - 1])
		cum_len.append(path_length)


func _id() -> int:
	_next_id += 1
	return _next_id


# ---------------------------------------------------------------- path helpers
func pos_at(d: float) -> Vector2:
	d = clampf(d, 0.0, path_length)
	for i in range(1, path.size()):
		if d <= cum_len[i]:
			var seg := cum_len[i] - cum_len[i - 1]
			return path[i - 1].lerp(path[i], (d - cum_len[i - 1]) / maxf(seg, 0.0001))
	return path[path.size() - 1]


func dir_at(d: float) -> Vector2:
	d = clampf(d, 0.0, path_length)
	for i in range(1, path.size()):
		if d <= cum_len[i]:
			return (path[i] - path[i - 1]).normalized()
	return (path[path.size() - 1] - path[path.size() - 2]).normalized()


func dist_to_path(p: Vector2) -> float:
	var best := INF
	for i in range(1, path.size()):
		var c := Geometry2D.get_closest_point_to_segment(p, path[i - 1], path[i])
		best = minf(best, c.distance_to(p))
	return best


# ---------------------------------------------------------------- towers
func placement_error(type: String, p: Vector2) -> String:
	var def: Dictionary = defs.towers[type]
	var r := float(def.radius)
	var b: Array = map.bounds
	if p.x - r < b[0] or p.x + r > b[2] or p.y - r < b[1] or p.y + r > b[3]:
		return "Can't build off the map"
	if dist_to_path(p) < path_half_width + r * 0.8:
		return "Can't build on the path"
	for t in towers:
		if t.pos.distance_to(p) < float(t.radius) + r:
			return "Too close to another tower"
	if gold < int(def.cost):
		return "Not enough gold"
	return ""


func place_tower(type: String, p: Vector2) -> int:
	if state == "lost" or placement_error(type, p) != "":
		return -1
	var def: Dictionary = defs.towers[type]
	var t := {
		"id": _id(), "type": type, "pos": p, "radius": float(def.radius),
		"level": 0, "branch": "", "spent": int(def.cost), "cd": 0.0,
		"facing": Vector2(0, 1), "kills": 0, "target": "first",
	}
	t.stats = _compute_stats(t)
	gold -= int(def.cost)
	towers.append(t)
	events.append({"e": "place", "id": t.id})
	return t.id


func get_tower(id: int):
	for t in towers:
		if t.id == id:
			return t
	return null


func tower_at(p: Vector2):
	for t in towers:
		if t.pos.distance_to(p) <= float(t.radius) + 0.15:
			return t
	return null


func _apply_mods(s: Dictionary, mods: Dictionary) -> void:
	for k in mods:
		var v = mods[k]
		if k.ends_with("_mult") and k != "crit_mult" and k != "boss_mult":
			var base_k: String = k.trim_suffix("_mult")
			s[base_k] = float(s.get(base_k, 0.0)) * float(v)
		elif v is String or v is bool:
			s[k] = v
		elif k == "crit_mult" or k == "boss_mult":
			s[k] = float(v)
		else:
			s[k] = float(s.get(k, 0.0)) + float(v)


func _compute_stats(t: Dictionary) -> Dictionary:
	var def: Dictionary = defs.towers[t.type]
	var s: Dictionary = def.base.duplicate(true)
	for i in range(mini(t.level, 2)):
		_apply_mods(s, def.tiers[i].mods)
	if t.branch != "":
		var bt: Array = def.branches[t.branch].tiers
		for i in range(t.level - 2):
			_apply_mods(s, bt[i].mods)
	return s


## Returns the upgrade choices available right now: [] when maxed,
## one entry normally, two entries (A and B) at the branch point.
func upgrade_options(t: Dictionary) -> Array:
	var def: Dictionary = defs.towers[t.type]
	if t.level < 2:
		var tier: Dictionary = def.tiers[t.level]
		return [{"key": "", "name": tier.name, "cost": int(tier.cost), "desc": tier.desc}]
	if t.level == 2:
		var out := []
		for k in ["A", "B"]:
			var br: Dictionary = def.branches[k]
			out.append({"key": k, "name": br.name, "cost": int(br.tiers[0].cost), "desc": br.desc, "branch_pick": true})
		return out
	if t.level < 5:
		var tier2: Dictionary = def.branches[t.branch].tiers[t.level - 2]
		return [{"key": t.branch, "name": tier2.name, "cost": int(tier2.cost), "desc": tier2.desc}]
	return []


func upgrade_tower(id: int, key: String = "") -> bool:
	var t = get_tower(id)
	if t == null or state == "lost":
		return false
	for opt in upgrade_options(t):
		if opt.key == key:
			if gold < opt.cost:
				return false
			gold -= opt.cost
			t.spent += opt.cost
			if t.level == 2:
				t.branch = key
			t.level += 1
			t.stats = _compute_stats(t)
			events.append({"e": "upgrade", "id": id})
			return true
	return false


func sell_value(t: Dictionary) -> int:
	return int(t.spent * SELL_RATE)


func sell_tower(id: int) -> bool:
	for i in range(towers.size()):
		if towers[i].id == id:
			gold += sell_value(towers[i])
			towers.remove_at(i)
			events.append({"e": "sell", "id": id})
			return true
	return false


func tower_display_name(t: Dictionary) -> String:
	var def: Dictionary = defs.towers[t.type]
	if t.branch == "":
		return def.name
	return def.branches[t.branch].tiers[t.level - 3].name


# ---------------------------------------------------------------- waves
func can_start_wave() -> bool:
	if state == "lost":
		return false
	if state == "won" and not endless:
		return false
	return spawn_queue.is_empty()


func start_wave() -> bool:
	if not can_start_wave():
		return false
	wave += 1
	state = "running"
	var groups: Array = defs.waves[wave - 1] if wave <= total_waves else _endless_wave(wave)
	var count := 0
	for g in groups:
		for i in range(int(g.count)):
			var at := tick + int(round((float(g.delay) + float(g.interval) * i) / TICK)) + 1
			spawn_queue.append({"t": at, "type": g.type, "wave": wave})
			count += 1
	spawn_queue.sort_custom(func(a, b): return a.t < b.t)
	wave_remaining[wave] = count
	events.append({"e": "wave_start", "wave": wave})
	return true


## Endless mode: deterministic, scaling remix of the robot roster.
func _endless_wave(n: int) -> Array:
	var k := n - total_waves
	var r := RandomNumberGenerator.new()
	r.seed = 9000 + n
	var groups := []
	var pool := ["walker", "scout", "brute", "carrier"]
	for i in range(2 + mini(k / 4, 3)):
		var type: String = pool[r.randi() % pool.size()]
		var base: int = {"walker": 40, "scout": 45, "brute": 14, "carrier": 8}[type]
		groups.append({"type": type, "count": base + k * 3, "interval": maxf(0.08, 0.5 - k * 0.02), "delay": i * 3.0})
	if k % 5 == 0:
		groups.append({"type": "prime_walker", "count": 1 + k / 10, "interval": 4.0, "delay": 2.0})
	return groups


func _hp_scale(w: int) -> float:
	return 1.0 if w <= total_waves else 1.0 + 0.15 * float(w - total_waves)


# ---------------------------------------------------------------- enemies
func _spawn_enemy(type: String, w: int, dist: float = 0.0) -> Dictionary:
	var d: Dictionary = defs.enemies[type]
	var hp := float(d.hp) * _hp_scale(w)
	var e := {
		"id": _id(), "type": type, "wave": w, "dist": dist, "pos": pos_at(dist), "prev_pos": pos_at(dist),
		"hp": hp, "max_hp": hp, "speed": float(d.speed), "armor": float(d.armor),
		"boss": d.get("boss", false), "alive": true,
		"slow_amt": 0.0, "slow_until": 0, "stun_until": 0, "summon_cd": 0.0,
	}
	enemies.append(e)
	events.append({"e": "spawn", "id": e.id})
	return e


func _damage(e: Dictionary, amount: float, dtype: String, src: Dictionary) -> void:
	if not e.alive:
		return
	var armor: float = e.armor
	if dtype == "blunt":
		armor *= 0.4
	elif dtype == "fire":
		armor *= 0.2
	var dmg := maxf(amount - armor, amount * 0.25)
	if e.boss and src.has("boss_mult"):
		dmg *= float(src.boss_mult)
	e.hp -= dmg
	events.append({"e": "hit", "id": e.id})
	if src.has("stun") and float(src.stun) > 0.0:
		var st := float(src.stun) * (0.25 if e.boss else 1.0)
		e.stun_until = maxi(e.stun_until, tick + int(st / TICK))
	if src.has("knockback") and not e.boss:
		e.dist = maxf(0.0, e.dist - float(src.knockback))
	if src.has("slow") and float(src.slow) > 0.0:
		var amt := minf(float(src.slow), 0.85) * (0.5 if e.boss else 1.0)
		if amt >= e.slow_amt or tick >= e.slow_until:
			e.slow_amt = amt
		e.slow_until = maxi(e.slow_until, tick + int(float(src.get("slow_time", 1.0)) / TICK))
	if e.hp <= 0.0:
		_kill(e, src)


func _kill(e: Dictionary, src: Dictionary) -> void:
	e.alive = false
	var d: Dictionary = defs.enemies[e.type]
	var bounty := int(d.bounty)
	gold += bounty
	stats.kills += 1
	stats.gold_earned += bounty
	if src.has("tower_id"):
		var t = get_tower(src.tower_id)
		if t != null:
			t.kills += 1
	events.append({"e": "kill", "id": e.id, "pos": e.pos, "bounty": bounty, "type": e.type})
	if d.has("on_death"):
		var od: Dictionary = d.on_death
		for i in range(int(od.count)):
			var child := _spawn_enemy(od.type, e.wave, maxf(0.0, e.dist - 0.35 * i))
			wave_remaining[e.wave] += 1
			child.stun_until = tick + 6
	_finish_enemy(e)


func _finish_enemy(e: Dictionary) -> void:
	wave_remaining[e.wave] -= 1
	if wave_remaining[e.wave] <= 0:
		wave_remaining.erase(e.wave)
		var bonus: int = 80 + 10 * int(e.wave)
		gold += bonus
		events.append({"e": "wave_clear", "wave": e.wave, "bonus": bonus})
		if e.wave == total_waves and lives > 0 and not endless:
			state = "won"
			events.append({"e": "victory"})
		elif wave_remaining.is_empty() and spawn_queue.is_empty() and state == "running":
			state = "ready"


# ---------------------------------------------------------------- targeting
func _find_targets(center: Vector2, rng_radius: float, limit: int = 1) -> Array:
	var found := []
	var r2 := rng_radius * rng_radius
	for e in enemies:
		if e.alive and e.pos.distance_squared_to(center) <= r2:
			found.append(e)
	found.sort_custom(func(a, b): return a.dist > b.dist)   # "first": furthest along the path
	if limit > 0 and found.size() > limit:
		found.resize(limit)
	return found


# ---------------------------------------------------------------- main step
func step() -> void:
	if state == "lost":
		return
	tick += 1

	# spawns
	while not spawn_queue.is_empty() and spawn_queue[0].t <= tick:
		var s: Dictionary = spawn_queue.pop_front()
		_spawn_enemy(s.type, s.wave)

	# movement, boss summons, leaks
	for e in enemies:
		if not e.alive:
			continue
		e.prev_pos = e.pos
		if tick >= e.stun_until:
			var sp: float = e.speed
			if tick < e.slow_until:
				sp *= 1.0 - e.slow_amt
			e.dist += sp * TICK
		var d: Dictionary = defs.enemies[e.type]
		if d.has("summon"):
			e.summon_cd -= TICK
			if e.summon_cd <= 0.0:
				e.summon_cd = float(d.summon.every)
				for i in range(int(d.summon.count)):
					_spawn_enemy(d.summon.type, e.wave, e.dist + 0.6 + 0.4 * i)
					wave_remaining[e.wave] += 1
				events.append({"e": "summon", "id": e.id})
		if e.dist >= path_length:
			e.alive = false
			var loss: int = mini(int(d.leak), lives)
			lives -= loss
			stats.leaked += 1
			events.append({"e": "leak", "id": e.id, "lives": loss})
			_finish_enemy(e)
			if lives <= 0:
				state = "lost"
				events.append({"e": "defeat"})
				return
		e.pos = pos_at(e.dist)

	# towers
	for t in towers:
		var s: Dictionary = t.stats
		t.cd -= TICK
		if t.cd > 0.0:
			continue
		var src := s.duplicate()
		src.tower_id = t.id
		match s.kind:
			"projectile":
				var tg := _find_targets(t.pos, s.range)
				if tg.is_empty():
					continue
				var e: Dictionary = tg[0]
				var dmg := float(s.damage)
				var crit := false
				if s.has("crit_chance") and rng.randf() < float(s.crit_chance):
					dmg *= float(s.get("crit_mult", 2.0))
					crit = true
				t.facing = (e.pos - t.pos).normalized()
				_add_projectile({"kind": "homing", "pos": t.pos, "target": e.id, "aim": e.pos,
					"speed": float(s.proj_speed), "damage": dmg, "src": src, "crit": crit})
				t.cd = float(s.cooldown)
				events.append({"e": "fire", "id": t.id})
			"lob":
				var tg2 := _find_targets(t.pos, s.range)
				if tg2.is_empty():
					continue
				var e2: Dictionary = tg2[0]
				var flight := float(s.flight)
				var lead := pos_at(e2.dist + e2.speed * flight * 0.85)
				t.facing = (lead - t.pos).normalized()
				_add_projectile({"kind": "lob", "pos": t.pos, "start": t.pos, "aim": lead,
					"t": 0.0, "flight": flight, "damage": float(s.damage), "src": src})
				t.cd = float(s.cooldown)
				events.append({"e": "fire", "id": t.id})
			"melee":
				var tg3 := _find_targets(t.pos, s.range, int(s.max_targets))
				if tg3.is_empty():
					continue
				t.facing = (tg3[0].pos - t.pos).normalized()
				for e3 in tg3:
					_damage(e3, float(s.damage), s.dtype, src)
				t.cd = float(s.cooldown)
				events.append({"e": "slam", "id": t.id, "radius": float(s.range)})
			"pulse":
				var tg4 := _find_targets(t.pos, s.range, 0)
				if tg4.is_empty():
					continue
				for e4 in tg4:
					_damage(e4, float(s.damage), s.dtype, src)
				t.cd = float(s.cooldown)
				events.append({"e": "pulse", "id": t.id, "radius": float(s.range)})

	# projectiles
	var keep := []
	for p in projectiles:
		if p.kind == "homing":
			var tgt = _enemy_by_id(p.target)
			if tgt != null and tgt.alive:
				p.aim = tgt.pos
			var to: Vector2 = p.aim - p.pos
			var stepd: float = p.speed * TICK
			if to.length() <= stepd + 0.2:
				p.pos = p.aim
				_impact(p, tgt if (tgt != null and tgt.alive) else null)
				continue
			p.pos += to.normalized() * stepd
		else:
			p.t += TICK
			var a: float = clampf(p.t / p.flight, 0.0, 1.0)
			p.pos = p.start.lerp(p.aim, a)
			if a >= 1.0:
				_impact(p, null)
				continue
		keep.append(p)
	projectiles = keep

	# drop dead enemies
	var alive := []
	for e in enemies:
		if e.alive:
			alive.append(e)
	enemies = alive


func _add_projectile(p: Dictionary) -> void:
	p.id = _id()
	projectiles.append(p)
	events.append({"e": "proj", "id": p.id})


func _enemy_by_id(id: int):
	for e in enemies:
		if e.id == id:
			return e
	return null


func _impact(p: Dictionary, direct) -> void:
	var src: Dictionary = p.src
	var splash := float(src.get("splash", 0.0))
	if direct != null:
		_damage(direct, p.damage, src.dtype, src)
	if splash > 0.0:
		for e in _find_targets(p.pos, splash, 0):
			if direct == null or e.id != direct.id:
				_damage(e, p.damage * (1.0 if direct == null else 0.6), src.dtype, src)
	events.append({"e": "impact", "pid": p.id, "pos": p.pos, "splash": splash, "crit": p.get("crit", false)})
