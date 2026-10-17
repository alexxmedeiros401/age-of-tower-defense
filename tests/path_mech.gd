## Headless check of path mechanics: one walker per path, stepped to the end.
## Reports travel time, rift jumps, time spent hidden in tunnels and the speed seen in lanes.
## Run: godot --headless --path . --script res://tests/path_mech.gd -- <map_id> [<map_id> ...]
extends SceneTree


func _init() -> void:
	var ids := OS.get_cmdline_user_args()
	for mid in ids:
		var map := Defs.load_map(mid)
		var defs := Defs.load_all(map)
		var s := Sim.new()
		s.setup(defs, map)
		s.wave_remaining[1] = 1000
		for pi in s.paths.size():
			var e: Dictionary = s._spawn_enemy("walker", 1, Sim.SPAWN_DIST, pi)
			e.hp = 1e9
			e.max_hp = 1e9
			var warps := 0
			var hidden_t := 0.0
			var max_jump := 0.0
			var t := 0
			var fast_seen := 0.0
			while e.alive and t < 30 * 600:
				var before: Vector2 = e.pos
				var d0: float = e.dist
				s.events.clear()
				s.step()
				t += 1
				for ev in s.events:
					if ev.e == "warp" and ev.id == e.id:
						warps += 1
						max_jump = maxf(max_jump, before.distance_to(e.pos))
				if e.hidden:
					hidden_t += Sim.TICK
				fast_seen = maxf(fast_seen, (float(e.dist) - d0) / Sim.TICK / float(e.speed))
			print("MECH|%s|path %d|len %.1f|time %.1fs|warps %d (jump %.1f)|hidden %.1fs|max lane mult %.2f|leaked %s" % [
				mid, pi, float(s.paths[pi].length), t * Sim.TICK, warps, max_jump, hidden_t, fast_seen, s.stats.leaked > 0])
			s.enemies.clear()
			s.stats.leaked = 0
	quit()
