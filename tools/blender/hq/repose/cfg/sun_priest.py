# Sun Priest: the sun staff was held in front of the face (the disc beside the nose, the shaft tilted into the head),
# raised straight up through the headdress (Attack ~f3-9), the Idle staff leaned into the head, and the left hand
# swept into the chest at the wind-up. Re-authored: the staff stands out at the right side (the disc beside and
# above the head), rises out at the side and tilts back, then presents the sun forward; the left hand stays open in
# front at the side.
import math
from mathutils import Vector as V
AXIS = {'R': V((-0.017, -0.989, 0.146))}          # staff, hand -> sun
SD = V((-0.20, -0.05, 0.98))
READY_R = V((-0.55, -0.14, 1.16)); READY_L = V((0.38, -0.32, 1.36))
ATK_R = [
    (0,  READY_R,                  {'dir': SD}),
    (6,  V((-0.54, -0.06, 1.40)),  {'dir': V((-0.15, 0.12, 0.98))}),   # raise out at the side, tilt back
    (12, V((-0.52, -0.36, 1.46)),  {'dir': V((-0.14, -0.30, 0.94))}),  # present the sun forward
    (21, V((-0.52, -0.35, 1.45)),  {'dir': V((-0.14, -0.29, 0.95))}),
    (33, V((-0.54, -0.22, 1.28)),  {'dir': V((-0.17, -0.18, 0.97))}),
    (42, READY_R,                  {'dir': SD}),
]
ATK_L = [
    (0,  READY_L, {}),
    (6,  V((0.42, -0.36, 1.26)), {}),
    (12, V((0.38, -0.40, 1.42)), {}),
    (21, V((0.38, -0.39, 1.42)), {}),
    (42, READY_L, {}),
]
def loop(base, amp, n, o, ph=0.0):
    def k(f):
        a = 2 * math.pi * f / n + ph
        return base + V((0, amp[0] * math.sin(a), amp[1] * math.sin(a))), o
    return k
IDLE_R = V((-0.55, -0.06, 1.06)); ID = V((-0.18, -0.02, 0.98))
CLIPS = {
    'Attack': {'R': ATK_R, 'L': ATK_L},
    'Combat': {'R': loop(READY_R, (0.01, 0.02), 40, {'dir': SD})},
    'Idle':   {'R': loop(IDLE_R, (0.01, 0.015), 120, {'dir': ID})},
}
