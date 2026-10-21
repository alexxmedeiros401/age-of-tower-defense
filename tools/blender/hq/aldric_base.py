"""Sir Aldric's stand: the muster yard's dais, where the commander reviews his knights. A round floor of grey flagstones
laid in two rings round a disc of red sandstone, a gold crown inlaid on it; a granite kerb round it, twelve gold glass
roundels set in its top in gold cups (the hero ring, their own emissive mesh); on a low grassy mound. Behind him on his
right his war banner on a tall ash pole: crimson, the gold crown over an upright sword, hanging from a crossbar with gold
finials. Behind him on his left a rack of lances: two posts and a rail, three lances leaning in it, crimson pennons at
their heads. Pebbles (distance fields) + grass and flowers (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
import kael_base as kb
import aldric as _al
from sunpriest_base import ring_func

ground_height = kb.ground_height
ground_field = kb.ground_field
GROUND_TOP = kb.GROUND_TOP
GROUND_R = kb.GROUND_R
TOP_Z = 0.3                        # the floor's top = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
DISC_R = 0.2
RING1_R = 0.42
DECK_R = 0.62
KERB_R = 0.77
KERB_TOP = TOP_Z - 0.008
RING_R = 0.695
N_GLOW = 12
POLE = v3((-0.74, 0.64, 0.0))      # the banner's pole
POLE_H = 1.55
BAN_FWD = norm(v3((0.34, -0.94, 0.0)))
BANNER_W, BANNER_H = 0.2, 0.62
RACK = v3((0.72, 0.62, 0.0))       # the lance rack's middle
RACK_AX = norm(v3((1.0, -0.75, 0.0)))     # along its rail


def _chip(P):
    return F(0.0018) * NOISE(P * F(11)) + F(0.001) * NOISE(P * F(37))


def floor_field():
    """Grey flagstones (label 0; worn pale where he stands, 6) in two rings, and the granite-grey kerb (its outer face
    weathered, 7)."""
    fd = Field("Floor")
    hz = (TOP_Z - GROUND_TOP + 0.06) / 2
    fd.add(ring_func(DISC_R, RING1_R, 8, 511, TOP_Z, hz, jitter=0.45, chip=_chip), 0.0)
    fd.add(ring_func(RING1_R, DECK_R, 12, 517, TOP_Z, hz, jitter=0.45, chip=_chip), 0.0)
    hk = (KERB_TOP - GROUND_TOP + 0.08) / 2
    fd.add(ring_func(DECK_R, KERB_R, 14, 531, KERB_TOP, hk, jitter=0.6, chip=_chip), 0.0)
    fd.paint(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(0.36), F(TOP_Z - 0.01) - P[:, 2]),
                  (-0.5, -0.5, TOP_Z - 0.05), (0.5, 0.5, TOP_Z + 0.03)), 6)
    fd.paint(Func(lambda P: np.maximum(F(KERB_R - 0.005) - np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2), P[:, 2] - F(KERB_TOP - 0.04)),
                  (-1, -1, GROUND_TOP - 0.1), (1, 1, KERB_TOP)), 7)
    return fd


def disc_field():
    """The disc of red sandstone in the middle of the floor."""
    fd = Field("Disc")
    hz = 0.05
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        q = np.stack([np.maximum(r - F(DISC_R - 0.006) + F(0.008), 0), np.maximum(np.abs(P[:, 2] - F(TOP_Z + 0.002 - hz)) - F(hz) + F(0.008), 0)], 1)
        inside = np.minimum(np.maximum(r - F(DISC_R - 0.006) + F(0.008), np.abs(P[:, 2] - F(TOP_Z + 0.002 - hz)) - F(hz) + F(0.008)), 0)
        return np.sqrt((q * q).sum(1)) + inside - F(0.008)
    fd.add(Func(disc, (-DISC_R, -DISC_R, TOP_Z - 0.11), (DISC_R, DISC_R, TOP_Z + 0.01), disp=_chip, disp_amp=0.002), 0.0)
    return fd


def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + math.pi / N_GLOW
    return v3((math.cos(a) * RING_R, math.sin(a) * RING_R, KERB_TOP - 0.002))


def glowstones_field():
    fd = Field("Glowstones")
    for i in range(N_GLOW):
        fd.add(Ellipsoid(glow_pos(i), (0.032, 0.032, 0.014)), 0.0)
    return fd


def banner_frame():
    g = ground_height(POLE[0], POLE[1])
    top = POLE + v3((0, 0, g + POLE_H))
    side = norm(np.cross(v3((0, 0, 1)), BAN_FWD))
    return top, BAN_FWD, side


def gold_field():
    """The crown inlaid on the sandstone disc (its band and three points, flush), the glass roundels' cups, the banner's
    crossbar finials and the pole's gilt cap."""
    fd = Field("Gold")
    def crown(P):
        u, v = P[:, 0] / F(0.6), (P[:, 1] + F(0.02)) / F(-0.6)
        d = _al.arms_2d(u, v + F(0.22)) * F(0.6)
        return np.maximum(d, np.abs(P[:, 2] - F(TOP_Z + 0.001)) - F(0.0025))
    fd.add(Func(crown, (-0.12, -0.15, TOP_Z - 0.01), (0.12, 0.12, TOP_Z + 0.01)), 0.0)
    for i in range(N_GLOW):
        fd.add(Torus(glow_pos(i) + v3((0, 0, -0.002)), 0.034, 0.008), 0.0)
    return fd


def finials_field():
    """Gilt finials on the banner's crossbar and the pole's cap (their own part: one field spanning the floor and the
    pole's top would mesh a needlessly huge grid)."""
    fd = Field("Finials")
    top, fwd, side = banner_frame()
    cb = top + v3((0, 0, -0.1))
    for s in (-1, 1):
        fd.add(Sphere(cb + side * (s * (BANNER_W + 0.04)), 0.02), 0.0)
        fd.add(RoundCone(cb + side * (s * (BANNER_W + 0.04)), cb + side * (s * (BANNER_W + 0.075)), 0.012, 0.004), 0.004)
    fd.add(Sphere(top + v3((0, 0, 0.03)), 0.028), 0.0)
    fd.add(RoundCone(top + v3((0, 0, 0.05)), top + v3((0, 0, 0.12)), 0.016, 0.003), 0.004)
    return fd


def banner_field():
    """His war banner: crimson wool (label 0), the gold crown over the sword (6), a gold border along its foot (5),
    hanging from the crossbar in a gentle wave, its foot cut in a swallow-tail."""
    fd = Field("Banner")
    top, fwd, side = banner_frame()
    cb = top + v3((0, 0, -0.1))
    def cloth(P):
        q = P - cb.astype(F)
        s = q @ side.astype(F)
        f = q @ fwd.astype(F)
        z = -q[:, 2]
        wave = F(0.014) * np.sin(s * F(24) + F(0.4)) * (F(1) + F(0.5) * np.clip(z / F(BANNER_H), 0, 1))
        notch = (z - F(BANNER_H - 0.14)) * F(0.6) - np.abs(s)
        d = np.maximum(np.maximum(np.abs(s) - F(BANNER_W), np.maximum(-z - F(0.005), z - F(BANNER_H))), np.abs(f - wave) - F(0.006))
        return np.maximum(d, notch)
    cs = [cb + side * su * 0.25 + fwd * sf * 0.1 + v3((0, 0, sz)) for su in (-1, 1) for sf in (-1, 1) for sz in (-BANNER_H - 0.05, 0.02)]
    lo, hi = np.minimum.reduce(cs), np.maximum.reduce(cs)
    fd.add(Func(cloth, lo, hi, disp=lambda P: F(0.0008) * NOISE(P * F(40)), disp_amp=0.001), 0.0)
    def arms(P):
        q = P - cb.astype(F)
        s = q @ side.astype(F)
        z = -q[:, 2]
        sc = F(0.5)
        return _al.arms_2d(s / sc, (F(0.27) - z) / sc) * sc
    fd.paint(Func(arms, lo, hi), 6)
    fd.paint(Func(lambda P: (F(BANNER_H - 0.17) - (-(P[:, 2] - F(cb[2])))), lo, hi), 5)
    return fd


def wood_field():
    """The banner's pole (ash, grain along Z: 11) and crossbar (10), iron-shod (6); the lance rack: two posts (11) and a
    rail (10) with three lances (ash, 11) leaning in it, their steel heads (6) and crimson pennons (5)."""
    fd = Field("Wood")
    g = ground_height(POLE[0], POLE[1])
    top, fwd, side = banner_frame()
    fd.add(RoundCone(POLE + v3((0, 0, g - 0.06)), top + v3((0, 0, 0.03)), 0.026, 0.02, disp=lambda P: F(0.0015) * NOISE(P * np.array([60, 60, 8], F)), disp_amp=0.002), 0.0, 11)
    fd.add(Cylinder(POLE + v3((0, 0, g + 0.02)), 0.03, 0.04, rr=0.006), 0.004, 6)
    cb = top + v3((0, 0, -0.1))
    fd.add(RoundCone(cb - side * (BANNER_W + 0.04), cb + side * (BANNER_W + 0.04), 0.012, 0.012), 0.006, 10)
    gr = ground_height(RACK[0], RACK[1])
    for s in (-1, 1):
        p = RACK + RACK_AX * (s * 0.2)
        fd.add(RoundCone(p + v3((0, 0, gr - 0.05)), p + v3((0, 0, gr + 0.62)), 0.026, 0.022), 0.0, 11)
    fd.add(RoundCone(RACK - RACK_AX * 0.24 + v3((0, 0, gr + 0.56)), RACK + RACK_AX * 0.24 + v3((0, 0, gr + 0.56)), 0.018, 0.018), 0.006, 10)
    rk = v3((RACK[0], RACK[1], 0.0))
    back = norm(rk - RACK_AX * float(RACK_AX @ rk))                       # (outward, away from the dais)
    for i, u in enumerate((-0.12, 0.0, 0.12)):
        foot = RACK + RACK_AX * u - back * 0.12 + v3((0, 0, gr - 0.02))
        lean = norm(v3((0, 0, 1)) + back * 0.12 + RACK_AX * (0.04 * (i - 1)))
        tip = foot + lean * 1.5
        fd.add(RoundCone(foot, tip - lean * 0.14, 0.014, 0.011, disp=lambda P: F(0.001) * NOISE(P * F(60)), disp_amp=0.0012), 0.0, 11)
        fd.add(RoundCone(tip - lean * 0.16, tip, 0.016, 0.002), 0.004, 6)
        pn = tip - lean * 0.22
        pd = norm(RACK_AX * (1 if i % 2 else -1) * 0.8 - lean * 0.3)
        fd.add(RoundBox(pn + pd * 0.08 - lean * 0.04, (0.004, 0.08, 0.05), 0.003, R=rot_from_axes(z_axis=lean, y_axis=pd)), 0.003, 5)
    return fd


def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < KERB_R + 0.08 + pad:
        return True
    if math.hypot(c[0] - POLE[0], c[1] - POLE[1]) < 0.08 + pad:
        return True
    if math.hypot(c[0] - RACK[0], c[1] - RACK[1]) < 0.32 + pad:
        return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(67)
    n = 0
    tries = 0
    while n < 12 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.9, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.024, 0.044), seed=780 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=71):
    old = kb._blocked
    kb._blocked = _blocked
    try:
        return kb.grass_geometry(seed)
    finally:
        kb._blocked = old


def flower_geometry(seed=73):
    old = kb._blocked
    kb._blocked = _blocked
    try:
        return kb.flower_geometry(seed)
    finally:
        kb._blocked = old


def fields():
    return [("Ground", ground_field(), 0.008), ("Floor", floor_field(), 0.0042), ("Disc", disc_field(), 0.004),
            ("Glowstones", glowstones_field(), 0.0025), ("Gold", gold_field(), 0.0018), ("Finials", finials_field(), 0.0018),
            ("Banner", banner_field(), 0.0024),
            ("Wood", wood_field(), 0.0024), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Floor", "Wood", "Banner")
LOW_TARGETS = {"Ground": 1400, "Floor": 4200, "Disc": 300, "Glowstones": 300, "Gold": 800, "Finials": 200, "Banner": 500, "Wood": 1600,
               "Pebbles": 340}
MAT_OVERRIDES = {"Floor": ("flagstone", {"name": "HQ_MusterFloor", "base": (0.46, 0.45, 0.43), "alt": (0.55, 0.52, 0.47)}),
                 "Disc": ("granite", {"name": "HQ_Sandstone", "base": (0.56, 0.24, 0.17), "feld": (0.68, 0.36, 0.26),
                                      "quartz": (0.62, 0.48, 0.4), "mica": (0.2, 0.08, 0.06)}),
                 "Gold": ("gold", {"name": "HQ_MusterGold"}), "Finials": ("gold", {"name": "HQ_MusterGold"}),
                 "Banner": ("wool", {"name": "HQ_AldricBanner", "base": _al.CRIMSON, "border": _al.GOLD_C, "stripe": _al.GOLD_C}),
                 "Wood": ("siege", {"name": "HQ_MusterWood", "wood": (0.56, 0.4, 0.25), "wood2": (0.4, 0.28, 0.16),
                                    "red": _al.CRIMSON, "metal": "iron"}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
GLOW = {"Glowstones": ((1.0, 0.74, 0.24), 1.0, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and KERB_R + 0.06 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.08))
