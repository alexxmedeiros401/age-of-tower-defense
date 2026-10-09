"""Bronze Age towers + all heroes. Run: python3 bronze.py --out DIR
Pivots for the game: Yaw (turns to face target), Arm (attack swing, + rotation = forward), Orb (pulse flash)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp
from lp import mat, empty, cyl, ico, uvs, box, torus, jitter, person, stone_base, arc

OUT = sys.argv[sys.argv.index("--out") + 1]
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
lp.reset(9)

# ---- palette
SAND = mat("Sandstone", (0.8, 0.64, 0.42), 0.85)
SAND_D = mat("SandstoneDark", (0.5, 0.36, 0.22), 0.85)
BRICK = mat("Mudbrick", (0.7, 0.5, 0.33), 0.9)
BRONZE = mat("Bronze", (0.66, 0.38, 0.13), 0.38, 0.55)
GOLD = mat("Gold", (0.95, 0.7, 0.18), 0.32, 0.6)
LINEN = mat("Linen", (0.94, 0.9, 0.8), 0.85)
RED = mat("RedCloth", (0.72, 0.14, 0.1), 0.85)
LAPIS = mat("Lapis", (0.14, 0.26, 0.72), 0.5)
SKIN = mat("SkinBronze", (0.66, 0.42, 0.27), 0.7)
SKIN_S = mat("Skin", (0.78, 0.45, 0.28), 0.7)
HAIR = mat("HairBlack", (0.07, 0.05, 0.05), 0.85)
HAIR_B = mat("Hair", (0.16, 0.09, 0.05), 0.9)
WOOD = mat("Wood", (0.5, 0.27, 0.09), 0.85)
WOOD_D = mat("WoodDark", (0.3, 0.17, 0.08), 0.85)
ROPE = mat("Rope", (0.72, 0.6, 0.38), 0.9)
LEATHER = mat("Leather", (0.36, 0.22, 0.12), 0.8)
STONE = mat("Stone", (0.52, 0.52, 0.5), 0.85)
FUR = mat("Fur", (0.72, 0.38, 0.10), 0.9)
SPOT = mat("FurSpot", (0.25, 0.15, 0.07), 0.9)
BONE = mat("Bone", (0.93, 0.89, 0.78), 0.6)
FIRE = mat("Ember", (1.0, 0.5, 0.1), 0.4, 0.0, emit=(1.0, 0.4, 0.05), strength=1.4)
SUN = mat("SunGlow", (1.0, 0.85, 0.35), 0.3, 0.6, emit=(1.0, 0.75, 0.2), strength=1.2)
PURPLE = mat("SpiritPurple", (0.75, 0.45, 1.0), 0.4, 0.0, emit=(0.6, 0.3, 1.0), strength=1.4)
HERO_RING = mat("HeroRing", (1.0, 0.82, 0.3), 0.3, 0.6, emit=(1.0, 0.7, 0.15), strength=0.8)


# ================================================================== TOWERS
def bronze_archer():
    root = empty("BronzeArcher")
    stone_base(root, SAND, SAND_D)
    # mudbrick lookout with crenellations
    box((1.3, 1.3, 0.7), (0, 0.1, 0.55), BRICK, root, bevel=0.03)
    for x in (-0.5, 0, 0.5):
        for y in (-0.5, 0.7):
            box((0.22, 0.18, 0.22), (x, y, 1.0), BRICK, root)
    for y in (-0.5, 0.1, 0.7):
        for x in (-0.6, 0.6):
            box((0.18, 0.22, 0.22), (x, y, 1.0), BRICK, root)
    box((1.36, 0.06, 0.08), (0, -0.56, 0.7), LAPIS, root)
    # quiver rack and arrows
    cyl(0.1, 0.5, (0.95, 0.75, 0.55), LEATHER, root, verts=6)
    for k in range(4):
        cyl(0.012, 0.35, (0.92 + 0.03 * k, 0.75, 0.9), WOOD, root, verts=3)
    yaw = empty("Yaw", (0, 0.05, 0.9), root)
    body, arm = person(yaw, (0, 0, 0), SKIN, LINEN, LINEN, HAIR, scale=1.2, helmet=BRONZE, belt=RED)
    cyl(0.07, 0.42, (0.1, 0.14, 0.9), LEATHER, body, verts=6, rot=(math.radians(15), 0, 0))  # quiver
    # bow arm: points forward, bow held vertical in front
    cyl(0.065, 0.42, (0, -0.18, -0.02), SKIN, arm, verts=6, rot=(math.radians(70), 0, 0))
    ico(0.075, (0, -0.37, -0.1), SKIN, arm, sub=1)
    arc(arm, WOOD_D, (0, -0.1, -0.1), 0.5, 0.035, -62, 62, segs=8)   # recurve bow, bulging forward
    for a in (-62, 62):
        ico(0.04, (0, -0.1 - 0.5 * math.cos(math.radians(a)), -0.1 + 0.5 * math.sin(math.radians(a))), BRONZE, arm, sub=1)
    box((0.015, 0.015, 0.88), (0, -0.33, -0.1), LINEN, arm)  # bowstring
    cyl(0.012, 0.7, (0, -0.42, -0.1), WOOD, arm, verts=3, rot=(math.radians(90), 0, 0))  # nocked arrow
    arm.rotation_euler = (math.radians(-10), 0, 0)
    return root


def spear_guard():
    root = empty("SpearGuard")
    stone_base(root, SAND, SAND_D)
    for x in (-1.05, 1.05):  # banner poles
        cyl(0.04, 1.6, (x, 0.6, 0.95), WOOD_D, root, verts=5)
        box((0.02, 0.4, 0.55), (x, 0.42, 1.45), RED, root)
        ico(0.06, (x, 0.6, 1.78), BRONZE, root, sub=1)
    box((0.9, 0.9, 0.12), (0, 0, 0.26), SAND_D, root, bevel=0.03)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    body, arm = person(yaw, (0, 0, 0), SKIN, BRONZE, RED, HAIR, scale=1.25, burly=1.12, helmet=BRONZE, crest=RED, belt=LEATHER)
    # big round shield on the left arm
    shield = cyl(0.42, 0.06, (0.42, -0.28, 0.72), BRONZE, body, verts=14, rot=(math.radians(90), 0, math.radians(-15)))
    cyl(0.12, 0.08, (0.43, -0.32, 0.72), GOLD, body, verts=10, rot=(math.radians(90), 0, math.radians(-15)))
    torus(0.41, 0.03, (0.42, -0.31, 0.72), GOLD, body, rot=(math.radians(90), 0, math.radians(-15)), major=16)
    # spear arm, couched forward for a thrust
    cyl(0.065, 0.4, (0, -0.12, -0.15), SKIN, arm, verts=6, rot=(math.radians(35), 0, 0))
    ico(0.075, (0, -0.25, -0.32), SKIN, arm, sub=1)
    cyl(0.03, 2.0, (0, -0.25 - 0.55, -0.32 + 0.1), WOOD_D, arm, verts=5, rot=(math.radians(84), 0, 0))
    cyl(0.07, 0.3, (0, -1.92, -0.2), BRONZE, arm, verts=5, r2=0.0, rot=(math.radians(84), 0, 0))
    arm.rotation_euler = (math.radians(-20), 0, 0)
    return root


def torsion_catapult():
    root = empty("TorsionCatapult")
    stone_base(root, SAND, SAND_D, r=1.6)
    for p in ((1.0, 0.95), (1.2, 0.6)):
        o = ico(0.22, (p[0], p[1], 0.42), STONE, root, sub=1, scale=(1, 1, 0.85)); jitter(o, 0.03)
    yaw = empty("Yaw", (0, 0, 0.3), root)
    for s in (-1, 1):
        box((0.16, 2.0, 0.16), (s * 0.48, 0.05, 0.12), WOOD, yaw, bevel=0.02)
        box((0.14, 0.14, 1.0), (s * 0.48, -0.05, 0.62), WOOD_D, yaw, bevel=0.02)
        # twisted sinew bundles (the torsion springs) with bronze caps
        cyl(0.17, 0.36, (s * 0.3, -0.05, 0.86), ROPE, yaw, verts=8, rot=(0, math.radians(90), 0))
        cyl(0.19, 0.06, (s * 0.12, -0.05, 0.86), BRONZE, yaw, verts=8, rot=(0, math.radians(90), 0))
        cyl(0.19, 0.06, (s * 0.48, -0.05, 0.86), BRONZE, yaw, verts=8, rot=(0, math.radians(90), 0))
    box((1.12, 0.14, 0.14), (0, 0.9, 0.12), WOOD, yaw)
    box((1.12, 0.14, 0.14), (0, -0.85, 0.12), WOOD, yaw)
    box((1.1, 0.12, 0.12), (0, -0.05, 1.18), WOOD, yaw, bevel=0.02)  # stop bar
    arm = empty("Arm", (0, -0.05, 0.86), yaw)
    cyl(0.09, 1.6, (0, 0.6, 0), WOOD, arm, verts=7, rot=(math.radians(90), 0, 0))
    torus(0.09, 0.025, (0, 0.2, 0), BRONZE, arm, rot=(math.radians(90), 0, 0), major=10)
    cyl(0.26, 0.16, (0, 1.38, 0.06), BRONZE, arm, verts=10, r2=0.34)
    o = ico(0.25, (0, 1.38, 0.28), STONE, arm, sub=1, scale=(1, 1, 0.9)); jitter(o, 0.03)
    arm.rotation_euler = (math.radians(-30), 0, 0)
    body, _a = person(yaw, (0.95, -0.6, -0.02), SKIN, LINEN, LINEN, HAIR, scale=0.85, hair_style="short", belt=LAPIS)
    return root


def sun_priest():
    root = empty("SunPriest")
    stone_base(root, SAND, SAND_D)
    # obelisk and fire brazier
    cyl(0.2, 1.7, (-1.0, 0.65, 1.05), SAND_D, root, verts=4, r2=0.13)
    cyl(0.13, 0.22, (-1.0, 0.65, 2.0), GOLD, root, verts=4, r2=0.0)
    cyl(0.22, 0.25, (1.0, 0.75, 0.42), BRONZE, root, verts=8, r2=0.3)
    cyl(0.0, 0.2, (1.0, 0.75, 0.68), FIRE, root, verts=6)
    for k in range(3):
        cyl(0.03, 0.4, (1.0 + 0.15 * math.cos(k * 2.1), 0.75 + 0.15 * math.sin(k * 2.1), 0.2), BRONZE, root, verts=4)
    # sun-dial disc inlaid in the floor
    cyl(0.55, 0.04, (0.2, -0.45, 0.3), GOLD, root, verts=16)
    torus(0.55, 0.04, (0.2, -0.45, 0.31), BRONZE, root, major=16)
    yaw = empty("Yaw", (-0.2, 0.15, 0.3), root)
    body = empty("Body", (0, 0, 0), yaw)
    body.scale = (1.15, 1.15, 1.15)
    robe = cyl(0.4, 1.0, (0, 0, 0.5), LINEN, body, verts=10, r2=0.22)
    cyl(0.42, 0.08, (0, 0, 0.06), GOLD, body, verts=10)
    box((0.42, 0.06, 0.3), (0, -0.2, 0.78), GOLD, body)  # pectoral collar
    ico(0.18, (0, -0.02, 1.12), SKIN, body, sub=2)
    for s in (-1, 1):
        ico(0.03, (s * 0.07, -0.18, 1.15), mat("Eye", (0.02, 0.02, 0.02), 0.3), body, sub=1)
        box((0.07, 0.02, 0.012), (s * 0.08, -0.185, 1.13), LAPIS, body)  # kohl
    cyl(0.2, 0.3, (0, 0.02, 1.3), GOLD, body, verts=10, r2=0.16)  # headdress
    box((0.42, 0.12, 0.38), (0, 0.06, 1.12), LAPIS, body)
    arm = empty("Arm", (-0.3, -0.05, 0.85), body)
    cyl(0.05, 0.3, (0, 0, 0), LINEN, arm, verts=6, rot=(0, math.radians(30), 0))
    cyl(0.03, 1.5, (-0.1, -0.05, 0.25), GOLD, arm, verts=5)
    orb = empty("Orb", (-0.1, -0.05, 1.1), arm)
    cyl(0.2, 0.05, (0, 0, 0), SUN, orb, verts=16, rot=(math.radians(90), 0, 0))
    for k in range(8):
        a = k * math.pi / 4
        box((0.03, 0.02, 0.12), (math.cos(a) * 0.27, 0, math.sin(a) * 0.27), GOLD, orb, rot=(0, -a, 0))
    arm.rotation_euler = (math.radians(-10), 0, 0)
    return root


# ================================================================== HEROES
def hero_base(parent, color_mat):
    cyl(0.8, 0.22, (0, 0, 0.11), STONE, parent, verts=12)
    torus(0.78, 0.06, (0, 0, 0.23), HERO_RING, parent, major=24)
    cyl(0.7, 0.04, (0, 0, 0.23), color_mat, parent, verts=12)


def ugo():
    root = empty("HeroUgo")
    hero_base(root, mat("UgoTeam", (0.75, 0.4, 0.12), 0.8))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body, arm = person(yaw, (0, 0, 0), SKIN_S, SKIN_S, FUR, HAIR_B, scale=1.3, burly=1.15, beard=HAIR_B, hair_style="long")
    cape = box((0.72, 0.1, 0.8), (0, 0.24, 0.78), FUR, body, bevel=0.05)
    for sx, sz in ((0.2, 0.6), (-0.2, 0.9), (0.1, 1.0)):
        ico(0.07, (sx, 0.3, sz), SPOT, body, sub=1, scale=(1.3, 0.4, 1))
    cyl(0.23, 0.06, (0, 0.0, 1.27), RED, body, verts=10)  # headband
    for k in range(3):
        box((0.04, 0.02, 0.3), (0.12 - k * 0.06, 0.15, 1.42), mat("Feather", (0.95, 0.85, 0.6), 0.8), body, rot=(0.3, 0.2 * k, 0))
    # sling arm raised overhead, stone in the pouch
    cyl(0.075, 0.5, (0, 0, 0.25), SKIN_S, arm, verts=6)
    ico(0.085, (0, 0, 0.52), SKIN_S, arm, sub=1)
    cyl(0.012, 0.5, (0, -0.1, 0.75), LEATHER, arm, verts=4, rot=(math.radians(-25), 0, 0))
    ico(0.1, (0, -0.2, 0.98), STONE, arm, sub=1)
    arm.rotation_euler = (math.radians(-30), 0, math.radians(-10))
    return root


def mara():
    root = empty("HeroMara")
    hero_base(root, mat("MaraTeam", (0.4, 0.25, 0.55), 0.8))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body, arm = person(yaw, (0, 0, 0), SKIN_S, mat("FurGrey", (0.55, 0.52, 0.48), 0.9), mat("FurGrey", (0.55, 0.52, 0.48), 0.9),
                       HAIR_B, scale=1.2, hair_style="long")
    for s in (-1, 1):  # antler headdress
        cyl(0.03, 0.4, (s * 0.15, 0.02, 1.45), BONE, body, verts=4, rot=(0, math.radians(s * 25), 0))
        cyl(0.025, 0.2, (s * 0.26, 0.02, 1.52), BONE, body, verts=4, rot=(0, math.radians(s * 70), 0))
    for k in range(5):  # bone necklace
        ico(0.035, (math.cos(k * 0.6 - 1.2) * 0.22, -0.2 + math.sin(k * 0.6 - 1.2) * 0.04, 0.98), BONE, body, sub=1)
    cyl(0.05, 0.3, (0, 0, 0), SKIN_S, arm, verts=6, rot=(0, math.radians(30), 0))
    cyl(0.035, 1.6, (-0.1, -0.05, 0.3), WOOD_D, arm, verts=5)
    orb = empty("Orb", (-0.1, -0.05, 1.15), arm)
    uvs(0.13, (0, 0, 0), PURPLE, orb, seg=10, rings=6)
    torus(0.12, 0.025, (-0.1, -0.05, 1.03), BONE, arm, major=8)
    arm.rotation_euler = (math.radians(-10), 0, 0)
    return root


def kira():
    root = empty("HeroKira")
    hero_base(root, mat("KiraTeam", (0.85, 0.6, 0.15), 0.8))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body, arm = person(yaw, (0, 0, 0), SKIN, BRONZE, RED, HAIR, scale=1.25, hair_style="pony", belt=GOLD)
    box((0.06, 0.04, 0.5), (0.15, -0.24, 0.55), GOLD, body, rot=(0, 0, 0.5))  # sash
    cyl(0.235, 0.05, (0, 0, 1.27), GOLD, body, verts=10)  # circlet
    ico(0.05, (0, -0.22, 1.28), LAPIS, body, sub=1)
    # khopesh: sickle sword held high
    cyl(0.065, 0.45, (0, 0, 0.22), SKIN, arm, verts=6)
    ico(0.075, (0, 0, 0.47), SKIN, arm, sub=1)
    cyl(0.03, 0.3, (0, -0.05, 0.62), LEATHER, arm, verts=5)
    box((0.035, 0.1, 0.42), (0, -0.05, 0.92), BRONZE, arm)            # straight part of the khopesh
    arc(arm, BRONZE, (0, -0.27, 1.13), 0.22, 0.045, -150, 60, segs=7)  # the hooked sickle blade
    arm.rotation_euler = (math.radians(-35), 0, 0)
    return root


def tarek():
    root = empty("HeroTarek")
    hero_base(root, mat("TarekTeam", (0.6, 0.35, 0.22), 0.8))
    # anvil and glowing ingot
    box((0.5, 0.26, 0.3), (0.62, 0.35, 0.4), STONE, root, bevel=0.03)
    box((0.62, 0.3, 0.12), (0.62, 0.35, 0.6), mat("Iron", (0.3, 0.3, 0.33), 0.4, 0.8), root, bevel=0.02)
    box((0.22, 0.1, 0.05), (0.62, 0.35, 0.69), FIRE, root)
    yaw = empty("Yaw", (-0.15, -0.1, 0.25), root)
    body, arm = person(yaw, (0, 0, 0), SKIN, SKIN, LEATHER, HAIR, scale=1.3, burly=1.25, beard=HAIR, hair_style="short")
    box((0.42, 0.06, 0.62), (0, -0.21, 0.66), LEATHER, body)  # apron
    for s in (-1, 1):
        cyl(0.09, 0.08, (s * 0.37, -0.02, 0.6), BRONZE, body, verts=8)  # bracers
    # big bronze hammer
    cyl(0.075, 0.42, (0, 0, 0.22), SKIN, arm, verts=6)
    ico(0.085, (0, 0, 0.46), SKIN, arm, sub=1)
    cyl(0.035, 0.75, (0, -0.05, 0.75), WOOD_D, arm, verts=6)
    box((0.42, 0.24, 0.22), (0, -0.05, 1.12), BRONZE, arm, bevel=0.03)
    arm.rotation_euler = (math.radians(-35), 0, 0)
    return root


BUILD = [("towers", "bronze_archer", bronze_archer), ("towers", "spear_guard", spear_guard),
         ("towers", "torsion_catapult", torsion_catapult), ("towers", "sun_priest", sun_priest),
         ("heroes", "ugo", ugo), ("heroes", "mara", mara), ("heroes", "kira", kira), ("heroes", "tarek", tarek)]

cam = lp.stage(bg=(0.55, 0.47, 0.33))
built = []
for folder, name, fn in BUILD:
    if ONLY and name not in ONLY:
        continue
    r = fn()
    lp.export_glb(r, os.path.join(OUT, folder, f"{name}.glb"))
    built.append(r)
if "--preview" in sys.argv:
    for i, r in enumerate(built):
        r.location = ((i % 4 - 1.5) * 3.4, (i // 4) * 3.6 - 1.6, 0)
    lp.shoot(cam, os.path.join(OUT, "bronze_lineup.png"), (0, 0.4, 0.9), 15.5, res=1400, pos_dir=(0.45, -1.2, 0.9))
print("DONE")
