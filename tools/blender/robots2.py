"""The Recursion, part 2: robots and bosses for the Iron..Datacenter eras.

Run:  python3 tools/blender/robots2.py [--out ASSETS_DIR] [--only id,id] [--preview DIR] [--no-export]

Exports assets/robots/<id>.glb for every entry of ROBOTS and BOSSES in tools/era_spec.py.
Same conventions as robots.py: Z up, front faces -Y, root Empty named after the robot, an Empty
"Body" holding everything that bobs, gait pivots LegA_* / LegB_* (swung in opposite phase about X).
Flyers keep Body at the origin and build their meshes high up (z ~0.85+), so the game's bob, which
overwrites Body.position.y, cannot drop them to the ground.
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import lp
from lp import mat, empty, cyl, ico, uvs, box, torus

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))


def _arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


OUT = _arg("--out", os.path.join(REPO, "assets"))
PREVIEW = _arg("--preview")
ONLY = _arg("--only")
EXPORT = "--no-export" not in sys.argv

lp.reset(7)

# faction palette (same names/values as robots.py)
SHELL = mat("Shell", (0.74, 0.77, 0.83), 0.42, 0.15)
STEEL = mat("Steel", (0.50, 0.54, 0.60), 0.35, 0.55)
DARK = mat("Joint", (0.10, 0.11, 0.14), 0.5, 0.4)
RED = mat("RedGlow", (0.9, 0.05, 0.03), 0.4, 0.0, emit=(1.0, 0.03, 0.015), strength=2.2)
HAZ = mat("Hazard", (0.95, 0.52, 0.10), 0.4, 0.3)
THRUST = mat("Thruster", (1.0, 0.4, 0.1), 0.4, 0.0, emit=(1.0, 0.3, 0.03), strength=2.0)
CYAN = mat("ShieldGlow", (0.3, 0.85, 1.0), 0.2, 0.0, emit=(0.15, 0.7, 1.0), strength=1.6)
# era accents
IRON = mat("Iron", (0.27, 0.26, 0.26), 0.55, 0.45)
RIVET = mat("Rivet", (0.66, 0.63, 0.58), 0.4, 0.45)
CLOAK = mat("Cloak", (0.22, 0.25, 0.32), 0.5, 0.2)
STEALTH = mat("Stealth", (0.07, 0.075, 0.09), 0.38, 0.35)
STEALTH2 = mat("StealthPanel", (0.18, 0.19, 0.23), 0.4, 0.35)
NANO = mat("Nano", (0.05, 0.05, 0.06), 0.3, 0.4)
NANO2 = mat("NanoEdge", (0.15, 0.15, 0.17), 0.35, 0.4)
GLASS = mat("BlackGlass", (0.035, 0.045, 0.07), 0.12, 0.45)
BLUE = mat("BlueLED", (0.2, 0.6, 1.0), 0.3, 0.0, emit=(0.1, 0.5, 1.0), strength=2.6)
MAG = mat("MagentaGlow", (1.0, 0.2, 0.85), 0.3, 0.0, emit=(1.0, 0.1, 0.8), strength=3.0)
FURN = mat("Furnace", (0.95, 0.2, 0.02), 0.4, 0.0, emit=(1.0, 0.13, 0.01), strength=1.7)
KNIGHT = mat("KnightBlack", (0.08, 0.08, 0.10), 0.32, 0.5)
KNIGHT2 = mat("KnightPlate", (0.19, 0.19, 0.23), 0.35, 0.5)
SOLAR = mat("Solar", (0.07, 0.14, 0.36), 0.25, 0.3)
EYECORE = mat("EyeCore", (1.0, 0.55, 0.4), 0.3, 0.0, emit=(1.0, 0.45, 0.25), strength=4.0)

PI = math.pi


# ------------------------------------------------------------------ helpers
def sym(pts):
    out = []
    for x, y, z in pts:
        out.append((x, y, z))
        if abs(x) > 1e-6:
            out.append((-x, y, z))
    return out


def hull(pts, material, parent=None, name="Hull"):
    """Faceted convex solid from points (parent-local)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    res = bmesh.ops.convex_hull(bm, input=bm.verts)
    junk = list({g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)})
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    bmesh.ops.dissolve_limit(bm, angle_limit=0.02, verts=bm.verts, edges=bm.edges)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return lp._link(o, material, parent)


def rod(p0, p1, r, material, parent, verts=6, r2=None, name=None):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    o = cyl(r, d.length, tuple((p0 + p1) / 2), material, parent, verts=verts, r2=r2, name=name)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return o


def rivets(parent, pts, axis="y", r=0.025):
    rot = {"y": (PI / 2, 0, 0), "x": (0, PI / 2, 0), "z": (0, 0, 0)}[axis]
    for p in pts:
        cyl(r, r * 1.2, p, RIVET, parent, verts=5, rot=rot)


def leg(name, hip, parent, thigh=(0.13, 0.15, 0.26), shin=0.07, foot=(0.15, 0.22, 0.07), length=0.5,
        tm=None, sm=None, fm=None, bv=0.02):
    p = empty(name, hip, parent)
    box(thigh, (0, 0, -thigh[2] / 2), tm or SHELL, p, bevel=bv)
    cyl(shin, length - thigh[2], (0, 0, -thigh[2] - (length - thigh[2]) / 2 + 0.02), sm or DARK, p, verts=6)
    box(foot, (0, -0.03, -length + foot[2] / 2), fm or STEEL, p, bevel=bv * 0.75)
    return p


def bez(ctrl, t):
    pts = [Vector(c) for c in ctrl]
    while len(pts) > 1:
        pts = [a.lerp(b, t) for a, b in zip(pts, pts[1:])]
    return pts[0]


def neck(parent, ctrl, r0, r1, n, m1=SHELL, m2=STEEL, verts=8):
    """Armoured serpent neck: telescoping frusta along a bezier curve."""
    pts = [bez(ctrl, i / n) for i in range(n + 1)]
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        d = (b - a)
        ra = r0 + (r1 - r0) * i / n
        rb = r0 + (r1 - r0) * (i + 1) / n
        rod(a, b + d * 0.25, ra, m1 if i % 2 == 0 else m2, parent, verts=verts, r2=rb * 0.88)
    return pts


def snake_head(parent, loc, s=1.0, pitch=0.15, yaw=0.0, name="Head"):
    h = empty(name, loc, parent)
    h.scale = (s, s, s)
    h.rotation_euler = (pitch, 0, yaw)
    hull(sym([(0.07, -0.5, 0.0), (0.16, -0.26, 0.07), (0.2, 0.02, 0.07), (0.15, 0.17, -0.0), (0.08, -0.48, -0.05),
              (0.2, 0.0, -0.05), (0, 0.08, 0.16), (0, -0.28, 0.12), (0.09, -0.08, 0.14)]), SHELL, h)
    hull(sym([(0.05, -0.42, -0.1), (0.15, 0.08, -0.08), (0.1, -0.06, -0.17), (0.0, 0.12, -0.13)]), STEEL, h)
    box((0.2, 0.3, 0.03), (0, -0.16, -0.075), RED, h)  # mouth glow
    box((0.22, 0.14, 0.04), (0, -0.1, 0.145), STEEL, h, rot=(0.12, 0, 0))
    box((0.2, 0.12, 0.04), (0, 0.06, 0.15), STEEL, h, rot=(-0.05, 0, 0))
    for sx in (-1, 1):
        ico(0.055, (sx * 0.155, -0.22, 0.085), RED, h, sub=1, scale=(1, 1.4, 0.75), name="Eye")
        cyl(0.022, 0.09, (sx * 0.055, -0.4, -0.1), SHELL, h, verts=4, r2=0.0, rot=(PI, 0, 0))  # fangs
        cyl(0.04, 0.2, (sx * 0.12, 0.16, 0.12), DARK, h, verts=4, r2=0.0, rot=(-1.0, 0, 0))  # back horns
    return h


def blade_ring(parent, name, center, R, rot, n, size, led):
    e = empty(name, center, parent)
    e.rotation_euler = rot
    for k in range(n):
        a = k * 2 * PI / n
        c, s_ = math.cos(a), math.sin(a)
        box(size, (c * R, s_ * R, 0), DARK, e, rot=(0, 0, a + PI / 2))
        box((size[0] * 0.7, 0.02, size[2] * 0.18), (c * (R + size[1] / 2 + 0.01), s_ * (R + size[1] / 2 + 0.01), 0),
            led, e, rot=(0, 0, a + PI / 2))
    return e


def root_body(name, z=0.0):
    root = empty(name)
    return root, empty("Body", (0, 0, z), root)


# ================================================================== REGULAR ROBOTS
def ironclad():
    root, body = root_body("Ironclad")
    box((0.56, 0.36, 0.16), (0, 0.04, 0.45), DARK, body, bevel=0.03)
    for nm, s in (("LegA_L", 1), ("LegB_R", -1)):
        p = leg(nm, (s * 0.22, 0.04, 0.47), body, thigh=(0.26, 0.28, 0.2), shin=0.12, foot=(0.32, 0.4, 0.11),
                length=0.47, tm=IRON, bv=0.03)
        box((0.24, 0.07, 0.18), (0, -0.15, -0.27), IRON, p, bevel=0.02)
        rivets(p, [(sx * 0.07, -0.19, -0.23) for sx in (-1, 1)])
    box((0.9, 0.62, 0.52), (0, 0.04, 0.83), SHELL, body, bevel=0.06)
    box((0.8, 0.08, 0.46), (0, -0.28, 0.83), IRON, body, bevel=0.025)
    rivets(body, [(x, -0.325, z) for x in (-0.33, -0.165, 0, 0.165, 0.33) for z in (0.64, 1.02)])
    box((0.04, 0.02, 0.3), (0, -0.325, 0.83), DARK, body)
    for s in (-1, 1):
        box((0.08, 0.5, 0.42), (s * 0.46, 0.04, 0.83), IRON, body, bevel=0.02)
        rivets(body, [(s * 0.505, y, z) for y in (-0.15, 0.2) for z in (0.68, 0.98)], axis="x")
        box((0.4, 0.56, 0.26), (s * 0.6, 0.04, 1.08), IRON, body, bevel=0.06, rot=(0, s * 0.18, 0))
        rivets(body, [(s * 0.6 + dx, -0.25, 1.06) for dx in (-0.1, 0.1)])
        cyl(0.1, 0.34, (s * 0.64, 0.0, 0.82), STEEL, body, verts=8)
        cyl(0.14, 0.12, (s * 0.65, -0.01, 0.7), IRON, body, verts=8)
        box((0.26, 0.28, 0.22), (s * 0.65, -0.03, 0.56), DARK, body, bevel=0.05)
    box((0.94, 0.66, 0.1), (0, 0.04, 0.6), IRON, body, bevel=0.02)
    box((0.34, 0.3, 0.18), (0, -0.06, 1.16), IRON, body, bevel=0.03)
    box((0.38, 0.08, 0.06), (0, -0.2, 1.24), IRON, body, bevel=0.01)
    box((0.2, 0.03, 0.035), (0, -0.215, 1.16), RED, body, name="Visor")
    cyl(0.035, 0.04, (0, -0.02, 1.27), RED, body, verts=8, name="TopLight")
    box((0.5, 0.16, 0.36), (0, 0.4, 0.86), STEEL, body, bevel=0.02)
    for k in range(3):
        box((0.42, 0.05, 0.03), (0, 0.15 + k * 0.1, 1.1), RED, body, name="Vent")
    return root


def hover_drone():
    root, body = root_body("HoverDrone")
    z = 0.85
    cyl(0.24, 0.07, (0, 0, z), SHELL, body, verts=12)
    cyl(0.2, 0.06, (0, 0, z + 0.06), STEEL, body, verts=12, r2=0.12)
    torus(0.245, 0.03, (0, 0, z), DARK, body, major=16, minor=4)
    uvs(0.1, (0, 0, z + 0.09), SHELL, body, seg=10, rings=5, scale=(1, 1, 0.6))
    cyl(0.035, 0.04, (0, 0, z + 0.15), RED, body, verts=8, name="TopLight")
    box((0.14, 0.03, 0.03), (0, -0.25, z), RED, body, name="Visor")
    cyl(0.1, 0.05, (0, 0, z - 0.05), DARK, body, verts=10, r2=0.08)
    uvs(0.075, (0, 0, z - 0.08), RED, body, seg=8, rings=6, name="Eye")
    for k in range(4):
        a = PI / 4 + k * PI / 2
        c = (math.cos(a) * 0.32, math.sin(a) * 0.32)
        box((0.24, 0.05, 0.035), (math.cos(a) * 0.2, math.sin(a) * 0.2, z), STEEL, body, rot=(0, 0, a))
        cyl(0.04, 0.08, (*c, z + 0.02), DARK, body, verts=6)
        torus(0.12, 0.018, (*c, z + 0.03), DARK, body, major=14, minor=4)
        for b in (0.4, 0.4 + PI / 2):
            box((0.21, 0.035, 0.01), (*c, z + 0.065), STEEL, body, rot=(0, 0, a + b))
    return root


def hydra_head():
    root, body = root_body("HydraHead")
    for nm, x, y in (("LegA_FL", 0.25, -0.2), ("LegB_FR", -0.25, -0.2), ("LegB_BL", 0.25, 0.48), ("LegA_BR", -0.25, 0.48)):
        p = leg(nm, (x, y, 0.5), body, thigh=(0.15, 0.17, 0.22), shin=0.06, foot=(0.16, 0.22, 0.07), length=0.5)
        ico(0.07, (0, 0, -0.22), DARK, p, sub=1)
    uvs(0.3, (0, 0.15, 0.62), SHELL, body, seg=12, rings=8, scale=(0.95, 1.4, 0.72))
    box((0.4, 0.8, 0.12), (0, 0.15, 0.42), DARK, body, bevel=0.03)
    for k, y in enumerate((-0.1, 0.15, 0.4)):
        box((0.36 - k * 0.05, 0.22, 0.06), (0, y, 0.84 - k * 0.03), STEEL, body, bevel=0.02, rot=(0.08, 0, 0))
        cyl(0.05, 0.14, (0, y + 0.06, 0.92 - k * 0.03), DARK, body, verts=4, r2=0.0, rot=(-0.5, 0, 0))
    ico(0.07, (0, -0.31, 0.58), RED, body, sub=1, name="Core")
    ctrl = [(0, -0.22, 0.7), (0, -0.45, 1.1), (0, 0.05, 1.45), (0, -0.55, 1.62)]
    neck(body, ctrl, 0.13, 0.08, 9)
    for t in (0.3, 0.5, 0.7, 0.88):
        p = bez(ctrl, t)
        cyl(0.04, 0.12, (p.x, p.y + 0.08, p.z + 0.06), DARK, body, verts=4, r2=0.0, rot=(-0.6, 0, 0))
    snake_head(body, (0, -0.68, 1.62), s=0.8, pitch=0.22)
    rod((0, 0.55, 0.62), (0, 0.95, 0.45), 0.1, SHELL, body, verts=6, r2=0.03)
    return root


def cloaker():
    root, body = root_body("Cloaker")
    box((0.22, 0.14, 0.1), (0, 0.05, 0.76), DARK, body, bevel=0.02)
    for nm, s in (("LegA_L", 1), ("LegB_R", -1)):
        p = leg(nm, (s * 0.085, 0.05, 0.76), body, thigh=(0.075, 0.09, 0.34), shin=0.03, foot=(0.07, 0.19, 0.04),
                length=0.76, tm=CLOAK, sm=DARK, fm=STEEL, bv=0.012)
        ico(0.04, (0, -0.01, -0.36), DARK, p, sub=1)
    rod((0, 0.05, 0.78), (0, -0.04, 1.06), 0.05, DARK, body)
    ico(0.13, (0, -0.06, 0.98), SHELL, body, sub=2, scale=(0.95, 0.7, 1.1))
    ico(0.035, (0, -0.15, 0.98), RED, body, sub=1, name="Core")
    # mantle + cape
    cyl(0.25, 0.26, (0, 0.0, 1.07), CLOAK, body, verts=8, r2=0.09, rot=(0.35, 0, 0))
    hull(sym([(0.2, 0.08, 1.12), (0.12, 0.14, 1.18), (0.32, 0.26, 0.5), (0.3, 0.2, 0.5), (0.0, 0.3, 0.46), (0.0, 0.24, 0.46)]),
         CLOAK, body, name="Cape")
    for k in (-1, 0, 1):
        cyl(0.07, 0.14, (k * 0.17, 0.27, 0.42), CLOAK, body, verts=4, r2=0.0, rot=(PI - 0.15, 0, 0))
    # pointed cowl hood with a dark face opening
    hull(sym([(0.17, -0.2, 1.12), (0.19, -0.02, 1.08), (0.17, 0.12, 1.16), (0.13, -0.25, 1.32), (0.0, -0.3, 1.4),
              (0.0, 0.08, 1.45), (0.0, 0.32, 1.5), (0.09, 0.14, 1.38), (0.12, -0.26, 1.16)]), CLOAK, body, name="Hood")
    uvs(0.11, (0, -0.24, 1.22), DARK, body, seg=8, rings=6, scale=(1, 0.45, 0.95))
    box((0.15, 0.03, 0.03), (0, -0.29, 1.22), CYAN, body, name="Visor")
    # thin arms with blades
    for s in (-1, 1):
        rod((s * 0.17, -0.04, 1.08), (s * 0.2, -0.16, 0.82), 0.025, DARK, body)
        ico(0.04, (s * 0.2, -0.16, 0.82), DARK, body, sub=1)
        rod((s * 0.2, -0.16, 0.82), (s * 0.2, -0.36, 0.66), 0.03, STEEL, body, verts=4, r2=0.0)
    return root


def bomber():
    root, body = root_body("Bomber")
    z = 0.95
    uvs(0.3, (0, 0, z), SHELL, body, seg=12, rings=8, scale=(0.95, 1.45, 0.78))
    uvs(0.11, (0, -0.38, z + 0.06), RED, body, seg=8, rings=6, scale=(1.3, 0.6, 0.7), name="Eye")
    box((1.3, 0.36, 0.07), (0, 0.02, z - 0.02), STEEL, body, bevel=0.03)
    for s in (-1, 1):
        box((0.12, 0.37, 0.08), (s * 0.62, 0.02, z - 0.02), HAZ, body)
        rod((s * 0.45, -0.25, z), (s * 0.45, 0.28, z), 0.11, DARK, body, verts=8, r2=0.07)
        rod((s * 0.45, -0.25, z), (s * 0.45, -0.37, z), 0.07, STEEL, body, verts=8, r2=0.01)
        prop = empty("Prop", (s * 0.45, -0.31, z), body)
        for k in range(3):
            a = k * 2 * PI / 3 + 0.3
            box((0.055, 0.012, 0.27), (math.sin(a) * 0.14, 0, math.cos(a) * 0.14), STEEL, prop, rot=(0, a, 0))
        cyl(0.045, 0.02, (s * 0.45, 0.29, z), THRUST, body, verts=8, rot=(PI / 2, 0, 0))
    # bomb bay
    box((0.36, 0.5, 0.12), (0, 0.04, z - 0.24), DARK, body, bevel=0.02)
    for k in range(4):
        box((0.38, 0.06, 0.02), (0, -0.15 + k * 0.125, z - 0.305), HAZ, body)
    for s in (-1, 1):
        uvs(0.07, (s * 0.09, 0.04, z - 0.37), DARK, body, seg=8, rings=6, scale=(1, 2.1, 1))
    cyl(0.045, 0.05, (0, -0.24, z - 0.3), RED, body, verts=8, name="Warning")
    cyl(0.06, 0.07, (0, 0.08, z + 0.24), RED, body, verts=8, name="Warning")
    cyl(0.08, 0.03, (0, 0.08, z + 0.2), DARK, body, verts=8)
    # tail
    box((0.04, 0.24, 0.24), (0, 0.42, z + 0.15), STEEL, body, rot=(-0.4, 0, 0))
    box((0.52, 0.16, 0.04), (0, 0.44, z + 0.05), STEEL, body)
    return root


def steam_tank():
    root, body = root_body("SteamTank")
    for s in (-1, 1):
        side = "L" if s > 0 else "R"
        box((0.26, 1.3, 0.32), (s * 0.43, 0, 0.2), DARK, body, bevel=0.1)
        for k in range(7):
            box((0.28, 0.06, 0.02), (s * 0.43, -0.54 + k * 0.18, 0.365), STEEL, body)
        box((0.32, 1.38, 0.04), (s * 0.43, 0, 0.43), IRON, body)
        for k, y in enumerate((-0.38, 0.0, 0.38)):
            grp = "A" if (k % 2 == 0) == (s > 0) else "B"
            p = empty(f"Leg{grp}_{side}{k}", (s * 0.575, y, 0.2), body)
            cyl(0.14, 0.05, (0, 0, 0), STEEL, p, verts=10, rot=(0, PI / 2, 0))
            box((0.02, 0.26, 0.045), (s * 0.03, 0, 0), DARK, p)
            box((0.02, 0.045, 0.26), (s * 0.03, 0, 0), DARK, p)
            cyl(0.045, 0.03, (s * 0.035, 0, 0), RED, p, verts=6, rot=(0, PI / 2, 0))
    box((0.74, 1.1, 0.3), (0, 0.05, 0.5), IRON, body, bevel=0.04)
    box((0.72, 0.06, 0.38), (0, -0.6, 0.46), IRON, body, bevel=0.02, rot=(-0.7, 0, 0))
    rivets(body, [(x, -0.67, 0.42) for x in (-0.27, -0.09, 0.09, 0.27)], axis="y")
    for s in (-1, 1):
        rivets(body, [(s * 0.375, y, z) for y in (-0.36, -0.12, 0.12, 0.36, 0.56) for z in (0.42, 0.58)], axis="x")
    box((0.6, 0.86, 0.06), (0, 0.1, 0.67), SHELL, body, bevel=0.02)
    cyl(0.22, 0.17, (0, -0.02, 0.78), SHELL, body, verts=8)
    cyl(0.19, 0.07, (0, -0.02, 0.9), STEEL, body, verts=8, r2=0.13)
    ico(0.06, (0, -0.22, 0.84), RED, body, sub=1, name="Eye")
    rod((0, -0.16, 0.74), (0, -0.66, 0.74), 0.045, STEEL, body)
    cyl(0.06, 0.08, (0, -0.66, 0.74), DARK, body, verts=6, rot=(PI / 2, 0, 0))
    cyl(0.08, 0.44, (0.2, 0.4, 0.88), IRON, body, verts=8)
    cyl(0.08, 0.1, (0.2, 0.4, 1.14), DARK, body, verts=8, r2=0.12)
    cyl(0.085, 0.02, (0.2, 0.4, 1.19), THRUST, body, verts=8, name="Ember")
    for k in range(3):
        box((0.4, 0.03, 0.04), (0, 0.61, 0.44 + k * 0.07), RED, body, name="Vent")
    return root


def stealth_jet():
    root, body = root_body("StealthJet")
    z = 0.9
    pts = sym([(0, -0.62, 0.0), (0.6, 0.32, 0.0), (0.24, 0.42, 0.0), (0, -0.28, 0.09), (0.14, 0.05, 0.08),
               (0, 0.28, 0.07), (0, -0.25, -0.05), (0.16, 0.12, -0.05)])
    hull([(x, y, zz + z) for x, y, zz in pts], STEALTH, body)
    hull([(x, y, zz + z + 0.012) for x, y, zz in sym([(0.1, -0.12, 0.085), (0.13, 0.2, 0.07), (0, -0.3, 0.09), (0, 0.3, 0.07)])],
         STEALTH2, body)
    rod((0, -0.48, z + 0.04), (0, -0.25, z + 0.098), 0.022, RED, body, verts=4, name="Cockpit")
    rod((0, -0.25, z + 0.098), (0, 0.0, z + 0.1), 0.022, RED, body, verts=4, name="Cockpit")
    for s in (-1, 1):
        box((0.02, 0.16, 0.15), (s * 0.13, 0.3, z + 0.12), STEALTH, body, rot=(0, s * 0.45, 0))
        cyl(0.045, 0.05, (s * 0.08, 0.4, z + 0.02), THRUST, body, verts=8, rot=(PI / 2, 0, 0))
        ico(0.02, (s * 0.57, 0.3, z), RED, body, sub=1)
    return root


def nano_swarm():
    root, body = root_body("NanoSwarm")
    c = Vector((0, 0, 0.5))
    ico(0.24, tuple(c), NANO, body, sub=1)
    ico(0.12, tuple(c + Vector((0, -0.16, 0))), RED, body, sub=1, name="Core")
    pa = empty("LegA_swarm", tuple(c), body)
    pb = empty("LegB_swarm", tuple(c), body)
    n = 58
    for i in range(n):
        yy = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(1 - yy * yy)
        th = i * 2.39996
        d = Vector((math.cos(th) * rr, yy, math.sin(th) * rr))
        d = Vector((d.x, d.y, d.z))
        red = i % 6 == 3
        sz = random.uniform(0.045, 0.06) if red else random.uniform(0.08, 0.115)
        p = d * (0.31 + (0.03 if red else random.uniform(-0.02, 0.03)))
        if red and p.y > 0.1:  # keep the lights on the front / sides
            red = False
            sz = 0.09
        o = box((sz, sz, sz), tuple(p), RED if red else (NANO2 if i % 5 == 0 else NANO), pa if d.x >= 0 else pb,
                rot=(random.uniform(0, PI), random.uniform(0, PI), random.uniform(0, PI)))
    for k in range(7):  # stragglers trickling down to the ground
        x, y = random.uniform(-0.2, 0.2), random.uniform(-0.15, 0.2)
        zz = random.uniform(0.05, 0.2)
        sz = random.uniform(0.06, 0.09)
        box((sz, sz, sz), (x, y, zz - c.z), NANO, pa if x >= 0 else pb,
            rot=(random.uniform(0, PI), random.uniform(0, PI), random.uniform(0, PI)))
    return root


def nano_mite():
    root, body = root_body("NanoMite")
    box((0.22, 0.26, 0.15), (0, 0, 0.2), NANO, body, bevel=0.02)
    box((0.15, 0.15, 0.06), (0, 0.03, 0.3), NANO2, body, bevel=0.01)
    box((0.09, 0.02, 0.05), (0, -0.135, 0.22), RED, body, name="Eye")
    box((0.05, 0.05, 0.03), (0, -0.06, 0.34), RED, body, name="Eye")
    for i, y in enumerate((-0.08, 0.0, 0.08)):
        for s in (-1, 1):
            grp = "A" if (i % 2 == 0) == (s > 0) else "B"
            p = empty(f"Leg{grp}_{i}{'L' if s > 0 else 'R'}", (s * 0.1, y, 0.2), body)
            spread = (i - 1) * 0.06
            rod((0, 0, 0), (s * 0.12, spread, 0.07), 0.018, NANO, p, verts=4)
            rod((s * 0.12, spread, 0.07), (s * 0.19, spread * 1.6, -0.2), 0.015, NANO2, p, verts=4)
    return root


def sentinel():
    root, body = root_body("Sentinel")
    for nm, s in (("LegA_L", 1), ("LegB_R", -1)):
        p = leg(nm, (s * 0.12, 0.02, 0.86), body, thigh=(0.12, 0.14, 0.42), shin=0.05, foot=(0.11, 0.24, 0.06),
                length=0.86, tm=GLASS, sm=DARK, fm=GLASS, bv=0.02)
        box((0.022, 0.012, 0.34), (0, -0.072, -0.21), BLUE, p)
        box((0.07, 0.07, 0.3), (0, -0.01, -0.62), GLASS, p, bevel=0.015)
        box((0.022, 0.012, 0.24), (0, -0.05, -0.62), BLUE, p)
    box((0.34, 0.2, 0.14), (0, 0.02, 0.88), GLASS, body, bevel=0.03)
    box((0.36, 0.22, 0.02), (0, 0.02, 0.94), BLUE, body)
    cyl(0.1, 0.2, (0, 0.02, 1.02), DARK, body, verts=8)
    t = cyl(0.15, 0.5, (0, 0.02, 1.32), GLASS, body, verts=6, r2=0.32)
    t.scale = (1, 0.6, 1)
    for s in (-1, 1):
        rod((s * 0.045, -0.072, 1.1), (s * 0.15, -0.135, 1.52), 0.012, BLUE, body, verts=4)
    box((0.42, 0.02, 0.02), (0, -0.155, 1.54), BLUE, body)
    ico(0.05, (0, -0.13, 1.33), RED, body, sub=1, name="Core")
    for s in (-1, 1):
        ico(0.09, (s * 0.33, 0.02, 1.54), GLASS, body, sub=1)
        cyl(0.03, 0.015, (s * 0.33, 0.02, 1.635), BLUE, body, verts=6)
        rod((s * 0.35, 0.02, 1.5), (s * 0.38, 0.0, 1.12), 0.045, GLASS, body)
        ico(0.045, (s * 0.38, 0.0, 1.12), DARK, body, sub=1)
        rod((s * 0.38, 0.0, 1.12), (s * 0.39, -0.08, 0.8), 0.04, GLASS, body, r2=0.03)
        rod((s * 0.385, -0.03, 1.08), (s * 0.39, -0.1, 0.84), 0.012, BLUE, body, verts=4)
        ico(0.045, (s * 0.39, -0.09, 0.77), GLASS, body, sub=1)
        box((0.02, 0.15, 0.5), (s * 0.17, 0.2, 1.66), GLASS, body, rot=(0.35, s * 0.45, 0))
        box((0.022, 0.03, 0.42), (s * 0.168, 0.165, 1.66), BLUE, body, rot=(0.35, s * 0.45, 0))
    cyl(0.045, 0.12, (0, 0.02, 1.62), DARK, body, verts=6)
    ico(0.12, (0, 0.0, 1.76), GLASS, body, sub=2, scale=(0.85, 0.95, 1.25))
    box((0.17, 0.03, 0.03), (0, -0.112, 1.77), BLUE, body, name="Visor")
    box((0.016, 0.2, 0.016), (0, 0.0, 1.905), BLUE, body)
    torus(0.2, 0.022, (0, 0.04, 2.03), BLUE, body, rot=(0.25, 0, 0), major=20, minor=4, name="Halo")
    return root


# ================================================================== BOSSES
def iron_colossus():
    root, body = root_body("IronColossus")
    box((1.1, 0.75, 0.36), (0, 0.08, 1.5), DARK, body, bevel=0.06)
    big = dict(thigh=(0.5, 0.56, 0.62), shin=0.22, foot=(0.66, 0.9, 0.24), length=1.5, tm=IRON, bv=0.05)
    for nm, s in (("LegA_L", 1), ("LegB_R", -1)):
        p = leg(nm, (s * 0.47, 0.08, 1.5), body, **big)
        box((0.46, 0.14, 0.4), (0, -0.25, -0.8), IRON, p, bevel=0.04)
        rivets(p, [(dx, -0.325, -0.8 + dz) for dx in (-0.14, 0.14) for dz in (-0.12, 0.12)], r=0.04)
        box((0.4, 0.4, 0.4), (0, 0.0, -1.1), IRON, p, bevel=0.05)
    box((2.0, 1.35, 1.3), (0, 0.1, 2.35), SHELL, body, bevel=0.15)
    box((1.85, 0.12, 1.2), (0, -0.58, 2.35), IRON, body, bevel=0.05)
    rivets(body, [(x, -0.65, z) for x in (-0.8, -0.6, 0.6, 0.8) for z in (1.9, 2.2, 2.5, 2.8)]
           + [(x, -0.65, z) for x in (-0.35, 0.0, 0.35) for z in (1.84, 2.86)], r=0.045)
    box((1.0, 0.1, 0.8), (0, -0.64, 2.33), DARK, body, bevel=0.03)
    box((0.86, 0.1, 0.66), (0, -0.66, 2.33), FURN, body, name="Furnace")
    ico(0.24, (0, -0.68, 2.33), RED, body, sub=2, scale=(1.3, 0.5, 1.0), name="Core")
    for x in (-0.33, -0.165, 0, 0.165, 0.33):
        box((0.06, 0.08, 0.76), (x, -0.73, 2.33), IRON, body)
    box((0.92, 0.08, 0.06), (0, -0.73, 2.33), IRON, body)
    for s in (-1, 1):
        box((0.1, 1.15, 1.1), (s * 1.0, 0.1, 2.35), IRON, body, bevel=0.03)
        rivets(body, [(s * 1.06, y, z) for y in (-0.3, 0.1, 0.5) for z in (1.95, 2.75)], axis="x", r=0.045)
        box((0.95, 1.15, 0.6), (s * 1.3, 0.1, 2.88), IRON, body, bevel=0.13, rot=(0, s * 0.18, 0))
        rivets(body, [(s * 1.3 + dx, -0.5, 2.85) for dx in (-0.25, 0.0, 0.25)], r=0.05)
        cyl(0.26, 0.8, (s * 1.42, 0.05, 2.3), STEEL, body, verts=8)
        box((0.54, 0.6, 0.72), (s * 1.46, 0.0, 1.72), IRON, body, bevel=0.06)
        box((0.84, 0.9, 0.78), (s * 1.5, -0.05, 1.05), IRON, body, bevel=0.1, name="Fist")
        for f in range(4):
            box((0.17, 0.12, 0.2), (s * 1.5 + (f - 1.5) * 0.19, -0.53, 0.98), DARK, body, bevel=0.03)
        rivets(body, [(s * 1.92, y, 1.05) for y in (-0.3, 0.2)], axis="x", r=0.05)
        cyl(0.17, 0.9, (s * 0.48, 0.78, 3.15), IRON, body, verts=8)
        cyl(0.17, 0.14, (s * 0.48, 0.78, 3.66), DARK, body, verts=8, r2=0.24)
        cyl(0.17, 0.03, (s * 0.48, 0.78, 3.74), FURN, body, verts=8, name="Ember")
    box((0.66, 0.6, 0.44), (0, -0.25, 3.15), IRON, body, bevel=0.07)
    box((0.74, 0.14, 0.12), (0, -0.55, 3.33), IRON, body, bevel=0.03)
    box((0.44, 0.05, 0.08), (0, -0.56, 3.15), RED, body, name="Visor")
    for k in range(4):
        box((1.2, 0.07, 0.04), (0, 0.3 + k * 0.15, 3.02), RED, body, name="Vent")
    return root


def hydra_swarm():
    root, body = root_body("HydraSwarm")
    legs = (("LegA_FL", 0.78, -0.35), ("LegB_FR", -0.78, -0.35), ("LegB_BL", 0.78, 1.25), ("LegA_BR", -0.78, 1.25))
    for nm, x, y in legs:
        p = leg(nm, (x, y, 1.35), body, thigh=(0.4, 0.46, 0.62), shin=0.17, foot=(0.52, 0.66, 0.18), length=1.35, bv=0.05)
        ico(0.2, (0, 0, -0.62), DARK, p, sub=1)
        box((0.44, 0.12, 0.3), (0, -0.25, -0.3), STEEL, p, bevel=0.03)
    uvs(1.0, (0, 0.45, 1.62), SHELL, body, seg=14, rings=8, scale=(0.95, 1.38, 0.6))
    box((1.2, 2.0, 0.3), (0, 0.45, 1.15), DARK, body, bevel=0.08)
    for k, y in enumerate((-0.3, 0.25, 0.8, 1.35)):
        box((1.0 - abs(k - 1.5) * 0.12, 0.42, 0.12), (0, y, 2.18 - abs(k - 1.5) * 0.04), STEEL, body, bevel=0.04)
        cyl(0.13, 0.4, (0, y + 0.12, 2.38), DARK, body, verts=4, r2=0.0, rot=(-0.5, 0, 0))
    box((0.9, 0.12, 0.55), (0, -0.82, 1.45), DARK, body, bevel=0.04)
    ico(0.18, (0, -0.88, 1.45), RED, body, sub=2, name="Core")
    specs = [([(0, -0.6, 2.0), (0, -0.9, 3.1), (0, -0.2, 3.9), (0, -1.15, 4.25)], (0, -1.3, 4.25), 1.5, 0.0),
             ([(0.55, -0.5, 1.85), (1.25, -0.75, 2.5), (1.55, -0.1, 3.3), (1.7, -0.95, 3.55)], (1.76, -1.08, 3.55), 1.4, 0.4),
             ([(-0.55, -0.5, 1.85), (-1.25, -0.75, 2.5), (-1.55, -0.1, 3.3), (-1.7, -0.95, 3.55)], (-1.76, -1.08, 3.55), 1.4, -0.4)]
    for ctrl, hp, s, yaw in specs:
        neck(body, ctrl, 0.3, 0.17, 10)
        for t in (0.3, 0.5, 0.7, 0.88):
            q = bez(ctrl, t)
            cyl(0.07, 0.22, (q.x, q.y + 0.12, q.z + 0.12), DARK, body, verts=4, r2=0.0, rot=(-0.6, 0, 0))
        snake_head(body, hp, s=s, pitch=0.25, yaw=yaw)
    rod((0, 1.75, 1.55), (0, 2.6, 1.05), 0.28, SHELL, body, verts=8, r2=0.12)
    rod((0, 2.5, 1.1), (0, 3.0, 0.75), 0.13, STEEL, body, verts=6, r2=0.02)
    return root


def black_knight():
    root, body = root_body("BlackKnight")
    box((0.95, 0.62, 0.36), (0, 0.05, 1.55), DARK, body, bevel=0.06)
    for nm, s in (("LegA_L", 1), ("LegB_R", -1)):
        p = leg(nm, (s * 0.4, 0.05, 1.55), body, thigh=(0.42, 0.48, 0.66), shin=0.19, foot=(0.46, 0.85, 0.2),
                length=1.55, tm=KNIGHT, sm=DARK, fm=KNIGHT, bv=0.05)
        box((0.38, 0.42, 0.62), (0, 0.0, -1.05), KNIGHT, p, bevel=0.06)
        ico(0.2, (0, -0.2, -0.7), STEEL, p, sub=1, scale=(1.0, 0.8, 1.0))
        cyl(0.12, 0.25, (0, -0.52, -1.48), KNIGHT, p, verts=4, r2=0.0, rot=(PI / 2, 0, PI / 4))
    for s in (-1, 1):
        box((0.42, 0.08, 0.55), (s * 0.24, -0.36, 1.4), KNIGHT2, body, bevel=0.03, rot=(0.15, 0, 0))
        box((0.08, 0.58, 0.55), (s * 0.55, 0.05, 1.4), KNIGHT2, body, bevel=0.03, rot=(0, s * 0.2, 0))
    box((1.6, 1.0, 1.15), (0, 0.05, 2.35), KNIGHT, body, bevel=0.18)
    hull(sym([(0.68, -0.45, 2.92), (0.52, -0.45, 1.82), (0, -0.66, 2.62), (0, -0.56, 1.82), (0.68, -0.3, 2.92),
              (0.52, -0.3, 1.82), (0, -0.62, 2.92)]), KNIGHT2, body)
    box((0.08, 0.06, 0.95), (0, -0.66, 2.32), STEEL, body, rot=(0.07, 0, 0))
    ico(0.13, (0, -0.66, 2.45), RED, body, sub=1, name="Core")
    cyl(0.42, 0.24, (0, -0.05, 2.98), KNIGHT2, body, verts=8)
    # shoulders
    for s in (-1, 1):
        uvs(0.52, (s * 0.95, 0.05, 2.85), KNIGHT, body, seg=10, rings=6, scale=(1, 1.1, 0.72), smooth=False)
        box((0.6, 0.9, 0.12), (s * 1.05, 0.05, 2.55), KNIGHT2, body, bevel=0.03, rot=(0, s * 0.35, 0))
        box((0.5, 0.8, 0.12), (s * 1.12, 0.05, 2.4), KNIGHT, body, bevel=0.03, rot=(0, s * 0.45, 0))
        cyl(0.2, 0.7, (s * 1.0, 0.05, 2.25), DARK, body, verts=8)
    # great helm
    cyl(0.4, 0.62, (0, -0.05, 3.3), KNIGHT, body, verts=8, rot=(0, 0, PI / 8))
    cyl(0.4, 0.12, (0, -0.05, 3.67), KNIGHT, body, verts=8, r2=0.28, rot=(0, 0, PI / 8))
    box((0.3, 0.05, 0.07), (0, -0.42, 3.4), RED, body, name="Visor")
    box((0.06, 0.05, 0.3), (0, -0.42, 3.24), RED, body, name="Visor")
    box((0.06, 0.66, 0.28), (0, -0.05, 3.85), STEEL, body, bevel=0.02)
    box((0.06, 0.04, 0.6), (0, -0.425, 3.33), STEEL, body)
    # shield arm (+X is the knight's left) and tower shield
    rod((1.02, 0.05, 1.95), (1.02, -0.5, 1.85), 0.18, KNIGHT2, body, verts=8)
    sh = empty("Shield", (1.12, -0.88, 1.75), body)
    box((0.52, 0.14, 2.2), (0, 0, 0), KNIGHT, sh, bevel=0.05)
    for s in (-1, 1):
        box((0.36, 0.12, 2.2), (s * 0.41, 0.07, 0), KNIGHT, sh, bevel=0.04, rot=(0, 0, s * -0.4))
        box((0.06, 0.1, 2.24), (s * 0.57, 0.15, 0), STEEL, sh, rot=(0, 0, s * -0.4))
    box((1.1, 0.1, 0.07), (0, 0.02, 1.08), STEEL, sh)
    box((1.1, 0.1, 0.07), (0, 0.02, -1.08), STEEL, sh)
    box((0.13, 0.05, 1.0), (0, -0.08, 0.15), RED, sh, name="Emblem")
    box((0.5, 0.05, 0.13), (0, -0.08, 0.38), RED, sh, name="Emblem")
    # lance arm (-X) and couched lance
    rod((-1.02, 0.05, 1.95), (-1.0, -0.35, 1.95), 0.18, KNIGHT2, body, verts=8)
    ico(0.2, (-1.0, -0.4, 1.95), DARK, body, sub=1)
    rod((-1.0, 0.7, 1.95), (-1.0, -0.6, 1.95), 0.09, DARK, body, verts=8)
    rod((-1.0, -0.8, 1.95), (-1.0, -0.45, 1.95), 0.12, STEEL, body, verts=10, r2=0.4)
    rod((-1.0, -0.8, 1.95), (-1.0, -3.0, 1.95), 0.15, KNIGHT2, body, verts=8, r2=0.02)
    rod((-1.0, -1.6, 1.95), (-1.0, -1.72, 1.95), 0.115, RED, body, verts=8, name="LanceRing")
    return root


def dreadnought():
    root, body = root_body("Dreadnought")
    for i, (nm, x, y) in enumerate((("LegA_FL", 0.72, -0.75), ("LegB_FR", -0.72, -0.75),
                                    ("LegB_BL", 0.72, 1.1), ("LegA_BR", -0.72, 1.1))):
        s = 1 if x > 0 else -1
        box((0.36, 0.6, 0.45), (s * 0.82, y, 1.75), DARK, body, bevel=0.05)
        p = leg(nm, (x, y, 1.75), body, thigh=(0.36, 0.42, 0.65), shin=0.15, foot=(0.5, 0.66, 0.2), length=1.75, bv=0.04)
        ico(0.2, (0, 0, -0.68), DARK, p, sub=1)
        box((0.3, 0.12, 0.35), (0, -0.2, -1.2), STEEL, p, bevel=0.03)
    deck = [(0, -2.15, 2.62), (0.72, -1.2, 2.56), (0.92, -0.6, 2.52), (0.92, 1.3, 2.52), (0.72, 1.85, 2.56)]
    mid = [(0, -1.95, 2.05), (0.66, -1.05, 1.8), (0.84, -0.55, 1.78), (0.84, 1.3, 1.78), (0.66, 1.8, 1.85)]
    keel = [(0, -1.6, 1.52), (0.4, -0.9, 1.45), (0.5, -0.4, 1.42), (0.5, 1.25, 1.45), (0.36, 1.75, 1.6)]
    hull(sym(deck + mid + keel), IRON, body, name="Hull")
    box((1.5, 2.9, 0.06), (0, 0.15, 2.55), SHELL, body)
    # red waterline
    hull(sym([(0.86, -0.55, 1.88), (0.86, 1.3, 1.88), (0.86, -0.55, 1.83), (0.86, 1.3, 1.83),
              (0.6, -1.15, 1.88), (0.6, -1.15, 1.83)]), RED, body, name="Waterline")
    for s in (-1, 1):
        for z, w in ((2.32, 0.885), (2.06, 0.865)):
            for y in (-0.45, 0.0, 0.45, 0.9):
                box((0.06, 0.18, 0.14), (s * (w + 0.01), y + (0.22 if z < 2.2 else 0), z), RED, body, name="Port")
                rod((s * w, y + (0.22 if z < 2.2 else 0), z), (s * (w + 0.3), y + (0.22 if z < 2.2 else 0), z),
                    0.055, DARK, body)
    # superstructure
    box((0.95, 0.85, 0.5), (0, 0.55, 2.82), SHELL, body, bevel=0.06)
    box((0.75, 0.5, 0.32), (0, 0.45, 3.22), STEEL, body, bevel=0.04)
    box((0.62, 0.03, 0.08), (0, 0.195, 3.24), RED, body, name="Visor")
    box((0.8, 0.03, 0.06), (0, 0.12, 2.9), RED, body, name="Visor")
    cyl(0.02, 0.6, (0.25, 0.6, 3.65), DARK, body, verts=4)
    ico(0.05, (0.25, 0.6, 3.97), RED, body, sub=1)
    for y, h in ((-0.35, 1.05), (1.3, 0.95)):
        cyl(0.21, h, (0, y, 2.55 + h / 2), IRON, body, verts=10, rot=(-0.12, 0, 0))
        top = Vector((0, y + math.sin(0.12) * h / 2, 2.55 + h))
        cyl(0.24, 0.12, tuple(top), DARK, body, verts=10, rot=(-0.12, 0, 0))
        cyl(0.22, 0.06, tuple(top + Vector((0, 0, -0.18))), RED, body, verts=10, rot=(-0.12, 0, 0), name="Band")
        cyl(0.18, 0.02, tuple(top + Vector((0, 0.007, 0.06))), THRUST, body, verts=10, rot=(-0.12, 0, 0))
    # bow turret
    cyl(0.32, 0.2, (0, -1.15, 2.68), SHELL, body, verts=8)
    cyl(0.25, 0.1, (0, -1.15, 2.82), STEEL, body, verts=8, r2=0.18)
    ico(0.08, (0, -1.44, 2.74), RED, body, sub=1, name="Eye")
    for s in (-1, 1):
        rod((s * 0.12, -1.3, 2.7), (s * 0.12, -1.95, 2.72), 0.06, STEEL, body)
    return root


def juggernaut():
    root, body = root_body("Juggernaut")
    for s in (-1, 1):
        side = "L" if s > 0 else "R"
        box((0.62, 3.4, 1.05), (s * 1.0, 0.1, 0.55), DARK, body, bevel=0.3)
        for k in range(10):
            box((0.64, 0.09, 0.04), (s * 1.0, -1.15 + k * 0.28, 1.08), STEEL, body)
        box((0.74, 3.5, 0.07), (s * 1.0, 0.1, 1.14), IRON, body, bevel=0.02)
        for k, y in enumerate((-1.05, 0.1, 1.25)):
            grp = "A" if (k % 2 == 0) == (s > 0) else "B"
            p = empty(f"Leg{grp}_{side}{k}", (s * 1.35, y, 0.55), body)
            cyl(0.42, 0.08, (0, 0, 0), STEEL, p, verts=12, rot=(0, PI / 2, 0))
            for a in (0, PI / 3, 2 * PI / 3):
                box((0.03, 0.74, 0.07), (s * 0.05, 0, 0), DARK, p, rot=(a, 0, 0))
            cyl(0.11, 0.05, (s * 0.06, 0, 0), RED, p, verts=8, rot=(0, PI / 2, 0))
    box((1.45, 3.3, 0.45), (0, 0.15, 1.0), DARK, body, bevel=0.05)
    # boiler
    cyl(0.72, 2.3, (0, -0.35, 1.85), IRON, body, verts=12, rot=(PI / 2, 0, 0))
    for y in (-1.15, -0.45, 0.25):
        cyl(0.76, 0.12, (0, y, 1.85), STEEL, body, verts=12, rot=(PI / 2, 0, 0))
    for y in (-0.8, 0.55):
        cyl(0.735, 0.08, (0, y, 1.85), FURN, body, verts=12, rot=(PI / 2, 0, 0), name="Glow")
    cyl(0.62, 0.06, (0, -1.52, 1.85), FURN, body, verts=12, rot=(PI / 2, 0, 0), name="Glow")
    torus(0.62, 0.06, (0, -1.54, 1.85), DARK, body, rot=(PI / 2, 0, 0), major=16, minor=4)
    ico(0.2, (0, -1.56, 1.85), RED, body, sub=2, scale=(1, 0.5, 1), name="Eye")
    cyl(0.16, 0.12, (0, -1.38, 2.72), DARK, body, verts=8, rot=(PI / 2, 0, 0))
    cyl(0.12, 0.04, (0, -1.45, 2.72), RED, body, verts=8, rot=(PI / 2, 0, 0), name="Lamp")
    # twin stacks
    for s in (-1, 1):
        cyl(0.17, 0.95, (s * 0.32, -0.95, 2.85), IRON, body, verts=10)
        cyl(0.17, 0.3, (s * 0.32, -0.95, 3.45), DARK, body, verts=10, r2=0.29)
        cyl(0.26, 0.02, (s * 0.32, -0.95, 3.6), THRUST, body, verts=10, name="Ember")
    # cab
    box((1.75, 1.15, 1.3), (0, 1.25, 2.1), SHELL, body, bevel=0.08)
    box((1.95, 1.35, 0.12), (0, 1.25, 2.82), STEEL, body, bevel=0.04)
    for s in (-1, 1):
        box((0.36, 0.03, 0.22), (s * 0.5, 0.665, 2.5), RED, body, name="Window")
        box((0.03, 0.6, 0.25), (s * 0.885, 1.25, 2.4), RED, body, name="Window")
        box((0.03, 0.5, 0.2), (s * 0.885, 1.25, 1.75), FURN, body, name="Firebox")
    box((0.9, 0.3, 0.7), (0, 1.95, 1.85), DARK, body, bevel=0.04)
    # cowcatcher + buffer beam
    box((1.7, 0.18, 0.28), (0, -1.6, 1.05), HAZ, body)
    hull(sym([(0.8, -1.68, 0.95), (0.8, -1.68, 0.15), (0.0, -2.4, 0.12), (0.0, -2.0, 0.92)]), STEEL, body, name="Cowcatcher")
    for k in range(5):
        x = -0.6 + k * 0.3
        rod((x, -1.72, 0.98), (x * 0.25, -2.3 + abs(x) * 0.3, 0.2), 0.035, DARK, body, verts=4)
    return root


def hunter_killer():
    root, body = root_body("HunterKiller")
    for nm, s in (("LegA_L", 1), ("LegB_R", -1)):
        p = empty(nm, (s * 0.62, 0.2, 2.3), body)
        knee = Vector((s * 0.18, -0.6, -0.95))
        ankle = Vector((s * 0.22, 0.38, -1.78))
        ico(0.26, (0, 0, 0), DARK, p, sub=1)
        rod((0, 0, 0), knee, 0.22, STEALTH, p, verts=6, r2=0.15)
        hull([tuple(Vector(v) + Vector((s * 0.0, 0, 0))) for v in
              [(s * 0.16, -0.05, 0.05), (s * 0.22, -0.55, -0.85), (s * 0.3, -0.2, -0.3), (s * 0.08, -0.62, -0.85),
               (s * 0.06, -0.1, 0.1), (s * 0.12, -0.35, -0.5)]], STEALTH2, p)
        ico(0.17, tuple(knee), DARK, p, sub=1)
        ico(0.07, tuple(knee + Vector((0, -0.15, 0.03))), RED, p, sub=1)
        rod(knee, ankle, 0.13, STEALTH2, p, verts=6, r2=0.1)
        ico(0.12, tuple(ankle), DARK, p, sub=1)
        for dx, ty in ((-0.16, -0.62), (0.0, -0.7), (0.16, -0.62), (0.0, 0.42)):
            toe = Vector((ankle.x + dx * 1.2, ankle.y + ty, -2.28))
            rod(ankle, toe, 0.09, STEALTH, p, verts=4, r2=0.04)
    pts = sym([(0, -1.45, 2.65), (0.38, -1.15, 2.88), (0.38, -1.15, 2.42), (0.86, -0.3, 3.0), (0.9, -0.2, 2.32),
               (0.75, 0.9, 2.95), (0.7, 1.0, 2.38), (0, 1.25, 2.7), (0, -0.45, 3.24), (0, 0.6, 3.2), (0, 0.2, 2.12)])
    hull(pts, STEALTH, body, name="Hull")
    hull(sym([(0.42, -0.3, 3.1), (0.36, 0.7, 3.06), (0, -0.62, 3.28), (0, 0.85, 3.22), (0.2, 0.2, 3.25)]), STEALTH2, body)
    hull(sym([(0.16, -1.36, 2.79), (0.16, -1.36, 2.6), (0.0, -1.5, 2.7), (0.08, -1.42, 2.57), (0.08, -1.42, 2.83)]),
         DARK, body)
    uvs(0.13, (0, -1.47, 2.7), RED, body, seg=10, rings=6, scale=(1.5, 0.75, 0.8), name="Eye")
    for s in (-1, 1):
        rod((s * 0.14, -1.18, 2.9), (s * 0.62, -0.42, 3.04), 0.025, RED, body, verts=4, name="Scan")
        rod((s * 0.7, -0.1, 2.75), (s * 1.0, -0.1, 2.8), 0.12, DARK, body)
        box((0.5, 1.0, 0.55), (s * 1.22, -0.1, 2.85), STEALTH2, body, bevel=0.05)
        hull([(s * 0.97, -0.62, 3.13), (s * 1.47, -0.62, 3.13), (s * 0.97, 0.4, 3.13), (s * 1.47, 0.4, 3.13),
              (s * 1.12, -0.5, 3.24), (s * 1.32, -0.5, 3.24), (s * 1.12, 0.3, 3.24), (s * 1.32, 0.3, 3.24)], STEALTH, body)
        for ix in range(3):
            for iz in range(2):
                pos = (s * 1.22 + (ix - 1) * 0.14, -0.62, 2.74 + iz * 0.2)
                cyl(0.055, 0.04, pos, DARK, body, verts=8, rot=(PI / 2, 0, 0))
                cyl(0.04, 0.12, (pos[0], -0.66, pos[2]), RED, body, verts=6, r2=0.0, rot=(PI / 2, 0, 0), name="Missile")
        box((0.03, 0.4, 0.3), (s * 0.3, 0.75, 3.3), STEALTH2, body, rot=(-0.4, s * 0.35, 0))
    cyl(0.02, 0.6, (0.2, 0.25, 3.5), DARK, body, verts=4)
    ico(0.04, (0.2, 0.25, 3.8), RED, body, sub=1)
    for k in range(3):
        box((0.7, 0.05, 0.03), (0, 0.55 + k * 0.15, 3.18), RED, body, name="Vent")
    return root


def orbital_uplink():
    root, body = root_body("OrbitalUplink")
    cyl(1.1, 0.3, (0, 0, 1.25), SHELL, body, verts=6)
    cyl(1.16, 0.08, (0, 0, 1.38), DARK, body, verts=6)
    cyl(0.5, 0.42, (0, 0, 0.9), DARK, body, verts=6, r2=1.0)
    cyl(0.3, 0.06, (0, 0, 0.67), THRUST, body, verts=10, name="Thruster")
    for k in range(6):
        a = k * PI / 3
        ico(0.07, (math.cos(a) * 1.13, math.sin(a) * 1.13, 1.45), RED, body, sub=1, name="RimLight")
    for k in range(3):
        a = PI / 2 + k * 2 * PI / 3
        x, y = math.cos(a) * 0.75, math.sin(a) * 0.75
        cyl(0.16, 0.3, (x, y, 0.95), STEEL, body, verts=8, r2=0.12)
        cyl(0.11, 0.04, (x, y, 0.79), THRUST, body, verts=8, name="Thruster")
    box((0.6, 0.04, 0.1), (0, -0.96, 1.25), RED, body, name="Visor")
    cyl(0.18, 0.7, (0, 0.15, 1.75), STEEL, body, verts=8)
    ico(0.25, (0, 0.15, 2.1), DARK, body, sub=1)
    dish = empty("Dish", (0, 0.12, 2.25), body)
    dish.rotation_euler = (0.65, 0, 0)
    cyl(0.22, 0.25, (0, 0, 0.0), DARK, dish, verts=8)
    cyl(0.3, 0.45, (0, 0, 0.3), SHELL, dish, verts=16, r2=1.15)
    cyl(1.08, 0.03, (0, 0, 0.53), STEEL, dish, verts=16)
    torus(0.7, 0.03, (0, 0, 0.55), DARK, dish, major=16, minor=4)
    torus(1.14, 0.05, (0, 0, 0.53), DARK, dish, major=16, minor=4)
    for k in range(3):
        a = PI / 2 + k * 2 * PI / 3
        rod((math.cos(a) * 1.05, math.sin(a) * 1.05, 0.55), (0, 0, 1.25), 0.03, DARK, dish, verts=4)
    ico(0.17, (0, 0, 1.3), MAG, dish, sub=2, name="Emitter")
    torus(0.24, 0.035, (0, 0, 1.3), MAG, dish, major=14, minor=4)
    cyl(0.1, 0.35, (0, 0, 1.58), MAG, dish, verts=6, r2=0.0)
    for s in (-1, 1):
        rod((s * 0.9, 0.1, 1.3), (s * 1.3, 0.1, 1.55), 0.06, STEEL, body)
        wing = empty("Wing", (s * 1.78, 0.1, 1.58), body)
        wing.rotation_euler = (0, s * 0.18, 0)
        box((0.95, 0.8, 0.05), (0, 0, 0), SOLAR, wing, bevel=0.01)
        for k in (-1, 0, 1):
            box((0.02, 0.82, 0.07), (k * 0.31, 0, 0), STEEL, wing)
        box((0.97, 0.02, 0.07), (0, 0, 0), STEEL, wing)
        box((0.97, 0.04, 0.07), (0, -0.4, 0), STEEL, wing)
        box((0.97, 0.04, 0.07), (0, 0.4, 0), STEEL, wing)
    return root


def the_core():
    root, body = root_body("TheCore")
    C = Vector((0, 0, 3.0))
    ico(1.15, tuple(C), GLASS, body, sub=2, name="Monolith")
    torus(1.16, 0.04, tuple(C), DARK, body, major=24, minor=4)
    cyl(0.62, 0.3, (0, -0.98, C.z), DARK, body, verts=16, rot=(PI / 2, 0, 0))
    uvs(0.5, (0, -1.1, C.z), RED, body, seg=16, rings=8, scale=(1, 0.42, 1), name="Eye")
    ico(0.16, (0, -1.27, C.z), EYECORE, body, sub=2, scale=(1, 0.5, 1), name="Pupil")
    torus(0.58, 0.05, (0, -1.13, C.z), STEEL, body, rot=(PI / 2, 0, 0), major=20, minor=4)
    blade_ring(body, "RingLow", (0, 0, 2.55), 1.5, (0.1, 0.0, 0.0), 20, (0.42, 0.1, 0.26), RED)
    blade_ring(body, "RingHigh", (0, 0, 3.78), 1.08, (-0.12, 0.08, 0.3), 14, (0.36, 0.08, 0.2), RED)
    cyl(0.78, 0.32, (0, 0, 1.95), DARK, body, verts=12)
    cyl(0.55, 0.15, (0, 0, 1.75), STEEL, body, verts=12)
    for i, (s, ang) in enumerate(((1, -40), (1, 0), (1, 40), (-1, -40), (-1, 0), (-1, 40))):
        grp = "A" if i in (0, 2, 4) else "B"
        a = math.radians(ang)
        dx, dy = s * math.cos(a), math.sin(a)
        p = empty(f"Leg{grp}_{i}", (dx * 0.62, dy * 0.62, 1.95), body)
        knee = Vector((dx * 1.15, dy * 1.15, 0.25))
        foot = Vector((dx * 1.6, dy * 1.6, -1.92))
        ico(0.16, (0, 0, 0), STEEL, p, sub=1)
        rod((0, 0, 0), knee, 0.14, DARK, p, verts=6, r2=0.11)
        ico(0.15, tuple(knee), STEEL, p, sub=1)
        ico(0.06, tuple(knee + Vector((0, 0, 0.14))), RED, p, sub=1)
        rod(knee, foot, 0.11, GLASS, p, verts=6, r2=0.05)
    return root


ROBOT_FNS = {"ironclad": ironclad, "hover_drone": hover_drone, "hydra_head": hydra_head, "cloaker": cloaker,
             "bomber": bomber, "steam_tank": steam_tank, "stealth_jet": stealth_jet, "nano_swarm": nano_swarm,
             "nano_mite": nano_mite, "sentinel": sentinel}
BOSS_FNS = {"iron_colossus": iron_colossus, "hydra_swarm": hydra_swarm, "black_knight": black_knight,
            "dreadnought": dreadnought, "juggernaut": juggernaut, "hunter_killer": hunter_killer,
            "orbital_uplink": orbital_uplink, "the_core": the_core}
ALL = {**ROBOT_FNS, **BOSS_FNS}


def bounds(root):
    bpy.context.view_layer.update()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in lp.hierarchy(root):
        if o.type == "MESH":
            for v in o.data.vertices:
                w = o.matrix_world @ v.co
                lo = Vector(map(min, lo, w))
                hi = Vector(map(max, hi, w))
    return lo, hi


def purge(root):
    for o in reversed(lp.hierarchy(root)):
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def ref_walker():
    """Scale reference: the existing walker silhouette (robots.py)."""
    root, body = root_body("RefWalker")
    box((0.30, 0.20, 0.14), (0, 0, 0.56), DARK, body, bevel=0.02)
    leg("LegA_L", (0.11, 0, 0.55), body)
    leg("LegB_R", (-0.11, 0, 0.55), body)
    ico(0.24, (0, 0, 0.84), SHELL, body, sub=2, scale=(1.15, 0.9, 1.05))
    ico(0.07, (0, -0.21, 0.86), RED, body, sub=1)
    uvs(0.16, (0, -0.01, 1.2), SHELL, body, seg=10, rings=6, scale=(1, 0.95, 0.8))
    box((0.22, 0.04, 0.045), (0, -0.145, 1.2), RED, body)
    for s in (-1, 1):
        cyl(0.05, 0.36, (s * 0.31, 0, 0.8), STEEL, body, verts=6)
    return root


if __name__ == "__main__":
    names = ONLY.split(",") if ONLY else list(ALL)
    if EXPORT:
        for nm in names:
            r = ALL[nm]()
            lo, hi = bounds(r)
            d = hi - lo
            print(f"SIZE {nm}: w={d.x:.2f} l={d.y:.2f} h={hi.z:.2f} minz={lo.z:.2f}")
            lp.export_glb(r, os.path.join(OUT, "robots", f"{nm}.glb"))
            assert bpy.data.objects.get("Body") is not None
            purge(r)
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        cam = lp.stage()
        res = int(_arg("--res", "1000"))
        which = _arg("--which", "robots,bosses").split(",")
        if "robots" in which:
            lineup = [("ref", ref_walker, -3.2, -0.9), ("hover_drone", hover_drone, -2.0, -1.0),
                      ("cloaker", cloaker, -0.9, -1.0), ("nano_mite", nano_mite, 0.0, -1.1),
                      ("nano_swarm", nano_swarm, 0.9, -1.0), ("stealth_jet", stealth_jet, 2.2, -1.5),
                      ("ironclad", ironclad, -2.8, 1.0), ("hydra_head", hydra_head, -1.3, 1.0),
                      ("bomber", bomber, 0.1, 1.0), ("steam_tank", steam_tank, 1.6, 1.0), ("sentinel", sentinel, 3.0, 1.0)]
            rs = []
            for nm, fn, x, y in lineup:
                r = fn()
                r.location = (x, y, 0)
                r.rotation_euler = (0, 0, math.radians(-20))
                rs.append(r)
            lp.shoot(cam, os.path.join(PREVIEW, "robots2_lineup.png"), (0.0, 0.1, 0.75), 6.6, res=res,
                     pos_dir=(0.45, -1.2, 0.6))
            lp.shoot(cam, os.path.join(PREVIEW, "robots2_top.png"), (0.0, 0.1, 0.5), 7.6, res=int(res * 0.7),
                     pos_dir=(0, -math.cos(math.radians(54)), math.sin(math.radians(54))))
            for r in rs:
                purge(r)
        if "bosses" in which:
            lineup = [("iron_colossus", -6.0, -2.5), ("hydra_swarm", -1.8, -2.5), ("black_knight", 2.4, -2.5),
                      ("dreadnought", 6.4, -2.5), ("juggernaut", -6.0, 3.2), ("hunter_killer", -1.8, 3.2),
                      ("orbital_uplink", 2.4, 3.2), ("the_core", 6.6, 3.2)]
            for nm, x, y in lineup:
                r = BOSS_FNS[nm]()
                r.location = (x, y, 0)
                r.rotation_euler = (0, 0, math.radians(-20))
            ref = ref_walker()
            ref.location = (-3.9, -3.6, 0)
            lp.shoot(cam, os.path.join(PREVIEW, "bosses2_lineup.png"), (0.2, 0.4, 1.8), 17.5, res=res,
                     pos_dir=(0.45, -1.2, 0.6))
            lp.shoot(cam, os.path.join(PREVIEW, "bosses2_top.png"), (0.2, 0.4, 1.0), 17.5, res=int(res * 0.7),
                     pos_dir=(0, -math.cos(math.radians(54)), math.sin(math.radians(54))))
    print("DONE")
