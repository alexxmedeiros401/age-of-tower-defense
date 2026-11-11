# Axe Warrior: both hands sat inside the huge beard in every clip (Combat/Attack ready at the chin, Idle on the
# planted haft under the chin), the haft crossed the face, and the two-handed swing pulled the left forearm through
# the beard. With this beard (down to the belt, out to the shoulders) a two-handed grip on the right side can only
# be reached across it, so the swing is re-authored one-handed: the axe is held up at the right side, wound up
# beside/behind the head out at the side and chopped forward-down; the left hand braces out in front at the left.
# Idle: the axe is held up at the right side (head up, beside the shoulder), the left hand rests at the belt.
import math
from mathutils import Vector as V
AXIS = {'R': V((0.0, -0.984, 0.176))}             # axe: grip -> head
READY_R = V((-0.50, -0.20, 1.12)); RD = V((-0.28, 0.15, 0.95))
READY_L = V((0.45, -0.28, 1.12))
# The axe sits across the fist (perpendicular to the forearm, pointing where the palm faces): it stands up when the
# forearm is level, points back when the forearm is upright and forward when the arm hangs. The chop is driven by
# the arm with a near-straight wrist (aim 0.2): the axe goes back over the shoulder at the wind-up and comes over
# the top to forward at the impact.
ATK_R = [
    (0,  READY_R,                 {'dir': RD, 'aim': 0.3}),
    (6,  V((-0.54, 0.02, 1.48)),  {'dir': V((-0.20, 0.50, 0.84)), 'aim': 0.4}),   # wind-up: forearm upright beside the head
    (10, V((-0.46, -0.36, 1.34)), {'dir': V((0.10, -0.30, 0.95)), 'aim': 0.2}),   # over the top
    (13, V((-0.40, -0.32, 0.90)), {'dir': V((0.15, -0.95, -0.25)), 'aim': 0.2}),  # impact: arm reaching down-forward
    (18, V((-0.41, -0.30, 0.92)), {'dir': V((0.15, -0.95, -0.20)), 'aim': 0.2}),
    (26, READY_R,                 {'dir': RD, 'aim': 0.3}),
]
ATK_L = [
    (0,  READY_L, {}),
    (10, V((0.48, -0.36, 1.20)), {}),
    (18, V((0.47, -0.34, 1.16)), {}),
    (26, READY_L, {}),
]
def loop(base, amp, n, o, ph=0.0):
    def k(f):
        a = 2 * math.pi * f / n + ph
        return base + V((0, amp[0] * math.sin(a), amp[1] * math.sin(a))), o
    return k
IDLE_R = V((-0.52, -0.04, 1.02)); ID = V((-0.32, 0.18, 0.93))
CLIPS = {
    'Attack': {'R': ATK_R, 'L': ATK_L},
    'Combat': {'R': loop(READY_R, (0.01, 0.02), 40, {'dir': RD, 'aim': 0.3}), 'L': loop(READY_L, (0.0, 0.015), 40, {}, 0.7)},
    'Idle':   {'R': loop(IDLE_R, (0.005, 0.01), 120, {'dir': ID}), 'L': loop(V((0.36, -0.20, 0.98)), (0.0, 0.01), 120, {}, 1.0)},
}
