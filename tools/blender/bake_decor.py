"""Bakes a map's static scenery (exported from the game with --export-decor) into the v2 art style.

Every part: material -> vertex color on a shared finish, welded + softly bevelled edges, ambient occlusion
baked against every other prop and the ground (contact shadows), merged into one mesh per finish, plus a
cartoon outline shell. The root keeps the exporter's name "Decor_<n>" so the game can check it matches.

Usage: python3 bake_decor.py -- --in exported.glb --out assets/decor/maps/<map>.glb [--rays 14]
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import sty
from sty import reg
import upgrade_v2 as up

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default
SRC = arg("--in")
OUT = arg("--out")
RAYS = int(arg("--rays", "14"))

sty.reset(5)
bpy.ops.import_scene.gltf(filepath=SRC)
root_name = next((o.name for o in sty.scene.objects if o.name.startswith("Decor_")), "Decor_0")
for o in sty.scene.objects:
    if o.type == "MESH":
        o.data = o.data.copy()
groups = {}
meshes = [o for o in sty.scene.objects if o.type == "MESH"]
parts = []
for o in meshes:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
    parts += up.split_by_material(o)
for o in parts:
    up.weld(o)
    m = o.data.materials[0] if o.data.materials else None
    rgb, key, ec = up.mat_info(m)
    if key == "glow":
        key = up.glow_key(ec)
    if key not in groups:
        g = bpy.data.objects.new("G_" + key, None)
        sty.scene.collection.objects.link(g)
        groups[key] = g
    dims = sorted(o.dimensions)
    bevel = None
    if dims[0] > 0.06 and len(o.data.vertices) < 500 and not key.startswith("glow") and key != "grass":
        bevel = min(0.03, dims[0] * 0.12)
    reg(o, rgb, matk=key, parent=None, bevel=bevel, var=0.07 if key in ("matte", "grass") else 0.04, smooth=True,
        noao=key.startswith("glow"))
# parent each part to its finish group without moving it
bpy.context.view_layer.update()
for o, _ in sty.PARTS:
    m = o.data.materials[0]
    key = next(k for k, v in sty.MAT.items() if v == m)
    mw = o.matrix_world.copy()
    o.parent = groups[key]
    o.matrix_world = mw

sty.bake(ao_dist=0.9, ao_strength=0.85, outline_w=0.05, ground=0.0, rays=RAYS, ray_offset=0.02, ao_floor=0.38)
names = {g.name: "Baked_" + k for k, g in groups.items()}
sty.merge(names)
sty.outline(0.05, 1.0)
for o in list(sty.scene.objects):          # drop the imported root so the new one gets the exact name
    if o.name.startswith("Decor_") and o.type == "EMPTY":
        bpy.data.objects.remove(o)
root = bpy.data.objects.new(root_name, None)
sty.scene.collection.objects.link(root)
for o in list(sty.scene.objects):
    if o.parent is None and o is not root:
        mw = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = mw
sty.stats(os.path.basename(OUT))
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_animations=False, export_apply=True)
print("BAKED", OUT, root_name)
