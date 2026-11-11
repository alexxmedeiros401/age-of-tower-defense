# Cannon gunner: lighting the touch-hole (Attack ~f5-8) brought the right hand and the linstock across in front of
# the face, and again on the way back (~f32-34). The move is kept (hand path/orientation, linstock bone placement relative to the hand) but carried 15 cm
# out to the right and 10 cm forward over those frames, easing in/out; the arm is rebuilt (follow.py). Everything
# else (left arm, rammer, the rest of the clip) is shipped.
from mathutils import Vector as V
import follow as FW
FW.attach('linstock', 'R')
PRE = FW.pre(('R',)); POST = FW.attach_post
AXIS = FW.AXIS; AXIS2 = FW.AXIS2
def _ss(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)
def off(f):
    return V((-0.15, -0.10, 0.0)) * max(_ss(3, 5, f) * (1 - _ss(8, 10, f)), _ss(30, 32, f) * (1 - _ss(34, 36, f)))
CLIPS = {'Attack': {'R': FW.track('Attack', 'R', off)}}
WINDOW = {'Attack': {'R': [(4, 9, 1), (31, 35, 1)]}}
