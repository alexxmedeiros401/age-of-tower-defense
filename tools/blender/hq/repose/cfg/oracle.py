# Oracle: the laurel sprig (right hand) was swept up behind the head with the elbow folded flat (Attack ~f6-9,
# the forearm skin collapsed), passed through the veil beside the face (Attack ~f12), and in Idle it was held upright
# in front of the face (its tip in the veil, ~f80-90). Re-authored the right arm: the sprig is held forward-out at
# chest height, raised out at the side above the shoulder (not behind the head), swept forward over the bowl and
# held toward the target; Idle holds it lower and leaning out. The sprig is small, so its direction is only a hint
# (aim 0.3): the wrist stays near straight. The left (bowl) arm keeps its shipped motion.
import math
from mathutils import Vector as V
AXIS = {'R': V((-0.141, -0.968, 0.209))}          # sprig: grip -> tip
READY = V((-0.30, -0.28, 1.36)); SD = V((-0.25, -0.70, 0.67))
ATK_R = [
    (0,  READY,                    {'dir': SD, 'aim': 0.3}),
    (6,  V((-0.52, -0.06, 1.58)),  {'dir': V((-0.25, -0.05, 0.97)), 'aim': 0.3}),   # raise out at the side
    (9,  V((-0.53, -0.04, 1.62)),  {'dir': V((-0.20, 0.05, 0.98)), 'aim': 0.3}),
    (13, V((-0.30, -0.40, 1.50)),  {'dir': V((0.25, -0.85, -0.10)), 'aim': 0.3}),   # sweep forward over the bowl
    (16, V((-0.27, -0.38, 1.50)),  {'dir': V((-0.10, -0.90, 0.40)), 'aim': 0.3}),   # hold toward the target
    (27, V((-0.27, -0.36, 1.48)),  {'dir': V((-0.14, -0.88, 0.45)), 'aim': 0.3}),
    (42, READY,                    {'dir': SD, 'aim': 0.3}),
]
def loop(base, amp, n, o):
    def k(f):
        a = 2 * math.pi * f / n
        return base + V((0, amp[0] * math.sin(a), amp[1] * math.sin(a))), o
    return k
CLIPS = {
    'Attack': {'R': ATK_R},
    'Combat': {'R': loop(READY, (0.01, 0.015), 40, {'dir': SD, 'aim': 0.3})},
    'Idle':   {'R': loop(V((-0.32, -0.22, 1.15)), (0.01, 0.02), 120, {'dir': V((-0.35, -0.45, 0.82)), 'aim': 0.3})},
}
