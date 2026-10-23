"""Rifleman base: a corner of a brick-works yard by the railway, on a round plinth of red brick capped with a course of
blue engineering bricks, rising from cinder ground. Where he stands: granite setts. Behind him a narrow-gauge track
crosses the yard on its ballast (two iron rails spiked to creosoted sleepers), running off the plinth's edge both ways;
on his left a low breastwork of sandbags; on his right, at the edge, a brick gate pier with a gas lamp on it (a
cast-iron post, a glazed lantern that glows); before him on his right an open crate of cartridges (brass rounds in
rows, its lid propped against it, a broad arrow stencilled on its side); weeds in the joints; round the plinth's foot
cinders, lumps of coal, grass and ragwort (distance fields + direct low-poly geometry for the grass and the flowers).

Nothing on the plinth rises above the setts within r = 0.8 but the rails (low), and nothing reaches the barrel's line
on the aim (the lamp's top is well under it, wherever he turns)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
from sunpriest_base import ring_func
from crossbowman_base import _bloom

GROUND_R = 1.32
GROUND_TOP = 0.08
PLINTH_R = 1.06                    # the plinth's brick face
TOP_Z = 0.22                       # the setts' top = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
COPE_R0, COPE_R1 = 0.94, PLINTH_R + 0.03     # the coping's ring of blue bricks
COPE_TOP = TOP_Z + 0.035
TRACK_Y = (0.48, 0.74)             # the rails' middles (a narrow gauge: a works tramway)
BED_Y = (0.37, 0.86)               # the ballast bed
SLEEPERS_X = (-0.72, -0.36, 0.0, 0.36, 0.72)
RAIL_TOP = TOP_Z + 0.06
PIER_C = v3((-0.78, 0.06, 0.0))     # the gate pier and its lamp (on his right, at the edge)
PIER_W, PIER_H = 0.12, 0.5         # half width, height above the setts
CRATE_C = v3((-0.5, -0.5, TOP_Z)) # the crate of cartridges (before him on his right)
CRATE_A = math.radians(40.0)
CRATE_HALF = (0.17, 0.12, 0.09)
BAGS_A = (-62.0, 14.0)             # the sandbags' arc on his left (degrees from +x), at r = BAGS_R
BAGS_R = 0.84


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def ground_height(x, y):
    r = math.hypot(x, y)
    if r < PLINTH_R - 0.02:
        return TOP_Z
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def _chip(P):
    return F(0.004) * NOISE(P * F(9)) + F(0.002) * NOISE(P * F(31))


def _fine(P):
    return F(0.0014) * NOISE(P * F(30)) + F(0.0008) * NOISE(P * F(90))


def _hash(a, b):
    v = np.sin(a.astype(np.float64) * 12.9898 + b.astype(np.float64) * 78.233) * 43758.5453
    return (v - np.floor(v)).astype(F)


# ---------------------------------------------------------------------------------------------- ground
def ground_field():
    """Cinder ground round the plinth's foot (the ground material: grass where it faces up, earth on its sides)."""
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


# ---------------------------------------------------------------------------------------------- the brick plinth
def _course_joints(P, course=0.07, brick=0.2):
    """Displacement: mortar joints of stretcher bond round the drum (sunk a little)."""
    z = P[:, 2]
    a = np.arctan2(P[:, 1], P[:, 0])
    row = np.floor(z / F(course))
    dz = np.abs(z - (row + F(0.5)) * F(course)) - F(course / 2)
    run = a * F(PLINTH_R) + np.mod(row, 2) * F(brick / 2)
    dsv = np.abs(np.mod(run, F(brick)) - F(brick / 2)) - F(brick / 2)
    j = np.minimum(np.abs(dz), np.abs(dsv))
    return F(0.0035) * smoothstep(0.006, 0.0, j)


def brick_field():
    """The plinth's drum of red brick (label 0; sooty low down, 6), its coping of blue engineering bricks (5)."""
    fd = Field("Brick")
    def drum(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(r - F(PLINTH_R), np.maximum(P[:, 2] - F(TOP_Z), F(-0.05) - P[:, 2]))
    fd.add(Func(drum, (-1.15, -1.15, -0.1), (1.15, 1.15, TOP_Z + 0.02), disp=lambda P: _course_joints(P) + F(0.0015) * NOISE(P * F(20)), disp_amp=0.006), 0.0)
    # (broken where the track crosses it)
    mid, half = (BED_Y[0] + BED_Y[1]) / 2, (BED_Y[1] - BED_Y[0]) / 2
    ring = ring_func(COPE_R0, COPE_R1, 30, 811, COPE_TOP, 0.03, jitter=0.6, chip=_chip)
    fd.add(Inter(ring, Func(lambda P: F(half + 0.012) - np.abs(P[:, 1] - F(mid)), ring.lo, ring.hi), 0.004), 0.006, 5)
    fd.paint(Func(lambda P: (P[:, 2] - F(0.09)) + F(0.04) * NOISE(P * F(4)), (-1.2, -1.2, -0.12), (1.2, 1.2, 0.3)), 6)
    return fd


# ---------------------------------------------------------------------------------------------- setts and the track bed
SETT_X, SETT_Y = 0.13, 0.09        # the setts' pitch (along x, rows along y)
SETT_H = 0.035


def _setts_sd(P):
    """Granite setts in staggered rows (one rounded block per cell, each a little high or low), up to the coping and
    the track bed."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    row = np.floor(y / F(SETT_Y))
    xs = x + np.mod(row, 2) * F(SETT_X / 2)
    col = np.floor(xs / F(SETT_X))
    lx = xs - (col + F(0.5)) * F(SETT_X)
    ly = y - (row + F(0.5)) * F(SETT_Y)
    hsh = _hash(col, row)
    top = F(TOP_Z) + (hsh - F(0.5)) * F(0.007)
    lz = z - (top - F(SETT_H / 2))
    rr = F(0.014)
    q = np.stack([np.abs(lx) - F(SETT_X / 2 - 0.006) + rr, np.abs(ly) - F(SETT_Y / 2 - 0.006) + rr, np.abs(lz) - F(SETT_H / 2) + rr], 1)
    d = np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - rr
    d = d + F(0.004) * (lx ** 2 + ly ** 2) / F(0.004)          # (domed a little: worn by cartwheels)
    r = np.sqrt(x * x + y * y)
    keep = np.maximum(r - F(COPE_R0 + 0.004), y - F(BED_Y[0] - 0.01))
    return np.maximum(d, keep)


def _sett_alt(P):
    """< 0 on about a third of the setts (a browner granite, label 7)."""
    x, y = P[:, 0], P[:, 1]
    row = np.floor(y / F(SETT_Y))
    col = np.floor((x + np.mod(row, 2) * F(SETT_X / 2)) / F(SETT_X))
    return np.where(_hash(col + F(7), row) > F(0.66), F(-1.0), F(1.0))


def setts_field():
    """Granite setts (label 0; a browner stone for some, 7) on a hidden bed of mortar."""
    fd = Field("Setts")
    lo, hi = (-1.0, -1.0, TOP_Z - 0.07), (1.0, 0.4, TOP_Z + 0.02)
    fd.add(Func(_setts_sd, lo, hi, disp=_fine, disp_amp=0.002), 0.0)
    def bed(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.maximum(r - F(COPE_R0 + 0.01), P[:, 2] - F(TOP_Z - 0.03)), np.maximum(F(TOP_Z - 0.08) - P[:, 2], P[:, 1] - F(BED_Y[0])))
    fd.add(Func(bed, lo, hi), 0.0, 7)
    fd.paint(Func(_sett_alt, lo, hi), 7)
    return fd


def ballast_field():
    """The track's bed of ballast: broken stone heaped between the sleepers (the stone material, fine)."""
    fd = Field("Ballast")
    def bed(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.sqrt(x * x + y * y)
        mid = F((BED_Y[0] + BED_Y[1]) / 2)
        half = F((BED_Y[1] - BED_Y[0]) / 2)
        crown = F(TOP_Z - 0.006) - F(0.02) * smoothstep(half - 0.08, half, np.abs(y - mid))
        lumps = F(0.006) * (np.abs(NOISE(P * F(38))) - F(0.3)) + F(0.003) * NOISE(P * F(90))
        d = np.maximum(z - crown - lumps, F(TOP_Z - 0.08) - z)
        return np.maximum(np.maximum(d, np.abs(y - mid) - half), r - F(PLINTH_R))
    fd.add(Func(bed, (-1.0, BED_Y[0] - 0.03, TOP_Z - 0.1), (1.0, BED_Y[1] + 0.03, TOP_Z + 0.03)), 0.0)
    fd.add(Func(lambda P: np.maximum(np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(PLINTH_R - 0.002), F(-0.05) - P[:, 2]),
                                     np.maximum(P[:, 2] - F(TOP_Z - 0.03), np.abs(P[:, 1] - F((BED_Y[0] + BED_Y[1]) / 2)) - F((BED_Y[1] - BED_Y[0]) / 2))),
                (-1.1, BED_Y[0] - 0.02, -0.1), (1.1, BED_Y[1] + 0.02, TOP_Z)), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the track
def _clip(P, pad=0.0):
    return np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(PLINTH_R + pad)


def rail_profile_sd(P, y0):
    """A flat-bottomed rail along x at y0 (head, web, foot), its top at RAIL_TOP."""
    y, z = P[:, 1] - F(y0), P[:, 2] - F(RAIL_TOP)
    def box(cy, cz, hy, hz, rr=0.003):
        qy = np.abs(y - F(cy)) - F(hy) + F(rr)
        qz = np.abs(z - F(cz)) - F(hz) + F(rr)
        return np.sqrt(np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qy, qz), 0) - F(rr)
    head = box(0.0, -0.01, 0.0125, 0.01, 0.004)
    web = box(0.0, -0.03, 0.0045, 0.014, 0.002)
    foot = box(0.0, -0.051, 0.022, 0.005, 0.002)
    return np.minimum(np.minimum(head, web), foot)


def track_field():
    """Timber (the `timber` material): creosoted sleepers (label 5, grain along y: 10) on the ballast, iron (6) rails
    spiked to them with chairs, a fishplate bolted across a joint in the nearer rail."""
    fd = Field("Track")
    for k, x0 in enumerate(SLEEPERS_X):
        c = v3((x0 + 0.01 * math.sin(k * 2.1), (BED_Y[0] + BED_Y[1]) / 2, RAIL_TOP - 0.074))
        R = euler(0, 0, 0.03 * math.sin(k * 1.3))
        sl = RoundBox(c, (0.06, (BED_Y[1] - BED_Y[0]) / 2 - 0.02, 0.02), 0.008, R=R,
                      disp=lambda P: F(0.0025) * NOISE(P * np.array([60, 6, 60], F)) + F(0.001) * NOISE(P * F(80)), disp_amp=0.003)
        fd.add(Inter(sl, Func(lambda P: _clip(P), sl.lo, sl.hi), 0.004), 0.0, 5)
        for y0 in TRACK_Y:
            if math.hypot(x0, y0) > PLINTH_R - 0.06:
                continue
            fd.add(RoundBox(v3((x0, y0, RAIL_TOP - 0.05)), (0.05, 0.034, 0.008), 0.004), 0.003, 6)      # the chair
            for sy in (-1, 1):
                fd.add(Sphere(v3((x0 + 0.03, y0 + sy * 0.026, RAIL_TOP - 0.042)), 0.008), 0.002, 6)   # spikes' heads
    lo, hi = (-1.0, TRACK_Y[0] - 0.05, RAIL_TOP - 0.08), (1.0, TRACK_Y[1] + 0.05, RAIL_TOP + 0.02)
    for y0 in TRACK_Y:
        fd.add(Func(lambda P, y0=y0: np.maximum(rail_profile_sd(P, y0), _clip(P, 0.015)), lo, hi,
                    disp=lambda P: F(0.0008) * NOISE(P * F(60)), disp_amp=0.001), 0.003, 6)
    # a fishplate over a joint in the nearer rail
    fx = -0.18
    for sy in (-1, 1):
        fd.add(RoundBox(v3((fx, TRACK_Y[0] + sy * 0.011, RAIL_TOP - 0.03)), (0.07, 0.004, 0.012), 0.002), 0.002, 6)
        for bx in (-0.045, -0.015, 0.015, 0.045):
            fd.add(Sphere(v3((fx + bx, TRACK_Y[0] + sy * 0.016, RAIL_TOP - 0.03)), 0.0055), 0.0015, 6)
    fd.sub(RoundBox(v3((fx, TRACK_Y[0], RAIL_TOP - 0.01)), (0.003, 0.02, 0.012), 0.001), 0.001)
    return fd


# ---------------------------------------------------------------------------------------------- the gate pier and lamp
def pier_field():
    """A gate pier of red brick (label 0) with a cap of blue bricks (5), sooty at its foot (6)."""
    fd = Field("Pier")
    c = PIER_C
    top = TOP_Z + PIER_H
    def joints(P):
        z = P[:, 2]
        row = np.floor(z / F(0.07))
        dz = np.abs(z - (row + F(0.5)) * F(0.07)) - F(0.035)
        run = P[:, 0] + P[:, 1] + np.mod(row, 2) * F(0.1)
        dsv = np.abs(np.mod(run, F(0.2)) - F(0.1)) - F(0.1)
        j = np.minimum(np.abs(dz), np.abs(dsv))
        return F(0.003) * smoothstep(0.006, 0.0, j)
    fd.add(RoundBox(v3((c[0], c[1], (TOP_Z - 0.05 + top) / 2)), (PIER_W, PIER_W, (top - TOP_Z + 0.05) / 2), 0.006,
                    disp=lambda P: joints(P) + F(0.0012) * NOISE(P * F(25)), disp_amp=0.004), 0.0)
    fd.add(RoundBox(v3((c[0], c[1], top + 0.025)), (PIER_W + 0.025, PIER_W + 0.025, 0.025), 0.01, disp=_chip, disp_amp=0.004), 0.004, 5)
    fd.add(RoundBox(v3((c[0], c[1], top + 0.06)), (PIER_W - 0.01, PIER_W - 0.01, 0.015), 0.012, disp=_chip, disp_amp=0.003), 0.008, 5)
    fd.paint(Func(lambda P: (P[:, 2] - F(TOP_Z + 0.12)) + F(0.05) * NOISE(P * F(5)), c - v3((0.3, 0.3, 0.2)), c + v3((0.3, 0.3, 1.0))), 6)
    return fd


LAMP_BASE_Z = TOP_Z + PIER_H + 0.075
LANTERN_Z = LAMP_BASE_Z + 0.3             # the lantern's foot
LANT_W0, LANT_W1, LANT_H = 0.06, 0.088, 0.2


def lamp_field():
    """The gas lamp's ironwork (timber's iron, label 6): a fluted cast-iron post with a collar and a ladder bar, the
    lantern's frame (a tapering square, glazed: the glass is its own glowing part), its roof and finial; brass (7) gas
    tap."""
    fd = Field("Lamp")
    c = v3((PIER_C[0], PIER_C[1], 0.0))
    b = c + v3((0, 0, LAMP_BASE_Z))
    t = c + v3((0, 0, LANTERN_Z))
    flutes = lambda P: F(0.0012) * np.sin(np.arctan2(P[:, 1] - F(c[1]), P[:, 0] - F(c[0])) * F(12))
    fd.add(Cylinder(b + v3((0, 0, 0.02)), 0.05, 0.04, rr=0.01), 0.0, 6)
    fd.add(RoundCone(b + v3((0, 0, 0.03)), t - v3((0, 0, 0.03)), 0.028, 0.02, disp=flutes, disp_amp=0.0015), 0.012, 6)
    fd.add(Torus(b + v3((0, 0, 0.12)), 0.028, 0.007), 0.004, 6)
    fd.add(Cylinder(t - v3((0, 0, 0.02)), 0.034, 0.03, rr=0.008), 0.006, 6)
    # the ladder bar under the lantern
    fd.add(RoundCone(t - v3((0.085, 0, 0.04)), t + v3((0.085, 0, -0.04)), 0.007, 0.007), 0.004, 6)
    for sx in (-1, 1):
        fd.add(Sphere(t + v3((sx * 0.088, 0, -0.04)), 0.011), 0.003, 6)
    fd.add(Cylinder(t - v3((0, 0.032, 0.008)), 0.01, 0.024, rr=0.003, R=rot_from_axes(z_axis=(0, 1, 0))), 0.003, 7)   # the gas tap
    # the lantern's frame: four corner bars on a tapering square, a base plate
    fd.add(RoundBox(t + v3((0, 0, 0.006)), (LANT_W0 + 0.01, LANT_W0 + 0.01, 0.008), 0.004, R=euler(0, 0, math.pi / 4)), 0.003, 6)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = v3((math.cos(a), math.sin(a), 0.0))
        p0 = t + v3((0, 0, 0.012)) + d * LANT_W0 * math.sqrt(2) * 0.72
        p1 = t + v3((0, 0, LANT_H)) + d * LANT_W1 * math.sqrt(2) * 0.72
        fd.add(RoundCone(p0, p1, 0.0055, 0.0055), 0.002, 6)
    top = t + v3((0, 0, LANT_H))
    fd.add(RoundBox(top + v3((0, 0, 0.004)), (LANT_W1 + 0.012, LANT_W1 + 0.012, 0.007), 0.004, R=euler(0, 0, math.pi / 4)), 0.003, 6)
    fd.add(RoundCone(top + v3((0, 0, 0.008)), top + v3((0, 0, 0.07)), LANT_W1 * 1.25, 0.012), 0.006, 6)    # the roof
    fd.add(Sphere(top + v3((0, 0, 0.078)), 0.016), 0.004, 6)
    fd.add(RoundCone(top + v3((0, 0, 0.09)), top + v3((0, 0, 0.125)), 0.008, 0.002), 0.003, 6)
    return fd


def glass_field():
    """The lantern's panes round the gas mantle (its own glowing mesh)."""
    fd = Field("Glass")
    t = v3((PIER_C[0], PIER_C[1], LANTERN_Z))
    def lant(P):
        q = P - t.astype(F)
        z = q[:, 2]
        k = np.clip((z - F(0.012)) / F(LANT_H - 0.012), 0, 1)
        w = F(LANT_W0) + F(LANT_W1 - LANT_W0) * k
        c, s = F(math.cos(math.pi / 4)), F(math.sin(math.pi / 4))
        u = q[:, 0] * c + q[:, 1] * s
        v = -q[:, 0] * s + q[:, 1] * c
        side = np.maximum(np.abs(u), np.abs(v)) - w * F(0.92)
        return np.maximum(side, np.maximum(F(0.012) - z, z - F(LANT_H - 0.004)))
    fd.add(Func(lant, t - 0.15, t + 0.25), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the sandbags
def bag_spots():
    """(centre, along, half sizes) of each sandbag: a bottom course of four along the arc, three on top over the joints."""
    out = []
    a0, a1 = math.radians(BAGS_A[0]), math.radians(BAGS_A[1])
    for course, n, z in ((0, 4, TOP_Z + 0.055), (1, 3, TOP_Z + 0.15)):
        for i in range(n):
            u = (i + 0.5 + (0.5 if course else 0.0)) / 4.0
            a = a0 + (a1 - a0) * u + 0.02 * math.sin(i * 3.1 + course)
            r = BAGS_R + (0.012 if course else 0.0) + 0.01 * math.cos(i * 1.7)
            c = v3((r * math.cos(a), r * math.sin(a), z))
            along = v3((-math.sin(a), math.cos(a), 0.0))
            out.append((c, along, (0.14, 0.095, 0.058), 0.06 * math.sin(i * 2.3 + course * 1.1)))
    return out


def sandbags_field():
    """Hessian sacks of sand (the wool material, coarse: label 0), plump in the middle, their tied ends pinched, laid in
    two courses."""
    fd = Field("Sandbags")
    for k, (c, along, (hl, hw, hh), tw) in enumerate(bag_spots()):
        outv = norm(np.cross(along, v3((0, 0, 1))))
        R = np.stack([along, -outv, v3((0, 0, 1))], axis=1) @ euler(0, tw, 0)
        def bag(P, c=c, R=R, hl=hl, hw=hw, hh=hh):
            q = (P - c.astype(F)) @ R.astype(F)
            s = np.clip(np.abs(q[:, 0]) / F(hl), 0, 1)
            pinch = F(1) - F(0.45) * s ** 4
            e = np.sqrt((q[:, 0] / F(hl)) ** 2 + (q[:, 1] / (F(hw) * pinch)) ** 2 + (q[:, 2] / (F(hh) * pinch)) ** 2)
            return (e - F(1)) * F(min(hw, hh))
        lo, hi = c - 0.2, c + 0.2
        wr = lambda P: F(0.003) * NOISE(P * F(16)) + F(0.0008) * NOISE(P * F(70))
        fd.add(Func(bag, lo, hi, disp=wr, disp_amp=0.004), 0.012)
        for s in (-1, 1):                                                   # the tied ends
            e = c + along * s * (hl - 0.004)
            fd.add(Ellipsoid(e, (0.016, 0.018, 0.018), R=R), 0.008, 5)
    return fd


# ---------------------------------------------------------------------------------------------- the crate of cartridges
def _crate_R():
    return euler(0, 0, CRATE_A)


def crate_field():
    """A deal crate (timber, label 0, grain along x: 10) with iron corner straps (6), open: its lid propped against its
    side, a broad arrow stencilled in black (5) on its front; inside, rows of brass cartridges (7)."""
    fd = Field("Crate")
    R = _crate_R()
    hx, hy, hz = CRATE_HALF
    c = CRATE_C + R @ v3((0, 0, hz))
    planks = lambda P: F(0.0018) * np.abs(np.sin(((P - c.astype(F)) @ R[:, 2].astype(F)) * F(math.pi / 0.045)))
    fd.add(RoundBox(c, (hx, hy, hz), 0.008, R=R, disp=lambda P: planks(P) + F(0.0008) * NOISE(P * F(40)), disp_amp=0.003), 0.0, 10)
    fd.sub(RoundBox(c + R @ v3((0, 0, 0.03)), (hx - 0.016, hy - 0.016, hz), 0.004, R=R), 0.003)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(RoundBox(c + R @ v3((sx * (hx - 0.002), sy * (hy - 0.002), 0.0)), (0.012, 0.012, hz + 0.002), 0.004, R=R), 0.002, 6)
    # the lid, leaning against its far side (behind it, away from him)
    lid_c = c + R @ v3((0.0, hy + 0.035, 0.0)) + v3((0, 0, 0.02))
    lid_R = R @ euler(0.32, 0, 0)
    fd.add(RoundBox(lid_c, (hx + 0.005, 0.009, hz + 0.02), 0.005, R=lid_R,
                    disp=lambda P: F(0.0008) * NOISE(P * F(40)), disp_amp=0.001), 0.003, 10)
    # the broad arrow on its front (toward the robots' side, -y of the crate)
    def arrow(P):
        q = (P - c.astype(F)) @ R.astype(F)
        x, z = q[:, 0], q[:, 2] + F(0.01)
        stem = np.maximum(np.abs(x) - F(0.007), np.abs(z + F(0.012)) - F(0.035))
        legs = np.minimum(np.maximum(np.abs(x - (z - F(0.02)) * F(-0.9)) - F(0.008), np.abs(z - F(0.0)) - F(0.025)),
                          np.maximum(np.abs(x + (z - F(0.02)) * F(-0.9)) - F(0.008), np.abs(z - F(0.0)) - F(0.025)))
        return np.maximum(np.minimum(stem, legs), F(-0.02) - q[:, 1] - F(hy - 0.03))
    fd.paint(Func(arrow, c - 0.3, c + 0.3), 5)
    # rows of cartridges standing in it, bullets up
    for i in range(7):
        for j in range(4):
            p = c + R @ v3((-hx + 0.03 + i * 0.041, -hy + 0.03 + j * 0.042, hz - 0.045 + 0.004 * math.sin(i * 1.7 + j)))
            fd.add(RoundCone(p, p + v3((0, 0, 0.032)), 0.0095, 0.0095), 0.0, 7)
            fd.add(RoundCone(p + v3((0, 0, 0.032)), p + v3((0, 0, 0.05)), 0.0085, 0.0035), 0.002, 7)
    return fd


# ---------------------------------------------------------------------------------------------- weeds, coal, pebbles
WEEDS = [(v3((0.3, -1.13, 0.0)), 11), (v3((-1.12, -0.38, 0.0)), 13), (v3((1.12, 0.42, 0.0)), 17), (v3((-0.28, -0.85, 0.0)), 19)]


def _leaf(fd, root, d, L, w, label=0):
    side = norm(np.cross(d, v3((0, 0, 1))))
    up = norm(np.cross(side, d))
    pts = [root + d * (L * u) + v3((0, 0, 0.25 * L * math.sin(math.pi * u * 0.9) - 0.12 * L * u * u)) for u in np.linspace(0, 1, 5)]
    ws = [w * (0.35 + 0.65 * math.sin(math.pi * min(1.0, u * 1.15))) + 0.002 for u in np.linspace(0, 1, 5)]
    fd.add(Lock(pts, ws, [0.003] * 5, [up] * 5, k=0.004), 0.003, label)


def weeds_field():
    """Weeds: dock-leaved rosettes at the plinth's foot and in the joints (leaf green, label 0)."""
    fd = Field("Weeds")
    for c, seed in WEEDS:
        rs = np.random.RandomState(seed)
        g = ground_height(c[0], c[1])
        base = c + v3((0, 0, g - 0.01))
        for k in range(rs.randint(6, 9)):
            a = 2 * math.pi * k / 7 + rs.uniform(-0.3, 0.3)
            d = norm(v3((math.cos(a), math.sin(a), rs.uniform(0.5, 1.1))))
            _leaf(fd, base, d, rs.uniform(0.11, 0.17), rs.uniform(0.026, 0.036))
    return fd


def _blocked(c, pad=0.0):
    r = math.hypot(c[0], c[1])
    if r < PLINTH_R + 0.06 + pad:
        return True
    for p, _s in WEEDS:
        if math.hypot(c[0] - p[0], c[1] - p[1]) < 0.12 + pad:
            return True
    return False


def coal_field():
    """Lumps of coal dropped among the cinders (the charcoal material)."""
    fd = Field("Coal")
    rs = np.random.RandomState(83)
    n, tries = 0, 0
    while n < 11 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.05, GROUND_R - 0.06)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, -0.03):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.022, 0.04), seed=880 + n, squash=(1, 1, 0.7), noise=0.08), 0.0)
        n += 1
    return fd


def grass_geometry(seed=89):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 24 and tries < 8000:
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
        big = 0.7 + 0.5 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.05)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            outv = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(outv * rs.uniform(0.15, 0.45) + v3((0, 0, 1)))
            L = rs.uniform(0.11, 0.22) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.042), outv * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=97):
    """Ragwort: a few stems of small yellow flowers (swatch 1) in the grass and the cinders."""
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
            h = rs.uniform(0.12, 0.2)
            d = norm(v3((math.cos(ang) * 0.25, math.sin(ang) * 0.25, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, 1))
            for j in range(3):
                tilt = norm(v3((rs.uniform(-0.5, 0.5), rs.uniform(-0.5, 0.5), 1.0)))
                top = root + d * h + v3((rs.uniform(-0.025, 0.025), rs.uniform(-0.025, 0.025), rs.uniform(-0.02, 0.01)))
                _bloom(out, top, tilt, 0.02, 1)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Brick", brick_field(), 0.0045), ("Setts", setts_field(), 0.0032),
            ("Ballast", ballast_field(), 0.0035), ("Track", track_field(), 0.0024), ("Pier", pier_field(), 0.003),
            ("Lamp", lamp_field(), 0.0018), ("Glass", glass_field(), 0.002), ("Sandbags", sandbags_field(), 0.003),
            ("Crate", crate_field(), 0.002), ("Weeds", weeds_field(), 0.0024), ("Coal", coal_field(), 0.004)]


REGION_PARTS = ("Brick", "Setts", "Track", "Pier", "Lamp", "Sandbags", "Crate")
LOW_TARGETS = {"Ground": 1500, "Brick": 3000, "Setts": 3600, "Ballast": 1200, "Track": 1900, "Pier": 700, "Lamp": 900,
               "Glass": 60, "Sandbags": 1300, "Crate": 1800, "Weeds": 900, "Coal": 380}
_TIMBER = {"wood": (0.62, 0.48, 0.32), "wood2": (0.46, 0.34, 0.21), "worn": (0.82, 0.72, 0.56), "stain": (0.36, 0.2, 0.1)}
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_CinderGround"}),
                 "Brick": ("red_brick", {"name": "HQ_PlinthBrick", "radial": PLINTH_R}),
                 "Setts": ("flagstone", {"name": "HQ_Setts", "base": (0.44, 0.44, 0.46), "alt": (0.52, 0.46, 0.4)}),
                 "Ballast": ("stone", {"name": "HQ_Ballast", "scale": 0.25}),
                 "Track": ("timber", dict(_TIMBER, name="HQ_Track")),
                 "Pier": ("red_brick", {"name": "HQ_PierBrick"}),
                 "Lamp": ("timber", dict(_TIMBER, name="HQ_Track")),
                 "Glass": ("glow_ball", {"name": "HQ_LampGlow", "col": (1.0, 0.82, 0.46), "strength": 2.0}),
                 "Sandbags": ("wool", {"name": "HQ_Hessian", "base": (0.6, 0.5, 0.33), "border": (0.42, 0.34, 0.22), "stripe": (0.3, 0.24, 0.16)}),
                 "Crate": ("timber", dict(_TIMBER, name="HQ_Track")),
                 "Weeds": ("leafy", {"name": "HQ_Weeds", "leaf": (0.22, 0.4, 0.12), "vein": (0.42, 0.58, 0.2), "twig": (0.38, 0.4, 0.16)}),
                 "Coal": ("charcoal", {"name": "HQ_Coal"})}
GLOW = {"Glass": ((1.0, 0.8, 0.42), 1.1, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = PLINTH_R + 0.04 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
    return n.z > 0.55 and on_ground and not _blocked((c.x, c.y), -0.1)
