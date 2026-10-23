"""The Tesla Coil (HQ tower, Industrial Age): a tall tesla coil and the eccentric electrical engineer who works it.
Rest pose: he stands in an A-pose facing -Y (the robots), feet at z = 0, the coil behind him on his left (+X), the switch
console before him on his right (-X); the knife-switch is closed (it rests open in every clip).

Him: the Spear Guard's body (spear.py), his own face: a lean old face, a high domed forehead and a bald crown, wild white
hair standing out in tufts round the sides and the back, big bushy white brows raised high, wide pale-blue eyes with
bags under them, a big hooked nose, a broad grin under a huge white handlebar moustache, big ears. Brass goggles with
green lenses pushed up on his forehead on a leather strap. A long white lab coat (to the knee, hanging open, wide
notched lapels, patch pockets, scorch marks at the cuffs and the hem) over a navy waistcoat with brass buttons and a
brass watch chain, a white wing collar and a crimson bow tie; charcoal trousers, brown boots; thick black rubber
gauntlets over his fists. A red pencil and a brass pen in his breast pocket.

The coil (on its own bone, `machine`, which deforms nothing of him): a riveted iron plinth with a big brass voltmeter on
its front, a varnished wooden deck, the primary (three turns of thick copper tube on porcelain insulators), the long
secondary (fine copper winding in four bands over a varnished wooden former, brass rings between them), a brass cap
and standoff, the big polished copper toroid (its centre has a bone of its own, `toroid`: the point the game's lightning
leaves from) with a brass breakout point; its charge (`Charge`, shipped glowing faint cyan) gathers along the
toroid's crest and in the ball on the breakout point.

The switch console (rigid with the coil): a cast-iron pedestal under a slate slab tilted toward him in an iron tray, the
knife-switch on it (copper hinge blocks and jaws on porcelain, brass binding posts), two gauges on a slate board at its
far end, the twin rubber cable down the pedestal and over the floor to the coil's plinth. The switch's blades, crossbar
and handle (ebonite, a red knob) ride their own bone (`switch`, child of `machine`), hinged at the hinge blocks.

Painted labels on the apparatus (material mats.electric): 0 polished copper, 5 brass, 6 iron, 7 varnished wood, 8
porcelain, 9 rubber / ebonite, 10 slate, 11 copper winding, 12 green glass, 13 enamel, 14 red paint, 4 leather."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from ugo import _blend_add
import spear as sp
from spear import (J, SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE, HS, DZ, HPIV, hp, hr, hinv, HEAD_C, HEAD_RAD, EYE_R,
                   eye_c, smoothstep, hand_frame, HAND_S, CURLS, fist_center, hand, foot, torso_prims, traps, neck_prim,
                   deltoid, eyes_field, _forearm, TORSO, TORSO_Z, torso_bones)

COPPER, BRASS, IRON, WOOD, PORC, RUBBER, SLATE, WIND, GLASS, ENAMEL, RED, LEATHER = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 4
IRIS = ((0.2, 0.32, 0.44), (0.5, 0.66, 0.78))          # pale blue eyes (prep.paint_eyes: outer ring, inner ring)
Z = v3((0.0, 0.0, 1.0))


# ======================================================================================= head
def mouth_slot():
    return [hp((-0.07, -0.156, 1.574)), hp((-0.042, -0.187, 1.548)), hp((0.0, -0.199, 1.537)), hp((0.042, -0.187, 1.548)),
            hp((0.07, -0.156, 1.574))]


def chin_mask(P):
    """His shaved chin and jaw (design coordinates): a pale shadow of stubble."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    return np.maximum(np.maximum(np.abs(x) - F(0.11), z - F(1.535)), np.maximum(F(1.43) - z, y + F(0.03)))


def brow_hull():
    """The cranium and the domed forehead (for laying creases and the goggles on)."""
    fd = Field("BrowHull")
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.0)
    fd.add(Ellipsoid(hp((0, -0.01, 1.8)), v3((0.16, 0.17, 0.125)) * HS), 0.08)
    return fd


def head(fd):
    """A lean old face full of mischief: a high domed forehead, high cheekbones over hollow cheeks, a long chin, wide eyes
    with bags under them, big bushy brows raised high, a big hooked nose, a broad grin (the upper teeth showing), big
    ears; three creases across the forehead."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.01, 1.8), (0.16, 0.17, 0.125)), 0.08, SKIN)                           # the domed forehead
    fd.add(E((0, -0.058, 1.582), (0.13, 0.126, 0.13)), 0.07, SKIN)                        # a lean jaw
    fd.add(E((0, -0.134, 1.488), (0.074, 0.066, 0.074)), 0.05, SKIN)                      # a long chin
    for sx in (-1, 1):
        fd.add(S((sx * 0.112, -0.12, 1.648), 0.046), 0.05, SKIN)                            # high cheekbones
        fd.add(S((sx * 0.118, -0.042, 1.56), 0.044), 0.05, SKIN)
        pts = [hp((sx * 0.154, -0.055, 1.748)), hp((sx * 0.117, -0.132, 1.756)), hp((sx * 0.06, -0.174, 1.754)), hp((0.0, -0.184, 1.75))]
        fd.add(Chain(pts, [hr(0.012), hr(0.021), hr(0.024), hr(0.023)], k=hr(0.022)), hr(0.034), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.104, -0.152, 1.582)), v3((0.026, 0.018, 0.032)) * HS), hr(0.03))   # hollow cheeks
    fd.paint(Func(chin_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # three creases across the forehead (raised brows), two frown lines between them
    hull = brow_hull()
    for zc in (1.8, 1.826, 1.852):
        pts = []
        for k in range(11):
            x = -0.1 + 0.2 * k / 10
            h, ok = ray_hit(hull, [hp((x, -0.6, zc - 0.012 * (x / 0.1) ** 2))], [v3((0, 1, 0))], tmax=0.7)
            if ok[0]:
                pts.append(h[0])
        if len(pts) > 3:
            fd.sub(Chain(pts, [hr(0.0024)] * len(pts), k=0.002), hr(0.003))
    for sx in (-1, 1):
        fd.sub(RoundCone(hp((sx * 0.013, -0.2, 1.742)), hp((sx * 0.017, -0.197, 1.768)), hr(0.0018), hr(0.0015)), hr(0.003))
    # big bushy brows, raised high and flaring up at their outer ends
    tuft = lambda P: F(0.0026) * NOISE(P * F(140)) + F(0.0012) * np.sin(P[:, 0] * F(360) + P[:, 2] * F(90))
    for sx in (-1, 1):
        pts = [hp((sx * 0.022, -0.212, 1.774)), hp((sx * 0.064, -0.208, 1.797)), hp((sx * 0.11, -0.188, 1.81)),
               hp((sx * 0.158, -0.148, 1.824)), hp((sx * 0.18, -0.12, 1.84))]
        fd.add(Chain([p + v3((0, 0.004, 0)) for p in pts], [hr(0.014), hr(0.019), hr(0.018), hr(0.012), hr(0.005)], k=hr(0.009),
                     disp=tuft, disp_amp=0.004), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.023), hr(0.028), hr(0.026), hr(0.019), hr(0.01)], k=hr(0.01)), BROW)
    # wide eyes (the upper lids high), bags under them, crow's feet
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.026))), (sx * 0.2, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0058)), Plane(ec + v3((0, 0, -hr(0.024))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.add(Ellipsoid(hp((sx * 0.072, -0.161, 1.637)), v3((0.032, 0.012, 0.012)) * HS), hr(0.012), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.023))), (sx * 0.2, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(3):
            a = hp((sx * (0.112 + 0.004 * k), -0.132 + 0.006 * k, 1.69 - 0.013 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.026, 0.012, 0.008 - 0.011 * k)), hr(0.0022), hr(0.0014)), hr(0.003))
    # a big hooked nose: a hump on the bridge, the tip drooping
    fd.add(RoundCone(hp((0, -0.184, 1.728)), hp((0, -0.252, 1.634)), hr(0.016), hr(0.022)), hr(0.016), SKIN)
    fd.add(S((0, -0.22, 1.694), 0.02), hr(0.012), SKIN)
    fd.add(S((0, -0.253, 1.616), 0.027), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.031, -0.222, 1.602), 0.02), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.016, -0.24, 1.59)), v3((0.009, 0.011, 0.007)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
        fd.sub(Chain([hp((sx * 0.046, -0.212, 1.602)), hp((sx * 0.07, -0.19, 1.578)), hp((sx * 0.08, -0.168, 1.552))],
                     [hr(0.0026), hr(0.003), hr(0.0022)], k=hr(0.003)), hr(0.004))        # the grin's folds
    # the grin: open, the corners drawn up, a full lower lip
    slot = mouth_slot()
    fd.sub(Chain(slot, [hr(0.003), hr(0.0085), hr(0.011), hr(0.0085), hr(0.003)], k=hr(0.004)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.0045), hr(0.011), hr(0.0135), hr(0.011), hr(0.0045)], k=hr(0.005)), MOUTH)
    lo_lip = [(-0.058, -0.162, 1.556), (-0.032, -0.188, 1.529), (0, -0.196, 1.52), (0.032, -0.188, 1.529), (0.058, -0.162, 1.556)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.004), hr(0.0072), hr(0.008), hr(0.0072), hr(0.004)], k=hr(0.007)), hr(0.008), LIP)
    # big ears
    for sx in (-1, 1):
        fd.add(Ellipsoid(hp((sx * 0.18, 0.035, 1.664)), v3((0.029, 0.054, 0.07)) * HS, R=euler(0, sx * 0.25, sx * -0.35)), hr(0.02), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.2, 0.028, 1.668)), v3((0.013, 0.034, 0.045)) * HS, R=euler(0, 0, sx * -0.35)), hr(0.01))
        fd.add(Sphere(hp((sx * 0.187, 0.03, 1.604)), hr(0.017)), hr(0.01), SKIN)


def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        fd.add(deltoid(side), 0.055, SKIN)
        fd.add(RoundCone(sh, el, 0.09, 0.07), 0.05, SKIN)
        fd.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.022, 0)), (0.08, 0.082, 0.12), R=rot_from_axes(z_axis=el - sh)), 0.04, SKIN)
        fd.add(RoundCone(el, wr, 0.068, 0.054), 0.035, SKIN)
        fd.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.085, 0.076, 0.125), R=rot_from_axes(z_axis=wr - el)), 0.04, SKIN)
        fd.add(Sphere(el + v3((0, 0.025, 0)), 0.053), 0.028, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def leg_prims(side):
    hip, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
    return [(RoundCone(hip, kn, 0.13, 0.086), 0.065),
            (Ellipsoid(lerp(hip, kn, 0.42) + v3((0, -0.02, 0)), (0.115, 0.11, 0.18), R=rot_from_axes(z_axis=kn - hip)), 0.048),
            (Sphere(kn + v3((0, -0.03, 0.0)), 0.066), 0.038),
            (RoundCone(kn, an, 0.082, 0.055), 0.038),
            (Ellipsoid(lerp(kn, an, 0.3) + v3((0, 0.03, 0)), (0.09, 0.088, 0.135), R=rot_from_axes(z_axis=an - kn)), 0.043)]


def skin_field():
    fd = Field("Skin")
    body_parts(fd)
    return fd


def teeth_field():
    """His upper teeth, showing in the grin under the moustache."""
    fd = Field("Teeth")
    slot = mouth_slot()
    pts = [lerp(slot[1], slot[2], 0.1), slot[2], lerp(slot[3], slot[2], 0.1)]
    pts = [p + v3((0, 0.006, 0.0045)) for p in pts]
    fd.add(Chain(pts, [hr(0.0062), hr(0.0068), hr(0.0062)], k=hr(0.004)), 0.0)
    return fd


# ======================================================================================= moustache
def moustache_field():
    """A huge white handlebar moustache: two thick locks from under his nose sweeping out over the grin past his cheeks,
    their ends curled up."""
    fd = Field("Moustache")
    strands = lambda P: F(0.0022) * NOISE(P * np.array([80, 80, 30], F)) + F(0.001) * NOISE(P * F(160))
    for sx in (-1, 1):
        pts = [hp((sx * 0.004, -0.244, 1.596)), hp((sx * 0.046, -0.234, 1.588)), hp((sx * 0.09, -0.204, 1.576)),
               hp((sx * 0.13, -0.17, 1.574)), hp((sx * 0.162, -0.15, 1.594)), hp((sx * 0.172, -0.15, 1.628)),
               hp((sx * 0.162, -0.156, 1.648))]
        fd.add(Lock(pts, [hr(0.021), hr(0.03), hr(0.028), hr(0.02), hr(0.013), hr(0.009), hr(0.005)],
                    [hr(0.014), hr(0.017), hr(0.015), hr(0.011), hr(0.009), hr(0.007), hr(0.004)],
                    [norm(v3((sx * 0.3, -1, 0.15)))] * 3 + [norm(v3((sx * 0.6, -1, 0.0)))] * 4, k=hr(0.007),
                    disp=strands, disp_amp=0.003), hr(0.008))
    return fd


# ======================================================================================= hair (wild, white)
def _hairline(Q):
    """> 0 where his head is bare (design coordinates): the face, the bald crown and forehead, round the ears."""
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    yl = F(-0.075) + F(0.11) * smoothstep(1.76, 1.9, z)                # the hairline: at the temples, back over the crown
    front = yl - y
    ears = np.where((ax > F(0.12)) & (z < F(1.72)) & (y < F(0.075)), F(0.02), F(-1.0))
    nape = F(1.6) - z
    return np.maximum(np.maximum(front, ears), nape)


def tuft_specs():
    """(angle round his head from the front (deg), height (design z), length, width, lift up, sweep back)."""
    rs = np.random.RandomState(17)
    out = []
    rows = [(1.645, (102, 126, 150, 172), 0.085, 0.032, -0.3, 0.35),
            (1.73, (86, 106, 128, 150, 172), 0.13, 0.04, 0.15, 0.3),
            (1.815, (94, 118, 142, 166), 0.12, 0.038, 0.55, 0.25)]
    for z, angs, L, w, lift, back in rows:
        for sx in (-1, 1):
            for a in angs:
                out.append((sx * (a + rs.uniform(-6, 6)), z + rs.uniform(-0.012, 0.012), L * rs.uniform(0.85, 1.15), w,
                            lift + rs.uniform(-0.15, 0.15), back))
    for a, L in ((150, 0.09), (-150, 0.09), (178, 0.1), (128, 0.08), (-128, 0.08)):      # over the crown, up and back
        out.append((a + rs.uniform(-5, 5), 1.89 + rs.uniform(-0.01, 0.01), L, 0.036, 1.1, 0.7))
    return out


def hair_field():
    """A shell of white hair round the back and sides of his head (from the temples back; the crown and the forehead
    bare), below the goggles' strap."""
    fd = Field("Hair")
    strands = lambda P: F(0.003) * NOISE(P * np.array([60, 60, 18], F)) + F(0.0015) * NOISE(P * F(110))
    keep = Func(lambda P: _hairline(hinv(P)), HEAD_C - 0.4, HEAD_C + 0.4)
    fd.add(Inter(Shell(Ellipsoid(HEAD_C, HEAD_RAD), hr(0.022), hr(0.03), pad=0.06, disp=strands, disp_amp=0.004), keep, 0.01), 0.0)
    fd.add(Ellipsoid(hp((0.0, 0.17, 1.65)), v3((0.13, 0.07, 0.07)) * HS, disp=strands, disp_amp=0.003), hr(0.03))   # full at the nape
    return fd


def tufts_field():
    """The wild tufts standing out of it: round the sides and the back, sweeping out and back, the upper ones lifting,
    a few up over the crown (on their own bone, `hair`: they bristle when the coil fires)."""
    fd = Field("Tufts")
    hull = Ellipsoid(HEAD_C, HEAD_RAD + hr(0.04))
    strands = lambda P: F(0.0025) * NOISE(P * np.array([70, 70, 22], F)) + F(0.0012) * NOISE(P * F(130))
    rs = np.random.RandomState(29)
    for a, z, L, w, lift, back in tuft_specs():
        ar = math.radians(a)
        d0 = v3((math.sin(ar), -math.cos(ar), 0.0))
        c = hp((0.0, 0.03, z))
        h, ok = ray_hit(hull, [c + d0 * 0.6], [-d0], tmax=0.7)
        if not ok[0]:
            continue
        root = h[0]
        n = norm(root - HEAD_C)
        d = norm(n + Z * lift + v3((0, 1, 0)) * back + v3(rs.uniform(-0.15, 0.15, 3)))
        curl = norm(Z * (0.6 if lift > 0 else -0.4) + v3((0, 1, 0)) * 0.4)
        pts, ws, ts, ns = [], [], [], []
        for i in range(6):
            u = i / 5.0
            p = root - n * hr(0.03) * (1 - u) + d * (hr(L) * u) + curl * (hr(L) * 0.35 * u * u)
            pts.append(p)
            ws.append(hr(w) * (0.75 + 0.5 * math.sin(min(1.0, u / 0.4) * math.pi / 2)) * (1 - 0.85 * u ** 1.4) + 0.002)
            ts.append(hr(0.018) * (1 - 0.7 * u) + 0.002)
            ref = Z if abs(d @ Z) < 0.8 else v3((0, 1, 0))
            ns.append(norm(ref - d * (ref @ d)))
        fd.add(Lock(pts, ws, ts, ns, k=hr(0.008), disp=strands, disp_amp=0.003), hr(0.01))
    return fd


# ======================================================================================= goggles (on his forehead)
STRAP_C = hp((0.0, -0.17, 1.868))              # the strap's middle on his forehead (design point)
STRAP_N = norm(v3((0.0, 0.3, 1.0)))            # its plane tilts down toward the back of his head


def goggle_frames():
    """(centre on the forehead, outward axis) for each lens: on the strap, either side of the middle, tipped up."""
    hull = brow_hull()
    out = []
    for sx in (-1, 1):
        o = hp((sx * 0.052, -0.6, 1.872))
        h, ok = ray_hit(hull, [o], [v3((0, 1, 0))], tmax=0.8)
        p = h[0] if ok[0] else hp((sx * 0.052, -0.16, 1.872))
        e = 0.004
        P = np.array([p + v3(d) * e for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))], F)
        dd = hull.eval(P)
        n = norm(v3((dd[0] - dd[1], dd[2] - dd[3], dd[4] - dd[5])))
        out.append((p, norm(n + Z * 0.25)))
    return out


def goggles_field():
    """Brass goggles (5) pushed up on his forehead: two cups with rolled rims and bottle-green lenses (12), a brass
    bridge, leather pads behind them; the leather strap (4) round his head (under the hair at the back)."""
    fd = Field("Goggles")
    hull = brow_hull()
    lo, hi = HEAD_C - 0.32, HEAD_C + 0.32
    def strap(P):
        Q = hinv(P)
        band = np.abs((Q - STRAP_C.astype(F)) @ STRAP_N.astype(F)) - F(0.017)
        d = hull.eval(P, margin=0.04)
        return np.maximum(np.abs(d - F(hr(0.009))) - F(hr(0.0045)), band * F(HS))
    fd.add(Func(strap, lo, hi), 0.0, LEATHER)
    fr = goggle_frames()
    for p, a in fr:
        R = rot_from_axes(z_axis=a)
        fd.add(Cylinder(p + a * hr(0.004), hr(0.042), hr(0.014), rr=hr(0.005), R=R), hr(0.004), LEATHER)     # the pad
        fd.add(Cylinder(p + a * hr(0.024), hr(0.036), hr(0.03), rr=hr(0.006), R=R), hr(0.004), BRASS)       # the cup
        fd.add(Torus(p + a * hr(0.039), hr(0.033), hr(0.0065), R=R), hr(0.003), BRASS)                      # its rim
        fd.add(Cylinder(p + a * hr(0.038), hr(0.029), hr(0.006), rr=hr(0.002), R=R), hr(0.002), GLASS)      # the lens
        for k in range(6):                                                                              # vent holes
            ang = 2 * math.pi * k / 6
            u = norm(np.cross(a, Z))
            v = np.cross(a, u)
            fd.sub(Sphere(p + a * hr(0.022) + (u * math.cos(ang) + v * math.sin(ang)) * hr(0.037), hr(0.005)), hr(0.002))
    (p0, a0), (p1, a1) = fr
    m = (p0 + p1) / 2 + norm(a0 + a1) * hr(0.03)
    fd.add(Chain([p0 + a0 * hr(0.03) + norm(p1 - p0) * hr(0.03), m, p1 + a1 * hr(0.03) - norm(p1 - p0) * hr(0.03)],
                 [hr(0.006), hr(0.007), hr(0.006)], k=hr(0.003)), hr(0.003), BRASS)
    return fd


# ======================================================================================= the lab coat (white linen)
WAIST_Z = 0.98
HEM_Z = 0.44
COAT_OFF, COAT_T = 0.04, 0.014
SLEEVE_OFF = 0.026
FLAP = 0.01                      # lapels and pockets: a layer on top of the coat
CUFF_S = 0.09                    # the sleeves end this far above the wrist (under the gauntlets' cuffs)


def coat_base():
    b = Field("CoatBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(RoundCone((0.0, 0.04, 0.95), (0.0, 0.07, 0.44), 0.235, 0.3), 0.08)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
        b.add(deltoid(side), 0.055)
        b.add(RoundCone(sh, el, 0.09, 0.07), 0.05)
        b.add(Ellipsoid(lerp(sh, el, 0.48) + v3((0, -0.022, 0)), (0.08, 0.082, 0.12), R=rot_from_axes(z_axis=el - sh)), 0.04)
        b.add(RoundCone(el, wr, 0.068, 0.056), 0.035)
        b.add(Ellipsoid(lerp(el, wr, 0.3) + v3((sx * 0.008, 0, 0)), (0.085, 0.076, 0.125), R=rot_from_axes(z_axis=wr - el)), 0.04)
        b.add(Sphere(el + v3((0, 0.025, 0)), 0.053), 0.028)
    return b


def _ang(P):
    """The angle round his body from straight ahead (0) to straight behind (pi), and the distance from its axis."""
    dx, dy = P[:, 0], P[:, 1] - F(0.04)
    return np.arctan2(np.abs(dx), -dy), np.sqrt(dx * dx + dy * dy)


def _below(z):
    return smoothstep(WAIST_Z, HEM_Z, z)


def front_a(z):
    """The coat's front edge (an angle round him): open over the waistcoat, hanging a little wider toward the hem."""
    return F(0.34) + F(0.16) * smoothstep(1.05, HEM_Z, z)


def hem_z(P):
    a, r = _ang(P)
    return F(HEM_Z) - F(0.015) * (F(1) - np.cos(a)) / F(2) + F(0.006) * NOISE(P * F(8))


def _arm_s(P, side, seg):
    """Distance along an arm segment (0: upper arm, 1: forearm), the squared distance off its axis, its length."""
    sh, el, wr = J["shoulder_" + side], J["elbow_" + side], J["wrist_" + side]
    a, b = (sh, el) if seg == 0 else (el, wr)
    ax = norm(b - a)
    L = float(np.linalg.norm(b - a))
    q = P - a.astype(F)
    s = q @ ax.astype(F)
    perp = q - s[:, None] * ax.astype(F)[None, :]
    return s, (perp ** 2).sum(1), L


def _sleeve_end(P):
    """> 0 past the sleeves' ends above the wrists (only round each forearm)."""
    out = F(-1.0) * np.ones(len(P), F)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        s, d2, L = _arm_s(P, side, 1)
        lateral = P[:, 0] * F(sx) - F(0.42)
        out = np.maximum(out, np.where((lateral > 0) & (d2 < F(0.16 ** 2)), s - F(L - CUFF_S), F(-1.0)))
    return out


def _neck_open(P):
    """> 0 inside the coat's opening round his neck (near the neck's axis only)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    yn = F(0.07) - F(0.2) * np.clip(z - F(1.36), 0, None)
    rho = np.sqrt(x * x + (F(0.9) * (y - yn)) ** 2)
    return np.minimum(F(0.138) - rho, z - F(1.38))


def coat_cut(P):
    """< 0 where the coat is: open down the front, a vent behind, round the neck, at the sleeves' ends, at the hem."""
    a, r = _ang(P)
    z = P[:, 2]
    front = (front_a(z) - a) * np.maximum(r, F(0.1))
    vent = np.where(z < F(0.74), (a - F(math.pi - 0.035)) * np.maximum(r, F(0.1)), F(-1.0))
    return np.maximum(np.maximum(np.maximum(front, vent), np.maximum(_neck_open(P), _sleeve_end(P))), hem_z(P) - z)


def lapel_w(z):
    return F(0.12) + F(0.3) * smoothstep(1.06, 1.38, z)


def lapel_region(P):
    """< 0 on the wide notched lapels: a band beside the front edge from the collar down to the top button."""
    a, r = _ang(P)
    z = P[:, 2]
    w = lapel_w(z)
    band = np.maximum(front_a(z) - a, a - (front_a(z) + w)) * np.maximum(r, F(0.1))
    notch = np.maximum(np.abs(z - F(1.372)) - F(0.011), (front_a(z) + w * F(0.55)) - a)          # the notch
    return np.maximum(np.maximum(np.maximum(band, F(1.05) - z), P[:, 1] + F(0.02)), -notch)


POCKETS = [(1.08, 0.66, 0.84, None), (0.98, 1.17, 1.29, 1)]      # (angle, z0, z1, only that side): the hips', the breast's


def pocket_region(P):
    """< 0 on the patch pockets: one on each hip, one on his left breast."""
    a, r = _ang(P)
    z = P[:, 2]
    out = F(1.0) * np.ones(len(P), F)
    for i, (ac, z0, z1, only) in enumerate(POCKETS):
        hw = F(0.25) if z1 < 1.0 else F(0.19)
        d = np.maximum(np.abs(a - F(ac)) * np.maximum(r, F(0.1)) - hw * F(0.25), np.maximum(F(z0) - z, z - F(z1)))
        if only is not None:
            d = np.where(P[:, 0] * F(only) > 0, d, F(1.0))
        out = np.minimum(out, d)
    return out


def coat_field():
    """White linen (label 0): to the knee, hanging open over the waistcoat, a vent behind; wide notched lapels and patch
    pockets (a layer raised a little over the coat); a turned-down collar; scorch marks (6) at the cuffs, on the right hip
    and along the hem."""
    fd = Field("Coat")
    base = coat_base()
    lo, hi = (-0.86, -0.42, 0.38), (0.86, 0.46, 1.57)
    def coat_all(P):
        d = base.eval(P, margin=0.1)
        x = np.abs(P[:, 0])
        arm = smoothstep(0.33, 0.44, x)
        z = P[:, 2]
        a, r = _ang(P)
        below = _below(z)
        folds = (F(0.007) * np.sin(a * F(9) + F(0.8) * NOISE(P * F(2))) * below + F(0.0016) * NOISE(P * F(14))) * (F(1) - arm)
        off = F(COAT_OFF) - F(COAT_OFF - SLEEVE_OFF) * arm + folds + F(0.014) * below
        main = np.abs(d - off) - F(COAT_T * 0.5)
        flap = np.abs(d - off - F(COAT_T * 0.5 + FLAP * 0.5 - 0.002)) - F(FLAP * 0.5)
        reg = np.minimum(lapel_region(P), pocket_region(P))
        return smax(smin(main, np.maximum(flap, reg), 0.003), coat_cut(P), 0.004)
    fd.add(Func(coat_all, lo, hi), 0.0)
    # the pockets' mouths: a groove along each top edge
    def mouths(P):
        a, r = _ang(P)
        z = P[:, 2]
        out = F(1.0) * np.ones(len(P), F)
        for ac, z0, z1, only in POCKETS:
            hw = F(0.25) if z1 < 1.0 else F(0.19)
            d = np.maximum(np.abs(a - F(ac)) * np.maximum(r, F(0.1)) - hw * F(0.25) + F(0.006), np.abs(z - F(z1 - 0.004)) - F(0.003))
            if only is not None:
                d = np.where(P[:, 0] * F(only) > 0, d, F(1.0))
            out = np.minimum(out, d)
        return np.maximum(out, np.abs(base.eval(P, margin=0.1) - F(COAT_OFF + 0.014 * 0.0 + COAT_T * 0.5 + FLAP)) - F(0.012))
    fd.sub(Func(mouths, lo, hi), 0.002)
    # the collar: turned down round the back of his neck, its points on the lapels
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    nk.add(traps(), 0.06)
    def collar(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        top = F(1.47) + F(0.04) * smoothstep(-0.02, 0.1, y)
        return np.maximum(np.maximum(z - top, F(1.37) - z), np.where(y < F(-0.02), F(0.075) - np.abs(x), F(-1.0)))
    fd.add(Inter(Shell(nk, 0.034, 0.014, pad=0.1), Func(collar, (-0.4, -0.4, 1.3), (0.4, 0.4, 1.6)), 0.004), 0.004)
    # scorch marks
    def scorch(P):
        n = F(0.4) * NOISE(P * F(9)) + F(0.25) * NOISE(P * F(23))
        out = F(1.0) * np.ones(len(P), F)
        for side in ("R", "L"):
            s, d2, L = _arm_s(P, side, 1)
            out = np.minimum(out, np.where(d2 < F(0.16 ** 2), (np.abs(s - F(L - CUFF_S - 0.03)) - F(0.05)) / F(0.05) + n, F(1.0)))
        hip = np.sqrt((P[:, 0] + F(0.2)) ** 2 + ((P[:, 1] + F(0.17)) * F(1.5)) ** 2 + ((P[:, 2] - F(0.62)) * F(0.8)) ** 2) / F(0.07) - F(1) + n
        hem = (P[:, 2] - hem_z(P) - F(0.045)) / F(0.03) + n * F(1.6) + F(0.6) * (NOISE(P * F(3)) + F(0.3))
        return np.minimum(np.minimum(out, hip), hem) * F(0.02)
    fd.paint(Func(scorch, lo, hi), 6)
    return fd


# ======================================================================================= waistcoat (navy), shirt, bow tie
def waistcoat_base():
    b = Field("WaistcoatBase")
    for p, k in torso_prims():
        b.add(p, k)
    b.add(traps(), 0.06)
    b.add(RoundCone((0.0, 0.04, 0.95), (0.0, 0.05, 0.74), 0.225, 0.24), 0.08)
    return b


WC_OFF = 0.022


def waistcoat_keep(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    yn = F(0.07) - F(0.2) * np.clip(z - F(1.36), 0, None)
    rho = np.sqrt(x * x + (F(0.9) * (y - yn)) ** 2)
    neck = np.minimum(F(0.12) - rho, z - F(1.36))
    vee = np.where(y < F(0.02), (z - (F(1.17) + F(2.1) * ax)) * F(0.4), F(-1.0))                  # the V opening
    hem = F(0.8) - F(0.055) * np.exp(-((ax - F(0.06)) / F(0.045)) ** 2) * (y < F(0.0))          # two points at the front
    return np.maximum(np.maximum(np.maximum(neck, vee), hem - z), np.maximum(y - F(0.15), ax - F(0.3)))


def waistcoat_field():
    """Navy wool (label 0), single-breasted, cut in a V over the shirt front, two points at its foot; welt pockets."""
    fd = Field("Waistcoat")
    base = waistcoat_base()
    lo, hi = (-0.6, -0.6, 0.6), (0.6, 0.4, 1.6)
    fd.add(Inter(Shell(base, WC_OFF, 0.012, pad=0.1, disp=lambda P: F(0.0012) * NOISE(P * F(20)), disp_amp=0.002),
                 Func(waistcoat_keep, lo, hi), 0.004), 0.0)
    for sx in (-1, 1):                                                       # welt pockets
        o = v3((sx * 0.13, -0.6, 0.93))
        h, ok = ray_hit(Func(lambda P: base.eval(P, margin=0.1) - F(WC_OFF + 0.006), (-1, -1, 0.5), (1, 1, 1.6)), [o], [v3((0, 1, 0))], tmax=0.8)
        if ok[0]:
            fd.add(RoundBox(h[0] + v3((0, -0.002, 0)), (0.05, 0.006, 0.008), 0.003, R=euler(0, 0, sx * 0.25)), 0.002)
    return fd


def shirt_field():
    """White linen (label 0): the shirt front in the waistcoat's V, a wing collar round his neck; the crimson bow tie (6)."""
    fd = Field("Shirt")
    base = waistcoat_base()
    fd.add(Inter(Shell(base, 0.012, 0.012, pad=0.1), Func(lambda P: np.maximum(np.maximum(F(1.12) - P[:, 2], P[:, 2] - F(1.44)),
                                                                         np.maximum(np.abs(P[:, 0]) - F(0.17), P[:, 1] + F(0.0))),
                                                         (-0.4, -0.5, 1.0), (0.4, 0.3, 1.6)), 0.004), 0.0)
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    fd.add(Inter(Shell(nk, 0.014, 0.012, pad=0.08), Func(lambda P: np.abs(P[:, 2] - F(1.452)) - F(0.042), (-0.3, -0.3, 1.3), (0.3, 0.3, 1.56)),
                 0.004), 0.0)
    K = bow_knot()
    for sx in (-1, 1):                                                       # the wing tips, folded down
        tip = K + v3((sx * 0.03, -0.004, 0.026))
        fd.add(Lock([tip + v3((sx * -0.01, 0.006, 0.012)), tip, tip + v3((sx * 0.012, -0.004, -0.014))], [0.014, 0.016, 0.008],
                    [0.004, 0.004, 0.003], [v3((0, -1, 0))] * 3, k=0.003), 0.003)
    # the bow tie
    tie = lambda P: F(0.0012) * NOISE(P * F(60))
    for sx in (-1, 1):
        fd.add(Ellipsoid(K + v3((sx * 0.04, -0.004, 0.0)), (0.036, 0.012, 0.024), R=euler(0, sx * -0.15, 0), disp=tie, disp_amp=0.002), 0.008, 6)
        fd.sub(RoundCone(K + v3((sx * 0.03, -0.018, 0.012)), K + v3((sx * 0.03, -0.018, -0.012)), 0.003, 0.003), 0.003)
    fd.add(Ellipsoid(K + v3((0, -0.01, 0)), (0.014, 0.012, 0.016)), 0.004, 6)
    return fd


def bow_knot():
    nk = Field("Neck")
    nk.add(neck_prim(), 0.0)
    h, ok = ray_hit(Func(lambda P: nk.eval(P, margin=0.06) - F(0.03), (-0.4, -0.4, 1.2), (0.4, 0.4, 1.7)), [v3((0, -0.6, 1.418))], [v3((0, 1, 0))], tmax=0.8)
    return h[0] if ok[0] else v3((0.0, -0.075, 1.418))


# ======================================================================================= trousers, boots
def legs_base():
    b = Field("Legs")
    tp = torso_prims()
    b.add(tp[5][0], 0.0)
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            b.add(p, k)
    return b


def trousers_field():
    """Charcoal wool (label 0) from his waist to his boots, wrinkled at the knees and breaking over the boots."""
    fd = Field("Trousers")
    lb = legs_base()
    lo, hi = v3((-0.5, -0.4, 0.08)), v3((0.5, 0.45, 1.06))
    def fn(P):
        d = lb.eval(P, margin=0.08)
        z = P[:, 2]
        off = F(0.013) + F(0.022) * smoothstep(0.34, 0.17, z)
        return np.abs(d - off) - F(0.0065)
    wr = lambda P: F(0.0016) * NOISE(P * np.array([30, 30, 60], F)) + F(0.003) * np.sin(P[:, 2] * F(70) + F(2) * NOISE(P * F(5))) * smoothstep(0.3, 0.14, P[:, 2])
    fd.add(Inter(Func(fn, lo, hi, disp=wr, disp_amp=0.004), Func(lambda P: np.maximum(F(0.125) - P[:, 2], P[:, 2] - F(0.99)), lo, hi), 0.004), 0.0)
    return fd


def foot_hull(side):
    ft = Field("FootHull")
    foot(ft, side)
    kn, an = J["knee_" + side], J["ankle_" + side]
    ft.add(RoundCone(kn, an, 0.082, 0.055), 0.03)
    return ft


def boots_field():
    """Brown leather ankle boots (label 0), thick soles and heels."""
    fd = Field("Boots")
    crease = lambda P: F(0.0014) * NOISE(P * F(26))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        ft = foot_hull(side)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        fd.add(Inter(Shell(ft, 0.002, 0.02, pad=0.06, disp=crease, disp_amp=0.002), Func(lambda P: P[:, 2] - F(0.2), an - 0.35, an + 0.35), 0.006), 0.0)
        fd.add(RoundBox(an + fwd * 0.078 + v3((0, 0, -0.1)), (0.072, 0.16, 0.013), 0.01, R=Rz), 0.008)
        fd.add(RoundBox(an + fwd * -0.035 + v3((0, 0, -0.082)), (0.058, 0.05, 0.03), 0.012, R=Rz), 0.008)
    return fd


# ======================================================================================= rubber gauntlets
def gloves_field():
    """Thick black rubber gauntlets (label 9) over his fists, their cuffs flaring over the coat's sleeves."""
    fd = Field("Gloves")
    for side in ("R", "L"):
        hh = Field("HandHull")
        hand(hh, side)
        fd.add(Shell(hh, 0.008, 0.012, pad=0.05, disp=lambda P: F(0.0008) * NOISE(P * F(50)), disp_amp=0.001), 0.0, RUBBER)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        def cuff(P, wr=wr, ax=ax):
            s = (P - wr.astype(F)) @ ax.astype(F)
            q = P - wr.astype(F) - s[:, None] * ax.astype(F)[None, :]
            rho = np.sqrt((q * q).sum(1))
            R = F(0.084) - F(0.21) * s
            return np.maximum(np.abs(rho - R) - F(0.006), np.maximum(-s - F(0.17), s - F(0.03)))
        fd.add(Func(cuff, wr - 0.3, wr + 0.3, disp=lambda P: F(0.001) * NOISE(P * F(30)), disp_amp=0.001), 0.012, RUBBER)
        rim_c = wr - ax * 0.168
        fd.add(Torus(rim_c, 0.084 + 0.21 * 0.168, 0.008, R=rot_from_axes(z_axis=ax)), 0.004, RUBBER)
    return fd


# ======================================================================================= brass: buttons, watch chain, pens
def _surface_pt(fn, o, d, tmax=1.0):
    h, ok = ray_hit(fn, [o], [d], tmax=tmax)
    return h[0] if ok[0] else None


def wc_outer():
    wb = waistcoat_base()
    return Func(lambda P: wb.eval(P, margin=0.14) - F(WC_OFF + 0.006), (-1, -1, 0.5), (1, 1, 1.8))


BUTTON_Z = (1.15, 1.075, 1.0, 0.925, 0.85)


def brass_field():
    """Brass (5): the waistcoat's buttons, the watch chain from the third button to his left pocket, a fob; in the coat's
    breast pocket a red pencil (14, its tip bare wood, 7) and a brass pen."""
    fd = Field("Brass")
    wc = wc_outer()
    btn = []
    for z in BUTTON_Z:
        p = _surface_pt(wc, v3((0, -0.8, z)), v3((0, 1, 0)))
        if p is not None:
            btn.append(p)
            fd.add(Ellipsoid(p + v3((0, -0.003, 0)), (0.011, 0.0065, 0.011)), 0.0, BRASS)
    pts = []
    for x, z in ((0.0, 1.0), (0.04, 0.975), (0.08, 0.958), (0.115, 0.958), (0.14, 0.94)):
        p = _surface_pt(wc, v3((x, -0.8, z)), v3((0, 1, 0)))
        if p is not None:
            pts.append(p + v3((0, -0.006, 0)))
    if len(pts) >= 3:
        fd.add(Chain(pts, [0.0045] * len(pts), k=0.002, disp=lambda P: F(0.0012) * np.sin(P[:, 0] * F(900)), disp_amp=0.0012), 0.002, BRASS)
        fob = pts[2] + v3((0, -0.004, -0.03))
        fd.add(Chain([pts[2], fob], [0.003, 0.003], k=0.0), 0.002, BRASS)
        fd.add(Ellipsoid(fob + v3((0, 0, -0.012)), (0.012, 0.004, 0.014)), 0.003, BRASS)
    # the breast pocket's pencil and pen
    base = coat_base()
    co = Func(lambda P: base.eval(P, margin=0.14) - F(COAT_OFF + COAT_T * 0.5 + FLAP), (-1, -1, 0.5), (1, 1, 1.8))
    for k, (dx, ln, lab) in enumerate(((-0.018, 0.11, RED), (0.016, 0.1, BRASS))):
        a = POCKETS[1][0] + dx * 4.0
        d = v3((math.sin(a), -math.cos(a), 0.0))
        o = v3((0, 0.04, 1.25)) + d * 0.8
        p = _surface_pt(co, o, -d)
        if p is None:
            continue
        b = p - d * 0.012 + v3((0, 0, -0.03))
        t = b + v3((0.004 * (k * 2 - 1), 0.0, ln))
        fd.add(RoundCone(b, t, 0.0065, 0.0065), 0.002, lab)
        if lab == RED:
            fd.add(RoundCone(t, t + v3((0, 0, 0.02)), 0.0062, 0.0015), 0.002, WOOD)
        else:
            fd.add(RoundCone(t - v3((0, 0, 0.04)), t - v3((0, 0, 0.04)) + d * 0.012, 0.0025, 0.002), 0.002, BRASS)     # its clip
    return fd


# ======================================================================================= the coil (machine bone)
COIL_C = v3((0.56, 0.26, 0.0))                # the coil's axis at the floor
PL_R = 0.225                                 # the plinth's drum
PL_TOP = 0.44
DECK_TOP = 0.485
SEC_R = 0.088                                # the secondary's former
SEC_Z0, SEC_Z1 = 0.535, 1.86
BANDS = ((0.575, 0.89), (0.915, 1.23), (1.255, 1.57), (1.595, 1.83))
TOR_Z, TOR_R, TOR_r = 2.12, 0.2, 0.085
TOR_C = COIL_C + Z * TOR_Z                   # the toroid's centre (the game's lightning leaves from here)
BALL = TOR_C + Z * 0.15                      # the breakout point's ball
COIL_FRONT = norm(v3((-0.25, -1.0, 0.0)))    # the plinth's voltmeter faces the robots


def coil_field():
    fd = Field("Coil")
    c = COIL_C
    rv = lambda P: F(0.0006) * NOISE(P * F(50))
    # the plinth: riveted iron, a flared foot and a top flange
    fd.add(Cylinder(c + Z * 0.028, 0.272, 0.056, rr=0.016, disp=rv, disp_amp=0.001), 0.0, IRON)
    fd.add(Cylinder(c + Z * 0.24, PL_R, 0.4, rr=0.012, disp=rv, disp_amp=0.001), 0.012, IRON)
    fd.add(Cylinder(c + Z * (PL_TOP - 0.016), 0.252, 0.036, rr=0.012), 0.008, IRON)
    for zb in (0.105, 0.36):
        fd.add(Torus(c + Z * zb, PL_R + 0.002, 0.012), 0.003, IRON)
        for k in range(18):
            a = 2 * math.pi * (k + 0.5) / 18
            fd.add(Sphere(c + v3((math.cos(a), math.sin(a), 0)) * (PL_R + 0.013) + Z * zb, 0.0075), 0.002, IRON)
    for k in range(22):
        a = 2 * math.pi * k / 22
        fd.add(Sphere(c + v3((math.cos(a), math.sin(a), 0)) * 0.252 + Z * 0.057, 0.008), 0.002, IRON)
    fa = math.atan2(COIL_FRONT[1], COIL_FRONT[0])
    for k in range(4):                                                     # vertical seams with rivets
        a = fa + math.pi / 4 + k * math.pi / 2
        d = v3((math.cos(a), math.sin(a), 0))
        fd.add(RoundBox(c + d * (PL_R + 0.002) + Z * 0.233, (0.02, 0.004, 0.115), 0.003, R=rot_from_axes(y_axis=d, z_axis=Z)), 0.003, IRON)
        for zz in (0.16, 0.233, 0.306):
            fd.add(Sphere(c + d * (PL_R + 0.008) + Z * zz, 0.0075), 0.002, IRON)
    # the voltmeter on its front: a brass case, a cream dial, a red needle
    gc = c + COIL_FRONT * (PL_R + 0.012) + Z * 0.235
    Rg = rot_from_axes(z_axis=COIL_FRONT)
    fd.add(Cylinder(gc, 0.082, 0.035, rr=0.01, R=Rg), 0.006, BRASS)
    fd.add(Torus(gc + COIL_FRONT * 0.018, 0.074, 0.008, R=Rg), 0.003, BRASS)
    fd.add(Cylinder(gc + COIL_FRONT * 0.016, 0.066, 0.006, rr=0.002, R=Rg), 0.002, ENAMEL)
    gu = norm(Z - COIL_FRONT * (Z @ COIL_FRONT))
    gs = np.cross(COIL_FRONT, gu)
    for k in range(9):                                                     # the scale's ticks
        a = math.radians(-60 + 15 * k)
        dd = gu * math.cos(a) + gs * math.sin(a)
        fd.add(RoundCone(gc + COIL_FRONT * 0.02 + dd * 0.045, gc + COIL_FRONT * 0.02 + dd * 0.056, 0.002, 0.002), 0.0, RUBBER)
    nd = gu * math.cos(math.radians(28)) + gs * math.sin(math.radians(28))
    fd.add(RoundCone(gc + COIL_FRONT * 0.021, gc + COIL_FRONT * 0.021 + nd * 0.052, 0.0035, 0.0018), 0.001, RED)
    fd.add(Sphere(gc + COIL_FRONT * 0.021, 0.006), 0.001, BRASS)
    # the cable's brass gland at the plinth's foot (toward the console)
    gd = norm(v3((CON_P[0] - c[0], CON_P[1] - c[1], 0.0)) + v3((0.0, -1.2, 0.0)))
    fd.add(Cylinder(c + gd * (PL_R + 0.022) + Z * 0.075, 0.034, 0.05, rr=0.008, R=rot_from_axes(z_axis=gd)), 0.004, BRASS)
    # the deck (varnished wood), the primary on four porcelain insulators
    fd.add(Cylinder(c + Z * (DECK_TOP - 0.022), 0.238, 0.044, rr=0.012, disp=rv, disp_amp=0.001), 0.004, WOOD)
    for k in range(4):
        a = fa + k * math.pi / 2
        d = v3((math.cos(a), math.sin(a), 0))
        pc = c + d * 0.178
        fd.add(Cylinder(pc + Z * (DECK_TOP + 0.075), 0.014, 0.15, rr=0.005), 0.003, PORC)
        for zz in (0.02, 0.05, 0.08, 0.11, 0.14):
            fd.add(Cylinder(pc + Z * (DECK_TOP + zz), 0.026, 0.012, rr=0.005), 0.004, PORC)
        fd.add(Sphere(pc + Z * (DECK_TOP + 0.155), 0.017), 0.004, PORC)
    hel = []
    for k in range(57):
        t = k / 56.0
        a = fa + 2 * math.pi * 2.75 * t
        hel.append(c + v3((math.cos(a), math.sin(a), 0)) * 0.178 + Z * (DECK_TOP + 0.035 + 0.1 * t))
    fd.add(Chain(hel, [0.012] * len(hel), k=0.002), 0.003, COPPER)
    # the secondary: a turned wooden collar, the former, four bands of winding with brass rings between
    fd.add(Cylinder(c + Z * (DECK_TOP + 0.025), 0.112, 0.05, rr=0.012), 0.006, WOOD)
    fd.add(Cylinder(c + Z * ((SEC_Z0 + SEC_Z1) / 2), SEC_R, SEC_Z1 - SEC_Z0, rr=0.005), 0.004, WOOD)
    turns = lambda P: F(0.0011) * np.sin(P[:, 2] * F(2 * math.pi / 0.0105))
    for z0, z1 in BANDS:
        fd.add(Cylinder(c + Z * ((z0 + z1) / 2), SEC_R + 0.006, z1 - z0, rr=0.003, disp=turns, disp_amp=0.0012), 0.002, WIND)
    for z0, z1 in zip([b[1] for b in BANDS[:-1]], [b[0] for b in BANDS[1:]]):
        fd.add(Torus(c + Z * ((z0 + z1) / 2), SEC_R + 0.006, 0.0075), 0.002, BRASS)
    fd.add(Torus(c + Z * (BANDS[0][0] - 0.012), SEC_R + 0.006, 0.0075), 0.002, BRASS)
    # the brass cap and standoff, the toroid, its centre disc, the breakout point
    fd.add(Cylinder(c + Z * (SEC_Z1 + 0.025), 0.1, 0.05, rr=0.012), 0.006, BRASS)
    fd.add(Torus(c + Z * (SEC_Z1 + 0.003), 0.098, 0.007), 0.003, BRASS)
    fd.add(RoundCone(c + Z * (SEC_Z1 + 0.05), TOR_C - Z * 0.05, 0.03, 0.024), 0.008, BRASS)
    fd.add(Torus(TOR_C, TOR_R, TOR_r, disp=lambda P: F(0.0005) * NOISE(P * F(30)), disp_amp=0.0006), 0.0, COPPER)
    fd.add(Ellipsoid(TOR_C + Z * 0.012, (0.15, 0.15, 0.05)), 0.02, COPPER)
    fd.add(Torus(TOR_C, TOR_R + TOR_r - 0.002, 0.006), 0.002, BRASS)
    fd.add(RoundCone(TOR_C + Z * 0.04, BALL - Z * 0.02, 0.012, 0.008), 0.005, BRASS)
    return fd


def charge_field():
    """The charge gathering on the toroid (shipped glowing faint cyan): a band along its crest, the breakout ball."""
    fd = Field("Charge")
    fd.add(Torus(TOR_C + Z * 0.075, TOR_R, 0.014), 0.0)
    fd.add(Sphere(BALL, 0.03), 0.0)
    return fd


# ======================================================================================= the switch console
CON_P = v3((-0.47, -0.3, 0.0))               # the pedestal's foot
CON_U = norm(v3((-CON_P[0], -CON_P[1], 0.0)))        # toward him (horizontal)
SLAB_H = 0.9                                 # the slab's middle above the floor
SN = norm(Z + CON_U * 0.35)                  # the slab's face (tilted toward him)
SU = norm(CON_U - SN * (CON_U @ SN))         # down the slab, toward him
SW = norm(np.cross(SU, SN))                  # across it (toward the robots' side)
R_SLAB = np.stack([SW, SU, SN], axis=1)
SLAB_C = CON_P + Z * SLAB_H
SLAB_HALF = (0.16, 0.24, 0.022)
HINGE_S, JAW_S, BAR_S = -0.135, 0.125, 0.165  # the hinge at the far (high) end, the jaws at the near end, the crossbar
BLADE_H = 0.05                               # the blades' axis over the slab's top
BLADE_W = 0.048                              # either side of the middle
BLADE_L = 0.31
HANDLE_L = 0.135                             # the bar -> the knob's centre
OPEN_DEG = 100.0                             # the switch's swing from closed (in the jaws) to open (standing up)


def slab_pt(w, s, h):
    return SLAB_C + SW * w + SU * s + SN * (SLAB_HALF[2] + h)


HINGE = slab_pt(0.0, HINGE_S, BLADE_H)
GRIP_REST = slab_pt(0.0, BAR_S, BLADE_H + 0.07)       # the fist's centre on the handle (switch closed, rest pose)
KNOB_REST = slab_pt(0.0, BAR_S, BLADE_H + HANDLE_L)
SWING_AX = SW                                          # + swings the blade up out of the jaws, away from him
BOARD_N = norm(SW + CON_U * 0.6 + Z * 0.25)            # the gauge board on the slab's back edge faces him and the robots
BOARD_UP = norm(Z - BOARD_N * (Z @ BOARD_N))
BOARD_X = norm(np.cross(BOARD_UP, BOARD_N))
BOARD_C = slab_pt(-(SLAB_HALF[0] - 0.005), -0.02, 0.0) + Z * 0.108


def gauge_centres():
    return [BOARD_C + BOARD_X * (sx * 0.075) + BOARD_N * 0.014 for sx in (-1, 1)]


def cable_path():
    """The twin cable: from under the slab down the back of the pedestal and over the floor in front of him to the coil's
    plinth."""
    back = -CON_U
    pts = [SLAB_C - SN * 0.05 + SU * -0.12, CON_P + back * 0.06 + Z * 0.62, CON_P + back * 0.065 + Z * 0.3,
           CON_P + back * 0.09 + Z * 0.06, CON_P + back * 0.16 + v3((0.04, -0.06, 0.02))]
    for x, y in ((-0.4, -0.56), (-0.12, -0.66), (0.22, -0.6), (0.46, -0.38)):
        pts.append(v3((x, y, 0.021)))
    gd = norm(v3((CON_P[0] - COIL_C[0], CON_P[1] - COIL_C[1], 0.0)) + v3((0.0, -1.2, 0.0)))
    end = COIL_C + gd * (PL_R + 0.05) + Z * 0.07
    pts += [end + gd * 0.1 + Z * -0.045, end]
    return pts


def console_field():
    fd = Field("Console")
    c = CON_P
    # the cast-iron pedestal: a flared foot, a column with rings, a cradle under the slab
    fd.add(Cylinder(c + Z * 0.026, 0.165, 0.052, rr=0.016), 0.0, IRON)
    fd.add(RoundCone(c + Z * 0.05, c + Z * 0.17, 0.12, 0.05), 0.03, IRON)
    fd.add(RoundCone(c + Z * 0.17, c + Z * 0.8, 0.046, 0.038, disp=lambda P: F(0.003) * np.abs(np.sin(np.arctan2(P[:, 1] - F(c[1]), P[:, 0] - F(c[0])) * F(4))), disp_amp=0.003), 0.012, IRON)
    for zz in (0.19, 0.5, 0.78):
        fd.add(Torus(c + Z * zz, 0.05, 0.012), 0.004, IRON)
    fd.add(Ellipsoid(SLAB_C - SN * 0.075, (0.1, 0.15, 0.05), R=R_SLAB), 0.03, IRON)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        fd.add(Sphere(c + v3((math.cos(a), math.sin(a), 0)) * 0.142 + Z * 0.053, 0.009), 0.002, IRON)
    # the slab in its iron tray
    fd.add(RoundBox(SLAB_C - SN * 0.008, (SLAB_HALF[0] + 0.014, SLAB_HALF[1] + 0.014, 0.019), 0.008, R=R_SLAB), 0.004, IRON)
    fd.add(RoundBox(SLAB_C, SLAB_HALF, 0.006, R=R_SLAB, disp=lambda P: F(0.0006) * NOISE(P * F(40)), disp_amp=0.001), 0.003, SLATE)
    for sw_ in (-1, 1):
        for ss in (-1, 1):
            fd.add(Sphere(slab_pt(sw_ * (SLAB_HALF[0] + 0.007), ss * (SLAB_HALF[1] + 0.007), -0.012), 0.008), 0.002, IRON)
    # the knife-switch's fixed parts: hinge blocks and jaws (copper on porcelain), binding posts (brass)
    for sx in (-1, 1):
        w = sx * BLADE_W
        fd.add(RoundBox(slab_pt(w, HINGE_S, 0.008), (0.026, 0.034, 0.009), 0.004, R=R_SLAB), 0.003, PORC)
        for e in (-1, 1):
            fd.add(RoundBox(slab_pt(w + e * 0.0105, HINGE_S, 0.034), (0.0045, 0.018, 0.024), 0.003, R=R_SLAB), 0.002, COPPER)
        fd.add(RoundBox(slab_pt(w, JAW_S, 0.008), (0.026, 0.034, 0.009), 0.004, R=R_SLAB), 0.003, PORC)
        for e in (-1, 1):
            fd.add(RoundBox(slab_pt(w + e * 0.0095, JAW_S, 0.036), (0.0035, 0.02, 0.026), 0.002, R=R_SLAB), 0.002, COPPER)
        for bw, bs in ((w, HINGE_S - 0.058), (sx * (BLADE_W + 0.052), JAW_S)):
            bp = slab_pt(bw, bs, 0.0)
            fd.add(Cylinder(bp + SN * 0.01, 0.012, 0.02, rr=0.003, R=R_SLAB), 0.002, BRASS)
            fd.add(Cylinder(bp + SN * 0.026, 0.009, 0.014, rr=0.003, R=R_SLAB, disp=lambda P: F(0.0008) * np.sin(P[:, 0] * F(900) + P[:, 1] * F(900)), disp_amp=0.001), 0.002, BRASS)
        fd.add(RoundBox(slab_pt(w, HINGE_S - 0.03, 0.006), (0.008, 0.03, 0.004), 0.002, R=R_SLAB), 0.002, COPPER)
        fd.add(RoundBox(slab_pt(sx * (BLADE_W + 0.027), JAW_S, 0.006), (0.027, 0.008, 0.004), 0.002, R=R_SLAB), 0.002, COPPER)
    fd.add(Cylinder(HINGE, 0.006, 2 * BLADE_W + 0.04, rr=0.002, R=rot_from_axes(z_axis=SW)), 0.002, BRASS)        # the hinge pin
    # the gauge board on the slab's back edge: slate, two gauges, iron brackets
    Rb = np.stack([BOARD_X, BOARD_UP, BOARD_N], axis=1)
    fd.add(RoundBox(BOARD_C, (0.165, 0.1, 0.012), 0.006, R=Rb), 0.0, SLATE)
    for sx in (-1, 1):
        fd.add(RoundBox(BOARD_C + BOARD_X * (sx * 0.12) - BOARD_N * 0.022 - BOARD_UP * 0.06, (0.008, 0.055, 0.012), 0.004, R=Rb), 0.004, IRON)
    gu = BOARD_UP
    gs = BOARD_X
    for k, gcen in enumerate(gauge_centres()):
        fd.add(Cylinder(gcen + BOARD_N * 0.008, 0.058, 0.024, rr=0.008, R=Rb), 0.004, BRASS)
        fd.add(Torus(gcen + BOARD_N * 0.02, 0.052, 0.006, R=Rb), 0.002, BRASS)
        fd.add(Cylinder(gcen + BOARD_N * 0.018, 0.046, 0.005, rr=0.002, R=Rb), 0.002, ENAMEL)
        for j in range(7):
            a = math.radians(-60 + 20 * j)
            dd = gu * math.cos(a) + gs * math.sin(a)
            fd.add(RoundCone(gcen + BOARD_N * 0.021 + dd * 0.032, gcen + BOARD_N * 0.021 + dd * 0.04, 0.0016, 0.0016), 0.0, RUBBER)
        na = math.radians(-35 if k == 0 else 20)
        nd = gu * math.cos(na) + gs * math.sin(na)
        fd.add(RoundCone(gcen + BOARD_N * 0.022, gcen + BOARD_N * 0.022 + nd * 0.038, 0.0028, 0.0014), 0.001, RUBBER)
        fd.add(Sphere(gcen + BOARD_N * 0.022, 0.005), 0.001, BRASS)
    # the twin cable
    pts = cable_path()
    for e in (-1, 1):
        q = [p + SW * (e * 0.016) if i < 4 else p + norm(np.cross(Z, norm(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]))) * (e * 0.017)
             for i, p in enumerate(pts)]
        fd.add(Chain(q, [0.016] * len(q), k=0.01), 0.004, RUBBER)
    for i in (5, 7):                                                     # two iron cleats holding it to the floor
        d = norm(pts[i + 1] - pts[i - 1])
        side = norm(np.cross(Z, d))
        cp = pts[i] + Z * 0.004
        fd.add(Inter(Shell(Cylinder(cp, 0.05, 0.06, R=rot_from_axes(z_axis=d)), 0.0, 0.008),
                     Func(lambda P, cp=cp, d=d: np.maximum(np.abs((P - cp.astype(F)) @ d.astype(F)) - F(0.016), F(0.0) - P[:, 2]), cp - 0.1, cp + 0.1), 0.002), 0.003, IRON)
        for e in (-1, 1):
            fd.add(Sphere(cp + side * (e * 0.047) + Z * -0.016, 0.009), 0.002, IRON)
    return fd


def switch_field():
    """The knife-switch's moving part (closed, in the rest pose): two copper blades (0) from the hinge into the jaws, an
    ebonite crossbar (9) over their ends and the ebonite handle standing out of it (9) with a red knob (14)."""
    fd = Field("Switch")
    R = R_SLAB
    for sx in (-1, 1):
        w = sx * BLADE_W
        a, b = HINGE + SW * w, HINGE + SW * w + SU * BLADE_L
        m = (a + b) / 2
        fd.add(RoundBox(m, (0.0045, BLADE_L / 2 + 0.008, 0.016), 0.003, R=R), 0.0, COPPER)
        fd.add(Cylinder(a, 0.014, 0.012, rr=0.003, R=rot_from_axes(z_axis=SW)), 0.003, COPPER)
    bar = slab_pt(0.0, BAR_S, BLADE_H)
    fd.add(RoundBox(bar, (BLADE_W + 0.02, 0.012, 0.016), 0.006, R=R), 0.003, RUBBER)
    fd.add(RoundCone(bar + SN * 0.01, bar + SN * (HANDLE_L - 0.022), 0.014, 0.018), 0.004, RUBBER)
    fd.add(Sphere(KNOB_REST, 0.026), 0.006, RED)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0.0, -0.253, 1.616)), 0.05, 0.7), (hp((0.0, -0.22, 1.69)), 0.03, 0.3)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.1, -0.14, 1.63)), 0.055, 0.5), (hp((sx * 0.18, 0.035, 1.664)), 0.05, 0.6),
                (hp((sx * 0.07, -0.16, 1.635)), 0.03, 0.25)]
    return pts


# ======================================================================================= build config
GLB_NAME = "tesla_coil"
ROOT_NAME = "TeslaCoilHQ"
TEX_PREFIX = "tesla"
MAT_NAME = "TeslaMat"
MESH_NAME = "Tesla"
BASE_MODULE = "tesla_base"
ANIM_MODULE = "anim_tesla"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Tufts", "Moustache", "Goggles", "Coat", "Waistcoat", "Shirt", "Trousers", "Boots",
         "Gloves", "Brass", "Coil", "Charge", "Console", "Switch"]
REGION_PARTS = ("Skin", "Goggles", "Coat", "Shirt", "Gloves", "Brass", "Coil", "Console", "Switch")
NAVY = (0.2, 0.25, 0.42)                 # (the corps' navy: about (0.05, 0.07, 0.17) in linear albedo)
WHITE_HAIR = {"name": "HQ_TeslaHair", "base": (0.86, 0.86, 0.84), "hi": (0.99, 0.99, 0.97), "low": (0.58, 0.58, 0.6),
              "streak": (0.72, 0.72, 0.72), "tint": (0.92, 0.9, 0.86)}
APPARATUS = ("electric", {"name": "HQ_TeslaApparatus"})
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_TeslaSkin", "base": (0.87, 0.67, 0.56), "ruddy": (0.88, 0.5, 0.42), "lips": (0.7, 0.4, 0.38),
                      "brow": ((0.8, 0.8, 0.78), (0.97, 0.97, 0.95)),
                      "extra": ((LASH, (0.4, 0.36, 0.34), 0.5), (STUBBLE, (0.74, 0.68, 0.64), 0.55, 0.4))}),
    "Hair": ("hair", WHITE_HAIR),
    "Tufts": ("hair", WHITE_HAIR),
    "Moustache": ("hair", dict(WHITE_HAIR, name="HQ_TeslaMoustache")),
    "Goggles": APPARATUS,
    "Coat": ("linen", {"name": "HQ_LabCoat", "base": (0.92, 0.92, 0.88), "stripe": (0.36, 0.32, 0.29)}),
    "Waistcoat": ("wool", {"name": "HQ_TeslaWaistcoat", "base": NAVY, "border": NAVY, "stripe": NAVY}),
    "Shirt": ("linen", {"name": "HQ_TeslaShirt", "base": (0.95, 0.94, 0.9), "stripe": (0.52, 0.07, 0.07)}),
    "Trousers": ("wool", {"name": "HQ_TeslaTrousers", "base": (0.2, 0.2, 0.23), "border": (0.2, 0.2, 0.23), "stripe": (0.2, 0.2, 0.23)}),
    "Boots": ("leather_dyed", {"name": "HQ_TeslaBoots", "base": (0.32, 0.18, 0.09), "dyed": (0.32, 0.18, 0.09)}),
    "Gloves": APPARATUS,
    "Brass": APPARATUS,
    "Coil": APPARATUS,
    "Charge": ("glow_ball", {"name": "HQ_Charge", "col": (0.45, 0.92, 1.0), "strength": 1.0}),
    "Console": APPARATUS,
    "Switch": APPARATUS,
}
GLOW = {"Charge": ((0.45, 0.92, 1.0), 1.0, 0.5)}
LOW_TARGETS = {"Skin": 6000, "Teeth": 80, "Hair": 900, "Tufts": 2200, "Moustache": 700, "Goggles": 700, "Coat": 5200,
               "Waistcoat": 900, "Shirt": 700, "Trousers": 1300, "Boots": 900, "Gloves": 1400, "Brass": 500, "Coil": 4200,
               "Charge": 300, "Console": 3600, "Switch": 500}
AO_EXCLUDE = ["Brass", "Switch"]
# the apparatus is baked 6 m away from him: his rest pose (his arms out) must leave no shadow on it
BAKE_APART = (["Coil", "Console", "Switch"], (6.0, 0.0, 0.0))
YAW_PIVOT = (0.05, -0.04, 0.0)            # the tower turns about this point (keeps the coil, the console and him on the base)


def prop_bones():
    return []


def extra_bones():
    """machine (the coil and the console, deforming nothing of him), toroid (its centre: the game's lightning leaves
    from it; bone_point ALONG 0), switch (the blades and the handle, hinged at the hinge pin; its tail toward the jaws),
    hair (his wild tufts, on the head: scaled up as they bristle)."""
    return [("machine", COIL_C + Z * 0.05, COIL_C + Z * 0.4, None),
            ("toroid", TOR_C, TOR_C + Z * 0.2, "machine"),
            ("switch", HINGE, HINGE + SU * 0.3, "machine"),
            ("hair", HEAD_C, HEAD_C + Z * 0.2, "head")]


def weight_rules():
    arms = {"clavicle.R", "clavicle.L", "upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Tufts": ("rigid", "hair"),
        "Moustache": ("rigid", "head"), "Goggles": ("rigid", "head"),
        "Coat": ("transfer", TORSO | arms | {"thigh.R", "thigh.L"}, {"thigh.R": 0.45, "thigh.L": 0.45}),
        "Waistcoat": ("transfer", TORSO | {"thigh.R", "thigh.L"}, {"thigh.R": 0.3, "thigh.L": 0.3}),
        "Shirt": ("transfer", TORSO, None),
        "Trousers": ("transfer", {"root", "spine", "thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gloves": ("transfer", {"forearm.R", "forearm.L", "hand.R", "hand.L"}, None),
        "Brass": ("transfer", TORSO, None),
        "Coil": ("rigid", "machine"), "Charge": ("rigid", "toroid"), "Console": ("rigid", "machine"),
        "Switch": ("rigid", "switch"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth", "Moustache", "Goggles") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Coil", "Console"):
        return 0.8
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Tufts", tufts_field(), 0.0022 if fine else 0.0032),
        ("Moustache", moustache_field(), 0.0018 if fine else 0.0026),
        ("Goggles", goggles_field(), 0.0014 if fine else 0.002),
        ("Coat", coat_field(), 0.0026 if fine else 0.0036),
        ("Waistcoat", waistcoat_field(), 0.0024 if fine else 0.0034),
        ("Shirt", shirt_field(), 0.0018 if fine else 0.0026),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Boots", boots_field(), 0.0022 if fine else 0.003),
        ("Gloves", gloves_field(), 0.0022 if fine else 0.003),
        ("Brass", brass_field(), 0.0014 if fine else 0.002),
        ("Coil", coil_field(), 0.0026 if fine else 0.0036),
        ("Charge", charge_field(), 0.002 if fine else 0.003),
        ("Console", console_field(), 0.0022 if fine else 0.0032),
        ("Switch", switch_field(), 0.0016 if fine else 0.0024),
    ]
