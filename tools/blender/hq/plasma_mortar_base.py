"""Plasma Mortar base: a firing pad of the tech corps. A round pad of dark graphite floor plates (seams between them, a
few plates with a tread pattern, bolts at their corners) with a band of yellow-and-black hazard striping round its edge;
nothing on the pad stands proud of it (the mortar and its crew turn over it). Round it a raised gunmetal rim with a
glowing violet strip in a channel along its top (broken by bolted clamps). Round the rim an apron of white epoxy floor
tiles with yellow hazard lines, and on it, behind the pad: a small reactor (a gunmetal drum ringed with cooling fins, a
band of violet windows round its waist, a domed vent cap), a rack of spare plasma cells (a low case with six cells
standing in their sockets, cores glowing), a terminal (a post carrying an angled screen with violet readouts and a
keyboard ledge); black cables in floor channels from the reactor and the terminal to junction boxes on the rim; two
bollards with violet tops at the pad's front corners. The glows (rim strip, reactor windows, cell cores, the screen's
readouts, the bollards' tops) are one emissive mesh (`Neon`)."""
import math
import numpy as np
from sdf import (Field, Sphere, Ellipsoid, RoundCone, RoundBox, Torus, Cylinder, Plane, Func, Chain, v3, norm,
                 rot_from_axes, smax, NOISE, F, euler)
from caveman import Inter, Shell
import plasma_mortar as _m

GROUND_R = 1.36
APRON_Z = 0.05                 # the apron's top
TOP_Z = 0.1                    # the pad's top: where the mortar and his feet rest
PAD_R = 0.97                   # the pad's edge (the rim begins)
RIM_R = (0.97, 1.1)            # the rim (inner, outer radius)
RIM_Z = 0.125                  # its top
STRIP_R = 1.035                # the violet strip's middle radius
STAND = v3((-_m.YAW_PIVOT[0], -_m.YAW_PIVOT[1], TOP_Z))
PLATE = 0.4                    # the floor plates' size
HAZ = (0.85, 0.95)             # the hazard band on the pad (radii)
N_CLAMP = 12
PROPS = {"reactor": math.radians(136.0), "cells": math.radians(78.0), "terminal": math.radians(34.0),
         "bollard_l": math.radians(-52.0), "bollard_r": math.radians(-128.0)}
PROP_R = 1.23                  # the props' middles (on the apron)
BASE_L, BLACK_L, VIO_L, WHITE_L, NAVY_L, GM_L, STEEL_L, GLASS_L, RUBBER_L, HAZ_L = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13


def _radial(P):
    return np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)


def _disc_sd(P, r, z0, z1, rr=0.012):
    dr = _radial(P) - F(r) + F(rr)
    dz = np.abs(P[:, 2] - F((z0 + z1) / 2)) - F((z1 - z0) / 2) + F(rr)
    return np.minimum(np.maximum(dr, dz), 0) + np.sqrt(np.maximum(dr, 0) ** 2 + np.maximum(dz, 0) ** 2) - F(rr)


def _annulus_sd(P, r0, r1, z0, z1, rr=0.008):
    r = _radial(P)
    dr = np.abs(r - F((r0 + r1) / 2)) - F((r1 - r0) / 2) + F(rr)
    dz = np.abs(P[:, 2] - F((z0 + z1) / 2)) - F((z1 - z0) / 2) + F(rr)
    return np.minimum(np.maximum(dr, dz), 0) + np.sqrt(np.maximum(dr, 0) ** 2 + np.maximum(dz, 0) ** 2) - F(rr)


def _cells(P, size):
    u = P[:, 0] / F(size) + F(0.5)
    v = P[:, 1] / F(size) + F(0.5)
    iu, iv = np.floor(u), np.floor(v)
    e = np.minimum(np.minimum(u - iu, F(1) - (u - iu)), np.minimum(v - iv, F(1) - (v - iv))) * F(size)
    rnd = np.abs(np.sin(iu * F(12.9898) + iv * F(78.233)) * F(43758.5453)) % F(1.0)
    return e, rnd, u - iu, v - iv


def ground_field():
    """The apron: white epoxy floor tiles (0) round the rim with grooved joints, a yellow (13) hazard line near its edge,
    its outer edge bevelled down."""
    fd = Field("Ground")
    R = GROUND_R
    lo, hi = (-R - 0.05, -R - 0.05, -0.2), (R + 0.05, R + 0.05, 0.15)
    fd.add(Func(lambda P: _disc_sd(P, R, -0.1, APRON_Z, rr=0.025), lo, hi,
                disp=lambda P: F(0.0006) * NOISE(P * F(40)), disp_amp=0.001), 0.0)
    def joints(P):
        e, rnd, fu, fv = _cells(P, 0.46)
        return np.maximum(np.maximum(e - F(0.003), np.abs(P[:, 2] - F(APRON_Z)) - F(0.006)), F(RIM_R[1] - 0.02) - _radial(P))
    fd.sub(Func(joints, lo, hi), 0.002)
    def line(P):
        return np.maximum(np.abs(_radial(P) - F(GROUND_R - 0.075)) - F(0.016), np.abs(P[:, 2] - F(APRON_Z)) - F(0.02))
    fd.paint(Func(line, lo, hi), HAZ_L)
    return fd


def pad_field():
    """The pad: dark graphite floor plates (0) with seams, some with a raised tread (diamond plate), bolts (9) at their
    corners; a band of hazard striping round its edge (yellow 13 and black 5); its side wall black."""
    fd = Field("Pad")
    R = PAD_R + 0.01
    lo, hi = (-R - 0.02, -R - 0.02, -0.12), (R + 0.02, R + 0.02, TOP_Z + 0.03)
    fd.add(Func(lambda P: _disc_sd(P, R, -0.08, TOP_Z, rr=0.01), lo, hi,
                disp=lambda P: F(0.0005) * NOISE(P * F(60)), disp_amp=0.001), 0.0)
    def seams(P):
        e, rnd, fu, fv = _cells(P, PLATE)
        return np.maximum(np.maximum(e - F(0.0035), np.abs(P[:, 2] - F(TOP_Z)) - F(0.006)), _radial(P) - F(HAZ[0] - 0.01))
    fd.sub(Func(seams, lo, hi), 0.002)
    def tread(P):
        e, rnd, fu, fv = _cells(P, PLATE)
        a = (P[:, 0] + P[:, 1]) * F(45.0)
        b = (P[:, 0] - P[:, 1]) * F(45.0)
        bumps = np.maximum(np.abs(np.sin(a)) - F(0.25), np.abs(np.sin(b * F(3.0))) - F(0.45))
        on = (rnd > F(0.55)) & (rnd < F(0.8)) & (e > F(0.03))
        d = np.maximum(bumps * F(0.004), np.abs(P[:, 2] - F(TOP_Z + 0.001)) - F(0.0016))
        return np.where(on & (_radial(P) < F(HAZ[0] - 0.03)), d, F(1.0))
    fd.add(Func(tread, lo, hi), 0.0008)
    # bolts at the plates' corners (inside the hazard band)
    n = int(R / PLATE) + 2
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            cx, cy = (i - 0.5) * PLATE, (j - 0.5) * PLATE
            for dx in (-0.035, 0.035):
                for dy in (-0.035, 0.035):
                    q = v3((cx + dx, cy + dy, TOP_Z))
                    if math.hypot(q[0], q[1]) < HAZ[0] - 0.04:
                        fd.add(Cylinder(q + v3((0, 0, 0.002)), 0.009, 0.006, rr=0.002), 0.001, GM_L)
    # the hazard band: yellow with black diagonal stripes
    def band(P):
        return np.maximum(np.abs(_radial(P) - F((HAZ[0] + HAZ[1]) / 2)) - F((HAZ[1] - HAZ[0]) / 2), np.abs(P[:, 2] - F(TOP_Z)) - F(0.015))
    fd.paint(Func(band, lo, hi), HAZ_L)
    def stripes(P):
        a = np.arctan2(P[:, 1], P[:, 0])
        r = _radial(P)
        ph = (a * F(0.9) + (r - F(0.9))) / F(0.055)
        st = np.abs((ph % F(2.0)) - F(1.0)) - F(0.5)
        return np.maximum(np.maximum(np.abs(r - F((HAZ[0] + HAZ[1]) / 2)) - F((HAZ[1] - HAZ[0]) / 2 - 0.004), np.abs(P[:, 2] - F(TOP_Z)) - F(0.015)), st * F(0.05))
    fd.paint(Func(stripes, lo, hi), BLACK_L)
    # the side wall below the rim: black
    fd.paint(Func(lambda P: P[:, 2] - F(TOP_Z - 0.03), lo, hi), BLACK_L)
    return fd


def rim_field():
    """The rim: a raised gunmetal ring (9) with a channel along its top (the violet strip lies in it), bolted clamps across
    the channel (steel 10), a black (5) lip on its inside; its outer face with grooves."""
    fd = Field("Rim")
    lo, hi = (-RIM_R[1] - 0.05, -RIM_R[1] - 0.05, -0.05), (RIM_R[1] + 0.05, RIM_R[1] + 0.05, RIM_Z + 0.05)
    fd.add(Func(lambda P: _annulus_sd(P, RIM_R[0], RIM_R[1], 0.0, RIM_Z, rr=0.014), lo, hi), 0.0, GM_L)
    fd.sub(Func(lambda P: _annulus_sd(P, STRIP_R - 0.019, STRIP_R + 0.019, RIM_Z - 0.016, RIM_Z + 0.03, rr=0.004), lo, hi), 0.003)
    fd.paint(Func(lambda P: _annulus_sd(P, RIM_R[0] - 0.01, RIM_R[0] + 0.018, 0.0, RIM_Z + 0.02, rr=0.0), lo, hi), BLACK_L)
    for z in (0.05, 0.08):
        fd.sub(Func(lambda P, z=z: _annulus_sd(P, RIM_R[1] - 0.004, RIM_R[1] + 0.02, z - 0.0035, z + 0.0035, rr=0.0), lo, hi), 0.002)
    for k in range(N_CLAMP):
        a = 2 * math.pi * (k + 0.5) / N_CLAMP
        d = v3((math.cos(a), math.sin(a), 0.0))
        t = v3((-math.sin(a), math.cos(a), 0.0))
        R = np.stack([d, t, v3((0, 0, 1))], axis=1)
        c = d * STRIP_R + v3((0, 0, RIM_Z + 0.002))
        fd.add(RoundBox(c, (0.03, 0.022, 0.008), 0.005, R=R), 0.003, STEEL_L)
        for s in (-1, 1):
            fd.add(Cylinder(c + d * (s * 0.02) + v3((0, 0, 0.008)), 0.0055, 0.006, rr=0.002), 0.001, GM_L)
    return fd


def _prop_frame(name, r=PROP_R):
    a = PROPS[name]
    o = v3((math.cos(a), math.sin(a), 0.0))
    t = v3((-math.sin(a), math.cos(a), 0.0))
    return o * r + v3((0, 0, APRON_Z)), o, t


REACTOR_R, REACTOR_H = 0.12, 0.3


def reactor_field():
    """A small reactor: a gunmetal drum (9) on a black (5) plinth, ringed with cooling fins, a band of window slots round
    its waist (the violet glow behind), a graphite (0) domed vent cap with a vent ring, hazard (13) bands; a cable socket."""
    fd = Field("Reactor")
    c0, o, t = _prop_frame("reactor")
    fd.add(Cylinder(c0 + v3((0, 0, 0.025)), REACTOR_R + 0.03, 0.05, rr=0.012), 0.0, BLACK_L)
    zc = 0.05 + REACTOR_H / 2
    fd.add(Cylinder(c0 + v3((0, 0, zc)), REACTOR_R, REACTOR_H, rr=0.02), 0.006, GM_L)
    for k in range(16):
        a = 2 * math.pi * k / 16
        d = v3((math.cos(a), math.sin(a), 0.0))
        R = np.stack([np.cross(v3((0, 0, 1)), d), d, v3((0, 0, 1))], axis=1)
        for z0, z1 in ((0.07, 0.16), (0.26, 0.33)):
            fd.add(RoundBox(c0 + d * (REACTOR_R + 0.014) + v3((0, 0, (z0 + z1) / 2)), (0.004, 0.018, (z1 - z0) / 2), 0.002, R=R), 0.003, GM_L)
    # the window band: slots round the waist
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        d = v3((math.cos(a), math.sin(a), 0.0))
        R = np.stack([np.cross(v3((0, 0, 1)), d), d, v3((0, 0, 1))], axis=1)
        fd.sub(RoundBox(c0 + d * REACTOR_R + v3((0, 0, 0.21)), (0.018, 0.02, 0.03), 0.006, R=R), 0.003)
    fd.add(Cylinder(c0 + v3((0, 0, 0.21)), REACTOR_R - 0.012, 0.074, rr=0.004), 0.0, BLACK_L)
    for z in (0.17, 0.25):
        fd.add(Cylinder(c0 + v3((0, 0, z)), REACTOR_R + 0.006, 0.012, rr=0.004), 0.003, HAZ_L)
    top = c0 + v3((0, 0, 0.05 + REACTOR_H))
    fd.add(Inter(Ellipsoid(top, (REACTOR_R - 0.005, REACTOR_R - 0.005, 0.07)), Plane(top, (0, 0, -1)), 0.006), 0.012, BASE_L)
    fd.add(Torus(top + v3((0, 0, 0.045)), 0.05, 0.01), 0.004, GM_L)
    fd.add(Cylinder(top + v3((0, 0, 0.06)), 0.035, 0.03, rr=0.008), 0.004, BLACK_L)
    fd.add(Cylinder(c0 - o * (REACTOR_R + 0.01) + v3((0, 0, 0.09)), 0.024, 0.04, rr=0.006, R=rot_from_axes(z_axis=o)), 0.004, BLACK_L)
    _m.stencil(fd, "RX-2", c0 - o * (REACTOR_R + 0.001) + v3((0, 0, 0.12)), t, v3((0, 0, 1)), 0.028, WHITE_L, depth=0.01)
    return fd


CELL_CASE = (0.11, 0.17, 0.05)        # the spare-cell case's half depth (radial), length, height


def _cell_spots():
    c0, o, t = _prop_frame("cells")
    out = []
    for i in (-1, 0, 1):
        for j in (-0.5, 0.5):
            out.append(c0 + t * (i * 0.1) + o * (j * 0.1) + v3((0, 0, 2 * CELL_CASE[2])))
    return out


def cells_field():
    """A rack of spare plasma cells: a low graphite (0) case with hazard (13) corners and black handles, six sockets with
    violet rims, a cell standing in each (black canisters, gunmetal caps, their cores showing through slots)."""
    fd = Field("Cells")
    c0, o, t = _prop_frame("cells")
    R = np.stack([o, t, v3((0, 0, 1))], axis=1)
    hx, hy, hz = CELL_CASE
    cc = c0 + v3((0, 0, hz))
    fd.add(RoundBox(cc, (hx, hy, hz), 0.014, R=R), 0.0, BASE_L)
    for su in (-1, 1):
        for sv in (-1, 1):
            fd.add(RoundBox(cc + o * (su * (hx - 0.012)) + t * (sv * (hy - 0.012)), (0.02, 0.02, hz + 0.004), 0.006, R=R), 0.004, HAZ_L)
    for sv in (-1, 1):
        fd.add(RoundBox(cc + t * (sv * (hy + 0.008)) + v3((0, 0, 0.012)), (0.04, 0.008, 0.012), 0.005, R=R), 0.003, BLACK_L)
    for p in _cell_spots():
        fd.sub(Cylinder(p - v3((0, 0, 0.02)), _m.CELL_R + 0.005, 0.06), 0.002)
        fd.paint(Torus(p, _m.CELL_R + 0.012, 0.005), VIO_L)
        _m.cell_into(fd, p + v3((0, 0, _m.CELL_L / 2 - 0.05)), v3((0, 0, 1)), k=0.002, seed=float(p[0] * 7))
    return fd


TERM_H = 0.42


def terminal_field():
    """A terminal: a gunmetal post (9) on a black foot, a graphite (0) head carrying an angled screen (smoked glass 11; its
    readouts glow), a keyboard ledge (black 5, steel keys), a violet stripe."""
    fd = Field("Terminal")
    c0, o, t = _prop_frame("terminal")
    fd.add(RoundBox(c0 + v3((0, 0, 0.02)), (0.09, 0.09, 0.02), 0.01, R=np.stack([o, t, v3((0, 0, 1))], axis=1)), 0.0, BLACK_L)
    fd.add(RoundBox(c0 + v3((0, 0, TERM_H / 2)), (0.035, 0.05, TERM_H / 2), 0.012, R=np.stack([o, t, v3((0, 0, 1))], axis=1)), 0.008, GM_L)
    # the head: a slab tilted to face in toward the pad and up
    n = norm(-o * 0.75 + v3((0, 0, 0.66)))
    up = norm(np.cross(t, n))
    if up[2] < 0:
        up = -up
    Rh = np.stack([t, up, n], axis=1)
    hc = c0 + v3((0, 0, TERM_H + 0.04)) - o * 0.02
    fd.add(RoundBox(hc, (0.12, 0.085, 0.022), 0.014, R=Rh), 0.01, BASE_L)
    fd.add(RoundBox(hc + n * 0.02, (0.1, 0.066, 0.004), 0.004, R=Rh), 0.002, GLASS_L)
    fd.paint(RoundBox(hc + up * (0.085 - 0.006) + n * 0.01, (0.12, 0.006, 0.03), 0.002, R=Rh), VIO_L)
    # the keyboard ledge below the screen, toward the pad
    kc = c0 + v3((0, 0, TERM_H - 0.04)) - o * 0.1
    Rk = np.stack([t, -o, v3((0, 0, 1))], axis=1) @ euler(0.35, 0, 0)
    fd.add(RoundBox(kc, (0.1, 0.05, 0.012), 0.008, R=Rk), 0.006, BLACK_L)
    for i in range(5):
        for j in range(2):
            fd.add(RoundBox(kc + Rk @ v3((-0.07 + 0.035 * i, -0.015 + 0.03 * j, 0.012)), (0.012, 0.009, 0.004), 0.002, R=Rk), 0.001, STEEL_L)
    return fd


def _screen_frame():
    c0, o, t = _prop_frame("terminal")
    n = norm(-o * 0.75 + v3((0, 0, 0.66)))
    up = norm(np.cross(t, n))
    if up[2] < 0:
        up = -up
    hc = c0 + v3((0, 0, TERM_H + 0.04)) - o * 0.02
    return hc + n * 0.025, t, up, n


def cable_paths():
    """Cables from the reactor and from the terminal along the apron to junction boxes on the rim."""
    out = []
    for name, ja in (("reactor", PROPS["reactor"] - 0.18), ("terminal", PROPS["terminal"] + 0.17)):
        c0, o, t = _prop_frame(name)
        start = c0 - o * (REACTOR_R + 0.03 if name == "reactor" else 0.0) + v3((0, 0, 0.012 if name == "terminal" else 0.09))
        jo = v3((math.cos(ja), math.sin(ja), 0.0))
        end = jo * (RIM_R[1] + 0.03) + v3((0, 0, APRON_Z + 0.03))
        mid = (start + end) * 0.5 + jo * 0.05
        mid[2] = APRON_Z + 0.012
        out.append(([start, start - o * 0.05 + v3((0, 0, -0.04)) if name == "reactor" else start, mid, end], ja))
    return out


def cables_field():
    """Black rubber cables (12) on the apron, junction boxes (graphite 0, black lids 5) on the rim's outer face."""
    fd = Field("Cables")
    for pts, ja in cable_paths():
        fd.add(Chain(pts, [0.013] * len(pts), k=0.02), 0.0, RUBBER_L)
        jo = v3((math.cos(ja), math.sin(ja), 0.0))
        jt = v3((-math.sin(ja), math.cos(ja), 0.0))
        R = np.stack([jo, jt, v3((0, 0, 1))], axis=1)
        jb = jo * (RIM_R[1] + 0.03) + v3((0, 0, APRON_Z + 0.04))
        fd.add(RoundBox(jb, (0.035, 0.06, 0.04), 0.01, R=R), 0.004, BASE_L)
        fd.add(RoundBox(jb + v3((0, 0, 0.04)), (0.038, 0.063, 0.006), 0.004, R=R), 0.003, BLACK_L)
    return fd


def bollards_field():
    """Two bollards at the pad's front corners: gunmetal posts (9) with hazard (13) bands and black caps round their
    glowing tops."""
    fd = Field("Bollards")
    for name in ("bollard_l", "bollard_r"):
        c0, o, t = _prop_frame(name, 1.2)
        fd.add(Cylinder(c0 + v3((0, 0, 0.11)), 0.045, 0.22, rr=0.012), 0.0, GM_L)
        fd.add(Cylinder(c0 + v3((0, 0, 0.12)), 0.048, 0.04, rr=0.006), 0.003, HAZ_L)
        fd.add(Cylinder(c0 + v3((0, 0, 0.012)), 0.06, 0.024, rr=0.008), 0.004, BLACK_L)
        fd.add(Torus(c0 + v3((0, 0, 0.222)), 0.042, 0.008), 0.003, BLACK_L)
    return fd


def neon_field():
    """Everything that glows on the base (one emissive mesh): the rim's strip (in segments between the clamps), the
    reactor's window band, the spare cells' cores, the terminal's readouts, the bollards' tops."""
    fd = Field("Neon")
    lo, hi = (-RIM_R[1], -RIM_R[1], 0.0), (RIM_R[1], RIM_R[1], RIM_Z + 0.03)
    fd.add(Func(lambda P: _annulus_sd(P, STRIP_R - 0.014, STRIP_R + 0.014, RIM_Z - 0.02, RIM_Z - 0.004, rr=0.004), lo, hi), 0.0)
    c0, o, t = _prop_frame("reactor")
    fd.add(Cylinder(c0 + v3((0, 0, 0.21)), REACTOR_R - 0.004, 0.064, rr=0.006), 0.0)
    for p in _cell_spots():
        _m.core_into(fd, p + v3((0, 0, _m.CELL_L / 2 - 0.05)), v3((0, 0, 1)))
    sc, x, up, n = _screen_frame()
    R = np.stack([x, up, n], axis=1)
    for k, (w, dy) in enumerate(((0.07, 0.04), (0.05, 0.018), (0.08, -0.004), (0.04, -0.026))):
        fd.add(RoundBox(sc + x * (-0.075 + w) + up * dy, (w, 0.0055, 0.003), 0.002, R=R), 0.0)
    fd.add(Torus(sc + x * 0.055 - up * 0.02, 0.022, 0.004, R=R), 0.0)
    for name in ("bollard_l", "bollard_r"):
        c0, o, t = _prop_frame(name, 1.2)
        fd.add(Cylinder(c0 + v3((0, 0, 0.226)), 0.036, 0.014, rr=0.005), 0.0)
    return fd


def grass_geometry(seed=0):
    """(No grass on a lab floor.)"""
    return np.zeros((0, 3)), [], np.zeros((0, 2)), np.zeros(0, int)


def flower_geometry(seed=0):
    return []


def fields():
    return [("Ground", ground_field(), 0.006), ("Pad", pad_field(), 0.0032), ("Rim", rim_field(), 0.0028),
            ("Reactor", reactor_field(), 0.0024), ("Cells", cells_field(), 0.0018), ("Terminal", terminal_field(), 0.002),
            ("Cables", cables_field(), 0.0024), ("Bollards", bollards_field(), 0.0024), ("Neon", neon_field(), 0.002)]


REGION_PARTS = ("Ground", "Pad", "Rim", "Reactor", "Cells", "Terminal", "Cables", "Bollards")
LOW_TARGETS = {"Ground": 900, "Pad": 2600, "Rim": 2200, "Reactor": 1900, "Cells": 1600, "Terminal": 900, "Cables": 500,
               "Bollards": 500, "Neon": 900}
KIT = dict(_m.KIT)
MAT_OVERRIDES = {"Ground": ("modern_kit", dict(KIT, name="HQ_PmApron", base=(0.8, 0.82, 0.85), weave=0.0)),
                 "Pad": ("modern_kit", dict(KIT, name="HQ_PmPad", base=(0.17, 0.18, 0.21), weave=0.0)),
                 "Rim": ("modern_kit", dict(KIT, name="HQ_PmKit", base=_m.HOUSING, weave=0.0)),
                 "Reactor": ("modern_kit", dict(KIT, name="HQ_PmKit", base=_m.HOUSING, weave=0.0)),
                 "Cells": ("modern_kit", dict(KIT, name="HQ_PmKit", base=_m.HOUSING, weave=0.0)),
                 "Terminal": ("modern_kit", dict(KIT, name="HQ_PmKit", base=_m.HOUSING, weave=0.0)),
                 "Cables": ("modern_kit", dict(KIT, name="HQ_PmKit", base=_m.HOUSING, weave=0.0)),
                 "Bollards": ("modern_kit", dict(KIT, name="HQ_PmKit", base=_m.HOUSING, weave=0.0))}
GLOW = {"Neon": (_m.VIOLET, 1.1, 0.5)}
FLAME_PIVOT = None


def is_grass_face(c, n):
    return False
