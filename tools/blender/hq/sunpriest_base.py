"""Sun Priest base: the sun court of a temple. A round dais of dressed limestone in two steps (curved blocks round a
centre stone, the paving where he stands polished pale by his feet), a sunburst of gold inlaid in the top round his
feet; behind him two small obelisks of red granite on plinths, carved with signs down their faces and capped with gilded
points that catch the light; papyrus, grass, flowers and pebbles round about (distance fields + direct low-poly
geometry for the grass, flowers and papyrus heads)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b

GROUND_R = 1.32
GROUND_TOP = 0.12
LOW_Z = 0.25                       # the lower step's top
TOP_Z = 0.4                        # the dais top = where his feet stand
STAND = v3((0.0, 0.0, TOP_Z))
CENTRE_R = 0.24                    # the centre stone
UPPER_R = 0.62                     # the upper step's edge
LOWER_R = 0.88                     # the lower step's edge
OBELISKS = [v3((sx * 0.56, 0.9, 0.0)) for sx in (-1, 1)]
PLINTH_H = 0.13                    # plinth half size 0.13, top PLINTH_H above the ground
OB_H = 1.02                        # shaft height
OB_W0, OB_W1 = 0.078, 0.052        # shaft half widths, foot and top
CAP_H = 0.1                        # the gilded point
RAYS = 16


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.04 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.03) * np.sin(a * 5 + 2.1) + F(0.02) * np.sin(a * 11 + 0.9) + F(0.015) * NOISE(P * F(3))
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


def _smooth_chip(P):
    """The upper step and the centre stone: dressed fine (the gold is inlaid in them)."""
    return F(0.0012) * NOISE(P * F(9)) + F(0.0006) * NOISE(P * F(31))


def ring_func(r0, r1, n, seed, top, hz, jitter=1.0, chip=_chip):
    """A ring of n curved blocks between radii r0 and r1, joints between them, tops at `top` (each set a little high or
    low and tilted by `jitter`), 2*hz deep."""
    rs = np.random.RandomState(seed)
    ph0 = rs.uniform(0, 2 * math.pi)
    dzs = (rs.uniform(-0.004, 0.003, n) * jitter).astype(F)
    tilt = (rs.uniform(-0.01, 0.01, (n, 2)) * jitter).astype(F)
    gap = F(0.0055)
    rr = F(0.01)
    step = 2 * math.pi / n
    def fn(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.sqrt(x * x + y * y)
        a = np.arctan2(y, x)
        u = (a - F(ph0)) / F(step)
        k = np.floor(u).astype(np.int64) % n
        da = (u - np.floor(u) - F(0.5)) * F(step)
        d_a = np.abs(da) * r - (F(step * 0.5) * r - gap)
        d_r = np.maximum(F(r0) + gap - r, r - (F(r1) - gap))
        rm = F((r0 + r1) / 2)
        t = F(top) + dzs[k] + tilt[k, 0] * (r - rm) + tilt[k, 1] * da * r
        d_z = np.abs(z - (t - F(hz))) - F(hz)
        q = np.stack([d_a + rr, d_r + rr, d_z + rr], 1)
        out = np.sqrt((np.maximum(q, 0) ** 2).sum(1))
        return out + np.minimum(q.max(1), 0) - rr
    R = r1 + 0.02
    return Func(fn, (-R, -R, top - 2 * hz - 0.02), (R, R, top + 0.03), disp=chip, disp_amp=0.006)


def stone_field():
    """The dais (limestone, label 0; the paving where he stands polished pale, 6) and the obelisks' plinths."""
    fd = Field("Stone")
    fd.add(Cylinder(v3((0, 0, (GROUND_TOP - 0.06 + LOW_Z) / 2)), 0.6, LOW_Z - GROUND_TOP + 0.06, rr=0.01), 0.0)   # core (hidden)
    fd.add(ring_func(0.52, LOWER_R, 20, 61, LOW_Z, (LOW_Z - GROUND_TOP + 0.06) / 2), 0.0)
    fd.add(ring_func(CENTRE_R, UPPER_R, 12, 62, TOP_Z, (TOP_Z - LOW_Z + 0.02) / 2, jitter=0.25, chip=_smooth_chip), 0.0)
    fd.add(Cylinder(v3((0, 0, TOP_Z - 0.09)), CENTRE_R - 0.0055, 0.18, rr=0.01, disp=_smooth_chip, disp_amp=0.003), 0.0)
    fd.paint(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(0.36), F(TOP_Z - 0.01) - P[:, 2]),
                  (-0.5, -0.5, TOP_Z - 0.05), (0.5, 0.5, TOP_Z + 0.05)), 6)
    for c in OBELISKS:
        g = ground_height(c[0], c[1])
        fd.add(RoundBox(c + v3((0, 0, g + PLINTH_H / 2 - 0.04)), (0.13, 0.13, PLINTH_H / 2 + 0.04), 0.012, disp=_chip,
                        disp_amp=0.006), 0.004)
        fd.add(RoundBox(c + v3((0, 0, g + PLINTH_H + 0.012)), (0.105, 0.105, 0.016), 0.008, disp=_chip, disp_amp=0.004), 0.003)
    return fd


def _ray(P, base, tip, w0, w1, z0, z1):
    """A flat tapered strip from `base` to `tip` (widths w0 -> w1) between heights z0 and z1."""
    d = tip - base
    L = float(np.linalg.norm(d[:2]))
    ax = d[:2] / L
    sd = np.array([-ax[1], ax[0]])
    q = P[:, :2] - base[:2].astype(F)
    u = q @ ax.astype(F)
    v = np.abs(q @ sd.astype(F))
    t = np.clip(u / F(L), 0, 1)
    w = F(w0) + (F(w1) - F(w0)) * t
    d_l = np.maximum(-u, u - F(L))
    d_w = v - w
    d_z = np.abs(P[:, 2] - F((z0 + z1) / 2)) - F((z1 - z0) / 2)
    q2 = np.stack([d_l, d_w, d_z], 1)
    return np.sqrt((np.maximum(q2, 0) ** 2).sum(1)) + np.minimum(q2.max(1), 0)


def ob_top(c):
    return c + v3((0, 0, ground_height(c[0], c[1]) + PLINTH_H + 0.028 + OB_H))


def gold_field():
    """The inlaid sunburst: a disc, a thin ring round it and sixteen rays, long and short by turns."""
    fd = Field("Gold")
    z0, z1 = TOP_Z - 0.005, TOP_Z + 0.0025
    fd.add(Cylinder(v3((0, 0, (z0 + z1) / 2)), 0.12, z1 - z0, rr=0.001), 0.0)
    fd.add(Torus(v3((0, 0, TOP_Z - 0.0008)), 0.155, 0.0033), 0.0)
    for k in range(RAYS):
        a = 2 * math.pi * (k + 0.5) / RAYS + math.pi / 2
        d = v3((math.cos(a), math.sin(a), 0))
        L = 0.58 if k % 2 == 0 else 0.46
        base, tip = d * 0.17, d * L
        fd.add(Func(lambda P, base=base, tip=tip, w0=(0.03 if k % 2 == 0 else 0.022): _ray(P, base, tip, w0, 0.003, z0, z1),
                    np.minimum(base, tip) + v3((-0.04, -0.04, z0 - 0.002)), np.maximum(base, tip) + v3((0.04, 0.04, z1 + 0.002))), 0.0)
    return fd


def caps_field():
    """The obelisks' gilded points (their own part: with the inlay its bounds would span the whole court)."""
    fd = Field("Caps")
    for c in OBELISKS:
        t = ob_top(c)
        def pyr(P, t=t):
            q = P - t.astype(F)
            h = F(CAP_H)
            # a square pyramid: base half width OB_W1 at q.z = 0, apex at q.z = h
            s = F(OB_W1) * (F(1) - np.clip(q[:, 2] / h, 0, 1))
            d_side = np.maximum(np.abs(q[:, 0]), np.abs(q[:, 1])) - s
            n = F(1.0 / math.sqrt(1 + (OB_W1 / CAP_H) ** 2))
            return np.maximum(d_side * n, np.maximum(-q[:, 2] - F(0.004), q[:, 2] - h))
        fd.add(Func(pyr, t - v3((OB_W1 + 0.02, OB_W1 + 0.02, 0.02)), t + v3((OB_W1 + 0.02, OB_W1 + 0.02, CAP_H + 0.02))), 0.0)
    return fd


def _glyphs(fd, c):
    """Signs sunk into the obelisk's front face (toward the dais): a sun disc, bars, water, a ring, an ankh, a bird."""
    g = ground_height(c[0], c[1]) + PLINTH_H + 0.028
    toward = norm(v3((-c[0], -c[1], 0)))                  # the face that looks at the dais
    side = norm(np.cross(v3((0, 0, 1)), toward))
    # the faces stay square to X/Y: use the axis face closest to `toward`
    if abs(toward[0]) > abs(toward[1]):
        nrm, sd = v3((math.copysign(1, toward[0]), 0, 0)), v3((0, 1, 0))
    else:
        nrm, sd = v3((0, math.copysign(1, toward[1]), 0)), v3((1, 0, 0))
    def face_pt(h, u):
        w = OB_W0 + (OB_W1 - OB_W0) * (h / OB_H)
        return c + v3((0, 0, g + h)) + nrm * w + sd * u
    R = rot_from_axes(z_axis=nrm, x_axis=sd)
    dep = 0.004
    fd.sub(Cylinder(face_pt(0.9, 0), 0.026, dep * 2, rr=0.0015, R=R), 0.002)                       # the sun
    for h in (0.83, 0.805):
        fd.sub(RoundBox(face_pt(h, 0), (0.03, 0.005, dep), 0.002, R=R), 0.0015)                      # bars
    zz = [face_pt(0.74, u) + nrm * 0.0 for u in (-0.033, -0.02, -0.007, 0.007, 0.02, 0.033)]
    for i, p in enumerate(zz):
        zz[i] = p + v3((0, 0, 0.008 if i % 2 else -0.008))
    fd.sub(Chain(zz, [0.0045] * len(zz), k=0.002), 0.0015)                                           # water
    fd.sub(Torus(face_pt(0.64, 0), 0.02, 0.0045, R=R), 0.0015)                                       # a ring
    # an ankh
    fd.sub(Torus(face_pt(0.535, 0), 0.013, 0.0045, R=R @ np.diag([1.25, 0.8, 1.0])), 0.0015)          # (the loop taller than wide)
    fd.sub(Chain([face_pt(0.515, 0), face_pt(0.42, 0)], [0.005, 0.005]), 0.0015)
    fd.sub(Chain([face_pt(0.5, -0.026), face_pt(0.5, 0.026)], [0.0045, 0.0045]), 0.0015)
    # a bird (a falcon in profile: body, head, tail)
    fd.sub(Ellipsoid(face_pt(0.33, 0.0), (0.024, 0.013, dep * 1.2), R=R @ euler(0, 0, 0.35)), 0.0015)
    fd.sub(Ellipsoid(face_pt(0.352, -0.022), (0.0085, 0.0085, dep), R=R), 0.0015)
    fd.sub(Chain([face_pt(0.322, 0.018), face_pt(0.3, 0.034)], [0.006, 0.003]), 0.0015)
    fd.sub(Chain([face_pt(0.315, -0.004), face_pt(0.28, -0.012)], [0.0035, 0.003]), 0.0015)
    fd.sub(Chain([face_pt(0.315, 0.006), face_pt(0.28, 0.004)], [0.0035, 0.003]), 0.0015)
    for h in (0.22, 0.195):
        fd.sub(RoundBox(face_pt(h, 0), (0.03, 0.005, dep), 0.002, R=R), 0.0015)


def granite_field():
    """Two obelisks of red granite, tapering, carved on the face toward the dais."""
    fd = Field("Granite")
    for c in OBELISKS:
        g = ground_height(c[0], c[1]) + PLINTH_H + 0.028
        def shaft(P, c=c, g=g):
            q = P - (c + v3((0, 0, g))).astype(F)
            t = np.clip(q[:, 2] / F(OB_H), 0, 1)
            w = F(OB_W0) + F(OB_W1 - OB_W0) * t
            rr = F(0.004)
            dx = np.abs(q[:, 0]) - w + rr
            dy = np.abs(q[:, 1]) - w + rr
            dz = np.abs(q[:, 2] - F(OB_H / 2)) - F(OB_H / 2) + rr
            qq = np.stack([dx, dy, dz], 1)
            return (np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0) - rr) * F(0.995)
        lo = c + v3((-OB_W0 - 0.02, -OB_W0 - 0.02, g - 0.02))
        hi = c + v3((OB_W0 + 0.02, OB_W0 + 0.02, g + OB_H + 0.02))
        fd.add(Func(shaft, lo, hi, disp=lambda P: F(0.0008) * NOISE(P * F(25)), disp_amp=0.001), 0.0)
        _glyphs(fd, c)
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < LOWER_R + 0.08 + pad:
        return True
    for o in OBELISKS:
        if abs(c[0] - o[0]) < 0.2 + pad and abs(c[1] - o[1]) < 0.2 + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(23)
    n = 0
    tries = 0
    while n < 14 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(LOWER_R + 0.06, GROUND_R - 0.05)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.0):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.022, 0.04), seed=400 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=41):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 24 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(LOWER_R + 0.07, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, -0.02):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.13 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(7, 12)
        big = 0.65 + 0.4 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.045)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.2, 0.5) + v3((0, 0, 1)))
            L = rs.uniform(0.11, 0.2) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.04), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


PAPYRUS = [(1.04, -0.42, 0.4), (-1.06, -0.36, 2.2), (-0.98, 0.5, 1.1)]


def flower_geometry(seed=43):
    """A few flowers (kinds 0-2) and papyrus clumps crowned with bursts of thin rays (kind 3, the papyrus swatch)."""
    rs = np.random.RandomState(seed)
    out = []
    spots = []
    tries = 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(LOWER_R + 0.1, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.03) or any(np.linalg.norm(c[:2] - s[0][:2]) < 0.22 for s in spots):
            continue
        if any(math.hypot(c[0] - x, c[1] - y) < 0.2 for x, y, _ in PAPYRUS):
            continue
        spots.append((c, rs.randint(0, 3)))
    for c, kind in spots:
        base = v3((c[0], c[1], ground_height(c[0], c[1]) - 0.01))
        h = rs.uniform(0.1, 0.14)
        top = base + v3((rs.uniform(-0.02, 0.02), rs.uniform(-0.02, 0.02), h))
        sv, sf, _ = _b.blade_mesh(base, top - base, h, 0.012, (0, 0, 0), segs=2)
        out.append((sv, sf, 0, kind))
        tilt = norm(v3((rs.uniform(-0.3, 0.3), rs.uniform(-0.5, -0.1), 1.0)))
        R = rot_from_axes(z_axis=tilt)
        pv, pf = [], []
        for k in range(5):
            a = 2 * math.pi * k / 5
            dirk = R @ v3((math.cos(a), math.sin(a), 0.12))
            sidek = R @ v3((-math.sin(a), math.cos(a), 0))
            b0 = len(pv)
            pv += [top + tilt * 0.004, top + dirk * 0.034 * 0.55 + sidek * 0.034 * 0.42, top + dirk * 0.034, top + dirk * 0.034 * 0.55 - sidek * 0.034 * 0.42]
            pf.append((b0, b0 + 1, b0 + 2, b0 + 3))
        out.append((pv, pf, 1, kind))
        cv = [top + R @ v3((math.cos(2 * math.pi * k / 6) * 0.012, math.sin(2 * math.pi * k / 6) * 0.012, 0.008)) for k in range(6)]
        cv.append(top + R @ v3((0, 0, 0.016)))
        out.append((cv, [(k, (k + 1) % 6, 6) for k in range(6)], 2, kind))
    for (x, y, a0) in PAPYRUS:
        for k in range(6):
            ang = a0 + k * 1.05
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.06)
            root = v3((x, y, 0)) + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.4, 0.6)
            d = norm(v3((math.cos(ang) * 0.14, math.sin(ang) * 0.14, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.016, v3((math.cos(ang), math.sin(ang), 0)) * 0.08, segs=4)
            out.append((sv, sf, 0, 0))
            top = root + d * h
            for j in range(11):
                aj = 2 * math.pi * j / 11 + k
                rd = norm(v3((math.cos(aj), math.sin(aj), 0)) * 0.9 + d * 0.5)
                rv, rf, _ = _b.blade_mesh(top, rd, rs.uniform(0.08, 0.11), 0.01, v3((0, 0, -0.35)), segs=2)
                out.append((rv, rf, 3, 3))
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Stone", stone_field(), 0.0042), ("Gold", gold_field(), 0.0018),
            ("Caps", caps_field(), 0.0016), ("Granite", granite_field(), 0.0018), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Stone",)
LOW_TARGETS = {"Ground": 1300, "Stone": 3600, "Gold": 640, "Caps": 40, "Granite": 420, "Pebbles": 300}
MAT_OVERRIDES = {"Stone": ("limestone", {"name": "HQ_SunDais"}),
                 "Gold": ("gold", {"name": "HQ_BaseGold"}), "Caps": ("gold", {"name": "HQ_BaseGold"}),
                 "Granite": ("granite", {"name": "HQ_Granite"}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
EXTRA_SWATCHES = [(0.56, 0.7, 0.24)]          # kind 3: papyrus heads
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and LOWER_R + 0.02 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.06))
