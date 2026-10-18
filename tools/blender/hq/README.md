# HQ model pipeline

Sculpted, rigged, animated and texture-baked game models made entirely in code with Blender (bpy) + numpy.
Models so far: the four Stone Age towers (`assets/towers/rock_slinger.glb`, `club_warrior.glb`, `tar_shaman.glb`,
`boulder_catapult.glb`) and both Stone Age heroes (`assets/heroes/ugo.glb`, `mara.glb`).

| Unit | Character module | Base module | Clips |
|---|---|---|---|
| Rock Slinger | `caveman` | `base` | `anim` (Idle, Whirl, Throw) |
| Club Warrior | `club_warrior` | `club_base` | `anim_club` (Idle, Combat, Attack) |
| Tar Pit Shaman | `tar_shaman` | `shaman_base` | `anim_shaman` (Idle, Combat, Attack) |
| Boulder Catapult | `catapult` | `catapult_base` | `anim_catapult` (Idle, Combat, Attack) |
| Ugo (hero) | `ugo` | `ugo_base` | `anim_ugo` (Idle, Whirl, Throw, Ability, Cheer) |
| Mara (hero) | `mara` | `mara_base` | `anim_mara` (Idle, Combat, Attack, Ability, Cheer) |

## Steps

Every script takes the character module with `--character` and the base module with `--module` (table above).

```
cd tools/blender/hq
python3 sculpt_char.py --character ugo --fine --out ugo_hi.blend [--shots DIR]     # ~10 min high-poly (+ clay renders)
python3 sculpt_base.py --module ugo_base --fine --out ugo_base_hi.blend          # ~5-12 min base high-poly
python3 build_game.py -- --character ugo --char ugo_hi.blend --base ugo_base_hi.blend --out OUT --tex 2048 --ao 40
cp OUT/ugo.glb ../../../assets/heroes/            # (rock_slinger.glb goes to assets/towers/)
godot --headless --path ../../.. --import        # extracts the textures (keep compress/mode=2, size_limit=1024)
python3 render_asset.py -- --blend OUT/ugo_hq.blend --out DIR --mode hero|closeup|game|frames
python3 icon_hq.py -- OUT/ugo_hq.blend ../../../assets/ui/icon_ugo.png Whirl 6 --zoom 3.2 --tz 1.45
python3 face_hq.py -- OUT/ugo_hq.blend ../../../assets/ui/face_ugo.png --target 0,0.03,2.2 --scale 0.86
python3 reanim.py -- --character ugo --blend OUT/char_game.blend   # re-key the clips only (no re-bake), then:
python3 build_game.py -- --character ugo --out OUT --stage export
```

## How it works

- `sdf.py`: signed-distance-field sculpting. Primitives (sphere, ellipsoid, round cone, round box, torus,
  chains) combined with smooth unions/subtractions, evaluated per bounding box on a voxel grid, meshed with
  marching cubes (outward winding). `fix_winding()` repairs older inward-facing meshes. Shells of a field pass
  their offset as `eval(margin=...)` so shapes are not clipped at their bounding boxes. `paint_dist()` gives
  the signed distance to every painted label, so painted edges (war paint, nose pads...) stay crisp between
  vertices.
- `character.py`: proxy for the character being built; shared modules (`rig`, `prep`, `lowpoly`) read joints,
  hands and build settings from it. A character module provides `J`, `hp`, `hand_frame`, `eye_c`,
  `sling_points`, `skin_field`, `warm_points`, `sculpt_parts`, `PARTS`, `LOW_TARGETS`, `AO_EXCLUDE`,
  `weight_rules`, `uv_boost`, the GLB/texture names, its base and animation modules, and optionally
  `torso_bones`, `TORSO_Z`, `extra_bones`, `REGION_PARTS`, `MAT_OVERRIDES`.
- `caveman.py` / `ugo.py`: the characters (rest pose = A-pose, facing -Y). Hair and beards are fans of
  flattened, grooved locks laid over the head (`fan_lock`); brows, lips and war paint are labels painted into
  the sculpt and split into per-label masks (`prep.region_masks`). Ugo's sabertooth hood is a hide shell over
  his head with the cat's snarling face (amber stones for eyes), saber fangs as flat curved blades, the cape a
  shell draped over a slab with a pelt-shaped hem, its forelegs projected onto his shoulders and chest.
- `base.py` / `ugo_base.py`: grassy mound plus props (rock pedestal and tusk arch / carved two-tier dais with an
  amber ring and painted standing stones); grass blades and flowers are direct low-poly geometry.
- `mats.py`: procedural hand-painted materials (Cycles); bump detail ends up in the normal map. `saber()` =
  tiger-striped hide with muzzle/nose/amber/suede regions.
- `lowpoly.py`: decimation targets, UV atlas (islands picked on a smoothed copy, relaxed on the real shape,
  concave packing, more texels for face/eyes/hands).
- `bake.py`: Cycles high->low bakes. The character is baked per part (each part only sees its own sculpt;
  AO sees everything except thin accessories), composited with UV masks.
- Optional character hooks: `prop_bones()` (props on their own bone: sling, staff orb), `extra_bones()` (bones that
  deform nothing of the body: a catapult's beam, counterweight, windlass, the boulder she carries), `GLOW` (parts
  shipped as their own emissive mesh, not baked: spirit orbs), `SPLIT` (parts split off after baking as their own
  unskinned mesh, e.g. Mara's orbiting stones `SpinSlowStones`, turned in game), `YAW_PIVOT` (the point the tower turns
  about, when the character isn't at the middle of its base).
- Optional base hooks: `GLOW` (amber hero rings, quartz), `BUBBLES` (tar bubbles `Bubble*` that swell and pop in game),
  `FLAME_COLOR`, `EXTRA_SWATCHES` (extra flat colours for direct geometry such as cattails).
- `rig.py`: armature from `J`; skin weights come straight from the sculpt (`sdf_weights`: each body shape
  belongs to its nearest bone); clothing/accessory weights are transferred with per-part allowed-bone sets.
  `Poser` = FK with world-space aims + analytic two-bone IK. Ugo adds two cape bones aimed in world space, so
  the cape trails his motion. A `("frame", ...)` aim sets a bone's whole orientation (a club or staff held rigidly in
  the fist); parentless extra bones move by `offsets`; scales may be per-axis (a stretched rope). The root offset is
  keyed relative to rest (before v0.9.16 it was dropped, so crouches lifted the feet: Ugo and the Rock Slinger were
  re-keyed with `reanim.py`).
- `anim.py` (Rock Slinger): Idle, Whirl (sling on a tilted circle), Throw (the stone bone scales to 0 at release).
  `anim_ugo.py` (Ugo): Idle (fist on hip), Whirl, Throw, Ability (Stone Rain call), Cheer (rank up).
  `anim_club.py`: club on the shoulder / cocked high / overhead smash. `anim_shaman.py`: leaning on the staff and
  stroking his beard / chanting / staff slam with the orb flaring. `anim_catapult.py`: hand on the trigger / ready /
  yank, the arm whips into the stop bar, four pulls on the windlass, a boulder heaved from the basket into the bucket.
  `anim_mara.py`: staff planted / calling the earth / staff thump (orb flares) / Earthquake (both hands, staff driven
  down in a deep crouch) / Cheer.
- In game (`game.gd`): `_hq_anim_setup/_hq_anim_tick` (idle / combat loop (Whirl or Combat) / attack (Throw or
  Attack) on fire, speed follows
  game speed and fire rate, frozen when stunned or paused), `_hq_play` (hero Ability / Cheer one-shots),
  `_hq_outline` (grow + front-cull next pass), Idle playback in the card model viewers.
  Test: `--shoot-hq [--tower=<id>] [--hq-idx=N] [--hq-cam=x,y,z]` (three towers fighting + a close-up) and
  `--shoot-hero-hq [--hero=<id>]` (the hero fighting, cheer, ability), `--gif` for frames.
