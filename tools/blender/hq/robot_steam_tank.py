"""Steam Tank, HQ: the Industrial Age's heavy, a robot steam tank. A white-armoured casemate on a gunmetal chassis
between two tracks: a sloped glacis with hazard stripes, white track guards over the tracks (hazard-striped at the
front), a squat turret with a red visor slot across its face (the robot's eye) and a stubby gun with a muzzle brake;
behind it a riveted boiler lying along the deck (gunmetal bands, a chrome steam dome and safety valve), a short funnel
with a flared spark-arrester crown at its front and a gunmetal firebox at its back with a red-glowing grate on top,
a round red core window on each side and a glowing fire door at the back. On each side, outside its track, a steam
cylinder on the track guard drives the rear sprocket's crank through a connecting rod, like a locomotive.
Each track: a static belt round a gunmetal side frame, three spoked road wheels and the idler/sprocket hubs on its
outer face, and at its two ends a ring of grousers that turns with its idler/sprocket (each ring is a full circle, so a
turn per loop is seamless; its inner half is hidden in the frame and its top under the track guard).
Walk (the drive loop, 24 frames): the sprockets and idlers turn once, the road wheels 1.25 times, the cranks drive the
rods and pistons (the two sides a quarter turn apart), the hull chugs four times (one per exhaust beat) on its springs,
the funnel's ember flares on each beat, and the turret sways a little. Faces -Y, Z up; model_scale 0.9.
walk_speed = 2 pi R_P * model_scale * 24 / WALK_FRAMES = 0.848 (the ground speed at which the tracks don't slide).
"""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, rot_from_axes, v3, norm,
                 F, smax)
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser

ROOT_NAME = "SteamTank"
GLB_NAME = "steam_tank"
TEX_PREFIX = "steam_tank"
MODEL_SCALE = 0.9
WALK_FRAMES = 24

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.22, 0.23, 0.26)
BLACK = (0.07, 0.07, 0.08)
DECKC = (0.56, 0.58, 0.61)
RED_GLOW = (1.0, 0.2, 0.08)
FIRE = (1.0, 0.38, 0.1)
EMBER = (1.0, 0.55, 0.15)

# ---- the tracks (the left one; the right mirrors it)
TX = 0.47                                  # a track's centre line (x)
TW = 0.22                                  # its width
YI, YS = -0.5, 0.48                        # the idler (front) and the sprocket (rear) axles
ZA = 0.2                                   # the axles' height
R_P = 0.15                                 # the belt's pitch radius round them: one turn = 2 pi R_P of ground
BELT_T = 0.035
LUG_H = 0.03                               # grousers: their tips touch the ground (ZA - R_P - BELT_T / 2 - LUG_H = 0)
N_LUG = 16
WHEEL_Y = (-0.265, -0.005, 0.255)          # road wheels (on the frame's outer face)
WHEEL_R = 0.12                             # (rolls 2 pi R_P / WHEEL_R = 1.25 turns per loop; 8 spokes keep it seamless)
WHEEL_Z = 0.19
XO = TX + TW / 2                           # the track's outer side (0.58)
XF = XO + 0.008                            # the side frame's outer face
WALK_DIST = 2 * math.pi * R_P              # ground covered per loop (model units)
WALK_SPEED = WALK_DIST * MODEL_SCALE * 24 / WALK_FRAMES

# ---- the drive: a crank on each rear sprocket, a connecting rod, a crosshead and piston in an inclined cylinder
XR = 0.66                                  # the rods' plane
RC = 0.075                                 # crank radius
LROD = 0.46                                # connecting rod length
U_CYL = norm(v3((0.0, -1.0, 0.42)))        # the cylinder's axis (from the crank centre, forward and up)
PHASE = {"L": 0.0, "R": math.pi / 2}       # the crank angle at frame 0 (the right side a quarter turn ahead)
CYL_S = (0.62, 0.88)                       # the cylinder along the axis (distance from the crank centre)

# ---- the hull
HULL_TOP = 0.62
TUR_C = v3((0.0, -0.14, HULL_TOP))         # the turret's foot
TUR_R = 0.2
GUN_Z = 0.705
BOIL_Z = 0.84
BOIL_R = 0.19
BOIL_Y = (0.14, 0.5)
FUN_C = v3((0.0, 0.2, 0.96))               # the funnel's foot (on the boiler)
FUN_TOP = 1.24                             # its crown's rim
FUN_MOUTH = v3((0.0, 0.2, FUN_TOP + 0.01)) # where the game puffs its smoke
FIRE_Y = (0.5, 0.64)
FB_C = v3((0.0, 0.57, 0.82))                # the firebox's centre
FB_H = 0.2                                 # its half height


def mirror(p):
    return (-p[0], p[1], p[2])


def sx_of(s):
    return 1.0 if s == "L" else -1.0


def crank_centre(s):
    return v3((sx_of(s) * XR, YS, ZA))


def u_cyl(s):
    return U_CYL


def pin_at(s, ang):
    """The crank pin at crank angle `ang` (0 = straight up; the crank turns forward over the top, about +X)."""
    c = crank_centre(s)
    a = ang + PHASE[s]
    return c + v3((0.0, -RC * math.sin(a), RC * math.cos(a)))


def xhead_s(s, ang):
    """The crosshead's distance along the cylinder axis from the crank centre."""
    c = crank_centre(s)
    d = pin_at(s, ang) - c
    u = u_cyl(s)
    du = float(d @ u)
    return du + math.sqrt(LROD * LROD - float(d @ d) + du * du)


def xhead_at(s, ang):
    return crank_centre(s) + u_cyl(s) * xhead_s(s, ang)


BONES = [
    ("root", (0, 0, 0.42), (0, 0, 0.6), None),
    ("turret", tuple(TUR_C), tuple(TUR_C + v3((0, 0, 0.2))), "root"),
    ("ember", tuple(FUN_MOUTH - v3((0, 0, 0.03))), tuple(FUN_MOUTH + v3((0, 0, 0.1))), "root"),
]
for s in ("L", "R"):
    sx = sx_of(s)
    BONES += [
        ("track." + s, (sx * TX, 0.0, ZA), (sx * TX, 0.3, ZA), None),
        ("idler." + s, (sx * TX, YI, ZA), (sx * (TX + 0.2), YI, ZA), "track." + s),
        ("sprocket." + s, (sx * TX, YS, ZA), (sx * (TX + 0.2), YS, ZA), "track." + s),
        ("rod." + s, tuple(pin_at(s, 0.0)), tuple(xhead_at(s, 0.0)), "sprocket." + s),
        ("piston." + s, tuple(xhead_at(s, 0.0)), tuple(xhead_at(s, 0.0) + u_cyl(s) * 0.2), None),
    ]
    for i, y in enumerate(WHEEL_Y):
        BONES.append(("wheel.%s%d" % (s, i), (sx * TX, y, WHEEL_Z), (sx * (TX + 0.2), y, WHEEL_Z), "track." + s))

MATS = {
    "armor": ("armor", dict(name="RB_TankArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.42), (4, BLACK, 0.45),
                                                         (5, DECKC, 0.5)], seams=[2], wear=1.2, scale=1.4)),
    "frame": ("gunmetal", dict(name="RB_TankFrame", base=(0.22, 0.23, 0.26), labels=[(1, ORANGE, 0.35), (2, (0.08, 0.08, 0.09), 0.6),
                                                                                      (4, BLACK, 0.5)], seams=[2], scale=1.4)),
    "iron": ("gunmetal", dict(name="RB_TankIron", base=(0.11, 0.11, 0.12), edge=(0.46, 0.47, 0.5), labels=[(2, (0.04, 0.04, 0.045), 0.6)],
                              rough=0.5, seams=[2], scale=1.4)),
    "chrome": ("chrome", dict(name="RB_TankChrome")),
    "socket": ("lens_socket", dict(name="RB_TankSocket")),
    "glow": ("glow", dict(name="RB_TankGlow", col=RED_GLOW)),
}
GLOW = {"Visor": (RED_GLOW, 1.5, 0.5), "Core": (FIRE, 1.4, 0.5), "Ember": (EMBER, 1.3, 0.5)}

LOW_TARGETS = {"Chassis": 240, "Hull": 850, "Turret": 420, "Visor": 50, "Gun": 200, "Boiler": 300, "Bands": 240,
               "Firebox": 240, "Core": 100, "Funnel": 220, "Ember": 40, "Dome": 120, "Pipes": 110}
for s in "LR":
    LOW_TARGETS.update({"Belt" + s: 280, "Frame" + s: 120, "LugsF" + s: 140, "LugsB" + s: 140, "Idler" + s: 110,
                        "Sprocket" + s: 140, "Rod" + s: 90, "Piston" + s: 90, "Cylinder" + s: 180})
    for i in range(3):
        LOW_TARGETS["Wheel%s%d" % (s, i)] = 90
X_AX = rot_from_axes(z_axis=(1, 0, 0))
Y_AX = rot_from_axes(z_axis=(0, 1, 0))


def _hazard(f, lo, hi, w=0.06, band=None, d=(0, 1, 1)):
    """Diagonal hazard stripes (orange 1 / black 4) over the box lo..hi (optionally only where band(P) < 0)."""
    lo, hi = v3(lo), v3(hi)
    dd = norm(d).astype(F)
    def box(P):
        return np.max(np.stack([lo.astype(F) - P, P - hi.astype(F)], 0), axis=(0, 2))
    def orange(P):
        b = box(P)
        return b if band is None else np.maximum(b, band(P))
    def black(P):
        s = (P @ dd) / F(w)
        fr = s - np.floor(s)
        return np.maximum(orange(P), (np.abs(fr - F(0.25)) - F(0.25)) * F(w * 0.7))
    f.paint(Func(orange, lo - 0.01, hi + 0.01), 1)
    f.paint(Func(black, lo - 0.01, hi + 0.01), 4)


def _stadium(P, x0):
    """(distance in the y-z plane from the axle line, |x - x0|) for a track whose centre line is x0."""
    yc = np.clip(P[:, 1], F(YI), F(YS))
    d2 = np.sqrt((P[:, 1] - yc) ** 2 + (P[:, 2] - F(ZA)) ** 2)
    return d2, np.abs(P[:, 0] - F(x0))


def rivet_row(f, a, b, n, r=0.012, k=0.004):
    a, b = v3(a), v3(b)
    for i in range(n):
        f.add(Sphere(a + (b - a) * (i / max(1, n - 1)), r), k=k)


def _spoked(f, c, r, n, sx, spoke_r=0.014, phase=0.0, hub=0.034):
    """A spoked iron wheel face on the outer side of a track (axis x): a rim, n spokes, a hub with an orange cap."""
    xo = sx * 1.0
    f.add(Cylinder(c + v3((xo * 0.003, 0, 0)), r - 0.01, 0.012, rr=0.004, R=X_AX))                  # the dished web
    f.add(Torus(c + v3((xo * 0.012, 0, 0)), r - 0.016, 0.016, R=X_AX), k=0.004)                    # the rim
    for i in range(n):
        a = phase + i * 2 * math.pi / n
        d = v3((0.0, math.cos(a), math.sin(a)))
        f.add(RoundCone(c + v3((xo * 0.014, 0, 0)) + d * hub * 0.8, c + v3((xo * 0.012, 0, 0)) + d * (r - 0.02), spoke_r, spoke_r * 0.8),
              k=0.004)
    f.add(Cylinder(c + v3((xo * 0.016, 0, 0)), hub, 0.03, rr=0.008, R=X_AX), k=0.006)
    f.paint(Cylinder(c + v3((xo * 0.03, 0, 0)), hub * 0.75, 0.012, R=X_AX), 1)


def parts(fine=False):
    vx = 0.0045 if fine else 0.008
    vs = 0.0032 if fine else 0.006
    out = []
    # ================================================================================================ the tracks
    for s in ("L", "R"):
        sx = sx_of(s)
        x0 = sx * TX
        # ---- the belt (static): a band round the axles; grouser blocks under its bottom run
        f = Field("Belt" + s)
        lo, hi = (x0 - 0.15, YI - 0.25, -0.02), (x0 + 0.15, YS + 0.25, ZA + 0.25)
        def belt(P, x0=x0):
            d2, dx = _stadium(P, x0)
            return np.maximum(np.abs(d2 - F(R_P)) - F(BELT_T / 2), dx - F(TW / 2))
        f.add(Func(belt, lo, hi))
        y = YI + 0.075
        while y < YS - 0.07:
            f.add(RoundBox((x0, y, (ZA - R_P - BELT_T / 2) / 2 + 0.002), (TW / 2 - 0.005, 0.021, (ZA - R_P - BELT_T / 2) / 2 + 0.004),
                           0.008), k=0.004)
            y += 2 * math.pi * (R_P + BELT_T / 2 + LUG_H / 2) / N_LUG
        for yy in np.arange(YI + 0.04, YS, 0.07):                                       # link seams across the runs
            f.paint(RoundBox((x0, yy, ZA), (0.2, 0.0035, 0.3)), 2)
        out.append(("Belt" + s, f, vs, "track." + s, "iron"))
        # ---- the side frame: fills the belt's inside, stands a little proud of its sides; bolts; an orange stripe
        f = Field("Frame" + s)
        def frame(P, x0=x0):
            d2, dx = _stadium(P, x0)
            return np.maximum(d2 - F(R_P), dx - F(TW / 2 + 0.008))
        f.add(Func(frame, lo, hi))
        for yy in (-0.395, -0.135, 0.125, 0.37):
            for zz in (ZA + 0.1, ZA - 0.11):
                f.add(Sphere((x0 + sx * (TW / 2 + 0.008), yy, zz), 0.011), k=0.003)
        out.append(("Frame" + s, f, vx, "track." + s, "frame"))
        # ---- the grouser rings at the idler and the sprocket (full circles: they turn a whole turn per loop)
        for nm, yc, bone in (("LugsF", YI, "idler."), ("LugsB", YS, "sprocket.")):
            f = Field(nm + s)
            c = v3((x0, yc, ZA))
            rm = R_P + BELT_T / 2 + LUG_H / 2
            for k in range(N_LUG):
                a = (k + 0.5) * 2 * math.pi / N_LUG
                d = v3((0.0, math.cos(a), math.sin(a)))
                f.add(RoundBox(c + d * (rm - 0.003), (TW / 2 - 0.006, 0.021, LUG_H / 2 + 0.004), 0.008,
                               R=rot_from_axes(x_axis=(1, 0, 0), z_axis=d)))
            out.append((nm + s, f, vs, bone + s, "iron"))
        # ---- the idler's hub (front) and the sprocket's hub with the crank (rear), on the frame's outer face
        f = Field("Idler" + s)
        _spoked(f, v3((sx * XF, YI, ZA)), 0.108, 5, sx, spoke_r=0.016, hub=0.04)
        out.append(("Idler" + s, f, vs, "idler." + s, "frame"))
        f = Field("Sprocket" + s)
        cs = v3((sx * XF, YS, ZA))
        f.add(Cylinder(cs + v3((sx * 0.006, 0, 0)), 0.112, 0.016, rr=0.005, R=X_AX))
        for i in range(6):                                                                 # lightening holes
            a = i * math.pi / 3 + math.pi / 6
            f.sub(Cylinder(cs + v3((sx * 0.01, 0.07 * math.cos(a), 0.07 * math.sin(a))), 0.022, 0.05, R=X_AX), k=0.004)
        f.add(Torus(cs + v3((sx * 0.012, 0, 0)), 0.1, 0.012, R=X_AX), k=0.004)
        p0 = pin_at(s, 0.0)
        cp = v3((sx * (XF + 0.024), p0[1], p0[2]))
        f.add(RoundCone(cs + v3((sx * 0.024, 0, 0)), cp, 0.04, 0.03), k=0.008)            # the crank arm
        f.add(Cylinder(cs + v3((sx * 0.026, 0, 0)), 0.045, 0.024, rr=0.008, R=X_AX), k=0.006)
        f.add(Cylinder((sx * (XF + XR) / 2 + sx * 0.012, p0[1], p0[2]), 0.016, XR - XF + 0.02, rr=0.004, R=X_AX), k=0.004)  # the pin
        f.paint(Cylinder(cs + v3((sx * 0.04, 0, 0)), 0.03, 0.02, R=X_AX), 1)
        out.append(("Sprocket" + s, f, vs, "sprocket." + s, "frame"))
        for i, y in enumerate(WHEEL_Y):
            f = Field("Wheel%s%d" % (s, i))
            _spoked(f, v3((sx * XF, y, WHEEL_Z)), WHEEL_R, 8, sx, phase=0.2 * i)
            out.append(("Wheel%s%d" % (s, i), f, vs, "wheel.%s%d" % (s, i), "frame"))
        # ---- the drive: the connecting rod (crank pin -> crosshead), the crosshead and piston rod, the cylinder
        x1 = xhead_at(s, 0.0)
        u = u_cyl(s)
        f = Field("Rod" + s)
        f.add(RoundBox((p0 + x1) / 2, (0.012, float(np.linalg.norm(x1 - p0)) / 2, 0.026), 0.01,
                       R=rot_from_axes(x_axis=(1, 0, 0), y_axis=norm(x1 - p0))))
        f.add(Cylinder(p0, 0.036, 0.034, rr=0.01, R=X_AX), k=0.01)                         # big end
        f.add(Cylinder(x1, 0.028, 0.032, rr=0.008, R=X_AX), k=0.01)                        # small end
        out.append(("Rod" + s, f, vs, "rod." + s, "chrome"))
        f = Field("Piston" + s)
        Ru = rot_from_axes(z_axis=u, x_axis=(1, 0, 0))
        f.add(RoundBox(x1 + u * 0.015, (0.03, 0.03, 0.045), 0.01, R=Ru))                    # the crosshead
        f.add(RoundCone(x1 + u * 0.04, x1 + u * 0.32, 0.016, 0.016), k=0.006)              # the piston rod
        out.append(("Piston" + s, f, vs, "piston." + s, "chrome"))
        f = Field("Cylinder" + s)
        cc = crank_centre(s)
        ca, cb = cc + u * CYL_S[0], cc + u * CYL_S[1]
        Rc = rot_from_axes(z_axis=u, x_axis=(1, 0, 0))
        f.add(Cylinder((ca + cb) / 2, 0.062, CYL_S[1] - CYL_S[0], rr=0.014, R=Rc))
        for e in (ca + u * 0.012, cb - u * 0.012):
            f.add(Torus(e, 0.062, 0.012, R=Rc), k=0.004)
        for i in range(8):
            a = i * math.pi / 4
            n2 = v3((math.cos(a), 0, 0)) + np.cross(u, v3((1, 0, 0))) * math.sin(a)
            f.add(Sphere(cb + n2 * 0.06 - u * 0.004, 0.008), k=0.002)
        f.paint(Cylinder((ca + cb) / 2, 0.08, 0.05, R=Rc), 1)                               # an orange band
        nrm = norm(np.cross(u, v3((1, 0, 0))))
        for sg in (-1, 1):                                                                  # the slide bars
            f.add(RoundCone(cc + u * 0.34 + nrm * sg * 0.034, ca + nrm * sg * 0.034, 0.008, 0.008), k=0.004)
        f.add(RoundCone(cc + u * 0.34 + nrm * 0.034, cc + u * 0.34 - nrm * 0.034, 0.009, 0.009), k=0.004)
        # the bracket from the cylinder in to the track guard's edge
        mid = (ca + cb) / 2
        f.add(RoundBox(v3((sx * (XF + 0.012), mid[1], mid[2] - 0.035)), (0.035, 0.09, 0.025), 0.01), k=0.012)
        out.append(("Cylinder" + s, f, vs, "track." + s, "frame"))

    # ================================================================================================ the hull
    # ---- the chassis: a gunmetal tub between the tracks
    f = Field("Chassis")
    f.add(RoundBox((0, -0.01, 0.27), (0.37, 0.59, 0.15), 0.05))
    f.inter(Plane((0, -0.6, 0.14), (0, -0.7, -0.7)), k=0.03)
    for sx in (-1, 1):                                                                  # axle housings into the frames
        for y in (YI, YS) + WHEEL_Y:
            f.add(Cylinder((sx * 0.36, y, ZA if y in (YI, YS) else WHEEL_Z), 0.035, 0.04, rr=0.01, R=X_AX), k=0.01)
    f.paint(RoundBox((0, -0.6, 0.3), (0.4, 0.02, 0.2)), 2)
    out.append(("Chassis", f, vx, "root", "frame"))
    # ---- the white upper hull: the casemate with its sloped glacis, the track guards (fenders), the deck
    f = Field("Hull")
    f.add(RoundBox((0, 0.0, 0.52), (0.35, 0.57, 0.1), 0.04))
    f.inter(Plane((0, -0.42, HULL_TOP), (0, -0.62, 0.78)), k=0.03)                       # the glacis slope
    for sx in (-1, 1):
        f.add(RoundBox((sx * (TX + 0.0), -0.005, 0.428), (TW / 2 + 0.035, 0.545, 0.018), 0.014), k=0.02)   # the guard
        rivet_row(f, (sx * (TX + TW / 2 + 0.025), -0.5, 0.446), (sx * (TX + TW / 2 + 0.025), 0.5, 0.446), 9, 0.009, 0.003)
        _hazard(f, (sx * TX - 0.16, -0.62, 0.36), (sx * TX + 0.16, -0.47, 0.46), w=0.06, d=(1, 0, 0.6))  # guards' fronts
        f.paint(RoundBox((sx * (TX - 0.02), 0.0, 0.448), (0.004, 0.5, 0.03)), 2)          # a seam along each guard
    # the glacis: hazard stripes along its lower edge, a seam, a red-rimmed hatch; the deck plates, side seams
    _hazard(f, (-0.4, -0.66, 0.4), (0.4, -0.5, 0.525), w=0.065, d=(1, 0, 0.6))
    f.paint(RoundBox((0, -0.5, 0.565), (0.4, 0.2, 0.004)), 2)                           # a seam across the glacis
    f.paint(RoundBox((0, 0.15, HULL_TOP), (0.31, 0.43, 0.012), 0.0), 5)                # the grey deck behind the turret
    for yy in (0.06, 0.32):
        f.paint(RoundBox((0, yy, HULL_TOP), (0.4, 0.004, 0.02)), 2)
    for sx in (-1, 1):
        f.paint(RoundBox((sx * 0.35, 0.0, 0.53), (0.012, 0.6, 0.004)), 2)
        f.paint(RoundBox((sx * 0.35, 0.0, 0.575), (0.012, 0.6, 0.012)), 1)              # an orange pinstripe on each flank
        rivet_row(f, (sx * 0.352, -0.38, 0.49), (sx * 0.352, 0.5, 0.49), 8, 0.01, 0.003)
    rivet_row(f, (-0.3, -0.555, 0.4), (0.3, -0.555, 0.4), 7, 0.011, 0.003)
    out.append(("Hull", f, vx, "root", "armor"))
    # ---- the turret: a squat drum with a sloped face, the visor slot, a hatch with a periscope; the gun
    f = Field("Turret")
    tc = TUR_C
    f.add(Cylinder(tc + v3((0, 0, 0.07)), TUR_R, 0.14, rr=0.04))
    f.add(Ellipsoid(tc + v3((0, 0.01, 0.13)), (TUR_R - 0.02, TUR_R - 0.02, 0.07)), k=0.04)
    f.inter(Plane(tc + v3((0, -0.155, 0.17)), (0, -0.7, 0.72)), k=0.02)                     # the sloped face
    f.add(RoundBox(tc + v3((0, -0.15, 0.085)), (0.1, 0.06, 0.06), 0.03), k=0.02)          # the mantlet
    f.sub(RoundBox(tc + v3((0, -0.19, 0.145)), (0.12, 0.05, 0.016), 0.012), k=0.006)       # the visor slot
    f.add(Cylinder(tc + v3((0.06, 0.06, 0.2)), 0.06, 0.03, rr=0.012), k=0.01)              # the hatch
    f.add(RoundBox(tc + v3((-0.08, 0.02, 0.21)), (0.025, 0.035, 0.04), 0.01), k=0.008)     # a periscope
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(tc[2] + 0.035)) - F(0.016), tc - 0.3, tc + 0.3), 1)    # an orange band
    f.paint(Func(lambda P: np.abs(P[:, 2] - F(tc[2] + 0.06)) - F(0.003), tc - 0.3, tc + 0.3), 2)
    f.paint(Torus(tc + v3((0.06, 0.06, 0.215)), 0.06, 0.008), 2)
    rivet_row(f, tc + v3((-0.15, -0.115, 0.03)), tc + v3((0.15, -0.115, 0.03)), 5, 0.009, 0.003)
    out.append(("Turret", f, vx, "turret", "armor"))
    f = Field("Visor")
    f.add(RoundBox(tc + v3((0, -0.16, 0.145)), (0.112, 0.018, 0.011), 0.009))
    out.append(("Visor", f, vs, "turret", "glow"))
    f = Field("Gun")
    gy0, gy1 = tc[1] - 0.18, tc[1] - 0.52
    f.add(Cylinder((0, (gy0 + gy1) / 2, GUN_Z), 0.034, gy0 - gy1, rr=0.01, R=Y_AX))
    f.add(Cylinder((0, gy0 + 0.02, GUN_Z), 0.05, 0.06, rr=0.015, R=Y_AX), k=0.01)          # the collar at the mantlet
    f.add(RoundBox((0, gy1 + 0.02, GUN_Z), (0.05, 0.045, 0.04), 0.016), k=0.01)            # the muzzle brake
    for sxx in (-1, 1):
        f.sub(RoundBox((sxx * 0.05, gy1 + 0.02, GUN_Z), (0.02, 0.02, 0.022), 0.006), k=0.004)
    f.sub(Cylinder((0, gy1, GUN_Z), 0.02, 0.06, R=Y_AX), k=0.004)                          # the bore
    f.paint(Cylinder((0, gy1 + 0.1, GUN_Z), 0.05, 0.03, R=Y_AX), 1)
    out.append(("Gun", f, vs, "turret", "frame"))
    # ---- the boiler: a white drum along the deck on two saddles, the smokebox front; gunmetal riveted bands
    f = Field("Boiler")
    by0, by1 = BOIL_Y
    f.add(Cylinder((0, (by0 + by1) / 2, BOIL_Z), BOIL_R, by1 - by0, rr=0.03, R=Y_AX))
    f.add(Ellipsoid((0, by0 + 0.01, BOIL_Z), (BOIL_R - 0.03, 0.05, BOIL_R - 0.03)), k=0.02)   # the smokebox door's dome
    for y in (by0 + 0.08, by1 - 0.08):
        f.add(RoundBox((0, y, (HULL_TOP + BOIL_Z) / 2 - 0.02), (0.15, 0.04, (BOIL_Z - HULL_TOP) / 2), 0.02), k=0.02)   # saddles
    f.paint(Cylinder((0, (by0 + by1) / 2 + 0.03, BOIL_Z), BOIL_R + 0.02, 0.045, R=Y_AX), 1)
    f.paint(Func(lambda P: np.maximum(np.abs(P[:, 0]) - F(0.004), F(BOIL_Z + 0.1) - P[:, 2]), (-0.3, by0, 0.6), (0.3, by1, 1.1)), 2)
    out.append(("Boiler", f, vx, "root", "armor"))
    f = Field("Bands")
    for y in (by0 + 0.035, by0 + 0.18, by1 - 0.13, by1 - 0.02):
        f.add(Torus((0, y, BOIL_Z), BOIL_R + 0.002, 0.014, R=Y_AX))
        for i in range(12):
            a = i * math.pi / 6
            f.add(Sphere((math.cos(a) * (BOIL_R + 0.012), y, BOIL_Z + math.sin(a) * (BOIL_R + 0.012)), 0.009), k=0.003)
    f.add(Torus((0, by0 - 0.005, BOIL_Z), BOIL_R - 0.04, 0.016, R=Y_AX), k=0.004)        # the smokebox door's rim
    f.add(Cylinder((0, by0 - 0.04, BOIL_Z), 0.022, 0.04, rr=0.008, R=Y_AX), k=0.004)     # its handle boss
    out.append(("Bands", f, vs, "root", "frame"))
    # ---- the firebox at the back: a gunmetal box, a grate glowing on top, a core window each side, a fire door
    f = Field("Firebox")
    fy0, fy1 = FIRE_Y
    fc = FB_C
    f.add(RoundBox(fc, (0.21, (fy1 - fy0) / 2, FB_H), 0.035))
    f.sub(RoundBox(fc + v3((0, 0, FB_H)), (0.13, (fy1 - fy0) / 2 - 0.035, 0.02), 0.01), k=0.006)   # the grate's recess
    for sx in (-1, 1):
        f.sub(Cylinder(fc + v3((sx * 0.21, 0, -0.02)), 0.048, 0.04, R=X_AX), k=0.006)         # the core windows
        f.add(Torus(fc + v3((sx * 0.215, 0, -0.02)), 0.056, 0.012, R=X_AX), k=0.004)
    f.sub(RoundBox(fc + v3((0, (fy1 - fy0) / 2, -0.02)), (0.075, 0.03, 0.06), 0.015), k=0.006)     # the fire door
    for i in range(4):                                                                      # the grate's bars
        f.add(RoundBox(fc + v3((-0.09 + 0.06 * i, 0, FB_H - 0.012)), (0.008, (fy1 - fy0) / 2 - 0.04, 0.012), 0.004), k=0.003)
    for i in range(3):
        f.add(RoundBox(fc + v3((0, (fy1 - fy0) / 2 + 0.004, -0.06 + 0.04 * i)), (0.08, 0.008, 0.006), 0.003), k=0.002)
    _hazard(f, fc + v3((-0.25, -0.1, -FB_H - 0.01)), fc + v3((0.25, 0.12, -FB_H + 0.06)), w=0.05, d=(1, 0, 1))
    f.add(Cylinder(fc + v3((0.215, 0.02, 0.11)), 0.032, 0.02, rr=0.006, R=X_AX), k=0.005)   # a pressure gauge
    f.paint(Cylinder(fc + v3((0.228, 0.02, 0.11)), 0.024, 0.01, R=X_AX), 2)
    out.append(("Firebox", f, vs, "root", "frame"))
    f = Field("Core")
    f.add(RoundBox(fc + v3((0, 0, FB_H - 0.02)), (0.125, (fy1 - fy0) / 2 - 0.04, 0.012), 0.008))
    for sx in (-1, 1):
        f.add(Ellipsoid(fc + v3((sx * 0.188, 0, -0.02)), (0.012, 0.046, 0.046)))
    f.add(RoundBox(fc + v3((0, (fy1 - fy0) / 2 - 0.012, -0.02)), (0.07, 0.008, 0.055), 0.01))
    out.append(("Core", f, vs, "root", "glow"))
    # ---- the funnel: a short stack with a flared spark-arrester crown, banded; its mouth glows
    f = Field("Funnel")
    f.add(Cylinder(FUN_C + v3((0, 0, (FUN_TOP - FUN_C[2]) / 2 - 0.03)), 0.072, FUN_TOP - FUN_C[2] - 0.06, rr=0.01))
    f.add(Cylinder(v3((0, FUN_C[1], FUN_C[2] + 0.075)), 0.1, 0.03, rr=0.012), k=0.02)      # its foot flange
    f.add(RoundCone(v3((0, FUN_C[1], FUN_TOP - 0.1)), v3((0, FUN_C[1], FUN_TOP - 0.02)), 0.075, 0.112), k=0.02)   # the crown
    f.add(Torus(v3((0, FUN_C[1], FUN_TOP - 0.015)), 0.105, 0.018), k=0.006)
    f.sub(Cylinder(v3((0, FUN_C[1], FUN_TOP + 0.02)), 0.085, 0.12), k=0.008)               # the mouth
    f.paint(Cylinder(v3((0, FUN_C[1], FUN_C[2] + 0.14)), 0.1, 0.04), 1)
    f.paint(Cylinder(v3((0, FUN_C[1], FUN_TOP - 0.015)), 0.14, 0.04), 4)
    out.append(("Funnel", f, vs, "root", "frame"))
    f = Field("Ember")
    f.add(Cylinder(v3((0, FUN_C[1], FUN_TOP - 0.06)), 0.086, 0.02, rr=0.006))
    out.append(("Ember", f, vs, "ember", "glow"))
    # ---- the steam dome and safety valve (chrome) on the boiler; a whistle
    f = Field("Dome")
    f.add(Cylinder((0, 0.38, BOIL_Z + BOIL_R + 0.01), 0.075, 0.08, rr=0.02))
    f.add(Ellipsoid((0, 0.38, BOIL_Z + BOIL_R + 0.05), (0.075, 0.075, 0.06)), k=0.02)
    f.add(Cylinder((0, 0.46, BOIL_Z + BOIL_R + 0.02), 0.025, 0.07, rr=0.006), k=0.008)
    f.add(Sphere((0, 0.46, BOIL_Z + BOIL_R + 0.07), 0.03), k=0.006)
    f.add(Cylinder((0.07, 0.28, BOIL_Z + BOIL_R - 0.01), 0.012, 0.08, rr=0.004), k=0.004)   # the whistle's stem
    f.add(RoundCone((0.07, 0.28, BOIL_Z + BOIL_R + 0.04), (0.07, 0.28, BOIL_Z + BOIL_R + 0.1), 0.022, 0.02), k=0.004)
    out.append(("Dome", f, vs, "root", "chrome"))
    # ---- steam pipes from the boiler down to each cylinder
    f = Field("Pipes")
    for s in ("L", "R"):
        sx = sx_of(s)
        cc = crank_centre(s)
        top = cc + U_CYL * (CYL_S[0] + CYL_S[1]) / 2 + v3((0, 0, 0.05))
        cb = cc + U_CYL * CYL_S[0]
        pts = [v3((sx * 0.17, 0.2, BOIL_Z - 0.07)), v3((sx * 0.29, 0.08, 0.655)), v3((sx * 0.4, 0.0, 0.61)),
               v3((sx * 0.56, -0.06, 0.5)), v3((sx * (XR - 0.01), cb[1] + 0.01, cb[2] + 0.05))]
        for i in range(len(pts) - 1):
            f.add(RoundCone(pts[i], pts[i + 1], 0.017, 0.017), k=0.012)
        f.add(Torus(pts[2], 0.02, 0.008, R=rot_from_axes(z_axis=pts[3] - pts[2])), k=0.003)
    out.append(("Pipes", f, vs, "root", "chrome"))
    return out


# ------------------------------------------------------------------------------------------------ clips
V = lambda *a: Vector(a)


def _spin(ang, axis=(1, 0, 0)):
    q = Quaternion(Vector(axis), ang)
    return ("rot", q)


def drive_pose(arm, t, chug=1.0, extra=None):
    """The drive at loop time t (0..1): wheels, rings, cranks, rods and pistons for one turn of the sprockets."""
    ang = 2 * math.pi * t                                   # sprockets / idlers: one turn per loop
    aims, offs = {}, {}
    for s in ("L", "R"):
        aims["idler." + s] = _spin(ang)
        aims["sprocket." + s] = _spin(ang)
        for i in range(3):
            aims["wheel.%s%d" % (s, i)] = _spin(ang * R_P / WHEEL_R)
        pin, xh = pin_at(s, ang), xhead_at(s, ang)
        aims["rod." + s] = Vector(tuple(xh - pin))
        offs["piston." + s] = tuple(U_CYL * (xhead_s(s, ang) - xhead_s(s, 0.0)))
    return aims, offs


def walk(arm):
    P = Poser(arm)
    act = ra.new_action(arm, "Walk")
    for f in range(WALK_FRAMES + 1):
        t = f / WALK_FRAMES
        aims, offs = drive_pose(arm, t)
        w = 2 * math.pi * t
        beat = abs(math.sin(4 * math.pi * t))               # four exhaust beats per turn (two cylinders, double-acting)
        root_off = V(0.0, 0.0, 0.006 * (1.0 - beat) + 0.002 * math.sin(w))
        root_rot = Quaternion(V(1, 0, 0), 0.008 * math.sin(4 * math.pi * t + 0.6)) @ Quaternion(V(0, 1, 0), 0.006 * math.sin(w))
        aims["turret"] = lambda P_, base, a=0.05 * math.sin(w): (base.col[1].xyz.copy(), a)
        puff = max(0.0, math.cos(4 * math.pi * t)) ** 6
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, offsets=offs,
                        scales={"ember": (1.0 + 0.25 * puff, 1.0 + 0.6 * puff, 1.0 + 0.25 * puff)})
        P.key(ch, f)
    ra.finish_action(arm, act, WALK_FRAMES, True)


def clips(arm):
    walk(arm)
