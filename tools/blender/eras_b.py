"""Industrial, Modern, Digital and Data Center towers + heroes (eras 6-9).
Run: python3 eras_b.py --out ASSETS_DIR [--only a,b] [--era industrial,modern] [--preview] [--previewdir DIR]
Pivots for the game: Yaw (turns to face target), Arm (attack swing / recoil, + rotation = forward), Orb (pulse flash).
Every model is built and exported with clean pivot names (no ".001" suffixes): the previous model's objects are
renamed out of the way before the next one is built."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp
from lp import mat, empty, cyl, ico, uvs, box, torus, jitter, person, arc

OUT = sys.argv[sys.argv.index("--out") + 1]
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
ERA = sys.argv[sys.argv.index("--era") + 1].split(",") if "--era" in sys.argv else None
PREVIEW_DIR = sys.argv[sys.argv.index("--previewdir") + 1] if "--previewdir" in sys.argv else OUT
lp.reset(11)
R = math.radians

# ---- shared palette
STONE = mat("Stone", (0.52, 0.52, 0.5), 0.85)
HERO_RING = mat("HeroRing", (1.0, 0.82, 0.3), 0.3, 0.6, emit=(1.0, 0.7, 0.15), strength=0.8)
EYE = mat("Eye", (0.02, 0.02, 0.02), 0.3)
SKIN = mat("Skin", (0.78, 0.52, 0.36), 0.7)
SKIN_L = mat("SkinLight", (0.88, 0.66, 0.5), 0.7)
SKIN_T = mat("SkinTan", (0.66, 0.44, 0.3), 0.7)
SKIN_D = mat("SkinDark", (0.42, 0.26, 0.16), 0.7)
HAIR_B = mat("HairBrown", (0.18, 0.1, 0.05), 0.9)
HAIR_K = mat("HairBlack", (0.06, 0.05, 0.05), 0.85)
BLACK = mat("HazBlack", (0.05, 0.05, 0.06), 0.7)
WHITE_P = mat("PaintWhite", (0.95, 0.95, 0.93), 0.6)
BOOT = mat("Boot", (0.16, 0.11, 0.07), 0.8)
BOOT_K = mat("BootBlack", (0.07, 0.07, 0.08), 0.7)
LEATHER = mat("Leather", (0.4, 0.24, 0.12), 0.8)
WOOD = mat("Wood", (0.52, 0.3, 0.12), 0.85)
WOOD_D = mat("WoodDark", (0.3, 0.17, 0.08), 0.85)
STEEL = mat("Steel", (0.42, 0.45, 0.5), 0.45, 0.35)
GUNMETAL = mat("Gunmetal", (0.2, 0.22, 0.25), 0.4, 0.45)
RED_LIGHT = mat("RedLight", (1.0, 0.1, 0.05), 0.4, 0.0, emit=(1.0, 0.05, 0.02), strength=2.5)

# ---- industrial
BRICK = mat("Brick", (0.62, 0.22, 0.14), 0.9)
MORTAR = mat("Mortar", (0.66, 0.6, 0.52), 0.9)
IRON = mat("Iron", (0.22, 0.22, 0.24), 0.55, 0.3)
SOOT = mat("Soot", (0.09, 0.09, 0.1), 0.6, 0.3)
COPPER = mat("Copper", (0.85, 0.4, 0.18), 0.35, 0.5)
BRASS = mat("Brass", (0.88, 0.66, 0.22), 0.32, 0.5)
FURNACE = mat("Furnace", (1.0, 0.3, 0.02), 0.4, 0.0, emit=(1.0, 0.15, 0.0), strength=1.5)
LAMP = mat("LampGlow", (1.0, 0.7, 0.3), 0.4, 0.0, emit=(1.0, 0.7, 0.3), strength=1.3)
STEAM = mat("Steam", (0.92, 0.93, 0.95), 0.95)
KHAKI = mat("Khaki", (0.6, 0.52, 0.32), 0.85)
KHAKI_D = mat("KhakiDark", (0.42, 0.36, 0.22), 0.85)
CAP_BROWN = mat("CapBrown", (0.3, 0.22, 0.14), 0.8)
BURLAP = mat("Burlap", (0.55, 0.45, 0.28), 0.95)
COAL = mat("Coal", (0.06, 0.06, 0.07), 0.5)
SHIRT_C = mat("ShirtCream", (0.86, 0.8, 0.66), 0.85)
DENIM = mat("Denim", (0.2, 0.3, 0.55), 0.85)
DENIM_D = mat("DenimDark", (0.16, 0.2, 0.32), 0.85)
TESLA = mat("TeslaGlow", (0.35, 0.6, 1.0), 0.3, 0.0, emit=(0.2, 0.5, 1.0), strength=1.3)
CERAMIC = mat("Ceramic", (0.92, 0.9, 0.84), 0.35)
SLATE = mat("Slate", (0.18, 0.2, 0.22), 0.7)
AUBURN = mat("HairAuburn", (0.55, 0.18, 0.06), 0.85)
BLOUSE = mat("Blouse", (0.92, 0.9, 0.84), 0.85)
SKIRT = mat("SkirtPlum", (0.4, 0.14, 0.2), 0.85)
RAY = mat("RayGlow", (0.05, 0.8, 0.5), 0.3, 0.0, emit=(0.05, 1.0, 0.6), strength=1.5)
GOGGLE = mat("GoggleLens", (0.4, 0.75, 0.7), 0.15, 0.3)
SOOTSHIRT = mat("SootyShirt", (0.52, 0.5, 0.46), 0.9)
SUSP = mat("Suspenders", (0.6, 0.14, 0.1), 0.8)

# ---- modern
CONC = mat("Concrete", (0.36, 0.36, 0.34), 0.9)
CONC_D = mat("ConcreteDark", (0.23, 0.23, 0.22), 0.9)
HAZ_Y = mat("HazardYellow", (0.98, 0.76, 0.08), 0.6)
OLIVE = mat("Olive", (0.34, 0.38, 0.17), 0.75)
OLIVE_D = mat("OliveDark", (0.22, 0.25, 0.11), 0.75)
TAN = mat("DesertTan", (0.78, 0.66, 0.44), 0.8)
TAN_D = mat("DesertTanDark", (0.6, 0.48, 0.3), 0.8)
CAMO_G = mat("CamoGreen", (0.36, 0.42, 0.22), 0.85)
CAMO_B = mat("CamoBrown", (0.38, 0.28, 0.16), 0.85)
CAMO_K = mat("CamoBlack", (0.14, 0.15, 0.1), 0.85)
SANDBAG = mat("Sandbag", (0.7, 0.62, 0.44), 0.95)
FUEL_RED = mat("FuelRed", (0.75, 0.12, 0.08), 0.55)
SILVER = mat("FireSuit", (0.74, 0.74, 0.72), 0.45, 0.35)
VISOR_GOLD = mat("VisorGold", (0.95, 0.62, 0.12), 0.2, 0.5)
FLAME = mat("Flame", (1.0, 0.3, 0.02), 0.4, 0.0, emit=(1.0, 0.18, 0.0), strength=1.7)
FLAME_Y = mat("FlameCore", (1.0, 0.75, 0.15), 0.4, 0.0, emit=(1.0, 0.5, 0.05), strength=1.7)
STAR_W = mat("StarWhite", (0.95, 0.95, 0.92), 0.6)
MISSILE = mat("MissileWhite", (0.9, 0.9, 0.88), 0.5)
EMP = mat("EmpGlow", (0.2, 0.5, 1.0), 0.2, 0.0, emit=(0.05, 0.35, 1.0), strength=1.4)
SCREEN = mat("TabletScreen", (0.05, 0.6, 0.9), 0.2, 0.0, emit=(0.05, 0.7, 1.0), strength=1.3)
VEST_Y = mat("HiVis", (0.95, 0.85, 0.1), 0.6)
REFLECT = mat("Reflective", (0.85, 0.87, 0.9), 0.3, 0.4)
SHIRT_B = mat("ShirtBlue", (0.3, 0.45, 0.72), 0.85)
PANTS_G = mat("PantsGrey", (0.28, 0.3, 0.34), 0.85)
HARDHAT = mat("HardHat", (0.96, 0.96, 0.94), 0.45)

# ---- digital
WHITE = mat("Composite", (0.84, 0.86, 0.9), 0.4)
WHITE_D = mat("CompositeGrey", (0.72, 0.75, 0.8), 0.4)
CARBON = mat("Carbon", (0.07, 0.07, 0.09), 0.45, 0.3)
CYAN = mat("NeonCyan", (0.0, 0.7, 0.85), 0.3, 0.0, emit=(0.0, 0.8, 1.0), strength=1.6)
MAGENTA = mat("NeonMagenta", (0.85, 0.0, 0.6), 0.3, 0.0, emit=(1.0, 0.0, 0.65), strength=1.6)
ICE = mat("IceGlow", (0.15, 0.6, 1.0), 0.3, 0.0, emit=(0.1, 0.6, 1.0), strength=1.4)
FROST = mat("Frost", (0.55, 0.8, 0.97), 0.25)
JACKET = mat("JacketBlack", (0.08, 0.08, 0.1), 0.6)
PANTS_K = mat("PantsCharcoal", (0.16, 0.16, 0.2), 0.8)
HAIR_M = mat("HairMagenta", (0.95, 0.15, 0.7), 0.6)
VISOR_C = mat("VisorCyan", (0.0, 0.8, 0.9), 0.2, 0.0, emit=(0.0, 0.9, 1.0), strength=1.6)
PILOT = mat("PilotSuit", (0.18, 0.2, 0.26), 0.7)

# ---- data center
DSTEEL = mat("DarkSteel", (0.22, 0.24, 0.27), 0.45, 0.45)
GRATE = mat("GrateDark", (0.08, 0.09, 0.1), 0.6, 0.3)
ORANGE = mat("ResistOrange", (1.0, 0.26, 0.02), 0.6)
ORANGE_D = mat("ResistOrangeWorn", (0.6, 0.16, 0.03), 0.7)
PATCH = mat("PatchOlive", (0.4, 0.42, 0.3), 0.85)
GLASS_K = mat("BlackGlass", (0.03, 0.035, 0.05), 0.12, 0.3)
LED_B = mat("LedBlue", (0.2, 0.5, 1.0), 0.3, 0.0, emit=(0.05, 0.3, 1.0), strength=1.8)
ARC = mat("ArcGlow", (0.3, 0.6, 1.0), 0.3, 0.0, emit=(0.2, 0.55, 1.0), strength=1.8)
CORE = mat("NovaCore", (0.85, 0.95, 1.0), 0.3, 0.0, emit=(0.5, 0.8, 1.0), strength=1.6)
HOLO_O = mat("HoloOrange", (1.0, 0.2, 0.0), 0.3, 0.0, emit=(1.0, 0.12, 0.0), strength=1.4)
R_SHELL = mat("RobotShellDark", (0.17, 0.18, 0.2), 0.45, 0.15)
R_JOINT = mat("RobotJoint", (0.04, 0.045, 0.055), 0.5, 0.35)
R_GLOW = mat("ReprogrammedGlow", (1.0, 0.35, 0.02), 0.4, 0.0, emit=(1.0, 0.25, 0.0), strength=1.5)
COAT = mat("CoatDark", (0.14, 0.15, 0.16), 0.8)
ARMOR = mat("PatchedArmor", (0.38, 0.4, 0.38), 0.6, 0.3)
HAIR_GREY = mat("HairGrey", (0.22, 0.22, 0.23), 0.9)
SCAR = mat("Scar", (0.62, 0.32, 0.28), 0.7)
HOODIE = mat("Hoodie", (0.13, 0.15, 0.1), 0.9)


# ================================================================== helpers
def rod(parent, material, p0, p1, r, verts=6, r2=None, name=None):
    """Cylinder from p0 to p1 (cone when r2 is given: r at p0, r2 at p1)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    o = cyl(r, d.length, tuple((p0 + p1) / 2), material, parent, verts=verts, r2=r2, name=name)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return o


def strip(body, test):
    """Delete mesh parts of a person() body whose local position matches test(loc)."""
    for o in list(body.children):
        if o.type == "MESH" and test(o.location):
            bpy.data.objects.remove(o, do_unlink=True)


LEFT_ARM = lambda p: p.x > 0.3 and 0.45 < p.z < 0.85
FACE = lambda p: p.y < -0.17 and 1.03 < p.z < 1.27
LEGS = lambda p: p.z < 0.25 and abs(p.x) < 0.2


def left_arm_to(arm, sleeve, skin, hand, r=0.065):
    """Replacement left arm hung on the right-shoulder Arm pivot, reaching from the left shoulder to `hand`."""
    rod(arm, sleeve, (0.6, 0.0, -0.03), hand, r)
    ico(0.075, hand, skin, arm, sub=1)


def kneel_legs(body, cloth, boot, zg):
    """Right knee down, left knee up. zg = ground height in body-local units."""
    rod(body, cloth, (-0.13, 0.0, 0.36), (-0.13, -0.06, zg + 0.07), 0.09)
    rod(body, cloth, (-0.13, -0.06, zg + 0.07), (-0.13, 0.3, zg + 0.07), 0.075)
    box((0.14, 0.12, 0.16), (-0.13, 0.36, zg + 0.08), boot, body, bevel=0.03)
    rod(body, cloth, (0.14, 0.0, 0.36), (0.14, -0.27, 0.4), 0.09)
    rod(body, cloth, (0.14, -0.27, 0.4), (0.14, -0.28, zg + 0.04), 0.075)
    ico(0.1, (0.14, -0.33, zg + 0.04), boot, body, sub=1, scale=(1, 1.4, 0.55))


def seated_legs(body, cloth, boot, zg):
    for s in (-1, 1):
        rod(body, cloth, (s * 0.13, 0.0, 0.33), (s * 0.13, -0.3, 0.33), 0.09)
        rod(body, cloth, (s * 0.13, -0.3, 0.33), (s * 0.13, -0.32, zg + 0.05), 0.075)
        ico(0.1, (s * 0.13, -0.37, zg + 0.04), boot, body, sub=1, scale=(1, 1.4, 0.55))


def peaked_cap(body, crown, band, visor, z=1.3):
    cyl(0.225, 0.1, (0, 0.02, z), band, body, verts=10)
    cyl(0.235, 0.11, (0, 0.03, z + 0.1), crown, body, verts=10, r2=0.27)
    box((0.3, 0.16, 0.03), (0, -0.21, z - 0.03), visor, body, rot=(R(12), 0, 0))


def flat_cap(body, m, z=1.31):
    ico(0.245, (0, 0.0, z), m, body, sub=2, scale=(1.08, 1.15, 0.45))
    box((0.3, 0.16, 0.035), (0, -0.23, z - 0.04), m, body, rot=(R(14), 0, 0))


def hard_hat(body, m, z=1.28):
    ico(0.25, (0, 0.01, z), m, body, sub=2, scale=(1.0, 1.06, 0.8))
    o = cyl(0.29, 0.025, (0, -0.03, z - 0.02), m, body, verts=12)
    o.scale = (1.0, 1.12, 1.0)
    box((0.06, 0.36, 0.035), (0, 0.01, z + 0.18), m, body, bevel=0.015)


def hood(body, m, visor=None):
    ico(0.27, (0, 0.03, 1.2), m, body, sub=2, scale=(1.0, 1.0, 1.12))
    cyl(0.32, 0.22, (0, 0.02, 1.0), m, body, verts=10, r2=0.22)  # hood skirt over the shoulders
    if visor is not None:
        box((0.32, 0.08, 0.14), (0, -0.23, 1.18), visor, body, bevel=0.025)


def star(parent, material, loc, r, rot=(0, 0, 0), depth=0.02):
    """Five-pointed star in local XY (point toward +Y), thickness along +Z."""
    me = bpy.data.meshes.new("Star")
    bm = bmesh.new()
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.4
        pts.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, 0)))
    c = bm.verts.new((0, 0, 0))
    for k in range(10):
        bm.faces.new((c, pts[k], pts[(k + 1) % 10]))
    ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    for v in ext["geom"]:
        if isinstance(v, bmesh.types.BMVert):
            v.co.z += depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("Star", me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    return lp._link(o, material, parent)


def handprint(parent, material, loc, size=1.0, rot=(0, 0, 0)):
    """Hand-painted handprint decal lying in local XY (fingers toward +Y). Returns its empty."""
    h = empty("Handprint", loc, parent)
    h.rotation_euler = rot
    h.scale = (size, size, size)
    ico(0.085, (0, 0, 0), material, h, sub=1, scale=(1.0, 1.05, 0.12))
    for k, (x, ln, a) in enumerate(((-0.06, 0.1, 8), (-0.02, 0.12, 2), (0.025, 0.115, -3), (0.065, 0.09, -10))):
        box((0.032, ln, 0.012), (x, 0.08 + ln / 2, 0), material, h, rot=(0, 0, R(a)))
    box((0.032, 0.09, 0.012), (-0.1, 0.0, 0), material, h, rot=(0, 0, R(50)))  # thumb
    return h


def wheel(parent, rim, spoke, hub, loc, Rr, n=8):
    """Spoked wheel with its axle along X."""
    torus(Rr, 0.05, loc, rim, parent, rot=(0, R(90), 0), major=16, minor=4)
    for k in range(n // 2):
        box((0.04, 0.045, 2 * Rr - 0.04), loc, spoke, parent, rot=(k * 2 * math.pi / n, 0, 0))
    cyl(0.1, 0.12, loc, hub, parent, verts=8, rot=(0, R(90), 0))


def sandbag(parent, loc, rz, m=SANDBAG, size=(0.44, 0.24, 0.17)):
    o = box(size, loc, m, parent, bevel=0.06, rot=(0, 0, rz))
    jitter(o, 0.015)
    return o


def sandbag_ring(parent, Rr, a0, a1, n, layers=2, z0=0.3, m=SANDBAG):
    for L in range(layers):
        cnt = n - (L % 2)
        for i in range(cnt):
            a = R(a0 + (a1 - a0) * (i + 0.5 + 0.5 * (L % 2)) / n)
            sandbag(parent, (math.cos(a) * Rr, math.sin(a) * Rr, z0 + 0.08 + L * 0.15), a + math.pi / 2, m,
                    size=(Rr * R(a1 - a0) / n * 1.02, 0.26, 0.17))


def hazard_ring(parent, c1, c2, r_out=1.33, r_in=1.07, z=0.26, n=26):
    """Flat ring of diagonal hazard stripes on a base top (top surface at z+0.04)."""
    cyl(r_out, 0.04, (0, 0, z + 0.01), c1, parent, verts=16)
    rm = (r_out + r_in) / 2
    ln = (r_out - r_in) / math.sin(R(45)) * 0.92
    for k in range(n):
        a = 2 * math.pi * k / n
        box((0.12, ln, 0.03), (math.cos(a) * rm, math.sin(a) * rm, z + 0.026), c2, parent, rot=(0, 0, a - R(45)))


def hazard_band(parent, c1, c2, r, z, h=0.12, n=16):
    """Vertical band of diagonal hazard stripes around a cylinder of radius r."""
    cyl(r, h, (0, 0, z), c1, parent, verts=16)
    for k in range(n):
        a = 2 * math.pi * k / n
        box((0.03, 0.05, h * 0.95), (math.cos(a) * (r - 0.005), math.sin(a) * (r - 0.005), z), c2, parent,
            rot=(R(40), 0, a))


# ---- era bases (radius ~1.5, top ~0.3)
def iron_base(parent, side=BRICK):
    """Brick plinth with a riveted iron deck plate."""
    cyl(1.55, 0.32, (0, 0, 0.04), side, parent, verts=8)
    for z in (-0.04, 0.06):
        cyl(1.56, 0.015, (0, 0, z), MORTAR, parent, verts=8)
    cyl(1.58, 0.07, (0, 0, 0.18), IRON, parent, verts=8)
    cyl(1.46, 0.1, (0, 0, 0.23), IRON, parent, verts=8)
    for k in range(4):
        a = k * math.pi / 4 + math.pi / 8
        box((0.04, 2.6, 0.02), (0, 0, 0.285), SOOT, parent, rot=(0, 0, a))
    for k in range(16):
        a = k * math.pi / 8 + math.pi / 16
        ico(0.045, (math.cos(a) * 1.3, math.sin(a) * 1.3, 0.28), BRASS, parent, sub=1, scale=(1, 1, 0.6))


def concrete_base(parent, stripes=True):
    cyl(1.55, 0.32, (0, 0, 0.04), CONC_D, parent, verts=8)
    cyl(1.48, 0.08, (0, 0, 0.22), CONC, parent, verts=8)
    if stripes:
        hazard_ring(parent, HAZ_Y, BLACK)
        cyl(1.07, 0.05, (0, 0, 0.285), CONC, parent, verts=16)
    else:
        for k in range(2):
            box((0.03, 2.5, 0.02), (0, 0, 0.265), CONC_D, parent, rot=(0, 0, k * math.pi / 2 + math.pi / 8))
    for k in range(8):  # anchor bolts
        a = k * math.pi / 4 + math.pi / 8
        cyl(0.05, 0.05, (math.cos(a) * 1.38, math.sin(a) * 1.38, 0.27), GUNMETAL, parent, verts=6)


def hex_base(parent, frost=False):
    cyl(1.6, 0.32, (0, 0, 0.04), WHITE, parent, verts=6)
    cyl(1.48, 0.08, (0, 0, 0.22), CARBON, parent, verts=6)
    cyl(0.95, 0.05, (0, 0, 0.275), WHITE_D, parent, verts=6)
    for k in range(6):
        a = k * math.pi / 3
        box((0.06, 1.0, 0.03), (math.cos(a) * 1.18, math.sin(a) * 1.18, 0.27), CYAN, parent, rot=(0, 0, a))
        box((0.02, 0.9, 0.05), (math.cos(a) * 1.395, math.sin(a) * 1.395, 0.08), CYAN, parent, rot=(0, 0, a))
        c = a + math.pi / 6
        box((0.12, 0.12, 0.02), (math.cos(c) * 0.72, math.sin(c) * 0.72, 0.3), CYAN, parent, rot=(0, 0, c))
    if frost:
        for k in range(7):
            a = k * 0.9 + 0.3
            rr = 0.95 + (k % 3) * 0.15
            o = ico(0.32, (math.cos(a) * rr, math.sin(a) * rr, 0.27), FROST, parent, sub=1, scale=(1.3, 1.0, 0.12))
            o.rotation_euler = (0, 0, a)


def grate_base(parent):
    cyl(1.55, 0.32, (0, 0, 0.04), DSTEEL, parent, verts=8)
    cyl(1.47, 0.06, (0, 0, 0.23), GRATE, parent, verts=8)
    hazard_ring(parent, ORANGE, GRATE)
    cyl(1.07, 0.03, (0, 0, 0.275), GRATE, parent, verts=16)
    for i in range(-6, 7):
        x = i * 0.15
        ln = 2 * math.sqrt(max(1.05 ** 2 - x * x, 0.01))
        box((0.04, ln, 0.03), (x, 0, 0.3), STEEL, parent)
    box((2.0, 0.06, 0.035), (0, 0, 0.31), DSTEEL, parent)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        cyl(0.06, 0.05, (math.cos(a) * 1.4, math.sin(a) * 1.4, 0.27), STEEL, parent, verts=6)


def hero_base(parent, color_mat):
    cyl(0.8, 0.22, (0, 0, 0.11), STONE, parent, verts=12)
    torus(0.78, 0.06, (0, 0, 0.23), HERO_RING, parent, major=24)
    cyl(0.7, 0.04, (0, 0, 0.23), color_mat, parent, verts=12)


def team(name, rgb):
    return mat(name + "Team", tuple(rgb), 0.8)


# ================================================================== INDUSTRIAL
def rifleman():
    root = empty("Rifleman")
    iron_base(root)
    # coal sack and coal lumps
    o = ico(0.26, (1.0, 0.72, 0.5), BURLAP, root, sub=2, scale=(1, 0.9, 1.05)); jitter(o, 0.02)
    cyl(0.1, 0.1, (1.0, 0.72, 0.76), BURLAP, root, verts=6, r2=0.05)
    for p in ((0.72, 1.02), (0.85, 1.12), (0.62, 0.92), (0.75, 0.95)):
        o = ico(0.09, (p[0], p[1], 0.34), COAL, root, sub=1); jitter(o, 0.02)
    # gas lamp post
    cyl(0.12, 0.14, (-1.05, 0.72, 0.36), IRON, root, verts=8)
    cyl(0.04, 1.75, (-1.05, 0.72, 1.2), SOOT, root, verts=6)
    box((0.3, 0.05, 0.05), (-1.05, 0.72, 1.95), SOOT, root)
    box((0.2, 0.2, 0.28), (-1.05, 0.72, 2.12), LAMP, root)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box((0.03, 0.03, 0.3), (-1.05 + sx * 0.1, 0.72 + sy * 0.1, 2.12), SOOT, root)
    cyl(0.18, 0.14, (-1.05, 0.72, 2.33), SOOT, root, verts=4, r2=0.02, rot=(0, 0, R(45)))
    # ammo box
    box((0.36, 0.24, 0.2), (0.55, -0.85, 0.4), WOOD, root, bevel=0.02)
    box((0.38, 0.06, 0.04), (0.55, -0.85, 0.5), BRASS, root)
    yaw = empty("Yaw", (0, 0.05, 0.3), root)
    body, arm = person(yaw, (0, 0, 0), SKIN, KHAKI, KHAKI, HAIR_B, scale=1.22, belt=LEATHER, sandal=BOOT)
    strip(body, LEFT_ARM)
    peaked_cap(body, KHAKI_D, LEATHER, LEATHER)
    ico(0.07, (0, -0.19, 1.04), HAIR_B, body, sub=1, scale=(1.4, 0.5, 0.45))  # moustache
    for s in (-1, 1):  # puttees
        cyl(0.095, 0.2, (s * 0.13, 0, 0.13), KHAKI_D, body, verts=6)
    box((0.08, 0.05, 0.66), (0, -0.2, 0.8), LEATHER, body, rot=(0, R(-38), 0))  # bandolier
    for k in range(4):
        box((0.035, 0.03, 0.06), (-0.12 + k * 0.08, -0.235, 0.66 + k * 0.1), BRASS, body, rot=(0, R(-38), 0))
    box((0.24, 0.16, 0.16), (0.18, 0.24, 0.66), LEATHER, body, bevel=0.02)  # pack
    # aiming arm + bolt-action rifle along -Y
    rod(arm, KHAKI, (0, 0, 0), (0.06, -0.3, -0.12), 0.07)
    ico(0.075, (0.08, -0.33, -0.13), SKIN, arm, sub=1)
    box((0.08, 0.36, 0.13), (0.12, -0.08, -0.08), WOOD, arm, bevel=0.02)       # stock
    box((0.07, 0.28, 0.08), (0.12, -0.4, -0.05), IRON, arm)                     # receiver
    box((0.07, 0.52, 0.07), (0.12, -0.78, -0.06), WOOD, arm)                    # forend
    rod(arm, IRON, (0.12, -0.5, -0.02), (0.12, -1.35, -0.02), 0.026)            # barrel
    cyl(0.035, 0.06, (0.12, -1.3, -0.02), IRON, arm, verts=6, rot=(R(90), 0, 0))
    box((0.02, 0.03, 0.05), (0.12, -1.28, 0.03), IRON, arm)                     # front sight
    rod(arm, BRASS, (0.08, -0.38, -0.02), (-0.03, -0.36, -0.04), 0.015)        # bolt handle
    ico(0.025, (-0.04, -0.36, -0.04), BRASS, arm, sub=1)
    left_arm_to(arm, KHAKI, SKIN, (0.14, -0.72, -0.12))
    arm.rotation_euler = (R(-4), 0, 0)
    return root


def steam_brawler():
    root = empty("SteamBrawler")
    iron_base(root, side=IRON)
    # pipes and valve wheel along the back rim
    for p0, p1 in (((-1.15, 0.55, 0.38), (0.0, 1.2, 0.38)), ((0.0, 1.2, 0.38), (1.15, 0.55, 0.38))):
        rod(root, COPPER, p0, p1, 0.07, verts=8)
    for p in ((-1.15, 0.55), (1.15, 0.55), (0.0, 1.2)):
        cyl(0.1, 0.12, (p[0], p[1], 0.38), BRASS, root, verts=8)
    rod(root, COPPER, (1.15, 0.55, 0.32), (1.15, 0.55, 0.95), 0.07, verts=8)
    torus(0.16, 0.025, (1.15, 0.55, 0.98), BRASS, root, major=12, minor=4)
    box((0.3, 0.03, 0.03), (1.15, 0.55, 0.98), BRASS, root)
    box((0.03, 0.3, 0.03), (1.15, 0.55, 0.98), BRASS, root)
    cyl(0.13, 0.05, (-0.9, 0.95, 0.62), CERAMIC, root, verts=12, rot=(R(70), 0, R(40)))  # gauge
    torus(0.13, 0.025, (-0.9, 0.95, 0.62), BRASS, root, rot=(R(70), 0, R(40)), major=12, minor=4)
    rod(root, COPPER, (-0.9, 0.98, 0.35), (-0.9, 0.98, 0.52), 0.03)
    yaw = empty("Yaw", (0, 0.05, 0.3), root)
    body, arm = person(yaw, (0, 0, 0), SKIN, SHIRT_C, DENIM, HAIR_B, scale=1.3, burly=1.22, sandal=BOOT, belt=LEATHER)
    flat_cap(body, CAP_BROWN)
    ico(0.075, (0, -0.19, 1.04), HAIR_B, body, sub=1, scale=(1.6, 0.5, 0.5))  # moustache
    box((0.38, 0.06, 0.3), (0, -0.215, 0.76), DENIM, body, bevel=0.02)  # overall bib
    for s in (-1, 1):
        box((0.06, 0.05, 0.26), (s * 0.13, -0.19, 0.98), DENIM, body, rot=(R(-15), 0, 0))
        ico(0.03, (s * 0.13, -0.25, 0.88), BRASS, body, sub=1)
    # boiler backpack with chimney and steam
    cyl(0.22, 0.6, (0, 0.36, 0.86), COPPER, body, verts=10)
    for z in (0.66, 1.06):
        cyl(0.235, 0.06, (0, 0.36, z), BRASS, body, verts=10)
    ico(0.22, (0, 0.36, 1.16), COPPER, body, sub=1, scale=(1, 1, 0.5))
    box((0.16, 0.05, 0.12), (0, 0.585, 0.82), FURNACE, body)
    cyl(0.065, 0.55, (0.12, 0.42, 1.38), SOOT, body, verts=8)
    cyl(0.07, 0.1, (0.12, 0.42, 1.67), SOOT, body, verts=8, r2=0.11)
    for k, (p, r) in enumerate((((0.13, 0.44, 1.82), 0.1), ((0.08, 0.5, 1.98), 0.13), ((0.18, 0.56, 2.14), 0.15))):
        o = ico(r, p, STEAM, body, sub=1); jitter(o, 0.015)
    rod(body, COPPER, (-0.2, 0.3, 0.98), (-0.36, 0.05, 0.98), 0.04)  # steam line to the gauntlet
    # the big steam gauntlet
    rod(arm, SHIRT_C, (0, 0, 0), (-0.03, -0.1, -0.28), 0.085)
    rod(arm, IRON, (-0.03, -0.1, -0.3), (-0.04, -0.46, -0.44), 0.17, verts=8)
    for t in (0.25, 0.65):
        c = Vector((-0.03, -0.1, -0.3)).lerp(Vector((-0.04, -0.46, -0.44)), t)
        o = rod(arm, BRASS, c - Vector((0, -0.02, 0.008)), c + Vector((0, -0.02, 0.008)), 0.19, verts=8)
    for s in (-1, 1):
        rod(arm, STEEL, (-0.03 + s * 0.17, -0.12, -0.22), (-0.04 + s * 0.17, -0.45, -0.38), 0.03)
    box((0.07, 0.12, 0.04), (-0.21, -0.3, -0.36), FURNACE, arm, rot=(R(-22), 0, 0))
    box((0.4, 0.36, 0.38), (-0.04, -0.66, -0.5), BRASS, arm, bevel=0.05)  # fist
    for k in range(4):
        box((0.085, 0.08, 0.1), (-0.17 + k * 0.088, -0.86, -0.42), IRON, arm, bevel=0.015)
    box((0.1, 0.16, 0.12), (0.17, -0.7, -0.6), BRASS, arm, bevel=0.02)  # thumb
    for x in (-0.16, 0.08):
        ico(0.035, (x, -0.66, -0.3), IRON, arm, sub=1)
    arm.rotation_euler = (R(-12), 0, 0)
    return root


def field_gun():
    root = empty("FieldGun")
    concrete_base(root, stripes=False)
    sandbag_ring(root, 1.3, 25, 155, 7, layers=2, z0=0.28)
    # shell crate
    box((0.48, 0.34, 0.24), (0.86, -0.86, 0.4), WOOD, root, bevel=0.02, rot=(0, 0, R(45)))
    for k in range(3):
        c = (0.86 + (k - 1) * 0.1, -0.86 + (k - 1) * 0.1, 0.62)
        cyl(0.05, 0.22, c, BRASS, root, verts=8)
        cyl(0.05, 0.1, (c[0], c[1], 0.78), IRON, root, verts=8, r2=0.0)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    for s in (-1, 1):
        wheel(yaw, WOOD_D, WOOD, IRON, (s * 0.62, 0.05, 0.45), 0.45, n=10)
        rod(yaw, GUNMETAL, (s * 0.2, 0.1, 0.45), (s * 0.08, 0.92, 0.07), 0.06, verts=4)  # trail legs
    box((0.45, 0.14, 0.14), (0, 0.95, 0.07), GUNMETAL, yaw)
    rod(yaw, IRON, (-0.6, 0.05, 0.45), (0.6, 0.05, 0.45), 0.05, verts=6)  # axle
    box((0.44, 0.3, 0.2), (0, 0.05, 0.55), GUNMETAL, yaw, bevel=0.02)  # carriage
    for s in (-1, 1):  # gun shield halves + lower plate
        box((0.36, 0.05, 0.66), (s * 0.3, -0.25, 0.78), STEEL, yaw, bevel=0.01, rot=(R(-8), 0, 0))
    box((0.26, 0.05, 0.22), (0, -0.23, 0.56), STEEL, yaw, bevel=0.01, rot=(R(-8), 0, 0))
    box((0.98, 0.06, 0.05), (0, -0.21, 1.12), GUNMETAL, yaw, rot=(R(-8), 0, 0))
    arm = empty("Arm", (0, 0.0, 0.8), yaw)
    rod(arm, STEEL, (0, 0.45, 0), (0, -1.15, 0), 0.105, verts=10)
    cyl(0.14, 0.14, (0, -1.12, 0), STEEL, arm, verts=10, rot=(R(90), 0, 0))
    rod(arm, GUNMETAL, (0, 0.3, -0.14), (0, -0.55, -0.14), 0.08, verts=8)  # recoil cylinder
    box((0.28, 0.32, 0.26), (0, 0.5, 0), GUNMETAL, arm, bevel=0.03)          # breech
    for s in (-1, 1):
        cyl(0.07, 0.1, (s * 0.15, 0, 0), IRON, arm, verts=8, rot=(0, R(90), 0))  # trunnions
    arm.rotation_euler = (R(-10), 0, 0)
    # gunner
    body, carm = person(yaw, (0.42, 0.72, 0), SKIN, KHAKI, KHAKI, HAIR_B, scale=0.82, belt=LEATHER, sandal=BOOT)
    carm.name = "CrewArm"
    peaked_cap(body, KHAKI_D, LEATHER, LEATHER)
    rod(carm, KHAKI, (0, 0, 0), (0.05, -0.28, -0.22), 0.065)
    cyl(0.07, 0.3, (0.07, -0.34, -0.25), BRASS, carm, verts=8, rot=(R(80), 0, 0))  # shell in hand
    return root


def tesla_coil():
    root = empty("TeslaCoil")
    iron_base(root)
    # switchboard with gauges and levers
    box((0.6, 0.14, 0.7), (1.0, 0.68, 0.65), SLATE, root, bevel=0.02, rot=(0, 0, R(35)))
    for k, dx in enumerate((-0.15, 0.13)):
        p = (1.0 + dx * math.cos(R(35)) - 0.08 * math.sin(R(35)), 0.68 + dx * math.sin(R(35)) - 0.08 * math.cos(R(35)), 0.82)
        cyl(0.09, 0.03, p, CERAMIC, root, verts=10, rot=(R(90), 0, R(35)))
        torus(0.09, 0.018, p, BRASS, root, rot=(R(90), 0, R(35)), major=10, minor=4)
    for k in range(3):
        dx = -0.15 + k * 0.15
        p = Vector((1.0 + dx * math.cos(R(35)) - 0.1 * math.sin(R(35)), 0.68 + dx * math.sin(R(35)) - 0.1 * math.cos(R(35)), 0.52))
        rod(root, BRASS, p, p + Vector((0, -0.08, 0.16)), 0.015)
        ico(0.035, tuple(p + Vector((0, -0.08, 0.17))), RED_LIGHT if k == 1 else SOOT, root, sub=1)
    rod(root, SOOT, (0.7, 0.5, 0.33), (0.45, 0.3, 0.33), 0.035)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    cyl(0.6, 0.3, (0, 0, 0.15), IRON, yaw, verts=8, r2=0.5)
    cyl(0.52, 0.08, (0, 0, 0.32), BRASS, yaw, verts=8)
    for k in range(3):  # ceramic insulators
        cyl(0.3 - k * 0.02, 0.07, (0, 0, 0.42 + k * 0.1), CERAMIC, yaw, verts=10)
        cyl(0.18, 0.04, (0, 0, 0.47 + k * 0.1), CERAMIC, yaw, verts=10)
    cyl(0.24, 1.15, (0, 0, 1.25), COPPER, yaw, verts=10)
    for k in range(9):
        torus(0.255, 0.035, (0, 0, 0.75 + k * 0.12), COPPER, yaw, major=12, minor=4)
    for z in (0.7, 1.83):
        cyl(0.29, 0.07, (0, 0, z), BRASS, yaw, verts=10)
    cyl(0.07, 0.4, (0, 0, 2.0), BRASS, yaw, verts=8)
    orb = empty("Orb", (0, 0, 2.28), yaw)
    torus(0.48, 0.15, (0, 0, 0), TESLA, orb, major=20, minor=8)
    cyl(0.36, 0.1, (0, 0, 2.28), BRASS, yaw, verts=12)
    ico(0.1, (0, 0, 2.36), BRASS, yaw, sub=1)
    for k in range(3):  # sparks leaping off the toroid
        a = k * 2 * math.pi / 3 + 0.4
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [d * 0.6 + Vector((0, 0, 0.08)), d * 0.72 + Vector((0, 0, 0.3)), d * 0.62 + Vector((0, 0, 0.42)),
               d * 0.78 + Vector((0, 0, 0.62))]
        for i in range(3):
            rod(orb, TESLA, pts[i], pts[i + 1], 0.028, verts=4)
    return root


def ada():
    root = empty("HeroAda")
    hero_base(root, team("Ada", (0.75, 0.5, 0.2)))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body, arm = person(yaw, (0, 0, 0), SKIN_L, BLOUSE, SKIRT, AUBURN, scale=1.24, hair_style="pony", belt=LEATHER, sandal=BOOT)
    box((0.42, 0.05, 0.62), (0, -0.285, 0.6), LEATHER, body, rot=(R(-10), 0, 0))  # apron
    box((0.3, 0.05, 0.2), (0, -0.22, 0.86), LEATHER, body)
    for s in (-1, 1):
        box((0.04, 0.03, 0.3), (s * 0.15, -0.19, 1.0), LEATHER, body, rot=(R(-20), 0, 0))
    # brass goggles pushed up on the head
    cyl(0.235, 0.05, (0, 0.02, 1.3), LEATHER, body, verts=10)
    for s in (-1, 1):
        cyl(0.075, 0.08, (s * 0.085, -0.19, 1.33), BRASS, body, verts=10, rot=(R(80), 0, 0))
        cyl(0.055, 0.02, (s * 0.085, -0.235, 1.34), GOGGLE, body, verts=10, rot=(R(80), 0, 0))
    # tool belt: pouches and wrench
    for s in (-1, 1):
        box((0.12, 0.1, 0.14), (s * 0.3, -0.06, 0.58), LEATHER, body, bevel=0.02)
    box((0.04, 0.03, 0.26), (0.33, 0.06, 0.5), STEEL, body, rot=(0, R(10), 0))
    torus(0.04, 0.015, (0.35, 0.06, 0.36), STEEL, body, rot=(R(90), 0, 0), major=8, minor=4)
    # ray gun held out
    rod(arm, BLOUSE, (0, 0, 0), (0.02, -0.34, -0.08), 0.065)
    ico(0.075, (0.03, -0.38, -0.09), SKIN_L, arm, sub=1)
    box((0.06, 0.08, 0.16), (0.03, -0.42, -0.15), WOOD_D, arm, bevel=0.015)       # grip
    rod(arm, BRASS, (0.03, -0.36, -0.03), (0.03, -0.78, -0.03), 0.075, verts=8)
    uvs(0.13, (0.03, -0.45, 0.04), COPPER, arm, seg=8, rings=5, smooth=False)       # chamber bulb
    ico(0.06, (0.03, -0.45, 0.17), RAY, arm, sub=1)
    for k in range(3):
        cyl(0.12, 0.03, (0.03, -0.58 - k * 0.07, -0.03), COPPER, arm, verts=10, rot=(R(90), 0, 0))
    rod(arm, BRASS, (0.03, -0.78, -0.03), (0.03, -0.9, -0.03), 0.06, r2=0.12, verts=8)
    ico(0.09, (0.03, -0.93, -0.03), RAY, arm, sub=1)
    arm.rotation_euler = (R(-6), 0, 0)
    return root


def jim():
    root = empty("HeroJim")
    hero_base(root, team("Jim", (0.35, 0.3, 0.3)))
    for p in ((0.5, 0.42), (0.6, 0.3), (0.42, 0.55), (0.58, 0.5)):  # coal pile
        o = ico(0.1, (p[0], p[1], 0.3), COAL, root, sub=1); jitter(o, 0.02)
    yaw = empty("Yaw", (0, -0.05, 0.25), root)
    body, arm = person(yaw, (0, 0, 0), SKIN, SOOTSHIRT, DENIM_D, HAIR_B, scale=1.32, burly=1.3,
                       beard=HAIR_B, sandal=BOOT)
    ico(0.17, (0, -0.15, 0.97), HAIR_B, body, sub=1, scale=(1.15, 0.75, 1.1))  # bushy beard
    flat_cap(body, mat("CapGrey", (0.32, 0.3, 0.3), 0.85))
    for s in (-1, 1):  # suspenders
        box((0.055, 0.04, 0.44), (s * 0.12, -0.2, 0.82), SUSP, body)
        box((0.055, 0.04, 0.44), (s * 0.12, 0.2, 0.82), SUSP, body)
        ico(0.028, (s * 0.12, -0.225, 0.62), BRASS, body, sub=1)
    for p in ((0.1, -0.2, 0.92), (-0.12, -0.18, 0.72), (0.2, 0.15, 0.85)):  # soot smudges
        ico(0.06, p, SOOT, body, sub=1, scale=(1, 0.4, 0.7))
    cyl(0.095, 0.1, (0.34, -0.02, 0.62), SOOTSHIRT, body, verts=6)  # rolled sleeve
    # giant sledgehammer raised
    cyl(0.08, 0.42, (0, 0, 0.21), SKIN, arm, verts=6)
    cyl(0.09, 0.1, (0, 0, 0.05), SOOTSHIRT, arm, verts=6)
    ico(0.09, (0, 0, 0.45), SKIN, arm, sub=1)
    cyl(0.04, 0.95, (0, -0.04, 0.72), WOOD, arm, verts=6)
    box((0.6, 0.3, 0.3), (0, -0.04, 1.2), IRON, arm, bevel=0.04)
    for s in (-1, 1):
        box((0.04, 0.32, 0.32), (s * 0.28, -0.04, 1.2), STEEL, arm)
    arm.rotation_euler = (R(-35), 0, R(-8))
    return root


# ================================================================== MODERN
def sniper():
    root = empty("Sniper")
    concrete_base(root, stripes=False)
    # roof corner parapet and antenna
    box((2.0, 0.24, 0.42), (0.05, 1.08, 0.45), CONC, root, bevel=0.02)
    box((0.24, 1.6, 0.42), (1.08, 0.25, 0.45), CONC, root, bevel=0.02)
    box((2.04, 0.28, 0.05), (0.05, 1.08, 0.68), CONC_D, root)
    box((0.28, 1.64, 0.05), (1.08, 0.25, 0.68), CONC_D, root)
    cyl(0.04, 2.1, (1.08, 1.08, 1.75), GUNMETAL, root, verts=6)
    for z, w in ((2.2, 0.4), (2.5, 0.28)):
        box((w, 0.03, 0.03), (1.08, 1.08, z), GUNMETAL, root)
    ico(0.06, (1.08, 1.08, 2.84), RED_LIGHT, root, sub=1)
    sandbag_ring(root, 0.85, -160, 160, 10, layers=2, z0=0.28)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    body, arm = person(yaw, (0, 0.05, -0.15), SKIN_T, CAMO_G, CAMO_G, HAIR_K, scale=1.15, belt=OLIVE_D)
    strip(body, LEFT_ARM)
    strip(body, LEGS)
    kneel_legs(body, CAMO_G, BOOT_K, 0.13)
    for p, m in (((0.12, -0.2, 0.86), CAMO_B), ((-0.14, -0.18, 0.72), CAMO_K), ((0.18, 0.12, 0.9), CAMO_K),
                 ((-0.1, 0.18, 0.75), CAMO_B), ((0.08, -0.28, 0.45), CAMO_B)):
        ico(0.07, p, m, body, sub=1, scale=(1.3, 0.45, 0.8))
    # boonie hat
    cyl(0.33, 0.03, (0, 0.0, 1.29), CAMO_G, body, verts=12)
    cyl(0.22, 0.14, (0, 0.02, 1.36), CAMO_G, body, verts=10, r2=0.19)
    cyl(0.225, 0.04, (0, 0.02, 1.32), CAMO_B, body, verts=10)
    for s in (-1, 1):
        box((0.08, 0.02, 0.025), (s * 0.08, -0.2, 1.13), CAMO_K, body)  # face paint
    # long rifle with scope and bipod
    rod(arm, CAMO_G, (0, 0, 0), (0.06, -0.28, -0.1), 0.07)
    ico(0.075, (0.08, -0.31, -0.11), SKIN_T, arm, sub=1)
    box((0.08, 0.36, 0.14), (0.12, -0.06, -0.08), OLIVE_D, arm, bevel=0.02)
    box((0.08, 0.4, 0.1), (0.12, -0.42, -0.05), GUNMETAL, arm)
    rod(arm, BLACK, (0.12, -0.2, 0.06), (0.12, -0.62, 0.06), 0.05, verts=8)        # scope
    cyl(0.06, 0.06, (0.12, -0.64, 0.06), BLACK, arm, verts=8, rot=(R(90), 0, 0))
    cyl(0.045, 0.01, (0.12, -0.675, 0.06), SCREEN, arm, verts=8, rot=(R(90), 0, 0))
    box((0.07, 0.36, 0.08), (0.12, -0.8, -0.06), OLIVE_D, arm)
    rod(arm, GUNMETAL, (0.12, -0.9, -0.04), (0.12, -1.75, -0.04), 0.03)
    box((0.07, 0.12, 0.07), (0.12, -1.76, -0.04), GUNMETAL, arm)                    # muzzle brake
    for s in (-1, 1):
        rod(arm, GUNMETAL, (0.12, -0.95, -0.08), (0.12 + s * 0.14, -1.02, -0.4), 0.02, verts=4)
    left_arm_to(arm, CAMO_G, SKIN_T, (0.16, -0.25, -0.17))
    arm.rotation_euler = (R(-3), 0, 0)
    return root


def flamethrower():
    root = empty("Flamethrower")
    concrete_base(root)
    for p, m in (((1.0, 0.78), FUEL_RED), ((0.62, 1.08), FUEL_RED), ((-1.05, 0.72), HAZ_Y)):
        cyl(0.21, 0.55, (p[0], p[1], 0.58), m, root, verts=10)
        for z in (0.45, 0.72):
            cyl(0.22, 0.04, (p[0], p[1], z), GUNMETAL, root, verts=10)
        cyl(0.04, 0.04, (p[0] + 0.1, p[1], 0.87), GUNMETAL, root, verts=6)
    yaw = empty("Yaw", (0, 0.05, 0.3), root)
    body, arm = person(yaw, (0, 0, 0), SKIN, SILVER, OLIVE, HAIR_K, scale=1.25, burly=1.12, hair_style="none",
                       belt=OLIVE_D, sandal=BOOT_K)
    strip(body, FACE)
    strip(body, LEFT_ARM)
    hood(body, SILVER, VISOR_GOLD)
    for s in (-1, 1):
        cyl(0.13, 0.62, (s * 0.14, 0.32, 0.85), FUEL_RED, body, verts=10)
        ico(0.13, (s * 0.14, 0.32, 1.16), FUEL_RED, body, sub=1, scale=(1, 1, 0.5))
        cyl(0.135, 0.06, (s * 0.14, 0.32, 0.7), HAZ_Y, body, verts=10)
        cyl(0.03, 0.08, (s * 0.14, 0.32, 1.25), GUNMETAL, body, verts=6)
    box((0.42, 0.06, 0.12), (0, 0.25, 0.62), GUNMETAL, body)
    rod(body, BLACK, (-0.14, 0.32, 0.55), (-0.36, 0.0, 0.6), 0.04)  # hose
    # flame gun at hip height
    rod(arm, SILVER, (0, 0, 0), (0.06, -0.12, -0.36), 0.075)
    ico(0.08, (0.07, -0.15, -0.4), SILVER, arm, sub=1)
    rod(arm, BLACK, (-0.05, 0.05, -0.36), (0.07, -0.18, -0.42), 0.04)
    rod(arm, GUNMETAL, (0.1, -0.05, -0.38), (0.1, -0.95, -0.38), 0.06, verts=8)
    cyl(0.075, 0.28, (0.1, -0.35, -0.5), FUEL_RED, arm, verts=8, rot=(R(90), 0, 0))
    box((0.05, 0.08, 0.16), (0.1, -0.2, -0.48), BLACK, arm)
    rod(arm, GUNMETAL, (0.1, -0.95, -0.38), (0.1, -1.08, -0.38), 0.07, r2=0.1, verts=8)
    rod(arm, FLAME, (0.1, -1.08, -0.38), (0.1, -1.42, -0.36), 0.11, r2=0.0, verts=8)
    rod(arm, FLAME_Y, (0.1, -1.08, -0.38), (0.1, -1.26, -0.37), 0.06, r2=0.0, verts=6)
    left_arm_to(arm, SILVER, SILVER, (0.14, -0.55, -0.42))
    arm.rotation_euler = (R(-4), 0, 0)
    return root


def missile_launcher():
    root = empty("MissileLauncher")
    concrete_base(root)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    cyl(0.8, 0.22, (0, 0, 0.11), OLIVE_D, yaw, verts=12)
    cyl(0.84, 0.06, (0, 0, 0.03), GUNMETAL, yaw, verts=12)
    box((0.62, 0.62, 0.38), (0, 0.1, 0.4), OLIVE, yaw, bevel=0.04)
    for s in (-1, 1):
        box((0.12, 0.36, 0.5), (s * 0.4, 0.05, 0.62), OLIVE_D, yaw, bevel=0.02)
    # radar mast
    rod(yaw, GUNMETAL, (0.4, 0.55, 0.3), (0.55, 0.62, 1.6), 0.04)
    dish = empty("Dish", (0.55, 0.62, 1.68), yaw)
    dish.rotation_euler = (R(-60), 0, R(20))
    cyl(0.36, 0.1, (0, 0, 0.0), OLIVE, dish, verts=12, r2=0.1)
    cyl(0.03, 0.3, (0, 0, 0.15), GUNMETAL, dish, verts=5)
    ico(0.05, (0, 0, 0.32), RED_LIGHT, dish, sub=1)
    arm = empty("Arm", (0, 0.05, 0.85), yaw)
    box((0.95, 1.25, 0.82), (0, -0.05, 0.15), OLIVE, arm, bevel=0.05)
    box((0.99, 0.08, 0.86), (0, -0.62, 0.15), OLIVE_D, arm)
    box((0.99, 0.08, 0.86), (0, 0.5, 0.15), OLIVE_D, arm)
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = (sx * 0.23, -0.67, 0.15 + sz * 0.2)
            cyl(0.16, 0.06, p, BLACK, arm, verts=10, rot=(R(90), 0, 0))
            cyl(0.13, 0.22, (p[0], -0.66, p[2]), MISSILE, arm, verts=10, r2=0.0, rot=(R(-90), 0, 0))
            cyl(0.06, 0.06, (p[0], -0.755, p[2]), FUEL_RED, arm, verts=8, r2=0.0, rot=(R(-90), 0, 0))
        star(arm, STAR_W, (sx * 0.502, -0.05, 0.18), 0.22, rot=(R(90), 0, R(sx * 90)), depth=0.015)
    for k in range(5):
        box((0.12 if k % 2 == 0 else 0.12, 0.08, 0.03), (-0.36 + k * 0.18, -0.6, 0.6), HAZ_Y if k % 2 == 0 else BLACK, arm)
    ico(0.05, (0.35, 0.4, 0.6), RED_LIGHT, arm, sub=1)
    arm.rotation_euler = (R(-22), 0, 0)
    return root


def emp_tower():
    root = empty("EmpTower")
    concrete_base(root)
    # ground cables and junction boxes
    for k in range(3):
        a = R(30 + k * 120)
        d = Vector((math.cos(a), math.sin(a), 0))
        rod(root, BLACK, d * 0.6 + Vector((0, 0, 0.33)), d * 1.15 + Vector((0, 0, 0.33)), 0.05)
        box((0.2, 0.2, 0.18), tuple(d * 1.2 + Vector((0, 0, 0.38))), GUNMETAL, root, rot=(0, 0, a))
        ico(0.035, tuple(d * 1.2 + Vector((0, 0, 0.49))), RED_LIGHT, root, sub=1)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    cyl(0.68, 0.9, (0, 0, 0.45), GUNMETAL, yaw, verts=8, r2=0.52)
    hazard_band(yaw, HAZ_Y, BLACK, 0.66, 0.18, h=0.16)
    for k in range(4):  # capacitor stacks
        a = k * math.pi / 2 + math.pi / 4
        p = (math.cos(a) * 0.62, math.sin(a) * 0.62)
        cyl(0.12, 0.7, (p[0], p[1], 0.55), OLIVE, yaw, verts=8)
        cyl(0.13, 0.05, (p[0], p[1], 0.4), BLACK, yaw, verts=8)
        cyl(0.09, 0.05, (p[0], p[1], 0.92), EMP, yaw, verts=8)
        rod(yaw, BLACK, (p[0], p[1], 0.9), (p[0] * 0.55, p[1] * 0.55, 1.05), 0.03)
    cyl(0.4, 0.22, (0, 0, 1.0), OLIVE_D, yaw, verts=10)
    torus(0.46, 0.06, (0, 0, 1.12), GUNMETAL, yaw, major=16, minor=4)
    for k in range(2):
        ico(0.05, (0.36 * (1 if k else -1), -0.36, 0.7), RED_LIGHT, yaw, sub=1)
    orb = empty("Orb", (0, 0, 1.15), yaw)
    uvs(0.42, (0, 0, 0.0), EMP, orb, seg=14, rings=8, scale=(1, 1, 0.85), smooth=False)
    for k in range(4):
        a = k * math.pi / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        rod(yaw, GUNMETAL, d * 0.38 + Vector((0, 0, 1.05)), d * 0.62 + Vector((0, 0, 1.6)), 0.035)
        ico(0.07, tuple(d * 0.64 + Vector((0, 0, 0.5))), EMP, orb, sub=1)
    return root


def maya():
    root = empty("HeroMaya")
    hero_base(root, team("Maya", (0.4, 0.45, 0.25)))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body, arm = person(yaw, (0, 0, 0), SKIN, TAN, TAN_D, HAIR_B, scale=1.25, hair_style="pony", belt=OLIVE_D, sandal=BOOT)
    strip(body, LEFT_ARM)
    for p, m in (((0.14, -0.15, 0.6), CAMO_B), ((-0.12, -0.25, 0.42), TAN_D), ((0.08, 0.2, 0.5), CAMO_B)):
        ico(0.07, p, m, body, sub=1, scale=(1.3, 0.45, 0.8))
    box((0.44, 0.38, 0.36), (0, -0.02, 0.8), OLIVE, body, bevel=0.05)  # plate carrier
    for k in range(3):
        box((0.1, 0.06, 0.12), (-0.12 + k * 0.12, -0.23, 0.72), OLIVE_D, body, bevel=0.015)
    # helmet with goggles
    ico(0.255, (0, 0.02, 1.29), OLIVE, body, sub=2, scale=(1.06, 1.1, 0.74))
    cyl(0.27, 0.03, (0, 0.02, 1.24), OLIVE_D, body, verts=12)
    box((0.42, 0.05, 0.05), (0, -0.2, 1.35), BLACK, body, rot=(R(-20), 0, 0))
    for s in (-1, 1):
        cyl(0.065, 0.06, (s * 0.09, -0.23, 1.37), BLACK, body, verts=8, rot=(R(70), 0, 0))
        cyl(0.05, 0.02, (s * 0.09, -0.26, 1.38), VISOR_GOLD, body, verts=8, rot=(R(70), 0, 0))
    # radio pack + antenna
    box((0.34, 0.2, 0.42), (0, 0.3, 0.8), OLIVE_D, body, bevel=0.03)
    box((0.12, 0.04, 0.08), (-0.06, 0.41, 0.9), BLACK, body)
    rod(body, BLACK, (0.1, 0.36, 1.0), (0.18, 0.42, 1.85), 0.014, verts=4)
    ico(0.03, (0.18, 0.42, 1.86), RED_LIGHT, body, sub=1)
    # assault rifle
    rod(arm, TAN, (0, 0, 0), (0.06, -0.28, -0.14), 0.07)
    ico(0.075, (0.08, -0.31, -0.15), SKIN, arm, sub=1)
    box((0.07, 0.26, 0.13), (0.12, -0.04, -0.1), TAN_D, arm, bevel=0.02)
    box((0.08, 0.36, 0.12), (0.12, -0.32, -0.08), BLACK, arm, bevel=0.01)
    box((0.06, 0.1, 0.22), (0.12, -0.38, -0.22), BLACK, arm, rot=(R(-15), 0, 0))  # magazine
    box((0.08, 0.32, 0.09), (0.12, -0.64, -0.08), TAN_D, arm)
    rod(arm, BLACK, (0.12, -0.78, -0.07), (0.12, -1.02, -0.07), 0.022)
    box((0.06, 0.12, 0.07), (0.12, -0.32, 0.02), BLACK, arm)                        # optic
    cyl(0.025, 0.01, (0.12, -0.385, 0.02), RED_LIGHT, arm, verts=6, rot=(R(90), 0, 0))
    left_arm_to(arm, TAN, SKIN, (0.14, -0.62, -0.15))
    arm.rotation_euler = (R(-4), 0, 0)
    return root


def ken():
    root = empty("HeroKen")
    hero_base(root, team("Ken", (0.9, 0.85, 0.2)))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body, arm = person(yaw, (0, 0, 0), SKIN_L, SHIRT_B, PANTS_G, HAIR_K, scale=1.22, belt=BLACK, sandal=BOOT_K)
    ico(0.285, (0, 0, 0.79), VEST_Y, body, sub=2, scale=(1.0, 0.82, 0.92))  # hi-vis vest
    for z in (0.68, 0.84):
        box((0.5, 0.03, 0.045), (0, -0.215, z), REFLECT, body)
    box((0.04, 0.03, 0.4), (0, -0.235, 0.76), SHIRT_B, body)
    hard_hat(body, HARDHAT)
    for s in (-1, 1):  # glasses
        torus(0.055, 0.014, (s * 0.08, -0.21, 1.19), BLACK, body, rot=(R(90), 0, 0), major=8, minor=4)
    box((0.06, 0.02, 0.015), (0, -0.21, 1.2), BLACK, body)
    # tablet held up
    rod(arm, SHIRT_B, (0, 0, 0), (0.06, -0.24, -0.26), 0.065)
    ico(0.075, (0.08, -0.27, -0.28), SKIN_L, arm, sub=1)
    tab = empty("Tablet", (0.2, -0.34, -0.22), arm)
    tab.rotation_euler = (R(-40), 0, 0)
    box((0.42, 0.3, 0.035), (0, 0, 0), BLACK, tab, bevel=0.01)
    box((0.36, 0.24, 0.01), (0, 0, 0.02), SCREEN, tab)
    # hovering drone by his left shoulder
    dr = empty("Drone", (0.62, 0.15, 1.85), yaw)
    box((0.2, 0.2, 0.08), (0, 0, 0), GUNMETAL, dr, bevel=0.02)
    ico(0.05, (0, -0.1, -0.03), SCREEN, dr, sub=1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            rod(dr, BLACK, (0, 0, 0), (sx * 0.2, sy * 0.2, 0.02), 0.015, verts=4)
            cyl(0.1, 0.012, (sx * 0.2, sy * 0.2, 0.05), mat("Rotor", (0.75, 0.78, 0.8), 0.4), dr, verts=10)
    ico(0.025, (0.1, 0.1, 0.05), RED_LIGHT, dr, sub=1)
    arm.rotation_euler = (R(-5), 0, 0)
    return root


# ================================================================== DIGITAL
def laser_turret():
    root = empty("LaserTurret")
    hex_base(root)
    cyl(0.62, 0.3, (0, 0, 0.45), WHITE, root, verts=6)
    cyl(0.45, 0.8, (0, 0, 0.95), WHITE_D, root, verts=6, r2=0.34)
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 6
        box((0.04, 0.03, 0.62), (math.cos(a) * 0.4, math.sin(a) * 0.4, 0.95), CYAN, root, rot=(0, R(-7), a))
    cyl(0.4, 0.08, (0, 0, 1.38), CARBON, root, verts=12)
    yaw = empty("Yaw", (0, 0, 1.42), root)
    uvs(0.5, (0, 0.05, 0.22), WHITE, yaw, seg=12, rings=7, scale=(1.0, 1.25, 0.62), smooth=False)
    box((0.8, 0.9, 0.06), (0, 0.05, 0.12), CARBON, yaw)
    box((0.22, 0.8, 0.06), (0, 0.12, 0.52), CARBON, yaw, bevel=0.02)
    box((0.06, 0.6, 0.065), (0, 0.15, 0.53), CYAN, yaw)
    for s in (-1, 1):
        box((0.04, 0.5, 0.12), (s * 0.5, 0.05, 0.25), CARBON, yaw)
        box((0.04, 0.3, 0.04), (s * 0.51, 0.05, 0.25), CYAN, yaw)
    box((0.34, 0.06, 0.08), (0, -0.56, 0.36), CYAN, yaw)  # sensor eye
    arm = empty("Arm", (0, -0.3, 0.2), yaw)
    for s in (-1, 1):
        box((0.2, 0.36, 0.22), (s * 0.24, -0.15, 0), WHITE, arm, bevel=0.04)
        rod(arm, CARBON, (s * 0.24, -0.2, 0), (s * 0.24, -1.25, 0), 0.09, verts=8)
        for y in (-0.5, -0.72, -0.94):
            cyl(0.12, 0.06, (s * 0.24, y, 0), CYAN, arm, verts=8, rot=(R(90), 0, 0))
        cyl(0.11, 0.08, (s * 0.24, -1.2, 0), WHITE, arm, verts=8, rot=(R(90), 0, 0))
        cyl(0.07, 0.08, (s * 0.24, -1.27, 0), CYAN, arm, verts=8, rot=(R(90), 0, 0))
    arm.rotation_euler = (R(-4), 0, 0)
    return root


def mech_brawler():
    root = empty("MechBrawler")
    hex_base(root)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    for s in (-1, 1):  # legs
        box((0.26, 0.42, 0.14), (s * 0.34, -0.05, 0.07), CARBON, yaw, bevel=0.03)
        rod(yaw, WHITE, (s * 0.34, -0.02, 0.12), (s * 0.34, -0.12, 0.5), 0.13, verts=6, r2=0.1)
        ico(0.12, (s * 0.34, -0.12, 0.52), CARBON, yaw, sub=1)
        box((0.24, 0.3, 0.38), (s * 0.34, -0.02, 0.76), WHITE, yaw, bevel=0.04, rot=(R(-12), 0, 0))
        box((0.04, 0.2, 0.04), (s * 0.465, -0.04, 0.76), MAGENTA, yaw)
    box((0.62, 0.42, 0.22), (0, 0.04, 0.95), CARBON, yaw, bevel=0.04)  # pelvis
    box((1.0, 0.8, 0.62), (0, 0.06, 1.35), WHITE, yaw, bevel=0.08)      # torso
    box((0.86, 0.06, 0.2), (0, -0.35, 1.12), CARBON, yaw)
    for k in range(3):
        box((0.6, 0.02, 0.025), (0, -0.385, 1.06 + k * 0.06), MAGENTA, yaw)
    box((0.52, 0.3, 0.3), (0, 0.4, 1.45), CARBON, yaw, bevel=0.04)       # backpack reactor
    cyl(0.1, 0.06, (0, 0.56, 1.45), MAGENTA, yaw, verts=10, rot=(R(90), 0, 0))
    # open cockpit with visible pilot and a canopy frame
    box((0.6, 0.5, 0.12), (0, -0.04, 1.68), CARBON, yaw)
    pil = empty("Pilot", (0, 0.0, 1.72), yaw)
    ico(0.2, (0, 0.02, 0.12), PILOT, pil, sub=2, scale=(1.1, 0.85, 0.9))
    ico(0.15, (0, 0, 0.36), SKIN_L, pil, sub=2)
    ico(0.165, (0, 0.03, 0.4), WHITE, pil, sub=2, scale=(1, 1, 0.9))
    box((0.24, 0.06, 0.07), (0, -0.13, 0.37), MAGENTA, pil)
    for a in (-45, 0, 45):
        parts = arc(yaw, CARBON, (0, 0, 0), 0.42, 0.025, 10, 170, segs=6, plane="xz", verts=4)
        hub = empty("Frame", (0, -0.0, 1.72), yaw)
        hub.rotation_euler = (0, 0, R(90 + a))
        for p in parts:
            p.parent = hub
    torus(0.42, 0.03, (0, 0, 1.75), CYAN, yaw, major=16, minor=4)
    # both arms on the Arm pivot: double-fist slam
    arm = empty("Arm", (0, 0.06, 1.5), yaw)
    for s in (-1, 1):
        box((0.36, 0.48, 0.38), (s * 0.66, 0.0, 0.08), WHITE, arm, bevel=0.06)          # shoulder
        box((0.04, 0.3, 0.04), (s * 0.85, 0.0, 0.12), MAGENTA, arm)
        rod(arm, CARBON, (s * 0.68, 0, -0.05), (s * 0.7, -0.08, -0.42), 0.09)
        ico(0.11, (s * 0.7, -0.1, -0.45), CARBON, arm, sub=1)
        box((0.32, 0.52, 0.32), (s * 0.7, -0.32, -0.5), WHITE, arm, bevel=0.05)        # forearm
        box((0.34, 0.06, 0.06), (s * 0.7, -0.32, -0.32), CARBON, arm)
        box((0.4, 0.34, 0.38), (s * 0.7, -0.72, -0.52), MAGENTA, arm, bevel=0.06)      # glowing fist
        for k in range(3):
            box((0.09, 0.06, 0.32), (s * 0.7 + (k - 1) * 0.12, -0.9, -0.52), CARBON, arm)
    arm.rotation_euler = (R(-8), 0, 0)
    return root


def plasma_mortar():
    root = empty("PlasmaMortar")
    hex_base(root)
    # ammo pods rack
    rack = empty("Rack", (0.95, 0.75, 0.3), root)
    rack.rotation_euler = (0, 0, R(-35))
    box((0.7, 0.32, 0.1), (0, 0, 0.05), CARBON, rack, bevel=0.02)
    for k in range(3):
        uvs(0.12, ((k - 1) * 0.22, 0, 0.24), WHITE, rack, seg=8, rings=6, scale=(1, 1, 1.5), smooth=False)
        ico(0.06, ((k - 1) * 0.22, 0, 0.44), MAGENTA, rack, sub=1)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    cyl(0.82, 0.16, (0, 0, 0.08), CARBON, yaw, verts=12)
    cyl(0.7, 0.05, (0, 0, 0.18), WHITE, yaw, verts=12)
    torus(0.76, 0.025, (0, 0, 0.17), MAGENTA, yaw, major=24, minor=4)
    for s in (-1, 1):
        box((0.14, 0.7, 0.72), (s * 0.44, 0.0, 0.52), WHITE, yaw, bevel=0.04)
        box((0.02, 0.4, 0.04), (s * 0.515, 0.0, 0.72), MAGENTA, yaw)
        for k in range(3):  # heat vents
            box((0.03, 0.4, 0.05), (s * 0.52, 0.02, 0.38 + k * 0.09), CARBON, yaw)
    arm = empty("Arm", (0, 0.05, 0.62), yaw)
    tube = empty("Tube", (0, 0, 0), arm)
    tube.rotation_euler = (R(36), 0, 0)
    ico(0.32, (0, 0, -0.05), CARBON, tube, sub=2, scale=(1, 1, 0.8))
    cyl(0.27, 1.3, (0, 0, 0.55), CARBON, tube, verts=10)
    cyl(0.31, 0.5, (0, 0, 0.2), WHITE, tube, verts=10)
    cyl(0.34, 0.16, (0, 0, 1.2), WHITE, tube, verts=10)
    cyl(0.22, 0.03, (0, 0, 1.275), MAGENTA, tube, verts=10)
    for z in (0.6, 0.78, 0.96):
        torus(0.28, 0.04, (0, 0, z), MAGENTA, tube, major=14, minor=4)
    for s in (-1, 1):
        box((0.06, 0.06, 0.5), (s * 0.31, 0.0, 0.2), MAGENTA, tube)
        cyl(0.07, 0.16, (s * 0.38, 0, 0), CARBON, arm, verts=8, rot=(0, R(90), 0))
    arm.rotation_euler = (R(-4), 0, 0)
    return root


def cryo_field():
    root = empty("CryoField")
    hex_base(root, frost=True)
    for k in range(6):  # ice crystals around the pad
        a = k * math.pi / 3 + 0.4
        rr = 1.12
        for j, (dr, h, tilt) in enumerate(((0, 0.55, 15), (0.12, 0.35, 35))):
            p = (math.cos(a + j * 0.25) * (rr + dr), math.sin(a + j * 0.25) * (rr + dr), 0.28 + h / 2 - 0.05)
            o = cyl(0.09, h, p, ICE if j == 0 else FROST, root, verts=5, r2=0.0)
            o.rotation_euler = (R(tilt) * math.sin(a), -R(tilt) * math.cos(a), 0)
            o.rotation_euler = (-R(tilt) * math.sin(a), R(tilt) * math.cos(a), 0)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    cyl(0.62, 0.3, (0, 0, 0.15), WHITE, yaw, verts=8)
    cyl(0.46, 1.4, (0, 0, 0.95), CARBON, yaw, verts=8)
    for k in range(4):
        a = k * math.pi / 2
        box((0.1, 0.42, 1.1), (math.cos(a) * 0.45, math.sin(a) * 0.45, 0.95), WHITE, yaw, bevel=0.02, rot=(0, 0, a))
    for z in (0.35, 1.62):
        cyl(0.56, 0.1, (0, 0, z), WHITE_D, yaw, verts=8)
    for k in range(4):  # vapor vents
        a = k * math.pi / 2 + math.pi / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        box((0.2, 0.06, 0.26), tuple(d * 0.5 + Vector((0, 0, 0.6))), CARBON, yaw, rot=(0, 0, a + math.pi / 2))
        for j, rr in enumerate((0.08, 0.11)):
            ico(rr, tuple(d * (0.62 + j * 0.13) + Vector((0, 0, 0.62 + j * 0.12))), STEAM, yaw, sub=1)
    cyl(0.4, 0.3, (0, 0, 1.82), WHITE_D, yaw, verts=8, r2=0.22)
    orb = empty("Orb", (0, 0, 1.15), yaw)
    torus(0.72, 0.1, (0, 0, 0), ICE, orb, major=20, minor=6)
    cyl(0.52, 0.18, (0, 0, 0), ICE, orb, verts=8)
    for k in range(4):
        a = k * math.pi / 2
        box((0.24, 0.05, 0.05), (math.cos(a) * 0.62, math.sin(a) * 0.62, 0), CARBON, orb, rot=(0, 0, a))
    for k, (a, h, t) in enumerate(((0, 0.7, 0), (2.1, 0.5, 25), (4.2, 0.45, 28), (1.0, 0.4, 32))):  # crystal crown
        o = cyl(0.12, h, (math.cos(a) * 0.1 * (k > 0), math.sin(a) * 0.1 * (k > 0), 1.95 + h / 2), ICE, yaw, verts=5, r2=0.0)
        o.rotation_euler = (-R(t) * math.sin(a), R(t) * math.cos(a), 0)
    return root


def nova():
    root = empty("HeroNova")
    hero_base(root, team("Nova", (0.9, 0.2, 0.8)))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body, arm = person(yaw, (0, 0, 0), SKIN_L, JACKET, PANTS_K, HAIR_M, scale=1.24, hair_style="none", belt=MAGENTA,
                       sandal=BOOT_K)
    strip(body, lambda p: p.y < -0.18 and 1.17 < p.z < 1.22)  # eyes under the visor
    # undercut: shaved side + long magenta sweep on top
    ico(0.225, (0, 0.03, 1.21), HAIR_K, body, sub=2, scale=(1.03, 0.98, 0.72))
    ico(0.2, (0.05, 0.0, 1.32), HAIR_M, body, sub=1, scale=(0.75, 1.15, 0.55))
    box((0.16, 0.12, 0.26), (0.14, -0.13, 1.28), HAIR_M, body, bevel=0.03, rot=(R(10), R(-20), 0))
    box((0.42, 0.06, 0.07), (0, -0.19, 1.19), VISOR_C, body, bevel=0.015)
    for s in (-1, 1):
        box((0.04, 0.24, 0.05), (s * 0.21, -0.08, 1.19), CARBON, body)
    # jacket details with neon trim
    cyl(0.2, 0.1, (0, 0.0, 1.0), JACKET, body, verts=8, r2=0.18)
    box((0.03, 0.02, 0.42), (0.05, -0.22, 0.78), CYAN, body)
    torus(0.27, 0.02, (0, 0, 0.56), MAGENTA, body, major=12, minor=4)
    for s in (-1, 1):
        box((0.12, 0.2, 0.04), (s * 0.27, 0, 1.0), CYAN, body, rot=(0, R(s * 20), 0))
    cyl(0.085, 0.42, (0.34, 0, 0.76), JACKET, body, verts=6, rot=(0, R(-10), 0))  # left sleeve
    box((0.3, 0.02, 0.2), (0.55, -0.25, 0.95), MAGENTA, body, rot=(0, 0, R(-20)))  # floating holo screen
    # laser pistol
    rod(arm, JACKET, (0, 0, 0), (0.02, -0.34, -0.08), 0.07)
    ico(0.075, (0.03, -0.38, -0.09), SKIN_L, arm, sub=1)
    box((0.06, 0.08, 0.15), (0.03, -0.41, -0.15), CARBON, arm, bevel=0.015)
    box((0.1, 0.48, 0.14), (0.03, -0.58, -0.03), WHITE, arm, bevel=0.03)
    box((0.105, 0.36, 0.035), (0.03, -0.6, 0.03), CYAN, arm)
    rod(arm, CARBON, (0.03, -0.8, -0.04), (0.03, -0.92, -0.04), 0.045)
    ico(0.065, (0.03, -0.95, -0.04), CYAN, arm, sub=1)
    arm.rotation_euler = (R(-6), 0, 0)
    return root


def glitch():
    root = empty("HeroGlitch")
    hero_base(root, team("Glitch", (0.2, 0.9, 0.9)))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body = empty("Body", (0, 0, 0), yaw)
    body.scale = (1.25, 1.25, 1.25)
    for s in (-1, 1):
        box((0.13, 0.22, 0.07), (s * 0.12, -0.04, 0.035), CARBON, body, bevel=0.02)
        rod(body, WHITE, (s * 0.12, 0, 0.06), (s * 0.12, 0, 0.3), 0.06, r2=0.075)
        ico(0.06, (s * 0.12, -0.01, 0.31), CARBON, body, sub=1)
        rod(body, WHITE, (s * 0.12, 0, 0.32), (s * 0.12, 0, 0.56), 0.075, r2=0.09)
        box((0.02, 0.02, 0.2), (s * 0.12, -0.08, 0.44), CYAN, body)
    box((0.3, 0.18, 0.14), (0, 0, 0.6), CARBON, body, bevel=0.03)
    ico(0.22, (0, 0, 0.86), WHITE, body, sub=2, scale=(1.05, 0.72, 1.05))      # chest
    box((0.22, 0.14, 0.14), (0, 0, 0.66), WHITE_D, body, bevel=0.03)            # waist
    box((0.025, 0.02, 0.36), (0, -0.165, 0.86), CYAN, body)
    for s in (-1, 1):
        box((0.02, 0.02, 0.26), (s * 0.12, -0.14, 0.86), CYAN, body, rot=(0, R(s * 12), 0))
    ico(0.05, (0, -0.16, 0.95), CYAN, body, sub=1)
    cyl(0.05, 0.12, (0, 0, 1.08), CARBON, body, verts=6)
    # head with cracked face plate
    uvs(0.17, (0, 0, 1.24), WHITE, body, seg=10, rings=7, scale=(0.95, 1.0, 1.15), smooth=False)
    box((0.26, 0.04, 0.12), (0, -0.155, 1.25), CARBON, body, bevel=0.015)
    box((0.07, 0.02, 0.03), (-0.06, -0.18, 1.26), CYAN, body)
    box((0.07, 0.02, 0.03), (0.06, -0.18, 1.26), CYAN, body)
    for p0, p1 in (((0.04, -0.165, 1.4), (0.08, -0.172, 1.33)), ((0.08, -0.172, 1.33), (0.05, -0.18, 1.3)),
                   ((0.08, -0.172, 1.33), (0.13, -0.15, 1.31))):
        rod(body, BLACK, p0, p1, 0.011, verts=4)
    rod(body, CYAN, (0.0, 0.0, 1.38), (0.0, 0.05, 1.5), 0.015, verts=4)  # antenna
    ico(0.03, (0, 0.05, 1.51), CYAN, body, sub=1)
    # left arm hangs
    ico(0.07, (0.24, 0, 0.98), CARBON, body, sub=1)
    rod(body, WHITE, (0.25, 0, 0.96), (0.28, 0, 0.72), 0.055)
    ico(0.05, (0.28, 0, 0.7), CARBON, body, sub=1)
    rod(body, WHITE, (0.28, 0, 0.68), (0.3, -0.04, 0.47), 0.05)
    box((0.02, 0.02, 0.16), (0.3, -0.06, 0.58), CYAN, body)
    ico(0.055, (0.3, -0.05, 0.43), CARBON, body, sub=1)
    # energy blade arm raised
    ico(0.07, (-0.24, 0, 0.98), CARBON, body, sub=1)
    arm = empty("Arm", (-0.25, 0, 0.98), body)
    rod(arm, WHITE, (0, 0, 0), (0, 0, 0.24), 0.055)
    ico(0.05, (0, 0, 0.26), CARBON, arm, sub=1)
    rod(arm, WHITE, (0, 0, 0.28), (0, -0.02, 0.48), 0.06, r2=0.075)
    cyl(0.09, 0.06, (0, -0.02, 0.5), CYAN, arm, verts=8)
    box((0.05, 0.2, 0.95), (0, -0.04, 1.0), CYAN, arm)                       # blade
    cyl(0.1, 0.16, (0, -0.04, 1.55), CYAN, arm, verts=4, r2=0.0, rot=(0, 0, R(45)))
    arm.rotation_euler = (R(-35), 0, 0)
    return root


# ================================================================== DATA CENTER
def arc_cannon():
    root = empty("ArcCannon")
    grate_base(root)
    sandbag_ring(root, 1.28, 30, 150, 6, layers=2, z0=0.3, m=PATCH)
    for p0, p1, p2 in (((-1.25, 0.2, 0.33), (-0.8, -0.3, 0.33), (-0.35, -0.1, 0.33)),
                       ((1.2, -0.5, 0.33), (0.7, -0.4, 0.33), (0.35, 0.05, 0.33))):
        rod(root, BLACK, p0, p1, 0.04)
        rod(root, BLACK, p1, p2, 0.04)
    box((0.3, 0.24, 0.24), (-1.2, 0.25, 0.42), DSTEEL, root, bevel=0.02, rot=(0, 0, R(20)))
    ico(0.04, (-1.2, 0.12, 0.5), LED_B, root, sub=1)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    cyl(0.45, 0.25, (0, 0, 0.12), DSTEEL, yaw, verts=8)
    cyl(0.2, 0.55, (0, 0, 0.5), STEEL, yaw, verts=8)
    cyl(0.5, 0.1, (0, 0, 0.78), DSTEEL, yaw, verts=10)
    box((0.95, 1.0, 0.55), (0, 0.15, 1.1), ORANGE, yaw, bevel=0.06)
    for p, sz, m in (((0.48, 0.25, 1.15), (0.03, 0.36, 0.3), PATCH), ((-0.48, 0.0, 1.05), (0.03, 0.3, 0.26), STEEL),
                     ((0.15, 0.4, 1.38), (0.36, 0.3, 0.03), DSTEEL)):
        box(sz, p, m, yaw)
        for dx in (-1, 1):
            for dz in (-1, 1):
                q = Vector(p) + Vector((0.02 * (sz[0] < 0.1) * (1 if p[0] > 0 else -1), 0, 0))
                ico(0.022, (q.x + (dx * sz[0] * 0.4 if sz[0] > 0.1 else 0),
                            q.y + dx * sz[1] * 0.4, q.z + (dz * sz[2] * 0.4 if sz[2] > 0.1 else 0.02)), STEEL, yaw, sub=1)
    box((0.3, 0.3, 0.4), (-0.3, 0.6, 1.0), DSTEEL, yaw, bevel=0.03)  # battery pack
    box((0.05, 0.2, 0.06), (-0.46, 0.6, 1.1), LED_B, yaw)
    rod(yaw, STEEL, (0.3, 0.55, 1.35), (0.35, 0.65, 2.3), 0.025, verts=4)  # antenna + rag flag
    box((0.02, 0.26, 0.14), (0.35, 0.78, 2.2), ORANGE, yaw)
    arm = empty("Arm", (0, -0.2, 1.15), yaw)
    rod(arm, DSTEEL, (0, 0.3, 0), (0, -1.2, 0), 0.1, verts=8)
    box((0.42, 0.4, 0.36), (0, 0.05, 0), DSTEEL, arm, bevel=0.04)
    for k in range(6):
        torus(0.17, 0.055, (0, -0.32 - k * 0.14, 0), COPPER, arm, rot=(R(90), 0, 0), major=12, minor=4)
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        p0 = Vector((math.cos(a) * 0.12, -1.15, math.sin(a) * 0.12))
        rod(arm, COPPER, p0, p0 + Vector((math.cos(a) * 0.08, -0.2, math.sin(a) * 0.08)), 0.03, verts=5)
    ico(0.11, (0, -1.3, 0), ARC, arm, sub=1)
    for k in range(4):  # crackling arcs
        a = k * math.pi / 2 + 0.3
        d = Vector((math.cos(a), 0, math.sin(a)))
        p0 = Vector((0, -1.3, 0)) + d * 0.1
        p1 = Vector((0, -1.4, 0)) + d * 0.22 + Vector((0, 0, 0.05))
        p2 = Vector((0, -1.48, 0)) + d * 0.3
        rod(arm, ARC, p0, p1, 0.018, verts=4)
        rod(arm, ARC, p1, p2, 0.018, verts=4)
    arm.rotation_euler = (R(-6), 0, 0)
    return root


def rleg(parent, hip, thigh, shin, foot, length):
    p = empty("Leg", hip, parent)
    box(thigh, (0, 0, -thigh[2] / 2), R_SHELL, p, bevel=0.03)
    cyl(shin, length - thigh[2], (0, 0, -thigh[2] - (length - thigh[2]) / 2 + 0.02), R_JOINT, p, verts=6)
    box(foot, (0, -0.04, -length + foot[2] / 2), STEEL, p, bevel=0.02)
    return p


def titan_mech():
    root = empty("TitanMech")
    grate_base(root)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    body = empty("Body", (0, 0, 0), yaw)
    body.scale = (1.5, 1.5, 1.45)
    box((0.45, 0.32, 0.18), (0, 0.04, 0.58), R_JOINT, body, bevel=0.03)
    rleg(body, (0.18, 0.04, 0.6), (0.2, 0.24, 0.26), 0.1, (0.24, 0.34, 0.09), 0.6)
    rleg(body, (-0.18, 0.04, 0.6), (0.2, 0.24, 0.26), 0.1, (0.24, 0.34, 0.09), 0.6)
    for s in (-1, 1):
        box((0.2, 0.02, 0.06), (s * 0.18, -0.085, 0.45), ORANGE, body)
    box((0.8, 0.58, 0.6), (0, 0.06, 1.0), R_SHELL, body, bevel=0.07)
    box((0.54, 0.06, 0.38), (0, -0.24, 1.0), R_JOINT, body, bevel=0.03)
    handprint(body, ORANGE, (0.08, -0.275, 0.98), size=1.05, rot=(R(90), 0, R(-8)))
    ico(0.05, (-0.17, -0.28, 1.12), R_GLOW, body, sub=1)
    box((0.81, 0.59, 0.07), (0, 0.06, 0.78), ORANGE, body)  # waist stripe
    box((0.3, 0.26, 0.18), (0, -0.12, 1.36), STEEL, body, bevel=0.03)
    box((0.22, 0.03, 0.045), (0, -0.26, 1.37), R_GLOW, body)
    box((0.06, 0.27, 0.19), (0, -0.12, 1.37), ORANGE, body)  # head stripe
    for k in range(3):
        box((0.44, 0.05, 0.03), (0, 0.14 + k * 0.09, 1.31), R_JOINT, body)
    for s in (-1, 1):
        box((0.32, 0.44, 0.28), (s * 0.52, 0.06, 1.25), R_SHELL, body, bevel=0.06)
        box((0.33, 0.12, 0.29), (s * 0.52, -0.04, 1.25), ORANGE, body)
    # giant fists on the Arm pivot (double slam)
    arm = empty("Arm", (0, 0.04, 1.22), body)
    for s in (-1, 1):
        rod(arm, STEEL, (s * 0.58, 0, -0.05), (s * 0.62, -0.06, -0.42), 0.09, verts=8)
        ico(0.1, (s * 0.62, -0.06, -0.44), R_JOINT, arm, sub=1)
        box((0.34, 0.4, 0.34), (s * 0.63, -0.18, -0.62), R_SHELL, arm, bevel=0.06)
        box((0.35, 0.08, 0.35), (s * 0.63, -0.08, -0.62), ORANGE, arm)
        for f in range(3):
            box((0.08, 0.1, 0.1), (s * 0.63 + (f - 1) * 0.1, -0.4, -0.66), STEEL, arm, bevel=0.015)
    arm.rotation_euler = (R(-6), 0, 0)
    return root


def nova_artillery():
    root = empty("NovaArtillery")
    grate_base(root)
    for p in ((1.05, 0.7), (0.75, 1.0)):  # spare cells
        cyl(0.13, 0.4, (p[0], p[1], 0.5), DSTEEL, root, verts=8)
        cyl(0.09, 0.06, (p[0], p[1], 0.72), CORE, root, verts=8)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    cyl(0.75, 0.3, (0, 0, 0.15), DSTEEL, yaw, verts=10)
    cyl(0.6, 0.08, (0, 0, 0.32), STEEL, yaw, verts=10)
    for s in (-1, 1):
        box((0.16, 0.95, 0.7), (s * 0.42, 0.1, 0.68), ORANGE, yaw, bevel=0.04)
        box((0.02, 0.36, 0.3), (s * 0.505, 0.25, 0.75), PATCH, yaw)
        box((0.02, 0.26, 0.1), (s * 0.505, -0.18, 0.55), STEEL, yaw)
    arm = empty("Arm", (0, 0.1, 0.88), yaw)
    rod(arm, DSTEEL, (0, -0.25, 0), (0, -1.8, 0), 0.12, verts=10)
    for k in range(6):  # cooling fins
        box((0.42, 0.035, 0.42), (0, -0.35 - k * 0.13, 0), DSTEEL, arm)
    box((0.3, 0.3, 0.2), (0, -1.75, 0), ORANGE, arm, bevel=0.03)  # muzzle brake
    cyl(0.1, 0.02, (0, -1.91, 0), CORE, arm, verts=10, rot=(R(90), 0, 0))
    # glowing core chamber in an open frame
    uvs(0.2, (0, 0.18, 0.02), CORE, arm, seg=10, rings=6, scale=(1, 1.5, 1), smooth=False)
    for y in (-0.15, 0.5):
        torus(0.26, 0.05, (0, y, 0.02), STEEL, arm, rot=(R(90), 0, 0), major=12, minor=4)
    for a in (45, 135, 225, 315):
        d = Vector((math.cos(R(a)), 0, math.sin(R(a))))
        rod(arm, STEEL, d * 0.26 + Vector((0, -0.15, 0.02)), d * 0.26 + Vector((0, 0.5, 0.02)), 0.03, verts=4)
    box((0.4, 0.3, 0.32), (0, 0.72, 0), ORANGE, arm, bevel=0.04)  # breech / counterweight
    box((0.41, 0.06, 0.33), (0, 0.62, 0), PATCH, arm)
    arm.rotation_euler = (R(-14), 0, 0)
    return root


def firewall():
    root = empty("Firewall")
    grate_base(root)
    # hooded hacker typing on a laptop crate (static)
    hk = empty("Hacker", (0.78, 0.0, 0.3), root)
    hk.rotation_euler = (0, 0, R(28))
    box((0.6, 0.42, 0.42), (0, -0.62, 0.21), PATCH, hk, bevel=0.03)
    box((0.62, 0.08, 0.06), (0, -0.62, 0.34), ORANGE, hk)
    box((0.44, 0.3, 0.03), (0, -0.62, 0.44), BLACK, hk)
    scr = box((0.44, 0.03, 0.3), (0, -0.76, 0.6), BLACK, hk, rot=(R(-15), 0, 0))
    box((0.38, 0.01, 0.24), (0, -0.74, 0.6), HOLO_O, hk, rot=(R(-15), 0, 0))
    box((0.36, 0.34, 0.26), (0, 0.04, 0.13), DSTEEL, hk, bevel=0.02)  # seat (ammo can)
    body, harm = person(hk, (0, 0.02, 0.0), SKIN_D, HOODIE, PANTS_K, HAIR_K, scale=0.9, hair_style="none", sandal=BOOT_K)
    harm.name = "HackerArm"
    strip(body, LEGS)
    strip(body, LEFT_ARM)
    body.location = (0, 0.02, 0.0)
    seated_legs(body, PANTS_K, BOOT_K, 0.0)
    hood(body, HOODIE)
    box((0.12, 0.05, 0.22), (0.2, -0.2, 0.8), ORANGE, body)  # orange patch
    rod(harm, HOODIE, (0, 0, 0), (0.08, -0.4, -0.38), 0.065)
    ico(0.07, (0.09, -0.44, -0.4), SKIN_D, harm, sub=1)
    rod(harm, HOODIE, (0.62, 0, -0.03), (0.5, -0.4, -0.38), 0.065)
    ico(0.07, (0.49, -0.44, -0.4), SKIN_D, harm, sub=1)
    rod(root, BLACK, (0.55, -0.55, 0.33), (-0.1, -0.2, 0.33), 0.04)
    rod(root, ORANGE, (0.6, -0.5, 0.33), (-0.05, 0.1, 0.33), 0.035)
    # black monolith with orbiting holo rings
    yaw = empty("Yaw", (-0.35, 0.3, 0.3), root)
    box((0.95, 0.95, 0.12), (0, 0, 0.06), DSTEEL, yaw, bevel=0.03)
    box((0.6, 0.42, 2.0), (0, 0, 1.1), GLASS_K, yaw, bevel=0.04)
    box((0.64, 0.46, 0.06), (0, 0, 2.12), STEEL, yaw)
    for s in (-1, 1):
        box((0.03, 0.02, 1.6), (s * 0.2, -0.215, 1.1), LED_B, yaw)
    for k in range(6):
        box((0.06, 0.02, 0.04), (-0.06 + (k % 3) * 0.06, -0.215, 1.55 - (k // 3) * 0.12), LED_B, yaw)
    box((0.4, 0.02, 0.04), (0, -0.215, 0.7), HOLO_O, yaw)
    orb = empty("Orb", (0, 0, 1.25), yaw)
    for k, (tx, ty, rr, z) in enumerate(((20, 0, 0.62, 0.4), (-15, 25, 0.68, -0.05), (10, -30, 0.58, -0.5))):
        torus(rr, 0.035, (0, 0, z), HOLO_O, orb, rot=(R(tx), R(ty), 0), major=24, minor=4)
    box((0.12, 0.12, 0.12), (0, -0.0, 1.05), HOLO_O, orb, rot=(R(45), R(35), 0))
    return root


def vega():
    root = empty("HeroVega")
    hero_base(root, team("Vega", (1.0, 0.5, 0.1)))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body, arm = person(yaw, (0, 0, 0), SKIN, ARMOR, COAT, HAIR_GREY, scale=1.26, burly=1.08, sandal=BOOT_K, belt=LEATHER)
    strip(body, LEFT_ARM)
    # long coat: tails behind and to the sides, collar
    box((0.62, 0.12, 0.85), (0, 0.22, 0.6), COAT, body, bevel=0.04, rot=(R(-6), 0, 0))
    for s in (-1, 1):
        box((0.12, 0.38, 0.8), (s * 0.3, 0.02, 0.62), COAT, body, bevel=0.03, rot=(0, R(s * 6), 0))
        box((0.1, 0.12, 0.5), (s * 0.22, -0.2, 0.86), COAT, body, bevel=0.02, rot=(0, R(s * -12), 0))
    cyl(0.24, 0.12, (0, 0.04, 1.02), COAT, body, verts=8, r2=0.27)
    # patched armour plates on the chest
    box((0.2, 0.05, 0.18), (-0.02, -0.22, 0.86), STEEL, body)
    box((0.12, 0.05, 0.1), (0.08, -0.215, 0.7), PATCH, body)
    box((0.14, 0.04, 0.03), (-0.05, -0.245, 0.88), ORANGE, body)
    # scar over the right eye
    box((0.025, 0.02, 0.14), (-0.08, -0.205, 1.18), SCAR, body, rot=(0, R(15), 0))
    # left arm in the coat sleeve with an orange armband
    cyl(0.09, 0.45, (0.34, 0, 0.76), COAT, body, verts=6, rot=(0, R(-10), 0))
    cyl(0.1, 0.1, (0.345, 0, 0.84), ORANGE, body, verts=6, rot=(0, R(-10), 0))
    ico(0.08, (0.37, -0.02, 0.52), SKIN, body, sub=1)
    # plasma rifle with a white-blue cell
    rod(arm, COAT, (0, 0, 0), (0.06, -0.28, -0.14), 0.075)
    ico(0.075, (0.08, -0.31, -0.15), SKIN, arm, sub=1)
    box((0.08, 0.3, 0.14), (0.12, -0.04, -0.1), DSTEEL, arm, bevel=0.02)
    box((0.11, 0.5, 0.15), (0.12, -0.42, -0.07), ORANGE, arm, bevel=0.03)
    uvs(0.075, (0.12, -0.3, 0.04), CORE, arm, seg=8, rings=5, scale=(1, 1.6, 1), smooth=False)
    box((0.07, 0.06, 0.18), (0.12, -0.24, -0.22), DSTEEL, arm)
    rod(arm, DSTEEL, (0.12, -0.67, -0.06), (0.12, -1.02, -0.06), 0.045, verts=8)
    for y in (-0.78, -0.9):
        cyl(0.07, 0.03, (0.12, y, -0.06), STEEL, arm, verts=8, rot=(R(90), 0, 0))
    ico(0.055, (0.12, -1.05, -0.06), CORE, arm, sub=1)
    left_arm_to(arm, COAT, SKIN, (0.14, -0.6, -0.16), r=0.075)
    arm.rotation_euler = (R(-4), 0, 0)
    return root


def zero():
    root = empty("HeroZero")
    hero_base(root, team("Zero", (0.5, 0.5, 0.55)))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body = empty("Body", (0, 0, 0), yaw)
    body.scale = (1.5, 1.42, 1.38)
    box((0.32, 0.2, 0.14), (0, 0, 0.56), R_JOINT, body, bevel=0.02)
    for s in (-1, 1):
        rleg(body, (s * 0.12, 0, 0.56), (0.14, 0.16, 0.26), 0.07, (0.16, 0.24, 0.07), 0.55)
    ico(0.26, (0, 0, 0.86), R_SHELL, body, sub=2, scale=(1.2, 0.9, 1.05))
    box((0.5, 0.05, 0.08), (0, 0.0, 0.8), ORANGE, body)
    for s in (-1, 1):
        box((0.06, 0.4, 0.06), (s * 0.27, 0.0, 0.8), ORANGE, body)
    handprint(body, WHITE_P, (0.04, -0.215, 0.9), size=0.75, rot=(R(80), 0, R(10)))
    box((0.3, 0.14, 0.05), (0, 0.02, 1.1), R_JOINT, body)
    uvs(0.16, (0, -0.01, 1.22), R_SHELL, body, seg=10, rings=6, scale=(1, 0.95, 0.8), smooth=False)
    box((0.22, 0.04, 0.045), (0, -0.145, 1.22), R_GLOW, body)
    box((0.05, 0.3, 0.13), (0, 0.0, 1.29), ORANGE, body)  # mohawk stripe
    box((0.24, 0.14, 0.28), (0, 0.2, 0.88), STEEL, body, bevel=0.02)
    for s in (-1, 1):  # shoulder pads + arms
        box((0.2, 0.26, 0.16), (s * 0.32, 0, 1.04), R_SHELL, body, bevel=0.04)
        cyl(0.055, 0.36, (s * 0.33, 0, 0.8), STEEL, body, verts=6, rot=(0, R(s * 8), 0))
        ico(0.075, (s * 0.35, -0.01, 0.6), R_JOINT, body, sub=1)
        box((0.12, 0.14, 0.12), (s * 0.36, -0.03, 0.52), R_SHELL, body, bevel=0.03)
    box((0.21, 0.08, 0.17), (0.32, -0.1, 1.04), ORANGE, body)
    # shoulder cannon on the right shoulder
    arm = empty("Arm", (-0.32, 0.02, 1.16), body)
    box((0.14, 0.18, 0.08), (0, 0, -0.02), R_JOINT, arm)
    rod(arm, R_SHELL, (0, 0.18, 0.08), (0, -0.2, 0.08), 0.085, verts=8)
    rod(arm, R_JOINT, (0, -0.2, 0.08), (0, -0.5, 0.08), 0.055, verts=8)
    cyl(0.07, 0.07, (0, -0.5, 0.08), ORANGE, arm, verts=8, rot=(R(90), 0, 0))
    cyl(0.045, 0.02, (0, -0.54, 0.08), R_GLOW, arm, verts=8, rot=(R(90), 0, 0))
    box((0.1, 0.12, 0.04), (0, 0.0, 0.17), ORANGE, arm)
    arm.rotation_euler = (R(-8), 0, 0)
    return root


BUILD = [
    ("industrial", "towers", "rifleman", rifleman), ("industrial", "towers", "steam_brawler", steam_brawler),
    ("industrial", "towers", "field_gun", field_gun), ("industrial", "towers", "tesla_coil", tesla_coil),
    ("industrial", "heroes", "ada", ada), ("industrial", "heroes", "jim", jim),
    ("modern", "towers", "sniper", sniper), ("modern", "towers", "flamethrower", flamethrower),
    ("modern", "towers", "missile_launcher", missile_launcher), ("modern", "towers", "emp_tower", emp_tower),
    ("modern", "heroes", "maya", maya), ("modern", "heroes", "ken", ken),
    ("digital", "towers", "laser_turret", laser_turret), ("digital", "towers", "mech_brawler", mech_brawler),
    ("digital", "towers", "plasma_mortar", plasma_mortar), ("digital", "towers", "cryo_field", cryo_field),
    ("digital", "heroes", "nova", nova), ("digital", "heroes", "glitch", glitch),
    ("datacenter", "towers", "arc_cannon", arc_cannon), ("datacenter", "towers", "titan_mech", titan_mech),
    ("datacenter", "towers", "nova_artillery", nova_artillery), ("datacenter", "towers", "firewall", firewall),
    ("datacenter", "heroes", "vega", vega), ("datacenter", "heroes", "zero", zero),
]
NEEDS_ARM = {"rifleman", "steam_brawler", "field_gun", "sniper", "flamethrower", "missile_launcher", "laser_turret",
             "mech_brawler", "plasma_mortar", "arc_cannon", "titan_mech", "nova_artillery"}
NEEDS_ORB = {"tesla_coil", "emp_tower", "cryo_field", "firewall"}


def check(root, name, folder):
    names = [o.name for o in lp.hierarchy(root)]
    for piv in ("Yaw", "Arm", "Orb"):
        assert names.count(piv) <= 1, f"{name}: {names.count(piv)} x {piv}"
    assert "Yaw" in names, name + ": no Yaw"
    if folder == "heroes" or name in NEEDS_ARM:
        assert "Arm" in names, name + ": no Arm"
    if name in NEEDS_ORB:
        assert "Orb" in names, name + ": no Orb"
    assert not any("." in n for n in names if n.split(".")[0] in ("Yaw", "Arm", "Orb")), names


cam = lp.stage(bg=(0.42, 0.44, 0.4))
built = {}
for n, (era, folder, name, fn) in enumerate(BUILD):
    if (ONLY and name not in ONLY) or (ERA and era not in ERA):
        continue
    # free up pivot names taken by models already exported
    for o in bpy.data.objects:
        if o.name.split(".")[0] in ("Yaw", "Arm", "Orb", "Body"):
            o.name = f"x{n}_{o.name}"
    r = fn()
    check(r, name, folder)
    lp.export_glb(r, os.path.join(OUT, folder, f"{name}.glb"))
    built.setdefault(era, []).append((folder, r))
if "--preview" in sys.argv:
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    every = [r for v in built.values() for _, r in v]
    for era, items in built.items():
        for r in every:
            for o in lp.hierarchy(r):
                o.hide_render = True
        towers = [r for f, r in items if f == "towers"]
        heroes = [r for f, r in items if f == "heroes"]
        for i, r in enumerate(towers):
            r.location = ((i - 1.5) * 3.4, -1.6, 0)
        for i, r in enumerate(heroes):
            r.location = ((i - 0.5) * 3.4, 2.3, 0)
        for r, _ in [(r, 0) for _, r in items]:
            for o in lp.hierarchy(r):
                o.hide_render = False
        lp.shoot(cam, os.path.join(PREVIEW_DIR, f"{era}_lineup.png"), (0, 0.3, 1.0), 14.5, res=1400, pos_dir=(0.45, -1.2, 0.9))
print("DONE")
