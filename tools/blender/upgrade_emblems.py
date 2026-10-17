"""Renders the upgrade emblems: one glossy 3D badge per kind of upgrade effect, in the v2 style (bevels, baked
AO, cartoon outline). The game layers an emblem over the tower's portrait to give every upgrade its own picture
(game.gd _upgrade_art). Output: assets/ui/emblem_<kind>.png (256x256, transparent).
Run: python3 tools/blender/upgrade_emblems.py [-- --only a,b]"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import sty
import icon_fix

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "ui")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None

# colours (linear)
RED = (0.85, 0.06, 0.03); ORANGE = (1.0, 0.36, 0.03); YEL = (1.0, 0.78, 0.08); GOLD = (0.95, 0.62, 0.08)
WHITE = (0.92, 0.93, 0.95); STEEL = (0.55, 0.58, 0.64); DARKSTEEL = (0.18, 0.2, 0.24); ICE = (0.45, 0.8, 1.0)
CYAN = (0.15, 0.85, 1.0); PURPLE = (0.45, 0.08, 0.85); GREEN = (0.2, 0.75, 0.12); WOOD = (0.48, 0.26, 0.10)
BLUE = (0.08, 0.3, 0.9)


# ---------------------------------------------------------------- shape helpers (emblems face -Y, in the XZ plane)
def prism(pts, depth=0.22, y=0.0, name="p"):
    bm = bmesh.new()
    vs = [bm.verts.new((x, y - depth / 2, z)) for x, z in pts]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    verts = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts, vec=(0, depth, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    sty.scene.collection.objects.link(o)
    return o


def star(n, r_out, r_in, cx=0.0, cz=0.0, rot=90.0, jitter=0.0):
    pts = []
    for i in range(n * 2):
        a = math.radians(rot + 180.0 * i / n)
        r = r_out if i % 2 == 0 else r_in
        if jitter and i % 2 == 0:
            r *= 1.0 + jitter * math.sin(i * 2.7)
        pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def circle(r, n=24, cx=0.0, cz=0.0):
    return [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def ring(R, r, loc=(0, 0, 0)):
    o = sty.torus(R, r, loc, rot=(math.radians(90), 0, 0), maj=40, mi=8)
    return o


def add(o, col, matk="gloss", bevel=0.03):
    return sty.reg(o, col, matk, bevel=bevel, var=0.0)


def bar(x0, z0, x1, z1, w, depth=0.18, y=0.0):
    """A flat rounded bar from (x0,z0) to (x1,z1)."""
    d = Vector((x1 - x0, z1 - z0))
    n = Vector((-d.y, d.x)).normalized() * w / 2
    pts = [(x0 + n.x, z0 + n.y), (x1 + n.x, z1 + n.y), (x1 - n.x, z1 - n.y), (x0 - n.x, z0 - n.y)]
    return prism(pts, depth, y)


def arrow_pts(length=1.6, shaft=0.36, head=0.85, head_len=0.7):
    L = length / 2
    return [(-L, shaft / 2), (L - head_len, shaft / 2), (L - head_len, head / 2), (L, 0), (L - head_len, -head / 2),
            (L - head_len, -shaft / 2), (-L, -shaft / 2)]


def rot2(pts, deg, cx=0.0, cz=0.0):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(cx + x * c - z * s, cz + x * s + z * c) for x, z in pts]


def crosshair(cx, cz, s, col=RED, y=0.0):
    add(sty.torus(0.62 * s, 0.09 * s, (cx, y, cz), rot=(math.radians(90), 0, 0), maj=32, mi=6), col)
    for a in range(4):
        pts = rot2([(0.42 * s, -0.07 * s), (0.95 * s, -0.07 * s), (0.95 * s, 0.07 * s), (0.42 * s, 0.07 * s)], a * 90)
        add(prism([(x + cx, z + cz) for x, z in pts], 0.16 * s, y), col)
    add(sty.uvs(0.13 * s, (cx, y - 0.05, cz)), col, "glow_red")


def arrow3d(x0, z0, x1, z1, shaft_col=WOOD, tip_col=STEEL, s=1.0, y=0.0):
    a, b = Vector((x0, y, z0)), Vector((x1, y, z1))
    d = (b - a).normalized()
    add(sty.rod(a, b - d * 0.35 * s, 0.07 * s, verts=8), shaft_col, "satin")
    add(sty.rod(b - d * 0.42 * s, b + d * 0.05 * s, 0.2 * s, verts=8, r2=0.0), tip_col, "metal")
    for k in (-1, 1):   # fletching
        side = Vector((-d.z, 0, d.x)) * 0.16 * s * k
        f = prism([(a.x, a.z), (a.x + d.x * 0.4 * s, a.z + d.z * 0.4 * s),
                   (a.x + d.x * 0.25 * s + side.x, a.z + d.z * 0.25 * s + side.z),
                   (a.x - d.x * 0.05 * s + side.x, a.z - d.z * 0.05 * s + side.z)], 0.05, y)
        add(f, RED, "satin", 0.01)


def flame_pts(h=1.8, w=1.1, cz=-0.9, n=26):
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        x = math.sin(t) * w / 2 * (1 - 0.35 * math.cos(t))
        z = cz + (1 - math.cos(t)) / 2 * h * (0.55 + 0.45 * abs(math.sin(t / 2)))
        z += 0.12 * math.sin(3 * t) * (z - cz) / h
        pts.append((x, z))
    pts.sort(key=lambda p: math.atan2(p[1] - (cz + h * 0.4), p[0]))
    return pts


# ---------------------------------------------------------------- the emblems
def e_damage():
    add(prism(star(9, 1.05, 0.62, jitter=0.12), 0.22), RED)
    add(prism(star(9, 0.78, 0.45, rot=110, jitter=0.1), 0.22, -0.1), ORANGE)
    add(prism(star(7, 0.48, 0.26, rot=100), 0.2, -0.2), YEL)


def e_range():
    add(ring(0.9, 0.08), BLUE)
    add(ring(0.52, 0.07), WHITE)
    for a in range(4):
        pts = rot2([(0.98, -0.2), (1.32, 0.0), (0.98, 0.2)], a * 90 + 45)
        add(prism(pts, 0.2), YEL)
    add(sty.uvs(0.16, (0, -0.05, 0)), RED, "glow_red")


def e_speed():
    bolt = [(0.15, 1.15), (-0.55, 0.0), (-0.05, 0.0), (-0.35, -1.15), (0.6, 0.25), (0.05, 0.25), (0.45, 1.15)]
    add(prism([(x + 0.07, z - 0.07) for x, z in bolt], 0.2, 0.1), ORANGE)
    add(prism(bolt, 0.24, -0.05), YEL)


def e_stun():
    for (cx, cz, s, rot) in ((-0.55, 0.35, 0.42, 80), (0.15, 0.7, 0.5, 100), (0.6, 0.0, 0.38, 90)):
        add(prism(star(5, s, s * 0.45, cx, cz, rot), 0.2), YEL)
    add(sty.torus(0.55, 0.06, (0.0, 0.0, -0.5), rot=(math.radians(90), 0, 0), maj=32, mi=6), ICE)
    add(sty.torus(0.3, 0.05, (0.0, -0.02, -0.5), rot=(math.radians(90), 0, 0), maj=24, mi=6), WHITE)


def e_splash():
    for a in range(8):
        pts = rot2([(0.5, -0.17), (1.2, 0.0), (0.5, 0.17)], a * 45 + 22)
        add(prism(pts, 0.18, 0.05), ORANGE)
    add(sty.torus(0.78, 0.07, (0, 0.02, 0), rot=(math.radians(90), 0, 0), maj=40, mi=6), YEL)
    rock = sty.ico(0.5, (0, -0.15, 0), sub=1, scale=(1.0, 0.8, 0.9))
    sty.jitter(rock, 0.05)
    add(rock, (0.42, 0.4, 0.38), "matte", 0.04)


def e_multi():
    crosshair(-0.5, 0.45, 0.62)
    crosshair(0.52, 0.42, 0.55)
    crosshair(0.0, -0.45, 0.72)


def e_pierce():
    shield = [(-0.75, 0.75), (0.75, 0.75), (0.75, 0.0), (0.0, -0.95), (-0.75, 0.0)]
    add(prism(shield, 0.2, 0.1), STEEL, "metal")
    add(prism([(x * 0.78, z * 0.78 + 0.03) for x, z in shield], 0.08, -0.04), DARKSTEEL, "metal")
    add(prism([(-0.15, 0.5), (0.05, 0.15), (-0.1, -0.1), (0.1, -0.45), (0.02, -0.45), (-0.2, -0.1), (-0.05, 0.15), (-0.23, 0.5)], 0.06, -0.1), (0.05, 0.05, 0.05), "matte", 0.0)
    arrow3d(-1.15, -0.95, 1.15, 0.95, WOOD, (0.85, 0.87, 0.9), 1.1, -0.2)


def e_expose():
    lens = [(math.cos(t) * 1.05, math.sin(t) * 0.55 * (1 - 0.1 * math.cos(2 * t))) for t in [i / 28 * 2 * math.pi for i in range(28)]]
    add(prism(lens, 0.2), WHITE)
    add(sty.cyl(0.42, 0.12, (0, -0.12, 0), verts=24, rot=(math.radians(90), 0, 0)), PURPLE, "gloss")
    add(sty.cyl(0.18, 0.12, (0, -0.2, 0), verts=16, rot=(math.radians(90), 0, 0)), (0.02, 0.02, 0.03), "gloss")
    add(sty.uvs(0.07, (0.12, -0.27, 0.12)), WHITE, "gloss", 0)
    add(sty.torus(1.15, 0.06, (0, 0.05, 0), rot=(math.radians(90), 0, 0), maj=40, mi=6), PURPLE, "glow_red")


def e_volley():
    for dx, ang in ((-0.45, 70), (0.0, 85), (0.45, 100)):
        a = math.radians(ang)
        arrow3d(dx - math.cos(a) * 1.0, -1.0, dx + math.cos(a) * 1.0, 1.05, WOOD, STEEL, 0.9)


def e_shred():
    plate = [(-0.85, -0.9), (0.85, -0.9), (0.85, 0.9), (-0.85, 0.9)]
    add(prism(plate, 0.2, 0.15), STEEL, "metal", 0.08)
    for k in range(4):
        add(sty.uvs(0.07, (0.65 * (1 if k % 2 else -1), 0.0, 0.7 * (1 if k < 2 else -1))), DARKSTEEL, "metal", 0)
    for i in (-1, 0, 1):
        pts = []
        for t in range(9):
            u = t / 8
            x = -0.75 + 1.5 * u + i * 0.42
            z = 0.9 - 1.8 * u + 0.25 * math.sin(u * math.pi)
            pts.append((x, z))
        top = [(x - 0.09 * math.sin(u * math.pi) - 0.02, z) for (x, z), u in zip(pts, [t / 8 for t in range(9)])]
        bot = [(x + 0.09 * math.sin(u * math.pi) + 0.02, z) for (x, z), u in zip(pts, [t / 8 for t in range(9)])]
        add(prism(top + bot[::-1], 0.12, -0.05), RED, "gloss", 0.01)


def e_boss():
    crown = [(-0.95, -0.55), (0.95, -0.55), (0.95, 0.75), (0.5, 0.2), (0.0, 0.95), (-0.5, 0.2), (-0.95, 0.75)]
    add(prism(crown, 0.26), GOLD, "metal")
    add(prism([(-0.95, -0.55), (0.95, -0.55), (0.95, -0.3), (-0.95, -0.3)], 0.3, -0.03), (0.75, 0.4, 0.04), "metal")
    for x, z, c in ((-0.5, -0.05, RED), (0.0, 0.1, (0.1, 0.4, 1.0)), (0.5, -0.05, RED)):
        add(sty.uvs(0.14, (x, -0.16, z)), c, "gloss", 0)
    for x, z in ((-0.95, 0.75), (0.0, 0.95), (0.95, 0.75)):
        add(sty.uvs(0.1, (x, 0, z)), WHITE, "gloss", 0)


def e_crit():
    crosshair(0.0, 0.0, 1.35)
    add(prism(star(4, 0.62, 0.14, rot=45), 0.14, -0.25), YEL)
    add(prism(star(4, 0.4, 0.1), 0.14, -0.3), WHITE)


def e_slow():
    for a in range(6):
        arm = rot2([(0.0, -0.08), (1.05, -0.08), (1.05, 0.08), (0.0, 0.08)], a * 60)
        add(prism(arm, 0.16), ICE, "gloss", 0.02)
        for d in (0.45, 0.75):
            for k in (-1, 1):
                br = rot2([(d, 0.0), (d + 0.28, 0.24 * k), (d + 0.2, 0.3 * k), (d - 0.05, 0.06 * k)], a * 60)
                add(prism(br, 0.14), WHITE, "gloss", 0.01)
    add(prism(star(6, 0.3, 0.2), 0.2, -0.05), WHITE)


FLAME = [(0.0, 1.2), (0.2, 0.62), (0.5, 0.92), (0.44, 0.32), (0.66, 0.06), (0.62, -0.42), (0.36, -0.86), (0.0, -1.0),
         (-0.36, -0.86), (-0.62, -0.42), (-0.66, 0.02), (-0.48, 0.5), (-0.44, 1.02), (-0.2, 0.5)]


def e_flame():
    for k, (s, col, y) in enumerate(((1.0, RED, 0.08), (0.7, ORANGE, -0.04), (0.42, YEL, -0.14))):
        add(prism([(x * s, z * s - (1 - s) * 0.95) for x, z in FLAME], 0.2, y), col)


def e_hammer():
    head = sty.box((1.3, 0.55, 0.62), (0.0, 0, 0.5), rot=(0, math.radians(-20), 0))
    add(head, STEEL, "metal", 0.08)
    add(sty.rod((0.18, 0, 0.4), (-0.45, 0, -1.15), 0.12, verts=10), WOOD, "satin")
    add(sty.rod((-0.36, 0, -0.92), (-0.47, 0, -1.2), 0.15, verts=10), (0.2, 0.1, 0.05), "satin")
    add(prism(star(5, 0.3, 0.12, 0.85, 0.95), 0.12, -0.2), YEL)


def e_energy():
    add(sty.uvs(0.62, (0, 0, 0), seg=24, rings=16), CYAN, "glow_cyan", 0)
    add(sty.uvs(0.32, (-0.08, -0.38, 0.1), seg=16, rings=10), WHITE, "gloss", 0)
    for rx, rz in ((90, 25), (90, -35)):
        o = sty.torus(0.95, 0.05, (0, 0, 0), rot=(math.radians(rx), math.radians(rz), 0), maj=40, mi=6)
        add(o, (0.6, 0.95, 1.0), "glow_cyan", 0)


def e_spear():
    head = [(0.0, 1.2), (0.38, 0.35), (0.12, 0.1), (-0.12, 0.1), (-0.38, 0.35)]
    add(prism(head, 0.18), (0.85, 0.87, 0.9), "metal", 0.02)
    add(sty.rod((0, 0, 0.12), (0, 0, -1.2), 0.1, verts=10), WOOD, "satin")
    add(sty.cyl(0.14, 0.18, (0, 0, 0.05), verts=10), RED, "satin")


def e_push():
    add(prism([(x + 0.25, z) for x, z in arrow_pts(1.5, 0.5, 1.15, 0.65)], 0.24), GREEN)
    for z, x0, x1 in ((0.55, -1.2, -0.55), (0.0, -1.3, -0.65), (-0.55, -1.2, -0.55)):
        add(bar(x0, z, x1, z, 0.14), WHITE, "gloss", 0.02)


def e_chain():
    pts = [(-0.95, -0.6), (-0.35, 0.15), (-0.1, -0.15), (0.35, 0.55), (0.95, 0.6), (0.3, 0.05), (0.05, 0.35), (-0.45, -0.45)]
    add(prism(pts, 0.16, -0.05), CYAN, "glow_cyan", 0.01)
    for x, z in ((-0.95, -0.75), (0.95, 0.75)):
        add(sty.uvs(0.3, (x, 0.05, z)), STEEL, "metal", 0)
        add(sty.torus(0.32, 0.05, (x, -0.05, z), rot=(math.radians(90), 0, 0), maj=24, mi=6), WHITE, "gloss", 0)


def e_air():
    jet = [(0.0, 1.05), (0.12, 0.45), (0.9, -0.05), (0.9, -0.2), (0.12, 0.05), (0.1, -0.6), (0.35, -0.85), (0.35, -0.95),
           (0.0, -0.85), (-0.35, -0.95), (-0.35, -0.85), (-0.1, -0.6), (-0.12, 0.05), (-0.9, -0.2), (-0.9, -0.05), (-0.12, 0.45)]
    add(prism(jet, 0.2), STEEL, "metal")
    add(sty.torus(1.1, 0.07, (0, 0.05, 0), rot=(math.radians(90), 0, 0), maj=40, mi=6), RED)
    for a in range(4):
        pts = rot2([(0.9, -0.06), (1.35, -0.06), (1.35, 0.06), (0.9, 0.06)], a * 90 + 45)
        add(prism(pts, 0.14), RED)


EMBLEMS = {
    "damage": e_damage, "range": e_range, "speed": e_speed, "stun": e_stun, "splash": e_splash, "multi": e_multi,
    "pierce": e_pierce, "expose": e_expose, "volley": e_volley, "shred": e_shred, "boss": e_boss, "crit": e_crit,
    "slow": e_slow, "flame": e_flame, "hammer": e_hammer, "energy": e_energy, "spear": e_spear, "push": e_push,
    "chain": e_chain, "air": e_air,
}


def render(name):
    sty.reset(7)
    root = sty.empty("E_" + name)
    EMBLEMS[name]()
    sty.finish(os.path.join("/tmp", "emblem_%s.glb" % name), outline_w=0.045, export=False, ao_dist=0.35)
    icon_fix.srgb_vertex_colors()
    sc = sty.scene
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.8, 0.86, 1.0, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.85
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(55), math.radians(-15), math.radians(-25)))
    bpy.context.object.data.energy = 3.4
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "Medium High Contrast"
    sc.render.film_transparent = True
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 3.05
    t = Vector((0, 0, 0))
    d = Vector((0.22, -1.0, 0.28)).normalized()
    cam.location = t + d * 12
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = sc.render.resolution_y = 256
    sc.render.filepath = os.path.join(OUT, "emblem_%s.png" % name)
    bpy.ops.render.render(write_still=True)
    print("EMBLEM", name)


for nm in EMBLEMS:
    if ONLY and nm not in ONLY:
        continue
    render(nm)
