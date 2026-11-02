# Godot headless import check of a hero GLB: each character surface, its material, emission on/off, energy and
# whether the emission texture is the albedo texture (cfg emissive). Run from any folder holding a project.godot:
#   godot --headless --path DIR --script godot_mats.gd -- HERO.glb
extends SceneTree
func _init() -> void:
	var path: String = OS.get_cmdline_user_args()[0]
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var err := doc.append_from_file(path, st)
	if err != OK:
		print("ERR ", err); quit(); return
	var root := doc.generate_scene(st)
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if str(m.name).begins_with("Glow") or str(m.name) in ["Base", "GrassBlades"]:
			continue
		for si in m.mesh.get_surface_count():
			var mat := m.mesh.surface_get_material(si) as BaseMaterial3D
			print("%s surface %d: %s emission_enabled=%s energy=%.2f emission_tex=%s albedo_tex=%s same_tex=%s tris=%d" % [m.name, si, mat.resource_name, mat.emission_enabled, mat.emission_energy_multiplier, mat.emission_texture != null, mat.albedo_texture != null, mat.emission_texture == mat.albedo_texture, m.mesh.surface_get_array_index_len(si) / 3])
	quit()
