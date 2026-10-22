"""War Drummer base: a corner of a colonial fort's parade ground. A round plinth of cut stone (two courses) with a kerb of
dressed blocks; on it worn flagstones round where he stands, and round them a ring of rounded cobbles set in beaten
earth. Behind him on his right the regiment's colour on a tall pole set in a stone socket: a big crimson flag with the
gold crowned sunburst and a gold fringe, a gold spearhead finial with cords and tassels. Behind him on his left two spare
drums stacked one on the other beside a powder keg. At the plinth's foot grass, a clump of broad tropical leaves and a
young fan palm, pebbles (distance fields + direct low-poly geometry for the grass and the flowers)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
import drummer as _d
from sunpriest_base import ring_func
from crossbowman_base import _bloom

GROUND_R = 1.34
GROUND_TOP = 0.1
PLINTH_R = 0.92                # the kerb's outer face (he and his drum sweep out to ~0.78 as the tower turns)
FLAGS_R = 0.46                 # the flagstones (the cobbles round them to the kerb)
KERB_IN = 0.79
TOP_Z = 0.22                   # the floor's top = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
POLE_C = v3((-0.66, 0.85, 0.0))            # the colour's pole (behind him, on his right, beyond the plinth)
POLE_TOP = 2.32                            # (above the ground)
DRUMS_C = v3((0.66, 0.9, 0.0))             # the spare drums (behind him, on his left, at the plinth's foot)
DRUMS_S = 0.8
KEG_C = v3((0.98, 0.56, 0.0))
PALM_C = v3((-1.0, -0.6, 0.0))             # tropical green at the edge
LEAVES_C = v3((1.06, -0.36, 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 0.7) + F(0.02) * np.sin(a * 11 + 2.1) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.03) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _chip(P):
    return F(0.004) * NOISE(P * F(9)) + F(0.002) * NOISE(P * F(31))


def _fine(P):
    return F(0.0014) * NOISE(P * F(30)) + F(0.0008) * NOISE(P * F(90))


def plinth_field():
    """Cut stone (label 0; weathered dark and green low down, 7): the plinth's wall in two courses of curved blocks, a
    kerb of dressed blocks round its top, the pole's socket stone."""
    fd = Field("Plinth")
    course = (TOP_Z - GROUND_TOP + 0.06) / 2
    fd.add(Cylinder(v3((0, 0, (GROUND_TOP - 0.06 + TOP_Z - 0.04) / 2)), PLINTH_R - 0.03, TOP_Z - GROUND_TOP + 0.02, rr=0.01), 0.0)
    fd.add(ring_func(KERB_IN - 0.1, PLINTH_R, 14, 503, GROUND_TOP - 0.06 + course, course / 2, jitter=0.6, chip=_chip), 0.0)
    fd.add(ring_func(KERB_IN, PLINTH_R, 15, 509, TOP_Z + 0.022, course / 2 + 0.011, jitter=0.7, chip=_chip), 0.0)
    sc = POLE_C + v3((0, 0, ground_height(POLE_C[0], POLE_C[1]) + 0.02))
    fd.add(RoundBox(sc, (0.085, 0.085, 0.05), 0.016, R=euler(0, 0, 0.5), disp=_chip, disp_amp=0.004), 0.008)
    fd.sub(Cylinder(sc + v3((0, 0, 0.05)), 0.03, 0.04, rr=0.004), 0.003)
    fd.paint(Func(lambda P: (P[:, 2] - F(GROUND_TOP + 0.05)) + F(0.04) * NOISE(P * F(4)), (-1.2, -1.2, -0.2), (1.2, 1.2, 0.5)), 7)
    return fd


CELL = 0.07


def _hash2(cx, cy, k):
    return np.mod(np.sin(cx * F(127.1 + 17 * k) + cy * F(311.7 + 29 * k)) * F(43758.5453), F(1.0))


def _cobble_d(P):
    x, y = P[:, 0], P[:, 1]
    gx, gy = np.floor(x / F(CELL)), np.floor(y / F(CELL))
    best = np.full(len(P), F(9.0))
    step = np.zeros(len(P), F)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx, cy = gx + F(dx), gy + F(dy)
            px = (cx + F(0.18) + F(0.64) * _hash2(cx, cy, 0)) * F(CELL)
            py = (cy + F(0.18) + F(0.64) * _hash2(cx, cy, 1)) * F(CELL)
            d = np.sqrt((x - px) ** 2 + (y - py) ** 2)
            closer = d < best
            best = np.where(closer, d, best)
            step = np.where(closer, (_hash2(cx, cy, 2) - F(0.5)) * F(0.008), step)
    return best, step


def floor_field():
    """Worn flagstones round where he stands (label 0; a browner stone for some, 7) and a ring of rounded cobbles set in
    beaten earth (6: the grit between them) out to the kerb."""
    fd = Field("Floor")
    hz = 0.04
    fd.add(Cylinder(v3((0, 0, TOP_Z - hz)), 0.2, 2 * hz, rr=0.008, disp=_fine, disp_amp=0.003), 0.0)
    fd.add(ring_func(0.2, FLAGS_R, 9, 611, TOP_Z, hz, jitter=0.5, chip=_fine), 0.0)
    def cobbles(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.sqrt(x * x + y * y)
        d1, st = _cobble_d(P)
        dome = F(0.017) * (F(1.0) - np.clip(d1 / F(0.6 * CELL), 0, 1) ** 2)
        top = F(TOP_Z - 0.018) + dome + st
        return np.maximum(np.maximum(np.maximum(r - F(KERB_IN + 0.01), F(FLAGS_R + 0.004) - r), z - top), F(TOP_Z - 0.09) - z)
    R = KERB_IN + 0.03
    fd.add(Func(cobbles, (-R, -R, TOP_Z - 0.1), (R, R, TOP_Z + 0.03), disp=lambda P: F(0.001) * NOISE(P * F(40)), disp_amp=0.0015), 0.0)
    def grit(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        d1, st = _cobble_d(P)
        return np.maximum(F(0.6 * CELL) * F(0.8) - d1, F(FLAGS_R + 0.01) - r)
    fd.paint(Func(grit, (-R, -R, TOP_Z - 0.1), (R, R, TOP_Z + 0.03)), 6)
    rs = np.random.RandomState(23)
    for k in range(4):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.25, 0.4)
        fd.paint(Sphere(v3((math.cos(a) * r, math.sin(a) * r, TOP_Z)), rs.uniform(0.1, 0.16)), 7)
    return fd


# ---------------------------------------------------------------------------------------------- the regiment's colour
FLAG_W, FLAG_H = 0.62, 0.52
FLAG_OUT = norm(v3((-0.86, 0.32, 0.0)))     # the flag streams out to his right, a little back


def pole_field():
    """The colour's pole (oak, label 0; grain along it: 11), set in its socket stone."""
    fd = Field("Pole")
    base = POLE_C + v3((0, 0, ground_height(POLE_C[0], POLE_C[1]) + 0.03))
    top = POLE_C + v3((0, 0, POLE_TOP))
    fd.add(Chain([base, top], [0.022, 0.018], k=0.0, disp=lambda P: F(0.0012) * NOISE(P * np.array([40, 40, 4], F)), disp_amp=0.002), 0.0, 11)
    return fd


def _flag_coords(P):
    """(s along the fly from the pole, t down from the flag's top edge, h off its mid-surface)."""
    top = POLE_C + v3((0, 0, POLE_TOP - 0.1))
    q = P - top.astype(F)
    side = norm(np.cross(FLAG_OUT, v3((0, 0, 1))))
    s = q @ FLAG_OUT.astype(F)
    t = -q[:, 2]
    k = np.clip(s / F(FLAG_W), 0, 1)
    wave = F(0.05) * np.sin(s * F(8.5) + F(0.4) - t * F(1.5)) * k + F(0.012) * np.sin(s * F(21) + t * F(9))
    t = t - F(0.06) * k * k                                        # its fly droops a little
    h = q @ side.astype(F) - wave
    return s, t, h


def flag_field():
    """The colour: crimson silk (wool, label 0) streaming from the pole, the gold crowned sunburst painted on it (5), a
    gold fringe along its fly and foot (5); its sleeve round the pole."""
    fd = Field("Flag")
    top = POLE_C + v3((0, 0, POLE_TOP - 0.1))
    lo, hi = top - v3((1.0, 0.5, 0.75)), top + v3((0.2, 0.5, 0.12))
    def cloth(P):
        s, t, h = _flag_coords(P)
        return np.maximum(np.maximum(np.abs(h) - F(0.006), np.maximum(-s, s - F(FLAG_W))), np.maximum(-t, t - F(FLAG_H)))
    fd.add(Func(cloth, lo, hi), 0.0)
    def device(P):
        s, t, h = _flag_coords(P)
        sc = F(1.75)
        return _d.sunburst_2d((s - F(FLAG_W * 0.5)) / sc, (F(FLAG_H * 0.52) - t) / sc) * sc
    fd.paint(Func(device, lo, hi), 5)
    # the fringe along the fly edge and the foot
    def fringe(P):
        s, t, h = _flag_coords(P)
        w = F(0.03) + F(0.006) * np.sin((s + t) * F(240))
        d1 = np.maximum(np.maximum(F(FLAG_W) - s, s - F(FLAG_W) - w), np.maximum(-t, t - F(FLAG_H) - w))
        d2 = np.maximum(np.maximum(F(FLAG_H) - t, t - F(FLAG_H) - w), np.maximum(-s, s - F(FLAG_W) - w))
        return np.maximum(np.minimum(d1, d2), np.abs(h) - F(0.007))
    fd.add(Func(fringe, lo, hi), 0.003, 5)
    # the sleeve round the pole
    fd.add(Cylinder(POLE_C + v3((0, 0, POLE_TOP - 0.1 - FLAG_H / 2)), 0.03, FLAG_H, rr=0.01), 0.004)
    return fd


def gold_field():
    """Gold (label 0): the pole's spearhead finial and its collar; two cords with tassels hanging from it."""
    fd = Field("Gold")
    top = POLE_C + v3((0, 0, POLE_TOP))
    fd.add(Cylinder(top + v3((0, 0, 0.02)), 0.028, 0.04, rr=0.008), 0.0)
    fd.add(Sphere(top + v3((0, 0, 0.06)), 0.03), 0.01)
    side = norm(np.cross(FLAG_OUT, v3((0, 0, 1))))
    fd.add(Ellipsoid(top + v3((0, 0, 0.17)), (0.045, 0.012, 0.11), R=rot_from_axes(z_axis=(0, 0, 1), y_axis=side)), 0.008)
    fd.add(Torus(top + v3((0, 0, -0.03)), 0.026, 0.008), 0.004)
    for sg in (-1, 1):
        a = top + v3((0, 0, -0.03)) + side * (sg * 0.024)
        b = a + v3((0, 0, -0.16)) + side * (sg * 0.06) - FLAG_OUT * 0.04
        c = b + v3((0, 0, -0.14)) + side * (sg * 0.02)
        fd.add(Chain([a, b, c], [0.006, 0.006, 0.006], k=0.004), 0.003)
        fd.add(RoundCone(c, c + v3((0, 0, -0.08)), 0.014, 0.024), 0.008)
    return fd


# ---------------------------------------------------------------------------------------------- spare drums, keg
def drums_field():
    """Two spare drums (smaller than his) stacked one on the other, the top one tipped a little and turned (drum())."""
    fd = Field("Drums")
    s = DRUMS_S
    g = ground_height(DRUMS_C[0], DRUMS_C[1]) - 0.015
    z0 = g + (_d.HOOP_UP + _d.DRUM_D / 2) * s + 0.002
    _d.drum_into(fd, DRUMS_C + v3((0, 0, z0)), (0, 0, 1), (-0.6, -1.0, 0.0), worn=False, s=s)
    z1 = z0 + (_d.DRUM_D + 2 * _d.HOOP_UP) * s + 0.004
    _d.drum_into(fd, DRUMS_C + v3((0.01, -0.01, z1)), norm(v3((0.06, -0.05, 1.0))), (-1.0, -0.4, 0.0), worn=True, s=s)
    return fd


KEG_R, KEG_H = 0.15, 0.38


def keg_field():
    """A powder keg: oak staves (label 11: the grain upright), copper hoops (6), its head (0), a black stencilled band (5)."""
    fd = Field("Keg")
    c = KEG_C + v3((0, 0, ground_height(KEG_C[0], KEG_C[1]) - 0.015))
    def keg(P):
        q = P - c.astype(F)
        z = q[:, 2]
        k = (z - F(KEG_H / 2)) / F(KEG_H / 2)
        r = F(KEG_R) * (F(1) + F(0.12) * (F(1) - k * k))
        rr = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        a = np.arctan2(q[:, 1], q[:, 0])
        stave = F(0.0025) * (F(1) - np.abs(np.cos(a * F(10))))
        return np.maximum(rr - r + stave, np.abs(z - F(KEG_H / 2)) - F(KEG_H / 2))
    fd.add(Func(keg, c - 0.3, c + v3((0.3, 0.3, 0.5))), 0.0, 11)
    fd.sub(Cylinder(c + v3((0, 0, KEG_H + 0.008)), KEG_R * 0.9, 0.03), 0.004)
    for zz in (0.04, 0.12, KEG_H - 0.12, KEG_H - 0.04):
        kk = (zz - KEG_H / 2) / (KEG_H / 2)
        r = KEG_R * (1 + 0.12 * (1 - kk * kk))
        fd.add(Torus(c + v3((0, 0, zz)), r + 0.002, 0.008), 0.002, 6)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(c[2] + KEG_H / 2)) - F(0.035), c - 0.3, c + 0.5), 5)
    return fd


# ---------------------------------------------------------------------------------------------- tropical green
def _leaf(fd, root, d, L, W, droop, seed):
    """A broad leaf on a stalk: arching out along d, drooping at the tip; a midrib groove."""
    rs = np.random.RandomState(seed)
    side = norm(np.cross(d, v3((0, 0, 1))))
    stalk_end = root + d * (L * 0.25) + v3((0, 0, L * 0.2))
    fd.add(RoundCone(root, stalk_end, 0.012, 0.008), 0.004)
    pts, ws, ts, ns = [], [], [], []
    n = 6
    for i in range(n + 1):
        u = i / n
        p = stalk_end + d * (L * 0.75 * u) + v3((0, 0, L * 0.18 * math.sin(u * math.pi) - droop * u * u))
        pts.append(p)
        ws.append(W * (0.35 + 0.9 * math.sin(min(1.0, u * 1.1) * math.pi * 0.95)) * 0.5 + 0.004)
        ts.append(0.006)
        up = norm(v3((0, 0, 1)) + d * (-0.4 + 0.9 * u))
        ns.append(norm(up + side * rs.uniform(-0.25, 0.25)))
    fd.add(Lock(pts, ws, ts, ns, k=0.01), 0.006)


def plants_field():
    """Tropical green at the plinth's foot: a clump of broad leaves (banana-like, label 0), a young fan palm (its
    fronds pleated)."""
    fd = Field("Plants")
    rs = np.random.RandomState(31)
    c = LEAVES_C + v3((0, 0, ground_height(LEAVES_C[0], LEAVES_C[1]) - 0.01))
    for k in range(6):
        a = 2 * math.pi * k / 6 + rs.uniform(-0.3, 0.3)
        d = v3((math.cos(a), math.sin(a), 0.0))
        _leaf(fd, c + d * 0.02, d, rs.uniform(0.32, 0.44), rs.uniform(0.11, 0.15), rs.uniform(0.12, 0.2), 40 + k)
    p = PALM_C + v3((0, 0, ground_height(PALM_C[0], PALM_C[1]) - 0.02))
    trunk_top = p + v3((0.02, 0.0, 0.22))
    fd.add(RoundCone(p, trunk_top, 0.05, 0.035, disp=lambda P: F(0.004) * np.sin(P[:, 2] * F(120)), disp_amp=0.004), 0.0)
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.3
        d = norm(v3((math.cos(a), math.sin(a), 0.55)))
        stem_end = trunk_top + d * 0.2
        fd.add(RoundCone(trunk_top, stem_end, 0.009, 0.007), 0.004)
        side = norm(np.cross(d, v3((0, 0, 1))))
        fan_c = stem_end + d * 0.1 + v3((0, 0, -0.02))
        def fan(P, fan_c=fan_c, d=d, side=side):
            q = P - fan_c.astype(F)
            up = norm(np.cross(side, d))
            u = q @ d.astype(F)
            w = q @ side.astype(F)
            h = q @ up.astype(F)
            ang = np.arctan2(w, u + F(0.1))
            rr = np.sqrt((u + F(0.1)) ** 2 + w * w)
            pleat = F(0.012) * np.abs(np.sin(ang * F(9))) * np.clip(rr / F(0.14), 0, 1)
            return np.maximum(np.maximum(np.abs(h - pleat + F(0.03) * (rr / F(0.2)) ** 2) - F(0.004), np.abs(ang) - F(0.75)),
                              np.maximum(rr - F(0.2), F(0.1) - rr))
        fd.add(Func(fan, fan_c - 0.3, fan_c + 0.3), 0.004)
    return fd


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(37)
    n, tries = 0, 0
    while n < 12 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.05, GROUND_R - 0.05)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if not _free(p, 0.0):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.02, 0.034), seed=340 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def _free(c, pad=0.0):
    for p, rad in ((KEG_C, 0.2), (PALM_C, 0.3), (LEAVES_C, 0.34), (DRUMS_C, 0.2), (POLE_C, 0.12)):
        if np.linalg.norm(c[:2] - p[:2]) < rad + pad:
            return False
    return True


def grass_geometry(seed=59):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.04, GROUND_R - 0.04)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.12 for t in tufts) or not _free(c, 0.02):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(7, 11)
        big = 0.7 + 0.4 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.04)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.2, 0.5) + v3((0, 0, 1)))
            L = rs.uniform(0.1, 0.18) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.042), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=61):
    """Little wild flowers in the grass (swatch 0: white, 1: yellow)."""
    rs = np.random.RandomState(seed)
    spots, tries = [], 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.06, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - s[0][:2]) < 0.25 for s in spots) or not _free(c, 0.04):
            continue
        spots.append((c, 0 if len(spots) % 2 else 1))
    out = []
    for c, col in spots:
        for k in range(rs.randint(2, 5)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.05)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.07, 0.12)
            d = norm(v3((math.cos(ang) * 0.35, math.sin(ang) * 0.35, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, col))
            tilt = norm(v3((rs.uniform(-0.4, 0.4), rs.uniform(-0.4, 0.4), 1.0)))
            _bloom(out, root + d * h, tilt, 0.026, col)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Plinth", plinth_field(), 0.0045), ("Floor", floor_field(), 0.0042),
            ("Pole", pole_field(), 0.003), ("Flag", flag_field(), 0.003), ("Gold", gold_field(), 0.002),
            ("Drums", drums_field(), 0.0028), ("Keg", keg_field(), 0.003), ("Plants", plants_field(), 0.003),
            ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Plinth", "Floor", "Pole", "Flag", "Drums", "Keg")
LOW_TARGETS = {"Ground": 1300, "Plinth": 2600, "Floor": 2600, "Pole": 260, "Flag": 1100, "Gold": 360, "Drums": 2200,
               "Keg": 700, "Plants": 1100, "Pebbles": 300}
_OAK = {"wood": (0.5, 0.35, 0.21), "wood2": (0.37, 0.25, 0.14), "red": (0.08, 0.07, 0.07), "blue": (0.2, 0.32, 0.5), "metal": "bronze"}
MAT_OVERRIDES = {"Plinth": ("stone", {"name": "HQ_FortStone", "moss": True}),
                 "Floor": ("flagstone", {"name": "HQ_ParadeFloor", "base": (0.5, 0.46, 0.42), "alt": (0.6, 0.52, 0.42)}),
                 "Pole": ("siege", dict(_OAK, name="HQ_FortOak")),
                 "Keg": ("siege", dict(_OAK, name="HQ_FortOak")),
                 "Flag": ("wool", {"name": "HQ_Colour", "base": _d.CRIMSON, "border": _d.GOLD, "stripe": _d.GOLD}),
                 "Gold": ("gold", {"name": "HQ_ColourGold"}),
                 "Drums": ("drum", {"name": "HQ_SpareDrums", "shell": _d.CRIMSON, "device": _d.GOLD, "hoop_gold": _d.GOLD}),
                 "Plants": ("leafy", {"name": "HQ_Tropical", "leaf": (0.16, 0.42, 0.12), "vein": (0.42, 0.62, 0.2)}),
                 "Pebbles": ("stone", {"name": "HQ_FortPebble", "scale": 0.3})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and PLINTH_R - 0.01 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
