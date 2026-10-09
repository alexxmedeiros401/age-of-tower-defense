## Autoload: which map to play next and the player's saved progress
## (unlocks, best stars, chosen hero, settings and the persistent Evolution level + perk tree).
extends Node

const SAVE_PATH := "user://save.json"
const DEFAULT_SETTINGS := {"music": 0.7, "sfx": 1.0, "auto_start": true, "shake": true, "popups": true, "glow": true}

var current_map := ""          # set before reloading the game scene; "" = show title
var open_map_select := false   # jump straight to map select on the next load
var open_evolution := false    # jump straight to the Evolution tree on the next load
var data := {"unlocked": ["mammoth_valley"], "stars": {}, "hero": "ugo", "tab": "", "evo_xp": 0, "perks": {},
	"settings": DEFAULT_SETTINGS.duplicate(), "cleared": []}
var evo: Dictionary = {}       # data/evolution.json
var _perk_defs := {}           # perk id -> def


func _ready() -> void:
	evo = JSON.parse_string(FileAccess.get_file_as_string("res://data/evolution.json"))
	for br in evo.branches:
		for p in br.perks:
			_perk_defs[p.id] = p
	var had_evo := false
	if FileAccess.file_exists(SAVE_PATH):
		var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			had_evo = d.has("evo_xp")
			data.merge(d, true)
	var st: Dictionary = data.settings
	for k in DEFAULT_SETTINGS:
		if not st.has(k):
			st[k] = DEFAULT_SETTINGS[k]
	if not had_evo:
		_migrate_old_save()


## Saves from before v0.5 have stars but no Evolution XP: credit those wins so testers keep their heroes.
func _migrate_old_save() -> void:
	var meta := _map_meta()
	for mid in data.stars:
		if meta.has(mid) and not mid in data.cleared:
			data.evo_xp = int(data.evo_xp) + match_xp(meta[mid], 20, true, true)
			data.cleared.append(mid)
	save()


func _map_meta() -> Dictionary:
	var out := {}
	for m in JSON.parse_string(FileAccess.get_file_as_string("res://data/maps.json")).maps:
		out[m.id] = m
	return out


func save() -> void:
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(data))


# ---------------------------------------------------------------- maps
func is_unlocked(map_id: String) -> bool:
	return map_id in data.unlocked


func stars(map_id: String) -> int:
	return int(data.stars.get(map_id, 0))


func unlock_all(map_order: Array) -> void:
	for m in map_order:
		if not is_unlocked(m):
			data.unlocked.append(m)
	save()


## 3 stars: lost 10 lives or fewer, 2 stars: lost 50 or fewer, 1 star: any win. Unlocks the next map.
## Returns [stars, newly unlocked map id or "", first time this map was cleared].
func record_win(map_id: String, lives_lost: int, map_order: Array) -> Array:
	var s := 3 if lives_lost <= 10 else (2 if lives_lost <= 50 else 1)
	data.stars[map_id] = maxi(stars(map_id), s)
	var first: bool = not map_id in data.cleared
	if first:
		data.cleared.append(map_id)
	var unlocked := ""
	var i := map_order.find(map_id)
	if i != -1 and i + 1 < map_order.size() and not is_unlocked(map_order[i + 1]):
		data.unlocked.append(map_order[i + 1])
		unlocked = map_order[i + 1]
	save()
	return [s, unlocked, first]


func next_map(map_id: String, map_order: Array) -> String:
	var i := map_order.find(map_id)
	return map_order[i + 1] if i != -1 and i + 1 < map_order.size() else ""


# ---------------------------------------------------------------- heroes
func hero() -> String:
	return str(data.get("hero", "ugo"))


func set_hero(id: String) -> void:
	data.hero = id
	save()


func hero_unlocked(hero_def: Dictionary) -> bool:
	return evo_level() >= int(hero_def.get("evo_unlock", 1))


# ---------------------------------------------------------------- settings
func setting(key: String):
	return data.settings.get(key, DEFAULT_SETTINGS.get(key))


func set_setting(key: String, value) -> void:
	data.settings[key] = value
	save()


# ---------------------------------------------------------------- evolution
func xp_needed(level: int) -> int:
	var x: Dictionary = evo.xp
	return mini(int(x.level_base) + int(x.level_step) * level, int(x.level_max_cost))


func evo_level() -> int:
	var lv := 1
	var left := int(data.evo_xp)
	while left >= xp_needed(lv):
		left -= xp_needed(lv)
		lv += 1
	return lv


## [xp into the current level, xp needed for the next level]
func evo_progress() -> Array:
	var lv := 1
	var left := int(data.evo_xp)
	while left >= xp_needed(lv):
		left -= xp_needed(lv)
		lv += 1
	return [left, xp_needed(lv)]


## Evolution XP for one match. waves = waves cleared, won = beat the final wave, first = first ever win on this map.
func match_xp(map_meta: Dictionary, waves: int, won: bool, first: bool) -> int:
	var x: Dictionary = evo.xp
	var mult := float(x.difficulty.get(str(map_meta.get("difficulty", "Normal")), 1.0)) * float(x.era.get(str(map_meta.get("era", "Stone Age")), 1.0))
	var total := float(x.per_wave) * waves
	if won:
		total += float(x.win)
	total *= mult
	if first:
		total += float(x.first_clear)
	return int(round(total))


## Adds XP and returns [old level, new level].
func add_xp(amount: int) -> Array:
	var before := evo_level()
	data.evo_xp = int(data.evo_xp) + amount
	save()
	return [before, evo_level()]


func points_total() -> int:
	return evo_level() - 1


func points_spent() -> int:
	var n := 0
	for k in data.perks:
		n += int(data.perks[k])
	return n


func points_free() -> int:
	return points_total() - points_spent()


func perk_rank(id: String) -> int:
	return int(data.perks.get(id, 0))


func perk_def(id: String) -> Dictionary:
	return _perk_defs.get(id, {})


func buy_perk(id: String) -> bool:
	var d := perk_def(id)
	if d.is_empty() or points_free() < 1 or perk_rank(id) >= int(d.max):
		return false
	data.perks[id] = perk_rank(id) + 1
	save()
	return true


func reset_perks() -> void:
	data.perks = {}
	save()


## Human text for a perk at a given rank, e.g. "+9% robot gold".
func perk_text(id: String, rank: int) -> String:
	var d := perk_def(id)
	var v := float(d.per_rank) * rank
	return str(d.fmt).replace("{v}", str(int(round(v)))).replace("{p}", str(int(round(v * 100.0))))


## Totals handed to Sim.apply_perks().
func sim_perks() -> Dictionary:
	var out := {}
	for id in _perk_defs:
		out[id] = float(_perk_defs[id].per_rank) * perk_rank(id)
	return out
