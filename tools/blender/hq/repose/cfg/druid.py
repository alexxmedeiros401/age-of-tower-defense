# Druid: the staff was held up in front of the beard with its gem beside the nose in every clip, and in Idle
# (~f74-92) the left hand went up into the beard. Re-authored: the staff stands out at the right side (gem beside and
# above the head, outside the hair), lifts a little and leans toward the target as the left hand casts (the cast keeps
# its shipped timing: out at the side, rising to head height); Idle keeps the left hand at the belt.
import math
from mathutils import Vector as V
AXIS = {'R': V((-0.046, -0.988, 0.15))}           # staff: grip -> gem
GD = V((-0.18, -0.05, 0.98))
READY_R = V((-0.52, -0.16, 1.10))
ATK_R = [
    (0,  READY_R,                  {'dir': GD}),
    (6,  V((-0.54, -0.10, 1.22)),  {'dir': V((-0.20, 0.05, 0.98))}),   # lift
    (12, V((-0.50, -0.26, 1.18)),  {'dir': V((-0.12, -0.30, 0.95))}),  # lean the gem toward the target
    (30, V((-0.50, -0.25, 1.16)),  {'dir': V((-0.13, -0.28, 0.95))}),
    (42, READY_R,                  {'dir': GD}),
]
ATK_L = [
    (0,  V((0.45, -0.28, 1.08)), {}),
    (6,  V((0.42, -0.24, 1.00)), {}),
    (12, V((0.42, -0.24, 1.24)), {}),
    (18, V((0.47, -0.26, 1.52)), {}),     # cast: hand up out at the side
    (24, V((0.48, -0.27, 1.49)), {}),
    (30, V((0.47, -0.28, 1.33)), {}),
    (42, V((0.45, -0.28, 1.08)), {}),
]
def loop(base, amp, n, o, ph=0.0):
    def k(f):
        a = 2 * math.pi * f / n + ph
        return base + V((0, amp[0] * math.sin(a), amp[1] * math.sin(a))), o
    return k
IDLE_L = [(66, V((0.33, -0.04, 0.92)), {}), (76, V((0.34, -0.10, 0.96)), {}), (86, V((0.34, -0.10, 0.97)), {}), (96, V((0.33, -0.04, 0.92)), {})]
CLIPS = {
    'Attack': {'R': ATK_R, 'L': ATK_L},
    'Combat': {'R': loop(READY_R, (0.01, 0.02), 40, {'dir': GD})},
    'Idle':   {'R': loop(V((-0.52, -0.06, 1.06)), (0.01, 0.015), 120, {'dir': V((-0.16, 0.02, 0.99))}), 'L': IDLE_L},
}
WINDOW = {'Idle': {'L': (70, 92, 6)}}
