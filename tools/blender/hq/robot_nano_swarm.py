"""Nano Swarm, HQ: a seething ball of Nano Mites crawling along the ground, clumped round a glowing cyan core. Forty-odd
mites (each a white armoured bead with a gunmetal belly, a hazard-orange stripe across its back, a red glowing eye at
its front and stubby gunmetal legs clinging to its neighbours) cling to the core in a rough ball, heading every which
way, the core glowing cyan through the gaps between them. When it is destroyed three Nano Mites burst out of it
(enemies.json "on_death"). Walk (30 frames): the ball rolls along the ground at its own speed (one turn a loop, its
bottom never sliding), the mites seething over it: twelve clumps of mites, each on its own bone, rock and heave in and
out of step with each other while the core pulses and spins the other way.
Faces -Y, Z up; model_scale 0.9.
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, Func, rot_from_axes, v3, norm, F
import robot_anim as ra
from mathutils import Vector, Quaternion
from rig import Poser

ROOT_NAME = "NanoSwarm"
GLB_NAME = "nano_swarm"
TEX_PREFIX = "nano_swarm"
WALK_FRAMES = 30
R_ROLL = 0.44              # the ball's rolling radius: it rolls 2 * pi * R_ROLL per loop of WALK_FRAMES
                           # walk_speed = 2 * pi * 0.44 * 0.9 * 24 / 30 = 1.99

ORANGE = (1.0, 0.45, 0.1)
SEAM = (0.2, 0.2, 0.22)
DARK = (0.22, 0.23, 0.26)
RED_GLOW = (1.0, 0.16, 0.08)
CYAN = (0.3, 0.88, 1.0)

BC = v3((0, 0, R_ROLL))                    # the ball's centre
CORE_R = 0.27
N_MITES = 46
RHO = 0.36                                 # the mites' centres lie about this far from the centre


def _icosa():
    p = (1 + 5 ** 0.5) / 2
    vs = []
    for a in (-1, 1):
        for b in (-p, p):
            vs += [(0, a, b), (a, b, 0), (b, 0, a)]
    return [norm(v) for v in vs]


CLUMP_DIRS = _icosa()                      # twelve clumps, round the twelve corners of an icosahedron


def _mites():
    """The mites: (centre, up (out from the core), forward (its eye's way), size, clump)."""
    rng = np.random.default_rng(7)
    out = []
    ga = math.pi * (3 - 5 ** 0.5)
    for i in range(N_MITES):
        z = 1 - 2 * (i + 0.5) / N_MITES
        r = math.sqrt(1 - z * z)
        th = ga * i + 0.4
        u = norm(v3((r * math.cos(th), r * math.sin(th), z)) + rng.normal(0, 0.06, 3))
        s = float(rng.uniform(0.9, 1.15))
        c = BC + u * (RHO + float(rng.uniform(-0.015, 0.02)) + (s - 1.0) * 0.04)
        t0 = norm(np.cross(u, v3((0, 0, 1))) if abs(u[2]) < 0.95 else np.cross(u, v3((1, 0, 0))))
        a = float(rng.uniform(0, 2 * math.pi))
        fwd = norm(t0 * math.cos(a) + np.cross(u, t0) * math.sin(a))
        k = int(np.argmax([float(u @ d) for d in CLUMP_DIRS]))
        out.append((c, u, fwd, s, k))
    return out


MITES = _mites()
BEAD = (0.075, 0.094, 0.062)               # a mite's half-sizes (side, length, height) at size 1

BONES = [("root", tuple(BC), tuple(BC + v3((0, 0, 0.15))), None),
         ("core", tuple(BC), tuple(BC + v3((0, -0.15, 0))), "root")]
for _k, _d in enumerate(CLUMP_DIRS):
    BONES.append(("clump%d" % _k, tuple(BC + _d * 0.1), tuple(BC + _d * 0.3), "root"))

MATS = {
    "armor": ("armor", dict(name="RB_SwarmArmor", labels=[(1, ORANGE, 0.35), (2, SEAM, 0.6), (3, DARK, 0.42)], seams=[2], scale=0.5)),
    "frame": ("gunmetal", dict(name="RB_NSwarmFrame", base=(0.2, 0.21, 0.25), scale=0.5)),
    "glow": ("glow", dict(name="RB_NSwarmGlow", col=CYAN)),
}
GLOW = {"Core": (CYAN, 1.4, 0.6)}
LOW_TARGETS = {"Core": 260, "Lattice": 360}
for _k in range(len(CLUMP_DIRS)):
    GLOW["Eyes%d" % _k] = (RED_GLOW, 1.6, 0.5)
    LOW_TARGETS["Clump%d" % _k] = 440
    LOW_TARGETS["Eyes%d" % _k] = 70


def _frame(u, fwd):
    """A mite's axes: x to its side, y backward (its eye looks along -y, as the robots do), z up (out of the ball)."""
    return rot_from_axes(z_axis=u, y_axis=-fwd)


def mite(f, c, u, fwd, s):
    """One mite on the ball: the bead, its face, stubby legs gripping the ball, painted (white top, orange stripe across
    the back, gunmetal belly and legs)."""
    R = _frame(u, fwd)
    rx, ry, rz = (b * s for b in BEAD)
    f.add(Ellipsoid(c, (rx, ry, rz), R=R), k=0.006)
    f.add(Ellipsoid(c + R @ v3((0, -ry * 0.55, 0.0)), (rx * 0.78, ry * 0.5, rz * 0.82), R=R), k=0.012)
    f.sub(Sphere(c + R @ v3((0, -ry * 1.02, rz * 0.12)), rx * 0.42), k=0.004)                    # the eye's socket
    for side in (-1, 1):                                                     # a stubby leg each side, splayed into the gaps
        for dy in (-0.05,):
            a = c + R @ v3((side * rx * 0.7, dy * ry, -rz * 0.25))
            b = c + R @ v3((side * rx * 1.45, (dy - 0.15) * ry * 1.2, -rz * 1.1))
            f.add(RoundCone(a, b, 0.017 * s, 0.011 * s), k=0.005, label=3)
    cf = c.astype(F)
    Rf = R.astype(F)
    lo, hi = c - 0.2, c + 0.2
    near = lambda P, cf=cf: np.sqrt(((P - cf) ** 2).sum(1)) - F(ry * 1.25)          # (only this mite, not its neighbours)
    loc = lambda P, cf=cf, Rf=Rf: (P - cf) @ Rf
    f.paint(Func(lambda P: np.maximum(loc(P)[:, 2] + F(rz * 0.3), near(P)), lo, hi), 3)
    f.paint(Func(lambda P: np.maximum(np.maximum(np.abs(loc(P)[:, 1] - F(ry * 0.3)) - F(ry * 0.2),
                                                 F(-rz * 0.2) - loc(P)[:, 2]), near(P)), lo, hi), 1)
    f.paint(Func(lambda P: np.maximum(np.maximum(np.abs(loc(P)[:, 0]) - F(0.0025), F(rz * 0.2) - loc(P)[:, 2]), near(P)), lo, hi), 2)


def eye(f, c, u, fwd, s):
    R = _frame(u, fwd)
    rx, ry, rz = (b * s for b in BEAD)
    f.add(Ellipsoid(c + R @ v3((0, -ry * 0.98, rz * 0.12)), (rx * 0.38, ry * 0.2, rx * 0.36), R=R))


def parts(fine=False):
    vx = 0.0034 if fine else 0.0062
    out = []
    f = Field("Core")
    f.add(Sphere(BC, CORE_R))
    out.append(("Core", f, vx, "core", "glow"))
    # a gunmetal cage round the core (three rings), so the gaps show machinery as well as light
    f = Field("Lattice")
    from sdf import Torus
    for ax in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
        f.add(Torus(BC, CORE_R + 0.01, 0.018, R=rot_from_axes(z_axis=ax)), k=0.01)
    out.append(("Lattice", f, vx, "core", "frame"))
    for k in range(len(CLUMP_DIRS)):
        ms = [m for m in MITES if m[4] == k]
        if not ms:
            continue
        f = Field("Clump%d" % k)
        for c, u, fwd, s, _ in ms:
            mite(f, c, u, fwd, s)
        out.append(("Clump%d" % k, f, vx, "clump%d" % k, "armor"))
        f = Field("Eyes%d" % k)
        for c, u, fwd, s, _ in ms:
            eye(f, c, u, fwd, s)
        out.append(("Eyes%d" % k, f, vx * 0.8, "clump%d" % k, "glow"))
    return out


# ------------------------------------------------------------------------------------------------ clips
V = lambda *a: Vector(a)


def walk(arm):
    """The roll: one whole turn a loop about the ball's centre (forward, -Y), so its bottom keeps pace with the ground;
    each clump rocks about its own axis and heaves in and out (whole numbers of wobbles a loop, out of step with the
    others), so the mites seem to crawl over each other; the core spins the other way and pulses."""
    P = Poser(arm)
    act = ra.new_action(arm, "Walk")
    rng = np.random.default_rng(3)
    wob = []
    for k, d in enumerate(CLUMP_DIRS):
        ax = norm(rng.normal(0, 1, 3))
        ax = norm(ax - d * float(ax @ d))                 # a rocking axis across the clump's direction
        wob.append((Vector(ax.tolist()), int(rng.integers(1, 3)), float(rng.uniform(0, 2 * math.pi)), int(rng.integers(2, 4)),
                    float(rng.uniform(0, 2 * math.pi))))
    for f in range(WALK_FRAMES + 1):
        t = f / WALK_FRAMES
        w = 2 * math.pi * t
        root_rot = Quaternion(V(1, 0, 0), w)
        root_off = V(0.0, 0.0, 0.008 * abs(math.sin(3 * w)))
        aims = {"core": ("rot", Quaternion(V(0, 0, 1), -2 * w) @ Quaternion(V(1, 0, 0), -w))}
        sc = {"core": 1.0 + 0.05 * math.sin(4 * w)}
        for k in range(len(CLUMP_DIRS)):
            ax, n1, p1, n2, p2 = wob[k]
            ang = 0.16 * math.sin(n1 * w + p1)
            aims["clump%d" % k] = (lambda q: (lambda P, base: ("rot", q)))(Quaternion(ax, ang))
            sc["clump%d" % k] = 1.0 + 0.05 * math.sin(n2 * w + p2)
        ch, _ = P.solve(aims, root_off=root_off, root_rot=root_rot, scales=sc)
        P.key(ch, f)
    ra.finish_action(arm, act, WALK_FRAMES, True)


def clips(arm):
    walk(arm)
