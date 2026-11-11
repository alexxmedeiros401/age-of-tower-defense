# Javelin Thrower (side-on stance in Combat/Attack, the target along chest +X, head turned to it): the cocked
# javelin ran through the beard/chin at shoulder height, the reload reached behind the neck (hand into the head at
# Attack ~f12), and in Idle (~f64-92) the javelin was lifted across the chin. Re-authored the throwing arm: cocked
# with the hand back beside the head and the shaft passing outside the cheek, the throw drives forward past the face
# side, the reload goes up the outside to the quiver behind the right shoulder; Idle rests the javelin on the right
# shoulder instead (and holds it upright at the side, not pointing down, the rest of the clip). The aiming (left) arm keeps its shipped motion.
import math
from mathutils import Vector as V
AXIS = {'R': V((-0.006, -0.993, 0.12))}            # javelin, grip -> tip
READY = V((-0.50, -0.30, 1.65)); T = V((0.95, 0.0, 0.30))
ATK_R = [   # (the javelin is hidden f3-14: the wrist is left straight there, aim 0)
    (0,  READY,                    {'dir': T}),
    (2,  V((-0.14, -0.40, 1.60)),  {'dir': V((0.97, -0.10, 0.20))}),            # throw past the cheek
    (4,  V((-0.04, -0.36, 1.42)),  {'dir': V((0.90, -0.30, -0.30)), 'aim': 0.0}),  # follow-through
    (8,  V((-0.45, -0.30, 1.48)),  {'dir': V((0.30, -0.30, 0.90)), 'aim': 0.0}),
    (12, V((-0.50, 0.10, 1.76)),   {'dir': V((-0.30, 0.20, 0.93)), 'aim': 0.0}),   # up the outside to the quiver
    (15, V((-0.42, 0.34, 1.78)),   {'dir': V((-0.52, 0.31, 0.79)), 'aim': 0.4}),   # grab a javelin behind the right shoulder
    (18, V((-0.46, 0.28, 1.86)),   {'dir': V((-0.45, 0.25, 0.86)), 'aim': 0.4}),           # draw it out upwards
    (21, V((-0.54, -0.10, 1.78)),  {'dir': V((0.35, -0.15, 0.92)), 'aim': 0.7}),           # bring it over beside the head
    (24, READY,                    {'dir': T}),
]
IDLE = V((-0.42, -0.10, 1.02)); UP = V((-0.05, -0.10, 0.99))
IDLE_R = [
    (0,  IDLE,                     {'dir': UP}),        # javelin stood upright at the right side
    (60, IDLE,                     {'dir': UP}),
    (70, V((-0.40, -0.30, 1.34)),  {'dir': V((-0.05, 0.55, 0.83))}),   # shouldered (rests on the right shoulder)
    (86, V((-0.40, -0.30, 1.35)),  {'dir': V((-0.05, 0.55, 0.83))}),
    (98, IDLE,                     {'dir': UP}),
    (120, IDLE,                    {'dir': UP}),
]
def hold(f, n=40):
    a = 2 * math.pi * f / n
    return READY + V((0.0, 0.005 * math.sin(a), 0.01 * math.sin(a))), {'dir': T}
CLIPS = {'Attack': {'R': ATK_R}, 'Combat': {'R': hold}, 'Idle': {'R': IDLE_R}}
