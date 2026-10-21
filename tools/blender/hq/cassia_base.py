"""Cassia's stand: the legate's tribunal, the platform a commander speaks to her legion from. A round floor of white marble
slabs laid in two rings round a disc of red porphyry, a gold laurel wreath inlaid round the disc; a moulded marble kerb
round it, twelve red glass roundels set in its top in bronze cups (the hero ring, their own emissive mesh); on a low
grassy mound. Behind her on her right the legion's eagle: a tall pole, a gold eagle with spread wings standing on a gold
laurel wreath, under it a red banner (vexillum) hung from a crossbar, gold-fringed. Behind her on her left a trophy: a
post and crossbar dressed in a beaten robot's armour (its dented head with a dead eye on top, its chest plate on the
post, its claw arms hung from the bar). Pebbles (distance fields) + grass and flowers (direct low-poly geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
import kael_base as kb
from sunpriest_base import ring_func

ground_height = kb.ground_height
ground_field = kb.ground_field
GROUND_TOP = kb.GROUND_TOP
GROUND_R = kb.GROUND_R

TOP_Z = 0.3                        # the floor's top = where she stands
STAND = v3((0.0, 0.0, TOP_Z))
DISC_R = 0.2                       # the porphyry disc
RING1_R = 0.42
DECK_R = 0.62                      # the floor's edge (inside the kerb)
KERB_R = 0.77
KERB_TOP = TOP_Z - 0.008
RING_R = 0.695                     # the glass roundels on the kerb
N_GLOW = 12
POLE = v3((-0.76, 0.62, 0.0))      # the eagle's pole
POLE_H = 1.4
AQ_FWD = norm(v3((0.32, -0.95, 0.0)))
TROPHY = v3((0.76, 0.6, 0.0))      # the trophy's post
TR_H = 1.12
TR_FWD = norm(v3((-0.36, -0.93, 0.0)))


def _chip(P):
    return F(0.0018) * NOISE(P * F(11)) + F(0.001) * NOISE(P * F(37))


def _grain(P):
    return F(0.0025) * NOISE(P * np.array([6, 60, 60], F))


# ---------------------------------------------------------------------------------------------- the floor
def marble_field():
    """White marble (label 0): two rings of slabs (polished by feet: 6) and the kerb, moulded, its outer face weathered
    (7)."""
    fd = Field("Marble")
    hz = (TOP_Z - GROUND_TOP + 0.06) / 2
    fd.add(ring_func(DISC_R, RING1_R, 8, 311, TOP_Z, hz, jitter=0.35, chip=_chip), 0.0)
    fd.add(ring_func(RING1_R, DECK_R, 12, 317, TOP_Z, hz, jitter=0.35, chip=_chip), 0.0)
    hk = (KERB_TOP - GROUND_TOP + 0.08) / 2
    fd.add(ring_func(DECK_R, KERB_R, 14, 331, KERB_TOP, hk, jitter=0.6, chip=_chip), 0.0)
    # the kerb's moulding: a rounded lip along its top outer edge, a groove under it
    def lip(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.sqrt((r - F(KERB_R - 0.004)) ** 2 + (P[:, 2] - F(KERB_TOP - 0.02)) ** 2) - F(0.022)
    fd.add(Func(lip, (-KERB_R - 0.05, -KERB_R - 0.05, KERB_TOP - 0.06), (KERB_R + 0.05, KERB_R + 0.05, KERB_TOP + 0.01),
                disp=_chip, disp_amp=0.003), 0.006)
    def groove(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.sqrt((r - F(KERB_R + 0.016)) ** 2 + (P[:, 2] - F(KERB_TOP - 0.062)) ** 2) - F(0.01)
    fd.sub(Func(groove, (-KERB_R - 0.05, -KERB_R - 0.05, KERB_TOP - 0.09), (KERB_R + 0.05, KERB_R + 0.05, KERB_TOP - 0.03)), 0.004)
    fd.paint(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(0.36), F(TOP_Z - 0.01) - P[:, 2]),
                  (-0.5, -0.5, TOP_Z - 0.05), (0.5, 0.5, TOP_Z + 0.03)), 6)
    fd.paint(Func(lambda P: np.maximum(F(KERB_R - 0.005) - np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2), P[:, 2] - F(KERB_TOP - 0.04)),
                  (-1, -1, GROUND_TOP - 0.1), (1, 1, KERB_TOP)), 7)
    return fd


def porphyry_field():
    """The disc of red porphyry in the middle of the floor, set a hair proud."""
    fd = Field("Porphyry")
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
    """Twelve roundels of red glass on the kerb (domed, each in a bronze cup: the Gold part)."""
    fd = Field("Glowstones")
    for i in range(N_GLOW):
        fd.add(Ellipsoid(glow_pos(i), (0.032, 0.032, 0.014)), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- gold: the inlay, the eagle
def aquila_frame():
    g = ground_height(POLE[0], POLE[1])
    top = POLE + v3((0, 0, g + POLE_H))
    side = norm(np.cross(v3((0, 0, 1)), AQ_FWD))
    return top, AQ_FWD, side


def eagle(fd, W, R):
    """A gold eagle standing upright, wings raised and spread, head turned to its right (W: local -> world; R: its frame)."""
    E = lambda c, r, rr=None: Ellipsoid(W(*c), r, R=R if rr is None else rr)
    fd.add(E((0, 0.0, 0.2), (0.042, 0.05, 0.075)), 0.0)                                  # body
    fd.add(E((0, 0.03, 0.225), (0.038, 0.04, 0.05)), 0.02)                               # breast
    fd.add(Sphere(W(0.004, 0.03, 0.3), 0.03), 0.02)                                      # head
    fd.add(RoundCone(W(0.006, 0.05, 0.302), W(0.01, 0.084, 0.29), 0.016, 0.008), 0.008)  # beak
    fd.add(RoundCone(W(0.01, 0.084, 0.29), W(0.011, 0.09, 0.274), 0.008, 0.003), 0.004)  # its hook
    for sx in (-1, 1):
        fd.sub(Sphere(W(sx * 0.024, 0.044, 0.31), 0.006), 0.002)                         # eyes
        # the wing: a broad arm out and up from the shoulder, the primaries fanning from its tip
        sh = W(sx * 0.036, -0.012, 0.25)
        el = W(sx * 0.1, -0.026, 0.31)
        tip = W(sx * 0.16, -0.03, 0.4)
        fd.add(Chain([sh, el, tip], [0.022, 0.018, 0.012], k=0.01), 0.012)
        wn = norm(np.cross(el - sh, tip - el))
        if wn @ AQ_FWD < 0:
            wn = -wn
        for k in range(5):                                                               # the wing's feathered trailing edge
            u = (k + 0.5) / 5
            root = lerp(sh, tip, 0.25 + 0.75 * u)
            drop = norm(v3((sx * (0.25 + 0.6 * u), 0.0, -(1.0 - 0.6 * u))))
            L = 0.05 + 0.05 * u
            fd.add(Ellipsoid(root + drop * L * 0.55, (0.016, 0.005, L * 0.55), R=rot_from_axes(z_axis=drop, y_axis=wn)), 0.006)
        for k in range(3):                                                               # the primaries at the wingtip
            d = norm(v3((sx * (0.5 + 0.25 * k), 0.0, 1.0 - 0.3 * k)))
            fd.add(Ellipsoid(tip + d * 0.04, (0.012, 0.005, 0.045), R=rot_from_axes(z_axis=d, y_axis=wn)), 0.005)
        fd.add(RoundCone(W(sx * 0.02, 0.0, 0.14), W(sx * 0.024, 0.006, 0.1), 0.012, 0.008), 0.008)   # legs
    for k in range(3):                                                                   # the tail
        d = norm(W(0.03 * (k - 1), -0.05, 0.06) - W(0, 0, 0.16))
        fd.add(Ellipsoid(W(0, -0.02, 0.13) + d * 0.04, (0.016, 0.005, 0.05), R=rot_from_axes(z_axis=d, y_axis=AQ_FWD)), 0.006)


def gold_field():
    """The laurel wreath inlaid round the porphyry disc; the bronze cups of the glass roundels; the eagle on its wreath,
    the crossbar's finials and the banner's fringe."""
    fd = Field("Gold")
    # the inlaid wreath: pairs of leaves along a ring round the disc, a hair proud of the marble
    n = 22
    for i in range(n):
        a = 2 * math.pi * i / n
        p = v3((math.cos(a) * (DISC_R + 0.045), math.sin(a) * (DISC_R + 0.045), TOP_Z + 0.001))
        tng = v3((-math.sin(a), math.cos(a), 0))
        out = v3((math.cos(a), math.sin(a), 0))
        for s in (-1, 1):
            d = norm(tng + out * 0.55 * s)
            fd.add(Ellipsoid(p + d * 0.02, (0.009, 0.024, 0.003), R=rot_from_axes(y_axis=d, z_axis=(0, 0, 1))), 0.002)
    ring = [v3((math.cos(2 * math.pi * k / 48) * (DISC_R + 0.045), math.sin(2 * math.pi * k / 48) * (DISC_R + 0.045), TOP_Z + 0.001))
            for k in range(49)]
    fd.add(Chain(ring, [0.004] * len(ring), k=0.003), 0.002)
    for i in range(N_GLOW):
        c = glow_pos(i)
        fd.add(Torus(c + v3((0, 0, -0.002)), 0.034, 0.008), 0.0)
    # the aquila
    top, fwd, side = aquila_frame()
    W = lambda x, y, z: top + side * x + fwd * y + v3((0, 0, z))
    R = rot_from_axes(y_axis=fwd, z_axis=(0, 0, 1))
    wc = W(0, 0, 0.06)
    fd.add(Torus(wc, 0.07, 0.012, R=rot_from_axes(z_axis=fwd)), 0.0)                     # the wreath it stands on
    for k in range(16):
        a = 2 * math.pi * k / 16
        rd = side * math.cos(a) + v3((0, 0, 1)) * math.sin(a)
        td = side * -math.sin(a) + v3((0, 0, 1)) * math.cos(a)
        for s in (-1, 1):
            d = norm(td + rd * 0.6 * s)
            fd.add(Ellipsoid(wc + rd * 0.07 + d * 0.016, (0.008, 0.004, 0.02), R=rot_from_axes(z_axis=d, y_axis=fwd)), 0.003)
    fd.add(Cylinder(W(0, 0, 0.0), 0.03, 0.03, rr=0.008), 0.004)                          # the socket on the pole
    eagle(fd, lambda x, y, z: W(x, y, z + 0.045), R)            # (its feet on the wreath's top)
    # the crossbar's finials and the banner's fringe
    cb = top + v3((0, 0, -0.14))
    for sx in (-1, 1):
        fd.add(Sphere(cb + side * sx * 0.215, 0.018), 0.0)
        fd.add(RoundCone(cb + side * sx * 0.215, cb + side * sx * 0.215 + v3((0, 0, 0.035)), 0.012, 0.004), 0.006)
    for k in range(13):
        s = -0.165 + 0.33 * k / 12
        b = cb + side * s + fwd * BANNER_WAVE(s) + v3((0, 0, -BANNER_H - 0.012))
        fd.add(RoundCone(b, b + v3((0, 0, -0.045)), 0.008, 0.004), 0.004)
    return fd


BANNER_H = 0.4
BANNER_W = 0.17                    # half width


def BANNER_WAVE(s):
    return 0.012 * math.sin(s * 26.0 + 0.4)


def banner_field():
    """The red vexillum hanging from the crossbar, a gentle wave across it (cloth)."""
    fd = Field("Banner")
    top, fwd, side = aquila_frame()
    cb = top + v3((0, 0, -0.14))
    def cloth(P):
        q = P - cb.astype(F)
        s = q @ side.astype(F)
        f = q @ fwd.astype(F)
        z = q[:, 2]
        wave = F(0.012) * np.sin(s * F(26) + F(0.4)) * (F(1) + F(0.5) * np.clip(-z / F(BANNER_H), 0, 1))
        hem = F(0.008) * np.sin(s * F(60))
        return np.maximum(np.maximum(np.abs(s) - F(BANNER_W), np.maximum(z + F(0.005), F(-BANNER_H) + hem * F(0.3) - z)),
                          np.abs(f - wave) - F(0.006))
    cs = [cb + side * su * 0.25 + fwd * sf * 0.1 + v3((0, 0, sz)) for su in (-1, 1) for sf in (-1, 1) for sz in (-BANNER_H - 0.05, 0.02)]
    fd.add(Func(cloth, np.minimum.reduce(cs), np.maximum.reduce(cs), disp=lambda P: F(0.0008) * NOISE(P * F(40)), disp_amp=0.001), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the pole, the trophy
def wood_field():
    """The eagle's pole (ash, grain along Z: 11) and its crossbar (10), iron-shod (6); the trophy's post (11) and crossbar
    (10), lashed (rope 8), dressed in the robot's armour (iron 6): its dented head with a dead red eye (5) on top, its
    chest plate riveted on the post, its claw arms hung from the bar's ends."""
    fd = Field("Wood")
    g = ground_height(POLE[0], POLE[1])
    top, fwd, side = aquila_frame()
    fd.add(RoundCone(POLE + v3((0, 0, g - 0.06)), top, 0.026, 0.02, disp=lambda P: F(0.0015) * NOISE(P * np.array([60, 60, 8], F)), disp_amp=0.002), 0.0, 11)
    fd.add(Cylinder(POLE + v3((0, 0, g + 0.02)), 0.03, 0.04, rr=0.006), 0.004, 6)
    cb = top + v3((0, 0, -0.14))
    fd.add(RoundCone(cb - side * 0.215, cb + side * 0.215, 0.012, 0.012), 0.004, 10)
    # the trophy
    gt = ground_height(TROPHY[0], TROPHY[1])
    tside = norm(np.cross(v3((0, 0, 1)), TR_FWD))
    T = lambda x, y, z: TROPHY + tside * x + TR_FWD * y + v3((0, 0, gt + z))
    Rt = rot_from_axes(x_axis=tside, y_axis=TR_FWD, z_axis=(0, 0, 1))
    fd.add(RoundCone(T(0, 0, -0.06), T(0, 0, TR_H), 0.042, 0.036, disp=lambda P: F(0.003) * NOISE(P * np.array([40, 40, 6], F)), disp_amp=0.004), 0.0, 11)
    bar_z = 0.84
    fd.add(RoundCone(T(-0.27, 0.0, bar_z), T(0.27, 0.0, bar_z), 0.026, 0.026, disp=_grain, disp_amp=0.003), 0.01, 10)
    for k in range(3):
        fd.add(Torus(T(0, 0, bar_z - 0.03 + 0.03 * k), 0.046, 0.007, R=rot_from_axes(z_axis=(0, 0, 1))), 0.003, 8)
    # the robot's head: a rounded box, dented, a round eye socket with a dead red lens, a bent antenna
    hc = T(0, 0.01, TR_H + 0.07)
    fd.add(RoundBox(hc, (0.085, 0.075, 0.072), 0.03, R=Rt), 0.0, 6)
    fd.add(RoundBox(hc + v3((0, 0, 0.07)), (0.05, 0.05, 0.012), 0.008, R=Rt), 0.01, 6)
    eye = hc + TR_FWD * 0.074 + v3((0, 0, 0.008))
    fd.sub(Cylinder(eye, 0.04, 0.03, rr=0.004, R=rot_from_axes(z_axis=TR_FWD)), 0.004)
    fd.add(Sphere(eye - TR_FWD * 0.022, 0.034), 0.0, 5)
    fd.add(Torus(eye - TR_FWD * 0.004, 0.04, 0.007, R=rot_from_axes(z_axis=TR_FWD)), 0.003, 6)
    for dx, dz in ((0.06, 0.05), (-0.07, -0.02), (0.03, -0.06)):
        fd.sub(Sphere(hc + tside * dx + TR_FWD * 0.1 + v3((0, 0, dz)), 0.034), 0.01)      # dents
    ant0 = hc + v3((0.0, 0.0, 0.08)) + tside * 0.03
    fd.add(Chain([ant0, ant0 + v3((0.01, 0, 0.07)), ant0 + v3((0.06, -0.02, 0.1))], [0.007, 0.005, 0.004], k=0.003), 0.004, 6)
    fd.add(Sphere(ant0 + v3((0.06, -0.02, 0.1)), 0.012), 0.003, 6)
    for sx in (-1, 1):                                                                   # its ear vents
        fd.add(Cylinder(hc + tside * sx * 0.09, 0.03, 0.012, rr=0.004, R=rot_from_axes(z_axis=tside)), 0.004, 6)
    # its chest plate on the post under the bar
    pc = T(0, 0.05, bar_z - 0.2)
    def plate(P):
        q = (P - pc.astype(F)) @ Rt.astype(F)
        bulge = F(0.04) * (F(1) - (q[:, 0] / F(0.16)) ** 2)
        return np.maximum(np.maximum(np.abs(q[:, 0]) - F(0.15), np.abs(q[:, 2]) - F(0.15) - F(0.03) * np.cos(q[:, 0] * F(9))),
                          np.abs(q[:, 1] - bulge) - F(0.012))
    fd.add(Func(plate, pc - 0.3, pc + 0.3, disp=lambda P: F(0.001) * NOISE(P * F(30)), disp_amp=0.002), 0.004, 6)
    for x in (-0.12, 0.12):
        for z in (-0.12, 0.0, 0.12):
            fd.add(Sphere(pc + tside * x + TR_FWD * (0.054 * (1 - (x / 0.16) ** 2) + 0.012) + v3((0, 0, z)), 0.011), 0.003, 6)
    fd.sub(Ellipsoid(pc + tside * 0.04 + TR_FWD * 0.06 + v3((0, 0, 0.05)), (0.05, 0.02, 0.008), R=rot_from_axes(x_axis=tside + v3((0, 0, 0.6)), y_axis=TR_FWD)), 0.004)
    # its claw arms hung from the bar's ends
    for sx in (-1, 1):
        a0 = T(sx * 0.24, 0.02, bar_z - 0.02)
        a1 = a0 + v3((0, 0, -0.2)) + tside * sx * 0.02
        a2 = a1 + v3((0, 0, -0.18)) + TR_FWD * 0.03
        fd.add(Torus(a0 + v3((0, 0, 0.0)), 0.03, 0.008, R=rot_from_axes(z_axis=tside)), 0.003, 8)
        fd.add(RoundCone(a0 + v3((0, 0, -0.03)), a1, 0.03, 0.026), 0.0, 6)
        fd.add(Sphere(a1, 0.034), 0.008, 6)
        fd.add(RoundCone(a1, a2, 0.026, 0.022), 0.008, 6)
        for k in (-1, 1):                                                                # the two-fingered claw
            c0 = a2 + TR_FWD * k * 0.02
            fd.add(Chain([c0, c0 + v3((0, 0, -0.05)) + TR_FWD * k * 0.03, c0 + v3((0, 0, -0.09)) + TR_FWD * k * 0.01],
                         [0.014, 0.011, 0.005], k=0.004), 0.006, 6)
    return fd


# ---------------------------------------------------------------------------------------------- scatter
def _blocked(c, pad=0.0):
    if math.hypot(c[0], c[1]) < KERB_R + 0.08 + pad:
        return True
    if math.hypot(c[0] - POLE[0], c[1] - POLE[1]) < 0.08 + pad:
        return True
    if math.hypot(c[0] - TROPHY[0], c[1] - TROPHY[1]) < 0.12 + pad:
        return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(61)
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
        fd.add(Stone(p, rs.uniform(0.024, 0.046), seed=760 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=37):
    old = kb._blocked
    kb._blocked = _blocked
    try:
        return kb.grass_geometry(seed)
    finally:
        kb._blocked = old


def flower_geometry(seed=43):
    old = kb._blocked
    kb._blocked = _blocked
    try:
        return kb.flower_geometry(seed)
    finally:
        kb._blocked = old


def fields():
    return [("Ground", ground_field(), 0.008), ("Marble", marble_field(), 0.0042), ("Porphyry", porphyry_field(), 0.004),
            ("Glowstones", glowstones_field(), 0.0025), ("Gold", gold_field(), 0.0018), ("Banner", banner_field(), 0.0024),
            ("Wood", wood_field(), 0.0024), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Marble", "Wood")
LOW_TARGETS = {"Ground": 1400, "Marble": 4200, "Porphyry": 300, "Glowstones": 300, "Gold": 2400, "Banner": 500, "Wood": 2200,
               "Pebbles": 340}
MAT_OVERRIDES = {"Marble": ("marble", {"name": "HQ_TribunalMarble"}),
                 "Porphyry": ("granite", {"name": "HQ_Porphyry", "base": (0.4, 0.1, 0.12), "feld": (0.6, 0.26, 0.28),
                                          "quartz": (0.5, 0.34, 0.34), "mica": (0.12, 0.04, 0.05)}),
                 "Gold": ("gold", {"name": "HQ_TribunalGold"}),
                 "Banner": ("cloth", {"name": "HQ_Vexillum", "col": (0.72, 0.09, 0.08)}),
                 "Wood": ("siege", {"name": "HQ_TrophyWood", "wood": (0.54, 0.38, 0.24), "wood2": (0.38, 0.26, 0.15),
                                    "red": (0.5, 0.06, 0.05), "metal": "iron"}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
GLOW = {"Glowstones": ((1.0, 0.2, 0.1), 1.0, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and KERB_R + 0.06 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.08))
