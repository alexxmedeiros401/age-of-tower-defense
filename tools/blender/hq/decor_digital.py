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
from decor_medieval import fern
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
        for (a, b) in strokes:
            p = o + side * (a[0] * w) + up * (a[1] * h)
            q = o + side * (b[0] * w) + up * (b[1] * h)
            f.add(RoundCone(p, q, r, r), k=0.0)


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
        mid = v3(((x0 + x1) / 2, -hy - 0.07, min(z0, z1) - 0.14))
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


def cable_reel(seed=0):
    """A cable reel standing on its flanges: plywood discs on an axle, orange cable wound round the drum, its end run
    off across the floor."""
    out = []
    rl, cb = Field("Reel"), Field("Cable")
    R0, Rf, W = 0.13, 0.27, 0.16
    for sy in (-1, 1):
        rl.add(Cylinder((0, sy * W, Rf), Rf, 0.025, rr=0.008, R=RY), k=0.0)
        rl.sub(Cylinder((0, sy * (W + 0.02), Rf), 0.035, 0.03, R=RY), k=0.0)
        for i in range(4):                                          # bolts round the hub
            a = math.pi / 4 + i * math.pi / 2
            rl.add(Cylinder((math.cos(a) * 0.07, sy * (W + 0.014), Rf + math.sin(a) * 0.07), 0.01, 0.01, R=RY), k=0.002, label=6)
    rl.add(Cylinder((0, 0, Rf), R0, 2 * W, R=RY), k=0.0)
    for j in range(4):                                              # turns of cable, the outer layer
        for i in range(7):
            y = -W + 0.035 + i * (2 * W - 0.07) / 6
            cb.add(Torus((0, y, Rf), R0 + 0.025 + j * 0.03, 0.017, R=RY), k=0.004)
    cb.inter(Cylinder((0, 0, Rf), R0 + 0.13, 2 * W - 0.02, R=RY), k=0.0)
    ce = Field("CableEnd")
    ce.add(Chain([v3((0.05, -W + 0.04, Rf + R0 + 0.11)), v3((0.24, -0.12, 0.3)), v3((0.32, -0.15, 0.02)), v3((0.55, -0.25, 0.02)), v3((0.7, -0.15, 0.02))],
                 [0.017] * 5, k=0.03), k=0.0)
    ce.add(RoundBox((0.74, -0.14, 0.03), (0.04, 0.03, 0.025), 0.01), k=0.004, label=7)
    ground_cut(rl, -0.01)
    ground_cut(ce, -0.005)
    out += [("Reel", rl, fine(0.005, 0.01), "plywood"), ("Cable", cb, fine(0.005, 0.01), "cable_orange"), ("CableEnd", ce, fine(0.004, 0.008), "cable_orange")]
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
        pt.add(RoundCone((0, 0, 0.0), (0, 0, 0.3), 0.13, 0.17), k=0.0)
        pt.add(Torus((0, 0, 0.3), 0.17, 0.016), k=0.006)
        pt.sub(Cylinder((0, 0, 0.36), 0.15, 0.12), k=0.004)
        pt.paint(Cylinder((0, 0, 0.06), 0.3, 0.035), 7)
        so.add(Cylinder((0, 0, 0.27), 0.155, 0.03, **wob(12.0, 0.006, seed)), k=0.0)
        top = 0.28
    ground_cut(pt, -0.01)
    out += [("Pot", pt, fine(0.004, 0.008), "white_tech"), ("Soil", so, fine(0.005, 0.01), "soil")]
    place_parts(out, fern(seed, s), (0, 0, top))
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
    raise KeyError(theme)
