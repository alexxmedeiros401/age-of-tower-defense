# War Drummer: the flourish at the start of the Attack (~f4-8) and the second one (~f11) raised the right stick across in front of
# the nose.
# The flourish is kept (hand path/orientation, the stick is a child of the hand) but carried 12 cm out to the right,
# 6 cm forward and 6 cm lower over those frames, easing in/out; the arm is rebuilt (follow.py). Left arm: shipped.
from mathutils import Vector as V
import follow as FW
PRE = FW.pre(('R',))
AXIS = FW.AXIS; AXIS2 = FW.AXIS2
def _ss(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)
def off(f):
    return V((-0.12, -0.06, -0.06)) * max(_ss(2, 4, f) * (1 - _ss(8, 10, f)), _ss(9, 10, f) * (1 - _ss(12, 14, f)))
CLIPS = {'Attack': {'R': FW.track('Attack', 'R', off)}}
WINDOW = {'Attack': {'R': (3, 13, 1)}}
