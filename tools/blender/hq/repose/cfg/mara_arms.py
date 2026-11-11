# Mara (Stone hero): the staff was held in front of her face in every clip (the orb over her eyes in Combat, Attack,
# Idle and the Ability's slam). The right arm now holds it out at her right side, upright and leaning a little out,
# raised high beside (not over) her head in Ability and Cheer; the left arm's raised poses are spread clear of her
# antlers. Attack's left-hand fling keeps its old arm (it was clean).
import math
from mathutils import Vector as V
HERO = 'mara'
AXIS_R = V((-0.015, -0.994, 0.105))       # staff, toward the orb (rest armature space, from the hand.R-carried verts)
IDLE_R = V((-0.56, 0.02, 1.16)); IDLE_POLE_R = V((-0.80, 0.30, 1.20)); IDLE_DIR = V((-0.06, 0.04, 1.0))
HOLD_R = V((-0.58, -0.10, 1.18)); HOLD_POLE_R = V((-0.80, 0.15, 1.15)); HOLD_DIR = V((-0.12, 0.03, 0.99))
HIGH_R = V((-0.66, 0.00, 1.72)); HIGH_POLE_R = V((-0.95, 0.15, 1.55)); HIGH_DIR = V((-0.14, 0.06, 0.99))
SLAM_R = V((-0.60, -0.16, 1.24)); SLAM_POLE_R = V((-0.85, 0.05, 1.25)); SLAM_DIR = V((-0.10, 0.22, 0.97))

def idle_r(f, n=120):
    a = 2 * math.pi * f / n
    return IDLE_R + V((0, 0.025 * math.sin(a), 0.005 * math.sin(2 * a))), IDLE_POLE_R
def combat_r(f, n=40):
    a = 2 * math.pi * f / n
    return HOLD_R + V((0.01 * math.sin(a), 0, 0.012 * math.sin(a))), HOLD_POLE_R
def combat_aim(f, n=40):
    a = 2 * math.pi * f / n
    return (HOLD_DIR + V((0, 0.03 * math.sin(a), 0))).normalized(), None

CLIPS = {
    'Idle': {'R': idle_r, 'hand_R': lambda f: (IDLE_DIR, None), 'loop': True},
    'Combat': {'R': combat_r, 'hand_R': combat_aim, 'loop': True},
    'Attack': {   # (the left hand's fling is the attack; the staff sways with the crouch and the throw)
        'R': [(0, HOLD_R, HOLD_POLE_R), (6, V((-0.57, -0.13, 1.13)), HOLD_POLE_R), (12, V((-0.59, -0.08, 1.24)), HOLD_POLE_R),
              (20, V((-0.58, -0.09, 1.21)), HOLD_POLE_R), (30, HOLD_R, HOLD_POLE_R)],
        'hand_R': [(0, HOLD_DIR, None), (6, V((-0.10, 0.0, 0.99)), None), (12, V((-0.16, 0.06, 0.98)), None), (30, HOLD_DIR, None)],
    },
    'Ability': {   # Earthquake: staff raised high at her side, then driven down in front of her (orb outside the face)
        'R': [(0, IDLE_R, IDLE_POLE_R), (6, V((-0.52, -0.10, 1.42)), IDLE_POLE_R), (12, HIGH_R, HIGH_POLE_R),
              (18, HIGH_R, HIGH_POLE_R), (24, SLAM_R, SLAM_POLE_R), (38, SLAM_R + V((0, 0.02, -0.02)), SLAM_POLE_R),
              (48, V((-0.50, -0.10, 1.20)), IDLE_POLE_R), (54, IDLE_R, IDLE_POLE_R)],
        'hand_R': [(0, IDLE_DIR, None), (12, HIGH_DIR, None), (18, HIGH_DIR, None), (24, SLAM_DIR, None), (38, SLAM_DIR, None),
                   (54, IDLE_DIR, None)],
        'L': [(0, V((0.41, -0.09, 0.90)), V((0.80, 0.30, 1.10))), (6, V((0.48, -0.10, 1.30)), V((0.85, 0.25, 1.20))),
              (12, V((0.58, -0.12, 1.86)), V((0.90, 0.10, 1.60))), (18, V((0.58, -0.12, 1.88)), V((0.90, 0.10, 1.60))),
              (24, V((0.38, -0.34, 0.94)), V((0.70, 0.00, 1.10))), (38, V((0.37, -0.31, 0.91)), V((0.70, 0.00, 1.10))),
              (48, V((0.40, -0.18, 0.86)), V((0.80, 0.20, 1.10))), (54, V((0.41, -0.09, 0.90)), V((0.80, 0.30, 1.10)))],
    },
    'Cheer': {   # staff thrust up beside her head, left fist pumps out to the side
        'R': [(0, IDLE_R, IDLE_POLE_R), (6, HIGH_R, HIGH_POLE_R), (33, HIGH_R, HIGH_POLE_R),
              (40, IDLE_R, IDLE_POLE_R)],
        'hand_R': [(0, IDLE_DIR, None), (6, HIGH_DIR, None), (33, HIGH_DIR, None), (40, IDLE_DIR, None)],
        'L': [(0, V((0.40, -0.12, 0.93)), V((0.80, 0.25, 1.10))), (6, V((0.58, -0.08, 1.90)), V((0.90, 0.10, 1.60))),
              (9, V((0.60, -0.10, 1.72)), V((0.95, 0.10, 1.50))), (12, V((0.55, -0.13, 1.45)), V((0.90, 0.10, 1.30))),
              (21, V((0.55, -0.13, 1.45)), V((0.90, 0.10, 1.30))), (24, V((0.58, -0.10, 1.85)), V((0.90, 0.10, 1.60))),
              (27, V((0.58, -0.08, 1.92)), V((0.90, 0.10, 1.60))), (30, V((0.58, -0.10, 1.62)), V((0.95, 0.10, 1.45))),
              (33, V((0.52, -0.12, 1.43)), V((0.90, 0.10, 1.30))), (36, V((0.45, -0.12, 1.19)), V((0.85, 0.20, 1.15))),
              (40, V((0.40, -0.12, 0.93)), V((0.80, 0.25, 1.10)))],
    },
}
