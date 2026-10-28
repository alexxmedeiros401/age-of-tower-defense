"""Unit Zero's stand: a Resistance repair bay inside the robots' data center. A round platform of steel floor grates
(bar gratings in a charcoal frame, a band of amber-and-black hazard striping round its side) on a deck of dark steel
floor plates; the hero ring of twelve amber marker lights in steel bezels in its rim (their own emissive mesh).
Behind him a steel gantry (two charcoal I-beam posts on braced feet, a beam across the top with a trolley) and its
chain hoist (an amber-painted chain block, its hand chain looped down, the load chain to a hook with a spare white
robot plate hanging from it, sprayed with an amber chevron). Spare robot plates sprayed amber lean against the left
post's foot; on his right, forward, an oil drum (an amber band, a dented lid) and an oil can lying by it in a dark
stain; on his left a welder's cart: two gas bottles (charcoal and steel, brass valves) chained to it, the welding set
on its deck, the torch on its hose coiled over the floor plates, a welding mask hung on the bottles."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Inter, Shell, Lock, lerp

GROUND_R = 1.32
GROUND_TOP = 0.08
PAD_R = 0.9                        # the grating platform
TOP_Z = 0.18                       # its top = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
RING_R = 0.82                      # the marker lights, in its rim
N_GLOW = 12

# mats.android labels
SUIT, FRAME, CHAR, SEAM, CLOTH, TAPE, STEEL, GLASS, FACE, WHITE, ORANGE, RUBBER, AMBER = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16


def ground_height(x, y):
    return GROUND_TOP


def _placed(angle_deg, r, turn=0.0):
    """A prop's place round him: (centre on the ground, its inward direction (toward him), its tangent)."""
    a = math.radians(angle_deg)
    c = v3((math.cos(a) * r, math.sin(a) * r, GROUND_TOP))
    inward = euler(0, 0, math.radians(turn)) @ -norm(v3((c[0], c[1], 0.0)))
    tang = norm(np.cross(v3((0, 0, 1)), inward))
    return c, inward, tang


def _frame_of(pl):
    c, inw, tg = pl
    return c, inw, tg, np.stack([tg, inw, v3((0, 0, 1))], 1)


DRUM = _placed(-38.0, 1.08, 0.0)
CAN = _placed(-62.0, 1.12, 40.0)
WELDER = _placed(205.0, 1.06, -10.0)
PLATES = _placed(118.0, 1.1, 10.0)
POST_X, POST_Y = 0.66, 0.96        # the gantry's posts (x = +-POST_X)
BEAM_Z = 2.3                        # the beam's top
HOIST_X = -0.26                     # the chain block hangs here on the beam (behind his right shoulder)
HOOK_Z = 1.42


# ---------------------------------------------------------------------------------------------- the deck, the platform
def ground_field():
    """Dark steel floor plates (charcoal 6) on a low round slab: seams between square plates (7), bolts at their
    corners (steel 10), an oil stain (7) by the drum."""
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        dx = r - F(GROUND_R)
        dz = np.maximum(P[:, 2] - F(GROUND_TOP), F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.025), 0), np.maximum(dz + F(0.025), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.025), dz + F(0.025)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.025)
    rough = lambda P: F(0.0008) * NOISE(P * F(60))
    fd.add(Func(disc, (-1.45, -1.45, -0.2), (1.45, 1.45, 0.2), disp=rough, disp_amp=0.001), 0.0, CHAR)
    T = 0.44
    def seams(P):
        u, v = P[:, 0] + F(0.1), P[:, 1] + F(0.07)
        su = np.abs(u - F(T) * np.floor(u / F(T) + F(0.5))) - F(0.004)
        sv = np.abs(v - F(T) * np.floor(v / F(T) + F(0.5))) - F(0.004)
        return np.maximum(np.minimum(su, sv), F(GROUND_TOP - 0.006) - P[:, 2])
    lo, hi = (-1.45, -1.45, GROUND_TOP - 0.03), (1.45, 1.45, GROUND_TOP + 0.03)
    fd.sub(Func(seams, lo, hi), 0.0015)
    fd.paint(Func(lambda P: seams(P) - F(0.004), lo, hi), SEAM)
    # bolts near the plates' corners (outside the platform)
    for i in range(-3, 4):
        for j in range(-3, 4):
            for di, dj in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                x = -0.1 + i * T + di * (T / 2 - 0.035)
                y = -0.07 + j * T + dj * (T / 2 - 0.035)
                r = math.hypot(x, y)
                if PAD_R + 0.05 < r < GROUND_R - 0.05:
                    fd.add(Cylinder((x, y, GROUND_TOP), 0.011, 0.01, rr=0.003), 0.002, STEEL)
    fd.paint(Ellipsoid(DRUM[0] + v3((0.06, -0.1, 0.0)), (0.22, 0.15, 0.05), R=euler(0, 0, 0.4),
                       disp=lambda P: F(0.025) * NOISE(P * F(12)), disp_amp=0.025), SEAM)
    return fd


def _grate_d(P):
    """< 0 in the grating's slots: long bars across (along x), slots 0.07 x 0.014 in rows."""
    u, v = P[:, 0], P[:, 1]
    su = np.abs(u - F(0.085) * np.floor(u / F(0.085) + F(0.5))) - F(0.034)
    sv = np.abs(v - F(0.03) * np.floor(v / F(0.03) + F(0.5))) - F(0.0075)
    return np.maximum(su, sv)


GRATE_R = PAD_R - 0.13              # the grating inside the platform's frame


def plates_field():
    """The platform: a charcoal frame (6) round a steel bar grating (5, gunmetal), cross beams under it showing through
    the slots; a hazard band round its side (amber 16 and black rubber 15); a ring of steel kerb plates round the
    grating with the marker lights' bezels."""
    fd = Field("Plates")
    z0 = GROUND_TOP - 0.04
    def slab(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        d_r = r - F(PAD_R)
        d_z = np.maximum(P[:, 2] - F(TOP_Z), F(z0) - P[:, 2])
        cham = (r - F(PAD_R) + P[:, 2] - F(TOP_Z) + F(0.022)) * F(0.7071)
        q = np.stack([np.maximum(d_r + F(0.006), 0), np.maximum(d_z + F(0.006), 0)], 1)
        box = np.minimum(np.maximum(d_r + F(0.006), d_z + F(0.006)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.006)
        return np.maximum(box, cham)
    B = (-1.0, -1.0, z0 - 0.03), (1.0, 1.0, TOP_Z + 0.03)
    fd.add(Func(slab, *B), 0.0, CHAR)
    # the grating: the slots cut 2 cm into the top inside the frame
    def slots(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.maximum(_grate_d(P), r - F(GRATE_R)), F(TOP_Z - 0.02) - P[:, 2])
    fd.sub(Func(slots, (-0.9, -0.9, TOP_Z - 0.04), (0.9, 0.9, TOP_Z + 0.02)), 0.0015)
    fd.paint(Func(lambda P: np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(GRATE_R + 0.004), *B), FRAME)
    fd.paint(Func(lambda P: np.maximum(np.maximum(_grate_d(P) + F(0.002), np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(GRATE_R)),
                                       P[:, 2] - F(TOP_Z - 0.008)), *B), SEAM)
    # the frame's seam round the grating, radial seams across the frame
    fd.sub(Func(lambda P: np.maximum(np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(GRATE_R + 0.004)) - F(0.004),
                                     F(TOP_Z - 0.006) - P[:, 2]), *B), 0.001)
    for k in range(6):
        a = math.radians(30 + 60 * k)
        d = v3((math.cos(a), math.sin(a), 0))
        fd.sub(RoundCone(d * (GRATE_R + 0.01) + v3((0, 0, TOP_Z)), d * (PAD_R - 0.01) + v3((0, 0, TOP_Z)), 0.004), 0.001)
    # the hazard band round the side
    def band(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(F(PAD_R - 0.03) - r, np.maximum(P[:, 2] - F(TOP_Z - 0.028), F(GROUND_TOP + 0.005) - P[:, 2]))
    def hazard(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        s = np.sin((a * F(PAD_R) + P[:, 2]) * F(2 * math.pi / 0.12))
        return np.maximum(band(P), -s * F(0.01))
    fd.paint(Func(band, (-1, -1, 0.0), (1, 1, TOP_Z)), RUBBER)
    fd.paint(Func(hazard, (-1, -1, 0.0), (1, 1, TOP_Z)), AMBER)
    return fd


def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + math.radians(15)
    return v3((math.cos(a) * RING_R, math.sin(a) * RING_R, TOP_Z + 0.004))


def rim_field():
    """The marker lights' steel bezels (10), with black screws (15)."""
    fd = Field("Rim")
    for i in range(N_GLOW):
        c = glow_pos(i)
        fd.add(Torus(c + v3((0, 0, -0.002)), 0.031, 0.008), 0.0, STEEL)
        fd.add(Cylinder(c + v3((0, 0, -0.008)), 0.039, 0.01, rr=0.004), 0.004, STEEL)
        for k in range(3):
            a = 2 * math.pi * k / 3 + i
            fd.add(Sphere(c + v3((math.cos(a) * 0.033, math.sin(a) * 0.033, -0.002)), 0.0045), 0.001, RUBBER)
    return fd


def glowmarks_field():
    fd = Field("Glowmarks")
    for i in range(N_GLOW):
        fd.add(Ellipsoid(glow_pos(i), (0.024, 0.024, 0.011)), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the gantry and its hoist
def _ibeam(fd, a, b, w, h, t, label, up=(0, 0, 1)):
    """An I-beam from a to b: flanges `w` wide across `up`'s normal, `h` deep along `up`, `t` thick."""
    a, b = v3(a), v3(b)
    z = norm(b - a)
    y = norm(v3(up) - z * float(v3(up) @ z))
    x = np.cross(y, z)
    R = np.stack([x, y, z], 1)
    c = (a + b) / 2
    L = float(np.linalg.norm(b - a)) / 2
    for s in (-1, 1):
        fd.add(RoundBox(c + y * (s * (h / 2 - t / 2)), (w / 2, t / 2, L), 0.004, R=R), 0.004, label)
    fd.add(RoundBox(c, (t / 2, h / 2, L), 0.003, R=R), 0.004, label)


def gantry_field():
    """The gantry (charcoal 6 I-beams): two posts on braced feet (steel base plates 10 bolted to the deck), the beam
    across the top with end plates; an amber stripe (16) up each post; the trolley (gunmetal 5) on the beam."""
    fd = Field("Gantry")
    for sx in (-1, 1):
        x = sx * POST_X
        foot = v3((x, POST_Y, GROUND_TOP))
        _ibeam(fd, foot + v3((0, 0, 0.02)), v3((x, POST_Y, BEAM_Z - 0.02)), 0.09, 0.1, 0.014, CHAR, up=(1, 0, 0))
        fd.add(RoundBox(foot + v3((0, 0, 0.01)), (0.12, 0.14, 0.01), 0.004), 0.004, STEEL)
        for dx in (-1, 1):
            for dy in (-1, 1):
                fd.add(Cylinder(foot + v3((dx * 0.09, dy * 0.11, 0.022)), 0.012, 0.012, rr=0.003), 0.002, STEEL)
        # braces: a diagonal strut from up the post down to the deck, toward the middle line behind him
        for dy in (-1, 1):
            a = v3((x, POST_Y, 0.62))
            b = v3((x, POST_Y + dy * 0.24, GROUND_TOP + 0.02))
            if dy < 0:
                b = v3((x + sx * 0.0, POST_Y - 0.2, GROUND_TOP + 0.02))
            fd.add(RoundBox((a + b) / 2, (0.02, 0.012, float(np.linalg.norm(b - a)) / 2), 0.004, R=rot_from_axes(z_axis=b - a, x_axis=(1, 0, 0))), 0.004, CHAR)
            fd.add(RoundBox(b, (0.04, 0.05, 0.01), 0.003), 0.003, STEEL)
        fd.paint(Func(lambda P, x=x: np.maximum(np.maximum(np.abs(P[:, 0] - F(x)) - F(0.06), np.abs(P[:, 1] - F(POST_Y)) - F(0.06)),
                                                np.maximum(np.abs(P[:, 2] - F(1.4)) - F(0.5), F(POST_Y) - P[:, 1] - F(0.035))),
                      (x - 0.1, POST_Y - 0.1, 0.8), (x + 0.1, POST_Y + 0.1, 2.0)), AMBER)
        fd.add(RoundBox((x, POST_Y, BEAM_Z + 0.008), (0.07, 0.07, 0.012), 0.004), 0.004, STEEL)
    _ibeam(fd, v3((-POST_X - 0.06, POST_Y, BEAM_Z - 0.06)), v3((POST_X + 0.06, POST_Y, BEAM_Z - 0.06)), 0.1, 0.12, 0.014, CHAR, up=(0, 0, 1))
    # the trolley on the beam's lower flange
    t = v3((HOIST_X, POST_Y, BEAM_Z - 0.12))
    fd.add(RoundBox(t + v3((0, 0, -0.01)), (0.07, 0.075, 0.025), 0.01), 0.004, FRAME)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fd.add(Cylinder(t + v3((sx * 0.04, sy * 0.062, 0.012)), 0.022, 0.012, rr=0.004, R=rot_from_axes(z_axis=(0, 1, 0))), 0.002, STEEL)
    return fd


def hoist_field():
    """The chain block (amber-painted 16, a charcoal cover 6) hanging from the trolley, its hand chain (steel 10) looped
    down beside it, the load chain down to the hook (gunmetal 5), and on the hook a spare white robot plate (13, an
    orange trim band 14, sprayed with an amber chevron) hung by a steel ring."""
    fd = Field("Hoist")
    t = v3((HOIST_X, POST_Y, BEAM_Z - 0.155))
    blk = t + v3((0, 0, -0.12))
    fd.add(RoundCone(t, blk, 0.02, 0.02), 0.004, FRAME)
    fd.add(RoundBox(blk, (0.07, 0.06, 0.08), 0.035), 0.01, AMBER)
    fd.add(Cylinder(blk + v3((0, -0.06, 0)), 0.065, 0.03, rr=0.008, R=rot_from_axes(z_axis=(0, 1, 0))), 0.006, CHAR)
    # the hand chain: a long loop down the block's side
    hc = blk + v3((0.0, -0.085, 0.0))
    for s in (-1, 1):
        pts = [hc + v3((s * 0.03, 0, 0)), hc + v3((s * 0.035, -0.01, -0.4)), hc + v3((s * 0.02, -0.01, -0.75))]
        fd.add(Chain(pts, [0.008] * 3, k=0.004, disp=lambda P: F(0.0025) * np.sin(P[:, 2] * F(260)), disp_amp=0.003), 0.003, STEEL)
    fd.add(Torus(hc + v3((0, -0.01, -0.76)), 0.02, 0.008, R=rot_from_axes(z_axis=(0, 1, 0))), 0.003, STEEL)
    # the load chain and the hook
    top = blk + v3((0, 0, -0.08))
    hook = v3((HOIST_X, POST_Y, HOOK_Z))
    fd.add(Chain([top, hook + v3((0, 0, 0.05))], [0.011, 0.011], disp=lambda P: F(0.003) * np.sin(P[:, 2] * F(220)), disp_amp=0.003), 0.004, FRAME)
    fd.add(RoundBox(hook + v3((0, 0, 0.065)), (0.03, 0.02, 0.03), 0.01), 0.004, FRAME)
    hk = [hook + v3((0, 0, 0.04)), hook + v3((0, 0, -0.02)), hook + v3((0.0, -0.04, -0.055)), hook + v3((0, -0.075, -0.03)),
          hook + v3((0, -0.07, 0.0))]
    fd.add(Chain(hk, [0.014, 0.014, 0.013, 0.011, 0.008], k=0.006), 0.004, FRAME)
    # the spare plate on the hook: a curved white plate (a robot's pauldron shell), hung by a ring through its edge
    ring_c = hook + v3((0, -0.045, -0.06))
    fd.add(Torus(ring_c, 0.03, 0.007, R=rot_from_axes(z_axis=(1, 0, 0))), 0.003, STEEL)
    pc = ring_c + v3((0.0, -0.02, -0.3))
    sph = Ellipsoid(pc + v3((0, 0.17, 0)), (0.2, 0.2, 0.24))
    cut = Func(lambda P: np.maximum(P[:, 1] - F(pc[1] + 0.04), np.abs(P[:, 2] - F(pc[2])) - F(0.24)), pc - 0.4, pc + 0.4)
    fd.add(Inter(Shell(sph, 0.0, 0.018), cut, 0.01), 0.004, WHITE)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(pc[2] - 0.17)) - F(0.02), pc - 0.4, pc + 0.4), ORANGE)
    def chev(P):
        a = P[:, 0] - F(pc[0])
        z = P[:, 2] - F(pc[2])
        c = np.abs(z - F(-0.02) - np.abs(a) * F(0.7)) - F(0.03)
        return np.maximum(np.maximum(c, np.abs(a) - F(0.17)), P[:, 1] - F(pc[1] + 0.02))
    fd.paint(Func(chev, pc - 0.4, pc + 0.4), AMBER)
    fd.sub(Sphere(pc + v3((0.07, -0.05, 0.06)), 0.04), 0.02)
    return fd


def spares_field():
    """Spare robot plates (white 13, orange trim 14) sprayed with amber chevrons (16), leaning against the left post's
    foot; a crate of bolts (charcoal 6)."""
    fd = Field("Spares")
    c, inw, tg, R = _frame_of(PLATES)
    for k, (o, tilt, rot, w, h) in enumerate(((-0.1, 0.3, 0.1, 0.17, 0.24), (0.14, 0.42, -0.2, 0.15, 0.2))):
        Rp = R @ euler(tilt, 0, rot)
        pc = c + tg * o + inw * (-0.02 + 0.05 * k) + v3((0, 0, h * math.cos(tilt) * 0.95))
        n = Rp[:, 1]
        sph = Ellipsoid(pc + n * 0.3, (w * 1.6, 0.3, h * 1.6), R=Rp)
        def box(P, pc=pc, Rp=Rp, w=w, h=h):
            q = (P - pc.astype(F)) @ Rp.astype(F)
            return np.maximum(np.abs(q[:, 0]) - F(w), np.abs(q[:, 2]) - F(h))
        fd.add(Inter(Shell(sph, 0.0, 0.02), Func(box, pc - 0.4, pc + 0.4), 0.012), 0.004, WHITE)
        fd.paint(Func(lambda P, pc=pc, Rp=Rp, h=h: np.abs(((P - pc.astype(F)) @ Rp.astype(F))[:, 2] + F(h - 0.04)) - F(0.018), pc - 0.4, pc + 0.4), ORANGE)
        def chev(P, pc=pc, Rp=Rp, w=w):
            q = (P - pc.astype(F)) @ Rp.astype(F)
            cc = np.abs(q[:, 2] - F(0.02) - np.abs(q[:, 0]) * F(0.7)) - F(0.03)
            return np.maximum(cc, np.abs(q[:, 0]) - F(w - 0.02))
        fd.paint(Func(chev, pc - 0.4, pc + 0.4), AMBER)
    cb = c + tg * 0.36 + inw * 0.06 + v3((0, 0, 0.07))
    fd.add(RoundBox(cb, (0.1, 0.07, 0.07), 0.01, R=R @ euler(0, 0, 0.3)), 0.004, CHAR)
    fd.sub(RoundBox(cb + v3((0, 0, 0.06)), (0.085, 0.055, 0.04), 0.006, R=R @ euler(0, 0, 0.3)), 0.003)
    rs = np.random.RandomState(5)
    for k in range(9):
        b = cb + R @ euler(0, 0, 0.3) @ v3((rs.uniform(-0.07, 0.07), rs.uniform(-0.04, 0.04), 0.045))
        fd.add(Cylinder(b, 0.013, 0.014, rr=0.004, R=euler(*rs.uniform(-0.5, 0.5, 3))), 0.002, STEEL)
    return fd


# ---------------------------------------------------------------------------------------------- the oil drum and can
def oil_field():
    """An oil drum (charcoal 6, an amber band 16 and stencil, rolling hoops, a dented lid with a steel bung) and an oil
    can (gunmetal 5, an orange cap 14, its spout) lying beside it."""
    fd = Field("Oil")
    c, inw, tg, R = _frame_of(DRUM)
    H, r = 0.4, 0.15
    dc = c + v3((0, 0, H / 2 + 0.002))
    fd.add(Cylinder(dc, r, H, rr=0.012), 0.0, CHAR)
    for z in (-0.1, 0.1):
        fd.add(Torus(dc + v3((0, 0, z)), r + 0.002, 0.007), 0.004, CHAR)
    fd.add(Torus(dc + v3((0, 0, H / 2 - 0.004)), r - 0.004, 0.008), 0.003, CHAR)
    fd.sub(Cylinder(dc + v3((0, 0, H / 2 + 0.006)), r - 0.015, 0.02, rr=0.004), 0.003)
    fd.add(Cylinder(dc + v3((0.06, 0.02, H / 2 - 0.004)), 0.022, 0.012, rr=0.003), 0.002, STEEL)
    fd.sub(Sphere(dc + v3((-0.05, -0.04, H / 2 + 0.05)), 0.06), 0.02)
    fd.paint(Func(lambda P: np.abs(P[:, 2] - F(dc[2] + 0.02)) - F(0.04), dc - 0.3, dc + 0.3), AMBER)
    fd.paint(Func(lambda P: np.maximum(np.maximum(np.abs(P[:, 2] - F(dc[2] + 0.02)) - F(0.016),
                                                  np.abs((P - dc.astype(F)) @ tg.astype(F)) - F(0.05)), (P - dc.astype(F)) @ inw.astype(F) - F(0.05)),
                  dc - 0.3, dc + 0.3), CHAR)
    c2, i2, t2, R2 = _frame_of(CAN)
    cc = c2 + v3((0, 0, 0.06))
    Rc = R2 @ euler(0, math.radians(90), 0)
    fd.add(RoundBox(cc, (0.06, 0.09, 0.11), 0.03, R=Rc), 0.0, FRAME)
    fd.add(RoundBox(cc + Rc @ v3((0, 0, 0.115)), (0.03, 0.05, 0.012), 0.008, R=Rc), 0.006, FRAME)
    sp0 = cc + Rc @ v3((0.0, 0.05, 0.12))
    fd.add(Chain([sp0, sp0 + Rc @ v3((0, 0.06, 0.06)), sp0 + Rc @ v3((0, 0.08, 0.15))], [0.012, 0.009, 0.006], k=0.004), 0.004, STEEL)
    fd.add(Cylinder(cc + Rc @ v3((0, -0.04, 0.12)), 0.022, 0.025, rr=0.005, R=Rc), 0.003, ORANGE)
    return fd


# ---------------------------------------------------------------------------------------------- the welder's cart
def welder_field():
    """A welder's cart (gunmetal 5, two rubber wheels): two gas bottles (charcoal 6 and steel 10, brass-coloured amber
    valves 16) chained to its back, the welding set on its deck (charcoal, a steel panel, orange dials 14), the torch's
    hose (rubber 15) coiled over the floor and the torch; a welding mask (charcoal, dark glass 11) hung on a bottle."""
    fd = Field("Welder")
    c, inw, tg, R = _frame_of(WELDER)
    base = c + v3((0, 0, 0.03))
    fd.add(RoundBox(base + v3((0, 0, 0.03)), (0.2, 0.12, 0.012), 0.006, R=R), 0.0, FRAME)
    for s in (-1, 1):
        fd.add(Cylinder(base + tg * (s * 0.17) - inw * 0.08 + v3((0, 0, 0.03)), 0.05, 0.035, rr=0.012, R=rot_from_axes(z_axis=tg)), 0.004, RUBBER)
    # the bottles at its back (outer side)
    for k, (o, lab, h) in enumerate(((-0.08, CHAR, 0.62), (0.07, STEEL, 0.56))):
        bc = base - inw * 0.07 + tg * o + v3((0, 0, 0.05 + h / 2))
        fd.add(Cylinder(bc, 0.062, h, rr=0.05), 0.006, lab)
        fd.add(RoundCone(bc + v3((0, 0, h / 2 - 0.01)), bc + v3((0, 0, h / 2 + 0.05)), 0.024, 0.018), 0.006, AMBER)
        fd.add(Cylinder(bc + v3((0, 0, h / 2 + 0.035)), 0.025, 0.012, rr=0.004, R=rot_from_axes(z_axis=tg)), 0.003, AMBER)
    fd.add(Torus(base - inw * 0.07 + v3((0, 0, 0.45)), 0.14, 0.006, R=np.diag([1.0, 0.55, 1.0])), 0.003, STEEL)
    # the handle frame up the back
    for s in (-1, 1):
        a = base - inw * 0.13 + tg * (s * 0.17)
        fd.add(RoundCone(a + v3((0, 0, 0.03)), a + v3((0, 0, 0.72)), 0.012), 0.004, FRAME)
    fd.add(RoundCone(base - inw * 0.13 + tg * -0.17 + v3((0, 0, 0.72)), base - inw * 0.13 + tg * 0.17 + v3((0, 0, 0.72)), 0.012), 0.004, FRAME)
    # the welding set on the deck's front
    ws = base + inw * 0.05 + v3((0, 0, 0.13))
    fd.add(RoundBox(ws, (0.15, 0.06, 0.09), 0.015, R=R), 0.004, CHAR)
    fd.add(RoundBox(ws + inw * 0.06, (0.11, 0.008, 0.06), 0.004, R=R), 0.003, STEEL)
    for s in (-1, 1):
        fd.add(Cylinder(ws + inw * 0.068 + tg * (s * 0.05) + v3((0, 0, 0.015)), 0.018, 0.016, rr=0.004, R=rot_from_axes(z_axis=inw)), 0.002, ORANGE)
    # the hose: from the set over the deck's edge, a coil on the floor, the torch at its end
    h0 = ws + inw * 0.065 + tg * -0.1 + v3((0, 0, -0.05))
    f = ground_height(0, 0) + 0.014
    pts = [h0, h0 + inw * 0.06 + v3((0, 0, -0.05)), c + inw * 0.24 + tg * -0.12 + v3((0, 0, f - c[2]))]
    for k in range(9):
        a = 2 * math.pi * k / 8 * 1.1
        pts.append(c + inw * (0.3 + 0.08 * math.cos(a)) + tg * (-0.0 + 0.11 * math.sin(a)) + v3((0, 0, f - c[2] + 0.014 * (k % 2))))
    fd.add(Chain(pts, [0.012] * len(pts), k=0.012), 0.004, RUBBER)
    tp = pts[-1]
    td = norm(tg * 0.8 + inw * 0.4)
    fd.add(RoundCone(tp, tp + td * 0.13, 0.016, 0.014), 0.006, FRAME)
    fd.add(RoundCone(tp + td * 0.13, tp + td * 0.2 + v3((0, 0, -0.012)), 0.008, 0.006), 0.004, STEEL)
    # the mask hung on the charcoal bottle's front
    mc = base - inw * 0.0 + tg * -0.08 + v3((0, 0, 0.5))
    Rm = R @ euler(-0.15, 0, 0)
    fd.add(Inter(Shell(Ellipsoid(mc - inw * 0.06, (0.1, 0.09, 0.13), R=Rm), 0.0, 0.012),
                 Func(lambda P, mc=mc: (P - mc.astype(F)) @ (-inw).astype(F) - F(0.02), mc - 0.3, mc + 0.3), 0.006), 0.004, CHAR)
    fd.add(RoundBox(mc + inw * 0.033 + v3((0, 0, 0.02)), (0.05, 0.006, 0.025), 0.004, R=Rm), 0.003, GLASS)
    return fd


def cables_field():
    """A black cable (15) from the welding set across the deck to the gantry's right post."""
    fd = Field("Cables")
    c, inw, tg, R = _frame_of(WELDER)
    a = c + inw * 0.05 + tg * 0.12 + v3((0, 0, 0.1))
    pts = [a, a + v3((0, 0, -0.09)) - inw * -0.03]
    for k in range(6):
        ang = math.radians(195 - 13 * k)
        r = 1.0 if k < 5 else 0.98
        pts.append(v3((math.cos(ang) * r, math.sin(ang) * r, GROUND_TOP + 0.012)))
    pts.append(v3((-POST_X + 0.0, POST_Y - 0.13, GROUND_TOP + 0.012)))
    pts.append(v3((-POST_X, POST_Y - 0.05, GROUND_TOP + 0.18)))
    fd.add(Chain(pts, [0.011] * len(pts), k=0.03), 0.0, RUBBER)
    return fd


# ---------------------------------------------------------------------------------------------- (no grass indoors)
def grass_geometry(seed=0):
    """No grass in the data center."""
    return np.zeros((0, 3)), [], np.zeros((0, 2)), np.zeros(0, int)


def flower_geometry(seed=0):
    return []


def fields():
    return [("Ground", ground_field(), 0.006), ("Plates", plates_field(), 0.0026), ("Rim", rim_field(), 0.0022),
            ("Glowmarks", glowmarks_field(), 0.002), ("Gantry", gantry_field(), 0.0034), ("Hoist", hoist_field(), 0.0026),
            ("Spares", spares_field(), 0.003), ("Oil", oil_field(), 0.0026), ("Welder", welder_field(), 0.0026),
            ("Cables", cables_field(), 0.003)]


REGION_PARTS = ("Ground", "Plates", "Rim", "Gantry", "Hoist", "Spares", "Oil", "Welder", "Cables")
LOW_TARGETS = {"Ground": 1500, "Plates": 3400, "Rim": 900, "Glowmarks": 300, "Gantry": 1700, "Hoist": 1300, "Spares": 1100,
               "Oil": 1200, "Welder": 1900, "Cables": 300}
BASE_KW = dict(suit=(0.12, 0.12, 0.14), graphite=(0.24, 0.25, 0.27), navy=(0.15, 0.155, 0.17), steel=(0.56, 0.58, 0.62),
               white=(0.86, 0.86, 0.83), orange=(0.95, 0.36, 0.07), yellow=(1.0, 0.64, 0.14), wear=1.5)
MAT_OVERRIDES = {nm: ("android", dict(BASE_KW, name="HQ_ZeroBay" + nm)) for nm in REGION_PARTS}
GLOW = {"Glowmarks": ((1.0, 0.64, 0.2), 1.0, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
