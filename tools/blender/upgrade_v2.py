"""Upgrades existing model GLBs to the v2 art style (see sty.py) without remodelling them.

For every mesh part: its material becomes a vertex color (plus a little per-part variation) on a shared
finish material (matte / satin / gloss / metal / glow / Grass), edges are welded and softly bevelled,
ambient occlusion is baked in, parts are merged per rig pivot, and a cartoon outline shell is added.
Rig pivots (Yaw, Arm, Orb, Body, LegA_*, LegB_*, ...) keep their names and transforms, so game.gd
animates the result exactly like the original.

Usage: python3 upgrade_v2.py -- --kind towers|heroes|robots --src DIR --out DIR [--only a,b] [--preview DIR]
"""
import sys, os, math, random, colorsys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import sty
from sty import reg, lerp, mul

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default
KIND = arg("--kind", "towers")
SRC = arg("--src")
OUT = arg("--out")
ONLY = arg("--only")
PREVIEW = arg("--preview")

PIVOT_PREFIXES = ("Yaw", "Arm", "Orb", "Body", "LegA", "LegB", "Top", "Spin", "Flicker", "Shoulder", "Caveman", "Head", "Turret")


def principled(m):
    if m is None or not m.use_nodes:
        return None
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
    return None


def to_srgb(c):
    """Material colours are linear; Godot uses vertex colours as written (sRGB), so convert to keep
    every part the exact colour it had before the upgrade."""
    return tuple((1.055 * (x ** (1 / 2.4)) - 0.055) if x > 0.0031308 else 12.92 * x for x in c)


def mat_info(m):
    """-> (vertex rgb in sRGB, finish key, emission rgb (linear) or None)"""
    rgb, key, ec = _mat_info(m)
    return to_srgb(rgb), key, ec


def _mat_info(m):
    b = principled(m)
    if b is None:
        return (0.6, 0.6, 0.6), "matte", None
    c = tuple(b.inputs["Base Color"].default_value[:3])
    rough = b.inputs["Roughness"].default_value
    metal = b.inputs["Metallic"].default_value
    ec = tuple(b.inputs["Emission Color"].default_value[:3])
    es = b.inputs["Emission Strength"].default_value
    if es > 0.01 and max(ec) > 0.05:
        return ec, "glow", ec
    name = m.name.lower()
    if name.startswith("grass"):
        return c, "grass", None
    if metal >= 0.45:
        return c, "metal", None
    if rough < 0.3:
        return c, "gloss", None
    if rough < 0.62:
        return c, "satin", None
    return c, "matte", None


_glow_cache = {}
def glow_key(ec):
    """One shared glow finish per emission colour (kept gentle: the bloom pass does the rest)."""
    k = "glow_%02x%02x%02x" % tuple(int(min(1.0, x) * 255) for x in ec)
    if k not in sty.MAT:
        sty.MAT[k] = sty._make_mat("Glow_" + k[5:], 0.4, emit=ec, emit_e=1.0)
    return k


def split_by_material(o):
    if len(o.data.materials) <= 1:
        return [o]
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.mesh.separate(type="MATERIAL")
    return [x for x in bpy.context.selected_objects if x.type == "MESH"]


def lift_children(o):
    """A mesh that parents other nodes is replaced by an Empty of the same name holding the mesh,
    so merging meshes later can never delete a pivot's parent."""
    if not o.children:
        return o
    e = bpy.data.objects.new(o.name, None)
    sty.scene.collection.objects.link(e)
    e.parent = o.parent
    e.matrix_world = o.matrix_world.copy()
    for c in list(o.children):
        mw = c.matrix_world.copy()
        c.parent = e
        c.matrix_world = mw
    o.name = o.name + "_geo"
    mw = o.matrix_world.copy()
    o.parent = e
    o.matrix_world = mw
    return o


def weld(o, max_edge=0.32):
    """Weld split vertices, then split long edges so the baked ambient occlusion is sampled across big flat
    faces (a floor disc with only rim vertices would otherwise go dark all over)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    # two-sided parts (a face and its mirror on the same vertices) would scramble the normals: keep only
    # the copy that faces away from the part's centre
    ctr = sum((v.co for v in bm.verts), Vector()) / max(1, len(bm.verts))
    groups = {}
    for f in bm.faces:
        groups.setdefault(frozenset(v.index for v in f.verts), []).append(f)
    drop = []
    for fs in groups.values():
        if len(fs) > 1:
            fs.sort(key=lambda f: -f.normal.dot(f.calc_center_median() - ctr + Vector((0, 0, 1e-3))))
            drop += fs[1:]
    if drop:
        bmesh.ops.delete(bm, geom=drop, context="FACES_ONLY")
    # inside-out parts (mirrored transforms upstream): most of the surface faces the centre -> flip it
    sc0 = o.matrix_world.to_scale()
    if sc0.x * sc0.y * sc0.z < 0:
        pass    # sty.reg flips these when it bakes the scale
    else:
        bm.normal_update()
        ctr2 = sum((f.calc_center_median() * f.calc_area() for f in bm.faces), Vector()) / max(1e-9, sum(f.calc_area() for f in bm.faces))
        out = sum(f.normal.dot((f.calc_center_median() - ctr2).normalized()) * f.calc_area() for f in bm.faces)
        tot = sum(f.calc_area() for f in bm.faces)
        if tot > 0 and out / tot < -0.25:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    sc = o.matrix_world.to_scale()
    k = (abs(sc.x) + abs(sc.y) + abs(sc.z)) / 3.0
    for _ in range(3):
        long = [e for e in bm.edges if e.calc_length() * k > max_edge]
        if not long or len(bm.verts) > 4000:
            break
        bmesh.ops.subdivide_edges(bm, edges=long, cuts=1, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.to_mesh(o.data)
    bm.free()


def convert(path):
    sty.reset(abs(hash(os.path.basename(path))) % 1000)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = list(sty.scene.objects)
    for o in objs:
        if o.type == "MESH":
            o.data = o.data.copy()
    meshes = [o for o in sty.scene.objects if o.type == "MESH"]
    for o in list(meshes):
        lift_children(o)
    parts = []
    for o in [x for x in sty.scene.objects if x.type == "MESH"]:
        parts += split_by_material(o)
    tops = [o for o in sty.scene.objects if o.parent is None and o.type == "EMPTY"]
    height = 1.0
    for o in parts:
        weld(o)
        m = o.data.materials[0] if o.data.materials else None
        rgb, key, ec = mat_info(m)
        if key == "glow":
            key = glow_key(ec)
        mname = (m.name if m else "").lower()
        skin = "skin" in mname
        dims = sorted(o.dimensions)
        bevel = None
        if dims[0] > 0.05 and len(o.data.vertices) < 600 and key not in ("grass",) and not key.startswith("glow"):
            bevel = min(0.022, dims[0] * 0.12)
        parent = o.parent
        if skin:
            with sty.soft_ao(0.5):
                reg(o, rgb, matk=key, parent=parent, bevel=bevel, var=0.03, smooth=True, noao=key.startswith("glow"))
        else:
            reg(o, rgb, matk=key, parent=parent, bevel=bevel, var=0.05 if key != "metal" else 0.03, smooth=True,
                noao=key.startswith("glow"))
        bpy.context.view_layer.update()
        height = max(height, max((o.matrix_world @ Vector(c)).z for c in o.bound_box))
    names = {}
    for o, _ in sty.PARTS:
        p = o.parent
        if p is not None:
            names[p.name] = "M_" + p.name
    return height, names


def outline_for(kind, height):
    if kind == "robots":
        return 0.042 * max(1.0, height / 1.6)
    if kind == "heroes":
        return 0.055
    return 0.06


if __name__ != "__main__":
    pass
else:
  items = sorted(f[:-4] for f in os.listdir(SRC) if f.endswith(".glb"))
  if ONLY:
      items = [i for i in items if i in ONLY.split(",")]
  os.makedirs(OUT, exist_ok=True)
  for name in items:
      if "--skip-existing" in ARGS and os.path.exists(os.path.join(OUT, name + ".glb")):
          continue
      h, names = convert(os.path.join(SRC, name + ".glb"))
      sty.finish(os.path.join(OUT, name + ".glb"), outline_w=outline_for(KIND, h), names=names, ao_dist=0.3 if KIND == "robots" else 0.5,
                 ray_offset=0.02, ao_floor=0.42, per_part_outline=True)
      if PREVIEW:
          os.makedirs(PREVIEW, exist_ok=True)
          cam = sty.studio()
          big = KIND == "towers"
          tz = h * 0.45
          sty.shoot(cam, os.path.join(PREVIEW, name + ".png"), target=(0, -0.2, tz), ortho=max(h * 1.4, 3.6 if not big else 5.0), res=(420, 420))
      print("UPGRADED", KIND, name)
