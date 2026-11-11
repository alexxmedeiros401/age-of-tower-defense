# Kira (Bronze hero): the khopesh arm. Idle rested the blade over her right shoulder straight back through the edge of
# her hair and ponytail; Ability held it point-up in front of her face, then thrust it up with the fist against the
# side of her head; Cheer the same raised fist in her hair. The blade now rests over the outside of her shoulder, is
# held beside (not before) her face, and is thrust up out at her right. Combat and Attack (the spin) were clean: kept.
import math
from mathutils import Vector as V
HERO = 'kira'
AXIS_R = V((0.095, -0.913, 0.396))        # khopesh, toward the tip (rest armature space)
IDLE_R = V((-0.34, -0.14, 1.17)); IDLE_POLE = V((-0.70, -0.05, 1.05)); IDLE_DIR = V((-0.30, 0.72, 0.62))
COMBAT_R = V((-0.20, -0.25, 1.38)); COMBAT_POLE = V((-0.72, -0.15, 1.20)); COMBAT_DIR = V((0.20, -0.39, 0.90))
UP_R = V((-0.50, 0.00, 1.88)); UP_POLE = V((-1.0, 0.20, 1.60)); UP_DIR = V((-0.15, -0.70, 0.70))

def idle_r(f, n=120):
    a = 2 * math.pi * f / n
    return IDLE_R + V((0, 0.006 * math.sin(a), 0.01 * math.sin(a))), IDLE_POLE

CLIPS = {
    'Idle': {'R': idle_r, 'hand_R': 'world', 'loop': True},
    'Ability': {   # Solar Flare
        'R': [(0, COMBAT_R, COMBAT_POLE), (8, V((-0.34, -0.18, 1.26)), V((-0.75, 0.0, 1.15))), (12, V((-0.35, -0.16, 1.30)), V((-0.75, 0.0, 1.15))),
              (18, UP_R, UP_POLE), (36, UP_R, UP_POLE), (42, V((-0.50, -0.12, 1.78)), UP_POLE),
              (48, V((-0.38, -0.20, 1.52)), V((-0.78, -0.05, 1.30))), (54, COMBAT_R, COMBAT_POLE)],
        'hand_R': 'world', 'wrist_max': 180,
        'blend_R': (4, 4),
    },
    'Cheer': {   # sword thrust up at her right, a twirl, held high
        'R': [(0, IDLE_R, IDLE_POLE), (6, UP_R, UP_POLE), (12, UP_R + V((-0.03, -0.03, 0.0)), UP_POLE), (18, UP_R, UP_POLE),
              (33, UP_R, UP_POLE), (40, IDLE_R, IDLE_POLE)],
        'hand_R': 'world', 'wrist_max': 180,
    },
}
