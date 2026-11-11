# Ballista crewman: the right hand held the trigger mallet up against the helmet/cheek (Combat), struck the trigger
# from in front of the face (Attack ~f2-8) and then held the mallet across the chest and beard for the rest of the
# reload (Attack ~f8-60) and the whole Idle. Re-authored the right arm: the mallet is carried at the right side with
# a straight wrist (it sits across the fist), raised out at the side, struck forward-down in front of the right
# shoulder, and carried at the side again while the left arm works the winch (left arm: shipped).
import math
from mathutils import Vector as V
AXIS = {'R': V((0.111, 0.98, 0.168))}             # mallet: grip -> head
SIDE = V((-0.50, -0.18, 1.05))
ATK_R = [
    (0,  SIDE,                      {}),
    (3,  V((-0.58, -0.14, 1.22)),   {}),     # raise out at the side
    (6,  V((-0.40, -0.42, 1.18)),   {}),     # strike forward-down, in front of the right shoulder
    (10, V((-0.46, -0.24, 1.12)),   {}),
    (14, SIDE,                      {}),
    (60, SIDE + V((0.0, -0.02, 0.01)), {}),
    (66, SIDE,                      {}),
]
def loop(base, amp, n):
    def k(f):
        a = 2 * math.pi * f / n
        return base + V((0, amp[0] * math.sin(a), amp[1] * math.sin(a))), {}
    return k
CLIPS = {'Attack': {'R': ATK_R}, 'Combat': {'R': loop(SIDE, (0.01, 0.012), 40)}, 'Idle': {'R': loop(SIDE + V((0.02, 0.03, -0.02)), (0.008, 0.01), 120)}}
