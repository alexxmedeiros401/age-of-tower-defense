"""Legionary base: a stretch of Roman road at the edge of a legion's camp. A round platform paved with big polygonal blocks
of dark basalt fitted tight (cambered, worn smooth on top, the joints gritty), held by a ring of kerbstones, on a grassy
mound; behind him on his left a training post (a stout oak stake hacked all over by sword cuts); behind him on his right
a rack with three pila leaning on it (long iron shanks, pyramid points, ash shafts with a lead weight); a milestone at the
front right; grass and pebbles (distance fields + direct low-poly geometry for the grass and flowers)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
from sunpriest_base import ring_func

GROUND_R = 1.32
GROUND_TOP = 0.12
KERB_Z = 0.25                      # the kerb's top
TOP_Z = 0.27                       # the paving's crown = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
PAVE_R = 0.6                       # the paving's edge (inside the kerb)
KERB_R = 0.74
POST_C = v3((-0.62, 0.74, 0.0))    # the training post
POST_R = 0.095
POST_H = 1.05
RACK_C = v3((0.64, 0.8, 0.0))      # the pila rack
MILE_C = v3((0.98, -0.42, 0.0))    # the milestone


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.04 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 1.3) + F(0.02) * np.sin(a * 11 + 0.2) + F(0.015) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.04) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def _chip(P):
    return F(0.0035) * NOISE(P * F(9)) + F(0.0018) * NOISE(P * F(31))


_rs = np.random.RandomState(83)
SEEDS = []
while len(SEEDS) < 34:
    a, r = _rs.uniform(0, 2 * math.pi), PAVE_R * math.sqrt(_rs.uniform(0, 1))
    p = np.array([math.cos(a) * r, math.sin(a) * r])
    if all(np.linalg.norm(p - q) > 0.15 for q in SEEDS):
        SEEDS.append(p)
SEEDS = np.array(SEEDS, np.float32)
LIFT = _rs.uniform(-0.004, 0.004, len(SEEDS)).astype(np.float32)


def _cells(P):
    """(distance to the nearest joint between the polygonal blocks, the block's own lift)."""
    d = np.sqrt(((P[:, None, :2] - SEEDS[None, :, :]) ** 2).sum(2))
    idx = np.argsort(d, axis=1)[:, :2]
    d1 = np.take_along_axis(d, idx[:, :1], 1)[:, 0]
    d2 = np.take_along_axis(d, idx[:, 1:2], 1)[:, 0]
    return (d2 - d1) * F(0.5), LIFT[idx[:, 0]]


def paving(P):
    """The road's surface: cambered (highest in the middle), each block domed a little and set a hair high or low, the
    joints sunk between them; down to below the kerb."""
    r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
    edge, lift = _cells(P)
    crown = F(TOP_Z) - F(0.025) * (r / F(PAVE_R)) ** 2 + lift - F(0.012) * np.clip(F(1) - edge / F(0.012), 0, 1) ** 2
    return np.maximum(np.maximum(P[:, 2] - crown, r - F(PAVE_R)), F(GROUND_TOP - 0.06) - P[:, 2])


def stone_field():
    """The paving (basalt, label 0) and the kerb (a lighter stone, 7); the milestone (7) on its plinth."""
    fd = Field("Stone")
    fd.add(Func(paving, (-PAVE_R - 0.02, -PAVE_R - 0.02, GROUND_TOP - 0.08), (PAVE_R + 0.02, PAVE_R + 0.02, TOP_Z + 0.02),
                disp=_chip, disp_amp=0.005), 0.0)
    fd.add(ring_func(PAVE_R - 0.005, KERB_R, 16, 91, KERB_Z, (KERB_Z - GROUND_TOP + 0.06) / 2), 0.0)
    fd.paint(Func(lambda P: F(PAVE_R + 0.004) - np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2), (-0.9, -0.9, GROUND_TOP - 0.1), (0.9, 0.9, KERB_Z + 0.03)), 7)
    g = ground_height(MILE_C[0], MILE_C[1])
    fd.add(RoundBox(MILE_C + v3((0, 0, g + 0.03)), (0.15, 0.15, 0.06), 0.012, disp=_chip, disp_amp=0.005), 0.0, 7)
    fd.add(Cylinder(MILE_C + v3((0, 0, g + 0.09 + 0.25)), 0.11, 0.5, rr=0.03, disp=_chip, disp_amp=0.005), 0.01, 7)
    for k in range(4):                                       # the carved lines of its inscription (on the side to the front)
        z = g + 0.42 - 0.075 * k
        c = MILE_C + v3((-0.02, -0.11, z))
        fd.sub(RoundBox(c, (0.07 - 0.012 * (k % 2), 0.02, 0.008), 0.004, R=rot_from_axes(x_axis=(1, 0, 0), y_axis=(0, 1, 0))), 0.003)
    return fd


# ======================================================================================= the training post, the pila
def _cut(f, c, nrm, size):
    """A sword cut: a thin wedge chopped into a post at c, its blade plane facing nrm."""
    f.sub(Ellipsoid(c, (size, 0.006, size * 0.35), R=rot_from_axes(y_axis=nrm, z_axis=(0, 0, 1))), 0.002)


def pila():
    """Three pila leaning on the rack: (butt, point, the shaft's end) for each."""
    top = RACK_C + v3((0, 0, 0.78))
    out = []
    for k, dx in enumerate((-0.16, 0.0, 0.16)):
        butt = RACK_C + v3((dx * 1.2, -0.24, ground_height(RACK_C[0], RACK_C[1]) - 0.01))
        lean = norm(top + v3((dx, 0.03, 0.0)) - butt)
        out.append((butt, lean))
    return out


def rack_posts():
    g = ground_height(RACK_C[0], RACK_C[1])
    return [RACK_C + v3((-0.24, 0.04, g - 0.03)), RACK_C + v3((0.24, 0.04, g - 0.03))]


def wood_field():
    """The training post (oak, grain along Z: label 11), the rack (two posts and a crossbar: 11 and 10), the pila's ash
    shafts (11), their iron shanks, points and the lead weights (6)."""
    fd = Field("Wood")
    g = ground_height(POST_C[0], POST_C[1])
    base = POST_C + v3((0, 0, g - 0.04))
    fd.add(RoundCone(base, base + v3((0, 0, POST_H)), POST_R * 1.04, POST_R * 0.96,
                     disp=lambda P: F(0.003) * NOISE(P * np.array([40, 40, 6], F)), disp_amp=0.004), 0.0, 11)
    fd.add(Sphere(base + v3((0, 0, POST_H)), POST_R * 0.9, disp=lambda P: F(0.004) * NOISE(P * F(30)), disp_amp=0.004), 0.03, 11)
    rs = np.random.RandomState(5)
    for k in range(16):                                      # cuts all over its front, most at head and chest height
        a = rs.uniform(-1.6, 1.6) - math.pi / 2
        z = base[2] + rs.uniform(0.35, 0.98)
        d = v3((math.cos(a), math.sin(a), 0))
        c = base + d * POST_R * 0.98 + v3((0, 0, z - base[2]))
        tilt = norm(v3((math.cos(a + 1.57), math.sin(a + 1.57), rs.uniform(-0.6, 0.6))))
        _cut(fd, c, np.cross(tilt, d), rs.uniform(0.03, 0.05))
    # the rack
    gtop = ground_height(RACK_C[0], RACK_C[1]) + 0.78
    for p in rack_posts():
        fd.add(RoundCone(p, v3((p[0], p[1], gtop + 0.05)), 0.024, 0.021), 0.0, 11)
    a, b = rack_posts()
    fd.add(RoundCone(v3((a[0] - 0.04, a[1], gtop)), v3((b[0] + 0.04, b[1], gtop)), 0.02, 0.02), 0.006, 10)
    # the pila: an ash shaft, a square block with a lead weight where the shank begins, a long thin iron shank, a point
    for butt, lean in pila():
        L_shaft, L_shank = 0.86, 0.42
        s_end = butt + lean * L_shaft
        fd.add(RoundCone(butt, s_end, 0.015, 0.017), 0.0, 11)
        fd.add(RoundBox(s_end + lean * 0.02, (0.022, 0.022, 0.03), 0.006, R=rot_from_axes(z_axis=lean)), 0.004, 6)
        sh_end = s_end + lean * L_shank
        fd.add(RoundCone(s_end + lean * 0.04, sh_end, 0.0065, 0.0055), 0.002, 6)
        fd.add(RoundCone(sh_end, sh_end + lean * 0.06, 0.012, 0.001), 0.003, 6)
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < KERB_R + 0.06 + pad:
        return True
    if math.hypot(c[0] - POST_C[0], c[1] - POST_C[1]) < 0.16 + pad:
        return True
    if math.hypot(c[0] - MILE_C[0], c[1] - MILE_C[1]) < 0.22 + pad:
        return True
    for p in rack_posts():
        if math.hypot(c[0] - p[0], c[1] - p[1]) < 0.07 + pad:
            return True
    for butt, lean in pila():
        if math.hypot(c[0] - butt[0], c[1] - butt[1]) < 0.06 + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(43)
    n = 0
    tries = 0
    while n < 16 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.82, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.024, 0.046), seed=620 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=47):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.82, GROUND_R - 0.08)
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
            L = rs.uniform(0.12, 0.22) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.042), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=53):
    """A few clumps of yellow and white field flowers."""
    import cretan_base as cb
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 5 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.84, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.04) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.22 for s in spots):
            continue
        spots.append((c, 1))
    for c, col in spots:
        for k in range(rs.randint(3, 6)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.07)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.1, 0.16)
            d = norm(v3((math.cos(ang) * 0.35, math.sin(ang) * 0.35, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, col))
            tilt = norm(v3((rs.uniform(-0.5, 0.5), rs.uniform(-0.5, 0.5), 1.0)))
            cb._bloom(out, root + d * h, tilt, 0.03, col)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Stone", stone_field(), 0.0042), ("Wood", wood_field(), 0.0024),
            ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Stone", "Wood")
LOW_TARGETS = {"Ground": 1500, "Stone": 4200, "Wood": 1500, "Pebbles": 400}
MAT_OVERRIDES = {"Stone": ("flagstone", {"name": "HQ_Basalt", "base": (0.27, 0.27, 0.28), "alt": (0.6, 0.57, 0.5)}),
                 "Wood": ("siege", {"name": "HQ_CampWood", "wood": (0.52, 0.36, 0.22), "wood2": (0.38, 0.25, 0.14), "metal": "iron"})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035 and r > KERB_R + 0.02
    return n.z > 0.55 and on_ground
