"""Stone Age map decor kit, v2 art pass. One GLB, one mesh per prop, every prop at the origin.
game.gd reads the meshes by name and scatters them with MultiMeshes (one draw call per prop type):
  Pine_A, Pine_B, Pine_C, Bush_A, Bush_B, Rock_A, Rock_B, Rock_C, Stump, Log, Flowers, Tuft
and places the one-off landmarks as normal nodes:
  Mammoth (skeleton), Dolmen, BoneHut, Cave (the base the robots march on)
Each mesh also has a *_Outline shell (the cartoon outline), except the small ones.

Usage: python3 decor_stone_v2.py -- --out assets/decor/stone_decor.glb [--preview DIR]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sty
from sty import P, reg, cyl, ico, uvs, torus, box, rod, empty, jitter, lerp, mul, point_at
from mathutils import Vector, noise
import bpy

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default
OUT = arg("--out", "assets/decor/stone_decor.glb")
PREVIEW = arg("--preview")

sty.reset(7)
PROPS = []


def prop(name):
    e = empty(name)
    PROPS.append(e)
    return e


def pine(name, h=2.6, layers=3, r0=0.95, col=(0.12, 0.42, 0.13), hi=(0.32, 0.64, 0.18)):
    with sty.soft_ao(0.35):
        return _pine(name, h, layers, r0, col, hi)


def _pine(name, h, layers, r0, col, hi):
    root = prop(name)
    reg(cyl(0.13, 0.55, (0, 0, 0.27), verts=6, r2=0.1), P["wood_dark"], parent=root, var=0.06, name="Trunk")
    for k in range(layers):
        t = k / max(layers - 1, 1)
        z0 = 0.4 + t * (h - 1.2)
        r = r0 * (1.0 - 0.32 * t)
        hh = 1.15 * (1.0 - 0.15 * t)
        c = cyl(r, hh, (0, 0, z0 + hh / 2), verts=9, r2=0.0)
        for v in c.data.vertices:          # jagged needle skirt
            if v.co.z < 0:
                a = math.atan2(v.co.y, v.co.x)
                v.co.z -= 0.08 * (1 + math.sin(a * 9))
                v.co.x *= random.uniform(0.92, 1.08)
                v.co.y *= random.uniform(0.92, 1.08)
        reg(c, col, parent=root, var=0, smooth=False, name="Needles",
            colfn=lambda p, n, col=col, hi=hi, h=h: lerp(col, hi, (p.z / h) * 0.7 + 0.35 * max(0.0, n.z) + 0.15 * noise.noise(p * 3)))
    return root


def bush(name, n=4, s=1.0):
    with sty.soft_ao(0.5):
        return _bush(name, n, s)


def _bush(name, n, s):
    root = prop(name)
    for k in range(n):
        a = k * math.tau / n + random.uniform(-0.3, 0.3)
        r = random.uniform(0.32, 0.45) * s
        rr = 0.0 if k == 0 else 0.3 * s
        o = ico(r, (rr * math.cos(a), rr * math.sin(a), r * 0.75), sub=2, scale=(1, 1, 0.85))
        jitter(o, 0.03 * s)
        reg(o, P["grass"], parent=root, var=0, name="Leaves",
            colfn=lambda p, n, s=s: lerp(mul(P["grass_dark"], 1.3), P["grass_hi"], 0.25 + p.z / (0.9 * s) * 0.6 + 0.2 * max(0.0, n.z)))
    if random.random() < 0.6:
        for k in range(3):
            a = random.uniform(0, math.tau)
            reg(ico(0.05 * s, (0.33 * s * math.cos(a), 0.33 * s * math.sin(a), 0.45 * s), sub=1), (0.85, 0.12, 0.1), parent=root, var=0.05, name="Berry")
    return root


def rock(name, r=0.6, moss=True, seed=0):
    root = prop(name)
    o = ico(r, (0, 0, r * 0.35), sub=2, scale=(1.25, 1.0, 0.72), rot=(0, 0, seed))
    for v in o.data.vertices:
        v.co *= 1.0 + 0.18 * noise.noise(v.co * 2.3 + Vector((seed, 0, 0)))
    reg(o, P["stone"], parent=root, var=0, smooth=False, name="Rock",
        colfn=lambda p, n, moss=moss: lerp(lerp(P["stone_dark"], P["stone_light"], 0.45 + 0.6 * noise.noise(p * 2.5)), P["moss"],
                                           0.85 if (moss and n.z > 0.75 and noise.noise(p * 3) > -0.15) else 0.0))
    return root


def stump(name):
    root = prop(name)
    reg(cyl(0.26, 0.38, (0, 0, 0.19), verts=9, r2=0.22), P["wood"], parent=root, bevel=0.03, var=0.06, name="Stump")
    reg(cyl(0.215, 0.02, (0, 0, 0.385), verts=9), P["wood_cut"], parent=root, var=0, name="Cut")
    reg(cyl(0.11, 0.02, (0, 0, 0.392), verts=9), P["wood"], parent=root, var=0, name="Ring")
    for k in range(3):
        a = k * math.tau / 3 + 0.4
        reg(rod((0.15 * math.cos(a), 0.15 * math.sin(a), 0.1), (0.36 * math.cos(a), 0.36 * math.sin(a), 0.0), 0.06, 5), P["wood_dark"], parent=root, var=0.05, name="Root")
    return root


def log(name):
    root = prop(name)
    reg(cyl(0.17, 1.4, (0, 0, 0.17), verts=9, rot=(0, math.radians(90), 0)), P["wood"], parent=root, bevel=0.03, var=0.06, name="Log",
        colfn=lambda p, n: lerp(P["wood_dark"], P["wood"], 0.5 + noise.noise(p * 4)) if n.z > -0.5 else P["moss"])
    for sx in (-1, 1):
        reg(cyl(0.15, 0.02, (sx * 0.705, 0, 0.17), verts=9, rot=(0, math.radians(90), 0)), P["wood_cut"], parent=root, var=0, name="End")
    return root


def flowers(name):
    root = prop(name)
    cols = [(0.95, 0.85, 0.2), (0.95, 0.95, 0.95), (0.85, 0.35, 0.7), (0.55, 0.65, 1.0)]
    for k in range(7):
        a = random.uniform(0, math.tau)
        r = random.uniform(0.0, 0.32)
        x, y = r * math.cos(a), r * math.sin(a)
        h = random.uniform(0.12, 0.22)
        reg(cyl(0.012, h, (x, y, h / 2), verts=3), P["grass"], parent=root, var=0.05, name="Stem")
        reg(ico(0.045, (x, y, h), sub=1, scale=(1, 1, 0.6)), random.choice(cols), parent=root, var=0.05, name="Bloom", noao=True)
    return root


def tuft_prop(name):
    root = prop(name)
    sty.tuft(root, 0, 0, 1.2, z=0.0)
    sty.tuft(root, 0.12, 0.06, 0.9, z=0.0)
    return root


def mammoth():
    """A mammoth skeleton half sunk in the grass: skull, tusks, ribs, spine."""
    root = prop("Mammoth")
    bone = P["bone"]
    old = P["bone_old"]
    cb = lambda p, n: lerp(old, bone, 0.45 + 0.6 * noise.noise(p * 2) + p.z * 0.3)
    # spine
    pts = [Vector((-1.6 + i * 0.55, 0, 1.05 + 0.25 * math.sin(i * 0.6))) for i in range(7)]
    for a, b in zip(pts, pts[1:]):
        reg(rod(a, b, 0.11, 7), bone, matk="satin", parent=root, var=0, name="Spine", colfn=cb)
        reg(cyl(0.07, 0.35, a + Vector((0, 0, 0.2)), verts=5, r2=0.03), bone, matk="satin", parent=root, var=0, name="Vertebra", colfn=cb)
    # ribs: arcs on both sides
    for i in range(5):
        x = -1.1 + i * 0.4
        for side in (-1, 1):
            prev = Vector((x, 0, 1.05 + 0.2 * math.sin((i + 1) * 0.6)))
            for k in range(1, 5):
                t = k / 4
                q = Vector((x + 0.08 * t, side * (0.15 + 0.75 * math.sin(t * 2.3)), prev.z - 0.27))
                reg(rod(prev, q, 0.06 - 0.008 * k, 6), bone, matk="satin", parent=root, var=0, name="Rib", colfn=cb)
                prev = q
    # skull + tusks + jaw
    sk = Vector((2.25, 0, 0.85))
    reg(ico(0.55, sk, sub=2, scale=(1.0, 0.85, 0.9)), bone, matk="satin", parent=root, var=0, name="Skull", colfn=cb)
    for side in (-1, 1):
        reg(ico(0.13, sk + Vector((0.3, side * 0.3, 0.12)), sub=1), P["eye"], parent=root, var=0, name="Socket")
        tp = [sk + Vector((0.35, side * 0.25, -0.3)), sk + Vector((0.95, side * 0.45, -0.75)), sk + Vector((1.65, side * 0.55, -0.45)), sk + Vector((1.85, side * 0.2, 0.15))]
        for i in range(3):
            reg(rod(tp[i], tp[i + 1], 0.16 - i * 0.04, 8, r2=0.12 - i * 0.04), bone, matk="satin", parent=root, var=0, name="Tusk", colfn=cb)
    # pelvis and leg bones lying around
    reg(ico(0.4, (-1.75, 0, 0.7), sub=2, scale=(0.6, 1.2, 0.8)), bone, matk="satin", parent=root, var=0, name="Pelvis", colfn=cb)
    for (a, b) in (((-1.2, 0.9, 0.1), (0.1, 1.2, 0.12)), ((0.6, -1.0, 0.1), (1.7, -1.3, 0.1)), ((-1.8, -0.8, 0.1), (-0.8, -1.4, 0.1))):
        reg(rod(a, b, 0.11, 7), bone, matk="satin", parent=root, var=0, name="LegBone", colfn=cb)
        for e in (a, b):
            reg(ico(0.15, e, sub=1), bone, matk="satin", parent=root, var=0, name="Knuckle", colfn=cb)
    for k in range(6):
        a = random.uniform(0, math.tau)
        sty.tuft(root, 1.8 * math.cos(a), 1.2 * math.sin(a), 1.3, z=0.0)
    return root


def dolmen():
    root = prop("Dolmen")
    cb = lambda p, n: lerp(lerp(P["stone_dark"], P["stone"], 0.5 + 0.7 * noise.noise(p * 2.5)), P["moss"], 0.7 if (n.z > 0.7 and noise.noise(p * 2) > 0) else max(0.0, 0.4 - p.z))
    for x, y, h in ((-0.8, -0.55, 1.6), (0.85, -0.5, 1.7), (0.0, 0.7, 1.65)):
        st = box((0.55, 0.42, h), (x, y, h / 2), rot=(random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), random.uniform(0, 1)))
        jitter(st, 0.05)
        reg(st, P["stone"], parent=root, bevel=0.08, var=0, name="Upright", colfn=cb)
    cap = box((2.5, 1.9, 0.38), (0, 0, 1.82), rot=(0.06, -0.05, 0.3))
    jitter(cap, 0.07)
    reg(cap, P["stone"], parent=root, bevel=0.1, var=0, name="Capstone", colfn=cb)
    for k in range(5):
        a = random.uniform(0, math.tau)
        sty.tuft(root, 1.2 * math.cos(a), 1.1 * math.sin(a), 1.3, z=0.0)
    # ochre spirals painted on the front stone
    for k in range(3):
        reg(torus(0.17 - k * 0.055, 0.02, (-0.8, -0.79, 0.95), rot=(math.radians(90), 0, 0), maj=12, mi=3), P["ochre"], parent=root, var=0, name="Spiral")
    return root


def bone_hut():
    """Mammoth-bone dwelling (like Mezhyrich): a hide dome ringed and roofed with tusks and jawbones."""
    root = prop("BoneHut")
    dome = uvs(1.1, (0, 0, 0.0), seg=14, rings=8, scale=(1.0, 1.0, 0.95))
    for v in dome.data.vertices:
        if v.co.z < 0:
            v.co.z = 0
        v.co.x += 0.04 * math.sin(v.co.z * 9 + v.co.y * 5)
    reg(dome, P["hide"], parent=root, var=0, name="Hide",
        colfn=lambda p, n: lerp(mul(P["hide"], 0.65), P["hide"], 0.5 + 0.9 * noise.noise(p * 3)))
    cb = lambda p, n: lerp(P["bone_old"], P["bone"], 0.5 + 0.6 * noise.noise(p * 3))
    for k in range(9):          # tusk arches leaning on the dome
        a = k * math.tau / 9 + 0.2
        base = Vector((1.15 * math.cos(a), 1.15 * math.sin(a), 0.0))
        top = Vector((0.45 * math.cos(a), 0.45 * math.sin(a), 1.05))
        mid = base.lerp(top, 0.5) + Vector((0.25 * math.cos(a), 0.25 * math.sin(a), 0.15))
        reg(rod(base, mid, 0.09, 6, r2=0.075), P["bone"], matk="satin", parent=root, var=0, name="Tusk", colfn=cb)
        reg(rod(mid, top, 0.075, 6, r2=0.04), P["bone"], matk="satin", parent=root, var=0, name="Tusk", colfn=cb)
    for k in range(14):         # ring of stacked jaw bones at the foot
        a = k * math.tau / 14
        reg(ico(0.17, (1.15 * math.cos(a), 1.15 * math.sin(a), 0.12), sub=1, scale=(1.3, 0.8, 0.7), rot=(0, 0, a)), P["bone"], matk="satin",
            parent=root, var=0, smooth=False, name="Jaw", colfn=cb)
    # doorway (front, -Y) with a hide flap and a smoke hole
    reg(box((0.6, 0.15, 0.75), (0, -1.06, 0.38)), (0.05, 0.03, 0.02), parent=root, var=0, name="Door", noao=True)
    reg(box((0.32, 0.06, 0.7), (0.22, -1.13, 0.4), rot=(0, 0.15, 0.4)), mul(P["hide"], 0.8), parent=root, bevel=0.02, var=0, name="Flap")
    reg(torus(0.18, 0.06, (0, 0, 1.03), maj=10, mi=4), P["wood_dark"], parent=root, var=0, name="SmokeHole")
    return root


def cave():
    """The humans' home cave at the end of the road. Mouth faces -X (the road arrives from the west)."""
    root = prop("Cave")
    cb = lambda p, n: lerp(lerp(P["stone_dark"], P["stone"], 0.45 + 0.6 * noise.noise(p * 1.5) + p.z * 0.08), P["moss"],
                           0.75 if (n.z > 0.72 and noise.noise(p * 1.4) > -0.1) else 0.0)
    for (x, y, z, r, sx, sy, sz) in ((1.0, 0.0, 0.3, 1.9, 1.0, 1.3, 0.95), (1.6, -1.6, 0.2, 1.3, 1.0, 1.0, 0.85),
                                     (1.5, 1.7, 0.2, 1.35, 1.0, 1.0, 0.9), (2.4, 0.2, 0.7, 1.4, 1.0, 1.2, 1.0), (0.6, 1.5, 0.0, 0.8, 1, 1, 0.8)):
        o = ico(r, (x, y, z), sub=2, scale=(sx, sy, sz))
        for v in o.data.vertices:
            v.co *= 1.0 + 0.16 * noise.noise(v.co * 1.7 + Vector((x, y, 0)))
        reg(o, P["stone"], parent=root, var=0, smooth=False, name="Crag", colfn=cb)
    mouth = ico(0.95, (-0.55, 0.0, 0.55), sub=2, scale=(0.45, 0.9, 0.95))
    reg(mouth, (0.03, 0.02, 0.02), parent=root, var=0, name="Mouth", noao=True)
    # hide windbreak on poles and a bone arch over the mouth
    for side in (-1, 1):
        reg(rod((-0.9, side * 0.95, 0.0), (-0.7, side * 0.75, 1.9), 0.05, 6), P["wood_dark"], parent=root, var=0.05, name="Pole")
        pts = [Vector((-0.75, side * 0.95, 0.0)), Vector((-0.85, side * 0.8, 1.1)), Vector((-0.85, side * 0.3, 1.65)), Vector((-0.85, 0.0, 1.75))]
        for i in range(3):
            reg(rod(pts[i], pts[i + 1], 0.11 - 0.025 * i, 7, r2=0.09 - 0.025 * i), P["bone"], matk="satin", parent=root, var=0, name="ArchTusk",
                colfn=lambda p, n: lerp(P["bone_old"], P["bone"], 0.6 + p.z * 0.2))
    for side in (-1, 1):
        f = box((0.06, 0.6, 1.2), (-0.95, side * 1.25, 0.6), rot=(0.08 * side, 0, 0.25 * side))
        reg(f, P["hide"], parent=root, bevel=0.02, var=0.04, name="Windbreak")
    horned = Vector((-0.9, 0.0, 2.0))
    reg(ico(0.18, horned, scale=(1.0, 1.15, 0.8)), P["bone"], matk="satin", parent=root, var=0.03, name="Skull")
    for side in (-1, 1):
        reg(rod(horned + Vector((0, side * 0.12, 0.05)), horned + Vector((0.05, side * 0.42, 0.32)), 0.06, 6, r2=0.0), P["bone"], matk="satin", parent=root, var=0, name="Horn")
    # ochre hand prints on the rock by the mouth
    for (y, z) in ((-0.95, 1.2), (0.9, 1.35), (-0.55, 1.55)):
        reg(ico(0.12, (-0.2, y, z), scale=(0.25, 1.0, 1.15)), P["ochre"], parent=root, var=0.05, name="HandPrint", no_outline=True)
    for k in range(10):
        a = random.uniform(0, math.tau)
        sty.tuft(root, 1.0 + 2.0 * math.cos(a), 2.2 * math.sin(a), 1.4, z=0.0)
    return root


pine("Pine_A", h=2.9, layers=3, r0=0.95)
pine("Pine_B", h=3.4, layers=4, r0=1.0, col=(0.08, 0.34, 0.14), hi=(0.22, 0.54, 0.2))
pine("Pine_C", h=2.0, layers=2, r0=0.75, col=(0.16, 0.46, 0.12), hi=(0.4, 0.68, 0.18))
bush("Bush_A", 4)
bush("Bush_B", 3, 0.8)
rock("Rock_A", 0.65, seed=1)
rock("Rock_B", 0.45, seed=2)
rock("Rock_C", 0.9, seed=3)
stump("Stump")
log("Log")
flowers("Flowers")
tuft_prop("Tuft")
mammoth()
dolmen()
bone_hut()
cave()

# spread the props out while baking AO (they all sit at the origin otherwise and occlude each other);
# removing their root Empties after the merge drops every mesh back to the origin for export
for i, e in enumerate(PROPS):
    e.location = ((i % 4) * 9.0, (i // 4) * 9.0, 0)
bpy.context.view_layer.update()
sty.bake(ao_dist=0.6, outline_w=0.05)
names = {e.name: e.name + "_M" for e in PROPS}
sty.merge(names)
for e in PROPS:   # flatten: the mesh becomes the prop itself (no extra Empty)
    m = bpy.data.objects.get(e.name + "_M")
    if m:
        bpy.data.objects.remove(e)
        m.location = (0, 0, 0)
        m.name = m.name[:-2]
small = {"Flowers", "Tuft"}
for o in list(sty.scene.objects):
    if o.type == "MESH" and o.name in small:
        o["skip_outline"] = 1
keep = [o for o in sty.scene.objects if o.type == "MESH" and o.name in small]
for o in keep:
    o.hide_set(False)
# outline every prop except the small ones
mesh_objs = [o for o in sty.scene.objects if o.type == "MESH"]
for o in mesh_objs:
    if o.name in small:
        for f in o.data.attributes.get("nol").data:
            f.value = 1
sty.outline(0.05, 0.55)
for o in list(sty.scene.objects):
    if o.name.endswith("_Outline") and len(o.data.polygons) == 0:
        bpy.data.objects.remove(o)
sty.stats("decor")
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_animations=False, export_apply=True)
print("EXPORTED", OUT, sorted(o.name for o in sty.scene.objects if o.type == "MESH"))

if PREVIEW:
    os.makedirs(PREVIEW, exist_ok=True)
    x = 0.0
    for o in sorted([o for o in sty.scene.objects if o.type == "MESH" and not o.name.endswith("_Outline")], key=lambda o: o.name):
        w = max(o.dimensions.x, o.dimensions.y)
        o.location.x = x + w / 2
        ol = bpy.data.objects.get(o.name + "_Outline")
        if ol:
            ol.location = o.location
        x += w + 0.4
    cam = sty.studio(floor=True)
    sty.shoot(cam, os.path.join(PREVIEW, "decor.png"), pos=(x / 2 + 4, -14, 9), target=(x / 2, 0, 0.8), ortho=x * 0.55, res=(1600, 600))
