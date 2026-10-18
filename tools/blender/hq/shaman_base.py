"""Tar Pit Shaman base: a grassy mound with a bubbling pit of black tar in front of him, a mammoth's ribcage and a tusk
rising out of it (it got stuck), tarry footprints from the pit to the flat stone he stands on, a spirit post hung with
bone charms, a stone bowl of green spirit fire, a standing stone painted with an ochre spiral, reeds with cattails at the
pit's edge, pebbles (distance fields) + grass, flowers and reeds (direct low-poly geometry). Bubbles that swell and pop
on the tar are their own little meshes (Bubble*), animated in game."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
from ugo import bez3
from ugo_base import spiral

GROUND_R = 1.3
GROUND_TOP = 0.16
TARL = 7          # tar stains (ground label)
PAINT = 5
PIT_C = v3((0.1, -0.4, 0.0))
PIT_R = (0.64, 0.42)
SLAB_C = v3((-0.06, 0.44, 0.0))
POST = v3((0.74, 0.6, 0.0))
BOWL = v3((-0.8, 0.5, 0.0))
SPIRAL_STONE = v3((-1.0, -0.22, 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.05 * max(0.0, 1 - (r / GROUND_R) ** 2)


TAR_Z = ground_height(PIT_C[0], PIT_C[1]) - 0.035
SLAB_TOP = ground_height(SLAB_C[0], SLAB_C[1]) + 0.05
STAND = v3((SLAB_C[0], SLAB_C[1], SLAB_TOP))
FLAME_TOP = v3((BOWL[0], BOWL[1], ground_height(BOWL[0], BOWL[1]) + 0.14))


def pit_sd(P, grow=0.0):
    """Signed distance (approx.) to the pit's irregular outline in the ground plane."""
    dx = (P[:, 0] - F(PIT_C[0])) / F(PIT_R[0] + grow)
    dy = (P[:, 1] - F(PIT_C[1])) / F(PIT_R[1] + grow)
    a = np.arctan2(dy, dx)
    wob = F(0.06) * np.sin(a * 3 + 0.8) + F(0.04) * np.sin(a * 5 + 2.1)
    return (np.sqrt(dx * dx + dy * dy) - F(1.0) - wob) * F(min(PIT_R) + grow) + F(0.012) * NOISE(P * F(7))


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.035) * np.sin(a * 5 + 0.7) + F(0.02) * np.sin(a * 11 + 2.0) + F(0.02) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.05) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.09), 0), np.maximum(dz + F(0.09), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.09), dz + F(0.09)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.09)
    fd.add(Func(disc, (-1.5, -1.5, -0.25), (1.5, 1.5, 0.35),
                disp=lambda P: F(0.008) * NOISE(P * F(7)) + F(0.004) * NOISE(P * F(23)), disp_amp=0.014), 0.0)
    # the pit: a dish sunk under the tar's surface, a little raised lip of mud round it
    fd.sub(Func(lambda P: np.maximum(pit_sd(P), F(TAR_Z - 0.05) - P[:, 2]), (-0.7, -1.0, -0.1), (0.9, 0.2, 0.5)), 0.04)
    fd.add(Func(lambda P: np.maximum(np.abs(pit_sd(P, 0.05)) - F(0.05), P[:, 2] - F(TAR_Z + 0.04)) + F(0.006) * NOISE(P * F(20)),
                (-0.7, -1.0, 0.0), (0.9, 0.2, 0.4)), 0.03)
    # tar smeared round the pit's edge, and tarry footprints walking from the pit to his stone
    fd.paint(Func(lambda P: pit_sd(P, 0.07) + F(0.02) * NOISE(P * F(14)), (-0.75, -1.0, -0.1), (0.95, 0.25, 0.5)), TARL)
    for i, (x, y, ang) in enumerate(((-0.12, -0.02, 0.15), (0.0, 0.13, -0.1), (-0.12, 0.26, 0.2))):
        c = v3((x, y, 0))
        R = euler(0, 0, ang)
        def foot(P, c=c, R=R, i=i):
            q = (P - c.astype(F)) @ R.astype(F)
            d = np.sqrt((q[:, 0] / F(0.042)) ** 2 + (q[:, 1] / F(0.075)) ** 2) * F(0.042) - F(0.042)
            for k, (tx, r) in enumerate(((-0.025, 0.012), (-0.004, 0.009), (0.013, 0.008), (0.028, 0.007))):
                d = np.minimum(d, np.sqrt((q[:, 0] - F(tx)) ** 2 + (q[:, 1] + F(0.095 - 0.006 * k)) ** 2) - F(r))
            return np.maximum(d, np.abs(P[:, 2] - F(0.2)) - F(0.08))
        fd.paint(Func(foot, c + v3((-0.2, -0.2, 0.0)), c + v3((0.2, 0.2, 0.4))), TARL)
    return fd


BUBBLES = [((0.28, -0.32), 0.05), ((-0.12, -0.5), 0.042), ((0.42, -0.5), 0.036), ((0.06, -0.2), 0.03)]


def tar_field():
    """The tar: a glossy pool with a few domes, slow ripples and a sag where things sank."""
    fd = Field("Tar")
    surf = Func(lambda P: np.maximum(pit_sd(P, 0.02), np.maximum(P[:, 2] - F(TAR_Z) - F(0.004) * NOISE(P * F(5)), F(TAR_Z - 0.06) - P[:, 2])),
                (-0.7, -1.0, TAR_Z - 0.1), (0.9, 0.2, TAR_Z + 0.05))
    fd.add(surf, 0.0)
    for (x, y), r in ((0.18, -0.6), 0.03), ((-0.25, -0.35), 0.026), ((0.52, -0.38), 0.022):
        fd.add(Sphere((x, y, TAR_Z - r * 0.35), r), 0.012)
    for (x, y), r in BUBBLES[:2]:
        fd.add(Torus((x, y, TAR_Z), r * 1.9, 0.005), 0.006)
        fd.add(Torus((x, y, TAR_Z), r * 3.0, 0.004), 0.006)
    return fd


def rocks_field():
    """The flat stone he stands on, the spirit-fire bowl, the spiral stone, stones round the pit, boulders."""
    fd = Field("Rocks")
    g = ground_height(SLAB_C[0], SLAB_C[1])
    slab = Stone(v3((SLAB_C[0], SLAB_C[1], g - 0.06)), 0.34, seed=31, cuts=11, squash=(1.0, 0.82, 0.38), soft=0.05, noise=0.012)
    fd.add(Inter(slab, Plane((0, 0, SLAB_TOP), (0.02, -0.03, 1.0)), 0.02), 0.0)
    # the bowl: a rough stone basin
    gb = ground_height(BOWL[0], BOWL[1])
    bowl = Stone(v3((BOWL[0], BOWL[1], gb + 0.04)), 0.17, seed=33, cuts=9, squash=(1.0, 1.0, 0.7), soft=0.06, noise=0.02)
    fd.add(Inter(bowl, Plane((0, 0, gb + 0.14), (0, 0, 1)), 0.015), 0.0)
    fd.sub(Ellipsoid((BOWL[0], BOWL[1], gb + 0.16), (0.12, 0.12, 0.07)), 0.02)
    # spiral stone
    gs = ground_height(SPIRAL_STONE[0], SPIRAL_STONE[1])
    base = v3((SPIRAL_STONE[0], SPIRAL_STONE[1], gs - 0.06))
    top = base + norm(v3((-0.12, 0.05, 1.0))) * 0.62
    R = rot_from_axes(z_axis=norm(top - base), y_axis=(0.25, 1, 0)) @ euler(0, 0, 0.0)
    fd.add(Stone((base + top) / 2, 0.31, seed=35, cuts=14, squash=(0.68, 0.42, 1.0), soft=0.03, depth=(0.78, 0.94), R=R, noise=0.016), 0.0)
    sc = lerp(base, top, 0.6) + v3((0, -0.06, 0))
    fd.paint(Func(lambda P: spiral(P, sc, turns=2.2, r1=0.075, w=0.011), sc - 0.3, sc + 0.3), PAINT)
    # stones round the pit's rim
    rs = np.random.RandomState(5)
    for i in range(11):
        a = 2 * math.pi * i / 11 + rs.uniform(-0.15, 0.15)
        x = PIT_C[0] + math.cos(a) * (PIT_R[0] + 0.07)
        y = PIT_C[1] + math.sin(a) * (PIT_R[1] + 0.06)
        if y > -0.05 and abs(x - SLAB_C[0]) < 0.3:
            continue                                     # leave the way from his stone to the pit open
        r = rs.uniform(0.045, 0.075)
        fd.add(Stone((x, y, ground_height(x, y) - 0.005), r, seed=50 + i, cuts=9, squash=(1.0, 0.9, 0.62), soft=0.06, noise=0.03), 0.01)
    for c, r, s in (((-1.02, 0.42, GROUND_TOP + 0.02), 0.12, 41), ((1.05, -0.05, GROUND_TOP + 0.03), 0.13, 43), ((0.35, 0.98, GROUND_TOP + 0.02), 0.1, 45)):
        fd.add(Stone(c, r, seed=s, cuts=10, squash=(1.0, 0.95, 0.75), soft=0.06, noise=0.02), 0.03)
    return fd


RIBS = [(-0.3, 1.0), (-0.16, 0.96), (-0.02, 0.88), (0.12, 0.76)]
SKULL_TOP = v3((0.36, -0.44, 0.0))


def bone_field():
    """A mammoth's ribs arching out of the tar, the top of its skull, charms on the spirit post."""
    fd = Field("Bone")
    for x, s in RIBS:
        z0 = TAR_Z - 0.03
        pts = [v3((x, -0.3, z0)), v3((x + 0.01, -0.36, z0 + 0.19 * s)), v3((x + 0.02, -0.47, z0 + 0.27 * s)), v3((x + 0.025, -0.58, z0 + 0.22 * s)),
               v3((x + 0.03, -0.66, z0 + 0.08 * s)), v3((x + 0.03, -0.68, z0 - 0.04))]
        fd.add(Chain(pts, [0.024 * s, 0.022 * s, 0.02 * s, 0.018 * s, 0.016 * s, 0.015 * s], k=0.01,
                     disp=lambda P: F(0.002) * NOISE(P * F(40)), disp_amp=0.003), 0.0)
    # spine knobs between the ribs where they leave the tar
    for i in range(len(RIBS) - 1):
        x = (RIBS[i][0] + RIBS[i + 1][0]) / 2
        fd.add(Ellipsoid((x, -0.3, TAR_Z + 0.005), (0.035, 0.025, 0.022)), 0.01)
    # the skull's dome and an eye socket's rim, sunk to the brow
    c = SKULL_TOP + v3((0, 0, TAR_Z - 0.04))
    fd.add(Ellipsoid(c, (0.15, 0.12, 0.1), R=euler(0.1, 0.2, 0.4), disp=lambda P: F(0.003) * NOISE(P * F(30)), disp_amp=0.004), 0.0)
    fd.sub(Sphere(c + v3((0.07, -0.1, 0.045)), 0.03), 0.01)
    fd.add(Torus(c + v3((0.07, -0.1, 0.045)), 0.03, 0.008, R=rot_from_axes(z_axis=(0.5, -0.8, 0.4))), 0.008)
    # charms hanging from the spirit post's crossbar
    for x, L in ((-0.15, 0.2), (0.0, 0.26), (0.15, 0.2)):
        top = POST + v3((x, 0.0, 1.28 - L))
        fd.add(RoundCone(top, top + v3((0, 0, -0.06)), 0.016, 0.012), 0.0)
        fd.add(Sphere(top + v3((0, 0, -0.07)), 0.018), 0.005)
        fd.add(Sphere(top + v3((0, 0, 0.012)), 0.014), 0.005)
    return fd


def tusks_field():
    fd = Field("Tusks")
    p0 = v3((0.46, -0.56, TAR_Z - 0.04))
    p1 = v3((0.52, -0.72, TAR_Z + 0.22))
    p2 = v3((0.68, -0.72, TAR_Z + 0.42))
    p3 = v3((0.7, -0.52, TAR_Z + 0.42))
    ts = np.linspace(0, 1, 18)
    pts = [bez3(p0, p1, p2, p3, t) for t in ts]
    fd.add(Chain(pts, [0.05 * (1 - t) ** 0.8 + 0.008 for t in ts], k=0.01,
                 disp=lambda P: F(0.002) * NOISE(P * np.array([40, 40, 8], F)), disp_amp=0.003), 0.0)
    return fd


def wood_field():
    """The spirit post: a weathered post with a crossbar, a carved knob on top."""
    fd = Field("Wood")
    g = ground_height(POST[0], POST[1])
    bark = lambda P: F(0.004) * NOISE(P * np.array([45, 45, 6], F)) + F(0.002) * NOISE(P * F(90))
    fd.add(Chain([POST + v3((0, 0, g - 0.06)), POST + v3((0.01, 0, 0.75)), POST + v3((-0.005, 0, 1.42))], [0.05, 0.046, 0.042], k=0.01,
                 disp=bark, disp_amp=0.005), 0.0)
    fd.add(Sphere(POST + v3((0, 0, 1.46)), 0.055), 0.02)
    fd.sub(Torus(POST + v3((0, 0, 1.46)), 0.056, 0.008), 0.003)
    fd.add(RoundCone(POST + v3((-0.24, 0, 1.3)), POST + v3((0.24, 0, 1.3)), 0.028, 0.026, disp=bark, disp_amp=0.004), 0.01)
    for a in (0.4, 2.5, 4.4):                                          # wedge stones at its foot
        d = v3((math.cos(a), math.sin(a), 0))
        fd.add(Stone(POST + d * 0.075 + v3((0, 0, g + 0.02)), 0.05, seed=int(a * 10), squash=(0.8, 0.8, 1.0), noise=0.05), 0.01)
    return fd


def cord_field():
    fd = Field("Cord")
    fd.add(Torus(POST + v3((0, 0, 1.3)), 0.052, 0.01, R=rot_from_axes(z_axis=(0.7, 0, 0.7))), 0.0)
    fd.add(Torus(POST + v3((0, 0, 1.3)), 0.052, 0.01, R=rot_from_axes(z_axis=(-0.7, 0, 0.7))), 0.0)
    for x, L in ((-0.15, 0.2), (0.0, 0.26), (0.15, 0.2)):
        top = POST + v3((x, 0.0, 1.28))
        fd.add(RoundCone(top, top + v3((0, 0, -L + 0.01)), 0.005, 0.005), 0.0)
    return fd


def flame_field():
    fd = Field("Flame")
    c = FLAME_TOP + v3((0, 0, 0.06))
    fd.add(Ellipsoid(c, (0.075, 0.075, 0.1)), 0.0)
    fd.add(RoundCone(c, c + v3((0.01, 0.0, 0.24)), 0.065, 0.005), 0.045)
    for a in (0.0, 2.1, 4.2):
        d = v3((math.cos(a), math.sin(a), 0))
        fd.add(RoundCone(c + d * 0.04, c + d * 0.055 + v3((0, 0, 0.16)), 0.036, 0.003), 0.03)
    return fd


FLAME_PIVOT = FLAME_TOP + np.array((0, 0, 0.0))
FLAME_COLOR = (0.25, 1.0, 0.3)
FLAME_STRENGTH = 1.1                  # a green flame stays green (2.5 reads white in game)


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(13)
    n = 0
    tries = 0
    while n < 14 and tries < 600:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.4, 1.22)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if pit_sd(p[None].astype(F), 0.12)[0] < 0 or np.linalg.norm(p[:2] - SLAB_C[:2]) < 0.4 or np.linalg.norm(p[:2] - BOWL[:2]) < 0.25:
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.025, 0.042), seed=100 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


# ---------------------------------------------------------------------------------------- direct geometry
def _blocked(c, pad=0.0):
    p = np.array([[c[0], c[1], 0.2]], np.float32)
    if pit_sd(p, 0.1 + pad)[0] < 0:
        return True
    for q, rr in ((SLAB_C, 0.42), (BOWL, 0.26), (POST, 0.16), (SPIRAL_STONE, 0.26)):
        if math.hypot(c[0] - q[0], c[1] - q[1]) < rr + pad:
            return True
    return False


def grass_geometry(seed=17):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 32 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.25, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.14 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(8, 13)
        big = 0.7 + 0.45 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.05)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.15, 0.45) + v3((0, 0, 1)))
            L = rs.uniform(0.13, 0.24) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.042), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


REED_SPOTS = [(-0.5, -0.66, 0.2), (0.62, -0.18, 1.3), (0.74, -0.62, 2.0), (-0.42, -0.12, 0.8)]


def flower_geometry(seed=23):
    """Flowers (kinds 0-2: stem, petals, centre) plus reeds with cattails at the pit's edge (kind 3 = brown head)."""
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 7 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.5, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.05) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.2 for s in spots):
            continue
        spots.append((c, rs.randint(0, 3)))
    for c, kind in spots:
        base = v3((c[0], c[1], ground_height(c[0], c[1]) - 0.01))
        h = rs.uniform(0.1, 0.15)
        top = base + v3((rs.uniform(-0.02, 0.02), rs.uniform(-0.02, 0.02), h))
        sv, sf, _ = _b.blade_mesh(base, top - base, h, 0.012, (0, 0, 0), segs=2)
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
        cv = [top + R @ v3((math.cos(2 * math.pi * k / 6) * 0.012, math.sin(2 * math.pi * k / 6) * 0.012, 0.008)) for k in range(6)]
        cv.append(top + R @ v3((0, 0, 0.016)))
        out.append((cv, [(k, (k + 1) % 6, 6) for k in range(6)], 2, kind))
    # reeds: tall thin blades, some with a brown cattail
    for (x, y, a0) in REED_SPOTS:
        for k in range(5):
            ang = a0 + k * 1.3
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.05)
            root = v3((x, y, 0)) + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.32, 0.48)
            d = norm(v3((math.cos(ang) * 0.12, math.sin(ang) * 0.12, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, rs.uniform(0.016, 0.022), v3((math.cos(ang), math.sin(ang), 0)) * 0.12, segs=4)
            out.append((sv, sf, 0, 0))
            if k % 2 == 0:
                c = root + d * h * 0.78
                R = rot_from_axes(z_axis=d)
                hv, hf = [], []
                ring = 7
                for zi, (zz, rr) in enumerate(((-0.045, 0.006), (-0.036, 0.016), (0.036, 0.016), (0.045, 0.006))):
                    for j in range(ring):
                        a = 2 * math.pi * j / ring
                        hv.append(c + R @ v3((math.cos(a) * rr, math.sin(a) * rr, zz)))
                for zi in range(3):
                    for j in range(ring):
                        a_, b_ = zi * ring + j, zi * ring + (j + 1) % ring
                        hf.append((a_, b_, b_ + ring, a_ + ring))
                out.append((hv, hf, 3, 3))
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Tar", tar_field(), 0.005), ("Rocks", rocks_field(), 0.005), ("Bone", bone_field(), 0.003),
            ("Tusks", tusks_field(), 0.004), ("Wood", wood_field(), 0.004), ("Cord", cord_field(), 0.0025), ("Flame", flame_field(), 0.004),
            ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Ground", "Rocks")
LOW_TARGETS = {"Ground": 1500, "Tar": 700, "Rocks": 2300, "Bone": 1000, "Tusks": 420, "Wood": 520, "Cord": 260, "Pebbles": 360, "Flame": 160}
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_PitGround", "tar_label": TARL}),
                 "Rocks": ("stone", {"name": "HQ_PitStone", "moss": True, "paint": True}),
                 "Tusks": ("bone", {"name": "HQ_Tusk", "banded": True}),
                 "Tar": ("tar", {})}
EXTRA_SWATCHES = [(0.42, 0.25, 0.12)]          # kind 3: cattail heads


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    p = np.array([[c.x, c.y, c.z]], np.float32)
    return (n.z > 0.55 and r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035 and pit_sd(p, 0.12)[0] > 0
            and math.hypot(c.x - SLAB_C[0], c.y - SLAB_C[1]) > 0.36)
