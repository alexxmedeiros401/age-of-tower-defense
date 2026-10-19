# HQ model pipeline

Sculpted, rigged, animated and texture-baked game models made entirely in code with Blender (bpy) + numpy.
Models so far: the Bronze Archer and the Spear Guard (`assets/towers/bronze_archer.glb`, v0.9.21, and
`spear_guard.glb`, v0.9.22, the first of the Bronze Age), the four Stone Age towers (`assets/towers/rock_slinger.glb`,
`club_warrior.glb`, `tar_shaman.glb`, `boulder_catapult.glb`), both Stone Age heroes (`assets/heroes/ugo.glb`,
`mara.glb`), the five Stone Age robots (`assets/robots/walker.glb`, `scout.glb`, `brute.glb`, `carrier.glb`,
`prime_walker.glb`, v0.9.18), the three Stone Age map kits (`assets/decor/stone_decor.glb`, `stone_decor_snow.glb`,
`stone_decor_volcano.glb`) and the time portal (`assets/decor/time_portal.glb`). The Stone Age map grounds are rendered
by `../map_ground_hq.py` (below).

| Unit | Character module | Base module | Clips |
|---|---|---|---|
| Rock Slinger | `caveman` | `base` | `anim` (Idle, Whirl, Throw) |
| Club Warrior | `club_warrior` | `club_base` | `anim_club` (Idle, Combat, Attack) |
| Tar Pit Shaman | `tar_shaman` | `shaman_base` | `anim_shaman` (Idle, Combat, Attack) |
| Boulder Catapult | `catapult` | `catapult_base` | `anim_catapult` (Idle, Combat, Attack) |
| Ugo (hero) | `ugo` | `ugo_base` | `anim_ugo` (Idle, Whirl, Throw, Ability, Cheer) |
| Mara (hero) | `mara` | `mara_base` | `anim_mara` (Idle, Combat, Attack, Ability, Cheer) |
| Bronze Archer (v0.9.21) | `archer` | `archer_base` | `anim_archer` (Idle, Combat, Attack) |
| Spear Guard (v0.9.22) | `spear` | `spear_base` | `anim_spear` (Idle, Combat, Attack) |

## Steps

Every script takes the character module with `--character` and the base module with `--module` (table above).

```
cd tools/blender/hq
python3 sculpt_char.py --character ugo --fine --out ugo_hi.blend [--shots DIR]     # ~10 min high-poly (+ clay renders)
python3 sculpt_base.py --module ugo_base --fine --out ugo_base_hi.blend          # ~5-12 min base high-poly
python3 build_game.py -- --character ugo --char ugo_hi.blend --base ugo_base_hi.blend --out OUT --tex 2048 --ao 40
cp OUT/ugo.glb ../../../assets/heroes/            # (rock_slinger.glb goes to assets/towers/)
godot --headless --path ../../.. --import        # extracts the textures (keep compress/mode=2, size_limit=1024)
(cd ../../.. && python3 tools/blender/footprints.py)   # re-measure every unit's footprint (data/footprints.json)
python3 render_asset.py -- --blend OUT/ugo_hq.blend --out DIR --mode hero|closeup|game|frames
python3 icon_hq.py -- OUT/ugo_hq.blend ../../../assets/ui/icon_ugo.png Whirl 6 --zoom 3.2 --tz 1.45
python3 face_hq.py -- OUT/ugo_hq.blend ../../../assets/ui/face_ugo.png --target 0,0.03,2.2 --scale 0.86
python3 reanim.py -- --character ugo --blend OUT/char_game.blend   # re-key the clips only (no re-bake), then:
python3 build_game.py -- --character ugo --out OUT --stage export
python3 lineup.py -- OUT.png 2400 860 64 A_hq.blend:RootName:Action:Frame:Scale ...   # group shot of finished units
```

### Robots (v0.9.18)

```
cd tools/blender/hq
python3 robot_build.py -- --robot brute --out D --stage sculpt --fine --shots D/shots   # high-poly + material shots
python3 robot_build.py -- --robot brute --out D --stage game --tex 2048 --ao 24          # low-poly, UVs, bakes, rig, clips
python3 robot_build.py -- --robot brute --out D --stage export                           # D/brute.glb
python3 robot_icon.py -- D/brute_hq.blend ../../../assets/ui/icon_brute.png --frame 8    # roster portrait (mid-stride)
python3 robot_icon.py -- D/brute_hq.blend D/strip --strip                               # animation strip to check a clip
```

| Robot | Module | Clips | In game |
|---|---|---|---|
| Walker | `robot_walker` | Walk | `walk_speed` 0.86 |
| Scout Drone | `robot_scout` | Fly (rotors spin, eye scans) | hover |
| Brute Bot | `robot_brute` | Walk (heavy stomp) | `walk_speed` 0.57 |
| Carrier | `robot_carrier` | Fly (hover sled, pods bob) | hover |
| Prime Walker (boss) | `robot_prime_walker` | Walk, Summon | `walk_speed` 0.7, Summon on its summon event |

Each part is weighted 100% to one bone (machines don't bend). `robot_mats.py`: white armour with painted labels
(hazard stripes, panel lines), gunmetal frames, chrome, rubber, lens sockets; glows (eyes, cores) ship as emissive meshes.
`robot_anim.py`: a biped march with planted feet (two-bone IK) and a hover loop. In game the walk clip's playback speed
follows the robot's real ground speed (`enemies.json` `walk_speed` = the ground speed the clip matches at speed 1).
Test: `--demo --map=mammoth_valley --shoot-bots [--gif]` (a mixed column plus a close-up of each type).

### Map kits and the time portal (v0.9.18)

```
python3 decor_build.py -- --theme meadow|snow|volcano|portal --out D --fine --tex 2048 --ao 24 --shots D/shots [--each]
python3 decor_build.py -- --theme volcano --only Volcano --out D --stage sculpt --shots D/shots --each   # quick look
```

`decor_props.py` sculpts every prop (pines, bushes, boulders, stumps, logs, snow mounds, ice, dead trees, obsidian, the
mammoth skeleton, dolmen, bone hut, cave, the volcano, the portal), `decor_mats.py` paints them (moss, snow caps, ash,
glowing seams). All props of a theme are baked into one atlas and exported as one GLB with one mesh per prop, at the
origin, named as `game.gd` `DECOR_V2` expects; glowing parts (lava, the portal's coils) stay emissive surfaces. Grass
tufts and flower clumps are direct geometry coloured from a swatch strip at the right of the atlas. In game every kit
mesh gets the HQ outline pass (`_kit_outline`), except tufts and flowers. `--each` adds a close-up of every prop.
Copy the GLB to `assets/decor/`, import, and set its textures' `.import` as for units (size_limit 2048 for a map kit's
atlas, 1024 for the portal).

### Grounds (v0.9.18)

```
python3 tools/blender/map_ground_hq.py mammoth_valley --samples 32 --out assets/textures/ground_mammoth_valley.png
```

The map's ground built as a real 3D surface (road sunk in with ruts, scattered 3D tufts, flowers, pebbles, snow lumps,
ice, basalt, glowing fissures...) lit by the game's sun and rendered straight down, so it always matches the
simulation's road and lanes (`tools/map_geo.py` reads the map). About 20 minutes per map. The outer band fades to one
colour (`tools/ground_fade.py`) so it meets the far plane without a seam. Keep the texture's `.import` at
`compress/mode=2` with `mipmaps/generate=true` (about 3 MB of GPU memory instead of 17).

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
  stroking his beard / chanting / Attack (v0.9.20): draws back and thrusts the spirit stone, the tar leaves it at
  `RELEASE` (frame 8). `anim_catapult.py`: hand on the trigger / ready /
  yank, the arm whips into the stop bar, four pulls on the windlass, a boulder heaved from the basket into the bucket.
  `anim_mara.py`: staff planted / calling the earth / Attack (v0.9.20): crouches and sweeps her palm over the earth,
  then flings it up and out to her side, the spikes burst up at `RELEASE` (frame 10) / Earthquake (both hands, staff
  driven down in a deep crouch) / Cheer.
  `anim_archer.py` (v0.9.21): bow at his side / at full draw / Attack: the arrows leave the string at `RELEASE`
  (frame 1), he reaches over his shoulder into the quiver, swings a fresh pair over his head onto the bow and draws
  again (the clip ends in the Combat pose). The bow is rigid in his left fist ("frame" aim: its axis upright, its back
  to the target); the grip is placed where the bow arm is almost straight (`aim_geometry`), the drawing fingers under
  his chin. The string is two extra bones (`string_top`, `string_bot`, children of the bow hand) aimed from the posed
  tips at the drawing fingers and stretched along their length (a second solve once the tips are known); the nocked
  pair rides the `arrow` prop bone, aimed through the arrow rest, its scale (constant keys) hiding it after the release.
  `anim_spear.py` (v0.9.22): spear planted at his side, the shield resting on his arm / the phalanx stance (left foot
  forward, the shield up before him, the spear overhand above his shoulder) / Attack: he draws the spear back, then
  drives a lunging overhand thrust past the shield's edge; at full reach (`THRUST`, frame 6) the game's lance of light
  leaves the point. The spear and the shield are rigid in his fists ("frame" aims: the spear along the right fist's
  thumb axis, the shield's grip in the left fist with its face along the knuckles).
- In game (`game.gd`): `_hq_anim_setup/_hq_anim_tick` (idle / combat loop (Whirl or Combat) / attack (Throw or
  Attack) on fire, speed follows
  game speed and fire rate, frozen when stunned or paused), `_hq_play` (hero Ability / Cheer one-shots),
  `_hq_outline` (grow + front-cull next pass), Idle playback in the card model viewers. The attack effects are timed
  to the clips: `game.gd` `ATTACK_FRAME` must match each module's `RELEASE` (`SMASH` for the club, `THRUST` for the
  spear). The clips are keyed at 30 frames a second in the modules' comments, but the scenes export at Blender's
  default 24 fps, so the `.glb` clips run at 24 fps (`CLIP_FPS` in `game.gd`) and Godot re-samples them at 30 Hz on
  import: pick an `ATTACK_FRAME` inside a held pose (the spear's full reach holds over frames 6-10, so 7), where the
  samples either side agree. Attack clips still fit their cooldowns: the game plays them at length / cooldown.
  Test: `--shoot-hq [--tower=<id>] [--hq-idx=N] [--hq-cam=x,y,z]` (three towers fighting + a close-up) and
  `--shoot-hero-hq [--hero=<id>]` (the hero fighting, cheer, ability), `--gif` for frames; `--shoot-attacks
  --unit=<tower>|hero` (frames of one attack, with `--fixed-fps 30`). Render a clip as a strip with `render_asset.py
  -- --blend <unit>_hq.blend --mode frames --action Attack --range 0,24 --step 2`.

## Gotchas

- **Memory:** the sandbox has about 6 GB. A kit bake peaks near 2.6 GB, a robot bake near 1.5 GB, a ground render near
  1 GB: run at most two of them at once (a third one got the kit bake killed).
- **Grid offset:** the meshing grid is offset by a fraction of a voxel (`sdf.Field.mesh`). Flat cuts that landed exactly on
  grid planes made zero-area triangles, and decimation tore the mesh there (the Club Warrior's kilt).
- **Degenerate geometry:** `lowpoly._clean` merges doubles and dissolves degenerate faces before decimating.
- **Glows:** emissive strength above about 1.5, or a bright albedo under the emission, washes out to white or pastel in
  game. `GLOW` specs are `(colour, strength[, albedo factor])`; orbs and hero rings use strength 1.0 with albedo 0.5.
  Flames take `FLAME_COLOR` / `FLAME_STRENGTH` (default 2.5, fine for a yellow torch; the shaman's green flame uses 1.1).
- **Valid meshes:** the joined character and base are validated before export (duplicate faces left by decimation make
  the glTF exporter warn that the mesh is not valid).
- **Texture imports:** after `godot --import`, set every extracted texture's `.import` to `compress/mode=2`,
  `process/size_limit=1024` and `compress/normal_map` 1 for normal maps, 2 for the others, then import again.
- **Memory, again:** an `Inter` takes its bounds from its first shape. Put the small shape first (a disc before the
  sphere its dome is cut from), or the mesher walks the big shape's whole box: a shield's 1 m sphere meant 300 million
  voxels and the sculpt was killed, taking a bake running beside it down too.
- **Materials added for the Bronze Age** (`mats.py`): `bronze`, `gold`, `linen`, `wool`, `bow`, `arrows`, `quiver`,
  `mudbrick` (brick courses from object coordinates, glazed bands, whitewash), `terracotta`, `reed`, `coals`,
  `limestone`, `plaster`, `spear_shaft`, `shield_hide`; `skin` labels can take a strength (a shadow of stubble).
- `icon_hq.py --yaw DEG` turns the unit for its shop icon (the archer is drawn in profile).
- **Materials added for the Stone Age set** (`mats.py`): `wolf`, `club_wood`, `flint`, `horn`, `robe`, `tar`, `quartz`,
  `glow_ball`, plus extra skin labels (scars, lashes, tar) and light-hair options for `hair`.
- **In game:** the HQ outline is a shader pass pushed slightly away from the camera, so it shows round the silhouette and
  not as dark dashes in creases (eyes, brows, hair grooves).
