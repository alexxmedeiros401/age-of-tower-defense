"""HQ Classical Age map props, sculpted as distance fields like decor_props, decor_bronze and decor_iron (same conventions:
every builder returns its parts [(part name, Field, voxel, material key)], built at the origin, Z up, ground at z = 0;
KITS lists each theme's props and their game-mesh triangle budgets; decor_build.materials resolves the material keys).

Olive Hills: olive trees (gnarled, twisted, split trunks under silvery crowns), Italian cypresses, herb cushions (thyme,
sage), limestone rocks, a dry-stone terrace wall, marble ruins (fluted Doric column drums, standing and broken, fallen
blocks), a heap of amphorae; a small ruined Doric temple, a farmhouse (whitewashed walls under a terracotta roof, a vine
over its pergola) and an olive press (a stone basin, an upright millstone, a beam).
Marble Coast: umbrella pines, cypresses, maquis bushes, white limestone rocks, the same ruins; an aqueduct (tall arches
of cut stone carrying the water channel: placed across the road where it runs under), a stone arch bridge, a lighthouse
(a square tower stepping in, a fire burning at the top) and a beached boat.
Acropolis: olives and cypresses, limestone, the ruins; marble statues on plinths (a draped figure with a raised arm, a
seated lion), a temple of the hill (a Doric temple on a stepped base, columns all round under a pediment, a few gone),
a theatre (rows of stone seats cut into a slope round a round floor) and an altar.
The Classical city at the end of every Classical Age road (a walled city's gate: two square towers of cut stone and an
arched gateway, the wall running off both ways with its walkway, red banners, braziers; inside, houses under terracotta
roofs and a temple's pediment rising behind) is its own kit ("classical_city", classical_city.glb).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Chain, Plane, Func, rot_from_axes, v3, NOISE, euler
import decor_props as DP
from decor_props import vx, wob, convex, rock, dead_tree, stump, log
from decor_bronze import fine, unit, frame, ground_cut, cut_above, cut_below, place, place_parts, mound, convex_w, walls_box
from decor_iron import Rz, R_xz, at_height, cone, gable

F32 = np.float32


# ------------------------------------------------------------------------------------------------ trees
def olive(h=1.9, seed=0, young=False):
    """An olive tree: a short, thick, gnarled trunk twisting as it rises, split into two or three stems (a hollow
    between them), knobbly burrs at its foot; low spreading branches under a broad, ragged crown of small silvery-green
    clumps, lumpy and open."""
    rng = np.random.default_rng(seed)
    s = h / 1.9
    f = Field("Trunk")
    c = Field("Leaves")
    n_st = 1 if young else rng.integers(2, 4)
    a0 = rng.uniform(0, 2 * math.pi)
    base_r = (0.1 if young else 0.2) * s
    # the bole: a twisted lumpy mass at the foot
    if not young:
        for k in range(5):
            a = a0 + 2 * math.pi * k / 5 + rng.uniform(-0.3, 0.3)
            c0 = v3((math.cos(a) * base_r * 0.6, math.sin(a) * base_r * 0.6, 0.12 * s))
            f.add(Ellipsoid(c0, (base_r * 0.6, base_r * 0.55, 0.22 * s), R=Rz(a), **wob(6.0 / s, 0.025 * s, seed + k)), k=0.06 * s)
        for k in range(4):                                     # roots spreading over the ground
            a = a0 + 2 * math.pi * k / 4 + rng.uniform(-0.4, 0.4)
            f.add(RoundCone((0, 0, 0.08 * s), (math.cos(a) * 0.42 * s, math.sin(a) * 0.42 * s, -0.04), 0.08 * s, 0.025 * s), k=0.06 * s)
    tops = []
    for i in range(n_st):
        a = a0 + 2 * math.pi * i / n_st + rng.uniform(-0.4, 0.4)
        out = v3((math.cos(a), math.sin(a), 0.0))
        side = v3((-math.sin(a), math.cos(a), 0.0))
        lean = rng.uniform(0.22, 0.4) * (0.6 if young else 1.0)
        hh = h * rng.uniform(0.42, 0.55)
        pts, rads = [], []
        for k in range(6):                                     # a stem twisting as it rises
            t = k / 5
            tw = math.sin(t * 2.6 + i) * 0.06 * s
            pts.append(out * (base_r * 0.4 + lean * hh * t) + side * tw + v3((0, 0, hh * t - (0.05 if k == 0 else 0.0))))
            rads.append(((0.1 if young else 0.13) * (1.0 - 0.45 * t) + 0.02) * s)
        f.add(Chain(pts, rads, k=0.03 * s, **wob(4.5 / s, 0.022 * s, seed * 10 + i)), k=0.07 * s)
        for k in range(3):                                     # burrs and knots along it
            t = rng.uniform(0.15, 0.7)
            p = at_height(pts, hh * t)
            d = unit(out * rng.uniform(-0.6, 1.0) + side * rng.uniform(-1, 1))
            f.add(Ellipsoid(p + d * rads[2] * 0.8, (0.05 * s, 0.045 * s, 0.06 * s), **wob(10.0 / s, 0.012 * s, seed + 40 + i * 3 + k)), k=0.03 * s)
        top = pts[-1]
        for j in range(4):                                     # branches spreading out low and wide
            b = a + rng.uniform(-1.4, 1.4)
            ob = v3((math.cos(b), math.sin(b), 0.0))
            L = h * rng.uniform(0.32, 0.48)
            p0 = at_height(pts, hh * rng.uniform(0.55, 0.95))
            p1 = p0 + ob * L * 0.5 + v3((0, 0, L * 0.3))
            p2 = p1 + ob * L * 0.5 + v3((0, 0, L * 0.12))
            f.add(Chain([p0, p1, p2], [0.045 * s, 0.03 * s, 0.014 * s], k=0.01, **wob(6.0 / s, 0.008 * s, seed * 20 + i * 4 + j)), k=0.03 * s)
            tops.append(p2)
            tops.append(p1 + v3((0, 0, 0.08 * s)))
        tops.append(top + v3((0, 0, 0.12 * s)))
    # the crown: many small open clumps round the branch ends, a ragged dome
    ctr = sum(tops, v3((0, 0, 0))) / len(tops)
    for j, q in enumerate(tops):
        for k in range(3):
            o = v3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.6))) * 0.16 * s
            r = s * rng.uniform(0.15, 0.22)
            c.add(Ellipsoid(q + o, (r, r * 0.9, r * 0.7), **wob(14.0 / s, 0.04 * s, seed * 100 + j * 3 + k)), k=0.06 * s)
    for j in range(8):
        u = rng.normal(size=3)
        u = u / np.linalg.norm(u)
        q = ctr + v3((u[0] * 0.55 * s, u[1] * 0.55 * s, abs(u[2]) * 0.3 * s + 0.1 * s))
        r = s * rng.uniform(0.17, 0.24)
        c.add(Ellipsoid(q, (r, r * 0.92, r * 0.72), **wob(14.0 / s, 0.04 * s, seed * 200 + j)), k=0.06 * s)
    return [("Trunk", f, fine(0.007, 0.014), "olive_bark"), ("Leaves", c, fine(0.011, 0.022), "olive_leaves")]


def cypress(h=3.4, seed=0, w=0.38):
    """An Italian cypress: a tall narrow flame of dense dark green, its foliage in soft vertical lobes, a slender trunk
    showing at its foot."""
    rng = np.random.default_rng(seed)
    s = h / 3.4
    f = Field("Trunk")
    f.add(RoundCone((0, 0, -0.08), (0, 0, 0.6 * s), 0.085 * s, 0.05 * s, **wob(5.0, 0.008, seed)))
    c = Field("Leaves")
    lean = v3((rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), 0.0)) * h

    def flame(P):
        z = P[:, 2]
        t = np.clip((z - F32(0.22 * h)) / F32(0.78 * h), 0, 1)
        prof = F32(w * s) * (F32(0.75) + F32(1.2) * t - F32(1.75) * t * t) * np.clip((z - F32(0.18 * h)) / F32(0.08 * h), 0.3, 1)
        cx = F32(lean[0]) * t
        cy = F32(lean[1]) * t
        rr = np.sqrt((P[:, 0] - cx) ** 2 + (P[:, 1] - cy) ** 2)
        a = np.arctan2(P[:, 1] - cy, P[:, 0] - cx)
        lobes = F32(0.03 * s) * np.sin(a * F32(7) + z * F32(3.0))
        return (np.maximum(rr - np.maximum(prof, F32(0.01)) + lobes, np.maximum(F32(0.2 * h) - z, z - F32(h))) * F32(0.8)).astype(F32)
    c.add(Func(flame, (-w * s * 1.8, -w * s * 1.8, 0.15 * h), (w * s * 1.8, w * s * 1.8, h + 0.05),
               **wob(5.0 / s, 0.035 * s, seed)))
    for j in range(10):                                    # soft clumps breaking its outline
        z = rng.uniform(0.3, 0.85) * h
        t = (z - 0.22 * h) / (0.78 * h)
        r_out = w * s * (0.75 + 1.2 * t - 1.75 * t * t)
        a = rng.uniform(0, 2 * math.pi)
        q = v3((math.cos(a) * r_out * 0.8, math.sin(a) * r_out * 0.8, z)) + lean * t
        r = s * rng.uniform(0.08, 0.13)
        c.add(Ellipsoid(q, (r, r, r * 1.6), **wob(14.0 / s, 0.025 * s, seed * 30 + j)), k=0.05 * s)
    return [("Trunk", f, fine(0.006, 0.012), "olive_bark"), ("Leaves", c, fine(0.01, 0.02), "cypress")]


def stone_pine(h=3.6, seed=0, twin=False):
    """An umbrella pine: a tall bare trunk (two when twin), curving and leaning, its bark in orange-grey plates,
    branching only at the top into a broad, flat-topped umbrella of dark green needle pads."""
    rng = np.random.default_rng(seed)
    s = h / 3.6
    f = Field("Trunk")
    c = Field("Crown")
    stems = [rng.uniform(0, 2 * math.pi)]
    if twin:
        stems.append(stems[0] + math.pi * 0.8)
    for si, a in enumerate(stems):
        d = v3((math.cos(a), math.sin(a), 0.0))
        lean = (0.16 if not twin else 0.28) * h
        hh = h * (1.0 if si == 0 else 0.85)
        pts = [v3((0, 0, -0.1)) + d * (0.0 if not twin else 0.04), v3((0, 0, hh * 0.3)) + d * lean * 0.18,
               v3((0, 0, hh * 0.6)) + d * lean * 0.55, v3((0, 0, hh * 0.82)) + d * lean]
        f.add(Chain(pts, [0.12 * s, 0.1 * s, 0.08 * s, 0.05 * s], k=0.02, **wob(3.0, 0.01 * s, seed + si)), k=0.04 * s)
        top = pts[-1]
        crown_c = top + v3((0, 0, 0.16 * s))
        for j in range(6):                                    # the branches fanning out under the umbrella
            b = a + 2 * math.pi * j / 6 + rng.uniform(-0.3, 0.3)
            ob = v3((math.cos(b), math.sin(b), 0.0))
            L = h * rng.uniform(0.22, 0.32)
            p1 = top + ob * L * 0.5 + v3((0, 0, L * 0.25))
            p2 = top + ob * L + v3((0, 0, L * 0.3))
            f.add(Chain([top, p1, p2], [0.05 * s, 0.035 * s, 0.018 * s], k=0.01), k=0.03 * s)
            for q in (p1, p2):                                # clumps of needles at the branch ends
                r = s * rng.uniform(0.24, 0.33)
                c.add(Ellipsoid(q + v3((0, 0, 0.1 * s)), (r, r * 0.95, r * 0.55), **wob(9.0 / s, 0.05 * s, seed * 50 + si * 10 + j)), k=0.05 * s)
        for j in range(9):                                    # the umbrella's broad, gently domed top, lumpy
            u = rng.uniform(-1, 1, 2)
            rr = math.hypot(u[0], u[1])
            q = crown_c + v3((u[0] * 0.55 * s, u[1] * 0.55 * s, (0.2 - 0.08 * rr) * s))
            r = s * rng.uniform(0.28, 0.38)
            c.add(Ellipsoid(q, (r, r * 0.95, r * 0.5), **wob(9.0 / s, 0.05 * s, seed * 70 + si * 10 + j)), k=0.06 * s)
    return [("Trunk", f, fine(0.008, 0.016), "pine_bark"), ("Crown", c, vx(h), "pine_crown")]


def bush(w=0.9, h=0.5, seed=0, mat="maquis", flowers=None):
    """A rounded evergreen bush (myrtle, lentisk, oleander): lumpy leafy clumps on a low mound, flowers dotted over it."""
    rng = np.random.default_rng(seed)
    c = Field("Leaves")
    for j in range(15):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.05, 0.36) * w
        q = v3((math.cos(a) * rr, math.sin(a) * rr, h * rng.uniform(0.3, 0.66) * (1.0 - 0.5 * (rr / (0.4 * w)) ** 2)))
        r = w * rng.uniform(0.15, 0.24)
        c.add(Ellipsoid(q, (r, r * 0.95, r * 0.82 * h / (w * 0.55)), **wob(14.0 / w, 0.022 * w, seed * 31 + j)), k=0.035 * w)
    c.add(Ellipsoid((0, 0, h * 0.2), (w * 0.38, w * 0.35, h * 0.42)), k=0.05 * w)
    c.inter(Plane((0, 0, -0.03), (0, 0, -1)))
    out = [("Leaves", c, fine(0.009, 0.018), mat)]
    if flowers:
        fl = Field("Flowers")
        for j in range(26):
            u = rng.normal(size=3)
            u[2] = abs(u[2]) + 0.4
            u = u / np.linalg.norm(u)
            q = v3((u[0] * w * 0.47, u[1] * w * 0.45, h * 0.28 + u[2] * h * 0.62))
            fl.add(Sphere(q, 0.022 * w), k=0.0)
        out.append(("Flowers", fl, fine(0.005, 0.01), flowers))
    return out


def herb(w=0.55, h=0.22, seed=0):
    """A herb cushion (thyme, sage): a low dome of tiny tufts, grey-green, small purple flower heads poking out."""
    rng = np.random.default_rng(seed)
    c = Field("Herb")
    for j in range(16):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, 0.38) * w
        q = v3((math.cos(a) * rr, math.sin(a) * rr, h * (0.6 - 0.5 * (rr / (0.4 * w)) ** 2)))
        r = w * rng.uniform(0.11, 0.17)
        c.add(Ellipsoid(q, (r, r, r * 0.8), **wob(30.0 / w, 0.012 * w, seed * 17 + j)), k=0.025 * w)
    c.inter(Plane((0, 0, -0.03), (0, 0, -1)))
    fl = Field("Flowers")
    for j in range(22):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, 0.37) * w
        q = v3((math.cos(a) * rr, math.sin(a) * rr, h * (0.72 - 0.5 * (rr / (0.4 * w)) ** 2) + 0.025))
        fl.add(Ellipsoid(q, (0.013, 0.013, 0.022)), k=0.0)
    return [("Herb", c, fine(0.006, 0.012), "herb"), ("Flowers", fl, fine(0.005, 0.01), "flower_purple")]


def limestone(w=1.6, h=0.5, seed=0, n_extra=2):
    """A pale limestone outcrop: blocky beds stacked in ledges, each a little narrower than the one under it, their faces
    leaning in, uneven; a crack or two; loose blocks at its foot."""
    rng = np.random.default_rng(seed)
    f = Field("Rock")

    def block(cx, cy, z0, th, hx, hy, k_seed, k=0.01 * w):
        planes = [((cx, cy, z0 + th), (rng.normal() * 0.08, rng.normal() * 0.08, 1.0)), ((cx, cy, z0 - 0.01), (0, 0, -1))]
        a0 = rng.uniform(0, 2 * math.pi)
        n_side = 7
        for kk in range(n_side):
            a = a0 + 2 * math.pi * kk / n_side + rng.uniform(-0.25, 0.25)
            r = rng.uniform(0.85, 1.0)
            ex = (cx + math.cos(a) * hx * r, cy + math.sin(a) * hy * r, z0)
            nrm = (math.cos(a) * hy, math.sin(a) * hx, rng.uniform(0.08, 0.3) * max(hx, hy))
            planes.append((ex, nrm))
        lo = (cx - hx - 0.1, cy - hy - 0.1, z0 - 0.1)
        hi = (cx + hx + 0.1, cy + hy + 0.1, z0 + th + 0.1)
        f.add(convex_w(planes, lo, hi, amp=0.022 * w, scale=3.5 / w, seed=k_seed), k=k)
    layers = 3 if n_extra > 1 else 2
    z = -0.08
    for L in range(layers):
        th = h * (0.6 if L == 0 else 0.34) * rng.uniform(0.85, 1.15)
        sc = 1.0 - 0.24 * L
        block(rng.uniform(-0.08, 0.08) * w, rng.uniform(-0.08, 0.08) * w, z, th + 0.02, w * 0.46 * sc, w * 0.4 * sc, seed * 10 + L)
        z += th
    for i in range(n_extra):                                   # loose blocks at its foot
        a = rng.uniform(0, 2 * math.pi)
        rr = w * rng.uniform(0.45, 0.55)
        sz = w * rng.uniform(0.1, 0.16)
        block(rr * math.cos(a), rr * math.sin(a), -0.06, sz * 1.2, sz, sz * 0.85, seed * 10 + 5 + i, k=0.0)
    for i in range(2):                                         # cracks running in from its edge, down its faces
        a = rng.uniform(0, 2 * math.pi)
        f.sub(RoundBox((math.cos(a) * w * 0.4, math.sin(a) * w * 0.36, h * 0.55), (w * 0.16, 0.011, h * 0.42), 0.004, R=Rz(a),
                       **wob(6.0 / w, 0.02 * w, seed * 3 + i)), k=0.006)
    f.inter(Plane((0, 0, -0.08), (0, 0, -1)))
    return [("Rock", f, vx(w) * 0.8, "limestone")]


# ------------------------------------------------------------------------------------------------ marble ruins
def _flutes(n, depth):
    def fn(P):
        th = np.arctan2(P[:, 1], P[:, 0])
        return (depth * (0.5 - 0.5 * np.cos(n * th))).astype(F32)
    return fn


def doric_shaft(f, c, z0, z1, r0, r1, n=20, depth=0.016):
    """A fluted Doric shaft from z0 to z1 at c (radius r0 at its foot, r1 at its top)."""
    cx, cy = float(c[0]), float(c[1])
    fl = _flutes(n, depth)

    def shaft(P):
        Q = P - np.array([cx, cy, 0.0], F32)
        rr = np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2)
        t = np.clip((P[:, 2] - F32(z0)) / F32(max(z1 - z0, 1e-3)), 0, 1)
        R = F32(r0) + (F32(r1) - F32(r0)) * t
        return (np.maximum(rr - R + fl(Q), np.maximum(F32(z0) - P[:, 2], P[:, 2] - F32(z1))) * F32(0.92)).astype(F32)
    return Func(shaft, (cx - r0 - 0.04, cy - r0 - 0.04, z0 - 0.02), (cx + r0 + 0.04, cy + r0 + 0.04, z1 + 0.02))


def doric_capital(f, c, z, r, k=0.01):
    """The echinus (a cushion flaring out) under the square abacus, on top of a shaft of radius r at height z."""
    cx, cy = float(c[0]), float(c[1])

    def echinus(P):
        Q = P - np.array([cx, cy, 0.0], F32)
        rr = np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2)
        t = np.clip((P[:, 2] - F32(z)) / F32(0.12 * r / 0.26), 0, 1)
        R = F32(r) * (F32(0.98) + F32(0.42) * np.sqrt(t))
        return (np.maximum(rr - R, np.maximum(F32(z) - P[:, 2], P[:, 2] - F32(z + 0.12 * r / 0.26))) * F32(0.85)).astype(F32)
    f.add(Func(echinus, (cx - r * 1.5, cy - r * 1.5, z - 0.02), (cx + r * 1.5, cy + r * 1.5, z + 0.15 * r / 0.26)), k=k)
    f.add(RoundBox((cx, cy, z + 0.12 * r / 0.26 + 0.045 * r / 0.26), (r * 1.42, r * 1.42, 0.045 * r / 0.26), 0.01), k=k * 0.5)
    for j in range(3):                                         # the rings under the echinus
        f.add(Torus((cx, cy, z - 0.02 - 0.025 * j), r * 0.99, 0.008), k=0.004)
    return z + 0.12 * r / 0.26 + 0.09 * r / 0.26


def column(h=1.6, r=0.24, seed=0, broken=True, capital=False, drums=4):
    """A marble Doric column on a square plinth stone: a fluted shaft in drums (their joints showing), tapering a
    little; a capital (echinus and abacus) on standing ones, a jagged break on broken ones; chips off its edges."""
    rng = np.random.default_rng(seed)
    f = Field("Column")
    f.add(RoundBox((0, 0, 0.06), (r * 1.55, r * 1.55, 0.09), 0.015, **wob(6.0, 0.005, seed)))
    f.add(doric_shaft(f, (0, 0), 0.12, h, r, r * 0.85), k=0.01)
    for k in range(1, drums):                                  # the joints between the drums
        z = 0.12 + (h - 0.12) * k / drums
        rk = r - (r * 0.15) * (z - 0.12) / max(h - 0.12, 0.1)
        f.sub(Torus((0, 0, z), rk + 0.004, 0.009), k=0.003)
    if capital and not broken:
        doric_capital(f, (0, 0), h, r * 0.85)
    if broken:
        nrm = unit((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), 1.0))
        cut_above(f, (0, 0, h * 0.94), nrm, (r * 2.0, r * 2.0, 0.6), disp=lambda P: NOISE.fbm(P * 9.0 + seed, 3) * 0.05, amp=0.06)
    for _ in range(5):                                         # chips
        a = rng.uniform(0, 2 * math.pi)
        z = rng.uniform(0.2, h * 0.9)
        f.sub(Sphere((math.cos(a) * r, math.sin(a) * r, z), rng.uniform(0.03, 0.06)), k=0.01)
    f.paint(Func(lambda P: (P[:, 2] - F32(0.35)).astype(F32), (-1, -1, -0.1), (1, 1, h + 0.5)), 7)     # weathered low down
    cut_below(f, -0.03, 0, 0, r * 2.0, r * 2.0)
    return [("Column", f, fine(0.0075, 0.015), "marble")]


def fallen_column(seed=0, L=1.4, r=0.22):
    """A column lying in the grass in three drums rolled apart, its capital beside them."""
    rng = np.random.default_rng(seed)
    f = Field("Fallen")
    a = rng.uniform(0, math.pi)
    d = v3((math.cos(a), math.sin(a), 0.0))
    side = v3((-math.sin(a), math.cos(a), 0.0))
    for k in range(3):
        c = d * (k * L / 3.0 - L * 0.4) + side * rng.uniform(-0.08, 0.08) * k + v3((0, 0, r * 0.88))
        ax = unit(d + side * rng.uniform(-0.25, 0.25))
        Rr = rot_from_axes(z_axis=ax)
        fl = _flutes(20, 0.016)

        def drum(P, c=c, Rr=Rr):
            Q = (P - c.astype(F32)) @ Rr.astype(F32)
            rr = np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2)
            return (np.maximum(rr - F32(r) + fl(Q), np.abs(Q[:, 2]) - F32(L / 6.6)) * F32(0.92)).astype(F32)
        f.add(Func(drum, c - 0.5, c + 0.5, **wob(6.0, 0.004, seed + k)), k=0.0)
    cc = d * (L * 0.62) + side * 0.25 + v3((0, 0, 0.1))
    f.add(RoundBox(cc + v3((0, 0, 0.04)), (r * 1.4, r * 1.4, 0.05), 0.01, R=Rz(a + 0.4)), k=0.0)
    f.add(Ellipsoid(cc + v3((0, 0, 0.13)), (r * 1.2, r * 1.2, 0.08)), k=0.02)
    f.sub(Sphere(cc + v3((r * 1.2, 0.0, 0.14)), 0.08), k=0.01)
    ground_cut(f)
    return [("Fallen", f, fine(0.0075, 0.015), "marble")]


def marble_blocks(seed=0):
    """Fallen marble blocks: a cornice block carved with a band of triglyphs, a plain block and a column drum."""
    rng = np.random.default_rng(seed)
    f = Field("Blocks")
    R1 = rot_from_axes(x_axis=(math.cos(0.3), math.sin(0.3), 0.06), z_axis=(0.05, -0.06, 1))
    f.add(RoundBox((0, 0, 0.2), (0.52, 0.28, 0.24), 0.02, R=R1, **wob(4.0, 0.006, seed)))
    face = R1 @ v3((0, -1, 0))
    ax = R1 @ v3((1, 0, 0))
    for k in range(4):                                       # triglyphs: three bars between metope panels
        c = v3((0, 0, 0.22)) + face * 0.28 + ax * (-0.36 + 0.24 * k)
        for b in (-1, 0, 1):
            f.add(RoundBox(c + ax * b * 0.026, (0.01, 0.008, 0.12), 0.004, R=R1), k=0.003)
    R2 = rot_from_axes(x_axis=(math.cos(1.4), math.sin(1.4), 0.2), z_axis=(0.15, -0.25, 1))
    f.add(RoundBox((0.55, 0.52, 0.14), (0.34, 0.24, 0.18), 0.02, R=R2, **wob(4.0, 0.006, seed + 1)))
    f.add(doric_shaft(f, (-0.6, 0.42), 0.0, 0.34, 0.24, 0.235), k=0.01)
    for _ in range(6):                                        # chips off the edges
        c = R1 @ v3((rng.choice([-0.52, 0.52]), rng.choice([-0.28, 0.28]), rng.uniform(-0.2, 0.24))) + v3((0, 0, 0.2))
        f.sub(Sphere(c, rng.uniform(0.05, 0.1)), k=0.02)
    ground_cut(f)
    return [("Blocks", f, fine(0.008, 0.016), "marble")]


def terrace_wall(L=2.2, h=0.42, seed=0):
    """A stretch of dry-stone terrace wall: rough limestone blocks laid in courses, the bank of earth behind it."""
    rng = np.random.default_rng(seed)
    f = Field("Wall")
    z = 0.0
    row = 0
    while z < h:
        bh = rng.uniform(0.1, 0.15)
        x = -L / 2 + (0.1 if row % 2 else 0.0)
        while x < L / 2:
            bw = rng.uniform(0.18, 0.32)
            cx = min(x + bw / 2, L / 2 - 0.05)
            f.add(RoundBox((cx, rng.uniform(-0.02, 0.02), z + bh / 2), (bw / 2 - 0.008, 0.11, bh / 2 - 0.006), 0.025,
                           **wob(8.0, 0.008, seed * 100 + row * 20 + int(x * 10))), k=0.004)
            x += bw
        z += bh
        row += 1
    e = Field("Bank")
    e.add(RoundBox((0, 0.32, h * 0.45), (L / 2 + 0.1, 0.3, h * 0.48), 0.12, **wob(3.0, 0.02, seed + 9)))
    e.inter(Plane((0, 0.1, h * 0.92), (0, -0.25, 1)))
    ground_cut(f)
    ground_cut(e)
    return [("Wall", f, fine(0.008, 0.016), "limestone"), ("Bank", e, fine(0.012, 0.024), "turf")]


def amphora(f, c, s=1.0, tilt=None, label=0):
    """One amphora: a tall body tapering to a pointed foot, a narrow neck, two handles."""
    R = tilt if tilt is not None else np.eye(3)
    up = R @ v3((0, 0, 1))
    side = R @ v3((1, 0, 0))
    f.add(Ellipsoid(c + up * 0.22 * s, (0.11 * s, 0.11 * s, 0.2 * s), R=R), k=0.0, label=label)
    f.add(RoundCone(c + up * 0.06 * s, c - up * 0.03 * s, 0.05 * s, 0.015 * s), k=0.03 * s, label=label)
    f.add(RoundCone(c + up * 0.38 * s, c + up * 0.5 * s, 0.045 * s, 0.035 * s), k=0.02 * s, label=label)
    f.add(Torus(c + up * 0.5 * s, 0.035 * s, 0.01 * s, R=R), k=0.005, label=label)
    for sd in (-1, 1):
        p0 = c + up * 0.47 * s + side * sd * 0.035 * s
        p1 = c + up * 0.47 * s + side * sd * 0.09 * s
        p2 = c + up * 0.36 * s + side * sd * 0.1 * s
        f.add(Chain([p0, p1, p2], [0.012 * s, 0.012 * s, 0.012 * s], k=0.004), k=0.008, label=label)


def amphorae(seed=0):
    """A heap of amphorae: three standing in a row, two leaning on them, one lying broken in the grass."""
    rng = np.random.default_rng(seed)
    f = Field("Amphorae")
    for k in range(3):
        amphora(f, v3((-0.22 + 0.22 * k, 0, 0.02)), 1.0, label=0 if k % 2 == 0 else 5)
    for k in range(2):
        R = rot_from_axes(z_axis=(0.0, -0.5 + 0.1 * k, 0.87), x_axis=(1, 0, 0))
        amphora(f, v3((-0.11 + 0.22 * k, -0.2, 0.04)), 0.9, R, label=5 if k == 0 else 0)
    R = rot_from_axes(z_axis=(0.95, 0.1, 0.15), x_axis=(0, 0, 1))
    amphora(f, v3((-0.5, 0.25, 0.1)), 0.95, R)
    f.sub(Sphere((-0.18, 0.28, 0.2), 0.09), k=0.01)
    ground_cut(f)
    return [("Amphorae", f, fine(0.006, 0.012), "pottery")]


# ------------------------------------------------------------------------------------------------ statues
def statue(seed=0, h=1.5):
    """A marble statue on a plinth: a draped figure (an orator, his cloak over one shoulder) with his right arm raised,
    weathered; the plinth's moulded top and foot, a carved panel on its face."""
    rng = np.random.default_rng(seed)
    f = Field("Statue")
    f.add(RoundBox((0, 0, 0.32), (0.32, 0.3, 0.32), 0.02))                               # the plinth
    f.add(RoundBox((0, 0, 0.04), (0.38, 0.36, 0.05), 0.015), k=0.01)
    f.add(RoundBox((0, 0, 0.62), (0.36, 0.34, 0.04), 0.015), k=0.01)
    f.sub(RoundBox((0, -0.3, 0.33), (0.22, 0.02, 0.2), 0.01), k=0.004)                    # its panel
    z0 = 0.66
    s = h / 1.5
    # the figure: legs under the drapery, the cloak's folds, the torso, the head; one arm raised in a speaker's gesture
    def folds(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        return (F32(0.008) * np.sin(a * F32(9) + P[:, 2] * F32(6))).astype(F32)
    f.add(RoundCone((0, 0.0, z0 + 0.02), (0, 0.0, z0 + 0.62 * s), 0.17 * s, 0.14 * s, disp=folds, disp_amp=0.01), k=0.03)
    f.add(Ellipsoid((0, 0.0, z0 + 0.74 * s), (0.15 * s, 0.1 * s, 0.17 * s)), k=0.06)           # chest
    f.add(Sphere((0, -0.01, z0 + 0.99 * s), 0.085 * s), k=0.03)                             # head
    f.add(RoundCone((0, 0.0, z0 + 0.86 * s), (0, -0.01, z0 + 0.94 * s), 0.05 * s, 0.045 * s), k=0.02)
    f.add(Ellipsoid((0, 0.02, z0 + 1.04 * s), (0.08 * s, 0.08 * s, 0.05 * s)), k=0.02)      # hair
    sh_r = v3((-0.14 * s, 0.0, z0 + 0.84 * s))
    el = sh_r + v3((-0.12 * s, -0.08 * s, 0.1 * s))
    wr = el + v3((-0.02 * s, -0.08 * s, 0.17 * s))
    f.add(Chain([sh_r, el, wr], [0.045 * s, 0.038 * s, 0.03 * s], k=0.01), k=0.03)
    f.add(Sphere(wr + v3((0, -0.01, 0.04 * s)), 0.035 * s), k=0.01)
    sh_l = v3((0.14 * s, 0.0, z0 + 0.84 * s))
    f.add(Chain([sh_l, sh_l + v3((0.05 * s, 0.02, -0.25 * s)), sh_l + v3((0.07 * s, -0.04, -0.45 * s))], [0.06 * s, 0.05 * s, 0.035 * s], k=0.01), k=0.04)
    f.add(Ellipsoid((0.11 * s, 0.01, z0 + 0.5 * s), (0.08 * s, 0.07 * s, 0.3 * s), disp=folds, disp_amp=0.01), k=0.04)   # the cloak's fall
    f.paint(Func(lambda P: (P[:, 2] - F32(0.2)).astype(F32), (-1, -1, -0.1), (1, 1, 2.5)), 7)
    ground_cut(f)
    return [("Statue", f, fine(0.006, 0.012), "marble")]


def lion(seed=0):
    """A marble lion lying on a plinth, head up and turned to watch the road, its mane in heavy locks."""
    f = Field("Lion")
    f.add(RoundBox((0, 0, 0.22), (0.62, 0.28, 0.22), 0.02))
    f.add(RoundBox((0, 0, 0.47), (0.66, 0.31, 0.03), 0.012), k=0.01)
    z0 = 0.5
    f.add(Ellipsoid((0.08, 0, z0 + 0.16), (0.42, 0.2, 0.16)), k=0.0)                        # the body lying down
    f.add(Ellipsoid((-0.28, 0, z0 + 0.24), (0.2, 0.22, 0.22)), k=0.08)                     # the chest and mane
    for k in range(12):                                                                     # the mane's locks
        a = 2 * math.pi * k / 12
        f.add(Ellipsoid((-0.32 + 0.04 * math.cos(a), 0.18 * math.sin(a), z0 + 0.32 + 0.14 * math.cos(a)), (0.07, 0.07, 0.09)), k=0.03)
    head = v3((-0.46, -0.06, z0 + 0.36))
    f.add(Ellipsoid(head, (0.13, 0.12, 0.12)), k=0.04)
    f.add(Ellipsoid(head + v3((-0.11, -0.02, -0.03)), (0.07, 0.07, 0.06)), k=0.03)          # muzzle
    for sd in (-1, 1):
        f.add(Ellipsoid((-0.42, sd * 0.14, z0 + 0.05), (0.16, 0.06, 0.05)), k=0.03)          # forepaws stretched out
        f.add(Ellipsoid((0.3, sd * 0.16, z0 + 0.1), (0.14, 0.07, 0.1)), k=0.04)              # haunches
    f.add(Chain([v3((0.48, 0.1, z0 + 0.08)), v3((0.6, 0.2, z0 + 0.03)), v3((0.52, 0.3, z0 + 0.02))], [0.03, 0.025, 0.035], k=0.01), k=0.02)
    f.paint(Func(lambda P: (P[:, 2] - F32(0.18)).astype(F32), (-1, -1, -0.1), (1, 1, 1.5)), 7)
    ground_cut(f)
    return [("Lion", f, fine(0.006, 0.012), "marble")]


# ------------------------------------------------------------------------------------------------ buildings
def stylobate(f, hx, hy, steps=3, step_h=0.09, step_w=0.12, label=0):
    """A stepped base: `steps` steps up to a top of half extents (hx, hy)."""
    for k in range(steps):
        e = (steps - 1 - k) * step_w
        f.add(RoundBox((0, 0, step_h * (k + 0.5)), (hx + e, hy + e, step_h / 2), 0.008), k=0.0, label=label)
    return step_h * steps


def ruined_temple(seed=0):
    """A small ruined Doric temple on its stepped base: four columns standing along one side and two at the front
    corner, the architrave still spanning two of them, the rest broken stumps; a fallen block on the steps."""
    rng = np.random.default_rng(seed)
    f = Field("Temple")
    hx, hy = 0.9, 1.4
    top = stylobate(f, hx, hy, 3)
    r = 0.13
    H = 1.35
    xs = (-hx + 0.16, hx - 0.16)
    ys = [(-hy + 0.16) + (2 * hy - 0.32) * k / 4 for k in range(5)]
    spots = [(xs[0], y) for y in ys] + [(xs[1], y) for y in ys] + [(0.0, ys[0]), (0.0, ys[-1])]
    standing = {(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)}
    for i, (x, y) in enumerate(spots):
        key = (0 if x < 0 else 1, ys.index(y)) if x != 0.0 else (2, i)
        if key in standing:
            f.add(doric_shaft(f, (x, y), top, top + H, r, r * 0.84, n=16, depth=0.01), k=0.006)
            doric_capital(f, (x, y), top + H, r * 0.84, k=0.006)
        else:
            hh = rng.uniform(0.15, 0.6)
            f.add(doric_shaft(f, (x, y), top, top + hh, r, r * 0.95, n=16, depth=0.01), k=0.006)
            cut_above(f, (x, y, top + hh), unit((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 1.0)), (r * 2, r * 2, 0.4),
                      disp=lambda P: NOISE.fbm(P * 9.0 + seed, 3) * 0.04, amp=0.05)
    za = top + H + 0.12
    f.add(RoundBox((xs[0], (ys[0] + ys[3]) / 2, za + 0.08), (0.14, (ys[3] - ys[0]) / 2 + 0.14, 0.08), 0.01), k=0.004)   # architrave
    f.add(RoundBox((xs[0], (ys[0] + ys[2]) / 2, za + 0.24), (0.15, (ys[2] - ys[0]) / 2 + 0.14, 0.08), 0.01), k=0.004)   # frieze
    for k in range(5):                                                                                    # its triglyphs
        y = ys[0] + (ys[2] - ys[0]) * k / 4
        f.add(RoundBox((xs[0] - 0.15, y, za + 0.24), (0.012, 0.035, 0.07), 0.004), k=0.002)
    f.add(RoundBox((hx * 0.3, -hy - 0.3, 0.12), (0.3, 0.18, 0.12), 0.02, R=Rz(0.4)), k=0.0)
    f.paint(Func(lambda P: (P[:, 2] - F32(0.3)).astype(F32), (-3, -3, -0.1), (3, 3, 3)), 7)
    ground_cut(f)
    return [("Temple", f, fine(0.008, 0.016), "marble")]


def farmhouse(seed=0):
    """A farmhouse: whitewashed walls of rubble stone under a terracotta tile roof, a plank door, small windows with
    shutters; a pergola of posts and beams with a vine over it beside the door; a big storage jar by the wall."""
    rng = np.random.default_rng(seed)
    w = Field("Walls")
    hx, hy, wh = 0.85, 0.55, 0.78
    w.add(walls_box(0, 0, hx, hy, 0.0, wh, batter=0.02, amp=0.006, seed=seed))
    w.sub(RoundBox((0.2, -hy, 0.3), (0.13, 0.08, 0.3), 0.01), k=0.004)                          # the doorway
    for x in (-0.48, 0.58):
        w.sub(RoundBox((x, -hy, 0.52), (0.08, 0.08, 0.08), 0.008), k=0.003)                     # windows
    w.sub(RoundBox((-hx, 0.1, 0.52), (0.08, 0.08, 0.08), 0.008), k=0.003)
    w.paint(Func(lambda P: (P[:, 2] - F32(0.1)).astype(F32), (-2, -2, -0.1), (2, 2, 2)), 7)     # its foot unwhitewashed
    roof = Field("Roof")
    roof.add(gable((0, 0), hx + 0.12, hy + 0.14, wh - 0.02, wh + 0.42, axis="x"))
    def tiles(P):                                                     # the rows of curved tiles running down the roof
        return (F32(0.012) * np.abs(np.sin(P[:, 0] * F32(36)))).astype(F32)
    roof.ops[-1][1].disp = tiles
    roof.ops[-1][1].disp_amp = 0.014
    wd = Field("Wood")
    wd.add(RoundBox((0.2, -hy - 0.005, 0.3), (0.12, 0.02, 0.29), 0.006), label=10)
    for x in (-0.48, 0.58):
        for sd in (-1, 1):
            wd.add(RoundBox((x + sd * 0.12, -hy - 0.02, 0.52), (0.035, 0.012, 0.085), 0.004), label=5)
    # the pergola beside the door, a vine over it
    px = 0.95
    posts = [(px + 0.0, -hy - 0.2), (px + 0.0, -hy - 0.9), (px + 0.65, -hy - 0.9), (px + 0.65, -hy - 0.2)]
    for (x, y) in posts:
        wd.add(RoundCone((x, y, 0.0), (x, y, 0.95), 0.035, 0.03), k=0.0, label=11)
    for y in (-hy - 0.2, -hy - 0.9):
        wd.add(RoundCone((px - 0.1, y, 0.97), (px + 0.75, y, 0.97), 0.03, 0.03), k=0.006, label=10)
    for k in range(5):
        x = px - 0.05 + 0.18 * k
        wd.add(RoundCone((x, -hy - 0.1, 1.02), (x, -hy - 1.0, 1.02), 0.02, 0.02), k=0.004)
    vine = Field("Vine")
    for k in range(14):
        q = v3((px + rng.uniform(-0.1, 0.75), -hy + rng.uniform(-1.0, -0.1), 1.08 + rng.uniform(-0.02, 0.06)))
        r = rng.uniform(0.1, 0.16)
        vine.add(Ellipsoid(q, (r, r, r * 0.45), **wob(12.0, 0.02, seed * 40 + k)), k=0.04)
    vine.add(Chain([v3((px + 0.66, -hy - 0.92, 0.0)), v3((px + 0.6, -hy - 0.9, 0.5)), v3((px + 0.66, -hy - 0.88, 1.0))], [0.03, 0.025, 0.02], k=0.01), k=0.02)
    jar = Field("Jar")
    jar.add(Ellipsoid((-0.55, -hy - 0.24, 0.26), (0.2, 0.2, 0.26)), k=0.0)
    jar.add(Torus((-0.55, -hy - 0.24, 0.5), 0.09, 0.025), k=0.02)
    jar.sub(Cylinder((-0.55, -hy - 0.24, 0.52), 0.07, 0.1), k=0.01)
    for part in (w, roof, wd, vine, jar):
        ground_cut(part)
    return [("Walls", w, fine(0.008, 0.016), "plaster"), ("Roof", roof, fine(0.008, 0.016), "tiles"),
            ("Wood", wd, fine(0.006, 0.012), "timber"), ("Vine", vine, fine(0.01, 0.02), "olive_leaves"),
            ("Jar", jar, fine(0.006, 0.012), "pottery")]


def olive_press(seed=0):
    """An olive press: a round stone basin on a low base, an upright millstone standing in it, turned on a wooden
    axle through the central post by a long beam; a basket of olives and two amphorae by it."""
    f = Field("Stone")
    R0 = 0.55
    def basin(P):
        rr = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        outer = np.maximum(rr - F32(R0), np.abs(P[:, 2] - F32(0.2)) - F32(0.2))
        inner = np.maximum(rr - F32(R0 - 0.08), F32(0.3) - P[:, 2])
        return np.maximum(outer, -inner).astype(F32)
    f.add(Func(basin, (-R0 - 0.05, -R0 - 0.05, -0.05), (R0 + 0.05, R0 + 0.05, 0.45), **wob(5.0, 0.005, seed)))
    f.add(Cylinder((0, 0, 0.42), 0.1, 0.24, rr=0.02), k=0.02)                                   # the central post's stone
    f.add(Cylinder((0.28, 0, 0.6), 0.3, 0.13, rr=0.03, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.0)   # the millstone on edge
    wd = Field("Wood")
    wd.add(RoundCone((0, 0, 0.3), (0, 0, 0.95), 0.05, 0.045), label=11)
    wd.add(RoundCone((-0.05, 0, 0.6), (0.48, 0, 0.6), 0.035, 0.035), k=0.01, label=10)          # the axle
    wd.add(RoundCone((0, 0.0, 0.9), (-1.0, 0.15, 0.82), 0.04, 0.035), k=0.01, label=10)       # the beam
    bk = Field("Basket")
    bk.add(Cylinder((-0.55, -0.55, 0.13), 0.17, 0.26, rr=0.03), k=0.0)
    bk.sub(Cylinder((-0.55, -0.55, 0.24), 0.14, 0.1), k=0.01)
    ol = Field("Olives")
    rng = np.random.default_rng(seed)
    for k in range(10):
        ol.add(Sphere((-0.55 + rng.uniform(-0.1, 0.1), -0.55 + rng.uniform(-0.1, 0.1), 0.24 + rng.uniform(0, 0.03)), 0.03), k=0.005)
    am = Field("Amphorae")
    amphora(am, v3((0.62, -0.5, 0.02)), 0.9)
    amphora(am, v3((0.8, -0.32, 0.02)), 0.85, label=5)
    for part in (f, wd, bk, am):
        ground_cut(part)
    return [("Stone", f, fine(0.008, 0.016), "limestone"), ("Wood", wd, fine(0.006, 0.012), "timber"),
            ("Basket", bk, fine(0.006, 0.012), "basket"), ("Olives", ol, fine(0.005, 0.01), "olive_fruit"),
            ("Amphorae", am, fine(0.006, 0.012), "pottery")]


def aqueduct(seed=0, n_arch=3, span=1.9, pier=0.42, H=2.3, broken=False):
    """A stretch of aqueduct: tall piers of cut stone carrying round arches, the water channel along the top under its
    capping slabs; along X, centred on the origin (its middle arch over the road). broken: both ends broken off in
    jagged steps (the one arch left standing over a road)."""
    rng = np.random.default_rng(seed)
    f = Field("Aqueduct")
    L = n_arch * span + (n_arch + 1) * pier
    T = 0.42
    f.add(RoundBox((0, 0, H / 2 + 0.1), (L / 2, T / 2, H / 2 + 0.1), 0.01, **wob(4.0, 0.004, seed)))
    for k in range(n_arch):                                            # the arches
        cx = -L / 2 + pier + span / 2 + k * (span + pier)
        r = span / 2
        spring = H - 0.55 - r
        f.sub(Cylinder((cx, 0, spring), r, T + 0.2, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.01)
        f.sub(RoundBox((cx, 0, spring / 2 - 0.1), (r, T / 2 + 0.1, spring / 2 + 0.1), 0.0), k=0.01)
        for j in range(9):                                               # the voussoirs' joints round the arch
            a = math.pi * (j + 0.5) / 9
            d = v3((math.cos(a), 0, math.sin(a)))
            p = v3((cx, -T / 2, spring)) + d * (r + 0.12)
            f.sub(RoundBox(p, (0.008, 0.02, 0.12), 0.0, R=rot_from_axes(z_axis=d, y_axis=(0, 1, 0))), k=0.002)
    for z in np.arange(0.35, H, 0.3):                                    # courses of the cut stone
        f.sub(RoundBox((0, -T / 2, z), (L / 2 + 0.1, 0.012, 0.006), 0.0), k=0.002)
        f.sub(RoundBox((0, T / 2, z), (L / 2 + 0.1, 0.012, 0.006), 0.0), k=0.002)
    f.add(RoundBox((0, 0, H + 0.24), (L / 2 + 0.04, T / 2 + 0.05, 0.05), 0.01), k=0.0)              # the cornice
    f.add(RoundBox((0, 0, H + 0.42), (L / 2, T / 2 - 0.02, 0.14), 0.01), k=0.0)                   # the channel's walls
    f.add(RoundBox((0, 0, H + 0.6), (L / 2 + 0.02, T / 2 + 0.03, 0.04), 0.01), k=0.0)            # its capping slabs
    for x in np.arange(-L / 2 + 0.3, L / 2, 0.6):
        f.sub(RoundBox((x, 0, H + 0.64), (0.008, T / 2 + 0.05, 0.05), 0.0), k=0.002)
    for _ in range(8):                                                   # weathering: chips off the edges
        x = rng.uniform(-L / 2, L / 2)
        f.sub(Sphere((x, rng.choice([-T / 2, T / 2]), rng.uniform(0.3, H)), rng.uniform(0.04, 0.08)), k=0.01)
    if broken:
        for sd in (-1, 1):                                               # its ends broken off, the top first
            cut_above(f, (sd * (L / 2 - 0.15), 0, H * 0.55), unit((sd * 0.75, 0, 0.65)), (0.55, T, H * 0.7),
                      disp=lambda P: NOISE.fbm(P * 5.0 + seed, 3) * 0.12, amp=0.14)
            cut_above(f, (sd * (L / 2 - 0.05), 0, H * 0.2), unit((sd * 1.0, 0, 0.25)), (0.3, T, H * 0.5),
                      disp=lambda P: NOISE.fbm(P * 7.0 + seed + 3, 3) * 0.08, amp=0.1)
    f.paint(Func(lambda P: (P[:, 2] - F32(0.5)).astype(F32), (-6, -2, -0.1), (6, 2, 4)), 7)
    ground_cut(f)
    return [("Aqueduct", f, fine(0.012, 0.024), "ashlar")]


def bridge(seed=0, L=3.4, W=2.1):
    """A stone bridge's two parapets along the road over the water (the road between them), each ending in a squat
    pillar, and the arch's faces showing below them down to the water; along X, centred on the origin."""
    f = Field("Bridge")
    f.add(RoundBox((0, 0, -0.08), (L / 2, W / 2 + 0.05, 0.07), 0.01), k=0.0)          # the deck (the road's paving covers it)
    for sd in (-1, 1):
        y = sd * (W / 2 + 0.1)
        f.add(RoundBox((0, y, 0.14), (L / 2, 0.11, 0.32), 0.02, **wob(4.0, 0.004, seed + sd)), k=0.0)   # (down into the water)
        f.add(RoundBox((0, y, 0.48), (L / 2 + 0.03, 0.14, 0.03), 0.01), k=0.004)
        for x in (-L / 2, L / 2):
            f.add(RoundBox((x, y, 0.32), (0.16, 0.18, 0.34), 0.02), k=0.004)
            f.add(RoundBox((x, y, 0.69), (0.19, 0.21, 0.04), 0.01), k=0.004)
        # the arch face below the road: a ring of voussoirs sunk to the water line
        f.add(Torus((0, y, -1.15), 1.3, 0.1, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.0)
    f.inter(Plane((0, 0, -0.12), (0, 0, -1)))
    for x in np.arange(-L / 2 + 0.3, L / 2, 0.36):
        for sd in (-1, 1):
            f.sub(RoundBox((x, sd * (W / 2 + 0.21), 0.24), (0.006, 0.012, 0.2), 0.0), k=0.002)
    return [("Bridge", f, fine(0.008, 0.016), "ashlar")]


def lighthouse(seed=0):
    """A lighthouse: a square tower of cut stone stepping in twice as it rises, a door and slit windows, a parapet at the
    top round a bronze brazier where the fire burns (the game adds the flame)."""
    f = Field("Tower")
    f.add(RoundBox((0, 0, 0.6), (0.55, 0.55, 0.6), 0.02))
    f.add(RoundBox((0, 0, 1.55), (0.42, 0.42, 0.38), 0.02), k=0.0)
    f.add(RoundBox((0, 0, 2.2), (0.3, 0.3, 0.3), 0.02), k=0.0)
    for z, h in ((1.22, 0.55), (1.95, 0.42)):
        f.add(RoundBox((0, 0, z), (h + 0.04, h + 0.04, 0.04), 0.01), k=0.004)
    f.add(RoundBox((0, 0, 2.52), (0.36, 0.36, 0.04), 0.01), k=0.004)
    for sd in (-1, 1):
        for a in range(2):
            x, y = (sd * 0.33, 0.0) if a == 0 else (0.0, sd * 0.33)
            f.add(RoundBox((x, y, 2.62), (0.03 if a == 0 else 0.33, 0.33 if a == 0 else 0.03, 0.08), 0.01), k=0.004)
    f.sub(RoundBox((0, -0.55, 0.32), (0.13, 0.06, 0.3), 0.01), k=0.004)
    for z in (0.9, 1.55, 2.2):
        f.sub(RoundBox((0, -0.6 + (z - 0.9) * 0.18, z), (0.03, 0.1, 0.1), 0.004), k=0.003)
    for z in np.arange(0.25, 2.5, 0.25):
        hw = 0.55 if z < 1.2 else (0.42 if z < 1.93 else 0.3)
        for sd in (-1, 1):
            f.sub(RoundBox((0, sd * hw, z), (hw + 0.05, 0.01, 0.005), 0.0), k=0.002)
            f.sub(RoundBox((sd * hw, 0, z), (0.01, hw + 0.05, 0.005), 0.0), k=0.002)
    f.paint(Func(lambda P: (P[:, 2] - F32(0.35)).astype(F32), (-2, -2, -0.1), (2, 2, 4)), 7)
    br = Field("Brazier")
    br.add(Cylinder((0, 0, 2.66), 0.1, 0.12, rr=0.02), k=0.0)
    br.add(Ellipsoid((0, 0, 2.8), (0.2, 0.2, 0.1)), k=0.02)
    br.sub(Ellipsoid((0, 0, 2.86), (0.17, 0.17, 0.08)), k=0.01)
    co = Field("Coals")
    co.add(Ellipsoid((0, 0, 2.83), (0.16, 0.16, 0.05)), k=0.0)
    ground_cut(f)
    return [("Tower", f, fine(0.009, 0.018), "ashlar"), ("Brazier", br, fine(0.006, 0.012), "bronze"),
            ("Coals", co, fine(0.006, 0.012), "glow_fire")]


def boat(seed=0):
    """A fishing boat drawn up on the shore: a clinker hull with a raised curved stern and an eye painted at the bow, a
    mast with its sail furled on the yard, oars inside, a net heaped at the stern."""
    f = Field("Hull")
    L, W, D = 1.5, 0.42, 0.3

    def hull(P):
        x = P[:, 0] / F32(L / 2)
        hw = F32(W / 2) * np.sqrt(np.clip(F32(1) - x * x, 0, 1)) + F32(0.004)
        z = P[:, 2]
        keel = F32(0.02) + F32(0.12) * x * x
        top = F32(D) + F32(0.12) * np.clip(x, 0, 1) ** 2 + F32(0.05) * np.clip(-x, 0, 1) ** 2
        d_out = np.maximum(np.abs(P[:, 1]) - hw * np.clip((z - keel) / F32(0.12), 0.15, 1), np.maximum(keel - z, z - top))
        d_in = np.maximum(np.abs(P[:, 1]) - (hw - F32(0.03)), np.maximum(keel + F32(0.05) - z, F32(-1)))
        return np.maximum(d_out, -d_in).astype(F32) * F32(0.8)
    f.add(Func(hull, (-L / 2 - 0.05, -W / 2 - 0.05, -0.05), (L / 2 + 0.05, W / 2 + 0.05, D + 0.2)))
    f.add(Chain([v3((L / 2 - 0.05, 0, D)), v3((L / 2 + 0.06, 0, D + 0.18)), v3((L / 2 + 0.0, 0, D + 0.3))], [0.03, 0.025, 0.02], k=0.01), k=0.02)
    for z in (0.12, 0.2):                                                 # the planks' laps
        f.sub(Func(lambda P, z=z: (np.abs(P[:, 2] - F32(z) - F32(0.05) * (P[:, 0] / F32(L / 2)) ** 2) - F32(0.006)).astype(F32),
                   (-L, -W, 0), (L, W, D + 0.2)), k=0.0)
    for sd in (-1, 1):                                                    # the eye at the bow
        f.paint(Sphere((-L / 2 + 0.2, sd * (W / 2 - 0.06), D - 0.06), 0.045), 5)
    f.inter(Plane((0, 0, -0.05), (0, 0, -1)))
    wd = Field("Rig")
    wd.add(RoundCone((-0.1, 0, 0.1), (-0.1, 0, 1.3), 0.025, 0.018), label=11)
    wd.add(RoundCone((-0.1, -0.5, 1.2), (-0.1, 0.5, 1.2), 0.02, 0.02), k=0.005, label=10)
    for sd in (-1, 1):
        wd.add(RoundCone((-0.5, sd * 0.1, 0.25), (0.45, sd * 0.13, 0.3), 0.015, 0.015), k=0.0, label=10)
    sail = Field("Sail")
    sail.add(Ellipsoid((-0.1, 0, 1.12), (0.05, 0.48, 0.07)), k=0.0)
    net = Field("Net")
    net.add(Ellipsoid((0.45, 0, 0.25), (0.16, 0.13, 0.08), **wob(20.0, 0.01, seed)), k=0.0)
    return [("Hull", f, fine(0.006, 0.012), "boat"), ("Rig", wd, fine(0.005, 0.01), "timber"),
            ("Sail", sail, fine(0.006, 0.012), "sailcloth"), ("Net", net, fine(0.006, 0.012), "rope")]


def great_temple(seed=0):
    """The temple of the hill: a Doric temple on its three-stepped base, columns all round (eight across the front,
    two missing on one flank, one broken), the architrave and the frieze of triglyphs round the top, a pediment at each
    end with the low-pitched roof between them, part of it fallen in."""
    rng = np.random.default_rng(seed)
    f = Field("Temple")
    hx, hy = 1.5, 2.6
    top = stylobate(f, hx, hy, 3, 0.1, 0.13)
    r = 0.15
    H = 1.55
    nx, ny = 6, 11
    missing = {(1, 4), (1, 5)}
    broken = {(1, 6)}
    cols = []
    for i in range(nx):
        x = -hx + 0.18 + (2 * hx - 0.36) * i / (nx - 1)
        cols += [(x, -hy + 0.18, ("f", i)), (x, hy - 0.18, ("b", i))]
    for j in range(1, ny - 1):
        y = -hy + 0.18 + (2 * hy - 0.36) * j / (ny - 1)
        cols += [(-hx + 0.18, y, (0, j)), (hx - 0.18, y, (1, j))]
    for x, y, key in cols:
        if key in missing:
            continue
        if key in broken:
            f.add(doric_shaft(f, (x, y), top, top + 0.7, r, r * 0.92, n=16, depth=0.01), k=0.006)
            cut_above(f, (x, y, top + 0.7), unit((0.4, -0.3, 1.0)), (r * 2, r * 2, 0.4), disp=lambda P: NOISE.fbm(P * 9.0, 3) * 0.04, amp=0.05)
            continue
        f.add(doric_shaft(f, (x, y), top, top + H, r, r * 0.83, n=16, depth=0.01), k=0.006)
        doric_capital(f, (x, y), top + H, r * 0.83, k=0.006)
    za = top + H + 0.14
    f.add(RoundBox((0, 0, za + 0.1), (hx - 0.02, hy - 0.02, 0.1), 0.01), k=0.004)                 # architrave
    f.add(RoundBox((0, 0, za + 0.3), (hx - 0.02, hy - 0.02, 0.1), 0.01), k=0.004)                 # frieze
    for i in range(16):                                                                           # triglyphs on the front and back
        x = -hx + 0.1 + (2 * hx - 0.2) * i / 15
        for sd in (-1, 1):
            f.add(RoundBox((x, sd * (hy - 0.01), za + 0.3), (0.035, 0.012, 0.085), 0.004), k=0.002)
    f.add(RoundBox((0, 0, za + 0.45), (hx + 0.04, hy + 0.04, 0.05), 0.01), k=0.004)               # cornice
    zr = za + 0.5
    for sd in (-1, 1):                                                                            # the pediments
        y = sd * (hy - 0.04)
        def ped(P, y=y):
            return np.maximum(np.maximum(np.abs(P[:, 0]) * F32(0.33) + (P[:, 2] - F32(zr)) - F32(0.5), F32(zr) - P[:, 2]),
                              np.abs(P[:, 1] - F32(y)) - F32(0.06)).astype(F32)
        f.add(Func(ped, (-hx - 0.1, y - 0.1, zr - 0.05), (hx + 0.1, y + 0.1, zr + 0.6)), k=0.004)
    roof = Field("Roof")
    def roof_fn(P):
        ridge = F32(zr) + F32(0.5) - np.abs(P[:, 0]) * F32(0.33)
        slab = np.maximum(P[:, 2] - ridge, ridge - F32(0.08) - P[:, 2])
        return np.maximum(np.maximum(slab, np.abs(P[:, 0]) - F32(hx + 0.08)), np.abs(P[:, 1]) - F32(hy - 0.05)).astype(F32)
    roof.add(Func(roof_fn, (-hx - 0.2, -hy, zr - 0.1), (hx + 0.2, hy, zr + 0.6),
                  disp=lambda P: (F32(0.008) * np.abs(np.sin(P[:, 1] * F32(30)))).astype(F32), disp_amp=0.01))
    roof.sub(Ellipsoid((0.4, 0.6, zr + 0.4), (0.8, 1.1, 0.6)), k=0.04)                           # fallen in
    for _ in range(6):                                                                            # blocks fallen at its foot
        a = rng.uniform(0, 2 * math.pi)
        c = v3((math.cos(a) * (hx + 0.55), math.sin(a) * (hy + 0.4), 0.1))
        f.add(RoundBox(c, (rng.uniform(0.12, 0.2), rng.uniform(0.1, 0.16), 0.1), 0.02, R=Rz(rng.uniform(0, 3))), k=0.0)
    f.paint(Func(lambda P: (P[:, 2] - F32(0.4)).astype(F32), (-4, -4, -0.1), (4, 4, 4)), 7)
    ground_cut(f)
    return [("Temple", f, fine(0.009, 0.018), "marble"), ("Roof", roof, fine(0.01, 0.02), "tiles")]


def theatre(seed=0):
    """A theatre: rows of stone seats rising round a semicircle cut into the slope, a stair up through them, the round
    floor (orchestra) at their foot and the low stage building across its open side."""
    f = Field("Seats")
    R0, R1, n = 0.7, 2.2, 7
    for k in range(n):
        r_in = R0 + (R1 - R0) * k / n
        r_out = R0 + (R1 - R0) * (k + 1) / n
        z1 = 0.12 * (k + 1)
        def row(P, r_in=r_in, r_out=r_out, z1=z1):
            rr = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
            d = np.maximum(np.maximum(rr - F32(r_out), F32(r_in) - rr), np.maximum(P[:, 2] - F32(z1), F32(-0.05) - P[:, 2]))
            return np.maximum(d, -P[:, 1]).astype(F32)                      # (the open side faces -Y)
        f.add(Func(row, (-r_out - 0.05, -0.1, -0.1), (r_out + 0.05, r_out + 0.05, z1 + 0.05)), k=0.0)
    for a in (math.radians(55), math.radians(125)):                        # the stairs
        d = v3((math.cos(a), math.sin(a), 0.0))
        for k in range(n * 2):
            r = R0 + (R1 - R0) * (k + 0.5) / (n * 2)
            f.sub(RoundBox(d * r + v3((0, 0, 0.06 * (k + 1) + 0.04)), (0.12, 0.05, 0.04), 0.0, R=Rz(a)), k=0.0)
    f.add(Cylinder((0, 0, 0.02), R0 - 0.03, 0.04, rr=0.01), k=0.0)                                # the orchestra
    f.add(RoundBox((0, -0.55, 0.22), (1.1, 0.16, 0.22), 0.02), k=0.0)                             # the stage building
    for x in (-0.6, 0.0, 0.6):
        f.sub(RoundBox((x, -0.7, 0.18), (0.1, 0.05, 0.16), 0.01), k=0.004)
    f.paint(Func(lambda P: (P[:, 2] - F32(0.15)).astype(F32), (-3, -3, -0.1), (3, 3, 2)), 7)
    ground_cut(f)
    return [("Seats", f, fine(0.009, 0.018), "limestone")]


def altar(seed=0):
    """An altar: a marble block on two steps, its top carved with volutes at the ends, a garland in relief on its
    front, embers glowing in a bronze bowl on top (the game adds the smoke)."""
    f = Field("Altar")
    stylobate(f, 0.5, 0.36, 2, 0.07, 0.09)
    f.add(RoundBox((0, 0, 0.42), (0.38, 0.24, 0.28), 0.02), k=0.0)
    for sd in (-1, 1):
        f.add(Cylinder((sd * 0.34, 0, 0.72), 0.07, 0.48, rr=0.03, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.01)
    f.add(RoundBox((0, 0, 0.71), (0.36, 0.22, 0.03), 0.01), k=0.006)
    for k in range(5):
        x = -0.24 + 0.12 * k
        f.add(Ellipsoid((x, -0.245, 0.5 - 0.04 * math.sin(k * math.pi / 4)), (0.05, 0.015, 0.03)), k=0.004)
    f.paint(Func(lambda P: (P[:, 2] - F32(0.15)).astype(F32), (-2, -2, -0.1), (2, 2, 2)), 7)
    br = Field("Bowl")
    br.add(Ellipsoid((0, 0, 0.8), (0.16, 0.16, 0.07)), k=0.0)
    br.sub(Ellipsoid((0, 0, 0.84), (0.14, 0.14, 0.05)), k=0.01)
    co = Field("Coals")
    co.add(Ellipsoid((0, 0, 0.81), (0.12, 0.12, 0.035)), k=0.0)
    ground_cut(f)
    return [("Altar", f, fine(0.007, 0.014), "marble"), ("Bowl", br, fine(0.005, 0.01), "bronze"), ("Coals", co, fine(0.005, 0.01), "glow_fire")]


# ------------------------------------------------------------------------------------------------ the Classical city
def crenels(f, x0, y0, x1, y1, z, n=None, w=0.16, h=0.2, t=0.42, label=0):
    """Merlons along a wall top from (x0, y0) to (x1, y1) at height z (w: half length along the wall, t: thickness)."""
    a, b = v3((x0, y0, 0)), v3((x1, y1, 0))
    L = float(np.linalg.norm(b - a))
    n = n or max(2, int(L / (2 * w + 0.12)))
    d = unit(b - a)
    R = R_xz(d, (0, 0, 1))
    for i in range(n):
        c = a + d * (L * (i + 0.5) / n) + v3((0, 0, z + h / 2))
        f.add(RoundBox(c, (w, t / 2, h / 2), 0.012, R=R), k=0.004, label=label)


def town_house(out, name, c, hx, hy, wh, yaw, seed):
    """A town house: whitewashed walls under a terracotta tile roof, a door and a window or two (the door on its -Y
    side, before the turn by yaw)."""
    w = Field(name + "Walls")
    R = Rz(yaw)
    cx, cy = float(c[0]), float(c[1])
    w.add(walls_box(0, 0, hx, hy, -0.05, wh, batter=0.015, amp=0.005, seed=seed))
    w.sub(RoundBox((0.0, -hy, 0.28), (0.11, 0.06, 0.28), 0.01), k=0.004)
    for x in (-hx * 0.55, hx * 0.55):
        w.sub(RoundBox((x, -hy, wh * 0.68), (0.06, 0.06, 0.07), 0.006), k=0.003)
    w.paint(Func(lambda P: (P[:, 2] - F32(0.08)).astype(F32), (-3, -3, -0.2), (3, 3, 3)), 7)
    roof = Field(name + "Roof")
    roof.add(gable((0, 0), hx + 0.1, hy + 0.12, wh - 0.02, wh + 0.36 * (hy / 0.5), axis="x"))
    roof.ops[-1][1].disp = lambda P: (F32(0.012) * np.abs(np.sin(P[:, 0] * F32(36)))).astype(F32)
    roof.ops[-1][1].disp_amp = 0.014
    dr = Field(name + "Door")
    dr.add(RoundBox((0.0, -hy + 0.02, 0.28), (0.1, 0.02, 0.27), 0.006), label=10)
    ground_cut(w)
    ground_cut(dr)
    place_parts(out, [(name + "Walls", w, fine(0.008, 0.016), "plaster"), (name + "Roof", roof, fine(0.008, 0.016), "tiles"),
                      (name + "Door", dr, fine(0.006, 0.012), "timber")], (cx, cy, 0.0), R)


def _ring_groove(cx, cy, half, z, depth=0.012, w=0.006, batter=0.0):
    """A horizontal groove (a course joint) cut all round a square block of half extent `half` at height z (its faces
    leaning in by `batter` per unit height)."""
    hz = half - batter * z

    def fn(P):
        m = np.maximum(np.abs(P[:, 0] - F32(cx)), np.abs(P[:, 1] - F32(cy)))
        return np.maximum.reduce([np.abs(P[:, 2] - F32(z)) - F32(w), F32(hz - depth) - m, m - F32(hz + 0.02)]).astype(F32)
    return Func(fn, (cx - half - 0.1, cy - half - 0.1, z - 0.04), (cx + half + 0.1, cy + half + 0.1, z + 0.04))


def classical_city(seed=0):
    """The gate of a walled city at the end of the road (the gate faces -X, where the road comes in): two square towers
    of cut stone with crenellated tops and slit windows, an arched gateway between them under a crenellated walkway,
    bronze-studded doors; the wall running off both ways with its parapet, dying away into the hillside;
    bronze braziers on tripods before the towers (game.gd lights them); red banners with a gold wreath down the towers;
    inside, town houses under terracotta roofs and the front of a temple (four columns under a pediment) rising
    behind them."""
    out = []
    TY, TX, TH, TS = 1.35, 0.8, 2.5, 0.62
    BAT = 0.02
    GH = 2.0                                                    # the gateway's walkway
    WH = 1.75                                                   # the walls' walkway
    st = Field("Stone")
    for sy in (-1, 1):                                         # the towers
        cy = sy * TY
        st.add(walls_box(TX, cy, TS, TS, -0.05, TH, batter=BAT, amp=0.004, seed=seed + sy))
        st.add(RoundBox((TX, cy, TH + 0.04), (TS - BAT * TH + 0.05, TS - BAT * TH + 0.05, 0.05), 0.01), k=0.004)
        e = TS - BAT * TH + 0.02
        crenels(st, TX - e, cy - e, TX - e, cy + e, TH + 0.08, 3, w=0.13, t=0.14)
        crenels(st, TX + e, cy - e, TX + e, cy + e, TH + 0.08, 3, w=0.13, t=0.14)
        crenels(st, TX - e, cy + sy * e, TX + e, cy + sy * e, TH + 0.08, 3, w=0.13, t=0.14)
        crenels(st, TX - e, cy - sy * e, TX + e, cy - sy * e, TH + 0.08, 3, w=0.13, t=0.14)
        # slit windows: one high on the front (over the banner), two on the outer side
        fx = TX - TS + BAT * 2.27
        st.sub(RoundBox((fx, cy, 2.27), (0.1, 0.035, 0.11), 0.006), k=0.003)
        for z in (1.05, 1.8):
            fy = cy + sy * (TS - BAT * z)
            st.sub(RoundBox((TX - 0.15, fy, z), (0.035, 0.1, 0.12), 0.006), k=0.003)
        for z in np.arange(0.3, TH - 0.1, 0.3):                                             # courses
            st.sub(_ring_groove(TX, cy, TS, z, batter=BAT), k=0.002)
    # the gateway between the towers: a wall with an arched opening, a crenellated walkway over it
    gw = TY - TS + 0.1
    st.add(RoundBox((TX, 0, (GH - 0.05) / 2), (0.4, gw, (GH + 0.05) / 2), 0.01), k=0.004)
    st.sub(Cylinder((TX, 0, 1.15), 0.62, 1.0, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.01)
    st.sub(RoundBox((TX, 0, 0.55), (0.6, 0.62, 0.62), 0.0), k=0.01)
    for j in range(9):                                                                    # the arch's voussoirs
        a = math.pi * (j + 0.5) / 9
        d = v3((0, math.cos(a), math.sin(a)))
        st.sub(RoundBox(v3((TX - 0.4, 0, 1.15)) + d * 0.72, (0.025, 0.01, 0.11), 0.0, R=R_xz((1, 0, 0), d)), k=0.002)
    st.add(RoundBox((TX - 0.4, 0, 1.15 + 0.86), (0.03, 0.3, 0.05), 0.01), k=0.004)          # the keystone's tablet
    crenels(st, TX - 0.33, -gw + 0.05, TX - 0.33, gw - 0.05, GH, 3, w=0.12, t=0.14)
    for z in np.arange(0.3, GH - 0.1, 0.3):
        st.sub(Func(lambda P, z=z: np.maximum.reduce([np.abs(P[:, 2] - F32(z)) - F32(0.006), np.abs(P[:, 0] - F32(TX - 0.4)) - F32(0.012),
                                                      np.abs(P[:, 1]) - F32(gw)]).astype(F32),
                    (TX - 0.5, -gw - 0.1, z - 0.04), (TX - 0.3, gw + 0.1, z + 0.04)), k=0.002)
    # the walls running off both ways (out to |y| ~ 7, dying away into the hillside)
    for sy in (-1, 1):
        def wall(P, sy=sy):
            x, y, z = P[:, 0], P[:, 1] * F32(sy), P[:, 2]
            fade = np.clip((F32(7.0) - y) / F32(1.6), 0.0, 1.0)
            hgt = F32(WH) * fade
            d = np.maximum(np.abs(x - F32(TX)) - F32(0.28) - F32(0.05) * np.clip(F32(0.6) - z, 0, 1), z - hgt)
            return np.maximum(d, np.maximum(F32(TY + TS - 0.15) - y, y - F32(7.1))).astype(F32)
        lo = (TX - 0.5, (TY + TS - 0.25) if sy > 0 else -7.2, -0.1)
        hi = (TX + 0.5, 7.2 if sy > 0 else -(TY + TS - 0.25), WH + 0.1)
        st.add(Func(wall, lo, hi, **wob(4.0, 0.006, seed + 3 + sy)), k=0.01)
        y = TY + TS + 0.2
        while y < 5.25:                                                                   # the parapet's merlons
            st.add(RoundBox((TX - 0.21, sy * y, WH + 0.1), (0.07, 0.13, 0.11), 0.012), k=0.004)
            y += 0.42
        st.add(RoundBox((TX - 0.21, sy * (TY + TS + 1.8), WH + 0.02), (0.07, 1.8, 0.03), 0.01), k=0.004)
        for z in np.arange(0.3, WH - 0.1, 0.3):
            st.sub(Func(lambda P, z=z, sy=sy: np.maximum.reduce([np.abs(P[:, 2] - F32(z)) - F32(0.006),
                                                                 np.abs(P[:, 0] - F32(TX - 0.28)) - F32(0.012),
                                                                 F32(TY + TS) - P[:, 1] * F32(sy), P[:, 1] * F32(sy) - F32(5.5)]).astype(F32),
                        (TX - 0.4, -6, z - 0.05), (TX - 0.2, 6, z + 0.05)), k=0.002)
    st.paint(Func(lambda P: (P[:, 2] - F32(0.35)).astype(F32), (-1, -8, -0.2), (3, 8, 4)), 7)
    ground_cut(st, -0.04)
    out.append(("Stone", st, fine(0.012, 0.024), "ashlar"))
    gd = Field("Gate")                                                                    # the doors, closed, studded with bronze
    for sy in (-1, 1):
        def door(P, sy=sy):
            q = P - np.array([TX - 0.1, sy * 0.3, 0.0], F32)
            arch = np.sqrt(P[:, 1] ** 2 + np.maximum(P[:, 2] - F32(1.15), F32(0)) ** 2) - F32(0.61)
            return np.maximum.reduce([np.abs(q[:, 0]) - F32(0.05), arch, F32(-0.02) - P[:, 2], np.abs(q[:, 1]) - F32(0.305)]).astype(F32)
        gd.add(Func(door, (TX - 0.2, sy * 0.3 - 0.35, -0.05), (TX, sy * 0.3 + 0.35, 1.8)), label=11)
        for z in (0.4, 0.9, 1.4):
            for k in range(3):
                gd.add(Sphere((TX - 0.155, sy * (0.1 + k * 0.17), z), 0.022), k=0.003, label=6)
        gd.add(RoundBox((TX - 0.155, sy * 0.3, 0.65), (0.01, 0.29, 0.025), 0.004), k=0.003, label=6)   # iron bands
        gd.add(RoundBox((TX - 0.155, sy * 0.3, 1.15), (0.01, 0.29, 0.025), 0.004), k=0.003, label=6)
    ground_cut(gd)
    out.append(("Gate", gd, fine(0.006, 0.012), "timber"))
    br = Field("Braziers")                                                                # bronze braziers on tripods
    for sy in (-1, 1):
        c = v3((-0.15, sy * (TY + 0.1), 0.0))
        for k in range(3):                                        # three legs curving out to lion's paws
            a = 2 * math.pi * k / 3 + 0.5
            d = v3((math.cos(a), math.sin(a), 0.0))
            br.add(Chain([c + d * 0.34 + v3((0, 0, 0.04)), c + d * 0.24 + v3((0, 0, 0.3)), c + d * 0.15 + v3((0, 0, 0.62)),
                          c + d * 0.19 + v3((0, 0, 0.96))], [0.026, 0.022, 0.02, 0.022], k=0.01), k=0.006)
            br.add(Ellipsoid(c + d * 0.36 + v3((0, 0, 0.03)), (0.05, 0.04, 0.035), R=Rz(a)), k=0.01)
        br.add(Torus(c + v3((0, 0, 0.5)), 0.17, 0.013), k=0.006)                          # the ring binding the legs
        br.add(Ellipsoid(c + v3((0, 0, 1.04)), (0.27, 0.27, 0.12)), k=0.02)              # the bowl, wide and deep
        br.add(Torus(c + v3((0, 0, 1.1)), 0.26, 0.022), k=0.01)                           # its rolled rim
        br.sub(Ellipsoid(c + v3((0, 0, 1.12)), (0.23, 0.23, 0.09)), k=0.01)
    ground_cut(br)
    out.append(("Braziers", br, fine(0.005, 0.01), "bronze"))
    cg = Field("Coals")
    for sy in (-1, 1):
        cg.add(Ellipsoid((-0.15, sy * (TY + 0.1), 1.08), (0.21, 0.21, 0.06), **wob(25.0, 0.008, seed + 5 + sy)))
    out.append(("Coals", cg, fine(0.005, 0.01), "glow_fire"))
    bn = Field("Banners")                                                                 # red banners down the towers' fronts
    B0, B1 = 0.95, 2.08
    for sy in (-1, 1):
        def banner_fn(P, cy=sy * TY):
            x, y, z = P[:, 0], P[:, 1] - F32(cy), P[:, 2]
            face = F32(TX - TS) + F32(BAT) * z - F32(0.05)
            wave = F32(0.015) * np.sin(z * F32(8.0) + y * F32(3.0))
            half = np.where(z < F32(B0 + 0.22), F32(0.22) - (F32(B0 + 0.22) - z) * F32(1.0), F32(0.22))
            return np.maximum.reduce([np.abs(x - (face + wave)) - F32(0.014), np.abs(y) - half, z - F32(B1), F32(B0) - z]).astype(F32)
        bn.add(Func(banner_fn, (TX - TS - 0.2, sy * TY - 0.3, B0 - 0.05), (TX - TS + 0.12, sy * TY + 0.3, B1 + 0.05)))
        bn.add(RoundCone((TX - TS + BAT * B1 - 0.06, sy * TY - 0.3, B1 + 0.02), (TX - TS + BAT * B1 - 0.06, sy * TY + 0.3, B1 + 0.02),
                         0.022, 0.022), k=0.004, label=6)                                    # the pole it hangs from
        def wreath(P, cy=sy * TY):
            r = np.sqrt((P[:, 1] - F32(cy)) ** 2 + (P[:, 2] - F32(1.62)) ** 2)
            return (np.abs(r - F32(0.11)) - F32(0.022)).astype(F32)
        bn.paint(Func(wreath, (TX - TS - 0.3, sy * TY - 0.3, 1.4), (TX - TS + 0.2, sy * TY + 0.3, 1.85)), 5)
        bn.paint(RoundBox((TX - TS, sy * TY, B1 - 0.08), (0.2, 0.3, 0.025)), 5)
        bn.paint(RoundBox((TX - TS, sy * TY, B0 + 0.32), (0.2, 0.3, 0.018)), 5)
    out.append(("Banners", bn, fine(0.005, 0.01), "banner"))
    dk = Field("Dark")                                                                    # the slits' darkness, set back in them
    for sy in (-1, 1):
        cy = sy * TY
        dk.add(RoundBox((TX - TS + BAT * 2.27 + 0.07, cy, 2.27), (0.02, 0.03, 0.1), 0.006))
        for z in (1.05, 1.8):
            dk.add(RoundBox((TX - 0.15, cy + sy * (TS - BAT * z - 0.07), z), (0.03, 0.02, 0.11), 0.006))
    out.append(("Dark", dk, fine(0.006, 0.012), "dark"))
    # inside: town houses, the temple front behind them
    for i, (hx_, hy_, c, yaw) in enumerate(((0.55, 0.42, (3.0, -2.4), 0.2), (0.6, 0.45, (3.2, 2.5), -0.25), (0.5, 0.4, (2.6, 4.4), 0.1),
                                            (0.48, 0.38, (2.5, -4.3), -0.1))):
        town_house(out, "House%d" % i, c, hx_, hy_, 0.75 + 0.1 * (i % 2), yaw - math.pi / 2, seed + 10 + i)
    tp = Field("Temple")
    cx = 4.4
    top = stylobate_at(tp, cx, 0.0, 0.62, 0.92, 3, 0.08, 0.09)
    CXc = cx - 0.44
    for j in range(4):
        y = -0.72 + 0.48 * j
        tp.add(doric_shaft(tp, (CXc, y), top, 1.62, 0.105, 0.09, n=14, depth=0.008), k=0.006)
        doric_capital(tp, (CXc, y), 1.62, 0.09, k=0.006)
    ztop = 1.62 + 0.12 * 0.09 / 0.26 + 0.09 * 0.09 / 0.26
    tp.add(RoundBox((cx + 0.06, 0, ztop + 0.1), (0.62, 0.88, 0.1), 0.01), k=0.004)                    # architrave and frieze
    for j in range(9):                                                                                # its triglyphs
        y = -0.8 + 0.2 * j
        tp.add(RoundBox((cx - 0.565, y, ztop + 0.14), (0.012, 0.03, 0.05), 0.004), k=0.002)
    zr = ztop + 0.2
    def ped(P):
        return np.maximum.reduce([np.abs(P[:, 1]) * F32(0.36) + (P[:, 2] - F32(zr)) - F32(0.34), F32(zr) - P[:, 2],
                                  np.abs(P[:, 0] - F32(cx - 0.5)) - F32(0.06)]).astype(F32)
    tp.add(Func(ped, (cx - 0.7, -1.2, zr - 0.1), (cx - 0.3, 1.2, zr + 0.45)), k=0.004)
    tp.sub(Func(lambda P: np.maximum.reduce([np.abs(P[:, 1]) * F32(0.36) + (P[:, 2] - F32(zr + 0.04)) - F32(0.24),
                                             F32(zr + 0.04) - P[:, 2], np.abs(P[:, 0] - F32(cx - 0.56)) - F32(0.02)]).astype(F32),
                (cx - 0.7, -1.0, zr), (cx - 0.4, 1.0, zr + 0.35)), k=0.002)                          # the tympanum, sunk
    tp.add(RoundBox((cx + 0.22, 0, (top + ztop) / 2), (0.38, 0.6, (ztop - top) / 2), 0.01), k=0.0)  # the cella behind
    tp.sub(RoundBox((cx - 0.16, 0, top + 0.45), (0.04, 0.2, 0.45), 0.01), k=0.004)                  # its doorway
    tp.paint(Func(lambda P: (P[:, 2] - F32(0.3)).astype(F32), (cx - 2, -2, -0.1), (cx + 2, 2, 3)), 7)
    tr = Field("TempleRoof")
    tr.add(gable((cx + 0.06, 0), 0.6, 0.95, zr - 0.01, zr + 0.33, axis="x"))
    tr.ops[-1][1].disp = lambda P: (F32(0.01) * np.abs(np.sin(P[:, 1] * F32(32)))).astype(F32)
    tr.ops[-1][1].disp_amp = 0.012
    ground_cut(tp)
    out.append(("Temple", tp, fine(0.008, 0.016), "marble"))
    out.append(("TempleRoof", tr, fine(0.008, 0.016), "tiles"))
    yard = Field("Yard")
    yard.add(RoundBox((2.4, 0, -0.03), (1.4, 0.9, 0.07), 0.04, **wob(4.0, 0.006, seed + 40)))
    yard.add(RoundBox((0.8, 0, -0.03), (0.75, 0.64, 0.07), 0.04, **wob(4.0, 0.006, seed + 41)), k=0.1)
    cut_below(yard, -0.02, 1.8, 0, 2.6, 1.2)
    out.append(("Yard", yard, fine(0.012, 0.024), "flags"))
    return out


def stylobate_at(f, cx, cy, hx, hy, steps=3, step_h=0.09, step_w=0.12, label=0):
    """stylobate() centred on (cx, cy)."""
    for k in range(steps):
        e = (steps - 1 - k) * step_w
        f.add(RoundBox((cx, cy, step_h * (k + 0.5)), (hx + e, hy + e, step_h / 2), 0.008), k=0.0, label=label)
    return step_h * steps


# ------------------------------------------------------------------------------------------------ the kits
# prop name -> (builder, game-mesh triangle budget), as decor_props.KITS. Tuft and Flowers are direct geometry
# (decor_build).
def KITS(theme):
    common = {
        "Rock_A": (lambda: limestone(1.6, 0.5, 201), 650), "Rock_B": (lambda: limestone(1.0, 0.32, 202, 1), 420),
        "Rock_C": (lambda: limestone(2.2, 0.7, 203, 3), 850),
        "Column_A": (lambda: column(1.0, 0.22, 204, broken=True, drums=3), 900),
        "Column_B": (lambda: column(1.9, 0.22, 205, broken=False, capital=True, drums=5), 1300),
        "Column_C": (lambda: column(0.45, 0.23, 206, broken=True, drums=1), 600),
        "Blocks": (lambda: marble_blocks(207), 1000), "Fallen": (lambda: fallen_column(208), 1000),
        "Cypress_A": (lambda: cypress(3.4, 209), 1100), "Cypress_B": (lambda: cypress(2.5, 210, 0.32), 900),
    }
    if theme == "olive":
        return dict(common, **{
            "Olive_A": (lambda: olive(1.9, 221), 2200), "Olive_B": (lambda: olive(1.6, 222), 2000),
            "Olive_C": (lambda: olive(1.2, 223, young=True), 1300),
            "Herb_A": (lambda: herb(0.55, 0.22, 224), 500), "Herb_B": (lambda: herb(0.4, 0.18, 225), 380),
            "Bush": (lambda: bush(0.8, 0.5, 226, "maquis", "flower_pink"), 800),
            "Wall": (lambda: terrace_wall(2.2, 0.42, 227), 1300), "Amphorae": (lambda: amphorae(228), 1300),
            "Temple": (lambda: ruined_temple(229), 5200), "Farm": (lambda: farmhouse(230), 4400), "Press": (lambda: olive_press(231), 2600),
        })
    if theme == "coast":
        return dict(common, **{
            "Pine_A": (lambda: stone_pine(3.6, 241), 1800), "Pine_B": (lambda: stone_pine(3.0, 242, twin=True), 2000),
            "Pine_C": (lambda: stone_pine(2.4, 243), 1300),
            "Maquis_A": (lambda: bush(0.9, 0.5, 244), 700), "Maquis_B": (lambda: bush(0.65, 0.4, 245, "maquis", "flower_pink"), 700),
            "Herb_A": (lambda: herb(0.5, 0.2, 246), 450), "Amphorae": (lambda: amphorae(247), 1300),
            "Aqueduct": (lambda: aqueduct(248, n_arch=1, span=2.4, pier=0.55, H=2.4, broken=True), 1500),
            "Aqueduct_Long": (lambda: aqueduct(252), 3200), "Bridge": (lambda: bridge(249), 1600),
            "Lighthouse": (lambda: lighthouse(250), 2600), "Boat": (lambda: boat(251), 1600),
        })
    if theme == "acropolis":
        return dict(common, **{
            "Olive_A": (lambda: olive(1.8, 261), 2100), "Olive_B": (lambda: olive(1.3, 262, young=True), 1300),
            "Herb_A": (lambda: herb(0.5, 0.2, 263), 450), "Maquis_A": (lambda: bush(0.75, 0.42, 264), 650),
            "Statue": (lambda: statue(265), 2200), "Lion": (lambda: lion(266), 1800),
            "Temple": (lambda: great_temple(267), 7600), "Theatre": (lambda: theatre(268), 4200), "Altar": (lambda: altar(269), 1500),
        })
    if theme == "classical_city":
        return {"City": (lambda: classical_city(271), 16000)}
    raise KeyError(theme)
