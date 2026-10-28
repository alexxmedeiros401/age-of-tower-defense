"""Nova Artillery base: the Resistance's gun emplacement inside the robots' data center. A round floor of steel tread
plates (seams between them, bolts at their corners) inside a parapet of grey sandbags laid in
two staggered courses (a third in stretches); nothing on the floor stands proud of it: the gun turns over it. Round the
parapet the data center's floor of steel grating. In the gaps of the parapet, behind the gun: a rack of glowing amber
shells standing nose up in a salvaged crate, the field radio on an ammo crate (a gunmetal case with a teal canvas cover,
dials, a handset on its coiled cord, a whip antenna, its amber display), and a barricade of salvaged white robot plates
propped against the bags (dented, strapped, the biggest sprayed with the amber Resistance chevron); black cables from
the radio along the floor, and a thick one in from outside. The glows (the shells' cores, the radio's display and lamp)
are one emissive mesh (`Neon`)."""
import math
import numpy as np
from sdf import (Field, Sphere, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Ellipsoid, Chain, v3, norm,
                 rot_from_axes, smax, NOISE, F, euler)
from caveman import Inter, Shell
import nova_artillery as _g

GROUND_R = 1.45
TOP_Z = 0.1                    # the floor's top: where the gun and his feet rest
FLOOR_R = 1.19                 # the floor's edge (the parapet's inner foot)
STAND = v3((-_g.YAW_PIVOT[0], -_g.YAW_PIVOT[1], TOP_Z))
GRATE_Z = 0.07                 # the grating outside the parapet
BAG = (0.17, 0.09, 0.052)      # a sandbag's half length, depth, height
BAG_R = (1.31, 1.3, 1.29)      # the courses' middle radii
GAPS = {"shells": math.radians(28.0), "radio": math.radians(72.0), "banner": math.radians(102.0), "plates": math.radians(136.0)}
GAP_W = {"shells": 0.17, "radio": 0.17, "banner": 0.0, "plates": 0.0}
PLATE = 0.4                    # the floor plates' size
BASE_L, BLACK_L, AMB_L, WHITE_L, TEAL_L, GM_L, STEEL_L, GLASS_L, RUBBER_L, HAZ_L, BRASS_L = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14


def _angd(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def in_gap(a, extra=0.0):
    return any(_angd(a, g) < GAP_W[k] + extra for k, g in GAPS.items() if GAP_W[k] > 0)


def _radial(P):
    return np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)


def _cells(P, size):
    u = P[:, 0] / F(size) + F(0.5)
    v = P[:, 1] / F(size) + F(0.5)
    iu, iv = np.floor(u), np.floor(v)
    e = np.minimum(np.minimum(u - iu, F(1) - (u - iu)), np.minimum(v - iv, F(1) - (v - iv))) * F(size)
    rnd = np.abs(np.sin(iu * F(12.9898) + iv * F(78.233)) * F(43758.5453)) % F(1.0)
    return e, rnd, u - iu, v - iv


def _disc_sd(P, r, z0, z1, rr=0.012):
    dr = _radial(P) - F(r) + F(rr)
    dz = np.abs(P[:, 2] - F((z0 + z1) / 2)) - F((z1 - z0) / 2) + F(rr)
    return np.minimum(np.maximum(dr, dz), 0) + np.sqrt(np.maximum(dr, 0) ** 2 + np.maximum(dz, 0) ** 2) - F(rr)


def ground_field():
    """The data center's floor round the parapet: steel grating (0) in square panels, black (5) slots between its bars,
    gunmetal (9) panel frames; its outer edge bevelled down."""
    fd = Field("Ground")
    R = GROUND_R
    lo, hi = (-R - 0.05, -R - 0.05, -0.2), (R + 0.05, R + 0.05, 0.15)
    fd.add(Func(lambda P: _disc_sd(P, R, -0.1, GRATE_Z, rr=0.025), lo, hi,
                disp=lambda P: F(0.0005) * NOISE(P * F(40)), disp_amp=0.001), 0.0)
    def slots(P):
        e, rnd, fu, fv = _cells(P, 0.36)
        bars = np.abs(((P[:, 0] + P[:, 1] * F(0.0)) / F(0.045)) % F(1.0) - F(0.5)) * F(0.045) - F(0.011)
        d = np.maximum(np.maximum(-bars, F(0.03) - e), np.abs(P[:, 2] - F(GRATE_Z)) - F(0.008))
        return np.maximum(d, F(FLOOR_R + 0.04) - _radial(P))
    fd.sub(Func(slots, lo, hi), 0.0015)
    def frames(P):
        e, rnd, fu, fv = _cells(P, 0.36)
        return np.maximum(np.maximum(e - F(0.024), np.abs(P[:, 2] - F(GRATE_Z)) - F(0.02)), F(FLOOR_R) - _radial(P))
    fd.paint(Func(frames, lo, hi), GM_L)
    fd.paint(Func(lambda P: np.maximum(P[:, 2] - F(GRATE_Z - 0.004), F(FLOOR_R + 0.04) - _radial(P)), lo, hi), BLACK_L)
    return fd


def floor_field():
    """The emplacement's floor: steel tread plates (0) with seams, a raised diamond tread on some, gunmetal (9) bolts at
    their corners; its side wall black."""
    fd = Field("Floor")
    R = FLOOR_R + 0.02
    lo, hi = (-R - 0.02, -R - 0.02, -0.12), (R + 0.02, R + 0.02, TOP_Z + 0.03)
    fd.add(Func(lambda P: _disc_sd(P, R, -0.08, TOP_Z, rr=0.01), lo, hi,
                disp=lambda P: F(0.0005) * NOISE(P * F(60)), disp_amp=0.001), 0.0)
    def seams(P):
        e, rnd, fu, fv = _cells(P, PLATE)
        return np.maximum(e - F(0.0035), np.abs(P[:, 2] - F(TOP_Z)) - F(0.006))
    fd.sub(Func(seams, lo, hi), 0.002)
    def tread(P):
        e, rnd, fu, fv = _cells(P, PLATE)
        a = (P[:, 0] + P[:, 1]) * F(45.0)
        b = (P[:, 0] - P[:, 1]) * F(45.0)
        bumps = np.maximum(np.abs(np.sin(a)) - F(0.25), np.abs(np.sin(b * F(3.0))) - F(0.45))
        on = (rnd > F(0.35)) & (e > F(0.03))
        d = np.maximum(bumps * F(0.004), np.abs(P[:, 2] - F(TOP_Z + 0.001)) - F(0.0016))
        return np.where(on & (_radial(P) < F(FLOOR_R - 0.03)), d, F(1.0))
    fd.add(Func(tread, lo, hi), 0.0008)
    n = int(R / PLATE) + 2
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            cx, cy = (i - 0.5) * PLATE, (j - 0.5) * PLATE
            for dx in (-0.032, 0.032):
                for dy in (-0.032, 0.032):
                    q = v3((cx + dx, cy + dy, TOP_Z))
                    if math.hypot(q[0], q[1]) < FLOOR_R - 0.04:
                        fd.add(Cylinder(q + v3((0, 0, 0.002)), 0.009, 0.006, rr=0.002), 0.001, GM_L)
    fd.paint(Func(lambda P: P[:, 2] - F(TOP_Z - 0.03), lo, hi), BLACK_L)
    return fd


def bag_specs(seed=5):
    """(centre, yaw, half extents, seed) of every sandbag: two staggered courses round the floor, the gaps left open."""
    rs = np.random.RandomState(seed)
    out = []
    for course in range(3):
        rr = BAG_R[course]
        n = int(2 * math.pi * rr / (2 * BAG[0] + 0.012))
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * course) / n
            if in_gap(a, 0.02) or (course == 2 and (math.sin(a * 3.0 + 0.7) < -0.2)):
                continue
            if course == 2 and _angd(a, GAPS["plates"]) < 0.3:
                continue
            z = GRATE_Z + BAG[2] * 0.9 + course * (2 * BAG[2] * 0.82) + rs.uniform(-0.004, 0.006)
            c = v3((math.cos(a) * (rr + rs.uniform(-0.012, 0.012)), math.sin(a) * (rr + rs.uniform(-0.012, 0.012)), z))
            yaw = a + math.pi / 2 + rs.uniform(-0.08, 0.08)
            h = (BAG[0] * rs.uniform(0.92, 1.04), BAG[1] * rs.uniform(0.92, 1.05), BAG[2] * rs.uniform(0.9, 1.05))
            out.append((c, yaw, h, int(rs.randint(1 << 20))))
    return out


def sandbags_field():
    """The parapet: plump grey sandbags (0), each a little different, their tied ends pinched (twine, 6), a stencilled
    mark on a few (5)."""
    fd = Field("Sandbags")
    lumpy = lambda P: F(0.004) * NOISE(P * F(12)) + F(0.0015) * NOISE(P * F(40))
    for c, yaw, h, sd in bag_specs():
        R = euler(0.03 * math.sin(sd), 0.04 * math.cos(sd), yaw)
        fd.add(RoundBox(c, h, h[2] * 0.95, R=R, disp=lumpy, disp_amp=0.006), 0.012, 0)
        e = c + R @ v3((h[0] + 0.012, 0.0, 0.0))
        fd.add(Ellipsoid(e, (0.022, 0.03, 0.022), R=R), 0.012, 0)
        fd.add(Torus(e - R @ v3((0.006, 0, 0)), 0.018, 0.0045, R=R @ rot_from_axes(z_axis=(1, 0, 0))), 0.002, 6)
        if sd % 5 == 0:
            fd.paint(Inter(Shell(Ellipsoid(c + v3((0, 0, h[2] * 0.4)), (0.06, 0.04, h[2] * 0.7), R=R), 0.0, 0.03),
                           Plane(c + v3((0, 0, h[2] * 0.5)), (0, 0, -1))), 5)
    return fd


def _gap_frame(name, r=1.31):
    a = GAPS[name]
    o = v3((math.cos(a), math.sin(a), 0.0))
    t = v3((-math.sin(a), math.cos(a), 0.0))
    return o * r, o, t


SHELL_CRATE = (0.13, 0.2, 0.16)        # the shell crate's half depth (radial), half length, height


def _shell_spots():
    c0, o, t = _gap_frame("shells")
    out = []
    for i in (-1.5, -0.5, 0.5, 1.5):
        for j in (-0.5, 0.5):
            if i == 1.5 and j == 0.5:
                continue                                                    # (one taken)
            out.append(c0 + t * (i * 0.092) + o * (j * 0.12) + v3((0, 0, GRATE_Z + 0.03)))
    return out


def shells_field():
    """A crate of shells standing nose up: gunmetal-black (0) with an amber (6) band, gunmetal (9) corners and black (5)
    rope handles, the shells in it (their cases, cages and noses: _g.shell_into)."""
    fd = Field("Shells")
    c0, o, t = _gap_frame("shells")
    R = np.stack([o, t, v3((0, 0, 1))], axis=1)
    hx, hy, h = SHELL_CRATE
    cz = c0 + v3((0, 0, GRATE_Z - 0.004))
    def box(P):
        q = (P - cz.astype(F)) @ R.astype(F)
        outer = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx), np.abs(q[:, 1]) - F(hy)), np.maximum(-q[:, 2], q[:, 2] - F(h)))
        inner = np.maximum(np.maximum(np.abs(q[:, 0]) - F(hx - 0.016), np.abs(q[:, 1]) - F(hy - 0.016)), F(0.03) - q[:, 2])
        return np.maximum(outer, -inner)
    fd.add(Func(box, cz - 0.35, cz + 0.35), 0.0, BASE_L)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(RoundBox(cz + R @ v3((sx * hx, sy * hy, h / 2)), (0.012, 0.012, h / 2 + 0.003), 0.004, R=R), 0.002, GM_L)
    fd.paint(Func(lambda P: np.maximum(np.abs(((P - cz.astype(F)) @ R.astype(F))[:, 2] - F(h * 0.55)) - F(0.025),
                                       F(hx - 0.004) - np.abs(((P - cz.astype(F)) @ R.astype(F))[:, 0])), cz - 0.35, cz + 0.35), AMB_L)
    for sy in (-1, 1):
        e = cz + R @ v3((0.0, sy * (hy + 0.01), h * 0.7))
        fd.add(Inter(Torus(e, 0.035, 0.0065, R=rot_from_axes(z_axis=t)), Plane(e + v3((0, 0, 0.008)), (0, 0, 1))), 0.002, BLACK_L)
    for k, p in enumerate(_shell_spots()):
        _g.shell_into(fd, p, v3((0.015 * ((k % 3) - 1), 0.01 * ((k % 2) - 0.5), 1.0)), k=0.002)
    return fd


RADIO_CRATE = (0.13, 0.17, 0.2)       # the crate under the radio: half depth (radial), half length, height
RADIO = (0.09, 0.13, 0.075)           # the radio's half depth, half length, half height


def _radio_frame():
    c0, o, t = _gap_frame("radio", 1.3)
    top = c0 + v3((0, 0, GRATE_Z + RADIO_CRATE[2]))
    return c0, o, t, top + v3((0, 0, RADIO[2]))


def radio_field():
    """The field radio on an ammo crate: the crate (gunmetal-black 0, stencils 7, gunmetal 9 latches); the radio: a gunmetal
    case (9) under a teal canvas cover (8) with its flap folded back, a black (5) face panel with steel (10) dials and
    switches, the handset on its hook and its coiled black cord (12), a whip antenna (5) with a steel base."""
    fd = Field("Radio")
    c0, o, t, rc = _radio_frame()
    R = np.stack([o, t, v3((0, 0, 1))], axis=1)
    hx, hy, h = RADIO_CRATE
    cc = c0 + v3((0, 0, GRATE_Z + h / 2 - 0.004))
    fd.add(RoundBox(cc, (hx, hy, h / 2), 0.014, R=R), 0.0, BASE_L)
    for sy in (-1, 1):
        fd.add(RoundBox(cc + R @ v3((-hx, sy * 0.1, h * 0.25)), (0.008, 0.02, 0.025), 0.004, R=R), 0.002, GM_L)
    _g.stencil(fd, "AMMO", cc + R @ v3((-hx - 0.001, 0.0, -0.04)), t, v3((0, 0, 1)), 0.03, WHITE_L, depth=0.01)
    ax, ay, az = RADIO
    fd.add(RoundBox(rc, (ax, ay, az), 0.014, R=R), 0.006, GM_L)
    fd.add(RoundBox(rc + R @ v3((0.01, 0.0, 0.004)), (ax + 0.008, ay + 0.008, az - 0.012), 0.016, R=R,
                    disp=lambda P: F(0.0012) * NOISE(P * F(30)), disp_amp=0.0015), 0.004, TEAL_L)
    face = rc - o * (ax + 0.004)
    fd.add(RoundBox(face, (0.006, ay - 0.02, az - 0.018), 0.004, R=R), 0.002, BLACK_L)
    fd.add(RoundBox(rc + o * 0.02 + v3((0, 0, az + 0.004)), (ax - 0.02, ay, 0.01), 0.006, R=R @ euler(0, 0.4, 0)), 0.004, TEAL_L)
    for k, (dy, dz, r) in enumerate(((-0.08, 0.025, 0.016), (-0.035, 0.025, 0.012), (0.01, 0.025, 0.012), (-0.08, -0.025, 0.012))):
        p = face - o * 0.008 + t * dy + v3((0, 0, dz))
        fd.add(Cylinder(p, r, 0.014, rr=0.004, R=rot_from_axes(z_axis=o)), 0.002, STEEL_L)
    for dy in (0.04, 0.06, 0.08):
        fd.add(RoundBox(face - o * 0.01 + t * dy + v3((0, 0, -0.03)), (0.006, 0.004, 0.012), 0.002, R=R), 0.001, STEEL_L)
    # the handset hanging on its hook at the side, its coiled cord
    hs = rc + t * (ay + 0.03) - o * 0.02 + v3((0, 0, 0.0))
    fd.add(RoundCone(hs + v3((0, 0, 0.05)), hs + v3((0, 0, -0.05)), 0.018, 0.018), 0.004, BLACK_L)
    for s in (-1, 1):
        fd.add(Ellipsoid(hs + v3((0, 0, s * 0.055)) - o * 0.012, (0.026, 0.02, 0.022)), 0.006, BLACK_L)
    pts = [hs + v3((0, 0, -0.06)) - t * 0.01 * k + v3((0, 0, -0.012 * k)) + o * (0.012 * math.sin(k * 1.9)) for k in range(7)]
    fd.add(Chain(pts, [0.008] * len(pts), k=0.006, disp=lambda P: F(0.003) * np.sin(P[:, 2] * F(260)), disp_amp=0.003), 0.003, RUBBER_L)
    # the antenna
    ab = rc + o * 0.05 - t * (ay - 0.03) + v3((0, 0, az))
    fd.add(Cylinder(ab + v3((0, 0, 0.012)), 0.014, 0.024, rr=0.004), 0.003, STEEL_L)
    fd.add(RoundCone(ab + v3((0, 0, 0.02)), ab + v3((0.02, 0.03, 0.46)), 0.006, 0.003), 0.002, BLACK_L)
    fd.add(Sphere(ab + v3((0.02, 0.03, 0.465)), 0.008), 0.002, BLACK_L)
    return fd


def _radio_display():
    c0, o, t, rc = _radio_frame()
    face = rc - o * (RADIO[0] + 0.004)
    return face, o, t


def plates_field():
    """The barricade: salvaged white robot plates (0 = robot white) propped against the bags in a gap of the parapet: a big
    curved torso plate (the amber chevron 6 sprayed across it), a shoulder plate and a shin plate leaning on it, dents and
    scrapes down to the gunmetal (9), black (5) straps holding them, a red-orange (13) hazard stripe the robots painted,
    half sprayed over; a sandbag on their foot."""
    fd = Field("Plates")
    c0, o, t = _gap_frame("plates", 1.27)
    up = v3((0, 0, 1))
    # the torso plate: a curved slab leaning outward against the bags
    lean = norm(up * 0.92 + o * 0.38)
    n = norm(np.cross(t, lean))
    if n @ o > 0:
        n = -n
    pc = c0 + v3((0, 0, GRATE_Z + 0.32)) + o * 0.04
    def torso_plate(P, pc=pc, lean=lean, n=n):
        q = P - pc.astype(F)
        u, v, w = q @ t.astype(F), q @ lean.astype(F), q @ n.astype(F)
        w = w - F(0.9) * (F(0.06) - u * u) * F(0.5) - F(0.4) * (F(0.06) - v * v) * F(0.5)
        e = np.sqrt((u / F(0.36)) ** 2 + (v / F(0.33)) ** 2) - F(1.0)
        d2 = np.maximum(e * F(0.33), np.abs(v) - F(0.3))
        return np.maximum(d2, np.abs(w) - F(0.013)) - F(0.004)
    fd.add(Func(torso_plate, pc - 0.4, pc + 0.4), 0.0, BASE_L)
    pt = lambda u, v, w=0.0: pc + t * u + lean * v + n * (w + 0.9 * (0.06 - u * u) * 0.5 + 0.4 * (0.06 - v * v) * 0.5)
    for su in (-1, 1):
        fd.paint(RoundCone(pt(su * 0.21, 0.16, 0.017), pt(0.0, -0.1, 0.017), 0.042, 0.042), AMB_L)
    fd.paint(RoundCone(pt(-0.26, -0.1, 0.017), pt(-0.12, -0.2, 0.017), 0.016, 0.016), HAZ_L)
    for u, v, r in ((0.15, -0.12, 0.024), (-0.12, 0.15, 0.018), (0.22, 0.12, 0.012)):
        fd.sub(Sphere(pt(u, v, 0.017 + r * 0.7), r), 0.004)
    fd.sub(RoundCone(pt(-0.2, 0.0, 0.017), pt(0.2, 0.0, 0.017), 0.004, 0.004), 0.002)                 # a panel line
    fd.paint(RoundCone(pt(0.05, 0.19, 0.017), pt(0.16, 0.16, 0.017), 0.005, 0.004), GM_L)
    # a shoulder plate leaning on its left, a shin plate on its right
    for side, (du, w, hgt, tilt) in ((-1, (0.36, 0.15, 0.22, 0.5)), (1, (0.34, 0.12, 0.3, 0.35))):
        bc = c0 + t * (side * du) - o * 0.06 + v3((0, 0, GRATE_Z + hgt * 0.5))
        Rb = rot_from_axes(z_axis=norm(up + o * tilt), x_axis=t)
        def curved(P, bc=bc, Rb=Rb, w=w, hgt=hgt):
            q = (P - bc.astype(F)) @ Rb.astype(F)
            ring = np.abs(np.sqrt((q[:, 0] / F(w)) ** 2 + ((q[:, 1] - F(0.08)) / F(0.1)) ** 2) - F(1.0)) * F(0.1) - F(0.011)
            half = np.maximum(ring, -q[:, 1] + F(0.03))
            return np.maximum(half, np.abs(q[:, 2]) - F(hgt * 0.5))
        fd.add(Func(curved, bc - 0.35, bc + 0.35), 0.006, BASE_L)
    # the straps round them and a sandbag on their foot
    for dz in (0.12, 0.3):
        sc = c0 + o * 0.02 + v3((0, 0, GRATE_Z + dz))
        fd.add(RoundBox(sc, (0.02, 0.36, 0.014), 0.006, R=rot_from_axes(z_axis=lean, y_axis=t)), 0.004, BLACK_L)
    return fd


BANNER_H = 1.32                # the pole's top (z)
BANNER = (0.17, 0.5)           # the banner's half width and its drop


def banner_field():
    """The Resistance banner: a gunmetal (9) pipe for a pole wedged in the parapet, a crossbar at its top; hanging from it a
    banner of amber cloth (0) with a swallow-tailed foot and a bold black (5) chevron, frayed and scorched (5) at an edge."""
    fd = Field("Banner")
    c0, o, t = _gap_frame("banner", 1.36)
    foot = c0 + v3((0, 0, GRATE_Z + 0.06))
    top = c0 + v3((0, 0, BANNER_H))
    fd.add(RoundCone(foot, top, 0.019, 0.016), 0.0, GM_L)
    fd.add(Sphere(top + v3((0, 0, 0.012)), 0.022), 0.004, GM_L)
    bar = top - v3((0, 0, 0.05)) + o * 0.02
    hw, drop = BANNER
    fd.add(RoundCone(bar - t * (hw + 0.03), bar + t * (hw + 0.03), 0.011, 0.011), 0.004, GM_L)
    def cloth(P):
        q = P - bar.astype(F)
        u = q @ t.astype(F)
        v = -q[:, 2]
        w = q @ (-o).astype(F)
        w0 = F(0.018) * np.sin(u * F(14.0) + v * F(4.0)) * np.clip(v / F(0.15), 0, 1) + F(0.006) * np.sin(v * F(20.0))
        tail = F(drop) - F(0.12) * (F(1.0) - np.abs(u) / F(hw))
        box = np.maximum(np.maximum(np.abs(u) - F(hw), F(0.01) - v), v - tail)
        return np.maximum(box, np.abs(w - w0) - F(0.006))
    lo, hi = bar - v3((0.3, 0.3, drop + 0.05)), bar + v3((0.3, 0.3, 0.05))
    fd.add(Func(cloth, lo, hi, disp=lambda P: F(0.001) * NOISE(P * F(30)), disp_amp=0.0015), 0.004, BASE_L)
    for su in (-1, 1):
        a = bar + t * (su * 0.11) - v3((0, 0, 0.1))
        b = bar - v3((0, 0, 0.3))
        fd.paint(RoundCone(a - o * 0.05, b - o * 0.05, 0.034, 0.034), BLACK_L)
        fd.paint(RoundCone(a + o * 0.05, b + o * 0.05, 0.034, 0.034), BLACK_L)
    fd.paint(Sphere(bar + t * (hw - 0.01) - v3((0, 0, drop - 0.06)), 0.05), BLACK_L)
    return fd


def cable_paths():
    """Cables: from the radio's back down over the bags and along the grating, and a thick one in from outside to it."""
    c0, o, t, rc = _radio_frame()
    a = rc + o * (RADIO[0] + 0.01) + v3((0, 0, -0.03))
    b = c0 + o * 0.15 + v3((0, 0, GRATE_Z + 0.012))
    cpath = [a, a + o * 0.04 + v3((0, 0, -0.06)), b, b + t * 0.25 + o * 0.03, b + t * 0.55 + o * 0.0 + v3((0, 0, 0.0))]
    for p in cpath[2:]:
        p[2] = GRATE_Z + 0.012
    a2 = c0 + o * 0.12 - t * 0.12 + v3((0, 0, GRATE_Z + 0.015))
    e2 = a2 + o * 0.0 - t * 0.5
    e2 = norm(v3((e2[0], e2[1], 0))) * (GROUND_R - 0.04) + v3((0, 0, GRATE_Z + 0.015))
    return [(cpath, 0.012), ([a2, (a2 + e2) * 0.5 + o * 0.02, e2], 0.02)]


def cables_field():
    """Black rubber cables (12) on the grating, a gunmetal (9) coupling on the thick one."""
    fd = Field("Cables")
    for pts, r in cable_paths():
        fd.add(Chain(pts, [r] * len(pts), k=0.03), 0.0, RUBBER_L)
    pts, r = cable_paths()[1]
    m = (pts[0] + pts[1]) * 0.5
    fd.add(Cylinder(m, r + 0.01, 0.05, rr=0.006, R=rot_from_axes(z_axis=norm(pts[1] - pts[0]))), 0.004, GM_L)
    return fd


def neon_field():
    """Everything that glows on the base (one emissive mesh): the shells' cores, the radio's display and its lamp."""
    fd = Field("Neon")
    for k, p in enumerate(_shell_spots()):
        _g.core_into(fd, p, v3((0.015 * ((k % 3) - 1), 0.01 * ((k % 2) - 0.5), 1.0)))
    face, o, t = _radio_display()
    R = np.stack([o, t, v3((0, 0, 1))], axis=1)
    fd.add(RoundBox(face - o * 0.006 + t * 0.06 + v3((0, 0, 0.022)), (0.004, 0.038, 0.016), 0.003, R=R), 0.0)
    fd.add(Sphere(face - o * 0.006 + t * 0.1 + v3((0, 0, -0.03)), 0.009), 0.0)
    return fd


def grass_geometry(seed=0):
    """(No grass inside the data center.)"""
    return np.zeros((0, 3)), [], np.zeros((0, 2)), np.zeros(0, int)


def flower_geometry(seed=0):
    return []


def fields():
    return [("Ground", ground_field(), 0.006), ("Floor", floor_field(), 0.0032), ("Sandbags", sandbags_field(), 0.004),
            ("Shells", shells_field(), 0.0022), ("Radio", radio_field(), 0.002), ("Plates", plates_field(), 0.003), ("Banner", banner_field(), 0.0024),
            ("Cables", cables_field(), 0.0024), ("Neon", neon_field(), 0.0018)]


REGION_PARTS = ("Ground", "Floor", "Sandbags", "Shells", "Radio", "Plates", "Banner", "Cables")
LOW_TARGETS = {"Ground": 1300, "Floor": 2600, "Sandbags": 4200, "Shells": 1900, "Radio": 1100, "Plates": 1100, "Banner": 700, "Cables": 400,
               "Neon": 500}
KIT = dict(_g.KIT)
MAT_OVERRIDES = {"Ground": ("modern_kit", dict(KIT, name="HQ_NaGrate", base=(0.2, 0.21, 0.23), weave=0.0)),
                 "Floor": ("modern_kit", dict(KIT, name="HQ_NaFloor", base=(0.27, 0.28, 0.3), weave=0.0)),
                 "Sandbags": ("sacking", {"name": "HQ_NaSandbags", "base": (0.46, 0.44, 0.38), "dark": (0.28, 0.27, 0.23),
                                          "stencil": (0.1, 0.1, 0.1)}),
                 "Shells": ("modern_kit", dict(KIT, name="HQ_NaKit", base=_g.ARMOUR, weave=0.0)),
                 "Radio": ("modern_kit", dict(KIT, name="HQ_NaKit", base=_g.ARMOUR, weave=0.0)),
                 "Cables": ("modern_kit", dict(KIT, name="HQ_NaKit", base=_g.ARMOUR, weave=0.0)),
                 "Banner": ("modern_kit", dict(KIT, name="HQ_NaBanner", base=_g.AMBER_P, weave=1.0)),
                 "Plates": ("modern_kit", dict(KIT, name="HQ_NaPlates", base=_g.ROBOT_WHITE, weave=0.0, gloss=0.42))}
GLOW = {"Neon": (_g.AMBER, 1.1, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
