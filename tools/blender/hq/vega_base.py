"""Vega's stand: the Resistance's forward command post inside the robots' data center. A round deck of steel floor
grating (square panels of grate in a solid frame, a chamfered rim with bolts and amber floor markings), the hero ring a
dashed amber light strip set into it (its own glowing mesh). Round him on the deck: behind him a low curved wall of
sandbags, two salvaged white robot armour plates propped against it as cover, sprayed with the Resistance's amber
chevron; behind him on his left the amber Resistance banner hanging from a crossbar on a steel pole (the charcoal
chevron on it); behind him on his right the map table: a gunmetal table made of a pried-off server-rack lid on four legs,
its top a glowing amber holo-map (a screen with the data center's blocks rising off it and a target ring: `Holo`); before
him on his left the field radio on an ammo crate (a whip antenna, a handset on its coiled cord); before him on his right a
dead robot's head lying on the grate (white, cracked, its eye socket dark); cables snaking over the deck from the table
to the radio."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Inter, Shell, Lock, lerp

PLATE_R = 1.16
TOP_Z = 0.16                      # the deck's top = where he stands
BOT_Z = -0.04
STAND = v3((0.0, 0.0, TOP_Z))
RING_R = 0.72                     # the hero ring
RING_W = 0.017                    # its half width
N_DASH = 16
Z = v3((0.0, 0.0, 1.0))
GRATE_R = 0.66                    # the grate inside the ring; solid deck plate outside it (where the props stand)

AMBER = (0.95, 0.58, 0.14)
AMBER_GLOW = (1.0, 0.62, 0.15)
CHARCOAL = (0.13, 0.13, 0.15)
GUNMETAL = (0.22, 0.23, 0.25)
WHITE = (0.88, 0.88, 0.86)


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def _placed(angle_deg, r):
    """A prop's place round him: (centre on the deck, its inward direction (toward him), its tangent). Angles from +x (his
    left) toward +y (behind him)."""
    a = math.radians(angle_deg)
    c = v3((math.cos(a) * r, math.sin(a) * r, TOP_Z))
    inward = -norm(v3((c[0], c[1], 0.0)))
    tang = norm(np.cross(Z, inward))
    return c, inward, tang


def _frame(pl, twist=0.0):
    c, inw, tg = pl
    return c, np.stack([tg, inw, Z], 1) @ euler(0, 0, twist)


WALL_A = (52.0, 128.0)            # the sandbag wall behind him
WALL_R = 1.04
PLATES = (_placed(66.0, 0.9), _placed(108.0, 0.9))
BANNER = _placed(32.0, 1.0)
TABLE = _placed(158.0, 0.86)
RADIO = _placed(-34.0, 0.94)
HEAD = _placed(-150.0, 0.93)


# ---------------------------------------------------------------------------------------------- the deck
def deck_field():
    """modern_kit: the deck (label 0, dark gunmetal, smooth) and its rim; inside the ring a steel grate (square holes in a
    grid of bars, sunk a little) in four panels with a solid frame between them; bolts (9) round the rim; amber (6) floor
    markings (dashes round the outer deck)."""
    fd = Field("Deck")
    def slab(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        d_r = r - F(PLATE_R)
        d_z = np.maximum(P[:, 2] - F(TOP_Z), F(BOT_Z) - P[:, 2])
        q = np.stack([np.maximum(d_r + F(0.026), 0), np.maximum(d_z + F(0.026), 0)], 1)
        return np.minimum(np.maximum(d_r + F(0.026), d_z + F(0.026)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.026)
    def grate(P):
        top = smoothstep(TOP_Z - 0.03, TOP_Z - 0.004, P[:, 2])
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        inner = smoothstep(GRATE_R + 0.004, GRATE_R - 0.012, r)
        cell = F(0.05)
        fx = np.abs(np.mod(P[:, 0] + F(0.025), cell) - F(0.025))
        fy = np.abs(np.mod(P[:, 1] + F(0.025), cell) - F(0.025))
        hole = smoothstep(0.012, 0.009, np.maximum(fx, fy))      # (1 in a hole, 0 on the bars)
        frame = smoothstep(0.028, 0.02, np.minimum(np.abs(P[:, 0]), np.abs(P[:, 1])))   # solid cross between the panels
        h = F(0.016) * hole * inner * (F(1) - frame)
        return h * top + F(0.0005) * NOISE(P * F(30))
    fd.add(Func(slab, (-1.22, -1.22, BOT_Z - 0.05), (1.22, 1.22, TOP_Z + 0.05), disp=grate, disp_amp=0.018), 0.0)
    # the ring's groove
    def groove(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.abs(r - F(RING_R)) - F(RING_W + 0.006), np.abs(P[:, 2] - F(TOP_Z)) - F(0.012))
    fd.sub(Func(groove, (-0.9, -0.9, TOP_Z - 0.03), (0.9, 0.9, TOP_Z + 0.03)), 0.003)
    # seams across the outer deck (its plates)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        d = v3((math.cos(a), math.sin(a), 0.0))
        def seam(P, d=d):
            r = P[:, :2] @ d[:2].astype(F)
            perp = np.abs(P[:, 0] * F(-d[1]) + P[:, 1] * F(d[0]))
            return np.maximum(np.maximum(perp - F(0.003), F(RING_R + 0.04) - r), np.abs(P[:, 2] - F(TOP_Z)) - F(0.006))
        fd.sub(Func(seam, (-1.3, -1.3, TOP_Z - 0.02), (1.3, 1.3, TOP_Z + 0.02)), 0.0015)
    # amber floor markings: short dashes round the outer deck, inside the rim
    def marks(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        s = np.sin(a * F(24))
        return np.maximum(np.maximum(np.abs(r - F(1.04)) - F(0.022), F(0.35) - s), F(TOP_Z - 0.006) - P[:, 2])
    fd.paint(Func(marks, (-1.2, -1.2, TOP_Z - 0.02), (1.2, 1.2, TOP_Z + 0.02)), 6)
    # bolts round the rim
    for i in range(28):
        a = 2 * math.pi * (i + 0.5) / 28
        c = v3((math.cos(a) * (PLATE_R - 0.045), math.sin(a) * (PLATE_R - 0.045), TOP_Z - 0.002))
        fd.add(Cylinder(c, 0.012, 0.01, rr=0.003), 0.002, 9)
    return fd


def ring_field():
    """The hero ring: sixteen dashes of amber light in the deck's groove (they glow)."""
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


# ---------------------------------------------------------------------------------------------- sandbags, salvaged plates
def bag_specs():
    """(centre, tangent, inward, length, twist) of each bag: three staggered courses along the arc behind him."""
    out = []
    a0, a1 = math.radians(WALL_A[0]), math.radians(WALL_A[1])
    L = 0.32
    rs = np.random.RandomState(29)
    for course in range(3):
        z = TOP_Z + 0.056 + course * 0.104
        r = WALL_R - 0.014 * course
        span = (a1 - a0) - 0.12 * max(0, course - 1)
        n = int(round(span * r / L))
        step = span / n
        for k in range(n + (0 if course % 2 == 0 else -1)):
            a = a0 + 0.06 * max(0, course - 1) + step * (k + (0.5 if course % 2 == 0 else 1.0)) + rs.uniform(-0.02, 0.02)
            c = v3((math.cos(a) * r, math.sin(a) * r, z + rs.uniform(-0.006, 0.006)))
            inward = -norm(v3((c[0], c[1], 0.0)))
            tang = norm(np.cross(Z, inward))
            out.append((c, tang, inward, step * r * 0.98, rs.uniform(-0.08, 0.08)))
    return out


def sandbags_field():
    """Sacking (label 0): pillowy bags, slumped and squashed under the course above, a few with a stencilled mark (5)."""
    fd = Field("Sandbags")
    lump = lambda P: F(0.004) * NOISE(P * F(14)) + F(0.0015) * NOISE(P * F(45))
    for i, (c, t, inw, L, tw) in enumerate(bag_specs()):
        R = np.stack([t, inw, Z], 1) @ euler(0, 0, tw)
        fd.add(RoundBox(c, (L * 0.5, 0.1, 0.058), 0.05, R=R, disp=lump, disp_amp=0.005), 0.012)
        fd.add(Ellipsoid(c + v3((0, 0, 0.014)), (L * 0.42, 0.09, 0.054), R=R), 0.02)
        if i % 4 == 1:
            fd.paint(RoundBox(c - inw * 0.1, (0.05, 0.03, 0.022), 0.005, R=R), 5)
    return fd


PLATE_H = 0.5                     # the propped robot plates' height


def plates_field():
    """modern_kit: two salvaged robot armour plates (white, 7: curved shells with a rolled edge, panel lines, scorched
    (5) and dented, torn bolts (9) along one edge) propped against the sandbags, leaning back; the Resistance's amber (6)
    chevron sprayed on each; a black (5) strap round the left one."""
    fd = Field("Plates")
    tex = lambda P: F(0.0007) * NOISE(P * F(40)) + F(0.0012) * NOISE(P * F(9))
    for i, pl in enumerate(PLATES):
        c, R = _frame(pl, (0.2, -0.25)[i])
        tg, inw = R[:, 0], R[:, 1]
        lean = norm(Z * 0.93 - inw * 0.36)                               # leaning back against the wall
        w = (0.2, 0.17)[i]
        base = c + inw * 0.02
        mid = base + lean * (PLATE_H / 2) + Z * 0.004
        nrm = norm(np.cross(tg, lean))
        if nrm @ inw < 0:
            nrm = -nrm
        Rp = np.stack([tg, lean, nrm], 1)
        cc = mid - nrm * 0.25                                            # (the curve's centre behind it)
        def shell(P, cc=cc, Rp=Rp, w=w, mid=mid):
            q = (P - mid.astype(F)) @ Rp.astype(F)
            d = np.sqrt(((P - cc.astype(F)) @ Rp[:, [0, 2]].astype(F)) ** 2 @ np.array([1, 1], F)) - F(0.25)
            region = np.maximum(np.abs(q[:, 0]) - F(w), np.abs(q[:, 1]) - F(PLATE_H / 2))
            return np.maximum(np.abs(d) - F(0.009), region)
        fd.add(Func(shell, mid - 0.4, mid + 0.4, disp=tex, disp_amp=0.0015), 0.006, 7)
        def rim(P, cc=cc, Rp=Rp, w=w, mid=mid):
            q = (P - mid.astype(F)) @ Rp.astype(F)
            d = np.sqrt(((P - cc.astype(F)) @ Rp[:, [0, 2]].astype(F)) ** 2 @ np.array([1, 1], F)) - F(0.25)
            region = np.maximum(np.abs(q[:, 0]) - F(w), np.abs(q[:, 1]) - F(PLATE_H / 2))
            return np.maximum(np.abs(d - F(0.004)) - F(0.012), np.abs(region + F(0.012)) - F(0.012))
        fd.add(Func(rim, mid - 0.4, mid + 0.4), 0.004, 7)
        def pline(P, cc=cc, Rp=Rp, mid=mid, w=w):
            q = (P - mid.astype(F)) @ Rp.astype(F)
            d = np.sqrt(((P - cc.astype(F)) @ Rp[:, [0, 2]].astype(F)) ** 2 @ np.array([1, 1], F)) - F(0.25)
            return np.maximum(np.maximum(np.abs(q[:, 1] - F(0.07)) - F(0.003), np.abs(d - F(0.01)) - F(0.005)), np.abs(q[:, 0]) - F(w - 0.03))
        fd.sub(Func(pline, mid - 0.4, mid + 0.4), 0.0015)
        front = mid + nrm * 0.012
        for d_ in ((-0.08, 0.12), (0.09, -0.15)):
            fd.sub(Sphere(front + tg * d_[0] + lean * d_[1] + nrm * 0.008, 0.02), 0.006)
        def chevron(P, mid=mid, Rp=Rp):
            q = (P - mid.astype(F)) @ Rp.astype(F)
            u, v = q[:, 0], q[:, 1]
            ch = np.abs(v - F(0.02) + np.abs(u) * F(0.95)) - F(0.035)
            return np.maximum(np.maximum(ch, np.abs(u) - F(0.15)), F(-0.002) - q[:, 2])
        fd.paint(Func(chevron, mid - 0.4, mid + 0.4), 6)
        fd.paint(Sphere(front + tg * (w * 0.7) - lean * 0.17, 0.05), 5)                        # scorched
        for k in range(4):
            fd.add(Cylinder(mid + tg * (-w + 0.02) + lean * (-0.16 + 0.1 * k) + nrm * 0.008, 0.011, 0.012, rr=0.003,
                            R=rot_from_axes(z_axis=nrm)), 0.002, 9)
    return fd


# ---------------------------------------------------------------------------------------------- the banner
POLE_H = 1.95


def pole_field():
    """modern_kit: the banner's pole (gunmetal, 9) in a weighted base (a black (5) disc), a crossbar at its top, a finial
    shaped as the Resistance's chevron (amber paint, 6)."""
    fd = Field("Pole")
    c, inw, tg = BANNER
    fd.add(Cylinder(c + Z * 0.03, 0.1, 0.06, rr=0.02), 0.0, 5)
    top = c + Z * POLE_H
    fd.add(RoundCone(c + Z * 0.05, top, 0.017, 0.013), 0.004, 9)
    bar = banner_bar()
    fd.add(RoundCone(bar[0], bar[1], 0.01, 0.01), 0.003, 9)
    for p in bar:
        fd.add(Sphere(p, 0.015), 0.003, 9)
    # the chevron finial
    fd.add(RoundCone(top + Z * 0.02 - tg * 0.04, top + Z * 0.09, 0.012, 0.011), 0.004, 6)
    fd.add(RoundCone(top + Z * 0.02 + tg * 0.04, top + Z * 0.09, 0.012, 0.011), 0.004, 6)
    return fd


BANNER_W, BANNER_H = 0.4, 0.72


def banner_bar():
    """The crossbar's two ends: out from the pole toward him and to his right (so the banner faces the front)."""
    c, inw, tg = BANNER
    top = c + Z * (POLE_H - 0.06)
    d = norm(v3((-1.0, -0.15, 0.0)))
    return top + d * 0.02, top + d * (BANNER_W + 0.06)


def banner_field():
    """Amber cloth (uniform's cloth, label 0) hanging from the crossbar: a long banner with a swallowtail foot, gentle
    folds; the Resistance's chevron in charcoal (5) on it, a charcoal border (5)."""
    fd = Field("Banner")
    a, b = banner_bar()
    along = norm(b - a)
    nrm = norm(np.cross(along, Z))
    if nrm[1] > 0:
        nrm = -nrm                                                        # (facing the front)
    top = a + along * 0.03 - Z * 0.014
    W, H = BANNER_W, BANNER_H
    def cloth(P):
        q = P - top.astype(F)
        u = q @ along.astype(F)
        v = -q[:, 2]
        n = q @ nrm.astype(F)
        wave = F(0.014) * np.sin(u * F(22) + F(0.4)) * np.clip(v / F(0.15), 0, 1) + F(0.005) * np.sin(v * F(14))
        inside = np.maximum(np.maximum(-u, u - F(W)), np.maximum(-v, v - F(H)))
        notch = F(H) - F(0.1) * (F(1) - np.abs(u - F(W * 0.5)) * F(2.0 / W))   # the swallowtail
        return np.maximum(np.maximum(inside, v - notch), np.abs(n - wave) - F(0.006))
    fd.add(Func(cloth, top - 0.7, top + 0.7), 0.0)
    fd.add(RoundCone(top - along * 0.01, top + along * (W + 0.01), 0.013, 0.013), 0.004)   # (the sleeve over the bar)
    def chevron(P):
        q = P - top.astype(F)
        u = q @ along.astype(F) - F(W * 0.5)
        v = -q[:, 2] - F(H * 0.42)
        ch = np.abs(v + np.abs(u) * F(0.95)) - F(0.04)
        return np.maximum(ch, np.abs(u) - F(0.12))
    fd.paint(Func(chevron, top - 0.7, top + 0.7), 5)
    def border(P):
        q = P - top.astype(F)
        u = q @ along.astype(F)
        v = -q[:, 2]
        inner = np.maximum(np.maximum(F(0.028) - u, u - F(W - 0.028)), F(0.05) - v)
        return -inner
    fd.paint(Func(border, top - 0.7, top + 0.7), 5)
    return fd


# ---------------------------------------------------------------------------------------------- the map table
TABLE_H = 0.46                    # the top's height above the deck
TABLE_HALF = (0.3, 0.19)         # (along the tangent, inward)


def table_frame():
    c, R = _frame(TABLE, -0.25)
    return c + Z * TABLE_H, R


def table_field():
    """modern_kit: a pried-off server-rack lid (gunmetal, 9; vent slots, a bent corner) on four black (5) legs braced
    near the floor; a raised rim round the screen, amber (6) edge marks; a little gunmetal box on its corner (a
    projector) with a lens (11)."""
    fd = Field("Table")
    top, R = table_frame()
    hx, hy = TABLE_HALF
    tg, inw = R[:, 0], R[:, 1]
    fd.add(RoundBox(top, (hx, hy, 0.018), 0.008, R=R), 0.0, 9)
    fd.sub(RoundBox(top + Z * 0.016, (hx - 0.03, hy - 0.03, 0.01), 0.004, R=R), 0.003)               # the screen's bed
    for k in range(6):                                                                                 # vents along its side
        fd.sub(RoundBox(top + inw * hy + tg * (-0.15 + 0.06 * k), (0.018, 0.006, 0.006), 0.003, R=R), 0.002)
    for sx in (-1, 1):
        for sy in (-1, 1):
            foot = top + tg * (sx * (hx - 0.04)) + inw * (sy * (hy - 0.04)) - Z * TABLE_H
            fd.add(RoundCone(foot + Z * 0.01, foot + Z * (TABLE_H - 0.01), 0.018, 0.016), 0.004, 5)
            fd.add(Cylinder(foot + Z * 0.008, 0.026, 0.016, rr=0.005), 0.004, 5)
        a = top + tg * (sx * (hx - 0.04)) - inw * (hy - 0.04) - Z * (TABLE_H - 0.1)
        b = top + tg * (sx * (hx - 0.04)) + inw * (hy - 0.04) - Z * (TABLE_H - 0.1)
        fd.add(RoundCone(a, b, 0.01, 0.01), 0.004, 5)
    fd.add(RoundCone(top + tg * -(hx - 0.04) - Z * (TABLE_H - 0.1), top + tg * (hx - 0.04) - Z * (TABLE_H - 0.1), 0.01, 0.01), 0.004, 5)
    for sx in (-1, 1):
        fd.paint(RoundBox(top + tg * (sx * (hx - 0.012)) + Z * 0.012, (0.006, hy - 0.04, 0.012), 0.002, R=R), 6)
    pj = top + tg * (hx - 0.05) - inw * (hy - 0.05) + Z * 0.04
    fd.add(RoundBox(pj, (0.03, 0.03, 0.024), 0.008, R=R), 0.004, 9)
    fd.add(Cylinder(pj + Z * 0.026, 0.013, 0.01, rr=0.003), 0.003, 11)
    return fd


def holo_field():
    """The holo-map (it glows amber): the screen in the table's top, the data center's blocks rising off it in a grid,
    a target ring round one of them."""
    fd = Field("Holo")
    top, R = table_frame()
    hx, hy = TABLE_HALF
    tg, inw = R[:, 0], R[:, 1]
    fd.add(RoundBox(top + Z * 0.012, (hx - 0.034, hy - 0.034, 0.004), 0.003, R=R), 0.0)
    rs = np.random.RandomState(7)
    for i in range(5):
        for j in range(3):
            if (i, j) in ((2, 1), (4, 0)):
                continue
            h = rs.uniform(0.012, 0.05)
            c = top + tg * (-0.17 + 0.085 * i) + inw * (-0.075 + 0.075 * j) + Z * (0.016 + h / 2)
            fd.add(RoundBox(c, (0.026, 0.022, h / 2), 0.004, R=R), 0.0)
    rc = top + tg * (-0.17 + 0.085 * 2) + Z * 0.03
    fd.add(Torus(rc, 0.034, 0.004), 0.0)
    fd.add(RoundCone(rc - Z * 0.012, rc + Z * 0.07, 0.006, 0.003), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the radio on its crate
CRATE_H = 0.2


def radio_frame():
    c, R = _frame(RADIO, 0.35)
    return c + Z * (CRATE_H - 0.004), R


def crate_field():
    """modern_kit: the ammo crate under the radio (gunmetal-black (5) steel, its lid's latch and handles (9), a white (7)
    stencil band); the dead robot's head before him on his right (white (7) shell, cracked open, a dark (5) eye socket,
    torn gunmetal (9) neck joint, an amber (6) X sprayed over its face)."""
    fd = Field("Crate")
    c, R = _frame(RADIO, 0.35)
    b = c + Z * (CRATE_H / 2)
    fd.add(RoundBox(b, (0.22, 0.15, CRATE_H / 2), 0.014, R=R), 0.0, 5)
    fd.add(RoundBox(b + Z * (CRATE_H / 2 - 0.008), (0.226, 0.156, 0.014), 0.007, R=R), 0.003, 5)
    for s in (-1, 1):
        fd.add(Torus(b + R[:, 0] * (s * 0.228) + Z * 0.02, 0.03, 0.007, R=rot_from_axes(z_axis=R[:, 1])), 0.003, 9)
    fd.add(RoundBox(b - R[:, 1] * 0.152 + Z * 0.06, (0.02, 0.007, 0.024), 0.003, R=R), 0.002, 9)
    fd.paint(RoundBox(b - R[:, 1] * 0.155 + Z * -0.02, (0.14, 0.01, 0.016), 0.002, R=R), 7)
    # the dead robot's head
    c, inw, tg = HEAD
    Rh = np.stack([tg, inw, Z], 1) @ euler(0.25, 0.5, 0.6)
    hc = c + Z * 0.1
    fd.add(Ellipsoid(hc, (0.11, 0.12, 0.095), R=Rh), 0.0, 7)
    fd.add(RoundBox(hc + Rh @ v3((0.0, -0.08, 0.0)), (0.085, 0.05, 0.06), 0.03, R=Rh), 0.02, 7)        # its faceplate
    eye = hc + Rh @ v3((0.0, -0.13, 0.012))
    fd.sub(Ellipsoid(eye, (0.055, 0.03, 0.022), R=Rh), 0.006)                                          # the eye slot
    fd.add(Ellipsoid(eye + Rh @ v3((0, 0.015, 0)), (0.045, 0.012, 0.014), R=Rh), 0.004, 5)            # its dead lens
    fd.sub(Chain([hc + Rh @ v3((0.06, -0.05, 0.08)), hc + Rh @ v3((0.03, -0.02, 0.1)), hc + Rh @ v3((0.05, 0.04, 0.09))],
                 [0.006, 0.008, 0.005], k=0.004), 0.003)                                                 # a crack
    fd.add(Cylinder(hc + Rh @ v3((0.0, 0.07, -0.08)), 0.045, 0.05, rr=0.01, R=rot_from_axes(z_axis=Rh @ v3((0, 0.6, -0.8)))), 0.008, 9)
    for k in range(3):
        a = 2 * math.pi * k / 3
        p = hc + Rh @ v3((math.cos(a) * 0.03, 0.09 + 0.02 * math.sin(a), -0.1))
        fd.add(RoundCone(p, p + Rh @ v3((math.cos(a) * 0.03, 0.04, -0.03)), 0.008, 0.005), 0.003, 5)  # torn cables
    for sx in (-1, 1):
        fd.add(Cylinder(hc + Rh @ v3((sx * 0.105, 0.0, 0.01)), 0.03, 0.02, rr=0.006, R=rot_from_axes(z_axis=Rh[:, 0])), 0.006, 9)
    fd.paint(Func(lambda P: np.minimum(_xmark(P, hc, Rh, 1), _xmark(P, hc, Rh, -1)), hc - 0.3, hc + 0.3), 6)
    return fd


def _xmark(P, hc, Rh, s):
    q = (P - hc.astype(F)) @ Rh.astype(F)
    return np.maximum(np.maximum(np.abs(q[:, 0] - F(s) * q[:, 2]) - F(0.012), np.abs(q[:, 0]) - F(0.07)), q[:, 1] + F(0.04))


def radio_field():
    """armory: the field radio (dark (8) case; black (5) knobs, its handset and coiled cord; bright steel (7) catches), a
    small display, its whip antenna (8)."""
    fd = Field("Radio")
    top, R = radio_frame()
    b = top + Z * 0.085 + R[:, 1] * 0.02
    fd.add(RoundBox(b, (0.155, 0.095, 0.085), 0.014, R=R), 0.0, 8)
    fp = b + R[:, 1] * 0.095
    for k, (dx, dz) in enumerate(((-0.08, 0.025), (-0.04, 0.025), (0.0, 0.025), (-0.08, -0.02))):
        fd.add(Cylinder(fp + R[:, 0] * dx + Z * dz + R[:, 1] * 0.008, 0.016, 0.02, rr=0.004, R=rot_from_axes(z_axis=R[:, 1])), 0.003, 5)
    fd.add(RoundBox(fp + R[:, 0] * 0.06 + Z * 0.012 + R[:, 1] * 0.003, (0.055, 0.006, 0.036), 0.004, R=R), 0.002, 7)
    for s in (-1, 1):
        fd.add(RoundBox(b + R[:, 0] * (s * 0.132), (0.006, 0.03, 0.02), 0.003, R=R), 0.002, 7)
    ab = b + R[:, 0] * 0.11 - R[:, 1] * 0.06 + Z * 0.085
    fd.add(Cylinder(ab + Z * 0.015, 0.014, 0.03, rr=0.004), 0.003, 8)
    tip = ab + norm(Z - R[:, 1] * 0.08 + R[:, 0] * 0.05) * 0.85
    fd.add(RoundCone(ab + Z * 0.02, tip, 0.0075, 0.0055), 0.003, 8)
    fd.add(Sphere(tip, 0.01), 0.003, 8)
    hs = top + R[:, 0] * -0.12 + R[:, 1] * 0.1 + Z * 0.022
    Rh = R @ euler(0, 0, 0.5)
    fd.add(RoundBox(hs, (0.02, 0.05, 0.016), 0.012, R=Rh), 0.004, 5)
    for s in (-1, 1):
        fd.add(RoundBox(hs + Rh[:, 1] * (s * 0.05) + Z * 0.012, (0.024, 0.022, 0.016), 0.01, R=Rh), 0.004, 5)
    a, z = hs - Rh[:, 1] * 0.06, fp + R[:, 0] * -0.1 + Z * -0.045
    coil = []
    for i in range(60):
        t = i / 59.0
        p = lerp(a, z, t) + Z * (0.03 * math.sin(math.pi * t))
        ang = 2 * math.pi * 9 * t
        coil.append(p + (R[:, 0] * math.cos(ang) + Z * math.sin(ang)) * 0.008)
    fd.add(Chain(coil, [0.0035] * len(coil), k=0.002), 0.003, 5)
    return fd


def screens_field():
    """The radio's display (it glows amber, dim)."""
    fd = Field("Screens")
    top, R = radio_frame()
    b = top + Z * 0.085 + R[:, 1] * 0.02
    fp = b + R[:, 1] * 0.095
    fd.add(RoundBox(fp + R[:, 0] * 0.06 + Z * 0.012 + R[:, 1] * 0.008, (0.045, 0.003, 0.026), 0.002, R=R), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- cables
def cables_field():
    """modern_kit's black rubber (12): cables from the table round his right side to the radio, from the table to the
    sandbags (back to the data center's sockets), a loose coil by the table; amber-sleeved (6) runs."""
    fd = Field("Cables")
    def run(a0, a1, r0, r1, n=14, wob=0.04, seed=0, rad=0.013, label=12):
        rs = np.random.RandomState(seed)
        pts = []
        for i in range(n):
            t = i / (n - 1.0)
            a = math.radians(a0 + (a1 - a0) * t)
            r = r0 + (r1 - r0) * t + wob * math.sin(t * math.pi * 3 + seed) + rs.uniform(-0.01, 0.01)
            pts.append(v3((math.cos(a) * r, math.sin(a) * r, TOP_Z + rad - 0.002)))
        fd.add(Chain(pts, [rad] * n, k=0.006), 0.004, label)
    run(176, 314, 0.88, 0.92, n=22, wob=0.03, seed=1)
    run(178, 312, 0.94, 0.98, n=22, wob=0.025, seed=2, rad=0.01, label=6)
    run(150, 132, 0.84, 1.0, n=8, wob=0.02, seed=3)
    cc = v3((math.cos(math.radians(186)) * 0.98, math.sin(math.radians(186)) * 0.98, TOP_Z))
    pts = []
    for i in range(40):
        t = i / 39.0
        a = 2 * math.pi * 1.7 * t
        r = 0.06 + 0.018 * t
        pts.append(cc + v3((math.cos(a) * r, math.sin(a) * r, 0.012 + 0.01 * math.sin(a * 0.5) ** 2)))
    fd.add(Chain(pts, [0.01] * len(pts), k=0.004), 0.004, 12)
    return fd


def grass_geometry(seed=0):
    return np.zeros((0, 3)), [], np.zeros((0, 2)), np.zeros(0, dtype=int)


def flower_geometry(seed=0):
    return []


def fields():
    return [("Deck", deck_field(), 0.006), ("Ring", ring_field(), 0.0025), ("Sandbags", sandbags_field(), 0.005),
            ("Plates", plates_field(), 0.004), ("Pole", pole_field(), 0.003), ("Banner", banner_field(), 0.003),
            ("Table", table_field(), 0.003), ("Holo", holo_field(), 0.002), ("Crate", crate_field(), 0.003),
            ("Radio", radio_field(), 0.0025), ("Screens", screens_field(), 0.002), ("Cables", cables_field(), 0.003)]


REGION_PARTS = ("Deck", "Sandbags", "Plates", "Pole", "Banner", "Table", "Crate", "Radio", "Cables")
LOW_TARGETS = {"Deck": 2600, "Ring": 640, "Sandbags": 2400, "Plates": 1400, "Pole": 400, "Banner": 500, "Table": 1200,
               "Holo": 500, "Crate": 1800, "Radio": 1100, "Screens": 40, "Cables": 1400}
KIT = dict(black=(0.05, 0.05, 0.055), red=AMBER, white=WHITE, gunmetal=GUNMETAL, rubber=(0.07, 0.07, 0.075))
MAT_OVERRIDES = {"Deck": ("modern_kit", dict(KIT, name="HQ_PostDeck", base=(0.17, 0.18, 0.2), weave=0.0)),
                 "Sandbags": ("sacking", {"name": "HQ_PostSandbags", "base": (0.46, 0.42, 0.33), "dark": (0.3, 0.27, 0.21)}),
                 "Plates": ("modern_kit", dict(KIT, name="HQ_PostPlates", base=WHITE, weave=0.0, gloss=0.5)),
                 "Pole": ("modern_kit", dict(KIT, name="HQ_PostKit", base=GUNMETAL, weave=0.0)),
                 "Banner": ("uniform", {"name": "HQ_PostBanner", "base": AMBER, "facing": CHARCOAL}),
                 "Table": ("modern_kit", dict(KIT, name="HQ_PostKit", base=GUNMETAL, weave=0.0)),
                 "Crate": ("modern_kit", dict(KIT, name="HQ_PostKit", base=GUNMETAL, weave=0.0)),
                 "Radio": ("armory", {"name": "HQ_PostRadio", "grip": (0.09, 0.09, 0.09)}),
                 "Cables": ("modern_kit", dict(KIT, name="HQ_PostKit", base=GUNMETAL, weave=0.0))}
GLOW = {"Ring": (AMBER_GLOW, 1.0, 0.5), "Holo": (AMBER_GLOW, 1.0, 0.5), "Screens": (AMBER_GLOW, 0.8, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
