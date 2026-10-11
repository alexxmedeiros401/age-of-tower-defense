"""Stone Age robots, v2 art pass (stylized pipeline, see sty.py).

Scout Drone, Walker, Brute Bot, Carrier, Prime Walker. Gleaming white plating graded down to gunmetal,
red glowing eyes and cores: the cold future against the warm, furry Stone Age.
Game pivots (game.gd animates them in code): Body (bob), LegA_* / LegB_* (gait, rotate x),
Spin* (rotors, spun around their own up axis).

Usage: python3 robots_v2.py -- --out assets/robots [--only walker,brute] [--preview DIR]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sty
from sty import P, reg, cyl, ico, uvs, torus, box, rod, empty, jitter, lerp, mul, point_at
from mathutils import Vector, noise

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default
OUT = arg("--out", "assets/robots")
ONLY = arg("--only")
PREVIEW = arg("--preview")
OUTLINE = float(arg("--outline", "0.042"))
H = [1.4]   # current robot height, for the plating gradient


def plate(p, n):
    t = p.z / H[0]
    c = lerp(mul(P["plate"], 0.72), P["plate"], 0.35 + t * 0.9)
    return lerp(c, mul(c, 0.9), 0.5 + 0.6 * noise.noise(p * 3.0))


def dark(p, n):
    return lerp(P["gunmetal"], P["plate_dark"], 0.3 + 0.5 * (p.z / H[0]))


def W(o, parent, name, bevel=0.02):
    return reg(o, P["plate"], matk="satin", parent=parent, bevel=bevel, var=0, name=name, colfn=plate)


def D(o, parent, name, bevel=0.015):
    return reg(o, P["gunmetal"], matk="metal", parent=parent, bevel=bevel, var=0, name=name, colfn=dark)


def R(o, parent, name, col=None):
    return reg(o, col or P["red_glow"], matk="glow_red", parent=parent, var=0, noao=True, name=name)


def HZ(o, parent, name, bevel=0.015):
    return reg(o, P["hazard"], matk="satin", parent=parent, bevel=bevel, var=0, name=name,
               colfn=lambda p, n: lerp(mul(P["hazard"], 0.8), P["hazard"], 0.5 + 0.5 * noise.noise(p * 5)))


def leg(name, hip, parent, thigh=(0.14, 0.16, 0.24), shin=(0.12, 0.14, 0.24), foot=(0.16, 0.24, 0.07), knee=0.075):
    """Leg pivot at the hip; geometry hangs below it (game swings rotation.x)."""
    p = empty(name, hip, parent)
    tz = thigh[2]
    D(box(thigh, (0, 0, -tz / 2)), p, "Thigh")
    W(ico(knee, (0, -0.02, -tz), sub=2), p, "Knee", bevel=None)
    sz = shin[2]
    W(box(shin, (0, 0, -tz - sz / 2 - 0.02)), p, "Shin")
    R(box((shin[0] * 0.5, 0.02, 0.03), (0, -shin[1] / 2 - 0.005, -tz - sz * 0.35)), p, "ShinLight")
    D(box(foot, (0, -0.03, -tz - sz - foot[2] / 2 - 0.02)), p, "Foot")
    return p


# ================================================================= WALKER
def walker():
    H[0] = 1.4
    root = empty("Walker")
    body = empty("Body", (0, 0, 0), root)
    D(box((0.3, 0.22, 0.14), (0, 0, 0.56)), body, "Pelvis")
    leg("LegA_L", (0.12, 0, 0.55), body)
    leg("LegB_R", (-0.12, 0, 0.55), body)
    D(cyl(0.13, 0.16, (0, 0, 0.66), verts=10), body, "Waist")
    W(ico(0.25, (0, 0, 0.86), scale=(1.15, 0.9, 1.0)), body, "Torso", bevel=None)
    W(box((0.32, 0.08, 0.2), (0, -0.2, 0.9), rot=(0.15, 0, 0)), body, "ChestPlate")
    R(ico(0.065, (0, -0.25, 0.88), sub=2), body, "Core")
    D(torus(0.075, 0.018, (0, -0.245, 0.88), rot=(math.radians(90), 0, 0), maj=12, mi=3), body, "CoreRing", bevel=None)
    # head: dome with a glowing visor band
    D(cyl(0.07, 0.08, (0, 0, 1.08), verts=8), body, "Neck")
    W(ico(0.17, (0, -0.01, 1.2), scale=(1.05, 0.95, 0.85)), body, "Head", bevel=None)
    D(box((0.28, 0.06, 0.08), (0, -0.14, 1.2)), body, "VisorFrame")
    R(box((0.22, 0.03, 0.04), (0, -0.172, 1.2)), body, "Visor")
    D(cyl(0.012, 0.28, (0.08, 0.06, 1.42), verts=4), body, "Antenna", bevel=None)
    R(ico(0.028, (0.08, 0.06, 1.56), sub=1), body, "AntennaTip")
    # shoulders, arms: blaster right, claw left
    for s in (-1, 1):
        W(ico(0.11, (s * 0.31, 0, 1.0), scale=(1.2, 1.1, 0.8)), body, "ShoulderPad", bevel=None)
        D(rod((s * 0.32, 0, 0.95), (s * 0.35, -0.02, 0.68), 0.045, 6), body, "Arm")
    D(cyl(0.06, 0.26, (-0.35, -0.1, 0.62), verts=8, rot=(math.radians(90), 0, 0)), body, "Blaster")
    R(cyl(0.04, 0.02, (-0.35, -0.235, 0.62), verts=8, rot=(math.radians(90), 0, 0)), body, "Muzzle")
    for k in (-1, 1):
        D(cyl(0.02, 0.12, (0.35 + k * 0.03, -0.04, 0.58), verts=4, r2=0.005, rot=(0.3, k * 0.3, 0)), body, "Claw", bevel=None)
    W(box((0.22, 0.12, 0.26), (0, 0.2, 0.9)), body, "Backpack")
    for k in range(3):
        D(box((0.16, 0.02, 0.02), (0, 0.265, 0.82 + k * 0.06)), body, "Vent", bevel=None)
    return root, {"Walker": "Root_Mesh", "Body": "Body_Mesh"}


# ================================================================= SCOUT DRONE
def scout():
    H[0] = 1.1
    root = empty("Scout")
    body = empty("Body", (0, 0, 0.85), root)
    W(ico(0.2, (0, 0, 0), sub=3), body, "Shell", bevel=None)
    D(torus(0.21, 0.04, (0, 0, -0.01), maj=18, mi=4), body, "Equator", bevel=None)
    D(cyl(0.11, 0.06, (0, -0.17, 0.01), verts=12, rot=(math.radians(90), 0, 0)), body, "LensSocket")
    R(ico(0.075, (0, -0.2, 0.01), sub=2, scale=(1, 0.55, 1)), body, "Lens")
    reg(ico(0.025, (0.02, -0.235, 0.035), sub=1), (1, 0.85, 0.8), matk="gloss", parent=body, var=0, noao=True, name="Glint")
    for s in (-1, 1):
        D(rod((s * 0.17, 0.02, 0.02), (s * 0.36, 0.06, 0.06), 0.03, 6), body, "RotorArm")
        D(cyl(0.05, 0.08, (s * 0.38, 0.06, 0.06), verts=8), body, "RotorHub")
        sp = empty("SpinRotor_" + ("L" if s < 0 else "R"), (s * 0.38, 0.06, 0.12), body)
        for k in range(2):
            b = box((0.34, 0.05, 0.012), (0, 0, 0), rot=(0, 0.12, k * math.pi / 2))
            reg(b, P["steel"], matk="metal", parent=sp, var=0, name="Blade", colfn=lambda p, n: P["steel"])
    for k in range(3):
        a = math.radians(90 + (k - 1) * 30)
        D(box((0.03, 0.12, 0.08), (math.cos(a) * 0.12, math.sin(a) * 0.17, 0.12), rot=(0.4, 0, a - math.pi / 2)), body, "Fin")
    D(cyl(0.09, 0.12, (0, 0, -0.22), verts=10, r2=0.05), body, "Thruster")
    R(cyl(0.05, 0.04, (0, 0, -0.29), verts=10), body, "ThrusterGlow", col=(1.0, 0.45, 0.2))
    return root, {"Scout": "Root_Mesh", "Body": "Body_Mesh", "SpinRotor_L": "RotorL_Mesh", "SpinRotor_R": "RotorR_Mesh"}


# ================================================================= BRUTE BOT
def brute():
    H[0] = 1.65
    root = empty("Brute")
    body = empty("Body", (0, 0, 0), root)
    D(box((0.46, 0.3, 0.18), (0, 0.04, 0.62)), body, "Pelvis")
    big = dict(thigh=(0.2, 0.24, 0.26), shin=(0.2, 0.24, 0.24), foot=(0.26, 0.34, 0.1), knee=0.1)
    leg("LegA_L", (0.18, 0.04, 0.62), body, **big)
    leg("LegB_R", (-0.18, 0.04, 0.62), body, **big)
    W(box((0.72, 0.5, 0.56), (0, 0.04, 1.04)), body, "Chest", bevel=0.07)
    HZ(box((0.74, 0.06, 0.1), (0, -0.215, 1.22)), body, "HazardBand")
    for k in range(4):
        D(box((0.07, 0.065, 0.11), (-0.27 + k * 0.18, -0.225, 1.22), rot=(0, 0.6, 0)), body, "HazardStripe", bevel=None)
    D(box((0.3, 0.06, 0.24), (0, -0.22, 0.98)), body, "ChestPanel")
    R(ico(0.08, (0, -0.26, 0.98), sub=2), body, "Core")
    # sunk head with a slit visor
    D(box((0.3, 0.28, 0.2), (0, -0.06, 1.38)), body, "Head", bevel=0.04)
    R(box((0.2, 0.03, 0.035), (0, -0.205, 1.4)), body, "Visor")
    for s in (-1, 1):
        W(ico(0.2, (s * 0.46, 0.04, 1.26), scale=(1.2, 1.15, 0.85)), body, "ShoulderPad", bevel=None)
        HZ(box((0.06, 0.3, 0.06), (s * 0.5, 0.04, 1.42), rot=(0, s * 0.5, 0)), body, "PadStripe")
        D(rod((s * 0.5, 0.04, 1.18), (s * 0.56, -0.02, 0.86), 0.075, 8), body, "UpperArm")
        W(cyl(0.12, 0.3, (s * 0.57, -0.05, 0.72), verts=10, r2=0.1), body, "Forearm")
        D(box((0.24, 0.24, 0.22), (s * 0.58, -0.08, 0.5)), body, "Fist", bevel=0.05)
        for k in range(3):
            D(box((0.05, 0.06, 0.06), (s * 0.58 + (k - 1) * 0.075, -0.22, 0.52)), body, "Knuckle", bevel=None)
    for s in (-1, 1):
        D(cyl(0.05, 0.4, (s * 0.16, 0.34, 1.3), verts=8), body, "Exhaust")
        R(cyl(0.035, 0.02, (s * 0.16, 0.34, 1.51), verts=8), body, "ExhaustGlow", col=(1.0, 0.4, 0.12))
    return root, {"Brute": "Root_Mesh", "Body": "Body_Mesh"}


# ================================================================= CARRIER
def carrier():
    H[0] = 1.0
    root = empty("Carrier")
    body = empty("Body", (0, 0, 0.62), root)
    hull = box((1.05, 0.74, 0.26), (0, 0, 0))
    HZ(hull, body, "Hull", bevel=0.08)
    W(box((0.9, 0.62, 0.1), (0, 0, 0.16)), body, "Deck", bevel=0.04)
    for k in range(5):
        D(box((0.06, 0.76, 0.05), (-0.42 + k * 0.21, 0, -0.1)), body, "Rib", bevel=None)
    R(box((0.7, 0.04, 0.05), (0, -0.385, 0.01)), body, "Lightbar")
    for k, x in enumerate((-0.3, 0.0, 0.3)):   # three docked scout drones
        D(torus(0.12, 0.028, (x, 0.05, 0.22), maj=14, mi=4), body, "Dock", bevel=None)
        W(ico(0.1, (x, 0.05, 0.3), sub=2), body, "DroneShell", bevel=None)
        R(ico(0.04, (x, -0.04, 0.31), sub=1, scale=(1, 0.6, 1)), body, "DroneLens")
    for sx in (-0.38, 0.38):
        for sy in (-0.24, 0.24):
            D(cyl(0.09, 0.07, (sx, sy, -0.17), verts=10), body, "Thruster")
            R(cyl(0.065, 0.02, (sx, sy, -0.215), verts=10), body, "ThrusterGlow", col=(1.0, 0.45, 0.2))
    D(cyl(0.012, 0.32, (0.42, 0.28, 0.32), verts=4), body, "Antenna", bevel=None)
    R(ico(0.03, (0.42, 0.28, 0.5), sub=1), body, "AntennaTip")
    return root, {"Carrier": "Root_Mesh", "Body": "Body_Mesh"}


# ================================================================= PRIME WALKER (boss)
def prime_walker():
    H[0] = 3.7
    root = empty("PrimeWalker")
    body = empty("Body", (0, 0, 0), root)
    D(box((1.0, 0.7, 0.35), (0, 0.08, 1.45)), body, "Pelvis", bevel=0.06)
    big = dict(thigh=(0.42, 0.5, 0.62), shin=(0.4, 0.5, 0.58), foot=(0.6, 0.8, 0.2), knee=0.2)
    for nm, x in (("LegA_L", 0.44), ("LegB_R", -0.44)):
        lp = leg(nm, (x, 0.08, 1.45), body, **big)
        D(rod((0, 0.22, -0.1), (0, 0.3, -1.0), 0.06, 8), lp, "Piston")
    W(box((1.9, 1.3, 1.25), (0, 0.1, 2.3)), body, "Chest", bevel=0.18)
    HZ(box((1.92, 0.08, 0.14), (0, -0.56, 2.8)), body, "HazardBand")
    for k in range(7):
        D(box((0.1, 0.09, 0.15), (-0.75 + k * 0.25, -0.57, 2.8), rot=(0, 0.6, 0)), body, "HazardStripe", bevel=None)
    D(box((1.3, 0.12, 0.85), (0, -0.56, 2.22)), body, "ChestPanel", bevel=0.06)
    R(ico(0.34, (0, -0.64, 2.24), sub=3), body, "Core")
    D(torus(0.44, 0.07, (0, -0.64, 2.24), rot=(math.radians(90), 0, 0), maj=20, mi=4), body, "CoreRing", bevel=None)
    for k in range(6):
        a = k * math.tau / 6
        D(box((0.08, 0.1, 0.16), (0.44 * math.cos(a), -0.7, 2.24 + 0.44 * math.sin(a)), rot=(0, -a, 0)), body, "CoreBolt", bevel=None)
    # head: three red eyes and a crown of red spikes
    D(box((0.74, 0.62, 0.45), (0, -0.2, 3.12)), body, "Head", bevel=0.1)
    D(box((0.6, 0.06, 0.16), (0, -0.52, 3.12)), body, "VisorFrame", bevel=None)
    for k, x in enumerate((-0.18, 0.0, 0.18)):
        R(ico(0.07 if k != 1 else 0.085, (x, -0.55, 3.13), sub=2, scale=(1, 0.6, 1)), body, "Eye")
    for k in range(5):
        a = math.radians(-50 + k * 25)
        sp = cyl(0.08, 0.46, (math.sin(a) * 0.32, -0.2 + 0.05 * abs(k - 2), 3.5 + 0.06 * (2 - abs(k - 2))), verts=6, r2=0.0, rot=(0, a * 0.6, 0))
        R(sp, body, "Spike")
    for k in range(4):
        R(box((1.2, 0.07, 0.04), (0, 0.25 + k * 0.17, 2.94)), body, "Vent")
    # shoulders, arm cannons, missile pods
    for s in (-1, 1):
        W(box((0.78, 0.98, 0.62), (s * 1.27, 0.1, 2.72)), body, "Shoulder", bevel=0.14)
        HZ(box((0.1, 1.0, 0.1), (s * 1.27, 0.1, 3.06)), body, "ShoulderStripe")
        D(cyl(0.24, 1.25, (s * 1.3, -0.15, 1.95), verts=12), body, "Arm")
        D(cyl(0.32, 0.95, (s * 1.3, -0.55, 1.35), verts=12, rot=(math.radians(90), 0, 0)), body, "Cannon", bevel=0.03)
        for k in range(3):
            D(torus(0.33, 0.04, (s * 1.3, -0.25 - k * 0.28, 1.35), rot=(math.radians(90), 0, 0), maj=14, mi=3), body, "CannonRing", bevel=None)
        R(cyl(0.18, 0.06, (s * 1.3, -1.03, 1.35), verts=12, rot=(math.radians(90), 0, 0)), body, "Muzzle")
        D(box((0.5, 0.45, 0.3), (s * 1.25, 0.35, 3.15)), body, "MissilePod", bevel=0.05)
        for i in range(2):
            for j in range(2):
                R(cyl(0.06, 0.04, (s * 1.25 + (i - 0.5) * 0.2, 0.35 + (j - 0.5) * 0.2, 3.31), verts=8), body, "MissileTip")
    for k in range(3):
        D(cyl(0.07, 0.6, (-0.3 + k * 0.3, 0.72, 2.9), verts=8), body, "Stack")
        R(cyl(0.05, 0.02, (-0.3 + k * 0.3, 0.72, 3.21), verts=8), body, "StackGlow", col=(1.0, 0.4, 0.12))
    return root, {"PrimeWalker": "Root_Mesh", "Body": "Body_Mesh"}


BUILD = [("scout", scout), ("walker", walker), ("brute", brute), ("carrier", carrier), ("prime_walker", prime_walker)]
for rid, fn in BUILD:
    if ONLY and rid not in ONLY.split(","):
        continue
    sty.reset(101 + len(rid))
    root, names = fn()
    # leg meshes must not start with "LegA"/"LegB": game.gd swings every node matching LegA*/LegB*
    names.update({"LegA_L": "ThighL_Mesh", "LegB_R": "ThighR_Mesh"})
    sty.finish(os.path.join(OUT, f"{rid}.glb"), outline_w=OUTLINE * (2.2 if rid == "prime_walker" else 1.0), names=names, ao_dist=0.3)
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        cam = sty.studio()
        h = H[0]
        sty.shoot(cam, os.path.join(PREVIEW, f"{rid}_hero.png"), target=(0, 0, h * 0.45), ortho=h * 1.45 if rid != "carrier" else 1.8, res=(450, 450))
    print("BUILT", rid)
