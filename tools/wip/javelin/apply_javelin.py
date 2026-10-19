"""The HQ Javelin Thrower in game.gd (v0.9.29): the javelin flies from his hand when his clip throws it (the `javelin`
bone's scale, as Tarek's hammer), point first in a shallow arc at the robot, strikes sparks and sticks in it.

    python3 apply_javelin.py game/game.gd [--dry]
"""
import sys

path = sys.argv[1]
dry = "--dry" in sys.argv
src = open(path).read()


def replace_once(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:70], n)
    return s.replace(old, new)


SECTION = '''# ---------------------------------------------------------------- Javelin Thrower (v0.9.29)
# The throw (tools/blender/hq/anim_javelin.py): from the poised stance his arm whips over and the javelin leaves his hand
# on the clip frame where the one in his fist vanishes (its bone's scale, as Tarek's hammer). It flies point first in a
# shallow arc at the robot (following it as it walks), strikes sparks off it and sticks in it, quivering, a moment; the
# sim's hit waits for it (a robot it destroys blows up then). The Spear Hunter's (Path A) javelins are bigger.
const JAV_LEN := 1.2                                 # javelin.py JAV_FWD + JAV_BACK (model units)
const JAV_FWD := 0.74                                # its grip -> its point (model units)
const JAV_FLY := 1.15                                # the flying javelin's size (of the one in his hand)
var _javs := {}                                      # sim projectile id -> its flying javelin (an effect)


## Is this sim projectile a javelin from an HQ Javelin Thrower?
func _jav_hq(p: Dictionary) -> bool:
	var uid := int((p.get("src", {}) as Dictionary).get("tower_id", -1))
	var u = sim.get_unit(uid)
	if u == null or str(u.type) != "javelin_thrower":
		return false
	return _hq_clips(uid) and (tower_nodes[uid] as Node3D).has_meta("yaw")


## A javelin (one cached mesh, model units): an ash shaft, a leather binding, an iron butt cap and a long-socketed,
## leaf-shaped iron head. The point is at the origin and it lies along +Z, so a node looking along its flight carries it
## point first.
func _jav_mesh() -> ArrayMesh:
	if _atk_cache.has("jav_mesh"):
		return _atk_cache["jav_mesh"]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_smooth_group(-1)
	var w := 0.017
	_arrow_prism(st, 0.17, JAV_LEN - 0.035, w, Color(0.74, 0.58, 0.38))           # ash shaft
	_arrow_prism(st, 0.19, 0.25, w * 1.4, Color(0.36, 0.22, 0.12))                # leather binding below the head
	_arrow_prism(st, JAV_LEN - 0.04, JAV_LEN, w * 1.3, Color(0.32, 0.32, 0.34))   # iron butt cap
	st.generate_normals()
	var m := st.commit()
	var sm := StandardMaterial3D.new()
	sm.vertex_color_use_as_albedo = true
	sm.roughness = 0.75
	sm.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.surface_set_material(0, sm)
	var st2 := SurfaceTool.new()                       # the head: a flat leaf with a raised midrib on a long socket
	st2.begin(Mesh.PRIMITIVE_TRIANGLES)
	st2.set_smooth_group(-1)
	var back := Vector3(0, 0, 0.2)
	var ring := [Vector3(0.034, 0, 0.075), Vector3(0, 0.013, 0.068), Vector3(-0.034, 0, 0.075), Vector3(0, -0.013, 0.068)]
	for i in 4:
		var j := (i + 1) % 4
		for tri in [[Vector3.ZERO, ring[i], ring[j]], [ring[j], ring[i], back]]:
			for v in tri:
				st2.add_vertex(v)
	st2.generate_normals()
	st2.commit(m)
	var hm := StandardMaterial3D.new()
	hm.albedo_color = Color(0.64, 0.66, 0.7)
	hm.metallic = 0.75
	hm.roughness = 0.32
	hm.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.surface_set_material(1, hm)
	_atk_cache["jav_mesh"] = m
	return m


## The javelin in his fist (world): its grip, and its direction along the basis' Y (scaled with the model). Carried by
## his right hand, so it is right even while the javelin itself is scaled away.
func _jav_in_hand(tn: Node3D) -> Transform3D:
	if not tn.has_meta("jav_rel"):
		var sk := tn.find_child("Skeleton3D", true, false) as Skeleton3D
		var rel := Transform3D()
		var ok := sk != null and sk.find_bone("javelin") >= 0 and sk.find_bone("hand.R") >= 0
		if ok:
			rel = sk.get_bone_global_rest(sk.find_bone("hand.R")).affine_inverse() * sk.get_bone_global_rest(sk.find_bone("javelin"))
		tn.set_meta("jav_rel", rel)
		tn.set_meta("jav_sk", sk if ok else null)
	var sk2 = tn.get_meta("jav_sk")
	if sk2 == null or not is_instance_valid(sk2):
		return Transform3D(Basis(), tn.global_position + Vector3(0, 1.4, 0))
	var s: Skeleton3D = sk2
	return s.global_transform * s.get_bone_global_pose(s.find_bone("hand.R")) * (tn.get_meta("jav_rel") as Transform3D)


## How big the javelin in his fist is drawn now (its bone's scale: 0 while his clip has it thrown).
func _jav_fist(tn: Node3D) -> float:
	if not tn.has_meta("jav_sk"):
		_jav_in_hand(tn)
	var sk = tn.get_meta("jav_sk")
	if sk == null or not is_instance_valid(sk):
		return 0.0
	var s: Skeleton3D = sk
	return s.get_bone_pose_scale(s.find_bone("javelin")).x


func _jav_throw(p: Dictionary) -> void:
	var root := Node3D.new()
	add_child(root)
	var mi := _mi(_jav_mesh(), null, root)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.visible = false
	var tid := int(p.get("target", -1))
	var e = sim._enemy_by_id(tid)
	var h := _hit_height(e)
	var to := _robot_point(tid, h)
	var uid := int((p.get("src", {}) as Dictionary).get("tower_id", -1))
	var u = sim.get_unit(uid)
	var big := 1.3 if u != null and str(u.get("branch", "")) == "A" and int(u.get("level", 0)) >= 3 else 1.0
	var fx := {"node": root, "t": 0.0, "life": INF, "kind": "javelin", "pid": int(p.id), "tid": tid, "h": h, "uid": uid,
		"launched": false, "landed": false, "impact": {}, "ids": [], "t0": 0.0, "dur": 0.2, "from": Vector3.ZERO,
		"to": to if to != Vector3.INF else _v3(p.aim, h), "s": 0.7, "big": big}
	effects.append(fx)
	_javs[int(p.id)] = fx


## The javelin's flight: in his fist (hidden) until his clip throws the one in his fist (_jav_release), then point first
## at its robot (following it as it walks), as long as the sim's shot has left to fly (at least 0.1 s; the hit waits).
func _tick_javelin(fx: Dictionary, n: Node3D) -> void:
	if not bool(fx.launched):
		if not bool(fx.get("asked", false)):        # (judged once this frame's animation is applied)
			fx.asked = true
			_jav_release.call_deferred(fx)
		return
	if bool(fx.landed):
		if float(fx.t) - float(fx.t0) - float(fx.dur) > 0.5:
			_javs.erase(int(fx.pid))                    # (no hit came for it)
			fx.life = 0.0
		return
	var k := clampf((float(fx.t) - float(fx.t0)) / float(fx.dur), 0.0, 1.0)
	var live := _robot_point(int(fx.tid), float(fx.h))
	if live != Vector3.INF:
		fx.to = live
	_jav_pose(fx, n, k)
	if k >= 1.0:
		fx.landed = true
		if not (fx.impact as Dictionary).is_empty():
			_jav_strike(fx)
			fx.life = 0.0
		else:
			n.visible = false                           # (the sim's hit is a moment behind: _jav_impact strikes then)


## Where the flying javelin's point is at `k` of its flight: a shallow arc from `from` to `to`, the javelin along the
## arc (nose up as it leaves, nose down as it strikes).
func _jav_pose(fx: Dictionary, n: Node3D, k: float) -> void:
	var from: Vector3 = fx.from
	var to: Vector3 = fx.to
	var d := to - from
	var arc := 0.32 * minf(d.length() / 5.0, 1.0)
	n.position = from.lerp(to, k) + Vector3(0, arc * 4.0 * k * (1.0 - k), 0)
	var tg := d + Vector3(0, arc * 4.0 * (1.0 - 2.0 * k), 0)
	if tg.length() > 0.01:
		var tn := tg.normalized()
		n.basis = Basis.looking_at(tn, Vector3.UP if absf(tn.y) < 0.98 else Vector3.RIGHT).scaled(Vector3.ONE * float(fx.s))


## Deferred from _tick_javelin, so it runs after this frame's animation is applied: the javelin leaves his hand on the
## frame his clip hides the one in his fist and starts where that one's point is drawn. If his clip isn't the throw or
## 0.45 s have passed, it goes at once (see _tarek_release).
func _jav_release(fx: Dictionary) -> void:
	fx.asked = false
	if bool(fx.launched) or float(fx.life) <= 0.0 or not is_instance_valid(fx.node):
		return
	var n: Node3D = fx.node
	var uid := int(fx.uid)
	var go := float(fx.t) >= 0.45 / maxf(float(speed), 0.01)
	if _hq_clips(uid):
		var tn: Node3D = tower_nodes[uid]
		var ap: AnimationPlayer = tn.get_meta("anim")
		go = go or ap.current_animation != str(tn.get_meta("clip_attack")) or _jav_fist(tn) < 0.5
		if go:
			var hand := _jav_in_hand(tn)
			var ax := hand.basis.y
			fx.s = JAV_FLY * ax.length() * float(fx.big)
			fx.from = hand.origin + ax * JAV_FWD
	else:
		go = true
		fx.from = (fx.to as Vector3) + Vector3(0, 1.0, 0)
	if not go:
		return
	fx.launched = true
	fx.t0 = fx.t
	var rem := 0.0
	var sp = _proj_by_id(int(fx.pid))
	if sp != null:
		rem = ((sp.aim as Vector2) - (sp.pos as Vector2)).length() / maxf(float(sp.speed), 0.1) / maxf(float(speed), 0.01)
	fx.dur = maxf(rem, 0.1)
	n.visible = true
	_jav_pose(fx, n, 0.0)


## The sim's javelin hit: the robot takes it when the flying javelin gets there; at once if it is already there.
func _jav_impact(ev: Dictionary) -> void:
	var fx: Dictionary = _javs[int(ev.pid)]
	var eid := int(ev.get("eid", -1))
	fx.impact = ev
	fx.ids = [eid] if eid >= 0 else []
	if bool(fx.landed):
		_jav_strike(fx)
		fx.life = 0.0
		return
	var eta := float(fx.dur) - (float(fx.t) - float(fx.t0)) if bool(fx.launched) else 0.2 / maxf(float(speed), 0.01) + 0.1
	if eid >= 0:
		_hold_hit(eid, maxf(eta, 0.0) + 0.02)


## A javelin the sim threw and landed between two frames (10x, or a robot right at his feet): it strikes at once.
func _jav_unseen(ev: Dictionary) -> bool:
	var su = sim.get_unit(int(ev.get("tower", -1)))
	if su == null or str(su.type) != "javelin_thrower" or not _hq_clips(int(su.id)):
		return false
	var eid := int(ev.get("eid", -1))
	var h := _hit_height_of(_robot_type(eid))
	var live := _robot_point(eid, h) if eid >= 0 else Vector3.INF
	var s := JAV_FLY * float(defs.towers.javelin_thrower.get("model_scale", 0.64))
	_jav_strike({"pid": int(ev.pid), "from": _v3(su.pos, 1.3), "to": live if live != Vector3.INF else _v3(ev.pos, h), "impact": ev,
		"ids": [eid] if live != Vector3.INF else [], "s": s})
	return true


## The javelin strikes: sparks off the robot's plating and a clank, and it sticks in the robot (quivering, then it sinks
## away) or, when that robot is gone, in the ground; the hit lands.
func _jav_strike(fx: Dictionary) -> void:
	_javs.erase(int(fx.pid))
	var ev: Dictionary = fx.impact
	var eid := int(ev.get("eid", -1))
	var at: Vector3 = fx.to
	var dir: Vector3 = at - (fx.from as Vector3)
	dir = dir.normalized() if dir.length() > 0.01 else Vector3.FORWARD
	var s := float(fx.s)
	var gl := clampi(Progress.gfx_level(), 0, 2)
	var life: float = [1.2, 0.8, 0.0][gl]
	if eid >= 0 and enemy_nodes.has(eid) and is_instance_valid(enemy_nodes[eid]):
		var en: Node3D = enemy_nodes[eid]
		if life > 0.0 and int(en.get_meta("arrows", 0)) < 3 and not en.has_meta("emerge") and not en.has_meta("ghost") and _fx_room(1):
			var d := (dir + Vector3(randf_range(-0.08, 0.08), randf_range(-0.05, 0.05), randf_range(-0.08, 0.08))).normalized()
			var a := _mi(_jav_mesh(), null, en)
			a.global_transform = Transform3D(Basis.looking_at(d, Vector3.UP if absf(d.y) < 0.98 else Vector3.RIGHT).scaled(Vector3.ONE * s),
				at + d * 0.16 * s)
			a.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			en.set_meta("arrows", int(en.get_meta("arrows", 0)) + 1)
			effects.append({"node": a, "t": 0.0, "life": life, "kind": "stuck", "b0": a.transform.basis, "en": en})
	else:
		at.y = 0.0
		if life > 0.0 and _fx_room(1):
			var flat := Vector3(dir.x, 0.0, dir.z)
			flat = flat.normalized() if flat.length() > 0.01 else Vector3.FORWARD
			var gd := (flat * 0.6 + Vector3(0, -0.8, 0)).normalized()
			var g := _mi(_jav_mesh(), null, self)
			g.global_transform = Transform3D(Basis.looking_at(gd, Vector3.UP).scaled(Vector3.ONE * s), at + gd * 0.12 * s)
			g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			effects.append({"node": g, "t": 0.0, "life": life * 1.3, "kind": "stuck", "b0": g.transform.basis})
		_dust_fx(at + Vector3(0, 0.08, 0), 2, 0.3)
	var n: int = [5, 3, 2][gl]
	if _fx_room(n):
		for i in n:
			var sp := _mi(_fx_mesh("spark"), _atk_mat("arrow_spark"), self, at - dir * 0.1)
			sp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var v := (-dir + Vector3(randf_range(-0.9, 0.9), randf_range(0.3, 1.2), randf_range(-0.9, 0.9))).normalized() * randf_range(2.6, 4.8)
			sp.look_at_from_position(sp.position, sp.position + v, Vector3.UP if absf(v.normalized().y) < 0.95 else Vector3.RIGHT)
			effects.append({"node": sp, "t": 0.0, "life": 0.22, "kind": "spark", "v": v})
	_sfx("rock_hit", -11.0, 0.25, 0.05)
	for t in fx.get("ids", []):
		_land_hit(int(t), 0.0)


'''

src = replace_once(src, "# ---------------------------------------------------------------- Tarek the Smith (v0.9.26)\n",
                   SECTION + "# ---------------------------------------------------------------- Tarek the Smith (v0.9.26)\n")

# the effect tick
src = replace_once(src, '''			"hammer":
				_tick_hammer(fx, n)
''', '''			"hammer":
				_tick_hammer(fx, n)
			"javelin":
				_tick_javelin(fx, n)
''')

# the sim's projectile: an HQ javelin flies from his hand (an effect, like Tarek's hammer)
src = replace_once(src, '''					if _tarek_hq(p):
						_tarek_throw(p)                     # v0.9.26: his red-hot hammer flies from his hand (an effect)
					else:''', '''					if _tarek_hq(p):
						_tarek_throw(p)                     # v0.9.26: his red-hot hammer flies from his hand (an effect)
					elif _jav_hq(p):
						_jav_throw(p)                       # v0.9.29: the javelin flies from his hand when his clip throws it
					else:''')
src = replace_once(src, '''				if _hammers.has(int(ev.pid)):
					_tarek_impact(ev)                       # it strikes when the flying hammer gets there
					continue
				if _tarek_unseen(ev):
					continue''', '''				if _hammers.has(int(ev.pid)):
					_tarek_impact(ev)                       # it strikes when the flying hammer gets there
					continue
				if _javs.has(int(ev.pid)):
					_jav_impact(ev)                         # it strikes when the flying javelin gets there
					continue
				if _tarek_unseen(ev) or _jav_unseen(ev):
					continue''')
# a robot the javelin destroys waits for it
src = replace_once(src, '''		elif ev0.e == "impact" and _hammers.has(int(ev0.pid)) and not bool(_hammers[int(ev0.pid)].landed):''',
                   '''		elif ev0.e == "impact" and _javs.has(int(ev0.pid)) and not bool(_javs[int(ev0.pid)].landed):
			if int(ev0.get("eid", -1)) >= 0:              # an HQ javelin, still in the air
				_atk_pending[int(ev0.eid)] = true
		elif ev0.e == "impact" and _hammers.has(int(ev0.pid)) and not bool(_hammers[int(ev0.pid)].landed):''')

if dry:
    print("ok (dry run)", len(src))
else:
    open(path, "w").write(src)
    print("patched", path)
