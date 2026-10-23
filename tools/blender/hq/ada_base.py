"""Ada's stand: a corner of her workshop on a cobbled street. A round turntable of oak floorboards on a drum of red
brick, its riveted iron rim set with the hero ring: twelve glowing amber lamps in brass bezels (their own emissive mesh).
Round it, on the granite setts: behind her on her right her workbench (an oak top on stout legs, an iron vice on its
corner with a brass gear clamped in it, two gears and a rolled blueprint on the top, another blueprint hanging over the
front edge, an oil can, a coil of copper pipe on the shelf below); behind her a stub of
brick wall broken off in steps, an oak pegboard on it hung with a saw, a big spanner, a hammer and callipers; behind her on
her left a small vertical steam engine
(a riveted boiler on an iron firebox whose grated door glows (an emissive mesh), a brass steam dome and whistle, a
pressure gauge, a chimney pipe, a flywheel on its bearing, a copper steam pipe to its cylinder); before her on her right
a blue-painted toolbox with a hammer, a spanner and a screwdriver; before her on her left a crate of brass cogs with a big
cog leaning against it; weeds between the setts."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
from drummer_base import _cobble_d, CELL

GROUND_R = 1.32
GROUND_TOP = 0.1
PLAT_R = 0.8                      # the turntable's brick drum
RIM_IN = 0.7                      # its iron rim, from here out to PLAT_R
TOP_Z = 0.24                      # the floorboards' top = where she stands
STAND = v3((0.0, 0.0, TOP_Z))
RING_R = 0.75                     # the lamps, in the rim
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


BENCH = _placed(128.0, 0.99)
ENGINE = _placed(52.0, 1.0)
TOOLBOX = _placed(206.0, 1.03)
CRATE = _placed(-31.0, 1.04)
TUFTS = [v3((1.12, 0.12, 0.0)), v3((-1.16, 0.3, 0.0)), v3((0.22, -1.17, 0.0)), v3((-0.5, -1.1, 0.0)), v3((0.25, 1.17, 0.0))]


# ---------------------------------------------------------------------------------------------- the street
def _setts(P):
    """Grooves between the granite setts (0 on a sett's crown, 1 in the joint)."""
    d1, st = _cobble_d(P)
    return smoothstep(0.42, 0.62, d1 / F(CELL)), st


def ground_field():
    """Granite setts (label 0; some a browner stone, 7; grit in the joints, 6) on a low round mound of the street."""
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
        g, st = _setts(P)
        top = smoothstep(GROUND_TOP - 0.03, GROUND_TOP + 0.005, P[:, 2])
        return (F(0.012) * g - st * F(0.6)) * top + F(0.0015) * NOISE(P * F(40))
    fd.add(Func(disc, (-1.45, -1.45, -0.2), (1.45, 1.45, 0.2), disp=relief, disp_amp=0.016), 0.0)
    def grit(P):
        g, st = _setts(P)
        return F(0.6) - g
    fd.paint(Func(grit, (-1.45, -1.45, -0.2), (1.45, 1.45, 0.2)), 6)
    rs = np.random.RandomState(31)
    for k in range(14):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.85, 1.25)
        fd.paint(Sphere(v3((math.cos(a) * r, math.sin(a) * r, GROUND_TOP)), rs.uniform(0.05, 0.09)), 7)
    return fd


# ---------------------------------------------------------------------------------------------- the turntable
def plinth_field():
    """Red brick (label 0): the turntable's drum, courses of bricks with sunk joints."""
    fd = Field("Plinth")
    z0, z1 = GROUND_TOP - 0.06, TOP_Z - 0.03
    course, brick = 0.052, 0.15
    def drum(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        d_r = r - F(PLAT_R)
        d_z = np.maximum(P[:, 2] - F(z1), F(z0) - P[:, 2])
        q = np.stack([np.maximum(d_r + F(0.012), 0), np.maximum(d_z + F(0.012), 0)], 1)
        return np.minimum(np.maximum(d_r + F(0.012), d_z + F(0.012)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.012)
    def joints(P):
        z = P[:, 2] - F(z0)
        row = np.floor(z / F(course))
        fz = z / F(course) - row
        a = np.arctan2(P[:, 1], P[:, 0]) * F(PLAT_R) / F(brick) + row * F(0.5)
        fx = a - np.floor(a)
        jz = np.minimum(fz, F(1) - fz)
        jx = np.minimum(fx, F(1) - fx)
        j = np.maximum(F(1) - smoothstep(0.04, 0.12, jz), F(1) - smoothstep(0.02, 0.06, jx))
        return F(0.004) * j + F(0.0015) * NOISE(P * F(30))
    fd.add(Func(drum, (-0.9, -0.9, z0 - 0.05), (0.9, 0.9, z1 + 0.05), disp=joints, disp_amp=0.005), 0.0)
    return fd


def floor_field():
    """Oak floorboards (label 10: the grain across them, along x) inside the rim, nailed (6: iron)."""
    fd = Field("Floor")
    rs = np.random.RandomState(7)
    pitch = 0.105
    n = int(2 * RIM_IN / pitch) + 2
    grain = lambda P: F(0.0014) * NOISE(P * np.array([5.0, 60.0, 60.0], F)) + F(0.0007) * NOISE(P * F(50))
    for i in range(n):
        y = -RIM_IN - 0.02 + pitch * (i + 0.5)
        half = math.sqrt(max(RIM_IN ** 2 - min(abs(y - pitch / 2), abs(y + pitch / 2)) ** 2, 0.0)) + 0.02
        if half < 0.06:
            continue
        dz = rs.uniform(-0.003, 0.002)
        c = v3((rs.uniform(-0.01, 0.01), y, TOP_Z - 0.02 + dz))
        board = RoundBox(c, (half, pitch / 2 - 0.005, 0.02), 0.006, R=euler(rs.uniform(-0.01, 0.01), 0, rs.uniform(-0.006, 0.006)),
                         disp=grain, disp_amp=0.0015)
        fd.add(Inter(board, Func(lambda P: np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(RIM_IN + 0.01), (-1, -1, 0), (1, 1, 0.5)), 0.004), 0.0, 10)
        for xx in (-0.45, -0.15, 0.15, 0.45):
            if abs(xx) < half - 0.04:
                for s in (-1, 1):
                    fd.add(Sphere(v3((xx + rs.uniform(-0.01, 0.01), y + s * 0.025, TOP_Z + dz + 0.0005)), 0.0055), 0.002, 6)
    return fd


def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + math.radians(15)
    return v3((math.cos(a) * RING_R, math.sin(a) * RING_R, TOP_Z + 0.014))


def rim_field():
    """The turntable's rim: a band of riveted iron plate (armory's dark iron, label 8) round the floorboards' edge, its top
    a little proud of the boards, with a brass-bezelled socket (6) for each lamp."""
    fd = Field("Rim")
    def band(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        d_r = np.maximum(F(RIM_IN) - r, r - F(PLAT_R + 0.012))
        d_z = np.maximum(P[:, 2] - F(TOP_Z + 0.008), F(TOP_Z - 0.06) - P[:, 2])
        q = np.stack([np.maximum(d_r + F(0.006), 0), np.maximum(d_z + F(0.006), 0)], 1)
        return np.minimum(np.maximum(d_r + F(0.006), d_z + F(0.006)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.006)
    fd.add(Func(band, (-0.9, -0.9, TOP_Z - 0.08), (0.9, 0.9, TOP_Z + 0.03), disp=lambda P: F(0.0008) * NOISE(P * F(40)), disp_amp=0.001), 0.0, 8)
    for k in range(48):                                         # rivets round its top and its side
        a = 2 * math.pi * (k + 0.5) / 48
        d = v3((math.cos(a), math.sin(a), 0.0))
        fd.add(Sphere(d * (PLAT_R - 0.016) + v3((0, 0, TOP_Z + 0.008)), 0.0055), 0.002, 8)
        fd.add(Sphere(d * (PLAT_R + 0.012) + v3((0, 0, TOP_Z - 0.03)), 0.0055), 0.002, 8)
    for i in range(N_GLOW):
        c = glow_pos(i)
        fd.add(Torus(c + v3((0, 0, -0.004)), 0.036, 0.008), 0.003, 6)
    return fd


def glowmarks_field():
    """The hero ring: twelve amber glass lamps in the rim (they glow)."""
    fd = Field("Glowmarks")
    for i in range(N_GLOW):
        c = glow_pos(i)
        fd.add(Ellipsoid(c, (0.03, 0.03, 0.02)), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the workshop's wall
WALL_A = (73.0, 107.0)            # a stub of the workshop's brick wall behind her (degrees round her)
WALL_R, WALL_T = 1.17, 0.12
WALL_TOP = GROUND_TOP + 0.78


def wall_top(a):
    """The wall's broken top: full height in the middle, stepping down course by course toward its ends."""
    m = (math.radians(WALL_A[0]) + math.radians(WALL_A[1])) / 2
    t = np.abs(a - F(m)) / F(math.radians(WALL_A[1] - WALL_A[0]) / 2)
    steps = np.floor(np.clip(t - F(0.45), 0, 1) * F(9)) * F(0.052)
    return F(WALL_TOP) - steps


def wall_field():
    """Red brick (label 0): a curved stub of wall, courses and joints cut into it, its top broken off in steps toward both
    ends."""
    fd = Field("Wall")
    a0, a1 = math.radians(WALL_A[0]), math.radians(WALL_A[1])
    course, brick = 0.052, 0.15
    def wall(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        d_r = np.abs(r - F(WALL_R)) - F(WALL_T / 2)
        d_a = np.maximum(F(a0) - a, a - F(a1)) * F(WALL_R)
        d_z = np.maximum(P[:, 2] - wall_top(a), F(GROUND_TOP - 0.06) - P[:, 2])
        q = np.stack([np.maximum(d_r + F(0.008), 0), np.maximum(d_a + F(0.008), 0), np.maximum(d_z + F(0.008), 0)], 1)
        return np.minimum(np.maximum(np.maximum(d_r, d_a), d_z) + F(0.008), 0) + np.sqrt((q ** 2).sum(1)) - F(0.008)
    def joints(P):
        z = P[:, 2] - F(GROUND_TOP - 0.06)
        row = np.floor(z / F(course))
        fz = z / F(course) - row
        x = np.arctan2(P[:, 1], P[:, 0]) * F(WALL_R) / F(brick) + row * F(0.5)
        fx = x - np.floor(x)
        j = np.maximum(F(1) - smoothstep(0.05, 0.14, np.minimum(fz, F(1) - fz)), F(1) - smoothstep(0.02, 0.06, np.minimum(fx, F(1) - fx)))
        return F(0.005) * j + F(0.002) * NOISE(P * F(25))
    R = WALL_R + 0.2
    fd.add(Func(wall, (-R, 0.0, GROUND_TOP - 0.1), (R, R, WALL_TOP + 0.05), disp=joints, disp_amp=0.006), 0.0)
    return fd


def board_frame():
    """The pegboard on the wall's inner face: (its middle, inward, tangent)."""
    a = math.radians(sum(WALL_A) / 2)
    d = v3((math.cos(a), math.sin(a), 0.0))
    c = d * (WALL_R - WALL_T / 2 - 0.012) + v3((0, 0, GROUND_TOP + 0.5))
    return c, -d, norm(np.cross(v3((0, 0, 1)), -d))


def board_field():
    """An oak pegboard (siege: label 10) on the wall, a row of iron pegs (6)."""
    fd = Field("Board")
    c, inw, tg = board_frame()
    R = np.stack([tg, inw, v3((0, 0, 1))], 1)
    fd.add(RoundBox(c, (0.25, 0.012, 0.17), 0.006, R=R, disp=lambda P: F(0.001) * NOISE(P * F(40)), disp_amp=0.0012), 0.0, 10)
    for k in range(5):
        fd.add(RoundCone(c + tg * (-0.18 + 0.09 * k) + v3((0, 0, 0.1)), c + tg * (-0.18 + 0.09 * k) + inw * 0.035 + v3((0, 0, 0.11)), 0.006, 0.005), 0.003, 6)
    return fd


# ---------------------------------------------------------------------------------------------- the workbench
BENCH_TOP = GROUND_TOP + 0.62
BENCH_HL, BENCH_HD = 0.34, 0.14


def bench_frame():
    """(its middle on the floor plan (z = 0: heights below are absolute), inward, tangent, its rotation)."""
    c, inw, tg = BENCH
    return v3((c[0], c[1], 0.0)), inw, tg, np.stack([tg, inw, v3((0, 0, 1))], 1)


def bench_field():
    """Oak (labels: 10 grain along its length, 11 upright): the bench top, four stout legs, rails and a shelf."""
    fd = Field("Bench")
    c, inw, tg, R = bench_frame()
    grain = lambda P: F(0.0012) * NOISE(P * F(40))
    top = c + v3((0, 0, BENCH_TOP - 0.025))
    fd.add(RoundBox(top, (BENCH_HL, BENCH_HD, 0.025), 0.008, R=R, disp=grain, disp_amp=0.0015), 0.0, 10)
    for sl in (-1, 1):
        for sd in (-1, 1):
            p = c + tg * (sl * (BENCH_HL - 0.04)) + inw * (sd * (BENCH_HD - 0.035))
            g = ground_height(p[0], p[1])
            fd.add(RoundBox(p + v3((0, 0, (g - 0.02 + BENCH_TOP - 0.05) / 2)), (0.026, 0.026, (BENCH_TOP - 0.05 - g + 0.02) / 2),
                            0.006, R=R, disp=grain, disp_amp=0.0015), 0.004, 11)
    shelf = c + v3((0, 0, GROUND_TOP + 0.16))
    fd.add(RoundBox(shelf, (BENCH_HL - 0.03, BENCH_HD - 0.02, 0.012), 0.005, R=R, disp=grain, disp_amp=0.0012), 0.004, 10)
    for sd in (-1, 1):
        fd.add(RoundBox(c + inw * (sd * (BENCH_HD - 0.035)) + v3((0, 0, BENCH_TOP - 0.09)), (BENCH_HL - 0.04, 0.012, 0.03), 0.005, R=R), 0.004, 10)
    return fd


def vice_point():
    c, inw, tg, R = bench_frame()
    return c + tg * (-(BENCH_HL - 0.09)) + inw * (BENCH_HD - 0.02) + v3((0, 0, BENCH_TOP))


def blueprint_frame():
    c, inw, tg, R = bench_frame()
    return c + tg * 0.06 + inw * 0.02 + v3((0, 0, BENCH_TOP)), inw, tg


def paper_field():
    """Blueprints (linen material: blue paper, label 0; white lines, 6): a sheet on the bench hanging over its front edge,
    curling at its foot, a gear drawn on it; a rolled sheet lying on the bench."""
    fd = Field("Paper")
    p0, inw, tg = blueprint_frame()
    c, _i, _t, R = bench_frame()
    edge = c + inw * BENCH_HD + v3((0, 0, BENCH_TOP))
    W = 0.13
    def sheet(P):
        q = P - edge.astype(F)
        u = q @ tg.astype(F) - F(0.06)
        s = -(q @ inw.astype(F))                   # back from the front edge (on the top)
        z = q[:, 2]
        # on the top: a slab from s = 0 to 0.2; over the edge: a curve hanging down 0.12, curling out at its foot
        top = np.maximum(np.maximum(-s, s - F(0.2)), np.abs(z - F(0.002)) - F(0.0018))
        hang = np.maximum(np.maximum(s - F(0.006), z - F(0.0)), np.maximum(-z - F(0.12), np.abs(s + F(0.006) + F(0.25) * np.maximum(-z - F(0.08), F(0)) ** 2 * F(10)) - F(0.0022)))
        fold = np.sqrt((s + F(0.002)) ** 2 + (z + F(0.0005)) ** 2) - F(0.0035)         # (round the bench's edge)
        return np.maximum(np.minimum(np.minimum(top, hang), fold), np.abs(u) - F(W))
    fd.add(Func(sheet, edge - 0.35, edge + 0.35, disp=lambda P: F(0.0006) * NOISE(P * F(30)), disp_amp=0.001), 0.0)
    # the drawing: a frame, a gear's circle and spokes, a few lines (on the top part)
    def lines(P):
        q = P - edge.astype(F)
        u = q @ tg.astype(F) - F(0.06)
        s = -(q @ inw.astype(F))
        frame = np.abs(np.maximum(np.abs(u) - F(W - 0.012), np.abs(s - F(0.1)) - F(0.088))) - F(0.0016)
        gc_u, gc_s = F(-0.03), F(0.1)
        rr = np.sqrt((u - gc_u) ** 2 + (s - gc_s) ** 2)
        circ = np.minimum(np.abs(rr - F(0.05)) - F(0.0016), np.abs(rr - F(0.018)) - F(0.0014))
        ang = np.arctan2(s - gc_s, u - gc_u)
        spokes = np.where(rr < F(0.05), np.abs(np.sin(ang * F(3))) * rr - F(0.0016), F(1))
        txt = np.where((u > F(0.04)) & (u < F(0.11)), np.minimum.reduce([np.abs(s - F(v)) - F(0.0012) for v in (0.04, 0.07, 0.1, 0.13)]), F(1))
        return np.minimum(np.minimum(frame, circ), np.minimum(spokes, txt))
    fd.paint(Func(lines, edge - 0.35, edge + 0.35), 6)
    # the rolled sheet
    a = c + tg * (BENCH_HL - 0.12) + inw * (-0.05) + v3((0, 0, BENCH_TOP + 0.022))
    d = norm(tg * 0.3 + inw * 1.0)
    fd.add(RoundCone(a - d * 0.12, a + d * 0.12, 0.022, 0.022), 0.004)
    fd.sub(Cylinder(a + d * 0.12, 0.012, 0.03, R=rot_from_axes(z_axis=d)), 0.002)
    return fd


# ---------------------------------------------------------------------------------------------- the steam engine
def engine_frame():
    c, inw, tg = ENGINE
    return c, inw, tg


BOILER_R = 0.14
BOX_TOP = GROUND_TOP + 0.24
BOILER_TOP = GROUND_TOP + 0.66


def engine_field():
    """armory: dark iron (8) for the firebox, the boiler's riveted plates, the chimney and the flywheel; brass (6) for its
    bands, the steam dome and whistle, the gauge's bezel; bright steel (7) for the gauge's face and the piston rod; copper
    (9) for the steam pipe."""
    fd = Field("Engine")
    c, inw, tg = engine_frame()
    Rf = np.stack([tg, inw, v3((0, 0, 1))], 1)
    ham = lambda P: F(0.0008) * NOISE(P * F(45))
    # the firebox: an iron box on short feet, its door toward her
    box = c + v3((0, 0, (GROUND_TOP + BOX_TOP) / 2 - c[2] + 0.01 + c[2]))
    box = v3((c[0], c[1], (GROUND_TOP + BOX_TOP) / 2 + 0.01))
    fd.add(RoundBox(box, (0.17, 0.16, (BOX_TOP - GROUND_TOP) / 2 - 0.005), 0.014, R=Rf, disp=ham, disp_amp=0.001), 0.0, 8)
    door = box + inw * 0.162
    fd.add(RoundBox(door, (0.075, 0.008, 0.06), 0.004, R=Rf), 0.003, 8)                         # the door's frame
    fd.sub(RoundBox(door + inw * 0.004, (0.06, 0.03, 0.046), 0.003, R=Rf), 0.002)               # its opening (the fire glows in it)
    for k in range(5):                                                                          # the grate's bars
        p = door + tg * (-0.048 + 0.024 * k)
        fd.add(RoundBox(p, (0.005, 0.006, 0.048), 0.002, R=Rf), 0.002, 8)
    fd.add(RoundCone(door + tg * 0.085 + inw * 0.004, door + tg * 0.085 + inw * 0.03, 0.006, 0.006), 0.002, 6)     # its handle
    for s in (-1, 1):
        for t in (-1, 1):
            fd.add(Sphere(box + tg * (s * 0.15) + inw * (t * 0.14) + v3((0, 0, (BOX_TOP - GROUND_TOP) / 2 - 0.01)), 0.006), 0.002, 8)
    # the boiler: a riveted drum with brass bands, a domed top
    b0 = v3((c[0], c[1], BOX_TOP - 0.01))
    b1 = v3((c[0], c[1], BOILER_TOP))
    fd.add(Cylinder((b0 + b1) / 2, BOILER_R, BOILER_TOP - BOX_TOP + 0.01, rr=0.02, disp=ham, disp_amp=0.001), 0.01, 8)
    fd.add(Ellipsoid(b1, (BOILER_R - 0.005, BOILER_R - 0.005, 0.07)), 0.02, 8)
    for z in (BOX_TOP + 0.05, (BOX_TOP + BOILER_TOP) / 2, BOILER_TOP - 0.04):
        fd.add(Torus(v3((c[0], c[1], z)), BOILER_R + 0.002, 0.008), 0.004, 6)
        for k in range(16):
            a = 2 * math.pi * k / 16
            d = v3((math.cos(a), math.sin(a), 0))
            fd.add(Sphere(v3((c[0], c[1], z + 0.02)) + d * (BOILER_R + 0.002), 0.005), 0.002, 8)
    # the steam dome and whistle
    dm = b1 + v3((0, 0, 0.05)) - inw * 0.02
    fd.add(RoundCone(dm, dm + v3((0, 0, 0.06)), 0.05, 0.042), 0.015, 6)
    fd.add(Ellipsoid(dm + v3((0, 0, 0.065)), (0.044, 0.044, 0.025)), 0.01, 6)
    wh = dm + v3((0, 0, 0.078)) + tg * 0.01
    fd.add(Cylinder(wh + v3((0, 0, 0.03)), 0.013, 0.06, rr=0.004), 0.004, 6)
    fd.add(Ellipsoid(wh + v3((0, 0, 0.065)), (0.016, 0.016, 0.01)), 0.003, 6)
    # the chimney, up from the back of the boiler's top
    ch0 = b1 - inw * 0.07 + v3((0, 0, 0.02))
    ch1 = v3((ch0[0], ch0[1], GROUND_TOP + 1.3))
    fd.add(RoundCone(ch0, ch1, 0.038, 0.034), 0.01, 8)
    fd.add(Cylinder(ch1 + v3((0, 0, 0.015)), 0.052, 0.05, rr=0.012), 0.008, 8)                      # its cap
    fd.sub(Cylinder(ch1 + v3((0, 0, 0.05)), 0.03, 0.06), 0.003)
    for z in (0.95, 1.15):
        fd.add(Torus(v3((ch0[0], ch0[1], GROUND_TOP + z)), 0.037, 0.006), 0.003, 6)
    # the gauge on the boiler's front
    gp = v3((c[0], c[1], BOILER_TOP - 0.13)) + inw * (BOILER_R + 0.012) + tg * 0.05
    fd.add(Cylinder(gp, 0.036, 0.022, rr=0.006, R=rot_from_axes(z_axis=inw)), 0.006, 6)
    fd.add(Cylinder(gp + inw * 0.009, 0.029, 0.008, rr=0.003, R=rot_from_axes(z_axis=inw)), 0.002, 7)
    fd.add(RoundCone(gp + inw * 0.014, gp + inw * 0.014 + norm(tg * 0.6 + v3((0, 0, 0.8))) * 0.022, 0.0026, 0.0016), 0.001, 8)
    # a valve wheel below it
    vp = v3((c[0], c[1], BOILER_TOP - 0.28)) + inw * (BOILER_R + 0.03) - tg * 0.06
    fd.add(RoundCone(vp - inw * 0.03, vp, 0.01, 0.01), 0.003, 6)
    fd.add(Torus(vp, 0.032, 0.006, R=rot_from_axes(z_axis=inw)), 0.003, 8)
    for k in range(3):
        a = 2 * math.pi * k / 3
        o = (tg * math.cos(a) + v3((0, 0, 1)) * math.sin(a)) * 0.03
        fd.add(RoundCone(vp, vp + o, 0.004, 0.004), 0.002, 8)
    # the flywheel on its bearing at the side, the cylinder and its rod
    fw = c - tg * 0.27 + inw * 0.02
    fw[2] = GROUND_TOP + 0.2
    Rw = rot_from_axes(z_axis=tg)
    fd.add(Torus(fw, 0.165, 0.018, R=Rw), 0.0, 8)
    fd.add(Cylinder(fw, 0.03, 0.05, rr=0.008, R=Rw), 0.006, 8)
    for k in range(6):
        a = 2 * math.pi * k / 6
        o = Rw @ v3((math.cos(a), math.sin(a), 0)) * 0.155
        fd.add(RoundCone(fw, fw + o, 0.011, 0.008), 0.006, 8)
    fd.add(RoundBox(fw + tg * 0.05 - v3((0, 0, 0.09)), (0.04, 0.06, 0.1), 0.01, R=Rf), 0.006, 8)       # the bearing stand
    fd.add(RoundCone(fw - tg * 0.03, fw + tg * 0.08, 0.016, 0.016), 0.004, 7)                          # the axle
    cy = c - tg * 0.13 + v3((0, 0, 0.0))
    cy[2] = BOX_TOP + 0.06
    fd.add(RoundCone(cy, cy - tg * 0.05, 0.04, 0.04), 0.008, 6)                                       # the cylinder (brass)
    fd.add(RoundCone(cy - tg * 0.05, fw + tg * 0.06 + v3((0, 0, 0.05)), 0.008, 0.008), 0.003, 7)     # the rod to the crank
    fd.add(RoundCone(fw + tg * 0.07, fw + tg * 0.065 + v3((0, 0, 0.05)), 0.012, 0.01), 0.004, 8)        # the crank
    # the copper steam pipe from the dome down to the cylinder
    pts = [dm + tg * -0.03 + v3((0, 0, 0.03)), dm - tg * 0.1 + v3((0, 0, 0.05)), cy + v3((0, 0, 0.2)) - tg * 0.02, cy + v3((0, 0, 0.04))]
    fd.add(Chain(pts, [0.011] * 4, k=0.01), 0.004, 9)
    return fd


def fire_field():
    """The glow behind the firebox's grated door (its own emissive mesh)."""
    fd = Field("Fire")
    c, inw, tg = engine_frame()
    Rf = np.stack([tg, inw, v3((0, 0, 1))], 1)
    box = v3((c[0], c[1], (GROUND_TOP + BOX_TOP) / 2 + 0.01))
    fd.add(RoundBox(box + inw * 0.14, (0.062, 0.015, 0.048), 0.006, R=Rf), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the toolbox and the crate
def crates_field():
    """Wood (siege: grain along x, 10; upright, 11): the toolbox painted blue (7) with a dark handle bar (6: iron), the
    hammer's handle (11); the crate of slats (10, 11), straw in it (8)."""
    fd = Field("Crates")
    # the toolbox
    c, inw, tg = TOOLBOX
    R = np.stack([tg, inw, v3((0, 0, 1))], 1) @ euler(0, 0, 0.25)
    tgr, inr = R[:, 0], R[:, 1]
    h = 0.13
    b = c + v3((0, 0, h / 2 - 0.004))
    fd.add(RoundBox(b, (0.16, 0.085, h / 2), 0.008, R=R), 0.0, 7)
    fd.sub(RoundBox(b + v3((0, 0, 0.03)), (0.148, 0.073, h / 2), 0.004, R=R), 0.004)
    for s in (-1, 1):                                                                                 # end boards up to the handle
        fd.add(Inter(RoundBox(b + tgr * (s * 0.152) + v3((0, 0, 0.06)), (0.008, 0.085, 0.1), 0.004, R=R),
                     Ellipsoid(b + tgr * (s * 0.152) + v3((0, 0, 0.0)), (0.05, 0.09, 0.2), R=R), 0.004), 0.003, 7)
    fd.add(RoundCone(b - tgr * 0.15 + v3((0, 0, 0.14)), b + tgr * 0.15 + v3((0, 0, 0.14)), 0.011, 0.011), 0.003, 6)
    hm = b + inr * 0.03 + tgr * 0.05
    fd.add(RoundCone(hm - tgr * 0.03 + v3((0, 0, -0.05)), hm + tgr * 0.1 + v3((0, 0, 0.13)), 0.011, 0.01), 0.003, 11)     # the hammer's handle
    # the crate
    c, inw, tg = CRATE
    R = np.stack([tg, inw, v3((0, 0, 1))], 1) @ euler(0, 0, -0.3)
    tgr, inr = R[:, 0], R[:, 1]
    hc = 0.2
    b = c + v3((0, 0, hc / 2 - 0.006))
    fd.add(RoundBox(b, (0.13, 0.13, hc / 2), 0.006, R=R), 0.0, 10)
    fd.sub(RoundBox(b + v3((0, 0, 0.04)), (0.118, 0.118, hc / 2), 0.004, R=R), 0.003)
    for zz in (-0.05, 0.03):                                                                          # gaps between the slats
        for ax in (tgr, inr):
            nrm = np.cross(ax, v3((0, 0, 1)))
            for s in (-1, 1):
                fd.sub(RoundBox(b + nrm * (s * 0.13) + v3((0, 0, zz + 0.005)), (0.14, 0.012, 0.004), 0.002,
                                R=np.stack([ax, nrm, v3((0, 0, 1))], 1)), 0.002)
    for s in (-1, 1):
        for t in (-1, 1):
            fd.add(RoundBox(b + tgr * (s * 0.122) + inr * (t * 0.122), (0.014, 0.014, hc / 2 + 0.004), 0.004, R=R), 0.003, 11)
    fd.add(Ellipsoid(b + v3((0, 0, 0.06)), (0.11, 0.11, 0.04), R=R, disp=lambda P: F(0.006) * NOISE(P * F(60)), disp_amp=0.007), 0.004, 8)
    return fd


def _gear(fd, c, n, r, th, teeth, label=6, hole=True):
    R = rot_from_axes(z_axis=n)
    def g(P, c=c, R=R):
        q = (P - c.astype(F)) @ R.astype(F)
        rr = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        a = np.arctan2(q[:, 1], q[:, 0])
        tooth = np.clip(np.cos(a * F(teeth)) * F(2.2), -1, 1) * F(0.5) + F(0.5)
        rad = F(r * 0.86) + F(r * 0.16) * tooth
        d = np.maximum(rr - rad, np.abs(q[:, 2]) - F(th * 0.5))
        if hole:
            d = np.maximum(d, F(r * 0.22) - rr)
            win = np.maximum(np.maximum(F(r * 0.34) - rr, rr - F(r * 0.66)), (F(0.42) - np.abs(np.sin(a * F(2)))) * F(r * 0.5))
            d = np.maximum(d, -win)
        return d
    fd.add(Func(g, c - r - 0.02, c + r + 0.02), 0.0, label)


def metal_field():
    """armory: the vice (dark iron, 8; its jaws steel, 7) with a brass gear (6) clamped in it, gears on the bench, an oil
    can (brass 6, its spout copper 9), a coil of copper pipe on the shelf; in the toolbox a spanner (8) and a screwdriver
    (7 shaft, 0 walnut handle), the hammer's head (8); brass cogs in the crate and a big one leaning on it."""
    fd = Field("Metal")
    c, inw, tg, R = bench_frame()
    # the vice
    vp = vice_point()
    fd.add(RoundBox(vp + v3((0, 0, 0.02)), (0.035, 0.05, 0.02), 0.006, R=R), 0.0, 8)
    for s in (-1, 1):
        jaw = vp + inw * (s * 0.02 + 0.02) + v3((0, 0, 0.065))
        fd.add(RoundBox(jaw, (0.045, 0.012, 0.035), 0.004, R=R), 0.004, 8)
        fd.add(RoundBox(jaw - inw * (s * 0.012) + v3((0, 0, 0.022)), (0.044, 0.003, 0.012), 0.002, R=R), 0.002, 7)
    sc0 = vp + inw * 0.05 + v3((0, 0, 0.055))
    fd.add(RoundCone(sc0 - inw * 0.03, sc0 + inw * 0.06, 0.009, 0.009), 0.003, 8)
    fd.add(RoundCone(sc0 + inw * 0.06 - tg * 0.06, sc0 + inw * 0.06 + tg * 0.06, 0.006, 0.006), 0.003, 8)
    for s in (-1, 1):
        fd.add(Sphere(sc0 + inw * 0.06 + tg * (s * 0.062), 0.01), 0.002, 8)
    _gear(fd, vp + inw * 0.02 + v3((0, 0, 0.105)), inw, 0.05, 0.012, 12)                       # the gear in the vice
    # gears lying on the bench
    _gear(fd, c + tg * 0.2 + inw * 0.04 + v3((0, 0, BENCH_TOP + 0.006)), v3((0, 0, 1)), 0.065, 0.012, 14)
    _gear(fd, c + tg * 0.25 + inw * -0.07 + v3((0, 0, BENCH_TOP + 0.006)), v3((0.1, 0, 1)), 0.04, 0.01, 10)
    # an oil can
    oc = c + tg * -0.12 + inw * -0.08 + v3((0, 0, BENCH_TOP))
    fd.add(RoundCone(oc + v3((0, 0, 0.01)), oc + v3((0, 0, 0.06)), 0.045, 0.032), 0.01, 6)
    fd.add(RoundCone(oc + v3((0, 0, 0.06)), oc + v3((0, 0, 0.09)), 0.018, 0.012), 0.006, 6)
    sp = oc + v3((0, 0, 0.085))
    fd.add(RoundCone(sp, sp + norm(inw + tg * 0.3 + v3((0, 0, 0.8))) * 0.11, 0.006, 0.003), 0.003, 9)
    fd.add(Torus(oc + v3((0, 0, 0.07)) - inw * 0.04, 0.025, 0.005, R=rot_from_axes(z_axis=tg)), 0.003, 6)
    # a coil of copper pipe on the shelf
    sc = c + tg * 0.12 + v3((0, 0, GROUND_TOP + 0.16 + 0.012 + 0.012))
    pts = []
    for i in range(61):
        a = 2 * math.pi * 2.6 * i / 60
        rr = 0.07 + 0.012 * i / 60
        pts.append(sc + tg * (math.cos(a) * rr) + inw * (math.sin(a) * rr) + v3((0, 0, 0.012 * i / 60)))
    fd.add(Chain(pts, [0.009] * len(pts), k=0.004), 0.003, 9)
    # in the toolbox: a spanner and a screwdriver standing up, the hammer's head
    c2, inw2, tg2 = TOOLBOX
    R2 = np.stack([tg2, inw2, v3((0, 0, 1))], 1) @ euler(0, 0, 0.25)
    tgr, inr = R2[:, 0], R2[:, 1]
    b = c2 + v3((0, 0, 0.061))
    sp0 = b - tgr * 0.08 - inr * 0.02
    d = norm(v3((0, 0, 1)) - tgr * 0.25)
    fd.add(RoundBox(sp0 + d * 0.07, (0.008, 0.004, 0.08), 0.003, R=rot_from_axes(z_axis=d, x_axis=tgr)), 0.0, 8)
    jc = sp0 + d * 0.17
    fd.add(Cylinder(jc, 0.024, 0.009, rr=0.003, R=rot_from_axes(z_axis=inr)), 0.004, 8)
    fd.sub(RoundBox(jc + d * 0.018, (0.008, 0.02, 0.025), 0.002, R=rot_from_axes(z_axis=d, x_axis=tgr)), 0.002)
    sd0 = b - tgr * 0.02 + inr * 0.03
    d2 = norm(v3((0, 0, 1)) + tgr * 0.2 - inr * 0.25)
    fd.add(RoundCone(sd0, sd0 + d2 * 0.1, 0.004, 0.004), 0.002, 7)
    fd.add(RoundCone(sd0 + d2 * 0.1, sd0 + d2 * 0.18, 0.012, 0.011), 0.003, 0)
    hm = b + inr * 0.03 + tgr * 0.05 + tgr * 0.1 + v3((0, 0, 0.13 - 0.02))
    hd = norm(tgr * 0.1 + v3((0, 0, 0.13)))
    hx = norm(np.cross(hd, inr))
    fd.add(RoundBox(hm + hd * 0.01, (0.05, 0.016, 0.016), 0.005, R=np.stack([hx, inr, hd], 1)), 0.004, 8)
    # brass cogs in the crate, a big one leaning on it
    c3, inw3, tg3 = CRATE
    R3 = np.stack([tg3, inw3, v3((0, 0, 1))], 1) @ euler(0, 0, -0.3)
    b3 = c3 + v3((0, 0, 0.1))
    _gear(fd, b3 + R3[:, 0] * 0.03 + v3((0, 0, 0.09)), norm(R3[:, 1] + v3((0, 0, 0.4))), 0.07, 0.014, 14)
    _gear(fd, b3 - R3[:, 0] * 0.05 + R3[:, 1] * -0.03 + v3((0, 0, 0.07)), norm(R3[:, 0] + v3((0, 0, 0.6))), 0.05, 0.012, 10)
    lean = c3 + inw3 * 0.15 + v3((0, 0, 0.11))
    _gear(fd, lean, norm(inw3 + v3((0, 0, 0.3))), 0.1, 0.016, 16)
    # tools hanging on the pegboard: a saw, a big spanner, a hammer, callipers
    c4, inw4, tg4 = board_frame()
    peg = lambda k: c4 + tg4 * (-0.18 + 0.09 * k) + inw4 * 0.03 + v3((0, 0, 0.1))
    Rb = np.stack([tg4, inw4, v3((0, 0, 1))], 1)
    p0 = peg(0)                                                                  # the saw: a steel blade (7), walnut handle (0)
    fd.add(RoundBox(p0 + v3((0, 0, -0.03)) + inw4 * 0.004, (0.022, 0.012, 0.03), 0.008, R=Rb), 0.0, 0)
    fd.add(Inter(RoundBox(p0 + v3((0, 0, -0.15)) + inw4 * 0.004, (0.03, 0.0025, 0.1), 0.002, R=Rb),
                 Plane(p0 + v3((0, 0, -0.06)) + tg4 * 0.032, norm(tg4 + v3((0, 0, -0.18)))), 0.002), 0.003, 7)
    p1 = peg(1) + inw4 * 0.004                                                   # a big spanner (8)
    fd.add(RoundBox(p1 + v3((0, 0, -0.12)), (0.011, 0.004, 0.1), 0.003, R=Rb), 0.0, 8)
    jc = p1 + v3((0, 0, -0.24))
    fd.add(Cylinder(jc, 0.032, 0.01, rr=0.003, R=rot_from_axes(z_axis=inw4)), 0.004, 8)
    fd.sub(RoundBox(jc + v3((0, 0, -0.025)), (0.012, 0.03, 0.03), 0.003, R=Rb), 0.002)
    fd.add(Torus(p1 + v3((0, 0, -0.012)), 0.014, 0.004, R=rot_from_axes(z_axis=inw4)), 0.002, 8)
    p3 = peg(3) + inw4 * 0.004                                                   # a hammer, head down
    fd.add(RoundCone(p3 + v3((0, 0, -0.01)), p3 + v3((0, 0, -0.17)), 0.009, 0.011), 0.0, 0)
    fd.add(RoundBox(p3 + v3((0, 0, -0.19)), (0.045, 0.014, 0.016), 0.005, R=Rb), 0.004, 8)
    p4 = peg(4) + inw4 * 0.004                                                   # callipers (brass, 6)
    for s_ in (-1, 1):
        fd.add(Chain([p4 + v3((0, 0, -0.01)), p4 + tg4 * (s_ * 0.025) + v3((0, 0, -0.09)), p4 + tg4 * (s_ * 0.012) + v3((0, 0, -0.17))],
                     [0.004, 0.004, 0.003], k=0.002), 0.002, 6)
    fd.add(Torus(p4 + v3((0, 0, -0.006)), 0.012, 0.004, R=rot_from_axes(z_axis=inw4)), 0.002, 6)
    return fd


# ---------------------------------------------------------------------------------------------- weeds
def grass_geometry(seed=59):
    """Weeds in the setts: short, arching blades."""
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    for ti, c in enumerate(TUFTS):
        for b in range(11):
            ang = rs.uniform(0, 2 * math.pi)
            out = v3((math.cos(ang), math.sin(ang), 0))
            root = c + out * rs.uniform(0, 0.03)
            root[2] = ground_height(root[0], root[1]) - 0.008
            d = norm(out * rs.uniform(0.25, 0.6) + v3((0, 0, 1)))
            L = rs.uniform(0.07, 0.14)
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
    return [("Ground", ground_field(), 0.008), ("Plinth", plinth_field(), 0.005), ("Floor", floor_field(), 0.004),
            ("Rim", rim_field(), 0.003), ("Glowmarks", glowmarks_field(), 0.0025), ("Bench", bench_field(), 0.004),
            ("Paper", paper_field(), 0.0022), ("Engine", engine_field(), 0.0035), ("Fire", fire_field(), 0.004),
            ("Crates", crates_field(), 0.003), ("Metal", metal_field(), 0.0022), ("Wall", wall_field(), 0.004),
            ("Board", board_field(), 0.003)]


REGION_PARTS = ("Ground", "Floor", "Rim", "Bench", "Paper", "Engine", "Crates", "Metal", "Board")
LOW_TARGETS = {"Ground": 2200, "Plinth": 1100, "Floor": 2200, "Rim": 1100, "Glowmarks": 300, "Bench": 900, "Paper": 500,
               "Engine": 2600, "Fire": 60, "Crates": 1100, "Metal": 2600, "Wall": 900, "Board": 300}
OAK = {"wood": (0.56, 0.38, 0.22), "wood2": (0.42, 0.27, 0.15), "metal": "iron"}
MAT_OVERRIDES = {"Ground": ("flagstone", {"name": "HQ_Setts", "base": (0.44, 0.43, 0.42), "alt": (0.52, 0.45, 0.37)}),
                 "Plinth": ("mudbrick", {"name": "HQ_RedBrick", "base": (0.6, 0.24, 0.16), "mortar": (0.66, 0.62, 0.55),
                                         "course": 0.052, "brick": 0.15}),
                 "Floor": ("siege", dict(OAK, name="HQ_Floorboards")),
                 "Rim": ("armory", {"name": "HQ_TurntableRim"}),
                 "Bench": ("siege", dict(OAK, name="HQ_Workbench")),
                 "Board": ("siege", dict(OAK, name="HQ_Workbench")),
                 "Wall": ("mudbrick", {"name": "HQ_RedBrick", "base": (0.6, 0.24, 0.16), "mortar": (0.66, 0.62, 0.55),
                                       "course": 0.052, "brick": 0.15}),
                 "Paper": ("linen", {"name": "HQ_Blueprint", "base": (0.2, 0.36, 0.64), "stripe": (0.9, 0.93, 0.97)}),
                 "Engine": ("armory", {"name": "HQ_SteamEngine", "copper": ((0.75, 0.35, 0.18), (0.98, 0.66, 0.44))}),
                 "Crates": ("siege", {"name": "HQ_Boxes", "wood": (0.6, 0.45, 0.28), "wood2": (0.46, 0.33, 0.2),
                                      "blue": (0.14, 0.26, 0.5), "metal": "iron"}),
                 "Metal": ("armory", {"name": "HQ_WorkshopMetal", "copper": ((0.75, 0.35, 0.18), (0.98, 0.66, 0.44))})}
GLOW = {"Glowmarks": ((1.0, 0.64, 0.2), 1.0, 0.5), "Fire": ((1.0, 0.42, 0.1), 1.2, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
