"""HQ Modern Age map props, sculpted as distance fields like decor_props, decor_bronze, decor_iron, decor_classical,
decor_medieval, decor_gunpowder and decor_industrial (same conventions: every builder returns its parts [(part name,
Field, voxel, material key)], built at the origin, Z up, ground at z = 0, a landmark's front toward -Y, a vehicle's nose
toward +X; KITS lists each theme's props and their game-mesh triangle budgets; decor_build.materials resolves the keys).

Airbase (military): HESCO barriers, sandbag walls, fuel drums, jerrycans, ammunition crates, traffic cones, light towers,
chain-link sections with razor wire, jersey barriers, a parked Humvee, dry scrub; landmarks: an arched hangar with a jet
nosing out of its doors, the control tower, a parked fighter on its chocks, a helicopter on its pad, a fuel bowser, a
radar dome; for the no-build zones rubble and a burnt-out wreck round the craters, a radar dish on its trailer, a
generator, an anti-aircraft gun in its sandbag ring, crates on a pallet and a forklift.
Downtown (metro): street lights, traffic lights, benches, a bus shelter, fire hydrants, newspaper boxes, bollards, trash
cans, street trees in planters and in iron guards; landmarks: two glass office towers with lit windows, a chrome diner
under its neon sign, a row of shop fronts with awnings and neon, a billboard, a city bus and a yellow cab; for the
no-build zones a mid-rise block with a water tank on its roof, and street trees.
Suburbia (suburb): mailboxes, picket fences, clipped hedges, garden gnomes, a bike, wheelie bins, lawn chairs, maples
and oaks, flower pots; landmarks: a two-storey house with its porch, garage and the minivan in the driveway, a ranch
house, a playground, a basketball hoop, a treehouse; for the no-build zones a cape-cod house, and the pool's
surroundings (loungers, an umbrella, a diving board, the pool ladder: the water itself is in the ground).
The Modern city at the end of every Modern Age road (a fortified command bunker: reinforced concrete under an earth
berm, blast doors open to the road, sandbag and HESCO walls, a radar mast and antennas, floodlights, the task force's
flag, camouflage netting, a watchtower) is its own kit ("bunker_city", modern_city.glb).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Chain, Plane, Func, rot_from_axes, v3, NOISE, euler
import decor_props as DP
from decor_props import vx, wob, convex, rock
from decor_bronze import fine, unit, box_bounds, ground_cut, cut_above, place, place_parts, convex_w, walls_box, scrub
from decor_iron import Rz, R_xz, cone, gable, pyramid_roof, post
from decor_medieval import oak
from decor_gunpowder import leaf, mirror, sandbag, flag, poly_sdf2
from decor_industrial import retex, plane_tree

F32 = np.float32
Z = v3((0, 0, 1))
RX = rot_from_axes(z_axis=(1, 0, 0))          # a cylinder's axis along X
RY = rot_from_axes(z_axis=(0, 1, 0))          # ... along Y


# ------------------------------------------------------------------------------------------------ helpers
def box(f, c, half, r=0.01, R=None, k=0.0, label=0):
    f.add(RoundBox(c, half, r, R=R), k=k, label=label)


def wheel(tf, hf, c, axis, r, w, hub=0.55, lugs=0):
    """A road wheel about `axis` (pointing out from the vehicle) through c: a rounded tyre (field tf), its hub (hf)
    proud of the tyre's outer wall; `lugs`: that many bumps round the hub."""
    a = unit(axis)
    R = rot_from_axes(z_axis=a)
    c = v3(c)
    tf.add(Cylinder(c, r, w, rr=min(w * 0.4, r * 0.35), R=R), k=0.0)
    tf.add(Torus(c, r * 0.82, w * 0.36, R=R), k=0.02)
    hf.add(Cylinder(c + a * (w * 0.36), r * hub, w * 0.22, rr=0.006, R=R), k=0.0)
    hf.add(Sphere(c + a * (w * 0.5), r * hub * 0.35), k=0.01)
    for k in range(lugs):
        t = 2 * math.pi * k / lugs
        q = c + a * (w * 0.47) + R @ v3((math.cos(t) * r * hub * 0.62, math.sin(t) * r * hub * 0.62, 0.0))
        hf.add(Sphere(q, r * 0.06), k=0.004)


def greenhouse(x_ws, x_wt, x_rt, x_rs, z0, z1, hw0, hw1):
    """A car's glasshouse as a convex block: the windscreen from (x_ws, z0) up to (x_wt, z1), the roof to x_rt, the
    rear glass down to (x_rs, z0); its sides lean in from half width hw0 at z0 to hw1 at z1 (nose toward +X)."""
    tw = (hw0 - hw1) / max(z1 - z0, 1e-3)
    planes = [((0, 0, z1), (0, 0, 1)), ((0, 0, z0), (0, 0, -1)),
              ((x_ws, 0, z0), (z1 - z0, 0, x_ws - x_wt)), ((x_rs, 0, z0), (-(z1 - z0), 0, x_rt - x_rs)),
              ((0, hw0, z0), (0, 1, tw)), ((0, -hw0, z0), (0, -1, tw))]
    lo = (min(x_rs, x_rt) - 0.1, -hw0 - 0.1, z0 - 0.1)
    hi = (max(x_ws, x_wt) + 0.1, hw0 + 0.1, z1 + 0.1)
    return convex(planes, lo, hi)


def car(out, L=1.4, W=0.62, H=0.52, rw=0.13, paint="car", seed=0, lit=False, kind="sedan", name="", o=(0, 0, 0), yaw=0.0, hubs="chrome"):
    """A chunky toy car, nose toward +X, L long, W wide, H to its roof, wheels of radius rw: the body (paint), its
    glasshouse (glass) framed by the roof and pillars, black bumpers, grille and sills (label 7), chrome (6), lamps
    (lit: glowing headlamps and tail lamps); kind sedan, taxi (a roof sign, a checker band), van (a tall box with a
    sliding door line), suv (boxy, high). Placed at o turned by yaw."""
    parts = []
    bd, gl, tf, hf, lp, tl = (Field(name + n) for n in ("Body", "Glass", "Tyres", "Hubs", "Lamps", "Tail"))
    hl, hw = L / 2, W / 2
    zb0, zb1 = rw * 0.55, H * (0.56 if kind in ("sedan", "taxi") else 0.5)
    box(bd, (0, 0, (zb0 + zb1) / 2), (hl, hw, (zb1 - zb0) / 2), 0.06)
    if kind in ("sedan", "taxi"):                                   # a lower nose and tail than the cabin's waist
        bd.sub(RoundBox((hl + 0.02, 0, zb1 + 0.02), (0.08, hw + 0.05, 0.06), 0.03), k=0.04)
        g = greenhouse(hl * 0.42, hl * 0.02, -hl * 0.48, -hl * 0.78, zb1 - 0.01, H, hw - 0.02, hw - 0.08)
    elif kind == "van":
        g = greenhouse(hl * 0.62, hl * 0.32, -hl * 0.92, -hl * 0.97, zb1 - 0.01, H, hw - 0.01, hw - 0.05)
    else:
        g = greenhouse(hl * 0.5, hl * 0.32, -hl * 0.86, -hl * 0.92, zb1 - 0.01, H, hw - 0.01, hw - 0.03)
    gl.add(g, k=0.0)
    gfn = g.fn
    bd.add(Func(lambda P: (gfn(P) - F32(0.006)).astype(F32), g.lo - 0.01, g.hi + 0.01), k=0.02)
    pil = 0.035
    zw0, zw1 = zb1 + 0.025, H - 0.03
    # side windows between the pillars, the windscreen and the rear glass inside their pillars
    if kind in ("sedan", "taxi"):
        xs = [(-hl * 0.6 + pil, -hl * 0.08), (-hl * 0.08 + pil, hl * 0.2)]
    elif kind == "van":
        xs = [(-hl * 0.82, -hl * 0.4), (-hl * 0.4 + pil, hl * 0.05), (hl * 0.05 + pil, hl * 0.4)]
    else:
        xs = [(-hl * 0.78, -hl * 0.3), (-hl * 0.3 + pil, hl * 0.32)]
    for (xa, xb) in xs:
        bd.sub(RoundBox(((xa + xb) / 2, 0, (zw0 + zw1) / 2), ((xb - xa) / 2, hw + 0.1, (zw1 - zw0) / 2), 0.012), k=0.0)
    bd.sub(RoundBox((hl * 0.55, 0, (zw0 + zw1) / 2), (hl * 0.32, hw - 0.075, (zw1 - zw0) / 2), 0.012), k=0.0)
    bd.sub(RoundBox((-hl * 0.95, 0, (zw0 + zw1) / 2 + 0.01), (hl * 0.3, hw - 0.075, (zw1 - zw0) / 2 - 0.01), 0.012), k=0.0)
    # bumpers, grille, sills, mirrors, door seams, handles
    for sx in (-1, 1):
        box(bd, (sx * (hl + 0.005), 0, zb0 + 0.05), (0.03, hw + 0.01, 0.04), 0.02, k=0.004, label=7)
    box(bd, (hl + 0.006, 0, zb0 + 0.13), (0.012, hw * 0.5, 0.035), 0.008, k=0.002, label=7)
    for sy in (-1, 1):
        box(bd, (0, sy * (hw + 0.004), zb0 + 0.02), (hl * 0.6, 0.012, 0.022), 0.008, k=0.002, label=7)
        box(bd, (hl * 0.28, sy * (hw + 0.03), zb1 + 0.04), (0.03, 0.025, 0.022), 0.01, k=0.004, label=7)
        bd.sub(RoundBox((hl * 0.02 if kind != "van" else hl * 0.05, sy * (hw + 0.004), (zb0 + zb1) / 2 + 0.02),
                        (0.004, 0.012, (zb1 - zb0) / 2 - 0.01), 0.0), k=0.0)
        bd.add(RoundBox((-hl * 0.15, sy * (hw + 0.004), zb1 - 0.04), (0.025, 0.008, 0.008), 0.004), k=0.002, label=6)
        if kind == "van":                                       # the sliding door's rail
            box(bd, (-hl * 0.2, sy * (hw + 0.006), zw1 - 0.02), (hl * 0.35, 0.006, 0.006), 0.003, k=0.0, label=7)
    if kind == "taxi":                                          # the checker band and the roof sign
        for sy in (-1, 1):
            bd.paint(RoundBox((0, sy * hw, zb1 - 0.035), (hl * 0.9, 0.05, 0.022), 0.0), 7)
            for i in range(int(hl * 1.8 / 0.06)):
                bd.paint(RoundBox((-hl * 0.9 + 0.03 + i * 0.06, sy * hw, zb1 - 0.035 + (0.011 if i % 2 else -0.011)),
                                  (0.015, 0.06, 0.011), 0.0), 9)
        box(bd, (-hl * 0.15, 0, H + 0.035), (0.12, 0.05, 0.035), 0.012, k=0.004, label=9)
        bd.paint(RoundBox((-hl * 0.15, 0, H + 0.04), (0.1, 0.07, 0.016), 0.0), 7)
    for sy in (-1, 1):
        q = v3((hl - 0.01, sy * (hw - 0.09), zb1 - 0.06))
        (lp if lit else bd).add(RoundBox(q, (0.02, 0.055, 0.03), 0.012), k=0.0, label=6)
        q = v3((-hl + 0.005, sy * (hw - 0.07), zb1 - 0.05))
        (tl if lit else bd).add(RoundBox(q, (0.015, 0.05, 0.035), 0.01), k=0.0, label=8)
    rr = rw
    xw = (hl * 0.66, -hl * 0.62)
    for x in xw:
        for sy in (-1, 1):                                      # the wheel arches (outboard only)
            bd.sub(Cylinder((x, sy * (hw - 0.03), rr), rr + 0.022, 0.26, R=RY), k=0.02)
        for sy in (-1, 1):
            wheel(tf, hf, (x, sy * (hw - 0.07), rr), (0, sy, 0), rr, 0.1, lugs=5)
    ground_cut(tf, -0.01)
    parts += [(name + "Body", bd, fine(0.006, 0.012), paint), (name + "Glass", gl, fine(0.006, 0.012), "glass"),
              (name + "Tyres", tf, fine(0.005, 0.01), "rubber"), (name + "Hubs", hf, fine(0.004, 0.008), hubs)]
    if lit:
        parts += [(name + "Lamps", lp, fine(0.004, 0.008), "glow_lamp"), (name + "Tail", tl, fine(0.004, 0.008), "glow_red")]
    return place_parts(out, parts, o, Rz(yaw))


def drum(f, c, r=0.1, h=0.3, R=None, label=0):
    """A steel 55-gallon drum (field f): two rolling hoops, the rims, the bung on its lid."""
    R = np.eye(3) if R is None else R
    c = v3(c)
    ax = R @ Z
    f.add(Cylinder(c, r, h, rr=0.012, R=R), k=0.0, label=label)
    for t in (-0.18, 0.18):
        f.add(Torus(c + ax * (h * t), r + 0.003, 0.008, R=R), k=0.004, label=label)
    for t in (-0.5, 0.5):
        f.add(Torus(c + ax * (h * t * 0.97), r - 0.004, 0.009, R=R), k=0.003, label=label)
    f.add(Cylinder(c + ax * (h * 0.5) + R @ v3((r * 0.55, 0, 0)), 0.02, 0.012, R=R), k=0.003, label=6)


def jerrycan(f, c, yaw=0.0, s=1.0, tilt=0.0):
    """A jerrycan (field f): the flat can with its X-pressing (label 5 paints nothing: the pressing is relief), the
    three handles on top and the spout cap."""
    R = Rz(yaw) @ euler(tilt, 0, 0)
    c = v3(c)
    hx, hy, hz = 0.1 * s, 0.045 * s, 0.13 * s
    f.add(RoundBox(c, (hx, hy, hz), 0.014 * s, R=R), k=0.0)
    for sy in (-1, 1):                                               # the X pressed into each face
        for sg in (-1, 1):
            d = unit(v3((hx * 0.8, 0, sg * hz * 0.8)))
            Rd = R @ np.stack([d, v3((0, 1, 0)), np.cross(d, v3((0, 1, 0)))], axis=1)
            f.add(RoundBox(c + R @ v3((0, sy * hy, 0)), (math.hypot(hx, hz) * 0.75, 0.006 * s, 0.012 * s), 0.004, R=Rd), k=0.006)
    for x in (-0.06, 0.0, 0.06):
        f.add(RoundCone(c + R @ v3((x * s, 0, hz + 0.004)), c + R @ v3((x * s, 0, hz + 0.035 * s)), 0.008 * s, 0.008 * s), k=0.004)
    f.add(RoundBox(c + R @ v3((0, 0, hz + 0.035 * s)), (0.08 * s, 0.01 * s, 0.008 * s), 0.005, R=R), k=0.004)
    f.add(Cylinder(c + R @ v3((hx * 0.75, 0, hz + 0.02 * s)), 0.02 * s, 0.04 * s, rr=0.006, R=R), k=0.004, label=7)


def stencil(f, c, nrm, w, h, label=5, n=3):
    """Paint a stencilled marking (label) on a face at c (outward normal nrm): a few short bars, as lettering reads
    from far off."""
    nn = unit(v3((nrm[0], nrm[1], 0.0)))
    s = v3((nn[1], -nn[0], 0.0))
    c = v3(c)
    for i in range(n):
        q = c + s * ((i - (n - 1) / 2) * w / n)
        f.paint(RoundBox(q, (w / n * 0.36 * abs(s[0]) + 0.03 * abs(nn[0]), w / n * 0.36 * abs(s[1]) + 0.03 * abs(nn[1]), h / 2), 0.0), label)


def ammo_crate(f, c, half, yaw=0.0, label=0, mark=True):
    """An olive ammunition crate (field f): its lid lip, rope beckets at the ends, latches, a stencilled marking."""
    R = Rz(yaw)
    c = v3(c)
    hx, hy, hz = half
    f.add(RoundBox(c, half, 0.012, R=R), k=0.0, label=label)
    f.add(RoundBox(c + R @ v3((0, 0, hz - 0.02)), (hx + 0.008, hy + 0.008, 0.016), 0.006, R=R), k=0.003, label=label)
    for sx in (-1, 1):
        f.add(Torus(c + R @ v3((sx * (hx + 0.01), 0, hz * 0.2)), 0.035, 0.007, R=R @ RX), k=0.002, label=8)
        for sy in (-1, 1):
            f.add(RoundBox(c + R @ v3((sx * hx * 0.5, sy * (hy + 0.006), hz - 0.05)), (0.012, 0.006, 0.02), 0.003, R=R), k=0.002, label=7)
    if mark:
        f.paint(RoundBox(c + R @ v3((0, -hy, 0)), (hx * 0.7, 0.02, hz * 0.18), 0.0, R=R), 5)
        f.paint(RoundBox(c + R @ v3((0, 0, hz)), (hx * 0.5, hy * 0.25, 0.03), 0.0, R=R), 5)


def ammo_can(f, c, yaw=0.0, s=1.0, label=0):
    """A steel ammunition can: the box, its lid with the latch arm and the carrying handle."""
    R = Rz(yaw)
    c = v3(c)
    f.add(RoundBox(c, (0.08 * s, 0.04 * s, 0.055 * s), 0.008, R=R), k=0.0, label=label)
    f.add(RoundBox(c + R @ v3((0, 0, 0.058 * s)), (0.085 * s, 0.045 * s, 0.008 * s), 0.004, R=R), k=0.003, label=label)
    f.add(Torus(c + R @ v3((0, 0, 0.07 * s)), 0.025 * s, 0.005 * s, R=R @ RY), k=0.002, label=7)
    f.add(RoundBox(c + R @ v3((0.084 * s, 0, 0.03 * s)), (0.006, 0.02 * s, 0.03 * s), 0.003, R=R), k=0.002, label=7)


def pallet(f, c, hx=0.36, hy=0.3, yaw=0.0):
    """A wooden pallet (field f): top boards over three bearers on blocks."""
    R = Rz(yaw)
    c = v3(c)
    n = int(hx / 0.07)
    for i in range(n):
        x = -hx + (i + 0.5) * 2 * hx / n
        f.add(RoundBox(c + R @ v3((x, 0, 0.085)), (hx / n * 0.8, hy, 0.012), 0.004, R=R), k=0.0, label=10)
    for y in (-hy + 0.03, 0.0, hy - 0.03):
        f.add(RoundBox(c + R @ v3((0, y, 0.06)), (hx, 0.035, 0.014), 0.004, R=R), k=0.0)
        for x in (-hx + 0.04, 0.0, hx - 0.04):
            f.add(RoundBox(c + R @ v3((x, y, 0.025)), (0.035, 0.035, 0.025), 0.004, R=R), k=0.0, label=11)


def hesco_cell(f, c, s=0.38, h=0.4, yaw=0.0, seed=0, fill=None):
    """A HESCO bastion cell: a square wire-mesh basket lined with tan geotextile (field f: the material draws the mesh),
    bulging a little, its corner coils, filled to the top with earth (field `fill`, sunk a little)."""
    R = Rz(yaw)
    c = v3(c)
    hs = s / 2
    f.add(RoundBox(c + Z * (h / 2), (hs, hs, h / 2), 0.02, R=R, **wob(9.0, 0.006, seed)), k=0.0)
    f.sub(RoundBox(c + Z * (h + 0.02), (hs - 0.025, hs - 0.025, 0.05), 0.01, R=R), k=0.006)
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = c + R @ v3((sx * hs, sy * hs, 0))
            f.add(RoundCone(q, q + Z * h, 0.012, 0.012), k=0.004, label=5)
    if fill is not None:
        fill.add(RoundBox(c + Z * (h - 0.04), (hs - 0.02, hs - 0.02, 0.03), 0.02, R=R, **wob(12.0, 0.01, seed + 3)), k=0.0)


def sandbag_run(f, a, b, layers=3, seed=0, rows=1, z0=0.0, gap=0.235):
    """Sandbags laid in courses from a to b (horizontal), stretcher bond, `rows` deep."""
    rng = np.random.default_rng(seed)
    a, b = v3(a), v3(b)
    d = b - a
    L = float(np.linalg.norm(d[:2]))
    t = unit(v3((d[0], d[1], 0.0)))
    nrm = v3((-t[1], t[0], 0.0))
    yaw = math.atan2(t[1], t[0])
    for layer in range(layers):
        z = z0 + 0.045 + layer * 0.085
        n = max(1, int(L / gap))
        for i in range(n + (0 if layer % 2 else 1)):
            s = (i + (0.5 if layer % 2 else 0.0)) * gap
            if s > L + 0.02:
                continue
            for r in range(rows):
                q = a + t * s + nrm * ((r - (rows - 1) / 2) * 0.14) + Z * z
                sandbag(f, q, yaw + rng.uniform(-0.08, 0.08), seed=seed + layer * 97 + i * 3 + r)


def flood_head(f, gl, c, d, s=1.0):
    """A floodlight head at c aimed along d: the box lamp housing (field f) and its glowing face (gl), a yoke."""
    d = unit(d)
    R = rot_from_axes(z_axis=d)
    c = v3(c)
    f.add(RoundBox(c, (0.09 * s, 0.07 * s, 0.05 * s), 0.015, R=R), k=0.0)
    f.add(RoundBox(c - d * (0.06 * s), (0.07 * s, 0.05 * s, 0.02 * s), 0.01, R=R), k=0.006)
    gl.add(RoundBox(c + d * (0.05 * s), (0.075 * s, 0.055 * s, 0.006), 0.008, R=R), k=0.0)


def lattice_mast(f, c, z0, z1, r0, r1, legs=3, step=0.28, rod=0.012):
    """A lattice mast (field f): `legs` tubular legs tapering from radius r0 at z0 to r1 at z1, zig-zag bracing."""
    c = v3(c)
    pts = []
    for i in range(legs):
        a = 2 * math.pi * i / legs + math.pi / 2
        u = v3((math.cos(a), math.sin(a), 0))
        pts.append(u)
        f.add(RoundCone(c + u * r0 + Z * z0, c + u * r1 + Z * z1, rod * 1.6, rod * 1.3), k=0.0)
    n = max(2, int((z1 - z0) / step))
    for j in range(n):
        za, zb = z0 + (z1 - z0) * j / n, z0 + (z1 - z0) * (j + 1) / n
        ra, rb = r0 + (r1 - r0) * j / n, r0 + (r1 - r0) * (j + 1) / n
        for i in range(legs):
            u, w = pts[i], pts[(i + 1) % legs]
            p, q = (c + u * ra + Z * za, c + w * rb + Z * zb) if j % 2 == 0 else (c + w * ra + Z * za, c + u * rb + Z * zb)
            f.add(RoundCone(p, q, rod, rod), k=0.002)
            f.add(RoundCone(c + u * rb + Z * zb, c + w * rb + Z * zb, rod, rod), k=0.002)


def razor_coil(f, a, b, r=0.06, pitch=0.05, rod=0.004):
    """A coil of razor wire from a to b (field f): a helix about the line."""
    a, b = v3(a), v3(b)
    t = unit(b - a)
    L = float(np.linalg.norm(b - a))
    u = unit(np.cross(t, Z)) if abs(t[2]) < 0.9 else v3((1, 0, 0))
    w = np.cross(t, u)
    n = max(8, int(L / pitch * 6))
    pts = [a + t * (L * i / n) + (u * math.cos(2 * math.pi * L * i / n / pitch) + w * math.sin(2 * math.pi * L * i / n / pitch)) * r
           for i in range(n + 1)]
    for i in range(n):
        f.add(RoundCone(pts[i], pts[i + 1], rod, rod), k=0.0)


def pole(f, a, b, r, rb=None, k=0.0, label=0):
    f.add(RoundCone(a, b, r, r if rb is None else rb), k=k, label=label)


def digits(f, c, nrm, s, text, label=9):
    """Paint `text` (digits) in seven-segment strokes on a face at c (its middle; outward normal nrm, horizontal),
    each digit s high."""
    SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
           "8": "abcdefg", "9": "abcfgd"}
    nn = unit(v3((nrm[0], nrm[1], 0.0)))
    side = v3((nn[1], -nn[0], 0.0))                  # (looking at the face, +side runs left to right)
    side = -side
    c = v3(c)
    w, t = s * 0.5, s * 0.09
    n = len(text)
    for i, ch in enumerate(text):
        o = c + side * ((i - (n - 1) / 2) * w * 1.5)
        segs = {"a": (0, s / 2, True), "g": (0, 0, True), "d": (0, -s / 2, True), "f": (-w / 2, s / 4, False),
                "b": (w / 2, s / 4, False), "e": (-w / 2, -s / 4, False), "c": (w / 2, -s / 4, False)}
        for sg in SEG.get(ch, ""):
            dx, dz, horiz = segs[sg]
            q = o + side * dx + Z * dz
            hs = (w / 2, t / 2) if horiz else (t / 2, s / 4)
            half = (abs(side[0]) * hs[0] + abs(nn[0]) * 0.03, abs(side[1]) * hs[0] + abs(nn[1]) * 0.03, hs[1])
            f.paint(RoundBox(q, half, 0.0), label)


# ------------------------------------------------------------------------------------------------ Airbase: scatter
def hesco(seed=0, layout="row"):
    """HESCO bastions: wire-mesh cells lined with tan geotextile, filled with earth (row: three in a line; ell: an L
    of four with one stacked on top)."""
    f, fl = Field("Hesco"), Field("Fill")
    cells = [(-0.38, 0, 0), (0, 0, 0), (0.38, 0, 0)] if layout == "row" else [(-0.19, 0, 0), (0.19, 0, 0), (0.19, 0.38, 0), (0.19, 0, 0.4)]
    for i, (x, y, z) in enumerate(cells):
        hesco_cell(f, (x, y, z), seed=seed + i, fill=fl)
    ground_cut(f, -0.02)
    return [("Hesco", f, fine(0.006, 0.012), "hesco"), ("Fill", fl, fine(0.008, 0.016), "dirt")]


def sandbags(seed=0):
    """A short curved wall of sandbags, three courses, two loose bags slumped at its end."""
    f = Field("Sandbags")
    pts = [v3((math.cos(a) * 1.4 - 1.33, math.sin(a) * 1.4, 0)) for a in np.linspace(-0.45, 0.45, 4)]
    for i in range(3):
        sandbag_run(f, pts[i], pts[i + 1], layers=3, seed=seed + i * 11, rows=2)
    sandbag(f, v3((-0.12, -0.8, 0.04)), 1.1, seed=seed + 90)
    sandbag(f, v3((0.03, -0.92, 0.035)), 0.3, seed=seed + 91)
    ground_cut(f, -0.01)
    return [("Sandbags", f, fine(0.005, 0.01), "sandbag")]


def fuel_drums(seed=0):
    """Fuel drums: a blue one with a white band, an olive one and a red one standing, a fourth lying on timber
    chocks."""
    f, wd = Field("Drums"), Field("Chocks")
    drum(f, (0.0, 0.0, 0.15), label=0)
    f.paint(Cylinder((0.0, 0.0, 0.2), 0.12, 0.05), 9)
    drum(f, (0.22, 0.06, 0.15), label=5)
    drum(f, (0.08, 0.22, 0.15), label=8)
    R = rot_from_axes(z_axis=(math.cos(0.4), math.sin(0.4), 0.0))
    drum(f, (-0.12, -0.32, 0.12), R=R, label=0)
    for t in (-0.1, 0.1):
        q = v3((-0.12, -0.32, 0.03)) + R @ v3((0, 0, t))
        wd.add(RoundBox(q, (0.03, 0.09, 0.03), 0.006, R=Rz(0.4)), k=0.0, label=10)
    ground_cut(f, -0.01)
    return [("Drums", f, fine(0.004, 0.008), "drums"), ("Chocks", wd, fine(0.004, 0.008), "timber")]


def jerrycans(seed=0):
    """Jerrycans: three standing in a row, one tipped against them, one lying."""
    f = Field("Cans")
    for i, x in enumerate((-0.11, 0.0, 0.11)):
        jerrycan(f, (x, 0.0, 0.13), yaw=math.pi / 2 + (i - 1) * 0.05)
    jerrycan(f, (0.25, 0.04, 0.125), yaw=math.pi / 2 + 0.1, tilt=-0.2)
    jerrycan(f, (-0.05, -0.24, 0.045), yaw=0.5, tilt=math.pi / 2)
    ground_cut(f, -0.01)
    return [("Cans", f, fine(0.004, 0.008), "olive")]


def ammo_stack(seed=0):
    """Ammunition: three olive crates stacked (stencilled, rope beckets), ammo cans on and beside them."""
    f = Field("Crates")
    ammo_crate(f, (0.0, 0.0, 0.12), (0.26, 0.15, 0.12), 0.05)
    ammo_crate(f, (0.02, 0.33, 0.12), (0.26, 0.15, 0.12), -0.04)
    ammo_crate(f, (0.02, 0.17, 0.36), (0.26, 0.15, 0.12), 0.1)
    for i, (x, y, z, yaw) in enumerate(((0.45, -0.05, 0.06, 0.3), (0.45, 0.12, 0.06, 0.25), (0.47, 0.03, 0.18, 0.3), (-0.05, 0.18, 0.54, 1.2))):
        ammo_can(f, (x, y, z), yaw, label=0)
    ground_cut(f, -0.01)
    return [("Crates", f, fine(0.004, 0.008), "crate_olive")]


def cones(seed=0):
    """Traffic cones: two standing on their square feet, one knocked over."""
    f = Field("Cones")

    def one(c, R=None):
        R = np.eye(3) if R is None else R
        c = v3(c)
        f.add(RoundBox(c + R @ v3((0, 0, 0.012)), (0.1, 0.1, 0.012), 0.008, R=R), k=0.0, label=6)
        f.add(RoundCone(c + R @ v3((0, 0, 0.02)), c + R @ v3((0, 0, 0.36)), 0.075, 0.014), k=0.006)
        for z in (0.17, 0.27):
            f.paint(Cylinder(c + R @ v3((0, 0, z)), 0.2, 0.045, R=R), 5)
    one((0, 0, 0))
    one((0.32, 0.12, 0))
    one((0.1, -0.3, 0.075), R=rot_from_axes(z_axis=(math.cos(2.4), math.sin(2.4), 0.0)) @ euler(0, 0, 0.3))
    ground_cut(f, -0.01)
    return [("Cones", f, fine(0.004, 0.008), "cone")]


def light_tower(seed=0):
    """A mobile light tower: a small yellow trailer on two wheels with its drawbar and outrigger jacks, the generator
    housing on it, the mast up, four floodlights on its crossbar (lit)."""
    out = []
    bd, ms, tf, hf, hd, gl = Field("Trailer"), Field("Mast"), Field("Tyres"), Field("Hubs"), Field("Heads"), Field("Lights")
    box(bd, (0, 0, 0.32), (0.42, 0.26, 0.16), 0.04)
    for sx in (-1, 1):
        bd.sub(RoundBox((sx * 0.43, 0, 0.32), (0.02, 0.2, 0.1), 0.01), k=0.004)
        for z in (0.27, 0.31, 0.35, 0.39):
            box(bd, (sx * 0.425, 0, z), (0.01, 0.19, 0.008), 0.004, k=0.0, label=7)
    box(bd, (0, 0, 0.17), (0.5, 0.22, 0.03), 0.01, k=0.004, label=7)
    pole(bd, (0.5, 0, 0.17), (0.95, 0, 0.12), 0.025, label=7)
    bd.add(Torus((0.97, 0, 0.12), 0.035, 0.012), k=0.004, label=7)
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = v3((sx * 0.42, sy * 0.36, 0.0))
            pole(bd, q + Z * 0.2, v3((sx * 0.3, sy * 0.2, 0.2)), 0.018, label=7)
            pole(bd, q + Z * 0.2, q + Z * 0.03, 0.018, label=7)
            box(bd, q + Z * 0.012, (0.05, 0.05, 0.012), 0.004, k=0.003, label=7)
    stencil(bd, (0, -0.265, 0.36), (0, -1, 0), 0.3, 0.05, label=7, n=4)
    for sy in (-1, 1):
        wheel(tf, hf, (0, sy * 0.3, 0.13), (0, sy, 0), 0.13, 0.08)
    ground_cut(tf, -0.01)
    ground_cut(bd, -0.01)
    H = 2.15
    ms.add(RoundCone((-0.2, 0, 0.45), (-0.2, 0, H), 0.04, 0.026), k=0.0)
    for z in (0.9, 1.4, 1.85):
        ms.add(Cylinder((-0.2, 0, z), 0.045, 0.03, rr=0.008), k=0.004)
    ms.add(RoundCone((-0.2, -0.45, H), (-0.2, 0.45, H), 0.02, 0.02), k=0.004)
    ms.add(RoundCone((-0.2, 0, H - 0.05), (-0.2, 0, H + 0.05), 0.04, 0.03), k=0.004)
    ms.add(RoundCone((-0.2, 0.0, 0.5), (0.25, 0.0, 0.62), 0.012, 0.012), k=0.004)
    out += [("Trailer", bd, fine(0.005, 0.01), "yellow_paint"), ("Mast", ms, fine(0.004, 0.008), "galv"),
            ("Tyres", tf, fine(0.004, 0.008), "rubber"), ("Hubs", hf, fine(0.004, 0.008), "galv")]
    for y in (-0.36, -0.12, 0.12, 0.36):
        flood_head(hd, gl, (-0.2, y, H + 0.1), (0.0, -0.55, -0.6), s=1.1)
    out += [("Heads", hd, fine(0.004, 0.008), "steel"), ("Lights", gl, fine(0.004, 0.008), "glow_flood")]
    return out


def chainlink(seed=0, L=1.6):
    """A section of chain-link fence: galvanised posts and top rail, the mesh (painted), outriggers leaning out with
    three strands of barbed wire and a coil of razor wire along the top."""
    ps, ms, wr = Field("Posts"), Field("Mesh"), Field("Wire")
    H = 0.95
    for x in (-L / 2, 0.0, L / 2):
        pole(ps, (x, 0, -0.05), (x, 0, H), 0.022)
        ps.add(Sphere((x, 0, H), 0.026), k=0.006)
        pole(ps, (x, 0, H - 0.02), (x, -0.2, H + 0.18), 0.012)
        ps.add(Cylinder((x, 0, 0.0), 0.06, 0.06, rr=0.01), k=0.01, label=5)
    pole(ps, (-L / 2, 0, H - 0.04), (L / 2, 0, H - 0.04), 0.014)
    pole(ps, (-L / 2, 0, 0.08), (L / 2, 0, 0.08), 0.007)
    ms.add(RoundBox((0, 0, 0.5), (L / 2, 0.004, 0.42), 0.002), k=0.0)
    for t in (0.33, 0.66, 1.0):
        q0, q1 = v3((-L / 2, -0.2 * t, H - 0.02 + 0.2 * t)), v3((L / 2, -0.2 * t, H - 0.02 + 0.2 * t))
        pole(wr, q0, q1, 0.0035)
    razor_coil(wr, (-L / 2, -0.06, H + 0.12), (L / 2, -0.06, H + 0.12), r=0.07, pitch=0.07, rod=0.0045)
    ground_cut(ps, -0.03)
    return [("Posts", ps, fine(0.004, 0.008), "galv"), ("Mesh", ms, fine(0.004, 0.008), "chainlink"), ("Wire", wr, fine(0.0035, 0.007), "galv")]


def jersey(f, c, L=0.9, yaw=0.0, stripes=False):
    """A concrete jersey barrier (field f), L long, centred at c: the sloped profile, lifting slots, hazard stripes."""
    R = Rz(yaw)
    c = v3(c)
    prof = [((0, 0.11, 0), (0, 1, 0.12)), ((0, -0.11, 0), (0, -1, 0.12)), ((0, 0.07, 0.12), (0, 1, 0.55)), ((0, -0.07, 0.12), (0, -1, 0.55)),
            ((0, 0, 0.32), (0, 0, 1)), ((0, 0, -0.02), (0, 0, -1)), ((L / 2, 0, 0), (1, 0, 0)), ((-L / 2, 0, 0), (-1, 0, 0))]
    planes = [(c + R @ v3(p), R @ v3(n)) for p, n in prof]
    lo, hi = c - v3((L, L, 0.1)), c + v3((L, L, 0.45))
    f.add(convex_w(planes, lo, hi, 0.004, 6.0, int(abs(c[0]) * 100)), k=0.0)
    for t in (-0.3, 0.3):
        f.sub(RoundBox(c + R @ v3((t * L, 0, 0.03)), (0.06, 0.2, 0.03), 0.008, R=R), k=0.004)
    if stripes:
        f.paint(RoundBox(c + R @ v3((0, 0, 0.16)), (L / 2 + 0.05, 0.2, 0.06), 0.0, R=R), 8)


def barriers(seed=0):
    """Two jersey barriers end to end, the second skewed, one striped yellow and black."""
    f = Field("Barriers")
    jersey(f, (-0.47, 0, 0), 0.9, 0.0, stripes=True)
    jersey(f, (0.47, 0.08, 0), 0.9, 0.18)
    ground_cut(f, -0.02)
    return [("Barriers", f, fine(0.006, 0.012), "concrete")]


def humvee(seed=0, paint="olive", wreck=False):
    """A Humvee: a broad, low, boxy utility vehicle in olive drab, its flat bonnet with the grille slots, a small square
    cab, a roof hatch ring, a whip antenna, a spare wheel and jerrycans on the tailgate (wreck: burnt out, no glass,
    sat on its rims)."""
    out = []
    car(out, L=1.5, W=0.8, H=0.62, rw=0.16, paint=paint, seed=seed, kind="suv", hubs=paint)
    if wreck:
        out = [(n, f, vxs, {"glass": "dark"}.get(m, m)) for (n, f, vxs, m) in out if n not in ("Tyres",)]
    kt = Field("Kit")
    bd = next(f for (n, f, _, _) in out if n == "Body")
    for i in range(5):                                              # grille slots
        bd.sub(RoundBox((0.755, -0.16 + i * 0.08, 0.36), (0.02, 0.012, 0.06), 0.004), k=0.0)
    bd.add(Torus((-0.15, 0.0, 0.625), 0.13, 0.025), k=0.004, label=7)
    if not wreck:
        pole(kt, (-0.62, 0.32, 0.6), (-0.66, 0.36, 1.45), 0.006)
        jerrycan(kt, (-0.77, -0.25, 0.42), yaw=0.0, s=0.9)
        jerrycan(kt, (-0.77, 0.25, 0.42), yaw=0.0, s=0.9)
        out.append(("Kit", kt, fine(0.004, 0.008), paint))
        tf2, hf2 = Field("Spare"), Field("SpareHub")
        wheel(tf2, hf2, (-0.79, 0, 0.42), (-1, 0, 0), 0.15, 0.09)
        out += [("Spare", tf2, fine(0.005, 0.01), "rubber"), ("SpareHub", hf2, fine(0.004, 0.008), paint)]
    return out


def dry_scrub(seed=0, w=0.8):
    return scrub(w, w * 0.45, seed, mat="scrub")


# ------------------------------------------------------------------------------------------------ Airbase: landmarks
def jet(seed=0, keep_x=None, chocks=True, ladder=True):
    """A fighter jet parked on its gear (nose toward +X): a long fuselage with a pointed nose and a pitot probe, the
    bubble canopy (gold-tinted), a cranked delta wing with missiles on the wingtip rails and drop tanks under it, the
    tailplanes and one tall fin with the task force's red-and-white flash, side intakes with red warning streamers,
    the nozzle; two-tone grey camouflage, chocks under the wheels, a yellow boarding ladder (keep_x: only what lies at
    x > keep_x, as when it noses out of a hangar)."""
    out = []
    bd, cn, gr, tf, hf, dk, ms = (Field(n) for n in ("Fuselage", "Canopy", "Gear", "Tyres", "Hubs", "Nozzle", "Missiles"))
    zc = 0.55
    prof = [(1.62, 0.006), (1.45, 0.05), (1.2, 0.1), (0.9, 0.15), (0.5, 0.19), (0.0, 0.21), (-0.6, 0.21), (-1.2, 0.19), (-1.55, 0.15)]
    bd.add(Chain([v3((x, 0, zc + (0.02 if x > 0.6 else 0.0))) for x, _ in prof], [r for _, r in prof], k=0.05), k=0.0)
    bd.add(Ellipsoid((0.3, 0, zc - 0.05), (0.9, 0.26, 0.16)), k=0.08)               # the belly and chines
    pole(bd, (1.6, 0, zc + 0.006), (1.85, 0, zc + 0.006), 0.008, k=0.01, label=6)
    wing = [(0.5, 0.0), (0.2, 0.3), (-0.55, 1.12), (-0.88, 1.12), (-0.95, 0.0)]
    bd.add(leaf((0, 0, zc - 0.02), (1, 0, 0), (0, 1, 0), [(a, b) for a, b in wing] + [(a, -b) for a, b in reversed(wing[1:-1])], 0.022), k=0.03)
    tail = [(-1.05, 0.0), (-1.3, 0.62), (-1.55, 0.62), (-1.58, 0.0)]
    bd.add(leaf((0, 0, zc), (1, 0, 0), (0, 1, 0), [(a, b) for a, b in tail] + [(a, -b) for a, b in reversed(tail[1:-1])], 0.016), k=0.02)
    fin = [(-0.85, 0.0), (-1.38, 0.78), (-1.6, 0.78), (-1.62, 0.0)]
    bd.add(leaf((0, 0, zc + 0.12), (1, 0, 0), (0, 0, 1), fin, 0.018), k=0.03)
    for sy in (-1, 1):                                              # intakes
        q = v3((0.25, sy * 0.21, zc - 0.03))
        bd.add(RoundBox(q, (0.4, 0.07, 0.1), 0.04), k=0.04)
        bd.sub(RoundBox(q + v3((0.42, 0, 0)), (0.08, 0.045, 0.07), 0.02), k=0.01)
        dk.add(RoundBox(q + v3((0.34, 0, 0)), (0.012, 0.05, 0.075), 0.01), k=0.0)
        bd.add(leaf(q + v3((0.6, 0.0, -0.06)), (0, 0, -1), (1, 0, 0), [(0.0, -0.012), (0.18, -0.01), (0.2, 0.01), (0.0, 0.012)], 0.004,
                    wave=(0.01, 30.0)), k=0.0, label=8)
    dk.add(Cylinder((-1.6, 0, zc), 0.13, 0.06, R=RX), k=0.0)
    bd.add(Cylinder((-1.58, 0, zc), 0.15, 0.08, rr=0.02, R=RX), k=0.01, label=7)
    bd.sub(Cylinder((-1.64, 0, zc), 0.12, 0.08, R=RX), k=0.006)
    cn.add(Ellipsoid((0.88, 0, zc + 0.15), (0.38, 0.115, 0.12)), k=0.0)
    cn.inter(Plane((0, 0, zc + 0.08), (0, 0, -1)))
    bd.add(RoundBox((0.88, 0, zc + 0.1), (0.4, 0.13, 0.02), 0.015), k=0.02, label=7)
    # paint: the camouflage's darker patches on top, the fin flash, a white serial
    rng = np.random.default_rng(seed + 5)
    for i in range(9):
        q = v3((rng.uniform(-1.3, 1.1), rng.uniform(-0.9, 0.9), zc + 0.2))
        bd.paint(Ellipsoid(q, (rng.uniform(0.18, 0.3), rng.uniform(0.12, 0.22), 0.4), R=Rz(rng.uniform(0, 3))), 5)
    for sy in (-1, 1):
        bd.paint(RoundBox((-1.38, sy * 0.02, zc + 0.6), (0.11, 0.05, 0.05), 0.0), 9)
        bd.paint(RoundBox((-1.38, sy * 0.02, zc + 0.6), (0.11, 0.05, 0.018), 0.0), 8)
        digits(bd, (-0.95, sy * 0.2, zc + 0.03), (0, sy, 0), 0.08, "07", label=9)
    # missiles on the wingtip rails, drop tanks
    for sy in (-1, 1):
        y = sy * 1.13
        pole(ms, (-0.85, y, zc - 0.02), (-0.25, y, zc - 0.02), 0.022)
        ms.add(RoundCone((-0.25, y, zc - 0.02), (-0.18, y, zc - 0.02), 0.022, 0.004), k=0.01, label=8)
        for t in (0.0, 1.5708):
            Rf = euler(t, 0, 0)
            ms.add(leaf(v3((-0.8, y, zc - 0.02)), (1, 0, 0), Rf @ v3((0, 1, 0)), [(-0.05, -0.06), (0.06, 0.0), (-0.05, 0.06)], 0.004), k=0.0)
        ms.add(Ellipsoid((-0.15, sy * 0.62, zc - 0.17), (0.34, 0.07, 0.07)), k=0.0)
        pole(ms, (-0.15, sy * 0.62, zc - 0.12), (-0.15, sy * 0.62, zc - 0.03), 0.015, k=0.01)
    # gear: the nose leg and the two mains, gear doors; chocks
    legs = [(1.0, 0.0, 0.07), (-0.3, 0.32, 0.085), (-0.3, -0.32, 0.085)]
    for (x, y, r) in legs:
        pole(gr, (x, y, zc - 0.12), (x, y, r), 0.018)
        gr.add(RoundBox((x + 0.03, y + (0.06 if y > 0 else -0.06 if y < 0 else 0.0), zc - 0.2), (0.12, 0.006, 0.08), 0.006), k=0.0)
        wheel(tf, hf, (x, y, r), (0, 1 if y >= 0 else -1, 0), r, 0.06, hub=0.6)
    ground_cut(tf, -0.01)
    parts = [("Fuselage", bd, fine(0.006, 0.012), "jet"), ("Canopy", cn, fine(0.005, 0.01), "canopy"), ("Gear", gr, fine(0.004, 0.008), "steel"),
             ("Tyres", tf, fine(0.004, 0.008), "rubber"), ("Hubs", hf, fine(0.004, 0.008), "steel"), ("Nozzle", dk, fine(0.005, 0.01), "dark"),
             ("Missiles", ms, fine(0.004, 0.008), "jet")]
    if chocks:
        ch = Field("Chocks")
        for (x, y, r) in legs:
            for sx in (-1, 1):
                ch.add(convex([((x + sx * (r + 0.005), y, 0), (sx, 0, 0)), ((x + sx * (r + 0.08), y, 0), (sx * 0.6, 0, 1)),
                               ((x, y + 0.06, 0), (0, 1, 0)), ((x, y - 0.06, 0), (0, -1, 0)), ((x, y, 0.0), (0, 0, -1))],
                              (x - 0.3, y - 0.2, -0.1), (x + 0.3, y + 0.2, 0.2)), k=0.0)
        parts.append(("Chocks", ch, fine(0.004, 0.008), "yellow_paint"))
    if ladder:
        ld = Field("Ladder")
        top, foot = v3((0.92, -0.17, zc + 0.12)), v3((0.82, -0.55, 0.0))
        for dx in (-0.08, 0.08):
            pole(ld, foot + v3((dx, 0, 0)), top + v3((dx, 0, 0)), 0.01)
        for t in np.linspace(0.12, 0.88, 5):
            q = foot + (top - foot) * t
            pole(ld, q - v3((0.08, 0, 0)), q + v3((0.08, 0, 0)), 0.008)
        parts.append(("Ladder", ld, fine(0.004, 0.008), "yellow_paint"))
    if keep_x is not None:
        kept = []
        for (n, f, vxs, m) in parts:
            lo, hi = f.bounds()
            if hi[0] < keep_x:
                continue
            f.inter(Plane((keep_x, 0, 0), (-1, 0, 0)))
            kept.append((n, f, vxs, m))
        parts = kept
    return parts


CORR = 0.008


def hangar(seed=0):
    """An arched hangar of corrugated steel (front toward -Y): the barrel vault on its ribs, a portal frame across its
    front with the door leaves slid back into their pockets, the dark hall inside lit by hanging lamps, a jet nosing
    out of it onto the concrete apron with its yellow lead-in line; roof vents, the hangar's number on the header."""
    out = []
    HW, HH, HD = 2.1, 1.9, 1.6
    vt = Field("Vault")

    def vault(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        e = np.sqrt((x / F32(HW)) ** 2 + (z / F32(HH)) ** 2)
        a = np.arctan2(z / F32(HH), x / F32(HW))
        corr = F32(CORR) * np.cos(a * F32(150))
        d = (e - F32(1.0)) * F32(min(HW, HH)) + corr
        return np.maximum.reduce([d, np.abs(y) - F32(HD), -z]).astype(F32)
    vt.add(Func(vault, (-HW - 0.1, -HD - 0.1, -0.1), (HW + 0.1, HD + 0.1, HH + 0.1)), k=0.0)
    rb = Field("Ribs")                                              # (the ribs a mesh of their own: merged into the corrugated
    for y in np.linspace(-HD + 0.05, HD - 0.05, 6):                 # vault they left slivers the decimation could not collapse)
        def rib(P, y=y):
            e = np.sqrt((P[:, 0] / F32(HW + 0.03)) ** 2 + (P[:, 2] / F32(HH + 0.03)) ** 2)
            return np.maximum.reduce([np.abs(e - F32(1.0)) * F32(min(HW, HH)) - F32(0.025), np.abs(P[:, 1] - F32(y)) - F32(0.04), -P[:, 2]]).astype(F32)
        rb.add(Func(rib, (-HW - 0.2, y - 0.1, -0.1), (HW + 0.2, y + 0.1, HH + 0.2)), k=0.0, label=7)
    for x in (-0.9, 0.0, 0.9):                                      # roof vents
        z = HH * math.sqrt(max(0.0, 1 - (x / HW) ** 2))
        for y in (-0.6, 0.6):
            vt.add(Cylinder((x, y, z + 0.06), 0.07, 0.16, rr=0.02), k=0.02, label=6)
            vt.add(Cylinder((x, y, z + 0.16), 0.1, 0.03, rr=0.01), k=0.004, label=6)
    # the door opening (a deep recess) and the portal frame with its door pockets
    DW, DH = 1.32, 1.42
    vt.sub(RoundBox((0, -HD + 0.3, DH / 2 - 0.05), (DW, 0.6, DH / 2 + 0.05), 0.01), k=0.0)
    ground_cut(vt, -0.03)
    rb.sub(RoundBox((0, -HD + 0.3, DH / 2 - 0.05), (DW, 0.6, DH / 2 + 0.05), 0.01), k=0.0)
    ground_cut(rb, -0.03)
    out += [("Vault", vt, fine(0.012, 0.024), "hangar"), ("Ribs", rb, fine(0.008, 0.016), "hangar")]
    pf = Field("Portal")
    for sx in (-1, 1):
        box(pf, (sx * 1.75, -HD - 0.04, 0.8), (0.42, 0.1, 0.82), 0.02)
        for k in range(5):
            box(pf, (sx * (1.4 + k * 0.17), -HD - 0.145, 0.8), (0.012, 0.008, 0.78), 0.004, k=0.002, label=7)
    box(pf, (0, -HD - 0.04, DH + 0.12), (2.17, 0.11, 0.12), 0.02, k=0.004, label=7)
    digits(pf, (0, -HD - 0.15, DH + 0.12), (0, -1, 0), 0.16, "2", label=9)
    for sx in (-1, 1):
        box(pf, (sx * 0.9, -HD - 0.18, DH + 0.02), (0.06, 0.05, 0.03), 0.01, k=0.004, label=6)
    ground_cut(pf, -0.03)
    out.append(("Portal", pf, fine(0.008, 0.016), "hangar"))
    dk, lt = Field("Hall"), Field("HallLights")
    box(dk, (0, -HD + 0.88, DH / 2), (DW, 0.02, DH / 2), 0.0)
    box(dk, (0, -HD + 0.3, DH - 0.03), (DW, 0.58, 0.02), 0.0)
    for x in (-0.8, 0.0, 0.8):
        lt.add(Ellipsoid((x, -HD + 0.45, DH - 0.12), (0.12, 0.08, 0.04)), k=0.0)
    for sx in (-1, 1):
        lt.add(RoundBox((sx * 0.9, -HD - 0.235, DH + 0.0), (0.05, 0.006, 0.02), 0.004), k=0.0)
    out += [("Hall", dk, fine(0.01, 0.02), "dark"), ("HallLights", lt, fine(0.005, 0.01), "glow_flood")]
    ap = Field("Apron")
    box(ap, (0, -HD - 0.7, 0.0), (2.3, 0.72, 0.035), 0.02)
    ap.paint(RoundBox((0, -HD - 0.7, 0.03), (0.035, 0.8, 0.05), 0.0), 5)
    for x in (-1.15, 1.15):
        ap.paint(RoundBox((x, -HD - 0.7, 0.03), (0.006, 0.8, 0.05), 0.0), 7)
    ground_cut(ap, -0.03)
    out.append(("Apron", ap, fine(0.012, 0.024), "concrete"))
    # the jet (scaled 0.8) turned nose toward -Y from y0: what lies deeper in the hall than its back wall is left out
    S, y0 = 0.8, -HD + 0.05
    js = jet(seed + 3, keep_x=-((-HD + 0.86) - y0) / S, chocks=True, ladder=False)
    sc = []
    for (n, f, vxs, m) in js:
        g = Field(n)
        for kind, prim, kk, lab in f.ops:
            g.ops.append((kind, Scaled(prim, S), kk * S, lab))
        sc.append(("Jet" + n, g, vxs * 0.85, m))
    place_parts(out, sc, (0, y0, 0.0), Rz(-math.pi / 2))
    return out


class Scaled:
    """A primitive scaled by s about the origin (distances scale with it)."""
    def __init__(self, prim, s):
        self.p, self.s = prim, s
        self.lo = v3(prim.lo) * s
        self.hi = v3(prim.hi) * s

    def __call__(self, P):
        return (self.p((P / F32(self.s)).astype(F32)) * F32(self.s)).astype(F32)


def control_tower(seed=0):
    """The control tower (front toward -Y): a low operations block with strip windows, a square concrete shaft with a
    slot of windows, the glass cab on top (its panes leaning out under a deep roof), a catwalk round it with a rail,
    antennas and a red warning beacon; a windsock on its mast beside it."""
    out = []
    cb, gl, st, dk = Field("Concrete"), Field("Glass"), Field("Steel"), Field("Dark")
    box(cb, (0.0, 0.0, 0.5), (0.95, 0.65, 0.52), 0.02)
    box(cb, (0.0, 0.0, 1.04), (1.0, 0.7, 0.04), 0.01, k=0.004, label=7)
    for sy in (-1, 1):
        gl.add(RoundBox((0, sy * 0.652, 0.62), (0.8, 0.008, 0.12), 0.004), k=0.0)
        cb.sub(RoundBox((0, sy * 0.66, 0.62), (0.8, 0.02, 0.12), 0.006), k=0.0)
    gl.add(RoundBox((0.952, 0, 0.62), (0.008, 0.5, 0.12), 0.004), k=0.0)
    cb.sub(RoundBox((0.96, 0, 0.62), (0.02, 0.5, 0.12), 0.006), k=0.0)
    cb.sub(RoundBox((-0.45, -0.66, 0.25), (0.14, 0.03, 0.25), 0.006), k=0.0)
    dk.add(RoundBox((-0.45, -0.635, 0.25), (0.14, 0.006, 0.25), 0.0), k=0.0)
    box(cb, (-0.45, -0.72, 0.53), (0.22, 0.1, 0.02), 0.01, k=0.004, label=7)
    sx0, H0, H1 = 0.35, 1.05, 3.05
    box(cb, (sx0, 0.05, (H0 + H1) / 2), (0.3, 0.3, (H1 - H0) / 2), 0.02)
    gl.add(RoundBox((sx0, -0.252, (H0 + H1) / 2 + 0.1), (0.06, 0.006, 0.75), 0.003), k=0.0)
    cb.sub(RoundBox((sx0, -0.26, (H0 + H1) / 2 + 0.1), (0.06, 0.02, 0.75), 0.004), k=0.0)
    box(cb, (sx0, 0.05, H1 - 0.02), (0.75, 0.75, 0.05), 0.02, k=0.004)
    # the cab: eight leaning panes
    R0, ZC0, ZC1 = 0.62, 3.05, 3.55
    planes = [((sx0, 0.05, ZC1), (0, 0, 1)), ((sx0, 0.05, ZC0), (0, 0, -1))]
    for i in range(8):
        a = 2 * math.pi * i / 8 + math.pi / 8
        n = v3((math.cos(a), math.sin(a), -0.28))
        planes.append((v3((sx0 + math.cos(a) * R0, 0.05 + math.sin(a) * R0, ZC0)), n))
    gl.add(convex(planes, (sx0 - 1, -1, ZC0 - 0.1), (sx0 + 1, 1.1, ZC1 + 0.1)), k=0.0)
    for i in range(8):
        a = 2 * math.pi * i / 8
        rr = R0 / math.cos(math.pi / 8)
        p0 = v3((sx0 + math.cos(a) * rr, 0.05 + math.sin(a) * rr, ZC0))
        p1 = v3((sx0 + math.cos(a) * (rr + 0.14), 0.05 + math.sin(a) * (rr + 0.14), ZC1))
        pole(st, p0, p1, 0.016)
    box(cb, (sx0, 0.05, ZC0 + 0.05), (0.62, 0.62, 0.06), 0.03, k=0.0, label=7)
    roofp = [((sx0, 0.05, ZC1 + 0.1), (0, 0, 1)), ((sx0, 0.05, ZC1 - 0.02), (0, 0, -1))]
    for i in range(8):
        a = 2 * math.pi * i / 8 + math.pi / 8
        roofp.append((v3((sx0 + math.cos(a) * (R0 + 0.28), 0.05 + math.sin(a) * (R0 + 0.28), ZC1)), v3((math.cos(a), math.sin(a), 0.4))))
    cb.add(convex(roofp, (sx0 - 1.2, -1.2, ZC1 - 0.1), (sx0 + 1.2, 1.3, ZC1 + 0.2)), k=0.0)
    # the catwalk's rail
    for i in range(16):
        a = 2 * math.pi * i / 16
        pole(st, (sx0 + math.cos(a) * 0.74, 0.05 + math.sin(a) * 0.74, ZC0 - 0.02), (sx0 + math.cos(a) * 0.74, 0.05 + math.sin(a) * 0.74, ZC0 + 0.22), 0.008)
    st.add(Torus((sx0, 0.05, ZC0 + 0.22), 0.74, 0.01), k=0.004)
    st.add(Torus((sx0, 0.05, ZC0 + 0.11), 0.74, 0.007), k=0.004)
    # antennas, the beacon
    pole(st, (sx0 + 0.2, 0.25, ZC1 + 0.1), (sx0 + 0.2, 0.25, ZC1 + 0.85), 0.012)
    pole(st, (sx0 - 0.25, 0.0, ZC1 + 0.1), (sx0 - 0.25, 0.0, ZC1 + 0.55), 0.008)
    st.add(Cylinder((sx0 - 0.1, 0.3, ZC1 + 0.2), 0.12, 0.05, rr=0.01, R=rot_from_axes(z_axis=(0.3, -0.5, 0.8))), k=0.0)
    bc = Field("Beacon")
    bc.add(Sphere((sx0 + 0.2, 0.25, ZC1 + 0.88), 0.04), k=0.0)
    box(cb, (-0.4, 0.2, 1.14), (0.18, 0.15, 0.08), 0.02, k=0.004, label=6)
    ground_cut(cb, -0.03)
    out += [("Concrete", cb, fine(0.01, 0.02), "concrete"), ("Glass", gl, fine(0.006, 0.012), "glass"), ("Steel", st, fine(0.004, 0.008), "galv"),
            ("Dark", dk, fine(0.006, 0.012), "dark"), ("Beacon", bc, fine(0.004, 0.008), "glow_red")]
    # the windsock on its mast beside the tower
    ws, sk = Field("SockMast"), Field("Sock")
    m0 = v3((-1.25, -0.3, 0.0))
    pole(ws, m0 - Z * 0.03, m0 + Z * 1.5, 0.014)
    ws.add(Torus(m0 + Z * 1.5 + v3((0.08, 0, 0)), 0.07, 0.008, R=RX), k=0.004)
    d = unit(v3((0.85, -0.3, -0.18)))
    Rsf = rot_from_axes(z_axis=d).astype(F32)
    sc0 = m0 + Z * 1.5 + v3((0.08, 0, 0))

    def sock(P):
        Q = (P - F32(sc0)) @ Rsf
        rad = F32(0.07) - Q[:, 2] * F32(0.05)
        return np.maximum.reduce([np.abs(np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2) - rad) - F32(0.008), -Q[:, 2], Q[:, 2] - F32(0.5)]).astype(F32)
    sk.add(Func(sock, sc0 - 0.7, sc0 + 0.7), k=0.0)
    for t in (0.1, 0.3):
        sk.paint(Func(lambda P, t=t: (np.abs(((P - F32(sc0)) @ Rsf)[:, 2] - F32(t + 0.05)) - F32(0.05)).astype(F32), sc0 - 0.7, sc0 + 0.7), 5)
    ground_cut(ws, -0.03)
    out += [("SockMast", ws, fine(0.004, 0.008), "galv"), ("Sock", sk, fine(0.004, 0.008), "cone")]
    return out


def helipad(seed=0, pad=True):
    """A helicopter on its pad: the concrete disc with its yellow ring, the white H and edge lights; a twin-engined
    utility helicopter in olive drab (nose toward +X) on its wheels, the cabin door slid open, four drooping main rotor
    blades, the tail boom with its fin, stabilator and tail rotor."""
    out = []
    pd, pl = Field("Pad"), Field("PadLights")
    pd.add(Cylinder((0, 0, 0.0), 1.32, 0.07, rr=0.02), k=0.0)
    pd.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(1.12)) - F32(0.06)).astype(F32), (-1.4, -1.4, -0.1), (1.4, 1.4, 0.1)), 5)
    for (c, h) in (((-0.3, 0, 0.03), (0.06, 0.4, 0.05)), ((0.3, 0, 0.03), (0.06, 0.4, 0.05)), ((0, 0, 0.03), (0.3, 0.06, 0.05))):
        pd.paint(RoundBox(c, h, 0.0), 6)
    for i in range(10):
        a = 2 * math.pi * i / 10
        pl.add(Sphere((math.cos(a) * 1.27, math.sin(a) * 1.27, 0.04), 0.03), k=0.0)
    ground_cut(pd, -0.03)
    if pad:
        out += [("Pad", pd, fine(0.01, 0.02), "concrete"), ("PadLights", pl, fine(0.004, 0.008), "glow_lamp")]
    bd, gl, rt, tf, hf, dk = (Field(n) for n in ("Heli", "HeliGlass", "Rotor", "HeliTyres", "HeliHubs", "Door"))
    zc = 0.5
    box(bd, (0.15, 0, zc), (0.55, 0.28, 0.24), 0.13)
    bd.add(Ellipsoid((0.68, 0, zc - 0.03), (0.32, 0.26, 0.21)), k=0.08)
    bd.add(RoundCone((-0.3, 0, zc + 0.08), (-1.5, 0, zc + 0.24), 0.17, 0.055), k=0.1)
    box(bd, (0.08, 0, zc + 0.3), (0.45, 0.2, 0.09), 0.06, k=0.05)
    for sy in (-1, 1):
        bd.add(RoundCone((0.38, sy * 0.16, zc + 0.32), (0.62, sy * 0.16, zc + 0.3), 0.07, 0.06), k=0.02)
        dk.add(RoundBox((0.6, sy * 0.21, zc + 0.31), (0.035, 0.035, 0.04), 0.02), k=0.0)
    gl.add(Ellipsoid((0.75, 0, zc + 0.08), (0.27, 0.24, 0.17)), k=0.0)
    gl.inter(Plane((0.55, 0, 0), (-1, 0, 0)))
    gl.inter(Plane((0, 0, zc - 0.02), (0, 0, -1)))
    for sy in (-1, 1):
        gl.add(RoundBox((0.32, sy * 0.275, zc + 0.08), (0.08, 0.008, 0.07), 0.02), k=0.0)
        dk.add(RoundBox((0.0, sy * 0.28, zc - 0.02), (0.2, 0.008, 0.19), 0.01), k=0.0)
    pole(bd, (0.92, 0, zc + 0.12), (0.62, 0, zc + 0.24), 0.012, k=0.004, label=7)
    fin = [(0.0, 0.0), (-0.1, 0.48), (-0.24, 0.5), (-0.22, 0.0)]
    bd.add(leaf((-1.42, 0, zc + 0.2), (1, 0, 0), (0, 0, 1), fin, 0.02), k=0.03)
    bd.add(leaf((-1.42, 0, zc + 0.22), (1, 0, 0), (0, 1, 0), [(0.0, 0.0), (-0.06, 0.3), (-0.18, 0.3), (-0.2, 0.0), (-0.18, -0.3), (-0.06, -0.3)], 0.012), k=0.02)
    for sy in (-1, 1):
        digits(bd, (-0.95, sy * 0.105, zc + 0.17), (0, sy, 0), 0.07, "24", label=9)
    # rotor: mast, hub, four drooping blades; tail rotor
    pole(rt, (0.05, 0, zc + 0.38), (0.05, 0, zc + 0.56), 0.04)
    rt.add(Cylinder((0.05, 0, zc + 0.55), 0.09, 0.05, rr=0.015), k=0.01)
    for i in range(4):
        a = 2 * math.pi * i / 4 + 0.35
        d = v3((math.cos(a), math.sin(a), 0.0))
        nrm = v3((-math.sin(a), math.cos(a), 0.0))
        Rb = np.stack([d, nrm, Z], axis=1) @ euler(0.06, -0.03, 0)
        rt.add(RoundBox(v3((0.05, 0, zc + 0.55)) + d * 0.72 - Z * 0.03, (0.68, 0.05, 0.008), 0.006, R=Rb), k=0.01)
    for i in range(4):
        a = 2 * math.pi * i / 4 + 0.6
        d = v3((math.cos(a), 0.0, math.sin(a)))
        rt.add(RoundBox(v3((-1.55, 0.1, zc + 0.52)) + d * 0.17, (0.17, 0.006, 0.025), 0.005, R=np.stack([d, v3((0, 1, 0)), np.cross(d, v3((0, 1, 0)))], axis=1)), k=0.004)
    rt.add(Sphere((-1.55, 0.1, zc + 0.52), 0.03), k=0.006)
    # gear
    for sy in (-1, 1):
        pole(bd, (0.15, sy * 0.25, zc - 0.15), (0.15, sy * 0.4, 0.1), 0.022, k=0.01, label=7)
        wheel(tf, hf, (0.15, sy * 0.42, 0.1), (0, sy, 0), 0.1, 0.07)
    pole(bd, (-1.25, 0, zc + 0.05), (-1.25, 0, 0.06), 0.012, k=0.01, label=7)
    wheel(tf, hf, (-1.25, 0.0, 0.055), (0, 1, 0), 0.055, 0.04)
    ground_cut(tf, -0.01)
    heli = [("Heli", bd, fine(0.006, 0.012), "olive"), ("HeliGlass", gl, fine(0.005, 0.01), "glass"), ("Rotor", rt, fine(0.004, 0.008), "gunmetal"),
            ("HeliTyres", tf, fine(0.004, 0.008), "rubber"), ("HeliHubs", hf, fine(0.004, 0.008), "steel"), ("Door", dk, fine(0.005, 0.01), "dark")]
    place_parts(out, heli, (0.05, 0, 0.035) if pad else (0.25, 0, 0.0), Rz(0.5) if pad else None)
    return out


def fuel_truck(seed=0):
    """A fuel bowser (nose toward +X): an olive cab-over cab, the oval tank on the chassis with its bands, a walkway
    and rail along its top, filler domes, the hose cabinet and reel at the back, a red flammable placard and white
    stencils; six wheels."""
    out = []
    bd, gl, tf, hf, tk, hs = (Field(n) for n in ("Cab", "Glass", "Tyres", "Hubs", "Tank", "Hose"))
    box(bd, (0.95, 0, 0.55), (0.25, 0.36, 0.33), 0.06)
    bd.sub(RoundBox((1.2, 0, 0.72), (0.03, 0.3, 0.12), 0.02), k=0.0)
    gl.add(RoundBox((1.185, 0, 0.72), (0.012, 0.3, 0.12), 0.01), k=0.0)
    for sy in (-1, 1):
        bd.sub(RoundBox((1.02, sy * 0.37, 0.72), (0.13, 0.03, 0.1), 0.02), k=0.0)
        gl.add(RoundBox((1.02, sy * 0.355, 0.72), (0.13, 0.008, 0.1), 0.01), k=0.0)
        box(bd, (1.22, sy * 0.39, 0.66), (0.02, 0.03, 0.06), 0.008, k=0.004, label=7)
    box(bd, (1.21, 0, 0.36), (0.03, 0.3, 0.07), 0.01, k=0.004, label=7)
    box(bd, (1.23, 0, 0.18), (0.03, 0.38, 0.05), 0.015, k=0.004, label=7)
    box(bd, (0.0, 0, 0.27), (1.15, 0.2, 0.05), 0.01, k=0.004, label=7)
    for sy in (-1, 1):                                              # mudguards
        for x in (0.95, -0.4, -0.75):
            box(bd, (x, sy * 0.33, 0.33), (0.17, 0.07, 0.015), 0.006, k=0.004, label=7)
    zt = 0.66
    tk.add(Func(lambda P: (np.maximum(np.sqrt((P[:, 1] / F32(0.36)) ** 2 + ((P[:, 2] - F32(zt)) / F32(0.3)) ** 2) * F32(0.3) - F32(0.3),
                                      np.abs(P[:, 0] + F32(0.18)) - F32(0.82))).astype(F32), (-1.1, -0.45, 0.3), (0.75, 0.45, 1.05)), k=0.0)
    tk.add(Ellipsoid((0.64, 0, zt), (0.05, 0.36, 0.3)), k=0.03)
    tk.add(Ellipsoid((-1.0, 0, zt), (0.05, 0.36, 0.3)), k=0.03)
    for x in (-0.7, -0.18, 0.34):
        tk.add(Func(lambda P, x=x: (np.maximum(np.sqrt((P[:, 1] / F32(0.375)) ** 2 + ((P[:, 2] - F32(zt)) / F32(0.315)) ** 2) * F32(0.31) - F32(0.31),
                                               np.abs(P[:, 0] - F32(x)) - F32(0.025))).astype(F32), (x - 0.1, -0.45, 0.3), (x + 0.1, 0.45, 1.05)), k=0.004, label=7)
    for x in (-0.6, 0.2):
        tk.add(Cylinder((x, 0, zt + 0.32), 0.08, 0.06, rr=0.015), k=0.01, label=6)
    for sy in (-1, 1):
        pole(tk, (-0.95, sy * 0.15, zt + 0.42), (0.55, sy * 0.15, zt + 0.42), 0.01, label=6)
        for x in (-0.9, -0.2, 0.5):
            pole(tk, (x, sy * 0.15, zt + 0.29), (x, sy * 0.15, zt + 0.42), 0.008, label=6)
        q = v3((-0.18, sy * 0.36, zt))
        tk.paint(RoundBox(q, (0.09, 0.05, 0.09), 0.0, R=euler(0, 0, 0) @ rot_from_axes(z_axis=(0, 1, 0)) @ euler(0, 0, 0.785)), 8)
        stencil(tk, (0.15, sy * 0.36, zt + 0.05), (0, sy, 0), 0.32, 0.06, label=9, n=4)
    box(tk, (-1.18, 0, 0.5), (0.12, 0.34, 0.2), 0.02, label=0)
    hs.add(Torus((-1.32, 0, 0.5), 0.13, 0.04, R=RX), k=0.0)
    hs.add(Torus((-1.32, 0, 0.5), 0.08, 0.04, R=RX), k=0.01)
    for (x, dual) in ((0.95, False), (-0.4, True), (-0.75, True)):
        for sy in (-1, 1):
            wheel(tf, hf, (x, sy * 0.3, 0.15), (0, sy, 0), 0.15, 0.1 if not dual else 0.14)
    ground_cut(tf, -0.01)
    out += [("Cab", bd, fine(0.006, 0.012), "olive"), ("Glass", gl, fine(0.005, 0.01), "glass"), ("Tank", tk, fine(0.006, 0.012), "olive"),
            ("Hose", hs, fine(0.004, 0.008), "rubber"), ("Tyres", tf, fine(0.005, 0.01), "rubber"), ("Hubs", hf, fine(0.004, 0.008), "olive")]
    return out


def radome(seed=0):
    """A radar dome: the white radome (its panels drawn in) on a ring beam over a concrete drum with a door, a ladder
    up the drum and a rail round the ring, a red warning light on top; an equipment hut beside it with an air
    conditioner."""
    out = []
    cb, rd, st, lt, dk = Field("Drum"), Field("Dome"), Field("Steel"), Field("Warn"), Field("Dark")
    cb.add(Cylinder((0, 0, 0.45), 0.55, 0.94, rr=0.02), k=0.0)
    box(cb, (0, 0, 0.93), (0.66, 0.66, 0.04), 0.02, k=0.0, label=7)
    cb.add(Cylinder((0, 0, 0.93), 0.66, 0.06, rr=0.02), k=0.0, label=7)
    cb.sub(RoundBox((0, -0.55, 0.3), (0.13, 0.08, 0.3), 0.01), k=0.0)
    dk.add(RoundBox((0, -0.5, 0.3), (0.13, 0.01, 0.3), 0.0), k=0.0)
    rd.add(Sphere((0, 0, 1.45), 0.75), k=0.0)
    rd.inter(Plane((0, 0, 0.95), (0, 0, -1)))
    for i in range(12):                                             # the rail round the ring
        a = 2 * math.pi * i / 12
        pole(st, (math.cos(a) * 0.82, math.sin(a) * 0.82, 0.96), (math.cos(a) * 0.82, math.sin(a) * 0.82, 1.18), 0.008)
    st.add(Torus((0, 0, 1.18), 0.82, 0.01), k=0.004)
    for dx in (-0.09, 0.09):                                        # the ladder
        pole(st, (0.3 + dx, -0.53, 0.0), (0.3 + dx, -0.56, 0.98), 0.009)
    for z in np.arange(0.12, 0.95, 0.11):
        pole(st, (0.21, -0.54 - z * 0.03, z), (0.39, -0.54 - z * 0.03, z), 0.007)
    pole(st, (0, 0, 2.18), (0, 0, 2.28), 0.012)
    lt.add(Sphere((0, 0, 2.3), 0.035), k=0.0)
    ht = Field("Hut")
    box(ht, (1.0, 0.35, 0.3), (0.3, 0.28, 0.3), 0.02)
    box(ht, (1.0, 0.35, 0.62), (0.34, 0.32, 0.03), 0.01, k=0.004, label=7)
    box(ht, (1.32, 0.35, 0.3), (0.05, 0.13, 0.1), 0.01, k=0.004, label=6)
    ht.sub(RoundBox((1.0, 0.06, 0.25), (0.09, 0.02, 0.22), 0.006), k=0.0)
    dk.add(RoundBox((1.0, 0.075, 0.25), (0.09, 0.006, 0.22), 0.0), k=0.0)
    for c in (cb, ht, st):
        ground_cut(c, -0.03)
    out += [("Drum", cb, fine(0.008, 0.016), "concrete"), ("Dome", rd, fine(0.01, 0.02), "radome"), ("Steel", st, fine(0.004, 0.008), "galv"),
            ("Warn", lt, fine(0.004, 0.008), "glow_red"), ("Dark", dk, fine(0.006, 0.012), "dark"), ("Hut", ht, fine(0.006, 0.012), "olive")]
    return out


# ------------------------------------------------------------------------------------------------ Airbase: no-build zones
def rubble(seed=0, metal=False):
    """Debris thrown up round a crater: broken slabs of runway concrete tilted on a heap of earth, rebar sticking out,
    chunks and gravel (metal: a torn sheet of corrugated steel and a bent pipe among them)."""
    rng = np.random.default_rng(seed)
    out = []
    cb, ea, rb = Field("Slabs"), Field("Earth"), Field("Rebar")
    ea.add(Ellipsoid((0, 0, -0.05), (0.62, 0.42, 0.2), **wob(5.0, 0.04, seed)), k=0.0)
    for i in range(4):
        a = 2 * math.pi * i / 4 + rng.uniform(-0.3, 0.3)
        c = v3((math.cos(a) * 0.3, math.sin(a) * 0.2, 0.09))
        R = Rz(rng.uniform(0, 3)) @ euler(rng.uniform(-0.6, 0.6), rng.uniform(-0.4, 0.4), 0)
        cb.add(RoundBox(c, (rng.uniform(0.16, 0.24), rng.uniform(0.12, 0.18), 0.045), 0.01, R=R, **wob(14.0, 0.008, seed + i)), k=0.0)
        for j in range(3):                                          # bites out of their edges
            q = c + R @ v3((rng.uniform(-0.2, 0.2), rng.uniform(-0.15, 0.15), 0.0))
            cb.sub(Sphere(q + R @ v3((0.18 * rng.choice([-1, 1]), 0, 0)), rng.uniform(0.04, 0.07)), k=0.01)
        for j in range(2):
            p = c + R @ v3((rng.uniform(-0.12, 0.12), rng.uniform(-0.1, 0.1), 0.0))
            q = p + v3((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), rng.uniform(0.08, 0.16)))
            pole(rb, p, q, 0.006)
    for i in range(7):
        c = v3((rng.uniform(-0.55, 0.55), rng.uniform(-0.4, 0.4), 0.03))
        cb.add(Ellipsoid(c, (rng.uniform(0.03, 0.07),) * 2 + (0.035,), R=Rz(rng.uniform(0, 3)), **wob(20.0, 0.006, seed + 20 + i)), k=0.0)
    for f in (cb, ea):
        ground_cut(f, -0.02)
    out += [("Slabs", cb, fine(0.006, 0.012), "concrete"), ("Earth", ea, fine(0.01, 0.02), "dirt"), ("Rebar", rb, fine(0.003, 0.006), "rust")]
    if metal:
        mt = Field("Sheet")
        mt.add(leaf((-0.3, 0.1, 0.12), (math.cos(0.5), math.sin(0.5), 0.25), (0, 0, 1), [(0, -0.05), (0.5, -0.12), (0.55, 0.15), (0.05, 0.2)], 0.006,
                    zfn=lambda a, b: (F32(0.012) * np.sin(b * F32(60)) + F32(0.25) * a * a, F32(0.5) * a, F32(0.72) * np.cos(b * F32(60))), zamp=0.08), k=0.0)
        mt.add(Chain([v3((0.25, -0.2, 0.05)), v3((0.45, -0.1, 0.12)), v3((0.55, 0.15, 0.08))], [0.025, 0.025, 0.025], k=0.02), k=0.0)
        out.append(("Sheet", mt, fine(0.004, 0.008), "rust"))
    return out


def wreck(seed=0):
    """A burnt-out Humvee: blackened and rusting, its glass gone, slumped on its rims, the bonnet sprung, a scorch on
    the ground round it."""
    out = humvee(seed, paint="rust", wreck=True)
    out = [(n, f, vxs, m) for (n, f, vxs, m) in out]
    sc = Field("Scorch")
    sc.add(Ellipsoid((0, 0, -0.02), (1.05, 0.7, 0.04), **wob(4.0, 0.03, seed)), k=0.0)
    ground_cut(sc, -0.02)
    moved = []
    place_parts(moved, out, (0, 0, -0.07), euler(0.06, -0.03, 0.0))
    bd = next(f for (n, f, _, _) in moved if n == "Body")
    bd.add(RoundBox((0.55, 0, 0.36), (0.22, 0.36, 0.012), 0.006, R=euler(0, -0.35, 0)), k=0.0)
    return moved + [("Scorch", sc, fine(0.012, 0.024), "soot")]


WRECK_SMOKE = (0.55, 0.0, 0.42)


def radar_dish(seed=0):
    """A mobile radar: a two-axle trailer on its jacks, an equipment shelter at its front, the turntable at its back
    carrying a parabolic dish tilted up toward -Y and its feed horn on three struts."""
    out = []
    tr, tf, hf, ds, st = Field("Trailer"), Field("Tyres"), Field("Hubs"), Field("Dish"), Field("Struts")
    box(tr, (0, 0, 0.32), (0.75, 0.32, 0.05), 0.015, label=7)
    box(tr, (0.42, 0, 0.6), (0.3, 0.3, 0.24), 0.03)
    stencil(tr, (0.42, -0.3, 0.68), (0, -1, 0), 0.4, 0.05, label=9, n=4)
    pole(tr, (0.75, 0, 0.3), (1.05, 0, 0.25), 0.025, label=7)
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = v3((sx * 0.68, sy * 0.36, 0.0))
            pole(tr, q + Z * 0.3, q + Z * 0.02, 0.02, label=7)
            box(tr, q + Z * 0.012, (0.05, 0.05, 0.012), 0.004, k=0.003, label=7)
    for x in (-0.15, -0.5):
        for sy in (-1, 1):
            wheel(tf, hf, (x, sy * 0.3, 0.15), (0, sy, 0), 0.15, 0.09)
    tr.add(Cylinder((-0.35, 0, 0.42), 0.2, 0.16, rr=0.03), k=0.0, label=7)
    tr.add(RoundBox((-0.35, 0, 0.62), (0.08, 0.12, 0.16), 0.03), k=0.02)
    ground_cut(tf, -0.01)
    ground_cut(tr, -0.01)
    c0 = v3((-0.35, 0, 0.82))
    ax = unit(v3((0, -0.75, 0.66)))
    R = rot_from_axes(z_axis=ax, y_axis=(1, 0, 0))
    Rf = R.astype(F32)
    Rd, Fc = 0.62, 0.38
    vert = c0 - ax * 0.1

    def dish(P):
        Q = (P - F32(vert)) @ Rf
        r2 = Q[:, 0] ** 2 + Q[:, 1] ** 2
        f = r2 / F32(4 * Fc)
        d = np.abs(Q[:, 2] - f) / np.sqrt(F32(1) + r2 / F32(4 * Fc * Fc)) - F32(0.012)
        return np.maximum(d, np.sqrt(r2) - F32(Rd)).astype(F32)
    ds.add(Func(dish, vert - 0.9, vert + 0.9), k=0.0)
    def rim(P):
        Q = (P - F32(vert)) @ Rf
        return (np.sqrt((np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2) - F32(Rd)) ** 2 + (Q[:, 2] - F32(Rd * Rd / (4 * Fc))) ** 2) - F32(0.02)).astype(F32)
    ds.add(Func(rim, vert - 0.9, vert + 0.9), k=0.004, label=7)
    focus = vert + ax * Fc
    for i in range(3):
        a = 2 * math.pi * i / 3
        q = vert + R @ v3((math.cos(a) * Rd * 0.85, math.sin(a) * Rd * 0.85, (Rd * 0.85) ** 2 / (4 * Fc)))
        pole(st, q, focus, 0.009)
    st.add(RoundCone(focus - ax * 0.02, focus + ax * 0.08, 0.05, 0.035), k=0.004)
    pole(st, vert - ax * 0.02, c0 - Z * 0.1, 0.04)
    out += [("Trailer", tr, fine(0.006, 0.012), "olive"), ("Tyres", tf, fine(0.005, 0.01), "rubber"), ("Hubs", hf, fine(0.004, 0.008), "olive"),
            ("Dish", ds, fine(0.006, 0.012), "radome"), ("Struts", st, fine(0.004, 0.008), "galv")]
    return out


def generator(seed=0):
    """A skid-mounted diesel generator: the louvred olive housing with its doors and stencils, the control panel, the
    exhaust stack with its rain cap, the fuel tank in the skid, cables run off across the ground to a junction box."""
    out = []
    g, st, cb = Field("Genset"), Field("Exhaust"), Field("Cables")
    box(g, (0, 0, 0.07), (0.62, 0.32, 0.06), 0.01, label=7)
    box(g, (0, 0, 0.42), (0.58, 0.3, 0.3), 0.03)
    box(g, (0, 0, 0.74), (0.6, 0.32, 0.025), 0.01, k=0.004)
    for sy in (-1, 1):
        for i in range(3):
            x = -0.38 + i * 0.38
            g.sub(RoundBox((x, sy * 0.305, 0.42), (0.16, 0.01, 0.22), 0.004), k=0.0)
            for z in np.arange(0.24, 0.62, 0.05):
                box(g, (x, sy * 0.3, z), (0.15, 0.012, 0.008), 0.003, R=euler(sy * 0.4, 0, 0), k=0.0, label=7)
        stencil(g, (0.0, sy * 0.3, 0.68), (0, sy, 0), 0.5, 0.04, label=9, n=5)
    box(g, (0.6, 0.0, 0.45), (0.04, 0.2, 0.16), 0.01, k=0.004, label=7)
    g.paint(RoundBox((0.64, 0.0, 0.5), (0.02, 0.12, 0.05), 0.0), 9)
    pole(st, (-0.35, 0.15, 0.74), (-0.35, 0.15, 1.15), 0.035)
    st.add(RoundBox((-0.33, 0.15, 1.17), (0.06, 0.05, 0.008), 0.004, R=euler(0, -0.4, 0)), k=0.0)
    pts = [v3((0.62, -0.1, 0.3)), v3((0.75, -0.2, 0.02)), v3((1.0, -0.45, 0.02)), v3((1.2, -0.4, 0.02))]
    cb.add(Chain(pts, [0.018] * 4, k=0.03), k=0.0)
    cb.add(Chain([v3((0.62, 0.1, 0.3)), v3((0.8, 0.25, 0.02)), v3((1.05, 0.2, 0.02)), v3((1.2, -0.3, 0.02))], [0.018] * 4, k=0.03), k=0.0)
    jb = Field("Box")
    box(jb, (1.25, -0.36, 0.12), (0.08, 0.12, 0.12), 0.02)
    for f in (g, cb, jb):
        ground_cut(f, -0.01)
    out += [("Genset", g, fine(0.005, 0.01), "olive"), ("Exhaust", st, fine(0.004, 0.008), "gunmetal"), ("Cables", cb, fine(0.004, 0.008), "rubber"),
            ("Box", jb, fine(0.004, 0.008), "yellow_paint")]
    return out


GEN_SMOKE = (-0.35, 0.15, 1.2)


def aa_gun(seed=0):
    """An anti-aircraft gun in its ring of sandbags: a twin-barrelled cannon on a cruciform mount with its jacks, the
    gunner's seat and sight, the barrels raised toward -Y with their flash hiders, ammunition boxes on the cradle and
    crates in the pit."""
    out = []
    sb, mt, br, cr = Field("Sandbags"), Field("Mount"), Field("Barrels"), Field("Crates")
    for i in range(10):
        a0, a1 = 2 * math.pi * i / 11 + 0.9, 2 * math.pi * (i + 1) / 11 + 0.9
        sandbag_run(sb, (math.cos(a0) * 0.88, math.sin(a0) * 0.88, 0), (math.cos(a1) * 0.88, math.sin(a1) * 0.88, 0), layers=3, seed=seed + i * 7)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        pole(mt, (0, 0, 0.12), (math.cos(a) * 0.55, math.sin(a) * 0.55, 0.06), 0.035)
        box(mt, (math.cos(a) * 0.55, math.sin(a) * 0.55, 0.03), (0.06, 0.06, 0.02), 0.006, k=0.004)
    mt.add(Cylinder((0, 0, 0.17), 0.22, 0.1, rr=0.02), k=0.0)
    box(mt, (0, 0, 0.36), (0.18, 0.2, 0.14), 0.03)
    for sx in (-1, 1):
        box(mt, (sx * 0.17, 0, 0.5), (0.03, 0.14, 0.12), 0.015, k=0.0)
    box(mt, (0.0, 0.32, 0.36), (0.1, 0.08, 0.02), 0.01, k=0.0, label=7)
    pole(mt, (0, 0.2, 0.3), (0, 0.32, 0.36), 0.015)
    box(mt, (0.18, 0.12, 0.62), (0.03, 0.03, 0.06), 0.01, k=0.0, label=7)
    el = 0.62
    ax = unit(v3((0, -math.cos(el), math.sin(el))))
    piv = v3((0, -0.02, 0.52))
    for sx in (-0.07, 0.07):
        b0 = piv + v3((sx, 0, 0)) - ax * 0.2
        br.add(RoundBox(b0 + ax * 0.15, (0.05, 0.12, 0.05), 0.015, R=rot_from_axes(y_axis=ax, x_axis=(1, 0, 0))), k=0.0)
        pole(br, b0 + ax * 0.2, b0 + ax * 1.05, 0.022, 0.018)
        br.add(RoundCone(b0 + ax * 1.0, b0 + ax * 1.12, 0.03, 0.028), k=0.006)
        br.add(Torus(b0 + ax * 0.5, 0.026, 0.007, R=rot_from_axes(z_axis=ax)), k=0.003)
    for sx in (-1, 1):
        ammo_can(mt, piv + v3((sx * 0.27, 0.03, -0.02)), 1.5708, s=1.2, label=0)
    ammo_crate(cr, (0.45, 0.2, 0.09), (0.18, 0.1, 0.09), 1.2)
    ammo_crate(cr, (-0.4, 0.3, 0.09), (0.18, 0.1, 0.09), -0.6)
    for f in (sb, mt, cr):
        ground_cut(f, -0.01)
    out += [("Sandbags", sb, fine(0.005, 0.01), "sandbag"), ("Mount", mt, fine(0.005, 0.01), "olive"), ("Barrels", br, fine(0.004, 0.008), "gunmetal"),
            ("Crates", cr, fine(0.005, 0.01), "crate_olive")]
    return out


def pallet_stack(seed=0):
    """Supplies on a pallet: six olive crates in two tiers and one on top, strapped down with yellow ratchet straps, a
    couple of ammo cans beside it."""
    out = []
    wd, cr, sp = Field("Pallet"), Field("Crates"), Field("Straps")
    pallet(wd, (0, 0, 0), 0.42, 0.34)
    for i, (x, y, z) in enumerate(((-0.21, -0.17, 0), (0.21, -0.17, 0), (-0.21, 0.17, 0), (0.21, 0.17, 0), (0.0, -0.17, 1), (0.0, 0.17, 1))):
        hx = 0.2 if z == 0 else 0.38
        ammo_crate(cr, (x, y, 0.2 + z * 0.22), (hx, 0.16, 0.1), 0.0, mark=(i % 2 == 0))
    ammo_crate(cr, (0.05, 0.0, 0.64), (0.2, 0.14, 0.1), 0.15)
    for x in (-0.18, 0.18):
        sp.add(Func(lambda P, x=x: np.maximum(np.abs(np.maximum(np.abs(P[:, 1]) - F32(0.35), np.abs(P[:, 2] - F32(0.3)) - F32(0.22))) - F32(0.006),
                                              np.abs(P[:, 0] - F32(x)) - F32(0.025)).astype(F32), (x - 0.1, -0.5, 0.0), (x + 0.1, 0.5, 0.6)), k=0.0)
        sp.add(RoundBox((x, -0.355, 0.32), (0.035, 0.012, 0.03), 0.006), k=0.004)
    ammo_can(cr, (0.55, -0.2, 0.055), 0.4, label=0)
    ammo_can(cr, (0.52, 0.05, 0.055), 0.2, label=0)
    for f in (wd, cr):
        ground_cut(f, -0.01)
    out += [("Pallet", wd, fine(0.004, 0.008), "timber"), ("Crates", cr, fine(0.005, 0.01), "crate_olive"), ("Straps", sp, fine(0.004, 0.008), "yellow_paint")]
    return out


def forklift(seed=0):
    """A yellow forklift (forks toward +X): the counterweighted body, the seat under its overhead guard, the mast with
    the forks a little raised, big front wheels and small steering wheels, an amber beacon on the guard."""
    out = []
    bd, gd, ms, tf, hf, fk = (Field(n) for n in ("Body", "Guard", "Mast", "Tyres", "Hubs", "Forks"))
    box(bd, (-0.05, 0, 0.3), (0.42, 0.28, 0.16), 0.05)
    bd.add(Ellipsoid((-0.42, 0, 0.36), (0.14, 0.28, 0.2)), k=0.08)
    box(bd, (-0.12, 0, 0.52), (0.16, 0.16, 0.08), 0.04, k=0.03, label=7)
    box(bd, (-0.18, 0, 0.66), (0.04, 0.15, 0.12), 0.03, k=0.0, label=7)
    pole(bd, (0.15, 0, 0.48), (0.08, 0, 0.62), 0.015, label=7)
    bd.add(Torus((0.08, 0, 0.63), 0.07, 0.01, R=rot_from_axes(z_axis=(-0.4, 0, 1))), k=0.004, label=7)
    for sx in (-1, 1):
        for sy in (-1, 1):
            pole(gd, (sx * 0.24 - 0.06, sy * 0.24, 0.42), (sx * 0.24 - 0.06 + (0.04 if sx > 0 else 0), sy * 0.24, 1.06), 0.018)
    box(gd, (-0.04, 0, 1.07), (0.3, 0.27, 0.02), 0.01, k=0.004)
    for y in (-0.12, 0.0, 0.12):
        gd.sub(RoundBox((-0.04, y, 1.07), (0.24, 0.04, 0.04), 0.0), k=0.0)
    for sy in (-1, 1):
        box(ms, (0.45, sy * 0.18, 0.62), (0.03, 0.03, 0.6), 0.008)
    box(ms, (0.45, 0, 1.18), (0.03, 0.2, 0.025), 0.008)
    box(ms, (0.45, 0, 0.5), (0.03, 0.2, 0.02), 0.008)
    box(fk, (0.5, 0, 0.3), (0.025, 0.2, 0.12), 0.008)
    for sy in (-1, 1):
        box(fk, (0.78, sy * 0.12, 0.2), (0.28, 0.035, 0.012), 0.006)
        box(fk, (0.51, sy * 0.12, 0.3), (0.02, 0.035, 0.12), 0.006)
    for (x, r) in ((0.28, 0.17), (-0.36, 0.13)):
        for sy in (-1, 1):
            wheel(tf, hf, (x, sy * 0.25, r), (0, sy, 0), r, 0.12)
    for sy in (-1, 1):
        bd.sub(Cylinder((0.28, sy * 0.25, 0.17), 0.2, 0.2, R=RY), k=0.01)
    lt = Field("Beacon")
    lt.add(Cylinder((-0.2, 0.15, 1.12), 0.035, 0.06, rr=0.015), k=0.0)
    ground_cut(tf, -0.01)
    out += [("Body", bd, fine(0.005, 0.01), "yellow_paint"), ("Guard", gd, fine(0.004, 0.008), "gunmetal"), ("Mast", ms, fine(0.004, 0.008), "gunmetal"),
            ("Forks", fk, fine(0.004, 0.008), "gunmetal"), ("Tyres", tf, fine(0.005, 0.01), "rubber"), ("Hubs", hf, fine(0.004, 0.008), "yellow_paint"),
            ("Beacon", lt, fine(0.004, 0.008), "glow_amber")]
    return out


# ------------------------------------------------------------------------------------------------ Downtown: scatter
def street_light(seed=0, H=2.4):
    """A street light: a tapering dark-grey pole on its plinth, the arm curving out over the street to a cobra-head
    lantern with its glowing lens underneath."""
    p, gl = Field("Pole"), Field("Lens")
    p.add(Cylinder((0, 0, 0.06), 0.075, 0.12, rr=0.02), k=0.0, label=7)
    pole(p, (0, 0, 0.1), (0, 0, H), 0.045, 0.028, k=0.02)
    p.add(Torus((0, 0, 0.14), 0.05, 0.012), k=0.004, label=7)
    arm = [v3((0, 0, H - 0.05)), v3((0.05, 0, H + 0.12)), v3((0.28, 0, H + 0.2)), v3((0.58, 0, H + 0.17))]
    p.add(Chain(arm, [0.026, 0.022, 0.02, 0.018], k=0.02), k=0.01)
    p.add(Ellipsoid((0.68, 0, H + 0.15), (0.17, 0.085, 0.045)), k=0.01)
    gl.add(Ellipsoid((0.7, 0, H + 0.115), (0.12, 0.06, 0.018)), k=0.0)
    ground_cut(p, -0.02)
    return [("Pole", p, fine(0.004, 0.008), "street_iron"), ("Lens", gl, fine(0.004, 0.008), "glow_lamp")]


def traffic_light(seed=0):
    """A traffic signal: a galvanised pole, a mast arm out over the street with a yellow signal head hanging from it
    (red lit), a second head on the pole, a pedestrian signal (the orange hand lit) and its push button."""
    out = []
    p, hd, ln, lt, ped = Field("Pole"), Field("Heads"), Field("Lenses"), Field("Red"), Field("Hand")
    p.add(Cylinder((0, 0, 0.05), 0.07, 0.1, rr=0.02), k=0.0)
    pole(p, (0, 0, 0.08), (0, 0, 2.1), 0.04, 0.032, k=0.02)
    pole(p, (0, 0, 1.9), (0.95, 0, 1.98), 0.026, 0.018, k=0.01)
    pole(p, (0, 0, 1.62), (0.5, 0, 1.9), 0.012, k=0.004)

    def head(c, facing=(0, -1, 0)):
        c = v3(c)
        R = rot_from_axes(y_axis=facing, x_axis=(1, 0, 0)) if abs(facing[0]) < 0.9 else rot_from_axes(y_axis=facing, x_axis=(0, 1, 0))
        n = R @ v3((0, 1, 0))
        hd.add(RoundBox(c, (0.07, 0.06, 0.2), 0.02, R=R), k=0.0)
        hd.add(RoundBox(c - n * 0.065, (0.11, 0.008, 0.24), 0.01, R=R), k=0.006, label=7)
        for i, z in enumerate((0.13, 0.0, -0.13)):
            q = c + n * 0.06 + Z * z
            hd.add(RoundBox(q + n * 0.035 + Z * 0.05, (0.06, 0.035, 0.007), 0.004, R=R), k=0.004)
            (lt if i == 0 else ln).add(Cylinder(q + n * 0.004, 0.048, 0.01, R=rot_from_axes(z_axis=n)), k=0.0, label=(0 if i == 0 else (5 if i == 1 else 6)))
    head((0.9, 0, 1.75))
    head((0.0, -0.1, 1.55))
    ped.add(RoundBox((0.0, -0.11, 0.98), (0.06, 0.006, 0.06), 0.01), k=0.0)
    hd.add(RoundBox((0.0, -0.075, 0.98), (0.075, 0.035, 0.075), 0.015), k=0.0, label=7)
    hd.add(RoundBox((0.0, -0.05, 0.62), (0.035, 0.02, 0.05), 0.01), k=0.0)
    ground_cut(p, -0.02)
    out += [("Pole", p, fine(0.004, 0.008), "galv"), ("Heads", hd, fine(0.004, 0.008), "signal"), ("Lenses", ln, fine(0.004, 0.008), "lenses"),
            ("Red", lt, fine(0.004, 0.008), "glow_red"), ("Hand", ped, fine(0.004, 0.008), "glow_amber")]
    return out


def bench_modern(seed=0):
    """A city bench: two dark steel end frames, a seat and back of hardwood slats, an armrest in the middle."""
    fr, sl = Field("Frame"), Field("Slats")
    L = 0.5
    for x in (-L + 0.05, L - 0.05, 0.0):
        if x != 0.0:
            fr.add(RoundBox((x, 0.0, 0.11), (0.018, 0.14, 0.11), 0.01), k=0.0)
            fr.sub(RoundBox((x, 0.0, 0.09), (0.03, 0.1, 0.07), 0.02), k=0.0)
            pole(fr, (x, 0.12, 0.2), (x, 0.18, 0.5), 0.015)
        pole(fr, (x, -0.12, 0.24), (x, -0.12, 0.32), 0.012)
        pole(fr, (x, -0.12, 0.32), (x, 0.08, 0.32), 0.012)
    for y in (-0.1, -0.035, 0.03, 0.095):
        box(sl, (0, y, 0.235), (L, 0.028, 0.012), 0.006, label=10)
    for z in (0.34, 0.44):
        box(sl, (0, 0.155 + (z - 0.34) * 0.2, z), (L, 0.01, 0.035), 0.006, R=euler(-0.2, 0, 0), label=10)
    ground_cut(fr, -0.02)
    return [("Frame", fr, fine(0.004, 0.008), "street_iron"), ("Slats", sl, fine(0.004, 0.008), "timber")]


def bus_stop(seed=0):
    """A bus shelter (front toward -Y): a steel frame under a curved roof, a glass back, a lit advertising panel at one
    end, a bench inside; the bus stop sign on its pole."""
    out = []
    fr, gl, ad, lt, sg = Field("Frame"), Field("Glass"), Field("Ad"), Field("AdLight"), Field("Sign")
    W, D, H = 0.75, 0.3, 0.95
    for x in (-W, W):
        for y in (-D, D):
            pole(fr, (x, y, -0.02), (x, y, H), 0.018)
    roof = Func(lambda P: np.maximum.reduce([np.abs(P[:, 2] - (F32(H + 0.04) - F32(0.25) * P[:, 1] ** 2)) - F32(0.018),
                                             np.abs(P[:, 0]) - F32(W + 0.08), np.abs(P[:, 1]) - F32(D + 0.12)]).astype(F32),
                (-W - 0.2, -D - 0.2, H - 0.1), (W + 0.2, D + 0.2, H + 0.15))
    fr.add(roof, k=0.0)
    pole(fr, (-W, D, 0.06), (W, D, 0.06), 0.012)
    pole(fr, (-W, D, H - 0.04), (W, D, H - 0.04), 0.014)
    gl.add(RoundBox((0, D, 0.5), (W - 0.02, 0.006, 0.42), 0.004), k=0.0)
    box(ad, (W, 0.0, 0.5), (0.025, D - 0.02, 0.4), 0.01)
    box(fr, (W, 0.0, 0.5), (0.04, D, 0.44), 0.015, k=0.0, label=7)
    fr.sub(RoundBox((W, 0.0, 0.5), (0.06, D - 0.03, 0.4), 0.01), k=0.0)
    lt.add(RoundBox((W, 0.0, 0.5), (0.03, D - 0.035, 0.405), 0.004), k=0.0)
    lt.sub(RoundBox((W, 0.0, 0.5), (0.04, D - 0.05, 0.385), 0.004), k=0.0)
    ad.paint(Ellipsoid((W, -0.05, 0.6), (0.2, 0.15, 0.15)), 5)
    ad.paint(RoundBox((W, 0.0, 0.25), (0.2, 0.22, 0.05), 0.0), 9)
    for y in (0.12, 0.2):
        box(fr, (0, y, 0.24), (W - 0.15, 0.03, 0.012), 0.006, k=0.0, label=6)
    for x in (-W + 0.2, W - 0.2):
        pole(fr, (x, 0.18, 0.0), (x, 0.18, 0.24), 0.012)
    pole(sg, (-W - 0.25, -D - 0.05, -0.02), (-W - 0.25, -D - 0.05, 1.35), 0.018)
    box(sg, (-W - 0.25, -D - 0.06, 1.2), (0.13, 0.012, 0.12), 0.01, label=5)
    sg.paint(RoundBox((-W - 0.25, -D - 0.08, 1.24), (0.07, 0.03, 0.03), 0.0), 9)
    for f in (fr, sg):
        ground_cut(f, -0.02)
    out += [("Frame", fr, fine(0.004, 0.008), "galv"), ("Glass", gl, fine(0.004, 0.008), "glass"), ("Ad", ad, fine(0.004, 0.008), "poster"),
            ("AdLight", lt, fine(0.003, 0.006), "glow_window"), ("Sign", sg, fine(0.004, 0.008), "sign")]
    return out


def hydrant(seed=0):
    """A fire hydrant: a red barrel on its flanged foot, the domed bonnet and its pentagon nut, two side outlets and the
    big pumper outlet in front, their chained silver caps."""
    f = Field("Hydrant")
    f.add(Cylinder((0, 0, 0.03), 0.09, 0.06, rr=0.015), k=0.0)
    f.add(RoundCone((0, 0, 0.04), (0, 0, 0.36), 0.062, 0.058), k=0.01)
    f.add(Torus((0, 0, 0.36), 0.066, 0.014), k=0.006)
    f.add(Ellipsoid((0, 0, 0.38), (0.068, 0.068, 0.06)), k=0.01)
    f.add(Cylinder((0, 0, 0.45), 0.022, 0.04, rr=0.006), k=0.004, label=6)
    for (d, r, L) in (((1, 0, 0), 0.03, 0.08), ((-1, 0, 0), 0.03, 0.08), ((0, -1, 0), 0.042, 0.09)):
        d = v3(d)
        q = v3((0, 0, 0.26))
        f.add(RoundCone(q, q + d * L, r, r), k=0.01)
        f.add(Cylinder(q + d * (L + 0.01), r + 0.008, 0.03, rr=0.008, R=rot_from_axes(z_axis=d)), k=0.003, label=6)
    ground_cut(f, -0.01)
    return [("Hydrant", f, fine(0.003, 0.006), "hydrant")]


def news_boxes(seed=0):
    """Newspaper boxes in a row on their pedestals: blue, red and yellow, each with its window, coin slot and the
    sloping top, the one at the end chained to the others."""
    f, gl = Field("Boxes"), Field("Windows")
    for i, (x, lab) in enumerate(((-0.2, 0), (0.0, 8), (0.2, 5))):
        c = v3((x, 0, 0.0))
        pole(f, c + Z * 0.0, c + Z * 0.14, 0.02, label=7)
        box(f, c + v3((0, 0, 0.01)), (0.07, 0.07, 0.01), 0.004, k=0.004, label=7)
        box(f, c + v3((0, 0, 0.3)), (0.085, 0.09, 0.16), 0.012, k=0.0, label=lab)
        f.add(convex([(c + v3((0, 0, 0.5)), (0, -0.3, 1)), (c + v3((0, 0, 0.44)), (0, 0, -1)), (c + v3((0.087, 0, 0)), (1, 0, 0)),
                      (c + v3((-0.087, 0, 0)), (-1, 0, 0)), (c + v3((0, 0.092, 0)), (0, 1, 0)), (c + v3((0, -0.092, 0)), (0, -1, 0))],
                     c + v3((-0.2, -0.2, 0.35)), c + v3((0.2, 0.2, 0.6))), k=0.01, label=lab)
        gl.add(RoundBox(c + v3((0, -0.088, 0.36)), (0.06, 0.006, 0.07), 0.006), k=0.0)
        f.paint(RoundBox(c + v3((0, -0.09, 0.23)), (0.06, 0.02, 0.025), 0.0), 9)
        box(f, c + v3((0.05, -0.092, 0.47)), (0.012, 0.006, 0.02), 0.003, k=0.002, label=6)
    ground_cut(f, -0.01)
    return [("Boxes", f, fine(0.004, 0.008), "newsbox"), ("Windows", gl, fine(0.004, 0.008), "glass")]


def bollards(seed=0):
    """A row of steel bollards with domed caps and yellow reflective bands."""
    f = Field("Bollards")
    for x in (-0.36, 0.0, 0.36):
        f.add(Cylinder((x, 0, 0.2), 0.05, 0.42, rr=0.01), k=0.0)
        f.add(Sphere((x, 0, 0.41), 0.05), k=0.01)
        f.paint(Cylinder((x, 0, 0.33), 0.08, 0.04), 5)
    ground_cut(f, -0.02)
    return [("Bollards", f, fine(0.004, 0.008), "bollard")]


def trash_can(seed=0):
    """A city litter bin: a slatted dark green steel drum, its domed lid with the opening, a white crest."""
    f = Field("Bin")
    f.add(Cylinder((0, 0, 0.21), 0.13, 0.42, rr=0.015, disp=lambda P: (F32(0.004) * np.cos(np.arctan2(P[:, 1], P[:, 0]) * F32(24))).astype(F32), disp_amp=0.005), k=0.0)
    for z in (0.06, 0.38):
        f.add(Torus((0, 0, z), 0.135, 0.012), k=0.004)
    f.add(Ellipsoid((0, 0, 0.43), (0.14, 0.14, 0.07)), k=0.01)
    f.sub(RoundBox((0, -0.13, 0.45), (0.07, 0.06, 0.035), 0.02), k=0.01)
    f.paint(Ellipsoid((0, -0.13, 0.24), (0.05, 0.05, 0.05)), 9)
    ground_cut(f, -0.01)
    return [("Bin", f, fine(0.004, 0.008), "street_green")]


def planter(seed=0):
    """A concrete planter on the sidewalk: the box with its chamfered coping, earth, a young street tree and flowers
    round its foot."""
    out = []
    pc, so, fl = Field("Planter"), Field("Soil"), Field("Flowers")
    box(pc, (0, 0, 0.17), (0.36, 0.36, 0.17), 0.02)
    box(pc, (0, 0, 0.35), (0.39, 0.39, 0.025), 0.012, k=0.004)
    pc.sub(RoundBox((0, 0, 0.42), (0.31, 0.31, 0.12), 0.01), k=0.0)
    so.add(RoundBox((0, 0, 0.3), (0.32, 0.32, 0.03), 0.02, **wob(10.0, 0.008, seed)), k=0.0)
    rng = np.random.default_rng(seed)
    for i in range(10):
        a = 2 * math.pi * i / 10 + rng.uniform(-0.2, 0.2)
        q = v3((math.cos(a) * 0.22, math.sin(a) * 0.22, 0.34))
        fl.add(Ellipsoid(q, (0.05, 0.05, 0.035), **wob(25.0, 0.01, seed + i)), k=0.0, label=(5 if i % 3 == 0 else (6 if i % 3 == 1 else 0)))
    ground_cut(pc, -0.02)
    out += [("Planter", pc, fine(0.006, 0.012), "concrete"), ("Soil", so, fine(0.008, 0.016), "dirt"), ("Flowers", fl, fine(0.005, 0.01), "flowers")]
    tr = retex(oak(1.55, seed + 1, young=True), {"oak_bark": "street_bark", "oak_leaves": "street_leaves"})
    place_parts(out, tr, (0, 0, 0.3))
    return out


def street_tree(h=3.0, seed=0, guard=True):
    """A street tree (a plane) in an iron guard, or (guard=False) over a square iron grate in the pavement."""
    out = retex(plane_tree(h, seed, guard=guard), {"soot_leaves": "street_leaves", "plane_bark": "street_bark", "weed_stem": "street_bark",
                                                  "black_iron": "street_iron"})
    if not guard:
        gr = Field("Grate")
        box(gr, (0, 0, 0.0), (0.38, 0.38, 0.02), 0.006)
        for r in (0.12, 0.2, 0.28):
            gr.sub(Func(lambda P, r=r: (np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(r)) - F32(0.02)).astype(F32), (-0.4, -0.4, -0.1), (0.4, 0.4, 0.1)), k=0.0)
        ground_cut(gr, -0.02)
        out.append(("Grate", gr, fine(0.004, 0.008), "street_iron"))
    return out


def linden(h=2.4, seed=0):
    """A round-headed street linden (a young oak's build, fresh green)."""
    return retex(oak(h, seed, young=True), {"oak_bark": "street_bark", "oak_leaves": "street_leaves"})


# ------------------------------------------------------------------------------------------------ Downtown: landmarks
def _cells(nx, nz, seed, p):
    """Which window cells of a facade are lit: a stable random pattern, about p of them."""
    rng = np.random.default_rng(seed)
    return rng.random((nx, nz)) < p


def rrect(cx, cy, hx, hy, z0, z1, rc):
    """A prism on a rounded rectangle (corner radius rc) from z0 to z1."""
    def fn(P):
        qx = np.maximum(np.abs(P[:, 0] - F32(cx)) - F32(hx - rc), 0)
        qy = np.maximum(np.abs(P[:, 1] - F32(cy)) - F32(hy - rc), 0)
        inner = np.minimum(np.maximum(np.abs(P[:, 0] - F32(cx)) - F32(hx - rc), np.abs(P[:, 1] - F32(cy)) - F32(hy - rc)), 0)
        d2 = np.sqrt(qx * qx + qy * qy) + inner - F32(rc)
        return np.maximum(d2, np.abs(P[:, 2] - F32((z0 + z1) / 2)) - F32((z1 - z0) / 2)).astype(F32)
    return Func(fn, (cx - hx - 0.05, cy - hy - 0.05, z0 - 0.05), (cx + hx + 0.05, cy + hy + 0.05, z1 + 0.05))


def curtain_box(f, gw, cx, cy, hx, hy, z0, z1, seed=0, bands=(), cell=(0.16, 0.3), p=0.22, label=5, rc=0.015):
    """A glass curtain-walled block (field f) from z0 to z1 (corners rounded to rc): its lit window cells painted in
    (label), whole floors lit (the `bands`: floor indices) as glowing strips just proud of the glass (field gw)."""
    f.add(rrect(cx, cy, hx, hy, z0, z1, rc), k=0.0)
    cw, ch = cell
    nfl = int((z1 - z0) / ch)
    for side, (nx, ny, hw) in enumerate(((0, -1, hx), (0, 1, hx), (-1, 0, hy), (1, 0, hy))):
        ncol = max(1, int(2 * hw / cw))
        lit = _cells(ncol, nfl, seed * 7 + side, p)
        sx, sy = (1, 0) if nx == 0 else (0, 1)
        for i in range(ncol):
            for j in range(nfl):
                if not lit[i, j] or j in bands:
                    continue
                u = -hw + (i + 0.5) * 2 * hw / ncol
                if abs(u) > hw - rc:
                    continue
                q = v3((cx + nx * hx + sx * u, cy + ny * hy + sy * u, z0 + (j + 0.55) * ch))
                f.paint(RoundBox(q, (abs(sx) * cw * 0.42 + abs(nx) * 0.03, abs(sy) * cw * 0.42 + abs(ny) * 0.03, ch * 0.33), 0.0), label)
        for j in bands:
            if j >= nfl:
                continue
            q = v3((cx + nx * (hx + 0.004), cy + ny * (hy + 0.004), z0 + (j + 0.55) * ch))
            ins = max(0.04, rc + 0.02)
            gw.add(RoundBox(q, (abs(sx) * (hw - ins) + abs(nx) * 0.006, abs(sy) * (hw - ins) + abs(ny) * 0.006, ch * 0.3), 0.004), k=0.0)


def office_tower(seed=0, variant=0):
    """A glass office tower (front toward -Y). Variant 0: a square tower of blue-green glass in its grid of mullions, a
    setback near the top, the crown of fins, a rooftop plant room and an antenna mast with its red light, the lit lobby
    under a canopy. Variant 1: a darker, round-cornered tower stepping in twice, a cyan light band round its crown and
    a spire. Window cells lit here and there, a few whole floors burning late."""
    out = []
    cw, gw, st, rf = Field("Glass"), Field("LitFloors"), Field("Frame"), Field("Roof")
    rng = np.random.default_rng(seed)
    if variant == 0:
        tiers = [(0.96, 0.96, 0.42, 5.52), (0.8, 0.8, 5.52, 6.72)]          # (half widths in whole mullion bays of 0.16,
    else:                                                                  # floors of 0.3 from 0.42: the material's grid)
        tiers = [(0.8, 0.8, 0.42, 4.62), (0.64, 0.64, 4.62, 5.82), (0.48, 0.48, 5.82, 6.42)]
    rc = 0.015 if variant == 0 else 0.2
    for k, (hx, hy, z0, z1) in enumerate(tiers):
        nfl = int((z1 - z0) / 0.3)
        bands = tuple(int(b) for b in rng.choice(np.arange(1, nfl - 1), 2, replace=False)) if nfl >= 5 else ()
        curtain_box(cw, gw, 0, 0, hx, hy, z0, z1, seed + k, bands=bands, rc=rc)
        st.add(rrect(0, 0, hx + 0.03, hy + 0.03, z1 - 0.04, z1 + 0.04, rc + 0.03), k=0.0)
    # vertical fins on the corners (variant 0) and the crown
    top = tiers[-1]
    if variant == 0:
        hx, hy, z0, z1 = tiers[0]
        for sx in (-1, 1):
            for sy in (-1, 1):
                box(st, (sx * hx, sy * hy, (z0 + z1) / 2), (0.03, 0.03, (z1 - z0) / 2), 0.01, k=0.0)
        hx, hy, z0, z1 = top
        for i in range(9):
            u = -hx + i * 2 * hx / 8
            for sy in (-1, 1):
                box(st, (u, sy * (hy + 0.02), z1 + 0.25), (0.015, 0.03, 0.27), 0.006, k=0.0)
            for sx in (-1, 1):
                box(st, (sx * (hx + 0.02), u, z1 + 0.25), (0.03, 0.015, 0.27), 0.006, k=0.0)
        box(rf, (0.15, 0.1, z1 + 0.22), (0.4, 0.3, 0.2), 0.02)
        lattice_mast(st, (-0.35, -0.3, 0), z1, z1 + 1.1, 0.07, 0.035, step=0.18, rod=0.008)
        lt = Field("Warn")
        lt.add(Sphere((-0.35, -0.3, z1 + 1.14), 0.035), k=0.0)
        out.append(("Warn", lt, fine(0.004, 0.008), "glow_red"))
    else:
        hx, hy, z0, z1 = top
        nb = Field("Crown")
        ring = rrect(0, 0, hx + 0.012, hy + 0.012, z1 - 0.15, z1 - 0.09, rc + 0.012)
        rfn = ring.fn
        nb.add(Func(lambda P: np.maximum(rfn(P), -(rfn(P) + F32(0.024))).astype(F32), ring.lo, ring.hi), k=0.0)
        out.append(("Crown", nb, fine(0.004, 0.008), "glow_neon_cyan"))
        box(rf, (0, 0, z1 + 0.15), (0.35, 0.35, 0.13), 0.03)
        pole(st, (0, 0, z1 + 0.25), (0, 0, z1 + 1.3), 0.05, 0.008)
        lt = Field("Warn")
        lt.add(Sphere((0, 0, z1 + 1.32), 0.03), k=0.0)
        out.append(("Warn", lt, fine(0.004, 0.008), "glow_red"))
    # the lobby: a recessed, lit glass ground floor under a canopy, the base's stone plinth
    hx, hy = tiers[0][0], tiers[0][1]
    pl, lb = Field("Plinth"), Field("Lobby")
    box(pl, (0, 0, 0.21), (hx + 0.02, hy + 0.02, 0.21), 0.01)
    pl.sub(RoundBox((0, -hy, 0.18), (hx - 0.12, 0.12, 0.2), 0.01), k=0.0)
    box(lb, (0, -hy + 0.1, 0.18), (hx - 0.12, 0.012, 0.19), 0.004)
    box(pl, (0, -hy - 0.18, 0.42), (hx * 0.6, 0.2, 0.025), 0.01, k=0.0, label=7)
    ground_cut(pl, -0.02)
    out += [("Glass", cw, fine(0.012, 0.024), "curtain_a" if variant == 0 else "curtain_b"), ("LitFloors", gw, fine(0.008, 0.016), "glow_window"),
            ("Frame", st, fine(0.006, 0.012), "galv"), ("Roof", rf, fine(0.01, 0.02), "concrete"), ("Plinth", pl, fine(0.008, 0.016), "stone"),
            ("Lobby", lb, fine(0.006, 0.012), "glow_window")]
    return out


NEON = {"D": [[(0, 0), (0, 1), (0.6, 1), (1, 0.7), (1, 0.3), (0.6, 0), (0, 0)]], "I": [[(0.5, 0), (0.5, 1)]],
        "N": [[(0, 0), (0, 1), (1, 0), (1, 1)]], "E": [[(1, 0), (0, 0), (0, 1), (1, 1)], [(0, 0.5), (0.75, 0.5)]],
        "R": [[(0, 0), (0, 1), (0.8, 1), (1, 0.82), (1, 0.66), (0.8, 0.5), (0, 0.5)], [(0.45, 0.5), (1, 0)]],
        "O": [[(0.2, 0), (0, 0.2), (0, 0.8), (0.2, 1), (0.8, 1), (1, 0.8), (1, 0.2), (0.8, 0), (0.2, 0)]],
        "P": [[(0, 0), (0, 1), (0.8, 1), (1, 0.82), (1, 0.66), (0.8, 0.5), (0, 0.5)]],
        "B": [[(0, 0), (0, 1), (0.75, 1), (0.95, 0.85), (0.75, 0.52), (0, 0.52)], [(0.75, 0.52), (1, 0.32), (1, 0.18), (0.8, 0), (0, 0)]],
        "A": [[(0, 0), (0.5, 1), (1, 0)], [(0.22, 0.42), (0.78, 0.42)]], "S": [[(1, 0.9), (0.85, 1), (0.15, 1), (0, 0.85), (0, 0.6), (1, 0.4), (1, 0.15), (0.85, 0), (0.15, 0), (0, 0.1)]]}


def neon_text(f, c, side, text, h, r=0.012):
    """Neon tube lettering (field f) centred at c, reading along `side` (horizontal), letters h high."""
    side = unit(side)
    c = v3(c)
    w = h * 0.7
    n = len(text)
    for i, ch in enumerate(text):
        o = c + side * ((i - (n - 1) / 2) * w * 1.35 - w / 2) - Z * (h / 2)
        for stroke in NEON.get(ch, []):
            pts = [o + side * (a * w) + Z * (b * h) for (a, b) in stroke]
            for p, q in zip(pts[:-1], pts[1:]):
                f.add(RoundCone(p, q, r, r), k=0.0)


def diner(seed=0):
    """A streamlined chrome diner (front toward -Y): the long fluted stainless body with its red band, the window band
    lit warm all along the front, the barrel roof, the entrance vestibule with its glass doors, and the DINER sign on
    the roof in pink neon on its red board."""
    out = []
    bd, wn, rf, vs, gl, sg, ne = Field("Body"), Field("Windows"), Field("Roof"), Field("Vestibule"), Field("Doors"), Field("Board"), Field("Neon")
    L, D, H = 1.25, 0.45, 0.72
    flutes = dict(disp=lambda P: (F32(0.004) * np.cos(P[:, 2] * F32(140))).astype(F32), disp_amp=0.005)
    bd.add(RoundBox((0, 0, H / 2 + 0.06), (L, D, H / 2), 0.2, **flutes), k=0.0)
    box(bd, (0, 0, 0.05), (L - 0.05, D - 0.05, 0.06), 0.02, k=0.0, label=7)
    bd.paint(Func(lambda P: (np.abs(P[:, 2] - F32(0.28)) - F32(0.05)).astype(F32), (-2, -1, 0), (2, 1, 0.6)), 5)
    bd.paint(Func(lambda P: (np.abs(P[:, 2] - F32(0.66)) - F32(0.02)).astype(F32), (-2, -1, 0.5), (2, 1, 0.8)), 5)
    zw0, zw1 = 0.4, 0.6
    bd.sub(RoundBox((0, -D, (zw0 + zw1) / 2), (L - 0.22, 0.05, (zw1 - zw0) / 2), 0.01), k=0.0)
    box(wn, (0, -D + 0.035, (zw0 + zw1) / 2), (L - 0.22, 0.01, (zw1 - zw0) / 2), 0.0)
    for x in np.linspace(-L + 0.26, L - 0.26, 9):
        box(bd, (x, -D + 0.04, (zw0 + zw1) / 2), (0.012, 0.012, (zw1 - zw0) / 2), 0.004, k=0.0, label=6)
    rf.add(Func(lambda P: np.maximum.reduce([np.sqrt((P[:, 1] / F32(D + 0.03)) ** 2 + ((P[:, 2] - F32(H + 0.02)) / F32(0.2)) ** 2) * F32(0.2) - F32(0.2),
                                             np.abs(P[:, 0]) - F32(L - 0.08), F32(H + 0.02) - P[:, 2]]).astype(F32), (-L, -D - 0.1, H - 0.1), (L, D + 0.1, H + 0.3)), k=0.0)
    box(vs, (0.45, -D - 0.2, 0.42), (0.22, 0.2, 0.42), 0.04)
    box(vs, (0.45, -D - 0.22, 0.87), (0.26, 0.24, 0.035), 0.01, k=0.0, label=5)
    vs.sub(RoundBox((0.45, -D - 0.4, 0.33), (0.14, 0.04, 0.33), 0.01), k=0.0)
    box(gl, (0.45, -D - 0.37, 0.33), (0.14, 0.008, 0.33), 0.004)
    box(vs, (0.45, -D - 0.53, 0.02), (0.25, 0.12, 0.03), 0.01, k=0.0, label=7)
    # the sign on the roof
    sc = v3((-0.35, 0.0, H + 0.62))
    for x in (-0.55, 0.55):
        pole(sg, sc + v3((x, 0.03, -0.45)), sc + v3((x, 0.03, -0.2)), 0.015, label=7)
    box(sg, sc, (0.72, 0.035, 0.22), 0.03, label=5)
    sg.paint(Func(lambda P: (np.abs(np.maximum(np.abs(P[:, 0] - F32(sc[0])) - F32(0.68), np.abs(P[:, 2] - F32(sc[2])) - F32(0.18))) - F32(0.025)).astype(F32),
                  sc - 0.8, sc + 0.8), 9)
    neon_text(ne, sc - v3((0, 0.045, 0)), (1, 0, 0), "DINER", 0.22, 0.013)
    ne.add(Func(lambda P: np.maximum(np.abs(np.maximum(np.abs(P[:, 0] - F32(sc[0])) - F32(0.66), np.abs(P[:, 2] - F32(sc[2])) - F32(0.17))) - F32(0.008),
                                     np.abs(P[:, 1] - F32(sc[1] - 0.045)) - F32(0.008)).astype(F32), sc - 0.8, sc + 0.8), k=0.0)
    for f in (bd, vs):
        ground_cut(f, -0.02)
    out += [("Body", bd, fine(0.008, 0.016), "diner"), ("Windows", wn, fine(0.006, 0.012), "glow_window"), ("Roof", rf, fine(0.008, 0.016), "diner_roof"),
            ("Vestibule", vs, fine(0.006, 0.012), "diner"), ("Doors", gl, fine(0.005, 0.01), "glass"), ("Board", sg, fine(0.006, 0.012), "diner"),
            ("Neon", ne, fine(0.0035, 0.007), "glow_neon_pink")]
    return out


def shops(seed=0):
    """A row of three shop fronts (front toward -Y): a two-storey brick block, the shops' lit windows and doors under
    striped awnings, their fascias, a cyan OPEN sign and a pink BAR sign in neon, sash windows upstairs (a few lit), the
    parapet, air-conditioners and a rooftop sign frame."""
    out = []
    bk, gw, aw, fs, ne1, ne2, gl, fr = (Field(n) for n in ("Brick", "Lit", "Awnings", "Fascia", "NeonA", "NeonB", "Glass", "Frames"))
    W, D, H = 1.6, 0.6, 1.75
    bk.add(walls_box(0, 0, W, D, -0.05, H, batter=0.0, amp=0.003, seed=seed), k=0.0)
    box(bk, (0, 0, H + 0.06), (W + 0.04, D + 0.04, 0.07), 0.01, k=0.003, label=6)
    bk.sub(RoundBox((0, 0, H + 0.2), (W - 0.06, D - 0.06, 0.15), 0.01), k=0.0)
    box(bk, (0, -D - 0.01, 0.9), (W + 0.02, 0.03, 0.03), 0.008, k=0.003, label=6)
    for i, x in enumerate((-1.06, 0.0, 1.06)):
        bk.sub(RoundBox((x, -D, 0.42), (0.44, 0.06, 0.36), 0.01), k=0.0)
        box(gw, (x - 0.08, -D + 0.04, 0.44), (0.32, 0.01, 0.3), 0.0)
        box(gl, (x + 0.33, -D + 0.04, 0.38), (0.08, 0.01, 0.34), 0.0)
        box(fr, (x + 0.24, -D + 0.05, 0.42), (0.012, 0.012, 0.36), 0.004, k=0.0)
        box(fr, (x - 0.08, -D + 0.05, 0.12), (0.32, 0.015, 0.04), 0.006, k=0.0)
        box(fs, (x, -D - 0.03, 0.84), (0.46, 0.025, 0.06), 0.008, label=(5 if i == 0 else (8 if i == 1 else 9)))
        # the awning: a sloping striped canvas with a valance
        a0, a1 = v3((x, -D - 0.02, 0.78)), v3((x, -D - 0.36, 0.6))
        nrm = unit(np.cross(v3((1, 0, 0)), a1 - a0))
        Ra = np.stack([v3((1, 0, 0)), unit(a1 - a0), nrm], axis=1)
        aw.add(RoundBox((a0 + a1) / 2, (0.45, float(np.linalg.norm(a1 - a0)) / 2, 0.01), 0.006, R=Ra), k=0.0)
        aw.add(RoundBox(a1 + v3((0, 0, -0.04)), (0.45, 0.008, 0.045), 0.004), k=0.004)
        lab = 5 if i != 1 else 6
        for j in range(9):
            if j % 2 == 0:
                aw.paint(RoundBox(v3((x - 0.4 + j * 0.1, -D - 0.2, 0.68)), (0.05, 0.3, 0.2), 0.0), lab)
        for sx in (-1, 1):
            pole(aw, a0 + v3((sx * 0.43, 0, 0)), a1 + v3((sx * 0.43, 0, 0)), 0.008)
        for k in range(2):                                          # upstairs sash windows
            q = v3((x - 0.22 + k * 0.44, -D, 1.32))
            bk.sub(RoundBox(q, (0.13, 0.05, 0.22), 0.006), k=0.0)
            lit = (seed + i * 2 + k) % 3 == 0
            (gw if lit else gl).add(RoundBox(q + v3((0, 0.035, 0)), (0.13, 0.008, 0.22), 0.0), k=0.0)
            box(fr, q + v3((0, 0.02, 0)), (0.13, 0.01, 0.012), 0.004, k=0.0)
            box(fr, q + v3((0, 0.02, 0)), (0.012, 0.01, 0.22), 0.004, k=0.0)
            box(bk, q + v3((0, -0.03, -0.24)), (0.16, 0.035, 0.02), 0.006, k=0.003, label=6)
    neon_text(ne1, (-1.14, -D + 0.022, 0.56), (1, 0, 0), "OPEN", 0.12, 0.009)
    neon_text(ne2, (0.98, -D + 0.022, 0.56), (1, 0, 0), "BAR", 0.15, 0.01)
    for (fx, fy) in ((-0.9, 0.2), (0.5, -0.1)):
        box(fs, (fx, fy, H + 0.12), (0.16, 0.12, 0.1), 0.02, label=7)
    for x in (-0.6, 0.6):
        pole(fs, (x, 0.35, H), (x, 0.35, H + 0.7), 0.015, label=7)
    box(fs, (0, 0.35, H + 0.58), (0.75, 0.02, 0.14), 0.01, label=9)
    fs.paint(RoundBox((0.2, 0.33, H + 0.58), (0.4, 0.05, 0.08), 0.0), 8)
    ground_cut(bk, -0.02)
    out += [("Brick", bk, fine(0.008, 0.016), "brick"), ("Lit", gw, fine(0.006, 0.012), "glow_window"), ("Awnings", aw, fine(0.005, 0.01), "awning"),
            ("Fascia", fs, fine(0.005, 0.01), "signs"), ("NeonA", ne1, fine(0.003, 0.006), "glow_neon_cyan"), ("NeonB", ne2, fine(0.003, 0.006), "glow_neon_pink"),
            ("Glass", gl, fine(0.006, 0.012), "glass"), ("Frames", fr, fine(0.004, 0.008), "frames")]
    return out


def billboard(seed=0):
    """A billboard (front toward -Y): the big panel with its poster on two steel legs, the catwalk under it with its
    rail, three lamps on arms lighting it, the frame on its back."""
    out = []
    st, pn, hd, gl = Field("Steel"), Field("Poster"), Field("Lamps"), Field("Lights")
    W, Hb, Z0 = 1.25, 0.55, 2.0
    for x in (-0.55, 0.55):
        box(st, (x, 0.08, Z0 / 2), (0.05, 0.05, Z0 / 2 + 0.05), 0.01)
        box(st, (x, 0.08, 0.05), (0.12, 0.12, 0.05), 0.01, k=0.004, label=7)
    box(st, (0, 0.06, Z0 + Hb), (W + 0.03, 0.05, Hb + 0.03), 0.01)
    box(pn, (0, 0.0, Z0 + Hb), (W, 0.02, Hb), 0.004)
    pn.paint(Ellipsoid((-0.55, 0.0, Z0 + Hb + 0.05), (0.42, 0.2, 0.42)), 5)
    pn.paint(RoundBox((0.45, 0.0, Z0 + Hb + 0.22), (0.6, 0.2, 0.08), 0.0), 9)
    pn.paint(RoundBox((0.3, 0.0, Z0 + Hb - 0.05), (0.45, 0.2, 0.05), 0.0), 9)
    pn.paint(RoundBox((0.6, 0.0, Z0 + 0.2), (0.4, 0.2, 0.09), 0.0), 7)
    pn.paint(Ellipsoid((-0.55, 0.0, Z0 + Hb + 0.05), (0.2, 0.2, 0.2)), 6)
    box(st, (0, -0.2, Z0 - 0.06), (W, 0.18, 0.015), 0.006, k=0.0, label=7)
    for x in np.linspace(-W, W, 9):
        pole(st, (x, -0.37, Z0 - 0.06), (x, -0.37, Z0 + 0.22), 0.007)
    pole(st, (-W, -0.37, Z0 + 0.22), (W, -0.37, Z0 + 0.22), 0.008)
    for x in (-0.8, 0.0, 0.8):
        arm = [v3((x, 0.0, Z0 + 2 * Hb + 0.02)), v3((x, -0.3, Z0 + 2 * Hb + 0.12)), v3((x, -0.5, Z0 + 2 * Hb + 0.08))]
        st.add(Chain(arm, [0.012, 0.012, 0.012], k=0.02), k=0.0)
        flood_head(hd, gl, arm[-1] + v3((0, 0, -0.03)), (0, 0.6, -0.6), s=0.8)
    ground_cut(st, -0.02)
    out += [("Steel", st, fine(0.005, 0.01), "galv"), ("Poster", pn, fine(0.006, 0.012), "poster"), ("Lamps", hd, fine(0.004, 0.008), "steel"),
            ("Lights", gl, fine(0.004, 0.008), "glow_flood")]
    return out


def fountain(seed=0):
    """A plaza fountain: a round stone basin with a moulded rim, its water, a fluted pedestal carrying two bowls, water
    spilling from the upper bowl and a jet from the top, lights under the water's surface round the rim."""
    out = []
    st, wt, lt = Field("Stone"), Field("Water"), Field("Lights")
    R = 0.78
    st.add(Cylinder((0, 0, 0.1), R + 0.08, 0.2, rr=0.03), k=0.0)
    st.add(Torus((0, 0, 0.21), R + 0.03, 0.055), k=0.01)
    st.sub(Cylinder((0, 0, 0.3), R - 0.02, 0.36), k=0.01)
    st.add(Cylinder((0, 0, 0.02), R + 0.2, 0.04, rr=0.015), k=0.01)
    st.add(RoundCone((0, 0, 0.0), (0, 0, 0.55), 0.13, 0.08, disp=lambda P: (F32(0.006) * np.cos(np.arctan2(P[:, 1], P[:, 0]) * F32(12))).astype(F32), disp_amp=0.007), k=0.03)
    for (z, r) in ((0.55, 0.36), (0.92, 0.2)):
        st.add(Func(lambda P, z=z, r=r: np.maximum(np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2 + ((P[:, 2] - F32(z + r * 0.55)) * F32(1.8)) ** 2) - F32(r)) - F32(0.025),
                                                  P[:, 2] - F32(z + r * 0.4)).astype(F32), (-r - 0.1, -r - 0.1, z - 0.3), (r + 0.1, r + 0.1, z + 0.4)), k=0.02)
        wt.add(Cylinder((0, 0, z + r * 0.36), r - 0.03, 0.02), k=0.0)
    st.add(RoundCone((0, 0, 0.6), (0, 0, 0.95), 0.06, 0.045), k=0.02)
    wt.add(Cylinder((0, 0, 0.14), R - 0.02, 0.04), k=0.0)
    for (z, r) in ((0.55, 0.36), (0.92, 0.2)):                       # sheets of water spilling over the bowls' lips
        wt.add(Func(lambda P, z=z, r=r: np.maximum.reduce([np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(r + 0.02) - (F32(z + r * 0.38) - P[:, 2]) * F32(0.15)) - F32(0.012),
                                                          P[:, 2] - F32(z + r * 0.38), F32(0.16 if z < 0.7 else 0.58) - P[:, 2]]).astype(F32),
                    (-r - 0.2, -r - 0.2, 0.1), (r + 0.2, r + 0.2, z + 0.3)), k=0.0)
    wt.add(RoundCone((0, 0, 1.0), (0, 0, 1.38), 0.035, 0.012), k=0.02)
    wt.add(Sphere((0, 0, 1.36), 0.035), k=0.02)
    for i in range(8):
        a = 2 * math.pi * i / 8
        lt.add(Sphere((math.cos(a) * (R - 0.08), math.sin(a) * (R - 0.08), 0.15), 0.03), k=0.0)
    ground_cut(st, -0.02)
    out += [("Stone", st, fine(0.006, 0.012), "stone"), ("Water", wt, fine(0.005, 0.01), "fountain_water"), ("Lights", lt, fine(0.004, 0.008), "glow_neon_cyan")]
    return out


def city_bus(seed=0):
    """A city bus (nose toward +X): a long white box with its blue band, the windows lit all along, the windscreen and
    the lit route sign over it, two doors, the roof's air-conditioning pod, six wheels' worth of arches (two axles)."""
    out = []
    bd, wn, gl, tf, hf, sg, tl = (Field(n) for n in ("Body", "Windows", "Glass", "Tyres", "Hubs", "Route", "Tail"))
    L, W, H = 1.55, 0.42, 1.0
    rw = 0.15
    box(bd, (0, 0, (H + 0.12) / 2), (L, W, (H - 0.12) / 2), 0.07)
    box(bd, (-0.3, 0, H + 0.06), (0.5, 0.3, 0.06), 0.04, k=0.03)
    bd.paint(Func(lambda P: (np.abs(P[:, 2] - F32(0.38)) - F32(0.06)).astype(F32), (-2, -1, 0), (2, 1, 1.2)), 5)
    for sy in (-1, 1):
        bd.sub(RoundBox((-0.15, sy * W, 0.72), (L - 0.35, 0.03, 0.17), 0.02), k=0.0)
        box(wn, (-0.15, sy * (W - 0.02), 0.72), (L - 0.35, 0.008, 0.17), 0.0)
        for x in np.linspace(-L + 0.25, L - 0.55, 7):
            box(bd, (x, sy * (W - 0.012), 0.72), (0.022, 0.012, 0.17), 0.004, k=0.0, label=7)
    bd.sub(RoundBox((L, 0, 0.66), (0.04, W - 0.04, 0.24), 0.03), k=0.0)
    box(gl, (L - 0.02, 0, 0.66), (0.01, W - 0.04, 0.24), 0.01)
    box(sg, (L - 0.01, 0, 0.94), (0.012, W - 0.1, 0.035), 0.006)
    for x in (L - 0.32, 0.0):
        bd.sub(RoundBox((x, -W, 0.5), (0.13, 0.03, 0.36), 0.01), k=0.0)
        box(gl, (x, -W + 0.02, 0.5), (0.13, 0.008, 0.36), 0.0)
    for sy in (-1, 1):
        tl.add(RoundBox((-L + 0.005, sy * (W - 0.06), 0.35), (0.012, 0.03, 0.07), 0.008), k=0.0)
    box(bd, (L + 0.01, 0, 0.12), (0.03, W + 0.01, 0.05), 0.02, k=0.004, label=7)
    for x in (L * 0.62, -L * 0.6):
        for sy in (-1, 1):
            bd.sub(Cylinder((x, sy * (W - 0.02), rw), rw + 0.025, 0.2, R=RY), k=0.02)
            wheel(tf, hf, (x, sy * (W - 0.07), rw), (0, sy, 0), rw, 0.11, lugs=6)
    ground_cut(tf, -0.01)
    out += [("Body", bd, fine(0.008, 0.016), "bus"), ("Windows", wn, fine(0.006, 0.012), "glow_window"), ("Glass", gl, fine(0.006, 0.012), "glass"),
            ("Tyres", tf, fine(0.005, 0.01), "rubber"), ("Hubs", hf, fine(0.004, 0.008), "chrome"), ("Route", sg, fine(0.004, 0.008), "glow_amber"),
            ("Tail", tl, fine(0.004, 0.008), "glow_red")]
    return out


def taxi(seed=0):
    """A yellow cab (nose toward +X): its checker band and roof sign, lamps lit."""
    return car([], L=1.45, W=0.64, H=0.54, rw=0.13, paint="taxi", seed=seed, lit=True, kind="taxi")


# ------------------------------------------------------------------------------------------------ Downtown: no-build zones
def midrise(seed=0):
    """A mid-rise block (front toward -Y): five storeys of brick over a stone ground floor of shop windows, rows of
    windows (some lit), a cornice, a fire escape down one side, and on the roof a wooden water tank on its steel legs,
    a stair bulkhead and air-conditioners."""
    out = []
    bk, st, gw, gl, wt, ir, rf = (Field(n) for n in ("Brick", "Stone", "Lit", "Glass", "Tank", "Iron", "Roof"))
    W, D, H = 1.2, 0.9, 3.3
    bk.add(walls_box(0, 0, W, D, 0.5, H, batter=0.0, amp=0.003, seed=seed), k=0.0)
    box(st, (0, 0, 0.27), (W + 0.02, D + 0.02, 0.28), 0.01)
    box(st, (0, 0, H + 0.05), (W + 0.07, D + 0.07, 0.06), 0.01)
    box(st, (0, 0, 0.56), (W + 0.04, D + 0.04, 0.03), 0.008, k=0.003)
    box(bk, (0, 0, H + 0.14), (W + 0.02, D + 0.02, 0.08), 0.01, k=0.0)
    bk.sub(RoundBox((0, 0, H + 0.26), (W - 0.05, D - 0.05, 0.13), 0.01), k=0.0)
    rng = np.random.default_rng(seed)
    for (nx, ny, hw) in ((0, -1, W), (0, 1, W), (-1, 0, D), (1, 0, D)):
        sx, sy = (1, 0) if nx == 0 else (0, 1)
        ncol = 5 if nx == 0 else 4
        for j, z in enumerate((0.92, 1.42, 1.92, 2.42, 2.92)):
            for i in range(ncol):
                u = -hw + (i + 0.5) * 2 * hw / ncol
                q = v3((nx * W + sx * u, ny * D + sy * u, z))
                half = (abs(sx) * 0.1 + abs(nx) * 0.05, abs(sy) * 0.1 + abs(ny) * 0.05, 0.16)
                bk.sub(RoundBox(q, half, 0.006), k=0.0)
                box(bk, q + v3((nx * 0.02, ny * 0.02, -0.18)), (abs(sx) * 0.12 + abs(nx) * 0.03, abs(sy) * 0.12 + abs(ny) * 0.03, 0.018), 0.005, k=0.002, label=6)
                if rng.random() < 0.3:
                    gw.add(RoundBox(q - v3((nx * 0.03, ny * 0.03, 0)), (abs(sx) * 0.1 + abs(nx) * 0.006, abs(sy) * 0.1 + abs(ny) * 0.006, 0.16), 0.0), k=0.0)
        # the dark glass behind every window of this face
        gl.add(RoundBox(v3((nx * (W - 0.035), ny * (D - 0.035), 1.92)), (abs(sx) * (hw - 0.05) + abs(nx) * 0.006, abs(sy) * (hw - 0.05) + abs(ny) * 0.006, 1.2), 0.0), k=0.0)
        # ground floor shop windows
        st.sub(RoundBox(v3((nx * W, ny * D, 0.27)), (abs(sx) * (hw - 0.15) + abs(nx) * 0.05, abs(sy) * (hw - 0.15) + abs(ny) * 0.05, 0.2), 0.006), k=0.0)
        gw.add(RoundBox(v3((nx * (W - 0.035), ny * (D - 0.035), 0.27)), (abs(sx) * (hw - 0.15) + abs(nx) * 0.006, abs(sy) * (hw - 0.15) + abs(ny) * 0.006, 0.2), 0.0), k=0.0)
    # fire escape on the +X side
    for z in (1.15, 1.65, 2.15, 2.65, 3.1):
        box(ir, (W + 0.16, 0, z - 0.17), (0.15, 0.4, 0.012), 0.004)
        pole(ir, (W + 0.31, -0.4, z - 0.16), (W + 0.31, 0.4, z - 0.16 + 0.0), 0.006)
        pole(ir, (W + 0.31, -0.4, z + 0.05), (W + 0.31, 0.4, z + 0.05), 0.007)
        for y in (-0.4, 0.0, 0.4):
            pole(ir, (W + 0.31, y, z - 0.16), (W + 0.31, y, z + 0.05), 0.006)
        if z < 3.0:
            pole(ir, (W + 0.12, -0.32, z - 0.15), (W + 0.12, 0.25, z + 0.33), 0.01)
            pole(ir, (W + 0.24, -0.32, z - 0.15), (W + 0.24, 0.25, z + 0.33), 0.01)
    # the roof: water tank, bulkhead, air-conditioners
    tc = v3((-0.45, 0.25, H + 0.05))
    for sx in (-1, 1):
        for sy in (-1, 1):
            pole(ir, tc + v3((sx * 0.18, sy * 0.18, 0)), tc + v3((sx * 0.18, sy * 0.18, 0.45)), 0.015)
    box(ir, tc + Z * 0.46, (0.24, 0.24, 0.015), 0.006)
    wt.add(Cylinder(tc + Z * 0.72, 0.26, 0.5, rr=0.01, disp=lambda P: (F32(0.003) * np.cos(np.arctan2(P[:, 1] - F32(tc[1]), P[:, 0] - F32(tc[0])) * F32(40))).astype(F32), disp_amp=0.004), k=0.0, label=11)
    for z in (0.56, 0.72, 0.88):
        wt.add(Torus(tc + Z * z, 0.265, 0.008), k=0.003, label=6)
    wt.add(cone((tc[0], tc[1]), H + 0.05 + 0.96, H + 0.05 + 1.2, 0.29, 0.02), k=0.01, label=10)
    box(rf, (0.5, -0.3, H + 0.25), (0.25, 0.22, 0.22), 0.02)
    for (x, y) in ((0.25, 0.5), (0.7, 0.45)):
        box(rf, (x, y, H + 0.13), (0.14, 0.1, 0.1), 0.02, label=7)
    for f in (bk, st):
        ground_cut(f, -0.02)
    out += [("Brick", bk, fine(0.01, 0.02), "brick"), ("Stone", st, fine(0.008, 0.016), "stone"), ("Lit", gw, fine(0.006, 0.012), "glow_window"),
            ("Glass", gl, fine(0.008, 0.016), "glass"), ("Tank", wt, fine(0.006, 0.012), "tank_wood"), ("Iron", ir, fine(0.004, 0.008), "street_iron"),
            ("Roof", rf, fine(0.008, 0.016), "concrete")]
    return out


# ------------------------------------------------------------------------------------------------ Suburbia: houses
def _window(wf, gl, tr, c, nrm, w, h, shutters=True, lit=None):
    """A double-hung window in a sided wall (field wf; outward normal nrm horizontal): the opening, its glass (gl, or
    `lit`), white trim and muntins (tr), black shutters either side (label 7 on the wall's field)."""
    nn = unit(v3((nrm[0], nrm[1], 0.0)))
    s = v3((nn[1], -nn[0], 0.0))
    R = np.stack([s, nn, Z], axis=1)
    c = v3(c)
    wf.sub(RoundBox(c, (w / 2, 0.04, h / 2), 0.004, R=R), k=0.0)
    (lit if lit is not None else gl).add(RoundBox(c - nn * 0.025, (w / 2, 0.006, h / 2), 0.0, R=R), k=0.0)
    tr.add(Func(lambda P, c=c, R=R: (lambda Q: np.maximum(np.abs(np.maximum(np.abs(Q[:, 0]) - F32(w / 2 + 0.01), np.abs(Q[:, 2]) - F32(h / 2 + 0.01))) - F32(0.018),
                                                         np.abs(Q[:, 1]) - F32(0.016)).astype(F32))(((P - F32(c)) @ F32(R)).astype(F32)), c - 0.5, c + 0.5), k=0.0)
    tr.add(RoundBox(c - nn * 0.015, (w / 2, 0.008, 0.008), 0.003, R=R), k=0.0)
    tr.add(RoundBox(c - nn * 0.015, (0.007, 0.008, h / 2), 0.003, R=R), k=0.0)
    tr.add(RoundBox(c + nn * 0.01 - Z * (h / 2 + 0.025), (w / 2 + 0.035, 0.03, 0.012), 0.004, R=R), k=0.002)
    if shutters:
        for sg in (-1, 1):
            wf.add(RoundBox(c + s * (sg * (w / 2 + 0.055)) + nn * 0.01, (0.04, 0.008, h / 2 + 0.01), 0.004, R=R), k=0.0, label=7)


def _door(wf, gl, tr, c, nrm, w=0.2, h=0.4, label=8, glass=True):
    """A front door (its foot at c) in a sided wall: painted panels (label), a fanlight, white trim, a brass knob."""
    nn = unit(v3((nrm[0], nrm[1], 0.0)))
    s = v3((nn[1], -nn[0], 0.0))
    R = np.stack([s, nn, Z], axis=1)
    c = v3(c)
    m = c + Z * (h / 2)
    wf.sub(RoundBox(m, (w / 2, 0.04, h / 2), 0.004, R=R), k=0.0)
    wf.add(RoundBox(m - nn * 0.025, (w / 2, 0.01, h / 2), 0.004, R=R), k=0.0, label=label)
    for zz in (-0.22, 0.12):
        wf.add(RoundBox(m - nn * 0.012 + Z * (h * zz), (w * 0.32, 0.006, h * 0.16), 0.004, R=R), k=0.002, label=label)
    if glass:
        gl.add(RoundBox(m + Z * (h / 2 + 0.035) - nn * 0.01, (w / 2, 0.006, 0.025), 0.0, R=R), k=0.0)
    tr.add(Func(lambda P, R=R: (lambda Q: np.maximum.reduce([np.abs(np.maximum(np.abs(Q[:, 0]) - F32(w / 2 + 0.01), np.abs(Q[:, 2] - F32(h / 2 + 0.03)) - F32(h / 2 + 0.04))) - F32(0.02),
                                                             np.abs(Q[:, 1]) - F32(0.016), -Q[:, 2]]).astype(F32))(((P - F32(c)) @ F32(R)).astype(F32)), c - 0.6, c + 0.8), k=0.0)
    tr.add(Sphere(m + s * (w * 0.32) + nn * (-0.005), 0.012), k=0.0)


def _garage_door(wf, tr, c, nrm, w=0.6, h=0.55):
    """A garage door: white raised panels in four rows, its trim."""
    nn = unit(v3((nrm[0], nrm[1], 0.0)))
    s = v3((nn[1], -nn[0], 0.0))
    R = np.stack([s, nn, Z], axis=1)
    c = v3(c)
    m = c + Z * (h / 2)
    wf.sub(RoundBox(m, (w / 2, 0.04, h / 2), 0.004, R=R), k=0.0)
    tr.add(RoundBox(m - nn * 0.025, (w / 2, 0.012, h / 2), 0.004, R=R), k=0.0)
    for j in range(4):
        for i in range(4):
            q = m - nn * 0.012 + s * ((i - 1.5) * w / 4) + Z * ((j - 1.5) * h / 4)
            tr.add(RoundBox(q, (w / 8 - 0.015, 0.006, h / 8 - 0.015), 0.006, R=R), k=0.002)
    tr.add(Func(lambda P, R=R: (lambda Q: np.maximum.reduce([np.abs(np.maximum(np.abs(Q[:, 0]) - F32(w / 2 + 0.01), np.abs(Q[:, 2] - F32(h / 2)) - F32(h / 2 + 0.01))) - F32(0.022),
                                                             np.abs(Q[:, 1]) - F32(0.016), -Q[:, 2]]).astype(F32))(((P - F32(c)) @ F32(R)).astype(F32)), c - 0.7, c + 0.8), k=0.0)


def _roof_gable(rf, wf, c, half_len, half_w, z_eave, z_ridge, axis="x", over=0.09):
    """A shingled gable roof (field rf) over a block, its gable ends filled (field wf: the siding), white fascia boards
    along its eaves and verges (label 5 of rf, the ridge cap 5 too)."""
    cx, cy = float(c[0]), float(c[1])
    s = (z_ridge - z_eave) / half_w
    zr = z_ridge + over * s
    rf.add(gable((cx, cy), half_len + over, half_w + over, z_eave - 0.035, zr, axis=axis), k=0.0)
    rf.sub(gable((cx, cy), half_len + over + 0.1, half_w + over - 0.035 * 1.6, z_eave - 0.12, zr - 0.065, axis=axis), k=0.0)
    L = half_len + over
    hx, hy = (L, 0.03) if axis == "x" else (0.03, L)
    rf.add(RoundBox((cx, cy, zr + 0.004), (hx, hy, 0.022), 0.012), k=0.004, label=7)
    wf.add(gable((cx, cy), half_len, half_w, z_eave - 0.05, z_ridge - 0.02, axis=axis), k=0.0)
    return zr


def _chimney(bk, c, z0, z1, hx=0.1, hy=0.12):
    bk.add(walls_box(c[0], c[1], hx, hy, z0, z1, batter=0.0, amp=0.003, seed=3), k=0.0)
    bk.add(RoundBox((c[0], c[1], z1 + 0.02), (hx + 0.02, hy + 0.02, 0.025), 0.006), k=0.003, label=5)
    bk.sub(RoundBox((c[0], c[1], z1 + 0.06), (hx - 0.04, hy - 0.05, 0.06), 0.004), k=0.0)


def mailbox(seed=0, o=(0, 0, 0), yaw=0.0):
    """A rural mailbox on its white post, the red flag up."""
    ps, mb = Field("Post"), Field("Mailbox")
    box(ps, (0, 0, 0.2), (0.025, 0.025, 0.24), 0.006)
    box(ps, (0, 0, 0.42), (0.11, 0.04, 0.012), 0.004)
    mb.add(Func(lambda P: np.maximum.reduce([np.minimum(np.sqrt(P[:, 1] ** 2 + np.maximum(P[:, 2] - F32(0.5), 0) ** 2), F32(1)) - F32(0.06),
                                             np.abs(P[:, 0]) - F32(0.13), F32(0.435) - P[:, 2]]).astype(F32), (-0.2, -0.1, 0.4), (0.2, 0.1, 0.6)), k=0.0)
    mb.add(RoundBox((0.13, 0, 0.5), (0.008, 0.062, 0.07), 0.004), k=0.002, label=7)
    mb.add(RoundBox((-0.02, 0.064, 0.62), (0.008, 0.004, 0.06), 0.002), k=0.0, label=8)
    mb.add(RoundBox((0.02, 0.064, 0.66), (0.04, 0.004, 0.025), 0.002), k=0.0, label=8)
    ground_cut(ps, -0.02)
    parts = [("Post", ps, fine(0.004, 0.008), "picket"), ("Mailbox", mb, fine(0.004, 0.008), "mailbox")]
    return place_parts([], parts, o, Rz(yaw))


def colonial(seed=0, drive=True, siding="siding_a"):
    """A two-storey house (front toward -Y): pale blue clapboard, white trim, black shutters, a shingled gable roof and
    a brick chimney up its end; a porch on white columns along the front with its steps and a red door; the garage at
    its side with a white panelled door, the minivan parked on the driveway in front, the mailbox at its end."""
    out = []
    sd, rf, tr, gl, bk, pc = (Field(n) for n in ("Siding", "Roof", "Trim", "Glass", "Chimney", "Porch"))
    X0, X1, Y0, Y1, H = -0.8, 0.7, -0.5, 0.5, 1.45
    sd.add(walls_box((X0 + X1) / 2, 0, (X1 - X0) / 2, Y1, -0.05, H, batter=0.0, amp=0.002, seed=seed), k=0.0)
    sd.paint(Func(lambda P: (P[:, 2] - F32(0.1)).astype(F32), (-3, -3, -0.2), (3, 3, 0.3)), 6)
    _roof_gable(rf, sd, ((X0 + X1) / 2, 0), (X1 - X0) / 2, Y1, H, H + 0.55, axis="x")
    for x in (-0.5, -0.05, 0.4):                                     # upstairs
        _window(sd, gl, tr, (x, Y0, 1.08), (0, -1, 0), 0.17, 0.28)
    for x in (0.35,):
        _window(sd, gl, tr, (x, Y0, 0.44), (0, -1, 0), 0.17, 0.28)
    _window(sd, gl, tr, (-0.55, Y0, 0.44), (0, -1, 0), 0.17, 0.28)
    _door(sd, gl, tr, (-0.15, Y0, 0.12), (0, -1, 0))
    for x in (-0.45, 0.2):
        _window(sd, gl, tr, (x, Y1, 0.44), (0, 1, 0), 0.17, 0.28, shutters=False)
        _window(sd, gl, tr, (x, Y1, 1.08), (0, 1, 0), 0.17, 0.28, shutters=False)
    _window(sd, gl, tr, (X0, 0.0, 1.08), (-1, 0, 0), 0.17, 0.28)
    tr.add(RoundBox((X0 + 0.0, 0, 0.78), (0.03, Y1 + 0.02, 0.02), 0.006), k=0.0)
    for sx in (X0, X1):
        for sy in (Y0, Y1):
            tr.add(RoundBox((sx, sy, H / 2), (0.025, 0.025, H / 2), 0.006), k=0.0)
    _chimney(bk, (X0 - 0.08, 0.0), -0.05, H + 0.75)
    # the porch: deck, steps, columns, its shed roof
    PX0, PX1, PY = -0.78, 0.2, -0.85
    box(pc, ((PX0 + PX1) / 2, (Y0 + PY) / 2, 0.08), ((PX1 - PX0) / 2, (Y0 - PY) / 2, 0.04), 0.01, label=10)
    for k in range(2):
        box(pc, (-0.15, PY - 0.06 - k * 0.08, 0.06 - k * 0.03), (0.16, 0.05, 0.03 - k * 0.005), 0.008, label=10)
    for x in np.linspace(PX0 + 0.04, PX1 - 0.04, 4):
        tr.add(Cylinder((x, PY + 0.04, 0.45), 0.025, 0.7, rr=0.008), k=0.0)
        tr.add(RoundBox((x, PY + 0.04, 0.13), (0.035, 0.035, 0.02), 0.006), k=0.004)
    for (xa, xb) in ((PX0 + 0.04, -0.28), (-0.02, PX1 - 0.04)):
        tr.add(RoundBox(((xa + xb) / 2, PY + 0.04, 0.3), ((xb - xa) / 2, 0.01, 0.012), 0.004), k=0.0)
        for x in np.arange(xa + 0.04, xb, 0.05):
            tr.add(RoundBox((x, PY + 0.04, 0.21), (0.006, 0.006, 0.08), 0.002), k=0.0)
    rf.add(convex([((0, Y0, 0.88), (0, -0.3, 1)), ((0, Y0, 0.84), (0, 0.3, -1)), ((PX0 - 0.08, 0, 0), (-1, 0, 0)), ((PX1 + 0.08, 0, 0), (1, 0, 0)),
                   ((0, PY - 0.1, 0), (0, -1, 0)), ((0, Y0 + 0.02, 0), (0, 1, 0))], (PX0 - 0.2, PY - 0.2, 0.6), (PX1 + 0.2, Y0 + 0.1, 1.0)), k=0.0)
    tr.add(RoundBox(((PX0 + PX1) / 2, PY + 0.04, 0.79), ((PX1 - PX0) / 2 + 0.02, 0.03, 0.025), 0.006), k=0.0)
    # the garage
    GX0, GX1, GY0, GY1, GH = X1, X1 + 0.82, -0.42, 0.45, 0.72
    sd.add(walls_box((GX0 + GX1) / 2, (GY0 + GY1) / 2, (GX1 - GX0) / 2, (GY1 - GY0) / 2, -0.05, GH, batter=0.0, amp=0.002, seed=seed + 1), k=0.0)
    _roof_gable(rf, sd, ((GX0 + GX1) / 2 - 0.02, (GY0 + GY1) / 2), (GX1 - GX0) / 2 + 0.02, (GY1 - GY0) / 2, GH, GH + 0.38, axis="x")
    _garage_door(sd, tr, ((GX0 + GX1) / 2, GY0, 0.0), (0, -1, 0), 0.62, 0.55)
    for sx in (GX0 + 0.12, GX1 - 0.12):
        tr.add(RoundBox((sx, GY0 - 0.02, 0.62), (0.025, 0.02, 0.035), 0.006), k=0.0)
    # driveway and front walk
    dw = Field("Drive")
    dw.add(RoundBox(((GX0 + GX1) / 2, GY0 - 0.95, 0.0), (0.42, 0.95, 0.025), 0.01), k=0.0)
    dw.add(RoundBox((-0.15, PY - 0.55, 0.0), (0.12, 0.42, 0.022), 0.01), k=0.0)
    if not drive:                                                   # (where the ground draws the drive: the house alone,
        dw = None                                                    # centred on its footprint)
    for f in (sd, bk, pc) + ((dw,) if dw is not None else ()):
        ground_cut(f, -0.03)
    out += [("Siding", sd, fine(0.008, 0.016), siding), ("Roof", rf, fine(0.008, 0.016), "shingles"), ("Trim", tr, fine(0.005, 0.01), "trim"),
            ("Glass", gl, fine(0.006, 0.012), "glass"), ("Chimney", bk, fine(0.006, 0.012), "brick"), ("Porch", pc, fine(0.006, 0.012), "deck")]
    if not drive:
        return place_parts([], out, (-0.33, 0.17, 0.0))
    out.append(("Drive", dw, fine(0.01, 0.02), "concrete"))
    car(out, L=1.45, W=0.66, H=0.62, rw=0.13, paint="minivan", seed=seed, kind="van", name="Van", o=((GX0 + GX1) / 2, GY0 - 1.0, 0.0), yaw=math.pi / 2)
    place_parts(out, mailbox(seed), ((GX0 + GX1) / 2 + 0.55, GY0 - 1.75, 0.0), Rz(math.pi))
    return out


def ranch(seed=0, drive=True, siding="siding_b"):
    """A ranch house (front toward -Y): one long storey in butter-yellow clapboard under a low hipped roof, a picture
    window and two pairs of windows with shutters, a stoop under a little gable on two columns, the garage door at its
    end, a brick chimney through the roof, a planter of shrubs under the window."""
    out = []
    sd, rf, tr, gl, bk, pc, sh = (Field(n) for n in ("Siding", "Roof", "Trim", "Glass", "Chimney", "Stoop", "Shrubs"))
    W, D, H = 1.25, 0.55, 0.72
    sd.add(walls_box(0, 0, W, D, -0.05, H, batter=0.0, amp=0.002, seed=seed), k=0.0)
    sd.paint(Func(lambda P: (P[:, 2] - F32(0.1)).astype(F32), (-3, -3, -0.2), (3, 3, 0.3)), 6)
    hipped(rf, (0, 0), W, D, H, H + 0.45, over=0.12)
    tr.add(Func(lambda P: np.maximum(np.abs(np.maximum(np.abs(P[:, 0]) - F32(W + 0.1), np.abs(P[:, 1]) - F32(D + 0.1))) - F32(0.02),
                                     np.abs(P[:, 2] - F32(H - 0.0)) - F32(0.035)).astype(F32), (-W - 0.2, -D - 0.2, H - 0.1), (W + 0.2, D + 0.2, H + 0.1)), k=0.0)
    _window(sd, gl, tr, (-0.55, -D, 0.42), (0, -1, 0), 0.5, 0.32, shutters=False)
    for x in (-1.0, 0.1):
        _window(sd, gl, tr, (x, -D, 0.44), (0, -1, 0), 0.16, 0.26)
    _door(sd, gl, tr, (-0.2, -D, 0.06), (0, -1, 0), w=0.18, h=0.42, label=5)
    _garage_door(sd, tr, (0.78, -D, 0.0), (0, -1, 0), 0.6, 0.55)
    for x in (-0.8, 0.0, 0.8):
        _window(sd, gl, tr, (x, D, 0.44), (0, 1, 0), 0.16, 0.26, shutters=False)
    for sx in (-W, W):
        for sy in (-D, D):
            tr.add(RoundBox((sx, sy, H / 2), (0.022, 0.022, H / 2), 0.006), k=0.0)
    box(pc, (-0.2, -D - 0.18, 0.05), (0.2, 0.18, 0.05), 0.01)
    box(pc, (-0.2, -D - 0.4, 0.025), (0.16, 0.06, 0.025), 0.008)
    for sx in (-1, 1):
        tr.add(Cylinder((-0.2 + sx * 0.17, -D - 0.32, 0.4), 0.02, 0.62, rr=0.006), k=0.0)
    rf.add(gable((-0.2, -D - 0.2), 0.22, 0.24, 0.7, 0.9, axis="y"), k=0.0)
    _chimney(bk, (0.35, 0.15), H - 0.1, H + 0.6)
    if drive:
        pc.add(RoundBox((0.78, -D - 0.85, 0.0), (0.36, 0.85, 0.025), 0.01), k=0.0)
        pc.add(RoundBox((-0.2, -D - 0.75, 0.0), (0.1, 0.32, 0.022), 0.01), k=0.0)
    rng = np.random.default_rng(seed)
    for i in range(6):
        q = v3((-0.98 + i * 0.12, -D - 0.12, 0.08))
        sh.add(Ellipsoid(q, (0.08, 0.07, 0.09), **wob(18.0, 0.012, seed + i)), k=0.03)
    for f in (sd, bk, pc, sh):
        ground_cut(f, -0.03)
    out += [("Siding", sd, fine(0.008, 0.016), siding), ("Roof", rf, fine(0.008, 0.016), "shingles_b"), ("Trim", tr, fine(0.005, 0.01), "trim"),
            ("Glass", gl, fine(0.006, 0.012), "glass"), ("Chimney", bk, fine(0.006, 0.012), "brick"), ("Stoop", pc, fine(0.008, 0.016), "concrete"),
            ("Shrubs", sh, fine(0.008, 0.016), "hedge")]
    return out


def hipped(rf, c, hx, hy, z_eave, z_top, over=0.1):
    """A hipped shingle roof over a box (half sizes hx >= hy), its ridge along X (the ridge cap: label 7)."""
    cx, cy = float(c[0]), float(c[1])
    hx, hy = hx + over, hy + over
    s = (z_top - z_eave) / hy
    planes = [((cx, cy + hy, z_eave), (0, 1, 1 / s)), ((cx, cy - hy, z_eave), (0, -1, 1 / s)),
              ((cx + hx, cy, z_eave), (1, 0, 1 / s)), ((cx - hx, cy, z_eave), (-1, 0, 1 / s)), ((cx, cy, z_eave - 0.035), (0, 0, -1))]
    rf.add(convex(planes, (cx - hx - 0.1, cy - hy - 0.1, z_eave - 0.1), (cx + hx + 0.1, cy + hy + 0.1, z_top + 0.1)), k=0.0)
    if hx > hy + 0.02:
        rf.add(RoundBox((cx, cy, z_top - 0.005), (hx - hy, 0.028, 0.022), 0.012), k=0.004, label=7)


def cape_cod(seed=0):
    """A cape-cod house (front toward -Y): one and a half storeys in sage-green clapboard under a steep shingled roof
    with two dormers, a white portico over the door, shuttered windows either side, a brick chimney at its end."""
    out = []
    sd, rf, tr, gl, bk, pc = (Field(n) for n in ("Siding", "Roof", "Trim", "Glass", "Chimney", "Walk"))
    W, D, H = 0.85, 0.55, 0.72
    sd.add(walls_box(0, 0, W, D, -0.05, H, batter=0.0, amp=0.002, seed=seed), k=0.0)
    sd.paint(Func(lambda P: (P[:, 2] - F32(0.1)).astype(F32), (-3, -3, -0.2), (3, 3, 0.3)), 6)
    zr = _roof_gable(rf, sd, (0, 0), W, D, H, H + 0.75, axis="x")
    for x in (-0.55, -0.3, 0.3, 0.55):
        _window(sd, gl, tr, (x, -D, 0.44), (0, -1, 0), 0.15, 0.26)
    _door(sd, gl, tr, (0.0, -D, 0.08), (0, -1, 0), w=0.19, h=0.42, label=8)
    for x in (-0.6, 0.0, 0.6):
        _window(sd, gl, tr, (x, D, 0.44), (0, 1, 0), 0.15, 0.26, shutters=False)
    # dormers: little gabled boxes out of the front slope
    for x in (-0.42, 0.42):
        dz0 = H + 0.2
        sd.add(RoundBox((x, -0.18, dz0 + 0.17), (0.17, 0.22, 0.17), 0.006), k=0.0)
        rf.add(gable((x, -0.2), 0.27, 0.22, dz0 + 0.32, dz0 + 0.5, axis="y"), k=0.0)
        _window(sd, gl, tr, (x, -0.4, dz0 + 0.17), (0, -1, 0), 0.13, 0.2, shutters=False)
    # portico
    box(pc, (0.0, -D - 0.17, 0.04), (0.22, 0.17, 0.04), 0.01)
    for sx in (-1, 1):
        tr.add(Cylinder((sx * 0.17, -D - 0.28, 0.4), 0.02, 0.66, rr=0.006), k=0.0)
    rf.add(gable((0.0, -D - 0.18), 0.2, 0.26, 0.72, 0.92, axis="y"), k=0.0)
    tr.add(RoundBox((0.0, -D - 0.36, 0.72), (0.27, 0.02, 0.025), 0.006), k=0.0)
    pc.add(RoundBox((0.0, -D - 0.8, 0.0), (0.12, 0.45, 0.022), 0.01), k=0.0)
    for sx in (-W, W):
        for sy in (-D, D):
            tr.add(RoundBox((sx, sy, H / 2), (0.022, 0.022, H / 2), 0.006), k=0.0)
    _chimney(bk, (W + 0.06, 0.0), -0.05, zr + 0.3)
    for f in (sd, bk, pc):
        ground_cut(f, -0.03)
    out += [("Siding", sd, fine(0.008, 0.016), "siding_c"), ("Roof", rf, fine(0.008, 0.016), "shingles"), ("Trim", tr, fine(0.005, 0.01), "trim"),
            ("Glass", gl, fine(0.006, 0.012), "glass"), ("Chimney", bk, fine(0.006, 0.012), "brick"), ("Walk", pc, fine(0.008, 0.016), "concrete")]
    return out


def minivan(seed=0):
    """A family minivan (nose toward +X) in metallic blue."""
    return car([], L=1.45, W=0.66, H=0.62, rw=0.13, paint="minivan", seed=seed, kind="van")


# ------------------------------------------------------------------------------------------------ Suburbia: garden scatter
def picket_fence(seed=0, L=1.2):
    """A section of white picket fence: two square posts with caps, two rails, pointed pickets."""
    f = Field("Fence")
    for x in (-L / 2, L / 2):
        box(f, (x, 0, 0.27), (0.03, 0.03, 0.3), 0.006)
        f.add(pyramid_roof((x, 0), 0.04, 0.57, 0.62), k=0.004)
    for z in (0.14, 0.42):
        box(f, (0, 0.03, z), (L / 2, 0.012, 0.02), 0.004)
    for x in np.arange(-L / 2 + 0.07, L / 2 - 0.04, 0.085):
        f.add(convex([((x, 0.065, 0), (0, 1, 0)), ((x, 0.04, 0), (0, -1, 0)), ((x + 0.025, 0, 0), (1, 0, 0)), ((x - 0.025, 0, 0), (-1, 0, 0)),
                      ((x, 0, 0.5), (1, 0, 1.0)), ((x, 0, 0.5), (-1, 0, 1.0)), ((x, 0, -0.04), (0, 0, -1))], (x - 0.1, -0.1, -0.1), (x + 0.1, 0.2, 0.6)), k=0.0)
    ground_cut(f, -0.02)
    return [("Fence", f, fine(0.004, 0.008), "picket")]


def box_hedge(seed=0, L=1.0):
    """A clipped privet hedge: a squared-off block, lumpy, a little wider at its foot."""
    f = Field("Hedge")
    f.add(RoundBox((0, 0, 0.22), (L / 2, 0.17, 0.22), 0.07, **wob(9.0, 0.02, seed)), k=0.0)
    rng = np.random.default_rng(seed)
    for i in range(10):
        q = v3((rng.uniform(-L / 2, L / 2), rng.choice([-1, 1]) * 0.16, rng.uniform(0.08, 0.4)))
        f.add(Ellipsoid(q, (0.07, 0.04, 0.06), **wob(20.0, 0.01, seed + i)), k=0.04)
    ground_cut(f, -0.02)
    return [("Hedge", f, fine(0.008, 0.016), "hedge")]


def gnome(seed=0):
    """A garden gnome: black boots, a blue coat with a belt, a white beard, a round pink face and nose, the tall red
    pointed hat; a little fishing rod over his shoulder."""
    f = Field("Gnome")
    for sx in (-1, 1):
        f.add(Ellipsoid((0.02, sx * 0.04, 0.025), (0.045, 0.03, 0.025)), k=0.0, label=8)
    f.add(Ellipsoid((0, 0, 0.13), (0.075, 0.07, 0.11)), k=0.02)
    f.add(Torus((0, 0, 0.12), 0.074, 0.01), k=0.004, label=8)
    f.add(Sphere((0.0, 0, 0.255), 0.05), k=0.02, label=7)
    f.add(Ellipsoid((0.04, 0, 0.215), (0.035, 0.05, 0.06)), k=0.01, label=6)
    f.add(Sphere((0.05, 0, 0.255), 0.016), k=0.004, label=7)
    f.add(RoundCone((-0.005, 0, 0.27), (-0.03, 0, 0.42), 0.058, 0.006), k=0.02, label=5)
    for sx in (-1, 1):
        f.add(RoundCone((0.0, sx * 0.065, 0.19), (0.05, sx * 0.05, 0.12), 0.02, 0.018), k=0.01)
    f.add(RoundCone((0.05, 0.04, 0.12), (-0.08, 0.04, 0.38), 0.005, 0.004), k=0.0, label=8)
    ground_cut(f, -0.01)
    return [("Gnome", f, fine(0.003, 0.006), "gnome")]


def bike(seed=0):
    """A kid's bike propped on its kickstand: red frame, black tyres on silver rims, handlebars with grips, a saddle."""
    out = []
    fr, ty = Field("Frame"), Field("Wheels")
    lean = euler(0.12, 0, 0)
    r = 0.15
    wa, wb = v3((0.28, 0, r)), v3((-0.26, 0, r))
    for c in (wa, wb):
        ty.add(Torus(c, r - 0.015, 0.016, R=RY), k=0.0)
        fr.add(Torus(c, r - 0.035, 0.008, R=RY), k=0.0, label=6)
        fr.add(Cylinder(c, 0.02, 0.05, R=RY), k=0.004, label=6)
        for i in range(8):
            a = math.pi * i / 8
            d = v3((math.cos(a), 0, math.sin(a)))
            fr.add(RoundCone(c - d * (r - 0.04), c + d * (r - 0.04), 0.003, 0.003), k=0.0, label=6)
    bb = v3((0.0, 0, 0.12))
    st = v3((-0.06, 0, 0.36))
    hd = v3((0.2, 0, 0.38))
    for a, b in ((wb, bb), (bb, st), (st, hd), (bb, hd), (wb, st), (hd, wa)):
        pole(fr, a, b, 0.016)
    pole(fr, st, st + v3((-0.02, 0, 0.08)), 0.012, label=6)
    fr.add(Ellipsoid(st + v3((-0.01, 0, 0.1)), (0.07, 0.035, 0.02)), k=0.0, label=7)
    pole(fr, hd, hd + v3((-0.02, 0, 0.09)), 0.012, label=6)
    pole(fr, hd + v3((-0.04, -0.13, 0.1)), hd + v3((-0.04, 0.13, 0.1)), 0.01, label=6)
    for sy in (-1, 1):
        pole(fr, hd + v3((-0.04, sy * 0.13, 0.1)), hd + v3((-0.04, sy * 0.17, 0.1)), 0.014, label=7)
    fr.add(Cylinder(bb, 0.05, 0.02, R=RY), k=0.004, label=6)
    pole(fr, bb + v3((-0.04, 0.03, 0)), v3((-0.1, 0.12, 0.0)), 0.006, label=6)
    out += [("Frame", fr, fine(0.003, 0.006), "bike"), ("Wheels", ty, fine(0.003, 0.006), "rubber")]
    return place_parts([], out, (0, 0, 0), lean)


def wheelie_bins(seed=0):
    """Two wheelie bins out for collection: green and blue, their hinged lids, handles and back wheels."""
    out = []
    f, tf, hf = Field("Bins"), Field("Tyres"), Field("Hubs")
    for i, (x, lab, yaw) in enumerate(((-0.17, 0, 0.1), (0.18, 5, -0.15))):
        R = Rz(yaw)
        c = v3((x, 0, 0))
        f.add(convex([(c + R @ v3((0, 0, 0.5)), R @ v3((0, 0, 1))), (c + R @ v3((0, 0, 0.03)), R @ v3((0, 0, -1))),
                      (c + R @ v3((0.13, 0, 0.25)), R @ v3((1, 0, -0.08))), (c + R @ v3((-0.13, 0, 0.25)), R @ v3((-1, 0, -0.08))),
                      (c + R @ v3((0, 0.15, 0.25)), R @ v3((0, 1, -0.08))), (c + R @ v3((0, -0.15, 0.25)), R @ v3((0, -1, -0.08)))],
                     c - 0.4, c + v3((0.4, 0.4, 0.7))), k=0.0, label=lab)
        f.add(RoundBox(c + R @ v3((0, 0.0, 0.52)), (0.16, 0.18, 0.02), 0.012, R=R), k=0.004, label=lab)
        pole(f, c + R @ v3((-0.12, 0.17, 0.5)), c + R @ v3((0.12, 0.17, 0.5)), 0.012, label=7)
        for sx in (-1, 1):
            wheel(tf, hf, c + R @ v3((sx * 0.13, 0.13, 0.05)), R @ v3((sx, 0, 0)), 0.05, 0.03)
    ground_cut(f, -0.01)
    ground_cut(tf, -0.01)
    out += [("Bins", f, fine(0.004, 0.008), "bins"), ("Tyres", tf, fine(0.003, 0.006), "rubber"), ("Hubs", hf, fine(0.003, 0.006), "bins")]
    return out


def adirondack(f, c, yaw, label=0):
    """An Adirondack chair (field f): the fan of back slats, the sloping seat, broad flat arms on their legs."""
    R = Rz(yaw)
    c = v3(c)
    P = lambda x, y, z: c + R @ v3((x, y, z))
    for i in range(5):
        a = (i - 2) * 0.09
        b0 = P(-0.12, a * 0.6, 0.2)
        b1 = P(-0.28, a * 1.4, 0.62)
        d = unit(b1 - b0)
        Rb = rot_from_axes(z_axis=d, y_axis=R @ v3((1, 0, 0)))
        f.add(RoundBox((b0 + b1) / 2, (0.03, 0.008, float(np.linalg.norm(b1 - b0)) / 2), 0.006, R=Rb), k=0.0, label=label)
    for j in range(4):
        x = 0.1 - j * 0.07
        f.add(RoundBox(P(x, 0, 0.22 - j * 0.012), (0.03, 0.17, 0.01), 0.005, R=R), k=0.0, label=label)
    for sy in (-1, 1):
        f.add(RoundBox(P(0.0, sy * 0.21, 0.36), (0.18, 0.05, 0.01), 0.006, R=R), k=0.0, label=label)
        pole(f, P(0.12, sy * 0.19, 0.0), P(0.12, sy * 0.19, 0.36), 0.014, label=label)
        pole(f, P(-0.12, sy * 0.17, 0.0), P(-0.08, sy * 0.17, 0.22), 0.014, label=label)
        pole(f, P(-0.12, sy * 0.17, 0.22), P(0.14, sy * 0.17, 0.2), 0.014, label=label)


def lawn_chairs(seed=0):
    """Two Adirondack chairs (one red, one teal) turned toward each other, a little side table between them with a
    pitcher and glasses."""
    f, tb = Field("Chairs"), Field("Table")
    adirondack(f, (-0.33, 0.0, 0.0), -0.35, label=8)
    adirondack(f, (0.33, 0.05, 0.0), math.pi + 0.35, label=0)
    box(tb, (0.0, -0.18, 0.24), (0.1, 0.1, 0.012), 0.006, label=9)
    for sx in (-1, 1):
        for sy in (-1, 1):
            pole(tb, (sx * 0.08, -0.18 + sy * 0.08, 0.0), (sx * 0.08, -0.18 + sy * 0.08, 0.24), 0.01, label=9)
    tb.add(RoundCone((0.02, -0.18, 0.25), (0.02, -0.18, 0.34), 0.03, 0.025), k=0.0, label=6)
    for x in (-0.05, 0.06):
        tb.add(Cylinder((x, -0.13, 0.28), 0.014, 0.05), k=0.0, label=6)
    for f_ in (f, tb):
        ground_cut(f_, -0.01)
    return [("Chairs", f, fine(0.004, 0.008), "chairs"), ("Table", tb, fine(0.003, 0.006), "chairs")]


def maple(h=2.5, seed=0, red=False):
    """A maple: a straight grey trunk dividing into upswept limbs under a dense rounded crown (red: a red maple in its
    autumn colour)."""
    rng = np.random.default_rng(seed)
    s = h / 2.5
    f, c = Field("Trunk"), Field("Leaves")
    r0 = 0.1 * s
    fork = h * 0.38
    f.add(RoundCone((0, 0, -0.06), (0, 0, fork), r0, r0 * 0.75, **wob(4.0 / s, 0.01 * s, seed)), k=0.0)
    for k in range(4):
        a = 2 * math.pi * k / 4 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((math.cos(a) * r0 * 0.4, math.sin(a) * r0 * 0.4, 0.1 * s), (math.cos(a) * r0 * 1.8, math.sin(a) * r0 * 1.8, -0.03), r0 * 0.4, r0 * 0.18), k=0.04 * s)
    tops = []
    a0 = rng.uniform(0, 2 * math.pi)
    for i in range(4):
        a = a0 + 2 * math.pi * i / 4 + rng.uniform(-0.3, 0.3)
        o = v3((math.cos(a), math.sin(a), 0.0))
        p0 = v3((0, 0, fork - 0.04 * s))
        p1 = p0 + o * 0.28 * s + v3((0, 0, 0.42 * s))
        p2 = p1 + o * 0.22 * s + v3((0, 0, 0.42 * s))
        f.add(Chain([p0, p1, p2], [r0 * 0.6, r0 * 0.42, r0 * 0.2], k=0.03 * s), k=0.04 * s)
        tops += [p1 + o * 0.12 * s, p2]
    ctr = v3((0, 0, h * 0.68))
    for j, q in enumerate(tops):
        for k in range(2):
            o = v3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.2, 0.6))) * 0.16 * s
            r = s * rng.uniform(0.3, 0.38)
            c.add(Ellipsoid(q + o, (r, r * 0.95, r * 0.85), **wob(10.0 / s, 0.04 * s, seed * 100 + j * 3 + k)), k=0.07 * s)
    for j in range(12):
        u = rng.normal(size=3)
        u = u / np.linalg.norm(u)
        q = ctr + v3((u[0] * 0.55 * s, u[1] * 0.55 * s, u[2] * 0.45 * s))
        r = s * rng.uniform(0.32, 0.42)
        c.add(Ellipsoid(q, (r, r * 0.95, r * 0.88), **wob(10.0 / s, 0.04 * s, seed * 200 + j)), k=0.08 * s)
    return [("Trunk", f, fine(0.007, 0.014), "maple_bark"), ("Leaves", c, vx(h) * 0.9, "maple_red" if red else "maple_leaves")]


def yard_oak(h=2.7, seed=0):
    return retex(oak(h, seed), {"oak_bark": "maple_bark", "oak_leaves": "oak_leaves"})


def flower_pots(seed=0):
    """Terracotta flower pots by a step: geraniums in red, petunias in purple and white, a galvanised watering can."""
    out = []
    pt, so, fl, cn = Field("Pots"), Field("Soil"), Field("Blooms"), Field("Can")
    rng = np.random.default_rng(seed)
    for i, (x, y, r, lab) in enumerate(((0.0, 0.0, 0.11, 5), (0.22, 0.06, 0.085, 6), (0.08, 0.2, 0.08, 0))):
        h = r * 1.4
        pt.add(RoundCone((x, y, 0.0), (x, y, h), r * 0.72, r), k=0.0)
        pt.add(Torus((x, y, h), r + 0.006, 0.014), k=0.004)
        pt.sub(Cylinder((x, y, h + 0.02), r - 0.012, 0.06), k=0.004)
        so.add(Cylinder((x, y, h - 0.015), r - 0.008, 0.02), k=0.0)
        for j in range(7):
            a = 2 * math.pi * j / 7 + rng.uniform(-0.3, 0.3)
            q = v3((x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55, h + 0.04 + rng.uniform(0, 0.04)))
            fl.add(Sphere(q, r * 0.32), k=0.02, label=lab if j % 2 == 0 else 7)
        fl.add(Sphere((x, y, h + 0.08), r * 0.4), k=0.02, label=7)
    cn.add(Cylinder((-0.22, -0.05, 0.08), 0.07, 0.16, rr=0.01), k=0.0)
    pole(cn, (-0.17, -0.05, 0.05), (-0.04, -0.05, 0.2), 0.012, k=0.006)
    cn.add(Torus((-0.22, -0.05, 0.2), 0.05, 0.008, R=RY), k=0.004)
    for f_ in (pt, cn):
        ground_cut(f_, -0.01)
    out += [("Pots", pt, fine(0.004, 0.008), "pottery"), ("Soil", so, fine(0.004, 0.008), "dirt"), ("Blooms", fl, fine(0.004, 0.008), "flowers"),
            ("Can", cn, fine(0.004, 0.008), "galv")]
    return out


# ------------------------------------------------------------------------------------------------ Suburbia: landmarks
def playground(seed=0):
    """A playground on its patch of wood chips inside a timber border: a play tower with a canopy, a yellow slide off
    it, a ladder up; a swing set (two A-frames and a beam) with two swings on their chains; a spring rider."""
    out = []
    ch, bd, tw, pl, rf, sw, ch2 = (Field(n) for n in ("Chips", "Border", "Tower", "Plastic", "Canopy", "Swings", "Chains"))
    ch.add(RoundBox((0, 0, -0.01), (1.25, 0.85, 0.03), 0.02, **wob(8.0, 0.006, seed)), k=0.0)
    bd.add(Func(lambda P: np.maximum(np.abs(np.maximum(np.abs(P[:, 0]) - F32(1.28), np.abs(P[:, 1]) - F32(0.88))) - F32(0.04),
                                     np.abs(P[:, 2] - F32(0.03)) - F32(0.045)).astype(F32), (-1.4, -1.0, -0.1), (1.4, 1.0, 0.15)), k=0.0)
    # the tower
    T0 = v3((-0.6, 0.15, 0.0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(tw, T0 + v3((sx * 0.22, sy * 0.22, 0.6)), (0.03, 0.03, 0.62), 0.008, label=11)
    box(tw, T0 + v3((0, 0, 0.55)), (0.25, 0.25, 0.025), 0.006, label=10)
    for sy in (-1, 1):
        for z in (0.68, 0.78):
            box(tw, T0 + v3((0, sy * 0.22, z)), (0.22, 0.012, 0.012), 0.004)
    rf.add(pyramid_roof((T0[0], T0[1]), 0.3, 1.18, 1.45), k=0.0)
    for k in range(4):                                               # the canopy's stripes
        rf.paint(Func(lambda P, k=k: (np.abs(np.arctan2(P[:, 1] - F32(T0[1]), P[:, 0] - F32(T0[0])) - F32(-math.pi + (k + 0.25) * math.pi / 2)) - F32(0.4)).astype(F32),
                      T0 + v3((-0.5, -0.5, 1.0)), T0 + v3((0.5, 0.5, 1.6))), 5)
    for z in np.arange(0.12, 0.55, 0.11):                           # ladder on its -X side
        box(tw, T0 + v3((-0.3, 0, z)), (0.012, 0.12, 0.012), 0.004)
    for sy in (-1, 1):
        box(tw, T0 + v3((-0.32, sy * 0.13, 0.3)), (0.015, 0.015, 0.3), 0.004, label=11)
    # the slide: a chute from the deck down toward +X
    s0, s1 = T0 + v3((0.25, 0.0, 0.56)), T0 + v3((1.05, 0.0, 0.08))
    d = unit(s1 - s0)
    Rs = rot_from_axes(x_axis=d)
    Rf = Rs.astype(F32)

    def chute(P):
        Q = (P - F32(s0)) @ Rf
        L = F32(np.linalg.norm(s1 - s0))
        inner = np.maximum(np.abs(Q[:, 1]) - F32(0.11), -Q[:, 2])
        outer = np.maximum(np.abs(Q[:, 1]) - F32(0.14), np.abs(Q[:, 2] - F32(0.03)) - F32(0.06))
        return np.maximum.reduce([outer, -np.maximum(np.abs(Q[:, 1]) - F32(0.11), F32(0.0) - Q[:, 2]), -Q[:, 0], Q[:, 0] - L]).astype(F32)
    pl.add(Func(chute, np.minimum(s0, s1) - 0.3, np.maximum(s0, s1) + 0.3), k=0.0)
    pl.add(RoundBox(s1 + v3((0.1, 0, -0.04)), (0.12, 0.14, 0.015), 0.01), k=0.02)
    for t in (0.35, 0.75):
        q = s0 + (s1 - s0) * t
        pole(tw, q - Z * 0.02, v3((q[0], q[1], 0.0)), 0.015, label=11)
    # the swing set
    S0 = v3((0.55, -0.35, 0.0))
    SW = 0.55
    for sx in (-1, 1):
        top = S0 + v3((sx * SW, 0, 1.0))
        for sy in (-1, 1):
            pole(sw, S0 + v3((sx * (SW + 0.05), sy * 0.35, -0.02)), top, 0.02)
    pole(sw, S0 + v3((-SW - 0.05, 0, 1.0)), S0 + v3((SW + 0.05, 0, 1.0)), 0.025)
    for i, x in enumerate((-0.22, 0.22)):
        seat = S0 + v3((x, 0.05 * (1 if i else -1), 0.28))
        for dx in (-0.08, 0.08):
            pole(ch2, S0 + v3((x + dx, 0, 0.98)), seat + v3((dx, 0, 0.02)), 0.005)
        pl.add(RoundBox(seat, (0.1, 0.05, 0.012), 0.008, R=euler(0.1, 0, 0)), k=0.0, label=7)
    # a spring rider
    rd = v3((0.75, 0.45, 0.0))
    pole(ch2, rd, rd + Z * 0.15, 0.03)
    pl.add(Ellipsoid(rd + Z * 0.27, (0.16, 0.07, 0.09)), k=0.0, label=6)
    pl.add(Sphere(rd + v3((0.14, 0, 0.38)), 0.06), k=0.03, label=6)
    pole(pl, rd + v3((0.08, -0.06, 0.38)), rd + v3((0.08, 0.06, 0.38)), 0.01, label=7)
    for f_ in (ch, bd, tw, sw):
        ground_cut(f_, -0.03)
    out += [("Chips", ch, fine(0.01, 0.02), "chips"), ("Border", bd, fine(0.008, 0.016), "timber"), ("Tower", tw, fine(0.005, 0.01), "timber"),
            ("Plastic", pl, fine(0.005, 0.01), "toy"), ("Canopy", rf, fine(0.006, 0.012), "awning"), ("Swings", sw, fine(0.005, 0.01), "toy_frame"),
            ("Chains", ch2, fine(0.003, 0.006), "galv")]
    return out


def hoop(seed=0):
    """A basketball hoop at the end of a driveway: the pole on its square pad of concrete, the white backboard with its
    orange square, the orange rim and the white net; a ball on the concrete."""
    out = []
    pd, pl, bb, rm, nt, ba = (Field(n) for n in ("Pad", "Pole", "Board", "Rim", "Net", "Ball"))
    box(pd, (0, -0.3, 0.0), (0.55, 0.65, 0.025), 0.01)
    pd.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + (P[:, 1] + F32(0.05)) ** 2) - F32(0.45)) - F32(0.012)).astype(F32), (-1, -1, -0.1), (1, 1, 0.1)), 6)
    pole(pl, (0, 0.2, -0.02), (0, 0.2, 1.25), 0.03)
    pole(pl, (0, 0.2, 1.15), (0, 0.04, 1.25), 0.02)
    box(bb, (0, 0.02, 1.3), (0.3, 0.015, 0.2), 0.01)
    bb.paint(Func(lambda P: np.maximum(np.abs(np.maximum(np.abs(P[:, 0]) - F32(0.11), np.abs(P[:, 2] - F32(1.23)) - F32(0.08))) - F32(0.01),
                                       np.abs(P[:, 1]) - F32(0.1)).astype(F32), (-0.4, -0.2, 1.0), (0.4, 0.2, 1.6)), 5)
    bb.paint(Func(lambda P: (np.abs(np.maximum(np.abs(P[:, 0]) - F32(0.29), np.abs(P[:, 2] - F32(1.3)) - F32(0.19))) - F32(0.012)).astype(F32),
                  (-0.4, -0.2, 1.0), (0.4, 0.2, 1.6)), 7)
    rm.add(Torus((0, -0.15, 1.16), 0.11, 0.008), k=0.0)
    rm.add(RoundBox((0, -0.02, 1.16), (0.04, 0.03, 0.012), 0.004), k=0.0)

    def net(P):
        q = np.sqrt(P[:, 0] ** 2 + (P[:, 1] + F32(0.15)) ** 2)
        t = (F32(1.16) - P[:, 2]) / F32(0.2)
        rad = F32(0.105) - t * F32(0.035)
        return np.maximum.reduce([np.abs(q - rad) - F32(0.006), P[:, 2] - F32(1.16), F32(0.96) - P[:, 2]]).astype(F32)
    nt.add(Func(net, (-0.2, -0.35, 0.9), (0.2, 0.05, 1.2)), k=0.0)
    ba.add(Sphere((0.25, -0.55, 0.075), 0.075), k=0.0)
    ba.paint(Func(lambda P: (np.abs(P[:, 0] - F32(0.25)) - F32(0.004)).astype(F32), (0, -0.7, 0), (0.4, -0.4, 0.2)), 7)
    ba.paint(Func(lambda P: (np.abs(P[:, 2] - F32(0.075)) - F32(0.004)).astype(F32), (0, -0.7, 0), (0.4, -0.4, 0.2)), 7)
    for f_ in (pd, pl):
        ground_cut(f_, -0.03)
    out += [("Pad", pd, fine(0.008, 0.016), "concrete"), ("Pole", pl, fine(0.004, 0.008), "street_iron"), ("Board", bb, fine(0.004, 0.008), "backboard"),
            ("Rim", rm, fine(0.003, 0.006), "rim_orange"), ("Net", nt, fine(0.003, 0.006), "net"), ("Ball", ba, fine(0.004, 0.008), "ball")]
    return out


def treehouse(seed=0):
    """A treehouse (front toward -Y): a big oak's trunk rising behind a plank platform on two posts, a little hut on
    it with a red tin roof, a window and an open doorway with a rail before it, a ladder of boards nailed up a post, a
    rope swing with its board from a low limb, the oak's crown standing high behind."""
    out = []
    rng = np.random.default_rng(seed)
    tk, lv, pf, ht, rf, rp = (Field(n) for n in ("Trunk", "Leaves", "Platform", "Hut", "HutRoof", "Rope"))
    T = v3((0.0, 0.35, 0.0))
    tk.add(RoundCone(T - Z * 0.06, T + Z * 1.5, 0.2, 0.15, **wob(4.0, 0.015, seed)), k=0.0)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        tk.add(RoundCone(T + v3((math.cos(a) * 0.08, math.sin(a) * 0.08, 0.16)), T + v3((math.cos(a) * 0.38, math.sin(a) * 0.38, -0.04)), 0.09, 0.04), k=0.06)
    tops = []
    for i, a in enumerate((0.4, 1.9, 3.3, 4.7)):
        o = v3((math.cos(a), math.sin(a) * 0.6 + 0.4, 0.0))
        p0 = T + Z * 1.35
        p1 = p0 + o * 0.45 + Z * 0.5
        p2 = p1 + o * 0.35 + Z * 0.35
        tk.add(Chain([p0, p1, p2], [0.11, 0.07, 0.035], k=0.03), k=0.05)
        tops += [p1, p2]
    low = [T + Z * 0.95, T + v3((0.55, -0.25, 1.15)), T + v3((0.9, -0.35, 1.25))]
    tk.add(Chain(low, [0.08, 0.05, 0.03], k=0.02), k=0.04)
    ctr = T + v3((0, 0.15, 2.35))
    for j, q in enumerate(tops):
        for k in range(2):
            o = v3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.1, 0.6))) * 0.18
            r = rng.uniform(0.3, 0.4)
            lv.add(Ellipsoid(q + o + Z * 0.1, (r, r * 0.92, r * 0.75), **wob(10.0, 0.045, seed * 100 + j * 3 + k)), k=0.07)
    for j in range(10):
        u = rng.normal(size=3)
        u = u / np.linalg.norm(u)
        q = ctr + v3((u[0] * 0.7, u[1] * 0.55, abs(u[2]) * 0.35))
        r = rng.uniform(0.32, 0.42)
        lv.add(Ellipsoid(q, (r, r * 0.92, r * 0.72), **wob(10.0, 0.045, seed * 200 + j)), k=0.08)
    lv.add(Ellipsoid(low[-1] + v3((0.05, 0, 0.12)), (0.25, 0.22, 0.18), **wob(10.0, 0.04, seed + 5)), k=0.05)
    # the platform: planks on joists, two posts in front, the trunk at the back
    ZP = 1.0
    for i in range(8):
        y = -0.72 + i * 0.105
        pf.add(RoundBox((0.0, y, ZP), (0.52, 0.048, 0.016), 0.005, R=Rz(rng.uniform(-0.01, 0.01))), k=0.0, label=10)
    for x in (-0.45, 0.45):
        pf.add(RoundBox((x, -0.3, ZP - 0.05), (0.03, 0.48, 0.035), 0.006), k=0.0)
        post(pf, (x, -0.68, -0.05), (x, -0.68, ZP - 0.02), 0.04)
        pole(pf, (x, -0.68, ZP - 0.4), (x, -0.25, ZP - 0.06), 0.022, label=11)
    for z in np.arange(0.18, ZP - 0.05, 0.14):                      # ladder boards up the left post
        pf.add(RoundBox((-0.45, -0.74, z), (0.1, 0.018, 0.022), 0.005), k=0.0, label=10)
    for x in (-0.48, 0.48):
        pole(pf, (x, -0.74, ZP), (x, -0.74, ZP + 0.3), 0.015, label=11)
    pole(pf, (-0.48, -0.74, ZP + 0.3), (-0.2, -0.74, ZP + 0.3), 0.012, label=11)
    pole(pf, (0.2, -0.74, ZP + 0.3), (0.48, -0.74, ZP + 0.3), 0.012, label=11)
    # the hut
    HX, HY0, HY1 = 0.36, -0.58, 0.06
    ht.add(RoundBox((0.0, (HY0 + HY1) / 2, ZP + 0.27), (HX, (HY1 - HY0) / 2, 0.26), 0.01), k=0.0, label=10)
    ht.sub(RoundBox((-0.12, HY0, ZP + 0.25), (0.08, 0.04, 0.16), 0.01), k=0.0)
    ht.sub(RoundBox((0.17, HY0, ZP + 0.33), (0.07, 0.04, 0.06), 0.01), k=0.0)
    ht.add(RoundBox((0.17, HY0 - 0.01, ZP + 0.33), (0.008, 0.012, 0.06), 0.003), k=0.0, label=7)
    ht.add(RoundBox((0.17, HY0 - 0.01, ZP + 0.33), (0.07, 0.012, 0.008), 0.003), k=0.0, label=7)
    ht.add(gable((0.0, (HY0 + HY1) / 2), HX - 0.01, (HY1 - HY0) / 2, ZP + 0.5, ZP + 0.68, axis="x"), k=0.0, label=10)
    for k in range(6):
        ht.sub(RoundBox((-HX - 0.01, (HY0 + HY1) / 2, ZP + 0.05 + k * 0.08), (0.004, 0.4, 0.006), 0.0), k=0.0)
    rf.add(gable((0.0, (HY0 + HY1) / 2), HX + 0.08, (HY1 - HY0) / 2 + 0.06, ZP + 0.5, ZP + 0.7, axis="x",
                 over=0.0), k=0.0)
    rf.sub(gable((0.0, (HY0 + HY1) / 2), HX + 0.12, (HY1 - HY0) / 2 + 0.03, ZP + 0.47, ZP + 0.665, axis="x"), k=0.0)
    rf.paint(Func(lambda P: (np.abs(np.mod(P[:, 0] * F32(25.0), F32(1.0)) - F32(0.5)) - F32(0.42)).astype(F32), (-1, -1, 1), (1, 1, 2)), 7)
    # the rope swing from the low limb
    k0 = low[-1] - v3((0.05, 0, 0.02))
    for dy in (-0.07, 0.07):
        pole(rp, k0 + v3((0, dy, 0)), v3((k0[0], k0[1] + dy, 0.33)), 0.007)
    rp.add(RoundBox((k0[0], k0[1], 0.32), (0.06, 0.12, 0.012), 0.005), k=0.0, label=10)
    ground_cut(tk, -0.03)
    ground_cut(pf, -0.03)
    out += [("Trunk", tk, fine(0.008, 0.016), "maple_bark"), ("Leaves", lv, vx(2.6) * 0.9, "oak_leaves"), ("Platform", pf, fine(0.005, 0.01), "timber"),
            ("Hut", ht, fine(0.005, 0.01), "timber"), ("HutRoof", rf, fine(0.005, 0.01), "tin_roof"), ("Rope", rp, fine(0.003, 0.006), "rope")]
    return out


# ------------------------------------------------------------------------------------------------ Suburbia: the pool's surroundings
def loungers(seed=0):
    """Two white pool loungers side by side, backs raised, a striped towel over one."""
    out = []
    f, tw = Field("Loungers"), Field("Towel")
    for y in (-0.22, 0.22):
        box(f, (0.05, y, 0.16), (0.36, 0.13, 0.02), 0.01)
        for x in np.linspace(-0.25, 0.38, 8):
            f.sub(RoundBox((x, y, 0.18), (0.012, 0.11, 0.03), 0.0), k=0.0)
        f.add(RoundBox((-0.42, y, 0.3), (0.16, 0.13, 0.02), 0.01, R=euler(0, 0.9, 0)), k=0.0)
        for sx in (-1, 1):
            for sy in (-1, 1):
                pole(f, (sx * 0.32 + 0.05, y + sy * 0.11, 0.0), (sx * 0.32 + 0.05, y + sy * 0.11, 0.15), 0.015)
    tw.add(RoundBox((0.1, 0.22, 0.185), (0.3, 0.12, 0.008), 0.006, **wob(15.0, 0.006, seed)), k=0.0)
    tw.add(RoundBox((0.1, 0.35, 0.12), (0.3, 0.008, 0.07), 0.006), k=0.01)
    for i in range(4):
        tw.paint(RoundBox((-0.15 + i * 0.16, 0.25, 0.15), (0.04, 0.2, 0.1), 0.0), 5)
    ground_cut(f, -0.01)
    out += [("Loungers", f, fine(0.004, 0.008), "plastic_white"), ("Towel", tw, fine(0.004, 0.008), "towel")]
    return out


def umbrella(seed=0):
    """A patio umbrella in red and white over a round table and two chairs."""
    out = []
    p, cn, tb = Field("Pole"), Field("Canopy"), Field("Table")
    pole(p, (0, 0, 0.0), (0, 0, 1.15), 0.015)
    p.add(Cylinder((0, 0, 0.02), 0.09, 0.04, rr=0.01), k=0.0)
    for i in range(8):
        a = 2 * math.pi * i / 8
        pole(p, (0, 0, 1.12), (math.cos(a) * 0.62, math.sin(a) * 0.62, 0.92), 0.006)

    def can(P):
        q = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        sc = F32(0.02) * np.abs(np.sin(a * F32(4)))
        z = F32(1.15) - q * F32(0.36) - sc * (q / F32(0.65)) ** 2
        return np.maximum(np.abs(P[:, 2] - z) - F32(0.01), q - F32(0.66) + sc * F32(2.0)).astype(F32)
    cn.add(Func(can, (-0.75, -0.75, 0.85), (0.75, 0.75, 1.25)), k=0.0)
    for i in range(4):
        a0 = 2 * math.pi * i / 4
        cn.paint(Func(lambda P, a0=a0: (np.abs(np.mod(np.arctan2(P[:, 1], P[:, 0]) - F32(a0) + F32(math.pi), F32(2 * math.pi)) - F32(math.pi)) - F32(math.pi / 8)).astype(F32),
                      (-0.8, -0.8, 0.8), (0.8, 0.8, 1.3)), 5)
    cn.add(Sphere((0, 0, 1.18), 0.03), k=0.004)
    tb.add(Cylinder((0, 0, 0.36), 0.3, 0.02, rr=0.008), k=0.0)
    for i in range(3):
        a = 2 * math.pi * i / 3
        pole(tb, (math.cos(a) * 0.25, math.sin(a) * 0.25, 0.0), (math.cos(a) * 0.1, math.sin(a) * 0.1, 0.35), 0.012)
    for a in (0.6, 3.6):
        c = v3((math.cos(a) * 0.45, math.sin(a) * 0.45, 0.0))
        R = Rz(a + math.pi)
        tb.add(RoundBox(c + v3((0, 0, 0.22)), (0.12, 0.12, 0.012), 0.008, R=R), k=0.0)
        tb.add(RoundBox(c + R @ v3((-0.12, 0, 0.36)), (0.012, 0.12, 0.13), 0.008, R=R @ euler(0, -0.15, 0)), k=0.0)
        for sx in (-1, 1):
            for sy in (-1, 1):
                pole(tb, c + R @ v3((sx * 0.1, sy * 0.1, 0.0)), c + R @ v3((sx * 0.1, sy * 0.1, 0.22)), 0.01)
    for f_ in (p, tb):
        ground_cut(f_, -0.01)
    out += [("Pole", p, fine(0.004, 0.008), "galv"), ("Canopy", cn, fine(0.005, 0.01), "umbrella"), ("Table", tb, fine(0.004, 0.008), "plastic_white")]
    return out


def diving_board(seed=0):
    """A diving board (reaching toward +X, over the water): its concrete footing, the steel stand and the blue board
    with its grip."""
    out = []
    ft, st, bd = Field("Footing"), Field("Stand"), Field("Board")
    box(ft, (-0.35, 0, 0.05), (0.22, 0.18, 0.06), 0.015)
    for x in (-0.45, -0.2):
        for sy in (-1, 1):
            pole(st, (x, sy * 0.1, 0.1), (x, sy * 0.1, 0.24), 0.018)
    box(st, (-0.32, 0, 0.25), (0.16, 0.12, 0.015), 0.006)
    bd.add(RoundBox((0.15, 0, 0.29), (0.6, 0.11, 0.022), 0.012, R=euler(0, -0.03, 0)), k=0.0)
    bd.paint(RoundBox((0.2, 0, 0.32), (0.5, 0.08, 0.02), 0.0), 5)
    ground_cut(ft, -0.02)
    out += [("Footing", ft, fine(0.005, 0.01), "concrete"), ("Stand", st, fine(0.004, 0.008), "chrome"), ("Board", bd, fine(0.004, 0.008), "board")]
    return out


def pool_ladder(seed=0):
    """The pool ladder's two chrome handrails curving over the coping toward +X (the water) and down."""
    f = Field("Ladder")
    for sy in (-1, 1):
        pts = [v3((-0.12, sy * 0.13, -0.03)), v3((-0.12, sy * 0.13, 0.32)), v3((-0.05, sy * 0.13, 0.4)), v3((0.08, sy * 0.13, 0.36)),
               v3((0.12, sy * 0.13, 0.15)), v3((0.12, sy * 0.13, -0.05))]
        f.add(Chain(pts, [0.016] * 6, k=0.02), k=0.0)
        f.add(Cylinder((-0.12, sy * 0.13, 0.0), 0.035, 0.02, rr=0.006), k=0.004)
    ground_cut(f, -0.02)
    return [("Ladder", f, fine(0.003, 0.006), "chrome")]


# ------------------------------------------------------------------------------------------------ the Modern city
BX0, BX1, BY, BH = 0.75, 3.4, 1.9, 1.3          # the bunker's front face (x), back, half width, wall top


def _container(f, c, yaw=0.0, L=1.2, W=0.48, H=0.5):
    """A shipping container (field f): corrugated sides, corner castings (label 7), the doors' locking bars at its end."""
    R = Rz(yaw)
    Rf = R.astype(F32)
    c = v3(c)
    f.add(RoundBox(c + Z * (H / 2), (L / 2, W / 2, H / 2), 0.01, R=R,
                   disp=lambda P: (F32(0.006) * np.cos((((P - F32(c)) @ Rf)[:, 0]) * F32(90))).astype(F32), disp_amp=0.007), k=0.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (0.03, H - 0.03):
                f.add(RoundBox(c + R @ v3((sx * (L / 2 - 0.03), sy * (W / 2 - 0.03), z)), (0.04, 0.04, 0.035), 0.006, R=R), k=0.003, label=7)
    for y in (-0.12, -0.04, 0.04, 0.12):
        f.add(RoundCone(c + R @ v3((L / 2 + 0.008, y, 0.04)), c + R @ v3((L / 2 + 0.008, y, H - 0.04)), 0.008, 0.008), k=0.002, label=7)


def modern_city(seed=0):
    """The Modern Age's city: a fortified command bunker at the end of the road (the road comes in from -X). Its
    reinforced concrete front stands out of an earth berm that buries its sides and back, retained by battered wing
    walls; the blast doors stand open to the road (two thick steel leaves in hazard stripes, their locking wheels and
    the task force's red-and-white flash), the hall inside lit; sandbag walls flank the approach, burn barrels before
    them (game.gd lights them); HESCO walls run off both ways and die away; floodlights on poles and on the roof's
    corners; on the roof a lattice radar mast with its rotating array and red beacon, whip and log-periodic antennas, a
    satellite dish, mushroom vents and the generator's exhaust (game.gd smokes it), the task force's flag; a watchtower
    with a searchlight on one flank, a vehicle bay under camouflage netting (a Humvee and supplies) on the other; behind
    the berm a container, a big satellite dish and a second mast."""
    rng = np.random.default_rng(seed)
    out = []
    # ---- the concrete: the bunker's front and roof, its door surround, wing walls, roof furniture
    cb = Field("Bunker")
    cx = (BX0 + BX1) / 2
    cb.add(walls_box(cx, 0, (BX1 - BX0) / 2, BY, -0.05, BH, batter=0.0, amp=0.004, seed=seed), k=0.0)
    cb.add(RoundBox((cx - 0.05, 0, BH + 0.1), ((BX1 - BX0) / 2 + 0.14, BY + 0.14, 0.12), 0.03), k=0.0)
    cb.add(convex([((BX0 - 0.1, 0, BH + 0.22), (-1, 0, 1.2)), ((BX0 - 0.2, 0, 0), (-1, 0, 0)), ((cx, 0, BH - 0.02), (0, 0, -1)),
                   ((cx, 0, BH + 0.22), (0, 0, 1)), ((cx, BY + 0.14, 0), (0, 1, 0)), ((cx, -BY - 0.14, 0), (0, -1, 0)), ((BX0 + 0.3, 0, 0), (1, 0, 0))],
                  (BX0 - 0.5, -BY - 0.3, BH - 0.2), (BX0 + 0.5, BY + 0.3, BH + 0.4)), k=0.01)
    cb.add(RoundBox((BX0 - 0.07, 0, 0.62), (0.09, 0.98, 0.68), 0.02), k=0.0)
    cb.paint(Func(lambda P: np.maximum(np.abs(np.maximum(np.abs(P[:, 1]) - F32(0.8), P[:, 2] - F32(1.2))) - F32(0.08),
                                       np.abs(P[:, 0] - F32(BX0 - 0.15)) - F32(0.06)).astype(F32), (BX0 - 0.4, -1.2, -0.1), (BX0 + 0.1, 1.2, 1.5)), 8)
    cb.sub(RoundBox((BX0 + 0.2, 0, 0.56), (0.5, 0.72, 0.57), 0.01), k=0.0)
    digits(cb, (BX0 - 0.2, 0.0, 1.36), (-1, 0, 0), 0.14, "01", label=9)
    for sy in (-1, 1):                                              # wing walls retaining the berm
        y0, y1 = sy * BY, sy * (BY + 1.35)
        cb.add(convex([((BX0 - 0.12, 0, 0), (-1, 0, 0.12)), ((BX0 + 0.12, 0, 0), (1, 0, 0)), ((0, y1, 0), (0, sy, 0)), ((0, y0, 0), (0, -sy, 0)),
                       ((0, y0, BH - 0.02), (0, sy * BH / 1.35, 1)), ((0, 0, -0.05), (0, 0, -1))],
                      (BX0 - 0.4, min(y0, y1) - 0.2, -0.1), (BX0 + 0.4, max(y0, y1) + 0.2, BH + 0.2)), k=0.0)
        cb.add(RoundBox((BX0 - 0.15, sy * (BY + 1.42), 0.08), (0.1, 0.1, 0.1), 0.02), k=0.0)
    for (x, y) in ((1.6, 0.6), (2.5, -0.4), (2.9, 0.9)):            # mushroom vents
        cb.add(Cylinder((x, y, BH + 0.32), 0.06, 0.2, rr=0.01), k=0.02)
        cb.add(Ellipsoid((x, y, BH + 0.44), (0.12, 0.12, 0.05)), k=0.01, label=7)
    box(cb, (2.5, 0.35, BH + 0.29), (0.2, 0.2, 0.08), 0.02, k=0.02)   # the roof hatch
    box(cb, (2.5, 0.35, BH + 0.38), (0.17, 0.17, 0.02), 0.01, k=0.0, label=7)
    ground_cut(cb, -0.04)
    out.append(("Bunker", cb, fine(0.012, 0.024), "concrete"))
    # ---- the earth berm burying its sides and back
    bm = Field("Berm")
    bm.add(convex_w([((cx, 0, BH - 0.06), (0, 0, 1)), ((cx, BY + 0.2, BH - 0.06), (0, 1, 0.9)), ((cx, -BY - 0.2, BH - 0.06), (0, -1, 0.9)),
                     ((BX1 + 0.2, 0, BH - 0.06), (1, 0, 0.9)), ((BX0 + 0.05, 0, 0), (-1, 0, 0)), ((cx, 0, -0.05), (0, 0, -1))],
                    (BX0 - 0.1, -BY - 1.6, -0.1), (BX1 + 1.6, BY + 1.6, BH + 0.1), 0.035, 2.5, seed), k=0.0)
    ground_cut(bm, -0.04)
    out.append(("Berm", bm, fine(0.02, 0.035), "berm"))
    # ---- the blast doors, swung open against the wing of the surround
    dr = Field("Doors")
    for sy in (-1, 1):
        hinge = v3((BX0 - 0.17, sy * 0.76, 0.0))
        th = math.radians(20.0)
        d = v3((-math.sin(th), sy * math.cos(th), 0.0))
        Rd = np.stack([d, unit(np.cross(Z, d)), Z], axis=1)
        mid = hinge + d * 0.37 + Z * 0.57
        dr.add(RoundBox(mid, (0.37, 0.06, 0.57), 0.02, R=Rd), k=0.0)
        n_in = unit(np.cross(Z, d)) * (-sy)                          # the face turned toward the road's axis
        for z in (0.2, 0.95):
            dr.add(Cylinder(hinge + Z * z, 0.05, 0.16, rr=0.01), k=0.006, label=7)
        dr.add(Torus(mid + n_in * 0.08, 0.13, 0.016, R=rot_from_axes(z_axis=n_in)), k=0.0, label=7)
        for k in range(3):
            a = math.pi * k / 3
            dr.add(RoundCone(mid + n_in * 0.075 + Rd @ v3((math.cos(a) * 0.13, 0, math.sin(a) * 0.13)),
                             mid + n_in * 0.075 - Rd @ v3((math.cos(a) * 0.13, 0, math.sin(a) * 0.13)), 0.01, 0.01), k=0.0, label=7)
        dr.add(Cylinder(mid + n_in * 0.075, 0.03, 0.04, R=rot_from_axes(z_axis=n_in)), k=0.004, label=7)
        for k in range(7):                                          # hazard chevrons along the leaf's edge
            q = hinge + d * (0.04 + k * 0.105) + Z * 0.08
            dr.paint(RoundBox(q, (0.035, 0.2, 0.09), 0.0, R=Rd @ euler(0, 0.6, 0)), 5 if k % 2 == 0 else 7)
            dr.paint(RoundBox(q + Z * 0.98, (0.035, 0.2, 0.09), 0.0, R=Rd @ euler(0, 0.6, 0)), 5 if k % 2 == 0 else 7)
        dr.paint(RoundBox(mid + Z * 0.33, (0.3, 0.2, 0.035), 0.0, R=Rd), 8)
        dr.paint(RoundBox(mid + Z * 0.33, (0.3, 0.2, 0.012), 0.0, R=Rd), 9)
    ground_cut(dr, -0.02)
    out.append(("Doors", dr, fine(0.006, 0.012), "blast"))
    hl, hg, al = Field("Hall"), Field("HallLight"), Field("Alarm")
    box(hl, (BX0 + 0.68, 0, 0.56), (0.02, 0.72, 0.56), 0.0)
    box(hl, (BX0 + 0.3, 0, 1.11), (0.4, 0.72, 0.012), 0.0)
    hg.add(RoundBox((BX0 + 0.35, 0, 1.09), (0.3, 0.035, 0.015), 0.006), k=0.0)
    hg.add(RoundBox((BX0 + 0.66, 0, 0.75), (0.012, 0.25, 0.08), 0.004), k=0.0)
    al.add(Sphere((BX0 - 0.17, -0.6, 1.36), 0.045), k=0.0)
    al.add(Sphere((BX0 - 0.17, 0.6, 1.36), 0.045), k=0.0)
    out += [("Hall", hl, fine(0.01, 0.02), "dark"), ("HallLight", hg, fine(0.005, 0.01), "glow_lamp"), ("Alarm", al, fine(0.004, 0.008), "glow_red")]
    # ---- sandbag walls flanking the approach, burn barrels before them
    sb = Field("Sandbags")
    for sy in (-1, 1):
        sandbag_run(sb, (0.15, sy * 1.62, 0), (-0.6, sy * 1.75, 0), layers=3, seed=seed + 10 + sy, rows=2)
        sandbag_run(sb, (-0.6, sy * 1.75, 0), (-0.85, sy * 2.5, 0), layers=3, seed=seed + 20 + sy, rows=2)
        sandbag_run(sb, (BX0 - 0.35, sy * (BY + 1.55), 0), (-0.3, sy * (BY + 1.3), 0), layers=2, seed=seed + 30 + sy, rows=1)
        sandbag_run(sb, (BX0 + 0.12, sy * 0.35, 0), (BX0 + 0.12, sy * (BY - 0.3), 0), layers=2, seed=seed + 40 + sy, z0=BH + 0.22)
        sandbag_run(sb, (BX0 + 0.3, sy * (BY - 0.05), 0), (BX0 + 0.95, sy * (BY - 0.05), 0), layers=2, seed=seed + 50 + sy, z0=BH + 0.22)
    ground_cut(sb, -0.01)
    out.append(("Sandbags", sb, fine(0.006, 0.012), "sandbag"))
    br, cl = Field("Barrels"), Field("Coals")
    for (fx, fy, fz) in CITY_FIRES:
        drum(br, (fx, fy, 0.15), label=0)
        for k in range(6):
            a = 2 * math.pi * k / 6
            br.sub(Sphere((fx + math.cos(a) * 0.1, fy + math.sin(a) * 0.1, 0.2), 0.022), k=0.004)
        br.sub(Cylinder((fx, fy, 0.3), 0.085, 0.06), k=0.0)
        cl.add(Ellipsoid((fx, fy, 0.27), (0.085, 0.085, 0.035), **wob(25.0, 0.008, seed)), k=0.0)
    ground_cut(br, -0.01)
    out += [("Barrels", br, fine(0.004, 0.008), "rust"), ("Coals", cl, fine(0.004, 0.008), "glow_fire")]
    # ---- HESCO walls running off both ways, dying away
    for sy in (-1, 1):
        hs, hf = Field("Hesco%d" % (sy + 1)), Field("Fill%d" % (sy + 1))
        ys = np.arange(BY + 1.6, 7.0, 0.38)
        for i, y in enumerate(ys):
            h = 0.4 if i < len(ys) - 2 else (0.32 if i == len(ys) - 2 else 0.24)
            hesco_cell(hs, (BX0 - 0.02, sy * y, 0), h=h, seed=seed + i * 3 + sy, fill=hf)
            if i < 4:
                hesco_cell(hs, (BX0 - 0.02, sy * y, h), h=0.4, seed=seed + i * 5 + sy + 50, fill=hf)
        ground_cut(hs, -0.02)
        out += [("Hesco%d" % (sy + 1), hs, fine(0.008, 0.016), "hesco"), ("Fill%d" % (sy + 1), hf, fine(0.012, 0.024), "dirt")]
    # ---- the radar mast with its array and beacon; antennas; the satellite dish; the flag; the exhaust
    ms = Field("Mast")
    MX, MY, MZ0, MZ1 = 3.0, -1.1, BH + 0.22, 4.7
    lattice_mast(ms, (MX, MY, 0), MZ0, MZ1, 0.24, 0.09, legs=3, step=0.3, rod=0.014)
    box(ms, (MX, MY, MZ1 + 0.02), (0.16, 0.16, 0.02), 0.006)
    ms.add(Cylinder((MX, MY, MZ1 + 0.1), 0.06, 0.14, rr=0.015), k=0.004)
    pole(ms, (1.25, 1.45, BH + 0.22), (1.25, 1.45, BH + 1.85), 0.014, 0.006)
    pole(ms, (2.75, 1.65, BH + 0.22), (2.75, 1.65, BH + 1.4), 0.012, 0.005)
    pole(ms, (1.35, -1.5, BH + 0.22), (1.35, -1.5, BH + 1.2), 0.012, 0.005)
    lp0 = v3((2.2, 1.1, BH + 1.3))                                   # a log-periodic antenna on its mast
    pole(ms, (2.2, 1.1, BH + 0.22), lp0, 0.02)
    pole(ms, lp0 + v3((-0.35, 0, 0)), lp0 + v3((0.35, 0, 0)), 0.012)
    for k in range(7):
        x = -0.32 + k * 0.1
        L = 0.42 - k * 0.045
        pole(ms, lp0 + v3((x, -L, 0)), lp0 + v3((x, L, 0)), 0.006)
    fp = v3((BX0 + 0.25, -1.65, BH + 0.22))                          # the flagpole
    pole(ms, fp, fp + Z * 2.0, 0.018, 0.012)
    ms.add(Sphere(fp + Z * 2.02, 0.03), k=0.004)
    ex = v3((3.15, 1.25, BH + 0.22))
    pole(ms, ex, ex + Z * 0.95, 0.045)
    box(ms, ex + Z * 0.98, (0.08, 0.06, 0.008), 0.004, R=euler(0, -0.35, 0))
    out.append(("Mast", ms, fine(0.005, 0.01), "galv"))
    ar, bc = Field("Array"), Field("Beacon")
    ar.add(RoundBox((MX, MY, MZ1 + 0.32), (0.07, 0.62, 0.14), 0.02, R=euler(0.0, -0.3, 0.6)), k=0.0)
    ar.add(RoundCone((MX, MY, MZ1 + 0.15), (MX, MY, MZ1 + 0.26), 0.05, 0.04), k=0.01)
    bc.add(Sphere((MX, MY, MZ1 + 0.55), 0.045), k=0.0)
    pole(ar, (MX, MY, MZ1 + 0.4), (MX, MY, MZ1 + 0.52), 0.012)
    out += [("Array", ar, fine(0.005, 0.01), "radome"), ("Beacon", bc, fine(0.004, 0.008), "glow_red")]
    sd = Field("SatDish")
    vert, ax = v3((1.65, -0.95, BH + 0.62)), unit(v3((-0.6, -0.3, 0.75)))
    Rf = rot_from_axes(z_axis=ax).astype(F32)

    def sdish(P, vert=vert, Rd=0.32, Fc=0.2):
        Q = (P - F32(vert)) @ Rf
        r2 = Q[:, 0] ** 2 + Q[:, 1] ** 2
        d = np.abs(Q[:, 2] - r2 / F32(4 * Fc)) / np.sqrt(F32(1) + r2 / F32(4 * Fc * Fc)) - F32(0.01)
        return np.maximum(d, np.sqrt(r2) - F32(Rd)).astype(F32)
    sd.add(Func(sdish, vert - 0.5, vert + 0.5), k=0.0)
    pole(sd, vert, v3((1.65, -0.95, BH + 0.22)), 0.03)
    pole(sd, vert + ax * 0.02, vert + ax * 0.2, 0.012)
    out.append(("SatDish", sd, fine(0.005, 0.01), "radome"))
    fl = Field("Flag")
    fo = fp + Z * 1.95
    fl.add(flag(fo, 0.66, 0.42, seed, th=0.008, wave=0.04, along=(1, 0.25, 0)), k=0.0)
    fd = unit(v3((1, 0.25, 0)))
    fc = fo + fd * 0.33 - Z * 0.21
    fl.paint(Sphere(fc, 0.12), 5)
    fl.paint(Func(lambda P: (lambda a, z: np.maximum(np.abs(z + np.abs(a) * F32(0.8) - F32(0.02)) - F32(0.03), np.abs(a) - F32(0.1)))(
        (P - F32(fc)) @ F32(fd), P[:, 2] - F32(fc[2])).astype(F32), fc - 0.3, fc + 0.3), 6)
    out.append(("Flag", fl, fine(0.004, 0.008), "flag"))
    # ---- floodlights: on two poles before the wing walls and on the roof's front corners
    fpole, fh, fg = Field("FloodPoles"), Field("FloodHeads"), Field("Floods")
    for sy in (-1, 1):
        b = v3((0.25, sy * 2.15, 0.0))
        fpole.add(Cylinder(b + Z * 0.06, 0.08, 0.12, rr=0.02), k=0.0)
        pole(fpole, b, b + Z * 2.45, 0.035, 0.025)
        pole(fpole, b + v3((0, -0.25, 2.4)), b + v3((0, 0.25, 2.4)), 0.018)
        for dy in (-0.2, 0.2):
            flood_head(fh, fg, b + v3((-0.06, dy, 2.32)), (-0.75, -sy * 0.3 + 0.0, -0.6), s=1.3)
        flood_head(fh, fg, v3((BX0 - 0.05, sy * (BY - 0.05), BH + 0.38)), (-0.6, -sy * 0.2, -0.7), s=1.2)
        pole(fpole, v3((BX0 + 0.05, sy * (BY - 0.05), BH + 0.22)), v3((BX0 + 0.0, sy * (BY - 0.05), BH + 0.36)), 0.02)
    ground_cut(fpole, -0.02)
    out += [("FloodPoles", fpole, fine(0.005, 0.01), "galv"), ("FloodHeads", fh, fine(0.004, 0.008), "steel"), ("Floods", fg, fine(0.004, 0.008), "glow_flood")]
    # ---- the watchtower on the -Y flank
    wt, wsb, wr, ws = Field("Tower"), Field("TowerBags"), Field("TowerRoof"), Field("Search")
    T = v3((1.55, -4.5, 0.0))
    ZP = 2.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            pole(wt, T + v3((sx * 0.48, sy * 0.48, -0.05)), T + v3((sx * 0.4, sy * 0.4, ZP)), 0.035)
            pole(wt, T + v3((sx * 0.4, sy * 0.4, ZP)), T + v3((sx * 0.4, sy * 0.4, ZP + 0.78)), 0.022)
    for z0, z1 in ((0.15, 1.0), (1.0, 1.9)):
        for sx in (-1, 1):
            r0, r1 = 0.48 - (0.08 * z0 / ZP), 0.48 - (0.08 * z1 / ZP)
            pole(wt, T + v3((sx * r0, -r0, z0)), T + v3((sx * r1, r1, z1)), 0.014)
            pole(wt, T + v3((-r0, sx * r0, z0)), T + v3((r1, sx * r1, z1)), 0.014)
    box(wt, T + Z * ZP, (0.52, 0.52, 0.04), 0.01, label=10)
    for z in np.arange(0.2, ZP, 0.2):                               # the ladder up its back
        pole(wt, T + v3((0.56, -0.12, z)), T + v3((0.56, 0.12, z)), 0.01)
    for sy in (-1, 1):
        pole(wt, T + v3((0.56, sy * 0.12, 0.0)), T + v3((0.56, sy * 0.12, ZP + 0.2)), 0.014)
    for (a, b) in (((-0.48, -0.48), (0.48, -0.48)), ((0.48, -0.48), (0.48, 0.2)), ((0.48, 0.48), (-0.48, 0.48)), ((-0.48, 0.48), (-0.48, -0.48))):
        sandbag_run(wsb, T + v3((a[0], a[1], 0)), T + v3((b[0], b[1], 0)), layers=2, seed=seed + int(a[0] * 10 + b[1] * 7), z0=ZP + 0.04, gap=0.24)
    wr.add(convex([(T + Z * (ZP + 0.85), (0.15, 0, 1)), (T + Z * (ZP + 0.79), (-0.15, 0, -1)), (T + v3((0.62, 0, 0)), (1, 0, 0)),
                   (T + v3((-0.62, 0, 0)), (-1, 0, 0)), (T + v3((0, 0.62, 0)), (0, 1, 0)), (T + v3((0, -0.62, 0)), (0, -1, 0))],
                  T + v3((-0.8, -0.8, ZP + 0.5)), T + v3((0.8, 0.8, ZP + 1.1))), k=0.0)
    wr.paint(Func(lambda P: (np.abs(np.mod((P[:, 1] - F32(T[1])) * F32(14.0), F32(1.0)) - F32(0.5)) - F32(0.4)).astype(F32), T - 1, T + 4), 7)
    flood_head(ws, fg, T + v3((-0.5, 0.0, ZP + 0.48)), (-0.8, 0.45, -0.4), s=1.4)
    pole(wt, T + v3((-0.45, 0.0, ZP + 0.3)), T + v3((-0.47, 0.0, ZP + 0.42)), 0.02)
    ground_cut(wt, -0.03)
    out += [("Tower", wt, fine(0.006, 0.012), "gunmetal"), ("TowerBags", wsb, fine(0.006, 0.012), "sandbag"), ("TowerRoof", wr, fine(0.006, 0.012), "tin_grey"),
            ("Search", ws, fine(0.004, 0.008), "steel")]
    # ---- the vehicle bay on the +Y flank under camouflage netting: a Humvee and supplies
    place_parts(out, humvee(seed + 3), (1.85, 4.55, 0.0), Rz(math.pi + 0.08), rename={"Body": "HumveeBody", "Glass": "HumveeGlass", "Tyres": "HumveeTyres",
                                                                                       "Hubs": "HumveeHubs", "Kit": "HumveeKit", "Spare": "HumveeSpare",
                                                                                       "SpareHub": "HumveeSpareHub"})
    place_parts(out, ammo_stack(seed + 4), (3.25, 4.15, 0.0), Rz(1.4), rename={"Crates": "BayCrates"})
    place_parts(out, fuel_drums(seed + 5), (3.3, 5.2, 0.0), Rz(0.3), rename={"Drums": "BayDrums", "Chocks": "BayChocks"})
    nt, np_ = Field("Net"), Field("NetPoles")
    NX0, NX1, NY0, NY1, NZ = 1.55, 3.85, 3.65, 5.75, 1.05
    poles = [(NX0, NY0), (NX1, NY0), (NX0, NY1), (NX1, NY1), ((NX0 + NX1) / 2, (NY0 + NY1) / 2)]
    for i, (x, y) in enumerate(poles):
        top = NZ + (0.3 if i == 4 else 0.0)
        pole(np_, (x, y, -0.03), (x, y, top), 0.022)

    CX, CY, HX, HY = (NX0 + NX1) / 2, (NY0 + NY1) / 2, (NX1 - NX0) / 2 + 0.2, (NY1 - NY0) / 2 + 0.18

    def net(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        Q = np.stack([x, y, np.zeros_like(x)], 1)
        u, w = (x - F32(CX)) / F32(HX), (y - F32(CY)) / F32(HY)
        # draped over the poles: a peak on the middle one, sagging between the corners, the garnish lumpy
        h = (F32(NZ - 0.06) + F32(0.3) * np.exp(-(u * u + w * w) * F32(2.5)) - F32(0.06) * (np.abs(np.sin(u * F32(math.pi))) + np.abs(np.sin(w * F32(math.pi))))
             + NOISE.fbm(Q * F32(5.0), 2) * F32(0.025))
        rect = np.maximum(np.abs(u) * F32(HX) - F32(HX), np.abs(w) * F32(HY) - F32(HY)) + NOISE.fbm(Q * F32(2.5) + F32(5.0), 2) * F32(0.1)
        hz = h - np.maximum(rect + F32(0.25), F32(0.0)) * F32(1.2)          # its skirts hang down beyond the poles
        return (np.maximum(np.abs(z - hz) - F32(0.03), rect) * F32(0.7)).astype(F32)
    nt.add(Func(net, (NX0 - 0.8, NY0 - 0.8, 0.0), (NX1 + 0.8, NY1 + 0.8, NZ + 0.45)), k=0.0)
    nt.inter(Plane((0, 0, 0.04), (0, 0, -1)))
    ground_cut(np_, -0.02)
    out += [("Net", nt, fine(0.01, 0.02), "camo"), ("NetPoles", np_, fine(0.005, 0.01), "timber")]
    # ---- behind the berm: a container, a big satellite dish, a second mast
    ct = Field("Container")
    _container(ct, (5.55, -2.0, 0.0), 0.3)
    ground_cut(ct, -0.02)
    out.append(("Container", ct, fine(0.008, 0.016), "container"))
    bd2 = Field("BigDish")
    vt2, ax2 = v3((5.6, 1.7, 1.15)), unit(v3((-0.5, -0.2, 0.85)))
    Rf2 = rot_from_axes(z_axis=ax2).astype(F32)

    def bdish(P, Rd=0.75, Fc=0.45):
        Q = (P - F32(vt2)) @ Rf2
        r2 = Q[:, 0] ** 2 + Q[:, 1] ** 2
        d = np.abs(Q[:, 2] - r2 / F32(4 * Fc)) / np.sqrt(F32(1) + r2 / F32(4 * Fc * Fc)) - F32(0.014)
        return np.maximum(d, np.sqrt(r2) - F32(Rd)).astype(F32)
    bd2.add(Func(bdish, vt2 - 1.0, vt2 + 1.0), k=0.0)
    pole(bd2, vt2, v3((5.6, 1.7, 0.4)), 0.06)
    bd2.add(RoundBox((5.6, 1.7, 0.2), (0.25, 0.25, 0.2), 0.03), k=0.0, label=7)
    for i in range(3):
        a = 2 * math.pi * i / 3
        q = vt2 + rot_from_axes(z_axis=ax2) @ v3((math.cos(a) * 0.6, math.sin(a) * 0.6, 0.36 / (4 * 0.45)))
        pole(bd2, q, vt2 + ax2 * 0.45, 0.01)
    ground_cut(bd2, -0.02)
    out.append(("BigDish", bd2, fine(0.008, 0.016), "radome"))
    m2 = Field("Mast2")
    lattice_mast(m2, (6.3, -0.2, 0), -0.05, 4.2, 0.26, 0.1, legs=3, step=0.32, rod=0.014)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        pole(m2, (6.3 + math.cos(a) * 0.1, -0.2 + math.sin(a) * 0.1, 3.6 + k * 0.15), (6.3 + math.cos(a) * 0.3, -0.2 + math.sin(a) * 0.3, 3.75 + k * 0.15), 0.012)
        m2.add(RoundBox((6.3 + math.cos(a) * 0.36, -0.2 + math.sin(a) * 0.36, 3.75 + k * 0.15), (0.04, 0.1, 0.16), 0.02, R=Rz(a)), k=0.0, label=7)
    ground_cut(m2, -0.03)
    wn = Field("Warn2")
    wn.add(Sphere((6.3, -0.2, 4.28), 0.04), k=0.0)
    out += [("Mast2", m2, fine(0.006, 0.012), "galv"), ("Warn2", wn, fine(0.004, 0.008), "glow_red")]
    return out


CITY_FIRES = [(-0.3, -1.12, 0.3), (-0.3, 1.12, 0.3)]                  # the burn barrels (Blender: x, y, z; game.gd: x, z, -y)
CITY_SMOKE = [(3.15, 1.25, BH + 1.2)]                               # the generator's exhaust on the roof
CITY_LIGHTS = []                                                     # filled below: [(position, aim)] of every flood head
for _sy in (-1, 1):
    for _dy in (-0.2, 0.2):
        CITY_LIGHTS.append(((0.25 - 0.06, _sy * 2.15 + _dy, 2.32), (-0.75, -_sy * 0.3, -0.6)))
    CITY_LIGHTS.append(((BX0 - 0.05, _sy * (BY - 0.05), BH + 0.38), (-0.6, -_sy * 0.2, -0.7)))
CITY_LIGHTS.append(((1.55 - 0.5, -4.5, 2.48), (-0.8, 0.45, -0.4)))


# ------------------------------------------------------------------------------------------------ the kits
# prop name -> (builder, game-mesh triangle budget), as decor_props.KITS. Tuft and Flowers are direct geometry
# (decor_build).
def KITS(theme):
    if theme == "military":
        return {
            "Hesco_A": (lambda: hesco(601, "row"), 700), "Hesco_B": (lambda: hesco(602, "ell"), 800), "Sandbags": (lambda: sandbags(603), 1200),
            "Drums": (lambda: fuel_drums(604), 800), "Jerrycans": (lambda: jerrycans(605), 600), "Ammo": (lambda: ammo_stack(606), 900),
            "Cones": (lambda: cones(607), 300), "LightTower": (lambda: light_tower(608), 1100), "Fence": (lambda: chainlink(609), 700),
            "Barriers": (lambda: barriers(610), 400), "Scrub_A": (lambda: dry_scrub(611, 0.8), 500), "Scrub_B": (lambda: dry_scrub(612, 0.6), 400),
            "Humvee": (lambda: humvee(613), 1400),
            "Hangar": (lambda: hangar(614), 5000), "Tower": (lambda: control_tower(615), 3000), "Jet": (lambda: jet(616), 3400),
            "Heli": (lambda: helipad(617), 3400), "FuelTruck": (lambda: fuel_truck(618), 2400), "Radome": (lambda: radome(619), 2000),
            "Helicopter": (lambda: helipad(628, pad=False), 2800),
            "Rubble_A": (lambda: rubble(620), 800), "Rubble_B": (lambda: rubble(621, metal=True), 900), "Wreck": (lambda: wreck(622), 1200),
            "Dish": (lambda: radar_dish(623), 1800), "Generator": (lambda: generator(624), 1400), "AAGun": (lambda: aa_gun(625), 2000),
            "Pallet": (lambda: pallet_stack(626), 1100), "Forklift": (lambda: forklift(627), 1500),
        }
    if theme == "metro":
        return {
            "StreetLight": (lambda: street_light(631), 500), "TrafficLight": (lambda: traffic_light(632), 700), "Bench": (lambda: bench_modern(633), 500),
            "BusStop": (lambda: bus_stop(634), 1000), "Hydrant": (lambda: hydrant(635), 300), "NewsBoxes": (lambda: news_boxes(636), 500),
            "Bollards": (lambda: bollards(637), 300), "TrashCan": (lambda: trash_can(638), 300), "Planter": (lambda: planter(639), 1300),
            "Tree_A": (lambda: street_tree(3.0, 640, guard=True), 1600), "Tree_B": (lambda: street_tree(2.6, 641, guard=False), 1400),
            "Tree_C": (lambda: linden(2.4, 642), 1300),
            "Tower_A": (lambda: office_tower(643, 0), 4000), "Tower_B": (lambda: office_tower(644, 1), 4000), "Diner": (lambda: diner(645), 3200),
            "Shops": (lambda: shops(646), 4200), "Billboard": (lambda: billboard(647), 1400), "Bus": (lambda: city_bus(648), 2000),
            "Taxi": (lambda: taxi(649), 1300),
            "MidRise": (lambda: midrise(650), 4200), "Fountain": (lambda: fountain(651), 1500),
        }
    if theme == "suburb":
        return {
            "Mailbox": (lambda: mailbox(661), 300), "Picket": (lambda: picket_fence(662), 500), "Hedge": (lambda: box_hedge(663), 500),
            "Gnome": (lambda: gnome(664), 400), "Bike": (lambda: bike(665), 700), "Bins": (lambda: wheelie_bins(666), 600),
            "Chairs": (lambda: lawn_chairs(667), 800), "Maple_A": (lambda: maple(2.5, 668), 1300), "Maple_B": (lambda: maple(2.2, 669, red=True), 1200),
            "Oak": (lambda: yard_oak(2.7, 670), 1500), "Pots": (lambda: flower_pots(671), 600),
            "House_A": (lambda: colonial(672), 6000), "House_B": (lambda: ranch(673), 4000), "Minivan": (lambda: minivan(674), 1300),
            "Playground": (lambda: playground(675), 3000), "Hoop": (lambda: hoop(676), 900), "Treehouse": (lambda: treehouse(677), 3600),
            "House_C": (lambda: cape_cod(678), 3600), "Loungers": (lambda: loungers(679), 700), "Umbrella": (lambda: umbrella(680), 900),
            "DivingBoard": (lambda: diving_board(681), 500), "PoolLadder": (lambda: pool_ladder(682), 300),
            "House_D": (lambda: colonial(683, drive=False, siding="siding_d"), 4200), "House_E": (lambda: ranch(684, drive=False, siding="siding_a"), 3700),
        }
    if theme == "bunker_city":
        return {"City": (lambda: modern_city(691), 21000)}
    raise KeyError(theme)
