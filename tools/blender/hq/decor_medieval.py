"""HQ Medieval Age map props, sculpted as distance fields like decor_props, decor_bronze, decor_iron and decor_classical
(same conventions: every builder returns its parts [(part name, Field, voxel, material key)], built at the origin, Z up,
ground at z = 0; KITS lists each theme's props and their game-mesh triangle budgets; decor_build.materials resolves the
material keys).

Hedgerow Fields (farmland): broad oaks, hedgerows of hawthorn in blossom on their banks, haystacks, wattle fences;
landmarks: a timber-framed cottage under a thick thatch, a barn, a post windmill with lattice sails, a well with its
winch, a scarecrow, a hay cart.
Darkwood: tall dark spruces, gnarled old oaks, dead trees, ferns, fly agarics, mossy boulders, stumps and logs;
landmarks: a woodcutter's hut (a log cabin under a turf roof, a chopping block with the axe in it, a woodpile), a ruined
chapel (stone walls broken off, a pointed window, a bell-cote, ivy), a wayside cross.
Castle Siege (castle): the besiegers' camp: round pavilions and ridge tents in striped canvas with pennants, mantlets
(wooden shields on stakes), a covered battering ram, a siege tower under its hides, barrels and crates, a pile of
catapult stones, a campfire, banners, a rack of spears; oaks and boulders.
The Medieval city at the end of every Medieval Age road (a castle's gatehouse: two round towers under conical slate roofs,
the gate between them, its portcullis raised, the drawbridge down; the curtain wall running off both ways with its
crenellated walk; blue banners; the keep rising behind with its turrets) is its own kit ("medieval_city",
medieval_city.glb).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Chain, Plane, Func, rot_from_axes, v3, NOISE, euler
import decor_props as DP
from decor_props import vx, wob, convex, rock, stump, log
from decor_bronze import fine, unit, frame, ground_cut, cut_above, cut_below, place, place_parts, mound, convex_w, walls_box
from decor_iron import Rz, R_xz, at_height, cone, gable
from decor_classical import bush, crenels

F32 = np.float32


# ------------------------------------------------------------------------------------------------ trees
def oak(h=2.6, seed=0, young=False, gnarled=False):
    """A broad oak: a thick short bole flaring into roots, dividing low into great limbs that reach out and up, under a
    broad, lumpy crown wider than it is tall (gnarled: an old forest oak, its bole hollowed and knotted, its crown
    darker and more ragged)."""
    rng = np.random.default_rng(seed)
    s = h / 2.6
    f = Field("Trunk")
    c = Field("Leaves")
    r0 = (0.12 if young else 0.22) * s
    fork = h * (0.42 if not young else 0.5)
    f.add(RoundCone((0, 0, -0.06), (0, 0, fork), r0, r0 * 0.72, **wob(4.0 / s, 0.02 * s, seed)), k=0.0)
    if not young:
        for k in range(5):                                      # root flare
            a = 2 * math.pi * k / 5 + rng.uniform(-0.3, 0.3)
            f.add(RoundCone((math.cos(a) * r0 * 0.5, math.sin(a) * r0 * 0.5, 0.18 * s),
                            (math.cos(a) * r0 * 2.1, math.sin(a) * r0 * 2.1, -0.04), r0 * 0.45, r0 * 0.2), k=0.07 * s)
    if gnarled:
        for k in range(4):                                      # knots and burrs
            a = rng.uniform(0, 2 * math.pi)
            z = rng.uniform(0.2, 0.85) * fork
            f.add(Ellipsoid((math.cos(a) * r0 * 0.8, math.sin(a) * r0 * 0.8, z), (0.07 * s, 0.07 * s, 0.09 * s),
                            **wob(9.0 / s, 0.015 * s, seed + 30 + k)), k=0.04 * s)
        f.sub(Ellipsoid((r0 * 0.75, -r0 * 0.6, 0.3 * s), (0.07 * s, 0.07 * s, 0.16 * s)), k=0.02)     # a hollow
    tops = []
    n_limbs = 3 if young else 4
    a0 = rng.uniform(0, 2 * math.pi)
    for i in range(n_limbs):
        a = a0 + 2 * math.pi * i / n_limbs + rng.uniform(-0.35, 0.35)
        out = v3((math.cos(a), math.sin(a), 0.0))
        L = h * rng.uniform(0.45, 0.6)
        p0 = v3((0, 0, fork - 0.05 * s))
        p1 = p0 + out * L * 0.42 + v3((0, 0, L * 0.4))
        p2 = p1 + out * L * 0.45 + v3((0, 0, L * 0.2 + rng.uniform(-0.05, 0.1) * s))
        f.add(Chain([p0, p1, p2], [r0 * 0.6, r0 * 0.4, r0 * 0.18], k=0.03 * s, **wob(5.0 / s, 0.012 * s, seed * 10 + i)), k=0.06 * s)
        for j in range(2):                                      # twigs off each limb
            b = a + rng.uniform(-1.2, 1.2)
            ob = v3((math.cos(b), math.sin(b), 0.0))
            q0 = p1 + (p2 - p1) * rng.uniform(0.0, 0.6)
            q1 = q0 + ob * L * 0.3 + v3((0, 0, L * 0.18))
            f.add(RoundCone(q0, q1, r0 * 0.16, r0 * 0.07), k=0.02 * s)
            tops.append(q1)
        tops += [p2, p1 + v3((0, 0, 0.18 * s))]
    tops.append(v3((0, 0, h * 0.86)))
    ctr = sum(tops, v3((0, 0, 0))) / len(tops)
    darker = 0.8 if gnarled else 1.0
    for j, q in enumerate(tops):                                # the crown: lumpy clumps round the limb ends
        for k in range(3):
            o = v3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.2, 0.7))) * 0.2 * s
            r = s * rng.uniform(0.24, 0.34) * darker
            c.add(Ellipsoid(q + o, (r, r * 0.92, r * 0.72), **wob(10.0 / s, 0.045 * s, seed * 100 + j * 3 + k)), k=0.07 * s)
    for j in range(10):                                         # filling the dome
        u = rng.normal(size=3)
        u = u / np.linalg.norm(u)
        q = ctr + v3((u[0] * 0.62 * s, u[1] * 0.62 * s, abs(u[2]) * 0.34 * s + 0.12 * s))
        r = s * rng.uniform(0.3, 0.4)
        c.add(Ellipsoid(q, (r, r * 0.92, r * 0.7), **wob(10.0 / s, 0.045 * s, seed * 200 + j)), k=0.08 * s)
    return [("Trunk", f, fine(0.008, 0.016), "oak_bark"), ("Leaves", c, vx(h) * 0.9, "dark_leaves" if gnarled else "oak_leaves")]


def spruce(h=3.6, seed=0):
    """A tall dark spruce: a straight trunk, its crown a narrow spire of drooping tiers, ragged at their edges, the
    lowest sweeping near the ground."""
    rng = np.random.default_rng(seed)
    s = h / 3.6
    f = Field("Trunk")
    f.add(RoundCone((0, 0, -0.06), (0, 0, h * 0.95), 0.09 * s, 0.02 * s, **wob(5.0, 0.008, seed)))
    for k in range(4):
        a = 2 * math.pi * k / 4 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((math.cos(a) * 0.04 * s, math.sin(a) * 0.04 * s, 0.1 * s), (math.cos(a) * 0.2 * s, math.sin(a) * 0.2 * s, -0.03),
                        0.045 * s, 0.015 * s), k=0.04 * s)
    c = Field("Needles")
    n_t = 6
    for i in range(n_t):
        t = i / (n_t - 1)
        zb = h * (0.14 + 0.66 * t)
        rb = s * (0.78 - 0.56 * t) * rng.uniform(0.92, 1.08)
        th = h * (0.24 - 0.06 * t)
        c.add(cone((rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02)), zb, zb + th, rb, rb * 0.18,
                   wob(7.0 / s, 0.05 * s, seed * 10 + i)), k=0.04 * s)
        for j in range(7):                                      # drooping tips breaking the tier's edge
            a = 2 * math.pi * j / 7 + rng.uniform(-0.3, 0.3) + i
            q = v3((math.cos(a) * rb * 0.82, math.sin(a) * rb * 0.82, zb + 0.02 * s))
            c.add(Ellipsoid(q, (rb * 0.22, rb * 0.22, 0.07 * s), R=Rz(a), **wob(12.0 / s, 0.02 * s, seed * 50 + i * 7 + j)), k=0.04 * s)
    c.add(RoundCone((0, 0, h * 0.86), (0, 0, h * 1.02), 0.06 * s, 0.005), k=0.03 * s)            # the leader
    return [("Trunk", f, fine(0.006, 0.012), "spruce_bark"), ("Needles", c, vx(h) * 0.8, "needles")]


def dead_tree(h=2.2, seed=0):
    """A dead tree, long bare: a grey trunk split and leaning, its branches crooked and broken off short."""
    rng = np.random.default_rng(seed)
    s = h / 2.2
    f = Field("Trunk")
    lean = v3((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0.0)) * s
    pts = [v3((0, 0, -0.06)), v3((0, 0, h * 0.3)) + lean * 0.3, v3((0, 0, h * 0.62)) + lean * 0.7, v3((0, 0, h * 0.86)) + lean]
    f.add(Chain(pts, [0.15 * s, 0.11 * s, 0.075 * s, 0.04 * s], k=0.03, **wob(4.0 / s, 0.016 * s, seed)))
    for k in range(4):                                          # roots
        a = 2 * math.pi * k / 4 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((0, 0, 0.12 * s), (math.cos(a) * 0.34 * s, math.sin(a) * 0.34 * s, -0.04), 0.08 * s, 0.025 * s), k=0.05 * s)
    for j in range(6):
        a = rng.uniform(0, 2 * math.pi)
        p0 = at_height(pts, h * rng.uniform(0.35, 0.82))
        ob = v3((math.cos(a), math.sin(a), 0.0))
        L = h * rng.uniform(0.22, 0.38)
        p1 = p0 + ob * L * 0.55 + v3((0, 0, L * 0.35))
        p2 = p1 + unit(ob + v3((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 0.6))) * L * 0.45
        f.add(Chain([p0, p1, p2], [0.05 * s, 0.03 * s, 0.012 * s], k=0.012, **wob(7.0 / s, 0.006 * s, seed * 9 + j)), k=0.03 * s)
    f.sub(Ellipsoid(pts[-1] + v3((0, 0, 0.06 * s)), (0.05 * s, 0.05 * s, 0.1 * s)), k=0.02)           # the broken top
    return [("Trunk", f, fine(0.007, 0.014), "deadwood")]


# ------------------------------------------------------------------------------------------------ hedges, fields
def hedge(L=2.4, h=0.72, seed=0):
    """A stretch of hedgerow on its bank: hawthorn and hazel laid thick, bushy lumps along it, a few shoots standing
    up out of the top, white may blossom over it; the turf bank under it."""
    rng = np.random.default_rng(seed)
    bank = Field("Bank")
    bank.add(Ellipsoid((0, 0, -0.06), (L * 0.55, 0.42, 0.2), **wob(2.0, 0.02, seed)))
    ground_cut(bank, -0.02)
    c = Field("Leaves")
    n = int(L / 0.2)
    for j in range(n):
        x = -L / 2 + L * (j + 0.5) / n + rng.uniform(-0.05, 0.05)
        for k in range(2):
            q = v3((x, rng.uniform(-0.12, 0.12), h * rng.uniform(0.32, 0.72)))
            r = rng.uniform(0.17, 0.25)
            c.add(Ellipsoid(q, (r, r * 0.9, r * 0.95), **wob(12.0, 0.025, seed * 40 + j * 2 + k)), k=0.06)
    c.add(RoundBox((0, 0, h * 0.4), (L / 2 - 0.05, 0.2, h * 0.32), 0.15), k=0.08)
    for j in range(4):                                          # shoots standing up
        x = rng.uniform(-L / 2 + 0.2, L / 2 - 0.2)
        q = v3((x, rng.uniform(-0.08, 0.08), h + rng.uniform(0.0, 0.12)))
        c.add(Ellipsoid(q, (0.1, 0.09, 0.16), **wob(14.0, 0.02, seed * 70 + j)), k=0.05)
    cut_below(c, 0.0, 0, 0, L, 1.0)
    fl = Field("Blossom")
    for j in range(int(L * 16)):
        u = rng.uniform(-L / 2 + 0.1, L / 2 - 0.1)
        side = rng.choice([-1, 1])
        q = v3((u, side * rng.uniform(0.12, 0.26), h * rng.uniform(0.35, 0.95)))
        for _ in range(10):                                     # settled onto the leaves
            if c.eval(q[None, :].astype(F32), margin=0.3)[0] < 0.0:
                break
            q = q * v3((1.0, 0.92, 0.97))
        fl.add(Sphere(q, rng.uniform(0.016, 0.024)), k=0.0)
    return [("Bank", bank, fine(0.015, 0.03), "turf"), ("Leaves", c, fine(0.01, 0.02), "hedge"), ("Blossom", fl, fine(0.005, 0.01), "blossom")]


def haystack(seed=0, s=1.0):
    """A haystack: a round stack of hay built up into a steep dome, its sides combed down in tufts, a twist of hay rope
    round it, loose hay at its foot."""
    rng = np.random.default_rng(seed)
    f = Field("Hay")
    def stack(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        z = P[:, 2]
        t = np.clip(z / F32(1.0 * s), 0, 1)
        prof = F32(0.52 * s) * np.sqrt(np.clip(F32(1.0) - t ** F32(2.2), 0, 1)) + F32(0.05 * s) * np.clip(F32(0.15) - t, 0, 1) * 4
        a = np.arctan2(P[:, 1], P[:, 0])
        comb = F32(0.012 * s) * np.sin(a * F32(26) + z * F32(4)) * np.clip(t * 3, 0, 1)
        return (np.maximum(r - prof + comb, -z) * F32(0.8)).astype(F32)
    f.add(Func(stack, (-0.7 * s, -0.7 * s, -0.05), (0.7 * s, 0.7 * s, 1.05 * s), **wob(6.0, 0.02 * s, seed)))
    f.add(Torus((0, 0, 0.5 * s), 0.47 * s, 0.022 * s), k=0.01)                                       # the hay rope
    f.add(RoundCone((0, 0, 0.92 * s), (0.03, 0.02, 1.08 * s), 0.05 * s, 0.015 * s), k=0.03)           # the topknot
    for j in range(7):                                          # loose hay at its foot
        a = rng.uniform(0, 2 * math.pi)
        q = v3((math.cos(a) * 0.6 * s, math.sin(a) * 0.6 * s, 0.02))
        f.add(Ellipsoid(q, (0.14 * s, 0.09 * s, 0.035), R=Rz(a), **wob(14.0, 0.012, seed * 9 + j)), k=0.03)
    ground_cut(f)
    return [("Hay", f, fine(0.008, 0.016), "hay")]


def fence(L=2.0, h=0.5, seed=0):
    """A wattle fence: hazel rods woven between stakes, a hurdle of three panels."""
    rng = np.random.default_rng(seed)
    f = Field("Fence")
    n_st = 7
    xs = [-L / 2 + L * i / (n_st - 1) for i in range(n_st)]
    for i, x in enumerate(xs):
        f.add(RoundCone((x, 0, -0.06), (x, 0, h + 0.06), 0.024, 0.02, **wob(10.0, 0.004, seed + i)), k=0.0)
    for r in range(7):                                          # the weave: rods passing in front of and behind the stakes
        z = 0.06 + r * (h - 0.08) / 6
        pts = []
        for i, x in enumerate(xs):
            pts.append(v3((x, (0.025 if (i + r) % 2 == 0 else -0.025), z + rng.uniform(-0.008, 0.008))))
        f.add(Chain(pts, [0.016] * len(pts), k=0.01), k=0.004, label=5)
    ground_cut(f)
    return [("Fence", f, fine(0.005, 0.01), "wattle")]


# ------------------------------------------------------------------------------------------------ the farm
def _timber_frame(wd, hx, hy, z0, z1, door_x=None, seed=0):
    """Dark oak timbers on the face of a wall block: corner posts, sill and wall plates, studs and braces."""
    for sy in (-1, 1):
        y = sy * hy
        wd.add(RoundBox((0, y, z1 - 0.03), (hx + 0.02, 0.03, 0.035), 0.008), k=0.002, label=10)            # wall plate
        wd.add(RoundBox((0, y, z0 + 0.05), (hx + 0.02, 0.03, 0.04), 0.008), k=0.002, label=10)             # sill
        n = max(2, int(hx * 2 / 0.32))
        for i in range(n + 1):
            x = -hx + 2 * hx * i / n
            if door_x is not None and sy < 0 and abs(x - door_x) < 0.2:
                continue
            wd.add(RoundBox((x, y, (z0 + z1) / 2), (0.028, 0.03, (z1 - z0) / 2), 0.008), k=0.002, label=11)
        for i, sg in ((0, 1), (n - 1, -1)):                      # braces at the corners
            xa = -hx + 2 * hx * i / n
            xb = xa + 2 * hx / n * (1 if i == 0 else 1)
            a, b = v3((xa, y, z0 + 0.08)), v3((xb, y, z1 - 0.06))
            if i != 0:
                a, b = v3((xb, y, z0 + 0.08)), v3((xa, y, z1 - 0.06))
            wd.add(RoundCone(a, b, 0.024, 0.024), k=0.002, label=11)
    for sx in (-1, 1):
        x = sx * hx
        wd.add(RoundBox((x, 0, z1 - 0.03), (0.03, hy + 0.02, 0.035), 0.008), k=0.002, label=10)
        wd.add(RoundBox((x, 0, z0 + 0.05), (0.03, hy + 0.02, 0.04), 0.008), k=0.002, label=10)
        n = max(2, int(hy * 2 / 0.32))
        for i in range(n + 1):
            y = -hy + 2 * hy * i / n
            wd.add(RoundBox((x, y, (z0 + z1) / 2), (0.03, 0.028, (z1 - z0) / 2), 0.008), k=0.002, label=11)


def thatch_roof(rf, hx, hy, z_eave, z_ridge, over=0.18, axis="x", seed=0):
    """A thick thatched roof: a gable block with deep rounded eaves, combed down in courses, a ridge capping."""
    rf.add(gable((0, 0), hx + over, hy + over, z_eave - 0.04, z_ridge, axis=axis, over=0.0))
    g = rf.ops[-1][1]
    g.disp = lambda P: (F32(0.01) * np.sin(P[:, 2] * F32(48)) + NOISE.fbm(P * F32(9) + F32(seed), 2) * F32(0.015)).astype(F32)
    g.disp_amp = 0.03
    if axis == "x":
        rf.add(RoundBox((0, 0, z_ridge - 0.02), (hx + over - 0.04, 0.09, 0.05), 0.04), k=0.04, label=5)   # the ridge capping
    else:
        rf.add(RoundBox((0, 0, z_ridge - 0.02), (0.09, hy + over - 0.04, 0.05), 0.04), k=0.04, label=5)


def cottage(seed=0):
    """A cottage: walls of white daub between dark oak timbers on a low stone footing, a plank door, small shuttered
    windows; a deep thatched roof down to the eaves; a stone chimney at one end, smoke from it (game.gd MARK_SMOKE)."""
    rng = np.random.default_rng(seed)
    hx, hy, wh = 0.85, 0.55, 0.7
    w = Field("Walls")
    w.add(walls_box(0, 0, hx, hy, 0.0, wh, batter=0.0, amp=0.004, seed=seed))
    w.sub(RoundBox((0.25, -hy, 0.28), (0.12, 0.06, 0.28), 0.01), k=0.004)                       # the doorway
    for x in (-0.4,):
        w.sub(RoundBox((x, -hy, 0.44), (0.09, 0.06, 0.08), 0.008), k=0.003)
    w.sub(RoundBox((hx, 0.05, 0.44), (0.06, 0.08, 0.08), 0.008), k=0.003)
    st = Field("Footing")
    st.add(walls_box(0, 0, hx + 0.03, hy + 0.03, -0.03, 0.12, batter=0.03, amp=0.01, seed=seed + 1))
    wd = Field("Timber")
    _timber_frame(wd, hx + 0.01, hy + 0.01, 0.1, wh, door_x=0.25, seed=seed)
    wd.add(RoundBox((0.25, -hy - 0.005, 0.27), (0.11, 0.02, 0.27), 0.006), label=10)                  # the plank door
    for x in (-0.4,):
        for sd in (-1, 1):
            wd.add(RoundBox((x + sd * 0.13, -hy - 0.02, 0.44), (0.04, 0.012, 0.085), 0.004), label=5)      # shutters
    rf = Field("Roof")
    thatch_roof(rf, hx, hy, wh, wh + 0.72, over=0.2, axis="x", seed=seed)
    ch = Field("Chimney")
    ch.add(walls_box(-hx + 0.12, 0.12, 0.13, 0.13, 0.0, wh + 0.95, batter=0.02, amp=0.01, seed=seed + 3))
    ch.add(RoundBox((-hx + 0.12, 0.12, wh + 0.93), (0.16, 0.16, 0.04), 0.01), k=0.01)
    ch.sub(Cylinder((-hx + 0.12, 0.12, wh + 0.98), 0.07, 0.1), k=0.004)
    for part in (w, st, wd, rf, ch):
        ground_cut(part)
    return [("Walls", w, fine(0.007, 0.014), "daub"), ("Footing", st, fine(0.01, 0.02), "drystone"),
            ("Timber", wd, fine(0.005, 0.01), "timber"), ("Roof", rf, fine(0.008, 0.016), "thatch"),
            ("Chimney", ch, fine(0.008, 0.016), "drystone")]


def barn(seed=0):
    """A barn: a long timber-framed building on a stone footing, weatherboarded, its great double doors standing open
    on the hay inside; a steep thatched roof hipped at the ends."""
    hx, hy, wh = 1.15, 0.65, 0.8
    w = Field("Walls")
    w.add(walls_box(0, 0, hx, hy, 0.0, wh, batter=0.0, amp=0.004, seed=seed))
    w.sub(RoundBox((0, -hy, 0.36), (0.3, 0.12, 0.38), 0.01), k=0.004)                            # the great doorway
    w.paint(Func(lambda P: (F32(0.3) - np.abs(np.mod(P[:, 2], F32(0.09)) - F32(0.045)) * F32(10)).astype(F32), (-2, -2, -0.1), (2, 2, 1.2)), 5)
    st = Field("Footing")
    st.add(walls_box(0, 0, hx + 0.03, hy + 0.03, -0.03, 0.1, batter=0.03, amp=0.01, seed=seed + 1))
    wd = Field("Timber")
    _timber_frame(wd, hx + 0.01, hy + 0.01, 0.08, wh, door_x=0.0, seed=seed)
    for sd in (-1, 1):                                          # the doors, swung open
        wd.add(RoundBox((sd * 0.48, -hy - 0.16, 0.36), (0.02, 0.15, 0.35), 0.006, R=Rz(sd * 0.2)), label=10)
    hay = Field("Hay")
    hay.add(Ellipsoid((0, -0.1, 0.12), (0.3, 0.35, 0.3), **wob(10.0, 0.03, seed)), k=0.0)
    rf = Field("Roof")
    rf.add(convex([((0, 0, wh + 0.85), (0, 0.75, 1)), ((0, 0, wh + 0.85), (0, -0.75, 1)), ((0, 0, wh + 0.85), (0.9, 0, 1)),
                   ((0, 0, wh + 0.85), (-0.9, 0, 1)), ((0, 0, wh - 0.06), (0, 0, -1)),
                   ((hx + 0.22, 0, 0), (1, 0, 0)), ((-hx - 0.22, 0, 0), (-1, 0, 0)), ((0, hy + 0.22, 0), (0, 1, 0)), ((0, -hy - 0.22, 0), (0, -1, 0))],
                  (-hx - 0.4, -hy - 0.4, wh - 0.2), (hx + 0.4, hy + 0.4, wh + 1.0)), k=0.0)
    rf.ops[-1][1].disp = lambda P: (F32(0.01) * np.sin(P[:, 2] * F32(48)) + NOISE.fbm(P * F32(9) + F32(seed), 2) * F32(0.015)).astype(F32)
    rf.ops[-1][1].disp_amp = 0.03
    for part in (w, st, wd, hay, rf):
        ground_cut(part)
    return [("Walls", w, fine(0.007, 0.014), "boards"), ("Footing", st, fine(0.01, 0.02), "drystone"),
            ("Timber", wd, fine(0.005, 0.01), "timber"), ("Hay", hay, fine(0.01, 0.02), "hay"), ("Roof", rf, fine(0.009, 0.018), "thatch")]


def windmill(seed=0):
    """A post mill: a tall timber body (weatherboarded, a little gabled roof) turned on its great post, the post's
    braces down to two crossed trestles on stone piers; four lattice sails on the windshaft at its front; the ladder
    and tail pole behind."""
    out = []
    bx, by, bz0, bz1 = 0.42, 0.55, 1.05, 2.05
    body = Field("Body")
    body.add(RoundBox((0, 0, (bz0 + bz1) / 2), (bx, by, (bz1 - bz0) / 2), 0.02))
    body.paint(Func(lambda P: (F32(0.3) - np.abs(np.mod(P[:, 2], F32(0.09)) - F32(0.045)) * F32(10)).astype(F32), (-1, -1, 0.9), (1, 1, 2.2)), 5)
    body.sub(RoundBox((bx, 0.1, 1.5), (0.04, 0.09, 0.12), 0.01), k=0.003)                       # a little window
    rf = Field("Roof")
    rf.add(gable((0, 0), by + 0.06, bx + 0.08, bz1 - 0.02, bz1 + 0.34, axis="y"))
    wd = Field("Frame")
    wd.add(Cylinder((0, 0, 0.62), 0.09, 0.9, rr=0.02), k=0.0, label=11)                            # the great post
    for a in range(4):                                          # its quarterbars and the crosstrees
        ang = a * math.pi / 2 + math.pi / 4
        d = v3((math.cos(ang), math.sin(ang), 0.0))
        wd.add(RoundCone(d * 0.55 + v3((0, 0, 0.16)), v3((0, 0, 0.75)), 0.04, 0.035), k=0.01, label=11)
    for ang in (math.pi / 4, -math.pi / 4):
        d = v3((math.cos(ang), math.sin(ang), 0.0))
        wd.add(RoundCone(-d * 0.62 + v3((0, 0, 0.14)), d * 0.62 + v3((0, 0, 0.14)), 0.045, 0.045), k=0.01, label=10)
    for sd in (-1, 1):                                          # the ladder up to the door at its back
        wd.add(RoundCone((sd * 0.16, by + 0.75, 0.0), (sd * 0.16, by + 0.02, bz0 + 0.1), 0.02, 0.02), k=0.0, label=11)
    for k in range(7):
        t = (k + 0.5) / 7
        p = v3((0, by + 0.75 + (0.02 - 0.75) * t, (bz0 + 0.1) * t))
        wd.add(RoundCone(p + v3((-0.16, 0, 0)), p + v3((0.16, 0, 0)), 0.014, 0.014), k=0.0, label=10)
    wd.add(RoundCone((0, by - 0.05, bz0 + 0.05), (0, by + 1.1, 0.12), 0.03, 0.03), k=0.0, label=11)      # the tail pole
    # the sails on the windshaft at its front (-Y)
    hub = v3((0, -by - 0.12, bz1 - 0.1))
    wd.add(RoundCone(hub + v3((0, 0.2, 0.0)), hub, 0.06, 0.06), k=0.0, label=10)
    sails = Field("Sails")
    sails.add(Sphere(hub + v3((0, -0.02, 0)), 0.08))
    for k in range(4):
        ang = k * math.pi / 2 + 0.3
        d = v3((math.cos(ang), 0.0, math.sin(ang)))
        sd = v3((-math.sin(ang), 0.0, math.cos(ang)))
        a0, a1 = hub + d * 0.08, hub + d * 1.27
        sails.add(RoundCone(a0, a1, 0.025, 0.018), k=0.004, label=10)                              # the stock
        for i in range(11):                                       # the lattice: bars across, and the outer rail
            q = hub + d * (0.24 + 0.1 * i)
            sails.add(RoundCone(q, q + sd * 0.22, 0.008, 0.008), k=0.002, label=10)
        sails.add(RoundCone(hub + d * 0.22 + sd * 0.22, hub + d * 1.25 + sd * 0.22, 0.01, 0.01), k=0.002, label=10)
        sails.add(sailcloth(hub, d, sd), k=0.0, label=5)
    for part in (body, rf, wd):
        ground_cut(part)
    st = Field("Piers")
    for ang in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):
        d = v3((math.cos(ang), math.sin(ang), 0.0))
        st.add(RoundBox(d * 0.62 + v3((0, 0, 0.04)), (0.1, 0.1, 0.08), 0.02, **wob(10.0, 0.006, seed + int(ang * 10))), k=0.0)
    ground_cut(st)
    return [("Body", body, fine(0.007, 0.014), "boards"), ("Roof", rf, fine(0.007, 0.014), "boards"), ("Frame", wd, fine(0.005, 0.01), "timber"),
            ("Sails", sails, fine(0.004, 0.008), "sails"), ("Piers", st, fine(0.008, 0.016), "drystone")]


def sailcloth(hub, d, sd):
    """The sailcloth over half a sail's lattice: a thin panel from 0.27 to 1.21 along the stock, 0.2 across."""
    c = hub + d * 0.74 + sd * 0.11 + v3((0, 0.012, 0))
    R = np.stack([unit(sd), unit(np.cross(d, sd)), unit(d)], axis=1)
    return RoundBox(c, (0.1, 0.005, 0.47), 0.004, R=R)


def well(seed=0):
    """A well: a round wall of fieldstone, a winch on two posts under a little shingled roof, the bucket on its rope."""
    st = Field("Stone")
    st.add(Cylinder((0, 0, 0.24), 0.42, 0.48, rr=0.04, **wob(8.0, 0.01, seed)))
    st.sub(Cylinder((0, 0, 0.4), 0.3, 0.4), k=0.01)
    ground_cut(st)
    wd = Field("Timber")
    for sx in (-1, 1):
        wd.add(RoundBox((sx * 0.38, 0, 0.72), (0.035, 0.035, 0.5), 0.008), k=0.0, label=11)
    wd.add(RoundCone((-0.42, 0, 0.82), (0.42, 0, 0.82), 0.04, 0.04), k=0.01, label=10)             # the winch's drum
    wd.add(Torus((0, 0, 0.82), 0.045, 0.01, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004, label=8)
    wd.add(Chain([v3((0.44, 0, 0.82)), v3((0.52, 0, 0.82)), v3((0.52, -0.1, 0.72))], [0.012, 0.012, 0.012], k=0.004), k=0.004, label=6)   # crank
    wd.add(RoundCone((0, 0, 0.8), (0, 0, 0.42), 0.006, 0.006), k=0.0, label=8)                     # rope
    wd.add(Cylinder((0, 0, 0.36), 0.08, 0.11, rr=0.01), k=0.004, label=10)                          # the bucket
    rf = Field("Roof")
    rf.add(gable((0, 0), 0.5, 0.36, 1.18, 1.5, axis="x"))
    rf.sub(gable((0, 0), 0.56, 0.3, 1.14, 1.42, axis="x"), k=0.004)
    return [("Stone", st, fine(0.007, 0.014), "drystone"), ("Timber", wd, fine(0.005, 0.01), "timber"), ("Roof", rf, fine(0.006, 0.012), "boards")]


def scarecrow(seed=0):
    """A scarecrow on its pole in the field: a cross of poles, a sacking head with a stitched face under a floppy hat,
    a ragged coat stuffed with straw (straw poking from the sleeves), a crow on one arm."""
    wd = Field("Poles")
    wd.add(RoundCone((0, 0, -0.06), (0, 0, 1.25), 0.03, 0.025), k=0.0)
    wd.add(RoundCone((-0.5, 0, 0.98), (0.5, 0, 0.98), 0.022, 0.022), k=0.01)
    cl = Field("Coat")
    cl.add(RoundCone((0, 0, 0.62), (0, 0, 1.0), 0.17, 0.14, **wob(10.0, 0.01, seed)), k=0.0)
    for sx in (-1, 1):
        cl.add(RoundCone((sx * 0.1, 0, 0.98), (sx * 0.4, 0, 0.97), 0.07, 0.06, **wob(12.0, 0.008, seed + sx)), k=0.04)
    cl.sub(RoundBox((0, 0, 0.58), (0.2, 0.2, 0.06), 0.0), k=0.0)
    for k in range(5):                                          # ragged hem
        a = 2 * math.pi * k / 5
        cl.sub(Ellipsoid((math.cos(a) * 0.17, math.sin(a) * 0.17, 0.64), (0.05, 0.05, 0.05)), k=0.01)
    hd = Field("Head")
    hd.add(Ellipsoid((0, 0, 1.14), (0.11, 0.1, 0.12), **wob(10.0, 0.008, seed)), k=0.0)
    hd.paint(Chain([v3((-0.05, -0.1, 1.1)), v3((0, -0.11, 1.08)), v3((0.05, -0.1, 1.1))], [0.006, 0.006, 0.006], k=0.003), 5)   # the stitched grin
    for sx in (-1, 1):
        hd.paint(Sphere((sx * 0.04, -0.1, 1.16), 0.014), 5)
    hat = Field("Hat")
    hat.add(Cylinder((0, 0, 1.24), 0.19, 0.02, rr=0.008), k=0.0)
    hat.add(RoundCone((0, 0, 1.24), (0.02, 0.01, 1.38), 0.09, 0.05), k=0.03)
    straw = Field("Straw")
    for sx in (-1, 1):
        for k in range(5):
            a = k * 0.5 - 1.0
            straw.add(RoundCone((sx * 0.44, 0, 0.97), (sx * 0.52, math.sin(a) * 0.06, 0.97 - 0.04 + math.cos(a) * 0.05), 0.006, 0.003), k=0.002)
    crow = Field("Crow")
    cw = v3((0.36, 0.0, 1.03))
    crow.add(Ellipsoid(cw + v3((0, 0, 0.05)), (0.035, 0.07, 0.04), R=euler(0.3, 0, 0)))
    crow.add(Sphere(cw + v3((0, -0.06, 0.1)), 0.028), k=0.01)
    crow.add(RoundCone(cw + v3((0, -0.08, 0.1)), cw + v3((0, -0.12, 0.095)), 0.01, 0.002), k=0.003)
    crow.add(RoundCone(cw + v3((0, 0.05, 0.06)), cw + v3((0, 0.12, 0.03)), 0.025, 0.005), k=0.01)
    for part in (wd,):
        ground_cut(part)
    return [("Poles", wd, fine(0.005, 0.01), "deadwood"), ("Coat", cl, fine(0.006, 0.012), "sacking"), ("Head", hd, fine(0.005, 0.01), "sacking"),
            ("Hat", hat, fine(0.005, 0.01), "hay"), ("Straw", straw, fine(0.004, 0.008), "hay"), ("Crow", crow, fine(0.004, 0.008), "dark")]


def hay_cart(seed=0):
    """A two-wheeled hay cart, its shafts resting on the ground: a plank bed with rails, heaped with hay; spoked wheels
    with iron tyres."""
    wd = Field("Cart")
    wd.add(RoundBox((0, 0, 0.42), (0.55, 0.36, 0.03), 0.01), k=0.0, label=10)
    for sy in (-1, 1):
        wd.add(RoundBox((0, sy * 0.36, 0.56), (0.55, 0.02, 0.012), 0.004), k=0.002, label=10)
        for i in range(6):
            x = -0.5 + 0.2 * i
            wd.add(RoundBox((x, sy * 0.36, 0.5), (0.012, 0.012, 0.08), 0.004), k=0.002, label=11)
    for sy in (-1, 1):                                          # the shafts, down to the ground in front
        wd.add(RoundCone((0.4, sy * 0.24, 0.4), (1.25, sy * 0.2, 0.04), 0.025, 0.02), k=0.004, label=11)
    whl = Field("Wheels")
    for sy in (-1, 1):
        c = v3((0.0, sy * 0.44, 0.32))
        R = rot_from_axes(z_axis=(0, 1, 0))
        whl.add(Torus(c, 0.3, 0.025, R=R), k=0.0, label=10)
        whl.add(Torus(c, 0.31, 0.014, R=R), k=0.002, label=6)                                     # iron tyre
        whl.add(Cylinder(c, 0.06, 0.08, rr=0.01, R=R), k=0.004, label=10)
        for k in range(8):
            a = 2 * math.pi * k / 8
            whl.add(RoundCone(c, c + v3((math.cos(a) * 0.29, 0, math.sin(a) * 0.29)), 0.012, 0.01), k=0.002, label=11)
    whl.add(RoundCone((0, -0.46, 0.32), (0, 0.46, 0.32), 0.022, 0.022), k=0.0, label=6)
    hay = Field("Hay")
    hay.add(Ellipsoid((0, 0, 0.66), (0.6, 0.4, 0.3), **wob(8.0, 0.03, seed)), k=0.0)
    hay.add(RoundBox((0, 0, 0.5), (0.54, 0.34, 0.08), 0.05), k=0.05)
    ground_cut(wd)
    return [("Cart", wd, fine(0.005, 0.01), "timber"), ("Wheels", whl, fine(0.004, 0.008), "timber"), ("Hay", hay, fine(0.009, 0.018), "hay")]


# ------------------------------------------------------------------------------------------------ the dark wood
def fern(seed=0, s=1.0):
    """A clump of ferns: arching fronds from a crown, their leaflets in pairs shrinking to the tip."""
    rng = np.random.default_rng(seed)
    f = Field("Fern")
    for k in range(8):
        a = 2 * math.pi * k / 8 + rng.uniform(-0.25, 0.25)
        d = v3((math.cos(a), math.sin(a), 0.0))
        L = rng.uniform(0.42, 0.56) * s
        pts = [d * (0.02 * s) + v3((0, 0, 0.02))]
        for i in range(1, 6):
            u = i / 5
            pts.append(d * (L * u) + v3((0, 0, (0.34 * math.sin(math.pi * u * 0.75) - 0.12 * u * u) * L)))
        f.add(Chain(pts, [0.008 * s] * len(pts), k=0.004), k=0.004, label=7)
        side = unit(np.cross(v3((0, 0, 1)), d))
        for i in range(1, 12):
            u = i / 12
            sidx = u * 5
            j = min(int(sidx), 4)
            p = pts[j] + (pts[j + 1] - pts[j]) * (sidx - j)
            sz = 0.07 * s * (1.0 - 0.7 * u)
            for sg in (-1, 1):
                q = p + side * (sg * sz * 0.9) + v3((0, 0, -0.01 * u))
                f.add(Ellipsoid(q, (sz, 0.004 * s, sz * 0.32), R=R_xz(side * sg + d * 0.4, (0, 0, 1))), k=0.004)
    ground_cut(f)
    return [("Fern", f, fine(0.004, 0.008), "fern")]


def toadstools(seed=0, big=1.0):
    """A ring of fly agarics: red caps flecked white on white stems, one big, the rest smaller round it."""
    rng = np.random.default_rng(seed)
    f = Field("Caps")
    st = Field("Stems")
    spots = [(0.0, 0.0, 0.16 * big, 0.3 * big)] + [(math.cos(a) * 0.2 * big, math.sin(a) * 0.2 * big, rng.uniform(0.06, 0.1) * big,
                                                     rng.uniform(0.12, 0.2) * big) for a in rng.uniform(0, 2 * math.pi, 5)]
    for (x, y, r, h) in spots:
        st.add(RoundCone((x, y, -0.03), (x, y, h), r * 0.3, r * 0.24), k=0.0)
        st.add(Torus((x, y, h * 0.72), r * 0.3, r * 0.06), k=0.01)                                  # the ring on the stem
        top = v3((x, y, h))
        f.add(Ellipsoid(top + v3((0, 0, r * 0.08)), (r, r, r * 0.62)), k=0.0)
        f.sub(Ellipsoid(top + v3((0, 0, -r * 0.22)), (r * 0.9, r * 0.9, r * 0.36)), k=0.01)
        for k in range(10):
            a = rng.uniform(0, 2 * math.pi)
            el = rng.uniform(0.3, 1.2)
            p = top + v3((math.cos(a) * r * math.cos(el), math.sin(a) * r * math.cos(el), r * 0.08 + r * 0.62 * math.sin(el)))
            f.add(Sphere(p, r * 0.1), k=0.004, label=5)
    ground_cut(st)
    return [("Caps", f, fine(0.004, 0.008), "toadstool"), ("Stems", st, fine(0.004, 0.008), "mushroom")]


def hut(seed=0):
    """A woodcutter's hut: walls of logs laid crosswise and notched at the corners, a low door, a roof of turf on
    planks (grass growing on it); a chopping block with the axe in it and a woodpile stacked against the wall."""
    rng = np.random.default_rng(seed)
    hx, hy, wh = 0.7, 0.5, 0.62
    lg = Field("Logs")
    n = 7
    for i in range(n):
        z = 0.05 + i * (wh - 0.05) / n
        if i % 2 == 0:
            for sy in (-1, 1):
                lg.add(RoundCone((-hx - 0.12, sy * hy, z), (hx + 0.12, sy * hy, z), 0.05, 0.05, **wob(9.0, 0.005, seed + i)), k=0.004)
        else:
            for sx in (-1, 1):
                lg.add(RoundCone((sx * hx, -hy - 0.12, z), (sx * hx, hy + 0.12, z), 0.05, 0.05, **wob(9.0, 0.005, seed + i + 20)), k=0.004)
    lg.add(RoundBox((0, 0, wh / 2), (hx - 0.02, hy - 0.02, wh / 2), 0.02), k=0.02)
    lg.sub(RoundBox((0.15, -hy, 0.25), (0.12, 0.12, 0.25), 0.01), k=0.004)                        # the door
    lg.add(RoundBox((0.15, -hy + 0.02, 0.25), (0.11, 0.02, 0.24), 0.006), k=0.0, label=5)
    rf = Field("Roof")
    rf.add(gable((0, 0), hx + 0.22, hy + 0.2, wh - 0.02, wh + 0.52, axis="x"))
    rf.ops[-1][1].disp = lambda P: NOISE.fbm(P * F32(7) + F32(seed), 3) * F32(0.02)
    rf.ops[-1][1].disp_amp = 0.025
    wd = Field("Wood")
    wd.add(Cylinder((0.62, -0.78, 0.14), 0.15, 0.28, rr=0.02), k=0.0, label=5)                       # the chopping block
    ax = unit(v3((0.2, -0.3, 1.0)))
    wd.add(RoundCone(v3((0.62, -0.78, 0.29)), v3((0.62, -0.78, 0.29)) + ax * 0.5, 0.016, 0.014), k=0.0, label=11)   # the axe's haft
    wd.add(RoundBox(v3((0.62, -0.78, 0.3)) + unit(v3((1, 0.6, 0))) * 0.0, (0.07, 0.012, 0.05), 0.006, R=Rz(0.6)), k=0.004, label=6)   # its head
    for i in range(4):                                          # the woodpile against the wall
        for j in range(6 - i):
            x = -0.55 + 0.12 * j + 0.06 * i
            wd.add(Cylinder((x, -hy - 0.12, 0.06 + 0.1 * i), 0.055, 0.3, rr=0.01, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.0, label=5)
    for part in (lg, rf, wd):
        ground_cut(part)
    return [("Logs", lg, fine(0.006, 0.012), "logs"), ("Roof", rf, fine(0.009, 0.018), "turf_roof"), ("Wood", wd, fine(0.005, 0.01), "logs")]


def chapel(seed=0):
    """A ruined chapel in the wood: walls of grey stone broken off at uneven heights, a pointed (Gothic) window in the
    east gable, a doorway with a pointed arch, a little bell-cote on the west gable, fallen stones; ivy creeping over it."""
    rng = np.random.default_rng(seed)
    hx, hy, wh = 1.0, 0.6, 1.0
    w = Field("Walls")
    t = 0.1
    w.add(walls_box(0, 0, hx, hy, 0.0, wh, batter=0.0, amp=0.008, seed=seed))
    w.sub(RoundBox((0, 0, wh / 2 + 0.05), (hx - t, hy - t, wh / 2 + 0.2), 0.01), k=0.0)             # hollow, roofless
    for sx in (-1, 1):                                          # the gables
        w.add(convex([((sx * hx, 0, 0), (sx, 0, 0)), ((sx * (hx - t), 0, 0), (-sx, 0, 0)), ((0, 0, wh + 0.62), (0, 0.9, 1)),
                      ((0, 0, wh + 0.62), (0, -0.9, 1)), ((0, 0, wh - 0.05), (0, 0, -1))],
                     (-hx - 0.2, -hy - 0.2, wh - 0.2), (hx + 0.2, hy + 0.2, wh + 0.8)), k=0.0)
    def arch(cx, cy, cz, half_w, h, axis):                      # a pointed arch opening (two circles' intersection over a box)
        R_ = half_w * 1.6
        if axis == "x":
            a1, a2 = v3((cx, cy - (R_ - half_w), cz)), v3((cx, cy + (R_ - half_w), cz))
            box = RoundBox((cx, cy, cz - h / 2), (0.3, half_w, h / 2), 0.0)
            cyl = lambda c: Cylinder(c, R_, 0.6, R=rot_from_axes(z_axis=(1, 0, 0)))
        else:
            a1, a2 = v3((cx - (R_ - half_w), cy, cz)), v3((cx + (R_ - half_w), cy, cz))
            box = RoundBox((cx, cy, cz - h / 2), (half_w, 0.3, h / 2), 0.0)
            cyl = lambda c: Cylinder(c, R_, 0.6, R=rot_from_axes(z_axis=(0, 1, 0)))
        w.sub(box, k=0.0)
        top = Field("Arch")
        top.add(cyl(a1))
        top.inter(cyl(a2))
        top.inter(Plane((cx, cy, cz), (0, 0, -1)))
        w.sub(_FieldPrim(top), k=0.0)
    arch(hx, 0.0, wh + 0.1, 0.16, 0.55, "x")                     # the east window
    arch(0.25, -hy, 0.52, 0.16, 0.52, "y")                       # the doorway
    arch(-0.4, -hy, 0.75, 0.1, 0.3, "y")                         # a side window
    # broken off: bites out of the wall tops, more on one side
    for k in range(6):
        x = rng.uniform(-hx, hx)
        sy = rng.choice([-1, 1])
        w.sub(Ellipsoid((x, sy * hy, wh + rng.uniform(-0.05, 0.25)), (rng.uniform(0.2, 0.4), 0.2, rng.uniform(0.25, 0.45)),
                        **wob(8.0, 0.03, seed + k)), k=0.02)
    w.sub(Ellipsoid((0.4, hy, wh + 0.1), (0.5, 0.25, 0.55)), k=0.02)
    # the bell-cote on the west gable
    w.add(RoundBox((-hx + 0.03, 0, wh + 0.75), (0.07, 0.16, 0.16), 0.01), k=0.01)
    w.sub(RoundBox((-hx + 0.03, 0, wh + 0.74), (0.12, 0.08, 0.1), 0.02), k=0.004)
    w.add(gable((-hx + 0.03, 0), 0.1, 0.2, wh + 0.88, wh + 1.02, axis="x"), k=0.01)
    stones = Field("Fallen")
    for k in range(8):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(hx + 0.15, hx + 0.5)
        q = v3((math.cos(a) * r, math.sin(a) * r * 0.75, 0.05))
        stones.add(RoundBox(q, (rng.uniform(0.07, 0.12), rng.uniform(0.05, 0.08), rng.uniform(0.04, 0.07)), 0.02, R=Rz(rng.uniform(0, 3)),
                            **wob(10.0, 0.008, seed + 40 + k)), k=0.0)
    ivy = Field("Ivy")
    for k in range(10):                                         # ivy climbing the walls in clumps
        sx = rng.choice([-1, 1])
        if rng.uniform() < 0.5:
            q = v3((rng.uniform(-hx, hx), sx * (hy + 0.03), rng.uniform(0.1, 0.8)))
        else:
            q = v3((sx * (hx + 0.03), rng.uniform(-hy, hy), rng.uniform(0.1, 0.9)))
        for j in range(4):
            o = v3((rng.uniform(-0.1, 0.1), rng.uniform(-0.03, 0.03), rng.uniform(-0.12, 0.12)))
            ivy.add(Ellipsoid(q + o, (0.09, 0.05, 0.09), **wob(16.0, 0.02, seed * 30 + k * 4 + j)), k=0.04)
    for part in (w, stones, ivy):
        ground_cut(part)
    fl = Field("Floor")
    fl.add(RoundBox((0, 0, 0.0), (hx - t, hy - t, 0.02), 0.01, **wob(6.0, 0.004, seed)), k=0.0)
    return [("Walls", w, fine(0.008, 0.016), "chapel_stone"), ("Fallen", stones, fine(0.008, 0.016), "chapel_stone"),
            ("Ivy", ivy, fine(0.008, 0.016), "ivy"), ("Floor", fl, fine(0.01, 0.02), "flags")]


class _FieldPrim:
    """A Field used as a primitive (its distance, its bounds)."""

    def __init__(self, fd):
        self.fd = fd
        self.lo, self.hi = None, None
        los = [p.lo for kind, p, k, l in fd.ops if kind == "add"]
        his = [p.hi for kind, p, k, l in fd.ops if kind == "add"]
        self.lo, self.hi = np.min(los, 0), np.max(his, 0)

    def __call__(self, P):
        return self.fd.eval(P)


def wayside_cross(seed=0):
    """A wayside cross: a weathered stone cross with a ring round its head (a wheel cross) on a stepped base, lichen on
    it, flowers left at its foot."""
    st = Field("Stone")
    st.add(RoundBox((0, 0, 0.06), (0.3, 0.3, 0.06), 0.015, **wob(8.0, 0.006, seed)), k=0.0)
    st.add(RoundBox((0, 0, 0.17), (0.2, 0.2, 0.05), 0.015, **wob(8.0, 0.006, seed + 1)), k=0.0)
    st.add(RoundBox((0, 0, 0.62), (0.055, 0.045, 0.42), 0.012, **wob(10.0, 0.004, seed + 2)), k=0.01)
    st.add(RoundBox((0, 0, 0.9), (0.22, 0.045, 0.05), 0.012), k=0.01)
    st.add(Torus((0, 0, 0.9), 0.13, 0.022, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.006)
    fl = Field("Flowers")
    for k in range(6):
        a = k * 1.1
        fl.add(Sphere((math.cos(a) * 0.12 - 0.1, -0.24 + math.sin(a) * 0.03, 0.03), 0.025), k=0.0)
    ground_cut(st)
    return [("Stone", st, fine(0.005, 0.01), "chapel_stone"), ("Flowers", fl, fine(0.004, 0.008), "blossom")]


# ------------------------------------------------------------------------------------------------ the siege camp
def pavilion(seed=0, r=0.62, h=0.75, top=1.35):
    """A round pavilion: striped canvas walls (red and white panels, a scalloped valance with a blue border) under a
    conical roof, its door flaps tied back, guy ropes pegged out, a pennant flying from its pole."""
    c = Field("Canvas")
    def walls(P):
        q = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.abs(q - F32(r)) - F32(0.012), np.maximum(-P[:, 2], P[:, 2] - F32(h))).astype(F32)
    c.add(Func(walls, (-r - 0.1, -r - 0.1, -0.05), (r + 0.1, r + 0.1, h + 0.05)), k=0.0)
    c.add(cone((0, 0), h - 0.02, top, r + 0.16, 0.03), k=0.02)
    for k in range(16):                                         # the valance's scallops
        a = 2 * math.pi * k / 16
        c.add(Ellipsoid((math.cos(a) * (r + 0.15), math.sin(a) * (r + 0.15), h - 0.04), (0.11, 0.11, 0.07), R=Rz(a)), k=0.01)
    c.sub(RoundBox((0, -r, 0.3), (0.15, 0.1, 0.3), 0.02), k=0.004)                                 # the door
    for sd in (-1, 1):
        c.add(Ellipsoid((sd * 0.2, -r - 0.03, 0.3), (0.06, 0.03, 0.3), R=Rz(sd * 0.4)), k=0.01)       # its flaps tied back
    def stripes(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        return (np.abs(np.mod(a * F32(8.0 / math.pi), F32(2.0)) - F32(1.0)) - F32(0.5)).astype(F32)
    c.paint(Func(stripes, (-r - 0.3, -r - 0.3, -0.1), (r + 0.3, r + 0.3, top + 0.1)), 5)
    c.paint(Func(lambda P: (np.abs(P[:, 2] - F32(h - 0.06)) - F32(0.03)).astype(F32), (-r - 0.3, -r - 0.3, -0.1), (r + 0.3, r + 0.3, top + 0.1)), 6)
    wd = Field("Pole")
    wd.add(RoundCone((0, 0, top - 0.05), (0, 0, top + 0.42), 0.02, 0.015), k=0.0)
    wd.add(Sphere((0, 0, top + 0.43), 0.03), k=0.004, label=6)
    for k in range(6):                                          # guy ropes to their pegs
        a = 2 * math.pi * k / 6 + 0.3
        p0 = v3((math.cos(a) * (r + 0.1), math.sin(a) * (r + 0.1), h - 0.05))
        p1 = v3((math.cos(a) * (r + 0.55), math.sin(a) * (r + 0.55), 0.04))
        wd.add(RoundCone(p0, p1, 0.006, 0.006), k=0.0, label=8)
        wd.add(RoundCone(p1 + v3((0, 0, -0.06)), p1 + v3((0, 0, 0.06)), 0.012, 0.01), k=0.004)
    fl = Field("Pennant")
    p0 = v3((0, 0, top + 0.38))
    fl.add(convex([((0, 0, top + 0.38), (0, 0, 1)), ((0, 0, top + 0.24), (0, 0, -1)), ((0.42, 0, top + 0.31), (1, 0, 0.0)),
                   ((0, 0.012, 0), (0, 1, 0)), ((0, -0.012, 0), (0, -1, 0)), ((0.0, 0, top + 0.38), (0.25, 0, 1)), ((0.0, 0, top + 0.24), (0.25, 0, -1))],
                  (-0.05, -0.1, top + 0.2), (0.5, 0.1, top + 0.42)), k=0.0)
    fl.ops[-1][1].disp = lambda P: (F32(0.015) * np.sin(P[:, 0] * F32(18))).astype(F32)
    fl.ops[-1][1].disp_amp = 0.016
    for part in (c, wd):
        ground_cut(part)
    return [("Canvas", c, fine(0.007, 0.014), "canvas"), ("Pole", wd, fine(0.005, 0.01), "timber"), ("Pennant", fl, fine(0.005, 0.01), "banner")]


def ridge_tent(seed=0, L=0.9, w=0.55, h=0.62):
    """A soldiers' ridge tent: plain canvas over a ridge pole, its ends closed, pegged down, a cooking pot by it."""
    c = Field("Canvas")
    c.add(gable((0, 0), L, w, 0.0, h, axis="x"), k=0.0)
    c.sub(gable((0, 0), L - 0.05, w - 0.04, -0.05, h - 0.035, axis="x"), k=0.0)
    c.sub(RoundBox((L, 0, 0.18), (0.08, 0.14, 0.18), 0.02), k=0.004)                               # its door
    c.paint(Func(lambda P: (np.abs(P[:, 2] - F32(0.08)) - F32(0.03)).astype(F32), (-2, -2, -0.1), (2, 2, 1)), 6)
    wd = Field("Poles")
    for sx in (-1, 1):
        wd.add(RoundCone((sx * L, 0, -0.04), (sx * L, 0, h + 0.08), 0.02, 0.018), k=0.0)
    wd.add(RoundCone((-L - 0.04, 0, h + 0.01), (L + 0.04, 0, h + 0.01), 0.018, 0.018), k=0.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p0 = v3((sx * L * 0.7, sy * w, 0.05))
            wd.add(RoundCone(p0, p0 + v3((0, sy * 0.25, -0.05)), 0.006, 0.006), k=0.0, label=8)
    pot = Field("Pot")
    pot.add(Ellipsoid((L + 0.35, -0.3, 0.12), (0.12, 0.12, 0.1)), k=0.0)
    pot.sub(Cylinder((L + 0.35, -0.3, 0.2), 0.08, 0.06), k=0.01)
    for part in (c, wd, pot):
        ground_cut(part)
    return [("Canvas", c, fine(0.007, 0.014), "canvas"), ("Poles", wd, fine(0.005, 0.01), "timber"), ("Pot", pot, fine(0.005, 0.01), "iron")]


def mantlet(seed=0, L=1.2, h=0.9):
    """A mantlet: a wall of planks on two props, leaning, an archer's slot cut in it, a few arrows stuck in its face."""
    rng = np.random.default_rng(seed)
    wd = Field("Planks")
    R = euler(0.22, 0, 0)
    for i in range(7):
        x = -L / 2 + L * (i + 0.5) / 7
        wd.add(RoundBox(R @ v3((x, 0, h / 2)), (L / 14 - 0.006, 0.025, h / 2 + rng.uniform(-0.02, 0.04)), 0.008, R=R), k=0.002, label=10)
    for z in (0.18, h - 0.18):
        wd.add(RoundBox(R @ v3((0, 0.045, z)), (L / 2, 0.02, 0.04), 0.008, R=R), k=0.004, label=11)
    for sx in (-1, 1):                                          # its props behind it
        wd.add(RoundCone(R @ v3((sx * L * 0.35, 0.05, h * 0.85)), v3((sx * L * 0.35, 0.55, -0.03)), 0.03, 0.03), k=0.004, label=11)
    wd.sub(RoundBox(R @ v3((0.12, 0, h * 0.62)), (0.12, 0.1, 0.03), 0.01, R=R), k=0.004)          # the archer's slot
    ar = Field("Arrows")
    for k in range(4):
        p = R @ v3((rng.uniform(-L * 0.4, L * 0.4), -0.03, rng.uniform(0.25, h - 0.15)))
        d = unit(v3((rng.uniform(-0.2, 0.2), -1.0, rng.uniform(-0.1, 0.2))))
        ar.add(RoundCone(p, p + d * 0.3, 0.007, 0.007), k=0.0)
        for j in range(3):
            a = 2 * math.pi * j / 3
            ar.add(Ellipsoid(p + d * 0.27 + v3((math.cos(a) * 0.012, 0, math.sin(a) * 0.012)), (0.003, 0.03, 0.014), R=rot_from_axes(y_axis=d)), k=0.002, label=8)
    ground_cut(wd)
    return [("Planks", wd, fine(0.005, 0.01), "timber"), ("Arrows", ar, fine(0.004, 0.008), "arrows")]


def ram(seed=0):
    """A covered battering ram: a timber frame on four solid wheels under a steep roof of hides, the ram (a great log
    with an iron head) slung by chains from the ridge, its head poking out in front."""
    wd = Field("Frame")
    L, W, H = 0.95, 0.42, 0.9
    for sx in (-1, 1):
        for sy in (-1, 1):
            wd.add(RoundBox((sx * L * 0.9, sy * W, H / 2 + 0.15), (0.035, 0.035, H / 2), 0.008), k=0.0, label=11)
    for sy in (-1, 1):
        wd.add(RoundBox((0, sy * W, 0.2), (L, 0.035, 0.04), 0.008), k=0.004, label=10)
    whl = Field("Wheels")
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = v3((sx * L * 0.62, sy * (W + 0.07), 0.18))
            R = rot_from_axes(z_axis=(0, 1, 0))
            whl.add(Cylinder(c, 0.18, 0.06, rr=0.015, R=R), k=0.0, label=10)
            whl.add(Torus(c, 0.18, 0.012, R=R), k=0.003, label=6)
    hide = Field("Hides")
    hide.add(gable((0, 0), L + 0.05, W + 0.16, H + 0.05, H + 0.6, axis="x"), k=0.0)
    hide.sub(gable((0, 0), L + 0.2, W + 0.1, H - 0.02, H + 0.52, axis="x"), k=0.0)
    hide.ops[-2][1].disp = lambda P: (NOISE.fbm(P * F32(6) + F32(seed), 2) * F32(0.015)).astype(F32)
    hide.ops[-2][1].disp_amp = 0.02
    hide.paint(Func(lambda P: (F32(0.25) - np.abs(np.mod(P[:, 0], F32(0.32)) - F32(0.16)) * F32(8)).astype(F32), (-2, -2, 0), (2, 2, 2)), 5)   # seams
    rm = Field("Ram")
    rm.add(RoundCone((L + 0.45, 0, 0.62), (-L + 0.1, 0, 0.62), 0.1, 0.11, **wob(6.0, 0.006, seed)), k=0.0, label=10)
    rm.add(RoundCone((L + 0.42, 0, 0.62), (L + 0.6, 0, 0.62), 0.13, 0.06), k=0.01, label=6)        # its iron head
    for x in (-0.3, 0.45):
        rm.add(RoundCone((x, 0, 0.66), (x, 0, H + 0.45), 0.012, 0.012), k=0.004, label=6)         # chains to the ridge
        rm.add(Torus((x, 0, 0.62), 0.12, 0.014, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004, label=6)
    for part in (wd, whl):
        ground_cut(part)
    return [("Frame", wd, fine(0.005, 0.01), "timber"), ("Wheels", whl, fine(0.005, 0.01), "timber"), ("Hides", hide, fine(0.008, 0.016), "hide"),
            ("Ram", rm, fine(0.006, 0.012), "ram")]


def siege_tower(seed=0):
    """A siege tower: a tall timber frame on solid wheels, three storeys, faced with wet hides against fire arrows, a
    drawbridge hinged at the top of its front, raised; a fighting deck behind a parapet at the top."""
    W, D, H = 0.6, 0.6, 2.7
    wd = Field("Frame")
    for sx in (-1, 1):
        for sy in (-1, 1):
            wd.add(RoundBox((sx * W, sy * D, H / 2), (0.05, 0.05, H / 2), 0.01), k=0.0, label=11)
    for z in (0.25, 1.05, 1.85, H - 0.05):
        for sy in (-1, 1):
            wd.add(RoundBox((0, sy * D, z), (W + 0.04, 0.04, 0.04), 0.008), k=0.004, label=10)
        for sx in (-1, 1):
            wd.add(RoundBox((sx * W, 0, z), (0.04, D + 0.04, 0.04), 0.008), k=0.004, label=10)
    for sx in (-1, 1):                                          # bracing on the sides
        for (za, zb) in ((0.25, 1.05), (1.05, 1.85), (1.85, H - 0.05)):
            wd.add(RoundCone((sx * W, -D, za), (sx * W, D, zb), 0.03, 0.03), k=0.004, label=11)
    wd.add(RoundBox((0, 0, H + 0.12), (W + 0.06, D + 0.06, 0.12), 0.01), k=0.004, label=10)       # the parapet
    wd.sub(RoundBox((0, 0, H + 0.2), (W - 0.02, D - 0.02, 0.15), 0.01), k=0.004)
    for sx in (-1, 0, 1):
        for sy in (-1, 1):
            wd.add(RoundBox((sx * W * 0.7, sy * (D + 0.06), H + 0.32), (0.08, 0.03, 0.08), 0.01), k=0.004, label=10)
    br = Field("Bridge")                                        # the drawbridge, raised against its front
    br.add(RoundBox((0, -D - 0.08, H - 0.45), (W - 0.06, 0.035, 0.42), 0.01), k=0.0, label=10)
    for i in range(5):
        br.add(RoundBox((-W + 0.12 + i * (2 * W - 0.24) / 4, -D - 0.12, H - 0.45), (0.025, 0.02, 0.4), 0.006), k=0.003, label=11)
    for sx in (-1, 1):
        br.add(RoundCone((sx * (W - 0.1), -D - 0.1, H - 0.05), (sx * (W - 0.1), -D + 0.05, H + 0.25), 0.012, 0.012), k=0.003, label=6)
    hide = Field("Hides")
    for sx in (-1, 1):                                          # hides over its sides and back
        hide.add(RoundBox((sx * (W + 0.07), 0, H * 0.55), (0.02, D - 0.03, H * 0.42), 0.02, **wob(5.0, 0.012, seed + sx)), k=0.0)
    hide.add(RoundBox((0, D + 0.07, H * 0.55), (W - 0.03, 0.02, H * 0.42), 0.02, **wob(5.0, 0.012, seed + 5)), k=0.0)
    hide.add(RoundBox((0, -D - 0.07, 0.9), (W - 0.03, 0.02, 0.6), 0.02, **wob(5.0, 0.012, seed + 6)), k=0.0)
    hide.paint(Func(lambda P: (F32(0.25) - np.abs(np.mod(P[:, 2], F32(0.35)) - F32(0.175)) * F32(8)).astype(F32), (-2, -2, 0), (2, 2, 4)), 5)
    whl = Field("Wheels")
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = v3((sx * (W - 0.2), sy * (D + 0.12), 0.2))
            R = rot_from_axes(z_axis=(0, 1, 0))
            whl.add(Cylinder(c, 0.2, 0.07, rr=0.015, R=R), k=0.0, label=10)
            whl.add(Torus(c, 0.2, 0.012, R=R), k=0.003, label=6)
    for part in (wd, whl):
        ground_cut(part)
    return [("Frame", wd, fine(0.006, 0.012), "timber"), ("Bridge", br, fine(0.006, 0.012), "timber"), ("Hides", hide, fine(0.009, 0.018), "hide"),
            ("Wheels", whl, fine(0.005, 0.01), "timber")]


def supplies(seed=0):
    """The camp's supplies: barrels (hooped), crates and a sack or two, heaped together."""
    rng = np.random.default_rng(seed)
    wd = Field("Barrels")
    for (x, y, z) in ((0.0, 0.0, 0.0), (0.36, 0.06, 0.0), (0.18, 0.02, 0.42)):
        def barrel(P, x=x, y=y, z=z):
            q = np.sqrt((P[:, 0] - F32(x)) ** 2 + (P[:, 1] - F32(y)) ** 2)
            t = (P[:, 2] - F32(z + 0.2)) / F32(0.2)
            prof = F32(0.15) + F32(0.03) * (F32(1) - t * t)
            return (np.maximum(q - prof, np.abs(P[:, 2] - F32(z + 0.2)) - F32(0.2)) * F32(0.9)).astype(F32)
        wd.add(Func(barrel, (x - 0.25, y - 0.25, z - 0.05), (x + 0.25, y + 0.25, z + 0.45)), k=0.0, label=10)
        for zz in (0.06, 0.34):
            wd.add(Torus((x, y, z + zz), 0.165, 0.012), k=0.002, label=6)
    cr = Field("Crates")
    for (x, y, z, r) in ((-0.42, -0.1, 0.17, 0.3), (-0.4, 0.3, 0.13, -0.2), (-0.38, 0.08, 0.47, 0.1)):
        cr.add(RoundBox((x, y, z), (0.17, 0.17, 0.15), 0.01, R=Rz(r)), k=0.0, label=10)
        for k in range(3):
            cr.add(RoundBox(v3((x, y, z)) + Rz(r) @ v3((0, -0.172, -0.1 + 0.1 * k)), (0.17, 0.01, 0.012), 0.004, R=Rz(r)), k=0.002, label=11)
    sk = Field("Sacks")
    for (x, y) in ((0.2, -0.36), (0.42, -0.3)):
        sk.add(Ellipsoid((x, y, 0.15), (0.14, 0.12, 0.17), **wob(8.0, 0.012, seed + int(x * 10))), k=0.0)
        sk.add(RoundCone((x, y, 0.28), (x, y, 0.36), 0.04, 0.03), k=0.02)
    for part in (wd, cr, sk):
        ground_cut(part)
    return [("Barrels", wd, fine(0.005, 0.01), "timber"), ("Crates", cr, fine(0.005, 0.01), "timber"), ("Sacks", sk, fine(0.006, 0.012), "sacking")]


def stone_pile(seed=0):
    """A pile of round catapult stones, roughly dressed, heaped up."""
    rng = np.random.default_rng(seed)
    f = Field("Stones")
    pts = [(0, 0, 0.15)] + [(math.cos(a) * 0.3, math.sin(a) * 0.3, 0.12) for a in np.linspace(0, 2 * math.pi, 7)[:-1]] + \
          [(math.cos(a) * 0.14, math.sin(a) * 0.14, 0.38) for a in (0.4, 2.5, 4.6)]
    for k, p in enumerate(pts):
        f.add(Sphere(p, rng.uniform(0.13, 0.16), **wob(9.0, 0.012, seed * 10 + k)), k=0.0)
    ground_cut(f)
    return [("Stones", f, fine(0.006, 0.012), "shot")]


def campfire(seed=0):
    """A campfire: a ring of stones round charred logs (the fire is game.gd's flame, MARK_FIRES), a spit over it on two
    forked sticks, a log to sit on."""
    rng = np.random.default_rng(seed)
    st = Field("Stones")
    for k in range(10):
        a = 2 * math.pi * k / 10
        st.add(Ellipsoid((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.04), (0.08, 0.07, 0.06), R=Rz(a), **wob(12.0, 0.008, seed + k)), k=0.0)
    wd = Field("Logs")
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        d = v3((math.cos(a), math.sin(a), 0.0))
        wd.add(RoundCone(d * 0.22 + v3((0, 0, 0.04)), -d * 0.02 + v3((0, 0, 0.1)), 0.035, 0.03), k=0.004, label=5)
    sp = Field("Wood")                                          # the spit on its forked sticks, a log to sit on
    for sx in (-1, 1):
        sp.add(RoundCone((sx * 0.38, 0, -0.03), (sx * 0.36, 0, 0.5), 0.018, 0.016), k=0.0, label=11)
        sp.add(RoundCone((sx * 0.36, 0, 0.42), (sx * 0.42, 0, 0.55), 0.012, 0.01), k=0.004, label=11)
    sp.add(RoundCone((-0.45, 0, 0.47), (0.45, 0, 0.47), 0.012, 0.012), k=0.004, label=10)
    sp.add(RoundCone((-0.3, 0.62, 0.1), (0.35, 0.58, 0.1), 0.1, 0.09), k=0.0, label=10)
    ash = Field("Ash")
    ash.add(Cylinder((0, 0, 0.0), 0.24, 0.03, rr=0.01), k=0.0)
    for part in (st, wd, sp, ash):
        ground_cut(part)
    return [("Stones", st, fine(0.006, 0.012), "rock"), ("Logs", wd, fine(0.005, 0.01), "charred"), ("Wood", sp, fine(0.005, 0.01), "timber"),
            ("Ash", ash, fine(0.008, 0.016), "dark")]


def banner_pole(seed=0, h=2.0):
    """A banner on a tall pole: a long blue banner with a gold border and a gold cross (the besiegers' arms), hanging
    from a crossbar, its foot cut in a swallow-tail; the pole's iron spike."""
    wd = Field("Pole")
    wd.add(RoundCone((0, 0, -0.08), (0, 0, h), 0.025, 0.02), k=0.0, label=11)
    wd.add(RoundCone((0, 0, h), (0, 0, h + 0.14), 0.02, 0.003), k=0.004, label=6)
    wd.add(RoundCone((0, -0.24, h - 0.08), (0, 0.24, h - 0.08), 0.012, 0.012), k=0.004, label=11)
    bn = Field("Banner")
    cb = v3((0.03, 0, h - 0.1))
    def cloth(P):
        q = P - cb.astype(F32)
        s = q[:, 1]
        z = -q[:, 2]
        wave = F32(0.012) * np.sin(s * F32(20) + F32(0.4))
        notch = (z - F32(0.86 - 0.12)) * F32(0.6) - np.abs(s)
        return np.maximum(np.maximum(np.maximum(np.abs(s) - F32(0.21), np.maximum(-z, z - F32(0.86))), np.abs(q[:, 0] - wave) - F32(0.006)), notch).astype(F32)
    bn.add(Func(cloth, cb + v3((-0.1, -0.3, -0.95)), cb + v3((0.1, 0.3, 0.05))), k=0.0)
    bn.paint(Func(lambda P: (np.maximum(np.abs(P[:, 1]) - F32(0.04), np.abs(P[:, 2] - F32(h - 0.45)) - F32(0.22))).astype(F32), cb - 1, cb + 1), 5)
    bn.paint(Func(lambda P: (np.maximum(np.abs(P[:, 1]) - F32(0.15), np.abs(P[:, 2] - F32(h - 0.37)) - F32(0.04))).astype(F32), cb - 1, cb + 1), 5)
    bn.paint(Func(lambda P: (F32(0.18) - np.abs(P[:, 1])).astype(F32), cb - 1, cb + 1), 5)                                  # the border
    ground_cut(wd)
    return [("Pole", wd, fine(0.005, 0.01), "timber"), ("Banner", bn, fine(0.005, 0.01), "banner")]


def spear_rack(seed=0):
    """A rack of spears: two trestles and a rail, five spears leaning in it, their steel heads up, a shield against it."""
    rng = np.random.default_rng(seed)
    wd = Field("Rack")
    for sx in (-1, 1):
        for sy in (-1, 1):
            wd.add(RoundCone((sx * 0.5, sy * 0.18, -0.03), (sx * 0.5, 0, 0.6), 0.02, 0.02), k=0.004, label=11)
    wd.add(RoundCone((-0.55, 0, 0.6), (0.55, 0, 0.6), 0.02, 0.02), k=0.004, label=10)
    sp = Field("Spears")
    for k in range(5):
        x = -0.36 + 0.18 * k
        foot = v3((x + rng.uniform(-0.02, 0.02), 0.22, 0.0))
        d = unit(v3((rng.uniform(-0.05, 0.05), -0.22, 1.0)))
        sp.add(RoundCone(foot, foot + d * 1.45, 0.013, 0.011), k=0.0, label=0)
        sp.add(RoundCone(foot + d * 1.42, foot + d * 1.62, 0.022, 0.002), k=0.004, label=6)
    sh = Field("Shield")
    sh.add(Ellipsoid((0.45, -0.18, 0.32), (0.22, 0.03, 0.3), R=euler(0.25, 0, 0.1)), k=0.0)
    sh.paint(Func(lambda P: (np.abs(P[:, 0] - F32(0.45)) - F32(0.04)).astype(F32), (0, -1, 0), (1, 1, 1)), 5)
    for part in (wd, sp):
        ground_cut(part)
    return [("Rack", wd, fine(0.005, 0.01), "timber"), ("Spears", sp, fine(0.004, 0.008), "spear"), ("Shield", sh, fine(0.005, 0.01), "banner")]


# ------------------------------------------------------------------------------------------------ the Medieval city
def _round_tower(st, rf, cx, cy, r, h, roof_h, seed, slits=()):
    """A round tower of grey stone: courses, a corbelled parapet ring at the top with crenels, a conical slate roof."""
    st.add(Cylinder((cx, cy, (h - 0.05) / 2), r, h + 0.05, rr=0.02, **wob(4.0, 0.005, seed)), k=0.0)
    st.add(Cylinder((cx, cy, h - 0.08), r + 0.08, 0.16, rr=0.02), k=0.01)                              # the corbelled ring
    for k in range(12):                                                                             # its corbels
        a = 2 * math.pi * k / 12
        st.add(RoundBox((cx + math.cos(a) * (r + 0.03), cy + math.sin(a) * (r + 0.03), h - 0.24), (0.05, 0.05, 0.08), 0.01, R=Rz(a)), k=0.004)
    n = 10
    for k in range(n):                                                                              # crenels round the top
        a = 2 * math.pi * (k + 0.5) / n
        st.add(RoundBox((cx + math.cos(a) * (r + 0.04), cy + math.sin(a) * (r + 0.04), h + 0.08), (0.09, 0.07, 0.1), 0.01, R=Rz(a + math.pi / 2)), k=0.004)
    for z in np.arange(0.3, h - 0.3, 0.3):                                                          # courses
        st.sub(Func(lambda P, z=z: np.maximum(np.abs(P[:, 2] - F32(z)) - F32(0.006),
                                              np.abs(np.sqrt((P[:, 0] - F32(cx)) ** 2 + (P[:, 1] - F32(cy)) ** 2) - F32(r)) - F32(0.012)).astype(F32),
                    (cx - r - 0.1, cy - r - 0.1, z - 0.04), (cx + r + 0.1, cy + r + 0.1, z + 0.04)), k=0.002)
    for (a, z) in slits:                                                                            # arrow slits
        st.sub(RoundBox((cx + math.cos(a) * r, cy + math.sin(a) * r, z), (0.06, 0.03, 0.13), 0.006, R=Rz(a)), k=0.003)
    rf.add(cone((cx, cy), h - 0.02, h + roof_h, r + 0.02, 0.0, wob(5.0, 0.006, seed + 7)), k=0.0)
    rf.add(RoundCone((cx, cy, h + roof_h - 0.05), (cx, cy, h + roof_h + 0.2), 0.02, 0.008), k=0.004, label=6)   # the finial


def medieval_city(seed=0):
    """A castle's gatehouse at the end of the road (the gate faces -X, where the road comes in): two round towers of grey
    stone under conical slate roofs, a corbelled crenellated parapet round each; between them the gate under a pointed
    arch, the portcullis raised in its slot, the oak gates standing open, a crenellated walk over it; the drawbridge down
    over the ditch on its chains; the curtain wall running off both ways (with a turret on each side) behind its
    crenellations; blue banners with a gold cross down the towers; iron fire baskets on poles before the gate (game.gd
    lights them); inside, the keep rising high, square, with a turret at each corner, and roofs of houses."""
    out = []
    TX, TY, TR, TH = 0.8, 1.4, 0.66, 2.7
    GH, WH = 2.1, 1.8
    st = Field("Stone")
    rf = Field("Roofs")
    for sy in (-1, 1):
        _round_tower(st, rf, TX, sy * TY, TR, TH, 1.25, seed + sy, slits=[(math.pi, 1.0), (math.pi, 1.9), (sy * math.pi / 2, 1.5)])
    # the gatehouse: a wall with the pointed-arched gateway, a crenellated walk over it, the portcullis slot
    gw = TY - TR + 0.15
    st.add(RoundBox((TX, 0, (GH - 0.05) / 2), (0.42, gw, (GH + 0.05) / 2), 0.01), k=0.004)
    R_ = 0.82
    def gateway(P):
        y, z = P[:, 1], P[:, 2]
        box = np.maximum(np.abs(y) - F32(0.52), np.maximum(-z - F32(0.1), z - F32(0.95)))
        a1 = np.sqrt((y - F32(-(R_ - 0.52))) ** 2 + (z - F32(0.95)) ** 2) - F32(R_)
        a2 = np.sqrt((y - F32(R_ - 0.52)) ** 2 + (z - F32(0.95)) ** 2) - F32(R_)
        arch = np.maximum(np.maximum(a1, a2), F32(0.95) - z)
        return np.maximum(np.minimum(box, arch), np.abs(P[:, 0] - F32(TX)) - F32(0.6)).astype(F32)
    st.sub(Func(gateway, (TX - 0.7, -0.7, -0.2), (TX + 0.7, 0.7, 1.9)), k=0.01)
    st.sub(RoundBox((TX - 0.18, 0, 1.0), (0.04, 0.56, 1.1), 0.0), k=0.0)                             # the portcullis' slot
    crenels(st, TX - 0.35, -gw + 0.05, TX - 0.35, gw - 0.05, GH, 3, w=0.12, t=0.14)
    for sy in (-1, 1):                                                                              # the curtain wall, both ways
        def wall(P, sy=sy):
            x, y, z = P[:, 0], P[:, 1] * F32(sy), P[:, 2]
            fade = np.clip((F32(7.0) - y) / F32(1.6), 0.0, 1.0)
            hgt = F32(WH) * fade
            d = np.maximum(np.abs(x - F32(TX)) - F32(0.3) - F32(0.05) * np.clip(F32(0.6) - z, 0, 1), z - hgt)
            return np.maximum(d, np.maximum(F32(TY + TR - 0.2) - y, y - F32(7.1))).astype(F32)
        lo = (TX - 0.5, (TY + TR - 0.3) if sy > 0 else -7.2, -0.1)
        hi = (TX + 0.5, 7.2 if sy > 0 else -(TY + TR - 0.3), WH + 0.1)
        st.add(Func(wall, lo, hi, **wob(4.0, 0.006, seed + 3 + sy)), k=0.01)
        y = TY + TR + 0.25
        while y < 5.3:
            if abs(y - 4.4) > 0.55:
                st.add(RoundBox((TX - 0.23, sy * y, WH + 0.1), (0.07, 0.13, 0.11), 0.012), k=0.004)
            y += 0.42
        st.add(RoundBox((TX - 0.23, sy * (TY + TR + 1.8), WH + 0.02), (0.07, 1.8, 0.03), 0.01), k=0.004)
        _round_tower(st, rf, TX + 0.05, sy * 4.4, 0.42, WH + 0.5, 0.75, seed + 20 + sy, slits=[(math.pi, 1.2)])
    st.paint(Func(lambda P: (P[:, 2] - F32(0.3)).astype(F32), (-1, -8, -0.2), (3, 8, 4)), 7)
    # the keep inside, square, a turret at each corner, a door up a stair
    KX, KS, KH = 3.7, 0.85, 3.9
    st.add(walls_box(KX, 0, KS, KS, -0.05, KH, batter=0.015, amp=0.004, seed=seed + 30), k=0.0)
    e = KS - 0.015 * KH + 0.03
    crenels(st, KX - e, -e, KX - e, e, KH + 0.02, 4, w=0.12, t=0.14)
    crenels(st, KX - e, e, KX + e, e, KH + 0.02, 4, w=0.12, t=0.14)
    crenels(st, KX - e, -e, KX + e, -e, KH + 0.02, 4, w=0.12, t=0.14)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _round_tower(st, rf, KX + sx * (KS - 0.08), sy * (KS - 0.08), 0.26, KH + 0.45, 0.62, seed + 40 + sx + 2 * sy)
    for z in (1.4, 2.4, 3.2):
        for sy in (-1, 0, 1):
            st.sub(RoundBox((KX - KS + 0.015 * z, sy * 0.4, z), (0.04, 0.05, 0.14), 0.01), k=0.003)
    for z in np.arange(0.3, KH - 0.1, 0.3):
        st.sub(_ring_groove_sq(KX, 0.0, KS, z, batter=0.015), k=0.002)
    ground_cut(st, -0.04)
    out.append(("Stone", st, fine(0.012, 0.024), "ashlar"))
    out.append(("Roofs", rf, fine(0.008, 0.016), "slate"))
    # the gates (open, swung in against the passage walls), the portcullis (raised: its spikes show under the arch)
    gd = Field("Gate")
    for sy in (-1, 1):
        gd.add(RoundBox((TX + 0.12, sy * 0.47, 0.5), (0.27, 0.035, 0.5), 0.008, R=Rz(sy * 0.15)), k=0.0, label=11)
        for z in (0.25, 0.75):
            gd.add(RoundBox((TX + 0.12, sy * 0.43, z), (0.27, 0.01, 0.025), 0.004, R=Rz(sy * 0.15)), k=0.002, label=6)
    gd.add(RoundBox((TX + 0.4, 0, 0.6), (0.02, 0.5, 0.6), 0.0), k=0.0, label=0)                     # the dark beyond (painted dark below)
    ground_cut(gd)
    out.append(("Gate", gd, fine(0.006, 0.012), "timber"))
    pc = Field("Portcullis")
    for k in range(7):
        y = -0.45 + 0.15 * k
        pc.add(RoundBox((TX - 0.18, y, 1.62), (0.02, 0.018, 0.5), 0.004), k=0.0)
        pc.add(RoundCone((TX - 0.18, y, 1.12), (TX - 0.18, y, 1.0), 0.018, 0.003), k=0.004)          # its spikes
    for z in (1.25, 1.55, 1.85):
        pc.add(RoundBox((TX - 0.18, 0, z), (0.02, 0.5, 0.016), 0.004), k=0.002)
    out.append(("Portcullis", pc, fine(0.005, 0.01), "iron"))
    # the drawbridge, down over the ditch, on its chains
    db = Field("Bridge")
    db.add(RoundBox((TX - 1.05, 0, 0.04), (0.62, 0.55, 0.045), 0.01), k=0.0, label=10)
    for k in range(9):
        db.add(RoundBox((TX - 1.6 + k * 0.14, 0, 0.09), (0.006, 0.56, 0.008), 0.002), k=0.002, label=0)
    for sy in (-1, 1):
        db.add(RoundCone((TX - 1.6, sy * 0.5, 0.1), (TX - 0.42, sy * 0.48, 1.65), 0.016, 0.016), k=0.004, label=6)   # chains
    ground_cut(db, -0.1)
    out.append(("Bridge", db, fine(0.006, 0.012), "timber"))
    ditch = Field("Ditch")                                                                          # the ditch under it: dark water
    ditch.add(RoundBox((TX - 1.05, 0, -0.08), (0.5, 4.0, 0.04), 0.02), k=0.0)
    out.append(("Ditch", ditch, fine(0.012, 0.024), "dark_water"))
    # fire baskets on iron poles before the gate
    fb = Field("Baskets")
    for sy in (-1, 1):
        c = v3((-0.15, sy * (TY + 0.1), 0.0))
        fb.add(RoundCone(c + v3((0, 0, -0.05)), c + v3((0, 0, 0.95)), 0.03, 0.025), k=0.0)
        for k in range(3):
            a = 2 * math.pi * k / 3
            fb.add(RoundCone(c + v3((0, 0, 0.3)), c + v3((math.cos(a) * 0.25, math.sin(a) * 0.25, -0.02)), 0.02, 0.018), k=0.01)
        for k in range(8):                                                                          # the basket's iron straps
            a = 2 * math.pi * k / 8
            fb.add(RoundCone(c + v3((0, 0, 0.95)), c + v3((math.cos(a) * 0.2, math.sin(a) * 0.2, 1.15)), 0.012, 0.012), k=0.004)
        fb.add(Torus(c + v3((0, 0, 1.15)), 0.2, 0.014), k=0.004)
        fb.add(Torus(c + v3((0, 0, 1.05)), 0.12, 0.012), k=0.004)
    ground_cut(fb)
    out.append(("Baskets", fb, fine(0.005, 0.01), "iron"))
    cg = Field("Coals")
    for sy in (-1, 1):
        cg.add(Ellipsoid((-0.15, sy * (TY + 0.1), 1.08), (0.15, 0.15, 0.08), **wob(25.0, 0.008, seed + 5 + sy)))
    out.append(("Coals", cg, fine(0.005, 0.01), "glow_fire"))
    # blue banners with a gold cross down the towers' fronts
    bn = Field("Banners")
    B0, B1 = 0.9, 2.15
    for sy in (-1, 1):
        def banner_fn(P, cy=sy * TY):
            x, y, z = P[:, 0], P[:, 1] - F32(cy), P[:, 2]
            face = F32(TX - TR - 0.04)
            wave = F32(0.015) * np.sin(z * F32(8.0) + y * F32(3.0))
            half = np.where(z < F32(B0 + 0.22), F32(0.22) - (F32(B0 + 0.22) - z) * F32(1.0), F32(0.22))
            return np.maximum.reduce([np.abs(x - (face + wave)) - F32(0.014), np.abs(y) - half, z - F32(B1), F32(B0) - z]).astype(F32)
        bn.add(Func(banner_fn, (TX - TR - 0.25, sy * TY - 0.3, B0 - 0.05), (TX - TR + 0.15, sy * TY + 0.3, B1 + 0.05)))
        bn.add(RoundCone((TX - TR - 0.06, sy * TY - 0.3, B1 + 0.02), (TX - TR - 0.06, sy * TY + 0.3, B1 + 0.02), 0.022, 0.022), k=0.004, label=6)
        bn.paint(Func(lambda P, cy=sy * TY: np.minimum(np.maximum(np.abs(P[:, 1] - F32(cy)) - F32(0.045), np.abs(P[:, 2] - F32(1.62)) - F32(0.3)),
                                                       np.maximum(np.abs(P[:, 1] - F32(cy)) - F32(0.17), np.abs(P[:, 2] - F32(1.72)) - F32(0.045))).astype(F32),
                      (TX - TR - 0.3, sy * TY - 0.3, 1.0), (TX - TR + 0.2, sy * TY + 0.3, 2.2)), 5)
    out.append(("Banners", bn, fine(0.005, 0.01), "banner"))
    dk = Field("Dark")                                                                              # the passage's shadow, the slits
    dk.add(RoundBox((TX + 0.55, 0, 0.6), (0.05, 0.5, 0.65), 0.0))
    for sy in (-1, 1):
        for z in (1.0, 1.9):
            dk.add(RoundBox((TX - TR + 0.05, sy * TY, z), (0.03, 0.02, 0.12), 0.006))
    out.append(("Dark", dk, fine(0.006, 0.012), "dark"))
    # roofs of houses inside, between the gate and the keep
    for i, (c, yaw) in enumerate((((2.5, -2.6), 0.15), ((2.6, 2.7), -0.2), ((2.2, 4.9), 0.05), ((2.3, -4.8), -0.1))):
        hs = cottage(seed + 60 + i)
        place_parts(out, [("House%d%s" % (i, n), f, vxs, m) for (n, f, vxs, m) in hs], (c[0], c[1], 0.0), Rz(yaw - math.pi / 2))
    return out


def _ring_groove_sq(cx, cy, half, z, depth=0.012, w=0.006, batter=0.0):
    """A course joint cut round a square block of half extent `half` at height z."""
    hz = half - batter * z
    def fn(P):
        m = np.maximum(np.abs(P[:, 0] - F32(cx)), np.abs(P[:, 1] - F32(cy)))
        return np.maximum.reduce([np.abs(P[:, 2] - F32(z)) - F32(w), F32(hz - depth) - m, m - F32(hz + 0.02)]).astype(F32)
    return Func(fn, (cx - half - 0.1, cy - half - 0.1, z - 0.04), (cx + half + 0.1, cy + half + 0.1, z + 0.04))


# ------------------------------------------------------------------------------------------------ the kits
# prop name -> (builder, game-mesh triangle budget), as decor_props.KITS. Tuft and Flowers are direct geometry
# (decor_build).
def KITS(theme):
    common = {
        "Rock_A": (lambda: rock(1.7, 0.5, 301), 650), "Rock_B": (lambda: rock(1.0, 0.36, 302, n_extra=1), 420),
        "Rock_C": (lambda: rock(2.3, 0.66, 303, n_extra=3), 850),
        "Stump": (lambda: stump(304), 450), "Log": (lambda: log(305), 450),
    }
    if theme == "farmland":
        return dict(common, **{
            "Oak_A": (lambda: oak(2.7, 311), 2400), "Oak_B": (lambda: oak(2.2, 312), 2100), "Oak_C": (lambda: oak(1.5, 313, young=True), 1400),
            "Hedge": (lambda: hedge(2.4, 0.72, 314), 1800), "Hedge_B": (lambda: hedge(1.6, 0.62, 315), 1300),
            "Bush": (lambda: bush(0.8, 0.55, 316, "hedge", "blossom"), 800),
            "Haystack": (lambda: haystack(317), 900), "Fence": (lambda: fence(2.0, 0.5, 318), 900),
            "Cottage": (lambda: cottage(319), 4600), "Barn": (lambda: barn(320), 4400), "Windmill": (lambda: windmill(321), 5200),
            "Well": (lambda: well(322), 1800), "Scarecrow": (lambda: scarecrow(323), 1400), "Cart": (lambda: hay_cart(324), 2200),
        })
    if theme == "darkwood":
        return dict(common, **{
            "Spruce_A": (lambda: spruce(3.8, 331), 1700), "Spruce_B": (lambda: spruce(3.0, 332), 1500), "Spruce_C": (lambda: spruce(2.2, 333), 1200),
            "Oak_A": (lambda: oak(2.6, 334, gnarled=True), 2400), "Dead_A": (lambda: dead_tree(2.4, 335), 900), "Dead_B": (lambda: dead_tree(1.7, 336), 800),
            "Fern_A": (lambda: fern(337), 900), "Fern_B": (lambda: fern(338, 0.75), 800),
            "Toadstools": (lambda: toadstools(339), 900), "Toadstools_B": (lambda: toadstools(340, 0.7), 700),
            "Hut": (lambda: hut(341), 4200), "Chapel": (lambda: chapel(342), 5600), "Cross": (lambda: wayside_cross(343), 900),
        })
    if theme == "castle":
        return dict(common, **{
            "Oak_A": (lambda: oak(2.4, 351), 2200), "Oak_B": (lambda: oak(1.6, 352, young=True), 1400),
            "Bush": (lambda: bush(0.8, 0.5, 353, "hedge"), 700),
            "Tent_A": (lambda: pavilion(354), 2400), "Tent_B": (lambda: ridge_tent(355), 1400),
            "Mantlet": (lambda: mantlet(356), 1400), "Ram": (lambda: ram(357), 3200), "Tower": (lambda: siege_tower(358), 4200),
            "Supplies": (lambda: supplies(359), 1800), "Shot": (lambda: stone_pile(360), 900), "Campfire": (lambda: campfire(361), 1200),
            "Banner": (lambda: banner_pole(362), 900), "Rack": (lambda: spear_rack(363), 1300),
        })
    if theme == "medieval_city":
        return {"City": (lambda: medieval_city(371), 18000)}
    raise KeyError(theme)
