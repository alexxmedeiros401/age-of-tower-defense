## Deterministic tower-defense simulation. No rendering, no Node dependencies.
## Fixed 30 Hz tick, seeded RNG, ordered arrays: the same inputs always produce
## the same game, which is what co-op and replays will be built on later.
class_name Sim
extends RefCounted

const TICK := 1.0 / 30.0
const SELL_RATE := 0.7
const LINEAGE_ORDER := ["Ranged", "Brute", "Siege", "Control"]
const TARGET_MODES := ["first", "strong", "close", "last"]
const HERO_RADIUS := 0.6

var defs: Dictionary
var map: Dictionary
var path := PackedVector2Array()       # first path (kept for visuals that only need one)
var cum_len := PackedFloat32Array()
var path_length := 0.0
var paths: Array = []                    # [{pts, cum, length}] one per portal
var blockers: Array = []                 # [Vector3(x, z, r)] no-build circles (lakes, lava, dunes...)
var rivers: Array = []                   # [{pts: PackedVector2Array, half: float}] no-build water
var hp_mult := 1.0
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

# hero
var hero = null                 # Dictionary once placed
var hero_id := ""
var hero_def: Dictionary = {}
var hero_levels: Array = []
var fury_until := 0
var fury_speed := 0.0

# persistent Evolution perks (all neutral unless apply_perks() is called)
var perks := {}
var start_lives := 0
var _bounty_frac := 0.0


func setup(p_defs: Dictionary, p_map: Dictionary, seed_value: int = 1337) -> void:
	defs = p_defs
	map = p_map
	rng.seed = seed_value
	gold = int(map.start_gold)
	lives = int(map.start_lives)
	start_lives = lives
	path_half_width = float(map.path_width) * 0.5
	total_waves = defs.waves.size()
	hp_mult = float(map.get("hp_mult", 1.0))
	var raw_paths: Array = map.paths if map.has("paths") else [map.path]
	paths.clear()
	for rp in raw_paths:
		var pts := _pts(rp)
		var cum := PackedFloat32Array([0.0])
		var total := 0.0
		for i in range(1, pts.size()):
			total += pts[i].distance_to(pts[i - 1])
			cum.append(total)
		paths.append({"pts": pts, "cum": cum, "length": total})
	path = paths[0].pts
	cum_len = paths[0].cum
	path_length = paths[0].length
	blockers.clear()
	for bl in map.get("blockers", []):
		blockers.append(Vector3(bl[0], bl[1], bl[2]))
	rivers.clear()
	for rv in map.get("rivers", []):
		rivers.append({"pts": _pts(rv.pts), "half": float(rv.width) * 0.5})


## Evolution perks from the player's save. Keys match data/evolution.json perk ids; values are totals.
func apply_perks(p: Dictionary) -> void:
	perks = p.duplicate()
	gold += int(perk("start_gold"))
	lives += int(perk("lives"))
	start_lives = lives


func perk(id: String) -> float:
	return float(perks.get(id, 0.0))


func tower_cost(type: String) -> int:
	return _discount(int(defs.towers[type].cost))


func _discount(c: int) -> int:
	return int(round(c * (1.0 - perk("cost"))))


func ability_cooldown() -> float:
	return float(hero_def.ability.cooldown) * (1.0 - perk("ability_cd"))


func aura_radius() -> float:
	return float(hero_def.get("aura", {}).get("radius", 0.0)) * (1.0 + perk("aura"))


func _pts(raw: Array) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for p in raw:
		pts.append(Vector2(p[0], p[1]))
	return pts


func _id() -> int:
	_next_id += 1
	return _next_id


func era() -> String:
	return str(map.get("era", "Stone Age"))


## Tower ids for this map's era, in shop order (Ranged, Brute, Siege, Control).
func tower_types() -> Array:
	var out := []
	for lin in LINEAGE_ORDER:
		for id in defs.towers:
			var d: Dictionary = defs.towers[id]
			if d.lineage == lin and str(d.get("era", "Stone Age")) == era():
				out.append(id)
	return out


# ---------------------------------------------------------------- path helpers
func pos_at(d: float, pi: int = 0) -> Vector2:
	var P: Dictionary = paths[pi]
	var pts: PackedVector2Array = P.pts
	var cum: PackedFloat32Array = P.cum
	d = clampf(d, 0.0, P.length)
	for i in range(1, pts.size()):
		if d <= cum[i]:
			var seg := cum[i] - cum[i - 1]
			return pts[i - 1].lerp(pts[i], (d - cum[i - 1]) / maxf(seg, 0.0001))
	return pts[pts.size() - 1]


func dir_at(d: float, pi: int = 0) -> Vector2:
	var P: Dictionary = paths[pi]
	var pts: PackedVector2Array = P.pts
	var cum: PackedFloat32Array = P.cum
	d = clampf(d, 0.0, P.length)
	for i in range(1, pts.size()):
		if d <= cum[i]:
			return (pts[i] - pts[i - 1]).normalized()
	return (pts[pts.size() - 1] - pts[pts.size() - 2]).normalized()


func _dist_to_polyline(p: Vector2, pts: PackedVector2Array) -> float:
	var best := INF
	for i in range(1, pts.size()):
		var c := Geometry2D.get_closest_point_to_segment(p, pts[i - 1], pts[i])
		best = minf(best, c.distance_to(p))
	return best


func dist_to_path(p: Vector2) -> float:
	var best := INF
	for P in paths:
		best = minf(best, _dist_to_polyline(p, P.pts))
	return best


func remaining(e: Dictionary) -> float:
	return float(paths[e.pi].length) - float(e.dist)


# ---------------------------------------------------------------- placement
func _spot_error(p: Vector2, r: float) -> String:
	var b: Array = map.bounds
	if p.x - r < b[0] or p.x + r > b[2] or p.y - r < b[1] or p.y + r > b[3]:
		return "Can't build off the map"
	if dist_to_path(p) < path_half_width + r * 0.8:
		return "Can't build on the path"
	for bl in blockers:
		if Vector2(bl.x, bl.y).distance_to(p) < bl.z + r * 1.3:
			return "Can't build there"
	for rv in rivers:
		if _dist_to_polyline(p, rv.pts) < float(rv.half) + r * 0.9:
			return "Can't build on water"
	for t in towers:
		if t.pos.distance_to(p) < float(t.radius) + r:
			return "Too close to another tower"
	if hero != null and hero.pos.distance_to(p) < HERO_RADIUS + r:
		return "Too close to your hero"
	return ""


func placement_error(type: String, p: Vector2) -> String:
	var def: Dictionary = defs.towers[type]
	var err := _spot_error(p, float(def.radius))
	if err != "":
		return err
	if gold < tower_cost(type):
		return "Not enough gold"
	return ""


func place_tower(type: String, p: Vector2) -> int:
	if state == "lost" or placement_error(type, p) != "":
		return -1
	var def: Dictionary = defs.towers[type]
	var t := {
		"id": _id(), "type": type, "pos": p, "radius": float(def.radius),
		"level": 0, "branch": "", "spent": tower_cost(type), "cd": 0.0,
		"facing": Vector2(0, 1), "kills": 0, "target": "first", "buffed": false,
	}
	t.stats = _compute_stats(t)
	gold -= tower_cost(type)
	towers.append(t)
	events.append({"e": "place", "id": t.id})
	return t.id


func get_tower(id: int):
	for t in towers:
		if t.id == id:
			return t
	return null


## A tower or the hero, by id.
func get_unit(id: int):
	var t = get_tower(id)
	if t == null and hero != null and hero.id == id:
		return hero
	return t


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
	_apply_perk_stats(s)
	return s


func _apply_perk_stats(s: Dictionary) -> void:
	if perks.is_empty():
		return
	s.damage = float(s.damage) * (1.0 + perk("damage"))
	s.range = float(s.range) * (1.0 + perk("range"))
	s.cooldown = float(s.cooldown) / (1.0 + perk("speed"))


## Returns the upgrade choices available right now: [] when maxed,
## one entry normally, two entries (A and B) at the branch point.
func upgrade_options(t: Dictionary) -> Array:
	var def: Dictionary = defs.towers[t.type]
	if t.level < 2:
		var tier: Dictionary = def.tiers[t.level]
		return [{"key": "", "name": tier.name, "cost": _discount(int(tier.cost)), "desc": tier.desc}]
	if t.level == 2:
		var out := []
		for k in ["A", "B"]:
			var br: Dictionary = def.branches[k]
			out.append({"key": k, "name": br.name, "cost": _discount(int(br.tiers[0].cost)), "desc": br.desc, "branch_pick": true})
		return out
	if t.level < 5:
		var tier2: Dictionary = def.branches[t.branch].tiers[t.level - 2]
		return [{"key": t.branch, "name": tier2.name, "cost": _discount(int(tier2.cost)), "desc": tier2.desc}]
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
	return int(t.spent * (SELL_RATE + perk("sell")))


func sell_tower(id: int) -> bool:
	for i in range(towers.size()):
		if towers[i].id == id:
			gold += sell_value(towers[i])
			towers.remove_at(i)
			events.append({"e": "sell", "id": id})
			return true
	return false


func cycle_target(id: int) -> String:
	var t = get_tower(id)
	if t == null and hero != null and hero.id == id:
		t = hero
	if t == null:
		return ""
	t.target = TARGET_MODES[(TARGET_MODES.find(t.target) + 1) % TARGET_MODES.size()]
	return t.target


func tower_display_name(t: Dictionary) -> String:
	var def: Dictionary = defs.towers[t.type]
	if t.branch == "":
		return def.name
	return def.branches[t.branch].tiers[t.level - 3].name


# ---------------------------------------------------------------- hero
func set_hero(id: String) -> bool:
	if not defs.has("heroes") or not defs.heroes.heroes.has(id):
		return false
	hero_id = id
	hero_def = defs.heroes.heroes[id]
	hero_levels = defs.heroes.levels
	return true


func hero_placement_error(p: Vector2) -> String:
	if hero_def.is_empty():
		return "No hero selected"
	if hero != null:
		return "Your hero is already on the field"
	if state == "lost":
		return "Game over"
	return _spot_error(p, HERO_RADIUS)


func place_hero(p: Vector2) -> bool:
	if hero_placement_error(p) != "":
		return false
	var lv0 := clampi(1 + int(perk("hero_level")), 1, hero_levels.size())
	hero = {"id": _id(), "type": hero_id, "pos": p, "radius": HERO_RADIUS, "level": lv0, "xp": float(hero_levels[lv0 - 1]), "cd": 0.0,
		"facing": Vector2(0, 1), "kills": 0, "target": "first", "ability_cd": 0.0, "is_hero": true, "buffed": false}
	hero.stats = _hero_stats(lv0)
	events.append({"e": "hero_place", "id": hero.id})
	return true


func _hero_stats(level: int) -> Dictionary:
	var s: Dictionary = hero_def.base.duplicate(true)
	var pl: Dictionary = hero_def.get("per_level", {})
	for k in pl:
		s[k] = float(s.get(k, 0.0)) + float(pl[k]) * float(level - 1)
	s.cooldown = maxf(float(s.cooldown), 0.15)
	return s


func _hero_gain_xp(amount: float) -> void:
	if hero == null:
		return
	hero.xp += amount * (1.0 + perk("hero_xp"))
	while hero.level < hero_levels.size() and hero.xp >= float(hero_levels[hero.level]):
		hero.level += 1
		hero.stats = _hero_stats(hero.level)
		events.append({"e": "hero_level", "level": hero.level})


## 0..1 progress toward the next level (1.0 at max).
func hero_xp_progress() -> float:
	if hero == null or hero.level >= hero_levels.size():
		return 1.0
	var lo := float(hero_levels[hero.level - 1])
	var hi := float(hero_levels[hero.level])
	return clampf((hero.xp - lo) / maxf(hi - lo, 1.0), 0.0, 1.0)


func ability_unlocked() -> bool:
	return hero != null and hero.level >= int(hero_def.ability.get("unlock", 3))


func ability_ready() -> bool:
	return ability_unlocked() and hero.ability_cd <= 0.0 and state != "lost"


func use_ability() -> bool:
	if not ability_ready():
		return false
	var ab: Dictionary = hero_def.ability
	var lv := float(hero.level - 1)
	var src := {"hero": true, "tower_id": -1}
	var hit_pos := []
	match str(ab.id):
		"stone_rain":
			var alive := []
			for e in enemies:
				if e.alive:
					alive.append(e)
			alive.sort_custom(func(a, b): return remaining(a) < remaining(b))
			var dmg := float(ab.damage) + float(ab.get("damage_per_level", 0.0)) * lv
			for i in mini(int(ab.targets), alive.size()):
				hit_pos.append(alive[i].pos)
				_damage(alive[i], dmg, "blunt", src)
		"earthquake":
			var st := float(ab.stun) + float(ab.get("stun_per_level", 0.0)) * lv
			var dmg2 := float(ab.damage) + float(ab.get("damage_per_level", 0.0)) * lv
			for e in enemies.duplicate():
				if e.alive:
					e.stun_until = maxi(e.stun_until, tick + int(st * (0.25 if e.boss else 1.0) / TICK))
					_damage(e, dmg2, "blunt", src)
		"solar_flare":
			var dmg3 := float(ab.damage) + float(ab.get("damage_per_level", 0.0)) * lv
			var fsrc := {"hero": true, "tower_id": -1, "expose": float(ab.expose), "expose_time": float(ab.expose_time)}
			for e in enemies.duplicate():
				if e.alive and e.pos.distance_to(hero.pos) <= float(ab.radius):
					hit_pos.append(e.pos)
					_damage(e, dmg3, "fire", fsrc)
		"forge_fury":
			fury_until = tick + int(float(ab.duration) / TICK)
			fury_speed = float(ab.speed)
	hero.ability_cd = ability_cooldown()
	events.append({"e": "ability", "ability": str(ab.id), "pos": hero.pos, "radius": float(ab.get("radius", 0.0)), "hits": hit_pos})
	return true


# ---------------------------------------------------------------- waves
func can_start_wave() -> bool:
	if state == "lost":
		return false
	if state == "won" and not endless:
		return false
	if wave >= total_waves and not endless:
		return false   # the boss wave was the last one; no extra waves until Endless is chosen
	return spawn_queue.is_empty()


func start_wave() -> bool:
	if not can_start_wave():
		return false
	wave += 1
	state = "running"
	var groups: Array = defs.waves[wave - 1] if wave <= total_waves else _endless_wave(wave)
	var count := 0
	for g in groups:
		var fixed_path := int(g.get("path", -1))
		for i in range(int(g.count)):
			var at := tick + int(round((float(g.delay) + float(g.interval) * i) / TICK)) + 1
			var pi: int = fixed_path if fixed_path >= 0 else i % paths.size()
			spawn_queue.append({"t": at, "type": g.type, "wave": wave, "pi": mini(pi, paths.size() - 1)})
			count += 1
	spawn_queue.sort_custom(func(a, b): return a.t < b.t)
	wave_remaining[wave] = count
	events.append({"e": "wave_start", "wave": wave})
	return true


## Endless mode: deterministic, scaling remix of the era's robot roster.
func _endless_wave(n: int) -> Array:
	var k := n - total_waves
	var r := RandomNumberGenerator.new()
	r.seed = 9000 + n
	var groups := []
	var pool: Array = map.get("endless_pool", ["walker", "scout", "brute", "carrier"] if era() == "Stone Age"
		else ["walker", "scout", "brute", "carrier", "shield_bot", "repair_drone"])
	var base_counts := {"walker": 40, "scout": 45, "brute": 14, "carrier": 8, "shield_bot": 16, "repair_drone": 8}
	for i in range(2 + mini(k / 4, 3)):
		var type: String = pool[r.randi() % pool.size()]
		var base: int = base_counts.get(type, 12)
		groups.append({"type": type, "count": base + k * 3, "interval": maxf(0.08, 0.5 - k * 0.02), "delay": i * 3.0})
	if k % 5 == 0:
		groups.append({"type": str(map.get("boss", "prime_walker")), "count": 1 + k / 10, "interval": 4.0, "delay": 2.0})
	return groups


func _hp_scale(w: int) -> float:
	return 1.0 if w <= total_waves else 1.0 + 0.15 * float(w - total_waves)


# ---------------------------------------------------------------- enemies
func _spawn_enemy(type: String, w: int, dist: float = 0.0, pi: int = 0) -> Dictionary:
	var d: Dictionary = defs.enemies[type]
	var mult := _hp_scale(w) * hp_mult
	if d.get("boss", false):
		mult *= float(map.get("boss_hp_mult", 1.0))
	var hp := float(d.hp) * mult
	var shield := float(d.get("shield", 0.0)) * mult
	var e := {
		"id": _id(), "type": type, "wave": w, "pi": pi, "dist": dist, "pos": pos_at(dist, pi), "prev_pos": pos_at(dist, pi),
		"hp": hp, "max_hp": hp, "speed": float(d.speed), "armor": float(d.armor),
		"boss": d.get("boss", false), "alive": true,
		"slow_amt": 0.0, "slow_until": 0, "stun_until": 0, "summon_cd": 0.0,
		"shield": shield, "max_shield": shield, "last_hit": -100000,
		"heal_cd": float(d.heal.every) if d.has("heal") else 0.0,
		"expose_amt": 0.0, "expose_until": 0,
	}
	enemies.append(e)
	events.append({"e": "spawn", "id": e.id})
	return e


func _damage(e: Dictionary, amount: float, dtype: String, src: Dictionary) -> void:
	if not e.alive:
		return
	var armor: float = maxf(0.0, e.armor - float(src.get("armor_pierce", 0.0)))
	if dtype == "blunt":
		armor *= 0.4
	elif dtype == "fire":
		armor *= 0.2
	var dmg := maxf(amount - armor, amount * 0.25)
	if e.boss and src.has("boss_mult"):
		dmg *= float(src.boss_mult)
	if tick < e.expose_until:
		dmg *= 1.0 + e.expose_amt
	e.last_hit = tick
	if e.shield > 0.0:
		var absorb := minf(e.shield, dmg)
		e.shield -= absorb
		dmg -= absorb
		if e.shield <= 0.0:
			events.append({"e": "shield_break", "id": e.id})
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
	if src.has("expose") and float(src.expose) > 0.0:
		var ex := float(src.expose)
		if ex >= e.expose_amt or tick >= e.expose_until:
			e.expose_amt = ex
		e.expose_until = maxi(e.expose_until, tick + int(float(src.get("expose_time", 3.0)) / TICK))
	if src.has("shred") and float(src.shred) > 0.0:
		e.armor = maxf(0.0, e.armor - float(src.shred))
	if e.hp <= 0.0:
		_kill(e, src)


func _kill(e: Dictionary, src: Dictionary) -> void:
	e.alive = false
	var d: Dictionary = defs.enemies[e.type]
	var base_bounty := int(d.bounty)
	var exact := base_bounty * (1.0 + perk("bounty")) + _bounty_frac
	var bounty := int(exact)
	_bounty_frac = exact - bounty
	gold += bounty
	stats.kills += 1
	stats.gold_earned += bounty
	if src.get("hero", false):
		if hero != null:
			hero.kills += 1
		_hero_gain_xp(base_bounty * 1.5)
	else:
		_hero_gain_xp(base_bounty * 0.6)   # heroes learn faster from their own kills
		if src.has("tower_id"):
			var t = get_tower(src.tower_id)
			if t != null:
				t.kills += 1
	events.append({"e": "kill", "id": e.id, "pos": e.pos, "bounty": bounty, "type": e.type})
	if d.has("on_death"):
		var od: Dictionary = d.on_death
		for i in range(int(od.count)):
			var child := _spawn_enemy(od.type, e.wave, maxf(0.0, e.dist - 0.35 * i), e.pi)
			wave_remaining[e.wave] += 1
			child.stun_until = tick + 6
	_finish_enemy(e)


func _finish_enemy(e: Dictionary) -> void:
	wave_remaining[e.wave] -= 1
	if wave_remaining[e.wave] <= 0:
		wave_remaining.erase(e.wave)
		var bonus: int = int(round((80 + 10 * int(e.wave)) * (1.0 + perk("wave_bonus"))))
		gold += bonus
		events.append({"e": "wave_clear", "wave": e.wave, "bonus": bonus})
		if e.wave == total_waves and lives > 0 and not endless:
			state = "won"
			events.append({"e": "victory"})
		elif wave_remaining.is_empty() and spawn_queue.is_empty() and state == "running":
			state = "ready"


# ---------------------------------------------------------------- targeting
## mode: first = closest to the base, strong = toughest (bosses first), close = nearest the tower, last = furthest back
func _find_targets(center: Vector2, rng_radius: float, limit: int = 1, mode: String = "first") -> Array:
	var found := []
	var r2 := rng_radius * rng_radius
	for e in enemies:
		if e.alive and e.pos.distance_squared_to(center) <= r2:
			found.append(e)
	match mode:
		"strong":
			found.sort_custom(func(a, b): return a.max_hp > b.max_hp or (a.max_hp == b.max_hp and remaining(a) < remaining(b)))
		"close":
			found.sort_custom(func(a, b): return a.pos.distance_squared_to(center) < b.pos.distance_squared_to(center))
		"last":
			found.sort_custom(func(a, b): return remaining(a) > remaining(b))
		_:
			found.sort_custom(func(a, b): return remaining(a) < remaining(b))
	if limit > 0 and found.size() > limit:
		found.resize(limit)
	return found


## Stats for a unit right now, after the hero's aura and Forge Fury.
func _effective_stats(t: Dictionary) -> Dictionary:
	var s: Dictionary = t.stats
	var is_hero: bool = t.get("is_hero", false)
	var dmg_mult := 1.0
	var spd := 0.0
	var rng_mult := 1.0
	t.buffed = false
	if hero != null and not is_hero:
		var au: Dictionary = hero_def.get("aura", {})
		if not au.is_empty() and t.pos.distance_to(hero.pos) <= aura_radius():
			var lin: String = str(au.get("lineage", ""))
			if lin == "" or defs.towers[t.type].lineage == lin:
				var lv := float(hero.level - 1)
				dmg_mult += float(au.get("damage", 0.0)) + float(au.get("damage_per_level", 0.0)) * lv
				spd += float(au.get("speed", 0.0)) + float(au.get("speed_per_level", 0.0)) * lv
				rng_mult += float(au.get("range", 0.0)) + float(au.get("range_per_level", 0.0)) * lv
				t.buffed = true
	var fury := tick < fury_until and not is_hero
	if not t.buffed and not fury:
		return s
	var out: Dictionary = s.duplicate()
	out.damage = float(s.damage) * dmg_mult
	out.range = float(s.range) * rng_mult
	var cdm := 1.0 - spd
	if fury:
		cdm /= 1.0 + fury_speed
		t.buffed = true
	out.cooldown = float(s.cooldown) * cdm
	return out


func _unit_attack(t: Dictionary) -> void:
	t.cd -= TICK
	if t.cd > 0.0:
		return
	var s := _effective_stats(t)
	var src := s.duplicate()
	src.tower_id = t.id
	if t.get("is_hero", false):
		src.hero = true
	match s.kind:
		"projectile":
			var tg := _find_targets(t.pos, s.range, int(s.get("shots", 1)), t.target)
			if tg.is_empty():
				return
			t.facing = (tg[0].pos - t.pos).normalized()
			for e in tg:
				var dmg := float(s.damage)
				var crit := false
				if s.has("crit_chance") and rng.randf() < float(s.crit_chance):
					dmg *= float(s.get("crit_mult", 2.0))
					crit = true
				_add_projectile({"kind": "homing", "pos": t.pos, "target": e.id, "aim": e.pos,
					"speed": float(s.proj_speed), "damage": dmg, "src": src, "crit": crit})
			t.cd = float(s.cooldown)
			events.append({"e": "fire", "id": t.id})
		"lob":
			var tg2 := _find_targets(t.pos, s.range, 1, t.target)
			if tg2.is_empty():
				return
			var e2: Dictionary = tg2[0]
			var flight := float(s.flight)
			var lead := pos_at(e2.dist + e2.speed * flight * 0.85, e2.pi)
			t.facing = (lead - t.pos).normalized()
			_add_projectile({"kind": "lob", "pos": t.pos, "start": t.pos, "aim": lead,
				"t": 0.0, "flight": flight, "damage": float(s.damage), "src": src})
			t.cd = float(s.cooldown)
			events.append({"e": "fire", "id": t.id})
		"melee":
			var tg3 := _find_targets(t.pos, s.range, int(s.max_targets), t.target)
			if tg3.is_empty():
				return
			t.facing = (tg3[0].pos - t.pos).normalized()
			for e3 in tg3:
				_damage(e3, float(s.damage), s.dtype, src)
			t.cd = float(s.cooldown)
			events.append({"e": "slam", "id": t.id, "radius": float(s.range)})
		"pulse":
			var tg4 := _find_targets(t.pos, s.range, 0)
			if tg4.is_empty():
				return
			for e4 in tg4:
				_damage(e4, float(s.damage), s.dtype, src)
			t.cd = float(s.cooldown)
			events.append({"e": "pulse", "id": t.id, "radius": float(s.range)})


# ---------------------------------------------------------------- main step
func step() -> void:
	if state == "lost":
		return
	tick += 1

	# spawns
	while not spawn_queue.is_empty() and spawn_queue[0].t <= tick:
		var s: Dictionary = spawn_queue.pop_front()
		_spawn_enemy(s.type, s.wave, 0.0, int(s.get("pi", 0)))

	# movement, shields, healing, boss summons, leaks
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
		if e.max_shield > 0.0 and e.shield < e.max_shield and tick - e.last_hit > int(float(d.get("shield_delay", 3.0)) / TICK):
			e.shield = e.max_shield
			events.append({"e": "shield_up", "id": e.id})
		if d.has("heal"):
			e.heal_cd -= TICK
			if e.heal_cd <= 0.0:
				e.heal_cd = float(d.heal.every)
				var healed := false
				var hr := float(d.heal.radius)
				for o in enemies:
					if o.alive and o.id != e.id and not o.boss and o.hp < o.max_hp and o.pos.distance_to(e.pos) <= hr:
						o.hp = minf(o.max_hp, o.hp + o.max_hp * float(d.heal.pct))
						healed = true
				if healed:
					events.append({"e": "heal", "id": e.id, "radius": hr})
		if d.has("summon"):
			e.summon_cd -= TICK
			if e.summon_cd <= 0.0:
				e.summon_cd = float(d.summon.every)
				for i in range(int(d.summon.count)):
					_spawn_enemy(d.summon.type, e.wave, e.dist + 0.6 + 0.4 * i, e.pi)
					wave_remaining[e.wave] += 1
				events.append({"e": "summon", "id": e.id})
		if e.dist >= float(paths[e.pi].length):
			e.alive = false
			var loss: int = mini(int(d.leak), lives)
			lives -= loss
			stats.leaked += 1
			events.append({"e": "leak", "id": e.id, "lives": loss, "type": e.type, "hp": e.hp, "max_hp": e.max_hp})
			_finish_enemy(e)
			if lives <= 0:
				state = "lost"
				events.append({"e": "defeat"})
				return
		e.pos = pos_at(e.dist, e.pi)

	# towers and hero
	for t in towers:
		_unit_attack(t)
	if hero != null:
		_unit_attack(hero)
		hero.ability_cd = maxf(0.0, hero.ability_cd - TICK)

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
