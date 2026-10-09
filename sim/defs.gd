## Loads all game data from JSON so balancing never needs code changes.
class_name Defs
extends RefCounted

static func _load(path: String) -> Variant:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("Missing data file: " + path)
		return {}
	return JSON.parse_string(f.get_as_text())

static func load_all() -> Dictionary:
	return {
		"towers": _load("res://data/towers.json"),
		"enemies": _load("res://data/enemies.json"),
		"waves": _load("res://data/waves.json").waves,
	}

static func load_map(name: String) -> Dictionary:
	return _load("res://data/map_%s.json" % name)
