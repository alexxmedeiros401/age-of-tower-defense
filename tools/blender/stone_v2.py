"""Stone Age towers, v2 art pass (stylized pipeline, see sty.py).

Rock Slinger, Club Warrior, Boulder Catapult, Tar Pit Shaman. Same footprints and game pivots as the
v1 models (game.gd rotates them in code):
  Rock Slinger: Caveman (yaw), Shoulder_R (throw), SpinSling (whirls overhead, spun in code)
  others:       Yaw, Arm (+x = forward swing), Orb (shaman's pulse)

Usage: python3 stone_v2.py -- --out assets [--only rock_slinger,ugo] [--preview DIR] [--outline 0.06]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sty
from sty import P, reg, cyl, ico, uvs, torus, box, rod, empty, jitter, lerp, mul, point_at
from mathutils import Vector, noise

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default
OUT = arg("--out", "assets")   # towers go to OUT/towers, heros to OUT/heroes
ONLY = arg("--only")
PREVIEW = arg("--preview")
OUTLINE = float(arg("--outline", "0.06"))


# ---------------------------------------------------------------- shared people parts
def jag_tunic(parent, col, r=0.37, rt=0.3, h=0.48, z=0.5, verts=14, hi=P["fur_hi"], name="Tunic"):
    t = cyl(r, h, (0, 0, z), verts=verts, r2=rt)
    for v in t.data.vertices:
        if v.co.z < 0:
            k = round((math.atan2(v.co.y, v.co.x) % math.tau) / (math.tau / verts))
            if k % 2:
                v.co.z -= 0.08
            v.co.x *= 1.03
            v.co.y *= 1.03
    jitter(t, 0.012)
    return reg(t, col, parent=parent, var=0, name=name,
               colfn=lambda p, n, col=col, hi=hi: lerp(col, hi, 0.5 + 1.2 * noise.noise(p * 7.0)))


def cave_body(body, tunic=P["fur"], spots=P["fur_dark"], skin=P["skin"], hair=P["hair"], paint=None,
              left_arm="hang", beard=True, angry=True, head=True):
    """Stylized caveman body under `body` (an Empty, local units). Front is -Y. Right arm is NOT built."""
    with sty.soft_ao():
        _cave_body(body, tunic, spots, skin, hair, paint, left_arm, beard, angry, head)


def _cave_body(body, tunic, spots, skin, hair, paint, left_arm, beard, angry, head):
    for side in (-1, 1):
        reg(cyl(0.095, 0.34, (side * 0.13, 0, 0.21), verts=10, r2=0.082), skin, parent=body, var=0.04, name="Leg")
        reg(ico(0.12, (side * 0.13, -0.05, 0.05), scale=(1.0, 1.35, 0.58)), P["leather"], parent=body, var=0.04, name="Boot")
        reg(torus(0.09, 0.035, (side * 0.13, 0, 0.12), maj=10, mi=4), tunic, parent=body, var=0.06, name="BootCuff")
    reg(ico(0.3, (0, 0, 0.66), scale=(1.05, 0.85, 1.0)), skin, parent=body, var=0.03, name="Torso")
    jag_tunic(body, tunic)
    for sx, sz in ((0.18, 0.55), (-0.14, 0.42), (0.05, 0.68), (-0.22, 0.62)):
        reg(ico(0.06, (sx, -0.31, sz), scale=(1.3, 0.35, 1.0)), spots, parent=body, var=0.04, name="FurSpot")
    reg(rod((0.24, -0.02, 0.4), (-0.26, -0.02, 0.92), 0.065, 8), tunic, parent=body, var=0.06, name="Strap")
    reg(torus(0.37, 0.042, (0, 0, 0.33), maj=18, mi=4), P["leather"], parent=body, var=0.04, name="Belt")
    reg(cyl(0.025, 0.12, (0.0, -0.405, 0.33), verts=6, rot=(0, math.radians(90), 0)), P["bone"], matk="satin", parent=body, name="BeltToggle")
    if paint:
        for k, (x, z) in enumerate(((-0.12, 0.78), (0.0, 0.8), (0.12, 0.78))):
            reg(box((0.035, 0.02, 0.16), (x, -0.255, z), rot=(0.25, 0, 0)), paint, parent=body, var=0.03, name="WarPaint")
    if head:
        sty.caveman_head(body, (0, -0.02, 1.13), hair=hair, beard=beard, angry=angry, skin=skin)
    if left_arm == "hang":
        reg(rod((0.33, 0, 0.9), (0.4, 0, 0.62), 0.08, 10), skin, parent=body, var=0.03, name="UpperArm_L")
        reg(torus(0.085, 0.032, (0.39, 0, 0.66), rot=(0, math.radians(-14), 0), maj=10, mi=4), tunic, parent=body, var=0.06, name="ArmBand_L")
        reg(cyl(0.1, 0.27, (0.42, -0.02, 0.5), verts=10, r2=0.08, rot=(0, math.radians(-8), 0)), skin, parent=body, var=0.03, name="Forearm_L")
        reg(ico(0.115, (0.43, -0.04, 0.34)), skin, parent=body, var=0.03, name="Hand_L")


def raised_arm(pivot, skin=P["skin"], band=P["fur"], thick=1.0):
    """Upper arm, band, forearm and fist along the pivot's +Z axis. Returns the fist's z."""
    with sty.soft_ao():
        return _raised_arm(pivot, skin, band, thick)


def _raised_arm(pivot, skin, band, thick):
    t = thick
    reg(cyl(0.085 * t, 0.3, (0, 0, 0.15), verts=10), skin, parent=pivot, var=0.03, name="UpperArm")
    reg(torus(0.09 * t, 0.033, (0, 0, 0.28), maj=10, mi=4), band, parent=pivot, var=0.06, name="ArmBand")
    reg(cyl(0.085 * t, 0.26, (0, 0, 0.42), verts=10, r2=0.102 * t), skin, parent=pivot, var=0.03, name="Forearm")
    reg(ico(0.118 * t, (0, 0, 0.6)), skin, parent=pivot, var=0.03, name="Fist")
    return 0.6


def palisade(root, a0=70, a1=290, n=11, r=1.33, hmin=0.85, hmax=1.15):
    lash = {0.45: [], 0.80: []}
    for i in range(n):
        a = math.radians(a0 + i * (a1 - a0) / max(n - 1, 1))
        h = random.uniform(hmin, hmax)
        x, y = r * math.cos(a), r * math.sin(a)
        tilt = (random.uniform(-0.07, 0.07), random.uniform(-0.07, 0.07), random.uniform(0, 6.28))
        s = cyl(0.1, h, (x, y, 0.18 + h / 2), verts=7, rot=tilt)
        reg(s, P["wood"], parent=root, bevel=0.02, var=0.12, name="Stake")
        R = s.rotation_euler.to_matrix()
        foot = Vector((x, y, 0.18))
        tip = cyl(0.1, 0.27, foot + R @ Vector((0, 0, h + 0.135)), verts=7, r2=0.0, rot=tilt)
        reg(tip, P["wood_cut"], parent=root, var=0.06, name="StakeTip")
        for hh in lash:
            t = torus(0.112, 0.026, foot + R @ Vector((0, 0, hh)), rot=tilt, maj=8, mi=3)
            reg(t, P["rope"], parent=root, var=0.06, name="Lashing")
            lash[hh].append(foot + R @ Vector((0, 0, hh)))
    for hh, pts in lash.items():
        for p0, p1 in zip(pts, pts[1:]):
            mid = (p0 + p1) / 2 - Vector((0, 0, 0.05))
            reg(rod(p0, mid, 0.018, 4), P["rope"], parent=root, var=0.05, name="Rope")
            reg(rod(mid, p1, 0.018, 4), P["rope"], parent=root, var=0.05, name="Rope")


def campfire(root, fx, fy, z=0.2, s=1.0):
    for i in range(7):
        a = i * math.tau / 7
        o = ico(0.07 * s, (fx + 0.2 * s * math.cos(a), fy + 0.2 * s * math.sin(a), z + 0.03), sub=1, scale=(1.2, 1, 0.75))
        reg(o, P["stone_dark"], parent=root, smooth=False, var=0.12, name="FireStone")
    for i in range(3):
        a = i * math.tau / 3 + 0.4
        p0 = Vector((fx + 0.17 * s * math.cos(a), fy + 0.17 * s * math.sin(a), z + 0.01))
        reg(rod(p0, (fx, fy, z + 0.22 * s), 0.035 * s, 5), P["wood_dark"], parent=root, var=0.1, name="FireLog",
            colfn=lambda p, n, z=z: lerp(P["wood_dark"], (0.05, 0.03, 0.02), (p.z - z - 0.05) / 0.15))
    fl = empty("FlickerFire", (fx, fy, z + 0.04), root)
    for r, h, dx, dy in ((0.16, 0.52, 0, 0), (0.09, 0.38, 0.06, 0.03), (0.085, 0.34, -0.05, -0.04)):
        f = cyl(r * s, h * s, (dx * s, dy * s, h * s / 2), verts=7, r2=0.0)
        for v in f.data.vertices:
            if v.co.z > 0:
                v.co.x += random.uniform(-0.02, 0.02)
        reg(f, P["flame"], matk="flame", parent=fl, var=0, name="Flame", noao=True, noocc=True, no_outline=True,
            colfn=lambda p, n, z=z, h=h * s: lerp(P["flame"], P["flame_tip"], (p.z - z) / h))


def boulder(root, loc, r, scale=(1.2, 1.0, 0.75), col=None, name="Boulder"):
    o = ico(r, loc, sub=1, scale=scale)
    jitter(o, r * 0.12)
    return reg(o, col or P["stone_dark"], parent=root, smooth=False, var=0.1, name=name)


# ================================================================= ROCK SLINGER
def rock_slinger():
    root = empty("RockSlinger")
    sty.grass_base(root, tufts=10, cobbles=16)
    palisade(root)
    # mammoth tusk arch, rope-wrapped roots
    for side in (-1, 1):
        bpy.ops.curve.primitive_bezier_curve_add()
        c = bpy.context.object
        p0, p1 = c.data.splines[0].bezier_points
        p0.co = Vector((side * 0.95, -1.15, 0.22)); p0.handle_left = p0.co + Vector((0, 0, -0.3)); p0.handle_right = p0.co + Vector((side * 0.45, -0.2, 1.1))
        p1.co = Vector((side * 0.12, -1.25, 2.05)); p1.handle_left = p1.co + Vector((side * 0.75, -0.05, 0.1)); p1.handle_right = p1.co + Vector((-side * 0.2, 0, 0.1))
        c.data.bevel_depth = 0.135
        c.data.bevel_resolution = 2
        c.data.resolution_u = 10
        c.data.use_fill_caps = True
        bpy.ops.curve.primitive_bezier_curve_add()
        taper = bpy.context.object
        tp = taper.data.splines[0].bezier_points
        tp[0].co = Vector((0, 1, 0)); tp[0].handle_left = Vector((-0.2, 1, 0)); tp[0].handle_right = Vector((0.3, 1, 0))
        tp[1].co = Vector((1, 0.12, 0)); tp[1].handle_left = Vector((0.7, 0.4, 0)); tp[1].handle_right = Vector((1.2, 0.1, 0))
        c.data.taper_object = taper
        cp = (p0.co.copy(), p0.handle_right.copy(), p1.handle_left.copy(), p1.co.copy())
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = c
        c.select_set(True)
        bpy.ops.object.convert(target="MESH")
        c = bpy.context.object
        bpy.data.objects.remove(taper)
        reg(c, P["bone"], matk="satin", parent=root, var=0, name="Tusk",
            colfn=lambda p, n: lerp(P["bone_old"], P["bone"], (p.z - 0.2) / 0.9))

        def tusk_center(z, cp=cp):
            for i in range(400):
                t = i / 400
                u = 1 - t
                q = cp[0] * u ** 3 + cp[1] * 3 * u * u * t + cp[2] * 3 * u * t * t + cp[3] * t ** 3
                if q.z >= z:
                    return q
            return cp[3]
        for k in range(3):
            z = 0.34 + k * 0.09
            d = (tusk_center(z + 0.06) - tusk_center(z - 0.06)).normalized()
            reg(torus(0.15 - k * 0.008, 0.03, tusk_center(z), maj=12, mi=4), P["rope"], parent=root, var=0.05, name="TuskWrap").rotation_euler = \
                Vector((0, 0, 1)).rotation_difference(d).to_euler()
    # log deck
    plat_z = 0.95
    top = 0.25 + plat_z
    for x, y in ((-0.5, -0.45), (0.5, -0.45), (-0.5, 0.45), (0.5, 0.45)):
        reg(cyl(0.11, plat_z + 0.05, (x, y, 0.2 + (plat_z + 0.05) / 2), verts=7), P["wood_dark"], parent=root, bevel=0.025, var=0.1, name="Post")
        reg(torus(0.12, 0.026, (x, y, top - 0.2), maj=8, mi=3), P["rope"], parent=root, var=0.05, name="PostLash")
    for x in (-0.5, 0.5):
        reg(cyl(0.09, 1.3, (x, 0, top - 0.12), verts=7, rot=(math.radians(90), 0, 0)), P["wood_dark"], parent=root, bevel=0.02, var=0.1, name="Beam")
    for i in range(6):
        L = random.uniform(1.32, 1.46)
        xo = random.uniform(-0.05, 0.05)
        y = -0.55 + i * 0.22
        reg(cyl(0.105, L, (xo, y, top), verts=8, rot=(0, math.radians(90), 0)), P["wood"], parent=root, bevel=0.03, var=0.12, name="Log")
        for sgn in (-1, 1):
            ex = xo + sgn * (L / 2 + 0.004)
            reg(cyl(0.088, 0.012, (ex, y, top), verts=8, rot=(0, math.radians(90), 0)), P["wood_cut"], parent=root, var=0.05, name="EndGrain")
            reg(cyl(0.042, 0.012, (ex + sgn * 0.004, y, top), verts=8, rot=(0, math.radians(90), 0)), P["wood"], parent=root, var=0.05, name="EndRing")
    for side in (-1, 1):
        reg(cyl(0.05, 1.3, (side * 0.19, -0.97, 0.76), verts=6, rot=(math.radians(-25), 0, 0)), P["wood_dark"], parent=root, bevel=0.012, var=0.08, name="LadderRail")
    for k in range(4):
        z = 0.42 + k * 0.24
        reg(cyl(0.036, 0.46, (0, -1.08 + k * 0.11, z), verts=6, rot=(0, math.radians(90), 0)), P["wood"], parent=root, var=0.1, name="Rung")
    # ammo basket on the deck, rock pile and campfire on the ground
    deck = top + 0.1
    bx, by = 0.42, 0.32
    reg(cyl(0.22, 0.24, (bx, by, deck + 0.1), verts=12, r2=0.27), P["wicker"], parent=root, bevel=0.02, var=0.04, name="Basket")
    for z in (0.02, 0.1, 0.18):
        reg(torus(0.225 + z * 0.2, 0.018, (bx, by, deck + z), maj=14, mi=3), P["wicker"], parent=root, var=0, name="Weave",
            colfn=lambda p, n: mul(P["wicker"], 0.62))
    for i in range(7):
        r = random.uniform(0.08, 0.11)
        a = i * 0.9
        boulder(root, (bx + 0.11 * math.cos(a) * (i > 0), by + 0.11 * math.sin(a) * (i > 0), deck + 0.25 + (0.06 if i == 0 else 0)), r,
                scale=(1, 1, 0.8), col=P["stone"] if i % 2 else P["stone_dark"], name="AmmoRock")
    for x, y, r in ((1.0, 0.25, 0.27), (1.25, 0.02, 0.17), (-1.0, -0.62, 0.22), (-0.85, 0.48, 0.15)):
        boulder(root, (x, y, 0.26), r)
    campfire(root, 1.0, -0.5)
    # banner pole: ochre handprint on a hide, horned skull on top (back-right, faces the camera)
    rig = empty("BannerRig", (0.88, 0.42, 0), root, rot=(0, 0, math.radians(41)))
    reg(cyl(0.06, 2.35, (0, 0, 0.18 + 1.175), verts=7), P["wood_dark"], parent=rig, bevel=0.015, var=0.08, name="Pole")
    reg(cyl(0.035, 0.66, (0.31, 0, 2.36), verts=6, rot=(0, math.radians(90), 0)), P["wood"], parent=rig, bevel=0.01, name="Crossbar")
    nx, nz = 6, 8
    bv, bf = [], []
    for j in range(nz + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / nz
            z = 2.32 - v * 0.8 + (0.08 if (j == nz and i % 2) else 0.0)
            bv.append((0.06 + u * 0.54, 0.018 * math.sin(u * math.pi * 2.5) * (0.4 + v), z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            bf.append((a, a + 1, a + nx + 2, a + nx + 1))
    banner = sty.mesh_from("Banner", bv, bf)
    reg(banner, P["hide"], parent=rig, var=0, name="Banner",
        colfn=lambda p, n: lerp(P["hide"], mul(P["hide"], 0.55), (1.75 - p.z) / 0.3))
    sol = banner.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness = 0.02
    sol.offset = 0
    hx, hz = 0.33, 1.9
    reg(ico(0.075, (hx, -0.05, hz), scale=(1.0, 0.15, 1.1)), P["ochre"], parent=rig, var=0.03, name="HandPalm")
    for fxo, ang, ln in ((-0.045, -24, 0.1), (-0.015, -8, 0.12), (0.016, 6, 0.12), (0.045, 20, 0.095), (-0.07, -62, 0.09)):
        base = Vector((hx + fxo, -0.05, hz + (0.05 if ang > -40 else -0.01)))
        d = Vector((math.sin(math.radians(ang)), 0, math.cos(math.radians(ang))))
        f = cyl(0.022, ln, base + d * ln / 2, verts=6, rot=(0, math.radians(ang), 0))
        f.scale = (1, 0.4, 1)
        reg(f, P["ochre"], parent=rig, var=0.03, name="HandFinger")
    horned_skull(rig, (0, 0, 2.6))
    # the slinger
    man = empty("Caveman", (-0.1, -0.05, deck), root)
    man.scale = (1.3, 1.3, 1.3)
    cave_body(man)
    spare = reg(ico(0.09, (0.43, -0.14, 0.32), sub=1, scale=(1, 0.9, 0.8)), P["stone"], parent=man, smooth=False, var=0.08, name="SpareRock")
    reg(cyl(0.028, 0.24, (0.09, 0.07, 1.48), verts=6, rot=(0.2, math.radians(70), 0.5)), P["bone"], matk="satin", parent=man, name="HairBone")
    reg(ico(0.09, (0, 0.06, 1.45), sub=2), P["hair"], parent=man, var=0.04, name="HairBun")
    for k in range(6):
        az = math.radians(-35 + k * 40)
        el = math.radians(random.uniform(25, 55))
        d = Vector((math.sin(az) * math.cos(el), abs(math.cos(az)) * math.cos(el), math.sin(el)))
        sp = cyl(0.075, 0.18, Vector((0, 0.04, 1.21)) + d * 0.27, verts=6, r2=0.0)
        point_at(sp, d)
        reg(sp, P["hair"], parent=man, var=0.08, name="HairSpike")
    shoulder = empty("Shoulder_R", (-0.33, 0, 0.92), man, rot=(math.radians(-10), math.radians(-38), 0))
    z = raised_arm(shoulder)
    sling = empty("SpinSling", (0, 0, z + 0.04), shoulder)
    for dy in (-0.028, 0.028):
        reg(rod((0, 0, 0), (0.42, dy, -0.02), 0.017, 4), P["rope"], parent=sling, var=0, name="SlingCord")
    reg(ico(0.085, (0.45, 0, -0.03), scale=(1.0, 0.85, 0.55)), P["leather"], parent=sling, name="SlingPouch")
    reg(ico(0.085, (0.45, 0, 0.02), sub=1, scale=(1, 1, 0.85)), P["stone"], parent=sling, smooth=False, var=0, name="SlingRock")
    return root, {"RockSlinger": "Tower_Static", "Caveman": "Caveman_Body", "Shoulder_R": "Arm_R_Mesh",
                  "SpinSling": "Sling_Mesh", "BannerRig": "Banner_Mesh", "FlickerFire": "Fire_Mesh"}


def horned_skull(parent, c, s=1.0):
    x, y, z = c
    reg(ico(0.1 * s, (x, y, z), scale=(1.0, 1.15, 0.78)), P["bone"], matk="satin", parent=parent, var=0.03, name="Skull")
    reg(ico(0.07 * s, (x, y - 0.13 * s, z - 0.04 * s), scale=(0.8, 1.3, 0.6)), P["bone"], matk="satin", parent=parent, var=0.03, name="Snout")
    for side in (-1, 1):
        reg(ico(0.03 * s, (x + side * 0.055 * s, y - 0.095 * s, z + 0.02 * s)), P["eye"], parent=parent, var=0, name="Socket")
        d = Vector((math.sin(math.radians(side * 60)), 0.15, math.cos(math.radians(side * 60))))
        hb = Vector((x + side * 0.08 * s, y + 0.02 * s, z + 0.04 * s))
        reg(cyl(0.042 * s, 0.26 * s, hb + d * 0.13 * s, verts=8, r2=0.0, rot=(0, math.radians(side * 60), 0)), P["bone"], matk="satin",
            parent=parent, var=0, name="Horn", colfn=lambda p, n, z=z: lerp(P["bone_old"], P["bone"], (p.z - z - 0.02) / (0.12 * s)))


# ================================================================= CLUB WARRIOR
def club_warrior():
    root = empty("ClubWarrior")
    sty.grass_base(root, tufts=9, cobbles=16)
    # trampled dirt ring where he fights
    ring = cyl(0.95, 0.03, (0, 0, 0.215), verts=16)
    jitter(ring, 0.01)
    reg(ring, P["dirt"], parent=root, var=0, name="Trampled", noocc=True,
        colfn=lambda p, n: lerp(P["dirt"], mul(P["dirt"], 1.25), 0.5 + noise.noise(p * 5.0)))
    # standing stones behind him (a little henge)
    for k, a in enumerate((95, 135, 175, 215, 255)):
        ar = math.radians(a)
        h = random.uniform(0.95, 1.35) if k != 2 else 1.55
        st = box((0.34, 0.22, h), (1.22 * math.cos(ar), 1.22 * math.sin(ar), 0.18 + h / 2), rot=(random.uniform(-0.06, 0.06), 0, ar))
        jitter(st, 0.03)
        reg(st, P["stone"], parent=root, bevel=0.05, var=0.1, name="Menhir",
            colfn=lambda p, n: lerp(P["moss"], P["stone"], (p.z - 0.15) * 2.2) if p.z < 0.6 else lerp(mul(P["stone_dark"], 1.1), mul(P["stone"], 0.95), 0.5 + 0.9 * noise.noise(p * 4)))
    lint = box((1.05, 0.3, 0.2), (1.22 * math.cos(math.radians(155)), 1.22 * math.sin(math.radians(155)) * 1.02, 1.62), rot=(0, 0, math.radians(155 - 90)))
    reg(lint, mul(P["stone"], 0.85), parent=root, bevel=0.05, var=0.1, name="Lintel")
    # trophy: mammoth skull and a bone pile
    sk = Vector((0.95, 0.6, 0.22))
    reg(ico(0.22, sk + Vector((0, 0, 0.16)), scale=(1.0, 1.25, 0.8)), P["bone"], matk="satin", parent=root, var=0.03, name="MammothSkull")
    reg(ico(0.12, sk + Vector((0, -0.25, 0.1)), scale=(1.0, 1.0, 0.9)), P["bone"], matk="satin", parent=root, var=0.03, name="SkullSnout")
    for side in (-1, 1):
        reg(ico(0.055, sk + Vector((side * 0.1, -0.2, 0.24))), P["eye"], parent=root, var=0, name="SkullEye")
        pts = [sk + Vector((side * 0.1, -0.3, 0.05)), sk + Vector((side * 0.25, -0.62, 0.02)), sk + Vector((side * 0.32, -0.85, 0.22)), sk + Vector((side * 0.22, -0.92, 0.42))]
        for i in range(3):
            reg(rod(pts[i], pts[i + 1], 0.06 - i * 0.015, 8, r2=0.045 - i * 0.015), P["bone"], matk="satin", parent=root, var=0,
                name="SkullTusk", colfn=lambda p, n: lerp(P["bone_old"], P["bone"], 0.7))
    for i in range(5):
        a = random.uniform(0, math.tau)
        p0 = Vector((-0.95 + 0.2 * math.cos(a), -0.55 + 0.2 * math.sin(a), 0.24))
        reg(rod(p0, p0 + Vector((math.cos(a + 1.5) * 0.35, math.sin(a + 1.5) * 0.35, 0.05)), 0.035, 6), P["bone"], matk="satin",
            parent=root, var=0.05, name="Bone")
    boulder(root, (1.1, -0.45, 0.25), 0.2)
    # the warrior: bigger, grey wolf pelt, blue war paint, red hair
    yaw = empty("Yaw", (0, 0, 0.21), root)
    body = empty("Body", (0, 0.05, 0), yaw)
    body.scale = (1.5, 1.5, 1.5)
    cave_body(body, tunic=P["fur_grey"], spots=mul(P["fur_grey"], 0.55), hair=P["hair_red"], paint=P["paint_blue"], left_arm=None)
    # wolf pelt over the left shoulder, wolf head on top
    reg(ico(0.2, (0.24, 0.02, 0.98), scale=(1.1, 1.0, 0.6)), P["fur_grey"], parent=body, var=0.05, name="Pelt")
    reg(ico(0.11, (0.27, -0.12, 1.08), scale=(0.9, 1.4, 0.8)), P["fur_grey"], parent=body, var=0.05, name="WolfHead")
    for side in (-1, 1):
        reg(cyl(0.04, 0.1, (0.27 + side * 0.06, -0.05, 1.18), verts=4, r2=0.0), mul(P["fur_grey"], 0.8), parent=body, var=0, name="WolfEar")
    # big left fist on the hip
    reg(rod((0.34, 0, 0.9), (0.46, -0.05, 0.62), 0.09, 10), P["skin"], parent=body, var=0.03, name="UpperArm_L")
    reg(cyl(0.11, 0.27, (0.44, -0.08, 0.5), verts=10, r2=0.09, rot=(math.radians(20), math.radians(-25), 0)), P["skin"], parent=body, var=0.03, name="Forearm_L")
    reg(ico(0.13, (0.38, -0.16, 0.38)), P["skin"], parent=body, var=0.03, name="Fist_L")
    reg(torus(0.1, 0.035, (0.42, 0.0, 0.7), rot=(0, math.radians(-20), 0), maj=10, mi=4), P["bone"], matk="satin", parent=body, name="BoneCuff")
    # club arm: raised back over the shoulder at rest, smashes forward (+x)
    arm = empty("Arm", (-0.36, 0, 0.92), body, rot=(math.radians(-40), math.radians(-22), 0))
    fz = raised_arm(arm, band=P["bone"], thick=1.15)
    club = Vector((0, -0.02, fz))
    reg(cyl(0.05, 0.3, club + Vector((0, 0, 0.05)), verts=8), P["leather"], parent=arm, var=0.04, name="Grip")
    c = rod(club + Vector((0, 0, 0.12)), club + Vector((0, 0, 0.8)), 0.075, 9, r2=0.18)
    jitter(c, 0.012)
    reg(c, P["wood"], parent=arm, bevel=0.02, var=0.06, name="Club",
        colfn=lambda p, n: lerp(P["wood_dark"], P["wood"], 0.5 + 1.2 * noise.noise(p * 6)))
    reg(cyl(0.155, 0.03, club + Vector((0, 0, 0.79)), verts=9), P["wood_cut"], parent=arm, var=0, name="ClubEnd")
    for k in range(7):
        a = k * 2.4
        zz = 0.42 + (k % 4) * 0.11
        rr = 0.075 + (0.18 - 0.075) * (zz - 0.12) / 0.68
        d = Vector((math.cos(a), math.sin(a), 0.25)).normalized()
        sp = cyl(0.045, 0.2, club + Vector((math.cos(a) * rr, math.sin(a) * rr, zz)) + d * 0.08, verts=5, r2=0.0)
        point_at(sp, d)
        reg(sp, P["bone"] if k % 2 else P["stone_light"], matk="satin", parent=arm, var=0.05, name="Spike")
    for zz in (0.22, 0.3):
        reg(torus(0.085, 0.022, club + Vector((0, 0, zz)), maj=10, mi=3), P["rope"], parent=arm, var=0.04, name="ClubWrap")
    return root, {"ClubWarrior": "Tower_Static", "Body": "Warrior_Body", "Arm": "Club_Mesh", "Yaw": "Yaw_Mesh"}


# ================================================================= BOULDER CATAPULT
def boulder_catapult():
    root = empty("BoulderCatapult")
    sty.grass_base(root, tufts=8, cobbles=16)
    # boulder stockpile at the back, held by stakes
    for x, y, r in ((-0.85, 0.75, 0.26), (-0.5, 0.95, 0.22), (-0.72, 1.05, 0.18), (-0.62, 0.8, 0.2)):
        boulder(root, (x, y, 0.3 + (0.2 if r < 0.2 else 0)), r, scale=(1.05, 1.0, 0.9), col=P["stone"])
    for x, y in ((-1.1, 0.5), (-0.3, 1.18)):
        reg(cyl(0.06, 0.6, (x, y, 0.45), verts=6), P["wood_dark"], parent=root, bevel=0.01, var=0.1, name="PileStake")
    yaw = empty("Yaw", (0, 0, 0.25), root)
    yaw.scale = (1.3, 1.3, 1.3)
    # sled frame on the ground + A-frames
    for x in (-0.42, 0.42):
        reg(cyl(0.085, 1.5, (x, 0.05, 0.02), verts=8, rot=(math.radians(90), 0, 0)), P["wood_dark"], parent=yaw, bevel=0.02, var=0.1, name="Runner")
        for y in (-0.35, 0.45):
            reg(rod((x * 1.05, y, 0.0), (x * 0.95, 0.05, 0.88), 0.075, 7), P["wood"], parent=yaw, bevel=0.02, var=0.1, name="Leg")
        reg(torus(0.1, 0.028, (x * 0.95, 0.05, 0.8), rot=(0, math.radians(90), 0), maj=8, mi=3), P["rope"], parent=yaw, var=0.05, name="Lash")
    for y in (-0.6, 0.65):
        reg(cyl(0.07, 1.0, (0, y, 0.05), verts=7, rot=(0, math.radians(90), 0)), P["wood_dark"], parent=yaw, bevel=0.02, var=0.1, name="Cross")
    reg(cyl(0.06, 1.05, (0, 0.05, 0.88), verts=8, rot=(0, math.radians(90), 0)), P["wood_dark"], parent=yaw, bevel=0.015, var=0.06, name="Axle")
    # stop bar the arm slams into
    reg(cyl(0.065, 0.95, (0, -0.42, 0.95), verts=7, rot=(0, math.radians(90), 0)), P["wood"], parent=yaw, bevel=0.02, var=0.06, name="StopBar")
    for x in (-0.42, 0.42):
        reg(rod((x, -0.35, 0.0), (x, -0.42, 0.95), 0.06, 6), P["wood"], parent=yaw, bevel=0.015, var=0.1, name="StopPost")
    # throwing arm: long end (bucket) low at the back, counterweight up front
    arm = empty("Arm", (0, 0.05, 0.88), yaw)
    ang = math.radians(-32)
    longd = Vector((0, math.cos(ang), math.sin(ang)))
    tip = longd * 1.35
    back = -longd * 0.5
    reg(rod(back, tip, 0.075, 8, r2=0.06), P["wood"], parent=arm, bevel=0.02, var=0.06, name="Beam")
    for k in (0.3, 0.75):
        reg(torus(0.085, 0.025, longd * k, maj=8, mi=3), P["rope"], parent=arm, var=0.05, name="BeamWrap").rotation_euler = \
            Vector((0, 0, 1)).rotation_difference(longd).to_euler()
    # hide bucket with the boulder
    cup = ico(0.26, tip + Vector((0, 0.05, 0.08)), scale=(1.0, 1.0, 0.55))
    for v in cup.data.vertices:
        if v.co.z > 0.02:
            v.co.z = 0.02 + (v.co.z - 0.02) * 0.2
    reg(cup, P["hide"], parent=arm, var=0.04, name="Bucket",
        colfn=lambda p, n: lerp(mul(P["hide"], 0.7), P["hide"], 0.5 + noise.noise(p * 8)))
    bd = ico(0.24, tip + Vector((0, 0.05, 0.27)), sub=2, scale=(1.05, 1.0, 0.95))
    jitter(bd, 0.025)
    reg(bd, P["stone"], parent=arm, smooth=False, var=0.06, name="Boulder",
        colfn=lambda p, n: lerp(P["stone_dark"], P["stone_light"], 0.5 + 0.8 * noise.noise(p * 5)))
    # counterweight: rope net of stones on the short end
    cw = back + Vector((0, 0, -0.3))
    reg(rod(back, cw, 0.02, 4), P["rope"], parent=arm, var=0, name="CWRope")
    for i in range(5):
        a = i * math.tau / 5
        boulder(arm, cw + Vector((0.12 * math.cos(a), 0.12 * math.sin(a), -0.05 + 0.08 * (i % 2))), 0.11, scale=(1, 1, 0.9), col=P["stone_dark"], name="CWStone")
    reg(ico(0.2, cw + Vector((0, 0, -0.02)), sub=1, scale=(1, 1, 0.8)), P["rope"], parent=arm, smooth=False, var=0, name="Net")
    # operator, small, pulling the trigger rope
    op = empty("Operator", (0.78, 0.25, 0.0), yaw, rot=(0, 0, math.radians(-75)))
    op.scale = (0.72, 0.72, 0.72)
    cave_body(op, tunic=P["fur"], left_arm="hang")
    pull = empty("PullArm", (-0.33, 0, 0.92), op, rot=(math.radians(-60), 0, 0))
    raised_arm(pull)
    return root, {"BoulderCatapult": "Tower_Static", "Yaw": "Frame_Mesh", "Arm": "Arm_Mesh", "Operator": "Operator_Mesh", "PullArm": "Operator_Arm"}


# ================================================================= TAR PIT SHAMAN
def tar_shaman():
    root = empty("TarShaman")
    sty.grass_base(root, tufts=7, cobbles=16)
    # bubbling tar pit (front-right)
    tx, ty = 0.42, -0.38
    reg(cyl(0.78, 0.06, (tx, ty, 0.2), verts=18), P["dirt_dark"], parent=root, bevel=0.02, var=0, name="PitRim",
        colfn=lambda p, n: lerp(P["dirt_dark"], P["dirt"], 0.3 + 0.6 * noise.noise(p * 4)))
    tar = cyl(0.66, 0.04, (tx, ty, 0.235), verts=18)
    reg(tar, P["tar"], matk="gloss", parent=root, var=0, name="Tar", noao=True)
    for i in range(6):
        a = random.uniform(0, math.tau)
        rr = random.uniform(0.1, 0.5)
        reg(ico(random.uniform(0.04, 0.09), (tx + rr * math.cos(a), ty + rr * math.sin(a), 0.255), scale=(1, 1, 0.7)),
            P["tar"], matk="gloss", parent=root, var=0, name="Bubble", noao=True)
    for i in range(9):
        a = i * math.tau / 9 + 0.2
        boulder(root, (tx + 0.8 * math.cos(a), ty + 0.8 * math.sin(a), 0.24), 0.09, col=P["stone_dark"], name="PitStone")
    # spirit post (back-right): horned skull, bone charms on a crossbar, ochre-spiral stone at its foot
    sp_ = empty("SpiritPost", (0.78, 0.72, 0.2), root)
    reg(cyl(0.075, 1.9, (0, 0, 0.95), verts=7), P["wood_dark"], parent=sp_, bevel=0.015, var=0.06, name="Post")
    reg(cyl(0.04, 0.8, (0, 0, 1.55), verts=6, rot=(0, math.radians(90), 0)), P["wood"], parent=sp_, bevel=0.01, name="PostBar")
    for k, x in enumerate((-0.32, -0.16, 0.16, 0.32)):
        reg(rod((x, 0, 1.55), (x, 0, 1.3 - 0.06 * (k % 2)), 0.01, 4), P["rope"], parent=sp_, var=0, name="CharmCord")
        reg(rod((x - 0.05, 0, 1.24 - 0.06 * (k % 2)), (x + 0.05, 0, 1.3 - 0.06 * (k % 2)), 0.025, 5), P["bone"], matk="satin", parent=sp_, name="Charm")
    horned_skull(sp_, (0, 0, 2.0), s=1.15)
    slab = box((0.5, 0.18, 0.62), (-0.35, -0.1, 0.31), rot=(0.05, 0, 0.3))
    jitter(slab, 0.02)
    reg(slab, P["stone"], parent=sp_, bevel=0.04, var=0.05, name="SpiralStone",
        colfn=lambda p, n: lerp(mul(P["stone_dark"], 1.1), P["stone"], 0.5 + 0.8 * noise.noise(p * 4)))
    for k in range(3):
        reg(torus(0.13 - k * 0.04, 0.018, (-0.39 + 0.28 * math.cos(0.3) * 0, -0.2, 0.36), rot=(math.radians(90), 0, 0.3), maj=12, mi=3),
            P["ochre"], parent=sp_, var=0, name="Spiral").location = Vector((-0.35 - 0.05 * math.sin(0.3) + 0.0, -0.1 - 0.1, 0.33 + 0.02 * k))
    # spirit fire bowl (front-left)
    reg(cyl(0.18, 0.14, (-0.95, -0.45, 0.27), verts=10, r2=0.24), P["stone_dark"], parent=root, bevel=0.02, var=0.06, name="Bowl")
    sp = empty("FlickerSpirit", (-0.95, -0.45, 0.35), root)
    for r, h in ((0.13, 0.42), (0.07, 0.3)):
        reg(cyl(r, h, (0, 0, h / 2), verts=7, r2=0.0), P["spirit"], matk="glow_green", parent=sp, var=0, noao=True, noocc=True, no_outline=True, name="SpiritFlame",
            colfn=lambda p, n, h=h: lerp((0.35, 0.95, 0.4), (0.1, 0.55, 0.2), (p.z - 0.35) / h))
    # the shaman: hunched, purple robe, bone mask headdress, staff with a green spirit orb
    yaw = empty("Yaw", (-0.38, 0.18, 0.25), root)
    body = empty("Body", (0, 0, 0), yaw)
    body.scale = (1.35, 1.35, 1.35)
    robe = cyl(0.36, 0.95, (0, 0, 0.47), verts=14, r2=0.2)
    for v in robe.data.vertices:
        if v.co.z < 0:
            k = round((math.atan2(v.co.y, v.co.x) % math.tau) / (math.tau / 14))
            if k % 2:
                v.co.z -= 0.06
    jitter(robe, 0.01)
    reg(robe, (0.33, 0.18, 0.48), parent=body, var=0, name="Robe",
        colfn=lambda p, n: lerp((0.22, 0.11, 0.33), (0.45, 0.25, 0.62), (p.z - 0.25) / 1.1))
    reg(torus(0.3, 0.05, (0, 0, 0.62), maj=16, mi=4), P["leather"], parent=body, var=0.04, name="Sash")
    for k in range(5):  # bone necklace
        reg(ico(0.035, (math.cos(k * 0.6 - 1.2) * 0.2, -0.17 + math.sin(k * 0.6 - 1.2) * 0.03, 0.88), sub=1), P["bone"], matk="satin", parent=body, name="Bead")
    reg(ico(0.22, (0, 0.02, 1.05), sub=3, scale=(1, 0.95, 1.05)), P["skin_tan"], parent=body, var=0.03, name="Head")
    # bone mask with glowing eyes
    reg(ico(0.17, (0, -0.13, 1.06), scale=(1.0, 0.5, 1.15)), P["bone"], matk="satin", parent=body, var=0.02, name="Mask")
    for side in (-1, 1):
        reg(ico(0.04, (side * 0.065, -0.21, 1.1), scale=(1, 0.5, 1.2)), (0.4, 1.0, 0.5), matk="glow_green", parent=body, var=0, noao=True, name="MaskEye")
        reg(box((0.03, 0.02, 0.12), (side * 0.1, -0.215, 0.97)), P["ochre"], parent=body, var=0, name="MaskStripe")
    # headdress: wolf-fur hood and antlers
    hood = ico(0.24, (0, 0.13, 1.13), scale=(1.05, 0.9, 1.0))
    jitter(hood, 0.02)
    reg(hood, P["fur_grey"], parent=body, var=0.04, name="Hood",
        colfn=lambda p, n: lerp(mul(P["fur_grey"], 0.7), P["fur_grey"], 0.5 + noise.noise(p * 8)))
    for side in (-1, 1):
        a0 = Vector((side * 0.14, 0.05, 1.3))
        a1 = Vector((side * 0.34, 0.08, 1.62))
        reg(rod(a0, a1, 0.032, 6, r2=0.022), P["bone"], matk="satin", parent=body, name="Antler")
        for t, dz in ((0.45, 0.2), (0.8, 0.16)):
            b0 = a0.lerp(a1, t)
            reg(rod(b0, b0 + Vector((side * 0.12, -0.04, dz)), 0.022, 5, r2=0.01), P["bone"], matk="satin", parent=body, name="AntlerTine")
    # left hand reaching toward the pit
    reg(rod((0.25, -0.05, 0.85), (0.42, -0.25, 0.7), 0.06, 8), P["skin_tan"], parent=body, var=0.03, name="Arm_L")
    reg(ico(0.08, (0.45, -0.28, 0.68)), P["skin_tan"], parent=body, var=0.03, name="Hand_L")
    # staff arm (pivot "Arm"), orb at the top (pivot "Orb")
    arm = empty("Arm", (-0.3, -0.05, 0.85), body)
    reg(rod((0, 0, 0), (0.02, -0.06, -0.2), 0.065, 8), P["skin_tan"], parent=arm, var=0.03, name="Arm_R")
    reg(ico(0.075, (0.02, -0.08, -0.22)), P["skin_tan"], parent=arm, var=0.03, name="Hand_R")
    reg(rod((0.02, -0.1, -0.9), (-0.08, -0.06, 1.0), 0.035, 6), P["wood_dark"], parent=arm, bevel=0.01, var=0.05, name="Staff")
    for zz in (-0.15, -0.3):
        reg(torus(0.045, 0.015, (0.0, -0.09, zz), maj=8, mi=3), P["rope"], parent=arm, var=0, name="StaffWrap")
    reg(ico(0.1, (-0.09, -0.05, 1.02), scale=(1, 1.1, 0.85)), P["bone"], matk="satin", parent=arm, name="StaffSkull")
    orb = empty("Orb", (-0.1, -0.05, 1.18), arm)
    reg(ico(0.11, (0, 0, 0), sub=2), P["spirit"], matk="glow_green", parent=orb, var=0, noao=True, name="Orb_Glow",
        colfn=lambda p, n: (0.55, 1.0, 0.6))
    return root, {"TarShaman": "Tower_Static", "SpiritPost": "Post_Mesh", "Body": "Shaman_Body", "Arm": "Staff_Mesh",
                  "Orb": "Orb_Mesh", "FlickerSpirit": "Spirit_Mesh"}


# ================================================================= HEROS
def hero_base(root, team):
    reg(cyl(0.82, 0.24, (0, 0, 0.1), verts=16, r2=0.76), P["stone"], parent=root, bevel=0.03, var=0, name="HeroStone",
        colfn=lambda p, n: lerp(P["stone_dark"], P["stone"], 0.4 + 0.8 * noise.noise(p * 3) + (p.z + 0.02) * 1.5))
    reg(torus(0.76, 0.055, (0, 0, 0.225), maj=28, mi=4), (1.0, 0.82, 0.3), matk="glow_orange", parent=root, var=0, name="HeroRing", noao=True)
    reg(cyl(0.68, 0.04, (0, 0, 0.225), verts=16), team, parent=root, var=0, name="HeroTeam",
        colfn=lambda p, n, team=team: lerp(mul(team, 0.75), team, 0.5 + noise.noise(p * 4)))


def ugo():
    root = empty("HeroUgo")
    hero_base(root, (0.75, 0.4, 0.12))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body = empty("Body", (0, 0, 0), yaw)
    body.scale = (1.42, 1.42, 1.42)
    cave_body(body, tunic=(0.85, 0.55, 0.16), spots=P["fur_dark"], paint=P["ochre"])
    with sty.soft_ao():
        # sabertooth pelt hood: head of the cat on his head, paws over the shoulders, fangs over the brow
        hood = ico(0.29, (0, 0.06, 1.24), scale=(1.08, 1.05, 0.78))
        jitter(hood, 0.015)
        reg(hood, (0.9, 0.42, 0.08), parent=body, var=0, name="SaberHood",
            colfn=lambda p, n: (0.12, 0.06, 0.03) if math.sin(p.x * 34 + p.z * 6) > 0.72 else lerp((0.9, 0.42, 0.08), (1.0, 0.66, 0.25), 0.5 + 0.8 * noise.noise(p * 9)))
        for side in (-1, 1):
            reg(ico(0.035, (side * 0.09, -0.24, 1.33), scale=(1.2, 0.5, 0.9)), (1.0, 0.75, 0.1), matk="gloss", parent=body, var=0, name="SaberEye")
        for side in (-1, 1):
            reg(cyl(0.06, 0.13, (side * 0.17, 0.0, 1.45), verts=5, r2=0.0, rot=(0, side * 0.3, 0)), (0.85, 0.55, 0.16), parent=body, var=0, name="SaberEar")
            reg(cyl(0.042, 0.24, (side * 0.2, -0.2, 1.2), verts=6, r2=0.0, rot=(math.radians(180) + 0.1, side * 0.12, 0)), P["bone"], matk="satin",
                parent=body, var=0, name="SaberFang")
        cape = box((0.78, 0.09, 0.85), (0, 0.27, 0.72), rot=(0.12, 0, 0))
        for v in cape.data.vertices:
            v.co.y += 0.06 * math.sin(v.co.x * 9) if v.co.z < 0 else 0
        reg(cape, (0.85, 0.55, 0.16), parent=body, bevel=0.04, var=0, name="Cape",
            colfn=lambda p, n: lerp((0.85, 0.55, 0.16), (0.98, 0.78, 0.4), 0.5 + 1.1 * noise.noise(p * 7)))
        reg(torus(0.24, 0.035, (0, -0.01, 1.2), maj=14, mi=4), P["ochre"], parent=body, var=0, name="Headband")
        for k in range(3):
            reg(box((0.05, 0.02, 0.26), (0.18 + k * 0.05, 0.12, 1.4 + k * 0.03), rot=(0.2, 0.35 + 0.15 * k, 0)), (0.95, 0.88, 0.7), parent=body, bevel=0.01, var=0.04, name="Feather")
        reg(ico(0.055, (0, -0.33, 0.88), sub=1), P["bone"], matk="satin", parent=body, name="Amulet")
    arm = empty("Arm", (-0.33, 0, 0.92), body, rot=(math.radians(-15), math.radians(-35), 0))
    z = raised_arm(arm, band=P["ochre"], thick=1.1)
    sling = empty("SpinSling", (0, 0, z + 0.04), arm)
    for dy in (-0.028, 0.028):
        reg(rod((0, 0, 0), (0.45, dy, -0.02), 0.018, 4), P["rope"], parent=sling, var=0, name="SlingCord")
    reg(ico(0.09, (0.48, 0, -0.03), scale=(1.0, 0.85, 0.55)), P["leather"], parent=sling, name="SlingPouch")
    reg(ico(0.095, (0.48, 0, 0.03), sub=1, scale=(1, 1, 0.85)), P["stone_light"], parent=sling, smooth=False, var=0, name="SlingRock")
    return root, {"HeroUgo": "Hero_Base", "Body": "Ugo_Body", "Arm": "Ugo_Arm", "SpinSling": "Sling_Mesh"}


def mara():
    root = empty("HeroMara")
    hero_base(root, (0.4, 0.25, 0.55))
    yaw = empty("Yaw", (0, 0, 0.25), root)
    body = empty("Body", (0, 0, 0), yaw)
    body.scale = (1.32, 1.32, 1.32)
    with sty.soft_ao():
        skin = P["skin_tan"]
        hair = (0.06, 0.04, 0.03)
        for side in (-1, 1):
            reg(cyl(0.085, 0.34, (side * 0.11, 0, 0.21), verts=10, r2=0.075), skin, parent=body, var=0.03, name="Leg")
            reg(ico(0.11, (side * 0.11, -0.05, 0.05), scale=(1.0, 1.35, 0.58)), P["leather"], parent=body, var=0.03, name="Boot")
        dress = cyl(0.36, 0.62, (0, 0, 0.5), verts=16, r2=0.24)
        for v in dress.data.vertices:
            if v.co.z < 0:
                k = round((math.atan2(v.co.y, v.co.x) % math.tau) / (math.tau / 16))
                v.co.z -= 0.07 if k % 2 else 0
        reg(dress, P["fur_grey"], parent=body, var=0, name="Dress",
            colfn=lambda p, n: lerp(mul(P["fur_grey"], 0.7), P["fur_white"], 0.45 + 0.9 * noise.noise(p * 8)))
        reg(ico(0.25, (0, 0, 0.82), scale=(1.0, 0.82, 0.85)), P["fur_grey"], parent=body, var=0.03, name="Chest")
        reg(torus(0.31, 0.04, (0, 0, 0.55), maj=16, mi=4), (0.45, 0.25, 0.6), parent=body, var=0, name="Sash")
        for k in range(7):
            a = k * 0.42 - 1.26
            reg(ico(0.035, (math.sin(a) * 0.2, -0.2 + (1 - math.cos(a)) * 0.08, 0.97 - abs(a) * 0.03), sub=1),
                (0.85, 0.55, 0.2) if k % 2 else P["bone"], matk="satin", parent=body, name="Bead")
        sty.caveman_head(body, (0, -0.02, 1.15), hair=hair, beard=False, angry=False, skin=skin, scale=0.92)
        for side in (-1, 1):  # long braids
            for k in range(4):
                reg(ico(0.06 - k * 0.006, (side * 0.2, 0.04, 1.02 - k * 0.11), sub=1, scale=(1, 1, 1.2)), hair, parent=body, var=0.03, name="Braid")
            reg(ico(0.03, (side * 0.2, 0.04, 0.6), sub=1), (0.45, 0.25, 0.6), parent=body, var=0, name="BraidTie")
        reg(torus(0.24, 0.03, (0, 0.0, 1.27), maj=14, mi=4), P["leather"], parent=body, var=0, name="Circlet")
        reg(ico(0.05, (0, -0.22, 1.28), sub=1), (0.9, 0.55, 0.15), matk="glow_orange", parent=body, var=0, name="CircletStone", noao=True)
        for side in (-1, 1):
            a0 = Vector((side * 0.16, 0.0, 1.32))
            a1 = Vector((side * 0.3, 0.05, 1.6))
            reg(rod(a0, a1, 0.028, 5, r2=0.018), P["bone"], matk="satin", parent=body, name="Antler")
            b0 = a0.lerp(a1, 0.55)
            reg(rod(b0, b0 + Vector((side * 0.1, -0.03, 0.14)), 0.018, 5, r2=0.008), P["bone"], matk="satin", parent=body, name="AntlerTine")
        reg(rod((0.27, 0, 0.92), (0.38, -0.12, 0.62), 0.065, 8), skin, parent=body, var=0.03, name="Arm_L")
        reg(ico(0.08, (0.4, -0.15, 0.58)), skin, parent=body, var=0.03, name="Hand_L")
    # staff arm with the amber orb (Orb pulses in code)
    arm = empty("Arm", (-0.28, -0.02, 0.9), body, rot=(math.radians(-10), 0, 0))
    with sty.soft_ao():
        reg(rod((0, 0, 0), (0.0, -0.08, -0.22), 0.06, 8), P["skin_tan"], parent=arm, var=0.03, name="Arm_R")
        reg(ico(0.075, (0.0, -0.1, -0.24)), P["skin_tan"], parent=arm, var=0.03, name="Hand_R")
    reg(rod((0.0, -0.11, -0.95), (-0.02, -0.08, 0.95), 0.035, 6), P["wood_dark"], parent=arm, bevel=0.01, var=0.05, name="Staff")
    for k in range(3):
        a = k * math.tau / 3
        reg(rod((-0.02, -0.08, 0.92), (-0.02 + 0.09 * math.cos(a), -0.08 + 0.09 * math.sin(a), 1.12), 0.018, 4), P["wood_dark"], parent=arm, var=0, name="Claw")
    orb = empty("Orb", (-0.02, -0.08, 1.08), arm)
    reg(ico(0.1, (0, 0, 0), sub=2), (1.0, 0.62, 0.18), matk="glow_orange", parent=orb, var=0, noao=True, name="Orb_Glow")
    # stonecaller: three stones orbit her (SpinStones is spun in code)
    spin = empty("SpinStones", (0, 0.04, 1.62), body)
    for k in range(3):
        a = k * math.tau / 3
        boulder(spin, (0.36 * math.cos(a), 0.36 * math.sin(a), 0.05 * (k - 1)), 0.07, scale=(1.1, 1, 0.85), col=P["stone_light"], name="OrbitStone")
    return root, {"HeroMara": "Hero_Base", "Body": "Mara_Body", "Arm": "Mara_Arm", "Orb": "Orb_Mesh", "SpinStones": "Stones_Mesh"}


import bpy  # noqa: E402  (after sty import so sty.reset owns factory reset)

BUILD = [("towers", "rock_slinger", rock_slinger), ("towers", "club_warrior", club_warrior),
         ("towers", "boulder_catapult", boulder_catapult), ("towers", "tar_shaman", tar_shaman),
         ("heroes", "ugo", ugo), ("heroes", "mara", mara)]
SEEDS = {"rock_slinger": 11, "club_warrior": 21, "boulder_catapult": 31, "tar_shaman": 41, "ugo": 51, "mara": 61}
for cat, tid, fn in BUILD:
    if ONLY and tid not in ONLY.split(","):
        continue
    sty.reset(SEEDS[tid])
    root, names = fn()
    sty.finish(os.path.join(OUT, cat, f"{tid}.glb"), outline_w=OUTLINE * (0.95 if cat == "heroes" else 1.0), names=names)
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        cam = sty.studio()
        big = cat == "towers"
        sty.shoot(cam, os.path.join(PREVIEW, f"{tid}_hero.png"), res=(600, 600), ortho=5.5 if big else 3.6,
                  target=(0, -0.3, 1.2) if big else (0, -0.2, 1.1))
        sty.shoot(cam, os.path.join(PREVIEW, f"{tid}_game.png"), pos=(0.01, -3.0, 10.0), target=(0, -0.2, 0.5), ortho=5.0 if big else 3.4, res=(400, 400))
    print("BUILT", tid)
