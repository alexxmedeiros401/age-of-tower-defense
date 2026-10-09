"""Stone Age towers (Club Warrior, Boulder Catapult, Tar Pit Shaman). Same scale as rock_slinger (game scale 0.52).
Pivots for the game: Yaw (faces target), Arm (attack swing, + rotation = forward), Orb (pulse flash)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp
from lp import mat, empty, cyl, ico, uvs, box, torus, jitter

OUT = sys.argv[sys.argv.index("--out") + 1]
lp.reset(5)

GRASS = mat("Grass", (0.20, 0.52, 0.10), 0.85)
DIRT = mat("Dirt", (0.42, 0.28, 0.16), 0.9)
WOOD = mat("Wood", (0.50, 0.27, 0.09), 0.85)
WOOD_D = mat("WoodDark", (0.30, 0.17, 0.08), 0.85)
STONE = mat("Stone", (0.52, 0.52, 0.50), 0.85)
STONE_D = mat("StoneDark", (0.36, 0.36, 0.35), 0.85)
SKIN = mat("Skin", (0.78, 0.45, 0.28), 0.7)
FUR = mat("Fur", (0.72, 0.38, 0.10), 0.9)
FUR2 = mat("FurGrey", (0.55, 0.52, 0.48), 0.9)
SPOT = mat("FurSpot", (0.25, 0.15, 0.07), 0.9)
HAIR = mat("Hair", (0.16, 0.09, 0.05), 0.9)
BONE = mat("Bone", (0.93, 0.89, 0.78), 0.6)
LEATHER = mat("Leather", (0.36, 0.22, 0.12), 0.8)
EYE = mat("Eye", (0.02, 0.02, 0.02), 0.3)
ROBE = mat("Robe", (0.33, 0.18, 0.48), 0.9)
ROBE_D = mat("RobeDark", (0.22, 0.11, 0.33), 0.9)
TAR = mat("Tar", (0.03, 0.03, 0.04), 0.08, 0.2)
GREEN = mat("SpiritGlow", (0.3, 1.0, 0.45), 0.4, 0.0, emit=(0.2, 1.0, 0.35), strength=1.1)
FIRE = mat("Ember", (1.0, 0.45, 0.08), 0.4, 0.0, emit=(1.0, 0.35, 0.03), strength=1.2)
PAINT = mat("WarPaint", (0.75, 0.1, 0.08), 0.8)


def base(parent, r=1.55):
    g = cyl(r, 0.25, (0, 0, 0.125), GRASS, parent, verts=7); jitter(g, 0.035)
    d = cyl(r + 0.05, 0.3, (0, 0, -0.1), DIRT, parent, verts=7); jitter(d, 0.045)
    for i in range(random.randint(3, 5)):
        a = random.uniform(0, math.tau)
        rr = random.uniform(0.9, 1.35)
        o = ico(random.uniform(0.08, 0.14), (math.cos(a) * rr, math.sin(a) * rr, 0.27), STONE, parent, sub=1, scale=(1.2, 1, 0.7))
        jitter(o, 0.02)
    for i in range(6):
        a = random.uniform(0, math.tau)
        rr = random.uniform(0.4, 1.4)
        cyl(0.05, 0.16, (math.cos(a) * rr, math.sin(a) * rr, 0.3), GRASS, parent, verts=3, r2=0.0)


def caveman(parent, loc, scale=1.0, tunic=FUR, burly=1.0, beard=True):
    """Returns (body_empty, right_shoulder_pivot). Body faces -Y."""
    body = empty("Body", loc, parent)
    body.scale = (scale * burly, scale, scale)
    for s in (-1, 1):
        cyl(0.09, 0.42, (s * 0.14, 0, 0.21), SKIN, body, verts=6)
        ico(0.11, (s * 0.14, -0.05, 0.03), LEATHER, body, sub=1, scale=(1, 1.4, 0.55))
    ico(0.3, (0, 0, 0.68), SKIN, body, sub=2, scale=(1.0, 0.82, 1.08))
    t = cyl(0.35, 0.5, (0, 0, 0.52), tunic, body, verts=7, r2=0.27); jitter(t, 0.035)
    for sx, sz in ((0.2, 0.55), (-0.15, 0.42), (0.05, 0.7)):
        ico(0.07, (sx, -0.3, sz), SPOT, body, sub=1, scale=(1.3, 0.4, 1))
    cyl(0.05, 0.85, (0, -0.02, 0.75), tunic, body, verts=5, rot=(0, math.radians(38), 0))
    cyl(0.36, 0.07, (0, 0, 0.33), LEATHER, body, verts=7)
    ico(0.22, (0, -0.03, 1.15), SKIN, body, sub=2, scale=(1, 0.95, 1.05))
    ico(0.11, (0, -0.2, 1.24), SKIN, body, sub=1, scale=(2.0, 0.6, 0.45))
    ico(0.065, (0, -0.24, 1.13), SKIN, body, sub=1, scale=(0.8, 1, 1.0))
    for s in (-1, 1):
        ico(0.032, (s * 0.085, -0.205, 1.18), EYE, body, sub=1)
    h = ico(0.25, (0, 0.07, 1.21), HAIR, body, sub=2, scale=(1.08, 0.98, 0.82)); jitter(h, 0.03)
    if beard:
        b = ico(0.17, (0, -0.15, 1.0), HAIR, body, sub=1, scale=(1.15, 0.7, 1.0)); jitter(b, 0.03)
    cyl(0.075, 0.5, (0.36, 0, 0.72), SKIN, body, verts=6, rot=(0, math.radians(-12), 0))
    ico(0.085, (0.4, -0.02, 0.45), SKIN, body, sub=1)
    sh = empty("Arm", (-0.33, 0, 0.92), body)
    return body, sh


# ------------------------------------------------------------------ CLUB WARRIOR
def club_warrior():
    root = empty("ClubWarrior")
    base(root)
    # flat boulder stage, skull totems, crossed bones
    st = ico(0.75, (0, 0.05, 0.22), STONE_D, root, sub=2, scale=(1.1, 1.0, 0.28)); jitter(st, 0.03)
    for x, y in ((1.05, 0.55), (-1.1, 0.4)):
        cyl(0.05, 0.9, (x, y, 0.65), WOOD_D, root, verts=5)
        ico(0.13, (x, y, 1.15), BONE, root, sub=1, scale=(1, 1.1, 1.1))
        for s in (-1, 1):
            ico(0.035, (x + s * 0.05, y - 0.11, 1.15), EYE, root, sub=1)
    for s in (-1, 1):
        cyl(0.04, 0.8, (0.6, -0.9, 0.3), BONE, root, verts=5, rot=(math.radians(90), 0, math.radians(s * 35)))
    yaw = empty("Yaw", (0, 0, 0.3), root)
    body, arm = caveman(yaw, (0, 0, 0.02), scale=1.3, burly=1.18, tunic=FUR2)
    # war paint stripes
    for s in (-1, 1):
        box((0.04, 0.02, 0.12), (s * 0.1, -0.24, 1.08), PAINT, body)
    # club held overhead, swings forward on attack
    cyl(0.075, 0.5, (0, 0, 0.25), SKIN, arm, verts=6)
    ico(0.085, (0, 0, 0.52), SKIN, arm, sub=1)
    club = cyl(0.07, 0.9, (0, 0.05, 0.85), WOOD, arm, verts=7, r2=0.17)
    for k in range(4):
        a = k * math.pi / 2
        cyl(0.04, 0.12, (math.cos(a) * 0.15, 0.05 + math.sin(a) * 0.15, 1.15), BONE, arm, verts=4, r2=0.0,
            rot=(math.cos(a) * 1.2, math.sin(a) * -1.2, 0))
    arm.rotation_euler = (math.radians(-25), 0, math.radians(-8))
    return root


# ------------------------------------------------------------------ BOULDER CATAPULT
def catapult():
    root = empty("BoulderCatapult")
    base(root, r=1.6)
    for p in ((0.95, 0.9), (1.15, 0.55), (0.85, 0.5)):
        o = ico(0.2, (p[0], p[1], 0.38), STONE, root, sub=1, scale=(1, 1, 0.85)); jitter(o, 0.03)
    yaw = empty("Yaw", (0, 0, 0.25), root)
    # sled frame
    for s in (-1, 1):
        cyl(0.13, 1.9, (s * 0.45, 0.1, 0.12), WOOD, yaw, verts=7, rot=(math.radians(90), 0, 0))
        cyl(0.11, 1.15, (s * 0.42, 0.25, 0.62), WOOD_D, yaw, verts=6, rot=(math.radians(-20), math.radians(s * -8), 0))
        cyl(0.11, 1.1, (s * 0.42, -0.25, 0.6), WOOD_D, yaw, verts=6, rot=(math.radians(25), math.radians(s * -8), 0))
    for y in (-0.7, 0.85):
        cyl(0.07, 1.0, (0, y, 0.12), WOOD, yaw, verts=6, rot=(0, math.radians(90), 0))
    cyl(0.11, 1.05, (0, 0, 1.1), WOOD, yaw, verts=7, rot=(0, math.radians(90), 0))
    torus(0.1, 0.03, (0.3, 0, 1.1), LEATHER, yaw, rot=(0, math.radians(90), 0), major=8)
    torus(0.1, 0.03, (-0.3, 0, 1.1), LEATHER, yaw, rot=(0, math.radians(90), 0), major=8)
    # throwing arm: rest pulled back (bucket behind, low); + rotation flings it up and forward
    arm = empty("Arm", (0, 0, 1.1), yaw)
    cyl(0.1, 1.7, (0, 0.55, 0), WOOD, arm, verts=7, rot=(math.radians(90), 0, 0))
    cyl(0.26, 0.18, (0, 1.38, 0.05), WOOD_D, arm, verts=8, r2=0.36)
    o = ico(0.27, (0, 1.38, 0.28), STONE, arm, sub=1, scale=(1, 1, 0.9)); jitter(o, 0.03)
    box((0.42, 0.32, 0.32), (0, -0.4, -0.05), STONE_D, arm, bevel=0.04)
    arm.rotation_euler = (math.radians(-28), 0, 0)
    # operator caveman beside it, pointing
    caveman(yaw, (0.85, -0.55, 0.0), scale=0.9)
    return root


# ------------------------------------------------------------------ TAR PIT SHAMAN
def tar_shaman():
    root = empty("TarShaman")
    base(root)
    pit = cyl(0.62, 0.06, (0.35, -0.3, 0.26), TAR, root, verts=12); jitter(pit, 0.01)
    torus(0.64, 0.06, (0.35, -0.3, 0.26), STONE_D, root, major=14)
    for i in range(5):
        a = random.uniform(0, math.tau)
        r = random.uniform(0.05, 0.45)
        uvs(random.uniform(0.04, 0.08), (0.35 + math.cos(a) * r, -0.3 + math.sin(a) * r, 0.29), TAR, root, seg=8, rings=4,
            scale=(1, 1, 0.6))
    # bone totem poles with feathers
    for x, y in ((-1.0, 0.6), (1.05, 0.75)):
        cyl(0.06, 1.3, (x, y, 0.85), WOOD_D, root, verts=6)
        ico(0.12, (x, y, 1.55), BONE, root, sub=1)
        box((0.04, 0.02, 0.25), (x + 0.08, y, 1.3), PAINT, root, rot=(0, 0.4, 0))
        box((0.04, 0.02, 0.22), (x - 0.08, y, 1.28), GREEN, root, rot=(0, -0.4, 0))
    yaw = empty("Yaw", (-0.35, 0.25, 0.25), root)
    body = empty("Body", (0, 0, 0), yaw)
    body.scale = (1.15, 1.15, 1.15)
    robe = cyl(0.42, 1.0, (0, 0, 0.5), ROBE, body, verts=8, r2=0.2); jitter(robe, 0.03)
    cyl(0.44, 0.1, (0, 0, 0.06), ROBE_D, body, verts=8)
    ico(0.18, (0, -0.02, 1.12), SKIN, body, sub=2)
    hood = cyl(0.27, 0.5, (0, 0.04, 1.25), ROBE_D, body, verts=8, r2=0.0); jitter(hood, 0.02)
    # skull mask
    ico(0.15, (0, -0.15, 1.1), BONE, body, sub=1, scale=(1, 0.6, 1.1))
    for s in (-1, 1):
        ico(0.035, (s * 0.055, -0.24, 1.14), GREEN, body, sub=1)
    for k in range(5):
        ico(0.04, (math.cos(k * 0.6 - 1.2) * 0.25, -0.18 + math.sin(k * 0.6 - 1.2) * 0.05, 0.85), BONE, body, sub=1)
    # staff arm with spirit orb
    arm = empty("Arm", (-0.3, -0.05, 0.85), body)
    cyl(0.05, 0.3, (0, 0, 0.0), ROBE, arm, verts=6, rot=(0, math.radians(30), 0))
    cyl(0.03, 1.5, (-0.1, -0.05, 0.25), WOOD_D, arm, verts=5)
    torus(0.1, 0.025, (-0.1, -0.05, 1.0), BONE, arm, major=8)
    orb = empty("Orb", (-0.1, -0.05, 1.12), arm)
    uvs(0.12, (0, 0, 0), GREEN, orb, seg=10, rings=6)
    arm.rotation_euler = (math.radians(-10), 0, 0)
    return root


cam = lp.stage()
built = []
for name, fn in (("club_warrior", club_warrior), ("boulder_catapult", catapult), ("tar_shaman", tar_shaman)):
    r = fn()
    lp.export_glb(r, os.path.join(OUT, "towers", f"{name}.glb"))
    built.append(r)
for i, r in enumerate(built):
    r.location = ((i - 1) * 3.6, 0, 0)
lp.shoot(cam, os.path.join(OUT, "towers_lineup.png"), (0, -0.3, 0.8), 11.5, res=1200, pos_dir=(0.45, -1.2, 0.9))
print("DONE")
