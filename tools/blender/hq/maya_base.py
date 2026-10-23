"""Maya's stand: a corner of a forward operating base. A round concrete pad (expansion joints, a worn edge) set in
packed earth, its edge ringed by the hero ring: twelve amber runway-edge lights in steel fittings (their own emissive
mesh). Round it on the packed earth: behind her a curved wall of sandbags three courses high; at its left end a
steel flag pole in a concrete block flying a small red guidon with the unit's white chevron; behind her on her right a
wooden crate with a field radio on it (knobs, a handset on its coiled cord, a tall whip antenna); before her on her
right a long olive-painted ammunition crate with rope handles and stencils, an ammo can on it; before her on her left
two ammo cans and a jerrycan; a few tufts of weeds in the earth."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b

GROUND_R = 1.32
GROUND_TOP = 0.1
PAD_R = 0.82                      # the concrete pad
TOP_Z = 0.2                       # its top = where she stands
STAND = v3((0.0, 0.0, TOP_Z))
RING_R = 0.74                     # the lights, in the pad's edge
N_GLOW = 12


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.02 * max(0.0, 1 - (r / GROUND_R) ** 2)


def _placed(angle_deg, r):
    """A prop's place round her: (centre on the ground, its inward direction (toward her), its tangent)."""
    a = math.radians(angle_deg)
    c = v3((math.cos(a) * r, math.sin(a) * r, 0.0))
    c[2] = ground_height(c[0], c[1])
    inward = -norm(v3((c[0], c[1], 0.0)))
    tang = norm(np.cross(v3((0, 0, 1)), inward))
    return c, inward, tang


WALL_A = (52.0, 142.0)            # the sandbag wall behind her (degrees round her: +x her left, +y behind her)
WALL_R = 1.1
FLAG = _placed(36.0, 1.08)
RADIO = _placed(162.0, 1.0)
AMMO = _placed(222.0, 1.02)
CANS = _placed(-42.0, 1.02)
JERRY = _placed(-12.0, 1.1)
TUFTS = [v3((1.2, -0.3, 0.0)), v3((-1.2, -0.25, 0.0)), v3((0.25, -1.2, 0.0)), v3((-0.55, -1.12, 0.0)), v3((0.9, 0.9, 0.0)),
         v3((-1.05, 0.62, 0.0))]


# ---------------------------------------------------------------------------------------------- the ground and the pad
def ground_field():
    """Packed earth (ground's trampled dirt, label 5 over all its top) on a low round mound, pebbles in it."""
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.025) * np.sin(a * 5 + 0.7) + F(0.015) * np.sin(a * 11 + 2.1)
        dome = F(GROUND_TOP) + F(0.02) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.05), 0), np.maximum(dz + F(0.05), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.05), dz + F(0.05)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.05)
    def relief(P):
        top = smoothstep(GROUND_TOP - 0.03, GROUND_TOP + 0.005, P[:, 2])
        ruts = F(0.006) * np.sin(P[:, 0] * F(9) + F(2) * NOISE(P * F(2)))
        return (F(0.004) * NOISE(P * F(12)) + ruts * F(0.5)) * top + F(0.0015) * NOISE(P * F(40))
    fd.add(Func(disc, (-1.45, -1.45, -0.2), (1.45, 1.45, 0.2), disp=relief, disp_amp=0.012), 0.0, 5)
    rs = np.random.RandomState(17)
    for k in range(22):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.9, 1.25)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0.0))
        c[2] = ground_height(c[0], c[1]) - 0.004
        fd.add(Stone(c, rs.uniform(0.016, 0.03), seed=k, squash=(1.0, 0.9, 0.6)), 0.004, 5)
    return fd


def pad_field():
    """Concrete (flagstone's grey stone): the round pad, its edge chamfered and chipped, expansion joints across it, a
    fitting cut into its edge for each light."""
    fd = Field("Pad")
    z0, z1 = GROUND_TOP - 0.06, TOP_Z
    def slab(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        d_r = r - F(PAD_R)
        d_z = np.maximum(P[:, 2] - F(z1), F(z0) - P[:, 2])
        q = np.stack([np.maximum(d_r + F(0.018), 0), np.maximum(d_z + F(0.018), 0)], 1)
        return np.minimum(np.maximum(d_r + F(0.018), d_z + F(0.018)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.018)
    def joints(P):
        j = np.minimum(np.abs(P[:, 0] + F(0.004)), np.abs(P[:, 1] - F(0.003)))
        top = smoothstep(TOP_Z - 0.02, TOP_Z, P[:, 2])
        return F(0.006) * (F(1) - smoothstep(0.0, 0.007, j)) * top + F(0.0012) * NOISE(P * F(30)) + F(0.002) * NOISE(P * F(7))
    fd.add(Func(slab, (-0.9, -0.9, z0 - 0.05), (0.9, 0.9, z1 + 0.05), disp=joints, disp_amp=0.007), 0.0)
    rs = np.random.RandomState(5)
    for k in range(7):                                                   # chips out of its edge
        a = rs.uniform(0, 2 * math.pi)
        fd.sub(Sphere(v3((math.cos(a) * (PAD_R + 0.01), math.sin(a) * (PAD_R + 0.01), TOP_Z + 0.004)), rs.uniform(0.02, 0.035)), 0.008)
    for i in range(N_GLOW):
        c = glow_pos(i)
        fd.sub(Cylinder(c + v3((0, 0, 0.0)), 0.04, 0.04, rr=0.004), 0.004)
    return fd


def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + math.radians(15)
    return v3((math.cos(a) * RING_R, math.sin(a) * RING_R, TOP_Z + 0.006))


def rim_field():
    """The lights' fittings: steel bezels (fieldgun's bright steel, label 7) round each, two bolts (8)."""
    fd = Field("Rim")
    for i in range(N_GLOW):
        c = glow_pos(i)
        fd.add(Torus(c + v3((0, 0, -0.002)), 0.034, 0.008), 0.0, 7)
        fd.add(Cylinder(c + v3((0, 0, -0.012)), 0.038, 0.012, rr=0.003), 0.003, 8)
        t = norm(np.cross(v3((0, 0, 1)), c))
        for s in (-1, 1):
            fd.add(Sphere(c + t * (s * 0.042) + v3((0, 0, -0.004)), 0.006), 0.002, 8)
    return fd


def glowmarks_field():
    """The hero ring: twelve amber runway lights (domed lenses; they glow)."""
    fd = Field("Glowmarks")
    for i in range(N_GLOW):
        c = glow_pos(i)
        fd.add(Ellipsoid(c + v3((0, 0, 0.002)), (0.028, 0.028, 0.018)), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the sandbag wall
def bag_specs():
    """(centre, tangent, inward, length) of each bag: three staggered courses along the arc behind her, the top course a
    little shorter at the ends."""
    out = []
    a0, a1 = math.radians(WALL_A[0]), math.radians(WALL_A[1])
    L = 0.3
    rs = np.random.RandomState(23)
    for course in range(3):
        z = GROUND_TOP + 0.05 + course * 0.095
        r = WALL_R - 0.012 * course
        span = (a1 - a0) - (0.12 if course == 2 else 0.0)
        n = int(round(span * r / L))
        step = span / n
        for k in range(n + (0 if course % 2 == 0 else -1)):
            a = a0 + (0.06 if course == 2 else 0.0) + step * (k + (0.5 if course % 2 == 0 else 1.0)) + rs.uniform(-0.02, 0.02)
            c = v3((math.cos(a) * r, math.sin(a) * r, z + rs.uniform(-0.006, 0.006)))
            inward = -norm(v3((c[0], c[1], 0.0)))
            tang = norm(np.cross(v3((0, 0, 1)), inward))
            out.append((c, tang, inward, step * r * 0.98, rs.uniform(-0.08, 0.08)))
    return out


def sandbags_field():
    """Sacking (label 0): pillowy bags, slumped and squashed under the course above, tied ends tucked under, a few with a
    stencilled mark (5)."""
    fd = Field("Sandbags")
    lump = lambda P: F(0.004) * NOISE(P * F(14)) + F(0.0015) * NOISE(P * F(45))
    for i, (c, t, inw, L, tw) in enumerate(bag_specs()):
        R = np.stack([t, inw, v3((0, 0, 1))], 1) @ euler(0, 0, tw)
        fd.add(RoundBox(c, (L * 0.5, 0.09, 0.052), 0.045, R=R, disp=lump, disp_amp=0.005), 0.012)
        fd.add(Ellipsoid(c + v3((0, 0, 0.012)), (L * 0.42, 0.08, 0.05), R=R), 0.02)               # (the bulge)
        if i % 5 == 2:
            fd.paint(RoundBox(c - inw * 0.09, (0.05, 0.03, 0.022), 0.005, R=R), 5)
    return fd


# ---------------------------------------------------------------------------------------------- crates and cans
def _box(fd, c, R, half, r, label, planks=None):
    fd.add(RoundBox(c, half, r, R=R), 0.0, label)
    if planks:                                           # grooves between the boards (along the box's x)
        axis, n = planks
        for k in range(1, n):
            z = -half[2] + 2 * half[2] * k / n
            fd.sub(RoundBox(c + R[:, 2] * z, (half[0] + 0.01, half[1] + 0.01, 0.0025), 0.001, R=R), 0.0015)


def crates_field():
    """fieldgun: the ammunition crate (olive paint, 0, over boards; rope handles, cord 10; black stencils 8; steel (7)
    latches), the radio's crate (oiled wood, 9; steel corners), three ammo cans (olive, 0; steel latches and handles,
    7; a yellow-white (13) stencil band), the jerrycan (olive, 0; its three handles; steel cap, 7)."""
    fd = Field("Crates")
    # the long ammunition crate before her on her right
    c, inw, tg = AMMO
    R = np.stack([tg, inw, v3((0, 0, 1))], 1) @ euler(0, 0, 0.35)
    h = 0.17
    b = c + v3((0, 0, h / 2 - 0.004))
    _box(fd, b, R, (0.24, 0.12, h / 2), 0.012, 0, planks=(0, 3))
    fd.add(RoundBox(b + v3((0, 0, h / 2 - 0.006)), (0.245, 0.125, 0.012), 0.006, R=R), 0.003, 0)      # the lid
    for s in (-1, 1):
        fd.add(RoundBox(b + R[:, 0] * (s * 0.2), (0.02, 0.126, h / 2 + 0.006), 0.006, R=R), 0.003, 0)    # end battens
        fd.add(Torus(b + R[:, 0] * (s * 0.255) + v3((0, 0, 0.01)), 0.03, 0.007, R=rot_from_axes(z_axis=R[:, 1])), 0.003, 10)
        fd.add(RoundBox(b - R[:, 1] * 0.124 + R[:, 0] * (s * 0.12) + v3((0, 0, 0.055)), (0.014, 0.006, 0.02), 0.003, R=R), 0.002, 7)
    for k in range(3):                                                                                  # stencils
        fd.paint(RoundBox(b - R[:, 1] * 0.13 + R[:, 0] * (-0.1 + 0.07 * k) + v3((0, 0, -0.03)), (0.026, 0.02, 0.012), 0.002, R=R), 8)
    # an ammo can on the crate
    ac = b + v3((0, 0, h / 2 + 0.006)) + R[:, 0] * 0.08
    _can(fd, ac, R @ euler(0, 0, -0.5))
    # the radio's crate behind her on her right
    c, inw, tg = RADIO
    R = np.stack([tg, inw, v3((0, 0, 1))], 1) @ euler(0, 0, -0.2)
    hb = 0.26
    b = c + v3((0, 0, hb / 2 - 0.004))
    _box(fd, b, R, (0.17, 0.15, hb / 2), 0.01, 9, planks=(0, 4))
    for s in (-1, 1):
        for t in (-1, 1):
            fd.add(RoundBox(b + R[:, 0] * (s * 0.165) + R[:, 1] * (t * 0.145), (0.012, 0.012, hb / 2 + 0.002), 0.004, R=R), 0.003, 7)
    # two ammo cans and a jerrycan before her on her left
    c, inw, tg = CANS
    R = np.stack([tg, inw, v3((0, 0, 1))], 1)
    _can(fd, c + R[:, 0] * -0.07, R @ euler(0, 0, 0.1))
    _can(fd, c + R[:, 0] * 0.08 + R[:, 1] * 0.03, R @ euler(0, 0, -0.25))
    _can(fd, c + v3((0, 0, 0.142)) + R[:, 0] * 0.0, R @ euler(0, 0, 0.6))
    c, inw, tg = JERRY
    R = np.stack([tg, inw, v3((0, 0, 1))], 1) @ euler(0, 0, 0.4)
    jb = c + v3((0, 0, 0.17))
    fd.add(RoundBox(jb, (0.1, 0.055, 0.17), 0.02, R=R), 0.0, 0)
    for s in (-1, 1):                                                                                   # the X pressings
        for d2 in (R[:, 0] + R[:, 2], R[:, 0] - R[:, 2]):
            dn = norm(d2)
            fd.sub(RoundBox(jb + R[:, 1] * (s * 0.056), (0.11, 0.004, 0.006), 0.002, R=np.stack([dn, R[:, 1], np.cross(dn, R[:, 1])], 1)), 0.002)
    for k in (-1, 0, 1):                                                                                # the three handles
        fd.add(Torus(jb + R[:, 0] * (k * 0.045 - 0.01) + v3((0, 0, 0.175)), 0.016, 0.006, R=rot_from_axes(z_axis=R[:, 1])), 0.003, 0)
    fd.add(Cylinder(jb + R[:, 0] * 0.07 + v3((0, 0, 0.18)), 0.018, 0.03, rr=0.005), 0.004, 7)          # the cap
    return fd


def _can(fd, c, R):
    """An ammo can: an olive steel box (0), its lid's latch and carrying handle (7), a pale stencil band (13)."""
    h = 0.13
    b = c + v3((0, 0, h / 2))
    fd.add(RoundBox(b, (0.13, 0.055, h / 2), 0.008, R=R), 0.0, 0)
    fd.add(RoundBox(b + v3((0, 0, h / 2 - 0.008)), (0.134, 0.06, 0.012), 0.005, R=R), 0.003, 0)
    fd.add(Torus(b + v3((0, 0, h / 2 + 0.008)), 0.028, 0.005, R=rot_from_axes(z_axis=R[:, 1])), 0.002, 7)
    fd.add(RoundBox(b + R[:, 0] * 0.135 + v3((0, 0, 0.03)), (0.006, 0.03, 0.02), 0.003, R=R), 0.002, 7)
    fd.paint(RoundBox(b - R[:, 1] * 0.06 + v3((0, 0, 0.0)), (0.07, 0.012, 0.012), 0.002, R=R), 13)


# ---------------------------------------------------------------------------------------------- the radio set
def radio_frame():
    c, inw, tg = RADIO
    R = np.stack([tg, inw, v3((0, 0, 1))], 1) @ euler(0, 0, -0.2)
    top = c + v3((0, 0, 0.26 - 0.004))
    return top, R


def radio_field():
    """armory: the field radio (dark (8) case; black (5) knobs, its handset and coiled cord; bright steel (7) catches), a
    small display, its whip antenna (8)."""
    fd = Field("Radio")
    top, R = radio_frame()
    b = top + v3((0, 0, 0.07)) + R[:, 1] * 0.02
    fd.add(RoundBox(b, (0.13, 0.08, 0.07), 0.012, R=R), 0.0, 8)
    fp = b + R[:, 1] * 0.08                                                     # its front panel (toward her)
    for k, (dx, dz) in enumerate(((-0.08, 0.025), (-0.04, 0.025), (0.0, 0.025), (-0.08, -0.02))):
        fd.add(Cylinder(fp + R[:, 0] * dx + v3((0, 0, dz)) + R[:, 1] * 0.008, 0.013, 0.018, rr=0.004, R=rot_from_axes(z_axis=R[:, 1])), 0.003, 5)
    fd.add(RoundBox(fp + R[:, 0] * 0.06 + v3((0, 0, 0.012)) + R[:, 1] * 0.003, (0.045, 0.006, 0.03), 0.004, R=R), 0.002, 7)   # the display
    for s in (-1, 1):
        fd.add(RoundBox(b + R[:, 0] * (s * 0.132) + v3((0, 0, 0.0)), (0.006, 0.03, 0.02), 0.003, R=R), 0.002, 7)
    # the antenna from its back corner
    ab = b + R[:, 0] * 0.09 - R[:, 1] * 0.05 + v3((0, 0, 0.07))
    fd.add(Cylinder(ab + v3((0, 0, 0.015)), 0.014, 0.03, rr=0.004), 0.003, 8)
    tip = ab + norm(v3((0, 0, 1)) - R[:, 1] * 0.08) * 0.9
    fd.add(RoundCone(ab + v3((0, 0, 0.02)), tip, 0.0075, 0.0055), 0.003, 8)
    fd.add(Sphere(tip, 0.01), 0.003, 8)
    # the handset lying on the crate beside it, its coiled cord
    hs = top + R[:, 0] * -0.06 + R[:, 1] * 0.11 + v3((0, 0, 0.022))
    Rh = R @ euler(0, 0, 0.5)
    fd.add(RoundBox(hs, (0.02, 0.05, 0.016), 0.012, R=Rh), 0.004, 5)
    for s in (-1, 1):
        fd.add(RoundBox(hs + Rh[:, 1] * (s * 0.05) + v3((0, 0, 0.012)), (0.024, 0.022, 0.016), 0.01, R=Rh), 0.004, 5)
    a, z = hs - Rh[:, 1] * 0.06, fp + R[:, 0] * -0.1 + v3((0, 0, -0.045))
    coil = []
    for i in range(60):
        t = i / 59.0
        p = lerp(a, z, t) + v3((0, 0, 0.03 * math.sin(math.pi * t)))
        ang = 2 * math.pi * 9 * t
        coil.append(p + (R[:, 0] * math.cos(ang) + v3((0, 0, 1)) * math.sin(ang)) * 0.008)
    fd.add(Chain(coil, [0.0035] * len(coil), k=0.002), 0.003, 5)
    return fd


# ---------------------------------------------------------------------------------------------- the flag
POLE_H = 1.95


def metal_field():
    """fieldgun: the flag pole's concrete block (grey paint, 5), the steel pole (7) with its finial and halyard cleat."""
    fd = Field("Metal")
    c, inw, tg = FLAG
    fd.add(RoundBox(c + v3((0, 0, 0.06)), (0.09, 0.09, 0.07), 0.015, R=np.stack([tg, inw, v3((0, 0, 1))], 1)), 0.0, 5)
    top = v3((c[0], c[1], POLE_H))
    fd.add(RoundCone(c + v3((0, 0, 0.1)), top, 0.016, 0.012), 0.004, 7)
    fd.add(Sphere(top + v3((0, 0, 0.022)), 0.024), 0.004, 7)
    fd.add(RoundBox(c + v3((0, 0, 0.6)) + inw * 0.018, (0.01, 0.008, 0.03), 0.003), 0.003, 7)
    return fd


def flag_pts():
    c, inw, tg = FLAG
    top = v3((c[0], c[1], POLE_H - 0.03))
    fly = norm(-inw * 0.8 + tg * 0.3 + v3((0, 0, -0.08)))                       # streaming out to her left
    return top, fly


def flag_field():
    """The guidon: red cloth (uniform's cloth, label 0) with the unit's white (7) chevron, a swallowtail fly, rippling."""
    fd = Field("Flag")
    top, fly = flag_pts()
    up = v3((0, 0, 1))
    nrm = norm(np.cross(fly, up))
    W, H = 0.36, 0.22
    def cloth(P):
        q = P - top.astype(F)
        u = q @ fly.astype(F)
        v = q[:, 2]
        n = q @ nrm.astype(F)
        wave = F(0.03) * np.sin(u * F(16) - F(0.6)) * np.clip(u / F(0.08), 0, 1) + F(0.01) * np.sin(v * F(20))
        inside = np.maximum(np.maximum(-u, u - F(W)), np.maximum(v, -F(H) - v))
        thr = F(W) - F(0.085) * (F(1) - np.abs(v + F(H * 0.5)) * F(2.0 / H))          # the swallowtail's notch
        return np.maximum(np.maximum(inside, u - thr), np.abs(n - wave) - F(0.006))
    fd.add(Func(cloth, top - 0.5, top + 0.5), 0.0)
    def chevron(P):
        q = P - top.astype(F)
        u = q @ fly.astype(F) - F(W * 0.32)
        v = q[:, 2] + F(H * 0.5)
        ch = np.abs(v - F(0.03) + np.abs(u) * F(1.1)) - F(0.016)
        return np.maximum(ch, np.abs(u) - F(0.07))
    fd.paint(Func(chevron, top - 0.5, top + 0.5), 7)
    return fd


# ---------------------------------------------------------------------------------------------- weeds
def grass_geometry(seed=59):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    for ti, c in enumerate(TUFTS):
        for b in range(10):
            ang = rs.uniform(0, 2 * math.pi)
            out = v3((math.cos(ang), math.sin(ang), 0))
            root = c + out * rs.uniform(0, 0.035)
            root[2] = ground_height(root[0], root[1]) - 0.008
            d = norm(out * rs.uniform(0.25, 0.6) + v3((0, 0, 1)))
            L = rs.uniform(0.07, 0.15)
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.014, 0.02), out * rs.uniform(0.6, 1.2) + v3((0, 0, -0.3)), segs=4,
                                     twist=rs.uniform(-0.5, 0.5))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=61):
    return []


def fields():
    return [("Ground", ground_field(), 0.008), ("Pad", pad_field(), 0.005), ("Rim", rim_field(), 0.0025),
            ("Glowmarks", glowmarks_field(), 0.0025), ("Sandbags", sandbags_field(), 0.005), ("Crates", crates_field(), 0.003),
            ("Radio", radio_field(), 0.0025), ("Metal", metal_field(), 0.003), ("Flag", flag_field(), 0.003)]


REGION_PARTS = ("Ground", "Rim", "Sandbags", "Crates", "Radio", "Metal", "Flag")
LOW_TARGETS = {"Ground": 2200, "Pad": 1500, "Rim": 900, "Glowmarks": 300, "Sandbags": 3000, "Crates": 2200, "Radio": 1100,
               "Metal": 300, "Flag": 400}
OLIVE_PAINT = (0.36, 0.38, 0.24)
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_PackedEarth", "dirt_label": 5}),
                 "Pad": ("flagstone", {"name": "HQ_Concrete", "base": (0.6, 0.59, 0.56), "alt": (0.66, 0.64, 0.6)}),
                 "Rim": ("fieldgun", {"name": "HQ_FobKit", "olive": OLIVE_PAINT}),
                 "Sandbags": ("sacking", {"name": "HQ_Sandbags"}),
                 "Crates": ("fieldgun", {"name": "HQ_FobKit", "olive": OLIVE_PAINT}),
                 "Radio": ("armory", {"name": "HQ_FobRadio", "grip": (0.09, 0.09, 0.09)}),
                 "Metal": ("fieldgun", {"name": "HQ_FobKit", "olive": OLIVE_PAINT}),
                 "Flag": ("uniform", {"name": "HQ_Guidon", "base": (0.78, 0.1, 0.08), "buff": (0.95, 0.94, 0.9)})}
GLOW = {"Glowmarks": ((1.0, 0.62, 0.18), 1.0, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
