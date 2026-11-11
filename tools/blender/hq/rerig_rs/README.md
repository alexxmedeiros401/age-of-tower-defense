# Rock Slinger re-rig

A new skeleton, new skin weights and new Idle / Whirl / Throw clips for `assets/towers/rock_slinger.glb`
(v0.9.119-art). The mesh, textures, base, node names, material names and clip names are the old unit's, so the game
loads the file as it is: `game.gd` only looks the clips up by name (`Idle`, `Whirl`, `Throw`), and the `.import` file
and the extracted textures do not change.

Nothing here needs the PC runner: it is headless Blender (`pip install bpy==5.2.2`), numpy, scipy and pillow.
The folder has a `.gdignore`, so Godot does not import its inputs.

## Why

The old unit rode the Tripo body on the old low-poly skeleton (25 bones). Its arms had half-turn helpers but no
twist chain, the sling was one stiff bone, and its Throw dropped the stone out of the pouch on frame 3 with the hand
still at the hip, then lifted and swung the empty sling: the arm moved after the rock had gone. The attack read as
a late, short swing of a stiff sling.

## What it builds

| | before | re-rig |
|---|---|---|
| bones | 25 | 38 |
| bind pose | old skeleton's | the sculpt's own pose |
| sling | 1 bone + stone | 4 bones + stone (rope simulated, baked) |
| triangles | 19,993 | 20,529 (the strap is cut at the new sling joints) |
| Idle / Whirl / Throw | 3.75 / 1.333 / 1.0 s | 3.75 / 1.0 / 1.0 s |
| file | 4.84 MB | 4.91 MB |

Skeleton (`rig/rs_skel.py`): root, spine, chest, neck, head; per arm clavicle, upperarm, forearm, hand plus the
helpers `shoulder_half` (half the arm's swing), `upperarm_sw` (swing, no twist), `upperarm_tw` (half the twist),
`elbow_half`, `forearm_tw`; per leg thigh, shin, foot, toe plus `knee_half`; `sling`, `sling.001-003`, `stone`.
Only `root` is ever moved, only `stone` is ever scaled (1 while a stone is in the pouch, 0 once it has left).

## Build

    bash build.sh            # prep -> weights -> rig -> export -> check  (under a minute; the same bytes every time)
    bash build.sh install    # copies out/rock_slinger.glb over assets/towers/rock_slinger.glb

Inputs, in `src/` (override with `RS_IN`, `RS_SHIPPED`; `RS_WORK` moves `out/`):

* `low.blend` and `hero_albedo.png`: the Tripo bake of the body (from `pcin/rock_slinger/bake/` at commit d5e07c3 of
  `pc-jobs/pctest-t1`). The albedo is only read for the head's mask (hair and beard are dark).
* `rock_slinger_before.glb`: the unit as it shipped up to v0.9.118-art. The base, the materials and the six embedded
  JPEGs are taken from it byte for byte, and the film's BEFORE half is rendered from it. (Building from the
  re-rigged unit instead also works; a few hundred base normals then drift by 1e-4 a generation.)

Steps:

1. `rs_prep.py` cuts the sling strap at the new joints and writes `mesh.npz`.
2. `rs_make_weights.py` (`rs_labels.py`, `rs_weights.py`): every body vertex gets one main bone (limbs by the
   nearest bone seen through the inside of the mesh, cut at joint planes; the head from the baked colours; the hip
   bag and belt knot rigid on the pelvis), then a surface blur (narrow at hinges, wide round shoulders, hips and
   trunk), then the helper bones take their share, at most 4 bones per vertex.
3. `rs_build.py` swaps the old `Caveman` / `CavemanRig` in the old file for the new ones.
4. `rs_export.py` bakes the clips (`rs_clips.py`) and exports with the pipeline's exporter settings, puts the
   old file's images back and repairs one zero tangent the exporter leaves.

## Clips (`rig/rs_clips.py`)

Clips are keyed on a few controls (pelvis, chest and head turns, wrist targets, elbow poles, feet) and solved by
`rs_core.py`; the helper bones are derived, never keyed. The sling is a rope: driven round the whirl circle while it
is loaded, simulated when it is empty (`rs_anim.py`), kept out of his body and beard and inside the base's ring of
tusks.

* **Idle**, 90 frames: weight shifts, breathing, the head scans, the loaded sling sways and gets one small bounce.
* **Whirl**, 24 frames, two turns: combat stance, left arm aims, the sling turns on a circle tilted 38 degrees beside
  his head (a flat overhead circle would hit the tusks: they stand 0.95 from his axis and do not turn with him).
* **Throw**, 24 frames, cyclic: cocked at 0, the stone leaves on frame 2, follow-through across the body, the hand
  comes back to the hip bag, a new stone is in the pouch from frame 11, a turn and a third of wind-up, cocked again
  at 24. The game starts Throw the moment the sim fires and spawns its own rock then, so the release has to be at
  the very start; because 24 is 0, shot after shot chains without a pop.

## Checks and review tools

* `rig/rs_check.py`: every frame of every clip. Stretched edges, flipped faces, reach, planted foot, clearance from
  the base for any facing, arm or sling inside head or trunk, loop closure. Exits 1 on a failure.
* `rig/rs_fight.py`: plays a unit file the way `game.gd` does (0.05 s cut into the attack, attack sped up to the
  cooldown, 0.25 s fades to the combat loop and back to Idle, Godot's blend maths) and renders it in Blender. It
  works on any unit GLB, so it is also a before/after tool for the other towers. `--rock` draws the game's projectile.
* `video/render.sh`, `compose.py`, `stills.py`: the before/after film and stills (720 x 1280, for a phone):
  `bash video/render.sh && python3 video/compose.py video before_after.mp4` (needs ffmpeg and the DejaVu fonts).
* `scripts/`: `cliptest.py` (frames of a clip), `shots.py` (frames of any unit file), `paintw.py` (weights),
  `flipmap.py`, `whipclear.py`, `inside.py`, `glbinfo.py` (file summary without Blender), `validate_all.js`
  (Khronos validator: `npm install gltf-validator`), `sheet.py` (contact sheets). Run them from this folder.

## Known limits

* The previews are Blender renders driven by an emulation of the game's clip logic, not engine captures.
  v0.9.119-art is the first build with the new unit; nobody had looked at it in the engine when this was written.
* The first shot from Idle snaps to the release in about 70 ms: the game fires first and animates after, with a
  0.05 s blend. Chained shots are smooth. A real fix is on the game's side (start the combat loop when a target is
  acquired, a beat before the first shot), not in the clip.
* Raising the sling arm overhead from an A-pose bind stretches the armpit (166 edges past 2x their length). It reads
  as skin in close-ups, but it is the weakest spot of the weights.
* The beard and the hip bag are rigid; faces fold in the creases under them when the head turns or the hips drop.
  The check's "flips" (27 in Idle, up to 139 in Throw) sit there, inside the folded elbow and knee, at the bracers,
  in the armpit and along the fur's edge on the left shoulder.
* The whirl is a tilted circle beside his head, not a flat one overhead: the base's tusks leave no room for that.
