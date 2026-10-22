"""Musketeer base: a corner of a star fort's bastion, on a round plinth of cut stone (two battered courses) rising from
the turf. Its top is trodden earth with flagstones set in it where he stands; behind him the bastion's parapet: two
faces of cut stone meeting at a blunt salient, capped with turf, an embrasure through the left face flanked by two
gabions (wicker baskets of earth) standing on the parapet; a powder keg with a lantern on it at the plinth's edge on his
right; a small crimson-and-gold flag on a staff at the salient; at the edge, a fern and a young palm for the colonial
jungle; grass and pebbles round the plinth's foot (distance fields + direct low-poly geometry for the grass).

Everything on the plinth stands clear of where the rest's spike and the musket's butt go as the tower turns (beyond
r = 0.8), and below the barrel's line on the aim."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
from sunpriest_base import ring_func
from crossbowman_base import _bloom

GROUND_R = 1.34
GROUND_TOP = 0.08
PLINTH_R = 1.08                    # the plinth's top edge
TOP_Z = 0.24                       # the floor = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
CLEAR_R = 0.8                      # (nothing on the floor inside this: the rest's spike and the musket's butt sweep it)
FACE_A = math.radians(65.0)        # the parapet's faces: inner faces tangent to CLEAR_R at 65 and 115 degrees
PAR_T = 0.16                       # the parapet's thickness
PAR_H = 0.34                       # its stone above the floor
TURF_H = 0.08                      # the turf cap on it
EMB_S = 0.32                       # the embrasure: along the left face from its tangent point
EMB_W0, EMB_W1 = 0.07, 0.15        # its half widths at the inner and the outer face
EMB_SILL = 0.16                    # its sill above the floor
KEG_C = v3((-0.925, -0.2, TOP_Z))  # the powder keg (on his right, at the plinth's edge)
KEG_R, KEG_H = 0.13, 0.3
FLAG_C = v3((0.0, 0.0, 0.0))       # (set below: on the turf at the salient)
PALM_C = v3((-0.98, 0.7, 0.0))     # the young palm (behind him on his right, outside the parapet)
FERN_C = v3((1.0, -0.72, 0.0))     # the fern (before him on his left, at the edge)


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def ground_height(x, y):
    r = math.hypot(x, y)
    if r < PLINTH_R - 0.02:
        return TOP_Z
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


# ---------------------------------------------------------------------------------------------- the plinth and floor
def masonry_field():
    """The plinth: cut stone (label 0; weathered dark and green low down, 7) in two courses, the upper one set back (a
    battered wall), on a hidden core."""
    fd = Field("Masonry")
    fd.add(Cylinder(v3((0, 0, 0.04)), PLINTH_R - 0.06, 0.2, rr=0.01), 0.0)
    fd.add(ring_func(0.72, PLINTH_R + 0.035, 19, 701, TOP_Z - 0.095, 0.055, jitter=0.7, chip=_chip), 0.0)
    fd.add(ring_func(0.72, PLINTH_R + 0.005, 17, 703, TOP_Z - 0.004, 0.045, jitter=0.5, chip=_chip), 0.0)
    fd.paint(Func(lambda P: (P[:, 2] - F(TOP_Z - 0.13)) + F(0.04) * NOISE(P * F(4)), (-1.3, -1.3, -0.2), (1.3, 1.3, 0.4)), 7)
    return fd


FLAGS = [(0.0, 0.02, 0.3, 0.25, 0.1), (-0.27, -0.2, 0.2, 0.18, -0.4), (0.25, -0.24, 0.21, 0.17, 0.5), (-0.05, -0.4, 0.22, 0.15, 0.2),
         (0.3, 0.12, 0.18, 0.15, -0.3), (-0.33, 0.1, 0.17, 0.2, 0.3), (0.06, 0.3, 0.2, 0.14, -0.2), (-0.5, -0.4, 0.15, 0.13, 0.7),
         (0.5, -0.38, 0.14, 0.12, -0.6)]                    # (x, y, half length, half width, turn)


def floor_field():
    """Trodden earth over the plinth's top (label 5: bare earth)."""
    fd = Field("Floor")
    def top(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        dz = P[:, 2] - (F(TOP_Z - 0.008) + F(0.004) * NOISE(P * F(6)))
        return np.maximum(dz, np.maximum(r - F(PLINTH_R - 0.02), F(TOP_Z - 0.06) - P[:, 2]))
    fd.add(Func(top, (-1.15, -1.15, TOP_Z - 0.1), (1.15, 1.15, TOP_Z + 0.03), disp=_fine, disp_amp=0.002), 0.0)
    fd.paint(Func(lambda P: P[:, 2] - F(TOP_Z + 0.05), (-1.2, -1.2, TOP_Z - 0.12), (1.2, 1.2, TOP_Z + 0.06)), 5)
    return fd


def flags_field():
    """Flagstones set in the earth where he stands (label 0; a browner stone for some, 7)."""
    fd = Field("Flags")
    for i, (x, y, hl, hw, a) in enumerate(FLAGS):
        c = v3((x, y, TOP_Z - 0.012))
        fd.add(RoundBox(c, (hl, hw, 0.014), 0.012, R=euler(0.012 * math.sin(i), 0.01 * math.cos(i * 1.7), a), disp=_fine, disp_amp=0.003), 0.0,
               7 if i % 3 == 1 else 0)
    return fd


# ---------------------------------------------------------------------------------------------- the parapet
def _face_frame(sx):
    """The face on his left (sx = 1) or right (-1): its outward normal n, the direction along it away from the salient."""
    a = FACE_A if sx > 0 else math.pi - FACE_A
    n = v3((math.cos(a), math.sin(a), 0.0))
    along = v3((sx * math.sin(FACE_A), -math.cos(FACE_A), 0.0))
    return n, along


def _par_local(P):
    """(t: out through the wall from its inner face, s: along it from the inner face's tangent point, side)."""
    x = P[:, 0]
    out_t, out_s = [], []
    for sx in (1, -1):
        n, along = _face_frame(sx)
        out_t.append(P @ n.astype(F) - F(CLEAR_R))
        out_s.append(P @ along.astype(F))
    t = np.where(x >= 0, out_t[0], out_t[1])
    s = np.where(x >= 0, out_s[0], out_s[1])
    return t, s


def _wall(P, extra=0.0):
    """The parapet's stone: from its inner face (t = 0) out to its battered outer face, the floor up to PAR_H, cut off at
    the plinth's edge."""
    t, s = _par_local(P)
    z = P[:, 2] - F(TOP_Z)
    batter = F(0.06) * np.clip((F(PAR_H) - z) / F(PAR_H), 0, 1)
    d = np.maximum(np.maximum(-t - F(extra), t - F(PAR_T + extra) - batter), np.maximum(z - F(PAR_H + extra), F(-0.1) - z))
    r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
    return np.maximum(d, r - F(PLINTH_R + 0.03))


def _embrasure(P):
    """< 0 inside the embrasure's notch (left face): splayed from the inner face out, down to its sill."""
    n, along = _face_frame(1)
    t = P @ n.astype(F) - F(CLEAR_R)
    s = P @ along.astype(F) - F(EMB_S)
    k = np.clip(t / F(PAR_T + 0.1), 0, 1)
    half = F(EMB_W0) + F(EMB_W1 - EMB_W0) * k
    return np.maximum(np.maximum(np.abs(s) - half, F(TOP_Z + EMB_SILL) - P[:, 2]), -P[:, 0])


def _joints(P):
    """Displacement: mortar joints between courses of cut blocks on the parapet's faces."""
    t, s = _par_local(P)
    z = P[:, 2] - F(TOP_Z)
    row = np.floor(z / F(0.113))
    dz = np.abs(z - (row + F(0.5)) * F(0.113)) - F(0.0565)
    sh = np.where(np.mod(row, 2) == 0, F(0.0), F(0.13))
    u = s + sh + F(0.02) * np.sin(row * F(1.7))
    dsv = np.abs(np.mod(u, F(0.26)) - F(0.13)) - F(0.13)
    j = np.minimum(np.abs(dz), np.abs(dsv))
    return F(0.005) * smoothstep(0.007, 0.0, j)


def parapet_field():
    """Cut stone (label 0; weathered green and dark low down, 7) in courses, the embrasure through the left face."""
    fd = Field("Parapet")
    lo, hi = (-1.15, 0.0, TOP_Z - 0.12), (1.15, 1.15, TOP_Z + PAR_H + 0.03)
    fd.add(Func(lambda P: _wall(P), lo, hi, disp=lambda P: _joints(P) + _chip(P), disp_amp=0.011), 0.0)
    fd.sub(Func(_embrasure, (0.2, 0.2, TOP_Z + 0.1), (0.9, 1.0, TOP_Z + PAR_H + 0.12)), 0.012)
    fd.paint(Func(lambda P: (P[:, 2] - F(TOP_Z + 0.08)) + F(0.05) * NOISE(P * F(5)), lo, hi), 7)
    return fd


def turf_field():
    """The turf cap on the parapet: a rounded bank of earth, grass on its top (the ground material colours it)."""
    fd = Field("Turf")
    def cap(P):
        t, s = _par_local(P)
        z = P[:, 2] - F(TOP_Z + PAR_H)
        e = np.sqrt(((t - F(PAR_T / 2)) / F(PAR_T / 2 + 0.018)) ** 2 + (z / F(TURF_H)) ** 2) - F(1.0)
        d = np.maximum(e * F(TURF_H), F(-0.02) - z)
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.maximum(d, r - F(PLINTH_R + 0.03)), -_embrasure(P))
    fd.add(Func(cap, (-1.15, 0.0, TOP_Z + PAR_H - 0.04), (1.15, 1.15, TOP_Z + PAR_H + TURF_H + 0.03),
                disp=lambda P: F(0.006) * NOISE(P * F(9)) + F(0.003) * NOISE(P * F(28)), disp_amp=0.01), 0.0)
    return fd


def turf_top(x, y):
    """The turf's top height at (x, y) on the parapet (for standing things on it)."""
    return TOP_Z + PAR_H + TURF_H * 0.92


def face_point(sx, s, t):
    n, along = _face_frame(sx)
    return n * (CLEAR_R + t) + along * s


# ---------------------------------------------------------------------------------------------- gabions, keg, lantern, flag
GABIONS = [(EMB_S - 0.25, 0.13), (EMB_S + 0.25, 0.125)]     # (along the left face, radius)
GAB_H = 0.27


def gabion_spots():
    out = []
    for s, r in GABIONS:
        c = face_point(1, s, PAR_T / 2)
        out.append((v3((c[0], c[1], turf_top(c[0], c[1]) - 0.035)), r))
    return out


def gabions_field():
    """Two gabions on the parapet flanking the embrasure: wicker (label 8) woven between upright stakes (11), filled
    with earth (9) heaped in their tops."""
    fd = Field("Gabions")
    for i, (c, r) in enumerate(gabion_spots()):
        def basket(P, c=c, r=r):
            q = P - c.astype(F)
            a = np.arctan2(q[:, 1], q[:, 0])
            rr = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
            z = q[:, 2]
            bulge = F(0.012) * np.sin(np.clip(z / F(GAB_H), 0, 1) * F(math.pi))
            weave = F(0.004) * np.sin(z * F(150) + np.where(np.mod(np.floor(a * F(14 / math.pi)), 2) == 0, F(0), F(math.pi)))
            side = rr - (F(r) + bulge + weave)
            return np.maximum(side, np.maximum(-z, z - F(GAB_H)))
        lo, hi = c - v3((r + 0.05, r + 0.05, 0.02)), c + v3((r + 0.05, r + 0.05, GAB_H + 0.08))
        fd.add(Func(basket, lo, hi), 0.0, 8)
        fd.sub(Cylinder(c + v3((0, 0, GAB_H)), r - 0.012, 0.05), 0.004)
        fd.add(Ellipsoid(c + v3((0, 0, GAB_H - 0.02)), (r - 0.008, r - 0.008, 0.05), disp=lambda P: F(0.006) * NOISE(P * F(14)), disp_amp=0.006), 0.006, 9)
        for k in range(14):
            a = 2 * math.pi * (k + 0.5) / 14
            p0 = c + v3((math.cos(a) * (r + 0.004), math.sin(a) * (r + 0.004), -0.01))
            fd.add(RoundCone(p0, p0 + v3((0, 0, GAB_H + 0.03)), 0.0075, 0.006), 0.002, 11)
    return fd


def keg_field():
    """The powder keg (oak staves, grain upright: 11) with iron hoops (6), a bung; the lantern standing on it: an iron
    frame (6) round its horn panes, a pierced cap and a ring to carry it by (the panes glow: the Glass part)."""
    fd = Field("Keg")
    c = KEG_C
    def keg(P):
        q = P - c.astype(F)
        z = q[:, 2]
        k = (z - F(KEG_H / 2)) / F(KEG_H / 2)
        r = F(KEG_R) * (F(1) + F(0.12) * (F(1) - k * k))
        rr = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        a = np.arctan2(q[:, 1], q[:, 0])
        stave = F(0.0025) * (F(1) - np.abs(np.cos(a * F(9))))
        return np.maximum(rr - r + stave, np.abs(z - F(KEG_H / 2)) - F(KEG_H / 2))
    fd.add(Func(keg, c - 0.3, c + v3((0.3, 0.3, 0.4))), 0.0, 11)
    fd.sub(Cylinder(c + v3((0, 0, KEG_H + 0.004)), KEG_R * 0.9, 0.012), 0.003)
    for zz in (0.045, 0.1, KEG_H - 0.1, KEG_H - 0.045):
        kk = (zz - KEG_H / 2) / (KEG_H / 2)
        fd.add(Torus(c + v3((0, 0, zz)), KEG_R * (1 + 0.12 * (1 - kk * kk)) + 0.002, 0.0075), 0.002, 6)
    fd.add(Cylinder(c + v3((KEG_R * 0.55, 0.0, KEG_H - 0.004)), 0.018, 0.012, rr=0.003), 0.003, 11)
    # the lantern
    L0 = c + v3((-0.01, 0.02, KEG_H - 0.006))
    w, h = 0.05, 0.13
    fd.add(RoundBox(L0 + v3((0, 0, 0.012)), (w + 0.008, w + 0.008, 0.012), 0.004), 0.0, 6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(RoundCone(L0 + v3((sx * w, sy * w, 0.02)), L0 + v3((sx * w, sy * w, h)), 0.0055, 0.0055), 0.002, 6)
    fd.add(RoundBox(L0 + v3((0, 0, h + 0.006)), (w + 0.008, w + 0.008, 0.008), 0.004), 0.003, 6)
    fd.add(RoundCone(L0 + v3((0, 0, h + 0.012)), L0 + v3((0, 0, h + 0.05)), w * 0.85, 0.01), 0.004, 6)
    fd.add(Torus(L0 + v3((0, 0, h + 0.075)), 0.024, 0.005, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, 6)
    return fd


def glass_field():
    """The lantern's horn panes round the candle (its own glowing mesh)."""
    fd = Field("Glass")
    L0 = KEG_C + v3((-0.01, 0.02, KEG_H - 0.006))
    fd.add(RoundBox(L0 + v3((0, 0, 0.076)), (0.046, 0.046, 0.054), 0.008), 0.0)
    return fd


def flag_base():
    c = face_point(1, 0.0, PAR_T / 2)
    c[0] = 0.0
    c[1] = CLEAR_R / math.sin(FACE_A) + PAR_T / 2 / math.sin(FACE_A)
    return v3((0.0, c[1] - 0.02, turf_top(0, c[1]) - 0.05))


FLAG_TOP_Z = 1.5                           # (below the barrel's line on the aim, wherever he turns)


def staff_field():
    """The flag's staff (ash, grain upright: 11) with an iron ball and spike at its top (6)."""
    fd = Field("Staff")
    b = flag_base()
    top = v3((b[0], b[1], FLAG_TOP_Z))
    fd.add(RoundCone(b, top, 0.016, 0.013, disp=lambda P: F(0.0012) * NOISE(P * np.array([60, 60, 8], F)), disp_amp=0.0015), 0.0, 11)
    fd.add(Sphere(top + v3((0, 0, 0.018)), 0.02), 0.004, 6)
    fd.add(RoundCone(top + v3((0, 0, 0.03)), top + v3((0, 0, 0.07)), 0.011, 0.002), 0.004, 6)
    return fd


FLAG_W, FLAG_H = 0.34, 0.22


def flag_field():
    """A small flag of crimson wool (label 0) with a gold-ochre saltire and border (5), streaming out to his right."""
    fd = Field("Flag")
    b = flag_base()
    top = v3((b[0], b[1] + 0.005, FLAG_TOP_Z - 0.02))
    out = norm(v3((-1.0, 0.25, 0.0)))
    side = norm(np.cross(out, v3((0, 0, 1))))
    def cloth(P):
        q = P - top.astype(F)
        s = q @ out.astype(F)
        z = -q[:, 2]
        k = np.clip(s / F(FLAG_W), 0, 1)
        wave = F(0.035) * np.sin(s * F(11) + F(0.4)) * k + F(0.008) * np.sin(s * F(27))
        h = q @ side.astype(F) - wave
        droop = F(0.05) * k * k
        zz = z - droop
        return np.maximum(np.maximum(np.maximum(-s, s - F(FLAG_W)), np.maximum(-zz, zz - F(FLAG_H))), np.abs(h) - F(0.006))
    lo, hi = top - v3((0.5, 0.3, 0.4)), top + v3((0.2, 0.3, 0.1))
    fd.add(Func(cloth, lo, hi, disp=lambda P: F(0.0008) * NOISE(P * F(40)), disp_amp=0.001), 0.0)
    def emblem(P):
        q = P - top.astype(F)
        sm = q @ out.astype(F)
        zm = -q[:, 2] - F(0.05) * np.clip(sm / F(FLAG_W), 0, 1) ** 2
        edge = np.minimum(np.minimum(sm, F(FLAG_W) - sm), np.minimum(zm, F(FLAG_H) - zm))
        u, w = sm / F(FLAG_W), zm / F(FLAG_H)
        d1 = np.abs(u - w) * F(FLAG_H) - F(0.016)
        d2 = np.abs(u + w - F(1)) * F(FLAG_H) - F(0.016)
        return np.minimum(edge - F(0.02), np.minimum(d1, d2))
    fd.paint(Func(emblem, lo, hi), 5)
    return fd


# ---------------------------------------------------------------------------------------------- the jungle at the edge
def _leaflets(fd, pts, side_dir, L0, label, seed, thin=0.0032):
    """Paired leaflets along a frond's rib (pts), shrinking toward its tip."""
    rs = np.random.RandomState(seed)
    n = len(pts) - 1
    for i in range(1, 15):
        u = i / 15
        s = u * n
        j = min(int(s), n - 1)
        p = lerp(pts[j], pts[j + 1], s - j)
        t = norm(pts[j + 1] - pts[j])
        sd = norm(side_dir - t * float(side_dir @ t))
        size = L0 * (1.0 - 0.7 * u) * (0.55 + 0.45 * math.sin(math.pi * min(1.0, u * 1.5)))
        for sg in (-1, 1):
            d = norm(sd * sg + t * 0.55 + v3((0, 0, -0.25)))
            c = p + d * size * 0.95
            fd.add(Ellipsoid(c, (size, thin, size * 0.22), R=rot_from_axes(x_axis=d, y_axis=v3((0, 0, 1)) - d * d[2])), 0.003, label)


def _frond(fd, root, d, L, droop, side_dir, leaf, label_rib, label_leaf, seed, width=0.006):
    pts = []
    for k in range(7):
        u = k / 6
        pts.append(root + d * (L * u) + v3((0, 0, 0.18 * L * math.sin(math.pi * u * 0.8) - droop * L * u * u)))
    fd.add(Chain(pts, [width * (1.0 - 0.6 * k / 6) for k in range(7)], k=0.003), 0.003, label_rib)
    _leaflets(fd, pts, side_dir, leaf, label_leaf, seed)


def palm_field():
    """A young palm: a short trunk ringed with old leaf scars (bark, 0), a crown of arching pinnate fronds (leaves:
    the Fronds part)."""
    fd = Field("Palm")
    g = ground_height(PALM_C[0], PALM_C[1])
    b = v3((PALM_C[0], PALM_C[1], g - 0.04))
    top = b + v3((0.04, -0.03, 0.62))
    scars = lambda P: F(0.006) * np.abs(np.sin(P[:, 2] * F(70))) + F(0.002) * NOISE(P * F(30))
    fd.add(Chain([b, lerp(b, top, 0.5) + v3((0.015, 0, 0)), top], [0.075, 0.058, 0.05], k=0.02, disp=scars, disp_amp=0.007), 0.0)
    fd.add(Ellipsoid(b + v3((0, 0, 0.03)), (0.12, 0.12, 0.07)), 0.04)
    return fd


def palm_top():
    g = ground_height(PALM_C[0], PALM_C[1])
    return v3((PALM_C[0], PALM_C[1], g - 0.04)) + v3((0.04, -0.03, 0.62))


def fronds_field():
    """The palm's fronds (leaf green, label 0; their ribs, 7)."""
    fd = Field("Fronds")
    top = palm_top()
    rs = np.random.RandomState(17)
    for k in range(7):
        a = 2 * math.pi * k / 7 + rs.uniform(-0.2, 0.2)
        el = rs.uniform(0.35, 0.75)
        d = norm(v3((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el))))
        sd = norm(np.cross(v3((0, 0, 1)), d))
        _frond(fd, top + d * 0.03, d, rs.uniform(0.42, 0.55), 0.55, sd, 0.075, 7, 0, 100 + k, width=0.008)
    fd.add(Ellipsoid(top + v3((0, 0, 0.03)), (0.05, 0.05, 0.07)), 0.02, 7)
    return fd


def fern_field():
    """A fern at the plinth's foot (leaf green, label 0; the stems, 7)."""
    fd = Field("Fern")
    rs = np.random.RandomState(23)
    g = ground_height(FERN_C[0], FERN_C[1])
    c = FERN_C + v3((0, 0, g - 0.01))
    for k in range(8):
        a = 2 * math.pi * k / 8 + rs.uniform(-0.2, 0.2)
        d = norm(v3((math.cos(a), math.sin(a), 0.9)))
        sd = norm(np.cross(v3((0, 0, 1)), d))
        _frond(fd, c + v3((math.cos(a) * 0.02, math.sin(a) * 0.02, 0.0)), d, rs.uniform(0.26, 0.34), 0.4, sd, 0.05, 7, 0, 200 + k)
    return fd


# ---------------------------------------------------------------------------------------------- pebbles, grass
def _blocked(c, pad=0.0):
    r = math.hypot(c[0], c[1])
    if r < PLINTH_R + 0.06 + pad:
        return True
    for p, rad in ((PALM_C, 0.18), (FERN_C, 0.2)):
        if math.hypot(c[0] - p[0], c[1] - p[1]) < rad + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(61)
    n, tries = 0, 0
    while n < 12 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.06, GROUND_R - 0.06)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, -0.03):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.024, 0.045), seed=780 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=67):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 26 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.08, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.0):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.13 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(8, 13)
        big = 0.75 + 0.5 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.05)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            outv = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(outv * rs.uniform(0.15, 0.45) + v3((0, 0, 1)))
            L = rs.uniform(0.12, 0.24) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.044), outv * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=71):
    """A few orange tropical blooms (swatch 3) in the grass."""
    rs = np.random.RandomState(seed)
    out = []
    spots, tries = [], 0
    while len(spots) < 5 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.1, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.03) or any(np.linalg.norm(c[:2] - s[:2]) < 0.25 for s in spots):
            continue
        spots.append(c)
    for c in spots:
        for k in range(rs.randint(2, 4)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.05)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.08, 0.14)
            d = norm(v3((math.cos(ang) * 0.3, math.sin(ang) * 0.3, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.011, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, 3))
            tilt = norm(v3((rs.uniform(-0.4, 0.4), rs.uniform(-0.4, 0.4), 1.0)))
            _bloom(out, root + d * h, tilt, 0.03, 3)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Masonry", masonry_field(), 0.0045), ("Floor", floor_field(), 0.0045),
            ("Flags", flags_field(), 0.0035), ("Parapet", parapet_field(), 0.0042), ("Turf", turf_field(), 0.0045),
            ("Gabions", gabions_field(), 0.003), ("Keg", keg_field(), 0.0024), ("Glass", glass_field(), 0.002),
            ("Staff", staff_field(), 0.0024), ("Flag", flag_field(), 0.0024), ("Palm", palm_field(), 0.003),
            ("Fronds", fronds_field(), 0.0024), ("Fern", fern_field(), 0.0024), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Masonry", "Floor", "Flags", "Parapet", "Gabions", "Keg", "Staff", "Flag", "Fronds", "Fern")
LOW_TARGETS = {"Ground": 1500, "Masonry": 3400, "Floor": 900, "Flags": 900, "Parapet": 2600, "Turf": 1000, "Gabions": 1500,
               "Keg": 900, "Glass": 60, "Staff": 200, "Flag": 380, "Palm": 500, "Fronds": 1500, "Fern": 900, "Pebbles": 380}
_CRIMSON = (0.55, 0.08, 0.08)
_GOLD = (0.85, 0.62, 0.2)
_WOOD = {"wood": (0.52, 0.36, 0.21), "wood2": (0.4, 0.27, 0.15), "red": _GOLD, "blue": _CRIMSON, "metal": "iron"}
MAT_OVERRIDES = {"Masonry": ("stone", {"name": "HQ_FortStone", "moss": True}),
                 "Floor": ("ground", {"name": "HQ_FortFloor", "dirt_label": 5}),
                 "Flags": ("flagstone", {"name": "HQ_FortFlags"}),
                 "Parapet": ("stone", {"name": "HQ_FortParapet", "moss": True}),
                 "Turf": ("ground", {"name": "HQ_FortTurf"}),
                 "Gabions": ("siege", dict(_WOOD, name="HQ_Gabion")),
                 "Keg": ("siege", dict(_WOOD, name="HQ_Keg")),
                 "Glass": ("glow_ball", {"name": "HQ_LanternGlow", "col": (1.0, 0.78, 0.4), "strength": 2.0}),
                 "Staff": ("siege", dict(_WOOD, name="HQ_Keg")),
                 "Flag": ("wool", {"name": "HQ_FortFlag", "base": _CRIMSON, "border": _GOLD, "stripe": _GOLD}),
                 "Palm": ("bark_wood", {"name": "HQ_PalmTrunk", "bark": (0.42, 0.32, 0.2), "wood": (0.7, 0.58, 0.4)}),
                 "Fronds": ("leafy", {"name": "HQ_Fronds", "leaf": (0.2, 0.44, 0.12), "vein": (0.42, 0.62, 0.2), "twig": (0.38, 0.42, 0.16)}),
                 "Fern": ("leafy", {"name": "HQ_Fronds", "leaf": (0.2, 0.44, 0.12), "vein": (0.42, 0.62, 0.2), "twig": (0.38, 0.42, 0.16)}),
                 "Pebbles": ("stone", {"name": "HQ_FortPebbles", "scale": 0.3})}
GLOW = {"Glass": ((1.0, 0.74, 0.36), 1.1, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = PLINTH_R + 0.04 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
    return n.z > 0.55 and on_ground and not _blocked((c.x, c.y), -0.1)
