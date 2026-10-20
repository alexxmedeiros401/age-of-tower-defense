"""HQ Iron Age map props, sculpted as distance fields like decor_props and decor_bronze (same conventions: every builder
returns its parts [(part name, Field, voxel, material key)], built at the origin, Z up, ground at z = 0; KITS lists each
theme's props and their game-mesh triangle budgets; decor_build.materials resolves the material keys).

Highland Ford: Scots pines, birches, heather, gorse in flower, bracken, mossy granite boulders, standing stones, reeds
and rushes on the stream banks; a broch (a round dry-stone tower, broken at the top), a thatched roundhouse with a stone
wall and a stone circle.
Ember Forge: charred dead trees, rust-stained ironstone, slag heaps, heaps of bog-iron ore, stacked cordwood, charcoal
clamps; a bloomery (two clay shaft furnaces glowing at the mouth, a leather bellows, slag tapped out at their feet) and
a smithy (an open timber shed over a stone hearth, an anvil, a quench trough).
Mirefen Bog: grey willows, alders, dead silver snags, reeds, soft rushes, cotton grass, sphagnum hummocks, black bog
oak, stacked peat; a crannog (a roundhouse on a timber platform over a peaty pool, a gangway, a dugout canoe) and a
carved wooden idol with quartz eyes in a ring of stakes.
The Iron city at the end of every Iron Age road (the gate of a hill fort: earth ramparts under a palisade, two timber
gate towers with thatched roofs and a walkway between them, iron-strapped doors, fire baskets, roundhouses and a
granary inside) is its own kit ("iron_city", iron_city.glb).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Chain, Plane, Func, rot_from_axes, v3, NOISE, euler
import decor_props as DP
from decor_props import vx, wob, convex, rock, dead_tree, stump, log
from decor_bronze import fine, unit, frame, ground_cut, cut_above, cut_below, place, place_parts, mound, convex_w, walls_box, reeds

F32 = np.float32


# ------------------------------------------------------------------------------------------------ helpers
def Rz(a):
    """Turn about Z by a (radians)."""
    return euler(0.0, 0.0, a)


def R_xz(x, zhint):
    """Rotation whose local X is exactly x and local Z as close to zhint as it can be."""
    x = unit(x)
    z = v3(zhint) - x * float(np.dot(v3(zhint), x))
    if np.linalg.norm(z) < 1e-6:
        z = np.cross(x, v3((0, 1, 0)))
    z = unit(z)
    return np.stack([x, np.cross(z, x), z], axis=1)


def at_height(pts, z):
    """The point of a polyline (rising in Z) at height z."""
    P = [v3(p) for p in pts]
    for a, b in zip(P[:-1], P[1:]):
        if a[2] <= z <= b[2]:
            t = (z - a[2]) / max(b[2] - a[2], 1e-9)
            return a + (b - a) * t
    return P[-1] if z > P[-1][2] else P[0]


def cone(c, zb, zt, rb, rt=0.0, n_wob=None):
    """A cone (truncated when rt > 0) on a flat base: axis Z through c, base at zb (radius rb), top at zt (radius rt).
    The distance is exact near the sloping side (where it matters for meshing)."""
    cx, cy = float(c[0]), float(c[1])
    H = zt - zb
    L = math.hypot(H, rb - rt)
    nq, nz = H / L, (rb - rt) / L

    def fn(P):
        q = np.sqrt((P[:, 0] - cx) ** 2 + (P[:, 1] - cy) ** 2)
        z = P[:, 2]
        d = (q - rb) * nq + (z - zb) * nz
        d = np.maximum(d, zb - z)
        if rt > 0:
            d = np.maximum(d, z - zt)
        return d.astype(F32)
    e = rb + 0.05
    kw = n_wob or {}
    return Func(fn, (cx - e, cy - e, zb - 0.05), (cx + e, cy + e, zt + 0.05), **kw)


def gable(c, half_len, half_w, z_eave, z_ridge, axis="y", over=0.0):
    """A solid gabled (ridged) roof block: the ridge runs along `axis` at z_ridge over c, the eaves at z_eave, half_w
    out each side; flat underneath."""
    cx, cy = float(c[0]), float(c[1])
    s = (z_ridge - z_eave) / half_w
    if axis == "y":
        planes = [((cx, cy, z_ridge), (s, 0, 1)), ((cx, cy, z_ridge), (-s, 0, 1)), ((cx, cy + half_len, 0), (0, 1, 0)),
                  ((cx, cy - half_len, 0), (0, -1, 0)), ((cx, cy, z_eave - over), (0, 0, -1))]
        lo, hi = (cx - half_w - 0.1, cy - half_len - 0.1, z_eave - over - 0.1), (cx + half_w + 0.1, cy + half_len + 0.1, z_ridge + 0.1)
    else:
        planes = [((cx, cy, z_ridge), (0, s, 1)), ((cx, cy, z_ridge), (0, -s, 1)), ((cx + half_len, cy, 0), (1, 0, 0)),
                  ((cx - half_len, cy, 0), (-1, 0, 0)), ((cx, cy, z_eave - over), (0, 0, -1))]
        lo, hi = (cx - half_len - 0.1, cy - half_w - 0.1, z_eave - over - 0.1), (cx + half_len + 0.1, cy + half_w + 0.1, z_ridge + 0.1)
    return convex(planes, lo, hi)


def pyramid_roof(c, half, z_eave, z_apex):
    """A four-sided pyramid roof over a square tower (half = half its width at the eaves)."""
    cx, cy = float(c[0]), float(c[1])
    s = (z_apex - z_eave) / half
    planes = [((cx, cy, z_apex), (s, 0, 1)), ((cx, cy, z_apex), (-s, 0, 1)), ((cx, cy, z_apex), (0, s, 1)),
              ((cx, cy, z_apex), (0, -s, 1)), ((cx, cy, z_eave), (0, 0, -1))]
    return convex(planes, (cx - half - 0.1, cy - half - 0.1, z_eave - 0.1), (cx + half + 0.1, cy + half + 0.1, z_apex + 0.1))


def plank_x(f, c, half, label=10, k=0.004, seed=0):
    """A plank or beam lying along X (its grain label 10)."""
    f.add(RoundBox(c, half, min(half[1], half[2]) * 0.35, **wob(9.0, 0.002, seed)), k=k, label=label)


def post(f, a, b, ra, rb=None, label=11, k=0.0, pointed=False):
    """An upright post (grain along Z: label 11); pointed=True sharpens its top."""
    rb = ra if rb is None else rb
    f.add(RoundCone(a, b, ra, rb), k=k, label=label)
    if pointed:
        b = v3(b)
        f.add(RoundCone(b, b + v3((0, 0, rb * 2.4)), rb * 0.98, rb * 0.12), k=rb * 0.3, label=label)


# ------------------------------------------------------------------------------------------------ highland plants
def scots_pine(h=3.0, seed=0, lean=0.05):
    """A Scots pine: a tall trunk, scaly and grey-brown low down and orange higher up, a few branches near the top and a
    flat-topped, broken crown of needle pads."""
    rng = np.random.default_rng(seed)
    s = h / 3.0
    a0 = rng.uniform(0, 2 * math.pi)
    lv = v3((math.cos(a0), math.sin(a0), 0.0)) * lean * h
    f = Field("Trunk")
    pts = [v3((0, 0, -0.1)), v3((0, 0, h * 0.22)) + lv * 0.15,
           v3((0, 0, h * 0.5)) + lv * 0.5 + v3((rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), 0.0)) * s,
           v3((0, 0, h * 0.84)) + lv]
    f.add(Chain(pts, [0.13 * s, 0.11 * s, 0.08 * s, 0.035 * s], k=0.02, **wob(3.0, 0.01 * s, seed)))
    for i in range(4):                                    # root flare
        a = 2 * math.pi * i / 4 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((0, 0, 0.14 * s), (0.28 * s * math.cos(a), 0.28 * s * math.sin(a), -0.04), 0.07 * s, 0.025 * s), k=0.06 * s)
    pads = []
    nb = 5
    for i in range(nb):
        t = 0.56 + 0.26 * i / (nb - 1) + rng.uniform(-0.02, 0.02)
        p0 = at_height(pts, h * t)
        a = a0 + 0.9 + i * 2.4 + rng.uniform(-0.35, 0.35)
        L = h * rng.uniform(0.17, 0.27) * (1.15 - 0.5 * i / (nb - 1))
        d = unit(v3((math.cos(a), math.sin(a), rng.uniform(0.15, 0.4))))
        p2 = p0 + d * L
        p1 = p0 + d * L * 0.5 + v3((0, 0, -0.04 * s))
        f.add(Chain([p0, p1, p2], [0.045 * s, 0.03 * s, 0.016 * s], k=0.01), k=0.03 * s)
        pads.append((p2 + v3((0, 0, 0.07 * s)), rng.uniform(0.27, 0.36) * s * (1.0 if i < nb - 1 else 0.85)))
    pads.append((pts[-1] + v3((0, 0, 0.1 * s)), 0.33 * s))
    c = Field("Crown")
    for j, (cc, r) in enumerate(pads):
        for k in range(4):
            ofs = v3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.25, 0.3))) * r * 0.55
            rr = r * rng.uniform(0.55, 0.8)
            c.add(Ellipsoid(cc + ofs, (rr, rr * rng.uniform(0.85, 1.0), rr * 0.48),
                            **wob(6.0 / max(r, 0.2), 0.045 * r + 0.015, seed * 50 + j * 5 + k)), k=0.09 * s)
    return [("Trunk", f, fine(0.008, 0.016), "scots_bark"), ("Crown", c, vx(h), "needles")]


def birch(h=2.6, seed=0, twin=False):
    """A silver birch: a slender white trunk (two from one root when twin), thin branches arching up, an airy oval crown
    of small leaf clumps."""
    rng = np.random.default_rng(seed)
    s = h / 2.6
    f = Field("Trunk")
    c = Field("Leaves")
    stems = [rng.uniform(0, 2 * math.pi)] if not twin else [rng.uniform(0, 2 * math.pi)] * 2
    if twin:
        stems[1] = stems[0] + math.pi + rng.uniform(-0.3, 0.3)
    for si, a in enumerate(stems):
        lean = (0.05 if not twin else 0.13) * h
        d = v3((math.cos(a), math.sin(a), 0.0))
        hh = h * (1.0 if si == 0 else 0.86)
        pts = [v3((0, 0, -0.08)) + d * (0.0 if not twin else 0.03), v3((0, 0, 0.25 * hh)) + d * lean * 0.2,
               v3((0, 0, 0.55 * hh)) + d * lean * 0.55 + v3((rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), 0.0)),
               v3((0, 0, 0.94 * hh)) + d * lean]
        rad = [0.075 * s, 0.06 * s, 0.044 * s, 0.013 * s] if not twin else [0.062 * s, 0.05 * s, 0.037 * s, 0.012 * s]
        f.add(Chain(pts, rad, k=0.015, **wob(4.0, 0.005 * s, seed + si)), k=0.05 * s)
        ctr = v3((0, 0, 0.66 * hh)) + d * lean * 0.75
        for j in range(7):                                # thin branches arching up and out
            t = rng.uniform(0.4, 0.85)
            p0 = at_height(pts, hh * t)
            b = a + rng.uniform(-1.6, 1.6) if twin else rng.uniform(0, 2 * math.pi)
            out = v3((math.cos(b), math.sin(b), 0.0))
            L = hh * rng.uniform(0.18, 0.3) * (1.2 - t * 0.6)
            p1 = p0 + out * L * 0.55 + v3((0, 0, L * 0.35))
            p2 = p1 + out * L * 0.4 + v3((0, 0, L * 0.3))
            f.add(Chain([p0, p1, p2], [0.02 * s, 0.012 * s, 0.006 * s], k=0.004), k=0.012 * s)
            for q in (p1, p2):
                r = s * rng.uniform(0.13, 0.18)
                c.add(Ellipsoid(q + v3((0, 0, 0.04 * s)), (r, r * 0.9, r * 0.8), **wob(12.0 / s, 0.03 * s, seed * 70 + si * 20 + j)), k=0.05 * s)
        for j in range(16):                               # the oval crown
            u = rng.normal(size=3)
            u = u / np.linalg.norm(u) * rng.uniform(0.55, 1.0) ** 0.5
            q = ctr + v3((u[0] * 0.5 * s, u[1] * 0.5 * s, u[2] * 0.33 * hh))
            r = s * rng.uniform(0.13, 0.2)
            c.add(Ellipsoid(q, (r, r * 0.9, r * 0.85), **wob(12.0 / s, 0.03 * s, seed * 90 + si * 30 + j)), k=0.05 * s)
    return [("Trunk", f, fine(0.006, 0.012), "birch_bark"), ("Leaves", c, fine(0.011, 0.022), "birch_leaves")]


def heather(w=0.9, h=0.28, seed=0):
    """A heather clump: a low cushion of wiry shoots, knobbly, purple on top."""
    rng = np.random.default_rng(seed)
    f = Field("Heather")
    f.add(Ellipsoid((0, 0, h * 0.2), (w * 0.42, w * 0.38, h * 0.75), **wob(7.0 / w, 0.035 * w, seed)))
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi)
        rr = w * 0.36 * math.sqrt(rng.uniform(0, 1))
        r = w * rng.uniform(0.1, 0.16)
        f.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a), h * rng.uniform(0.3, 0.65)), (r, r, r * 0.8),
                        **wob(16.0 / w, 0.03 * w, seed * 20 + i)), k=0.05 * w)
    f.inter(Plane((0, 0, -0.03), (0, 0, -1)))
    return [("Heather", f, fine(0.006, 0.012), "heather")]


def gorse(w=0.95, h=0.62, seed=0):
    """A gorse bush in flower: dense spiny dark green clumps, scattered with yellow blossom."""
    rng = np.random.default_rng(seed)
    f = Field("Gorse")
    f.add(Ellipsoid((0, 0, h * 0.42), (w * 0.32, w * 0.34, h * 0.5), **wob(14.0 / w, 0.045 * w, seed)))
    for i in range(10):
        a = 2 * math.pi * i / 10 + rng.uniform(-0.3, 0.3)
        rr = w * 0.3 * rng.uniform(0.4, 1.0)
        r = w * rng.uniform(0.16, 0.23)
        f.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a) * 1.1, h * rng.uniform(0.35, 0.72)), (r, r, r * 1.08),
                        **wob(14.0 / w, 0.05 * w, seed * 10 + i)), k=0.06 * w)
    for i in range(34):                                   # blossom
        a = rng.uniform(0, 2 * math.pi)
        el = rng.uniform(0.15, 1.2)
        q = v3((math.cos(a) * math.cos(el) * w * 0.48, math.sin(a) * math.cos(el) * w * 0.5, h * 0.42 + math.sin(el) * h * 0.58))
        f.paint(Sphere(q, 0.06 * w), 1)
    f.inter(Plane((0, 0, -0.03), (0, 0, -1)))
    return [("Gorse", f, fine(0.006, 0.012), "gorse")]


def bracken(seed=0, n=7, h=0.75):
    """Bracken: fronds rising from the ground and arching over, each a stalk with pairs of pinnae shrinking to the
    tip."""
    rng = np.random.default_rng(seed)
    f = Field("Fronds")
    th = max(0.0055, fine(0.005, 0.01) * 0.65)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        hz = v3((math.cos(a), math.sin(a), 0.0))
        L = h * rng.uniform(0.75, 1.1)
        K = 8
        T = np.linspace(0, 1, K)
        P = [v3((0.05 * math.cos(a), 0.05 * math.sin(a), -0.03)) + hz * (L * 0.7 * t ** 1.4) + v3((0, 0, L * 0.82 * math.sin(t * math.pi * 0.62)))
             for t in T]
        f.add(Chain(P, [0.011 * (1 - 0.6 * t) for t in T], k=0.004))
        for j in range(1, K - 1):
            t = T[j]
            if t < 0.28:
                continue
            tg, sd, nn = frame(P[j + 1] - P[j - 1])
            Lp = 0.14 * L / 0.75 * (1.0 - (t - 0.28) / 0.85)
            for side in (-1, 1):
                dp = unit(sd * side * 0.9 + tg * 0.35 - nn * 0.12)
                f.add(Ellipsoid(P[j] + dp * Lp * 0.5, (Lp * 0.5, 0.024, th), R=R_xz(dp, nn)), k=0.004)
        f.add(Ellipsoid(P[-1], (0.035, 0.016, th), R=R_xz(unit(P[-1] - P[-2]), v3((0, 0, 1)))), k=0.004)
    return [("Fronds", f, fine(0.005, 0.01), "bracken")]


def rushes(seed=0, n=30, h=0.7):
    """Soft rushes: a dense clump of thin dark green stems fanning out of a tussock, brown flower tufts on a few."""
    rng = np.random.default_rng(seed)
    st, hd, tu = Field("Stems"), Field("Heads"), Field("Tussock")
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, 0.09)
        b0 = v3((rr * math.cos(a), rr * math.sin(a), 0.0))
        lean = rng.uniform(0.08, 0.42)
        hh = h * rng.uniform(0.6, 1.0)
        tip = b0 + v3((math.cos(a) * lean * hh, math.sin(a) * lean * hh, hh * (1 - 0.15 * lean)))
        mid = b0 + (tip - b0) * 0.5 - v3((math.cos(a), math.sin(a), 0)) * 0.02 * lean
        st.add(Chain([b0, mid, tip], [0.009, 0.007, 0.0025], k=0.003))
        if i % 6 == 0:
            q = b0 + (tip - b0) * 0.62 + v3((math.cos(a + 1.5), math.sin(a + 1.5), 0)) * 0.012
            hd.add(Ellipsoid(q, (0.022, 0.022, 0.035), **wob(40.0, 0.006, seed + i)))
    tu.add(Ellipsoid((0, 0, -0.02), (0.19, 0.17, 0.09), **wob(6.0, 0.015, seed)))
    ground_cut(tu)
    return [("Stems", st, fine(0.004, 0.008), "rushes"), ("Heads", hd, fine(0.005, 0.01), "cattail"),
            ("Tussock", tu, fine(0.01, 0.018), "mud")]


def menhir(h=1.6, w=0.55, seed=0, lean=0.0):
    """A standing stone: a rough slab, broader than deep, its top worn blunt, chipped facets, lichen and moss."""
    rng = np.random.default_rng(seed)
    f = Field("Stone")
    R = rot_from_axes(z_axis=(lean, 0.0, 1.0))
    f.add(RoundBox(v3((lean * h * 0.45, 0, h * 0.45)), (w * 0.5, w * 0.3, h * 0.58), 0.07, R=R, **wob(2.6, 0.03, seed)))
    for sx in (-1, 1):                                    # the top tapers
        f.inter(Plane(v3((sx * w * 0.42, 0, h * 0.7)) + v3((lean * h * 0.7, 0, 0)), (sx, 0, 0.45 + rng.uniform(-0.15, 0.15))), k=0.05)
    for i in range(6):                                    # chipped facets
        nrm = unit(v3((rng.normal(), rng.normal() * 1.4, abs(rng.normal()) * 0.6)))
        ext = v3((w * 0.5 * nrm[0], w * 0.3 * nrm[1], h * 0.5 + h * 0.5 * nrm[2]))
        f.inter(Plane(ext * 0.92, nrm), k=0.03)
    f.inter(Plane((0, 0, -0.06), (0, 0, -1)))
    return [("Stone", f, vx(max(h, 1.0)) * 0.75, "rock")]


def fallen_stone(L=1.5, seed=0):
    """A standing stone that has fallen: lying on its side, half sunk in the turf."""
    rng = np.random.default_rng(seed)
    f = Field("Stone")
    R = R_xz(v3((1, 0.1, 0.05)), v3((0, -0.3, 1)))
    f.add(RoundBox((0, 0, 0.08), (L * 0.5, 0.27, 0.17), 0.07, R=R, **wob(2.6, 0.03, seed)))
    for i in range(4):
        nrm = unit(v3((rng.normal() * 0.6, rng.normal(), abs(rng.normal()) + 0.3)))
        f.inter(Plane(v3((L * 0.45 * nrm[0], 0.27 * nrm[1], 0.08 + 0.17 * nrm[2])) * 0.95, nrm), k=0.03)
    f.inter(Plane((0, 0, -0.04), (0, 0, -1)))
    return [("Stone", f, vx(L) * 0.75, "rock")]


def stone_circle(seed=0):
    """A ring of seven standing stones of different heights on a low grassy platform, their broad faces turned to the
    centre; a recumbent stone lying between the two tallest, a fallen one across the ring."""
    rng = np.random.default_rng(seed)
    out = []
    n = 7
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.12, 0.12)
        x, y = 1.65 * math.cos(a), 1.35 * math.sin(a)
        if i == 2:
            continue                                     # (the fallen one's place)
        hh = [1.55, 1.25, 0.0, 1.05, 1.15, 1.4, 1.75][i] * rng.uniform(0.92, 1.05)
        st = menhir(hh, 0.5 + hh * 0.08, seed * 10 + i, lean=rng.uniform(-0.08, 0.08))
        place_parts(out, st, (x, y, 0.0), Rz(a + math.pi / 2 + rng.uniform(-0.2, 0.2)))
    a2 = 2 * math.pi * 2 / n
    place_parts(out, fallen_stone(1.4, seed + 3), (1.2 * math.cos(a2), 1.0 * math.sin(a2), 0.0), Rz(a2 + 0.5))
    a6 = (2 * math.pi * 6 / n + 2 * math.pi * 5 / n) / 2 + 0.15
    rec = Field("Recumbent")
    rec.add(RoundBox((0, 0, 0.25), (0.62, 0.22, 0.3), 0.08, **wob(2.5, 0.025, seed + 9)))
    rec.inter(Plane((0, 0, -0.05), (0, 0, -1)))
    place_parts(out, [("Stone", rec, vx(1.2) * 0.75, "rock")], (1.6 * math.cos(a6), 1.3 * math.sin(a6), 0.0), Rz(a6 + math.pi / 2))
    return mound(out, 2.3, 1.95, 0.12, seed)


# ------------------------------------------------------------------------------------------------ highland landmarks
def broch(seed=0):
    """A broch: a round dry-stone tower whose hollow wall curves in like a cooling tower as it rises, the top broken
    away on the front-left with its stones tumbled at the foot; a low lintelled doorway (-Y) with the gallery voids
    stacked above it, a turf skirt."""
    rng = np.random.default_rng(seed)
    out = []
    H, R0, R1, TW = 2.75, 1.32, 0.98, 0.36
    tb = -2.7                                             # where the top is broken away (angle round Z: front-left)

    def prof(z):
        u = np.clip(z / H, 0.0, 1.0)
        return R1 + (R0 - R1) * (1.0 - u) ** 1.7

    def body(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.sqrt(x * x + y * y)
        ro = prof(z)
        th = np.arctan2(y, x)
        dth = np.angle(np.exp(1j * (th - tb)))
        top = H - 0.95 * np.exp(-(dth / 0.75) ** 2) - 0.12 * np.exp(-((dth - 1.2) / 0.3) ** 2)
        top = top + NOISE.fbm(P * 3.0 + 11.0, 2) * 0.09
        d = np.maximum(r - ro, -np.maximum(r - (ro - TW), 0.32 - z))
        d = np.maximum(d, z - top)
        d = np.maximum(d, -0.05 - z)
        return (d * 0.92).astype(F32)

    W = Field("Wall")
    W.add(Func(body, (-R0 - 0.1, -R0 - 0.1, -0.1), (R0 + 0.1, R0 + 0.1, H + 0.15), **wob(3.0, 0.012, seed)))
    W.sub(RoundBox((0, -prof(0.4), 0.36), (0.19, 0.5, 0.36), 0.03))          # the doorway
    W.add(RoundBox((0, -prof(0.8) + 0.03, 0.8), (0.32, 0.12, 0.075), 0.03, **wob(5.0, 0.008, seed + 1)), k=0.01)   # lintel
    for z in (1.3, 1.82):                                 # the voids over the door
        W.sub(RoundBox((0, -prof(z), z), (0.12, 0.45, 0.16), 0.02))
    ground_cut(W, -0.04)
    out.append(("Wall", W, fine(0.0125, 0.024), "drystone"))
    d = Field("Dark")
    d.add(RoundBox((0, -prof(0.4) + TW * 0.55, 0.36), (0.18, 0.05, 0.35), 0.02))
    for z in (1.3, 1.82):
        d.add(RoundBox((0, -prof(z) + TW * 0.6, z), (0.11, 0.04, 0.15), 0.02))
    out.append(("Dark", d, fine(0.01, 0.02), "dark"))
    rb = Field("Rubble")                                  # stones tumbled from the broken top
    for i in range(14):
        a = tb + rng.uniform(-0.75, 0.75)
        rr = R0 + rng.uniform(0.05, 0.75)
        sz = rng.uniform(0.09, 0.17)
        q = v3((rr * math.cos(a), rr * math.sin(a), sz * 0.25))
        rb.add(Ellipsoid(q, (sz * 1.5, sz, sz * 0.6), R=Rz(rng.uniform(0, math.pi)), **wob(9.0, 0.012, seed * 30 + i)), k=0.01)
    ground_cut(rb)
    out.append(("Rubble", rb, fine(0.008, 0.016), "drystone"))
    return mound(out, 1.95, 1.95, 0.14, seed)


def roundhouse(seed=0, wall="drystone", r=1.05, wall_h=0.62, roof_h=1.5, z0=0.0, base=True):
    """An Iron Age roundhouse: a low round wall (dry stone, or daub), a steep conical thatched roof with deep eaves and
    a bound ridge, a porch over a dark doorway (-Y) with timber door posts. z0 lifts it (onto a crannog's platform);
    base=True sets it in a turf mound."""
    out = []
    zt = z0 + wall_h
    Wl = Field("Wall")
    Wl.add(Cylinder((0, 0, z0 + wall_h / 2 - 0.04), r, wall_h + 0.08, rr=0.05, **wob(3.0, 0.012, seed)))
    Wl.sub(RoundBox((0, -r, z0 + 0.34), (0.18, 0.26, 0.36), 0.03))
    for sx in (-1, 1):                                    # the porch's side walls
        Wl.add(RoundBox((sx * 0.31, -r - 0.17, z0 + 0.25), (0.08, 0.22, 0.28), 0.04, **wob(6.0, 0.008, seed + sx)), k=0.03)
    cut_below(Wl, z0 - 0.03, 0, -0.2, r + 0.3, r + 0.6)
    out.append(("Wall", Wl, fine(0.009, 0.018), wall))
    rf = Field("Roof")
    eave = r + 0.34
    rf.add(cone((0, 0), zt - 0.05, zt - 0.05 + roof_h * (eave / (eave - 0.04)), eave, 0.0, wob(3.0, 0.016, seed + 1)))
    rf.inter(Plane((0, 0, zt + roof_h - 0.06), (0, 0, 1)), k=0.04)
    rf.add(gable((0, -r - 0.12), 0.34, 0.42, zt - 0.06, zt + 0.36), k=0.08)      # the porch roof
    rf.add(Cylinder((0, 0, zt + roof_h - 0.1), 0.11, 0.12, rr=0.04), k=0.04, label=5)   # the bound ridge
    for zz, rr in ((0.62, 0.0), (0.8, 0.0)):              # hazel spars pinning the top courses
        z = zt - 0.05 + roof_h * zz
        rad = eave * (1.0 - (z - zt + 0.05) / (roof_h * (eave / (eave - 0.04))))
        rf.add(Torus((0, 0, z), rad + 0.006, 0.014), k=0.006, label=5)
    out.append(("Roof", rf, fine(0.0105, 0.021), "thatch"))
    wd = Field("Door")
    for sx in (-1, 1):
        post(wd, (sx * 0.21, -r - 0.36, z0 - 0.02), (sx * 0.21, -r - 0.36, zt - 0.06), 0.04, 0.036)
    plank_x(wd, (0, -r - 0.36, zt - 0.1), (0.3, 0.05, 0.045))                      # the lintel, under the porch roof
    out.append(("Door", wd, fine(0.006, 0.012), "timber"))
    dk = Field("Dark")
    dk.add(RoundBox((0, -r + 0.1, z0 + 0.33), (0.17, 0.05, 0.34), 0.03))
    out.append(("Dark", dk, fine(0.009, 0.018), "dark"))
    if base:
        mound(out, r + 0.75, r + 0.75, 0.12, seed)
    return out


# ------------------------------------------------------------------------------------------------ forge props
def slag_heap(w=1.4, h=0.45, seed=0):
    """A slag heap: tapped iron slag dumped in a heap, lobes and runs of black glassy slag with ropey flows down the
    sides, broken lumps round the foot."""
    rng = np.random.default_rng(seed)
    f = Field("Slag")
    f.add(Ellipsoid((0, 0, 0), (w * 0.45, w * 0.4, h), **wob(3.0 / w, 0.06 * w, seed)))
    for i in range(7):
        a = rng.uniform(0, 2 * math.pi)
        rr = w * rng.uniform(0.12, 0.38)
        r = w * rng.uniform(0.12, 0.19)
        f.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a), h * rng.uniform(0.25, 0.6)), (r, r * 0.8, r * 0.42), R=Rz(rng.uniform(0, 3)),
                        **wob(8.0 / w, 0.02 * w, seed * 10 + i)), k=0.06 * w)
    for i in range(5):
        a = 2 * math.pi * i / 5 + rng.uniform(-0.3, 0.3)
        p0 = v3((0.12 * w * math.cos(a), 0.12 * w * math.sin(a), h * 0.8))
        p1 = v3((0.46 * w * math.cos(a), 0.42 * w * math.sin(a), 0.05))
        f.add(RoundCone(p0, p1, 0.07 * w, 0.05 * w, **wob(10.0 / w, 0.012 * w, seed * 20 + i)), k=0.05 * w)
    for i in range(7):
        a = rng.uniform(0, 2 * math.pi)
        rr = w * rng.uniform(0.5, 0.68)
        r = w * rng.uniform(0.05, 0.09)
        f.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a), r * 0.3), (r, r * 0.8, r * 0.55), R=Rz(rng.uniform(0, 3)),
                        **wob(20.0 / w, 0.01 * w, seed * 40 + i)), k=0.01)
    ground_cut(f, -0.02)
    return [("Slag", f, fine(0.008, 0.016), "slag")]


def ore_heap(w=1.0, h=0.42, seed=0):
    """A heap of roasted bog-iron ore: rusty knobbly nodules piled in a cone."""
    rng = np.random.default_rng(seed)
    f = Field("Ore")
    f.add(Ellipsoid((0, 0, -h * 0.15), (w * 0.4, w * 0.36, h * 0.92), **wob(4.0 / w, 0.03 * w, seed)))
    for i in range(42):
        a = rng.uniform(0, 2 * math.pi)
        u = rng.uniform(0.0, 1.0)
        rr = w * 0.4 * math.sqrt(u)
        z = h * 0.77 * (1.0 - u ** 0.9) * 0.95
        r = w * rng.uniform(0.045, 0.085)
        f.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a) * 0.9, z), (r, r * 0.9, r * 0.8), **wob(30.0 / w, 0.008 * w, seed * 50 + i)), k=0.012)
    ground_cut(f)
    return [("Ore", f, fine(0.006, 0.012), "iron_ore")]


def cordwood(seed=0):
    """Split logs stacked for the charcoal burners: three rows between two pairs of stakes."""
    rng = np.random.default_rng(seed)
    f = Field("Logs")
    r, L = 0.075, 1.1
    for k, n in enumerate((5, 4, 3)):
        for i in range(n):
            y = (i - (n - 1) / 2) * r * 2.05
            z = r * 0.95 + k * r * 1.72
            rr = r * rng.uniform(0.85, 1.05)
            f.add(Cylinder((rng.uniform(-0.05, 0.05), y, z), rr, L * rng.uniform(0.92, 1.0), rr=0.012,
                           R=rot_from_axes(z_axis=(1.0, rng.uniform(-0.04, 0.04), rng.uniform(-0.02, 0.02))), **wob(8.0, 0.006, seed + k * 9 + i)), k=0.004)
    s = Field("Stakes")
    for sx in (-1, 1):
        for sy in (-1, 1):
            post(s, (sx * (L / 2 + 0.05), sy * 0.42, -0.02), (sx * (L / 2 + 0.07), sy * 0.43, 0.56), 0.03, 0.025, pointed=True)
    ground_cut(f)
    ground_cut(s)
    return [("Logs", f, fine(0.006, 0.012), "logs"), ("Stakes", s, fine(0.005, 0.01), "timber")]


def clamp(seed=0, R=0.85, H=0.55):
    """A charcoal clamp: a dome of turf and earth over the stacked wood, a few smoking vents near the top with embers
    glowing in one, split billets and spilt charcoal round its foot."""
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Clamp")
    f.add(Ellipsoid((0, 0, 0), (R, R * 0.95, H), **wob(3.0, 0.03, seed)))
    vents = []
    for i in range(4):
        a = 2 * math.pi * i / 4 + rng.uniform(-0.4, 0.4)
        el = rng.uniform(0.55, 0.9)
        q = v3((R * math.cos(el) * math.cos(a), R * 0.95 * math.cos(el) * math.sin(a), H * math.sin(el)))
        f.sub(Sphere(q, 0.06), k=0.02)
        vents.append(q)
    ground_cut(f)
    out.append(("Clamp", f, fine(0.009, 0.018), "earth"))
    e = Field("Embers")
    e.add(Sphere(vents[0] * 0.95, 0.045, **wob(30.0, 0.008, seed + 3)))
    out.append(("Embers", e, fine(0.006, 0.012), "glow_fire"))
    dk = Field("Dark")
    for q in vents[1:]:
        dk.add(Sphere(q * 0.96, 0.05))
    out.append(("Dark", dk, fine(0.008, 0.016), "dark"))
    c = Field("Charcoal")
    for i in range(16):
        a = rng.uniform(0, 2 * math.pi)
        rr = R * rng.uniform(1.0, 1.25)
        c.add(RoundBox((rr * math.cos(a), rr * math.sin(a) * 0.95, 0.02), (rng.uniform(0.04, 0.07), 0.025, 0.022), 0.01,
                       R=Rz(rng.uniform(0, 3)), **wob(20.0, 0.004, seed + 30 + i)))
    ground_cut(c)
    out.append(("Charcoal", c, fine(0.005, 0.01), "charcoal"))
    return out


def anvil(f, c, s=1.0):
    """A forged iron anvil (horn toward +X) with its top at c."""
    c = v3(c)
    f.add(RoundBox(c + v3((0, 0, -0.04 * s)), v3((0.14, 0.07, 0.04)) * s, 0.008 * s), k=0.004, label=6)
    f.add(RoundCone(c + v3((0.13 * s, 0, -0.035 * s)), c + v3((0.27 * s, 0, -0.03 * s)), 0.045 * s, 0.008 * s), k=0.01, label=6)
    f.add(RoundBox(c + v3((0, 0, -0.12 * s)), v3((0.07, 0.05, 0.05)) * s, 0.008 * s), k=0.02, label=6)
    f.add(RoundBox(c + v3((0, 0, -0.18 * s)), v3((0.11, 0.08, 0.025)) * s, 0.008 * s), k=0.02, label=6)


def bloomery(seed=0):
    """A bloomery: two clay shaft furnaces, the nearer one burning (its arched tapping mouth glowing, slag run out
    before it), a leather bellows on a board feeding its tuyere, a heap of roasted ore and a basket of charcoal by the
    other; a slag heap behind, all on a trampled earth floor."""
    rng = np.random.default_rng(seed)
    out = []
    cl = Field("Clay")
    gl = Field("Glow")
    dk = Field("Dark")
    furn = [((-0.45, -0.05), 1.3, True), ((0.55, 0.35), 1.05, False)]
    for i, ((x, y), hh, lit) in enumerate(furn):
        cl.add(cone((x, y), -0.05, hh, 0.44, 0.24, wob(5.0, 0.012, seed + i)))
        cl.add(Torus((x, y, hh - 0.02), 0.22, 0.04), k=0.03)                       # the lip
        cl.sub(Cylinder((x, y, hh), 0.16, 0.5))                                    # the shaft
        cl.sub(RoundBox((x, y - 0.42, 0.18), (0.13, 0.2, 0.2), 0.06))             # the arched tapping mouth (-Y)
        cl.paint(Ellipsoid((x, y - 0.38, 0.24), (0.26, 0.14, 0.3)), 5)            # soot round it
        cl.paint(Ellipsoid((x, y - 0.4, 0.02), (0.2, 0.14, 0.06)), 6)             # glaze where the slag ran
        tu = v3((x + 0.37, y - 0.05, 0.3))                                         # the tuyere (+X side)
        cl.add(RoundCone(tu + v3((0.12, 0, 0.02)), tu - v3((0.02, 0, 0)), 0.05, 0.07), k=0.03)
        if lit:
            gl.add(Ellipsoid((x, y - 0.3, 0.16), (0.11, 0.08, 0.13), **wob(20.0, 0.01, seed + 5)))
            gl.add(Sphere((x, y, hh - 0.05), 0.13, **wob(18.0, 0.015, seed + 6)))
        else:
            dk.add(RoundBox((x, y - 0.3, 0.17), (0.11, 0.04, 0.16), 0.04))
            dk.add(Cylinder((x, y, hh - 0.08), 0.15, 0.06))
    ground_cut(cl, -0.04)
    out.append(("Clay", cl, fine(0.008, 0.016), "furnace_clay"))
    out.append(("Glow", gl, fine(0.006, 0.012), "glow_fire"))
    out.append(("Dark", dk, fine(0.008, 0.016), "dark"))
    sl = Field("Slag")                                    # slag run out of the lit furnace, a heap behind
    x, y = furn[0][0]
    sl.add(Ellipsoid((x, y - 0.66, 0.0), (0.24, 0.2, 0.06), **wob(10.0, 0.012, seed + 7)))
    for i in range(4):
        sl.add(Ellipsoid((x + rng.uniform(-0.2, 0.2), y - 0.78 + rng.uniform(-0.1, 0.1), 0.02), (0.07, 0.05, 0.04), **wob(20.0, 0.006, seed + 8 + i)), k=0.02)
    for i in range(6):
        a = rng.uniform(0, 2 * math.pi)
        sl.add(Ellipsoid((-0.1 + 0.35 * math.cos(a), 1.05 + 0.25 * math.sin(a), 0.05), (0.2, 0.16, 0.16), **wob(8.0, 0.015, seed + 20 + i)), k=0.08)
    ground_cut(sl)
    out.append(("Slag", sl, fine(0.008, 0.016), "slag"))
    lb = Field("Bellows")                                 # the bellows: two boards and a leather bag between them
    bc = v3((0.25, -0.15, 0.1))
    lb.add(Ellipsoid(bc, (0.22, 0.15, 0.08), **wob(12.0, 0.006, seed + 9)))
    lb.add(RoundCone(bc - v3((0.18, 0, -0.02)), v3((-0.04, -0.07, 0.3)), 0.035, 0.025), k=0.02)
    out.append(("Bellows", lb, fine(0.006, 0.012), "leather"))
    wd = Field("Boards")
    for zz in (-0.01, 0.2):
        plank_x(wd, bc + v3((0.03, 0, zz)), (0.26, 0.17, 0.018))
    plank_x(wd, bc + v3((0.32, 0, 0.21)), (0.12, 0.03, 0.02))                     # the handle
    out.append(("Boards", wd, fine(0.005, 0.01), "timber"))
    place_parts(out, ore_heap(0.75, 0.34, seed + 10), (1.25, -0.35, 0.0))
    bk = Field("Basket")                                  # a wicker basket of charcoal
    bq = v3((1.05, 0.95, 0.0))
    bk.add(Cylinder(bq + v3((0, 0, 0.17)), 0.2, 0.34, rr=0.03))
    bk.sub(Cylinder(bq + v3((0, 0, 0.3)), 0.17, 0.2))
    bk.paint(Cylinder(bq + v3((0, 0, 0.3)), 0.25, 0.06), 7)
    out.append(("Basket", bk, fine(0.006, 0.012), "basket"))
    ch = Field("Charcoal")
    for i in range(9):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, 0.12)
        ch.add(RoundBox(bq + v3((rr * math.cos(a), rr * math.sin(a), 0.3)), (0.05, 0.03, 0.025), 0.01, R=Rz(rng.uniform(0, 3))))
    out.append(("Charcoal", ch, fine(0.005, 0.01), "charcoal"))
    out.append(("Floor", ground_cut(_floor(2.0, 1.6, (0.3, 0.2), seed + 11)), fine(0.012, 0.022), "earth"))
    return out


def _floor(rx, ry, c, seed):
    f = Field("Floor")
    f.add(Ellipsoid((c[0], c[1], -0.1), (rx, ry, 0.13), **wob(2.0, 0.015, seed)))
    return f


def smithy(seed=0):
    """A smithy: an open shed of four posts and tie beams under a ridged thatch roof; a stone hearth at the back with
    coals glowing on it and a clay tuyere, an anvil on a log, a quench trough, a sword blank on the anvil and a pair of
    tongs; a log seat and a stack of iron bars outside."""
    rng = np.random.default_rng(seed)
    out = []
    t = Field("Timber")
    X, Y, EZ = 1.0, 0.75, 1.32                            # half sizes of the post square, eave height
    for sx in (-1, 1):
        for sy in (-1, 1):
            post(t, (sx * X, sy * Y, -0.04), (sx * X, sy * Y, EZ), 0.065, 0.058)
    for sy in (-1, 1):
        plank_x(t, (0, sy * Y, EZ + 0.03), (X + 0.18, 0.06, 0.06))
    for sx in (-1, 1):
        t.add(RoundBox((sx * X, 0, EZ + 0.1), (0.06, Y + 0.12, 0.05), 0.02), k=0.004)
    t.add(RoundBox((0, 0, EZ + 0.86), (X + 0.3, 0.05, 0.05), 0.02), k=0.004, label=10)   # ridge pole
    ground_cut(t)
    out.append(("Timber", t, fine(0.006, 0.012), "timber"))
    rf = Field("Roof")
    rf.add(gable((0, 0), X + 0.32, Y + 0.42, EZ + 0.02, EZ + 0.88, axis="x", over=0.08), **{})
    rf.sub(gable((0, 0), X + 0.5, Y + 0.3, EZ - 0.1, EZ + 0.72, axis="x"))           # (hollow underneath)
    rf.paint(RoundBox((0, 0, EZ + 0.88), (X + 0.4, 0.12, 0.08)), 5)
    out.append(("Roof", rf, fine(0.0095, 0.019), "thatch"))
    hs = Field("Hearth")                                  # the hearth at the back (+Y)
    hs.add(RoundBox((-0.25, Y - 0.25, 0.3), (0.42, 0.28, 0.32), 0.05, **wob(4.0, 0.008, seed + 2)))
    hs.sub(Ellipsoid((-0.25, Y - 0.27, 0.64), (0.3, 0.18, 0.1)))
    hs.add(RoundBox((-0.25, Y + 0.02, 0.75), (0.36, 0.09, 0.15), 0.04, **wob(5.0, 0.008, seed + 3)), k=0.02)  # its back wall
    ground_cut(hs)
    out.append(("Hearth", hs, fine(0.008, 0.016), "drystone"))
    cg = Field("Coals")
    cg.add(Ellipsoid((-0.25, Y - 0.27, 0.6), (0.27, 0.15, 0.06), **wob(22.0, 0.01, seed + 4)))
    out.append(("Coals", cg, fine(0.006, 0.012), "glow_fire"))
    cl = Field("Clay")
    cl.add(RoundCone((-0.25, Y + 0.06, 0.66), (-0.25, Y - 0.12, 0.62), 0.06, 0.045), k=0.01)   # tuyere through the back wall
    cl.paint(Sphere((-0.25, Y - 0.12, 0.62), 0.07), 5)
    out.append(("Clay", cl, fine(0.006, 0.012), "furnace_clay"))
    ir = Field("Iron")
    lg = v3((0.35, -0.1, 0.0))
    anvil(ir, lg + v3((0, 0, 0.62)), 1.0)
    ir.add(RoundBox(lg + v3((0.0, 0.01, 0.635)), (0.16, 0.022, 0.006), 0.003, R=Rz(0.15)), k=0.002, label=6)    # a sword blank
    ir.add(RoundCone(lg + v3((-0.12, 0.08, 0.64)), lg + v3((-0.5, 0.25, 0.6)), 0.008, 0.007), label=6)        # tongs
    ir.add(RoundCone(lg + v3((-0.12, 0.1, 0.64)), lg + v3((-0.5, 0.29, 0.62)), 0.008, 0.007), label=6)
    for i in range(5):                                    # a stack of iron bars outside (-X)
        ir.add(RoundBox((-X - 0.45 + (i % 3) * 0.06, -0.35 + (i // 3) * 0.03, 0.03 + (i // 3) * 0.04), (0.025, 0.24, 0.018), 0.005), label=6)
    out.append(("Iron", ir, fine(0.004, 0.008), "iron"))
    lw = Field("Logs")
    lw.add(Cylinder(lg + v3((0, 0, 0.21)), 0.17, 0.44, rr=0.02, **wob(8.0, 0.006, seed + 5)), label=0)
    lw.paint(Cylinder(lg + v3((0, 0, 0.43)), 0.2, 0.03), 5)
    lw.add(Cylinder((0.8, -Y - 0.45, 0.13), 0.13, 0.7, rr=0.02, R=rot_from_axes(z_axis=(1, 0.15, 0)), **wob(8.0, 0.006, seed + 6)))   # a log seat
    ground_cut(lw)
    out.append(("Logs", lw, fine(0.006, 0.012), "bark_wood"))
    tr = Field("Trough")                                  # the quench trough (+X, toward the front)
    tq = v3((0.85, 0.3, 0.0))
    tr.add(RoundBox(tq + v3((0, 0, 0.17)), (0.14, 0.34, 0.17), 0.03), label=0)
    tr.sub(RoundBox(tq + v3((0, 0, 0.3)), (0.1, 0.3, 0.12), 0.02))
    ground_cut(tr)
    out.append(("Trough", tr, fine(0.005, 0.01), "timber"))
    wt = Field("Water")
    wt.add(RoundBox(tq + v3((0, 0, 0.27)), (0.1, 0.3, 0.012), 0.005))
    out.append(("Water", wt, fine(0.005, 0.01), "dark_water"))
    out.append(("Floor", ground_cut(_floor(1.6, 1.3, (0, 0), seed + 7)), fine(0.012, 0.022), "earth"))
    return out


# ------------------------------------------------------------------------------------------------ bog props
def willow(h=2.1, seed=0):
    """A grey willow: a short leaning trunk, gnarled, splitting into a crown of upright stems, each wrapped in narrow
    grey-green leaf clumps."""
    rng = np.random.default_rng(seed)
    s = h / 2.1
    a0 = rng.uniform(0, 2 * math.pi)
    d0 = v3((math.cos(a0), math.sin(a0), 0.0))
    f = Field("Trunk")
    head = v3((0, 0, h * 0.34)) + d0 * 0.16 * s
    f.add(Chain([v3((0, 0, -0.08)), v3((0, 0, h * 0.16)) + d0 * 0.05 * s, head], [0.16 * s, 0.13 * s, 0.12 * s], k=0.03, **wob(5.0, 0.02 * s, seed)))
    f.add(Ellipsoid(head, (0.17 * s, 0.16 * s, 0.11 * s), **wob(8.0, 0.02 * s, seed + 1)), k=0.05 * s)
    for i in range(4):
        a = 2 * math.pi * i / 4 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((0, 0, 0.12 * s), (0.32 * s * math.cos(a), 0.32 * s * math.sin(a), -0.04), 0.07 * s, 0.025 * s), k=0.06 * s)
    lv = Field("Leaves")
    for j in range(8):
        a = a0 + 2 * math.pi * j / 8 + rng.uniform(-0.3, 0.3)
        out = v3((math.cos(a), math.sin(a), 0.0))
        L = h * rng.uniform(0.5, 0.72)
        p0 = head + out * 0.06 * s + v3((0, 0, 0.05 * s))
        p1 = p0 + out * L * 0.22 + v3((0, 0, L * 0.5))
        p2 = p1 + out * L * 0.22 + v3((0, 0, L * 0.42))
        f.add(Chain([p0, p1, p2], [0.04 * s, 0.024 * s, 0.01 * s], k=0.01), k=0.03 * s)
        for q, r in ((p0 + (p1 - p0) * 0.75, 0.15), (p1 + (p2 - p1) * 0.45, 0.17), (p2, 0.13)):
            r *= s * rng.uniform(0.85, 1.15)
            lv.add(Ellipsoid(q, (r * 0.85, r * 0.85, r * 1.6), R=rot_from_axes(z_axis=unit(p2 - p0)),
                             **wob(14.0 / s, 0.03 * s, seed * 60 + j * 3 + int(r * 100))), k=0.06 * s)
    return [("Trunk", f, fine(0.008, 0.016), "willow_bark"), ("Leaves", lv, fine(0.011, 0.022), "willow_leaves")]


def alder(h=2.8, seed=0):
    """An alder: a dark straight trunk, branches rising at a steep angle, a dense rounded crown of dark green leaf
    clumps."""
    rng = np.random.default_rng(seed)
    s = h / 2.8
    f = Field("Trunk")
    pts = [v3((0, 0, -0.08)), v3((0.02, 0, h * 0.3)), v3((-0.02, 0.02, h * 0.62)), v3((0.0, 0.0, h * 0.9))]
    f.add(Chain(pts, [0.1 * s, 0.08 * s, 0.06 * s, 0.02 * s], k=0.02, **wob(4.0, 0.008 * s, seed)))
    for i in range(4):
        a = 2 * math.pi * i / 4 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((0, 0, 0.12 * s), (0.25 * s * math.cos(a), 0.25 * s * math.sin(a), -0.04), 0.06 * s, 0.02 * s), k=0.05 * s)
    c = Field("Leaves")
    ctr = v3((0, 0, h * 0.64))
    for j in range(6):
        t = rng.uniform(0.38, 0.72)
        p0 = at_height(pts, h * t)
        a = rng.uniform(0, 2 * math.pi)
        out = v3((math.cos(a), math.sin(a), 0.0))
        p2 = p0 + out * h * 0.2 + v3((0, 0, h * 0.24))
        f.add(Chain([p0, p0 + (p2 - p0) * 0.5, p2], [0.035 * s, 0.022 * s, 0.01 * s], k=0.006), k=0.02 * s)
    for j in range(26):
        u = rng.normal(size=3)
        u = u / np.linalg.norm(u) * rng.uniform(0.6, 1.0) ** 0.4
        q = ctr + v3((u[0] * 0.62 * s, u[1] * 0.62 * s, u[2] * 0.36 * h))
        r = s * rng.uniform(0.17, 0.25)
        c.add(Ellipsoid(q, (r, r * 0.92, r * 0.8), **wob(10.0 / s, 0.035 * s, seed * 80 + j)), k=0.07 * s)
    return [("Trunk", f, fine(0.008, 0.016), "alder_bark"), ("Leaves", c, fine(0.012, 0.024), "alder_leaves")]


def snag(h=2.0, seed=0):
    """A dead tree drowned by the bog: a silver-grey trunk with its top snapped off in splinters, a few broken
    branch stubs, the bark long gone."""
    rng = np.random.default_rng(seed)
    s = h / 2.0
    f = Field("Snag")
    a0 = rng.uniform(0, 2 * math.pi)
    d0 = v3((math.cos(a0), math.sin(a0), 0.0))
    pts = [v3((0, 0, -0.1)), v3((0, 0, h * 0.35)) + d0 * 0.04 * s, v3((0, 0, h * 0.75)) + d0 * 0.1 * s, v3((0, 0, h * 1.05)) + d0 * 0.14 * s]
    f.add(Chain(pts, [0.12 * s, 0.1 * s, 0.075 * s, 0.06 * s], k=0.02, **wob(5.0, 0.01 * s, seed)))
    for i in range(3):
        a = 2 * math.pi * i / 3 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((0, 0, 0.1 * s), (0.27 * s * math.cos(a), 0.27 * s * math.sin(a), -0.04), 0.07 * s, 0.025 * s), k=0.05 * s)
    for i in range(4):
        z = h * rng.uniform(0.35, 0.8)
        p0 = at_height(pts, z)
        a = rng.uniform(0, 2 * math.pi)
        L = rng.uniform(0.15, 0.4) * s
        p1 = p0 + v3((math.cos(a) * L, math.sin(a) * L, L * 0.5))
        f.add(RoundCone(p0, p1, 0.035 * s, 0.018 * s), k=0.02 * s)
    zc = h * rng.uniform(0.85, 0.95)                      # snapped: a jagged slant
    top = at_height(pts, zc)
    nrm = unit(v3((math.cos(a0 + 2.0) * 0.5, math.sin(a0 + 2.0) * 0.5, 1.0)))

    def snapped(P):
        dp = (P - top.astype(F32)) @ nrm.astype(F32)
        jag = np.abs(np.sin(P[:, 0] * 41.0 + P[:, 1] * 37.0)) * 0.06 * s + NOISE.fbm(P * 12.0, 2) * 0.03 * s
        return (dp - jag).astype(F32)
    f.inter(Func(lambda P: -snapped(P) * -1.0, (-1, -1, -1), (1, 1, h * 1.2)))
    f.inter(Plane((0, 0, -0.06), (0, 0, -1)))
    return [("Snag", f, fine(0.007, 0.014), "deadwood")]


def cotton_grass(seed=0, n=9):
    """Bog cotton: a tuft of fine tawny blades, slender stalks above it carrying white cotton heads."""
    rng = np.random.default_rng(seed)
    bl, ct = Field("Blades"), Field("Cotton")
    th = max(0.005, fine(0.004, 0.008) * 0.7)
    for i in range(16):
        a = rng.uniform(0, 2 * math.pi)
        b0 = v3((0.04 * math.cos(a), 0.04 * math.sin(a), -0.02))
        hh = rng.uniform(0.2, 0.34)
        bend = rng.uniform(0.3, 0.7)
        hz = v3((math.cos(a), math.sin(a), 0.0))
        P = [b0 + hz * (bend * hh * t ** 2) + v3((0, 0, hh * t)) for t in np.linspace(0, 1, 5)]
        for k in range(4):
            tg, sd, nn = frame(P[k + 1] - P[k])
            L = float(np.linalg.norm(P[k + 1] - P[k]))
            bl.add(Ellipsoid((P[k] + P[k + 1]) / 2, (L * 0.62, 0.012 * (1 - k / 4) + 0.003, th), R=rot_from_axes(x_axis=tg, y_axis=sd)), k=0.004)
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.0, 0.1)
        b0 = v3((rr * math.cos(a), rr * math.sin(a), 0.0))
        hh = rng.uniform(0.38, 0.55)
        top = b0 + v3((math.cos(a) * 0.06, math.sin(a) * 0.06, hh))
        bl.add(RoundCone(b0, top, 0.006, 0.004), k=0.002)
        ct.add(Ellipsoid(top + v3((0, 0, 0.03)), (0.034, 0.034, 0.045), **wob(45.0, 0.008, seed * 20 + i)))
    return [("Blades", bl, fine(0.004, 0.008), "bog_grass"), ("Cotton", ct, fine(0.005, 0.01), "cotton")]


def hummock(w=1.1, h=0.32, seed=0):
    """A sphagnum hummock: a soft cushion of moss, swelling in lumps."""
    rng = np.random.default_rng(seed)
    f = Field("Moss")
    f.add(Ellipsoid((0, 0, -h * 0.25), (w * 0.48, w * 0.42, h * 1.15), **wob(4.0 / w, 0.03 * w, seed)))
    for i in range(7):
        a = rng.uniform(0, 2 * math.pi)
        rr = w * rng.uniform(0.1, 0.36)
        r = w * rng.uniform(0.14, 0.22)
        f.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a), h * rng.uniform(0.2, 0.55)), (r, r, r * 0.6), **wob(8.0 / w, 0.02 * w, seed * 10 + i)), k=0.08 * w)
    ground_cut(f)
    return [("Moss", f, fine(0.008, 0.016), "sphagnum")]


def bog_oak(seed=0, L=2.0):
    """A bog oak: a gnarled trunk stained black by thousands of years in the peat, lying half sunk, a broken root plate
    at one end, snapped branch stubs."""
    rng = np.random.default_rng(seed)
    f = Field("Oak")
    pts = [v3((-L / 2, 0, 0.06)), v3((-L / 6, 0.08, 0.1)), v3((L / 6, -0.04, 0.08)), v3((L / 2, 0.06, 0.04))]
    f.add(Chain(pts, [0.2, 0.17, 0.14, 0.1], k=0.04, **wob(4.0, 0.02, seed)))
    for i in range(6):                                    # the root plate (-X end)
        a = 2 * math.pi * i / 6 + rng.uniform(-0.3, 0.3)
        tip = v3((-L / 2 - 0.12, 0.42 * math.cos(a), 0.06 + 0.36 * math.sin(a)))
        f.add(RoundCone(v3((-L / 2 + 0.05, 0, 0.08)), tip, 0.09, 0.03, **wob(10.0, 0.008, seed + i)), k=0.06)
    for i in range(3):
        p0 = at_height([pts[0], pts[3]], 0.0) if False else pts[1 + i % 2] + v3((rng.uniform(-0.2, 0.2), 0, 0))
        a = rng.uniform(0.3, 2.8)
        p1 = p0 + v3((rng.uniform(-0.15, 0.15), math.cos(a) * 0.3, math.sin(a) * 0.3 + 0.1))
        f.add(RoundCone(p0, p1, 0.07, 0.045), k=0.04)
    f.inter(Plane((0, 0, -0.05), (0, 0, -1)))
    return [("Oak", f, fine(0.008, 0.016), "bog_oak")]


def peat_stack(seed=0):
    """Peat turves stacked to dry: a round, slightly leaning stack of dark bricks laid in rings, gaps between them for
    the wind, a few spare turves at its foot."""
    rng = np.random.default_rng(seed)
    f = Field("Peat")
    for k in range(5):
        R = 0.42 - k * 0.075
        n = max(4, int(2 * math.pi * R / 0.2))
        z = 0.05 + k * 0.1
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * (k % 2)) / n + rng.uniform(-0.06, 0.06)
            c = v3((R * math.cos(a), R * math.sin(a), z))
            R_ = rot_from_axes(x_axis=(-math.sin(a), math.cos(a), 0.0), z_axis=(math.cos(a) * 0.25, math.sin(a) * 0.25, 1.0))
            f.add(RoundBox(c, (0.11 * rng.uniform(0.85, 1.1), 0.055, 0.045), 0.012, R=R_, **wob(14.0, 0.006, seed * 40 + k * 10 + i)), k=0.004)
    f.add(RoundBox((0, 0, 0.56), (0.1, 0.08, 0.045), 0.015, R=Rz(0.6)), k=0.004)
    for i in range(4):
        a = rng.uniform(0, 2 * math.pi)
        f.add(RoundBox((0.62 * math.cos(a), 0.62 * math.sin(a), 0.03), (0.11, 0.055, 0.04), 0.012, R=Rz(rng.uniform(0, 3))), k=0.004)
    ground_cut(f)
    return [("Peat", f, fine(0.006, 0.012), "peat")]


# ------------------------------------------------------------------------------------------------ bog landmarks
def crannog(seed=0):
    """A crannog: a roundhouse of daub and thatch on a round timber platform raised on piles over a peaty pool,
    the piles' heads ringing it as a low palisade; a gangway of planks on posts to the bank (-Y), a dugout canoe
    tied alongside."""
    rng = np.random.default_rng(seed)
    out = []
    PZ, PR = 0.36, 1.45
    pl = Field("Platform")
    pl.add(Cylinder((0, 0, PZ - 0.04), PR, 0.08, rr=0.02), label=10)
    for i in range(1, 12):                                # the joints between its planks
        pl.sub(RoundBox((0, -PR + i * 2 * PR / 12, PZ), (PR + 0.1, 0.009, 0.014), 0.004))
    n = 30
    for i in range(n):                                    # the piles, their heads a low palisade
        a = 2 * math.pi * i / n
        hh = PZ + rng.uniform(0.12, 0.3)
        if -math.pi / 2 - 0.2 < math.atan2(math.sin(a), math.cos(a)) < -math.pi / 2 + 0.2:
            hh = PZ + 0.04                                # (a gap where the gangway lands)
        post(pl, (PR * math.cos(a), PR * math.sin(a), -0.1), ((PR + 0.01) * math.cos(a), (PR + 0.01) * math.sin(a), hh), 0.05, 0.045, pointed=hh > PZ + 0.1)
    for i in range(6):                                    # piles under the middle
        a = 2 * math.pi * i / 6 + 0.3
        post(pl, (0.8 * math.cos(a), 0.8 * math.sin(a), -0.1), (0.8 * math.cos(a), 0.8 * math.sin(a), PZ - 0.05), 0.05)
    for i in range(6):                                    # the gangway: posts and planks
        y = -PR - 0.15 - i * 0.24
        for sx in (-1, 1):
            if i % 2 == 0:
                post(pl, (sx * 0.24, y, -0.1), (sx * 0.24, y, PZ - 0.04 - i * 0.035), 0.035)
        pl.add(RoundBox((0, y, PZ - 0.03 - i * 0.035), (0.3, 0.1, 0.02), 0.008, **wob(10.0, 0.003, seed + i)), k=0.002, label=10)
    out.append(("Platform", pl, fine(0.006, 0.012), "timber"))
    for nm, f, vv, m in roundhouse(seed + 1, wall="daub", r=0.95, wall_h=0.56, roof_h=1.35, z0=PZ, base=False):
        out.append((nm, f, vv, m))
    cn = Field("Canoe")                                   # a dugout canoe tied alongside (+X)
    cq = v3((PR + 0.35, -0.3, 0.06))
    R_ = Rz(1.45)
    cn.add(Ellipsoid(cq, (0.12, 0.85, 0.09), R=R_))
    cn.sub(Ellipsoid(cq + v3((0, 0, 0.06)), (0.09, 0.78, 0.08), R=R_))
    cn.inter(Plane(cq + v3((0, 0, 0.065)), (0, 0, 1)))
    out.append(("Canoe", cn, fine(0.005, 0.01), "logs"))
    pw = Field("Pool")                                    # the peaty pool round it
    pw.add(Cylinder((0, 0, 0.0), PR + 0.75, 0.04, rr=0.015, **wob(1.5, 0.08, seed + 9)))
    pw.sub(Cylinder((0, -PR - 1.7, 0.0), 0.75, 0.2))      # (the bank where the gangway lands)
    out.append(("Pool", pw, fine(0.012, 0.024), "dark_water"))
    sh = Field("Shore")
    sh.add(Torus((0, 0, -0.02), PR + 0.78, 0.12, **wob(2.0, 0.04, seed + 10)))
    sh.add(Ellipsoid((0, -PR - 1.75, -0.04), (0.8, 0.55, 0.12), **wob(3.0, 0.02, seed + 11)), k=0.1)
    ground_cut(sh)
    out.append(("Shore", sh, fine(0.012, 0.024), "sphagnum"))
    place_parts(out, reeds(seed + 12, 16, 0.95), (PR + 0.6, 0.85, 0.0))
    place_parts(out, reeds(seed + 13, 14, 0.85), (-PR - 0.55, -0.6, 0.0))
    return out


def idol(seed=0):
    """A carved wooden idol: a tall standing figure of dark oak, a big head with a heavy brow and white quartz pebbles
    for eyes, arms carved down the body to hands meeting at the belly, legs parted; set in a cairn of stones inside a
    ring of stakes bound with withies, offerings at its feet (a pot, an iron sword driven into the ground)."""
    rng = np.random.default_rng(seed)
    out = []
    w = Field("Figure")
    w.add(RoundBox((0, 0, 0.62), (0.15, 0.1, 0.36), 0.05), label=11)                             # the legs as one block
    w.sub(RoundBox((0, -0.02, 0.48), (0.025, 0.2, 0.24), 0.01))                        # parted
    w.add(RoundBox((0, 0, 1.18), (0.17, 0.11, 0.25), 0.06), k=0.04, label=11)                    # the body
    w.add(Ellipsoid((0, -0.01, 1.62), (0.14, 0.12, 0.18)), k=0.06, label=11)                     # the head
    w.add(RoundBox((0, -0.07, 1.68), (0.13, 0.05, 0.025), 0.02), k=0.02, label=11)               # the brow ridge
    w.add(RoundCone((0, -0.1, 1.64), (0, -0.13, 1.57), 0.022, 0.03), k=0.015, label=11)          # the nose
    for sx in (-1, 1):
        w.sub(Sphere((sx * 0.055, -0.11, 1.62), 0.035))                                # eye sockets
        w.add(Chain([(sx * 0.17, -0.02, 1.38), (sx * 0.18, -0.08, 1.15), (sx * 0.06, -0.12, 1.02)], [0.04, 0.035, 0.03], k=0.01), k=0.015, label=11)  # arms
    w.sub(RoundBox((0, -0.13, 1.5), (0.04, 0.03, 0.006), 0.004))                       # the mouth
    w.add(RoundBox((0, 0, 0.13), (0.13, 0.13, 0.15), 0.03), k=0.05, label=11)                    # the foot of the post
    out.append(("Figure", w, fine(0.005, 0.01), "idol_wood"))
    ey = Field("Eyes")
    for sx in (-1, 1):
        ey.add(Sphere((sx * 0.055, -0.1, 1.62), 0.027))
    out.append(("Eyes", ey, fine(0.004, 0.008), "quartz"))
    cr = Field("Cairn")
    for i in range(22):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.18, 0.5)
        sz = rng.uniform(0.08, 0.14)
        z = 0.22 * (1 - rr / 0.55)
        cr.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a), z), (sz * 1.3, sz, sz * 0.75), R=Rz(rng.uniform(0, 3)), **wob(10.0, 0.01, seed + i)), k=0.01)
    ground_cut(cr)
    out.append(("Cairn", cr, fine(0.008, 0.016), "rock"))
    st = Field("Stakes")
    n = 11
    for i in range(n):
        a = 2 * math.pi * i / n + 0.15
        if abs(math.atan2(math.sin(a + math.pi / 2), math.cos(a + math.pi / 2))) < 0.35:
            continue                                     # (open toward the front, -Y)
        hh = rng.uniform(0.75, 0.95)
        post(st, (0.95 * math.cos(a), 0.85 * math.sin(a), -0.03), (0.97 * math.cos(a), 0.87 * math.sin(a), hh), 0.035, 0.03, pointed=True)
        st.paint(Cylinder((0.95 * math.cos(a), 0.85 * math.sin(a), 0.5), 0.07, 0.12), 7)     # withy bands
    ground_cut(st)
    out.append(("Stakes", st, fine(0.005, 0.01), "bark_wood"))
    of = Field("Pot")
    pq = v3((-0.32, -0.55, 0.0))
    of.add(Ellipsoid(pq + v3((0, 0, 0.12)), (0.12, 0.12, 0.12)))
    of.add(Torus(pq + v3((0, 0, 0.22)), 0.075, 0.016), k=0.01)
    of.sub(Cylinder(pq + v3((0, 0, 0.25)), 0.065, 0.1))
    ground_cut(of)
    out.append(("Pot", of, fine(0.005, 0.01), "pottery"))
    sw = Field("Sword")
    sq = v3((0.3, -0.6, 0.0))
    R_ = rot_from_axes(z_axis=(0.15, -0.1, 1.0))
    sw.add(RoundBox(sq + R_ @ v3((0, 0, 0.12)), (0.022, 0.006, 0.2), 0.003, R=R_), label=6)
    sw.add(RoundBox(sq + R_ @ v3((0, 0, 0.33)), (0.06, 0.015, 0.012), 0.006, R=R_), k=0.004, label=6)
    sw.add(RoundCone(sq + R_ @ v3((0, 0, 0.34)), sq + R_ @ v3((0, 0, 0.44)), 0.014, 0.012, R=None), k=0.004, label=9)
    sw.add(Sphere(sq + R_ @ v3((0, 0, 0.455)), 0.02), k=0.004, label=6)
    out.append(("Sword", sw, fine(0.003, 0.006), "timber"))
    return mound(out, 1.25, 1.15, 0.1, seed)


# ------------------------------------------------------------------------------------------------ the Iron city
def iron_city(seed=0):
    """The gate of a hill fort at the end of the road (the gate faces -X, where the road comes in): earth ramparts
    running off both ways under a palisade of sharpened stakes; two square timber gate towers with plank walls, a
    fighting platform and a thatched pyramid roof each, a walkway between them over the gate; heavy plank doors with
    iron straps; iron fire baskets on poles before the towers (game.gd lights them); woad-blue banners; inside, three
    roundhouses and a granary on stilts."""
    rng = np.random.default_rng(seed)
    out = []
    TY, TX, TH, TS = 1.3, 0.75, 2.35, 0.6                 # tower centre |y| and x, platform height, half size
    rp = Field("Rampart")
    for sy in (-1, 1):
        def bank(P, sy=sy):
            x, y, z = P[:, 0], P[:, 1] * sy, P[:, 2]
            hgt = 1.15 + 0.05 * np.sin(y * 1.7)
            half = 1.25 - z * 0.62                        # (steep, battered faces)
            d = np.maximum(np.abs(x - 1.05) - half, z - hgt)
            d = np.maximum(d, np.maximum(TY - 0.55 - y, y - 6.9))
            return (d * 0.8).astype(F32)
        lo = (-0.6, (TY - 0.7) if sy > 0 else -7.0, -0.1)
        hi = (2.7, 7.0 if sy > 0 else -(TY - 0.7), 1.3)
        rp.add(Func(bank, lo, hi, **wob(1.5, 0.05, seed + sy)), k=0.1)
    ground_cut(rp, -0.04)
    out.append(("Rampart", rp, fine(0.014, 0.028), "turf"))
    pa = Field("Palisade")
    for sy in (-1, 1):
        y = TY + TS + 0.06
        i = 0
        while y < 6.75:
            hh = 1.95 + rng.uniform(-0.07, 0.07)
            x = 0.62 + rng.uniform(-0.02, 0.02)
            post(pa, (x, sy * y, 0.95), (x + rng.uniform(-0.02, 0.02), sy * y, hh), 0.075, 0.07, pointed=True)
            y += 0.155 + rng.uniform(-0.01, 0.01)
            i += 1
        plank_x(pa, (0.74, sy * 4.1, 1.62), (0.035, 2.75, 0.04), label=0)          # the rail tying the stakes
    out.append(("Palisade", pa, fine(0.0095, 0.019), "timber"))
    tw = Field("Towers")
    for sy in (-1, 1):
        cy = sy * TY
        for (dx, dy) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            post(tw, (TX + dx * TS, cy + dy * TS, -0.04), (TX + dx * TS, cy + dy * TS, TH + 0.62), 0.09, 0.08)
        for z in (0.95, 1.55):                            # plank walls on the outside and the gate side
            tw.add(RoundBox((TX - TS, cy, z), (0.035, TS, 0.3), 0.01), k=0.004, label=11)
            tw.add(RoundBox((TX, cy + sy * TS, z), (TS, 0.035, 0.3), 0.01), k=0.004, label=11)
            tw.add(RoundBox((TX, cy - sy * TS, z), (TS, 0.035, 0.3), 0.01), k=0.004, label=11)
        tw.add(RoundBox((TX, cy, TH), (TS + 0.1, TS + 0.1, 0.05), 0.015), k=0.004, label=10)   # the fighting platform
        for z in (TH + 0.32,):                            # its rail
            for (a, b) in (((TX - TS, cy - TS), (TX - TS, cy + TS)), ((TX + TS, cy - TS), (TX + TS, cy + TS))):
                tw.add(RoundCone((a[0], a[1], z), (b[0], b[1], z), 0.03, 0.03), k=0.004, label=0)
            for (a, b) in (((TX - TS, cy - TS), (TX + TS, cy - TS)), ((TX - TS, cy + TS), (TX + TS, cy + TS))):
                tw.add(RoundCone((a[0], a[1], z), (b[0], b[1], z), 0.03, 0.03), k=0.004, label=10)
        for k in range(5):                                # wall slits (dark insets added below)
            pass
    tw.add(RoundBox((TX, 0, TH - 0.02), (0.55, TY - TS + 0.02, 0.05), 0.015), k=0.004, label=0)     # the walkway over the gate
    for sx in (-1, 1):
        tw.add(RoundCone((TX + sx * 0.5, -(TY - TS), TH + 0.3), (TX + sx * 0.5, TY - TS, TH + 0.3), 0.028, 0.028), k=0.004, label=0)
        for k in range(3):
            yy = -0.4 + k * 0.4
            post(tw, (TX + sx * 0.5, yy, TH), (TX + sx * 0.5, yy, TH + 0.32), 0.025)
    plank_x(tw, (TX - 0.05, 0, TH - 0.2), (0.12, TY - TS + 0.15, 0.09), label=0)      # the lintel beam
    tw.paint(RoundBox((TX - TS - 0.04, -TY, 1.25), (0.02, 0.22, 0.32)), 7)          # blue paint on the outer planks
    tw.paint(RoundBox((TX - TS - 0.04, TY, 1.25), (0.02, 0.22, 0.32)), 7)
    ground_cut(tw, -0.04)
    out.append(("Towers", tw, fine(0.007, 0.014), "timber"))
    rf = Field("Roofs")
    for sy in (-1, 1):
        rf.add(pyramid_roof((TX, sy * TY), TS + 0.28, TH + 0.6, TH + 1.35))
        rf.paint(Sphere((TX, sy * TY, TH + 1.33), 0.12), 5)
    out.append(("Roofs", rf, fine(0.0095, 0.019), "thatch"))
    gd = Field("Gate")
    for sy in (-1, 1):                                    # the two doors, closed
        gd.add(RoundBox((TX - 0.02, sy * 0.36, 0.95), (0.06, 0.35, 0.95), 0.015), label=11)
        for z in (0.35, 0.95, 1.55):                      # iron straps and studs
            gd.add(RoundBox((TX - 0.085, sy * 0.36, z), (0.012, 0.33, 0.04), 0.006), k=0.003, label=6)
            for k in range(4):
                gd.add(Sphere((TX - 0.1, sy * (0.1 + k * 0.17), z), 0.017), k=0.003, label=6)
        gd.add(Torus((TX - 0.11, sy * 0.1, 1.0), 0.065, 0.013, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.003, label=6)
    ground_cut(gd)
    out.append(("Gate", gd, fine(0.0055, 0.011), "timber"))
    fb = Field("Baskets")                                 # iron fire baskets on poles before the towers
    for sy in (-1, 1):
        c = v3((-0.1, sy * TY, 0.0))
        fb.add(RoundCone(c, c + v3((0, 0, 1.1)), 0.03, 0.025), label=6)
        for k in range(6):
            a = 2 * math.pi * k / 6
            fb.add(RoundCone(c + v3((0.05 * math.cos(a), 0.05 * math.sin(a), 1.08)), c + v3((0.17 * math.cos(a), 0.17 * math.sin(a), 1.32)), 0.012, 0.012), k=0.006, label=6)
        fb.add(Torus(c + v3((0, 0, 1.32)), 0.17, 0.014), k=0.004, label=6)
        fb.add(Torus(c + v3((0, 0, 1.2)), 0.11, 0.012), k=0.004, label=6)
    ground_cut(fb)
    out.append(("Baskets", fb, fine(0.0045, 0.009), "iron"))
    cg = Field("Coals")
    for sy in (-1, 1):
        cg.add(Ellipsoid((-0.1, sy * TY, 1.24), (0.11, 0.11, 0.06), **wob(25.0, 0.008, seed + sy)))
    out.append(("Coals", cg, fine(0.005, 0.01), "glow_fire"))
    bn = Field("Banners")                                 # woad-blue banners hung from the platforms
    for sy in (-1, 1):
        def banner_fn(P, cy=sy * TY):
            x, y, z = P[:, 0], P[:, 1] - cy, P[:, 2]
            wave = 0.025 * np.sin(z * 8.0 + y * 3.0)
            half = np.where(z < 1.45, 0.24 - (1.45 - z) * 0.9, 0.24)
            return np.maximum.reduce([np.abs(x - (TX - TS - 0.12 + wave)) - 0.014, np.abs(y) - half, z - (TH - 0.04), 1.2 - z]).astype(F32)
        bn.add(Func(banner_fn, (TX - TS - 0.3, sy * TY - 0.35, 1.1), (TX - TS + 0.05, sy * TY + 0.35, TH + 0.05)))
        bn.paint(Cylinder((TX - TS - 0.13, sy * TY, 1.78), 0.12, 0.1, R=rot_from_axes(z_axis=(1, 0, 0))), 5)    # a white disc
        bn.paint(RoundBox((TX - TS - 0.12, sy * TY, TH - 0.12), (0.06, 0.3, 0.035)), 5)
    out.append(("Banners", bn, fine(0.005, 0.01), "banner"))
    dk = Field("Dark")
    for sy in (-1, 1):
        for z in (1.0, 1.6):
            dk.add(RoundBox((TX - TS - 0.02, sy * TY + 0.25, z), (0.03, 0.03, 0.1), 0.01))
    out.append(("Dark", dk, fine(0.006, 0.012), "dark"))
    for (hx, hy, r, sd) in ((3.55, -2.7, 0.95, 1), (4.45, 1.75, 1.05, 2), (3.35, 4.6, 0.85, 3)):
        parts = roundhouse(seed + 20 + sd, wall="daub", r=r, wall_h=0.55, roof_h=1.35, base=False)
        # (each house its own fields: merged, their meshing grids would span the whole fort)
        place_parts(out, parts, (hx, hy, 0.0), Rz(math.atan2(-hy, 1.5 - hx) + math.pi / 2),
                    rename={n: "%s%d" % (n, sd) for n in ("Wall", "Roof", "Door", "Dark")})
    gr = Field("Granary")                                 # a granary on four stilts
    gq = v3((4.6, -0.5, 0.0))
    for (dx, dy) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        post(gr, gq + v3((dx * 0.32, dy * 0.32, -0.03)), gq + v3((dx * 0.32, dy * 0.32, 0.55)), 0.05)
    gr.add(RoundBox(gq + v3((0, 0, 0.58)), (0.4, 0.4, 0.03), 0.01), k=0.004, label=10)
    ground_cut(gr)
    out.append(("Granary", gr, fine(0.006, 0.012), "timber"))
    gw = Field("GranaryWall")                             # its wickerwork body
    gw.add(Cylinder(gq + v3((0, 0, 0.82)), 0.34, 0.45, rr=0.03))
    out.append(("GranaryWall", gw, fine(0.006, 0.012), "basket"))
    gt = Field("GranaryRoof")
    gt.add(cone(gq, 1.0, 1.62, 0.5, 0.0))
    out.append(("GranaryRoof", gt, fine(0.008, 0.016), "thatch"))
    yard = Field("Yard")
    yard.add(RoundBox((2.6, 0, -0.03), (1.6, 0.95, 0.07), 0.04, **wob(4.0, 0.008, seed + 40)))
    yard.add(RoundBox((0.75, 0, -0.03), (0.75, 0.62, 0.07), 0.04, **wob(4.0, 0.008, seed + 41)), k=0.1)
    cut_below(yard, -0.02, 1.8, 0, 2.6, 1.2)
    out.append(("Yard", yard, fine(0.012, 0.024), "earth"))
    return out


# ------------------------------------------------------------------------------------------------ the kits
# prop name -> (builder, game-mesh triangle budget), as decor_props.KITS. Tuft (and Flowers on the highland) are direct
# geometry (decor_build).
def KITS(theme):
    if theme == "highland":
        return {
            "Pine_A": (lambda: scots_pine(3.2, 101), 1800), "Pine_B": (lambda: scots_pine(2.6, 102, 0.09), 1500),
            "Pine_C": (lambda: scots_pine(1.9, 103, 0.03), 1100),
            "Birch_A": (lambda: birch(2.7, 104), 1500), "Birch_B": (lambda: birch(2.4, 105, twin=True), 1700),
            "Heather_A": (lambda: heather(0.95, 0.3, 106), 600), "Heather_B": (lambda: heather(0.62, 0.24, 107), 400),
            "Gorse": (lambda: gorse(0.95, 0.62, 108), 800), "Bracken": (lambda: bracken(109), 800),
            "Rock_A": (lambda: rock(1.8, 0.55, 110, "meadow"), 700), "Rock_B": (lambda: rock(1.1, 0.34, 111, "meadow", 1), 450),
            "Rock_C": (lambda: rock(2.4, 0.75, 112, "meadow", 3), 900),
            "Menhir_A": (lambda: menhir(1.6, 0.55, 113), 450), "Menhir_B": (lambda: menhir(1.1, 0.5, 114, lean=0.12), 400),
            "Stump": (lambda: stump(115, "meadow"), 400), "Log": (lambda: log(116, "meadow"), 420),
            "Reeds": (lambda: reeds(117, 18, 0.95), 800), "Rushes": (lambda: rushes(118), 900),
            "Broch": (lambda: broch(119), 3800), "Roundhouse": (lambda: roundhouse(120), 2600), "Circle": (lambda: stone_circle(121), 2800),
        }
    if theme == "forge":
        return {
            "Dead_A": (lambda: dead_tree(1.4, 131, "volcano"), 700), "Dead_B": (lambda: dead_tree(1.05, 132, "volcano"), 600),
            "Stump": (lambda: stump(133, "volcano"), 400),
            "Rock_A": (lambda: rock(1.8, 0.55, 134, "forge"), 700), "Rock_B": (lambda: rock(1.1, 0.34, 135, "forge", 1), 450),
            "Rock_C": (lambda: rock(2.4, 0.75, 136, "forge", 3), 900),
            "Slag_A": (lambda: slag_heap(1.4, 0.45, 137), 800), "Slag_B": (lambda: slag_heap(0.9, 0.32, 138), 500),
            "Ore_A": (lambda: ore_heap(1.0, 0.42, 139), 900), "Ore_B": (lambda: ore_heap(0.62, 0.3, 140), 500),
            "Cordwood": (lambda: cordwood(141), 900), "Clamp": (lambda: clamp(142), 800),
            "Bloomery": (lambda: bloomery(143), 4200), "Smithy": (lambda: smithy(144), 4400),
        }
    if theme == "bog":
        return {
            "Willow_A": (lambda: willow(2.2, 151), 1600), "Willow_B": (lambda: willow(1.6, 152), 1200),
            "Alder": (lambda: alder(2.8, 153), 1600),
            "Snag_A": (lambda: snag(2.0, 154), 600), "Snag_B": (lambda: snag(1.3, 155), 450),
            "Reeds": (lambda: reeds(156, 20, 1.0), 800), "Rushes": (lambda: rushes(157), 900), "Cotton": (lambda: cotton_grass(158), 700),
            "Hummock_A": (lambda: hummock(1.2, 0.34, 159), 450), "Hummock_B": (lambda: hummock(0.8, 0.26, 160), 300),
            "BogOak": (lambda: bog_oak(161), 700), "PeatStack": (lambda: peat_stack(162), 900),
            "Rock_A": (lambda: rock(1.0, 0.32, 163, "meadow", 1), 400),
            "Crannog": (lambda: crannog(164), 5600), "Idol": (lambda: idol(165), 2600),
        }
    if theme == "iron_city":
        return {"City": (lambda: iron_city(171), 15000)}
    raise KeyError(theme)
