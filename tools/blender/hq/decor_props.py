"""HQ Stone Age map props, sculpted as distance fields. Every prop function returns its parts:
[(part name, Field, voxel, material key)], built at the origin (Z up, ground at z = 0), and the kit lists which props
each theme ships (KITS). Material keys are resolved per theme by decor_build.MATERIALS.

Sizes follow the v2 kit the game already places (game.gd DECOR_V2), so scatter density and landmark spots still fit.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Chain, Plane, Func, rot_from_axes, v3, NOISE, axis_angle

FINE = [False]


def vx(size):
    """Voxel for a prop about `size` units big (finer on --fine)."""
    return size * (0.0065 if FINE[0] else 0.012)


def wob(scale, amp, seed):
    off = np.array([seed * 13.13, seed * 7.71, seed * 3.37], np.float32)
    return dict(disp=lambda P: NOISE.fbm(P * scale + off, 3) * amp, disp_amp=amp * 1.2)


def convex(planes, lo, hi):
    """Convex polytope from planes [(point, outward normal)]: the max of the plane distances."""
    pl = [(v3(c).astype(np.float32), (v3(n) / np.linalg.norm(n)).astype(np.float32)) for c, n in planes]
    def fn(P):
        d = None
        for c, n in pl:
            x = (P - c) @ n
            d = x if d is None else np.maximum(d, x)
        return d
    return Func(fn, lo, hi)


def crystal(base, axis, r, h, tip=0.35, twist=0.0):
    """Hexagonal crystal standing on `base` along `axis`: six side faces and a six-faced point."""
    ax = v3(axis) / np.linalg.norm(axis)
    R = rot_from_axes(z_axis=ax)
    base = v3(base)
    planes = []
    for i in range(6):
        a = twist + i * math.pi / 3
        n = R @ v3((math.cos(a), math.sin(a), 0.0))
        planes.append((base + n * r, n))
        nt = R @ v3((math.cos(a) * 1.0, math.sin(a) * 1.0, tip / max(r, 1e-3) * 0.9))
        nt = nt / np.linalg.norm(nt)
        apex = base + ax * h
        planes.append((apex, nt))
    planes.append((base - ax * 0.05, -ax))
    e = max(r, h) + 0.05
    return convex(planes, base - e, base + e)


# ------------------------------------------------------------------------------------------------ trees & plants
def pine(h=2.8, tiers=4, r0=0.95, seed=0, theme="meadow"):
    rng = np.random.default_rng(seed)
    s = h / 2.8
    out = []
    f = Field("Trunk")
    f.add(RoundCone((0, 0, -0.1), (0, 0, h * 0.86), 0.12 * s, 0.035 * s, **wob(3.0, 0.012 * s, seed)))
    for i in range(5):
        a = i * 2 * math.pi / 5 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((0, 0, 0.16 * s), (0.3 * s * math.cos(a), 0.3 * s * math.sin(a), -0.04), 0.07 * s, 0.025 * s), k=0.07 * s)
    out.append(("Trunk", f, vx(h) * 0.7, "bark"))
    f = Field("Needles")
    for t in range(tiers):
        u = t / max(tiers - 1, 1)
        zb = h * (0.22 + 0.58 * u)
        R = r0 * (1.0 - 0.7 * u) * rng.uniform(0.93, 1.07)
        ht = h * 0.34 * (1.0 - 0.3 * u)
        zt = zb + ht
        f.add(RoundCone((0, 0, zb + 0.08 * s), (0, 0, zt), R * 0.58, 0.05 * s, **wob(2.2 / max(R, 0.3), 0.05 * R + 0.02, seed * 10 + t)), k=0.12 * s)
        nl = max(6, 10 - t)
        for i in range(nl):
            a = 2 * math.pi * i / nl + rng.uniform(-0.18, 0.18) + t * 0.7
            rr = R * rng.uniform(0.9, 1.08)
            tip = (rr * math.cos(a), rr * math.sin(a), zb - 0.09 * R)
            root = (0.25 * R * math.cos(a), 0.25 * R * math.sin(a), zb + ht * 0.55)
            f.add(RoundCone(root, tip, 0.15 * R + 0.06 * s, 0.07 * R + 0.035 * s, **wob(3.0 / max(R, 0.3), 0.035 * R + 0.012, seed * 100 + t * 10 + i)), k=0.13 * R + 0.04)
    f.add(RoundCone((0, 0, h * 0.84), (0, 0, h * 1.0), 0.1 * s, 0.012), k=0.07 * s)
    out.append(("Needles", f, vx(h), "needles"))
    return out


def dead_tree(h=1.3, seed=0, theme="volcano"):
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Trunk")
    pts = [(0, 0, -0.05), (0.02, 0.0, h * 0.35), (-0.05, 0.03, h * 0.7), (0.03, -0.02, h * 0.95)]
    f.add(Chain(pts, [0.11, 0.085, 0.06, 0.03], k=0.03, **wob(4.0, 0.012, seed)))
    for i in range(4):
        a = 2 * math.pi * i / 4 + rng.uniform(-0.4, 0.4)
        f.add(RoundCone((0, 0, 0.1), (0.24 * math.cos(a), 0.24 * math.sin(a), -0.03), 0.06, 0.02), k=0.05)
    for i in range(4):
        z0 = h * rng.uniform(0.4, 0.8)
        a = rng.uniform(0, 2 * math.pi)
        L = h * rng.uniform(0.25, 0.42)
        p0 = v3((0, 0, z0))
        p1 = p0 + v3((math.cos(a) * L * 0.6, math.sin(a) * L * 0.6, L * 0.45))
        p2 = p1 + v3((math.cos(a + 0.5) * L * 0.4, math.sin(a + 0.5) * L * 0.4, L * 0.35))
        f.add(Chain([p0, p1, p2], [0.04, 0.025, 0.008], k=0.02), k=0.03)
    out.append(("Trunk", f, vx(h) * 0.6, "charred"))
    return out


def bush(w=1.0, h=0.36, seed=0, theme="meadow", berries=False):
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Leaves")
    n = 8
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        rr = w * 0.3 * rng.uniform(0.5, 1.0)
        rad = w * rng.uniform(0.2, 0.28)
        c = (rr * math.cos(a), rr * math.sin(a) * 1.15, h * 0.35)
        f.add(Ellipsoid(c, (rad, rad, rad * h / (w * 0.32)), **wob(5.0 / w, 0.03 * w, seed * 10 + i)), k=0.08 * w)
    f.add(Ellipsoid((0, 0, h * 0.5), (w * 0.3, w * 0.34, h * 0.55), **wob(5.0 / w, 0.03 * w, seed)), k=0.1 * w)
    if berries:
        for i in range(14):
            a = rng.uniform(0, 2 * math.pi)
            rr = w * rng.uniform(0.15, 0.42)
            f.paint(Sphere((rr * math.cos(a), rr * math.sin(a) * 1.1, h * rng.uniform(0.5, 0.9)), 0.045), 1)
    out.append(("Leaves", f, vx(w), "leaves_berry" if berries else "leaves"))
    return out


def rock(w=2.0, h=0.52, seed=0, theme="meadow", n_extra=2):
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Rock")
    f.add(Ellipsoid((0, 0, h * 0.25), (w * 0.46, w * 0.42, h * 0.95), **wob(2.5 / w, 0.05 * w, seed)))
    for i in range(n_extra):
        a = rng.uniform(0, 2 * math.pi)
        rr = w * 0.33
        sz = w * rng.uniform(0.18, 0.26)
        f.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a), h * 0.1), (sz, sz * 0.9, h * 0.6), **wob(3.5 / w, 0.04 * w, seed + i + 1)), k=0.06 * w)
    for i in range(7):                                     # chisel a few flat facets
        nrm = v3((rng.normal(), rng.normal(), abs(rng.normal()) + 0.6))
        nrm /= np.linalg.norm(nrm)
        ext = v3((w * 0.46 * nrm[0], w * 0.42 * nrm[1], h * 0.95 * nrm[2] + h * 0.25))
        f.inter(Plane(ext * 0.86, nrm), k=0.03 * w)
    f.inter(Plane((0, 0, -0.08), (0, 0, -1)))
    out.append(("Rock", f, vx(w) * 0.8, "rock"))
    return out


def stump(seed=0, theme="meadow"):
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Stump")
    f.add(Cylinder((0, 0, 0.06), 0.27, 0.34, rr=0.04, **wob(5.0, 0.012, seed)))
    for i in range(5):
        a = 2 * math.pi * i / 5 + rng.uniform(-0.3, 0.3)
        f.add(RoundCone((0.18 * math.cos(a), 0.18 * math.sin(a), 0.12), (0.4 * math.cos(a), 0.4 * math.sin(a), -0.02), 0.08, 0.03), k=0.06)
    f.inter(Plane((0, 0, 0.21), (0.05, 0.03, 1.0)))
    out.append(("Stump", f, vx(0.8) * 0.8, "wood_end"))
    return out


def log(seed=0, theme="meadow"):
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Log")
    f.add(Cylinder((0, 0, 0.14), 0.15, 1.42, rr=0.025, R=rot_from_axes(z_axis=(1, 0, 0)), **wob(5.0, 0.01, seed)))
    f.add(RoundCone((0.2, 0.0, 0.2), (0.32, -0.12, 0.38), 0.05, 0.03), k=0.03)         # broken branch stub
    f.inter(Plane((0, 0, -0.01), (0, 0, -1)))
    out.append(("Log", f, vx(1.4) * 0.7, "wood_end"))
    return out


def mound(w=2.2, h=0.38, seed=0):
    out = []
    f = Field("Snow")
    f.add(Ellipsoid((0, 0, 0.0), (w * 0.5, w * 0.41, h), **wob(2.0 / w, 0.06, seed)))
    f.add(Ellipsoid((w * 0.18, w * 0.05, 0.0), (w * 0.28, w * 0.24, h * 0.75), **wob(3.0 / w, 0.05, seed + 1)), k=0.15)
    f.inter(Plane((0, 0, -0.02), (0, 0, -1)))
    out.append(("Snow", f, vx(w), "snow"))
    return out


def ice_cluster(w=1.2, h=0.7, seed=0, mat="ice"):
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Crystal")
    n = 6
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.4, 0.4)
        rr = 0 if i == 0 else w * rng.uniform(0.12, 0.3)
        base = (rr * math.cos(a), rr * math.sin(a), -0.05)
        tilt = 0.0 if i == 0 else rng.uniform(0.25, 0.6)
        axis = (math.cos(a) * tilt, math.sin(a) * tilt, 1.0)
        hh = h * (1.0 if i == 0 else rng.uniform(0.45, 0.8))
        f.add(crystal(base, axis, w * (0.13 if i == 0 else rng.uniform(0.07, 0.11)), hh, twist=rng.uniform(0, 1)))
    out.append(("Crystal", f, vx(max(w, h)) * 0.6, mat))
    return out


def obsidian(w=1.7, h=1.0, seed=0):
    out = ice_cluster(w, h, seed, "obsidian")
    f = Field("Base")
    f.add(Ellipsoid((0, 0, 0.0), (w * 0.45, w * 0.42, 0.18), **wob(3.0, 0.05, seed)))
    f.inter(Plane((0, 0, -0.03), (0, 0, -1)))
    out.append(("Base", f, vx(w), "rock"))
    return out


# ------------------------------------------------------------------------------------------------ landmarks
def mammoth(seed=0, theme="meadow"):
    """A mammoth skeleton half sunk in the ground: skull with great curling tusks (+X), spine, ribs, pelvis, leg bones."""
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Bones")
    # spine and vertebrae
    sp = [v3((-1.7 + i * 0.52, 0.0, 0.95 + 0.25 * math.sin(i * 0.55))) for i in range(8)]
    f.add(Chain(sp, [0.1] * len(sp), k=0.04))
    for p in sp[1:-1]:
        f.add(RoundCone(p, p + v3((0.03, 0, 0.3)), 0.06, 0.025), k=0.03)
        f.add(Sphere(p, 0.13), k=0.04)
    # ribs: curved arcs down both sides
    for i in range(6):
        p0 = sp[1] + (sp[6] - sp[1]) * (i / 5.0)
        for side in (-1, 1):
            pts = [p0]
            for k in range(1, 6):
                t = k / 5.0
                pts.append(v3((p0[0] + 0.1 * t, side * (0.12 + 0.82 * math.sin(t * 2.2)), p0[2] - 0.98 * t + 0.05 * math.sin(t * 3))))
            f.add(Chain(pts, [0.055, 0.05, 0.045, 0.04, 0.032, 0.024], k=0.01), k=0.02)
    # skull: dome, snout, eye sockets, jaw
    sk = v3((2.25, 0.0, 0.85))
    f.add(Ellipsoid(sk, (0.55, 0.5, 0.55), **wob(3.0, 0.02, seed)), k=0.06)
    f.add(Ellipsoid(sk + v3((0.38, 0, -0.25)), (0.32, 0.36, 0.42)), k=0.12)
    for side in (-1, 1):
        f.sub(Sphere(sk + v3((0.35, side * 0.32, 0.12)), 0.13), k=0.03)
    f.add(RoundBox(sk + v3((0.15, 0, -0.55)), (0.32, 0.3, 0.08), 0.06), k=0.05)
    # tusks: thick, curling forward and up
    for side in (-1, 1):
        pts = [sk + v3((0.4, side * 0.22, -0.35)), sk + v3((0.95, side * 0.45, -0.75)), sk + v3((1.6, side * 0.58, -0.55)),
               sk + v3((1.95, side * 0.42, -0.05)), sk + v3((1.85, side * 0.12, 0.35))]
        f.add(Chain(pts, [0.17, 0.15, 0.12, 0.085, 0.04], k=0.02), k=0.04)
    # pelvis and scattered leg bones
    f.add(Ellipsoid((-1.85, 0, 0.72), (0.25, 0.55, 0.38), **wob(3.0, 0.02, seed + 2)), k=0.08)
    for a, b in (((-1.2, 0.95, 0.1), (0.15, 1.25, 0.14)), ((0.55, -1.05, 0.1), (1.75, -1.35, 0.12)), ((-1.85, -0.85, 0.1), (-0.8, -1.42, 0.1))):
        f.add(RoundCone(a, b, 0.1, 0.085), k=0.02)
        for e in (a, b):
            f.add(Sphere(e, 0.15), k=0.04)
    f.inter(Plane((0, 0, -0.04), (0, 0, -1)))
    out.append(("Bones", f, 0.012 if FINE[0] else 0.022, "bone"))
    t = Field("Mound")
    t.add(Ellipsoid((0.2, 0, -0.25), (3.2, 1.5, 0.42), **wob(1.5, 0.06, seed + 5)))
    t.inter(Plane((0, 0, -0.02), (0, 0, -1)))
    out.append(("Mound", t, 0.02 if FINE[0] else 0.035, "turf"))
    return out


def dolmen(seed=0, theme="meadow"):
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Stones")
    for x, y, hh in ((-0.8, -0.55, 1.6), (0.85, -0.5, 1.7), (0.0, 0.7, 1.65)):
        R = rot_from_axes(x_axis=(math.cos(rng.uniform(0, 1)), math.sin(rng.uniform(0, 1)), 0), z_axis=(rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 1))
        f.add(RoundBox((x, y, hh / 2 - 0.05), (0.3, 0.22, hh / 2), 0.09, R=R, **wob(2.5, 0.04, seed + int(x * 10))))
    f.add(RoundBox((0, 0, 1.82), (1.25, 0.95, 0.19), 0.12, R=rot_from_axes(x_axis=(math.cos(0.3), math.sin(0.3), 0.06), z_axis=(0.06, -0.05, 1)),
                   **wob(1.8, 0.06, seed + 7)), k=0.03)
    for i in range(5):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(1.1, 1.4)
        f.add(Ellipsoid((rr * math.cos(a), rr * math.sin(a), 0.02), (0.18, 0.15, 0.12), **wob(5.0, 0.02, seed + 20 + i)))
    f.inter(Plane((0, 0, -0.05), (0, 0, -1)))
    out.append(("Stones", f, 0.014 if FINE[0] else 0.024, "rock"))
    o = Field("Spiral")
    for k in range(3):
        o.add(Torus((-0.8, -0.79, 0.95), 0.17 - k * 0.055, 0.018, R=rot_from_axes(z_axis=(0, -1, 0))))
    out.append(("Spiral", o, 0.006 if FINE[0] else 0.012, "ochre"))
    t = Field("Mound")
    t.add(Ellipsoid((0, 0, -0.18), (1.75, 1.5, 0.3), **wob(1.8, 0.05, seed + 3)))
    t.inter(Plane((0, 0, -0.02), (0, 0, -1)))
    out.append(("Mound", t, 0.02 if FINE[0] else 0.035, "turf"))
    return out


def bone_hut(seed=0, theme="meadow"):
    """A mammoth-bone dwelling: a hide dome ringed with jawbones and arched over with tusks; door to -Y, smoke hole."""
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Hide")
    f.add(Ellipsoid((0, 0, 0.0), (1.1, 1.1, 1.05), **wob(3.0, 0.03, seed)))
    f.sub(RoundBox((0, -1.08, 0.35), (0.3, 0.3, 0.38), 0.12), k=0.05)            # doorway
    f.sub(Cylinder((0, 0, 1.05), 0.14, 0.3), k=0.04)                             # smoke hole
    f.inter(Plane((0, 0, -0.02), (0, 0, -1)))
    out.append(("Hide", f, 0.012 if FINE[0] else 0.022, "hide"))
    b = Field("Bones")
    for k in range(9):
        a = k * 2 * math.pi / 9 + 0.2
        if abs(math.sin(a) + 1) < 0.25:
            continue
        base = v3((1.15 * math.cos(a), 1.15 * math.sin(a), 0.0))
        top = v3((0.42 * math.cos(a), 0.42 * math.sin(a), 1.02))
        mid = (base + top) / 2 + v3((0.28 * math.cos(a), 0.28 * math.sin(a), 0.12))
        b.add(Chain([base, mid, top], [0.09, 0.075, 0.04], k=0.02))
    for k in range(16):
        a = k * 2 * math.pi / 16
        if abs(math.sin(a) + 1) < 0.2:
            continue
        b.add(Ellipsoid((1.16 * math.cos(a), 1.16 * math.sin(a), 0.1), (0.19, 0.11, 0.12),
                        R=rot_from_axes(x_axis=(-math.sin(a), math.cos(a), 0), z_axis=(0, 0, 1))), k=0.03)
    for side in (-1, 1):                                                         # tusk door frame
        b.add(Chain([v3((side * 0.38, -1.1, 0.0)), v3((side * 0.44, -1.2, 0.5)), v3((side * 0.2, -1.18, 0.92))], [0.08, 0.065, 0.04], k=0.02), k=0.02)
    b.add(Torus((0, 0, 1.03), 0.17, 0.05), k=0.02)
    b.inter(Plane((0, 0, -0.02), (0, 0, -1)))
    out.append(("Bones", b, 0.01 if FINE[0] else 0.02, "bone"))
    d = Field("Door")
    d.add(RoundBox((0, -0.98, 0.35), (0.28, 0.08, 0.36), 0.1))
    out.append(("Door", d, 0.012 if FINE[0] else 0.022, "dark"))
    t = Field("Mound")
    t.add(Ellipsoid((0, 0, -0.12), (1.45, 1.45, 0.22), **wob(2.0, 0.04, seed + 3)))
    t.inter(Plane((0, 0, -0.02), (0, 0, -1)))
    out.append(("Mound", t, 0.018 if FINE[0] else 0.03, "turf"))
    return out


def cave(seed=0, theme="meadow"):
    """The humans' cave at the end of the road: a crag with a deep dark mouth facing -X, a tusk arch and a horned skull over
    it, hide windbreaks on poles, ochre hand prints."""
    rng = np.random.default_rng(seed)
    out = []
    f = Field("Crags")
    for (x, y, z, r, sx, sy, sz) in ((1.0, 0.0, 0.3, 1.9, 1.0, 1.3, 0.95), (1.6, -1.6, 0.2, 1.3, 1.0, 1.0, 0.85),
                                     (1.5, 1.7, 0.2, 1.35, 1.0, 1.0, 0.9), (2.4, 0.2, 0.7, 1.4, 1.0, 1.2, 1.0), (0.6, 1.5, 0.0, 0.8, 1, 1, 0.8)):
        f.add(Ellipsoid((x, y, z), (r * sx, r * sy, r * sz), **wob(1.4, 0.12, seed + int(x * 10 + y))), k=0.25)
    for i in range(9):                                                          # chiselled facets
        nrm = v3((rng.normal(), rng.normal(), abs(rng.normal()) + 0.3))
        nrm /= np.linalg.norm(nrm)
        f.inter(Plane(v3((1.2, 0, 0.4)) + nrm * 1.85, nrm), k=0.12)
    f.sub(Ellipsoid((-0.55, 0.0, 0.55), (0.75, 0.88, 0.95)), k=0.18)            # the mouth
    f.inter(Plane((0, 0, -0.05), (0, 0, -1)))
    out.append(("Crags", f, 0.02 if FINE[0] else 0.035, "rock"))
    m = Field("Mouth")
    m.add(Ellipsoid((-0.15, 0.0, 0.55), (0.55, 0.78, 0.85)))
    out.append(("Mouth", m, 0.02 if FINE[0] else 0.035, "dark"))
    b = Field("Bones")
    for side in (-1, 1):
        pts = [v3((-0.75, side * 0.95, 0.0)), v3((-0.85, side * 0.8, 1.1)), v3((-0.85, side * 0.32, 1.66)), v3((-0.85, 0.0, 1.76))]
        b.add(Chain(pts, [0.12, 0.1, 0.075, 0.05], k=0.02), k=0.03)
    sk = v3((-0.9, 0.0, 2.0))
    b.add(Ellipsoid(sk, (0.18, 0.21, 0.15)), k=0.03)
    for side in (-1, 1):
        b.add(Chain([sk + v3((0, side * 0.12, 0.05)), sk + v3((0.04, side * 0.32, 0.22)), sk + v3((0.08, side * 0.4, 0.42))], [0.055, 0.04, 0.008], k=0.01), k=0.02)
    out.append(("Bones", b, 0.01 if FINE[0] else 0.02, "bone"))
    p = Field("Poles")
    for side in (-1, 1):
        p.add(RoundCone((-0.9, side * 0.95, 0.0), (-0.7, side * 0.75, 1.9), 0.05, 0.035))
        p.add(RoundCone((-0.95, side * 1.55, 0.0), (-0.9, side * 1.45, 1.25), 0.04, 0.03))
    out.append(("Poles", p, 0.008 if FINE[0] else 0.016, "bark"))
    w = Field("Hides")
    for side in (-1, 1):
        w.add(RoundBox((-0.95, side * 1.25, 0.62), (0.03, 0.3, 0.58), 0.02,
                       R=rot_from_axes(x_axis=(1, 0, 0.08 * side), y_axis=(0, math.cos(0.25 * side), math.sin(0.25 * side)))))
    out.append(("Hides", w, 0.008 if FINE[0] else 0.016, "hide"))
    o = Field("HandPrints")
    for (y, z) in ((-0.95, 1.2), (0.9, 1.35), (-0.55, 1.55)):
        o.add(Ellipsoid((-0.28, y, z), (0.03, 0.12, 0.14)))
    out.append(("HandPrints", o, 0.008 if FINE[0] else 0.014, "ochre"))
    t = Field("Mound")
    t.add(Ellipsoid((0.9, 0, -0.2), (3.0, 3.2, 0.4), **wob(1.4, 0.06, seed + 3)))
    t.inter(Plane((0, 0, -0.02), (0, 0, -1)))
    out.append(("Mound", t, 0.025 if FINE[0] else 0.04, "turf"))
    return out


def volcano(seed=0):
    """The volcano on the horizon: a ridged cone with a dark crater rim round a glowing lava pool, and lava rivers
    running down the valleys between the ridges on the side that faces the map (-Y)."""
    out = []
    RIM, FLOOR = 1.75, 1.05

    def height(x, y):
        r = np.sqrt(x * x + y * y)
        a = np.arctan2(y, x)
        cone = 4.7 * np.clip(1.0 - np.maximum(r, 1.6) / 7.0, 0, 1) ** 0.9
        lip = 0.22 * np.exp(-((r - RIM) / 0.3) ** 2)                       # a raised rim round the crater
        t = np.clip((r - (RIM + 0.05)) / (FLOOR - RIM - 0.05), 0, 1)
        bowl = 1.15 * t * t * (3 - 2 * t)                                    # the crater bowl
        sink = np.clip(r - 6.8, 0, None) * 0.8                              # sinking into the ground past r = 6.8
        ridge = 0.35 * np.sin(a * 7.0) * np.clip((r - 2.0) / 3.5, 0, 1)    # ridges fade out before the rim
        return cone + lip - bowl - sink + ridge

    def cone_fn(P):
        return (P[:, 2] - height(P[:, 0], P[:, 1])) * 0.6
    f = Field("Cone")
    f.add(Func(cone_fn, (-7.8, -7.8, -0.2), (7.8, 7.8, 5.2), **wob(0.5, 0.15, seed)))
    f.inter(Plane((0, 0, -0.05), (0, 0, -1)))
    out.append(("Cone", f, 0.05 if FINE[0] else 0.08, "rock"))

    def surface_z(x, y):
        """Where the (displaced) cone surface is above (x, y): bisect the field along z."""
        lo, hi = -0.3, 5.6
        for _ in range(28):
            m = 0.5 * (lo + hi)
            d = f.eval(np.array([[x, y, m]], np.float32))[0]
            lo, hi = (m, hi) if d < 0 else (lo, m)
        return 0.5 * (lo + hi)

    g = Field("Lava")
    g.add(Cylinder((0, 0, 2.86), 1.55, 0.07, rr=0.03))                      # the pool (its edge hides in the bowl wall)
    for m, length in ((-1, 4.3), (-2, 4.6), (0, 3.0), (-3, 2.6)):           # valleys: sin(7a) = -1
        a0 = (-math.pi / 2 + 2 * math.pi * m) / 7
        pts, radii = [], []
        for j in range(10):
            t = j / 9
            rr = RIM + 0.15 + length * t
            a = a0 + 0.05 * math.sin(j * 1.7 + m) + 0.03 * math.sin(j * 3.9 + 2 * m)
            x, y = rr * math.cos(a), rr * math.sin(a)
            rad = 0.15 * (1 - t) + 0.035 * t
            pts.append(v3((x, y, surface_z(x, y) - rad * 0.45)))
            radii.append(rad)
        g.add(Chain(pts, radii, k=0.04), k=0.05)
    out.append(("Lava", g, 0.03 if FINE[0] else 0.05, "glow_lava"))
    return out


# ------------------------------------------------------------------------------------------------ the time portal
PZ = 1.55            # ring centre height (game.gd _build_portal hz)
AXY = rot_from_axes(z_axis=(0, 1, 0))      # rings face along Y (the path runs through them)


def portal(seed=0):
    """The robots' time gate, in their colours: a gunmetal ring clad in twelve white armour plates, each with an orange
    band, on two white pylons with orange-and-black hazard stripes and vents, slanted coil rods, a glowing cyan inner ring
    and coils, magenta beacons. The rotating light strips are a separate prop (PortalLights)."""
    out = []
    f = Field("Frame")                                                         # gunmetal: ring, footings, rods, cups
    f.add(Torus((0, 0, PZ), 1.52, 0.17, R=AXY))
    for sgn in (-1, 1):
        f.add(RoundBox((sgn * 1.62, 0.0, 0.06), (0.44, 0.58, 0.08), 0.04), k=0.03)           # footing slab
        f.add(RoundCone((sgn * 1.72, 0.0, 0.52), (sgn * 2.0, 0.0, 1.62), 0.13, 0.09), k=0.04)   # slanted rod
        f.add(Sphere((sgn * 2.05, 0.0, 1.72), 0.19), k=0.03)                                     # beacon cup
        for k in range(4):                                                                        # bolts on the slab
            f.add(Sphere((sgn * 1.62 + (k % 2 - 0.5) * 0.66, (k // 2 - 0.5) * 0.9, 0.15), 0.045))
    f.inter(Plane((0, 0, -0.02), (0, 0, -1)))
    out.append(("Frame", f, 0.011 if FINE[0] else 0.02, "portal_metal"))
    a = Field("Plates")                                                        # white armour plates round the ring
    for k in range(12):
        ang = 2 * math.pi * k / 12
        c = v3((1.55 * math.cos(ang), 0.0, PZ + 1.55 * math.sin(ang)))
        R = rot_from_axes(x_axis=(math.cos(ang), 0, math.sin(ang)), y_axis=(0, 1, 0))
        a.add(RoundBox(c, (0.21, 0.3, 0.26), 0.06, R=R))
        a.paint(RoundBox(c + v3((0.02 * math.cos(ang), 0, 0.02 * math.sin(ang))), (0.3, 0.4, 0.07), 0.0, R=R), 1)   # band
        for side in (-1, 1):                                                   # panel line framing each face
            a.paint(RoundBox(c + v3((0, side * 0.31, 0)), (0.16, 0.012, 0.2), 0.0, R=R), 2)
            a.sub(RoundBox(c + v3((0, side * 0.31, 0)), (0.13, 0.03, 0.17), 0.01, R=R), k=0.01)
    out.append(("Plates", a, 0.009 if FINE[0] else 0.018, "portal_armor"))
    b = Field("Pylons")                                                        # white pylons with hazard stripes
    for sgn in (-1, 1):
        b.add(RoundBox((sgn * 1.55, 0.0, 0.44), (0.32, 0.44, 0.44), 0.09))
        b.add(RoundBox((sgn * 1.55, 0.0, 0.9), (0.26, 0.36, 0.06), 0.04), k=0.03)              # cap
        for side in (-1, 1):
            n = 7
            Rh = rot_from_axes(x_axis=(math.cos(0.6), 0, math.sin(0.6)), y_axis=(0, 1, 0))
            for i in range(n):                                                 # a hazard band low on each face
                off = ((i + 0.5) / n - 0.5) * 0.64
                b.paint(RoundBox((sgn * 1.55 + off, side * 0.44, 0.2), (0.32 / n, 0.06, 0.16), 0.0, R=Rh), 1 if i % 2 == 0 else 3)
            b.paint(RoundBox((sgn * 1.55, side * 0.44, 0.09), (0.36, 0.06, 0.012)), 2)      # seam under it
            for i in range(3):                                                 # vents above it
                z = 0.5 + i * 0.12
                b.sub(RoundBox((sgn * 1.55, side * 0.45, z), (0.18, 0.04, 0.025), 0.01), k=0.01)
                b.paint(RoundBox((sgn * 1.55, side * 0.44, z), (0.2, 0.05, 0.04)), 2)
    b.inter(Plane((0, 0, 0.0), (0, 0, -1)))
    out.append(("Pylons", b, 0.009 if FINE[0] else 0.018, "portal_armor"))
    g = Field("Core")
    g.add(Torus((0, 0, PZ), 1.33, 0.05, R=AXY))
    for sgn in (-1, 1):
        for i in range(3):
            t = 0.25 + 0.25 * i
            c = v3((sgn * (1.72 + 0.28 * t), 0.0, 0.52 + 1.1 * t))
            g.add(Torus(c, 0.19, 0.035, R=rot_from_axes(z_axis=(sgn * 0.28, 0, 1.1))))
    out.append(("Core", g, 0.008 if FINE[0] else 0.016, "glow_cyan"))
    t = Field("Beacons")
    for sgn in (-1, 1):
        t.add(Sphere((sgn * 2.05, 0.0, 1.8), 0.14))
    out.append(("Beacons", t, 0.008 if FINE[0] else 0.016, "glow_magenta"))
    return out


def portal_lights():
    """Twelve light strips round the ring's rim, alternately magenta and cyan; game.gd turns them."""
    out = []
    a_f, b_f = Field("LightsA"), Field("LightsB")
    for k in range(12):
        a = 2 * math.pi * k / 12 + math.pi / 12
        c = v3((1.74 * math.cos(a), 0.0, PZ + 1.74 * math.sin(a)))
        R = rot_from_axes(x_axis=(math.cos(a), 0, math.sin(a)), y_axis=(0, 1, 0))
        (a_f if k % 2 == 0 else b_f).add(RoundBox(c, (0.05, 0.27, 0.07), 0.025, R=R))
    out.append(("LightsA", a_f, 0.006 if FINE[0] else 0.012, "glow_magenta"))
    out.append(("LightsB", b_f, 0.006 if FINE[0] else 0.012, "glow_cyan"))
    return out


# ------------------------------------------------------------------------------------------------ the kits
# prop name -> (builder, game-mesh triangle budget). Tuft and Flowers are direct geometry (decor_build).
def KITS(theme):
    if theme in ("delta", "desert", "canyon", "city"):     # the Bronze Age kits (v0.9.28)
        import decor_bronze
        return decor_bronze.KITS(theme)
    if theme in ("highland", "forge", "bog", "iron_city"):  # the Iron Age kits
        import decor_iron
        return decor_iron.KITS(theme)
    if theme in ("olive", "coast", "acropolis", "classical_city"):  # the Classical Age kits
        import decor_classical
        return decor_classical.KITS(theme)
    if theme == "portal":
        return {"Portal": (lambda: portal(23), 3600), "PortalLights": (lambda: portal_lights(), 300)}
    if theme == "meadow":
        return {
            "Pine_A": (lambda: pine(2.8, 4, 0.95, 1, theme), 1500), "Pine_B": (lambda: pine(3.3, 5, 1.0, 2, theme), 1800),
            "Pine_C": (lambda: pine(1.9, 3, 0.72, 3, theme), 1100),
            "Bush_A": (lambda: bush(1.0, 0.36, 4, theme), 700), "Bush_B": (lambda: bush(0.68, 0.3, 5, theme, berries=True), 500),
            "Rock_A": (lambda: rock(2.0, 0.52, 6, theme), 700), "Rock_B": (lambda: rock(1.3, 0.32, 7, theme, 1), 450),
            "Rock_C": (lambda: rock(2.4, 0.65, 8, theme, 3), 900),
            "Stump": (lambda: stump(9, theme), 400), "Log": (lambda: log(10, theme), 420),
            "Mammoth": (lambda: mammoth(11, theme), 5200), "Dolmen": (lambda: dolmen(12, theme), 2400),
            "BoneHut": (lambda: bone_hut(13, theme), 3200), "Cave": (lambda: cave(14, theme), 5000),
        }
    if theme == "snow":
        return {
            "Pine_A": (lambda: pine(2.8, 4, 0.95, 1, theme), 1500), "Pine_B": (lambda: pine(3.3, 5, 1.0, 2, theme), 1800),
            "Pine_C": (lambda: pine(1.9, 3, 0.72, 3, theme), 1100),
            "Rock_A": (lambda: rock(2.0, 0.52, 6, theme), 700), "Rock_B": (lambda: rock(1.3, 0.32, 7, theme, 1), 450),
            "Rock_C": (lambda: rock(2.4, 0.65, 8, theme, 3), 900),
            "Mound_A": (lambda: mound(2.2, 0.38, 15), 500), "Mound_B": (lambda: mound(1.5, 0.25, 16), 350),
            "Ice_A": (lambda: ice_cluster(1.2, 0.7, 17), 300), "Ice_B": (lambda: ice_cluster(0.7, 0.5, 18), 220),
            "Stump": (lambda: stump(9, theme), 400), "Log": (lambda: log(10, theme), 420),
            "Mammoth": (lambda: mammoth(11, theme), 5200), "Dolmen": (lambda: dolmen(12, theme), 2400),
            "BoneHut": (lambda: bone_hut(13, theme), 3200), "Cave": (lambda: cave(14, theme), 5000),
        }
    return {
        "Dead_A": (lambda: dead_tree(1.3, 19, theme), 700), "Dead_B": (lambda: dead_tree(1.02, 20, theme), 600),
        "Rock_A": (lambda: rock(2.0, 0.52, 6, theme), 700), "Rock_B": (lambda: rock(1.3, 0.32, 7, theme, 1), 450),
        "Rock_C": (lambda: rock(2.4, 0.65, 8, theme, 3), 900),
        "Obsidian": (lambda: obsidian(1.7, 1.0, 21), 500), "Stump": (lambda: stump(9, theme), 400),
        "Mammoth": (lambda: mammoth(11, theme), 5200), "Cave": (lambda: cave(14, theme), 5000),
        "Volcano": (lambda: volcano(22), 4000),
    }
