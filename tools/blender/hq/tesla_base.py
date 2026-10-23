"""Tesla Coil base: a little power-station corner in a smoky Victorian street. A round drum of red brick carries a
riveted iron floor plate with a chequered tread, a seam across it and an access hatch; nothing on the plate stands proud
of it but the rivets (the coil, the console and he sweep out to ~0.86 as the tower turns). Round
its foot cobbles set in grit, weeds in the gaps, a grassy verge at the edge. On the cobbles: behind him on his right a
bipolar dynamo (two tall field coils wound in copper over iron pole pieces, the armature between them, a spoked iron
flywheel), its copper bus bar running on porcelain insulators to a junction box on the plate's edge; behind him on his
left a tray of three Leyden jars (green glass coated in copper foil, brass rods and knobs, linked by a brass wire);
on his left a wooden reel of rubber cable; before him on his left a toolbox (a big spanner, a hammer). (Distance fields
+ direct low-poly geometry for the weeds and the dandelions.)"""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
import tesla as _t
from crossbowman_base import _bloom

GROUND_R = 1.32
GROUND_TOP = 0.1
PLINTH_R = 0.97                # the brick drum's face
PLATE_R = 0.958                # the floor plate (he, the coil and the console sweep out to ~0.86 of it)
TOP_Z = 0.2                    # the plate's top = where he stands
COBBLE_R = 1.24                # the cobbles, out to the grassy verge
STAND = v3((-_t.YAW_PIVOT[0], -_t.YAW_PIVOT[1], TOP_Z))
Z = v3((0.0, 0.0, 1.0))
PROP_R = 1.12                  # the props' ring, on the cobbles
DYN_A = math.radians(128.0)    # the dynamo: behind him, on his right (the camera's left)
JUNC_A = math.radians(104.0)   # its junction box on the plate's edge
JARS_A = math.radians(60.0)    # the Leyden jars: behind him on his left
REEL_A = math.radians(14.0)    # the cable reel: on his left
TOOL_A = math.radians(-62.0)   # the toolbox: before him, on his left
HATCH_C = v3((-0.34, 0.5, TOP_Z))


def ring_pt(a, r):
    return v3((math.cos(a) * r, math.sin(a) * r, 0.0))


def ring_frame(a):
    """At angle a on the ring: outward and along (counter-clockwise)."""
    return v3((math.cos(a), math.sin(a), 0.0)), v3((-math.sin(a), math.cos(a), 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    if r < PLINTH_R:
        return TOP_Z
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.025) * np.sin(a * 5 + 0.7) + F(0.018) * np.sin(a * 11 + 2.1) + F(0.012) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.03) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.08), 0), np.maximum(dz + F(0.08), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.08), dz + F(0.08)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.08)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


def brick_field():
    """The drum of red brick (mudbrick's courses drawn in the material)."""
    fd = Field("Brick")
    h = TOP_Z - 0.03 - (GROUND_TOP - 0.06)
    fd.add(Cylinder(v3((0, 0, GROUND_TOP - 0.06 + h / 2)), PLINTH_R, h, rr=0.012,
                    disp=lambda P: F(0.0015) * NOISE(P * F(30)), disp_amp=0.002), 0.0)
    return fd


def _tread(P):
    """The chequer plate's tread: raised lozenges, each cell's turned a quarter turn from its neighbours'."""
    cs = F(0.07)
    gx, gy = np.floor(P[:, 0] / cs), np.floor(P[:, 1] / cs)
    fx, fy = P[:, 0] / cs - gx - F(0.5), P[:, 1] / cs - gy - F(0.5)
    alt = np.mod(gx + gy, F(2)) < F(0.5)
    u, v = np.where(alt, fx + fy, fx - fy) * F(0.7071), np.where(alt, fx - fy, fx + fy) * F(0.7071)
    bump = np.clip(F(1) - (u / F(0.32)) ** 2 - (v / F(0.1)) ** 2, 0, 1)
    top = smoothstep(TOP_Z - 0.012, TOP_Z - 0.003, P[:, 2])
    return -F(0.0028) * np.sqrt(bump) * top


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def plate_field():
    """Riveted iron (label 0): the floor plate with its chequered tread, an angle-iron rim round its edge, a seam across
    it, a hatch with a sunk ring handle; rivets."""
    fd = Field("Plate")
    fd.add(Cylinder(v3((0, 0, TOP_Z - 0.016)), PLATE_R, 0.032, rr=0.008, disp=_tread, disp_amp=0.003), 0.0)
    fd.add(Inter(Shell(Cylinder(v3((0, 0, TOP_Z - 0.04)), PLATE_R + 0.004, 0.08, rr=0.006), 0.0, 0.008),
                 Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(PLATE_R + 0.02), F(PLATE_R - 0.012) - np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)),
                      (-1.1, -1.1, TOP_Z - 0.1), (1.1, 1.1, TOP_Z + 0.02)), 0.002), 0.003)
    for k in range(56):
        a = 2 * math.pi * (k + 0.5) / 56
        fd.add(Sphere(ring_pt(a, PLATE_R - 0.024) + Z * (TOP_Z - 0.003), 0.0105), 0.002)
    # a seam across the plate (front to back, under his right side), riveted
    sx = -0.42
    yl = math.sqrt(PLATE_R ** 2 - sx ** 2) - 0.03
    fd.sub(RoundBox(v3((sx, 0.0, TOP_Z)), (0.0035, yl, 0.006), 0.002), 0.002)
    for k in range(17):
        y = -yl + 2 * yl * (k + 0.5) / 17
        for e in (-1, 1):
            fd.add(Sphere(v3((sx + e * 0.022, y, TOP_Z - 0.003)), 0.0095), 0.002)
    # the hatch
    fd.sub(Inter(Shell(RoundBox(HATCH_C, (0.15, 0.13, 0.03), 0.02), 0.0, 0.006), Func(lambda P: TOP_Z - 0.008 - P[:, 2], HATCH_C - 0.3, HATCH_C + 0.3), 0.002), 0.002)
    fd.add(RoundBox(HATCH_C + v3((0, 0, -0.003)), (0.13, 0.11, 0.004), 0.004), 0.002)
    fd.sub(Torus(HATCH_C + v3((0.0, -0.07, 0.0)), 0.026, 0.007), 0.002)
    fd.add(Torus(HATCH_C + v3((0.0, -0.07, -0.002)), 0.026, 0.0045), 0.0)
    for e in (-1, 1):
        fd.add(RoundBox(HATCH_C + v3((e * 0.08, 0.125, 0.002)), (0.025, 0.012, 0.004), 0.003), 0.002)       # the hinges
    return fd


CELL = 0.075


def _hash2(cx, cy, k):
    return np.mod(np.sin(cx * F(127.1 + 17 * k) + cy * F(311.7 + 29 * k)) * F(43758.5453), F(1.0))


def _cobble_d(P):
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


def cobbles_field():
    """Rounded granite setts (label 0; a browner stone for some, 7) round the drum's foot, set in dark grit (6)."""
    fd = Field("Cobbles")
    def cobbles(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        r = np.sqrt(x * x + y * y)
        d1, st = _cobble_d(P)
        dome = F(0.018) * (F(1.0) - np.clip(d1 / F(0.6 * CELL), 0, 1) ** 2)
        g = F(GROUND_TOP) + F(0.03) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        top = g + F(0.004) + dome + st
        edge = F(COBBLE_R) + F(0.02) * np.sin(np.arctan2(y, x) * F(7)) + F(0.015) * NOISE(P * F(4))
        return np.maximum(np.maximum(np.maximum(r - edge, F(PLINTH_R - 0.01) - r), z - top), g - F(0.05) - z)
    R = COBBLE_R + 0.05
    fd.add(Func(cobbles, (-R, -R, GROUND_TOP - 0.08), (R, R, GROUND_TOP + 0.08), disp=lambda P: F(0.001) * NOISE(P * F(40)), disp_amp=0.0015), 0.0)
    def grit(P):
        d1, st = _cobble_d(P)
        return F(0.6 * CELL) * F(0.8) - d1
    fd.paint(Func(grit, (-R, -R, GROUND_TOP - 0.08), (R, R, GROUND_TOP + 0.08)), 6)
    rs = np.random.RandomState(41)
    for k in range(5):
        a = rs.uniform(0, 2 * math.pi)
        fd.paint(Sphere(ring_pt(a, rs.uniform(1.02, 1.2)) + Z * GROUND_TOP, rs.uniform(0.1, 0.16)), 7)
    return fd


# ---------------------------------------------------------------------------------------------- the dynamo
def dynamo_into(fd):
    """A bipolar dynamo on an iron bedplate (6): two tall field coils (copper winding 11 between brass rims 5) on iron
    pole pieces, a yoke over them, the armature (copper 0) between the poles on a shaft through two bearing pedestals, a
    spoked iron flywheel, brass terminals and a brass maker's plate; an oil can beside it."""
    out, along = ring_frame(DYN_A)
    c = ring_pt(DYN_A, PROP_R)
    g = ground_height(c[0], c[1]) - 0.008
    Rb = np.stack([along, out, Z], axis=1)
    fd.add(RoundBox(c + Z * (g + 0.022), (0.2, 0.12, 0.022), 0.008, R=Rb), 0.0, 6)
    for e in (-1, 1):
        for f in (-1, 1):
            fd.add(Sphere(c + along * (e * 0.175) + out * (f * 0.095) + Z * (g + 0.046), 0.011), 0.002, 6)
    zp = g + 0.044
    for e in (-1, 1):                                                            # pole pieces and field coils
        pc = c + out * (e * 0.072)
        fd.add(RoundBox(pc + Z * (zp + 0.05), (0.07, 0.04, 0.05), 0.012, R=Rb), 0.006, 6)
        fd.add(Cylinder(pc + Z * (zp + 0.235), 0.058, 0.3, rr=0.01, disp=lambda P: F(0.0009) * np.sin(P[:, 2] * F(2 * math.pi / 0.009)), disp_amp=0.001), 0.004, 11)
        for zz in (zp + 0.092, zp + 0.378):
            fd.add(Cylinder(pc + Z * zz, 0.068, 0.014, rr=0.004), 0.003, 5)
    fd.add(RoundBox(c + Z * (zp + 0.415), (0.07, 0.15, 0.03), 0.014, R=Rb), 0.006, 6)                 # the yoke
    ac = c + Z * (zp + 0.05)
    Ra = rot_from_axes(z_axis=along)
    fd.add(Cylinder(ac, 0.05, 0.12, rr=0.008, R=Ra, disp=lambda P: F(0.001) * np.sin(np.arctan2(P[:, 2] - F(ac[2]), (P - ac.astype(F)) @ out.astype(F)) * F(24)), disp_amp=0.0012), 0.003, 0)
    fd.add(Cylinder(ac - along * 0.085, 0.036, 0.04, rr=0.004, R=Ra), 0.002, 0)                        # the commutator
    fd.add(RoundCone(ac - along * 0.2, ac + along * 0.27, 0.014, 0.014), 0.002, 6)                     # the shaft
    for e in (-1, 1):                                                            # bearing pedestals
        bp = ac + along * (e * 0.17)
        fd.add(RoundCone(bp - Z * 0.05, bp, 0.03, 0.026), 0.008, 6)
        fd.add(Cylinder(bp, 0.03, 0.04, rr=0.006, R=Ra), 0.004, 5)
    for e in (-1, 1):                                                            # brushes
        fd.add(RoundBox(ac - along * 0.085 + Z * 0.05 + out * (e * 0.02), (0.008, 0.008, 0.02), 0.003, R=Rb), 0.002, 5)
    # the flywheel: rim, spokes, hub
    fc = ac + along * 0.24 + Z * 0.075
    Rf = rot_from_axes(z_axis=along)
    rim = lambda P: F(0.0006) * NOISE(P * F(40))
    fd.add(Inter(Shell(Cylinder(fc, 0.17, 0.04, rr=0.006, R=Rf), 0.0, 0.028), Func(lambda P: np.abs((P - fc.astype(F)) @ along.astype(F)) - F(0.022), fc - 0.3, fc + 0.3), 0.004), 0.0, 6)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        d = out * math.cos(a) + Z * math.sin(a)
        fd.add(RoundCone(fc + d * 0.03, fc + d * 0.152, 0.012, 0.009, disp=rim, disp_amp=0.001), 0.006, 6)
    fd.add(Cylinder(fc, 0.034, 0.06, rr=0.008, R=Rf), 0.006, 6)
    fd.add(RoundCone(fc - Z * 0.08 + along * 0.0, fc - Z * 0.075, 0.01, 0.01), 0.0, 6)
    # terminals and the maker's plate
    for e in (-1, 1):
        tp = c - along * 0.15 + out * (e * 0.05) + Z * (g + 0.044)
        fd.add(Cylinder(tp + Z * 0.016, 0.014, 0.032, rr=0.004), 0.002, 5)
        fd.add(Cylinder(tp + Z * 0.036, 0.01, 0.014, rr=0.003), 0.002, 5)
    pl = c + out * 0.1 + Z * (zp + 0.2)
    fd.add(RoundBox(pl, (0.05, 0.004, 0.025), 0.004, R=Rb), 0.002, 5)
    # an oil can
    oc = c - along * 0.26 + out * 0.07
    og = ground_height(oc[0], oc[1])
    fd.add(Cylinder(oc + Z * (og + 0.04), 0.04, 0.08, rr=0.012), 0.0, 14)
    fd.add(RoundCone(oc + Z * (og + 0.085), oc + Z * (og + 0.16) + along * 0.05, 0.012, 0.004), 0.004, 5)
    return c


def busbar_into(fd):
    """The dynamo's copper bus bar (two flat bars, 0) on porcelain insulators (8) along the cobbles to a junction box on
    the plate's edge (iron 6, brass terminals 5)."""
    out_d, along_d = ring_frame(DYN_A)
    start = ring_pt(DYN_A, PROP_R) - along_d * 0.15 + Z * 0.0
    jo, ja = ring_frame(JUNC_A)
    jc = ring_pt(JUNC_A, PLATE_R + 0.03)
    jg = ground_height(jc[0] * 1.06, jc[1] * 1.06)
    Rj = np.stack([ja, jo, Z], axis=1)
    fd.add(RoundBox(jc + Z * (jg + 0.06), (0.075, 0.05, 0.06), 0.01, R=Rj), 0.0, 6)
    fd.add(RoundBox(jc + Z * (jg + 0.124), (0.08, 0.055, 0.008), 0.004, R=Rj), 0.003, 6)
    for e in (-1, 1):
        fd.add(Sphere(jc + ja * (e * 0.06) + jo * 0.04 + Z * (jg + 0.124), 0.008), 0.002, 6)
    zb = 0.19
    angs = np.linspace(DYN_A - 0.13, JUNC_A + 0.07, 4)
    for e in (-1, 1):
        pts = []
        for a in angs:
            o, al = ring_frame(a)
            pts.append(ring_pt(a, PROP_R - 0.02 + e * 0.025) + Z * zb)
        pts = [start + jo * 0.0 + out_d * (e * 0.025) + Z * 0.075 + Z * (GROUND_TOP - 0.01)] + pts
        ends = jc + jo * (e * 0.025) + ja * 0.0 + Z * (jg + 0.09)
        pts.append(ends + jo * 0.06 + Z * 0.005)
        pts.append(ends)
        fd.add(Chain(pts, [0.009] * len(pts), k=0.004), 0.002, 0)
    for a in angs[1:-1]:
        p = ring_pt(a, PROP_R - 0.02)
        g = ground_height(p[0], p[1])
        for e in (-1, 1):
            q = ring_pt(a, PROP_R - 0.02 + e * 0.025)
            fd.add(Cylinder(q + Z * (g + 0.045), 0.009, 0.09, rr=0.003), 0.002, 8)
            for zz in (0.03, 0.06, 0.085):
                fd.add(Cylinder(q + Z * (g + zz), 0.017, 0.008, rr=0.003), 0.003, 8)
        fd.add(RoundBox(p + Z * (g + 0.008), (0.03, 0.06, 0.008), 0.004, R=rot_from_axes(y_axis=ring_frame(a)[0], z_axis=Z)), 0.003, 6)


def jars_into(fd):
    """Three Leyden jars in a wooden tray (7): green glass (12) coated in copper foil (0) up two thirds of the way, wooden
    stoppers (7), brass rods and ball knobs (5) linked by a brass wire."""
    out, along = ring_frame(JARS_A)
    c = ring_pt(JARS_A, PROP_R)
    g = ground_height(c[0], c[1]) - 0.006
    Rt = np.stack([along, out, Z], axis=1)
    fd.add(RoundBox(c + Z * (g + 0.018), (0.2, 0.075, 0.018), 0.006, R=Rt), 0.0, 7)
    fd.sub(RoundBox(c + Z * (g + 0.038), (0.185, 0.06, 0.014), 0.004, R=Rt), 0.003)
    knobs = []
    for k, e in enumerate((-1, 0, 1)):
        jc = c + along * (e * 0.125) + out * (0.008 * e)
        h = 0.2 + 0.02 * (k % 2)
        fd.add(Cylinder(jc + Z * (g + 0.03 + h / 2), 0.047, h, rr=0.014), 0.0, 12)
        fd.add(Cylinder(jc + Z * (g + 0.03 + h * 0.33), 0.0495, h * 0.62, rr=0.01), 0.002, 0)
        fd.add(Cylinder(jc + Z * (g + 0.03 + h + 0.006), 0.04, 0.022, rr=0.006), 0.003, 7)
        top = jc + Z * (g + 0.03 + h + 0.1)
        fd.add(RoundCone(jc + Z * (g + 0.03 + h), top, 0.005, 0.005), 0.002, 5)
        fd.add(Sphere(top, 0.019), 0.003, 5)
        knobs.append(top)
    fd.add(Chain([knobs[0], (knobs[0] + knobs[1]) / 2 - Z * 0.012, knobs[1], (knobs[1] + knobs[2]) / 2 - Z * 0.012, knobs[2]],
                 [0.004] * 5, k=0.002), 0.002, 5)


def reel_into(fd):
    """A wooden cable reel (7) standing on its rim, black rubber cable (9) wound on it, its end trailing."""
    out, along = ring_frame(REEL_A)
    c = ring_pt(REEL_A, PROP_R + 0.02)
    g = ground_height(c[0], c[1])
    rc = c + Z * (g + 0.15)
    Rr = rot_from_axes(z_axis=along)
    for e in (-1, 1):
        fd.add(Cylinder(rc + along * (e * 0.075), 0.15, 0.022, rr=0.006, R=Rr), 0.0, 7)
    fd.add(Cylinder(rc, 0.105, 0.13, rr=0.015, R=Rr, disp=lambda P: F(0.004) * np.abs(np.sin(((P - rc.astype(F)) @ along.astype(F)) * F(2 * math.pi / 0.032))), disp_amp=0.004), 0.004, 9)
    fd.add(Cylinder(rc, 0.03, 0.2, rr=0.006, R=Rr), 0.003, 6)
    s = rc + out * -0.0 + Z * -0.0
    st = rc + Z * 0.1 - along * 0.03
    pts = [st, rc + Z * 0.06 - out * 0.12 - along * 0.02, c - out * 0.22 + Z * (g + 0.02) + along * 0.04, c - out * 0.3 + along * 0.16 + Z * (g + 0.018)]
    fd.add(Chain(pts, [0.014] * len(pts), k=0.01), 0.004, 9)


def toolbox_into(fd):
    """A wooden toolbox (7, a red-painted band 14) with a dowel handle; a big iron spanner (6) and a hammer (6, a wooden
    handle 7) in it."""
    out, along = ring_frame(TOOL_A)
    c = ring_pt(TOOL_A, PROP_R)
    g = ground_height(c[0], c[1]) - 0.006
    Rt = np.stack([along, out, Z], axis=1)
    fd.add(RoundBox(c + Z * (g + 0.055), (0.16, 0.085, 0.055), 0.008, R=Rt), 0.0, 7)
    fd.sub(RoundBox(c + Z * (g + 0.1), (0.146, 0.071, 0.06), 0.004, R=Rt), 0.003)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(g + 0.08)) - F(0.012), c - 0.3, c + 0.3), 14)
    for e in (-1, 1):
        fd.add(RoundBox(c + along * (e * 0.15) + Z * (g + 0.12), (0.008, 0.07, 0.07), 0.006, R=Rt), 0.003, 7)
    fd.add(RoundCone(c - along * 0.15 + Z * (g + 0.17), c + along * 0.15 + Z * (g + 0.17), 0.011, 0.011), 0.003, 7)
    fd.add(RoundBox(c + Z * (g + 0.07), (0.14, 0.006, 0.06), 0.003, R=Rt), 0.002, 7)
    # the spanner, leaning out of it
    s0 = c + along * -0.08 + out * 0.04 + Z * (g + 0.06)
    s1 = s0 + norm(along * 0.5 + out * 0.3 + Z * 0.8) * 0.26
    fd.add(RoundCone(s0, s1, 0.012, 0.012), 0.002, 6)
    for p, d in ((s1, norm(s1 - s0)), (s0, -norm(s1 - s0))):
        jaw = p + d * 0.02
        fd.add(Torus(jaw, 0.026, 0.01, R=rot_from_axes(z_axis=out)), 0.004, 6)
        fd.sub(RoundBox(jaw + d * 0.02, (0.012, 0.03, 0.03), 0.003, R=rot_from_axes(y_axis=d, z_axis=out)), 0.002)
    # the hammer
    h0 = c + along * 0.06 - out * 0.03 + Z * (g + 0.05)
    h1 = h0 + norm(-along * 0.3 + out * -0.2 + Z * 1.0) * 0.2
    fd.add(RoundCone(h0, h1, 0.011, 0.012), 0.002, 7)
    fd.add(RoundBox(h1, (0.022, 0.06, 0.022), 0.006, R=rot_from_axes(y_axis=along, z_axis=norm(h1 - h0))), 0.003, 6)


def apparatus_field():
    fd = Field("Apparatus")
    dynamo_into(fd)
    busbar_into(fd)
    jars_into(fd)
    reel_into(fd)
    toolbox_into(fd)
    return fd


def _clear(p, pad=0.0):
    for a, rad in ((DYN_A, 0.3), (JUNC_A, 0.12), (JARS_A, 0.24), (REEL_A, 0.22), (TOOL_A, 0.2)):
        if np.linalg.norm(p[:2] - ring_pt(a, PROP_R)[:2]) < rad + pad:
            return False
    for a in np.linspace(DYN_A - 0.13, JUNC_A + 0.07, 6):
        if np.linalg.norm(p[:2] - ring_pt(a, PROP_R - 0.02)[:2]) < 0.07 + pad:
            return False
    return True


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(53)
    n, tries = 0, 0
    while n < 10 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(COBBLE_R - 0.02, GROUND_R - 0.04)
        p = ring_pt(a, r)
        if not _clear(p):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.02, 0.034), seed=360 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=61):
    """Weeds in the cobbles' gaps and a grassy verge at the edge."""
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 26 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.04, GROUND_R - 0.04) if len(tufts) < 12 else rs.uniform(COBBLE_R - 0.02, GROUND_R - 0.03)
        c = ring_pt(a, r)
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.12 for t in tufts) or not _clear(c, 0.02):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(5, 9)
        big = 0.6 + 0.4 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.035)
            root[2] = ground_height(root[0], root[1]) - 0.005
            o = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(o * rs.uniform(0.2, 0.5) + Z)
            v, f, uv = _b.blade_mesh(root, d, rs.uniform(0.08, 0.15) * big, rs.uniform(0.03, 0.042), o * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)),
                                     segs=4, twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=67):
    """Dandelions among the weeds (swatch 1: yellow)."""
    rs = np.random.RandomState(seed)
    spots, tries = [], 0
    while len(spots) < 5 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.06, GROUND_R - 0.06)
        c = ring_pt(a, r)
        if any(np.linalg.norm(c[:2] - s[:2]) < 0.3 for s in spots) or not _clear(c, 0.05):
            continue
        spots.append(c)
    out = []
    for c in spots:
        for k in range(rs.randint(1, 3)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.04)
            root[2] = ground_height(root[0], root[1]) - 0.005
            h = rs.uniform(0.07, 0.11)
            d = norm(v3((math.cos(ang) * 0.3, math.sin(ang) * 0.3, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, 1))
            _bloom(out, root + d * h, norm(v3((rs.uniform(-0.3, 0.3), rs.uniform(-0.3, 0.3), 1.0))), 0.026, 1)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Brick", brick_field(), 0.005), ("Plate", plate_field(), 0.0034),
            ("Cobbles", cobbles_field(), 0.0042), ("Apparatus", apparatus_field(), 0.0026), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Cobbles", "Apparatus")
LOW_TARGETS = {"Ground": 1000, "Brick": 900, "Plate": 3000, "Cobbles": 2600, "Apparatus": 5200, "Pebbles": 240}
MAT_OVERRIDES = {"Brick": ("mudbrick", {"name": "HQ_RedBrick", "base": (0.56, 0.22, 0.14), "mortar": (0.6, 0.56, 0.5),
                                        "glaze": (0.56, 0.22, 0.14), "course": 0.07, "brick": 0.22}),
                 "Plate": ("iron", {"name": "HQ_FloorPlate", "col": {"base": (0.26, 0.26, 0.28), "hi": (0.58, 0.6, 0.64),
                                                                     "dark": (0.08, 0.08, 0.09), "rust": (0.46, 0.22, 0.1)}}),
                 "Cobbles": ("flagstone", {"name": "HQ_Setts", "base": (0.42, 0.41, 0.4), "alt": (0.5, 0.44, 0.38)}),
                 "Apparatus": ("electric", {"name": "HQ_StationApparatus"}),
                 "Pebbles": ("stone", {"name": "HQ_StationPebble", "scale": 0.3})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and COBBLE_R - 0.02 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
