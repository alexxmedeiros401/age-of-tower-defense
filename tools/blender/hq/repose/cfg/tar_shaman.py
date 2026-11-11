# Tar Shaman: the staff (right hand) stood in front of the face and its orb in the skull; the left hand sat in the
# beard (Idle) and swept through it (Attack). Re-authored: staff held out at the side (orb beside the head, not in
# front of it), raised beside the head and thrust forward; the left hand casts out at the side.
import math
from mathutils import Vector as V
AXIS = {'R': V((0.032, -0.985, 0.171)).normalized()}      # staff, wrist -> orb
RD = V((-0.15, -0.05, 0.99))
READY_R = V((-0.52, -0.16, 1.12)); READY_L = V((0.38, -0.46, 1.12))
ATK_R = [
    (0,  READY_R,                {'dir': RD}),
    (6,  V((-0.56, -0.02, 1.32)), {'dir': V((-0.15, 0.25, 0.96))}),   # raise beside the head
    (9,  V((-0.46, -0.50, 1.24)), {'dir': V((-0.05, -0.72, 0.69))}),  # thrust: the orb pitched forward at the enemy
    (15, V((-0.46, -0.48, 1.23)), {'dir': V((-0.05, -0.70, 0.71))}),
    (21, V((-0.49, -0.38, 1.20)), {'dir': V((-0.08, -0.50, 0.86))}),
    (27, V((-0.51, -0.22, 1.16)), {'dir': V((-0.13, -0.15, 0.98))}),
    (32, READY_R,                {'dir': RD}),
]
ATK_L = [
    (0,  READY_L, {}),
    (5,  V((0.42, -0.44, 1.22)), {}),
    (9,  V((0.50, -0.44, 1.46)), {}),     # cast: claw up and out at the side
    (18, V((0.50, -0.45, 1.44)), {}),
    (25, V((0.44, -0.48, 1.26)), {}),
    (32, READY_L, {}),
]
def loop(base, amp, n, ph=0.0, d=None):
    def k(f):
        a = 2 * math.pi * f / n + ph
        o = {'dir': d} if d is not None else {}
        return base + V((amp[0] * math.sin(a), amp[1] * math.sin(a), amp[2] * math.sin(a))), o
    return k
def idle_l(f):
    # slow conjuring gesture: lift and turn the hand out, back down (frames 30-80)
    t = min(max((f - 30) / 50.0, 0.0), 1.0); s = math.sin(math.pi * t)
    return READY_L + V((0.04 * s, 0.02 * s, 0.12 * s)) + V((0, 0, 0.01 * math.sin(2 * math.pi * f / 120))), {}
CLIPS = {
    'Attack': {'R': ATK_R, 'L': ATK_L},
    'Combat': {'R': loop(READY_R, (0.0, 0.01, 0.025), 40, 0.0, RD), 'L': loop(READY_L, (0.01, 0.0, 0.02), 40, 1.0)},
    'Idle':   {'R': loop(READY_R + V((0, 0.02, -0.03)), (0.0, 0.015, 0.02), 120, 0.0, RD), 'L': idle_l},
}
