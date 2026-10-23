"""Sniper base: an overwatch nest on a flat roof. A round plinth of cast concrete (the top of a building: shuttering
joints, rust streaks, a galvanized coping round its lip) rising from a suburban lawn; on the roof's gravel a ring of
sandbags four courses high (the nest), its top course pressed flat where the rifle's bipod rests (wherever the tower
turns, the feet land on it: anim_sniper.LEDGE_Z, sniper.RING_R); a scrap of camo net with jute garnish thrown over the
back of the ring and spilling onto the roof. Inside the ring, round his knees: an olive .50 ammo can with a laser
rangefinder on it, a canteen, a rugged laptop open on its case (the screen faintly lit: its own glowing mesh), a
spotting scope on a short tripod, spent brass on the gravel; outside it on the roof a mushroom vent and a drain; round
the plinth's foot grass and dandelions (distance fields + direct low-poly geometry for the grass and the flowers).

Nothing inside the ring rises above r_body (where he kneels and turns) or into the rifle's sweep (everything is under
LEDGE_Z, the rifle passes over it)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b
from crossbowman_base import _bloom
import sniper as _s

GROUND_R = 1.36
GROUND_TOP = 0.08
PLINTH_R = 1.1                     # the concrete drum's face
TOP_Z = 0.22                       # the roof's gravel = where he kneels
STAND = v3((0.0, 0.0, TOP_Z))
COPE_R0, COPE_R1 = 1.035, 1.13     # the coping round the roof's lip
COPE_Z = TOP_Z + 0.07
RING_R = _s.RING_R                 # the sandbag ring's middle (the bipod's feet)
BAG = (0.205, 0.118, 0.07)         # a sandbag's half length (round the ring), depth (radial), height
COURSES = 4
N_BAGS = 14
LEDGE_TOP = TOP_Z + _s.LEDGE_Z - 0.0145    # the top course's flat (the bipod's feet sit on it: their centres 0.0145 above)
COURSE_DZ = (LEDGE_TOP - TOP_Z + 0.012 - 2 * 0.92 * BAG[2]) / (COURSES - 1)     # (the top course pressed flat by 1.2 cm)
NET_A = (math.radians(55.0), math.radians(135.0))   # the camo net over the ring's back (angles from +x)
GEAR_R = 0.62                      # the gear inside the ring (between his knees' sweep and the bags)


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def ground_height(x, y):
    r = math.hypot(x, y)
    if r < PLINTH_R - 0.02:
        return TOP_Z
    return GROUND_TOP + 0.03 * max(0.0, 1 - (r / GROUND_R) ** 2)


def _chip(P):
    return F(0.004) * NOISE(P * F(9)) + F(0.002) * NOISE(P * F(31))


def _fine(P):
    return F(0.0014) * NOISE(P * F(30)) + F(0.0008) * NOISE(P * F(90))


def _hash(a, b):
    v = np.sin(a.astype(np.float64) * 12.9898 + b.astype(np.float64) * 78.233) * 43758.5453
    return (v - np.floor(v)).astype(F)


# ---------------------------------------------------------------------------------------------- ground
def ground_field():
    """The lawn round the plinth's foot (the ground material: grass where it faces up, earth on its sides)."""
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
                disp=lambda P: F(0.006) * NOISE(P * F(7)) + F(0.003) * NOISE(P * F(23)), disp_amp=0.01), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the concrete plinth, roof
def plinth_field():
    """The building's top: cast concrete (label 0) with shuttering joints and rust streaks (9: dark stains), its lip a
    low upstand capped with galvanized flashing (8)."""
    fd = Field("Plinth")
    def joints(P):
        z = P[:, 2]
        a = np.arctan2(P[:, 1], P[:, 0])
        run = a * F(PLINTH_R)
        jz = np.abs(z - F(0.04))
        jv = np.abs(np.mod(run, F(0.62)) - F(0.31)) - F(0.31)
        j = np.minimum(jz, np.abs(jv))
        holes = F(-0.002) * smoothstep(0.012, 0.004, np.sqrt((np.mod(run + F(0.155), F(0.31)) - F(0.155)) ** 2 + (z + F(0.0)) ** 2))
        return F(-0.003) * smoothstep(0.006, 0.0, j) + holes + F(0.0015) * NOISE(P * F(20))
    def drum(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(r - F(PLINTH_R), np.maximum(P[:, 2] - F(COPE_Z - 0.02), F(-0.06) - P[:, 2]))
    fd.add(Func(drum, (-1.2, -1.2, -0.1), (1.2, 1.2, COPE_Z), disp=joints, disp_amp=0.005), 0.0)
    fd.sub(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F(COPE_R0), F(TOP_Z - 0.03) - P[:, 2]),
                (-1.1, -1.1, TOP_Z - 0.05), (1.1, 1.1, COPE_Z + 0.05)), 0.006)
    # the flashing: a folded metal cap over the upstand
    def cap(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        q = np.stack([np.abs(r - F((COPE_R0 + COPE_R1) / 2)) - F((COPE_R1 - COPE_R0) / 2 + 0.006) + F(0.004),
                      np.abs(P[:, 2] - F(COPE_Z - 0.006)) - F(0.012) + F(0.004)], 1)
        d = np.sqrt((np.maximum(q, 0) ** 2).sum(1)) + np.minimum(q.max(1), 0) - F(0.004)
        seam = np.abs(np.mod(np.arctan2(P[:, 1], P[:, 0]) * F(PLINTH_R), F(0.9)) - F(0.45))
        return d + F(0.0015) * smoothstep(0.01, 0.002, seam)
    fd.add(Func(cap, (-1.2, -1.2, COPE_Z - 0.04), (1.2, 1.2, COPE_Z + 0.03)), 0.003, 8)
    # rust streaks under the flashing's seams, dark at the foot
    def streaks(P):
        a = np.arctan2(P[:, 1], P[:, 0]) * F(PLINTH_R)
        s = np.abs(np.mod(a + F(0.2), F(0.9)) - F(0.45)) - (F(0.012) + F(0.01) * NOISE(P * F(6)))
        return np.maximum(s, P[:, 2] - F(COPE_Z - 0.025) + F(0.1) * NOISE(P * F(3)) - F(0.15))
    fd.paint(Func(streaks, (-1.2, -1.2, -0.1), (1.2, 1.2, COPE_Z)), 9)
    fd.paint(Func(lambda P: (P[:, 2] - F(0.0)) + F(0.035) * NOISE(P * F(4)), (-1.2, -1.2, -0.12), (1.2, 1.2, 0.1)), 9)
    return fd


def roof_field():
    """The roof: grey gravel (label 7) over the membrane, a cast-iron drain grate (8) near the lip."""
    fd = Field("Roof")
    def slab(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        pebbles = F(0.0035) * (np.abs(NOISE(P * F(55))) - F(0.25)) + F(0.002) * NOISE(P * F(130))
        return np.maximum(np.maximum(r - F(COPE_R0 + 0.01), P[:, 2] - F(TOP_Z) - pebbles), F(TOP_Z - 0.06) - P[:, 2])
    fd.add(Func(slab, (-1.1, -1.1, TOP_Z - 0.08), (1.1, 1.1, TOP_Z + 0.01)), 0.0, 7)
    dc = v3((math.cos(-0.9) * 0.97, math.sin(-0.9) * 0.97, TOP_Z))
    fd.add(Cylinder(dc + v3((0, 0, 0.004)), 0.055, 0.012, rr=0.004), 0.004, 8)
    def grate(P):
        q = P - dc.astype(F)
        return np.maximum(np.abs(np.mod(q[:, 0] + q[:, 1], F(0.018)) - F(0.009)) - F(0.0035),
                          np.maximum(np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - F(0.042), F(0.0) - q[:, 2]))
    fd.sub(Func(grate, dc - 0.07, dc + 0.07), 0.001)
    return fd


# ---------------------------------------------------------------------------------------------- the sandbag ring
def _bag_params(course):
    rs = np.random.RandomState(300 + course)
    n = N_BAGS
    ph = (0.5 * (course % 2) + rs.uniform(-0.08, 0.08)) * 2 * math.pi / n
    return dict(ph=ph, dl=rs.uniform(-0.012, 0.01, n), dr=rs.uniform(-0.012, 0.012, n), dz=rs.uniform(-0.006, 0.006, n),
                tw=rs.uniform(-0.06, 0.06, n), tie=rs.randint(0, 2, n) * 2 - 1, sq=rs.uniform(0.92, 1.05, n))


def _course_z(course):
    return TOP_Z + BAG[2] * 0.92 + COURSE_DZ * course


def course_fn(course):
    """All the bags of one course of the ring (pillowy blocks along the ring's chords, one end tied and pinched); the
    top course flattened on top (the bipod's ledge)."""
    pr = _bag_params(course)
    n = N_BAGS
    step = 2 * math.pi / n
    zc0 = _course_z(course)
    top = course == COURSES - 1
    hl0, hw0, hh0 = BAG
    def one(P, k):
        a = F(pr["ph"]) + k.astype(F) * F(step)
        c, s = np.cos(a), np.sin(a)
        rc = F(RING_R) + pr["dr"][k].astype(F)
        cx, cy = rc * c, rc * s
        tw = pr["tw"][k].astype(F)
        ca, sa = np.cos(a + tw), np.sin(a + tw)
        qx, qy = P[:, 0] - cx, P[:, 1] - cy
        lt = -qx * sa + qy * ca                      # along the bag (tangent)
        lr = qx * ca + qy * sa                       # radial
        zc = F(zc0) + pr["dz"][k].astype(F)
        lz = P[:, 2] - zc
        hl = F(hl0) + pr["dl"][k].astype(F)
        tie = pr["tie"][k].astype(F)
        s_end = np.clip(lt * tie / hl, 0, 1)
        pinch = F(1) - F(0.42) * s_end ** 5
        hh = F(hh0) * pr["sq"][k].astype(F) * pinch
        hw = F(hw0) * pinch
        p = F(3.2)
        e = (np.abs(lt / hl) ** p + np.abs(lr / hw) ** p + np.abs(lz / hh) ** p) ** (F(1) / p)
        d = (e - F(1)) * np.minimum(hw, hh) * F(0.9)
        if top:
            d = np.maximum(d, P[:, 2] - F(LEDGE_TOP) - F(0.004) * NOISE(P * F(14)))
        return d
    def fn(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        u = (a - F(pr["ph"])) / F(step)
        k0 = np.floor(u + F(0.5)).astype(np.int64)
        d = one(P, k0 % n)
        frac = u - np.floor(u + F(0.5))
        k1 = np.where(frac > 0, k0 + 1, k0 - 1) % n
        return smin(d, one(P, k1), 0.012)
    R = RING_R + BAG[1] + 0.05
    return Func(fn, (-R, -R, zc0 - BAG[2] - 0.02), (R, R, zc0 + BAG[2] + 0.02),
                disp=lambda P: F(0.0028) * NOISE(P * F(16)) + F(0.0009) * NOISE(P * F(60)), disp_amp=0.004)


def sandbags_field():
    """Jute sandbags (the sacking material: label 0; a stencilled mark on a few, 5; twine at the tied ends, 6) in four
    courses round him, each course's joints over the bags below."""
    fd = Field("Sandbags")
    for c in range(COURSES):
        fd.add(course_fn(c), 0.006)
    # twine round the tied ends, a stencil on a few bags' outer faces
    for c in range(COURSES):
        pr = _bag_params(c)
        step = 2 * math.pi / N_BAGS
        for k in range(N_BAGS):
            a = pr["ph"] + k * step
            tw = pr["tw"][k]
            tdir = v3((-math.sin(a + tw), math.cos(a + tw), 0.0))
            rc = RING_R + pr["dr"][k]
            cen = v3((rc * math.cos(a), rc * math.sin(a), _course_z(c) + pr["dz"][k]))
            end = cen + tdir * (BAG[0] + pr["dl"][k] - 0.03) * pr["tie"][k]
            fd.paint(Sphere(end, 0.03), 6)
            if (k + c) % 5 == 2:
                rdir = v3((math.cos(a + tw), math.sin(a + tw), 0.0))
                pc = cen + rdir * (BAG[1] - 0.01)
                fd.paint(Func(lambda P, pc=pc, tdir=tdir: np.maximum(np.abs((P - pc.astype(F)) @ tdir.astype(F)) - F(0.05),
                                                                     np.abs(P[:, 2] - F(pc[2])) - F(0.012) - F(0.004) * np.sin(((P - pc.astype(F)) @ tdir.astype(F)) * F(120))),
                              pc - 0.1, pc + 0.1), 5)
    return fd


# ---------------------------------------------------------------------------------------------- the camo net
def ring_env(P):
    """A smooth envelope over the ring of bags (for draping the net)."""
    r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
    top = F(LEDGE_TOP)
    q0 = np.abs(r - F(RING_R)) - F(BAG[1] + 0.006)
    q1 = np.abs(P[:, 2] - F((top + TOP_Z) / 2)) - F((top - TOP_Z) / 2)
    rr = F(0.05)
    a, b = q0 + rr, q1 + rr
    ring = np.sqrt(np.maximum(a, 0) ** 2 + np.maximum(b, 0) ** 2) + np.minimum(np.maximum(a, b), 0) - rr
    roof = P[:, 2] - F(TOP_Z + 0.004)
    return smin(ring, roof, 0.06)


def _net_keep(P):
    r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
    a = np.arctan2(P[:, 1], P[:, 0])
    m = (NET_A[0] + NET_A[1]) / 2
    half = (NET_A[1] - NET_A[0]) / 2
    da = np.abs(np.angle(np.exp(1j * (a.astype(np.float64) - m)))).astype(F)
    rag = F(0.1) * NOISE(P * F(5)) + F(0.05) * np.sin(r * F(20))
    reach = F(RING_R + BAG[1] + 0.2) + F(0.06) * np.sin(a * F(9)) + rag * F(0.5)
    inside = F(RING_R - BAG[1] + 0.02) - r                         # it stops just over the inner edge of the top
    return np.maximum(np.maximum(da - F(half) - rag, r - reach), inside)


def net_field():
    """A scrap of camo net with jute garnish (the ghillie material: 0 moss and olive, 5 tan, 6 brown) thrown over the
    ring's back, spilling down its outer face onto the roof; garnish strips in tufts on it."""
    fd = Field("Net")
    lo, hi = (-0.92, 0.3, TOP_Z - 0.02), (0.78, 1.25, LEDGE_TOP + 0.08)
    lumps = lambda P: F(0.006) * NOISE(P * F(11)) + F(0.003) * NOISE(P * F(35))
    fd.add(Inter(Func(lambda P: np.abs(ring_env(P) - F(0.012)) - F(0.005), lo, hi, disp=lumps, disp_amp=0.008),
                 Func(_net_keep, lo, hi), 0.01), 0.0)
    rs = np.random.RandomState(77)
    env = Func(lambda P: ring_env(P) - F(0.02), lo, hi)
    from caveman import ray_hit
    tufts = 0
    tries = 0
    while tufts < 16 and tries < 400:
        tries += 1
        a = rs.uniform(*NET_A)
        r = rs.uniform(RING_R - 0.05, RING_R + BAG[1] + 0.16)
        o = v3((r * math.cos(a), r * math.sin(a), LEDGE_TOP + 0.3))
        if _net_keep(np.array([o * v3((1, 1, 0)) + v3((0, 0, TOP_Z + 0.2))], F))[0] > -0.03:
            continue
        h, ok = ray_hit(env, [o], [v3((0, 0, -1))], tmax=0.8, step=0.004)
        if not ok[0]:
            continue
        lab = (0, 5, 6, 0)[tufts % 4]
        for j in range(3):
            d = norm(v3((rs.uniform(-1, 1), rs.uniform(-1, 1), rs.uniform(-0.2, 0.4))))
            L = rs.uniform(0.05, 0.09)
            p0 = h[0] + v3((0, 0, 0.004))
            pts = [p0, p0 + d * L * 0.5 + v3((0, 0, 0.01)), p0 + d * L + v3((0, 0, -0.004))]
            fd.add(Lock(pts, [0.016, 0.014, 0.008], [0.004] * 3, [v3((0, 0, 1))] * 3, k=0.004), 0.004, lab)
        tufts += 1
    return fd


# ---------------------------------------------------------------------------------------------- the gear in the nest
def _gear_spot(deg, r=GEAR_R):
    a = math.radians(deg)
    return v3((r * math.cos(a), r * math.sin(a), TOP_Z)), a


def kit_field():
    """The gear (modern kit: olive paint 8, black 5, gunmetal 9, brass 14, coyote 13, rubber 12): a .50 ammo can with a
    laser rangefinder on it, a canteen, a rugged laptop on its hard case, a spotting scope on a short tripod, spent
    brass on the gravel, a mushroom vent on the roof outside the ring."""
    fd = Field("Kit")
    # the ammo can (lying along the ring, its lid's latch outward), the rangefinder on it
    c, a = _gear_spot(205.0)
    tg = v3((-math.sin(a), math.cos(a), 0.0))
    R = np.stack([tg, np.cross(v3((0, 0, 1)), tg), v3((0, 0, 1))], axis=1)
    can = c + v3((0, 0, 0.095))
    fd.add(RoundBox(can, (0.15, 0.072, 0.095), 0.012, R=R), 0.0, 8)
    fd.add(RoundBox(can + v3((0, 0, 0.09)), (0.153, 0.075, 0.012), 0.008, R=R), 0.003, 8)         # the lid
    fd.add(RoundBox(can + R @ v3((0, 0.072, 0.04)), (0.045, 0.012, 0.03), 0.006, R=R), 0.003, 8)  # the latch
    fd.add(Chain([can + R @ v3((-0.05, 0.0, 0.103)), can + R @ v3((-0.04, 0.0, 0.118)), can + R @ v3((0.04, 0.0, 0.118)),
                  can + R @ v3((0.05, 0.0, 0.103))], [0.006] * 4, k=0.003), 0.003, 5)          # the handle
    rf = can + v3((0, 0, 0.13)) + R @ v3((0.06, -0.02, 0.0))
    Rr = R @ euler(0, 0, 0.5)
    fd.add(RoundBox(rf, (0.075, 0.035, 0.028), 0.012, R=Rr), 0.003, 13)
    for sv in (-1, 1):
        fd.add(Cylinder(rf + Rr @ v3((0.075, sv * 0.017, 0.004)), 0.015, 0.012, rr=0.003, R=Rr @ rot_from_axes(z_axis=(1, 0, 0))), 0.003, 5)
    # the canteen, standing
    c, a = _gear_spot(232.0, GEAR_R + 0.02)
    fd.add(RoundCone(c + v3((0, 0, 0.03)), c + v3((0, 0, 0.17)), 0.045, 0.042), 0.02, 8)
    fd.add(Cylinder(c + v3((0, 0, 0.215)), 0.022, 0.03, rr=0.006), 0.006, 5)
    fd.add(Torus(c + v3((0, 0, 0.19)), 0.03, 0.006), 0.004, 5)
    # the laptop on its hard case: the lid open toward him (the screen: its own glowing mesh)
    c, a = _gear_spot(330.0)
    inward = v3((-math.cos(a), -math.sin(a), 0.0))
    R = rot_from_axes(y_axis=inward, z_axis=(0, 0, 1))
    case = c + v3((0, 0, 0.06))
    fd.add(RoundBox(case, (0.19, 0.13, 0.06), 0.015, R=R), 0.0, 5)
    for sx in (-1, 1):
        fd.add(RoundBox(case + R @ v3((sx * 0.12, 0.13, 0.0)), (0.03, 0.012, 0.02), 0.005, R=R), 0.003, 5)   # latches
    base = case + v3((0, 0, 0.075))
    fd.add(RoundBox(base + R @ v3((0, 0.02, 0.0)), (0.15, 0.1, 0.012), 0.008, R=R), 0.003, 13)
    hinge = base + R @ v3((0, -0.08, 0.012))
    Rl = R @ euler(-0.38, 0, 0)
    fd.add(RoundBox(hinge + Rl @ v3((0, -0.006, 0.1)), (0.15, 0.01, 0.1), 0.008, R=Rl), 0.003, 13)
    fd.add(RoundBox(hinge + Rl @ v3((0, 0.004, 0.1)), (0.125, 0.004, 0.08), 0.002, R=Rl), 0.001, 5)
    # the spotting scope on a short tripod, pointing out over the ring
    c, a = _gear_spot(28.0, GEAR_R - 0.02)
    out = v3((math.cos(a), math.sin(a), 0.0))
    side = np.cross(v3((0, 0, 1)), out)
    head = c + v3((0, 0, 0.28))
    for k in range(3):
        b = 2 * math.pi * k / 3 + 0.4
        foot = c + (out * math.cos(b) + side * math.sin(b)) * 0.12
        fd.add(RoundCone(head - v3((0, 0, 0.02)), foot + v3((0, 0, 0.008)), 0.008, 0.006), 0.003, 5)
        fd.add(Sphere(foot + v3((0, 0, 0.008)), 0.01), 0.002, 12)
    fd.add(RoundBox(head, (0.025, 0.025, 0.018), 0.006), 0.004, 9)
    ax = norm(out * math.cos(0.18) + v3((0, 0, math.sin(0.18))))
    s0 = head + v3((0, 0, 0.045)) - ax * 0.1
    fd.add(RoundCone(s0, s0 + ax * 0.2, 0.032, 0.038), 0.006, 8)
    fd.add(RoundCone(s0 + ax * 0.2, s0 + ax * 0.26, 0.042, 0.042), 0.004, 5)
    fd.add(RoundCone(s0 - ax * 0.07, s0, 0.02, 0.03), 0.004, 5)                       # the eyepiece, angled
    fd.add(Cylinder(s0 + ax * 0.262, 0.033, 0.006, rr=0.002, R=rot_from_axes(z_axis=ax)), 0.0, 11)
    # spent brass on the gravel
    rs = np.random.RandomState(91)
    for k in range(7):
        d = rs.uniform(-60.0, 60.0) - 90.0 + rs.uniform(-10, 10)
        r = rs.uniform(0.5, 0.7)
        p, aa = _gear_spot(d, r)
        ang = rs.uniform(0, 2 * math.pi)
        dv = v3((math.cos(ang), math.sin(ang), 0.0))
        p = p + v3((0, 0, 0.012))
        fd.add(RoundCone(p - dv * 0.05, p + dv * 0.04, 0.011, 0.011), 0.0, 14)
        fd.add(RoundCone(p + dv * 0.04, p + dv * 0.07, 0.0105, 0.007), 0.003, 14)
    # the mushroom vent on the roof outside the ring
    vc = v3((math.cos(math.radians(-35.0)) * 0.99, math.sin(math.radians(-35.0)) * 0.99, TOP_Z))
    fd.add(Cylinder(vc + v3((0, 0, 0.11)), 0.035, 0.22, rr=0.006), 0.0, 9)
    fd.add(Ellipsoid(vc + v3((0, 0, 0.235)), (0.075, 0.075, 0.035)), 0.01, 9)
    fd.add(Cylinder(vc + v3((0, 0, 0.012)), 0.06, 0.024, rr=0.008), 0.006, 9)
    return fd


def screen_field():
    """The laptop's screen (its own faintly glowing mesh)."""
    fd = Field("Screen")
    c, a = _gear_spot(330.0)
    inward = v3((-math.cos(a), -math.sin(a), 0.0))
    R = rot_from_axes(y_axis=inward, z_axis=(0, 0, 1))
    base = c + v3((0, 0, 0.06)) + v3((0, 0, 0.075))
    hinge = base + R @ v3((0, -0.08, 0.012))
    Rl = R @ euler(-0.38, 0, 0)
    fd.add(RoundBox(hinge + Rl @ v3((0, 0.009, 0.1)), (0.118, 0.002, 0.074), 0.001, R=Rl), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- grass, dandelions
def _blocked(c, pad=0.0):
    return math.hypot(c[0], c[1]) < PLINTH_R + 0.06 + pad


def grass_geometry(seed=89):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 26 and tries < 8000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.07, GROUND_R - 0.07)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.0):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.13 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        nb = rs.randint(8, 13)
        big = 0.7 + 0.5 * rs.rand()
        for b in range(nb):
            ang = rs.uniform(0, 2 * math.pi)
            off = v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0, 0.05)
            root = c + off
            root[2] = ground_height(root[0], root[1]) - 0.01
            outv = v3((math.cos(ang), math.sin(ang), 0))
            d = norm(outv * rs.uniform(0.15, 0.45) + v3((0, 0, 1)))
            L = rs.uniform(0.1, 0.2) * big
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.03, 0.042), outv * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=4,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=97):
    """Dandelions: a few yellow heads (swatch 1) on short stems in the lawn."""
    rs = np.random.RandomState(seed)
    out = []
    spots, tries = [], 0
    while len(spots) < 6 and tries < 3000:
        tries += 1
        a = rs.uniform(0, 2 * math.pi)
        r = rs.uniform(PLINTH_R + 0.09, GROUND_R - 0.06)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.02) or any(np.linalg.norm(c[:2] - s[:2]) < 0.25 for s in spots):
            continue
        spots.append(c)
    for c in spots:
        for k in range(rs.randint(1, 3)):
            ang = rs.uniform(0, 2 * math.pi)
            root = c + v3((math.cos(ang), math.sin(ang), 0)) * rs.uniform(0.0, 0.04)
            root[2] = ground_height(root[0], root[1]) - 0.01
            h = rs.uniform(0.07, 0.13)
            d = norm(v3((math.cos(ang) * 0.2, math.sin(ang) * 0.2, 1.0)))
            sv, sf, _ = _b.blade_mesh(root, d, h, 0.01, v3((math.cos(ang), math.sin(ang), 0)) * 0.1, segs=2)
            out.append((sv, sf, 0, 1))
            tilt = norm(v3((rs.uniform(-0.3, 0.3), rs.uniform(-0.3, 0.3), 1.0)))
            _bloom(out, root + d * h, tilt, 0.026, 1)
    return out


def fields():
    return [("Ground", ground_field(), 0.008), ("Plinth", plinth_field(), 0.0045), ("Roof", roof_field(), 0.0035),
            ("Sandbags", sandbags_field(), 0.0032), ("Net", net_field(), 0.003), ("Kit", kit_field(), 0.0018),
            ("Screen", screen_field(), 0.0015)]


REGION_PARTS = ("Plinth", "Roof", "Sandbags", "Net", "Kit")
LOW_TARGETS = {"Ground": 1300, "Plinth": 1500, "Roof": 900, "Sandbags": 4400, "Net": 1400, "Kit": 2600, "Screen": 30}
MAT_OVERRIDES = {"Ground": ("ground", {"name": "HQ_LawnGround"}),
                 "Plinth": ("concrete_roof", {"name": "HQ_SnipConcrete"}),
                 "Roof": ("concrete_roof", {"name": "HQ_SnipConcrete"}),
                 "Sandbags": ("sacking", {"name": "HQ_SnipSacking"}),
                 "Net": ("ghillie", {"name": "HQ_Ghillie"}),
                 "Kit": ("modern_kit", {"name": "HQ_SnipGear", "base": (0.3, 0.31, 0.33)})}
GLOW = {"Screen": ((0.45, 0.85, 0.72), 0.9, 0.4)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    r = math.hypot(c.x, c.y)
    on_ground = PLINTH_R + 0.03 < r < GROUND_R + 0.05 and abs(c.z - ground_height(c.x, c.y)) < 0.035
    return n.z > 0.55 and on_ground
