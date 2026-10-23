"""The Sniper (HQ tower, Modern Age). Rest pose = A-pose, facing -Y, feet at z = 0; right side = -X.

A calm, sharp-eyed marksman of the task force in his thirties, built on the Musketeer's long, rangy skeleton: a lean,
weathered face (high cheekbones over hollow cheeks, a long straight nose, a firm thin mouth, a few days' dark stubble),
level dark brows low over steady grey-green eyes. An olive boonie hat, its front brim pushed up, strips of jute scrim
tucked in its band; a comms headset under it (olive cups over his ears, a boom mic at his mouth). A ghillie capelet of
jute strips over his shoulders (moss, olive, tan and brown, hanging in ragged strands). An olive combat shirt, sleeves
rolled to below the elbow, a red-and-white unit patch on the left sleeve; a coyote plate carrier (MOLLE rows, two
magazine pouches and an admin pouch with the unit patch on the front, a radio on the left side with its whip antenna
standing up behind his shoulder) over a coyote battle belt; olive trousers with cargo pockets, black knee pads, black
boots; black gloves.

The rifle: a big bolt-action anti-materiel rifle (1.57 m): a black polymer stock with a cheek riser and a rubber butt
pad, a pistol grip, a gunmetal receiver with a rail, a box magazine, a long slotted handguard, a heavy fluted barrel and
a big double-port muzzle brake; a big scope (flip caps open, the objective lens glowing faintly: its own emissive mesh,
"Lens"), a bipod. The bolt (its shroud, body and handle with a big knob) and the bipod are bones of their own.

His body is the Musketeer's (musketeer.py: skeleton, feet, limbs) with his own head, hands (a cupped left hand) and
kit. The rifle, the bolt and the bipod are props on bones with no parent, posed directly in every frame ("world" aims in
anim_sniper.py)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, Noise, F)
from caveman import Inter, Shell, ray_hit, Lock, lerp
from musketeer import (J, hp, hr, hinv, HS, HEAD_C, HEAD_RAD, EYE_R, eye_c, smoothstep, hand_frame, HAND_S,
                       foot, torso_prims, traps, neck_prim, deltoid, upper_arm_prims, forearm_prims, leg_prims,
                       shin_prims, _arm_seg_dist, layer, _fgrad, torso_bones, TORSO_Z, TORSO)

SKIN, NAIL, LIP, MOUTH, BROW, LASH, STUBBLE = 0, 1, 2, 3, 4, 8, 9
IRIS = ((0.22, 0.27, 0.22), (0.5, 0.58, 0.48))          # steady grey-green eyes (prep.paint_eyes)


# ======================================================================================= hands
CURLS = {"R": (1.45, 1.6, 1.2), "L": (0.95, 1.05, 0.8)}   # right: a fist round the pistol grip; left: cupped under the butt


def fist_center(side):
    wr, f, n, t = hand_frame(side)
    return wr + f * 0.106 * HAND_S + n * 0.034


def hand(fd, side, s=HAND_S):
    """The Musketeer's hand (long bony fingers), the right curled in a fist, the left cupped."""
    wr, f, n, t = hand_frame(side)
    Rp = np.stack([t, n, f], axis=1)
    c = wr + f * 0.077 * s
    fd.add(RoundBox(c, v3((0.059, 0.03, 0.066)) * s, 0.027 * s, R=Rp), 0.027, SKIN)
    fd.add(Ellipsoid(c - n * 0.011 + t * 0.03 * s - f * 0.01, v3((0.032, 0.027, 0.05)) * s, R=Rp), 0.018, SKIN)
    curl_ax = norm(np.cross(f, n))
    curls = CURLS[side]
    offs = (0.042, 0.014, -0.014, -0.042)
    lens = (0.98, 1.05, 0.98, 0.82)
    for i, (o, ls) in enumerate(zip(offs, lens)):
        p = wr + f * 0.138 * s + t * o * s - n * 0.004
        d = norm(f - t * o * 1.2)
        pts, rads = [p], [0.0195 * s * (0.92 if i == 3 else 1.0)]
        seglen = (0.053 * ls * s, 0.043 * ls * s, 0.035 * ls * s)
        for j in range(3):
            d = axis_angle(curl_ax, curls[j] * (0.9 if i == 3 else 1.0)) @ d
            p = p + d * seglen[j]
            pts.append(p)
            rads.append(rads[-1] * 0.9)
        fd.add(Chain(pts, rads, k=0.006), 0.011, SKIN)
        fd.add(Sphere(pts[0] - n * 0.011, 0.0145 * s), 0.009, SKIN)                 # knuckles
    tb = wr + f * 0.045 * s + t * 0.05 * s + n * 0.011
    d1 = norm(f * 0.55 + t * 0.55 + n * 0.6)
    d2 = norm(f * 0.25 - t * 0.85 + n * 0.45)
    p1 = tb + d1 * 0.05 * s
    p2 = p1 + d2 * 0.043 * s
    fd.add(Chain([tb, p1, p2], [0.024 * s, 0.021 * s, 0.018 * s], k=0.008), 0.018, SKIN)


GLOVE_BACK = 0.045                         # the gloves' cuffs: this far up the forearm from the wrist joint


def _glove_along(P, side):
    """Distance past the glove's cuff line along the forearm (> 0 inside the glove), limited to that hand."""
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    along = (P - (wr - ax * GLOVE_BACK).astype(F)) @ ax.astype(F)
    near = np.sqrt(((P - wr.astype(F)) ** 2).sum(1)) < F(0.3)
    return np.where(near, along, F(-1.0))


# ======================================================================================= head
def stubble_mask(P):
    """Cheeks, jaw, chin and upper lip (design coordinates): a few days' growth."""
    Q = hinv(P)
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    ax = np.abs(x)
    top = F(1.61) + F(0.025) * smoothstep(0.06, 0.15, ax)
    return np.maximum(np.maximum(z - top, F(1.43) - z), y - F(0.04))


def head(fd):
    """A lean, weathered face: a long jaw and a firm chin, high cheekbones over hollow cheeks, a long straight nose,
    level brows set low over calm, hooded eyes (crow's feet from squinting through glass), a firm thin mouth."""
    E = lambda c, r, R=None: Ellipsoid(hp(c), v3(r) * HS, R=R)
    S = lambda c, r: Sphere(hp(c), hr(r))
    fd.add(Ellipsoid(HEAD_C, HEAD_RAD), 0.06, SKIN)
    fd.add(E((0, -0.05, 1.59), (0.121, 0.124, 0.122)), 0.07, SKIN)                           # a lean jaw
    fd.add(E((0, -0.134, 1.5), (0.072, 0.064, 0.066)), 0.05, SKIN)                           # a firm chin
    fd.sub(RoundCone(hp((0, -0.2, 1.486)), hp((0, -0.197, 1.508)), hr(0.0035), hr(0.0025)), hr(0.005))   # its cleft
    for sx in (-1, 1):
        fd.add(S((sx * 0.108, -0.116, 1.64), 0.042), 0.05, SKIN)                               # high cheekbones
        fd.add(S((sx * 0.113, -0.046, 1.562), 0.043), 0.05, SKIN)                              # jaw corners
        pts = [hp((sx * 0.15, -0.055, 1.744)), hp((sx * 0.114, -0.13, 1.752)), hp((sx * 0.06, -0.174, 1.75)), hp((0.0, -0.184, 1.75))]
        fd.add(Chain(pts, [hr(0.012), hr(0.022), hr(0.027), hr(0.027)], k=hr(0.022)), hr(0.035), SKIN)     # brow ridge
        fd.sub(Ellipsoid(hp((sx * 0.117, -0.118, 1.574)), v3((0.022, 0.016, 0.026)) * HS, R=euler(0, 0, sx * -0.5)), hr(0.02))
    fd.paint(Func(stubble_mask, HEAD_C - 0.4, HEAD_C + 0.2), STUBBLE)
    # level brows, low and straight (a calm, steady look), a faint furrow between them
    for sx in (-1, 1):
        pts = [hp((sx * 0.022, -0.213, 1.748)), hp((sx * 0.064, -0.209, 1.762)), hp((sx * 0.108, -0.188, 1.768)), hp((sx * 0.15, -0.146, 1.762))]
        fd.add(Chain([p + v3((0, 0.006, 0)) for p in pts], [hr(0.011), hr(0.013), hr(0.011), hr(0.005)], k=hr(0.008)), hr(0.01), BROW)
        fd.paint(Chain(pts, [hr(0.018), hr(0.02), hr(0.018), hr(0.01)], k=hr(0.01)), BROW)
        fd.sub(RoundCone(hp((sx * 0.01, -0.212, 1.738)), hp((sx * 0.011, -0.208, 1.764)), hr(0.0018), hr(0.0013)), hr(0.0025))
    for sx in (-1, 1):
        ec = eye_c(sx)
        fd.sub(Sphere(ec, EYE_R + hr(0.006)), hr(0.012))
        up = Inter(Sphere(ec, EYE_R + hr(0.0068)), Plane(ec + v3((0, 0, hr(0.0142))), (sx * 0.18, 0.06, -1.0)), hr(0.004))
        fd.add(up, hr(0.005), SKIN)
        lo = Inter(Sphere(ec, EYE_R + hr(0.0056)), Plane(ec + v3((0, 0, -hr(0.0185))), (sx * -0.12, 0.06, 1.0)), hr(0.004))
        fd.add(lo, hr(0.005), SKIN)
        fd.paint(Inter(Shell(Sphere(ec, EYE_R + hr(0.009)), 0.0, hr(0.007)), Plane(ec + v3((0, 0, hr(0.0132))), (sx * 0.18, 0.06, -1.0)), hr(0.002)), LASH)
        for k in range(3):                                                                      # crow's feet
            a = hp((sx * (0.108 + 0.004 * k), -0.134 + 0.006 * k, 1.688 - 0.011 * k))
            fd.sub(RoundCone(a, a + v3((sx * 0.025, 0.012, 0.006 - 0.01 * k)), hr(0.002), hr(0.0013)), hr(0.003))
    # a long straight nose
    fd.add(RoundCone(hp((0, -0.186, 1.73)), hp((0, -0.249, 1.624)), hr(0.0145), hr(0.02)), hr(0.016), SKIN)
    fd.add(S((0, -0.25, 1.609), 0.023), hr(0.014), SKIN)
    for sx in (-1, 1):
        fd.add(S((sx * 0.026, -0.221, 1.6), 0.018), hr(0.012), SKIN)
        fd.sub(Ellipsoid(hp((sx * 0.014, -0.237, 1.59)), v3((0.008, 0.01, 0.006)) * HS, R=euler(0.5, 0, sx * 0.3)), hr(0.004))
    # mouth: a firm, thin line; a thin lower lip
    slot = [hp((-0.05, -0.174, 1.552)), hp((-0.026, -0.195, 1.548)), hp((0, -0.201, 1.547)), hp((0.026, -0.195, 1.548)), hp((0.05, -0.174, 1.552))]
    fd.sub(Chain(slot, [hr(0.0024), hr(0.003), hr(0.0034), hr(0.003), hr(0.0024)], k=hr(0.003)), hr(0.003))
    fd.paint(Chain(slot, [hr(0.003), hr(0.0042), hr(0.0046), hr(0.0042), hr(0.003)], k=hr(0.004)), MOUTH)
    up_lip = [(-0.044, -0.176, 1.556), (-0.02, -0.196, 1.553), (0, -0.2, 1.552), (0.02, -0.196, 1.553), (0.044, -0.176, 1.556)]
    fd.add(Chain([hp(p) for p in up_lip], [hr(0.003), hr(0.0045), hr(0.005), hr(0.0045), hr(0.003)], k=hr(0.004)), hr(0.006), LIP)
    lo_lip = [(-0.04, -0.174, 1.541), (-0.021, -0.19, 1.534), (0, -0.194, 1.532), (0.021, -0.19, 1.534), (0.04, -0.174, 1.541)]
    fd.add(Chain([hp(p) for p in lo_lip], [hr(0.0045), hr(0.0068), hr(0.0074), hr(0.0068), hr(0.0045)], k=hr(0.006)), hr(0.007), LIP)
    # ears (under the headset's cups)
    for sx in (-1, 1):
        R = euler(0, sx * 0.25, sx * -0.35)
        c = hp((sx * 0.157, 0.035, 1.66))
        fd.add(Ellipsoid(c, v3((0.02, 0.04, 0.052)) * HS, R=R), hr(0.02), SKIN)


# ======================================================================================= body
def body_parts(fd):
    for p, k in torso_prims():
        fd.add(p, k, SKIN)
    fd.add(traps(), 0.06, SKIN)
    fd.add(neck_prim(), 0.05, SKIN)
    for side in ("R", "L"):
        fd.add(deltoid(side), 0.055, SKIN)
        for p, k in upper_arm_prims(side) + forearm_prims(side):
            fd.add(p, k, SKIN)
        hand(fd, side)
        for p, k in leg_prims(side) + shin_prims(side):
            fd.add(p, k, SKIN)
        foot(fd, side)
    head(fd)


def _under_hat(P):
    """< 0 where the head may be: below the hat's band, or well inside its crown (nothing shows through the cloth)."""
    q = hat_local(P)
    return np.minimum(q[:, 2] + F(0.004), crown_sd(q) + F(HAT_T + 0.004))


def skin_field():
    """The body; the hands end inside the gloves' cuffs (cut away past them)."""
    fd = Field("Skin")
    body_parts(fd)
    fd.inter(Func(_under_hat, HAT_O - 0.5, HAT_O + 0.5), 0.003)
    for side in ("R", "L"):
        wr = J["wrist_" + side]
        fd.inter(Func(lambda P, side=side: _glove_along(P, side) - F(0.016), wr - 0.35, wr + 0.35), 0.002)
    return fd


def eyes_field():
    fd = Field("Eyes")
    for sx in (-1, 1):
        fd.add(Sphere(eye_c(sx), EYE_R))
    return fd


def teeth_field():
    fd = Field("Teeth")
    for sx in (-1, 1):
        fd.add(RoundBox(hp((sx * 0.009 + 0.003, -0.178, 1.551)), v3((0.008, 0.006, 0.006)) * HS, hr(0.003)), 0.0)
    return fd


# ======================================================================================= the boonie hat
HAT_O = v3((0.0, 0.024, 1.826))            # the crown's foot, on its axis (world)
HAT_R = euler(0.03, 0.0, 0.0)              # tipped a hair forward
HAT_CH = 0.1                               # the crown's height
HAT_R0 = (0.196, 0.218)                    # its radii at the band (x, y) and at the top
HAT_R1 = (0.188, 0.206)
HAT_T = 0.008
BAND_H = 0.032
BRIM_TH = 0.0075


def hat_local(P):
    return ((P - HAT_O.astype(F)) @ HAT_R.astype(F)).astype(F)


def hat_world(q):
    return HAT_O + HAT_R @ v3(q)


def crown_sd(q):
    """Signed distance to the crown (hat-local): a soft oval, a little narrower at its rounded top."""
    z = q[:, 2]
    t = np.clip(z / F(HAT_CH), 0, 1)
    rx = F(HAT_R0[0]) + F(HAT_R1[0] - HAT_R0[0]) * t
    ry = F(HAT_R0[1]) + F(HAT_R1[1] - HAT_R0[1]) * t
    e = (np.sqrt((q[:, 0] / rx) ** 2 + (q[:, 1] / ry) ** 2) - F(1.0)) * np.minimum(rx, ry)
    top = F(HAT_CH) - F(0.008) * np.exp(-((q[:, 0] / F(0.09)) ** 2 + ((q[:, 1] - F(0.01)) / F(0.12)) ** 2))   # a soft dent on top
    dz = np.maximum(z - top, F(-0.03) - z)
    rr = F(0.062)
    a = e + rr
    b = dz + rr
    return np.sqrt(np.maximum(a, 0) ** 2 + np.maximum(b, 0) ** 2) + np.minimum(np.maximum(a, b), 0) - rr


def _band_r(a):
    return 1.0 / np.sqrt((np.sin(a) / F(HAT_R0[0])) ** 2 + (np.cos(a) / F(HAT_R0[1])) ** 2)


def _brim_front(a):
    return smoothstep(1.05, 0.45, np.abs(a))


def brim_width(a):
    return F(0.088) - F(0.026) * _brim_front(a) - F(0.004) * np.cos(a)       # (narrow at the front, widest behind)


def brim_z(t, a):
    """The brim's middle height (hat-local) at t out from the band, angle a from the front: pushed up in front, drooping
    at the sides and behind, a soft wave round its edge."""
    fr = _brim_front(a)
    wave = F(0.008) * np.sin(a * F(3.0) + F(0.6)) + F(0.004) * np.sin(a * F(5.0) + F(2.1))
    W = brim_width(a)
    return (F(0.003) + fr * (F(0.42) * t) + (F(1) - fr) * (F(-0.28) * t - F(2.6) * t * t)
            + wave * (t / W) ** 2 * (F(1) - fr))


def brim_sd(q):
    a = np.arctan2(q[:, 0], -q[:, 1])
    rho = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - (_band_r(a) - F(0.004))
    W = brim_width(a)
    t = np.clip(rho, 0, W)
    zc = brim_z(t, a)
    eps = F(0.002)
    slope = (brim_z(np.clip(t + eps, 0, None), a) - brim_z(np.clip(t - eps, 0, None), a)) / (F(2) * eps)
    dv = np.abs(q[:, 2] - zc) / np.sqrt(F(1) + slope * slope) - F(BRIM_TH / 2)
    de = rho - W
    rr = F(0.003)
    d = np.sqrt(np.maximum(dv + rr, 0) ** 2 + np.maximum(de + rr, 0) ** 2) + np.minimum(np.maximum(dv + rr, de + rr), 0) - rr
    return np.maximum(d, F(-0.012) - rho)


def hat_field():
    """Olive ripstop (label 0): the crown (a soft shell with a dent on top), the brim (stitched in rings, pushed up in
    front); the band (5) with foliage loops."""
    fd = Field("Hat")
    cloth = lambda P: F(0.0009) * NOISE(P * F(40)) + F(0.0006) * NOISE(P * F(110))
    lo, hi = HAT_O - v3((0.4, 0.4, 0.15)), HAT_O + v3((0.4, 0.4, 0.3))
    fd.add(Func(lambda P: np.abs(crown_sd(hat_local(P)) + F(HAT_T / 2)) - F(HAT_T / 2), lo, hi, disp=cloth, disp_amp=0.001), 0.0)
    fd.inter(Func(lambda P: F(-0.003) - hat_local(P)[:, 2], lo, hi), 0.0)
    def stitches(P):
        q = hat_local(P)
        a = np.arctan2(q[:, 0], -q[:, 1])
        rho = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - _band_r(a)
        return F(-0.0008) * smoothstep(0.75, 0.95, np.abs(np.sin(rho * F(math.pi / 0.011)))) * smoothstep(0.004, 0.012, rho)
    blo, bhi = HAT_O - v3((0.36, 0.36, 0.16)), HAT_O + v3((0.36, 0.36, 0.08))
    fd.add(Func(lambda P: brim_sd(hat_local(P)), blo, bhi, disp=lambda P: stitches(P) + cloth(P), disp_amp=0.0015), 0.004)
    # the band and its foliage loops
    def band(P):
        q = hat_local(P)
        return np.maximum(np.abs(crown_sd(q) - F(0.001)) - F(0.0045), np.abs(q[:, 2] - F(BAND_H / 2 + 0.002)) - F(BAND_H / 2))
    fd.add(Func(band, lo, hi), 0.002, 5)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        qs, n = hat_surface_point(a, BAND_H / 2 + 0.002, 0.0055)
        c = hat_world(qs)
        nw = norm(HAT_R @ n)
        upw = HAT_R @ v3((0, 0, 1))
        fd.add(RoundBox(c, (0.008, 0.003, BAND_H / 2 + 0.005), 0.002, R=rot_from_axes(z_axis=upw, y_axis=nw)), 0.002, 5)
    return fd


def hat_surface_point(a, z, out=0.0):
    """A point on the crown's outer surface (hat-local) at angle a from the front, height z; its outward normal."""
    q = np.array([[math.sin(a) * 0.3, -math.cos(a) * 0.3, z]], F)
    for _ in range(10):
        d = crown_sd(q)
        g = np.zeros_like(q)
        for k in range(2):
            e = np.zeros(3, F)
            e[k] = 0.001
            g[:, k] = (crown_sd(q + e) - crown_sd(q - e)) / F(0.002)
        g = g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), F(1e-9))
        q = q - g * d[:, None]
    n = norm(v3(g[0]))
    return v3(q[0]) + n * (out + HAT_T * 0.0), n


SCRIM_A = (-2.75, -2.25, -1.75, -1.3, -0.82, 0.86, 1.32, 1.8, 2.3, 2.85)


def scrim_paths():
    """The jute strips tucked in the band: out over the brim and hanging past its edge (world points, normals)."""
    out = []
    rs = np.random.RandomState(41)
    for k, a in enumerate(SCRIM_A):
        a = a + rs.uniform(-0.12, 0.12)
        br = float(_band_r(np.float32(a)))
        W = float(brim_width(np.float32(a)))
        dirv = v3((math.sin(a), -math.cos(a), 0.0))
        L = rs.uniform(0.014, 0.03)
        pts, ns = [], []
        for t in (-0.004, 0.02, 0.045, W + 0.004):
            z = float(brim_z(np.float32(max(t, 0.0)), np.float32(a))) + BRIM_TH / 2 + 0.004 + (0.012 if t < 0 else 0.0)
            pts.append(dirv * (br + t + (0.006 if t < 0 else 0.0)) + v3((0, 0, z)))
            ns.append(v3((0, 0, 1)) if t >= 0 else dirv)
        last = pts[-1]
        for j, dz in enumerate((L * 0.5, L)):
            pts.append(last + dirv * (0.008 + 0.006 * j) + v3((0, 0, -dz)))
            ns.append(dirv)
        out.append(([hat_world(p) for p in pts], [norm(HAT_R @ n) for n in ns], k))
    return out


def scrim_field():
    """Jute scrim (the ghillie material: label 0 moss and olive, 5 tan, 6 brown) in strips from the hat's band."""
    fd = Field("Scrim")
    fib = lambda P: F(0.0012) * NOISE(P * np.array([160, 160, 40], F))
    for pts, ns, k in scrim_paths():
        n = len(pts)
        ws = [0.009, 0.011, 0.011, 0.0105, 0.009, 0.006][:n]
        ts = [0.0028] * n
        fd.add(Lock(pts, ws, ts, ns, k=0.003, disp=fib, disp_amp=0.0015), 0.002, (0, 5, 6)[k % 3])
    return fd


# ======================================================================================= hair
def hair_field():
    """Short dark hair under the hat: cropped close at the back and over the ears, short sideburns."""
    fd = Field("Hair")
    hull = Field("HairHull")
    hull.add(Ellipsoid(HEAD_C, HEAD_RAD + v3((0.004, 0.006, 0.006))), 0.0)
    strands = lambda P: (F(0.0006) * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(0.03)) * F(140) + P[:, 2] * F(40))
                         + F(0.001) * NOISE(P * np.array([110, 110, 40], F)) + F(0.0008) * NOISE(P * F(30)))
    def keep(P):
        Q = hinv(P)
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        ax = np.abs(x)
        back = smoothstep(0.03, 0.1, y)
        burn = smoothstep(0.0, -0.03, y) * smoothstep(0.1, 0.13, ax)
        bottom = F(1.716) + F(1.59 - 1.716) * back + F(1.63 - 1.716) * burn
        bottom = bottom + F(0.005) * np.sin(x * F(60))
        front = np.where(ax > F(0.125), F(-0.075) - y, F(-0.02) - y)
        return np.maximum(bottom - z, front)
    fd.add(Inter(Shell(hull, 0.002, 0.01, pad=0.06, disp=strands, disp_amp=0.002),
                 Func(keep, HEAD_C - v3((0.4, 0.4, 0.5)), HEAD_C + 0.35), 0.003), 0.0)
    fd.inter(Func(_under_hat, HAT_O - 0.5, HAT_O + 0.5), 0.002)
    return fd


# ======================================================================================= the headset
def _ear(sx):
    R = euler(0, sx * 0.25, sx * -0.35)
    c = hp((sx * 0.157, 0.035, 1.66))
    out = norm(R @ v3((sx, 0, 0)))
    return c, out, R


def cup_center(sx):
    c, out, R = _ear(sx)
    return c + out * hr(0.034), out


def headset_field():
    """Olive-drab ear cups (label 8) with black cushions and rims (5), the band rising from them under the hat, a boom
    mic from the left cup to the corner of his mouth (5) with its foam windscreen."""
    fd = Field("Headset")
    for sx in (-1, 1):
        c, out = cup_center(sx)
        R = rot_from_axes(z_axis=out, y_axis=(0, 0, 1))
        fd.add(Cylinder(c, hr(0.05), hr(0.042), rr=0.012, R=R), 0.0, 8)
        fd.add(Cylinder(c + out * hr(0.024), hr(0.036), hr(0.012), rr=0.005, R=R), 0.004, 8)        # the outer boss
        fd.add(Torus(c - out * hr(0.018), hr(0.046), hr(0.012), R=R), 0.004, 5)                    # the cushion
        fd.add(Torus(c + out * hr(0.014), hr(0.048), hr(0.004), R=R), 0.002, 5)                    # the rim
        # the band: from the cup's top up under the hat
        top = c + v3((0, 0, hr(0.05)))
        q_in = hat_world(v3((sx * 0.17, 0.02, 0.03)))
        fd.add(Chain([top - out * 0.006, top + v3((0, 0, 0.04)) + out * 0.004, q_in], [0.008, 0.007, 0.007], k=0.004), 0.004, 5)
    # the boom mic on the left cup
    c, out = cup_center(1)
    p0 = c + out * hr(0.01) + v3((0, -hr(0.035), -hr(0.012)))
    p1 = hp((0.135, -0.17, 1.582))
    p2 = hp((0.075, -0.212, 1.556))
    fd.add(Chain([p0, p1, p2], [0.0055, 0.0045, 0.0042], k=0.003), 0.003, 5)
    fd.add(Ellipsoid(p2 + v3((-0.008, -0.004, 0.0)), (0.014, 0.012, 0.012)), 0.003, 5)
    return fd


# ======================================================================================= the shirt (olive)
SHIRT_OFF, SHIRT_T = 0.014, 0.01
SHIRT_FACE = SHIRT_OFF + SHIRT_T / 2 + 0.003
ROLL_AT = 0.07                              # the sleeves end this far down the forearm from the elbow, rolled
WAIST_Z = 0.955                             # the belt's middle

_SB = []


def shirt_base():
    if _SB:
        return _SB[0]
    b = Field("ShirtBase")
    for i, (p, k) in enumerate(torso_prims()):
        if i in (2, 3):
            continue
        b.add(p, k)
    b.add(Ellipsoid((0, -0.05, 1.3), (0.24, 0.15, 0.18)), 0.06)
    b.add(traps(), 0.06)
    for side in ("R", "L"):
        el = J["elbow_" + side]
        b.add(deltoid(side), 0.055)
        for p, k in upper_arm_prims(side) + forearm_prims(side):
            b.add(p, k)
        b.add(Sphere(el + v3((0, 0.02, 0)), 0.052), 0.03)
    _SB.append(b)
    return b


def _neck_cut(P):
    rho = np.sqrt(P[:, 0] ** 2 + ((P[:, 1] - F(0.05)) * F(0.95)) ** 2)
    return P[:, 2] - (F(1.462) + F(0.4) * smoothstep(0.112, 0.14, rho))


def _sleeve_along(P, side, at=ROLL_AT):
    """Distance past the rolled sleeve's end along the forearm (> 0 beyond it), limited to that arm."""
    sx = -1 if side == "R" else 1
    el, wr = J["elbow_" + side], J["wrist_" + side]
    ax = norm(wr - el)
    along = (P - (el + ax * at).astype(F)) @ ax.astype(F)
    on = (P[:, 0] * F(sx) > F(0.36)) & (_arm_seg_dist(P, side) < F(0.15))
    return np.where(on, along, F(-1.0))


def _sleeve_cut(P):
    return np.maximum(_sleeve_along(P, "R"), _sleeve_along(P, "L"))


def shirt_outer():
    b = shirt_base()
    return Func(lambda P: b.eval(P, margin=0.1) - F(SHIRT_OFF + SHIRT_T / 2), (-0.8, -0.6, 0.6), (0.8, 0.6, 1.65))


def collar_region(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = np.clip(-(y - F(0.03)) / F(0.12), 0, 1)
    top = F(1.515) - F(0.04) * front * np.exp(-(x / F(0.1)) ** 2)
    gap = np.where(y < F(0.0), F(0.007) - np.abs(x), F(-1.0))
    return np.maximum(np.maximum(z - top, F(1.43) - z), gap)


def patch_spot():
    """The unit patch on the left sleeve: (centre, outward normal, up along the arm) on the shirt's face."""
    sh, el = J["shoulder_L"], J["elbow_L"]
    ax = norm(el - sh)
    c0 = sh + ax * 0.2
    outv = norm(v3((1, -0.25, 0)) - ax * float(v3((1, -0.25, 0)) @ ax))
    h, ok = ray_hit(shirt_outer(), [c0 + outv * 0.3], [-outv], tmax=0.5)
    p = h[0] if ok[0] else c0 + outv * 0.09
    n = _fgrad(shirt_outer(), p)
    return p, n, -ax


def shirt_field():
    """The combat shirt: olive ripstop (label 0) with a mandarin collar, sleeves rolled to below the elbow; the unit
    patch on the left sleeve: red (5) with a white band (7); a gunmetal zip (6) at the collar."""
    fd = Field("Shirt")
    base = shirt_base()
    soft = lambda P: F(0.0016) * NOISE(P * F(14)) + F(0.0008) * NOISE(P * F(45))
    lo, hi = (-0.85, -0.6, 0.82), (0.85, 0.6, 1.65)
    def keep(P):
        return np.maximum(np.maximum(_neck_cut(P), F(0.9) - P[:, 2]), _sleeve_cut(P))
    fd.add(Inter(Shell(base, SHIRT_OFF, SHIRT_T, pad=0.12, disp=soft, disp_amp=0.004), Func(keep, lo, hi), 0.004), 0.0)
    # the rolled cuffs: a thick fold at each sleeve's end
    for side in ("R", "L"):
        el, wr = J["elbow_" + side], J["wrist_" + side]
        ax = norm(wr - el)
        c = el + ax * (ROLL_AT - 0.022)
        roll = lambda P, c=c, ax=ax: F(0.0025) * np.sin(((P - c.astype(F)) @ ax.astype(F)) * F(260)) + F(0.001) * NOISE(P * F(40))
        fd.add(Inter(Func(lambda P, c=c, ax=ax, side=side: np.maximum(np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.024),
                                                                      _arm_seg_dist(P, side) - F(0.15)), c - 0.18, c + 0.18),
                     Shell(base, SHIRT_OFF + 0.009, 0.016, pad=0.12, disp=roll, disp_amp=0.003), 0.003), 0.004)
    # the mandarin collar, its zip
    nk = Field("NeckHull")
    nk.add(neck_prim(), 0.0)
    clo, chi = (-0.2, -0.2, 1.38), (0.2, 0.25, 1.6)
    fd.add(Inter(Shell(nk, 0.024, 0.011, pad=0.06), Func(collar_region, clo, chi), 0.003), 0.004)
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 0]) - F(0.011), np.maximum(P[:, 1] + F(0.02), F(1.4) - P[:, 2])), clo, chi), 6)
    # the unit patch: a small rounded shield of red with a white band across it
    p, n, upv = patch_spot()
    side = norm(np.cross(upv, n))
    R = np.stack([side, upv, n], axis=1)
    fd.add(RoundBox(p + n * 0.002, (0.03, 0.036, 0.003), 0.003, R=R), 0.002, 5)
    def band(P, p=p, R=R):
        q = (P - p.astype(F)) @ R.astype(F)
        return np.maximum(np.abs(q[:, 1] - F(0.004)) - F(0.008), np.abs(q[:, 0]) - F(0.034))
    fd.paint(Func(band, p - 0.06, p + 0.06), 7)
    return fd


# ======================================================================================= trousers, knee pads, boots
BOOT_TOP = 0.27


def legs_field():
    legs = Field("Legs")
    tp = torso_prims()
    legs.add(tp[4][0], 0.0)
    legs.add(tp[5][0], tp[5][1])
    for side in ("R", "L"):
        for p, k in leg_prims(side):
            legs.add(p, k)
        sh = shin_prims(side)
        legs.add(sh[0][0], sh[0][1])
        legs.add(sh[1][0], sh[1][1])
    return legs


def trousers_field():
    """Olive trousers (label 0), loose at the thigh, bloused over the boots' tops; cargo pockets on the thighs."""
    fd = Field("Trousers")
    legs = legs_field()
    folds = lambda P: F(0.004) * np.sin(np.arctan2(P[:, 1] - F(0.02), P[:, 0] - np.sign(P[:, 0]) * F(0.15)) * F(7)) * smoothstep(0.72, 0.5, P[:, 2]) \
        + F(0.0014) * NOISE(P * F(25)) + F(0.003) * np.sin(P[:, 2] * F(70)) * smoothstep(0.38, 0.3, P[:, 2])
    fd.add(Inter(Shell(legs, 0.016, 0.012, pad=0.1, disp=folds, disp_amp=0.006),
                 Func(lambda P: np.maximum(F(BOOT_TOP + 0.005) - P[:, 2], P[:, 2] - F(1.02)), (-0.5, -0.4, 0.15), (0.5, 0.4, 1.1)), 0.004), 0.0)
    # bloused over the boot tops
    for side in ("R", "L"):
        kn, an = J["knee_" + side], J["ankle_" + side]
        ax = norm(kn - an)
        c = an + ax * ((BOOT_TOP + 0.03 - an[2]) / ax[2])
        sb = Field("Blouse" + side)
        for p, k in shin_prims(side):
            sb.add(p, k)
        fd.add(Inter(Shell(sb, 0.028, 0.014, pad=0.06, disp=lambda P: F(0.004) * np.sin(np.arctan2(P[:, 1], P[:, 0]) * F(9)), disp_amp=0.004),
                     Func(lambda P, c=c: np.abs(P[:, 2] - F(c[2])) - F(0.03), c - 0.2, c + 0.2), 0.006), 0.008)
    # cargo pockets on the outer thighs
    outer = Func(lambda P: legs.eval(P, margin=0.1) - F(0.026), (-0.5, -0.4, 0.3), (0.5, 0.4, 1.1))
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        hip, kn = J["hip_" + side], J["knee_" + side]
        c0 = lerp(hip, kn, 0.5)
        dirv = norm(v3((sx, -0.35, 0)))
        h, ok = ray_hit(outer, [c0 + dirv * 0.35], [-dirv], tmax=0.5)
        if not ok[0]:
            continue
        n = _fgrad(outer.fn, h[0])
        upv = norm(hip - kn)
        sd = norm(np.cross(upv, n))
        R = np.stack([sd, upv, n], axis=1)
        pc = h[0] + n * 0.008
        fd.add(RoundBox(pc, (0.058, 0.07, 0.012), 0.01, R=R, disp=lambda P: F(0.001) * NOISE(P * F(40)), disp_amp=0.001), 0.006)
        fd.add(RoundBox(pc + n * 0.006 + upv * 0.05, (0.062, 0.026, 0.008), 0.006, R=R), 0.003)          # the flap
    return fd


def knee_front(side):
    kn = J["knee_" + side]
    return kn + v3((0, -0.02, 0.0))


def pads_field():
    """Black knee pads (label 0): a hard cap over each knee, a raised ridge, its straps round the leg (5)."""
    fd = Field("Pads")
    legs = legs_field()
    for side in ("R", "L"):
        kn = J["knee_" + side]
        kf = knee_front(side)
        def region(P, kn=kn):
            dz = (P[:, 2] - F(kn[2] - 0.005)) / F(0.085)
            dx = (P[:, 0] - F(kn[0])) / F(0.07)
            e = np.sqrt(dz * dz + dx * dx) - F(1.0)
            return np.maximum(e * F(0.07), P[:, 1] - F(kn[1] - 0.03))
        lo, hi = kn - v3((0.16, 0.2, 0.16)), kn + v3((0.16, 0.1, 0.16))
        ridge = lambda P, kn=kn: F(-0.004) * np.exp(-((P[:, 2] - F(kn[2])) / F(0.012)) ** 2)
        fd.add(Inter(Shell(legs, 0.034, 0.016, pad=0.06, disp=ridge, disp_amp=0.004), Func(region, lo, hi), 0.008), 0.0)
        for zc in (kn[2] + 0.075, kn[2] - 0.075):
            fd.add(Inter(Shell(legs, 0.027, 0.007, pad=0.06),
                         Func(lambda P, zc=zc, kn=kn: np.maximum(np.abs(P[:, 2] - F(zc)) - F(0.011), np.abs(P[:, 0] - F(kn[0])) - F(0.13)), lo, hi), 0.002), 0.003, 5)
    return fd


def boot_base(side):
    b = Field("BootBase" + side)
    an = J["ankle_" + side]
    for p, k in shin_prims(side):
        b.add(p, k)
    b.add(RoundCone(an + v3((0, 0.01, -0.02)), an + v3((0, 0.02, 0.12)), 0.058, 0.06), 0.03)
    foot(b, side)
    sx = -1 if side == "R" else 1
    Rz = euler(0, 0, sx * 0.1)
    fwd = Rz @ v3((0, -1, 0))
    b.add(RoundBox(an + fwd * 0.11 + v3((0, 0, -0.075)), (0.06, 0.09, 0.03), 0.028, R=Rz), 0.04)     # a smooth toe box
    return b


def boots_field():
    """Black combat boots (label 0) to above the ankle, laced up the front, thick lugged soles and heels (5)."""
    fd = Field("Boots")
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        an = J["ankle_" + side]
        bb = boot_base(side)
        crease = lambda P: F(0.0012) * NOISE(P * F(26)) + F(0.0015) * np.sin(P[:, 2] * F(90)) * smoothstep(0.14, 0.08, P[:, 2])
        lo, hi = an - v3((0.2, 0.35, 0.2)), an + v3((0.2, 0.25, 0.3))
        fd.add(Inter(Shell(bb, 0.017, 0.014, pad=0.06, disp=crease, disp_amp=0.003), Func(lambda P: P[:, 2] - F(BOOT_TOP + 0.02), lo, hi), 0.004), 0.0)
        Rz = euler(0, 0, sx * 0.1)
        fwd = Rz @ v3((0, -1, 0))
        rgt = Rz @ v3((1, 0, 0))
        lugs = lambda P: F(0.0025) * (np.abs(np.sin(P[:, 1] * F(110))) > F(0.6)).astype(F) * smoothstep(0.012, 0.002, P[:, 2])
        fd.add(RoundBox(an + fwd * 0.08 + v3((0, 0, -0.098)), (0.072, 0.162, 0.016), 0.01, R=Rz, disp=lugs, disp_amp=0.003), 0.006, 5)
        fd.add(RoundBox(an - fwd * 0.03 + v3((0, 0, -0.088)), (0.058, 0.052, 0.028), 0.01, R=Rz), 0.006, 5)      # the heel
        for k in range(6):                                                                  # the laces up the front
            c = an + fwd * (0.06 + 0.02 * k) + v3((0, 0, 0.0 - 0.016 * k)) if k < 4 else an + fwd * 0.062 + v3((0, 0, 0.04 + 0.04 * (k - 4)))
            fd.add(RoundCone(c - rgt * 0.022, c + rgt * 0.022, 0.0045, 0.0045), 0.003)
    return fd


# ======================================================================================= gloves
def gloves_field():
    """Black gloves (label 0): the hand a little fuller, a cuff with a strap (5) round the wrist, knuckle pads (5)."""
    fd = Field("Gloves")
    for side in ("R", "L"):
        hf = Field("HandHull" + side)
        hand(hf, side)
        el, wr = J["elbow_" + side], J["wrist_" + side]
        for p, k in forearm_prims(side)[:1]:
            hf.add(p, k)
        ax = norm(wr - el)
        lo, hi = wr - 0.3, wr + 0.3
        seams = lambda P: F(0.0008) * NOISE(P * F(60))
        fd.add(Inter(Func(lambda P, hf=hf: hf.eval(P, margin=0.02) - F(0.004), lo, hi, disp=seams, disp_amp=0.001),
                     Func(lambda P, side=side: -_glove_along(P, side), lo, hi), 0.002), 0.0)
        c = wr - ax * (GLOVE_BACK - 0.016)
        fd.add(Inter(Func(lambda P, hf=hf: hf.eval(P, margin=0.03) - F(0.0085), lo, hi),
                     Func(lambda P, c=c, ax=ax: np.abs((P - c.astype(F)) @ ax.astype(F)) - F(0.014), lo, hi), 0.002), 0.003, 5)
        wr_, f, n, t = hand_frame(side)
        for i, o in enumerate((0.042, 0.014, -0.014, -0.042)):
            p = wr_ + f * 0.138 * HAND_S + t * o * HAND_S - n * 0.022
            fd.add(Ellipsoid(p, (0.013, 0.008, 0.012), R=rot_from_axes(z_axis=f, y_axis=-n)), 0.004, 5)
    return fd


# ======================================================================================= the plate carrier, belt, radio
VEST_PLATE = (0.036, 0.026)                 # (offset, thickness) of the plates from the shirt's base field
VEST_BAND = (0.031, 0.017)                  # the cummerbund
VEST_STRAP = (0.03, 0.013)                  # the shoulder straps
VEST_FACE = VEST_PLATE[0] + VEST_PLATE[1] / 2


def _plate_region(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    top_f = F(1.37) - F(0.55) * np.clip(ax - F(0.065), 0, 1)              # (the shooter's cut at the top corners)
    front = np.maximum(np.maximum(ax - F(0.155), F(1.0) - z), np.maximum(z - top_f, y + F(0.02)))
    top_b = F(1.41) - F(0.4) * np.clip(ax - F(0.08), 0, 1)
    back = np.maximum(np.maximum(ax - F(0.165), F(0.99) - z), np.maximum(z - top_b, F(0.09) - y))
    return np.maximum(np.minimum(front, back), ax - F(0.3))


def _band_region(P):
    return np.maximum(np.abs(P[:, 2] - F(1.06)) - F(0.06), np.abs(P[:, 0]) - F(0.3))


def _strap_region(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    return np.maximum(np.maximum(np.abs(np.abs(x) - F(0.118)) - F(0.03), F(1.3) - z), np.abs(y - F(0.06)) - F(0.24))


def vest_outer():
    b = shirt_base()
    return Func(lambda P: b.eval(P, margin=0.12) - F(VEST_FACE), (-0.6, -0.6, 0.85), (0.6, 0.6, 1.6))


def radio_spot():
    """(the radio's centre, outward normal) on the cummerbund's left side."""
    b = shirt_base()
    f = Func(lambda P: b.eval(P, margin=0.12) - F(VEST_BAND[0] + VEST_BAND[1] / 2), (-0.6, -0.6, 0.85), (0.6, 0.6, 1.6))
    d = norm(v3((1.0, 0.25, 0.0)))
    h, ok = ray_hit(f, [v3((0.0, 0.05, 1.07)) + d * 0.6], [-d], tmax=0.7)
    p = h[0] if ok[0] else v3((0.24, 0.1, 1.07))
    n = norm(_fgrad(f, p) * v3((1, 1, 0)))
    return p, n


def antenna_pts():
    p, n = radio_spot()
    top = p + n * 0.03 + v3((0, 0, 0.075))
    return [top, top + v3((0.01, 0.03, 0.14)), top + v3((0.03, 0.08, 0.36)), top + v3((0.05, 0.12, 0.6))]


def vest_field():
    """The plate carrier in coyote cordura (label 0): front and back plates with rows of MOLLE webbing, the cummerbund
    round his sides, shoulder straps; two magazine pouches and an admin pouch (the unit patch on it: red 6, white 7);
    black buckles and tabs (5); the radio (olive, 8) in its pouch on the left side, its whip antenna (5); the battle
    belt (0) with a black buckle (5)."""
    fd = Field("Vest")
    base = shirt_base()
    lo, hi = (-0.42, -0.5, 0.85), (0.42, 0.5, 1.6)
    molle = lambda P: F(-0.0012) * smoothstep(0.55, 0.8, np.abs(np.sin(P[:, 2] * F(math.pi / 0.026)))) + F(0.0006) * NOISE(P * F(70))
    fd.add(Inter(Func(_plate_region, lo, hi), Shell(base, VEST_PLATE[0], VEST_PLATE[1], pad=0.12, disp=molle, disp_amp=0.0015), 0.01), 0.0)
    fd.add(Inter(Func(_band_region, lo, hi), Shell(base, VEST_BAND[0], VEST_BAND[1], pad=0.12, disp=molle, disp_amp=0.0015), 0.008), 0.006)
    fd.add(Inter(Func(_strap_region, lo, hi), Shell(base, VEST_STRAP[0], VEST_STRAP[1], pad=0.12), 0.006), 0.006)
    # the drag handle on the back's top
    vo = vest_outer()
    h, ok = ray_hit(vo, [v3((0.0, 0.6, 1.38))], [v3((0, -1, 0))], tmax=0.6)
    if ok[0]:
        c = h[0]
        fd.add(Chain([c + v3((-0.03, 0.0, -0.01)), c + v3((-0.02, 0.018, 0.012)), c + v3((0.02, 0.018, 0.012)), c + v3((0.03, 0.0, -0.01))],
                     [0.006] * 4, k=0.003), 0.003, 5)
    # pouches on the front
    def pouch(x, z, half, flap=True, label=0):
        h, ok = ray_hit(vo, [v3((x, -0.6, z))], [v3((0, 1, 0))], tmax=0.7)
        if not ok[0]:
            return None
        n = norm(_fgrad(vo.fn, h[0]) * v3((1, 1, 0.3)))
        sd = norm(np.cross(v3((0, 0, 1)), n))
        R = np.stack([sd, np.cross(n, sd), n], axis=1)
        c = h[0] + n * (half[2] - 0.003)
        fd.add(RoundBox(c, half, min(0.01, half[2] * 0.7), R=R, disp=lambda P: F(0.0008) * NOISE(P * F(50)), disp_amp=0.001), 0.004, label)
        if flap:
            fd.add(RoundBox(c + n * 0.004 + R[:, 1] * (half[1] - 0.012), (half[0] + 0.003, 0.016, half[2] - 0.002), 0.006, R=R), 0.003, label)
            fd.add(RoundBox(c + n * (half[2] + 0.001) + R[:, 1] * (half[1] - 0.022), (0.009, 0.013, 0.003), 0.002, R=R), 0.002, 5)
        return c, n, R
    for x in (-0.068, 0.068):
        pouch(x, 1.11, (0.05, 0.062, 0.024))
    ap = pouch(0.0, 1.27, (0.075, 0.042, 0.012), flap=False)
    if ap is not None:
        c, n, R = ap
        pc = c + n * 0.013 + R[:, 1] * 0.006
        fd.add(RoundBox(pc, (0.032, 0.022, 0.003), 0.003, R=R), 0.002, 6)
        def band(P, pc=pc, R=R):
            q = (P - pc.astype(F)) @ R.astype(F)
            return np.maximum(np.abs(q[:, 1]) - F(0.0065), np.abs(q[:, 0]) - F(0.036))
        fd.paint(Func(band, pc - 0.06, pc + 0.06), 7)
    # the battle belt
    tr = legs_field()
    fd.add(Inter(Func(lambda P: np.abs(P[:, 2] - F(WAIST_Z)) - F(0.03), (-0.4, -0.4, WAIST_Z - 0.06), (0.4, 0.4, WAIST_Z + 0.06)),
                 Shell(tr, 0.041, 0.016, pad=0.1, disp=lambda P: F(0.0006) * NOISE(P * F(60)), disp_amp=0.001), 0.004), 0.004)
    bo = Func(lambda P: tr.eval(P, margin=0.1) - F(0.049), (-0.4, -0.4, WAIST_Z - 0.1), (0.4, 0.4, WAIST_Z + 0.1))
    h, ok = ray_hit(bo, [v3((0.0, -0.6, WAIST_Z))], [v3((0, 1, 0))], tmax=0.7)
    if ok[0]:
        n = norm(_fgrad(bo.fn, h[0]) * v3((1, 1, 0)))
        R = rot_from_axes(z_axis=n, y_axis=(0, 0, 1))
        fd.add(RoundBox(h[0] + n * 0.006, (0.034, 0.024, 0.007), 0.004, R=R), 0.002, 5)
    # the radio in its pouch on the left side, its antenna rising behind his shoulder
    p, n = radio_spot()
    sd = norm(np.cross(v3((0, 0, 1)), n))
    R = np.stack([sd, v3((0, 0, 1)), n], axis=1)
    c = p + n * 0.022
    fd.add(RoundBox(c + v3((0, 0, -0.01)), (0.033, 0.05, 0.022), 0.008, R=R), 0.004)
    fd.add(RoundBox(c + n * 0.002 + v3((0, 0, 0.045)), (0.026, 0.02, 0.017), 0.006, R=R), 0.003, 8)
    fd.add(Cylinder(c + n * 0.006 + sd * 0.01 + v3((0, 0, 0.07)), 0.007, 0.016, rr=0.002), 0.002, 5)     # a knob
    ap = antenna_pts()
    fd.add(Cylinder(ap[0] - v3((0, 0, 0.006)), 0.008, 0.022, rr=0.003), 0.003, 5)
    fd.add(Chain(ap, [0.006, 0.0052, 0.0045, 0.004], k=0.002), 0.002, 5)
    fd.add(Sphere(ap[-1], 0.0065), 0.002, 5)
    return fd


# ======================================================================================= the ghillie capelet
CAPE_OFF, CAPE_T = 0.064, 0.013


def _cape_hem(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    a = np.arctan2(x, -(y - F(0.05)))
    fa = np.cos(a)
    hem = F(1.27) + F(0.075) * np.clip(fa, 0, 1) - F(0.075) * np.clip(-fa, 0, 1)
    hem = hem + F(0.025) * np.where(x < 0, np.clip(fa, 0, 1), F(0)) * smoothstep(0.06, 0.16, np.abs(x))   # (clear of the butt's pocket)
    return hem + F(0.016) * np.sin(a * F(11) + F(0.7)) + F(0.012) * NOISE(P * F(9))


def _cape_keep(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    k = _cape_hem(P) - z
    rho = np.sqrt(x * x + ((y - F(0.05)) * F(0.95)) ** 2)
    neck = z - (F(1.45) + F(0.4) * smoothstep(0.15, 0.2, rho))
    k = np.maximum(k, neck)
    for side in ("R", "L"):
        sx = -1 if side == "R" else 1
        sh, el = J["shoulder_" + side], J["elbow_" + side]
        ax = norm(el - sh)
        along = (P - sh.astype(F)) @ ax.astype(F)
        lim = F(0.12) + F(0.012) * np.sin(np.arctan2(y, z) * F(17))
        k = np.maximum(k, np.where(x * F(sx) > F(0.24), along - lim, F(-1.0)))
    return k


def cape_outer(extra=0.0):
    b = shirt_base()
    return Func(lambda P: b.eval(P, margin=0.12) - F(CAPE_OFF + CAPE_T / 2 + extra), (-0.7, -0.6, 0.9), (0.7, 0.6, 1.65))


def strand_paths(n=84, seed=23):
    """Hanging jute strips round the capelet's hem: (points, normals, label) each."""
    rs = np.random.RandomState(seed)
    co = cape_outer(-0.004)
    out = []
    for i in range(n):
        a = 2 * math.pi * (i + rs.uniform(-0.3, 0.3)) / n
        d = v3((math.sin(a), -math.cos(a), 0.0))
        # where the hem is along this direction: march down from high up until outside the kept region
        x0 = v3((0.0, 0.05, 0.0))
        z_hem = None
        for z in np.arange(1.5, 1.05, -0.006):
            h, ok = ray_hit(co, [x0 + d * 0.7 + v3((0, 0, z))], [-d], tmax=0.75, step=0.003)
            if not ok[0]:
                continue
            if _cape_keep(np.array([h[0]], F))[0] > 0:
                if z_hem is not None:
                    break
                continue
            z_hem = (z, h[0])
        if z_hem is None:
            continue
        z0, p0 = z_hem
        z0 = z0 + (rs.uniform(0.02, 0.1) if i % 3 == 1 else 0.0)                 # (a layer of strips laid on the net above the hem)
        L = rs.uniform(0.04, 0.15) * (1.25 if math.cos(a) < -0.3 else 1.0)
        pts, ns = [], []
        for j in range(5):
            z = z0 + 0.03 - (L + 0.03) * j / 4
            h, ok = ray_hit(co, [x0 + d * 0.7 + v3((0, 0, z))], [-d], tmax=0.75, step=0.003)
            p = h[0] if ok[0] else (pts[-1] + v3((0, 0, -(L + 0.03) / 4)) if pts else p0)
            if pts and ok[0] and np.linalg.norm(p - pts[-1]) > 0.08:
                p = pts[-1] + v3((0, 0, -(L + 0.03) / 4))
            pts.append(p + d * 0.002)
            ns.append(d)
        out.append((pts, ns, (0, 0, 5, 6)[rs.randint(4)], rs.uniform(0.011, 0.017)))
    return out


def cape_field():
    """Jute ghillie strips on a net over his shoulders: the body (label 0, mottled moss and olive) with deep vertical
    fibres, a ragged hem, strips hanging from it (0, tan 5, brown 6)."""
    fd = Field("Cape")
    base = shirt_base()
    fib = lambda P: (F(0.0035) * np.sin(np.arctan2(P[:, 0], P[:, 1] - F(0.05)) * F(46) + F(5.0) * NOISE(P * F(4)) + P[:, 2] * F(9)) * (F(0.6) + F(0.6) * NOISE(P * F(9)))
                     + F(0.0016) * NOISE(P * np.array([90, 90, 20], F)) + F(0.002) * NOISE(P * F(14)))
    lo, hi = (-0.62, -0.5, 1.0), (0.62, 0.55, 1.62)
    fd.add(Inter(Func(_cape_keep, lo, hi), Shell(base, CAPE_OFF, CAPE_T, pad=0.12, disp=fib, disp_amp=0.005), 0.006), 0.0)
    sfib = lambda P: F(0.0012) * NOISE(P * np.array([140, 140, 30], F))
    for pts, ns, lab, w in strand_paths():
        n = len(pts)
        ws = [w * (1.0 - 0.5 * (j / (n - 1)) ** 2) for j in range(n)]
        fd.add(Lock(pts, ws, [0.0035] * n, ns, k=0.004, disp=sfib, disp_amp=0.0015), 0.004, lab)
    return fd


# ======================================================================================= the rifle
# Rifle coordinates: u along the bore (forward), v to the gun's right (the bolt side), h up; the origin (u = 0, h = 0) is
# the right fist's grip centre on the pistol grip, below and behind the receiver.
GRIP_RAKE = 0.35                            # the pistol grip's rake (radians from square to the bore)
BORE_H = 0.072                              # the bore's height over the grip centre
BUTT_U = -0.45
RECV_U = (-0.06, 0.29)
HG_U = (0.28, 0.68)                         # the handguard
BRAKE_U = (1.015, 1.125)
MUZZLE_U = BRAKE_U[1]
MAG_U = (0.075, 0.175)
BIPOD_U = 0.42                              # the bipod's pivot under the handguard
BIPOD_H = BORE_H - 0.05
BIPOD_L = 0.3                               # pivot to the feet's middle
BIPOD_SPLAY = 0.36                          # each leg out to the side (radians)
SCOPE_H = BORE_H + 0.1
SCOPE_U = (-0.14, 0.41)
BOLT_U = (-0.13, 0.12)
KNOB = (-0.06, 0.088, BORE_H - 0.034)       # the bolt handle's knob (u, v, h), bolt closed
HANDLE_U = -0.045                           # where the handle leaves the bolt
GLASS_U = SCOPE_U[1] - 0.012                # the objective lens (recessed in the sunshade)
LEDGE_Z = 0.56                              # the sandbags' top under the bipod's feet (above where he kneels)
RING_R = 0.86                               # the ring's middle radius (the bipod's feet land on it as he turns)


def rifle_frame():
    """Rest pose: the pistol grip in his right fist (the grip's axis along the fist's thumb axis), the barrel pointing
    up beside his right arm, a little outward (the gun's parts are moved apart for the bake: BAKE_APART)."""
    wr, f, n, t = hand_frame("R")
    G = fist_center("R")
    g = norm(t)
    ref = norm(v3((-0.35, 0.0, 1.0)))
    A0 = norm(ref - g * (g @ ref))
    s, c = math.sin(GRIP_RAKE), math.cos(GRIP_RAKE)
    A = A0 * c + g * s
    U = norm(g - A * (g @ A))
    S = np.cross(A, U)
    return G, A, U, S


RIFLE_FRAME = rifle_frame


def mpt(u, v=0.0, h=0.0):
    G, A, U, S = rifle_frame()
    return G + A * u + S * v + U * h


def m_local(P):
    G, A, U, S = rifle_frame()
    q = P - G.astype(F)
    return q @ A.astype(F), q @ S.astype(F), q @ U.astype(F)


def m_bounds(u0, u1, r=0.15, h0=None, h1=None):
    h0 = -r if h0 is None else h0
    h1 = r if h1 is None else h1
    pts = [mpt(u, v, h) for u in (u0, u1) for v in (-r, r) for h in (h0, h1)]
    return np.min(pts, 0), np.max(pts, 0)


def _rbox(u, v, h, cu, cv, ch, hu, hv, hh, rr):
    q = np.stack([np.abs(u - F(cu)) - F(hu) + F(rr), np.abs(v - F(cv)) - F(hv) + F(rr), np.abs(h - F(ch)) - F(hh) + F(rr)], 1)
    return np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - F(rr)


def stock_profile(u):
    """(h_bot, h_top, half width) of the butt stock at u (arrays): a straight comb just under the bore, the bottom line
    sloping down to the butt's toe."""
    k = np.clip((F(-0.05) - u) / F(-0.05 - BUTT_U), 0, 1)               # 0 at the receiver .. 1 at the butt
    hb = F(0.008) - F(0.1) * k
    ht = F(BORE_H - 0.012) + F(0.004) * k
    w = F(0.02) + F(0.004) * k
    return hb, ht, w


def _stock_sd(P):
    u, v, h = m_local(P)
    hb, ht, w = stock_profile(u)
    hc, hh = (ht + hb) / F(2), (ht - hb) / F(2)
    rr = F(0.01)
    q = np.stack([np.abs(v) - w + rr, np.abs(h - hc) - hh + rr, np.maximum(F(BUTT_U) - u, u - F(RECV_U[0] + 0.01)) + rr], 1)
    d = np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - rr
    # a skeleton hole through the butt (behind the grip), the cheek riser on top
    hole = _rbox(u, v, h, -0.2, 0.0, -0.032, 0.085, 0.05, 0.018, 0.015)
    d = np.maximum(d, -hole)
    riser = _rbox(u, v, h, -0.25, 0.0, BORE_H + 0.012, 0.1, 0.017, 0.032, 0.012)
    return np.minimum(d, riser)


def _grip_sd(P):
    """The pistol grip: a rounded block along the grip's axis, finger grooves on its front."""
    u, v, h = m_local(P)
    s, c = F(math.sin(GRIP_RAKE)), F(math.cos(GRIP_RAKE))
    gu = u * s + h * c                       # along the grip (up)
    gf = u * c - h * s                       # across it (forward)
    d = _rbox(gf, v, gu, 0.002, 0.0, -0.005, 0.024, 0.016, 0.062, 0.012)
    grooves = F(0.0025) * smoothstep(0.4, 0.9, np.cos(gu * F(2 * math.pi / 0.024))) * smoothstep(0.015, 0.024, gf)
    return d + grooves


def _brake_sd(P):
    u, v, h = m_local(P)
    c = (BRAKE_U[0] + BRAKE_U[1]) / 2
    d = _rbox(u, v, h, c, 0.0, BORE_H, (BRAKE_U[1] - BRAKE_U[0]) / 2, 0.03, 0.025, 0.008)
    for pu in (BRAKE_U[0] + 0.032, BRAKE_U[0] + 0.074):
        port = _rbox(u, v, h, pu, 0.0, BORE_H, 0.016, 0.05, 0.016, 0.004)
        d = np.maximum(d, -port)
    bore = np.maximum(np.sqrt(v * v + (h - F(BORE_H)) ** 2) - F(0.009), F(BRAKE_U[1] - 0.03) - u)
    return np.maximum(d, -bore)


def _barrel_sd(P):
    u, v, h = m_local(P)
    a = np.arctan2(v, h - F(BORE_H))
    flutes = F(0.0028) * smoothstep(0.3, 0.9, np.cos(a * F(6))) * smoothstep(HG_U[1] + 0.02, HG_U[1] + 0.05, u) * smoothstep(BRAKE_U[0] - 0.01, BRAKE_U[0] - 0.04, u)
    r = np.sqrt(v * v + (h - F(BORE_H)) ** 2) - (F(0.0185) - flutes)
    ax = np.maximum(F(HG_U[0]) - u, u - F(BRAKE_U[0] + 0.01))
    q0, q1 = np.maximum(r, 0), np.maximum(ax, 0)
    return np.sqrt(q0 * q0 + q1 * q1) + np.minimum(np.maximum(r, ax), 0)


def _handguard_sd(P):
    """A long octagonal tube round the barrel, M-LOK slots down its sides and under it."""
    u, v, h = m_local(P)
    hh = h - F(BORE_H)
    c45 = F(math.sqrt(0.5))
    oct_ = np.maximum(np.maximum(np.abs(v), np.abs(hh)), (np.abs(v) + np.abs(hh)) * c45) - F(0.033)
    ax = np.abs(u - F((HG_U[0] + HG_U[1]) / 2)) - F((HG_U[1] - HG_U[0]) / 2)
    q0, q1 = np.maximum(oct_ + F(0.004), 0), np.maximum(ax + F(0.004), 0)
    d = np.sqrt(q0 * q0 + q1 * q1) + np.minimum(np.maximum(oct_, ax), 0) - F(0.004)
    pitch = F(0.05)
    lu = np.mod(u - F(HG_U[0] + 0.05), pitch) - pitch / F(2)
    on = (u > F(HG_U[0] + 0.04)) & (u < F(HG_U[1] - 0.03))
    slot_side = np.maximum(np.maximum(np.abs(lu) - F(0.014), np.abs(hh) - F(0.006)), F(0.024) - np.abs(v))
    slot_bot = np.maximum(np.maximum(np.abs(lu) - F(0.014), np.abs(v) - F(0.006)), F(0.024) + hh)
    slots = np.where(on, np.minimum(slot_side, slot_bot), F(1.0))
    return np.maximum(d, -slots)


def rifle_field():
    """Black polymer (label 0): the stock with its cheek riser and skeleton hole, the pistol grip, the handguard; a
    rubber butt pad (12); gunmetal (9): the receiver, its rail, the magazine, the barrel, the muzzle brake, the bipod's
    mount, the trigger guard."""
    fd = Field("Rifle")
    G, A, U, S = rifle_frame()
    Rm = np.stack([A, S, U], axis=1)
    lo, hi = m_bounds(BUTT_U - 0.02, MUZZLE_U + 0.02, 0.12)
    stip = lambda P: F(0.0004) * NOISE(P * F(150))
    fd.add(Func(_stock_sd, *m_bounds(BUTT_U - 0.02, RECV_U[0] + 0.03, 0.14), disp=stip, disp_amp=0.0005), 0.0)
    fd.paint(Func(lambda P: m_local(P)[0] - F(BUTT_U + 0.022), *m_bounds(BUTT_U - 0.02, BUTT_U + 0.05, 0.14)), 12)
    fd.add(Func(_grip_sd, *m_bounds(-0.1, 0.06, 0.12)), 0.006)
    # the receiver: a long block round the bolt, flat sides, the rail on top
    def recv(P):
        u, v, h = m_local(P)
        d = _rbox(u, v, h, (RECV_U[0] + RECV_U[1]) / 2, 0.0, BORE_H - 0.004, (RECV_U[1] - RECV_U[0]) / 2, 0.027, 0.034, 0.008)
        port = _rbox(u, v, h, -0.005, 0.03, BORE_H + 0.004, 0.04, 0.012, 0.013, 0.004)       # the ejection port (right)
        d = np.maximum(d, -port)
        way = np.maximum(np.sqrt(v * v + (h - F(BORE_H)) ** 2) - F(0.0135), u - F(RECV_U[0] + 0.07))   # the bolt's way in
        return np.maximum(d, -way)
    fd.add(Func(recv, *m_bounds(RECV_U[0] - 0.02, RECV_U[1] + 0.02, 0.1)), 0.003, 9)
    def rail(P):
        u, v, h = m_local(P)
        d = _rbox(u, v, h, (RECV_U[0] + HG_U[1] - 0.08) / 2, 0.0, BORE_H + 0.037, (HG_U[1] - 0.08 - RECV_U[0]) / 2, 0.011, 0.007, 0.002)
        teeth = np.maximum(np.abs(np.mod(u, F(0.01)) - F(0.005)) - F(0.0022), F(BORE_H + 0.04) - h)
        return np.maximum(d, -teeth)
    fd.add(Func(rail, *m_bounds(RECV_U[0] - 0.02, HG_U[1], 0.1, -0.02, 0.15)), 0.002, 9)
    fd.add(Func(_handguard_sd, *m_bounds(HG_U[0] - 0.01, HG_U[1] + 0.01, 0.06, BORE_H - 0.06, BORE_H + 0.06)), 0.004)
    fd.add(Func(_barrel_sd, *m_bounds(HG_U[0], BRAKE_U[0] + 0.02, 0.04, BORE_H - 0.04, BORE_H + 0.04)), 0.003, 9)
    fd.add(Func(_brake_sd, *m_bounds(BRAKE_U[0] - 0.01, BRAKE_U[1] + 0.01, 0.05, BORE_H - 0.05, BORE_H + 0.05)), 0.004, 9)
    # the box magazine, raked a little forward
    mc = mpt((MAG_U[0] + MAG_U[1]) / 2, 0.0, -0.012)
    fd.add(RoundBox(mc, ((MAG_U[1] - MAG_U[0]) / 2, 0.021, 0.05), 0.006, R=Rm @ euler(0, 0.1, 0)), 0.004, 9)
    fd.add(RoundBox(mc + U * -0.048 + A * 0.004, ((MAG_U[1] - MAG_U[0]) / 2 + 0.004, 0.024, 0.008), 0.004, R=Rm @ euler(0, 0.1, 0)), 0.003, 0)
    # the trigger guard and trigger
    mp = lambda u, h, v=0.0: mpt(u, v, h)
    guard = [mp(0.005, 0.038), mp(0.03, -0.012), mp(0.06, -0.016), mp(0.074, 0.008), mp(0.074, 0.038)]
    fd.add(Chain(guard, [0.0045] * 5, k=0.003), 0.003, 9)
    fd.add(Chain([mp(0.045, 0.036), mp(0.042, 0.016), mp(0.035, 0.004)], [0.004, 0.0035, 0.003], k=0.002), 0.002, 9)
    # the bipod's mount under the handguard, a sling stud and the rear monopod's knob under the butt
    fd.add(RoundBox(mpt(BIPOD_U, 0.0, BIPOD_H + 0.012), (0.03, 0.022, 0.014), 0.005, R=Rm), 0.004, 9)
    hb = float(stock_profile(np.array([-0.38], F))[0][0])
    fd.add(Cylinder(mpt(-0.38, 0.0, hb - 0.008), 0.013, 0.03, rr=0.004, R=rot_from_axes(z_axis=U, y_axis=A)), 0.004, 9)
    fd.add(Cylinder(mpt(-0.38, 0.0, hb - 0.03), 0.009, 0.02, rr=0.003, R=rot_from_axes(z_axis=U, y_axis=A)), 0.003, 12)
    return fd


def scope_r(u):
    """The scope's radius along it: the ocular bell, the tube, the objective bell and its sunshade."""
    u = np.asarray(u, F)
    r = F(0.0175) + F(0.0085) * smoothstep(-0.04, -0.075, u) + F(0.0155) * smoothstep(0.215, 0.285, u)
    return r


def scope_field():
    """The scope: black anodised (label 5) tube and bells, gunmetal (9) rings and turrets with knurled caps, the
    ocular glass (11); the flip caps open (5): the rear one standing up behind the eyepiece, the front one swung out to
    the left."""
    fd = Field("Scope")
    G, A, U, S = rifle_frame()
    Rm = np.stack([A, S, U], axis=1)
    def tube(P):
        u, v, h = m_local(P)
        rad = np.sqrt(v * v + (h - F(SCOPE_H)) ** 2) - scope_r(u)
        ax = np.maximum(F(SCOPE_U[0]) - u, u - F(SCOPE_U[1]))
        q0, q1 = np.maximum(rad + F(0.004), 0), np.maximum(ax + F(0.004), 0)
        d = np.sqrt(q0 * q0 + q1 * q1) + np.minimum(np.maximum(rad, ax), 0) - F(0.004)
        rec = np.maximum(np.sqrt(v * v + (h - F(SCOPE_H)) ** 2) - (scope_r(u) - F(0.004)), F(GLASS_U) - u)
        rec2 = np.maximum(np.sqrt(v * v + (h - F(SCOPE_H)) ** 2) - F(0.019), u - F(SCOPE_U[0] + 0.006))
        return np.maximum(d, -np.minimum(rec, rec2))
    lo, hi = m_bounds(SCOPE_U[0] - 0.01, SCOPE_U[1] + 0.01, 0.05, SCOPE_H - 0.05, SCOPE_H + 0.05)
    fd.add(Func(tube, lo, hi, disp=lambda P: F(0.0003) * NOISE(P * F(120)), disp_amp=0.0004), 0.0, 5)
    fd.add(Cylinder(mpt(SCOPE_U[0] + 0.009, 0.0, SCOPE_H), 0.019, 0.004, R=rot_from_axes(z_axis=A)), 0.0, 11)   # ocular glass
    # rings and their bases on the rail
    for u0 in (0.0, 0.2):
        fd.add(Torus(mpt(u0, 0.0, SCOPE_H), 0.0205, 0.0055, R=rot_from_axes(z_axis=A, y_axis=U)), 0.003, 9)
        fd.add(RoundBox(mpt(u0, 0.0, (SCOPE_H + BORE_H + 0.044) / 2 - 0.004), (0.011, 0.012, (SCOPE_H - BORE_H - 0.044) / 2), 0.003, R=Rm), 0.004, 9)
        fd.add(Cylinder(mpt(u0, 0.016, BORE_H + 0.05), 0.006, 0.01, rr=0.002, R=rot_from_axes(z_axis=S)), 0.002, 9)   # cross-bolt nut
    # turrets: elevation on top, windage to the right, parallax to the left
    knurl = lambda P: F(0.0007) * np.sin(np.arctan2(*m_local(P)[:2]) * F(40))
    tu = 0.1
    fd.add(Cylinder(mpt(tu, 0.0, SCOPE_H + 0.03), 0.0165, 0.026, rr=0.004, R=rot_from_axes(z_axis=U, y_axis=A), disp=knurl, disp_amp=0.001), 0.004, 9)
    fd.add(Cylinder(mpt(tu, 0.03, SCOPE_H), 0.015, 0.022, rr=0.004, R=rot_from_axes(z_axis=S, y_axis=A)), 0.004, 9)
    fd.add(Cylinder(mpt(tu, -0.028, SCOPE_H), 0.014, 0.018, rr=0.004, R=rot_from_axes(z_axis=-S, y_axis=A)), 0.004, 9)
    fd.add(Cylinder(mpt(tu, 0.0, SCOPE_H), 0.022, 0.05, rr=0.006, R=rot_from_axes(z_axis=S, y_axis=A)), 0.004, 5)    # the saddle
    # the flip caps (open): rear hinged on top of the eyepiece, standing up; front hinged on its left, swung out
    hr_ = scope_r(np.array([SCOPE_U[0]], F))[0]
    hinge = mpt(SCOPE_U[0] + 0.004, 0.0, SCOPE_H + float(hr_) + 0.003)
    fd.add(Cylinder(hinge, 0.005, 0.016, rr=0.002, R=rot_from_axes(z_axis=S)), 0.002, 5)
    ax_up = norm(U * math.cos(0.5) + A * math.sin(0.5))                    # the cap flipped up and over, leaning forward
    fd.add(Cylinder(hinge + ax_up * (float(hr_) + 0.004) - A * 0.006, float(hr_) + 0.004, 0.008, rr=0.003,
                    R=rot_from_axes(z_axis=norm(np.cross(ax_up, S)), y_axis=ax_up)), 0.003, 5)
    fr = float(scope_r(np.array([SCOPE_U[1]], F))[0])
    hinge_f = mpt(SCOPE_U[1] + 0.002, -(fr + 0.003), SCOPE_H)
    fd.add(Cylinder(hinge_f, 0.005, 0.016, rr=0.002, R=rot_from_axes(z_axis=U)), 0.002, 5)
    sw = norm(-S * math.cos(0.35) + A * math.sin(0.35))                      # swung out to the left, a little forward
    fd.add(Cylinder(hinge_f + sw * (fr + 0.004), fr + 0.004, 0.009, rr=0.003, R=rot_from_axes(z_axis=norm(np.cross(U, sw)), y_axis=U)), 0.003, 5)
    return fd


def lens_field():
    """The objective lens (its own faintly glowing mesh)."""
    fd = Field("Lens")
    G, A, U, S = rifle_frame()
    r = float(scope_r(np.array([GLASS_U], F))[0]) - 0.004
    fd.add(Cylinder(mpt(GLASS_U + 0.001, 0.0, SCOPE_H), r, 0.006, rr=0.002, R=rot_from_axes(z_axis=A)), 0.0)
    return fd


def bolt_field():
    """The bolt: its shroud behind the receiver (gunmetal 9), the body (bright steel 10) and the handle (10) with a big
    black knob (5), turned down."""
    fd = Field("Bolt")
    G, A, U, S = rifle_frame()
    fd.add(RoundCone(mpt(BOLT_U[0] + 0.03, 0.0, BORE_H), mpt(BOLT_U[1], 0.0, BORE_H), 0.0125, 0.0125), 0.0, 10)
    fd.add(Cylinder(mpt(BOLT_U[0] + 0.022, 0.0, BORE_H), 0.0175, 0.044, rr=0.006, R=rot_from_axes(z_axis=A)), 0.003, 9)
    fd.add(Sphere(mpt(BOLT_U[0] - 0.002, 0.0, BORE_H), 0.009), 0.004, 9)
    root = mpt(HANDLE_U, 0.008, BORE_H)
    knob = mpt(*KNOB)
    mid = mpt((HANDLE_U + KNOB[0]) / 2, 0.05, BORE_H - 0.012)
    fd.add(Chain([root, mid, knob], [0.0075, 0.0062, 0.0058], k=0.003), 0.003, 10)
    fd.add(Ellipsoid(knob + norm(knob - mid) * 0.01, (0.017, 0.017, 0.02), R=rot_from_axes(z_axis=norm(knob - mid))), 0.003, 5)
    return fd


def bipod_frame():
    """The bipod's pivot (rest pose) and its axes: down its legs D (the gun's down), across S, along the gun A."""
    G, A, U, S = rifle_frame()
    return mpt(BIPOD_U, 0.0, BIPOD_H), -U, S, A


def bipod_feet():
    P0, D, S, A = bipod_frame()
    return [P0 + (D * math.cos(BIPOD_SPLAY) + S * (sv * math.sin(BIPOD_SPLAY))) * BIPOD_L for sv in (-1, 1)]


def bipod_field():
    """The bipod: a gunmetal (9) yoke clamped under the handguard, two black (5) legs splayed out, their lower tubes
    (9) drawn out, rubber feet (12)."""
    fd = Field("Bipod")
    P0, D, S, A = bipod_frame()
    fd.add(RoundBox(P0, (0.024, 0.028, 0.014), 0.006, R=np.stack([S, A, -D], axis=1)), 0.0, 9)
    fd.add(Cylinder(P0 + A * 0.0, 0.009, 0.06, rr=0.003, R=rot_from_axes(z_axis=S)), 0.003, 9)      # the pivot pin
    for sv in (-1, 1):
        L = norm(D * math.cos(BIPOD_SPLAY) + S * (sv * math.sin(BIPOD_SPLAY)))
        a = P0 + S * (sv * 0.022)
        fd.add(RoundCone(a, a + L * 0.15, 0.0105, 0.0105), 0.004, 5)
        fd.add(RoundCone(a + L * 0.14, a + L * (BIPOD_L - 0.02), 0.0075, 0.0075), 0.003, 9)
        fd.add(Torus(a + L * 0.145, 0.0105, 0.003, R=rot_from_axes(z_axis=L)), 0.002, 5)          # the lock collar
        fd.add(Ellipsoid(a + L * BIPOD_L, (0.016, 0.016, 0.014), R=rot_from_axes(z_axis=L)), 0.004, 12)
    return fd


# ======================================================================================= painting
def warm_points():
    pts = [(hp((0, -0.25, 1.609)), 0.045, 0.5)]
    for sx in (-1, 1):
        pts += [(hp((sx * 0.105, -0.14, 1.63)), 0.05, 0.4)]
    return pts


# ======================================================================================= build config
GLB_NAME = "sniper"
ROOT_NAME = "SniperHQ"
TEX_PREFIX = "snip"
MAT_NAME = "SniperMat"
MESH_NAME = "Sniper"
BASE_MODULE = "sniper_base"
ANIM_MODULE = "anim_sniper"
PARTS = ["Skin", "Eyes", "Teeth", "Hair", "Hat", "Scrim", "Headset", "Shirt", "Trousers", "Pads", "Boots", "Gloves", "Vest",
         "Cape", "Rifle", "Scope", "Lens", "Bolt", "Bipod"]
REGION_PARTS = ("Skin", "Hat", "Scrim", "Headset", "Shirt", "Trousers", "Pads", "Boots", "Gloves", "Vest", "Cape", "Rifle",
                "Scope", "Bolt", "Bipod")
OLIVE = (0.4, 0.42, 0.28)                   # the task force's olive drab (the brief)
OLIVE_DARK = (0.31, 0.33, 0.22)
COYOTE = (0.6, 0.5, 0.36)
RED = (0.74, 0.1, 0.08)
WHITE = (0.93, 0.92, 0.88)
GUNMETAL = (0.24, 0.25, 0.27)
BLACK = (0.075, 0.075, 0.08)
HAIR = {"name": "HQ_SnipHair", "base": (0.12, 0.09, 0.07), "hi": (0.3, 0.24, 0.19), "low": (0.05, 0.04, 0.03),
        "streak": (0.08, 0.06, 0.045), "tint": (0.18, 0.13, 0.09)}
CLOTH = dict(base=OLIVE, facing=RED, brass=GUNMETAL, buff=WHITE, black=BLACK)
GHILLIE = {"name": "HQ_Ghillie"}
MAT_OVERRIDES = {
    "Skin": ("skin", {"name": "HQ_SnipSkin", "base": (0.76, 0.54, 0.41), "ruddy": (0.78, 0.46, 0.36), "lips": (0.6, 0.37, 0.32),
                      "brow": ((0.07, 0.05, 0.04), (0.16, 0.11, 0.08)),
                      "extra": ((LASH, (0.06, 0.04, 0.035), 0.5), (STUBBLE, (0.3, 0.22, 0.18), 0.6, 0.45))}),
    "Hair": ("hair", HAIR),
    "Hat": ("uniform", dict(CLOTH, name="HQ_SnipHat", facing=OLIVE_DARK)),
    "Scrim": ("ghillie", GHILLIE),
    "Headset": ("modern_kit", {"name": "HQ_SnipHeadset", "base": OLIVE_DARK}),
    "Shirt": ("uniform", dict(CLOTH, name="HQ_SnipShirt")),
    "Trousers": ("uniform", dict(CLOTH, name="HQ_SnipTrousers", base=(0.37, 0.39, 0.26))),
    "Pads": ("modern_kit", {"name": "HQ_SnipBlack", "base": BLACK, "weave": 0.0}),
    "Boots": ("leather_dyed", {"name": "HQ_SnipBoots", "base": (0.075, 0.07, 0.07), "dyed": (0.045, 0.042, 0.042), "worn_c": (0.3, 0.29, 0.28)}),
    "Gloves": ("leather_dyed", {"name": "HQ_SnipGloves", "base": (0.08, 0.078, 0.08), "dyed": (0.16, 0.16, 0.16), "worn_c": (0.3, 0.3, 0.3)}),
    "Vest": ("modern_kit", {"name": "HQ_SnipVest", "base": COYOTE}),
    "Cape": ("ghillie", GHILLIE),
    "Rifle": ("modern_kit", {"name": "HQ_SnipRifle", "base": BLACK, "weave": 0.0}),
    "Scope": ("modern_kit", {"name": "HQ_SnipRifle", "base": BLACK, "weave": 0.0}),
    "Bolt": ("modern_kit", {"name": "HQ_SnipRifle", "base": BLACK, "weave": 0.0}),
    "Bipod": ("modern_kit", {"name": "HQ_SnipRifle", "base": BLACK, "weave": 0.0}),
}
GLOW = {"Lens": ((0.62, 0.86, 1.0), 0.7, 0.45)}
LOW_TARGETS = {"Skin": 4400, "Teeth": 60, "Hair": 700, "Hat": 1500, "Scrim": 700, "Headset": 600, "Shirt": 2300,
               "Trousers": 2000, "Pads": 500, "Boots": 1200, "Gloves": 900, "Vest": 3000, "Cape": 3200, "Rifle": 2400,
               "Scope": 1300, "Lens": 60, "Bolt": 300, "Bipod": 500}
AO_EXCLUDE = ["Rifle", "Scope", "Lens", "Bolt", "Bipod", "Scrim"]
BAKE_APART = (["Rifle", "Scope", "Bolt", "Bipod", "Lens"], (-0.9, 0.0, 0.0))


def prop_bones():
    """The rifle, its bolt and its bipod have no parent (posed in the world, "world" aims)."""
    P0, D, S, A = bipod_frame()
    return [("rifle", mpt(0.0), mpt(MUZZLE_U, 0.0, BORE_H), None),
            ("bolt", mpt(HANDLE_U, 0.0, BORE_H), mpt(HANDLE_U + 0.1, 0.0, BORE_H), None),
            ("bipod", P0, P0 + D * 0.12, None)]


def glove_weights(ob, skin_ob, arm):
    """The gloves go with the hands; their cuffs blend into the forearms."""
    from ugo import _blend_add
    groups = {}
    for v in ob.data.vertices:
        p = np.array(v.co, F)[None, :]
        side = "R" if p[0, 0] < 0 else "L"
        a = float(_glove_along(p, side)[0])
        k = max(0.0, min(1.0, (a - 0.012) / 0.03))
        k = k * k * (3 - 2 * k)
        _blend_add(ob, groups, v.index, {"hand." + side: k, "forearm." + side: 1.0 - k})


def weight_rules():
    body = TORSO | {"clavicle.R", "clavicle.L"}
    arms = {"upperarm.R", "upperarm.L", "forearm.R", "forearm.L"}
    return {
        "Eyes": ("rigid", "head"), "Teeth": ("rigid", "head"), "Hair": ("rigid", "head"), "Hat": ("rigid", "head"),
        "Scrim": ("rigid", "head"), "Headset": ("rigid", "head"),
        "Shirt": ("transfer", body | arms, None),
        "Cape": ("transfer", body | arms, None),
        "Vest": ("transfer", body, None),
        "Trousers": ("transfer", body | {"thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Pads": ("transfer", {"thigh.R", "thigh.L", "shin.R", "shin.L"}, None),
        "Boots": ("transfer", {"shin.R", "shin.L", "foot.R", "foot.L"}, None),
        "Gloves": ("custom", glove_weights),
        "Rifle": ("rigid", "rifle"), "Scope": ("rigid", "rifle"), "Lens": ("rigid", "rifle"), "Bolt": ("rigid", "bolt"),
        "Bipod": ("rigid", "bipod"),
    }


def uv_boost(c, part):
    face_z = hp((0, 0, 1.45))[2]
    if part == "Eyes":
        return 2.0
    if part in ("Skin", "Teeth") and c.z > face_z and c.y < 0.0 and abs(c.x) < 0.3:
        return 1.9
    if part in ("Rifle", "Bipod"):
        return 0.85
    if part in ("Scope", "Bolt", "Hat", "Headset"):
        return 1.15
    return 1.0


def sculpt_parts(fine=True):
    return [
        ("Skin", skin_field(), 0.003 if fine else 0.0045),
        ("Eyes", eyes_field(), 0.0015),
        ("Teeth", teeth_field(), 0.0012),
        ("Hair", hair_field(), 0.0024 if fine else 0.0034),
        ("Hat", hat_field(), 0.0022 if fine else 0.003),
        ("Scrim", scrim_field(), 0.0014 if fine else 0.002),
        ("Headset", headset_field(), 0.0016 if fine else 0.0022),
        ("Shirt", shirt_field(), 0.0026 if fine else 0.0036),
        ("Trousers", trousers_field(), 0.0026 if fine else 0.0036),
        ("Pads", pads_field(), 0.002 if fine else 0.0028),
        ("Boots", boots_field(), 0.0024 if fine else 0.0034),
        ("Gloves", gloves_field(), 0.0018 if fine else 0.0024),
        ("Vest", vest_field(), 0.002 if fine else 0.0028),
        ("Cape", cape_field(), 0.0022 if fine else 0.003),
        ("Rifle", rifle_field(), 0.0016 if fine else 0.0022),
        ("Scope", scope_field(), 0.0014 if fine else 0.002),
        ("Lens", lens_field(), 0.0012),
        ("Bolt", bolt_field(), 0.0011 if fine else 0.0014),
        ("Bipod", bipod_field(), 0.0014 if fine else 0.002),
    ]
