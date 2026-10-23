"""Dr. Ito's stand: his mobile field workshop on a corner of the airbase apron. A round pad of poured concrete (expansion
joints cut across it, a yellow-and-black hazard band round its side) on the asphalt (worn yellow and white lines, an oil
stain), the hero ring set in its top: twelve amber marker lights in steel bezels (their own emissive mesh). Round it:
behind him on his left a portable generator (olive drab in a black tube frame, a control panel with outlets and a red
switch, a muffler) with a jerrycan beside it; behind him on his right his rugged equipment case lying open (black, its
lid up, grey foam, a yellow drill, spanners and screwdrivers in their cut-outs); before him on his right a laptop open on
an olive ammo crate (its screen glows: its own emissive mesh); before him on his left a small quadcopter drone on its
landing mat (a white H in a ring); black cables run over the asphalt from the generator to the case and on to the
laptop; a strip of lawn behind a concrete kerb at the back, grass in it."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, Prim,
                 v3, norm, rot_from_axes, euler, axis_angle, smin, smax, NOISE, F)
from caveman import Stone, Inter, Shell, Lock, lerp
import base as _b

GROUND_R = 1.32
GROUND_TOP = 0.08
PAD_R = 0.8                        # the concrete pad
TOP_Z = 0.2                        # its top = where he stands
STAND = v3((0.0, 0.0, TOP_Z))
RING_R = 0.7                       # the marker lights, in its top
N_GLOW = 12
LAWN_A = (62.0, 118.0)             # the lawn behind the kerb (degrees round him: 0 = his left, 90 = behind)
LAWN_R0 = 1.06


def smoothstep(e0, e1, x):
    t = np.clip((x - F(e0)) / F(e1 - e0), 0, 1)
    return t * t * (F(3) - F(2) * t)


def ground_height(x, y):
    r = math.hypot(x, y)
    return GROUND_TOP + 0.015 * max(0.0, 1 - (r / GROUND_R) ** 2)


def _placed(angle_deg, r, turn=0.0):
    """A prop's place round him: (centre on the ground, its inward direction (toward him), its tangent), turned `turn`
    degrees about the vertical."""
    a = math.radians(angle_deg)
    c = v3((math.cos(a) * r, math.sin(a) * r, 0.0))
    c[2] = ground_height(c[0], c[1])
    inward = euler(0, 0, math.radians(turn)) @ -norm(v3((c[0], c[1], 0.0)))
    tang = norm(np.cross(v3((0, 0, 1)), inward))
    return c, inward, tang


GEN = _placed(44.0, 1.03, -20.0)
CASE = _placed(138.0, 1.04, 15.0)
CRATE = _placed(214.0, 1.03, 30.0)
DRONE = _placed(-38.0, 1.04, 0.0)


# ---------------------------------------------------------------------------------------------- the asphalt, the lawn
def _in_lawn(x, y, pad=0.0):
    a = math.degrees(math.atan2(y, x))
    return LAWN_A[0] - pad * 60 < a < LAWN_A[1] + pad * 60 and math.hypot(x, y) > LAWN_R0 - pad


def ground_field():
    """Asphalt (pavement: label 0) on a low round slab: a worn yellow line (5) along the front, white parking marks (6),
    an oil stain (8); cut away behind for the lawn."""
    fd = Field("Ground")
    def disc(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        a = np.arctan2(P[:, 1], P[:, 0])
        R = F(GROUND_R) + F(0.012) * np.sin(a * 5 + 0.7) + F(0.008) * np.sin(a * 11 + 2.1)
        dome = F(GROUND_TOP) + F(0.015) * np.clip(1 - (r / F(GROUND_R)) ** 2, 0, 1)
        dx = r - R
        dz = np.maximum(P[:, 2] - dome, F(-0.12) - P[:, 2])
        q = np.stack([np.maximum(dx + F(0.03), 0), np.maximum(dz + F(0.03), 0)], 1)
        return np.minimum(np.maximum(dx + F(0.03), dz + F(0.03)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.03)
    rough = lambda P: F(0.0016) * NOISE(P * F(60)) + F(0.0012) * NOISE(P * F(13))
    fd.add(Func(disc, (-1.45, -1.45, -0.2), (1.45, 1.45, 0.2), disp=rough, disp_amp=0.003), 0.0)
    # (a lowered bed for the lawn behind the kerb)
    def lawn_cut(P):
        a = np.arctan2(P[:, 1], P[:, 0]) * F(180 / math.pi)
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.maximum(F(LAWN_A[0]) - a, a - F(LAWN_A[1])) * F(0.0175) * r, F(LAWN_R0) - r)
    fd.sub(Func(lambda P: np.maximum(lawn_cut(P), F(GROUND_TOP - 0.02) - P[:, 2]), (-1.5, 0.0, -0.1), (1.5, 1.5, 0.3)), 0.006)
    # cracks
    rs = np.random.RandomState(5)
    for k in range(5):
        a = rs.uniform(0, 2 * math.pi)
        if 40 < math.degrees(a) % 360 < 140:
            continue
        r0 = rs.uniform(0.86, 1.0)
        pts = []
        for i in range(5):
            rr = r0 + 0.07 * i
            aa = a + rs.uniform(-0.05, 0.05)
            pts.append(v3((math.cos(aa) * rr, math.sin(aa) * rr, ground_height(math.cos(aa) * rr, math.sin(aa) * rr) + 0.003)))
        fd.sub(Chain(pts, [0.004, 0.005, 0.004, 0.003, 0.002], k=0.003), 0.002)
    # road paint: a yellow line along the front, white parking marks on the right, an oil stain on the left
    fd.paint(Func(lambda P: np.maximum(np.abs(P[:, 1] + F(1.0) + F(0.04) * P[:, 0]) - F(0.045), F(-0.02) - P[:, 2] + F(GROUND_TOP)),
                  (-1.5, -1.5, -0.1), (1.5, -0.6, 0.3)), 5)
    def marks(P):
        d1 = np.maximum(np.abs(P[:, 0] + F(0.98)) - F(0.03), np.abs(P[:, 1] - F(0.05)) - F(0.35))
        d2 = np.maximum(np.abs(P[:, 1] + F(0.26)) - F(0.03), np.abs(P[:, 0] + F(1.1)) - F(0.14))
        return np.maximum(np.minimum(d1, d2), F(GROUND_TOP - 0.02) - P[:, 2])
    fd.paint(Func(marks, (-1.5, -1.0, -0.1), (-0.6, 0.6, 0.3)), 6)
    fd.paint(Ellipsoid(v3((1.0, -0.22, GROUND_TOP)), (0.13, 0.09, 0.05), R=euler(0, 0, 0.5),
                       disp=lambda P: F(0.02) * NOISE(P * F(14)), disp_amp=0.02), 8)
    return fd


def lawn_field():
    """A strip of lawn behind the kerb (ground material: grass on top)."""
    fd = Field("Lawn")
    def bed(P):
        a = np.arctan2(P[:, 1], P[:, 0]) * F(180 / math.pi)
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        side = np.maximum(F(LAWN_A[0] + 1.0) - a, a - F(LAWN_A[1] - 1.0)) * F(0.0175) * r
        inner = F(LAWN_R0 + 0.035) - r
        outer = r - F(GROUND_R - 0.02)
        top = P[:, 2] - (F(GROUND_TOP + 0.03) + F(0.015) * smoothstep(1.32, 1.12, r))
        bot = F(GROUND_TOP - 0.06) - P[:, 2]
        return np.maximum(np.maximum(np.maximum(side, inner), np.maximum(outer, top)), bot)
    fd.add(Func(bed, (-0.8, 0.6, GROUND_TOP - 0.08), (0.8, 1.4, GROUND_TOP + 0.08),
                disp=lambda P: F(0.004) * NOISE(P * F(9)), disp_amp=0.005), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the concrete pad
def pad_field():
    """Poured concrete (pavement: label 7): the round pad he stands on, its edge chamfered, expansion joints sawn across it,
    a yellow (5) and black (9) hazard band round its side; the kerb along the lawn."""
    fd = Field("Pad")
    z0 = GROUND_TOP - 0.05
    def slab(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        d_r = r - F(PAD_R)
        d_z = np.maximum(P[:, 2] - F(TOP_Z), F(z0) - P[:, 2])
        cham = (r - F(PAD_R) + P[:, 2] - F(TOP_Z) + F(0.02)) * F(0.7071)
        q = np.stack([np.maximum(d_r + F(0.006), 0), np.maximum(d_z + F(0.006), 0)], 1)
        box = np.minimum(np.maximum(d_r + F(0.006), d_z + F(0.006)), 0) + np.sqrt((q ** 2).sum(1)) - F(0.006)
        return np.maximum(box, cham)
    pores = lambda P: F(0.0008) * NOISE(P * F(90)) + F(0.0012) * NOISE(P * F(20))
    fd.add(Func(slab, (-0.9, -0.9, z0 - 0.03), (0.9, 0.9, TOP_Z + 0.03), disp=pores, disp_amp=0.002), 0.0, 7)
    for ang in (0.35, 0.35 + math.pi / 2):                                                    # expansion joints
        d = v3((math.cos(ang), math.sin(ang), 0))
        fd.sub(Func(lambda P, d=d: np.maximum(np.abs(P @ d.astype(F)) - F(0.004), F(TOP_Z - 0.008) - P[:, 2]),
                    (-0.9, -0.9, TOP_Z - 0.02), (0.9, 0.9, TOP_Z + 0.02)), 0.002)
    for k in range(3):                                                                        # spalled chips on the edge
        a = 1.1 + k * 2.2
        fd.sub(Sphere(v3((math.cos(a) * PAD_R, math.sin(a) * PAD_R, TOP_Z - 0.01)), 0.025, disp=lambda P: F(0.006) * NOISE(P * F(40)), disp_amp=0.006), 0.004)
    def hazard(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        s = np.sin((a * F(PAD_R) + P[:, 2]) * F(2 * math.pi / 0.11))
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(np.maximum(-s * F(0.01), F(PAD_R - 0.03) - r), np.maximum(P[:, 2] - F(TOP_Z - 0.03), F(GROUND_TOP + 0.01) - P[:, 2]))
    def band(P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        return np.maximum(F(PAD_R - 0.03) - r, np.maximum(P[:, 2] - F(TOP_Z - 0.03), F(GROUND_TOP + 0.01) - P[:, 2]))
    fd.paint(Func(band, (-0.9, -0.9, 0.0), (0.9, 0.9, TOP_Z)), 9)
    fd.paint(Func(hazard, (-0.9, -0.9, 0.0), (0.9, 0.9, TOP_Z)), 5)
    # the kerb along the lawn
    def kerb(P):
        a = np.arctan2(P[:, 1], P[:, 0]) * F(180 / math.pi)
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        side = np.maximum(F(LAWN_A[0]) - a, a - F(LAWN_A[1])) * F(0.0175) * r
        d_r = np.abs(r - F(LAWN_R0 + 0.012)) - F(0.03)
        d_z = np.maximum(P[:, 2] - F(GROUND_TOP + 0.05), F(GROUND_TOP - 0.06) - P[:, 2])
        return np.maximum(np.maximum(side, d_r), d_z) - F(0.0)
    fd.add(Func(kerb, (-0.8, 0.5, GROUND_TOP - 0.08), (0.8, 1.4, GROUND_TOP + 0.08), disp=pores, disp_amp=0.002), 0.0, 7)
    return fd


def glow_pos(i):
    a = i * 2 * math.pi / N_GLOW + math.radians(15)
    return v3((math.cos(a) * RING_R, math.sin(a) * RING_R, TOP_Z + 0.006))


def rim_field():
    """The marker lights' steel bezels (fieldgun: bright steel, 7; black screws, 8), flush in the pad's top."""
    fd = Field("Rim")
    for i in range(N_GLOW):
        c = glow_pos(i)
        fd.add(Torus(c + v3((0, 0, -0.002)), 0.034, 0.008), 0.0, 7)
        fd.add(Cylinder(c + v3((0, 0, -0.008)), 0.042, 0.01, rr=0.004), 0.004, 7)
        for k in range(3):
            a = 2 * math.pi * k / 3 + i
            fd.add(Sphere(c + v3((math.cos(a) * 0.036, math.sin(a) * 0.036, -0.002)), 0.0045), 0.001, 8)
    return fd


def glowmarks_field():
    fd = Field("Glowmarks")
    for i in range(N_GLOW):
        fd.add(Ellipsoid(glow_pos(i), (0.027, 0.027, 0.012)), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the generator
def gen_frame():
    c, inw, tg = GEN
    return v3((c[0], c[1], ground_height(c[0], c[1]))), inw, tg, np.stack([tg, inw, v3((0, 0, 1))], 1)


GEN_H = (0.22, 0.16, 0.18)              # half sizes of its body (along, across, up)


def generator_field():
    """fieldgun: an olive-drab generator (0) in a black tube frame (8): a control panel (gunmetal, 5) on its face toward him
    with black outlets, a red switch (12) and a white label (13); a steel muffler (7) on its end, a black fuel cap; a
    jerrycan (olive) beside it."""
    fd = Field("Generator")
    c, inw, tg, R = gen_frame()
    ham = lambda P: F(0.0007) * NOISE(P * F(50))
    body = c + v3((0, 0, 0.05 + GEN_H[2]))
    fd.add(RoundBox(body, GEN_H, 0.03, R=R, disp=ham, disp_amp=0.001), 0.0, 0)
    fd.add(RoundBox(body + v3((0, 0, GEN_H[2] - 0.01)), (GEN_H[0] * 0.85, GEN_H[1] * 0.8, 0.03), 0.03, R=R), 0.02, 0)   # its domed top
    for k in range(5):                                                                          # cooling louvres
        fd.sub(RoundBox(body - inw * GEN_H[1] + tg * (0.07 + 0.024 * k) + v3((0, 0, 0.02)), (0.006, 0.01, 0.07), 0.003, R=R), 0.002)
    # the tube frame: four posts, top and bottom rails
    corners = [body + tg * (sl * (GEN_H[0] + 0.035)) + inw * (sd * (GEN_H[1] + 0.035)) for sl in (-1, 1) for sd in (-1, 1)]
    zb, zt = c[2] + 0.02, body[2] + GEN_H[2] + 0.06
    for p in corners:
        fd.add(RoundCone(v3((p[0], p[1], zb)), v3((p[0], p[1], zt)), 0.013, 0.013), 0.004, 8)
    for (i, j) in ((0, 1), (2, 3), (0, 2), (1, 3)):
        for z in (zb, zt):
            a, b = corners[i], corners[j]
            fd.add(RoundCone(v3((a[0], a[1], z)), v3((b[0], b[1], z)), 0.013, 0.013), 0.006, 8)
    # the control panel on the face toward him
    pc = body + inw * (GEN_H[1] + 0.004) + tg * (-0.06)
    fd.add(RoundBox(pc, (0.075, 0.008, 0.075), 0.006, R=R), 0.004, 5)
    for k in (-1, 1):
        fd.add(Cylinder(pc + inw * 0.008 + tg * (k * 0.032) + v3((0, 0, -0.03)), 0.019, 0.01, rr=0.003, R=rot_from_axes(z_axis=inw)), 0.002, 8)
    fd.add(RoundBox(pc + inw * 0.01 + v3((0, 0, 0.035)) + tg * 0.03, (0.012, 0.008, 0.008), 0.003, R=R), 0.002, 12)
    fd.add(RoundBox(pc + inw * 0.009 + v3((0, 0, 0.035)) - tg * 0.025, (0.03, 0.002, 0.016), 0.002, R=R), 0.002, 13)
    # the muffler on its far end, the fuel cap on top
    mc = body + tg * (GEN_H[0] + 0.03) + v3((0, 0, 0.03))
    fd.add(Cylinder(mc, 0.032, 0.18, rr=0.012, R=rot_from_axes(z_axis=inw)), 0.006, 7)
    fd.add(RoundCone(mc + inw * 0.09, mc + inw * 0.13 + v3((0, 0, 0.02)), 0.012, 0.01), 0.004, 7)
    fd.add(Cylinder(body + v3((0, 0, GEN_H[2] + 0.03)) - tg * 0.1, 0.026, 0.026, rr=0.006), 0.004, 8)
    # the jerrycan beside it (toward the lawn's end)
    jc = c + tg * 0.36 + inw * 0.06 + v3((0, 0, 0.17))
    Rj = R @ euler(0, 0, 0.2)
    fd.add(RoundBox(jc, (0.07, 0.11, 0.16), 0.02, R=Rj, disp=ham, disp_amp=0.001), 0.0, 0)
    for s in (-1, 1):                                                                           # the pressed X on its sides
        fd.sub(RoundBox(jc + Rj[:, 0] * (s * 0.071), (0.004, 0.006, 0.13), 0.002, R=Rj @ euler(0.6, 0, 0)), 0.003)
        fd.sub(RoundBox(jc + Rj[:, 0] * (s * 0.071), (0.004, 0.006, 0.13), 0.002, R=Rj @ euler(-0.6, 0, 0)), 0.003)
    for k in (-1, 0, 1):                                                                        # its three handles
        fd.add(RoundBox(jc + Rj[:, 1] * (k * 0.045) + v3((0, 0, 0.175)), (0.012, 0.012, 0.022), 0.006, R=Rj), 0.004, 0)
    fd.add(RoundCone(jc + Rj[:, 1] * 0.085 + v3((0, 0, 0.15)), jc + Rj[:, 1] * 0.12 + v3((0, 0, 0.19)), 0.02, 0.016), 0.006, 0)
    return fd


# ---------------------------------------------------------------------------------------------- the equipment case
CASE_H = (0.27, 0.17, 0.085)


def case_frame():
    c, inw, tg = CASE
    return v3((c[0], c[1], ground_height(c[0], c[1]))), inw, tg, np.stack([tg, inw, v3((0, 0, 1))], 1)


def case_field():
    """fieldgun: a rugged black case (8) lying open: ribbed sides, steel latches (7), its lid up behind it (thrown back past
    upright) lined with grey foam (5); grey foam in the case with cut-outs holding a yellow drill (0), two steel spanners
    and screwdrivers (black handles)."""
    fd = Field("Case")
    c, inw, tg, R = case_frame()
    b = c + v3((0, 0, CASE_H[2] + 0.004))
    fd.add(RoundBox(b, CASE_H, 0.02, R=R), 0.0, 8)
    fd.sub(RoundBox(b + v3((0, 0, 0.04)), (CASE_H[0] - 0.018, CASE_H[1] - 0.018, CASE_H[2]), 0.01, R=R), 0.004)
    for k in range(4):                                                                          # ribs round its sides
        fd.add(RoundBox(b + v3((0, 0, -0.03 + 0.02 * k)), (CASE_H[0] + 0.004, CASE_H[1] + 0.004, 0.004), 0.003, R=R), 0.003, 8)
    for s in (-1, 1):
        fd.add(RoundBox(b + tg * (s * 0.13) + inw * (CASE_H[1] + 0.006) + v3((0, 0, 0.03)), (0.022, 0.008, 0.022), 0.004, R=R), 0.003, 7)
        fd.add(RoundBox(b + tg * (s * (CASE_H[0] + 0.012)) + v3((0, 0, 0.03)), (0.008, 0.04, 0.012), 0.004, R=R), 0.003, 8)   # handles
    # the foam bed and the tools in it
    ft = b + v3((0, 0, CASE_H[2] - 0.012))
    fd.add(RoundBox(ft - v3((0, 0, 0.03)), (CASE_H[0] - 0.02, CASE_H[1] - 0.02, 0.03), 0.006, R=R), 0.002, 5)
    # (the drill: yellow body, black grip and battery)
    d0 = ft + tg * 0.08 + inw * 0.01
    fd.add(RoundBox(d0 + tg * 0.03, (0.06, 0.028, 0.022), 0.014, R=R), 0.002, 0)
    fd.add(RoundBox(d0 - tg * 0.02 + inw * 0.05, (0.018, 0.04, 0.018), 0.01, R=R), 0.002, 8)
    fd.add(RoundBox(d0 - tg * 0.02 + inw * 0.095, (0.03, 0.02, 0.022), 0.008, R=R), 0.002, 8)
    fd.add(RoundCone(d0 + tg * 0.09, d0 + tg * 0.14, 0.012, 0.004), 0.002, 7)
    # spanners and screwdrivers
    for k in range(2):
        s0 = ft - tg * (0.06 + 0.05 * k) + inw * 0.0
        fd.add(RoundBox(s0, (0.007, 0.08, 0.004), 0.003, R=R), 0.002, 7)
        for e in (-1, 1):
            fd.add(Cylinder(s0 + inw * (e * 0.085), 0.016, 0.008, rr=0.003), 0.003, 7)
    for k in range(2):
        s0 = ft - tg * (0.19 - 0.025 * k) + inw * 0.0
        fd.add(RoundCone(s0 - inw * 0.09, s0 - inw * 0.02, 0.011, 0.011), 0.002, 8)
        fd.add(RoundCone(s0 - inw * 0.02, s0 + inw * 0.08, 0.004, 0.0035), 0.002, 7)
    # the lid, hinged on the back edge, thrown back
    hinge = b - inw * CASE_H[1] + v3((0, 0, CASE_H[2]))
    lid_dir = norm(-inw * 0.25 + v3((0, 0, 1)))
    Rl = np.stack([tg, norm(np.cross(tg, lid_dir)), lid_dir], 1)
    lc = hinge + lid_dir * CASE_H[1]
    fd.add(RoundBox(lc - Rl[:, 1] * 0.012, (CASE_H[0], 0.03, CASE_H[1]), 0.02, R=Rl), 0.004, 8)
    fd.add(RoundBox(lc + Rl[:, 1] * 0.006, (CASE_H[0] - 0.024, 0.014, CASE_H[1] - 0.024), 0.008, R=Rl), 0.003, 5)
    for k in range(3):
        fd.sub(RoundBox(lc + Rl[:, 1] * 0.02 + tg * (-0.12 + 0.12 * k), (0.03, 0.01, 0.08), 0.008, R=Rl), 0.003)
    return fd


# ---------------------------------------------------------------------------------------------- the crate and the laptop
CRATE_H = (0.21, 0.13, 0.11)


def crate_frame():
    c, inw, tg = CRATE
    return v3((c[0], c[1], ground_height(c[0], c[1]))), inw, tg, np.stack([tg, inw, v3((0, 0, 1))], 1)


def crate_field():
    """fieldgun: an olive-drab ammunition crate (painted wood, 0) with cleats round its ends, white stencilled lines (13),
    steel hasps (7), rope handles (10)."""
    fd = Field("Crate")
    c, inw, tg, R = crate_frame()
    b = c + v3((0, 0, CRATE_H[2] + 0.002))
    grain = lambda P: F(0.0012) * NOISE(P * np.array([10.0, 60.0, 60.0], F))
    fd.add(RoundBox(b, CRATE_H, 0.012, R=R, disp=grain, disp_amp=0.0015), 0.0, 0)
    for s in (-1, 1):
        fd.add(RoundBox(b + tg * (s * (CRATE_H[0] - 0.02)), (0.022, CRATE_H[1] + 0.008, CRATE_H[2] + 0.004), 0.008, R=R), 0.004, 0)
        fd.add(Torus(b + tg * (s * (CRATE_H[0] + 0.006)) + v3((0, 0, 0.02)), 0.03, 0.007, R=rot_from_axes(z_axis=tg)), 0.003, 10)
    fd.sub(RoundBox(b + v3((0, 0, CRATE_H[2] - 0.035)), (CRATE_H[0] + 0.05, CRATE_H[1] + 0.05, 0.0025), 0.001, R=R), 0.002)   # the lid's seam
    for s in (-1, 1):
        fd.add(RoundBox(b + inw * (CRATE_H[1] + 0.004) + tg * (s * 0.1) + v3((0, 0, CRATE_H[2] - 0.04)), (0.014, 0.006, 0.026), 0.003, R=R), 0.002, 7)
    def stencil(P):
        q = (P - b.astype(F)) @ R.astype(F)
        rows = np.minimum(np.abs(q[:, 2] - F(0.01)) - F(0.008), np.abs(q[:, 2] + F(0.03)) - F(0.006))
        return np.maximum(np.maximum(rows, np.abs(q[:, 0]) - F(0.12)), F(CRATE_H[1] - 0.004) - q[:, 1])
    fd.paint(Func(stencil, b - 0.4, b + 0.4), 13)
    return fd


LAP_H = (0.13, 0.095, 0.011)


def laptop_frame():
    c, inw, tg, R = crate_frame()
    top = c + v3((0, 0, 2 * CRATE_H[2] + 0.004))
    Rz = euler(0, 0, math.radians(-25.0))                 # turned toward the front, the screen to him and to the camera
    tgl, inl = Rz @ tg, Rz @ inw
    return top, inl, tgl, np.stack([tgl, inl, v3((0, 0, 1))], 1)


def laptop_field():
    """fieldgun: a rugged laptop (black 8, gunmetal corners 5), open on the crate, the keyboard (5) toward him, the screen's
    bezel (8) round the glowing screen (LaptopScreen)."""
    fd = Field("Laptop")
    top, inw, tg, R = laptop_frame()
    b = top + v3((0, 0, LAP_H[2]))
    fd.add(RoundBox(b, LAP_H, 0.008, R=R), 0.0, 8)
    fd.add(RoundBox(b + v3((0, 0, LAP_H[2] - 0.001)) + inw * 0.01, (LAP_H[0] - 0.016, LAP_H[1] * 0.55, 0.002), 0.002, R=R), 0.001, 5)
    for a in (-1, 1):
        for d in (-1, 1):
            fd.add(Sphere(b + tg * (a * (LAP_H[0] - 0.006)) + inw * (d * (LAP_H[1] - 0.006)), 0.017), 0.004, 5)
    hinge = b - inw * LAP_H[1] + v3((0, 0, LAP_H[2]))
    up = norm(v3((0, 0, 1)) - inw * 0.3)
    Rs = np.stack([tg, norm(np.cross(up, tg)), up], 1)
    sc = hinge + up * LAP_H[1]
    fd.add(RoundBox(sc - Rs[:, 1] * 0.0, (LAP_H[0], 0.009, LAP_H[1]), 0.007, R=Rs), 0.004, 8)
    return fd


def laptop_screen_field():
    fd = Field("LaptopScreen")
    top, inw, tg, R = laptop_frame()
    b = top + v3((0, 0, LAP_H[2]))
    hinge = b - inw * LAP_H[1] + v3((0, 0, LAP_H[2]))
    up = norm(v3((0, 0, 1)) - inw * 0.3)
    Rs = np.stack([tg, norm(np.cross(up, tg)), up], 1)
    sc = hinge + up * (LAP_H[1] + 0.006)
    n = Rs[:, 1]
    if n @ inw < 0:
        n = -n
    fd.add(RoundBox(sc + n * 0.008, (LAP_H[0] - 0.016, 0.002, LAP_H[1] - 0.022), 0.002, R=Rs), 0.0)
    return fd


# ---------------------------------------------------------------------------------------------- the drone and its mat
def drone_frame():
    c, inw, tg = DRONE
    return v3((c[0], c[1], ground_height(c[0], c[1]))), inw, tg, np.stack([tg, inw, v3((0, 0, 1))], 1) @ euler(0, 0, 0.3)


def drone_field():
    """fieldgun: the landing mat (black rubber 8, a white ring and H, 13); the quadcopter: a tan body shell (0) on a gunmetal
    frame (5), four black arms and motors (8), two-bladed props (5), black skids, a camera on a gimbal at its nose (a
    steel lens, 7)."""
    fd = Field("Drone")
    c, inw, tg, R = drone_frame()
    mat = c + v3((0, 0, 0.006))
    fd.add(RoundBox(mat, (0.21, 0.21, 0.008), 0.006, R=R), 0.0, 8)
    def mark(P):
        q = (P - mat.astype(F)) @ R.astype(F)
        r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        ring = np.abs(r - F(0.165)) - F(0.012)
        hb = np.minimum(np.maximum(np.abs(np.abs(q[:, 0]) - F(0.05)) - F(0.013), np.abs(q[:, 1]) - F(0.075)),
                        np.maximum(np.abs(q[:, 0]) - F(0.05), np.abs(q[:, 1]) - F(0.012)))
        return np.maximum(np.minimum(ring, hb), F(0.004) - q[:, 2])
    fd.paint(Func(mark, mat - 0.3, mat + 0.3), 13)
    body = c + v3((0, 0, 0.075))
    fd.add(RoundBox(body, (0.055, 0.085, 0.024), 0.02, R=R), 0.004, 0)
    fd.add(RoundBox(body - v3((0, 0, 0.02)), (0.045, 0.07, 0.014), 0.01, R=R), 0.006, 5)
    fd.add(RoundBox(body + v3((0, 0, 0.018)) - R[:, 1] * 0.02, (0.03, 0.04, 0.012), 0.01, R=R), 0.006, 5)   # battery on top
    for a in range(4):
        d = R @ norm(v3((1 if a in (0, 3) else -1, 1 if a < 2 else -1, 0)))
        m = body + d * 0.15 + v3((0, 0, 0.012))
        fd.add(RoundCone(body + d * 0.04, m, 0.011, 0.009), 0.004, 8)
        fd.add(Cylinder(m + v3((0, 0, 0.006)), 0.017, 0.028, rr=0.005), 0.004, 8)
        fd.add(Cylinder(m + v3((0, 0, 0.024)), 0.005, 0.012, rr=0.002), 0.002, 7)
        pa = 0.6 + a * 1.1
        pd = v3((math.cos(pa), math.sin(pa), 0.0))
        fd.add(RoundBox(m + v3((0, 0, 0.03)), (0.075, 0.009, 0.0022), 0.002, R=rot_from_axes(x_axis=pd, z_axis=(0, 0, 1)) @ euler(0.15, 0, 0)), 0.002, 5)
    for s in (-1, 1):                                                                           # skids
        a0 = body + R[:, 0] * (s * 0.045) - v3((0, 0, 0.02))
        f0, f1 = c + R[:, 0] * (s * 0.07) + R[:, 1] * 0.07 + v3((0, 0, 0.018)), c + R[:, 0] * (s * 0.07) - R[:, 1] * 0.07 + v3((0, 0, 0.018))
        fd.add(RoundCone(f0, f1, 0.006, 0.006), 0.003, 8)
        fd.add(RoundCone(a0, lerp(f0, f1, 0.5), 0.006, 0.006), 0.003, 8)
    nose = body - R[:, 1] * 0.09 - v3((0, 0, 0.01))
    fd.add(Sphere(nose, 0.022), 0.006, 8)
    fd.add(Cylinder(nose - R[:, 1] * 0.018, 0.011, 0.012, rr=0.003, R=rot_from_axes(z_axis=R[:, 1])), 0.002, 7)
    return fd


# ---------------------------------------------------------------------------------------------- cables
def cable_paths():
    """The cables over the asphalt: generator -> case (round behind the pad), case -> the crate (round its right side)."""
    gc, gi, gt, _ = gen_frame()
    cc, ci, ct, _ = case_frame()
    kc, ki, kt, _ = crate_frame()
    def arc(a0, a1, r, n):
        out = []
        for i in range(n):
            a = math.radians(a0 + (a1 - a0) * i / (n - 1))
            x, y = math.cos(a) * r, math.sin(a) * r
            out.append(v3((x, y, ground_height(x, y) + 0.009)))
        return out
    p0 = gc + gi * (GEN_H[1] + 0.02) - gt * 0.03 + v3((0, 0, 0.12))
    g_out = [p0, p0 + gi * 0.05 - v3((0, 0, 0.06)), p0 + gi * 0.09 - v3((0, 0, 0.1))]
    g_out[-1][2] = ground_height(g_out[-1][0], g_out[-1][1]) + 0.01
    path1 = g_out + arc(58.0, 122.0, 0.86, 7) + [cc + ci * (CASE_H[1] + 0.02) + v3((0, 0, 0.01)), cc + ci * (CASE_H[1]) + v3((0, 0, 0.05))]
    path2 = [cc + ci * CASE_H[1] - ct * 0.12 + v3((0, 0, 0.05)), cc + ci * (CASE_H[1] + 0.03) - ct * 0.14 + v3((0, 0, 0.01))] + arc(160.0, 196.0, 0.88, 5) + \
        [kc + ki * (CRATE_H[1] + 0.03) + v3((0, 0, 0.01)), kc + ki * (CRATE_H[1] + 0.01) + v3((0, 0, 0.05)),
         kc + ki * CRATE_H[1] + v3((0, 0, 2 * CRATE_H[2] + 0.01))]
    for p in path1 + path2:
        if math.hypot(p[0], p[1]) > 0.84:
            p[2] = max(p[2], ground_height(p[0], p[1]) + 0.009)
    return [path1, path2]


def cables_field():
    """Black rubber cables (fieldgun 8) lying over the asphalt, a plug (5) at the case."""
    fd = Field("Cables")
    for pts in cable_paths():
        fd.add(Chain(pts, [0.009] * len(pts), k=0.02), 0.004, 8)
    return fd


# ---------------------------------------------------------------------------------------------- grass in the lawn
def _blocked(c, pad=0.0):
    if not _in_lawn(c[0], c[1], -pad):
        return True
    gc, gi, gt, _ = gen_frame()
    if math.hypot(c[0] - gc[0], c[1] - gc[1]) < 0.3 + pad:
        return True
    cc, ci, ct, _ = case_frame()
    if math.hypot(c[0] - cc[0], c[1] - cc[1]) < 0.3 + pad:
        return True
    return False


def grass_geometry(seed=41):
    rs = np.random.RandomState(seed)
    V, Fc, UV, TUFT = [], [], [], []
    tufts = []
    tries = 0
    while len(tufts) < 14 and tries < 6000:
        tries += 1
        a = math.radians(rs.uniform(LAWN_A[0] + 3, LAWN_A[1] - 3))
        r = rs.uniform(LAWN_R0 + 0.07, GROUND_R - 0.05)
        c = v3((math.cos(a) * r, math.sin(a) * r, 0))
        if _blocked(c, 0.02):
            continue
        if any(np.linalg.norm(c[:2] - t[:2]) < 0.07 for t in tufts):
            continue
        tufts.append(c)
    for ti, c in enumerate(tufts):
        for b in range(rs.randint(9, 13)):
            ang = rs.uniform(0, 2 * math.pi)
            out = v3((math.cos(ang), math.sin(ang), 0))
            root = c + out * rs.uniform(0, 0.04)
            root[2] = GROUND_TOP + 0.03
            d = norm(out * rs.uniform(0.15, 0.45) + v3((0, 0, 1)))
            L = rs.uniform(0.07, 0.13)
            v, f, uv = _b.blade_mesh(root, d, L, rs.uniform(0.022, 0.032), out * rs.uniform(0.4, 0.9) + v3((0, 0, -0.2)), segs=3,
                                     twist=rs.uniform(-0.6, 0.6))
            base = len(V)
            V += v
            Fc += [tuple(base + i for i in q) for q in f]
            UV += uv
            TUFT += [ti] * len(v)
    return np.array(V), Fc, np.array(UV), np.array(TUFT)


def flower_geometry(seed=43):
    return []


def fields():
    return [("Ground", ground_field(), 0.007), ("Lawn", lawn_field(), 0.006), ("Pad", pad_field(), 0.004),
            ("Rim", rim_field(), 0.0022), ("Glowmarks", glowmarks_field(), 0.002), ("Generator", generator_field(), 0.003),
            ("Case", case_field(), 0.0026), ("Crate", crate_field(), 0.003), ("Laptop", laptop_field(), 0.0022),
            ("LaptopScreen", laptop_screen_field(), 0.0015), ("Drone", drone_field(), 0.0022), ("Cables", cables_field(), 0.003)]


REGION_PARTS = ("Ground", "Pad", "Rim", "Generator", "Case", "Crate", "Laptop", "Drone", "Cables")
LOW_TARGETS = {"Ground": 1700, "Lawn": 400, "Pad": 1700, "Rim": 900, "Glowmarks": 300, "Generator": 2300, "Case": 2000,
               "Crate": 800, "Laptop": 600, "LaptopScreen": 40, "Drone": 1800, "Cables": 500}
OLIVE = (0.4, 0.42, 0.28)
TAN = (0.6, 0.5, 0.36)
YELLOW = (0.93, 0.74, 0.14)
GEAR = dict(grey=(0.3, 0.31, 0.33), white=(0.92, 0.91, 0.88))
MAT_OVERRIDES = {"Ground": ("pavement", {"name": "HQ_ApronAsphalt"}),
                 "Pad": ("pavement", {"name": "HQ_ApronConcrete"}),
                 "Lawn": ("ground", {"name": "HQ_ApronLawn"}),
                 "Rim": ("fieldgun", dict(GEAR, name="HQ_PadBezels")),
                 "Generator": ("fieldgun", dict(GEAR, name="HQ_Generator", olive=OLIVE)),
                 "Case": ("fieldgun", dict(GEAR, name="HQ_EquipCase", olive=YELLOW)),
                 "Crate": ("fieldgun", dict(GEAR, name="HQ_AmmoCrate", olive=OLIVE)),
                 "Laptop": ("fieldgun", dict(GEAR, name="HQ_Laptop")),
                 "Drone": ("fieldgun", dict(GEAR, name="HQ_Drone", olive=TAN)),
                 "Cables": ("fieldgun", dict(GEAR, name="HQ_Cables"))}
GLOW = {"Glowmarks": ((1.0, 0.64, 0.2), 1.0, 0.5), "LaptopScreen": ((0.36, 0.86, 1.0), 0.9, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
