"""Iron, Classical, Medieval and Gunpowder Age towers + heroes (16 towers, 8 heroes).
Run: python3 eras_a.py --out ASSETS_DIR [--only a,b] [--era iron,medieval] [--preview] [--pdir PREVIEW_DIR]
Pivots for the game: Yaw (turns to face target), Arm (attack swing, + rotation = forward), Orb (pulse flash).
Visual briefs live in tools/era_spec.py (TOWERS / HEROES "visual", ERAS "look")."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp
from lp import mat, empty, cyl, ico, uvs, box, torus, jitter


def _arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


OUT = _arg("--out")
ONLY = _arg("--only").split(",") if "--only" in sys.argv else None
ERA_SEL = _arg("--era").split(",") if "--era" in sys.argv else None
PDIR = _arg("--pdir", OUT)
R = math.radians
lp.reset(17)

# ================================================================== shared palette
SKIN = mat("Skin", (0.78, 0.45, 0.28), 0.7)
SKIN_P = mat("SkinPale", (0.88, 0.6, 0.45), 0.7)
SKIN_T = mat("SkinTan", (0.66, 0.42, 0.27), 0.7)
SKIN_D = mat("SkinDeep", (0.45, 0.27, 0.16), 0.7)
EYE = mat("Eye", (0.02, 0.02, 0.02), 0.3)
STONE = mat("Stone", (0.52, 0.52, 0.5), 0.85)
HERO_RING = mat("HeroRing", (1.0, 0.82, 0.3), 0.3, 0.6, emit=(1.0, 0.7, 0.15), strength=0.8)
HAIR_BLACK = mat("HairBlack", (0.07, 0.05, 0.05), 0.85)
HAIR_BROWN = mat("Hair", (0.16, 0.09, 0.05), 0.9)
HAIR_RED = mat("HairRed", (0.75, 0.22, 0.05), 0.85)
HAIR_BLOND = mat("HairBlond", (0.88, 0.64, 0.26), 0.85)
HAIR_WHITE = mat("HairWhite", (0.9, 0.88, 0.84), 0.85)
HAIR_GREY = mat("HairGrey", (0.6, 0.58, 0.56), 0.85)
FIRE = mat("Ember", (1.0, 0.5, 0.1), 0.4, 0.0, emit=(1.0, 0.4, 0.05), strength=1.4)
ROPE = mat("Rope", (0.72, 0.6, 0.38), 0.9)
SHOE = mat("ShoeBlack", (0.1, 0.08, 0.07), 0.6)


# ================================================================== helpers
def seg(p0, p1, r, m, parent, verts=6, r2=None, ext=1.0):
    """Cylinder (or cone with r2) from p0 to p1 in the parent's local space."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    o = cyl(r, d.length * ext, tuple((p0 + p1) / 2), m, parent, verts=verts, r2=r2)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return o


def orient(o, z_axis, x_hint):
    """Rotate o so its local Z points along z_axis and local X as close as possible to x_hint."""
    from mathutils import Matrix
    z = Vector(z_axis).normalized()
    x = Vector(x_hint)
    x = (x - z * x.dot(z)).normalized()
    y = z.cross(x)
    o.rotation_euler = Matrix((x, y, z)).transposed().to_euler()
    return o


def chain(parent, m, pts, r, verts=5, joints=False):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        seg(a, b, r, m, parent, verts=verts, ext=1.08)
    if joints:
        for p in pts[1:-1]:
            ico(r * 1.05, tuple(p), m, parent, sub=1)


def arc_pts(center, radius, a0, a1, segs, u=(0, -1, 0), v=(0, 0, 1)):
    c, u, v = Vector(center), Vector(u), Vector(v)
    return [c + radius * (math.cos(R(a0 + (a1 - a0) * i / segs)) * u + math.sin(R(a0 + (a1 - a0) * i / segs)) * v)
            for i in range(segs + 1)]


def slab(parent, m, pts, thick, loc=(0, 0, 0), plane="xz", rot=(0, 0, 0), name="Slab"):
    """Flat extruded polygon. plane 'xz': points are (x, z), thickness along Y (faces the front);
    'yz': (y, z), thickness along X; 'xy': (x, y), thickness along Z."""
    def P(u, v, w):
        if plane == "xz":
            return (u, w, v)
        if plane == "yz":
            return (w, u, v)
        return (u, v, w)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    f = [bm.verts.new(P(u, v, -thick / 2)) for u, v in pts]
    b = [bm.verts.new(P(u, v, thick / 2)) for u, v in pts]
    bm.faces.new(f)
    bm.faces.new(list(reversed(b)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((f[i], f[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    return lp._link(o, m, parent)


def figure(parent, loc, skin, top, bottom, hair=None, scale=1.0, burly=1.0, beard=None, hair_style="short",
           belt=None, sleeve=None, leg=None, boot=None, left_arm=True, robe=None, face=True):
    """lp.person with extra options: sleeve/leg/boot materials, robe (replaces legs), no left arm, no face.
    Returns (body, arm). Arm is the right-shoulder pivot; the left shoulder is at (0.62, 0, 0) in Arm space."""
    body = empty("Body", loc, parent)
    body.scale = (scale * burly, scale, scale)
    leg = leg or skin
    sleeve = sleeve or skin
    boot = boot or mat("Sandal", (0.38, 0.24, 0.13), 0.8)
    if robe is None:
        for s in (-1, 1):
            cyl(0.085, 0.42, (s * 0.13, 0, 0.21), leg, body, verts=6)
            ico(0.1, (s * 0.13, -0.05, 0.03), boot, body, sub=1, scale=(1, 1.4, 0.5))
        cyl(0.33, 0.42, (0, 0, 0.5), bottom, body, verts=8, r2=0.25)
    else:
        cyl(0.4, 0.78, (0, 0, 0.39), robe, body, verts=10, r2=0.25)
    ico(0.27, (0, 0, 0.8), top, body, sub=2, scale=(1.0, 0.78, 1.05))
    if belt is not None:
        cyl(0.3, 0.07, (0, 0, 0.6), belt, body, verts=8)
    cyl(0.08, 0.12, (0, -0.01, 1.03), skin, body, verts=6)
    ico(0.21, (0, -0.02, 1.16), skin, body, sub=2, scale=(1, 0.95, 1.05))
    if face:
        ico(0.055, (0, -0.22, 1.13), skin, body, sub=1, scale=(0.8, 1, 1))
        for s in (-1, 1):
            ico(0.03, (s * 0.08, -0.195, 1.19), EYE, body, sub=1)
    if hair is not None:
        if hair_style in ("short", "long", "pony", "braids"):
            ico(0.225, (0, 0.03, 1.22), hair, body, sub=2, scale=(1.05, 1.0, 0.78))
        if hair_style == "long":
            box((0.36, 0.12, 0.42), (0, 0.13, 1.02), hair, body, bevel=0.04)
        if hair_style == "pony":
            cyl(0.07, 0.45, (0, 0.24, 1.08), hair, body, verts=6, rot=(R(-25), 0, 0))
        if hair_style == "braids":
            for s in (-1, 1):
                chain(body, hair, [(s * 0.19, 0.04, 1.16), (s * 0.23, -0.04, 0.98), (s * 0.22, -0.1, 0.78)], 0.055, verts=6)
                ico(0.05, (s * 0.22, -0.1, 0.76), hair, body, sub=1)
    if beard is not None:
        ico(0.15, (0, -0.15, 1.03), beard, body, sub=1, scale=(1.1, 0.7, 1.0))
    if left_arm:
        cyl(0.07, 0.45, (0.34, 0, 0.76), sleeve, body, verts=6, rot=(0, R(-10), 0))
        ico(0.08, (0.37, -0.02, 0.52), skin, body, sub=1)
    arm = empty("Arm", (-0.31, 0, 0.96), body)
    return body, arm


def limb(parent, sleeve, skin, end, start=(0, 0, 0), elbow=None, r=0.068):
    """Arm from start (shoulder) via optional elbow to a hand at end."""
    pts = [start] + ([elbow] if elbow else []) + [end]
    for a, b in zip(pts, pts[1:]):
        seg(a, b, r, sleeve, parent, verts=6, ext=1.06)
    if elbow:
        ico(r * 1.02, elbow, sleeve, parent, sub=1)
    ico(0.078, end, skin, parent, sub=1)
    return Vector(end)


LSH = (0.62, 0, 0)  # left shoulder in Arm space


def cuff(parent, m, a, b, t=0.75, r=0.08):
    """Short wider ring along the limb a->b at fraction t (sleeve cuff / bracer)."""
    a, b = Vector(a), Vector(b)
    p = a + (b - a) * t
    d = (b - a).normalized() * 0.05
    seg(p - d, p + d, r, m, parent, verts=8)


def hero_base(parent, color_mat):
    cyl(0.8, 0.22, (0, 0, 0.11), STONE, parent, verts=12)
    torus(0.78, 0.06, (0, 0, 0.23), HERO_RING, parent, major=24)
    cyl(0.7, 0.04, (0, 0, 0.23), color_mat, parent, verts=12)


def team(name, rgb):
    return mat(name + "Team", tuple(rgb), 0.8)


def cape(body, m, lines=None, length=0.75, width=0.62, tilt=8, y=0.25, top=1.05, collar=True):
    c = empty("Cape", (0, y, top), body)
    c.rotation_euler = (R(tilt), 0, 0)
    box((width, 0.07, length), (0, 0, -length / 2), m, c, bevel=0.02)
    if lines is not None:  # plaid: two vertical and two horizontal stripes on the back
        for x in (-width * 0.22, width * 0.22):
            box((0.045, 0.012, length * 0.96), (x, 0.04, -length / 2), lines, c)
        for z in (-length * 0.3, -length * 0.68):
            box((width * 0.96, 0.012, 0.045), (0, 0.042, z), lines, c)
    if collar:
        cyl(0.31, 0.12, (0, 0.03, 1.0), m, body, verts=8, r2=0.25)
    return c


def sash(body, m, tilt=35, z=0.8, R0=0.265, r=0.035):
    """Ring wrapped diagonally round the torso (crossbelt / baldric / sash)."""
    o = torus(R0, r, (0, 0, z), m, body, rot=(0, R(tilt), 0), major=14, minor=4)
    o.scale = (1, 0.82, 1)
    return o


def hood(body, m, point=0.0, tilt=-35):
    ico(0.27, (0, 0.09, 1.22), m, body, sub=2, scale=(1.08, 1.0, 1.08))
    cyl(0.33, 0.18, (0, 0.03, 1.0), m, body, verts=10, r2=0.25)
    if point > 0:
        cyl(0.15, point, (0, 0.2, 1.4 + point * 0.25), m, body, verts=8, r2=0.0, rot=(R(tilt), 0, 0))


def helm_dome(body, m, crest=None, trim=None, nose=True, transverse=False):
    cyl(0.235, 0.2, (0, 0.0, 1.27), m, body, verts=10, r2=0.2)
    ico(0.2, (0, 0.0, 1.33), m, body, sub=2, scale=(1.08, 1.08, 0.7))
    if nose:
        box((0.04, 0.09, 0.14), (0, -0.2, 1.19), m, body)
    if trim is not None:
        cyl(0.245, 0.04, (0, 0, 1.19), trim, body, verts=10)
    if crest is not None:
        if transverse:
            box((0.52, 0.07, 0.17), (0, 0.0, 1.5), crest, body, bevel=0.03)
        else:
            box((0.07, 0.46, 0.18), (0, 0.04, 1.5), crest, body, bevel=0.03)


def helm_cone(body, m, trim=None):
    cyl(0.235, 0.14, (0, 0, 1.25), m, body, verts=10)
    cyl(0.235, 0.36, (0, 0, 1.5), m, body, verts=10, r2=0.02)
    if trim is not None:
        cyl(0.245, 0.05, (0, 0, 1.2), trim, body, verts=10)
    box((0.05, 0.08, 0.2), (0, -0.23, 1.15), m, body)


def hero_yaw(root, rgb, name):
    hero_base(root, team(name, rgb))
    return empty("Yaw", (0, 0, 0.25), root)


def plank_lines(parent, m, r, z, n=5, along="y"):
    for i in range(n):
        x = -r * 0.8 + 1.6 * r * i / (n - 1)
        L = 2 * math.sqrt(max(r * r - x * x, 0.01)) * 0.92
        if along == "y":
            box((0.035, L, 0.02), (x, 0, z), m, parent)
        else:
            box((L, 0.035, 0.02), (0, x, z), m, parent)


def stakes(parent, wood, tip, r, a0, a1, n, h=0.6, z0=0.25, thick=0.09):
    for k in range(n):
        a = R(a0 + (a1 - a0) * k / (n - 1))
        x, y = math.cos(a) * r, math.sin(a) * r
        hh = h * random.uniform(0.85, 1.1)
        cyl(thick, hh, (x, y, z0 + hh / 2), wood, parent, verts=6)
        cyl(thick, 0.17, (x, y, z0 + hh + 0.085), tip, parent, verts=6, r2=0.0)


def hide_tree(root, hide=True):
    for o in lp.hierarchy(root):
        o.hide_render = hide


# ================================================================== IRON AGE
IR_IRON = mat("Ir_Iron", (0.26, 0.27, 0.3), 0.45, 0.5)
IR_EDGE = mat("Ir_Edge", (0.7, 0.72, 0.76), 0.3, 0.5)
IR_TIMBER = mat("Ir_Timber", (0.55, 0.34, 0.16), 0.85)
IR_TIMBER_D = mat("Ir_TimberDark", (0.33, 0.2, 0.1), 0.85)
IR_WATTLE = mat("Ir_Wattle", (0.66, 0.5, 0.28), 0.9)
IR_STONE = mat("Ir_Stone", (0.5, 0.52, 0.48), 0.9)
IR_STONE_D = mat("Ir_StoneDark", (0.36, 0.38, 0.35), 0.9)
IR_MOSS = mat("Ir_Moss", (0.3, 0.55, 0.16), 0.9)
IR_GRASS = mat("Ir_Grass", (0.38, 0.62, 0.22), 0.9)
IR_GREEN = mat("Ir_PlaidGreen", (0.1, 0.5, 0.22), 0.85)
IR_BLUE = mat("Ir_PlaidBlue", (0.14, 0.3, 0.75), 0.85)
IR_WOOL = mat("Ir_Wool", (0.85, 0.74, 0.52), 0.9)
IR_RED = mat("Ir_Red", (0.75, 0.16, 0.1), 0.85)
IR_WOAD = mat("Ir_Woad", (0.08, 0.35, 1.0), 0.6)
IR_BRONZE = mat("Ir_Bronze", (0.8, 0.5, 0.18), 0.35, 0.55)
IR_FUR = mat("Ir_Fur", (0.45, 0.3, 0.17), 0.95)
IR_FUR_L = mat("Ir_FurLight", (0.66, 0.5, 0.32), 0.95)
IR_WOLF = mat("Ir_Wolf", (0.4, 0.38, 0.38), 0.95)
IR_LEATHER = mat("Ir_Leather", (0.4, 0.24, 0.12), 0.8)
IR_ROBE = mat("Ir_Robe", (0.94, 0.93, 0.86), 0.85)
IR_GLOW = mat("Ir_DruidGlow", (0.25, 0.95, 0.2), 0.3, 0.0, emit=(0.2, 0.9, 0.12), strength=1.0)
IR_SHIELD = mat("Ir_ShieldPaint", (0.12, 0.32, 0.85), 0.7)
IR_CREAM = mat("Ir_Cream", (0.96, 0.9, 0.7), 0.7)


def iron_base(root, r=1.5):
    """Timber deck on a low ring of field stones."""
    cyl(r + 0.05, 0.26, (0, 0, 0.01), IR_STONE_D, root, verts=12)
    for k in range(11):
        a = k * 2 * math.pi / 11 + 0.2
        o = ico(0.2, (math.cos(a) * (r - 0.02), math.sin(a) * (r - 0.02), 0.08), IR_STONE, root, sub=1,
                scale=(1.2, 1.0, 0.75))
        o.rotation_euler = (0, 0, a)
        jitter(o, 0.03)
    cyl(r - 0.12, 0.14, (0, 0, 0.21), IR_TIMBER, root, verts=12)
    plank_lines(root, IR_TIMBER_D, r - 0.12, 0.285, n=6)
    torus(r - 0.12, 0.035, (0, 0, 0.27), IR_TIMBER_D, root, major=20, minor=4)


def javelin(parent, p0, p1, wood=None, tip=None, r=0.022):
    wood = wood or IR_TIMBER
    tip = tip or IR_IRON
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    seg(p0, p1, r, wood, parent, verts=5)
    seg(p1 - d * 0.02, p1 + d * 0.24, r * 2.3, tip, parent, verts=4, r2=0.0)


def woad_face(body):
    box((0.36, 0.05, 0.07), (0, -0.165, 1.19), IR_WOAD, body)  # band across the eyes
    for s in (-1, 1):
        box((0.035, 0.04, 0.12), (s * 0.12, -0.165, 1.08), IR_WOAD, body, rot=(0, R(s * 15), 0))


def javelin_thrower():
    root = empty("JavelinThrower")
    iron_base(root)
    # wattle fence segment (back-left)
    posts = [Vector((math.cos(R(a)) * 1.18, math.sin(R(a)) * 1.18, 0)) for a in (102, 122, 142, 162)]
    for p in posts:
        cyl(0.045, 0.75, (p.x, p.y, 0.62), IR_TIMBER_D, root, verts=5)
    for i in range(3):
        a, b = posts[i], posts[i + 1]
        for j, z in enumerate((0.42, 0.56, 0.7, 0.84)):
            off = 0.035 if (i + j) % 2 else -0.035
            n = Vector((a.x + b.x, a.y + b.y, 0)).normalized() * off
            seg((a.x + n.x, a.y + n.y, z), (b.x - n.x, b.y - n.y, z), 0.04, IR_WATTLE, root, verts=5, ext=1.1)
    # javelin rack (back-right)
    c = Vector((math.cos(R(50)) * 1.05, math.sin(R(50)) * 1.05, 0))
    t = Vector((-math.sin(R(50)), math.cos(R(50)), 0))
    for s in (-1, 1):
        p = c + t * 0.28 * s
        cyl(0.04, 0.75, (p.x, p.y, 0.62), IR_TIMBER_D, root, verts=5)
    seg(c - t * 0.32 + Vector((0, 0, 0.92)), c + t * 0.32 + Vector((0, 0, 0.92)), 0.035, IR_TIMBER_D, root, verts=5)
    for k in range(3):
        b = c + t * (-0.2 + 0.2 * k) + Vector((0, 0, 0.3)) + c.normalized() * 0.1
        javelin(root, b, b + Vector((0, 0, 1.05)) - c.normalized() * 0.18)
    # the warrior
    yaw = empty("Yaw", (0, 0, 0.29), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN_P, IR_WOOL, IR_BLUE, HAIR_BLOND, scale=1.25, hair_style="long",
                       belt=IR_LEATHER, leg=IR_BLUE, boot=IR_LEATHER, left_arm=False)
    woad_face(body)
    box((0.26, 0.06, 0.05), (0, -0.215, 1.07), HAIR_BLOND, body)           # drooping mustache
    for s in (-1, 1):
        box((0.05, 0.05, 0.12), (s * 0.12, -0.2, 1.02), HAIR_BLOND, body)
    torus(0.1, 0.025, (0, -0.01, 1.0), IR_BRONZE, body, major=10, minor=4)  # torc
    cape(body, IR_GREEN, lines=IR_BLUE, length=0.8)
    ico(0.06, (-0.2, -0.18, 1.0), IR_BRONZE, body, sub=1)                   # cloak brooch
    # javelin bundle on the back
    for k in range(3):
        javelin(body, (-0.26 + 0.06 * k, 0.36, 0.3), (0.16 + 0.06 * k, 0.36, 1.45))
    seg((-0.22, 0.36, 0.6), (0.02, 0.36, 1.0), 0.06, IR_LEATHER, body, verts=6)
    # left arm thrust forward for aim/balance
    limb(body, IR_WOOL, SKIN_P, (0.42, -0.42, 0.98), start=(0.31, 0, 0.96), elbow=(0.42, -0.2, 0.88))
    # throwing arm: javelin cocked overhead
    limb(arm, IR_WOOL, SKIN_P, (0.02, 0.05, 0.46))
    cuff(arm, IR_BRONZE, (0, 0, 0), (0.02, 0.05, 0.46), 0.7)
    javelin(arm, (0.02, 0.75, 0.52), (0.02, -0.95, 0.45), r=0.03)
    arm.rotation_euler = (R(-22), 0, 0)
    return root


def axe_warrior():
    root = empty("AxeWarrior")
    iron_base(root)
    stakes(root, IR_TIMBER, IR_TIMBER_D, 1.3, 25, 155, 10, h=0.62, z0=0.26)
    for z in (0.5, 0.75):  # binding rails
        pts = arc_pts((0, 0, z), 1.2, 25, 155, 6, u=(1, 0, 0), v=(0, 1, 0))
        chain(root, IR_TIMBER_D, pts, 0.03, verts=4)
    # cooking pot on a tripod (front-right)
    pc = Vector((1.0, -0.55, 0.28))
    for k in range(3):
        a = k * 2.1 + 0.4
        seg(pc + Vector((math.cos(a) * 0.32, math.sin(a) * 0.32, 0)), pc + Vector((0, 0, 0.85)), 0.025,
            IR_TIMBER_D, root, verts=4)
    seg(pc + Vector((0, 0, 0.85)), pc + Vector((0, 0, 0.5)), 0.012, IR_IRON, root, verts=4)
    cyl(0.17, 0.2, tuple(pc + Vector((0, 0, 0.38))), IR_IRON, root, verts=10, r2=0.2)
    cyl(0.17, 0.03, tuple(pc + Vector((0, 0, 0.47))), mat("Ir_Stew", (0.7, 0.45, 0.2), 0.6), root, verts=10)
    cyl(0.12, 0.14, tuple(pc + Vector((0, 0, 0.08))), FIRE, root, verts=6, r2=0.0)
    for k in range(3):
        a = k * 2.1
        seg(pc + Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, 0.03)), pc + Vector((-math.cos(a) * 0.05, -math.sin(a) * 0.05, 0.05)),
            0.035, IR_TIMBER_D, root, verts=5)
    # the warrior
    yaw = empty("Yaw", (0, -0.05, 0.29), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN_P, IR_FUR, IR_GREEN, None, scale=1.3, burly=1.25, beard=HAIR_RED,
                       belt=IR_LEATHER, leg=IR_GREEN, boot=IR_LEATHER, left_arm=False)
    helm_cone(body, IR_IRON, trim=IR_BRONZE)
    ico(0.21, (0, 0.06, 1.12), HAIR_RED, body, sub=1, scale=(1.05, 0.9, 0.8))  # hair under the helm
    box((0.22, 0.12, 0.25), (0, -0.17, 0.92), HAIR_RED, body, bevel=0.04)       # long beard
    for s in (-1, 1):
        chain(body, HAIR_RED, [(s * 0.08, -0.2, 0.85), (s * 0.08, -0.22, 0.66)], 0.04)
        ico(0.04, (s * 0.08, -0.22, 0.64), IR_BRONZE, body, sub=1)
        ico(0.15, (s * 0.25, 0.02, 0.99), IR_FUR_L, body, sub=1, scale=(1.2, 1.1, 0.7))  # fur shoulders
    box((0.1, 0.05, 0.08), (0, -0.3, 0.6), IR_BRONZE, body)  # belt buckle
    # two-handed bearded axe raised overhead
    rh = limb(arm, SKIN_P, SKIN_P, (0.0, -0.22, 0.42))
    cuff(arm, IR_IRON, (0, 0, 0), rh, 0.75, r=0.085)
    lh = limb(arm, SKIN_P, SKIN_P, (0.04, -0.3, 0.22), start=LSH, elbow=(0.45, -0.42, -0.12))
    cuff(arm, IR_IRON, (0.45, -0.42, -0.12), lh, 0.6, r=0.085)
    hb, ht = Vector((0.05, -0.33, 0.05)), Vector((-0.04, -0.15, 1.38))
    seg(hb, ht, 0.045, IR_TIMBER, arm, verts=6)
    hdir = (ht - hb).normalized()
    head = empty("AxeHead", tuple(ht - hdir * 0.2), arm)
    orient(head, hdir, (0.77, -0.64, 0))  # twisted a little so the blade reads from the camera
    blade = [(0.04, 0.12), (-0.1, 0.12), (-0.28, 0.24), (-0.42, 0.22), (-0.45, -0.02), (-0.4, -0.3),
             (-0.28, -0.26), (-0.14, -0.08), (0.04, -0.06)]
    slab(head, IR_IRON, blade, 0.07, plane="yz")
    chain(head, IR_EDGE, [(0, -0.43, 0.23), (0, -0.465, -0.02), (0, -0.41, -0.31)], 0.03, verts=4)
    box((0.08, 0.14, 0.12), (0, 0.1, 0.03), IR_IRON, head)
    arm.rotation_euler = (R(-15), 0, 0)
    return root


def ballista():
    root = empty("Ballista")
    for x, y in ((-1.15, -1.15), (1.15, -1.15), (-1.15, 1.15), (1.15, 1.15), (0, -1.25), (0, 1.25), (-1.25, 0), (1.25, 0)):
        o = ico(0.3, (x, y, 0.02), IR_STONE, root, sub=1, scale=(1.2, 1.2, 0.6))
        jitter(o, 0.04)
    box((2.7, 2.7, 0.16), (0, 0, 0.2), IR_TIMBER, root)
    for s in (-1, 1):
        box((2.8, 0.16, 0.2), (0, s * 1.3, 0.2), IR_TIMBER_D, root)
        box((0.16, 2.8, 0.2), (s * 1.3, 0, 0.2), IR_TIMBER_D, root)
    for i in range(5):
        box((0.03, 2.5, 0.02), (-0.9 + 0.45 * i, 0, 0.285), IR_TIMBER_D, root)
    for p in ((-1.0, 0.95), (-0.75, 1.05)):  # spare bolts
        javelin(root, (p[0], p[1], 0.33), (p[0] + 0.05, p[1] - 1.0, 0.33), r=0.03)
    # turntable
    yaw = empty("Yaw", (0, 0, 0.29), root)
    cyl(0.8, 0.1, (0, 0, 0.05), IR_TIMBER_D, yaw, verts=14)
    torus(0.8, 0.022, (0, 0, 0.1), IR_IRON, yaw, major=20, minor=4)
    box((0.36, 0.36, 0.64), (0, 0.1, 0.42), IR_TIMBER, yaw, bevel=0.03)
    for s in (-1, 1):
        seg((s * 0.5, 0.1, 0.1), (s * 0.12, 0.1, 0.6), 0.05, IR_TIMBER_D, yaw, verts=5)
    arm = empty("Arm", (0, 0.1, 0.8), yaw)
    bw = empty("Bow", (0, 0, 0), arm)
    bw.scale = (1.3, 1.2, 1.25)
    box((0.24, 2.0, 0.16), (0, 0.1, 0), IR_TIMBER, bw, bevel=0.02)          # stock
    for y in (-0.35, 0.4, 0.95):
        box((0.27, 0.06, 0.19), (0, y, 0), IR_IRON, arm)                      # iron bands
    # torsion frame
    fy = -0.7
    for s in (-1, 1):
        cyl(0.11, 0.5, (s * 0.3, fy, 0.05), mat("Ir_Sinew", (0.62, 0.5, 0.34), 0.9), bw, verts=8)
        for z in (-0.22, 0.32):
            cyl(0.13, 0.06, (s * 0.3, fy, z), IR_IRON, bw, verts=8)
        box((0.1, 0.18, 0.62), (s * 0.48, fy, 0.05), IR_TIMBER_D, arm)
        tip = Vector((s * 0.95, -0.3, 0.06))
        seg((s * 0.3, fy, 0.06), tip, 0.05, IR_TIMBER, bw, verts=6)
        ico(0.055, tuple(tip), IR_IRON, bw, sub=1)
        seg(tip, (0, 0.62, 0.1), 0.014, IR_WOOL, bw, verts=4)
    for z in (-0.25, 0.35):
        box((1.08, 0.2, 0.1), (0, fy, z), IR_TIMBER_D, arm)
        box((1.1, 0.04, 0.12), (0, fy - 0.1, z), IR_IRON, arm)
    # the bolt
    javelin(bw, (0, 0.68, 0.11), (0, -1.3, 0.11), r=0.035)
    for k in range(2):
        slab(bw, IR_RED, [(0, 0), (0.18, 0.0), (0.18, 0.08), (0.04, 0.08)], 0.015, loc=(0, 0.48, 0.11),
             plane="yz", rot=(0, R(90 * k), 0))
    # winch at the back
    cyl(0.08, 0.5, (0, 1.0, -0.02), IR_TIMBER_D, bw, verts=8, rot=(0, R(90), 0))
    for s in (-1, 1):
        box((0.05, 0.05, 0.3), (s * 0.27, 1.0, -0.02), IR_IRON, arm)
    arm.rotation_euler = (R(-6), 0, 0)
    # crewman leaning on the winch
    body, carm = figure(yaw, (0.72, 0.85, 0.0), SKIN_P, IR_GREEN, IR_WOOL, HAIR_RED, scale=0.85, beard=HAIR_RED,
                        belt=IR_LEATHER, leg=IR_WOOL, boot=IR_LEATHER)
    carm.name = "CrewArm"
    body.rotation_euler = (R(12), 0, R(25))
    limb(carm, IR_GREEN, SKIN_P, (0.05, -0.38, -0.2))
    return root


def druid():
    root = empty("Druid")
    cyl(1.55, 0.3, (0, 0, 0.03), IR_STONE_D, root, verts=12)
    cyl(1.45, 0.12, (0, 0, 0.22), IR_GRASS, root, verts=12, r2=1.35)
    for k in range(7):
        a = random.uniform(0, 6.28)
        rr = random.uniform(0.6, 1.2)
        ico(0.2, (math.cos(a) * rr, math.sin(a) * rr, 0.27), IR_MOSS, root, sub=1, scale=(1.3, 1.0, 0.35))
    for a, h in ((-25, 0.62), (25, 0.78), (155, 0.75), (205, 0.6), (240, 0.5), (300, 0.5)):
        x, y = math.cos(R(a)) * 1.2, math.sin(R(a)) * 1.2
        o = box((0.3, 0.2, h), (x, y, 0.26 + h / 2), IR_STONE, root, rot=(0, 0, R(a + 90)))
        jitter(o, 0.03)
        ico(0.13, (x, y, 0.27 + h), IR_MOSS, root, sub=1, scale=(1.2, 0.9, 0.45))
    for a in (72, 108):  # trilithon at the back
        x, y = math.cos(R(a)) * 1.22, math.sin(R(a)) * 1.22
        o = box((0.3, 0.24, 1.1), (x, y, 0.81), IR_STONE, root, rot=(0, 0, R(a + 90)))
        jitter(o, 0.025)
    o = box((1.15, 0.28, 0.22), (0, 1.22, 1.45), IR_STONE, root)
    jitter(o, 0.025)
    ico(0.16, (0.25, 1.22, 1.57), IR_MOSS, root, sub=1, scale=(1.5, 1.0, 0.4))
    # the druid
    yaw = empty("Yaw", (0, -0.05, 0.28), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN_P, IR_ROBE, None, None, scale=1.22, robe=IR_ROBE,
                       belt=mat("Ir_GoldRope", (0.95, 0.75, 0.25), 0.5, 0.3))
    hood(body, IR_GREEN, point=0.32)
    cyl(0.41, 0.06, (0, 0, 0.04), IR_GREEN, body, verts=10)        # hem
    box((0.22, 0.1, 0.36), (0, -0.19, 0.9), HAIR_WHITE, body, bevel=0.05)  # long white beard
    ico(0.15, (0, -0.15, 1.04), HAIR_WHITE, body, sub=1, scale=(1.1, 0.7, 1.0))
    box((0.24, 0.05, 0.05), (0, -0.21, 1.08), HAIR_WHITE, body)
    arc_s = arc_pts((0.28, -0.12, 0.62), 0.12, -60, 110, 4, u=(0, -1, 0), v=(0, 0, 1))  # golden sickle at the belt
    chain(body, IR_BRONZE, arc_s, 0.025, verts=4)
    # staff arm, gnarled staff with a claw cradling the Orb
    hnd = limb(arm, IR_ROBE, SKIN_P, (-0.04, -0.3, 0.12))
    cuff(arm, IR_GREEN, (0, 0, 0), hnd, 0.75, r=0.085)
    pts = [(-0.04, -0.3, -0.88), (-0.02, -0.29, -0.45), (-0.07, -0.31, -0.05), (-0.03, -0.3, 0.35),
           (-0.08, -0.32, 0.7), (-0.04, -0.3, 0.88)]
    chain(arm, IR_TIMBER_D, pts, 0.045, verts=6, joints=True)
    for k in range(3):
        a = k * 2.1
        chain(arm, IR_TIMBER_D, [(-0.04, -0.3, 0.86), (-0.04 + math.cos(a) * 0.15, -0.3 + math.sin(a) * 0.15, 1.0),
                                 (-0.04 + math.cos(a) * 0.08, -0.3 + math.sin(a) * 0.08, 1.16)], 0.03, verts=4)
    ico(0.07, (0.03, -0.3, 0.55), IR_MOSS, arm, sub=1, scale=(1, 1, 0.6))  # mistletoe sprig
    orb = empty("Orb", (-0.04, -0.3, 1.04), arm)
    uvs(0.15, (0, 0, 0), IR_GLOW, orb, seg=10, rings=7)
    arm.rotation_euler = (R(-8), 0, 0)
    return root


def brenna():
    root = empty("HeroBrenna")
    yaw = hero_yaw(root, (0.3, 0.55, 0.85), "Brenna")
    body, arm = figure(yaw, (0, 0, 0), SKIN_P, IR_IRON, IR_BLUE, HAIR_RED, scale=1.25, hair_style="braids",
                       belt=IR_LEATHER, leg=IR_BLUE, boot=IR_LEATHER, sleeve=SKIN_P)
    for z in (0.66, 0.8, 0.94):  # scale-armour rows
        k = math.sqrt(max(1 - ((z - 0.8) / 0.2835) ** 2, 0.1))
        o = torus(0.272 * k, 0.022, (0, 0, z), IR_EDGE, body, major=14, minor=4)
        o.scale = (1, 0.78, 1)
    cape(body, IR_BLUE, lines=IR_GREEN, length=0.82)
    cyl(0.235, 0.04, (0, -0.01, 1.3), IR_BRONZE, body, verts=10)  # bronze circlet
    # round painted shield on the left arm
    sh = empty("Shield", (0.44, -0.3, 0.68), body)
    sh.rotation_euler = (0, 0, R(-18))
    cyl(0.42, 0.06, (0, 0, 0), IR_SHIELD, sh, verts=16, rot=(R(90), 0, 0))
    torus(0.42, 0.035, (0, 0, 0), IR_IRON, sh, rot=(R(90), 0, 0), major=16, minor=4)
    pts = []
    for i in range(22):
        t = i / 21
        a = t * 2.3 * 2 * math.pi
        rr = 0.07 + 0.27 * t
        pts.append((math.cos(a) * rr, -0.045, math.sin(a) * rr))
    chain(sh, IR_CREAM, pts, 0.022, verts=4)
    ico(0.08, (0, -0.05, 0), IR_IRON, sh, sub=1, scale=(1, 0.6, 1))
    # spear held forward and up
    hnd = limb(arm, SKIN_P, SKIN_P, (0, -0.24, -0.26))
    cuff(arm, IR_BRONZE, (0, 0, 0), hnd, 0.7)
    seg((0, 0.25, -0.86), (0, -0.62, 1.05), 0.032, IR_TIMBER, arm, verts=5)
    leaf = [(0, 0), (0.07, 0.12), (0, 0.4), (-0.07, 0.12)]
    d = Vector((0, -0.87, 1.91)).normalized()
    tip = Vector((0, -0.62, 1.05))
    slab(arm, IR_EDGE, leaf, 0.03, loc=tuple(tip), plane="xz", rot=(math.atan2(-d.y, d.z), 0, 0))
    arm.rotation_euler = (R(-10), 0, 0)
    return root


def kael():
    root = empty("HeroKael")
    yaw = hero_yaw(root, (0.4, 0.7, 0.3), "Kael")
    body, arm = figure(yaw, (0, 0, 0), SKIN, IR_GREEN, IR_LEATHER, None, scale=1.22, burly=0.92, beard=HAIR_BROWN,
                       belt=IR_LEATHER, leg=IR_LEATHER, boot=IR_LEATHER)
    sash(body, IR_BLUE, tilt=-35)
    # wolf-pelt hood with the head on top
    hood(body, IR_WOLF)
    ico(0.16, (0, 0.03, 1.45), IR_WOLF, body, sub=1, scale=(1.0, 1.35, 0.6))
    ico(0.08, (0, -0.17, 1.43), IR_WOLF, body, sub=1, scale=(1.0, 1.4, 0.75))
    ico(0.035, (0, -0.28, 1.44), EYE, body, sub=1)
    for s in (-1, 1):
        cyl(0.06, 0.14, (s * 0.12, 0.02, 1.55), IR_WOLF, body, verts=4, r2=0.0)
        ico(0.022, (s * 0.07, -0.13, 1.5), mat("Ir_WolfEye", (1.0, 0.75, 0.1), 0.4), body, sub=1)
        box((0.09, 0.14, 0.06), (s * 0.24, -0.16, 0.95), IR_WOLF, body)     # paws over the shoulders
    cape(body, IR_WOLF, length=0.8, collar=False)
    # quiver of javelins on the back
    seg((0.18, 0.34, 0.45), (-0.08, 0.34, 1.05), 0.075, IR_LEATHER, body, verts=6)
    for k in range(3):
        javelin(body, (0.12 - 0.04 * k, 0.36, 0.7), (-0.18 - 0.04 * k, 0.36, 1.45))
    # one javelin raised to throw
    hnd = limb(arm, IR_GREEN, SKIN, (0.02, 0.05, 0.46))
    cuff(arm, IR_LEATHER, (0, 0, 0), hnd, 0.72)
    javelin(arm, (0.02, 0.7, 0.53), (0.02, -0.95, 0.46), r=0.028)
    arm.rotation_euler = (R(-25), 0, 0)
    return root


# ================================================================== CLASSICAL AGE
CL_MARBLE = mat("Cl_Marble", (0.78, 0.74, 0.65), 0.5)
CL_MARBLE_D = mat("Cl_MarbleShade", (0.56, 0.51, 0.43), 0.55)
CL_TERRA = mat("Cl_Terracotta", (0.8, 0.36, 0.18), 0.8)
CL_CRIMSON = mat("Cl_Crimson", (0.74, 0.06, 0.08), 0.8)
CL_BRONZE = mat("Cl_Bronze", (0.88, 0.58, 0.22), 0.3, 0.55)
CL_GOLD = mat("Cl_Gold", (1.0, 0.76, 0.2), 0.3, 0.55)
CL_LAUREL = mat("Cl_Laurel", (0.3, 0.6, 0.2), 0.7)
CL_LINEN = mat("Cl_Linen", (0.96, 0.94, 0.88), 0.85)
CL_STEEL = mat("Cl_Steel", (0.58, 0.6, 0.66), 0.35, 0.5)
CL_LEATHER = mat("Cl_Leather", (0.46, 0.27, 0.12), 0.8)
CL_WOOD = mat("Cl_Wood", (0.56, 0.33, 0.15), 0.85)
CL_WOOD_D = mat("Cl_WoodDark", (0.33, 0.19, 0.09), 0.85)
CL_SMOKE = mat("Cl_Smoke", (0.5, 0.5, 0.54), 1.0)
CL_GLOW = mat("Cl_OracleGlow", (1.0, 0.72, 0.12), 0.3, 0.0, emit=(1.0, 0.6, 0.08), strength=1.0)


def marble_round(root, r=1.5):
    cyl(r + 0.05, 0.2, (0, 0, -0.02), CL_MARBLE_D, root, verts=16)
    cyl(r - 0.12, 0.22, (0, 0, 0.19), CL_MARBLE, root, verts=16)
    cyl(r - 0.1, 0.05, (0, 0, 0.17), CL_TERRA, root, verts=16)


def marble_square(root, s=2.9, pavers=False):
    box((s + 0.1, s + 0.1, 0.22), (0, 0, -0.01), CL_MARBLE_D, root, bevel=0.03)
    box((s - 0.2, s - 0.2, 0.2), (0, 0, 0.2), CL_MARBLE, root, bevel=0.03)
    box((s - 0.17, s - 0.17, 0.05), (0, 0, 0.17), CL_TERRA, root)
    if pavers:
        for i in range(1, 4):
            v = -s / 2 + 0.1 + (s - 0.2) * i / 4
            box((0.03, s - 0.24, 0.015), (v, 0, 0.302), CL_MARBLE_D, root)
            box((s - 0.24, 0.03, 0.015), (0, v, 0.302), CL_MARBLE_D, root)


def laurel_pot(root, loc):
    x, y = loc
    cyl(0.17, 0.32, (x, y, 0.46), CL_TERRA, root, verts=10, r2=0.24)
    torus(0.24, 0.035, (x, y, 0.62), CL_TERRA, root, major=12, minor=4)
    for dx, dy, dz, r in ((0, 0, 0.82, 0.22), (0.12, 0.05, 0.75, 0.15), (-0.1, -0.06, 0.74, 0.15), (0.0, 0.0, 1.0, 0.13)):
        ico(r, (x + dx, y + dy, dz), CL_LAUREL, root, sub=1)


def column(root, loc, h, r=0.14, broken=False):
    x, y, z = loc
    box((r * 2.6, r * 2.6, 0.08), (x, y, z + 0.04), CL_MARBLE, root)
    o = cyl(r, h, (x, y, z + 0.08 + h / 2), CL_MARBLE, root, verts=10)
    if broken:
        for v in o.data.vertices:
            if v.co.z > 0:
                v.co.z += random.uniform(-0.12, 0.05)
    else:
        cyl(r * 1.25, 0.06, (x, y, z + 0.11 + h), CL_MARBLE, root, verts=10, r2=r * 1.5)
        box((r * 3.0, r * 3.0, 0.08), (x, y, z + 0.18 + h), CL_MARBLE, root)


def gladius(parent, base, d=(0, -1, 0), length=0.62):
    """Short sword with the grip starting at base pointing along d."""
    b, d = Vector(base), Vector(d).normalized()
    seg(b - d * 0.1, b + d * 0.08, 0.035, CL_LEATHER, parent, verts=6)
    ico(0.05, tuple(b - d * 0.12), CL_GOLD, parent, sub=1)
    g = b + d * 0.1
    seg(g - d * 0.025, g + d * 0.025, 0.09, CL_GOLD, parent, verts=6)
    e = empty("Blade", tuple(g), parent)
    e.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    slab(e, CL_STEEL, [(-0.06, 0), (0.06, 0), (0.055, length - 0.12), (0, length), (-0.055, length - 0.12)], 0.025)
    return e


def cretan_archer():
    root = empty("CretanArcher")
    marble_round(root)
    column(root, (-0.95, 0.72, 0.3), 0.75, broken=True)
    o = cyl(0.14, 0.32, (-0.45, 1.05, 0.44), CL_MARBLE, root, verts=10, rot=(R(90), 0, R(30)))
    laurel_pot(root, (1.0, 0.72))
    yaw = empty("Yaw", (0, 0, 0.3), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN, CL_LINEN, CL_LINEN, None, scale=1.22, belt=CL_LEATHER,
                       boot=CL_LEATHER, left_arm=False, sleeve=SKIN)
    helm_dome(body, CL_BRONZE, crest=CL_CRIMSON)
    for s in (-1, 1):
        box((0.06, 0.12, 0.18), (s * 0.2, -0.1, 1.12), CL_BRONZE, body)  # cheek guards
    cape(body, CL_CRIMSON, length=0.85)
    ico(0.06, (0.22, -0.17, 1.0), CL_GOLD, body, sub=1)
    seg((0.16, 0.34, 0.5), (-0.06, 0.34, 1.12), 0.075, CL_LEATHER, body, verts=6)  # quiver
    for k in range(3):
        seg((-0.04 - 0.03 * k, 0.34, 1.1), (-0.09 - 0.03 * k, 0.34, 1.32), 0.015, CL_LINEN, body, verts=3)
    # bow arm forward, drawing hand (left) pulled back to the shoulder
    hnd = limb(arm, SKIN, SKIN, (0.0, -0.48, -0.03))
    cuff(arm, CL_LEATHER, (0, 0, 0), hnd, 0.7)
    c = (0, 0.08, -0.03)
    pts = arc_pts(c, 0.56, -62, 62, 10)
    chain(arm, CL_WOOD_D, pts, 0.035, verts=5)
    tips = []
    for p, s in ((pts[0], -1), (pts[-1], 1)):
        t = p + Vector((0, -0.1, s * 0.05))
        chain(arm, CL_WOOD_D, [p, t], 0.03, verts=4)
        ico(0.035, tuple(t), CL_GOLD, arm, sub=1)
        tips.append(t)
    draw = Vector((0.02, -0.03, -0.02))
    for t in tips:
        seg(t, draw, 0.012, CL_LINEN, arm, verts=3)
    seg(draw, (0.0, -0.78, -0.03), 0.014, CL_WOOD, arm, verts=4)
    seg((0.0, -0.78, -0.03), (0.0, -0.9, -0.03), 0.035, CL_BRONZE, arm, verts=4, r2=0.0)
    limb(arm, SKIN, SKIN, (0.03, -0.06, -0.01), start=LSH, elbow=(0.5, -0.32, -0.08))
    arm.rotation_euler = (R(-4), 0, 0)
    return root


def legionary():
    root = empty("Legionary")
    marble_square(root)
    # golden eagle standard (back-left)
    sx, sy = -1.0, 0.95
    seg((sx, sy, 0.3), (sx, sy, 2.45), 0.04, CL_WOOD_D, root, verts=6)
    for z in (1.2, 1.5):
        torus(0.11, 0.03, (sx, sy, z), CL_GOLD, root, major=10, minor=4, rot=(R(90), 0, 0))
    box((0.5, 0.04, 0.04), (sx, sy, 1.95), CL_GOLD, root)
    box((0.42, 0.03, 0.42), (sx, sy - 0.01, 1.72), CL_CRIMSON, root)
    box((0.44, 0.035, 0.05), (sx, sy - 0.01, 1.5), CL_GOLD, root)
    cyl(0.07, 0.08, (sx, sy, 2.48), CL_GOLD, root, verts=8)
    ico(0.1, (sx, sy, 2.6), CL_GOLD, root, sub=1, scale=(0.8, 1.2, 0.9))
    ico(0.06, (sx, sy - 0.13, 2.68), CL_GOLD, root, sub=1)
    cyl(0.025, 0.06, (sx, sy - 0.2, 2.68), CL_GOLD, root, verts=4, r2=0.0, rot=(R(90), 0, 0))
    for s in (-1, 1):
        slab(root, CL_GOLD, [(0, 0), (s * 0.35, 0.18), (s * 0.42, 0.34), (s * 0.24, 0.24), (s * 0.08, 0.1)], 0.03,
             loc=(sx + s * 0.05, sy, 2.58))
    # the legionary
    yaw = empty("Yaw", (0, 0, 0.3), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN, CL_STEEL, CL_CRIMSON, HAIR_BLACK, scale=1.25, burly=1.12,
                       belt=CL_LEATHER, boot=CL_LEATHER, left_arm=True)
    for z in (0.68, 0.8, 0.92):  # lorica bands
        k = math.sqrt(max(1 - ((z - 0.8) / 0.2835) ** 2, 0.1))
        o = torus(0.272 * k, 0.018, (0, 0, z), mat("Cl_SteelDark", (0.38, 0.4, 0.44), 0.4, 0.5), body, major=14, minor=4)
        o.scale = (1, 0.78, 1)
    for s in (-1, 1):
        ico(0.15, (s * 0.26, 0.0, 0.99), CL_STEEL, body, sub=1, scale=(1.1, 1.1, 0.6))
    for x in (-0.15, -0.05, 0.05, 0.15):
        box((0.06, 0.03, 0.2), (x, -0.27, 0.5), CL_LEATHER, body)  # apron straps
    helm_dome(body, CL_STEEL, crest=CL_CRIMSON, trim=CL_BRONZE)
    box((0.42, 0.14, 0.05), (0, 0.2, 1.18), CL_STEEL, body, rot=(R(-20), 0, 0))  # neck guard
    for s in (-1, 1):
        box((0.05, 0.13, 0.2), (s * 0.21, -0.08, 1.1), CL_BRONZE, body)
    cape(body, CL_CRIMSON, length=0.7, collar=False)
    # curved scutum on the left
    sc = empty("Scutum", (0.36, -0.42, 0.64), body)
    sc.rotation_euler = (0, 0, R(-18))
    for i in range(7):
        a = -36 + 12 * i
        x, y = 0.55 * math.sin(R(a)), 0.55 - 0.55 * math.cos(R(a))
        box((0.12, 0.05, 0.96), (x, y, 0), CL_CRIMSON, sc, rot=(0, 0, R(a)))
        for z in (-0.48, 0.48):
            box((0.12, 0.07, 0.04), (x, y, z), CL_GOLD, sc, rot=(0, 0, R(a)))
    for s in (-1, 1):
        a = s * 40
        box((0.04, 0.07, 1.0), (0.55 * math.sin(R(a)), 0.55 - 0.55 * math.cos(R(a)), 0), CL_GOLD, sc, rot=(0, 0, R(a)))
    ico(0.1, (0, -0.05, 0), CL_GOLD, sc, sub=1, scale=(1, 0.6, 1))
    box((0.4, 0.03, 0.035), (0, -0.03, 0.0), CL_GOLD, sc)
    box((0.035, 0.03, 0.8), (0, -0.03, 0.0), CL_GOLD, sc)
    # gladius thrust
    hnd = limb(arm, SKIN, SKIN, (0, -0.32, -0.22))
    cuff(arm, CL_LEATHER, (0, 0, 0), hnd, 0.72)
    gladius(arm, (0, -0.33, -0.22), d=(0, -1, 0.25), length=0.7)
    arm.rotation_euler = (R(-18), 0, 0)
    return root


def onager():
    root = empty("Onager")
    marble_square(root, pavers=True)
    for p in ((1.05, 1.0), (1.2, 0.72), (0.95, 0.75)):
        o = ico(0.18, (p[0], p[1], 0.42), STONE, root, sub=1)
        jitter(o, 0.03)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    for s in (-1, 1):
        box((0.2, 2.1, 0.22), (s * 0.48, 0.05, 0.12), CL_WOOD, yaw, bevel=0.02)
        for y in (-0.95, 1.05):
            box((0.23, 0.12, 0.25), (s * 0.48, y, 0.12), CL_BRONZE, yaw)  # bronze end plates
        # buffer uprights + braces
        box((0.15, 0.15, 0.85), (s * 0.42, -0.6, 0.55), CL_WOOD_D, yaw, bevel=0.02)
        seg((s * 0.42, 0.35, 0.2), (s * 0.42, -0.55, 0.85), 0.06, CL_WOOD_D, yaw, verts=5)
        # torsion skein washers
        cyl(0.22, 0.08, (s * 0.64, 0.45, 0.5), CL_BRONZE, yaw, verts=10, rot=(0, R(90), 0))
        box((0.12, 0.34, 0.06), (s * 0.69, 0.45, 0.5), CL_WOOD_D, yaw)
        box((0.14, 0.14, 0.4), (s * 0.48, 0.45, 0.32), CL_WOOD_D, yaw)
    box((1.15, 0.2, 0.18), (0, -0.98, 0.12), CL_WOOD, yaw)
    box((1.15, 0.2, 0.18), (0, 1.02, 0.12), CL_WOOD, yaw)
    cyl(0.16, 0.95, (0, 0.45, 0.5), ROPE, yaw, verts=10, rot=(0, R(90), 0))
    cyl(0.12, 0.92, (0, -0.6, 1.0), CL_LEATHER, yaw, verts=8, rot=(0, R(90), 0))  # padded buffer
    box((1.0, 0.16, 0.08), (0, -0.6, 0.9), CL_BRONZE, yaw)
    arm = empty("Arm", (0, 0.45, 0.5), yaw)
    seg((0, -0.18, 0), (0, 1.4, 0), 0.1, CL_WOOD, arm, verts=8)
    for y in (0.15, 0.75):
        cyl(0.12, 0.07, (0, y, 0), CL_BRONZE, arm, verts=8, rot=(R(90), 0, 0))
    cyl(0.2, 0.1, (0, 1.42, 0.12), CL_BRONZE, arm, verts=10, r2=0.26)   # sling cup
    o = ico(0.2, (0, 1.42, 0.3), STONE, arm, sub=1)
    jitter(o, 0.025)
    for s in (-1, 1):
        seg((s * 0.18, 1.42, 0.2), (s * 0.05, 1.2, 0.05), 0.015, ROPE, arm, verts=4)
    arm.rotation_euler = (R(-8), 0, 0)
    # crewman
    body, carm = figure(yaw, (0.95, -0.35, -0.02), SKIN, CL_LINEN, CL_CRIMSON, HAIR_BLACK, scale=0.85,
                        belt=CL_LEATHER, boot=CL_LEATHER)
    carm.name = "CrewArm"
    helm_dome(body, CL_BRONZE, nose=False)
    limb(carm, SKIN, SKIN, (0.05, -0.2, 0.42))
    seg((0.05, -0.2, -0.85), (0.05, -0.2, 0.75), 0.03, CL_WOOD_D, carm, verts=5)  # crowbar/lever
    return root


def oracle():
    root = empty("Oracle")
    marble_round(root)
    for a in (55, 90, 125):
        column(root, (math.cos(R(a)) * 1.12, math.sin(R(a)) * 1.12, 0.3), 1.15, r=0.13)
    # tripod brazier with smoke
    tx, ty = 0.55, -0.55
    for k in range(3):
        a = k * 2.094 + 0.5
        seg((tx + math.cos(a) * 0.32, ty + math.sin(a) * 0.32, 0.3), (tx + math.cos(a) * 0.16, ty + math.sin(a) * 0.16, 0.9),
            0.03, CL_BRONZE, root, verts=5)
    cyl(0.26, 0.16, (tx, ty, 0.95), CL_BRONZE, root, verts=12, r2=0.32)
    torus(0.32, 0.03, (tx, ty, 1.03), CL_GOLD, root, major=14, minor=4)
    cyl(0.25, 0.08, (tx, ty, 1.03), FIRE, root, verts=8, r2=0.1)
    for dz, dx, rr in ((1.15, 0.0, 0.13), (1.3, 0.1, 0.11), (1.45, -0.04, 0.09)):
        ico(rr, (tx + dx - 0.18, ty + 0.05, dz), CL_SMOKE, root, sub=1)
    orb = empty("Orb", (tx, ty, 1.55), root)
    uvs(0.17, (0, 0, 0), CL_GLOW, orb, seg=12, rings=8)
    torus(0.26, 0.02, (0, 0, 0), CL_GOLD, orb, rot=(R(70), 0, 0), major=16, minor=4)
    # the priestess
    yaw = empty("Yaw", (-0.35, 0.22, 0.3), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN, CL_LINEN, None, HAIR_BLACK, scale=1.2, robe=CL_LINEN, belt=CL_GOLD,
                       hair_style="long")
    cyl(0.41, 0.07, (0, 0, 0.05), CL_GOLD, body, verts=10)                      # gold hem
    cyl(0.235, 0.05, (0, 0, 1.28), CL_GOLD, body, verts=10)                     # diadem
    ico(0.05, (0, -0.22, 1.3), CL_CRIMSON, body, sub=1)
    sash(body, CL_GOLD, tilt=30, R0=0.27, r=0.03)
    cape(body, CL_LINEN, length=0.95, y=0.24, collar=False)
    # laurel branch raised over the tripod
    hnd = limb(arm, CL_LINEN, SKIN, (0.02, -0.3, 0.25))
    cuff(arm, CL_GOLD, (0, 0, 0), hnd, 0.8)
    base = Vector((0.02, -0.3, 0.2))
    top = Vector((0.0, -0.42, 0.85))
    seg(base, top, 0.02, CL_WOOD_D, arm, verts=4)
    for i in range(7):
        p = base + (top - base) * (0.25 + 0.11 * i)
        s = 1 if i % 2 else -1
        o = ico(0.06, tuple(p + Vector((s * 0.06, 0, 0))), CL_LAUREL, arm, sub=1, scale=(1.4, 0.5, 0.6))
        o.rotation_euler = (0, R(s * 30), 0)
    arm.rotation_euler = (R(-8), 0, 0)
    return root


def cassia():
    root = empty("HeroCassia")
    yaw = hero_yaw(root, (0.8, 0.15, 0.15), "Cassia")
    body, arm = figure(yaw, (0, 0, 0), SKIN_T, CL_GOLD, CL_CRIMSON, HAIR_BLACK, scale=1.25, burly=1.05,
                       belt=CL_LEATHER, boot=CL_LEATHER, hair_style="pony")
    for s in (-1, 1):
        ico(0.1, (s * 0.1, -0.16, 0.9), CL_GOLD, body, sub=1, scale=(1.1, 0.5, 0.75))   # sculpted cuirass
        for k in range(3):
            box((0.06, 0.03, 0.16), (s * (0.08 + 0.09 * k), -0.18 + 0.03 * k, 0.48), CL_CRIMSON, body)
    helm_dome(body, CL_STEEL, crest=CL_CRIMSON, trim=CL_GOLD, transverse=True)
    cape(body, CL_CRIMSON, length=0.85)
    ico(0.06, (-0.2, -0.17, 1.0), CL_GOLD, body, sub=1)
    # round shield
    sh = empty("Shield", (0.45, -0.3, 0.68), body)
    sh.rotation_euler = (0, 0, R(-18))
    cyl(0.38, 0.06, (0, 0, 0), CL_CRIMSON, sh, verts=16, rot=(R(90), 0, 0))
    torus(0.38, 0.035, (0, 0, 0), CL_GOLD, sh, rot=(R(90), 0, 0), major=16, minor=4)
    torus(0.2, 0.02, (0, -0.035, 0), CL_GOLD, sh, rot=(R(90), 0, 0), major=12, minor=3)
    ico(0.08, (0, -0.05, 0), CL_GOLD, sh, sub=1, scale=(1, 0.6, 1))
    # gladius raised high
    hnd = limb(arm, SKIN_T, SKIN_T, (0, -0.02, 0.46))
    cuff(arm, CL_GOLD, (0, 0, 0), hnd, 0.72)
    gladius(arm, (0, -0.02, 0.5), d=(0, -0.25, 1), length=0.72)
    arm.rotation_euler = (R(-30), 0, 0)
    return root


def theron():
    root = empty("HeroTheron")
    yaw = hero_yaw(root, (0.95, 0.85, 0.4), "Theron")
    body, arm = figure(yaw, (0, 0, 0), SKIN, CL_LINEN, None, None, scale=1.22, robe=CL_LINEN, beard=HAIR_WHITE)
    cyl(0.41, 0.07, (0, 0, 0.05), CL_GOLD, body, verts=10)
    sash(body, CL_GOLD, tilt=-32, R0=0.27, r=0.035)
    o = slab(body, CL_LINEN, [(-0.2, 0), (0.2, 0), (0.25, 0.4), (-0.15, 0.6)], 0.06, loc=(0.05, -0.2, 0.3))
    box((0.22, 0.1, 0.35), (0, -0.19, 0.9), HAIR_WHITE, body, bevel=0.05)
    ico(0.2, (0, 0.06, 1.12), HAIR_WHITE, body, sub=1, scale=(1.08, 0.8, 0.75))  # hair at the back
    box((0.24, 0.05, 0.05), (0, -0.21, 1.08), HAIR_WHITE, body)
    for s in (-1, 1):
        box((0.1, 0.03, 0.03), (s * 0.08, -0.2, 1.26), HAIR_WHITE, body)  # bushy brows
    torus(0.21, 0.03, (0, 0.0, 1.26), CL_LAUREL, body, major=14, minor=4)
    for k in range(10):
        a = k * 0.55 + 1.9 - 3.14
        if -2.5 < a < -0.6:
            continue
        o = ico(0.05, (math.cos(a) * 0.22, math.sin(a) * 0.22, 1.28), CL_LAUREL, body, sub=1, scale=(1.5, 0.6, 0.7))
        o.rotation_euler = (0, R(20), a)
    # glowing gold staff
    hnd = limb(arm, CL_LINEN, SKIN, (-0.02, -0.3, 0.12))
    cuff(arm, CL_GOLD, (0, 0, 0), hnd, 0.78)
    seg((-0.02, -0.3, -0.88), (-0.02, -0.3, 0.92), 0.04, CL_GOLD, arm, verts=6)
    orb = empty("Orb", (-0.02, -0.3, 1.06), arm)
    uvs(0.13, (0, 0, 0), CL_GLOW, orb, seg=10, rings=7)
    torus(0.15, 0.025, (0, 0, -0.04), CL_GOLD, orb, major=12, minor=4)
    for k in range(4):
        a = k * math.pi / 2
        seg((math.cos(a) * 0.15, math.sin(a) * 0.15, -0.04), (math.cos(a) * 0.08, math.sin(a) * 0.08, 0.15), 0.02, CL_GOLD, orb,
            verts=4)
    arm.rotation_euler = (R(-8), 0, 0)
    return root


# ================================================================== MEDIEVAL AGE
MD_STONE = mat("Md_Stone", (0.5, 0.5, 0.51), 0.85)
MD_STONE_D = mat("Md_StoneDark", (0.34, 0.34, 0.37), 0.85)
MD_BLUE = mat("Md_HeraldBlue", (0.08, 0.2, 0.75), 0.75)
MD_GOLD = mat("Md_Gold", (1.0, 0.78, 0.18), 0.3, 0.5)
MD_YELLOW = mat("Md_Yellow", (1.0, 0.8, 0.15), 0.7)
MD_MAIL = mat("Md_Mail", (0.4, 0.42, 0.46), 0.55, 0.5)
MD_STEEL = mat("Md_Steel", (0.5, 0.54, 0.62), 0.3, 0.5)
MD_WOOD = mat("Md_Wood", (0.52, 0.31, 0.14), 0.85)
MD_WOOD_D = mat("Md_WoodDark", (0.3, 0.18, 0.09), 0.85)
MD_RED = mat("Md_Red", (0.78, 0.08, 0.08), 0.8)
MD_PURPLE = mat("Md_Purple", (0.42, 0.14, 0.62), 0.8)
MD_LEATHER = mat("Md_Leather", (0.45, 0.27, 0.13), 0.8)
MD_GREEN = mat("Md_Green", (0.16, 0.48, 0.18), 0.85)
MD_GREEN_D = mat("Md_GreenDark", (0.1, 0.3, 0.12), 0.85)
MD_HOSE = mat("Md_Hose", (0.35, 0.22, 0.14), 0.85)
MD_IRON = mat("Md_Iron", (0.2, 0.2, 0.22), 0.45, 0.5)
MD_GLOW = mat("Md_FlaskGlow", (0.3, 1.0, 0.15), 0.2, 0.0, emit=(0.25, 0.95, 0.1), strength=1.0)
MD_GLASS = mat("Md_Glass", (0.75, 0.9, 0.9), 0.15)


def cobble_dais(root, r=1.5):
    cyl(r + 0.05, 0.3, (0, 0, 0.03), MD_STONE_D, root, verts=14)
    cyl(r - 0.1, 0.06, (0, 0, 0.2), MD_STONE, root, verts=14)
    for k in range(16):
        a = k * 2 * math.pi / 16 + random.uniform(-0.1, 0.1)
        rr = r - 0.32 if k % 2 else r - 0.62
        o = cyl(0.17, 0.06, (math.cos(a) * rr, math.sin(a) * rr, 0.24), MD_STONE_D, root, verts=6)
        o.rotation_euler = (0, 0, random.uniform(0, 1))
        jitter(o, 0.015)


def surcoat_lion(body, loc=(0, -0.205, 0.8), s=1.0):
    pts = [(-0.05, -0.14), (-0.02, -0.02), (-0.09, 0.04), (-0.06, 0.1), (-0.01, 0.07), (0.02, 0.15), (0.07, 0.12),
           (0.05, 0.06), (0.09, 0.02), (0.05, -0.04), (0.07, -0.14), (0.02, -0.09)]
    slab(body, MD_GOLD, [(x * s * 1.3, z * s * 1.3) for x, z in pts], 0.03, loc=loc)


def crossbowman():
    root = empty("Crossbowman")
    lp.stone_base(root, MD_STONE, MD_STONE_D)
    cyl(1.08, 0.66, (0, 0, 0.55), MD_STONE, root, verts=12)
    cyl(1.12, 0.08, (0, 0, 0.88), MD_STONE_D, root, verts=12)
    cyl(0.98, 0.04, (0, 0, 0.91), MD_WOOD, root, verts=12)
    for k in range(12):
        a = k * math.pi / 6 + math.pi / 12
        if 225 < math.degrees(a) < 315:
            continue
        box((0.26, 0.2, 0.26), (math.cos(a) * 1.0, math.sin(a) * 1.0, 1.05), MD_STONE, root, rot=(0, 0, a + math.pi / 2))
    for k in range(9):
        a = random.uniform(0, 6.28)
        z = random.uniform(0.35, 0.75)
        box((0.24, 0.06, 0.1), (math.cos(a) * 1.08, math.sin(a) * 1.08, z), MD_STONE_D, root, rot=(0, 0, a + math.pi / 2))
    box((0.08, 0.1, 0.3), (0, -1.06, 0.55), mat("Md_Slit", (0.05, 0.05, 0.06), 0.9), root)  # arrow slit
    # pennant pole at the back
    seg((0.75, 0.6, 0.9), (0.75, 0.6, 2.1), 0.03, MD_WOOD_D, root, verts=5)
    slab(root, MD_BLUE, [(0, 0), (0.55, -0.1), (0, -0.25)], 0.02, loc=(0.75, 0.6, 2.05), plane="yz")
    yaw = empty("Yaw", (0, 0, 0.93), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN, MD_BLUE, MD_BLUE, None, scale=1.15, belt=MD_LEATHER, sleeve=MD_MAIL,
                       leg=MD_HOSE, boot=MD_LEATHER, left_arm=False, beard=HAIR_BROWN)
    box((0.12, 0.04, 0.5), (0, -0.21, 0.75), MD_YELLOW, body)        # tabard stripe
    box((0.12, 0.04, 0.34), (0, -0.3, 0.38), MD_YELLOW, body, rot=(R(-12), 0, 0))
    cyl(0.29, 0.2, (0, 0.02, 1.03), MD_MAIL, body, verts=10, r2=0.23)  # mail collar
    ico(0.21, (0, 0.03, 1.2), MD_MAIL, body, sub=1, scale=(1.08, 1.0, 0.95))  # coif
    ico(0.21, (0, 0, 1.31), MD_STEEL, body, sub=2, scale=(1.08, 1.08, 0.78))  # kettle hat
    cyl(0.42, 0.08, (0, 0, 1.3), MD_STEEL, body, verts=14, r2=0.27)
    # pavise
    pv = empty("Pavise", (0.75, -0.42, 0.0), yaw)
    pv.rotation_euler = (R(-8), 0, R(-20))
    box((0.62, 0.08, 1.0), (0, 0, 0.52), MD_BLUE, pv, bevel=0.03)
    box((0.14, 0.09, 1.0), (0, -0.01, 0.52), MD_YELLOW, pv)
    box((0.62, 0.09, 0.08), (0, -0.01, 0.75), MD_YELLOW, pv)
    seg((0, 0.05, 0.75), (0, 0.45, 0.0), 0.03, MD_WOOD_D, pv, verts=4)
    # crossbow at the shoulder
    x = 0.17
    hnd = limb(arm, MD_MAIL, SKIN, (x, -0.2, -0.05))
    box((0.07, 0.95, 0.09), (x, -0.4, 0.02), MD_WOOD, arm, bevel=0.01)
    box((0.08, 0.22, 0.16), (x, 0.0, -0.02), MD_WOOD, arm, bevel=0.02)
    pts = arc_pts((x, -0.48, 0.07), 0.38, -65, 65, 8, u=(0, -1, 0), v=(1, 0, 0))
    chain(arm, MD_STEEL, pts, 0.03, verts=4)
    for t in (pts[0], pts[-1]):
        seg(t, (x, -0.3, 0.08), 0.01, MD_HOSE, arm, verts=3)
    torus(0.07, 0.015, (x, -0.92, 0.0), MD_STEEL, arm, rot=(0, R(90), 0), major=8, minor=3)
    seg((x, -0.3, 0.1), (x, -0.86, 0.1), 0.018, MD_WOOD_D, arm, verts=4)
    seg((x, -0.86, 0.1), (x, -0.95, 0.1), 0.035, MD_STEEL, arm, verts=4, r2=0.0)
    limb(arm, MD_MAIL, SKIN, (x + 0.02, -0.55, -0.04), start=LSH, elbow=(0.55, -0.3, -0.3))
    arm.rotation_euler = (R(-3), 0, 0)
    return root


def knight():
    root = empty("Knight")
    cobble_dais(root)
    seg((1.0, 0.85, 0.25), (1.0, 0.85, 2.3), 0.035, MD_WOOD_D, root, verts=6)
    ico(0.07, (1.0, 0.85, 2.33), MD_GOLD, root, sub=1)
    box((0.04, 0.6, 0.04), (1.0, 0.6, 2.2), MD_WOOD_D, root)
    slab(root, MD_RED, [(0, 0), (-0.55, 0), (-0.55, -0.85), (-0.28, -0.65), (0, -0.85)], 0.025,
         loc=(1.0, 0.85, 2.2), plane="yz")
    yaw = empty("Yaw", (0, 0, 0.28), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN, MD_BLUE, MD_BLUE, None, scale=1.3, burly=1.15, belt=MD_LEATHER,
                       sleeve=MD_STEEL, leg=MD_STEEL, boot=MD_STEEL, left_arm=False, face=False)
    surcoat_lion(body)
    for s in (-1, 1):
        ico(0.16, (s * 0.26, 0.0, 1.0), MD_STEEL, body, sub=1, scale=(1.15, 1.1, 0.65))  # pauldrons
        ico(0.07, (s * 0.13, -0.06, 0.29), MD_STEEL, body, sub=1)  # knee cops
    # great helm
    cyl(0.25, 0.44, (0, -0.01, 1.19), MD_STEEL, body, verts=10, rot=(0, 0, R(18)))
    cyl(0.25, 0.07, (0, -0.01, 1.445), MD_STEEL, body, verts=10, r2=0.17, rot=(0, 0, R(18)))
    box((0.34, 0.04, 0.045), (0, -0.25, 1.24), mat("Md_Slit", (0.05, 0.05, 0.06), 0.9), body)
    box((0.05, 0.04, 0.3), (0, -0.252, 1.12), MD_GOLD, body)
    torus(0.25, 0.02, (0, -0.01, 1.41), MD_GOLD, body, major=10, minor=3)
    # two-handed longsword raised to the right
    h1 = limb(arm, MD_STEEL, MD_STEEL, (0.06, -0.24, 0.38))
    h2 = limb(arm, MD_STEEL, MD_STEEL, (0.07, -0.25, 0.24), start=LSH, elbow=(0.5, -0.36, -0.18))
    gx, gy = 0.065, -0.245
    seg((gx, gy, 0.12), (gx, gy, 0.5), 0.035, MD_LEATHER, arm, verts=6)
    ico(0.055, (gx, gy, 0.1), MD_GOLD, arm, sub=1)
    box((0.42, 0.06, 0.06), (gx, gy, 0.52), MD_GOLD, arm)
    slab(arm, MD_STEEL, [(-0.06, 0), (0.06, 0), (0.05, 1.0), (0, 1.15), (-0.05, 1.0)], 0.03, loc=(gx, gy, 0.54))
    arm.rotation_euler = (R(-25), 0, 0)
    return root


def trebuchet():
    root = empty("Trebuchet")
    cyl(1.55, 0.26, (0, 0, 0.01), MD_STONE_D, root, verts=10)
    box((2.3, 2.3, 0.14), (0, 0, 0.21), MD_WOOD, root)
    for i in range(5):
        box((0.03, 2.25, 0.02), (-0.92 + 0.46 * i, 0, 0.285), MD_WOOD_D, root)
    for p, r in (((-1.05, -0.75, 0.42), 0.17), ((-0.85, -0.95, 0.4), 0.15), ((-0.98, -0.88, 0.62), 0.14)):
        o = ico(r, p, STONE, root, sub=1)
        jitter(o, 0.03)
    yaw = empty("Yaw", (0, 0, 0.29), root)
    for s in (-1, 1):
        x = s * 0.48
        box((0.18, 2.0, 0.18), (x, 0, 0.09), MD_WOOD_D, yaw, bevel=0.02)
        for y in (-0.8, 0.8):
            seg((x, y, 0.1), (x, 0, 1.95), 0.075, MD_WOOD, yaw, verts=6)
        box((0.14, 1.0, 0.12), (x, 0, 0.85), MD_WOOD, yaw)
        cyl(0.12, 0.08, (s * 0.6, 0, 1.95), MD_IRON, yaw, verts=8, rot=(0, R(90), 0))
    box((1.1, 0.16, 0.16), (0, 0.9, 0.09), MD_WOOD_D, yaw)
    box((1.1, 0.16, 0.16), (0, -0.9, 0.09), MD_WOOD_D, yaw)
    cyl(0.07, 1.25, (0, 0, 1.95), MD_IRON, yaw, verts=8, rot=(0, R(90), 0))
    # winch at the back
    cyl(0.1, 0.9, (0, 0.75, 0.32), MD_WOOD, yaw, verts=8, rot=(0, R(90), 0))
    arm = empty("Arm", (0, 0, 1.95), yaw)
    A = 26  # rest angle of the cocked arm
    box((0.22, 2.45, 0.24), (0, 0.65, 0), MD_WOOD, arm, bevel=0.02)
    for y in (-0.3, 0.3, 1.2):
        box((0.25, 0.06, 0.27), (0, y, 0), MD_IRON, arm)
    hinge = empty("Hinge", (0, -0.5, 0), arm)
    hinge.rotation_euler = (R(A), 0, 0)
    for s in (-1, 1):
        seg((s * 0.12, 0, 0), (s * 0.25, 0, -0.3), 0.03, MD_IRON, hinge, verts=4)
    box((0.72, 0.5, 0.55), (0, 0, -0.55), MD_WOOD_D, hinge, bevel=0.03)
    for z in (-0.36, -0.74):
        box((0.75, 0.53, 0.06), (0, 0, z), MD_IRON, hinge)
    # sling from the long tip, hanging down to the deck
    tip = Vector((0, 1.85, 0))
    dn = Vector((0, math.sin(R(A)), -math.cos(R(A))))
    pouch = tip + dn * 0.95
    seg(tip, pouch + Vector((0, 0.08, 0)), 0.016, ROPE, arm, verts=4)
    seg(tip, pouch - Vector((0, 0.18, 0)), 0.016, ROPE, arm, verts=4)
    ico(0.15, tuple(pouch - Vector((0, 0.05, 0.02))), MD_LEATHER, arm, sub=1, scale=(1.3, 1.3, 0.6))
    o = ico(0.17, tuple(pouch - Vector((0, 0.05, -0.08))), STONE, arm, sub=1)
    jitter(o, 0.02)
    arm.rotation_euler = (R(-A), 0, 0)
    # small banner on the frame
    slab(yaw, MD_RED, [(0, 0), (0, -0.4), (0.35, -0.2)], 0.02, loc=(0.6, -0.35, 1.6), plane="yz", rot=(0, 0, R(90)))
    return root


def alchemist():
    root = empty("Alchemist")
    box((2.95, 2.95, 0.3), (0, 0, 0.03), MD_STONE_D, root, bevel=0.03)
    for i in range(4):
        for j in range(4):
            box((0.66, 0.66, 0.06), (-1.05 + 0.7 * i, -1.05 + 0.7 * j, 0.21), MD_STONE if (i + j) % 2 else
                mat("Md_StoneMid", (0.52, 0.52, 0.53), 0.85), root)
    # workbench with a shelf of bottles (back)
    bx, by = 0.15, 0.9
    box((1.5, 0.55, 0.08), (bx, by, 0.85), MD_WOOD, root)
    for sx in (-0.65, 0.65):
        for sy in (-0.2, 0.2):
            box((0.08, 0.08, 0.6), (bx + sx, by + sy, 0.53), MD_WOOD_D, root)
        box((0.07, 0.25, 0.8), (bx + sx, by + 0.15, 1.3), MD_WOOD_D, root)
    box((1.5, 0.25, 0.05), (bx, by + 0.15, 1.45), MD_WOOD, root)
    box((1.5, 0.25, 0.05), (bx, by + 0.15, 1.72), MD_WOOD, root)
    cols = [(0.9, 0.15, 0.15), (0.2, 0.45, 1.0), (1.0, 0.8, 0.1), (0.6, 0.2, 0.9), (0.2, 0.9, 0.4), (1.0, 0.45, 0.1)]
    for k, c in enumerate(cols):
        m = mat(f"Md_Potion{k}", c, 0.3)
        z = 1.48 if k < 3 else 1.75
        x = bx - 0.45 + 0.42 * (k % 3) + random.uniform(-0.05, 0.05)
        cyl(0.07, 0.16, (x, by + 0.15, z + 0.08), m, root, verts=6)
        cyl(0.025, 0.08, (x, by + 0.15, z + 0.2), MD_GLASS, root, verts=4)
    for k, c in enumerate(cols[:3]):  # on the bench top
        ico(0.08, (bx - 0.5 + 0.35 * k, by - 0.1, 0.96), mat(f"Md_Potion{k + 3}", cols[k + 3], 0.3), root, sub=1)
        cyl(0.02, 0.1, (bx - 0.5 + 0.35 * k, by - 0.1, 1.07), MD_GLASS, root, verts=4)
    box((0.3, 0.22, 0.06), (bx + 0.45, by - 0.1, 0.92), mat("Md_Book", (0.55, 0.12, 0.12), 0.8), root)
    # cauldron (front-right)
    cx, cy = 0.95, -0.7
    for k in range(3):
        a = k * 2.1
        cyl(0.04, 0.2, (cx + math.cos(a) * 0.22, cy + math.sin(a) * 0.22, 0.33), MD_IRON, root, verts=4)
    ico(0.32, (cx, cy, 0.6), MD_IRON, root, sub=2, scale=(1, 1, 0.8))
    torus(0.27, 0.04, (cx, cy, 0.8), MD_IRON, root, major=14, minor=4)
    cyl(0.26, 0.03, (cx, cy, 0.8), MD_GLOW, root, verts=12)
    for dx, dy, r in ((0.08, 0.05, 0.06), (-0.1, -0.04, 0.05), (0.0, -0.12, 0.04)):
        ico(r, (cx + dx, cy + dy, 0.84), MD_GLOW, root, sub=1)
    cyl(0.18, 0.14, (cx, cy, 0.31), FIRE, root, verts=6, r2=0.0)
    # the alchemist
    yaw = empty("Yaw", (-0.3, -0.1, 0.24), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN, MD_PURPLE, None, None, scale=1.22, robe=MD_PURPLE, beard=HAIR_GREY,
                       belt=MD_GOLD)
    hood(body, MD_PURPLE, point=0.55, tilt=-18)
    cyl(0.41, 0.06, (0, 0, 0.05), MD_GOLD, body, verts=10)
    box((0.2, 0.1, 0.28), (0, -0.19, 0.92), HAIR_GREY, body, bevel=0.05)
    for p in ((0.15, -0.3, 0.45), (-0.2, -0.28, 0.25), (0.12, 0.3, 0.6)):
        slab(body, MD_GOLD, [(0, 0.05), (0.015, 0.015), (0.05, 0), (0.015, -0.015), (0, -0.05), (-0.015, -0.015),
                             (-0.05, 0), (-0.015, 0.015)], 0.02, loc=p)  # little stars on the robe
    box((0.12, 0.08, 0.14), (0.28, -0.12, 0.55), MD_LEATHER, body)  # belt pouch
    hnd = limb(arm, MD_PURPLE, SKIN, (0.0, -0.22, 0.36))
    cuff(arm, MD_GOLD, (0, 0, 0), hnd, 0.75, r=0.085)
    orb = empty("Orb", (0.0, -0.24, 0.52), arm)
    uvs(0.14, (0, 0, 0), MD_GLOW, orb, seg=10, rings=7)
    cyl(0.04, 0.16, (0, 0, 0.17), MD_GLASS, orb, verts=6)
    cyl(0.045, 0.05, (0, 0, 0.27), MD_WOOD, orb, verts=6)
    for dx, dz, r in ((0.05, 0.32, 0.03), (-0.03, 0.4, 0.025), (0.02, 0.47, 0.02)):
        ico(r, (dx, 0, dz), MD_GLOW, orb, sub=1)
    arm.rotation_euler = (R(-12), 0, 0)
    return root


def aldric():
    root = empty("HeroAldric")
    yaw = hero_yaw(root, (0.25, 0.4, 0.85), "Aldric")
    body, arm = figure(yaw, (0, 0, 0), SKIN, MD_BLUE, MD_BLUE, None, scale=1.25, burly=1.1, belt=MD_LEATHER,
                       sleeve=MD_STEEL, leg=MD_STEEL, boot=MD_STEEL, beard=HAIR_BROWN)
    box((0.12, 0.04, 0.5), (0, -0.21, 0.75), MD_YELLOW, body)
    for s in (-1, 1):
        ico(0.16, (s * 0.26, 0.0, 1.0), MD_STEEL, body, sub=1, scale=(1.15, 1.1, 0.65))
    # bascinet with mail aventail
    cyl(0.3, 0.16, (0, 0.02, 1.0), MD_MAIL, body, verts=10, r2=0.24)
    cyl(0.235, 0.16, (0, 0.02, 1.28), MD_STEEL, body, verts=10)
    cyl(0.235, 0.32, (0, 0.04, 1.51), MD_STEEL, body, verts=10, r2=0.03)
    box((0.14, 0.06, 0.05), (0, -0.21, 1.37), MD_GOLD, body)
    # kite shield
    sh = empty("Shield", (0.45, -0.3, 0.66), body)
    sh.rotation_euler = (0, 0, R(-18))
    kite = [(0, -0.5), (0.26, 0.0), (0.26, 0.28), (0, 0.34), (-0.26, 0.28), (-0.26, 0.0)]
    slab(sh, MD_GOLD, [(x * 1.12, z * 1.08) for x, z in kite], 0.05, loc=(0, 0.01, 0))
    slab(sh, MD_BLUE, kite, 0.06, loc=(0, -0.01, 0))
    slab(sh, MD_GOLD, [(-0.18, 0.08), (0, -0.12), (0.18, 0.08), (0.18, 0.18), (0, -0.02), (-0.18, 0.18)], 0.07,
         loc=(0, -0.012, 0))
    # longsword raised
    hnd = limb(arm, MD_STEEL, MD_STEEL, (0, -0.02, 0.46))
    seg((0, -0.03, 0.36), (0, -0.03, 0.58), 0.03, MD_LEATHER, arm, verts=6)
    ico(0.05, (0, -0.03, 0.34), MD_GOLD, arm, sub=1)
    box((0.36, 0.06, 0.06), (0, -0.03, 0.6), MD_GOLD, arm)
    slab(arm, MD_STEEL, [(-0.055, 0), (0.055, 0), (0.045, 0.85), (0, 0.98), (-0.045, 0.85)], 0.03, loc=(0, -0.03, 0.62))
    arm.rotation_euler = (R(-30), 0, 0)
    return root


def wren():
    root = empty("HeroWren")
    yaw = hero_yaw(root, (0.3, 0.6, 0.25), "Wren")
    body, arm = figure(yaw, (0, 0, 0), SKIN, MD_LEATHER, MD_GREEN_D, HAIR_RED, scale=1.22, burly=0.95,
                       belt=MD_LEATHER, leg=MD_GREEN_D, boot=MD_LEATHER, left_arm=False, hair_style="long",
                       sleeve=MD_GREEN)
    hood(body, MD_GREEN, point=0.28, tilt=-60)
    cape(body, MD_GREEN, length=1.0, y=0.26, collar=False)
    slab(body, MD_YELLOW, [(0, 0), (0.05, 0.12), (0.03, 0.35), (-0.02, 0.4), (-0.03, 0.2)], 0.02,
         loc=(0.22, 0.15, 1.3), plane="yz", rot=(0, R(10), 0))
    slab(body, mat("Md_Feather", (0.95, 0.95, 0.9), 0.7), [(0, 0), (0.06, 0.12), (0.05, 0.42), (-0.01, 0.5), (-0.03, 0.22)],
         0.02, loc=(0.24, 0.18, 1.32), plane="yz", rot=(R(-25), R(15), 0))
    seg((0.18, 0.36, 0.5), (-0.06, 0.36, 1.1), 0.075, MD_LEATHER, body, verts=6)  # quiver
    for k in range(3):
        seg((-0.04 - 0.03 * k, 0.36, 1.08), (-0.09 - 0.03 * k, 0.36, 1.3), 0.015, MD_WOOD, body, verts=3)
        box((0.05, 0.015, 0.08), (-0.09 - 0.03 * k, 0.36, 1.3), MD_RED, body)
    # tall longbow
    hnd = limb(arm, MD_GREEN, SKIN, (0.0, -0.48, -0.03))
    cuff(arm, MD_LEATHER, (0, 0, 0), hnd, 0.75)
    pts = arc_pts((0, 0.4, -0.03), 0.88, -55, 55, 12)
    chain(arm, MD_WOOD_D, pts, 0.035, verts=5)
    draw = Vector((0.02, -0.05, -0.02))
    for t in (pts[0], pts[-1]):
        seg(t, draw, 0.012, mat("Md_String", (0.95, 0.92, 0.8), 0.8), arm, verts=3)
    seg(draw, (0.0, -0.8, -0.03), 0.014, MD_WOOD, arm, verts=4)
    seg((0.0, -0.8, -0.03), (0.0, -0.92, -0.03), 0.035, MD_STEEL, arm, verts=4, r2=0.0)
    limb(arm, MD_GREEN, SKIN, (0.03, -0.08, -0.01), start=LSH, elbow=(0.5, -0.32, -0.08))
    arm.rotation_euler = (R(-4), 0, 0)
    return root


# ================================================================== GUNPOWDER AGE
GP_NAVY = mat("Gp_Navy", (0.08, 0.14, 0.42), 0.75)
GP_RED = mat("Gp_Red", (0.82, 0.1, 0.1), 0.75)
GP_WHITE = mat("Gp_White", (0.95, 0.95, 0.92), 0.8)
GP_BUFF = mat("Gp_Buff", (0.92, 0.86, 0.68), 0.85)
GP_IRON = mat("Gp_Iron", (0.12, 0.12, 0.13), 0.45, 0.45)
GP_BRASS = mat("Gp_Brass", (0.92, 0.68, 0.25), 0.3, 0.5)
GP_OAK = mat("Gp_Oak", (0.58, 0.38, 0.19), 0.85)
GP_OAK_D = mat("Gp_OakDark", (0.36, 0.23, 0.12), 0.85)
GP_EARTH = mat("Gp_Earth", (0.52, 0.39, 0.23), 0.95)
GP_EARTH_D = mat("Gp_EarthDark", (0.4, 0.29, 0.17), 0.95)
GP_WICKER = mat("Gp_Wicker", (0.72, 0.55, 0.3), 0.9)
GP_YELLOW = mat("Gp_Yellow", (1.0, 0.78, 0.12), 0.75)
GP_HAT = mat("Gp_HatBlack", (0.07, 0.07, 0.08), 0.7)
GP_CARRIAGE = mat("Gp_Carriage", (0.72, 0.12, 0.08), 0.8)
GP_STONE = mat("Gp_Stone", (0.56, 0.51, 0.44), 0.85)
GP_STONE_D = mat("Gp_StoneDark", (0.4, 0.36, 0.31), 0.85)
GP_SPARK = mat("Gp_Spark", (1.0, 0.7, 0.2), 0.3, 0.0, emit=(1.0, 0.55, 0.1), strength=3.0)
GP_DRUMHEAD = mat("Gp_DrumHead", (0.98, 0.95, 0.85), 0.5, 0.0, emit=(1.0, 0.95, 0.8), strength=0.3)
GP_BLUEFLAG = mat("Gp_FlagBlue", (0.1, 0.3, 0.8), 0.8)


def tricorn(body, m=None, trim=None):
    m = m or GP_HAT
    cyl(0.2, 0.17, (0, 0.03, 1.38), m, body, verts=10)
    cyl(0.33, 0.12, (0, 0.03, 1.33), m, body, verts=3, r2=0.4, rot=(0, 0, R(180)))
    if trim is not None:
        cyl(0.43, 0.025, (0, 0.03, 1.375), trim, body, verts=3, rot=(0, 0, R(180)))


def coat(body, m, skirt=0.45, r_bottom=0.37, cuffs=None, z_top=0.74):
    cyl(r_bottom, skirt, (0, 0.02, z_top - skirt / 2), m, body, verts=10, r2=0.29)


def earthwork(root):
    cyl(1.58, 0.3, (0, 0, 0.03), GP_EARTH_D, root, verts=12, r2=1.45)
    cyl(1.42, 0.06, (0, 0, 0.2), GP_EARTH, root, verts=12)
    for a in (205, 235, 305, 335, 25, 155):
        x, y = math.cos(R(a)) * 1.18, math.sin(R(a)) * 1.18
        cyl(0.26, 0.52, (x, y, 0.47), GP_WICKER, root, verts=9)
        for z in (0.33, 0.6):
            cyl(0.272, 0.04, (x, y, z), GP_OAK_D, root, verts=9)
        cyl(0.24, 0.06, (x, y, 0.72), GP_EARTH, root, verts=9, r2=0.15)


def musket(parent, butt, d=(0, -1, 0), L=1.45):
    b, d = Vector(butt), Vector(d).normalized()
    e = empty("Musket", tuple(b), parent)
    e.rotation_euler = d.to_track_quat("-Y", "Z").to_euler()
    box((0.08, 0.32, 0.14), (0, -0.14, -0.02), GP_OAK, e, bevel=0.02)
    box((0.06, 0.6, 0.07), (0, -0.55, 0.02), GP_OAK, e)
    seg((0, -0.3, 0.06), (0, -L, 0.06), 0.036, GP_IRON, e, verts=6)
    box((0.05, 0.1, 0.06), (0.04, -0.33, 0.04), GP_BRASS, e)
    for y in (-0.62, -0.84):
        cyl(0.04, 0.03, (0, y, 0.05), GP_BRASS, e, verts=6, rot=(R(90), 0, 0))
    seg((0, -L + 0.02, 0.0), (0, -L - 0.35, 0.0), 0.012, mat("Gp_Bayonet", (0.75, 0.76, 0.78), 0.3, 0.5), e, verts=3)
    return e


def musketeer():
    root = empty("Musketeer")
    earthwork(root)
    cyl(0.17, 0.32, (0.95, 0.6, 0.39), GP_OAK, root, verts=8)  # powder keg
    for z in (0.28, 0.5):
        cyl(0.18, 0.03, (0.95, 0.6, z), GP_IRON, root, verts=8)
    yaw = empty("Yaw", (0, 0, 0.23), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN, GP_NAVY, GP_BUFF, HAIR_WHITE, scale=1.22, belt=GP_WHITE, sleeve=GP_NAVY,
                       leg=GP_WHITE, boot=SHOE, left_arm=False, hair_style="pony")
    coat(body, GP_NAVY)
    sash(body, GP_WHITE, tilt=35, r=0.03)
    sash(body, GP_WHITE, tilt=-35, r=0.03)
    for s in (-1, 1):
        box((0.06, 0.04, 0.4), (s * 0.08, -0.24, 0.48), GP_RED, body)  # coat facings
    ico(0.04, (0, -0.215, 0.82), GP_BRASS, body, sub=1)
    tricorn(body, trim=GP_WHITE)
    x = 0.2
    hnd = limb(arm, GP_NAVY, SKIN, (x - 0.02, -0.18, -0.06))
    cuff(arm, GP_RED, (0, 0, 0), hnd, 0.78, r=0.085)
    musket(arm, (x, 0.08, 0.02), d=(0, -1, 0.1), L=1.6)
    lh = limb(arm, GP_NAVY, SKIN, (x + 0.02, -0.62, -0.02), start=LSH, elbow=(0.6, -0.38, -0.32))
    cuff(arm, GP_RED, (0.6, -0.38, -0.32), lh, 0.75, r=0.085)
    arm.rotation_euler = (R(-3), 0, 0)
    return root


def halberdier():
    root = empty("Halberdier")
    cyl(1.55, 0.26, (0, 0, 0.01), GP_STONE_D, root, verts=12)
    cyl(1.42, 0.14, (0, 0, 0.21), GP_OAK, root, verts=12)
    plank_lines(root, GP_OAK_D, 1.42, 0.285, n=6, along="x")
    stakes(root, GP_OAK, GP_OAK_D, 1.3, 20, 160, 11, h=0.55, z0=0.26, thick=0.08)
    for z in (0.45, 0.68):
        chain(root, GP_OAK_D, arc_pts((0, 0, z), 1.2, 20, 160, 6, u=(1, 0, 0), v=(0, 1, 0)), 0.035, verts=4)
    yaw = empty("Yaw", (0, 0, 0.28), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN, GP_YELLOW, GP_RED, HAIR_BROWN, scale=1.25, burly=1.1, beard=HAIR_BROWN,
                       belt=GP_OAK_D, leg=GP_YELLOW, boot=SHOE, left_arm=False, sleeve=GP_YELLOW, hair_style="short")
    for x in (-0.16, 0.0, 0.16):  # red stripes on the puffy doublet
        ico(0.27, (x, 0, 0.8), GP_RED, body, sub=2, scale=(0.16, 0.82, 1.07))
    for x in (-0.13, 0.13):  # yellow slashes on the red breeches
        cyl(0.05, 0.4, (x * 1.6, -0.18, 0.5), GP_YELLOW, body, verts=4, r2=0.03, rot=(R(-12), 0, 0))
    for s in (-1, 1):
        ico(0.15, (s * 0.31, 0, 0.92), GP_YELLOW, body, sub=1, scale=(1, 1, 0.9))     # puffed shoulders
        ico(0.15, (s * 0.31, 0, 0.92), GP_RED, body, sub=1, scale=(0.3, 1.05, 0.95))
    box((0.26, 0.08, 0.05), (0, -0.21, 1.07), HAIR_BROWN, body)  # mustache
    # morion
    M = mat("Gp_Morion", (0.6, 0.62, 0.67), 0.3, 0.5)
    ico(0.21, (0, 0, 1.31), M, body, sub=2, scale=(1.0, 1.15, 0.85))
    slab(body, M, [(-0.2, 0), (0.2, 0), (0.16, 0.12), (0.0, 0.18), (-0.16, 0.12)], 0.04, loc=(0, 0, 1.38), plane="yz")
    o = cyl(0.3, 0.04, (0, 0, 1.25), M, body, verts=14)
    o.scale = (0.85, 1.4, 1)
    for s in (-1, 1):
        box((0.2, 0.12, 0.035), (0, s * 0.43, 1.31), M, body, rot=(R(s * -35), 0, 0))
    ico(0.04, (0, 0, 1.6), GP_BRASS, body, sub=1)
    # halberd held diagonally
    R_ = Vector((0.0, -0.3, -0.04))
    L_ = Vector((0.32, -0.32, 0.26))
    d = (L_ - R_).normalized()
    limb(arm, GP_YELLOW, SKIN, tuple(R_))
    limb(arm, GP_YELLOW, SKIN, tuple(L_), start=LSH, elbow=(0.68, -0.25, -0.12))
    top = R_ + d * 1.6
    seg(R_ - d * 0.7, top, 0.032, GP_OAK, arm, verts=6)
    hd = empty("HalberdHead", tuple(top), arm)
    orient(hd, d, (d.z, 0, -d.x))
    hd.scale = (1.2, 1.2, 1.2)
    S = mat("Gp_Steel", (0.62, 0.64, 0.7), 0.3, 0.5)
    seg((0, 0, -0.05), (0, 0, 0.4), 0.04, S, hd, verts=4, r2=0.0)
    slab(hd, S, [(0.02, -0.12), (0.2, -0.2), (0.32, -0.12), (0.34, 0.08), (0.24, 0.16), (0.02, 0.1)], 0.03,
         loc=(0, 0, 0), plane="xz")
    slab(hd, S, [(-0.02, -0.06), (-0.22, -0.16), (-0.12, 0.0), (-0.02, 0.06)], 0.03, plane="xz")
    for z in (-0.16, -0.24):
        cyl(0.045, 0.03, (0, 0, z), GP_RED, hd, verts=6)
    arm.rotation_euler = (R(-10), 0, 0)
    return root


def spoked_wheel(parent, loc, r=0.32, rim=None, hub=None):
    rim = rim or GP_CARRIAGE
    hub = hub or GP_IRON
    e = empty("Wheel", loc, parent)
    torus(r, 0.05, (0, 0, 0), rim, e, rot=(0, R(90), 0), major=14, minor=4)
    torus(r + 0.02, 0.025, (0, 0, 0), GP_IRON, e, rot=(0, R(90), 0), major=14, minor=4)
    cyl(0.08, 0.14, (0, 0, 0), hub, e, verts=8, rot=(0, R(90), 0))
    for k in range(6):
        a = k * math.pi / 3
        seg((0, 0, 0), (0, math.cos(a) * r, math.sin(a) * r), 0.025, rim, e, verts=4)
    return e


def cannon():
    root = empty("Cannon")
    box((3.0, 3.0, 0.32), (0, 0, 0.04), GP_STONE_D, root, bevel=0.04)
    box((2.8, 2.8, 0.06), (0, 0, 0.21), GP_STONE, root)
    for k in range(10):
        box((0.45, 0.3, 0.02), (random.uniform(-1.1, 1.1), random.uniform(-1.1, 1.1), 0.245), GP_STONE_D, root)
    # L-shaped bastion parapet at the back-left corner
    box((2.7, 0.3, 0.42), (0.0, 1.32, 0.45), GP_STONE, root, bevel=0.03)
    box((0.3, 2.4, 0.42), (-1.32, 0.15, 0.45), GP_STONE, root, bevel=0.03)
    for i in range(6):
        box((0.3, 0.32, 0.05), (-1.1 + 0.45 * i, 1.32, 0.68), GP_STONE_D, root)
    box((0.42, 0.42, 0.62), (-1.29, 1.29, 0.55), GP_STONE_D, root, bevel=0.03)  # corner bastion pillar
    # cannonball pyramid
    for p in ((0.95, 0.75, 0.37), (1.17, 0.75, 0.37), (1.06, 0.94, 0.37), (1.06, 0.82, 0.55)):
        uvs(0.12, p, GP_IRON, root, seg=8, rings=6, smooth=False)
    yaw = empty("Yaw", (0, -0.05, 0.25), root)
    # carriage
    for s in (-1, 1):
        slab(yaw, GP_CARRIAGE, [(-0.55, 0.1), (0.75, 0.0), (0.75, 0.2), (0.15, 0.35), (-0.05, 0.6), (-0.4, 0.6),
                                (-0.55, 0.45)], 0.09, loc=(s * 0.22, 0, 0.05), plane="yz")
        spoked_wheel(yaw, (s * 0.38, -0.3, 0.32))
    box((0.85, 0.12, 0.1), (0, -0.3, 0.32), GP_OAK_D, yaw)
    box((0.36, 0.5, 0.08), (0, 0.45, 0.12), GP_OAK_D, yaw)
    arm = empty("Arm", (0, -0.2, 0.68), yaw)
    seg((0, 0.62, 0), (0, -1.0, 0), 0.19, GP_IRON, arm, verts=12, r2=0.14)
    for y, r in ((0.55, 0.21), (0.25, 0.2), (-0.35, 0.17), (-0.95, 0.18)):
        cyl(r, 0.06, (0, y, 0), GP_IRON, arm, verts=12, rot=(R(90), 0, 0))
    cyl(0.12, 0.04, (0, -1.02, 0), mat("Gp_Bore", (0.02, 0.02, 0.02), 0.9), arm, verts=10, rot=(R(90), 0, 0))
    ico(0.08, (0, 0.72, 0), GP_IRON, arm, sub=1)
    cyl(0.05, 0.6, (0, 0.0, 0), GP_IRON, arm, verts=6, rot=(0, R(90), 0))  # trunnions
    ico(0.03, (0, 0.5, 0.2), GP_SPARK, arm, sub=1)
    arm.rotation_euler = (R(-5), 0, 0)
    # gunner with a ramrod
    body, carm = figure(yaw, (0.78, 0.45, -0.02), SKIN_D, GP_NAVY, GP_BUFF, HAIR_BLACK, scale=0.9, belt=GP_WHITE,
                        sleeve=GP_NAVY, leg=GP_WHITE, boot=SHOE)
    carm.name = "CrewArm"
    coat(body, GP_NAVY)
    ico(0.22, (0, 0.02, 1.26), GP_RED, body, sub=1, scale=(1.05, 1.05, 0.7))  # headscarf
    body.rotation_euler = (0, 0, R(20))
    limb(carm, GP_NAVY, SKIN_D, (0.0, -0.25, 0.3))
    seg((0.0, -0.25, -0.85), (0.0, -0.25, 1.0), 0.025, GP_OAK, carm, verts=5)
    cyl(0.07, 0.18, (0.0, -0.25, 1.05), mat("Gp_Sponge", (0.85, 0.8, 0.65), 0.95), carm, verts=8)
    return root


def war_drummer():
    root = empty("WarDrummer")
    cyl(1.55, 0.26, (0, 0, 0.01), GP_STONE_D, root, verts=8)
    cyl(1.45, 0.14, (0, 0, 0.21), GP_OAK, root, verts=8)
    plank_lines(root, GP_OAK_D, 1.4, 0.285, n=6)
    torus(1.42, 0.04, (0, 0, 0.27), GP_OAK_D, root, major=8, minor=4, rot=(0, 0, R(22.5)))
    # flag pole
    fx, fy = -1.0, 0.75
    seg((fx, fy, 0.25), (fx, fy, 2.6), 0.035, GP_OAK_D, root, verts=6)
    ico(0.06, (fx, fy, 2.64), GP_BRASS, root, sub=1)
    for i in range(3):
        x0 = 0.05 + 0.25 * i
        dy = (0.0, 0.07, -0.02, 0.05)
        e = empty("FlagPart", (fx, fy, 2.5), root)
        slab(e, GP_BLUEFLAG, [(x0, 0), (x0 + 0.26, 0), (x0 + 0.26, -0.48), (x0, -0.48)], 0.02,
             loc=(0, dy[i], 0), rot=(0, 0, R((-1) ** i * 12)))
        slab(e, GP_WHITE, [(x0, -0.18), (x0 + 0.26, -0.18), (x0 + 0.26, -0.3), (x0, -0.3)], 0.025,
             loc=(0, dy[i], 0), rot=(0, 0, R((-1) ** i * 12)))
    # drummer boy
    yaw = empty("Yaw", (0.05, -0.05, 0.28), root)
    body, arm = figure(yaw, (0, 0, 0), SKIN_P, GP_NAVY, GP_WHITE, HAIR_BROWN, scale=1.08, belt=GP_WHITE,
                       sleeve=GP_NAVY, leg=GP_WHITE, boot=SHOE, left_arm=False)
    coat(body, GP_NAVY)
    sash(body, GP_WHITE, tilt=-38, r=0.03)
    for s in (-1, 1):
        box((0.06, 0.04, 0.4), (s * 0.08, -0.24, 0.48), GP_RED, body)
    # shako
    cyl(0.2, 0.36, (0, 0.01, 1.42), GP_HAT, body, verts=10, r2=0.23)
    box((0.32, 0.16, 0.03), (0, -0.2, 1.26), GP_HAT, body, rot=(R(-15), 0, 0))
    box((0.14, 0.03, 0.14), (0, -0.215, 1.42), GP_BRASS, body)
    cyl(0.235, 0.04, (0, 0.01, 1.58), GP_RED, body, verts=10)
    cyl(0.05, 0.22, (0, -0.14, 1.72), GP_RED, body, verts=6)
    ico(0.06, (0, -0.14, 1.85), GP_WHITE, body, sub=1)
    # side drum on the left hip; its head is the Orb
    dr = empty("Drum", (0.3, -0.32, 0.5), body)
    dr.rotation_euler = (R(-12), R(14), 0)
    cyl(0.25, 0.3, (0, 0, 0), GP_BRASS, dr, verts=14)
    for z in (-0.15, 0.15):
        torus(0.255, 0.035, (0, 0, z), GP_RED, dr, major=14, minor=4)
    for k in range(7):
        a0 = k * 2 * math.pi / 7
        a1 = a0 + math.pi / 7
        seg((math.cos(a0) * 0.26, math.sin(a0) * 0.26, -0.12), (math.cos(a1) * 0.26, math.sin(a1) * 0.26, 0.12), 0.012,
            GP_WHITE, dr, verts=3)
    orb = empty("Orb", (0, 0, 0.16), dr)
    cyl(0.235, 0.03, (0, 0, 0), GP_DRUMHEAD, orb, verts=14)
    seg((0, 0.24, 0.15), (-0.32, 0.3, 0.55), 0.015, GP_WHITE, dr, verts=3)  # drum sling
    # drumsticks: right one raised (Arm), left one on the drum head
    hnd = limb(arm, GP_NAVY, SKIN_P, (0.06, -0.3, 0.3))
    cuff(arm, GP_RED, (0, 0, 0), hnd, 0.78, r=0.08)
    seg((0.06, -0.3, 0.3), (0.12, -0.42, 0.65), 0.02, GP_OAK, arm, verts=4)
    ico(0.035, (0.12, -0.42, 0.66), GP_OAK, arm, sub=1)
    lh = limb(body, GP_NAVY, SKIN_P, (0.28, -0.42, 0.78), start=(0.31, 0, 0.96), elbow=(0.42, -0.2, 0.78))
    seg((0.28, -0.42, 0.78), (0.24, -0.5, 0.66), 0.02, GP_OAK, body, verts=4)
    arm.rotation_euler = (R(-20), 0, 0)
    return root


def isla():
    root = empty("HeroIsla")
    yaw = hero_yaw(root, (0.15, 0.3, 0.6), "Isla")
    body, arm = figure(yaw, (0, 0, 0), SKIN_T, GP_WHITE, GP_NAVY, HAIR_BLACK, scale=1.25, belt=GP_RED,
                       sleeve=GP_NAVY, leg=GP_NAVY, boot=SHOE, hair_style="long")
    # long navy coat
    cyl(0.39, 0.5, (0, 0.03, 0.47), GP_NAVY, body, verts=10, r2=0.3)
    for s in (-1, 1):
        box((0.14, 0.06, 0.62), (s * 0.18, -0.21, 0.78), GP_NAVY, body, rot=(R(-6), 0, R(s * -8)))
        box((0.04, 0.065, 0.62), (s * 0.12, -0.24, 0.78), GP_BRASS, body, rot=(R(-6), 0, R(s * -8)))
        cyl(0.1, 0.2, (s * 0.13, 0, 0.12), SHOE, body, verts=6)
    cyl(0.31, 0.09, (0, 0, 0.62), GP_RED, body, verts=10)
    box((0.1, 0.04, 0.32), (0.18, -0.26, 0.45), GP_RED, body, rot=(R(-8), 0, R(10)))  # sash tail
    # wide feathered hat
    cyl(0.21, 0.2, (0, 0.03, 1.42), GP_HAT, body, verts=10, r2=0.19)
    o = cyl(0.46, 0.04, (0, 0.03, 1.32), GP_HAT, body, verts=14, rot=(R(-6), R(8), 0))
    cyl(0.215, 0.04, (0, 0.03, 1.36), GP_RED, body, verts=10)
    slab(body, GP_WHITE, [(-0.1, 0), (0.02, 0.12), (0.22, 0.2), (0.48, 0.18), (0.58, 0.06), (0.35, 0.07), (0.14, 0.02)],
         0.04, loc=(0.2, 0.0, 1.4), plane="yz")
    slab(body, GP_RED, [(-0.05, 0), (0.05, 0.08), (0.25, 0.12), (0.4, 0.05), (0.2, 0.02)], 0.045,
         loc=(0.21, 0.02, 1.38), plane="yz")
    torus(0.03, 0.01, (-0.21, -0.02, 1.08), GP_BRASS, body, rot=(0, R(90), 0), major=8, minor=3)  # earring
    # cutlass at the left hip
    pts = arc_pts((0.38, 0.0, 0.85), 0.55, 200, 245, 5, u=(0, -1, 0), v=(0, 0, 1))
    chain(body, mat("Gp_Steel", (0.62, 0.64, 0.7), 0.3, 0.5), pts, 0.03, verts=4)
    torus(0.07, 0.015, (0.38, -0.5, 0.65), GP_BRASS, body, major=8, minor=3, rot=(0, R(90), 0))
    # flintlock pistol aimed forward
    hnd = limb(arm, GP_NAVY, SKIN_T, (0.02, -0.46, 0.06))
    cuff(arm, GP_WHITE, (0, 0, 0), hnd, 0.8, r=0.09)
    box((0.06, 0.16, 0.06), (0.02, -0.42, 0.0), GP_OAK, arm, rot=(R(-35), 0, 0))
    ico(0.045, (0.02, -0.38, -0.07), GP_BRASS, arm, sub=1)
    box((0.07, 0.36, 0.08), (0.02, -0.62, 0.1), GP_OAK, arm)
    seg((0.02, -0.5, 0.13), (0.02, -0.95, 0.13), 0.035, GP_IRON, arm, verts=8)
    box((0.04, 0.06, 0.06), (0.04, -0.52, 0.16), GP_BRASS, arm)
    arm.rotation_euler = (R(-8), 0, 0)
    return root


def marco():
    root = empty("HeroMarco")
    yaw = hero_yaw(root, (0.85, 0.35, 0.1), "Marco")
    body, arm = figure(yaw, (0, 0, 0), SKIN, GP_RED, GP_BUFF, HAIR_BLACK, scale=1.3, burly=1.22, belt=GP_WHITE,
                       sleeve=GP_RED, leg=GP_WHITE, boot=SHOE)
    coat(body, GP_RED)
    sash(body, GP_WHITE, tilt=35, r=0.035)
    for s in (-1, 1):
        box((0.07, 0.04, 0.42), (s * 0.08, -0.24, 0.46), GP_NAVY, body)
        ico(0.06, (s * 0.09, -0.2, 1.08), HAIR_BLACK, body, sub=1, scale=(1.4, 0.7, 0.6))   # big mustache
        ico(0.035, (s * 0.15, -0.18, 1.11), HAIR_BLACK, body, sub=1)
        cyl(0.085, 0.07, (0.37 * s, -0.02, 0.6), GP_NAVY, body, verts=6) if s > 0 else None
    for z in (0.7, 0.8, 0.9):
        ico(0.025, (0, -0.215, z), GP_BRASS, body, sub=1)
    # mitre cap
    cyl(0.2, 0.42, (0, 0.04, 1.48), GP_RED, body, verts=8, r2=0.08)
    slab(body, GP_BRASS, [(-0.24, 0), (0.24, 0), (0.18, 0.36), (0, 0.62), (-0.18, 0.36)], 0.04, loc=(0, -0.16, 1.24))
    slab(body, GP_NAVY, [(-0.18, 0.05), (0.18, 0.05), (0.13, 0.33), (0, 0.52), (-0.13, 0.33)], 0.05, loc=(0, -0.165, 1.24))
    ico(0.06, (0, -0.2, 1.42), GP_BRASS, body, sub=1)
    ico(0.06, (0, -0.1, 1.88), GP_WHITE, body, sub=1)
    # grenade bag on the hip
    box((0.26, 0.14, 0.24), (-0.3, 0.05, 0.5), mat("Gp_Bag", (0.25, 0.17, 0.1), 0.8), body, bevel=0.03)
    ico(0.07, (-0.3, -0.04, 0.6), GP_IRON, body, sub=1)
    # lit grenade raised to lob
    hnd = limb(arm, GP_RED, SKIN, (0.0, 0.02, 0.46))
    cuff(arm, GP_NAVY, (0, 0, 0), hnd, 0.78, r=0.09)
    uvs(0.14, (0, -0.04, 0.6), GP_IRON, arm, seg=10, rings=7, smooth=False)
    seg((0, -0.04, 0.72), (0.03, -0.08, 0.84), 0.02, ROPE, arm, verts=4)
    ico(0.06, (0.03, -0.08, 0.87), GP_SPARK, arm, sub=1)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        seg((0.03, -0.08, 0.87), (0.03 + math.cos(a) * 0.12, -0.08 + math.sin(a) * 0.04, 0.87 + math.sin(a) * 0.1),
            0.012, GP_SPARK, arm, verts=3)
    arm.rotation_euler = (R(-40), 0, 0)
    return root


# ================================================================== build
BUILD = [
    ("iron", "towers", "javelin_thrower", javelin_thrower), ("iron", "towers", "axe_warrior", axe_warrior),
    ("iron", "towers", "ballista", ballista), ("iron", "towers", "druid", druid),
    ("iron", "heroes", "brenna", brenna), ("iron", "heroes", "kael", kael),
    ("classical", "towers", "cretan_archer", cretan_archer), ("classical", "towers", "legionary", legionary),
    ("classical", "towers", "onager", onager), ("classical", "towers", "oracle", oracle),
    ("classical", "heroes", "cassia", cassia), ("classical", "heroes", "theron", theron),
    ("medieval", "towers", "crossbowman", crossbowman), ("medieval", "towers", "knight", knight),
    ("medieval", "towers", "trebuchet", trebuchet), ("medieval", "towers", "alchemist", alchemist),
    ("medieval", "heroes", "aldric", aldric), ("medieval", "heroes", "wren", wren),
    ("gunpowder", "towers", "musketeer", musketeer), ("gunpowder", "towers", "halberdier", halberdier),
    ("gunpowder", "towers", "cannon", cannon), ("gunpowder", "towers", "war_drummer", war_drummer),
    ("gunpowder", "heroes", "isla", isla), ("gunpowder", "heroes", "marco", marco),
]

GROUND = {"iron": (0.33, 0.45, 0.24), "classical": (0.55, 0.5, 0.36), "medieval": (0.36, 0.44, 0.28),
          "gunpowder": (0.45, 0.42, 0.3)}

PIVOTS = ("Yaw", "Arm", "Orb")
cam = lp.stage(bg=(0.45, 0.45, 0.35))
floor = bpy.data.materials["_floor"]
built = {}
for era, folder, name, fn in BUILD:
    if ERA_SEL and era not in ERA_SEL:
        continue
    if ONLY and name not in ONLY:
        continue
    r = fn()
    # every model shares one Blender scene, so its pivots come out as "Yaw.003" etc.; the game looks them
    # up by exact name, so claim the plain names for the export and park them under unique names after.
    pivots = [o for o in lp.hierarchy(r) if o.name.split(".")[0] in PIVOTS]
    for o in pivots:
        o.name = o.name.split(".")[0]
        assert o.name in PIVOTS, f"{name}: pivot name clash {o.name}"
    lp.export_glb(r, os.path.join(OUT, folder, f"{name}.glb"))
    for o in pivots:
        o.name = f"{o.name}~{name}"
    built.setdefault(era, []).append((folder, r))

if "--preview" in sys.argv:
    os.makedirs(PDIR, exist_ok=True)
    allroots = [r for v in built.values() for _, r in v]
    for era, items in built.items():
        for r in allroots:
            hide_tree(r, True)
        towers = [r for f, r in items if f == "towers"]
        heroes = [r for f, r in items if f == "heroes"]
        for i, r in enumerate(towers):
            hide_tree(r, False)
            r.location = ((i - (len(towers) - 1) / 2) * 3.4, -1.6, 0)
        for i, r in enumerate(heroes):
            hide_tree(r, False)
            r.location = ((i - (len(heroes) - 1) / 2) * 3.4, 2.0, 0)
        floor.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*GROUND[era], 1)
        bpy.context.scene.eevee.taa_render_samples = 16
        lp.shoot(cam, os.path.join(PDIR, f"{era}_lineup.png"), (0, 0.4, 0.9), 15.5, res=1400, pos_dir=(0.45, -1.2, 0.9))
print("DONE")
