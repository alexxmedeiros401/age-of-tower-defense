# Tripo heroes: the generic pipeline (herotripo)

Rebuilds a hero from Alexx's Tripo model (an A-pose static mesh of ~2M triangles with its props fused to the body and
three 4096 maps) onto the OLD hero's rig and clips, which stay exactly as they were. Commander Vega was done first with
Vega-only scripts (`../vegatripo_*`); this is the same pipeline made generic, driven by one small config per hero,
`../herotripo_cfg/<id>.json`. Ugo and Mara were done with it (configs there: read them as examples).

```
herotripo_prep/   (numpy steps, local, ~1-2 GB RAM)        ../herotripo_bake.py   (Blender, GitHub runner)
  old.py      old scene -> old.npz / old.json                ../herotripo_rig.py    (Blender, local, light)
  load.py     Tripo GLB -> mesh arrays, face graph, facing   ../herotripo_review.py (Blender, local renders)
  look.py     numpy previews with a coordinate grid
  cut.py      props cut out of the fused mesh -> labels.npz
  patches.py  holes the cuts left, filled -> patches.pkl
  fit.py      old rig posed onto the Tripo body -> fit.json
  push_bake.sh / fetch.sh   runner jobs
  decode.mjs / package.json the meshopt decoder (runs on the runner)
```

## Per hero: the exact steps

Paths: the work folder is `/home/claude/work/herotripo/<id>/prep` (`HEROTRIPO_WORK` or `--work` change it). The Tripo
model is `/home/claude/work/heroglb/plain/<id>.glb` (plain floats, decoded), its compressed original
`/home/claude/work/heroglb/src/<id>.glb` (what goes to the runner). Run everything from `tools/blender/hq/herotripo_prep`
(the Blender scripts from `tools/blender/hq`). Only ONE local Blender process that loads a Tripo high-poly at a time
(the bake's `--test`); everything else here is light.

0. **Config.** Start `../herotripo_cfg/<id>.json` with just `{"old": ...}` (a local `<id>_hq.blend` if there is one AND it
   matches the shipped GLB, else leave `old` out: the default is the shipped `assets/heroes/<id>.glb`). Check a local
   blend against the shipped GLB first: same objects, same actions and frame ranges, same bone positions over the clips
   (`/home/claude/work/herotripo/scratch/cmp_anim.py` did this for Ugo and Mara: max difference < 3e-6).
1. `python3 old.py -- --hero <id>`: prints the mesh, the prop bones (any bone not in the shared biped set and not
   cape/tail/hair/...: list extra soft bones in `"body_bones"`, or give `"prop_bones"` outright), how many old faces
   ride each prop bone, and old props weighted rigidly to a hand (e.g. Mara's staff on `hand.R`: left out of the fit).
2. `python3 load.py -- --hero <id>`: prints the facing it found (`yaw`: the arm span is the wide axis at hand height;
   the toes stick out in front of the ankles) and the first scale. Ugo and Mara both came out yaw 270 (they face +X in
   Blender). If a look shows him from behind, set `"yaw"` in the config.
3. `python3 look.py -- --hero <id> --px 700 --views front,left,back,right` -> `<work>/look_all.png`; zoom with
   `--crop " x0,x1,y0,y1,z0,z1"` (note the leading space: a value starting with '-' is fine then). Read the coordinates
   off the grid (game/armature units, he faces -Y, his right hand is at -X). These are the frame of every box, seed
   and landmark in the config.
4. Props in the config (below), then `python3 cut.py -- --hero <id>` and check with
   `python3 look.py -- --hero <id> --labels --crop ...` (body grey-tinted, prop 1 blue, 2 green, 3 amber ..., dropped
   magenta). Iterate on the boxes until every prop is clean.
5. `python3 patches.py -- --hero <id>` (seconds).
6. `python3 fit.py -- --hero <id>` (~30 s), then `python3 look.py -- --hero <id> --fit` (the old body posed by the fit,
   in dark red: red where the old surface is outside the Tripo one; `--fitonly` shows the old body alone). The arms
   must reach the Tripo hands. rms ~3 cm is normal (the Tripo bodies are bulkier).
7. Commit the config and scripts, then `bash push_bake.sh <tag> <run> <id> [<id> ...]` (one runner job per hero; it
   makes the branch `art-jobs/<tag>-<run>` from the current commit with the inputs in `herotripo_in/<id>/`; use your
   own tag and a new run name for each push). ~10-20 min once a runner picks it up.
   `gh run list -R alexxmedeiros401/age-of-tower-defense --branch art-jobs/<tag>-<run>` shows the state;
   `bash fetch.sh <tag>_<id>_<run> /home/claude/work/herotripo/<id>/bake_<run>` gets the result (low.blend, the three
   maps, look/*.png, bake.log). Before pushing, `python3 ../herotripo_bake.py -- --hero <id> --in DIR --out DIR2 --test`
   with DIR holding `tripo.glb` (a link to the plain GLB), labels.npz, patches.pkl, fit.json checks the code path in
   ~1 min (the head only).
8. `python3 herotripo_rig.py -- --hero <id> --low <bake>/low.blend --out /home/claude/work/herotripo/<id>/out`
   -> `<id>.glb`, `<id>_hq.blend`, `rig_report.json` (triangles, file size, influences, weight sums, prop placements).
9. `python3 herotripo_review.py -- --hero <id> --new <out>/<id>_hq.blend --out <out>` -> turn.png, face.png,
   clips.png, old_vs_new.png, closeups.png (~10 min on 2 CPUs; `--only clips,close` to redo some).
   Look hard at them (quality bar below), fix in the config, and redo from the step that the fix touches.

## Config keys (defaults in `common.py` DEFAULTS)

| key | default | what |
|---|---|---|
| `old` | `assets/heroes/<id>.glb` | the old scene (a `.blend` or the shipped `.glb`) |
| `mesh`, `material` | auto | the old character mesh (the skinned mesh on CavemanRig with most faces) and its material |
| `tripo` | `heroglb/plain/<id>.glb` | the Tripo model |
| `yaw` | `"auto"` | degrees about +Z that turn the Tripo model to face -Y |
| `scale` | `"auto"` | Tripo -> game scale; auto: fitted (started from the body heights) |
| `tris` | 24500 | the character's triangle budget (body + props) |
| `head_share` | 0.25 | the body triangles' share above the neck |
| `face_boost` | 2.2 | texel density of the face (rest of the head 1.5, hands 1.15, props 1.2, feet 0.65) |
| `tex` | 2048 | map size |
| `body_patch` | `"rim"` | colour of the body's hole patches: `rim` (interpolated from the rim) or `dark` (the rim's darker half, Vega's coat) |
| `head_rigid_above` | 30% up the head bone (fitted pose) | z above which the head bone takes all the weight |
| `hand_prop_dist` | 0.12 | old faces 100% on a hand bone and this far from it are an old hand-held prop |
| `body_bones` / `prop_bones` | auto | see step 1 |
| `fit_reg` | 0.05 | the fit's pull toward the rest pose |
| `props` | [] | list, below |
| `armour` | [] | list, below |
| `glows` | {} | old glow meshes to move: below |
| `review_frames`, `cmp_frames`, `closeup_frames` | auto | extra review frames: `{"Attack": [10]}`, `[["Attack", 10], ["Ability", 27]]`, `{"<prop>": [["Ability", 30]]}` |

**Shapes** (seeds, sinks, armour selections) are a list of boxes `[[x0,x1],[y0,y1],[z0,z1]]`, balls
`{"ball": {"c": [x,y,z], "r": r}}`, or `{"box": ..., "col": {"min": [r,g,b], "max": [r,g,b]}}` (a test on the Tripo
base colour, 0..1; for armour, the baked albedo). Union of all; `"not": true` on an entry removes it.

**A prop** (`props[]`, in order; label k = its 1-based index):
- `name`, `bone` (the bone it rides 100%; default its name; may be a body bone, e.g. Mara's staff on `hand.R`);
- the cut: `region` (a box holding the whole prop with room to spare: its skin is a sink), `seeds`, `sinks`,
  `within` (cut from another prop's faces, e.g. the stone out of Ugo's sling), `keep` (`largest` | `all`: a staff
  that goes through a fist is two pieces), `drop` (remove it, patch over), `mode: "pieces"` (no cut: every loose piece
  of the mesh a seed touches, e.g. Mara's floating stones), `concave_k`, `margin`, `tris` (its triangle budget;
  default by its share of the faces, 250-2500), `uv_boost` (1.2);
- `object`: the prop replaces that old object's mesh instead of riding a bone (Mara's stones -> `SpinSlowStones`, which
  the game turns; it keeps the new atlas and the hero material);
- `place`: how it goes into the rest pose:
  - `"fit"`: rides its bone exactly as it sat in the Tripo pose (the fitted pose's bone matrix inverted);
  - `{"mode": "points", "from": [A, B], "to": [a, b], "scale": "match" | "keep" | number, "anchor": 0 | 1,
    "spin": deg, "offset": [dx,dy,dz]}`: A, B are landmarks on the Tripo prop (load frame: read off the grid, e.g. the
    grip's middle in the fist and the orb's middle); a, b the rest-pose targets (`"bone:<name>.head"` /
    `".tail"` or coordinates in armature space). After the fit placement the prop is turned (the least turn) so A->B
    lies along a->b, scaled (`match`: |ab|/|AB|), and A put on a (`anchor` 1: B on b, A slides along the line);
  - `{"like": "<prop>"}`: the same transform as an earlier prop (a stone in a pouch), its own bone.

**Armour** (`armour[]`): `{"name", "select": shapes (load frame, Tripo pose; colours of the baked albedo), "grow": rings,
"within": shapes, "bones": {"upperarm.R": 1.0}, "fade": {"bone": "clavicle.R", "share": 0.35, "len": 0.2},
"seam_rings": 3, "scale": 0.86, "drop": 0.015}`: rigid to `bones`, with a share of `fade.bone` at the joint fading to 0
`len` down the first bone, the coat seam round it smoothed, optionally shrunk toward the first bone's head and lowered
(Vega's pauldron: exactly this).

**Glows** (`glows{}`): old glow meshes ride their bones unchanged unless listed: `{"GlowOrb": {"at": "bone:orb.head",
"radius": 0.104}}` re-centres and resizes it (or `"fit_to": "<prop>"` takes a prop piece's centre and size; `"pad"`
scales the radius; `"scale"`/`"offset"` just nudge; `"hide": true`).

## How each step works (and what went wrong on the way)

- **The Tripo GLB is interleaved.** gltf-transform writes POSITION/NORMAL/TEXCOORD_0 into one buffer view with a
  32-byte stride; Vega's reader ignored `byteStride` (its GLB was not interleaved) and read normals as positions (a
  bbox of exactly [-1, 1]). `common.read_glb` handles strides. The textures come out by role (base / rm / normal) from
  the material, not by image order (Tripo lists Color, ORM, NormalGL, but the textures point at them out of order).
- **Facing.** The Tripo heroes face +X in Blender (Vega faced -Y). `load.py` finds it from the feet; the yaw goes into
  one transform (`xf.json`: game = s * Rz(yaw) * tripo + t) that every step uses.
- **Two frames.** The config's coordinates are in the LOAD step's frame (`xf.json`), which never changes; the fit
  refines scale and offset into `fit.json`'s `xf` (Ugo: x0.963), which the bake and the rig use. (First version: the
  cut read the fitted transform once fit.json existed, so the same seeds cut a different sling. Fixed: look/cut always
  use xf.json, and the rig maps config landmarks through both.)
- **The cut** is a max-flow min-cut on the face graph inside the region (edge capacity = edge length, much cheaper
  across concave creases), between the seeds and the sinks plus the region's skin. Ugo's sling: seeds = everything
  below the fist inside a box round the hanging sling, sinks = a thin slab of the fist: the cut ran round the cords
  exactly where they enter the fist. The stone: a ball of seeds in it and the brown (pouch) faces as sinks, cut from
  the sling's faces (`within`). Mara's staff: seeds above and below the fist and on the claws, sinks = the skin-coloured
  faces of the fist (green < 0.5; the pale wood is > 0.6). The first try lost the staff's foot: the region box's side
  ran through the tilted staff near the ground, and its skin is a sink. Make the region generous.
- **Mara's staff goes THROUGH her fist**: the mesh is one surface, so the staff is two pieces joined only by the hand
  (`keep: "all"`); the fist and the staff's ends are patched.
- **Old hand-held props bias the fit.** Mara's old staff is weighted 100% to `hand.R` (not a prop bone), so it counted
  as body: the fit twisted her arm to lay the old staff along the Tripo body (rms 0.145 to start, the arm folded down).
  `old.py` now marks faces 100% on a hand bone and > 0.12 from it as an old hand prop (Tprop -2): left out of the fit and
  of the weight transfer. After that her arm reaches the Tripo fist.
- **Glow pivots.** Mara's `orb` bone scales (up to 2x in the Attack) about its head; the old GlowOrb (an opaque
  emissive sphere) sits on that head. The Tripo orb is nearer her fist than the old one, so the staff is placed with
  `anchor: 1` (the orb's middle exactly on `orb.head`, the staff sliding along its axis in the fist) and scaled 1.25
  (so the shaft still reaches near the ground), and GlowOrb re-centred there at the Tripo orb's size. A glow or prop
  that scales must be centred on its bone's head.
- **Loose pieces.** Mara's three rune stones are separate pieces of the Tripo mesh: `mode: "pieces"` takes them whole;
  `object: "SpinSlowStones"` puts them into the old orbiting-stones object (game.gd turns `SpinSlow*` nodes), in its
  own space; they keep the hero atlas (SpinSlowStones used MaraMat: left alone, its old UVs would have pointed at
  garbage in the new atlas: check every old object that uses the hero material!).
- **Weights** come from the old mesh posed with the fit (nearest surface point with an agreeing normal, barycentric,
  4 Laplacian passes), the skull rigid to the head, at most 4 influences, normalised; the body is then un-posed into the
  rest pose by inverting that skinning, and the soles put back on the old soles.

## Quality bar (check every hero)
Same face, sharp eyes; no floating armour (Vega's pauldron floated by his ear in the Ability: weight armour to the
upper arm, see `armour`); no props through hands or bodies; no grip sticking out of the fist (Vega's pistol grip had
to be shortened); no tearing in crouches; props in the hands in every clip; the Tripo look kept unless it breaks a clip.
