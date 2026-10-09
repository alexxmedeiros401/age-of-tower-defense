"""The Recursion: robot army for Age of Tower Defense. Run: python3 robots.py --out DIR"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp
from lp import mat, empty, cyl, ico, uvs, box, torus

OUT = sys.argv[sys.argv.index("--out") + 1]
lp.reset(3)

SHELL = mat("Shell", (0.74, 0.77, 0.83), 0.42, 0.15)
STEEL = mat("Steel", (0.50, 0.54, 0.60), 0.35, 0.65)
DARK = mat("Joint", (0.10, 0.11, 0.14), 0.5, 0.4)
RED = mat("RedGlow", (0.9, 0.05, 0.03), 0.4, 0.0, emit=(1.0, 0.03, 0.015), strength=2.2)
HAZ = mat("Hazard", (0.95, 0.52, 0.10), 0.4, 0.3)
THRUST = mat("Thruster", (1.0, 0.4, 0.1), 0.4, 0.0, emit=(1.0, 0.3, 0.03), strength=2.0)


def leg(name, hip, parent, thigh=(0.13, 0.15, 0.26), shin=0.07, foot=(0.15, 0.22, 0.07), length=0.5):
    p = empty(name, hip, parent)
    box(thigh, (0, 0, -thigh[2] / 2), SHELL, p, bevel=0.02)
    cyl(shin, length - thigh[2], (0, 0, -thigh[2] - (length - thigh[2]) / 2 + 0.02), DARK, p, verts=6)
    box(foot, (0, -0.03, -length + foot[2] / 2), STEEL, p, bevel=0.015)
    return p


# ------------------------------------------------------------------ WALKER
def walker():
    root = empty("Walker")
    body = empty("Body", (0, 0, 0), root)
    box((0.30, 0.20, 0.14), (0, 0, 0.56), DARK, body, bevel=0.02)
    leg("LegA_L", (0.11, 0, 0.55), body)
    leg("LegB_R", (-0.11, 0, 0.55), body)
    torso = ico(0.24, (0, 0, 0.84), SHELL, body, sub=2, scale=(1.15, 0.9, 1.05))
    ico(0.07, (0, -0.21, 0.86), RED, body, sub=1, name="Core")
    box((0.30, 0.14, 0.05), (0, 0.02, 1.07), DARK, body)
    head = uvs(0.16, (0, -0.01, 1.2), SHELL, body, seg=10, rings=6, scale=(1, 0.95, 0.8))
    box((0.22, 0.04, 0.045), (0, -0.145, 1.2), RED, body, name="Visor")
    cyl(0.035, 0.03, (0, 0, 1.33), RED, body, verts=8, name="TopLight")
    box((0.22, 0.12, 0.26), (0, 0.19, 0.88), STEEL, body, bevel=0.02)
    cyl(0.012, 0.32, (0.07, 0.22, 1.15), DARK, body, verts=4)
    ico(0.03, (0.07, 0.22, 1.32), RED, body, sub=1)
    for s in (-1, 1):
        cyl(0.05, 0.36, (s * 0.31, 0, 0.8), STEEL, body, verts=6, rot=(0, math.radians(s * 8), 0))
        ico(0.065, (s * 0.33, -0.01, 0.6), DARK, body, sub=1)
    cyl(0.035, 0.22, (-0.33, -0.12, 0.6), DARK, body, verts=6, rot=(math.radians(90), 0, 0))
    return root


# ------------------------------------------------------------------ SCOUT
def scout():
    root = empty("Scout")
    body = empty("Body", (0, 0, 0.85), root)
    uvs(0.2, (0, 0, 0), SHELL, body, seg=12, rings=8)
    torus(0.24, 0.045, (0, 0, -0.02), DARK, body, major=18)
    uvs(0.075, (0, -0.17, 0.02), RED, body, seg=8, rings=6, name="Eye")
    for s in (-1, 1):
        box((0.22, 0.12, 0.025), (s * 0.3, 0.04, 0.0), STEEL, body, rot=(0, math.radians(s * -14), 0))
    cyl(0.1, 0.12, (0, 0, -0.22), DARK, body, verts=8, r2=0.06)
    cyl(0.06, 0.05, (0, 0, -0.3), THRUST, body, verts=8, name="Thruster")
    cyl(0.03, 0.03, (0, 0, 0.21), RED, body, verts=6, name="TopLight")
    return root


# ------------------------------------------------------------------ BRUTE
def brute():
    root = empty("Brute")
    body = empty("Body", (0, 0, 0), root)
    box((0.45, 0.32, 0.18), (0, 0.04, 0.58), DARK, body, bevel=0.03)
    leg("LegA_L", (0.17, 0.04, 0.6), body, thigh=(0.2, 0.24, 0.26), shin=0.1, foot=(0.24, 0.32, 0.09), length=0.6)
    leg("LegB_R", (-0.17, 0.04, 0.6), body, thigh=(0.2, 0.24, 0.26), shin=0.1, foot=(0.24, 0.32, 0.09), length=0.6)
    box((0.78, 0.56, 0.58), (0, 0.06, 1.0), SHELL, body, bevel=0.07)
    box((0.52, 0.06, 0.36), (0, -0.24, 1.0), DARK, body, bevel=0.03)
    ico(0.1, (0, -0.28, 1.02), RED, body, sub=1, name="Core")
    box((0.3, 0.26, 0.18), (0, -0.12, 1.36), STEEL, body, bevel=0.03)
    box((0.22, 0.03, 0.045), (0, -0.26, 1.37), RED, body, name="Visor")
    for k in range(3):
        box((0.44, 0.05, 0.03), (0, 0.14 + k * 0.09, 1.31), RED, body, name="Vent")
    for s in (-1, 1):
        box((0.3, 0.42, 0.26), (s * 0.5, 0.06, 1.24), SHELL, body, bevel=0.06)
        cyl(0.09, 0.52, (s * 0.56, 0.0, 0.84), STEEL, body, verts=8)
        box((0.24, 0.26, 0.2), (s * 0.58, -0.04, 0.5), DARK, body, bevel=0.05)
        for f in range(3):
            box((0.05, 0.06, 0.06), (s * 0.58 + (f - 1) * 0.07, -0.18, 0.43), STEEL, body)
    return root


# ------------------------------------------------------------------ CARRIER
def carrier():
    root = empty("Carrier")
    body = empty("Body", (0, 0, 0.62), root)
    box((1.05, 0.72, 0.24), (0, 0, 0), HAZ, body, bevel=0.06)
    box((0.9, 0.62, 0.08), (0, 0, 0.15), SHELL, body, bevel=0.03)
    box((0.7, 0.05, 0.06), (0, -0.37, 0.0), RED, body, name="Lightbar")
    for k in range(4):
        box((0.12, 0.74, 0.05), (-0.39 + k * 0.26, 0, -0.1), DARK, body)
    for k, x in enumerate((-0.3, 0.0, 0.3)):
        torus(0.11, 0.025, (x, 0.05, 0.2), DARK, body, major=12)
        d = uvs(0.1, (x, 0.05, 0.29), SHELL, body, seg=10, rings=6)
        uvs(0.035, (x, -0.04, 0.3), RED, body, seg=6, rings=4)
    for sx in (-0.38, 0.38):
        for sy in (-0.24, 0.24):
            cyl(0.08, 0.06, (sx, sy, -0.16), THRUST, body, verts=8, name="Thruster")
    cyl(0.012, 0.3, (0.42, 0.28, 0.32), DARK, body, verts=4)
    ico(0.03, (0.42, 0.28, 0.48), RED, body, sub=1)
    return root


# ------------------------------------------------------------------ PRIME WALKER (boss)
def prime():
    root = empty("PrimeWalker")
    body = empty("Body", (0, 0, 0), root)
    big = dict(thigh=(0.42, 0.5, 0.6), shin=0.2, foot=(0.55, 0.75, 0.2), length=1.45)
    box((1.0, 0.7, 0.35), (0, 0.08, 1.45), DARK, body, bevel=0.06)
    leg("LegA_L", (0.42, 0.08, 1.45), body, **big)
    leg("LegB_R", (-0.42, 0.08, 1.45), body, **big)
    box((1.9, 1.3, 1.25), (0, 0.1, 2.3), SHELL, body, bevel=0.15)
    box((1.3, 0.12, 0.85), (0, -0.56, 2.3), DARK, body, bevel=0.06)
    ico(0.32, (0, -0.62, 2.32), RED, body, sub=2, name="Core")
    torus(0.42, 0.06, (0, -0.62, 2.32), STEEL, body, rot=(math.radians(90), 0, 0), major=20)
    # head with crown of red spikes
    box((0.7, 0.6, 0.42), (0, -0.2, 3.1), STEEL, body, bevel=0.08)
    box((0.5, 0.04, 0.08), (0, -0.51, 3.12), RED, body, name="Visor")
    for k in range(5):
        a = math.radians(-50 + k * 25)
        cyl(0.07, 0.42, (math.sin(a) * 0.32, -0.2 + 0.05 * abs(k - 2), 3.45 + 0.06 * (2 - abs(k - 2))),
            RED, body, verts=5, r2=0.0, rot=(0, a * 0.6, 0), name="Spike")
    for k in range(4):
        box((1.2, 0.07, 0.04), (0, 0.25 + k * 0.17, 2.94), RED, body, name="Vent")
    # shoulders and arm cannons
    for s in (-1, 1):
        box((0.75, 0.95, 0.6), (s * 1.25, 0.1, 2.7), SHELL, body, bevel=0.12)
        cyl(0.24, 1.25, (s * 1.3, -0.15, 1.95), STEEL, body, verts=10)
        cyl(0.3, 0.9, (s * 1.3, -0.55, 1.35), DARK, body, verts=10, rot=(math.radians(90), 0, 0))
        cyl(0.16, 0.06, (s * 1.3, -1.0, 1.35), RED, body, verts=10, rot=(math.radians(90), 0, 0), name="Muzzle")
        for k in range(3):
            cyl(0.06, 0.5, (s * (1.1 + k * 0.2), 0.45, 3.2), DARK, body, verts=5)
    return root


# ------------------------------------------------------------------ BRONZE AGE ROBOTS
CYAN = mat("ShieldGlow", (0.3, 0.85, 1.0), 0.2, 0.0, emit=(0.15, 0.7, 1.0), strength=1.6)
GREEN = mat("RepairGlow", (0.3, 1.0, 0.4), 0.3, 0.0, emit=(0.2, 1.0, 0.3), strength=2.0)


def shield_bot():
    root = empty("ShieldBot")
    body = empty("Body", (0, 0, 0), root)
    box((0.32, 0.22, 0.14), (0, 0.04, 0.55), DARK, body, bevel=0.02)
    leg("LegA_L", (0.13, 0.04, 0.55), body, thigh=(0.15, 0.17, 0.24), shin=0.08, foot=(0.17, 0.25, 0.07), length=0.52)
    leg("LegB_R", (-0.13, 0.04, 0.55), body, thigh=(0.15, 0.17, 0.24), shin=0.08, foot=(0.17, 0.25, 0.07), length=0.52)
    box((0.5, 0.36, 0.42), (0, 0.05, 0.86), SHELL, body, bevel=0.06)
    ico(0.07, (0, -0.14, 0.9), RED, body, sub=1, name="Core")
    box((0.26, 0.2, 0.14), (0, 0.02, 1.15), STEEL, body, bevel=0.03)
    box((0.2, 0.03, 0.04), (0, -0.09, 1.16), RED, body, name="Visor")
    # emitter arm and the curved energy shield in front
    box((0.08, 0.3, 0.08), (0.3, -0.12, 0.9), DARK, body)
    for k in range(5):
        a = math.radians(-50 + k * 25)
        box((0.17, 0.035, 0.62), (math.sin(a) * 0.42, -0.38 - (1 - math.cos(a)) * -0.12, 0.86), CYAN, body,
            rot=(0, 0, a), name="Shield")
    box((0.62, 0.05, 0.05), (0, -0.4, 1.19), STEEL, body)
    box((0.62, 0.05, 0.05), (0, -0.4, 0.54), STEEL, body)
    return root


def repair_drone():
    root = empty("RepairDrone")
    body = empty("Body", (0, 0, 0.9), root)
    uvs(0.2, (0, 0, 0), SHELL, body, seg=12, rings=8, scale=(1.1, 1.1, 0.8))
    box((0.16, 0.05, 0.05), (0, -0.21, 0.02), GREEN, body)  # cross light
    box((0.05, 0.05, 0.16), (0, -0.21, 0.02), GREEN, body)
    for s in (-1, 1):
        cyl(0.12, 0.03, (s * 0.32, 0.0, 0.12), DARK, body, verts=10)        # rotor hubs
        box((0.42, 0.04, 0.02), (s * 0.32, 0.0, 0.14), STEEL, body, rot=(0, 0, 0.6))
        cyl(0.02, 0.28, (s * 0.15, -0.08, -0.2), STEEL, body, verts=5, rot=(0.3, 0, s * 0.3))  # tool arms
        ico(0.045, (s * 0.2, -0.12, -0.33), GREEN, body, sub=1)
    cyl(0.07, 0.08, (0, 0, -0.18), DARK, body, verts=8)
    cyl(0.04, 0.03, (0, 0, -0.24), THRUST, body, verts=8)
    return root


def siege_crawler():
    root = empty("SiegeCrawler")
    body = empty("Body", (0, 0, 0), root)
    # six legs: alternate gait groups A/B
    for i, (x, y) in enumerate([(0.75, -0.7), (0.85, 0.05), (0.75, 0.8), (-0.75, -0.7), (-0.85, 0.05), (-0.75, 0.8)]):
        grp = "A" if (i % 2 == 0) == (x > 0) else "B"
        side = 1 if x > 0 else -1
        hip = empty(f"Leg{grp}_{i}", (side * 0.5, y, 1.05), body)
        # thigh rises from the hip to the knee, shin drops from the knee to the foot
        box((0.76, 0.2, 0.2), (side * 0.335, 0, 0.15), STEEL, hip, bevel=0.03, rot=(0, -side * 0.42, 0))
        ico(0.13, (side * 0.67, 0, 0.3), DARK, hip, sub=1)
        box((0.17, 0.17, 1.34), (side * 0.76, 0, -0.35), DARK, hip, bevel=0.03, rot=(0, -side * 0.14, 0))
        cyl(0.14, 0.1, (side * 0.85, 0, -1.0), STEEL, hip, verts=8)
    # armored hull
    box((1.3, 1.9, 0.62), (0, 0.05, 1.15), SHELL, body, bevel=0.14)
    box((1.0, 1.5, 0.3), (0, 0.15, 1.55), STEEL, body, bevel=0.08)
    for k in range(4):
        box((1.36, 0.08, 0.06), (0, -0.55 + k * 0.38, 1.47), RED, body, name="Vent")
    # battering ram with bronze-looted plates in front
    box((0.5, 0.7, 0.4), (0, -1.2, 1.05), DARK, body, bevel=0.06)
    cyl(0.2, 0.7, (0, -1.7, 1.05), STEEL, body, verts=8, rot=(math.radians(90), 0, 0))
    cyl(0.26, 0.2, (0, -2.05, 1.05), STEEL, body, verts=8, r2=0.1, rot=(math.radians(90), 0, 0))
    for s in (-1, 0, 1):
        ico(0.09, (s * 0.24, -0.98, 1.3), RED, body, sub=1, name="Eye")
    # shield generator dome
    uvs(0.32, (0, 0.45, 1.75), CYAN, body, seg=12, rings=6, scale=(1, 1, 0.6), name="Dome")
    torus(0.36, 0.05, (0, 0.45, 1.72), DARK, body, major=16)
    for s in (-1, 1):
        cyl(0.04, 0.6, (s * 0.45, 0.85, 1.95), DARK, body, verts=5)
        ico(0.06, (s * 0.45, 0.85, 2.27), RED, body, sub=1)
    return root


cam = lp.stage()
lineup = [("scout", scout, 0.0), ("walker", walker, 0.0), ("brute", brute, 0.0), ("carrier", carrier, 0.0), ("prime_walker", prime, 0.0),
          ("shield_bot", shield_bot, 0.0), ("repair_drone", repair_drone, 0.0), ("siege_crawler", siege_crawler, 0.0)]
roots = []
for name, fn, _ in lineup:
    r = fn()
    lp.export_glb(r, os.path.join(OUT, "robots", f"{name}.glb"))
    roots.append((name, r))

# preview lineup: little robots in front, boss behind
pos = {"scout": (-2.2, -0.6), "walker": (-1.1, -0.9), "brute": (0.3, -0.9), "carrier": (1.9, -0.7), "prime_walker": (-1.6, 2.2),
       "shield_bot": (3.2, -0.9), "repair_drone": (4.3, -0.6), "siege_crawler": (2.6, 2.4)}
for name, r in roots:
    r.location = (*pos[name], 0)
    r.rotation_euler = (0, 0, math.radians(-18))
lp.shoot(cam, os.path.join(OUT, "robots_lineup.png"), (1.0, 0.6, 1.3), 8.6, res=1200, pos_dir=(0.55, -1.2, 0.55))
print("DONE")
