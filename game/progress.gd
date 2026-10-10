## Autoload: which map to play next and the player's saved progress
## (unlocks, best stars, chosen hero, settings and the persistent Legacy level + perk tree).
extends Node

const SAVE_PATH := "user://save.json"
const DEFAULT_SETTINGS := {"music": 0.7, "sfx": 1.0, "auto_start": true, "shake": true, "popups": true, "glow": true, "ui_scale": 1.15}
const UI_SCALES := [1.0, 1.15, 1.3]

var current_map := ""          # set before reloading the game scene; "" = show title
var open_map_select := false   # jump straight to map select on the next load
var open_legacy := false    # jump straight to the Legacy tree on the next load
var data := {"unlocked": ["mammoth_valley"], "stars": {}, "hero": "ugo", "tab": "", "legacy_xp": 0, "perks": {},
	"settings": DEFAULT_SETTINGS.duplicate(), "cleared": [], "timeline": 1}
var legacy: Dictionary = {}       # data/legacy.json
var workshop: Dictionary = {}     # data/workshop.json (Scrap + tower unlocks, per era)
var _towers: Dictionary = {}      # data/towers.json
var _perk_defs := {}           # perk id -> def


func _ready() -> void:
	legacy = JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy.json"))
	workshop = JSON.parse_string(FileAccess.get_file_as_string("res://data/workshop.json"))
	_towers = JSON.parse_string(FileAccess.get_file_as_string("res://data/towers.json"))
	for br in legacy.branches:
		for p in br.perks:
			_perk_defs[p.id] = p
	var had_legacy := false
	if FileAccess.file_exists(SAVE_PATH):
		var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			if d.has("evo_xp") and not d.has("legacy_xp"):   # v0.5.0 called it Evolution
				d["legacy_xp"] = d["evo_xp"]
			d.erase("evo_xp")
			had_legacy = d.has("legacy_xp")
			data.merge(d, true)
	var st: Dictionary = data.settings
	for k in DEFAULT_SETTINGS:
		if not st.has(k):
			st[k] = DEFAULT_SETTINGS[k]
	if not had_legacy:
		_migrate_old_save()
	if not data.has("towers"):
		_migrate_towers()
	if points_spent() > points_total():
		data.perks = {}      # v0.8: points no longer come from levels, so refund perks bought that way
		save()


## Saves from before v0.5 have stars but no Legacy XP: credit those wins so testers keep their heroes.
func _migrate_old_save() -> void:
	var meta := _map_meta()
	for mid in data.stars:
		if meta.has(mid) and not mid in data.cleared:
			data.legacy_xp = int(data.get("legacy_xp", 0)) + match_xp(meta[mid], 20, true, true)
			data.cleared.append(mid)
	save()


## Saves from before v0.8 had every tower: keep the towers of every era the player has already played.
func _migrate_towers() -> void:
	data.towers = []
	data.scrap = {}
	var meta := _map_meta()
	var eras := []
	for mid in data.get("cleared", []):
		if meta.has(mid):
			eras.append(str(meta[mid].era))
	for tid in _towers:
		if str(_towers[tid].get("era", "Stone Age")) in eras:
			data.towers.append(tid)
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
	return legacy_level() >= int(hero_def.get("legacy_unlock", 1))


# ---------------------------------------------------------------- settings
func setting(key: String):
	return data.settings.get(key, DEFAULT_SETTINGS.get(key))


func set_setting(key: String, value) -> void:
	data.settings[key] = value
	save()


# ---------------------------------------------------------------- legacy
func xp_needed(level: int) -> int:
	var x: Dictionary = legacy.xp
	return mini(int(x.level_base) + int(x.level_step) * level, int(x.level_max_cost))


func legacy_level() -> int:
	var lv := 1
	var left := int(data.get("legacy_xp", 0))
	while left >= xp_needed(lv):
		left -= xp_needed(lv)
		lv += 1
	return lv


## [xp into the current level, xp needed for the next level]
func legacy_progress() -> Array:
	var lv := 1
	var left := int(data.get("legacy_xp", 0))
	while left >= xp_needed(lv):
		left -= xp_needed(lv)
		lv += 1
	return [left, xp_needed(lv)]


## Legacy XP for one match. waves = waves cleared, won = beat the final wave, first = first ever win on this map.
func match_xp(map_meta: Dictionary, waves: int, won: bool, first: bool) -> int:
	var x: Dictionary = legacy.xp
	var mult := timeline_xp_mult() * float(x.difficulty.get(str(map_meta.get("difficulty", "Normal")), 1.0)) * float(x.era.get(str(map_meta.get("era", "Stone Age")), 1.0))
	var total := float(x.per_wave) * waves
	if won:
		total += float(x.win)
	total *= mult
	if first:
		total += float(x.first_clear) * timeline_xp_mult()
	return int(round(total))


## Adds XP and returns [old level, new level].
func add_xp(amount: int) -> Array:
	var before := legacy_level()
	data.legacy_xp = int(data.get("legacy_xp", 0)) + amount
	save()
	return [before, legacy_level()]


## Legacy perk points come only from reaching a New Timeline (Legacy level itself unlocks heroes).
func points_total() -> int:
	return timeline_bonus_points()


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


## Max rank grows with each New Timeline.
func perk_max(id: String) -> int:
	return int(perk_def(id).max) + int(legacy.timeline.max_rank_per) * (timeline() - 1)


func buy_perk(id: String) -> bool:
	var d := perk_def(id)
	if d.is_empty() or points_free() < 1 or perk_rank(id) >= perk_max(id):
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


# ---------------------------------------------------------------- timelines (prestige)
## Beating the final map lets the player start a New Timeline: map progress resets, Legacy is kept and grows.
func timeline() -> int:
	return int(data.get("timeline", 1))


func timeline_bonus_points() -> int:
	return int(legacy.timeline.bonus_points_per) * (timeline() - 1)


func timeline_xp_mult() -> float:
	return 1.0 + float(legacy.timeline.xp_per) * (timeline() - 1)


func timeline_hp_mult() -> float:
	return 1.0 + float(legacy.timeline.robot_hp_per) * (timeline() - 1)


## True once every map of the current timeline has been beaten.
func can_new_timeline(map_order: Array) -> bool:
	for m in map_order:
		if not m in data.cleared:
			return false
	return not map_order.is_empty()


func start_new_timeline(map_order: Array) -> void:
	data.timeline = timeline() + 1
	data.best_timeline = maxi(int(data.get("best_timeline", 1)), timeline())
	data.unlocked = [map_order[0]]
	data.stars = {}
	data.cleared = []
	data.tab = ""
	data.towers = []
	data.scrap = {}
	save()


# ---------------------------------------------------------------- workshop: Scrap and tower unlocks
## Every era has its own Scrap wallet that starts at 0, and its own towers to unlock.
## The Ranged tower of each era is free; the rest are bought with that era's Scrap.
func scrap(era: String) -> int:
	return int(data.get("scrap", {}).get(era, 0))


func add_scrap(era: String, amount: int) -> void:
	if not data.has("scrap"):
		data.scrap = {}
	data.scrap[era] = scrap(era) + amount
	save()


## Towers unlock in a fixed order per era, weakest first (data/workshop.json "order").
## The first one is free; each of the others must be bought with that era's Scrap, in order.
func unlock_rank(tid: String) -> int:
	return workshop.order.find(str(_towers[tid].lineage))


func tower_scrap_cost(tid: String) -> int:
	if unlock_rank(tid) < int(workshop.free):
		return 0
	return int(workshop.cost.get(str(_towers[tid].lineage), 200))


func tower_unlocked(tid: String) -> bool:
	return tower_scrap_cost(tid) == 0 or tid in data.get("towers", [])


## The era's tower that can be bought next ("" when all are unlocked).
func next_unlock(era: String) -> String:
	for tid in era_towers(era):
		if not tower_unlocked(tid):
			return tid
	return ""


func unlock_tower(tid: String) -> bool:
	if tower_unlocked(tid):
		return true
	var era := str(_towers[tid].get("era", "Stone Age"))
	if next_unlock(era) != tid:
		return false          # weaker towers come first
	var c := tower_scrap_cost(tid)
	if scrap(era) < c:
		return false
	data.scrap[era] = scrap(era) - c
	if not data.has("towers"):
		data.towers = []
	data.towers.append(tid)
	save()
	return true


## Scrap for one match: waves cleared, a win bonus and a first-clear bonus, scaled by difficulty.
func match_scrap(map_meta: Dictionary, waves: int, won: bool, first: bool) -> int:
	var e: Dictionary = workshop.earn
	var mult := float(workshop.difficulty.get(str(map_meta.get("difficulty", "Normal")), 1.0))
	var total := float(e.per_wave) * waves
	if won:
		total += float(e.win)
	total *= mult
	if first:
		total += float(e.first_clear)
	return int(round(total))


func era_towers(era: String) -> Array:
	var out := []
	for lin in workshop.order:
		for tid in _towers:
			if str(_towers[tid].lineage) == lin and str(_towers[tid].get("era", "Stone Age")) == era:
				out.append(tid)
	return out


## How many of the era's towers are unlocked (1..4); each one past the first adds the Workshop tech bonus.
func era_unlocked_count(era: String) -> int:
	var n := 0
	for tid in era_towers(era):
		if tower_unlocked(tid):
			n += 1
	return n


func tech_mult(era: String) -> float:
	return 1.0 + float(workshop.get("tech_bonus", 0.0)) * maxi(0, era_unlocked_count(era) - 1)
