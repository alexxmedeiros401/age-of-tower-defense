# Musketeer (pass 2): ramming the charge (Attack ~f13-22) pushes the right fist down the upright barrel above his head:
# the fist and the ramrod went through the wide hat brim (up to 6 cm). The whole loading move (both hands, the musket,
# the ramrod and the charge, which ride with the hands) is carried 5 cm forward, 11 cm lower and 3 cm out to his left over those
# frames, easing in over f9-12 and out over f22-25; the arms are rebuilt (follow.py + armsolve). Timing, grip and the
# rest of the clip are shipped.
from mathutils import Vector as V
import follow as FW
FW.attach('musket', 'L'); FW.attach('charge', 'L'); FW.attach('ramrod', 'R')
PRE = FW.pre(('R', 'L')); POST = FW.attach_post
AXIS = FW.AXIS; AXIS2 = FW.AXIS2
def _ss(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)
def off(f):
    return V((0.03, -0.05, -0.11)) * (_ss(9, 12, f) * (1 - _ss(22, 25, f)))
CLIPS = {'Attack': {'L': FW.track('Attack', 'L', off), 'R': FW.track('Attack', 'R', off, extra={'pole': V((-1.0, 0.4, -0.3))})}}
WINDOW = {'Attack': {'L': (8, 26, 1), 'R': (8, 26, 1)}}
