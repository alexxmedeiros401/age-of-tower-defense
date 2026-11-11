# Cretan Archer (same rig, stance and clips as the Bronze Archer: body side-on, head turned ~70 deg to the target
# along chest +X): the draw hand anchored under the jaw inside the beard/neck (string through the face), the draw
# arm's shoulder skin collapsed, and the reach to the quiver went behind the helmet. Re-authored the draw arm as for
# the Bronze Archer: anchor beside the right jaw, elbow back along the arrow line; reload out beside the head to the
# fletchings, nock in front of the chest, draw back. Bow arm shipped; string/arrow follow (bowstring.py).
import math
from mathutils import Vector as V
import bowstring as BS
ANCHOR = V((-0.06, -0.33, 1.56))
EL = V((-0.9, 0.1, 0.25))                         # draw elbow: back along the arrow line
ATK_R = [
    (0,  ANCHOR,                    {'pole': EL}),
    (2,  V((-0.20, -0.36, 1.55)),   {'pole': EL}),   # release: the hand flicks back
    (6,  V((-0.50, -0.08, 1.74)),   {}),             # out beside the head
    (10, V((-0.42, 0.24, 1.88)),    {}),             # at the fletchings behind the right shoulder
    (12, V((-0.43, 0.23, 1.91)),    {}),
    (13, V((-0.50, 0.08, 1.84)),    {}),             # out from the quiver (beside the head)
    (15, V((-0.40, -0.30, 1.60)),   {}),             # out and forward
    (18, V((0.05, -0.36, 1.47)),    {}),             # nock, toward the bow
    (21, V((0.02, -0.35, 1.52)),    {}),             # draw
    (24, ANCHOR,                    {'pole': EL}),
]
def hold(f, n=40):
    a = 2 * math.pi * f / n
    return ANCHOR + V((0.004 * math.sin(a), 0, 0.006 * math.sin(a))), {'pole': EL}
CLIPS = {'Attack': {'R': ATK_R}, 'Combat': {'R': hold}}
PRE = BS.pre('L', 'R'); POST = BS.post
