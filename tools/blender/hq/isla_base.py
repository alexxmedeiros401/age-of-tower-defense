"""Isla's stand: the end of a weathered timber jetty on a sandy shore. Silver-grey planks on three stringers and round
pilings, a little above the sand; on the jetty's front-left piling a small bronze swivel gun in an iron yoke (her
Broadside's promise) pointing out over the shore; at its front-right an iron mooring bollard with the rope looped round it
and coiled on the planks, its end trailing off the jetty into the sand; behind her on her left a lantern hanging from an
iron arm on a post (its glass glows warm); behind her on her right, in the sand, an iron-bound sea chest, its lid thrown
back, spilling gold coins; scallop shells and a whelk in the sand, two tufts of beach grass; round it all the hero ring:
twelve glowing sea-glass pebbles set in the sand (their own emissive mesh), small white shells round each."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
import kael_base as kb

ground_height = kb.ground_height
ground_field = kb.ground_field
GROUND_TOP = kb.GROUND_TOP
GROUND_R = kb.GROUND_R
TOP_Z = 0.3                        # the planks' top = where she stands
STAND = v3((0.0, 0.0, TOP_Z))
DECK_X, DECK_Y = 0.52, 0.6         # the jetty's end: half its width, half its length
PLANK_T = 0.035
STRINGER_X = (-0.38, 0.0, 0.38)
PILES = [(-0.45, -0.54, 0.1), (0.45, -0.54, 0.2), (-0.45, 0.0, 0.0), (0.45, 0.0, 0.0), (-0.45, 0.54, 0.04)]   # (x, y, rise above the deck)
GUN_POST = v3((0.45, -0.54, TOP_Z + 0.2))          # the swivel gun's post top
GUN_T = GUN_POST + v3((0.0, 0.0, 0.1))              # its trunnions
GUN_D = norm(v3((0.32, -1.0, 0.1)))                 # its bore, out over the shore to the front-left
BOLLARD = v3((-0.34, -0.42, TOP_Z))
COIL = v3((-0.17, -0.45, TOP_Z))
LAMP_POST = v3((0.45, 0.54, 0.0))
LAMP_POST_H = TOP_Z + 0.86
LAMP_C = v3((0.31, 0.41, TOP_Z + 0.6))               # the lantern's middle
CHEST_C = v3((-0.78, 0.42, 0.0))                    # the sea chest, in the sand behind her on her right
CHEST_F = norm(v3((-0.42, -1.0, 0.0)))              # the way its front faces
CHEST_H = (0.17, 0.11, 0.095)                         # half its length, depth, the body's height
RING_R = 1.12
N_GLOW = 12
TUFTS = [v3((0.86, 0.47, 0.0)), v3((0.0, 0.98, 0.0))]


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


# ---------------------------------------------------------------------------------------------- the jetty
def deck_field():
    """Weathered timber: planks across (grain along X, label 10) on three stringers (grain along Y, 0) and round pilings
    (along Z, 11), tarred and weedy where they go into the sand (5); iron nails and the mooring bollard (6)."""
    fd = Field("Deck")
    rs = np.random.RandomState(7)
    n = 11
    pitch = 2 * DECK_Y / n
    for i in range(n):
        y = -DECK_Y + pitch * (i + 0.5)
        x0 = -DECK_X + rs.uniform(-0.02, 0.035)
        x1 = DECK_X + rs.uniform(-0.035, 0.02)
        dz = rs.uniform(-0.004, 0.002)
        tilt = rs.uniform(-0.02, 0.02)
        grain = lambda P: F(0.0018) * NOISE(P * np.array([6.0, 60.0, 60.0], F)) + F(0.0008) * NOISE(P * F(50))
        c = v3(((x0 + x1) / 2, y, TOP_Z - PLANK_T / 2 + dz))
        fd.add(RoundBox(c, ((x1 - x0) / 2, pitch / 2 - 0.007, PLANK_T / 2), 0.007, R=euler(tilt, 0, rs.uniform(-0.01, 0.01)),
                        disp=grain, disp_amp=0.002), 0.0, 10)
        for sx in STRINGER_X:
            fd.add(Sphere(v3((sx + rs.uniform(-0.01, 0.01), y + rs.uniform(-0.02, 0.02), TOP_Z + dz + 0.001)), 0.0065), 0.002, 6)
    for sx in STRINGER_X:
        fd.add(RoundBox(v3((sx, 0.0, TOP_Z - PLANK_T - 0.033)), (0.03, DECK_Y + 0.03, 0.033), 0.006,
                        disp=lambda P: F(0.0015) * NOISE(P * np.array([60.0, 6.0, 60.0], F)), disp_amp=0.002), 0.004, 0)
    for x, y, rise in PILES:
        g = ground_height(x, y)
        top = TOP_Z + rise
        fd.add(RoundCone(v3((x, y, g - 0.08)), v3((x, y, top)), 0.056, 0.052,
                       disp=lambda P: F(0.0025) * NOISE(P * np.array([40.0, 40.0, 5.0], F)) + F(0.001) * NOISE(P * F(60)), disp_amp=0.003), 0.004, 11)
        if rise > 0.05:
            fd.add(Ellipsoid(v3((x, y, top)), (0.05, 0.05, 0.016)), 0.012, 11)
        fd.paint(RoundCone(v3((x, y, g - 0.08)), v3((x, y, g + 0.05)), 0.07, 0.066), 5)
    # the bollard: an iron post with a mushroom head on a bolted plate
    b = BOLLARD
    fd.add(Cylinder(b + v3((0, 0, 0.006)), 0.07, 0.012, rr=0.004), 0.004, 6)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        fd.add(Sphere(b + v3((math.cos(a) * 0.052, math.sin(a) * 0.052, 0.013)), 0.008), 0.002, 6)
    fd.add(RoundCone(b + v3((0, 0, 0.01)), b + v3((0, 0, 0.12)), 0.046, 0.04), 0.01, 6)
    fd.add(Ellipsoid(b + v3((0, 0, 0.13)), (0.066, 0.066, 0.034)), 0.012, 6)
    return fd


# ---------------------------------------------------------------------------------------------- the swivel gun
def cannon_field():
    """A small swivel gun: a bronze barrel (label 9) with reinforcing rings, a swelled muzzle and a cascabel, in an iron
    yoke (8) on the piling, its iron tiller (8) reaching back."""
    fd = Field("Cannon")
    D = GUN_D
    T = GUN_T
    side = norm(np.cross(D, v3((0, 0, 1))))
    up = np.cross(side, D)
    breech, muzzle = T - D * 0.16, T + D * 0.31
    fd.add(RoundCone(breech, muzzle, 0.05, 0.039), 0.0, 9)
    for s, r, w in ((0.0, 0.056, 0.012), (0.18, 0.048, 0.009), (0.36, 0.046, 0.009), (0.47, 0.047, 0.013)):
        fd.add(Torus(breech + D * s, r - 0.004, w * 0.55, R=rot_from_axes(z_axis=D)), 0.004, 9)
    fd.add(Sphere(breech - D * 0.03, 0.03), 0.012, 9)                           # the cascabel's knob
    fd.add(Sphere(breech - D * 0.07, 0.019), 0.008, 9)
    fd.sub(Cylinder(muzzle, 0.021, 0.12, R=rot_from_axes(z_axis=D)), 0.002)     # the bore
    # trunnions and the yoke: a fork down to a pin in the post
    fd.add(RoundCone(T - side * 0.07, T + side * 0.07, 0.016, 0.016), 0.004, 8)
    for s in (-1, 1):
        a = T + side * (s * 0.064)
        fd.add(Chain([a, a - up * 0.05 + side * (s * 0.006), GUN_POST + side * (s * 0.04) + v3((0, 0, 0.03)), GUN_POST + v3((0, 0, 0.02))],
                     [0.012, 0.011, 0.011, 0.014], k=0.006), 0.004, 8)
    fd.add(Cylinder(GUN_POST + v3((0, 0, 0.012)), 0.022, 0.03, rr=0.005), 0.004, 8)
    # the tiller: an iron bar from the breech back toward her, a knob at its end
    t0 = breech - D * 0.05
    t1 = t0 - D * 0.17 + v3((0, 0, -0.05))
    fd.add(Chain([t0, lerp(t0, t1, 0.5) + v3((0, 0, 0.008)), t1], [0.011, 0.01, 0.01], k=0.004), 0.004, 8)
    fd.add(Sphere(t1, 0.016), 0.004, 8)
    return fd


# ---------------------------------------------------------------------------------------------- rope
def coil_points(c, r0, r1, turns, z0, n=None):
    n = n or int(turns * 22)
    out = []
    for i in range(n + 1):
        t = i / n
        a = 2 * math.pi * turns * t
        r = r0 + (r1 - r0) * t
        out.append(c + v3((math.cos(a) * r, math.sin(a) * r, z0)))
    return out


def rope_field():
    """Hemp rope: coiled flat on the planks, led to the bollard and looped twice round its neck, its end trailing off the
    jetty and lying in the sand."""
    fd = Field("Rope")
    R = 0.011
    lay = lambda P: F(0.0016) * np.sin((P[:, 0] + P[:, 1] + P[:, 2]) * F(260))
    pts = coil_points(COIL, 0.024, 0.1, 3.4, R, 80)
    fd.add(Chain(pts, [R] * len(pts), k=0.004, disp=lay, disp_amp=0.002), 0.0)
    pts2 = coil_points(COIL + v3((0.004, -0.004, 0)), 0.045, 0.085, 1.6, R * 2.7, 40)
    fd.add(Chain(pts2, [R] * len(pts2), k=0.004, disp=lay, disp_amp=0.002), 0.004)
    # from the coil's outer end to the bollard, twice round its neck, then off the jetty's side into the sand
    end = pts[-1]
    b = BOLLARD
    neck = 0.046 + R
    lead = [end, lerp(end, b, 0.5) + v3((0, 0, R)), b + v3((neck * 0.9, -0.02, 0.06))]
    fd.add(Chain(lead, [R] * 3, k=0.004, disp=lay, disp_amp=0.002), 0.004)
    for z in (0.055, 0.083):
        fd.add(Torus(b + v3((0, 0, z)), neck, R, disp=lay, disp_amp=0.002), 0.004)
    xs, ys = -DECK_X - 0.01, b[1] + 0.04
    tail = [b + v3((-neck * 0.9, 0.03, 0.07)), v3((xs, ys, TOP_Z + R)), v3((xs - 0.07, ys + 0.02, TOP_Z - 0.08)),
            v3((-0.8, ys + 0.06, ground_height(-0.8, ys) + R * 0.6)), v3((-0.96, ys + 0.2, ground_height(-0.96, ys + 0.2) + R * 0.5))]
    fd.add(Chain(tail, [R] * len(tail), k=0.006, disp=lay, disp_amp=0.002), 0.004)
    return fd


# ---------------------------------------------------------------------------------------------- the lantern
def lantern_field():
    """The post (weathered timber, label 11), an iron arm and hook (6), the lantern: a brass cap, cage and base (7)."""
    fd = Field("Lantern")
    p = LAMP_POST
    g = ground_height(p[0], p[1])
    top = v3((p[0], p[1], LAMP_POST_H))
    fd.add(RoundCone(v3((p[0], p[1], g - 0.08)), top, 0.054, 0.048,
                   disp=lambda P: F(0.0025) * NOISE(P * np.array([40.0, 40.0, 5.0], F)), disp_amp=0.003), 0.0, 11)
    fd.add(Ellipsoid(top, (0.046, 0.046, 0.014)), 0.01, 11)
    fd.paint(RoundCone(v3((p[0], p[1], g - 0.08)), v3((p[0], p[1], g + 0.05)), 0.07, 0.066), 5)
    c = LAMP_C
    hook = v3((c[0], c[1], c[2] + 0.17))
    arm0 = top + v3((0, 0, -0.06))
    fd.add(Chain([arm0 + norm(hook - arm0) * -0.02, lerp(arm0, hook, 0.5) + v3((0, 0, 0.035)), hook + v3((0, 0, 0.012))], [0.009, 0.008, 0.007], k=0.004), 0.004, 6)
    fd.add(Torus(arm0, 0.054, 0.007), 0.004, 6)                                   # its band round the post
    fd.add(Torus(hook + v3((0, 0, -0.022)), 0.016, 0.004, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, 6)   # the ring it hangs from
    fd.add(RoundCone(c + v3((0, 0, 0.075)), c + v3((0, 0, 0.13)), 0.058, 0.014), 0.006, 7)                 # the cap
    fd.add(Torus(c + v3((0, 0, 0.142)), 0.012, 0.004, R=rot_from_axes(z_axis=(1, 0, 0))), 0.002, 7)       # the handle's loop
    fd.add(Cylinder(c + v3((0, 0, -0.072)), 0.052, 0.016, rr=0.005), 0.004, 7)                             # the base
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        o = v3((math.cos(a) * 0.05, math.sin(a) * 0.05, 0))
        fd.add(RoundCone(c + o + v3((0, 0, -0.068)), c + o + v3((0, 0, 0.078)), 0.0065, 0.0065), 0.003, 7)
    fd.add(Torus(c + v3((0, 0, 0.072)), 0.05, 0.0065), 0.003, 7)
    return fd


def lantern_glass_field():
    fd = Field("LanternGlass")
    fd.add(Cylinder(LAMP_C, 0.045, 0.135, rr=0.01), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the sea chest and its gold
def chest_frame():
    Fv = CHEST_F
    L = norm(np.cross(v3((0, 0, 1)), Fv))
    Z = v3((0, 0, 1))
    g = ground_height(CHEST_C[0], CHEST_C[1])
    base = v3((CHEST_C[0], CHEST_C[1], g - 0.02))
    return base, L, Fv, Z


def lid_rot():
    """The lid thrown back about its hinge (the body's back top edge): the rotation, chosen so its front edge goes up."""
    base, L, Fv, Z = chest_frame()
    for ang in (math.radians(108), math.radians(-108)):
        R = axis_angle(L, ang)
        if (R @ Fv)[2] > 0.5:
            return R
    return np.eye(3)


def chest_field():
    """An iron-bound sea chest of stained oak (label 9), two iron bands round it and over its lid (6), brass corners and
    a lock plate (7); the lid thrown back on its hinges."""
    fd = Field("Chest")
    base, L, Fv, Z = chest_frame()
    hl, hd, hh = CHEST_H
    Rb = np.stack([L, Fv, Z], 1)
    c = base + Z * hh
    grain = lambda P: F(0.0012) * NOISE(P * F(60))
    fd.add(RoundBox(c, (hl, hd, hh), 0.012, R=Rb, disp=grain, disp_amp=0.002), 0.0, 9)
    fd.sub(RoundBox(c + Z * 0.03, (hl - 0.018, hd - 0.018, hh), 0.006, R=Rb), 0.004)                     # hollow
    for s in (-1, 1):                                                                                      # iron bands
        fd.add(Inter(RoundBox(c, (hl + 0.004, hd + 0.005, hh + 0.004), 0.014, R=Rb),
                     Func(lambda P, s=s: np.abs((P - c.astype(F)) @ L.astype(F) - F(s * 0.125)) - F(0.013), c - 0.4, c + 0.4), 0.003), 0.003, 6)
        for t in (-1, 1):
            fd.add(Sphere(c + L * (s * (hl - 0.004)) + Fv * (t * (hd - 0.004)) + Z * (hh - 0.004), 0.017), 0.004, 7)   # brass corners
            fd.add(Sphere(c + L * (s * (hl - 0.004)) + Fv * (t * (hd - 0.004)) - Z * (hh - 0.012), 0.016), 0.004, 7)
    fd.add(RoundBox(c + Fv * (hd + 0.004) + Z * (hh - 0.035), (0.032, 0.006, 0.03), 0.004, R=Rb), 0.003, 7)          # lock plate
    fd.add(Sphere(c + Fv * (hd + 0.01) + Z * (hh - 0.04), 0.007), 0.002, 6)
    # the lid, thrown back
    hinge = base + Z * (2 * hh) - Fv * hd
    R = lid_rot()
    lc = hinge + R @ (Fv * hd + Z * 0.032)
    Rl = R @ Rb
    fd.add(Inter(Ellipsoid(lc, (hl + 0.03, hd + 0.03, 0.058), R=Rl), RoundBox(lc, (hl, hd, 0.032), 0.012, R=Rl), 0.01), 0.004, 9)
    fd.sub(RoundBox(lc - (R @ Z) * 0.02, (hl - 0.02, hd - 0.02, 0.02), 0.006, R=Rl), 0.004)
    for s in (-1, 1):
        fd.add(Inter(RoundBox(lc, (hl + 0.004, hd + 0.005, 0.036), 0.014, R=Rl),
                     Func(lambda P, s=s: np.abs((P - lc.astype(F)) @ (R @ L).astype(F) - F(s * 0.125)) - F(0.013), lc - 0.4, lc + 0.4), 0.003), 0.003, 6)
        fd.add(Cylinder(hinge + L * (s * 0.125), 0.012, 0.04, rr=0.004, R=rot_from_axes(z_axis=L)), 0.003, 6)   # hinges
    return fd


def coin_spots(seed=21):
    """(centre, normal) of every coin: heaped in the chest and spilt over its front edge onto the sand."""
    rs = np.random.RandomState(seed)
    base, L, Fv, Z = chest_frame()
    hl, hd, hh = CHEST_H
    out = []
    top = base + Z * (2 * hh)
    for i in range(46):                                         # the heap, mounded above the rim
        u, v = rs.uniform(-1, 1), rs.uniform(-1, 1)
        h = 0.035 * (1 - u * u) * (1 - v * v) + 0.004
        p = top + L * (u * (hl - 0.03)) + Fv * (v * (hd - 0.03)) + Z * (h - 0.012)
        n = norm(Z + L * (-u * 0.3) + Fv * (-v * 0.3) + v3(rs.normal(0, 0.25, 3)))
        out.append((p, n))
    for i in range(16):                                         # spilling over the front edge
        t = i / 15
        p = top + Fv * (hd + 0.012) + L * rs.uniform(-0.1, 0.12) - Z * (t * 2 * hh) + Fv * (0.02 * t)
        out.append((p, norm(Fv + v3(rs.normal(0, 0.4, 3)))))
    for i in range(30):                                         # on the sand in front, in a spreading fan
        t = rs.uniform(0.0, 1.0) ** 0.7
        side = float(np.clip(rs.normal(0, 0.04 + 0.06 * t), -0.11, 0.11))
        q = base + Fv * (hd + 0.04 + 0.3 * t) + L * side
        z = ground_height(q[0], q[1]) + 0.004
        out.append((v3((q[0], q[1], z)), norm(v3((0, 0, 1)) + v3(rs.normal(0, 0.18, 3)))))
    return out


def coins_field():
    """Gold coins (label 0): a heap filling the chest, a stream over its front edge, a spill across the sand."""
    fd = Field("Coins")
    base, L, Fv, Z = chest_frame()
    hl, hd, hh = CHEST_H
    top = base + Z * (2 * hh)
    fd.add(Ellipsoid(top - Z * 0.01, (hl - 0.02, hd - 0.02, 0.04), R=np.stack([L, Fv, Z], 1),
                     disp=lambda P: F(0.004) * NOISE(P * F(50)), disp_amp=0.005), 0.0)
    for p, n in coin_spots():
        fd.add(Cylinder(p, 0.021, 0.0065, rr=0.0025, R=rot_from_axes(z_axis=n)), 0.002)
    return fd


# ---------------------------------------------------------------------------------------------- shells, the hero ring
def _scallop(fd, c, ang, r, label=0, tilt=(0.0, 0.0)):
    """A scallop shell lying in the sand: a ribbed fan, its hinge toward `ang`."""
    d = v3((math.cos(ang), math.sin(ang), 0.0))
    R = euler(tilt[0], tilt[1], ang)
    hinge = c + d * (r * 0.8)
    def ribs(P, hinge=hinge, d=d):
        q = P - hinge.astype(F)
        a = np.arctan2(q @ np.array([-d[1], d[0], 0], F), -(q @ d.astype(F)))
        return F(r * 0.06) * np.abs(np.sin(a * F(9)))
    fd.add(Inter(Ellipsoid(c, (r * 0.95, r, r * 0.34), R=R, disp=ribs, disp_amp=r * 0.07), Plane(c - v3((0, 0, r * 0.05)), (0, 0, -1)), r * 0.05), 0.0, label)
    fd.add(Ellipsoid(hinge, (r * 0.26, r * 0.16, r * 0.12), R=R), r * 0.08, label)


def _whelk(fd, c, d, L, label=0):
    """A whelk: a spiral cone of whorls lying on its side."""
    for k in range(5):
        t = k / 5
        fd.add(Ellipsoid(c + d * (L * t), (L * (0.32 - 0.05 * k),) * 2 + (L * 0.2,), R=rot_from_axes(z_axis=d)), L * 0.06, label)
    fd.add(RoundCone(c + d * (L * 0.8), c + d * (L * 1.2), L * 0.1, L * 0.02), L * 0.05, label)


def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + math.radians(15)
    x, y = math.cos(a) * RING_R, math.sin(a) * RING_R
    return v3((x, y, ground_height(x, y) + 0.004))


def glowmarks_field():
    """The hero ring: twelve rounded pebbles of sea glass (they glow)."""
    fd = Field("Glowmarks")
    for i in range(N_GLOW):
        a = i * 2 * math.pi / N_GLOW + math.radians(15)
        fd.add(Ellipsoid(glow_pos(i), (0.043, 0.035, 0.022), R=euler(0, 0, a + 0.4)), 0.0)
    return fd


def kerb_field():
    """Small white shells round each sea-glass pebble."""
    fd = Field("Kerb")
    rs = np.random.RandomState(83)
    for i in range(N_GLOW):
        c = glow_pos(i)
        for k in range(3):
            a = rs.uniform(0, 2 * math.pi)
            p = c + v3((math.cos(a) * 0.066, math.sin(a) * 0.066, -0.002))
            _scallop(fd, p, rs.uniform(0, 2 * math.pi), rs.uniform(0.018, 0.024))
    return fd


SHELLS = [(v3((0.72, -0.6, 0.0)), 0.042), (v3((0.88, -0.2, 0.0)), 0.034), (v3((-0.58, -0.76, 0.0)), 0.038),
          (v3((0.24, 0.88, 0.0)), 0.03), (v3((0.62, 0.86, 0.0)), 0.036), (v3((-0.5, 0.88, 0.0)), 0.03)]
WHELKS = [(v3((0.12, -0.86, 0.0)), 0.6, 0.09), (v3((0.92, 0.12, 0.0)), 2.4, 0.07)]


def shells_field():
    """Scallop shells and whelks on the sand (label 0 cream; 5 a coral pink on some)."""
    fd = Field("Shells")
    rs = np.random.RandomState(91)
    for k, (p, r) in enumerate(SHELLS):
        c = v3((p[0], p[1], ground_height(p[0], p[1]) + 0.002))
        _scallop(fd, c, rs.uniform(0, 2 * math.pi), r, 5 if k % 3 == 1 else 0, tilt=(rs.uniform(-0.15, 0.15), rs.uniform(-0.15, 0.15)))
    for p, a, L in WHELKS:
        d = v3((math.cos(a), math.sin(a), 0.04))
        c = v3((p[0], p[1], ground_height(p[0], p[1]) + L * 0.18))
        _whelk(fd, c, norm(d), L)
    return fd


def _blocked(c, pad=0.0):
    x, y = c[0], c[1]
    if abs(x) < DECK_X + 0.08 + pad and abs(y) < DECK_Y + 0.08 + pad:
        return True
    base, L, Fv, Z = chest_frame()
    q = v3((x, y, 0)) - v3((base[0], base[1], 0))
    if abs(q @ L) < CHEST_H[0] + 0.08 + pad and -CHEST_H[1] - 0.08 - pad < q @ Fv < CHEST_H[1] + 0.42 + pad:
        return True
    if math.hypot(x - LAMP_POST[0], y - LAMP_POST[1]) < 0.12 + pad:
        return True
    for p, r in SHELLS:
        if math.hypot(x - p[0], y - p[1]) < r + 0.03 + pad:
            return True
    for p, a, L in WHELKS:
        if math.hypot(x - p[0], y - p[1]) < L + 0.03 + pad:
            return True
    for i in range(N_GLOW):
        g = glow_pos(i)
        if math.hypot(x - g[0], y - g[1]) < 0.11 + pad:
            return True
    return False


def pebbles_field():
    fd = Field("Pebbles")
    rs = np.random.RandomState(53)
    n, tries = 0, 0
    while n < 7 and tries < 900:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(0.75, 1.25)
        p = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(p, 0.02):
            continue
        p[2] = ground_height(p[0], p[1]) + 0.008
        fd.add(Stone(p, rs.uniform(0.02, 0.034), seed=700 + n, squash=(1, 1, 0.55), noise=0.06), 0.0)
        n += 1
    return fd


def grass_geometry(seed=59):
    """Two tufts of marram grass: long, thin, arching blades."""
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    for ti, c in enumerate(TUFTS):
        for b in range(16):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.04)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            out = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(out * rs.uniform(0.15, 0.4) + v3((0, 0, 1)))
            L = rs.uniform(0.2, 0.34)
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.016, 0.022), out * rs.uniform(0.5, 1.0) + v3((0, 0, -0.25)), segs=5,
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
    return [("Ground", ground_field(), 0.008), ("Deck", deck_field(), 0.004), ("Cannon", cannon_field(), 0.0024),
            ("Rope", rope_field(), 0.0024), ("Lantern", lantern_field(), 0.0024), ("LanternGlass", lantern_glass_field(), 0.003),
            ("Chest", chest_field(), 0.003), ("Coins", coins_field(), 0.0018), ("Glowmarks", glowmarks_field(), 0.0025),
            ("Kerb", kerb_field(), 0.002), ("Shells", shells_field(), 0.002), ("Pebbles", pebbles_field(), 0.004)]


REGION_PARTS = ("Deck", "Cannon", "Lantern", "Chest", "Shells")
LOW_TARGETS = {"Ground": 1400, "Deck": 4000, "Cannon": 1100, "Rope": 1100, "Lantern": 700, "LanternGlass": 120, "Chest": 1300,
               "Coins": 1700, "Glowmarks": 360, "Kerb": 500, "Shells": 700, "Pebbles": 200}
MAT_OVERRIDES = {"Ground": ("beach_sand", {"name": "HQ_BeachSand"}),
                 "Deck": ("timber", {"name": "HQ_JettyTimber"}),
                 "Cannon": ("armory", {"name": "HQ_SwivelGun"}),
                 "Rope": ("cord", {}),
                 "Lantern": ("timber", {"name": "HQ_LanternPost"}),
                 "Chest": ("timber", {"name": "HQ_SeaChest"}),
                 "Coins": ("gold", {"name": "HQ_Coins"}),
                 "Kerb": ("bone", {"name": "HQ_ShellsWhite"}),
                 "Shells": ("terracotta", {"name": "HQ_Shells", "base": (0.93, 0.87, 0.76), "paint": (0.94, 0.6, 0.5)}),
                 "Pebbles": ("stone", {"name": "HQ_Pebble", "scale": 0.3})}
GLOW = {"Glowmarks": ((0.3, 0.82, 1.0), 1.0, 0.5), "LanternGlass": ((1.0, 0.72, 0.3), 1.0, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
