"""Nova's stand: a rooftop netrunner's nest. A round dark deck plate of diamond-tread steel (panel seams across it, a
chamfered edge, black-and-yellow hazard stripes round its side), the hero ring a dashed violet light strip set into it
(its own glowing mesh). Round her on the plate's outer ring: behind her on her right a small server stack (a gunmetal
frame, black server units with violet status lights and a little screen, vents, cables out of its back); behind her on
her left a black hard case with her spare deck open on it (a keyboard slab, the lid's screen glowing violet) and a can
of energy drink beside it; on her left a little satellite dish on a tripod, tilted up at the sky (a violet light on its
feed); on her right a rooftop cooling unit (a fan under a round grille); behind her a stretch of the roof's parapet (hazard
stripes, a little antenna mast with a violet light on top); cable spaghetti snaking over the plate between
them all."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Inter, Shell, lerp

PLATE_R = 1.18
TOP_Z = 0.16                      # the plate's top = where she stands
BOT_Z = -0.04
STAND = v3((0.0, 0.0, TOP_Z))
RING_R = 0.72                     # the hero ring
RING_W = 0.016                    # its half width
N_DASH = 16
Z = v3((0.0, 0.0, 1.0))


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def _placed(angle_deg, r):
    """A prop's place round her: (centre on the plate, its inward direction (toward her), its tangent)."""
    a = math.radians(angle_deg)
    c = v3((math.cos(a) * r, math.sin(a) * r, TOP_Z))
    inward = -norm(v3((c[0], c[1], 0.0)))
    tang = norm(np.cross(Z, inward))
    return c, inward, tang


RACK = _placed(142.0, 0.98)       # (+x her left, +y behind her)
CRATE = _placed(42.0, 0.97)
DISH = _placed(-22.0, 0.96)
COOLER = _placed(204.0, 0.97)
DISH_R = 0.21
WALL_A = (66.0, 116.0)            # a stretch of the roof's parapet behind her
WALL_R = (1.04, 1.16)
WALL_H = 0.2
MAST_A = 100.0


def _frame(pl, twist=0.0):
    c, inw, tg = pl
    return c, np.stack([tg, inw, Z], 1) @ euler(0, 0, twist)


# ---------------------------------------------------------------------------------------------- the plate
def plate_field():
    """modern_kit: the deck plate (label 0, dark graphite, smooth) with a diamond tread on its top, panel seams, a
    groove for the ring; hazard stripes (8: yellow; the rest dark) round its side."""
    fd = Field("Plate")
    def slab(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        d_r = r - F(PLATE_R)
        d_z = np.maximum(P[:, 2] - F(TOP_Z), F(BOT_Z) - P[:, 2])
        q = np.stack([np.maximum(d_r + F(0.024), 0), np.maximum(d_z + F(0.024), 0)], 1)
        return np.minimum(np.maximum(d_r + F(0.024), d_z + F(0.024)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.024)
    def tread(P):
        top = smoothstep(TOP_Z - 0.012, TOP_Z - 0.002, P[:, 2])
        u = (P[:, 0] + P[:, 1]) * F(0.7071)
        v = (P[:, 0] - P[:, 1]) * F(0.7071)
        k = F(2 * math.pi / 0.05)
        cell = np.floor(u / F(0.05)) + np.floor(v / F(0.05))
        a = np.where(np.mod(cell, 2) == 0, u, v)
        b = np.where(np.mod(cell, 2) == 0, v, u)
        bump = np.abs(np.sin(a * k * F(0.5))) ** 6 * np.abs(np.sin(b * k * F(0.5) + F(1.57))) ** 2
        seams = np.minimum(np.minimum(np.abs(P[:, 0] - F(0.42)), np.abs(P[:, 0] + F(0.42))), np.minimum(np.abs(P[:, 1] - F(0.42)), np.abs(P[:, 1] + F(0.42))))
        seam = F(0.004) * (F(1) - smoothstep(0.0, 0.006, seams))
        return (-F(0.0022) * bump + seam) * top + F(0.0006) * NOISE(P * F(30))
    fd.add(Func(slab, (-1.25, -1.25, BOT_Z - 0.05), (1.25, 1.25, TOP_Z + 0.05), disp=tread, disp_amp=0.005), 0.0)
    # the ring's groove
    def groove(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.abs(r - F(RING_R)) - F(RING_W + 0.006), np.abs(P[:, 2] - F(TOP_Z)) - F(0.012))
    fd.sub(Func(groove, (-0.9, -0.9, TOP_Z - 0.03), (0.9, 0.9, TOP_Z + 0.03)), 0.003)
    # hazard stripes round the side
    def hazard(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        s = np.sin((a * F(PLATE_R) + P[:, 2]) * F(2 * math.pi / 0.11))
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        band = np.maximum(np.maximum(F(BOT_Z + 0.02) - P[:, 2], P[:, 2] - F(TOP_Z - 0.03)), F(PLATE_R - 0.03) - r)
        return np.maximum(band, -s * F(0.02))
    fd.paint(Func(hazard, (-1.3, -1.3, BOT_Z - 0.02), (1.3, 1.3, TOP_Z)), 8)
    # bolts round the rim
    for i in range(24):
        a = 2 * math.pi * (i + 0.5) / 24
        c = v3((math.cos(a) * (PLATE_R - 0.05), math.sin(a) * (PLATE_R - 0.05), TOP_Z - 0.002))
        fd.add(Cylinder(c, 0.011, 0.008, rr=0.003), 0.002, 9)
    return fd


def ring_field():
    """The hero ring: sixteen dashes of violet light in the plate's groove (they glow)."""
    fd = Field("Ring")
    gap = math.radians(5.0)
    for i in range(N_DASH):
        a0 = 2 * math.pi * i / N_DASH + gap / 2
        a1 = 2 * math.pi * (i + 1) / N_DASH - gap / 2
        mid = (a0 + a1) / 2
        half = (a1 - a0) / 2
        def dash(P, mid=mid, half=half):
            r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
            a = np.arctan2(P[:, 1], P[:, 0]) - F(mid)
            a = np.arctan2(np.sin(a), np.cos(a))
            da = (np.abs(a) - F(half)) * F(RING_R)
            q = np.stack([np.maximum(np.abs(r - F(RING_R)) - F(RING_W - 0.004), 0), np.maximum(np.abs(P[:, 2] - F(TOP_Z - 0.006)) - F(0.002), 0),
                          np.maximum(da + F(0.004), 0)], 1)
            return np.sqrt((q ** 2).sum(1)) - F(0.004)
        c = v3((math.cos(mid) * RING_R, math.sin(mid) * RING_R, TOP_Z))
        fd.add(Func(dash, c - 0.2, c + 0.2), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the server stack
RACK_H = 0.6
RACK_HALF = (0.19, 0.15)          # along the tangent, inward


def rack_field():
    """modern_kit: a gunmetal (9) frame, black (5) server units with vents, a black base; violet (6) painted labels."""
    fd = Field("Rack")
    c, R = _frame(RACK, -0.15)
    w, d = RACK_HALF
    b = c + Z * (RACK_H / 2 + 0.02)
    fd.add(RoundBox(b, (w, d, RACK_H / 2), 0.012, R=R), 0.0, 5)
    front = R[:, 1]
    for sx in (-1, 1):                                                       # the frame's posts
        for sy in (-1, 1):
            fd.add(RoundBox(b + R[:, 0] * (sx * (w - 0.004)) + front * (sy * (d - 0.004)), (0.016, 0.016, RACK_H / 2 + 0.012), 0.004, R=R), 0.003, 9)
    fd.add(RoundBox(b + Z * (RACK_H / 2 + 0.006), (w + 0.008, d + 0.008, 0.012), 0.005, R=R), 0.004, 9)      # its top
    fd.add(RoundBox(c + Z * 0.012, (w + 0.01, d + 0.01, 0.014), 0.005, R=R), 0.004, 5)                      # its plinth
    # the units: grooves between them on the front, vents, handles
    n = 5
    for k in range(n):
        z = 0.04 + (RACK_H - 0.04) * (k + 0.5) / n
        uc = c + Z * z + front * d
        fd.sub(RoundBox(uc + Z * ((RACK_H - 0.04) / n * 0.5), (w - 0.02, 0.006, 0.003), 0.002, R=R), 0.002)
        for j in range(6):
            fd.sub(RoundBox(uc + R[:, 0] * (-0.02 + 0.026 * j) - Z * 0.012, (0.008, 0.006, 0.016), 0.003, R=R), 0.002)
        for sx in (-1, 1):
            fd.add(RoundBox(uc + R[:, 0] * (sx * (w - 0.035)) + front * 0.008, (0.006, 0.008, 0.028), 0.003, R=R), 0.002, 9)
        fd.paint(RoundBox(uc + R[:, 0] * -0.13 + front * 0.002 + Z * 0.016, (0.02, 0.006, 0.005), 0.002, R=R), 7)
    return fd


def rack_lights():
    """(centre, R, half) of the rack's glowing bits: a status bar on each unit and a little screen on the top one."""
    c, R = _frame(RACK, -0.15)
    w, d = RACK_HALF
    front = R[:, 1]
    out = []
    n = 5
    for k in range(n):
        z = 0.04 + (RACK_H - 0.04) * (k + 0.5) / n
        uc = c + Z * z + front * (d + 0.003)
        out.append((uc + R[:, 0] * -0.1 - Z * 0.01, (0.035, 0.004, 0.005)))
    top = c + Z * (0.04 + (RACK_H - 0.04) * (n - 0.5) / n) + front * (d + 0.003)
    out.append((top + R[:, 0] * 0.1 + Z * 0.004, (0.045, 0.004, 0.026)))
    return R, out


# ---------------------------------------------------------------------------------------------- the case, the deck, the can
CASE_HALF = (0.22, 0.15, 0.115)


def deck_frame():
    """(base centre on the case's lid, R) of the open deck."""
    c, R = _frame(CRATE, 0.2)
    top = c + Z * (2 * CASE_HALF[2] + 0.004)
    return top, R


DECK_TILT = math.radians(108.0)        # the lid opened this far from closed


def props_field():
    """modern_kit: the hard case (black polymer, 5; gunmetal (9) latches and corners), the deck (gunmetal case, black
    keys, the lid), the energy drink can (green 13, a white (7) band, violet (6) claw marks), the satellite dish (white,
    7, on a gunmetal tripod, its feed arm and horn), the cooling unit (graphite (0) with a black fan under a gunmetal
    grille)."""
    fd = Field("Props")
    # the hard case
    c, R = _frame(CRATE, 0.2)
    hx, hy, hz = CASE_HALF
    b = c + Z * hz
    fd.add(RoundBox(b, (hx, hy, hz), 0.026, R=R, disp=lambda P: F(0.0006) * NOISE(P * F(60)), disp_amp=0.001), 0.0, 5)
    fd.sub(RoundBox(b + Z * (hz * 0.45), (hx + 0.01, hy + 0.01, 0.003), 0.002, R=R), 0.002)                # the lid's seam
    for k in (-1, 1):
        fd.add(RoundBox(b + R[:, 0] * (k * 0.12) + R[:, 1] * (hy + 0.004) + Z * (hz * 0.42), (0.024, 0.008, 0.026), 0.005, R=R), 0.003, 9)
        fd.add(RoundBox(b + R[:, 0] * (k * (hx - 0.01)) + Z * (hz * 0.42), (0.012, hy - 0.03, 0.016), 0.005, R=R), 0.003, 9)
    for k in range(3):                                                       # ribs on its lid
        fd.add(RoundBox(b + Z * hz + R[:, 0] * (-0.14 + 0.14 * k) - R[:, 1] * 0.0, (0.008, hy - 0.02, 0.005), 0.003, R=R), 0.003, 5)
    # the deck: its slab, keys, the lid
    top, Rd = deck_frame()
    slab_c = top + Z * 0.014 + Rd[:, 0] * -0.04
    fd.add(RoundBox(slab_c, (0.15, 0.1, 0.014), 0.007, R=Rd), 0.004, 9)
    for i in range(10):
        for j in range(4):
            kc = slab_c + Rd[:, 0] * (-0.12 + 0.026 * i) + Rd[:, 1] * (0.06 - 0.026 * j - 0.01) + Z * 0.014
            fd.add(RoundBox(kc, (0.0105, 0.0105, 0.004), 0.003, R=Rd), 0.0015, 5)
    hinge = slab_c - Rd[:, 1] * 0.1 + Z * 0.01
    ld = Rd @ euler(-(math.pi - DECK_TILT), 0, 0)          # the lid's frame: its local y up the lid from the hinge
    lup = norm(Rd[:, 2] * math.sin(DECK_TILT) + Rd[:, 1] * -math.cos(DECK_TILT))
    lid_n = norm(np.cross(Rd[:, 0], lup))
    if lid_n @ Rd[:, 1] < 0:
        lid_n = -lid_n
    Rl = np.stack([Rd[:, 0], lup, lid_n], 1)
    fd.add(RoundBox(hinge + lup * 0.1, (0.15, 0.1, 0.008), 0.006, R=Rl), 0.004, 9)
    fd.sub(RoundBox(hinge + lup * 0.1 + lid_n * 0.008, (0.135, 0.085, 0.004), 0.003, R=Rl), 0.002)
    fd.add(Cylinder(hinge, 0.009, 0.28, rr=0.003, R=rot_from_axes(z_axis=Rd[:, 0])), 0.003, 5)
    # the energy drink can, on the case's lid beside the deck
    cc = top + Rd[:, 0] * 0.165 + Rd[:, 1] * 0.06
    fd.add(Cylinder(cc + Z * 0.062, 0.032, 0.124, rr=0.008), 0.0, 13)
    fd.add(Cylinder(cc + Z * 0.122, 0.026, 0.01, rr=0.003), 0.002, 10)
    fd.paint(Cylinder(cc + Z * 0.03, 0.04, 0.016), 7)
    for k in range(3):                                                       # claw marks
        a = -0.4 + 0.25 * k
        dd = v3((math.cos(a), math.sin(a), 0.0))
        dd = Rd @ dd
        p = cc + dd * 0.032 + Z * 0.075
        fd.paint(RoundCone(p - Z * 0.03 + dd * 0.0, p + Z * 0.025, 0.004, 0.0025), 6)
    # the satellite dish on its tripod, tilted up at the sky, out away from her
    c, inw, tg = DISH
    mount = c + Z * 0.3
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        foot = c + v3((math.cos(a), math.sin(a), 0.0)) * 0.13 + Z * 0.004
        fd.add(RoundCone(foot, mount - Z * 0.02, 0.009, 0.007), 0.004, 9)
        fd.add(Sphere(foot, 0.014), 0.004, 12)
    fd.add(Cylinder(mount, 0.026, 0.05, rr=0.008), 0.006, 9)
    ax = norm(-inw * 0.55 + Z * 0.85)                                         # the dish's axis
    dc = mount + ax * 0.06
    Rdish = rot_from_axes(z_axis=ax)
    def dish(P, dc=dc, ax=ax):
        q = P - dc.astype(F)
        h = q @ ax.astype(F)
        rho = np.sqrt(np.maximum((q * q).sum(1) - h * h, 0))
        surf = h - F(1.0) * rho * rho                                         # a shallow paraboloid
        return np.maximum(np.abs(surf) - F(0.007), rho - F(DISH_R))
    fd.add(Func(dish, dc - 0.25, dc + 0.25), 0.004, 7)
    fd.add(Torus(dc + ax * (1.0 * DISH_R ** 2), DISH_R - 0.002, 0.008, R=Rdish), 0.004, 7)
    feed = dc + ax * 0.2
    for k in range(3):
        a = 2 * math.pi * k / 3
        rim = dc + ax * (1.0 * (DISH_R - 0.01) ** 2) + Rdish @ v3((math.cos(a) * (DISH_R - 0.01), math.sin(a) * (DISH_R - 0.01), 0))
        fd.add(RoundCone(rim, feed, 0.0045, 0.004), 0.003, 9)
    fd.add(RoundCone(feed - ax * 0.01, feed + ax * 0.025, 0.017, 0.012), 0.004, 9)
    # a stretch of the roof's parapet behind her: a graphite wall (0), a gunmetal (9) coping, a hazard band (8)
    def wall(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.degrees(np.arctan2(P[:, 1], P[:, 0]))
        dr = np.abs(r - F(sum(WALL_R) / 2)) - F((WALL_R[1] - WALL_R[0]) / 2)
        da = (np.abs(a - F(sum(WALL_A) / 2)) - F((WALL_A[1] - WALL_A[0]) / 2)) * F(math.pi / 180 * 1.1)
        dz = np.abs(P[:, 2] - F(TOP_Z + WALL_H / 2)) - F(WALL_H / 2)
        q = np.stack([np.maximum(dr + F(0.01), 0), np.maximum(da + F(0.01), 0), np.maximum(dz + F(0.01), 0)], 1)
        return np.sqrt((q ** 2).sum(1)) + np.minimum(np.maximum(np.maximum(dr, da), dz) + F(0.01), 0) - F(0.01)
    fd.add(Func(wall, (-0.6, 0.8, TOP_Z - 0.02), (0.6, 1.25, TOP_Z + WALL_H + 0.02), disp=lambda P: F(0.0012) * NOISE(P * F(25)), disp_amp=0.0015), 0.0, 0)
    def coping(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.degrees(np.arctan2(P[:, 1], P[:, 0]))
        return np.maximum(np.maximum(np.abs(r - F(sum(WALL_R) / 2)) - F((WALL_R[1] - WALL_R[0]) / 2 + 0.012),
                                     (np.abs(a - F(sum(WALL_A) / 2)) - F((WALL_A[1] - WALL_A[0]) / 2 + 0.6)) * F(0.019)),
                          np.abs(P[:, 2] - F(TOP_Z + WALL_H + 0.008)) - F(0.012))
    fd.add(Func(coping, (-0.6, 0.8, TOP_Z + WALL_H - 0.03), (0.6, 1.25, TOP_Z + WALL_H + 0.04)), 0.006, 9)
    def band(P):
        a = np.degrees(np.arctan2(P[:, 1], P[:, 0]))
        st = np.sin((a * F(math.pi / 180 * 1.1) + P[:, 2]) * F(2 * math.pi / 0.09))
        return np.maximum(np.abs(P[:, 2] - F(TOP_Z + 0.05)) - F(0.025), -st * F(0.02))
    fd.paint(Func(band, (-0.6, 0.8, TOP_Z), (0.6, 1.25, TOP_Z + 0.1)), 8)
    ma = math.radians(MAST_A)
    mb = v3((math.cos(ma) * sum(WALL_R) / 2, math.sin(ma) * sum(WALL_R) / 2, TOP_Z + WALL_H + 0.02))
    fd.add(Cylinder(mb + Z * 0.01, 0.022, 0.02, rr=0.006), 0.004, 9)
    fd.add(RoundCone(mb, mb + Z * 0.5, 0.009, 0.005), 0.003, 9)
    for k in range(3):
        fd.add(RoundBox(mb + Z * (0.22 + 0.09 * k), (0.06 - 0.012 * k, 0.004, 0.004), 0.003, R=rot_from_axes(z_axis=Z, x_axis=v3((math.cos(ma), math.sin(ma), 0)))), 0.002, 9)
    # the cooling unit
    c, R = _frame(COOLER, 0.1)
    b = c + Z * 0.13
    fd.add(RoundBox(b, (0.17, 0.15, 0.13), 0.016, R=R), 0.0, 0)
    for k in range(5):                                                       # louvres on its sides
        z = 0.05 + 0.04 * k
        for s in (-1, 1):
            fd.sub(RoundBox(c + Z * z + R[:, 0] * (s * 0.17), (0.006, 0.11, 0.008), 0.003, R=R), 0.003)
    gc = b + Z * 0.13
    fd.sub(Cylinder(gc, 0.12, 0.05, rr=0.004), 0.004)
    fd.add(Cylinder(gc - Z * 0.03, 0.03, 0.03, rr=0.008), 0.004, 5)                                         # the hub
    for k in range(5):                                                        # the fan's blades
        a = 2 * math.pi * k / 5
        dd = v3((math.cos(a), math.sin(a), 0.0))
        side = np.cross(Z, dd)
        fd.add(RoundBox(gc - Z * 0.032 + dd * 0.07, (0.045, 0.02, 0.003), 0.003, R=np.stack([dd, side, Z], 1) @ euler(0.4, 0, 0)), 0.003, 5)
    for rr_ in (0.05, 0.085, 0.118):                                          # the grille
        fd.add(Torus(gc - Z * 0.004, rr_, 0.0045), 0.002, 9)
    for k in range(4):
        a = math.pi * k / 4
        dd = v3((math.cos(a), math.sin(a), 0.0))
        fd.add(RoundCone(gc - dd * 0.12 - Z * 0.004, gc + dd * 0.12 - Z * 0.004, 0.004, 0.004), 0.002, 9)
    return fd


def screens_field():
    """The glowing bits (violet, they glow): the rack's status bars and little screen, the deck's screen, the dish's light."""
    fd = Field("Screens")
    R, lights = rack_lights()
    for c, half in lights:
        fd.add(RoundBox(c, half, 0.0025, R=R), 0.0)
    top, Rd = deck_frame()
    slab_c = top + Z * 0.014 + Rd[:, 0] * -0.04
    hinge = slab_c - Rd[:, 1] * 0.1 + Z * 0.01
    lup = norm(Rd[:, 2] * math.sin(DECK_TILT) + Rd[:, 1] * -math.cos(DECK_TILT))
    lid_n = norm(np.cross(Rd[:, 0], lup))
    if lid_n @ Rd[:, 1] < 0:
        lid_n = -lid_n
    Rl = np.stack([Rd[:, 0], lup, lid_n], 1)
    fd.add(RoundBox(hinge + lup * 0.1 + lid_n * 0.006, (0.13, 0.08, 0.003), 0.002, R=Rl), 0.0)
    c, inw, tg = DISH
    fd.add(Sphere(c + Z * 0.3 + inw * 0.026 + Z * 0.012, 0.009), 0.0)
    ma = math.radians(MAST_A)
    fd.add(Sphere(v3((math.cos(ma) * sum(WALL_R) / 2, math.sin(ma) * sum(WALL_R) / 2, TOP_Z + WALL_H + 0.53)), 0.013), 0.0)
    return fd


def cables_field():
    """Cable spaghetti (modern_kit's black rubber, label 12; violet-sleeved (6) runs): from the rack round behind her to
    the case, from the case to the dish, from the rack to the cooling unit, a loose coil by the rack."""
    fd = Field("Cables")
    def run(a0, a1, r0, r1, n=14, wob=0.04, seed=0, rad=0.014, label=12, lift=0.0):
        rs = np.random.RandomState(seed)
        pts = []
        for i in range(n):
            t = i / (n - 1.0)
            a = math.radians(a0 + (a1 - a0) * t)
            r = r0 + (r1 - r0) * t + wob * math.sin(t * math.pi * 3 + seed) + rs.uniform(-0.012, 0.012)
            pts.append(v3((math.cos(a) * r, math.sin(a) * r, TOP_Z + rad - 0.002 + lift * math.sin(t * math.pi))))
        fd.add(Chain(pts, [rad] * n, k=0.006), 0.004, label)
    run(132, 54, 0.86, 0.85, n=16, wob=0.035, seed=1)
    run(130, 56, 0.9, 0.92, n=16, wob=0.03, seed=2, rad=0.011, label=6)
    run(136, 50, 0.82, 0.8, n=14, wob=0.04, seed=3, rad=0.012)
    run(30, -12, 0.86, 0.86, n=12, wob=0.03, seed=4)
    run(28, -14, 0.92, 0.9, n=12, wob=0.025, seed=5, rad=0.011, label=6)
    run(152, 196, 0.86, 0.84, n=12, wob=0.03, seed=6)
    run(150, 192, 0.92, 0.93, n=12, wob=0.02, seed=7, rad=0.011)
    # a loose coil on the plate by the rack
    cc = v3((math.cos(math.radians(116)) * 0.88, math.sin(math.radians(116)) * 0.88, TOP_Z))
    pts = []
    for i in range(40):
        t = i / 39.0
        a = 2 * math.pi * 1.7 * t
        r = 0.07 + 0.02 * t
        pts.append(cc + v3((math.cos(a) * r, math.sin(a) * r, 0.012 + 0.012 * math.sin(a * 0.5) ** 2)))
    fd.add(Chain(pts, [0.011] * len(pts), k=0.004), 0.004, 12)
    # plugs into the rack's back and the case
    return fd


def grass_geometry(seed=0):
    return np.zeros((0, 3)), [], np.zeros((0, 2)), np.zeros(0, dtype=int)


def flower_geometry(seed=0):
    return []


def fields():
    return [("Plate", plate_field(), 0.006), ("Ring", ring_field(), 0.0025), ("Rack", rack_field(), 0.003),
            ("Props", props_field(), 0.0025), ("Screens", screens_field(), 0.002), ("Cables", cables_field(), 0.0028)]


REGION_PARTS = ("Plate", "Rack", "Props", "Cables")
LOW_TARGETS = {"Plate": 2600, "Ring": 640, "Rack": 1800, "Props": 4200, "Screens": 260, "Cables": 1800}
KIT = dict(weave=0.0, black=(0.05, 0.05, 0.06), red=(0.85, 0.25, 0.95), white=(0.9, 0.9, 0.92), gunmetal=(0.24, 0.25, 0.28),
           rubber=(0.07, 0.07, 0.08), olive=(0.95, 0.74, 0.12), coyote=(0.42, 0.9, 0.18))
MAT_OVERRIDES = {"Plate": ("modern_kit", dict(KIT, name="HQ_NestPlate", base=(0.15, 0.16, 0.19))),
                 "Rack": ("modern_kit", dict(KIT, name="HQ_NestKit", base=(0.16, 0.17, 0.2))),
                 "Props": ("modern_kit", dict(KIT, name="HQ_NestKit", base=(0.16, 0.17, 0.2))),
                 "Cables": ("modern_kit", dict(KIT, name="HQ_NestKit", base=(0.16, 0.17, 0.2)))}
GLOW = {"Ring": ((0.85, 0.25, 0.95), 1.0, 0.5), "Screens": ((0.9, 0.45, 1.0), 1.0, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
