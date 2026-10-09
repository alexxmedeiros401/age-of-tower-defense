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
	}


static func map_list() -> Array:
	return _load("res://data/maps.json").maps

static func load_map(name: String) -> Dictionary:
	return _load("res://data/map_%s.json" % name)
