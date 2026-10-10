## World dressing for eras 3-10 (Iron Age .. The Data Center): lighting/colors per theme,
## scattered props, the 3D look of no-build zones ("blockers") and the human base at the end of the road.
## Called from game.gd. `g` is the game node; use its helpers g._mat, g._mi, g._box, g._cyl, g._sph,
## g._palm, g._campfire and g.effects (animated things). Everything here is visual only.
class_name EraDecor
extends RefCounted

const OLD_THEMES := ["meadow", "snow", "volcano", "delta", "desert", "canyon"]


static func handles(theme_id: String) -> bool:
	return not theme_id in OLD_THEMES


## Same keys as game.gd THEMES: bg, far, ambient, ambient_e, sun, sun_e, rock, cave, base ("" = no recolor).
static func env(theme_id: String) -> Dictionary:
	return {"bg": Color(0.2, 0.3, 0.15), "far": Color(0.22, 0.32, 0.16), "ambient": Color(0.85, 0.9, 1.0), "ambient_e": 0.36,
		"sun": Color(1.0, 0.95, 0.86), "sun_e": 0.74, "rock": Color(0.5, 0.5, 0.5), "cave": Color(0.45, 0.42, 0.4), "base": ""}


## Scatter props around the map, away from the road, blockers and the base.
## free(p: Vector2, clearance: float) -> bool tells whether a ground spot is clear.
static func build_decor(g: Node3D, theme_id: String, free: Callable) -> void:
	pass


## One no-build zone. `n` is already positioned at the zone center; `rad` is its radius.
static func build_blocker(g: Node3D, theme_id: String, kind: String, n: Node3D, rad: float, r: RandomNumberGenerator) -> void:
	var rock: StandardMaterial3D = g._mat("era_rock", env(theme_id).rock)
	for k in 4:
		var off := Vector2(r.randf_range(-0.6, 0.6), r.randf_range(-0.6, 0.6)) * rad
		var sz := r.randf_range(0.35, 0.7) * rad
		g._mi(g._sph(sz, 6), rock, n, Vector3(off.x, sz * 0.4, off.y), Vector3(0, r.randf() * 3, 0), Vector3(1.1, 0.8, 1))


## The humans' base where the road ends (p = road end point, robots arrive from -x).
## base_id: hillfort | temple | castle | fort | factory | bunker | lab | camp
static func build_base(g: Node3D, base_id: String, p: Vector2) -> void:
	var n := Node3D.new()
	n.position = Vector3(p.x, 0, p.y)
	g.add_child(n)
	var wall: StandardMaterial3D = g._mat("era_base_wall", Color(0.6, 0.55, 0.5))
	g._mi(g._box(1.2, 2.2, 6.0), wall, n, Vector3(1.0, 1.1, 0))
