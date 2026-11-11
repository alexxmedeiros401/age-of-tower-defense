# Ugo (Stone hero): Throw re-authored (the old whip crossed the face and folded the left arm behind the hood),
# Ability's raised arms spread to the sides of the sabertooth hood. Whirl, Idle, Cheer keep their arms.
import math
from mathutils import Vector as V
HERO = 'ugo'
UP_R = V((-0.75, 0.05, 1.87)); UP_POLE_R = V((-1.15, 0.10, 1.50))      # the whirl pose (Whirl's ends)
AIM_L = V((0.46, -0.47, 1.57)); AIM_POLE_L = V((0.75, -0.10, 1.25))   # left hand pointing at the target
CLIPS = {
    'Throw': {   # release at frame 3: whip forward out beside the hood, follow through, reload at the hip pouch
        'R': [(0, UP_R, UP_POLE_R),
              (3, V((-0.60, -0.16, 2.04)), V((-1.15, 0.10, 1.70))),
              (6, V((-0.58, -0.50, 1.62)), V((-1.10, -0.05, 1.45))),
              (9, V((-0.52, -0.52, 1.20)), V((-1.05, 0.15, 1.20))),
              (15, V((-0.52, -0.32, 1.00)), V((-1.00, 0.40, 1.10))),
              (20, V((-0.70, -0.08, 1.48)), V((-1.15, 0.30, 1.30))),
              (24, UP_R, UP_POLE_R)],
        'L': [(0, AIM_L, AIM_POLE_L),
              (4, V((0.52, -0.22, 1.30)), V((1.00, 0.20, 1.15))),
              (9, V((0.54, -0.10, 1.16)), V((1.00, 0.30, 1.10))),
              (15, V((0.50, -0.30, 1.30)), V((1.00, 0.15, 1.15))),
              (24, AIM_L, AIM_POLE_L)],
        'hand_L': 'straight', 'keep_world': ['sling'], 'blend_R': (2, 2), 'blend_L': (4, 4),
    },
    'Ability': {   # crouch, spring up with both arms thrown high OUT beside the hood, roar, sweep the sling at the enemy
        'R': [(0, V((-0.55, -0.13, 1.03)), V((-1.0, 0.35, 1.15))),
              (8, V((-0.52, -0.22, 1.12)), V((-1.0, 0.30, 1.20))),
              (14, V((-0.64, -0.06, 2.04)), V((-1.15, 0.15, 1.75))),
              (22, V((-0.65, -0.06, 2.05)), V((-1.15, 0.15, 1.75))),
              (30, V((-0.64, -0.06, 2.04)), V((-1.15, 0.15, 1.75))),
              (38, V((-0.42, -0.62, 1.38)), V((-1.05, -0.05, 1.30))),
              (48, V((-0.55, -0.13, 1.05)), V((-1.0, 0.35, 1.15)))],
        'L': [(0, V((0.33, 0.00, 1.06)), V((0.9, 0.35, 1.15))),
              (8, V((0.47, -0.18, 1.10)), V((1.0, 0.30, 1.20))),
              (14, V((0.66, -0.06, 1.96)), V((1.15, 0.15, 1.70))),
              (30, V((0.66, -0.06, 1.96)), V((1.15, 0.15, 1.70))),
              (38, V((0.45, -0.22, 1.12)), V((1.0, 0.30, 1.15))),
              (48, V((0.33, 0.00, 1.08)), V((0.9, 0.35, 1.15)))],
        'hand_L': 'straight', 'keep_world': ['sling'], 'blend': (3, 3),
    },
}
