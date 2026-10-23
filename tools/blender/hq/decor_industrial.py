"""HQ Industrial Age map props, sculpted as distance fields like decor_props, decor_bronze, decor_iron, decor_classical,
decor_medieval and decor_gunpowder (same conventions: every builder returns its parts [(part name, Field, voxel,
material key)], built at the origin, Z up, ground at z = 0, a landmark's front toward -Y; KITS lists each theme's props
and their game-mesh triangle budgets; decor_build.materials resolves the material keys).

Foundry Row (factory): broken brick chimney stubs, scrap heaps, iron castings, stacks of pig iron, a slag ladle on its
bogie, casks, crates, cable drums, willowherb and dock on the cinders, soot-stained ironstone, a few sooty trees;
landmarks: a brick foundry (a cupola furnace glowing at its tap hole and blazing at its top, a glowing furnace mouth
inside its great arched door, a tall round chimney), a gasholder in its guide frame, a steam hammer shed (the hammer
over a glowing billet), a water tower on a brick base; for the no-build zones a workshop under a sawtooth roof, a steam
hammer with its boiler, a beam engine and a steam crane.
Railyard (railyard): buffer stops, semaphore signals, chaldron coal tubs, stacks of sleepers, crates, casks, gas lamps,
milk churns, weeds, birches; landmarks: a navy-and-brass 0-6-0 tender engine on a siding, an open coal wagon and a goods
van, a water tower on an iron trestle with its water crane, a signal box, an engine shed; for the no-build zones coal
heaps in sleeper bins and a timber coal staithe.
Smog City (smog): gas lamps, pillar boxes, benches, casks, crates, iron railings on a dwarf wall, soot-blackened London
planes, a builder's pile of chimney pots; landmarks: a row of terraced brick houses, a corner pub (its windows lit), a
clock tower, a canal lock, a factory chimney; for the canal basins stone kerbs, iron bollards and a moored narrowboat.
The Industrial city at the end of every Industrial Age road (a great works' entrance: a brick gatehouse with iron gates
under a clock tower, gas lamps and fire baskets either side, the boundary wall running off both ways, sawtooth-roofed
sheds behind, an engine house, tall smokestacks; the corps' navy-and-brass banners) is its own kit ("factory_city",
industrial_city.glb).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Chain, Plane, Func, rot_from_axes, v3, NOISE, euler
import decor_props as DP
from decor_props import vx, wob, convex, rock
from decor_bronze import fine, unit, frame, box_bounds, ground_cut, cut_above, cut_below, place, place_parts, mound, convex_w, walls_box
from decor_iron import Rz, R_xz, at_height, cone, gable, pyramid_roof, post
from decor_medieval import oak
from decor_gunpowder import leaf, mirror, lance, barrels, crates, add_barrel, poly_sdf2, flag

F32 = np.float32
NAVY = (0.07, 0.1, 0.24)                # the Industrial corps' colours (as material colours)
BRASS = (0.8, 0.55, 0.22)
Z = v3((0, 0, 1))


# ------------------------------------------------------------------------------------------------ helpers
def retex(parts, mapping):
    """The same parts with some material keys swapped (an oak as a sooty town tree)."""
    return [(n, f, vxs, mapping.get(m, m)) for (n, f, vxs, m) in parts]


def Rn(nrm):
    """For a wall whose outward normal (horizontal) is nrm: the rotation with local X along the wall, Y = nrm, Z up;
    and those two vectors."""
    n = unit((nrm[0], nrm[1], 0.0))
    s = v3((n[1], -n[0], 0.0))
    return np.stack([s, n, Z], axis=1), s, n


def window(wf, dk, fr, c, nrm, w, h, depth=0.05, arch=False, bars=True, sill=True, head=True, pane=None, dress=6):
    """A window in a wall (field wf) at c (its middle, on the wall's face; outward normal nrm), w wide and h high to the
    springing of its arch (arch: a round head on top): the opening, the glass set back in it (field dk, or `pane` for a
    lit one), glazing bars (fr), a stone sill and a lintel or the arch's dressed stones (label `dress`)."""
    R, s, n = Rn(nrm)
    Rc = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
    c = v3(c)
    hw, hh = w / 2, h / 2
    top = c + Z * hh
    wf.sub(RoundBox(c, (hw, depth, hh), 0.005, R=R), k=0.004)
    if arch:
        wf.sub(Cylinder(top, hw, 2 * depth, rr=0.004, R=Rc), k=0.004)
    pf = pane if pane is not None else dk
    pc = c - n * (depth * 0.7)
    pf.add(RoundBox(pc, (hw + 0.004, 0.012, hh), 0.0, R=R), k=0.0)
    if arch:
        pf.add(Cylinder(top - n * (depth * 0.7), hw + 0.004, 0.024, R=Rc), k=0.0)
    if bars and fr is not None:
        bc = c - n * (depth * 0.45)
        zt = hh + (hw * 0.95 if arch else 0.0)
        fr.add(RoundBox(bc + Z * ((zt - hh) / 2), (0.008, 0.009, (zt + hh) / 2), 0.003, R=R), k=0.0)
        rails = [0.1 * hh] if h < 2.4 * w else [0.35 * hh, -0.35 * hh]
        for zz in rails:
            fr.add(RoundBox(bc + Z * zz, (hw, 0.009, 0.008), 0.003, R=R), k=0.0)
        if arch:
            fr.add(RoundBox(bc + Z * hh, (hw, 0.009, 0.008), 0.003, R=R), k=0.0)
    if sill:
        wf.add(RoundBox(c + n * 0.014 - Z * (hh + 0.016), (hw + 0.03, 0.03, 0.016), 0.004, R=R), k=0.002, label=dress)
    if head and not arch:
        wf.add(RoundBox(c + n * 0.008 + Z * (hh + 0.022), (hw + 0.035, 0.02, 0.022), 0.004, R=R), k=0.002, label=dress)
    elif head:
        tf, Rf = top.astype(F32), R.astype(F32)
        ra = hw + 0.032

        def ring(P):
            Q = (P - tf) @ Rf
            d = np.abs(np.sqrt(Q[:, 0] ** 2 + Q[:, 2] ** 2) - F32(ra)) - F32(0.03)
            return np.maximum.reduce([d, -Q[:, 2] - F32(0.004), np.abs(Q[:, 1]) - F32(0.12)]).astype(F32)
        wf.paint(Func(ring, top - ra - 0.2, top + ra + 0.2), dress)


def doorway(wf, lf, c, nrm, w, h, depth=0.06, arch=False, label=5, panels=True, step=True, dk=None, open_=False):
    """A doorway in a wall (wf) whose foot is at c (on the wall's face): the opening (a round head on top: arch), the
    door leaf set back in it (field lf, its paint label `label`, raised panels), a stone step (label 6); open_: no leaf,
    the dark inside (dk) instead."""
    R, s, n = Rn(nrm)
    Rc = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
    c = v3(c)
    hw, hh = w / 2, h / 2
    mid = c + Z * hh
    wf.sub(RoundBox(mid, (hw, depth, hh + 0.02), 0.005, R=R), k=0.004)
    if arch:
        wf.sub(Cylinder(c + Z * h, hw, 2 * depth, rr=0.004, R=Rc), k=0.004)
    if open_:
        if dk is not None:
            dk.add(RoundBox(mid - n * depth * 0.8, (hw + 0.01, 0.015, hh), 0.0, R=R), k=0.0)
            if arch:
                dk.add(Cylinder(c + Z * h - n * depth * 0.8, hw + 0.01, 0.03, R=Rc), k=0.0)
    else:
        lc = mid - n * (depth * 0.6)
        lf.add(RoundBox(lc, (hw, 0.018, hh), 0.005, R=R), k=0.0, label=label)
        if arch:
            lf.add(Cylinder(c + Z * h - n * (depth * 0.6), hw, 0.036, R=Rc), k=0.0, label=label)
        if panels:
            for sx in (-1, 1):
                for zz in (-0.45, 0.25):
                    lf.add(RoundBox(lc + s * (sx * hw * 0.45) + Z * (hh * zz) + n * 0.016, (hw * 0.32, 0.008, hh * 0.28), 0.004, R=R),
                           k=0.002, label=label)
    if step:
        wf.add(RoundBox(c + n * 0.05 + Z * 0.012, (hw + 0.04, 0.07, 0.03), 0.006, R=R), k=0.002, label=6)


def gear_fn(c, axis, r, w, teeth=12, th=None, spokes=5, hub=0.22):
    """A cast-iron gear wheel (or a flywheel: teeth=0) about `axis` through c: rim, spokes, hub, `w` thick."""
    R = rot_from_axes(z_axis=axis).astype(F32)
    cf = v3(c).astype(F32)
    th = r * 0.12 if th is None else th

    def fn(P):
        Q = (P - cf) @ R
        q = np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2)
        a = np.arctan2(Q[:, 1], Q[:, 0])
        if teeth:
            tooth = np.clip(np.cos(a * F32(teeth)) * F32(2.5), -1, 1) * F32(0.5) + F32(0.5)
            rim_o = q - (F32(r) + F32(th) * tooth)
        else:
            rim_o = q - F32(r)
        rim = np.maximum(rim_o, F32(r * 0.76) - q)
        sa = np.mod(a, F32(2 * math.pi / spokes)) - F32(math.pi / spokes)
        sp = np.maximum(np.abs(np.sin(sa)) * q - F32(r * 0.07), q - F32(r * 0.8))
        flat = np.maximum(np.minimum(rim, sp), np.abs(Q[:, 2]) - F32(w / 2))
        hb = np.maximum(np.maximum(q - F32(r * hub), np.abs(Q[:, 2]) - F32(w * 0.85)), F32(r * 0.07) - q)
        return (np.minimum(flat, hb) * F32(0.85)).astype(F32)
    e = r + th + w + 0.05
    return Func(fn, v3(c) - e, v3(c) + e)


def rwheel_fn(c, axis, r, w=0.045, spokes=12, counter=True):
    """A railway wheel about `axis` through c (the axis pointing out from the engine): a tyre and its flange on the
    inner side, spokes, a hub with its crank boss, a crescent balance weight between the spokes (counter)."""
    R = rot_from_axes(z_axis=axis).astype(F32)
    cf = v3(c).astype(F32)

    def fn(P):
        Q = (P - cf) @ R
        q = np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2)
        a = np.arctan2(Q[:, 1], Q[:, 0])
        z = Q[:, 2]
        tyre = np.maximum(np.maximum(q - F32(r), F32(r * 0.8) - q), np.abs(z) - F32(w / 2))
        flange = np.maximum(np.maximum(q - F32(r * 1.1), F32(r * 0.85) - q), np.abs(z + F32(w * 0.45)) - F32(w * 0.18))
        sa = np.mod(a, F32(2 * math.pi / spokes)) - F32(math.pi / spokes)
        sp = np.maximum.reduce([np.abs(np.sin(sa)) * q - F32(r * 0.045), q - F32(r * 0.85), np.abs(z) - F32(w * 0.32)])
        hb = np.maximum(q - F32(r * 0.24), np.abs(z) - F32(w * 0.7))
        d = np.minimum.reduce([tyre, flange, sp, hb])
        if counter:
            cw = np.maximum.reduce([q - F32(r * 0.82), F32(r * 0.45) - q, np.cos(a - F32(math.pi)) * F32(-1.0) + F32(0.55),
                                    np.abs(z) - F32(w * 0.35)])
            d = np.minimum(d, cw)
        return (d * F32(0.85)).astype(F32)
    e = r * 1.15 + w + 0.05
    return Func(fn, v3(c) - e, v3(c) + e)


def chimney_round(f, c, z0, z1, r0, r1, seed=0, bands=(), cap=True):
    """A round tapering brick chimney stack (into field f) from z0 to z1, iron bands round it (label 7: grime-dark),
    an oversailing cap; its top black with soot (label 5)."""
    cx, cy = float(c[0]), float(c[1])
    f.add(cone((cx, cy), z0, z1, r0, r1, wob(4.0, 0.004, seed)), k=0.0)
    for zb in bands:
        rr = r0 + (r1 - r0) * (zb - z0) / (z1 - z0)
        f.add(Torus((cx, cy, zb), rr + 0.004, 0.012), k=0.004, label=7)
    if cap:
        f.add(Cylinder((cx, cy, z1 - 0.05), r1 + 0.05, 0.1, rr=0.02), k=0.01)
        f.add(Cylinder((cx, cy, z1 - 0.16), r1 + 0.025, 0.06, rr=0.015), k=0.01)
        f.sub(Cylinder((cx, cy, z1 + 0.02), r1 * 0.62, 0.2), k=0.01)
    f.paint(Func(lambda P: (F32(z1 - 0.35) - P[:, 2]).astype(F32), (cx - 1, cy - 1, z1 - 0.6), (cx + 1, cy + 1, z1 + 0.3)), 5)


def chimney_square(f, c, z0, z1, h0, h1, seed=0, cap=True, plinth=None):
    """A square tapering brick chimney (field f) from z0 to z1 (half widths h0 at its foot, h1 at its top), a corbelled
    cap, a plinth of engineering brick (label 8) up to `plinth`, the top black with soot (label 5)."""
    cx, cy = float(c[0]), float(c[1])
    bat = (h0 - h1) / max(z1 - z0, 1e-3)
    f.add(walls_box(cx, cy, h0, h0, z0, z1, batter=bat, amp=0.004, seed=seed), k=0.0)
    if plinth:
        f.add(walls_box(cx, cy, h0 + 0.05, h0 + 0.05, z0, plinth, batter=0.0, amp=0.003, seed=seed + 1), k=0.006, label=8)
        f.add(RoundBox((cx, cy, plinth), (h0 + 0.07, h0 + 0.07, 0.03), 0.01), k=0.004, label=6)
    if cap:
        for k, (dz, e) in enumerate(((0.0, 0.03), (0.06, 0.06), (0.12, 0.045))):
            f.add(RoundBox((cx, cy, z1 - 0.12 + dz), (h1 + e, h1 + e, 0.03), 0.008), k=0.004)
        f.sub(RoundBox((cx, cy, z1 + 0.05), (h1 * 0.55, h1 * 0.55, 0.2), 0.01), k=0.006)
    f.paint(Func(lambda P: (F32(z1 - 0.3) - P[:, 2]).astype(F32), (cx - 1, cy - 1, z1 - 0.5), (cx + 1, cy + 1, z1 + 0.3)), 5)


def chimney_pots(f, c, n=3, half=0.08, z=0.0, seed=0):
    """Chimney pots in a row along X on a stack's top at height z (field f, terracotta; their rims sooty: label 5)."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        x = float(c[0]) + (i - (n - 1) / 2) * half * 2 / max(n, 1) * 1.6
        h = rng.uniform(0.11, 0.17)
        q = v3((x, float(c[1]), z))
        f.add(RoundCone(q, q + Z * h, 0.042, 0.032), k=0.0)
        f.add(Torus(q + Z * (h - 0.004), 0.032, 0.011), k=0.004)
        f.sub(Cylinder(q + Z * (h + 0.02), 0.024, 0.08), k=0.004)
        f.paint(Func(lambda P, q=q, h=h: (F32(q[2] + h - 0.04) - P[:, 2]).astype(F32), q - 0.2, q + 0.4), 5)


def stack(f, pf, c, hx, hy, z0, z1, pots=3, seed=0):
    """A brick chimney stack (field f) on a roof from z0 to z1, a stone cap (label 6), its pots (field pf)."""
    cx, cy = float(c[0]), float(c[1])
    f.add(walls_box(cx, cy, hx, hy, z0, z1, batter=0.0, amp=0.003, seed=seed), k=0.0)
    f.add(RoundBox((cx, cy, z1 - 0.06), (hx + 0.025, hy + 0.025, 0.025), 0.006), k=0.003, label=6)
    f.add(RoundBox((cx, cy, z1 - 0.01), (hx + 0.012, hy + 0.012, 0.02), 0.006), k=0.003)
    f.paint(Func(lambda P: (F32(z1 - 0.12) - P[:, 2]).astype(F32), (cx - 1, cy - 1, z1 - 0.3), (cx + 1, cy + 1, z1 + 0.3)), 5)
    if pots:
        chimney_pots(pf, (cx, cy), pots, hx, z1 - 0.01, seed)


def roof(rf, c, half_len, half_w, z_eave, z_ridge, axis="x", over=0.1, ridge=True, wall=None, wall_in=0.0):
    """A slate roof (field rf): a gabled block overhanging its walls by `over`, the ridge tiles (label 5); `wall`: a
    field to fill the gables of (the walls' own gable ends, inset by wall_in)."""
    cx, cy = float(c[0]), float(c[1])
    s = (z_ridge - z_eave) / half_w
    zr = z_ridge + over * s
    rf.add(gable((cx, cy), half_len + over, half_w + over, z_eave - 0.03, zr, axis=axis), k=0.0)
    if ridge:
        L = half_len + over
        hx, hy = (L, 0.035) if axis == "x" else (0.035, L)
        rf.add(RoundBox((cx, cy, zr + 0.005), (hx, hy, 0.03), 0.02), k=0.006, label=5)
    if wall is not None:
        wall.add(gable((cx, cy), half_len - wall_in, half_w - wall_in, z_eave - 0.05, z_ridge - 0.04, axis=axis), k=0.0)
    return zr


def hipped(rf, c, hx, hy, z_eave, z_top, over=0.1, ridge=True):
    """A hipped slate roof over a box (half sizes hx >= hy), its ridge along X (label 5 on the ridge and hips)."""
    cx, cy = float(c[0]), float(c[1])
    hx, hy = hx + over, hy + over
    s = (z_top - z_eave) / hy
    planes = [((cx, cy + hy, z_eave), (0, 1, 1 / s)), ((cx, cy - hy, z_eave), (0, -1, 1 / s)),
              ((cx + hx, cy, z_eave), (1, 0, 1 / s)), ((cx - hx, cy, z_eave), (-1, 0, 1 / s)), ((cx, cy, z_eave - 0.03), (0, 0, -1))]
    rf.add(convex(planes, (cx - hx - 0.1, cy - hy - 0.1, z_eave - 0.1), (cx + hx + 0.1, cy + hy + 0.1, z_top + 0.1)), k=0.0)
    if ridge and hx > hy + 0.02:
        rf.add(RoundBox((cx, cy, z_top - 0.005), (hx - hy, 0.03, 0.025), 0.02), k=0.006, label=5)


def sawtooth(rf, gl, fr, x0, x1, y0, y1, z0, n, h, glaze=-1):
    """A sawtooth roof over the box x0..x1, y0..y1 from z0: n teeth across Y, their ridges along X, each a long slate
    slope (rf) and a steep glazed face (gl: glass, fr: its bars) facing -Y (glaze=-1) or +Y."""
    dy = (y1 - y0) / n
    for i in range(n):
        ya, yb = y0 + i * dy, y0 + (i + 1) * dy
        yg, ys = (ya, yb) if glaze < 0 else (yb, ya)            # the glazed face's foot and the slope's foot
        sg = -1.0 if glaze < 0 else 1.0
        nrm_slope = v3((0.0, -sg * h, dy))
        planes = [((0, ys, z0), nrm_slope), ((0, yg, z0), (0, sg, 0.12)), ((0, 0, z0 - 0.02), (0, 0, -1)),
                  ((x1, 0, 0), (1, 0, 0)), ((x0, 0, 0), (-1, 0, 0))]
        rf.add(convex(planes, (x0 - 0.2, min(ya, yb) - 0.2, z0 - 0.1), (x1 + 0.2, max(ya, yb) + 0.2, z0 + h + 0.15)), k=0.0)
        # the glazing on the steep face, slightly proud of it
        gp = v3(((x0 + x1) / 2, yg + sg * 0.012 - sg * 0.12 * h * 0.5, z0 + h * 0.52))
        R = np.stack([v3((1, 0, 0)), unit((0, sg, 0.12)), unit(np.cross((1, 0, 0), (0, sg, 0.12)))], axis=1)
        if R[2, 2] < 0:
            R[:, 2] = -R[:, 2]
        gl.add(RoundBox(gp, ((x1 - x0) / 2 - 0.06, 0.008, h * 0.4), 0.0, R=R), k=0.0)
        for x in np.arange(x0 + 0.1, x1 - 0.05, 0.16):
            fr.add(RoundBox(v3((x, gp[1], gp[2])) + R @ v3((0, 0.01, 0)), (0.009, 0.01, h * 0.42), 0.003, R=R), k=0.0)
        fr.add(RoundBox(gp + R @ v3((0, 0.01, h * 0.41)), ((x1 - x0) / 2 - 0.05, 0.012, 0.012), 0.004, R=R), k=0.0)
        fr.add(RoundBox(gp + R @ v3((0, 0.01, -h * 0.41)), ((x1 - x0) / 2 - 0.05, 0.012, 0.012), 0.004, R=R), k=0.0)


def rail_track(out, x0, x1, y=0.0, gauge=0.34, seed=0, bed=True, spacing=0.2, name="Track"):
    """A length of track along X from x0 to x1: two rails on creosoted sleepers half sunk in a bed of ballast."""
    rl, sl = Field(name + "Rails"), Field(name + "Sleepers")
    rng = np.random.default_rng(seed)
    L = (x1 - x0) / 2
    xc = (x0 + x1) / 2
    for sy in (-1, 1):
        yy = y + sy * gauge / 2
        rl.add(RoundBox((xc, yy, 0.062), (L, 0.016, 0.014), 0.008), k=0.0)
        rl.add(RoundBox((xc, yy, 0.044), (L, 0.007, 0.012), 0.003), k=0.004)
        rl.add(RoundBox((xc, yy, 0.033), (L, 0.022, 0.006), 0.003), k=0.004)
    for x in np.arange(x0 + spacing / 2, x1, spacing):
        sl.add(RoundBox((x + rng.uniform(-0.01, 0.01), y, 0.015), (0.045, gauge / 2 + 0.11, 0.018), 0.006, R=Rz(rng.uniform(-0.03, 0.03)),
                        **wob(20.0, 0.002, seed + int(x * 50))), k=0.0, label=10)
    ground_cut(sl, -0.02)
    out += [(name + "Rails", rl, fine(0.004, 0.008), "rail"), (name + "Sleepers", sl, fine(0.005, 0.01), "sleeper")]
    if bed:
        bd = Field(name + "Bed")
        bd.add(convex_w([((xc, y, 0.03), (0, 0, 1)), ((xc, y, -0.05), (0, 0, -1)), ((xc, y + gauge / 2 + 0.2, 0), (0, 1, 0.9)),
                         ((xc, y - gauge / 2 - 0.2, 0), (0, -1, 0.9)), ((x1 + 0.05, y, 0), (1, 0, 0.9)), ((x0 - 0.05, y, 0), (-1, 0, 0.9))],
                        (x0 - 0.3, y - gauge - 0.5, -0.1), (x1 + 0.3, y + gauge + 0.5, 0.1), 0.006, 12.0, seed), k=0.0)
        ground_cut(bd, -0.02)
        out.append((name + "Bed", bd, fine(0.012, 0.024), "ballast"))
    return out


def gas_lamp(out, c=(0, 0, 0), h=1.45, seed=0, R=None, name="", standard=True):
    """A gas lamp standard: a fluted cast-iron column on its base, a collar, the ladder bar, a square lantern of four
    glass panes (lit: glow_lamp) under a ventilated cap and finial (standard=False: the lantern alone, its foot at c,
    for a bracket)."""
    c = v3(c)
    f, g = Field(name + "Lamp"), Field(name + "LampGlass")
    if not standard:
        h = 0.2
    flutes = dict(disp=lambda P: (F32(0.003) * np.cos(np.arctan2(P[:, 1] - F32(c[1]), P[:, 0] - F32(c[0])) * F32(8))).astype(F32), disp_amp=0.004)
    if standard:
        f.add(Cylinder(c + Z * 0.06, 0.075, 0.12, rr=0.02), k=0.0, label=7)
        f.add(RoundCone(c + Z * 0.1, c + Z * 0.26, 0.06, 0.045), k=0.02, label=7)
        f.add(RoundCone(c + Z * 0.25, c + Z * (h - 0.25), 0.036, 0.026, **flutes), k=0.01)
        f.add(Torus(c + Z * 0.32, 0.042, 0.012), k=0.006)
        f.add(Torus(c + Z * (h - 0.28), 0.032, 0.011), k=0.006)
        zb = h - 0.31
        f.add(RoundCone(c + Z * zb + v3((-0.13, 0, 0)), c + Z * zb + v3((0.13, 0, 0)), 0.011, 0.011), k=0.004)
        for sx in (-1, 1):
            f.add(Sphere(c + Z * zb + v3((sx * 0.135, 0, 0)), 0.018), k=0.004)
        f.add(RoundCone(c + Z * (h - 0.26), c + Z * (h - 0.2), 0.03, 0.05), k=0.006)
    else:
        f.add(RoundCone(c - Z * 0.02, c + Z * 0.01, 0.02, 0.045), k=0.0)
    zl0, zl1 = h - 0.2, h - 0.02
    for sx in (-1, 1):                                              # the lantern's corner bars
        for sy in (-1, 1):
            f.add(RoundCone(c + v3((sx * 0.05, sy * 0.05, zl0)), c + v3((sx * 0.08, sy * 0.08, zl1)), 0.009, 0.009), k=0.003)
    f.add(RoundBox(c + Z * zl0, (0.058, 0.058, 0.012), 0.006), k=0.004)
    f.add(pyramid_roof((c[0], c[1]), 0.1, zl1, zl1 + 0.09), k=0.004)
    f.add(Sphere(c + Z * (zl1 + 0.11), 0.022), k=0.006)
    f.add(RoundCone(c + Z * (zl1 + 0.12), c + Z * (zl1 + 0.17), 0.012, 0.004), k=0.004)
    g.add(convex([((c[0], c[1], zl1 - 0.005), (0, 0, 1)), ((c[0], c[1], zl0), (0, 0, -1)),
                  ((c[0] + 0.052, c[1], zl0), (1, 0, -0.16)), ((c[0] - 0.052, c[1], zl0), (-1, 0, -0.16)),
                  ((c[0], c[1] + 0.052, zl0), (0, 1, -0.16)), ((c[0], c[1] - 0.052, zl0), (0, -1, -0.16))],
                 c + v3((-0.15, -0.15, zl0 - 0.05)), c + v3((0.15, 0.15, zl1 + 0.05))), k=0.0)
    parts = [(name + "Lamp", f, fine(0.004, 0.008), "lamp_iron"), (name + "LampGlass", g, fine(0.004, 0.008), "glow_lamp")]
    if R is not None:
        place_parts(out, parts, (0, 0, 0), R)
    else:
        out += parts
    return out


# ------------------------------------------------------------------------------------------------ Foundry Row: scatter
def chimney_stub(seed=0, square=True):
    """A broken chimney: a square brick stack on its plinth of blue engineering brick, snapped off ragged and sooty
    (square), or the stump of a round stack in iron bands (not square); fallen bricks and rubble round its foot, weeds
    on the rubble."""
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Brick")
    if square:
        H = 1.25
        chimney_square(f, (0, 0), -0.05, H + 0.6, 0.2, 0.16, seed, cap=False, plinth=0.32)
        cut_above(f, (0, 0, H), (0.35, -0.2, 1.0), (0.5, 0.5, 0.8), disp=lambda P: (NOISE.fbm(P * F32(9.0) + F32(seed), 2) * F32(0.09)).astype(F32), amp=0.1)
        f.sub(RoundBox((0, 0, H + 0.2), (0.11, 0.11, 0.6), 0.01), k=0.006)
        f.paint(Func(lambda P: (F32(H - 0.3) - P[:, 2]).astype(F32), (-1, -1, H - 0.5), (1, 1, H + 0.5)), 5)
    else:
        H = 0.95
        chimney_round(f, (0, 0), -0.05, H + 0.8, 0.27, 0.2, seed, bands=(0.35, 0.7), cap=False)
        f.add(walls_box(0, 0, 0.32, 0.32, -0.05, 0.25, batter=0.0, amp=0.003, seed=seed), k=0.01, label=8)
        f.add(RoundBox((0, 0, 0.25), (0.34, 0.34, 0.03), 0.01), k=0.004, label=6)
        cut_above(f, (0, 0, H), (-0.3, 0.25, 1.0), (0.5, 0.5, 0.9), disp=lambda P: (NOISE.fbm(P * F32(8.0) + F32(seed), 2) * F32(0.08)).astype(F32), amp=0.1)
        f.sub(Cylinder((0, 0, H + 0.2), 0.13, 1.0), k=0.006)
        f.paint(Func(lambda P: (F32(H - 0.25) - P[:, 2]).astype(F32), (-1, -1, H - 0.5), (1, 1, H + 0.5)), 5)
    for k in range(9):                                              # fallen bricks
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.38, 0.62)
        f.add(RoundBox((math.cos(a) * rr, math.sin(a) * rr, 0.02), (0.06, 0.03, 0.022), 0.006,
                       R=euler(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0, 3))), k=0.0)
    ground_cut(f)
    out.append(("Brick", f, fine(0.006, 0.012), "brick"))
    rb = Field("Rubble")
    a0 = rng.uniform(0, 2 * math.pi)
    for k in range(3):
        a = a0 + k * 0.5
        rb.add(Ellipsoid((math.cos(a) * 0.38, math.sin(a) * 0.38, 0.0), (0.24, 0.18, 0.1), **wob(10.0, 0.02, seed + k)), k=0.05)
    ground_cut(rb, -0.01)
    out.append(("Rubble", rb, fine(0.008, 0.016), "turf"))
    wd = weeds(seed + 3, s=0.55, n=4)
    place_parts(out, wd, (math.cos(a0 + 0.5) * 0.38, math.sin(a0 + 0.5) * 0.38, 0.04))
    return out


def scrap_heap(seed=0):
    """A heap of scrap iron: rusty plates, pipes and a girder end, a broken gear and a cart wheel, a length of chain, on
    a mound of rust and cinders."""
    rng = np.random.default_rng(seed)
    f = Field("Scrap")
    f.add(Ellipsoid((0, 0, 0.0), (0.62, 0.48, 0.32), **wob(5.0, 0.04, seed)), k=0.0)
    for k in range(7):                                              # plates sticking out at angles
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.15, 0.42)
        c = v3((math.cos(a) * rr, math.sin(a) * rr, 0.22 - rr * 0.25))
        f.add(RoundBox(c, (rng.uniform(0.12, 0.2), rng.uniform(0.08, 0.14), 0.01), 0.005,
                       R=euler(rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9), a), **wob(14.0, 0.006, seed + k)), k=0.01)
    for k in range(3):                                              # pipes
        a = rng.uniform(0, 2 * math.pi)
        p0 = v3((math.cos(a) * 0.15, math.sin(a) * 0.15, 0.25))
        p1 = p0 + v3((math.cos(a + 0.4) * 0.5, math.sin(a + 0.4) * 0.5, rng.uniform(-0.2, 0.05)))
        f.add(RoundCone(p0, p1, 0.035, 0.035), k=0.01)
        f.sub(Sphere(p1, 0.024), k=0.004)
    gc = v3((0.12, -0.18, 0.36))                                     # a broken gear, leaning
    f.add(gear_fn(gc, (0.3, -0.8, 0.5), 0.22, 0.045, teeth=14, spokes=4), k=0.01)
    f.sub(Ellipsoid(gc + v3((0.18, -0.05, 0.12)), (0.12, 0.12, 0.12)), k=0.01)
    a, b = v3((-0.5, 0.1, 0.06)), v3((0.0, 0.32, 0.42))             # a girder's end
    t, bb, n = frame(b - a)
    R = np.stack([t, bb, n], axis=1)
    m = (a + b) / 2
    L = float(np.linalg.norm(b - a)) / 2
    f.add(RoundBox(m, (L, 0.008, 0.07), 0.004, R=R), k=0.006)
    for sz in (-1, 1):
        f.add(RoundBox(m + n * (sz * 0.07), (L, 0.05, 0.009), 0.004, R=R), k=0.006)
    for k in range(7):                                              # chain trailing off it
        q = v3((0.45 + 0.07 * k, 0.25 + 0.03 * math.sin(k), 0.025))
        Rk = rot_from_axes(z_axis=(0, 1, 0)) if k % 2 == 0 else rot_from_axes(z_axis=(0, 0, 1))
        f.add(Torus(q, 0.035, 0.011, R=Rk), k=0.004)
    ground_cut(f)
    out = [("Scrap", f, fine(0.006, 0.012), "rust_iron")]
    wh = Field("Wheel")                                             # a broken cart wheel against it
    wc = v3((-0.38, -0.28, 0.28))
    ax = unit((0.5, -0.6, 0.62))
    Rw = rot_from_axes(z_axis=ax)
    wh.add(Torus(wc, 0.26, 0.022, R=Rw), k=0.0, label=10)
    wh.add(Torus(wc, 0.28, 0.012, R=Rw), k=0.003, label=6)
    wh.add(Cylinder(wc, 0.05, 0.09, rr=0.012, R=Rw), k=0.004, label=10)
    for k in range(8):
        if k in (2, 3):
            continue
        aa = 2 * math.pi * k / 8
        d = Rw @ v3((math.cos(aa), math.sin(aa), 0.0))
        wh.add(RoundCone(wc + d * 0.05, wc + d * 0.25, 0.012, 0.01), k=0.003, label=11)
    ground_cut(wh)
    out.append(("Wheel", wh, fine(0.005, 0.01), "timber"))
    return out


def castings(seed=0):
    """Fresh iron castings laid out on timber skids: a big gear wheel lying flat, a fluted column on its side, a pipe
    elbow and a short flanged pipe, a cylinder block; the sand of the mould still clinging orange in places."""
    rng = np.random.default_rng(seed)
    out = []
    f, sk = Field("Iron"), Field("Skids")
    for (x, y, L, yaw) in ((-0.2, 0.0, 0.62, 0.0), (-0.2, 0.42, 0.62, 0.0), (0.55, -0.1, 0.45, 1.57)):
        sk.add(RoundBox((x, y, 0.04), (L, 0.05, 0.04), 0.01, R=Rz(yaw), **wob(12.0, 0.003, seed + int(x * 10))), k=0.0, label=10)
    ground_cut(sk)
    f.add(gear_fn((-0.25, 0.2, 0.13), (0, 0, 1), 0.38, 0.07, teeth=22, spokes=6), k=0.0)
    cc = v3((0.42, -0.05, 0.2))                                       # a column lying across the third skid
    Rc = rot_from_axes(z_axis=(0, 1, 0))
    fl = dict(disp=lambda P: (F32(0.006) * np.cos(np.arctan2(P[:, 2] - F32(0.2), P[:, 0] - F32(0.42)) * F32(10))).astype(F32), disp_amp=0.007)
    f.add(RoundCone(cc + v3((0, -0.55, 0)), cc + v3((0, 0.42, 0)), 0.1, 0.085, **fl), k=0.0)
    f.add(RoundBox(cc + v3((0, -0.6, 0)), (0.15, 0.04, 0.15), 0.01), k=0.01)
    f.add(Cylinder(cc + v3((0, 0.46, 0)), 0.13, 0.06, rr=0.012, R=Rc), k=0.01)
    pe = v3((-0.6, -0.42, 0.11))                                      # a pipe elbow (a quarter torus with flanges)
    Re = rot_from_axes(z_axis=(0, 0, 1))
    f.add(Func(lambda P: np.maximum(np.sqrt((np.sqrt((P[:, 0] - F32(pe[0])) ** 2 + (P[:, 1] - F32(pe[1])) ** 2) - F32(0.2)) ** 2
                                            + (P[:, 2] - F32(pe[2])) ** 2) - F32(0.09),
                                    np.maximum(F32(pe[0]) - P[:, 0], F32(pe[1]) - P[:, 1])).astype(F32),
               pe + v3((-0.05, -0.05, -0.15)), pe + v3((0.35, 0.35, 0.15))), k=0.0)
    for q, ax in ((pe + v3((0.2, 0.0, 0.0)), (0, 1, 0)), (pe + v3((0.0, 0.2, 0.0)), (1, 0, 0))):
        f.add(Cylinder(q, 0.12, 0.03, rr=0.008, R=rot_from_axes(z_axis=ax)), k=0.006)
    f.sub(Cylinder(pe + v3((0.2, 0.0, 0.0)), 0.065, 0.1, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.004)
    f.sub(Cylinder(pe + v3((0.0, 0.2, 0.0)), 0.065, 0.1, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004)
    bc = v3((0.05, -0.5, 0.13))                                       # a cylinder block
    f.add(RoundBox(bc, (0.16, 0.12, 0.12), 0.02), k=0.0)
    f.add(Cylinder(bc + v3((0, 0, 0.0)), 0.13, 0.3, rr=0.02, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.02)
    for sx in (-1, 1):
        f.add(Cylinder(bc + v3((sx * 0.16, 0, 0)), 0.15, 0.03, rr=0.008, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.006)
    f.sub(Cylinder(bc + v3((0.18, 0, 0)), 0.09, 0.06, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.006)
    f.paint(Func(lambda P: (NOISE.fbm(P * F32(5.0) + F32(seed), 2) * F32(1.0) + F32(0.12)).astype(F32), (-1.2, -1.2, -0.1), (1.2, 1.2, 0.6)), 5)
    ground_cut(f)
    out += [("Iron", f, fine(0.005, 0.01), "cast_iron"), ("Skids", sk, fine(0.006, 0.012), "timber")]
    return out


def ingots(seed=0):
    """Pig iron: two stacks of ingots laid crosswise in alternate courses on timber bearers, a few loose ones."""
    rng = np.random.default_rng(seed)
    f, wd = Field("Pigs"), Field("Bearers")
    for (cx, cy, n_layers, yaw) in ((-0.22, 0.0, 6, 0.1), (0.3, 0.08, 4, -0.15)):
        Rs = Rz(yaw)
        for sy in (-1, 1):
            wd.add(RoundBox(v3((cx, cy, 0.03)) + Rs @ v3((0, sy * 0.13, 0)), (0.2, 0.035, 0.03), 0.008, R=Rs), k=0.0, label=10)
        for L in range(n_layers):
            z = 0.075 + L * 0.058
            rot = (L % 2) * math.pi / 2
            for i in range(4):
                o = (i - 1.5) * 0.085
                d = v3((0, o, 0)) if L % 2 == 0 else v3((o, 0, 0))
                c = v3((cx, cy, z)) + Rs @ d + v3((rng.uniform(-0.008, 0.008), rng.uniform(-0.008, 0.008), 0))
                f.add(RoundBox(c, (0.17, 0.034, 0.026), 0.009, R=Rs @ Rz(rot + rng.uniform(-0.03, 0.03))), k=0.0)
    for k in range(3):
        a = rng.uniform(0, 2 * math.pi)
        f.add(RoundBox((0.05 + math.cos(a) * 0.45, -0.3 + math.sin(a) * 0.12, 0.024), (0.17, 0.034, 0.026), 0.009, R=Rz(rng.uniform(0, 3))), k=0.0)
    ground_cut(f)
    ground_cut(wd)
    return [("Pigs", f, fine(0.005, 0.01), "pig_iron"), ("Bearers", wd, fine(0.005, 0.01), "timber")]


def slag_cart(seed=0):
    """A slag ladle on its bogie on a short length of track: a cast-iron bowl hung on trunnions in a frame over four
    wheels, filled with slag crusted black over a glowing heart."""
    out = []
    rail_track(out, -0.75, 0.75, 0.0, 0.34, seed, spacing=0.21)
    fr, bw, sl, gw = Field("Frame"), Field("Bowl"), Field("Slag"), Field("Glow")
    zr = 0.08
    for sx in (-1, 1):
        for sy in (-1, 1):
            fr.add(rwheel_fn((sx * 0.3, sy * 0.21, zr + 0.13), (0, sy, 0), 0.13, 0.04, spokes=8, counter=False), k=0.0)
        fr.add(RoundCone((sx * 0.3, -0.26, zr + 0.13), (sx * 0.3, 0.26, zr + 0.13), 0.02, 0.02), k=0.004)
    for sy in (-1, 1):
        fr.add(RoundBox((0, sy * 0.28, zr + 0.22), (0.46, 0.022, 0.05), 0.01), k=0.004)
        fr.add(RoundBox((0, sy * 0.28, zr + 0.42), (0.06, 0.03, 0.18), 0.01), k=0.006)
        fr.add(Cylinder((0, sy * 0.3, zr + 0.56), 0.05, 0.06, rr=0.01, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.006, label=7)
    fr.add(RoundBox((0, 0, zr + 0.24), (0.48, 0.3, 0.025), 0.01), k=0.004)
    for sx in (-1, 1):
        fr.add(RoundBox((sx * 0.5, 0, zr + 0.24), (0.03, 0.22, 0.05), 0.01), k=0.004, label=5)
        for sy in (-1, 1):
            fr.add(Cylinder((sx * 0.55, sy * 0.15, zr + 0.24), 0.04, 0.06, rr=0.01, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004, label=7)
    ground_cut(fr)
    out.append(("Frame", fr, fine(0.005, 0.01), "machine"))
    zb = zr + 0.28
    bw.add(cone((0, 0), zb, zb + 0.5, 0.2, 0.36), k=0.0)
    bw.sub(cone((0, 0), zb + 0.06, zb + 0.6, 0.15, 0.32), k=0.01)
    bw.add(Torus((0, 0, zb + 0.5), 0.36, 0.03), k=0.01)
    for sy in (-1, 1):
        bw.add(Cylinder((0, sy * 0.32, zb + 0.29), 0.05, 0.08, rr=0.01, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.01)
    bw.add(RoundCone((0.3, 0, zb + 0.48), (0.46, 0, zb + 0.5), 0.05, 0.03), k=0.02)              # its lip
    bw.paint(Func(lambda P: (F32(zb + 0.38) - P[:, 2]).astype(F32), (-1, -1, zb - 0.1), (1, 1, zb + 0.7)), 5)
    out.append(("Bowl", bw, fine(0.006, 0.012), "rust_iron"))
    sl.add(Ellipsoid((0, 0, zb + 0.46), (0.33, 0.33, 0.07), **wob(12.0, 0.015, seed)), k=0.0)
    sl.sub(Ellipsoid((0.05, -0.04, zb + 0.53), (0.14, 0.11, 0.06), **wob(14.0, 0.012, seed + 1)), k=0.02)
    sl.inter(Plane((0, 0, zb + 0.52), (0, 0, 1)))
    out.append(("Slag", sl, fine(0.005, 0.01), "slag"))
    gw.add(Ellipsoid((0.05, -0.04, zb + 0.47), (0.15, 0.12, 0.04), **wob(16.0, 0.01, seed + 2)), k=0.0)
    out.append(("Glow", gw, fine(0.005, 0.01), "glow_fire"))
    return out


def cable_drum(seed=0):
    """A wooden cable drum standing on its rim, wound with steel wire rope, the rope's end trailing; a smaller empty
    drum lying on its flange beside it."""
    out = []
    wd, wr = Field("Drum"), Field("Wire")
    c = v3((0, 0, 0.42))
    Ry = rot_from_axes(z_axis=(0, 1, 0))
    for sy in (-1, 1):
        wd.add(Cylinder(c + v3((0, sy * 0.24, 0)), 0.42, 0.045, rr=0.01, R=Ry), k=0.0, label=10)
        for k in range(6):
            a = 2 * math.pi * k / 6
            d = v3((math.cos(a), 0, math.sin(a)))
            wd.add(RoundBox(c + v3((0, sy * 0.27, 0)) + d * 0.22, (0.035, 0.012, 0.2), 0.005, R=rot_from_axes(z_axis=d, y_axis=(0, 1, 0))),
                   k=0.002, label=11)
        wd.add(Cylinder(c + v3((0, sy * 0.275, 0)), 0.07, 0.03, rr=0.008, R=Ry), k=0.004, label=6)
    wd.sub(Cylinder(c, 0.045, 0.7, R=Ry), k=0.004)
    wd.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + (P[:, 2] - F32(0.42)) ** 2) - F32(0.33)) - F32(0.025)).astype(F32),
                  (-0.5, -0.4, -0.1), (0.5, 0.4, 0.9)), 5)
    ground_cut(wd)
    cf = c.astype(F32)

    def wound(P):
        Q = P - cf
        q = np.sqrt(Q[:, 0] ** 2 + Q[:, 2] ** 2)
        a = np.arctan2(Q[:, 2], Q[:, 0])
        groove = F32(0.006) * np.abs(np.sin((Q[:, 1] + a * F32(0.022 / (2 * math.pi))) * F32(math.pi / 0.022)))
        return (np.maximum(q - F32(0.31) + groove, np.abs(Q[:, 1]) - F32(0.215)) * F32(0.9)).astype(F32)
    wr.add(Func(wound, c - v3((0.36, 0.25, 0.36)), c + v3((0.36, 0.25, 0.36))), k=0.0)
    wr.add(Chain([v3((-0.3, 0.1, 0.2)), v3((-0.42, 0.14, 0.02)), v3((-0.6, 0.3, 0.02)), v3((-0.85, 0.24, 0.02))], [0.016] * 4, k=0.004), k=0.004)
    ground_cut(wr, -0.005)
    out += [("Drum", wd, fine(0.005, 0.01), "drum_wood"), ("Wire", wr, fine(0.005, 0.01), "wire")]
    d2 = Field("Drum2")
    c2 = v3((0.62, -0.42, 0.0))
    for z in (0.025, 0.3):
        d2.add(Cylinder(c2 + Z * z, 0.26, 0.04, rr=0.008), k=0.0, label=10)
    d2.add(Cylinder(c2 + Z * 0.16, 0.12, 0.28, rr=0.01), k=0.004, label=11)
    d2.sub(Cylinder(c2 + Z * 0.16, 0.035, 0.5), k=0.004)
    ground_cut(d2)
    out.append(("Drum2", d2, fine(0.005, 0.01), "drum_wood"))
    return out


def weeds(seed=0, s=1.0, n=6, flowers=True):
    """A clump of wasteland weeds: rosebay willowherb (tall stems of narrow leaves under spikes of pink flowers) and
    dock (broad leaves, rusty seed heads) at its foot."""
    rng = np.random.default_rng(seed)
    st, lv, fl = Field("Stems"), Field("WeedLeaves"), Field("Blooms")
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.4, 0.4)
        rr = rng.uniform(0.03, 0.14) * s
        h = rng.uniform(0.5, 0.78) * s
        b = v3((math.cos(a) * rr, math.sin(a) * rr, -0.02))
        lean = v3((math.cos(a) * 0.12, math.sin(a) * 0.12, 1.0))
        top = b + unit(lean) * h
        st.add(RoundCone(b, top, max(0.011 * s, 0.008), max(0.006 * s, 0.005)), k=0.0)
        for j in range(5):                                          # narrow leaves up the stem
            t = 0.15 + 0.13 * j
            q = b + (top - b) * t
            aa = a + j * 2.1 + rng.uniform(-0.3, 0.3)
            d = unit(v3((math.cos(aa), math.sin(aa), 0.25)))
            L = (0.13 - 0.012 * j) * s
            lv.add(leaf(q, d, np.cross(Z, d) + Z * 0.01, lance(L, 0.026 * s), 0.003, bend=-0.6), k=0.0)
        if flowers:                                                 # the flower spike
            fl.add(RoundCone(b + (top - b) * 0.7, top + unit(lean) * 0.03 * s, 0.02 * s, 0.008 * s), k=0.0)
            for j in range(7):
                t = 0.72 + 0.04 * j
                q = b + (top - b) * t
                aa = j * 2.4
                fl.add(Sphere(q + v3((math.cos(aa), math.sin(aa), 0)) * 0.018 * s, (0.02 - 0.0015 * j) * s), k=0.008 * s)
    for k in range(5):                                              # dock leaves at the foot
        a = 2 * math.pi * k / 5 + rng.uniform(-0.3, 0.3)
        d = unit(v3((math.cos(a), math.sin(a), 0.5)))
        lv.add(leaf(v3((0, 0, 0.02)), d, np.cross(Z, d) + Z * 0.01, lance(0.26 * s, 0.07 * s), 0.004, bend=-0.9, cup=1.2), k=0.0)
    ground_cut(st, -0.01)
    out = [("Stems", st, fine(0.004, 0.008), "weed_stem"), ("WeedLeaves", lv, fine(0.004, 0.008), "weed_leaf")]
    if flowers:
        out.append(("Blooms", fl, fine(0.004, 0.008), "willowherb"))
    return out


def sooty_tree(h=2.2, seed=0, young=True):
    """A town tree that has grown up among the works: an oak's shape, its bark grimed with soot, its leaves dull."""
    return retex(oak(h, seed, young=young), {"oak_bark": "soot_bark", "oak_leaves": "soot_leaves"})


# ------------------------------------------------------------------------------------------------ Foundry Row: landmarks
def foundry(seed=0):
    """A foundry: a long brick casting shop under a slate roof with a louvred ventilator along its ridge, pilasters
    between round-headed windows, a great arched doorway (inside it the furnace's mouth glows, the brick round it black
    with soot); at its east end a cupola furnace in riveted iron plates on its brick base, a charging gallery round its
    top and a ladder up to it, the tap hole glowing over a runner and a ladle; at its west end the tall round chimney on
    its square plinth."""
    rng = np.random.default_rng(seed)
    out = []
    hx, hy, ze, zr = 1.25, 0.66, 1.2, 1.78
    wl, dk, fr, gw = Field("Walls"), Field("Glass"), Field("Frames"), Field("Glow")
    wl.add(walls_box(0, 0, hx, hy, -0.05, ze, batter=0.0, amp=0.003, seed=seed), k=0.0)
    wl.paint(Func(lambda P: (P[:, 2] - F32(0.2)).astype(F32), (-3, -2, -0.2), (3, 2, 0.4)), 8)
    wl.add(RoundBox((0, 0, 0.2), (hx + 0.025, hy + 0.025, 0.02), 0.006), k=0.003, label=6)
    for x in np.linspace(-hx, hx, 6):                               # pilasters
        for sy in (-1, 1):
            wl.add(RoundBox((x, sy * (hy + 0.03), ze / 2), (0.06, 0.035, ze / 2), 0.006), k=0.003)
    wl.add(RoundBox((0, 0, ze - 0.04), (hx + 0.06, hy + 0.06, 0.04), 0.008), k=0.003, label=6)    # the cornice
    xs = np.linspace(-hx, hx, 6)
    door_x = -0.25
    for i in range(5):
        x = (xs[i] + xs[i + 1]) / 2
        for sy in (-1, 1):
            if sy < 0 and abs(x - door_x) < 0.4:
                continue
            window(wl, dk, fr, (x, sy * (hy + 0.0), 0.72), (0, sy, 0), 0.2, 0.42, arch=True)
    roof(Field("_"), (0, 0), hx, hy, ze, zr, wall=wl, wall_in=0.0)
    # the great doorway (its arch, the soot over it), the furnace mouth glowing inside
    dw, dh = 0.62, 0.62
    doorway(wl, None, (door_x, -hy - 0.03, 0.0), (0, -1, 0), dw, dh, depth=0.3, arch=True, open_=True, dk=dk, step=False)
    wl.paint(Func(lambda P: np.maximum(np.abs(P[:, 0] - F32(door_x)) - F32(0.42), np.maximum(F32(0.45) - P[:, 2], P[:, 1] + F32(hy - 0.08))).astype(F32),
                  (door_x - 0.6, -hy - 0.3, 0.3), (door_x + 0.6, -hy + 0.3, ze + 0.1)), 5)
    fm = v3((door_x, -hy + 0.2, 0.0))
    wl.add(walls_box(fm[0], fm[1] + 0.1, 0.3, 0.12, -0.05, 0.8, batter=0.0, amp=0.003, seed=seed + 3), k=0.0, label=5)
    wl.sub(Func(lambda P: (np.maximum(np.minimum(np.maximum(np.abs(P[:, 0] - F32(fm[0])) - F32(0.13), P[:, 2] - F32(0.3)),
                                                 np.sqrt((P[:, 0] - F32(fm[0])) ** 2 + (P[:, 2] - F32(0.3)) ** 2) - F32(0.13)),
                                      np.abs(P[:, 1] - F32(fm[1] - 0.02)) - F32(0.06))).astype(F32),
                fm + v3((-0.3, -0.2, -0.1)), fm + v3((0.3, 0.2, 0.6))), k=0.01)
    gw.add(RoundBox(fm + v3((0, 0.03, 0.22)), (0.14, 0.02, 0.22), 0.0), k=0.0)
    gw.add(Ellipsoid(fm + v3((0, -0.05, 0.03)), (0.18, 0.1, 0.03)), k=0.02)
    ground_cut(wl)
    out += [("Walls", wl, fine(0.008, 0.016), "brick"), ("Glass", dk, fine(0.006, 0.012), "glass"), ("Frames", fr, fine(0.004, 0.008), "frames")]
    rf = Field("Roof")
    zt = roof(rf, (0, 0), hx, hy, ze, zr, over=0.1)
    out.append(("Roof", rf, fine(0.008, 0.016), "slate"))
    # the ridge ventilator: louvres under a little slate roof
    lv = Field("Louvres")
    for sy in (-1, 1):
        for j in range(3):
            lv.add(RoundBox((0, sy * 0.15, zt + 0.06 + j * 0.06), (hx * 0.62, 0.012, 0.022), 0.004, R=euler(sy * 0.5, 0, 0)), k=0.0, label=10)
    for x in np.linspace(-hx * 0.62, hx * 0.62, 4):
        lv.add(RoundBox((x, 0, zt + 0.1), (0.02, 0.16, 0.1), 0.004), k=0.002, label=11)
    rf2 = Field("VentRoof")
    roof(rf2, (0, 0), hx * 0.64, 0.2, zt + 0.21, zt + 0.36, over=0.04)
    out += [("Louvres", lv, fine(0.004, 0.008), "timber"), ("VentRoof", rf2, fine(0.006, 0.012), "slate")]
    # the chimney at the west end
    ch = Field("Chimney")
    chx = -hx - 0.3
    chimney_square(ch, (chx, 0.1), -0.05, 0.6, 0.27, 0.25, seed, cap=False, plinth=0.5)
    ch.add(RoundBox((chx, 0.1, 0.62), (0.3, 0.3, 0.04), 0.01), k=0.004, label=6)
    chimney_round(ch, (chx, 0.1), 0.6, 3.75, 0.23, 0.15, seed + 1, bands=(1.3, 2.1, 2.9))
    ground_cut(ch)
    out.append(("Chimney", ch, fine(0.007, 0.014), "brick"))
    # the cupola at the east end
    cu, bs, gl2 = Field("Cupola"), Field("CupolaBase"), Field("Gallery")
    cx = hx + 0.42
    bs.add(walls_box(cx, -0.05, 0.32, 0.32, -0.05, 0.42, batter=0.02, amp=0.004, seed=seed + 5), k=0.0)
    bs.sub(Func(lambda P: (np.maximum(np.minimum(np.maximum(np.abs(P[:, 0] - F32(cx)) - F32(0.07), P[:, 2] - F32(0.2)),
                                                 np.sqrt((P[:, 0] - F32(cx)) ** 2 + (P[:, 2] - F32(0.2)) ** 2) - F32(0.07)),
                                      np.abs(P[:, 1] + F32(0.37)) - F32(0.06))).astype(F32), (cx - 0.2, -0.5, -0.1), (cx + 0.2, -0.2, 0.4)), k=0.01)
    bs.paint(Func(lambda P: (np.sqrt((P[:, 0] - F32(cx)) ** 2 + (P[:, 2] - F32(0.2)) ** 2) - F32(0.2)).astype(F32), (cx - 0.4, -0.6, -0.2), (cx + 0.4, 0.0, 0.6)), 5)
    ground_cut(bs)
    out.append(("CupolaBase", bs, fine(0.007, 0.014), "brick"))
    cu.add(cone((cx, -0.05), 0.4, 2.35, 0.3, 0.26), k=0.0)
    for z in np.arange(0.55, 2.3, 0.3):
        rr = 0.3 - 0.04 * (z - 0.4) / 1.95
        cu.add(Torus((cx, -0.05, z), rr + 0.003, 0.012), k=0.004, label=7)
    for k in range(10):                                             # vertical seams of rivets
        a = 2 * math.pi * k / 10
        cu.add(RoundCone((cx + math.cos(a) * 0.3, -0.05 + math.sin(a) * 0.3, 0.42), (cx + math.cos(a) * 0.265, -0.05 + math.sin(a) * 0.265, 2.3), 0.01, 0.01), k=0.004)
    cu.sub(Cylinder((cx, -0.05, 2.4), 0.18, 0.4), k=0.01)
    cu.add(Torus((cx, -0.05, 2.35), 0.24, 0.03), k=0.01)
    cu.paint(Func(lambda P: (F32(2.0) - P[:, 2]).astype(F32), (cx - 1, -1, 1.8), (cx + 1, 1, 2.6)), 5)
    out.append(("Cupola", cu, fine(0.006, 0.012), "rust_iron"))
    zg = 1.62                                                       # the charging gallery and its ladder
    gl2.add(Func(lambda P: np.maximum(np.abs(np.sqrt((P[:, 0] - F32(cx)) ** 2 + (P[:, 1] + F32(0.05)) ** 2) - F32(0.42)) - F32(0.13),
                                      np.abs(P[:, 2] - F32(zg)) - F32(0.018)).astype(F32), (cx - 0.7, -0.75, zg - 0.05), (cx + 0.7, 0.65, zg + 0.05)), k=0.0, label=0)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        p = v3((cx + math.cos(a) * 0.53, -0.05 + math.sin(a) * 0.53, 0))
        gl2.add(RoundCone(p + Z * zg, p + Z * (zg + 0.28), 0.01, 0.01), k=0.002)
        gl2.add(RoundCone(p + Z * zg, v3((cx + math.cos(a) * 0.31, -0.05 + math.sin(a) * 0.31, zg - 0.3)), 0.012, 0.012), k=0.002)
    gl2.add(Torus((cx, -0.05, zg + 0.28), 0.53, 0.01), k=0.002)
    for sy in (-1, 1):
        gl2.add(RoundCone((cx + 0.62, -0.05 + sy * 0.12, -0.03), (cx + 0.55, -0.05 + sy * 0.12, zg + 0.3), 0.012, 0.012), k=0.0)
    for k in range(9):
        t = (k + 0.5) / 9
        p = v3((cx + 0.62 - 0.07 * t, -0.05, -0.03 + (zg + 0.3) * t))
        gl2.add(RoundCone(p + v3((0, -0.12, 0)), p + v3((0, 0.12, 0)), 0.008, 0.008), k=0.0)
    ground_cut(gl2)
    out.append(("Gallery", gl2, fine(0.004, 0.008), "machine"))
    # the tap hole: a runner to a ladle of molten iron (glowing), the glow in the tap hole
    ld = Field("Ladle")
    lc = v3((cx, -0.75, 0.0))
    ld.add(cone((lc[0], lc[1]), 0.0, 0.26, 0.15, 0.2), k=0.0)
    ld.sub(cone((lc[0], lc[1]), 0.05, 0.4, 0.12, 0.17), k=0.01)
    ld.add(Torus(lc + Z * 0.26, 0.2, 0.02), k=0.006)
    ld.add(RoundBox((cx, -0.5, 0.17), (0.04, 0.16, 0.025), 0.01, R=euler(-0.25, 0, 0)), k=0.0)
    for sx in (-1, 1):
        ld.add(RoundBox((cx + sx * 0.05, -0.5, 0.2), (0.012, 0.16, 0.03), 0.004, R=euler(-0.25, 0, 0)), k=0.004)
    ground_cut(ld)
    out.append(("Ladle", ld, fine(0.005, 0.01), "rust_iron"))
    gw.add(Ellipsoid(lc + Z * 0.21, (0.17, 0.17, 0.035)), k=0.0)
    gw.add(RoundBox((cx, -0.5, 0.2), (0.032, 0.17, 0.012), 0.006, R=euler(-0.25, 0, 0)), k=0.01)
    gw.add(RoundBox((cx, -0.36, 0.2), (0.07, 0.03, 0.07), 0.01), k=0.01)
    out.append(("Glow", gw, fine(0.005, 0.01), "glow_fire"))
    # scrap and coke by the cupola
    ck = Field("Coke")
    for k in range(5):
        a = rng.uniform(-1.0, 1.0)
        ck.add(Ellipsoid((cx + 0.5 + math.cos(a) * 0.15, 0.45 + math.sin(a) * 0.15, 0.0), (0.18, 0.15, 0.13), **wob(14.0, 0.02, seed + k)), k=0.04)
    ground_cut(ck, -0.01)
    out.append(("Coke", ck, fine(0.006, 0.012), "coal"))
    return out


FOUNDRY_FIRE = (1.67, -0.05, 2.4)        # the cupola's top (Blender: x, y, z)
FOUNDRY_SMOKE = (-1.55, 0.1, 3.8)        # the chimney's mouth


def gasholder(seed=0):
    """A gasholder: the bell (a riveted iron drum with a domed crown, half risen) in its round tank of brick with a stone
    coping, in a guide frame of eight cast-iron columns joined by two tiers of lattice girders, rollers on the bell's
    rim running up the columns, a ladder up one."""
    out = []
    R0, Rt, Hc = 1.05, 1.0, 2.25
    tk = Field("Tank")
    tk.add(Func(lambda P: np.maximum(np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(Rt)) - F32(0.07), P[:, 2] - F32(0.28)).astype(F32),
                (-1.2, -1.2, -0.1), (1.2, 1.2, 0.35)), k=0.0)
    tk.add(Torus((0, 0, 0.28), Rt, 0.085), k=0.01, label=6)
    tk.paint(Func(lambda P: (P[:, 2] - F32(0.12)).astype(F32), (-2, -2, -0.2), (2, 2, 0.3)), 8)
    ground_cut(tk)
    out.append(("Tank", tk, fine(0.008, 0.016), "brick"))
    bl = Field("Bell")
    zb0, zb1 = 0.1, 1.35
    bl.add(Cylinder((0, 0, (zb0 + zb1) / 2), Rt - 0.1, zb1 - zb0, rr=0.03), k=0.0)
    bl.add(Ellipsoid((0, 0, zb1 - 0.02), (Rt - 0.1, Rt - 0.1, 0.22)), k=0.03)
    bl.inter(Plane((0, 0, zb1 + 0.25), (0, 0, 1)))
    for z in np.arange(0.4, zb1, 0.26):
        bl.add(Torus((0, 0, z), Rt - 0.098, 0.01), k=0.004)
    for k in range(16):
        a = 2 * math.pi * k / 16
        bl.add(RoundCone((math.cos(a) * (Rt - 0.098), math.sin(a) * (Rt - 0.098), 0.3), (math.cos(a) * (Rt - 0.098), math.sin(a) * (Rt - 0.098), zb1 - 0.04), 0.008, 0.008), k=0.003)
    bl.add(Torus((0, 0, zb1 - 0.02), Rt - 0.1, 0.03), k=0.008, label=7)
    bl.add(Cylinder((0, 0, zb1 + 0.22), 0.1, 0.06, rr=0.02), k=0.02, label=7)
    for k in range(8):                                              # the guide rollers' carriages on its rim
        a = 2 * math.pi * (k + 0.5) / 8
        d = v3((math.cos(a), math.sin(a), 0))
        bl.add(RoundBox(d * (Rt - 0.02) + Z * (zb1 - 0.02), (0.06, 0.05, 0.05), 0.012, R=Rz(a)), k=0.006, label=7)
    out.append(("Bell", bl, fine(0.008, 0.016), "gas_iron"))
    fr = Field("Guides")
    Rc = Rt + 0.12
    cols = []
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        p = v3((math.cos(a) * Rc, math.sin(a) * Rc, 0))
        cols.append(p)
        fr.add(RoundBox(p + Z * 0.1, (0.08, 0.08, 0.1), 0.015, R=Rz(a)), k=0.0, label=7)
        fr.add(RoundCone(p + Z * 0.18, p + Z * Hc, 0.045, 0.034), k=0.01)
        for z in (0.3, Hc - 0.12):
            fr.add(Torus(p + Z * z, 0.044, 0.01), k=0.004)
        fr.add(Sphere(p + Z * (Hc + 0.05), 0.05), k=0.01, label=6)
        fr.add(RoundCone(p + Z * (Hc + 0.09), p + Z * (Hc + 0.18), 0.02, 0.004), k=0.006)
    for zt in (1.25, Hc - 0.06):                                    # lattice girders between the columns
        for k in range(8):
            a, b = cols[k] + Z * zt, cols[(k + 1) % 8] + Z * zt
            fr.add(RoundCone(a, b, 0.016, 0.016), k=0.004)
            fr.add(RoundCone(a - Z * 0.16, b - Z * 0.16, 0.012, 0.012), k=0.004)
            for j in range(3):
                t0, t1 = j / 3, (j + 1) / 3
                p0 = a + (b - a) * t0
                p1 = a + (b - a) * t1 - Z * 0.16
                fr.add(RoundCone(p0, p1, 0.008, 0.008), k=0.002)
                fr.add(RoundCone(p0 - Z * 0.16, a + (b - a) * t1, 0.008, 0.008), k=0.002)
    for sy in (-1, 1):                                              # a ladder up the front column
        p = cols[5]
        fr.add(RoundCone(p + v3((0.0, -0.08, -0.03)) + v3((sy * 0.07, 0, 0)), p + v3((0.0, -0.08, Hc)) + v3((sy * 0.07, 0, 0)), 0.008, 0.008), k=0.0)
    for k in range(14):
        p = cols[5] + v3((0, -0.08, 0.1 + k * 0.155))
        fr.add(RoundCone(p - v3((0.07, 0, 0)), p + v3((0.07, 0, 0)), 0.006, 0.006), k=0.0)
    ground_cut(fr)
    out.append(("Guides", fr, fine(0.004, 0.008), "frame_iron"))
    return out


def _steam_hammer(out, o=(0, 0, 0), yaw=0.0, seed=0, billet=True, name=""):
    """A steam hammer: two cast-iron standards in an A over the anvil block, the steam cylinder on top with its valve
    chest and piston rod down to the tup; a glowing billet on the anvil (billet)."""
    hm, gw = Field(name + "Hammer"), Field(name + "Billet")
    H = 1.55
    for sx in (-1, 1):
        a, b = v3((sx * 0.42, 0, 0.0)), v3((sx * 0.15, 0, H - 0.06))
        t = unit(b - a)
        Rs = np.stack([unit(np.cross((0, 1, 0), t)), v3((0, 1, 0)), t], axis=1)
        hm.add(RoundBox((a + b) / 2, (0.06, 0.1, float(np.linalg.norm(b - a)) / 2), 0.015, R=Rs), k=0.0, label=0)
        hm.add(RoundBox((a + b) / 2 + Rs @ v3((0.0, 0.0, 0.0)), (0.025, 0.13, float(np.linalg.norm(b - a)) / 2 - 0.05), 0.01, R=Rs), k=0.004, label=0)
        hm.add(RoundBox((sx * 0.4, 0, 0.05), (0.14, 0.2, 0.05), 0.01), k=0.01, label=0)
        for sy in (-1, 1):
            hm.add(Sphere((sx * 0.48, sy * 0.13, 0.1), 0.022), k=0.004, label=6)
    hm.add(RoundBox((0, 0, H - 0.02), (0.26, 0.16, 0.06), 0.015), k=0.01)
    hm.add(Cylinder((0, 0, H + 0.22), 0.17, 0.42, rr=0.03), k=0.01)
    for z in (H + 0.05, H + 0.4):
        hm.add(Cylinder((0, 0, z), 0.2, 0.04, rr=0.01), k=0.004, label=7)
    hm.add(RoundBox((0.2, 0, H + 0.24), (0.06, 0.1, 0.15), 0.015), k=0.01, label=7)
    hm.add(RoundCone((0.24, 0, H + 0.4), (0.4, 0, H + 0.62), 0.03, 0.03), k=0.004, label=7)
    hm.add(RoundCone((0, 0, H - 0.1), (0, 0, 0.62), 0.03, 0.03), k=0.004, label=6)
    hm.add(RoundBox((0, 0, 0.52), (0.12, 0.13, 0.12), 0.015), k=0.006, label=7)                     # the tup
    hm.add(RoundBox((0, 0, 0.13), (0.2, 0.2, 0.13), 0.02), k=0.0, label=7)                          # the anvil block
    hm.add(RoundBox((0, 0, 0.29), (0.11, 0.14, 0.04), 0.01), k=0.004, label=7)
    hm.add(Cylinder((0.38, 0, H + 0.45), 0.04, 0.07, rr=0.01, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004, label=6)
    ground_cut(hm)
    parts = [(name + "Hammer", hm, fine(0.005, 0.01), "machine")]
    if billet:
        gw.add(RoundBox((0.02, 0, 0.36), (0.13, 0.05, 0.035), 0.012), k=0.0)
        parts.append((name + "Billet", gw, fine(0.004, 0.008), "glow_fire"))
    return place_parts(out, parts, o, Rz(yaw))


def _vertical_boiler(out, o, seed=0, h=1.1, r=0.22, name=""):
    """A vertical boiler: a riveted drum on a firebox base, its chimney, a pressure gauge (brass), the firedoor glowing."""
    bo, gw = Field(name + "Boiler"), Field(name + "Fire")
    o = v3(o)
    bo.add(Cylinder(o + Z * (h / 2), r, h, rr=0.03), k=0.0)
    bo.add(Ellipsoid(o + Z * h, (r, r, 0.1)), k=0.02)
    for z in np.arange(0.2, h, 0.22):
        bo.add(Torus(o + Z * z, r + 0.002, 0.009), k=0.003, label=7)
    bo.add(RoundCone(o + Z * (h + 0.05), o + Z * (h + 0.75), 0.06, 0.055), k=0.01, label=7)
    bo.add(Torus(o + Z * (h + 0.75), 0.06, 0.016), k=0.004, label=7)
    bo.add(Cylinder(o + v3((0, -r - 0.02, h * 0.7)), 0.05, 0.03, rr=0.008, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.004, label=6)
    bo.add(Cylinder(o + v3((0, -r - 0.03, h * 0.7)), 0.035, 0.012, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.0, label=7)
    bo.sub(RoundBox(o + v3((0, -r, 0.24)), (0.07, 0.06, 0.07), 0.015), k=0.006)
    bo.add(Sphere(o + v3((0.1, -0.1, h + 0.08)), 0.04), k=0.006, label=6)
    ground_cut(bo)
    gw.add(RoundBox(o + v3((0, -r + 0.03, 0.24)), (0.065, 0.02, 0.065), 0.01), k=0.0)
    return place_parts(out, [(name + "Boiler", bo, fine(0.005, 0.01), "machine"), (name + "Fire", gw, fine(0.004, 0.008), "glow_fire")], (0, 0, 0))


def steam_hammer(seed=0):
    """A steam hammer in the open: the hammer on its bed over a glowing billet, its vertical boiler beside it, a heap of
    coal, tongs propped on the anvil."""
    out = []
    _steam_hammer(out, (0, 0, 0), 0.0, seed)
    _vertical_boiler(out, (0.72, 0.3, 0), seed)
    cl = Field("Coal")
    for k in range(4):
        cl.add(Ellipsoid((0.75 + 0.12 * math.cos(k * 1.7), -0.35 + 0.1 * math.sin(k * 1.7), 0.0), (0.2, 0.16, 0.14), **wob(16.0, 0.02, seed + k)), k=0.04)
    ground_cut(cl, -0.01)
    out.append(("Coal", cl, fine(0.006, 0.012), "coal"))
    tg = Field("Tongs")
    tg.add(RoundCone((0.1, -0.24, 0.3), (0.42, -0.62, 0.02), 0.012, 0.012), k=0.0)
    tg.add(RoundCone((0.14, -0.22, 0.3), (0.48, -0.58, 0.02), 0.012, 0.012), k=0.0)
    ground_cut(tg)
    out.append(("Tongs", tg, fine(0.004, 0.008), "iron"))
    pl = Field("Bed")
    pl.add(convex_w([((0, 0, 0.04), (0, 0, 1)), ((0, 0, -0.05), (0, 0, -1)), ((0.62, 0, 0), (1, 0, 0.5)), ((-0.62, 0, 0), (-1, 0, 0.5)),
                     ((0, 0.42, 0), (0, 1, 0.5)), ((0, -0.42, 0), (0, -1, 0.5))], (-0.8, -0.6, -0.1), (0.8, 0.6, 0.1), 0.004, 8.0, seed), k=0.0)
    ground_cut(pl)
    out.append(("Bed", pl, fine(0.008, 0.016), "stone"))
    return out


def hammer_shed(seed=0):
    """A steam hammer shed: brick back and end walls, the front open between cast-iron columns under a slate roof with
    skylights; inside, the steam hammer over its glowing billet; its boiler outside the end wall, coal heaped by it."""
    out = []
    hx, hy, ze = 1.15, 0.7, 1.95
    wl, dk, fr = Field("Walls"), Field("Glass"), Field("Frames")
    wl.add(walls_box(0, hy - 0.06, hx, 0.06, -0.05, ze, batter=0.0, amp=0.003, seed=seed), k=0.0)
    for sx in (-1, 1):
        wl.add(walls_box(sx * (hx - 0.06), 0, 0.06, hy, -0.05, ze, batter=0.0, amp=0.003, seed=seed + 1), k=0.0)
    wl.paint(Func(lambda P: (P[:, 2] - F32(0.22)).astype(F32), (-3, -2, -0.2), (3, 2, 0.4)), 8)
    for x in (-0.6, 0.0, 0.6):
        window(wl, dk, fr, (x, hy, 1.3), (0, 1, 0), 0.22, 0.4, arch=True)
    for sx in (-1, 1):
        window(wl, dk, fr, (sx * hx, 0.1, 1.3), (sx, 0, 0), 0.22, 0.4, arch=True)
    for sx in (-1, 1):
        wl.add(gable((sx * (hx - 0.06), 0), 0.06, hy, ze - 0.05, ze + 0.5, axis="x"), k=0.0)
    ground_cut(wl)
    out += [("Walls", wl, fine(0.008, 0.016), "brick"), ("Glass", dk, fine(0.006, 0.012), "glass"), ("Frames", fr, fine(0.004, 0.008), "frames")]
    co = Field("Columns")
    for x in np.linspace(-hx + 0.06, hx - 0.06, 4):
        co.add(Cylinder((x, -hy + 0.04, 0.08), 0.07, 0.16, rr=0.02), k=0.0)
        co.add(RoundCone((x, -hy + 0.04, 0.12), (x, -hy + 0.04, ze - 0.08), 0.045, 0.036), k=0.01)
        co.add(RoundBox((x, -hy + 0.04, ze - 0.06), (0.07, 0.07, 0.05), 0.012), k=0.01)
    co.add(RoundBox((0, -hy + 0.04, ze + 0.01), (hx, 0.05, 0.05), 0.01), k=0.006, label=7)
    ground_cut(co)
    out.append(("Columns", co, fine(0.005, 0.01), "frame_iron"))
    rf = Field("Roof")
    roof(rf, (0, 0), hx, hy, ze, ze + 0.55, over=0.1)
    out.append(("Roof", rf, fine(0.008, 0.016), "slate"))
    sk = Field("Skylights")
    for x in (-0.55, 0.55):
        sk.add(RoundBox((x, -0.36, ze + 0.32), (0.22, 0.24, 0.02), 0.005, R=euler(-math.atan2(0.55, hy + 0.1), 0, 0)), k=0.0)
    out.append(("Skylights", sk, fine(0.005, 0.01), "glass"))
    fl = Field("Floor")
    fl.add(RoundBox((0, 0, 0.0), (hx - 0.05, hy - 0.05, 0.03), 0.01), k=0.0)
    ground_cut(fl, -0.02)
    out.append(("Floor", fl, fine(0.008, 0.016), "flags"))
    _steam_hammer(out, (0.0, 0.05, 0.02), 0.0, seed)
    _vertical_boiler(out, (hx + 0.35, 0.3, 0), seed, h=0.95, r=0.2)
    cl = Field("Coal")
    for k in range(4):
        cl.add(Ellipsoid((hx + 0.35 + 0.1 * math.cos(k * 1.7), -0.3 + 0.1 * math.sin(k * 1.7), 0.0), (0.18, 0.15, 0.13), **wob(16.0, 0.02, seed + k)), k=0.04)
    ground_cut(cl, -0.01)
    out.append(("Coal", cl, fine(0.006, 0.012), "coal"))
    return out


def water_tower(seed=0, trestle=False):
    """A water tower: a sectional iron tank (its flanged panels in a grid, a float gauge, a ladder up its side, a
    railing round its top) on a square brick tower with round-headed windows and a door (or, trestle: on four cast-iron
    legs braced with ties, a water crane beside it with its swinging arm and leather hose)."""
    out = []
    S, Ht, Th = 0.62, (1.35 if not trestle else 1.45), 0.6
    if not trestle:
        bs, dk, fr, dr = Field("Base"), Field("Glass"), Field("Frames"), Field("Door")
        bs.add(walls_box(0, 0, S - 0.04, S - 0.04, -0.05, Ht, batter=0.012, amp=0.003, seed=seed), k=0.0)
        bs.paint(Func(lambda P: (P[:, 2] - F32(0.2)).astype(F32), (-2, -2, -0.2), (2, 2, 0.4)), 8)
        bs.add(RoundBox((0, 0, Ht - 0.04), (S + 0.02, S + 0.02, 0.05), 0.01), k=0.004, label=6)
        doorway(bs, dr, (0.0, -(S - 0.04), 0.0), (0, -1, 0), 0.24, 0.42, arch=True, label=5)
        window(bs, dk, fr, (0.0, -(S - 0.04), 0.9), (0, -1, 0), 0.18, 0.3, arch=True)
        for sx in (-1, 1):
            window(bs, dk, fr, (sx * (S - 0.04), 0.0, 0.75), (sx, 0, 0), 0.18, 0.34, arch=True)
        ground_cut(bs)
        out += [("Base", bs, fine(0.008, 0.016), "brick"), ("Glass", dk, fine(0.006, 0.012), "glass"), ("Frames", fr, fine(0.004, 0.008), "frames"),
                ("Door", dr, fine(0.005, 0.01), "door")]
    else:
        lg = Field("Legs")
        for sx in (-1, 1):
            for sy in (-1, 1):
                lg.add(RoundBox((sx * 0.5, sy * 0.5, 0.08), (0.08, 0.08, 0.1), 0.015), k=0.0, label=8)
                lg.add(RoundCone((sx * 0.5, sy * 0.5, 0.1), (sx * 0.45, sy * 0.45, Ht), 0.05, 0.04), k=0.01)
        for z in (0.55, 1.05):
            for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
                lg.add(RoundCone((a[0] * 0.48, a[1] * 0.48, z), (b[0] * 0.48, b[1] * 0.48, z), 0.016, 0.016), k=0.004)
        for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            lg.add(RoundCone((a[0] * 0.49, a[1] * 0.49, 0.15), (b[0] * 0.47, b[1] * 0.47, 1.0), 0.01, 0.01), k=0.002)
            lg.add(RoundCone((b[0] * 0.49, b[1] * 0.49, 0.15), (a[0] * 0.47, a[1] * 0.47, 1.0), 0.01, 0.01), k=0.002)
        lg.add(RoundBox((0, 0, Ht - 0.02), (S, S, 0.04), 0.01), k=0.006, label=7)
        ground_cut(lg)
        out.append(("Legs", lg, fine(0.005, 0.01), "frame_iron"))
    tk = Field("Tank")
    z0, z1 = Ht + 0.02, Ht + 0.02 + Th
    tk.add(RoundBox((0, 0, (z0 + z1) / 2), (S, S, Th / 2), 0.02), k=0.0)
    tk.add(RoundBox((0, 0, z0 + 0.02), (S + 0.03, S + 0.03, 0.025), 0.008), k=0.004, label=7)
    tk.add(RoundBox((0, 0, z1 - 0.01), (S + 0.03, S + 0.03, 0.02), 0.008), k=0.004, label=7)
    for t in np.linspace(-S, S, 5)[1:-1]:                         # the panels' flanges
        for sgn in (-1, 1):
            tk.add(RoundBox((t, sgn * (S + 0.01), (z0 + z1) / 2), (0.012, 0.012, Th / 2), 0.004), k=0.003)
            tk.add(RoundBox((sgn * (S + 0.01), t, (z0 + z1) / 2), (0.012, 0.012, Th / 2), 0.004), k=0.003)
    for sgn in (-1, 1):
        tk.add(RoundBox((0, sgn * (S + 0.01), (z0 + z1) / 2), (S, 0.012, 0.012), 0.004), k=0.003)
        tk.add(RoundBox((sgn * (S + 0.01), 0, (z0 + z1) / 2), (0.012, S, 0.012), 0.004), k=0.003)
    tk.sub(RoundBox((0, 0, z1 + 0.05), (S - 0.04, S - 0.04, 0.1), 0.01), k=0.006)
    tk.add(RoundBox((0.25, -S - 0.03, z0 + 0.3), (0.012, 0.012, 0.26), 0.004), k=0.002, label=6)              # the float gauge
    tk.add(RoundBox((0.25, -S - 0.04, z0 + 0.22), (0.035, 0.012, 0.02), 0.004), k=0.002, label=5)
    for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
        tk.add(RoundCone((a[0] * S, a[1] * S, z1 + 0.22), (b[0] * S, b[1] * S, z1 + 0.22), 0.009, 0.009), k=0.002)
        tk.add(RoundCone((a[0] * S, a[1] * S, z1), (a[0] * S, a[1] * S, z1 + 0.22), 0.009, 0.009), k=0.002)
    out.append(("Tank", tk, fine(0.006, 0.012), "gas_iron"))
    wt = Field("Water")
    wt.add(RoundBox((0, 0, z1 - 0.06), (S - 0.04, S - 0.04, 0.02), 0.0), k=0.0)
    out.append(("Water", wt, fine(0.014, 0.028), "dark_water"))
    ld = Field("Ladder")
    for sx in (-1, 1):
        ld.add(RoundCone((S + 0.06, sx * 0.1, -0.03 if trestle else Ht - 0.02), (S + 0.06, sx * 0.1, z1 + 0.22), 0.009, 0.009), k=0.0)
    for k in range(int(((z1 + 0.2) - (0.0 if trestle else Ht)) / 0.13)):
        z = (0.08 if trestle else Ht + 0.06) + k * 0.13
        ld.add(RoundCone((S + 0.06, -0.1, z), (S + 0.06, 0.1, z), 0.006, 0.006), k=0.0)
    if trestle:
        ground_cut(ld)
    out.append(("Ladder", ld, fine(0.004, 0.008), "frame_iron"))
    if trestle:                                                     # the water crane
        wc = Field("Crane")
        c = v3((-0.2, -1.05, 0.0))
        wc.add(Cylinder(c + Z * 0.05, 0.12, 0.1, rr=0.02), k=0.0, label=7)
        wc.add(RoundCone(c + Z * 0.08, c + Z * 1.05, 0.065, 0.05), k=0.01)
        wc.add(Torus(c + Z * 0.95, 0.055, 0.012), k=0.004, label=6)
        arm = [c + Z * 1.05, c + Z * 1.12 + v3((0.25, 0.0, 0)), c + Z * 1.1 + v3((0.6, 0.02, 0))]
        wc.add(Chain(arm, [0.05, 0.045, 0.04], k=0.02), k=0.01)
        wc.add(Sphere(c + Z * 1.15, 0.06), k=0.01)
        wc.add(RoundCone(c + Z * 1.2, c + Z * 1.35, 0.05, 0.03), k=0.004)
        wc.add(RoundCone(c + Z * 1.0 + v3((-0.05, 0, 0)), c + Z * 0.9 + v3((-0.35, 0, 0)), 0.014, 0.014), k=0.004, label=7)
        wc.add(Sphere(c + Z * 0.9 + v3((-0.38, 0, 0)), 0.05), k=0.004, label=7)
        ground_cut(wc)
        hs = Field("Hose")
        hp = c + Z * 1.08 + v3((0.62, 0.02, 0))
        hs.add(Chain([hp, hp + v3((0.04, 0, -0.25)), hp + v3((0.0, 0.03, -0.5)), hp + v3((-0.05, 0.05, -0.62))], [0.035, 0.032, 0.03, 0.028], k=0.01), k=0.0)
        out += [("Crane", wc, fine(0.005, 0.01), "frame_iron"), ("Hose", hs, fine(0.005, 0.01), "leather")]
    return out


def workshop(seed=0):
    """A small brick workshop under a sawtooth roof (north lights to the front), double doors with a sign board over
    them, round-headed windows, a stub chimney, casks by the door."""
    out = []
    hx, hy, ze = 0.95, 0.62, 0.95
    wl, dk, fr, dr, gl = Field("Walls"), Field("Glass"), Field("Frames"), Field("Doors"), Field("Lights")
    wl.add(walls_box(0, 0, hx, hy, -0.05, ze, batter=0.0, amp=0.003, seed=seed), k=0.0)
    wl.paint(Func(lambda P: (P[:, 2] - F32(0.18)).astype(F32), (-3, -2, -0.2), (3, 2, 0.4)), 8)
    wl.add(RoundBox((0, 0, ze - 0.03), (hx + 0.04, hy + 0.04, 0.035), 0.008), k=0.003, label=6)
    doorway(wl, dr, (-0.35, -hy - 0.01, 0.0), (0, -1, 0), 0.46, 0.62, depth=0.06, label=5)
    wl.add(RoundBox((-0.35, -hy - 0.025, 0.75), (0.3, 0.02, 0.07), 0.01), k=0.002, label=9)        # the sign board
    for x in (0.25, 0.65):
        window(wl, dk, fr, (x, -hy, 0.5), (0, -1, 0), 0.2, 0.36, arch=True)
    for sx in (-1, 1):
        window(wl, dk, fr, (sx * hx, 0.0, 0.5), (sx, 0, 0), 0.2, 0.36, arch=True)
    rf = Field("Roof")
    sawtooth(rf, gl, fr, -hx + 0.02, hx - 0.02, -hy - 0.04, hy + 0.04, ze, 3, 0.42, glaze=-1)
    for sx in (-1, 1):                                              # the zigzag gable walls
        dy = 2 * (hy + 0.04) / 3
        for i in range(3):
            ya = -hy - 0.04 + i * dy
            wl.add(convex([((sx * hx, ya + dy, ze + 0.025), (0, 0.42, dy)), ((sx * hx, ya, ze), (0, -1, 0.12)), ((0, 0, ze - 0.05), (0, 0, -1)),
                           ((sx * hx + 0.02, 0, 0), (1, 0, 0)), ((sx * hx - 0.06, 0, 0), (-1, 0, 0))],
                          (sx * hx - 0.3, ya - 0.2, ze - 0.2), (sx * hx + 0.3, ya + dy + 0.2, ze + 0.6)), k=0.0)
    stack(wl, Field("_"), (0.6, 0.35), 0.1, 0.1, ze, ze + 0.75, pots=0, seed=seed)
    ground_cut(wl)
    out += [("Walls", wl, fine(0.008, 0.016), "brick"), ("Glass", dk, fine(0.006, 0.012), "glass"), ("Frames", fr, fine(0.004, 0.008), "frames"),
            ("Doors", dr, fine(0.005, 0.01), "door"), ("Roof", rf, fine(0.007, 0.014), "slate"), ("Lights", gl, fine(0.005, 0.01), "glass")]
    bb = Field("Casks")
    add_barrel(bb, (0.25, -hy - 0.25, 0.17), hl=0.16, r_end=0.12)
    add_barrel(bb, (0.55, -hy - 0.22, 0.13), R=rot_from_axes(z_axis=(1, 0.2, 0)), hl=0.16, r_end=0.11)
    ground_cut(bb)
    out.append(("Casks", bb, fine(0.005, 0.01), "cask"))
    return out


def beam_engine(seed=0):
    """A beam engine in the open on its stone bed: the great iron beam rocking on an entablature carried by fluted
    columns, the cylinder under one end with its piston rod and parallel motion, the connecting rod down from the other
    end to the crank of the spoked flywheel."""
    out = []
    bd, mc, fw = Field("Bed"), Field("Engine"), Field("Flywheel")
    bd.add(convex_w([((0, 0, 0.14), (0, 0, 1)), ((0, 0, -0.05), (0, 0, -1)), ((1.15, 0, 0), (1, 0, 0.3)), ((-1.0, 0, 0), (-1, 0, 0.3)),
                     ((0, 0.45, 0), (0, 1, 0.3)), ((0, -0.45, 0), (0, -1, 0.3))], (-1.2, -0.6, -0.1), (1.3, 0.6, 0.2), 0.004, 8.0, seed), k=0.0)
    ground_cut(bd)
    out.append(("Bed", bd, fine(0.008, 0.016), "stone"))
    zc = 1.45                                                       # the beam's pivot
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = v3((sx * 0.22, sy * 0.25, 0.14))
            mc.add(Cylinder(p + Z * 0.05, 0.06, 0.1, rr=0.015), k=0.0)
            mc.add(RoundCone(p + Z * 0.08, p + Z * (zc - 0.22), 0.04, 0.032,
                             disp=lambda P, p=p: (F32(0.003) * np.cos(np.arctan2(P[:, 1] - F32(p[1]), P[:, 0] - F32(p[0])) * F32(8))).astype(F32), disp_amp=0.004), k=0.01)
            mc.add(RoundBox(p + Z * (zc - 0.2), (0.06, 0.06, 0.03), 0.01), k=0.006, label=6)
    mc.add(RoundBox((0, 0, zc - 0.14), (0.32, 0.32, 0.05), 0.012), k=0.004)
    for sy in (-1, 1):
        mc.add(RoundBox((0, sy * 0.06, zc - 0.05), (0.08, 0.025, 0.08), 0.01), k=0.004)
    def beam(P):
        x, z = P[:, 0], P[:, 2] - F32(zc)
        half = F32(0.06) + F32(0.08) * np.clip(F32(1) - np.abs(x) / F32(0.95), 0, 1)
        return np.maximum.reduce([np.abs(z) - half, np.abs(x) - F32(0.95), np.abs(P[:, 1]) - F32(0.03)]).astype(F32) * F32(0.9)
    mc.add(Func(beam, (-1.0, -0.1, zc - 0.25), (1.0, 0.1, zc + 0.25)), k=0.0)
    mc.add(Cylinder((0, 0, zc), 0.05, 0.14, rr=0.01, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.006, label=6)
    mc.sub(Ellipsoid((0.45, 0, zc), (0.15, 0.1, 0.045)), k=0.01)
    mc.sub(Ellipsoid((-0.45, 0, zc), (0.15, 0.1, 0.045)), k=0.01)
    cy0 = v3((-0.85, 0, 0.14))                                       # the cylinder
    mc.add(Cylinder(cy0 + Z * 0.38, 0.17, 0.62, rr=0.03), k=0.0, label=7)
    for z in (0.12, 0.64):
        mc.add(Cylinder(cy0 + Z * z, 0.2, 0.05, rr=0.012), k=0.004, label=7)
    mc.add(RoundBox(cy0 + v3((0.2, 0, 0.38)), (0.05, 0.1, 0.22), 0.015), k=0.006, label=7)
    mc.add(RoundCone(cy0 + Z * 0.66, v3((-0.85, 0, zc - 0.02)), 0.022, 0.022), k=0.004, label=6)
    mc.add(RoundCone((-0.85, -0.05, zc - 0.06), (-0.6, -0.05, zc - 0.06), 0.014, 0.014), k=0.004)
    mc.add(RoundCone((-0.6, -0.05, zc - 0.06), (-0.7, -0.05, 0.9), 0.014, 0.014), k=0.004)
    fc = v3((0.82, 0.32, 0.75))                                      # the flywheel and its crank
    fw.add(gear_fn(fc, (0, 1, 0), 0.6, 0.05, teeth=0, spokes=6, hub=0.12), k=0.0)
    out.append(("Flywheel", fw, fine(0.006, 0.012), "machine"))
    for sx in (-1, 1):
        mc.add(convex([((fc[0] + sx * 0.18, 0, 0), (sx, 0, 0.2)), ((fc[0], 0, fc[2] + 0.02), (0, 0, 1)), ((0, 0.36, 0), (0, 1, 0)),
                       ((0, 0.28, 0), (0, -1, 0)), ((0, 0, 0.1), (0, 0, -1))], (fc[0] - 0.4, 0.2, 0.0), (fc[0] + 0.4, 0.45, fc[2] + 0.1)), k=0.01)
    mc.add(RoundCone((fc[0], 0.0, fc[2]), (fc[0], 0.36, fc[2]), 0.035, 0.035), k=0.004, label=6)
    crank = fc + v3((0.0, -0.05, 0.24))
    mc.add(RoundBox((fc[0], 0.12, fc[2] + 0.12), (0.04, 0.025, 0.14), 0.01), k=0.006)
    mc.add(RoundCone(v3((0.88, 0.12, zc - 0.05)), crank + v3((0, 0.17, 0)), 0.03, 0.026), k=0.006, label=7)
    ground_cut(mc)
    out.append(("Engine", mc, fine(0.005, 0.01), "machine"))
    return out


def steam_crane(seed=0):
    """A steam crane: a cab on a turntable on its round pedestal, the vertical boiler's chimney through its roof, the
    lattice jib raised over the yard, its chain down to a hook with a casting slung on it."""
    out = []
    pd, cb, jb, ch = Field("Pedestal"), Field("Cab"), Field("Jib"), Field("Chain")
    pd.add(cone((0, 0), -0.05, 0.3, 0.5, 0.42), k=0.0)
    pd.add(Torus((0, 0, 0.3), 0.42, 0.03), k=0.01, label=6)
    ground_cut(pd)
    out.append(("Pedestal", pd, fine(0.008, 0.016), "stone"))
    cb.add(Cylinder((0, 0, 0.34), 0.42, 0.06, rr=0.015), k=0.0, label=7)
    cb.add(RoundBox((-0.1, 0, 0.7), (0.38, 0.32, 0.36), 0.02), k=0.0)
    cb.add(RoundBox((-0.1, 0, 1.08), (0.42, 0.36, 0.03), 0.02, R=euler(0, 0, 0)), k=0.006, label=7)
    for sy in (-1, 1):
        cb.sub(RoundBox((0.05, sy * 0.32, 0.82), (0.14, 0.04, 0.12), 0.01), k=0.004)
    cb.sub(RoundBox((0.28, 0, 0.6), (0.06, 0.18, 0.26), 0.01), k=0.004)
    cb.add(RoundCone((-0.3, 0, 1.08), (-0.3, 0, 1.55), 0.06, 0.055), k=0.006, label=7)
    cb.add(Torus((-0.3, 0, 1.55), 0.06, 0.015), k=0.004, label=6)
    cb.add(RoundBox((-0.55, 0, 0.55), (0.06, 0.28, 0.18), 0.02), k=0.006, label=7)                  # the counterweight
    out.append(("Cab", cb, fine(0.006, 0.012), "crane"))
    dk = Field("Dark")
    dk.add(RoundBox((0.1, 0, 0.75), (0.2, 0.28, 0.25), 0.01), k=0.0)
    out.append(("Dark", dk, fine(0.006, 0.012), "dark"))
    root = v3((0.3, 0, 0.45))
    tip = v3((1.75, 0, 1.95))
    t, b, n = frame(tip - root)
    for sy in (-1, 1):
        for sz in (-1, 1):
            w = 0.13 * (1.0 - 0.0)
            jb.add(RoundCone(root + b * (sy * 0.16) + n * (sz * 0.09), tip + b * (sy * 0.05) + n * (sz * 0.04), 0.016, 0.012), k=0.002)
    L = float(np.linalg.norm(tip - root))
    for k in range(9):
        t0 = (k + 0.5) / 9
        q = root + (tip - root) * t0
        hw, hz = 0.16 - 0.11 * t0, 0.09 - 0.05 * t0
        for sy in (-1, 1):
            jb.add(RoundCone(q + b * (sy * hw) + n * hz, q + (tip - root) / 9 + b * (sy * hw * 0.9) - n * hz * 0.9, 0.008, 0.008), k=0.002)
        jb.add(RoundCone(q + b * (-hw) + n * hz, q + b * hw + n * hz, 0.008, 0.008), k=0.002)
    jb.add(Cylinder(tip, 0.07, 0.08, rr=0.02, R=rot_from_axes(z_axis=b)), k=0.006, label=7)
    jb.add(RoundCone(v3((-0.3, 0, 1.6)) + v3((0.05, 0, 0)), tip, 0.008, 0.008), k=0.002)
    out.append(("Jib", jb, fine(0.004, 0.008), "crane"))
    hk = tip + v3((0.05, 0, -1.35))
    for k in range(14):
        q = tip + (hk - tip) * (k / 14) + v3((0.05, 0, -0.04))
        Rk = rot_from_axes(z_axis=(0, 1, 0)) if k % 2 == 0 else rot_from_axes(z_axis=(1, 0, 0))
        ch.add(Torus(q, 0.03, 0.009, R=Rk), k=0.002)
    ch.add(Torus(hk + v3((0.05, 0, -0.05)), 0.05, 0.016, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.004)
    ch.inter(Plane((0, 0, hk[2] - 0.12), (0, 0, -1)))
    out.append(("Chain", ch, fine(0.004, 0.008), "iron"))
    ld = Field("Load")
    ld.add(gear_fn(hk + v3((0.05, 0, -0.38)), (0, 1, 0), 0.3, 0.06, teeth=16, spokes=5), k=0.0)
    for sx in (-1, 1):
        ld.add(RoundCone(hk + v3((0.05, 0, -0.07)), hk + v3((0.05 + sx * 0.18, 0, -0.28)), 0.01, 0.01), k=0.0)
    out.append(("Load", ld, fine(0.005, 0.01), "cast_iron"))
    return out


# ------------------------------------------------------------------------------------------------ Railyard: scatter
def buffer_stop(seed=0):
    """A buffer stop at the end of a siding: the rails bent up into its frame, a red timber buffer beam with two
    buffers and a red lamp on it, ballast heaped behind."""
    out = []
    rail_track(out, -0.95, 0.42, 0.0, 0.34, seed)
    bf, bm = Field("Frame"), Field("Beam")
    for sy in (-1, 1):
        y = sy * 0.17
        bf.add(Chain([v3((0.25, y, 0.062)), v3((0.42, y, 0.1)), v3((0.5, y, 0.3)), v3((0.52, y, 0.44))], [0.02] * 4, k=0.02), k=0.0)
        bf.add(Chain([v3((0.52, y, 0.44)), v3((0.68, y, 0.3)), v3((0.86, y, 0.0))], [0.02] * 3, k=0.02), k=0.01)
    ground_cut(bf, -0.01)
    out.append(("Frame", bf, fine(0.005, 0.01), "rail"))
    bm.add(RoundBox((0.5, 0, 0.42), (0.065, 0.36, 0.08), 0.012), k=0.0, label=5)
    bm.paint(RoundBox((0.43, 0, 0.42), (0.03, 0.06, 0.1), 0.0), 7)
    for sy in (-1, 1):
        bm.add(RoundCone((0.43, sy * 0.24, 0.42), (0.33, sy * 0.24, 0.42), 0.035, 0.03), k=0.006, label=6)
        bm.add(Cylinder((0.32, sy * 0.24, 0.42), 0.065, 0.025, rr=0.008, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004, label=6)
        bm.add(RoundBox((0.56, sy * 0.17, 0.3), (0.06, 0.035, 0.08), 0.01), k=0.004, label=6)
    bm.add(RoundBox((0.5, 0.0, 0.54), (0.04, 0.05, 0.05), 0.01), k=0.004, label=6)
    bm.add(Cylinder((0.45, 0.0, 0.55), 0.035, 0.015, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.0, label=5)
    out.append(("Beam", bm, fine(0.005, 0.01), "timber"))
    bl = Field("Ballast")
    bl.add(Ellipsoid((0.85, 0, -0.02), (0.38, 0.45, 0.22), **wob(6.0, 0.02, seed)), k=0.0)
    ground_cut(bl, -0.01)
    out.append(("Ballast", bl, fine(0.006, 0.012), "ballast"))
    return out


def semaphore(seed=0):
    """A semaphore signal: a tapering timber post painted white on a black foot, its arm at danger (red, a white band
    near the tip) on the spectacle plate with its red and green glasses, the lamp behind them, a ladder up to a little
    platform, the finial on top; the balance lever and its weight at the foot."""
    out = []
    f, gl = Field("Post"), Field("Lenses")
    H = 1.85
    f.add(walls_box(0, 0, 0.055, 0.055, -0.05, H, batter=0.012, amp=0.0, seed=seed), k=0.0)
    f.paint(Func(lambda P: (P[:, 2] - F32(0.25)).astype(F32), (-1, -1, -0.2), (1, 1, 0.5)), 7)
    f.add(RoundBox((0, 0, H + 0.02), (0.05, 0.05, 0.02), 0.01), k=0.004, label=7)
    f.add(Sphere((0, 0, H + 0.08), 0.04), k=0.006, label=7)
    f.add(RoundCone((0, 0, H + 0.1), (0, 0, H + 0.2), 0.02, 0.003), k=0.004, label=7)
    za = 1.55
    f.add(leaf(v3((-0.04, -0.06, za)), (-1, 0, 0), (0, 0, 1), [(0.0, -0.04), (0.44, -0.035), (0.44, 0.035), (0.0, 0.04)], 0.009), k=0.0, label=5)
    f.paint(RoundBox((-0.36, -0.06, za), (0.025, 0.05, 0.05), 0.0), 0)
    f.add(RoundBox((0.04, -0.065, za - 0.05), (0.08, 0.008, 0.1), 0.01), k=0.004, label=7)        # the spectacle plate
    for zz in (za - 0.01, za - 0.11):
        f.sub(Cylinder((0.06, -0.065, zz), 0.03, 0.04, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.003)
    gl.add(Cylinder((0.06, -0.065, za - 0.01), 0.032, 0.008, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.0, label=5)
    gl.add(Cylinder((0.06, -0.065, za - 0.11), 0.032, 0.008, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.0, label=6)
    f.add(RoundBox((0.06, 0.0, za - 0.08), (0.05, 0.045, 0.07), 0.012), k=0.004, label=7)            # the lamp
    f.add(RoundCone((0.06, 0.0, za - 0.0), (0.06, 0.0, za + 0.06), 0.03, 0.015), k=0.004, label=7)
    f.add(RoundBox((0.0, 0.1, za - 0.25), (0.14, 0.1, 0.012), 0.004), k=0.004, label=7)              # the platform
    for sx in (-1, 1):
        f.add(RoundCone((sx * 0.07, 0.24, -0.03), (sx * 0.07, 0.17, za - 0.24), 0.008, 0.008), k=0.0, label=7)
    for k in range(11):
        t = (k + 0.5) / 11
        f.add(RoundCone((-0.07, 0.24 - 0.07 * t, (za - 0.24) * t), (0.07, 0.24 - 0.07 * t, (za - 0.24) * t), 0.006, 0.006), k=0.0, label=7)
    f.add(RoundCone((0.0, -0.08, 0.14), (0.32, -0.12, 0.1), 0.012, 0.012), k=0.004, label=7)        # the balance lever
    f.add(Sphere((0.3, -0.12, 0.1), 0.045), k=0.004, label=7)
    f.add(RoundCone((0.0, -0.06, 0.15), (-0.03, -0.065, za - 0.06), 0.005, 0.005), k=0.002, label=7)
    ground_cut(f)
    out += [("Post", f, fine(0.004, 0.008), "signal"), ("Lenses", gl, fine(0.004, 0.008), "lenses")]
    return out


def coal_tub(seed=0):
    """A chaldron coal tub on a short length of track: a tapering timber body, tarred black and strapped with iron,
    on four small iron wheels, heaped with coal."""
    out = []
    rail_track(out, -0.55, 0.55, 0.0, 0.34, seed, spacing=0.22)
    bd, wh, cl = Field("Body"), Field("Wheels"), Field("Coal")
    zb = 0.27
    bd.add(convex_w([((0, 0, zb + 0.34), (0, 0, 1)), ((0, 0, zb), (0, 0, -1)), ((0.3, 0, zb), (1, 0, -0.22)), ((-0.3, 0, zb), (-1, 0, -0.22)),
                     ((0, 0.2, zb), (0, 1, -0.2)), ((0, -0.2, zb), (0, -1, -0.2))], (-0.5, -0.4, zb - 0.1), (0.5, 0.4, zb + 0.45), 0.0), k=0.0, label=10)
    bd.sub(convex([((0, 0, zb + 0.5), (0, 0, 1)), ((0, 0, zb + 0.06), (0, 0, -1)), ((0.27, 0, zb), (1, 0, -0.22)), ((-0.27, 0, zb), (-1, 0, -0.22)),
                   ((0, 0.17, zb), (0, 1, -0.2)), ((0, -0.17, zb), (0, -1, -0.2))], (-0.5, -0.4, zb), (0.5, 0.4, zb + 0.6)), k=0.006)
    for x in (-0.18, 0.0, 0.18):
        for sy in (-1, 1):
            bd.add(RoundBox((x * (1 + 0.1), sy * (0.215 + 0.0), zb + 0.17), (0.014, 0.014, 0.18), 0.004, R=euler(sy * 0.2, 0, 0)), k=0.003, label=6)
    for sx in (-1, 1):
        bd.add(RoundBox((sx * 0.38, 0, zb - 0.02), (0.04, 0.12, 0.04), 0.01), k=0.004, label=10)
    bd.add(RoundBox((0, 0, zb - 0.03), (0.36, 0.14, 0.03), 0.008), k=0.004, label=6)
    out.append(("Body", bd, fine(0.005, 0.01), "tub"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            wh.add(rwheel_fn((sx * 0.2, sy * 0.17, 0.076 + 0.1), (0, sy, 0), 0.1, 0.035, spokes=6, counter=False), k=0.0)
        wh.add(RoundCone((sx * 0.2, -0.21, 0.176), (sx * 0.2, 0.21, 0.176), 0.016, 0.016), k=0.004)
    out.append(("Wheels", wh, fine(0.004, 0.008), "iron"))
    cl.add(Ellipsoid((0, 0, zb + 0.32), (0.3, 0.2, 0.14), **wob(14.0, 0.02, seed)), k=0.0)
    for k in range(6):
        a = 2 * math.pi * k / 6
        cl.add(Ellipsoid((math.cos(a) * 0.15, math.sin(a) * 0.09, zb + 0.4), (0.06, 0.05, 0.05), R=Rz(a)), k=0.01)
    cl.inter(Plane((0, 0, zb + 0.25), (0, 0, -1)))
    out.append(("Coal", cl, fine(0.005, 0.01), "coal"))
    return out


def sleeper_stack(seed=0):
    """A stack of old sleepers, crib-fashion in alternate courses, two more propped against it."""
    rng = np.random.default_rng(seed)
    f = Field("Sleepers")
    for L in range(5):
        z = 0.045 + L * 0.085
        for i in range(4):
            o = (i - 1.5) * 0.21
            if L % 2 == 0:
                c, R = (o, 0.0, z), Rz(math.pi / 2 + rng.uniform(-0.04, 0.04))
            else:
                c, R = (0.0, o, z), Rz(rng.uniform(-0.04, 0.04))
            f.add(RoundBox(c, (0.42, 0.06, 0.04), 0.008, R=R, **wob(14.0, 0.003, seed + L * 4 + i)), k=0.0, label=10)
    for k, (x, a) in enumerate(((0.62, 0.35), (0.6, -0.35))):
        R = Rz(math.pi / 2) @ euler(0, -0.0, 0) @ euler(a * 0.0, 0, 0)
        f.add(RoundBox((x, a * 0.6, 0.28), (0.04, 0.06, 0.32), 0.008, R=euler(0, -0.45, 0) @ Rz(a), **wob(14.0, 0.003, seed + 30 + k)), k=0.0, label=11)
    ground_cut(f)
    return [("Sleepers", f, fine(0.005, 0.01), "sleeper")]


def churns(seed=0):
    """Milk churns waiting on the platform, and a sack truck with two more on it."""
    rng = np.random.default_rng(seed)
    f, tr = Field("Churns"), Field("Truck")

    def churn(c, tilt=None):
        c = v3(c)
        R = np.eye(3) if tilt is None else tilt
        u = R @ Z
        f.add(RoundCone(c + u * 0.02, c + u * 0.22, 0.1, 0.095), k=0.0)
        f.add(RoundCone(c + u * 0.22, c + u * 0.3, 0.095, 0.05), k=0.02)
        f.add(RoundCone(c + u * 0.3, c + u * 0.36, 0.05, 0.055), k=0.01)
        f.add(Cylinder(c + u * 0.37, 0.065, 0.03, rr=0.01, R=R), k=0.006, label=6)
        f.add(Torus(c + u * 0.15, 0.1, 0.01, R=R), k=0.004)
        for s in (-1, 1):
            f.add(Torus(c + u * 0.27 + (R @ v3((s * 0.08, 0, 0))), 0.03, 0.008, R=R @ rot_from_axes(z_axis=(0, 1, 0))), k=0.004)
    for (x, y) in ((0.0, 0.0), (0.22, 0.06), (0.1, 0.22), (-0.16, 0.2)):
        churn((x, y, 0.0))
    tc = v3((0.5, -0.35, 0.0))                                      # the sack truck, tipped back on its wheels
    tilt = euler(0, -0.5, 0.3)
    u = tilt @ Z
    for s in (-1, 1):
        side = tilt @ v3((0, s * 0.13, 0))
        tr.add(RoundCone(tc + side + v3((0, 0, 0.09)), tc + side + u * 0.75, 0.015, 0.015), k=0.0, label=11)
        tr.add(Cylinder(tc + side * 1.25 + v3((0, 0, 0.09)), 0.09, 0.035, rr=0.01, R=rot_from_axes(z_axis=tilt @ v3((0, 1, 0)))), k=0.004, label=6)
    for k in range(3):
        tr.add(RoundCone(tc + v3((0, 0, 0.09)) + u * (0.25 + 0.2 * k) + tilt @ v3((0, -0.13, 0)), tc + v3((0, 0, 0.09)) + u * (0.25 + 0.2 * k) + tilt @ v3((0, 0.13, 0)),
                         0.01, 0.01), k=0.002, label=10)
    tr.add(RoundBox(tc + v3((0, 0, 0.09)) + tilt @ v3((0.06, 0, 0)), (0.07, 0.15, 0.012), 0.004, R=tilt), k=0.004, label=6)
    ground_cut(tr)
    out = [("Truck", tr, fine(0.004, 0.008), "timber")]
    ground_cut(f)
    out.append(("Churns", f, fine(0.004, 0.008), "churn"))
    return out


# ------------------------------------------------------------------------------------------------ Railyard: landmarks
def locomotive(seed=0):
    """An 0-6-0 tender engine standing on a siding: the corps' navy blue lined out in brass, red buffer beams and wheels;
    a black smokebox and chimney with a copper cap, a polished brass dome and safety valves, outside cylinders with their
    rods, the cab with its spectacle windows, the tender heaped with coal and the corps' brass cog on its side."""
    out = []
    rail_track(out, -2.05, 1.5, 0.0, 0.34, seed, spacing=0.21)
    bd, wh, rd, gl, dk, gw, cl = Field("Engine"), Field("Wheels"), Field("Rods"), Field("Glass"), Field("Dark"), Field("Lamps"), Field("Coal")
    zr = 0.076
    Rx = rot_from_axes(z_axis=(1, 0, 0))
    # frames, running plate, valances, buffer beams, buffers
    bd.add(RoundBox((0.05, 0, 0.32), (0.95, 0.1, 0.07), 0.01), k=0.0, label=7)
    bd.add(RoundBox((0.08, 0, 0.45), (1.0, 0.33, 0.014), 0.006), k=0.004)
    for sy in (-1, 1):
        bd.add(RoundBox((0.08, sy * 0.33, 0.42), (1.0, 0.012, 0.035), 0.004), k=0.003, label=5)
    for (x, sx) in ((1.07, 1), (-1.84, -1)):
        bd.add(RoundBox((x, 0, 0.38), (0.035, 0.33, 0.07), 0.01), k=0.004, label=5)
        for sy in (-1, 1):
            bd.add(RoundCone((x + sx * 0.03, sy * 0.24, 0.38), (x + sx * 0.13, sy * 0.24, 0.38), 0.03, 0.025), k=0.004, label=7)
            bd.add(Cylinder((x + sx * 0.145, sy * 0.24, 0.38), 0.06, 0.022, rr=0.008, R=Rx), k=0.004, label=7)
        bd.add(Torus((x + sx * 0.08, 0, 0.36), 0.03, 0.009, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.003, label=7)
    # the boiler, firebox, smokebox and its saddle, chimney, dome, safety valves
    bd.add(Cylinder((0.25, 0, 0.72), 0.24, 0.95, rr=0.02, R=Rx), k=0.0)
    for x in (-0.1, 0.25, 0.6):
        bd.add(Cylinder((x, 0, 0.72), 0.243, 0.025, rr=0.008, R=Rx), k=0.003, label=6)
    bd.add(RoundBox((-0.36, 0, 0.7), (0.16, 0.26, 0.26), 0.05), k=0.02)
    bd.add(Cylinder((0.85, 0, 0.72), 0.255, 0.28, rr=0.02, R=Rx), k=0.006, label=7)
    bd.add(Ellipsoid((0.99, 0, 0.72), (0.03, 0.22, 0.22)), k=0.01, label=7)
    bd.add(RoundCone((1.0, -0.06, 0.72), (1.0, 0.06, 0.72), 0.012, 0.012), k=0.004, label=6)
    bd.add(Sphere((1.02, 0, 0.72), 0.022), k=0.004, label=6)
    bd.add(RoundBox((0.85, 0, 0.55), (0.12, 0.15, 0.1), 0.02), k=0.02, label=7)
    bd.add(RoundCone((0.86, 0, 0.92), (0.86, 0, 1.2), 0.075, 0.068), k=0.03, label=7)
    bd.add(Torus((0.86, 0, 1.2), 0.07, 0.022), k=0.008, label=6)
    bd.add(RoundCone((0.25, 0, 0.9), (0.25, 0, 0.98), 0.13, 0.1), k=0.03, label=6)
    bd.add(Ellipsoid((0.25, 0, 0.99), (0.1, 0.1, 0.1)), k=0.02, label=6)
    bd.add(RoundCone((-0.3, 0, 0.92), (-0.3, 0, 1.06), 0.04, 0.03), k=0.02, label=6)
    bd.add(Ellipsoid((-0.3, 0, 1.06), (0.05, 0.05, 0.035)), k=0.01, label=6)
    bd.add(RoundCone((0.55, 0.0, 0.94), (0.55, 0.0, 1.0), 0.02, 0.016), k=0.01, label=6)            # the whistle
    # outside cylinders, slide bars
    for sy in (-1, 1):
        cy_c = v3((0.78, sy * 0.27, 0.33))
        bd.add(Cylinder(cy_c, 0.1, 0.34, rr=0.02, R=Rx), k=0.004)
        for dx in (-0.16, 0.16):
            bd.add(Cylinder(cy_c + v3((dx, 0, 0)), 0.105, 0.025, rr=0.008, R=Rx), k=0.003, label=6)
        rd.add(RoundCone(cy_c - v3((0.17, 0, 0)), v3((0.38, sy * 0.27, 0.33)), 0.012, 0.012), k=0.0)
        rd.add(RoundBox((0.4, sy * 0.27, 0.33), (0.04, 0.02, 0.03), 0.006), k=0.004)
        rd.add(RoundCone((0.4, sy * 0.28, 0.33), (0.0, sy * 0.28, zr + 0.2 + 0.08), 0.016, 0.014), k=0.004)       # connecting rod
        rd.add(RoundCone((0.45, sy * 0.3, zr + 0.2 - 0.07), (-0.45, sy * 0.3, zr + 0.2 - 0.07), 0.014, 0.014), k=0.004)   # coupling rod
        for x in (0.45, 0.0, -0.45):
            rd.add(Cylinder((x, sy * 0.29, zr + 0.2 - (0.07 if x != 0 else -0.08)), 0.02, 0.05, rr=0.006, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.003)
    # the cab
    for sy in (-1, 1):
        bd.add(RoundBox((-0.66, sy * 0.31, 0.78), (0.17, 0.016, 0.34), 0.01), k=0.004)
        bd.sub(RoundBox((-0.62, sy * 0.31, 0.88), (0.09, 0.05, 0.13), 0.03), k=0.004)
    bd.add(RoundBox((-0.49, 0, 0.84), (0.016, 0.31, 0.4), 0.01), k=0.004)
    for sy in (-1, 1):
        bd.sub(Cylinder((-0.49, sy * 0.17, 1.02), 0.06, 0.06, R=Rx), k=0.004)
        gl.add(Cylinder((-0.485, sy * 0.17, 1.02), 0.062, 0.012, R=Rx), k=0.0)
        bd.add(Torus((-0.47, sy * 0.17, 1.02), 0.062, 0.01, R=Rx), k=0.003, label=6)
    bd.add(Ellipsoid((-0.66, 0, 1.2), (0.22, 0.37, 0.07)), k=0.006)
    bd.inter(Plane((0, 0, 1.24), (0, 0, 1)))
    dk.add(RoundBox((-0.66, 0, 0.78), (0.16, 0.29, 0.32), 0.01), k=0.0)
    # the tender
    bd.add(RoundBox((-1.38, 0, 0.6), (0.44, 0.3, 0.2), 0.03), k=0.0)
    bd.add(RoundBox((-1.38, 0, 0.82), (0.44, 0.31, 0.025), 0.01), k=0.004, label=7)
    for sy in (-1, 1):
        bd.add(RoundBox((-1.38, sy * 0.3, 0.88), (0.42, 0.012, 0.05), 0.006), k=0.003)
        bd.add(RoundBox((-1.38, sy * 0.31, 0.37), (0.4, 0.015, 0.05), 0.006), k=0.003, label=7)
        for x in (-1.68, -1.38, -1.08):
            bd.add(RoundBox((x, sy * 0.24, 0.26), (0.045, 0.03, 0.05), 0.01), k=0.003, label=7)
            bd.add(RoundBox((x, sy * 0.25, 0.33), (0.1, 0.015, 0.015), 0.006), k=0.003, label=6)
        cog = v3((-1.38, sy * 0.305, 0.6))                          # the corps' brass cog
        bd.paint(Torus(cog, 0.08, 0.022, R=rot_from_axes(z_axis=(0, 1, 0))), 6)
        for k in range(8):
            a = 2 * math.pi * k / 8
            bd.paint(Sphere(cog + v3((math.cos(a) * 0.11, 0, math.sin(a) * 0.11)), 0.022), 6)
    for sy in (-1, 1):                                              # brass lining round the tender's panel and the cab side
        bd.paint(Func(lambda P, sy=sy: np.maximum(np.abs(np.maximum(np.abs(P[:, 0] + F32(1.38)) - F32(0.36), np.abs(P[:, 2] - F32(0.6)) - F32(0.13))) - F32(0.008),
                                                np.abs(P[:, 1] - F32(sy * 0.3)) - F32(0.05)).astype(F32), (-1.9, sy * 0.3 - 0.1, 0.3), (-0.8, sy * 0.3 + 0.1, 0.9)), 6)
    cl.add(Ellipsoid((-1.4, 0, 0.84), (0.38, 0.26, 0.12), **wob(14.0, 0.02, seed)), k=0.0)
    cl.inter(Plane((0, 0, 0.8), (0, 0, -1)))
    gw.add(RoundBox((1.09, 0.2, 0.5), (0.025, 0.035, 0.04), 0.01), k=0.0)
    gw.add(RoundBox((-1.86, -0.2, 0.5), (0.025, 0.035, 0.04), 0.01), k=0.0)
    for (x, sx) in ((1.09, 1), (-1.86, -1)):
        bd.add(RoundBox((x - sx * 0.02, sx * 0.2, 0.5), (0.03, 0.045, 0.05), 0.01), k=0.004, label=7)
    # the wheels: three coupled drivers, three tender axles
    for x in (0.45, 0.0, -0.45):
        for sy in (-1, 1):
            wh.add(rwheel_fn((x, sy * 0.19, zr + 0.2), (0, sy, 0), 0.2, 0.045, spokes=14), k=0.0)
    for x in (-1.68, -1.38, -1.08):
        for sy in (-1, 1):
            wh.add(rwheel_fn((x, sy * 0.19, zr + 0.13), (0, sy, 0), 0.13, 0.04, spokes=10, counter=False), k=0.0)
    ground_cut(bd)
    out += [("Engine", bd, fine(0.005, 0.01), "loco"), ("Wheels", wh, fine(0.004, 0.008), "loco_wheels"), ("Rods", rd, fine(0.004, 0.008), "steel"),
            ("Glass", gl, fine(0.004, 0.008), "glass"), ("Dark", dk, fine(0.006, 0.012), "dark"), ("Lamps", gw, fine(0.004, 0.008), "glow_lamp"),
            ("Coal", cl, fine(0.005, 0.01), "coal")]
    return out


def goods_wagon(seed=0, van=False):
    """A goods wagon on a length of track: an open wagon of grey planks heaped with coal (or, van: a covered van in red
    oxide under a curved white roof, its sliding door), iron strapping and corner plates, W-irons and leaf springs over
    its two axles, buffers at both ends, the owner's letters in white."""
    out = []
    rail_track(out, -0.95, 0.95, 0.0, 0.34, seed, spacing=0.21)
    bd, wh, ld = Field("Body"), Field("Wheels"), Field("Load")
    zr = 0.076
    L, W = 0.66, 0.31
    zb, zt = 0.32, (0.62 if not van else 0.88)
    bd.add(RoundBox((0, 0, (zb + zt) / 2), (L, W, (zt - zb) / 2), 0.012), k=0.0, label=10)
    if not van:
        bd.sub(RoundBox((0, 0, zt + 0.1), (L - 0.03, W - 0.03, (zt - zb) - 0.04 + 0.1), 0.01), k=0.004)
    for z in np.arange(zb + 0.07, zt - 0.02, 0.07):                # the planks' joints
        for sy in (-1, 1):
            bd.sub(RoundBox((0, sy * W, z), (L + 0.02, 0.006, 0.004), 0.0), k=0.0)
        for sx in (-1, 1):
            bd.sub(RoundBox((sx * L, 0, z), (0.006, W + 0.02, 0.004), 0.0), k=0.0)
    for x in (-L + 0.02, -0.22, 0.22, L - 0.02):                  # strapping
        for sy in (-1, 1):
            bd.add(RoundBox((x, sy * (W + 0.006), (zb + zt) / 2), (0.016, 0.008, (zt - zb) / 2), 0.004), k=0.002, label=6)
    for sy in (-1, 1):
        bd.add(RoundBox((0, sy * (W + 0.006), zt - 0.02), (L, 0.01, 0.016), 0.004), k=0.002, label=6)
        bd.add(RoundBox((0, sy * (W - 0.02), zb - 0.04), (L + 0.04, 0.025, 0.045), 0.006), k=0.003, label=5)       # solebars
        for i, x in enumerate((-0.42, -0.3, -0.18, 0.18)):          # the owner's letters
            bd.paint(RoundBox((x, sy * (W + 0.01), zt - 0.12), (0.035, 0.03, 0.045), 0.0), 7)
        if van:
            bd.add(RoundBox((0.0, sy * (W + 0.012), (zb + zt) / 2 + 0.02), (0.2, 0.012, (zt - zb) / 2 - 0.04), 0.006), k=0.002, label=10)
            bd.add(RoundBox((0.0, sy * (W + 0.02), zt - 0.03), (0.34, 0.01, 0.012), 0.004), k=0.002, label=6)
    for sx in (-1, 1):
        bd.add(RoundBox((sx * (L + 0.04), 0, zb - 0.02), (0.035, W + 0.02, 0.06), 0.01), k=0.004, label=5)
        for sy in (-1, 1):
            bd.add(RoundCone((sx * (L + 0.07), sy * 0.22, zb - 0.02), (sx * (L + 0.17), sy * 0.22, zb - 0.02), 0.026, 0.022), k=0.004, label=6)
            bd.add(Cylinder((sx * (L + 0.18), sy * 0.22, zb - 0.02), 0.05, 0.02, rr=0.006, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.003, label=6)
    for x in (-0.4, 0.4):                                           # W-irons, axleboxes, springs
        for sy in (-1, 1):
            bd.add(RoundBox((x, sy * 0.27, zb - 0.06), (0.05, 0.02, 0.045), 0.008), k=0.003, label=5)
            bd.add(Ellipsoid((x, sy * 0.28, zb - 0.02), (0.16, 0.02, 0.025)), k=0.003, label=6)
    ground_cut(bd)
    out.append(("Body", bd, fine(0.005, 0.01), "wagon_red" if van else "wagon_grey"))
    for x in (-0.4, 0.4):
        for sy in (-1, 1):
            wh.add(rwheel_fn((x, sy * 0.19, zr + 0.14), (0, sy, 0), 0.14, 0.04, spokes=8, counter=False), k=0.0)
        wh.add(RoundCone((x, -0.24, zr + 0.14), (x, 0.24, zr + 0.14), 0.02, 0.02), k=0.004)
    out.append(("Wheels", wh, fine(0.004, 0.008), "iron"))
    if van:
        rf = Field("Roof")
        rf.add(Func(lambda P: np.maximum(np.maximum(np.sqrt(P[:, 1] ** 2 + (P[:, 2] - F32(zt - 0.5)) ** 2) - F32(0.62), F32(zt - 0.02) - P[:, 2]),
                                         np.abs(P[:, 0]) - F32(L + 0.04)).astype(F32) * F32(0.9), (-L - 0.1, -0.5, zt - 0.1), (L + 0.1, 0.5, zt + 0.2)), k=0.0)
        out.append(("Roof", rf, fine(0.006, 0.012), "van_roof"))
    else:
        ld.add(Ellipsoid((0, 0, zt - 0.04), (L * 0.95, W * 0.92, 0.13), **wob(10.0, 0.02, seed)), k=0.0)
        for k in range(8):
            a = 2 * math.pi * k / 8 + 0.3
            ld.add(Ellipsoid((math.cos(a) * 0.4, math.sin(a) * 0.17, zt + 0.06), (0.07, 0.06, 0.05), R=Rz(a)), k=0.01)
        ld.inter(Plane((0, 0, zt - 0.1), (0, 0, -1)))
        out.append(("Load", ld, fine(0.005, 0.01), "coal"))
    return out


def signal_box(seed=0):
    """A signal box: a locking room of brick with round-headed windows, the operating floor above it in timber painted
    cream and brown, glazed all round with many small panes, under a hipped slate roof with iron finials, a stove pipe;
    a stair up its side to the door, the nameboard under the windows."""
    out = []
    hx, hy, z1, z2 = 0.62, 0.42, 0.62, 1.22
    wl, dk, fr, tb, dr = Field("Walls"), Field("Glass"), Field("Frames"), Field("Cabin"), Field("Door")
    wl.add(walls_box(0, 0, hx, hy, -0.05, z1, batter=0.0, amp=0.003, seed=seed), k=0.0)
    wl.paint(Func(lambda P: (P[:, 2] - F32(0.15)).astype(F32), (-2, -2, -0.2), (2, 2, 0.3)), 8)
    wl.add(RoundBox((0, 0, z1 - 0.02), (hx + 0.03, hy + 0.03, 0.03), 0.008), k=0.003, label=6)
    for x in (-0.36, 0.0, 0.36):
        window(wl, dk, fr, (x, -hy, 0.32), (0, -1, 0), 0.18, 0.26, arch=True)
    ground_cut(wl)
    out.append(("Walls", wl, fine(0.007, 0.014), "brick"))
    tb.add(RoundBox((0, 0, (z1 + z2) / 2), (hx + 0.02, hy + 0.02, (z2 - z1) / 2), 0.01), k=0.0, label=5)
    tb.paint(Func(lambda P: (P[:, 2] - F32(z1 + 0.2)).astype(F32), (-2, -2, z1 - 0.1), (2, 2, z1 + 0.3)), 7)
    for x in np.arange(-hx + 0.04, hx, 0.05):                        # boarding below the windows
        tb.sub(RoundBox((x, -hy - 0.02, z1 + 0.1), (0.003, 0.01, 0.1), 0.0), k=0.0)
    zw0, zw1 = z1 + 0.22, z2 - 0.06
    for sy in (-1, 1):
        tb.sub(RoundBox((0, sy * (hy + 0.02), (zw0 + zw1) / 2), (hx - 0.05, 0.04, (zw1 - zw0) / 2), 0.004), k=0.003)
        dk.add(RoundBox((0, sy * (hy - 0.005), (zw0 + zw1) / 2), (hx - 0.04, 0.008, (zw1 - zw0) / 2), 0.0), k=0.0)
        for x in np.linspace(-hx + 0.05, hx - 0.05, 9):
            fr.add(RoundBox((x, sy * (hy + 0.0), (zw0 + zw1) / 2), (0.01, 0.012, (zw1 - zw0) / 2), 0.003), k=0.0)
        fr.add(RoundBox((0, sy * (hy + 0.0), (zw0 + zw1) / 2 + 0.05), (hx - 0.05, 0.012, 0.008), 0.003), k=0.0)
    tb.sub(RoundBox((-hx - 0.02, -0.05, (zw0 + zw1) / 2), (0.04, hy - 0.08, (zw1 - zw0) / 2), 0.004), k=0.003)
    dk.add(RoundBox((-hx + 0.005, -0.05, (zw0 + zw1) / 2), (0.008, hy - 0.07, (zw1 - zw0) / 2), 0.0), k=0.0)
    for y in np.linspace(-hy + 0.05, hy - 0.15, 5):
        fr.add(RoundBox((-hx, y, (zw0 + zw1) / 2), (0.012, 0.01, (zw1 - zw0) / 2), 0.003), k=0.0)
    tb.add(RoundBox((0, -hy - 0.035, z1 + 0.13), (0.3, 0.012, 0.045), 0.006), k=0.003, label=7)       # the nameboard
    for i in range(6):
        tb.paint(RoundBox((-0.22 + i * 0.088, -hy - 0.05, z1 + 0.13), (0.022, 0.02, 0.026), 0.0), 5)
    doorway(tb, dr, (hx + 0.02, 0.2, z1), (1, 0, 0), 0.2, 0.46, depth=0.04, label=7, step=False)
    out += [("Cabin", tb, fine(0.006, 0.012), "box_timber"), ("Glass", dk, fine(0.006, 0.012), "glass"), ("Frames", fr, fine(0.004, 0.008), "frames"),
            ("Door", dr, fine(0.005, 0.01), "box_timber")]
    rf = Field("Roof")
    hipped(rf, (0, 0), hx + 0.02, hy + 0.02, z2, z2 + 0.32, over=0.12)
    out.append(("Roof", rf, fine(0.007, 0.014), "slate"))
    ir = Field("Iron")
    for sx in (-1, 1):
        ir.add(RoundCone((sx * (hx - hy + 0.0), 0, z2 + 0.3), (sx * (hx - hy), 0, z2 + 0.48), 0.014, 0.004), k=0.0)
        ir.add(Sphere((sx * (hx - hy), 0, z2 + 0.37), 0.025), k=0.004)
    ir.add(RoundCone((0.35, 0.25, z2), (0.35, 0.25, z2 + 0.62), 0.03, 0.03), k=0.0)
    ir.add(RoundCone((0.35, 0.25, z2 + 0.62), (0.35, 0.25, z2 + 0.7), 0.05, 0.02), k=0.004)
    sx0 = hx + 0.14                                                 # the stair and its landing
    ir.add(RoundBox((sx0 + 0.02, 0.2, z1 - 0.01), (0.14, 0.15, 0.015), 0.004), k=0.0)
    for k in range(7):
        t = (k + 0.5) / 7
        ir.add(RoundBox((sx0 + 0.06, -0.6 + 0.65 * t, z1 * t - 0.02), (0.1, 0.045, 0.012), 0.003), k=0.0)
    for sx in (-1, 1):
        ir.add(RoundCone((sx0 + 0.06 + sx * 0.1, -0.68, -0.03), (sx0 + 0.06 + sx * 0.1, 0.06, z1), 0.012, 0.012), k=0.0)
    ir.add(RoundCone((sx0 + 0.16, -0.66, 0.32), (sx0 + 0.16, 0.06, z1 + 0.3), 0.01, 0.01), k=0.0)
    ir.add(RoundCone((sx0 + 0.16, 0.06, z1 + 0.3), (sx0 + 0.16, 0.35, z1 + 0.3), 0.01, 0.01), k=0.0)
    for y in (-0.66, -0.3, 0.06, 0.35):
        ir.add(RoundCone((sx0 + 0.16, y, -0.02 + (z1 * (y + 0.68) / 0.74 if y < 0.07 else z1)), (sx0 + 0.16, y, min(z1, z1 * (y + 0.68) / 0.74) + 0.3), 0.008, 0.008), k=0.0)
    ground_cut(ir)
    out.append(("Iron", ir, fine(0.004, 0.008), "lamp_iron"))
    return out


def engine_shed(seed=0):
    """An engine shed: a long brick shed with its gable end to the yard, two round-arched doorways with tracks running
    in out of the dark, pilasters, a round window in the gable, tall arched windows down its sides, a slate roof with a
    long louvred smoke vent along its ridge."""
    out = []
    hx, hy, ze, zr = 1.1, 1.2, 1.3, 2.0
    wl, dk, fr = Field("Walls"), Field("Glass"), Field("Frames")
    wl.add(walls_box(0, 0, hx, hy, -0.05, ze, batter=0.0, amp=0.003, seed=seed), k=0.0)
    wl.add(gable((0, 0), hy, hx, ze - 0.05, zr - 0.03, axis="y"), k=0.0)
    wl.paint(Func(lambda P: (P[:, 2] - F32(0.22)).astype(F32), (-3, -3, -0.2), (3, 3, 0.4)), 8)
    for x in (-hx, 0.0, hx):                                        # pilasters on the gable end
        wl.add(RoundBox((x, -hy - 0.03, ze / 2), (0.08, 0.04, ze / 2), 0.006), k=0.003)
    wl.add(RoundBox((0, -hy - 0.035, ze + 0.0), (hx + 0.06, 0.045, 0.04), 0.008), k=0.003, label=6)
    for sx in (-1, 1):                                              # the gable's stone coping
        a = v3((sx * (hx + 0.06), -hy - 0.02, ze))
        b = v3((0, -hy - 0.02, zr - 0.02))
        t, _, n = frame(b - a)
        wl.add(RoundBox((a + b) / 2, (float(np.linalg.norm(b - a)) / 2 + 0.03, 0.06, 0.03), 0.008,
                        R=np.stack([t, np.cross(n, t), n], axis=1)), k=0.003, label=6)
    for sx in (-1, 1):
        doorway(wl, None, (sx * 0.52, -hy - 0.0, 0.0), (0, -1, 0), 0.68, 0.82, depth=0.35, arch=True, open_=True, dk=dk, step=False)
    oc = v3((0, -hy, 1.6))                                          # the round window
    Rc = rot_from_axes(z_axis=(0, 1, 0))
    wl.sub(Cylinder(oc, 0.16, 0.1, R=Rc), k=0.004)
    dk.add(Cylinder(oc + v3((0, 0.03, 0)), 0.165, 0.02, R=Rc), k=0.0)
    wl.paint(Torus(oc, 0.2, 0.04, R=Rc), 6)
    for k in range(2):
        a = k * math.pi / 2
        fr.add(RoundBox(oc + v3((0, 0.01, 0)), (0.16, 0.01, 0.01), 0.003, R=rot_from_axes(x_axis=(math.cos(a), 0, math.sin(a)))), k=0.0)
    for sx in (-1, 1):                                              # windows down the sides
        for y in np.linspace(-hy + 0.35, hy - 0.35, 4):
            window(wl, dk, fr, (sx * hx, y, 0.72), (sx, 0, 0), 0.26, 0.5, arch=True)
            wl.add(RoundBox((sx * (hx + 0.03), y + 0.29, ze / 2), (0.035, 0.07, ze / 2), 0.006), k=0.003)
    ground_cut(wl)
    out += [("Walls", wl, fine(0.01, 0.02), "brick"), ("Glass", dk, fine(0.008, 0.016), "glass"), ("Frames", fr, fine(0.004, 0.008), "frames")]
    rf = Field("Roof")
    zt = roof(rf, (0, 0), hy, hx, ze, zr, axis="y", over=0.1)
    out.append(("Roof", rf, fine(0.01, 0.02), "slate"))
    lv, vr = Field("Louvres"), Field("VentRoof")
    for sx in (-1, 1):
        for j in range(3):
            lv.add(RoundBox((sx * 0.16, 0, zt + 0.06 + j * 0.06), (0.012, hy * 0.75, 0.022), 0.004, R=euler(0, -sx * 0.5, 0)), k=0.0, label=0)
    for y in np.linspace(-hy * 0.75, hy * 0.75, 5):
        lv.add(RoundBox((0, y, zt + 0.1), (0.17, 0.02, 0.1), 0.004), k=0.002, label=10)
    roof(vr, (0, 0), hy * 0.78, 0.2, zt + 0.21, zt + 0.36, axis="y", over=0.04)
    out += [("Louvres", lv, fine(0.004, 0.008), "timber"), ("VentRoof", vr, fine(0.006, 0.012), "slate")]
    for sx in (-1, 1):                                              # the tracks out of the doorways
        trk = []
        rail_track(trk, -hy + 0.25 - 2.0, -hy + 0.25, 0.0, 0.34, seed + sx, spacing=0.21, name="T%d" % (sx + 1))
        place_parts(out, trk, (sx * 0.52, 0, 0), Rz(math.pi / 2), rename={n: n[2:] for (n, _, _, _) in trk})
    return out


SHED_SMOKE = [(0.0, -0.55, 2.45), (0.0, 0.55, 2.45)]    # the engine shed's smoke vent (Blender: x, y, z)


def coal_bin(seed=0):
    """A coal heap in a bin of old sleepers on edge between rail posts, a shovel stuck in it."""
    rng = np.random.default_rng(seed)
    out = []
    sl, ps, cl = Field("Sleepers"), Field("Posts"), Field("Coal")
    W, D = 0.95, 0.7
    for z in (0.08, 0.2, 0.32):
        sl.add(RoundBox((0, D, z), (W, 0.04, 0.06), 0.008, **wob(10.0, 0.003, seed + int(z * 10))), k=0.0, label=10)
        for sx in (-1, 1):
            sl.add(RoundBox((sx * W, D * 0.35, z), (0.04, D * 0.65, 0.06), 0.008, **wob(10.0, 0.003, seed + sx + int(z * 10))), k=0.0, label=0)
    ground_cut(sl)
    for (x, y) in ((-W - 0.06, D + 0.06), (W + 0.06, D + 0.06), (-W - 0.06, -0.1), (W + 0.06, -0.1), (0.0, D + 0.06)):
        ps.add(RoundBox((x, y, 0.2), (0.016, 0.03, 0.24), 0.006), k=0.0)
    ground_cut(ps)
    cl.add(Ellipsoid((0, 0.28, 0.0), (0.85, 0.5, 0.48), **wob(4.0, 0.04, seed)), k=0.0)
    cl.add(Ellipsoid((0.1, -0.25, 0.0), (0.6, 0.35, 0.2), **wob(5.0, 0.03, seed + 1)), k=0.08)
    for k in range(10):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.2, 0.75)
        cl.add(Ellipsoid((math.cos(a) * rr, 0.1 + math.sin(a) * rr * 0.6, 0.0), (0.07, 0.06, 0.05), R=Rz(a)), k=0.01)
    ground_cut(cl, -0.01)
    out += [("Sleepers", sl, fine(0.006, 0.012), "sleeper"), ("Posts", ps, fine(0.005, 0.01), "rail"), ("Coal", cl, fine(0.007, 0.014), "coal")]
    sh = Field("Shovel")
    a, b = v3((0.3, 0.05, 0.3)), v3((0.45, -0.1, 0.85))
    sh.add(RoundCone(a, b, 0.014, 0.014), k=0.0, label=11)
    sh.add(RoundCone(b, b + v3((0.04, -0.04, 0.06)), 0.03, 0.03), k=0.004, label=11)
    sh.add(RoundBox(a + v3((-0.03, 0.03, -0.12)), (0.09, 0.012, 0.11), 0.01, R=rot_from_axes(x_axis=(1, 0.3, 0), z_axis=unit(b - a))), k=0.006, label=6)
    out.append(("Shovel", sh, fine(0.004, 0.008), "timber"))
    return out


def staithe(seed=0):
    """A coal staithe: a timber stage on braced trestles, rails along its deck with a coal tub on them, a chute sloping
    from its edge, coal heaped and spilled beneath it, a ladder up."""
    rng = np.random.default_rng(seed)
    out = []
    wd, cl = Field("Stage"), Field("Coal")
    L, W, zd = 1.0, 0.45, 0.85
    for x in np.linspace(-L, L, 4):
        for sy in (-1, 1):
            post(wd, (x, sy * W, -0.05), (x, sy * W, zd), 0.035)
        wd.add(RoundCone((x, -W, 0.1), (x, W, zd - 0.12), 0.018, 0.018), k=0.002, label=10)
        wd.add(RoundCone((x, -W, zd - 0.06), (x, W, zd - 0.06), 0.03, 0.03), k=0.004, label=10)
    for sy in (-1, 1):
        wd.add(RoundCone((-L, sy * W, 0.1), (0, sy * W, zd - 0.1), 0.018, 0.018), k=0.002, label=10)
        wd.add(RoundCone((L, sy * W, 0.1), (0, sy * W, zd - 0.1), 0.018, 0.018), k=0.002, label=10)
    for y in np.arange(-W - 0.02, W + 0.04, 0.09):
        wd.add(RoundBox((0, y, zd), (L + 0.08, 0.042, 0.018), 0.004, **wob(12.0, 0.002, seed + int(y * 100))), k=0.0, label=10)
    ch = v3((0.0, -W - 0.02, zd - 0.02))                             # the chute
    t = unit((0, -0.8, -0.55))
    Rch = np.stack([v3((1, 0, 0)), t, np.cross((1, 0, 0), t)], axis=1)
    if Rch[2, 2] < 0:
        Rch[:, 2] = -Rch[:, 2]
    wd.add(RoundBox(ch + t * 0.32, (0.18, 0.32, 0.012), 0.004, R=Rch), k=0.0, label=0)
    for sx in (-1, 1):
        wd.add(RoundBox(ch + t * 0.32 + v3((sx * 0.18, 0, 0)) + Rch @ v3((0, 0, 0.05)), (0.012, 0.32, 0.05), 0.004, R=Rch), k=0.003, label=0)
    for sx in (-1, 1):
        wd.add(RoundCone((1.1, sx * 0.1, -0.03), (L + 0.05, sx * 0.1, zd + 0.02), 0.012, 0.012), k=0.0, label=11)
    for k in range(7):
        tt = (k + 0.5) / 7
        p = v3((1.1 - 0.05 * tt, 0, -0.03 + (zd + 0.05) * tt))
        wd.add(RoundCone(p - v3((0, 0.1, 0)), p + v3((0, 0.1, 0)), 0.008, 0.008), k=0.0, label=10)
    ground_cut(wd)
    out.append(("Stage", wd, fine(0.005, 0.01), "sleeper"))
    trk = []
    rail_track(trk, -L, L, 0.0, 0.34, seed, bed=False, spacing=0.3)
    place_parts(out, trk, (0, 0.05, zd + 0.0))
    tub = coal_tub(seed + 3)
    place_parts(out, [(n, f, v, m) for (n, f, v, m) in tub if not n.startswith("Track")], (0.35, 0.05, zd + 0.0), Rz(0.0), rename={"Coal": "TubCoal"})
    cl.add(Ellipsoid((0.0, -W - 0.45, 0.0), (0.62, 0.42, 0.4), **wob(4.0, 0.04, seed)), k=0.0)
    cl.add(Ellipsoid((-0.5, -0.2, 0.0), (0.45, 0.4, 0.2), **wob(5.0, 0.03, seed + 1)), k=0.08)
    for k in range(9):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.3, 0.8)
        cl.add(Ellipsoid((math.cos(a) * rr * 0.8, -W - 0.4 + math.sin(a) * rr * 0.45, 0.0), (0.07, 0.06, 0.05), R=Rz(a)), k=0.01)
    ground_cut(cl, -0.01)
    out.append(("Coal", cl, fine(0.007, 0.014), "coal"))
    return out


# ------------------------------------------------------------------------------------------------ Smog City: scatter
def lamp_standard(seed=0, h=1.45):
    """A gas lamp standard on its own (lit)."""
    return gas_lamp([], (0, 0, 0), h, seed)


def pillar_box(seed=0):
    """A pillar box: a red cast-iron column on a black plinth, its posting slot under the rim of a domed cap, the
    collection plate, a gilt band and a little gilt crown on top."""
    f = Field("Box")
    f.add(Cylinder((0, 0, 0.05), 0.135, 0.1, rr=0.02), k=0.0, label=5)
    f.add(Cylinder((0, 0, 0.32), 0.115, 0.46, rr=0.02), k=0.01)
    f.add(Torus((0, 0, 0.5), 0.12, 0.016), k=0.006)
    f.add(Ellipsoid((0, 0, 0.55), (0.135, 0.135, 0.07)), k=0.01)
    f.add(Torus((0, 0, 0.53), 0.13, 0.014), k=0.004, label=6)
    f.add(Sphere((0, 0, 0.64), 0.03), k=0.01, label=6)
    f.add(RoundCone((0, 0, 0.66), (0, 0, 0.71), 0.016, 0.004), k=0.004, label=6)
    f.sub(RoundBox((0, -0.115, 0.44), (0.055, 0.03, 0.009), 0.004), k=0.002)
    f.paint(RoundBox((0, -0.115, 0.44), (0.07, 0.05, 0.02), 0.0), 5)
    f.add(RoundBox((0, -0.11, 0.32), (0.045, 0.015, 0.035), 0.008), k=0.002, label=7)
    f.add(RoundBox((0, -0.11, 0.2), (0.025, 0.015, 0.03), 0.008), k=0.002, label=6)
    ground_cut(f)
    return [("Box", f, fine(0.004, 0.008), "pillar")]


def bench(seed=0):
    """A park bench: two scrolled cast-iron ends painted green, slatted seat and back of oiled wood."""
    out = []
    ir, wd = Field("Ends"), Field("Slats")
    L = 0.45
    for sx in (-1, 1):
        x = sx * (L - 0.04)
        leg = [v3((x, -0.17, 0.0)), v3((x, -0.16, 0.12)), v3((x, -0.12, 0.22)), v3((x, -0.17, 0.33)), v3((x, -0.13, 0.37))]
        ir.add(Chain(leg, [0.016, 0.014, 0.013, 0.013, 0.012], k=0.01), k=0.0)
        bk = [v3((x, 0.15, 0.0)), v3((x, 0.12, 0.2)), v3((x, 0.14, 0.4)), v3((x, 0.19, 0.6)), v3((x, 0.16, 0.66))]
        ir.add(Chain(bk, [0.016, 0.014, 0.013, 0.012, 0.012], k=0.01), k=0.0)
        ir.add(RoundCone((x, -0.15, 0.22), (x, 0.13, 0.22), 0.014, 0.014), k=0.006)
        ir.add(Torus((x, -0.12, 0.36), 0.03, 0.009, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004)
        ir.add(Torus((x, 0.17, 0.66), 0.025, 0.008, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004)
    ground_cut(ir)
    for y in (-0.11, -0.04, 0.03, 0.1):
        wd.add(RoundBox((0, y, 0.24), (L, 0.03, 0.012), 0.006), k=0.0, label=10)
    for z in (0.38, 0.5):
        wd.add(RoundBox((0, 0.14 + (z - 0.38) * 0.2, z), (L, 0.01, 0.035), 0.006, R=euler(-0.25, 0, 0)), k=0.0, label=10)
    out += [("Ends", ir, fine(0.004, 0.008), "lamp_iron"), ("Slats", wd, fine(0.004, 0.008), "timber")]
    return out


def railings(seed=0):
    """A run of iron railings with gilt spear heads on a brick dwarf wall with a stone coping, a pier at each end."""
    out = []
    wl, ir = Field("Wall"), Field("Railings")
    L = 0.82
    wl.add(walls_box(0, 0, L, 0.07, -0.05, 0.18, batter=0.0, amp=0.003, seed=seed), k=0.0)
    wl.add(RoundBox((0, 0, 0.19), (L, 0.09, 0.02), 0.008), k=0.003, label=6)
    for sx in (-1, 1):
        wl.add(walls_box(sx * (L + 0.05), 0, 0.08, 0.1, -0.05, 0.72, batter=0.0, amp=0.003, seed=seed + sx), k=0.0)
        wl.add(RoundBox((sx * (L + 0.05), 0, 0.73), (0.1, 0.12, 0.025), 0.008), k=0.003, label=6)
        wl.add(pyramid_roof((sx * (L + 0.05), 0), 0.09, 0.75, 0.82), k=0.003, label=6)
    ground_cut(wl)
    out.append(("Wall", wl, fine(0.005, 0.01), "brick"))
    for x in np.arange(-L + 0.04, L - 0.02, 0.07):
        ir.add(RoundCone((x, 0, 0.2), (x, 0, 0.6), 0.008, 0.008), k=0.0)
        ir.add(RoundCone((x, 0, 0.6), (x, 0, 0.66), 0.018, 0.002), k=0.004, label=6)
    for z in (0.26, 0.55):
        ir.add(RoundBox((0, 0, z), (L, 0.008, 0.012), 0.004), k=0.003)
    out.append(("Railings", ir, fine(0.003, 0.006), "black_iron"))
    return out


def plane_tree(h=3.2, seed=0, guard=False):
    """A London plane: a tall straight trunk in mottled flaking bark, soot-black low down, branching high into upswept
    limbs under a tall domed crown of dull sooty green, seed balls hanging; guard: an iron tree guard round its foot."""
    rng = np.random.default_rng(seed)
    s = h / 3.2
    f, c, sd = Field("Trunk"), Field("Leaves"), Field("Seeds")
    r0 = 0.12 * s
    fork = h * 0.48
    f.add(RoundCone((0, 0, -0.06), (0, 0, fork), r0, r0 * 0.75, **wob(4.0 / s, 0.012 * s, seed)), k=0.0)
    for k in range(4):
        a = 2 * math.pi * k / 4 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((math.cos(a) * r0 * 0.4, math.sin(a) * r0 * 0.4, 0.12 * s), (math.cos(a) * r0 * 1.9, math.sin(a) * r0 * 1.9, -0.04), r0 * 0.45, r0 * 0.2), k=0.05 * s)
    tops = []
    a0 = rng.uniform(0, 2 * math.pi)
    for i in range(4):
        a = a0 + 2 * math.pi * i / 4 + rng.uniform(-0.3, 0.3)
        out_ = v3((math.cos(a), math.sin(a), 0.0))
        p0 = v3((0, 0, fork - 0.05 * s))
        p1 = p0 + out_ * 0.28 * s + v3((0, 0, 0.45 * s))
        p2 = p1 + out_ * 0.3 * s + v3((0, 0, 0.5 * s))
        f.add(Chain([p0, p1, p2], [r0 * 0.6, r0 * 0.42, r0 * 0.2], k=0.03 * s, **wob(5.0 / s, 0.01 * s, seed * 10 + i)), k=0.05 * s)
        tops += [p1 + out_ * 0.15 * s + v3((0, 0, 0.1 * s)), p2]
    tops.append(v3((0, 0, h * 0.9)))
    ctr = sum(tops, v3((0, 0, 0))) / len(tops)
    for j, q in enumerate(tops):
        for k in range(3):
            o = v3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.6))) * 0.2 * s
            r = s * rng.uniform(0.26, 0.36)
            c.add(Ellipsoid(q + o, (r, r * 0.92, r * 0.8), **wob(10.0 / s, 0.045 * s, seed * 100 + j * 3 + k)), k=0.07 * s)
    for j in range(9):
        u = rng.normal(size=3)
        u = u / np.linalg.norm(u)
        q = ctr + v3((u[0] * 0.55 * s, u[1] * 0.55 * s, abs(u[2]) * 0.45 * s + 0.1 * s))
        r = s * rng.uniform(0.3, 0.4)
        c.add(Ellipsoid(q, (r, r * 0.92, r * 0.8), **wob(10.0 / s, 0.045 * s, seed * 200 + j)), k=0.08 * s)
    for j in range(10):                                             # seed balls hanging under the crown's rim
        a = 2 * math.pi * j / 10 + rng.uniform(-0.2, 0.2)
        q = ctr + v3((math.cos(a) * 0.62 * s, math.sin(a) * 0.62 * s, -0.42 * s + rng.uniform(-0.05, 0.05)))
        sd.add(Sphere(q, 0.03 * s), k=0.0)
        sd.add(RoundCone(q, q + v3((0, 0, 0.12 * s)), 0.004, 0.004), k=0.004)
    out = [("Trunk", f, fine(0.007, 0.014), "plane_bark"), ("Leaves", c, vx(h) * 0.9, "soot_leaves"), ("Seeds", sd, fine(0.004, 0.008), "weed_stem")]
    if guard:
        gd = Field("Guard")
        for k in range(14):
            a = 2 * math.pi * k / 14
            gd.add(RoundCone((math.cos(a) * 0.3, math.sin(a) * 0.3, -0.03), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.55), 0.008, 0.008), k=0.0)
            gd.add(RoundCone((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.55), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.6), 0.016, 0.002), k=0.004, label=6)
        for z in (0.12, 0.5):
            gd.add(Torus((0, 0, z), 0.3, 0.01), k=0.003)
        ground_cut(gd)
        out.append(("Guard", gd, fine(0.003, 0.006), "black_iron"))
    return out


def pot_pile(seed=0):
    """A builder's pile in the street: a pallet stacked with new bricks, three chimney pots standing by it (one with a
    cowl), another lying broken, a heap of sand."""
    rng = np.random.default_rng(seed)
    out = []
    pl, bk, pt, sd = Field("Pallet"), Field("Bricks"), Field("Pots"), Field("Sand")
    for x in (-0.2, 0.0, 0.2):
        pl.add(RoundBox((x, 0, 0.03), (0.03, 0.26, 0.03), 0.006), k=0.0, label=11)
    for y in np.linspace(-0.22, 0.22, 5):
        pl.add(RoundBox((0, y, 0.07), (0.27, 0.035, 0.01), 0.004), k=0.0, label=10)
    ground_cut(pl)
    for L in range(4):
        for i in range(2):
            for j in range(3):
                if L == 3 and j == 2:
                    continue
                c = v3((-0.12 + i * 0.24 if L % 2 == 0 else -0.14 + j * 0.14, -0.14 + j * 0.14 if L % 2 == 0 else -0.12 + i * 0.24, 0.12 + L * 0.075))
                bk.add(RoundBox(c, (0.11, 0.06, 0.034) if L % 2 == 0 else (0.06, 0.11, 0.034), 0.006), k=0.0)
    out += [("Pallet", pl, fine(0.005, 0.01), "timber"), ("Bricks", bk, fine(0.005, 0.01), "brick")]
    for k, (x, y, h, cowl) in enumerate(((0.45, 0.05, 0.42, False), (0.5, -0.25, 0.36, True), (0.38, 0.3, 0.3, False))):
        q = v3((x, y, 0.0))
        pt.add(RoundCone(q, q + Z * h, 0.09, 0.065), k=0.0)
        pt.add(Torus(q + Z * (h - 0.005), 0.062, 0.016), k=0.004)
        pt.add(Torus(q + Z * 0.04, 0.09, 0.016), k=0.004)
        pt.sub(Cylinder(q + Z * (h + 0.02), 0.045, 0.1), k=0.004)
        if cowl:
            pt.add(Ellipsoid(q + Z * (h + 0.07), (0.07, 0.07, 0.07)), k=0.01, label=5)
            pt.sub(Cylinder(q + Z * (h + 0.07) + v3((0.05, 0, 0)), 0.04, 0.12, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004)
    q = v3((-0.1, -0.45, 0.075))
    pt.add(RoundCone(q, q + v3((0.34, -0.06, 0.0)), 0.08, 0.06), k=0.0)
    pt.sub(Cylinder(q + v3((0.17, -0.03, 0)), 0.05, 0.6, R=rot_from_axes(z_axis=(1, -0.18, 0))), k=0.004)
    pt.sub(Ellipsoid(q + v3((0.33, -0.06, 0.05)), (0.1, 0.12, 0.06)), k=0.01)
    ground_cut(pt)
    out.append(("Pots", pt, fine(0.005, 0.01), "pottery"))
    sd.add(Ellipsoid((-0.55, 0.15, 0.0), (0.26, 0.22, 0.16), **wob(8.0, 0.015, seed)), k=0.0)
    ground_cut(sd, -0.01)
    out.append(("Sand", sd, fine(0.006, 0.012), "sand"))
    return out


# ------------------------------------------------------------------------------------------------ Smog City: landmarks
def terrace(seed=0, n=3):
    """A row of terraced brick houses: two storeys under a slate roof, chimney stacks with their pots on the party
    walls, each house a panelled front door in its own colour under a fanlight, a stone step, a bay window with its own
    little slate roof, sash windows above with stone sills and lintels, a stone string course, iron downpipes; a lamp
    lit behind a window or two; the flagged pavement in front."""
    rng = np.random.default_rng(seed)
    out = []
    w = 0.95
    hx, hy, z1, ze, zr = n * w / 2, 0.5, 0.72, 1.42, 1.92
    wl, dk, fr, dr, gw = Field("Walls"), Field("Glass"), Field("Frames"), Field("Doors"), Field("Lit")
    wl.add(walls_box(0, 0, hx, hy, -0.05, ze, batter=0.0, amp=0.003, seed=seed), k=0.0)
    wl.add(gable((0, 0), hx, hy, ze - 0.05, zr - 0.04, axis="x"), k=0.0)
    wl.add(RoundBox((0, 0, z1), (hx + 0.012, hy + 0.012, 0.022), 0.006), k=0.002, label=6)
    wl.paint(Func(lambda P: (P[:, 2] - F32(0.1)).astype(F32), (-3, -2, -0.2), (3, 2, 0.3)), 7)
    labels = [5, 7, 10, 5, 7]
    lit = rng.permutation(n * 2)[:2]
    br = Field("Bays")
    bf = Field("BayRoofs")
    for i in range(n):
        xc = -hx + w * (i + 0.5)
        doorway(wl, dr, (xc - 0.24, -hy, 0.0), (0, -1, 0), 0.2, 0.42, depth=0.05, arch=True, label=labels[i % len(labels)])
        bx = xc + 0.16
        br.add(RoundBox((bx, -hy - 0.07, 0.34), (0.2, 0.08, 0.34), 0.01), k=0.0)
        br.add(RoundBox((bx, -hy - 0.07, 0.03), (0.21, 0.09, 0.04), 0.01), k=0.004, label=8)
        window(br, dk, fr, (bx, -hy - 0.15, 0.4), (0, -1, 0), 0.22, 0.36, depth=0.03)
        for sx in (-1, 1):
            window(br, dk, fr, (bx + sx * 0.2, -hy - 0.07, 0.4), (sx, 0, 0), 0.07, 0.36, depth=0.025, sill=False, head=False)
        bf.add(convex([((bx, -hy - 0.17, 0.68), (0, -1, 1.4)), ((bx + 0.22, -hy, 0.68), (1, 0, 1.4)), ((bx - 0.22, -hy, 0.68), (-1, 0, 1.4)),
                       ((bx, -hy, 0.66), (0, 0, -1)), ((bx, -hy + 0.02, 0), (0, 1, 0))], (bx - 0.4, -hy - 0.4, 0.6), (bx + 0.4, -hy + 0.1, 0.9)), k=0.0)
        for j, x in enumerate((xc - 0.24, xc + 0.16)):
            idx = i * 2 + j
            window(wl, dk, fr, (x, -hy, 1.07), (0, -1, 0), 0.2, 0.36, pane=gw if idx in lit else None)
        window(wl, dk, fr, (xc, hy, 1.07), (0, 1, 0), 0.2, 0.34)
        window(wl, dk, fr, (xc, hy, 0.4), (0, 1, 0), 0.2, 0.34)
    ground_cut(wl)
    ground_cut(br)
    out += [("Walls", wl, fine(0.01, 0.018), "brick"), ("Bays", br, fine(0.006, 0.012), "brick"), ("BayRoofs", bf, fine(0.005, 0.01), "slate"),
            ("Glass", dk, fine(0.005, 0.01), "glass"), ("Frames", fr, fine(0.004, 0.008), "frames"), ("Doors", dr, fine(0.005, 0.01), "door"),
            ("Lit", gw, fine(0.005, 0.01), "glow_lamp")]
    rf = Field("Roof")
    roof(rf, (0, 0), hx, hy, ze, zr, over=0.08)
    out.append(("Roof", rf, fine(0.008, 0.016), "slate"))
    st, pt = Field("Stacks"), Field("Pots")
    for k in range(n + 1):
        x = -hx + w * k
        x = max(-hx + 0.12, min(hx - 0.12, x))
        stack(st, pt, (x, 0.0), 0.11, 0.2, zr - 0.25, zr + 0.32, pots=3 if 0 < k < n else 2, seed=seed + k)
    out += [("Stacks", st, fine(0.006, 0.012), "brick"), ("Pots", pt, fine(0.004, 0.008), "pottery")]
    ip = Field("Pipes")
    for k in range(1, n):
        x = -hx + w * k
        ip.add(RoundCone((x, -hy - 0.025, 0.02), (x, -hy - 0.025, ze - 0.02), 0.014, 0.014), k=0.0)
        ip.add(RoundBox((x, -hy - 0.035, ze - 0.02), (0.035, 0.03, 0.03), 0.006), k=0.004)
    ip.add(RoundBox((0, -hy - 0.09, ze + 0.0), (hx + 0.08, 0.025, 0.02), 0.01), k=0.0)
    ground_cut(ip)
    out.append(("Pipes", ip, fine(0.004, 0.008), "black_iron"))
    pv = Field("Pavement")
    pv.add(RoundBox((0, -hy - 0.38, 0.0), (hx + 0.1, 0.36, 0.03), 0.01), k=0.0)
    pv.add(RoundBox((0, -hy - 0.74, 0.0), (hx + 0.1, 0.04, 0.045), 0.01), k=0.004, label=7)
    ground_cut(pv, -0.02)
    out.append(("Pavement", pv, fine(0.012, 0.024), "flags"))
    return out


def pub(seed=0):
    """A corner pub: the ground floor faced in dark green glazed tile, its big windows lit warm behind their bars, the
    door under the gilt-lettered fascia, the sign hanging from an iron bracket on the corner, a gas lamp over the door;
    brick above with sash windows, a hipped slate roof and its stacks; casks by the cellar flaps on the pavement."""
    out = []
    hx, hy, z1, ze = 0.72, 0.52, 0.8, 1.55
    wl, dk, fr, dr, gw = Field("Walls"), Field("Glass"), Field("Frames"), Field("Door"), Field("Lit")
    wl.add(walls_box(0, 0, hx, hy, -0.05, ze, batter=0.0, amp=0.003, seed=seed), k=0.0)
    wl.paint(Func(lambda P: (P[:, 2] - F32(z1)).astype(F32), (-2, -2, -0.2), (2, 2, z1 + 0.2)), 9)
    wl.add(RoundBox((0, 0, 0.05), (hx + 0.02, hy + 0.02, 0.06), 0.01), k=0.003, label=8)
    for x in (-hx, -0.12, hx):                                      # tiled pilasters
        wl.add(RoundBox((x, -hy - 0.025, z1 / 2), (0.045, 0.035, z1 / 2), 0.008), k=0.003, label=9)
    wl.add(RoundBox((-hx - 0.025, 0.0, z1 / 2), (0.035, 0.045, z1 / 2), 0.008), k=0.003, label=9)
    wl.add(RoundBox((0, 0, ze - 0.03), (hx + 0.04, hy + 0.04, 0.035), 0.008), k=0.003, label=6)
    for x in (-0.42, 0.22):
        window(wl, dk, fr, (x, -hy, 0.42), (0, -1, 0), 0.34 if x < 0 else 0.22, 0.44, pane=gw, sill=True, head=False, dress=8)
    window(wl, dk, fr, (-hx, 0.0, 0.42), (-1, 0, 0), 0.4, 0.44, pane=gw, head=False, dress=8)
    doorway(wl, dr, (0.52, -hy, 0.0), (0, -1, 0), 0.2, 0.5, depth=0.05, label=7)
    for x in (-0.4, 0.0, 0.4):
        window(wl, dk, fr, (x, -hy, 1.17), (0, -1, 0), 0.2, 0.38)
    for y in (-0.22, 0.22):
        window(wl, dk, fr, (-hx, y, 1.17), (-1, 0, 0), 0.2, 0.38)
    ground_cut(wl)
    out += [("Walls", wl, fine(0.008, 0.016), "brick"), ("Glass", dk, fine(0.005, 0.01), "glass"), ("Frames", fr, fine(0.004, 0.008), "frames"),
            ("Door", dr, fine(0.005, 0.01), "door"), ("Lit", gw, fine(0.005, 0.01), "glow_lamp")]
    fs = Field("Fascia")
    fs.add(RoundBox((0, -hy - 0.05, z1 + 0.04), (hx + 0.06, 0.03, 0.06), 0.01), k=0.0)
    fs.add(RoundBox((-hx - 0.05, 0, z1 + 0.04), (0.03, hy + 0.06, 0.06), 0.01), k=0.0)
    fs.add(RoundBox((0, -hy - 0.07, z1 + 0.11), (hx + 0.08, 0.04, 0.015), 0.006), k=0.004)
    for i in range(9):
        fs.paint(RoundBox((-0.5 + i * 0.1, -hy - 0.09, z1 + 0.04), (0.028, 0.03, 0.03), 0.0), 5)
    sg = v3((-hx - 0.04, -hy - 0.04, 1.2))                           # the hanging sign
    fs.add(RoundCone(sg, sg + v3((-0.22, -0.22, 0)), 0.012, 0.012), k=0.0)
    fs.add(RoundCone(sg - Z * 0.14, sg + v3((-0.16, -0.16, -0.01)), 0.009, 0.009), k=0.0)
    bc = sg + v3((-0.16, -0.16, -0.2))
    fs.add(RoundBox(bc, (0.15, 0.17, 0.014), 0.01, R=rot_from_axes(x_axis=unit((1, 1, 0)), z_axis=unit((1, -1, 0)))), k=0.0)
    for sgn in (-1, 1):
        fs.add(RoundCone(bc + v3((sgn * 0.08, sgn * 0.08, 0.17)), bc + v3((sgn * 0.08, sgn * 0.08, 0.2)), 0.006, 0.006), k=0.0)
    fs.paint(Torus(bc, 0.08, 0.02, R=rot_from_axes(z_axis=unit((1, -1, 0)))), 5)
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = rot_from_axes(z_axis=unit((1, -1, 0))) @ v3((math.cos(a), math.sin(a), 0))
        fs.paint(Sphere(bc + d * 0.11, 0.022), 5)
    out.append(("Fascia", fs, fine(0.004, 0.008), "sign"))
    rf = Field("Roof")
    hipped(rf, (0, 0), hx, hy, ze, ze + 0.42, over=0.08)
    out.append(("Roof", rf, fine(0.008, 0.016), "slate"))
    st, pt = Field("Stacks"), Field("Pots")
    stack(st, pt, (-0.35, 0.3), 0.14, 0.1, ze + 0.1, ze + 0.72, pots=3, seed=seed)
    stack(st, pt, (0.4, 0.3), 0.12, 0.1, ze + 0.1, ze + 0.66, pots=2, seed=seed + 1)
    out += [("Stacks", st, fine(0.006, 0.012), "brick"), ("Pots", pt, fine(0.004, 0.008), "pottery")]
    lp = []
    gas_lamp(lp, (0, 0, 0), seed=seed, name="Door", standard=False)
    place_parts(out, lp, (0.52, -hy - 0.12, 0.94))
    br = Field("Bracket")
    br.add(RoundCone((0.52, -hy - 0.0, 0.92), (0.52, -hy - 0.12, 0.92), 0.01, 0.01), k=0.0)
    br.add(RoundCone((0.52, -hy - 0.0, 0.8), (0.52, -hy - 0.1, 0.9), 0.008, 0.008), k=0.0)
    out.append(("Bracket", br, fine(0.004, 0.008), "lamp_iron"))
    pv = Field("Pavement")
    pv.add(RoundBox((0.0, -hy - 0.3, 0.0), (hx + 0.32, 0.3, 0.03), 0.01), k=0.0)
    pv.add(RoundBox((-hx - 0.3, 0.1, 0.0), (0.3, hy + 0.4, 0.03), 0.01), k=0.0)
    ground_cut(pv, -0.02)
    out.append(("Pavement", pv, fine(0.012, 0.024), "flags"))
    cf = Field("Flaps")
    cf.add(RoundBox((-0.1, -hy - 0.22, 0.04), (0.2, 0.13, 0.012), 0.006), k=0.0, label=10)
    cf.add(RoundBox((-0.1, -hy - 0.22, 0.054), (0.004, 0.13, 0.004), 0.002), k=0.0, label=6)
    out.append(("Flaps", cf, fine(0.004, 0.008), "timber"))
    bb = Field("Casks")
    add_barrel(bb, (0.25, -hy - 0.3, 0.17), hl=0.16, r_end=0.12)
    add_barrel(bb, (-0.42, -hy - 0.3, 0.13), R=rot_from_axes(z_axis=(1, 0.3, 0)), hl=0.16, r_end=0.11)
    ground_cut(bb)
    out.append(("Casks", bb, fine(0.005, 0.01), "cask"))
    return out


PUB_SMOKE = (-0.35, 0.3, 2.35)


def clock_face(f, c, nrm, r=0.2):
    """A clock face (field f, material 'clock'): a cream dial with black hour marks and hands at ten past ten, a gilt
    bezel (label 6)."""
    c = v3(c)
    n = unit(nrm)
    Rc = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
    f.add(Cylinder(c, r, 0.02, rr=0.005, R=Rc), k=0.0)
    f.add(Torus(c + n * 0.008, r, 0.018, R=Rc), k=0.004, label=6)
    for k in range(12):
        a = 2 * math.pi * k / 12
        d = Rc @ v3((math.cos(a), math.sin(a), 0))
        f.paint(Sphere(c + n * 0.01 + d * r * 0.8, r * (0.07 if k % 3 == 0 else 0.045)), 5)
    for ang, L in ((math.radians(150), 0.5), (math.radians(30), 0.72)):
        d = Rc @ v3((math.cos(ang), math.sin(ang), 0))
        f.add(RoundCone(c + n * 0.012, c + n * 0.012 + d * r * L, 0.012, 0.006), k=0.0, label=5)
    f.add(Sphere(c + n * 0.014, 0.016), k=0.003, label=5)


def clock_tower(seed=0):
    """A clock tower: a square brick shaft on a stone plinth with stone quoins and string courses, a door and tall
    round-headed windows; the clock stage with a face on every side under a stone cornice, a belfry of louvred arches,
    a steep slate spire with iron cresting, a gilt weathervane."""
    out = []
    S, H1, H2, H3 = 0.3, 2.25, 2.85, 3.25
    wl, dk, fr, dr = Field("Walls"), Field("Glass"), Field("Frames"), Field("Door")
    wl.add(walls_box(0, 0, S, S, -0.05, H3, batter=0.0, amp=0.002, seed=seed), k=0.0)
    wl.add(walls_box(0, 0, S + 0.05, S + 0.05, -0.05, 0.32, batter=0.0, amp=0.002, seed=seed + 1), k=0.006, label=6)
    for z in (1.15, H1):
        wl.add(RoundBox((0, 0, z), (S + 0.03, S + 0.03, 0.025), 0.006), k=0.003, label=6)
    wl.add(RoundBox((0, 0, (H1 + H2) / 2), (S + 0.04, S + 0.04, (H2 - H1) / 2), 0.008), k=0.004)
    wl.add(RoundBox((0, 0, H2), (S + 0.07, S + 0.07, 0.035), 0.008), k=0.003, label=6)
    wl.add(RoundBox((0, 0, H3), (S + 0.06, S + 0.06, 0.03), 0.008), k=0.003, label=6)
    for sx in (-1, 1):                                              # quoins
        for sy in (-1, 1):
            for k in range(11):
                z = 0.4 + k * 0.17
                big = k % 2 == 0
                wl.add(RoundBox((sx * (S - (0.03 if big else 0.02)), sy * (S - (0.02 if big else 0.03)), z), (0.04 if big else 0.028, 0.028 if big else 0.04, 0.05), 0.006),
                       k=0.002, label=6)
    doorway(wl, dr, (0, -S, 0.0), (0, -1, 0), 0.2, 0.42, arch=True, label=7)
    for (nx, ny) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        c = v3((nx * S, ny * S, 0.0))
        if ny != -1:
            window(wl, dk, fr, c + Z * 0.62, (nx, ny, 0), 0.14, 0.34, arch=True)
        window(wl, dk, fr, c + Z * 1.55, (nx, ny, 0), 0.14, 0.42, arch=True)
        # the belfry's louvred arch
        bc = c + Z * 3.0
        R, s, n = Rn((nx, ny, 0))
        wl.sub(RoundBox(bc, (0.09, 0.08, 0.1), 0.006, R=R), k=0.004)
        wl.sub(Cylinder(bc + Z * 0.1, 0.09, 0.16, R=rot_from_axes(z_axis=n, y_axis=(0, 0, 1))), k=0.004)
        dk.add(RoundBox(bc - n * 0.06, (0.09, 0.01, 0.1), 0.0, R=R), k=0.0)
        for j in range(4):
            fr.add(RoundBox(bc - n * 0.03 + Z * (-0.07 + j * 0.055), (0.09, 0.008, 0.012), 0.003, R=R @ euler(0.5, 0, 0)), k=0.0)
    ground_cut(wl)
    out += [("Walls", wl, fine(0.007, 0.014), "brick"), ("Glass", dk, fine(0.005, 0.01), "glass"), ("Frames", fr, fine(0.004, 0.008), "frames"),
            ("Door", dr, fine(0.005, 0.01), "door")]
    ck = Field("Clocks")
    for (nx, ny) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        clock_face(ck, v3((nx * (S + 0.05), ny * (S + 0.05), (H1 + H2) / 2)), (nx, ny, 0), 0.2)
    out.append(("Clocks", ck, fine(0.004, 0.008), "clock"))
    rf = Field("Spire")
    rf.add(pyramid_roof((0, 0), S + 0.08, H3 + 0.02, H3 + 1.15), k=0.0)
    for (nx, ny) in ((0, -1), (1, 0), (0, 1), (-1, 0)):            # lucarnes
        c = v3((nx * 0.2, ny * 0.2, H3 + 0.32))
        R, s, n = Rn((nx, ny, 0))
        rf.add(gable((c[0], c[1]), 0.08 if nx == 0 else 0.1, 0.1 if nx == 0 else 0.08, H3 + 0.25, H3 + 0.45, axis="y" if nx == 0 else "x"), k=0.01)
    out.append(("Spire", rf, fine(0.006, 0.012), "slate"))
    ir = Field("Iron")
    for (nx, ny) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        R, s, n = Rn((nx, ny, 0))
        for k in range(5):
            q = v3((nx * (S + 0.06), ny * (S + 0.06), H3 + 0.05)) + s * ((k - 2) * 0.13)
            ir.add(RoundCone(q, q + Z * 0.08, 0.008, 0.008), k=0.0)
            ir.add(Sphere(q + Z * 0.09, 0.014), k=0.003, label=6)
    ir.add(RoundCone((0, 0, H3 + 1.1), (0, 0, H3 + 1.45), 0.016, 0.01), k=0.0)
    ir.add(Sphere((0, 0, H3 + 1.22), 0.035), k=0.004, label=6)
    ir.add(RoundCone((0, 0, H3 + 1.36), (0.12, 0, H3 + 1.36), 0.008, 0.008), k=0.002, label=6)
    ir.add(leaf(v3((0.0, 0, H3 + 1.4)), (-1, 0, 0), (0, 0, 1), [(0.0, -0.04), (0.18, -0.02), (0.22, 0.03), (0.0, 0.04)], 0.006), k=0.0, label=6)
    out.append(("Iron", ir, fine(0.004, 0.008), "black_iron"))
    return out


def canal_lock(seed=0):
    """A canal lock: the chamber between walls of dressed stone with a coping of big rounded stones, the water dark in it
    and running on beyond both ends between low stone banks, a pair of timber mitre gates at each end with long balance
    beams (their ends painted white) reaching out over the towpath, paddle gear on the gates, iron bollards."""
    out = []
    L, Wc, zt, zw = 1.25, 0.36, 0.3, 0.14
    st, cp, wt = Field("Walls"), Field("Coping"), Field("Water")
    for sy in (-1, 1):
        st.add(walls_box(0, sy * (Wc + 0.14), L + 0.55, 0.14, -0.05, zt, batter=0.0, amp=0.004, seed=seed + sy), k=0.0)
        cp.add(RoundBox((0, sy * (Wc + 0.13), zt + 0.03), (L + 0.55, 0.15, 0.04), 0.03, **wob(5.0, 0.004, seed + sy)), k=0.0)
        for x in np.arange(-L - 0.5, L + 0.55, 0.3):
            cp.sub(RoundBox((x, sy * (Wc + 0.13), zt + 0.06), (0.004, 0.2, 0.05), 0.0), k=0.0)
        bk = Field("Bank%d" % (sy + 1))                             # the banks sloping away behind the walls
        bk.add(convex_w([((0, sy * (Wc + 0.27), zt), (0, 0, 1)), ((0, sy * (Wc + 0.27), zt), (0, sy * 0.0 - sy * 1.0, 0)),
                         ((0, sy * (Wc + 0.27 + 0.6), 0), (0, sy, 0.6)), ((0, 0, -0.05), (0, 0, -1)),
                         ((L + 0.55, 0, 0), (1, 0, 0)), ((-L - 0.55, 0, 0), (-1, 0, 0))],
                        (-L - 0.6, min(sy * 0.3, sy * 1.6) - 0.1, -0.1), (L + 0.6, max(sy * 0.3, sy * 1.6) + 0.1, zt + 0.1), 0.01, 5.0, seed + 5 * sy), k=0.0)
        ground_cut(bk)
        out.append(("Bank%d" % (sy + 1), bk, fine(0.014, 0.028), "turf"))
    st.paint(Func(lambda P: (P[:, 2] - F32(zw + 0.05)).astype(F32), (-3, -2, -0.2), (3, 2, 0.4)), 7)
    ground_cut(st)
    wt.add(RoundBox((0, 0, zw - 0.1), (L + 0.55, Wc + 0.01, 0.1), 0.0), k=0.0)
    ground_cut(wt)
    out += [("Walls", st, fine(0.007, 0.014), "stone"), ("Coping", cp, fine(0.007, 0.014), "stone"), ("Water", wt, fine(0.014, 0.028), "canal_water")]
    gt, ir = Field("Gates"), Field("Paddles")
    for sx in (-1, 1):
        x0 = sx * (L - 0.05)
        for sy in (-1, 1):
            hinge = v3((x0, sy * Wc, 0.0))
            tip = v3((x0 - sx * 0.1, 0.0, 0.0))
            d = unit(tip - hinge)
            Lg = float(np.linalg.norm(tip - hinge))
            Rg = np.stack([d, np.cross(Z, d), Z], axis=1)
            gt.add(RoundBox(hinge + d * (Lg / 2) + Z * (zt - 0.02) * 0.5, (Lg / 2, 0.03, (zt + 0.06) / 2), 0.008, R=Rg), k=0.0, label=10)
            for zz in (0.1, 0.22):
                gt.add(RoundBox(hinge + d * (Lg / 2) + Z * zz + Rg @ v3((0, -sx * 0.035, 0)), (Lg / 2, 0.006, 0.014), 0.003, R=Rg), k=0.002, label=6)
            gt.add(RoundBox(hinge + Z * (zt / 2), (0.04, 0.04, zt / 2 + 0.04), 0.01), k=0.004, label=11)
            # the balance beam out over the towpath
            bb0 = hinge + Z * (zt + 0.12)
            bd = unit(v3((sx * 0.85, sy * 0.55, 0)))
            gt.add(RoundBox(bb0 + bd * 0.45 - d * 0.08, (0.55, 0.045, 0.045), 0.012, R=np.stack([bd, np.cross(Z, bd), Z], axis=1)), k=0.0, label=10)
            gt.paint(RoundBox(bb0 + bd * 0.85, (0.16, 0.08, 0.08), 0.0, R=np.stack([bd, np.cross(Z, bd), Z], axis=1)), 7)
            ir.add(RoundCone(hinge + d * (Lg * 0.6) + Z * zt, hinge + d * (Lg * 0.6) + Z * (zt + 0.22), 0.012, 0.012), k=0.0)
            ir.add(RoundBox(hinge + d * (Lg * 0.6) + Z * (zt + 0.18), (0.03, 0.03, 0.03), 0.008), k=0.004)
    ground_cut(gt)
    out += [("Gates", gt, fine(0.005, 0.01), "lock_timber"), ("Paddles", ir, fine(0.004, 0.008), "black_iron")]
    bl = Field("Bollards")
    for (x, sy) in ((-0.5, -1), (0.6, -1), (0.0, 1)):
        c = v3((x, sy * (Wc + 0.32), zt))
        bl.add(RoundCone(c, c + Z * 0.12, 0.05, 0.04), k=0.0)
        bl.add(Cylinder(c + Z * 0.14, 0.055, 0.04, rr=0.015), k=0.01)
    out.append(("Bollards", bl, fine(0.004, 0.008), "black_iron"))
    return out


def factory_chimney(seed=0, H=4.6):
    """A mill chimney: a square pedestal of brick with sunk arched panels and a stone cornice, the round shaft tapering
    up from it in iron bands to an oversailing cap of corbelled courses, black with soot; a lightning conductor."""
    out = []
    f = Field("Brick")
    chimney_square(f, (0, 0), -0.05, 1.0, 0.42, 0.4, seed, cap=False, plinth=0.25)
    for (nx, ny) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        R, s, n = Rn((nx, ny, 0))
        c = v3((nx * 0.41, ny * 0.41, 0.6))
        f.sub(RoundBox(c, (0.18, 0.03, 0.22), 0.006, R=R), k=0.003)
        f.sub(Cylinder(c + Z * 0.22, 0.18, 0.06, R=rot_from_axes(z_axis=n, y_axis=(0, 0, 1))), k=0.003)
    f.add(RoundBox((0, 0, 1.0), (0.47, 0.47, 0.05), 0.012), k=0.004, label=6)
    f.add(RoundBox((0, 0, 1.08), (0.43, 0.43, 0.04), 0.012), k=0.004, label=6)
    chimney_round(f, (0, 0), 1.05, H, 0.33, 0.22, seed + 1, bands=tuple(np.arange(1.6, H - 0.4, 0.55)), cap=False)
    for k, (dz, e) in enumerate(((0.0, 0.03), (0.07, 0.06), (0.14, 0.085), (0.22, 0.06))):
        f.add(Cylinder((0, 0, H - 0.25 + dz), 0.22 + e, 0.07, rr=0.015), k=0.004)
    f.sub(Cylinder((0, 0, H + 0.05), 0.16, 0.4), k=0.006)
    f.paint(Func(lambda P: (F32(H - 0.55) - P[:, 2]).astype(F32), (-1, -1, H - 0.8), (1, 1, H + 0.4)), 5)
    ground_cut(f)
    out.append(("Brick", f, fine(0.007, 0.014), "brick"))
    ir = Field("Conductor")
    ir.add(RoundCone((0.0, -0.3, 0.1), (0.0, -0.24, H + 0.25), 0.008, 0.008), k=0.0)
    ir.add(RoundCone((0.0, -0.22, H + 0.25), (0.0, -0.22, H + 0.4), 0.012, 0.003), k=0.0, label=6)
    ground_cut(ir)
    out.append(("Conductor", ir, fine(0.004, 0.008), "black_iron"))
    return out


# ------------------------------------------------------------------------------------------------ Smog City: the canal basins
def kerb(seed=0):
    """A coping stone for a canal basin's edge: a long dressed block with a rounded top, an iron mooring ring."""
    f, ir = Field("Kerb"), Field("Ring")
    f.add(RoundBox((0, 0, 0.04), (0.3, 0.075, 0.07), 0.035, **wob(6.0, 0.003, seed)), k=0.0)
    f.sub(RoundBox((0.3, 0, 0.1), (0.004, 0.2, 0.2), 0.0), k=0.0)
    ground_cut(f)
    ir.add(Torus((0.12, -0.07, 0.09), 0.035, 0.011, R=rot_from_axes(z_axis=(0, 1, 0.4))), k=0.0)
    return [("Kerb", f, fine(0.005, 0.01), "stone"), ("Ring", ir, fine(0.003, 0.006), "black_iron")]


def bollard(seed=0):
    """A cast-iron mooring bollard: a squat waisted post with a domed cap, black, its top worn bright."""
    f = Field("Bollard")
    f.add(Cylinder((0, 0, 0.03), 0.075, 0.06, rr=0.015), k=0.0)
    f.add(RoundCone((0, 0, 0.05), (0, 0, 0.19), 0.06, 0.05), k=0.02)
    f.add(Cylinder((0, 0, 0.21), 0.07, 0.05, rr=0.02), k=0.02)
    f.add(Ellipsoid((0, 0, 0.24), (0.06, 0.06, 0.03)), k=0.01)
    f.add(RoundCone((0, 0, 0.1), (0.06, 0, 0.14), 0.02, 0.016), k=0.01)
    ground_cut(f)
    return [("Bollard", f, fine(0.004, 0.008), "black_iron")]


def narrowboat(seed=0):
    """A narrowboat moored in the basin (her waterline at z = 0, bow to +X): a long dark green hull with a red and
    yellow band, the cabin aft with brass portholes and its doors painted in roses and castles, the stove chimney with
    its brass bands, the tiller; forward, the hold heaped with coal under its top planks and side cloths."""
    out = []
    Lh, W, D = 1.05, 0.17, 0.2
    f = Field("Hull")

    def hull(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        tb = np.clip((x - F32(Lh - 0.45)) / F32(0.45), 0, 1)
        ts = np.clip((F32(-Lh + 0.2) - x) / F32(0.2), 0, 1)
        hw = F32(W) * np.sqrt(np.clip(F32(1) - tb ** 2, 0, 1)) * (F32(1) - F32(0.35) * ts ** 2) + F32(0.003)
        top = F32(D) + F32(0.06) * tb ** 2
        dd = np.maximum.reduce([np.abs(y) - hw, F32(-0.05) - z, z - top, -x - F32(Lh)])
        di = np.maximum.reduce([np.abs(y) - (hw - F32(0.02)), F32(0.06) - z, -x - F32(Lh - 0.03), x - F32(Lh - 0.08)])
        return (np.maximum(dd, -di) * F32(0.85)).astype(F32)
    f.add(Func(hull, (-Lh - 0.05, -W - 0.05, -0.08), (Lh + 0.05, W + 0.05, D + 0.12)), k=0.0, label=10)
    f.paint(Func(lambda P: (np.abs(P[:, 2] - F32(D - 0.04)) - F32(0.018)).astype(F32), (-2, -1, -0.1), (2, 1, 0.5)), 5)
    f.paint(Func(lambda P: (np.abs(P[:, 2] - F32(D - 0.072)) - F32(0.009)).astype(F32), (-2, -1, -0.1), (2, 1, 0.5)), 7)
    f.paint(Func(lambda P: (P[:, 2] - F32(0.05)).astype(F32), (-2, -1, -0.2), (2, 1, 0.2)), 9)
    cx0, cx1 = -Lh + 0.12, -0.1                                     # the cabin
    f.add(RoundBox(((cx0 + cx1) / 2, 0, D + 0.1), ((cx1 - cx0) / 2, W - 0.03, 0.1), 0.015), k=0.004, label=10)
    f.add(RoundBox(((cx0 + cx1) / 2, 0, D + 0.21), ((cx1 - cx0) / 2 + 0.02, W - 0.01, 0.015), 0.012), k=0.004, label=5)
    for sy in (-1, 1):
        for x in np.linspace(cx0 + 0.15, cx1 - 0.1, 4):
            f.add(Torus((x, sy * (W - 0.03), D + 0.12), 0.026, 0.008, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.002, label=6)
        f.paint(Func(lambda P, sy=sy: np.maximum(np.abs(np.maximum(np.abs(P[:, 0] - F32((cx0 + cx1) / 2)) - F32((cx1 - cx0) / 2 - 0.03),
                                                                  np.abs(P[:, 2] - F32(D + 0.1)) - F32(0.07))) - F32(0.007),
                                                np.abs(P[:, 1] - F32(sy * (W - 0.03))) - F32(0.03)).astype(F32), (cx0, sy * W - 0.1, D), (cx1, sy * W + 0.1, D + 0.25)), 7)
    for sy in (-1, 1):                                              # the doors aft: roses and castles
        dc = v3((cx0 - 0.005, sy * 0.06, D + 0.1))
        f.paint(Sphere(dc + v3((0, 0, 0.02)), 0.03), 5)
        f.paint(RoundBox(dc + v3((0, 0, -0.04)), (0.02, 0.03, 0.015), 0.0), 7)
    f.add(RoundCone((-Lh + 0.02, 0, D + 0.02), (-Lh - 0.18, 0, D + 0.08), 0.012, 0.012), k=0.004, label=6)       # the tiller
    f.add(RoundBox((-Lh - 0.03, 0, 0.08), (0.03, 0.008, 0.11), 0.006), k=0.004, label=10)
    f.add(RoundCone((cx1 - 0.15, 0.06, D + 0.2), (cx1 - 0.15, 0.06, D + 0.4), 0.022, 0.024), k=0.004, label=7)
    for z in (D + 0.28, D + 0.36):
        f.add(Torus((cx1 - 0.15, 0.06, z), 0.024, 0.007), k=0.002, label=6)
    for x in np.linspace(cx1 + 0.08, Lh - 0.3, 4):                   # the hold: stands and top planks, side cloths
        f.add(RoundCone((x, 0, D - 0.02), (x, 0, D + 0.18), 0.012, 0.012), k=0.0, label=11)
    f.add(RoundBox(((cx1 + Lh - 0.25) / 2, 0, D + 0.19), ((Lh - 0.25 - cx1) / 2, 0.035, 0.008), 0.003), k=0.002, label=10)
    out.append(("Hull", f, fine(0.005, 0.01), "narrowboat"))
    cl = Field("Coal")
    cl.add(Ellipsoid(((cx1 + Lh - 0.3) / 2, 0, D - 0.02), ((Lh - 0.3 - cx1) / 2, W - 0.02, 0.11), **wob(14.0, 0.015, seed)), k=0.0)
    cl.inter(Plane((0, 0, D - 0.04), (0, 0, -1)))
    out.append(("Coal", cl, fine(0.005, 0.01), "coal"))
    return out


# ------------------------------------------------------------------------------------------------ the Industrial city
CXW, YEND = 0.55, 7.0               # the boundary wall's front face (x) and its ends (+-y)


def _wall_fade(y):
    return np.clip((F32(YEND - 0.15) - np.abs(y)) / F32(1.6), 0, 1) ** F32(0.6)


def industrial_city(seed=0):
    """A great works' entrance at the end of the road (the road comes in from -X): the boundary wall of red brick on a
    blue-brick plinth with stone-capped piers, running off both ways and dying away; the gatehouse in the middle (two
    lodges with round-headed windows and stone dressings either side of the gateway's arch, the iron gates standing
    open, the company's board over the arch), the clock tower rising behind the arch, the corps' navy-and-brass banners
    down the lodges, gas lamps on the lodges' corners, fire baskets on brick piers before them (game.gd lights them);
    behind the wall, sheds under sawtooth roofs, an engine house and three tall smokestacks (game.gd adds their smoke)."""
    rng = np.random.default_rng(seed)
    out = []
    # ---- the boundary wall
    wl = Field("Wall")
    HW = 1.15

    def wall(P):
        fd = _wall_fade(P[:, 1])
        top = F32(HW) * fd
        d = np.maximum.reduce([np.abs(P[:, 0] - F32(CXW + 0.1)) - F32(0.1), np.abs(P[:, 1]) - F32(YEND), P[:, 2] - top, -P[:, 2] - F32(0.06),
                               F32(1.2) - np.abs(P[:, 1])])
        return (d * F32(0.95)).astype(F32)
    wl.add(Func(wall, (CXW - 0.2, -YEND - 0.1, -0.1), (CXW + 0.4, YEND + 0.1, HW + 0.1)), k=0.0)

    def coping(P):
        fd = _wall_fade(P[:, 1])
        top = F32(HW) * fd
        dd = np.sqrt((P[:, 0] - F32(CXW + 0.1)) ** 2 * F32(0.6) + (P[:, 2] - top) ** 2) - F32(0.11)
        return np.maximum.reduce([dd, np.abs(P[:, 1]) - F32(YEND), F32(0.08) - top, F32(1.6) - np.abs(P[:, 1])]).astype(F32)
    wl.add(Func(coping, (CXW - 0.2, -YEND - 0.1, -0.1), (CXW + 0.4, YEND + 0.1, HW + 0.2)), k=0.01, label=6)
    wl.paint(Func(lambda P: (P[:, 2] - F32(0.22)).astype(F32), (-1, -8, -0.2), (2, 8, 0.4)), 8)
    for y in np.arange(2.0, YEND - 0.5, 1.15):                       # piers
        for sy in (-1, 1):
            fd = float(np.clip((YEND - 0.15 - y) / 1.6, 0, 1) ** 0.6)
            if fd < 0.3:
                continue
            wl.add(walls_box(CXW + 0.1, sy * y, 0.17, 0.15, -0.05, HW * fd + 0.18, batter=0.0, amp=0.003, seed=seed + int(y * 10)), k=0.004)
            wl.add(pyramid_roof((CXW + 0.1, sy * y), 0.2, HW * fd + 0.18, HW * fd + 0.3), k=0.004, label=6)
    ground_cut(wl, -0.04)
    out.append(("Wall", wl, fine(0.016, 0.03), "brick"))
    # ---- the gatehouse: two lodges either side of the gateway
    gh, dk, fr, gw = Field("Gatehouse"), Field("Glass"), Field("Frames"), Field("Lit")
    LX0, LX1, LY0, LY1, LH = 0.35, 1.45, 0.75, 1.75, 1.95
    for sy in (-1, 1):
        yc = sy * (LY0 + LY1) / 2
        hyl = (LY1 - LY0) / 2
        gh.add(walls_box((LX0 + LX1) / 2, yc, (LX1 - LX0) / 2, hyl, -0.05, LH, batter=0.0, amp=0.003, seed=seed + sy), k=0.0)
        gh.paint(Func(lambda P: (P[:, 2] - F32(0.25)).astype(F32), (0, -3, -0.2), (2, 3, 0.4)), 8)
        gh.add(RoundBox(((LX0 + LX1) / 2, yc, 0.25), ((LX1 - LX0) / 2 + 0.02, hyl + 0.02, 0.025), 0.006), k=0.003, label=6)
        gh.add(RoundBox(((LX0 + LX1) / 2, yc, 1.05), ((LX1 - LX0) / 2 + 0.02, hyl + 0.02, 0.025), 0.006), k=0.003, label=6)
        gh.add(RoundBox(((LX0 + LX1) / 2, yc, LH), ((LX1 - LX0) / 2 + 0.06, hyl + 0.06, 0.05), 0.01), k=0.003, label=6)
        for k in range(9):                                          # crenellated parapet
            t = -1 + 2 * k / 8
            gh.add(RoundBox((LX0 - 0.02, yc + t * (hyl - 0.05), LH + 0.13), (0.06, 0.06, 0.08), 0.01), k=0.003)
        for sx2 in (-1, 1):                                         # quoins
            for sy2 in (-1, 1):
                for k in range(9):
                    z = 0.35 + k * 0.17
                    big = k % 2 == 0
                    gh.add(RoundBox(((LX0 if sx2 < 0 else LX1) - sx2 * (0.03 if big else 0.02), yc + sy2 * (hyl - (0.02 if big else 0.03)), z),
                                    (0.04 if big else 0.028, 0.028 if big else 0.04, 0.05), 0.006), k=0.002, label=6)
        window(gh, dk, fr, (LX0, yc, 0.55), (-1, 0, 0), 0.24, 0.36, arch=True, pane=gw if sy > 0 else None)
        for z in (0.55, 1.45):
            window(gh, dk, fr, ((LX0 + LX1) / 2, sy * LY1, z), (0, sy, 0), 0.22, 0.36, arch=True)
    # the gateway: a block over the passage between the lodges (the clock tower rises from it), the arch through it,
    # the company's board and a pediment over the arch
    ZS = 1.1
    gh.add(RoundBox(((LX0 + LX1) / 2, 0, 1.25), ((LX1 - LX0) / 2, LY0 + 0.05, 1.05), 0.01), k=0.003)
    gh.sub(Func(lambda P: np.maximum(np.minimum(np.maximum(np.abs(P[:, 1]) - F32(LY0 - 0.02), P[:, 2] - F32(ZS)),
                                                np.sqrt(P[:, 1] ** 2 + (P[:, 2] - F32(ZS)) ** 2) - F32(LY0 - 0.02)),
                                     np.abs(P[:, 0] - F32((LX0 + LX1) / 2)) - F32((LX1 - LX0) / 2 + 0.1)).astype(F32), (0.1, -1.0, -0.2), (1.7, 1.0, 2.1)), k=0.006)
    gh.paint(Func(lambda P: np.maximum(np.maximum(np.abs(np.sqrt(P[:, 1] ** 2 + (P[:, 2] - F32(ZS)) ** 2) - F32(LY0 + 0.05)) - F32(0.07),
                                                  F32(ZS - 0.02) - P[:, 2]), np.abs(P[:, 0] - F32(LX0)) - F32(0.12)).astype(F32),
                  (0.1, -1.2, ZS - 0.1), (0.6, 1.2, 2.1)), 6)
    gh.add(RoundBox((LX0 - 0.02, 0, 2.0), (0.03, 0.55, 0.11), 0.01), k=0.003, label=9)
    for i in range(8):
        gh.paint(RoundBox((LX0 - 0.05, -0.42 + i * 0.12, 2.0), (0.03, 0.035, 0.05), 0.0), 6)
    gh.add(RoundBox(((LX0 + LX1) / 2, 0, 2.3), ((LX1 - LX0) / 2 + 0.05, LY0 + 0.08, 0.04), 0.01), k=0.003, label=6)
    gh.add(convex([((LX0, 0, 2.72), (0, 1.0, 1.6)), ((LX0, 0, 2.72), (0, -1.0, 1.6)), ((LX0 - 0.06, 0, 0), (-1, 0, 0)), ((LX0 + 0.14, 0, 0), (1, 0, 0)),
                   ((LX0, 0, 2.3), (0, 0, -1))], (LX0 - 0.2, -1.0, 2.2), (LX0 + 0.3, 1.0, 2.85)), k=0.004, label=6)
    ground_cut(gh, -0.04)
    out += [("Gatehouse", gh, fine(0.01, 0.02), "brick"), ("Glass", dk, fine(0.006, 0.012), "glass"), ("Frames", fr, fine(0.005, 0.01), "frames"),
            ("Lit", gw, fine(0.006, 0.012), "glow_lamp")]
    rf = Field("Roofs")
    for sy in (-1, 1):
        hipped(rf, ((LX0 + LX1) / 2 + 0.05, sy * (LY0 + LY1) / 2), (LX1 - LX0) / 2 - 0.08, (LY1 - LY0) / 2 - 0.08, LH + 0.04, LH + 0.5, over=0.0)
    out.append(("Roofs", rf, fine(0.008, 0.016), "slate"))
    # ---- the clock tower behind the arch
    ct = Field("Tower")
    tx, S, T1, T2 = (LX0 + LX1) / 2 + 0.05, 0.36, 3.55, 4.15
    ct.add(walls_box(tx, 0, S, S, 2.2, T2, batter=0.0, amp=0.002, seed=seed + 7), k=0.0)
    for z in (2.85, T1):
        ct.add(RoundBox((tx, 0, z), (S + 0.03, S + 0.03, 0.03), 0.006), k=0.003, label=6)
    ct.add(RoundBox((tx, 0, (T1 + T2) / 2), (S + 0.05, S + 0.05, (T2 - T1) / 2), 0.008), k=0.004)
    ct.add(RoundBox((tx, 0, T2), (S + 0.08, S + 0.08, 0.04), 0.008), k=0.003, label=6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k in range(8):
                z = 2.45 + k * 0.17
                if z > T2 - 0.1:
                    break
                big = k % 2 == 0
                ct.add(RoundBox((tx + sx * (S - (0.03 if big else 0.02)), sy * (S - (0.02 if big else 0.03)), z), (0.04 if big else 0.028, 0.028 if big else 0.04, 0.05), 0.006),
                       k=0.002, label=6)
    cdk, cfr = Field("TGlass"), Field("TFrames")
    for (nx, ny) in ((-1, 0), (0, 1), (0, -1)):
        window(ct, cdk, cfr, (tx + nx * S, ny * S, 3.1), (nx, ny, 0), 0.16, 0.36, arch=True)
    ground_cut(ct, 2.1)
    out += [("Tower", ct, fine(0.008, 0.016), "brick"), ("TGlass", cdk, fine(0.005, 0.01), "glass"), ("TFrames", cfr, fine(0.004, 0.008), "frames")]
    ck = Field("Clocks")
    for (nx, ny) in ((-1, 0), (0, 1), (0, -1), (1, 0)):
        clock_face(ck, v3((tx + nx * (S + 0.06), ny * (S + 0.06), (T1 + T2) / 2)), (nx, ny, 0), 0.23)
    out.append(("Clocks", ck, fine(0.004, 0.008), "clock"))
    sp = Field("Spire")
    sp.add(pyramid_roof((tx, 0), S + 0.1, T2 + 0.03, T2 + 1.15), k=0.0)
    out.append(("Spire", sp, fine(0.007, 0.014), "slate"))
    ir = Field("Iron")
    ir.add(RoundCone((tx, 0, T2 + 1.1), (tx, 0, T2 + 1.5), 0.02, 0.012), k=0.0)
    ir.add(Sphere((tx, 0, T2 + 1.24), 0.045), k=0.004, label=6)
    ir.add(RoundCone((tx, 0, T2 + 1.4), (tx, 0.16, T2 + 1.4), 0.01, 0.01), k=0.002, label=6)
    ir.add(leaf(v3((tx, 0.0, T2 + 1.45)), (0, -1, 0), (0, 0, 1), [(0.0, -0.05), (0.22, -0.025), (0.27, 0.04), (0.0, 0.05)], 0.007), k=0.0, label=6)
    # the iron gates standing open, swung in against the passage
    for sy in (-1, 1):
        hinge = v3((0.3, sy * (LY0 - 0.04), 0.0))
        d = unit(v3((0.9, -sy * 0.42, 0.0)))
        Rg = np.stack([d, np.cross(Z, d), Z], axis=1)
        Lg = 0.7
        for zz in (0.1, 0.62, 1.12):
            ir.add(RoundBox(hinge + d * (Lg / 2) + Z * zz, (Lg / 2, 0.012, 0.018), 0.005, R=Rg), k=0.0)
        ir.add(RoundCone(hinge, hinge + Z * 1.3, 0.03, 0.03), k=0.0)
        ir.add(RoundCone(hinge + d * Lg, hinge + d * Lg + Z * 1.25, 0.022, 0.022), k=0.0)
        for k in range(1, 9):
            q = hinge + d * (Lg * k / 9)
            top = 1.12 + 0.12 * math.sin(math.pi * k / 9)
            ir.add(RoundCone(q + Z * 0.08, q + Z * top, 0.009, 0.009), k=0.0)
            ir.add(RoundCone(q + Z * top, q + Z * (top + 0.07), 0.02, 0.002), k=0.004, label=6)
        ir.add(Torus(hinge + d * (Lg / 2) + Z * 0.87, 0.12, 0.012, R=rot_from_axes(z_axis=np.cross(Z, d))), k=0.003, label=6)
    # gas lamps on brackets at the lodges' front corners
    for sy in (-1, 1):
        for y in (LY0 + 0.12, LY1 - 0.12):
            b0 = v3((LX0, sy * y, 1.2))
            ir.add(RoundCone(b0, b0 + v3((-0.2, 0, 0)), 0.012, 0.012), k=0.0)
            ir.add(RoundCone(b0 - Z * 0.14, b0 + v3((-0.14, 0, -0.01)), 0.009, 0.009), k=0.0)
    ground_cut(ir)
    out.append(("Iron", ir, fine(0.004, 0.008), "black_iron"))
    for sy in (-1, 1):
        for y in (LY0 + 0.12, LY1 - 0.12):
            lp = []
            gas_lamp(lp, (0, 0, 0), seed=seed, name="Gate", standard=False)
            place_parts(out, lp, (LX0 - 0.2, sy * y, 1.22))
    # the corps' banners down the lodges' fronts
    bn = Field("Banners")
    for sy in (-1, 1):
        o = v3((LX0 - 0.04, sy * (LY0 + LY1) / 2, 1.88))
        bn.add(leaf(o, (0, 0, -1), (0, 1, 0), [(0.0, -0.2), (0.62, -0.2), (0.75, 0.0), (0.62, 0.2), (0.0, 0.2)], 0.008,
                    zfn=lambda a, b: (F32(0.012) * np.sin(b * F32(18)), F32(0.0) * a, F32(0.012 * 18) * np.cos(b * F32(18))), zamp=0.015), k=0.0)
        bn.add(RoundCone(o + v3((-0.03, -0.24, 0.02)), o + v3((-0.03, 0.24, 0.02)), 0.014, 0.014), k=0.004, label=6)
        cg = o + v3((-0.01, 0, -0.32))
        Rb = rot_from_axes(z_axis=(1, 0, 0))
        bn.paint(Torus(cg, 0.08, 0.024, R=Rb), 5)
        for k in range(8):
            a = 2 * math.pi * k / 8
            bn.paint(Sphere(cg + v3((0, math.cos(a) * 0.115, math.sin(a) * 0.115)), 0.024), 5)
        bn.paint(Func(lambda P, o=o: (np.minimum(np.abs(P[:, 1] - F32(o[1])) - F32(0.17), F32(1.0)) * F32(-1.0)).astype(F32),
                      o + v3((-0.2, -0.3, -0.9)), o + v3((0.2, 0.3, 0.1))), 5)
    out.append(("Banners", bn, fine(0.005, 0.01), "banner"))
    # fire baskets on brick piers before the lodges
    pr, fb, cg2 = Field("Piers"), Field("Baskets"), Field("Coals")
    for (fx, fy, fz) in CITY_FIRES:
        c = v3((fx, fy, 0.0))
        pr.add(walls_box(fx, fy, 0.14, 0.14, -0.05, 0.62, batter=0.0, amp=0.003, seed=seed + int(fy * 10)), k=0.0)
        pr.add(RoundBox(c + Z * 0.64, (0.17, 0.17, 0.035), 0.008), k=0.003, label=6)
        pr.paint(Func(lambda P: (P[:, 2] - F32(0.15)).astype(F32), c - 1, c + 1), 8)
        for k in range(6):
            a = 2 * math.pi * k / 6
            fb.add(RoundCone(c + Z * 0.68 + v3((math.cos(a) * 0.06, math.sin(a) * 0.06, 0)), c + Z * 0.95 + v3((math.cos(a) * 0.17, math.sin(a) * 0.17, 0)),
                             0.012, 0.012), k=0.004)
        fb.add(Torus(c + Z * 0.95, 0.17, 0.014), k=0.004)
        fb.add(Torus(c + Z * 0.82, 0.115, 0.012), k=0.004)
        fb.add(Cylinder(c + Z * 0.68, 0.08, 0.03, rr=0.01), k=0.004)
        cg2.add(Ellipsoid(c + Z * 0.9, (0.13, 0.13, 0.08), **wob(25.0, 0.01, seed + int(fy * 10))), k=0.0)
    ground_cut(pr)
    out += [("Piers", pr, fine(0.006, 0.012), "brick"), ("Baskets", fb, fine(0.004, 0.008), "black_iron"), ("Coals", cg2, fine(0.005, 0.01), "glow_fire")]
    # ---- behind the wall: two sheds under sawtooth roofs
    for sy in (-1, 1):
        y0, y1 = (1.95, 5.6) if sy > 0 else (-5.6, -1.95)
        x0, x1, zs = 1.75, 4.2, 1.65
        sh, sg, sf, sd, sw = Field("Shed%d" % (sy + 1)), Field("ShedLights%d" % (sy + 1)), Field("ShedBars%d" % (sy + 1)), Field("ShedGlass%d" % (sy + 1)), Field("ShedRoof%d" % (sy + 1))
        sh.add(walls_box((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, -0.05, zs, batter=0.0, amp=0.003, seed=seed + 20 + sy), k=0.0)
        sh.add(RoundBox(((x0 + x1) / 2, (y0 + y1) / 2, zs - 0.03), ((x1 - x0) / 2 + 0.03, (y1 - y0) / 2 + 0.03, 0.035), 0.008), k=0.003, label=6)
        for y in np.linspace(y0 + 0.4, y1 - 0.4, 5):
            window(sh, sd, sf, (x0, y, 1.15), (-1, 0, 0), 0.24, 0.5, arch=True)
        sawtooth(sw, sg, sf, x0 + 0.0, x1 - 0.0, y0 - 0.0, y1 + 0.0, zs, 5, 0.55, glaze=-1)
        dyt = (y1 - y0) / 5
        for i in range(5):                                          # the zigzag gable wall facing the road
            ya = y0 + i * dyt
            sh.add(convex([((x0, ya + dyt, zs + 0.025), (0, 0.55, dyt)), ((x0, ya, zs), (0, -1, 0.12)), ((0, 0, zs - 0.05), (0, 0, -1)),
                           ((x0 + 0.08, 0, 0), (1, 0, 0)), ((x0 - 0.03, 0, 0), (-1, 0, 0))],
                          (x0 - 0.3, ya - 0.2, zs - 0.2), (x0 + 0.3, ya + dyt + 0.2, zs + 0.8)), k=0.0)
        ground_cut(sh)
        out += [("Shed%d" % (sy + 1), sh, fine(0.016, 0.03), "brick"), ("ShedRoof%d" % (sy + 1), sw, fine(0.016, 0.03), "slate"),
                ("ShedLights%d" % (sy + 1), sg, fine(0.014, 0.028), "glass"), ("ShedBars%d" % (sy + 1), sf, fine(0.008, 0.016), "frames"),
                ("ShedGlass%d" % (sy + 1), sd, fine(0.012, 0.024), "glass")]
    # ---- the engine house and the smokestacks
    eh = Field("EngineHouse")
    ex, ey = 4.9, -0.6
    eh.add(walls_box(ex, ey, 0.55, 0.9, -0.05, 2.1, batter=0.0, amp=0.003, seed=seed + 30), k=0.0)
    eh.add(gable((ex, ey), 0.9, 0.55, 2.05, 2.6, axis="y"), k=0.0)
    edk, efr = Field("EGlass"), Field("EFrames")
    for y in (ey - 0.45, ey + 0.0, ey + 0.45):
        window(eh, edk, efr, (ex - 0.55, y, 1.25), (-1, 0, 0), 0.22, 0.7, arch=True)
    ground_cut(eh)
    rfe = Field("EngineRoof")
    roof(rfe, (ex, ey), 0.9, 0.55, 2.1, 2.6, axis="y", over=0.08)
    out += [("EngineHouse", eh, fine(0.014, 0.028), "brick"), ("EngineRoof", rfe, fine(0.014, 0.028), "slate"),
            ("EGlass", edk, fine(0.008, 0.016), "glass"), ("EFrames", efr, fine(0.006, 0.012), "frames")]
    ch = Field("Stacks")
    for i, (cx, cy, H) in enumerate(CITY_STACKS):
        chimney_square(ch, (cx, cy), -0.05, 0.75, 0.36, 0.34, seed + 40 + i, cap=False, plinth=0.3)
        ch.add(RoundBox((cx, cy, 0.77), (0.4, 0.4, 0.04), 0.01), k=0.004, label=6)
        chimney_round(ch, (cx, cy), 0.75, H, 0.28, 0.18, seed + 41 + i, bands=tuple(np.arange(1.4, H - 0.5, 0.6)))
    ground_cut(ch)
    out.append(("Stacks", ch, fine(0.013, 0.024), "brick"))
    return out


CITY_FIRES = [(-0.18, -1.25, 1.0), (-0.18, 1.25, 1.0)]                 # the fire baskets (Blender: x, y, z; game.gd: x, z, -y)
CITY_STACKS = [(5.9, -2.6, 6.2), (6.3, 1.4, 6.8), (5.1, 4.2, 5.6)]     # the smokestacks: x, y, height
CITY_SMOKE = [(x, y, h + 0.05) for (x, y, h) in CITY_STACKS]          # their mouths


# ------------------------------------------------------------------------------------------------ the kits
# prop name -> (builder, game-mesh triangle budget), as decor_props.KITS. Tuft and Flowers are direct geometry
# (decor_build).
def KITS(theme):
    if theme == "factory":
        return {
            "Stub_A": (lambda: chimney_stub(501, square=True), 900), "Stub_B": (lambda: chimney_stub(502, square=False), 800),
            "Scrap": (lambda: scrap_heap(503), 1300), "Castings": (lambda: castings(504), 1300), "Ingots": (lambda: ingots(505), 900),
            "SlagCart": (lambda: slag_cart(506), 1500), "Barrels": (lambda: barrels(507), 1000), "Crates": (lambda: crates(508), 1100),
            "Drum": (lambda: cable_drum(509), 1000), "Weeds": (lambda: weeds(510), 700),
            "Rock_A": (lambda: rock(1.4, 0.45, 511, n_extra=2), 600), "Rock_B": (lambda: rock(0.9, 0.3, 512, n_extra=1), 400),
            "Tree_A": (lambda: sooty_tree(2.3, 513), 1400), "Tree_B": (lambda: sooty_tree(1.8, 514), 1100),
            "Foundry": (lambda: foundry(515), 6000), "Gasholder": (lambda: gasholder(516), 4200), "HammerShed": (lambda: hammer_shed(517), 4200),
            "WaterTower": (lambda: water_tower(518), 2600),
            "Workshop": (lambda: workshop(519), 2600), "Hammer": (lambda: steam_hammer(520), 2000), "BeamEngine": (lambda: beam_engine(521), 2400),
            "Crane": (lambda: steam_crane(522), 2200),
        }
    if theme == "railyard":
        return {
            "Buffer": (lambda: buffer_stop(531), 1000), "Signal": (lambda: semaphore(532), 900), "CoalTub": (lambda: coal_tub(533), 1100),
            "Sleepers": (lambda: sleeper_stack(534), 700), "Crates": (lambda: crates(535), 1100), "Barrels": (lambda: barrels(536), 1000),
            "Lamp": (lambda: lamp_standard(537), 500), "Churns": (lambda: churns(538), 900), "Weeds": (lambda: weeds(539), 700),
            "Tree_A": (lambda: __import__("decor_iron").birch(2.4, 540), 1300), "Tree_B": (lambda: __import__("decor_iron").birch(1.8, 541), 1000),
            "Loco": (lambda: locomotive(542), 6000), "Wagon_A": (lambda: goods_wagon(543), 2000), "Wagon_B": (lambda: goods_wagon(544, van=True), 2000),
            "WaterTower": (lambda: water_tower(545, trestle=True), 3000), "SignalBox": (lambda: signal_box(546), 3000),
            "EngineShed": (lambda: engine_shed(547), 4800),
            "Coal": (lambda: coal_bin(548), 1500), "Staithe": (lambda: staithe(549), 2600),
        }
    if theme == "smog":
        return {
            "Lamp": (lambda: lamp_standard(561), 500), "PillarBox": (lambda: pillar_box(562), 400), "Bench": (lambda: bench(563), 600),
            "Barrels": (lambda: barrels(564), 1000), "Crates": (lambda: crates(565), 1100), "Railings": (lambda: railings(566), 1100),
            "Plane_A": (lambda: plane_tree(3.2, 567, guard=True), 1800), "Plane_B": (lambda: plane_tree(2.6, 568), 1400),
            "Pots": (lambda: pot_pile(569), 900),
            "Terrace": (lambda: terrace(570), 5600), "Pub": (lambda: pub(571), 4400), "ClockTower": (lambda: clock_tower(572), 3400),
            "Lock": (lambda: canal_lock(573), 3000), "Chimney": (lambda: factory_chimney(574), 1600),
            "Kerb": (lambda: kerb(575), 160), "Bollard": (lambda: bollard(576), 200), "Narrowboat": (lambda: narrowboat(577), 1800),
        }
    if theme == "factory_city":
        return {"City": (lambda: industrial_city(591), 19000)}
    raise KeyError(theme)
