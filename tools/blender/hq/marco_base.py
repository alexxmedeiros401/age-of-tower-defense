"""Marco's stand: a corner of a fort's powder magazine. A round floor of grey flagstones in rings, worn where he stands,
a ring of darker kerb stones in it with twelve ember-orange glass roundels set in brass cups (the hero ring, their own
emissive mesh); behind him on his left the corner of the magazine's walls (cut limestone in courses, a coping on top)
standing on the floor's rim, and in the corner a stack of powder kegs (two standing, one lying across them); against the
back wall an open crate of grenades packed in straw, its lid propped against it; behind him on his right the army's flag
on a short pole: crimson, a gold border and a gold flaming grenade; before him on his left an iron brazier of glowing
coals (a small flame flickers on them in game) and the slow match coiled on the flags beside it, its end smouldering;
before him on his right a few sandbags. Round it all the fort's trampled earth, grass at its rim (distance fields + grass
and flowers as direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
import kael_base as kb
from sunpriest_base import ring_func
import marco as _mc

GROUND_R = 1.32
GROUND_TOP = 0.1
TOP_Z = 0.26                       # the floor's top = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
FLOOR_R = 0.98
KERB_R0, KERB_R1 = 0.62, 0.72      # the ring of darker kerb stones the roundels are set in
RING_R = 0.67
N_GLOW = 12
WALL_D = 1.08                      # the walls: three straight runs round behind him (an angle of the magazine), their
WALL_NORMALS = (47.0, 90.0, 133.0) # centre lines this far out, facing these ways (degrees from his left, round behind)
WALL_HT = 0.12                     # half their thickness
WALL_TOP = TOP_Z + 0.36
COURSE = 0.09
def _polar(deg, r):
    return v3((r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)), TOP_Z))


BRAZIER = _polar(-30, 0.84)
COIL = _polar(-4, 0.86)
SANDBAGS = _polar(212, 0.85)
POLE = _polar(161, 0.86)
POLE_H = 1.3


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    """The fort's earth round the magazine floor: trampled bare (label 5) but for a grassy rim."""
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
    fd.paint(Func(lambda P: np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(1.1) - F(0.06) * NOISE(P * F(4)), (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3)), 5)
    return fd


def _chip(P):
    return F(0.0026) * NOISE(P * F(11)) + F(0.0014) * NOISE(P * F(37))


def floor_field():
    """Grey flagstones (label 0) in rings round a centre slab, worn pale where he stands (6: grit); a ring of browner kerb
    stones (7); soot by the brazier (5)."""
    fd = Field("Floor")
    hz = (TOP_Z - GROUND_TOP + 0.08) / 2
    fd.add(Cylinder(v3((0, 0, TOP_Z - 0.09)), 0.2 - 0.0055, 0.18, rr=0.01, disp=_chip, disp_amp=0.004), 0.0)
    fd.add(ring_func(0.2, 0.42, 8, 811, TOP_Z, hz, jitter=0.4, chip=_chip), 0.0)
    fd.add(ring_func(0.42, KERB_R0, 12, 817, TOP_Z, hz, jitter=0.4, chip=_chip), 0.0)
    fd.add(ring_func(KERB_R0, KERB_R1, 16, 823, TOP_Z - 0.004, hz, jitter=0.3, chip=_chip), 0.0)
    fd.add(ring_func(KERB_R1, FLOOR_R, 18, 829, TOP_Z, hz, jitter=0.8, chip=_chip), 0.0)
    lo, hi = (-1.1, -1.1, GROUND_TOP - 0.2), (1.1, 1.1, TOP_Z + 0.03)
    fd.paint(Func(lambda P: np.maximum(np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F((KERB_R0 + KERB_R1) / 2)) - F(0.05), F(TOP_Z - 0.03) - P[:, 2]),
                  lo, hi), 7)
    fd.paint(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(0.3), F(TOP_Z - 0.01) - P[:, 2]), lo, hi), 6)
    fd.paint(Func(lambda P: np.sqrt((P[:, 0] - F(BRAZIER[0])) ** 2 + (P[:, 1] - F(BRAZIER[1])) ** 2) - F(0.2) - F(0.05) * NOISE(P * F(8)), lo, hi), 5)
    return fd


def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + math.pi / N_GLOW
    return v3((math.cos(a) * RING_R, math.sin(a) * RING_R, TOP_Z - 0.004))


def glowstones_field():
    fd = Field("Glowstones")
    for i in range(N_GLOW):
        fd.add(Ellipsoid(glow_pos(i), (0.03, 0.03, 0.013)), 0.0)
    return fd


def brass_field():
    """Brass: the roundels' cups, the flag's finial, the brazier's ring handles."""
    fd = Field("Brass")
    for i in range(N_GLOW):
        fd.add(Torus(glow_pos(i) + v3((0, 0, -0.001)), 0.033, 0.0075), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the magazine's walls
def _runs():
    """The walls' runs as (start, end) on their centre lines, from his left round behind him to his right."""
    out = []
    pts = []
    for i in range(len(WALL_NORMALS) - 1):                  # the corners: where neighbouring runs meet
        a1, a2 = math.radians(WALL_NORMALS[i]), math.radians(WALL_NORMALS[i + 1])
        m = (a1 + a2) / 2
        r = WALL_D / math.cos((a2 - a1) / 2)
        pts.append(v3((r * math.cos(m), r * math.sin(m), 0.0)))
    half = math.radians((WALL_NORMALS[1] - WALL_NORMALS[0]) / 2)
    a0 = math.radians(WALL_NORMALS[0]) - half
    a3 = math.radians(WALL_NORMALS[-1]) + half
    r_end = WALL_D / math.cos(half)
    ends = [v3((r_end * math.cos(a0), r_end * math.sin(a0), 0.0))] + pts + [v3((r_end * math.cos(a3), r_end * math.sin(a3), 0.0))]
    for i in range(len(ends) - 1):
        out.append((ends[i], ends[i + 1]))
    return out


def wall_inner(theta):
    """Along the direction theta from the middle, how far until the walls' inner faces (inf if none)."""
    d = v3((math.cos(theta), math.sin(theta), 0.0))
    best = 9.0
    for a, b in _runs():
        t = norm(b - a)
        n = v3((-t[1], t[0], 0.0))
        if n @ a < 0:
            n = -n                                         # (pointing away from the middle)
        dist = float(n @ a) - WALL_HT
        c = float(d @ n)
        if c <= 1e-3:
            continue
        r = dist / c
        p = d * r
        u = float((p - a) @ t)
        if -WALL_HT <= u <= float(np.linalg.norm(b - a)) + WALL_HT:
            best = min(best, r)
    return best


def place(theta, clear):
    """The point at angle theta where a round thing of radius `clear` stands against the walls."""
    lo, hi = 0.3, 1.2
    d = v3((math.cos(theta), math.sin(theta), 0.0))
    for _ in range(40):
        m = (lo + hi) / 2
        p = d * m
        ok = True
        for a, b in _runs():
            t = norm(b - a)
            L = float(np.linalg.norm(b - a))
            u = min(max(float((p - a) @ t), 0.0), L)
            if np.linalg.norm(p - (a + t * u)) < WALL_HT + clear:
                ok = False
        if ok:
            lo = m
        else:
            hi = m
    return d * lo


def _wall_run(a, b, seed):
    t = norm(b - a)
    n = v3((-t[1], t[0], 0.0))
    L = float(np.linalg.norm(b - a))
    c = (a + b) / 2
    z0, z1 = GROUND_TOP - 0.06, WALL_TOP
    rs = np.random.RandomState(seed)
    offs = rs.uniform(0, 0.3, 12)
    def fn(P):
        q = P - c.astype(F)
        u = q @ t.astype(F)
        w = q @ n.astype(F)
        z = P[:, 2]
        du = np.abs(u) - F(L / 2 + WALL_HT * 0.9)
        dw = np.abs(w) - F(WALL_HT)
        dz = np.abs(z - F((z0 + z1) / 2)) - F((z1 - z0) / 2)
        qq = np.stack([du + F(0.012), dw + F(0.012), dz + F(0.012)], 1)
        return np.sqrt((np.maximum(qq, 0) ** 2).sum(1)) + np.minimum(qq.max(1), 0) - F(0.012)
    def joints(P):
        q = P - c.astype(F)
        u = q @ t.astype(F) + F(L / 2 + 0.5)
        z = P[:, 2] - F(TOP_Z)
        row = np.floor(z / F(COURSE))
        fz = z / F(COURSE) - row
        jz = np.minimum(fz, F(1) - fz)
        blk = F(0.26)
        st = np.take(offs, (row.astype(np.int64) % 12))
        fu = np.mod(u + st.astype(F), blk) / blk
        ju = np.minimum(fu, F(1) - fu)
        groove = np.maximum(F(1) - jz / F(0.07), F(0.0)) + np.maximum(F(1) - ju / F(0.03), F(0.0))
        return F(0.004) * np.minimum(groove, F(1.0)) + _chip(P)
    m = L / 2 + 0.3
    cs = [c + t * (su * m) + n * (sn * 0.2) for su in (-1, 1) for sn in (-1, 1)]
    lo, hi = np.minimum.reduce(cs), np.maximum.reduce(cs)
    return Func(fn, (lo[0], lo[1], z0 - 0.02), (hi[0], hi[1], z1 + 0.02), disp=joints, disp_amp=0.008)


def wall_field():
    """Cut limestone in courses (label 0), a coping slab along the top, standing on the floor's rim."""
    fd = Field("Wall")
    for i, (a, b) in enumerate(_runs()):
        fd.add(_wall_run(a, b, 900 + i), 0.0)
        t = norm(b - a)
        n = v3((-t[1], t[0], 0.0))
        L = float(np.linalg.norm(b - a))
        c = (a + b) / 2
        fd.add(RoundBox(c + v3((0, 0, WALL_TOP + 0.025)), (L / 2 + WALL_HT + 0.02, WALL_HT + 0.022, 0.028), 0.01,
                        R=np.stack([t, n, v3((0, 0, 1))], axis=1), disp=_chip, disp_amp=0.004), 0.004)
    return fd


# ---------------------------------------------------------------------------------------------- kegs, crate, shot
def keg_func(c, ax, h, r0, r1):
    """A barrel: from c (the middle of one head) along ax for h, its heads r0, its belly r1; staves (shallow grooves)."""
    ax = norm(ax)
    e = norm(np.cross(ax, v3((0, 0, 1)) if abs(ax[2]) < 0.9 else v3((1, 0, 0))))
    f = np.cross(ax, e)
    def fn(P):
        q = P - c.astype(F)
        z = q @ ax.astype(F)
        x, y = q @ e.astype(F), q @ f.astype(F)
        k = np.clip(z / F(h), 0, 1)
        r = F(r0) + F(r1 - r0) * np.sin(k * F(math.pi))
        a = np.arctan2(y, x)
        rr = np.sqrt(x * x + y * y)
        d_r = rr - r + F(0.0016) * np.abs(np.sin(a * F(10))) ** 0.3
        d_z = np.abs(z - F(h / 2)) - F(h / 2)
        qq = np.stack([np.maximum(d_r + F(0.008), 0), np.maximum(d_z + F(0.008), 0)], 1)
        return np.sqrt((qq ** 2).sum(1)) + np.minimum(np.maximum(d_r + F(0.008), d_z + F(0.008)), 0) - F(0.008)
    mid = c + ax * (h / 2)
    ext = np.abs(ax) * (h / 2) + r1 * np.sqrt(np.maximum(1.0 - ax * ax, 0.0)) + 0.02
    return Func(fn, mid - ext, mid + ext, disp=lambda P: F(0.0012) * NOISE(P * F(40)), disp_amp=0.0015)


KEG_H, KEG_R0, KEG_R1 = 0.3, 0.1, 0.122


def keg_spots():
    """The stack in the corner: two kegs standing side by side against the walls, a third lying across their tops."""
    p1 = place(math.radians(50), KEG_R1 + 0.012)
    p2 = place(math.radians(70), KEG_R1 + 0.012)
    if np.linalg.norm(p1 - p2) < 2 * KEG_R1 + 0.02:
        mid = (p1 + p2) / 2
        d = norm(p2 - p1)
        p1, p2 = mid - d * (KEG_R1 + 0.012), mid + d * (KEG_R1 + 0.012)
    return [v3((p[0], p[1], TOP_Z)) for p in (p1, p2)]


def kegs_field():
    """Oak powder kegs (label 0; their staves' grain upright: 11, along the lying one: 10), iron hoops (6)."""
    fd = Field("Kegs")
    s1, s2 = keg_spots()
    for c in (s1, s2):
        fd.add(keg_func(c, v3((0, 0, 1)), KEG_H, KEG_R0, KEG_R1), 0.0, 11)
        for zf in (0.07, 0.22, 0.78, 0.93):
            r = KEG_R0 + (KEG_R1 - KEG_R0) * math.sin(zf * math.pi)
            fd.add(Torus(c + v3((0, 0, KEG_H * zf)), r + 0.001, 0.006), 0.003, 6)
        fd.sub(Cylinder(c + v3((0, 0, KEG_H + 0.002)), KEG_R0 - 0.013, 0.012, rr=0.003), 0.003)
    ax = norm(s2 - s1)
    mid = (s1 + s2) / 2 + v3((0, 0, KEG_H + KEG_R0 + 0.004))
    a0 = mid - ax * (KEG_H / 2)
    fd.add(keg_func(a0, ax, KEG_H, KEG_R0, KEG_R1), 0.004, 10)
    for zf in (0.07, 0.22, 0.78, 0.93):
        r = KEG_R0 + (KEG_R1 - KEG_R0) * math.sin(zf * math.pi)
        fd.add(Torus(a0 + ax * (KEG_H * zf), r + 0.001, 0.006, R=rot_from_axes(z_axis=ax)), 0.003, 6)
    for c in (a0, a0 + ax * KEG_H):
        fd.sub(Cylinder(c, KEG_R0 - 0.013, 0.012, rr=0.003, R=rot_from_axes(z_axis=ax)), 0.003)
    return fd


CRATE_HALF = (0.19, 0.1, 0.095)        # along the wall, out from it, up


def crate_frame():
    """The crate against the back wall behind him on his right: its middle, its long axis (along the wall), its depth
    axis (out from the wall, toward the middle)."""
    a, b = _runs()[2]                                      # (squarely against the run behind him on his right)
    t = norm(b - a)
    n = v3((-t[1], t[0], 0.0))
    if n @ a > 0:
        n = -n                                             # (toward the middle)
    mid = (a + b) / 2
    c = mid + n * (WALL_HT + 0.025 + CRATE_HALF[1]) + t * 0.07
    return v3((c[0], c[1], TOP_Z + CRATE_HALF[2])), t, n


def crate_field():
    """An open crate of planks (label 0: grain along it, 10 along its end battens)."""
    fd = Field("Crate")
    c, t, n = crate_frame()
    hx, hy, hz = CRATE_HALF
    R = np.stack([t, n, v3((0, 0, 1))], axis=1)
    fd.add(RoundBox(c, (hx, hy, hz), 0.008, R=R, disp=lambda P: F(0.001) * NOISE(P * F(40)), disp_amp=0.0015), 0.0)
    fd.sub(RoundBox(c + v3((0, 0, 0.03)), (hx - 0.016, hy - 0.016, hz), 0.004, R=R), 0.002)                    # open
    for sx in (-1, 1):                                                                                         # end battens
        fd.add(RoundBox(c + t * (sx * (hx + 0.006)), (0.008, hy + 0.004, hz + 0.002), 0.004, R=R), 0.003, 10)
    for k in (-1, 1):                                                                                          # planks' seams
        fd.sub(RoundBox(c + v3((0, 0, k * hz * 0.34)), (hx + 0.02, hy + 0.003, 0.0018), 0.001, R=R), 0.001)
    return fd


def straw_field():
    """Straw packed round the grenades in the crate (label 5: darker, damp)."""
    fd = Field("Straw")
    c, t, n = crate_frame()
    hx, hy, hz = CRATE_HALF
    R = np.stack([t, n, v3((0, 0, 1))], axis=1)
    fib = lambda P: F(0.004) * NOISE(P * np.array([30, 30, 60], F)) + F(0.002) * NOISE(P * F(90))
    fd.add(RoundBox(c + v3((0, 0, hz * 0.45)), (hx - 0.02, hy - 0.02, hz * 0.45), 0.02, R=R, disp=fib, disp_amp=0.006), 0.0)
    rs = np.random.RandomState(44)
    for k in range(14):                                                                                         # wisps over the rim
        p = c + t * rs.uniform(-hx, hx) + n * rs.uniform(-hy, hy) * 0.9 + v3((0, 0, hz * 0.9))
        d = norm(rs.normal(size=3) * v3((1, 1, 0.3)))
        fd.add(RoundCone(p, p + d * rs.uniform(0.04, 0.07), 0.004, 0.002), 0.002)
    return fd


def shot_spots():
    c, t, n = crate_frame()
    hx, hy, hz = CRATE_HALF
    out = []
    for i, (u, v) in enumerate(((-0.62, -0.4), (-0.18, 0.38), (0.26, -0.36), (0.66, 0.34), (0.05, -0.02), (-0.5, 0.42))):
        out.append((c + t * (u * (hx - 0.06)) + n * (v * (hy - 0.05)) + v3((0, 0, hz * 0.62 + 0.012 * (i % 2))), i))
    return out


def shot_field():
    """The grenades nestled in the straw: black iron (label 0), wooden fuse plugs (5)."""
    fd = Field("Shot")
    rs = np.random.RandomState(7)
    for p, i in shot_spots():
        fd.add(Sphere(p, 0.05, disp=lambda P: F(0.0012) * NOISE(P * F(55)), disp_amp=0.0014), 0.0)
        d = norm(rs.normal(size=3) * v3((1, 1, 0.4)) + v3((0, 0, 1.2)))
        fd.add(RoundCone(p + d * 0.042, p + d * 0.066, 0.012, 0.0095), 0.003, 5)
    return fd


# ---------------------------------------------------------------------------------------------- flag, brazier, match, sandbags
FLAG_W, FLAG_H = 0.44, 0.3


def flag_frame():
    top = POLE + v3((0, 0, POLE_H))
    out = norm(v3((0.55, 0.62, 0.0)))                      # the flag flies toward the back, over the crate
    return top, out


def wood_field():
    """The flag's pole (ash, grain along it: 11) on a stone foot, iron-shod (6)."""
    fd = Field("Wood")
    top, out = flag_frame()
    fd.add(RoundCone(POLE + v3((0, 0, -0.02)), top + v3((0, 0, 0.02)), 0.022, 0.017,
                     disp=lambda P: F(0.0012) * NOISE(P * np.array([60, 60, 8], F)), disp_amp=0.0015), 0.0, 11)
    fd.add(Cylinder(POLE + v3((0, 0, 0.03)), 0.028, 0.06, rr=0.006), 0.004, 6)
    fd.add(Stone(POLE + v3((0, 0, 0.03)), 0.075, seed=71, squash=(1.0, 1.0, 0.55), noise=0.04), 0.01, 0)
    return fd


def finial_field():
    fd = Field("Finial")
    top, out = flag_frame()
    fd.add(Sphere(top + v3((0, 0, 0.035)), 0.024), 0.0)
    fd.add(RoundCone(top + v3((0, 0, 0.05)), top + v3((0, 0, 0.12)), 0.016, 0.002), 0.005)
    return fd


def flag_field():
    """Crimson wool (label 0), a gold border (5), a gold flaming grenade (6); it hangs from the pole in a gentle wave."""
    fd = Field("Flag")
    top, out = flag_frame()
    up = v3((0, 0, 1))
    nrm = norm(np.cross(out, up))
    def cloth(P):
        q = P - (top - up * 0.03).astype(F)
        s = q @ out.astype(F)                                # out along the flag from the pole
        h = -(q @ up.astype(F))                              # down from its top edge
        w = q @ nrm.astype(F)
        wave = F(0.03) * np.sin(s * F(14) + F(0.5)) * np.clip(s / F(FLAG_W), 0, 1) + F(0.006) * np.sin(h * F(20))
        sag = F(0.05) * (s / F(FLAG_W)) ** 2
        d = np.maximum(np.maximum(-s + F(0.012), s - F(FLAG_W)), np.maximum(-(h - sag) - F(0.0), (h - sag) - F(FLAG_H)))
        return np.maximum(d, np.abs(w - wave) - F(0.007))
    cs = [top + out * so + up * sz + nrm * sn for so in (-0.05, FLAG_W + 0.05) for sz in (0.02, -FLAG_H - 0.12) for sn in (-0.08, 0.08)]
    lo, hi = np.minimum.reduce(cs), np.maximum.reduce(cs)
    fd.add(Func(cloth, lo, hi, disp=lambda P: F(0.0008) * NOISE(P * F(40)), disp_amp=0.001), 0.0)
    def coords(P):
        q = P - (top - up * 0.03).astype(F)
        s = q @ out.astype(F)
        h = -(q @ up.astype(F)) - F(0.05) * (s / F(FLAG_W)) ** 2
        return s, h
    def border(P):
        s, h = coords(P)
        inner = np.maximum(np.maximum(F(0.035) - s, s - F(FLAG_W - 0.035)), np.maximum(F(0.03) - h, h - F(FLAG_H - 0.03)))
        return -inner
    fd.paint(Func(border, lo, hi), 5)
    def emblem(P):
        s, h = coords(P)
        return _mc.badge_2d(s, -h, (FLAG_W * 0.5, -FLAG_H * 0.52), 0.21)
    fd.paint(Func(emblem, lo, hi), 6)
    return fd


BRAZ_R = 0.13
BRAZ_Z = 0.36                          # its bowl's rim above the floor


def iron_field():
    """The brazier (forged iron): a round bowl with a rolled rim on three splayed legs, a ring handle each side."""
    fd = Field("Iron")
    c = BRAZIER + v3((0, 0, BRAZ_Z))
    bowl = Field("Bowl")
    bowl.add(Sphere(c + v3((0, 0, 0.02)), BRAZ_R), 0.0)
    fd.add(Inter(Shell(bowl, 0.0, 0.012, pad=0.05), Plane(c, (0, 0, 1)), 0.004), 0.0)
    fd.add(Torus(c, BRAZ_R * 0.995, 0.01), 0.004)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        d = v3((math.cos(a), math.sin(a), 0.0))
        p0 = c + d * (BRAZ_R * 0.75) + v3((0, 0, -0.07))
        p1 = BRAZIER + d * (BRAZ_R + 0.035) + v3((0, 0, 0.012))
        fd.add(Chain([p0, lerp(p0, p1, 0.5) + d * 0.015, p1], [0.011, 0.01, 0.012], k=0.005), 0.006)
        fd.add(Sphere(p1 + v3((0, 0, -0.004)), 0.017), 0.004)
    for s in (-1, 1):
        d = v3((s * 1.0, 0.0, 0.0))
        fd.add(Torus(c + d * (BRAZ_R + 0.026) + v3((0, 0, -0.03)), 0.026, 0.0055, R=rot_from_axes(z_axis=(0, 1, 0))), 0.003)
    return fd


def coals_field():
    """Dark coal lumps heaped in the bowl, over the glowing bed."""
    fd = Field("Coals")
    c = BRAZIER + v3((0, 0, BRAZ_Z))
    rs = np.random.RandomState(13)
    for k in range(11):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.0, BRAZ_R * 0.72)
        p = c + v3((math.cos(a) * r, math.sin(a) * r, 0.005 + 0.03 * (1 - r / BRAZ_R)))
        fd.add(Stone(p, rs.uniform(0.022, 0.034), seed=300 + k, squash=(1.0, 1.0, 0.7), noise=0.05), 0.004)
    return fd


def embers_field():
    """The glowing bed of the brazier (its own emissive mesh)."""
    fd = Field("Embers")
    c = BRAZIER + v3((0, 0, BRAZ_Z))
    fd.add(Ellipsoid(c + v3((0, 0, -0.004)), (BRAZ_R * 0.86, BRAZ_R * 0.86, 0.035), disp=lambda P: F(0.006) * NOISE(P * F(16)), disp_amp=0.008), 0.0)
    return fd


def flame_field():
    fd = Field("Flame")
    c = BRAZIER + v3((0, 0, BRAZ_Z + 0.03))
    fd.add(Ellipsoid(c, (0.07, 0.07, 0.05)), 0.0)
    fd.add(RoundCone(c, c + v3((0.005, 0.0, 0.17)), 0.055, 0.004), 0.04)
    return fd


def coil_pts():
    """The slow match coiled flat on the flags (three turns), its free end trailing toward the brazier."""
    pts = []
    for k in range(43):
        u = k / 42.0
        a = 2 * math.pi * 3 * u
        r = 0.035 + 0.06 * u
        pts.append(COIL + v3((math.cos(a) * r, math.sin(a) * r, 0.012 + 0.009 * (1 - abs(2 * u - 1)) * 0.0)))
    last = pts[-1]
    to = norm(BRAZIER - COIL)
    pts += [last + to * 0.04 + v3((0, 0, 0.004)), last + to * 0.08 + v3((0.01, 0.0, 0.03)), last + to * 0.1 + v3((0.02, 0.0, 0.06))]
    return pts


def rope_field():
    fd = Field("Rope")
    pts = coil_pts()
    tw = lambda P: F(0.0012) * np.sin(P[:, 0] * F(400) + P[:, 1] * F(400))
    fd.add(Chain(pts, [0.0105] * len(pts), k=0.004, disp=tw, disp_amp=0.0014), 0.0)
    return fd


def match_glow_field():
    fd = Field("MatchGlow")
    pts = coil_pts()
    fd.add(Sphere(pts[-1], 0.014), 0.0)
    fd.add(RoundCone(pts[-2], pts[-1], 0.009, 0.012), 0.004)
    return fd


def sandbags_field():
    """Three sandbags of sacking (label 0), tied at their necks (6): two side by side on the flags, one on them."""
    fd = Field("Sandbags")
    weave = lambda P: F(0.0014) * (np.sin(P[:, 0] * F(260)) + np.sin(P[:, 1] * F(260))) + F(0.003) * NOISE(P * F(9))
    a = math.atan2(SANDBAGS[1], SANDBAGS[0])
    t = v3((-math.sin(a), math.cos(a), 0.0))               # along the bags: round the floor's edge
    n = v3((-t[1], t[0], 0.0))
    specs = [(SANDBAGS + n * 0.076 + v3((0, 0, 0.055)), 0.0), (SANDBAGS - n * 0.076 + v3((0, 0, 0.055)), 0.0),
             (SANDBAGS + v3((0, 0, 0.15)) + t * 0.02, 0.25)]
    for c, rot in specs:
        tt = norm(t * math.cos(rot) + n * math.sin(rot))
        R = np.stack([tt, np.cross(v3((0, 0, 1)), tt), v3((0, 0, 1))], axis=1)
        fd.add(Ellipsoid(c, (0.17, 0.08, 0.058), R=R, disp=weave, disp_amp=0.004), 0.012)
        neck = c + tt * 0.17
        fd.add(Ellipsoid(neck + tt * 0.02, (0.03, 0.028, 0.026), R=R, disp=weave, disp_amp=0.004), 0.01)
        fd.add(Torus(neck + tt * 0.004, 0.024, 0.006, R=rot_from_axes(z_axis=tt)), 0.003, 6)
    return fd


def ball_spots():
    """A few iron round shot by the brazier."""
    b = _polar(-63, 0.8)
    r = 0.055
    return [b + v3((-r, 0, r)), b + v3((r, 0, r)), b + v3((0, r * 1.7, r)), b + v3((0, r * 0.57, r * 2.63))]


def balls_field():
    fd = Field("Balls")
    for p in ball_spots():
        fd.add(Sphere(p, 0.055, disp=lambda P: F(0.0012) * NOISE(P * F(50)), disp_amp=0.0014), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- scatter
def _blocked(c, pad=0.0):
    r = math.hypot(c[0], c[1])
    if r < FLOOR_R + 0.06 + pad:
        return True
    for a, b in _runs():
        t = norm(b - a)
        L = float(np.linalg.norm(b - a))
        p = v3((c[0], c[1], 0.0))
        u = min(max(float((p - a) @ t), -0.1), L + 0.1)
        if np.linalg.norm(p - (a + t * u)) < WALL_HT + 0.1 + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(83)
    n = 0
    tries = 0
    while n < 12 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(1.0, 1.26)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.0):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.024, 0.044), seed=880 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=91):
    old = kb._blocked
    kb._blocked = _blocked
    try:
        return kb.grass_geometry(seed)
    finally:
        kb._blocked = old


def flower_geometry(seed=93):
    old = kb._blocked
    kb._blocked = _blocked
    try:
        return kb.flower_geometry(seed)
    finally:
        kb._blocked = old


def fields():
    return [("Ground", ground_field(), 0.008), ("Floor", floor_field(), 0.0042), ("Glowstones", glowstones_field(), 0.0025),
            ("Brass", brass_field(), 0.002), ("Wall", wall_field(), 0.005), ("Kegs", kegs_field(), 0.0032),
            ("Crate", crate_field(), 0.0026), ("Straw", straw_field(), 0.003), ("Shot", shot_field(), 0.0024),
            ("Wood", wood_field(), 0.0026), ("Finial", finial_field(), 0.0018), ("Flag", flag_field(), 0.0024),
            ("Iron", iron_field(), 0.0024), ("Coals", coals_field(), 0.003), ("Embers", embers_field(), 0.004),
            ("Rope", rope_field(), 0.0024), ("MatchGlow", match_glow_field(), 0.0018), ("Sandbags", sandbags_field(), 0.0034),
            ("Balls", balls_field(), 0.0026), ("Pebbles", pebbles_field(), 0.004), ("Flame", flame_field(), 0.004)]


REGION_PARTS = ("Ground", "Floor", "Kegs", "Crate", "Shot", "Wood", "Flag", "Sandbags")
LOW_TARGETS = {"Ground": 1300, "Floor": 3400, "Glowstones": 300, "Brass": 400, "Wall": 1500, "Kegs": 1100, "Crate": 600,
               "Straw": 500, "Shot": 400, "Wood": 400, "Finial": 100, "Flag": 500, "Iron": 700, "Coals": 400, "Embers": 160,
               "Rope": 500, "MatchGlow": 60, "Sandbags": 600, "Balls": 300, "Pebbles": 300, "Flame": 160}
WOOD_C, WOOD2_C = (0.5, 0.33, 0.18), (0.37, 0.23, 0.12)
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_FortGround", "dirt_label": 5}),
                 "Floor": ("flagstone", {"name": "HQ_MagazineFloor", "base": (0.44, 0.43, 0.41), "alt": (0.56, 0.5, 0.42)}),
                 "Brass": ("bronze", {"name": "HQ_MagazineBrass", "base": (0.8, 0.6, 0.24), "hi": (1.0, 0.92, 0.6),
                                      "dark": (0.38, 0.25, 0.08), "patina": (0.42, 0.44, 0.24)}),
                 "Finial": ("gold", {"name": "HQ_FlagFinial"}),
                 "Wall": ("limestone", {"name": "HQ_FortLimestone"}),
                 "Kegs": ("siege", {"name": "HQ_BaseKegs", "wood": WOOD_C, "wood2": WOOD2_C, "metal": "iron"}),
                 "Crate": ("siege", {"name": "HQ_GrenadeCrate", "wood": (0.6, 0.45, 0.28), "wood2": (0.46, 0.33, 0.2), "metal": "iron"}),
                 "Straw": ("reed", {"name": "HQ_Straw", "base": (0.78, 0.68, 0.38)}),
                 "Shot": ("iron", {"name": "HQ_CrateGrenades", "col": {"base": (0.1, 0.1, 0.11), "hi": (0.46, 0.47, 0.5),
                                                                        "dark": (0.03, 0.03, 0.035), "rust": (0.26, 0.15, 0.08)},
                                   "wood": (0.62, 0.46, 0.28)}),
                 "Balls": ("iron", {"name": "HQ_RoundShot", "col": {"base": (0.16, 0.16, 0.17), "hi": (0.52, 0.53, 0.56),
                                                                     "dark": (0.05, 0.05, 0.055), "rust": (0.36, 0.2, 0.1)}}),
                 "Wood": ("siege", {"name": "HQ_FlagPole", "wood": (0.62, 0.47, 0.3), "wood2": (0.48, 0.35, 0.21), "metal": "iron"}),
                 "Flag": ("wool", {"name": "HQ_GunpowderFlag", "base": _mc.CRIMSON, "border": _mc.GOLD, "stripe": _mc.GOLD}),
                 "Iron": ("iron", {"name": "HQ_Brazier", "col": {"base": (0.16, 0.16, 0.17), "hi": (0.5, 0.5, 0.52),
                                                                  "dark": (0.05, 0.05, 0.05), "rust": (0.42, 0.2, 0.08)}}),
                 "Coals": ("coals", {}),
                 "Rope": ("leather", {"name": "HQ_SlowMatch", "base": (0.44, 0.36, 0.24)}),
                 "Sandbags": ("linen", {"name": "HQ_Sacking", "base": (0.66, 0.56, 0.38), "border": (0.4, 0.3, 0.18),
                                        "stripe": (0.36, 0.27, 0.16)}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
GLOW = {"Glowstones": ((1.0, 0.46, 0.1), 1.0, 0.5), "Embers": ((1.0, 0.4, 0.08), 1.1, 0.5), "MatchGlow": ((1.0, 0.38, 0.08), 1.1, 0.5)}
FLAME_PIVOT = BRAZIER + np.array((0, 0, BRAZ_Z + 0.01))
FLAME_COLOR = (1.0, 0.56, 0.16)
FLAME_STRENGTH = 1.5


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and 1.1 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.05))
