"""HQ Gunpowder Age map props, sculpted as distance fields like decor_props, decor_bronze, decor_iron, decor_classical and
decor_medieval (same conventions: every builder returns its parts [(part name, Field, voxel, material key)], built at the
origin, Z up, ground at z = 0, a landmark's front toward -Y; KITS lists each theme's props and their game-mesh triangle
budgets; decor_build.materials resolves the material keys).

Jungle Outpost (jungle): tall rainforest trees on buttress roots under broad crowns hung with lianas, coconut palms,
bananas, tree ferns and giant ferns, monstera and elephant ears, heliconias in red and gold, bromeliads, mossy boulders,
a fallen log grown with bracket fungi, a stump; landmarks: an overgrown Maya-style temple pyramid (steep tiers, a steep
stair up its front to a shrine with a dark doorway under a roof comb, roots and lianas over it), carved stelae (one
broken), tumbled carved blocks with a serpent head, the outpost's timber watchtower on stilts under a palm thatch flying
the crimson-and-gold flag, a stilt hut under a palm-thatch roof, a dugout canoe.
Smuggler's Harbor (harbor): coconut palms, sea-grape and beach scrub, pale beach rocks, driftwood; the contraband:
crates, barrels, bales of indigo and sacks, a coil of rope, an anchor, a rowboat drawn up on the sand, nets drying on
poles, a chest of treasure; landmarks: a brigantine at her mooring (a dark hull with a gold stripe and gun ports, two
masts with furled sails and rigging, the red-and-black flag), a timber jetty, a waterfront tavern and warehouse (stone
below, timber and plaster above, a red tile roof, a hoist beam and a hanging sign), a lookout tower.
Star Fort (fortress): the besiegers' works: gabions, fascines, a curved earthen rampart, a trench parapet of sandbags,
a field gun on its carriage, a mortar, a pyramid of round shot, powder kegs, bell tents and the officers' marquee with
its pennants, a supply wagon, broken wheels; oaks, cypresses, bushes and rocks; landmarks: a redoubt (a square
earthwork with guns in its embrasures), a mortar battery, a tower windmill turned observation post.
The Gunpowder city at the end of every Gunpowder Age road (a star fort's gate: pale stone bastions with sloping scarps,
thick parapets with guns in their embrasures and domed sentry boxes at the angles, the gateway in the curtain under a
pediment carved with the crimson-and-gold arms, the drawbridge down over the dry ditch, braziers, the flag on its tall
pole; behind the walls the red-tiled barracks and a church tower with its bell) is its own kit ("fort_city",
gunpowder_city.glb).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Chain, Plane, Func, rot_from_axes, v3, NOISE, euler
import decor_props as DP
from decor_props import vx, wob, convex, crystal, rock, stump, log
from decor_bronze import (fine, unit, frame, box_bounds, ground_cut, cut_above, cut_below, place, place_parts, mound, convex_w,
                          walls_box, _half_blade, _blade, FOLD)
from decor_iron import Rz, R_xz, at_height, cone, gable, pyramid_roof, post
from decor_classical import bush as cbush, cypress, limestone, crenels, town_house
from decor_medieval import oak, fern, sailcloth, _timber_frame

F32 = np.float32
CRIMSON = (0.55, 0.08, 0.08)          # the Gunpowder army's colours (as material colours)
GOLD = (0.85, 0.62, 0.2)


# ------------------------------------------------------------------------------------------------ helpers
def poly_sdf2(x, y, poly):
    """Signed distance (negative inside) from 2D points (arrays x, y) to the closed polygon `poly` [(x, y), ...]."""
    Pp = np.asarray(poly, np.float32)
    x = x.astype(F32)
    y = y.astype(F32)
    d2 = (x - Pp[0, 0]) ** 2 + (y - Pp[0, 1]) ** 2
    s = np.ones(len(x), F32)
    n = len(Pp)
    for i in range(n):
        ax, ay = Pp[i]
        bx, by = Pp[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        wx, wy = x - ax, y - ay
        t = np.clip((wx * ex + wy * ey) / max(float(ex * ex + ey * ey), 1e-12), 0.0, 1.0)
        dx, dy = wx - ex * t, wy - ey * t
        d2 = np.minimum(d2, dx * dx + dy * dy)
        c1 = y >= ay
        c2 = y < by
        c3 = ex * wy > ey * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return (s * np.sqrt(d2)).astype(F32)


def leaf(o, u, v, poly, th, bend=0.0, cup=0.0, wave=None, holes=(), zfn=None, zamp=0.0):
    """A thin leaf (or any flat cut-out: a flag, a sign board) in the plane through o spanned by u (its length) and v
    (across it): the outline `poly` [(a, b), ...] in (u, v) coordinates, `th` its half thickness; bent along its length
    (offset bend * a^2 along n = u x v: a droop when bend < 0 and n points up), cupped across (cup * b^2), rippled by
    `wave` = (amplitude, wavenumber) growing toward its free end (a flag). `holes` [(a, b, r)] are cut through it; `zfn`
    (a, b) -> (offset, d/da, d/db) adds any other surface (folds in a hanging net), at most `zamp` either way."""
    o = v3(o)
    u = unit(u)
    v = unit(v3(v) - u * float(np.dot(v3(v), u)))
    n = unit(np.cross(u, v))
    of, uf, vf, nf = (x.astype(F32) for x in (o, u, v, n))
    A = np.array([p[0] for p in poly])
    B = np.array([p[1] for p in poly])
    L = max(float(A.max()), 1e-3)

    def zf(a, b):
        f = F32(bend) * a * a + F32(cup) * b * b
        fa = F32(2 * bend) * a
        fb = F32(2 * cup) * b
        if wave is not None:
            amp, k = wave
            t = np.clip(a / F32(L), 0, 1)
            f = f + F32(amp) * np.sin(a * F32(k)) * t
            fa = fa + F32(amp) * (F32(k) * np.cos(a * F32(k)) * t + np.sin(a * F32(k)) / F32(L))
        if zfn is not None:
            g, ga, gb = zfn(a, b)
            f, fa, fb = f + g, fa + ga, fb + gb
        return f, fa, fb

    def fn(P):
        Q = P - of
        a, b, c = Q @ uf, Q @ vf, Q @ nf
        f, fa, fb = zf(a, b)
        dz = np.abs(c - f) / np.sqrt(1.0 + fa * fa + fb * fb) - F32(th)
        d2 = poly_sdf2(a, b, poly)
        for (ha, hb, hr) in holes:
            d2 = np.maximum(d2, F32(hr) - np.sqrt((a - F32(ha)) ** 2 + (b - F32(hb)) ** 2))
        return np.maximum(dz, d2 * F32(0.9)).astype(F32)
    amin, amax, bmin, bmax = float(A.min()), float(A.max()), float(B.min()), float(B.max())
    fs = [bend * a * a + cup * b * b for a in (amin, amax, 0.0) for b in (bmin, bmax, 0.0)]
    wa = (abs(wave[0]) if wave is not None else 0.0) + zamp
    corners = [o + u * a + v * b + n * f for a in (amin, amax) for b in (bmin, bmax) for f in (min(fs) - wa - th, max(fs) + wa + th)]
    lo, hi = box_bounds(corners, 0.01)
    return Func(fn, lo, hi)


def leaf_mid(o, u, v, a0, a1, bend, r0, r1, n=6):
    """The midrib of a `leaf` (same o, u, v, bend): a tapering cord along its bent length from a0 to a1."""
    u = unit(u)
    v = unit(v3(v) - u * float(np.dot(v3(v), u)))
    nn = unit(np.cross(u, v))
    pts = [v3(o) + u * a + nn * (bend * a * a) for a in np.linspace(a0, a1, n)]
    return Chain(pts, list(np.linspace(r0, r1, n)), k=0.002)


def mirror(half):
    """A symmetric outline from its right half [(a, b >= 0), ...] (tip first, ending on the axis or near it)."""
    right = list(half)
    left = [(a, -b) for (a, b) in reversed(half) if b > 1e-6]
    return right + left


def heart(L, W):
    """An elephant ear: a broad heart, pointed tip at a = L, two rounded lobes behind the stalk (a < 0), a notch."""
    h = [(1.0, 0.0), (0.88, 0.16), (0.72, 0.33), (0.52, 0.45), (0.3, 0.5), (0.08, 0.48), (-0.12, 0.41), (-0.26, 0.28),
         (-0.31, 0.14), (-0.26, 0.05), (-0.08, 0.012)]
    return mirror([(a * L, b * W * 2) for a, b in h])


def monstera_leaf(L, W, rng):
    """A monstera leaf: a broad heart split from the edge in toward the midrib (the slits as narrow notches)."""
    base = [(1.0, 0.0), (0.9, 0.17), (0.75, 0.33), (0.55, 0.45), (0.33, 0.5), (0.1, 0.47), (-0.1, 0.38), (-0.22, 0.24),
            (-0.24, 0.1), (-0.12, 0.02)]
    out = []
    for i, (a, b) in enumerate(base):
        out.append((a * L, b * W * 2))
        if 1 <= i <= 6:                                  # a slit between this edge point and the next
            a2, b2 = base[i + 1]
            am, bm = (a + a2) / 2, (b + b2) / 2
            dep = rng.uniform(0.45, 0.62)
            out.append((am * L + 0.012, bm * W * 2))
            out.append((am * L * (1 - dep * 0.25) + 0.004, bm * W * 2 * (1 - dep)))
            out.append((am * L - 0.012, bm * W * 2 - 0.01))
    return mirror(out)


def paddle(L, W, rng=None, tears=0):
    """A banana leaf: a long oblong paddle, blunt at its tip, torn in from the edge here and there (`tears`)."""
    h = [(1.0, 0.0), (0.985, 0.22), (0.94, 0.42), (0.85, 0.48), (0.7, 0.5), (0.5, 0.5), (0.3, 0.49), (0.14, 0.42),
         (0.05, 0.25), (0.0, 0.06)]
    pts = [(a * L, b * W * 2) for a, b in h]
    if tears and rng is not None:
        out = [pts[0]]
        for i in range(1, len(pts)):
            a0, b0 = pts[i - 1]
            a1, b1 = pts[i]
            if 2 <= i <= 8 and rng.uniform() < tears:
                am, bm = (a0 + a1) / 2, (b0 + b1) / 2
                out += [(am + 0.006, bm), (am + 0.002, bm * rng.uniform(0.15, 0.35)), (am - 0.006, bm)]
            out.append((a1, b1))
        pts = out
    return mirror(pts)


def lance(L, W):
    """A narrow pointed leaf (heliconia, ginger)."""
    h = [(1.0, 0.0), (0.9, 0.2), (0.75, 0.38), (0.55, 0.48), (0.35, 0.5), (0.18, 0.42), (0.06, 0.25), (0.0, 0.05)]
    return mirror([(a * L, b * W * 2) for a, b in h])


def ring_scars(h, ring, amp, axis_fn):
    """Displacement for a palm trunk: a ring (leaf scar) every `ring` of height, a little noise."""
    def disp(P):
        z = np.clip(P[:, 2], 0, h)
        s = (z / F32(ring)) % F32(1.0)
        return ((np.minimum(s, F32(1.0) - s) - F32(0.25)) * F32(amp) * np.clip(z / F32(0.3), 0, 1) +
                NOISE.fbm(P * F32(8.0), 2) * F32(0.004)).astype(F32)
    return dict(disp=disp, disp_amp=amp + 0.006)


def hang(p0, length, sway, seed, n=7):
    """The points of a liana hanging from p0, swaying a little as it falls."""
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 2 * math.pi, 2)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        pts.append(v3(p0) + v3((sway * math.sin(t * 2.4 + ph[0]) * t, sway * math.sin(t * 1.9 + ph[1]) * t, -length * t)))
    return pts


def plank_box(f, c, half, R=None, label=10, k=0.003, r=0.006):
    f.add(RoundBox(c, half, r, R=R), k=k, label=label)


def flag(o, L, H, seed=0, th=0.007, wave=0.035, swallow=False, along=(1, 0, 0)):
    """A flag hanging from its hoist at o (the top of the hoist), flying along `along` (horizontal), L long, H high,
    rippled; swallow: its fly cut in a swallow-tail."""
    d = unit(along)
    poly = [(0.0, 0.0), (L, 0.0), (L, -H)] if not swallow else [(0.0, 0.0), (L, 0.0), (L * 0.78, -H * 0.5), (L, -H)]
    poly = poly + [(0.0, -H)]
    return leaf(o, d, v3((0, 0, 1)), [(a, b) for a, b in poly], th, wave=(wave, 2 * math.pi / (L * 0.9)))


def flag_paint(f, o, L, H, d=(1, 0, 0), saltire=0.06, border=0.04, label=6):
    """Paint the army's flag (made by `flag` at o, L x H, flying along d): a gold saltire (label 6) and a gold border
    on its crimson."""
    d = unit(d)
    of, df = v3(o).astype(F32), d.astype(F32)
    nrm = math.hypot(L, H)
    lo, hi = v3(o) - v3((L + 0.3, L + 0.3, H + 0.3)), v3(o) + v3((L + 0.3, L + 0.3, 0.3))

    def ab(P):
        Q = P - of
        return Q @ df, -(P[:, 2] - of[2])

    def salt(P):
        a, y = ab(P)
        d1 = np.abs(F32(H) * a - F32(L) * y) / F32(nrm)
        d2 = np.abs(F32(H) * a + F32(L) * y - F32(L * H)) / F32(nrm)
        return (np.minimum(d1, d2) - F32(saltire)).astype(F32)

    def bord(P):
        a, y = ab(P)
        return (np.minimum.reduce([a, F32(L) - a, y, F32(H) - y]) - F32(border)).astype(F32)
    if saltire > 0:
        f.paint(Func(salt, lo, hi), label)
    if border > 0:
        f.paint(Func(bord, lo, hi), label)


# ------------------------------------------------------------------------------------------------ jungle trees
def buttress(a, r_in, Hb, Rb, th, seed):
    """A buttress root: a thin plank-like fin from the trunk (height Hb up its side) curving down to the ground Rb out,
    snaking a little in plan, thick at the trunk, thin at its edge."""
    d = v3((math.cos(a), math.sin(a), 0.0))
    t = v3((-math.sin(a), math.cos(a), 0.0))
    df, tf = d.astype(F32), t.astype(F32)
    n = 10
    top = [(r_in + (Rb - r_in) * (i / n), Hb * (1.0 - i / n) ** 1.9) for i in range(n + 1)]
    poly = [(0.0, -0.06)] + [(0.0, Hb)] + top[1:] + [(Rb + 0.02, -0.06)]
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28)

    def fn(P):
        r = P @ df
        q = P @ tf - F32(0.035) * np.sin(r * F32(5.0) + F32(ph)) * np.clip(r / F32(Rb), 0, 1)
        d2 = poly_sdf2(r, P[:, 2], poly)
        tt = F32(th) * (F32(0.45) + F32(0.75) * np.clip(F32(1.0) - r / F32(Rb), 0, 1))
        return np.maximum(d2 * F32(0.9), np.abs(q) - tt).astype(F32)
    e = Rb + 0.1
    return Func(fn, (-e, -e, -0.08), (e, e, Hb + 0.05))


def jungle_tree(h=3.6, seed=0, crown_w=1.2, dome=0.35, vines=8, lean=0.04):
    """A tall rainforest tree: a straight pale trunk standing on thin buttress roots that snake out over the ground,
    great limbs spreading at the top under a broad, layered crown (lumpy clumps, darker below), lianas hanging from the
    crown's edge (one winding up the trunk), a few leafy tufts along them, epiphytes in the forks."""
    rng = np.random.default_rng(seed)
    s = h / 3.6
    f = Field("Trunk")
    c = Field("Leaves")
    vn = Field("Vines")
    vl = Field("VineLeaves")
    a0 = rng.uniform(0, 2 * math.pi)
    lv = v3((math.cos(a0), math.sin(a0), 0.0)) * lean * h
    Ht = h * 0.6
    r0 = 0.12 * s
    pts = [v3((0, 0, -0.08)), v3((0, 0, Ht * 0.35)) + lv * 0.3,
           v3((0, 0, Ht * 0.7)) + lv * 0.7 + v3((rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), 0.0)) * s, v3((0, 0, Ht)) + lv]
    f.add(Chain(pts, [r0 * 1.05, r0 * 0.9, r0 * 0.8, r0 * 0.72], k=0.03, **wob(5.0 / s, 0.008 * s, seed)))
    nb = 5
    for k in range(nb):                                         # buttress roots
        a = a0 + 2 * math.pi * k / nb + rng.uniform(-0.3, 0.3)
        Hb = rng.uniform(0.62, 0.9) * s
        Rb = rng.uniform(0.5, 0.68) * s
        f.add(buttress(a, r0 * 0.5, Hb, Rb, 0.032 * s, seed * 10 + k), k=0.04 * s)
        d = v3((math.cos(a), math.sin(a), 0.0))
        b = a + rng.uniform(-0.5, 0.5)
        e = v3((math.cos(b), math.sin(b), 0.0))
        f.add(Chain([d * (Rb - 0.04 * s) + v3((0, 0, 0.0)), d * Rb * 1.15 + e * 0.12 * s + v3((0, 0, 0.0)),
                     d * Rb * 1.45 + e * 0.2 * s + v3((0, 0, -0.03))], [0.03 * s, 0.022 * s, 0.012 * s], k=0.01), k=0.02)
    # the great limbs and the crown above them
    top = pts[-1]
    tips = []
    n_l = 5
    for i in range(n_l):
        a = a0 + 0.6 + 2 * math.pi * i / n_l + rng.uniform(-0.3, 0.3)
        out = v3((math.cos(a), math.sin(a), 0.0))
        L = crown_w * s * rng.uniform(0.75, 0.95)
        p0 = top - v3((0, 0, 0.12 * s))
        p1 = p0 + out * L * 0.4 + v3((0, 0, h * 0.13))
        p2 = p0 + out * L * 0.85 + v3((0, 0, h * 0.2 + rng.uniform(-0.05, 0.05) * s))
        f.add(Chain([p0, p1, p2], [r0 * 0.6, r0 * 0.38, r0 * 0.16], k=0.02, **wob(6.0 / s, 0.008 * s, seed * 7 + i)), k=0.05 * s)
        tips.append(p2)
        for j in range(2):                                      # boughs off each limb
            bq = a + rng.uniform(-1.0, 1.0)
            ob = v3((math.cos(bq), math.sin(bq), 0.0))
            q0 = p1 + (p2 - p1) * rng.uniform(0.0, 0.5)
            q1 = q0 + ob * L * 0.35 + v3((0, 0, h * 0.05))
            f.add(RoundCone(q0, q1, r0 * 0.14, r0 * 0.06), k=0.015 * s)
            tips.append(q1)
    zc = top[2] + h * 0.2
    ctr = v3((top[0], top[1], zc))
    for j, q in enumerate(tips):                                # clumps round the bough ends: the crown's broad layer
        for k in range(2):
            o = v3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.5))) * 0.16 * s
            r = s * rng.uniform(0.3, 0.42)
            c.add(Ellipsoid(q + o + v3((0, 0, 0.08 * s)), (r, r * 0.92, r * 0.55), **wob(9.0 / s, 0.04 * s, seed * 100 + j * 3 + k)), k=0.08 * s)
    W = crown_w * s
    rings = [(0.0, 1), (0.48, 6), (0.86, 10)]                   # filling it out into a broad, gently domed umbrella
    for ri, (fr, cnt) in enumerate(rings):
        for j in range(cnt):
            aa = a0 + 2 * math.pi * (j + 0.5 * ri) / cnt + rng.uniform(-0.2, 0.2)
            rr = W * fr * rng.uniform(0.9, 1.08)
            q = ctr + v3((math.cos(aa) * rr, math.sin(aa) * rr, dome * s * (1.0 - fr ** 2) + rng.uniform(-0.05, 0.05) * s))
            r = s * (rng.uniform(0.4, 0.5) if ri < 2 else rng.uniform(0.3, 0.4))
            c.add(Ellipsoid(q, (r, r * 0.95, r * 0.55), **wob(9.0 / s, 0.045 * s, seed * 200 + ri * 20 + j)), k=0.09 * s)
    # lianas: hanging from the crown's edge, some looping between two points under it, one winding up the trunk
    zb = zc - 0.2 * s
    for i in range(vines):
        aa = a0 + 2 * math.pi * (i + 0.5) / vines + rng.uniform(-0.25, 0.25)
        rr = W * rng.uniform(0.62, 0.92)
        p0 = v3((ctr[0] + math.cos(aa) * rr, ctr[1] + math.sin(aa) * rr, zb - 0.1 * s * (rr / W)))
        if i % 3 == 2:                                          # a loop sagging between two points under the crown
            bb = aa + rng.uniform(0.5, 0.8)
            p1 = v3((ctr[0] + math.cos(bb) * rr * 0.9, ctr[1] + math.sin(bb) * rr * 0.9, zb - 0.05 * s))
            sag = rng.uniform(0.45, 0.85) * s
            P = [p0 + (p1 - p0) * t + v3((0, 0, -sag * 4 * t * (1 - t))) for t in np.linspace(0, 1, 9)]
            rad = 0.017 * s
        else:
            Lh = (p0[2] - 0.15) * rng.uniform(0.3, 0.9)
            P = hang(p0, Lh, 0.07 * s, seed * 30 + i)
            rad = rng.uniform(0.012, 0.018) * s
        vn.add(Chain(P, [rad] * len(P), k=0.004), k=0.004)
        for j in range(1, len(P)):                              # leafy tufts along it
            if rng.uniform() < 0.5:
                q = P[j]
                for _ in range(2):
                    dd = unit(v3((rng.normal(), rng.normal(), rng.uniform(-0.3, 0.6))))
                    vl.add(Ellipsoid(q + dd * 0.04 * s, (0.055 * s, 0.032 * s, 0.012 * s), R=R_xz(dd, (0, 0, 1))), k=0.01)
    spiral = []                                                 # the liana winding up the trunk into the crown
    for k in range(26):
        t = k / 25
        z = 0.05 + t * (Ht - 0.1)
        ang = a0 + t * 2 * math.pi * 1.6
        base = at_height(pts, z)
        rr = r0 * (1.05 - 0.35 * t) + 0.012 * s
        spiral.append(base + v3((math.cos(ang) * rr, math.sin(ang) * rr, 0.0)))
    vn.add(Chain(spiral, [0.02 * s] * len(spiral), k=0.004), k=0.004)
    for k in range(3, 26, 4):
        q = spiral[k]
        dd = unit(v3((q[0] - pts[0][0], q[1] - pts[0][1], 0.3)))
        vl.add(Ellipsoid(q + dd * 0.035 * s, (0.06 * s, 0.035 * s, 0.012 * s), R=R_xz(dd, (0, 0, 1))), k=0.01)
    for i in range(2):                                          # epiphytes in the forks: spiky tufts
        q = tips[i * 3] * 0.45 + top * 0.55 + v3((0, 0, 0.04 * s))
        for k in range(7):
            aa = 2 * math.pi * k / 7
            dd = v3((math.cos(aa) * 0.6, math.sin(aa) * 0.6, 0.8))
            vl.add(RoundCone(q, q + unit(dd) * 0.12 * s, 0.018 * s, 0.004), k=0.008)
    ground_cut(f, -0.05)
    return [("Trunk", f, fine(0.008, 0.016), "jungle_bark"), ("Leaves", c, vx(h) * 0.85, "jungle_leaves"),
            ("Vines", vn, fine(0.007, 0.012), "liana"), ("VineLeaves", vl, fine(0.006, 0.012), "vine_leaves")]


# ------------------------------------------------------------------------------------------------ palms and plants
def coco_frond(blades, ribs, base, az, el, L, droop, W0, th, teeth=14, K=11, fold=-0.25, sp=0.06):
    """A coconut frond: a long rib arching out and drooping, its leaflets narrow (fine grooves), hanging down off the rib
    (fold < 0) rather than held up in a V as the date palm's."""
    d0 = v3((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    S = [i / K for i in range(K + 1)]
    pts = [base + d0 * (L * s) + v3((0, 0, -droop * L * s * s)) for s in S]
    ribs.add(Chain(pts, [0.026 - 0.02 * s for s in S], k=0.01))
    Lf = sum(float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(K))
    for i in range(K):
        if S[i + 1] <= 0.12:
            continue
        p0, p1 = pts[i], pts[i + 1]
        t, b, n = frame(p1 - p0)
        Ls = float(np.linalg.norm(p1 - p0))
        for side in (-1, 1):
            q = unit(b * (side * math.cos(fold)) + n * math.sin(fold))
            blades.add(_half_blade(p0, t, q, Ls, S[i], S[i + 1], Lf, W0, teeth, th, sp=sp, groove=0.007, depth=0.55))
    return pts


def coconut_palm(h=3.1, seed=0, lean=0.42, n_fronds=13, nuts=True):
    """A coconut palm: a slender grey trunk ringed with leaf scars, swelling at its foot, leaning out and curving up; a
    crown of long arching fronds drooping toward their tips (one dead and hanging), coconuts clustered under it."""
    rng = np.random.default_rng(seed)
    a0 = rng.uniform(0, 2 * math.pi)
    d = v3((math.cos(a0), math.sin(a0), 0.0))
    N = 12
    th0 = lean
    P = [v3((0, 0, -0.1))]
    seg = h / (N - 1)
    for i in range(1, N):
        t = i / (N - 1)
        ang = th0 * (1.0 - 0.8 * t)
        P.append(P[-1] + d * (seg * math.sin(ang)) + v3((0, 0, seg * math.cos(ang))))
    P[0] = v3((0, 0, -0.1))
    T = P[-1]
    radii = [0.15] + [0.115 - 0.035 * (i / (N - 1)) for i in range(1, N)]
    f = Field("Trunk")
    f.add(Chain(P, radii, k=0.05, **ring_scars(h * 1.1, 0.075, 0.016, None)))
    f.add(Ellipsoid((0, 0, 0.02), (0.2, 0.2, 0.2), **wob(6.0, 0.012, seed)), k=0.12)                 # the swollen foot
    for i in range(7):                                          # a mat of roots round it
        a = 2 * math.pi * i / 7 + rng.uniform(-0.3, 0.3)
        f.add(Ellipsoid((0.2 * math.cos(a), 0.2 * math.sin(a), 0.0), (0.08, 0.05, 0.045), R=Rz(a)), k=0.04)
    f.add(Ellipsoid(T + v3((0, 0, 0.03)), (0.13, 0.13, 0.17)), k=0.06)                                # the heart of the crown
    for i in range(10):                                         # the boots of old fronds round the top
        a = 2 * math.pi * i / 10 + rng.uniform(-0.2, 0.2)
        b0 = T + v3((0.05 * math.cos(a), 0.05 * math.sin(a), -0.12 - 0.05 * (i % 2)))
        f.add(RoundCone(b0, b0 + v3((0.16 * math.cos(a), 0.16 * math.sin(a), -0.12)), 0.05, 0.02), k=0.02)
    ground_cut(f, -0.04)
    out = [("Trunk", f, fine(0.008, 0.016), "coco_bark")]
    blades, ribs = Field("Fronds"), Field("Ribs")
    s = h / 3.1
    th = max(0.011, fine(0.0058, 0.011))
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n_fronds):
        u = i / max(n_fronds - 1, 1)
        az = a0 + i * golden + rng.uniform(-0.15, 0.15)
        el = math.radians(52 - 78 * u) + rng.uniform(-0.08, 0.08)
        L = (1.25 + 0.4 * math.sin(u * math.pi * 0.9)) * s * rng.uniform(0.92, 1.06)
        droop = (0.45 + 0.6 * u) * rng.uniform(0.85, 1.15)
        base = T + v3((0.05 * math.cos(az), 0.05 * math.sin(az), 0.06 - 0.1 * u))
        coco_frond(blades, ribs, base, az, el, L, droop, 0.2 * s, th)
    out.append(("Fronds", blades, fine(0.0058, 0.011), "frond"))
    out.append(("Ribs", ribs, fine(0.006, 0.012), "frond_rib"))
    dead = Field("Dead")                                        # a dead frond hanging down the trunk
    az = a0 + math.pi + 0.4
    hz = v3((math.cos(az), math.sin(az), 0.0))
    p0 = T + hz * 0.08 + v3((0, 0, -0.1))
    pts = [p0, p0 + hz * 0.18 + v3((0, 0, -0.2)), p0 + hz * 0.24 + v3((0, 0, -0.65)), p0 + hz * 0.22 + v3((0, 0, -1.0))]
    dead.add(Chain(pts, [0.022, 0.018, 0.014, 0.008], k=0.01))
    for k in range(1, 3):
        t, b, n = frame(pts[k + 1] - pts[k])
        for side in (-1, 1):
            q = unit(b * side * 0.5 - hz * 0.2 + n * 0.1)
            dead.add(_half_blade(pts[k], t, q, float(np.linalg.norm(pts[k + 1] - pts[k])), 0.2 + 0.35 * (k - 1), 0.55 + 0.35 * (k - 1),
                                 1.0, 0.13, 10, th, sp=0.06, groove=0.007, depth=0.55))
    out.append(("Dead", dead, fine(0.006, 0.012), "frond_dry"))
    if nuts:
        cn = Field("Nuts")
        for k in range(8):
            a = a0 + 2 * math.pi * k / 8 + rng.uniform(-0.3, 0.3)
            rr = rng.uniform(0.1, 0.15)
            q = T + v3((math.cos(a) * rr, math.sin(a) * rr, -0.1 - rng.uniform(0.0, 0.1)))
            cn.add(Ellipsoid(q, (0.075, 0.075, 0.085), R=rot_from_axes(z_axis=unit(q - T + v3((0, 0, -0.1))))), k=0.01)
        out.append(("Nuts", cn, fine(0.006, 0.012), "coconut"))
    return out


def banana(seed=0, s=1.0):
    """A banana plant: three green pseudostems blotched dark, their great paddle leaves arching out and drooping (torn
    in strips at the edges, a pale midrib), an old leaf hanging dry and brown down the tallest, which carries a bunch of
    green bananas on a curving stalk ending in the purple heart."""
    rng = np.random.default_rng(seed)
    st, lf, rb = Field("Stems"), Field("Leaves"), Field("Ribs")
    dry, fr, bud = Field("Dry"), Field("Fruit"), Field("Bud")
    stems = [((0.0, 0.0), 1.25 * s, 6), ((0.26, 0.12), 0.85 * s, 5), ((-0.14, 0.24), 0.55 * s, 4)]
    th = max(0.0065, fine(0.0045, 0.009) * 0.75)
    for si, ((x, y), hh, nl) in enumerate(stems):
        b0 = v3((x, y, -0.04))
        top = v3((x + rng.uniform(-0.03, 0.03), y + rng.uniform(-0.03, 0.03), hh))
        st.add(RoundCone(b0, top, 0.085 * s * (1.0 if si == 0 else 0.8), 0.055 * s * (1.0 if si == 0 else 0.8), **wob(8.0, 0.006, seed + si)), k=0.03)
        a0 = rng.uniform(0, 2 * math.pi)
        for k in range(nl):
            az = a0 + k * 2.39996 + rng.uniform(-0.2, 0.2)
            hz = v3((math.cos(az), math.sin(az), 0.0))
            sd = v3((-math.sin(az), math.cos(az), 0.0))
            el = math.radians(rng.uniform(35, 62) if k < nl - 1 else 78)
            pl = rng.uniform(0.16, 0.26) * s                    # the petiole
            p0 = top + v3((0, 0, -0.04))
            p1 = p0 + unit(hz * math.cos(el) + v3((0, 0, math.sin(el)))) * pl
            st.add(RoundCone(p0, p1, 0.022 * s, 0.015 * s), k=0.015)
            L = rng.uniform(0.75, 0.95) * s * (0.85 if si == 2 else 1.0)
            W = rng.uniform(0.12, 0.15) * s
            el2 = el - math.radians(28)
            u = unit(hz * math.cos(el2) + v3((0, 0, math.sin(el2))))
            nrm_hint = unit(np.cross(u, sd))
            bend = -rng.uniform(0.5, 0.85) / s                  # drooping toward its tip
            twist = rng.uniform(-0.25, 0.25)
            v = unit(sd * math.cos(twist) + nrm_hint * math.sin(twist))
            lf.add(leaf(p1, u, v, paddle(L, W, rng, tears=0.45), th, bend=bend if np.dot(np.cross(u, v), (0, 0, 1)) > 0 else -bend,
                        cup=0.6), k=0.0)
            nn = np.cross(u, unit(v - u * np.dot(v, u)))
            b2 = bend if nn[2] > 0 else -bend
            rb.add(leaf_mid(p1, u, v, 0.0, L * 0.97, b2, 0.011 * s, 0.004 * s), k=0.0)
        if si == 0:
            # an old leaf hanging dry down the stem
            az = a0 + 1.2
            hz = v3((math.cos(az), math.sin(az), 0.0))
            sd = v3((-math.sin(az), math.cos(az), 0.0))
            p0 = top + v3((0, 0, -0.08)) + hz * 0.06
            dry.add(leaf(p0, unit(hz * 0.25 + v3((0, 0, -1.0))), sd, paddle(0.62 * s, 0.07 * s, rng, tears=0.7), th * 1.2, cup=1.4), k=0.0)
            # the bunch on its curving stalk, the purple heart at its end
            az = a0 - 1.9
            hz = v3((math.cos(az), math.sin(az), 0.0))
            sp = [top + v3((0, 0, -0.02)), top + hz * 0.18 + v3((0, 0, 0.04)), top + hz * 0.3 + v3((0, 0, -0.18)),
                  top + hz * 0.32 + v3((0, 0, -0.5)), top + hz * 0.3 + v3((0, 0, -0.62))]
            st.add(Chain(sp, [0.022 * s, 0.02 * s, 0.018 * s, 0.015 * s, 0.012 * s], k=0.01), k=0.01)
            for hk in range(4):                                 # hands of bananas, curving up off the stalk
                q = at_height(list(reversed(sp[2:4])), 0.0) if False else sp[2] + (sp[3] - sp[2]) * (0.12 + 0.24 * hk)
                for j in range(7):
                    aa = 2 * math.pi * j / 7 + hk * 0.45
                    o = v3((math.cos(aa), math.sin(aa), 0.0))
                    fr.add(Chain([q + o * 0.03 * s, q + o * 0.09 * s + v3((0, 0, 0.0)), q + o * 0.12 * s + v3((0, 0, 0.07 * s))],
                                 [0.017 * s, 0.019 * s, 0.012 * s], k=0.006), k=0.004)
            bq = sp[4] + v3((0, 0, -0.08 * s))
            bud.add(Ellipsoid(bq, (0.05 * s, 0.05 * s, 0.1 * s)), k=0.0)
            bud.add(RoundCone(bq + v3((0, 0, -0.05 * s)), bq + v3((0, 0, -0.16 * s)), 0.035 * s, 0.006), k=0.02)
    ground_cut(st)
    return [("Stems", st, fine(0.006, 0.012), "banana_stem"), ("Leaves", lf, fine(0.0045, 0.009), "banana_leaf"),
            ("Ribs", rb, fine(0.0045, 0.009), "banana_rib"), ("Dry", dry, fine(0.0045, 0.009), "frond_dry"),
            ("Fruit", fr, fine(0.005, 0.01), "bananas"), ("Bud", bud, fine(0.005, 0.01), "banana_bud")]


def tree_fern(h=1.0, seed=0, n=10):
    """A tree fern: a short shaggy trunk studded with old frond bases, a crown of long fronds arching out (their pinnae
    fine-cut), fiddleheads unrolling in the middle."""
    rng = np.random.default_rng(seed)
    f = Field("Trunk")
    lean = v3((rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08), 0.0))
    T = v3((0, 0, h)) + lean
    f.add(RoundCone((0, 0, -0.06), T, 0.11, 0.085, **wob(14.0, 0.012, seed)), k=0.0)
    f.add(Ellipsoid((0, 0, 0.03), (0.17, 0.17, 0.12), **wob(8.0, 0.012, seed + 1)), k=0.06)
    for k in range(14):                                         # old frond bases
        z = rng.uniform(0.15, h - 0.08)
        a = rng.uniform(0, 2 * math.pi)
        c = v3((0, 0, z)) + lean * (z / h)
        f.add(RoundCone(c, c + v3((math.cos(a) * 0.12, math.sin(a) * 0.12, -0.05)), 0.03, 0.012), k=0.02)
    f.add(Ellipsoid(T + v3((0, 0, 0.02)), (0.1, 0.1, 0.07)), k=0.03)
    ground_cut(f)
    blades, ribs = Field("Fronds"), Field("Ribs")
    th = max(0.0105, fine(0.0055, 0.0105))
    a0 = rng.uniform(0, 2 * math.pi)
    for i in range(n):
        az = a0 + 2 * math.pi * i / n + rng.uniform(-0.15, 0.15)
        el = math.radians(rng.uniform(28, 48))
        L = rng.uniform(0.85, 1.05)
        base = T + v3((0.04 * math.cos(az), 0.04 * math.sin(az), 0.02))
        coco_frond(blades, ribs, base, az, el, L, rng.uniform(0.55, 0.8), 0.17, th, teeth=18, K=10, fold=0.05, sp=0.04)
    fh = Field("Fiddleheads")                                   # unrolling crosiers
    for k in range(3):
        a = a0 + k * 2.1
        c = T + v3((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.1 + 0.03 * k))
        fh.add(RoundCone(T, c, 0.012, 0.012), k=0.005)
        fh.add(Torus(c + v3((0, 0, 0.03)), 0.03, 0.011, R=rot_from_axes(z_axis=(-math.sin(a), math.cos(a), 0))), k=0.006)
    return [("Trunk", f, fine(0.007, 0.014), "fern_trunk"), ("Fronds", blades, fine(0.0055, 0.0105), "fern"),
            ("Ribs", ribs, fine(0.006, 0.012), "frond_rib"), ("Fiddleheads", fh, fine(0.005, 0.01), "fern")]


def big_leaves(seed=0, s=1.0):
    """A clump of big-leaved aroids: elephant ears standing up behind on long stalks (broad hearts, the tips hanging),
    monstera in front, held flatter (their leaves split from the edge and holed), all glossy deep green."""
    rng = np.random.default_rng(seed)
    st, lf, rb = Field("Stalks"), Field("Leaves"), Field("Ribs")
    th = max(0.0065, fine(0.0045, 0.009) * 0.75)
    specs = []
    for k in range(4):                                          # elephant ears at the back (+Y), tall
        az = math.pi / 2 + (k - 1.5) * 0.55 + rng.uniform(-0.15, 0.15)
        specs.append(("ear", az, rng.uniform(0.75, 0.95) * s, rng.uniform(0.4, 0.48) * s))
    for k in range(5):                                          # monstera in front (-Y), lower and flatter
        az = -math.pi / 2 + (k - 2) * 0.62 + rng.uniform(-0.15, 0.15)
        specs.append(("mon", az, rng.uniform(0.4, 0.55) * s, rng.uniform(0.36, 0.44) * s))
    for kind, az, hh, L in specs:
        hz = v3((math.cos(az), math.sin(az), 0.0))
        sd = v3((-math.sin(az), math.cos(az), 0.0))
        b0 = hz * 0.05 * s + v3((0, 0, -0.03))
        top = hz * (0.2 if kind == "ear" else 0.34) * s + v3((0, 0, hh))
        mid = (b0 + top) / 2 + hz * (0.03 if kind == "ear" else 0.08) * s + v3((0, 0, 0.04 * s))
        st.add(Chain([b0, mid, top], [0.02 * s, 0.017 * s, 0.013 * s], k=0.005), k=0.01)
        if kind == "ear":                                       # the blade hangs from its stalk, tip down and out
            u = unit(hz * 0.5 + v3((0, 0, -0.86)))
            poly = heart(L, L * 0.42)
            bend = -0.2 / s
        else:
            u = unit(hz * 0.85 + v3((0, 0, -0.5)))
            poly = monstera_leaf(L, L * 0.42, rng)
            bend = -0.5 / s
        v = sd
        nn = np.cross(u, v)
        if nn[2] < 0:
            v = -v
        holes = []
        if kind == "mon":
            for j in range(4):
                aa = L * rng.uniform(0.25, 0.62)
                holes.append((aa, rng.choice([-1, 1]) * L * rng.uniform(0.09, 0.15), 0.018 * s))
        lf.add(leaf(top, u, v, poly, th, bend=bend, cup=(1.0 if kind == "ear" else 0.5), holes=holes), k=0.0)
        rb.add(leaf_mid(top, u, v, 0.0, L * 0.95, bend, 0.009 * s, 0.003 * s), k=0.0)
    ground_cut(st)
    return [("Stalks", st, fine(0.005, 0.01), "aroid_stalk"), ("Leaves", lf, fine(0.0045, 0.009), "aroid"),
            ("Ribs", rb, fine(0.0045, 0.009), "aroid_rib")]


def heliconia(seed=0, s=1.0):
    """Heliconia: tall paddle leaves on upright stalks, and flower spikes standing among them: boat-shaped bracts
    alternating up a zigzag stem, scarlet, their lips gold edged with green."""
    rng = np.random.default_rng(seed)
    st, lf, rb, fl = Field("Stalks"), Field("Leaves"), Field("Ribs"), Field("Bracts")
    th = max(0.0065, fine(0.0045, 0.009) * 0.75)
    a0 = rng.uniform(0, 2 * math.pi)
    for k in range(6):
        az = a0 + k * 2.39996 + rng.uniform(-0.2, 0.2)
        hz = v3((math.cos(az), math.sin(az), 0.0))
        sd = v3((-math.sin(az), math.cos(az), 0.0))
        hh = rng.uniform(0.45, 0.7) * s
        b0 = hz * 0.04 + v3((0, 0, -0.03))
        top = hz * 0.12 * s + v3((0, 0, hh))
        st.add(RoundCone(b0, top, 0.016 * s, 0.011 * s), k=0.01)
        u = unit(hz * 0.45 + v3((0, 0, 0.9)))
        L = rng.uniform(0.5, 0.65) * s
        v = sd if np.cross(u, sd)[2] >= 0 else -sd
        lf.add(leaf(top, u, v, lance(L, 0.12 * s), th, bend=-0.6 / s, cup=0.8), k=0.0)
        rb.add(leaf_mid(top, u, v, 0.0, L * 0.95, -0.6 / s, 0.007 * s, 0.003 * s), k=0.0)
    for k in range(3):                                          # the flower spikes
        az = a0 + 0.9 + k * 2.1
        hz = v3((math.cos(az), math.sin(az), 0.0))
        sd = v3((-math.sin(az), math.cos(az), 0.0))
        b0 = hz * 0.06 + v3((0, 0, -0.03))
        zs = rng.uniform(0.55, 0.78) * s
        top = hz * 0.1 + v3((0, 0, zs))
        st.add(RoundCone(b0, top - v3((0, 0, 0.2 * s)), 0.014 * s, 0.012 * s), k=0.008)
        nb = 6
        prev = top - v3((0, 0, 0.2 * s))
        for j in range(nb):
            t = j / (nb - 1)
            side = 1 if j % 2 == 0 else -1
            node = top - v3((0, 0, 0.2 * s)) + v3((0, 0, 0.32 * s * t)) + sd * side * 0.012
            st.add(RoundCone(prev, node, 0.012 * s, 0.01 * s), k=0.005, label=6)
            prev = node
            out = unit(sd * side * 0.9 + v3((0, 0, 0.45)))
            Lb = 0.17 * s * (1.0 - 0.4 * t)
            c = node + out * Lb * 0.5
            R = R_xz(out, (0, 0, 1))
            fl.add(Ellipsoid(c, (Lb * 0.55, 0.042 * s * (1 - 0.3 * t), 0.03 * s), R=R), k=0.004)
            fl.add(RoundCone(c + R @ v3((Lb * 0.35, 0, 0.004)), c + R @ v3((Lb * 0.62, 0, 0.03 * s)), 0.016 * s, 0.003), k=0.01)
            fl.sub(Ellipsoid(c + R @ v3((0.0, 0.0, 0.022 * s)), (Lb * 0.46, 0.03 * s * (1 - 0.3 * t), 0.02 * s), R=R), k=0.003)
            fl.paint(Sphere(node + out * Lb * 0.95, Lb * 0.32), 5)          # gold lips
            fl.paint(Sphere(node + out * Lb * 1.05, Lb * 0.12), 6)          # green tips
    ground_cut(st)
    return [("Stalks", st, fine(0.005, 0.01), "aroid_stalk"), ("Leaves", lf, fine(0.0045, 0.009), "heli_leaf"),
            ("Ribs", rb, fine(0.0045, 0.009), "aroid_rib"), ("Bracts", fl, fine(0.004, 0.008), "heli_flower")]


def bromeliad(seed=0, s=1.0):
    """A bromeliad: a rosette of strap leaves, glossy green, arching out from a red heart, a spike of scarlet bracts
    tipped gold standing up out of it."""
    rng = np.random.default_rng(seed)
    lv, sp = Field("Leaves"), Field("Spike")
    golden = math.pi * (3 - math.sqrt(5))
    n = 18
    a0 = rng.uniform(0, 2 * math.pi)
    for i in range(n):
        u = (i + 0.5) / n
        az = a0 + i * golden
        hz = v3((math.cos(az), math.sin(az), 0))
        el = math.radians(75 - 55 * u ** 0.8 + rng.uniform(-5, 5))
        L = s * (0.22 + 0.2 * u ** 0.6) * rng.uniform(0.92, 1.08)
        Wb = s * (0.045 + 0.012 * u)
        d0 = unit(hz * math.cos(el) + v3((0, 0, math.sin(el))))
        K = 8
        P, W, T = [], [], []
        for k in range(K + 1):
            t = k / K
            P.append(hz * (0.015 * s) + v3((0, 0, 0.02)) + d0 * (L * t) + v3((0, 0, -L * 0.55 * t * t * (1.0 - 0.5 * math.sin(el)))))
            W.append(Wb * (1.0 - t) ** 0.3 * (0.8 + 0.2 * math.sin(min(1.0, t * 4.0) * math.pi / 2)) + 0.004)
            T.append(s * (0.012 - 0.006 * t))
        lv.add(_blade(P, W, T, (-math.sin(az), math.cos(az), 0), channel=1.2), k=0.008 * s)
    lv.paint(Ellipsoid((0, 0, 0.05 * s), (0.11 * s, 0.11 * s, 0.1 * s)), 5)           # the red heart
    ctr = v3((0, 0, 0.05 * s))
    sp.add(RoundCone(ctr, ctr + v3((0, 0, 0.22 * s)), 0.02 * s, 0.014 * s), k=0.0)
    for j in range(9):
        t = j / 8
        aa = j * 2.4
        q = ctr + v3((0, 0, 0.1 * s + 0.15 * s * t))
        dd = unit(v3((math.cos(aa), math.sin(aa), 0.9)))
        sp.add(Ellipsoid(q + dd * 0.025 * s, (0.035 * s * (1 - 0.4 * t), 0.016 * s, 0.012 * s), R=R_xz(dd, (0, 0, 1))), k=0.006)
        sp.paint(Sphere(q + dd * 0.05 * s, 0.014 * s), 5)
    ground_cut(lv, -0.03)
    return [("Leaves", lv, fine(0.004, 0.008) * s, "brom"), ("Spike", sp, fine(0.004, 0.008) * s, "heli_flower")]


# ------------------------------------------------------------------------------------------------ jungle floor
def jungle_log(seed=0, L=1.7, r=0.17):
    """A fallen trunk rotting on the forest floor: thick, mossy on top, its broken end jagged, the other end hollow and
    dark inside; shelves of bracket fungus up its side, a branch stub."""
    rng = np.random.default_rng(seed)
    f = Field("Log")
    R = rot_from_axes(z_axis=(1, 0.06, 0))
    f.add(Cylinder((0, 0, r * 0.82), r, L, rr=0.03, R=R, **wob(5.0, 0.012, seed)))
    f.add(RoundCone((0.1, 0.0, r * 1.2), (0.28, -0.18, r * 1.9), 0.06, 0.035), k=0.03)                   # a branch stub
    for k in range(4):                                          # the broken end: jagged
        a = 2 * math.pi * k / 4 + rng.uniform(-0.4, 0.4)
        f.sub(Ellipsoid((L / 2 + 0.02, math.cos(a) * r * 0.6, r * 0.82 + math.sin(a) * r * 0.6), (0.09, 0.07, 0.07)), k=0.02)
    f.sub(Cylinder((-L / 2, 0.0, r * 0.82), r * 0.62, 0.5, R=R), k=0.02)                                  # hollow at the other end
    f.inter(Plane((0, 0, -0.01), (0, 0, -1)))
    d = Field("Hollow")
    d.add(Cylinder((-L / 2 + 0.2, 0.0, r * 0.82), r * 0.6, 0.12, R=R), k=0.0)
    fg = Field("Fungus")
    for k in range(7):                                          # bracket fungi in tiers on its flank
        x = rng.uniform(-L * 0.35, L * 0.3)
        sd = -1 if k < 5 else 1
        z = r * 0.82 + rng.uniform(-0.04, 0.09)
        rr = rng.uniform(0.05, 0.085)
        c = v3((x, sd * (r * 0.95 + rr * 0.35), z))
        fg.add(Ellipsoid(c, (rr, rr * 0.75, rr * 0.28), R=Rz(rng.uniform(-0.3, 0.3))), k=0.0)
    return [("Log", f, fine(0.007, 0.014), "logs_moss"), ("Hollow", d, fine(0.008, 0.016), "dark"),
            ("Fungus", fg, fine(0.004, 0.008), "fungus")]


def jungle_stump(seed=0):
    """A stump: the old trunk broken off on its buttresses, mossy, bracket fungi on one side."""
    rng = np.random.default_rng(seed)
    f = Field("Stump")
    f.add(Cylinder((0, 0, 0.22), 0.2, 0.5, rr=0.04, **wob(5.0, 0.012, seed)))
    for k in range(4):
        a = 2 * math.pi * k / 4 + rng.uniform(-0.3, 0.3)
        f.add(buttress(a, 0.08, 0.32, 0.42, 0.03, seed + k), k=0.03)
    cut_above(f, (0, 0, 0.42), (0.25, 0.1, 1.0), (0.4, 0.4, 0.3), disp=lambda P: NOISE.fbm(P * F32(9.0), 2) * F32(0.05), amp=0.06)
    f.sub(Cylinder((0, 0, 0.52), 0.12, 0.2), k=0.03)
    f.inter(Plane((0, 0, -0.02), (0, 0, -1)))
    fg = Field("Fungus")
    for k in range(4):
        z = 0.15 + 0.08 * k
        rr = 0.07 - 0.008 * k
        fg.add(Ellipsoid((0.0, -0.2 - rr * 0.3, z), (rr, rr * 0.75, rr * 0.28), R=Rz(rng.uniform(-0.3, 0.3))), k=0.0)
    return [("Stump", f, fine(0.007, 0.014), "logs_moss"), ("Fungus", fg, fine(0.004, 0.008), "fungus")]


# ------------------------------------------------------------------------------------------------ jungle landmarks
def _overgrow(out, rng, pts_list, seed, suffix=""):
    """Lianas hanging from the given points (each (p0, length)) with leafy tufts along them (one field per group, so a
    group spread along one side of a building keeps its meshing grid small)."""
    vn, vl = Field("Vines" + suffix), Field("VineLeaves" + suffix)
    for i, (p0, Lh) in enumerate(pts_list):
        P = hang(p0, Lh, 0.05, seed * 13 + i, n=6)
        vn.add(Chain(P, [0.015] * len(P), k=0.004), k=0.004)
        for j in range(1, len(P)):
            if rng.uniform() < 0.6:
                for _ in range(2):
                    dd = unit(v3((rng.normal(), rng.normal(), rng.uniform(-0.3, 0.6))))
                    vl.add(Ellipsoid(P[j] + dd * 0.035, (0.05, 0.03, 0.011), R=R_xz(dd, (0, 0, 1))), k=0.01)
    out.append(("Vines" + suffix, vn, fine(0.007, 0.012), "liana"))
    out.append(("VineLeaves" + suffix, vl, fine(0.006, 0.012), "vine_leaves"))
    return out


def maya_pyramid(seed=0):
    """An overgrown Maya temple pyramid: six steep tiers of grey limestone, each with an apron moulding and inset
    corners, a steep stair up the front (-Y) between sloping balustrades to the shrine on top (a dark doorway under a
    heavy cornice, a sloping roof, a pierced roof comb, traces of red stucco); a strangler fig rooted on the upper tiers,
    its roots poured down the stepped side, lianas hanging off the tier edges, bushes on the terraces, fallen stones."""
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Tiers")
    tiers, TH = 6, 0.48
    hx0, hy0, step, bat = 2.25, 2.0, 0.26, 0.16
    H = tiers * TH
    for k in range(tiers):
        hx, hy = hx0 - step * k, hy0 - step * k
        z0, z1 = k * TH - 0.03, (k + 1) * TH
        f.add(convex_w([((0, 0, z1), (0, 0, 1)), ((0, 0, z0), (0, 0, -1)), ((hx, 0, z0), (1, 0, bat)), ((-hx, 0, z0), (-1, 0, bat)),
                        ((0, hy, z0), (0, 1, bat)), ((0, -hy, z0), (0, -1, bat))],
                       (-hx - 0.2, -hy - 0.2, z0 - 0.1), (hx + 0.2, hy + 0.2, z1 + 0.1), 0.012, 2.0, seed + k), k=0.0)
        e = bat * TH
        f.add(RoundBox((0, 0, z1 - 0.055), (hx - e + 0.035, hy - e + 0.035, 0.05), 0.012), k=0.004)          # the apron
        for sx in (-1, 1):                                      # inset corners
            for sy in (-1, 1):
                f.sub(RoundBox((sx * (hx - e * 0.5), sy * (hy - e * 0.5), (z0 + z1) / 2), (0.13, 0.13, TH * 0.62), 0.012), k=0.01)
        if k % 2 == 1:
            f.paint(RoundBox((0, 0, z1 - 0.055), (hx + 0.1, hy + 0.1, 0.06)), 5)                          # red stucco traces
    # the stair: steep, between sloping balustrades
    Yt = hy0 - step * (tiers - 1) - bat * TH
    Yb = hy0 + 0.7
    nsteps = 26
    rise = H / nsteps
    tread = (Yb - Yt) / nsteps
    hw = 0.52

    def stair(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        kk = np.floor(np.clip(z, 0, H - 1e-4) / F32(rise))
        yf = F32(-Yb) + kk * F32(tread)
        return np.maximum.reduce([np.abs(x) - F32(hw), yf - y, -z, z - F32(H), y]).astype(F32)

    def balustrade(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        zt = (y + F32(Yb)) / F32(Yb - Yt) * F32(H) + F32(0.13)
        return np.maximum.reduce([np.abs(np.abs(x) - F32(hw + 0.09)) - F32(0.09), z - zt, -z, -(y + F32(Yb + 0.04)), y]).astype(F32)
    f.add(Func(stair, (-hw - 0.05, -Yb - 0.05, -0.05), (hw + 0.05, 0.05, H + 0.05)), k=0.0)
    f.add(Func(balustrade, (-hw - 0.25, -Yb - 0.1, -0.05), (hw + 0.25, 0.05, H + 0.3)), k=0.0)
    f.sub(Ellipsoid((hx0 + 0.15, -hy0 - 0.1, 0.25), (1.05, 0.9, 1.15), **wob(3.0, 0.08, seed + 7)), k=0.06)    # a corner fallen in
    ground_cut(f)
    out.append(("Tiers", f, fine(0.02, 0.04), "ruin_stone"))
    # the shrine on top
    sh = Field("Shrine")
    sy0 = 0.05
    sh.add(walls_box(0, sy0, 0.68, 0.5, H - 0.04, H + 0.72, 0.03, 0.006, seed + 20), k=0.0)
    sh.add(RoundBox((0, sy0, H + 0.78), (0.76, 0.58, 0.07), 0.02), k=0.006)                                   # the cornice
    sh.add(convex([((0, sy0, H + 1.08), (0, 0, 1)), ((0, sy0, H + 0.8), (0, 0, -1)), ((0.76, sy0, H + 0.8), (1, 0, 0.6)),
                   ((-0.76, sy0, H + 0.8), (-1, 0, 0.6)), ((0, sy0 + 0.58, H + 0.8), (0, 1, 0.6)), ((0, sy0 - 0.58, H + 0.8), (0, -1, 0.6))],
                  (-0.9, sy0 - 0.7, H + 0.75), (0.9, sy0 + 0.7, H + 1.15)), k=0.004)                            # the sloping roof
    sh.add(RoundBox((0, sy0 + 0.12, H + 1.42), (0.46, 0.07, 0.36), 0.015, **wob(6.0, 0.006, seed + 21)), k=0.01)  # the roof comb
    sh.add(RoundBox((0, sy0 + 0.12, H + 1.8), (0.5, 0.1, 0.035), 0.01), k=0.004)
    for zz in (H + 1.25, H + 1.55):
        for xx in (-0.27, 0.0, 0.27):
            sh.sub(RoundBox((xx, sy0 + 0.12, zz), (0.07, 0.12, 0.07), 0.008), k=0.004)
    sh.sub(RoundBox((0, sy0 - 0.5, H + 0.26), (0.17, 0.12, 0.3), 0.01), k=0.004)                            # the doorway
    for xx in (-0.45, 0.45):                                    # carved masks either side of it
        sh.add(Ellipsoid((xx, sy0 - 0.52, H + 0.42), (0.1, 0.03, 0.12)), k=0.01)
        sh.sub(Ellipsoid((xx - 0.04, sy0 - 0.55, H + 0.47), (0.025, 0.02, 0.018)), k=0.004)
        sh.sub(Ellipsoid((xx + 0.04, sy0 - 0.55, H + 0.47), (0.025, 0.02, 0.018)), k=0.004)
    cut_above(sh, (0.12, sy0 + 0.12, H + 1.58), (0.55, 0.0, 1.0), (0.6, 0.3, 0.45),
              disp=lambda P: (NOISE.fbm(P * F32(10.0), 2) * F32(0.06)).astype(F32), amp=0.07)                 # the comb broken
    sh.paint(RoundBox((0, sy0, H + 0.45), (0.9, 0.7, 0.45)), 5)
    sh.paint(RoundBox((0, sy0 + 0.12, H + 1.5), (0.6, 0.2, 0.4)), 5)
    out.append(("Shrine", sh, fine(0.01, 0.02), "ruin_stone"))
    dk = Field("Dark")
    dk.add(RoundBox((0, sy0 - 0.42, H + 0.26), (0.16, 0.04, 0.28), 0.01), k=0.0)
    out.append(("Dark", dk, fine(0.01, 0.02), "dark"))
    # a strangler fig on the upper tiers (back left), its roots poured down the stepped side
    tb = v3((-0.75, 0.45, 4 * TH))
    tr = jungle_tree(2.3, seed + 40, crown_w=1.05, dome=0.3, vines=4, lean=0.06)
    place_parts(out, [(n, fl, vxs, m) for (n, fl, vxs, m) in tr], tb)
    rt = Field("Roots")
    for i in range(5):
        a = math.pi * (0.55 + 0.22 * i) + rng.uniform(-0.1, 0.1)
        dvec = v3((math.cos(a), math.sin(a), 0.0))
        P = [tb + v3((0, 0, 0.1))]
        for k in range(4, 0, -1):                               # out over each tier's edge and down its face
            hx, hy = hx0 - step * (k - 1), hy0 - step * (k - 1)
            ts = []
            if abs(dvec[0]) > 1e-3:
                ts.append(((hx if dvec[0] > 0 else -hx) - tb[0]) / dvec[0])
            if abs(dvec[1]) > 1e-3:
                ts.append(((hy if dvec[1] > 0 else -hy) - tb[1]) / dvec[1])
            t = max(0.05, min(ts))
            q = v3((tb[0] + dvec[0] * t, tb[1] + dvec[1] * t, k * TH + 0.04))
            P.append(q + v3((0, 0, 0.03)))
            P.append(q + dvec * 0.07 + v3((0, 0, -TH * 0.5)))
        P.append(P[-1] + dvec * 0.3 + v3((0, 0, -0.5)))
        rad = [0.075 - 0.009 * j for j in range(len(P))]
        rt.add(Chain(P, [max(r, 0.025) for r in rad], k=0.03, **wob(10.0, 0.008, seed + 50 + i)), k=0.02)
    ground_cut(rt)
    out.append(("Roots", rt, fine(0.008, 0.016), "jungle_bark"))
    # lianas off the tier edges on the front and sides, bushes on the terraces
    hangs = {"front": [], "left": [], "right": []}
    for i in range(10):
        k = rng.integers(2, tiers)
        hx, hy = hx0 - step * k, hy0 - step * k
        side = ["front", "left", "right"][i % 3]
        if side == "front":
            x = rng.choice([-1, 1]) * rng.uniform(hw + 0.3, max(hw + 0.35, hx - 0.1))
            p0 = v3((x, -hy - 0.04, k * TH + 0.02))
        else:
            sx = -1 if side == "left" else 1
            p0 = v3((sx * (hx + 0.04), rng.uniform(-hy + 0.1, hy - 0.1), k * TH + 0.02))
        hangs[side].append((p0, rng.uniform(0.35, 0.95)))
    for side, pts in hangs.items():
        _overgrow(out, rng, pts, seed, "_" + side[0].upper())
    bu = Field("Bushes")
    for i in range(10):                                         # clumps draping over the tier edges
        k = rng.integers(1, tiers)
        hx, hy = hx0 - step * k, hy0 - step * k
        sx = rng.choice([-1, 1])
        if rng.uniform() < 0.5:
            q = v3((sx * (hx - 0.02), rng.uniform(-hy + 0.2, hy - 0.2), k * TH - 0.05))
        else:
            q = v3((rng.choice([-1, 1]) * rng.uniform(hw + 0.25, max(hw + 0.3, hx - 0.15)), sx * (hy - 0.02), k * TH - 0.05))
        bu.add(Ellipsoid(q, (0.2, 0.2, 0.26), **wob(12.0, 0.025, seed * 5 + i)), k=0.05)
        bu.add(Ellipsoid(q + v3((0, 0, 0.16)), (0.16, 0.16, 0.12), **wob(12.0, 0.025, seed * 5 + i + 50)), k=0.05)
    for i in range(22):
        k = rng.integers(0, tiers)
        hx, hy = hx0 - step * k, hy0 - step * k
        side = rng.integers(0, 4)
        tt = rng.uniform(-1, 1)
        if side == 0:
            q = v3((tt * (hx - 0.15), -(hy - 0.12), (k + 1) * TH))
            if abs(q[0]) < hw + 0.25:
                q[0] = math.copysign(hw + 0.35, q[0] if q[0] != 0 else 1.0)
        elif side == 1:
            q = v3((tt * (hx - 0.15), hy - 0.12, (k + 1) * TH))
        else:
            sx = -1 if side == 2 else 1
            q = v3((sx * (hx - 0.12), tt * (hy - 0.15), (k + 1) * TH))
        for j in range(3):
            o = v3((rng.uniform(-0.14, 0.14), rng.uniform(-0.14, 0.14), rng.uniform(0.02, 0.1)))
            r = rng.uniform(0.12, 0.2)
            bu.add(Ellipsoid(q + o, (r, r * 0.9, r * 0.75), **wob(14.0, 0.02, seed * 9 + i * 3 + j)), k=0.04)
    out.append(("Bushes", bu, fine(0.01, 0.02), "jungle_leaves"))
    fs = Field("Fallen")
    for k in range(6):
        a = rng.uniform(-0.3, 1.2) if k < 4 else rng.uniform(2.2, 3.6)
        rr = rng.uniform(2.5, 3.0)
        q = v3((math.cos(a) * rr * 0.95, -math.sin(a) * rr * 0.9 if k < 4 else math.sin(a) * rr, 0.07))
        fs.add(RoundBox(q, (rng.uniform(0.12, 0.2), rng.uniform(0.09, 0.14), rng.uniform(0.07, 0.11)), 0.025, R=Rz(rng.uniform(0, 3)),
                        **wob(9.0, 0.008, seed + 60 + k)), k=0.0)
    for k in range(14):                                         # the rubble of the fallen corner
        q = v3((hx0 - 0.25 + rng.uniform(-0.45, 0.55), -hy0 + 0.25 + rng.uniform(-0.55, 0.45), 0.0))
        q[2] = max(0.05, 0.42 - 0.35 * math.hypot(q[0] - hx0 + 0.35, q[1] + hy0 - 0.35)) + rng.uniform(0.0, 0.08)
        fs.add(RoundBox(q, (rng.uniform(0.1, 0.18), rng.uniform(0.08, 0.13), rng.uniform(0.06, 0.1)), 0.025,
                        R=Rz(rng.uniform(0, 3)) @ euler(rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 0.0), **wob(9.0, 0.008, seed + 80 + k)), k=0.0)
    ground_cut(fs)
    out.append(("Fallen", fs, fine(0.009, 0.018), "ruin_stone"))
    return mound(out, 3.1, 2.9, 0.16, seed, c=(0, -0.2), voxel=fine(0.025, 0.045))


def _stela_body(f, H, seed):
    """A carved stela on its base: a tall slab, its top rounded, a ruler in relief on its front (-Y: a great feathered
    headdress, the face, a ceremonial bar held across the chest, a skirt), panels of glyph blocks down its sides."""
    f.add(RoundBox((0, 0, H / 2), (0.25, 0.1, H / 2), 0.035, **wob(6.0, 0.006, seed)), k=0.0)
    f.add(Ellipsoid((0, 0, H - 0.02), (0.25, 0.1, 0.12)), k=0.02)
    yf = -0.1
    rel = [Ellipsoid((0, yf, H - 0.2), (0.2, 0.025, 0.14)),                                  # the headdress
           Sphere((0, yf - 0.005, H - 0.4), 0.075),                                           # the face
           RoundBox((0, yf, H - 0.72), (0.11, 0.022, 0.2), 0.03),                             # the body
           RoundCone((-0.17, yf - 0.02, H - 0.66), (0.17, yf - 0.02, H - 0.66), 0.035, 0.035),  # the ceremonial bar
           RoundBox((0, yf, H - 1.0), (0.14, 0.02, 0.1), 0.02)]                               # the skirt
    for i in range(5):                                                                        # the feathers fanning out
        a = math.pi * (0.15 + 0.175 * i)
        rel.append(Ellipsoid((math.cos(a) * 0.15, yf - 0.006, H - 0.2 + math.sin(a) * 0.09), (0.035, 0.018, 0.08),
                             R=rot_from_axes(z_axis=(math.cos(a), 0, math.sin(a) + 0.4), y_axis=(0, 1, 0))))
    for p in rel:
        f.add(p, k=0.006)
    f.sub(Ellipsoid((-0.03, yf - 0.07, H - 0.4), (0.014, 0.01, 0.01)), k=0.003)
    f.sub(Ellipsoid((0.03, yf - 0.07, H - 0.4), (0.014, 0.01, 0.01)), k=0.003)
    for sx in (-1, 1):                                                                        # glyph blocks down the sides
        for row in range(6):
            for col in range(2):
                z = H - 0.25 - row * 0.17
                y = -0.045 + col * 0.09
                f.sub(RoundBox((sx * 0.25, y, z), (0.012, 0.035, 0.06), 0.01), k=0.004)
                f.add(Ellipsoid((sx * 0.245, y, z), (0.01, 0.022, 0.035)), k=0.004)


def stela(seed=0, broken=False):
    """A carved stela (see _stela_body) on its low base, a round altar stone before it; broken: snapped off across, its
    top lying face up beside the stump among a few fragments."""
    rng = np.random.default_rng(seed)
    H = 1.35
    st = Field("Stone")
    st.add(RoundBox((0, 0.02, 0.06), (0.36, 0.24, 0.08), 0.025, **wob(6.0, 0.008, seed)), k=0.0)
    body = Field("Body")
    _stela_body(body, H, seed)
    if not broken:
        place(st, body, (0, 0, 0.12), rot_from_axes(z_axis=(0.03, 0.04, 1.0)))
    else:
        zc = 0.55
        nrm = (0.35, 0.15, 1.0)
        brk = lambda P: (NOISE.fbm(P * F32(11.0), 2) * F32(0.05)).astype(F32)
        low = Field("Low")
        place(low, body, (0, 0, 0.0))
        cut_above(low, (0, 0, zc), nrm, (0.4, 0.3, 1.0), disp=brk, amp=0.06)
        place(st, low, (0, 0, 0.12))
        top = Field("Top")
        place(top, body, (0, 0, 0.0))
        cut_above(top, (0, 0, zc), tuple(-x for x in nrm), (0.4, 0.3, 1.0), disp=brk, amp=0.06)
        R = Rz(2.7) @ euler(-math.pi / 2 + 0.08, 0.0, 0.0)
        place(st, top, (0.75, 0.25, 0.1 - zc * 0.0 + 0.0), R)
        for k in range(4):
            q = v3((rng.uniform(-0.2, 0.9), rng.uniform(-0.55, 0.6), 0.04))
            st.add(RoundBox(q, (rng.uniform(0.04, 0.08), rng.uniform(0.03, 0.06), 0.04), 0.015, R=Rz(rng.uniform(0, 3)),
                            **wob(14.0, 0.006, seed + 30 + k)), k=0.0)
    alt = v3((0.0, -0.55, 0.0))                                # the altar: a drum of stone, carved round its rim
    st.add(Cylinder(alt + v3((0, 0, 0.11)), 0.27, 0.24, rr=0.03, **wob(7.0, 0.006, seed + 3)), k=0.0)
    st.sub(Torus(alt + v3((0, 0, 0.17)), 0.272, 0.012), k=0.004)
    for k in range(8):
        a = 2 * math.pi * k / 8
        st.add(Ellipsoid(alt + v3((math.cos(a) * 0.265, math.sin(a) * 0.265, 0.09)), (0.02, 0.02, 0.03)), k=0.004)
    ground_cut(st)
    out = [("Stone", st, fine(0.006, 0.012), "ruin_stone")]
    return mound(out, 0.95, 0.9, 0.1, seed, c=(0.15 if broken else 0.0, -0.2), voxel=fine(0.014, 0.025))


def serpent_head(f, c, s=1.0, R=None):
    """A feathered serpent's head carved in stone (the foot of a temple stair): a squared snout with a curl on it, an
    open mouth with fangs, round eyes under heavy brows."""
    R = np.eye(3) if R is None else R
    tmp = Field("Head")
    tmp.add(RoundBox((0, 0, 0.22 * s), (0.24 * s, 0.3 * s, 0.2 * s), 0.07 * s), k=0.0)
    tmp.add(RoundBox((0, -0.24 * s, 0.25 * s), (0.2 * s, 0.14 * s, 0.14 * s), 0.06 * s), k=0.05 * s)      # the snout
    tmp.sub(RoundBox((0, -0.36 * s, 0.17 * s), (0.17 * s, 0.14 * s, 0.045 * s), 0.02 * s), k=0.01 * s)   # the open mouth
    for sx in (-1, 1):
        tmp.add(Sphere((sx * 0.13 * s, -0.12 * s, 0.4 * s), 0.07 * s), k=0.02 * s)                           # eyes
        tmp.sub(Sphere((sx * 0.13 * s, -0.17 * s, 0.41 * s), 0.035 * s), k=0.01 * s)
        tmp.add(RoundCone((sx * 0.1 * s, -0.36 * s, 0.22 * s), (sx * 0.1 * s, -0.38 * s, 0.13 * s), 0.025 * s, 0.006), k=0.006)   # fangs
        tmp.add(Torus((sx * 0.06 * s, -0.33 * s, 0.37 * s), 0.045 * s, 0.014 * s, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.008)  # the curl
    place(f, tmp, c, R)


def ruin_blocks(seed=0):
    """Tumbled blocks from the temple: squared stones carved with glyphs and a mask, lying askew and half sunk, a
    feathered serpent's head among them."""
    rng = np.random.default_rng(seed)
    st = Field("Stone")
    specs = [((-0.35, 0.15), (0.24, 0.2, 0.16), 0.3, (0.1, 0.0)), ((0.2, 0.35), (0.2, 0.17, 0.14), -0.4, (0.0, 0.25)),
             ((0.55, -0.15), (0.17, 0.14, 0.12), 0.9, (-0.2, 0.1)), ((-0.15, -0.45), (0.15, 0.13, 0.11), 1.6, (0.3, -0.2))]
    for i, ((x, y), half, yaw, (tx, ty)) in enumerate(specs):
        R = Rz(yaw) @ euler(tx, ty, 0.0)
        c = v3((x, y, half[2] * 0.75))
        st.add(RoundBox(c, half, 0.03, R=R, **wob(7.0, 0.008, seed + i)), k=0.0)
        fr = R @ v3((0, -1, 0))
        for gx in (-1, 1):                                      # glyph cartouches on a face
            for gz in (-1, 1):
                q = c + R @ v3((gx * half[0] * 0.45, -half[1], gz * half[2] * 0.42))
                st.sub(RoundBox(q, (half[0] * 0.38, 0.012, half[2] * 0.34), 0.012, R=R), k=0.004)
                st.add(Ellipsoid(q + fr * 0.002, (half[0] * 0.2, 0.01, half[2] * 0.2), R=R), k=0.004)
    serpent_head(st, (0.15, -0.95, -0.04), 0.9, Rz(0.35) @ euler(0.12, -0.08, 0.0))
    ground_cut(st)
    out = [("Stone", st, fine(0.007, 0.014), "ruin_stone")]
    return mound(out, 1.15, 1.25, 0.1, seed, c=(0.1, -0.25), voxel=fine(0.014, 0.025))


def watchtower(seed=0):
    """The outpost's watchtower: four timber legs on stone pads, splayed and cross-braced, a ladder up its front to a
    plank platform behind a breastwork of planks, a steep pyramid roof of palm thatch on four posts, a bell under it, the
    crimson-and-gold flag on a pole above."""
    out = []
    wd = Field("Timber")
    zp, B0, B1 = 2.0, 0.58, 0.44
    legs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            a, b = v3((sx * B0, sy * B0, -0.05)), v3((sx * B1, sy * B1, zp))
            legs.append((a, b))
            post(wd, a, b + v3((0, 0, 0.06)), 0.055, 0.048)
    def leg_at(i, z):
        a, b = legs[i]
        t = (z + 0.05) / (zp + 0.05)
        return a + (b - a) * t
    sides = [(0, 1), (2, 3), (0, 2), (1, 3)]
    for (i, j) in sides:                                       # X braces and ties on every side
        for (za, zb) in ((0.2, 1.05), (1.05, 1.9)):
            wd.add(RoundCone(leg_at(i, za), leg_at(j, zb), 0.026, 0.026), k=0.004, label=10)
            wd.add(RoundCone(leg_at(j, za), leg_at(i, zb), 0.026, 0.026), k=0.004, label=10)
        for z in (0.2, 1.05):
            wd.add(RoundCone(leg_at(i, z), leg_at(j, z), 0.03, 0.03), k=0.004, label=10)
    for sy in (-1, 1):                                          # joists and the plank floor
        wd.add(RoundBox((0, sy * B1, zp - 0.04), (B1 + 0.12, 0.045, 0.045), 0.008), k=0.004, label=10)
    for k in range(9):
        x = -0.6 + k * 0.15
        wd.add(RoundBox((x, 0, zp + 0.025), (0.07, 0.66, 0.022), 0.006), k=0.002, label=0)
    hw = 0.66
    for (cx, cy, ax) in ((0, hw, "x"), (-hw, 0, "y"), (hw, 0, "y")):   # the breastwork: upright planks
        n = 9
        for k in range(n):
            t = -hw + 2 * hw * (k + 0.5) / n
            c = (t, cy, zp + 0.25) if ax == "x" else (cx, t, zp + 0.25)
            hz = 0.22 + 0.02 * ((k * 7 + seed) % 3)
            wd.add(RoundBox(c, (0.07, 0.02, hz) if ax == "x" else (0.02, 0.07, hz), 0.008), k=0.002, label=11)
    for sx in (-1, 1):                                          # the front, open for the ladder in the middle
        for k in range(3):
            t = sx * (hw - 0.07 - k * 0.14)
            wd.add(RoundBox((t, -hw, zp + 0.25), (0.07, 0.02, 0.22), 0.008), k=0.002, label=11)
    wd.add(RoundBox((0, hw, zp + 0.47), (hw + 0.03, 0.035, 0.03), 0.008), k=0.004, label=10)
    for sx in (-1, 1):
        wd.add(RoundBox((sx * hw, 0, zp + 0.47), (0.035, hw + 0.03, 0.03), 0.008), k=0.004, label=10)
        wd.add(RoundBox((sx * (hw - 0.22), -hw, zp + 0.47), (0.23, 0.035, 0.03), 0.008), k=0.004, label=10)
    for sx in (-1, 1):                                          # the roof posts
        for sy in (-1, 1):
            post(wd, (sx * (hw - 0.05), sy * (hw - 0.05), zp), (sx * (hw - 0.05), sy * (hw - 0.05), zp + 0.92), 0.035)
    for sx in (-1, 1):                                          # the ladder up the front
        wd.add(RoundCone((sx * 0.17, -1.12, -0.04), (sx * 0.17, -hw - 0.02, zp + 0.42), 0.026, 0.024), k=0.0, label=11)
    for k in range(9):
        t = (k + 0.6) / 10
        p = v3((0, -1.12 + (1.12 - hw - 0.02) * t, -0.04 + (zp + 0.46) * t))
        wd.add(RoundCone(p + v3((-0.17, 0, 0)), p + v3((0.17, 0, 0)), 0.015, 0.015), k=0.0, label=10)
    pole_top = zp + 2.15
    wd.add(RoundCone((0, 0, zp + 1.3), (0, 0, pole_top), 0.022, 0.016), k=0.0, label=11)     # the flagpole
    ground_cut(wd)
    out.append(("Timber", wd, fine(0.005, 0.01), "timber"))
    pads = Field("Pads")
    for sx in (-1, 1):
        for sy in (-1, 1):
            pads.add(RoundBox((sx * B0, sy * B0, 0.03), (0.11, 0.11, 0.07), 0.03, **wob(10.0, 0.008, seed + sx + 3 * sy)), k=0.0)
    ground_cut(pads)
    out.append(("Pads", pads, fine(0.008, 0.016), "jrock"))
    rf = Field("Roof")
    ze, za, hr = zp + 0.86, zp + 1.62, hw + 0.24
    rf.add(pyramid_roof((0, 0), hr, ze, za), k=0.0)
    rf.ops[-1][1].disp = lambda P: (F32(0.012) * np.sin(P[:, 2] * F32(46)) + NOISE.fbm(P * F32(9) + F32(seed), 2) * F32(0.016)).astype(F32)
    rf.ops[-1][1].disp_amp = 0.03
    rf.sub(pyramid_roof((0, 0), hr - 0.08, ze - 0.1, za - 0.16), k=0.01)
    for k in range(16):                                         # a ragged fringe at the eaves
        a = 2 * math.pi * k / 16
        rr = hr / max(abs(math.cos(a)), abs(math.sin(a)))
        rf.add(Ellipsoid((math.cos(a) * rr * 0.97, math.sin(a) * rr * 0.97, ze + 0.02), (0.09, 0.09, 0.05), R=Rz(a)), k=0.02)
    rf.add(RoundCone((0, 0, za - 0.08), (0, 0, za + 0.08), 0.06, 0.03), k=0.02, label=5)
    out.append(("Roof", rf, fine(0.007, 0.014), "palm_thatch"))
    bl = Field("Bell")
    bl.add(RoundCone((0, 0, zp + 0.66), (0, 0, zp + 0.5), 0.045, 0.075), k=0.0)
    bl.add(Torus((0, 0, zp + 0.5), 0.072, 0.012), k=0.006)
    bl.add(RoundCone((0, 0, zp + 0.66), (0, 0, zp + 0.82), 0.008, 0.008), k=0.004)
    out.append(("Bell", bl, fine(0.004, 0.008), "brass"))
    fg = Field("Flag")
    fo = v3((0.02, 0, pole_top - 0.04))
    fg.add(flag(fo, 0.62, 0.4, seed), k=0.0)
    flag_paint(fg, fo, 0.62, 0.4)
    out.append(("Flag", fg, fine(0.004, 0.008), "flag"))
    fn = Field("Finial")
    fn.add(Sphere((0, 0, pole_top + 0.03), 0.035), k=0.0)
    out.append(("Finial", fn, fine(0.004, 0.008), "brass"))
    return out


def stilt_hut(seed=0):
    """A hut on stilts: a floor of planks on posts, walls of split cane, a doorway and a window, a veranda with a rail
    at its front reached by a notched log, a steep roof of palm thatch with ragged eaves; pots under it."""
    rng = np.random.default_rng(seed)
    out = []
    zf, hx, hy, wh = 0.62, 0.62, 0.42, 0.68
    wd = Field("Timber")
    for x in (-0.58, 0.0, 0.58):                               # the stilts
        for y in (-0.72, -0.02, 0.4):
            post(wd, (x, y, -0.05), (x, y, zf), 0.04, 0.036)
    for y in (-0.72, -0.02, 0.4):
        wd.add(RoundBox((0, y, zf - 0.04), (0.7, 0.04, 0.04), 0.008), k=0.003, label=10)
    for k in range(12):                                         # floor planks (running along Y)
        x = -0.66 + k * 0.12
        wd.add(RoundBox((x, -0.17, zf + 0.02), (0.055, 0.62, 0.02), 0.005), k=0.002, label=0)
    for x in (-0.66, -0.2, 0.2, 0.66):                         # the veranda rail
        post(wd, (x, -0.76, zf), (x, -0.76, zf + 0.38), 0.025)
    wd.add(RoundCone((-0.68, -0.76, zf + 0.36), (0.68, -0.76, zf + 0.36), 0.022, 0.022), k=0.003, label=10)
    wd.add(RoundCone((-0.68, -0.76, zf + 0.18), (-0.36, -0.76, zf + 0.18), 0.018, 0.018), k=0.003, label=10)
    wd.add(RoundCone((0.36, -0.76, zf + 0.18), (0.68, -0.76, zf + 0.18), 0.018, 0.018), k=0.003, label=10)
    lg = [v3((0.0, -1.25, -0.03)), v3((0.0, -0.8, zf + 0.02))]   # a notched log up to the veranda
    wd.add(RoundCone(lg[0], lg[1], 0.06, 0.05), k=0.0, label=11)
    for k in range(4):
        t = (k + 0.7) / 5
        q = lg[0] + (lg[1] - lg[0]) * t
        wd.sub(RoundBox(q + v3((0, -0.05, 0.03)), (0.07, 0.03, 0.02), 0.005), k=0.004)
    for sx in (-1, 1):                                          # corner posts of the walls
        for sy in (-1, 1):
            post(wd, (sx * hx, sy * hy + 0.05, zf), (sx * hx, sy * hy + 0.05, zf + wh + 0.05), 0.035)
    ground_cut(wd)
    out.append(("Timber", wd, fine(0.005, 0.01), "timber"))
    w = Field("Walls")
    w.add(RoundBox((0, 0.05, zf + wh / 2 + 0.02), (hx - 0.01, hy - 0.01, wh / 2), 0.01,
                   disp=lambda P: (F32(0.005) * np.sin((P[:, 0] + P[:, 1]) * F32(85))).astype(F32), disp_amp=0.006), k=0.0)
    w.sub(RoundBox((0.18, 0.05 - hy, zf + 0.29), (0.13, 0.06, 0.28), 0.01), k=0.004)          # the doorway
    w.sub(RoundBox((hx, 0.1, zf + 0.42), (0.06, 0.12, 0.1), 0.01), k=0.004)                    # a window
    for z in (zf + 0.08, zf + wh - 0.05):                      # binding rails round the walls
        w.add(RoundBox((0, 0.05, z), (hx + 0.012, hy + 0.012, 0.016), 0.006), k=0.003, label=5)
    out.append(("Walls", w, fine(0.006, 0.012), "cane"))
    dk = Field("Dark")
    dk.add(RoundBox((0.18, 0.05 - hy + 0.06, zf + 0.29), (0.12, 0.03, 0.27), 0.008), k=0.0)
    dk.add(RoundBox((hx - 0.05, 0.1, zf + 0.42), (0.03, 0.11, 0.09), 0.008), k=0.0)
    out.append(("Dark", dk, fine(0.006, 0.012), "dark"))
    rf = Field("Roof")
    ze, zr = zf + wh - 0.02, zf + wh + 0.92
    rf.add(gable((0, 0.05), hx + 0.24, hy + 0.36, ze, zr, axis="x"), k=0.0)
    rf.ops[-1][1].disp = lambda P: (F32(0.012) * np.sin(P[:, 2] * F32(46)) + NOISE.fbm(P * F32(9) + F32(seed), 2) * F32(0.016)).astype(F32)
    rf.ops[-1][1].disp_amp = 0.03
    rf.sub(gable((0, 0.05), hx + 0.3, hy + 0.26, ze - 0.12, zr - 0.14, axis="x"), k=0.01)
    for sy in (-1, 1):                                          # ragged eaves
        for k in range(10):
            x = -hx - 0.2 + k * (2 * hx + 0.4) / 9
            rf.add(Ellipsoid((x, 0.05 + sy * (hy + 0.33), ze + 0.02), (0.09, 0.06, 0.05)), k=0.02)
    rf.add(RoundBox((0, 0.05, zr - 0.02), (hx + 0.2, 0.07, 0.045), 0.035), k=0.03, label=5)
    out.append(("Roof", rf, fine(0.007, 0.014), "palm_thatch"))
    pt = Field("Pots")
    for (x, y, s) in ((-0.35, -0.3, 1.0), (-0.15, -0.38, 0.75), (0.45, 0.2, 0.85)):
        c = v3((x, y, 0))
        pt.add(Ellipsoid(c + v3((0, 0, 0.11 * s)), (0.1 * s, 0.1 * s, 0.11 * s)), k=0.0)
        pt.add(Torus(c + v3((0, 0, 0.21 * s)), 0.045 * s, 0.012 * s), k=0.01)
        pt.sub(Cylinder(c + v3((0, 0, 0.23 * s)), 0.035 * s, 0.08), k=0.005)
    ground_cut(pt)
    out.append(("Pots", pt, fine(0.005, 0.01), "pottery"))
    return out


def dugout(seed=0, L=1.75, W=0.36, D=0.22):
    """A dugout canoe: one log hollowed out, its ends drawn to points and a little raised, a carved handle at each, a
    paddle lying in it."""
    f = Field("Hull")

    def hull(P):
        x = P[:, 0] / F32(L / 2)
        hw = F32(W / 2) * np.sqrt(np.clip(F32(1) - np.abs(x) ** F32(2.6), 0, 1)) + F32(0.003)
        top = F32(D) + F32(0.06) * np.clip(np.abs(x) - F32(0.55), 0, 1) ** 2 * F32(4)
        zc = F32(D * 0.55)
        e_out = np.sqrt((P[:, 1] / np.maximum(hw, F32(1e-3))) ** 2 + ((P[:, 2] - zc) / F32(D * 0.62)) ** 2) - F32(1)
        d_out = np.maximum(e_out * np.minimum(hw, F32(D * 0.62)), P[:, 2] - top)
        hwi = np.maximum(hw - F32(0.035), F32(1e-3))
        e_in = np.sqrt((P[:, 1] / hwi) ** 2 + ((P[:, 2] - zc - F32(0.03)) / F32(D * 0.5)) ** 2) - F32(1)
        d_in = np.maximum(e_in * np.minimum(hwi, F32(D * 0.5)), F32(0.75) * np.abs(x) - F32(0.75) + F32(0.12))
        return np.maximum(d_out, -d_in).astype(F32) * F32(0.8)
    f.add(Func(hull, (-L / 2 - 0.05, -W / 2 - 0.05, -0.05), (L / 2 + 0.05, W / 2 + 0.05, D + 0.12),
               **wob(6.0, 0.004, seed)), k=0.0, label=10)
    for sx in (-1, 1):
        f.add(RoundCone((sx * (L / 2 - 0.08), 0, D + 0.02), (sx * (L / 2 + 0.06), 0, D + 0.06), 0.03, 0.022), k=0.02)
    f.inter(Plane((0, 0, 0.0), (0, 0, -1)))
    pd = Field("Paddle")
    a, b = v3((-0.55, 0.05, D + 0.03)), v3((0.45, -0.02, D - 0.02))
    pd.add(RoundCone(a, b, 0.016, 0.016), k=0.0)
    pd.add(Ellipsoid(b + unit(b - a) * 0.17, (0.17, 0.07, 0.012), R=R_xz(unit(b - a), (0, 0, 1))), k=0.02)
    pd.add(RoundCone(a, a - unit(b - a) * 0.06, 0.03, 0.02), k=0.01)
    return [("Hull", f, fine(0.006, 0.012), "dugout"), ("Paddle", pd, fine(0.005, 0.01), "timber")]


# ------------------------------------------------------------------------------------------------ the harbour: plants, shore
def sea_grape(w=1.1, h=0.72, seed=0):
    """A sea-grape bush: crooked grey stems under a dome of big round leathery leaves (red-veined), bunches of green
    and purple grapes hanging at its edge."""
    rng = np.random.default_rng(seed)
    tw, lv, gr = Field("Twigs"), Field("Leaves"), Field("Grapes")
    for i in range(7):
        a = 2 * math.pi * i / 7 + rng.uniform(-0.3, 0.3)
        rr = w * rng.uniform(0.18, 0.38)
        tip = v3((rr * math.cos(a), rr * math.sin(a), h * rng.uniform(0.4, 0.75)))
        mid = tip * 0.45 + v3((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 0.05))
        tw.add(Chain([v3((0, 0, -0.03)), mid, tip], [0.032, 0.02, 0.012], k=0.01), k=0.01)
    c0 = v3((0, 0, h * 0.5))
    lv.add(Ellipsoid(c0, (w * 0.34, w * 0.32, h * 0.38), **wob(6.0, 0.02, seed)), k=0.0)
    n = 48
    golden = math.pi * (3 - math.sqrt(5))
    for j in range(n):
        zz = 1.0 - 1.2 * (j + 0.5) / n                              # a spiral over the dome, down to a little below its equator
        rr = math.sqrt(max(0.0, 1.0 - zz * zz))
        a = j * golden
        dvec = v3((math.cos(a) * rr, math.sin(a) * rr, zz))
        q = c0 + dvec * v3((w * 0.42, w * 0.4, h * 0.46))
        nrm = unit(dvec + v3((rng.normal() * 0.35, rng.normal() * 0.35, 0.5)))
        r = w * rng.uniform(0.07, 0.095)
        lv.add(Ellipsoid(q, (r, r * 0.92, 0.009), R=rot_from_axes(z_axis=nrm)), k=0.006)
    for k in range(4):
        a = rng.uniform(0, 2 * math.pi)
        q = c0 + v3((math.cos(a) * w * 0.4, math.sin(a) * w * 0.38, -h * 0.12))
        gr.add(RoundCone(q, q + v3((0, 0, -0.16)), 0.006, 0.005), k=0.0)
        for j in range(12):
            t = j / 11
            o = v3((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * 0.025 * (1.0 - 0.5 * t)
            gr.add(Sphere(q + o + v3((0, 0, -0.03 - 0.13 * t)), 0.017), k=0.004)
        gr.paint(Sphere(q + v3((0, 0, -0.12)), 0.06), 5)
    ground_cut(tw)
    lv.inter(Plane((0, 0, 0.02), (0, 0, -1)))
    return [("Twigs", tw, fine(0.005, 0.01), "driftwood"), ("Leaves", lv, fine(0.005, 0.01), "seagrape"),
            ("Grapes", gr, fine(0.004, 0.008), "grapes")]


def driftwood(seed=0, L=1.5):
    """A drift log bleached silver by the sea: a crooked trunk lying in the sand, a plate of broken roots at one end,
    a branch or two snapped off."""
    rng = np.random.default_rng(seed)
    f = Field("Wood")
    pts = [v3((-L / 2 + L * t, 0.06 * math.sin(t * 4.0 + seed), 0.075 - 0.02 * t)) for t in np.linspace(0, 1, 6)]
    f.add(Chain(pts, [0.1, 0.085, 0.075, 0.065, 0.05, 0.035], k=0.02, **wob(6.0, 0.01, seed)), k=0.0)
    root = pts[0]
    for k in range(7):
        a = 2 * math.pi * k / 7 + rng.uniform(-0.3, 0.3)
        d = v3((-0.4, math.cos(a), math.sin(a)))
        f.add(RoundCone(root, root + unit(d) * rng.uniform(0.18, 0.32), 0.045, 0.012), k=0.03)
    for k in range(3):
        b = at_height(pts, 0.0) if False else pts[1 + k]
        d = unit(v3((rng.uniform(-0.3, 0.6), rng.choice([-1, 1]) * 0.8, rng.uniform(0.2, 0.9))))
        f.add(RoundCone(b, b + d * rng.uniform(0.12, 0.3), 0.03, 0.012), k=0.015)
    f.inter(Plane((0, 0, 0.0), (0, 0, -1)))
    return [("Wood", f, fine(0.006, 0.012), "driftwood")]


# ------------------------------------------------------------------------------------------------ the contraband
def barrel_fn(c, R, hl, r_end, bulge):
    """A barrel (staves bulging) about the local Z of R, centred at c, half length hl."""
    cf = v3(c).astype(F32)
    Rf = np.asarray(R, np.float32)

    def fn(P):
        Q = (P - cf) @ Rf
        q = np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2)
        t = Q[:, 2] / F32(hl)
        prof = F32(r_end) + F32(bulge) * (F32(1) - t * t)
        staves = F32(0.0025) * np.cos(np.arctan2(Q[:, 1], Q[:, 0]) * F32(22))
        return (np.maximum(q - prof + staves, np.abs(Q[:, 2]) - F32(hl)) * F32(0.9)).astype(F32)
    e = r_end + bulge + hl + 0.05
    return Func(fn, v3(c) - e, v3(c) + e)


def add_barrel(f, c, R=None, hl=0.2, r_end=0.15, bulge=0.03, hoops=(0.72, 0.28), hoop_label=6, mark=None):
    R = np.eye(3) if R is None else R
    c = v3(c)
    ax = R @ v3((0, 0, 1))
    grain = 11 if abs(ax[2]) > 0.7 else (10 if abs(ax[0]) >= abs(ax[1]) else 0)      # (the staves' grain along its axis)
    f.add(barrel_fn(c, R, hl, r_end, bulge), k=0.0, label=grain)
    for t in hoops:
        for sg in (-1, 1):
            z = sg * hl * t
            rr = r_end + bulge * (1 - t * t) + 0.004
            f.add(Torus(c + ax * z, rr, 0.011, R=R), k=0.002, label=hoop_label)
    f.add(Cylinder(c + ax * (hl - 0.005), r_end - 0.012, 0.02, R=R), k=0.0, label=0)
    if mark is not None:
        f.paint(mark, 5)


def barrels(seed=0):
    """Rum casks: two standing, one stacked on them, one lying on chocks, a keg; iron hoops, a mark daubed on one."""
    rng = np.random.default_rng(seed)
    f = Field("Barrels")
    add_barrel(f, (0.0, 0.0, 0.23), hl=0.22)
    add_barrel(f, (0.37, 0.05, 0.23), hl=0.22, mark=RoundBox((0.37, -0.2, 0.25), (0.06, 0.06, 0.06), 0.0))
    add_barrel(f, (0.18, 0.03, 0.66), R=Rz(0.4), hl=0.2)
    R = rot_from_axes(z_axis=(math.cos(0.3), math.sin(0.3), 0.0))
    add_barrel(f, (-0.2, -0.42, 0.19), R=R, hl=0.22, r_end=0.14)
    add_barrel(f, (0.62, -0.32, 0.13), hl=0.13, r_end=0.1, bulge=0.02)
    for sx in (-0.42, 0.02):
        f.add(RoundBox((sx, -0.42, 0.035), (0.04, 0.16, 0.04), 0.008, R=Rz(0.3)), k=0.0, label=10)
    ground_cut(f)
    return [("Barrels", f, fine(0.005, 0.01), "cask")]


def crates(seed=0):
    """A stack of crates (boards nailed over battens, stencilled marks), a rope round one; an open crate beside them
    packed with straw and dark bottles, its lid propped against it."""
    rng = np.random.default_rng(seed)
    cr, st, bt = Field("Crates"), Field("Straw"), Field("Bottles")

    def crate(c, half, yaw, mark=True, tilt=0.0):
        R = Rz(yaw) @ euler(tilt, 0.0, 0.0)
        c = v3(c)
        cr.add(RoundBox(c, half, 0.012, R=R), k=0.0, label=10)
        hx, hy, hz = half
        for sy in (-1, 1):                                          # battens round each face
            for z in (-hz + 0.03, hz - 0.03):
                cr.add(RoundBox(c + R @ v3((0, sy * (hy + 0.008), z)), (hx + 0.008, 0.012, 0.02), 0.005, R=R), k=0.002, label=10)
            for x in (-hx + 0.03, hx - 0.03):
                cr.add(RoundBox(c + R @ v3((x, sy * (hy + 0.008), 0)), (0.02, 0.012, hz), 0.005, R=R), k=0.002, label=11)
        for sx in (-1, 1):
            for y in (-hy + 0.03, hy - 0.03):
                cr.add(RoundBox(c + R @ v3((sx * (hx + 0.008), y, 0)), (0.012, 0.02, hz), 0.005, R=R), k=0.002, label=11)
        for k in range(3):                                          # board joints
            z = -hz + (k + 1) * 2 * hz / 4
            cr.sub(RoundBox(c + R @ v3((0, -hy - 0.004, z)), (hx - 0.03, 0.008, 0.003), 0.0, R=R), k=0.0)
        if mark:
            m = c + R @ v3((0, -hy - 0.01, 0.0))
            cr.paint(Torus(m, 0.055, 0.013, R=R @ rot_from_axes(z_axis=(0, 1, 0))), 5)
            cr.paint(RoundBox(m, (0.075, 0.03, 0.012), 0.0, R=R @ euler(0, 0.78, 0)), 5)
    crate((0.0, 0.0, 0.17), (0.2, 0.18, 0.17), 0.05)
    crate((0.44, 0.04, 0.15), (0.2, 0.19, 0.15), -0.12)
    crate((-0.1, 0.42, 0.17), (0.22, 0.2, 0.17), 0.2, mark=False)
    crate((0.22, 0.05, 0.49), (0.19, 0.17, 0.15), 0.3)
    crate((0.05, 0.38, 0.5), (0.16, 0.15, 0.14), -0.25, mark=False)
    cr.add(Torus((0.22, 0.05, 0.49), 0.205, 0.014, R=rot_from_axes(z_axis=(math.cos(0.3), math.sin(0.3), 0))), k=0.002, label=8)
    o = v3((-0.52, -0.32, 0.13))                                    # the open crate
    cr.add(RoundBox(o, (0.18, 0.15, 0.13), 0.01, R=Rz(-0.3)), k=0.0, label=10)
    cr.sub(RoundBox(o + v3((0, 0, 0.06)), (0.155, 0.125, 0.13), 0.005, R=Rz(-0.3)), k=0.0)
    cr.add(RoundBox((-0.78, -0.6, 0.2), (0.17, 0.02, 0.15), 0.008, R=Rz(-0.3) @ euler(0.35, 0, 0)), k=0.0, label=10)   # its lid
    st.add(Ellipsoid(o + v3((0, 0, 0.1)), (0.15, 0.12, 0.05), **wob(30.0, 0.008, seed)), k=0.0)
    for j in range(6):
        q = o + Rz(-0.3) @ v3((-0.09 + 0.09 * (j % 3), -0.045 + 0.09 * (j // 3), 0.13))
        tilt = v3((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 1.0))
        bt.add(RoundCone(q, q + unit(tilt) * 0.08, 0.032, 0.03), k=0.0)
        bt.add(RoundCone(q + unit(tilt) * 0.08, q + unit(tilt) * 0.16, 0.012, 0.01), k=0.015)
    ground_cut(cr)
    return [("Crates", cr, fine(0.005, 0.01), "crate"), ("Straw", st, fine(0.005, 0.01), "straw"), ("Bottles", bt, fine(0.004, 0.008), "bottle")]


def bales(seed=0):
    """Bales of contraband cloth (sacking, and bales of indigo-dyed cloth) lashed with rope, and sacks heaped by them."""
    rng = np.random.default_rng(seed)
    f, sk = Field("Bales"), Field("Sacks")
    for i, (c, half, yaw, indigo) in enumerate((((0.0, 0.0, 0.17), (0.3, 0.22, 0.17), 0.1, False),
                                                 ((0.62, 0.08, 0.15), (0.26, 0.2, 0.15), -0.2, True),
                                                 ((0.28, 0.06, 0.48), (0.27, 0.2, 0.15), 0.25, True))):
        R = Rz(yaw)
        c = v3(c)
        f.add(RoundBox(c, half, 0.07, R=R, **wob(7.0, 0.01, seed + i)), k=0.0)
        hx, hy, hz = half
        for x in (-hx * 0.5, hx * 0.5):                             # the rope lashings
            f.add(RoundBox(c + R @ v3((x, 0, 0)), (0.016, hy + 0.012, hz + 0.012), 0.05, R=R), k=0.004, label=5)
        f.add(RoundBox(c, (hx + 0.012, 0.016, hz + 0.012), 0.05, R=R), k=0.004, label=5)
        if indigo:
            f.paint(RoundBox(c, (hx - 0.02, hy + 0.05, hz + 0.05), 0.0, R=R), 6)
            f.paint(RoundBox(c, (hx + 0.05, hy - 0.02, hz + 0.05), 0.0, R=R), 6)
    for i, (x, y, a) in enumerate(((-0.42, -0.2, 0.3), (-0.3, 0.3, -0.6), (0.2, -0.4, 1.2))):
        c = v3((x, y, 0.15))
        sk.add(Ellipsoid(c, (0.15, 0.13, 0.17), R=euler(0.25, 0, a), **wob(8.0, 0.012, seed + 10 + i)), k=0.0)
        sk.add(RoundCone(c + v3((0, 0, 0.13)), c + v3((0.03, 0, 0.24)), 0.045, 0.03), k=0.03)
        sk.add(Torus(c + v3((0.01, 0, 0.18)), 0.04, 0.012), k=0.01, label=5)
    ground_cut(f)
    ground_cut(sk)
    return [("Bales", f, fine(0.006, 0.012), "bales"), ("Sacks", sk, fine(0.006, 0.012), "bales")]


def rope_coil(seed=0, R0=0.27, r=0.024):
    """A coil of heavy rope flaked down on the sand, a second turn lying over the first, its end trailing off."""
    f = Field("Rope")
    pts = []
    turns = 3.3
    for i in range(70):
        t = i / 69 * turns
        rr = R0 - 0.052 * t
        a = 2 * math.pi * t
        pts.append(v3((math.cos(a) * rr, math.sin(a) * rr, r * 0.9)))
    f.add(Chain(pts, [r] * len(pts), k=0.004), k=0.0, label=8)
    top = [v3((math.cos(a) * (R0 - 0.06), math.sin(a) * (R0 - 0.06), r * 2.6)) for a in np.linspace(0.3, 4.2, 18)]
    f.add(Chain(top, [r] * len(top), k=0.004), k=0.004, label=8)
    tail = [v3((R0, 0, r * 0.9)), v3((R0 + 0.15, -0.12, r * 0.9)), v3((R0 + 0.28, -0.05, r * 0.9)), v3((R0 + 0.45, -0.16, r * 0.9))]
    f.add(Chain(tail, [r] * len(tail), k=0.004), k=0.004, label=8)
    f.inter(Plane((0, 0, 0.0), (0, 0, -1)))
    return [("Rope", f, fine(0.004, 0.008), "rope")]


def anchor(seed=0):
    """A ship's anchor lying in the sand: the long shank, the curved arms with their spade flukes (one dug in), the ring,
    an iron stock with ball ends across the top, a few links of chain."""
    f = Field("Iron")
    tilt = euler(0.0, 0.42, 0.0)                                   # the arms' plane tilted: one fluke digs in
    def T(p):
        return tilt @ v3(p) + v3((0, 0, 0.14))
    f.add(RoundCone(T((-0.6, 0, 0)), T((0.42, 0, 0)), 0.04, 0.05), k=0.0)
    for sy in (-1, 1):                                              # the arms
        arm = [T((0.42, 0, 0)), T((0.4, sy * 0.2, 0)), T((0.26, sy * 0.36, 0)), T((0.05, sy * 0.44, 0))]
        f.add(Chain(arm, [0.05, 0.045, 0.04, 0.032], k=0.02), k=0.02)
        tip = arm[-1]
        dirv = unit(arm[-1] - arm[-2])
        f.add(Ellipsoid(tip - dirv * 0.05, (0.11, 0.07, 0.02), R=R_xz(dirv, tilt @ v3((0, 0, 1)))), k=0.015)
        f.add(RoundCone(tip, tip + dirv * 0.08, 0.02, 0.004), k=0.01)
    f.add(Sphere(T((0.45, 0, 0)), 0.065), k=0.02)
    f.add(Torus(T((-0.68, 0, 0)), 0.085, 0.022, R=rot_from_axes(z_axis=tilt @ v3((0, 1, 0)))), k=0.01)
    stock_a, stock_b = T((-0.5, 0, -0.48)), T((-0.5, 0, 0.48))
    f.add(RoundCone(stock_a, stock_b, 0.03, 0.03), k=0.01)
    for e in (stock_a, stock_b):
        f.add(Sphere(e, 0.045), k=0.01)
    for k in range(5):                                              # chain links snaking off the ring
        c = T((-0.82, 0, 0)) + v3((-0.12 * k, 0.05 * math.sin(k * 1.3), 0.0))
        c[2] = 0.025
        R = rot_from_axes(z_axis=(0, 1, 0) if k % 2 == 0 else (0, 0, 1), x_axis=(1, 0, 0))
        f.add(Torus(c, 0.05, 0.016, R=rot_from_axes(x_axis=(1, 0, 0), z_axis=(0, 1, 0)) if k % 2 == 0 else np.eye(3)), k=0.004)
    f.inter(Plane((0, 0, 0.0), (0, 0, -1)))
    return [("Iron", f, fine(0.005, 0.01), "rust_iron")]


def rowboat(seed=0, L=1.6, W=0.64, D=0.3):
    """A rowboat drawn up on the sand, heeled over a little: a clinker hull (a pointed bow, a small transom stern, a red
    stripe under the gunwale), two thwarts, the oars lying in it, a bailer."""
    f = Field("Hull")
    Lh = L / 2

    def hull(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        xb = np.clip(x / F32(Lh), 0, 1.2)
        xs = np.clip(-x / F32(Lh), 0, 1.2)
        hw = F32(W / 2) * np.where(x > 0, np.sqrt(np.clip(F32(1) - xb ** F32(2.0), 0, 1)) ** F32(0.8),
                                   np.sqrt(np.clip(F32(1) - xs ** F32(5.0), 0, 1))) + F32(0.004)
        keel = F32(0.03) + F32(0.1) * (x / F32(Lh)) ** 2
        top = F32(D) + F32(0.09) * (x / F32(Lh)) ** 2
        sec = np.clip((z - keel) / F32(0.16), F32(0.12), F32(1))
        d_out = np.maximum.reduce([np.abs(y) - hw * sec, keel - z, z - top, -x - F32(Lh * 0.96)])
        d_in = np.maximum.reduce([np.abs(y) - (hw - F32(0.028)) * sec, keel + F32(0.05) - z, -x - F32(Lh * 0.96 - 0.03)])
        return (np.maximum(d_out, -d_in) * F32(0.8)).astype(F32)
    hull_f = Func(hull, (-Lh - 0.05, -W / 2 - 0.05, -0.05), (Lh + 0.05, W / 2 + 0.05, D + 0.15))
    tmp = Field("H")
    tmp.add(hull_f, k=0.0, label=10)
    for z in (0.12, 0.19):                                          # the planks' laps, drawn dark
        tmp.paint(Func(lambda P, z=z: (np.abs(P[:, 2] - F32(z) - F32(0.05) * (P[:, 0] / F32(Lh)) ** 2) - F32(0.006)).astype(F32),
                       (-Lh - 0.1, -W, 0), (Lh + 0.1, W, D + 0.2)), 7)
    tmp.paint(Func(lambda P: (np.abs(P[:, 2] - F32(D - 0.045) - F32(0.09) * (P[:, 0] / F32(Lh)) ** 2) - F32(0.022)).astype(F32),
                   (-Lh - 0.1, -W, 0), (Lh + 0.1, W, D + 0.2)), 5)
    for x in (-0.3, 0.25):                                          # thwarts
        tmp.add(RoundBox((x, 0, D - 0.07), (0.07, W / 2 - 0.03, 0.015), 0.005), k=0.0, label=0)
    tmp.add(RoundBox((-Lh * 0.96 + 0.015, 0, D * 0.62), (0.015, W * 0.3, D * 0.33), 0.008), k=0.004, label=11)   # transom
    for sy in (-1, 1):                                              # the oars lying in it
        a, b = v3((-0.62, sy * 0.1, D - 0.04)), v3((0.68, sy * 0.06, D - 0.02))
        tmp.add(RoundCone(a, b, 0.017, 0.015), k=0.0, label=10)
        tmp.add(Ellipsoid(a + unit(a - b) * 0.0 + v3((0.12, 0, 0)), (0.14, 0.05, 0.01)), k=0.01, label=10)
    R = euler(0.14, 0.03, 0.0)
    place(f, tmp, (0, 0, -0.01), R)
    f.inter(Plane((0, 0, 0.0), (0, 0, -1)))
    return [("Hull", f, fine(0.005, 0.01), "boat")]


def nets(seed=0):
    """Fishing nets drying on poles: two forked poles with a spar across them, the net draped over it in folds, corks
    along its edges; a heap of net at the foot of one pole."""
    rng = np.random.default_rng(seed)
    wd, nt, ck = Field("Poles"), Field("Net"), Field("Corks")
    X, Z = 0.75, 1.12
    for sx in (-1, 1):
        post(wd, (sx * X, 0, -0.06), (sx * X, 0, Z - 0.1), 0.03, 0.026)
        for sy in (-1, 1):
            wd.add(RoundCone((sx * X, 0, Z - 0.12), (sx * X, sy * 0.07, Z + 0.06), 0.022, 0.016), k=0.01, label=11)
    wd.add(RoundCone((-X - 0.15, 0, Z), (X + 0.15, 0, Z), 0.025, 0.025), k=0.004, label=10)
    ground_cut(wd)
    Ln = 2 * X - 0.1
    for sy in (-1, 1):
        o = v3((-X + 0.05, sy * 0.03, Z + 0.02))
        u = v3((1, 0, 0))
        v = v3((0, sy * 0.28, -1.0))
        hang_len = 0.86 if sy > 0 else 0.7
        poly = [(0.0, 0.0), (Ln, 0.0)] + [(Ln - Ln * t, hang_len + 0.05 * math.sin(t * 17 + sy)) for t in np.linspace(0, 1, 12)]

        def folds(a, b, sy=sy):
            k = F32(13.0 + sy)
            fb = np.clip(b / F32(0.9), 0, 1)
            g = F32(0.035) * np.sin(a * k) * fb
            return g, F32(0.035) * k * np.cos(a * k) * fb, F32(0.035) * np.sin(a * k) / F32(0.9)
        nt.add(leaf(o, u, v, poly, 0.006, zfn=folds, zamp=0.04), k=0.0)
        for t in np.linspace(0.04, 0.96, 9):                       # corks along the hem
            a = Ln * t
            vv = unit(v - u * float(np.dot(v, u)))
            q = o + u * a + vv * (hang_len + 0.05 * math.sin((1 - t) * 17 + sy))
            ck.add(Ellipsoid(q, (0.03, 0.022, 0.022)), k=0.0)
    for j in range(5):                                              # the heap at the foot
        q = v3((X + 0.28 + rng.uniform(-0.12, 0.12), rng.uniform(-0.15, 0.15), 0.04))
        nt.add(Ellipsoid(q, (0.14, 0.12, 0.07), **wob(18.0, 0.015, seed + j)), k=0.04)
    nt.inter(Plane((0, 0, 0.0), (0, 0, -1)))
    return [("Poles", wd, fine(0.005, 0.01), "driftwood"), ("Net", nt, fine(0.004, 0.008), "net"),
            ("Corks", ck, fine(0.004, 0.008), "cork")]


def treasure(seed=0):
    """A pirates' chest standing open on the sand: iron-bound oak, its round lid thrown back, heaped over its rim with
    gold coins; coins spilled down its front and in little stacks, a gold goblet, a string of pearls, a ruby and an
    emerald."""
    rng = np.random.default_rng(seed)
    ch, gd, gm, pl = Field("Chest"), Field("Gold"), Field("Gems"), Field("Pearls")
    hx, hy, hz = 0.27, 0.17, 0.14
    ch.add(RoundBox((0, 0, hz), (hx, hy, hz), 0.015), k=0.0, label=10)
    ch.sub(RoundBox((0, 0, hz * 2 + 0.05), (hx - 0.025, hy - 0.025, 0.12), 0.01), k=0.0)
    for x in (-hx * 0.62, 0.0, hx * 0.62):                          # iron bands
        ch.add(RoundBox((x, 0, hz), (0.018, hy + 0.008, hz + 0.006), 0.006), k=0.002, label=6)
    ch.add(RoundBox((0, -hy - 0.01, hz * 1.55), (0.04, 0.012, 0.05), 0.006), k=0.002, label=6)           # the lock plate
    hinge = v3((0, hy, hz * 2))                                     # the lid: a half-barrel thrown back on its hinges
    Rl = euler(-1.95, 0.0, 0.0)
    lid = Field("L")
    lid.add(Cylinder((0, -hy, 0.0), hy, 2 * hx, rr=0.012, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.0, label=10)
    lid.sub(Cylinder((0, -hy, 0.0), hy - 0.022, 2 * hx - 0.04, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.0)
    lid.sub(RoundBox((0, -hy, -0.2), (hx + 0.1, hy + 0.1, 0.2), 0.0), k=0.0)
    for x in (-hx * 0.62, 0.0, hx * 0.62):
        lid.add(Torus((x, -hy, 0.0), hy + 0.004, 0.012, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.002, label=6)
    lid.sub(RoundBox((0, -hy, -0.2), (hx + 0.1, hy + 0.1, 0.2), 0.0), k=0.0)
    place(ch, lid, hinge, Rl)
    gd.add(Ellipsoid((0, 0, hz * 2 - 0.01), (hx - 0.02, hy - 0.02, 0.08), **wob(25.0, 0.01, seed)), k=0.0)     # the heap
    for k in range(26):                                             # coins over the heap and spilled before it
        if k < 10:
            a = rng.uniform(0, 2 * math.pi)
            q = v3((math.cos(a) * hx * 0.6 * rng.uniform(0, 1), math.sin(a) * hy * 0.6 * rng.uniform(0, 1), hz * 2 + 0.06))
            nrm = unit(v3((rng.normal() * 0.4, rng.normal() * 0.4, 1.0)))
        else:
            q = v3((rng.uniform(-0.45, 0.45), -hy - rng.uniform(0.05, 0.4), 0.008))
            nrm = unit(v3((rng.normal() * 0.15, rng.normal() * 0.15, 1.0)))
        gd.add(Cylinder(q, 0.03, 0.009, rr=0.003, R=rot_from_axes(z_axis=nrm)), k=0.0)
    for (x, y, n) in ((0.34, -0.3, 4), (-0.32, -0.34, 3)):         # little stacks
        for j in range(n):
            gd.add(Cylinder((x + rng.uniform(-0.004, 0.004), y, 0.006 + 0.0105 * j), 0.03, 0.009, rr=0.003), k=0.0)
    gl = v3((-0.42, -0.08, 0.0))                                    # a goblet
    gd.add(Cylinder(gl + v3((0, 0, 0.008)), 0.045, 0.016, rr=0.005), k=0.0)
    gd.add(RoundCone(gl + v3((0, 0, 0.01)), gl + v3((0, 0, 0.1)), 0.012, 0.012), k=0.01)
    gd.add(Ellipsoid(gl + v3((0, 0, 0.15)), (0.055, 0.055, 0.06)), k=0.01)
    gd.sub(Cylinder(gl + v3((0, 0, 0.19)), 0.045, 0.08), k=0.004)
    gm.add(crystal((0.12, -0.42, 0.0), (0.2, -0.1, 1.0), 0.03, 0.05), k=0.0)
    gm.add(crystal((-0.12, 0.02, hz * 2 + 0.05), (-0.3, 0.1, 1.0), 0.03, 0.05), k=0.0)
    gm.paint(Sphere((-0.12, 0.02, hz * 2 + 0.07), 0.08), 5)
    for k in range(22):                                             # a string of pearls hanging over the rim
        t = k / 21
        q = v3((hx * 0.3 - 0.35 * t, -hy - 0.01 - 0.04 * math.sin(t * math.pi), hz * 2 + 0.02 - 0.22 * math.sin(t * math.pi) ** 0.8))
        if q[2] < 0.012:
            q[2] = 0.012
        pl.add(Sphere(q, 0.012), k=0.0)
    ground_cut(ch)
    ground_cut(gd, 0.0)
    out = [("Chest", ch, fine(0.005, 0.01), "chest"), ("Gold", gd, fine(0.004, 0.008), "gold"),
           ("Gems", gm, fine(0.004, 0.008), "gems"), ("Pearls", pl, fine(0.003, 0.006), "pearl")]
    return mound(out, 0.75, 0.62, 0.08, seed, c=(0, -0.12), voxel=fine(0.012, 0.022))


# ------------------------------------------------------------------------------------------------ the harbour: landmarks
def brigantine(seed=0):
    """A brigantine at her mooring (afloat at z = 0, her bow toward +X): a dark tarred hull with a raised quarterdeck,
    a gold stripe along her side, gun ports in the bulwarks with crimson lids, muzzles run out, stern windows framed in
    gold and a stern lantern; a bowsprit and jib boom, a gilded figurehead; two masts with tops, the fore square-rigged
    and the main with gaff and boom, every sail furled; shrouds and stays; the red-and-black flag at the main masthead."""
    out = []
    xs, xb, W = -1.85, 1.95, 1.0

    def hw_of(x, z):
        tb = np.clip((x - F32(0.2)) / F32(xb - 0.2), 0, 1)
        ts = np.clip((F32(-0.5) - x) / F32(-0.5 - xs), 0, 1)
        hw = F32(W / 2) * np.sqrt(np.clip(F32(1) - tb ** F32(2.2), 0, 1)) ** F32(1.1) * (F32(1) - F32(0.3) * ts ** 2)
        return hw * (F32(1) - F32(0.1) * np.clip((z - F32(0.25)) / F32(0.4), 0, 1)) + F32(0.003)

    def top_of(x):
        tb = np.clip((x - F32(0.2)) / F32(xb - 0.2), 0, 1)
        ts = np.clip((F32(-0.75) - x) / F32(0.4), 0, 1)
        return F32(0.52) + F32(0.12) * tb ** 2 + F32(0.24) * ts * ts * (F32(3) - F32(2) * ts)

    def deck_of(x):
        ts = np.clip((F32(-0.8) - x) / F32(0.12), 0, 1)
        tf = np.clip((x - F32(1.3)) / F32(0.12), 0, 1)
        return F32(0.34) + F32(0.2) * ts + F32(0.08) * tf

    def hull(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        hw = hw_of(x, z)
        d_out = np.maximum.reduce([np.abs(y) - hw, z - top_of(x), F32(xs) - x, -z - F32(0.1)])
        d_in = np.maximum(np.abs(y) - (hw - F32(0.045)), deck_of(x) - z)
        return (np.maximum(d_out, -d_in) * F32(0.75)).astype(F32)
    h = Field("Hull")
    h.add(Func(hull, (xs - 0.05, -W / 2 - 0.05, -0.12), (xb + 0.05, W / 2 + 0.05, 0.9)), k=0.0, label=10)
    h.paint(Func(lambda P: (np.abs(P[:, 2] - F32(0.27) - F32(0.06) * np.clip((P[:, 0] - F32(0.2)) / F32(1.75), 0, 1) ** 2) - F32(0.026)).astype(F32),
                 (xs - 0.1, -0.7, 0), (xb + 0.1, 0.7, 0.6)), 5)                                   # the gold stripe
    for x in (-0.55, -0.05, 0.45, 0.95):                            # gun ports, their crimson lids raised
        for sy in (-1, 1):
            hwx = float(hw_of(np.array([x], F32), np.array([0.43], F32))[0])
            h.sub(RoundBox((x, sy * hwx, 0.43), (0.06, 0.08, 0.055), 0.008), k=0.003)
            h.add(RoundBox((x, sy * (hwx + 0.03), 0.53), (0.065, 0.008, 0.055), 0.004, R=euler(-sy * 0.9, 0, 0)), k=0.0, label=7)
    sw = []                                                         # stern windows
    for y in (-0.22, 0.0, 0.22):
        h.sub(RoundBox((xs, y, 0.6), (0.04, 0.06, 0.07), 0.008), k=0.003)
        h.paint(RoundBox((xs, y, 0.6), (0.05, 0.09, 0.1), 0.0), 5)
        sw.append((y, 0.6))
    h.inter(Plane((0, 0, -0.04), (0, 0, -1)))
    out.append(("Hull", h, fine(0.008, 0.016), "hull"))
    dk = Field("Deck")
    dk.add(Func(lambda P: (np.maximum(np.abs(P[:, 1]) - (hw_of(P[:, 0], P[:, 2]) - F32(0.04)), np.abs(P[:, 2] - deck_of(P[:, 0]) + F32(0.012)) - F32(0.012))
                           * F32(0.8)).astype(F32), (xs, -0.55, 0.25), (xb, 0.55, 0.7)), k=0.0, label=10)
    dk.add(RoundBox((0.2, 0, 0.36), (0.22, 0.17, 0.04), 0.01), k=0.0, label=10)                       # the hatch coaming
    out.append(("Deck", dk, fine(0.008, 0.016), "deck"))
    dark = Field("Dark")
    dark.add(RoundBox((0.2, 0, 0.395), (0.18, 0.13, 0.008), 0.004), k=0.0)
    for x in (-0.55, -0.05, 0.45, 0.95):
        for sy in (-1, 1):
            hwx = float(hw_of(np.array([x], F32), np.array([0.43], F32))[0])
            dark.add(RoundBox((x, sy * (hwx - 0.03), 0.43), (0.055, 0.02, 0.05), 0.006), k=0.0)
    for (y, z) in sw:
        dark.add(RoundBox((xs + 0.025, y, z), (0.01, 0.05, 0.06), 0.006), k=0.0)
    out.append(("Dark", dark, fine(0.006, 0.012), "dark"))
    gn = Field("Guns")
    for x in (-0.05, 0.95):                                         # muzzles run out of two ports a side
        for sy in (-1, 1):
            hwx = float(hw_of(np.array([x], F32), np.array([0.43], F32))[0])
            gn.add(RoundCone((x, sy * (hwx - 0.1), 0.43), (x, sy * (hwx + 0.09), 0.43), 0.035, 0.03), k=0.0)
            gn.add(Torus((x, sy * (hwx + 0.075), 0.43), 0.032, 0.008, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.003)
    out.append(("Guns", gn, fine(0.005, 0.01), "gun_iron"))
    wd = Field("Spars")
    rud = Field("Rudder")
    rud.add(RoundBox((xs - 0.03, 0, 0.32), (0.035, 0.025, 0.34), 0.01), k=0.0, label=11)
    rud.inter(Plane((0, 0, -0.04), (0, 0, -1)))
    out.append(("Rudder", rud, fine(0.006, 0.012), "hull"))
    bs0, bs1 = v3((1.7, 0, 0.62)), v3((2.75, 0, 0.98))             # the bowsprit and jib boom
    wd.add(RoundCone(bs0, bs1, 0.05, 0.03), k=0.0, label=10)
    wd.add(RoundCone(bs1 - unit(bs1 - bs0) * 0.3, bs1 + unit(bs1 - bs0) * 0.35, 0.022, 0.016), k=0.005, label=10)
    masts = [(0.85, 3.25, 2.15), (-0.45, 3.6, 2.35)]               # (x, height of the masthead, height of the top)
    tops = []
    for (mx, mh, mt) in masts:
        wd.add(RoundCone((mx, 0, 0.3), (mx, 0, mt + 0.1), 0.055, 0.045), k=0.0, label=11)
        wd.add(RoundCone((mx, 0, mt - 0.05), (mx, 0, mh), 0.032, 0.022), k=0.004, label=11)
        wd.add(RoundBox((mx, 0, mt), (0.16, 0.22, 0.025), 0.01), k=0.004, label=10)                     # the top
        wd.add(Sphere((mx, 0, mh + 0.02), 0.035), k=0.004, label=6)                                    # the truck
        tops.append((mx, mt, mh))
    sl = Field("Sails")
    for (z, hl) in ((1.45, 0.78), (2.62, 0.56)):                    # the fore yards, their sails furled on them
        wd.add(RoundCone((0.85, -hl, z), (0.85, hl, z), 0.022, 0.022), k=0.004, label=0)
        sl.add(RoundCone((0.87, -hl * 0.92, z - 0.035), (0.87, hl * 0.92, z - 0.035), 0.045, 0.045, **wob(14.0, 0.006, seed + int(z * 10))), k=0.0)
        for k in range(5):
            t = -0.8 + 0.4 * k
            sl.add(Torus((0.87, hl * t, z - 0.035), 0.047, 0.008, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.003, label=5)
    wd.add(RoundCone((-0.45, 0, 0.92), (-1.95, 0, 0.82), 0.03, 0.025), k=0.0, label=10)                # the main boom
    wd.add(RoundCone((-0.45, 0, 2.2), (-1.35, 0, 2.6), 0.026, 0.02), k=0.0, label=10)                  # the gaff
    sl.add(RoundCone((-0.6, 0, 0.98), (-1.85, 0, 0.88), 0.065, 0.05, **wob(12.0, 0.008, seed + 5)), k=0.0)   # the mainsail, furled
    wd.add(RoundCone((-0.45, -0.5, 2.95), (-0.45, 0.5, 2.95), 0.02, 0.02), k=0.004, label=0)           # the main topsail yard
    sl.add(RoundCone((-0.43, -0.45, 2.915), (-0.43, 0.45, 2.915), 0.04, 0.04, **wob(14.0, 0.006, seed + 7)), k=0.0)
    out.append(("Sails", sl, fine(0.005, 0.01), "sail"))
    rg = Field("Rigging")
    for (mx, mt, mh) in tops:                                       # shrouds to the chains, ratlines across them
        for sy in (-1, 1):
            for dx in (-0.16, 0.0, 0.16):
                xx = mx + dx - 0.05
                hwx = float(hw_of(np.array([xx], F32), np.array([0.5], F32))[0])
                a, b = v3((mx, sy * 0.06, mt - 0.02)), v3((xx, sy * (hwx + 0.04), float(top_of(np.array([xx], F32))[0]) - 0.04))
                rg.add(RoundCone(a, b, 0.008, 0.008), k=0.0)
            for k in range(4):
                t = 0.25 + 0.17 * k
                xa, xb2 = mx - 0.21, mx + 0.11
                za = mt - 0.02 + (float(top_of(np.array([mx], F32))[0]) - 0.04 - mt + 0.02) * t
                yy = sy * (0.06 + (W / 2 - 0.02) * t)
                rg.add(RoundCone((mx - 0.2 * t, yy, za), (mx + 0.12 * t, yy, za), 0.006, 0.006), k=0.0)
    rg.add(RoundCone((0.85, 0, 3.15), bs1, 0.009, 0.009), k=0.0)                                      # the stays
    rg.add(RoundCone((0.85, 0, 2.1), bs0 + v3((0.4, 0, 0.12)), 0.01, 0.01), k=0.0)
    rg.add(RoundCone((-0.45, 0, 3.5), (0.85, 0, 1.0), 0.008, 0.008), k=0.0)
    rg.add(RoundCone((-0.45, 0, 2.3), (0.85, 0, 0.62), 0.009, 0.009), k=0.0)
    for sy in (-1, 1):                                              # backstays
        rg.add(RoundCone((-0.45, 0, 3.5), (-1.25, sy * 0.4, 0.75), 0.007, 0.007), k=0.0)
    out.append(("Rigging", rg, fine(0.005, 0.01), "tarred_rope"))
    out.append(("Spars", wd, fine(0.006, 0.012), "timber"))
    gl = Field("Gilt")                                               # the figurehead, the stern lantern
    fh = v3((1.88, 0, 0.6))
    gl.add(Ellipsoid(fh, (0.08, 0.05, 0.1), R=euler(0, -0.6, 0)), k=0.0)
    gl.add(Sphere(fh + v3((0.06, 0, 0.08)), 0.05), k=0.02)
    gl.add(RoundCone((xs + 0.04, 0, 0.75), (xs - 0.02, 0, 1.0), 0.015, 0.015), k=0.0)
    gl.add(RoundCone((xs - 0.02, 0, 1.0), (xs - 0.02, 0, 1.14), 0.05, 0.035), k=0.01)
    gl.add(RoundCone((xs - 0.02, 0, 1.14), (xs - 0.02, 0, 1.2), 0.02, 0.004), k=0.01)
    out.append(("Gilt", gl, fine(0.004, 0.008), "gold"))
    wh = Field("Wheel")                                             # the ship's wheel on the quarterdeck
    wc = v3((-1.25, 0, 0.78))
    wh.add(Torus(wc, 0.13, 0.014, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.0, label=10)
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = v3((0, math.cos(a), math.sin(a)))
        wh.add(RoundCone(wc, wc + d * 0.17, 0.008, 0.007), k=0.004, label=10)
    wh.add(RoundBox((-1.25, 0, 0.62), (0.04, 0.06, 0.1), 0.01), k=0.006, label=11)
    out.append(("Wheel", wh, fine(0.004, 0.008), "timber"))
    fg = Field("Flag")
    fo = v3((-0.47, 0, 3.55))
    fg.add(flag(fo, 0.62, 0.42, seed, along=(-1, 0, 0)), k=0.0)
    ff = v3((-0.47 - 0.31, 0, 3.55 - 0.2))
    fg.paint(Sphere(ff + v3((0, 0, 0.04)), 0.075), 5)                                    # a red skull...
    fg.paint(RoundBox(ff + v3((0, 0, -0.04)), (0.045, 0.1, 0.035), 0.01), 5)
    for sg in (-1, 1):                                                                  # ...over crossed bones
        R = rot_from_axes(x_axis=(math.cos(sg * 0.6), 0, math.sin(sg * 0.6)), y_axis=(0, 1, 0))
        fg.paint(RoundBox(ff + v3((0, 0, -0.06)), (0.2, 0.1, 0.018), 0.01, R=R), 5)
    for sx in (-1, 1):
        fg.paint(Sphere(ff + v3((sx * 0.028, 0, 0.05)), 0.022), 6)                       # its eyes, black
    out.append(("Flag", fg, fine(0.004, 0.008), "flag_pirate"))
    return out


def jetty(seed=0, L=2.7, W=0.86, zd=0.34):
    """A timber jetty from the shore (x = 0) out into the water (+X): piles in pairs with their caps, stringers, a deck
    of planks laid across, mooring posts at its end with a rope round one, a ladder down into the water, a lantern on a
    post, a crate."""
    rng = np.random.default_rng(seed)
    wd = Field("Timber")
    xs_ = [0.25, 0.85, 1.45, 2.05, L - 0.08]
    for i, x in enumerate(xs_):
        for sy in (-1, 1):
            ztop = zd - 0.04 if i < len(xs_) - 1 else zd + 0.32
            post(wd, (x, sy * (W / 2 - 0.05), -0.2), (x, sy * (W / 2 - 0.05), ztop), 0.06, 0.055)
        wd.add(RoundBox((x, 0, zd - 0.075), (0.05, W / 2 + 0.04, 0.04), 0.01), k=0.003, label=0)
    for sy in (-1, 1):
        wd.add(RoundBox((L / 2, sy * 0.24, zd - 0.06), (L / 2, 0.04, 0.035), 0.01), k=0.003, label=10)
    x = 0.04
    while x < L - 0.02:                                             # the deck planks, laid across
        wl = W / 2 + rng.uniform(-0.03, 0.03)
        wd.add(RoundBox((x, rng.uniform(-0.02, 0.02), zd - 0.012 + rng.uniform(-0.005, 0.005)), (0.052, wl, 0.02), 0.006,
                        R=Rz(rng.uniform(-0.03, 0.03))), k=0.002, label=0)
        x += 0.115
    wd.add(RoundBox((0.0, 0, zd * 0.5), (0.1, W / 2, zd * 0.5), 0.02), k=0.01, label=0)               # its shore end
    for k in range(5):                                              # a ladder down the end into the water
        z = zd - 0.08 - 0.09 * k
        wd.add(RoundCone((L + 0.03, 0.12, z), (L + 0.03, 0.3, z), 0.012, 0.012), k=0.0, label=10)
    for y in (0.12, 0.3):
        post(wd, (L + 0.03, y, -0.15), (L + 0.03, y, zd + 0.1), 0.018)
    post(wd, (L - 0.3, -W / 2 + 0.08, zd), (L - 0.3, -W / 2 + 0.08, zd + 0.72), 0.025)                    # the lantern post
    wd.add(RoundCone((L - 0.3, -W / 2 + 0.08, zd + 0.7), (L - 0.3, -W / 2 - 0.08, zd + 0.7), 0.014, 0.014), k=0.004, label=10)
    wd.add(RoundBox((0.55, 0.12, zd + 0.13), (0.13, 0.12, 0.12), 0.01, R=Rz(0.3)), k=0.0, label=10)      # a crate on the deck
    ground_cut(wd, -0.04)
    out = [("Timber", wd, fine(0.005, 0.01), "pier")]
    rp = Field("Rope")
    for sy in (-1, 1):
        rp.add(Torus((L - 0.08, sy * (W / 2 - 0.05), zd + 0.2), 0.065, 0.016), k=0.0, label=8)
    pts = [v3((L - 0.08, W / 2 - 0.05, zd + 0.19)), v3((L - 0.3, W / 2 + 0.05, zd + 0.05)), v3((L - 0.6, W / 2 - 0.1, zd + 0.02))]
    rp.add(Chain(pts, [0.016] * 3, k=0.004), k=0.004, label=8)
    for i in range(30):                                             # a coil of rope on the deck
        t = i / 29 * 2.2
        rr = 0.13 - 0.035 * t
        a = 2 * math.pi * t
        rp.add(Sphere((1.25 + math.cos(a) * rr, -0.15 + math.sin(a) * rr, zd + 0.024), 0.02), k=0.012, label=8)
    out.append(("Rope", rp, fine(0.004, 0.008), "rope"))
    ln = Field("Lantern")
    lc = v3((L - 0.3, -W / 2 - 0.08, zd + 0.56))
    ln.add(RoundCone(lc + v3((0, 0, 0.13)), lc + v3((0, 0, 0.08)), 0.008, 0.008), k=0.0)
    ln.add(RoundBox(lc, (0.05, 0.05, 0.075), 0.01), k=0.004)
    ln.add(RoundCone(lc + v3((0, 0, 0.07)), lc + v3((0, 0, 0.12)), 0.06, 0.012), k=0.004)
    out.append(("Lantern", ln, fine(0.004, 0.008), "brass"))
    return out


def tavern(seed=0):
    """A waterfront tavern and warehouse: a ground floor of rough stone, an upper floor of dark timbers over white
    plaster jettied out over the street, a red tile roof with a stone chimney; the tavern door with a lantern, shuttered
    windows, its sign hanging from an iron bracket; at the gable end a loft door under a hoist beam with its rope and
    hook, wide doors below; barrels and a bench by the door."""
    rng = np.random.default_rng(seed)
    out = []
    hx, hy = 1.05, 0.6
    z1, z2 = 0.82, 1.5
    st = Field("Stone")
    st.add(walls_box(0, 0, hx, hy, -0.04, z1, batter=0.02, amp=0.008, seed=seed), k=0.0)
    st.sub(RoundBox((-0.3, -hy, 0.34), (0.15, 0.08, 0.34), 0.012), k=0.004)                      # the tavern door
    st.sub(RoundBox((hx, 0.0, 0.38), (0.08, 0.27, 0.38), 0.012), k=0.004)                         # the warehouse doors
    st.sub(RoundBox((0.4, -hy, 0.45), (0.12, 0.08, 0.13), 0.01), k=0.004)                         # a window
    st.paint(Func(lambda P: (F32(0.25) - P[:, 2]).astype(F32), (-2, -2, -0.2), (2, 2, 1.0)), 7)
    ch = v3((-hx + 0.22, 0.25, 0))
    st.add(walls_box(ch[0], ch[1], 0.14, 0.14, z2 - 0.2, z2 + 1.0, batter=0.02, amp=0.008, seed=seed + 1), k=0.0)
    st.add(RoundBox((ch[0], ch[1], z2 + 0.98), (0.17, 0.17, 0.04), 0.01), k=0.006)
    st.sub(Cylinder((ch[0], ch[1], z2 + 1.04), 0.07, 0.12), k=0.004)
    ground_cut(st)
    out.append(("Stone", st, fine(0.008, 0.016), "rubble"))
    pl = Field("Plaster")
    jet = 0.07
    pl.add(RoundBox((0, -jet / 2, (z1 + z2) / 2), (hx + 0.02, hy + jet / 2, (z2 - z1) / 2), 0.01), k=0.0)
    for x in (-0.55, 0.05):
        pl.sub(RoundBox((x, -hy - jet, z1 + 0.36), (0.11, 0.08, 0.13), 0.01), k=0.004)              # upstairs windows
    pl.sub(RoundBox((hx + 0.02, 0.0, z1 + 0.34), (0.08, 0.17, 0.27), 0.01), k=0.004)                # the loft door
    pl.add(gable((0, -jet / 2), hx + 0.02, hy + jet / 2, z2 - 0.02, z2 + 0.66, axis="x"), k=0.0)     # the gables
    out.append(("Plaster", pl, fine(0.008, 0.016), "plaster"))
    wd = Field("Timber")
    _timber_frame(wd, hx + 0.03, hy + jet / 2 + 0.01, z1, z2, door_x=None, seed=seed)
    for k in range(7):                                              # the jetty's joist ends under the overhang
        x = -hx + 0.1 + k * (2 * hx - 0.2) / 6
        wd.add(RoundBox((x, -hy - jet + 0.02, z1 - 0.03), (0.035, 0.06, 0.035), 0.006), k=0.002, label=0)
    wd.add(RoundBox((-0.3, -hy + 0.01, 0.33), (0.135, 0.02, 0.32), 0.006), k=0.0, label=11)          # the doors
    wd.add(RoundBox((hx + 0.01, 0.0, 0.37), (0.02, 0.25, 0.36), 0.006), k=0.0, label=11)
    for sd in (-1, 1):                                              # crimson shutters
        wd.add(RoundBox((0.4 + sd * 0.19, -hy - 0.03, 0.45), (0.065, 0.012, 0.13), 0.004), k=0.0, label=5)
        for x in (-0.55, 0.05):
            wd.add(RoundBox((x + sd * 0.18, -hy - jet - 0.02, z1 + 0.36), (0.06, 0.012, 0.13), 0.004), k=0.0, label=5)
    hb0 = v3((hx + 0.02, 0, z2 + 0.42))                             # the hoist beam, its pulley, rope and hook
    wd.add(RoundBox(hb0 + v3((0.25, 0, 0)), (0.32, 0.045, 0.045), 0.01), k=0.0, label=10)
    wd.add(Cylinder(hb0 + v3((0.5, 0, -0.08)), 0.05, 0.03, rr=0.01, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.0, label=6)
    wd.add(RoundCone(hb0 + v3((0.54, 0, -0.08)), hb0 + v3((0.54, 0, -1.05)), 0.01, 0.01), k=0.0, label=8)
    wd.add(Torus(hb0 + v3((0.54, 0, -1.1)), 0.035, 0.01, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.004, label=6)
    br0 = v3((-hx + 0.15, -hy - jet - 0.01, z1 + 0.5))              # the sign's bracket and board
    wd.add(RoundCone(br0, br0 + v3((0, -0.42, 0)), 0.014, 0.014), k=0.0, label=6)
    wd.add(RoundCone(br0 + v3((0, 0, -0.2)), br0 + v3((0, -0.3, -0.01)), 0.01, 0.01), k=0.0, label=6)
    for yy in (-0.12, -0.36):
        wd.add(RoundCone(br0 + v3((0, yy, 0)), br0 + v3((0, yy, -0.07)), 0.007, 0.007), k=0.0, label=6)
    sg = v3((-hx + 0.15, -hy - jet - 0.25, z1 + 0.27))
    wd.add(RoundBox(sg, (0.018, 0.17, 0.15), 0.01), k=0.0, label=5)
    for sx in (-1, 1):                                              # an anchor painted on it (gold)
        wd.paint(RoundBox(sg + v3((sx * 0.02, 0, 0.02)), (0.01, 0.018, 0.09), 0.0), 6)
        wd.paint(Torus(sg + v3((sx * 0.02, 0, -0.03)), 0.06, 0.016, R=rot_from_axes(z_axis=(1, 0, 0))), 6)
        wd.paint(RoundBox(sg + v3((sx * 0.02, 0, 0.07)), (0.01, 0.06, 0.012), 0.0), 6)
    bn = v3((0.85, -hy - 0.22, 0.0))                                # a bench by the door
    wd.add(RoundBox(bn + v3((0, 0, 0.2)), (0.3, 0.08, 0.025), 0.006), k=0.0, label=10)
    for sx in (-1, 1):
        wd.add(RoundBox(bn + v3((sx * 0.24, 0, 0.1)), (0.025, 0.07, 0.1), 0.006), k=0.0, label=11)
    ground_cut(wd)
    out.append(("Timber", wd, fine(0.005, 0.01), "timber"))
    rf = Field("Roof")
    rf.add(gable((0, -jet / 2), hx + 0.16, hy + jet / 2 + 0.16, z2 - 0.04, z2 + 0.72, axis="x"), k=0.0)
    rf.ops[-1][1].disp = lambda P: (F32(0.012) * np.abs(np.sin(P[:, 0] * F32(36)))).astype(F32)
    rf.ops[-1][1].disp_amp = 0.014
    rf.add(RoundBox((0, -jet / 2, z2 + 0.71), (hx + 0.16, 0.05, 0.035), 0.03), k=0.01)
    out.append(("Roof", rf, fine(0.007, 0.014), "tiles"))
    dk = Field("Dark")
    dk.add(RoundBox((0.4, -hy + 0.04, 0.45), (0.11, 0.03, 0.12), 0.008), k=0.0)
    for x in (-0.55, 0.05):
        dk.add(RoundBox((x, -hy - jet + 0.04, z1 + 0.36), (0.1, 0.03, 0.12), 0.008), k=0.0)
    dk.add(RoundBox((hx - 0.03, 0.0, z1 + 0.34), (0.03, 0.16, 0.26), 0.008), k=0.0)
    out.append(("Dark", dk, fine(0.006, 0.012), "dark"))
    bb = Field("Barrels")
    add_barrel(bb, (-0.75, -hy - 0.25, 0.2), hl=0.19, r_end=0.13)
    add_barrel(bb, (-0.48, -hy - 0.3, 0.17), hl=0.16, r_end=0.12)
    add_barrel(bb, (hx + 0.35, 0.45, 0.19), R=rot_from_axes(z_axis=(0.2, 1.0, 0.0)), hl=0.19, r_end=0.12)
    ground_cut(bb)
    out.append(("Barrels", bb, fine(0.005, 0.01), "cask"))
    ln = Field("Lantern")
    lc = v3((-0.07, -hy - 0.1, 0.78))
    ln.add(RoundCone(lc + v3((0, 0.1, 0.06)), lc + v3((0, 0, 0.06)), 0.008, 0.008), k=0.0)
    ln.add(RoundBox(lc, (0.045, 0.045, 0.065), 0.01), k=0.004)
    ln.add(RoundCone(lc + v3((0, 0, 0.06)), lc + v3((0, 0, 0.11)), 0.055, 0.01), k=0.004)
    out.append(("Lantern", ln, fine(0.004, 0.008), "brass"))
    return out


def lookout(seed=0):
    """A lookout tower on the point: a round tower of rubble stone, whitewashed and flaking, a door at its foot; on
    top a plank platform behind a rail, four posts carrying a little roof of red tiles, a signal lantern and a bell; a
    ladder up its side; the smugglers' black pennant."""
    out = []
    st = Field("Stone")
    R0, R1, H = 0.52, 0.44, 1.15
    st.add(cone((0, 0), -0.05, H, R0, R1, wob(5.0, 0.01, seed)), k=0.0)
    st.add(Cylinder((0, 0, H - 0.05), R1 + 0.06, 0.1, rr=0.02), k=0.01)
    st.sub(RoundBox((0, -R0, 0.33), (0.13, 0.12, 0.33), 0.012), k=0.004)
    st.sub(RoundBox((R0 - 0.04, 0.05, 0.75), (0.08, 0.04, 0.09), 0.008), k=0.004)
    st.paint(Func(lambda P: (NOISE.fbm(P * F32(3.0) + F32(seed), 2) * F32(1.0) - F32(0.05)).astype(F32), (-1, -1, -0.1), (1, 1, 1.3)), 7)
    ground_cut(st)
    out.append(("Stone", st, fine(0.008, 0.016), "rubble"))
    wd = Field("Timber")
    zp = H + 0.02
    for k in range(9):
        x = -0.5 + k * 0.125
        wd.add(RoundBox((x, 0, zp), (0.058, 0.55, 0.02), 0.005), k=0.002, label=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            post(wd, (sx * 0.46, sy * 0.46, zp), (sx * 0.46, sy * 0.46, zp + 0.82), 0.03)
    for (a, b) in (((-0.46, -0.46), (0.46, -0.46)), ((-0.46, 0.46), (0.46, 0.46)), ((-0.46, -0.46), (-0.46, 0.46)), ((0.46, -0.46), (0.46, 0.46))):
        wd.add(RoundCone((a[0], a[1], zp + 0.36), (b[0], b[1], zp + 0.36), 0.02, 0.02), k=0.003, label=10)
        wd.add(RoundCone((a[0], a[1], zp + 0.18), (b[0], b[1], zp + 0.18), 0.015, 0.015), k=0.003, label=10)
    for sx in (-1, 1):                                              # the ladder up its side
        wd.add(RoundCone((0.9, sx * 0.14, -0.04), (0.5, sx * 0.14, zp + 0.3), 0.02, 0.018), k=0.0, label=11)
    for k in range(8):
        t = (k + 0.6) / 9
        p = v3((0.9 - 0.4 * t, 0, -0.04 + (zp + 0.34) * t))
        wd.add(RoundCone(p + v3((0, -0.14, 0)), p + v3((0, 0.14, 0)), 0.012, 0.012), k=0.0, label=10)
    wd.add(RoundCone((0, 0, zp + 1.05), (0, 0, zp + 1.75), 0.016, 0.012), k=0.0, label=11)
    ground_cut(wd)
    out.append(("Timber", wd, fine(0.005, 0.01), "timber"))
    rf = Field("Roof")
    rf.add(pyramid_roof((0, 0), 0.62, zp + 0.8, zp + 1.22), k=0.0)
    rf.ops[-1][1].disp = lambda P: (F32(0.01) * np.abs(np.sin((P[:, 0] + P[:, 1]) * F32(30)))).astype(F32)
    rf.ops[-1][1].disp_amp = 0.012
    rf.sub(pyramid_roof((0, 0), 0.55, zp + 0.75, zp + 1.12), k=0.005)
    out.append(("Roof", rf, fine(0.006, 0.012), "tiles"))
    br = Field("Brass")
    lc = v3((0.25, -0.3, zp + 0.55))
    br.add(RoundCone(lc + v3((0, 0, 0.2)), lc + v3((0, 0, 0.09)), 0.008, 0.008), k=0.0)
    br.add(RoundBox(lc, (0.05, 0.05, 0.08), 0.012), k=0.004)
    br.add(RoundCone(lc + v3((0, 0, 0.075)), lc + v3((0, 0, 0.13)), 0.06, 0.012), k=0.004)
    bc = v3((-0.2, 0.15, zp + 0.66))
    br.add(RoundCone(bc + v3((0, 0, 0.1)), bc + v3((0, 0, -0.04)), 0.04, 0.07), k=0.0)
    br.add(Torus(bc + v3((0, 0, -0.04)), 0.068, 0.01), k=0.006)
    out.append(("Brass", br, fine(0.004, 0.008), "brass"))
    fg = Field("Flag")
    fo = v3((0.02, 0, zp + 1.72))
    fg.add(flag(fo, 0.42, 0.26, seed, swallow=True), k=0.0)
    fg.paint(Func(lambda P: (np.abs(P[:, 2] - F32(zp + 1.59)) - F32(0.035)).astype(F32), fo - 1, fo + 1), 5)
    out.append(("Flag", fg, fine(0.004, 0.008), "flag_pirate"))
    return out


# ------------------------------------------------------------------------------------------------ the siege works
def wicker(c, r, nst=14, pitch=0.055, amp=0.006):
    """The weave of a gabion: withies passing alternately in front of and behind its stakes."""
    cx, cy = float(c[0]), float(c[1])

    def disp(P):
        th = np.arctan2(P[:, 1] - F32(cy), P[:, 0] - F32(cx))
        seg = np.floor((th + F32(math.pi)) / F32(2 * math.pi) * F32(nst))
        ph = (seg % F32(2)) * F32(math.pi)
        return (F32(amp) * np.sin(P[:, 2] * F32(2 * math.pi / pitch) + ph)).astype(F32)
    return dict(disp=disp, disp_amp=amp * 1.2)


def gabion(wk, ea, c, r=0.27, h=0.62, seed=0, stakes=14):
    """A gabion: a wicker basket (stakes, withies woven between them) filled with earth heaped a little over its rim."""
    c = v3(c)
    wk.add(Cylinder(c + v3((0, 0, h / 2)), r, h, rr=0.025, **wicker(c, r, stakes)), k=0.0)
    wk.sub(Cylinder(c + v3((0, 0, h + 0.01)), r - 0.03, 0.06), k=0.004)
    for k in range(stakes):
        a = 2 * math.pi * (k + 0.5) / stakes
        p = c + v3((math.cos(a) * (r - 0.006), math.sin(a) * (r - 0.006), 0))
        wk.add(RoundCone(p + v3((0, 0, h - 0.06)), p + v3((0, 0, h + 0.05)), 0.011, 0.008), k=0.004)
    ea.add(Ellipsoid(c + v3((0, 0, h - 0.04)), (r - 0.02, r - 0.02, 0.07), **wob(9.0, 0.012, seed)), k=0.0)


def gabions(seed=0, n=4):
    """A row of gabions as the sappers set them, one with a fascine laid over the gap to the next."""
    rng = np.random.default_rng(seed)
    wk, ea, fs = Field("Wicker"), Field("Earth"), Field("Fascine")
    r = 0.27
    xs_ = [(-(n - 1) / 2 + i) * (2 * r + 0.03) for i in range(n)]
    for i, x in enumerate(xs_):
        gabion(wk, ea, (x, rng.uniform(-0.03, 0.03), 0.0), r, 0.62 + rng.uniform(-0.03, 0.03), seed + i)
    fascine(fs, (xs_[1] - 0.25, -0.05, 0.7), (xs_[2] + 0.25, 0.05, 0.71), 0.085, seed)
    ground_cut(wk)
    return [("Wicker", wk, fine(0.005, 0.01), "wicker"), ("Earth", ea, fine(0.008, 0.016), "earthwork"),
            ("Fascine", fs, fine(0.005, 0.01), "brushwood")]


def fascine(f, a, b, r, seed, binds=4):
    """A fascine: a long bundle of brushwood bound with withies, twig ends sticking out."""
    a, b = v3(a), v3(b)
    ax = unit(b - a)
    L = float(np.linalg.norm(b - a))
    R = rot_from_axes(z_axis=ax)
    def twigs(P):
        Q = (P - a.astype(F32)) @ R.astype(F32)
        return (NOISE.fbm(Q * F32(np.array([60.0, 60.0, 4.0], np.float32)), 2) * F32(0.008)).astype(F32)
    f.add(Cylinder((a + b) / 2, r, L, rr=r * 0.5, R=R, disp=twigs, disp_amp=0.01), k=0.0)
    for k in range(binds):
        t = (k + 0.5) / binds
        f.add(Torus(a + (b - a) * t, r + 0.004, 0.012, R=R), k=0.003, label=5)
    rng = np.random.default_rng(seed)
    for end, sg in ((a, -1), (b, 1)):
        for k in range(5):
            o = R @ v3((rng.uniform(-0.6, 0.6) * r, rng.uniform(-0.6, 0.6) * r, 0.0))
            f.add(RoundCone(end + o, end + o + ax * sg * rng.uniform(0.04, 0.09), 0.01, 0.004), k=0.004)


def fascines(seed=0):
    """Fascines stacked for the sappers: three on the ground, two in the grooves over them, one on top."""
    fs = Field("Fascines")
    r, L = 0.1, 1.45
    for (y, z) in ((-0.2, r), (0.0, r), (0.2, r), (-0.1, r * 2.7), (0.1, r * 2.7), (0.0, r * 4.4)):
        fascine(fs, (-L / 2, y, z), (L / 2, y, z), r, int(y * 100 + z * 10) + seed)
    ground_cut(fs)
    return [("Fascines", fs, fine(0.005, 0.01), "brushwood")]


def bank(prof, path_pts, seed=0, amp=0.02):
    """An earth bank: the 2D cross-section `prof` [(across, z), ...] (across > 0 toward the bank's outside: the right of
    the path's direction, i.e. -Y for a straight bank along +X) swept along a polyline path (in plan), the segments
    overlapping a little at the joints, the bank's two ends slumping down."""
    P2 = [v3((p[0], p[1], 0.0)) for p in path_pts]
    segs = []
    total = 0.0
    for i in range(len(P2) - 1):
        a, b = P2[i], P2[i + 1]
        L = float(np.linalg.norm(b - a))
        segs.append((a, (b - a) / L, L, total, 0.0 if i == 0 else 0.3, 0.0 if i == len(P2) - 2 else 0.3))
        total += L
    W = max(abs(p[0]) for p in prof) + 0.1
    H = max(p[1] for p in prof) + 0.1

    def fn(P):
        best = None
        for a, dv, L, s0, e0, e1 in segs:
            qx, qy = P[:, 0] - F32(a[0]), P[:, 1] - F32(a[1])
            u = qx * F32(dv[0]) + qy * F32(dv[1])
            across = qx * F32(dv[1]) - qy * F32(dv[0])
            s = F32(s0) + np.clip(u, 0, L)
            dend = np.maximum(F32(0.0), np.maximum(F32(0.4) - s, s - F32(total - 0.4)))
            zs = P[:, 2] + dend * F32(1.1)                          # the ends slump down
            d = np.maximum(poly_sdf2(across, zs, prof), np.maximum(-u - F32(e0), u - F32(L + e1)))
            best = d if best is None else np.minimum(best, d)
        return (best * F32(0.85)).astype(F32)
    lo = np.min(P2, 0) - W
    hi = np.max(P2, 0) + W
    lo[2], hi[2] = -0.1, H
    return Func(fn, lo, hi, **wob(4.0, amp, seed))


def rampart(seed=0):
    """A curved section of the besiegers' earthen rampart (a redoubt's face): a bank of fresh-dug earth, its outer slope
    toward -Y, a firing step behind the crest, gabions along the crest, stakes revetting its inner foot."""
    rng = np.random.default_rng(seed)
    ea, wk, wd = Field("Earth"), Field("Wicker"), Field("Timber")
    prof = [(0.62, -0.05), (0.62, 0.0), (0.22, 0.58), (-0.08, 0.6), (-0.22, 0.32), (-0.48, 0.3), (-0.62, 0.0), (-0.62, -0.05)]
    Rc = 2.4
    path = [v3((Rc * math.sin(a), Rc - Rc * math.cos(a), 0.0)) for a in np.linspace(0.55, -0.55, 13)]
    ea.add(bank(prof, path, seed=seed), k=0.0)
    ground_cut(ea)
    for k, a in enumerate(np.linspace(0.42, -0.42, 5)):            # gabions along the crest
        c = v3((Rc * math.sin(a), Rc - Rc * math.cos(a), 0.0)) + v3((-math.sin(a), math.cos(a), 0.0)) * 0.0
        gabion(wk, ea, (c[0] - math.sin(a) * 0.05, c[1] + math.cos(a) * 0.05, 0.55), 0.2, 0.42, seed + k, stakes=12)
    for k, a in enumerate(np.linspace(0.48, -0.48, 11)):           # stakes revetting the inner foot
        n = v3((math.sin(a), -math.cos(a), 0.0))
        c = v3((Rc * math.sin(a), Rc - Rc * math.cos(a), 0.0)) - n * 0.55
        post(wd, c + v3((0, 0, -0.05)), c + v3((0, 0, 0.36)), 0.022, pointed=True)
    ground_cut(wd)
    return [("Earth", ea, fine(0.01, 0.02), "earthwork"), ("Wicker", wk, fine(0.005, 0.01), "wicker"),
            ("Timber", wd, fine(0.005, 0.01), "timber")]


def sandbag(f, c, yaw, half=(0.11, 0.065, 0.045), seed=0):
    R = Rz(yaw)
    f.add(RoundBox(c, half, min(half) * 0.9, R=R, **wob(14.0, 0.004, seed)), k=0.004)
    f.add(Ellipsoid(c + R @ v3((half[0] * 0.95, 0, 0)), (0.025, half[1] * 0.7, half[2] * 0.7), R=R), k=0.01, label=5)


def trench(seed=0, L=2.4):
    """A length of siege trench: the parapet of earth thrown up toward the fort (-Y), sandbags laid two deep along its
    crest with loopholes left between them, the trench's inner face revetted with planks between stakes."""
    rng = np.random.default_rng(seed)
    ea, sb, wd = Field("Earth"), Field("Sandbags"), Field("Timber")
    prof = [(0.75, -0.05), (0.75, 0.0), (0.15, 0.36), (-0.12, 0.38), (-0.35, 0.05), (-0.35, -0.05)]
    ea.add(bank(prof, [v3((-L / 2, 0, 0)), v3((L / 2, 0, 0))], seed=seed), k=0.0)
    ground_cut(ea)
    for layer in range(3):
        z = 0.42 + layer * 0.085
        n = int((L - 0.6) / 0.235)
        for i in range(n):
            x = -L / 2 + 0.35 + i * 0.235 + (0.117 if layer % 2 else 0.0)
            if layer == 2 and i in (2, n - 3):
                continue                                            # loopholes
            if x > L / 2 - 0.3:
                continue
            for row, y in enumerate((-0.05, 0.08)):
                if layer == 2 and row == 0:
                    continue
                sandbag(sb, v3((x + rng.uniform(-0.01, 0.01), y, z)), rng.uniform(-0.06, 0.06), seed=seed + layer * 50 + i * 2 + row)
    for k in range(7):                                              # the revetment behind
        x = -L / 2 + 0.3 + k * (L - 0.6) / 6
        post(wd, (x, 0.32, -0.05), (x, 0.32, 0.42), 0.022)
    for z in (0.08, 0.2, 0.32):
        wd.add(RoundBox((0, 0.3, z), (L / 2 - 0.25, 0.012, 0.055), 0.006), k=0.0, label=10)
    ground_cut(wd)
    return [("Earth", ea, fine(0.01, 0.02), "earthwork"), ("Sandbags", sb, fine(0.005, 0.01), "sandbag"),
            ("Timber", wd, fine(0.005, 0.01), "timber")]


def spoked_wheel(f, c, axis, r=0.36, n=12, w=0.05, broken=None, seed=0):
    """A spoked wheel (axle along `axis`): hub, spokes, a felloe and an iron tyre (label 6); `broken` = spokes missing."""
    c = v3(c)
    R = rot_from_axes(z_axis=axis)
    f.add(Torus(c, r - 0.03, 0.028, R=R), k=0.0, label=10)
    f.add(Torus(c, r - 0.005, 0.016, R=R), k=0.003, label=6)
    f.add(Cylinder(c, 0.07, w * 2.4, rr=0.015, R=R), k=0.004, label=10)
    f.add(Cylinder(c, 0.04, w * 3.0, rr=0.01, R=R), k=0.004, label=6)
    for k in range(n):
        if broken and k in broken:
            continue
        a = 2 * math.pi * k / n
        d = R @ v3((math.cos(a), math.sin(a), 0.0))
        f.add(RoundCone(c + d * 0.06, c + d * (r - 0.04), 0.017, 0.013), k=0.004, label=11)


def cannon_barrel(f, breech, muzzle, r0=0.1, r1=0.075, rm=0.088, label=0):
    """A cannon's barrel from the breech to the muzzle: the base ring, the reinforces, the chase tapering to the muzzle's
    swell, the cascabel's knob behind, trunnions on its sides, two dolphins on top."""
    a, b = v3(breech), v3(muzzle)
    ax = unit(b - a)
    L = float(np.linalg.norm(b - a))
    R = rot_from_axes(z_axis=ax)
    f.add(RoundCone(a, b, r0, r1), k=0.0, label=label)
    f.add(RoundCone(a + ax * (-0.02), a + ax * 0.05, r0 + 0.01, r0 + 0.01), k=0.01, label=label)
    for t, rr in ((0.32, r0 * 0.96), (0.55, r1 * 1.12)):
        f.add(Torus(a + ax * (L * t), rr, 0.012, R=R), k=0.004, label=label)
    f.add(Torus(b - ax * 0.04, rm, 0.018, R=R), k=0.006, label=label)
    f.add(RoundCone(a, a - ax * 0.07, r0 * 0.5, 0.03), k=0.015, label=label)
    f.add(Sphere(a - ax * 0.11, 0.04), k=0.01, label=label)
    sd = R @ v3((1, 0, 0))
    up = R @ v3((0, 1, 0))
    if up[2] < 0:
        up = -up
    tc = a + ax * (L * 0.38)
    f.add(RoundCone(tc - sd * (r0 + 0.07), tc + sd * (r0 + 0.07), 0.032, 0.032), k=0.008, label=label)
    for t in (0.3, 0.45):
        p = a + ax * (L * t) + up * r0
        f.add(Torus(p + up * 0.02, 0.035, 0.01, R=rot_from_axes(z_axis=sd)), k=0.006, label=label)
    f.sub(Cylinder(b, r1 * 0.55, 0.12, R=R), k=0.004)
    return tc


def field_gun(seed=0, bronze=True):
    """A field gun on its carriage (its muzzle toward -Y): a bronze barrel on two cheeks, the trail on the ground behind,
    two big spoked wheels with iron tyres, a quoin under the breech, iron fittings; a rammer lying by it."""
    out = []
    ca, wh, gn = Field("Carriage"), Field("Wheels"), Field("Barrel")
    rw = 0.36
    for sx in (-1, 1):                                              # the cheeks: brackets of timber
        o = v3((sx * 0.12, 0.0, 0.0))
        poly = [(-0.22, 0.34), (-0.18, 0.56), (0.08, 0.6), (0.22, 0.5), (1.02, 0.14), (1.02, 0.02), (0.75, 0.0), (0.15, 0.28), (-0.22, 0.28)]
        ca.add(leaf(o, (0, 1, 0), (0, 0, 1), poly, 0.032), k=0.0, label=10)
        ca.paint(Func(lambda P, sx=sx: (np.abs(P[:, 0] - F32(sx * 0.12)) - F32(0.05)).astype(F32), (-1, -1, -0.2), (1, 2, 1)), 7)
    ca.add(RoundBox((0, 0.0, rw), (0.34, 0.05, 0.05), 0.012), k=0.004, label=10)                      # the axle tree
    ca.add(RoundBox((0, 0.55, 0.3), (0.1, 0.04, 0.04), 0.01), k=0.004, label=10)                      # transoms
    ca.add(RoundBox((0, 0.92, 0.09), (0.12, 0.08, 0.05), 0.012), k=0.004, label=10)                   # the trail's end
    ca.add(Torus((0, 1.03, 0.1), 0.045, 0.012, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004, label=6)
    ca.add(convex([((0, 0.22, 0.47), (0, -0.4, 1)), ((0, 0.4, 0.38), (0, 1, 0)), ((0, 0.14, 0.38), (0, -1, 0)), ((0.07, 0, 0), (1, 0, 0)),
                   ((-0.07, 0, 0), (-1, 0, 0)), ((0, 0, 0.36), (0, 0, -1))], (-0.1, 0.1, 0.3), (0.1, 0.45, 0.55)), k=0.0, label=10)  # the quoin
    for sx in (-1, 1):
        ca.add(RoundBox((sx * 0.12, 0.0, 0.6), (0.045, 0.06, 0.012), 0.004), k=0.002, label=6)        # the capsquares
    ground_cut(ca)
    out.append(("Carriage", ca, fine(0.005, 0.01), "carriage"))
    for sx in (-1, 1):
        spoked_wheel(wh, (sx * 0.38, 0.0, rw), (1, 0, 0), rw, 12, seed=seed + sx)
    ground_cut(wh)
    out.append(("Wheels", wh, fine(0.005, 0.01), "carriage"))
    el = math.radians(6)
    br = v3((0, 0.32, 0.6))
    mz = br + v3((0, -math.cos(el), math.sin(el))) * 1.15
    cannon_barrel(gn, br, mz)
    out.append(("Barrel", gn, fine(0.004, 0.008), "gun_bronze" if bronze else "gun_iron"))
    rm = Field("Rammer")
    a, b = v3((0.55, -0.6, 0.03)), v3((0.65, 0.75, 0.03))
    rm.add(RoundCone(a, b, 0.016, 0.016), k=0.0, label=11)
    rm.add(Cylinder(a, 0.045, 0.09, rr=0.012, R=rot_from_axes(z_axis=unit(b - a))), k=0.01, label=10)
    rm.add(Cylinder(b, 0.05, 0.12, rr=0.02, R=rot_from_axes(z_axis=unit(b - a))), k=0.01, label=9)
    rm.inter(Plane((0, 0, -0.01), (0, 0, -1)))
    out.append(("Rammer", rm, fine(0.005, 0.01), "carriage"))
    dk = Field("Dark")
    dk.add(Cylinder(mz - unit(mz - br) * 0.02, 0.04, 0.03, R=rot_from_axes(z_axis=unit(mz - br))), k=0.0)
    out.append(("Dark", dk, fine(0.004, 0.008), "dark"))
    return out


def mortar(seed=0):
    """A siege mortar (its mouth toward -Y): a short wide bronze barrel cocked up at 45 degrees on its trunnions between
    the cheeks of a heavy oak bed bound with iron, three shells by it with their fuses."""
    out = []
    bd, gn, sh = Field("Bed"), Field("Barrel"), Field("Shells")
    bd.add(RoundBox((0, 0.05, 0.1), (0.28, 0.36, 0.1), 0.02), k=0.0, label=10)
    for sx in (-1, 1):
        o = v3((sx * 0.24, 0, 0))
        bd.add(leaf(o, (0, 1, 0), (0, 0, 1), [(-0.25, 0.15), (-0.18, 0.42), (0.08, 0.46), (0.35, 0.2), (0.38, 0.15)], 0.045), k=0.01, label=10)
        for y in (-0.15, 0.25):
            bd.add(RoundBox((sx * 0.24, y, 0.2), (0.05, 0.02, 0.1), 0.004), k=0.002, label=6)
    ground_cut(bd)
    out.append(("Bed", bd, fine(0.005, 0.01), "carriage"))
    a = v3((0, 0.12, 0.36))
    d = unit(v3((0, -1.0, 1.0)))
    b = a + d * 0.5
    gn.add(RoundCone(a - d * 0.08, b, 0.15, 0.17), k=0.0)
    gn.add(Sphere(a - d * 0.06, 0.14), k=0.03)
    R = rot_from_axes(z_axis=d)
    for t in (0.12, 0.3):
        gn.add(Torus(a + d * t, 0.165, 0.016, R=R), k=0.004)
    gn.add(Torus(b - d * 0.02, 0.17, 0.022, R=R), k=0.005)
    gn.add(RoundCone((-0.27, 0.12, 0.36), (0.27, 0.12, 0.36), 0.045, 0.045), k=0.01)
    gn.sub(Cylinder(b, 0.115, 0.36, R=R), k=0.006)
    out.append(("Barrel", gn, fine(0.005, 0.01), "gun_bronze"))
    dk = Field("Dark")
    dk.add(Cylinder(b - d * 0.12, 0.12, 0.04, R=R), k=0.0)
    out.append(("Dark", dk, fine(0.005, 0.01), "dark"))
    for (x, y) in ((0.42, -0.25), (0.5, 0.05), (0.62, -0.12)):
        c = v3((x, y, 0.09))
        sh.add(Sphere(c, 0.09), k=0.0)
        sh.add(Cylinder(c + v3((0, 0, 0.09)), 0.022, 0.04, rr=0.005), k=0.004, label=6)
    ground_cut(sh)
    out.append(("Shells", sh, fine(0.005, 0.01), "shot"))
    return out


def shot_pyramid(seed=0, n=4, r=0.075):
    """Round shot stacked in a square pyramid on two planks."""
    f = Field("Shot")
    z0 = 0.04
    for k in range(n):
        m = n - k
        for i in range(m):
            for j in range(m):
                x = (i - (m - 1) / 2) * 2 * r
                y = (j - (m - 1) / 2) * 2 * r
                f.add(Sphere((x, y, z0 + r + k * r * math.sqrt(2)), r), k=0.0)
    out = [("Shot", f, fine(0.005, 0.01), "shot")]
    wd = Field("Planks")
    for y in (-0.12, 0.12):
        wd.add(RoundBox((0, y, 0.02), (n * r + 0.06, 0.09, 0.022), 0.006), k=0.0, label=10)
    ground_cut(wd)
    out.append(("Planks", wd, fine(0.005, 0.01), "timber"))
    return out


def powder_kegs(seed=0):
    """Powder kegs with copper hoops (no iron near the powder): three in a row, one on them, one on its side, POWDER
    daubed on them in black."""
    f = Field("Kegs")
    for (x, y) in ((-0.25, 0.0), (0.0, 0.03), (0.25, -0.01)):
        add_barrel(f, (x, y, 0.15), hl=0.15, r_end=0.1, bulge=0.018, hoops=(0.8, 0.35),
                   mark=RoundBox((x, y - 0.12, 0.16), (0.07, 0.04, 0.03), 0.0))
    add_barrel(f, (-0.12, 0.015, 0.43), R=Rz(0.5), hl=0.15, r_end=0.1, bulge=0.018, hoops=(0.8, 0.35))
    add_barrel(f, (0.32, -0.36, 0.11), R=rot_from_axes(z_axis=(math.cos(-0.4), math.sin(-0.4), 0)), hl=0.15, r_end=0.1, bulge=0.018,
               hoops=(0.8, 0.35))
    ground_cut(f)
    return [("Kegs", f, fine(0.005, 0.01), "keg")]


def bell_tent(seed=0, R=0.68, H=1.3):
    """A soldiers' bell tent: white canvas falling from its pole in a concave cone to a short wall, the door flaps tied
    back on a dark doorway, guy ropes pegged out round it, a knob on the pole."""
    c = Field("Canvas")

    def tent(P):
        q = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        z = P[:, 2]
        t = np.clip(z / F32(H), 0, 1)
        prof = np.where(z < F32(0.16), F32(R), F32(R) * (F32(1) - np.clip((z - F32(0.16)) / F32(H - 0.16), 0, 1)) ** F32(1.25))
        return (np.maximum(q - prof, np.maximum(-z, z - F32(H))) * F32(0.7)).astype(F32)
    c.add(Func(tent, (-R - 0.1, -R - 0.1, -0.05), (R + 0.1, R + 0.1, H + 0.05), **wob(6.0, 0.006, seed)), k=0.0)
    for k in range(10):                                             # the seams' gentle ridges
        a = 2 * math.pi * k / 10
        c.add(RoundCone((math.cos(a) * R * 0.98, math.sin(a) * R * 0.98, 0.17), (0, 0, H - 0.02), 0.008, 0.006), k=0.006, label=5)
    c.sub(RoundBox((0, -R, 0.28), (0.13, 0.25, 0.3), 0.03), k=0.01)
    for sd in (-1, 1):
        c.add(Ellipsoid((sd * 0.19, -R * 0.92, 0.3), (0.06, 0.035, 0.28), R=Rz(sd * 0.5)), k=0.012)
    c.paint(Func(lambda P: (np.abs(P[:, 2] - F32(0.1)) - F32(0.05)).astype(F32), (-2, -2, -0.1), (2, 2, 2)), 5)
    ground_cut(c)
    out = [("Canvas", c, fine(0.006, 0.012), "canvas")]
    wd = Field("Pole")
    wd.add(RoundCone((0, 0, H - 0.05), (0, 0, H + 0.14), 0.02, 0.016), k=0.0, label=11)
    wd.add(Sphere((0, 0, H + 0.16), 0.03), k=0.004, label=6)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        if abs(math.sin(a) + 1) < 0.25:
            continue
        p0 = v3((math.cos(a) * R * 0.96, math.sin(a) * R * 0.96, 0.17))
        p1 = v3((math.cos(a) * (R + 0.42), math.sin(a) * (R + 0.42), 0.03))
        wd.add(RoundCone(p0, p1, 0.006, 0.006), k=0.0, label=8)
        wd.add(RoundCone(p1 + v3((0, 0, -0.05)), p1 + v3((0, 0, 0.05)), 0.012, 0.01), k=0.004, label=10)
    ground_cut(wd)
    out.append(("Pole", wd, fine(0.005, 0.01), "timber"))
    dk = Field("Dark")
    dk.add(RoundBox((0, -R + 0.08, 0.27), (0.11, 0.04, 0.27), 0.02), k=0.0)
    out.append(("Dark", dk, fine(0.006, 0.012), "dark"))
    return out


def marquee(seed=0):
    """The officers' marquee: white canvas walls under a hipped roof edged with a scalloped blue valance, its poles
    through the ridge flying blue swallow-tailed pennants, the front flap stretched out as an awning on two poles over
    a camp table spread with a map, two folding chairs; guy ropes."""
    out = []
    hx, hy, wh, rh = 0.85, 0.55, 0.62, 1.22
    c = Field("Canvas")
    c.add(RoundBox((0, 0, wh / 2), (hx, hy, wh / 2), 0.02), k=0.0)
    c.add(convex([((0, 0, rh), (0, 0.95, 1)), ((0, 0, rh), (0, -0.95, 1)), ((hx - 0.25, 0, rh), (1.4, 0, 1)), ((-hx + 0.25, 0, rh), (-1.4, 0, 1)),
                   ((0, 0, wh - 0.04), (0, 0, -1))], (-hx - 0.3, -hy - 0.3, wh - 0.1), (hx + 0.3, hy + 0.3, rh + 0.1)), k=0.02)
    for x in np.linspace(-hx, hx, 9):                               # the valance's scallops
        for sy in (-1, 1):
            c.add(Ellipsoid((x, sy * (hy + 0.03), wh - 0.03), (0.1, 0.02, 0.065)), k=0.008, label=5)
    for y in np.linspace(-hy, hy, 6):
        for sx in (-1, 1):
            c.add(Ellipsoid((sx * (hx + 0.03), y, wh - 0.03), (0.02, 0.1, 0.065)), k=0.008, label=5)
    c.sub(RoundBox((0, -hy, 0.28), (0.22, 0.1, 0.3), 0.02), k=0.008)
    aw = Field("Awning")                                            # the awning on its poles
    aw.add(leaf((0, -hy - 0.02, wh - 0.02), (0, -1, -0.28), (1, 0, 0), [(0.0, -0.4), (0.0, 0.4), (0.62, 0.4), (0.62, -0.4)], 0.008,
                cup=-0.15), k=0.0)
    aw.paint(Func(lambda P: (P[:, 1] + F32(hy + 0.53)).astype(F32), (-1, -2, 0), (1, 0, 2)), 5)
    ground_cut(c)
    out += [("Canvas", c, fine(0.006, 0.012), "canvas"), ("Awning", aw, fine(0.005, 0.01), "canvas")]
    wd = Field("Timber")
    for sx in (-1, 1):
        post(wd, (sx * 0.38, -hy - 0.62, -0.04), (sx * 0.38, -hy - 0.62, wh - 0.16), 0.016)
        post(wd, (sx * (hx - 0.25), 0, rh - 0.05), (sx * (hx - 0.25), 0, rh + 0.32), 0.018)
        wd.add(Sphere((sx * (hx - 0.25), 0, rh + 0.34), 0.025), k=0.004, label=6)
    tb = v3((0.0, -hy - 0.4, 0.0))                                  # the camp table and its map
    wd.add(RoundBox(tb + v3((0, 0, 0.36)), (0.22, 0.14, 0.015), 0.005), k=0.0, label=10)
    for sx in (-1, 1):
        wd.add(RoundCone(tb + v3((sx * 0.18, -0.1, 0.0)), tb + v3((-sx * 0.18, 0.1, 0.35)), 0.01, 0.01), k=0.004, label=11)
    for (x, y, yaw) in ((-0.38, -hy - 0.36, 0.4), (0.36, -hy - 0.5, -0.6)):
        R = Rz(yaw)
        o = v3((x, y, 0))
        wd.add(RoundBox(o + v3((0, 0, 0.22)), (0.09, 0.08, 0.012), 0.004, R=R), k=0.0, label=10)
        for sx in (-1, 1):
            wd.add(RoundCone(o + R @ v3((sx * 0.08, -0.08, 0.0)), o + R @ v3((-sx * 0.08, 0.08, 0.22)), 0.008, 0.008), k=0.0, label=11)
        wd.add(RoundBox(o + R @ v3((0, 0.08, 0.33)), (0.085, 0.01, 0.06), 0.004, R=R), k=0.0, label=9)
    for k in range(6):                                              # guy ropes
        a = [0.5, 1.2, 2.0, 2.6, -0.5, -2.6][k]
        p0 = v3((math.cos(a) * hx * 0.95, math.sin(a) * hy * 0.95, wh))
        p1 = p0 + v3((math.cos(a) * 0.5, math.sin(a) * 0.5, -wh + 0.03))
        wd.add(RoundCone(p0, p1, 0.006, 0.006), k=0.0, label=8)
        wd.add(RoundCone(p1 + v3((0, 0, -0.05)), p1 + v3((0, 0, 0.05)), 0.012, 0.01), k=0.004, label=10)
    ground_cut(wd)
    out.append(("Timber", wd, fine(0.005, 0.01), "timber"))
    mp = Field("Map")
    mp.add(RoundBox(tb + v3((0.02, 0.0, 0.38)), (0.13, 0.09, 0.004), 0.002, R=Rz(0.25)), k=0.0)
    out.append(("Map", mp, fine(0.004, 0.008), "map"))
    pn = Field("Pennants")
    for sx in (-1, 1):
        fo = v3((sx * (hx - 0.25) + 0.02, 0, rh + 0.3))
        pn.add(flag(fo, 0.36, 0.13, seed + sx, swallow=True), k=0.0)
    out.append(("Pennants", pn, fine(0.004, 0.008), "flag_blue"))
    dk = Field("Dark")
    dk.add(RoundBox((0, -hy + 0.06, 0.28), (0.2, 0.04, 0.28), 0.02), k=0.0)
    out.append(("Dark", dk, fine(0.006, 0.012), "dark"))
    return out


def supply_wagon(seed=0):
    """A supply wagon: a plank box on four spoked wheels (the front pair smaller), a canvas tilt on hoops open at the
    back on barrels and sacks, its pole down on the ground in front (-X)."""
    out = []
    wd, wh, cv, ld = Field("Body"), Field("Wheels"), Field("Tilt"), Field("Load")
    L, Wb, zb = 0.72, 0.32, 0.42
    wd.add(RoundBox((0, 0, zb), (L, Wb, 0.035), 0.01), k=0.0, label=10)
    for sy in (-1, 1):
        wd.add(RoundBox((0, sy * Wb, zb + 0.15), (L, 0.025, 0.15), 0.008), k=0.003, label=10)
        for x in np.linspace(-L + 0.05, L - 0.05, 6):
            wd.add(RoundBox((x, sy * (Wb + 0.02), zb + 0.15), (0.018, 0.012, 0.15), 0.004), k=0.002, label=11)
    for sx in (-1, 1):
        wd.add(RoundBox((sx * L, 0, zb + 0.12), (0.025, Wb, 0.12), 0.008), k=0.003, label=10)
    for x, r in ((-0.5, 0.29), (0.48, 0.37)):
        wd.add(RoundBox((x, 0, r), (0.05, Wb + 0.12, 0.04), 0.01), k=0.004, label=0)
    wd.add(RoundCone((-0.55, 0, 0.3), (-1.55, 0, 0.04), 0.03, 0.025), k=0.004, label=10)              # the pole
    ground_cut(wd)
    out.append(("Body", wd, fine(0.005, 0.01), "wagon"))
    for x, r in ((-0.5, 0.29), (0.48, 0.37)):
        for sy in (-1, 1):
            spoked_wheel(wh, (x, sy * (Wb + 0.14), r), (0, 1, 0), r, 10, w=0.04, seed=seed + int(x * 10) + sy)
    ground_cut(wh)
    out.append(("Wheels", wh, fine(0.005, 0.01), "wagon"))

    def tilt(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        cz = F32(zb + 0.3)
        rr = np.sqrt(y * y + np.maximum(z - cz, F32(0)) ** 2 * F32(0.9))
        d = np.abs(rr - F32(Wb + 0.06)) - F32(0.012)
        d = np.maximum(d, np.abs(x) - F32(L - 0.02))
        d = np.maximum(d, cz - F32(0.02) - z)
        return (d * F32(0.85)).astype(F32)
    cv.add(Func(tilt, (-L, -Wb - 0.2, zb), (L, Wb + 0.2, zb + 0.8), **wob(6.0, 0.006, seed)), k=0.0)
    for x in np.linspace(-L + 0.06, L - 0.06, 4):
        cv.add(Func(lambda P, x=x: (np.maximum(np.abs(np.sqrt(P[:, 1] ** 2 + np.maximum(P[:, 2] - F32(zb + 0.3), 0) ** 2 * F32(0.9)) - F32(Wb + 0.075)) - F32(0.01),
                                               np.abs(P[:, 0] - F32(x)) - F32(0.018)) * F32(0.85)).astype(F32),
                    (x - 0.05, -Wb - 0.2, zb + 0.25), (x + 0.05, Wb + 0.2, zb + 0.8)), k=0.004, label=5)
    out.append(("Tilt", cv, fine(0.006, 0.012), "canvas"))
    add_barrel(ld, (0.5, -0.1, zb + 0.18), hl=0.14, r_end=0.1, bulge=0.018)
    ld.add(Ellipsoid((0.45, 0.14, zb + 0.15), (0.12, 0.11, 0.13), **wob(8.0, 0.01, seed)), k=0.0, label=9)
    out.append(("Load", ld, fine(0.005, 0.01), "wagon"))
    return out


def broken_wheels(seed=0):
    """Wreckage: a gun wheel lying flat with spokes missing and its felloe split, another half sunk on its edge against
    a broken axle, loose spokes in the grass."""
    rng = np.random.default_rng(seed)
    f = Field("Wheels")
    spoked_wheel(f, (0.0, 0.0, 0.05), (0.15, 0.1, 1.0), 0.36, 12, broken={2, 3, 7}, seed=seed)
    f.sub(Ellipsoid((0.3, 0.2, 0.05), (0.08, 0.08, 0.1)), k=0.01)
    spoked_wheel(f, (0.72, 0.35, 0.25), (0.9, -0.3, 0.35), 0.33, 12, broken={5}, seed=seed + 1)
    f.add(RoundCone((0.72, 0.35, 0.25), (1.05, 0.2, 0.02), 0.045, 0.04), k=0.01, label=10)
    for k in range(4):
        a = rng.uniform(0, 2 * math.pi)
        q = v3((rng.uniform(-0.5, 0.4), rng.uniform(-0.6, -0.3), 0.02))
        f.add(RoundCone(q, q + v3((math.cos(a) * 0.28, math.sin(a) * 0.28, 0.0)), 0.016, 0.013), k=0.0, label=11)
    f.inter(Plane((0, 0, 0.0), (0, 0, -1)))
    return [("Wheels", f, fine(0.005, 0.01), "wagon")]


# ------------------------------------------------------------------------------------------------ the siege landmarks
def redoubt(seed=0):
    """A redoubt: a small square fort of earth (ramparts with an outer slope, a crest and a firing step inside, their
    corners rounded), two embrasures cut through its front (-Y) with field guns run up to them, gabions along the other
    faces, its entrance at the back closed by a barrier of pointed stakes, a powder magazine dug in at the back, the
    besiegers' flag on a pole in the middle."""
    rng = np.random.default_rng(seed)
    out = []
    ea = Field("Earth")
    S = 1.45
    prof = [(0.62, -0.05), (0.62, 0.0), (0.2, 0.62), (-0.08, 0.64), (-0.2, 0.34), (-0.45, 0.32), (-0.6, 0.0), (-0.6, -0.05)]

    def sq(P):                                                      # a rounded square's "radius" (its distance out from the middle)
        ax, ay = np.abs(P[:, 0]), np.abs(P[:, 1])
        m = np.maximum(ax, ay)
        rc = F32(0.45)
        cx, cy = np.maximum(ax - F32(S - 0.45), 0), np.maximum(ay - F32(S - 0.45), 0)
        return np.where((cx > 0) & (cy > 0), F32(S - 0.45) + np.sqrt(cx * cx + cy * cy), m)

    def ramp(P):
        across = sq(P) - F32(S)
        return (poly_sdf2(across, P[:, 2], prof) * F32(0.85)).astype(F32)
    ea.add(Func(ramp, (-S - 0.8, -S - 0.8, -0.1), (S + 0.8, S + 0.8, 0.75), **wob(3.0, 0.02, seed)), k=0.0)
    for sx in (-1, 1):                                              # the embrasures in its front
        ea.sub(convex([((sx * 0.55, -S, 0.4), (0, 0, -1)), ((sx * 0.55 + 0.14, -S, 0), (1, -0.35, 0)), ((sx * 0.55 - 0.14, -S, 0), (-1, -0.35, 0))],
                      (sx * 0.55 - 0.6, -S - 0.8, 0.35), (sx * 0.55 + 0.6, -S + 0.4, 0.9)), k=0.03)
    ea.sub(RoundBox((0, S, 0.3), (0.3, 0.9, 0.5), 0.05), k=0.05)                                       # the entrance
    ea.add(convex_w([((0, 0, 0.25), (0, 0, 1)), ((0, 0, -0.05), (0, 0, -1)), ((-0.25, 0, 0), (1, 0, 0.4)), ((-1.05, 0, 0), (-1, 0, 0.4)),
                     ((0, 0.95, 0), (0, 1, 0.4)), ((0, 0.45, 0), (0, -1, 0.4))], (-1.2, 0.3, -0.1), (-0.1, 1.1, 0.35), 0.01, 3.0, seed + 3), k=0.05)
    ground_cut(ea)
    out.append(("Earth", ea, fine(0.012, 0.024), "earthwork"))
    wk, ea2 = Field("Wicker"), Field("Earth2")
    for sx in (-1, 1):                                              # gabions along the side faces
        for k in range(4):
            y = -0.8 + k * 0.45
            gabion(wk, ea2, (sx * (S - 0.05), y, 0.6), 0.17, 0.34, seed + k + 10 * sx, stakes=11)
    for x in (-0.95, 0.95):                                         # and beside the embrasures
        gabion(wk, ea2, (x, -S + 0.02, 0.6), 0.17, 0.34, seed + 30 + int(x * 10), stakes=11)
    out += [("Wicker", wk, fine(0.005, 0.01), "wicker"), ("Earth2", ea2, fine(0.008, 0.016), "earthwork")]
    for sx in (-1, 1):                                              # the guns run up to the embrasures
        g = field_gun(seed + 40 + sx)
        place_parts(out, [(n, f, vxs, m) for (n, f, vxs, m) in g if n != "Rammer"], (sx * 0.55, -S + 0.75, 0.0))
    wd = Field("Timber")
    for k in range(7):                                              # the barrier across the entrance
        x = -0.3 + k * 0.1
        post(wd, (x, S + 0.05, -0.05), (x + 0.05 * math.sin(k), S + 0.2, 0.55), 0.025, pointed=True)
    wd.add(RoundCone((-0.38, S + 0.1, 0.25), (0.38, S + 0.1, 0.25), 0.03, 0.03), k=0.004, label=10)
    wd.add(gable((-0.65, 0.7), 0.42, 0.3, 0.22, 0.48, axis="x"), k=0.0, label=10)                       # the magazine's roof
    wd.add(RoundBox((-0.65, 0.42, 0.13), (0.14, 0.03, 0.13), 0.01), k=0.0, label=11)
    post(wd, (0.2, 0.25, -0.05), (0.2, 0.25, 2.6), 0.03, 0.022)                                           # the flagpole
    wd.add(Sphere((0.2, 0.25, 2.62), 0.035), k=0.004, label=6)
    ground_cut(wd)
    out.append(("Timber", wd, fine(0.005, 0.01), "timber"))
    fg = Field("Flag")
    fo = v3((0.22, 0.25, 2.56))
    fg.add(flag(fo, 0.62, 0.4, seed), k=0.0)
    fg.paint(Func(lambda P: (np.minimum(np.abs(P[:, 0] - F32(0.22 + 0.22)), np.abs(P[:, 2] - F32(2.56 - 0.2))) - F32(0.04)).astype(F32), fo - 1, fo + 1), 5)
    out.append(("Flag", fg, fine(0.004, 0.008), "flag_blue"))
    return out


def battery(seed=0):
    """A mortar battery: an epaulement of earth faced with gabions toward the fort (-Y), two mortars on their timber
    platforms behind it, shells heaped by them, powder kegs behind a traverse of sandbags, a rammer and a sponge."""
    rng = np.random.default_rng(seed)
    out = []
    ea, wk, ea2, sb, wd = Field("Earth"), Field("Wicker"), Field("Earth2"), Field("Sandbags"), Field("Timber")
    prof = [(0.7, -0.05), (0.7, 0.0), (0.2, 0.5), (-0.05, 0.52), (-0.32, 0.0), (-0.32, -0.05)]
    path = [v3((x, -0.65 + 0.14 * (x / 1.4) ** 2, 0.0)) for x in np.linspace(-1.45, 1.45, 7)]
    ea.add(bank(prof, path, seed=seed), k=0.0)
    ground_cut(ea)
    for k in range(6):
        x = -1.15 + k * 0.46
        gabion(wk, ea2, (x, -0.7 + 0.14 * (x / 1.4) ** 2, 0.48), 0.2, 0.4, seed + k, stakes=12)
    for sx in (-1, 1):                                              # the platforms and their mortars
        c = v3((sx * 0.62, 0.35, 0.0))
        for k in range(6):
            wd.add(RoundBox(c + v3((-0.32 + k * 0.128, 0, 0.03)), (0.06, 0.4, 0.03), 0.006), k=0.002, label=0)
        m = mortar(seed + 5 + sx)
        place_parts(out, [(n, f, vxs, mk) for (n, f, vxs, mk) in m if n != "Shells"], c + v3((0, 0, 0.06)), Rz(sx * 0.12))
    shells = Field("Shells")                                        # shells heaped between them
    for i, (x, y, z) in enumerate(((-0.08, 0.5, 0.09), (0.1, 0.5, 0.09), (0.0, 0.66, 0.09), (0.18, 0.66, 0.09), (-0.16, 0.66, 0.09), (0.01, 0.57, 0.24))):
        shells.add(Sphere((x, y, z), 0.09), k=0.0)
        shells.add(Cylinder((x, y, z + 0.09), 0.02, 0.04, rr=0.005), k=0.004, label=6)
    ground_cut(shells)
    out.append(("Shells", shells, fine(0.005, 0.01), "shot"))
    for layer in range(3):                                          # a sandbag traverse at its right end
        for i in range(4):
            sandbag(sb, v3((1.35 + (0.06 if layer % 2 else 0.0), 0.05 + i * 0.2, 0.05 + layer * 0.085)), math.pi / 2 + rng.uniform(-0.1, 0.1),
                    seed=seed + layer * 10 + i)
    kg = Field("Kegs")
    for (x, y, z) in ((1.6, 0.2, 0.15), (1.62, 0.5, 0.15), (1.61, 0.35, 0.43)):
        add_barrel(kg, (x, y, z), R=Rz(0.3) if z > 0.3 else None, hl=0.15, r_end=0.1, bulge=0.018, hoops=(0.8, 0.35))
    ground_cut(kg)
    a, b = v3((-1.2, 0.75, 0.03)), v3((0.2, 1.05, 0.03))
    wd.add(RoundCone(a, b, 0.016, 0.016), k=0.0, label=11)
    wd.add(Cylinder(b, 0.06, 0.12, rr=0.02, R=rot_from_axes(z_axis=unit(b - a))), k=0.01, label=9)
    ground_cut(wd)
    out += [("Wicker", wk, fine(0.005, 0.01), "wicker"), ("Earth2", ea2, fine(0.008, 0.016), "earthwork"), ("Earth", ea, fine(0.01, 0.02), "earthwork"),
            ("Sandbags", sb, fine(0.005, 0.01), "sandbag"), ("Platforms", wd, fine(0.005, 0.01), "timber"), ("Kegs", kg, fine(0.005, 0.01), "keg")]
    return out


def tower_mill(seed=0):
    """A tower windmill taken over as the besiegers' observation post: a tapering round tower of whitewashed stone (the
    render fallen away in patches), a door and small windows up it, a timber gallery round it with sandbags on it and a
    ladder up to it, a boarded cap turned to the wind, four lattice sails on the windshaft (one snapped and hanging),
    the besiegers' flag on the cap."""
    rng = np.random.default_rng(seed)
    out = []
    R0, R1, H = 0.62, 0.44, 2.35
    tw = Field("Tower")
    tw.add(cone((0, 0), -0.05, H, R0, R1, wob(5.0, 0.008, seed)), k=0.0)
    for z in (0.75, 1.55):
        rr = R0 + (R1 - R0) * (z / H)
        tw.add(Torus((0, 0, z), rr, 0.022), k=0.008, label=5)
    tw.sub(RoundBox((0, -R0, 0.35), (0.15, 0.12, 0.35), 0.015), k=0.004)                          # the door
    wins = [(-math.pi / 2 + 0.6, 1.15), (math.pi * 0.2, 0.9), (-math.pi / 2 - 0.4, 1.95), (math.pi * 0.75, 1.7)]
    for (a, z) in wins:
        rr = R0 + (R1 - R0) * (z / H)
        tw.sub(RoundBox((math.cos(a) * rr, math.sin(a) * rr, z), (0.07, 0.07, 0.1), 0.01, R=Rz(a)), k=0.003)
    tw.paint(Func(lambda P: (NOISE.fbm(P * F32(2.6) + F32(seed), 2) - F32(0.18)).astype(F32), (-1, -1, -0.1), (1, 1, H + 0.1)), 7)
    ground_cut(tw)
    out.append(("Tower", tw, fine(0.008, 0.016), "mill_render"))
    dk = Field("Dark")
    dk.add(RoundBox((0, -R0 + 0.08, 0.34), (0.13, 0.04, 0.33), 0.012), k=0.0)
    for (a, z) in wins:
        rr = R0 + (R1 - R0) * (z / H) - 0.06
        dk.add(RoundBox((math.cos(a) * rr, math.sin(a) * rr, z), (0.03, 0.06, 0.09), 0.008, R=Rz(a)), k=0.0)
    out.append(("Dark", dk, fine(0.006, 0.012), "dark"))
    wd = Field("Timber")
    zg = 1.3                                                        # the gallery round the tower
    rg = R0 + (R1 - R0) * (zg / H)
    wd.add(Func(lambda P: (np.maximum(np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(rg + 0.22)) - F32(0.24), np.abs(P[:, 2] - F32(zg)) - F32(0.025))
                           ).astype(F32), (-1.0, -1.0, zg - 0.1), (1.0, 1.0, zg + 0.1)), k=0.0, label=0)
    for k in range(12):
        a = 2 * math.pi * k / 12
        p = v3((math.cos(a) * (rg + 0.44), math.sin(a) * (rg + 0.44), 0))
        post(wd, p + v3((0, 0, zg)), p + v3((0, 0, zg + 0.36)), 0.016)
        wd.add(RoundCone(p + v3((0, 0, zg)), v3((math.cos(a) * rg, math.sin(a) * rg, zg - 0.38)), 0.018, 0.018), k=0.004, label=10)   # struts
    wd.add(Torus((0, 0, zg + 0.36), rg + 0.44, 0.018), k=0.004, label=10)
    for sx in (-1, 1):                                              # a ladder up to the gallery
        wd.add(RoundCone((0.55 + sx * 0.14, -1.25, -0.04), (0.42 + sx * 0.14, -0.9, zg + 0.05), 0.02, 0.018), k=0.0, label=11)
    for k in range(7):
        t = (k + 0.6) / 8
        p = v3((0.55 - 0.13 * t, -1.25 + 0.35 * t, -0.04 + (zg + 0.09) * t))
        wd.add(RoundCone(p + v3((-0.14, 0, 0)), p + v3((0.14, 0, 0)), 0.012, 0.012), k=0.0, label=10)
    ground_cut(wd)
    out.append(("Timber", wd, fine(0.005, 0.01), "timber"))
    sb = Field("Sandbags")
    for k in range(9):                                              # sandbags along the gallery's front
        a = -math.pi / 2 + (k - 4) * 0.2
        sandbag(sb, v3((math.cos(a) * (rg + 0.36), math.sin(a) * (rg + 0.36), zg + 0.07)), a + math.pi / 2, seed=seed + k)
        if k % 2 == 0:
            sandbag(sb, v3((math.cos(a + 0.1) * (rg + 0.36), math.sin(a + 0.1) * (rg + 0.36), zg + 0.155)), a + math.pi / 2, seed=seed + 20 + k)
    out.append(("Sandbags", sb, fine(0.005, 0.01), "sandbag"))
    cp = Field("Cap")                                               # the boarded cap
    cp.add(Ellipsoid((0, 0.05, H + 0.02), (R1 + 0.08, R1 + 0.16, 0.48)), k=0.0, label=11)
    cp.inter(Plane((0, 0, H - 0.04), (0, 0, -1)))
    cp.add(Cylinder((0, 0, H - 0.01), R1 + 0.1, 0.08, rr=0.02), k=0.01, label=10)
    cp.add(RoundCone((0, -R1 - 0.1, H + 0.15), (0, -R1 - 0.32, H + 0.2), 0.06, 0.06), k=0.01, label=10)   # the windshaft
    cp.add(RoundCone((0, R1 + 0.1, H + 0.05), (0, R1 + 1.0, 0.25), 0.03, 0.025), k=0.0, label=11)          # the tail pole
    post(cp, (0, 0.1, H + 0.45), (0, 0.1, H + 1.45), 0.022, 0.016)
    out.append(("Cap", cp, fine(0.006, 0.012), "boards"))
    sl = Field("Sails")
    hub = v3((0, -R1 - 0.34, H + 0.2))
    sl.add(Sphere(hub, 0.08), k=0.0, label=10)
    for k in range(4):
        ang = k * math.pi / 2 + 0.35
        d = v3((math.cos(ang), 0.0, math.sin(ang)))
        sd = v3((-math.sin(ang), 0.0, math.cos(ang)))
        if k == 2:                                                  # this one snapped: its stub, the rest hanging
            sl.add(RoundCone(hub + d * 0.08, hub + d * 0.42, 0.025, 0.02), k=0.004, label=10)
            tip = hub + d * 0.42
            hang_d = unit(v3((0.15, -0.1, -1.0)))
            sl.add(RoundCone(tip, tip + hang_d * 0.75, 0.018, 0.015), k=0.004, label=10)
            for i in range(5):
                q = tip + hang_d * (0.12 + 0.13 * i)
                sl.add(RoundCone(q, q + unit(np.cross(hang_d, v3((0, 1, 0)))) * 0.2, 0.007, 0.007), k=0.002, label=10)
            continue
        a0, a1 = hub + d * 0.08, hub + d * 1.25
        sl.add(RoundCone(a0, a1, 0.025, 0.018), k=0.004, label=10)
        for i in range(11):
            q = hub + d * (0.24 + 0.1 * i)
            sl.add(RoundCone(q, q + sd * 0.22, 0.008, 0.008), k=0.002, label=10)
        sl.add(RoundCone(hub + d * 0.22 + sd * 0.22, hub + d * 1.23 + sd * 0.22, 0.01, 0.01), k=0.002, label=10)
        if k != 1:
            sl.add(sailcloth(hub, d, sd), k=0.0, label=5)
    out.append(("Sails", sl, fine(0.004, 0.008), "sails"))
    fg = Field("Flag")
    fo = v3((0.02, 0.1, H + 1.42))
    fg.add(flag(fo, 0.55, 0.36, seed), k=0.0)
    fg.paint(Func(lambda P: (np.minimum(np.abs(P[:, 0] - F32(0.22)), np.abs(P[:, 2] - F32(H + 1.24))) - F32(0.035)).astype(F32), fo - 1, fo + 1), 5)
    out.append(("Flag", fg, fine(0.004, 0.008), "flag_blue"))
    return out


# ------------------------------------------------------------------------------------------------ the Gunpowder city
XC, XS, XP, XI, YB, YS1, YS2, YEND = 0.66, 0.0, -0.92, 2.3, 3.35, 2.5, 4.2, 7.15
HS, BAT, PW, PH = 1.45, 0.2, 0.5, 0.55          # the scarp's height and batter, the parapet's thickness and height


def _trace():
    """The plan of the wall's foot: the curtain with the gate (x = XC), a bastion each side (shoulders at x = XS, the
    salients at x = XP, y = +-YB), the curtain running on to y = +-YEND, the terreplein's inner face at x = XI."""
    half = [(XC, 0.0), (XC, YS1), (XS, YS1), (XP, YB), (XS, YS2), (XC, YS2), (XC, YEND), (XI, YEND)]
    other = [(x, -y) for (x, y) in reversed(half[1:])]
    return half + other


def _fade(y):
    """The curtain's height fading out toward its ends (as the Medieval wall's)."""
    return np.clip((F32(YEND - 0.15) - np.abs(y)) / F32(1.6), 0, 1) ** F32(0.6)


def _arch2(w, z, half, zc, zb=-0.1):
    """A round-headed opening in 2D (w across it, z up): jambs half apart, its arch springing at zc."""
    box = np.maximum(np.abs(w) - F32(half), np.maximum(F32(zb) - z, z - F32(zc)))
    rnd = np.sqrt(w * w + (z - F32(zc)) ** 2) - F32(half)
    return np.minimum(box, rnd)


def _garrison_gun(gn, ca, base, d):
    """A gun on a garrison carriage behind an embrasure: the iron barrel along d (its muzzle in the embrasure), a
    timber carriage on four trucks."""
    d = unit(v3((d[0], d[1], 0.0)))
    sd = v3((-d[1], d[0], 0.0))
    base = v3(base)
    R = np.stack([sd, d, v3((0, 0, 1))], axis=1)
    ca.add(RoundBox(base + v3((0, 0, 0.12)), (0.17, 0.27, 0.07), 0.015, R=R), k=0.0, label=10)
    for sx in (-1, 1):
        ca.add(RoundBox(base + sd * (sx * 0.12) + v3((0, 0, 0.21)) + d * 0.04, (0.03, 0.2, 0.08), 0.01, R=R), k=0.006, label=10)
        for sy in (-1, 1):
            c = base + sd * (sx * 0.2) + d * (sy * 0.16) + v3((0, 0, 0.075))
            ca.add(Cylinder(c, 0.075, 0.05, rr=0.012, R=rot_from_axes(z_axis=sd)), k=0.0, label=10)
    br = base + v3((0, 0, 0.3)) - d * 0.2
    cannon_barrel(gn, br, br + d * 0.95 + v3((0, 0, 0.03)), r0=0.085, r1=0.065, rm=0.075)


def _sentry_box(st, dm, c, out_dir):
    """An echauguette: a little round sentry box of stone corbelled out from the angle of a bastion at its cordon, slit
    windows, a stone dome with a ball finial."""
    c = v3(c)
    st.add(cone((c[0], c[1]), HS - 0.38, HS + 0.02, 0.02, 0.17), k=0.02)
    st.add(Cylinder(c + v3((0, 0, HS + 0.27)), 0.17, 0.52, rr=0.015), k=0.01)
    st.add(Torus(c + v3((0, 0, HS + 0.53)), 0.175, 0.018), k=0.004)
    for k in range(3):
        a = math.atan2(out_dir[1], out_dir[0]) + (k - 1) * 1.1
        st.sub(RoundBox(c + v3((math.cos(a) * 0.17, math.sin(a) * 0.17, HS + 0.3)), (0.02, 0.03, 0.08), 0.008, R=Rz(a)), k=0.003)
    dm.add(Ellipsoid(c + v3((0, 0, HS + 0.53)), (0.19, 0.19, 0.19)), k=0.0)
    dm.add(Sphere(c + v3((0, 0, HS + 0.75)), 0.04), k=0.02)
    dm.add(RoundCone(c + v3((0, 0, HS + 0.77)), c + v3((0, 0, HS + 0.86)), 0.016, 0.004), k=0.01)


def gunpowder_city(seed=0):
    """A star fort's gate at the end of the road (the road comes in from -X): the curtain of pale cut stone, its scarp
    sloping, a rounded cordon along its top, a thick parapet over it; a bastion either side, its faces meeting at a
    salient toward the road and its flanks turning back to the curtain, guns on garrison carriages in the embrasures of
    its parapet, a domed sentry box corbelled out at each of its angles, grass on its terreplein; in the middle the
    gateway: rusticated stone round a round arch between pilasters, a cornice and a pediment carved with the arms (a
    crimson shield with a gold saltire under a gold crown, gilded palms), the oak gates open; the drawbridge down over
    the dry ditch on its chains; iron braziers either side of it (game.gd lights them); the crimson-and-gold flag on its
    tall pole behind the gate; inside, the barracks under red tiles (a chimney smoking) and the church's white tower, its
    bell in the belfry under a tiled dome."""
    out = []
    poly = _trace()
    lo_xy, hi_xy = (XP - 0.4, -YEND - 0.3), (XI + 0.2, YEND + 0.3)
    # ---- the scarp: the whole trace, its faces battered; the cordon; the parapet
    sc = Field("Stone")

    def scarp(P):
        d2 = poly_sdf2(P[:, 0], P[:, 1], poly)
        top = F32(HS) * _fade(P[:, 1])
        return (np.maximum.reduce([d2 + F32(BAT) * np.clip(P[:, 2], 0, HS), P[:, 2] - top, -P[:, 2] - F32(0.06)]) * F32(0.94)).astype(F32)
    sc.add(Func(scarp, (lo_xy[0], lo_xy[1], -0.1), (hi_xy[0], hi_xy[1], HS + 0.05)), k=0.0)

    def cordon(P):
        d2 = poly_sdf2(P[:, 0], P[:, 1], poly) + F32(BAT * HS) - F32(0.025)
        zc = F32(HS - 0.03) * _fade(P[:, 1])
        dd = np.sqrt(d2 * d2 + (P[:, 2] - zc) ** 2) - F32(0.05)
        return np.maximum(dd, P[:, 0] - F32(XI - 0.45)).astype(F32)
    sc.add(Func(cordon, (lo_xy[0], lo_xy[1], -0.1), (hi_xy[0], hi_xy[1], HS + 0.08)), k=0.006)

    def parapet(P):
        d2 = poly_sdf2(P[:, 0], P[:, 1], poly) + F32(BAT * HS)
        fd = _fade(P[:, 1])
        base = F32(HS) * fd
        zt = base + (F32(PH) - F32(0.12) * np.clip(-d2 / F32(PW), 0, 1)) * fd        # its top sloping down inward
        band = np.maximum(d2, -d2 - F32(PW))
        return (np.maximum.reduce([band, P[:, 2] - zt, base - F32(0.05) - P[:, 2], P[:, 0] - F32(XI - 0.55)]) * F32(0.9)).astype(F32)
    sc.add(Func(parapet, (lo_xy[0], lo_xy[1], -0.1), (hi_xy[0], hi_xy[1], HS + PH + 0.05)), k=0.01)
    # embrasures in the bastions' faces and flanks, a gun behind each
    guns = []
    for sy in (-1, 1):
        S1, Pt, S2 = v3((XS, sy * YS1, 0)), v3((XP, sy * YB, 0)), v3((XS, sy * YS2, 0))
        A, B = v3((XC, sy * YS1, 0)), v3((XC, sy * YS2, 0))
        inner = v3((1.2, sy * YB, 0.0))
        for (p, q) in ((S1, Pt), (Pt, S2), (A, S1), (S2, B)):
            m = (p + q) / 2
            t = unit(q - p)
            nrm = v3((t[1], -t[0], 0.0))
            if np.dot(nrm, m - inner) < 0:
                nrm = -nrm
            side = v3((-nrm[1], nrm[0], 0.0))
            mt = m - nrm * (BAT * HS)
            guns.append((mt, nrm))
            ci = mt - nrm * PW
            sc.sub(convex([(mt + v3((0, 0, HS + 0.17)), (0, 0, -1)), (ci + side * 0.08, side - nrm * 0.45), (ci - side * 0.08, -side - nrm * 0.45)],
                          mt + v3((-0.9, -0.9, HS + 0.1)), mt + v3((0.9, 0.9, HS + PH + 0.2))), k=0.02)
    # the counterscarp's kerb across the front of the curtain (the drawbridge rests on it)
    sc.add(RoundBox((-0.72, 0.0, 0.05), (0.09, YS1 - 0.3, 0.07), 0.025, **wob(6.0, 0.006, seed)), k=0.0)
    # ---- the gateway
    gx0, gx1, gw, gz = 0.42, 1.05, 0.88, 2.12
    sc.add(RoundBox(((gx0 + gx1) / 2, 0, gz / 2), ((gx1 - gx0) / 2, gw, gz / 2), 0.012), k=0.004)
    for z in np.arange(0.2, 1.85, 0.2):                             # rustication: deep joints between its courses
        sc.sub(RoundBox((gx0, 0, z), (0.018, gw - 0.04, 0.012), 0.004), k=0.002)
    for y in (-0.72, 0.72):                                         # pilasters, their bases and capitals
        sc.add(RoundBox((gx0 - 0.03, y, 0.95), (0.04, 0.09, 0.92), 0.008), k=0.003)
        sc.add(RoundBox((gx0 - 0.04, y, 0.06), (0.05, 0.11, 0.06), 0.008), k=0.003)
        sc.add(RoundBox((gx0 - 0.045, y, 1.84), (0.055, 0.115, 0.04), 0.008), k=0.003)
    sc.add(RoundBox((gx0 - 0.02, 0, 1.97), (0.06, gw + 0.06, 0.055), 0.012), k=0.004)               # the cornice
    sc.add(convex([((gx0 - 0.04, 0, 2.62), (0, 1.0, 1.45)), ((gx0 - 0.04, 0, 2.62), (0, -1.0, 1.45)), ((gx0 - 0.07, 0, 0), (-1, 0, 0)),
                   ((gx0 + 0.25, 0, 0), (1, 0, 0)), ((gx0, 0, 2.02), (0, 0, -1))], (gx0 - 0.15, -gw - 0.2, 1.95), (gx0 + 0.3, gw + 0.2, 2.75)),
           k=0.004)                                                 # the pediment
    sc.sub(convex([((gx0 - 0.04, 0, 2.56), (0, 1.0, 1.45)), ((gx0 - 0.04, 0, 2.56), (0, -1.0, 1.45)), ((gx0 - 0.075, 0, 0), (-1, 0, 0)),
                   ((gx0 - 0.02, 0, 0), (1, 0, 0)), ((gx0, 0, 2.1), (0, 0, -1))], (gx0 - 0.15, -gw, 2.0), (gx0 + 0.1, gw, 2.7)), k=0.004)
    sh_c = v3((gx0 - 0.05, 0, 2.27))                                # the arms in the tympanum: the shield
    sc.add(RoundBox(sh_c, (0.03, 0.11, 0.08), 0.02), k=0.004)
    sc.add(RoundCone(sh_c + v3((0, 0, -0.06)), sh_c + v3((0, 0, -0.15)), 0.08, 0.012), k=0.02)
    cr = sh_c + v3((-0.01, 0, 0.13))                                # the crown over it
    sc.add(RoundBox(cr, (0.025, 0.09, 0.02), 0.008), k=0.004)
    for k in range(5):
        y = -0.08 + k * 0.04
        sc.add(RoundCone(cr + v3((0, y, 0.01)), cr + v3((-0.005, y, 0.06 if k % 2 == 0 else 0.045)), 0.012, 0.006), k=0.004)
        sc.add(Sphere(cr + v3((-0.005, y, 0.065 if k % 2 == 0 else 0.05)), 0.012), k=0.003)
    for sg in (-1, 1):                                              # gilded palms either side
        for k in range(4):
            sc.add(Ellipsoid(sh_c + v3((-0.01, sg * (0.16 + 0.05 * k), -0.08 + 0.06 * k)), (0.012, 0.05, 0.018), R=euler(sg * (0.5 + 0.3 * k), 0, 0)),
                   k=0.004)
    sc.paint(Func(lambda P: (P[:, 2] - F32(0.32)).astype(F32), (lo_xy[0], lo_xy[1], -0.2), (hi_xy[0], hi_xy[1], 3)), 7)     # grime at the foot
    sc.paint(Func(lambda P: (np.maximum(np.abs(P[:, 1]) - F32(0.12), np.abs(P[:, 2] - F32(2.2)) - F32(0.16))).astype(F32),
                  sh_c - 0.4, sh_c + 0.4), 5)                       # the shield crimson...
    for sg in (-1, 1):                                              # ...with the gold saltire
        R = rot_from_axes(x_axis=(0, math.cos(sg * 0.85), math.sin(sg * 0.85)), y_axis=(1, 0, 0))
        sc.paint(RoundBox(sh_c + v3((-0.04, 0, -0.03)), (0.16, 0.06, 0.022), 0.0, R=R), 6)
    sc.paint(Func(lambda P: (np.maximum(np.abs(P[:, 1]) - F32(0.11), np.abs(P[:, 2] - F32(cr[2] + 0.03)) - F32(0.06))).astype(F32), cr - 0.3, cr + 0.3), 6)
    for sg in (-1, 1):
        sc.paint(Func(lambda P, sg=sg: (np.maximum(np.abs(P[:, 1] - F32(sg * 0.24)) - F32(0.11), np.abs(P[:, 2] - F32(2.3)) - F32(0.15))).astype(F32),
                      sh_c - 0.5, sh_c + 0.5), 6)
    # the arch and the passage behind it, the voussoirs, the keystone
    sc.sub(Func(lambda P: np.maximum(_arch2(P[:, 1], P[:, 2], 0.42, 0.98), np.maximum(F32(gx0 - 0.2) - P[:, 0], P[:, 0] - F32(XI + 0.2))).astype(F32),
                (gx0 - 0.25, -0.6, -0.2), (XI + 0.25, 0.6, 1.5)), k=0.01)
    for k in range(9):
        a = math.pi * (k + 0.5) / 9
        d = v3((0, math.cos(a), math.sin(a)))
        c = v3((gx0, 0, 0.98)) + d * 0.52
        sc.sub(RoundBox(c, (0.02, 0.008, 0.11), 0.003, R=rot_from_axes(x_axis=(1, 0, 0), z_axis=d)), k=0.002)
    sc.add(RoundBox((gx0 - 0.02, 0, 1.52), (0.045, 0.07, 0.09), 0.01), k=0.004)
    ground_cut(sc, -0.04)
    out.append(("Stone", sc, fine(0.012, 0.024), "fort_stone"))
    # ---- grass on the terreplein, behind the parapets
    tf = Field("Turf")

    def turf(P):
        d2 = poly_sdf2(P[:, 0], P[:, 1], poly) + F32(BAT * HS)
        top = F32(HS) * _fade(P[:, 1])
        return (np.maximum.reduce([d2 + F32(PW - 0.02), np.abs(P[:, 2] - top - F32(0.015)) - F32(0.025), F32(0.05) - top]) * F32(0.9)).astype(F32)
    tf.add(Func(turf, (lo_xy[0], lo_xy[1], -0.05), (hi_xy[0], hi_xy[1], HS + 0.1)), k=0.0)
    out.append(("Turf", tf, fine(0.014, 0.028), "fort_turf"))
    # ---- sentry boxes at the bastions' angles
    sbx, dm = Field("Boxes"), Field("Domes")
    for sy in (-1, 1):
        for (p, o) in (((XP - 0.02, sy * YB), (-1.0, 0.0)), ((XS - 0.06, sy * (YS1 - 0.06)), (-0.7, -sy * 0.7)),
                       ((XS - 0.06, sy * (YS2 + 0.06)), (-0.7, sy * 0.7))):
            c = v3((p[0] + BAT * HS + o[0] * 0.05, p[1] + o[1] * 0.05, 0.0))
            _sentry_box(sbx, dm, c, o)
    out.append(("Boxes", sbx, fine(0.006, 0.012), "fort_stone"))
    out.append(("Domes", dm, fine(0.006, 0.012), "fort_stone"))
    # ---- the guns in the embrasures
    gn, ca = Field("Guns"), Field("Carriages")
    for (mt, nrm) in guns:
        _garrison_gun(gn, ca, mt - nrm * (PW + 0.35) + v3((0, 0, HS)), nrm)
    out.append(("Guns", gn, fine(0.005, 0.01), "gun_iron"))
    out.append(("Carriages", ca, fine(0.005, 0.01), "timber"))
    # ---- the gates (open, swung in against the passage), the drawbridge and its chains
    gd = Field("Gates")
    for sy in (-1, 1):
        gd.add(RoundBox((gx1 + 0.2, sy * 0.38, 0.62), (0.21, 0.03, 0.6), 0.008, R=Rz(sy * 0.12)), k=0.0, label=11)
        for z in (0.25, 0.65, 1.05):
            gd.add(RoundBox((gx1 + 0.2, sy * 0.345, z), (0.21, 0.008, 0.02), 0.004, R=Rz(sy * 0.12)), k=0.002, label=6)
    for k in range(10):
        gd.add(RoundBox((-0.78 + k * 0.125, 0, 0.075), (0.058, 0.48, 0.03), 0.006), k=0.002, label=0)
    for sy in (-1, 1):
        gd.add(RoundBox((-0.18, sy * 0.46, 0.04), (0.64, 0.035, 0.035), 0.008), k=0.003, label=10)
        gd.add(RoundCone((-0.76, sy * 0.47, 0.12), (gx0 - 0.08, sy * 0.52, 1.66), 0.014, 0.014), k=0.004, label=6)
        gd.add(Torus((gx0 - 0.08, sy * 0.52, 1.66), 0.035, 0.01, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.004, label=6)
    ground_cut(gd, -0.04)
    out.append(("Gates", gd, fine(0.006, 0.012), "timber"))
    dk = Field("Dark")                                              # the passage's shadow
    dk.add(RoundBox((XI - 0.2, 0, 0.6), (0.05, 0.45, 0.65), 0.0), k=0.0)
    out.append(("Dark", dk, fine(0.008, 0.016), "dark"))
    # ---- braziers by the gate
    fb, cg = Field("Braziers"), Field("Coals")
    for (fx, fy, fz) in CITY_FIRES:
        c = v3((fx, fy, 0.0))
        fb.add(RoundBox(c + v3((0, 0, 0.12)), (0.14, 0.14, 0.12), 0.02), k=0.0, label=7)
        for k in range(3):
            a = 2 * math.pi * k / 3 + 0.5
            fb.add(RoundCone(c + v3((math.cos(a) * 0.1, math.sin(a) * 0.1, 0.24)), c + v3((0, 0, 0.95)), 0.016, 0.014), k=0.006)
        fb.add(Ellipsoid(c + v3((0, 0, 1.0)), (0.2, 0.2, 0.1)), k=0.02)
        fb.sub(Ellipsoid(c + v3((0, 0, 1.08)), (0.17, 0.17, 0.08)), k=0.01)
        for k in range(6):
            a = 2 * math.pi * k / 6
            fb.add(RoundCone(c + v3((math.cos(a) * 0.18, math.sin(a) * 0.18, 1.04)), c + v3((math.cos(a) * 0.23, math.sin(a) * 0.23, 1.13)), 0.012, 0.008),
                   k=0.004)
        cg.add(Ellipsoid(c + v3((0, 0, 1.07)), (0.15, 0.15, 0.06), **wob(25.0, 0.008, seed + int(fy * 10))), k=0.0)
    ground_cut(fb)
    out.append(("Braziers", fb, fine(0.005, 0.01), "brazier"))
    out.append(("Coals", cg, fine(0.005, 0.01), "glow_fire"))
    # ---- the flag on its tall pole behind the gate
    pl = Field("Pole")
    pc = v3((1.75, 1.2, HS))
    post(pl, pc, pc + v3((0, 0, 3.1)), 0.035, 0.025)
    pl.add(RoundCone(pc + v3((0, 0, 3.1)), pc + v3((0, 0, 3.22)), 0.03, 0.005), k=0.01, label=6)
    pl.add(RoundBox(pc + v3((0, 0, 0.12)), (0.12, 0.12, 0.12), 0.02), k=0.02, label=10)
    out.append(("Pole", pl, fine(0.005, 0.01), "timber"))
    fg = Field("Flag")
    fo = pc + v3((0, 0.03, 3.04))
    fg.add(flag(fo, 0.95, 0.62, seed, along=(0, 1, 0), wave=0.05), k=0.0)
    flag_paint(fg, fo, 0.95, 0.62, d=(0, 1, 0), saltire=0.085, border=0.05)
    out.append(("Flag", fg, fine(0.005, 0.01), "flag"))
    # ---- inside: the barracks (a chimney smoking) and the church
    for i, (c, hx, hy, yaw) in enumerate((((3.15, -2.45), 1.05, 0.48, math.pi / 2), ((3.15, 2.45), 1.05, 0.48, -math.pi / 2),
                                          ((3.9, -4.85), 0.75, 0.42, 0.25), ((3.85, 4.9), 0.7, 0.42, -0.2))):
        town_house(out, "House%d" % i, c, hx, hy, 0.95, yaw, seed + 60 + i)
    chm = Field("Chimney")
    cx0, cy0 = CITY_SMOKE[0], CITY_SMOKE[1]
    chm.add(walls_box(cx0, cy0, 0.11, 0.11, 0.9, 2.05, batter=0.02, amp=0.006, seed=seed + 7), k=0.0)
    chm.add(RoundBox((cx0, cy0, 2.03), (0.14, 0.14, 0.035), 0.01), k=0.006)
    chm.sub(Cylinder((cx0, cy0, 2.08), 0.06, 0.1), k=0.004)
    out.append(("Chimney", chm, fine(0.007, 0.014), "fort_stone"))
    ch = Field("Church")
    cx, cy = 3.85, -0.35
    ch.add(walls_box(cx + 0.65, cy, 0.62, 0.42, -0.05, 1.15, batter=0.01, amp=0.005, seed=seed + 8), k=0.0)        # the nave
    ch.add(walls_box(cx - 0.12, cy, 0.3, 0.3, -0.05, 3.05, batter=0.008, amp=0.004, seed=seed + 9), k=0.0)          # the tower
    for z in (1.15, 2.2):
        ch.add(RoundBox((cx - 0.12, cy, z), (0.33, 0.33, 0.035), 0.01), k=0.004, label=5)
    ch.add(RoundBox((cx - 0.12, cy, 3.08), (0.35, 0.35, 0.05), 0.012), k=0.004, label=5)
    for sx in (-1, 1):                                              # quoins up its corners
        for sy in (-1, 1):
            for k in range(8):
                z = 0.15 + k * 0.36
                ch.add(RoundBox((cx - 0.12 + sx * 0.295, cy + sy * 0.295, z), (0.03, 0.03, 0.08), 0.006), k=0.002, label=5)
    bc = v3((cx - 0.12, cy, 2.62))
    for ax in (0, 1):                                               # the belfry: an arch through it each way
        ch.sub(Func(lambda P, ax=ax: np.maximum(_arch2(P[:, 1 - ax] - F32(bc[1 - ax]), P[:, 2], 0.12, bc[2], bc[2] - 0.32),
                                                np.abs(P[:, ax] - F32(bc[ax])) - F32(0.4)).astype(F32), bc - 0.5, bc + 0.5), k=0.006)
    ch.sub(RoundBox((cx - 0.42, cy, 0.38), (0.06, 0.13, 0.38), 0.01), k=0.004)                      # its door
    ch.paint(Func(lambda P: (F32(0.12) - P[:, 2]).astype(F32), (cx - 1, cy - 1, -0.2), (cx + 2, cy + 1, 0.4)), 7)
    ground_cut(ch)
    out.append(("Church", ch, fine(0.008, 0.016), "fort_plaster"))
    rf = Field("ChurchRoof")
    rf.add(gable((cx + 0.65, cy), 0.68, 0.48, 1.12, 1.6, axis="x"), k=0.0)
    rf.ops[-1][1].disp = lambda P: (F32(0.012) * np.abs(np.sin(P[:, 0] * F32(36)))).astype(F32)
    rf.ops[-1][1].disp_amp = 0.014
    rf.add(Ellipsoid((cx - 0.12, cy, 3.12), (0.27, 0.27, 0.34)), k=0.0)                              # the dome
    rf.inter(Plane((0, 0, 1.1), (0, 0, -1)))
    out.append(("ChurchRoof", rf, fine(0.007, 0.014), "tiles"))
    cr2 = Field("Cross")
    cr2.add(RoundCone((cx - 0.12, cy, 3.42), (cx - 0.12, cy, 3.62), 0.04, 0.03), k=0.0)
    cr2.add(Sphere((cx - 0.12, cy, 3.64), 0.04), k=0.01)
    cr2.add(RoundCone((cx - 0.12, cy, 3.66), (cx - 0.12, cy, 3.92), 0.014, 0.014), k=0.004)
    cr2.add(RoundCone((cx - 0.12, cy - 0.08, 3.84), (cx - 0.12, cy + 0.08, 3.84), 0.013, 0.013), k=0.004)
    out.append(("Cross", cr2, fine(0.005, 0.01), "brass"))
    bl = Field("Bell")
    bl.add(RoundCone(bc + v3((0, 0, 0.08)), bc + v3((0, 0, -0.1)), 0.05, 0.1), k=0.0)
    bl.add(Torus(bc + v3((0, 0, -0.1)), 0.095, 0.014), k=0.006)
    bl.add(RoundCone(bc + v3((0, -0.25, 0.14)), bc + v3((0, 0.25, 0.14)), 0.014, 0.014), k=0.004)
    out.append(("Bell", bl, fine(0.004, 0.008), "bronze"))
    dk2 = Field("Dark2")
    dk2.add(RoundBox((cx - 0.12, cy, 2.6), (0.24, 0.24, 0.2), 0.02), k=0.0)
    dk2.add(RoundBox((cx - 0.38, cy, 0.38), (0.03, 0.12, 0.37), 0.008), k=0.0)
    out.append(("Dark2", dk2, fine(0.008, 0.016), "dark"))
    return out


CITY_FIRES = [(0.18, -1.18, 1.1), (0.18, 1.18, 1.1)]   # where the braziers' fires burn (Blender: x, y, z; game.gd: x, z, -y)
CITY_SMOKE = (3.45, 3.05, 2.1)                          # the barracks chimney's top


# ------------------------------------------------------------------------------------------------ the kits
# prop name -> (builder, game-mesh triangle budget), as decor_props.KITS. Tuft and Flowers are direct geometry
# (decor_build).
def KITS(theme):
    if theme == "jungle":
        return {
            "Tree_A": (lambda: jungle_tree(3.8, 401, crown_w=1.25, dome=0.35, vines=9), 2400),
            "Tree_B": (lambda: jungle_tree(3.2, 402, crown_w=1.05, dome=0.55, vines=7, lean=0.07), 2200),
            "Tree_C": (lambda: jungle_tree(2.4, 403, crown_w=0.9, dome=0.4, vines=6, lean=0.1), 1600),
            "Palm_A": (lambda: coconut_palm(3.2, 404, lean=0.42), 1800), "Palm_B": (lambda: coconut_palm(2.6, 405, lean=0.3, n_fronds=12), 1600),
            "Banana": (lambda: banana(406), 1200), "Fern": (lambda: tree_fern(1.0, 407), 1100), "Fern_B": (lambda: fern(408, 1.55), 800),
            "Monstera": (lambda: big_leaves(409), 1000), "Heliconia": (lambda: heliconia(410), 900), "Bromeliad": (lambda: bromeliad(411), 700),
            "Rock_A": (lambda: rock(1.6, 0.55, 412, n_extra=2), 650), "Rock_B": (lambda: rock(1.0, 0.38, 413, n_extra=1), 420),
            "Log": (lambda: jungle_log(414), 750), "Stump": (lambda: jungle_stump(415), 450),
            "Pyramid": (lambda: maya_pyramid(416), 6000), "Stela": (lambda: stela(417), 800), "Stela_B": (lambda: stela(418, broken=True), 700),
            "Blocks": (lambda: ruin_blocks(419), 1000), "Watchtower": (lambda: watchtower(420), 3400), "Hut": (lambda: stilt_hut(421), 3000),
            "Canoe": (lambda: dugout(422), 700),
        }
    if theme == "harbor":
        return {
            "Palm_A": (lambda: coconut_palm(3.2, 431, lean=0.48), 1800), "Palm_B": (lambda: coconut_palm(2.5, 432, lean=0.3, n_fronds=12), 1600),
            "SeaGrape": (lambda: sea_grape(1.1, 0.72, 433), 900), "Scrub": (lambda: cbush(0.85, 0.5, 434, "scrub", "flower_yellow"), 700),
            "Rock_A": (lambda: limestone(1.5, 0.5, 435), 650), "Rock_B": (lambda: limestone(0.95, 0.32, 436, 1), 420),
            "Rock_C": (lambda: limestone(2.1, 0.62, 437, 3), 850), "Driftwood": (lambda: driftwood(438), 600),
            "Crates": (lambda: crates(439), 1300), "Barrels": (lambda: barrels(440), 1200), "Bales": (lambda: bales(441), 1000),
            "Rope": (lambda: rope_coil(442), 500), "Anchor": (lambda: anchor(443), 700), "Rowboat": (lambda: rowboat(444), 1400),
            "Nets": (lambda: nets(445), 1200), "Treasure": (lambda: treasure(446), 1400),
            "Ship": (lambda: brigantine(447), 7000), "Jetty": (lambda: jetty(448), 2200), "Tavern": (lambda: tavern(449), 4800),
            "Lookout": (lambda: lookout(450), 2200),
        }
    if theme == "fortress":
        return {
            "Oak_A": (lambda: oak(2.4, 461), 2200), "Oak_B": (lambda: oak(1.6, 462, young=True), 1400),
            "Cypress": (lambda: cypress(2.9, 463), 1000), "Bush": (lambda: cbush(0.8, 0.5, 464, "bush"), 700),
            "Rock_A": (lambda: rock(1.6, 0.48, 465), 650), "Rock_B": (lambda: rock(1.0, 0.34, 466, n_extra=1), 420),
            "Gabions": (lambda: gabions(467), 1400), "Fascines": (lambda: fascines(468), 900), "Rampart": (lambda: rampart(469), 1600),
            "Trench": (lambda: trench(470), 1400), "Gun": (lambda: field_gun(471), 1800), "Mortar": (lambda: mortar(472), 1000),
            "Shot": (lambda: shot_pyramid(473), 700), "Powder": (lambda: powder_kegs(474), 1000), "Tent": (lambda: bell_tent(475), 1000),
            "Marquee": (lambda: marquee(476), 2400), "Wagon": (lambda: supply_wagon(477), 2200), "Wheels": (lambda: broken_wheels(478), 600),
            "Redoubt": (lambda: redoubt(479), 4500), "Battery": (lambda: battery(480), 3000), "Windmill": (lambda: tower_mill(481), 4000),
        }
    if theme == "fort_city":
        return {"City": (lambda: gunpowder_city(491), 18000)}
    raise KeyError(theme)
