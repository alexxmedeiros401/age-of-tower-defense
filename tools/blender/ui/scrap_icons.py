"""Scrap, the currency of each age: one pile of salvaged robot parts (a big gear leaning on a curled armour plate with its
red eye lens, a bolt sticking up, a nut and a spring), recoloured and given one extra piece per age, so every age's Scrap
reads as the same thing with its own look.

    python3 tools/blender/ui/scrap_icons.py [--only stone,bronze] [--samples 48] [--res 512]

Writes assets/ui/scrap_<age key>.png (256 px) and copies the Stone Age pile to assets/ui/icon_scrap.png (used where no
age is at hand).
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Euler
import ui_kit as K

A = sys.argv
ONLY = A[A.index("--only") + 1].split(",") if "--only" in A else None
SAMPLES = int(A[A.index("--samples") + 1]) if "--samples" in A else 48
RES = int(A[A.index("--res") + 1]) if "--res" in A else 512
TMP = os.path.join(__import__("tempfile").gettempdir(), "scrap_render")
os.makedirs(TMP, exist_ok=True)

# age key -> gear metal, plate paint (metallic?), lens colour, bolt metal, and the extra piece
AGES = {
    "stone":      dict(gear=(0.78, 0.81, 0.86), plate=(0.93, 0.93, 0.9), pm=0.0, lens=(1.0, 0.25, 0.12), bolt=(0.6, 0.63, 0.68)),
    "bronze":     dict(gear=(0.95, 0.62, 0.3), plate=(0.86, 0.55, 0.26), pm=1.0, lens=(1.0, 0.45, 0.1), bolt=(0.8, 0.5, 0.24)),
    "iron":       dict(gear=(0.45, 0.46, 0.5), plate=(0.36, 0.37, 0.4), pm=1.0, lens=(1.0, 0.5, 0.1), bolt=(0.38, 0.39, 0.42)),
    "classical":  dict(gear=(1.0, 0.77, 0.3), plate=(0.96, 0.94, 0.9), pm=0.0, lens=(0.3, 0.6, 1.0), bolt=(0.98, 0.75, 0.32)),
    "medieval":   dict(gear=(0.66, 0.7, 0.78), plate=(0.25, 0.32, 0.62), pm=0.0, lens=(1.0, 0.8, 0.2), bolt=(0.55, 0.58, 0.64)),
    "gunpowder":  dict(gear=(0.96, 0.76, 0.36), plate=(0.55, 0.12, 0.1), pm=0.0, lens=(1.0, 0.7, 0.2), bolt=(0.9, 0.7, 0.32)),
    "industrial": dict(gear=(0.9, 0.5, 0.3), plate=(0.24, 0.22, 0.22), pm=1.0, lens=(1.0, 0.6, 0.15), bolt=(0.92, 0.72, 0.34)),
    "modern":     dict(gear=(0.7, 0.72, 0.75), plate=(0.4, 0.47, 0.25), pm=0.0, lens=(0.2, 1.0, 0.3), bolt=(0.55, 0.57, 0.6)),
    "digital":    dict(gear=(0.85, 0.9, 0.96), plate=(0.16, 0.2, 0.3), pm=0.0, lens=(0.2, 0.95, 1.0), bolt=(0.7, 0.75, 0.82)),
    "datacenter": dict(gear=(0.3, 0.3, 0.36), plate=(0.1, 0.1, 0.13), pm=0.0, lens=(1.0, 0.25, 0.85), bolt=(0.25, 0.25, 0.3)),
}


def gear_profile(R, depth, teeth):
    pts = []
    for t in range(teeth):
        a0 = 2 * math.pi * t / teeth
        for f, r in ((0.0, R - depth), (0.14, R - depth), (0.27, R), (0.6, R), (0.73, R - depth)):
            a = a0 + f * 2 * math.pi / teeth
            pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def hexagon(r):
    return [(r * math.cos(math.pi / 3 * i + math.pi / 6), r * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]


def place(ob, loc, rot):
    ob.location = Vector(loc)
    ob.rotation_euler = Euler([math.radians(x) for x in rot])


ACCENT = [(0.9, 0.2, 0.1)]


def plate(m_plate, m_rivet, m_lens, m_rim):
    """A curled shard of robot armour: painted plate with a torn corner, rivets, and the socket of a red eye lens."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=40, y_segments=28, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.36
        v.co.y *= 0.28
    me = bpy.data.meshes.new("Plate")
    bm.to_mesh(me)
    bm.free()
    ob = K.link(me, "Plate", m_plate)
    so = ob.modifiers.new("Solid", "SOLIDIFY")
    so.thickness = 0.045
    so.offset = 0.0
    # the torn corner: cut along a jagged line
    zz = [(0.0, 0.42)]
    for i in range(9):
        t = i / 8.0
        x = 0.05 + 0.34 * t
        y = 0.3 - 0.38 * t + (0.035 if i % 2 else -0.02)
        zz.append((x, y))
    zz += [(0.5, -0.2), (0.5, 0.42)]
    cut = K.prism("Tear", zz, -0.2, 0.2)
    cut.hide_render = cut.hide_viewport = True
    cut.parent = ob
    bo = ob.modifiers.new("Tear", "BOOLEAN")
    bo.operation = "DIFFERENCE"
    bo.object = cut
    bo.solver = "EXACT"
    bd = ob.modifiers.new("Bend", "SIMPLE_DEFORM")
    bd.deform_method = "BEND"
    bd.deform_axis = "Y"
    bd.angle = math.radians(40)
    K.bevel(ob, 0.012, 2, 40)
    rim = K.torus("LensRim", 0.088, 0.024, m_rim, loc=(0.16, -0.08, 0.03), seg=48, mseg=12)
    lens = K.sphere("Lens", 0.078, m_lens, loc=(0.16, -0.08, 0.03), scale=(1, 1, 0.55), seg=32, rings=16)
    for r in (rim, lens):
        r.parent = ob
    stripe = K.prism("Stripe", [(-0.36, 0.05), (-0.36, 0.12), (0.1, 0.28), (0.1, 0.21)], 0.0, 0.006,
                     K.paint("StripePaint", ACCENT[0], 0.35, coat=0.4), loc=(0, 0, 0.022))
    stripe.parent = ob
    for x, y in ((-0.3, 0.22), (-0.3, -0.22), (0.02, -0.23), (0.3, -0.23), (-0.08, 0.22)):
        rv = K.sphere("Rivet", 0.026, m_rivet, loc=(x, y, 0.03), scale=(1, 1, 0.6), seg=16, rings=8)
        rv.parent = ob
    return ob


def gear(m):
    ob = K.prism("Gear", gear_profile(0.36, 0.1, 8), -0.06, 0.06, m,
                 holes=[(0, 0, 0.075, 32)] + [(0.19 * math.cos(a), 0.19 * math.sin(a), 0.055, 24) for a in
                                              [i * 2 * math.pi / 4 + math.pi / 4 for i in range(4)]])
    K.bevel(ob, 0.016, 3, 30)
    hub = K.torus("Hub", 0.1, 0.035, m, seg=48, mseg=16)
    hub.parent = ob
    hub.location = (0, 0, 0.05)
    return ob


def bolt(m):
    head = K.prism("BoltHead", hexagon(0.1), 0, 0.085, m)
    K.bevel(head, 0.014, 3, 30)
    shaft = K.cylinder("Shaft", 0.05, 0.4, 32, m, loc=(0, 0, -0.2))
    shaft.parent = head
    K.bevel(shaft, 0.01, 2, 40)
    for i in range(9):
        t = K.torus("Thread", 0.05, 0.011, m, loc=(0, 0, -0.09 - i * 0.034), seg=32, mseg=8)
        t.parent = head
    return head


def nut(m):
    ob = K.prism("Nut", hexagon(0.085), -0.035, 0.035, m, holes=[(0, 0, 0.04, 32)])
    K.bevel(ob, 0.012, 3, 30)
    return ob


def spring(m):
    pts = []
    turns, r, h = 4.5, 0.075, 0.28
    for i in range(int(turns * 32) + 1):
        a = 2 * math.pi * i / 32
        pts.append((r * math.cos(a), r * math.sin(a), -h / 2 + h * i / (turns * 32)))
    return K.curve_tube("Spring", pts, 0.017, m)


def build(key):
    cfg = AGES[key]
    ACCENT[0] = cfg.get("accent", tuple(min(1.0, c * 0.85) for c in cfg["lens"]))
    K.reset(RES, SAMPLES, hdri="studio.exr", hdri_strength=0.9, hdri_rot=0.6)
    if key == "bronze":
        m_gear = K.weathered("Gear", cfg["gear"], (0.32, 0.72, 0.6), 0.45, 5.0)
        m_plate = K.weathered("Plate", cfg["plate"], (0.3, 0.68, 0.58), 0.6, 4.0)
    elif key == "iron":
        m_gear = K.weathered("Gear", cfg["gear"], (0.62, 0.27, 0.08), 0.45, 5.0)
        m_plate = K.weathered("Plate", cfg["plate"], (0.6, 0.26, 0.08), 0.65, 4.0)
    else:
        m_gear = K.metal("Gear", cfg["gear"], 0.24, 1.0, noise=0.06)
        m_plate = K.metal("Plate", cfg["plate"], 0.3, 1.0, noise=0.06) if cfg["pm"] > 0 else K.paint("Plate", cfg["plate"], 0.3, coat=0.5)
    m_bolt = K.metal("Bolt", cfg["bolt"], 0.28, 1.0, noise=0.05)
    m_lens = K.emit("Lens", cfg["lens"], 2.4)
    m_rim = K.metal("LensRim", (0.2, 0.21, 0.24), 0.3)
    pl = plate(m_plate, m_bolt, m_lens, m_rim)
    place(pl, (0.2, 0.2, 0.34), (62, 0, -32))           # armour shard standing behind, leaning back
    g = gear(m_gear)
    place(g, (-0.13, -0.12, 0.33), (66, 6, 10))         # the big gear in front of it
    b = bolt(m_bolt)
    place(b, (0.28, -0.3, 0.3), (-44, 40, 18))          # across the front right, head up
    n = nut(m_bolt)
    place(n, (-0.36, -0.42, 0.06), (10, -6, 18))
    extra(key, pl, g, b)
    K.studio(key=3.4, rim=3.0, fill=0.8)
    cam = K.camera((-1.2, -3.5, 2.5), (0.0, 0.0, 0.3), lens=85)
    K.fit_ortho(cam, margin=0.03)
    raw = os.path.join(TMP, key + ".png")
    K.render(raw)
    out = os.path.join(K.UI, "scrap_%s.png" % key)
    K.post(raw, out, size=256, outline=0.016, shadow=0.012, shadow_off=(0.0, 0.025), pad=0.05)
    print("wrote", out, flush=True)
    return out


def extra(key, pl, g, b):
    if key == "stone":
        # a leather thong lashed round the bolt
        lea = K.paint("Leather", (0.42, 0.22, 0.09), 0.6)
        pts = []
        for i in range(4 * 24 + 1):
            a = 2 * math.pi * i / 24
            pts.append((0.064 * math.cos(a), 0.064 * math.sin(a), -0.1 - 0.16 * i / (4 * 24)))
        th = K.curve_tube("Thong", pts, 0.019, lea)
        th.parent = b
        tail = K.curve_tube("ThongTail", [(0.064, 0, -0.26), (0.11, -0.03, -0.29), (0.17, -0.07, -0.35), (0.2, -0.08, -0.43)], 0.017, lea)
        tail.parent = b
    elif key == "classical":
        leaf = K.metal("LaurelGold", (1.0, 0.8, 0.32), 0.18)
        stem = []
        for i in range(9):
            t = i / 8.0
            a = math.radians(200 - 170 * t)
            x, y = 0.3 * math.cos(a), 0.3 * math.sin(a)
            stem.append((x, y, 0.08))
            for sgn in (-1, 1):
                lf = K.sphere("Leaf", 0.055, leaf, loc=(x * (1 + sgn * 0.13), y * (1 + sgn * 0.13), 0.085), scale=(1.0, 0.42, 0.18), seg=12, rings=6)
                lf.rotation_euler = Euler((0, 0, a + math.pi / 2 + sgn * 0.6))
                lf.parent = g
        st = K.curve_tube("Stem", stem, 0.012, leaf)
        st.parent = g
    elif key == "medieval":
        chain = K.metal("Chain", (0.72, 0.75, 0.8), 0.22)
        for i in range(5):
            ln = K.torus("Link", 0.06, 0.016, chain, loc=(-0.52 + i * 0.09, -0.18 - i * 0.045, 0.06), seg=32, mseg=10)
            ln.scale = (1.0, 0.6, 1.0)
            ln.rotation_euler = Euler((math.radians(90) * (i % 2), 0, -0.45))
    elif key == "gunpowder":
        K.sphere("Cannonball", 0.14, K.metal("BallIron", (0.13, 0.13, 0.14), 0.32), loc=(-0.5, -0.12, 0.14))
    elif key == "industrial":
        red = K.paint("ValveRed", (0.85, 0.12, 0.08), 0.3, coat=0.6)
        w = K.torus("Valve", 0.12, 0.022, red, loc=(-0.5, -0.12, 0.17), seg=48, mseg=12)
        w.rotation_euler = Euler((math.radians(60), 0, 0.5))
        for i in range(3):
            sp = K.cylinder("Spoke", 0.014, 0.24, 12, red)
            sp.parent = w
            sp.rotation_euler = Euler((math.radians(90), 0, i * math.pi / 3))
        hb = K.cylinder("ValveHub", 0.034, 0.06, 16, red)
        hb.parent = w
    elif key == "modern":
        yel = K.paint("HazYellow", (1.0, 0.78, 0.08), 0.35)
        blk = K.paint("HazBlack", (0.06, 0.06, 0.07), 0.4)
        for i in range(7):
            st = K.prism("Stripe", [(-0.025, -0.1), (0.025, -0.1), (0.075, 0.1), (0.025, 0.1)], 0, 0.004,
                         yel if i % 2 == 0 else blk, loc=(-0.05 + i * 0.05 - 0.15, -0.12, 0.024))
            st.parent = pl
    elif key == "digital":
        pcb = K.paint("PCB", (0.08, 0.55, 0.28), 0.4)
        chip = K.prism("Chip", [(-0.14, -0.1), (0.14, -0.1), (0.14, 0.1), (-0.14, 0.1)], 0, 0.022, pcb, loc=(-0.5, -0.14, 0.06), rot=(0.35, 0.1, 0.5))
        K.bevel(chip, 0.005, 1, 30)
        die = K.prism("Die", [(-0.055, -0.055), (0.055, -0.055), (0.055, 0.055), (-0.055, 0.055)], 0.02, 0.045, K.paint("Die", (0.06, 0.06, 0.08), 0.2))
        die.parent = chip
        led = K.sphere("LED", 0.026, K.emit("LEDCyan", (0.2, 0.95, 1.0), 6.0), loc=(0.095, 0.055, 0.03), seg=12, rings=6)
        led.parent = chip
        gp = K.metal("Pins", (1.0, 0.8, 0.32), 0.2)
        for i in range(6):
            p = K.prism("Pin", [(-0.009, 0), (0.009, 0), (0.009, 0.035), (-0.009, 0.035)], 0, 0.006, gp, loc=(-0.11 + i * 0.044, 0.1, 0.008))
            p.parent = chip
    elif key == "datacenter":
        crystal = K.emit("CoreMagenta", (1.0, 0.25, 0.85), 3.0)
        c = K.sphere("Core", 0.12, crystal, loc=(-0.5, -0.12, 0.16), scale=(0.75, 0.75, 1.3), seg=6, rings=4)
        c.rotation_euler = Euler((0.2, 0.25, 0.5))
        neon = K.emit("NeonPurple", (0.65, 0.3, 1.0), 4.0)
        for y in (-0.12, 0.12):
            ln = K.cylinder("Neon", 0.012, 0.62, 12, neon, loc=(0.0, y, 0.03), rot=(0, math.radians(90), 0))
            ln.parent = pl


for k in AGES:
    if ONLY and k not in ONLY:
        continue
    build(k)
if not ONLY or "stone" in ONLY:
    import shutil
    shutil.copy(os.path.join(K.UI, "scrap_stone.png"), os.path.join(K.UI, "icon_scrap.png"))
