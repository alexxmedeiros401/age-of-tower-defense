# Arc Cannon operator: in Idle (~f58-82) the right hand came up across the face to the left side of the chin
# (the forearm across the mouth, ~5 cm into the chin). The gesture and timing are kept (shipped hand path and
# orientation) but the hand stays on the right side: it is carried 16 cm to the right and 3 cm down at the hold,
# eased in and out; the arm is rebuilt for that (follow.py). Combat/Attack and the left arm: shipped.
from mathutils import Vector as V
import follow as FW
PRE = FW.pre(('R',))
AXIS = FW.AXIS; AXIS2 = FW.AXIS2
def _ss(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)
def off(f):
    return V((-0.16, -0.02, -0.03)) * (_ss(52, 62, f) * (1 - _ss(78, 88, f)))
CLIPS = {'Idle': {'R': FW.track('Idle', 'R', off)}}
WINDOW = {'Idle': {'R': (52, 88, 2)}}
