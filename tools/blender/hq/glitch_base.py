"""Glitch's stand: a scrapyard-lab corner of the tech corps' base. A round platform of dark floor plates (graphite, panel
seams between the plates, a band of yellow-and-black hazard striping round its side) on a cracked asphalt yard; violet
light strips set in some of its seams (their own emissive mesh), the hero ring of twelve amber marker lights in steel
bezels in its top (their own emissive mesh), and a round data port in the floor before him on his right (a steel hatch
in a violet-lit ring): where his fist lands in his Ability when he faces the base's front.
Behind him on his left a steel workbench: spare robot parts on it (a white robot head with orange hazard stripes and
dead, dark eyes, its neck cables trailing, a severed claw), a big wrench, bolts, a coil of cable. Behind him on his
right his charging station: a graphite dock with navy panels, a violet light strip up its face, a small screen glowing
teal (a battery, filling), its charging cable looped down to the floor. A severed white robot arm lies on the asphalt
before him on his left; black cables run over the plates from the dock to the bench; a few weeds in the asphalt's
cracks at the back."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b

GROUND_R = 1.32
GROUND_TOP = 0.08
PAD_R = 0.86                       # the floor-plate platform
TOP_Z = 0.2                        # its top = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
RING_R = 0.76                      # the marker lights, in its top
N_GLOW = 12
PORT = v3((-0.42, -0.36, TOP_Z))   # the data port (his Ability's fist, facing the base's front: anim_glitch.PUNCH_PT)
PORT_R = 0.085

# the robots' colours (the spare parts) and the hazard band
SUIT, GRAPHITE, NAVY, SEAM, VIOLET, TAPE, STEEL, GLASS, FACE, WHITE, ORANGE, RUBBER, YELLOW = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.012 * max(0.0, 1 - (r / GROUND_R) ** 2)


def _placed(angle_deg, r, turn=0.0):
    """A prop's place round him: (centre on the ground, its inward direction (toward him), its tangent)."""
    a = math.radians(angle_deg)
    c = v3((math.cos(a) * r, math.sin(a) * r, 0.0))
    c[2] = ground_height(c[0], c[1])
    inward = euler(0, 0, math.radians(turn)) @ -norm(v3((c[0], c[1], 0.0)))
    tang = norm(np.cross(v3((0, 0, 1)), inward))
    return c, inward, tang


BENCH = _placed(58.0, 1.08, 8.0)
DOCK = _placed(126.0, 1.04, -6.0)
ARM_SCRAP = _placed(-52.0, 1.06, 30.0)


def _frame_of(pl):
    c, inw, tg = pl
    return c, inw, tg, np.stack([tg, inw, v3((0, 0, 1))], 1)


# ---------------------------------------------------------------------------------------------- the yard, the platform
def ground_field():
    """Cracked asphalt (pavement: label 0) on a low round slab, an oil stain (8), a faded yellow line (5)."""
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.012) * np.sin(a * 5 + 0.7) + F(0.008) * np.sin(a * 11 + 2.1)
        dome = F(GROUND_TOP) + F(0.012) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.03), 0), np.maximum(dz + F(0.03), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.03), dz + F(0.03)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.03)
    rough = lambda P: F(0.0016) * NOISE(P * F(60)) + F(0.0012) * NOISE(P * F(13))
    fd.add(Func(disc, (-1.45, -1.45, -0.2), (1.45, 1.45, 0.2), disp=rough, disp_amp=0.003), 0.0)
    rs = np.random.RandomState(9)
    for k in range(7):
        a = rs.uniform(0, 2 * math.pi)
        r0 = rs.uniform(0.9, 1.02)
        pts = []
        aa = a
        for i in range(5):
            rr = r0 + 0.07 * i
            aa += rs.uniform(-0.06, 0.06)
            pts.append(v3((math.cos(aa) * rr, math.sin(aa) * rr, ground_height(math.cos(aa) * rr, math.sin(aa) * rr) + 0.003)))
        fd.sub(Chain(pts, [0.005, 0.006, 0.005, 0.004, 0.002], k=0.003), 0.002)
    fd.paint(Ellipsoid(v3((-0.98, 0.3, GROUND_TOP)), (0.14, 0.1, 0.05), R=euler(0, 0, 0.6),
                       disp=lambda P: F(0.02) * NOISE(P * F(14)), disp_amp=0.02), 8)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 1] + F(1.05) - F(0.05) * P[:, 0]) - F(0.04), F(GROUND_TOP - 0.02) - P[:, 2]),
                  (-1.5, -1.5, -0.1), (1.5, -0.7, 0.3)), 5)
    return fd


SEAMS_A = 0.3                      # the plates' seams run at this angle (radians) ...
PLATE = 0.32                       # ... this far apart


def _plate_uv(P):
    c, s = math.cos(SEAMS_A), math.sin(SEAMS_A)
    return P[:, 0] * F(c) + P[:, 1] * F(s), -P[:, 0] * F(s) + P[:, 1] * F(c)


STRIPS = [(-1, 0.15, 0.62), (1, -0.62, -0.25), (1, 0.3, 0.7)]       # (seam index, from, to) along v (u = index * PLATE + PLATE/2)


def _strip_d(P, grow=0.0):
    u, v = _plate_uv(P)
    d = np.full(len(P), F(1.0))
    for i, a, b in STRIPS:
        uc = F((i + 0.5) * PLATE)
        di = np.maximum(np.abs(u - uc) - F(0.009 + grow), np.maximum(F(a) - v, v - F(b)) - F(grow))
        d = np.minimum(d, di)
    return d


def plates_field():
    """The platform (android: graphite plates 5) with chamfered edges: panel seams (7) between square plates, rows of
    treads on the plates, a hazard band (yellow 16, black rubber 15) round its side; the violet strips' channels; the
    data port's ring (steel 10) and hatch."""
    fd = Field("Plates")
    z0 = GROUND_TOP - 0.05
    def slab(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        d_r = r - F(PAD_R)
        d_z = np.maximum(P[:, 2] - F(TOP_Z), F(z0) - P[:, 2])
        cham = (r - F(PAD_R) + P[:, 2] - F(TOP_Z) + F(0.024)) * F(0.7071)
        q = np.stack([np.maximum(d_r + F(0.006), 0), np.maximum(d_z + F(0.006), 0)], 1)
        box = np.minimum(np.maximum(d_r + F(0.006), d_z + F(0.006)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.006)
        return np.maximum(box, cham)
    fd.add(Func(slab, (-0.95, -0.95, z0 - 0.03), (0.95, 0.95, TOP_Z + 0.03)), 0.0, GRAPHITE)
    # seams between the plates (grooves)
    def seams(P):
        u, v = _plate_uv(P)
        su = np.abs(u - F(PLATE) * np.floor(u / F(PLATE) + F(0.5)) - F(0.0)) - F(0.0035)
        sv = np.abs(v - F(PLATE) * np.floor(v / F(PLATE) + F(0.5))) - F(0.0035)
        su = np.abs((u + F(PLATE * 0.5)) - F(PLATE) * np.floor((u + F(PLATE * 0.5)) / F(PLATE) + F(0.5))) - F(0.0035)
        return np.maximum(np.minimum(su, sv), F(TOP_Z - 0.006) - P[:, 2])
    fd.sub(Func(seams, (-0.95, -0.95, TOP_Z - 0.02), (0.95, 0.95, TOP_Z + 0.02)), 0.0015)
    fd.paint(Func(lambda P: seams(P) - F(0.004), (-0.95, -0.95, TOP_Z - 0.03), (0.95, 0.95, TOP_Z + 0.03)), SEAM)
    # tread bumps: short raised bars in alternating directions on each plate
    def treads(P):
        u, v = _plate_uv(P)
        cu = np.floor(u / F(PLATE) + F(0.5))
        cv = np.floor(v / F(PLATE))
        flip = np.mod(cu + cv, F(2)) > F(0.5)
        a, b = np.where(flip, u, v), np.where(flip, v, u)
        sa = np.abs(a - F(0.04) * np.floor(a / F(0.04) + F(0.5))) - F(0.006)
        sb = np.abs(b - F(0.04) * np.floor(b / F(0.04)) - F(0.02)) - F(0.012)
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.maximum(np.maximum(sa, sb), np.abs(P[:, 2] - F(TOP_Z)) - F(0.0025)), r - F(PAD_R - 0.06))
    fd.add(Func(treads, (-0.9, -0.9, TOP_Z - 0.01), (0.9, 0.9, TOP_Z + 0.01)), 0.0015, GRAPHITE)
    # the violet strips' channels
    fd.sub(Func(lambda P: np.maximum(_strip_d(P, 0.004), F(TOP_Z - 0.01) - P[:, 2]), (-0.95, -0.95, TOP_Z - 0.03), (0.95, 0.95, TOP_Z + 0.03)), 0.001)
    # the hazard band round the side
    def band(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(F(PAD_R - 0.035) - r, np.maximum(P[:, 2] - F(TOP_Z - 0.03), F(GROUND_TOP + 0.005) - P[:, 2]))
    def hazard(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        s = np.sin((a * F(PAD_R) + P[:, 2]) * F(2 * math.pi / 0.12))
        return np.maximum(band(P), -s * F(0.01))
    fd.paint(Func(band, (-0.95, -0.95, 0.0), (0.95, 0.95, TOP_Z)), RUBBER)
    fd.paint(Func(hazard, (-0.95, -0.95, 0.0), (0.95, 0.95, TOP_Z)), YELLOW)
    # the data port: a steel ring flush in the floor round a hatch with a grip bar
    p = PORT
    fd.sub(Cylinder(p, PORT_R + 0.03, 0.02), 0.002)
    fd.add(Cylinder(p + v3((0, 0, -0.006)), PORT_R + 0.028, 0.012, rr=0.004), 0.002, STEEL)
    fd.add(Cylinder(p + v3((0, 0, -0.002)), PORT_R - 0.006, 0.01, rr=0.004), 0.002, GRAPHITE)
    fd.sub(Torus(p + v3((0, 0, 0.003)), PORT_R + 0.01, 0.007), 0.001)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        fd.add(Sphere(p + v3((math.cos(a) * (PORT_R + 0.021), math.sin(a) * (PORT_R + 0.021), 0.0)), 0.006), 0.001, STEEL)
    fd.add(RoundBox(p + v3((0, 0, 0.004)), (0.045, 0.01, 0.006), 0.004, R=euler(0, 0, 0.5)), 0.002, STEEL)
    for s in (-1, 1):
        fd.paint(Func(lambda P, s=s: np.maximum(np.abs((P - p.astype(F)) @ np.array([math.cos(0.5 + 1.5708), math.sin(0.5 + 1.5708), 0], F)
                                                         - F(s * 0.032)) - F(0.008), np.sqrt(((P - p.astype(F))[:, :2] ** 2).sum(1)) - F(PORT_R - 0.012)),
                      p - 0.15, p + 0.15), YELLOW)
    return fd


def strips_field():
    """The violet light strips in the plates' channels (their own glowing mesh)."""
    fd = Field("Strips")
    fd.add(Func(lambda P: np.maximum(_strip_d(P), np.abs(P[:, 2] - F(TOP_Z - 0.006)) - F(0.0045)), (-0.95, -0.95, TOP_Z - 0.03), (0.95, 0.95, TOP_Z + 0.03)), 0.0)
    return fd


def port_glow_field():
    """The violet ring round the data port's hatch."""
    fd = Field("PortGlow")
    fd.add(Torus(PORT + v3((0, 0, 0.001)), PORT_R + 0.01, 0.0055), 0.0)
    return fd


def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + math.radians(15)
    return v3((math.cos(a) * RING_R, math.sin(a) * RING_R, TOP_Z + 0.005))


def rim_field():
    """The marker lights' steel bezels (10), with black screws (15)."""
    fd = Field("Rim")
    for i in range(N_GLOW):
        c = glow_pos(i)
        fd.add(Torus(c + v3((0, 0, -0.002)), 0.032, 0.008), 0.0, STEEL)
        fd.add(Cylinder(c + v3((0, 0, -0.008)), 0.04, 0.01, rr=0.004), 0.004, STEEL)
        for k in range(3):
            a = 2 * math.pi * k / 3 + i
            fd.add(Sphere(c + v3((math.cos(a) * 0.034, math.sin(a) * 0.034, -0.002)), 0.0045), 0.001, RUBBER)
    return fd


def glowmarks_field():
    fd = Field("Glowmarks")
    for i in range(N_GLOW):
        fd.add(Ellipsoid(glow_pos(i), (0.025, 0.025, 0.011)), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the workbench and its scrap
BENCH_H = (0.27, 0.15, 0.62)      # half length, half depth, the top's height above the ground


def bench_frame():
    return _frame_of(BENCH)


def robot_head_frame():
    c, inw, tg, R = bench_frame()
    top = c + v3((0, 0, BENCH_H[2] + 0.02))
    hc = top + tg * 0.08 + inw * 0.02 + v3((0, 0, 0.1))
    Rh = R @ euler(0.2, 0.0, math.radians(-150))               # tipped back a little, its dead face to him and the camera
    return hc, Rh


def bench_field():
    """android: a steel (10) workbench: a graphite (5) top with a navy (6) edge, tube legs and a shelf; on it a white (13)
    robot head with hazard-orange (14) stripes and dark glass (11) eyes (dead), its neck cables (15) trailing, a severed
    white claw, a big steel wrench with a rubber grip, a few bolts, a coil of black cable."""
    fd = Field("Bench")
    c, inw, tg, R = bench_frame()
    L, D, H = BENCH_H
    top = c + v3((0, 0, H))
    fd.add(RoundBox(top, (L, D, 0.02), 0.008, R=R), 0.0, GRAPHITE)
    fd.paint(Func(lambda P: F(D - 0.02) - np.abs((P - top.astype(F)) @ inw.astype(F)), top - 0.5, top + 0.5), NAVY)
    for sl in (-1, 1):
        for sd in (-1, 1):
            a = top + tg * (sl * (L - 0.035)) + inw * (sd * (D - 0.03))
            fd.add(RoundCone(v3((a[0], a[1], c[2] - 0.01)), a, 0.016, 0.016), 0.004, STEEL)
    shelf = c + v3((0, 0, 0.13))
    fd.add(RoundBox(shelf, (L - 0.03, D - 0.03, 0.01), 0.005, R=R), 0.006, STEEL)
    # a crate of parts on the shelf
    fd.add(RoundBox(shelf + tg * 0.1 + v3((0, 0, 0.06)), (0.11, 0.08, 0.05), 0.008, R=R), 0.004, NAVY)
    # the robot head: a white dome, an orange stripe over its crown, a dark visor band with two dead lens eyes, a jaw grille
    hc, Rh = robot_head_frame()
    fwd = Rh[:, 1] * -1.0                                       # (its face)
    fd.add(Ellipsoid(hc, (0.105, 0.1, 0.095), R=Rh), 0.006, WHITE)
    fd.add(RoundBox(hc - Rh[:, 2] * 0.06 + fwd * 0.02, (0.085, 0.07, 0.04), 0.03, R=Rh), 0.03, WHITE)
    fd.paint(Func(lambda P: np.abs((P - hc.astype(F)) @ Rh[:, 0].astype(F)) - F(0.022), hc - 0.2, hc + 0.2), ORANGE)
    fd.sub(RoundBox(hc + fwd * 0.1 + Rh[:, 2] * 0.01, (0.075, 0.03, 0.024), 0.02, R=Rh), 0.006)
    fd.paint(RoundBox(hc + fwd * 0.09 + Rh[:, 2] * 0.01, (0.082, 0.04, 0.03), 0.022, R=Rh), GLASS)
    for s in (-1, 1):
        fd.add(Sphere(hc + fwd * 0.078 + Rh[:, 2] * 0.01 + Rh[:, 0] * (s * 0.034), 0.017), 0.003, GLASS)
        fd.add(Torus(hc + fwd * 0.088 + Rh[:, 2] * 0.01 + Rh[:, 0] * (s * 0.034), 0.02, 0.004, R=rot_from_axes(z_axis=fwd)), 0.002, STEEL)
        fd.add(Cylinder(hc + Rh[:, 0] * (s * 0.1), 0.03, 0.03, rr=0.008, R=rot_from_axes(z_axis=Rh[:, 0])), 0.004, STEEL)   # ear bolts
    for k in range(3):
        fd.sub(RoundBox(hc + fwd * 0.095 - Rh[:, 2] * (0.045 + 0.013 * k), (0.03, 0.02, 0.003), 0.002, R=Rh), 0.002)
    # neck cables trailing from under it over the bench's edge
    base = hc - Rh[:, 2] * 0.09
    for i, (o, lab) in enumerate(((-0.025, RUBBER), (0.0, STEEL), (0.026, RUBBER))):
        p0 = base + tg * o
        pts = [p0, p0 + inw * -0.05 + v3((0, 0, -0.03)), top + tg * (0.02 + o) - inw * (D - 0.01) + v3((0, 0, 0.025)),
               top + tg * (0.02 + o * 1.4) - inw * (D + 0.02) + v3((0, 0, -0.03)), top + tg * (0.03 + o * 1.8) - inw * (D + 0.03) + v3((0, 0, -0.1 - 0.02 * i))]
        fd.add(Chain(pts, [0.008] * len(pts), k=0.01), 0.003, lab)
    # a severed claw (white, three steel talons)
    cc = top + tg * -0.12 + inw * 0.04 + v3((0, 0, 0.04))
    fd.add(Ellipsoid(cc, (0.05, 0.04, 0.03), R=R @ euler(0, 0, 0.6)), 0.004, WHITE)
    for k in range(3):
        a = -0.6 + 0.6 * k
        d = R @ norm(v3((math.cos(a + 0.6), math.sin(a + 0.6), 0.0)))
        fd.add(Chain([cc + d * 0.04, cc + d * 0.075 + v3((0, 0, -0.01)), cc + d * 0.095 + v3((0, 0, -0.03))], [0.011, 0.009, 0.005], k=0.004), 0.004, STEEL)
    # the wrench lying across the front of the top
    w0 = top + tg * -0.2 + inw * 0.08 + v3((0, 0, 0.026))
    wd = R @ norm(v3((1.0, -0.2, 0.0)))
    fd.add(RoundBox(w0 + wd * 0.1, (0.016, 0.007, 0.11), 0.004, R=rot_from_axes(z_axis=wd, y_axis=(0, 0, 1))), 0.003, STEEL)
    fd.add(RoundBox(w0 + wd * 0.05, (0.019, 0.01, 0.05), 0.006, R=rot_from_axes(z_axis=wd, y_axis=(0, 0, 1))), 0.003, RUBBER)
    for e, r in ((-0.005, 0.03), (0.215, 0.034)):
        fd.add(Cylinder(w0 + wd * e, r, 0.012, rr=0.004), 0.004, STEEL)
        fd.sub(RoundBox(w0 + wd * (e - 0.02 if e < 0 else e + 0.02), (0.012, 0.03, 0.02), 0.002, R=rot_from_axes(z_axis=(0, 0, 1), y_axis=wd)), 0.002)
    # bolts, a coil of cable
    rs = np.random.RandomState(3)
    for k in range(4):
        b = top + tg * rs.uniform(-0.25, 0.0) + inw * rs.uniform(-0.1, 0.1) + v3((0, 0, 0.026))
        fd.add(Cylinder(b, 0.011, 0.012, rr=0.003), 0.002, STEEL)
    cc2 = top + tg * 0.21 + inw * -0.06 + v3((0, 0, 0.032))
    fd.add(Torus(cc2, 0.045, 0.011), 0.003, RUBBER)
    fd.add(Torus(cc2 + v3((0, 0, 0.016)), 0.04, 0.011, R=euler(0.1, 0.05, 0)), 0.003, RUBBER)
    return fd


# ---------------------------------------------------------------------------------------------- the charging station
DOCK_H = 0.92


def dock_frame():
    return _frame_of(DOCK)


def dock_field():
    """android: a graphite (5) charging dock, navy (6) side panels, a steel (10) base and cradle arm, panel lines (7); its
    screen's dark glass bezel (11); the charging cable (15) looped down to the floor."""
    fd = Field("Dock")
    c, inw, tg, R = dock_frame()
    b = c + v3((0, 0, 0.03))
    fd.add(RoundBox(b + v3((0, 0, 0.0)), (0.17, 0.13, 0.03), 0.012, R=R), 0.0, STEEL)
    body = c + v3((0, 0, DOCK_H / 2 + 0.04))
    fd.add(RoundBox(body, (0.12, 0.085, DOCK_H / 2), 0.03, R=R), 0.01, GRAPHITE)
    fd.add(RoundBox(body + v3((0, 0, DOCK_H / 2 - 0.01)), (0.135, 0.1, 0.035), 0.03, R=R), 0.01, NAVY)          # a cap
    for s in (-1, 1):
        fd.add(RoundBox(body + tg * (s * 0.118), (0.012, 0.07, DOCK_H / 2 - 0.08), 0.008, R=R), 0.006, NAVY)
    fd.paint(Func(lambda P: np.abs((P - body.astype(F)) @ np.array([0, 0, 1], F) - F(0.1)) - F(0.003), body - 0.5, body + 0.5), SEAM)
    # the light strip's channel up its face, the screen's bezel
    face = body + inw * 0.085
    fd.sub(RoundBox(face + tg * -0.06 + v3((0, 0, -0.05)), (0.012, 0.02, 0.3), 0.006, R=R), 0.002)
    sc = face + v3((0, 0, 0.26)) + tg * 0.03
    fd.add(RoundBox(sc, (0.07, 0.012, 0.055), 0.008, R=R), 0.004, GLASS)
    # the cradle arm and the plug on its end, the cable looping down to the floor and away toward the bench
    arm0 = face + v3((0, 0, 0.05)) + tg * 0.05
    fd.add(RoundBox(arm0 + inw * 0.04, (0.03, 0.05, 0.025), 0.01, R=R), 0.004, STEEL)
    plug = arm0 + inw * 0.09
    fd.add(Cylinder(plug, 0.024, 0.05, rr=0.008, R=rot_from_axes(z_axis=inw)), 0.004, RUBBER)
    g = ground_height(plug[0], plug[1])
    pts = [plug + inw * 0.02, plug + inw * 0.06 + v3((0, 0, -0.12)), plug + inw * 0.05 + tg * 0.06 + v3((0, 0, -0.3)),
           v3((plug[0], plug[1], 0)) + inw * 0.0 + tg * 0.1 + v3((0, 0, g + 0.012)), v3((plug[0], plug[1], 0)) - inw * 0.05 + tg * 0.18 + v3((0, 0, g + 0.012))]
    fd.add(Chain(pts, [0.011] * len(pts), k=0.03), 0.004, RUBBER)
    return fd


def dock_strip_field():
    """The violet light strip up the dock's face."""
    fd = Field("DockStrip")
    c, inw, tg, R = dock_frame()
    body = c + v3((0, 0, DOCK_H / 2 + 0.04))
    face = body + inw * 0.085
    fd.add(RoundBox(face + tg * -0.06 + v3((0, 0, -0.05)) - inw * 0.006, (0.008, 0.012, 0.29), 0.004, R=R), 0.0)
    return fd


def screen_field():
    """The dock's screen (glowing teal: a battery filling)."""
    fd = Field("Screen")
    c, inw, tg, R = dock_frame()
    body = c + v3((0, 0, DOCK_H / 2 + 0.04))
    sc = body + inw * 0.085 + v3((0, 0, 0.26)) + tg * 0.03
    fd.add(RoundBox(sc + inw * 0.012, (0.055, 0.004, 0.04), 0.003, R=R), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the scrap arm, the cables
def scrap_field():
    """android: a severed robot arm on the asphalt (a white (13) forearm shell with an orange (14) band, a steel (10)
    elbow joint, torn black (15) cables at the stump, three steel claws)."""
    fd = Field("Scrap")
    c, inw, tg, R = _frame_of(ARM_SCRAP)
    g = c[2]
    a = c + tg * -0.13 + v3((0, 0, 0.045))
    b = c + tg * 0.14 + inw * 0.04 + v3((0, 0, 0.045))
    fd.add(RoundCone(a, b, 0.05, 0.042), 0.0, WHITE)
    fd.paint(Func(lambda P: np.abs((P - lerp(a, b, 0.55).astype(F)) @ norm(b - a).astype(F)) - F(0.022), a - 0.3, b + 0.3), ORANGE)
    fd.add(Sphere(a - norm(b - a) * 0.02, 0.046), 0.006, STEEL)
    for k in range(3):
        d = norm(-norm(b - a) + v3((math.sin(k * 2.1), math.cos(k * 2.1), 0.3)) * 0.4)
        p0 = a - norm(b - a) * 0.04
        fd.add(Chain([p0, p0 + d * 0.05 + v3((0, 0, -0.02)), p0 + d * 0.09 + v3((0, 0, -0.04))], [0.009, 0.008, 0.006], k=0.004), 0.003, RUBBER)
    hd = norm(b - a)
    fd.add(Ellipsoid(b + hd * 0.04, (0.045, 0.04, 0.034), R=rot_from_axes(z_axis=hd)), 0.006, STEEL)
    for k in range(3):
        ang = -0.7 + 0.7 * k
        d = norm(hd + norm(np.cross(v3((0, 0, 1)), hd)) * math.sin(ang) * 0.9)
        p0 = b + hd * 0.06
        fd.add(Chain([p0, p0 + d * 0.06 + v3((0, 0, 0.005)), p0 + d * 0.1 + v3((0, 0, -0.02))], [0.012, 0.009, 0.005], k=0.004), 0.003, STEEL)
    return fd


def cables_field():
    """Black cables (15) over the plates from the dock to the bench."""
    fd = Field("Cables")
    cb, ib, tb, _ = bench_frame()
    cd, idd, td, _ = dock_frame()
    pts = []
    for i in range(9):
        a = math.radians(122.0 - (122.0 - 64.0) * i / 8.0)
        r = 0.9 if i in (0, 8) else 0.82
        x, y = math.cos(a) * r, math.sin(a) * r
        z = TOP_Z + 0.008 if math.hypot(x, y) < PAD_R - 0.03 else ground_height(x, y) + 0.008
        pts.append(v3((x, y, z)))
    pts = [cd + idd * 0.15 + v3((0, 0, 0.012))] + pts + [cb + ib * 0.12 + v3((0, 0, 0.02)), cb + ib * 0.12 + v3((0, 0, 0.3))]
    for p in pts[1:-2]:
        r = math.hypot(p[0], p[1])
        if PAD_R - 0.05 < r < PAD_R + 0.04:
            p[2] = TOP_Z + 0.01
    fd.add(Chain(pts, [0.01] * len(pts), k=0.03), 0.0, RUBBER)
    return fd


# ---------------------------------------------------------------------------------------------- weeds in the cracks
def _blocked(c, pad=0.0):
    r = math.hypot(c[0], c[1])
    if r < PAD_R + 0.08 + pad or r > GROUND_R - 0.05:
        return True
    for pl, rr in ((BENCH, 0.34), (DOCK, 0.24), (ARM_SCRAP, 0.22)):
        if math.hypot(c[0] - pl[0][0], c[1] - pl[0][1]) < rr + pad:
            return True
    return False


def grass_geometry(seed=41):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 9 and tries < 6000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PAD_R + 0.1, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.02) or c[1] < -0.5:
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.12 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        for b in range(rs.randint(6, 10)):
            ang = rs.uniform(0, 2 * math.pi)
            out = v3((math.cos(ang), math.sin(ang), 0))
            root = c + out * rs.uniform(0, 0.03)
            root[2] = ground_height(root[0], root[1]) - 0.005
            d = norm(out * rs.uniform(0.2, 0.5) + v3((0, 0, 1)))
            L = rs.uniform(0.05, 0.1)
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.018, 0.026), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=3,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=43):
    return []


def fields():
    return [("Ground", ground_field(), 0.007), ("Plates", plates_field(), 0.003), ("Strips", strips_field(), 0.002),
            ("PortGlow", port_glow_field(), 0.0018), ("Rim", rim_field(), 0.0022), ("Glowmarks", glowmarks_field(), 0.002),
            ("Bench", bench_field(), 0.0024), ("Dock", dock_field(), 0.0026), ("DockStrip", dock_strip_field(), 0.002),
            ("Screen", screen_field(), 0.0016), ("Scrap", scrap_field(), 0.002), ("Cables", cables_field(), 0.003)]


REGION_PARTS = ("Ground", "Plates", "Rim", "Bench", "Dock", "Scrap", "Cables")
LOW_TARGETS = {"Ground": 1600, "Plates": 3400, "Strips": 200, "PortGlow": 120, "Rim": 900, "Glowmarks": 300, "Bench": 3200,
               "Dock": 1600, "DockStrip": 40, "Screen": 40, "Scrap": 900, "Cables": 400}
MAT_OVERRIDES = {"Ground": ("pavement", {"name": "HQ_YardAsphalt", "asphalt": (0.2, 0.2, 0.21)})}
for _nm in ("Plates", "Rim", "Bench", "Dock", "Scrap", "Cables"):
    MAT_OVERRIDES[_nm] = ("android", {"name": "HQ_Glitch" + _nm, "wear": 1.3})
VIOLET_GLOW = (0.85, 0.25, 0.95)
GLOW = {"Glowmarks": ((1.0, 0.64, 0.2), 1.0, 0.5), "Strips": (VIOLET_GLOW, 1.2, 0.5), "PortGlow": (VIOLET_GLOW, 1.2, 0.5),
        "DockStrip": (VIOLET_GLOW, 1.2, 0.5), "Screen": ((0.12, 1.0, 0.78), 0.9, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
