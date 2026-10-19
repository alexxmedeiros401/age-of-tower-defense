"""Main-menu art, rendered: gold medallion rims, label plaques, currency pills, gem buttons and 3D icons.

    python3 tools/blender/ui/menu_art.py [--only rim,plaque,...] [--samples 64]

Everything lands in assets/ui/mm_*.png. game.gd builds the menu buttons from these layers: a shader-drawn enamel disc
(any colour, with a moving shine), the 3D icon (it may pop out over the rim) and the gold rim on top; labels sit on
the plaque (a 9-patch), currencies in the pill (9-patch).
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Euler, Matrix
import ui_kit as K

A = sys.argv
ONLY = A[A.index("--only") + 1].split(",") if "--only" in A else None
SAMPLES = int(A[A.index("--samples") + 1]) if "--samples" in A else 64
TMP = os.path.join(__import__("tempfile").gettempdir(), "menu_render")
os.makedirs(TMP, exist_ok=True)
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))


def _font():
    """Blender can't read woff2: convert the game's font (assets/fonts/LilitaOne.woff2) to a TTF once (needs fontTools +
    brotli: pip install fonttools brotli)."""
    ttf = os.path.join(TMP, "LilitaOne.ttf")
    if not os.path.exists(ttf):
        from fontTools.ttLib import TTFont
        f = TTFont(os.path.join(ROOT, "assets", "fonts", "LilitaOne.woff2"))
        f.flavor = None
        f.save(ttf)
    return ttf


FONT = _font()
JOBS = []


def job(fn):
    JOBS.append(fn)
    return fn


def top_camera(scale, res_w, res_h=None):
    """Straight-down orthographic camera over the XY plane (UI flats)."""
    sc = bpy.context.scene
    sc.render.resolution_x = res_w
    sc.render.resolution_y = res_h or res_w
    cam = K.camera((0, 0, 10), (0, 0, 0), ortho=scale)
    cam.rotation_euler = Euler((0, 0, 0))
    return cam


def flat_lights():
    """UI flats: key from the top left, soft fill, so bevels read as raised."""
    K.light("SUN", (-3, 3, 6), (0, 0, 0), energy=3.2, color=(1.0, 0.96, 0.88), size=math.radians(8))
    K.light("AREA", (4, -3, 3), (0, 0, 0), energy=120, color=(0.8, 0.88, 1.0), size=4)


def out(name, raw, size, outline=0.0, shadow=0.0, pad=0.0, shadow_off=(0.0, 0.02)):
    dst = os.path.join(K.UI, name + ".png")
    K.post(raw, dst, size=size, outline=outline, shadow=shadow, pad=pad, shadow_off=shadow_off)
    print("wrote", dst, flush=True)


# ------------------------------------------------------------------------------------------------ medallion rims
def rim_geometry(R=1.0, w=0.2, studs=12, gems=0, gem_col=(0.3, 0.8, 1.0)):
    gold = K.gold("Gold", (1.0, 0.76, 0.33), 0.2)
    dark = K.matte("Outline", (0.04, 0.03, 0.06))
    # profile: inner lip, groove, rounded crown, outer step (r, z)
    ri = R - w
    prof = [(ri - 0.01, -0.02), (ri, 0.02), (ri + 0.012, 0.05), (ri + 0.03, 0.062), (ri + 0.05, 0.056), (ri + 0.062, 0.04),
            (ri + 0.075, 0.038), (ri + 0.09, 0.07), (ri + 0.12, 0.09), (ri + 0.15, 0.085), (ri + 0.175, 0.06), (R - 0.006, 0.03),
            (R, 0.0), (R, -0.02)]
    ring = K.revolve("Rim", prof, 160, gold)
    K.subsurf(ring, 1)
    # dark outline just outside and inside
    K.revolve("OutlineO", [(R - 0.01, -0.03), (R + 0.03, -0.03), (R + 0.03, 0.02), (R - 0.01, 0.02)], 160, dark)
    K.revolve("OutlineI", [(ri - 0.03, -0.03), (ri + 0.005, -0.03), (ri + 0.005, 0.015), (ri - 0.03, 0.015)], 160, dark)
    for i in range(studs):
        a = 2 * math.pi * i / studs + math.pi / studs
        if gems and i % (studs // gems) == 0:
            continue
        r0 = ri + 0.12
        K.sphere("Stud", 0.036, gold, loc=(r0 * math.cos(a), r0 * math.sin(a), 0.085), scale=(1, 1, 0.75), seg=24, rings=12)
    if gems:
        gm = K.gem("Gem", gem_col)
        for i in range(gems):
            a = 2 * math.pi * i / gems + math.pi / studs
            r0 = ri + 0.12
            g = K.sphere("Gem", 0.05, gm, loc=(r0 * math.cos(a), r0 * math.sin(a), 0.09), scale=(1, 1, 0.6), seg=8, rings=4)
            K.cylinder("GemSet", 0.062, 0.03, 32, gold, loc=(r0 * math.cos(a), r0 * math.sin(a), 0.075))
    return ring


@job
def rim():
    K.reset(1024, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2)
    rim_geometry(1.0, 0.2, studs=12)
    top_camera(2.12, 1024)
    flat_lights()
    raw = K.render(os.path.join(TMP, "rim.png"))
    out("mm_rim", raw, 512)


@job
def rim_play():
    K.reset(1024, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2)
    rim_geometry(1.0, 0.17, studs=16, gems=4, gem_col=(0.35, 0.95, 0.4))
    top_camera(2.12, 1024)
    flat_lights()
    raw = K.render(os.path.join(TMP, "rim_play.png"))
    out("mm_rim_play", raw, 512)


# ------------------------------------------------------------------------------------------------ plaques / pills
def rounded_rect_pts(w, h, r, n=12):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def tube_frame(name, w, h, r, thick, mat, z=0.0):
    """A round gold tube following a rounded rectangle (catches highlights from every side)."""
    pts = [(x, y, z) for x, y in rounded_rect_pts(w, h, r, 16)]
    ob = K.curve_tube(name, pts, thick, mat, res=16, closed=True)
    return ob


def dome_face(name, w, h, r, z0, z1, mat, rings=14):
    """A cushion: rounded rectangle whose surface rolls down to its edge on a quarter circle of radius r (a capsule
    becomes a half cylinder), so light runs across it as a gradient with a highlight line."""
    bm = bmesh.new()
    loops = []
    n = 16
    for k in range(rings + 1):
        o = r * k / rings
        z = z0 + (z1 - z0) * math.sqrt(max(0.0, 1.0 - (1.0 - o / r) ** 2))
        rr = max(r - o, 1e-4)
        loops.append([bm.verts.new((x, y, z)) for x, y in rounded_rect_pts(w - 2 * o, h - 2 * o, rr, n)])
    m = len(loops[0])
    for k in range(rings):
        a, b = loops[k], loops[k + 1]
        for i in range(m):
            j = (i + 1) % m
            try:
                bm.faces.new((a[i], a[j], b[j], b[i]))
            except ValueError:
                pass
    if w - 2 * r > 1e-3 and h - 2 * r > 1e-3:
        bm.faces.new(loops[-1])                     # flat top of a cushion that isn't a capsule
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return K.link(me, name, mat)


def slab(name, w, h, r, z0, z1, mat, bevel=0.02):
    ob = K.prism(name, rounded_rect_pts(w, h, r), z0, z1, mat)
    K.bevel(ob, bevel, 3, 30)
    return ob


@job
def plaque():
    """Label plaque, a 9-patch: navy enamel in a round gold frame (straight middle so it can stretch)."""
    K.reset(0, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2, w=1024, h=320)
    gold = K.gold("Gold", (1.0, 0.76, 0.33), 0.2)
    dark = K.matte("Outline", (0.04, 0.03, 0.06))
    navy = K.paint("Navy", (0.12, 0.2, 0.4), 0.22, coat=0.8)
    slab("Out", 3.02, 0.84, 0.42, -0.08, -0.02, dark, 0.01)
    dome_face("Face", 2.86, 0.68, 0.34, -0.04, 0.07, navy)
    tube_frame("Frame", 2.86, 0.68, 0.34, 0.055, gold, 0.02)
    top_camera(3.2, 1024, 320)
    flat_lights()
    raw = K.render(os.path.join(TMP, "plaque.png"))
    out("mm_plaque", raw, (512, 160))


@job
def pill():
    """Currency pill, a 9-patch: dark glass in a round gold frame."""
    K.reset(0, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2, w=1024, h=256)
    gold = K.gold("Gold", (1.0, 0.76, 0.33), 0.2)
    dark = K.matte("Outline", (0.04, 0.03, 0.06))
    glass = K.paint("Glass", (0.05, 0.07, 0.13), 0.12, coat=1.0)
    slab("Out", 3.62, 0.88, 0.44, -0.08, -0.02, dark, 0.01)
    dome_face("Face", 3.46, 0.72, 0.36, -0.04, 0.06, glass)
    tube_frame("Frame", 3.46, 0.72, 0.36, 0.05, gold, 0.02)
    top_camera(3.84, 1024, 256)
    flat_lights()
    raw = K.render(os.path.join(TMP, "pill.png"))
    out("mm_pill", raw, (512, 128))


@job
def panel():
    """Info panel, a 9-patch: dark glass in a round gold frame with corner studs."""
    K.reset(0, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2, w=768, h=768)
    gold = K.gold("Gold", (1.0, 0.76, 0.33), 0.2)
    dark = K.matte("Outline", (0.04, 0.03, 0.06))
    glass = K.paint("Glass", (0.06, 0.08, 0.16), 0.15, coat=1.0)
    slab("Out", 2.9, 2.9, 0.36, -0.08, -0.02, dark, 0.01)
    dome_face("Face", 2.74, 2.74, 0.3, -0.04, 0.05, glass)
    tube_frame("Frame", 2.74, 2.74, 0.3, 0.05, gold, 0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.sphere("Stud", 0.075, gold, loc=(sx * 1.24, sy * 1.24, 0.07), scale=(1, 1, 0.7), seg=24, rings=12)
    top_camera(3.0, 768, 768)
    flat_lights()
    raw = K.render(os.path.join(TMP, "panel.png"))
    out("mm_panel", raw, (384, 384))


@job
def xpbar():
    """XP bar track, a 9-patch: a thin round gold frame round a dark groove (the fill is drawn in game)."""
    K.reset(0, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2, w=1024, h=192)
    gold = K.gold("Gold", (1.0, 0.76, 0.33), 0.2)
    dark = K.matte("Outline", (0.04, 0.03, 0.06))
    groove = K.paint("Groove", (0.03, 0.04, 0.07), 0.4)
    slab("Out", 3.82, 0.58, 0.29, -0.08, -0.02, dark, 0.01)
    slab("Groove", 3.66, 0.42, 0.21, -0.04, 0.0, groove, 0.01)
    tube_frame("Frame", 3.66, 0.42, 0.21, 0.04, gold, 0.02)
    top_camera(3.96, 1024, 192)
    flat_lights()
    raw = K.render(os.path.join(TMP, "xpbar.png"))
    out("mm_xpbar", raw, (512, 96))


# ------------------------------------------------------------------------------------------------ gem buttons, badges
def gem_button(name, col, glyph=None, glyph_col=(1, 1, 1)):
    K.reset(512, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2)
    gold = K.gold("Gold", (1.0, 0.76, 0.33), 0.2)
    dark = K.matte("Outline", (0.04, 0.03, 0.06))
    K.cylinder("Out", 1.06, 0.05, 96, dark, loc=(0, 0, -0.03))
    rim = K.revolve("Rim", [(0.78, 0.0), (0.8, 0.06), (0.86, 0.1), (0.94, 0.1), (1.0, 0.06), (1.0, 0.0)], 128, gold)
    dome = K.revolve("Dome", [(0.0, 0.32), (0.3, 0.3), (0.55, 0.24), (0.72, 0.15), (0.8, 0.07), (0.8, 0.0)], 128,
                     K.paint("Enamel", col, 0.12, coat=1.0))
    if glyph == "plus":
        w = K.paint("Glyph", glyph_col, 0.2, coat=0.6)
        a, b = 0.44, 0.14
        pts = [(b, a), (-b, a), (-b, b), (-a, b), (-a, -b), (-b, -b), (-b, -a), (b, -a), (b, -b), (a, -b), (a, b), (b, b)]
        pl = K.prism("Plus", pts, 0.0, 0.12, w, loc=(0, 0, 0.27))
        K.bevel(pl, 0.05, 4, 30)
    top_camera(2.2, 512)
    flat_lights()
    raw = K.render(os.path.join(TMP, name + ".png"))
    out(name, raw, 192)


@job
def plus():
    gem_button("mm_plus", (0.3, 0.8, 0.2), "plus")


@job
def badge():
    gem_button("mm_badge", (0.92, 0.12, 0.1))


# ------------------------------------------------------------------------------------------------ 3D icons
def icon_scene(res=768):
    K.reset(res, SAMPLES, hdri="studio.exr", hdri_strength=0.9, hdri_rot=0.6)
    K.studio(key=3.4, rim=3.2, fill=0.8)


def finish_icon(name, size=256, outline=0.014, cam=(-1.0, -3.6, 2.6), target=(0, 0, 0.3), margin=0.04):
    c = K.camera(cam, target, lens=85)
    K.fit_ortho(c, margin=margin)
    raw = K.render(os.path.join(TMP, name + ".png"))
    out(name, raw, size, outline=outline, shadow=0.012, pad=0.04, shadow_off=(0.0, 0.025))


@job
def play():
    """Glossy cream play triangle with a gold bevel."""
    icon_scene()
    cream = K.paint("Cream", (1.0, 0.98, 0.92), 0.15, coat=1.0)
    gold = K.gold("Gold", (1.0, 0.76, 0.33), 0.2)
    pts = []
    tri = [(0.62, 0.0), (-0.38, 0.6), (-0.38, -0.6)]
    # rounded triangle: offset corners
    for i in range(3):
        p0, p1, p2 = Vector(tri[i - 1] + (0,)), Vector(tri[i] + (0,)), Vector(tri[(i + 1) % 3] + (0,))
        d0, d1 = (p0 - p1).normalized(), (p2 - p1).normalized()
        r = 0.16
        for k in range(9):
            t = k / 8.0
            q = p1 + (d0 * (1 - t) + d1 * t).normalized() * 0.0
            a = p1 + d0 * r
            b = p1 + d1 * r
            # quadratic bezier a -> p1 -> b
            pq = a * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + b * t * t
            pts.append((pq.x, pq.y))
    base = K.prism("PlayGold", [(x * 1.12, y * 1.12) for x, y in pts], -0.1, 0.0, gold)
    K.bevel(base, 0.05, 4, 30)
    face = K.prism("Play", pts, 0.0, 0.22, cream)
    K.bevel(face, 0.1, 6, 30)
    for o in (base, face):
        o.rotation_euler = Euler((math.radians(90), 0, 0))
        o.location.z = 0.6
    finish_icon("mm_play", cam=(-0.8, -4.0, 1.2), target=(0, 0, 0.6))


@job
def upgrade():
    """A chunky gold up-arrow with a blue gem."""
    icon_scene()
    gold = K.toon_gold("ArrowGold", axis="Y")
    pts = [(0.0, 0.75), (0.62, 0.12), (0.26, 0.12), (0.26, -0.7), (-0.26, -0.7), (-0.26, 0.12), (-0.62, 0.12)]
    a = K.prism("Arrow", pts, -0.16, 0.16, gold)
    K.bevel(a, 0.13, 6, 30)
    g = K.sphere("Gem", 0.17, K.gem("Gem", (0.25, 0.7, 1.0)), loc=(0, -0.2, 0.16), scale=(1, 1, 0.55), seg=8, rings=4)
    g.parent = a
    for o in (a,):
        o.rotation_euler = Euler((math.radians(90), 0, math.radians(-8)))
        o.location.z = 0.75
    finish_icon("mm_upgrade", cam=(-1.2, -4.0, 1.5), target=(0, 0, 0.75))


@job
def gear():
    """Settings: a steel gear with a blue enamel centre."""
    icon_scene()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    steel = K.metal("Steel", (0.8, 0.84, 0.9), 0.22)
    pts = []
    teeth, R, d = 8, 0.75, 0.2
    for t in range(teeth):
        a0 = 2 * math.pi * t / teeth
        for f, r in ((0.0, R - d), (0.14, R - d), (0.27, R), (0.6, R), (0.73, R - d)):
            a = a0 + f * 2 * math.pi / teeth
            pts.append((r * math.cos(a), r * math.sin(a)))
    g = K.prism("Gear", pts, -0.13, 0.13, steel, holes=[(0, 0, 0.26, 48)])
    K.bevel(g, 0.04, 3, 30)
    hub = K.torus("Hub", 0.3, 0.07, steel, loc=(0, 0, 0.12), seg=64, mseg=16)
    hub.parent = g
    gm = K.sphere("Core", 0.22, K.gem("Blue", (0.25, 0.55, 1.0)), loc=(0, 0, 0.0), scale=(1, 1, 0.5), seg=32, rings=16)
    gm.parent = g
    g.rotation_euler = Euler((math.radians(70), 0, math.radians(10)))
    g.location.z = 0.75
    finish_icon("mm_gear", cam=(-1.0, -4.0, 1.8), target=(0, 0, 0.75))


@job
def door():
    """Quit: an arched wooden door with iron bands in a stone frame."""
    icon_scene()
    wood = K.paint("Wood", (0.58, 0.33, 0.15), 0.55)
    iron = K.metal("Iron", (0.3, 0.3, 0.33), 0.35)
    stone = K.paint("Stone", (0.62, 0.6, 0.58), 0.7)
    def arch(w, h, n=16):
        pts = [(-w / 2, 0.0), (w / 2, 0.0)]
        for i in range(n + 1):
            a = math.pi * i / n
            pts.append((w / 2 * math.cos(a), h - w / 2 + w / 2 * math.sin(a)))
        return pts
    fr = K.prism("Frame", arch(1.2, 1.55), -0.12, 0.12, stone)
    K.bevel(fr, 0.05, 3, 30)
    dr = K.prism("Door", arch(0.9, 1.36), -0.06, 0.16, wood)
    K.bevel(dr, 0.03, 3, 30)
    for i in range(4):
        x = -0.34 + i * 0.227
        pl = K.prism("Plank", [(x - 0.004, 0.02), (x + 0.004, 0.02), (x + 0.004, 1.2), (x - 0.004, 1.2)], 0.16, 0.17, K.paint("Gap", (0.2, 0.1, 0.05), 0.8))
        pl.parent = dr
    for z in (0.32, 0.98):
        b = K.prism("Band", [(-0.45, z - 0.05), (0.32, z - 0.05), (0.32, z + 0.05), (-0.45, z + 0.05)], 0.16, 0.2, iron)
        K.bevel(b, 0.015, 2, 30)
        b.parent = dr
    ring = K.torus("Ring", 0.08, 0.018, K.gold("Brass", (1.0, 0.74, 0.3), 0.25), loc=(0.27, 0.66, 0.2), seg=32, mseg=10)
    ring.parent = dr
    for o in (fr, dr):
        o.rotation_euler = Euler((math.radians(90), 0, math.radians(-10)))
    finish_icon("mm_door", cam=(-1.0, -4.0, 1.4), target=(0, 0, 0.7))


@job
def mapicon():
    """Maps: a folded parchment map with a dotted route and a red pin."""
    icon_scene()
    # parchment texture painted with PIL: land, sea, a dotted route
    from PIL import Image, ImageDraw
    W = 512
    im = Image.new("RGB", (W, int(W * 0.72)), (236, 214, 160))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, int(W * 0.72)], fill=(150, 200, 230))
    d.polygon([(40, 60), (200, 30), (330, 70), (470, 50), (490, 300), (330, 350), (150, 330), (30, 280)], fill=(196, 222, 140))
    d.polygon([(120, 120), (230, 100), (260, 180), (170, 230), (100, 190)], fill=(150, 196, 100))
    d.polygon([(300, 160), (420, 130), (450, 250), (330, 270)], fill=(214, 190, 130))
    for i in range(14):
        t = i / 13.0
        x = 70 + 380 * t
        y = 280 - 150 * math.sin(t * 2.6) + 30 * t
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(160, 40, 30))
    tex = os.path.join(TMP, "map_tex.png")
    im.save(tex)
    m = bpy.data.materials.new("Parchment")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    ti = nt.nodes.new("ShaderNodeTexImage")
    ti.image = bpy.data.images.load(tex)
    nt.links.new(ti.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    # three panels, zig-zag folded
    bm = bmesh.new()
    cols = 3
    w, h = 1.5, 1.08
    verts = []
    for i in range(cols * 8 + 1):
        u = i / (cols * 8)
        x = -w / 2 + w * u
        seg = u * cols
        k = seg - math.floor(seg) if i < cols * 8 else 1.0
        z = 0.12 * (1 - abs(2 * ((seg % 2) / 2.0) - 1)) * 2 - 0.06
        verts.append(((x, z), u))
    grid = []
    for (x, z), u in verts:
        grid.append([bm.verts.new((x, z, -h / 2 + h * j / 6)) for j in range(7)])
    uv_rows = []
    faces = []
    for i in range(len(grid) - 1):
        for j in range(6):
            f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
            faces.append((f, i, j))
    uvl = bm.loops.layers.uv.new("UVMap")
    for f, i, j in faces:
        for lp, (di, dj) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            lp[uvl].uv = ((i + di) / (len(grid) - 1), (j + dj) / 6)
    me = bpy.data.meshes.new("Map")
    bm.to_mesh(me)
    bm.free()
    mp = K.link(me, "Map", m, smooth=False)
    so = mp.modifiers.new("Solid", "SOLIDIFY")
    so.thickness = 0.02
    mp.rotation_euler = Euler((0, 0, math.radians(-6)))
    mp.location.z = 0.6
    # the pin
    red = K.paint("PinRed", (0.9, 0.12, 0.1), 0.2, coat=1.0)
    K.sphere("PinHead", 0.13, red, loc=(0.42, -0.25, 0.98))
    K.cylinder("PinNeedle", 0.018, 0.4, 16, K.metal("Steel", (0.8, 0.82, 0.86), 0.2), loc=(0.42, -0.22, 0.78), rot=(math.radians(-10), 0, 0))
    finish_icon("mm_map", cam=(-1.0, -4.0, 1.6), target=(0, 0, 0.6))


@job
def shard():
    """Time Shard: a glowing violet crystal cluster on a gold setting."""
    icon_scene()
    vio = K.gem("Violet", (0.62, 0.35, 1.0), rough=0.02)
    vio_emit = vio.node_tree.nodes["Principled BSDF"]
    vio_emit.inputs["Emission Color"].default_value = K.lin((0.55, 0.3, 1.0))
    vio_emit.inputs["Emission Strength"].default_value = 0.6
    def crystal(h, r, loc, rot):
        bm = bmesh.new()
        n = 6
        ring_lo = [bm.verts.new((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), 0)) for i in range(n)]
        ring_hi = [bm.verts.new((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), h * 0.72)) for i in range(n)]
        tip = bm.verts.new((0, 0, h))
        bot = bm.verts.new((0, 0, -h * 0.12))
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((ring_lo[i], ring_lo[j], ring_hi[j], ring_hi[i]))
            bm.faces.new((ring_hi[i], ring_hi[j], tip))
            bm.faces.new((ring_lo[j], ring_lo[i], bot))
        me = bpy.data.meshes.new("Crystal")
        bm.to_mesh(me)
        bm.free()
        ob = K.link(me, "Crystal", vio, loc, rot, smooth=False)
        K.bevel(ob, 0.01, 1, 20, harden=False)
        return ob
    crystal(1.3, 0.24, (0, 0, 0.0), (0, 0, 0))
    crystal(0.9, 0.18, (-0.24, 0.02, 0.0), (0, math.radians(-24), 0.3))
    crystal(0.8, 0.16, (0.24, 0.0, 0.0), (0, math.radians(26), 0.8))
    crystal(0.55, 0.12, (0.06, -0.2, 0.0), (math.radians(-28), math.radians(12), 0.2))
    gold = K.gold("Gold", (1.0, 0.76, 0.33), 0.22)
    K.revolve("Setting", [(0.0, -0.18), (0.42, -0.18), (0.48, -0.1), (0.44, 0.02), (0.3, 0.06), (0.0, 0.06)], 64, gold)
    finish_icon("mm_shard", cam=(-1.0, -4.0, 1.6), target=(0, 0, 0.5))


@job
def star():
    """Level badge: a puffy toon-gold star (the level number is drawn over it in game)."""
    K.reset(512, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2)
    gold = K.toon_gold("StarGold", top=(1.0, 0.95, 0.5), bottom=(1.0, 0.58, 0.1), axis="Y")
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        r = 1.0 if i % 2 == 0 else 0.5
        pts.append((r * math.cos(a), r * math.sin(a)))
    st = K.prism("Star", pts, -0.12, 0.12, gold)
    K.bevel(st, 0.16, 6, 30)
    top_camera(2.5, 512)
    flat_lights()
    raw = K.render(os.path.join(TMP, "star.png"))
    out("mm_star", raw, 192, outline=0.016, shadow=0.012)


@job
def logo():
    """The title: 'TOWER DEFENSE' in chunky gold letters with bronze sides, 'AGE OF' on a blue enamel plaque above."""
    K.reset(0, SAMPLES, hdri="studio.exr", hdri_strength=1.0, hdri_rot=1.2, w=1600, h=640)
    gold = K.toon_gold("TitleGold", top=(1.0, 0.95, 0.5), bottom=(1.0, 0.55, 0.1), axis="Y")
    side = K.paint("Side", (0.5, 0.22, 0.05), 0.4, coat=0.4)
    t = K.text3d("Title", "TOWER DEFENSE", size=1.0, extrude=0.16, bevel_depth=0.04, mat=gold, font=FONT, loc=(0, -0.28, 0))
    t.data.space_character = 1.02
    s_ = K.text3d("Age", "AGE OF", size=0.5, extrude=0.08, bevel_depth=0.025, mat=K.paint("Cream", (1.0, 0.98, 0.9), 0.2, coat=0.6), font=FONT, loc=(0, 0.6, 0.04))
    s_.data.space_character = 1.08
    navy = K.paint("Plaque", (0.18, 0.32, 0.66), 0.22, coat=0.8)
    pq = dome_face("Plaque", 2.6, 0.62, 0.31, -0.12, 0.0, navy)
    pq.location = (0, 0.6, 0)
    fr = tube_frame("PlaqueFrame", 2.6, 0.62, 0.31, 0.05, K.gold("Gold2", (1.0, 0.76, 0.33), 0.2), -0.04)
    fr.location = (0, 0.6, 0)
    bpy.context.view_layer.update()
    # gold faces up front, the extruded sides in bronze: material by face normal after conversion
    for ob in bpy.context.scene.objects:
        ob.select_set(ob == t)
    bpy.context.view_layer.objects.active = t
    bpy.ops.object.convert(target="MESH")
    t = bpy.context.view_layer.objects.active
    t.data.materials.clear()
    t.data.materials.append(gold)
    t.data.materials.append(side)
    for p in t.data.polygons:
        p.material_index = 0 if p.normal.z > 0.55 else 1
    cam = top_camera(8.0, 1600, 640)
    cam.location = (0, -2.2, 10)
    cam.rotation_euler = Euler((math.radians(12), 0, 0))
    flat_lights()
    K.fit_ortho(cam, margin=0.03)
    raw = K.render(os.path.join(TMP, "logo.png"))
    out("mm_logo", raw, (1200, 480), outline=0.007, shadow=0.008, shadow_off=(0.0, 0.03))


for fn in JOBS:
    if ONLY and fn.__name__ not in ONLY:
        continue
    fn()
