# Trebuchet crewman: the right hand was held behind the head (Combat, Attack start/end) and the mallet lay across
# the chest and beard while waiting (Attack ~f6-18, ~f46-66, the whole Idle). Re-authored the right arm: the mallet
# is carried at the right side with a straight wrist (it sits across the fist) and only comes forward to work the
# release lever (Attack ~f24-40, the shipped hand place on the lever). Left arm: shipped (machine contacts).
import math
from mathutils import Vector as V
AXIS = {'R': V((-0.581, -0.24, -0.778))}          # mallet: grip -> head
SIDE = V((-0.48, -0.18, 1.05))
LEVER = V((-0.16, -0.31, 0.97))
ATK_R = [
    (0,  SIDE,                      {}),
    (16, SIDE + V((0.0, -0.02, 0.0)), {}),
    (22, V((-0.26, -0.30, 1.00)),   {}),
    (24, LEVER,                     {}),     # on the release lever (shipped hand place)
    (40, V((-0.15, -0.30, 0.95)),   {}),
    (46, SIDE + V((0.0, -0.02, 0.0)), {}),
    (68, SIDE,                      {}),
]
def loop(base, amp, n):
    def k(f):
        a = 2 * math.pi * f / n
        return base + V((0, amp[0] * math.sin(a), amp[1] * math.sin(a))), {}
    return k
CLIPS = {'Attack': {'R': ATK_R}, 'Combat': {'R': loop(SIDE, (0.01, 0.012), 40)}, 'Idle': {'R': loop(SIDE + V((0.02, 0.03, -0.02)), (0.008, 0.01), 120)}}
