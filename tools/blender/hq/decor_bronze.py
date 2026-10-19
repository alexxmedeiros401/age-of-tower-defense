"""HQ Bronze Age map props (v0.9.28), sculpted as distance fields like decor_props (same conventions: every builder
returns its parts [(part name, Field, voxel, material key)], built at the origin, Z up, ground at z = 0; KITS lists each
theme's props and their game-mesh triangle budgets; decor_build.materials resolves the material keys).

River Delta: date palms, papyrus, cattail reeds, bushes; a farmhouse, a granary, a shaduf and a reed boat.
Desert Citadel: palms, acacias, scrub, sand drifts, sandstone rocks, broken columns, fallen blocks; a ruined colonnade,
an obelisk and the step pyramid on the horizon.
Copper Canyon: mesas, hoodoos, red rocks, scrub, dead trees, malachite, mine carts, timber stacks; the mine and a
copper smelter.
The Bronze city at the end of every Bronze Age road is its own kit ("city", bronze_city.glb).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Chain, Plane, Func, rot_from_axes, v3, NOISE
import decor_props as DP
from decor_props import vx, wob, convex, crystal, rock, bush, dead_tree

F32 = np.float32


def fine(a, b):
    return a if DP.FINE[0] else b


def unit(v):
    v = v3(v)
    return v / max(float(np.linalg.norm(v)), 1e-9)


def frame(t):
    """Tangent t, a horizontal side vector b and n = t x b (the 'up' side of something lying along t)."""
    t = unit(t)
    b = np.cross(v3((0, 0, 1)), t)
    if np.linalg.norm(b) < 1e-6:
        b = v3((0, 1, 0))
    b = unit(b)
    return t, b, unit(np.cross(t, b))


def box_bounds(pts, pad):
    P = np.array(pts)
    return P.min(0) - pad, P.max(0) + pad


def ground_cut(f, z=-0.03):
    f.inter(Plane((0, 0, z), (0, 0, -1)))
    return f


def cut_above(f, c, nrm, half, disp=None, amp=0.0):
    """Remove what lies above the plane through c (normal nrm), only inside a box of half extents `half` round c: a
    bounded cut (an `inter` would cut every other shape merged into the same field)."""
    cf, nf, hf = v3(c).astype(F32), unit(nrm).astype(F32), v3(half).astype(F32)

    def fn(P):
        Q = P - cf
        dp = Q @ nf
        if disp is not None:
            dp = dp + disp(P)
        return np.maximum(-dp, np.max(np.abs(Q) - hf, axis=1)).astype(F32)
    f.sub(Func(fn, v3(c) - v3(half) - amp, v3(c) + v3(half) + amp))
    return f


def cut_below(f, z, cx, cy, hx, hy):
    """A bounded ground cut: remove what lies below z inside the box round (cx, cy)."""
    f.sub(RoundBox((cx, cy, z - 1.0), (hx, hy, 1.0), 0.0))
    return f


# ------------------------------------------------------------------------------------------------ date palm
def _wprof(s, W0):
    a = np.clip((s - 0.1) / 0.22, 0, 1)
    a = a * a * (3 - 2 * a)
    return W0 * a * np.clip(1 - s ** 2.2, 0, 1) ** 0.7


def _half_blade(p0, t, q, L, s0, s1, Lf, W0, teeth, th, sp=0.085, groove=0.008, depth=0.5):
    """One straight piece of a frond's half-blade: from p0 along t (length L), reaching out along q from the rib to a
    serrated edge (the frond's width profile at s0..s1, `teeth` leaflet tips along the frond), `th` thick, with grooves
    between the leaflets in both faces from the rib out to the edge, leaning toward the tip. (Grooves, not slits cut
    through: slits made a comb of up to a hundred loose bits per palm that the decimator could not bring under 5k
    triangles; grooves keep each frond one closed piece and still bake as the lines between the leaflets.)"""
    m = unit(np.cross(t, q))
    p0f, tf, qf, mf = (x.astype(F32) for x in (p0, t, q, m))

    def fn(P):
        Q = P - p0f
        x, y, z = Q @ tf, Q @ qf, Q @ mf
        s = s0 + np.clip(x / L, 0, 1) * (s1 - s0)
        saw = 1.0 - ((s * teeth) % 1.0)
        W = _wprof(s, W0) * (0.72 + 0.28 * saw)
        d = np.maximum(np.maximum(np.maximum(-x - 0.012, x - L - 0.012), np.maximum(-y - 0.008, y - W)), np.abs(z) - th)
        g = ((s * Lf - y * 0.8) / sp) % 1.0
        dg = np.maximum(np.maximum(np.abs(g - 0.5) * sp - groove, 0.12 * W - y), th * (1.0 - depth) - np.abs(z))
        return np.maximum(d, -dg).astype(F32)
    Wm = W0 * 1.02
    lo, hi = box_bounds([p0 + t * a + q * b + m * c for a in (-0.02, L + 0.02) for b in (-0.02, Wm) for c in (-th - 0.01, th + 0.01)], 0.01)
    return Func(fn, lo, hi)


FOLD = 0.4


def frond(blades, ribs, base, az, el, L, droop, W0, th, teeth=8, K=9):
    d0 = v3((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    S = [i / K for i in range(K + 1)]
    pts = [base + d0 * (L * s) + v3((0, 0, -droop * L * s * s)) for s in S]
    ribs.add(Chain(pts, [0.028 - 0.022 * s for s in S], k=0.01))
    Lf = sum(float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(K))
    for i in range(K):
        if S[i + 1] <= 0.12:                            # the bare stalk
            continue
        p0, p1 = pts[i], pts[i + 1]
        t, b, n = frame(p1 - p0)
        Ls = float(np.linalg.norm(p1 - p0))
        for side in (-1, 1):
            q = unit(b * (side * math.cos(FOLD)) + n * math.sin(FOLD))
            blades.add(_half_blade(p0, t, q, Ls, S[i], S[i + 1], Lf, W0, teeth, th))
    return pts


def palm(h=3.0, lean=0.3, seed=0, n_fronds=11, dates=True, young=False):
    """A date palm: a gently leaning trunk of criss-crossed leaf-base scales flaring at the foot, a crown of arching
    pinnate fronds (serrated, slit between the leaflets, folded up off the rib), bunches of dates under the crown."""
    rng = np.random.default_rng(seed)
    out = []
    a0 = rng.uniform(0, 2 * math.pi)
    lx, ly = math.cos(a0) * lean, math.sin(a0) * lean

    def C(t):
        return v3((lx * h * t ** 1.7, ly * h * t ** 1.7, h * t))
    N = 10
    pts = [C(i / (N - 1)) for i in range(N)]
    pts[0] = pts[0] + v3((0, 0, -0.12))
    r0 = 0.15 if not young else 0.17
    radii = [r0 + 0.05 if i == 0 else r0 - 0.035 * (i / (N - 1)) for i in range(N)]
    ring = 0.085 if not young else 0.075

    def scars(P):
        z = np.clip(P[:, 2], 0, h)
        u = (z / h) ** 1.7
        ang = np.arctan2(P[:, 1] - ly * h * u, P[:, 0] - lx * h * u)
        w = ang / (2 * math.pi) * 3.0
        s = np.minimum((z / ring + w) % 1.0, (z / ring - w) % 1.0)
        return (s - 0.5) * 0.022 * np.clip(z / 0.25, 0, 1) + NOISE.fbm(P * 7.0 + seed, 2) * 0.006
    f = Field("Trunk")
    f.add(Chain(pts, radii, k=0.05, disp=scars, disp_amp=0.02))
    f.add(Ellipsoid((0, 0, -0.04), (r0 + 0.12, r0 + 0.12, 0.22), **wob(6.0, 0.012, seed)), k=0.12)     # the flared foot
    for i in range(6):                                  # a mat of short roots round it
        a = 2 * math.pi * i / 6 + rng.uniform(-0.3, 0.3)
        f.add(Ellipsoid(((r0 + 0.1) * math.cos(a), (r0 + 0.1) * math.sin(a), 0.0), (0.09, 0.06, 0.05),
                        R=rot_from_axes(x_axis=(math.cos(a), math.sin(a), 0))), k=0.05)
    T = C(1.0)
    f.add(Ellipsoid(T + v3((0, 0, 0.02)), (0.12, 0.12, 0.17)), k=0.06)          # the heart of the crown
    for i in range(9):                                  # stubs of old fronds round the top of the trunk
        a = 2 * math.pi * i / 9 + rng.uniform(-0.2, 0.2)
        b0 = T + v3((0.05 * math.cos(a), 0.05 * math.sin(a), -0.16 - 0.06 * (i % 2)))
        f.add(RoundCone(b0, b0 + v3((0.2 * math.cos(a), 0.2 * math.sin(a), -0.1)), 0.045, 0.018), k=0.02)
    ground_cut(f, -0.04)
    out.append(("Trunk", f, fine(0.008, 0.016), "palm_bark"))

    blades, ribs = Field("Fronds"), Field("Ribs")
    s = h / 3.0
    th = max(0.011, fine(0.0058, 0.011) * 1.0)
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n_fronds):
        u = i / max(n_fronds - 1, 1)                    # 0: the top fronds (rising), 1: the lowest (drooping)
        az = a0 + i * golden + rng.uniform(-0.15, 0.15)
        el = math.radians((64 - 92 * u) if not young else (72 - 70 * u)) + rng.uniform(-0.08, 0.08)
        L = (1.0 + 0.45 * math.sin(u * math.pi * 0.85)) * s * rng.uniform(0.92, 1.06) * (0.85 if young else 1.0)
        droop = (0.32 + 0.62 * u) * rng.uniform(0.85, 1.15)
        base = T + v3((0.05 * math.cos(az), 0.05 * math.sin(az), 0.05 - 0.1 * u))
        frond(blades, ribs, base, az, el, L, droop, 0.25 * s, th)
    out.append(("Fronds", blades, fine(0.0058, 0.011), "frond"))
    out.append(("Ribs", ribs, fine(0.006, 0.012), "frond_rib"))
    if dates:                                           # heavy bunches hanging under the crown on orange stalks
        d = Field("Dates")
        for k in range(3):
            a = a0 + 0.9 + k * 2.1 + rng.uniform(-0.3, 0.3)
            hz = v3((math.cos(a), math.sin(a), 0))
            st = [T + hz * 0.08 + v3((0, 0, -0.08)), T + hz * 0.24 + v3((0, 0, -0.14)), T + hz * 0.3 + v3((0, 0, -0.36))]
            d.add(Chain(st, [0.022, 0.018, 0.014], k=0.01))
            c = st[2] + v3((0, 0, -0.02))
            for j in range(46):
                o = v3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
                if np.linalg.norm(o) > 1:
                    continue
                o = o * v3((0.075, 0.075, 0.11))
                d.add(Ellipsoid(c + o, (0.028, 0.028, 0.038), R=rot_from_axes(z_axis=unit(o + v3((0, 0, -0.12))))), k=0.005)
        out.append(("Dates", d, fine(0.005, 0.01), "dates"))
    return out


# ------------------------------------------------------------------------------------------------ waterside plants
def papyrus(seed=0, n=11, h=1.5):
    """A papyrus clump: tall green stems, each topped with a burst of thread-like rays (the umbel), dark sheaths at the
    foot, in a mound of river mud."""
    rng = np.random.default_rng(seed)
    st, hd, mu = Field("Stems"), Field("Heads"), Field("Mud")
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.0, 0.22)
        b0 = v3((rr * math.cos(a), rr * math.sin(a), -0.04))
        hh = h * rng.uniform(0.62, 1.0)
        lean = rng.uniform(0.06, 0.24)
        top = b0 + v3((math.cos(a) * lean * hh, math.sin(a) * lean * hh, hh))
        mid = b0 + (top - b0) * 0.5 + v3((math.cos(a) * 0.03, math.sin(a) * 0.03, 0))
        st.add(Chain([b0, mid, top], [0.02, 0.016, 0.01], k=0.005))
        st.add(RoundCone(b0, b0 + v3((0, 0, 0.16)), 0.032, 0.02), k=0.01)        # the sheath at its foot
        up = unit(top - b0)
        nr = 15
        for j in range(nr):
            ph = 2 * math.pi * j / nr + rng.uniform(-0.15, 0.15)
            hz = v3((math.cos(ph), math.sin(ph), 0))
            ray = unit(up * 0.5 + hz * 0.86)
            Lr = rng.uniform(0.16, 0.22) * h / 1.5
            p1 = top + ray * (Lr * 0.55) + v3((0, 0, 0.012))
            p2 = top + ray * Lr + v3((0, 0, -0.035))
            hd.add(Chain([top, p1, p2], [0.0075, 0.0065, 0.004]), k=0.003)
        hd.add(Sphere(top, 0.02), k=0.004)
    mu.add(Ellipsoid((0, 0, -0.05), (0.36, 0.32, 0.11), **wob(4.0, 0.02, seed)))
    ground_cut(mu)
    return [("Stems", st, fine(0.005, 0.01), "papyrus"), ("Heads", hd, fine(0.0042, 0.0085), "papyrus_head"),
            ("Mud", mu, fine(0.012, 0.02), "mud")]


def reeds(seed=0, n=20, h=1.05):
    """Cattail reeds: long narrow leaves arching out of a mud mound, a few brown cattail heads on straight stalks."""
    rng = np.random.default_rng(seed)
    lv, ct, mu = Field("Leaves"), Field("Heads"), Field("Mud")
    th = max(0.0055, fine(0.005, 0.01) * 0.6)
    for i in range(n):                                  # flat leaf blades arching out (a chain of flat ellipsoids)
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, 0.18)
        b0 = v3((rr * math.cos(a), rr * math.sin(a), -0.04))
        hh = h * rng.uniform(0.55, 1.0)
        bend = rng.uniform(0.25, 0.7)
        hz = v3((math.cos(a), math.sin(a), 0))
        K = 9
        P = [b0 + hz * (bend * hh * (t ** 2.2)) + v3((0, 0, hh * t * (1.0 - 0.35 * bend * t ** 2))) for t in np.linspace(0, 1, K)]
        for k in range(K - 1):
            t0 = k / (K - 1)
            tg, sd, nn = frame(P[k + 1] - P[k])
            wdt = 0.022 * (1.0 - t0) ** 0.7 + 0.004
            L = float(np.linalg.norm(P[k + 1] - P[k]))
            lv.add(Ellipsoid((P[k] + P[k + 1]) / 2, (L * 0.62, wdt, th), R=rot_from_axes(x_axis=tg, y_axis=sd)), k=0.006)
    for i in range(4):
        a = rng.uniform(0, 2 * math.pi)
        b0 = v3((0.08 * math.cos(a), 0.08 * math.sin(a), -0.04))
        hh = h * rng.uniform(0.9, 1.15)
        top = b0 + v3((0.06 * math.cos(a), 0.06 * math.sin(a), hh))
        lv.add(RoundCone(b0, top, 0.011, 0.007))
        c = b0 + (top - b0) * 0.82
        ct.add(RoundCone(c - unit(top - b0) * 0.08, c + unit(top - b0) * 0.06, 0.03, 0.028))
        ct.add(RoundCone(c + unit(top - b0) * 0.06, top + unit(top - b0) * 0.05, 0.006, 0.003), k=0.004)
    mu.add(Ellipsoid((0, 0, -0.05), (0.3, 0.27, 0.1), **wob(4.0, 0.02, seed)))
    ground_cut(mu)
    return [("Leaves", lv, fine(0.005, 0.01), "reed_leaf"), ("Heads", ct, fine(0.006, 0.012), "cattail"),
            ("Mud", mu, fine(0.012, 0.02), "mud")]


# ------------------------------------------------------------------------------------------------ dry land plants
def acacia(h=2.3, w=2.9, seed=0):
    """An umbrella thorn acacia: a short twisting trunk forking into limbs that spread under a wide, flat-topped canopy."""
    rng = np.random.default_rng(seed)
    f = Field("Trunk")
    fork = v3((0.1, -0.06, h * 0.42))
    f.add(Chain([v3((0, 0, -0.08)), v3((0.04, 0.02, h * 0.2)), fork], [0.16, 0.125, 0.11], k=0.04, **wob(4.0, 0.012, seed)))
    for i in range(4):
        a = 2 * math.pi * i / 4 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((0.05 * math.cos(a), 0.05 * math.sin(a), 0.1), (0.3 * math.cos(a), 0.3 * math.sin(a), -0.03), 0.06, 0.025), k=0.05)
    tips = []
    for i in range(4):
        a = i * 2 * math.pi / 4 + rng.uniform(-0.35, 0.35) + 0.4
        rr = w * rng.uniform(0.28, 0.38)
        end = v3((rr * math.cos(a), rr * math.sin(a), h * rng.uniform(0.8, 0.88)))
        mid = fork + (end - fork) * 0.5 + v3((0, 0, -0.05))
        f.add(Chain([fork, mid, end], [0.09, 0.065, 0.04], k=0.02, **wob(6.0, 0.006, seed + i)), k=0.03)
        tips.append(end)
        for j in range(3):
            b = a + rng.uniform(-0.8, 0.8)
            tw = end + v3((0.3 * math.cos(b), 0.3 * math.sin(b), 0.14))
            f.add(RoundCone(end, tw, 0.03, 0.012), k=0.015)
    c = Field("Canopy")                                  # a flat-topped layer of many leafy clumps
    for i in range(42):
        a = rng.uniform(0, 2 * math.pi)
        rr = w * 0.44 * rng.uniform(0, 1) ** 0.75
        cz = h * (0.93 + 0.04 * (1 - rr / (w * 0.44))) + rng.uniform(-0.03, 0.03)
        rad = w * rng.uniform(0.09, 0.13)
        c.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a), cz), (rad, rad * 0.9, rad * 0.55), **wob(10.0 / w, 0.025, seed + 30 + i)), k=0.05)
    c.inter(Plane((0, 0, h * 1.03), (0, 0, 1)), k=0.05)                         # the flat top
    c.inter(Plane((0, 0, h * 0.86), (0, 0, -1)), k=0.05)                        # and a flat underside
    return [("Trunk", f, fine(0.008, 0.016), "acacia_bark"), ("Canopy", c, fine(0.012, 0.024), "acacia_leaves")]


def scrub(w=0.8, h=0.4, seed=0, mat="scrub"):
    """Dry desert scrub: crooked twigs fanning out of the sand, each ending in a small tuft of dusty grey-green leaves,
    gaps between them."""
    rng = np.random.default_rng(seed + 7)
    tw, lv = Field("Twigs"), Field("Leaves")
    for i in range(9):
        a = 2 * math.pi * i / 9 + rng.uniform(-0.3, 0.3)
        rr = w * rng.uniform(0.25, 0.5)
        tip = v3((rr * math.cos(a), rr * math.sin(a), h * rng.uniform(0.45, 1.0)))
        mid = tip * 0.45 + v3((rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), 0.04))
        tw.add(Chain([v3((0, 0, -0.03)), mid, tip], [0.024, 0.015, 0.007], k=0.01))
        for j in range(3):
            c = tip + v3((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), rng.uniform(-0.03, 0.04)))
            rad = w * rng.uniform(0.07, 0.11)
            lv.add(Ellipsoid(c, (rad, rad, rad * 0.8), **wob(12.0 / w, 0.012, seed * 10 + i * 3 + j)), k=0.03)
    ground_cut(tw)
    return [("Twigs", tw, fine(0.005, 0.01), "acacia_bark"), ("Leaves", lv, fine(0.006, 0.012), mat)]


# ------------------------------------------------------------------------------------------------ sand and stone
def dune(w=2.4, h=0.5, seed=0):
    """A crescent sand drift: a gentle windward back, a steep hollow slip face between two horns, wind ripples."""
    def ripples(P):
        return 0.006 * np.sin(P[:, 0] * 26.0 + NOISE.fbm(P * 1.5 + seed, 2) * 4.0) + NOISE.fbm(P * 2.0 + seed, 2) * 0.02
    f = Field("Sand")
    f.add(Ellipsoid((-w * 0.06, 0, -h * 0.25), (w * 0.5, w * 0.38, h * 1.25), disp=ripples, disp_amp=0.03))
    for side in (-1, 1):
        f.add(Ellipsoid((w * 0.24, side * w * 0.27, -h * 0.25), (w * 0.27, w * 0.13, h * 0.62), R=rot_from_axes(x_axis=(1, -side * 0.35, 0)),
                        disp=ripples, disp_amp=0.03), k=0.18 * w)
    f.sub(Ellipsoid((w * 0.43, 0, h * 0.3), (w * 0.26, w * 0.24, h * 1.05)), k=0.1 * w)
    ground_cut(f)
    return [("Sand", f, fine(0.012, 0.024) * w / 2.4, "sand")]


def sandrock(w=1.6, h=0.6, seed=0, n_extra=2):
    """A wind-carved desert rock: the boulder of decor_props.rock, cut into flat ledges along its bedding."""
    parts = rock(w, h, seed, "desert", n_extra)
    name, f, vxs, _ = parts[0]
    for k in range(2):                                   # (the boulder's radius at that height, so the groove bites)
        z = h * (0.3 + 0.28 * k)
        rz = 0.44 * w * math.sqrt(max(0.0, 1.0 - ((z - 0.25 * h) / (0.95 * h)) ** 2))
        f.sub(Torus((0, 0, z), rz + 0.02 * w, 0.045 * w, R=rot_from_axes(z_axis=(0.04 * k, 0.03, 1))), k=0.02 * w)
    return [(name, f, vxs, "rock")]


def _flutes(r, n, depth):
    def fn(P):
        th = np.arctan2(P[:, 1], P[:, 0])
        return depth * (0.5 - 0.5 * np.cos(n * th))
    return fn


def column(h=1.2, r=0.26, seed=0, broken=True, capital=False, glyphs=True, paint=True):
    """A sandstone column: square plinth, a round moulding, a fluted shaft (tapering a little), a lotus capital and abacus
    (standing ones) or a jagged break (broken ones); a band of carved signs and worn red and blue paint."""
    rng = np.random.default_rng(seed)
    f = Field("Column")
    f.add(RoundBox((0, 0, 0.05), (r * 1.4, r * 1.4, 0.08), 0.02, **wob(6.0, 0.006, seed)))
    f.add(Torus((0, 0, 0.15), r * 1.03, 0.05), k=0.02)
    H = h + 0.1
    fl = _flutes(r, 16, 0.014)

    def shaft(P):
        rr = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        R = r * (1.0 - 0.07 * np.clip(P[:, 2] / max(h, 0.5), 0, 1))
        return np.maximum(rr - R + fl(P), np.maximum(0.12 - P[:, 2], P[:, 2] - H)) * 0.92
    f.add(Func(shaft, (-r - 0.03, -r - 0.03, 0.1), (r + 0.03, r + 0.03, H + 0.02), **wob(5.0, 0.004, seed)), k=0.02)
    top = h
    if capital:                                         # a papyrus-bundle capital: a ribbed bell under a square abacus
        fl8 = _flutes(r, 8, 0.03)

        def bell(P):
            z = P[:, 2]
            t = np.clip((z - (h - 0.06)) / 0.3, 0, 1)
            R = r * (0.93 + 0.6 * t * t)
            rr = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
            return (np.maximum(rr - R + fl8(P) * t, np.maximum((h - 0.06) - z, z - (h + 0.24))) * 0.85).astype(F32)
        f.add(Func(bell, (-r * 1.6, -r * 1.6, h - 0.1), (r * 1.6, r * 1.6, h + 0.28)), k=0.02)
        for k in range(4):                                                                     # bands binding the bundle
            f.add(Torus((0, 0, h - 0.13 + k * 0.035), r * 0.94, 0.012), k=0.006)
        f.add(RoundBox((0, 0, h + 0.3), (r * 1.4, r * 1.4, 0.07), 0.015), k=0.01)             # the abacus
        top = h + 0.37
        if paint:
            f.paint(Cylinder((0, 0, h - 0.09), r * 1.1, 0.07), 7)
            f.paint(Cylinder((0, 0, h - 0.18), r * 1.1, 0.03), 5)
            f.paint(Cylinder((0, 0, h + 0.3), r * 1.6, 0.04), 5)
    if broken:
        nrm = unit((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 1.0))
        cut_above(f, (0, 0, h), nrm, (r * 2.0, r * 2.0, 0.6), disp=lambda P: NOISE.fbm(P * 9.0 + seed, 3) * 0.05, amp=0.06)
    if glyphs:                                                                                   # carved signs
        z0 = top * 0.45 if not capital else h * 0.55
        for col in range(5):
            th = 2 * math.pi * col / 5 + rng.uniform(-0.1, 0.1)
            nrm2 = v3((math.cos(th), math.sin(th), 0))
            tan = v3((-math.sin(th), math.cos(th), 0))
            for row in range(5):
                z = z0 + row * 0.075
                if broken and z > h - 0.12:
                    continue
                kind = rng.integers(0, 3)
                c = nrm2 * (r * (1.0 - 0.07 * min(z / max(h, 0.5), 1.0)) - 0.008) + v3((0, 0, z))
                R = rot_from_axes(x_axis=nrm2, y_axis=tan)
                if kind == 0:
                    f.sub(RoundBox(c, (0.014, 0.024, 0.012), 0.004, R=R), k=0.003)
                elif kind == 1:
                    f.sub(Ellipsoid(c, (0.014, 0.018, 0.026), R=R), k=0.003)
                else:
                    f.sub(RoundBox(c, (0.014, 0.008, 0.028), 0.004, R=R), k=0.003)
                    f.sub(RoundBox(c + v3((0, 0, 0.018)), (0.014, 0.022, 0.008), 0.004, R=R), k=0.003)
        if paint and not capital:
            f.paint(Cylinder((0, 0, z0 - 0.06), r * 1.2, 0.035), 5)
    cut_below(f, -0.03, 0, 0, r * 2.0, r * 2.0)
    return [("Column", f, fine(0.0075, 0.015), "sandstone")]


def blocks(seed=0):
    """Fallen ashlar blocks: two dressed blocks with chipped edges, one carved with a winged sun disc, and a column drum."""
    rng = np.random.default_rng(seed)
    f = Field("Blocks")
    R1 = rot_from_axes(x_axis=(math.cos(0.3), math.sin(0.3), 0.08), z_axis=(0.05, -0.06, 1))
    f.add(RoundBox((0, 0, 0.2), (0.5, 0.3, 0.26), 0.03, R=R1, **wob(4.0, 0.008, seed)))
    R2 = rot_from_axes(x_axis=(math.cos(1.4), math.sin(1.4), 0.25), z_axis=(0.2, -0.3, 1))
    f.add(RoundBox((0.55, 0.5, 0.14), (0.36, 0.26, 0.2), 0.03, R=R2, **wob(4.0, 0.008, seed + 1)))
    # the sun disc and its wings on the big block's face (-y side)
    face = R1 @ v3((0, -1, 0))
    fc = v3((0, 0, 0.22)) + face * 0.3
    f.add(Cylinder(fc, 0.075, 0.03, rr=0.008, R=rot_from_axes(z_axis=face)), k=0.006)            # the sun disc in relief
    f.paint(Cylinder(fc + face * 0.01, 0.085, 0.04, R=rot_from_axes(z_axis=face)), 5)
    for side in (-1, 1):                                                                         # and its wings
        ax = R1 @ v3((side, 0, 0))
        for k in range(3):
            wc = fc + ax * (0.16 + 0.07 * k) + v3((0, 0, 0.035 - 0.022 * k))
            f.add(RoundBox(wc, (0.055, 0.012, 0.016), 0.006, R=rot_from_axes(x_axis=ax, y_axis=face)), k=0.004)
            f.paint(RoundBox(wc + face * 0.012, (0.06, 0.02, 0.022), 0.0, R=rot_from_axes(x_axis=ax, y_axis=face)), 7)
    for _ in range(6):                                  # chips off the edges
        c = R1 @ v3((rng.choice([-0.5, 0.5]), rng.choice([-0.3, 0.3]), rng.uniform(-0.2, 0.26))) + v3((0, 0, 0.2))
        f.sub(Sphere(c, rng.uniform(0.06, 0.11)), k=0.02)
    f.add(Cylinder((-0.55, 0.45, 0.2), 0.22, 0.42, rr=0.03, R=rot_from_axes(z_axis=(math.cos(0.9), math.sin(0.9), 0.05)), **wob(5.0, 0.006, seed + 2)))
    ground_cut(f)
    return [("Blocks", f, fine(0.009, 0.018), "sandstone")]


# ------------------------------------------------------------------------------------------------ canyon rock
def mesa(h=2.4, r=1.1, seed=0, layers=5):
    """A red-rock butte: stacked strata, each a little narrower than the one below (ledges), worn into gullies, a hard
    caprock overhanging the top, a skirt of fallen rubble at the foot."""
    rng = np.random.default_rng(seed)
    f = Field("Rock")
    z = 0.0
    lh = h / layers

    def gully(P):
        th = np.arctan2(P[:, 1], P[:, 0])
        return 0.06 * r * np.maximum(0, np.sin(th * 7 + NOISE.fbm(P * 0.8 + seed, 2) * 6.0)) ** 3 + NOISE.fbm(P * v3((2.5, 2.5, 0.6)).astype(F32) + seed, 3) * 0.06 * r
    for k in range(layers):
        rk = r * (1.0 - 0.09 * k + rng.uniform(-0.04, 0.04))
        top = h - 0.04 if k == layers - 1 else z + lh
        f.add(Cylinder((rng.uniform(-0.04, 0.04) * r, rng.uniform(-0.04, 0.04) * r, (z + top) / 2 - 0.02), rk, top - z + 0.04, rr=lh * 0.25,
                       disp=gully, disp_amp=0.1 * r), k=0.04)
        z = top
    f.add(Cylinder((0, 0, h - lh * 0.3), r * (1.0 - 0.09 * (layers - 1)) * 1.1, lh * 0.6, rr=0.06, **wob(1.8 / r, 0.04 * r, seed + 3)), k=0.03)
    for i in range(9):
        nrm = unit((rng.normal(), rng.normal(), rng.uniform(-0.15, 0.15)))
        f.inter(Plane(nrm * r * rng.uniform(0.88, 1.0) + v3((0, 0, h * 0.5)), nrm), k=0.05 * r)
    sk = Field("Rubble")
    sk.add(Ellipsoid((0, 0, -0.1), (r * 1.35, r * 1.3, 0.34), **wob(2.0 / r, 0.05, seed + 5)))
    for i in range(10):
        a = rng.uniform(0, 2 * math.pi)
        rr = r * rng.uniform(1.0, 1.35)
        sz = rng.uniform(0.08, 0.18)
        sk.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a), 0.03), (sz, sz * 0.8, sz * 0.6), **wob(8.0, 0.02, seed + 20 + i)), k=0.03)
    ground_cut(f)
    ground_cut(sk)
    return [("Rock", f, fine(0.012, 0.024) * max(h, 2 * r) / 2.4, "rock"), ("Rubble", sk, fine(0.012, 0.024), "rock")]


def hoodoo(h=2.6, r=0.42, seed=0):
    """A hoodoo: a thin spire of soft rock pinched between harder bands, balancing a flat capstone."""
    rng = np.random.default_rng(seed)
    f = Field("Rock")
    n = 4
    lean = v3((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 0))
    zs = np.cumsum([0] + list(rng.uniform(0.7, 1.3, n)))
    zs = zs / zs[-1] * h
    for k in range(n):
        z0, z1 = zs[k], zs[k + 1]
        rk = r * (1.05 - 0.12 * k) * rng.uniform(0.85, 1.1)
        c = lean * ((z0 + z1) / 2 / h) + v3((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), (z0 + z1) / 2))
        f.add(Ellipsoid(c, (rk, rk * rng.uniform(0.8, 0.95), (z1 - z0) * 0.62), R=rot_from_axes(x_axis=(math.cos(k * 1.3), math.sin(k * 1.3), 0)),
                        **wob(3.0, 0.06, seed + k)), k=0.12)
    f.add(RoundCone((0, 0, -0.05), lean + v3((0, 0, h * 0.95)), r * 0.8, r * 0.42, **wob(4.0, 0.03, seed + 7)), k=0.12)
    for i in range(6):                                  # chipped facets
        nrm = unit((rng.normal(), rng.normal(), rng.uniform(-0.2, 0.2)))
        f.inter(Plane(v3((0, 0, h * 0.5)) + nrm * r * 0.95, nrm), k=0.06)
    cap = lean + v3((0.04, -0.02, h + 0.06))
    f.add(Ellipsoid(cap, (r * 1.4, r * 1.2, 0.2), R=rot_from_axes(x_axis=(math.cos(seed), math.sin(seed), 0.12)), **wob(3.0, 0.06, seed + 9)), k=0.03)
    f.add(Ellipsoid(cap + v3((r * 0.4, r * 0.2, 0.1)), (r * 0.7, r * 0.6, 0.15), **wob(4.0, 0.04, seed + 10)), k=0.08)
    f.add(Ellipsoid((0, 0, -0.08), (r * 1.6, r * 1.5, 0.28), **wob(3.0, 0.04, seed + 11)), k=0.12)
    ground_cut(f)
    return [("Rock", f, fine(0.01, 0.02), "rock")]


def ore(w=0.9, h=0.55, seed=0, glow=True):
    """A copper ore outcrop: red rock lumps crusted with banded green malachite, a few glowing turquoise crystal points."""
    rng = np.random.default_rng(seed)
    base = Field("Rock")
    base.add(Ellipsoid((0, 0, 0.0), (w * 0.5, w * 0.42, h * 0.55), **wob(3.0 / w, 0.03, seed)))
    base.add(Ellipsoid((w * 0.3, w * 0.12, 0.0), (w * 0.28, w * 0.24, h * 0.4), **wob(4.0 / w, 0.025, seed + 1)), k=0.05)
    for i in range(6):
        nrm = unit((rng.normal(), rng.normal(), abs(rng.normal()) + 0.5))
        base.inter(Plane(v3((0, 0, h * 0.1)) + nrm * w * 0.44, nrm), k=0.02)
    ground_cut(base)
    m = Field("Malachite")                               # a bubbly crust on the rock's top and flanks
    pts = []
    for i in range(400):
        a = rng.uniform(0, 2 * math.pi)
        rr = w * 0.5 * math.sqrt(rng.uniform(0, 1))
        P0 = v3((rr * math.cos(a), rr * math.sin(a), h))
        zz = h
        for _ in range(24):                             # drop it onto the rock
            if base.eval(np.array([[P0[0], P0[1], zz]], np.float32))[0] < 0 or zz < 0:
                break
            zz -= h / 22
        if zz > h * 0.12:
            pts.append(v3((P0[0], P0[1], zz)))
        if len(pts) >= 30:
            break
    for i, q in enumerate(pts):
        m.add(Sphere(q, w * rng.uniform(0.045, 0.075)), k=0.02)
    ground_cut(m)
    out = [("Rock", base, fine(0.008, 0.016), "rock"), ("Malachite", m, fine(0.006, 0.012), "malachite")]
    if glow:
        g = Field("Crystals")
        for i in range(5):
            a = 2 * math.pi * i / 5 + rng.uniform(-0.4, 0.4)
            b = v3((w * 0.18 * math.cos(a), w * 0.18 * math.sin(a), h * 0.25))
            cr = w * rng.uniform(0.035, 0.05)
        g.add(crystal(b, (math.cos(a) * 0.5, math.sin(a) * 0.5, 1.0), cr, h * rng.uniform(0.45, 0.7), tip=cr * 1.1, twist=rng.uniform(0, 1)))   # (pointed)
        out.append(("Crystals", g, fine(0.005, 0.01), "glow_turq"))
    return out


def cart(seed=0, ore_load=True, off=(0, 0, 0)):
    """A mine cart: a flared timber box with bronze corner straps and studs on four solid wheels, heaped with ore."""
    o = v3(off)
    f = Field("Cart")
    body = convex([(o + v3((0, 0, 0.62)), (0, 0, 1)), (o + v3((0, 0, 0.18)), (0, 0, -1)),
                   (o + v3((0.45, 0, 0.4)), (1, 0, -0.18)), (o + v3((-0.45, 0, 0.4)), (-1, 0, -0.18)),
                   (o + v3((0, 0.3, 0.4)), (0, 1, -0.18)), (o + v3((0, -0.3, 0.4)), (0, -1, -0.18))], o - 0.7, o + 0.9)
    f.add(body)
    f.sub(RoundBox(o + v3((0, 0, 0.62)), (0.42, 0.27, 0.36), 0.02))
    for sx in (-1, 1):                                    # bronze straps at the corners, studs along the rim
        for sy in (-1, 1):
            f.paint(RoundBox(o + v3((sx * 0.44, sy * 0.3, 0.4)), (0.05, 0.05, 0.24), 0.0), 6)
    f.paint(RoundBox(o + v3((0, 0, 0.6)), (0.6, 0.45, 0.03)), 6)
    for k in range(7):
        for sy in (-1, 1):
            f.add(Sphere(o + v3((-0.36 + k * 0.12, sy * 0.335, 0.48)), 0.016), k=0.004, label=6)
    for sx in (-1, 1):                                    # wheels and axles
        f.add(Cylinder(o + v3((sx * 0.27, 0, 0.15)), 0.035, 0.74, R=rot_from_axes(z_axis=(0, 1, 0))))
        for sy in (-1, 1):
            f.add(Cylinder(o + v3((sx * 0.27, sy * 0.34, 0.15)), 0.15, 0.06, rr=0.015, R=rot_from_axes(z_axis=(0, 1, 0))), k=0.004)
            f.paint(Cylinder(o + v3((sx * 0.27, sy * 0.37, 0.15)), 0.05, 0.03, R=rot_from_axes(z_axis=(0, 1, 0))), 6)
    f.inter(Plane(o + v3((0, 0, 0.0)), (0, 0, -1)))
    out = [("Cart", f, fine(0.006, 0.012), "siege")]
    if ore_load:
        rng = np.random.default_rng(seed)
        m, rk = Field("Load"), Field("LoadRock")
        for i in range(24):
            c = o + v3((rng.uniform(-0.34, 0.34), rng.uniform(-0.2, 0.2), rng.uniform(0.55, 0.64) + 0.06 * (1 - abs(rng.uniform(-1, 1)))))
            (m if i % 3 == 0 else rk).add(Ellipsoid(c, v3((0.08, 0.07, 0.06)) * rng.uniform(0.8, 1.3), **wob(14.0, 0.01, seed + i)), k=0.015)
        m.inter(Plane(o + v3((0, 0, 0.5)), (0, 0, -1)))
        rk.inter(Plane(o + v3((0, 0, 0.5)), (0, 0, -1)))
        out.append(("Load", m, fine(0.006, 0.012), "malachite"))
        out.append(("LoadRock", rk, fine(0.006, 0.012), "rock"))
    return out


def timbers(seed=0):
    """Pit props stacked for the mine: five trimmed logs in a pile, two planks and a wedge."""
    rng = np.random.default_rng(seed)
    f = Field("Logs")
    R = rot_from_axes(z_axis=(1, 0.05, 0))
    for i, (y, z) in enumerate(((-0.22, 0.11), (0.0, 0.11), (0.22, 0.11), (-0.11, 0.3), (0.11, 0.3))):
        f.add(Cylinder((rng.uniform(-0.05, 0.05), y, z), 0.105, 1.3 + rng.uniform(-0.1, 0.1), rr=0.02, R=R, **wob(5.0, 0.008, seed + i)))
    for k in range(2):
        f.add(RoundBox((0.1, 0.5 + 0.1 * k, 0.04 + 0.05 * k), (0.62, 0.09, 0.022), 0.008, R=rot_from_axes(x_axis=(math.cos(0.15 * k), math.sin(0.15 * k), 0))))
    ground_cut(f)
    return [("Logs", f, fine(0.007, 0.014), "wood_end")]


# ------------------------------------------------------------------------------------------------ placing sub-fields
class Moved:
    """A primitive moved (and turned: R's columns are its local axes in the world) to `o`."""
    def __init__(self, prim, o, R=None):
        self.p = prim
        self.o = v3(o)
        self.R = np.eye(3) if R is None else np.asarray(R, np.float64)
        lo, hi = v3(prim.lo), v3(prim.hi)
        if np.all(np.abs(lo) < 1e8):
            C = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) @ self.R.T + self.o
            self.lo, self.hi = C.min(0), C.max(0)
        else:
            self.lo, self.hi = np.full(3, -1e9), np.full(3, 1e9)
        self.Rf, self.of = self.R.astype(F32), self.o.astype(F32)

    def __call__(self, P):
        return self.p(((P - self.of) @ self.Rf).astype(F32))


def place(dst, src, o, R=None):
    """Copy every op of field `src` into field `dst`, moved to `o` (and turned by R)."""
    for kind, prim, k, label in src.ops:
        dst.ops.append((kind, Moved(prim, o, R), k, label))
    return dst


def place_parts(out, parts, o, R=None, rename=None):
    """Append a prop's parts to `out`, moved; parts with the same name (and material) merge into one field."""
    have = {n: (f, vxs, m) for n, f, vxs, m in out}
    for n, f, vxs, m in parts:
        n2 = rename.get(n, n) if rename else n
        global_ops = any(op[0] == "inter" for op in f.ops)
        if n2 in have and global_ops:                  # (an inter would cut the shapes already in that field)
            k = 2
            while "%s_%d" % (n2, k) in have:
                k += 1
            n2 = "%s_%d" % (n2, k)
        if n2 in have and have[n2][2] == m and not any(op[0] == "inter" for op in have[n2][0].ops):
            place(have[n2][0], f, o, R)
        else:
            g = place(Field(n2), f, o, R)
            out.append((n2, g, vxs, m))
            have[n2] = (g, vxs, m)
    return out


def mound(out, rx, ry, h=0.2, seed=0, c=(0, 0), voxel=None):
    t = Field("Mound")
    t.add(Ellipsoid((c[0], c[1], -h * 0.6), (rx, ry, h * 1.6), **wob(1.6, 0.04, seed)))
    ground_cut(t, -0.02)
    out.append(("Mound", t, voxel or fine(0.02, 0.035), "turf"))
    return out


def convex_w(planes, lo, hi, amp=0.0, scale=3.0, seed=0):
    """decor_props.convex, with a little hand-made unevenness (noise displacement)."""
    c = convex(planes, lo, hi)
    if amp <= 0:
        return c
    off = np.array([seed * 5.17, seed * 2.31, seed * 7.9], F32)
    fn = c.fn
    return Func(lambda P: fn(P) + NOISE.fbm(P * scale + off, 2) * amp, lo, hi)


def walls_box(cx, cy, hx, hy, z0, z1, batter=0.05, amp=0.006, seed=0):
    """A block with battered (inward-leaning) walls."""
    return convex_w([((cx, cy, z1), (0, 0, 1)), ((cx, cy, z0), (0, 0, -1)), ((cx + hx, cy, 0), (1, 0, batter)),
                     ((cx - hx, cy, 0), (-1, 0, batter)), ((cx, cy + hy, 0), (0, 1, batter)), ((cx, cy - hy, 0), (0, -1, batter))],
                    (cx - hx - 0.1, cy - hy - 0.1, z0 - 0.1), (cx + hx + 0.1, cy + hy + 0.1, z1 + 0.1), amp, 3.0, seed)


def jar(f, c, s=1.0, painted=True):
    """A water jar: a round belly, a neck and a rolled rim, hollow at the mouth."""
    c = v3(c)
    f.add(Ellipsoid(c + v3((0, 0, 0.19 * s)), (0.13 * s, 0.13 * s, 0.17 * s)))
    f.add(RoundCone(c + v3((0, 0, 0.3 * s)), c + v3((0, 0, 0.42 * s)), 0.06 * s, 0.045 * s), k=0.03 * s)
    f.add(Torus(c + v3((0, 0, 0.43 * s)), 0.05 * s, 0.014 * s), k=0.01 * s)
    f.sub(Cylinder(c + v3((0, 0, 0.45 * s)), 0.035 * s, 0.12 * s))
    if painted:
        f.paint(Cylinder(c + v3((0, 0, 0.26 * s)), 0.2 * s, 0.025 * s), 5)


# ------------------------------------------------------------------------------------------------ delta landmarks
def house(seed=0):
    """A delta farmhouse of mud brick: battered walls, a parapet round the flat roof with a reed-mat shade on palm
    poles, palm-log beam ends under it, a whitewashed doorway with a log lintel, small windows, an outside stair to the
    roof; beside it a walled yard with a bread oven and water jars. The door faces -Y."""
    rng = np.random.default_rng(seed)
    out = []
    W, D, H = 1.0, 0.78, 1.3
    f = Field("Walls")
    f.add(walls_box(0, 0, W, D, -0.05, H + 0.14, 0.05, 0.007, seed))
    f.sub(RoundBox((0, 0, H + 0.4), (W - 0.2, D - 0.2, 0.4), 0.03))                      # the roof inside the parapet
    f.sub(RoundBox((-0.35, -D, 0.37), (0.2, 0.22, 0.38), 0.05))                          # doorway
    for (c, half) in (((0.45, -D, 0.95), (0.1, 0.2, 0.09)), ((W, 0.22, 0.95), (0.2, 0.1, 0.09)), ((-W, -0.3, 0.95), (0.2, 0.09, 0.08))):
        f.sub(RoundBox(c, half, 0.02))                                                    # windows
    f.paint(RoundBox((-0.35, -D - 0.05, 0.45), (0.36, 0.12, 0.52)), 7)                   # whitewash round the door
    f.paint(RoundBox((0, 0, H - 0.07), (W + 0.3, D + 0.3, 0.035)), 5)                    # a band of blue glazed brick
    for k in range(6):                                                                    # stair to the roof (-X side)
        zt = (k + 1) * H / 6
        f.add(RoundBox((-W - 0.24, -D + 0.32 + k * 0.2, zt / 2), (0.21, 0.11, zt / 2), 0.02, **wob(5.0, 0.005, seed + k)), k=0.012)
    yard = [((W - 0.05, -D + 0.08), (W + 1.05, -D + 0.08)), ((W + 1.05, -D + 0.08), (W + 1.05, -0.18)),
            ((W + 1.05, 0.28), (W + 1.05, D - 0.08)), ((W + 1.05, D - 0.08), (W - 0.05, D - 0.08))]
    for (a, b) in yard:                                                                   # the yard wall (gap = its gate)
        a, b = v3((a[0], a[1], 0)), v3((b[0], b[1], 0))
        L = float(np.linalg.norm(b - a))
        R = rot_from_axes(x_axis=unit(b - a), z_axis=(0, 0, 1))
        f.add(RoundBox((a + b) / 2 + v3((0, 0, 0.27)), (L / 2 + 0.07, 0.075, 0.3), 0.04, R=R, **wob(4.0, 0.006, seed + 3)), k=0.02)
    ground_cut(f)
    out.append(("Walls", f, fine(0.0095, 0.019), "mudbrick"))
    w = Field("Wood")
    w.add(Cylinder((-0.35, -D - 0.02, 0.8), 0.055, 0.6, rr=0.015, R=rot_from_axes(z_axis=(1, 0, 0))), label=10)   # lintel
    for k in range(6):                                                                    # roof beam ends
        x = -W + 0.2 + k * (2 * W - 0.4) / 5
        for sy in (-1, 1):
            w.add(Cylinder((x, sy * (D + 0.02), H - 0.18), 0.045, 0.16, rr=0.01, R=rot_from_axes(z_axis=(0, 1, 0))))
    for (x, y) in ((0.05, -0.38), (0.75, -0.38), (0.05, 0.38), (0.75, 0.38)):          # shade poles on the roof
        w.add(RoundCone((x, y, H - 0.02), (x, y, H + 0.72), 0.035, 0.03), label=11)
    for y in (-0.38, 0.38):
        w.add(Cylinder((0.4, y, H + 0.74), 0.03, 0.9, R=rot_from_axes(z_axis=(1, 0, 0))), label=10)
    out.append(("Wood", w, fine(0.006, 0.012), "siege"))
    m = Field("Mat")
    m.add(RoundBox((0.4, 0.0, H + 0.79), (0.5, 0.5, 0.022), 0.01, R=rot_from_axes(x_axis=(1, 0, 0.06), z_axis=(-0.06, 0, 1)), **wob(6.0, 0.004, seed + 5)))
    for k in range(5):
        m.paint(RoundBox((0.4, -0.4 + k * 0.2, H + 0.79), (0.55, 0.012, 0.06)), 5)
    out.append(("Mat", m, fine(0.006, 0.012), "reed"))
    p = Field("Pots")
    p.add(Ellipsoid((W + 0.75, 0.42, 0.0), (0.24, 0.24, 0.32)))                       # the bread oven
    p.sub(Ellipsoid((W + 0.75, 0.42, 0.0), (0.19, 0.19, 0.27)))
    p.sub(Cylinder((W + 0.75, 0.42, 0.3), 0.07, 0.1))
    p.sub(RoundBox((W + 0.55, 0.42, 0.1), (0.1, 0.07, 0.08), 0.03))
    for (x, y, s) in ((W + 0.32, -0.5, 1.0), (W + 0.5, -0.56, 0.85), (-0.85, -D - 0.25, 0.9)):
        jar(p, (x, y, 0), s)
    ground_cut(p)
    out.append(("Pots", p, fine(0.006, 0.012), "terracotta"))
    d = Field("Dark")
    d.add(RoundBox((-0.35, -D + 0.12, 0.37), (0.19, 0.04, 0.37), 0.04))
    for (c, half) in (((0.45, -D + 0.1, 0.95), (0.09, 0.03, 0.08)), ((W - 0.1, 0.22, 0.95), (0.03, 0.09, 0.08)), ((-W + 0.1, -0.3, 0.95), (0.03, 0.08, 0.07))):
        d.add(RoundBox(c, half, 0.015))
    out.append(("Dark", d, fine(0.008, 0.016), "dark"))
    return mound(out, 2.2, 1.35, 0.16, seed, c=(0.35, 0))


def granary(seed=0):
    """Three beehive grain silos of plastered mud on a low platform: a hatch at each top (one lid off, leaning), a
    hatch near the foot, a palm-log ladder up the tallest."""
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Silos")
    f.add(RoundBox((0, -0.05, 0.04), (1.08, 0.98, 0.1), 0.07, **wob(3.0, 0.01, seed)))
    silos = [((-0.45, 0.12), 0.45, 1.4), ((0.45, 0.28), 0.38, 1.15), ((0.05, -0.5), 0.34, 0.95)]
    for i, ((x, y), r, hh) in enumerate(silos):
        zb = hh - r * 0.95
        f.add(RoundCone((x, y, 0.05), (x, y, zb), r, r * 0.94, **wob(4.0, 0.006, seed + i)), k=0.05)
        f.add(Ellipsoid((x, y, zb), (r * 0.94, r * 0.94, r * 0.98), **wob(4.0, 0.006, seed + i)), k=0.04)
        f.add(Cylinder((x, y, hh + 0.02), r * 0.27, 0.09, rr=0.025), k=0.03)
        f.sub(Cylinder((x, y, hh + 0.08), r * 0.18, 0.2))
        f.sub(RoundBox((x, y - r * 0.95, 0.42), (0.09, 0.12, 0.1), 0.03))
        f.paint(Torus((x, y, zb * 0.62), r * 0.98, 0.025), 5 if i == 0 else 7)
    ground_cut(f)
    out.append(("Silos", f, fine(0.009, 0.018), "mud_plaster"))
    w = Field("Wood")
    (x, y), r, hh = silos[0]
    for sx in (-1, 1):                                                                    # ladder up the tallest silo
        w.add(RoundCone((x - 0.75 + sx * 0.16, y - 0.35, 0.0), (x - 0.38 + sx * 0.16, y - 0.12, hh * 0.92), 0.03, 0.025), label=11)
    for k in range(7):
        t = (k + 0.5) / 7
        p0 = v3((x - 0.75 + 0.37 * t, y - 0.35 + 0.23 * t, hh * 0.92 * t))
        w.add(Cylinder(p0, 0.018, 0.36, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.006, label=10)
    (x2, y2), r2, hh2 = silos[1]
    w.add(Cylinder((x2 + r2 * 0.9, y2 + 0.05, 0.38), r2 * 0.25, 0.04, rr=0.012, R=rot_from_axes(z_axis=(0.9, 0.1, 0.42))))   # a lid, leaning
    w.add(Cylinder((silos[2][0][0], silos[2][0][1], silos[2][2] + 0.09), silos[2][1] * 0.24, 0.04, rr=0.012))
    out.append(("Wood", w, fine(0.006, 0.012), "siege"))
    d = Field("Dark")
    for (x, y), r, hh in silos:
        d.add(RoundBox((x, y - r * 0.86, 0.42), (0.085, 0.03, 0.095), 0.02))
        d.add(Cylinder((x, y, hh + 0.02), r * 0.17, 0.06))
    out.append(("Dark", d, fine(0.008, 0.016), "dark"))
    s = Field("Sacks")
    for k in range(3):
        c = v3((0.85 + 0.2 * k, -0.75 + 0.1 * k, 0.12))
        s.add(Ellipsoid(c, (0.14, 0.11, 0.16), **wob(8.0, 0.01, seed + 20 + k)))
        s.add(RoundCone(c + v3((0, 0, 0.12)), c + v3((0.02, 0, 0.22)), 0.04, 0.025), k=0.03)
    ground_cut(s)
    out.append(("Sacks", s, fine(0.006, 0.012), "linen"))
    return mound(out, 1.5, 1.4, 0.15, seed)


def shaduf(seed=0):
    """A shaduf by the river: two plastered posts and a crossbeam carry a long sweep pole, its counterweight of dried
    mud raised high, its bucket on a rope lowered toward the water (+X)."""
    out = []
    f = Field("Posts")
    for sy in (-1, 1):
        f.add(RoundCone((0, sy * 0.32, 0.0), (0, sy * 0.32, 1.56), 0.12, 0.085, **wob(5.0, 0.008, seed + sy)))
    f.add(RoundBox((-0.1, 0, 0.05), (0.62, 0.55, 0.1), 0.06, **wob(3.0, 0.01, seed)), k=0.06)
    f.add(RoundBox((1.25, 0, 0.1), (0.36, 0.24, 0.1), 0.05, **wob(3.0, 0.008, seed + 4)), k=0.04)      # a trough
    f.sub(RoundBox((1.25, 0, 0.2), (0.28, 0.16, 0.1), 0.04))
    f.add(RoundBox((1.85, 0, 0.04), (0.28, 0.09, 0.06), 0.03), k=0.05)                                # its channel
    f.sub(RoundBox((1.9, 0, 0.11), (0.4, 0.05, 0.06), 0.02))
    ground_cut(f)
    out.append(("Posts", f, fine(0.008, 0.016), "mud_plaster"))
    w = Field("Wood")
    w.add(Cylinder((0, 0, 1.62), 0.055, 0.86, rr=0.015, R=rot_from_axes(z_axis=(0, 1, 0))))
    P0 = v3((0, 0, 1.69))
    dr = v3((math.cos(math.radians(-27)), 0, math.sin(math.radians(-27))))
    long_end, short_end = P0 + dr * 2.15, P0 - dr * 1.0
    w.add(RoundCone(short_end, long_end, 0.05, 0.032), label=10)
    for o in (-0.05, 0.05):
        w.add(Torus(P0 + dr * o, 0.06, 0.012, R=rot_from_axes(z_axis=dr)), k=0.004, label=8)          # lashing
    w.add(RoundCone(long_end, long_end - v3((0, 0, 0.46)), 0.008, 0.008), label=8)                  # the rope
    for o in (-0.07, 0.07):
        w.add(Torus(short_end + dr * o - v3((0, 0, 0.1)), 0.15, 0.012), k=0.003, label=8)
    out.append(("Wood", w, fine(0.0055, 0.011), "siege"))
    c = Field("Weight")
    c.add(Ellipsoid(short_end - v3((0, 0, 0.11)), (0.17, 0.16, 0.15), **wob(6.0, 0.012, seed + 8)))
    out.append(("Weight", c, fine(0.008, 0.016), "mud"))
    p = Field("Pot")
    pc = long_end - v3((0, 0, 0.62))
    p.add(Ellipsoid(pc, (0.12, 0.12, 0.11)))
    p.add(Torus(pc + v3((0, 0, 0.09)), 0.075, 0.016), k=0.01)
    p.sub(Cylinder(pc + v3((0, 0, 0.12)), 0.065, 0.1))
    p.paint(Cylinder(pc + v3((0, 0, 0.02)), 0.14, 0.025), 5)
    out.append(("Pot", p, fine(0.005, 0.01), "terracotta"))
    return mound(out, 1.3, 0.9, 0.12, seed, c=(0.4, 0))


def boat(seed=0):
    """A papyrus reed boat at its mooring: bundles of reeds bound with rope, both ends sweeping up and curling in, a
    punting pole and a basket aboard. It floats at z = 0 (the river's surface)."""
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Hull")
    L = 1.2
    N = 28
    xs = np.linspace(-L, L, N)

    def zc(x):
        a = np.clip((abs(x) - 0.5) / (L - 0.5), 0, 1)
        return 0.02 + 0.5 * a ** 1.6

    def reeds_disp(P):
        return 0.006 * np.sin(P[:, 1] * 70.0 + np.sin(P[:, 0] * 3.0)) + NOISE.fbm(P * 8.0 + seed, 2) * 0.004
    for i, x in enumerate(xs):
        u = abs(x) / L
        wy = 0.3 * max(0.0, 1 - u ** 2.4) ** 0.6 + 0.035
        hz = 0.11 * max(0.0, 1 - u ** 2.0) ** 0.5 + 0.035
        x2 = xs[min(i + 1, N - 1)] if i < N - 1 else x + 0.01
        tan = unit(v3((x2 - x, 0, zc(x2) - zc(x))) if i < N - 1 else v3((1, 0, zc(x) - zc(xs[i - 1]))))
        f.add(Ellipsoid((x, 0, zc(x)), (0.09, wy, hz), R=rot_from_axes(x_axis=tan, y_axis=(0, 1, 0)), disp=reeds_disp, disp_amp=0.01), k=0.04)
    for sx in (-1, 1):                                                                    # the curled ends
        e = v3((sx * L, 0, zc(L)))
        f.add(Chain([e, e + v3((sx * 0.08, 0, 0.14)), e + v3((0, 0, 0.24)), e + v3((-sx * 0.08, 0, 0.2))], [0.04, 0.032, 0.024, 0.018], k=0.02), k=0.02)
    for k in range(9):                                                                    # rope bindings
        x = -1.0 + k * 0.25
        tan = unit(v3((0.02, 0, zc(x + 0.01) - zc(x))) + v3((1, 0, 0)))
        f.paint(Cylinder((x, 0, zc(x)), 0.4, 0.035, R=rot_from_axes(z_axis=tan)), 5)
    f.inter(Plane((0, 0, -0.03), (0, 0, -1)))
    out.append(("Hull", f, fine(0.007, 0.014), "reed"))
    w = Field("Pole")
    w.add(RoundCone((-0.9, 0.12, 0.16), (1.05, -0.08, 0.2), 0.022, 0.018), label=10)
    out.append(("Pole", w, fine(0.005, 0.01), "siege"))
    b = Field("Basket")
    b.add(Cylinder((0.35, 0.02, 0.2), 0.13, 0.16, rr=0.03))
    b.sub(Cylinder((0.35, 0.02, 0.3), 0.1, 0.14))
    out.append(("Basket", b, fine(0.005, 0.01), "reed"))
    return out


# ------------------------------------------------------------------------------------------------ desert landmarks
def ruin(seed=0):
    """A ruined colonnade on its stepped platform: two columns still carrying a stretch of architrave, one broken
    halfway, one a stump; drums and a fallen block lying in the sand before it."""
    out = []
    plat = Field("Platform")
    plat.add(RoundBox((0, 0, 0.09), (1.9, 0.62, 0.12), 0.025, **wob(3.0, 0.006, seed)))
    plat.add(RoundBox((0, 0, 0.26), (1.72, 0.48, 0.08), 0.02, **wob(3.0, 0.006, seed + 1)), k=0.01)
    for (x, y, rr) in ((1.6, -0.55, 0.22), (-1.75, 0.5, 0.18), (0.4, 0.62, 0.15)):
        plat.sub(Sphere((x, y, 0.3), rr), k=0.03)                                        # broken corners
    ground_cut(plat)
    out.append(("Platform", plat, fine(0.01, 0.02), "ashlar"))
    cols = [(-1.25, 2.1, False, True), (-0.42, 2.1, False, True), (0.42, 1.05, True, False), (1.25, 0.42, True, False)]
    for i, (x, hh, broken, cap) in enumerate(cols):
        place_parts(out, column(hh, 0.24, seed + 10 + i, broken=broken, capital=cap, glyphs=(i != 3)), (x, 0, 0.32))
    a = Field("Architrave")
    a.add(RoundBox((-0.84, 0, 2.1 + 0.32 + 0.38 + 0.15), (0.72, 0.3, 0.15), 0.02, **wob(4.0, 0.006, seed + 3)))
    a.sub(Sphere((-0.1, 0.25, 2.92), 0.2), k=0.03)                                      # broken off at one end
    a.paint(RoundBox((-0.84, -0.31, 2.95), (0.8, 0.03, 0.035)), 7)
    a.paint(RoundBox((-0.84, -0.31, 2.87), (0.8, 0.03, 0.025)), 5)
    out.append(("Architrave", a, fine(0.009, 0.018), "sandstone"))
    d = Field("Fallen")
    for k, (x, y, ang) in enumerate(((0.9, -1.05, 0.2), (1.55, -1.25, 0.6), (-0.4, -1.15, -0.3))):
        R = rot_from_axes(z_axis=(math.cos(ang), math.sin(ang), 0.05))
        d.add(Cylinder((x, y, 0.2), 0.235, 0.4, rr=0.025, R=R, **wob(5.0, 0.006, seed + 30 + k)))
    d.add(RoundBox((-1.35, -1.0, 0.16), (0.42, 0.24, 0.17), 0.03, R=rot_from_axes(x_axis=(math.cos(0.5), math.sin(0.5), 0.1)),
                   **wob(4.0, 0.008, seed + 40)))
    ground_cut(d)
    out.append(("Fallen", d, fine(0.009, 0.018), "sandstone"))
    return mound(out, 2.4, 1.8, 0.14, seed)


def obelisk(seed=0, h=3.3):
    """A red granite obelisk on a stepped limestone plinth: four tapering faces carved with columns of signs, a gilded
    pyramidion at the top."""
    rng = np.random.default_rng(seed)
    out = []
    pl = Field("Plinth")
    pl.add(RoundBox((0, 0, 0.1), (0.62, 0.62, 0.12), 0.02, **wob(4.0, 0.005, seed)))
    pl.add(RoundBox((0, 0, 0.29), (0.44, 0.44, 0.08), 0.015), k=0.005)
    ground_cut(pl)
    out.append(("Plinth", pl, fine(0.008, 0.016), "ashlar"))
    z0, b0, b1 = 0.36, 0.2, 0.13
    bat = (b0 - b1) / (h - z0)
    s = Field("Shaft")
    s.add(convex([((0, 0, h), (0, 0, 1)), ((0, 0, z0 - 0.02), (0, 0, -1)), ((b0, 0, z0), (1, 0, bat)), ((-b0, 0, z0), (-1, 0, bat)),
                  ((0, b0, z0), (0, 1, bat)), ((0, -b0, z0), (0, -1, bat))], (-0.3, -0.3, 0.2), (0.3, 0.3, h + 0.1)))
    for fa in range(4):
        th = fa * math.pi / 2
        nrm, tan = v3((math.cos(th), math.sin(th), 0)), v3((-math.sin(th), math.cos(th), 0))
        R = rot_from_axes(x_axis=nrm, y_axis=tan)
        for row in range(13):
            z = 0.62 + row * 0.18
            half = b0 - bat * (z - z0)
            c = nrm * (half - 0.004) + v3((0, 0, z))
            kind = rng.integers(0, 4)
            if kind == 0:
                s.sub(Ellipsoid(c, (0.012, 0.045, 0.03), R=R), k=0.003)
            elif kind == 1:
                s.sub(RoundBox(c, (0.012, 0.012, 0.055), 0.004, R=R), k=0.003)
                s.sub(RoundBox(c + v3((0, 0, 0.04)), (0.012, 0.04, 0.012), 0.004, R=R), k=0.003)
            elif kind == 2:
                s.sub(Torus(c, 0.035, 0.009, R=rot_from_axes(z_axis=nrm)), k=0.002)
            else:
                for j in (-1, 1):
                    s.sub(RoundBox(c + tan * (0.025 * j), (0.012, 0.012, 0.045), 0.004, R=R), k=0.003)
    out.append(("Shaft", s, fine(0.007, 0.014), "granite"))
    g = Field("Gold")
    hp = 0.32
    g.add(convex([((b1, 0, h), (1, 0, b1 / hp)), ((-b1, 0, h), (-1, 0, b1 / hp)), ((0, b1, h), (0, 1, b1 / hp)), ((0, -b1, h), (0, -1, b1 / hp)),
                  ((0, 0, h - 0.01), (0, 0, -1))], (-0.2, -0.2, h - 0.05), (0.2, 0.2, h + hp + 0.05)))
    out.append(("Gold", g, fine(0.005, 0.01), "gold"))
    return mound(out, 1.0, 1.0, 0.1, seed)


def pyramid(seed=0):
    """The step pyramid on the citadel's horizon: five battered tiers of dressed stone, a steep stair with balustrades
    up the front (-Y), a shrine with a red-painted doorway on top under a gilded roof."""
    out = []
    f = Field("Tiers")
    tiers = 5
    TH = 0.9
    wx = [4.5 - k * 0.84 for k in range(tiers)]
    for k in range(tiers):
        hx, hy = wx[k], wx[k] * 0.72
        z0, z1 = k * TH - 0.02, (k + 1) * TH
        f.add(convex_w([((0, 0, z1), (0, 0, 1)), ((0, 0, z0), (0, 0, -1)), ((hx, 0, z0), (1, 0, 0.12)), ((-hx, 0, z0), (-1, 0, 0.12)),
                        ((0, hy, z0), (0, 1, 0.12)), ((0, -hy, z0), (0, -1, 0.12))],
                       (-hx - 0.2, -hy - 0.2, z0 - 0.1), (hx + 0.2, hy + 0.2, z1 + 0.1), 0.02, 1.5, seed + k))
        f.paint(RoundBox((0, 0, z1 - 0.06), (hx + 0.3, hy + 0.3, 0.05)), 5 if k % 2 == 0 else 7)       # painted bands
    H = tiers * TH
    Yb = wx[0] * 0.72 + 1.0
    Yt = wx[-1] * 0.72
    nsteps = 30
    rise = H / nsteps
    tread = (Yb - Yt) / nsteps
    hw = 0.6

    def stair(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        k = np.floor(np.clip(z, 0, H - 1e-4) / rise)
        yf = -Yb + k * tread
        return np.maximum.reduce([np.abs(x) - hw, yf - y, -z, z - H, y]).astype(F32)

    def balustrade(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        zt = (y + Yb) / (Yb - Yt) * H + 0.16
        return np.maximum.reduce([np.abs(np.abs(x) - hw - 0.09) - 0.09, z - zt, -z, -(y + Yb + 0.05), y]).astype(F32)
    f.add(Func(stair, (-hw - 0.05, -Yb - 0.05, -0.05), (hw + 0.05, 0.05, H + 0.05)))
    f.add(Func(balustrade, (-hw - 0.25, -Yb - 0.1, -0.05), (hw + 0.25, 0.05, H + 0.3)))
    ground_cut(f)
    out.append(("Tiers", f, fine(0.026, 0.05), "ashlar"))
    sh = Field("Shrine")
    sh.add(walls_box(0, 0.1, 0.62, 0.5, H - 0.02, H + 0.82, 0.04, 0.0))
    sh.add(RoundBox((0, 0.1, H + 0.86), (0.72, 0.6, 0.06), 0.015), k=0.01)                # cornice
    sh.sub(RoundBox((0, -0.42, H + 0.32), (0.18, 0.12, 0.32), 0.03))                    # door
    sh.paint(RoundBox((0, -0.44, H + 0.36), (0.3, 0.1, 0.42)), 5)
    sh.paint(RoundBox((0, 0.1, H + 0.72), (0.8, 0.7, 0.04)), 7)
    out.append(("Shrine", sh, fine(0.01, 0.02), "ashlar"))
    g = Field("Gold")
    g.add(convex([((0.6, 0.1, H + 0.9), (1, 0, 0.9)), ((-0.6, 0.1, H + 0.9), (-1, 0, 0.9)), ((0, 0.65, H + 0.9), (0, 1, 0.9)),
                  ((0, -0.45, H + 0.9), (0, -1, 0.9)), ((0, 0.1, H + 0.9), (0, 0, -1))], (-0.8, -0.7, H + 0.85), (0.8, 0.9, H + 1.6)))
    out.append(("Gold", g, fine(0.01, 0.02), "gold"))
    d = Field("Dark")
    d.add(RoundBox((0, -0.36, H + 0.32), (0.16, 0.04, 0.3), 0.03))
    out.append(("Dark", d, fine(0.01, 0.02), "dark"))
    return mound(out, 6.0, 4.6, 0.25, seed, voxel=fine(0.04, 0.07))


# ------------------------------------------------------------------------------------------------ canyon landmarks
def mine(seed=0):
    """A copper mine in a red-rock crag: a timbered adit (dark tunnel mouth facing -Y), a lamp hanging from the cap
    beam, rails running out on sleepers with a loaded cart, tailings heaped beside the entrance."""
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Crag")
    for (x, y, z, rx, ry, rz) in ((0.0, 0.9, 0.5, 1.9, 1.3, 1.6), (-1.35, 0.6, 0.2, 1.1, 1.0, 1.15), (1.4, 0.7, 0.25, 1.15, 1.05, 1.25),
                                  (0.3, 1.5, 1.1, 1.3, 1.0, 1.2), (-0.6, 1.4, 0.9, 1.0, 0.9, 1.0)):
        f.add(Ellipsoid((x, y, z), (rx, ry, rz), **wob(1.4, 0.1, seed + int(x * 10 + y))), k=0.25)
    for i in range(14):
        nrm = unit((rng.normal(), rng.normal() - 0.4, abs(rng.normal()) * 0.6 + 0.2))
        f.inter(Plane(v3((0.0, 0.9, 0.6)) + nrm * rng.uniform(1.6, 1.85), nrm), k=0.08)
    for i in range(5):                                  # ledges along the bedding
        z = 0.45 + 0.42 * i
        f.sub(Torus((0.0, 0.9, z), 2.0 - 0.25 * i, 0.06, R=rot_from_axes(z_axis=(0.03, 0.05, 1))), k=0.05)
    f.sub(RoundBox((0, -0.2, 0.62), (0.46, 1.4, 0.64), 0.12))                            # the adit
    f.add(Ellipsoid((1.55, -0.85, -0.05), (0.75, 0.55, 0.38), **wob(3.0, 0.05, seed + 3)), k=0.15)       # tailings
    ground_cut(f)
    out.append(("Crag", f, fine(0.02, 0.035), "rock"))
    t = Field("Timber")
    for sx in (-1, 1):
        t.add(RoundBox((sx * 0.5, -0.52, 0.64), (0.07, 0.07, 0.68), 0.015, **wob(6.0, 0.004, seed + sx)), label=11)
        t.add(RoundBox((sx * 0.5, -0.1, 0.64), (0.07, 0.07, 0.68), 0.015), label=11)
        t.add(RoundCone((sx * 0.5, -0.52, 1.0), (sx * 0.22, -0.52, 1.28), 0.035, 0.035), label=11)   # braces
    for y in (-0.52, -0.1):
        t.add(RoundBox((0, y, 1.36), (0.68, 0.08, 0.075), 0.015, **wob(6.0, 0.004, seed + 7)), label=10)
    for k in range(7):                                                                    # sleepers
        t.add(RoundBox((0, -0.55 - k * 0.3, 0.03), (0.42, 0.07, 0.035), 0.01, **wob(8.0, 0.003, seed + 20 + k)), label=10)
    for k in range(4):
        t.add(RoundBox((0, -0.2 + k * 0.3, 0.03), (0.42, 0.07, 0.035), 0.01), label=10)
    out.append(("Timber", t, fine(0.006, 0.012), "siege"))
    r = Field("Rails")
    for sx in (-1, 1):
        r.add(RoundBox((sx * 0.34, -1.0, 0.085), (0.022, 1.75, 0.022), 0.006))
    out.append(("Rails", r, fine(0.005, 0.01), "rail"))
    d = Field("Dark")
    d.add(RoundBox((0, 0.35, 0.62), (0.44, 0.7, 0.62), 0.1))
    out.append(("Dark", d, fine(0.02, 0.035), "dark"))
    lamp = Field("Lamp")
    lamp.add(Sphere((0.0, -0.6, 1.08), 0.06))
    out.append(("Lamp", lamp, fine(0.005, 0.01), "glow_fire"))
    hk = Field("Hook")
    hk.add(RoundCone((0.0, -0.6, 1.28), (0.0, -0.6, 1.13), 0.008, 0.008))
    hk.add(Torus((0.0, -0.6, 1.12), 0.045, 0.01), k=0.004)
    out.append(("Hook", hk, fine(0.004, 0.008), "rail"))
    place_parts(out, cart(seed + 1), (0, -1.55, 0.105), rot_from_axes(x_axis=(0, 1, 0), y_axis=(-1, 0, 0)))     # (wheels on the rails)
    place_parts(out, ore(0.55, 0.35, seed + 2, glow=True), (1.75, -1.15, 0.12))
    return mound(out, 2.8, 2.2, 0.2, seed, c=(0, 0.4))


def smelter(seed=0):
    """A copper smelter: a clay shaft furnace glowing at its top and its tapping arch, two goatskin bellows feeding it
    through clay pipes, a stack of oxhide copper ingots on a flat stone, charcoal and ore heaped ready."""
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Furnace")
    f.add(RoundCone((0, 0, 0.0), (0, 0, 1.25), 0.58, 0.32, **wob(4.0, 0.012, seed)))
    f.sub(Cylinder((0, 0, 1.3), 0.21, 0.5))
    f.sub(RoundBox((0, -0.5, 0.2), (0.15, 0.3, 0.2), 0.06))
    for z in (0.42, 0.86):
        f.add(Torus((0, 0, z), 0.58 - 0.26 * z / 1.25 + 0.02, 0.03), k=0.02)
        f.paint(Torus((0, 0, z), 0.58 - 0.26 * z / 1.25 + 0.02, 0.05), 5)
    for sx in (-1, 1):                                                                    # clay pipes (tuyeres)
        f.add(RoundCone((sx * 0.85, -0.3, 0.32), (sx * 0.42, -0.1, 0.26), 0.045, 0.05), k=0.03)
    ground_cut(f)
    out.append(("Furnace", f, fine(0.008, 0.016), "terracotta"))
    g = Field("Fire")
    g.add(Cylinder((0, 0, 1.12), 0.2, 0.1))
    g.add(Ellipsoid((0, -0.38, 0.12), (0.13, 0.2, 0.12)))
    g.add(Ellipsoid((0, -0.78, 0.0), (0.2, 0.17, 0.04), **wob(10.0, 0.01, seed + 2)))   # a puddle of slag run out
    out.append(("Fire", g, fine(0.006, 0.012), "glow_fire"))
    b = Field("Bellows")
    for sx in (-1, 1):
        c = v3((sx * 1.08, -0.35, 0.16))
        b.add(Ellipsoid(c, (0.26, 0.2, 0.15), **wob(6.0, 0.012, seed + 5 + sx)))
        b.add(RoundCone(c + v3((-sx * 0.2, 0.02, 0)), c + v3((-sx * 0.3, 0.03, 0.06)), 0.05, 0.04), k=0.03)
        for o in (-0.1, 0.1):
            b.add(Cylinder(c + v3((0, o, 0.14)), 0.015, 0.4, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.01)
    ground_cut(b)
    out.append(("Bellows", b, fine(0.007, 0.014), "hide"))
    s = Field("Stone")
    s.add(RoundBox((0.95, -0.85, 0.06), (0.32, 0.26, 0.07), 0.04, **wob(4.0, 0.01, seed + 9)))
    ground_cut(s)
    out.append(("Stone", s, fine(0.008, 0.016), "rock"))
    ing = Field("Ingots")
    for k in range(5):
        ang = 0.3 + (k % 2) * 1.4
        c = v3((0.95, -0.85, 0.15 + 0.035 * k))
        ax, ay = v3((math.cos(ang), math.sin(ang), 0)), v3((-math.sin(ang), math.cos(ang), 0))
        ing.add(RoundBox(c, (0.17, 0.1, 0.016), 0.01, R=rot_from_axes(x_axis=ax, y_axis=ay)))
        for sx in (-1, 1):
            for sy in (-1, 1):
                ing.add(Ellipsoid(c + ax * (sx * 0.16) + ay * (sy * 0.095), (0.05, 0.035, 0.016), R=rot_from_axes(x_axis=ax, y_axis=ay)), k=0.01)
    out.append(("Ingots", ing, fine(0.005, 0.01), "copper"))
    ch = Field("Charcoal")
    ch.add(Ellipsoid((-1.0, -0.85, 0.0), (0.38, 0.3, 0.2), **wob(14.0, 0.02, seed + 11)))
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi)
        ch.add(RoundBox((-1.0 + 0.3 * math.cos(a) * rng.uniform(0.3, 1), -0.85 + 0.24 * math.sin(a) * rng.uniform(0.3, 1), rng.uniform(0.05, 0.16)),
                        (0.05, 0.035, 0.03), 0.01, R=rot_from_axes(x_axis=(math.cos(a), math.sin(a), 0.3))), k=0.01)
    ground_cut(ch)
    out.append(("Charcoal", ch, fine(0.006, 0.012), "charcoal"))
    place_parts(out, ore(0.7, 0.4, seed + 3, glow=False), (0.95, 0.65, 0.0))
    return mound(out, 1.9, 1.5, 0.16, seed)


# ------------------------------------------------------------------------------------------------ the Bronze city
def merlon(f, c, R=None, s=1.0):
    """A stepped (Mesopotamian) merlon: a broad block with a narrower one on top."""
    c = v3(c)
    f.add(RoundBox(c + v3((0, 0, 0.07 * s)), v3((0.13, 0.13, 0.07)) * s, 0.012 * s, R=R), k=0.01)
    f.add(RoundBox(c + v3((0, 0, 0.19 * s)), v3((0.075, 0.075, 0.06)) * s, 0.01 * s, R=R), k=0.008)


def small_house(f, d, cx, cy, hx, hy, hh, seed, door=(0, -1)):
    """A flat-roofed town house: battered mud-brick walls, a parapet, a door (dark inset) on side `door`."""
    f.add(walls_box(cx, cy, hx, hy, -0.05, hh + 0.1, 0.04, 0.006, seed))
    f.sub(RoundBox((cx, cy, hh + 0.3), (hx - 0.12, hy - 0.12, 0.3), 0.02))
    dx, dy = door
    dc = v3((cx + dx * hx, cy + dy * hy, 0.3))
    half = (0.13, 0.16, 0.3) if dx == 0 else (0.16, 0.13, 0.3)
    f.sub(RoundBox(dc, half, 0.03))
    d.add(RoundBox(dc - v3((dx, dy, 0)) * 0.1, (0.12 if dx == 0 else 0.03, 0.03 if dx == 0 else 0.12, 0.29), 0.02))
    f.paint(RoundBox((cx, cy, hh - 0.05), (hx + 0.2, hy + 0.2, 0.03)), 7)


def city(seed=0):
    """The Bronze Age city at the end of the road (the gate faces -X, where the road comes in): two gate towers with
    stepped merlons, bands of blue glazed brick and glazed rosettes, arrow slits and red banners; a gateway with bronze-
    banded cedar doors under a glazed lintel; walls with buttresses running off both ways; a stepped ziggurat with a gilded
    shrine and three town houses behind; bronze braziers before the towers (game.gd lights fires in them)."""
    rng = np.random.default_rng(seed)
    out = []
    d = Field("Dark")
    T = Field("Towers")
    for sy in (-1, 1):
        cy = sy * 1.55
        T.add(walls_box(0.7, cy, 0.66, 0.66, -0.05, 2.3, 0.035, 0.006, seed + sy))
        for (mx, my) in ((-0.48, -0.48), (0, -0.48), (0.48, -0.48), (-0.48, 0), (0.48, 0), (-0.48, 0.48), (0, 0.48), (0.48, 0.48)):
            merlon(T, (0.7 + mx, cy + my, 2.28))
        T.sub(RoundBox((0.7, cy, 2.5), (0.4, 0.4, 0.28), 0.02))                         # the fighting platform
        T.paint(RoundBox((0.7, cy, 1.86), (0.8, 0.8, 0.07)), 5)                         # glazed band
        xf = 0.04 + 0.035 * 1.56                                                         # (the battered face at that height)
        for k in range(3):                                                               # glazed rosettes below it
            ry = cy + (k - 1) * 0.36
            T.add(Cylinder((xf - 0.004, ry, 1.56), 0.075, 0.03, rr=0.01, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.006)
            T.paint(Cylinder((xf - 0.02, ry, 1.56), 0.085, 0.06, R=rot_from_axes(z_axis=(1, 0, 0))), 6)
        for z in (0.95, 1.3):                                                            # arrow slits
            T.sub(RoundBox((0.04, cy + sy * 0.3, z), (0.08, 0.025, 0.12), 0.01))
            d.add(RoundBox((0.1, cy + sy * 0.3, z), (0.02, 0.022, 0.11), 0.005))
    T.add(RoundBox((0.7, 0, 2.05), (0.5, 1.0, 0.24), 0.03, **wob(4.0, 0.005, seed + 4)), k=0.02)   # lintel over the gate
    T.paint(RoundBox((0.7, 0, 2.06), (0.6, 1.1, 0.07)), 5)
    for k in range(5):
        T.add(Cylinder((0.19, -0.6 + k * 0.3, 2.17), 0.055, 0.03, rr=0.01, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.005)
        T.paint(Cylinder((0.17, -0.6 + k * 0.3, 2.17), 0.065, 0.06, R=rot_from_axes(z_axis=(1, 0, 0))), 6)
    cut_below(T, -0.03, 0.7, 0, 1.0, 2.4)
    out.append(("Towers", T, fine(0.0095, 0.019), "mudbrick"))
    for sy in (-1, 1):
        W = Field("Wall%s" % ("S" if sy < 0 else "N"))
        W.add(walls_box(1.0, sy * 4.3, 0.45, 2.15, -0.05, 1.5, 0.04, 0.007, seed + 10 + sy))
        W.sub(RoundBox((1.12, sy * 4.3, 1.75), (0.3, 2.0, 0.3), 0.02))                # a walkway behind the parapet
        for k in range(7):
            merlon(W, (0.66, sy * (2.45 + k * 0.62), 1.47), s=0.85)
        for k in range(5):                                                              # buttresses on the outer face
            W.add(RoundBox((0.53, sy * (2.6 + k * 0.85), 0.72), (0.07, 0.16, 0.74), 0.02, **wob(5.0, 0.004, seed + 20 + k)), k=0.015)
        W.paint(RoundBox((0.55, sy * 4.3, 1.2), (0.2, 2.3, 0.04)), 5)
        cut_below(W, -0.03, 1.0, sy * 4.3, 0.8, 2.4)
        out.append((W.name, W, fine(0.0105, 0.021), "mudbrick"))
    Z = Field("Ziggurat")
    zc = v3((4.1, 2.5, 0))
    widths = [3.2, 2.5, 1.8, 1.1]
    for k, w in enumerate(widths):
        Z.add(walls_box(zc[0], zc[1], w / 2, w / 2, k * 0.55 - 0.05, (k + 1) * 0.55, 0.06, 0.008, seed + 30 + k))
        Z.paint(RoundBox((zc[0], zc[1], (k + 1) * 0.55 - 0.05), (w / 2 + 0.2, w / 2 + 0.2, 0.035)), 5 if k % 2 == 0 else 7)
    nst = 14
    for k in range(nst):                                                                # the stair up its -X face
        zt = (k + 1) * 2.2 / nst
        x0 = zc[0] - 1.6 - 0.35 + k * (1.6 + 0.35 - 0.55) / nst
        Z.add(RoundBox(((x0 + zc[0]) / 2, zc[1], zt / 2), ((zc[0] - x0) / 2, 0.3, zt / 2), 0.01), k=0.006)
    Z.add(walls_box(zc[0], zc[1], 0.42, 0.36, 2.15, 2.75, 0.03, 0.0), k=0.01)          # the shrine on top
    Z.sub(RoundBox((zc[0] - 0.42, zc[1], 2.42), (0.12, 0.13, 0.22), 0.02))
    d.add(RoundBox((zc[0] - 0.34, zc[1], 2.42), (0.03, 0.12, 0.21), 0.01))
    Z.paint(RoundBox((zc[0], zc[1], 2.68), (0.6, 0.6, 0.04)), 5)
    cut_below(Z, -0.03, zc[0], zc[1], 2.0, 2.0)
    out.append(("Ziggurat", Z, fine(0.013, 0.026), "mudbrick"))
    g = Field("Gold")
    g.add(convex([((zc[0] + 0.44, zc[1], 2.75), (1, 0, 0.8)), ((zc[0] - 0.44, zc[1], 2.75), (-1, 0, 0.8)),
                  ((zc[0], zc[1] + 0.38, 2.75), (0, 1, 0.8)), ((zc[0], zc[1] - 0.38, 2.75), (0, -1, 0.8)), ((zc[0], zc[1], 2.74), (0, 0, -1))],
                 zc + v3((-0.6, -0.6, 2.6)), zc + v3((0.6, 0.6, 3.4))))
    out.append(("Gold", g, fine(0.008, 0.016), "gold"))
    H = Field("Houses")
    small_house(H, d, 3.0, -2.2, 0.6, 0.5, 0.9, seed + 40, door=(-1, 0))
    small_house(H, d, 4.6, -1.0, 0.55, 0.5, 1.0, seed + 41, door=(0, -1))
    cut_below(H, -0.03, 3.8, -1.6, 1.6, 1.4)
    out.append(("Houses", H, fine(0.0105, 0.021), "mudbrick"))
    H2 = Field("House3")
    small_house(H2, d, 2.6, 5.2, 0.6, 0.5, 0.95, seed + 42, door=(-1, 0))
    cut_below(H2, -0.03, 2.6, 5.2, 1.0, 1.0)
    out.append(("House3", H2, fine(0.0105, 0.021), "mudbrick"))
    G = Field("Gate")                                                                   # cedar doors, bronze bands and studs
    for sy in (-1, 1):
        G.add(RoundBox((1.0, sy * 0.45, 0.9), (0.06, 0.44, 0.9), 0.015), label=11)
    for z in (0.35, 0.9, 1.45):
        G.add(RoundBox((0.95, 0, z), (0.02, 0.88, 0.05), 0.008), k=0.004, label=6)
        for k in range(9):
            G.add(Sphere((0.93, -0.8 + k * 0.2, z), 0.02), k=0.004, label=6)
    for sy in (-1, 1):
        G.add(Torus((0.92, sy * 0.12, 0.95), 0.07, 0.014, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.004, label=6)   # ring pulls
    for sy in (-1, 1):                                                                  # banner poles on brackets
        G.add(Cylinder((-0.05, sy * 1.55, 1.98), 0.025, 0.74, R=rot_from_axes(z_axis=(0, 1, 0))), label=10)
        for o in (-0.3, 0.3):
            G.add(RoundCone((0.14, sy * 1.55 + o, 1.98), (-0.06, sy * 1.55 + o, 1.98), 0.02, 0.016), k=0.008, label=6)
    out.append(("Gate", G, fine(0.006, 0.012), "siege"))
    B = Field("Banners")
    for sy in (-1, 1):
        def banner_fn(P, cy=sy * 1.55):
            x, y, z = P[:, 0], P[:, 1] - cy, P[:, 2]
            wave = 0.03 * np.sin(z * 7.0 + y * 3.0)
            half = np.where(z < 1.32, 0.3 - (1.32 - z) * 1.5, 0.3)                       # narrowing to a point at the foot
            return np.maximum.reduce([np.abs(x - (-0.06 + wave)) - 0.016, np.abs(y) - half, z - 1.96, 1.12 - z]).astype(F32)
        B.add(Func(banner_fn, (-0.2, sy * 1.55 - 0.4, 1.0), (0.1, sy * 1.55 + 0.4, 2.0)))
        B.paint(RoundBox((-0.06, sy * 1.55, 1.9), (0.1, 0.4, 0.04)), 5)
        B.paint(Cylinder((-0.07, sy * 1.55, 1.6), 0.11, 0.1, R=rot_from_axes(z_axis=(1, 0, 0))), 6)
    out.append(("Banners", B, fine(0.006, 0.012), "wool"))
    Br = Field("Braziers")
    for sy in (-1, 1):
        c = v3((-0.15, sy * 1.55, 0))
        Br.add(Ellipsoid(c + v3((0, 0, 0.58)), (0.2, 0.2, 0.1)))
        Br.sub(Ellipsoid(c + v3((0, 0, 0.64)), (0.16, 0.16, 0.08)))
        Br.add(Torus(c + v3((0, 0, 0.63)), 0.19, 0.018), k=0.01)
        for k in range(3):
            a = 2 * math.pi * k / 3
            Br.add(RoundCone(c + v3((0.2 * math.cos(a), 0.2 * math.sin(a), 0.0)), c + v3((0.08 * math.cos(a), 0.08 * math.sin(a), 0.52)), 0.022, 0.018), k=0.02)
    out.append(("Braziers", Br, fine(0.005, 0.01), "bronze"))
    cg = Field("Coals")
    for sy in (-1, 1):
        cg.add(Ellipsoid((-0.15, sy * 1.55, 0.6), (0.14, 0.14, 0.05), **wob(20.0, 0.008, seed + sy)))
    out.append(("Coals", cg, fine(0.005, 0.01), "glow_fire"))
    pv = Field("Plaza")                                                                 # paving through the gate
    pv.add(RoundBox((0.75, 0, 0.0), (0.9, 0.95, 0.035), 0.01, **wob(6.0, 0.003, seed + 50)))
    pv.add(RoundBox((2.2, 0.0, 0.0), (0.7, 1.4, 0.035), 0.01, **wob(6.0, 0.003, seed + 51)))
    cut_below(pv, -0.02, 1.4, 0, 1.8, 1.6)
    out.append(("Plaza", pv, fine(0.012, 0.024), "ashlar"))
    out.append(("Dark", d, fine(0.006, 0.012), "dark"))
    return out


# ------------------------------------------------------------------------------------------------ the kits
# prop name -> (builder, game-mesh triangle budget), as decor_props.KITS. Tuft (and Flowers on the delta) are direct
# geometry (decor_build).
def KITS(theme):
    if theme == "delta":
        return {
            "Palm_A": (lambda: palm(3.0, 0.24, 1, 15), 2200), "Palm_B": (lambda: palm(3.6, 0.36, 2, 17), 2500),
            "Palm_C": (lambda: palm(2.2, 0.12, 3, 11, dates=False, young=True), 1600),
            "Papyrus": (lambda: papyrus(4), 1300), "Reeds": (lambda: reeds(5), 800),
            "Bush_A": (lambda: bush(1.0, 0.36, 6), 700), "Bush_B": (lambda: bush(0.7, 0.3, 7, berries=True), 500),
            "Rock_A": (lambda: rock(1.4, 0.42, 8, "delta"), 500), "Rock_B": (lambda: rock(0.9, 0.28, 9, "delta", 1), 350),
            "House": (lambda: house(10), 4200), "Granary": (lambda: granary(11), 2600),
            "Shaduf": (lambda: shaduf(12), 1800), "Boat": (lambda: boat(13), 1500),
        }
    if theme == "desert":
        return {
            "Palm_A": (lambda: palm(3.0, 0.26, 21, 14), 2200), "Palm_B": (lambda: palm(3.4, 0.4, 22, 16), 2400),
            "Acacia_A": (lambda: acacia(2.3, 2.9, 23), 1500), "Acacia_B": (lambda: acacia(1.8, 2.3, 24), 1200),
            "Scrub_A": (lambda: scrub(0.8, 0.4, 25), 600), "Scrub_B": (lambda: scrub(0.55, 0.3, 26), 450),
            "Dune_A": (lambda: dune(2.4, 0.5, 27), 600), "Dune_B": (lambda: dune(1.7, 0.36, 28), 450),
            "Rock_A": (lambda: sandrock(1.6, 0.6, 29), 600), "Rock_B": (lambda: sandrock(1.1, 0.4, 30, 1), 400),
            "Rock_C": (lambda: sandrock(2.2, 0.8, 31, 3), 800),
            "Column_A": (lambda: column(1.0, 0.26, 32, broken=True), 900), "Column_B": (lambda: column(2.1, 0.26, 33, broken=False, capital=True), 1300),
            "Column_C": (lambda: column(0.5, 0.27, 34, broken=True, glyphs=False), 600), "Blocks": (lambda: blocks(35), 900),
            "Ruin": (lambda: ruin(36), 5200), "Obelisk": (lambda: obelisk(37), 1400), "Pyramid": (lambda: pyramid(38), 5000),
        }
    if theme == "canyon":
        return {
            "Mesa_A": (lambda: mesa(2.4, 1.1, 41), 1500), "Mesa_B": (lambda: mesa(1.6, 0.8, 42, 4), 1100),
            "Mesa_C": (lambda: mesa(3.1, 1.3, 43, 6), 1800), "Pillar": (lambda: mesa(3.0, 0.9, 45, 6), 1500),
            "Hoodoo": (lambda: hoodoo(2.6, 0.42, 44), 900),
            "Rock_A": (lambda: rock(1.6, 0.5, 46, "canyon"), 600), "Rock_B": (lambda: rock(1.0, 0.32, 47, "canyon", 1), 400),
            "Rock_C": (lambda: rock(2.2, 0.7, 48, "canyon", 3), 800),
            "Scrub_A": (lambda: scrub(0.7, 0.36, 49), 600), "Dead_A": (lambda: dead_tree(1.3, 50, "canyon"), 700),
            "Ore_A": (lambda: ore(0.9, 0.55, 51), 900), "Ore_B": (lambda: ore(0.6, 0.4, 52), 600),
            "Cart": (lambda: cart(53), 1200), "Timbers": (lambda: timbers(54), 600),
            "Mine": (lambda: mine(55), 6000), "Smelter": (lambda: smelter(56), 3600),
        }
    if theme == "city":
        return {"City": (lambda: city(61), 14000)}
    raise KeyError(theme)
