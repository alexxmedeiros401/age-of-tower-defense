"""Brenna's stand: the war band's muster ground on a hill fort's rampart. A round floor of rounded river cobbles set
close in beaten earth, ringed by a kerb of big flat stones, on a low turf bank;
round its foot a ring of twelve blue-glowing stones set in the turf (the hero ring, its own emissive mesh); behind her
on her left a weapon rack (two posts and a crossbar) with three spears leaning on it and a round shield hung from it,
painted red with a white spiral; behind her on her right a tall pole bearing a bronze boar standard; pebbles (distance
fields) + grass, heather and gorse (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
import kael_base as kb

GROUND_R = 1.32
GROUND_TOP = 0.14
TOP_Z = 0.3                        # the cobbles' tops = where her feet stand
STAND = v3((0.0, 0.0, TOP_Z))
DECK_R = 0.62
RING_R = 0.86
N_GLOW = 12
RACK = (v3((0.3, 0.98, 0.0)), v3((0.92, 0.56, 0.0)))     # the rack's two posts (behind her, on her left)
RACK_H = 0.82
POLE = v3((-0.78, 0.66, 0.0))                             # the boar standard's pole (behind her, on her right)
POLE_H = 1.5

ground_height = kb.ground_height
ground_field = kb.ground_field


def _grain(P):
    return F(0.0025) * NOISE(P * np.array([6, 60, 60], F))


CELL = 0.074                       # the cobbles' spacing


def _hash2(cx, cy, k):
    return np.mod(np.sin(cx * F(127.1 + 17 * k) + cy * F(311.7 + 29 * k)) * F(43758.5453), F(1.0))


def _cobble_d(P):
    """Distance (in the ground plane) to the nearest cobble's middle, and that cobble's own little height step."""
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
    """The muster ground: a round floor of rounded river cobbles set close in beaten earth, ringed by a kerb of big flat
    stones."""
    fd = Field("Stone")
    def floor(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.sqrt(x * x + y * y)
        d1, st = _cobble_d(P)
        dome = F(0.016) * (F(1.0) - np.clip(d1 / F(0.62 * CELL), 0, 1) ** 2)
        top = F(TOP_Z - 0.016) + dome + st
        return np.maximum(np.maximum(r - F(DECK_R), z - top), F(GROUND_TOP - 0.08) - z)
    fd.add(Func(floor, (-DECK_R - 0.03, -DECK_R - 0.03, GROUND_TOP - 0.1), (DECK_R + 0.03, DECK_R + 0.03, TOP_Z + 0.03),
                disp=lambda P: F(0.0012) * NOISE(P * F(40)), disp_amp=0.0015), 0.0)
    rs = np.random.RandomState(13)
    n = 24
    for i in range(n):                                                  # the kerb
        a = 2 * math.pi * (i + rs.uniform(-0.15, 0.15)) / n
        c = v3((math.cos(a) * (DECK_R + 0.05), math.sin(a) * (DECK_R + 0.05), TOP_Z - 0.06))
        fd.add(Stone(c, rs.uniform(0.075, 0.09), seed=900 + i, squash=(1.0, 0.75, 0.62),
                     R=euler(0, 0, a + math.pi / 2 + rs.uniform(-0.2, 0.2)), noise=0.05), 0.012)
    return fd


def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + 0.26
    x, y = math.cos(a) * RING_R, math.sin(a) * RING_R
    return v3((x, y, ground_height(x, y) + 0.008))


def glowstones_field():
    fd = Field("Glowstones")
    for i in range(N_GLOW):
        c = glow_pos(i)
        a = i * 2 * math.pi / N_GLOW + 0.26
        fd.add(Ellipsoid(c, (0.042, 0.034, 0.026), R=euler(0, 0, a)), 0.0)
    return fd


def kerb_field():
    fd = Field("Kerb")
    rs = np.random.RandomState(43)
    for i in range(N_GLOW):
        c = glow_pos(i)
        for k in range(3):
            a = rs.uniform(0, 2 * math.pi)
            p = c + v3((math.cos(a) * 0.06, math.sin(a) * 0.06, -0.006))
            fd.add(Stone(p, rs.uniform(0.022, 0.03), seed=700 + i * 3 + k, squash=(1.2, 1.0, 0.45), noise=0.05), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the rack, the shield
def rack_field():
    """The weapon rack: two posts (grain along Z, 11) and a crossbar lashed to them (grain along X, 10; rope 8); three
    spears leaning on it (ash, iron heads 6)."""
    fd = Field("Rack")
    p0, p1 = RACK
    tops = []
    for p in (p0, p1):
        g = ground_height(p[0], p[1])
        b = p + v3((0, 0, g - 0.06))
        top = p + v3((0, 0, g + RACK_H))
        tops.append(top)
        fd.add(RoundCone(b, top, 0.045, 0.04, disp=lambda P: F(0.003) * NOISE(P * np.array([40, 40, 6], F)), disp_amp=0.004), 0.0, 11)
        fd.add(Sphere(top, 0.04), 0.02, 11)
    a, b = tops[0] + v3((0, -0.03, -0.1)), tops[1] + v3((0, -0.03, -0.1))
    fd.add(RoundCone(a - norm(b - a) * 0.08, b + norm(b - a) * 0.08, 0.03, 0.03, disp=_grain, disp_amp=0.003), 0.01, 10)
    for c in (a, b):
        for k in range(3):
            fd.add(Torus(c + v3((0, 0, -0.025 + 0.018 * k)), 0.05, 0.007, R=rot_from_axes(z_axis=(0, 0, 1))), 0.003, 8)
    # three spears leaning on the bar, butts in the turf in front of it
    d_bar = norm(b - a)
    for k, u in enumerate((0.25, 0.5, 0.75)):
        rest = lerp(a, b, u) + v3((0, -0.035, 0.03))
        foot = rest + v3((0.0, -0.36, 0.0))
        foot[2] = ground_height(foot[0], foot[1]) - 0.04
        ax = norm(rest - foot + v3((0.02 * (k - 1), 0, 0)))
        L = 1.5
        tip = foot + ax * L
        fd.add(Chain([foot, foot + ax * (L - 0.23)], [0.014, 0.013], k=0.0, disp=lambda P: F(0.0015) * NOISE(P * F(70)), disp_amp=0.002), 0.0)
        side = norm(np.cross(ax, v3((0, 0, 1)))) if abs(ax[2]) < 0.95 else v3((1, 0, 0))
        fd.add(RoundCone(foot + ax * (L - 0.25), foot + ax * (L - 0.18), 0.018, 0.015), 0.003, 6)
        fd.add(Ellipsoid(foot + ax * (L - 0.09), (0.026, 0.006, 0.09), R=rot_from_axes(z_axis=ax, x_axis=side)), 0.005, 6)
        fd.add(Chain([foot + ax * (L - 0.19), tip], [0.008, 0.0025], k=0.004), 0.005, 6)
    return fd


def hung_shield_frame():
    p0, p1 = RACK
    g = ground_height((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    c = lerp(p0, p1, 0.5) + v3((0, 0.06, g + RACK_H - 0.36))
    face = norm(v3((-0.45, -0.85, 0.12)))                       # turned toward the front, a little to her
    up = norm(v3((0, 0, 1)) - face * face[2])
    return c, face, up


def shield_field():
    """A round shield hung on the rack: its face painted red (5) with a white spiral (7 painted pale) round an iron boss
    and rim (6); the boards behind (0)."""
    fd = Field("Shield")
    c, face, up = hung_shield_frame()
    s = np.cross(face, up)
    R = rot_from_axes(z_axis=face, y_axis=up)
    Rr = 0.27
    fd.add(Cylinder(c, Rr, 0.024, rr=0.01, R=R, disp=lambda P: F(0.001) * NOISE(P * F(40)), disp_amp=0.0012), 0.0)
    def front(P):
        return F(0.004) - (P - c.astype(F)) @ face.astype(F)
    def polar(P):
        q = P - c.astype(F)
        u, v = q @ up.astype(F), q @ s.astype(F)
        return np.sqrt(u * u + v * v), np.arctan2(v, u)
    fd.paint(Func(front, c - 0.4, c + 0.4), 5)
    def spiral(P):
        rr, a = polar(P)
        best = F(1.0)
        for k in range(2):
            th = F(k * math.pi) + F(3.4) * (rr - F(0.07)) / F(0.17)
            da = np.mod(a - th + F(math.pi), F(2 * math.pi)) - F(math.pi)
            u = np.clip((rr - F(0.07)) / F(0.16), 0, 1)
            arm = np.abs(da) * rr - (F(0.026) * (F(1) - u) + F(0.007))
            best = np.minimum(best, np.maximum(arm, np.maximum(F(0.068) - rr, rr - F(0.23))))
        return np.maximum(best, front(P))
    fd.paint(Func(spiral, c - 0.4, c + 0.4), 7)
    fd.add(Torus(c + face * 0.006, Rr - 0.004, 0.013, R=R), 0.005, 6)
    fd.add(Inter(Sphere(c + face * 0.0, 0.06), Plane(c + face * 0.012, -face), 0.004), 0.006, 6)
    fd.add(Torus(c + face * 0.013, 0.058, 0.007, R=R), 0.003, 6)
    return fd


# ---------------------------------------------------------------------------------------------- the boar standard
def standard_field():
    """A tall ash pole (wood), iron-shod; on its top a bronze boar (label 6 in the siege material): a deep body with a
    bristling crest along its back, a long snout with tusks, pricked ears, short legs on a crossbar."""
    fd = Field("Standard")
    g = ground_height(POLE[0], POLE[1])
    b = POLE + v3((0, 0, g - 0.06))
    top = POLE + v3((0, 0, g + POLE_H))
    fd.add(RoundCone(b, top, 0.024, 0.02, disp=lambda P: F(0.0015) * NOISE(P * np.array([60, 60, 8], F)), disp_amp=0.002), 0.0, 11)
    fd.add(Cylinder(top + v3((0, 0, -0.012)), 0.028, 0.03, rr=0.006), 0.004, 6)                       # the socket
    fwd = norm(v3((0.55, -0.83, 0.0)))                                                                 # it faces the field
    side = norm(np.cross(v3((0, 0, 1)), fwd))
    W = lambda x, y, z: top + side * x + fwd * y + v3((0, 0, z))
    R = rot_from_axes(y_axis=fwd, z_axis=(0, 0, 1))
    fd.add(RoundCone(W(0, -0.1, 0.02), W(0, 0.1, 0.02), 0.012, 0.012), 0.004, 6)                        # the crossbar
    body = W(0, 0.0, 0.12)
    fd.add(Ellipsoid(body, (0.05, 0.13, 0.06), R=R), 0.0, 6)
    fd.add(Ellipsoid(W(0, -0.06, 0.135), (0.054, 0.07, 0.066), R=R), 0.03, 6)                           # haunch
    fd.add(Ellipsoid(W(0, 0.08, 0.14), (0.052, 0.07, 0.07), R=R), 0.03, 6)                             # shoulders
    head0, head1 = W(0, 0.15, 0.13), W(0, 0.26, 0.09)
    fd.add(RoundCone(head0, head1, 0.042, 0.018), 0.025, 6)                                           # head and snout
    fd.add(Cylinder(head1 + fwd * 0.004, 0.019, 0.01, rr=0.004, R=rot_from_axes(z_axis=fwd)), 0.004, 6)
    for sx in (-1, 1):
        fd.add(RoundCone(W(sx * 0.02, 0.24, 0.085), W(sx * 0.034, 0.255, 0.115), 0.006, 0.002), 0.003, 6)      # tusks
        fd.add(RoundCone(W(sx * 0.026, 0.14, 0.17), W(sx * 0.04, 0.12, 0.215), 0.014, 0.004), 0.006, 6)        # ears
        for yy in (-0.08, 0.08):                                                                       # legs
            fd.add(RoundCone(W(sx * 0.03, yy, 0.09), W(sx * 0.032, yy + 0.01 * (1 if yy > 0 else -1), 0.025), 0.016, 0.011), 0.01, 6)
    for k in range(9):                                                                                 # the crest of bristles
        y = -0.1 + 0.025 * k
        h = 0.05 + 0.03 * math.sin(math.pi * k / 8)
        fd.add(RoundBox(W(0, y, 0.17 + h * 0.5), (0.005, 0.011, h * 0.5), 0.003, R=R), 0.006, 6)
    fd.add(Chain([W(0, -0.13, 0.13), W(0, -0.17, 0.12), W(0, -0.18, 0.09)], [0.008, 0.006, 0.004], k=0.004), 0.004, 6)  # tail
    return fd


# ---------------------------------------------------------------------------------------------- scatter
def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < DECK_R + 0.14 + pad:
        return True
    p0, p1 = RACK
    d = p1 - p0
    t = max(0.0, min(1.0, float(((v3((c[0], c[1], 0)) - p0) @ d) / (d @ d))))
    q = p0 + d * t
    if math.hypot(c[0] - q[0], c[1] - q[1]) < 0.12 + pad:
        return True
    for k, u in enumerate((0.25, 0.5, 0.75)):
        f = lerp(p0, p1, u) + v3((0, -0.39, 0))
        if math.hypot(c[0] - f[0], c[1] - f[1]) < 0.09 + pad:
            return True
    if math.hypot(c[0] - POLE[0], c[1] - POLE[1]) < 0.1 + pad:
        return True
    for i in range(N_GLOW):
        gp = glow_pos(i)
        if math.hypot(c[0] - gp[0], c[1] - gp[1]) < 0.1 + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(29)
    n = 0
    tries = 0
    while n < 12 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.95, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.026, 0.05), seed=380 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=31):
    old = kb._blocked
    kb._blocked = _blocked
    try:
        return kb.grass_geometry(seed)
    finally:
        kb._blocked = old


def flower_geometry(seed=41):
    old = kb._blocked
    kb._blocked = _blocked
    try:
        return kb.flower_geometry(seed)
    finally:
        kb._blocked = old


def fields():
    return [("Ground", ground_field(), 0.008), ("Stone", floor_field(), 0.004), ("Glowstones", glowstones_field(), 0.0025),
            ("Kerb", kerb_field(), 0.004), ("Rack", rack_field(), 0.0024), ("Shield", shield_field(), 0.0024),
            ("Standard", standard_field(), 0.0018), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Rack", "Shield", "Standard")
LOW_TARGETS = {"Ground": 1400, "Stone": 4600, "Glowstones": 460, "Kerb": 520, "Rack": 1100, "Shield": 700, "Standard": 1100,
               "Pebbles": 340}
OAK = {"wood": (0.52, 0.38, 0.24), "wood2": (0.38, 0.26, 0.15)}
MAT_OVERRIDES = {"Stone": ("stone", {"name": "HQ_Cobbles", "scale": 0.5}),
                 "Kerb": ("stone", {"name": "HQ_KerbStone", "scale": 0.3}),
                 "Rack": ("siege", dict(OAK, name="HQ_RackOak", metal="iron")),
                 "Shield": ("siege", {"name": "HQ_HungShield", "wood": (0.5, 0.34, 0.2), "wood2": (0.36, 0.24, 0.13),
                                      "red": (0.66, 0.12, 0.07), "blue": (0.9, 0.88, 0.8), "metal": "iron"}),
                 "Standard": ("siege", dict(OAK, name="HQ_BoarStandard")),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
GLOW = {"Glowstones": ((0.36, 0.62, 1.0), 1.0, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and DECK_R + 0.1 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.08))
