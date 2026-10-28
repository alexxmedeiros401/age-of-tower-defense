"""HQ Data Center map props, sculpted as distance fields like decor_props, decor_bronze, ... decor_modern and
decor_digital (same conventions: every builder returns its parts [(part name, Field, voxel, material key)], built at
the origin, Z up, ground at z = 0, a landmark's front toward -Y, a vehicle's nose toward +X; KITS lists each theme's
props and their game-mesh triangle budgets; decor_build.materials resolves the keys).

The Data Center is the robots' own: their machines are white with hazard orange, gunmetal frames, cyan energy and red
eyes, their halls graphite and steel. The Resistance fighting its way in is charcoal and gunmetal-black with one accent,
ember amber-gold (paint, light strips), and builds from salvage: white robot plates taken from the enemy, dented,
strapped and sprayed with the Resistance's amber chevron so they never read as the enemy's.
Coolant Vaults (cooling): frosted pipe runs with valves, coolant canisters, ice chunks, pumps, hazard barriers, steel
crates, cable bundles; landmarks: a giant frozen coolant tower, a heat-exchanger wall, a robot frozen mid-stride in the
ice, a pump station with its gauges; for the no-build zones great ice formations and ice-crusted coolant tanks
(venting), and huge chiller units with their fans.
Server Hall (server): server racks blinking cyan and red, cable trays, rack carts, floor fans, parked maintenance
drones, toppled racks; landmarks: a cathedral-like mainframe wall, a cooling-duct column, a robot workstation, the
Resistance's breach (a blasted wall sprayed amber); for the no-build zones rows of racks and a mainframe / power unit.
The Core (core): energy conduits, data spires, cable runs, debris, wrecked robot parts, scorch marks, glowing data
crystals; landmarks: a giant data spire, a towering cable-bundle column, a wrecked Resistance tank, a fallen robot
giant; for the no-build zones energy pillars ringed with light (arcs crackle on them) and wrecks: a wrecked robot and a
burnt-out Resistance vehicle.
The Resistance camp at the end of every Data Center road (a fortified forward camp built from salvage inside the data
center: barricades of salvaged robot plates and sandbags, a gate of welded plates under the amber banner, a converted
container as the command post with its lit doorway, a field generator with amber lights, a radio mast, crates, burning
barrels) is its own kit ("camp_city", datacenter_city.glb).
"""
import math
import numpy as np
from sdf import Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Chain, Plane, Func, rot_from_axes, v3, NOISE, euler
import decor_props as DP
from decor_props import vx, wob, convex, rock, crystal
from decor_bronze import fine, unit, ground_cut, cut_above, place, place_parts, convex_w
from decor_iron import Rz, R_xz
from decor_gunpowder import leaf, mirror, sandbag, flag
from decor_modern import box, wheel, drum, jerrycan, stencil, ammo_crate, ammo_can, pallet, sandbag_run, flood_head, lattice_mast, pole, RX, RY
from decor_digital import seg, strip, screen, hexagon, ring, railing_line, finish_glows, G, _frosted_pipe

F32 = np.float32
Z = v3((0, 0, 1))


# ------------------------------------------------------------------------------------------------ helpers
def chevron(f, c, nrm, w, h, t=0.05, label=5, up=(0, 0, 1), n=1):
    """Paint the Resistance's mark on a face at c (outward normal nrm): `n` bold chevrons pointing up, w wide, h high
    (label: the amber spray paint of the salvage / armour materials)."""
    nn = unit(nrm)
    upv = unit(v3(up) - nn * float(np.dot(v3(up), nn)))
    s = np.cross(upv, nn)
    c = v3(c)
    for i in range(n):
        o = c - upv * (i * t * 2.4)
        for sg in (-1, 1):
            d = unit(s * sg * (w / 2) - upv * h)
            mid = o + d * (math.hypot(w / 2, h) / 2)
            R = np.stack([d, np.cross(nn, d), nn], axis=1)
            f.paint(RoundBox(mid, (math.hypot(w / 2, h) / 2 + t * 0.4, t / 2, 0.06), 0.0, R=R), label)


def slash(f, a, b, t, label=5, depth=0.06):
    """Paint a sprayed slash from a to b (on a face): a band t wide."""
    a, b = v3(a), v3(b)
    d = b - a
    L = float(np.linalg.norm(d))
    x = d / max(L, 1e-9)
    y = unit(np.cross(Z if abs(x[2]) < 0.9 else v3((1, 0, 0)), x))
    f.paint(RoundBox((a + b) / 2, (L / 2, t / 2, depth), 0.0, R=np.stack([x, y, np.cross(x, y)], axis=1)), label)


def plate(f, c, n, up, w, h, t=0.022, bow=0.05, label=0):
    """A salvaged robot armour plate (field f) at c facing n: w wide, h high, t thick, bowed out by `bow` (a
    rounded shield-like panel with chamfered corners)."""
    n = unit(n)
    upv = unit(v3(up) - n * float(np.dot(v3(up), n)))
    s = np.cross(upv, n)
    R = np.stack([s, upv, n], axis=1)
    Rf = R.astype(F32)
    cf = v3(c).astype(F32)
    hw, hh = F32(w / 2), F32(h / 2)
    k = F32(bow / max(w * w / 4, 1e-6))

    def fn(P):
        Q = (P - cf) @ Rf
        x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
        zc = z + k * (x * x) * F32(1.0) - F32(bow)            # bowed: the middle stands out by `bow`
        dz = np.abs(zc) - F32(t / 2)
        dx = np.abs(x) - hw
        dy = np.abs(y) - hh
        dc = (np.abs(x) + np.abs(y)) - (hw + hh - F32(min(w, h) * 0.22))      # chamfered corners
        d2 = np.maximum(np.maximum(dx, dy), dc * F32(0.7071))
        return (np.maximum(d2, dz)).astype(F32)
    e = max(w, h) / 2 + bow + t + 0.05
    f.add(Func(fn, v3(c) - e, v3(c) + e), k=0.0, label=label)
    return R


def strap(f, a, b, w=0.04, t=0.008, nrm=(0, 0, 1), label=7):
    """A flat strap (field f) from a to b lying on a face of normal nrm."""
    a, b = v3(a), v3(b)
    d = b - a
    L = float(np.linalg.norm(d))
    x = d / max(L, 1e-9)
    n = unit(v3(nrm) - x * float(np.dot(v3(nrm), x)))
    y = np.cross(n, x)
    f.add(RoundBox((a + b) / 2, (L / 2, w / 2, t), t * 0.8, R=np.stack([x, y, n], axis=1)), k=0.0, label=label)


def gauge(f, gl, c, nrm, r=0.06, label=7, glow=True):
    """A round dial gauge at c facing nrm: its bezel (field f) and lit face (gl), a needle painted dark."""
    n = unit(nrm)
    R = rot_from_axes(z_axis=n)
    c = v3(c)
    f.add(Cylinder(c - n * 0.015, r + 0.012, 0.03, rr=0.008, R=R), k=0.0, label=label)
    if glow:
        gl.add(Cylinder(c + n * 0.001, r, 0.006, rr=0.002, R=R), k=0.0)


def valve_wheel(f, c, axis, r=0.08, label=8):
    """A handwheel on its stem (field f): the rim, three spokes, the hub."""
    a = unit(axis)
    R = rot_from_axes(z_axis=a)
    c = v3(c)
    f.add(Torus(c, r, r * 0.13, R=R), k=0.0, label=label)
    for k in range(3):
        t = 2 * math.pi * k / 3
        f.add(RoundCone(c, c + R @ v3((math.cos(t) * r, math.sin(t) * r, 0)), r * 0.08, r * 0.08), k=0.0, label=label)
    f.add(Cylinder(c, r * 0.2, r * 0.3, rr=r * 0.05, R=R), k=0.0, label=label)


def flange(f, c, axis, r, label=6):
    """A bolted pipe flange (field f) round a pipe of radius r."""
    a = unit(axis)
    R = rot_from_axes(z_axis=a)
    c = v3(c)
    f.add(Cylinder(c, r * 1.55, r * 0.5, rr=r * 0.12, R=R), k=0.0, label=label)
    for k in range(6):
        t = 2 * math.pi * k / 6
        f.add(Cylinder(c + R @ v3((math.cos(t) * r * 1.3, math.sin(t) * r * 1.3, 0)), r * 0.13, r * 0.75, R=R), k=0.0, label=label)


def icicles(f, a, b, n, L, seed, r=0.02):
    """A fringe of icicles (field f) hanging under the edge from a to b."""
    rng = np.random.default_rng(seed)
    a, b = v3(a), v3(b)
    for i in range(n):
        q = a + (b - a) * ((i + rng.uniform(0.2, 0.8)) / n)
        l = L * rng.uniform(0.4, 1.0)
        f.add(RoundCone(q, q - Z * l, r * rng.uniform(0.8, 1.2), 0.003), k=0.01)


def frost_crust(f, c, radii, seed, amp=0.03):
    """A lumpy crust of frost or ice (field f): an ellipsoid sunk in the ground, wobbled."""
    f.add(Ellipsoid(v3(c), radii, **wob(5.0, amp, seed)), k=0.03)


def ice_shards(f, c, n, h, r, seed, spread=0.4, tilt=0.45):
    """A cluster of n ice crystals (field f) springing from round c, leaning out, up to h tall."""
    rng = np.random.default_rng(seed)
    c = v3(c)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.4, 0.4)
        d = v3((math.cos(a), math.sin(a), 0))
        base = c + d * rng.uniform(0.0, spread) - Z * 0.05
        ax = unit(d * rng.uniform(0.1, tilt) * (1 if i else 0.2) + Z)
        hh = h * rng.uniform(0.45, 1.0) * (1.0 if i else 1.15)
        f.add(crystal(base, ax, r * rng.uniform(0.6, 1.1) * (hh / h) ** 0.5, hh, tip=r * 0.9, twist=rng.uniform(0, 1)), k=0.01)


def cable_bundle(f, pts, n=5, r=0.025, seed=0, spread=None, labels=(0, 5, 0, 9, 8, 0)):
    """A loose bundle of n cables (field f) following the polyline pts, twisting round one another."""
    rng = np.random.default_rng(seed)
    pts = [v3(p) for p in pts]
    spread = r * 1.6 if spread is None else spread
    for i in range(n):
        ph = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        q = []
        for j, p in enumerate(pts):
            t = j / max(1, len(pts) - 1)
            if j == 0:
                d = unit(pts[1] - pts[0])
            elif j == len(pts) - 1:
                d = unit(pts[-1] - pts[-2])
            else:
                d = unit(pts[j + 1] - pts[j - 1])
            u = unit(np.cross(d, Z)) if abs(d[2]) < 0.95 else v3((1, 0, 0))
            w = np.cross(d, u)
            a = ph + t * 3.0
            q.append(p + (u * math.cos(a) + w * math.sin(a)) * spread * rng.uniform(0.7, 1.1))
        f.add(Chain(q, [r * rng.uniform(0.8, 1.15)] * len(q), k=0.02), k=0.0, label=labels[i % len(labels)])


def hazard_band(f, c, axis, r, h, label=8):
    """Paint a hazard band (label 8: yellow and black stripes in the tech materials) round a cylinder."""
    f.paint(Cylinder(v3(c), r + 0.05, h, R=rot_from_axes(z_axis=axis)), label)


# ------------------------------------------------------------------------------------------------ the robots
def _limb_dir(a, b, sx):
    """A limb's direction from its joint: swung forward (toward -Y) by pitch a, out to the side sx by b."""
    return unit(v3((sx * math.sin(b), -math.sin(a) * math.cos(b), -math.cos(a) * math.cos(b))))


def robot_figure(out, o=(0, 0, 0), R=None, s=1.0, pose=None, prefix="Bot", eye="glow_red", missing=(), torn=False, seed=0,
                 plates="robot_white", frame="gunmetal"):
    """One of the robots' white soldiers (about 1.9 m tall at s = 1, front toward -Y): gunmetal frame and joints under
    white armour plates with hazard-orange stripes, broad pauldrons, a rounded helmet with a red visor slit, a red core
    in the chest. pose: {lean, twist, head (yaw, pitch), legs {+1/-1: (pitch, out, knee)}, arms {+1/-1: (pitch, out,
    elbow)}, z: the pelvis' height}; the figure is built in its own frame and moved to o turned by R (it may lie on the
    ground: build the pose standing). missing: limbs torn off ("arm+1", "arm-1", "leg+1", "head"); torn: the chest plate
    ripped open on the frame inside. Returns {joint name: world point}."""
    R = np.eye(3) if R is None else np.asarray(R, np.float64)
    o = v3(o)
    pose = pose or {}
    W = lambda p: o + R @ (v3(p) * s)                               # (local, unscaled -> world)
    Wd = lambda d: unit(R @ v3(d))
    pl, fr = Field(prefix + "Plates"), Field(prefix + "Frame")
    gl = Field(prefix + "Eye")
    lean, twist = pose.get("lean", 0.0), pose.get("twist", 0.0)
    pz = pose.get("z", 0.95)
    Pv = v3((0, 0, pz))
    u = unit(v3((0, -math.sin(lean), math.cos(lean))))
    side = unit(Rz(twist) @ v3((1, 0, 0)))
    side = unit(side - u * float(np.dot(side, u)))
    front = np.cross(side, u)
    Rt = np.stack([side, -front, u], axis=1)                       # torso frame (local y = back)
    Rtw = R @ Rt
    N = Pv + u * 0.62
    C = Pv + u * 0.38
    J = {}
    # ---- pelvis, waist, chest
    fr.add(RoundBox(W(Pv), (0.15 * s, 0.1 * s, 0.08 * s), 0.04 * s, R=Rtw), k=0.0)
    pl.add(RoundBox(W(Pv + front * 0.06 - u * 0.02), (0.12 * s, 0.05 * s, 0.07 * s), 0.035 * s, R=Rtw), k=0.02)
    for i in range(3):
        fr.add(Cylinder(W(Pv + u * (0.1 + i * 0.065)), (0.1 - i * 0.004) * s, 0.05 * s, rr=0.015 * s, R=R @ rot_from_axes(z_axis=u)), k=0.01)
    pl.add(RoundBox(W(C + u * 0.07), (0.22 * s, 0.14 * s, 0.17 * s), 0.07 * s, R=Rtw), k=0.02)
    pl.add(RoundBox(W(C + u * 0.04 + front * 0.1), (0.16 * s, 0.05 * s, 0.13 * s), 0.05 * s, R=Rtw), k=0.03)
    pl.paint(RoundBox(W(C + u * 0.2 + front * 0.12), (0.2 * s, 0.1 * s, 0.022 * s), 0.0, R=Rtw), 5)        # hazard-orange band
    pl.add(RoundBox(W(C + u * 0.08 - front * 0.12), (0.17 * s, 0.06 * s, 0.14 * s), 0.05 * s, R=Rtw), k=0.02)   # the back pack
    core = C + u * 0.05 + front * 0.152
    if torn:                                                        # the chest ripped open: ribs and the frame inside
        pl.sub(Ellipsoid(W(core + front * 0.02 + side * 0.03), (0.13 * s, 0.1 * s, 0.13 * s), R=Rtw, **wob(9.0 / s, 0.015 * s, seed)), k=0.01)
        fr.add(RoundBox(W(C + u * 0.05 + front * 0.02), (0.13 * s, 0.06 * s, 0.13 * s), 0.03 * s, R=Rtw), k=0.0)
        for i in range(4):
            q = C + u * (-0.05 + i * 0.065) + front * 0.07
            fr.add(RoundCone(W(q - side * 0.11), W(q + side * 0.11), 0.014 * s, 0.014 * s), k=0.0)
        gl.add(Sphere(W(C + u * 0.05 + front * 0.09), 0.045 * s), k=0.0)
        pl.paint(Sphere(W(core + front * 0.02), 0.17 * s), 9)        # scorched round the tear
    else:
        gl.add(Cylinder(W(core), 0.045 * s, 0.012 * s, rr=0.004 * s, R=R @ rot_from_axes(z_axis=front)), k=0.0)
        pl.sub(Cylinder(W(core), 0.06 * s, 0.03 * s, R=R @ rot_from_axes(z_axis=front)), k=0.004)
        fr.add(Torus(W(core - front * 0.006), 0.06 * s, 0.01 * s, R=R @ rot_from_axes(z_axis=front)), k=0.0)
    # ---- the head
    hy, hp = pose.get("head", (0.0, 0.0))
    fr.add(Cylinder(W(N + u * 0.03), 0.05 * s, 0.1 * s, rr=0.015 * s, R=R @ rot_from_axes(z_axis=u)), k=0.01)
    if "head" not in missing:
        hf = unit(Rz(hy) @ front)
        hf = unit(hf * math.cos(hp) - u * math.sin(hp))
        hu = unit(u - hf * float(np.dot(u, hf)))
        hs = np.cross(hu, hf)
        Rh = R @ np.stack([hs, -hf, hu], axis=1)
        H = N + u * 0.17
        pl.add(Ellipsoid(W(H), (0.115 * s, 0.13 * s, 0.13 * s), R=Rh), k=0.0)
        pl.add(RoundBox(W(H - hu * 0.07 + hf * 0.04), (0.085 * s, 0.07 * s, 0.05 * s), 0.035 * s, R=Rh), k=0.03)     # the jaw
        pl.add(RoundBox(W(H + hu * 0.06 - hf * 0.02), (0.03 * s, 0.11 * s, 0.05 * s), 0.02 * s, R=Rh), k=0.02)      # the crest
        pl.sub(RoundBox(W(H + hf * 0.12 + hu * 0.01), (0.095 * s, 0.05 * s, 0.022 * s), 0.012 * s, R=Rh), k=0.01)  # the visor slit
        gl.add(RoundBox(W(H + hf * 0.095 + hu * 0.01), (0.085 * s, 0.012 * s, 0.014 * s), 0.008 * s, R=Rh), k=0.0)
        for sg in (-1, 1):
            fr.add(Cylinder(W(H + hs * sg * 0.115), 0.035 * s, 0.03 * s, rr=0.008 * s, R=R @ rot_from_axes(z_axis=hs)), k=0.0)
        J["head"] = W(H)
    J["chest"] = W(C + u * 0.07)
    J["core"] = W(core)
    J["pelvis"] = W(Pv)
    # ---- the arms
    for sx in (-1, 1):
        S = N - u * 0.08 + side * sx * 0.27
        J["shoulder%+d" % sx] = W(S)
        pl.add(Ellipsoid(W(S + u * 0.03 + side * sx * 0.03), (0.13 * s, 0.13 * s, 0.1 * s), R=Rtw), k=0.02)
        pl.paint(Ellipsoid(W(S + u * 0.03 + side * sx * 0.1), (0.07 * s, 0.15 * s, 0.11 * s), R=Rtw), 5)
        if "arm%+d" % sx in missing:
            fr.add(Sphere(W(S), 0.06 * s), k=0.01)
            for k in range(3):                                      # torn cables at the socket
                d = unit(side * sx + front * (k - 1) * 0.6 - u * 0.3)
                fr.add(RoundCone(W(S), W(S + d * 0.12), 0.012 * s, 0.006 * s), k=0.0, label=5)
            continue
        a, b, e = pose.get("arms", {}).get(sx, (0.1, 0.12, 0.25))
        # (the arm swings in the torso's frame)
        d1l = _limb_dir(a, b, sx)
        d1 = unit(side * d1l[0] + front * (-d1l[1]) + u * d1l[2])
        d2l = _limb_dir(a + e, b * 0.6, sx)
        d2 = unit(side * d2l[0] + front * (-d2l[1]) + u * d2l[2])
        E = S + d1 * 0.36
        Wr = E + d2 * 0.33
        fr.add(RoundCone(W(S), W(E), 0.05 * s, 0.045 * s), k=0.01)
        pl.add(RoundCone(W(S + d1 * 0.08), W(E - d1 * 0.06), 0.075 * s, 0.062 * s), k=0.01)
        fr.add(Sphere(W(E), 0.055 * s), k=0.01)
        pl.add(RoundCone(W(E + d2 * 0.05), W(Wr - d2 * 0.02), 0.075 * s, 0.06 * s), k=0.01)
        pl.paint(Cylinder(W(Wr - d2 * 0.07), 0.09 * s, 0.035 * s, R=R @ rot_from_axes(z_axis=d2)), 5)
        hd = unit(d2 + front * 0.15)
        Rhd = R @ np.stack([side, unit(np.cross(hd, side)), hd], axis=1)
        fr.add(RoundBox(W(Wr + hd * 0.07), (0.035 * s, 0.05 * s, 0.06 * s), 0.025 * s, R=Rhd), k=0.01)
        for k in range(3):
            fr.add(RoundCone(W(Wr + hd * 0.11 + side * (k - 1) * 0.026), W(Wr + hd * 0.17 + front * 0.03 + side * (k - 1) * 0.026), 0.012 * s, 0.01 * s), k=0.006)
        J["hand%+d" % sx] = W(Wr + hd * 0.1)
        J["elbow%+d" % sx] = W(E)
    # ---- the legs (in the robot's own frame: they don't lean with the torso)
    for sx in (-1, 1):
        Hp = Pv + v3((sx * 0.12, 0, -0.04))
        if "leg%+d" % sx in missing:
            fr.add(Sphere(W(Hp), 0.07 * s), k=0.01)
            for k in range(3):
                d = unit(v3((sx * 0.4, (k - 1) * 0.6, -1)))
                fr.add(RoundCone(W(Hp), W(Hp + d * 0.14), 0.014 * s, 0.006 * s), k=0.0, label=5)
            continue
        a, b, kn = pose.get("legs", {}).get(sx, (0.0, 0.05, 0.05))
        d1 = _limb_dir(a, b, sx)
        d2 = _limb_dir(a - kn, b * 0.5, sx)
        K = Hp + d1 * 0.44
        A = K + d2 * 0.44
        fr.add(Sphere(W(Hp), 0.07 * s), k=0.01)
        fr.add(RoundCone(W(Hp), W(K), 0.06 * s, 0.055 * s), k=0.01)
        pl.add(RoundCone(W(Hp + d1 * 0.06), W(K - d1 * 0.06), 0.1 * s, 0.08 * s), k=0.01)
        fr.add(Sphere(W(K), 0.065 * s), k=0.01)
        kf = unit(v3((0, -1, 0)) - d1 * float(np.dot(v3((0, -1, 0)), d1)) * 0.5)
        pl.add(Ellipsoid(W(K + kf * 0.05), (0.07 * s, 0.06 * s, 0.075 * s)), k=0.01)
        pl.add(RoundCone(W(K + d2 * 0.05), W(A - d2 * 0.07), 0.09 * s, 0.07 * s), k=0.01)
        pl.paint(Cylinder(W(K + d2 * 0.2), 0.11 * s, 0.04 * s, R=R @ rot_from_axes(z_axis=d2)), 5)
        fr.add(Sphere(W(A), 0.05 * s), k=0.01)
        ff = unit(v3((0, -1, 0)) - d2 * float(np.dot(v3((0, -1, 0)), d2)))
        fu = -d2
        Rf = R @ np.stack([np.cross(-ff, fu), -ff, fu], axis=1)
        pl.add(RoundBox(W(A + d2 * 0.05 + ff * 0.06), (0.075 * s, 0.14 * s, 0.045 * s), 0.03 * s, R=Rf), k=0.01, label=7)
        J["knee%+d" % sx] = W(K)
        J["foot%+d" % sx] = W(A + d2 * 0.05 + ff * 0.06)
    vx_ = fine(0.004, 0.008) * max(1.0, s * 0.85)
    out += [(prefix + "Plates", pl, vx_, plates), (prefix + "Frame", fr, vx_, frame), (prefix + "Eye", gl, vx_ * 0.8, eye)]
    return J


# ------------------------------------------------------------------------------------------------ the Resistance's vehicles
def _stadium_track(f, x0, x1, yc, zc, r, w, seed=0, label=0):
    """A tank track's loop as a solid (field f): flat runs between round ends from x0 to x1 at height zc, radius r, w
    wide (half w/2), its tread ribbed."""
    def fn(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        dx = np.maximum(np.maximum(F32(x0) - x, x - F32(x1)), F32(0.0))
        d2 = np.sqrt(dx * dx + (z - F32(zc)) ** 2) - F32(r)
        rib = F32(0.008) * np.maximum(np.cos(x * F32(70.0)), F32(0.0)) * (np.abs(z - F32(zc)) > F32(r * 0.6)).astype(F32)
        return np.maximum(d2 - rib, np.abs(y - F32(yc)) - F32(w / 2)).astype(F32)
    f.add(Func(fn, (x0 - r - 0.05, yc - w, zc - r - 0.05), (x1 + r + 0.05, yc + w, zc + r + 0.05)), k=0.0, label=label)


def res_tank(out, o=(0, 0, 0), yaw=0.0, wrecked=True, seed=0, prefix="Tank"):
    """The Resistance's battle tank (nose toward +X, 2.6 m long): a charcoal hull with a sloped glacis, salvaged white
    robot plates strapped on its flanks and turret front sprayed with the amber chevron, tracks on road wheels, a low
    turret with a long gun, stowage (crates, jerrycans) in the bustle rack; wrecked: the turret knocked askew, the gun
    drooping and bent, the left track thrown off and lying out along the ground before it, the road wheels bare, the
    hull scorched. Returns {name: world point} (the hatch's smoke, the scorch)."""
    o = v3(o)
    R = Rz(yaw)
    hl, sp, tr, wh = Field(prefix + "Hull"), Field(prefix + "Salvage"), Field(prefix + "Tracks"), Field(prefix + "Wheels")
    tu = Field(prefix + "Turret")
    glows = G("glow_ember", prefix=prefix)
    rng = np.random.default_rng(seed)
    # (built at the origin, moved by place_parts at the end)
    hl.add(convex([((0, 0, 0.66), (0, 0, 1)), ((0, 0, 0.2), (0, 0, -1)), ((1.12, 0, 0.4), (1, 0, 0.85)), ((1.2, 0, 0.3), (1, 0, -0.6)),
                   ((-1.15, 0, 0.4), (-1, 0, 0.2)), ((0, 0.5, 0), (0, 1, 0)), ((0, -0.5, 0), (0, -1, 0))], (-1.4, -0.7, 0.1), (1.5, 0.7, 0.8)), k=0.0)
    for sy in (-1, 1):                                              # fenders over the tracks
        box(hl, (0.0, sy * 0.66, 0.6), (1.22, 0.17, 0.025), 0.012)
        hl.add(convex([((1.22, sy * 0.66, 0.6), (1, 0, 0.6)), ((1.0, sy * 0.66, 0.62), (0, 0, 1)), ((1.0, sy * 0.66, 0.57), (0, 0, -1)),
                       ((1.0, sy * 0.83, 0.6), (0, sy, 0)), ((1.0, sy * 0.49, 0.6), (0, -sy, 0)), ((0.9, sy * 0.66, 0.6), (-1, 0, 0))],
                      (0.8, sy * 0.66 - 0.3, 0.4), (1.5, sy * 0.66 + 0.3, 0.8)), k=0.0)
    box(hl, (-1.12, 0.0, 0.48), (0.06, 0.4, 0.12), 0.02, label=7)   # the engine deck's grille at the back
    for sx in (-1, 1):
        hl.add(Cylinder((-1.18, sx * 0.3, 0.42), 0.06, 0.08, rr=0.02, R=RX), k=0.0, label=7)
    # tracks: the right one on, the left thrown when wrecked
    for sy in (-1, 1):
        yc = sy * 0.66
        thrown = wrecked and sy < 0
        xs = np.linspace(-0.9, 0.9, 5)
        if not thrown:
            _stadium_track(tr, -0.92, 0.95, yc, 0.27, 0.26, 0.26, seed)
            for x in xs:
                wh.add(Cylinder((x, yc + sy * 0.13, 0.25), 0.16, 0.025, rr=0.008, R=RY), k=0.0)
                wh.add(Cylinder((x, yc + sy * 0.145, 0.25), 0.05, 0.02, rr=0.006, R=RY), k=0.0, label=6)
        else:
            for x in xs:                                            # bare road wheels, the idler and sprocket
                wh.add(Cylinder((x, yc, 0.2), 0.19, 0.2, rr=0.03, R=RY), k=0.0)
                wh.add(Torus((x, yc + sy * 0.1, 0.2), 0.12, 0.018, R=RY), k=0.0, label=6)
                wh.add(Cylinder((x, yc + sy * 0.11, 0.2), 0.05, 0.03, rr=0.008, R=RY), k=0.0, label=6)
            wh.add(Cylinder((1.02, yc, 0.33), 0.15, 0.18, rr=0.03, R=RY), k=0.0)
            for k in range(10):                                     # the sprocket's teeth
                a = 2 * math.pi * k / 10
                wh.add(Cylinder((-1.02 + math.cos(a) * 0.165, yc, 0.33 + math.sin(a) * 0.165), 0.028, 0.14, rr=0.008, R=RY), k=0.0)
            wh.add(Cylinder((-1.02, yc, 0.33), 0.15, 0.18, rr=0.03, R=RY), k=0.0)
            # the thrown track: a broken run lying out over the ground in front, curling at its end
            pts = [(1.25, yc, 0.03), (1.9, yc - 0.05, 0.03), (2.45, yc - 0.18, 0.03), (2.8, yc - 0.45, 0.03)]
            for i in range(len(pts) - 1):
                a, b = v3(pts[i]), v3(pts[i + 1])
                d = unit(b - a)
                L = float(np.linalg.norm(b - a))
                n = int(L / 0.09)
                for j in range(n):
                    q = a + d * ((j + 0.5) * L / n)
                    tr.add(RoundBox(q, (0.038, 0.13, 0.025), 0.01, R=np.stack([d, np.cross(Z, d), Z], axis=1)), k=0.0)
            tr.add(Chain([v3((1.2, yc, 0.08)), v3((1.0, yc, 0.4)), v3((0.75, yc, 0.55))], [0.03] * 3, k=0.02), k=0.0)
    # salvaged robot plates on the flanks and the glacis, sprayed with the chevron
    for sy in (-1, 1):
        for i, x in enumerate((-0.55, 0.15)):
            c = v3((x, sy * 0.83, 0.48))
            plate(sp, c, (0, sy, 0), (0, 0, 1), 0.66, 0.34, t=0.02, bow=0.03)
            chevron(sp, c + v3((0, sy * 0.03, 0)), (0, sy, 0), 0.26, 0.12, t=0.045)
            for z in (0.38, 0.58):
                strap(hl, c + v3((-0.3, sy * 0.03, z - 0.48)), c + v3((0.3, sy * 0.03, z - 0.48)), w=0.03, nrm=(0, sy, 0))
    gc = v3((1.08, 0, 0.5))
    gn = unit(v3((1, 0, 0.85)))
    plate(sp, gc, gn, (0, 0, 1), 0.7, 0.36, t=0.02, bow=0.03)
    chevron(sp, gc + gn * 0.03, gn, 0.3, 0.14, t=0.05, up=(-0.6, 0, 0.8))
    # the turret
    ty = 0.55 if wrecked else 0.0
    tilt = 0.09 if wrecked else 0.0
    Rt = Rz(ty) @ euler(tilt, 0.0, 0.0)
    T0 = v3((-0.1, 0.05 if wrecked else 0.0, 0.66 + (0.05 if wrecked else 0.0)))
    tu.add(convex([(T0 + Rt @ v3((0, 0, 0.3)), Rt @ v3((0, 0, 1))), (T0, Rt @ v3((0, 0, -1))), (T0 + Rt @ v3((0.58, 0, 0.1)), Rt @ v3((1, 0, 0.7))),
                   (T0 + Rt @ v3((-0.62, 0, 0.1)), Rt @ v3((-1, 0, 0.25))), (T0 + Rt @ v3((0, 0.44, 0.1)), Rt @ v3((0, 1, 0.4))),
                   (T0 + Rt @ v3((0, -0.44, 0.1)), Rt @ v3((0, -1, 0.4))), (T0 + Rt @ v3((0.4, 0.38, 0.1)), Rt @ unit(v3((1, 1, 0.3)))),
                   (T0 + Rt @ v3((0.4, -0.38, 0.1)), Rt @ unit(v3((1, -1, 0.3))))], T0 - 0.9, T0 + 0.9), k=0.0)
    tu.add(Cylinder(T0 + Z * 0.01, 0.42, 0.06, rr=0.02), k=0.0, label=7)
    hatch = T0 + Rt @ v3((-0.2, 0.18, 0.32))
    tu.add(Cylinder(hatch, 0.14, 0.06, rr=0.02, R=Rt), k=0.01)
    tu.add(Cylinder(hatch + Rt @ v3((-0.1, 0.0, 0.14)), 0.13, 0.025, rr=0.008, R=Rt @ euler(0, -1.2, 0)), k=0.0)     # the hatch lid, open
    tu.sub(Cylinder(hatch + Rt @ v3((0, 0, 0.03)), 0.1, 0.06, R=Rt), k=0.0)
    # the gun: mantlet, barrel (drooping and bent when wrecked), muzzle brake
    M = T0 + Rt @ v3((0.6, 0, 0.16))
    tu.add(RoundBox(M, (0.08, 0.16, 0.1), 0.04, R=Rt), k=0.02)
    d1 = Rt @ unit(v3((1, 0, -0.12 if wrecked else 0.02)))
    B1 = M + d1 * 0.7
    tu.add(RoundCone(M, B1, 0.055, 0.045), k=0.01)
    d2 = unit(Rt @ unit(v3((1, 0.15, -0.45)))) if wrecked else d1
    B2 = B1 + d2 * 0.55
    tu.add(RoundCone(B1, B2, 0.045, 0.042), k=0.02)
    tu.add(Cylinder(B2, 0.06, 0.14, rr=0.015, R=rot_from_axes(z_axis=d2)), k=0.0, label=7)
    tu.sub(Cylinder(B2 + d2 * 0.05, 0.03, 0.2, R=rot_from_axes(z_axis=d2)), k=0.0)
    # salvaged plate on the turret front, the chevron on its flank, a whip antenna (bent), the bustle rack
    tf = T0 + Rt @ v3((0.5, 0.0, 0.16))
    plate(sp, tf + Rt @ v3((0, 0.27, 0)), Rt @ unit(v3((0.7, 0.7, 0.3))), Rt @ v3((0, 0, 1)), 0.36, 0.22, t=0.02, bow=0.02)
    chevron(tu, T0 + Rt @ v3((0.0, -0.44, 0.17)), Rt @ v3((0, -1, 0.4)), 0.28, 0.1, t=0.05)
    an = T0 + Rt @ v3((-0.45, -0.3, 0.3))
    tu.add(Chain([an, an + Z * 0.5, an + Z * 0.8 + Rt @ v3((-0.15, 0, 0)), an + Z * 0.85 + Rt @ v3((-0.4, 0, 0))], [0.012, 0.009, 0.007, 0.006], k=0.01), k=0.0)
    for sy in (-1, 1):
        seg(tu, T0 + Rt @ v3((-0.6, sy * 0.38, 0.12)), T0 + Rt @ v3((-0.9, sy * 0.38, 0.12)), 0.014)
        seg(tu, T0 + Rt @ v3((-0.9, sy * 0.38, 0.12)), T0 + Rt @ v3((-0.9, sy * 0.38, 0.32)), 0.014)
    seg(tu, T0 + Rt @ v3((-0.9, -0.38, 0.32)), T0 + Rt @ v3((-0.9, 0.38, 0.32)), 0.014)
    for i, y in enumerate((-0.2, 0.05)):
        ammo_crate(sp, T0 + Rt @ v3((-0.76, y, 0.22)), (0.1, 0.12, 0.09), yaw=ty + 0.1 * i, label=7, mark=False)
    jerrycan(sp, T0 + Rt @ v3((-0.78, 0.27, 0.25)), yaw=ty + math.pi / 2, s=0.9)
    # an amber light strip on the turret's side (dead on the wreck: painted, not glowing), the hull's chevron
    if not wrecked:
        strip(glows["glow_ember"], T0 + Rt @ v3((-0.3, 0.45, 0.14)), T0 + Rt @ v3((0.3, 0.45, 0.14)), 0.02, up=Rt @ v3((0, 1, 0.4)))
    chevron(hl, (-1.18, 0, 0.5), (-1, 0, 0.2), 0.3, 0.12, t=0.05)
    if wrecked:                                                     # scorch over the hull and the turret
        for i in range(6):
            q = v3((rng.uniform(-1.0, 1.0), rng.choice([-0.6, 0.6]) * rng.uniform(0.6, 1.0), rng.uniform(0.3, 0.7)))
            for f in (hl, sp):
                f.paint(Sphere(q, rng.uniform(0.12, 0.2), **wob(6.0, 0.04, seed + i)), 9)
        tu.paint(Sphere(T0 + Rt @ v3((0.3, -0.35, 0.2)), 0.16, **wob(6.0, 0.04, seed + 9)), 9)
    ground_cut(tr, -0.02)
    ground_cut(wh, -0.02)
    parts = [(prefix + "Hull", hl, fine(0.006, 0.012), "res_armor"), (prefix + "Turret", tu, fine(0.006, 0.012), "res_armor"),
             (prefix + "Salvage", sp, fine(0.005, 0.01), "salvage"), (prefix + "Tracks", tr, fine(0.005, 0.01), "track"),
             (prefix + "Wheels", wh, fine(0.005, 0.01), "track")]
    finish_glows(parts, glows)
    place_parts(out, parts, o, R)
    return {"hatch": o + R @ (hatch + Z * 0.05), "deck": o + R @ v3((-0.95, 0.0, 0.7))}


def res_buggy(out, o=(0, 0, 0), yaw=0.0, burnt=True, seed=0, prefix="Buggy"):
    """The Resistance's armoured car (nose toward +X, 1.9 m long): a slab-sided charcoal hull with a sloped nose, an
    open crew bay behind a salvaged robot plate shield, a refitted robot cannon on a ring mount (its cell amber), big
    off-road wheels; burnt: blackened and rusting, the tyres burnt off the rims, the front right wheel gone and the
    nose down on its hub, a door hanging open, the plate shield scorched. Returns {name: world point}."""
    o = v3(o)
    R = Rz(yaw)
    hl, sp, wh, gn = Field(prefix + "Hull"), Field(prefix + "Plate"), Field(prefix + "Wheels"), Field(prefix + "Gun")
    rng = np.random.default_rng(seed)
    tilt = euler(0.06, 0.07, 0.0) if burnt else np.eye(3)
    zc = 0.42 if not burnt else 0.38
    C0 = v3((0, 0, zc))
    hull_mat = "burnt_res" if burnt else "res_armor"
    hl.add(convex([(C0 + tilt @ v3((0, 0, 0.36)), tilt @ v3((0, 0, 1))), (C0 + tilt @ v3((0, 0, -0.16)), tilt @ v3((0, 0, -1))),
                   (C0 + tilt @ v3((0.7, 0, 0.36)), tilt @ unit(v3((1, 0, 1.6)))), (C0 + tilt @ v3((1.0, 0, -0.02)), tilt @ unit(v3((1, 0, 0.5)))),
                   (C0 + tilt @ v3((1.0, 0, -0.1)), tilt @ unit(v3((1, 0, -0.8)))),
                   (C0 + tilt @ v3((-0.92, 0, 0)), tilt @ v3((-1, 0, 0.05))), (C0 + tilt @ v3((0, 0.42, 0)), tilt @ unit(v3((0, 1, 0.12)))),
                   (C0 + tilt @ v3((0, -0.42, 0)), tilt @ unit(v3((0, -1, 0.12))))], C0 - 1.2, C0 + 1.2), k=0.0)
    hl.sub(RoundBox(C0 + tilt @ v3((-0.4, 0, 0.42)), (0.42, 0.33, 0.2), 0.04, R=tilt), k=0.0)                          # the open crew bay
    for sy in (-1, 1):                                              # vision slits in the cab's sides and front
        hl.sub(RoundBox(C0 + tilt @ v3((0.35, sy * 0.4, 0.26)), (0.16, 0.05, 0.025), 0.01, R=tilt), k=0.0)
    hl.sub(RoundBox(C0 + tilt @ v3((0.72, 0, 0.3)), (0.05, 0.26, 0.025), 0.01, R=tilt @ euler(0, -0.55, 0)), k=0.0)
    for sy in (-1, 1):                                              # wheel arches
        for x in (-0.55, 0.6):
            hl.sub(Cylinder(C0 + tilt @ v3((x, sy * 0.42, -0.12)), 0.27, 0.3, R=tilt @ RY), k=0.02)
    for sx in (-1, 1):
        box(hl, C0 + tilt @ v3((0.98, sx * 0.3, -0.04)), (0.03, 0.07, 0.04), 0.01, R=tilt, label=7)
    # the door on the left flank hanging open
    dh = C0 + tilt @ v3((0.05, -0.43, 0.0))
    box(hl, dh + tilt @ v3((-0.15, -0.1, 0.03)), (0.15, 0.015, 0.14), 0.01, R=tilt @ Rz(-0.6))
    # wheels: tyres on the left, rims only (burnt), the front right one gone
    wheels = [(-0.55, -1), (0.6, -1), (-0.55, 1), (0.6, 1)]
    for (x, sy) in wheels:
        c = C0 + tilt @ v3((x, sy * 0.47, -0.12))
        if burnt and x > 0 and sy > 0:
            wh.add(Cylinder(c - Z * 0.12 + v3((0, -sy * 0.05, 0)), 0.07, 0.18, rr=0.02, R=RY), k=0.0, label=6)    # the bare hub on the floor
            continue
        if burnt:
            wh.add(Cylinder(c, 0.17, 0.16, rr=0.03, R=RY), k=0.0)
            wh.add(Torus(c, 0.17, 0.03, R=RY), k=0.0)
            for k in range(6):
                a = 2 * math.pi * k / 6
                wh.sub(Cylinder(c + v3((math.cos(a) * 0.1, sy * 0.08, math.sin(a) * 0.1)), 0.035, 0.1, R=RY), k=0.0)
            wh.add(Torus(c, 0.21, 0.025, R=RY, **wob(20.0, 0.01, seed + int(x * 10))), k=0.0, label=7)   # burnt shreds of tyre
        else:
            wheel(wh, wh, c, (0, sy, 0), 0.26, 0.17, hub=0.55, lugs=6)
    # the plate shield and the refitted robot cannon on its ring
    pc = C0 + tilt @ v3((0.0, 0, 0.6))
    plate(sp, pc, tilt @ unit(v3((1, 0, 0.25))), tilt @ v3((0, 0, 1)), 0.62, 0.36, t=0.022, bow=0.06)
    chevron(sp, pc + tilt @ v3((0.06, 0, 0)), tilt @ unit(v3((1, 0, 0.25))), 0.26, 0.12, t=0.05)
    for sy in (-1, 1):
        seg(hl, C0 + tilt @ v3((-0.02, sy * 0.25, 0.34)), pc + tilt @ v3((-0.04, sy * 0.25, -0.1)), 0.02)
    rgc = C0 + tilt @ v3((-0.38, 0, 0.36))
    gn.add(Torus(rgc, 0.24, 0.025, R=tilt), k=0.0)
    seg(gn, rgc, rgc + tilt @ v3((0, 0, 0.26)), 0.035)
    gd = tilt @ unit(v3((1, 0.25, 0.18 if not burnt else -0.05)))
    G0 = rgc + tilt @ v3((0, 0, 0.3))
    gn.add(RoundBox(G0, (0.16, 0.08, 0.08), 0.035, R=R_xz(gd, Z)), k=0.0)
    gn.add(RoundCone(G0 + gd * 0.1, G0 + gd * 0.62, 0.045, 0.035), k=0.01)
    slash(gn, G0 + gd * 0.25 + Z * 0.04, G0 + gd * 0.45 + Z * 0.04, 0.04)
    gn.add(Cylinder(G0 + gd * 0.62, 0.05, 0.08, rr=0.012, R=rot_from_axes(z_axis=gd)), k=0.0)
    gn.add(Cylinder(G0 - gd * 0.12 + tilt @ v3((0, 0.09, 0)), 0.04, 0.12, rr=0.012, R=rot_from_axes(z_axis=gd)), k=0.0, label=6)   # the exposed power cell
    # stowage and scorch
    for i in range(2):
        jerrycan(hl, C0 + tilt @ v3((-0.98, -0.2 + i * 0.4, 0.12)), yaw=math.pi / 2, s=0.85)
    chevron(hl, C0 + tilt @ v3((-0.45, 0.425, 0.0)), tilt @ v3((0, 1, 0.15)), 0.24, 0.1, t=0.045)
    if burnt:
        for i in range(6):
            q = C0 + v3((rng.uniform(-0.9, 0.9), rng.uniform(-0.4, 0.4), rng.uniform(-0.1, 0.4)))
            for f in (hl, sp, gn):
                f.paint(Sphere(q, rng.uniform(0.15, 0.28), **wob(7.0, 0.05, seed + i)), 9)
    for f in (hl, wh):
        ground_cut(f, -0.02)
    parts = [(prefix + "Hull", hl, fine(0.005, 0.01), hull_mat), (prefix + "Plate", sp, fine(0.004, 0.008), "salvage"),
             (prefix + "Wheels", wh, fine(0.004, 0.008), "track"), (prefix + "Gun", gn, fine(0.004, 0.008), "salvage")]
    place_parts(out, parts, o, R)
    return {"bay": o + R @ (C0 + v3((-0.35, 0, 0.1)))}


# ------------------------------------------------------------------------------------------------ Coolant Vaults: scatter
def frosted(f, pts, r, seed, cover=(0.15, 0.85)):
    """A frost sleeve (field f) over the stretch `cover` (fractions of its length) of a pipe through pts, radius r."""
    pts = [v3(p) for p in pts]
    L = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        L.append(L[-1] + float(np.linalg.norm(b - a)))
    def at(t):
        s = t * L[-1]
        for i in range(len(pts) - 1):
            if s <= L[i + 1] + 1e-9:
                u = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
                return pts[i] + (pts[i + 1] - pts[i]) * u
        return pts[-1]
    q = [at(t) for t in np.linspace(cover[0], cover[1], 2 + len(pts) * 2)]
    f.add(Chain(q, [r * 1.3] * len(q), k=0.02, **wob(22.0, r * 0.3, seed)), k=0.0)


def pipe_run(seed=0, variant=0):
    """A coolant pipe run (variant 0: two pipes side by side along X on U-stanchions, a flanged joint, a gate valve with
    its red handwheel, frost furring the pipes; variant 1: a pipe rising out of the deck through its floor flange, an
    elbow, a run to a valve station with a pressure gauge and a drain cock, frost at the elbow)."""
    out = []
    pp, fr, st, vl = Field("Pipes"), Field("Frost"), Field("Stands"), Field("Valve")
    glows = G("glow_screen", "glow_coolant")
    if variant == 0:
        L = 0.85
        for y, r, z in ((-0.12, 0.07, 0.42), (0.12, 0.055, 0.42)):
            seg(pp, (-L, y, z), (L, y, z), r)
            for x in (-L, L):
                flange(pp, (x, y, z), (1, 0, 0), r)
            flange(pp, (0.0, y, z), (1, 0, 0), r)
            frosted(fr, [(-L, y, z), (L, y, z)], r, seed + int(y * 100), cover=(0.05, 0.42) if y < 0 else (0.55, 0.95))
            pp.paint(Cylinder((0.42, y, z), r + 0.03, 0.08, R=RX), 5)
        for x in (-0.55, 0.55):                                     # U-stanchions on base plates
            for sy in (-1, 1):
                seg(st, (x, sy * 0.24, 0.0), (x, sy * 0.24, 0.42), 0.022)
            seg(st, (x, -0.24, 0.34), (x, 0.24, 0.34), 0.022)
            box(st, (x, 0, 0.012), (0.08, 0.3, 0.012), 0.005)
            for y in (-0.12, 0.12):
                st.add(Torus((x, y, 0.42), 0.075, 0.012, R=RX), k=0.0)
        # the gate valve on the big pipe
        vb = v3((-0.3, -0.12, 0.42))
        vl.add(RoundBox(vb, (0.09, 0.1, 0.1), 0.03), k=0.0)
        seg(vl, vb + Z * 0.08, vb + Z * 0.3, 0.02, label=6)
        vl.add(RoundBox(vb + Z * 0.16, (0.05, 0.06, 0.05), 0.02), k=0.0)
        valve_wheel(vl, vb + Z * 0.32, (0, 0, 1), 0.1, label=8)
        ground_cut(st, -0.01)
    else:
        b = v3((-0.55, 0.0, 0.0))
        pts = [b, b + Z * 0.55, b + Z * 0.75 + v3((0.2, 0, 0)), v3((0.35, 0, 0.75))]
        pp.add(Chain(pts, [0.08] * 4, k=0.12), k=0.0)
        flange(pp, b + Z * 0.04, (0, 0, 1), 0.08)
        pp.add(Cylinder(b + Z * 0.01, 0.2, 0.02, rr=0.006), k=0.0, label=7)
        flange(pp, b + Z * 0.4, (0, 0, 1), 0.08)
        frosted(fr, pts, 0.08, seed, cover=(0.3, 0.75))
        # the valve station: a body on a stand, a gauge, a drain cock, the pipe running on down into the deck
        vb = v3((0.45, 0, 0.75))
        vl.add(RoundBox(vb, (0.12, 0.12, 0.12), 0.04), k=0.0)
        flange(vl, vb - v3((0.12, 0, 0)), (1, 0, 0), 0.08, label=6)
        seg(pp, vb + v3((0.12, 0, 0)), vb + v3((0.3, 0, 0)), 0.07)
        pp.add(Chain([vb + v3((0.3, 0, 0)), vb + v3((0.45, 0, -0.1)), vb + v3((0.45, 0, -0.75))], [0.07] * 3, k=0.1), k=0.0)
        flange(pp, vb + v3((0.45, 0, -0.71)), (0, 0, 1), 0.07)
        pp.paint(Cylinder(vb + v3((0.45, 0, -0.4)), 0.11, 0.1), 5)
        valve_wheel(vl, vb + Z * 0.24, (0, 0, 1), 0.11, label=8)
        seg(vl, vb + Z * 0.1, vb + Z * 0.24, 0.02, label=6)
        seg(vl, vb + v3((0, -0.12, 0.05)), vb + v3((0, -0.22, 0.12)), 0.015, label=6)
        gauge(vl, glows["glow_screen"], vb + v3((0, -0.25, 0.16)), (0, -1, 0.3), 0.055)
        seg(st, vb - Z * 0.12, (vb[0], 0, 0), 0.03)
        box(st, (vb[0], 0, 0.012), (0.12, 0.12, 0.012), 0.005)
        ground_cut(st, -0.01)
        ground_cut(pp, -0.03)
    out += [("Pipes", pp, fine(0.005, 0.01), "pipe"), ("Frost", fr, fine(0.005, 0.01), "frost"), ("Stands", st, fine(0.004, 0.008), "steel"),
            ("Valve", vl, fine(0.004, 0.008), "valves")]
    return finish_glows(out, glows)


def coolant_canisters(seed=0):
    """Coolant canisters: three tall white pressure canisters in a low steel frame, blue caps and bands, a glowing
    sight strip down each showing the pale blue coolant, frost round their feet; a fourth lying on its side."""
    out = []
    cn, fr, rk, fs = Field("Canisters"), Field("Caps"), Field("Frame"), Field("Frost")
    glows = G("glow_coolant")

    def can(c, R=None, h=0.62, r=0.11):
        R = np.eye(3) if R is None else R
        ax = R @ Z
        c = v3(c)
        cn.add(RoundCone(c + ax * 0.06, c + ax * (h - r * 0.8), r, r), k=0.0)
        cn.add(Ellipsoid(c + ax * (h - r * 0.8), (r, r, r * 0.7), R=R), k=0.03)
        cn.paint(Cylinder(c + ax * (h * 0.32), r + 0.03, 0.05, R=R), 5)
        cn.paint(Cylinder(c + ax * (h * 0.62), r + 0.03, 0.03, R=R), 5)
        fr.add(Cylinder(c + ax * (h - 0.02), 0.045, 0.07, rr=0.012, R=R), k=0.0)
        fr.add(Torus(c + ax * (h + 0.02), 0.05, 0.012, R=R), k=0.0)
        fr.add(Cylinder(c + ax * 0.035, r * 0.95, 0.07, rr=0.015, R=R), k=0.0, label=7)
        n = R @ v3((0, -1, 0))
        strip(glows["glow_coolant"], c + ax * 0.14 + n * (r + 0.002), c + ax * (h - 0.18) + n * (r + 0.002), 0.03, up=n)
        cn.sub(RoundBox(c + ax * ((h - 0.04) / 2) + n * r, (0.025, 0.03, (h - 0.3) / 2), 0.01, R=R), k=0.006)
    for i, x in enumerate((-0.25, 0.0, 0.25)):
        can((x, 0.0, 0.0))
    for z in (0.12, 0.4):
        for sy in (-1, 1):
            seg(rk, (-0.4, sy * 0.14, z), (0.4, sy * 0.14, z), 0.014)
    for sx in (-1, 1):
        for sy in (-1, 1):
            seg(rk, (sx * 0.4, sy * 0.14, -0.02), (sx * 0.4, sy * 0.14, 0.45), 0.018)
    can((0.4, -0.42, 0.11), R=rot_from_axes(z_axis=(-1, -0.25, 0.0)) @ euler(0, 0, 0.0), h=0.6)
    for i, x in enumerate((-0.25, 0.0, 0.25, 0.15)):
        frost_crust(fs, (x, -0.05 if i < 3 else -0.4, 0.0), (0.18, 0.18, 0.06), seed + i, amp=0.02)
    ground_cut(rk, -0.01)
    ground_cut(fs, -0.01)
    ground_cut(cn, -0.01)
    out += [("Canisters", cn, fine(0.004, 0.008), "canister"), ("Caps", fr, fine(0.004, 0.008), "pipe"), ("Frame", rk, fine(0.004, 0.008), "steel"),
            ("Frost", fs, fine(0.005, 0.01), "frost")]
    return finish_glows(out, glows)


def ice_chunk(seed=0, s=1.0):
    """A chunk of ice broken off the vault's crusts: a few blocky crystals and a slab, frosted round their feet."""
    out = []
    ic, fs = Field("Ice"), Field("Frost")
    rng = np.random.default_rng(seed)
    ice_shards(ic, (0, 0, 0), 4, 0.55 * s, 0.13 * s, seed, spread=0.18 * s)
    ic.add(convex_w([((0, 0, 0.16 * s), (0.2, 0.1, 1)), ((0, 0, -0.05), (0, 0, -1)), ((0.3 * s, 0, 0), (1, 0.2, 0.3)), ((-0.32 * s, 0, 0), (-1, 0.1, 0.2)),
                     ((0, 0.25 * s, 0), (0.1, 1, 0.3)), ((0, -0.27 * s, 0), (-0.2, -1, 0.25))], (-0.6 * s, -0.6 * s, -0.1), (0.6 * s, 0.6 * s, 0.5 * s), 0.012, 4.0, seed),
           k=0.01)
    frost_crust(fs, (0.05 * s, 0.0, 0.0), (0.42 * s, 0.36 * s, 0.07), seed + 3)
    ground_cut(ic, -0.02)
    ground_cut(fs, -0.01)
    out += [("Ice", ic, fine(0.005, 0.01), "ice"), ("Frost", fs, fine(0.006, 0.012), "frost")]
    return out


def coolant_pump(seed=0):
    """A coolant pump on its skid (along X): the ribbed motor in the robots' white with a hazard-orange band, a yellow
    coupling guard, the pump's volute with frosted inlet and outlet pipes, a gauge on the outlet."""
    out = []
    mt, pv, sk, fs = Field("Motor"), Field("Pump"), Field("Skid"), Field("Frost")
    glows = G("glow_screen", "glow_red")
    box(sk, (0, 0, 0.05), (0.62, 0.24, 0.05), 0.012)
    for sy in (-1, 1):
        box(sk, (0, sy * 0.24, 0.06), (0.64, 0.03, 0.06), 0.008, label=7)
    mt.add(Cylinder((-0.3, 0, 0.32), 0.17, 0.46, rr=0.04, R=RX), k=0.0)
    for k in range(12):                                             # cooling fins round the motor
        a = 2 * math.pi * k / 12
        mt.add(RoundBox((-0.3, math.cos(a) * 0.175, 0.32 + math.sin(a) * 0.175), (0.2, 0.012, 0.02), 0.006, R=euler(a, 0, 0)), k=0.006)
    mt.paint(Cylinder((-0.3, 0, 0.32), 0.25, 0.08, R=RX), 5)
    box(mt, (-0.3, 0, 0.12), (0.18, 0.15, 0.06), 0.02, label=7)
    mt.add(Cylinder((-0.56, 0, 0.32), 0.12, 0.05, rr=0.02, R=RX), k=0.01, label=7)
    box(mt, (-0.3, 0, 0.52), (0.08, 0.07, 0.05), 0.015, label=7)            # its junction box
    glows["glow_red"].add(Sphere((-0.3, -0.075, 0.54), 0.018), k=0.0)
    box(pv, (0.02, 0, 0.32), (0.1, 0.12, 0.1), 0.03, label=8)                # the coupling guard (hazard)
    pv.add(Cylinder((0.3, 0, 0.32), 0.2, 0.16, rr=0.05, R=RX), k=0.0)           # the volute
    pv.add(Torus((0.3, 0, 0.32), 0.17, 0.05, R=RX), k=0.03)
    box(pv, (0.3, 0, 0.12), (0.14, 0.14, 0.06), 0.02, label=7)
    inlet = [v3((0.4, 0, 0.32)), v3((0.75, 0, 0.32))]
    outlet = [v3((0.3, -0.18, 0.45)), v3((0.3, -0.18, 0.75)), v3((0.3, -0.45, 0.85))]
    pv.add(Chain(inlet, [0.065] * 2, k=0.0), k=0.02)
    pv.add(Chain(outlet, [0.055] * 3, k=0.08), k=0.02)
    flange(pv, inlet[1], (1, 0, 0), 0.065)
    flange(pv, outlet[2] + v3((0, 0.02, 0)), (0, -1, 0.3), 0.055)
    frosted(fs, inlet, 0.065, seed, cover=(0.2, 0.9))
    frosted(fs, outlet, 0.055, seed + 1, cover=(0.25, 0.8))
    gauge(pv, glows["glow_screen"], v3((0.3, -0.27, 0.7)), (0, -1, 0.3), 0.05)
    seg(pv, (0.3, -0.18, 0.7), (0.3, -0.24, 0.7), 0.012, label=6)
    ground_cut(sk, -0.01)
    out += [("Motor", mt, fine(0.004, 0.008), "robot_white"), ("Pump", pv, fine(0.004, 0.008), "pipe"), ("Skid", sk, fine(0.004, 0.008), "steel"),
            ("Frost", fs, fine(0.004, 0.008), "frost")]
    return finish_glows(out, glows)


def hazard_barrier(seed=0):
    """A hazard barrier: a striped yellow-and-black board on two A-frame legs, a flashing amber lamp on one end, a
    sandbag on each foot; rime along its top."""
    out = []
    bd, lg, fs, sb = Field("Board"), Field("Legs"), Field("Frost"), Field("Bags")
    glows = G("glow_amber")
    L = 0.75
    for z in (0.62, 0.36):
        box(bd, (0, 0, z), (L, 0.025, 0.07), 0.012, label=8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            seg(lg, (sx * 0.62, sy * 0.2, 0.0), (sx * 0.62, 0.0, 0.7), 0.022)
        seg(lg, (sx * 0.62, -0.13, 0.22), (sx * 0.62, 0.13, 0.22), 0.015)
        sandbag(sb, v3((sx * 0.62, 0.0, 0.04)), 0.0, seed=seed + sx)
    lg.add(Cylinder((-0.62, 0, 0.74), 0.04, 0.06, rr=0.01), k=0.0, label=7)
    glows["glow_amber"].add(Ellipsoid((-0.62, 0, 0.81), (0.055, 0.055, 0.045)), k=0.0)
    fs.add(RoundBox((0.05, 0, 0.7), (0.62, 0.035, 0.025), 0.02, **wob(18.0, 0.012, seed)), k=0.0)
    icicles(fs, (-0.5, -0.03, 0.29), (0.6, -0.03, 0.29), 7, 0.08, seed, r=0.012)
    ground_cut(lg, -0.01)
    out += [("Board", bd, fine(0.004, 0.008), "hazard_yellow"), ("Legs", lg, fine(0.004, 0.008), "steel"), ("Frost", fs, fine(0.004, 0.008), "frost"),
            ("Bags", sb, fine(0.004, 0.008), "sandbag")]
    return finish_glows(out, glows)


def steel_crates(seed=0):
    """Steel crates of the robots' spares: two ribbed crates stacked crosswise and a third beside them, stencilled,
    rime on their lids."""
    out = []
    cr, fs = Field("Crates"), Field("Frost")

    def crate(c, half, yaw):
        R = Rz(yaw)
        c = v3(c)
        hx, hy, hz = half
        cr.add(RoundBox(c, half, 0.02, R=R), k=0.0)
        for t in (-0.6, 0.0, 0.6):                                  # ribs round the crate
            cr.add(RoundBox(c + R @ v3((t * hx, 0, 0)), (0.02, hy + 0.012, hz + 0.012), 0.008, R=R), k=0.004, label=7)
        for sx in (-1, 1):
            cr.add(RoundBox(c + R @ v3((sx * (hx + 0.012), 0, hz * 0.4)), (0.012, 0.06, 0.02), 0.006, R=R), k=0.003, label=6)
        stencil(cr, c + R @ v3((-hx * 0.3, -hy, 0.0)), R @ v3((0, -1, 0)), hx * 0.6, hz * 0.4, label=9, n=3)
        cr.paint(RoundBox(c + R @ v3((hx * 0.3, -hy, 0.0)), (0.06, 0.03, 0.06), 0.0, R=R @ euler(0, 0.785, 0)), 5)
        frost_crust(fs, c + Z * (hz + 0.005), (hx * 0.8, hy * 0.8, 0.025), seed + int(c[0] * 10), amp=0.012)
    crate((0, 0, 0.2), (0.38, 0.26, 0.2), 0.0)
    crate((0.02, 0.0, 0.58), (0.3, 0.22, 0.18), 1.4)
    crate((0.68, 0.1, 0.16), (0.2, 0.18, 0.16), 0.3)
    ground_cut(cr, -0.01)
    out += [("Crates", cr, fine(0.005, 0.01), "crate_steel"), ("Frost", fs, fine(0.005, 0.01), "frost")]
    return out


def cable_floor(seed=0, L=1.6, n=5):
    """A fat bundle of cables snaking across the deck, clamped down by brackets, running into a junction box."""
    out = []
    cb, br = Field("Cables"), Field("Brackets")
    pts = [(-L / 2, -0.1, 0.04), (-L / 6, 0.12, 0.04), (L / 6, -0.08, 0.04), (L / 2 - 0.15, 0.05, 0.04)]
    cable_bundle(cb, pts, n=n, r=0.026, seed=seed)
    for t in (0.2, 0.55):
        q = v3(pts[1]) * (1 - t) + v3(pts[2]) * t
        br.add(Torus(q + Z * 0.0, 0.085, 0.014, R=RX), k=0.0)
        box(br, q + Z * 0.004, (0.03, 0.13, 0.006), 0.004)
    box(br, (L / 2, 0.05, 0.16), (0.12, 0.1, 0.16), 0.02)
    br.paint(RoundBox((L / 2 - 0.12, 0.05, 0.22), (0.02, 0.06, 0.05), 0.0), 8)
    ground_cut(cb, -0.01)
    ground_cut(br, -0.01)
    out += [("Cables", cb, fine(0.004, 0.008), "cables"), ("Brackets", br, fine(0.004, 0.008), "steel")]
    return out


def ice_slick(seed=0, w=0.8):
    """A frozen slick of spilt coolant on the deck (ground cover): a thin glossy sheet with a frosted rim, a few
    splinters of ice."""
    out = []
    ic, fs = Field("Slick"), Field("Rim")
    ic.add(Ellipsoid((0, 0, 0.0), (w * 0.5, w * 0.36, 0.025), **wob(3.0 / w, 0.05 * w, seed)), k=0.0)
    fs.add(Func(lambda P: (np.abs(np.sqrt((P[:, 0] / F32(w * 0.5)) ** 2 + (P[:, 1] / F32(w * 0.36)) ** 2) - F32(1.0)) * F32(w * 0.4) - F32(0.025)
                           + NOISE.fbm(P * F32(9.0), 2) * F32(0.02)).astype(F32) * F32(0.8), (-w, -w, -0.05), (w, w, 0.05)), k=0.0)
    fs.inter(Plane((0, 0, 0.03), (0, 0, 1)))
    ice_shards(ic, (w * 0.2, 0.05, 0.0), 2, 0.14, 0.04, seed, spread=0.05)
    ground_cut(ic, -0.005)
    ground_cut(fs, -0.005)
    return [("Slick", ic, fine(0.004, 0.008), "ice"), ("Rim", fs, fine(0.004, 0.008), "frost")]


# ------------------------------------------------------------------------------------------------ Coolant Vaults: landmarks
def coolant_tower(seed=0):
    """The giant frozen coolant tower (front toward -Y): a ribbed white column on its stepped plinth, frost climbing it
    from the deck and icicles hanging off every rib band, a tall sight glass glowing pale blue with the coolant's level,
    a catwalk ring with its railing near the top reached by a caged ladder, a domed top with its vent stack (vapour),
    frosted pipes running into its foot, the robots' hazard-orange bands and placard."""
    out = []
    tw, pl, fs, ic, lad, pp = Field("Tower"), Field("Plinth"), Field("Frost"), Field("Ice"), Field("Ladder"), Field("Pipes")
    glows = G("glow_coolant", "glow_red")
    Rt, H = 0.85, 3.7
    box(pl, (0, 0, 0.08), (1.2, 1.2, 0.08), 0.03)
    pl.add(Cylinder((0, 0, 0.22), Rt + 0.14, 0.14, rr=0.03), k=0.0, label=7)
    pl.paint(Func(lambda P: (np.abs(np.maximum(np.abs(P[:, 0]), np.abs(P[:, 1])) - F32(1.1)) - F32(0.06)).astype(F32), (-1.4, -1.4, -0.1), (1.4, 1.4, 0.3)), 8)
    tw.add(Cylinder((0, 0, 0.25 + H / 2), Rt, H, rr=0.06), k=0.0)
    tw.add(Ellipsoid((0, 0, 0.25 + H - 0.02), (Rt, Rt, 0.32)), k=0.04)
    for z in np.arange(0.6, H, 0.55):                                # rib bands
        tw.add(Torus((0, 0, z), Rt + 0.005, 0.035), k=0.004, label=6)
    rng = np.random.default_rng(seed)
    for z in np.arange(0.6, 2.3, 0.55):                              # icicles round the lower bands
        for k in range(14):
            a = 2 * math.pi * k / 14 + rng.uniform(-0.1, 0.1)
            q = v3((math.cos(a) * (Rt + 0.035), math.sin(a) * (Rt + 0.035), z - 0.03))
            l = rng.uniform(0.05, 0.22) * (1.4 - z / 2.5)
            ic.add(RoundCone(q, q - Z * l, 0.022, 0.003), k=0.01)
    tw.paint(Cylinder((0, 0, 0.25 + H * 0.78), Rt + 0.05, 0.16), 5)
    tw.paint(Cylinder((0, 0, 0.25 + H * 0.84), Rt + 0.05, 0.04), 5)
    tw.paint(RoundBox((0.0, -Rt, 1.95), (0.3, 0.1, 0.2), 0.0), 9)       # the placard
    tw.paint(RoundBox((0.0, -Rt, 1.95), (0.2, 0.12, 0.12), 0.0, R=euler(0, 0.785, 0)), 5)
    # frost climbing the column from its foot
    tw_f = lambda P: (np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(Rt + 0.025) - NOISE.fbm(P * F32(7.0), 3) * F32(0.02)).astype(F32)
    fs.add(Func(lambda P: np.maximum(tw_f(P), P[:, 2] - F32(1.5) - NOISE.fbm(P * F32(2.2) + F32(3.0), 3) * F32(0.8)).astype(F32),
                (-Rt - 0.2, -Rt - 0.2, 0.1), (Rt + 0.2, Rt + 0.2, 2.6)), k=0.0)
    frost_crust(fs, (0, 0, 0.18), (Rt + 0.55, Rt + 0.5, 0.26), seed + 5, amp=0.06)
    # a sheath of blue ice frozen down its flank in runs
    ic.add(Func(lambda P: np.maximum(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(Rt + 0.07) - NOISE.fbm(P * F32(4.0), 3) * F32(0.04),
                                     P[:, 2] - F32(0.9) - (np.cos(np.arctan2(P[:, 1], P[:, 0]) * F32(5.0)) * F32(0.5) + F32(0.35))
                                     - NOISE.fbm(P * F32(1.5) + F32(1.0), 3) * F32(0.5)).astype(F32) * F32(0.8),
                (-Rt - 0.3, -Rt - 0.3, 0.1), (Rt + 0.3, Rt + 0.3, 2.4)), k=0.0)
    ic.sub(Cylinder((0, 0, 0.25 + 1.2), Rt - 0.05, 2.6), k=0.0)
    ice_shards(ic, (Rt * 0.9, -Rt * 0.7, 0.15), 3, 0.6, 0.12, seed + 1, spread=0.15)
    ice_shards(ic, (-Rt * 0.95, -Rt * 0.4, 0.15), 3, 0.45, 0.1, seed + 2, spread=0.15)
    # the sight glass: a slot down the front, the coolant glowing in it to its level
    sg = v3((-0.32, -Rt + 0.02, 0.0))
    tw.sub(RoundBox(sg + Z * 2.0, (0.06, 0.08, 0.95), 0.03, R=Rz(-0.45)), k=0.01)
    box(tw, sg + Z * 2.0 + v3((0.0, -0.04, 0.0)), (0.09, 0.03, 1.0), 0.02, R=Rz(-0.45), k=0.0, label=7)
    tw.sub(RoundBox(sg + Z * 2.0 + v3((0.0, -0.05, 0.0)), (0.05, 0.06, 0.93), 0.02, R=Rz(-0.45)), k=0.0)
    glows["glow_coolant"].add(RoundBox(sg + Z * 1.75 + v3((0.02, 0.02, 0.0)), (0.05, 0.03, 0.68), 0.02, R=Rz(-0.45)), k=0.0)
    # the catwalk ring and its railing, the caged ladder up to it
    zc = 2.75
    lad.add(Func(lambda P: np.maximum(np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(Rt + 0.24)) - F32(0.24), np.abs(P[:, 2] - F32(zc)) - F32(0.025)).astype(F32),
                 (-Rt - 0.6, -Rt - 0.6, zc - 0.1), (Rt + 0.6, Rt + 0.6, zc + 0.1)), k=0.0)
    n = 22
    for k in range(n):
        a = 2 * math.pi * k / n
        q = v3((math.cos(a) * (Rt + 0.46), math.sin(a) * (Rt + 0.46), zc))
        seg(lad, q, q + Z * 0.42, 0.012)
        if k % 2:
            ic.add(RoundCone(q - Z * 0.03, q - Z * rng.uniform(0.12, 0.3), 0.02, 0.003), k=0.0)
        if k % 4 == 0:
            seg(lad, q - Z * 0.02, v3((math.cos(a) * (Rt + 0.02), math.sin(a) * (Rt + 0.02), zc - 0.35)), 0.016)
    for z in (zc + 0.42, zc + 0.22):
        lad.add(Torus((0, 0, z), Rt + 0.46, 0.014 if z > zc + 0.3 else 0.01), k=0.0)
    la = 0.9                                                          # the ladder up the right flank
    for sg_ in (-1, 1):
        a = la + sg_ * 0.13
        seg(lad, (math.cos(a) * (Rt + 0.12), math.sin(a) * (Rt + 0.12), 0.3), (math.cos(a) * (Rt + 0.12), math.sin(a) * (Rt + 0.12), zc + 0.45), 0.015)
    for z in np.arange(0.45, zc, 0.22):
        seg(lad, (math.cos(la - 0.13) * (Rt + 0.12), math.sin(la - 0.13) * (Rt + 0.12), z), (math.cos(la + 0.13) * (Rt + 0.12), math.sin(la + 0.13) * (Rt + 0.12), z), 0.01)
    for z in np.arange(1.3, zc, 0.45):                               # its cage hoops
        lad.add(Torus((math.cos(la) * (Rt + 0.22), math.sin(la) * (Rt + 0.22), z), 0.17, 0.009), k=0.0)
    # the dome's vent stack, a warning light
    vt = v3((0.25, 0.15, 0.25 + H + 0.2))
    seg(pp, vt - Z * 0.2, vt + Z * 0.55, 0.06)
    pp.add(Cylinder(vt + Z * 0.58, 0.09, 0.08, rr=0.02), k=0.01)
    pp.sub(Cylinder(vt + Z * 0.62, 0.05, 0.08), k=0.0)
    glows["glow_red"].add(Sphere((-0.3, -0.1, 0.25 + H + 0.24), 0.05), k=0.0)
    # frosted pipes into its foot
    for (a, L2, r) in ((-2.2, 1.2, 0.09), (-0.9, 1.0, 0.07), (2.4, 1.3, 0.08)):
        d = v3((math.cos(a), math.sin(a), 0))
        pts = [d * (Rt - 0.05) + Z * 0.5, d * (Rt + 0.3) + Z * 0.5, d * (Rt + 0.55) + Z * 0.3, d * (Rt + L2) + Z * 0.3]
        pp.add(Chain(pts, [r] * 4, k=0.1), k=0.0)
        flange(pp, d * (Rt + 0.15) + Z * 0.5, d, r)
        frosted(fs, pts, r, seed + int(a * 10), cover=(0.2, 1.0))
    for f in (pl, tw, lad, pp):
        ground_cut(f, -0.02)
    ground_cut(fs, -0.02)
    ground_cut(ic, -0.02)
    out += [("Tower", tw, fine(0.008, 0.016), "cryo"), ("Plinth", pl, fine(0.008, 0.016), "deck"), ("Frost", fs, fine(0.007, 0.014), "frost"),
            ("Ice", ic, fine(0.006, 0.012), "ice"), ("Ladder", lad, fine(0.005, 0.01), "galv"), ("Pipes", pp, fine(0.006, 0.012), "pipe")]
    return finish_glows(out, glows)


TOWER_VENTS = [(0.25, 0.15, 0.25 + 3.7 + 0.2 + 0.62)]          # its vent stack (Blender, prop-local)


def heat_exchanger(seed=0):
    """A heat-exchanger wall (front toward -Y, 3 m long): banks of finned tubes in a steel frame between two big
    headers, frost growing up the lower tubes and icicles under the beams, coolant glowing in sight tubes on the
    headers, gauges, a walkway grating at its foot, hazard stripes on the plinth."""
    out = []
    fr, tb, hd, fs, ic = Field("Frame"), Field("Tubes"), Field("Headers"), Field("Frost"), Field("Ice")
    glows = G("glow_coolant", "glow_screen", "glow_red")
    L, H = 1.35, 1.9
    box(fr, (0, 0, 0.08), (L + 0.35, 0.32, 0.08), 0.02)
    fr.paint(RoundBox((0, -0.3, 0.08), (L + 0.4, 0.05, 0.1), 0.0), 8)
    for x in (-L, -L / 3, L / 3, L):
        box(fr, (x, -0.16, H / 2 + 0.1), (0.04, 0.04, H / 2), 0.008)
        box(fr, (x, 0.16, H / 2 + 0.1), (0.04, 0.04, H / 2), 0.008)
    for z in (0.22, H + 0.12):
        for y in (-0.16, 0.16):
            box(fr, (0, y, z), (L + 0.05, 0.04, 0.04), 0.008)
    for x in (-L + 0.4, 0.0, L - 0.4):                                # cross bracing at the back
        seg(fr, (x - 0.4, 0.17, 0.3), (x + 0.4, 0.17, H), 0.018)
    # the tube banks: rows of tubes, finned (a fine ripple along them)
    for j, z in enumerate(np.arange(0.38, H, 0.15)):
        for y in (-0.08, 0.08):
            zz = z + (0.04 if y > 0 else 0.0)
            tb.add(Func(lambda P, y=y, zz=zz: (np.sqrt((P[:, 1] - F32(y)) ** 2 + (P[:, 2] - F32(zz)) ** 2) - F32(0.045)
                                                - F32(0.012) * (np.cos(P[:, 0] * F32(80.0)) > F32(0.6)).astype(F32)).astype(F32),
                        (-L + 0.05, y - 0.08, zz - 0.08), (L - 0.05, y + 0.08, zz + 0.08)), k=0.0)
    tb.inter(Func(lambda P: (np.abs(P[:, 0]) - F32(L - 0.06)).astype(F32), (-L, -1, 0), (L, 1, 3)))
    for sx in (-1, 1):                                               # the headers
        c = v3((sx * (L + 0.18), 0.0, 0.0))
        hd.add(Cylinder(c + Z * (H / 2 + 0.2), 0.17, H - 0.1, rr=0.05), k=0.0)
        hd.add(Ellipsoid(c + Z * (H + 0.15), (0.17, 0.17, 0.12)), k=0.03)
        for z in (0.5, 1.2, 1.8):
            hd.add(Torus(c + Z * z, 0.175, 0.025), k=0.004, label=6)
        hd.paint(Cylinder(c + Z * 1.5, 0.22, 0.07), 5)
        n = v3((0, -1, 0))
        hd.sub(RoundBox(c + v3((0, -0.17, 1.0)), (0.035, 0.04, 0.4), 0.015), k=0.005)
        glows["glow_coolant"].add(RoundBox(c + v3((0, -0.15, 0.92)), (0.025, 0.02, 0.3), 0.012), k=0.0)
        gauge(hd, glows["glow_screen"], c + v3((0, -0.2, 1.55)), (0, -1, 0.1), 0.055)
        pts = [c + Z * 0.35 + v3((sx * 0.1, 0, 0)), c + Z * 0.35 + v3((sx * 0.4, -0.1, 0)), c + v3((sx * 0.55, -0.1, 0.0))]
        hd.add(Chain(pts, [0.08] * 3, k=0.08), k=0.0)
        frosted(fs, pts, 0.08, seed + sx, cover=(0.0, 1.0))
    glows["glow_red"].add(Sphere((L + 0.18, 0.0, H + 0.3), 0.04), k=0.0)
    # frost up the lower tubes, icicles under the top beam
    fs.add(Func(lambda P: np.maximum(np.maximum(np.abs(P[:, 1]) - F32(0.14) - NOISE.fbm(P * F32(6.0), 3) * F32(0.03), np.abs(P[:, 0]) - F32(L - 0.05)),
                                     P[:, 2] - F32(0.75) - NOISE.fbm(P * F32(1.8) + F32(7.0), 3) * F32(0.45)).astype(F32),
                (-L, -0.3, 0.2), (L, 0.3, 1.5)), k=0.0)
    icicles(ic, (-L + 0.05, -0.2, H + 0.08), (L - 0.05, -0.2, H + 0.08), 18, 0.2, seed, r=0.02)
    icicles(ic, (-L + 0.05, -0.2, 0.18), (L - 0.05, -0.2, 0.18), 10, 0.07, seed + 1, r=0.016)
    frost_crust(fs, (0, -0.1, 0.12), (L + 0.2, 0.42, 0.1), seed + 3, amp=0.03)
    for f in (fr, hd):
        ground_cut(f, -0.02)
    ground_cut(fs, -0.02)
    out += [("Frame", fr, fine(0.006, 0.012), "steel"), ("Tubes", tb, fine(0.005, 0.01), "pipe"), ("Headers", hd, fine(0.006, 0.012), "cryo"),
            ("Frost", fs, fine(0.006, 0.012), "frost"), ("Ice", ic, fine(0.005, 0.01), "ice")]
    return finish_glows(out, glows)


def frozen_robot(seed=0):
    """A robot caught in the ice mid-stride (front toward -Y): one of the white soldiers striding forward with an arm
    reaching out, its legs and hips swallowed by a great block of ice that climbs to its chest, crystals jutting from
    it, frost on its shoulders and helmet, its visor still glowing a faint red."""
    out = []
    J = robot_figure(out, (0, 0.05, 0), None, 1.0,
                     {"lean": 0.22, "twist": 0.15, "head": (-0.3, -0.15),
                      "arms": {1: (2.3, 0.3, 0.35), -1: (0.2, 0.95, 0.2)},
                      "legs": {1: (0.42, 0.05, 0.25), -1: (-0.32, 0.05, 0.08)}, "z": 0.9}, prefix="Bot", seed=seed)
    ic, fs = Field("Ice"), Field("Frost")
    for (cx, cy, top, nx, ny, w) in ((0.0, 0.0, 1.0, 0.3, -0.35, 0.45), (0.3, -0.25, 0.75, 0.6, -0.2, 0.35), (-0.3, 0.2, 0.85, -0.5, 0.3, 0.4),
                                      (-0.15, -0.35, 0.55, -0.3, -0.6, 0.3)):
        c = v3((cx, cy, 0))
        ic.add(convex_w([(c + Z * top, (nx, ny, 1)), (c - Z * 0.05, (0, 0, -1)), (c + v3((w, 0, 0)), (1, 0.2, 0.25)), (c - v3((w, 0, 0)), (-1, -0.15, 0.2)),
                         (c + v3((0, w * 0.9, 0)), (0.2, 1, 0.3)), (c - v3((0, w, 0)), (-0.15, -1, 0.3)), (c + v3((w * 0.7, -w * 0.7, 0)), (1, -1, 0.3)),
                         (c + v3((-w * 0.7, w * 0.7, 0)), (-1, 1, 0.25))], c - v3((1, 1, 0.1)), c + v3((1, 1, 1.4)), 0.025, 3.0, seed + int(cx * 10)), k=0.03)
    ice_shards(ic, (0.35, -0.3, 0.3), 4, 1.0, 0.13, seed + 1, spread=0.25, tilt=0.7)
    ice_shards(ic, (-0.45, 0.25, 0.3), 3, 0.85, 0.12, seed + 2, spread=0.2, tilt=0.7)
    ice_shards(ic, (-0.2, -0.5, 0.1), 3, 0.6, 0.1, seed + 3, spread=0.15, tilt=0.6)
    ice_shards(ic, (0.5, 0.3, 0.1), 2, 0.55, 0.1, seed + 7, spread=0.1, tilt=0.6)
    frost_crust(fs, (0, -0.05, 0.0), (0.95, 0.85, 0.12), seed + 4, amp=0.04)
    for k in ("shoulder+1", "shoulder-1", "head"):
        if k in J:
            fs.add(Ellipsoid(J[k] + Z * 0.08, (0.12, 0.12, 0.05), **wob(14.0, 0.015, seed + len(k))), k=0.0)
    icicles(fs, J["elbow+1"] - v3((0.06, 0, 0.04)), J["hand+1"] - v3((0, 0, 0.05)), 5, 0.12, seed + 6, r=0.016)
    ground_cut(ic, -0.02)
    ground_cut(fs, -0.02)
    out += [("Ice", ic, fine(0.006, 0.012), "ice"), ("Frost", fs, fine(0.005, 0.01), "frost")]
    return out


def pump_station(seed=0):
    """A pump station (front toward -Y): a raised deck-plate platform with steps and a railing, two big coolant pumps
    side by side feeding a frosted manifold that runs off into the deck, a control panel of dial gauges glowing on its
    pedestal, a stack light, hazard edges."""
    out = []
    pf, rl, pn = Field("Platform"), Field("Railing"), Field("Panel")
    glows = G("glow_screen", "glow_red", "glow_amber", "glow_green", "glow_coolant")
    HX, HY, PZ = 1.25, 0.8, 0.22
    box(pf, (0, 0, PZ / 2), (HX, HY, PZ / 2), 0.02)
    pf.paint(Func(lambda P: (np.abs(np.maximum(np.abs(P[:, 0]) - F32(HX - 0.08), np.abs(P[:, 1]) - F32(HY - 0.08))) - F32(0.05)).astype(F32) * 1.0
                  + np.maximum(F32(PZ - 0.02) - P[:, 2], F32(0.0)) * F32(10.0), (-HX - 0.2, -HY - 0.2, -0.1), (HX + 0.2, HY + 0.2, 0.4)), 8)
    for i in range(3):                                               # the steps up its front
        box(pf, (0.6, -HY - 0.12 - i * 0.12, PZ * (2 - i) / 3 / 2 + 0.005), (0.3, 0.06, PZ * (2 - i) / 3 / 2 + 0.005), 0.01)
    # the railing round the back and sides
    railing_line(rl, [(-HX + 0.05, -HY + 0.05, 0), (-HX + 0.05, HY - 0.05, 0), (HX - 0.05, HY - 0.05, 0), (HX - 0.05, -HY + 0.05, 0)], h=0.5, step=0.4, r=0.014, z0=PZ)
    # two pumps
    for k, x in enumerate((-0.55, 0.35)):
        place_parts(out, coolant_pump(seed + k), (x, 0.1, PZ), Rz(math.pi / 2), rename={"Skid": "Skids", "Motor": "Motors", "Pump": "Pumps", "Frost": "Frost",
                                                                                         "ScreenGlow": "Gauges", "Screen": "Gauges", "Red": "PumpLights"})
    # the manifold behind them
    mf = Field("Manifold")
    pts = [v3((-HX - 0.4, 0.62, 0.0)), v3((-HX - 0.4, 0.62, 0.95)), v3((-HX - 0.1, 0.62, 1.15)), v3((HX + 0.1, 0.62, 1.15)), v3((HX + 0.4, 0.62, 0.95)), v3((HX + 0.4, 0.62, 0.0))]
    mf.add(Chain(pts, [0.12] * 6, k=0.18), k=0.0)
    for x in (-0.55, 0.35):
        mf.add(Chain([v3((x, 0.3, PZ + 0.75)), v3((x, 0.5, PZ + 0.95)), v3((x, 0.62, 1.15))], [0.06] * 3, k=0.08), k=0.0)
    for x in (-HX - 0.4, HX + 0.4):
        flange(mf, (x, 0.62, 0.05), (0, 0, 1), 0.12)
    mf.paint(Cylinder((0.0, 0.62, 1.15), 0.2, 0.3, R=RX), 5)
    fs2 = Field("Frost2")
    frosted(fs2, pts, 0.12, seed + 7, cover=(0.0, 0.55))
    ground_cut(mf, -0.03)
    # the control panel on its pedestal at the front left
    c = v3((-0.75, -HY + 0.2, PZ))
    box(pn, c + Z * 0.42, (0.08, 0.08, 0.42), 0.02)
    Rp = euler(-0.55, 0, 0)
    box(pn, c + Z * 0.92, (0.36, 0.06, 0.2), 0.03, R=Rp)
    for i in range(4):
        gx = -0.24 + i * 0.16
        q = c + Z * 0.92 + Rp @ v3((gx, -0.065, 0.04))
        gauge(pn, glows["glow_screen"], q, Rp @ v3((0, -1, 0)), 0.055)
    for i, k in enumerate(("glow_green", "glow_amber", "glow_red")):
        glows[k].add(Sphere(c + Z * 0.92 + Rp @ v3((-0.2 + i * 0.1, -0.065, -0.12)), 0.018), k=0.0)
    # a stack light at the back corner
    seg(pn, (HX - 0.1, HY - 0.1, PZ), (HX - 0.1, HY - 0.1, PZ + 0.9), 0.02)
    for i, k in enumerate(("glow_green", "glow_amber", "glow_red")):
        glows[k].add(Cylinder((HX - 0.1, HY - 0.1, PZ + 0.97 + i * 0.07), 0.035, 0.06, rr=0.008), k=0.0)
    ground_cut(pf, -0.02)
    out += [("Platform", pf, fine(0.007, 0.014), "deck"), ("Railing", rl, fine(0.004, 0.008), "hazard_yellow"), ("Panel", pn, fine(0.005, 0.01), "graphite"),
            ("Manifold", mf, fine(0.007, 0.014), "pipe"), ("Frost2", fs2, fine(0.007, 0.014), "frost")]
    return finish_glows(out, glows)


# ------------------------------------------------------------------------------------------------ Coolant Vaults: no-build zones
def ice_formation(seed=0, variant=0):
    """A great ice formation (about 2.4 m across): towering crystals of blue ice grown over the deck in a crust of
    frost (variant 0: a crown of spires; variant 1: a broken mound split by a coolant pipe frozen inside it)."""
    out = []
    ic, fs = Field("Ice"), Field("Frost")
    rng = np.random.default_rng(seed)
    if variant == 0:
        ice_shards(ic, (0, 0, 0), 7, 1.9, 0.3, seed, spread=0.55, tilt=0.5)
        ice_shards(ic, (0.7, 0.4, 0), 3, 0.9, 0.18, seed + 1, spread=0.2)
        ice_shards(ic, (-0.65, -0.45, 0), 3, 0.8, 0.16, seed + 2, spread=0.2)
        ic.add(Ellipsoid((0, 0, 0.1), (0.85, 0.75, 0.42), **wob(2.0, 0.08, seed)), k=0.08)
    else:
        ic.add(Ellipsoid((0, 0, 0.05), (1.0, 0.85, 0.8), **wob(1.6, 0.16, seed)), k=0.0)
        ic.add(Ellipsoid((0.45, -0.3, 0.05), (0.6, 0.5, 0.55), **wob(2.2, 0.1, seed + 1)), k=0.1)
        ic.sub(convex([((0.0, 0, 0), (1, 0.15, 0.0)), ((0.1, 0, 0), (-1, -0.15, 0.0)), ((0, 0, 0.45), (0, 0, -1))], (-0.3, -1.5, 0.4), (0.4, 1.5, 1.6)), k=0.03)   # the split
        ice_shards(ic, (0.55, -0.35, 0.6), 4, 0.9, 0.17, seed + 1, spread=0.25, tilt=0.6)
        ice_shards(ic, (-0.6, 0.3, 0.55), 3, 0.8, 0.16, seed + 2, spread=0.2, tilt=0.6)
        ice_shards(ic, (-0.1, 0.0, 0.85), 3, 0.7, 0.15, seed + 4, spread=0.2, tilt=0.4)
        ice_shards(ic, (0.75, 0.4, 0.2), 2, 0.6, 0.13, seed + 5, spread=0.1, tilt=0.5)
        pp = Field("Pipe")
        pts = [v3((-1.5, 0.1, 0.0)), v3((-1.2, 0.1, 0.35)), v3((1.2, -0.1, 0.45)), v3((1.5, -0.1, 0.0))]
        pp.add(Chain(pts, [0.12] * 4, k=0.15), k=0.0)
        flange(pp, (-1.38, 0.1, 0.18), unit(v3((0.3, 0, 0.35))), 0.12)
        ground_cut(pp, -0.03)
        out.append(("Pipe", pp, fine(0.007, 0.014), "pipe"))
    frost_crust(fs, (0, 0, 0.0), (1.3, 1.15, 0.16), seed + 3, amp=0.06)
    for i in range(5):
        a = 2 * math.pi * i / 5 + rng.uniform(-0.3, 0.3)
        q = v3((math.cos(a) * 1.15, math.sin(a) * 1.0, 0.0))
        ic.add(crystal(q - Z * 0.03, unit(v3((math.cos(a) * 0.4, math.sin(a) * 0.4, 1))), 0.07, rng.uniform(0.15, 0.3), tip=0.06), k=0.005)
    ground_cut(ic, -0.02)
    ground_cut(fs, -0.02)
    out += [("Ice", ic, fine(0.008, 0.016), "ice"), ("Frost", fs, fine(0.008, 0.016), "frost")]
    return out


def iced_tank(seed=0):
    """An ice-crusted coolant tank: a horizontal tank on its saddles swallowed in rime and icicles, ice crystals grown
    up round its foot, a vent pipe on top still venting vapour, its placard half buried."""
    out = []
    tk, fs, ic, pp = Field("Tank"), Field("Frost"), Field("Ice"), Field("Pipes")
    L, r, zc = 0.9, 0.55, 0.72
    tk.add(Func(lambda P: np.maximum(np.sqrt(P[:, 1] ** 2 + (P[:, 2] - F32(zc)) ** 2) - F32(r), np.abs(P[:, 0]) - F32(L)).astype(F32),
                (-L - 0.1, -r - 0.1, zc - r - 0.1), (L + 0.1, r + 0.1, zc + r + 0.1)), k=0.0)
    for sx in (-1, 1):
        tk.add(Ellipsoid((sx * L, 0, zc), (0.24, r, r)), k=0.05)
        box(tk, (sx * 0.55, 0, 0.2), (0.12, 0.4, 0.2), 0.02, label=7)
    for x in (-0.55, 0.0, 0.55):
        tk.add(Torus((x, 0, zc), r + 0.004, 0.025, R=RX), k=0.004, label=6)
    tk.paint(RoundBox((0.25, -r, zc + 0.05), (0.14, 0.14, 0.14), 0.0, R=euler(0, 0.785, 0)), 8)
    stencil(tk, (-0.35, -r, zc + 0.12), (0, -1, 0), 0.4, 0.07, label=9, n=4)
    # rime over its top and down its flanks, icicles off its belly
    fs.add(Func(lambda P: np.maximum(np.sqrt(P[:, 1] ** 2 + (P[:, 2] - F32(zc)) ** 2) - F32(r + 0.05) - NOISE.fbm(P * F32(5.0), 3) * F32(0.05),
                                     np.maximum(np.abs(P[:, 0]) - F32(L + 0.15), F32(zc + 0.1) - P[:, 2] - NOISE.fbm(P * F32(2.0) + F32(2.0), 3) * F32(0.6))).astype(F32),
                (-L - 0.4, -r - 0.3, zc - 0.6), (L + 0.4, r + 0.3, zc + r + 0.3)), k=0.0)
    icicles(ic, (-L + 0.1, -r * 0.75, zc - r * 0.55), (L - 0.1, -r * 0.75, zc - r * 0.55), 12, 0.25, seed, r=0.025)
    icicles(ic, (-L + 0.1, r * 0.75, zc - r * 0.55), (L - 0.1, r * 0.75, zc - r * 0.55), 10, 0.22, seed + 1, r=0.025)
    ice_shards(ic, (-0.7, -0.6, 0.0), 4, 0.8, 0.14, seed + 2, spread=0.25)
    ice_shards(ic, (0.75, 0.55, 0.0), 3, 0.7, 0.13, seed + 3, spread=0.2)
    ice_shards(ic, (0.3, -0.75, 0.0), 2, 0.45, 0.1, seed + 4, spread=0.1)
    frost_crust(fs, (0, 0, 0.0), (1.35, 1.0, 0.18), seed + 5, amp=0.06)
    vt = v3((0.45, 0.15, zc + r - 0.05))
    seg(pp, vt, vt + Z * 0.6, 0.05)
    pp.add(Cylinder(vt + Z * 0.62, 0.075, 0.07, rr=0.015), k=0.01)
    pp.sub(Cylinder(vt + Z * 0.66, 0.045, 0.08), k=0.0)
    flange(pp, vt + Z * 0.12, (0, 0, 1), 0.05)
    valve_wheel(pp, vt + Z * 0.3 + v3((0.0, -0.12, 0.0)), (0, -1, 0), 0.07, label=8)
    seg(pp, vt + Z * 0.3, vt + Z * 0.3 + v3((0.0, -0.1, 0.0)), 0.014, label=6)
    for f in (tk,):
        ground_cut(f, -0.02)
    ground_cut(fs, -0.02)
    ground_cut(ic, -0.02)
    out += [("Tank", tk, fine(0.007, 0.014), "cryo"), ("Frost", fs, fine(0.007, 0.014), "frost"), ("Ice", ic, fine(0.006, 0.012), "ice"),
            ("Pipes", pp, fine(0.004, 0.008), "valves")]
    return out


TANK_VENTS = [(0.45, 0.15, 0.72 + 0.55 - 0.05 + 0.66)]               # the iced tank's vent (Blender, prop-local)


def chiller(seed=0, variant=0):
    """A huge chiller unit (about 2.3 x 1.3 m): the robots' white housing with hazard-orange bands and louvred
    sides on a steel base, big fans in their shrouds and guards (variant 0: three on top; variant 1: two on the front
    face, standing taller), a control box with its screen and warning lights, frosted coolant pipes out of its end."""
    out = []
    hs, fn, gd, pp, fs = Field("Housing"), Field("Fans"), Field("Guards"), Field("Pipes"), Field("Frost")
    glows = G("glow_screen", "glow_red", "glow_amber", "glow_coolant")
    if variant == 0:
        HX, HY, HZ = 1.15, 0.62, 0.55
    else:
        HX, HY, HZ = 0.95, 0.58, 0.85
    zc = 0.12 + HZ
    box(hs, (0, 0, 0.06), (HX + 0.05, HY + 0.05, 0.06), 0.015, label=7)
    hs.add(RoundBox((0, 0, zc), (HX, HY, HZ), 0.05), k=0.0)
    hs.paint(RoundBox((0, 0, zc + HZ - 0.12), (HX + 0.1, HY + 0.1, 0.04), 0.0), 5)
    hs.paint(RoundBox((0, 0, 0.2), (HX + 0.1, HY + 0.1, 0.05), 0.0), 8)
    for sy in (-1, 1):                                               # louvres down the long sides
        for i in range(9):
            z = 0.32 + i * (2 * HZ - 0.5) / 8
            hs.sub(RoundBox((-0.25, sy * HY, z), (HX - 0.6, 0.03, 0.018), 0.008), k=0.0)
            hs.add(RoundBox((-0.25, sy * (HY - 0.01), z - 0.012), (HX - 0.6, 0.022, 0.008), 0.004, R=euler(sy * 0.6, 0, 0)), k=0.0, label=7)
    def fan(c, nrm, Rf):
        n = unit(nrm)
        R = rot_from_axes(z_axis=n)
        c = v3(c)
        hs.add(Cylinder(c + n * 0.06, Rf + 0.06, 0.14, rr=0.03, R=R), k=0.02)
        hs.sub(Cylinder(c + n * 0.1, Rf, 0.2, R=R), k=0.01)
        fn.add(Cylinder(c + n * 0.02, 0.08, 0.08, rr=0.02, R=R), k=0.0)
        for k in range(5):
            a = 2 * math.pi * k / 5 + seed
            b = R @ v3((math.cos(a), math.sin(a), 0))
            t = np.cross(n, b)
            fn.add(RoundBox(c + n * 0.03 + b * (Rf * 0.52), (Rf * 0.45, 0.07, 0.008), 0.006, R=np.stack([b, t, n], axis=1) @ euler(0.35, 0, 0)), k=0.0)
        gd.add(Torus(c + n * 0.13, Rf + 0.01, 0.012, R=R), k=0.0)
        for k in range(3):
            gd.add(Torus(c + n * 0.13, Rf * (0.28 + k * 0.24), 0.008, R=R), k=0.0)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            b = R @ v3((math.cos(a), math.sin(a), 0))
            gd.add(RoundCone(c + n * 0.13, c + n * 0.13 + b * Rf, 0.008, 0.008), k=0.0)
    if variant == 0:
        for x in (-0.72, 0.0, 0.72):
            fan((x, 0.0, zc + HZ - 0.06), (0, 0, 1), 0.3)
    else:
        for x in (-0.46, 0.46):
            fan((x, -HY + 0.06, zc + 0.1), (0, -1, 0), 0.38)
        for x in (-0.5, 0.5):
            fan((x, 0.0, zc + HZ - 0.06), (0, 0, 1), 0.26)
    # the control box and its lights at the +X end
    cb = v3((HX + 0.02, -0.25, zc - 0.05))
    box(hs, cb, (0.08, 0.2, 0.25), 0.02, k=0.0, label=7)
    screen(hs, glows["glow_screen"], cb + v3((0.085, 0, 0.08)), (1, 0, 0), 0.24, 0.14, bezel=0.012, depth=0.012, label=7)
    for i, k in enumerate(("glow_red", "glow_amber")):
        glows[k].add(Sphere(cb + v3((0.09, -0.1 + i * 0.2, -0.15)), 0.025), k=0.0)
    # frosted coolant pipes out of the -X end, down into the deck
    for y, r in ((-0.25, 0.09), (0.25, 0.075)):
        pts = [v3((-HX + 0.05, y, 0.45)), v3((-HX - 0.3, y, 0.45)), v3((-HX - 0.45, y, 0.2)), v3((-HX - 0.45, y, 0.0))]
        pp.add(Chain(pts, [r] * 4, k=0.1), k=0.0)
        flange(pp, (-HX - 0.12, y, 0.45), (1, 0, 0), r)
        frosted(fs, pts, r, seed + int(y * 10), cover=(0.25, 1.0))
        glows["glow_coolant"].add(RoundBox((-HX - 0.22, y, 0.45 + r + 0.005), (0.06, r * 0.4, 0.008), 0.006), k=0.0)
    frost_crust(fs, (-HX - 0.45, 0.0, 0.0), (0.3, 0.5, 0.08), seed + 9, amp=0.03)
    for f in (hs, pp):
        ground_cut(f, -0.02)
    ground_cut(fs, -0.02)
    out += [("Housing", hs, fine(0.007, 0.014), "chiller"), ("Fans", fn, fine(0.005, 0.01), "graphite"), ("Guards", gd, fine(0.004, 0.008), "steel"),
            ("Pipes", pp, fine(0.006, 0.012), "pipe"), ("Frost", fs, fine(0.006, 0.012), "frost")]
    return finish_glows(out, glows)


# ------------------------------------------------------------------------------------------------ Server Hall: scatter
def robo_rack(f, dr, leds, c, yaw=0.0, W=0.3, D=0.42, H=1.65, door="closed", seed=0, red=0.3):
    """One of the robots' server cabinets (fields: f the graphite cabinet, dr its perforated door, leds {key: field}
    with glow_cyan and glow_red) at c, its front toward -Y turned by yaw: lights blinking cyan through the perforated
    door (red ones among them, `red` of them), a cyan status bar along its top, cable grommets on its roof; door
    "open": swung wide on the blades inside; "none": torn away, the blades bare."""
    R = Rz(yaw)
    c = v3(c)
    rng = np.random.default_rng(seed)
    f.add(RoundBox(c + Z * (H / 2 + 0.03), (W, D, H / 2), 0.02, R=R), k=0.0)
    f.add(RoundBox(c + Z * 0.02, (W - 0.02, D - 0.02, 0.025), 0.006, R=R), k=0.0, label=7)
    f.add(RoundBox(c + R @ v3((0, 0, H + 0.04)), (W + 0.01, D + 0.01, 0.012), 0.006, R=R), k=0.003, label=7)
    for sx in (-1, 1):
        f.add(Cylinder(c + R @ v3((sx * W * 0.5, D * 0.3, H + 0.055)), 0.04, 0.02, rr=0.006), k=0.003, label=7)
    fz0, fz1 = 0.12, H - 0.1

    def led_key():
        return "glow_red" if rng.random() < red else "glow_cyan"
    if door == "closed":
        dr.add(RoundBox(c + R @ v3((0, -D - 0.006, (fz0 + fz1) / 2 + 0.03)), (W - 0.025, 0.008, (fz1 - fz0) / 2), 0.006, R=R), k=0.0)
        f.add(RoundBox(c + R @ v3((W - 0.06, -D - 0.022, H * 0.55)), (0.012, 0.012, 0.09), 0.006, R=R), k=0.003, label=6)
        for j in range(10):
            zz = fz0 + 0.07 + j * (fz1 - fz0 - 0.12) / 9
            for i in range(2):
                if rng.random() < 0.8:
                    leds[led_key()].add(RoundBox(c + R @ v3((-W + 0.1 + i * 0.17 + rng.uniform(-0.03, 0.03), -D - 0.016, zz + 0.03)),
                                                 (rng.uniform(0.025, 0.055), 0.005, 0.01), 0.004, R=R), k=0.0)
    else:
        f.sub(RoundBox(c + R @ v3((0, -D, (fz0 + fz1) / 2 + 0.03)), (W - 0.03, 0.06, (fz1 - fz0) / 2), 0.006, R=R), k=0.0)
        if door == "open":
            hinge = c + R @ v3((-W, -D - 0.01, 0))
            d = R @ unit(v3((-0.5, -1.0, 0)))
            Rd = np.stack([d, unit(np.cross(Z, d)), Z], axis=1)
            dr.add(RoundBox(hinge + d * (W - 0.02) + Z * ((fz0 + fz1) / 2 + 0.03), (W - 0.025, 0.008, (fz1 - fz0) / 2), 0.006, R=Rd), k=0.0)
        n = int((fz1 - fz0) / 0.075)
        for j in range(n):
            zz = fz0 + 0.07 + j * 0.075
            f.add(RoundBox(c + R @ v3((0, -D + 0.04, zz)), (W - 0.04, 0.02, 0.03), 0.004, R=R), k=0.0, label=(7 if j % 3 else 0))
            for i in range(2):
                if rng.random() < 0.8:
                    leds[led_key()].add(RoundBox(c + R @ v3((-W + 0.1 + i * 0.2, -D + 0.018, zz)), (rng.uniform(0.02, 0.045), 0.005, 0.009), 0.004, R=R), k=0.0)
    leds["glow_cyan"].add(RoundBox(c + R @ v3((0, -D - 0.012, H - 0.02)), (W - 0.05, 0.006, 0.014), 0.004, R=R), k=0.0)


def robo_racks(seed=0, n=2, door=None, red=0.3):
    """The robots' server cabinets side by side (front toward -Y), cyan and red lights blinking through their doors
    (door: {index: "open" | "none"}), a cable tray across their roofs carrying bundles of cable."""
    out = []
    f, dr, tr, cb = Field("Cabinets"), Field("Doors"), Field("Tray"), Field("Cables")
    leds = G("glow_cyan", "glow_red", prefix="Led")
    W = 0.3
    xs = [(i - (n - 1) / 2) * (2 * W + 0.02) for i in range(n)]
    for i, x in enumerate(xs):
        robo_rack(f, dr, leds, (x, 0, 0), 0.0, W=W, door=(door or {}).get(i, "closed"), seed=seed + i, red=red)
    L = (xs[-1] - xs[0]) / 2 + W + 0.1
    for sy in (-1, 1):
        seg(tr, (-L, sy * 0.13, 1.86), (L, sy * 0.13, 1.86), 0.01)
    for x in np.linspace(-L, L, 2 * n + 2):
        seg(tr, (x, -0.13, 1.86), (x, 0.13, 1.86), 0.008)
    for sx in (-1, 1):
        seg(tr, (sx * L, 0.0, 1.7), (sx * L, 0.0, 1.86), 0.01)
    cable_bundle(cb, [(-L - 0.05, 0, 1.9), (0, 0.0, 1.9), (L + 0.05, 0, 1.9)], n=4, r=0.022, seed=seed, spread=0.05)
    for x in xs:
        cb.add(Chain([v3((x - 0.1, 0.05, 1.87)), v3((x - 0.12, 0.05, 1.8)), v3((x - 0.15, 0.1, 1.71))], [0.015] * 3, k=0.01), k=0.0, label=5)
    ground_cut(f, -0.01)
    out += [("Cabinets", f, fine(0.005, 0.01), "graphite"), ("Doors", dr, fine(0.004, 0.008), "perforated"), ("Tray", tr, fine(0.004, 0.008), "galv"),
            ("Cables", cb, fine(0.004, 0.008), "cables")]
    return finish_glows(out, leds)


def cable_tray(seed=0, L=0.9):
    """A run of ladder cable tray on two T-stands (along X), heavy with bundles of cable, a few loops sagging over
    its side to the floor."""
    out = []
    tr, cb = Field("Tray"), Field("Cables")
    zt = 0.85
    for sy in (-1, 1):
        seg(tr, (-L, sy * 0.2, zt), (L, sy * 0.2, zt), 0.014)
        seg(tr, (-L, sy * 0.2, zt), (-L, sy * 0.2, zt + 0.06), 0.012)
        seg(tr, (L, sy * 0.2, zt), (L, sy * 0.2, zt + 0.06), 0.012)
    for x in np.linspace(-L, L, 9):
        seg(tr, (x, -0.2, zt - 0.005), (x, 0.2, zt - 0.005), 0.01)
    for x in (-L * 0.6, L * 0.6):
        seg(tr, (x, 0, 0.0), (x, 0, zt - 0.02), 0.03)
        seg(tr, (x, -0.24, zt - 0.03), (x, 0.24, zt - 0.03), 0.02)
        box(tr, (x, 0, 0.012), (0.12, 0.12, 0.012), 0.005)
    cable_bundle(cb, [(-L - 0.1, -0.06, zt + 0.05), (0, 0.0, zt + 0.05), (L + 0.1, 0.06, zt + 0.05)], n=6, r=0.025, seed=seed, spread=0.08)
    cb.add(Chain([v3((0.2, 0.2, zt + 0.04)), v3((0.25, 0.3, zt - 0.2)), v3((0.32, 0.38, 0.03)), v3((0.7, 0.45, 0.03))], [0.02] * 4, k=0.05), k=0.0, label=5)
    cb.add(Chain([v3((-0.4, -0.2, zt + 0.04)), v3((-0.38, -0.32, zt - 0.3)), v3((-0.3, -0.36, zt - 0.4)), v3((-0.15, -0.3, zt - 0.2)),
                  v3((-0.05, -0.2, zt + 0.04))], [0.018] * 5, k=0.04), k=0.0, label=9)
    ground_cut(tr, -0.01)
    ground_cut(cb, -0.01)
    out += [("Tray", tr, fine(0.004, 0.008), "galv"), ("Cables", cb, fine(0.004, 0.008), "cables")]
    return out


def rack_cart(seed=0):
    """A rack cart: a steel trolley carrying a server blade pulled from its rack (its lights still blinking), a stack
    of drives and a coil of cable, the push handle at its back."""
    out = []
    fr, kt, tf = Field("Frame"), Field("Kit"), Field("Castors")
    leds = G("glow_cyan", "glow_red")
    hx, hy = 0.4, 0.25
    box(fr, (0, 0, 0.32), (hx, hy, 0.02), 0.008)
    box(fr, (0, 0, 0.12), (hx - 0.02, hy - 0.02, 0.015), 0.006)
    for sx in (-1, 1):
        for sy in (-1, 1):
            seg(fr, (sx * (hx - 0.03), sy * (hy - 0.03), 0.07), (sx * (hx - 0.03), sy * (hy - 0.03), 0.32), 0.014)
            wheel(tf, fr, (sx * (hx - 0.05), sy * (hy - 0.05), 0.04), (0, sy, 0), 0.04, 0.03)
    for sy in (-1, 1):
        seg(fr, (-hx, sy * 0.18, 0.32), (-hx - 0.06, sy * 0.18, 0.92), 0.014)
    seg(fr, (-hx - 0.06, -0.18, 0.92), (-hx - 0.06, 0.18, 0.92), 0.018)
    box(kt, (0.08, 0, 0.42), (0.28, 0.2, 0.08), 0.015)                  # the blade
    kt.paint(RoundBox((0.08, -0.2, 0.42), (0.3, 0.02, 0.1), 0.0), 7)
    rng = np.random.default_rng(seed)
    for i in range(6):
        leds["glow_red" if i == 2 else "glow_cyan"].add(RoundBox((-0.12 + i * 0.07, -0.205, 0.42 + rng.uniform(-0.03, 0.03)), (0.02, 0.005, 0.008), 0.004), k=0.0)
    for i in range(4):                                                  # a stack of drives
        box(kt, (-0.25, 0.08, 0.36 + i * 0.035), (0.08, 0.11, 0.015), 0.006, label=(5 if i % 2 else 0))
    kt.add(Torus((-0.22, -0.1, 0.36), 0.08, 0.02), k=0.0, label=9)
    kt.add(Torus((-0.22, -0.1, 0.39), 0.07, 0.02), k=0.0, label=9)
    ground_cut(tf, -0.01)
    ground_cut(fr, -0.01)
    out += [("Frame", fr, fine(0.004, 0.008), "steel"), ("Kit", kt, fine(0.004, 0.008), "graphite"), ("Castors", tf, fine(0.004, 0.008), "rubber")]
    return finish_glows(out, leds)


def floor_fan(seed=0):
    """A big drum fan on its wheeled stand, tilted up toward the racks: the shroud with its guard grille, the blades,
    the motor pod, the cord trailing off across the floor."""
    out = []
    sh, bl, gd, st = Field("Shroud"), Field("Blades"), Field("Guard"), Field("Stand")
    R0, c = 0.38, v3((0, 0, 0.55))
    n = unit(v3((0, -1, 0.35)))
    Rn = rot_from_axes(z_axis=n)
    sh.add(Cylinder(c, R0 + 0.04, 0.22, rr=0.03, R=Rn), k=0.0)
    sh.sub(Cylinder(c, R0, 0.4, R=Rn), k=0.01)
    sh.paint(Cylinder(c + n * 0.1, R0 + 0.1, 0.03, R=Rn), 5)
    bl.add(Ellipsoid(c - n * 0.06, (0.11, 0.11, 0.1), R=Rn), k=0.0)
    for k in range(3):
        a = 2 * math.pi * k / 3 + seed
        b = Rn @ v3((math.cos(a), math.sin(a), 0))
        t = np.cross(n, b)
        bl.add(RoundBox(c + b * (R0 * 0.5), (R0 * 0.42, 0.11, 0.01), 0.008, R=np.stack([b, t, n], axis=1) @ euler(0.4, 0, 0)), k=0.0)
    for s_ in (1, -1):
        gd.add(Torus(c + n * (0.11 * s_), R0 + 0.01, 0.012, R=Rn), k=0.0)
        for k in range(3):
            gd.add(Torus(c + n * (0.11 * s_), R0 * (0.3 + k * 0.23), 0.007, R=Rn), k=0.0)
        for k in range(6):
            a = k * math.pi / 3
            b = Rn @ v3((math.cos(a), math.sin(a), 0))
            gd.add(RoundCone(c + n * (0.11 * s_), c + n * (0.11 * s_) + b * R0, 0.006, 0.006), k=0.0)
    for sx in (-1, 1):                                               # the yoke and the wheeled stand
        p = c + Rn @ v3((sx * (R0 + 0.05), 0, 0))
        seg(st, p, v3((sx * (R0 + 0.07), 0.05, 0.12)), 0.022)
        st.add(Cylinder(p, 0.04, 0.05, rr=0.01, R=rot_from_axes(z_axis=(1, 0, 0))), k=0.0, label=7)
    box(st, (0, 0.05, 0.1), (R0 + 0.12, 0.12, 0.03), 0.01)
    for sx in (-1, 1):
        wheel(st, st, (sx * (R0 + 0.08), 0.18, 0.06), (sx, 0, 0), 0.06, 0.04)
    st.add(Chain([v3((0.0, 0.17, 0.1)), v3((0.1, 0.4, 0.02)), v3((0.5, 0.6, 0.02)), v3((0.8, 0.5, 0.02))], [0.012] * 4, k=0.03), k=0.0, label=7)
    ground_cut(st, -0.01)
    out += [("Shroud", sh, fine(0.004, 0.008), "fan"), ("Blades", bl, fine(0.004, 0.008), "graphite"), ("Guard", gd, fine(0.003, 0.006), "chrome"),
            ("Stand", st, fine(0.004, 0.008), "fan")]
    return out


def maint_drone(seed=0, pad=True):
    """One of the robots' maintenance drones, parked: a squat white body on four jointed legs, a big round red eye
    lens, hazard-orange stripes, a manipulator arm folded at its side and a cable reel on its back; on its charging
    pad ringed with cyan light."""
    out = []
    bd, lg, pd = Field("Body"), Field("Legs"), Field("Pad")
    glows = G("glow_red", "glow_cyan")
    zb = 0.42
    bd.add(Ellipsoid((0, 0, zb), (0.32, 0.26, 0.18)), k=0.0)
    bd.add(RoundBox((0, 0, zb - 0.06), (0.3, 0.24, 0.1), 0.08), k=0.05)
    bd.paint(RoundBox((0, 0, zb + 0.02), (0.4, 0.4, 0.03), 0.0), 5)
    bd.add(Cylinder((0.0, -0.24, zb + 0.03), 0.09, 0.08, rr=0.02, R=RY), k=0.02, label=7)          # the eye's housing
    glows["glow_red"].add(Cylinder((0.0, -0.28, zb + 0.03), 0.06, 0.01, rr=0.003, R=RY), k=0.0)
    for sx in (-1, 1):
        glows["glow_red"].add(Sphere((sx * 0.13, -0.22, zb + 0.08), 0.016), k=0.0)
    bd.add(Cylinder((0.05, 0.12, zb + 0.17), 0.1, 0.07, rr=0.02), k=0.02, label=7)                # the cable reel on its back
    bd.add(Torus((0.05, 0.12, zb + 0.22), 0.07, 0.018), k=0.0, label=5)
    for k in range(4):                                                  # four jointed legs
        a = math.pi / 4 + k * math.pi / 2
        d = v3((math.cos(a), math.sin(a), 0))
        hip = d * 0.24 + Z * (zb - 0.06)
        knee = d * 0.42 + Z * (zb + 0.08)
        foot = d * 0.5 + Z * 0.03
        seg(lg, hip, knee, 0.03)
        seg(lg, knee, foot, 0.025)
        lg.add(Sphere(knee, 0.04), k=0.01, label=7)
        lg.add(Cylinder(foot, 0.05, 0.03, rr=0.01), k=0.0, label=7)
        bd.add(RoundCone(hip - d * 0.02, knee - Z * 0.03, 0.05, 0.035), k=0.01)
    s0 = v3((0.28, -0.05, zb + 0.04))                                  # the folded manipulator arm on its right side
    seg(lg, s0, s0 + v3((0.08, -0.15, 0.08)), 0.025)
    seg(lg, s0 + v3((0.08, -0.15, 0.08)), s0 + v3((0.05, -0.3, -0.08)), 0.02)
    lg.add(RoundBox(s0 + v3((0.05, -0.33, -0.1)), (0.02, 0.03, 0.04), 0.01), k=0.0, label=7)
    if pad:
        pd.add(Cylinder((0, 0, 0.02), 0.62, 0.04, rr=0.015), k=0.0)
        pd.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(0.5)) - F32(0.03)).astype(F32), (-1, -1, -0.1), (1, 1, 0.1)), 8)
        glows["glow_cyan"].add(Torus((0, 0, 0.04), 0.58, 0.012), k=0.0)
        ground_cut(pd, -0.01)
        out.append(("Pad", pd, fine(0.005, 0.01), "graphite"))
    ground_cut(lg, -0.01)
    out += [("Body", bd, fine(0.004, 0.008), "robot_white"), ("Legs", lg, fine(0.004, 0.008), "gunmetal")]
    return finish_glows(out, glows)


def toppled_rack(seed=0):
    """A server cabinet toppled onto its back, its door torn off and lying beside it, blades spilling out on their
    cables, a few lights still blinking red and cyan."""
    out = []
    f, dr, cb = Field("Cabinet"), Field("Door"), Field("Cables")
    leds = G("glow_cyan", "glow_red", prefix="Led")
    tmp_f, tmp_dr = Field("tf"), Field("td")                           # (built standing, then laid on its back: its front up)
    tl = G("glow_cyan", "glow_red", prefix="tl")
    robo_rack(tmp_f, tmp_dr, tl, (0, 0, 0), 0.0, W=0.3, D=0.42, H=1.65, door="none", seed=seed, red=0.5)
    Rlay = np.stack([v3((0, 1, 0)), v3((0, 0, -1)), v3((1, 0, 0))], axis=1)   # its height along +X, its front up
    o = v3((-0.85, 0.0, 0.43))
    place(f, tmp_f, o, Rlay)
    for k in ("glow_cyan", "glow_red"):
        place(leds[k], tl[k], o, Rlay)
    dr.add(RoundBox((0.1, -0.75, 0.03), (0.72, 0.26, 0.01), 0.006, R=Rz(0.3) @ euler(0.06, 0, 0)), k=0.0)   # the door torn off beside it
    for i, (x, y, a) in enumerate(((-0.2, -0.32, 0.4), (0.25, -0.38, -0.2), (0.55, 0.42, 0.7))):           # blades spilling out
        box(f, (x, y, 0.05), (0.28, 0.2, 0.03), 0.01, R=Rz(a) @ euler(0.15, 0, 0), label=7)
        cb.add(Chain([v3((x, 0.0, 0.7)), v3((x + 0.05, y * 0.5, 0.5)), v3((x, y, 0.08))], [0.012] * 3, k=0.03), k=0.0, label=(5, 9, 8)[i])
    cable_bundle(cb, [(-0.9, 0.2, 0.75), (-1.15, 0.45, 0.4), (-1.25, 0.7, 0.03), (-0.9, 0.95, 0.03)], n=3, r=0.02, seed=seed)
    ground_cut(f, -0.02)
    ground_cut(cb, -0.01)
    out += [("Cabinet", f, fine(0.005, 0.01), "graphite"), ("Door", dr, fine(0.004, 0.008), "perforated"), ("Cables", cb, fine(0.004, 0.008), "cables")]
    return finish_glows(out, leds)


def vent_tile(seed=0):
    """A perforated floor tile over the cold air (ground cover): the punched grid with a cyan glow below it, its
    steel frame."""
    out = []
    tl, fr = Field("Tile"), Field("TileFrame")
    glows = G("glow_cyan")
    box(fr, (0, 0, 0.012), (0.32, 0.32, 0.012), 0.004)
    fr.sub(RoundBox((0, 0, 0.03), (0.28, 0.28, 0.02), 0.004), k=0.0)
    box(tl, (0, 0, 0.016), (0.28, 0.28, 0.006), 0.003)
    for i in range(6):                                                  # the punched slots
        tl.sub(RoundBox((-0.2 + i * 0.08, 0, 0.02), (0.02, 0.24, 0.02), 0.008), k=0.0)
    glows["glow_cyan"].add(RoundBox((0, 0, 0.006), (0.26, 0.26, 0.003), 0.002), k=0.0)
    ground_cut(fr, -0.005)
    out += [("Tile", tl, fine(0.003, 0.006), "perforated"), ("TileFrame", fr, fine(0.003, 0.006), "steel")]
    return finish_glows(out, glows)


# ------------------------------------------------------------------------------------------------ Server Hall: landmarks
def _tower_block(f, gl, c, w, d, h, peak, seed, lancets=2):
    """A rack tower of the mainframe wall (field f, lights gl {key: field}) at c (its foot's centre, front -Y): w
    half wide, d half deep, h to its shoulders, rising to a pointed (gothic) top `peak` higher; lancets of cyan light
    up its front, rows of blinking lights."""
    c = v3(c)
    f.add(convex([(c, (0, 0, -1)), (c + v3((w, 0, 0)), (1, 0, 0)), (c - v3((w, 0, 0)), (-1, 0, 0)),
                  (c + v3((0, d, 0)), (0, 1, 0)), (c - v3((0, d, 0)), (0, -1, 0)),
                  (c + Z * (h + peak), unit(v3((peak, 0, w)))), (c + Z * (h + peak), unit(v3((-peak, 0, w))))],
                 c - v3((w + 0.2, d + 0.2, 0.1)), c + v3((w + 0.2, d + 0.2, h + peak + 0.2))), k=0.0)
    f.add(RoundBox(c + Z * (h - 0.04), (w + 0.03, d + 0.03, 0.04), 0.01), k=0.0, label=7)     # the cornice at its shoulders
    rng = np.random.default_rng(seed)
    for i in range(lancets):                                          # lancets of cyan light up its front
        x = (i - (lancets - 1) / 2) * (2 * w / (lancets + 0.6))
        z0, z1 = 0.35, h - 0.2
        f.sub(RoundBox(c + v3((x, -d, (z0 + z1) / 2)), (0.05, 0.04, (z1 - z0) / 2), 0.02), k=0.005)
        gl["glow_cyan"].add(RoundBox(c + v3((x, -d + 0.02, (z0 + z1) / 2)), (0.04, 0.012, (z1 - z0) / 2 - 0.01), 0.012), k=0.0)
    for j in range(int(h / 0.22)):                                    # rows of status lights between the lancets
        z = 0.3 + j * 0.22
        for i in range(lancets + 1):
            x = (i - lancets / 2) * (2 * w / (lancets + 0.6))
            if abs(x) > w - 0.06 or rng.random() < 0.3:
                continue
            gl["glow_red" if rng.random() < 0.25 else "glow_cyan"].add(RoundBox(c + v3((x, -d - 0.005, z)), (0.025, 0.006, 0.01), 0.004), k=0.0)
    f.add(RoundBox(c + v3((0, -d - 0.01, 0.08)), (w + 0.02, 0.03, 0.08), 0.01), k=0.0, label=7)


def mainframe_wall(seed=0):
    """The mainframe wall (front toward -Y, 4 m wide): a cathedral of the machine. Rack towers rise in steps to a
    tall pointed nave, every one lit with lancets of cyan light and rows of blinking lights, buttresses of armoured
    cable conduit between them; over the nave's door a great rose window of cyan light rings round the robots' red
    eye; a stepped plinth before it, cable trunks pouring down into the floor behind."""
    out = []
    tw, pl, ct, rs = Field("Towers"), Field("Plinth"), Field("Conduits"), Field("Rose")
    glows = G("glow_cyan", "glow_red")
    box(pl, (0, 0.05, 0.06), (2.2, 0.75, 0.06), 0.02)
    box(pl, (0, -0.05, 0.16), (1.9, 0.6, 0.06), 0.02)
    pl.paint(RoundBox((0, -0.68, 0.1), (2.3, 0.05, 0.12), 0.0), 8)
    z0 = 0.22
    for (x, w, h, pk, nl) in ((0.0, 0.5, 2.9, 0.75, 3), (-0.95, 0.36, 2.2, 0.5, 2), (0.95, 0.36, 2.2, 0.5, 2),
                              (-1.68, 0.3, 1.55, 0.36, 1), (1.68, 0.3, 1.55, 0.36, 1)):
        _tower_block(tw, glows, (x, 0.0, z0), w, 0.42, h, pk, seed + int(x * 10), lancets=nl)
    for x in (-0.5, 0.5, -1.33, 1.33):                                # buttresses of cable conduit between the towers
        top = 2.4 if abs(x) < 1 else 1.7
        ct.add(RoundCone(v3((x, -0.3, z0)), v3((x, -0.15, z0 + top)), 0.09, 0.06), k=0.0)
        for z in np.arange(z0 + 0.25, z0 + top, 0.35):
            ct.add(Torus((x, -0.3 + (z - z0) / top * 0.15, z), 0.095, 0.02), k=0.0, label=6)
    for i, x in enumerate((-0.3, 0.3, -1.1, 1.1)):                    # cable trunks pouring down behind
        cable_bundle(ct, [(x, 0.3, z0 + 2.0 - abs(x) * 0.4), (x * 1.1, 0.6, z0 + 1.2), (x * 1.2, 0.75, 0.05)], n=3, r=0.04, seed=seed + i, spread=0.07)
    rc = v3((0.0, -0.44, z0 + 2.55))                                  # the rose window over the nave
    Rr = rot_from_axes(z_axis=(0, -1, 0))
    tw.add(Cylinder(rc + v3((0, 0.02, 0)), 0.48, 0.08, rr=0.03, R=Rr), k=0.02)
    rs.add(Torus(rc, 0.42, 0.04, R=Rr), k=0.0, label=7)
    for k in range(8):
        a = 2 * math.pi * k / 8
        b = v3((math.cos(a), 0, math.sin(a)))
        rs.add(RoundCone(rc + b * 0.14, rc + b * 0.4, 0.025, 0.025), k=0.0, label=7)
        glows["glow_cyan"].add(Sphere(rc + b * 0.27 - v3((0, 0.01, 0)), 0.06), k=0.0)
    glows["glow_cyan"].add(Torus(rc - v3((0, 0.02, 0)), 0.42, 0.022, R=Rr), k=0.0)
    glows["glow_red"].add(Cylinder(rc - v3((0, 0.01, 0)), 0.11, 0.04, rr=0.015, R=Rr), k=0.0)
    rs.add(Torus(rc, 0.13, 0.025, R=Rr), k=0.0, label=7)
    tw.sub(convex([((0, -0.42, z0), (0, 0, -1)), ((0.24, -0.42, 0), (1, 0, 0)), ((-0.24, -0.42, 0), (-1, 0, 0)),       # the nave's door
                   ((0, -0.3, 0), (0, 1, 0)), ((0, -0.42, z0 + 1.2), unit(v3((0.2, 0, 0.24)))), ((0, -0.42, z0 + 1.2), unit(v3((-0.2, 0, 0.24))))],
                  (-0.5, -0.6, 0), (0.5, 0.0, 1.8)), k=0.0)
    strip(glows["glow_cyan"], (-0.3, -0.45, z0 + 1.38), (0.3, -0.45, z0 + 1.38), 0.03, up=(0, -1, 0))
    for f in (tw, pl, ct):
        ground_cut(f, -0.02)
    out += [("Towers", tw, fine(0.008, 0.016), "graphite"), ("Plinth", pl, fine(0.008, 0.016), "tile"), ("Conduits", ct, fine(0.006, 0.012), "gunmetal"),
            ("Rose", rs, fine(0.005, 0.01), "robot_white")]
    return finish_glows(out, glows)


def duct_column(seed=0):
    """A cooling-duct column (3.8 m): a great round duct rising from its square plinth in flanged sections, louvred
    vents breathing cyan-lit cold air, a fan housing at mid height, branches elbowing off at its top, armoured cables
    clipped up its side, hazard bands at its foot."""
    out = []
    dc, pl, fn, cb = Field("Duct"), Field("Plinth"), Field("Fan"), Field("Cables")
    glows = G("glow_cyan", "glow_red")
    R0, H = 0.55, 3.5
    box(pl, (0, 0, 0.15), (0.8, 0.8, 0.15), 0.03)
    pl.paint(RoundBox((0, 0, 0.15), (0.85, 0.85, 0.06), 0.0), 8)
    dc.add(Cylinder((0, 0, 0.3 + H / 2), R0, H, rr=0.05), k=0.0)
    for z in np.arange(0.5, H + 0.3, 0.6):
        dc.add(Torus((0, 0, z), R0 + 0.01, 0.04), k=0.004, label=6)
        for k in range(8):
            a = 2 * math.pi * k / 8
            dc.add(Sphere((math.cos(a) * (R0 + 0.045), math.sin(a) * (R0 + 0.045), z), 0.018), k=0.0, label=6)
    for a in (-math.pi / 2 - 0.5, -math.pi / 2 + 0.5, 0.6):           # louvred vents with cyan light behind
        d = v3((math.cos(a), math.sin(a), 0))
        Rv = np.stack([d, np.cross(Z, d), Z], axis=1)
        for j in range(5):
            dc.sub(RoundBox(d * R0 + Z * (1.0 + j * 0.12), (0.06, 0.2, 0.025), 0.01, R=Rv), k=0.0)
        glows["glow_cyan"].add(RoundBox(d * (R0 - 0.04) + Z * 1.24, (0.02, 0.18, 0.3), 0.01, R=Rv), k=0.0)
    fc = v3((0, -R0 - 0.15, 2.15))                                     # the fan housing on the front at mid height
    Rf = rot_from_axes(z_axis=(0, -1, 0))
    dc.add(RoundBox(fc + v3((0, 0.1, 0)), (0.38, 0.15, 0.38), 0.05), k=0.04)
    dc.sub(Cylinder(fc - v3((0, 0.06, 0)), 0.32, 0.12, R=Rf), k=0.01)
    fn.add(Cylinder(fc, 0.06, 0.06, rr=0.015, R=Rf), k=0.0)
    for k in range(5):
        a = 2 * math.pi * k / 5
        b = v3((math.cos(a), 0, math.sin(a)))
        fn.add(RoundBox(fc + b * 0.17, (0.14, 0.008, 0.05), 0.006, R=np.stack([b, v3((0, 1, 0)), np.cross(b, v3((0, 1, 0)))], axis=1) @ euler(0.4, 0, 0)), k=0.0)
    for k in range(3):
        fn.add(Torus(fc - v3((0, 0.07, 0)), 0.1 + k * 0.1, 0.008, R=Rf), k=0.0, label=7)
    glows["glow_red"].add(Sphere(fc + v3((0.32, -0.12, 0.32)), 0.03), k=0.0)
    zt = 0.3 + H                                                       # the top: a cap and two branch ducts running off
    dc.add(Ellipsoid((0, 0, zt), (R0, R0, 0.22)), k=0.05)
    for a, L in ((0.3, 1.0), (math.pi + 0.5, 0.8)):
        d = v3((math.cos(a), math.sin(a), 0))
        dc.add(Chain([Z * (zt - 0.4), d * 0.4 + Z * (zt - 0.3), d * (0.4 + L) + Z * (zt - 0.25)], [0.3, 0.3, 0.3], k=0.15), k=0.05)
        dc.add(Torus(d * (0.4 + L) + Z * (zt - 0.25), 0.31, 0.04, R=rot_from_axes(z_axis=d)), k=0.0, label=6)
        dc.sub(Cylinder(d * (0.4 + L + 0.05) + Z * (zt - 0.25), 0.24, 0.12, R=rot_from_axes(z_axis=d)), k=0.0)
    a = 2.3                                                            # cables clipped up its side
    d = v3((math.cos(a), math.sin(a), 0))
    cable_bundle(cb, [d * (R0 + 0.06) + Z * 0.3, d * (R0 + 0.06) + Z * 1.6, d * (R0 + 0.06) + Z * 3.0, d * (R0 + 0.2) + Z * 3.6], n=3, r=0.035, seed=seed, spread=0.05)
    cable_bundle(cb, [d * (R0 + 0.06) + Z * 0.3, d * (R0 + 0.4) + Z * 0.05, d * (R0 + 1.0) + Z * 0.05], n=3, r=0.035, seed=seed + 1, spread=0.05)
    for z in (0.9, 1.9, 2.9):
        cb.add(Torus(d * (R0 + 0.06) + Z * z, 0.09, 0.015), k=0.0, label=6)
    for f in (dc, pl):
        ground_cut(f, -0.02)
    ground_cut(cb, -0.02)
    out += [("Duct", dc, fine(0.008, 0.016), "white_tech"), ("Plinth", pl, fine(0.007, 0.014), "tile"), ("Fan", fn, fine(0.005, 0.01), "graphite"),
            ("Cables", cb, fine(0.006, 0.012), "cables")]
    return finish_glows(out, glows)


def robot_workstation(seed=0):
    """A robot workstation (front toward -Y): a curved graphite console with three screens glowing pale blue over their
    lit keyboards, a rack behind it cabled into it, and the robot operator standing at it powered down, head bowed,
    hands on the desk, its visor a dim red."""
    out = []
    cs, rk, td = Field("Console"), Field("Rack"), Field("Door")
    glows = G("glow_screen", "glow_cyan")
    leds = G("glow_cyan", "glow_red", prefix="Led")
    for k in range(3):                                                  # the console curving round the operator
        a = math.pi / 2 + (k - 1) * 0.6
        d = v3((math.cos(a), math.sin(a), 0))                           # (from the operator out to the desk)
        c = v3((0, -0.35, 0)) + d * 0.75
        R = np.stack([np.cross(d, Z), -d, Z], axis=1)
        cs.add(RoundBox(c + Z * 0.42, (0.3, 0.2, 0.42), 0.03, R=R), k=0.03)
        cs.add(RoundBox(c + Z * 0.87 - d * 0.05, (0.31, 0.25, 0.03), 0.015, R=R), k=0.02, label=7)
        sc_c = c + Z * 1.18 + d * 0.1
        screen(cs, glows["glow_screen"], sc_c, -d, 0.48, 0.3, tilt=-0.1, bezel=0.02, depth=0.03)
        seg(cs, sc_c + d * 0.04 - Z * 0.15, c + Z * 0.88 + d * 0.06, 0.03)
        glows["glow_cyan"].add(RoundBox(c + Z * 0.905 - d * 0.12, (0.22, 0.07, 0.006), 0.004, R=R), k=0.0)
        cs.paint(RoundBox(c + Z * 0.6 - d * 0.2, (0.26, 0.05, 0.05), 0.0, R=R), 5)
    robo_rack(rk, td, leds, (0.0, 1.05, 0.0), 0.0, W=0.3, D=0.42, H=1.75, seed=seed)
    cable_bundle(rk, [(0.15, 0.62, 0.05), (0.1, 0.5, 0.03), (0.0, 0.4, 0.05)], n=3, r=0.025, seed=seed, spread=0.04)
    robot_figure(out, (0.0, -0.4, 0.0), Rz(math.pi), 1.0,                 # the operator, powered down at the desk, facing +Y
                 {"lean": 0.42, "head": (0.0, 0.45), "arms": {1: (0.85, 0.15, 0.5), -1: (0.8, 0.2, 0.55)},
                  "legs": {1: (0.12, 0.06, 0.08), -1: (-0.05, 0.06, 0.04)}}, prefix="Bot", seed=seed)
    for f in (cs, rk):
        ground_cut(f, -0.02)
    out += [("Console", cs, fine(0.006, 0.012), "graphite"), ("Rack", rk, fine(0.006, 0.012), "graphite"), ("Door", td, fine(0.005, 0.01), "perforated")]
    finish_glows(out, glows)
    return finish_glows(out, leds)


def breach(seed=0):
    """The Resistance's breach (front toward -Y, 3.2 m): a stretch of the hall's armoured wall blown open, a ragged hole
    through its panels, plates bent outward round it and blackened, rubble and twisted panels heaped before it; the
    Resistance's amber spray paint over it: a great double chevron, slashes and an arrow pointing in, an amber work
    lamp hung by the hole."""
    out = []
    wl, rb, bp = Field("Wall"), Field("Rubble"), Field("Bent")
    glows = G("glow_ember", "glow_red")
    rng = np.random.default_rng(seed)
    L, H, T = 1.6, 2.5, 0.2
    wl.add(RoundBox((0, 0.0, H / 2), (L, T, H / 2), 0.03), k=0.0)
    for x in np.arange(-L + 0.4, L, 0.8):                            # panel seams and ribs
        wl.add(RoundBox((x, -T, H / 2), (0.04, 0.03, H / 2), 0.01), k=0.0, label=7)
    for z in (0.15, H - 0.12):
        wl.add(RoundBox((0, -T, z), (L, 0.04, 0.05), 0.01), k=0.0, label=7)
    hole = v3((0.15, 0.0, 1.0))
    wl.sub(Ellipsoid(hole, (0.72, 0.6, 0.85), **wob(3.0, 0.12, seed)), k=0.02)
    wl.paint(Ellipsoid(hole - v3((0, 0.2, 0)), (1.05, 0.5, 1.15), **wob(3.0, 0.15, seed + 1)), 9)          # the scorch round it
    for k in range(9):                                                # bent plates curling out round the hole
        a = 2 * math.pi * k / 9 + rng.uniform(-0.2, 0.2)
        d = v3((math.cos(a), 0, math.sin(a)))
        q = hole + d * v3((0.72, 0, 0.85))
        if q[2] < 0.15:
            continue
        nrm = unit(v3((0, -1, 0)) + d * 0.6)
        plate(bp, q - v3((0, 0.18, 0)) + d * 0.08, nrm, d, rng.uniform(0.18, 0.3), rng.uniform(0.25, 0.4), t=0.02, bow=0.06)
    rb.add(Ellipsoid((0.15, -0.55, 0.0), (0.95, 0.45, 0.25), **wob(4.0, 0.08, seed + 2)), k=0.0)          # the rubble heap
    for i in range(10):
        q = v3((rng.uniform(-0.75, 0.95), rng.uniform(-1.0, -0.2), rng.uniform(0.05, 0.22)))
        rb.add(RoundBox(q, (rng.uniform(0.08, 0.18), rng.uniform(0.06, 0.14), rng.uniform(0.05, 0.1)), 0.02, R=euler(*rng.uniform(-0.6, 0.6, 3)),
                        **wob(9.0, 0.015, seed + i)), k=0.02)
    for i in range(3):
        plate(bp, (rng.uniform(-0.8, 0.9), rng.uniform(-1.1, -0.5), 0.12), unit(v3((rng.uniform(-0.3, 0.3), -0.3, 1))), (1, 0.2, 0), 0.4, 0.28, t=0.02, bow=0.04)
    chevron(wl, (-1.15, -T, 1.75), (0, -1, 0), 0.55, 0.3, t=0.09, n=2)          # the Resistance's spray paint
    for (a, b) in (((1.0, 1.9), (1.45, 1.55)), ((1.05, 1.65), (1.5, 1.3))):
        slash(wl, (a[0], -T, a[1]), (b[0], -T, b[1]), 0.07)
    slash(wl, (-1.4, -T, 0.6), (-0.95, -T, 0.6), 0.08)
    chevron(wl, (-0.88, -T, 0.6), (0, -1, 0), 0.24, 0.12, t=0.08, up=(1, 0, 0))
    lp = v3((-0.75, -T - 0.12, 2.05))                                  # an amber work lamp hung by the hole
    seg(bp, lp + v3((0, 0.12, 0.15)), lp + v3((0, 0, 0.15)), 0.012)
    bp.add(Cylinder(lp + Z * 0.06, 0.06, 0.1, rr=0.02), k=0.0, label=7)
    glows["glow_ember"].add(Sphere(lp - Z * 0.02, 0.06), k=0.0)
    bp.add(Chain([lp + v3((0, 0.05, 0.12)), lp + v3((0.05, 0.08, -0.6)), v3((-0.55, -T - 0.1, 0.03)), v3((-0.3, -0.6, 0.03))], [0.01] * 4, k=0.04), k=0.0, label=7)
    glows["glow_red"].add(Sphere((1.35, -T - 0.02, 2.3), 0.04), k=0.0)                 # the hall's alarm light, still flashing
    ground_cut(wl, -0.02)
    ground_cut(rb, -0.02)
    ground_cut(bp, -0.02)
    out += [("Wall", wl, fine(0.008, 0.016), "panel_wall"), ("Rubble", rb, fine(0.007, 0.014), "concrete"), ("Bent", bp, fine(0.005, 0.01), "panel_wall")]
    return finish_glows(out, glows)


BREACH_LAMP = (-0.75, -0.32, 2.03)                                       # the amber lamp by the hole (Blender, prop-local)


# ------------------------------------------------------------------------------------------------ Server Hall: no-build zones
def rack_row(seed=0, variant=0):
    """A row of the robots' server racks (no-build zone): variant 0 four cabinets end to end under their cable tray
    (one door open), end panels with the robots' orange mark; variant 1 three cabinets and the end one pulled out and
    toppled, its blades spilt."""
    out = []
    f, dr, tr, cb = Field("Cabinets"), Field("Doors"), Field("Tray"), Field("Cables")
    leds = G("glow_cyan", "glow_red", prefix="Led")
    W = 0.3
    n = 4 if variant == 0 else 3
    xs = [(i - (n - 1) / 2) * (2 * W + 0.02) for i in range(n)]
    if variant == 1:
        xs = [x + 0.1 for x in xs]
    for i, x in enumerate(xs):
        robo_rack(f, dr, leds, (x, 0, 0), 0.0, W=W, door=("open" if (i == 1 and variant == 0) else "closed"), seed=seed + i, red=0.3)
    x0, x1 = xs[0] - W - 0.03, xs[-1] + W + 0.03
    for x in (x0, x1):                                                # end panels
        box(f, (x, 0, 0.88), (0.025, 0.46, 0.86), 0.01)
        f.paint(RoundBox((x, 0, 1.3), (0.05, 0.2, 0.2), 0.0, R=euler(0.785, 0, 0)), 5)
    for sy in (-1, 1):
        seg(tr, (x0, sy * 0.13, 1.92), (x1, sy * 0.13, 1.92), 0.012)
    for x in np.linspace(x0, x1, 2 * n + 2):
        seg(tr, (x, -0.13, 1.92), (x, 0.13, 1.92), 0.009)
    for x in (x0 + 0.1, x1 - 0.1):
        seg(tr, (x, 0.0, 1.72), (x, 0.0, 1.92), 0.012)
    cable_bundle(cb, [(x0 - 0.1, 0, 1.96), ((x0 + x1) / 2, 0.0, 1.97), (x1 + 0.1, 0, 1.96)], n=5, r=0.025, seed=seed, spread=0.06)
    cable_bundle(cb, [(x1 + 0.1, 0, 1.96), (x1 + 0.25, 0.05, 1.5), (x1 + 0.3, 0.1, 0.04), (x1 + 0.6, 0.2, 0.04)], n=3, r=0.025, seed=seed + 1, spread=0.05)
    if variant == 1:
        place_parts(out, toppled_rack(seed + 7), (0.0, -1.0, 0), Rz(0.12), rename={"Cabinet": "Toppled", "Door": "TDoor", "Cables": "TCables",
                                                                                   "LedCyan": "TCyan", "LedRed": "TRed"})
    ground_cut(f, -0.01)
    out += [("Cabinets", f, fine(0.006, 0.012), "graphite"), ("Doors", dr, fine(0.005, 0.01), "perforated"), ("Tray", tr, fine(0.005, 0.01), "galv"),
            ("Cables", cb, fine(0.005, 0.01), "cables")]
    return finish_glows(out, leds)


def mainframe_unit(seed=0):
    """A mainframe (machine zone): a broad white block with a core window glowing cyan over its data drums, banks of
    blinking lights, a screen, side vents, thick cables into the floor, the robots' hazard stripes round its foot."""
    out = []
    hs, dm, cb = Field("Housing"), Field("Drums"), Field("Cables")
    glows = G("glow_cyan", "glow_red", "glow_screen")
    rng = np.random.default_rng(seed)
    HX, HY, HZ = 0.95, 0.55, 0.8
    hs.add(RoundBox((0, 0, HZ + 0.06), (HX, HY, HZ), 0.06), k=0.0)
    hs.add(RoundBox((0, 0, 0.06), (HX + 0.05, HY + 0.05, 0.06), 0.02), k=0.0, label=7)
    hs.paint(RoundBox((0, 0, 0.15), (HX + 0.1, HY + 0.1, 0.05), 0.0), 8)
    hs.add(RoundBox((0, 0, 2 * HZ + 0.12), (HX - 0.15, HY - 0.1, 0.08), 0.04), k=0.02, label=7)
    hs.sub(RoundBox((-0.35, -HY, HZ + 0.25), (0.42, 0.12, 0.45), 0.06), k=0.01)               # the core window and its drums
    glows["glow_cyan"].add(RoundBox((-0.35, -HY + 0.1, HZ + 0.25), (0.4, 0.01, 0.43), 0.04), k=0.0)
    for i, z in enumerate((HZ - 0.02, HZ + 0.52)):
        for x in (-0.55, -0.15):
            dm.add(Cylinder((x, -HY + 0.05, z), 0.15, 0.04, rr=0.01, R=RY), k=0.0)
            dm.add(Cylinder((x, -HY + 0.03, z), 0.05, 0.03, rr=0.008, R=RY), k=0.0, label=6)
    for j in range(6):                                                  # light banks and the screen on the right half
        for i in range(5):
            if rng.random() < 0.8:
                glows["glow_red" if rng.random() < 0.3 else "glow_cyan"].add(RoundBox((0.25 + i * 0.12, -HY - 0.005, 0.55 + j * 0.13), (0.035, 0.006, 0.012), 0.004), k=0.0)
    screen(hs, glows["glow_screen"], (0.5, -HY - 0.005, 1.48), (0, -1, 0), 0.5, 0.18, bezel=0.015, depth=0.015)
    hs.paint(RoundBox((0.5, -HY, 0.32), (0.4, 0.05, 0.03), 0.0), 5)
    for sx in (-1, 1):                                                 # side vents
        for j in range(6):
            hs.sub(RoundBox((sx * HX, 0.0, 0.5 + j * 0.15), (0.03, HY - 0.15, 0.025), 0.01), k=0.0)
    for i, x in enumerate((-0.5, 0.0, 0.5)):
        cable_bundle(cb, [(x, HY - 0.05, 2 * HZ + 0.1), (x, HY + 0.3, 2 * HZ - 0.2), (x * 1.2, HY + 0.45, 0.04), (x * 1.3, HY + 0.9, 0.04)],
                     n=2, r=0.045, seed=seed + i, spread=0.06)
    ground_cut(hs, -0.02)
    ground_cut(cb, -0.02)
    out += [("Housing", hs, fine(0.007, 0.014), "white_tech"), ("Drums", dm, fine(0.005, 0.01), "chrome"), ("Cables", cb, fine(0.005, 0.01), "cables")]
    return finish_glows(out, glows)


def power_unit(seed=0):
    """A power unit (machine zone): a graphite transformer cabinet ribbed with cooling fins, white insulators and bus
    bars on its roof, thick armoured cables down into the floor, red warning lights, hazard placards, a cyan meter."""
    out = []
    hs, fn, ins, cb = Field("Housing"), Field("Fins"), Field("Insulators"), Field("Cables")
    glows = G("glow_red", "glow_cyan")
    HX, HY, HZ = 0.8, 0.5, 0.65
    hs.add(RoundBox((0, 0, HZ + 0.12), (HX, HY, HZ), 0.05), k=0.0)
    box(hs, (0, 0, 0.06), (HX + 0.15, HY + 0.15, 0.06), 0.02, label=7)
    hs.paint(RoundBox((0, 0, 0.16), (HX + 0.1, HY + 0.1, 0.05), 0.0), 8)
    for sy in (-1, 1):                                                  # fins down the long sides
        for i in range(11):
            x = -HX + 0.12 + i * (2 * HX - 0.24) / 10
            fn.add(RoundBox((x, sy * (HY + 0.07), HZ + 0.1), (0.012, 0.08, HZ - 0.12), 0.006), k=0.0)
    for i, x in enumerate((-0.45, 0.0, 0.45)):                           # insulators and bus bars on the roof
        for z in range(4):
            ins.add(Cylinder((x, 0.0, 2 * HZ + 0.18 + z * 0.07), 0.09 - z * 0.008, 0.035, rr=0.012), k=0.0)
        seg(hs, (x, 0.0, 2 * HZ + 0.15), (x, 0.0, 2 * HZ + 0.5), 0.02, label=6)
        seg(hs, (x, 0.0, 2 * HZ + 0.5), (x, 0.45, 2 * HZ + 0.5), 0.02, label=6)
    hs.paint(RoundBox((-0.3, -HY, HZ + 0.4), (0.16, 0.08, 0.16), 0.0, R=euler(0, 0.785, 0)), 5)
    hs.paint(RoundBox((0.3, -HY, HZ + 0.4), (0.16, 0.08, 0.16), 0.0, R=euler(0, 0.785, 0)), 5)
    for sx in (-1, 1):
        glows["glow_red"].add(Sphere((sx * (HX - 0.12), -HY - 0.02, 2 * HZ + 0.02), 0.04), k=0.0)
    screen(hs, glows["glow_cyan"], (0.0, -HY - 0.005, HZ + 0.5), (0, -1, 0), 0.22, 0.12, bezel=0.015, depth=0.015)
    for i, x in enumerate((-0.45, 0.0, 0.45)):
        cable_bundle(cb, [(x, 0.45, 2 * HZ + 0.5), (x, 0.75, 2 * HZ + 0.1), (x * 1.1, 0.9, 0.05), (x * 1.2, 1.3, 0.05)], n=1, r=0.055, seed=seed + i, spread=0.0)
    ground_cut(hs, -0.02)
    ground_cut(cb, -0.02)
    out += [("Housing", hs, fine(0.007, 0.014), "graphite"), ("Fins", fn, fine(0.005, 0.01), "steel"), ("Insulators", ins, fine(0.004, 0.008), "white_tech"),
            ("Cables", cb, fine(0.005, 0.01), "cables")]
    return finish_glows(out, glows)


# ------------------------------------------------------------------------------------------------ The Core: scatter
def energy_conduit(seed=0, L=1.5, h=0.55):
    """An energy conduit arching out of the floor and back in (along X): an armoured dark pipe in segments, cyan light
    glowing through the seams between them, heavy collars where it meets the floor."""
    out = []
    cd, cl = Field("Conduit"), Field("Collars")
    glows = G("glow_cyan")
    n = 9
    pts = [v3((-L / 2 + L * i / (n - 1), 0, h * math.sin(math.pi * i / (n - 1)) - 0.05)) for i in range(n)]
    cd.add(Chain(pts, [0.11] * n, k=0.05), k=0.0)
    for i in range(1, n - 1):                                          # glowing seams between the segments
        d = unit(pts[i + 1] - pts[i - 1])
        q = (pts[i] + pts[i + 1]) / 2 if i < n - 2 else pts[i]
        cd.sub(Cylinder(q, 0.13, 0.03, R=rot_from_axes(z_axis=d)), k=0.0)
        glows["glow_cyan"].add(Cylinder(q, 0.105, 0.028, rr=0.006, R=rot_from_axes(z_axis=d)), k=0.0)
        cd.add(Torus(pts[i], 0.115, 0.018, R=rot_from_axes(z_axis=d)), k=0.0, label=7)
    for sx in (-1, 1):
        cl.add(Cylinder((sx * L / 2, 0, 0.05), 0.2, 0.1, rr=0.03), k=0.0)
        for k in range(6):
            a = 2 * math.pi * k / 6
            cl.add(Cylinder((sx * L / 2 + math.cos(a) * 0.16, math.sin(a) * 0.16, 0.11), 0.018, 0.03, rr=0.005), k=0.0, label=6)
    cd.paint(Cylinder((0, 0, h), 0.2, 0.15, R=RX), 5)
    ground_cut(cd, -0.02)
    ground_cut(cl, -0.01)
    out += [("Conduit", cd, fine(0.005, 0.01), "core_dark"), ("Collars", cl, fine(0.004, 0.008), "gunmetal")]
    return finish_glows(out, glows)


def data_spire(seed=0, H=1.3, s=1.0):
    """A small data spire: a tapering hexagonal obelisk on its stepped foot, cyan circuit traces climbing its faces in
    angled runs, a red light at its tip."""
    out = []
    sp, bs = Field("Spire"), Field("Base")
    glows = G("glow_cyan", "glow_red")
    H, rb, rt = H * s, 0.2 * s, 0.07 * s
    bs.add(hexagon((0, 0), 0.34 * s, 0.1 * s), k=0.0)
    bs.add(hexagon((0, 0), 0.27 * s, 0.1 * s, z0=0.08 * s), k=0.01, label=7)
    pl = [((0, 0, 0.16 * s), (0, 0, -1))]
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3
        n = unit(v3((math.cos(a), math.sin(a), (rb - rt) / H)))
        pl.append(((math.cos(a) * rb * 0.87, math.sin(a) * rb * 0.87, 0.16 * s), n))
        pl.append(((0, 0, 0.16 * s + H), unit(v3((math.cos(a), math.sin(a), 1.4)))))
    sp.add(convex(pl, (-0.4 * s, -0.4 * s, 0.1 * s), (0.4 * s, 0.4 * s, H + 0.4 * s)), k=0.0)
    rng = np.random.default_rng(seed)
    for i in range(6):                                                   # circuit traces up its faces
        a = math.pi / 6 + i * math.pi / 3
        d = v3((math.cos(a), math.sin(a), 0))
        side = np.cross(Z, d)
        z = 0.25 * s
        x = rng.uniform(-0.3, 0.3)
        pts = []
        while z < H * 0.8:
            r = rb + (rt - rb) * (z - 0.16 * s) / H
            pts.append(d * (r * 0.87 + 0.004) + side * (x * r) + Z * z)
            z += rng.uniform(0.12, 0.22) * s
            x = float(np.clip(x + rng.choice([-0.35, 0.0, 0.35]), -0.45, 0.45))
        for p, q in zip(pts[:-1], pts[1:]):
            m = v3((p[0], p[1], q[2] - 0.04 * s)) if abs(x) > 0 else q
            strip(glows["glow_cyan"], p, m, 0.018 * s, up=d)
            strip(glows["glow_cyan"], m, q, 0.018 * s, up=d)
        if pts:
            glows["glow_cyan"].add(Sphere(pts[-1], 0.022 * s), k=0.0)
    glows["glow_red"].add(Sphere((0, 0, 0.16 * s + H + 0.02 * s), 0.05 * s), k=0.0)
    ground_cut(bs, -0.01)
    out += [("Spire", sp, fine(0.004, 0.008), "core_dark"), ("Base", bs, fine(0.004, 0.008), "gunmetal")]
    return finish_glows(out, glows)


def core_cables(seed=0, L=1.8):
    """A run of the Core's heavy power cables over the floor: thick black cables snaking side by side, clamped to the
    floor by heavy brackets, one with a cyan-lit coupling."""
    out = []
    cb, br = Field("Cables"), Field("Clamps")
    glows = G("glow_cyan")
    pts = [(-L / 2, -0.15, 0.06), (-L / 6, 0.15, 0.06), (L / 6, -0.1, 0.06), (L / 2, 0.12, 0.06)]
    cable_bundle(cb, pts, n=4, r=0.055, seed=seed, spread=0.12, labels=(0, 0, 5, 0))
    for t in (0.25, 0.75):
        q = v3(pts[1]) * (1 - t) + v3(pts[2]) * t
        box(br, q + Z * 0.08, (0.06, 0.24, 0.035), 0.012)
        for sy in (-1, 1):
            box(br, q + v3((0, sy * 0.22, 0.04)), (0.06, 0.03, 0.05), 0.01)
    c = v3(pts[2]) * 0.6 + v3(pts[3]) * 0.4
    br.add(Cylinder(c + Z * 0.02, 0.1, 0.18, rr=0.03, R=RX), k=0.0, label=7)
    glows["glow_cyan"].add(Torus(c + Z * 0.02, 0.1, 0.014, R=RX), k=0.0)
    ground_cut(cb, -0.02)
    ground_cut(br, -0.01)
    out += [("Cables", cb, fine(0.005, 0.01), "cables"), ("Clamps", br, fine(0.004, 0.008), "gunmetal")]
    return finish_glows(out, glows)


def debris(seed=0, variant=0):
    """Battle debris on the Core's floor (variant 0: torn-up floor plates and a bent beam among chunks of the floor;
    variant 1: shattered white robot armour and frame parts, scorched)."""
    out = []
    rng = np.random.default_rng(seed)
    if variant == 0:
        fp, ch = Field("Plates"), Field("Chunks")
        for i in range(3):
            c = v3((rng.uniform(-0.45, 0.45), rng.uniform(-0.3, 0.3), 0.05 + i * 0.03))
            n = unit(v3((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), 1)))
            plate(fp, c, n, (1, rng.uniform(-0.5, 0.5), 0), rng.uniform(0.35, 0.5), rng.uniform(0.3, 0.42), t=0.025, bow=0.03)
        seg(fp, (-0.5, 0.35, 0.05), (0.2, 0.15, 0.25), 0.04)
        seg(fp, (0.2, 0.15, 0.25), (0.55, 0.3, 0.06), 0.04)
        for i in range(7):
            q = v3((rng.uniform(-0.6, 0.6), rng.uniform(-0.45, 0.45), rng.uniform(0.02, 0.08)))
            ch.add(RoundBox(q, tuple(rng.uniform(0.04, 0.1, 3)), 0.015, R=euler(*rng.uniform(-0.8, 0.8, 3)), **wob(10.0, 0.01, seed + i)), k=0.0)
        fp.paint(Sphere((0.0, 0.0, 0.0), 0.4, **wob(5.0, 0.1, seed)), 9)
        ground_cut(fp, -0.01)
        ground_cut(ch, -0.01)
        out += [("Plates", fp, fine(0.004, 0.008), "core_dark"), ("Chunks", ch, fine(0.004, 0.008), "core_dark")]
    else:
        ar, fr = Field("Armour"), Field("Frame")
        for i in range(5):
            c = v3((rng.uniform(-0.5, 0.5), rng.uniform(-0.35, 0.35), 0.06))
            n = unit(v3((rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), 1)))
            plate(ar, c, n, (rng.uniform(-1, 1), 1, 0), rng.uniform(0.18, 0.32), rng.uniform(0.14, 0.26), t=0.025, bow=0.04)
            if i % 2:                                                    # a hazard-orange stripe across it
                ar.paint(RoundBox(c, (0.03, 0.4, 0.2), 0.0, R=Rz(rng.uniform(0, 3))), 5)
        ar.paint(Sphere((0.2, -0.1, 0.0), 0.16, **wob(5.0, 0.05, seed)), 9)
        for i in range(4):
            a = v3((rng.uniform(-0.5, 0.5), rng.uniform(-0.4, 0.4), 0.04))
            b = a + v3((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0.0, 0.15)))
            seg(fr, a, b, 0.025)
            fr.add(Sphere(b, 0.04), k=0.01)
        cable_bundle(fr, [(-0.2, 0.0, 0.04), (0.0, 0.25, 0.1), (0.3, 0.3, 0.03)], n=3, r=0.012, seed=seed, spread=0.02, labels=(5, 9, 8))
        ground_cut(ar, -0.01)
        ground_cut(fr, -0.01)
        out += [("Armour", ar, fine(0.004, 0.008), "robot_white"), ("Frame", fr, fine(0.004, 0.008), "gunmetal")]
    return out


def robot_parts(seed=0):
    """Wrecked robot parts: a robot's torso torn off at the waist lying on its side, one arm still on it and its
    helmet's visor glowing a dim red, its legs lying apart; scorched."""
    out = []
    # the torso lying on its side (its up along -X, its front toward -Y), legs and one arm gone
    R = np.stack([v3((0, 0, 1)), v3((0, 1, 0)), v3((-1, 0, 0))], axis=1)       # local x -> up, y -> y, z -> -x
    J = robot_figure(out, (0.75, 0.0, 0.22), R, 1.0, {"lean": 0.0, "head": (0.6, 0.2), "arms": {1: (0.6, 0.2, 0.9)}, "z": 0.0},
                     prefix="Bot", missing=("arm-1", "leg+1", "leg-1"), torn=True, seed=seed)
    lg, ls = Field("LegFrame"), Field("LegPlates")                      # a leg lying apart
    a, b, c = v3((-0.75, 0.35, 0.09)), v3((-0.35, 0.45, 0.09)), v3((0.05, 0.38, 0.08))
    seg(lg, a, b, 0.055)
    seg(lg, b, c, 0.05)
    lg.add(Sphere(b, 0.065), k=0.01)
    ls.add(RoundCone(a + (b - a) * 0.15, b - (b - a) * 0.15, 0.095, 0.08), k=0.0)
    ls.add(RoundCone(b + (c - b) * 0.12, c - (c - b) * 0.15, 0.085, 0.068), k=0.0)
    ls.add(RoundBox(c + v3((0.08, 0, -0.02)), (0.07, 0.13, 0.04), 0.03, R=Rz(math.pi / 2)), k=0.01, label=7)
    ls.paint(Sphere(a, 0.12), 9)
    for f in (lg, ls):
        ground_cut(f, -0.01)
    for (n, f, v, m) in out:
        ground_cut(f, -0.01)
    out += [("LegFrame", lg, fine(0.004, 0.008), "gunmetal"), ("LegPlates", ls, fine(0.004, 0.008), "robot_white")]
    return out


def scorch_mark(seed=0, w=1.0):
    """A scorch mark on the floor (ground cover): a blackened splash, a few glowing embers of molten slag in it."""
    out = []
    sc = Field("Scorch")
    glows = G("glow_amber")
    rng = np.random.default_rng(seed)

    def fn(P):
        r = np.sqrt((P[:, 0] / F32(w * 0.5)) ** 2 + (P[:, 1] / F32(w * 0.42)) ** 2)
        rr = r + NOISE.fbm(P * F32(3.0 / w), 3) * F32(0.5) + np.cos(np.arctan2(P[:, 1], P[:, 0]) * F32(7.0)) * F32(0.12)
        return np.maximum((rr - F32(1.0)) * F32(w * 0.35), np.abs(P[:, 2]) - F32(0.008)).astype(F32)
    sc.add(Func(fn, (-w, -w, -0.03), (w, w, 0.03)), k=0.0)
    for i in range(4):
        q = v3((rng.uniform(-0.25, 0.25) * w, rng.uniform(-0.2, 0.2) * w, 0.004))
        glows["glow_amber"].add(Ellipsoid(q, (0.03, 0.02, 0.008), R=Rz(rng.uniform(0, 3))), k=0.0)
    ground_cut(sc, -0.005)
    out += [("Scorch", sc, fine(0.004, 0.008), "scorch")]
    return finish_glows(out, glows)


def data_crystals(seed=0, s=1.0):
    """Data crystals: a cluster of glowing cyan crystals grown out of a dark data node on the floor, ringed by a
    gunmetal collar."""
    out = []
    nd, cr = Field("Node"), Field("Crystals")
    nd.add(Cylinder((0, 0, 0.05 * s), 0.25 * s, 0.1 * s, rr=0.03 * s), k=0.0)
    nd.add(Torus((0, 0, 0.1 * s), 0.25 * s, 0.03 * s), k=0.0, label=7)
    ice_shards(cr, (0, 0, 0.05 * s), 5, 0.55 * s, 0.07 * s, seed, spread=0.12 * s, tilt=0.6)
    ice_shards(cr, (0.3 * s, 0.15 * s, 0.0), 2, 0.25 * s, 0.04 * s, seed + 1, spread=0.04 * s, tilt=0.5)
    ground_cut(nd, -0.01)
    ground_cut(cr, -0.01)
    out += [("Node", nd, fine(0.004, 0.008), "core_dark"), ("Crystals", cr, fine(0.004, 0.008), "glow_cyan")]
    return out


# ------------------------------------------------------------------------------------------------ The Core: landmarks
def giant_spire(seed=0):
    """The giant data spire (4.6 m): a faceted dark obelisk on a stepped hexagonal base, rings of cyan light girdling it
    on their mounts, circuit traces climbing its faces, a red core blazing in a cage near its tip, heavy cables pouring
    into its foot."""
    out = []
    sp, bs, rg, cb = Field("Spire"), Field("Base"), Field("Mounts"), Field("Cables")
    glows = G("glow_cyan", "glow_red")
    s = 2.6
    parts = data_spire(seed, H=1.55, s=s)
    for (n, f, v, m) in parts:                                           # the small spire, scaled up
        nm = {"Spire": "Spire", "Base": "Base", "Cyan": "Cyan", "Red": "Red"}[n]
        if nm in ("Cyan", "Red"):
            place(glows["glow_cyan" if nm == "Cyan" else "glow_red"], f, (0, 0, 0))
        else:
            place(sp if nm == "Spire" else bs, f, (0, 0, 0))
    bs.add(hexagon((0, 0), 1.25, 0.12), k=0.0)
    bs.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(1.12)) - F32(0.05)).astype(F32), (-1.5, -1.5, -0.1), (1.5, 1.5, 0.3)), 5)
    H = 0.16 * s + 1.55 * s
    for z, R in ((1.2, 0.62), (2.4, 0.5), (3.4, 0.38)):                  # rings of light on their mounts
        glows["glow_cyan"].add(Torus((0, 0, z), R, 0.035), k=0.0)
        rg.add(Torus((0, 0, z), R, 0.05), k=0.0)
        rg.sub(Torus((0, 0, z), R, 0.032), k=0.0)
        for k in range(3):
            a = 2 * math.pi * k / 3 + z
            r_in = 0.52 * (1 - (z - 0.42) / (H - 0.42) * 0.65) - 0.02
            seg(rg, (math.cos(a) * r_in, math.sin(a) * r_in, z), (math.cos(a) * R, math.sin(a) * R, z), 0.025)
    zc = H - 0.55                                                         # the red core in its cage near the tip
    sp.sub(Cylinder((0, 0, zc), 0.4, 0.3), k=0.02)
    glows["glow_red"].add(Ellipsoid((0, 0, zc), (0.17, 0.17, 0.13)), k=0.0)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        seg(rg, (math.cos(a) * 0.17, math.sin(a) * 0.17, zc - 0.17), (math.cos(a) * 0.17, math.sin(a) * 0.17, zc + 0.17), 0.018)
    for i, a in enumerate((0.4, 2.2, 3.9)):                               # cables pouring into its foot
        d = v3((math.cos(a), math.sin(a), 0))
        cable_bundle(cb, [d * 0.7 + Z * 0.15, d * 1.1 + Z * 0.1, d * 1.6 + Z * 0.06, d * 2.0 + Z * 0.05], n=3, r=0.05, seed=seed + i, spread=0.08)
    ground_cut(bs, -0.02)
    ground_cut(cb, -0.02)
    out += [("Spire", sp, fine(0.008, 0.016), "core_dark"), ("Base", bs, fine(0.007, 0.014), "gunmetal"), ("Mounts", rg, fine(0.005, 0.01), "gunmetal"),
            ("Cables", cb, fine(0.006, 0.012), "cables")]
    return finish_glows(out, glows)


SPIRE_CORE = (0.0, 0.0, 0.16 * 2.6 + 1.55 * 2.6 - 0.55)               # the giant spire's red core (Blender, prop-local)


def cable_column(seed=0):
    """A towering cable-bundle column (4.2 m): a twisting trunk of heavy cables rising from the floor into the dark,
    splaying out at its foot into roots that dive into the floor, bound by clamp rings with cyan lights, frayed ends
    sparking at a break part way up, a crown of cables fanning out at the top."""
    out = []
    cb, cl = Field("Cables"), Field("Clamps")
    glows = G("glow_cyan", "glow_red")
    rng = np.random.default_rng(seed)
    H = 4.2
    n = 9
    for i in range(n):
        ph = 2 * math.pi * i / n
        r0 = rng.uniform(0.17, 0.26)
        pts = []
        for t in np.linspace(0, 1, 9):
            a = ph + t * 2.4
            r = r0 * (1.0 + 0.25 * math.sin(t * 7 + i))
            pts.append(v3((math.cos(a) * r, math.sin(a) * r, 0.35 + t * (H - 0.6))))
        foot = v3((math.cos(ph - 0.4) * 0.8, math.sin(ph - 0.4) * 0.8, 0.0))   # the roots splaying into the floor
        top = pts[-1] + v3((math.cos(ph + 2.4) * 0.6, math.sin(ph + 2.4) * 0.6, 0.35))
        pts = [foot + Z * 0.0, (foot + pts[0]) / 2 + Z * 0.08] + pts + [top]
        cb.add(Chain(pts, [0.075] * len(pts), k=0.04), k=0.0, label=(0, 0, 5, 0, 9)[i % 5])
    for z in (0.8, 1.9, 3.2):                                             # clamp rings with their lights
        cl.add(Torus((0, 0, z), 0.42, 0.07), k=0.0)
        cl.add(Cylinder((0, 0, z), 0.45, 0.1, rr=0.03), k=0.0)
        cl.sub(Cylinder((0, 0, z), 0.36, 0.2), k=0.0)
        for k in range(6):
            a = 2 * math.pi * k / 6 + z
            glows["glow_cyan"].add(RoundBox((math.cos(a) * 0.46, math.sin(a) * 0.46, z), (0.012, 0.05, 0.025), 0.01, R=Rz(a)), k=0.0)
    glows["glow_red"].add(Sphere((0.48, 0.0, 3.2), 0.04), k=0.0)
    ground_cut(cb, -0.02)
    out += [("Cables", cb, fine(0.008, 0.016), "cables"), ("Clamps", cl, fine(0.006, 0.012), "core_dark")]
    return finish_glows(out, glows)


def wrecked_tank(seed=0):
    """A wrecked Resistance tank (nose toward +X), knocked out in the battle for the Core: see res_tank; on a
    scorch mark with debris round it."""
    out = []
    pts = res_tank(out, (0, 0, 0), 0.0, wrecked=True, seed=seed)
    sc = Field("Scorch")
    sc.add(Func(lambda P: np.maximum((np.sqrt((P[:, 0] / F32(1.6)) ** 2 + (P[:, 1] / F32(1.1)) ** 2) + NOISE.fbm(P * F32(2.0), 3) * F32(0.4) - F32(1.0)) * F32(0.5),
                                     np.abs(P[:, 2]) - F32(0.008)).astype(F32), (-2.2, -1.6, -0.03), (2.2, 1.6, 0.03)), k=0.0)
    ground_cut(sc, -0.005)
    out.append(("Scorch", sc, fine(0.006, 0.012), "scorch"))
    place_parts(out, debris(seed + 1, 0), (-1.4, 0.7, 0), Rz(0.5), rename={"Plates": "DPlates", "Chunks": "DChunks"})
    return out


TANK_SMOKE = (-0.3, 0.23, 1.07)                                        # the tank's open hatch (Blender, prop-local; see res_tank)


def fallen_giant(seed=0):
    """A fallen robot giant (4 m long, head toward +X): one of the robots' great war machines lying on its back where
    the Resistance brought it down, one knee drawn up, an arm flung up and clawing at the air, the other out across
    the floor, its head lolled toward the camera with its visor still burning red, its chest plate torn open on the
    frame and core inside (sparks), plates shed round it, a scorched crater under it."""
    out = []
    s = 2.0
    Rb = np.stack([v3((0, -1, 0)), v3((0, 0, -1)), v3((1, 0, 0))], axis=1)    # lying on its back, head toward +X, face up
    J = robot_figure(out, (-1.9, 0.0, 0.25 * s), Rb, s,
                     {"lean": 0.0, "head": (0.65, -0.2), "arms": {1: (1.7, 0.35, 0.9), -1: (0.1, 1.35, 0.35)},
                      "legs": {1: (0.95, 0.1, 1.6), -1: (0.1, 0.15, 0.15)}},
                     prefix="Giant", torn=True, missing=(), seed=seed)
    for (n, f, v, m) in out:
        ground_cut(f, -0.02)
    sc = Field("Crater")
    sc.add(Func(lambda P: np.maximum((np.sqrt((P[:, 0] / F32(2.4)) ** 2 + (P[:, 1] / F32(1.5)) ** 2) + NOISE.fbm(P * F32(1.5), 3) * F32(0.35) - F32(1.0)) * F32(0.6),
                                     np.abs(P[:, 2]) - F32(0.01)).astype(F32), (-3.2, -2.2, -0.03), (3.2, 2.2, 0.03)), k=0.0)
    ground_cut(sc, -0.005)
    out.append(("Crater", sc, fine(0.007, 0.014), "scorch"))
    place_parts(out, debris(seed + 1, 1), (0.6, -1.15, 0), Rz(0.3), rename={"Armour": "Shed", "Frame": "ShedFrame"})
    place_parts(out, debris(seed + 2, 1), (-1.5, 1.2, 0), Rz(2.0), rename={"Armour": "Shed", "Frame": "ShedFrame"})
    return out, J


def _giant():
    return fallen_giant(846)[0]


def giant_sparks():
    """Where the fallen giant's sparks fly (Blender, prop-local): its torn chest, a shoulder."""
    _, J = fallen_giant(846)
    return [tuple(round(float(x), 3) for x in J["core"]), tuple(round(float(x), 3) for x in J["shoulder-1"])]


# ------------------------------------------------------------------------------------------------ The Core: no-build zones
def energy_pillar(seed=0, variant=0):
    """An energy pillar (no-build zone, 2.8 m): a hexagonal data column on a stepped base, three rings of cyan light
    floating round it on their emitter arms (variant 0), or drums of light stacked up it between armoured bands
    (variant 1); a red light at its crown, electrodes where the arcs crackle, cables into the floor."""
    out = []
    cl, bs, rg = Field("Column"), Field("Base"), Field("Emitters")
    glows = G("glow_cyan", "glow_red")
    bs.add(hexagon((0, 0), 0.85, 0.14), k=0.0)
    bs.add(hexagon((0, 0), 0.62, 0.14, z0=0.12), k=0.01, label=7)
    bs.paint(Func(lambda P: (np.abs(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - F32(0.75)) - F32(0.05)).astype(F32), (-1, -1, -0.1), (1, 1, 0.3)), 8)
    H = 2.6
    cl.add(hexagon((0, 0), 0.34, H, z0=0.2), k=0.0)
    cl.add(hexagon((0, 0), 0.42, 0.18, z0=H + 0.1), k=0.02, label=7)
    cl.add(Cylinder((0, 0, H + 0.36), 0.12, 0.12, rr=0.03), k=0.01, label=7)
    glows["glow_red"].add(Sphere((0, 0, H + 0.46), 0.08), k=0.0)
    sparks = []
    if variant == 0:
        for z, R in ((0.85, 0.62), (1.55, 0.56), (2.25, 0.5)):
            glows["glow_cyan"].add(Torus((0, 0, z), R, 0.04), k=0.0)
            for k in range(3):
                a = 2 * math.pi * k / 3 + z * 2
                d = v3((math.cos(a), math.sin(a), 0))
                seg(rg, d * 0.3 + Z * (z - 0.12), d * (R - 0.06) + Z * (z - 0.05), 0.025)
                rg.add(Sphere(d * (R - 0.04) + Z * (z - 0.04), 0.045), k=0.01, label=6)
            sparks.append((R, 0.0, z))
    else:
        for z in (0.6, 1.25, 1.9):
            cl.sub(Cylinder((0, 0, z + 0.25), 0.5, 0.36), k=0.02)
            glows["glow_cyan"].add(hexagon((0, 0), 0.3, 0.34, z0=z + 0.08), k=0.0)
            cl.add(Cylinder((0, 0, z + 0.06), 0.4, 0.06, rr=0.02), k=0.0, label=7)
            for k in range(6):
                a = 2 * math.pi * k / 6
                rg.add(RoundCone((math.cos(a) * 0.36, math.sin(a) * 0.36, z + 0.06), (math.cos(a) * 0.36, math.sin(a) * 0.36, z + 0.44), 0.02, 0.02), k=0.0)
            sparks.append((0.36, 0.0, z + 0.25))
    cl.paint(Func(lambda P: (np.abs(np.mod(P[:, 2], F32(0.5)) - F32(0.25)) - F32(0.02)).astype(F32), (-1, -1, 0.3), (1, 1, H)), 5)
    for i, a in enumerate((0.5, 2.6, 4.4)):
        d = v3((math.cos(a), math.sin(a), 0))
        cable_bundle(rg, [d * 0.55 + Z * 0.2, d * 0.9 + Z * 0.08, d * 1.25 + Z * 0.05], n=2, r=0.04, seed=seed + i, spread=0.05)
    ground_cut(bs, -0.02)
    ground_cut(rg, -0.02)
    out += [("Column", cl, fine(0.006, 0.012), "core_dark"), ("Base", bs, fine(0.006, 0.012), "gunmetal"), ("Emitters", rg, fine(0.005, 0.01), "gunmetal")]
    finish_glows(out, glows)
    return out


def _pillar_sparks():
    """Where the pillars' arcs crackle (Blender, prop-local): the ring emitters' tips (Pillar) or the drums' edges
    (Pillar_B), and the crown light."""
    a = []
    for z, R in ((0.85, 0.62), (1.55, 0.56), (2.25, 0.5)):
        t = 2 * math.pi * 0 / 3 + z * 2
        a.append((round(math.cos(t) * (R - 0.04), 3), round(math.sin(t) * (R - 0.04), 3), round(z - 0.04, 3)))
    b = [(0.3, 0.0, 0.85), (-0.15, 0.26, 1.5), (-0.15, -0.26, 2.15)]
    return {"Pillar": a + [(0.0, 0.0, 3.06)], "Pillar_B": b + [(0.0, 0.0, 3.06)]}


PILLAR_SPARKS = _pillar_sparks()


def wreck_robot(seed=0):
    """A wrecked robot (no-build zone): one of the white soldiers twice a man's height, slumped sitting against a heap
    of wreckage, head fallen forward, one arm torn off and lying beside it, its chest blasted open, scorched."""
    out = []
    s = 1.35
    Rw = Rz(math.pi * 0.15) @ euler(-0.35, 0, 0)                     # sitting back against the heap
    J = robot_figure(out, (0.0, 0.2, -0.85 * s + 0.15), Rw, s,
                     {"lean": -0.15, "head": (0.4, 0.75), "arms": {1: (0.25, 0.7, 0.4)},
                      "legs": {1: (1.45, 0.25, 0.4), -1: (1.25, 0.35, 1.1)}, "z": 0.95},
                     prefix="Bot", missing=("arm-1",), torn=True, seed=seed)
    for (n, f, v, m) in out:
        ground_cut(f, -0.02)
    hp = Field("Heap")                                                # the heap it slumps against
    hp.add(Ellipsoid((0.0, 0.85, 0.0), (1.0, 0.6, 0.55), **wob(2.5, 0.1, seed)), k=0.0)
    rng = np.random.default_rng(seed)
    for i in range(6):
        c = v3((rng.uniform(-0.8, 0.8), rng.uniform(0.5, 1.1), rng.uniform(0.2, 0.5)))
        plate(hp, c, unit(v3((rng.uniform(-1, 1), rng.uniform(-0.5, 0.5), 1))), (1, 0, 0), rng.uniform(0.3, 0.5), rng.uniform(0.25, 0.4), t=0.03, bow=0.03)
    ground_cut(hp, -0.02)
    out.append(("Heap", hp, fine(0.007, 0.014), "core_dark"))
    ag, ap = Field("ArmFrame"), Field("ArmPlates")                    # the torn-off arm lying beside it
    a, b, c = v3((0.9, -0.55, 0.1)), v3((1.3, -0.35, 0.1)), v3((1.65, -0.6, 0.09))
    seg(ag, a, b, 0.06 * s)
    ag.add(Sphere(b, 0.07 * s), k=0.01)
    ap.add(RoundCone(a + (b - a) * 0.15, b - (b - a) * 0.15, 0.1 * s, 0.085 * s), k=0.0)
    ap.add(RoundCone(b + (c - b) * 0.1, c, 0.1 * s, 0.08 * s), k=0.0)
    ag.add(RoundBox(c + v3((0.08, -0.04, 0)), (0.05 * s, 0.07 * s, 0.04 * s), 0.02, R=Rz(-0.6)), k=0.01)
    ap.paint(Sphere(a, 0.15), 9)
    ground_cut(ag, -0.01)
    ground_cut(ap, -0.01)
    out += [("ArmFrame", ag, fine(0.005, 0.01), "gunmetal"), ("ArmPlates", ap, fine(0.005, 0.01), "robot_white")]
    place_parts(out, scorch_mark(seed + 3, 2.2), (0.1, 0.1, 0), None, rename={"Scorch": "Scorch", "Amber": "Embers"})
    return out


def wreck_vehicle(seed=0):
    """A burnt-out Resistance armoured car (no-build zone): see res_buggy; on a scorch mark, its salvaged plate shield
    blown off and lying by it, debris round it."""
    out = []
    res_buggy(out, (0.0, 0.0, 0.0), 0.35, burnt=True, seed=seed)
    place_parts(out, scorch_mark(seed + 3, 2.4), (0.0, 0.0, 0), None, rename={"Scorch": "Scorch", "Amber": "Embers"})
    place_parts(out, debris(seed + 1, 0), (-0.9, -0.85, 0), Rz(1.2), rename={"Plates": "DPlates", "Chunks": "DChunks"})
    return out


BUGGY_SMOKE = (-0.35, 0.0, 0.48)                                        # its crew bay (Blender, prop-local, before its yaw of 0.35)


# ------------------------------------------------------------------------------------------------ the Resistance camp
CAMP_FIRES = [(-0.45, -1.42, 0.31), (-0.45, 1.42, 0.31), (2.55, 1.45, 0.31)]   # burning barrels' tops (Blender, prop-local)


def burn_barrel(br, cl, c, seed=0):
    """A burn barrel (fields: br the rusted drum, cl the glowing coals in its mouth) at c: holes punched round its
    top, the coals heaped in it (game.gd lights the fire)."""
    fx, fy = c[0], c[1]
    drum(br, (fx, fy, 0.15), label=0)
    for k in range(6):
        a = 2 * math.pi * k / 6 + seed
        br.sub(Sphere((fx + math.cos(a) * 0.1, fy + math.sin(a) * 0.1, 0.2), 0.022), k=0.004)
    br.sub(Cylinder((fx, fy, 0.3), 0.085, 0.06), k=0.0)
    cl.add(Ellipsoid((fx, fy, 0.27), (0.085, 0.085, 0.035), **wob(25.0, 0.008, seed)), k=0.0)


def salvage_barricade(sp, fr, sb, a, b, h0, h1, seed=0, marks=True, bags=True):
    """A barricade of salvaged robot plates (fields: sp the white plates, fr the steel posts and braces, sb the
    sandbags) from a to b on the ground, its face toward the left of a->b (the enemy side): curved white plates stood
    on end overlapping, leaning back on braces, sprayed with the amber chevron and slashes, sandbags piled along their
    foot; h0 to h1 its height along it."""
    rng = np.random.default_rng(seed)
    a, b = v3(a), v3(b)
    d = b - a
    L = float(np.linalg.norm(d[:2]))
    t = unit(v3((d[0], d[1], 0)))
    n = v3((-t[1], t[0], 0))                                            # (the face)
    k = max(1, int(L / 0.56))
    for i in range(k):
        u = (i + 0.5) / k
        h = h0 + (h1 - h0) * u
        w = L / k + 0.12
        c = a + t * (u * L) + n * rng.uniform(-0.03, 0.03) + Z * (h / 2)
        lean = unit(Z - n * 0.12)
        plate(sp, c, n, lean, w, h, t=0.026, bow=0.05)
        if marks and rng.random() < 0.55:
            if rng.random() < 0.55:
                chevron(sp, c + n * 0.06 + Z * (h * 0.1), n, w * 0.6, h * 0.25, t=0.06)
            else:
                slash(sp, c + n * 0.06 - t * (w * 0.3) + Z * (h * 0.25), c + n * 0.06 + t * (w * 0.3) - Z * (h * 0.05), 0.06)
        q = a + t * (u * L) - n * 0.05
        seg(fr, q, q + Z * (h + 0.06), 0.022)                           # its post, a brace behind it
        seg(fr, q + Z * (h * 0.75), q - n * (h * 0.45), 0.018)
        if i % 2 == 0:                                                   # weld seams: a strap across the joint
            strap(sp, q + n * 0.08 + t * 0.0 + Z * (h * 0.3), q + n * 0.08 + Z * (h * 0.7), w=0.04, nrm=n)
    if bags:
        sandbag_run(sb, a + n * 0.2, b + n * 0.2, layers=2, seed=seed + 5, rows=1)


def camp_city(seed=0):
    """The Resistance's forward camp at the end of every Data Center road (the road comes in from -X): a gate of
    welded salvaged plates swung open between two plate-armoured gate towers, an amber light strip and the amber
    Resistance banner hung from the gantry over the road, amber lamps on the towers; barricades of salvaged robot
    plates and sandbags running off both ways and dying away, tank traps welded from robot frames before them; burn barrels at the gate and in the yard; inside, a converted shipping
    container as the command post (its doorway and window lit, a canvas awning over the door, sandbags round it, a
    whip antenna), a field generator with amber lamps cabled to it (its exhaust smokes), a lattice radio mast with an
    amber beacon and guy wires, stacks of supply crates, ammo cans and jerrycans, a charcoal-teal supply tent, work
    lights on poles aimed down the road."""
    out = []
    rng = np.random.default_rng(seed)
    glows = G("glow_ember", "glow_lamp", "glow_fire", "glow_red", "glow_screen", prefix="C")
    # ---- the gate towers and the gantry
    gt, gp, gs = Field("GateTowers"), Field("GatePlates"), Field("GateBags")
    GY, GH = 1.2, 2.35
    for sy in (-1, 1):
        c = v3((0.0, sy * GY, 0.0))
        for sx in (-1, 1):                                               # four I-beam posts
            for sz in (-1, 1):
                q = c + v3((sx * 0.22, sz * 0.22, 0))
                box(gt, q + Z * (GH / 2), (0.035, 0.035, GH / 2), 0.008)
        for z in (0.5, 1.3, GH - 0.05):
            box(gt, c + Z * z, (0.26, 0.26, 0.03), 0.008)
        for nrm in ((-1, 0, 0), (0, sy, 0), (1, 0, 0)):                  # plates welded over its faces
            n = v3(nrm)
            for z0 in (0.9, 1.75):
                plate(gp, c + n * 0.27 + Z * z0, n, (0, 0, 1), 0.5, 0.8, t=0.024, bow=0.03)
        chevron(gp, c + v3((-0.3, 0, 1.85)), (-1, 0, 0), 0.34, 0.18, t=0.07, n=2)
        sandbag_run(gs, c + v3((-0.32, -0.3, 0)), c + v3((-0.32, 0.3, 0)), layers=3, seed=seed + sy, rows=2)
        sandbag_run(gs, c + v3((-0.3, sy * 0.32, 0)), c + v3((0.3, sy * 0.32, 0)), layers=3, seed=seed + 3 + sy, rows=1)
        # an amber lamp on its top
        gt.add(Cylinder(c + Z * (GH + 0.05), 0.06, 0.1, rr=0.02), k=0.0, label=7)
        glows["glow_ember"].add(Ellipsoid(c + Z * (GH + 0.15), (0.08, 0.08, 0.07)), k=0.0)
    for sy in (-1, 1):                                                   # the gantry: two beams across the road
        box(gt, (-0.12 + 0.24 * (sy > 0), 0.0, GH + 0.02), (0.035, GY + 0.25, 0.06), 0.008)
    plate(gp, (-0.2, 0.0, GH - 0.12), (-1, 0, 0), (0, 0, 1), 2.0, 0.3, t=0.024, bow=0.02)
    strip(glows["glow_ember"], (-0.24, -1.0, GH - 0.3), (-0.24, 1.0, GH - 0.3), 0.04, up=(-1, 0, -0.4))
    # the banner hanging from the gantry over the road
    bn = Field("Banner")
    Wb, Hb = 0.75, 1.0
    poly = [(0.0, -Wb / 2), (Hb, -Wb / 2), (Hb * 0.8, 0.0), (Hb, Wb / 2), (0.0, Wb / 2)]
    bn.add(leaf(v3((-0.06, 0.0, GH - 0.3)), (0, 0, -1), (0, 1, 0), poly, 0.008, wave=(0.025, 2 * math.pi / 0.9)), k=0.0)
    chevron(bn, (-0.08, 0.0, GH - 0.62), (-1, 0, 0), 0.5, 0.26, t=0.09, label=6, n=2)
    for sy in (-1, 1):
        bn.paint(RoundBox((-0.06, sy * (Wb / 2 - 0.035), GH - 0.8), (0.1, 0.035, 0.6), 0.0), 6)
    seg(gt, (-0.06, -Wb / 2 - 0.05, GH - 0.28), (-0.06, Wb / 2 + 0.05, GH - 0.28), 0.016)
    # the gate leaves: welded plates on steel frames, swung open into the yard
    gl_ = Field("Leaves")
    for sy in (-1, 1):
        hinge = v3((0.26, sy * (GY - 0.3), 0.0))
        d = unit(v3((1.0, sy * 0.25, 0.0)))                              # (swung wide open into the yard)
        nn = unit(np.cross(Z, d)) * (-sy)
        for j, (a0, z0) in enumerate(((0.25, 0.45), (0.75, 0.45), (0.25, 1.15), (0.75, 1.15))):
            plate(gl_, hinge + d * a0 + Z * z0 + nn * 0.02, nn, (0, 0, 1), 0.52, 0.72, t=0.022, bow=0.025)
        for z in (0.1, 0.8, 1.5):
            seg(gt, hinge + Z * z, hinge + d * 1.0 + Z * z, 0.022)
        seg(gt, hinge, hinge + Z * 1.55, 0.03)
        seg(gt, hinge + d * 1.0, hinge + d * 1.0 + Z * 1.55, 0.025)
        seg(gt, hinge + Z * 0.1, hinge + d * 1.0 + Z * 1.5, 0.018)
        chevron(gl_, hinge + d * 0.5 + Z * 0.95 + nn * 0.08, nn, 0.5, 0.26, t=0.07)
    ground_cut(gt, -0.02)
    ground_cut(gs, -0.01)
    out += [("GateTowers", gt, fine(0.006, 0.012), "res_armor"), ("GatePlates", gp, fine(0.006, 0.012), "salvage"), ("GateBags", gs, fine(0.006, 0.012), "sandbag"),
            ("Banner", bn, fine(0.005, 0.01), "banner"), ("Leaves", gl_, fine(0.006, 0.012), "salvage")]
    # ---- barricades running off both ways, dying away
    for sy in (-1, 1):
        sp, fr, sb = Field("Plates%d" % (sy + 1)), Field("Braces%d" % (sy + 1)), Field("Bags%d" % (sy + 1))
        pts = [v3((-0.1, sy * (GY + 0.35), 0)), v3((-0.25, sy * 3.0, 0)), v3((0.1, sy * 4.6, 0)), v3((0.6, sy * 6.0, 0))]
        hs = [1.45, 1.3, 1.0, 0.55]
        for i in range(3):
            a, b = (pts[i + 1], pts[i]) if sy < 0 else (pts[i], pts[i + 1])     # (its face toward -X, the road)
            h0, h1 = (hs[i + 1], hs[i]) if sy < 0 else (hs[i], hs[i + 1])
            salvage_barricade(sp, fr, sb, a, b, h0, h1, seed=seed + 11 * i + sy, marks=True, bags=True)
        ground_cut(sp, -0.02)
        ground_cut(fr, -0.02)
        ground_cut(sb, -0.01)
        out += [("Plates%d" % (sy + 1), sp, fine(0.007, 0.014), "salvage"), ("Braces%d" % (sy + 1), fr, fine(0.006, 0.012), "res_armor"),
                ("Bags%d" % (sy + 1), sb, fine(0.007, 0.014), "sandbag")]
    # tank traps welded from robot frames before the barricades
    tt = Field("TankTraps")
    for (x, y) in ((-1.0, -3.3), (-0.95, 3.4), (-1.2, -5.0)):
        c = v3((x, y, 0.28))
        for k, ax in enumerate(((1, 0.3, 0.6), (-0.3, 1, 0.6), (0.4, -0.5, -0.9))):
            d = unit(v3(ax))
            seg(tt, c - d * 0.36, c + d * 0.36, 0.03)
    ground_cut(tt, -0.02)
    out.append(("TankTraps", tt, fine(0.005, 0.01), "gunmetal"))
    # ---- burn barrels
    br, cl = Field("Barrels"), Field("Coals")
    for i, (fx, fy, fz) in enumerate(CAMP_FIRES):
        burn_barrel(br, cl, (fx, fy), seed + i)
    ground_cut(br, -0.01)
    out += [("Barrels", br, fine(0.004, 0.008), "rust"), ("Coals", cl, fine(0.004, 0.008), "glow_fire")]
    # ---- the command post: a converted container
    ct, aw, cb_ = Field("Container"), Field("Awning"), Field("PostBags")
    C0, CL, CW, CH = v3((3.3, -1.75, 0.0)), 1.25, 0.5, 1.05             # its centre, half length (x), half width, height
    ct.add(RoundBox(C0 + Z * (CH / 2), (CL, CW, CH / 2), 0.015,
                    disp=lambda P: (F32(0.007) * np.cos((P[:, 0] - F32(C0[0])) * F32(75.0))).astype(F32), disp_amp=0.008), k=0.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (0.035, CH - 0.035):
                ct.add(RoundBox(C0 + v3((sx * (CL - 0.035), sy * (CW - 0.035), z)), (0.045, 0.045, 0.04), 0.006), k=0.003, label=7)
    door = C0 + v3((0.35, -CW, 0.0))                                      # its doorway cut in its front (-Y), lit
    ct.sub(RoundBox(door + Z * 0.5, (0.28, 0.12, 0.48), 0.02), k=0.0)
    glows["glow_lamp"].add(RoundBox(door + v3((0, 0.1, 0.5)), (0.27, 0.01, 0.47), 0.01), k=0.0)
    ct.add(RoundBox(door + v3((0.42, -0.18, 0.5)), (0.012, 0.18, 0.47), 0.008), k=0.0, label=7)   # its door swung open
    win = C0 + v3((-0.6, -CW, 0.62))
    ct.sub(RoundBox(win, (0.22, 0.1, 0.15), 0.02), k=0.0)
    glows["glow_lamp"].add(RoundBox(win + v3((0, 0.06, 0)), (0.21, 0.01, 0.14), 0.01), k=0.0)
    for k in range(3):
        seg(ct, win + v3((-0.15 + k * 0.15, 0.0, -0.15)), win + v3((-0.15 + k * 0.15, 0.0, 0.15)), 0.01)
    chevron(ct, C0 + v3((-0.2, CW, 0.62)), (0, 1, 0), 0.5, 0.25, t=0.08, n=2)
    chevron(ct, C0 + v3((-0.6, -CW, 0.95)), (0, -1, 0), 0.3, 0.06, t=0.05)
    stencil(ct, C0 + v3((0.95, -CW, 0.35)), (0, -1, 0), 0.25, 0.07, label=9, n=3)
    chevron(ct, C0 + v3((-CL, 0.0, 0.62)), (-1, 0, 0), 0.4, 0.2, t=0.07)
    # the awning over its door on two poles, guy ropes
    a0 = door + v3((0.0, 0.0, CH - 0.06))
    aw.add(leaf(a0 + v3((-0.6, -0.02, 0)), (1, 0, 0), unit(v3((0, -1, -0.32))), [(0.0, 0.0), (1.2, 0.0), (1.2, 0.8), (0.0, 0.8)], 0.008, cup=0.08), k=0.0)
    aw.paint(RoundBox(a0 + v3((0.0, -0.78, -0.25)), (0.65, 0.06, 0.1), 0.0), 6)
    for sx in (-1, 1):
        q = a0 + v3((sx * 0.58, -0.76, -0.25))
        seg(cb_, v3((q[0], q[1], 0.0)), q + Z * 0.02, 0.018)
        seg(cb_, q, v3((q[0] + sx * 0.25, q[1] - 0.4, 0.0)), 0.006)
    # sandbags round its back and its road end, a whip antenna, a box of kit on its roof
    sandbag_run(cb_, C0 + v3((-CL - 0.15, CW + 0.2, 0)), C0 + v3((CL + 0.15, CW + 0.2, 0)), layers=2, seed=seed + 40, rows=1)
    sandbag_run(cb_, C0 + v3((-CL - 0.2, -CW - 0.1, 0)), C0 + v3((-CL - 0.2, CW + 0.1, 0)), layers=2, seed=seed + 41, rows=1)
    sandbag_run(cb_, C0 + v3((-0.3, -0.3, CH)), C0 + v3((-0.3, 0.3, CH)), layers=1, seed=seed + 42, rows=1, z0=CH)
    seg(cb_, C0 + v3((CL - 0.2, -CW + 0.15, CH)), C0 + v3((CL - 0.2, -CW + 0.15, CH + 1.4)), 0.012)
    cb_.add(Sphere(C0 + v3((CL - 0.2, -CW + 0.15, CH + 1.42)), 0.02), k=0.0)
    ammo_crate(cb_, C0 + v3((0.5, -0.15, CH + 0.1)), (0.18, 0.12, 0.1), yaw=0.3, label=7, mark=False)
    ground_cut(ct, -0.02)
    ground_cut(cb_, -0.02)
    out += [("Container", ct, fine(0.007, 0.014), "container"), ("Awning", aw, fine(0.005, 0.01), "canvas"), ("PostBags", cb_, fine(0.006, 0.012), "sandbag")]
    # ---- the field generator with its amber lamps, cabled to the post and the lights
    gn, gc = Field("Generator"), Field("GenCables")
    G0 = v3((1.75, -3.35, 0.0))
    box(gn, G0 + Z * 0.06, (0.62, 0.36, 0.06), 0.015, label=7)
    gn.add(RoundBox(G0 + Z * 0.45, (0.55, 0.32, 0.34), 0.05), k=0.0)
    for k in range(6):                                                    # its grille
        gn.sub(RoundBox(G0 + v3((-0.2 + k * 0.08, -0.32, 0.5)), (0.018, 0.05, 0.18), 0.008), k=0.0)
    gn.add(Cylinder(G0 + v3((0.35, 0.0, 0.85)), 0.13, 0.1, rr=0.03), k=0.02, label=7)       # fuel filler, exhaust
    seg(gn, G0 + v3((-0.35, 0.15, 0.78)), G0 + v3((-0.35, 0.15, 1.25)), 0.035, label=6)
    gn.add(RoundBox(G0 + v3((-0.35, 0.15, 1.27)), (0.06, 0.05, 0.01), 0.005, R=euler(0, -0.4, 0)), k=0.0, label=6)
    chevron(gn, G0 + v3((0.25, -0.32, 0.5)), (0, -1, 0), 0.22, 0.12, t=0.05)
    gn.paint(RoundBox(G0 + v3((0, 0, 0.18)), (0.6, 0.4, 0.04), 0.0), 5)
    for sx in (-1, 1):                                                    # amber lamps on its corners
        gn.add(Cylinder(G0 + v3((sx * 0.48, -0.25, 0.82)), 0.035, 0.05, rr=0.01), k=0.0, label=7)
        glows["glow_ember"].add(Sphere(G0 + v3((sx * 0.48, -0.25, 0.87)), 0.045), k=0.0)
    screen(gn, glows["glow_screen"], G0 + v3((-0.3, -0.33, 0.62)), (0, -1, 0), 0.14, 0.08, bezel=0.012, depth=0.012, label=7)
    jerrycan(gn, G0 + v3((0.75, -0.1, 0.13)), yaw=0.4)
    jerrycan(gn, G0 + v3((0.78, 0.15, 0.13)), yaw=0.2)
    cable_bundle(gc, [G0 + v3((0.0, 0.33, 0.3)), G0 + v3((0.3, 0.8, 0.03)), C0 + v3((-0.6, -CW - 0.4, 0.03)), C0 + v3((-0.9, -CW, 0.3))],
                 n=2, r=0.02, seed=seed, spread=0.03, labels=(0, 5))
    cable_bundle(gc, [G0 + v3((-0.55, 0.0, 0.3)), G0 + v3((-0.9, 0.4, 0.03)), v3((0.75, -2.3, 0.03)), v3((0.65, -2.05, 0.1))], n=1, r=0.02, seed=seed + 1)
    ground_cut(gn, -0.02)
    ground_cut(gc, -0.01)
    out += [("Generator", gn, fine(0.005, 0.01), "res_armor"), ("GenCables", gc, fine(0.004, 0.008), "cables")]
    # ---- the radio mast: lattice, whips, a small dish, guy wires, the amber beacon
    ms = Field("Mast")
    M0, MH = v3((4.85, -3.1, 0.0)), 4.2
    lattice_mast(ms, M0, -0.05, MH, 0.22, 0.08, legs=3, step=0.3, rod=0.013)
    box(ms, M0 + Z * 0.03, (0.32, 0.32, 0.03), 0.01)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        seg(ms, M0 + v3((math.cos(a) * 0.12, math.sin(a) * 0.12, MH - 0.6 + k * 0.15)),
            M0 + v3((math.cos(a) * 0.3, math.sin(a) * 0.3, MH - 0.6 + k * 0.15)), 0.012)
        ms.add(RoundBox(M0 + v3((math.cos(a) * 0.36, math.sin(a) * 0.36, MH - 0.6 + k * 0.15)), (0.03, 0.08, 0.14), 0.015, R=Rz(a)), k=0.0, label=7)
        a = (-0.6, 1.3, 3.7)[k]                                           # guy wires to their anchors (clear of the post)
        g = M0 + v3((math.cos(a) * 1.8, math.sin(a) * 1.8, 0.03))
        seg(ms, M0 + Z * (MH * 0.72) + v3((math.cos(a) * 0.1, math.sin(a) * 0.1, 0)), g, 0.005)
        ms.add(Cylinder(g, 0.05, 0.06, rr=0.01), k=0.0, label=7)
    pole(ms, M0 + Z * MH, M0 + Z * (MH + 0.8), 0.014, 0.005)
    glows["glow_ember"].add(Sphere(M0 + Z * (MH + 0.05), 0.06), k=0.0)
    vt, ax = M0 + v3((-0.25, 0.0, MH - 1.2)), unit(v3((-0.8, 0.3, 0.5)))
    ms.add(Func(lambda P, vt=vt, ax=ax: (lambda Q: np.maximum(np.abs(Q[:, 2] - (Q[:, 0] ** 2 + Q[:, 1] ** 2) / F32(0.8)) - F32(0.008),
                                                             np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2) - F32(0.22)))(((P - F32(vt)) @ rot_from_axes(z_axis=ax).astype(F32))).astype(F32),
                vt - 0.4, vt + 0.4), k=0.0)
    seg(ms, vt, M0 + v3((-0.1, 0, MH - 1.2)), 0.015)
    ground_cut(ms, -0.03)
    out.append(("Mast", ms, fine(0.005, 0.01), "galv"))
    # ---- supplies: crates, ammo cans, jerrycans on pallets; the supply tent
    cr, pt = Field("Crates"), Field("Pallets")
    for (x, y, yaw) in ((1.25, -1.55, 0.2), (2.0, 2.6, -0.3), (4.4, 0.9, 0.5)):
        pallet(pt, (x, y, 0), 0.4, 0.33, yaw=yaw)
        R = Rz(yaw)
        ammo_crate(cr, v3((x, y, 0)) + R @ v3((-0.12, -0.05, 0.22)), (0.22, 0.15, 0.11), yaw=yaw, label=0)
        ammo_crate(cr, v3((x, y, 0)) + R @ v3((0.18, 0.06, 0.22)), (0.17, 0.2, 0.12), yaw=yaw + 0.1, label=0)
        ammo_crate(cr, v3((x, y, 0)) + R @ v3((-0.05, 0.0, 0.43)), (0.2, 0.13, 0.1), yaw=yaw - 0.15, label=0)
        chevron(cr, v3((x, y, 0)) + R @ v3((-0.12, -0.2, 0.22)), R @ v3((0, -1, 0)), 0.14, 0.07, t=0.035)
        for k in range(3):
            ammo_can(cr, v3((x, y, 0)) + R @ v3((0.45, -0.25 + k * 0.17, 0.06)), yaw=yaw + 0.1 * k, label=7)
    jerrycan(cr, (1.75, -1.15, 0.13), yaw=0.3)
    jerrycan(cr, (1.95, -1.1, 0.13), yaw=-0.2)
    ground_cut(cr, -0.01)
    ground_cut(pt, -0.01)
    out += [("Crates", cr, fine(0.005, 0.01), "res_crate"), ("Pallets", pt, fine(0.005, 0.01), "timber")]
    tn = Field("Tent")
    T0 = v3((3.6, 2.2, 0.0))
    TL, TW, TH = 0.85, 0.65, 0.95
    tn.add(convex([(T0 + Z * TH, unit(v3((0, TH, TW)))), (T0 + Z * TH, unit(v3((0, -TH, TW)))), (T0, (0, 0, -1)),
                   (T0 + v3((TL, 0, 0)), (1, 0, 0)), (T0 - v3((TL, 0, 0)), (-1, 0, 0))], T0 - v3((1.2, 1.0, 0.1)), T0 + v3((1.2, 1.0, 1.2))), k=0.0)
    tn.sub(convex([(T0 + Z * (TH - 0.12), unit(v3((0, TH, TW)))), (T0 + Z * (TH - 0.12), unit(v3((0, -TH, TW)))), (T0 + Z * 0.05, (0, 0, -1)),
                   (T0 - v3((TL - 0.04, 0, 0)), (-1, 0, 0))], T0 - v3((1.0, 0.9, 0.0)), T0 + v3((1.3, 0.9, 1.1))), k=0.0)    # open at its +X end
    tn.paint(RoundBox(T0 + v3((0, 0, TH * 0.55)), (TL + 0.1, TW, 0.05), 0.0), 6)
    pole(tn, T0 + v3((TL - 0.02, 0, 0)), T0 + v3((TL - 0.02, 0, TH + 0.12)), 0.018)
    pole(tn, T0 - v3((TL - 0.02, 0, 0)), T0 - v3((TL - 0.02, 0, -TH - 0.12)), 0.018)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tn.add(RoundCone(T0 + v3((sx * (TL - 0.1), sy * (TW * 0.5), TH * 0.5)), T0 + v3((sx * (TL + 0.1), sy * (TW + 0.35), 0.0)), 0.004, 0.004), k=0.0)
    glows["glow_lamp"].add(RoundBox(T0 + v3((TL - 0.08, 0, 0.3)), (0.01, TW * 0.5, 0.25), 0.01), k=0.0)
    ground_cut(tn, -0.02)
    out.append(("Tent", tn, fine(0.006, 0.012), "canvas"))
    # ---- work lights on poles aimed down the road
    lp_, lh = Field("LightPoles"), Field("LightHeads")
    for sy in (-1, 1):
        b = v3((0.75, sy * 2.15, 0.0))
        lp_.add(Cylinder(b + Z * 0.05, 0.08, 0.1, rr=0.02), k=0.0)
        pole(lp_, b, b + Z * 2.2, 0.03, 0.022)
        pole(lp_, b + v3((0, -0.18, 2.15)), b + v3((0, 0.18, 2.15)), 0.016)
        for dy in (-0.14, 0.14):
            flood_head(lh, glows["glow_lamp"], b + v3((-0.06, dy, 2.08)), (-0.8, -sy * 0.3, -0.5), s=1.1)
        cable_bundle(lp_, [b + v3((0.02, 0, 0.3)), b + v3((0.2, 0, 0.03)), b + v3((0.6, -sy * 0.3, 0.03))], n=1, r=0.012, seed=seed + sy)
    ground_cut(lp_, -0.02)
    out += [("LightPoles", lp_, fine(0.005, 0.01), "res_armor"), ("LightHeads", lh, fine(0.004, 0.008), "gunmetal")]
    return finish_glows(out, glows)


# game.gd (prop-local, Blender x, y, z; Godot x, z, -y): the work lights [(position, aim)], the lamps' amber glows, the
# generator's exhaust, the doorway's warm light
CAMP_LIGHTS = []
for _sy in (-1, 1):
    for _dy in (-0.14, 0.14):
        CAMP_LIGHTS.append(((0.75 - 0.06, _sy * 2.15 + _dy, 2.08), (-0.8, -_sy * 0.3, -0.5)))
CAMP_AMBER = [(0.0, -1.2, 2.5), (0.0, 1.2, 2.5), (-0.24, 0.0, 2.05), (4.85, -3.1, 4.25)]   # gate lamps, the gantry strip, the beacon
CAMP_SMOKE = [(1.75 - 0.35, -3.35 + 0.15, 1.3)]                       # the generator's exhaust
CAMP_DOOR = (3.65, -2.5, 0.6)                                         # the command post's lit doorway (warm)




def KITS(theme):
    if theme == "cooling":
        return {
            "Pipe_A": (lambda: pipe_run(801, 0), 1100), "Pipe_B": (lambda: pipe_run(802, 1), 900), "Canisters": (lambda: coolant_canisters(803), 900),
            "Ice_A": (lambda: ice_chunk(804, 1.0), 450), "Ice_B": (lambda: ice_chunk(805, 0.7), 350), "Pump": (lambda: coolant_pump(806), 1000),
            "Barrier": (lambda: hazard_barrier(807), 600), "Crates": (lambda: steel_crates(808), 700), "Cables": (lambda: cable_floor(809), 600),
            "Slick": (lambda: ice_slick(810), 160),
            "CoolTower": (lambda: coolant_tower(811), 4200), "Exchanger": (lambda: heat_exchanger(812), 3800), "FrozenBot": (lambda: frozen_robot(813), 3400),
            "PumpStation": (lambda: pump_station(814), 4200),
            "IceBig_A": (lambda: ice_formation(815, 0), 1800), "IceBig_B": (lambda: ice_formation(816, 1), 1900), "Tank_Ice": (lambda: iced_tank(817), 2300),
            "Chiller_A": (lambda: chiller(818, 0), 2400), "Chiller_B": (lambda: chiller(819, 1), 2400),
        }
    if theme == "server":
        return {
            "Rack_A": (lambda: robo_racks(821, 2), 1100), "Rack_B": (lambda: robo_racks(822, 3, door={2: "open"}), 1500),
            "Tray": (lambda: cable_tray(823), 800), "Cart": (lambda: rack_cart(824), 800), "Fan": (lambda: floor_fan(825), 800),
            "Drone": (lambda: maint_drone(826), 1000), "Toppled": (lambda: toppled_rack(827), 1100), "Vent": (lambda: vent_tile(828), 120),
            "Mainframe": (lambda: mainframe_wall(829), 5200), "Duct": (lambda: duct_column(830), 3200), "Workstation": (lambda: robot_workstation(831), 4000),
            "Breach": (lambda: breach(832), 3600),
            "RackRow_A": (lambda: rack_row(833, 0), 2600), "RackRow_B": (lambda: rack_row(834, 1), 2800),
            "MainframeUnit": (lambda: mainframe_unit(835), 2400), "PowerUnit": (lambda: power_unit(836), 2200),
        }
    if theme == "core":
        return {
            "Conduit": (lambda: energy_conduit(841), 900), "Spire": (lambda: data_spire(842), 700), "CableRun": (lambda: core_cables(843), 900),
            "Debris_A": (lambda: debris(844, 0), 600), "Debris_B": (lambda: debris(845, 1), 700), "RobotParts": (lambda: robot_parts(847), 1800),
            "Scorch": (lambda: scorch_mark(848), 160), "Crystals": (lambda: data_crystals(849), 500),
            "DataSpire": (lambda: giant_spire(850), 3600), "CableColumn": (lambda: cable_column(851), 3600), "Tank": (lambda: wrecked_tank(852), 4200),
            "Giant": (_giant, 5200),
            "Pillar": (lambda: energy_pillar(853, 0), 2200), "Pillar_B": (lambda: energy_pillar(854, 1), 2200),
            "Wreck_Bot": (lambda: wreck_robot(855), 3000), "Wreck_Car": (lambda: wreck_vehicle(856), 2600),
        }
    if theme == "camp_city":
        return {"City": (lambda: camp_city(891), 21000)}
    raise KeyError(theme)
