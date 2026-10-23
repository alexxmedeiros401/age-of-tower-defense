"""EMP Tower base: a fortified electronics post on the edge of a lawn. A round pad of cast concrete (a yellow line painted
round its rim, an expansion joint across it, a few oil stains) rises from the grass; nothing on it stands proud but the
bolts of a junction box at its edge (the emitter, the case and he sweep out to ~0.9 as the tower turns). Round its foot
on the lawn: before him a low wall of sandbags in two arcs (a gap in the middle), behind him on his right a diesel
generator on skids (olive, louvred, an exhaust stack, a control panel, a jerrycan beside it) cabled to the junction
box, behind him on his left a stack of rugged equipment cases (black and olive, latches, a stencilled mark), behind
him a tripod mast with a yagi antenna, on his left a cable reel. (Distance fields + direct low-poly geometry for the grass
and the dandelions.)"""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
import emp as _e
from crossbowman_base import _bloom

GROUND_R = 1.34
GROUND_TOP = 0.1
PAD_R = 0.99                   # the concrete pad (he, the emitter and the case sweep out to ~0.9 of it)
TOP_Z = 0.18                   # the pad's top = where he stands
STAND = v3((-_e.YAW_PIVOT[0], -_e.YAW_PIVOT[1], TOP_Z))
Z = v3((0.0, 0.0, 1.0))
PROP_R = 1.16                  # the props' ring, on the lawn
GEN_A = math.radians(138.0)    # the generator: behind him, on his right (the camera's left)
JUNC_A = math.radians(118.0)   # its junction box on the pad's edge
CASES_A = math.radians(52.0)   # the equipment cases: behind him on his left
ANT_A = math.radians(92.0)     # the antenna mast: behind him
REEL_A = math.radians(4.0)     # the cable reel: on his left
CAN_A = math.radians(160.0)    # the jerrycan, beside the generator
BAGS = ((-168.0, -104.0), (-76.0, -16.0))      # the sandbag arcs before him (deg)
BAG = (0.15, 0.085, 0.05)
BAG_R = 1.17


def ring_pt(a, r):
    return v3((math.cos(a) * r, math.sin(a) * r, 0.0))


def ring_frame(a):
    """At angle a on the ring: outward and along (counter-clockwise)."""
    return v3((math.cos(a), math.sin(a), 0.0)), v3((-math.sin(a), math.cos(a), 0.0))


def ground_height(x, y):
    r = math.hypot(x, y)
    if r < PAD_R:
        return TOP_Z
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


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


def pad_field():
    """Cast concrete (label 0): the round pad with a chamfered rim, a yellow line painted round its rim (5), an expansion
    joint across it, oil stains (7), a few chips out of its edge."""
    fd = Field("Pad")
    h = TOP_Z - (GROUND_TOP - 0.06)
    fd.add(Cylinder(v3((0, 0, GROUND_TOP - 0.06 + h / 2)), PAD_R, h, rr=0.03,
                    disp=lambda P: F(0.0012) * NOISE(P * F(30)) + F(0.002) * NOISE(P * F(6)) * smoothstep(PAD_R - 0.05, PAD_R, np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)),
                    disp_amp=0.004), 0.0)
    # the expansion joint across it (front to back, under his right side) and a cross joint behind him
    fd.sub(RoundBox(v3((-0.36, 0.0, TOP_Z)), (0.004, PAD_R, 0.006), 0.002), 0.002)
    fd.sub(RoundBox(v3((0.0, 0.62, TOP_Z)), (PAD_R, 0.004, 0.006), 0.002), 0.002)
    rr = lambda P: np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
    fd.paint(Func(lambda P: np.maximum(np.abs(rr(P) - F(PAD_R - 0.065)) - F(0.022), F(TOP_Z - 0.02) - P[:, 2]),
                  (-1.1, -1.1, 0.0), (1.1, 1.1, 0.3)), 5)
    # black hazard chevrons on the yellow line before him (the camera's side)
    def chev(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        u = a * F(PAD_R - 0.065) + (rr(P) - F(PAD_R - 0.065)) * F(0.8)
        st = np.abs(np.mod(u, F(0.09)) - F(0.045)) - F(0.02)
        front = np.abs(a + F(math.pi / 2)) - F(0.5)
        return np.maximum(np.maximum(st, front), np.maximum(np.abs(rr(P) - F(PAD_R - 0.065)) - F(0.022), F(TOP_Z - 0.02) - P[:, 2]))
    fd.paint(Func(chev, (-1.1, -1.1, 0.0), (1.1, 1.1, 0.3)), 6)
    rs = np.random.RandomState(7)
    for k in range(3):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.3, 0.75)
        fd.paint(Ellipsoid(ring_pt(a, r) + Z * TOP_Z, (rs.uniform(0.08, 0.13), rs.uniform(0.05, 0.09), 0.03), R=euler(0, 0, rs.uniform(0, 3))), 7)
    for k in range(5):                                                        # chips out of the rim
        a = rs.uniform(0, 2 * math.pi)
        fd.sub(Sphere(ring_pt(a, PAD_R + 0.01) + Z * (TOP_Z - 0.01), rs.uniform(0.018, 0.03)), 0.006)
    return fd


def bag_specs(seed=5):
    """(centre, yaw, half extents, seed) of every sandbag: two courses in two arcs before him."""
    rs = np.random.RandomState(seed)
    out = []
    for a0, a1 in BAGS:
        for course in range(2):
            rr = BAG_R - 0.01 * course
            span = math.radians(a1 - a0) - (0.08 if course else 0.0)
            n = max(1, int(span * rr / (2 * BAG[0] + 0.01)))
            for k in range(n):
                a = math.radians(a0) + (0.04 if course else 0.0) + span * (k + 0.5) / n
                z = GROUND_TOP + BAG[2] * 0.85 + course * (2 * BAG[2] * 0.8) + rs.uniform(-0.004, 0.006)
                c = v3((math.cos(a) * (rr + rs.uniform(-0.01, 0.01)), math.sin(a) * (rr + rs.uniform(-0.01, 0.01)), z))
                yaw = a + math.pi / 2 + rs.uniform(-0.08, 0.08)
                h = (BAG[0] * rs.uniform(0.92, 1.04), BAG[1] * rs.uniform(0.92, 1.05), BAG[2] * rs.uniform(0.9, 1.05))
                out.append((c, yaw, h, int(rs.randint(1 << 20))))
    return out


def sandbags_field():
    """Plump sandbags (0), their tied ends pinched (twine, 6), a stencilled mark on a few (5)."""
    fd = Field("Sandbags")
    lumpy = lambda P: F(0.004) * NOISE(P * F(12)) + F(0.0015) * NOISE(P * F(40))
    for c, yaw, h, sd in bag_specs():
        R = euler(0.03 * math.sin(sd), 0.04 * math.cos(sd), yaw)
        fd.add(RoundBox(c, h, h[2] * 0.95, R=R, disp=lumpy, disp_amp=0.006), 0.012, 0)
        e = c + R @ v3((h[0] + 0.012, 0.0, 0.0))
        fd.add(Ellipsoid(e, (0.022, 0.028, 0.022), R=R), 0.012, 0)
        fd.add(Torus(e - R @ v3((0.006, 0, 0)), 0.017, 0.0045, R=R @ rot_from_axes(z_axis=(1, 0, 0))), 0.002, 6)
        if sd % 4 == 0:
            fd.paint(Inter(Shell(Ellipsoid(c + v3((0, 0, h[2] * 0.4)), (0.055, 0.04, h[2] * 0.7), R=R), 0.0, 0.03),
                           Plane(c + v3((0, 0, h[2] * 0.5)), (0, 0, -1))), 5)
    return fd


# ---------------------------------------------------------------------------------------------- the generator
def generator_into(fd):
    """A diesel generator on skids (olive 0): louvred sides, a black control panel with a red stop button and a gauge,
    an exhaust stack with a rain cap (gunmetal 5), lifting eyes, a hazard label (13, 8); a jerrycan beside it (olive)."""
    out, along = ring_frame(GEN_A)
    c = ring_pt(GEN_A, PROP_R)
    g = ground_height(c[0], c[1]) - 0.006
    Rb = np.stack([along, out, Z], axis=1)
    for e in (-1, 1):                                                          # the skids
        fd.add(RoundBox(c + out * (e * 0.09) + Z * (g + 0.018), (0.2, 0.022, 0.018), 0.006, R=Rb), 0.0, 5)
    bc = c + Z * (g + 0.17)
    fd.add(RoundBox(bc, (0.19, 0.13, 0.135), 0.022, R=Rb, disp=lambda P: F(0.0006) * NOISE(P * F(40)), disp_amp=0.001), 0.006, 0)
    fd.add(RoundBox(bc + Z * 0.14, (0.17, 0.11, 0.012), 0.01, R=Rb), 0.004, 0)                       # the roof's lip
    # louvres along both long sides
    for e in (-1, 1):
        for k in range(6):
            lc = bc + out * (e * 0.132) + along * (-0.12 + 0.048 * k) + Z * 0.01
            fd.sub(RoundBox(lc, (0.008, 0.012, 0.075), 0.004, R=Rb), 0.003)
    # the control panel on the end toward the pad
    pe = bc - along * 0.192
    Rp = np.stack([out, -along, Z], axis=1)
    fd.add(RoundBox(pe + Z * 0.02, (0.075, 0.008, 0.06), 0.006, R=Rb @ euler(0, 0, 0)), 0.003, 8)
    fd.add(Cylinder(pe - along * 0.01 + Z * 0.05 + out * 0.035, 0.016, 0.014, rr=0.004, R=rot_from_axes(z_axis=-along)), 0.002, 12)
    fd.add(Cylinder(pe - along * 0.008 + Z * 0.04 - out * 0.03, 0.022, 0.01, rr=0.003, R=rot_from_axes(z_axis=-along)), 0.002, 7)
    # the hazard label on its outer side
    lc = bc + out * 0.135 + Z * 0.05 + along * 0.12
    fd.paint(Sphere(lc, 0.035), 13)
    # the exhaust stack and lifting eyes
    ex = bc + Z * 0.15 + along * 0.11 + out * 0.04
    fd.add(Cylinder(ex + Z * 0.08, 0.022, 0.16, rr=0.006), 0.004, 5)
    fd.add(RoundBox(ex + Z * 0.17, (0.035, 0.035, 0.006), 0.004, R=Rb @ euler(0.4, 0, 0)), 0.003, 5)
    for e in (-1, 1):
        fd.add(Torus(bc + Z * 0.165 + along * (e * 0.12) - out * 0.04, 0.016, 0.005, R=rot_from_axes(z_axis=out)), 0.002, 5)
    fd.add(Cylinder(bc + Z * 0.16 - along * 0.06 - out * 0.05, 0.02, 0.02, rr=0.005), 0.003, 12)        # the fuel cap
    # a jerrycan beside it
    out2, along2 = ring_frame(CAN_A)
    jc = ring_pt(CAN_A, PROP_R + 0.02)
    jg = ground_height(jc[0], jc[1])
    Rj = np.stack([out2, along2, Z], axis=1)
    fd.add(RoundBox(jc + Z * (jg + 0.115), (0.06, 0.03, 0.11), 0.014, R=Rj), 0.0, 0)
    fd.sub(RoundBox(jc + Z * (jg + 0.13) + along2 * 0.032, (0.03, 0.006, 0.05), 0.01, R=Rj @ euler(0, 0, 0)), 0.004)
    for e in (-1, 1):
        fd.sub(RoundBox(jc + Z * (jg + 0.13) + along2 * (e * 0.032) + out2 * 0.02, (0.012, 0.006, 0.05), 0.006, R=Rj), 0.003)
    fd.add(Chain([jc + Z * (jg + 0.2) - out2 * 0.04, jc + Z * (jg + 0.25) - out2 * 0.02, jc + Z * (jg + 0.25) + out2 * 0.02,
                  jc + Z * (jg + 0.2) + out2 * 0.03], [0.008] * 4, k=0.004), 0.004, 0)          # its handles
    fd.add(Cylinder(jc + Z * (jg + 0.235) + out2 * 0.045, 0.014, 0.03, rr=0.004, R=rot_from_axes(z_axis=norm(out2 + Z))), 0.003, 5)
    return pe


def junction_into(fd, gen_panel):
    """A junction box (gunmetal 5, a hazard label 13) on the pad's rim, and the generator's black cable (8) to it."""
    jo, ja = ring_frame(JUNC_A)
    jc = ring_pt(JUNC_A, PAD_R + 0.035)
    jg = GROUND_TOP + 0.02
    Rj = np.stack([ja, jo, Z], axis=1)
    fd.add(RoundBox(jc + Z * (jg + 0.06), (0.07, 0.045, 0.065), 0.01, R=Rj), 0.0, 5)
    fd.add(RoundBox(jc + Z * (jg + 0.128), (0.074, 0.05, 0.006), 0.004, R=Rj), 0.003, 5)
    fd.paint(Sphere(jc + jo * 0.045 + Z * (jg + 0.07), 0.028), 13)
    for e in (-1, 1):
        fd.add(Sphere(jc + ja * (e * 0.055) + jo * 0.035 + Z * (jg + 0.13), 0.007), 0.002, 7)
    start = jc + jo * 0.045 + Z * (jg + 0.03)
    end = gen_panel - ring_frame(GEN_A)[1] * 0.02 + Z * (-0.06)
    mid = lerp(start, end, 0.5)
    mid[2] = ground_height(mid[0], mid[1]) + 0.016
    pts = [start, start + jo * 0.05 + Z * -0.02, mid + v3((0.03, 0.04, 0)), end - Z * 0.07 + ring_frame(GEN_A)[1] * -0.03, end]
    for p in pts[1:-1]:
        p[2] = max(p[2], ground_height(p[0], p[1]) + 0.016)
    fd.add(Chain(pts, [0.016] * len(pts), k=0.012), 0.004, 8)


def cases_into(fd):
    """A stack of rugged equipment cases: a long black one (8) on the lawn, an olive one (0) on it, a small black one
    standing beside them; moulded ribs, latches and handles (5), a stencilled mark (13)."""
    out, along = ring_frame(CASES_A)
    c = ring_pt(CASES_A, PROP_R + 0.01)
    g = ground_height(c[0], c[1]) - 0.004
    Rb = np.stack([along, out, Z], axis=1)
    def case(cc, half, lab, R):
        fd.add(RoundBox(cc, half, 0.016, R=R), 0.004, lab)
        fd.sub(RoundBox(cc + R @ v3((0, 0, half[2] * 0.25)), (half[0] + 0.01, half[1] + 0.01, 0.003), 0.002, R=R), 0.002)    # the lid's seam
        for e in (-1, 1):
            fd.add(RoundBox(cc + R @ v3((e * half[0] * 0.55, -(half[1] + 0.004), half[2] * 0.25)), (0.018, 0.006, 0.022), 0.004, R=R), 0.002, 5)  # latches
        fd.add(Chain([cc + R @ v3((-0.04, -(half[1] + 0.002), half[2] * 0.6)), cc + R @ v3((-0.03, -(half[1] + 0.016), half[2] * 0.62)),
                      cc + R @ v3((0.03, -(half[1] + 0.016), half[2] * 0.62)), cc + R @ v3((0.04, -(half[1] + 0.002), half[2] * 0.6))],
                     [0.007] * 4, k=0.003), 0.003, 5)
    case(c + Z * (g + 0.07), (0.2, 0.13, 0.07), 8, Rb)
    R2 = Rb @ euler(0, 0, 0.12)
    case(c + Z * (g + 0.2) + along * 0.02, (0.16, 0.11, 0.06), 0, R2)
    fd.paint(RoundBox(c + Z * (g + 0.205) + along * 0.02 - out * 0.112, (0.06, 0.02, 0.025), 0.004, R=R2), 13)
    c3 = c + along * -0.27 + out * 0.03
    g3 = ground_height(c3[0], c3[1]) - 0.004
    case(c3 + Z * (g3 + 0.1), (0.07, 0.08, 0.1), 8, Rb @ euler(0, 0, -0.3))


def antenna_into(fd):
    """A tripod mast (gunmetal 5) with a yagi antenna on top (bright steel 7, black insulators 8), guyed by a cable."""
    out, along = ring_frame(ANT_A)
    c = ring_pt(ANT_A, PROP_R + 0.04)
    g = ground_height(c[0], c[1])
    hub = c + Z * (g + 0.32)
    for k in range(3):
        a = ANT_A + math.pi / 6 + 2 * math.pi * k / 3
        d = v3((math.cos(a), math.sin(a), 0))
        ft = c + d * 0.17
        ft[2] = ground_height(ft[0], ft[1]) + 0.008
        fd.add(RoundCone(hub, ft, 0.012, 0.011), 0.004, 5)
        fd.add(Sphere(ft, 0.016), 0.003, 8)
    top = c + Z * (g + 1.42)
    fd.add(RoundCone(hub - Z * 0.02, hub + Z * 0.55, 0.022, 0.02), 0.004, 5)
    fd.add(RoundCone(hub + Z * 0.55, top, 0.016, 0.013), 0.004, 5)
    for zz in (0.02, 0.55):
        fd.add(Cylinder(hub + Z * zz, 0.03, 0.03, rr=0.008), 0.004, 8)
    # the yagi: a boom across the top, elements across it
    boom_d = norm(-out + Z * 0.15)
    b0, b1 = top - boom_d * 0.22, top + boom_d * 0.3
    fd.add(RoundCone(b0, b1, 0.01, 0.01), 0.003, 7)
    fd.add(RoundBox(top, (0.03, 0.03, 0.03), 0.008, R=rot_from_axes(y_axis=boom_d, z_axis=Z)), 0.004, 8)
    for k in range(6):
        u = -0.18 + 0.09 * k
        L = 0.2 - 0.018 * k
        p = top + boom_d * u
        fd.add(RoundCone(p - along * L, p + along * L, 0.0065, 0.0065), 0.002, 7)
        fd.add(Sphere(p, 0.012), 0.002, 8)
    # a guy line from the hub's top to a peg (dark cord)
    peg = c + out * 0.36 + along * 0.12
    peg[2] = ground_height(peg[0], peg[1])
    fd.add(RoundCone(hub + Z * 0.55, peg + Z * 0.01, 0.004, 0.004), 0.002, 8)
    fd.add(RoundCone(peg + Z * 0.04, peg - Z * 0.02, 0.008, 0.006), 0.002, 5)


def reel_into(fd):
    """A cable reel standing on its rim: plywood cheeks (9), black cable (8) wound on it, its end trailing; a steel axle."""
    out, along = ring_frame(REEL_A)
    c = ring_pt(REEL_A, PROP_R + 0.02)
    g = ground_height(c[0], c[1])
    rc = c + Z * (g + 0.16)
    Rr = rot_from_axes(z_axis=along)
    for e in (-1, 1):
        fd.add(Cylinder(rc + along * (e * 0.08), 0.16, 0.022, rr=0.006, R=Rr), 0.0, 9)
        for k in range(4):
            a = 2 * math.pi * k / 4 + 0.3
            fd.sub(Sphere(rc + along * (e * 0.092) + (out * math.cos(a) + Z * math.sin(a)) * 0.1, 0.02), 0.004)
    fd.add(Cylinder(rc, 0.112, 0.14, rr=0.015, R=Rr, disp=lambda P: F(0.004) * np.abs(np.sin(((P - rc.astype(F)) @ along.astype(F)) * F(2 * math.pi / 0.034))), disp_amp=0.004), 0.004, 8)
    fd.add(Cylinder(rc, 0.03, 0.22, rr=0.006, R=Rr), 0.003, 7)
    st = rc + Z * 0.105 - along * 0.03
    pts = [st, rc + Z * 0.06 - out * 0.13 - along * 0.02, c - out * 0.22 + Z * (g + 0.02) + along * 0.04, c - out * 0.3 + along * 0.18 + Z * (g + 0.018)]
    fd.add(Chain(pts, [0.014] * len(pts), k=0.01), 0.004, 8)


def kit_field():
    fd = Field("Kit")
    pe = generator_into(fd)
    junction_into(fd, pe)
    cases_into(fd)
    antenna_into(fd)
    reel_into(fd)
    return fd


def _clear(p, pad=0.0):
    for a, rad in ((GEN_A, 0.3), (JUNC_A, 0.12), (CASES_A, 0.3), (ANT_A, 0.22), (REEL_A, 0.22), (CAN_A, 0.12)):
        if np.linalg.norm(p[:2] - ring_pt(a, PROP_R)[:2]) < rad + pad:
            return False
    a = math.degrees(math.atan2(p[1], p[0]))
    r = math.hypot(p[0], p[1])
    for a0, a1 in BAGS:
        if a0 - 4 < a < a1 + 4 and abs(r - BAG_R) < 0.13 + pad:
            return False
    return True


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(53)
    n, tries = 0, 0
    while n < 8 and tries < 800:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PAD_R + 0.05, GROUND_R - 0.05)
        p = ring_pt(a, r)
        if not _clear(p):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.01
        fd.add(Stone(p, rs.uniform(0.02, 0.032), seed=380 + n, squash=(1, 1, 0.6), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=61):
    """Tufts of lawn grass round the pad and between the props."""
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 30 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PAD_R + 0.03, GROUND_R - 0.03)
        c = ring_pt(a, r)
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.11 for t in tufts) or not _clear(c, 0.02):
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
            v, f, uv = _b.blade_mesh(root, d, rs.uniform(0.07, 0.13) * big, rs.uniform(0.03, 0.04), o * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)),
                                     segs=4, twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=67):
    """Dandelions in the lawn (swatch 1: yellow)."""
    rs = np.random.RandomState(seed)
    spots, tries = [], 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PAD_R + 0.06, GROUND_R - 0.06)
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
    return [("Ground", ground_field(), 0.008), ("Pad", pad_field(), 0.0045), ("Sandbags", sandbags_field(), 0.004),
            ("Kit", kit_field(), 0.0024), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Pad", "Sandbags", "Kit")
LOW_TARGETS = {"Ground": 1000, "Pad": 1800, "Sandbags": 3400, "Kit": 6600, "Pebbles": 200}
MAT_OVERRIDES = {"Pad": ("field_concrete", {"name": "HQ_EmpPad"}),
                 "Sandbags": ("sacking", {"name": "HQ_EmpSandbags", "base": (0.62, 0.55, 0.4), "dark": (0.42, 0.36, 0.25)}),
                 "Kit": ("fieldgun", dict(_e.MACHINE, name="HQ_EmpPostKit", wood=(0.62, 0.5, 0.34))),
                 "Pebbles": ("stone", {"name": "HQ_EmpPebble", "scale": 0.3})}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and PAD_R - 0.01 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
