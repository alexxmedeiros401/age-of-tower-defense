"""Moves the Spear Guard, Sun Priest, Tar Pit Shaman, Mara and Club Warrior effects onto their attack clips
(_on_clip, as Kira and Tarek): the robots' hits are held when the attack starts, and everything the attack throws
starts on the frame the clip reaches its strike, not on a timer set when the attack starts.

    python3 apply_clip_timing.py game/game.gd [--dry]
"""
import re
import sys

path = sys.argv[1]
dry = "--dry" in sys.argv
src = open(path).read()


def func_span(s, name):
    """The text of `func name(` up to (not including) the two blank lines after it."""
    i = s.index("\nfunc %s(" % name) + 1
    j = s.index("\n\n\n", i)
    return i, j


def replace_func(s, name, new):
    i, j = func_span(s, name)
    return s[:i] + new.strip("\n") + s[j:]


def replace_once(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:60], n)
    return s.replace(old, new)


# ---------------------------------------------------------------- the helper, after _clip_delay
HELPER = '''

## Runs `fn` on the frame the attack clip that just started on unit `uid` reaches clip frame `frame` (_on_clip: a timer
## set now runs a frame ahead of a clip restarted at the end of its last attack, and drifts if the game speed changes
## mid-clip). A model without clips runs it after `fallback` real seconds. Returns how long that is at 1x, which no game
## speed makes longer in real seconds: the hold for the robots it will hit (_hold_hit).
func _at_attack_frame(uid: int, frame: float, fallback: float, fn: Callable) -> float:
	if not _hq_clips(uid):
		_fx_after(fallback, fn)
		return fallback
	var tn: Node3D = tower_nodes[uid]
	var clip := str(tn.get_meta("clip_attack", "Attack"))
	var rate := maxf(float(tn.get_meta("throw_rate", 1.0)), 0.01)
	var at := frame / CLIP_FPS
	_fx_after(0.0, func() -> void: _on_clip(uid, clip, at, at / rate, fn))
	return at / rate'''

i, j = func_span(src, "_clip_delay")
src = src[:j] + HELPER + src[j:]

# ---------------------------------------------------------------- Tar Pit Shaman
src = replace_once(src, "## Tar Pit Shaman: he thrusts his spirit stone and it spits tar; a glob arcs onto every robot the pulse hit (capped).\n",
                   "## Tar Pit Shaman: he thrusts his spirit stone and it spits tar; a glob arcs onto every robot the pulse hit (capped).\n"
                   "## The robots' hits are held now; the tar leaves the stone as his clip reaches the thrust.\n")
src = replace_func(src, "_tar_volley", '''
func _tar_volley(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	var lead := _at_attack_frame(uid, ATTACK_FRAME.tar_shaman, 0.0, func() -> void: _tar_spit(uid, targets))
	var i := 0
	for tid in targets:
		var to := _robot_point(int(tid), 0.55)
		if to == Vector3.INF:
			continue
		var dist := _v3(u.pos, 0.0).distance_to(Vector3(to.x, 0.0, to.z))
		_hold_hit(int(tid), lead + 0.04 * i + 0.26 + dist * 0.045)
		i += 1


func _tar_spit(uid: int, targets: Array) -> void:
	var u = sim.get_unit(uid)
	if u == null:                                     # (sold mid-thrust)
		for tid in targets:
			_land_hit(int(tid))
		return
	var hot := str(u.get("branch", "")) == "B"
	var cap: int = [8, 5, 3][clampi(Progress.gfx_level(), 0, 2)]
	var face: Vector2 = u.facing
	if tower_nodes.has(uid) and (tower_nodes[uid] as Node3D).has_meta("face_to"):
		face = (tower_nodes[uid] as Node3D).get_meta("face_to")      # (he turned to face it as he wound up)
	var from := _orb_point(u, face)
	var i := 0
	for tid in targets:
		if i >= cap or not _fx_room(2):               # (past the cap: hit as the tar leaves, no glob)
			_land_hit(int(tid))
			continue
		var to := _robot_point(int(tid), 0.55)
		if to == Vector3.INF:
			continue
		var g := Node3D.new()
		add_child(g)
		g.position = from
		g.visible = false
		var gs := randf_range(0.75, 1.0) if i > 0 else 1.05
		g.scale = Vector3.ONE * gs
		var tm := _atk_mat("tar_hot" if hot else "tar")
		var core := _mi(_sph_c(0.1, 12), tm, g)
		core.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		g.set_meta("core", core)
		# a string of shrinking beads trailing behind it (local +Z points back along the flight): sticky tar
		for k in 3:
			var dm := _mi(_sph_c(0.1, 8), tm, g, Vector3(0, 0.0, 0.11 + 0.085 * k + 0.01 * k * k), Vector3.ZERO,
				Vector3.ONE * (0.52 - 0.14 * k))
			dm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if hot:
			_fire_halo(g, 0.6)
		var dist := _v3(u.pos, 0.0).distance_to(Vector3(to.x, 0.0, to.z))
		var dur := 0.26 + dist * 0.045
		effects.append({"node": g, "t": -0.04 * i, "life": dur, "kind": "glob", "src": uid, "tid": int(tid),
			"from": from, "to": to, "dur": dur, "arc": (0.4 + dist * 0.12) * randf_range(0.8, 1.2), "hot": hot})
		i += 1
	if i > 0:
		_orb_spit(uid, from, hot)
''')

# ---------------------------------------------------------------- Mara
src = replace_once(src, "## then three stone and quartz spikes burst up round every robot hit, leaning in over it, and throw it up a little.\n",
                   "## then three stone and quartz spikes burst up round every robot hit, leaning in over it, and throw it up a little.\n"
                   "## The robots' hits are held now; the earth answers as her clip reaches the cast.\n")
src = replace_func(src, "_earth_spikes", '''
func _earth_spikes(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	var lead := _at_attack_frame(uid, ATTACK_FRAME.mara, 0.0, func() -> void: _earth_answers(uid, targets))
	var fissures: int = [3, 2, 1][clampi(Progress.gfx_level(), 0, 2)]
	var origin := _v3(u.pos, 0.0)
	var i := 0
	for tid in targets:
		var tp := _robot_point(int(tid), 0.0)
		if tp == Vector3.INF:
			continue
		tp.y = 0.0
		_hold_hit(int(tid), lead + (0.16 if i < fissures and tp.distance_to(origin) > 1.3 else 0.0) + 0.03)
		i += 1


func _earth_answers(uid: int, targets: Array) -> void:
	var u = sim.get_unit(uid)
	if u == null:
		for tid in targets:
			_land_hit(int(tid))
		return
	var gl := clampi(Progress.gfx_level(), 0, 2)
	var cap: int = [6, 4, 2][gl]
	var fissures: int = [3, 2, 1][gl]
	var origin := _v3(u.pos, 0.0)
	var i := 0
	for tid in targets:
		if i >= cap:                                  # (past the cap: hit as the earth answers, no spikes)
			_land_hit(int(tid))
			continue
		var tp := _robot_point(int(tid), 0.0)
		if tp == Vector3.INF:
			continue
		tp.y = 0.0
		var dv := tp - origin
		var dist := dv.length()
		var dn := dv / maxf(dist, 0.01)
		var side := Vector3(-dn.z, 0, dn.x)
		var travel := 0.0
		if i < fissures and dist > 1.3:
			# from the edge of her dais to just short of the robot
			var run := dist - 1.05
			var steps := clampi(int(run / 0.45), 1, 4)
			for st in steps:
				var f := (st + 0.5) / steps
				var at0 := origin + dn * (0.75 + run * f) + side * randf_range(-0.09, 0.09)
				_spike(at0, f * 0.16, randf_range(0.1, 0.13), randf_range(0.4, 0.52), st % 2 == 1, 0.12,
					Vector3(randf_range(-0.2, 0.2), 0, randf_range(-0.2, 0.2)))
			travel = 0.16
		_spike_cluster(tp, travel + 0.03, int(tid))
		i += 1
''')

# ---------------------------------------------------------------- Club Warrior
src = replace_once(src, "## earth races out to every robot it hit; each one is bounced up off the ground when it arrives.\n",
                   "## earth races out to every robot it hit; each one is bounced up off the ground when it arrives. The robots' hits are\n"
                   "## held now; the club lands as his clip reaches the smash.\n")
src = replace_func(src, "_club_smash", '''
func _club_smash(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	var lead := _at_attack_frame(uid, ATTACK_FRAME.club_warrior, 0.12, func() -> void: _club_lands(uid, targets))
	var hit := _v3(u.pos, 0.0) + Vector3(u.facing.x, 0.0, u.facing.y) * 0.72
	for tid in targets:
		var tp := _robot_point(int(tid), 0.0)
		if tp != Vector3.INF:
			tp.y = 0.0
			_hold_hit(int(tid), lead + 0.03 * (clampi(int(tp.distance_to(hit) / 0.32), 0, 5) + 1))


func _club_lands(uid: int, targets: Array) -> void:
	var u = sim.get_unit(uid)
	if u == null:                                     # (sold mid-swing)
		for tid in targets:
			_land_hit(int(tid))
		return
	var origin := _v3(u.pos, 0.0)
	var fwd := Vector3(u.facing.x, 0.0, u.facing.y)
	var hit := origin + fwd * 0.72
	_ground_decal(hit, "crack", 1.25, 1.2)
	_dust_fx(hit + Vector3(0, 0.15, 0), 5, 0.9)
	_pebble_fx(hit + Vector3(0, 0.3, 0), 3)
	_clods(hit, 4, 1.0)
	shake = maxf(shake, 0.12)
	var cap: int = [5, 4, 2][clampi(Progress.gfx_level(), 0, 2)]
	var i := 0
	for tid in targets:
		if i >= cap:                                  # (past the cap: hit as the club lands, no ripple)
			_land_hit(int(tid))
			continue
		var tp := _robot_point(int(tid), 0.0)
		if tp == Vector3.INF:
			continue
		tp.y = 0.0
		var dv := tp - hit
		var steps := clampi(int(dv.length() / 0.32), 0, 5)
		for st in steps:
			var f := (st + 1.0) / (steps + 1.0)
			var at := hit + dv * f
			_fx_after(0.03 * (st + 1), func() -> void:
				_clods(at, 2 if i == 0 else 1, 0.75)
				_dust_fx(at + Vector3(0, 0.12, 0), 1, 0.4))
		var htid := int(tid)
		_fx_after(0.03 * (steps + 1), func() -> void:
			_dust_fx(tp + Vector3(0, 0.2, 0), 3, 0.7)
			_pebble_fx(tp + Vector3(0, 0.3, 0), 2)
			_clods(tp, 2, 1.0)
			_land_hit(htid, 0.18))
		_ground_decal(tp, "crack", 0.75, 0.9, 0.03 * (steps + 1))
		i += 1
''')

# ---------------------------------------------------------------- Spear Guard
src = replace_func(src, "_spear_thrust", '''
func _spear_thrust(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	# (the robots' hits are held now; the lances leave the spear's point as his clip reaches full reach)
	var lead := _at_attack_frame(uid, ATTACK_FRAME.spear_guard, 0.08, func() -> void: _spear_reach(uid, targets))
	for tid in targets:
		if _robot_point(int(tid), 0.0) != Vector3.INF:
			_hold_hit(int(tid), lead + 0.14)


## Full reach: a lance from the spear's point to each robot hit (capped: the rest are hit at once, no lance).
func _spear_reach(uid: int, targets: Array) -> void:
	var cap: int = [6, 4, 2][clampi(Progress.gfx_level(), 0, 2)]
	var i := 0
	for tid in targets:
		var t := int(tid)
		if _robot_point(t, 0.0) == Vector3.INF:      # (gone already, e.g. split on death: no lance for it)
			continue
		if i >= cap:
			_land_hit(t, 0.05)
			continue
		if i == 0:
			_spear_lance(uid, t)
		else:
			_fx_after(0.01 * i, func() -> void: _spear_lance(uid, t))
		i += 1
''')

# ---------------------------------------------------------------- Sun Priest
src = replace_func(src, "_sun_beams", '''
func _sun_beams(u: Dictionary, targets: Array) -> void:
	var uid := int(u.id)
	# his strike pose holds ~9 clip frames past RELEASE, 0.3 s at 1x: at 3x/10x or on a fast Solar Lance the beams' timing
	# shrinks with it, so they are gone before he swings back and winds up again
	var ts := clampf(_clip_delay(uid, 9) / 0.3, 0.25, 1.0)
	var kind := _sun_kind(u)
	# (the robots' hits are held now; the beams leave the disc as his clip reaches RELEASE)
	var lead := _at_attack_frame(uid, ATTACK_FRAME.sun_priest, 0.08, func() -> void: _sun_release(uid, targets, kind, ts))
	var cap: int = [8, 5, 3][clampi(Progress.gfx_level(), 0, 2)]
	var i := 0
	for tid in targets:
		var t := int(tid)
		if _robot_point(t, 0.0) != Vector3.INF:
			_hold_hit(t, lead + (0.012 * mini(i, cap - 1) + BEAM_GROW) * ts + 0.02)
			i += 1


## RELEASE: the disc flares and a beam reaches each robot hit (capped: the rest are hit with the last beam).
func _sun_release(uid: int, targets: Array, kind: int, ts: float) -> void:
	var cap: int = [8, 5, 3][clampi(Progress.gfx_level(), 0, 2)]
	_sun_flare(uid, kind)
	var i := 0
	var rest := []
	for tid in targets:
		var t := int(tid)
		if _robot_point(t, 0.0) == Vector3.INF:      # (gone already, e.g. split on death: no beam for it)
			continue
		if i >= cap:                                  # (past the cap: hit as the beams strike, no beam)
			rest.append(t)
			continue
		if i == 0:
			_sun_beam(uid, t, kind, ts)
		else:
			_fx_after(0.012 * i * ts, func() -> void: _sun_beam(uid, t, kind, ts))
		i += 1
	if not rest.is_empty():
		# (with the last beam's hit: robots blowing up before the beams leave would use up the effects budget)
		_fx_after((0.012 * maxi(i - 1, 0) + BEAM_GROW) * ts, func() -> void:
			for rt in rest:
				_land_hit(int(rt)))
''')

if dry:
    print("ok (dry run)", len(src))
else:
    open(path, "w").write(src)
    print("patched", path)
