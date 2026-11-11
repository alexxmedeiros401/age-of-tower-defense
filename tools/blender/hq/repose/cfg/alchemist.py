# Alchemist: the flask (right hand) was held up under the chin and lifted into the face to be inspected (Combat,
# Attack ~f1-9, Idle ~f25-90), and in the Attack (~f12-22) the left hand crossed in front of the face to pour.
# The gestures and their timing are right, so the hands keep their shipped paths and orientations (flask upright,
# vial in the left hand) but are moved: the flask is held 8 cm lower and out to the right, and when it is lifted to be inspected it
# goes out to the right of the face, not in front of it (it sat under the chin); the left hand pours from out at the
# left side.
# The arms are rebuilt for the new hand places (follow.py + armsolve).
from mathutils import Vector as V
import follow as FW
PRE = FW.pre(('R', 'L'))
AXIS = FW.AXIS; AXIS2 = FW.AXIS2
def _ss(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)
def off_r(clip):
    def o(f):
        p = FW.orig(clip, 'R', f)[0]
        lift = _ss(1.18, 1.42, p.z)            # out to the right of the face when lifted
        return V((-0.08 - 0.10 * lift, -0.03 - 0.05 * lift, -0.08))
    return o
def off_l(f):
    w = _ss(8, 12, f) * (1 - _ss(21, 25, f))   # the pour (Attack ~f12-22) moves out to the left side
    return V((0.24, -0.08, -0.10)) * w
def aim_r(f):   # the flask flip at the pour (Attack ~f4-11) needed a ~110 deg wrist: there the flask facing is a hint
    return {'aim': 1.0 - 0.6 * _ss(2, 5, f) * (1 - _ss(10, 13, f))}
CLIPS = {c: {'R': FW.track(c, 'R', off_r(c))} for c in ('Combat', 'Idle')}
CLIPS['Attack'] = {'R': FW.track('Attack', 'R', off_r('Attack'), aim_r)}
CLIPS['Attack']['L'] = FW.track('Attack', 'L', off_l)
