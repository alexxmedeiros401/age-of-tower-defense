extends SceneTree
func _init():
	var sim := Sim.new()
	sim.setup(Defs.load_all(), Defs.load_map("mammoth_valley"))
	sim.gold += 9000
	var ids := []
	for p in [Vector2(-6.0, 0.0), Vector2(0.5, 1.0), Vector2(7.3, 1.0), Vector2(-11.5, -1.5)]:
		ids.append(sim.place_tower("rock_slinger", p))
	for p in [Vector2(-6.0, 6.7), Vector2(0.5, -7.6)]:
		ids.append(sim.place_tower("club_warrior", p))
	ids.append(sim.place_tower("boulder_catapult", Vector2(0.5, 6.8)))
	ids.append(sim.place_tower("tar_shaman", Vector2(7.3, 7.0)))
	for k in 2:
		for id in ids:
			sim.upgrade_tower(id, "")
	sim.upgrade_tower(ids[0], "A"); sim.upgrade_tower(ids[1], "B"); sim.upgrade_tower(ids[1], "B"); sim.upgrade_tower(ids[6], "A")
	for w in 10:
		sim.start_wave()
		var t0 := sim.tick
		while not (sim.can_start_wave() and sim.enemies.is_empty()):
			sim.step()
			if w == 9 and (sim.tick - t0) % 90 == 0:
				var ds := []
				for e in sim.enemies:
					ds.append("%s:%.1f" % [e.type.substr(0,1), e.dist])
				print("t=%ds n=%d " % [(sim.tick - t0) / 30, sim.enemies.size()], ds.slice(0, 12))
		print("wave ", w + 1, " took ", (sim.tick - t0) / 30.0, "s")
	quit()
