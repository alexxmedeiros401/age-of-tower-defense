"""Big Jim's stand: a corner of the railway yard. A length of track runs from the front of the base back to a timber
buffer stop behind him (painted red with white stripes, two iron buffers): dark creosoted sleepers bedded in grey
ballast, two iron rails spiked down through tie plates; he stands on the sleepers between the rails. On his left, on
the cinders beside the track, a small riveted vertical boiler (black iron, brass bands, a pressure gauge, a brass steam
dome and whistle, a tall stack with a flared cap, its firebox door open on a glowing fire: its own emissive mesh), and a
steam pipe led along the ground from its foot to a valve standpipe at the front-left of the track, topped with a big red
striker cap: the valve his Ability slams open with the maul (anim_jim.VALVE). A heap of coal behind the boiler; on his
right a signal lamp on an iron post (a red glowing lens toward the robots) and a stack of spare sleepers. Round it all
the hero ring: twelve amber lamp glasses set in brass cups in the cinders (their own emissive mesh), where the track and
the props leave room; trampled earth and cinders, grass at the rim (distance fields + grass as direct low-poly
geometry)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, lerp
import base as _b
import kael_base as kb
from tarek import curls

GROUND_R = kb.GROUND_R
GROUND_TOP = kb.GROUND_TOP
ground_height = kb.ground_height
TOP_Z = 0.28                       # the sleepers' tops = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
BALLAST_Z = TOP_Z - 0.012          # the ballast's top between the sleepers
BED_W = 0.72                       # half the ballast bed's width at its top
BED_BACK = 0.98                    # its back end (y)
RAIL_X = 0.46                      # the rails' centre lines (x = +-)
RAIL_Y0, RAIL_Y1 = -1.15, 0.82     # their ends
SLEEPERS_Y = (-0.96, -0.64, -0.32, 0.0, 0.32, 0.64)
SLEEPER_H = (0.6, 0.078, 0.036)    # half sizes: along X, along Y, height
BUFFER_Y = 0.86                    # the buffer stop's beam (its front face a little in front)
BEAM_Z = TOP_Z + 0.3
BOILER = v3((0.9, 0.24, 0.0))      # the boiler, on his left
BOILER_R = 0.16
BOILER_TOP = 0.78                  # its barrel's top (world z)
VALVE = v3((0.68, -0.6, 0.0))      # the valve standpipe at the track's front-left
VALVE_TOP = TOP_Z + 0.2            # the red striker cap's top (world z)
LAMP = v3((-0.86, 0.5, 0.0))       # the signal lamp's post
LAMP_C = v3((-0.86, 0.47, 1.12))   # its lamp head
STACK = v3((-0.9, -0.34, 0.0))     # the sleeper stack
COAL = v3((0.86, 0.66, 0.0))
RING_R = 1.19
N_GLOW = 12


def valve_point():
    """The middle of the red striker cap's top (base space = character space when he faces the base's front)."""
    return v3((VALVE[0], VALVE[1], VALVE_TOP))


def _chip(P):
    return F(0.0024) * NOISE(P * F(11)) + F(0.0012) * NOISE(P * F(37))


# ---------------------------------------------------------------------------------------------- ground and ballast
def ground_field():
    """The yard's earth: trampled bare and sooty with cinders (label 5) but for a grassy rim."""
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.035) * np.sin(a * 5 + 0.3) + F(0.02) * np.sin(a * 11 + 1.9) + F(0.02) * NOISE(P * F(3))
        dome = F(GROUND_TOP) + F(0.05) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.09), 0), np.maximum(dz + F(0.09), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.09), dz + F(0.09)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.09)
    fd.add(Func(disc, (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3),
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    fd.paint(Func(lambda P: np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(1.08) - F(0.07) * NOISE(P * F(4)), (-1.6, -1.6, -0.25), (1.6, 1.6, 0.3)), 5)
    return fd


def ballast_field():
    """Grey crushed-stone ballast (label 0): a bed under the track, its sides sloping down to the earth, its back end
    sloped off behind the buffer stop; it runs out over the base's front edge."""
    fd = Field("Ballast")
    def bed(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        s = (F(BALLAST_Z) - z) * F(1.1)
        side = (np.abs(x) - F(BED_W) - s) * F(0.7)
        back = (y - F(BED_BACK) - s) * F(0.7)
        top = z - F(BALLAST_Z)
        bottom = F(GROUND_TOP - 0.08) - z
        rim = np.sqrt(x * x + y * y) - F(1.27)
        return np.maximum(np.maximum(np.maximum(side, back), np.maximum(top, bottom)), rim)
    fd.add(Func(bed, (-1.1, -1.35, GROUND_TOP - 0.1), (1.1, 1.25, TOP_Z + 0.02),
                disp=lambda P: curls(P, 0.026, 0.012) + F(0.002) * NOISE(P * F(9)), disp_amp=0.014), 0.0)
    return fd


def sleepers_field():
    """Creosoted timber sleepers (grain along X, label 10), checked and split at their ends."""
    fd = Field("Sleepers")
    rs = np.random.RandomState(17)
    hx, hy, hz = SLEEPER_H
    grain = lambda P: F(0.0022) * NOISE(P * np.array([5.0, 70.0, 70.0], F)) + F(0.001) * NOISE(P * F(45))
    for y in SLEEPERS_Y:
        c = v3((rs.uniform(-0.02, 0.02), y + rs.uniform(-0.012, 0.012), TOP_Z - hz + rs.uniform(-0.004, 0.0)))
        L = hx + rs.uniform(-0.03, 0.02)
        fd.add(RoundBox(c, (L, hy, hz), 0.012, R=euler(0, rs.uniform(-0.012, 0.012), rs.uniform(-0.04, 0.04)), disp=grain, disp_amp=0.0025), 0.0, 10)
        for sx in (-1, 1):                                                            # splits in the ends
            e = c + v3((sx * (L - 0.02), 0, 0))
            fd.sub(RoundBox(e + v3((0, rs.uniform(-0.03, 0.03), 0.02)), (0.05, 0.003, 0.03), 0.002), 0.002)
    return fd


def _rail2d(dx, zr):
    """A flat-bottomed rail's section (2D distance, < 0 inside): head, web, foot; zr from the sleeper's top."""
    def rect(cx, cz, hx, hz, r):
        qx = np.abs(dx) - F(hx - r)
        qz = np.abs(zr - F(cz)) - F(hz - r)
        return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qx, qz), 0) - F(r)
    head = rect(0, 0.07, 0.025, 0.017, 0.006)
    web = rect(0, 0.036, 0.0095, 0.028, 0.003)
    foot = rect(0, 0.0115, 0.044, 0.0065, 0.003)
    return smin(smin(head, web, 0.008), foot, 0.008)


def rails_field():
    """Iron: the two rails (worn bright along their heads: the material's edges), a tie plate under each rail on every
    sleeper and two spike heads either side of it (label 0)."""
    fd = Field("Rails")
    for sx in (-1, 1):
        xc = sx * RAIL_X
        def rail(P, xc=xc):
            d = _rail2d(P[:, 0] - F(xc), P[:, 2] - F(TOP_Z + 0.006))
            ends = np.abs(P[:, 1] - F((RAIL_Y0 + RAIL_Y1) / 2)) - F((RAIL_Y1 - RAIL_Y0) / 2)
            return np.maximum(d, ends)
        fd.add(Func(rail, (xc - 0.06, RAIL_Y0 - 0.02, TOP_Z - 0.01), (xc + 0.06, RAIL_Y1 + 0.02, TOP_Z + 0.1),
                    disp=lambda P: F(0.0012) * NOISE(P * F(40)), disp_amp=0.0015), 0.0)
        for y in SLEEPERS_Y:
            fd.add(RoundBox(v3((xc, y, TOP_Z + 0.002)), (0.066, 0.06, 0.006), 0.003), 0.003)
            for s2 in (-1, 1):
                for t in (-1, 1):
                    p = v3((xc + s2 * 0.054, y + t * 0.03, TOP_Z + 0.012))
                    fd.add(RoundBox(p, (0.011, 0.009, 0.007), 0.003), 0.002)
    return fd


# ---------------------------------------------------------------------------------------------- the buffer stop
def buffer_field():
    """Heavy timber (posts: grain up, 11; the beam: along X, 10; braces 0) painted red (5) with white stripes (7) on the
    beam's face, iron buffers and bolts (6)."""
    fd = Field("Buffer")
    grain = lambda P: F(0.0018) * NOISE(P * F(60))
    yb = BUFFER_Y
    for sx in (-1, 1):
        x = sx * 0.5
        foot = v3((x, yb + 0.02, BALLAST_Z - 0.06))
        fd.add(RoundBox(foot + v3((0, 0, 0.27)), (0.06, 0.06, 0.29), 0.012, disp=grain, disp_amp=0.002), 0.0, 11)
        # a brace from the post's top back down to the ballast
        a = v3((x, yb + 0.05, BEAM_Z + 0.03))
        b = v3((x, yb + 0.42, BALLAST_Z - 0.05))
        d = norm(b - a)
        fd.add(RoundBox((a + b) / 2, (0.045, 0.045, np.linalg.norm(b - a) / 2), 0.01, R=rot_from_axes(z_axis=d, x_axis=(1, 0, 0)),
                        disp=grain, disp_amp=0.002), 0.008, 0)
    beam_c = v3((0.0, yb, BEAM_Z))
    fd.add(RoundBox(beam_c, (0.66, 0.075, 0.075), 0.014, disp=grain, disp_amp=0.002), 0.006, 5)
    # white diagonal stripes on the beam's front (the red is the beam's own label)
    def stripes(P):
        s = np.sin((P[:, 0] + (P[:, 2] - F(BEAM_Z))) * F(2 * math.pi / 0.2))
        face = np.maximum(P[:, 1] - F(yb - 0.05), np.abs(P[:, 2] - F(BEAM_Z)) - F(0.09))
        return np.maximum(F(0.35) - s, face * F(10.0)) * F(0.01)
    fd.paint(Func(stripes, beam_c - v3((0.8, 0.2, 0.2)), beam_c + v3((0.8, 0.2, 0.2))), 7)
    # the buffers: a stock out of the beam, a round iron head
    for sx in (-1, 1):
        x = sx * 0.34
        p0 = v3((x, yb - 0.07, BEAM_Z))
        fd.add(Cylinder(p0 + v3((0, 0.005, 0)), 0.06, 0.012, rr=0.004, R=rot_from_axes(z_axis=(0, 1, 0))), 0.004, 6)
        fd.add(RoundCone(p0, p0 + v3((0, -0.1, 0)), 0.036, 0.034), 0.006, 6)
        fd.add(Ellipsoid(p0 + v3((0, -0.12, 0)), (0.07, 0.022, 0.07)), 0.008, 6)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            fd.add(Sphere(p0 + v3((math.cos(a) * 0.045, 0.0, math.sin(a) * 0.045)), 0.008), 0.002, 6)
    return fd


# ---------------------------------------------------------------------------------------------- the boiler and its valve
def boiler_field():
    """A small vertical boiler: black iron (8) riveted in courses (rivets 8), brass bands, steam dome and whistle (6), a
    steel gauge face (7) in a brass rim with a black needle (8), the firebox door hinged open (8), a tall stack with a
    flared cap; the steam pipe along the ground to the valve standpipe (iron 8, brass flanges 6)."""
    fd = Field("Boiler")
    b = BOILER
    g0 = ground_height(b[0], b[1]) - 0.03
    R = BOILER_R
    # the firebox: a wider drum at the foot, on a plinth
    fd.add(Cylinder(v3((b[0], b[1], g0 + 0.04)), R + 0.05, 0.08, rr=0.012), 0.0, 8)
    fd.add(Cylinder(v3((b[0], b[1], g0 + 0.17)), R + 0.025, 0.2, rr=0.016), 0.01, 8)
    fd.add(Cylinder(v3((b[0], b[1], (g0 + 0.25 + BOILER_TOP) / 2)), R, BOILER_TOP - g0 - 0.25, rr=0.02), 0.012, 8)
    fd.add(Ellipsoid(v3((b[0], b[1], BOILER_TOP - 0.02)), (R, R, 0.08)), 0.02, 8)                       # the domed crown
    # the firebox door opening (toward the front-right: the camera), the door swung open beside it
    fwd = norm(v3((-0.55, -1.0, 0.0)))
    side = norm(np.cross(v3((0, 0, 1)), fwd))
    dc = v3((b[0], b[1], g0 + 0.17)) + fwd * (R + 0.02)
    fd.sub(Ellipsoid(dc, (0.075, 0.075, 0.06), R=np.stack([side, v3((0, 0, 1)), fwd], 1)), 0.008)
    fd.add(Torus(dc - fwd * 0.004, 0.072, 0.011, R=rot_from_axes(z_axis=fwd)), 0.004, 8)
    hinge = dc + side * 0.078
    dn = norm(fwd * 0.7 + side * 0.7)
    fd.add(Cylinder(hinge + dn * 0.07, 0.068, 0.014, rr=0.005, R=rot_from_axes(z_axis=norm(np.cross(dn, v3((0, 0, 1)))))), 0.004, 8)
    # rivet rows round the seams, brass bands
    for zz in (g0 + 0.27, 0.48, BOILER_TOP - 0.06):
        fd.add(Torus(v3((b[0], b[1], zz)), R + 0.002, 0.008), 0.004, 6 if zz == 0.48 else 8)
        if zz != 0.48:
            for k in range(20):
                a = 2 * math.pi * k / 20
                fd.add(Sphere(v3((b[0] + math.cos(a) * (R + 0.006), b[1] + math.sin(a) * (R + 0.006), zz + 0.018)), 0.0065), 0.002, 8)
    # the stack: up from the crown, a flared cap
    top = v3((b[0] + 0.03, b[1] + 0.03, BOILER_TOP + 0.05))
    stack_top = top + v3((0, 0, 0.42))
    fd.add(RoundCone(top, stack_top, 0.048, 0.044), 0.012, 8)
    fd.add(RoundCone(stack_top - v3((0, 0, 0.01)), stack_top + v3((0, 0, 0.07)), 0.05, 0.075), 0.01, 8)
    fd.sub(Cylinder(stack_top + v3((0, 0, 0.07)), 0.055, 0.05), 0.004)
    fd.add(Torus(top + v3((0, 0, 0.14)), 0.05, 0.007), 0.003, 6)
    # the brass steam dome and whistle on the crown's front
    dome = v3((b[0] - 0.06, b[1] - 0.06, BOILER_TOP + 0.03))
    fd.add(RoundCone(dome, dome + v3((0, 0, 0.07)), 0.05, 0.044), 0.012, 6)
    fd.add(Sphere(dome + v3((0, 0, 0.07)), 0.046), 0.01, 6)
    w = dome + v3((0, 0, 0.12))
    fd.add(RoundCone(w, w + v3((0, 0, 0.09)), 0.016, 0.019), 0.006, 6)
    fd.add(Ellipsoid(w + v3((0, 0, 0.1)), (0.022, 0.022, 0.012)), 0.004, 6)
    # the pressure gauge on the barrel's front
    gc = v3((b[0], b[1], 0.62)) + fwd * (R + 0.012)
    fd.add(Cylinder(gc, 0.052, 0.024, rr=0.008, R=rot_from_axes(z_axis=fwd)), 0.006, 6)
    fd.add(Cylinder(gc + fwd * 0.012, 0.042, 0.004, rr=0.001, R=rot_from_axes(z_axis=fwd)), 0.0, 7)
    fd.add(RoundCone(gc + fwd * 0.016, gc + fwd * 0.016 + norm(side * 0.6 + v3((0, 0, 0.8))) * 0.034, 0.004, 0.0025), 0.0, 8)
    # the steam pipe: out of the barrel's foot, down along the cinders and the ballast's edge to the standpipe
    v = VALVE
    p0 = v3((b[0], b[1], 0.36)) + norm(v3((-0.3, -1.0, 0))) * (R + 0.01)
    gv = ground_height(0.84, -0.1)
    pts = [p0, p0 + v3((-0.03, -0.1, -0.12)), v3((0.82, -0.02, gv + 0.04)), v3((0.8, -0.42, ground_height(0.8, -0.42) + 0.04)),
           v3((v[0] + 0.04, v[1] - 0.02, BALLAST_Z + 0.04))]
    fd.add(Chain(pts, [0.03] * len(pts), k=0.03), 0.01, 8)
    for i in range(1, len(pts) - 1):
        d = norm(pts[i + 1] - pts[i])
        fd.add(Torus(lerp(pts[i], pts[i + 1], 0.5), 0.034, 0.009, R=rot_from_axes(z_axis=d)), 0.003, 6)
    # the standpipe: up from the bend, a valve body, a brass gland under the striker cap (the cap: Valve)
    vb = v3((v[0], v[1], BALLAST_Z + 0.02))
    fd.add(RoundCone(vb, vb + v3((0, 0, VALVE_TOP - 0.06 - vb[2])), 0.034, 0.03), 0.012, 8)
    fd.add(Sphere(vb + v3((0, 0, 0.06)), 0.058), 0.014, 8)
    fd.add(Cylinder(v3((v[0], v[1], VALVE_TOP - 0.06)), 0.04, 0.03, rr=0.006), 0.004, 6)
    fd.add(Cylinder(vb + v3((0, 0, 0.01)), 0.06, 0.02, rr=0.006), 0.004, 8)
    return fd


def valve_field():
    """The striker cap: a big red-painted iron mushroom (5) on a steel stem (6) on top of the standpipe."""
    fd = Field("Valve")
    c = valve_point()
    fd.add(RoundCone(c - v3((0, 0, 0.07)), c - v3((0, 0, 0.03)), 0.02, 0.02), 0.0, 6)
    fd.add(Inter(Ellipsoid(c - v3((0, 0, 0.03)), (0.085, 0.085, 0.045)), Plane(c - v3((0, 0, 0.034)), (0, 0, -1)), 0.006), 0.006, 5)
    return fd


def fire_field():
    """The fire inside the open firebox door (its own glowing mesh)."""
    fd = Field("Fire")
    b = BOILER
    g0 = ground_height(b[0], b[1]) - 0.03
    fwd = norm(v3((-0.55, -1.0, 0.0)))
    dc = v3((b[0], b[1], g0 + 0.17)) + fwd * (BOILER_R - 0.01)
    fd.add(Ellipsoid(dc, (0.07, 0.07, 0.056), R=rot_from_axes(z_axis=fwd), disp=lambda P: F(0.006) * NOISE(P * F(18)), disp_amp=0.008), 0.0)
    return fd


def coal_field():
    """A heap of coal behind the boiler, and lumps spilt by the firebox door (charcoal)."""
    fd = Field("Coal")
    rs = np.random.RandomState(31)
    c = COAL
    g = ground_height(c[0], c[1])
    fd.add(Ellipsoid(v3((c[0], c[1], g - 0.02)), (0.2, 0.16, 0.12)), 0.0)
    for k in range(22):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0, 1) ** 0.6
        p = v3((c[0] + math.cos(a) * r * 0.2, c[1] + math.sin(a) * r * 0.16, 0))
        p[2] = g - 0.02 + 0.12 * math.sqrt(max(0.0, 1 - r * r)) + 0.005
        fd.add(Stone(p, rs.uniform(0.026, 0.04), seed=500 + k, squash=(1, 1, 0.75), noise=0.12), 0.006)
    fwd = norm(v3((-0.55, -1.0, 0.0)))
    for k in range(5):
        p = BOILER + fwd * rs.uniform(0.26, 0.4) + v3((rs.uniform(-0.08, 0.08), rs.uniform(-0.06, 0.06), 0))
        p[2] = ground_height(p[0], p[1]) + 0.012
        fd.add(Stone(p, rs.uniform(0.022, 0.032), seed=540 + k, squash=(1, 1, 0.7), noise=0.12), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the signal lamp, the stack
def lamp_field():
    """An iron post (label 8) on a stone foot (the stone: 5), a ladder-rung cross-arm, the lamp: a black iron case with a
    hood and a little chimney, a round red lens in a brass bezel (6) facing the robots, a smaller white one at its side."""
    fd = Field("Lamp")
    p = LAMP
    g = ground_height(p[0], p[1])
    top = v3((p[0], p[1], LAMP_C[2] - 0.12))
    fd.add(RoundCone(v3((p[0], p[1], g - 0.05)), top, 0.03, 0.026), 0.0, 8)
    fd.add(Cylinder(v3((p[0], p[1], g + 0.03)), 0.075, 0.08, rr=0.015, disp=_chip, disp_amp=0.003), 0.008, 5)
    fd.add(RoundBox(v3((p[0], p[1], g + 0.6)), (0.09, 0.012, 0.012), 0.005), 0.006, 8)
    c = LAMP_C
    fd.add(RoundBox(c, (0.075, 0.07, 0.1), 0.02), 0.01, 8)
    fd.add(RoundBox(c + v3((0, 0, 0.115)), (0.09, 0.085, 0.014), 0.008), 0.006, 8)
    fd.add(RoundCone(c + v3((0, 0, 0.12)), c + v3((0, 0, 0.2)), 0.024, 0.02), 0.006, 8)
    fd.add(Cylinder(c + v3((0, 0, 0.205)), 0.034, 0.012, rr=0.005), 0.004, 8)
    fd.add(Torus(c + v3((0, -0.074, 0.0)), 0.048, 0.008, R=rot_from_axes(z_axis=(0, 1, 0))), 0.004, 6)
    fd.add(Torus(c + v3((-0.079, 0.0, 0.0)), 0.03, 0.006, R=rot_from_axes(z_axis=(1, 0, 0))), 0.004, 6)
    fd.add(Torus(c + v3((0, 0.0, 0.25)), 0.02, 0.005, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, 8)     # the carrying ring
    return fd


def lens_field():
    fd = Field("Lens")
    c = LAMP_C
    fd.add(Ellipsoid(c + v3((0, -0.07, 0.0)), (0.042, 0.016, 0.042)), 0.0)
    return fd


def lens2_field():
    fd = Field("Lens2")
    c = LAMP_C
    fd.add(Ellipsoid(c + v3((-0.075, 0.0, 0.0)), (0.012, 0.025, 0.025)), 0.0)
    return fd


def stack_field():
    """Spare sleepers stacked crosswise (creosoted timber: grain along Y, 0, or X, 10)."""
    fd = Field("Stack")
    rs = np.random.RandomState(5)
    c = STACK
    g = ground_height(c[0], c[1]) - 0.01
    grain = lambda P: F(0.002) * NOISE(P * F(55))
    h = 0.034
    for layer in range(3):
        z = g + h + layer * (2 * h - 0.004)
        along_y = layer % 2 == 0
        for k in (-1, 1):
            off = v3((k * 0.085, 0, 0)) if along_y else v3((0, k * 0.1, 0))
            half = (0.07, 0.26, h) if along_y else (0.24, 0.07, h)
            fd.add(RoundBox(c + off + v3((rs.uniform(-0.01, 0.01), rs.uniform(-0.01, 0.01), z - c[2])), half, 0.01,
                            R=euler(0, 0, rs.uniform(-0.06, 0.06)), disp=grain, disp_amp=0.002), 0.0, 0 if along_y else 10)
    return fd


# ---------------------------------------------------------------------------------------------- the hero ring
def _blocked(c, pad=0.0):
    x, y = c[0], c[1]
    if abs(x) < BED_W + 0.14 + pad and y < BED_BACK + 0.1 + pad:
        return True
    for p, r in ((BOILER, BOILER_R + 0.1), (COAL, 0.24), (LAMP, 0.1), (STACK, 0.3), (VALVE, 0.12)):
        if math.hypot(x - p[0], y - p[1]) < r + pad:
            return True
    if abs(x) < 0.62 + pad and BUFFER_Y - 0.1 < y < BUFFER_Y + 0.5 + pad:
        return True
    return False


def bed_height(x, y):
    """The top of the ground or the ballast bed at (x, y)."""
    over = max(0.0, abs(x) - BED_W, y - BED_BACK)
    zb = BALLAST_Z - over / 1.1 if math.hypot(x, y) < 1.27 else -1.0
    return max(ground_height(x, y), zb)


def glow_spots():
    """The ring's lamp glasses: evenly round it where the rails and the props leave room (about twelve)."""
    out = []
    for i in range(24):
        a = i * 2 * math.pi / 24 + math.radians(7.5)
        x, y = math.cos(a) * RING_R, math.sin(a) * RING_R
        if abs(abs(x) - RAIL_X) < 0.12 and y < 0:
            continue                                        # (the rails cross the ring at the front)
        if any(math.hypot(x - p[0], y - p[1]) < r for p, r in ((BOILER, BOILER_R + 0.12), (COAL, 0.26), (STACK, 0.32), (LAMP, 0.12))):
            continue
        if out and min(math.hypot(x - q[0], y - q[1]) for q in out) < 0.5:
            continue
        out.append(v3((x, y, bed_height(x, y) + 0.004)))
    return out


def glowmarks_field():
    fd = Field("Glowmarks")
    for p in glow_spots():
        fd.add(Ellipsoid(p, (0.032, 0.032, 0.016)), 0.0)
    return fd


def cups_field():
    """Brass cups round the lamp glasses."""
    fd = Field("Cups")
    for p in glow_spots():
        fd.add(Torus(p + v3((0, 0, -0.002)), 0.036, 0.009), 0.0)
        fd.add(Cylinder(p + v3((0, 0, -0.016)), 0.044, 0.014, rr=0.005), 0.004)
    return fd


def cinders_field():
    """Lumps of coal and cinders scattered on the earth (charcoal)."""
    fd = Field("Cinders")
    rs = np.random.RandomState(73)
    n, tries = 0, 0
    while n < 12 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.8, 1.24)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02) or any(np.linalg.norm(p[:2] - g[:2]) < 0.09 for g in glow_spots()):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.008
        fd.add(Stone(p, rs.uniform(0.018, 0.03), seed=900 + n, squash=(1, 1, 0.6), noise=0.1), 0.0)
        n += 1
    return fd


def grass_geometry(seed=97):
    old = kb._blocked
    kb._blocked = lambda c, pad=0.0: _blocked(c, pad) or math.hypot(c[0], c[1]) < 1.0 + pad or \
        any(math.hypot(c[0] - g[0], c[1] - g[1]) < 0.1 + pad for g in glow_spots())
    try:
        return kb.grass_geometry(seed)
    finally:
        kb._blocked = old


def flower_geometry(seed=99):
    return []


def fields():
    return [("Ground", ground_field(), 0.008), ("Ballast", ballast_field(), 0.0045), ("Sleepers", sleepers_field(), 0.0036),
            ("Rails", rails_field(), 0.0024), ("Buffer", buffer_field(), 0.0032), ("Boiler", boiler_field(), 0.0026),
            ("Valve", valve_field(), 0.002), ("Fire", fire_field(), 0.003), ("Coal", coal_field(), 0.003),
            ("Lamp", lamp_field(), 0.0024), ("Lens", lens_field(), 0.002), ("Lens2", lens2_field(), 0.002),
            ("Stack", stack_field(), 0.0034), ("Glowmarks", glowmarks_field(), 0.0025), ("Cups", cups_field(), 0.002),
            ("Cinders", cinders_field(), 0.004)]


REGION_PARTS = ("Ground", "Sleepers", "Buffer", "Boiler", "Valve", "Lamp", "Stack")
LOW_TARGETS = {"Ground": 1400, "Ballast": 3200, "Sleepers": 1400, "Rails": 1600, "Buffer": 1300, "Boiler": 2600, "Valve": 300,
               "Fire": 120, "Coal": 900, "Lamp": 800, "Lens": 80, "Lens2": 60, "Stack": 700, "Glowmarks": 300, "Cups": 400,
               "Cinders": 300}
CREOSOTE = {"wood": (0.32, 0.22, 0.15), "wood2": (0.2, 0.13, 0.085)}
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_YardGround", "dirt_label": 5}),
                 "Ballast": ("stone", {"name": "HQ_Ballast", "scale": 0.35}),
                 "Sleepers": ("siege", dict(CREOSOTE, name="HQ_Sleepers", metal="iron")),
                 "Stack": ("siege", dict(CREOSOTE, name="HQ_SleeperStack", metal="iron")),
                 "Rails": ("iron", {"name": "HQ_Rails", "col": {"base": (0.24, 0.22, 0.21), "hi": (0.72, 0.72, 0.74),
                                                               "dark": (0.08, 0.07, 0.07), "rust": (0.5, 0.25, 0.1)}}),
                 "Buffer": ("siege", {"name": "HQ_BufferStop", "wood": (0.46, 0.33, 0.2), "wood2": (0.34, 0.23, 0.13),
                                      "red": (0.74, 0.12, 0.07), "blue": (0.93, 0.91, 0.86), "metal": "iron"}),
                 "Boiler": ("armory", {"name": "HQ_Boiler"}),
                 "Valve": ("siege", {"name": "HQ_ValveCap", "red": (0.8, 0.1, 0.06), "metal": "iron"}),
                 "Coal": ("charcoal", {"name": "HQ_Coal"}),
                 "Cinders": ("charcoal", {"name": "HQ_Cinders"}),
                 "Lamp": ("armory", {"name": "HQ_SignalLamp"}),
                 "Cups": ("bronze", {"name": "HQ_RingBrass", "base": (0.8, 0.55, 0.22), "hi": (1.0, 0.9, 0.56),
                                     "dark": (0.38, 0.24, 0.08), "patina": (0.42, 0.44, 0.24)})}
GLOW = {"Glowmarks": ((1.0, 0.56, 0.16), 1.0, 0.5), "Fire": ((1.0, 0.42, 0.08), 1.2, 0.5), "Lens": ((1.0, 0.12, 0.06), 1.2, 0.5),
        "Lens2": ((1.0, 0.86, 0.6), 0.9, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return (n.z > 0.55 and 1.12 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
            and not _blocked((c.x, c.y), -0.05))
