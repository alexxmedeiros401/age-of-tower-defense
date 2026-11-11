# Torsion Catapult crewman: in Combat (and the start/end of Attack) the right hand was held on top of the head with
# the mallet hanging down through the face; in Idle the mallet ran through the beard; at the trigger strike and while
# waiting for the release (Attack ~f44-60) the mallet lay across the chest/beard. Re-authored the right arm: the
# mallet hangs from the fist at the right side (ready), winds back and strikes forward-down at the trigger, then waits
# at the side.
# The cranking (Attack ~f14-40) follows the shipped hand path on the winch handle with the mallet hanging (it
# lay across the belly); the left arm keeps its shipped motion (machine contacts).
import math
from mathutils import Vector as V
AXIS = {'R': V((-0.104, 0.994, 0.025))}           # mallet, grip -> head
READY = V((-0.50, -0.20, 1.02))
# The mallet sits in the fist across the palm: with a straight wrist it hangs down when the forearm is level and
# points forward when the forearm is upright, so the arm alone carries it (no wrist aiming).
ATK_R = [
    (0,  READY,                    {}),                # mallet hanging at the side
    (2,  V((-0.56, 0.06, 1.02)),  {}),                 # wind back at the side
    (4,  V((-0.38, -0.36, 1.04)),  {}),                # strike forward-down at the trigger
    (7,  V((-0.40, -0.28, 1.00)),  {}),
    (14, V((-0.56, -0.22, 0.92)),  {}),                # on the winch handle (shipped hand path)
    (20, V((-0.56, -0.25, 0.96)),  {}),
    (28, V((-0.56, -0.21, 0.91)),  {}),
    (36, V((-0.56, -0.23, 0.94)),  {}),
    (40, V((-0.56, -0.19, 0.90)),  {}),
    (44, V((-0.58, 0.02, 0.84)),   {}),
    (48, V((-0.48, -0.22, 1.05)),  {}),                # wait, mallet hanging at the side
    (58, V((-0.48, -0.22, 1.05)),  {}),
    (66, READY,                    {}),
]
def loop(base, amp, n, o):
    def k(f):
        a = 2 * math.pi * f / n
        return base + V((0, amp[0] * math.sin(a), amp[1] * math.sin(a))), o
    return k
CLIPS = {
    'Attack': {'R': ATK_R},
    'Combat': {'R': loop(READY, (0.01, 0.015), 40, {})},
    'Idle':   {'R': loop(READY + V((0.02, 0.04, -0.02)), (0.01, 0.01), 120, {})},
}
