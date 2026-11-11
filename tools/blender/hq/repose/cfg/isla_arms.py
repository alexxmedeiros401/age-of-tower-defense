# Isla (Gunpowder hero): the cutlass was raised high from a fist inside the crown of her tricorn (Ability 24-27 "raises
# it high", Cheer 18-33) and brought up/down across the front of her face (Ability 18 and 30, Cheer 36). Those frames
# now raise it out at her right, beside the hat, and bring it up and down in front of her right shoulder. Every other
# frame follows the shipped wrist path (the draw across her body, the sheathing, the pistol). The cutlass (a parentless
# prop) keeps its grip; the fist keeps its shipped orientation per frame.
from mathutils import Vector as V
HERO = 'isla'
P_LOW = V((-0.80, 0.20, 1.10)); P_HIGH = V((-1.00, 0.15, 1.70))
def path(keys):
    return [(f, V(w), P_HIGH if w[2] > 1.6 else P_LOW) for f, w in keys]
UP = (-0.52, 0.00, 1.94)
CLIPS = {
    'Ability': {   # Broadside: SIGNAL 31 (the cutlass swept down to point at the robots)
        'R': path([(0, (-0.63, -0.40, 1.35)), (3, (-0.17, -0.45, 1.32)), (6, (-0.06, -0.26, 1.06)), (9, (0.13, -0.19, 1.02)),
                   (12, (0.14, -0.22, 1.06)), (15, (-0.26, -0.32, 1.40)), (18, (-0.50, -0.30, 1.60)), (21, (-0.58, -0.12, 1.82)),
                   (24, UP), (27, (-0.53, 0.02, 1.96)), (30, (-0.46, -0.40, 1.76)), (33, (-0.30, -0.54, 1.47)), (36, (-0.28, -0.55, 1.45)),
                   (39, (-0.28, -0.55, 1.46)), (42, (0.10, -0.33, 1.50)), (45, (-0.04, -0.27, 1.50)), (48, (0.00, -0.22, 1.27)),
                   (51, (0.13, -0.20, 1.03)), (54, (-0.04, -0.27, 1.06)), (57, (-0.11, -0.48, 1.32)), (60, (-0.60, -0.43, 1.35)),
                   (64, (-0.63, -0.40, 1.35))]),
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
    'Cheer': {
        'R': path([(0, (-0.63, -0.40, 1.35)), (3, (-0.10, -0.37, 1.30)), (6, (0.06, -0.22, 1.00)), (9, (0.14, -0.21, 1.04)),
                   (12, (-0.12, -0.25, 1.40)), (15, (-0.38, -0.36, 1.62)), (18, UP), (33, UP), (36, (-0.42, -0.30, 1.70)),
                   (39, (-0.14, -0.24, 1.42)), (42, (0.14, -0.21, 1.04)), (45, (-0.04, -0.27, 1.06)), (48, (-0.19, -0.51, 1.33)),
                   (50, (-0.63, -0.40, 1.35))]),
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
}
