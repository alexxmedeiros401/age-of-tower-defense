# Halberdier (side-on stance, head turned to the target along chest +X): at the start of the Attack (~f2-6) the
# halberd was swung up with the left hand passing under the chin (the left forearm through the jaw/neck, head
# penetration ~12 cm). The swing, grip and timing are kept: both hands keep their shipped orientations and their
# relation to each other, and the halberd bone (a separate prop bone) is re-keyed every frame to keep its shipped
# placement relative to the right hand. That phase is carried 25 cm lower, 15 cm forward and 12 cm toward the
# target side (peak f3-5, easing in over f1-3 and out over f5-8), so the left forearm passes in front of the chest
# below the chin; the arms are rebuilt for those hand places (follow.py + armsolve).
from mathutils import Vector as V
import follow as FW
FW.attach('halberd', 'R')
PRE = FW.pre(('R', 'L')); POST = FW.attach_post
AXIS = FW.AXIS; AXIS2 = FW.AXIS2
def _ss(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)
def off(f):
    return V((0.12, -0.15, -0.25)) * (_ss(0.0, 3.5, f) * (1 - _ss(5, 8, f)))
CLIPS = {'Attack': {'R': FW.track('Attack', 'R', off), 'L': FW.track('Attack', 'L', off, {'pole': V((0.8, -0.2, -0.55))})}}   # left elbow kept out at the left
WINDOW = {'Attack': {'R': (1, 8, 1), 'L': (1, 8, 1)}}
