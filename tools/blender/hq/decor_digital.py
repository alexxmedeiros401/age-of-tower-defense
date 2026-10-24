"""HQ Digital Age map props, sculpted as distance fields like decor_props, decor_bronze, ... decor_industrial and
decor_modern (same conventions: every builder returns its parts [(part name, Field, voxel, material key)], built at the
origin, Z up, ground at z = 0, a landmark's front toward -Y, a vehicle's nose toward +X; KITS lists each theme's props
and their game-mesh triangle budgets; decor_build.materials resolves the keys).

The Digital Age belongs to one near-future tech corps (graphite and midnight navy, glowing magenta-violet trim); the
robots it fights are white with hazard orange, cyan energy and red eyes, so the corps' own things glow violet.
Cleanroom (lab): lab carts, instrument racks, server racks with their status lights, cable reels, hazard bollards,
glass partitions, potted lab ferns, spill kits, gas cylinders; landmarks: a robotic arm cell behind safety glass, a
particle accelerator's ring segment between its shielding walls, a glass-walled control room, a containment pod, a
gantry crane holding a crate; for the no-build zones lab machines (a robotic arm on its plinth by a conveyor, a
centrifuge, a scanner) and cryogenic tanks with frosted pipes and venting vapour.
Dish Array (satellite): small dishes, antenna masts with red warning lights, solar panels, cable drums, desert scrub,
cacti and rocks, fence sections, junction boxes; landmarks: a giant radio telescope, the control building with its lit
windows, a radar tower, a fuel tank, a parked utility truck; for the no-build zones a big dish on its mount and solar
arrays with their inverters.
Neon Grid (neon): neon street signs, holo-ad pylons, vending machines, food carts under lanterns, cable poles, trash
bins, magenta and cyan street lights, puddles, planters of glowing plants; landmarks: towers with lit windows and neon
signs (invented glyphs), a giant holographic billboard, a noodle bar, a monorail pylon, a parked hover-car; for the
no-build zones energy pylons with crackling coils and the rims of glowing data pits (the shafts are in the ground).
The Digital city at the end of every Digital Age road (a hardened high-tech campus: the glass-and-steel lab with its
server racks glowing through the glass, the corps' violet holo-emblem, an antenna array, a drone on its pad, the
security gate with its barrier arms and light strips) is its own kit ("lab_city", digital_city.glb).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Chain, Plane, Func, rot_from_axes, v3, NOISE, euler
import decor_props as DP
from decor_props import vx, wob, convex, rock
from decor_bronze import fine, unit, box_bounds, ground_cut, cut_above, place, place_parts, convex_w, walls_box, scrub, saguaro, barrel, sandrock
from decor_iron import Rz, R_xz, cone

from decor_gunpowder import leaf, mirror
from decor_industrial import retex
from decor_modern import (box, wheel, car, drum, pole, flood_head, lattice_mast, chainlink, digits, stencil, rrect, curtain_box, Scaled,
                          RX, RY)

F32 = np.float32
Z = v3((0, 0, 1))


# ------------------------------------------------------------------------------------------------ helpers
def seg(f, a, b, r, rb=None, k=0.0, label=0):
    """A rod from a to b (field f)."""
    f.add(RoundCone(v3(a), v3(b), r, r if rb is None else rb), k=k, label=label)


def strip(f, a, b, w, t=0.006, up=(0, 0, 1)):
    """A flat light strip from a to b (field f): w wide, t thick, its face toward `up` (as far as it can be)."""
    a, b = v3(a), v3(b)
    d = b - a
    L = float(np.linalg.norm(d))
    x = d / max(L, 1e-9)
    n = v3(up) - x * float(np.dot(v3(up), x))
    if np.linalg.norm(n) < 1e-6:
        n = v3((0, 0, 1)) if abs(x[2]) < 0.9 else v3((1, 0, 0))
    n = unit(n)
    y = np.cross(n, x)
    f.add(RoundBox((a + b) / 2, (L / 2, w / 2, t), min(t, w / 2) * 0.9, R=np.stack([x, y, n], axis=1)), k=0.0)


def screen(f, gl, c, nrm, w, h, bezel=0.018, depth=0.03, tilt=0.0, label=7):
    """A flat screen at c facing nrm (horizontal, tilted back by `tilt`): its bezel and back (field f, label) and the
    glowing face (gl), w by h."""
    n = unit(v3((nrm[0], nrm[1], 0.0)))
    s = v3((n[1], -n[0], 0.0))
    up = Z * math.cos(tilt) - n * math.sin(tilt)
    nn = n * math.cos(tilt) + Z * math.sin(tilt)
    R = np.stack([s, up, nn], axis=1)
    c = v3(c)
    f.add(RoundBox(c - nn * (depth / 2), (w / 2 + bezel, h / 2 + bezel, depth / 2), 0.008, R=R), k=0.0, label=label)
    gl.add(RoundBox(c + nn * 0.001, (w / 2, h / 2, 0.004), 0.003, R=R), k=0.0)


def hexagon(c, R, h, z0=0.0, rr=0.0, rot=0.0):
    """A hexagonal prism (corner radius R) standing from z0 to z0 + h at c."""
    c = v3((c[0], c[1], 0.0))
    pl = [((c[0], c[1], z0 + h), (0, 0, 1)), ((c[0], c[1], z0), (0, 0, -1))]
    ri = R * math.cos(math.pi / 6)
    for i in range(6):
        a = rot + math.pi / 6 + i * math.pi / 3
        pl.append(((c[0] + math.cos(a) * ri, c[1] + math.sin(a) * ri, z0), (math.cos(a), math.sin(a), 0.0)))
    return convex(pl, (c[0] - R - 0.1, c[1] - R - 0.1, z0 - 0.1), (c[0] + R + 0.1, c[1] + R + 0.1, z0 + h + 0.1))


def ring(c, R, r, axis=(0, 0, 1)):
    return Torus(v3(c), R, r, R=rot_from_axes(z_axis=axis))


def dish_fn(vert, ax, Rd, Fc, th=0.012):
    """A parabolic dish (its vertex at vert, opening along ax, rim radius Rd, focal length Fc, half thickness th)."""
    vert = v3(vert)
    Rf = rot_from_axes(z_axis=unit(ax)).astype(F32)

    def fn(P):
        Q = (P - F32(vert)) @ Rf
        r2 = Q[:, 0] ** 2 + Q[:, 1] ** 2
        d = np.abs(Q[:, 2] - r2 / F32(4 * Fc)) / np.sqrt(F32(1) + r2 / F32(4 * Fc * Fc)) - F32(th)
        return np.maximum(d, np.sqrt(r2) - F32(Rd)).astype(F32)
    e = Rd + 0.1
    return Func(fn, vert - e - Rd * Rd / (4 * Fc), vert + e + Rd * Rd / (4 * Fc))


def dish_rim(vert, ax, Rd, Fc, r=0.02):
    vert = v3(vert)
    Rf = rot_from_axes(z_axis=unit(ax)).astype(F32)
    zr = Rd * Rd / (4 * Fc)

    def fn(P):
        Q = (P - F32(vert)) @ Rf
        return (np.sqrt((np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2) - F32(Rd)) ** 2 + (Q[:, 2] - F32(zr)) ** 2) - F32(r)).astype(F32)
    e = Rd + 0.1
    return Func(fn, vert - e - zr, vert + e + zr)


def dish_point(vert, ax, Rd, Fc, a, t):
    """A point on the dish's surface: at fraction t of the rim radius, angle a round its axis."""
    R = rot_from_axes(z_axis=unit(ax))
    r = Rd * t
    return v3(vert) + R @ v3((math.cos(a) * r, math.sin(a) * r, r * r / (4 * Fc)))


def bar(f, p, q, r, nrm):
    """A flat light bar from p to q (field f), r wide each side, lying in the face of normal nrm: a stroke of a glyph.
    (Flat bars decimate to a few clean faces each; round tubes collapsed into blobs in the game meshes.)"""
    p, q = v3(p), v3(q)
    d = q - p
    L = float(np.linalg.norm(d))
    if L < 1e-6:
        return
    x = d / L
    n = unit(v3(nrm) - x * float(np.dot(v3(nrm), x)))
    y = np.cross(n, x)
    f.add(RoundBox((p + q) / 2, (L / 2 + r, r, r * 0.8), r * 0.3, R=np.stack([x, y, n], axis=1)), k=0.0)


def glyphs(f, c, side, n, h, seed, r=0.01, up=(0, 0, 1)):
    """A line of n invented glyphs (no real script) in neon tube (field f) centred at c, reading along `side`, each h
    high: three to five strokes joining points of a 3 x 4 grid, every glyph its own."""
    rng = np.random.default_rng(seed)
    side = unit(side)
    up = unit(up)
    c = v3(c)
    w = h * 0.62
    for i in range(n):
        o = c + side * ((i - (n - 1) / 2) * w * 1.45 - w / 2) - up * (h / 2)
        pts = [(x / 2.0, y / 3.0) for x in range(3) for y in range(4)]
        k = int(rng.integers(3, 6))
        cur = pts[int(rng.integers(0, len(pts)))]
        strokes = []
        for _ in range(k):
            nxt = pts[int(rng.integers(0, len(pts)))]
            if nxt == cur:
                continue
            strokes.append((cur, nxt))
            cur = nxt if rng.random() < 0.7 else pts[int(rng.integers(0, len(pts)))]
        if not strokes:
            strokes = [((0.0, 0.0), (0.0, 1.0)), ((0.0, 1.0), (1.0, 1.0))]
        strokes.append(((0.0, 1.0), (1.0, 1.0)) if rng.random() < 0.4 else ((0.5, 0.0), (0.5, 1.0)))
        nrm = np.cross(side, up)
        for (a, b) in strokes:
            p = o + side * (a[0] * w) + up * (a[1] * h)
            q = o + side * (b[0] * w) + up * (b[1] * h)
            bar(f, p, q, r, nrm)


def railing_line(f, pts, h=0.42, step=0.32, r=0.012, z0=0.0):
    """A railing along a polyline (field f): posts every `step`, a top rail and a mid rail."""
    pts = [v3(p) for p in pts]
    for a, b in zip(pts[:-1], pts[1:]):
        L = float(np.linalg.norm(b - a))
        n = max(1, int(round(L / step)))
        for i in range(n + 1):
            q = a + (b - a) * (i / n)
            seg(f, q + Z * (z0 - 0.02), q + Z * (z0 + h), r)
        seg(f, a + Z * (z0 + h), b + Z * (z0 + h), r * 1.1)
        seg(f, a + Z * (z0 + h * 0.5), b + Z * (z0 + h * 0.5), r * 0.8)


def stack_light(parts_f, c, z0, glows):
    """A machine's stack light on a short post at c from z0: green, amber and red segments (fields given in `glows`:
    {key: field}), a dark cap."""
    f = parts_f
    c = v3(c)
    seg(f, c + Z * z0, c + Z * (z0 + 0.12), 0.012)
    for i, k in enumerate(("glow_green", "glow_amber", "glow_red")):
        glows[k].add(Cylinder(c + Z * (z0 + 0.15 + i * 0.055), 0.03, 0.05, rr=0.006), k=0.0)
    f.add(Cylinder(c + Z * (z0 + 0.32), 0.032, 0.025, rr=0.008), k=0.0)


def finish_glows(out, glows, vox=None):
    """Append the non-empty glow fields of `glows` {material key: field} to out."""
    for k, g in glows.items():
        if any(op[0] == "add" for op in g.ops):
            out.append((g.name, g, vox or fine(0.004, 0.008), k))
    return out


def G(*keys, prefix=""):
    return {k: Field(prefix + "".join(w.capitalize() for w in k.split("_")[1:])) for k in keys}


# ------------------------------------------------------------------------------------------------ Cleanroom: scatter
def lab_cart(seed=0):
    """A lab trolley (handle toward -X): white shelves on a steel frame and castors, a monitor (lit), a keyboard, a rack
    of sample tubes and a sealed case on top, storage boxes underneath."""
    out = []
    fr, sh, kt, tf, sc, tb = Field("Frame"), Field("Shelves"), Field("Kit"), Field("Castors"), Field("Screen"), Field("Tubes")
    hx, hy = 0.34, 0.21
    for sx in (-1, 1):
        for sy in (-1, 1):
            seg(fr, (sx * hx, sy * hy, 0.07), (sx * hx, sy * hy, 0.8), 0.013)
            seg(fr, (sx * hx, sy * hy, 0.07), (sx * hx, sy * hy, 0.04), 0.008)
            wheel(tf, kt, (sx * hx, sy * hy, 0.035), (0, sy, 0), 0.035, 0.025, hub=0.5)
    for z in (0.18, 0.5, 0.78):
        box(sh, (0, 0, z), (hx + 0.02, hy + 0.02, 0.013), 0.008)
        box(sh, (0, 0, z + 0.022), (hx + 0.02, hy + 0.02, 0.008), 0.004, k=0.0, label=7)
        sh.sub(RoundBox((0, 0, z + 0.03), (hx - 0.01, hy - 0.01, 0.012), 0.004), k=0.0)
    for sy in (-1, 1):                                              # the push handle
        seg(fr, (-hx, sy * 0.16, 0.74), (-hx - 0.08, sy * 0.16, 0.88), 0.011)
    seg(fr, (-hx - 0.08, -0.16, 0.88), (-hx - 0.08, 0.16, 0.88), 0.014)
    screen(kt, sc, (0.12, 0.05, 0.98), (0.3, -1, 0), 0.24, 0.15, tilt=0.15)
    seg(kt, (0.12, 0.08, 0.8), (0.12, 0.08, 0.9), 0.015, label=7)
    box(kt, (0.12, 0.08, 0.805), (0.06, 0.05, 0.008), 0.004, label=7)
    box(kt, (-0.08, -0.08, 0.805), (0.13, 0.05, 0.008), 0.004, label=7)
    box(kt, (-0.17, 0.1, 0.83), (0.08, 0.06, 0.03), 0.006, label=7)
    for i in range(5):                                              # sample tubes in their rack, coloured caps
        q = v3((-0.24 + i * 0.03, 0.1, 0.875))
        tb.add(Cylinder(q, 0.009, 0.07, rr=0.004), k=0.0, label=(5 if i % 2 else 8))
    box(kt, (0.18, -0.06, 0.56), (0.12, 0.09, 0.05), 0.012, label=5)
    box(kt, (-0.12, 0.0, 0.25), (0.16, 0.15, 0.06), 0.01, label=5)
    box(kt, (0.18, 0.04, 0.24), (0.1, 0.12, 0.05), 0.01, label=0)
    for f in (fr, tf):
        ground_cut(f, -0.01)
    out += [("Frame", fr, fine(0.004, 0.008), "chrome"), ("Shelves", sh, fine(0.005, 0.01), "white_tech"), ("Kit", kt, fine(0.004, 0.008), "graphite"),
            ("Castors", tf, fine(0.004, 0.008), "rubber"), ("Screen", sc, fine(0.004, 0.008), "glow_screen"), ("Tubes", tb, fine(0.003, 0.006), "vials")]
    return out


def instrument_rack(seed=0):
    """A rolling instrument rack (front toward -Y): a graphite 19-inch frame on castors stacked with instruments, their
    screens and status lights lit, rows of knobs, patch cables looping from socket to socket."""
    out = []
    rk, un, tf, sc, gl = Field("Rack"), Field("Units"), Field("Castors"), Field("Screens"), Field("Leds")
    vi, cb = Field("LedsV"), Field("Cables")
    hx, hy, H = 0.28, 0.24, 1.12
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(rk, (sx * hx, sy * hy, 0.6), (0.022, 0.022, 0.52), 0.006)
            wheel(tf, rk, (sx * (hx - 0.03), sy * (hy - 0.03), 0.04), (0, sy, 0), 0.04, 0.03)
    box(rk, (0, 0, H + 0.01), (hx + 0.025, hy + 0.025, 0.02), 0.008)
    box(rk, (0, 0, 0.1), (hx + 0.025, hy + 0.025, 0.02), 0.008)
    rng = np.random.default_rng(seed)
    z = 0.14
    for i, uh in enumerate((0.2, 0.12, 0.24, 0.1, 0.18, 0.12)):
        if z + uh > H - 0.02:
            break
        zc = z + uh / 2
        lab = 0 if i % 2 == 0 else 7
        box(un, (0, 0.0, zc), (hx - 0.03, hy - 0.04, uh / 2 - 0.006), 0.008, label=lab)
        box(un, (0, -hy + 0.01, zc), (hx + 0.012, 0.008, uh / 2 - 0.004), 0.004, k=0.0, label=7)
        if uh >= 0.18:
            screen(un, sc, (-0.1, -hy - 0.004, zc + 0.01), (0, -1, 0), 0.2, uh * 0.55, bezel=0.01, depth=0.012)
            for j in range(3):
                un.add(Cylinder((0.08 + j * 0.055, -hy - 0.01, zc - 0.02), 0.014, 0.02, rr=0.004, R=RY), k=0.002, label=6)
        else:
            for j in range(3):
                q = v3((-0.17 + j * 0.13, -hy - 0.006, zc))
                (gl if rng.random() < 0.6 else vi).add(RoundBox(q, (0.035, 0.006, 0.012), 0.005), k=0.0)
            un.add(Cylinder((0.22, -hy - 0.012, zc), 0.016, 0.02, rr=0.004, R=RY), k=0.002, label=6)
        z += uh
    for k in range(3):                                              # patch cables looping down the front
        x0, x1 = -0.18 + k * 0.12, -0.05 + k * 0.14
        z0, z1 = 0.32 + k * 0.2, 0.62 - k * 0.1
        mid = v3(((x0 + x1) / 2, -hy - 0.05, min(z0, z1) - 0.06))
        cb.add(Chain([v3((x0, -hy - 0.015, z0)), mid, v3((x1, -hy - 0.015, z1))], [0.006] * 3, k=0.02), k=0.0, label=(5, 8, 9)[k])
    ground_cut(tf, -0.01)
    ground_cut(rk, -0.01)
    out += [("Rack", rk, fine(0.004, 0.008), "graphite"), ("Units", un, fine(0.004, 0.008), "instrument"), ("Castors", tf, fine(0.004, 0.008), "rubber"),
            ("Screens", sc, fine(0.004, 0.008), "glow_screen"), ("Leds", gl, fine(0.003, 0.006), "glow_green"), ("LedsV", vi, fine(0.003, 0.006), "glow_violet"),
            ("Cables", cb, fine(0.003, 0.006), "cables")]
    return out


def server_rack(f, dr, leds, c, yaw=0.0, W=0.3, D=0.4, H=1.55, open_door=False, seed=0):
    """One server cabinet (fields: f the graphite cabinet, dr its perforated door, leds {key: field}) at c, its front
    toward -Y turned by yaw: the perforated door with its handle and the blinking lights shining through it (or, opened,
    the blade servers behind it), the status bar at the top, cable grommets on the roof."""
    R = Rz(yaw)
    c = v3(c)
    rng = np.random.default_rng(seed)
    f.add(RoundBox(c + Z * (H / 2 + 0.03), (W, D, H / 2), 0.02, R=R), k=0.0)
    f.add(RoundBox(c + Z * 0.02, (W - 0.02, D - 0.02, 0.025), 0.006, R=R), k=0.0, label=7)
    f.add(RoundBox(c + R @ v3((0, 0, H + 0.04)), (W + 0.01, D + 0.01, 0.012), 0.006, R=R), k=0.003, label=7)
    for sx in (-1, 1):
        f.add(Cylinder(c + R @ v3((sx * W * 0.5, D * 0.3, H + 0.055)), 0.04, 0.02, rr=0.006), k=0.003, label=7)
    fz0, fz1 = 0.12, H - 0.08
    if not open_door:
        dr.add(RoundBox(c + R @ v3((0, -D - 0.006, (fz0 + fz1) / 2 + 0.03)), (W - 0.025, 0.008, (fz1 - fz0) / 2), 0.006, R=R), k=0.0)
        f.add(RoundBox(c + R @ v3((W - 0.06, -D - 0.022, H * 0.55)), (0.012, 0.012, 0.09), 0.006, R=R), k=0.003, label=6)
        for j in range(9):                                          # lights glowing through the perforations
            zz = fz0 + 0.07 + j * (fz1 - fz0 - 0.12) / 8
            for i in range(2):
                if rng.random() < 0.75:
                    key = "glow_green" if rng.random() < 0.65 else ("glow_cyan" if rng.random() < 0.5 else "glow_amber")
                    leds[key].add(RoundBox(c + R @ v3((-W + 0.1 + i * 0.16 + rng.uniform(-0.03, 0.03), -D - 0.016, zz + 0.03)),
                                           (rng.uniform(0.025, 0.05), 0.005, 0.009), 0.004, R=R), k=0.0)
    else:                                                           # the door swung open, the blades inside
        f.sub(RoundBox(c + R @ v3((0, -D, (fz0 + fz1) / 2 + 0.03)), (W - 0.03, 0.06, (fz1 - fz0) / 2), 0.006, R=R), k=0.0)
        hinge = c + R @ v3((-W, -D - 0.01, 0))
        d = R @ unit(v3((-0.5, -1.0, 0)))
        Rd = np.stack([d, unit(np.cross(Z, d)), Z], axis=1)
        dr.add(RoundBox(hinge + d * (W - 0.02) + Z * ((fz0 + fz1) / 2 + 0.03), (W - 0.025, 0.008, (fz1 - fz0) / 2), 0.006, R=Rd), k=0.0)
        n = int((fz1 - fz0) / 0.075)
        for j in range(n):
            zz = fz0 + 0.07 + j * 0.075
            f.add(RoundBox(c + R @ v3((0, -D + 0.04, zz)), (W - 0.04, 0.02, 0.03), 0.004, R=R), k=0.0, label=(7 if j % 3 else 0))
            for i in range(2):
                if rng.random() < 0.8:
                    key = "glow_green" if rng.random() < 0.65 else ("glow_violet" if rng.random() < 0.5 else "glow_amber")
                    leds[key].add(RoundBox(c + R @ v3((-W + 0.1 + i * 0.2, -D + 0.018, zz)), (rng.uniform(0.02, 0.045), 0.005, 0.009), 0.004, R=R), k=0.0)
    leds["glow_violet"].add(RoundBox(c + R @ v3((0, -D - 0.012, H - 0.02)), (W - 0.05, 0.006, 0.012), 0.004, R=R), k=0.0)


def server_racks(seed=0, n=2, open_door=False):
    """Server cabinets side by side (front toward -Y), their lights glowing through the perforated doors (one standing
    open on its blades), a cable tray across their roofs carrying bundles of cable."""
    out = []
    f, dr, tr, cb = Field("Cabinets"), Field("Doors"), Field("Tray"), Field("Cables")
    leds = G("glow_green", "glow_cyan", "glow_amber", "glow_violet", prefix="Led")
    W = 0.3
    xs = [(i - (n - 1) / 2) * (2 * W + 0.02) for i in range(n)]
    for i, x in enumerate(xs):
        server_rack(f, dr, leds, (x, 0, 0), 0.0, W=W, open_door=(open_door and i == n - 1), seed=seed + i)
    L = (xs[-1] - xs[0]) / 2 + W + 0.1
    for sy in (-1, 1):
        seg(tr, (-L, sy * 0.12, 1.75), (L, sy * 0.12, 1.75), 0.01)
    for x in np.linspace(-L, L, 2 * n + 2):
        seg(tr, (x, -0.12, 1.75), (x, 0.12, 1.75), 0.008)
    for sx in (-1, 1):
        seg(tr, (sx * L, 0.0, 1.6), (sx * L, 0.0, 1.75), 0.01)
    for k in range(3):
        y = -0.07 + k * 0.07
        cb.add(Chain([v3((-L - 0.05, y, 1.78)), v3((0, y, 1.785)), v3((L + 0.05, y, 1.78))], [0.022, 0.022, 0.022], k=0.01), k=0.0, label=(0, 5, 9)[k])
    for x in xs:
        cb.add(Chain([v3((x - 0.1, 0.05, 1.76)), v3((x - 0.12, 0.05, 1.7)), v3((x - 0.15, 0.1, 1.6))], [0.015] * 3, k=0.01), k=0.0, label=5)
    ground_cut(f, -0.01)
    out += [("Cabinets", f, fine(0.005, 0.01), "graphite"), ("Doors", dr, fine(0.004, 0.008), "perforated"), ("Tray", tr, fine(0.004, 0.008), "galv"),
            ("Cables", cb, fine(0.004, 0.008), "cables")]
    return finish_glows(out, leds)


def cable_reel(seed=0, Rf=0.27, R0=0.13, W=0.16, reel="plywood", cable="cable_orange", end=True):
    """A cable reel standing on its flanges: plywood discs on an axle, orange cable wound round the drum, its end run
    off across the floor."""
    out = []
    rl, cb = Field("Reel"), Field("Cable")
    for sy in (-1, 1):
        rl.add(Cylinder((0, sy * W, Rf), Rf, 0.025, rr=0.008, R=RY), k=0.0)
        rl.sub(Cylinder((0, sy * (W + 0.02), Rf), 0.035, 0.03, R=RY), k=0.0)
        for i in range(4):                                          # bolts round the hub
            a = math.pi / 4 + i * math.pi / 2
            rl.add(Cylinder((math.cos(a) * 0.07, sy * (W + 0.014), Rf + math.sin(a) * 0.07), 0.01, 0.01, R=RY), k=0.002, label=6)
    rl.add(Cylinder((0, 0, Rf), R0, 2 * W, R=RY), k=0.0)
    rc = 0.017 * Rf / 0.27                                          # the wound cable: a drum grooved turn by turn
    Rw = Rf - 0.04
    cb.add(Func(lambda P: (np.maximum(np.sqrt(P[:, 0] ** 2 + (P[:, 2] - F32(Rf)) ** 2) - F32(Rw), np.abs(P[:, 1]) - F32(W - 0.012))
                           + F32(rc * 0.35) * (F32(1) - np.abs(np.cos(P[:, 1] * F32(math.pi / (2 * rc)))))).astype(F32),
                (-Rf, -W, 0.0), (Rf, W, 2 * Rf)), k=0.0)
    ground_cut(rl, -0.01)
    out += [("Reel", rl, fine(0.005, 0.01), reel), ("Cable", cb, fine(0.005, 0.01), cable)]
    if end:
        ce = Field("CableEnd")
        ce.add(Chain([v3((0.05, -W + 0.04, Rf + R0 + 0.11)), v3((0.24, -0.12, 0.3)), v3((0.32, -0.15, 0.02)), v3((0.55, -0.25, 0.02)), v3((0.7, -0.15, 0.02))],
                     [0.017] * 5, k=0.03), k=0.0)
        ce.add(RoundBox((0.74, -0.14, 0.03), (0.04, 0.03, 0.025), 0.01), k=0.004, label=7)
        ground_cut(ce, -0.005)
        out.append(("CableEnd", ce, fine(0.004, 0.008), cable))
    return out


def hazard_bollards(seed=0):
    """Hazard bollards: three yellow posts banded black on weighted rubber bases, a yellow-and-black plastic chain
    sagging between them."""
    out = []
    ps, bs, ch = Field("Posts"), Field("Bases"), Field("Chain")
    xs = [(-0.42, 0.0), (0.0, 0.06), (0.42, 0.0)]
    for (x, y) in xs:
        bs.add(Cylinder((x, y, 0.025), 0.12, 0.05, rr=0.02), k=0.0)
        ps.add(Cylinder((x, y, 0.4), 0.04, 0.72, rr=0.01), k=0.0)
        ps.add(Sphere((x, y, 0.76), 0.042), k=0.01)
        for z in (0.2, 0.38, 0.56):
            ps.paint(Cylinder((x, y, z), 0.06, 0.06), 7)
        ps.add(Torus((x, y, 0.66), 0.042, 0.008), k=0.003, label=7)
    for (a, b) in zip(xs[:-1], xs[1:]):
        p, q = v3((a[0], a[1], 0.66)), v3((b[0], b[1], 0.66))
        mid = (p + q) / 2 - Z * 0.12
        pts = [p + (mid - p) * t if t <= 1 else mid + (q - mid) * (t - 1) for t in np.linspace(0, 2, 9)]
        for i in range(len(pts) - 1):
            ch.add(RoundCone(pts[i], pts[i + 1], 0.011, 0.011), k=0.0, label=(7 if i % 2 else 0))
    ground_cut(bs, -0.01)
    out += [("Posts", ps, fine(0.004, 0.008), "hazard_yellow"), ("Bases", bs, fine(0.004, 0.008), "rubber"), ("Chain", ch, fine(0.003, 0.006), "hazard_yellow")]
    return out


def glass_partition(seed=0, L=1.1):
    """A free-standing glass partition: an aluminium frame on two splayed feet, the glass with a frosted band across
    it and the corps' violet stripe."""
    out = []
    fr, gl = Field("Frame"), Field("Glass")
    H = 1.05
    for sx in (-1, 1):
        box(fr, (sx * L / 2, 0, H / 2 + 0.04), (0.02, 0.025, H / 2), 0.008)
        box(fr, (sx * L / 2, 0, 0.02), (0.035, 0.2, 0.02), 0.01)
    box(fr, (0, 0, H + 0.05), (L / 2 + 0.02, 0.025, 0.018), 0.008)
    box(fr, (0, 0, 0.1), (L / 2, 0.022, 0.016), 0.008)
    gl.add(RoundBox((0, 0, (H + 0.1) / 2 + 0.04), (L / 2 - 0.015, 0.006, (H - 0.1) / 2), 0.003), k=0.0)
    gl.paint(RoundBox((0, 0, 0.62), (L, 0.05, 0.12), 0.0), 5)
    gl.paint(RoundBox((0, 0, 0.47), (L, 0.05, 0.018), 0.0), 6)
    ground_cut(fr, -0.01)
    out += [("Frame", fr, fine(0.004, 0.008), "chrome"), ("Glass", gl, fine(0.003, 0.006), "lab_glass")]
    return out


def potted_fern(seed=0, s=1.0, square=False):
    """A lab fern in its white planter (round, or a tall square one), dark soil under the fronds."""
    out = []
    pt, so = Field("Pot"), Field("Soil")
    if square:
        box(pt, (0, 0, 0.21), (0.17, 0.17, 0.21), 0.03)
        pt.sub(RoundBox((0, 0, 0.44), (0.14, 0.14, 0.06), 0.01), k=0.0)
        box(pt, (0, 0, 0.03), (0.175, 0.175, 0.03), 0.01, k=0.003, label=7)
        so.add(RoundBox((0, 0, 0.385), (0.145, 0.145, 0.02), 0.01, **wob(12.0, 0.006, seed)), k=0.0)
        top = 0.4
    else:
        pt.add(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - (F32(0.13) + P[:, 2] * F32(0.13)), np.abs(P[:, 2] - F32(0.15)) - F32(0.15)).astype(F32),
                    (-0.25, -0.25, -0.05), (0.25, 0.25, 0.35)), k=0.0)
        pt.add(Torus((0, 0, 0.3), 0.17, 0.016), k=0.006)
        pt.sub(Cylinder((0, 0, 0.32), 0.15, 0.2), k=0.004)
        pt.paint(Cylinder((0, 0, 0.06), 0.3, 0.035), 7)
        so.add(Cylinder((0, 0, 0.27), 0.155, 0.03, **wob(12.0, 0.006, seed)), k=0.0)
        top = 0.28
    ground_cut(pt, -0.01)
    out += [("Pot", pt, fine(0.004, 0.008), "white_tech"), ("Soil", so, fine(0.005, 0.01), "soil")]
    lv, stl = Field("Leaves"), Field("Stalks")
    rng = np.random.default_rng(seed)
    n = 11 if square else 9
    for k in range(n):                                              # broad glossy leaves arching out on their stalks
        a = 2 * math.pi * k / n + rng.uniform(-0.25, 0.25)
        d = v3((math.cos(a), math.sin(a), 0.0))
        el = rng.uniform(0.5, 1.1)
        L = rng.uniform(0.32, 0.46) * s
        b0 = v3((0, 0, top)) + d * 0.03
        tip = b0 + (d * math.cos(el) + Z * math.sin(el)) * L
        seg(stl, b0, tip, 0.008 * s)
        u = unit(d * math.cos(el - 0.7) + Z * math.sin(el - 0.7))
        c = tip + u * 0.1 * s
        lv.add(Ellipsoid(c, (0.13 * s, 0.055 * s, 0.012 * s), R=R_xz(u, Z)), k=0.0)
    out += [("Leaves", lv, fine(0.005, 0.01), "fern"), ("Stalks", stl, fine(0.004, 0.008), "fern")]
    return out


def spill_kit(seed=0):
    """A spill kit: a yellow wheeled bin with its lid, the white label band and black lettering; a folding wet-floor
    sign beside it."""
    out = []
    bn, wh, sg = Field("Bin"), Field("Wheels"), Field("Sign")
    box(bn, (0, 0, 0.3), (0.2, 0.17, 0.26), 0.03)
    box(bn, (0, 0, 0.58), (0.215, 0.185, 0.025), 0.015, k=0.003, label=5)
    box(bn, (-0.17, 0, 0.62), (0.03, 0.15, 0.02), 0.01, k=0.004, label=5)
    bn.paint(RoundBox((0, -0.17, 0.38), (0.16, 0.03, 0.06), 0.0), 9)
    stencil(bn, (0, -0.172, 0.38), (0, -1, 0), 0.24, 0.05, label=7, n=4)
    for sy in (-1, 1):
        wheel(wh, bn, (-0.12, sy * 0.19, 0.055), (0, sy, 0), 0.055, 0.035)
    box(bn, (0.15, 0, 0.03), (0.03, 0.14, 0.03), 0.01, label=7)
    # the wet-floor sign: two yellow boards leaning together
    o = v3((0.42, -0.12, 0.0))
    for sx in (-1, 1):
        n = unit(v3((sx * 0.92, 0, 0.18)))
        Rb = rot_from_axes(z_axis=n, y_axis=(-sx * 0.18, 0, 0.92))
        c = o + v3((sx * 0.06, 0, 0.29))
        sg.add(RoundBox(c, (0.1, 0.29, 0.008), 0.006, R=Rb), k=0.0)
        sg.paint(RoundBox(c + v3((sx * 0.01, 0, 0.06)), (0.04, 0.05, 0.05), 0.0, R=Rb @ euler(0, 0, 0.785)), 7)
        sg.paint(RoundBox(c + v3((sx * 0.008, 0, -0.1)), (0.06, 0.07, 0.014), 0.0), 7)
    sg.add(Cylinder(o + Z * 0.6, 0.03, 0.03, rr=0.008, R=RY), k=0.01)
    for f in (bn, wh, sg):
        ground_cut(f, -0.01)
    out += [("Bin", bn, fine(0.004, 0.008), "hazard_yellow"), ("Wheels", wh, fine(0.004, 0.008), "rubber"), ("Sign", sg, fine(0.004, 0.008), "hazard_yellow")]
    return out


def gas_cylinders(seed=0):
    """Gas cylinders chained in their rack: three tall bottles (oxygen white-shouldered, nitrogen black, argon green)
    with brass regulators and gauges, a fourth on a hand truck."""
    out = []
    cy, rk, rg = Field("Bottles"), Field("Rack"), Field("Regulators")

    def bottle(c, h=0.78, r=0.085, lab=0, tilt=None):
        c = v3(c)
        R = np.eye(3) if tilt is None else tilt
        ax = R @ Z
        cy.add(RoundCone(c + ax * 0.04, c + ax * (h - r), r, r), k=0.0, label=lab)
        cy.add(Sphere(c + ax * (h - r), r), k=0.02, label=lab)
        cy.paint(Sphere(c + ax * (h - r * 0.6), r * 1.25), 9)                # (the white shoulder)
        cy.add(Cylinder(c + ax * (h + 0.02), 0.03, 0.06, rr=0.008, R=R), k=0.01, label=6)
        rg.add(RoundBox(c + ax * (h + 0.07), (0.035, 0.03, 0.025), 0.01, R=R), k=0.0, label=6)
        rg.add(Cylinder(c + ax * (h + 0.07) + R @ v3((0, -0.045, 0)), 0.03, 0.02, rr=0.006, R=R @ RY), k=0.004, label=6)
        rg.paint(Sphere(c + ax * (h + 0.07) + R @ v3((0, -0.058, 0)), 0.026), 9)
        cy.add(Cylinder(c + ax * 0.025, r - 0.004, 0.05, rr=0.01, R=R), k=0.005, label=7)
    for i, (x, lab) in enumerate(((-0.2, 0), (0.0, 7), (0.2, 5))):
        bottle((x, 0.0, 0.0), lab=lab)
    for x in (-0.32, 0.32):                                         # the rack: two uprights, a top hoop
        seg(rk, (x, 0.1, -0.02), (x, 0.1, 0.95), 0.02)
        box(rk, (x, 0.1, 0.01), (0.05, 0.05, 0.01), 0.004)
    for z in (0.45, 0.7):
        seg(rk, (-0.32, 0.1, z), (0.32, 0.1, z), 0.014)
        rk.add(Chain([v3((-0.32, 0.1, z - 0.02)), v3((-0.2, -0.1, z - 0.06)), v3((0.2, -0.1, z - 0.06)), v3((0.32, 0.1, z - 0.02))],
                     [0.008] * 4, k=0.02), k=0.0, label=6)
    # the hand truck with its bottle leaning back
    T = rot_from_axes(z_axis=(0.25, 0.0, 0.97))
    o = v3((0.58, -0.05, 0.0))
    bottle(o + v3((0.0, 0, 0.06)), h=0.74, r=0.08, lab=0, tilt=T)
    for sy in (-1, 1):
        seg(rk, o + v3((-0.02, sy * 0.09, 0.08)), o + T @ v3((0.02, sy * 0.09, 0.95)), 0.012)
        wheel(rk, rg, o + v3((0.08, sy * 0.13, 0.07)), (0, sy, 0), 0.07, 0.04)
    seg(rk, o + T @ v3((0.02, -0.09, 0.95)), o + T @ v3((0.02, 0.09, 0.95)), 0.012)
    box(rk, o + v3((-0.08, 0, 0.015)), (0.08, 0.1, 0.012), 0.004)
    for f in (cy, rk):
        ground_cut(f, -0.01)
    out += [("Bottles", cy, fine(0.004, 0.008), "gas"), ("Rack", rk, fine(0.004, 0.008), "graphite"), ("Regulators", rg, fine(0.003, 0.006), "brass")]
    return out


def cable_cover(seed=0):
    """A short run of cables under a yellow-and-black floor ramp."""
    f, cb = Field("Ramp"), Field("Cables")
    f.add(convex([((0, 0, 0.035), (0, 0, 1)), ((0, 0.07, 0), (0, 1, 0.9)), ((0, -0.07, 0), (0, -1, 0.9)), ((0.3, 0, 0), (1, 0, 0)), ((-0.3, 0, 0), (-1, 0, 0)),
                  ((0, 0, -0.01), (0, 0, -1))], (-0.4, -0.2, -0.05), (0.4, 0.2, 0.1)), k=0.0)
    for i in range(6):
        f.paint(RoundBox((-0.25 + i * 0.1, 0, 0.03), (0.025, 0.12, 0.05), 0.0, R=Rz(0.6)), 7)
    for sx in (-1, 1):
        cb.add(Chain([v3((sx * 0.28, 0.0, 0.012)), v3((sx * 0.4, 0.04, 0.012)), v3((sx * 0.52, -0.02, 0.012))], [0.014] * 3, k=0.02), k=0.0)
    ground_cut(f, -0.005)
    ground_cut(cb, -0.003)
    return [("Ramp", f, fine(0.004, 0.008), "hazard_yellow"), ("Cables", cb, fine(0.004, 0.008), "rubber")]


# ------------------------------------------------------------------------------------------------ Cleanroom: landmarks
def robot_arm(out, o=(0, 0, 0), yaw=0.0, reach=(1.15, -0.35), s=1.0, prefix="Arm", grip=True):
    """A six-axis robot arm (white covers, graphite joints, violet light rings) on its base at o, reaching along yaw:
    the turret, the upper arm raised, the forearm, the wrist bent down to a two-fingered gripper (grip: a glowing
    violet sample in its fingers). reach = (upper arm pitch, forearm pitch) in radians."""
    o = v3(o)
    d = v3((math.cos(yaw), math.sin(yaw), 0.0))
    side = v3((-d[1], d[0], 0.0))
    ar, gl, sm = Field(prefix), Field(prefix + "Rings"), Field(prefix + "Sample")
    Rj = rot_from_axes(z_axis=side)
    ar.add(Cylinder(o + Z * 0.08 * s, 0.26 * s, 0.16 * s, rr=0.03 * s), k=0.0, label=7)
    ar.add(Cylinder(o + Z * 0.25 * s, 0.21 * s, 0.18 * s, rr=0.05 * s), k=0.01)
    ar.sub(Torus(o + Z * 0.17 * s, 0.21 * s, 0.012 * s), k=0.004)
    gl.add(Torus(o + Z * 0.17 * s, 0.205 * s, 0.009 * s), k=0.0)
    S = o + Z * 0.52 * s
    ar.add(RoundBox(o + Z * 0.42 * s - d * 0.04 * s, (0.17 * s, 0.17 * s, 0.13 * s), 0.07 * s, R=np.stack([d, side, Z], axis=1)), k=0.03)
    ar.add(Cylinder(S, 0.14 * s, 0.4 * s, rr=0.04 * s, R=Rj), k=0.01, label=7)
    a1, a2 = reach
    u1 = d * math.cos(a1) + Z * math.sin(a1)
    E = S + u1 * 0.78 * s
    ar.add(RoundCone(S, E, 0.125 * s, 0.1 * s), k=0.02)
    ar.add(RoundBox(S + u1 * 0.2 * s + side * 0.14 * s, (0.07 * s, 0.06 * s, 0.09 * s), 0.03 * s, R=np.stack([side, d, Z], axis=1)), k=0.02)
    ar.add(Cylinder(E, 0.105 * s, 0.32 * s, rr=0.035 * s, R=Rj), k=0.01, label=7)
    u2 = d * math.cos(a2) + Z * math.sin(a2)
    W = E + u2 * 0.7 * s
    ar.add(RoundCone(E - u2 * 0.16 * s, W, 0.095 * s, 0.065 * s), k=0.02)
    ar.add(Sphere(W, 0.072 * s), k=0.01, label=7)
    t = unit(u2 * 0.35 - Z)                                         # the tool points down past the wrist
    T0 = W + t * 0.08 * s
    ar.add(Cylinder(T0, 0.055 * s, 0.05 * s, rr=0.012 * s, R=rot_from_axes(z_axis=t)), k=0.006, label=7)
    Rt = rot_from_axes(z_axis=t, y_axis=side)                         # (local y across the fingers)
    ar.add(RoundBox(T0 + t * 0.06 * s, (0.035 * s, 0.08 * s, 0.03 * s), 0.012 * s, R=Rt), k=0.004, label=7)
    for sg in (-1, 1):
        ar.add(RoundBox(T0 + t * 0.14 * s + side * sg * 0.045 * s, (0.025 * s, 0.012 * s, 0.06 * s), 0.006 * s, R=Rt), k=0.0, label=6)
    for (c, R0) in ((S, 0.13), (E, 0.1)):                            # violet light rings at the joints
        for sg in (-1, 1):
            gl.add(Torus(c + side * sg * (0.205 if R0 > 0.12 else 0.165) * s, R0 * 0.75 * s, 0.009 * s, R=Rj), k=0.0)
    gl.add(Torus(W - u2 * 0.05 * s, 0.07 * s, 0.008 * s, R=rot_from_axes(z_axis=u2)), k=0.0)
    out += [(prefix, ar, fine(0.006, 0.012), "white_tech"), (prefix + "Rings", gl, fine(0.004, 0.008), "glow_violet")]
    if grip:
        sm.add(Cylinder(T0 + t * 0.16 * s, 0.03 * s, 0.07 * s, rr=0.01 * s, R=rot_from_axes(z_axis=side)), k=0.0)
        out.append((prefix + "Sample", sm, fine(0.004, 0.008), "glow_violet"))
    return T0 + t * 0.16 * s


def arm_cell(seed=0):
    """A robotic arm cell (front toward -Y): a white six-axis arm on its epoxy plinth turned to a fixture table, behind
    safety glass in graphite posts all round (a door in the front under a light curtain), hazard stripes round the
    plinth, a stack light on a corner post and the operator's pedestal with its screen outside."""
    out = []
    pl, gs, ps, tb = Field("Plinth"), Field("Glass"), Field("Posts"), Field("Table")
    glows = G("glow_green", "glow_amber", "glow_red", "glow_violet", "glow_screen")
    HX, HY, H = 1.25, 1.0, 0.95
    box(pl, (0, 0, 0.05), (HX + 0.12, HY + 0.12, 0.05), 0.02)
    pl.paint(Func(lambda P: (np.abs(np.maximum(np.abs(P[:, 0]) - F32(HX + 0.02), np.abs(P[:, 1]) - F32(HY + 0.02))) - F32(0.06)).astype(F32),
                  (-HX - 0.3, -HY - 0.3, -0.1), (HX + 0.3, HY + 0.3, 0.2)), 8)
    ground_cut(pl, -0.02)
    xs = np.linspace(-HX, HX, 5)
    ys = np.linspace(-HY, HY, 4)
    posts = [(x, -HY) for x in xs] + [(x, HY) for x in xs] + [(-HX, y) for y in ys[1:-1]] + [(HX, y) for y in ys[1:-1]]
    for (x, y) in posts:
        box(ps, (x, y, 0.1 + H / 2), (0.03, 0.03, H / 2 + 0.02), 0.01)
    for (x0, y0, x1, y1) in ((-HX, -HY, HX, -HY), (-HX, HY, HX, HY), (-HX, -HY, -HX, HY), (HX, -HY, HX, HY)):
        c = v3(((x0 + x1) / 2, (y0 + y1) / 2, 0.1 + H + 0.02))
        hx, hy = abs(x1 - x0) / 2 + 0.03, abs(y1 - y0) / 2 + 0.03
        box(ps, c, (max(hx, 0.025), max(hy, 0.025), 0.02), 0.008, k=0.0, label=7)
        box(ps, c - Z * (H - 0.02), (max(hx, 0.025), max(hy, 0.025), 0.02), 0.008, k=0.0, label=7)
        if y0 == y1 and y0 < 0:                                     # the front: two panes and a door opening
            for (a, b) in ((-HX, -0.38), (0.38, HX)):
                gs.add(RoundBox(((a + b) / 2, y0, 0.1 + H / 2 + 0.02), ((b - a) / 2, 0.007, H / 2 - 0.02), 0.003), k=0.0)
        else:
            gs.add(RoundBox((c[0], c[1], 0.1 + H / 2 + 0.02), (max(hx - 0.03, 0.007), max(hy - 0.03, 0.007), H / 2 - 0.02), 0.003), k=0.0)
    for sx in (-1, 1):                                              # the light curtain's posts at the door
        box(ps, (sx * 0.36, -HY - 0.05, 0.1 + 0.55), (0.025, 0.025, 0.55), 0.008, k=0.0, label=7)
        strip(glows["glow_violet"], (sx * 0.33, -HY - 0.05, 0.2), (sx * 0.33, -HY - 0.05, 1.15), 0.012, up=(-sx, 0, 0))
    stack_light(ps, (HX, -HY, 0), 0.1 + H + 0.04, glows)
    # the fixture table and its part, the arm turned to it
    box(tb, (0.62, -0.1, 0.42), (0.28, 0.24, 0.025), 0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            seg(tb, (0.62 + sx * 0.24, -0.1 + sy * 0.2, 0.1), (0.62 + sx * 0.24, -0.1 + sy * 0.2, 0.4), 0.018)
    box(tb, (0.62, -0.1, 0.47), (0.12, 0.1, 0.03), 0.01, label=7)
    glows["glow_violet"].add(Cylinder((0.62, -0.1, 0.52), 0.035, 0.05, rr=0.01), k=0.0)
    robot_arm(out, (-0.45, 0.2, 0.1), math.atan2(-0.3, 1.07), reach=(1.05, -0.2))
    # the operator's pedestal outside the door
    pd = Field("Pedestal")
    box(pd, (-0.85, -HY - 0.45, 0.45), (0.08, 0.08, 0.45), 0.02)
    box(pd, (-0.85, -HY - 0.47, 0.95), (0.16, 0.1, 0.06), 0.02)
    screen(pd, glows["glow_screen"], (-0.85, -HY - 0.56, 0.98), (0, -1, 0), 0.2, 0.1, tilt=0.6, bezel=0.015, depth=0.015)
    ground_cut(pd, -0.02)
    ground_cut(ps, -0.02)
    out += [("Plinth", pl, fine(0.01, 0.02), "epoxy"), ("Glass", gs, fine(0.004, 0.008), "lab_glass"), ("Posts", ps, fine(0.005, 0.01), "graphite"),
            ("Table", tb, fine(0.005, 0.01), "chrome"), ("Pedestal", pd, fine(0.005, 0.01), "graphite")]
    return finish_glows(out, glows)


def accelerator(seed=0):
    """A particle accelerator's ring segment (front toward -Y): the beam pipe sweeping in a long arc through blue
    bending magnets and yellow focusing magnets on their stands, a glass window on the pipe where the beam glows
    violet, cable trays along it, and the arc running out through shielding walls of stacked concrete blocks with
    radiation signs at both ends."""
    out = []
    mg, pp, st, sh, tr, bm = Field("Magnets"), Field("Pipe"), Field("Stands"), Field("Shield"), Field("Trays"), Field("Beam")
    Rr, zp = 4.6, 0.55
    C = v3((0.0, Rr - 0.9, 0.0))                                    # the ring's centre lies behind: the arc bows toward -Y
    a0, a1 = -math.pi / 2 - 0.42, -math.pi / 2 + 0.42

    def on(a, dr=0.0, z=zp):
        return C + v3((math.cos(a) * (Rr + dr), math.sin(a) * (Rr + dr), z))

    def arc_tube(r, dr=0.0, z=zp, aa=a0, ab=a1):
        def fn(P):
            q = P - F32(C)
            rad = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
            ang = np.arctan2(q[:, 1], q[:, 0])
            d = np.sqrt((rad - F32(Rr + dr)) ** 2 + (P[:, 2] - F32(z)) ** 2) - F32(r)
            cap = np.maximum(F32(aa) - ang, ang - F32(ab)) * F32(Rr)
            return np.maximum(d, cap).astype(F32)
        lo = C + v3((-Rr - 1, -Rr - 1, z - r - 0.1))
        hi = C + v3((Rr + 1, -Rr * math.cos(0.5) + 1.0, z + r + 0.1))
        return Func(fn, lo, hi)
    pp.add(arc_tube(0.06), k=0.0)
    n = 9
    for i in range(n):
        a = a0 + 0.06 + (a1 - a0 - 0.12) * (i + 0.5) / n
        t = v3((-math.sin(a), math.cos(a), 0.0))
        rr = v3((math.cos(a), math.sin(a), 0.0))
        R = np.stack([t, rr, Z], axis=1)
        q = on(a)
        if i == n // 2:                                             # the window: a glass sleeve, the beam glowing in it
            pp.add(Cylinder(q, 0.1, 0.36, rr=0.02, R=rot_from_axes(z_axis=t)), k=0.0, label=7)
            pp.sub(Cylinder(q, 0.12, 0.24, R=rot_from_axes(z_axis=t)), k=0.0)
            bm.add(Cylinder(q, 0.075, 0.26, rr=0.02, R=rot_from_axes(z_axis=t)), k=0.0)
        elif i % 2 == 0:                                            # a bending magnet: a blue C-yoke round the pipe
            mg.add(RoundBox(q - Z * 0.02, (0.26, 0.2, 0.2), 0.03, R=R), k=0.0)
            mg.sub(RoundBox(q + rr * 0.12, (0.3, 0.13, 0.07), 0.02, R=R), k=0.0)
            mg.add(RoundBox(q + Z * 0.13, (0.28, 0.17, 0.05), 0.02, R=R), k=0.0, label=7)
            mg.add(RoundBox(q - Z * 0.17, (0.28, 0.17, 0.05), 0.02, R=R), k=0.0, label=7)
            stencil(mg, q - rr * 0.2, -rr, 0.2, 0.05, label=9, n=3)
        else:                                                       # a focusing magnet: a squat yellow quadrupole
            mg.add(Cylinder(q, 0.17, 0.2, rr=0.03, R=rot_from_axes(z_axis=t)), k=0.0, label=5)
            for k in range(4):
                ang = math.pi / 4 + k * math.pi / 2
                mg.add(RoundBox(q + (rr * math.cos(ang) + Z * math.sin(ang)) * 0.17, (0.06, 0.05, 0.05), 0.02,
                                R=np.stack([t, rr * math.cos(ang) + Z * math.sin(ang), np.cross(t, rr * math.cos(ang) + Z * math.sin(ang))], axis=1)),
                       k=0.01, label=8)
        for sg in (-1, 1):                                          # its stand
            b = q + rr * sg * 0.12
            seg(st, v3((b[0], b[1], 0.0)), v3((b[0], b[1], zp - 0.22)), 0.03)
            box(st, v3((b[0], b[1], 0.02)), (0.07, 0.07, 0.02), 0.006, R=R)
        box(st, q - Z * (zp - 0.32) * 0.0 - Z * 0.24, (0.12, 0.17, 0.02), 0.006, R=R)
    tr.add(arc_tube(0.012, dr=-0.55, z=0.18), k=0.0)
    tr.add(arc_tube(0.012, dr=-0.75, z=0.18), k=0.0)
    for k in range(10):
        a = a0 + 0.08 + (a1 - a0 - 0.16) * k / 9
        seg(tr, on(a, -0.55, 0.18), on(a, -0.75, 0.18), 0.01)
        seg(tr, on(a, -0.65, 0.0), on(a, -0.65, 0.18), 0.012)
    cbs = Field("Cables")
    for j in range(3):
        cbs.add(arc_tube(0.022, dr=-0.6 - j * 0.05, z=0.215), k=0.0, label=(0, 5, 9)[j])
    # the shielding walls at both ends: stacked concrete blocks, the pipe running through
    for a in (a0, a1):
        t = v3((-math.sin(a), math.cos(a), 0.0))
        rr = v3((math.cos(a), math.sin(a), 0.0))
        R = np.stack([t, rr, Z], axis=1)
        q = on(a, 0.0, 0.0)
        for row in range(3):
            for col in range(3):
                off = (col - 1) * 0.52 + (0.13 if row % 2 else 0.0)
                if abs(off) > 0.7:
                    continue
                c = q + rr * off + Z * (0.19 + row * 0.38)
                sh.add(RoundBox(c, (0.2, 0.25, 0.18), 0.02, R=R, **wob(8.0, 0.003, seed + row * 3 + col)), k=0.0)
        sh.sub(Cylinder(on(a), 0.08, 0.6, R=rot_from_axes(z_axis=t)), k=0.0)
        sg = q - t * 0.21 * (1 if a < -math.pi / 2 else -1) + Z * 0.82
        nrm = -t * (1 if a < -math.pi / 2 else -1)
        sh.paint(Cylinder(sg, 0.13, 0.06, R=rot_from_axes(z_axis=nrm)), 5)
        for k in range(3):
            ang = math.pi / 2 + k * 2 * math.pi / 3
            Rs = rot_from_axes(z_axis=nrm)
            sh.paint(Func(lambda P, sg=sg, Rs=Rs, ang=ang: (lambda Q: np.maximum.reduce([
                np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2) - F32(0.105), F32(0.03) - np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2),
                np.abs(np.arctan2(Q[:, 1], Q[:, 0]) - F32(ang - 2 * math.pi * (ang > math.pi))) * F32(0.06) - F32(0.03),
                np.abs(Q[:, 2]) - F32(0.06)]))(((P - F32(sg)) @ Rs.astype(F32))).astype(F32), sg - 0.2, sg + 0.2), 7)
        sh.paint(Sphere(sg, 0.02), 7)
    for f in (st, sh):
        ground_cut(f, -0.02)
    ground_cut(tr, -0.02)
    out += [("Magnets", mg, fine(0.006, 0.012), "magnet"), ("Pipe", pp, fine(0.004, 0.008), "chrome"), ("Stands", st, fine(0.005, 0.01), "galv"),
            ("Shield", sh, fine(0.01, 0.02), "concrete"), ("Trays", tr, fine(0.004, 0.008), "galv"), ("Cables", cbs, fine(0.004, 0.008), "cables"),
            ("Beam", bm, fine(0.004, 0.008), "glow_violet")]
    return out


def control_room(seed=0):
    """A glass-walled control room (front toward -Y) on a low plinth: glass on three sides in graphite mullions, the
    operators' screens glowing behind it, a big wall display, a white roof slab trimmed with a violet light strip, the
    corps' hex emblem lit on the fascia, air handlers and a vent on the roof, the door with its step and a card reader."""
    out = []
    pl, gs, fr, rf, ac = Field("Plinth"), Field("Glass"), Field("Mullions"), Field("Roof"), Field("Units")
    glows = G("glow_screen", "glow_violet", "glow_green")
    HX, HY, H = 1.35, 0.85, 1.15
    box(pl, (0, 0, 0.06), (HX + 0.12, HY + 0.12, 0.06), 0.02)
    box(pl, (0.5, -HY - 0.22, 0.04), (0.3, 0.12, 0.04), 0.015)
    ground_cut(pl, -0.02)
    z0 = 0.12
    box(fr, (0, HY - 0.04, z0 + H / 2), (HX, 0.04, H / 2), 0.02)               # the back wall
    gs.add(RoundBox((0, -HY, z0 + H / 2), (HX - 0.02, 0.008, H / 2 - 0.02), 0.004), k=0.0)
    for sx in (-1, 1):
        gs.add(RoundBox((sx * HX, -0.04, z0 + H / 2), (0.008, HY - 0.06, H / 2 - 0.02), 0.004), k=0.0)
    for x in np.linspace(-HX, HX, 7):
        box(fr, (x, -HY, z0 + H / 2), (0.025, 0.025, H / 2), 0.008)
    for y in np.linspace(-HY, HY - 0.1, 4)[1:]:
        for sx in (-1, 1):
            box(fr, (sx * HX, y, z0 + H / 2), (0.025, 0.025, H / 2), 0.008)
    for sx in (-1, 1):
        box(fr, (sx * HX, -HY, z0 + H / 2), (0.035, 0.035, H / 2), 0.01)
    box(fr, (0, -HY, z0 + 0.03), (HX, 0.03, 0.03), 0.008)
    for sx in (-1, 1):
        box(fr, (sx * HX, 0, z0 + 0.03), (0.03, HY, 0.03), 0.008)
    # the door (the glass cut away, a frame, a card reader)
    gs.sub(RoundBox((0.5, -HY, z0 + 0.45), (0.2, 0.05, 0.45), 0.004), k=0.0)
    box(fr, (0.5, -HY - 0.005, z0 + 0.45), (0.19, 0.012, 0.45), 0.006, label=7)
    fr.sub(RoundBox((0.5, -HY - 0.02, z0 + 0.5), (0.13, 0.02, 0.32), 0.006), k=0.0)
    glows["glow_screen"].add(RoundBox((0.5, -HY - 0.012, z0 + 0.5), (0.13, 0.004, 0.32), 0.004), k=0.0)
    box(fr, (0.78, -HY - 0.03, z0 + 0.55), (0.035, 0.012, 0.05), 0.006, label=7)
    glows["glow_green"].add(RoundBox((0.78, -HY - 0.045, z0 + 0.58), (0.02, 0.006, 0.012), 0.005), k=0.0)
    # the operators' screens glowing through the front and side glass, the big display on the back wall
    for x in (-1.0, -0.62, -0.24, 0.98):
        glows["glow_screen"].add(RoundBox((x, -HY - 0.01, z0 + 0.52), (0.14, 0.004, 0.08), 0.004), k=0.0)
    for sx in (-1, 1):
        for y in (-0.35, 0.15):
            glows["glow_screen"].add(RoundBox((sx * (HX + 0.01), y, z0 + 0.52), (0.004, 0.13, 0.08), 0.004), k=0.0)
    # the roof slab, its violet trim, the emblem, the air handlers
    box(rf, (0, 0, z0 + H + 0.06), (HX + 0.14, HY + 0.14, 0.06), 0.02)
    for sy in (-1, 1):
        strip(glows["glow_violet"], (-HX - 0.1, sy * (HY + 0.145), z0 + H + 0.05), (HX + 0.1, sy * (HY + 0.145), z0 + H + 0.05), 0.02, up=(0, sy, 0))
    for sx in (-1, 1):
        strip(glows["glow_violet"], (sx * (HX + 0.145), -HY - 0.1, z0 + H + 0.05), (sx * (HX + 0.145), HY + 0.1, z0 + H + 0.05), 0.02, up=(sx, 0, 0))
    em = v3((-0.3, -HY - 0.15, z0 + H + 0.32))
    rf.add(RoundBox(em + v3((0, 0.03, -0.12)), (0.04, 0.02, 0.12), 0.01), k=0.0, label=7)
    _hex_emblem(glows["glow_violet"], em, (0, -1, 0), 0.19)
    for (x, y) in ((0.6, 0.3), (1.0, 0.3)):
        box(ac, (x, y, z0 + H + 0.24), (0.17, 0.2, 0.12), 0.02)
        ac.sub(Cylinder((x, y, z0 + H + 0.37), 0.12, 0.04), k=0.0)
        ac.add(Cylinder((x, y, z0 + H + 0.34), 0.03, 0.02), k=0.0, label=7)
        for k in range(3):
            a = k * 2 * math.pi / 3
            ac.add(RoundBox((x + math.cos(a) * 0.06, y + math.sin(a) * 0.06, z0 + H + 0.34), (0.05, 0.018, 0.004), 0.003, R=Rz(a + 0.4)), k=0.0, label=7)
    ac.add(Cylinder((-0.9, 0.35, z0 + H + 0.2), 0.09, 0.16, rr=0.02), k=0.0)
    ac.add(Cylinder((-0.9, 0.35, z0 + H + 0.3), 0.13, 0.03, rr=0.01), k=0.0, label=7)
    ground_cut(fr, -0.02)
    out += [("Plinth", pl, fine(0.01, 0.02), "epoxy"), ("Glass", gs, fine(0.005, 0.01), "lab_glass"), ("Mullions", fr, fine(0.006, 0.012), "graphite"),
            ("Roof", rf, fine(0.01, 0.02), "white_tech"), ("Units", ac, fine(0.006, 0.012), "instrument")]
    return finish_glows(out, glows)


def _hex_emblem(f, c, nrm, R, t=0.014):
    """The tech corps' emblem as light tube (field f) on a face at c (normal nrm): a hexagon outline round an
    upward-pointing chevron and a dot."""
    nrm = unit(nrm)
    s = unit(np.cross(Z, nrm)) if abs(nrm[2]) < 0.9 else v3((1, 0, 0))
    u = np.cross(nrm, s)
    c = v3(c)
    pts = [c + (s * math.cos(math.pi / 2 + i * math.pi / 3) + u * math.sin(math.pi / 2 + i * math.pi / 3)) * R for i in range(7)]
    for a, b in zip(pts[:-1], pts[1:]):
        f.add(RoundCone(a, b, t, t), k=0.0)
    ch = [c - s * R * 0.45 - u * R * 0.2, c + u * R * 0.35, c + s * R * 0.45 - u * R * 0.2]
    for a, b in zip(ch[:-1], ch[1:]):
        f.add(RoundCone(a, b, t * 1.1, t * 1.1), k=0.0)
    f.add(Sphere(c - u * R * 0.42, t * 1.6), k=0.0)


def containment_pod(seed=0):
    """A containment pod: a tall capsule of glowing violet fluid caged in graphite ribs and rings, a white collar and
    cap with vents and pipes running up from it, standing on a hex plinth ringed with hazard stripes; a console beside
    it with its screen, cables snaking across to it."""
    out = []
    pl, rb, cp, fl, cn, cb = Field("Plinth"), Field("Ribs"), Field("Caps"), Field("Fluid"), Field("Console"), Field("Cables")
    glows = G("glow_screen", "glow_green")
    pl.add(hexagon((0, 0), 0.75, 0.12), k=0.0)
    pl.add(hexagon((0, 0), 0.62, 0.2), k=0.01, label=7)
    pl.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(0.68)) - F32(0.04)).astype(F32), (-1, -1, -0.1), (1, 1, 0.3)), 8)
    ground_cut(pl, -0.02)
    z0, z1, r = 0.42, 1.55, 0.36
    fl.add(Cylinder((0, 0, (z0 + z1) / 2), r, z1 - z0 + 0.1, rr=0.1), k=0.0)
    cp.add(Cylinder((0, 0, 0.3), 0.48, 0.24, rr=0.05), k=0.0)
    cp.add(Torus((0, 0, z0), r + 0.02, 0.04), k=0.01, label=7)
    cp.add(Cylinder((0, 0, z1 + 0.08), 0.45, 0.2, rr=0.06), k=0.0)
    cp.add(Ellipsoid((0, 0, z1 + 0.18), (0.4, 0.4, 0.14)), k=0.04)
    cp.add(Torus((0, 0, z1 - 0.02), r + 0.02, 0.04), k=0.01, label=7)
    for k in range(6):                                              # vents round the cap
        a = k * math.pi / 3
        cp.sub(RoundBox((math.cos(a) * 0.45, math.sin(a) * 0.45, z1 + 0.08), (0.03, 0.08, 0.05), 0.01, R=Rz(a)), k=0.005)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        seg(rb, (math.cos(a) * (r + 0.015), math.sin(a) * (r + 0.015), z0), (math.cos(a) * (r + 0.015), math.sin(a) * (r + 0.015), z1), 0.025)
    for z in np.linspace(z0 + 0.3, z1 - 0.3, 2):
        rb.add(Torus((0, 0, z), r + 0.02, 0.022), k=0.006)
    for (a, h) in ((0.4, 2.15), (2.5, 2.3)):                         # pipes up from the cap
        p = v3((math.cos(a) * 0.22, math.sin(a) * 0.22, z1 + 0.22))
        cb.add(Chain([p, p + Z * 0.25, v3((math.cos(a) * 0.5, math.sin(a) * 0.5, h)), v3((math.cos(a) * 0.9, math.sin(a) * 0.9, h + 0.05))],
                     [0.035] * 4, k=0.05), k=0.0, label=6)
    # the console
    o = v3((0.95, -0.55, 0.0))
    cn.add(convex([(o + v3((0, 0, 0.72)), (0, -0.6, 1)), (o + v3((0, 0, 0)), (0, 0, -1)), (o + v3((0.22, 0, 0)), (1, 0, 0)),
                   (o + v3((-0.22, 0, 0)), (-1, 0, 0)), (o + v3((0, 0.16, 0)), (0, 1, 0)), (o + v3((0, -0.16, 0)), (0, -1, 0))],
                  o + v3((-0.4, -0.4, -0.1)), o + v3((0.4, 0.4, 0.9))), k=0.0)
    screen(cn, glows["glow_screen"], o + v3((0, -0.03, 0.73)), (0, -1, 0), 0.3, 0.13, tilt=1.0, bezel=0.015, depth=0.012)
    for i in range(4):
        glows["glow_green"].add(RoundBox(o + v3((-0.15 + i * 0.1, -0.165, 0.52)), (0.025, 0.006, 0.012), 0.005), k=0.0)
    cb.add(Chain([o + v3((-0.18, 0.05, 0.03)), v3((0.65, -0.3, 0.03)), v3((0.42, -0.2, 0.03)), v3((0.38, -0.1, 0.25))], [0.025] * 4, k=0.05), k=0.0)
    ground_cut(cn, -0.02)
    ground_cut(cb, -0.01)
    out += [("Plinth", pl, fine(0.008, 0.016), "epoxy"), ("Ribs", rb, fine(0.005, 0.01), "graphite"), ("Caps", cp, fine(0.006, 0.012), "white_tech"),
            ("Fluid", fl, fine(0.008, 0.016), "glow_violet"), ("Console", cn, fine(0.005, 0.01), "graphite"), ("Cables", cb, fine(0.004, 0.008), "chrome")]
    return finish_glows(out, glows)


def gantry(seed=0):
    """A gantry crane (front toward -Y): two yellow A-frame legs on bogies running on floor rails, the box girder
    across them with hazard stripes at its ends, a trolley with its hoist, the hook block hanging on its cables with a
    graphite equipment crate slung under it."""
    out = []
    lg, rl, tr, cbl, cr = Field("Frame"), Field("Rails"), Field("Trolley"), Field("Cables"), Field("Crate")
    glows = G("glow_amber", "glow_violet")
    SX, H, RY0 = 1.5, 2.3, 0.75
    for sx in (-1, 1):
        x = sx * SX
        for sy in (-1, 1):
            seg(lg, (x, sy * RY0, 0.18), (x, sy * 0.12, H - 0.1), 0.06, 0.05)
        box(lg, (x, 0, 0.12), (0.1, RY0 + 0.15, 0.08), 0.02, label=7)
        for sy in (-1, 1):
            wheel(lg, lg, (x, sy * RY0, 0.07), (1, 0, 0), 0.07, 0.06)
        box(lg, (x, 0, 0.75), (0.04, 0.45, 0.035), 0.01)
        seg(rl, (x, -2.1, 0.02), (x, 2.1, 0.02), 0.03)
        box(rl, (x, 0, 0.005), (0.09, 2.1, 0.01), 0.004, label=7)
    box(lg, (0, 0, H), (SX + 0.15, 0.16, 0.14), 0.02)
    for sx in (-1, 1):
        lg.paint(RoundBox((sx * (SX + 0.05), 0, H), (0.15, 0.3, 0.2), 0.0), 8)
    xt = 0.25
    box(tr, (xt, 0, H + 0.2), (0.24, 0.24, 0.07), 0.02)
    tr.add(Cylinder((xt, 0, H - 0.17), 0.1, 0.36, rr=0.02, R=RY), k=0.0)
    box(tr, (xt, 0.0, H - 0.17), (0.18, 0.15, 0.13), 0.03, k=0.0, label=7)
    glows["glow_amber"].add(Cylinder((xt + 0.15, 0.15, H + 0.3), 0.03, 0.05, rr=0.01), k=0.0)
    zh = 1.1
    for sy in (-1, 1):
        seg(cbl, (xt, sy * 0.06, H - 0.28), (xt, sy * 0.06, zh + 0.12), 0.008)
    box(tr, (xt, 0, zh + 0.07), (0.07, 0.1, 0.07), 0.02, label=5)
    tr.add(Torus((xt, 0, zh - 0.03), 0.045, 0.014, R=RX), k=0.004, label=6)
    for (dx, dy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        seg(cbl, (xt, 0, zh - 0.06), (xt + dx * 0.32, dy * 0.24, zh - 0.36), 0.006)
    cz = zh - 0.36 - 0.18
    box(cr, (xt, 0, cz), (0.36, 0.28, 0.18), 0.03)
    cr.add(RoundBox((xt, 0, cz + 0.17), (0.37, 0.29, 0.02), 0.01), k=0.003, label=7)
    stencil(cr, (xt, -0.28, cz), (0, -1, 0), 0.32, 0.06, label=9, n=3)
    strip(glows["glow_violet"], (xt - 0.3, -0.285, cz - 0.1), (xt + 0.3, -0.285, cz - 0.1), 0.018, up=(0, -1, 0))
    ground_cut(lg, -0.02)
    ground_cut(rl, -0.01)
    out += [("Frame", lg, fine(0.008, 0.016), "crane_yellow"), ("Rails", rl, fine(0.005, 0.01), "steel"), ("Trolley", tr, fine(0.005, 0.01), "crane_yellow"),
            ("Cables", cbl, fine(0.003, 0.006), "steel"), ("Crate", cr, fine(0.006, 0.012), "graphite")]
    return finish_glows(out, glows)


# ------------------------------------------------------------------------------------------------ Cleanroom: no-build zones
def machine_arm(seed=0):
    """A robot cell without its glass: the arm on its plinth reaching over a short conveyor carrying sample cases, a
    ring of hazard stripes, yellow guard posts, a stack light."""
    out = []
    pl, cv, ps, cs = Field("Plinth"), Field("Conveyor"), Field("Posts"), Field("Cases")
    glows = G("glow_green", "glow_amber", "glow_red", "glow_violet")
    pl.add(Cylinder((0, 0, 0.05), 1.0, 0.1, rr=0.02), k=0.0)
    pl.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(0.88)) - F32(0.07)).astype(F32), (-1.2, -1.2, -0.1), (1.2, 1.2, 0.2)), 8)
    ground_cut(pl, -0.02)
    robot_arm(out, (-0.25, 0.1, 0.1), -0.25, reach=(1.0, -0.15), s=1.1)
    # the conveyor: a belt between rails on legs, rollers at its ends
    y0 = -0.45
    box(cv, (0.35, y0, 0.48), (0.75, 0.16, 0.03), 0.01, label=7)
    for sy in (-1, 1):
        box(cv, (0.35, y0 + sy * 0.18, 0.5), (0.77, 0.025, 0.045), 0.01)
        for x in (-0.3, 0.35, 1.0):
            seg(cv, (x, y0 + sy * 0.16, 0.0), (x, y0 + sy * 0.16, 0.46), 0.022)
    for x in (-0.42, 1.12):
        cv.add(Cylinder((x, y0, 0.48), 0.04, 0.34, R=RY), k=0.0, label=6)
    for i, x in enumerate((0.05, 0.5, 0.9)):
        box(cs, (x, y0, 0.56), (0.11, 0.09, 0.05), 0.015, label=(5 if i == 1 else 0))
        glows["glow_violet"].add(RoundBox((x, y0 - 0.091, 0.56), (0.06, 0.004, 0.012), 0.003), k=0.0)
    for k in range(5):                                              # yellow guard posts round the back
        a = math.pi * 0.15 + k * math.pi * 0.18
        p = v3((math.cos(a) * 0.98, math.sin(a) * 0.98, 0.0))
        ps.add(Cylinder(p + Z * 0.35, 0.035, 0.7, rr=0.01), k=0.0)
        ps.paint(Cylinder(p + Z * 0.45, 0.06, 0.08), 7)
    stack_light(ps, (-0.85, -0.45, 0), 0.0, glows)
    seg(ps, (-0.85, -0.45, 0.0), (-0.85, -0.45, 0.62), 0.02)
    for f in (cv, ps):
        ground_cut(f, -0.02)
    out += [("Plinth", pl, fine(0.008, 0.016), "epoxy"), ("Conveyor", cv, fine(0.005, 0.01), "graphite"), ("Posts", ps, fine(0.004, 0.008), "hazard_yellow"),
            ("Cases", cs, fine(0.005, 0.01), "white_tech")]
    return finish_glows(out, glows)


def centrifuge(seed=0):
    """An industrial centrifuge: a white cabinet with a domed lid, the rotor's glass window ringed with a violet light,
    a control panel with its screen and keys on the front, louvres and a chiller unit beside it with its fan, hoses
    between them, a stack light on top."""
    out = []
    cb, ld, ch = Field("Cabinet"), Field("Lid"), Field("Chiller")
    glows = G("glow_violet", "glow_screen", "glow_green", "glow_amber", "glow_red")
    box(cb, (0, 0, 0.42), (0.62, 0.55, 0.42), 0.06)
    box(cb, (0, 0, 0.04), (0.6, 0.53, 0.04), 0.01, label=7)
    for sx in (-1, 1):
        for k in range(5):
            cb.sub(RoundBox((sx * 0.62, 0.1, 0.25 + k * 0.08), (0.02, 0.3, 0.012), 0.006), k=0.0)
    cb.add(convex([((0, -0.55, 0.72), (0, -0.7, 1)), ((0, -0.55, 0.45), (0, -1, 0)), ((0.5, 0, 0), (1, 0, 0)), ((-0.5, 0, 0), (-1, 0, 0)),
                   ((0, -0.3, 0), (0, 1, 0)), ((0, 0, 0.42), (0, 0, -1))], (-0.6, -0.8, 0.3), (0.6, 0.0, 0.9)), k=0.01, label=7)
    screen(cb, glows["glow_screen"], (-0.15, -0.66, 0.66), (0, -1, 0), 0.26, 0.12, tilt=0.95, bezel=0.012, depth=0.01)
    for i in range(3):
        for j in range(2):
            cb.add(RoundBox((0.17 + i * 0.07, -0.66 + j * 0.05, 0.64 + j * 0.03), (0.025, 0.018, 0.01), 0.005, R=euler(0.95, 0, 0)), k=0.0, label=6)
    ld.add(Cylinder((0, 0.08, 0.86), 0.46, 0.06, rr=0.02), k=0.0)
    ld.add(Ellipsoid((0, 0.08, 0.89), (0.44, 0.44, 0.12)), k=0.03)
    ld.inter(Plane((0, 0, 0.83), (0, 0, -1)))
    ld.sub(Cylinder((0, 0.08, 1.0), 0.22, 0.12), k=0.01)
    wnd = Field("Window")
    wnd.add(Cylinder((0, 0.08, 0.96), 0.22, 0.03), k=0.0)
    glows["glow_violet"].add(Torus((0, 0.08, 0.98), 0.235, 0.016), k=0.0)
    seg(ld, (-0.38, -0.3, 0.92), (0.38, -0.3, 0.92), 0.02)
    stack_light(cb, (0.5, 0.45, 0), 0.84, glows)
    # the chiller beside it
    box(ch, (0.95, 0.15, 0.32), (0.25, 0.32, 0.32), 0.03)
    ch.sub(Cylinder((0.95, 0.15, 0.65), 0.2, 0.04), k=0.0)
    ch.add(Cylinder((0.95, 0.15, 0.62), 0.04, 0.02), k=0.0, label=7)
    for k in range(4):
        a = k * math.pi / 2 + 0.3
        ch.add(RoundBox((0.95 + math.cos(a) * 0.1, 0.15 + math.sin(a) * 0.1, 0.62), (0.08, 0.025, 0.004), 0.003, R=Rz(a + 0.5)), k=0.0, label=7)
    for k in range(6):
        ch.sub(RoundBox((0.95, -0.17, 0.12 + k * 0.07), (0.2, 0.02, 0.012), 0.005), k=0.0)
    hs = Field("Hoses")
    for dz in (0.2, 0.32):
        hs.add(Chain([v3((0.7, 0.3, dz)), v3((0.66, 0.42, dz - 0.05)), v3((0.6, 0.45, dz))], [0.025] * 3, k=0.02), k=0.0)
    for f in (cb, ch):
        ground_cut(f, -0.02)
    out += [("Cabinet", cb, fine(0.006, 0.012), "white_tech"), ("Lid", ld, fine(0.006, 0.012), "white_tech"), ("Window", wnd, fine(0.005, 0.01), "dark_glass"),
            ("Chiller", ch, fine(0.006, 0.012), "instrument"), ("Hoses", hs, fine(0.004, 0.008), "rubber")]
    return finish_glows(out, glows)


def scanner(seed=0):
    """A scanner: a great white ring housing with its bore lit violet, a narrow bed on its pedestal sliding into it,
    side panels with status lights, a control console and coolant lines."""
    out = []
    hs, bd, cn = Field("Housing"), Field("Bed"), Field("Console")
    glows = G("glow_violet", "glow_screen", "glow_green")
    zc, Ro, Ri, W = 0.85, 0.82, 0.38, 0.62
    hs.add(RoundBox((0, 0, zc - 0.05), (W / 2, 0.84, zc - 0.03), 0.12), k=0.0)
    hs.add(Cylinder((0, 0, zc), Ro, W, rr=0.12, R=RX), k=0.06)
    hs.sub(Cylinder((0, 0, zc), Ri, W + 0.4, rr=0.0, R=RX), k=0.06)
    hs.add(Torus((-W / 2 - 0.01, 0, zc), Ri + 0.04, 0.03, R=RX), k=0.01, label=7)
    hs.add(Torus((W / 2 + 0.01, 0, zc), Ri + 0.04, 0.03, R=RX), k=0.01, label=7)
    hs.paint(Func(lambda P: (np.abs(P[:, 0]) - F32(0.06)).astype(F32), (-0.2, -1, 0), (0.2, 1, 2)), 5)
    glows["glow_violet"].add(Torus((-W / 2 - 0.035, 0, zc), Ri + 0.04, 0.012, R=RX), k=0.0)
    glows["glow_violet"].add(Torus((W / 2 + 0.035, 0, zc), Ri + 0.04, 0.012, R=RX), k=0.0)
    for sy in (-1, 1):
        for k in range(3):
            glows["glow_green"].add(RoundBox((-W / 2 - 0.02, sy * 0.62, 0.35 + k * 0.06), (0.006, 0.03, 0.014), 0.005), k=0.0)
    # the bed on its pedestal, running out toward -X
    box(bd, (-0.95, 0, 0.3), (0.35, 0.16, 0.3), 0.05)
    box(bd, (-0.62, 0, 0.64), (0.75, 0.2, 0.035), 0.03, label=7)
    bd.add(Ellipsoid((-1.2, 0, 0.69), (0.12, 0.13, 0.04)), k=0.02, label=5)
    # the console and the coolant lines
    o = v3((-0.9, -0.95, 0.0))
    cn.add(RoundBox(o + v3((0, 0, 0.42)), (0.2, 0.12, 0.42), 0.03), k=0.0)
    screen(cn, glows["glow_screen"], o + v3((0, -0.02, 0.95)), (0.3, -1, 0), 0.3, 0.18, tilt=0.2, bezel=0.015, depth=0.02)
    cl = Field("Lines")
    for dy in (0.25, 0.4):
        cl.add(Chain([v3((0.2, dy, 1.4)), v3((0.5, dy, 1.6)), v3((0.9, dy + 0.1, 1.3)), v3((1.05, dy + 0.1, 0.03))], [0.03] * 4, k=0.06), k=0.0)
    for f in (hs, bd, cn, cl):
        ground_cut(f, -0.02)
    out += [("Housing", hs, fine(0.007, 0.014), "white_tech"), ("Bed", bd, fine(0.006, 0.012), "instrument"), ("Console", cn, fine(0.005, 0.01), "graphite"),
            ("Lines", cl, fine(0.005, 0.01), "chrome")]
    return finish_glows(out, glows)


def _frosted_pipe(f, pts, r, seed):
    """A pipe through pts (field f) furred with frost (a lumpy rime round it)."""
    f.add(Chain([v3(p) for p in pts], [r] * len(pts), k=0.03, **wob(30.0, r * 0.25, seed)), k=0.0)


def cryo_tanks(seed=0, variant=0):
    """Cryogenic tanks, frosted white (variant 0: two tall dewars on their skirts with a ladder up the bigger one, a
    manifold of frosted pipes and valves between them, a vent stack venting vapour; variant 1: a horizontal tank on
    saddles beside a bank of finned vaporiser columns furred with frost), hazard placards, pressure gauges."""
    out = []
    tk, pp, vl, lad = Field("Tanks"), Field("Pipes"), Field("Valves"), Field("Ladder")
    glows = G("glow_cyan", "glow_green")
    vents = []
    if variant == 0:
        for (x, y, r, h) in ((-0.3, 0.15, 0.42, 2.0), (0.48, -0.1, 0.32, 1.5)):
            tk.add(Cylinder((x, y, h / 2 + 0.12), r, h - 0.1, rr=0.08), k=0.0)
            tk.add(Ellipsoid((x, y, h + 0.04), (r, r, r * 0.45)), k=0.04)
            tk.add(Cylinder((x, y, 0.08), r * 0.92, 0.16, rr=0.02), k=0.01, label=7)
            for z in (0.5, h - 0.25):
                tk.add(Torus((x, y, z), r + 0.005, 0.02), k=0.005, label=6)
            tk.paint(RoundBox((x, y - r, h * 0.55), (0.1, 0.1, 0.1), 0.0, R=rot_from_axes(y_axis=(0, 1, 0)) @ euler(0, 0.785, 0)), 8)
            tk.paint(RoundBox((x, y - r, h * 0.55), (0.065, 0.12, 0.065), 0.0, R=euler(0, 0.785, 0)), 9)
            vl.add(Cylinder((x + r * 0.5, y - r * 0.8, h * 0.72), 0.05, 0.03, rr=0.008, R=rot_from_axes(z_axis=(0.5, -0.8, 0))), k=0.0, label=6)
            vl.paint(Sphere((x + r * 0.5 + 0.0125, y - r * 0.8 - 0.02, h * 0.72), 0.045), 9)
        for z in np.arange(0.25, 1.95, 0.14):                         # the ladder up the big one
            seg(lad, (-0.48, -0.31, z), (-0.12, -0.31, z), 0.01)
        for x in (-0.48, -0.12):
            seg(lad, (x, -0.3, 0.0), (x, -0.3, 2.15), 0.014)
        _frosted_pipe(pp, [(-0.05, 0.3, 1.6), (0.25, 0.3, 1.6), (0.48, 0.2, 1.5)], 0.045, seed)
        _frosted_pipe(pp, [(0.0, 0.5, 0.35), (0.6, 0.45, 0.35), (0.8, 0.2, 0.35), (0.8, -0.35, 0.35), (0.8, -0.35, 0.02)], 0.05, seed + 1)
        _frosted_pipe(pp, [(-0.3, 0.57, 0.6), (-0.3, 0.62, 0.3), (0.0, 0.62, 0.2), (0.0, 0.5, 0.2)], 0.04, seed + 2)
        for p in ((0.4, 0.45, 0.35), (0.8, -0.1, 0.35)):
            vl.add(Cylinder(v3(p), 0.06, 0.1, rr=0.02), k=0.0, label=7)
            vl.add(Torus(v3(p) + Z * 0.12, 0.06, 0.012), k=0.0, label=8)
            seg(vl, v3(p), v3(p) + Z * 0.12, 0.012, label=8)
        vt = v3((0.8, 0.45, 0.0))                                   # the vent stack
        seg(pp, vt, vt + Z * 1.9, 0.04)
        pp.add(Cylinder(vt + Z * 1.92, 0.06, 0.06, rr=0.015), k=0.01)
        vents.append(vt + Z * 1.98)
    else:
        L, r, zc = 0.95, 0.42, 0.62
        tk.add(Func(lambda P: (np.maximum(np.sqrt(P[:, 1] ** 2 + (P[:, 2] - F32(zc)) ** 2) - F32(r), np.abs(P[:, 0] + F32(0.25)) - F32(L))).astype(F32),
                    (-1.4, -0.6, 0.1), (0.9, 0.6, 1.2)), k=0.0)
        for sx in (-1, 1):
            tk.add(Ellipsoid((-0.25 + sx * L, 0, zc), (0.2, r, r)), k=0.04)
            box(tk, (-0.25 + sx * 0.6, 0, 0.17), (0.1, 0.32, 0.17), 0.02, label=7)
        for x in (-0.85, -0.25, 0.35):
            tk.add(Torus((x, 0, zc), r + 0.004, 0.02, R=RX), k=0.004, label=6)
        tk.paint(RoundBox((-0.25, -r, zc), (0.12, 0.12, 0.12), 0.0, R=euler(0, 0.785, 0)), 8)
        tk.paint(RoundBox((-0.25, -r, zc), (0.08, 0.14, 0.08), 0.0, R=euler(0, 0.785, 0)), 9)
        stencil(tk, (-0.85, -r, zc + 0.1), (0, -1, 0), 0.35, 0.06, label=9, n=4)
        # the vaporiser bank: finned columns frosted toward the bottom
        for i in range(3):
            for j in range(2):
                c = v3((0.95 + i * 0.22, -0.2 + j * 0.3, 0.0))
                tk.add(Cylinder(c + Z * 0.8, 0.04, 1.5, rr=0.01), k=0.0, label=6)
                for k in range(4):
                    a = k * math.pi / 4
                    tk.add(RoundBox(c + Z * 0.8, (0.09, 0.008, 0.74), 0.004, R=Rz(a)), k=0.0, label=6)
                pp.add(Cylinder(c + Z * 0.38, 0.1, 0.72, rr=0.04, **wob(18.0, 0.02, seed + i * 2 + j)), k=0.0)
        seg(tk, (0.95, -0.2, 1.6), (1.39, -0.2, 1.6), 0.03, label=6)
        seg(tk, (0.95, 0.1, 1.6), (1.39, 0.1, 1.6), 0.03, label=6)
        _frosted_pipe(pp, [(0.66, 0.0, zc), (0.85, 0.0, zc), (0.95, -0.2, 0.15)], 0.045, seed)
        vl.add(Cylinder((0.75, 0.0, zc + 0.12), 0.055, 0.12, rr=0.02), k=0.0, label=7)
        vl.add(Torus((0.75, 0.0, zc + 0.24), 0.06, 0.012), k=0.0, label=8)
        vt = v3((-1.05, 0.25, 0.0))
        seg(pp, vt + Z * 0.95, vt + Z * 1.7, 0.035)
        pp.add(Cylinder(vt + Z * 1.72, 0.055, 0.05, rr=0.012), k=0.01)
        _frosted_pipe(pp, [(-0.8, 0.25, 0.95), (-1.05, 0.25, 0.95)], 0.035, seed + 5)
        vents.append(vt + Z * 1.78)
        vents.append(v3((1.17, -0.05, 0.25)))                       # (the vaporisers' foot fogs too)
    for f in (tk, lad):
        ground_cut(f, -0.02)
    ground_cut(pp, -0.02)
    out += [("Tanks", tk, fine(0.007, 0.014), "cryo"), ("Pipes", pp, fine(0.005, 0.01), "frost"), ("Valves", vl, fine(0.004, 0.008), "valves")]
    if any(op[0] == "add" for op in lad.ops):
        out.append(("Ladder", lad, fine(0.004, 0.008), "galv"))
    return finish_glows(out, glows)


# vapour points (Blender, prop-local: x, y, z) of the cryo tanks' vents; game.gd wants (x, z, -y)
CRYO_VENTS = {"Tank_A": [(0.8, 0.45, 1.98)], "Tank_B": [(-1.05, 0.25, 1.78), (1.17, -0.05, 0.25)]}


# ------------------------------------------------------------------------------------------------ Dish Array: scatter
def small_dish(seed=0, tripod=False):
    """A small station dish: an offset-fed white reflector tilted up toward -Y, its feed arm and the graphite feed horn,
    on a steel pole in a ballast frame weighed down with concrete blocks (tripod: on three splayed legs pegged into the
    sand, a cable run off from it)."""
    out = []
    ds, mt, fd, bl = Field("Dish"), Field("Mount"), Field("Feed"), Field("Ballast")
    ax = unit(v3((0, -0.6, 0.8)))
    vert = v3((0, 0.05, 0.95))
    ds.add(dish_fn(vert, ax, 0.42, 0.32, 0.012), k=0.0)
    ds.add(dish_rim(vert, ax, 0.42, 0.32, 0.016), k=0.004, label=7)
    seg(mt, vert - ax * 0.02, vert - ax * 0.14, 0.04)
    if tripod:
        for k in range(3):
            a = math.pi / 2 + k * 2 * math.pi / 3
            seg(mt, vert - ax * 0.14, v3((math.cos(a) * 0.5, 0.05 + math.sin(a) * 0.5, 0.0)), 0.02)
            bl.add(Cylinder((math.cos(a) * 0.5, 0.05 + math.sin(a) * 0.5, 0.02), 0.04, 0.04, rr=0.01), k=0.0)
        cb = Field("Cable")
        cb.add(Chain([vert - ax * 0.14, v3((0.05, 0.2, 0.5)), v3((0.1, 0.35, 0.02)), v3((0.4, 0.6, 0.02)), v3((0.7, 0.55, 0.02))], [0.012] * 5, k=0.03), k=0.0)
        ground_cut(cb, -0.005)
        out.append(("Cable", cb, fine(0.004, 0.008), "rubber"))
    else:
        seg(mt, vert - ax * 0.14, (0, 0.1, 0.05), 0.035)
        for sx in (-1, 1):
            seg(mt, (sx * 0.38, -0.3, 0.05), (sx * 0.38, 0.4, 0.05), 0.022)
            seg(mt, (sx * 0.38, 0.1, 0.05), (0, 0.1, 0.5), 0.016)
        for sy in (-0.3, 0.4):
            seg(mt, (-0.38, sy, 0.05), (0.38, sy, 0.05), 0.022)
        for (x, y) in ((-0.22, -0.18), (0.22, -0.18), (-0.22, 0.28), (0.22, 0.28)):
            bl.add(RoundBox((x, y, 0.1), (0.13, 0.09, 0.07), 0.015, **wob(10.0, 0.003, seed + int(x * 10 + y * 7))), k=0.0)
    F = vert + ax * 0.32
    rim_lo = dish_point(vert, ax, 0.42, 0.32, -math.pi / 2, 1.0)
    seg(fd, rim_lo, F + ax * 0.02, 0.013)
    fd.add(RoundCone(F - ax * 0.06, F + ax * 0.06, 0.035, 0.05), k=0.006)
    fd.add(RoundBox(F + ax * 0.09, (0.04, 0.04, 0.035), 0.012, R=rot_from_axes(z_axis=ax)), k=0.006)
    for f in (mt, bl):
        ground_cut(f, -0.02)
    out += [("Dish", ds, fine(0.005, 0.01), "radome"), ("Mount", mt, fine(0.004, 0.008), "galv"), ("Feed", fd, fine(0.004, 0.008), "graphite"),
            ("Ballast", bl, fine(0.005, 0.01), "concrete")]
    return out


def antenna_mast(seed=0, H=3.0):
    """An antenna mast: a galvanised lattice on its concrete pad, guyed three ways to anchors in the sand, panel antennas
    and a microwave drum on it, a whip at the top and red aircraft warning lights at the top and half way up."""
    out = []
    ms, pd, gy, an, rl = Field("Mast"), Field("Pad"), Field("Guys"), Field("Antennas"), Field("Lights")
    pd.add(RoundBox((0, 0, 0.04), (0.3, 0.3, 0.06), 0.02, **wob(6.0, 0.004, seed)), k=0.0)
    lattice_mast(ms, (0, 0, 0), 0.05, H, 0.17, 0.12, legs=3, step=0.26, rod=0.011)
    seg(ms, (0, 0, H), (0, 0, H + 0.6), 0.012, 0.004)
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        g0 = v3((math.cos(a) * 1.3, math.sin(a) * 1.3, 0.04))
        for z in (H * 0.5, H * 0.92):
            seg(gy, g0, v3((math.cos(a) * 0.13, math.sin(a) * 0.13, z)), 0.004)
        pd.add(RoundBox(g0 - Z * 0.01, (0.07, 0.07, 0.04), 0.01), k=0.0)
    for k, a in enumerate((0.3, 2.4, 4.5)):                        # panel antennas round the top
        d = v3((math.cos(a), math.sin(a), 0))
        q = d * 0.24 + Z * (H - 0.35)
        an.add(RoundBox(q, (0.06, 0.035, 0.28), 0.015, R=np.stack([unit(np.cross(Z, d)), d, Z], axis=1)), k=0.0)
        seg(an, d * 0.13 + Z * (H - 0.35), d * 0.2 + Z * (H - 0.35), 0.01)
    d = v3((0.0, -1.0, 0.0))                                        # the microwave drum
    an.add(Cylinder(d * 0.28 + Z * (H * 0.62), 0.16, 0.12, rr=0.03, R=rot_from_axes(z_axis=d)), k=0.0, label=7)
    seg(an, d * 0.12 + Z * (H * 0.62), d * 0.22 + Z * (H * 0.62), 0.015)
    for z in (H + 0.02, H * 0.5):
        rl.add(Sphere((0.1, 0, z + 0.04), 0.035), k=0.0)
        seg(ms, (0.06, 0, z), (0.1, 0, z + 0.02), 0.008)
    rl.add(Sphere((0, 0, H + 0.62), 0.03), k=0.0)
    ground_cut(pd, -0.02)
    out += [("Mast", ms, fine(0.004, 0.008), "galv"), ("Pad", pd, fine(0.008, 0.016), "concrete"), ("Guys", gy, fine(0.003, 0.006), "steel"),
            ("Antennas", an, fine(0.004, 0.008), "radome"), ("Lights", rl, fine(0.004, 0.008), "glow_red")]
    return out


def _panel(f, fr, c, yaw, tilt, W=0.46, Hh=0.3):
    """A solar panel (cells in field f, its frame in fr) at c, facing -Y turned by yaw, tilted up by `tilt`."""
    R = Rz(yaw) @ euler(tilt, 0, 0)                                  # (its back edge, +Y, raised)
    c = v3(c)
    f.add(RoundBox(c, (W, Hh, 0.012), 0.004, R=R), k=0.0)
    fr.add(RoundBox(c - R @ v3((0, 0, 0.012)), (W + 0.012, Hh + 0.012, 0.012), 0.004, R=R), k=0.0)
    fr.sub(RoundBox(c + R @ v3((0, 0, 0.004)), (W - 0.004, Hh - 0.004, 0.014), 0.002, R=R), k=0.0)


def solar_panel(seed=0):
    """Two solar panels on a tilted steel frame on concrete footings, a small combiner box under them."""
    out = []
    sl, fr, st = Field("Cells"), Field("Frames"), Field("Stand")
    tilt = 0.55
    for x in (-0.48, 0.48):
        _panel(sl, fr, (x, 0, 0.62), 0.0, tilt)
        for (y, h) in ((-0.18, 0.46), (0.2, 0.69)):
            seg(st, (x * 1.2, y, 0.0), (x * 1.2, y, h), 0.02)
            st.add(Cylinder((x * 1.2, y, 0.02), 0.05, 0.06, rr=0.01), k=0.0, label=7)
    for (y, h) in ((-0.18, 0.46), (0.2, 0.69)):
        seg(st, (-0.6, y, h), (0.6, y, h), 0.018)
    box(st, (0.0, 0.25, 0.32), (0.1, 0.05, 0.12), 0.015, label=5)
    seg(st, (0.0, 0.25, 0.2), (0.0, 0.28, 0.0), 0.015)
    ground_cut(st, -0.02)
    out += [("Cells", sl, fine(0.004, 0.008), "solar"), ("Frames", fr, fine(0.004, 0.008), "galv"), ("Stand", st, fine(0.004, 0.008), "station")]
    return out


def cable_drum(seed=0):
    """Cable drums: a big wooden drum of black cable on its flanges, a smaller empty one lying beside it."""
    out = cable_reel(seed, Rf=0.42, R0=0.2, W=0.22, reel="timber", cable="rubber", end=False)
    d2 = Field("Drum2")
    c = v3((0.75, 0.25, 0.0))
    for z in (0.025, 0.25):
        d2.add(Cylinder(c + Z * z, 0.3, 0.04, rr=0.008), k=0.0)
    d2.add(Cylinder(c + Z * 0.14, 0.14, 0.2), k=0.0)
    d2.sub(Cylinder(c + Z * 0.27, 0.04, 0.1), k=0.0)
    ground_cut(d2, -0.01)
    out.append(("Drum2", d2, fine(0.005, 0.01), "timber"))
    return out


def junction_box(seed=0):
    """A junction box: a grey steel cabinet on its concrete plinth, door seams, a hazard label and a green status
    light, conduits down into the sand, a stubby antenna on top."""
    out = []
    cb, pl, cd, gl = Field("Cabinet"), Field("Plinth"), Field("Conduits"), Field("Led")
    pl.add(RoundBox((0, 0, 0.05), (0.32, 0.2, 0.07), 0.02, **wob(7.0, 0.004, seed)), k=0.0)
    box(cb, (0, 0, 0.45), (0.26, 0.14, 0.33), 0.02)
    box(cb, (0, 0, 0.8), (0.29, 0.17, 0.025), 0.01, k=0.004)
    cb.sub(RoundBox((0, -0.14, 0.45), (0.003, 0.02, 0.3), 0.0), k=0.0)
    for sx in (-1, 1):
        box(cb, (sx * 0.05, -0.145, 0.5), (0.008, 0.01, 0.04), 0.004, k=0.002, label=6)
    cb.paint(RoundBox((-0.13, -0.14, 0.6), (0.05, 0.03, 0.05), 0.0, R=euler(0, 0.785, 0)), 8)
    stencil(cb, (0.13, -0.142, 0.62), (0, -1, 0), 0.14, 0.03, label=7, n=3)
    gl.add(RoundBox((0.13, -0.145, 0.7), (0.02, 0.006, 0.012), 0.005), k=0.0)
    seg(cb, (0.2, 0.05, 0.82), (0.2, 0.05, 1.2), 0.01, 0.005, label=7)
    for x in (-0.15, 0.0, 0.15):
        cd.add(Chain([v3((x, 0.15, 0.3)), v3((x, 0.22, 0.12)), v3((x, 0.26, -0.03))], [0.025] * 3, k=0.03), k=0.0)
    for f in (cb, pl, cd):
        ground_cut(f, -0.02)
    out += [("Cabinet", cb, fine(0.004, 0.008), "station"), ("Plinth", pl, fine(0.005, 0.01), "concrete"), ("Conduits", cd, fine(0.004, 0.008), "graphite"),
            ("Led", gl, fine(0.003, 0.006), "glow_green")]
    return out


def desert_scrub(seed=0, w=0.8):
    return scrub(w, w * 0.45, seed, mat="scrub")


# ------------------------------------------------------------------------------------------------ Dish Array: landmarks
def radio_telescope(seed=0):
    """A great radio telescope (front toward -Y): the white dish tilted up toward the sky in front, its backing truss of
    rings and ribs, the hub and its counterweight boom, the feed cabin held at the focus on four legs with a red warning
    light; the elevation axle in a yoke on the turret, the concrete pedestal with its door and ladder, on its apron."""
    out = []
    ds, bk, yk, pd, fd, lt = Field("Dish"), Field("Truss"), Field("Yoke"), Field("Pedestal"), Field("Feed"), Field("Warn")
    A = v3((0, 0.25, 2.05))
    el = math.radians(48)
    ax = unit(v3((0, -math.cos(el), math.sin(el))))
    Rd, Fc = 1.7, 0.85
    vert = A + ax * 0.35
    ds.add(dish_fn(vert, ax, Rd, Fc, 0.02), k=0.0)
    ds.add(dish_rim(vert, ax, Rd, Fc, 0.035), k=0.006, label=7)
    for t in (0.45, 0.8):                                            # the backing rings and the radial ribs
        Rr = Rd * t
        zr = Rr * Rr / (4 * Fc)
        bk.add(Torus(vert + ax * (zr - 0.12), Rr, 0.03, R=rot_from_axes(z_axis=ax)), k=0.0)
    for k in range(12):
        a = k * math.pi / 6
        p = dish_point(vert, ax, Rd, Fc, a, 0.98) - ax * 0.04
        q = dish_point(vert, ax, Rd, Fc, a, 0.2) - ax * 0.26
        seg(bk, p, q, 0.025)
    bk.add(Cylinder(vert - ax * 0.12, 0.34, 0.24, rr=0.04, R=rot_from_axes(z_axis=ax)), k=0.0, label=7)
    seg(bk, vert - ax * 0.12, A - ax * 0.85, 0.07)                   # the counterweight boom
    cw = A - ax * 0.95
    bk.add(RoundBox(cw, (0.32, 0.2, 0.2), 0.03, R=rot_from_axes(z_axis=ax, y_axis=(1, 0, 0))), k=0.01, label=7)
    # the feed on its quadrupod
    Fp = vert + ax * Fc
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        seg(fd, dish_point(vert, ax, Rd, Fc, a, 0.93) + ax * 0.02, Fp - ax * 0.05, 0.022)
    fd.add(Cylinder(Fp, 0.17, 0.4, rr=0.04, R=rot_from_axes(z_axis=ax)), k=0.01)
    fd.add(RoundCone(Fp - ax * 0.2, Fp - ax * 0.32, 0.12, 0.06), k=0.01, label=7)
    lt.add(Sphere(Fp + ax * 0.22 + Z * 0.02, 0.05), k=0.0)
    # the yoke, the axle, the turret
    yk.add(Cylinder(A, 0.09, 1.5, rr=0.02, R=RX), k=0.0, label=7)
    for sx in (-1, 1):
        yk.add(convex([((sx * 0.65, 0, 0), (sx, 0, 0)), ((sx * 0.5, 0, 0), (-sx, 0, 0)), ((0, 0.25 - 0.22, 0), (0, -1, 0)),
                       ((0, 0.25 + 0.22, 0), (0, 1, 0)), ((0, 0.25, 1.35), (0, 0, -1)), ((0, 0.25, A[2] + 0.18), (0, 0, 1)),
                       ((0, 0.25 - 0.1, A[2] + 0.18), (0, -1, 1.2)), ((0, 0.25 + 0.1, A[2] + 0.18), (0, 1, 1.2))],
                      (sx * 0.65 - 0.2 if sx > 0 else -0.85, -0.3, 1.2), (0.85 if sx > 0 else -0.3, 0.8, A[2] + 0.4)), k=0.0)
    box(yk, (0, 0.25, 1.28), (0.75, 0.5, 0.1), 0.03)
    box(yk, (0, 0.25, 1.16), (0.68, 0.44, 0.035), 0.01, label=7)
    # the pedestal and its apron
    pd.add(Cylinder((0, 0.25, 0.6), 0.55, 1.1, rr=0.03), k=0.0)
    pd.add(Cylinder((0, 0.25, 0.04), 1.25, 0.08, rr=0.02), k=0.0)
    pd.sub(RoundBox((0, -0.28, 0.32), (0.15, 0.08, 0.3), 0.01), k=0.0)
    dk = Field("Door")
    box(dk, (0, -0.23, 0.32), (0.15, 0.01, 0.3), 0.0)
    for sx in (-1, 1):
        seg(yk, (0.42 + sx * 0.08, -0.15, 0.08), (0.42 + sx * 0.08, -0.15, 1.15), 0.01)
    for z in np.arange(0.2, 1.1, 0.12):
        seg(yk, (0.34, -0.15, z), (0.5, -0.15, z), 0.008)
    pd.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + (P[:, 1] - F32(0.25)) ** 2) - F32(1.12)) - F32(0.05)).astype(F32), (-1.4, -1.2, -0.1), (1.4, 1.6, 0.2)), 5)
    for f in (pd, yk):
        ground_cut(f, -0.02)
    out += [("Dish", ds, fine(0.012, 0.024), "radome"), ("Truss", bk, fine(0.006, 0.012), "galv"), ("Yoke", yk, fine(0.008, 0.016), "station"),
            ("Pedestal", pd, fine(0.01, 0.02), "concrete"), ("Feed", fd, fine(0.005, 0.01), "radome"), ("Warn", lt, fine(0.004, 0.008), "glow_red"),
            ("Door", dk, fine(0.006, 0.012), "dark")]
    return out


def control_building(seed=0):
    """The station's control building (front toward -Y): a long low block of painted concrete with a navy band, a row
    of lit windows (warm offices, the cool glow of the operations room), the door under its canopy and lamp, a sign
    board; on the flat roof behind the parapet air handlers, two small dishes, a lattice mast with a red light and a
    whip antenna."""
    out = []
    bd, gl, gw, gc, fr, rf = Field("Walls"), Field("Glass"), Field("Lit"), Field("LitCool"), Field("Frames"), Field("RoofKit")
    glows = G("glow_lamp", "glow_red", "glow_violet")
    W, D, H = 1.45, 0.75, 0.95
    bd.add(walls_box(0, 0, W, D, -0.05, H, batter=0.0, amp=0.003, seed=seed), k=0.0)
    box(bd, (0, 0, H + 0.06), (W + 0.04, D + 0.04, 0.07), 0.01, k=0.003)
    bd.sub(RoundBox((0, 0, H + 0.18), (W - 0.04, D - 0.04, 0.12), 0.01), k=0.0)
    bd.paint(Func(lambda P: (np.abs(P[:, 2] - F32(0.82)) - F32(0.04)).astype(F32), (-2, -1, 0), (2, 1, 1.2)), 5)
    for i, x in enumerate((-1.15, -0.75, -0.35, 0.05, 0.95, 1.25)):
        q = v3((x, -D, 0.5))
        bd.sub(RoundBox(q, (0.15, 0.05, 0.16), 0.008), k=0.0)
        (gc if i in (1, 2, 3) else (gw if i != 4 else gl)).add(RoundBox(q + v3((0, 0.035, 0)), (0.15, 0.008, 0.16), 0.0), k=0.0)
        box(fr, q + v3((0, 0.015, 0)), (0.012, 0.012, 0.16), 0.004)
        box(bd, q + v3((0, -0.03, -0.18)), (0.18, 0.035, 0.018), 0.006, k=0.003, label=7)
    for (sx, x) in ((1, W), (-1, -W)):                              # windows round the ends
        q = v3((x, 0.0, 0.5))
        bd.sub(RoundBox(q, (0.05, 0.2, 0.16), 0.008), k=0.0)
        gw.add(RoundBox(q - v3((sx * 0.035, 0, 0)), (0.008, 0.2, 0.16), 0.0), k=0.0)
    # the door, its canopy, lamp and sign
    q = v3((0.5, -D, 0.36))
    bd.sub(RoundBox(q, (0.16, 0.05, 0.36), 0.008), k=0.0)
    box(fr, q + v3((0, 0.03, 0)), (0.16, 0.01, 0.36), 0.0, label=7)
    gl.add(RoundBox(q + v3((0, 0.02, 0.12)), (0.1, 0.008, 0.14), 0.0), k=0.0)
    box(bd, (0.5, -D - 0.22, 0.78), (0.3, 0.22, 0.025), 0.008, k=0.0, label=7)
    for sx in (-1, 1):
        seg(fr, (0.5 + sx * 0.27, -D - 0.4, 0.0), (0.5 + sx * 0.27, -D - 0.4, 0.77), 0.014)
    glows["glow_lamp"].add(RoundBox((0.5, -D - 0.22, 0.75), (0.12, 0.08, 0.008), 0.004), k=0.0)
    box(bd, (-0.35, -D - 0.02, 0.95), (0.5, 0.02, 0.07), 0.008, k=0.0, label=7)
    glyphs(glows["glow_violet"], (-0.35, -D - 0.045, 0.95), (1, 0, 0), 5, 0.08, seed, r=0.006)
    box(bd, (0.5, -D - 0.12, 0.02), (0.3, 0.18, 0.03), 0.01, label=0)
    # the roof
    for (x, y) in ((-0.9, 0.3), (-0.5, 0.3)):
        box(rf, (x, y, H + 0.18), (0.16, 0.2, 0.12), 0.02, label=0)
        rf.sub(Cylinder((x, y, H + 0.31), 0.11, 0.04), k=0.0)
        rf.add(Cylinder((x, y, H + 0.28), 0.03, 0.02), k=0.0, label=7)
    place_parts(out, [(n, Scaled_field(f, 0.6), v * 0.8, m) for (n, f, v, m) in small_dish(seed + 1, tripod=True)], (0.35, 0.2, H + 0.06), Rz(0.3), rename={"Dish": "RoofDish", "Mount": "RoofMount", "Feed": "RoofFeed",
                                                                                            "Ballast": "RoofBallast", "Cable": "RoofCable"})
    place_parts(out, [(n, Scaled_field(f, 0.5), v * 0.7, m) for (n, f, v, m) in small_dish(seed + 2)], (-0.05, -0.3, H + 0.06), Rz(-0.4),
                rename={"Dish": "RoofDish", "Mount": "RoofMount", "Feed": "RoofFeed", "Ballast": "RoofBallast"})
    mt = Field("Mast")
    lattice_mast(mt, (1.15, 0.45, 0), H + 0.06, H + 1.7, 0.09, 0.05, legs=3, step=0.2, rod=0.008)
    glows["glow_red"].add(Sphere((1.15, 0.45, H + 1.74), 0.035), k=0.0)
    seg(mt, (0.9, 0.5, H + 0.06), (0.9, 0.5, H + 1.1), 0.01, 0.004)
    ground_cut(bd, -0.02)
    ground_cut(fr, -0.02)
    out += [("Walls", bd, fine(0.008, 0.016), "station"), ("Glass", gl, fine(0.006, 0.012), "glass"), ("Lit", gw, fine(0.006, 0.012), "glow_window"),
            ("LitCool", gc, fine(0.006, 0.012), "glow_window_cool"), ("Frames", fr, fine(0.004, 0.008), "graphite"), ("RoofKit", rf, fine(0.006, 0.012), "station"),
            ("Mast", mt, fine(0.004, 0.008), "galv")]
    return finish_glows(out, glows)


def Scaled_field(f, s):
    """A copy of field f scaled by s about the origin."""
    g = Field(f.name)
    for kind, prim, kk, lab in f.ops:
        g.ops.append((kind, Scaled(prim, s), kk * s, lab))
    return g


def radar_tower(seed=0):
    """A radar tower: a four-legged galvanised lattice with a platform and rail at the top, the long curved reflector of
    a surveillance radar on its turning pedestal, a red beacon on a mast, an equipment shelter at its foot."""
    out = []
    tw, pf, rd, sh = Field("Tower"), Field("Platform"), Field("Radar"), Field("Shelter")
    glows = G("glow_red", "glow_green")
    H = 2.9
    lattice_mast(tw, (0, 0, 0), 0.0, H, 0.55, 0.32, legs=4, step=0.36, rod=0.016)
    for k in range(4):
        a = math.pi / 2 + k * math.pi / 2
        tw.add(RoundBox((math.cos(a) * 0.55, math.sin(a) * 0.55, 0.06), (0.1, 0.1, 0.08), 0.02), k=0.0, label=7)
    box(pf, (0, 0, H + 0.02), (0.5, 0.5, 0.03), 0.01)
    railing_line(pf, [(-0.5, -0.5, H), (0.5, -0.5, H), (0.5, 0.5, H), (-0.5, 0.5, H), (-0.5, -0.5, H)], h=0.3, step=0.25, r=0.009)
    pf.add(Cylinder((0, 0, H + 0.14), 0.16, 0.22, rr=0.03), k=0.0, label=7)
    # the reflector: a wide, shallow curved sheet tilted up, its feed horn on a boom
    rc = v3((0, -0.12, H + 0.55))
    yaw = 0.35
    Rr = Rz(yaw)
    Rf = Rr.astype(F32)

    def refl(P):
        Q = (P - F32(rc)) @ Rf
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        surf = y - (x * x * F32(0.18) + z * z * F32(0.9)) + F32(0.02) * z
        return np.maximum.reduce([np.abs(surf) - F32(0.018), np.abs(x) - F32(0.95), np.abs(z) - F32(0.2)]).astype(F32)
    rd.add(Func(refl, rc - 1.2, rc + 1.2), k=0.0)
    seg(rd, rc + Rr @ v3((0, 0.08, -0.2)), v3((0, 0, H + 0.24)), 0.04)
    seg(rd, rc + Rr @ v3((0, 0.04, -0.15)), rc + Rr @ v3((0, -0.45, -0.18)), 0.02)
    rd.add(RoundBox(rc + Rr @ v3((0, -0.5, -0.18)), (0.25, 0.05, 0.04), 0.015, R=Rr), k=0.01, label=7)
    seg(rd, (0.3, 0.3, H + 0.05), (0.3, 0.3, H + 0.85), 0.012, 0.006, label=7)
    glows["glow_red"].add(Sphere((0.3, 0.3, H + 0.88), 0.04), k=0.0)
    # the shelter at the foot
    box(sh, (0.85, 0.55, 0.32), (0.32, 0.26, 0.32), 0.02)
    box(sh, (0.85, 0.55, 0.66), (0.36, 0.3, 0.025), 0.01, k=0.004, label=7)
    sh.sub(RoundBox((0.85, 0.29, 0.28), (0.09, 0.02, 0.24), 0.006), k=0.0)
    box(sh, (1.18, 0.55, 0.32), (0.05, 0.13, 0.1), 0.01, k=0.004, label=6)
    glows["glow_green"].add(RoundBox((0.62, 0.285, 0.5), (0.02, 0.006, 0.012), 0.005), k=0.0)
    for f in (tw, sh):
        ground_cut(f, -0.02)
    out += [("Tower", tw, fine(0.005, 0.01), "galv"), ("Platform", pf, fine(0.004, 0.008), "galv"), ("Radar", rd, fine(0.005, 0.01), "radome"),
            ("Shelter", sh, fine(0.006, 0.012), "station")]
    return finish_glows(out, glows)


def fuel_tank(seed=0):
    """A fuel tank: a long white cylinder with a red band and stencils on concrete saddles inside a low bund wall, a
    ladder up its end to a railed catwalk along the top, filler domes, pipes with valves down to a dispenser."""
    out = []
    tk, bw, st, pp = Field("Tank"), Field("Bund"), Field("Steel"), Field("Pipes")
    glows = G("glow_amber")
    L, r, zc = 1.05, 0.42, 0.62
    tk.add(Func(lambda P: (np.maximum(np.sqrt(P[:, 1] ** 2 + (P[:, 2] - F32(zc)) ** 2) - F32(r), np.abs(P[:, 0]) - F32(L))).astype(F32),
                (-1.2, -0.6, 0.1), (1.2, 0.6, 1.2)), k=0.0)
    for sx in (-1, 1):
        tk.add(Ellipsoid((sx * L, 0, zc), (0.16, r, r)), k=0.04)
    tk.paint(Func(lambda P: (np.abs(P[:, 0] - F32(0.2)) - F32(0.12)).astype(F32), (-2, -1, 0), (2, 1, 2)), 5)
    for sy in (-1, 1):
        stencil(tk, (-0.45, sy * r, zc), (0, sy, 0), 0.5, 0.1, label=9, n=4)
    for x in (-0.3, 0.45):
        tk.add(Cylinder((x, 0, zc + r + 0.03), 0.09, 0.07, rr=0.02), k=0.01, label=7)
    for x in (-0.6, 0.6):
        box(bw, (x, 0, 0.15), (0.1, 0.36, 0.15), 0.02)
    bw.add(Func(lambda P: (np.maximum(np.abs(np.maximum(np.abs(P[:, 0]) - F32(1.45), np.abs(P[:, 1]) - F32(0.75))) - F32(0.05),
                                      np.abs(P[:, 2] - F32(0.1)) - F32(0.12))).astype(F32), (-1.6, -0.9, -0.1), (1.6, 0.9, 0.3)), k=0.0)
    # the ladder, the catwalk and its rail
    for sy in (-1, 1):
        seg(st, (-L - 0.22, sy * 0.13, 0.0), (-L - 0.22, sy * 0.13, zc + r + 0.4), 0.012)
    for z in np.arange(0.15, zc + r, 0.13):
        seg(st, (-L - 0.22, -0.13, z), (-L - 0.22, 0.13, z), 0.009)
    box(st, (0, 0, zc + r + 0.06), (L * 0.85, 0.12, 0.012), 0.004)
    for sy in (-1, 1):
        railing_line(st, [(-L * 0.85, sy * 0.12, zc + r + 0.06), (L * 0.85, sy * 0.12, zc + r + 0.06)], h=0.26, step=0.35, r=0.008)
    # pipes, valves, the dispenser
    pp.add(Chain([v3((L - 0.1, -0.3, zc - 0.25)), v3((L + 0.25, -0.5, 0.25)), v3((L + 0.25, -0.5, 0.12)), v3((L + 0.6, -0.5, 0.12))], [0.03] * 4, k=0.04), k=0.0)
    pp.add(Cylinder((L + 0.25, -0.5, 0.3), 0.05, 0.08, rr=0.015), k=0.0, label=7)
    pp.add(Torus((L + 0.25, -0.5, 0.36), 0.055, 0.01), k=0.0, label=8)
    box(pp, (L + 0.72, -0.5, 0.42), (0.12, 0.1, 0.42), 0.02, label=0)
    pp.add(RoundBox((L + 0.72, -0.6, 0.6), (0.08, 0.008, 0.06), 0.004), k=0.0, label=7)
    glows["glow_amber"].add(RoundBox((L + 0.72, -0.605, 0.6), (0.06, 0.004, 0.045), 0.003), k=0.0)
    pp.add(Chain([v3((L + 0.62, -0.62, 0.5)), v3((L + 0.55, -0.75, 0.25)), v3((L + 0.66, -0.66, 0.15))], [0.015] * 3, k=0.02), k=0.0, label=7)
    for f in (bw, st, pp):
        ground_cut(f, -0.02)
    out += [("Tank", tk, fine(0.007, 0.014), "fuel"), ("Bund", bw, fine(0.008, 0.016), "concrete"), ("Steel", st, fine(0.004, 0.008), "galv"),
            ("Pipes", pp, fine(0.005, 0.01), "fuel")]
    return finish_glows(out, glows)


def utility_truck(seed=0):
    """A station utility truck (nose toward +X): a white cab with its windscreen and side windows, an orange stripe, an
    amber light bar on the roof, a utility body with lockers behind it under a ladder rack carrying a ladder,
    headlamps and tail lamps lit."""
    out = []
    bd, gl, tf, hf, lr = Field("Body"), Field("Glass"), Field("Tyres"), Field("Hubs"), Field("Rack")
    glows = G("glow_amber", "glow_lamp", "glow_red")
    hw, rw = 0.33, 0.15
    box(bd, (0.0, 0, 0.24), (0.9, hw - 0.02, 0.06), 0.02, label=7)              # the chassis
    box(bd, (0.62, 0, 0.5), (0.28, hw, 0.24), 0.07)                             # the cab
    box(bd, (0.98, 0, 0.4), (0.15, hw, 0.13), 0.06, k=0.03)                     # the bonnet
    bd.sub(RoundBox((0.88, 0, 0.6), (0.03, hw - 0.05, 0.1), 0.02, R=euler(0, -0.35, 0)), k=0.0)
    gl.add(RoundBox((0.865, 0, 0.6), (0.012, hw - 0.05, 0.1), 0.01, R=euler(0, -0.35, 0)), k=0.0)
    for sy in (-1, 1):
        bd.sub(RoundBox((0.6, sy * hw, 0.6), (0.18, 0.03, 0.09), 0.015), k=0.0)
        gl.add(RoundBox((0.6, sy * (hw - 0.02), 0.6), (0.18, 0.008, 0.09), 0.01), k=0.0)
        box(bd, (0.86, sy * (hw + 0.03), 0.6), (0.02, 0.025, 0.04), 0.008, k=0.004, label=7)
    box(bd, (-0.42, 0, 0.47), (0.5, hw, 0.18), 0.03)                            # the utility body and its lockers
    for sy in (-1, 1):
        for x in (-0.72, -0.42, -0.12):
            bd.sub(RoundBox((x, sy * hw, 0.47), (0.13, 0.004, 0.14), 0.0), k=0.0)
            box(bd, (x + 0.08, sy * (hw + 0.004), 0.5), (0.025, 0.006, 0.008), 0.003, k=0.002, label=6)
    bd.paint(Func(lambda P: (np.abs(P[:, 2] - F32(0.33)) - F32(0.025)).astype(F32), (-2, -1, 0), (2, 1, 1)), 5)
    box(bd, (1.13, 0, 0.3), (0.03, hw + 0.01, 0.05), 0.015, k=0.004, label=7)
    box(bd, (-0.93, 0, 0.3), (0.03, hw, 0.05), 0.015, k=0.004, label=7)
    for sy in (-1, 1):
        glows["glow_lamp"].add(RoundBox((1.12, sy * (hw - 0.08), 0.42), (0.012, 0.05, 0.03), 0.01), k=0.0)
        glows["glow_red"].add(RoundBox((-0.925, sy * (hw - 0.06), 0.45), (0.008, 0.04, 0.05), 0.008), k=0.0)
    box(bd, (0.6, 0, 0.77), (0.04, hw - 0.04, 0.03), 0.01, label=7)
    glows["glow_amber"].add(RoundBox((0.6, 0, 0.81), (0.035, hw - 0.06, 0.025), 0.01), k=0.0)
    for (x0, x1) in ((-0.88, 0.05),):                                            # the ladder rack and its ladder
        for sy in (-1, 1):
            for x in (x0, -0.42, x1):
                seg(lr, (x, sy * (hw - 0.02), 0.65), (x, sy * (hw - 0.02), 0.82), 0.012)
            seg(lr, (x0, sy * (hw - 0.02), 0.82), (x1 + 0.2, sy * (hw - 0.02), 0.82), 0.012)
        for x in (x0, -0.42, x1):
            seg(lr, (x, -hw + 0.02, 0.82), (x, hw - 0.02, 0.82), 0.012)
    for sy in (-0.12, 0.12):
        seg(lr, (-0.95, sy, 0.86), (0.55, sy, 0.86), 0.013)
    for x in np.arange(-0.88, 0.55, 0.16):
        seg(lr, (x, -0.12, 0.86), (x, 0.12, 0.86), 0.008)
    for x in (0.7, -0.62):
        for sy in (-1, 1):
            bd.sub(Cylinder((x, sy * (hw - 0.02), rw), rw + 0.02, 0.2, R=RY), k=0.02)
            wheel(tf, hf, (x, sy * (hw - 0.07), rw), (0, sy, 0), rw, 0.1, lugs=5)
    ground_cut(tf, -0.01)
    out += [("Body", bd, fine(0.006, 0.012), "truck"), ("Glass", gl, fine(0.005, 0.01), "glass"), ("Tyres", tf, fine(0.005, 0.01), "rubber"),
            ("Hubs", hf, fine(0.004, 0.008), "galv"), ("Rack", lr, fine(0.004, 0.008), "galv")]
    return finish_glows(out, glows)


# ------------------------------------------------------------------------------------------------ Dish Array: no-build zones
def big_dish(seed=0):
    """A big dish on its king-post mount: a concrete footing, the steel pedestal and its azimuth head, the white
    reflector tilted up on its elevation jack, the feed on a tripod, a cable conduit and a hazard-striped kerb."""
    out = []
    ds, mt, ft, fd = Field("Dish"), Field("Mount"), Field("Footing"), Field("Feed")
    glows = G("glow_red")
    ft.add(hexagon((0, 0), 0.7, 0.14), k=0.0)
    ft.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(0.56)) - F32(0.05)).astype(F32), (-1, -1, -0.1), (1, 1, 0.3)), 8)
    mt.add(Cylinder((0, 0, 0.7), 0.16, 1.1, rr=0.03), k=0.0)
    mt.add(Cylinder((0, 0, 1.28), 0.26, 0.18, rr=0.04), k=0.01, label=7)
    ax = unit(v3((0, -0.62, 0.78)))
    piv = v3((0, 0.05, 1.42))
    vert = piv + ax * 0.22
    Rd, Fc = 1.15, 0.6
    ds.add(dish_fn(vert, ax, Rd, Fc, 0.016), k=0.0)
    ds.add(dish_rim(vert, ax, Rd, Fc, 0.025), k=0.006, label=7)
    for t in (0.55,):
        Rr = Rd * t
        mt.add(Torus(vert + ax * (Rr * Rr / (4 * Fc) - 0.08), Rr, 0.022, R=rot_from_axes(z_axis=ax)), k=0.0)
    for k in range(8):
        a = k * math.pi / 4
        seg(mt, dish_point(vert, ax, Rd, Fc, a, 0.97) - ax * 0.03, dish_point(vert, ax, Rd, Fc, a, 0.15) - ax * 0.16, 0.018)
    mt.add(Cylinder(vert - ax * 0.08, 0.22, 0.14, rr=0.03, R=rot_from_axes(z_axis=ax)), k=0.0, label=7)
    mt.add(Cylinder(piv, 0.07, 0.6, rr=0.02, R=RX), k=0.0, label=7)
    seg(mt, (0, 0.22, 1.0), vert - ax * 0.1 + v3((0, 0.25, -0.15)), 0.035)   # the elevation jack
    mt.add(Cylinder((0, 0.22, 1.0), 0.05, 0.12, rr=0.01, R=RX), k=0.0, label=7)
    Fp = vert + ax * Fc
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        seg(fd, dish_point(vert, ax, Rd, Fc, a, 0.92) + ax * 0.02, Fp - ax * 0.03, 0.016)
    fd.add(RoundCone(Fp - ax * 0.1, Fp + ax * 0.08, 0.05, 0.08), k=0.01, label=7)
    glows["glow_red"].add(Sphere(dish_point(vert, ax, Rd, Fc, math.pi / 2, 1.0) + ax * 0.04, 0.035), k=0.0)
    cd = Field("Conduit")
    cd.add(Chain([v3((0.1, 0.12, 0.5)), v3((0.25, 0.4, 0.06)), v3((0.7, 0.75, 0.04)), v3((1.0, 0.9, 0.04))], [0.03] * 4, k=0.04), k=0.0)
    for f in (ft, mt, cd):
        ground_cut(f, -0.02)
    out += [("Dish", ds, fine(0.007, 0.014), "radome"), ("Mount", mt, fine(0.005, 0.01), "galv"), ("Footing", ft, fine(0.008, 0.016), "concrete"),
            ("Feed", fd, fine(0.004, 0.008), "radome"), ("Conduit", cd, fine(0.004, 0.008), "graphite")]
    return finish_glows(out, glows)


def solar_array(seed=0):
    """A solar array on its bed: three rows of panels tilted up toward -Y, each row carried on single steel posts set on
    the ground's footings (rows at y = -0.8, 0, 0.8, posts every 0.55 in x), an inverter cabinet on its posts at the
    east end with a status light and display, the cable conduit from the rows to it."""
    out = []
    sl, fr, rk, iv = Field("Cells"), Field("Frames"), Field("Racking"), Field("Inverter")
    glows = G("glow_green", "glow_screen")
    tilt, zr = 0.5, 0.5
    xs = [-1.375, -0.825, -0.275, 0.275, 0.825, 1.375]
    for y in (-0.8, 0.0, 0.8):
        for x in (-0.92, 0.0, 0.92):
            _panel(sl, fr, (x, y, zr + 0.08), 0.0, tilt, W=0.45, Hh=0.26)
        for x in xs:
            seg(rk, (x, y, 0.0), (x, y, zr), 0.024)
            rk.add(Cylinder((x, y, 0.02), 0.05, 0.05, rr=0.01), k=0.0, label=7)
            seg(rk, (x, y - 0.18, zr - 0.02), (x, y + 0.18, zr + 0.16), 0.016)
        seg(rk, (-1.4, y, zr + 0.02), (1.4, y, zr + 0.02), 0.018)
    box(iv, (1.62, 0.0, 0.55), (0.1, 0.16, 0.22), 0.02)
    for sy in (-1, 1):
        seg(iv, (1.62, sy * 0.1, 0.0), (1.62, sy * 0.1, 0.35), 0.02, label=7)
    iv.sub(RoundBox((1.72, 0.0, 0.62), (0.02, 0.1, 0.06), 0.006), k=0.0)
    glows["glow_screen"].add(RoundBox((1.715, 0.0, 0.62), (0.006, 0.09, 0.05), 0.003), k=0.0)
    glows["glow_green"].add(RoundBox((1.725, 0.08, 0.48), (0.006, 0.015, 0.012), 0.004), k=0.0)
    cd = Field("Conduit")
    cd.add(Chain([v3((1.52, 0.0, 0.4)), v3((1.45, 0.05, 0.03)), v3((1.2, 0.1, 0.03)), v3((1.2, 0.45, 0.03)), v3((-1.3, 0.45, 0.03))], [0.025] * 5, k=0.04), k=0.0)
    for f in (rk, iv, cd):
        ground_cut(f, -0.02)
    out += [("Cells", sl, fine(0.004, 0.008), "solar"), ("Frames", fr, fine(0.004, 0.008), "galv"), ("Racking", rk, fine(0.004, 0.008), "galv"),
            ("Inverter", iv, fine(0.005, 0.01), "graphite"), ("Conduit", cd, fine(0.004, 0.008), "graphite")]
    return finish_glows(out, glows)


# ------------------------------------------------------------------------------------------------ Neon Grid: scatter
def _glyph_column(f, c, nrm, n, h, seed, r=0.01):
    """A column of n invented glyphs (field f) reading downward on a face at c (its top glyph's middle), facing nrm."""
    nrm = unit(nrm)
    side = unit(np.cross(Z, nrm))
    for i in range(n):
        glyphs(f, v3(c) - Z * (i * h * 1.3), -side, 1, h, seed * 7 + i, r=r)


def neon_sign(seed=0, variant=0):
    """A neon street sign. Variant 0: a tall blade sign on its pole, a column of invented glyphs in magenta tube down
    both faces, a cyan tube round its edge. Variant 1: an arrow in magenta tube over a box sign of cyan glyphs, on a
    bracket off a short pole."""
    out = []
    pl, bd = Field("Pole"), Field("Board")
    glows = G("glow_magenta", "glow_cyan")
    if variant == 0:
        seg(pl, (0, 0, -0.02), (0, 0, 2.5), 0.035, 0.03)
        pl.add(Cylinder((0, 0, 0.05), 0.08, 0.1, rr=0.02), k=0.0, label=7)
        for z in (1.4, 2.4):
            seg(pl, (0, 0, z), (0.18, 0, z), 0.018)
        c = v3((0.3, 0, 1.9))
        box(bd, c, (0.13, 0.03, 0.58), 0.02)
        for sy in (-1, 1):
            _glyph_column(glows["glow_magenta"], c + v3((0, sy * 0.04, 0.44)), (0, sy, 0), 4, 0.17, seed + sy, r=0.011)
            for (a, b) in (((-0.11, 0.56), (0.11, 0.56)), ((0.11, 0.56), (0.11, -0.56)), ((0.11, -0.56), (-0.11, -0.56)), ((-0.11, -0.56), (-0.11, 0.56))):
                seg(glows["glow_cyan"], c + v3((a[0], sy * 0.038, a[1])), c + v3((b[0], sy * 0.038, b[1])), 0.009)
    else:
        seg(pl, (0, 0, -0.02), (0, 0, 2.2), 0.035, 0.03)
        pl.add(Cylinder((0, 0, 0.05), 0.08, 0.1, rr=0.02), k=0.0, label=7)
        seg(pl, (0, 0, 2.05), (0.75, 0, 2.05), 0.02)
        for x in (0.25, 0.65):
            seg(pl, (x, 0, 2.05), (x, 0, 1.92), 0.01)
        c = v3((0.45, 0, 1.7))
        box(bd, c, (0.36, 0.035, 0.2), 0.03)
        for sy in (-1, 1):
            glyphs(glows["glow_cyan"], c + v3((0, sy * 0.045, 0.0)), (-sy, 0, 0), 4, 0.17, seed + 3 * sy, r=0.011)
        arrow = [(-0.3, 0.12), (0.12, 0.12), (0.12, 0.24), (0.38, 0.0), (0.12, -0.24), (0.12, -0.12), (-0.3, -0.12), (-0.3, 0.12)]
        a0 = v3((0.45, 0, 2.38))
        box(bd, a0 - Z * 0.01, (0.4, 0.02, 0.27), 0.02, label=7)
        for sy in (-1, 1):
            pts = [a0 + v3((x, sy * 0.03, z)) for (x, z) in arrow]
            for a, b in zip(pts[:-1], pts[1:]):
                seg(glows["glow_magenta"], a, b, 0.012)
    ground_cut(pl, -0.02)
    out += [("Pole", pl, fine(0.004, 0.008), "graphite"), ("Board", bd, fine(0.005, 0.01), "graphite")]
    return finish_glows(out, glows)


def holo_pylon(seed=0):
    """A holo-ad pylon: a slim graphite column on its plinth with a projector head, the advert hanging in the air beside
    it as glowing scan lines of cyan with a magenta glyph line and frame over them."""
    out = []
    pl = Field("Pylon")
    glows = G("glow_cyan", "glow_magenta", "glow_violet")
    pl.add(hexagon((0, 0), 0.2, 0.12), k=0.0, label=7)
    pl.add(RoundBox((0, 0, 0.95), (0.07, 0.07, 0.85), 0.03), k=0.0)
    pl.add(RoundBox((0.06, 0, 1.85), (0.14, 0.1, 0.07), 0.03), k=0.01, label=7)
    strip(glows["glow_violet"], (0, -0.072, 0.25), (0, -0.072, 1.7), 0.02, up=(0, -1, 0))
    glows["glow_cyan"].add(Sphere((0.2, 0, 1.85), 0.035), k=0.0)
    c = v3((0.62, 0, 1.25))
    W, H = 0.38, 0.5
    n = 9
    for i in range(n):
        z = c[2] - H + (i + 0.5) * 2 * H / n
        glows["glow_cyan"].add(RoundBox((c[0], c[1], z), (W, 0.006, H / n * 0.55), 0.004), k=0.0)
    for (a, b) in (((-W, H), (W, H)), ((W, H), (W, -H)), ((W, -H), (-W, -H)), ((-W, -H), (-W, H))):
        seg(glows["glow_magenta"], c + v3((a[0], -0.012, a[1])), c + v3((b[0], -0.012, b[1])), 0.008)
    glyphs(glows["glow_magenta"], c + v3((0, -0.015, 0.12)), (1, 0, 0), 4, 0.16, seed, r=0.009)
    glows["glow_magenta"].add(RoundBox(c + v3((0, -0.015, -0.25)), (0.25, 0.006, 0.03), 0.006), k=0.0)
    ground_cut(pl, -0.02)
    out.append(("Pylon", pl, fine(0.004, 0.008), "graphite"))
    return finish_glows(out, glows)


def vending_machines(seed=0):
    """Vending machines (front toward -Y): a red one and a blue one side by side, their lit windows of drinks, glowing
    logo bands, coin panels and the dispenser slots; a recycling bin beside them."""
    out = []
    rd, bl, bn = Field("Red"), Field("Blue"), Field("Bin")
    glows = G("glow_screen", "glow_magenta", "glow_cyan")
    for (f, x, logo) in ((rd, -0.23, "glow_magenta"), (bl, 0.23, "glow_cyan")):
        box(f, (x, 0, 0.5), (0.22, 0.2, 0.5), 0.02)
        box(f, (x, -0.21, 0.04), (0.2, 0.02, 0.04), 0.008, label=7)
        f.sub(RoundBox((x - 0.04, -0.2, 0.58), (0.14, 0.03, 0.28), 0.01), k=0.0)
        glows["glow_screen"].add(RoundBox((x - 0.04, -0.185, 0.58), (0.14, 0.006, 0.28), 0.004), k=0.0)
        for j in range(4):                                          # the shelves of drinks in the window
            for i in range(4):
                f.add(Cylinder((x - 0.14 + i * 0.065, -0.19, 0.36 + j * 0.13), 0.02, 0.07, rr=0.008), k=0.0, label=(5 if (i + j) % 2 else 9))
            f.add(RoundBox((x - 0.04, -0.188, 0.32 + j * 0.13), (0.14, 0.012, 0.005), 0.003), k=0.0, label=7)
        box(f, (x + 0.15, -0.205, 0.55), (0.04, 0.012, 0.12), 0.008, label=7)
        f.add(RoundBox((x - 0.02, -0.205, 0.17), (0.13, 0.02, 0.05), 0.01), k=0.0, label=7)
        glows[logo].add(RoundBox((x, -0.205, 0.93), (0.18, 0.006, 0.04), 0.006), k=0.0)
    bn.add(Cylinder((0.62, -0.05, 0.25), 0.13, 0.5, rr=0.03), k=0.0)
    bn.add(Ellipsoid((0.62, -0.05, 0.5), (0.14, 0.14, 0.05)), k=0.02, label=7)
    bn.sub(Cylinder((0.62, -0.05, 0.55), 0.05, 0.1), k=0.0)
    for f in (rd, bl, bn):
        ground_cut(f, -0.02)
    out += [("Red", rd, fine(0.004, 0.008), "vending_red"), ("Blue", bl, fine(0.004, 0.008), "vending_blue"), ("Bin", bn, fine(0.004, 0.008), "street_iron")]
    return finish_glows(out, glows)


def food_cart(seed=0):
    """A street food cart (front toward -Y): a red cart on two wheels with its counter and a steaming pot, a striped
    awning on poles hung with paper lanterns, a menu board of glowing glyphs, two stools."""
    out = []
    ct, aw, wh, pt, st = Field("Cart"), Field("Awning"), Field("Wheels"), Field("Pot"), Field("Stools")
    glows = G("glow_red", "glow_amber", "glow_magenta")
    box(ct, (0, 0, 0.5), (0.5, 0.26, 0.3), 0.03)
    box(ct, (0, -0.05, 0.82), (0.55, 0.34, 0.025), 0.01, label=5)
    ct.paint(Func(lambda P: (np.abs(P[:, 2] - F32(0.62)) - F32(0.04)).astype(F32), (-1, -1, 0), (1, 1, 1)), 9)
    for sy in (-1, 1):
        wheel(wh, ct, (-0.28, sy * 0.28, 0.2), (0, sy, 0), 0.2, 0.05)
    seg(ct, (0.45, 0.0, 0.25), (0.75, 0.0, 0.3), 0.02, label=7)
    for x in (0.38, 0.45):
        seg(ct, (x, -0.2, 0.2), (x, -0.2, 0.0), 0.02, label=7)
    pt.add(Cylinder((0.22, 0.05, 0.92), 0.13, 0.18, rr=0.02), k=0.0)
    pt.add(Torus((0.22, 0.05, 1.01), 0.13, 0.012), k=0.004)
    pt.add(Cylinder((-0.15, 0.05, 0.88), 0.1, 0.1, rr=0.02), k=0.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            seg(ct, (sx * 0.5, sy * 0.3, 0.82), (sx * 0.5, sy * 0.3, 1.62), 0.014, label=7)
    nrm = unit(v3((0, -0.4, 1)))
    Ra = rot_from_axes(z_axis=nrm, y_axis=(0, 1, 0.4))
    aw.add(RoundBox((0, -0.08, 1.66), (0.62, 0.48, 0.012), 0.008, R=Ra), k=0.0)
    for k in range(7):
        if k % 2 == 0:
            aw.paint(RoundBox((-0.54 + k * 0.18, -0.08, 1.66), (0.09, 0.6, 0.1), 0.0), 5)
    aw.add(RoundBox((0, -0.56, 1.55), (0.62, 0.008, 0.06), 0.004), k=0.004)
    for i in range(5):                                              # lanterns under the awning's front edge
        x = -0.48 + i * 0.24
        seg(aw, (x, -0.52, 1.5), (x, -0.52, 1.4), 0.004, label=7)
        glows["glow_red" if i % 2 == 0 else "glow_amber"].add(Ellipsoid((x, -0.52, 1.32), (0.06, 0.06, 0.08)), k=0.0)
    box(ct, (0.0, 0.3, 1.25), (0.3, 0.02, 0.17), 0.01, label=7)
    glyphs(glows["glow_magenta"], (0.0, 0.275, 1.27), (-1, 0, 0), 3, 0.14, seed, r=0.009)
    for x in (-0.3, 0.25):                                          # stools
        st.add(Cylinder((x, -0.62, 0.48), 0.1, 0.04, rr=0.015), k=0.0)
        for k in range(3):
            a = k * 2 * math.pi / 3
            seg(st, (x + math.cos(a) * 0.04, -0.62 + math.sin(a) * 0.04, 0.46), (x + math.cos(a) * 0.12, -0.62 + math.sin(a) * 0.12, 0.0), 0.012)
    for f in (ct, wh, st):
        ground_cut(f, -0.02)
    out += [("Cart", ct, fine(0.005, 0.01), "stall"), ("Awning", aw, fine(0.005, 0.01), "canvas"), ("Wheels", wh, fine(0.004, 0.008), "rubber"),
            ("Pot", pt, fine(0.004, 0.008), "pot_metal"), ("Stools", st, fine(0.004, 0.008), "street_iron")]
    return finish_glows(out, glows)


FOOD_STEAM = (0.22, 0.05, 1.08)


def cable_pole(seed=0):
    """A utility pole hung with the city's cables: a dark steel pole with two crossarms and their insulators, a
    transformer can, cables sagging off it in loops and a bundle running down to a box at its foot."""
    out = []
    pl, ca, tr = Field("Pole"), Field("Cables"), Field("Transformer")
    glows = G("glow_amber")
    H = 2.7
    seg(pl, (0, 0, -0.02), (0, 0, H), 0.05, 0.035)
    for z, L in ((H - 0.1, 0.55), (H - 0.45, 0.45)):
        seg(pl, (-L, 0, z), (L, 0, z), 0.022)
        for x in (-L + 0.05, -L * 0.4, L * 0.4, L - 0.05):
            pl.add(Cylinder((x, 0, z + 0.05), 0.022, 0.07, rr=0.008), k=0.004, label=6)
    tr.add(Cylinder((0, 0.16, H - 0.85), 0.13, 0.32, rr=0.03), k=0.0)
    seg(tr, (0, 0.03, H - 0.75), (0, 0.13, H - 0.75), 0.02)
    glows["glow_amber"].add(Sphere((0.0, 0.03, H - 0.95), 0.025), k=0.0)
    rng = np.random.default_rng(seed)
    for k in range(5):                                              # sagging loops off the crossarms
        z = (H - 0.05) if k < 3 else (H - 0.4)
        x0 = rng.uniform(-0.5, 0.5)
        x1 = x0 + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9)
        x1 = float(np.clip(x1, -0.9, 0.9))
        mid = v3(((x0 + x1) / 2, rng.uniform(-0.25, 0.25), z - rng.uniform(0.25, 0.5)))
        ca.add(Chain([v3((x0, 0, z)), mid, v3((x1, 0.1, z - 0.4 * (abs(x1) > 0.6)))], [0.009] * 3, k=0.1), k=0.0, label=(5 if k == 1 else 0))
    ca.add(Chain([v3((0.04, 0.05, H - 0.4)), v3((0.08, 0.06, 1.2)), v3((0.08, 0.08, 0.35))], [0.03] * 3, k=0.04), k=0.0)
    box(pl, (0.08, 0.14, 0.25), (0.12, 0.08, 0.2), 0.015, label=7)
    ground_cut(pl, -0.02)
    out += [("Pole", pl, fine(0.005, 0.01), "street_iron"), ("Cables", ca, fine(0.004, 0.008), "cables"), ("Transformer", tr, fine(0.005, 0.01), "street_iron")]
    return finish_glows(out, glows)


def trash_bins(seed=0):
    """Trash: two wheelie bins (one lid propped open on its overflow), black bin bags piled against them, a flattened
    box."""
    out = []
    bn, bg, bx = Field("Bins"), Field("Bags"), Field("Box")
    rng = np.random.default_rng(seed)
    for i, x in enumerate((-0.22, 0.22)):
        bn.add(RoundCone((x, 0.0, 0.03), (x, 0.0, 0.62), 0.17, 0.2), k=0.0)
        bn.add(RoundBox((x, 0.0, 0.32), (0.18, 0.2, 0.3), 0.04), k=0.04)
        bn.sub(RoundBox((x, 0.0, 0.66), (0.15, 0.17, 0.06), 0.02), k=0.0)
        if i == 0:
            bn.add(RoundBox((x, 0.0, 0.66), (0.2, 0.22, 0.015), 0.01), k=0.0, label=7)
        else:
            bn.add(RoundBox((x, 0.18, 0.86), (0.2, 0.015, 0.22), 0.01), k=0.0, label=7)
            bg.add(Ellipsoid((x, 0.0, 0.66), (0.16, 0.17, 0.1), **wob(10.0, 0.02, seed)), k=0.0)
        for sy in (-1, 1):
            bn.add(Cylinder((x - 0.05 * sy, 0.2, 0.05), 0.05, 0.04, R=RX), k=0.0, label=7)
        bn.paint(RoundBox((x, -0.21, 0.4), (0.08, 0.03, 0.05), 0.0), 5)
    for k in range(4):
        c = v3((rng.uniform(-0.4, 0.45), -0.32 + rng.uniform(-0.08, 0.08), 0.13))
        bg.add(Ellipsoid(c, (0.16, 0.14, 0.14), **wob(9.0, 0.02, seed + k)), k=0.03)
        bg.add(RoundCone(c + Z * 0.1, c + Z * 0.18, 0.03, 0.015), k=0.02)
    box(bx, (0.55, 0.15, 0.03), (0.2, 0.15, 0.025), 0.01, R=Rz(0.4))
    for f in (bn, bg, bx):
        ground_cut(f, -0.02)
    out += [("Bins", bn, fine(0.005, 0.01), "street_iron"), ("Bags", bg, fine(0.005, 0.01), "bags"), ("Box", bx, fine(0.004, 0.008), "paper")]
    return out


def neon_light(seed=0, glow="glow_magenta"):
    """A street light of the neon city: a slim graphite pole with a long arm carrying a linear lamp glowing magenta
    (or cyan), a ring of the same light round its foot."""
    out = []
    pl = Field("Pole")
    glows = G(glow)
    gf = glows[glow]
    pl.add(Cylinder((0, 0, 0.06), 0.09, 0.12, rr=0.02), k=0.0, label=7)
    seg(pl, (0, 0, 0.1), (0, 0, 2.5), 0.04, 0.028)
    pl.add(RoundBox((0.42, 0, 2.5), (0.48, 0.045, 0.035), 0.02), k=0.02)
    gf.add(RoundBox((0.48, 0, 2.46), (0.38, 0.03, 0.012), 0.008), k=0.0)
    gf.add(Torus((0, 0, 0.14), 0.07, 0.012), k=0.0)
    ground_cut(pl, -0.02)
    out.append(("Pole", pl, fine(0.004, 0.008), "graphite"))
    return finish_glows(out, glows)


def puddle_piece(seed=0, w=0.7):
    """A rain puddle on the asphalt, reflecting the neon."""
    f = Field("Puddle")
    f.add(Ellipsoid((0, 0, -0.01), (w, w * 0.6, 0.04), **wob(3.0, 0.08, seed)), k=0.0)
    f.inter(Plane((0, 0, 0.012), (0, 0, 1)))
    ground_cut(f, -0.02)
    return [("Puddle", f, fine(0.006, 0.01), "puddle")]


def glow_planter(seed=0):
    """A planter of glowing plants: a graphite box with a violet light strip round its lip, dark soil, arching blades
    glowing cyan and bulbs glowing magenta on their stems."""
    out = []
    pc, so, st = Field("Planter"), Field("Soil"), Field("Stems")
    glows = G("glow_cyan", "glow_magenta", "glow_violet")
    box(pc, (0, 0, 0.18), (0.42, 0.26, 0.18), 0.03)
    pc.sub(RoundBox((0, 0, 0.38), (0.37, 0.21, 0.12), 0.02), k=0.0)
    for sy in (-1, 1):
        strip(glows["glow_violet"], (-0.4, sy * 0.262, 0.3), (0.4, sy * 0.262, 0.3), 0.018, up=(0, sy, 0))
    so.add(RoundBox((0, 0, 0.3), (0.38, 0.22, 0.03), 0.02, **wob(10.0, 0.008, seed)), k=0.0)
    rng = np.random.default_rng(seed)
    for k in range(9):                                              # arching blades
        a = 2 * math.pi * k / 9 + rng.uniform(-0.3, 0.3)
        d = v3((math.cos(a), math.sin(a) * 0.6, 0))
        b0 = v3((rng.uniform(-0.2, 0.2), rng.uniform(-0.08, 0.08), 0.32))
        L = rng.uniform(0.35, 0.55)
        pts = [b0, b0 + d * L * 0.3 + Z * L * 0.6, b0 + d * L * 0.75 + Z * L * 0.75, b0 + d * L + Z * L * 0.45]
        glows["glow_cyan"].add(Chain(pts, [0.022, 0.02, 0.014, 0.004], k=0.02), k=0.0)
    for k in range(4):
        b0 = v3((rng.uniform(-0.28, 0.28), rng.uniform(-0.12, 0.12), 0.32))
        tip = b0 + v3((rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), rng.uniform(0.35, 0.6)))
        seg(st, b0, tip, 0.008)
        glows["glow_magenta"].add(Sphere(tip, rng.uniform(0.035, 0.05)), k=0.0)
    ground_cut(pc, -0.02)
    out += [("Planter", pc, fine(0.005, 0.01), "graphite"), ("Soil", so, fine(0.006, 0.012), "bags"), ("Stems", st, fine(0.003, 0.006), "street_iron")]
    return finish_glows(out, glows)


# ------------------------------------------------------------------------------------------------ Neon Grid: landmarks
def _lit_strips(gf, cx, cy, hx, hy, z0, z1, seed, p=0.45, floor=0.3, inset=0.06, faces=None):
    """Lit window runs on a block's four faces (field gf; `faces`: only those, as (nx, ny)): on each floor of each face,
    maybe a run of glowing windows over part of its width."""
    rng = np.random.default_rng(seed)
    nfl = int((z1 - z0) / floor)
    for (nx, ny, hw) in ((0, -1, hx), (0, 1, hx), (-1, 0, hy), (1, 0, hy)):
        if faces is not None and (nx, ny) not in faces:
            continue
        for j in range(nfl):
            if rng.random() > p:
                continue
            a = rng.uniform(-hw + inset, hw - inset - 0.2)
            b = min(hw - inset, a + rng.uniform(0.2, hw))
            u = (a + b) / 2
            z = z0 + (j + 0.55) * floor
            sx, sy = (1, 0) if nx == 0 else (0, 1)
            q = v3((cx + nx * (hx + 0.005) + sx * u, cy + ny * (hy + 0.005) + sy * u, z))
            gf.add(RoundBox(q, (abs(sx) * (b - a) / 2 + abs(nx) * 0.006, abs(sy) * (b - a) / 2 + abs(ny) * 0.006, floor * 0.28), 0.004), k=0.0)


def cyber_tower(seed=0, variant=0):
    """A tower of the neon city (front toward -Y): dark glass in its grid of mullions with runs of lit windows warm and
    cool, a tall blade sign of invented glyphs down its front, glowing bands at its setbacks, a lit shopfront under a
    canopy at street level; on the roof a sign frame with big glyphs (variant 0) or a hologram ring (variant 1),
    antennas with red lights and air handlers."""
    out = []
    cw, gw, st, rf = Field("Glass"), Field("LitFloors"), Field("Frame"), Field("Roof")
    glows = G("glow_window", "glow_window_cool", "glow_magenta", "glow_cyan", "glow_violet", "glow_red")
    if variant == 0:
        tiers = [(0.96, 0.8, 0.42, 4.92), (0.64, 0.64, 4.92, 6.42)]
        rc = 0.015
    else:
        tiers = [(0.8, 0.8, 0.42, 3.72), (0.64, 0.64, 3.72, 5.22), (0.48, 0.48, 5.22, 6.12)]
        rc = 0.18
    for k, (hx, hy, z0, z1) in enumerate(tiers):
        curtain_box(cw, gw, 0, 0, hx, hy, z0, z1, seed + k, bands=(), p=0.12, rc=rc)
        _lit_strips(glows["glow_window_cool" if k % 2 == 0 else "glow_window"], 0, 0, hx, hy, z0, z1, seed * 3 + k, p=0.3)
        _lit_strips(glows["glow_window" if k % 2 == 0 else "glow_window_cool"], 0, 0, hx, hy, z0, z1, seed * 5 + k, p=0.15)
        st.add(rrect(0, 0, hx + 0.03, hy + 0.03, z1 - 0.04, z1 + 0.04, rc + 0.03), k=0.0)
        if k < len(tiers) - 1:                                      # a glowing band at the setback
            ring_f = rrect(0, 0, hx + 0.035, hy + 0.035, z1 - 0.1, z1 - 0.06, rc + 0.035)
            fnr = ring_f.fn
            glows["glow_cyan" if variant == 1 else "glow_magenta"].add(Func(lambda P, fnr=fnr: np.maximum(fnr(P), -(fnr(P) + F32(0.03))).astype(F32), ring_f.lo, ring_f.hi), k=0.0)
    # the blade sign down the front
    hx, hy = tiers[0][0], tiers[0][1]
    bx = -hx + 0.25 if variant == 0 else hx - 0.2
    c = v3((bx, -hy - 0.28, 2.9))
    box(st, c, (0.035, 0.24, 1.35), 0.02)
    for sx in (-1, 1):
        _glyph_column(glows["glow_magenta" if variant == 0 else "glow_cyan"], c + v3((sx * 0.045, 0, 1.12)), (sx, 0, 0), 7, 0.24, seed + sx, r=0.013)
        for (a, b) in (((-0.2, 1.3), (0.2, 1.3)), ((0.2, 1.3), (0.2, -1.3)), ((0.2, -1.3), (-0.2, -1.3)), ((-0.2, -1.3), (-0.2, 1.3))):
            seg(glows["glow_cyan" if variant == 0 else "glow_violet"], c + v3((sx * 0.043, a[0], a[1])), c + v3((sx * 0.043, b[0], b[1])), 0.01)
    for z in (1.7, 4.1):
        seg(st, (bx, -hy, z), (bx, -hy - 0.1, z), 0.02)
    # the shopfront at street level
    pl, sh = Field("Plinth"), Field("Shop")
    box(pl, (0, 0, 0.21), (hx + 0.02, hy + 0.02, 0.21), 0.01)
    pl.sub(RoundBox((0, -hy, 0.2), (hx - 0.12, 0.12, 0.2), 0.01), k=0.0)
    glows["glow_window"].add(RoundBox((0, -hy + 0.1, 0.2), (hx - 0.12, 0.012, 0.19), 0.004), k=0.0)
    box(sh, (0, -hy - 0.2, 0.44), (hx * 0.75, 0.2, 0.025), 0.01)
    strip(glows["glow_violet" if variant == 0 else "glow_magenta"], (-hx * 0.75, -hy - 0.405, 0.44), (hx * 0.75, -hy - 0.405, 0.44), 0.03, up=(0, -1, 0))
    glyphs(glows["glow_cyan" if variant == 0 else "glow_magenta"], (0, -hy - 0.13, 0.54), (1, 0, 0), 5, 0.13, seed + 9, r=0.009)
    box(sh, (0, -hy - 0.11, 0.54), (0.5, 0.012, 0.09), 0.006, label=7)
    # the roof
    top = tiers[-1]
    hx2, hy2, z1 = top[0], top[1], top[3]
    box(rf, (0.15, 0.15, z1 + 0.18), (0.3, 0.25, 0.16), 0.02)
    for (x, y) in ((-0.3, 0.25), (-0.3, -0.05)):
        box(rf, (x, y, z1 + 0.1), (0.12, 0.1, 0.08), 0.02, label=7)
    if variant == 0:
        sc = v3((0.0, -hy2 + 0.1, z1 + 0.75))
        for x in (-0.5, 0.0, 0.5):
            seg(st, (x, -hy2 + 0.12, z1), (x, -hy2 + 0.12, z1 + 1.05), 0.018)
        seg(st, (-0.6, -hy2 + 0.12, z1 + 1.05), (0.6, -hy2 + 0.12, z1 + 1.05), 0.018)
        seg(st, (-0.6, -hy2 + 0.12, z1 + 0.45), (0.6, -hy2 + 0.12, z1 + 0.45), 0.018)
        glyphs(glows["glow_cyan"], sc - v3((0, 0.04, 0)), (1, 0, 0), 4, 0.42, seed + 11, r=0.022)
        lattice_mast(st, (0.45, 0.3, 0), z1, z1 + 1.4, 0.08, 0.04, step=0.2, rod=0.008)
        glows["glow_red"].add(Sphere((0.45, 0.3, z1 + 1.44), 0.04), k=0.0)
    else:
        hc = v3((0.0, 0.0, z1 + 0.9))
        seg(st, (0, 0, z1), hc - Z * 0.3, 0.04)
        glows["glow_magenta"].add(Torus(hc, 0.42, 0.022, R=rot_from_axes(z_axis=(0, -0.3, 1))), k=0.0)
        _hex_emblem(glows["glow_cyan"], hc + Z * 0.1, (0, -1, 0), 0.3, t=0.016)
        seg(st, (0.3, 0.3, z1), (0.3, 0.3, z1 + 1.6), 0.03, 0.006)
        glows["glow_red"].add(Sphere((0.3, 0.3, z1 + 1.63), 0.035), k=0.0)
    ground_cut(pl, -0.02)
    out += [("Glass", cw, fine(0.012, 0.024), "tower_curtain"), ("Frame", st, fine(0.006, 0.012), "graphite"), ("Roof", rf, fine(0.01, 0.02), "graphite"),
            ("Plinth", pl, fine(0.008, 0.016), "graphite"), ("Shop", sh, fine(0.006, 0.012), "graphite")]
    if any(op[0] == "add" for op in gw.ops):
        out.append(("LitFloors", gw, fine(0.008, 0.016), "glow_window"))
    return finish_glows(out, glows, fine(0.006, 0.012))


def holo_billboard(seed=0):
    """A giant holographic billboard (front toward -Y): two tall graphite pylons and the projector beam between them,
    its lenses lit, the hologram standing over it as a great panel of cyan scan lines with a magenta emblem and lines
    of glyphs, a violet frame of light."""
    out = []
    st, pj = Field("Pylons"), Field("Projector")
    glows = G("glow_cyan", "glow_magenta", "glow_violet", "glow_red")
    W, Z0, H = 1.35, 1.0, 0.85
    for sx in (-1, 1):
        x = sx * (W + 0.2)
        st.add(hexagon((x, 0), 0.22, 0.15), k=0.0, label=7)
        st.add(RoundBox((x, 0, Z0 + H), (0.1, 0.12, Z0 + H), 0.03), k=0.0)
        strip(glows["glow_violet"], (x, -0.122, 0.3), (x, -0.122, 2 * (Z0 + H) - 0.1), 0.025, up=(0, -1, 0))
        glows["glow_red"].add(Sphere((x, 0, 2 * (Z0 + H) + 0.06), 0.04), k=0.0)
    box(pj, (0, 0, Z0 - 0.12), (W + 0.12, 0.15, 0.1), 0.03)
    for i in range(6):
        x = -W + 0.2 + i * (2 * W - 0.4) / 5
        pj.add(Cylinder((x, -0.08, Z0 - 0.01), 0.06, 0.05, rr=0.01), k=0.0, label=7)
        glows["glow_cyan"].add(Cylinder((x, -0.08, Z0 + 0.02), 0.045, 0.02, rr=0.006), k=0.0)
    n = 14
    for i in range(n):
        z = Z0 + 0.1 + (i + 0.5) * 2 * H / n
        glows["glow_cyan"].add(RoundBox((0, 0, z), (W, 0.006, H / n * 0.5), 0.004), k=0.0)
    for (a, b) in (((-W, Z0 + 0.1), (W, Z0 + 0.1)), ((W, Z0 + 0.1), (W, Z0 + 0.1 + 2 * H)), ((W, Z0 + 0.1 + 2 * H), (-W, Z0 + 0.1 + 2 * H)),
                   ((-W, Z0 + 0.1 + 2 * H), (-W, Z0 + 0.1))):
        seg(glows["glow_violet"], (a[0], -0.015, a[1]), (b[0], -0.015, b[1]), 0.014)
    ec = v3((-0.65, -0.02, Z0 + 0.1 + H))
    glows["glow_magenta"].add(Torus(ec, 0.45, 0.022, R=RY), k=0.0)
    _hex_emblem(glows["glow_magenta"], ec - v3((0, 0.005, 0)), (0, -1, 0), 0.3, t=0.016)
    for j in range(3):
        glyphs(glows["glow_magenta"], (0.55, -0.02, Z0 + 0.1 + H + 0.45 - j * 0.42), (1, 0, 0), 4, 0.28, seed + j, r=0.016)
    for f in (st, pj):
        ground_cut(f, -0.02)
    out += [("Pylons", st, fine(0.006, 0.012), "graphite"), ("Projector", pj, fine(0.005, 0.01), "graphite")]
    return finish_glows(out, glows)


def noodle_bar(seed=0):
    """A noodle bar (front toward -Y): a narrow shop under a sloping roof, its counter open to the street with stools
    before it, a split cloth curtain over the opening, paper lanterns either side, the kitchen behind lit warm with
    steaming pots, a big sign of glowing glyphs on the roof's edge, a vertical neon sign at its corner, an air
    conditioner and pipes on its side wall."""
    out = []
    bd, rf, ct, nr, st, pt = Field("Shop"), Field("Roof"), Field("Counter"), Field("Curtain"), Field("Stools"), Field("Pots")
    glows = G("glow_window", "glow_red", "glow_amber", "glow_magenta", "glow_cyan")
    W, D, H = 0.9, 0.55, 1.15
    bd.add(walls_box(0, 0, W, D, -0.05, H, batter=0.0, amp=0.003, seed=seed), k=0.0)
    bd.sub(RoundBox((0, -D, 0.62), (W - 0.12, 0.3, 0.38), 0.01), k=0.0)
    glows["glow_window"].add(RoundBox((0, -D + 0.29, 0.62), (W - 0.12, 0.01, 0.38), 0.004), k=0.0)
    for x in (-0.55, -0.15, 0.25):                                  # shelves of bowls on the lit back wall
        box(bd, (x, -D + 0.27, 0.72), (0.15, 0.03, 0.01), 0.004, label=7)
    rf.add(convex([((0, 0, H + 0.12), (0, -0.35, 1)), ((0, 0, H - 0.02), (0, 0, -1)), ((W + 0.12, 0, 0), (1, 0, 0)), ((-W - 0.12, 0, 0), (-1, 0, 0)),
                   ((0, D + 0.08, 0), (0, 1, 0)), ((0, -D - 0.3, 0), (0, -1, 0))], (-W - 0.3, -D - 0.5, H - 0.1), (W + 0.3, D + 0.3, H + 0.5)), k=0.0)
    box(ct, (0, -D - 0.08, 0.5), (W - 0.1, 0.1, 0.025), 0.01)
    box(ct, (0, -D + 0.02, 0.27), (W - 0.12, 0.02, 0.24), 0.01, label=5)
    for i in range(4):                                              # the split curtain
        x = -W + 0.25 + i * 0.4
        nr.add(RoundBox((x, -D - 0.02, 0.88), (0.17, 0.006, 0.12), 0.004), k=0.0)
        nr.paint(Sphere((x, -D - 0.02, 0.9), 0.06), 5)
    seg(bd, (-W + 0.08, -D - 0.03, 1.01), (W - 0.08, -D - 0.03, 1.01), 0.012, label=7)
    for (x, y) in ((0.25, -D + 0.12), (-0.25, -D + 0.12)):
        pt.add(Cylinder((x, y, 0.6), 0.1, 0.16, rr=0.02), k=0.0)
    for i in range(4):
        x = -0.6 + i * 0.4
        st.add(Cylinder((x, -D - 0.38, 0.42), 0.09, 0.035, rr=0.012), k=0.0, label=5)
        seg(st, (x, -D - 0.38, 0.4), (x, -D - 0.38, 0.0), 0.016)
        st.add(Cylinder((x, -D - 0.38, 0.01), 0.07, 0.02, rr=0.005), k=0.0)
    for sx in (-1, 1):                                              # lanterns either side
        seg(bd, (sx * (W + 0.06), -D - 0.05, 1.0), (sx * (W + 0.06), -D - 0.12, 1.0), 0.008, label=7)
        glows["glow_red"].add(Ellipsoid((sx * (W + 0.06), -D - 0.14, 0.86), (0.08, 0.08, 0.12)), k=0.0)
        seg(bd, (sx * (W + 0.06), -D - 0.14, 0.99), (sx * (W + 0.06), -D - 0.14, 0.97), 0.02, label=7)
    sc = v3((0, -D - 0.32, H + 0.36))
    box(rf, sc + v3((0, 0.02, 0)), (W * 0.82, 0.03, 0.18), 0.02, label=7)
    glyphs(glows["glow_amber"], sc - v3((0, 0.015, 0)), (1, 0, 0), 5, 0.24, seed, r=0.014)
    for (a, b) in (((-W * 0.8, 0.16), (W * 0.8, 0.16)), ((W * 0.8, 0.16), (W * 0.8, -0.16)), ((W * 0.8, -0.16), (-W * 0.8, -0.16)), ((-W * 0.8, -0.16), (-W * 0.8, 0.16))):
        seg(glows["glow_magenta"], sc + v3((a[0], -0.015, a[1])), sc + v3((b[0], -0.015, b[1])), 0.009)
    vc = v3((W + 0.12, -D + 0.2, 0.95))                             # the corner sign
    box(bd, vc, (0.03, 0.12, 0.45), 0.02, label=7)
    seg(bd, (W, -D + 0.2, 1.3), (W + 0.12, -D + 0.2, 1.3), 0.012, label=7)
    _glyph_column(glows["glow_cyan"], vc + v3((0.035, 0, 0.32)), (1, 0, 0), 4, 0.14, seed + 2, r=0.01)
    box(bd, (-W - 0.08, 0.15, 0.75), (0.08, 0.18, 0.13), 0.02, label=7)
    seg(bd, (-W - 0.02, 0.3, 0.62), (-W - 0.02, 0.3, 0.02), 0.015, label=6)
    for f in (bd, st):
        ground_cut(f, -0.02)
    out += [("Shop", bd, fine(0.007, 0.014), "stall"), ("Roof", rf, fine(0.007, 0.014), "street_iron"), ("Counter", ct, fine(0.005, 0.01), "wood"),
            ("Curtain", nr, fine(0.004, 0.008), "canvas"), ("Stools", st, fine(0.004, 0.008), "stall"), ("Pots", pt, fine(0.004, 0.008), "pot_metal")]
    return finish_glows(out, glows)


NOODLE_STEAM = [(0.25, -0.43, 0.75), (-0.25, -0.43, 0.75)]


def monorail_pylon(seed=0):
    """A monorail pylon: a tapering concrete column on its hazard-striped footing, the T-head carrying a length of the
    track beam with a cyan light strip running under it, conduits and a maintenance ladder up the column."""
    out = []
    cl, bm, st = Field("Column"), Field("Beam"), Field("Steel")
    glows = G("glow_cyan", "glow_red")
    H = 3.0
    cl.add(RoundBox((0, 0, 0.08), (0.48, 0.48, 0.1), 0.03), k=0.0)
    cl.paint(Func(lambda P: (np.abs(np.maximum(np.abs(P[:, 0]), np.abs(P[:, 1])) - F32(0.42)) - F32(0.06)).astype(F32), (-0.6, -0.6, -0.1), (0.6, 0.6, 0.3)), 8)
    cl.add(convex([((0, 0, H), (0, 0, 1)), ((0, 0, 0.1), (0, 0, -1)), ((0.3, 0, 0), (1, 0, 0.06)), ((-0.3, 0, 0), (-1, 0, 0.06)),
                   ((0, 0.22, 0), (0, 1, 0.04)), ((0, -0.22, 0), (0, -1, 0.04))], (-0.5, -0.4, 0.0), (0.5, 0.4, H + 0.1)), k=0.02)
    cl.add(convex([((0, 0, H + 0.12), (0, 0, 1)), ((0, 0, H - 0.3), (-0.0, 0, -1)), ((0, 0.5, H), (0, 1, -0.4)), ((0, -0.5, H), (0, -1, -0.4)),
                   ((0.24, 0, 0), (1, 0, 0)), ((-0.24, 0, 0), (-1, 0, 0))], (-0.4, -0.8, H - 0.5), (0.4, 0.8, H + 0.3)), k=0.03)
    bm.add(RoundBox((0, 0, H + 0.38), (2.2, 0.22, 0.26), 0.05), k=0.0)
    bm.add(RoundBox((0, 0, H + 0.66), (2.2, 0.1, 0.03), 0.01), k=0.0, label=7)
    for sy in (-1, 1):
        strip(glows["glow_cyan"], (-2.15, sy * 0.225, H + 0.2), (2.15, sy * 0.225, H + 0.2), 0.025, up=(0, sy, 0))
    for x in (-2.2, 2.2):
        bm.add(RoundBox((x, 0, H + 0.38), (0.02, 0.23, 0.27), 0.01), k=0.0, label=7)
    glows["glow_red"].add(Sphere((0.0, -0.24, H + 0.6), 0.03), k=0.0)
    for sx in (-1, 1):
        seg(st, (0.12 * sx, -0.27, 0.2), (0.12 * sx, -0.27, H - 0.1), 0.012)
    for z in np.arange(0.35, H - 0.1, 0.18):
        seg(st, (-0.12, -0.27, z), (0.12, -0.27, z), 0.009)
    st.add(Chain([v3((0.25, 0.2, H - 0.1)), v3((0.27, 0.22, 1.0)), v3((0.32, 0.3, 0.12))], [0.03] * 3, k=0.03), k=0.0, label=7)
    for f in (cl, st):
        ground_cut(f, -0.02)
    out += [("Column", cl, fine(0.008, 0.016), "concrete"), ("Beam", bm, fine(0.008, 0.016), "graphite"), ("Steel", st, fine(0.004, 0.008), "galv")]
    return finish_glows(out, glows)


def hover_car(seed=0):
    """A parked hover-car (nose toward +X): a sleek pearl body with a smoked canopy, a magenta trim line along its
    flanks, the tail light bar, four hover pods glowing cyan underneath and the glow they throw on the ground."""
    out = []
    bd, cn, pd = Field("Body"), Field("Canopy"), Field("Pods")
    glows = G("glow_cyan", "glow_magenta", "glow_red", "glow_screen")
    zc = 0.4
    bd.add(Ellipsoid((0.0, 0, zc), (0.85, 0.37, 0.13)), k=0.0)
    bd.add(Ellipsoid((-0.35, 0, zc + 0.02), (0.5, 0.39, 0.13)), k=0.08)
    bd.add(RoundCone((0.5, 0, zc - 0.02), (0.92, 0, zc - 0.05), 0.12, 0.04), k=0.08)
    cn.add(Ellipsoid((0.0, 0, zc + 0.14), (0.42, 0.24, 0.15)), k=0.0)
    cn.inter(Plane((0, 0, zc + 0.06), (0, 0, -1)))
    for sy in (-1, 1):
        bd.add(RoundBox((-0.62, sy * 0.33, zc + 0.12), (0.18, 0.08, 0.025), 0.02, R=euler(sy * 0.3, -0.15, 0)), k=0.03)
        glows["glow_magenta"].add(Func(lambda P, sy=sy: np.maximum.reduce([
            np.abs(np.sqrt((P[:, 0] / F32(0.84)) ** 2 + (P[:, 1] / F32(0.355)) ** 2) - F32(1.0)) * F32(0.3) - F32(0.006),
            np.abs(P[:, 2] - F32(zc + 0.02)) - F32(0.01), F32(-sy) * P[:, 1], np.abs(P[:, 0]) - F32(0.7)]).astype(F32),
            (-0.9, -0.45, zc - 0.05), (0.9, 0.45, zc + 0.08)), k=0.0)
    glows["glow_red"].add(RoundBox((-0.84, 0, zc + 0.04), (0.012, 0.26, 0.018), 0.008), k=0.0)
    for sy in (-1, 1):
        glows["glow_screen"].add(RoundBox((0.86, sy * 0.15, zc - 0.04), (0.012, 0.06, 0.015), 0.006), k=0.0)
    for (x, y) in ((0.48, 0.3), (0.48, -0.3), (-0.5, 0.32), (-0.5, -0.32)):
        pd.add(Cylinder((x, y, zc - 0.17), 0.11, 0.1, rr=0.03), k=0.0)
        seg(pd, (x * 0.8, y * 0.6, zc - 0.05), (x, y, zc - 0.15), 0.035)
        glows["glow_cyan"].add(Cylinder((x, y, zc - 0.23), 0.085, 0.02, rr=0.006), k=0.0)
        glows["glow_cyan"].add(Torus((x, y, 0.01), 0.14, 0.008), k=0.0)
    out += [("Body", bd, fine(0.006, 0.012), "hover"), ("Canopy", cn, fine(0.005, 0.01), "dark_glass"), ("Pods", pd, fine(0.005, 0.01), "graphite")]
    return finish_glows(out, glows)


# ------------------------------------------------------------------------------------------------ Neon Grid: no-build zones
def energy_pylon(seed=0):
    """An energy pylon: a graphite mast on a hexagonal hazard-striped base, white insulator discs stacked up it, two
    coil rings glowing violet and a cyan electrode sphere at the top where the arcs crackle, power cables run out to
    junction boxes on the ground."""
    out = []
    bs, ms, ins, jb = Field("Base"), Field("Mast"), Field("Insulators"), Field("Boxes")
    glows = G("glow_violet", "glow_cyan", "glow_red")
    bs.add(hexagon((0, 0), 0.75, 0.16), k=0.0)
    bs.add(hexagon((0, 0), 0.55, 0.3), k=0.02, label=7)
    bs.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(0.66)) - F32(0.06)).astype(F32), (-1, -1, -0.1), (1, 1, 0.3)), 8)
    ms.add(RoundCone((0, 0, 0.3), (0, 0, 2.3), 0.16, 0.08), k=0.0)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        seg(ms, (math.cos(a) * 0.45, math.sin(a) * 0.45, 0.3), (math.cos(a) * 0.12, math.sin(a) * 0.12, 1.2), 0.04)
    for z in np.arange(0.55, 1.05, 0.09):
        ins.add(Cylinder((0, 0, z), 0.2, 0.035, rr=0.015), k=0.0)
    for z in np.arange(1.75, 2.15, 0.08):
        ins.add(Cylinder((0, 0, z), 0.14, 0.03, rr=0.012), k=0.0)
    for z, R in ((1.3, 0.34), (1.58, 0.26)):
        ms.add(Torus((0, 0, z), R, 0.045), k=0.0, label=7)
        for k in range(10):
            a = k * 2 * math.pi / 10
            glows["glow_violet"].add(Torus((math.cos(a) * R, math.sin(a) * R, z), 0.05, 0.016, R=rot_from_axes(z_axis=(-math.sin(a), math.cos(a), 0))), k=0.0)
        seg(ms, (0, 0, z), (R, 0, z), 0.02)
        seg(ms, (0, 0, z), (-R, 0, z), 0.02)
    glows["glow_cyan"].add(Sphere((0, 0, 2.42), 0.14), k=0.0)
    ms.add(Torus((0, 0, 2.32), 0.1, 0.03), k=0.0, label=7)
    glows["glow_red"].add(Sphere((0.3, 0, 0.42), 0.03), k=0.0)
    for k, a in enumerate((0.5, 2.6)):                              # cables out to junction boxes
        d = v3((math.cos(a), math.sin(a), 0))
        q = d * 1.1
        box(jb, q + Z * 0.15, (0.12, 0.09, 0.15), 0.02, R=Rz(a))
        jb.add(Chain([d * 0.5 + Z * 0.2, d * 0.75 + Z * 0.03, q - d * 0.1 + Z * 0.08], [0.03] * 3, k=0.03), k=0.0, label=7)
        glows["glow_violet"].add(RoundBox(q + d * 0.095 + Z * 0.2, (0.006, 0.05, 0.012), 0.004, R=Rz(a)), k=0.0)
    for f in (bs, ms, jb):
        ground_cut(f, -0.02)
    out += [("Base", bs, fine(0.007, 0.014), "graphite"), ("Mast", ms, fine(0.005, 0.01), "graphite"), ("Insulators", ins, fine(0.004, 0.008), "white_tech"),
            ("Boxes", jb, fine(0.005, 0.01), "navy")]
    return finish_glows(out, glows)


# where the pylon's arcs crackle (Blender, prop-local: x, y, z): the coil rings and the electrode
PYLON_SPARKS = [(0.34, 0.0, 1.3), (-0.34, 0.0, 1.3), (0.0, 0.26, 1.58), (0.0, -0.26, 1.58), (0.0, 0.0, 2.42)]


def pit_rim(seed=0, R=1.0):
    """A data pit's rim (the glowing shaft is in the ground): a raised kerb ringed with hazard stripes, segments of cyan
    light round its inner lip, a railing on posts with gaps, triangular warning signs hung on it, a console by it."""
    out = []
    kb, rl, sg, cn = Field("Kerb"), Field("Rail"), Field("Signs"), Field("Console")
    glows = G("glow_cyan", "glow_magenta", "glow_screen")
    kb.add(Func(lambda P: np.maximum(np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(R + 0.06)) - F32(0.1), np.abs(P[:, 2] - F32(0.03)) - F32(0.08)).astype(F32),
                (-R - 0.3, -R - 0.3, -0.1), (R + 0.3, R + 0.3, 0.2)), k=0.0)
    kb.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(R + 0.12)) - F32(0.045)).astype(F32), (-R - 0.3, -R - 0.3, -0.1), (R + 0.3, R + 0.3, 0.2)), 8)
    n = 12
    for k in range(n):                                              # light segments round the lip
        a = 2 * math.pi * k / n
        Rs = rot_from_axes(z_axis=(0, 0, 1))
        glows["glow_cyan"].add(Func(lambda P, a=a: np.maximum.reduce([
            np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(R - 0.035)) - F32(0.014),
            np.abs(P[:, 2] - F32(0.1)) - F32(0.012),
            np.abs(np.arctan2(np.sin(np.arctan2(P[:, 1], P[:, 0]) - F32(a)), np.cos(np.arctan2(P[:, 1], P[:, 0]) - F32(a)))) * F32(R) - F32(0.17)]).astype(F32),
            (-R - 0.1, -R - 0.1, 0.0), (R + 0.1, R + 0.1, 0.2)), k=0.0)
    Rr = R + 0.22
    gaps = (1.2, 4.3)
    pts = []
    for k in range(25):
        a = 2 * math.pi * k / 24
        pts.append(a)
    for a0, a1 in zip(pts[:-1], pts[1:]):
        am = (a0 + a1) / 2
        if any(abs(math.atan2(math.sin(am - g), math.cos(am - g))) < 0.3 for g in gaps):
            continue
        p, q = v3((math.cos(a0) * Rr, math.sin(a0) * Rr, 0)), v3((math.cos(a1) * Rr, math.sin(a1) * Rr, 0))
        for z in (0.55, 0.32):
            seg(rl, p + Z * z, q + Z * z, 0.016 if z > 0.5 else 0.011)
        seg(rl, p - Z * 0.02, p + Z * 0.56, 0.018)
    for k, a in enumerate((0.3, 2.4, 3.6, 5.2)):                    # warning signs on the rail
        d = v3((math.cos(a), math.sin(a), 0))
        c = d * (Rr + 0.02) + Z * 0.44
        tri = [(0.0, 0.12), (0.11, -0.08), (-0.11, -0.08)]
        Rf = np.stack([unit(np.cross(Z, d)), d, Z], axis=1)
        sg.add(convex([(c + Rf @ v3((0, 0.006, 0)), Rf @ v3((0, 1, 0))), (c - Rf @ v3((0, 0.006, 0)), Rf @ v3((0, -1, 0)))] +
                      [(c + Rf @ v3((tri[i][0], 0, tri[i][1])) * 1.0, Rf @ unit(v3((-(tri[(i + 1) % 3][1] - tri[i][1]), 0, tri[(i + 1) % 3][0] - tri[i][0]))))
                       for i in range(3)], c - 0.3, c + 0.3), k=0.0)
        sg.paint(RoundBox(c + Rf @ v3((0, 0, -0.01)), (0.012, 0.03, 0.045), 0.0, R=Rf), 7)
        sg.paint(Sphere(c + Rf @ v3((0, 0, -0.065)), 0.014), 7)
    o = v3((math.cos(1.2) * (Rr + 0.15), math.sin(1.2) * (Rr + 0.15), 0))
    cn.add(RoundBox(o + Z * 0.35, (0.12, 0.1, 0.35), 0.03, R=Rz(1.2)), k=0.0)
    screen(cn, glows["glow_screen"], o + Z * 0.72 - v3((math.cos(1.2), math.sin(1.2), 0)) * 0.06, (-math.cos(1.2), -math.sin(1.2), 0), 0.18, 0.1, tilt=0.6,
           bezel=0.012, depth=0.012)
    glows["glow_magenta"].add(RoundBox(o + Z * 0.5 - v3((math.cos(1.2), math.sin(1.2), 0)) * 0.105, (0.05, 0.05, 0.012), 0.004, R=Rz(1.2)), k=0.0)
    for f in (kb, rl, cn):
        ground_cut(f, -0.02)
    out += [("Kerb", kb, fine(0.006, 0.012), "asphalt"), ("Rail", rl, fine(0.004, 0.008), "hazard_yellow"), ("Signs", sg, fine(0.004, 0.008), "hazard_yellow"),
            ("Console", cn, fine(0.005, 0.01), "graphite")]
    return finish_glows(out, glows)


# ------------------------------------------------------------------------------------------------ the Digital city
LX0, LX1, LY, LH = 1.75, 5.0, 2.2, 2.45          # the lab's ground-floor face (x), its back, half width, roof


def drone(out, o=(0, 0, 0), yaw=0.0, prefix="Drone"):
    """A quadcopter drone sitting on its skids at o: a graphite body with a white shell, four arms to rotors in their
    guard rings, a camera gimbal underneath, violet running lights."""
    bd, rt = Field(prefix), Field(prefix + "Rotors")
    glows = G("glow_violet", "glow_green", "glow_red", prefix=prefix)
    zb = 0.2
    bd.add(RoundBox((0, 0, zb), (0.2, 0.14, 0.06), 0.04), k=0.0, label=7)
    bd.add(Ellipsoid((0.02, 0, zb + 0.05), (0.18, 0.12, 0.05)), k=0.03)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = v3((math.cos(a), math.sin(a), 0))
        h = d * 0.36 + Z * (zb + 0.02)
        seg(bd, d * 0.12 + Z * zb, h, 0.02, 0.016, label=7)
        bd.add(Cylinder(h - Z * 0.01, 0.035, 0.05, rr=0.01), k=0.01, label=7)
        rt.add(Torus(h + Z * 0.02, 0.17, 0.012), k=0.0)
        for j in range(3):
            b = j * 2 * math.pi / 3 + k
            rt.add(RoundBox(h + Z * 0.035, (0.14, 0.018, 0.004), 0.003, R=Rz(b)), k=0.0)
        glows["glow_violet"].add(Sphere(h + d * 0.19 + Z * 0.02, 0.018), k=0.0)
    for sy in (-1, 1):                                              # skids
        seg(bd, (-0.1, sy * 0.1, zb - 0.04), (-0.12, sy * 0.16, 0.02), 0.01, label=7)
        seg(bd, (0.1, sy * 0.1, zb - 0.04), (0.12, sy * 0.16, 0.02), 0.01, label=7)
        seg(bd, (-0.2, sy * 0.16, 0.02), (0.2, sy * 0.16, 0.02), 0.012, label=7)
    bd.add(Sphere((0.12, 0, zb - 0.07), 0.04), k=0.01, label=7)
    glows["glow_green"].add(Sphere((0.16, 0, zb - 0.07), 0.015), k=0.0)
    parts = [(prefix, bd, fine(0.004, 0.008), "white_tech"), (prefix + "Rotors", rt, fine(0.003, 0.006), "graphite")]
    finish_glows(parts, glows)
    place_parts(out, parts, o, Rz(yaw))


def lab_city(seed=0):
    """The Digital Age's city: the tech corps' hardened campus at the end of the road (the road comes in from -X). At
    the gate two guard booths with lit windows, barrier arms raised (white with hazard stripes and violet light strips),
    retracted bollards ringed with violet light, a portal frame over the road carrying the corps' emblem in light,
    floodlights on poles; security walls running off both ways topped with violet light strips, stepping down as they
    die away. Behind the gate a plaza and the lab: a glass-and-steel block whose ground floor glows with racks of
    servers seen through the glass, its upper floor cantilevered out over the entrance on raked steel columns, lit
    offices, a roof of air handlers and an antenna array, the corps' great holo-emblem floating violet over its front
    edge; a drone on its landing pad on one flank, a row of dishes and a lattice mast on the other, cooling units
    behind."""
    out = []
    regions = {}

    def GL(region, key):
        """A glow field local to one part of the campus (one field spanning the whole campus would be meshed on a grid
        of billions of voxels)."""
        if (region, key) not in regions:
            regions[(region, key)] = Field(region + "".join(w.capitalize() for w in key.split("_")[1:]))
        return regions[(region, key)]

    def cstrip(*a, **k):
        strip(*a, t=0.009, **k)
    # ---- the plaza and the road into the gate
    pz = Field("Plaza")
    box(pz, (2.4, 0, 0.0), (3.4, 3.0, 0.035), 0.02)
    pz.paint(RoundBox((0.4, 0, 0.03), (1.4, 0.04, 0.05), 0.0), 9)
    for sy in (-1, 1):
        pz.paint(RoundBox((0.4, sy * 0.86, 0.03), (1.4, 0.03, 0.05), 0.0), 5)
    pz.paint(RoundBox((-0.45, 0, 0.03), (0.06, 0.9, 0.05), 0.0), 9)
    ground_cut(pz, -0.03)
    out.append(("Plaza", pz, fine(0.012, 0.024), "asphalt"))
    for sy in (-1, 1):
        cstrip(GL("Road", "glow_violet"), (-0.9, sy * 0.95, 0.04), (1.6, sy * 0.95, 0.04), 0.035)
    for k in range(5):                                              # retracted bollards, ringed with light
        y = -0.68 + k * 0.34
        GL("Road", "glow_violet").add(Torus((-0.25, y, 0.036), 0.07, 0.014), k=0.0)
    bl = Field("Bollards")
    for k in range(5):
        bl.add(Cylinder((-0.25, -0.68 + k * 0.34, 0.03), 0.055, 0.03, rr=0.01), k=0.0)
    out.append(("Bollards", bl, fine(0.004, 0.008), "steel"))
    # ---- the gate: booths, barrier arms, the portal frame
    gt, bo, ar = Field("Gate"), Field("Booths"), Field("Arms")
    for sy in (-1, 1):
        c = v3((0.25, sy * 1.42, 0.0))
        box(bo, c + Z * 0.45, (0.3, 0.26, 0.45), 0.03)
        box(bo, c + Z * 0.95, (0.38, 0.34, 0.05), 0.02, k=0.0, label=7)
        bo.sub(RoundBox(c + v3((-0.3, 0, 0.55)), (0.03, 0.2, 0.2), 0.01), k=0.0)
        bo.sub(RoundBox(c + v3((0, -sy * 0.26, 0.55)), (0.22, 0.03, 0.2), 0.01), k=0.0)
        GL("Gate", "glow_window_cool").add(RoundBox(c + v3((-0.285, 0, 0.55)), (0.006, 0.2, 0.2), 0.004), k=0.0)
        GL("Gate", "glow_window_cool").add(RoundBox(c + v3((0, -sy * 0.245, 0.55)), (0.22, 0.006, 0.2), 0.004), k=0.0)
        for (a, b) in (((-0.38, -0.34), (0.38, -0.34)), ((-0.38, 0.34), (0.38, 0.34))):
            cstrip(GL("Gate", "glow_violet"), c + v3((a[0], a[1], 0.95)), c + v3((b[0], b[1], 0.95)), 0.025, up=(0, a[1], 0))
        cstrip(GL("Gate", "glow_violet"), c + v3((-0.385, -0.3, 0.95)), c + v3((-0.385, 0.3, 0.95)), 0.025, up=(-1, 0, 0))
        # the barrier arm, raised
        pv = v3((0.0, sy * 1.0, 0.52))
        box(ar, pv - Z * 0.26, (0.09, 0.09, 0.27), 0.02, label=7)
        th = math.radians(72)
        d = v3((0, -sy * math.cos(th), math.sin(th)))
        Ra = np.stack([d, v3((1, 0, 0)), np.cross(d, v3((1, 0, 0)))], axis=1)
        ar.add(RoundBox(pv + d * 0.75, (0.75, 0.035, 0.045), 0.02, R=Ra), k=0.0)
        for k in range(6):
            ar.paint(RoundBox(pv + d * (0.15 + k * 0.24), (0.06, 0.08, 0.08), 0.0, R=Ra), 8)
        ar.add(Cylinder(pv, 0.07, 0.24, rr=0.02, R=RX), k=0.0, label=7)
        cstrip(GL("Gate", "glow_violet"), pv + d * 0.1 + v3((-0.037, 0, 0)), pv + d * 1.45 + v3((-0.037, 0, 0)), 0.02, up=(-1, 0, 0))
        # the portal frame's column, its light
        q = v3((-0.1, sy * 1.85, 0.0))
        box(gt, q + Z * 1.25, (0.13, 0.13, 1.25), 0.02)
        box(gt, q + Z * 0.05, (0.2, 0.2, 0.06), 0.015, k=0.003, label=7)
        cstrip(GL("Gate", "glow_violet"), q + v3((-0.132, 0, 0.2)), q + v3((-0.132, 0, 2.35)), 0.03, up=(-1, 0, 0))
    box(gt, (-0.1, 0, 2.52), (0.16, 2.0, 0.17), 0.03)
    cstrip(GL("Gate", "glow_violet"), (-0.1, -1.7, 2.34), (-0.1, 1.7, 2.34), 0.05, up=(0, 0, -1))
    box(gt, (-0.27, 0, 2.52), (0.02, 0.5, 0.15), 0.01, label=7)
    _hex_emblem(GL("Gate", "glow_violet"), (-0.3, 0, 2.52), (-1, 0, 0), 0.13, t=0.012)
    for f in (gt, bo, ar):
        ground_cut(f, -0.02)
    out += [("Gate", gt, fine(0.008, 0.016), "graphite"), ("Booths", bo, fine(0.006, 0.012), "graphite"), ("Arms", ar, fine(0.005, 0.01), "white_tech")]
    # ---- the security walls running off both ways, dying away
    for sy in (-1, 1):
        wl = Field("Wall%d" % (sy + 1))
        ys = np.arange(2.2, 6.9, 0.95)
        for i, y in enumerate(ys):
            h = 1.0 if i < len(ys) - 2 else (0.72 if i == len(ys) - 2 else 0.45)
            box(wl, (0.0, sy * (y + 0.475), h / 2), (0.1, 0.46, h / 2), 0.015)
            box(wl, (0.0, sy * y, (h + 0.08) / 2), (0.15, 0.06, (h + 0.08) / 2), 0.015, k=0.0, label=7)
            if i < len(ys) - 1:
                cstrip(GL("Wall%d" % (sy + 1), "glow_violet"), (-0.104, sy * (y + 0.06), h - 0.06), (-0.104, sy * (y + 0.89), h - 0.06), 0.022, up=(-1, 0, 0))
        ground_cut(wl, -0.02)
        out.append(("Wall%d" % (sy + 1), wl, fine(0.008, 0.016), "navy"))
    # ---- floodlights on poles at the gate
    fp, fh = Field("FloodPoles"), Field("FloodHeads")
    for sy in (-1, 1):
        b = v3((0.55, sy * 2.35, 0.0))
        fp.add(Cylinder(b + Z * 0.06, 0.09, 0.12, rr=0.02), k=0.0)
        seg(fp, b, b + Z * 2.7, 0.035, 0.025)
        seg(fp, b + v3((0, -0.22, 2.62)), b + v3((0, 0.22, 2.62)), 0.018)
        for dy in (-0.17, 0.17):
            flood_head(fh, GL("Flood", "glow_flood"), b + v3((-0.06, dy, 2.55)), (-0.8, -sy * 0.35, -0.55), s=1.2)
    ground_cut(fp, -0.02)
    out += [("FloodPoles", fp, fine(0.005, 0.01), "galv"), ("FloodHeads", fh, fine(0.004, 0.008), "graphite")]
    # ---- the lab: the ground floor's glass and the racks glowing through it, the cantilevered upper floor, the roof
    cx, z1, z2 = (LX0 + LX1) / 2, 1.22, LH
    lf, cw, fr, rf = Field("LabFloor"), Field("Curtain"), Field("Steel"), Field("RoofSlab")
    gw = Field("LitBands")
    box(lf, (cx + 0.1, 0, 0.07), ((LX1 - LX0) / 2 + 0.15, LY + 0.1, 0.07), 0.02)
    lf.add(RoundBox((cx + 0.1, 0, z1 - 0.06), ((LX1 - LX0) / 2 + 0.15, LY + 0.1, 0.07), 0.02), k=0.0)
    cw.add(RoundBox((cx + 0.1, 0, (0.14 + z1 - 0.13) / 2), ((LX1 - LX0) / 2, LY, (z1 - 0.27) / 2), 0.01), k=0.0)
    for x in np.arange(LX0, LX1 + 0.01, 0.4):                       # mullions round the ground floor
        for sy in (-1, 1):
            box(fr, (x + 0.1, sy * (LY + 0.012), (0.14 + z1 - 0.13) / 2), (0.02, 0.02, (z1 - 0.27) / 2), 0.006)
    for y in np.arange(-LY, LY + 0.01, 0.4):
        box(fr, (LX0 + 0.088, y, (0.14 + z1 - 0.13) / 2), (0.02, 0.02, (z1 - 0.27) / 2), 0.006)
    rng = np.random.default_rng(seed + 4)
    racks = []                                                      # racks seen through the front and side glass
    for y in np.arange(-LY + 0.25, LY - 0.2, 0.4):
        if abs(y) < 0.55:
            continue
        racks.append((v3((LX0 + 0.1 - 0.014, y, 0.0)), v3((-1, 0, 0))))
    for x in np.arange(LX0 + 0.35, LX1 - 0.1, 0.4):
        for sy in (-1, 1):
            racks.append((v3((x + 0.1, sy * (LY + 0.014), 0.0)), v3((0, sy, 0))))
    for (q, n) in racks:
        face = "F" if n[0] < 0 else ("L" if n[1] < 0 else "R")
        s_ = unit(np.cross(Z, n))
        R = np.stack([s_, n, Z], axis=1)
        GL("Rack" + face, "glow_violet").add(RoundBox(q + Z * 0.68, (0.012, 0.005, 0.42), 0.004, R=R), k=0.0)
        for j in range(5):
            if rng.random() < 0.75:
                k = "glow_green" if rng.random() < 0.6 else "glow_cyan"
                GL("Rack" + face, k).add(RoundBox(q + s_ * rng.uniform(0.05, 0.12) * rng.choice([-1, 1]) + Z * (0.38 + j * 0.13), (0.035, 0.005, 0.012), 0.004, R=R), k=0.0)
    # the entrance: lit sliding doors in the front glass
    cw.sub(RoundBox((LX0 + 0.1, 0, 0.55), (0.06, 0.42, 0.45), 0.01), k=0.0)
    GL("Front", "glow_window_cool").add(RoundBox((LX0 + 0.13, 0, 0.55), (0.008, 0.42, 0.45), 0.004), k=0.0)
    for y in (-0.42, 0.0, 0.42):
        box(fr, (LX0 + 0.1, y, 0.55), (0.025, 0.025, 0.46), 0.006, label=7)
    # the upper floor, cantilevered forward over the entrance
    UX0 = LX0 - 0.45
    curtain_box(cw, gw, (UX0 + LX1) / 2, 0, (LX1 - UX0) / 2, LY + 0.15, z1 + 0.02, z2 - 0.05, seed + 1, bands=(), cell=(0.16, 0.3), p=0.2, rc=0.02)
    for i, (fc, (fnx, fny)) in enumerate((("F", (-1, 0)), ("B", (1, 0)), ("L", (0, -1)), ("R", (0, 1)))):
        _lit_strips(GL("Upper" + fc, "glow_window_cool"), (UX0 + LX1) / 2, 0, (LX1 - UX0) / 2, LY + 0.15, z1 + 0.02, z2 - 0.05, seed + 2 + i * 13, p=0.35,
                    faces=((fnx, fny),))
    for sy in (-1, 1):                                              # raked steel columns under the overhang
        seg(fr, (LX0 + 0.12, sy * 1.3, 0.12), (UX0 + 0.08, sy * 1.45, z1), 0.05)
        seg(fr, (LX0 + 0.12, sy * 0.6, 0.12), (UX0 + 0.08, sy * 0.5, z1), 0.04)
    bnd = Field("Bands")
    for z in (z1, z2):
        bnd.add(RoundBox(((UX0 + LX1) / 2, 0, z), ((LX1 - UX0) / 2 + 0.06, LY + 0.21, 0.05), 0.02), k=0.0, label=7)
    out.append(("Bands", bnd, fine(0.01, 0.02), "graphite"))
    for y in np.linspace(-LY - 0.15, LY + 0.15, 9):                  # fins on the upper floor's front
        box(fr, (UX0 - 0.03, y, (z1 + z2) / 2), (0.05, 0.018, (z2 - z1) / 2), 0.006)
    cstrip(GL("Front", "glow_violet"), (UX0 - 0.065, -LY - 0.2, z1 - 0.02), (UX0 - 0.065, LY + 0.2, z1 - 0.02), 0.035, up=(-1, 0, 0))
    cstrip(GL("Front", "glow_violet"), (UX0 - 0.065, -LY - 0.2, z2 + 0.03), (UX0 - 0.065, LY + 0.2, z2 + 0.03), 0.035, up=(-1, 0, 0))
    box(rf, ((UX0 + LX1) / 2, 0, z2 + 0.1), ((LX1 - UX0) / 2 + 0.04, LY + 0.19, 0.06), 0.02)
    rf.sub(RoundBox(((UX0 + LX1) / 2, 0, z2 + 0.2), ((LX1 - UX0) / 2 - 0.06, LY + 0.09, 0.08), 0.01), k=0.0)
    ground_cut(lf, -0.02)
    ground_cut(fr, -0.02)
    out += [("LabFloor", lf, fine(0.01, 0.02), "white_tech"), ("Curtain", cw, fine(0.012, 0.024), "curtain"), ("Steel", fr, fine(0.007, 0.012), "graphite"),
            ("RoofSlab", rf, fine(0.012, 0.024), "white_tech")]
    if any(op[0] == "add" for op in gw.ops):
        out.append(("LitBands", gw, fine(0.008, 0.016), "glow_window_cool"))
    # ---- on the roof: air handlers, the antenna array, the holo-emblem's projector
    rk = Field("RoofKit")
    zr = z2 + 0.13
    for (x, y) in ((3.9, 1.2), (4.5, 1.2), (3.9, 0.4)):
        box(rk, (x, y, zr + 0.16), (0.24, 0.3, 0.16), 0.02)
        rk.sub(Cylinder((x, y, zr + 0.33), 0.17, 0.04), k=0.0)
        rk.add(Cylinder((x, y, zr + 0.3), 0.04, 0.02), k=0.0, label=7)
        for k in range(3):
            a = k * 2 * math.pi / 3 + x
            rk.add(RoundBox((x + math.cos(a) * 0.08, y + math.sin(a) * 0.08, zr + 0.3), (0.07, 0.022, 0.004), 0.003, R=Rz(a + 0.5)), k=0.0, label=7)
    ms = Field("Masts")
    for (x, y, h) in ((4.4, -1.4, 1.9), (3.6, -1.7, 1.3), (4.7, -0.5, 1.1)):
        lattice_mast(ms, (x, y, 0), zr, zr + h, 0.1, 0.05, legs=3, step=0.2, rod=0.009)
        GL("Roof", "glow_red").add(Sphere((x, y, zr + h + 0.04), 0.035), k=0.0)
    for (x, y, az) in ((3.2, -1.3, 2.6), (3.6, -0.6, 3.4)):
        ax = unit(v3((math.cos(az) * 0.6, math.sin(az) * 0.6, 0.8)))
        vt = v3((x, y, zr + 0.45))
        ms.add(dish_fn(vt, ax, 0.3, 0.2, 0.01), k=0.0)
        seg(ms, vt, (x, y, zr), 0.025)
        seg(ms, vt, vt + ax * 0.2, 0.008)
    pj = v3((2.0, 0, zr))
    box(rk, pj + Z * 0.1, (0.18, 0.3, 0.1), 0.03, label=7)
    GL("Emblem", "glow_violet").add(Cylinder(pj + Z * 0.21, 0.09, 0.03, rr=0.01), k=0.0)
    em = pj + Z * 1.15 - v3((0.1, 0, 0))
    GL("Emblem", "glow_violet").add(Torus(em, 0.62, 0.03, R=rot_from_axes(z_axis=(-1, 0, 0.12))), k=0.0)
    _hex_emblem(GL("Emblem", "glow_violet"), em, (-1, 0, 0.12), 0.46, t=0.026)
    out += [("RoofKit", rk, fine(0.008, 0.016), "instrument"), ("Masts", ms, fine(0.005, 0.01), "galv")]
    # ---- the drone on its pad on the +Y flank
    dp = Field("Pad")
    P0 = v3((2.6, 3.75, 0.0))
    dp.add(hexagon(P0, 0.85, 0.2), k=0.0)
    dp.paint(Func(lambda P: (np.abs(np.sqrt((P[:, 0] - F32(P0[0])) ** 2 + (P[:, 1] - F32(P0[1])) ** 2) - F32(0.66)) - F32(0.05)).astype(F32),
                  P0 - 1, P0 + 1), 8)
    dp.paint(Func(lambda P: (np.abs(np.sqrt((P[:, 0] - F32(P0[0])) ** 2 + (P[:, 1] - F32(P0[1])) ** 2) - F32(0.38)) - F32(0.03)).astype(F32),
                  P0 - 1, P0 + 1), 9)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        GL("Pad", "glow_green").add(RoundBox(P0 + v3((math.cos(a) * 0.74, math.sin(a) * 0.74, 0.2)), (0.04, 0.04, 0.012), 0.008), k=0.0)
    ground_cut(dp, -0.02)
    out.append(("Pad", dp, fine(0.008, 0.016), "epoxy"))
    drone(out, P0 + Z * 0.2, 0.4)
    # ---- the dish row and the mast on the -Y flank
    dr = Field("Dishes")
    for i, x in enumerate((1.9, 2.75, 3.6)):
        c = v3((x, -3.75, 0.0))
        dr.add(Cylinder(c + Z * 0.06, 0.25, 0.12, rr=0.03), k=0.0, label=7)
        seg(dr, c, c + Z * 0.7, 0.05)
        ax = unit(v3((-0.55, -0.3, 0.78)))
        vt = c + Z * 0.85 + ax * 0.05
        dr.add(dish_fn(vt, ax, 0.48, 0.32, 0.013), k=0.0)
        dr.add(dish_rim(vt, ax, 0.48, 0.32, 0.018), k=0.004, label=7)
        seg(dr, vt - ax * 0.05, c + Z * 0.68, 0.045)
        for k in range(3):
            a = math.pi / 2 + k * 2 * math.pi / 3
            seg(dr, dish_point(vt, ax, 0.48, 0.32, a, 0.9), vt + ax * 0.32, 0.008)
        dr.add(Sphere(vt + ax * 0.33, 0.035), k=0.004, label=7)
    lm = Field("Lattice")
    lattice_mast(lm, (4.5, -3.9, 0), -0.05, 3.6, 0.26, 0.1, legs=3, step=0.3, rod=0.013)
    GL("Mast", "glow_red").add(Sphere((4.5, -3.9, 3.66), 0.045), k=0.0)
    GL("Mast", "glow_red").add(Sphere((4.62, -3.9, 1.8), 0.035), k=0.0)
    for f in (dr, lm):
        ground_cut(f, -0.02)
    out += [("Dishes", dr, fine(0.006, 0.012), "radome"), ("Lattice", lm, fine(0.006, 0.012), "galv")]
    # ---- cooling units behind the lab
    cu = Field("Coolers")
    for y in (-1.2, 0.0, 1.2):
        box(cu, (5.65, y, 0.42), (0.35, 0.5, 0.42), 0.03)
        for dy in (-0.24, 0.24):
            cu.sub(Cylinder((5.65, y + dy, 0.86), 0.2, 0.04), k=0.0)
            cu.add(Cylinder((5.65, y + dy, 0.82), 0.05, 0.02), k=0.0, label=7)
        for k in range(5):
            cu.sub(RoundBox((5.3, y, 0.15 + k * 0.12), (0.02, 0.4, 0.02), 0.006), k=0.0)
    ground_cut(cu, -0.02)
    out.append(("Coolers", cu, fine(0.008, 0.016), "instrument"))
    for g in regions.values():
        if any(op[0] == "add" for op in g.ops):
            out.append((g.name, g, fine(0.005, 0.008), next(k for (r, k), f in regions.items() if f is g)))
    return out


# game.gd (prop-local, Blender x, y, z; Godot x, z, -y): the floodlights [(position, aim)], the emblem's violet glow
CITY_LIGHTS = []
for _sy in (-1, 1):
    for _dy in (-0.17, 0.17):
        CITY_LIGHTS.append(((0.55 - 0.06, _sy * 2.35 + _dy, 2.55), (-0.8, -_sy * 0.35, -0.55)))
CITY_EMBLEM = (1.9, 0.0, LH + 0.13 + 1.15)                          # the holo-emblem's centre (an OmniLight, violet)
CITY_GATE_GLOW = (-0.1, 0.0, 2.34)                                  # under the portal's light strip


# ------------------------------------------------------------------------------------------------ the kits
# prop name -> (builder, game-mesh triangle budget), as decor_props.KITS. Tuft is direct geometry (decor_build).
def KITS(theme):
    if theme == "lab":
        return {
            "Cart": (lambda: lab_cart(701), 900), "Instruments": (lambda: instrument_rack(702), 1000),
            "Servers_A": (lambda: server_racks(703, 2), 1100), "Servers_B": (lambda: server_racks(704, 3, open_door=True), 1500),
            "Reel": (lambda: cable_reel(705), 600), "Bollards": (lambda: hazard_bollards(706), 500), "Partition": (lambda: glass_partition(707), 300),
            "Fern_A": (lambda: potted_fern(708, 1.0), 900), "Fern_B": (lambda: potted_fern(709, 1.25, square=True), 1000),
            "SpillKit": (lambda: spill_kit(710), 600), "Cylinders": (lambda: gas_cylinders(711), 900), "Cable": (lambda: cable_cover(712), 160),
            "ArmCell": (lambda: arm_cell(713), 3600), "Accelerator": (lambda: accelerator(714), 3600), "ControlRoom": (lambda: control_room(715), 3200),
            "Pod": (lambda: containment_pod(716), 2000), "Gantry": (lambda: gantry(717), 2200),
            "Robot": (lambda: machine_arm(718), 2400), "Centrifuge": (lambda: centrifuge(719), 1800), "Scanner": (lambda: scanner(720), 1800),
            "Tank_A": (lambda: cryo_tanks(721, 0), 2200), "Tank_B": (lambda: cryo_tanks(722, 1), 2200),
        }
    if theme == "satellite":
        return {
            "Dish_A": (lambda: small_dish(731), 700), "Dish_B": (lambda: small_dish(732, tripod=True), 600),
            "Mast": (lambda: antenna_mast(733, 3.0), 800), "Solar": (lambda: solar_panel(734), 500), "Drums": (lambda: cable_drum(735), 700),
            "JBox": (lambda: junction_box(736), 450), "Fence": (lambda: chainlink(737), 700),
            "Scrub_A": (lambda: desert_scrub(738, 0.8), 500), "Scrub_B": (lambda: desert_scrub(739, 0.6), 400),
            "Saguaro": (lambda: saguaro(1.6, ((0.25, 0, 0.5, 0.76),), 740, flowers=False), 800), "Barrel": (lambda: barrel(741), 800),
            "Rock_A": (lambda: sandrock(1.4, 0.5, 742), 500), "Rock_B": (lambda: sandrock(0.9, 0.34, 743, 1), 350),
            "Telescope": (lambda: radio_telescope(744), 5200), "Control": (lambda: control_building(745), 3400),
            "Radar": (lambda: radar_tower(746), 2600), "FuelTank": (lambda: fuel_tank(747), 2000), "Truck": (lambda: utility_truck(748), 1800),
            "BigDish": (lambda: big_dish(749), 2600), "Array": (lambda: solar_array(750), 2600),
        }
    if theme == "neon":
        return {
            "Sign_A": (lambda: neon_sign(751, 0), 700), "Sign_B": (lambda: neon_sign(752, 1), 800), "HoloAd": (lambda: holo_pylon(753), 600),
            "Vending": (lambda: vending_machines(754), 900), "FoodCart": (lambda: food_cart(755), 1300), "CablePole": (lambda: cable_pole(756), 700),
            "Bins": (lambda: trash_bins(757), 600), "Light_M": (lambda: neon_light(758, "glow_magenta"), 300), "Light_C": (lambda: neon_light(759, "glow_cyan"), 300),
            "Puddle": (lambda: puddle_piece(760, 0.7), 120), "Planter": (lambda: glow_planter(761), 900),
            "Tower_A": (lambda: cyber_tower(762, 0), 4800), "Tower_B": (lambda: cyber_tower(763, 1), 4600), "Holo": (lambda: holo_billboard(764), 2200),
            "NoodleBar": (lambda: noodle_bar(765), 3200), "Monorail": (lambda: monorail_pylon(766), 1600), "HoverCar": (lambda: hover_car(767), 1500),
            "Pylon": (lambda: energy_pylon(768), 2200), "PitRim": (lambda: pit_rim(769), 1800),
        }
    if theme == "lab_city":
        return {"City": (lambda: lab_city(791), 22000)}
    raise KeyError(theme)
