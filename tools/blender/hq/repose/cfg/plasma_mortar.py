# Plasma Mortar operator (same Idle as the Missile Launcher): in Idle (~f52-75) the right hand goes up to the headset: the shipped arm folds flat
# (elbow 165-178 deg) with the hand above the shoulder, and the forearm/hand sink into the helmet and ear cup (head
# penetration ~14 cm). Re-authored that gesture: the hand goes to the outside of the ear cup with the elbow raised
# out to the side (a real "hand to headset" pose), the hand facing only loosely kept (aim 0.3); before/after the
# gesture the shipped hand path is followed and eased into (follow.py). Attack/Combat and the left arm: shipped.
from mathutils import Vector as V
import follow as FW
PRE = FW.pre(('R',))
AXIS = FW.AXIS; AXIS2 = FW.AXIS2
EAR = V((-0.31, -0.02, 1.62))
def _ss(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)
def w(f): return _ss(40, 54, f) * (1 - _ss(72, 86, f))
def off(f):
    # the hand travels out and forward on its way up/down (a straight path passes the shoulder and folds the arm flat)
    import math
    k = w(f)
    return (EAR - FW.orig('Idle', 'R', f)[0]) * k + V((-0.16, -0.18, 0.0)) * math.sin(math.pi * k)
def extra(f):
    return {'aim': 1.0 - 0.7 * w(f), 'pole': V((-0.85, -0.25, 0.45))}
CLIPS = {'Idle': {'R': FW.track('Idle', 'R', off, extra)}}
WINDOW = {'Idle': {'R': (40, 86, 3)}}
