import math
from mathutils import Vector as V
ATTACK, LOOP = 'Attack', 'Combat'
SLING = False
CLUB_AXIS = V((0.05, -0.968, 0.248)).normalized()
READY_R = V((-0.86, -0.14, 1.08)); POLE_R = V((-1.15, 0.35, 1.15))
ATK_R = [
    (0,  READY_R,                     POLE_R),
    (5,  V((-0.98, 0.00, 1.42)),      V((-1.25, 0.30, 1.20))),   # lift out to the side
    (9,  V((-0.88, 0.22, 1.86)),      V((-1.25, 0.25, 1.45))),   # top of the wind-up, beside and behind the head
    (12, V((-0.78, -0.52, 1.30)),     V((-1.25, 0.05, 1.45))),   # smash
    (15, V((-0.74, -0.58, 1.10)),     V((-1.20, 0.05, 1.25))),   # impact
    (19, V((-0.86, -0.34, 1.04)),     V((-1.20, 0.25, 1.15))),
    (24, READY_R,                     POLE_R),
]
READY_L = V((0.92, -0.04, 0.95)); POLE_L = V((1.20, 0.35, 1.15))
ATK_L = [
    (0,  READY_L,                     POLE_L),
    (6,  V((0.84, -0.26, 1.18)),      V((1.20, 0.10, 1.25))),    # brace forward
    (15, V((0.86, -0.30, 1.12)),      V((1.20, 0.10, 1.20))),
    (24, READY_L,                     POLE_L),
]
def loop_r(f, n=32):
    a = 2 * math.pi * f / n
    return READY_R + V((0, 0.02 * math.sin(a), 0.03 * math.sin(a))), POLE_R
def loop_l(f, n=32):
    return READY_L + V((0, 0, 0.015 * math.sin(2 * math.pi * f / n))), POLE_L
CLUB_KEYS = [  # frame, club direction (chest frame)
    (0,  V((-0.22, 0.10, 0.97))),
    (5,  V((-0.25, 0.25, 0.93))),
    (9,  V((-0.10, 0.80, 0.60))),
    (12, V((-0.05, -0.75, 0.20))),
    (15, V((-0.02, -0.62, -0.78))),
    (19, V((-0.10, -0.90, 0.10))),
    (24, V((-0.22, 0.10, 0.97))),
]
def _slerp(a, b, t):
    a = a.normalized(); b = b.normalized()
    q = a.rotation_difference(b)
    import mathutils
    return (mathutils.Quaternion().slerp(q, t) @ a).normalized()
def club_dir(clip, f):
    if clip == LOOP:
        a = 2 * math.pi * f / 32
        return (CLUB_KEYS[0][1] + V((0, 0.05 * math.sin(a), 0))).normalized()
    ks = CLUB_KEYS
    for i in range(len(ks) - 1):
        if ks[i][0] <= f <= ks[i + 1][0]:
            t = (f - ks[i][0]) / (ks[i + 1][0] - ks[i][0])
            t = t * t * (3 - 2 * t)
            # wind-up to smash: go over the top (through straight up)
            if ks[i][0] == 9:
                up = V((-0.08, 0.0, 1.0))
                return _slerp(ks[i][1], up, t * 2) if t < 0.5 else _slerp(up, ks[i + 1][1], t * 2 - 1)
            return _slerp(ks[i][1], ks[i + 1][1], t)
    return ks[-1][1]
