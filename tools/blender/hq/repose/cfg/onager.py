# Onager crewman (same crew clips as the Torsion Catapult): in Combat and the start/end of Attack the right hand sat
# on top of the head with the mallet hanging down in front of the face, Idle held the mallet across the beard, and
# the trigger strike / release wait (Attack ~f2-8, ~f44-60) laid it across the chest. Re-authored the right arm as for
# the Torsion Catapult: mallet hanging from the fist at the right side (straight wrist), wind back and strike
# forward-down at the trigger, wait at the side. Cranking (~f14-40): the shipped
# hand path on the winch with the mallet hanging (not across the belly). Left arm: shipped (machine contacts).
import math
from mathutils import Vector as V
AXIS = {'R': V((-0.001, 0.904, 0.427))}           # mallet, grip -> head
READY = V((-0.50, -0.20, 1.02))
# The mallet sits in the fist across the palm: with a straight wrist it hangs down when the forearm is level and
# points forward when the forearm is upright, so the arm alone carries it (no wrist aiming).
ATK_R = [
    (0,  READY,                    {}),                # mallet hanging at the side
    (2,  V((-0.56, 0.06, 1.02)),  {}),                 # wind back at the side
    (4,  V((-0.38, -0.36, 1.04)),  {}),                # strike forward-down at the trigger
    (7,  V((-0.40, -0.28, 1.00)),  {}),
    (14, V((-0.56, -0.24, 1.05)),  {}),                # on the winch handle (shipped hand path)
    (24, V((-0.56, -0.22, 1.03)),  {}),
    (32, V((-0.56, -0.21, 1.02)),  {}),
    (40, V((-0.56, -0.19, 0.99)),  {}),
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
