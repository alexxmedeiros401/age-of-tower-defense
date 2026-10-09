## Autoload: which map to play next and the player's saved progress (unlocks, best stars, chosen hero).
extends Node

const SAVE_PATH := "user://save.json"

var current_map := ""          # set before reloading the game scene; "" = show title
var open_map_select := false   # jump straight to map select on the next load
var data := {"unlocked": ["mammoth_valley"], "stars": {}, "hero": "ugo", "tab": ""}


func _ready() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			data.merge(d, true)


func save() -> void:
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(data))


func is_unlocked(map_id: String) -> bool:
	return map_id in data.unlocked


func stars(map_id: String) -> int:
	return int(data.stars.get(map_id, 0))


func hero() -> String:
	return str(data.get("hero", "ugo"))


func set_hero(id: String) -> void:
	data.hero = id
	save()


func unlock_all(map_order: Array) -> void:
	for m in map_order:
		if not is_unlocked(m):
			data.unlocked.append(m)
	save()


## 3 stars: 90+ lives left, 2 stars: 50+, 1 star: any win. Unlocks the next map in the list.
## Returns [stars, newly unlocked map id or ""].
func record_win(map_id: String, lives: int, map_order: Array) -> Array:
	var s := 3 if lives >= 90 else (2 if lives >= 50 else 1)
	data.stars[map_id] = maxi(stars(map_id), s)
	var unlocked := ""
	var i := map_order.find(map_id)
	if i != -1 and i + 1 < map_order.size() and not is_unlocked(map_order[i + 1]):
		data.unlocked.append(map_order[i + 1])
		unlocked = map_order[i + 1]
	save()
	return [s, unlocked]


func next_map(map_id: String, map_order: Array) -> String:
	var i := map_order.find(map_id)
	return map_order[i + 1] if i != -1 and i + 1 < map_order.size() else ""
