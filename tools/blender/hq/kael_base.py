"""Kael's knoll: a granite tor on a heathery hilltop. Two great rounded slabs weathered into layers and split by joints,
the top one flat where he stands, lichen on their tops; round its foot a ring of fourteen green-glowing stones set in
the turf (the hero ring, its own emissive mesh); behind him on his left a weathered post with a red deer stag's skull
and antlers bound to its top with rawhide (the warden's waymark); behind him on his right three javelins planted in the
turf; pebbles (distance fields) + grass, heather and gorse (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
import javelin as jv

GROUND_R = 1.32
GROUND_TOP = 0.14
TOP_Z = 0.34                       # the tor's flat top = where his feet stand
STAND = v3((0.0, 0.0, TOP_Z))
RING_R = 0.86                      # the glowing stones
N_GLOW = 14
POST = v3((0.7, 0.8, 0.0))         # the waymark (behind him, on his left)
POST_H = 0.92
JAV_FOOT = v3((-0.74, 0.74, 0.0))  # the planted javelins (behind him, on his right)


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.05 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    """The heathery hilltop: a low mound."""
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.035) * np.sin(a * 5 + 0.3) + F(0.02) * np.sin(a * 11 + 1.9) + F(0.02) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.05) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.09), 0), np.maximum(dz + F(0.09), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.09), dz + F(0.09)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.09)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _slab(c, r0, z0, z1, seed, rr=0.07, flat=0.0):
    """A rounded granite slab: a lobed disc of radius ~r0 from z0 to z1, its edges rounded by rr, weathered into thin
    layers on its sides; `flat` keeps the middle of its top smooth (where he stands)."""
    rs = np.random.RandomState(seed)
    ph = rs.uniform(0, 2 * math.pi, 3)
    amp = rs.uniform(0.025, 0.06, 3)
    zm, h = (z0 + z1) / 2, (z1 - z0) / 2
    def fn(P):
        x, y, z = P[:, 0] - F(c[0]), P[:, 1] - F(c[1]), P[:, 2]
        r = np.sqrt(x * x + y * y)
        a = np.arctan2(y, x)
        R = F(r0) + F(amp[0]) * np.sin(a * 2 + F(ph[0])) + F(amp[1]) * np.sin(a * 3 + F(ph[1])) + F(amp[2]) * np.sin(a * 5 + F(ph[2]))
        R = R + F(0.012) * np.sin(z * F(95) + F(0.8) * NOISE(P * F(5)))                 # the weathered layers
        dr = r - R
        dz = np.abs(z - F(zm)) - F(h)
        q0 = np.maximum(dr + F(rr), 0)
        q1 = np.maximum(dz + F(rr), 0)
        return np.minimum(np.maximum(dr + F(rr), dz + F(rr)), 0) + np.sqrt(q0 * q0 + q1 * q1) - F(rr)
    def disp(P):
        x, y = P[:, 0] - F(c[0]), P[:, 1] - F(c[1])
        keep = np.clip((np.sqrt(x * x + y * y) - F(flat)) / F(0.15), 0, 1) if flat > 0 else F(1.0)
        return (F(0.008) * NOISE(P * F(6) + F(seed)) + F(0.004) * NOISE(P * F(19) + F(seed * 2))) * keep + F(0.0015) * NOISE(P * F(45))
    m = r0 + 0.2
    return Func(fn, (c[0] - m, c[1] - m, z0 - 0.05), (c[0] + m, c[1] + m, z1 + 0.05), disp=disp, disp_amp=0.014)


def rock_field():
    """Granite: the tor (two slabs, the lower one broader and offset), its joints, a split boulder at its side."""
    fd = Field("Rock")
    fd.add(_slab((0.04, 0.05), 0.7, -0.04, 0.2, 11, rr=0.08), 0.0)
    fd.add(_slab((0.0, 0.0), 0.57, 0.16, TOP_Z, 12, rr=0.07, flat=0.36), 0.02)
    for a, w in ((0.4, 0.008), (2.2, 0.007), (3.9, 0.009), (5.2, 0.006)):       # vertical joints down its sides
        d = v3((math.cos(a), math.sin(a), 0.0))
        c = d * 0.66 + v3((0, 0, 0.12))
        fd.sub(RoundBox(c, (w, 0.16, 0.2), 0.004, R=rot_from_axes(z_axis=(0, 0, 1), y_axis=d)), 0.006)
    fd.add(Stone(v3((0.56, -0.5, 0.17)), 0.17, seed=31, squash=(1.1, 0.9, 0.7), noise=0.05), 0.03)
    fd.add(Stone(v3((0.68, -0.32, 0.16)), 0.1, seed=32, squash=(1.0, 0.9, 0.7), noise=0.05), 0.02)
    return fd


def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + 0.12
    x, y = math.cos(a) * RING_R, math.sin(a) * RING_R
    return v3((x, y, ground_height(x, y) + 0.008))


def glowstones_field():
    fd = Field("Glowstones")
    for i in range(N_GLOW):
        c = glow_pos(i)
        a = i * 2 * math.pi / N_GLOW + 0.12
        fd.add(Ellipsoid(c, (0.042, 0.034, 0.026), R=euler(0, 0, a)), 0.0)
    return fd


def kerb_field():
    """Small flat stones set round each glowing stone (in the turf)."""
    fd = Field("Kerb")
    rs = np.random.RandomState(41)
    for i in range(N_GLOW):
        c = glow_pos(i)
        for k in range(3):
            a = rs.uniform(0, 2 * math.pi)
            p = c + v3((math.cos(a) * 0.06, math.sin(a) * 0.06, -0.006))
            fd.add(Stone(p, rs.uniform(0.022, 0.03), seed=600 + i * 3 + k, squash=(1.2, 1.0, 0.45), noise=0.05), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the waymark
SKULL_UP = v3((0.0, 0.0, 1.0))
SKULL_FWD = norm(v3((-0.25, -1.0, -0.12)))          # it looks out over the knoll, toward the front


def skull_frame():
    g = ground_height(POST[0], POST[1])
    top = POST + v3((0, 0, g + POST_H))
    fwd = SKULL_FWD
    side = norm(np.cross(fwd, SKULL_UP))
    up = np.cross(side, fwd)
    return top + up * 0.05 + fwd * 0.02, fwd, side, up


def wood_field():
    """The post: a weathered split log (bark, label 0; its split face 5), a forked top the skull sits in, rawhide lashing
    (label 7 in bark_wood: withies) round the skull's base."""
    fd = Field("Wood")
    g = ground_height(POST[0], POST[1])
    b = POST + v3((0, 0, g - 0.05))
    grain = lambda P: F(0.003) * NOISE(P * np.array([40, 40, 6], F))
    fd.add(RoundCone(b, b + v3((0.01, 0.0, POST_H)), 0.062, 0.052, disp=grain, disp_amp=0.004), 0.0)
    fd.add(Sphere(b + v3((0.01, 0.0, POST_H)), 0.05), 0.03, 5)                         # its cut top
    fd.add(RoundCone(b + v3((0, 0, 0.02)), b + v3((0, 0, 0.12)), 0.09, 0.064, disp=grain, disp_amp=0.004), 0.03)    # flared foot
    c, fwd, side, up = skull_frame()
    for s in (-1, 1):                                                                 # the fork's two prongs
        p0 = b + v3((0.01, 0.0, POST_H - 0.04))
        p1 = c - up * 0.02 + side * (s * 0.05) - fwd * 0.04
        fd.add(RoundCone(p0, p1, 0.03, 0.022, disp=grain, disp_amp=0.003), 0.02)
    for k in range(3):                                                                # rawhide lashing
        fd.add(Torus(b + v3((0.01, 0, POST_H - 0.06 - 0.022 * k)), 0.055, 0.008), 0.003, 7)
    return fd


def _tine(fd, a, b, r0, r1, k=0.01):
    fd.add(RoundCone(a, b, r0, r1), k)


def antler_pts(s):
    """One antler (s = +1 his left, -1 his right): its beam's points (skull frame: x side, y forward, z up)."""
    return [v3((s * 0.03, -0.01, 0.06)), v3((s * 0.07, 0.0, 0.12)), v3((s * 0.13, 0.03, 0.24)), v3((s * 0.18, 0.02, 0.36)),
            v3((s * 0.19, -0.03, 0.46)), v3((s * 0.16, -0.06, 0.54))]


def bone_field():
    """A red deer stag's bleached skull (its long face, the eye sockets and nostrils hollowed) and its antlers: two
    beams with brow, bez and trez tines and a forked crown, burrs at their roots."""
    fd = Field("Bone")
    c, fwd, side, up = skull_frame()
    W = lambda p: c + side * p[0] + fwd * p[1] + up * p[2]
    R = rot_from_axes(x_axis=side, y_axis=fwd)
    fd.add(Ellipsoid(W((0, -0.01, 0.0)), (0.058, 0.075, 0.056), R=R), 0.0)                        # cranium
    fd.add(RoundCone(W((0, 0.04, -0.01)), W((0, 0.2, -0.05)), 0.042, 0.022), 0.03)                # the long face
    fd.add(Ellipsoid(W((0, 0.11, -0.035)), (0.04, 0.07, 0.03), R=R), 0.02)
    for s in (-1, 1):
        fd.add(Sphere(W((s * 0.05, 0.035, 0.0)), 0.022), 0.012)                                  # orbits
        fd.sub(Sphere(W((s * 0.06, 0.04, 0.004)), 0.015), 0.004)
        fd.sub(Ellipsoid(W((s * 0.012, 0.205, -0.045)), (0.008, 0.02, 0.008), R=R), 0.003)       # nostrils
    for s in (-1, 1):
        pts = [W(p) for p in antler_pts(s)]
        fd.add(Chain(pts, [0.017, 0.016, 0.014, 0.012, 0.01, 0.006], k=0.006,
                     disp=lambda P: F(0.0018) * NOISE(P * F(70)), disp_amp=0.002), 0.012)
        fd.add(Torus(pts[0], 0.019, 0.006, R=rot_from_axes(z_axis=pts[1] - pts[0])), 0.004)     # the burr
        _tine(fd, W((s * 0.04, 0.0, 0.08)), W((s * 0.07, 0.13, 0.1)), 0.012, 0.004)              # brow tine
        _tine(fd, W((s * 0.06, 0.0, 0.12)), W((s * 0.1, 0.11, 0.16)), 0.01, 0.004)               # bez
        _tine(fd, W((s * 0.15, 0.03, 0.29)), W((s * 0.2, 0.13, 0.33)), 0.01, 0.004)              # trez
        _tine(fd, W((s * 0.19, -0.03, 0.46)), W((s * 0.25, 0.0, 0.53)), 0.008, 0.003)            # the crown's points
        _tine(fd, W((s * 0.185, -0.04, 0.48)), W((s * 0.2, -0.12, 0.54)), 0.008, 0.003)
    return fd


def planted_javelins():
    """(butt in the turf, direction, length) of the three planted javelins."""
    out = []
    for k, (dx, dy, lean_x, lean_y) in enumerate(((0.0, 0.0, -0.08, 0.1), (0.1, 0.06, 0.06, 0.16), (-0.06, 0.1, -0.16, 0.06))):
        x, y = JAV_FOOT[0] + dx, JAV_FOOT[1] + dy
        butt = v3((x, y, ground_height(x, y) - 0.08))
        out.append((butt, norm(v3((lean_x, lean_y, 1.0))), 1.08 + 0.05 * k))
    return out


def javelins_field():
    """Three javelins planted butt-first in the turf, leaning: ash (label 0), bindings (5), iron heads (6)."""
    fd = Field("Javelins")
    for butt, d, L in planted_javelins():
        up = norm(np.cross(d, v3((1, 0, 0))))
        a0 = butt + d * (L - jv.JAV_FWD)
        jv._javelin(fd, a0, d, up, back=L - jv.JAV_FWD, fwd=jv.JAV_FWD, wood=0, full=False)
    return fd


# ---------------------------------------------------------------------------------------------- scatter
def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < 0.8 + pad:
        return True
    if math.hypot(c[0] - 0.6, c[1] + 0.42) < 0.3 + pad:
        return True
    if math.hypot(c[0] - POST[0], c[1] - POST[1]) < 0.14 + pad:
        return True
    if math.hypot(c[0] - JAV_FOOT[0], c[1] - JAV_FOOT[1]) < 0.18 + pad:
        return True
    for i in range(N_GLOW):
        g = glow_pos(i)
        if math.hypot(c[0] - g[0], c[1] - g[1]) < 0.1 + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(23)
    n = 0
    tries = 0
    while n < 14 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.95, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.026, 0.05), seed=340 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=29):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 26 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.84, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, -0.03):
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


def _bloom(out, top, tilt, size, kind_col):
    R = rot_from_axes(z_axis=tilt)
    pv, pf = [], []
    for k in range(5):
        a = 2 * math.pi * k / 5
        dirk = R @ v3((math.cos(a), math.sin(a), 0.15))
        sidek = R @ v3((-math.sin(a), math.cos(a), 0))
        b0 = len(pv)
        pv += [top + tilt * 0.003, top + dirk * size * 0.55 + sidek * size * 0.42, top + dirk * size, top + dirk * size * 0.55 - sidek * size * 0.42]
        pf.append((b0, b0 + 1, b0 + 2, b0 + 3))
    out.append((pv, pf, 1, kind_col))
    cv = [top + R @ v3((math.cos(2 * math.pi * k / 6) * size * 0.3, math.sin(2 * math.pi * k / 6) * size * 0.3, 0.006)) for k in range(6)]
    cv.append(top + R @ v3((0, 0, 0.012)))
    out.append((cv, [(k, (k + 1) % 6, 6) for k in range(6)], 2, kind_col))


def flower_geometry(seed=37):
    """Heather: low clumps of stems spiked with purple bells (swatch 2); a few yellow gorse blooms (swatch 1)."""
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 8 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.9, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.04) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.22 for s in spots):
            continue
        spots.append((c, 2 if len(spots) % 3 else 1))
    for c, col in spots:
        n_stem = rs.randint(5, 9) if col == 2 else rs.randint(3, 5)
        for k in range(n_stem):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.07)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.09, 0.16)
            d = norm(v3((math.cos(ang) * 0.35, math.sin(ang) * 0.35, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.011, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, col))
            nb = 3 if col == 2 else 1
            for j in range(nb):
                p = root + d * h * (1.0 - 0.22 * j) + v3((rs.uniform(-0.01, 0.01), rs.uniform(-0.01, 0.01), 0))
                tilt = norm(v3((rs.uniform(-0.5, 0.5), rs.uniform(-0.5, 0.5), 1.0)))
                _bloom(out, p, tilt, 0.022 if col == 2 else 0.032, col)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Rock", rock_field(), 0.0045), ("Glowstones", glowstones_field(), 0.0025),
            ("Kerb", kerb_field(), 0.004), ("Wood", wood_field(), 0.003), ("Bone", bone_field(), 0.0018),
            ("Javelins", javelins_field(), 0.0018), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Wood", "Javelins")
LOW_TARGETS = {"Ground": 1400, "Rock": 4200, "Glowstones": 500, "Kerb": 600, "Wood": 700, "Bone": 900, "Javelins": 500,
               "Pebbles": 380}
MAT_OVERRIDES = {"Rock": ("stone", {"name": "HQ_Granite", "moss": True}),
                 "Kerb": ("stone", {"name": "HQ_KerbStone", "scale": 0.3}),
                 "Wood": ("bark_wood", {"name": "HQ_WaymarkPost", "bark": (0.4, 0.33, 0.26), "wood": (0.7, 0.62, 0.5)}),
                 "Bone": ("bone", {"name": "HQ_StagSkull"}),
                 "Javelins": ("javelin_shaft", {"name": "HQ_BaseJavelin"}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
GLOW = {"Glowstones": ((0.42, 1.0, 0.38), 1.0, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and 0.8 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.08))
