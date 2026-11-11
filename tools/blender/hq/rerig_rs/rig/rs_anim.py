"""Rock Slinger re-rig: clip authoring (numpy). Keyed controls with cubic interpolation, the sling's rope, and the bake
to per-frame bone deltas.

A clip is a set of tracks (frame -> value) for the solver's controls; in-betweens are cubic (Catmull-Rom style tangents on
uneven key spacing), so hands and hips travel on arcs. The sling is a chain of nodes hanging from the fist: while the
stone is in the pouch the pouch is driven round a circle (taut cords), and once the stone is gone the empty sling is
simulated (gravity, drag, kept out of the body), then gathered back for the reload.
"""
import numpy as np
import rs_core, rs_skel
from rs_core import J, ypr, unit

FPS = 24.0


class Track:
    """Keys {frame: value}; cubic through them. period: the clip's length when the motion loops."""

    def __init__(self, keys, period=None, mode='cubic', flat=()):
        ks = sorted(keys.items())
        self.t = np.array([k for k, _ in ks], float)
        self.v = np.array([np.atleast_1d(np.asarray(v, float)) for _, v in ks])
        self.period = period; self.mode = mode
        self.flat = set(flat)
        n = len(self.t)
        if period is not None and n > 1:
            # wrap: the keys of the cycle before and after, so the tangents (and the curve) are periodic
            assert self.t[0] >= 0 and self.t[-1] <= period
            if abs(self.t[-1] - period) < 1e-9 and abs(self.t[0]) < 1e-9:
                self.t = self.t[:-1]; self.v = self.v[:-1]
            self.t = np.concatenate([self.t - period, self.t, self.t + period])
            self.v = np.concatenate([self.v, self.v, self.v])
        elif period is not None:
            self.period = None
        self.m = self._tangents()

    def _tangents(self):
        t, v = self.t, self.v
        n = len(t); m = np.zeros_like(v)
        for i in range(n):
            if n == 1: break
            if i == 0: m[i] = (v[1] - v[0]) / (t[1] - t[0])
            elif i == n - 1: m[i] = (v[-1] - v[-2]) / (t[-1] - t[-2])
            else:
                h0 = t[i] - t[i - 1]; h1 = t[i + 1] - t[i]
                d0 = (v[i] - v[i - 1]) / h0; d1 = (v[i + 1] - v[i]) / h1
                m[i] = (d0 * h1 + d1 * h0) / (h0 + h1)
        for i in range(n):
            tt = self.t[i] % self.period if self.period else self.t[i]
            if any(abs(tt - f) < 1e-9 for f in self.flat): m[i] = 0.0
        return m

    def __call__(self, f):
        t, v, m = self.t, self.v, self.m
        if self.period is not None:
            f = f % self.period
        if len(t) == 1: return v[0].copy() if v.shape[1] > 1 else float(v[0, 0])
        f = float(np.clip(f, t[0], t[-1]))
        i = int(np.clip(np.searchsorted(t, f, side='right') - 1, 0, len(t) - 2))
        h = t[i + 1] - t[i]; s = (f - t[i]) / h
        if self.mode == 'step':
            out = v[i]
        elif self.mode == 'lin':
            out = v[i] * (1 - s) + v[i + 1] * s
        else:
            s2, s3 = s * s, s * s * s
            out = (2 * s3 - 3 * s2 + 1) * v[i] + (s3 - 2 * s2 + s) * h * m[i] + (-2 * s3 + 3 * s2) * v[i + 1] + (s3 - s2) * h * m[i + 1]
        return out.copy() if v.shape[1] > 1 else float(out[0])


class Clip:
    def __init__(self, name, frames, loop):
        self.name = name; self.frames = frames; self.loop = loop
        self.tr = {}
        self.extra = []          # functions (f, controls) -> None, applied after the tracks
        self.sling = None        # dict: see bake()

    def key(self, name, keys, mode='cubic', flat=(), periodic=None):
        per = self.frames if (self.loop if periodic is None else periodic) else None
        self.tr[name] = Track(keys, per, mode, flat)

    def controls(self, f):
        c = rs_core.default_controls()
        g = lambda nme, dflt: self.tr[nme](f) if nme in self.tr else dflt
        c['pelvis'] = J['pelvis'] + g('pelvis', np.zeros(3))
        c['pelvis_rot'] = ypr(*g('pelvis_ypr', np.zeros(3)))
        c['chest_rot'] = ypr(*g('chest_ypr', np.zeros(3)))
        c['head_rot'] = ypr(*g('head_ypr', np.zeros(3)))
        for s in 'LR':
            a = c['arm.' + s]
            a['clav_auto'] = 1.0
            if 'wrist.' + s in self.tr: a['wrist'] = self.tr['wrist.' + s](f)
            if 'cwrist.' + s in self.tr: a['wrist'] = self.tr['cwrist.' + s](f); a['space'] = 'chest'
            if 'pole.' + s in self.tr: a['pole'] = self.tr['pole.' + s](f)
            if 'aim.' + s in self.tr: a['aim'] = self.tr['aim.' + s](f)
            a['roll'] = g('roll.' + s, 0.0)
            if 'shrug.' + s in self.tr: a['shrug'] = self.tr['shrug.' + s](f)
            if 'protract.' + s in self.tr: a['protract'] = self.tr['protract.' + s](f)
            l = c['leg.' + s]
            l['ball'] = J['ball.' + s] + g('ball.' + s, np.zeros(3))
            l['yaw'] = g('foot_yaw.' + s, 0.0); l['lift'] = g('foot_lift.' + s, 0.0); l['roll'] = g('foot_roll.' + s, 0.0)
            if 'knee.' + s in self.tr: l['pole'] = self.tr['knee.' + s](f)
            if 'toe.' + s in self.tr: l['toe'] = self.tr['toe.' + s](f)
        c['stone'] = g('stone', 1.0)
        for fn in self.extra: fn(f, c)
        return c


# ------------------------------------------------------------------------------------------------ the sling
SLING_L = float(np.linalg.norm(rs_skel.sling_nodes()[-1] - rs_skel.sling_nodes()[0]))
SEG = SLING_L / rs_skel.SLING_SEGS
GRAV = np.array([0.0, 0.0, -14.0])

# the body as capsules the empty sling must stay out of (a, b, radius), in the pose's frame of the named bone
BODY_CAPS = [('root', (0.0, 0.03, 0.55), (0.0, 0.05, 0.95), 0.40), ('chest', (0.0, 0.04, 1.0), (0.0, 0.05, 1.35), 0.42),
             ('head', (0.0, 0.0, 1.6), (0.0, 0.03, 1.85), 0.37), ('head', (0.0, -0.20, 1.45), (0.0, -0.25, 1.24), 0.17),      # (and his beard)
             ('shin.L', J['knee.L'], J['ankle.L'], 0.17), ('shin.R', J['knee.R'], J['ankle.R'], 0.17),
             ('thigh.L', J['hip.L'], J['knee.L'], 0.19), ('thigh.R', J['hip.R'], J['knee.R'], 0.19)]


def _collide(p, caps, floor=0.02, pad=0.0):
    for a, b, r in caps:
        ab = b - a
        t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        c = a + t * ab; d = p - c; n = np.linalg.norm(d)
        if n < r + pad:
            p = c + d / max(n, 1e-9) * (r + pad)
    if p[2] < floor: p = np.array([p[0], p[1], floor])
    return p


# the base does not turn with him: its tusks, torch and basket stand in a ring round the yaw axis. Least radius by height
# (armature space, measured on the shipped base; nothing stands above 2.0), less the pouch's own size.
RING_Z = np.array([1.00, 1.50, 1.75, 2.00, 2.12])
RING_R = np.array([1.10, 1.04, 0.98, 0.95, 1.60]) - 0.11


def _ring(p):
    """Keep a sling node inside the base's ring."""
    rmax = float(np.interp(p[2], RING_Z, RING_R))
    r = float(np.hypot(p[0], p[1]))
    if r > rmax: p = np.array([p[0] * rmax / r, p[1] * rmax / r, p[2]])
    return p


def _cr(P, f, loop):
    """Catmull-Rom through per-frame samples P[0..n] (P[n] == P[0] when looping) at fractional frame f."""
    n = len(P) - 1
    i = int(np.floor(f)); s = f - i
    def at(k):
        if loop: return P[k % n]
        return P[int(np.clip(k, 0, n))]
    p0, p1, p2, p3 = at(i - 1), at(i), at(i + 1), at(i + 2)
    return 0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3)


def sim_sling(grips, caps_per_frame, drive, loop, substeps=10, loops=3, drag=3.5, stiff_iters=12, start=None):
    """grips: (n+1, 3) grip positions per frame; drive(f) -> (w, dir): how firmly (0..1) the pouch is held on the unit
    direction dir from the grip. Returns (n+1, S+1, 3) node positions per frame."""
    n = len(grips) - 1; S = rs_skel.SLING_SEGS
    dt = 1.0 / FPS / substeps
    g0 = grips[0]
    w0, d0 = drive(0.0)
    d0 = unit(d0) if d0 is not None else np.array([0, 0, -1.0])
    X = np.array([g0 + d0 * SEG * k for k in range(S + 1)]) if start is None else start.copy()
    Xp = X.copy()
    out = np.zeros((n + 1, S + 1, 3))
    total = loops if loop else 1
    for lp in range(total):
        for fi in range(n + (0 if loop else 1)):
            for ss in range(substeps):
                f = fi + ss / substeps
                if not loop and fi == n and ss > 0: break
                if ss == 0 and lp == total - 1:
                    out[fi] = X
                G = _cr(grips, f + 1.0 / substeps, loop)
                w, d = drive(f + 1.0 / substeps)
                caps = caps_per_frame[min(int(round(f)), n) % (n if loop else n + 1)] if caps_per_frame is not None else []
                # verlet
                V = (X - Xp) * (1.0 - drag * dt)
                Xp = X.copy()
                X = X + V + GRAV * dt * dt
                X[0] = G
                if w > 0 and d is not None:
                    tgt = np.array([G + unit(d) * SEG * k for k in range(S + 1)])
                    X = X * (1 - w) + tgt * w
                for it in range(stiff_iters):
                    X[0] = G
                    for k in range(S):
                        dv = X[k + 1] - X[k]; L = np.linalg.norm(dv)
                        corr = dv * (1 - SEG / max(L, 1e-9))
                        if k == 0: X[k + 1] -= corr
                        else: X[k] += corr * 0.5; X[k + 1] -= corr * 0.5
                    if w < 0.999 and caps:
                        for k in range(1, S + 1):
                            X[k] = _ring(_collide(X[k], caps, pad=0.03 if k == S else 0.0))
        if loop and lp == total - 1:
            out[n] = out[0]
    if not loop:
        pass
    return out


def bake(clip, weights=None):
    """-> list of (P, info) for frames 0..clip.frames, with the sling solved."""
    n = clip.frames
    poses = []
    for f in range(n + 1):
        c = clip.controls(float(f))
        P, info = rs_core.solve(c)
        poses.append((c, P, info))
    sp = clip.sling
    if sp is not None:
        grips = np.array([p[2]['grip'] for p in poses])
        caps = []
        for c, P, info in poses:
            cc = []
            for bone, a, b, r in BODY_CAPS:
                cc.append((P[bone](np.asarray(a, float)), P[bone](np.asarray(b, float)), r))
            caps.append(cc)
        nodes = sim_sling(grips, caps, sp['drive'], clip.loop, loops=sp.get('loops', 3), drag=sp.get('drag', 3.5), substeps=sp.get('substeps', 10))
        out = []
        for f, (c, P, info) in enumerate(poses):
            c['sling'] = [nodes[f][k] for k in range(nodes.shape[1])]
            P, info = rs_core.solve(c)
            info['nodes'] = nodes[f]
            out.append((c, P, info))
        poses = out
    return poses
