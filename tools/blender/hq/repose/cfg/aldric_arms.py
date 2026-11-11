# Sir Aldric (Medieval hero): the longsword guard held the fist at his right cheek (Combat), the cut came down across
# his face (Attack 3-9), and the raised sword (Ability's lance, Cheer) went up from a fist over his brow. The fist now
# guards out beside his head, the cut starts there and comes down across his chest in front of him, and the raises go
# up out at his right; the sword keeps its shipped orientation per frame. Shield arm and Idle: clean, kept.
import math
from mathutils import Vector as V
HERO = 'aldric'
WR = -25.0     # the guard's blade tilted out about the forward axis: its upper half off his head from behind too

def ramp(f, pts):
    for (a, wa), (b, wb) in zip(pts, pts[1:]):
        if a <= f <= b:
            t = (f - a) / float(b - a); t = t * t * (3 - 2 * t); return wa + (wb - wa) * t
    return pts[-1][1] if f > pts[-1][0] else pts[0][1]
GUARD = V((-0.58, 0.02, 1.58)); GUARD_POLE = V((-1.00, 0.10, 1.35))
HIGH = V((-0.58, 0.00, 1.98)); HIGH_POLE = V((-1.00, 0.15, 1.70))
POINT = V((-0.34, -0.50, 1.55)); POINT_POLE = V((-0.95, -0.15, 1.40))

def guard(f, n=40):
    return GUARD + V((0, 0, 0.012 * math.sin(2 * math.pi * f / n))), GUARD_POLE

CLIPS = {
    'Combat': {'R': guard, 'hand_R': 'world', 'loop': True, 'world_rot': ((0, 1, 0), WR)},
    'Attack': {   # CUT at frame 7
        'R': [(0, GUARD, GUARD_POLE), (3, V((-0.60, 0.05, 1.66)), GUARD_POLE), (6, V((-0.42, -0.40, 1.42)), POINT_POLE),
              (9, V((-0.12, -0.47, 1.16)), V((-0.80, -0.20, 1.20))), (12, V((-0.04, -0.42, 1.12)), V((-0.80, -0.20, 1.15))),
              (15, V((-0.52, -0.28, 1.32)), V((-0.90, -0.10, 1.25))), (18, V((-0.50, -0.06, 1.50)), GUARD_POLE), (21, GUARD, GUARD_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.0, 'world_rot': lambda f: ((0, 1, 0), WR * ramp(f, [(0, 1), (4, 1), (6, 0), (11, 0), (15, 3.6), (21, 1)])),
    },
    'Ability': {   # GATHER 16, STRIKE 30
        'R': [(0, GUARD, GUARD_POLE), (3, V((-0.58, -0.01, 1.66)), GUARD_POLE), (6, V((-0.58, -0.01, 1.82)), HIGH_POLE), (10, HIGH, HIGH_POLE),
              (24, HIGH, HIGH_POLE), (27, V((-0.52, -0.12, 1.90)), HIGH_POLE), (30, POINT, POINT_POLE), (39, POINT, POINT_POLE),
              (42, V((-0.40, -0.36, 1.58)), POINT_POLE), (45, V((-0.50, -0.16, 1.58)), GUARD_POLE), (50, GUARD, GUARD_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.0, 'world_rot': lambda f: ((0, 1, 0), WR * ramp(f, [(0, 1), (6, 0), (42, 0), (50, 1)])),
    },
    'Cheer': {
        'R': [(0, GUARD, GUARD_POLE), (3, V((-0.58, -0.01, 1.80)), HIGH_POLE), (6, HIGH, HIGH_POLE), (12, HIGH + V((0, 0, -0.02)), HIGH_POLE),
              (24, HIGH, HIGH_POLE), (33, HIGH + V((0, 0, -0.02)), HIGH_POLE), (36, V((-0.58, -0.01, 1.82)), HIGH_POLE), (40, GUARD, GUARD_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.0, 'world_rot': lambda f: ((0, 1, 0), WR * ramp(f, [(0, 1), (6, 0), (34, 0), (40, 1)])),
    },
}
