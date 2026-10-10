## Loads all game data from JSON so balancing never needs code changes.
class_name Defs
extends RefCounted

static func _load(path: String) -> Variant:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("Missing data file: " + path)
		return {}
	return JSON.parse_string(f.get_as_text())

## Loads towers, enemies and the wave list for a map (each map can name its own wave file).
static func load_all(map: Dictionary = {}) -> Dictionary:
	return {
		"towers": _load("res://data/towers.json"),
		"enemies": _load("res://data/enemies.json"),
		"waves": _load("res://data/" + str(map.get("waves_file", "waves.json"))).waves,
		"heroes": load_heroes(),
	}


## heroes.json with each hero's own id filled in.
static func load_heroes() -> Dictionary:
	var h: Dictionary = _load("res://data/heroes.json")
	for id in h.heroes:
		h.heroes[id]["id"] = id
	return h


static var _era_power := {}

## An age's power (the armor multiplier of its maps; Stone and Bronze are 1.0).
static func era_power(era: String) -> float:
	if _era_power.is_empty():
		for m in map_list():
			var e := str(m.era)
			if not _era_power.has(e):
				_era_power[e] = float(load_map(str(m.id)).get("armor_mult", 1.0))
	return float(_era_power.get(era, 1.0))


static func map_list() -> Array:
	return _load("res://data/maps.json").maps

static func load_map(name: String) -> Dictionary:
	return _load("res://data/map_%s.json" % name)
