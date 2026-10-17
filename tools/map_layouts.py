"""Hand-designed robot paths for all 30 maps (layout v2, BTD6-style variety).

Each map gets one or more paths (one portal each) built from straight runs with rounded corners, curves,
and path mechanics the sim understands (sim/sim.gd):
  fast   - speed lane (ice slide, minecart rails, conveyor, runway, data highway): ground robots x2
  slow   - mud, sand, fords, snowdrifts, decontamination: ground robots x0.55
  tunnel - mine shafts, sewers, gatehouses, subways: ground robots can't be targeted inside
  rift   - a time rift: the robot vanishes and steps out somewhere else on the map
Flying robots ignore fast/slow/tunnel (they fly over them) but are pulled through rifts.
Every path ends at the same exit on the right edge, where the base stands.

Writes "paths", "blockers" (re-placed clear of the new roads) and "layout": 2 into data/map_<id>.json and the
map blurbs into data/maps.json. Prints a report (lengths, robot travel time, free build space, warnings).
Run: python3 tools/map_layouts.py [--plot out.png] [map_id ...]
"""
import json
import math
import os
import random
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D = os.path.join(ROOT, "data")
BX0, BY0, BX1, BY1 = -15.0, -8.5, 15.0, 8.5
LX, RX, TY, BY = -15.6, 15.4, -9.2, 9.2      # where roads enter / leave (just past the map edge)
HALF = 0.85
MULT = {"fast": 2.0, "slow": 0.55}


def L(y): return (LX, y)        # enter from the left edge
def T(x): return (x, TY)        # from the top edge
def B(x): return (x, BY)        # from the bottom edge
def E(y): return (RX, y)        # the exit (right edge, where the base is)


class P:
    """A path: corner nodes joined by tagged runs. Corners are rounded unless sharp (arcs, rifts)."""

    def __init__(self, start, r=1.4):
        self.n = [tuple(map(float, start))]
        self.t = []
        self.sharp = [True]
        self.r = r

    def to(self, x, y=None, tag=None, sharp=False):
        if y is None:
            x, y = x
        self.n.append((float(x), float(y)))
        self.t.append(tag)
        self.sharp.append(sharp)
        return self

    def fast(self, x, y=None): return self.to(x, y, "fast")
    def slow(self, x, y=None): return self.to(x, y, "slow")
    def tunnel(self, x, y=None): return self.to(x, y, "tunnel")
    def rift(self, x, y=None): return self.to(x, y, "rift")

    def arc(self, cx, cy, rad, a0, a1, tag=None, step=12.0):
        """Curve around (cx, cy). Angles in degrees, 0 = east, 90 = south (screen down). Starts at a0."""
        n = max(2, int(abs(a1 - a0) / step))
        for k in range(1, n + 1):
            a = math.radians(a0 + (a1 - a0) * k / n)
            self.to(cx + rad * math.cos(a), cy + rad * math.sin(a), tag, sharp=True)
        return self

    def then(self, tail):
        for x, y, tag in tail:
            self.to(x, y, tag)
        return self

    # ---- expand: rounded corners, then zones / rifts by point index
    def build(self):
        pts = [self.n[0]]
        tags = []
        n = self.n
        for i in range(1, len(n)):
            tin = self.t[i - 1]
            last = i == len(n) - 1
            tout = None if last else self.t[i]
            p = n[i]
            if last or self.sharp[i] or tin == "rift" or tout == "rift":
                pts.append(p)
                tags.append(tin)
                continue
            a, c = n[i - 1], n[i + 1]
            lin = math.dist(a, p)
            lout = math.dist(p, c)
            din = ((p[0] - a[0]) / lin, (p[1] - a[1]) / lin)
            dout = ((c[0] - p[0]) / lout, (c[1] - p[1]) / lout)
            cross = din[0] * dout[1] - din[1] * dout[0]
            if abs(cross) < 0.02 and din[0] * dout[0] + din[1] * dout[1] > 0:
                pts.append(p)
                tags.append(tin)
                continue
            r = min(self.r, 0.45 * lin, 0.45 * lout)
            s = (p[0] - din[0] * r, p[1] - din[1] * r)
            e = (p[0] + dout[0] * r, p[1] + dout[1] * r)
            pts.append(s)
            tags.append(tin)
            mid_tag = tin if tin == tout else None
            for k in range(1, 7):
                u = k / 6.0
                q = ((1 - u) ** 2 * s[0] + 2 * (1 - u) * u * p[0] + u * u * e[0],
                     (1 - u) ** 2 * s[1] + 2 * (1 - u) * u * p[1] + u * u * e[1])
                pts.append(q)
                tags.append(mid_tag)
        spec = {"pts": [[round(x, 3), round(y, 3)] for x, y in pts]}
        rifts = [k + 1 for k, tg in enumerate(tags) if tg == "rift"]
        if rifts:
            spec["rift"] = rifts
        zones = []
        k = 0
        while k < len(tags):
            tg = tags[k]
            if tg in ("fast", "slow", "tunnel"):
                j = k
                while j + 1 < len(tags) and tags[j + 1] == tg:
                    j += 1
                z = {"k": tg, "a": k, "b": j + 1}
                if tg in MULT:
                    z["m"] = MULT[tg]
                zones.append(z)
                k = j + 1
            else:
                k += 1
        if zones:
            spec["zones"] = zones
        return spec


def seq(*nodes):
    """A shared tail: [(x, y, tag)] from (x, y) or (x, y, tag) items."""
    return [(n[0], n[1], n[2] if len(n) > 2 else None) for n in nodes]


# =====================================================================================================
# The designs. Coordinates: x -15..15 left to right, y -8.5 (top of screen) .. 8.5 (bottom).
# =====================================================================================================
MAPS = {}


def design(mid, blurb):
    def deco(fn):
        MAPS[mid] = (fn, blurb)
        return fn
    return deco


# ---------------------------------------------------------------- Stone Age
@design("mammoth_valley", "One long winding trail that crosses itself. Towers at the crossing hit robots twice.")
def _():
    return [P(L(-3), 1.8).to(6, -3).to(6, 5).to(-6, 5).to(-6, -6.5).to(10, -6.5).to(10, 1.5).to(E(1.5))]


@design("glacier_pass", "Robots skid fast down the ice slide, then wade slowly through deep snow. Kill them in the drift.")
def _():
    return [P(T(4.5)).to(4.5, -4).to(-11, -4).to(-11, 4.5).to(-8, 4.5).fast(8.5, 4.5).slow(8.5, 0).to(8.5, -6).to(E(-6))]


@design("volcano_ridge", "Two portals. Their trails meet and dive into a lava tube where no tower can reach them.")
def _():
    tail = seq((4, 0), (4, -6), (5.5, -6), (9.5, -6, "tunnel"), (11, -6), (11, 3), E(3))
    a = P(L(-5)).to(-6, -5).to(-6, 0).then(tail)
    b = P(B(-9)).to(-9, 5).to(2, 5).to(2, 0).then(tail)
    return [a, b]


# ---------------------------------------------------------------- Bronze Age
@design("river_delta", "Portals north and south. Both roads meet at the only bridge, then slog through the riverbank mud.")
def _():
    tail = seq((-3, 1.5), (4, 1.5), (4, -1.5, "slow"), (4, -6), (10, -6), (10, 5), E(5))
    a = P(L(-5.5)).to(-9, -5.5).to(-9, -2).to(-3, -2).then(tail)
    b = P(B(-12)).to(-12, 4.5).to(-6, 4.5).to(-6, 1.5).then(tail)
    return [a, b]


@design("desert_citadel", "The road spirals into the citadel, then vanishes into the catacombs and bursts out at your gate.")
def _():
    return [P(L(-6.5), 1.3).to(10.5, -6.5).to(10.5, 5.5).to(-10.5, 5.5).to(-10.5, -2).to(-3, -2)
            .to(-3, 1.5).to(0, 1.5).tunnel(12.5, 1.5).to(E(1.5))]


@design("copper_canyon", "Two mines. Robots ride minecart rails at double speed, and one trail runs through a mine shaft.")
def _():
    tail = seq((2, -1), (9, -1), (9, 6), E(6))
    a = P(L(-5)).to(-10, -5).to(-10, 4).fast(2, 4).then(tail)
    b = P(T(6)).to(6, -5).to(4, -5).tunnel(-2, -5).to(-4, -5).to(-4, -1).then(tail)
    return [a, b]


# ---------------------------------------------------------------- Iron Age
@design("highland_ford", "The road fords the cold stream three times. Robots wade slowly through every crossing.")
def _():
    return [P(B(-11)).to(-11, -5.5).to(-6, -5.5).to(-6, 5.5).to(-1, 5.5).to(-1, -6.5)
            .to(4.4, -6.5).slow(7.8, -6.5).to(10, -6.5).to(10, -0.5).to(7.4, -0.5).slow(4.0, -0.5).to(2.4, -0.5)
            .to(2.4, 5.5).to(4.6, 5.5).slow(8.0, 5.5).to(E(5.5))]


@design("ember_forge", "A time rift flickers in the forge. Robots step in on the left and walk out on the right.")
def _():
    return [P(L(-6)).to(-9, -6).to(-9, 5.5).to(-3, 5.5).to(-3, -2).rift(4, 6).to(4, 0).slow(4, -6)
            .to(10, -6).to(10, 3).to(E(3))]


@design("mirefen_bog", "Two plank roads cross in the marsh. Robots sink into the mud where they meet.")
def _():
    tail = seq((8, 4), (11.5, 4), (11.5, -5), E(-5))
    a = P(L(-6)).to(2, -6).to(2, -3.5).slow(2, 0.5).to(2, 4).then(tail)
    b = P(L(5)).to(-4, 5).slow(-4, 0).to(-4, -2).to(8, -2).then(tail)
    return [a, b]


# ---------------------------------------------------------------- Classical
@design("olive_hills", "Robots run fast downhill and trudge slowly back up. A second trail joins halfway down the slope.")
def _():
    t = 0.68
    jx = -4 + 6 * t
    tail = seq((2, 6, "fast"), (7, 6), (11, -4, "slow"), E(-4))
    a = P(L(-6.5)).to(-4, -6.5).fast(jx, 2).then(tail)
    b = P(B(-12)).to(-12, 2).to(jx, 2).then(tail)
    return [a, b]


@design("marble_coast", "Two roads pass under old aqueducts, where robots are out of reach, then cross the inlet bridge.")
def _():
    tail = seq((5, -1), (8, -1), (8, 5), E(5))
    a = P(L(-1)).to(-6, -1).tunnel(-6, 4).to(-6, 6).to(2, 6).to(2, -1).then(tail)
    b = P(L(-6)).to(-3, -6).tunnel(2, -6).to(5, -6).then(tail)
    return [a, b]


@design("acropolis", "The main road loops around the temple hill and crosses itself. A short back stair comes from the north.")
def _():
    tail = seq((6, -2), (10, -2), (10, 5.5), E(5.5))
    a = P(L(-6)).to(2, -6).to(2, 5.5).to(-6, 5.5).to(-6, -2).then(tail)
    b = P(T(8.5)).to(8.5, -5.5).to(6, -5.5).then(tail)
    return [a, b]


# ---------------------------------------------------------------- Medieval
@design("hedgerow_fields", "Two lanes cross each other twice between the hedges. Cloakers hide in the crowd.")
def _():
    tail = seq((8, -2), (11, -2), E(-2))
    a = P(L(-5)).to(-2, -5).to(-2, 5.5).to(5, 5.5).to(5, -2).then(tail)
    b = P(L(4)).to(-8, 4).slow(-8, 1).to(8, 1).then(tail)
    return [a, b]


@design("castle_siege", "Two armies circle the castle, one over the north wall and one under the south. They meet in the moat at the back gate.")
def _():
    tail = seq((9, 0), E(0))
    a = P(L(-0.5)).to(-10, -0.5).to(-10, -5.5).to(9, -5.5).slow(9, -1.8).then(tail)
    b = P(B(-12)).to(-12, 5.5).to(9, 5.5).slow(9, 1.8).then(tail)
    return [a, b]


@design("darkwood", "The woods twist you around: near the end a rift throws the robots back to the start for a second lap.")
def _():
    return [P(L(-5)).to(-6, -5).to(-6, 4).to(2, 4).to(2, -5).to(9, -5).to(9, 1).rift(-12, 7).to(12, 7)
            .to(12, -2).to(E(-2))]


# ---------------------------------------------------------------- Gunpowder
@design("smugglers_harbor", "One road crosses the harbor bridge. The smugglers' road sneaks under the water in a tunnel.")
def _():
    tail = seq((10, 6), E(6))
    a = P(L(-5)).to(-4, -5).to(-4, 3).to(2, 3).to(2, -6).to(10, -6).then(tail)
    b = P(B(-10)).to(-10, 6).to(3, 6).tunnel(9, 6).then(tail)
    return [a, b]


@design("star_fort", "The road traces the star fort's bastions, zigzagging around a walled field in the middle.")
def _():
    cx, cy, ro, ri = 0.5, 0.0, 6.6, 3.0
    def pt(a, r): return (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    a = P(L(0), 0.9)
    for k, ang in enumerate([180, 216, 252, 288, 324, 360, 396]):
        a.to(*pt(ang, ro if k % 2 == 0 else ri))
    o36 = pt(396, ro)
    a.to(E(o36[1]))
    b = P(B(-1.5), 0.9).to(pt(108, ro)[0], 6.3).to(*pt(108, ro)).to(*pt(72, ri)).to(*o36).to(E(o36[1]))
    return [a, b]


@design("jungle_outpost", "Three trails out of the jungle. Robots zip down the vines fast before the trails meet.")
def _():
    tail = seq((3, -1), (3, 5), (10, 5), (10, -3), E(-3))
    a = P(L(-6.5)).to(-5, -6.5).to(-5, -1).then(tail)
    c = P(B(-10)).fast(-10, 2.5).to(0, 2.5).to(0, -1).then(tail)
    b = P(T(6.5)).fast(6.5, 0).to(6.5, 5).then(seq((10, 5), (10, -3), E(-3)))
    return [a, b, c]


# ---------------------------------------------------------------- Industrial
@design("railyard", "Robots ride the rails at double speed. Two lines cross in the middle of the yard.")
def _():
    tail = seq((4, 2), (4, -2), (11, -2), E(-2))
    a = P(L(-6)).fast(-6, -6).to(-6, 6).fast(4, 6).then(tail)
    b = P(L(2)).fast(4, 2).then(tail[1:])
    return [a, b]


@design("foundry_row", "An assembly line: conveyor belts rush robots along, and the smelter swallows them for a moment.")
def _():
    return [P(L(6), 1.2).to(-11, 6).fast(-11, -6).to(-6, -6).to(-6, 5).to(-1, 5).fast(-1, -6).to(4, -6)
            .to(4, 5).to(9, 5).to(9, 3).tunnel(9, -2).to(9, -4).to(E(-4))]


@design("smog_city", "Three portals in the smog. Two roads run through the sewers before everything meets downtown.")
def _():
    tail = seq((5, 0), (5, 5), (11, 5), E(5))
    a = P(L(-6)).to(-3, -6).to(-3, -5).tunnel(-3, -1).to(-3, 0).to(0, 0).then(tail)
    c = P(B(-9)).to(-9, 4).to(-7, 4).tunnel(-2, 4).to(0, 4).to(0, 0).then(tail)
    b = P(T(9)).to(9, -5).to(5, -5).then(tail)
    return [a, b, c]


# ---------------------------------------------------------------- Modern
@design("suburbia", "Robots drive a full lap around the block, then race down the highway. A second road joins the highway.")
def _():
    tail = seq((4, 6), (11, 6, "fast"), (11, -3), E(-3))
    a = P(L(-4)).to(-3, -4).to(-3, 3).to(-10, 3).to(-10, -4).to(4, -4).then(tail)
    b = P(B(-1)).to(-1, 6).then(tail)
    return [a, b]


@design("airbase", "Robots taxi down the runway at full speed and cut through the hangar, where you can't hit them.")
def _():
    tail = seq((6, 4.5), (12, 4.5), E(4.5))
    a = P(L(-6.5)).fast(9, -6.5).to(9, -1.5).to(-8, -1.5).tunnel(-8, 2.5).to(-8, 4.5).then(tail)
    b = P(B(-12)).to(-12, 7.5).to(6, 7.5).then(tail)
    return [a, b]


@design("downtown", "Two highways cross downtown. Robots jam up in the traffic at the crossing, then take the subway.")
def _():
    tail = seq((9, 6), E(6))
    a = P(L(-2)).fast(-6, -2).to(2, -2).slow(6, -2).fast(9, -2).then(tail)
    b = P(T(4)).fast(4, -5).to(4, -4).slow(4, 0).to(4, 1.5).rift(-11, 6).fast(9, 6).to(E(6))
    return [a, b]


# ---------------------------------------------------------------- Digital
@design("neon_grid", "Data highways and three rifts. Robots blink across the grid; watch the arrows to see where they land.")
def _():
    a = P(L(-6)).fast(-6, -6).to(-6, 1).rift(6, -6.5).fast(6, 1).to(-2, 1).to(-2, 6).rift(10, 6.5)
    a.to(10, -2).to(E(-2))
    b = P(B(-10)).to(-10, 4).to(-2, 4).then(seq((-2, 6), (10, 6.5, "rift"), (10, -2), E(-2)))
    return [a, b]


@design("dish_array", "The road curls around the big dish and into its center, where the uplink beams robots to your gate.")
def _():
    a = P(L(0), 1.2).to(0.5 - 7.35, 0)
    a.arc(0.5, 0, 7.35, 180, 180 + 330, step=10)
    a.arc(0.5, 0, 4.2, 150, 150 + 300, step=12)       # inward: a second, tighter lap round the dish
    a.rift(11.5, -6.5).to(11.5, 6).to(E(6))
    return [a]


@design("cleanroom", "Airlocks hide the robots, decontamination slows them, and a rift skips the last corridor.")
def _():
    tail = seq((5, -2), (5, 5), (10, 5), (10, -4), E(-4))
    a = P(L(-6)).to(-10, -6).to(-10, -2).tunnel(-6, -2).slow(0, -2).then(tail)
    b = P(B(-6)).to(-6, 5).to(-1, 5).to(-1, 2).rift(5, -6.5).to(5, -2).then(tail[1:])
    c = P(T(7.3)).to(7.3, -5).slow(7.3, -2).to(5, -2).then(tail[1:])
    return [a, b, c]


# ---------------------------------------------------------------- Data Center
@design("server_hall", "Two data streams braid together, crossing four times. They race down data lanes and duck into cable ducts.")
def _():
    out = []
    for sign, lanes in ((-1, {"fast": (-4.5, 2.9), "tunnel": (3.6, 7.2)}), (1, {"fast": (2.9, 10.3), "tunnel": (-11.2, -7.8)})):
        p = P(L(-1 + sign * 4.5), 1.0)
        x = -15.6
        while x < 11.0:
            x = min(11.0, x + 0.45)
            y = -1 + sign * 4.5 * math.cos(math.pi * (x + 15.6) / 7.4)
            tag = None
            for k, (x0, x1) in lanes.items():
                if x0 < x <= x1:
                    tag = k
            p.to(x, y, tag, sharp=True)
        p.to(12.6, -1).to(E(-1))
        out.append(p)
    return out


@design("coolant_vaults", "Three portals in the vaults. Robots crawl through coolant pipes and slip on frozen floors.")
def _():
    tail = seq((3, 0), (3, 6), (11, 6), (11, -1), E(-1))
    a = P(L(-6)).to(-8, -6).tunnel(-8, -1).to(-8, 0).slow(3, 0).then(tail[1:])
    b = P(T(7)).to(7, -5).tunnel(2, -5).to(-3, -5).to(-3, 0).slow(3, 0).then(tail[1:])
    c = P(B(-12)).to(-12, 3.5).fast(-4, 3.5).to(-4, 0).slow(3, 0).then(tail[1:])
    return [a, b, c]


@design("the_core", "Three portals, chained rifts and data highways spiral into THE CORE. End it.")
def _():
    tail = seq((7, 4), (7, -4), (11.5, -4), (11.5, 6.5), E(6.5))
    a = P(L(-6.5)).fast(-1, -6.5).to(-1, -3).to(-11, -3).to(-11, 6.5).rift(3, -6.5).to(3, 4).then(tail)
    b = P(T(9)).fast(9, -6.5).to(5, -6.5)
    b.rift(-8, 0).to(-4, 0).to(-4, 4).fast(3, 4).then(tail)
    c = P(B(-6)).to(-6, 6.5).to(1, 6.5).to(1, 4).to(3, 4).then(tail)
    return [a, b, c]


# =====================================================================================================
# geometry checks, blocker placement, report
# =====================================================================================================
def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def legs(spec):
    pts = spec["pts"]
    rifts = set(spec.get("rift", []))
    out = [[pts[0]]]
    for i in range(1, len(pts)):
        if i in rifts:
            out.append([pts[i]])
        else:
            out[-1].append(pts[i])
    return out


def all_segs(specs):
    s = []
    for si, sp in enumerate(specs):
        for lg in legs(sp):
            for i in range(1, len(lg)):
                s.append((tuple(lg[i - 1]), tuple(lg[i])))
    return s


def dist_to_roads(p, segs):
    return min(seg_dist(p, a, b) for a, b in segs)


def path_stats(spec):
    pts = spec["pts"]
    rifts = set(spec.get("rift", []))
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + (0 if i in rifts else math.dist(pts[i - 1], pts[i])))
    length = cum[-1]
    t = 0.0
    hidden = 0.0
    for i in range(1, len(pts)):
        seg = cum[i] - cum[i - 1]
        m = 1.0
        for z in spec.get("zones", []):
            if z["a"] <= i - 1 and i <= z["b"]:
                if z["k"] == "tunnel":
                    hidden += seg
                else:
                    m *= z["m"]
        t += seg / m
    return length, t, hidden


def near_misses(specs):
    """Spots where two stretches of road run closer than ~a road width apart without crossing or merging
    (they would read as one blob of road). Samples every road at 0.25 and compares samples that are far apart
    along the road; spots near a real crossing or join point are ignored."""
    samples = []          # (path, s, x, y)
    for si, sp in enumerate(specs):
        pts = sp["pts"]
        rifts = set(sp.get("rift", []))
        s = 0.0
        for i in range(1, len(pts)):
            if i in rifts:
                continue
            a, b = pts[i - 1], pts[i]
            L_ = math.dist(a, b)
            n = max(1, int(L_ / 0.25))
            for k in range(n):
                u = k / n
                samples.append((si, s + L_ * u, a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
            s += L_
    touch = []
    close = []
    for i in range(len(samples)):
        si, s1, x1, y1 = samples[i]
        for j in range(i + 1, len(samples)):
            sj, s2, x2, y2 = samples[j]
            if si == sj and abs(s1 - s2) < 5.0:
                continue
            d = math.hypot(x1 - x2, y1 - y2)
            if d < 0.3:
                touch.append((x1, y1))
            elif d < 2.2:
                close.append((round(d, 2), (round(x1, 1), round(y1, 1))))
    out = []
    for d, p in close:
        if all(math.dist(p, t) > 2.6 for t in touch) and all(math.dist(p, q[1]) > 2.0 for q in out):
            out.append((d, p))
    return out


def _intersects(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


def river_dist(p, rivers):
    best = 1e9
    for rv in rivers:
        pts = rv["pts"]
        for i in range(1, len(pts)):
            best = min(best, seg_dist(p, pts[i - 1], pts[i]) - rv["width"] / 2)
    return best


def place_blockers(mid, old, segs, rivers, exit_y):
    rnd = random.Random(sum(ord(ch) for ch in mid) * 7 + 3)
    placed = []
    for bl in old:
        kind = bl[3]
        cands = []
        for r in (bl[2], round(bl[2] * 0.8, 2), round(bl[2] * 0.65, 2)):      # shrink it if the roads crowd it out
            y = BY0 + r + 0.4
            while y <= BY1 - r - 0.4:
                x = BX0 + r + 0.4
                while x <= BX1 - r - 0.4:
                    p = (x, y)
                    dr = dist_to_roads(p, segs)
                    ok = dr >= r + 1.25 and river_dist(p, rivers) >= r + 0.9
                    ok = ok and all(math.dist(p, (q[0], q[1])) >= r + q[2] + 1.6 for q in placed)
                    ok = ok and not (x > 12.0 and abs(y - exit_y) < 3.0)
                    if ok:
                        cands.append((p, dr))
                    x += 0.5
                y += 0.5
            if cands:
                break
        if not cands:
            print("  !! no room for blocker", kind, r)
            continue
        # prefer spots a little off the road (they read as scenery the road bends around)
        cands.sort(key=lambda c: abs(c[1] - (r + 2.2)) + rnd.random() * 2.5)
        p = cands[0][0]
        placed.append([round(p[0], 1), round(p[1], 1), r, kind])
    return placed


def free_space(segs, rivers, blockers):
    free = 0
    total = 0
    y = BY0 + 0.6
    while y < BY1 - 0.5:
        x = BX0 + 0.6
        while x < BX1 - 0.5:
            total += 1
            p = (x, y)
            if dist_to_roads(p, segs) >= HALF + 0.5 and river_dist(p, rivers) >= 0.5 and \
                    all(math.dist(p, (b[0], b[1])) >= b[2] + 0.65 for b in blockers):
                free += 1
            x += 0.5
        y += 0.5
    return free / total


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    plot = None
    if "--plot" in sys.argv:
        plot = sys.argv[sys.argv.index("--plot") + 1]
        args = [a for a in args if a != plot]
    dry = "--dry" in sys.argv
    order = [m["id"] for m in json.load(open(os.path.join(D, "maps.json")))["maps"]]
    ids = args or order
    index = json.load(open(os.path.join(D, "maps.json")))
    built = {}
    for mid in ids:
        fn, blurb = MAPS[mid]
        specs = [p.build() for p in fn()]
        path = os.path.join(D, "map_%s.json" % mid)
        m = json.load(open(path))
        ends = {tuple(s["pts"][-1]) for s in specs}
        segs = all_segs(specs)
        rivers = m.get("rivers", [])
        exit_y = specs[0]["pts"][-1][1]
        old_bl = m.get("blockers", [])
        if not old_bl:
            old_bl = [[0, 0, 1.3, "rocks"]] * 0
        blockers = place_blockers(mid, old_bl, segs, rivers, exit_y)
        stats = [path_stats(s) for s in specs]
        fs = free_space(segs, rivers, blockers)
        warns = near_misses(specs)
        print("%2d %-17s portals=%d len=%s time=%s hidden=%s free=%.0f%% %s%s" % (
            order.index(mid) + 1, mid, len(specs), [round(s[0]) for s in stats], [round(s[1]) for s in stats],
            [round(s[2]) for s in stats], fs * 100, "" if len(ends) == 1 else "!! EXITS DIFFER ",
            ("near-miss x%d %s" % (len(warns), warns[:2])) if warns else ""))
        for s in specs:
            p0 = s["pts"][0]
            if BX0 < p0[0] < BX1 and BY0 < p0[1] < BY1:
                print("  !! path starts inside the map", p0)
        built[mid] = (specs, blockers, blurb)
        if not dry:
            m.pop("path", None)
            m["paths"] = specs
            m["blockers"] = blockers
            m["layout"] = 2
            json.dump(m, open(path, "w"), indent=1)
            for e in index["maps"]:
                if e["id"] == mid:
                    e["blurb"] = blurb
    if not dry:
        json.dump(index, open(os.path.join(D, "maps.json"), "w"), indent=1)
    if plot:
        draw(built, order, plot)


def draw(built, order, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ids = [m for m in order if m in built]
    cols = 5 if len(ids) > 4 else len(ids)
    rows = (len(ids) + cols - 1) // cols
    fig, axs = plt.subplots(rows, cols, figsize=(5.4 * cols, 3.4 * rows), squeeze=False)
    zc = {"fast": "#ffcc00", "slow": "#7a4a1a", "tunnel": "#222222"}
    for ax in axs.flat:
        ax.axis("off")
    for ax, mid in zip(axs.flat, ids):
        specs, blockers, _b = built[mid]
        m = json.load(open(os.path.join(D, "map_%s.json" % mid)))
        ax.add_patch(plt.Rectangle((BX0, BY0), BX1 - BX0, BY1 - BY0, fc="#d8ecc8"))
        for rv in m.get("rivers", []):
            xs, ys = zip(*rv["pts"])
            ax.plot(xs, ys, color="#5aa0ff", lw=rv["width"] * 4.2, alpha=0.6, solid_capstyle="round")
        for b in blockers:
            ax.add_patch(plt.Circle((b[0], b[1]), b[2], fc="#9a9a9a"))
        pc = ["#c0504d", "#4f6fc0", "#3c9a50"]
        for si, s in enumerate(specs):
            for lg in legs(s):
                xs, ys = zip(*lg)
                ax.plot(xs, ys, lw=5.5, color=pc[si % 3], solid_capstyle="round", alpha=0.9)
            pts = s["pts"]
            for z in s.get("zones", []):
                xs, ys = zip(*pts[z["a"]:z["b"] + 1])
                ax.plot(xs, ys, lw=2.5, color=zc[z["k"]], ls="--" if z["k"] == "tunnel" else "-")
            for k in s.get("rift", []):
                a, b = pts[k - 1], pts[k]
                ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", color="#a020f0", lw=1.6, ls=":"))
                ax.plot(*a, "o", color="#a020f0", ms=9)
                ax.plot(*b, "o", color="#a020f0", ms=9, mfc="white")
            ax.plot(*pts[0], "s", color="purple", ms=11)
            # direction arrows
            for k in range(3, len(pts) - 1, 9):
                if k in s.get("rift", []) or (k + 1) in s.get("rift", []):
                    continue
                a, b = pts[k], pts[k + 1]
                ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-|>", color="white", lw=1.2))
        ax.plot(RX, specs[0]["pts"][-1][1], "D", color="black", ms=10)
        ax.set_xlim(-16.5, 16.5)
        ax.set_ylim(9.7, -9.7)
        ax.set_aspect("equal")
        ax.set_title("%d. %s" % (order.index(mid) + 1, mid), fontsize=13)
    plt.tight_layout()
    plt.savefig(out, dpi=60)


if __name__ == "__main__":
    main()
