# HQ model pipeline (Rock Slinger prototype)

Sculpted, rigged, animated and texture-baked game models made entirely in code with Blender (bpy) + numpy.
First model: the Rock Slinger (`assets/towers/rock_slinger.glb`).

## Steps

```
cd tools/blender/hq
python3 sculpt_char.py --fine --out char_hi.blend      # ~10 min: caveman high-poly (~3.5M tris)
python3 sculpt_base.py --fine --out base_hi.blend      # ~12 min: base high-poly
python3 build_game.py -- --char char_hi.blend --base base_hi.blend --out OUT --tex 2048 --ao 40   # ~20 min
cp OUT/rock_slinger.glb ../../../assets/towers/
godot --headless --path ../../.. --import              # extracts the textures (keep compress/mode=2, size_limit=1024)
python3 render_asset.py -- --blend OUT/rock_slinger_hq.blend --out DIR --mode hero|closeup|game|frames
python3 icon_hq.py -- OUT/rock_slinger_hq.blend ../../../assets/ui/icon_rock_slinger.png Whirl 6
```

## How it works

- `sdf.py`: signed-distance-field sculpting. Primitives (sphere, ellipsoid, round cone, round box, torus,
  chains) combined with smooth unions/subtractions, evaluated per bounding box on a voxel grid, meshed with
  marching cubes (outward winding). `fix_winding()` repairs older inward-facing meshes.
- `caveman.py`: the character (rest pose = A-pose, facing -Y). Joints in `J` are shared with the rig. Hair and
  beard are fans of flattened, grooved locks laid over the head (`fan_lock`); brows are sculpted into the skin
  and painted via the `region` label; eyes get painted irises/highlights (`prep.paint_eyes`).
- `base.py`: grassy mound, chiselled layered rock pedestal (`Stone` = sphere cut by random planes), tusk arch,
  woven basket, torch, pebbles; grass blades and flowers are direct low-poly geometry.
- `mats.py`: procedural hand-painted materials (Cycles); bump detail ends up in the normal map.
- `lowpoly.py`: decimation targets, UV atlas (islands picked on a smoothed copy, relaxed on the real shape,
  concave packing, more texels for face/eyes/hands).
- `bake.py`: Cycles high->low bakes. The character is baked per part (each part only sees its own sculpt;
  AO sees everything except thin accessories), composited with UV masks.
- `rig.py`: armature from `J`; skin weights come straight from the sculpt (`sdf_weights`: each body shape
  belongs to its nearest bone); clothing/accessory weights are transferred with per-part allowed-bone sets.
  `Poser` = FK with world-space aims + analytic two-bone IK.
- `anim.py`: Idle (90f loop), Whirl (32f loop, sling on a tilted circle), Throw (24f; the stone bone scales to
  0 at release and back after the reload).
- In game (`game.gd`): `_hq_anim_setup/_hq_anim_tick` (idle / whirl in combat / throw on fire, speed follows
  game speed and fire rate, frozen when stunned or paused) and `_hq_outline` (grow + front-cull next pass).
