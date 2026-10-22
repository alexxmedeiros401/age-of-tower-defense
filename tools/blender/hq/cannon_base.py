"""Cannon base: a gun platform on a bastion of the star fort. The round plinth is the bastion's top: a ring of dressed
limestone blocks in two courses holds rammed earth; on it a round deck of heavy oak planks laid front to back, pinned
with trenails over three sleepers, inside a low kerb of curved oak timbers with iron dogs. Nothing on the deck stands
proud of the planks (the gun recoils over it and the whole crew sweeps it when the tower turns). Beyond the kerb, earth
and grass: at the back three gabions (wicker baskets packed with earth) and the army's small crimson-and-gold flag on a
pole; on the left a ridge pile of iron round shot and a bucket of water for the sponge; on the right a powder keg with
a crimson band and a second keg on its side; broad tropical leaves with red blooms at the edge, pebbles (distance
fields + direct low-poly geometry for the grass, the leaves and the flowers)."""
import math
import numpy as np
from sdf import (Field, Sphere, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Ellipsoid, v3, norm, rot_from_axes,
                 smax, NOISE, F)
from caveman import Stone, Inter, Shell
import base as _b
import cannon as _c
from crossbowman_base import _bloom

GROUND_R = 1.55
GROUND_TOP = 0.1
FLOOR_R = 1.27                 # the deck's edge (the recoiling trail sweeps up to ~1.22 of it)
KERB_W = 0.08                  # the kerb's width outside the deck
TOP_Z = 0.16                   # the deck's top: where the gun and his feet rest
STAND = v3((-_c.YAW_PIVOT[0], -_c.YAW_PIVOT[1], TOP_Z))
PLANK_W = 0.16
PLANK_H = 0.032                # half thickness
SLEEPERS = (-0.62, 0.0, 0.62)  # y of the sleepers under the planks (the trenail rows)
WALL_IN = GROUND_R - 0.07      # the revetment's inner face (earth inside it)
WALL_OUT = GROUND_R + 0.015
WALL_TOP = GROUND_TOP + 0.012
WALL_BOT = -0.14
PROP_R = 1.43                  # the props' ring, between the kerb and the coping
GABIONS = (math.radians(83.8), math.radians(90.0), math.radians(96.2))     # behind (+Y), shoulder to shoulder
FLAG_A, FLAG_R = math.radians(111.0), 1.47                                   # beyond the crew's reach
SHOT_A = math.radians(205.0)                                                 # the round shot: on the left
BUCKET_A = math.radians(232.0)
KEG_A = math.radians(20.0)                                                   # the powder: on the right
KEG2_A = math.radians(352.0)
PLANTS = (math.radians(150.0), math.radians(178.0), math.radians(262.0), math.radians(302.0), math.radians(52.0))
SHOT_R = _c.ROUND_R            # the gun's own round shot


def ground_height(x, y):
    r = math.hypot(x, y)
    if r < FLOOR_R:
        return TOP_Z
    if r > WALL_IN:
        return WALL_TOP
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    """The bastion's rammed earth, inside the stone ring."""
    fd = Field("Ground")
    RE = WALL_IN + 0.04
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        dome = F(GROUND_TOP) + F(0.03) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - F(RE)
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.04), 0), np.maximum(dz + F(0.04), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.04), dz + F(0.04)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.04)
    fd.add(Func(disc, (-RE - 0.05, -RE - 0.05, -0.2), (RE + 0.05, RE + 0.05, 0.2),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def wall_field():
    """The bastion's revetment: dressed limestone blocks in two courses, the joints staggered, each block a little
    proud or sunk on its own, the upper course a coping a shade proud of the lower."""
    fd = Field("Wall")
    n = 26
    rs = np.random.RandomState(5)
    off = rs.uniform(-0.004, 0.004, (2, n)).astype(F)
    off[1] += F(0.005)
    gap = F(0.0045)
    zc = F(-0.035)                                                  # the course joint
    step = F(2 * math.pi / n)
    rm, hw = F((WALL_IN + WALL_OUT) / 2), F((WALL_OUT - WALL_IN) / 2)
    zm, hh = F((WALL_TOP + WALL_BOT) / 2), F((WALL_TOP - WALL_BOT) / 2)
    def fn(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.sqrt(x * x + y * y)
        a = np.arctan2(y, x)
        upper = z > zc
        u = a / step + np.where(upper, F(0.5), F(0.0))                 # staggered joints
        k = np.floor(u).astype(np.int64) % n
        o = off[upper.astype(np.int64), k]
        dr = np.abs(r - rm - o) - hw
        dz = np.abs(z - zm) - hh
        rr = F(0.009)
        q = np.stack([np.maximum(dr + rr, 0), np.maximum(dz + rr, 0)], 1)
        d = np.sqrt((q ** 2).sum(1)) + np.minimum(np.maximum(dr, dz) + rr, 0) - rr
        dj = gap - np.abs(u - np.round(u)) * step * r                  # the vertical joints
        dc = gap - np.abs(z - zc)                                      # the course joint
        return smax(smax(d, dj, 0.005), dc, 0.005)
    R = WALL_OUT + 0.03
    fd.add(Func(fn, (-R, -R, WALL_BOT - 0.02), (R, R, WALL_TOP + 0.02),
                disp=lambda P: F(0.0022) * NOISE(P * F(13)) + F(0.0009) * NOISE(P * F(55)), disp_amp=0.004), 0.0)
    return fd


def _grain(P):
    return F(0.0016) * NOISE(P * np.array([70, 6, 70], F)) + F(0.0008) * NOISE(P * F(140))


def deck_func(seed=11):
    """The planks: strips along Y sawn round to the deck's edge, gaps between them, each a little proud or sunk and
    tilted on its own, their ends butting at staggered joints over the sleepers."""
    rs = np.random.RandomState(seed)
    n = int(2 * FLOOR_R / PLANK_W) + 3
    dzs = rs.uniform(-0.004, 0.0025, (n, 2)).astype(F)
    tilt = rs.uniform(-0.004, 0.004, (n, 2)).astype(F)
    joint = np.where(np.arange(n) % 2 == 0, F(SLEEPERS[0]), F(SLEEPERS[2])).astype(F)
    gap = F(0.006)
    rr = F(0.007)
    def fn(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        u = (x + F(FLOOR_R + PLANK_W * 0.41)) / F(PLANK_W)
        k = np.clip(np.floor(u).astype(np.int64), 0, n - 1)
        du = (u - np.floor(u) - F(0.5)) * F(PLANK_W)
        d_u = np.abs(du) - (F(PLANK_W * 0.5) - gap)
        j = joint[k]
        seg = (y > j).astype(np.int64)
        d_j = gap - np.abs(y - j)                                  # the butt joint across the plank
        r = np.sqrt(x * x + y * y)
        d_r = r - F(FLOOR_R - 0.012)
        top = F(TOP_Z) + dzs[k, seg] + tilt[k, seg] * y
        d_z = np.abs(z - (top - F(PLANK_H))) - F(PLANK_H)
        q = np.stack([d_u + rr, d_r + rr, d_z + rr], 1)
        out = np.sqrt((np.maximum(q, 0) ** 2).sum(1))
        return np.maximum(out + np.minimum(q.max(1), 0) - rr, d_j)
    R = FLOOR_R + 0.02
    return Func(fn, (-R, -R, TOP_Z - 2 * PLANK_H - 0.02), (R, R, TOP_Z + 0.03), disp=_grain, disp_amp=0.003)


def deck_field():
    """The planks (oak, grain along Y: label 0) and their trenails (oak end grain, darker: label 11)."""
    fd = Field("Deck")
    fd.add(deck_func(), 0.0, 0)
    fd.add(Cylinder(v3((0, 0, TOP_Z - 2 * PLANK_H - 0.02)), FLOOR_R - 0.03, 0.06, rr=0.01), 0.0, 0)
    n = int(2 * FLOOR_R / PLANK_W) + 3
    for i in range(n):
        xc = -FLOOR_R - PLANK_W * 0.41 + (i + 0.5) * PLANK_W
        for ys in SLEEPERS:
            for dx in (-0.038, 0.038):
                p = v3((xc + dx, ys + (0.03 if ys != 0.0 and abs(ys) > 0.1 and i % 2 == (0 if ys < 0 else 1) else 0.0), TOP_Z))
                if math.hypot(p[0], p[1]) < FLOOR_R - 0.07:
                    fd.add(Cylinder(p + v3((0, 0, -0.004)), 0.011, 0.01, rr=0.003), 0.002, 11)
    return fd


def kerb_field():
    """A ring of curved oak timbers round the deck, a little proud of it, jointed with iron dogs (6)."""
    fd = Field("Kerb")
    r0, r1 = FLOOR_R - 0.01, FLOOR_R + KERB_W
    top = TOP_Z + 0.025
    def ring(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        seg = np.abs(((a + F(0.2)) / F(2 * math.pi / 10)) - np.round((a + F(0.2)) / F(2 * math.pi / 10))) * F(2 * math.pi / 10) * r
        dr = np.abs(r - F((r0 + r1) / 2)) - F((r1 - r0) / 2)
        dz = np.abs(P[:, 2] - F((top + GROUND_TOP - 0.04) / 2)) - F((top - GROUND_TOP + 0.04) / 2)
        dj = F(0.004) - seg
        q = np.stack([np.maximum(dr + F(0.008), 0), np.maximum(dz + F(0.008), 0)], 1)
        d = np.sqrt((q ** 2).sum(1)) + np.minimum(np.maximum(dr, dz) + F(0.008), 0) - F(0.008)
        return np.maximum(d, dj)
    R = r1 + 0.05
    grain = lambda P: F(0.0014) * NOISE(np.stack([np.arctan2(P[:, 1], P[:, 0]) * F(8), P[:, 2] * F(60), np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) * F(60)], 1))
    fd.add(Func(ring, (-R, -R, GROUND_TOP - 0.1), (R, R, top + 0.03), disp=grain, disp_amp=0.002), 0.0, 10)
    for k in range(10):
        a = 2 * math.pi * k / 10 - 0.2
        c = v3((math.cos(a) * (r0 + r1) / 2, math.sin(a) * (r0 + r1) / 2, top))
        t = v3((-math.sin(a), math.cos(a), 0.0))
        fd.add(RoundBox(c, (0.012, 0.045, 0.006), 0.003, R=rot_from_axes(z_axis=(0, 0, 1), y_axis=t)), 0.002, 6)
        for s in (-1, 1):
            fd.add(Sphere(c + t * (s * 0.038), 0.009), 0.002, 6)
    return fd


def _gabion_c(i, a):
    c = v3((math.cos(a) * PROP_R, math.sin(a) * PROP_R, 0.0))
    z0 = ground_height(c[0], c[1]) - 0.03
    h = (0.29, 0.33, 0.27)[i]
    return c, z0, h


def gabion_field():
    """Three gabions shoulder to shoulder: wicker baskets (stakes and woven withies) packed with earth."""
    fd = Field("Gabions")
    for i, a in enumerate(GABIONS):
        c, z0, h = _gabion_c(i, a)
        r = 0.075
        def weave(P, c=c):
            q = P - c.astype(F)
            ang = np.arctan2(q[:, 1], q[:, 0])
            return F(0.004) * np.sin(ang * F(9)) * np.sin(q[:, 2] * F(110)) + F(0.0012) * NOISE(P * F(60))
        fd.add(Inter(Shell(Cylinder(c + v3((0, 0, z0 + h / 2)), r, h, rr=0.01), 0.0, 0.016, disp=weave, disp_amp=0.006),
                     Func(lambda P, z0=z0, h=h: P[:, 2] - F(z0 + h - 0.006), c - 0.3, c + 0.6), 0.004), 0.0)
        for k in range(8):                                                        # the stakes, proud of the rim
            ak = 2 * math.pi * k / 8 + 0.2 * i
            p = c + v3((math.cos(ak) * r, math.sin(ak) * r, 0))
            fd.add(RoundCone(p + v3((0, 0, z0)), p + v3((0, 0, z0 + h + 0.035)), 0.009, 0.006), 0.003)
    return fd


def gabion_fill():
    fd = Field("Fill")
    for i, a in enumerate(GABIONS):
        c, z0, h = _gabion_c(i, a)
        fd.add(Ellipsoid(c + v3((0, 0, z0 + h - 0.015)), (0.07, 0.07, 0.035), disp=lambda P: F(0.004) * NOISE(P * F(20)), disp_amp=0.005), 0.0)
    return fd


def _ring_frame(a, r):
    o = v3((math.cos(a), math.sin(a), 0.0))
    t = v3((-math.sin(a), math.cos(a), 0.0))
    return o * r, o, t


def shot_centres():
    """A ridge pile: three by two on the ground, two more in the hollows along the top."""
    c, o, t = _ring_frame(SHOT_A, PROP_R + 0.02)          # the outer row rests on the coping, clear of the kerb
    R = SHOT_R + 0.0015
    out = []
    for j in (-0.5, 0.5):
        for i in (-1, 0, 1):
            p = c + t * (i * 2 * R) + o * (j * 2 * R)
            p[2] = ground_height(p[0], p[1]) + SHOT_R - 0.004
            out.append(p)
    z = sum(p[2] for p in out) / len(out) + R * math.sqrt(2)
    for i in (-0.5, 0.5):
        p = c + t * (i * 2 * R)
        p[2] = z
        out.append(p)
    return out


def shot_field():
    fd = Field("Shot")
    for i, p in enumerate(shot_centres()):
        fd.add(Sphere(p, SHOT_R, disp=lambda P: F(0.0009) * NOISE(P * F(90)) + F(0.0006) * NOISE(P * F(31)), disp_amp=0.0015), 0.0)
    return fd


def _cask(fd, c, ax, h, r_end, r_belly, n=14, grain=11, head=10, band=True):
    """A small cask: bulging staves (grain along the cask), their joints a shallow groove, the heads sunk inside the
    chimes (grain across), four iron hoops (6), a band of crimson paint round the belly (5)."""
    c = v3(c)
    ax = norm(ax)
    e1 = norm(np.cross(ax, v3((0, 0, 1)) if abs(ax[2]) < 0.9 else v3((1, 0, 0))))
    e2 = np.cross(ax, e1)
    cf, af, e1f, e2f = c.astype(F), ax.astype(F), e1.astype(F), e2.astype(F)
    def prof(t):
        return F(r_end) + F(r_belly - r_end) * (F(1) - t * t)
    def coords(P):
        q = P - cf
        a = q @ af
        x1, x2 = q @ e1f, q @ e2f
        return a, np.sqrt(x1 * x1 + x2 * x2), np.arctan2(x2, x1)
    def body(P):
        a, rho, th = coords(P)
        t = np.clip(a / F(h / 2), -1, 1)
        rad = prof(t)
        dr = (rho - rad) * F(0.97)
        da = np.abs(a) - F(h / 2)
        rr = F(0.006)
        q = np.stack([np.maximum(dr + rr, 0), np.maximum(da + rr, 0)], 1)
        d = np.sqrt((q ** 2).sum(1)) + np.minimum(np.maximum(dr, da) + rr, 0) - rr
        s = th / F(2 * math.pi / n)
        gd = np.abs(s - np.round(s)) * F(2 * math.pi / n) * rho
        groove = np.maximum(gd - F(0.0012), rad - F(0.0025) - rho)        # the stave joints
        d = np.maximum(d, -groove)
        sunk = np.maximum(rho - F(r_end - 0.008), F(h / 2 - 0.007) - np.abs(a))   # the heads inside the chimes
        return np.maximum(d, -sunk)
    B = h / 2 + r_belly + 0.02
    fd.add(Func(body, c - B, c + B, disp=lambda P: F(0.0007) * NOISE(P * F(80)), disp_amp=0.001), 0.0, grain)
    fd.paint(Func(lambda P: np.maximum(coords(P)[1] - F(r_end - 0.005), F(h / 2 - 0.012) - np.abs(coords(P)[0])), c - B, c + B), head)
    if band:
        fd.paint(Func(lambda P: np.abs(coords(P)[0]) - F(h * 0.13), c - B, c + B), 5)
    for t0 in (-0.84, -0.5, 0.5, 0.84):
        a0 = t0 * h / 2
        r0 = float(prof(F(t0))) + 0.0022
        def hoop(P, a0=a0, r0=r0):
            a, rho, _ = coords(P)
            dr = np.abs(rho - F(r0)) - F(0.0028)
            da = np.abs(a - F(a0)) - F(0.0075)
            return np.minimum(np.maximum(dr, da), 0) + np.sqrt(np.maximum(dr, 0) ** 2 + np.maximum(da, 0) ** 2)
        fd.add(Func(hoop, c - B, c + B), 0.001, 6)


def keg_place():
    c, o, t = _ring_frame(KEG_A, PROP_R)
    return c + v3((0, 0, ground_height(c[0], c[1]) - 0.004))


def keg2_place():
    c, o, t = _ring_frame(KEG2_A, PROP_R + 0.01)
    return c + v3((0, 0, ground_height(c[0], c[1]) + 0.058))


def bucket_place():
    c, o, t = _ring_frame(BUCKET_A, PROP_R)
    return c + v3((0, 0, ground_height(c[0], c[1]) - 0.004))


def flag_foot():
    c, o, t = _ring_frame(FLAG_A, FLAG_R)
    return c + v3((0, 0, ground_height(c[0], c[1]) - 0.05))


POLE_H = 1.08                  # the flagpole above its foot
FLAG_W = norm(v3((-1.0, 0.12, 0.0)))     # the way the flag flies (outward, seen broadside from the front)
FLAG_L, FLAG_H = 0.3, 0.19


def props_field():
    """The powder kegs (oak, iron hoops, a crimson band), the water bucket and the flagpole (oak, iron)."""
    fd = Field("Props")
    k = keg_place()
    _cask(fd, k + v3((0, 0, 0.1)), (0, 0, 1), 0.2, 0.062, 0.075)
    k2 = keg2_place()
    _cask(fd, k2, (0, 1, 0), 0.155, 0.048, 0.058, n=12, grain=0, head=10, band=False)
    fd.add(Stone(k2 + v3((0.055, -0.05, -0.045)), 0.022, seed=71, squash=(1, 1, 0.6)), 0.003, 10)   # a chock
    # the bucket: a tapered tub of staves, two hoops, an iron bail resting on the rim
    b = bucket_place()
    h, r0, r1 = 0.105, 0.052, 0.066
    bf = b.astype(F)
    def tub(P):
        q = P - bf
        z = q[:, 2]
        rho = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        rad = F(r0) + F(r1 - r0) * np.clip(z / F(h), 0, 1)
        dr = (rho - rad) * F(0.99)
        dz = np.maximum(-z, z - F(h))
        rr = F(0.004)
        qq = np.stack([np.maximum(dr + rr, 0), np.maximum(dz + rr, 0)], 1)
        d = np.sqrt((qq ** 2).sum(1)) + np.minimum(np.maximum(dr, dz) + rr, 0) - rr
        inner = np.maximum(rho - (rad - F(0.008)), F(0.012) - z)
        th = np.arctan2(q[:, 1], q[:, 0])
        s = th / F(2 * math.pi / 12)
        gd = np.abs(s - np.round(s)) * F(2 * math.pi / 12) * rho
        groove = np.maximum(gd - F(0.0011), rad - F(0.0022) - rho)
        return np.maximum(np.maximum(d, -inner), -groove)
    fd.add(Func(tub, b - 0.1, b + 0.15, disp=lambda P: F(0.0006) * NOISE(P * F(80)), disp_amp=0.001), 0.0, 11)
    for z0 in (0.022, 0.085):
        rz0 = r0 + (r1 - r0) * z0 / h + 0.0022
        def hoop(P, z0=z0, rz0=rz0):
            q = P - bf
            rho = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
            dr = np.abs(rho - F(rz0)) - F(0.0026)
            dz = np.abs(q[:, 2] - F(z0)) - F(0.007)
            return np.minimum(np.maximum(dr, dz), 0) + np.sqrt(np.maximum(dr, 0) ** 2 + np.maximum(dz, 0) ** 2)
        fd.add(Func(hoop, b - 0.1, b + 0.15), 0.001, 6)
    e = v3((math.cos(BUCKET_A + 0.6), math.sin(BUCKET_A + 0.6), 0.0))          # through the two lugs
    top = b + v3((0, 0, h - 0.012))
    for s in (-1, 1):
        fd.add(RoundBox(top + e * (s * (r1 + 0.002)), (0.006, 0.006, 0.012), 0.002, R=rot_from_axes(z_axis=(0, 0, 1), y_axis=e)), 0.002, 6)
    up = norm(np.cross(e, v3((0, 0, 1))) * math.sin(math.radians(62.0)) + v3((0, 0, 1)) * math.cos(math.radians(62.0)))
    nrm = norm(np.cross(e, up))
    fd.add(Inter(Torus(top, r1 + 0.006, 0.0035, R=rot_from_axes(z_axis=nrm)), Plane(top, -up)), 0.002, 6)
    # the flagpole: oak, an iron spike and knob at the top, wedged with stones at its foot
    f0 = flag_foot()
    f1 = f0 + v3((0, 0, POLE_H))
    fd.add(RoundCone(f0, f1, 0.014, 0.011), 0.0, 11)
    fd.add(Sphere(f1 + v3((0, 0, 0.01)), 0.016), 0.003, 6)
    fd.add(RoundCone(f1 + v3((0, 0, 0.02)), f1 + v3((0, 0, 0.075)), 0.009, 0.0015), 0.002, 6)
    for z in (0.92, 0.72):                                                          # the flag's ties
        fd.add(Torus(f0 + v3((0, 0, POLE_H * z)), 0.015, 0.003), 0.001, 5)
    return fd


def water_field():
    fd = Field("Water")
    b = bucket_place()
    h, r0, r1 = 0.105, 0.052, 0.066
    zw = h - 0.024                                       # a disc just under the rim (it never reaches the tapered foot)
    fd.add(Cylinder(b + v3((0, 0, zw - 0.006)), r0 + (r1 - r0) * zw / h - 0.006, 0.012, rr=0.002), 0.0)
    return fd


def _flag_coords(P):
    f1 = flag_foot() + v3((0, 0, POLE_H - 0.04))
    w = FLAG_W
    n = norm(np.cross(w, v3((0, 0, 1))))
    q = P - f1.astype(F)
    u = q @ w.astype(F) - F(0.014)
    v = -q[:, 2]
    s = q @ n.astype(F)
    return u, v, s


def flag_field():
    """The army's flag: crimson linen with a gold border (5) and a gold saltire (6), rippling in a breeze, its fly end
    sagging a little."""
    fd = Field("Flag")
    L, H = FLAG_L, FLAG_H
    def fn(P):
        u, v, s = _flag_coords(P)
        un = np.clip(u / F(L), 0, 1)
        sag = F(0.025) * un * un
        s0 = F(0.03) * np.sin(u * F(17.0) - F(0.4)) * un + F(0.006) * np.sin(v * F(23.0) + u * F(9.0))
        d_sheet = (np.abs(s - s0) - F(0.005)) * F(0.8)
        vv = v - sag
        d_box = np.maximum(np.maximum(-u, u - F(L)), np.maximum(-vv, vv - F(H)))
        return np.maximum(d_sheet, d_box)
    c = flag_foot() + v3((0, 0, POLE_H - 0.04))
    lo = c + v3((-0.45, -0.45, -0.3))
    hi = c + v3((0.45, 0.45, 0.06))
    fd.add(Func(fn, lo, hi), 0.0, 0)
    def border(P):
        u, v, s = _flag_coords(P)
        un = np.clip(u / F(L), 0, 1)
        vv = v - F(0.025) * un * un
        return F(0.02) - np.minimum(np.minimum(u, F(L) - u), np.minimum(vv, F(H) - vv))
    def saltire(P):
        u, v, s = _flag_coords(P)
        un = np.clip(u / F(L), 0, 1)
        vv = v - F(0.025) * un * un
        k = F(math.hypot(L, H))
        d1 = np.abs(u * F(H) - vv * F(L)) / k
        d2 = np.abs(u * F(H) + vv * F(L) - F(L * H)) / k
        return np.minimum(d1, d2) - F(0.017)
    fd.paint(Func(lambda P: -border(P), lo, hi), 5)
    fd.paint(Func(saltire, lo, hi), 6)
    return fd


def _avoid():
    """(angle, half-width in radians) of everything standing round the rim."""
    out = [(a, 0.07) for a in GABIONS] + [(FLAG_A, 0.05), (SHOT_A, 0.15), (BUCKET_A, 0.07), (KEG_A, 0.08), (KEG2_A, 0.09)]
    return out


def _clear(a, extra=0.0, plants=True):
    for s, w in _avoid():
        if abs((a - s + math.pi) % (2 * math.pi) - math.pi) < w + extra:
            return False
    if plants:
        for s in PLANTS:
            if abs((a - s + math.pi) % (2 * math.pi) - math.pi) < 0.08 + extra:
                return False
    return True


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(29)
    n = 0
    tries = 0
    while n < 11 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        if not _clear(a, 0.05):
            continue
        r = rs.uniform(FLOOR_R + KERB_W + 0.03, WALL_IN - 0.02)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.02, 0.03), seed=320 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    f0 = flag_foot()                                     # stones wedging the flagpole
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.4
        p = f0 + v3((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.0))
        p[2] = ground_height(p[0], p[1]) + 0.008
        fd.add(Stone(p, 0.024, seed=360 + i, squash=(1, 1, 0.7), noise=0.05), 0.0)
    return fd


def grass_geometry(seed=47):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 26 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(FLOOR_R + KERB_W + 0.02, WALL_IN - 0.01)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.12 for t in tufts) or not _clear(a, 0.0, plants=False):
            continue
        tufts.append(c)
    n_ground = len(tufts)
    for i, a in enumerate(GABIONS):                       # grass on the gabions' earth
        if i == 1:
            continue
        c, z0, h = _gabion_c(i, a)
        c = c.copy()
        c[2] = z0 + h + 0.012
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(7, 11)
        big = 0.6 + 0.35 * rs.rand()
        on_gab = ti >= n_ground
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.035)
            root = c + off
            root[2] = (c[2] if on_gab else ground_height(root[0], root[1])) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.25, 0.55) + v3((0, 0, 1)))
            L = rs.uniform(0.09, 0.16) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.04), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def _leaf(out, root, az, L, W, lift, roll):
    """A broad tropical leaf (a young banana, an elephant's ear): a stalk (stem swatch), then a wide blade (kind 3, the
    leaf green) folded a little along its midrib, arching over and drooping to its tip."""
    o = v3((math.cos(az), math.sin(az), 0.0))
    up = v3((0, 0, 1))
    side = norm(v3((-math.sin(az), math.cos(az), 0.0)) + up * roll)
    P0 = root
    P1 = root + o * (0.35 * L) + up * (0.7 * L * lift)
    P2 = root + o * L + up * (0.12 * L * lift - 0.1 * L)
    def m(t):
        return P0 * (1 - t) ** 2 + P1 * (2 * t * (1 - t)) + P2 * (t * t)
    ts = 0.28
    sv, sf = [], []
    for j, t in enumerate((0.0, ts * 0.5, ts)):
        p = m(t)
        sv += [p - side * 0.006, p + side * 0.006]
    sf = [(0, 1, 3, 2), (2, 3, 5, 4)]
    out.append((sv, sf, 0, 4))
    n = 7
    bv, bf = [], []
    for j in range(n):
        s = j / (n - 1)
        t = ts + (1 - ts) * s
        p = m(t)
        w = W * max(0.0, math.sin(math.pi * (0.12 + 0.88 * s))) ** 0.7
        bv += [p, p + side * w - up * (0.35 * w), p - side * w - up * (0.35 * w)]
    for j in range(n - 1):
        a, b = 3 * j, 3 * (j + 1)
        bf += [(a, a + 1, b + 1, b), (a, b, b + 2, a + 2)]
    out.append((bv, bf, 3, 0))


def flower_geometry(seed=53):
    """Clumps of broad tropical leaves at the edge (kind 3: the extra leaf green), a few red blooms on stems among them
    (petals: swatch 6, the extra red; orange centres)."""
    rs = np.random.RandomState(seed)
    out = []
    for i, a in enumerate(PLANTS):
        r = PROP_R + rs.uniform(0.0, 0.03)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0.0))
        c[2] = ground_height(c[0], c[1]) - 0.01
        nl = rs.randint(5, 8)
        for k in range(nl):
            az = a + rs.uniform(-1.25, 1.25)                     # outward and along the rim, never in over the deck
            L = rs.uniform(0.15, 0.24) * (0.85 if i % 2 else 1.0)
            _leaf(out, c + v3((rs.uniform(-0.02, 0.02), rs.uniform(-0.02, 0.02), 0.0)), az, L, L * rs.uniform(0.3, 0.38),
                  rs.uniform(0.6, 1.0), rs.uniform(-0.35, 0.35))
        for k in range(rs.randint(1, 3)):
            ang = a + rs.uniform(-0.9, 0.9)
            root = c + v3((math.cos(ang), math.sin(ang), 0.0)) * rs.uniform(0.02, 0.05)
            hgt = rs.uniform(0.13, 0.19)
            d = norm(v3((math.cos(ang) * 0.3, math.sin(ang) * 0.3, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, hgt, 0.012, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, 4))
            tilt = norm(v3((math.cos(a) * 0.4 + rs.uniform(-0.2, 0.2), math.sin(a) * 0.4 + rs.uniform(-0.2, 0.2), 1.0)))
            _bloom(out, root + d * hgt, tilt, 0.034, 6)
    return out


EXTRA_SWATCHES = [(0.16, 0.42, 0.1), (0.86, 0.12, 0.1)]      # kind 3: the tropical leaves; swatch 6: red blooms


def fields():
    return [("Ground", ground_field(), 0.008), ("Wall", wall_field(), 0.006), ("Deck", deck_field(), 0.0042),
            ("Kerb", kerb_field(), 0.004), ("Gabions", gabion_field(), 0.003), ("Fill", gabion_fill(), 0.005),
            ("Shot", shot_field(), 0.003), ("Props", props_field(), 0.0024), ("Water", water_field(), 0.003),
            ("Flag", flag_field(), 0.0025), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Deck", "Kerb", "Props", "Flag")
LOW_TARGETS = {"Ground": 900, "Wall": 2000, "Deck": 4000, "Kerb": 800, "Gabions": 1400, "Fill": 200, "Shot": 560,
               "Props": 1800, "Water": 40, "Flag": 400, "Pebbles": 260}
MAT_OVERRIDES = {"Deck": ("siege", {"name": "HQ_GunDeck", "wood": (0.5, 0.36, 0.22), "wood2": (0.36, 0.25, 0.15), "metal": "iron"}),
                 "Kerb": ("siege", {"name": "HQ_GunKerb", "wood": (0.44, 0.31, 0.19), "wood2": (0.32, 0.22, 0.13), "metal": "iron"}),
                 "Wall": ("limestone", {"name": "HQ_BastionStone"}),
                 "Gabions": ("basket", {}),
                 "Fill": ("ground", {"name": "HQ_GabionEarth"}),
                 "Shot": ("iron", {"name": "HQ_RoundShot"}),
                 "Props": ("siege", {"name": "HQ_GunProps", "wood": (0.5, 0.33, 0.19), "wood2": (0.36, 0.23, 0.13),
                                     "red": (0.55, 0.08, 0.08), "metal": "iron"}),
                 "Water": ("tar", {"name": "HQ_BucketWater"}),
                 "Flag": ("linen", {"name": "HQ_ArmyFlag", "base": (0.55, 0.08, 0.08), "border": (0.85, 0.62, 0.2),
                                    "stripe": (0.85, 0.62, 0.2)}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and FLOOR_R + KERB_W - 0.01 < r < WALL_IN + 0.005 and abs(c.z - ground_height(c.x, c.y)) < 0.035
