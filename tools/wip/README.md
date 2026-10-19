# Work in progress

Scripts and outputs from the art pass that are not part of the game yet. Godot ignores this folder (`.gdignore`).
The scripts were run from `/home/claude/work/...` paths; adjust the paths when re-running.

- `kits/build_kits.sh THEMES...`: the fine kit builds (delta, desert, canyon, city), one at a time (a kit bake peaks
  near 3.9 GB: run nothing else heavy beside it). `kits/resume_game.sh THEMES...` resumes from a kit's sculpt.
- `javelin/`: the Iron Age Javelin Thrower: quick and fine build scripts, pose strips, and `apply_javelin.py` (already
  applied to game.gd).
- `test/`: map showcase shots, attack frame captures, the GLB installers (`install_kits.py` installs several at a
  given texture size limit), and the game.gd patches already applied (clip timing, the Bronze map kits; v0.9.28).
