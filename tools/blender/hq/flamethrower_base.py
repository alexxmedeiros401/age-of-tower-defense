"""The Flamethrower's base: a scorched patch of street at a burnt-out checkpoint. A round patch of cracked asphalt (a
worn double yellow line running across it, an old tar patch, a cast-iron manhole cover by his left foot) inside a
concrete kerb, a strip of suburban lawn round it; a fan of black scorch marks burnt into the asphalt before him where his
jet licks the street. Behind him on his left a low wall of sandbags (three courses), behind him on his right a stack of
olive fuel drums (two standing, one lying across them; yellow bands, red-and-white flammable placards), on his left
behind the sandbags a charred burn barrel with embers glowing in it (its own glowing mesh), before him on his right a
coyote jerrycan, before him on his left a red fire extinguisher. Grass tufts and a few dandelions on the lawn (direct
low-poly geometry).

Everything above the asphalt stands clear of the gun as the tower turns: nothing above the street inside r = 0.78 (the
manhole cover and the paint lie flush), nothing at the rim higher than 0.7 above it, and the arc before him where the
jet sweeps (240-300 degrees round from his left) is bare street."""
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
TOP_Z = 0.2                        # the asphalt's top = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
ASPH_R = 1.08
KERB_R = (1.08, 1.18)
KERB_TOP = TOP_Z + 0.03
CLEAR_R = 0.78
# fieldgun labels: olive paint, (5: a second paint), brass, steel, black, -, -, -, red, white
OLIVE, PAINT2, BRASS, STEEL, BLACK, RED, WHITE = 0, 5, 6, 7, 8, 12, 13
# steamworks labels
W_IRON, W_RUST, W_BLACK = 0, 9, 12
SOOT, YELLOW, WHITE_P, TARPATCH = 5, 6, 7, 8


def _polar(deg, r, z=TOP_Z):
    return v3((r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)), z))


DRUM_A = (138.0, 167.0)            # the two standing drums (degrees round from his left; 90 = behind him)
DRUM_RR = 0.94
DRUM_R, DRUM_H = 0.152, 0.45
BARREL = _polar(34.0, 0.93)
BARREL_R, BARREL_H = 0.13, 0.35
JERRY = _polar(207.0, 0.95)
EXT = _polar(323.0, 0.93)
MANHOLE = v3((0.4, -0.27, TOP_Z))
MANHOLE_R = 0.15
BAGS_A = (48.0, 122.0)             # the sandbag wall's arc
BAGS_R = 0.93
LINE_P = v3((0.05, 0.0, 0.0))      # the double yellow line: through here ...
LINE_D = norm(v3((-0.5, 0.866, 0.0)))   # ... along this


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def ground_field():
    """The lawn round the street (ground recipe: grass on top, earth on its sides)."""
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
    return fd


def _crack_paths(seed=17):
    rs = np.random.RandomState(seed)
    out = []
    starts = [(0.62, -0.5), (-0.55, -0.62), (0.2, 0.62), (-0.82, 0.05), (0.85, -0.1), (0.05, -0.9), (-0.3, -0.35)]
    for sx, sy in starts:
        p = np.array([sx, sy])
        ang = math.atan2(-sy, -sx) + rs.uniform(-0.9, 0.9)
        pts = [p.copy()]
        for k in range(rs.randint(4, 8)):
            ang += rs.uniform(-0.7, 0.7)
            p = p + np.array([math.cos(ang), math.sin(ang)]) * rs.uniform(0.05, 0.11)
            if np.hypot(*p) > ASPH_R - 0.03:
                break
            pts.append(p.copy())
        if len(pts) > 2:
            out.append(pts)
            if rs.rand() < 0.6:                                              # a branch
                i = rs.randint(1, len(pts) - 1)
                q = pts[i].copy()
                a2 = ang + rs.choice([-1, 1]) * rs.uniform(0.8, 1.4)
                br = [q.copy()]
                for k in range(3):
                    a2 += rs.uniform(-0.5, 0.5)
                    q = q + np.array([math.cos(a2), math.sin(a2)]) * rs.uniform(0.04, 0.08)
                    if np.hypot(*q) > ASPH_R - 0.03:
                        break
                    br.append(q.copy())
                if len(br) > 1:
                    out.append(br)
    return out


def _line_d(P):
    """Signed distance across the double yellow line's middle."""
    q = P[:, :2] - LINE_P[:2].astype(F)
    n = np.array([-LINE_D[1], LINE_D[0]], F)
    return q @ n


def asphalt_field():
    """The street (asphalt recipe): cracked asphalt (0), scorch (5) before him, the double yellow line (6), a white stop
    bar at its edge (7), an old tar patch (8)."""
    fd = Field("Asphalt")
    tex = lambda P: F(0.0014) * NOISE(P * F(45)) + F(0.0022) * NOISE(P * F(9))
    fd.add(Cylinder(v3((0, 0, (TOP_Z + GROUND_TOP - 0.1) / 2)), ASPH_R + 0.004, TOP_Z - GROUND_TOP + 0.1, rr=0.012, disp=tex, disp_amp=0.003), 0.0)
    # the tar patch: a raised rectangle of newer tar
    pc, pa = v3((-0.42, 0.28, TOP_Z)), 0.5
    Rp = euler(0, 0, pa)
    fd.add(RoundBox(pc + v3((0, 0, -0.008)), (0.2, 0.13, 0.011), 0.006, R=Rp), 0.004, TARPATCH)
    # cracks
    for path in _crack_paths():
        pts = [v3((p[0], p[1], TOP_Z + 0.002)) for p in path]
        rads = [0.0065 * (1.0 - 0.6 * i / (len(pts) - 1)) + 0.0015 for i in range(len(pts))]
        fd.sub(Chain(pts, rads, k=0.003), 0.002)
    lo, hi = (-1.2, -1.2, GROUND_TOP - 0.15), (1.2, 1.2, TOP_Z + 0.05)
    # the double yellow line (two stripes, worn)
    fd.paint(Func(lambda P: np.abs(np.abs(_line_d(P)) - F(0.04)) - F(0.021), lo, hi), YELLOW)
    # a white stop bar near the kerb on his right
    def stop(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        return np.maximum(np.abs(r - F(0.98)) - F(0.035), (np.abs(a - F(math.radians(-150))) - F(0.22)) * r)
    fd.paint(Func(stop, lo, hi), WHITE_P)
    # the scorch: a fan burnt into the street before him (ragged), blotches round it
    def fan(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        da = np.abs(a - F(math.radians(-90)))
        w = F(math.radians(30)) + F(0.25) * NOISE(P * F(5)) * F(0.6)
        edge = (da - w) * r
        rag = F(0.05) * NOISE(P * F(9)) + F(0.025) * NOISE(P * F(23))
        return np.maximum(np.maximum(edge, F(0.3) - r), r - F(ASPH_R + 0.02)) + rag
    fd.paint(Func(fan, lo, hi), SOOT)
    rs = np.random.RandomState(5)
    for k in range(7):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.35, 0.95)
        c = v3((r * math.cos(a), r * math.sin(a), TOP_Z))
        s = rs.uniform(0.05, 0.11)
        fd.paint(Func(lambda P, c=c, s=s: np.sqrt(((P[:, :2] - c[:2].astype(F)) ** 2).sum(1)) - F(s) + F(0.03) * NOISE(P * F(14)), c - 0.3, c + 0.3), SOOT)
    bc = BARREL
    fd.paint(Func(lambda P: np.sqrt(((P[:, :2] - bc[:2].astype(F)) ** 2).sum(1)) - F(0.24) + F(0.05) * NOISE(P * F(10)), bc - 0.4, bc + 0.4), SOOT)
    return fd


def kerb_field():
    """Concrete kerb stones round the street (flagstone recipe, pale)."""
    fd = Field("Kerb")
    hz = (KERB_TOP - GROUND_TOP + 0.06) / 2
    chip = lambda P: F(0.002) * NOISE(P * F(11)) + F(0.0012) * NOISE(P * F(37))
    fd.add(ring_func(KERB_R[0], KERB_R[1], 16, 233, KERB_TOP, hz, jitter=0.6, chip=chip), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the sandbag wall
BAG_HALF = (0.112, 0.068, 0.042)


def bag_spots():
    out = []
    a0, a1 = BAGS_A
    n0 = 5
    L = math.radians(a1 - a0) / n0
    for row in range(3):
        n = n0 - (row % 2)
        for k in range(n):
            a = math.radians(a0) + L * (k + 0.5 + 0.5 * (row % 2))
            r = BAGS_R - 0.005 * row
            z = TOP_Z + BAG_HALF[2] * 0.95 + row * BAG_HALF[2] * 1.75
            out.append((a, r, z, row * 10 + k))
    return out


def sandbags_field():
    """Sandbags (sacking: label 0, stencilled marks 5, twine ties 6) in three courses, slumped, their tied ends tucked."""
    fd = Field("Sandbags")
    for a, r, z, k in bag_spots():
        rs = np.random.RandomState(400 + k)
        c = v3((r * math.cos(a), r * math.sin(a), z))
        t = v3((-math.sin(a), math.cos(a), 0.0))
        n = v3((math.cos(a), math.sin(a), 0.0))
        tw = rs.uniform(-0.12, 0.12)
        R = rot_from_axes(x_axis=np.cos(tw) * t + np.sin(tw) * n, z_axis=(0, 0, 1))
        sag = lambda P: F(0.004) * NOISE(P * F(16)) + F(0.0016) * NOISE(P * F(60))
        hx, hy, hz = BAG_HALF
        fd.add(RoundBox(c, (hx * rs.uniform(0.95, 1.05), hy, hz), 0.038, R=R, disp=sag, disp_amp=0.005), 0.012)
        fd.add(Ellipsoid(c + v3((0, 0, 0.004)), (hx * 0.9, hy * 0.95, hz * 1.12), R=R), 0.02)
        # the tied end (twine round the gathered neck)
        e = c + R @ v3((hx + 0.012, 0.0, -0.004))
        fd.add(Ellipsoid(e, (0.022, 0.034, 0.026), R=R), 0.014)
        fd.add(Torus(e - R @ v3((0.008, 0, 0)), 0.026, 0.0045, R=R @ rot_from_axes(z_axis=(1, 0, 0))), 0.003, 6)
        if k in (1, 3, 12):
            fd.paint(Inter(RoundBox(c + n * 0.06, (0.05, 0.05, 0.02), 0.01, R=R), Sphere(c, 0.2), 0.0), 5)
    return fd


# ---------------------------------------------------------------------------------------------- fuel drums
def drum_axes():
    """(centre of the foot, up) of the two standing drums and (centre, axis) of the one lying across them."""
    s = [(_polar(a, DRUM_RR), v3((0, 0, 1))) for a in DRUM_A]
    m = (s[0][0] + s[1][0]) / 2 + v3((0, 0, DRUM_H + DRUM_R - 0.004))
    ax = norm(s[1][0] - s[0][0])
    return s, (m, ax)


def _drum(fd, c, ax, front, rs):
    """One drum, its axis along `ax` from the middle `c`: chimes (rims) at both ends, two rolling hoops, a lid with two
    bungs, a yellow band (5), a red-and-white flammable placard (12, 13) facing `front`."""
    R = rot_from_axes(z_axis=ax)
    dent = lambda P: F(0.0016) * NOISE(P * F(9)) + F(0.0006) * NOISE(P * F(40))
    fd.add(Cylinder(c, DRUM_R, DRUM_H, rr=0.014, R=R, disp=dent, disp_amp=0.002), 0.0, OLIVE)
    for s in (-1, 1):
        fd.add(Torus(c + ax * s * (DRUM_H / 2 - 0.008), DRUM_R - 0.004, 0.0085, R=R), 0.003, OLIVE)
    for s in (-1, 1):
        fd.add(Torus(c + ax * s * DRUM_H * 0.17, DRUM_R + 0.002, 0.007, R=R), 0.004, OLIVE)
    lid = c + ax * (DRUM_H / 2 - 0.004)
    fd.sub(Cylinder(lid + ax * 0.008, DRUM_R - 0.016, 0.014, rr=0.004, R=R), 0.004)
    e1 = norm(np.cross(ax, v3((0.31, 0.47, 0.82))))
    for o, r in ((0.075, 0.022), (-0.08, 0.014)):
        fd.add(Cylinder(lid + e1 * o - ax * 0.002, r, 0.014, rr=0.004, R=R), 0.003, STEEL)
    # the band and the placard
    lo, hi = c - 0.4, c + 0.4
    fd.paint(Func(lambda P: np.abs((P - c.astype(F)) @ ax.astype(F) - F(DRUM_H * 0.31)) - F(0.028), lo, hi), PAINT2)
    f = norm(front - ax * (front @ ax))
    side = np.cross(ax, f)

    def diamond(P, size):
        q = P - c.astype(F)
        u = q @ side.astype(F)
        v = q @ ax.astype(F) + F(0.02)
        return np.maximum((np.abs(u) + np.abs(v)) / F(math.sqrt(2)) - F(size), F(0.02) - q @ f.astype(F))
    # a red flame left in the white (the white is mixed over the red: it leaves the flame out)
    def flame(P):
        q = P - c.astype(F)
        u = q @ side.astype(F)
        v = q @ ax.astype(F) + F(0.02)
        w = F(0.016) * np.clip((F(0.03) - v) / F(0.05), 0, 1) + F(0.006) * np.abs(np.sin(u * F(160)))
        return np.maximum(np.abs(u) - w, np.abs(v + F(0.004)) - F(0.025))
    fd.paint(Func(lambda P: diamond(P, 0.058), lo, hi), RED)
    fd.paint(Func(lambda P: np.maximum(diamond(P, 0.04), -flame(P)), lo, hi), WHITE)


def drums_field():
    """Two olive fuel drums standing, a third lying across their tops (fieldgun paint)."""
    fd = Field("Drums")
    rs = np.random.RandomState(31)
    (s0, s1), (m, ax) = drum_axes()
    front = v3((0.2, -1.0, 0.25))
    for c, up in (s0, s1):
        _drum(fd, c + up * (DRUM_H / 2), up, front, rs)
    _drum(fd, m, ax, front + v3((0, 0, 0.6)), rs)
    # wooden chocks under the lying drum, on the tops (black rubber)
    for c, up in (s0, s1):
        top = c + up * (DRUM_H + 0.006)
        d = norm(m - top)
        fd.add(RoundBox(top + v3((0, 0, 0.006)), (0.03, 0.06, 0.012), 0.006, R=rot_from_axes(x_axis=ax, z_axis=(0, 0, 1))), 0.004, BLACK)
    return fd


# ---------------------------------------------------------------------------------------------- the burn barrel
def barrel_field():
    """A charred steel drum (steamworks: black iron 0, rust 9) burnt out and used as a burn barrel: dented, holes punched
    round its foot, its top open (a lip rolled outward), half full of charred wood."""
    fd = Field("Barrel")
    c = BARREL + v3((0, 0, BARREL_H / 2))
    dent = lambda P: F(0.003) * NOISE(P * F(7)) + F(0.001) * NOISE(P * F(30))
    fd.add(Cylinder(c, BARREL_R, BARREL_H, rr=0.012, disp=dent, disp_amp=0.004), 0.0, W_IRON)
    fd.sub(Cylinder(c + v3((0, 0, 0.04)), BARREL_R - 0.009, BARREL_H, rr=0.006), 0.003)
    top = c + v3((0, 0, BARREL_H / 2))
    fd.add(Torus(top - v3((0, 0, 0.004)), BARREL_R + 0.002, 0.008), 0.003, W_IRON)
    for z in (0.33, 0.67):
        fd.add(Torus(BARREL + v3((0, 0, BARREL_H * z)), BARREL_R + 0.002, 0.006), 0.003, W_IRON)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        d = v3((math.cos(a), math.sin(a), 0))
        fd.sub(Sphere(BARREL + d * BARREL_R + v3((0, 0, 0.05)), 0.016), 0.003)
    fd.paint(Func(lambda P: F(0.01) - NOISE(P * F(6)) * F(0.06) - F(0.012), c - 0.3, c + 0.3), W_RUST)
    return fd


def char_field():
    """Charred wood standing up out of the barrel (charcoal recipe)."""
    fd = Field("Char")
    rs = np.random.RandomState(77)
    top = BARREL + v3((0, 0, BARREL_H))
    for k in range(5):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.02, 0.07)
        b = BARREL + v3((math.cos(a) * r, math.sin(a) * r, BARREL_H * 0.6))
        d = norm(v3((math.cos(a) * 0.5 + rs.uniform(-0.2, 0.2), math.sin(a) * 0.5 + rs.uniform(-0.2, 0.2), 1.0)))
        L = rs.uniform(0.1, 0.2)
        fd.add(RoundCone(b, b + d * L, rs.uniform(0.014, 0.02), rs.uniform(0.008, 0.013), disp=lambda P: F(0.002) * NOISE(P * F(40)), disp_amp=0.002), 0.004)
    return fd


def embers_field():
    """The embers glowing in the barrel (its own glowing mesh): a lumpy bed just under its lip."""
    fd = Field("Embers")
    rs = np.random.RandomState(91)
    z = BARREL_H - 0.045
    fd.add(Cylinder(BARREL + v3((0, 0, z)), BARREL_R - 0.012, 0.03, rr=0.012), 0.0)
    for k in range(9):
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.0, BARREL_R - 0.04)
        fd.add(Sphere(BARREL + v3((math.cos(a) * r, math.sin(a) * r, z + 0.012)), rs.uniform(0.016, 0.026)), 0.01)
    return fd


# ---------------------------------------------------------------------------------------------- the jerrycan
JC_HALF = (0.085, 0.05, 0.12)


def jerry_frame():
    """Its middle, the direction along its broad side (t) and the normal of its broad side (n, turned toward the front)."""
    c = JERRY + v3((0, 0, JC_HALF[2] + 0.002))
    n = euler(0, 0, 0.6) @ norm(v3((-JERRY[0], -JERRY[1], 0)))
    t = np.cross(n, v3((0, 0, 1)))
    return c, t, n


def jerrycan_field():
    """A coyote-tan steel jerrycan (fieldgun paint 0): the stamped X on its sides, a rim seam, three handles on top, the
    spout's cap (black, 8) and its clamp lever (steel 7)."""
    fd = Field("Jerrycan")
    c, t, n = jerry_frame()
    up = v3((0, 0, 1))
    R = np.stack([t, n, up], axis=1)
    hx, hy, hz = JC_HALF
    fd.add(RoundBox(c, (hx, hy, hz), 0.016, R=R, disp=lambda P: F(0.0008) * NOISE(P * F(30)), disp_amp=0.001), 0.0, OLIVE)
    fd.add(RoundBox(c, (hx + 0.004, 0.006, hz + 0.003), 0.005, R=R), 0.004, OLIVE)                 # the welded rim
    for s in (-1, 1):                                                                               # the stamped X
        for d in (1, -1):
            a = c + n * s * (hy + 0.001) + t * (-hx * 0.75) + up * (-hz * 0.75 * d)
            b = c + n * s * (hy + 0.001) + t * (hx * 0.75) + up * (hz * 0.75 * d)
            fd.sub(RoundCone(a, b, 0.008, 0.008), 0.004)
    # three handles over the top
    for o in (-0.045, 0.0, 0.045):
        p0 = c + up * (hz - 0.004) + t * o
        pts = [p0 - n * 0.026, p0 - n * 0.022 + up * 0.03, p0 + n * 0.022 + up * 0.03, p0 + n * 0.026]
        fd.add(Chain(pts, [0.0075] * 4, k=0.006), 0.004, OLIVE)
    sp = c + up * (hz + 0.006) + t * (hx - 0.022)
    fd.add(Cylinder(sp + up * 0.012, 0.022, 0.03, rr=0.006), 0.006, BLACK)
    fd.add(RoundCone(sp + up * 0.026 - t * 0.02, sp + up * 0.03 - t * 0.06, 0.006, 0.006), 0.003, STEEL)
    return fd


# ---------------------------------------------------------------------------------------------- the fire extinguisher
EXT_R, EXT_H = 0.05, 0.25


def extinguisher_field():
    """A red fire extinguisher (fieldgun paint 0 = red here): a domed cylinder, a white label (13), the steel valve head
    (7), a black carrying handle and lever (8), its black hose looped down to the nozzle clipped on its side."""
    fd = Field("Extinguisher")
    up = v3((0, 0, 1))
    c = EXT + up * (EXT_H / 2)
    fd.add(Cylinder(c, EXT_R, EXT_H, rr=0.02), 0.0, OLIVE)
    fd.add(Inter(Sphere(EXT + up * (EXT_H - 0.01), EXT_R), Plane(EXT + up * (EXT_H - 0.01), (0, 0, -1)), 0.004), 0.01, OLIVE)
    fd.add(Torus(EXT + up * 0.012, EXT_R - 0.002, 0.008), 0.004, BLACK)                            # its foot ring
    out = norm(v3((EXT[0], EXT[1], 0)))
    side = np.cross(up, out)
    face = -out                                                                                     # (it faces him)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 2] - F(EXT[2] + EXT_H * 0.5)) - F(0.045), F(0.01) - (P - c.astype(F)) @ face.astype(F)),
                  c - 0.2, c + 0.2), WHITE)
    vh = EXT + up * (EXT_H + EXT_R * 0.75)
    fd.add(Cylinder(vh, 0.02, 0.04, rr=0.006), 0.004, STEEL)
    fd.add(RoundBox(vh + up * 0.03 + face * 0.01, (0.018, 0.05, 0.007), 0.005, R=rot_from_axes(y_axis=face, z_axis=up)), 0.003, BLACK)
    fd.add(RoundBox(vh + up * 0.048 + face * 0.02, (0.016, 0.055, 0.006), 0.005, R=rot_from_axes(y_axis=norm(face + up * 0.3), z_axis=up)), 0.003, BLACK)
    # the hose: from the valve head, looping down its back and up to the nozzle clipped on its side
    pts = [vh - face * 0.022, vh - face * 0.06 - up * 0.05, EXT + up * 0.1 - face * 0.075 + side * 0.03,
           EXT + up * 0.06 + side * 0.07, EXT + up * 0.16 + side * 0.06]
    fd.add(Chain(pts, [0.009] * len(pts), k=0.01), 0.004, BLACK)
    fd.add(RoundCone(pts[-1], pts[-1] + up * 0.05, 0.011, 0.009), 0.004, BLACK)
    return fd


# ---------------------------------------------------------------------------------------------- the manhole cover
def manhole_field():
    """A cast-iron manhole cover (steamworks iron 0) lying flush in the asphalt: a raised rim, a grid of raised bars, two
    lifting holes."""
    fd = Field("Manhole")
    c = MANHOLE + v3((0, 0, -0.008))
    fd.add(Cylinder(c, MANHOLE_R, 0.022, rr=0.006), 0.0, W_IRON)
    fd.add(Torus(MANHOLE + v3((0, 0, 0.002)), MANHOLE_R - 0.012, 0.007), 0.003, W_IRON)

    def grid(P):
        q = P - MANHOLE.astype(F)
        u, v = q[:, 0] * F(0.8) + q[:, 1] * F(0.6), -q[:, 0] * F(0.6) + q[:, 1] * F(0.8)
        g = np.minimum(np.abs((u / F(0.04)) - np.round(u / F(0.04))), np.abs((v / F(0.04)) - np.round(v / F(0.04)))) * F(0.04)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        return np.maximum(np.maximum(g - F(0.005), r - F(MANHOLE_R - 0.03)), np.abs(q[:, 2] - F(0.002)) - F(0.0035))
    fd.add(Func(grid, MANHOLE - 0.2, MANHOLE + 0.2), 0.002, W_IRON)
    for s in (-1, 1):
        fd.sub(Cylinder(MANHOLE + v3((s * (MANHOLE_R - 0.05), 0.0, 0.004)), 0.011, 0.012, rr=0.003), 0.002)
    return fd


# ---------------------------------------------------------------------------------------------- lawn: grass, dandelions
def _blocked(c, pad=0.0):
    r = math.hypot(c[0], c[1])
    return r < KERB_R[1] + 0.03 + pad


def grass_geometry(seed=61):
    """Tufts of lawn grass round the kerb."""
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 22 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(KERB_R[1] + 0.05, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.0):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.15 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(7, 12)
        big = 0.6 + 0.4 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.045)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            outv = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(outv * rs.uniform(0.2, 0.55) + v3((0, 0, 1)))
            L = rs.uniform(0.08, 0.16) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.026, 0.038), outv * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=67):
    """A few dandelions in the lawn (swatch 1: yellow)."""
    rs = np.random.RandomState(seed)
    out = []
    spots, tries = [], 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(KERB_R[1] + 0.06, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.02) or any(np.linalg.norm(c[:2] - s[:2]) < 0.25 for s in spots):
            continue
        spots.append(c)
    for c in spots:
        for k in range(rs.randint(1, 3)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.04)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.06, 0.11)
            d = norm(v3((math.cos(ang) * 0.3, math.sin(ang) * 0.3, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, 1))
            tilt = norm(v3((rs.uniform(-0.4, 0.4), rs.uniform(-0.4, 0.4), 1.0)))
            _bloom(out, root + d * h, tilt, 0.024, 1)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Asphalt", asphalt_field(), 0.004), ("Kerb", kerb_field(), 0.004),
            ("Sandbags", sandbags_field(), 0.0034), ("Drums", drums_field(), 0.003), ("Barrel", barrel_field(), 0.003),
            ("Char", char_field(), 0.003), ("Embers", embers_field(), 0.003), ("Jerrycan", jerrycan_field(), 0.0024),
            ("Extinguisher", extinguisher_field(), 0.0022), ("Manhole", manhole_field(), 0.0026)]


REGION_PARTS = ("Asphalt", "Sandbags", "Drums", "Barrel", "Jerrycan", "Extinguisher", "Manhole")
LOW_TARGETS = {"Ground": 1100, "Asphalt": 2800, "Kerb": 1000, "Sandbags": 1900, "Drums": 2000, "Barrel": 1000, "Char": 250,
               "Embers": 90, "Jerrycan": 600, "Extinguisher": 700, "Manhole": 450}
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_StreetLawn"}),
                 "Asphalt": ("asphalt", {"name": "HQ_StreetAsphalt"}),
                 "Kerb": ("flagstone", {"name": "HQ_StreetKerb", "base": (0.62, 0.61, 0.58), "alt": (0.68, 0.66, 0.61)}),
                 "Sandbags": ("sacking", {"name": "HQ_CheckpointBags"}),
                 "Drums": ("fieldgun", {"name": "HQ_FuelDrums", "olive": (0.3, 0.33, 0.2), "grey": (0.88, 0.68, 0.12),
                                        "red": (0.74, 0.1, 0.07)}),
                 "Barrel": ("steamworks", {"name": "HQ_BurnBarrel", "iron": (0.1, 0.095, 0.09), "leather": (0.36, 0.17, 0.07)}),
                 "Char": ("charcoal", {"name": "HQ_BarrelChar"}),
                 "Embers": ("glow_ball", {"name": "HQ_Embers", "col": (1.0, 0.45, 0.1)}),
                 "Jerrycan": ("fieldgun", {"name": "HQ_Jerrycan", "olive": (0.6, 0.5, 0.36)}),
                 "Extinguisher": ("fieldgun", {"name": "HQ_Extinguisher", "olive": (0.74, 0.1, 0.07)}),
                 "Manhole": ("steamworks", {"name": "HQ_StreetIron", "iron": (0.16, 0.155, 0.15)})}
GLOW = {"Embers": ((1.0, 0.42, 0.08), 1.2, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    return n.z > 0.55 and KERB_R[1] + 0.02 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
