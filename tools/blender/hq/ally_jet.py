"""v0.9.69: the task force's strike jet for Sgt. Maya Cole's Airstrike (game.gd _maya_strike): a small stylised fighter
in two-tone grey with a dark canopy, twin canted fins and a glowing afterburner. It only ever streaks over the field
high and fast, so it is built from clean bevelled primitives with flat materials (no bake).

python3 ally_jet.py -- OUT.glb     (nose along Blender +Y = Godot -Z, its forward)
"""
import sys
import math
import bpy
import bmesh
from mathutils import Vector

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/ally_jet.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, col, rough=0.5, metal=0.2, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 4.0
    return m


GREY = mat("jet_grey", (0.42, 0.46, 0.5), 0.45, 0.25)
GREY_D = mat("jet_grey_dark", (0.24, 0.27, 0.3), 0.5, 0.3)
GLASS = mat("jet_canopy", (0.05, 0.09, 0.16), 0.08, 0.6)
NOZZLE = mat("jet_nozzle", (0.12, 0.12, 0.13), 0.4, 0.8)
BURN = mat("jet_burner", (1.0, 0.55, 0.15), 0.5, 0.0, (1.0, 0.5, 0.12))
STRIPE = mat("jet_stripe", (0.75, 0.62, 0.22), 0.5, 0.1)


def obj_from_bm(name, bm, m, smooth=True, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if bevel > 0:
        bv = o.modifiers.new("bv", "BEVEL")
        bv.width = bevel
        bv.segments = 2
        bv.limit_method = "ANGLE"
    return o


def lathe(name, prof, m, seg=20, squash=(1.0, 0.85), y0=0.0, z0=0.0):
    """A body of revolution along +Y: prof = [(y, r), ...]; squash scales x and z."""
    bm = bmesh.new()
    rings = []
    for y, r in prof:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            ring.append(bm.verts.new((math.cos(a) * r * squash[0], y + y0, math.sin(a) * r * squash[1] + z0)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(seg):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]))
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        c = bm.verts.new((sum(v.co.x for v in ring) / seg, ring[0].co.y, sum(v.co.z for v in ring) / seg))
        for k in range(seg):
            f = (ring[k], ring[(k + 1) % seg], c)
            bm.faces.new(f[::-1] if flip else f)
    return obj_from_bm(name, bm, m)


def slab(name, pts, thick, m, z=0.0, bevel=0.012):
    """A flat plate in XY (outline pts, counter-clockwise from above), thick in Z, centred on z."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z - thick / 2)) for x, y in pts]
    hi = [bm.verts.new((x, y, z + thick / 2)) for x, y in pts]
    bm.faces.new(hi)
    bm.faces.new(lo[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return obj_from_bm(name, bm, m, smooth=False, bevel=bevel)


parts = []
# fuselage: a sharp nose, the cockpit hump, a wide middle over the intakes, tapering to the nozzles
parts.append(lathe("Fuselage", [(1.75, 0.0), (1.6, 0.05), (1.35, 0.12), (1.0, 0.19), (0.6, 0.24), (0.1, 0.27), (-0.5, 0.27),
                                (-1.0, 0.24), (-1.3, 0.2)], GREY, squash=(1.0, 0.8)))
parts.append(lathe("Radome", [(1.78, 0.0), (1.7, 0.035), (1.58, 0.06)], GREY_D, seg=14, squash=(1.0, 0.8)))
parts.append(lathe("Canopy", [(1.15, 0.0), (1.05, 0.07), (0.85, 0.12), (0.55, 0.13), (0.3, 0.1), (0.15, 0.0)], GLASS, seg=16,
                   squash=(0.85, 1.0), z0=0.17))
# intakes either side, and the nozzle with its afterburner glow
for sx in (-1, 1):
    o = lathe("Intake", [(0.55, 0.11), (0.5, 0.13), (-0.4, 0.13)], GREY_D, seg=12, squash=(1.0, 1.0))
    o.location = (sx * 0.27, 0.0, -0.06)
    parts.append(o)
parts.append(lathe("Nozzle", [(-1.25, 0.18), (-1.45, 0.17), (-1.5, 0.15)], NOZZLE, seg=16, squash=(1.0, 0.8)))
burn = lathe("Burner", [(-1.47, 0.0), (-1.5, 0.13), (-1.52, 0.0)], BURN, seg=16, squash=(1.0, 0.8))
parts.append(burn)
# delta wings (swept leading edge, clipped tips), tailplanes, twin canted fins
for sx in (-1, 1):
    w = [(0.2, 0.55), (1.35, -0.55), (1.35, -0.8), (0.2, -0.95)]
    pts = [(sx * x, y) for x, y in w]
    if sx < 0:
        pts = pts[::-1]
    parts.append(slab("Wing", pts, 0.05, GREY, z=-0.02))
    t = [(0.15, -0.95), (0.7, -1.3), (0.7, -1.48), (0.15, -1.45)]
    pts = [(sx * x, y) for x, y in t]
    if sx < 0:
        pts = pts[::-1]
    parts.append(slab("Tailplane", pts, 0.035, GREY, z=-0.02))
    fin = slab("Fin", [(0.0, -0.85), (0.0, -1.4), (0.62, -1.45), (0.62, -1.2)][::-1], 0.035, GREY_D, z=0.0)
    # drawn flat (x = height, y = along the body): stand it up on its root edge, canted out
    fin.rotation_euler = (0.0, math.radians(-90 + 18 * sx), 0.0)
    fin.location = (sx * 0.2, 0.0, 0.12)
    parts.append(fin)
    # a yellow band on each wing tip
    tip = [(1.15, -0.4), (1.36, -0.56), (1.36, -0.8), (1.15, -0.85)]
    pts = [(sx * x, y) for x, y in tip]
    if sx < 0:
        pts = pts[::-1]
    parts.append(slab("Stripe", pts, 0.056, STRIPE, z=-0.02, bevel=0.0))

for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
for o in parts:
    bpy.context.view_layer.objects.active = o
    for md in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)
bpy.ops.object.select_all(action="SELECT")
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
jet = bpy.context.view_layer.objects.active
jet.name = "Jet"
print("tris", sum(len(p.vertices) - 2 for p in jet.data.polygons))
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_apply=True)
print("wrote", OUT)
