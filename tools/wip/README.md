# Work in progress (paused 2026-10-19)

Scripts and outputs from the art pass that are not part of the game yet. Godot ignores this folder (`.gdignore`).
The scripts were run from `/home/claude/work/...` paths; adjust the paths when re-running.

- `bronze_maps/apply_bronze_decor.py`: the game.gd patch that places the Bronze Age scenery kits on River Delta,
  Desert Citadel and Copper Canyon and the Bronze city (dry-run and parse check passed; **not applied yet**: apply it
  after the four kit GLBs are installed in `assets/decor/`).
- `kits/build_kits.sh THEMES...`: the fine kit builds (delta, desert, canyon, city), one at a time (a kit bake peaks
  near 3.9 GB: run nothing else heavy beside it). `kits/resume_game.sh THEMES...` resumes from a kit's sculpt.
- `kits/bronze_decor_delta.glb`: the finished River Delta kit (v0.9.28 build, palms within budget). Desert: sculpted,
  its bake was killed (out of memory); canyon and city: not built yet.
- `javelin/`: the Iron Age Javelin Thrower: quick and fine build scripts, pose strips, and `apply_javelin.py` (already
  applied to game.gd).
- `test/`: map showcase shots, attack frame captures, the GLB installer, the clip-timing patch (applied).
