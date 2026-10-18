"""Rock Slinger base: grassy mound, chiselled rock pedestal with steps, mammoth-tusk arch, ammo basket,
torch, pebbles (distance fields) + grass blades and flowers (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp

TOP_Z = 0.9             # pedestal top = where the caveman's feet stand
STAND = v3((0.0, 0.06, TOP_Z))
GROUND_R = 1.42
GROUND_TOP = 0.2


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.035) * np.sin(a * 5 + 0.7) + F(0.02) * np.sin(a * 11 + 2.0) + F(0.02) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.06) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.09), 0), np.maximum(dz + F(0.09), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.09), dz + F(0.09)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.09)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.4),
                disp=lambda P: F(0.008) * NOISE(P * F(7)) + F(0.004) * NOISE(P * F(23)), disp_amp=0.014), 0.0)
    return fd


def rocks_field():
    fd = Field("Rocks")
    # pedestal: a big chiselled block with a flat-ish top, two buttress rocks, a broken slab behind
    ped = Stone((0.0, 0.07, 0.44), 0.74, seed=21, cuts=15, squash=(1.0, 0.88, 0.8), soft=0.035, depth=(0.82, 0.97), noise=0.012,
                R=euler(0.05, -0.03, 0.4))
    fd.add(Inter(ped, Plane((0, 0, TOP_Z - 0.005), (0.03, -0.02, 1.0)), 0.03), 0.0)
    fd.add(Inter(Stone((0.5, 0.36, 0.36), 0.46, seed=5, cuts=11, squash=(1.0, 0.9, 0.9), soft=0.04, noise=0.015),
                 Plane((0, 0, TOP_Z - 0.12), (0.15, 0.1, 1.0)), 0.03), 0.012)
    fd.add(Inter(Stone((-0.52, 0.34, 0.32), 0.42, seed=8, cuts=11, squash=(1.0, 0.95, 0.95), soft=0.04, noise=0.015),
                 Plane((0, 0, TOP_Z - 0.2), (-0.2, 0.1, 1.0)), 0.03), 0.012)
    # layered rock: two wobbly ledges cut around the pedestal
    for z0, depth in ((0.38, 0.016), (0.64, 0.013)):
        def ledge(P, z0=z0, depth=depth):
            wob = F(0.02) * NOISE(P * F(3.0) + z0)
            return np.abs(P[:, 2] - F(z0) - wob) - F(depth)
        fd.sub(Inter(Func(ledge, (-1.2, -1.2, z0 - 0.1), (1.2, 1.2, z0 + 0.1)),
                     Func(lambda P: F(0.62) - np.sqrt(P[:, 0] ** 2 + ((P[:, 1] - F(0.07)) / F(0.88)) ** 2), (-1.2, -1.2, z0 - 0.1), (1.2, 1.2, z0 + 0.1)), 0.01), 0.012)
    # steps up the front right
    for i, (c, r, s) in enumerate((((0.34, -0.62, 0.28), 0.26, 31), ((0.62, -0.88, 0.2), 0.2, 33))):
        st = Stone(c, r, seed=s, cuts=10, squash=(1.0, 0.9, 0.45), soft=0.06, noise=0.015, R=euler(0.04, 0.02, 0.5 + i))
        fd.add(Inter(st, Plane((0, 0, c[2] + r * 0.32), (0.0, 0.05, 1.0)), 0.03), 0.015)
    # boulders around the foot of the pedestal and at the rim
    for i, (c, r, s) in enumerate((((-0.74, -0.2, 0.22), 0.19, 41), ((0.86, 0.02, 0.22), 0.17, 43), ((-0.2, 0.74, 0.22), 0.22, 45),
                                    ((1.12, -0.42, 0.21), 0.11, 47), ((-1.05, 0.78, 0.22), 0.14, 49), ((0.28, 1.08, 0.2), 0.12, 51))):
        fd.add(Stone(c, r, seed=s, cuts=10, squash=(1.0, 0.95, 0.75), soft=0.06, noise=0.02), 0.03)
    # a few cracks chiselled into the pedestal face
    rs = np.random.RandomState(4)
    for i in range(4):
        a0 = rs.uniform(-2.4, -0.6)
        p0 = v3((0.0, 0.08, 0.0)) + v3((math.cos(a0) * 0.62, math.sin(a0) * 0.52, rs.uniform(0.35, 0.75)))
        pts = [p0]
        for j in range(4):
            pts.append(pts[-1] + v3((rs.uniform(-0.05, 0.05), 0, -0.06 - rs.uniform(0, 0.04))))
        fd.sub(Chain(pts, [0.012, 0.01, 0.008, 0.006, 0.003], k=0.004), 0.008)
    return fd


def tusk_curve(side):
    p0 = v3((side * 1.0, 0.64, 0.1))
    p1 = v3((side * 1.32, 0.82, 2.3))
    p2 = v3((side * 0.3, 0.98, 2.88))
    return p0, p1, p2


def bez(p0, p1, p2, t):
    return p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t


def tusks_field():
    fd = Field("Tusks")
    for side in (-1, 1):
        p0, p1, p2 = tusk_curve(side)
        pts = [bez(p0, p1, p2, t) for t in np.linspace(0, 1, 16)]
        rad = [0.175 * (1 - t) ** 0.85 + 0.015 for t in np.linspace(0, 1, 16)]
        fd.add(Chain(pts, rad, k=0.02, disp=lambda P: F(0.003) * NOISE(P * np.array([40, 40, 8], F)), disp_amp=0.004), 0.0)
    return fd


def wraps_field():
    fd = Field("BaseLeather")
    for side in (-1, 1):
        p0, p1, p2 = tusk_curve(side)
        for t, w in ((0.1, 0.05), (0.17, 0.035)):
            c = bez(p0, p1, p2, t)
            tg = norm(bez(p0, p1, p2, t + 0.01) - bez(p0, p1, p2, t - 0.01))
            r = 0.175 * (1 - t) ** 0.85 + 0.015
            fd.add(Torus(c, r + 0.004, w * 0.42, R=rot_from_axes(z_axis=tg)), 0.0)
    # torch head wrap
    fd.add(Ellipsoid(TORCH_TOP + v3((0, 0, -0.02)), (0.062, 0.062, 0.1), disp=lambda P: F(0.004) * NOISE(P * F(40)), disp_amp=0.005), 0.0)
    return fd


BASKET_C = v3((0.86, -0.62, GROUND_TOP + 0.02))


def basket_field():
    fd = Field("Basket")
    c = BASKET_C
    body = RoundCone(c + v3((0, 0, 0.02)), c + v3((0, 0, 0.21)), 0.17, 0.215)
    def weave(P):
        q = P - c.astype(F)
        a = np.arctan2(q[:, 1], q[:, 0])
        return F(0.006) * np.sin(a * 22) * np.sin(q[:, 2] * F(110)) + F(0.004) * np.sin(q[:, 2] * F(220))
    fd.add(Inter(Shell(body, 0.0, 0.03, pad=0.03, disp=weave, disp_amp=0.01), Plane(c + v3((0, 0, 0.24)), (0, 0, 1)), 0.01), 0.0)
    fd.add(Torus(c + v3((0, 0, 0.235)), 0.215, 0.022, disp=lambda P: F(0.004) * np.sin(np.arctan2(P[:, 1] - F(c[1]), P[:, 0] - F(c[0])) * F(30)), disp_amp=0.005), 0.01)
    fd.add(Cylinder(c + v3((0, 0, 0.025)), 0.17, 0.05, rr=0.02), 0.01)
    return fd


def ammo_field():
    fd = Field("AmmoStones")
    c = BASKET_C
    rs = np.random.RandomState(9)
    for i in range(8):
        a = i * 2.39996
        rr = 0.11 * math.sqrt((i + 0.5) / 8)
        p = c + v3((math.cos(a) * rr, math.sin(a) * rr, 0.24 + 0.03 * (i == 0)))
        fd.add(Stone(p, rs.uniform(0.058, 0.07), seed=60 + i, noise=0.05, squash=(1, 1, 0.85)), 0.004)
    # a little pile by the caveman's left foot
    for i, (dx, dy, dz, r) in enumerate(((0.36, -0.12, 0.05, 0.065), (0.43, -0.03, 0.05, 0.06), (0.4, -0.08, 0.13, 0.058))):
        fd.add(Stone(STAND + v3((dx, dy, dz)), r, seed=80 + i, noise=0.05, squash=(1, 1, 0.85)), 0.004)
    return fd


TORCH_BASE = v3((-0.95, -0.52, GROUND_TOP - 0.05))
TORCH_TOP = v3((-1.02, -0.58, 1.3))


def wood_field():
    fd = Field("Wood")
    fd.add(Chain([TORCH_BASE, lerp(TORCH_BASE, TORCH_TOP, 0.5) + v3((0.01, 0, 0)), TORCH_TOP], [0.045, 0.04, 0.036], k=0.01,
                 disp=lambda P: F(0.004) * NOISE(P * np.array([45, 45, 6], F)), disp_amp=0.005), 0.0)
    # stake wedges at the base
    for a in (0.3, 2.4, 4.4):
        d = v3((math.cos(a), math.sin(a), 0))
        fd.add(Stone(TORCH_BASE + d * 0.08 + v3((0, 0, 0.25)), 0.06, seed=int(a * 10), squash=(0.7, 0.7, 1.0), noise=0.05), 0.01)
    return fd


def flame_field():
    fd = Field("Flame")
    c = TORCH_TOP + v3((0, 0, 0.1))
    fd.add(Ellipsoid(c, (0.085, 0.085, 0.12)), 0.0)
    fd.add(RoundCone(c, c + v3((0.01, 0.0, 0.26)), 0.075, 0.005), 0.05)
    for a in (0.0, 2.1, 4.2):
        d = v3((math.cos(a), math.sin(a), 0))
        fd.add(RoundCone(c + d * 0.045, c + d * 0.06 + v3((0, 0, 0.18)), 0.042, 0.003), 0.035)
    return fd


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(13)
    n = 0
    while n < 16:
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.75, 1.32)
        p = v3((math.cos(a) * r, math.sin(a) * r, GROUND_TOP + 0.03))
        if np.linalg.norm(p[:2] - BASKET_C[:2]) < 0.32 or np.linalg.norm(p[:2] - TORCH_BASE[:2]) < 0.2:
            continue
        fd.add(Stone(p, rs.uniform(0.03, 0.055), seed=100 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


# ---------------------------------------------------------------------------------------- direct geometry
def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.06 * max(0.0, 1 - (r / GROUND_R) ** 2)


def blade_mesh(root, d, length, width, bend, segs=4, twist=0.0):
    """One grass blade: a tapered, bent, two-sided strip. Returns verts, faces, uvs(v along blade)."""
    verts, faces, uvs = [], [], []
    side = norm(np.cross(d, v3((0, 0, 1)))) if abs(d[2]) < 0.99 else v3((1, 0, 0))
    p = v3(root)
    dirv = norm(d)
    for i in range(segs + 1):
        t = i / segs
        w = width * (1 - t) ** 0.9 * 0.5 + 0.0006
        s = axis_angle(dirv, twist * t) @ side
        verts.append(p - s * w)
        verts.append(p + s * w)
        uvs.append((0.0, t))
        uvs.append((1.0, t))
        dirv = norm(dirv + v3(bend) / segs)
        p = p + dirv * length / segs
    for i in range(segs):
        a = 2 * i
        faces.append((a, a + 1, a + 3, a + 2))
    return verts, faces, uvs


def grass_geometry(seed=17):
    """Grass tufts (clusters of blades) around the mound, avoiding the rocks and basket."""
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    avoid = [((0.0, 0.08), 0.66), ((0.45, 0.32), 0.38), ((-0.5, 0.28), 0.32), (tuple(BASKET_C[:2]), 0.28),
             ((0.34, -0.62), 0.24), ((0.62, -0.88), 0.18), (tuple(TORCH_BASE[:2]), 0.14)]
    tufts = []
    tries = 0
    while len(tufts) < 44 and tries < 6000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = math.sqrt(rs.uniform(0.25, 1.0)) * (GROUND_R - 0.1)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - np.array(q)) < rr for q, rr in avoid):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.15 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(8, 14)
        big = 0.75 + 0.5 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.055)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.15, 0.45) + v3((0, 0, 1)))
            L = rs.uniform(0.14, 0.26) * big
            v, f, uv = blade_mesh(root, d, L, rs.uniform(0.03, 0.044), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                  twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=23):
    """Small five-petal flowers on stems (white/yellow/violet)."""
    rs = np.random.RandomState(seed)
    out = []          # (verts, faces, kind) kind: 0 stem, 1 petal, 2 centre
    spots = []
    tries = 0
    while len(spots) < 9 and tries < 2000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.85, 1.3)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if np.linalg.norm(c[:2] - BASKET_C[:2]) < 0.35 or np.linalg.norm(c[:2] - TORCH_BASE[:2]) < 0.25:
            continue
        if any(np.linalg.norm(c[:2] - s[0][:2]) < 0.2 for s in spots):
            continue
        spots.append((c, rs.randint(0, 3)))
    for c, kind in spots:
        base = v3((c[0], c[1], ground_height(c[0], c[1]) - 0.01))
        h = rs.uniform(0.1, 0.16)
        top = base + v3((rs.uniform(-0.02, 0.02), rs.uniform(-0.02, 0.02), h))
        sv, sf, _ = blade_mesh(base, top - base, h, 0.012, (0, 0, 0), segs=2)
        out.append((sv, sf, 0, kind))
        n = 5
        pr = 0.035
        tilt = norm(v3((rs.uniform(-0.3, 0.3), rs.uniform(-0.5, -0.1), 1.0)))
        R = rot_from_axes(z_axis=tilt)
        pv, pf = [], []
        for k in range(n):
            a = 2 * math.pi * k / n
            dirk = R @ v3((math.cos(a), math.sin(a), 0.12))
            sidek = R @ v3((-math.sin(a), math.cos(a), 0))
            b0 = len(pv)
            pv += [top + tilt * 0.004, top + dirk * pr * 0.55 + sidek * pr * 0.42, top + dirk * pr, top + dirk * pr * 0.55 - sidek * pr * 0.42]
            pf.append((b0, b0 + 1, b0 + 2, b0 + 3))
        out.append((pv, pf, 1, kind))
        cv, cf = [], []
        for k in range(6):
            a = 2 * math.pi * k / 6
            cv.append(top + R @ v3((math.cos(a) * 0.012, math.sin(a) * 0.012, 0.008)))
        cv.append(top + R @ v3((0, 0, 0.016)))
        cf = [(k, (k + 1) % 6, 6) for k in range(6)]
        out.append((cv, cf, 2, kind))
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Rocks", rocks_field(), 0.006), ("Tusks", tusks_field(), 0.004),
            ("BaseLeather", wraps_field(), 0.003), ("Basket", basket_field(), 0.003), ("AmmoStones", ammo_field(), 0.004),
            ("Wood", wood_field(), 0.003), ("Flame", flame_field(), 0.004), ("Pebbles", pebbles_field(), 0.004)]


LOW_TARGETS = {"Ground": 1500, "Rocks": 3800, "Tusks": 1300, "BaseLeather": 420, "Basket": 900, "AmmoStones": 620,
               "Wood": 300, "Pebbles": 420, "Flame": 160}
FLAME_PIVOT = TORCH_TOP + np.array((0, 0, 0.02))


def is_grass_face(c, n):
    import math
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and 0.1 < c.z < 0.32 and r < GROUND_R + 0.05 and not (r < 0.95 and c.z > 0.28)
