# Knight (two-handed sword): both hands held the hilt in front of the chin with the blade across the visor (Combat,
# Attack start/end), the wind-up pulled the forearms across the helmet, and the recovery (Attack ~f16-20) raised the
# blade straight up through the helmet and plume. With these short arms both hands only meet on the hilt close in
# front of the chest, so the stance is re-authored as a low middle guard: hilt at the belt line, blade pointing
# forward-up away from the visor; the attack chambers at the right hip and thrusts forward, then returns. The left
# hand rides the hilt behind the right (GRAB); nothing passes in front of the face.
import math
from mathutils import Vector as V
AXIS = {'R': V((0.035, -0.969, 0.246))}           # sword: grip -> tip
GUARD = V((-0.07, -0.32, 1.12)); GD = V((0.05, -0.65, 0.76))
ATK_R = [
    (0,  GUARD,                    {'dir': GD}),
    (4,  V((-0.22, -0.22, 1.02)),  {'dir': V((0.10, -0.45, 0.89))}),    # chamber at the right hip
    (8,  V((-0.05, -0.40, 1.22)),  {'dir': V((0.05, -0.95, 0.30))}),    # thrust forward
    (13, V((-0.05, -0.39, 1.21)),  {'dir': V((0.05, -0.94, 0.33))}),
    (24, GUARD,                    {'dir': GD}),
]
L_ON_HILT = ('R', -0.09, V((0.0, 0.0, 0.0)))
def guard(f, n=40):
    a = 2 * math.pi * f / n
    return GUARD + V((0, 0.008 * math.sin(a), 0.012 * math.sin(a))), {'dir': GD}
CLIPS = {
    'Attack': {'R': ATK_R, 'L': [(0, GUARD, {})]},
    'Combat': {'R': guard, 'L': [(0, GUARD, {})]},
}
GRAB = {'Attack': {'L': L_ON_HILT}, 'Combat': {'L': L_ON_HILT}}
