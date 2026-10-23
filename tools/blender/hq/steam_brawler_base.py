"""The Steam Brawler's base: a corner of a foundry's works yard where the stokers box. A round floor of granite setts
in rings inside a kerb, a riveted iron floor plate in the middle (checker tread, worn bright where he stands); behind him
a run of riveted steam pipe on two red-brick piers, a flanged joint and a red valve wheel on it; behind him on his left
a heavy punching bag of patched sackcloth hanging on a chain from a riveted iron gallows; behind him on his right a
cast-iron gas lamp (its glass its own glowing mesh); before him on his right a crate with a towel thrown over it (his
corner); before him on his left a coal scuttle heaped with coal, a shovel in it, lumps spilled on the setts. Round it
the yard's cinders, weeds at its rim (distance fields + grass as direct low-poly geometry).

Everything on the floor stands clear of the fists as the tower turns: nothing above the floor inside r = 0.78 (the hanging
fists of the Idle reach r = 0.73), and nothing at the rim higher than 0.95 above the floor (the blow passes over it)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
from sunpriest_base import ring_func
from crossbowman_base import _bloom

GROUND_R = 1.32
GROUND_TOP = 0.1
TOP_Z = 0.25                       # the plate's top = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
PLATE_R = 0.5
FLOOR_R = 1.02
SETT_TOP = TOP_Z - 0.012
CLEAR_R = 0.78
IRON, BRASS, COPPER, STEEL, RUBBER, LEATHER, ENAMEL, RED, BLACK_L, GLASS = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13


def _polar(deg, r, z=TOP_Z):
    return v3((r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)), z))


BAG_A = 36.0                       # the punching bag (degrees from his left, round behind)
BAG = _polar(BAG_A, 0.9)
POST = _polar(BAG_A, 1.1)
LAMP = _polar(150.0, 1.06)
CRATE = _polar(196.0, 0.93)
SCUTTLE = _polar(318.0, 0.92)
PIPE_Y = 0.97                      # the steam pipe's run behind him
PIPE_X = 0.6
PIPE_Z = TOP_Z + 0.17
PIPE_R = 0.05


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    """The yard's cinders round the floor (label 5: bare), a few weeds at its rim."""
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
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.004) * NOISE(P * F(23)), disp_amp=0.012), 0.0)
    fd.paint(Func(lambda P: np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(1.2) - F(0.07) * NOISE(P * F(4)), (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3)), 5)
    return fd


def _chip(P):
    return F(0.0026) * NOISE(P * F(11)) + F(0.0014) * NOISE(P * F(37))


def floor_field():
    """Granite setts in rings (label 0, some browner: 7), a kerb of long stones at the rim; soot and coal dust by the
    scuttle (5)."""
    fd = Field("Floor")
    hz = (SETT_TOP - GROUND_TOP + 0.08) / 2
    rings = [(PLATE_R - 0.02, 0.6, 22), (0.6, 0.7, 26), (0.7, 0.8, 30), (0.8, 0.9, 34)]
    for i, (r0, r1, n) in enumerate(rings):
        fd.add(ring_func(r0, r1, n, 901 + 7 * i, SETT_TOP, hz, jitter=1.2, chip=_chip), 0.0)
    fd.add(ring_func(0.9, FLOOR_R, 14, 941, SETT_TOP + 0.004, hz + 0.004, jitter=0.6, chip=_chip), 0.0)
    lo, hi = (-1.1, -1.1, GROUND_TOP - 0.2), (1.1, 1.1, TOP_Z + 0.03)
    def browner(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return F(0.25) - np.abs(np.sin(a * F(13) + r * F(37)) * np.sin(a * F(7) - r * F(19)))
    fd.paint(Func(browner, lo, hi), 7)
    fd.paint(Func(lambda P: np.sqrt((P[:, 0] - F(SCUTTLE[0])) ** 2 + (P[:, 1] - F(SCUTTLE[1])) ** 2) - F(0.24) - F(0.06) * NOISE(P * F(8)), lo, hi), 5)
    return fd


def plate_field():
    """The iron floor plate (steamworks label 0): checker tread, a rolled rim, a ring of rivets."""
    fd = Field("Plate")
    def tread(P):
        x, y = P[:, 0] * F(70), P[:, 1] * F(70)
        a = np.abs(np.sin(x + y)) * np.abs(np.sin(x - y))
        return -F(0.0016) * np.clip((a - F(0.55)) * F(4), 0, 1) * (P[:, 2] > F(TOP_Z - 0.01))
    fd.add(Cylinder(v3((0, 0, TOP_Z - 0.03)), PLATE_R, 0.06, rr=0.012, disp=tread, disp_amp=0.002), 0.0, IRON)
    fd.add(Torus(v3((0, 0, TOP_Z - 0.003)), PLATE_R - 0.012, 0.008), 0.004, IRON)
    for k in range(20):
        a = 2 * math.pi * k / 20
        fd.add(Sphere(v3((math.cos(a) * (PLATE_R - 0.04), math.sin(a) * (PLATE_R - 0.04), TOP_Z - 0.003)), 0.011), 0.002, IRON)
    return fd


# ---------------------------------------------------------------------------------------------- the steam pipe on brick piers
PIER_X = (-0.34, 0.34)


def bricks_field():
    """Two red-brick piers under the pipe (mats.mudbrick recoloured: courses of brick, pale mortar)."""
    fd = Field("Bricks")
    for x in PIER_X:
        c = v3((x, PIPE_Y, (TOP_Z - 0.04 + PIPE_Z - PIPE_R) / 2))
        h = (PIPE_Z - PIPE_R) - (TOP_Z - 0.04)
        fd.add(RoundBox(c, (0.1, 0.09, h / 2), 0.008, disp=_chip, disp_amp=0.004), 0.0)
        fd.add(RoundBox(c + v3((0, 0, h / 2 + 0.008)), (0.115, 0.1, 0.014), 0.006, disp=_chip, disp_amp=0.003), 0.004)
    return fd


def pipe_field():
    """Riveted iron steam pipe (0) dropping into the yard at each end, a flanged joint with bolts, iron saddles on the
    piers, a valve with a red wheel (11) and a brass gland (5)."""
    fd = Field("Pipe")
    a, b = v3((-PIPE_X, PIPE_Y, PIPE_Z)), v3((PIPE_X, PIPE_Y, PIPE_Z))
    fd.add(RoundCone(a, b, PIPE_R, PIPE_R), 0.0, IRON)
    for sx in (-1, 1):                                                          # elbows down into the yard
        e = v3((sx * PIPE_X, PIPE_Y, PIPE_Z))
        pts = [e, e + v3((sx * 0.07, 0.03, -0.01)), e + v3((sx * 0.12, 0.07, -0.08)), e + v3((sx * 0.13, 0.09, -0.3))]
        fd.add(Chain(pts, [PIPE_R] * 4, k=0.03), 0.01, IRON)
        fd.add(Cylinder(e + v3((sx * 0.02, 0, 0)), PIPE_R + 0.016, 0.022, rr=0.005, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, IRON)
    for x in (-0.15, 0.25):
        c = v3((x, PIPE_Y, PIPE_Z))
        fd.add(Cylinder(c, PIPE_R + 0.02, 0.026, rr=0.006, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, IRON)
        for k in range(6):
            t = 2 * math.pi * k / 6
            fd.add(Cylinder(c + v3((0, math.cos(t) * (PIPE_R + 0.011), math.sin(t) * (PIPE_R + 0.011))), 0.007, 0.04, rr=0.002,
                            R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, BRASS)
    for x in np.linspace(-0.5, 0.5, 11):                                         # rivets along its top
        fd.add(Sphere(v3((x, PIPE_Y, PIPE_Z + PIPE_R)), 0.0075), 0.002, IRON)
    for x in PIER_X:                                                             # saddles on the piers
        fd.add(Inter(Torus(v3((x, PIPE_Y, PIPE_Z)), PIPE_R + 0.004, 0.012, R=rot_from_axes(z_axis=(1, 0, 0))),
                     Plane(v3((x, PIPE_Y, PIPE_Z + 0.01)), (0, 0, 1)), 0.003), 0.003, IRON)
    # the valve: a body on the pipe, a brass gland, a stem, a red handwheel
    vc = v3((0.05, PIPE_Y, PIPE_Z))
    fd.add(Sphere(vc, PIPE_R + 0.018), 0.01, IRON)
    fd.add(Cylinder(vc + v3((0, 0, PIPE_R + 0.03)), 0.026, 0.04, rr=0.006), 0.006, BRASS)
    fd.add(RoundCone(vc + v3((0, 0, PIPE_R + 0.04)), vc + v3((0, 0, PIPE_R + 0.11)), 0.009, 0.009), 0.003, STEEL)
    wc = vc + v3((0, 0, PIPE_R + 0.11))
    fd.add(Torus(wc, 0.065, 0.011), 0.0, RED)
    for k in range(4):
        t = 2 * math.pi * k / 4 + 0.4
        fd.add(RoundCone(wc, wc + v3((math.cos(t) * 0.062, math.sin(t) * 0.062, 0)), 0.008, 0.007), 0.004, RED)
    fd.add(Sphere(wc, 0.016), 0.004, RED)
    return fd


# ---------------------------------------------------------------------------------------------- the punching bag and its gallows
GAL_H = 0.95                        # the gallows' arm, above the floor
BAG_TOP, BAG_BOT, BAG_RAD = 0.76, 0.24, 0.112


def gallows_field():
    """Riveted iron (0): a post on a bolted foot plate, an arm out over the bag with a brace, a hook and chain."""
    fd = Field("Gallows")
    up = v3((0, 0, 1))
    inn = norm(v3((BAG[0] - POST[0], BAG[1] - POST[1], 0)))
    top = POST + up * GAL_H
    fd.add(RoundBox(POST + up * (GAL_H / 2), (0.032, 0.032, GAL_H / 2), 0.01, R=rot_from_axes(z_axis=up, x_axis=inn)), 0.0, IRON)
    fd.add(RoundBox(POST + up * 0.012, (0.085, 0.085, 0.012), 0.006, R=rot_from_axes(z_axis=up, x_axis=inn)), 0.006, IRON)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = POST + inn * (sx * 0.06) + np.cross(up, inn) * (sy * 0.06) + up * 0.026
            fd.add(Cylinder(p, 0.011, 0.012, rr=0.003), 0.002, IRON)
    arm_end = v3((BAG[0], BAG[1], TOP_Z + GAL_H)) - inn * 0.06
    fd.add(RoundBox((top + arm_end) / 2 + up * 0.0, (float(np.linalg.norm(arm_end - top)) / 2 + 0.03, 0.024, 0.03), 0.008,
                    R=rot_from_axes(x_axis=inn, z_axis=up)), 0.006, IRON)
    fd.add(RoundCone(POST + up * (GAL_H - 0.3), top + inn * 0.16, 0.016, 0.016), 0.006, IRON)                       # brace
    for k in range(5):
        p = top + inn * (0.02 + 0.04 * k) + up * 0.03
        fd.add(Sphere(p, 0.007), 0.002, IRON)
    # the hook and the chain down to the bag
    h0 = v3((BAG[0], BAG[1], TOP_Z + GAL_H - 0.03))
    for k in range(4):
        c = h0 - up * (0.025 + 0.042 * k)
        R = rot_from_axes(z_axis=(1, 0, 0)) if k % 2 == 0 else rot_from_axes(z_axis=(0, 1, 0))
        fd.add(Torus(c, 0.016, 0.0055, R=R), 0.0, IRON)
    return fd


def bag_field():
    """A heavy punching bag of sackcloth (linen recipe: label 0), patched (5), lashed with rope (6) round its top and
    middle, a leather cap and ring at its top (6)."""
    fd = Field("Bag")
    c0, c1 = v3((BAG[0], BAG[1], TOP_Z + BAG_BOT)), v3((BAG[0], BAG[1], TOP_Z + BAG_TOP))
    weave = lambda P: F(0.0012) * (np.sin(P[:, 0] * F(300)) + np.sin(P[:, 2] * F(300))) + F(0.004) * NOISE(P * F(9))
    fd.add(RoundCone(c0 + v3((0, 0, BAG_RAD * 0.6)), c1 - v3((0, 0, BAG_RAD * 0.5)), BAG_RAD * 0.94, BAG_RAD, disp=weave, disp_amp=0.005), 0.0)
    for z in (0.12, 0.32, 0.47):
        fd.add(Torus(lerp(c0, c1, z / (BAG_TOP - BAG_BOT)), BAG_RAD * (0.97 if z > 0.2 else 0.95), 0.008), 0.004, 6)
    fd.add(Inter(Sphere(c1 - v3((0, 0, 0.03)), BAG_RAD * 0.92), Plane(c1 - v3((0, 0, 0.03)), (0, 0, -1)), 0.004), 0.01, 6)
    fd.add(Torus(c1 + v3((0, 0, 0.068)), 0.02, 0.006, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, 6)
    for c, r in (((0.05, -0.1, 0.42), (0.06, 0.03, 0.05)), ((-0.08, -0.06, 0.6), (0.045, 0.04, 0.04)), ((0.0, 0.11, 0.35), (0.05, 0.03, 0.06))):
        fd.paint(Ellipsoid(v3((BAG[0] + c[0], BAG[1] + c[1], TOP_Z + c[2])), r), 5)
    return fd


# ---------------------------------------------------------------------------------------------- the gas lamp
LAMP_H = 0.66                      # the lantern's foot above the floor


def lamp_field():
    """A cast-iron gas lamp standard (0): a stepped base, a fluted column, a ladder bar, the lantern's frame and domed
    cap with a finial, brass (5) on the burner."""
    fd = Field("Lamp")
    up = v3((0, 0, 1))
    b = LAMP
    fd.add(Cylinder(b + up * 0.04, 0.075, 0.08, rr=0.01), 0.0, IRON)
    fd.add(Cylinder(b + up * 0.11, 0.058, 0.06, rr=0.012), 0.006, IRON)
    flutes = lambda P: F(0.0018) * np.sin(np.arctan2(P[:, 1] - F(b[1]), P[:, 0] - F(b[0])) * F(12))
    fd.add(RoundCone(b + up * 0.13, b + up * (LAMP_H - 0.04), 0.036, 0.026, disp=flutes, disp_amp=0.002), 0.01, IRON)
    fd.add(Torus(b + up * (LAMP_H - 0.12), 0.03, 0.007), 0.003, IRON)
    tang = norm(v3((-b[1], b[0], 0)))
    fd.add(RoundCone(b + up * (LAMP_H - 0.1) - tang * 0.09, b + up * (LAMP_H - 0.1) + tang * 0.09, 0.009, 0.009), 0.004, IRON)
    for s in (-1, 1):
        fd.add(Sphere(b + up * (LAMP_H - 0.1) + tang * (s * 0.09), 0.013), 0.003, IRON)
    fd.add(Cylinder(b + up * (LAMP_H - 0.02), 0.05, 0.03, rr=0.008), 0.006, IRON)
    # the lantern: four corner posts flaring out, a domed cap, a finial
    L0, L1 = LAMP_H + 0.0, LAMP_H + 0.17
    for k in range(4):
        t = 2 * math.pi * k / 4 + math.pi / 4
        d = v3((math.cos(t), math.sin(t), 0))
        fd.add(RoundCone(b + up * L0 + d * 0.045, b + up * L1 + d * 0.075, 0.007, 0.007), 0.003, IRON)
    fd.add(Inter(Sphere(b + up * (L1 - 0.01), 0.088), Plane(b + up * (L1 - 0.012), (0, 0, -1)), 0.004), 0.004, IRON)
    fd.add(Torus(b + up * (L1 + 0.002), 0.082, 0.008), 0.004, IRON)
    fd.add(RoundCone(b + up * (L1 + 0.07), b + up * (L1 + 0.12), 0.012, 0.004), 0.008, IRON)
    fd.add(Cylinder(b + up * (L0 + 0.02), 0.022, 0.03, rr=0.006), 0.004, BRASS)
    return fd


def lamp_glow_field():
    """The lamp's glass with the gas mantle's light (its own glowing mesh)."""
    fd = Field("LampGlow")
    b, up = LAMP, v3((0, 0, 1))
    L0, L1 = LAMP_H + 0.0, LAMP_H + 0.17
    def lantern(P):
        q = P - b.astype(F)
        z = q[:, 2]
        k = np.clip((z - F(L0)) / F(L1 - L0), 0, 1)
        half = F(0.034) + F(0.026) * k
        rot = np.abs(q[:, 0] + q[:, 1]) / F(math.sqrt(2)), np.abs(q[:, 0] - q[:, 1]) / F(math.sqrt(2))
        d = np.maximum(np.maximum(rot[0], rot[1]) - half, np.maximum(F(L0 + 0.012) - z, z - F(L1 - 0.012)))
        return d
    fd.add(Func(lantern, b + v3((-0.12, -0.12, L0 - 0.02)), b + v3((0.12, 0.12, L1 + 0.02))), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- his corner: crate and towel
CRATE_HALF = (0.17, 0.12, 0.12)


def crate_frame():
    c = CRATE
    t = norm(v3((-c[1], c[0], 0)))                       # along the rim
    n = norm(v3((c[0], c[1], 0)))
    return v3((c[0], c[1], TOP_Z + CRATE_HALF[2])), t, n


def crate_field():
    """A closed crate of planks (siege recipe: label 0 grain along it, 10 its battens), iron corner straps (6)."""
    fd = Field("Crate")
    c, t, n = crate_frame()
    hx, hy, hz = CRATE_HALF
    R = np.stack([t, n, v3((0, 0, 1))], axis=1)
    fd.add(RoundBox(c, (hx, hy, hz), 0.008, R=R, disp=lambda P: F(0.001) * NOISE(P * F(40)), disp_amp=0.0015), 0.0)
    for sx in (-1, 1):
        fd.add(RoundBox(c + t * (sx * (hx + 0.006)), (0.008, hy + 0.004, hz + 0.002), 0.004, R=R), 0.003, 10)
        for sz in (-1, 1):
            fd.add(RoundBox(c + t * (sx * (hx - 0.01)) + v3((0, 0, sz * (hz - 0.01))), (0.03, hy + 0.007, 0.012), 0.003, R=R), 0.002, 6)
    for k in (-1, 0, 1):
        fd.sub(RoundBox(c + v3((0, 0, k * hz * 0.5)), (hx + 0.02, hy + 0.003, 0.0018), 0.001, R=R), 0.001)
    fd.sub(RoundBox(c + v3((0, 0, hz)), (hx - 0.03, 0.0018, 0.004), 0.001, R=R), 0.001)
    return fd


def towel_field():
    """A towel (off-white linen, a red stripe: 5) thrown over the crate's top and down its side."""
    fd = Field("Towel")
    c, t, n = crate_frame()
    hx, hy, hz = CRATE_HALF
    R = np.stack([t, n, v3((0, 0, 1))], axis=1)
    box = RoundBox(c, (hx, hy, hz), 0.008, R=R)
    fold = lambda P: F(0.004) * np.sin((P @ t.astype(F)) * F(60)) + F(0.002) * NOISE(P * F(20))
    def drape(P):
        q = P - c.astype(F)
        u, v, w = q @ t.astype(F), q @ n.astype(F), q[:, 2]
        over = np.minimum(F(hz - 0.012) - w, np.maximum(v + F(hy - 0.012), F(hz - 0.14) - w))   # its top, down its inner side
        region = np.maximum(np.abs(u + F(0.03)) - F(0.085), over)
        return np.maximum(region, np.abs(box(P) - F(0.009)) - F(0.006))
    fd.add(Func(drape, c - 0.25, c + 0.25, disp=fold, disp_amp=0.005), 0.0)
    fd.paint(Func(lambda P: np.abs((P - c.astype(F)) @ t.astype(F) + F(0.03)) - F(0.012), c - 0.25, c + 0.25), 5)
    return fd


# ---------------------------------------------------------------------------------------------- the coal scuttle
SC_R0, SC_R1, SC_H = 0.1, 0.13, 0.2


def scuttle_axes():
    c = SCUTTLE
    out = norm(v3((c[0], c[1], 0)))
    side = norm(np.cross(v3((0, 0, 1)), out))
    return c, out, side


def scuttle_field():
    """A black iron coal scuttle (0): a round bucket widening to a lipped spout turned toward him, a brass rim (5) and a
    bail handle, a foot ring."""
    fd = Field("Scuttle")
    c, out, side = scuttle_axes()
    up = v3((0, 0, 1))
    def bucket(P):
        q = P - c.astype(F)
        z = q[:, 2]
        k = np.clip(z / F(SC_H), 0, 1)
        # the spout: its rim rises and juts toward the middle (-out) at the front
        fwd = -(q @ out.astype(F))
        r = F(SC_R0) + F(SC_R1 - SC_R0) * k + F(0.05) * k * k * np.clip(fwd / F(SC_R1), 0, 1)
        rr = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        top = F(SC_H) + F(0.05) * np.clip(fwd / F(SC_R1), -0.3, 1)
        shell = np.abs(rr - r) - F(0.007)
        return np.maximum(np.maximum(shell, -z + F(0.015)), z - top)
    fd.add(Func(bucket, c - v3((0.25, 0.25, 0.02)), c + v3((0.25, 0.25, 0.32))), 0.0, IRON)
    fd.add(Cylinder(c + up * 0.02, SC_R0 + 0.004, 0.03, rr=0.006), 0.004, IRON)
    fd.add(Torus(c + up * 0.006, SC_R0 + 0.006, 0.008), 0.003, IRON)
    pts = []
    for k in range(13):
        a = 2 * math.pi * k / 12
        d = out * math.cos(a) + side * math.sin(a)
        fwd = -math.cos(a) * SC_R1
        rr = SC_R1 + 0.05 * max(0.0, min(1.0, fwd / SC_R1))
        z = SC_H + 0.05 * max(-0.3, min(1.0, fwd / SC_R1))
        pts.append(c + d * rr + up * z)
    fd.add(Chain(pts, [0.008] * len(pts), k=0.004), 0.004, BRASS)
    # the bail handle over the top, from side to side
    h = [c + side * (s * SC_R1) + up * (SC_H - 0.02) for s in (-1, 1)]
    bail = [h[0], c - side * 0.09 + up * (SC_H + 0.12), c + up * (SC_H + 0.17), c + side * 0.09 + up * (SC_H + 0.12), h[1]]
    fd.add(Chain(bail, [0.007] * 5, k=0.006), 0.004, IRON)
    fd.add(RoundCone(c + up * (SC_H + 0.165) - side * 0.04, c + up * (SC_H + 0.165) + side * 0.04, 0.014, 0.014), 0.004, BRASS)
    for s in (-1, 1):
        fd.add(Sphere(h[0 if s < 0 else 1], 0.014), 0.003, BRASS)
    # the shovel standing in the coal, its blade buried, the handle leaning out
    sh0 = c + out * 0.03 + up * 0.17
    sh1 = sh0 + norm(out * 0.5 + side * 0.25 + up * 1.0) * 0.27
    fd.add(RoundCone(sh0, sh1, 0.012, 0.011), 0.003, IRON)
    d = norm(sh1 - sh0)
    fd.add(RoundCone(sh1 - side * 0.04, sh1 + side * 0.04, 0.013, 0.013), 0.006, 9)
    fd.add(RoundBox(sh0 - d * 0.03, (0.06, 0.008, 0.07), 0.006, R=rot_from_axes(z_axis=d, x_axis=side)), 0.004, IRON)
    return fd


def coal_field():
    """Coal heaped in the scuttle and spilled on the setts by it (charcoal recipe)."""
    fd = Field("Coal")
    c, out, side = scuttle_axes()
    rs = np.random.RandomState(29)
    for k in range(16):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.0, SC_R1 * 0.82)
        p = c + v3((math.cos(a) * r, math.sin(a) * r, SC_H - 0.03 + 0.06 * (1 - r / SC_R1)))
        fd.add(Stone(p, rs.uniform(0.026, 0.04), seed=500 + k, squash=(1.0, 1.0, 0.75), noise=0.05), 0.004)
    fd.add(Cylinder(c + v3((0, 0, SC_H * 0.55)), SC_R1 - 0.012, SC_H * 0.8, rr=0.02), 0.01)
    for k in range(7):
        a = rs.uniform(-1.2, 1.2)
        d = -out * math.cos(a) + side * math.sin(a)
        p = c + d * rs.uniform(0.17, 0.3) + v3((0, 0, 0.012 - 0.0))
        p[2] = SETT_TOP + 0.014
        fd.add(Stone(p, rs.uniform(0.018, 0.03), seed=540 + k, squash=(1.0, 1.0, 0.7), noise=0.05), 0.0)
    return fd


def _blocked(c, pad=0.0):
    r = math.hypot(c[0], c[1])
    if r < FLOOR_R + 0.06 + pad:
        return True
    if abs(c[0]) < PIPE_X + 0.25 + pad and abs(c[1] - PIPE_Y) < 0.2 + pad:
        return True
    return False


def pebbles_field():
    """Cinders and stones in the yard."""
    fd = Field("Pebbles")
    rs = np.random.RandomState(87)
    n, tries = 0, 0
    while n < 14 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(1.06, 1.27)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, -0.04):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.022, 0.04), seed=880 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=61):
    """Sparse weeds in the cinders at the rim."""
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 18 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(FLOOR_R + 0.08, GROUND_R - 0.08)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.0):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.16 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(6, 11)
        big = 0.6 + 0.45 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.045)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            outv = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(outv * rs.uniform(0.2, 0.55) + v3((0, 0, 1)))
            L = rs.uniform(0.1, 0.2) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.028, 0.04), outv * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=67):
    """A few dandelions among the weeds (swatch 1: yellow)."""
    rs = np.random.RandomState(seed)
    out = []
    spots, tries = [], 0
    while len(spots) < 5 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(FLOOR_R + 0.1, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.03) or any(np.linalg.norm(c[:2] - s[:2]) < 0.25 for s in spots):
            continue
        spots.append(c)
    for c in spots:
        for k in range(rs.randint(1, 3)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.04)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.07, 0.12)
            d = norm(v3((math.cos(ang) * 0.3, math.sin(ang) * 0.3, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, 1))
            tilt = norm(v3((rs.uniform(-0.4, 0.4), rs.uniform(-0.4, 0.4), 1.0)))
            _bloom(out, root + d * h, tilt, 0.026, 1)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Floor", floor_field(), 0.0042), ("Plate", plate_field(), 0.003),
            ("Bricks", bricks_field(), 0.0035), ("Pipe", pipe_field(), 0.0026), ("Gallows", gallows_field(), 0.0026),
            ("Bag", bag_field(), 0.003), ("Lamp", lamp_field(), 0.0022), ("LampGlow", lamp_glow_field(), 0.003),
            ("Crate", crate_field(), 0.0028), ("Towel", towel_field(), 0.0026), ("Scuttle", scuttle_field(), 0.0024),
            ("Coal", coal_field(), 0.003), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Ground", "Floor", "Plate", "Pipe", "Gallows", "Bag", "Lamp", "Crate", "Towel", "Scuttle")
LOW_TARGETS = {"Ground": 1300, "Floor": 3400, "Plate": 900, "Bricks": 300, "Pipe": 1400, "Gallows": 700, "Bag": 700,
               "Lamp": 700, "LampGlow": 60, "Crate": 500, "Towel": 400, "Scuttle": 800, "Coal": 600, "Pebbles": 350}
WORKS = {"name": "HQ_YardIron"}
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_YardCinders", "dirt_label": 5}),
                 "Floor": ("flagstone", {"name": "HQ_YardSetts", "base": (0.4, 0.39, 0.38), "alt": (0.5, 0.45, 0.4)}),
                 "Plate": ("steamworks", WORKS),
                 "Bricks": ("mudbrick", {"name": "HQ_YardBrick", "base": (0.56, 0.22, 0.14), "mortar": (0.66, 0.62, 0.55),
                                         "course": 0.055, "brick": 0.17}),
                 "Pipe": ("steamworks", WORKS),
                 "Gallows": ("steamworks", WORKS),
                 "Bag": ("linen", {"name": "HQ_Sackcloth", "base": (0.64, 0.52, 0.34), "border": (0.48, 0.37, 0.22),
                                   "stripe": (0.36, 0.24, 0.13)}),
                 "Lamp": ("steamworks", dict(WORKS, name="HQ_YardLamp", iron=(0.09, 0.12, 0.1))),
                 "LampGlow": ("glow_ball", {"name": "HQ_GasLight", "col": (1.0, 0.86, 0.55)}),
                 "Crate": ("siege", {"name": "HQ_YardCrate", "wood": (0.58, 0.44, 0.28), "wood2": (0.44, 0.32, 0.2), "metal": "iron"}),
                 "Towel": ("linen", {"name": "HQ_CornerTowel", "base": (0.9, 0.88, 0.82), "border": (0.66, 0.12, 0.08)}),
                 "Scuttle": ("steamworks", WORKS),
                 "Coal": ("charcoal", {"name": "HQ_Coal"}),
                 "Pebbles": ("stone", {"name": "HQ_YardPebble", "scale": 0.3})}
GLOW = {"LampGlow": ((1.0, 0.84, 0.52), 1.1, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and FLOOR_R + 0.08 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.05))
