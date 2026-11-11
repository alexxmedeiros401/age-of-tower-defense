# Brenna (Iron hero): the overhand spear fist sat at her cheek in Combat and drove straight across in front of her chin
# for the thrust (Attack), the shaft beats on the shield came across her chin (Ability) and the raised spear went up from
# a fist over her brow with the shaft down across her face (Ability's roar, Cheer). The spear fist now sits out beside
# her head, thrusts forward at her right, beats the shield low in front, and is raised out at her right; the spear keeps
# its shipped orientation in every frame (only where the fist is changes). Shield arm and Idle: clean, kept.
import math
from mathutils import Vector as V
HERO = 'brenna'
COMBAT = V((-0.46, 0.06, 1.58)); COMBAT_POLE = V((-0.95, 0.15, 1.40))
HIGH = V((-0.52, -0.05, 1.92)); HIGH_POLE = V((-0.95, 0.15, 1.65))
RAISE = V((-0.46, -0.10, 1.72)); RAISE_POLE = V((-0.95, 0.10, 1.50))
BEAT = V((-0.30, -0.42, 1.30)); BEAT_POLE = V((-0.85, -0.10, 1.25))
THRUST = V((-0.38, -0.46, 1.50)); THRUST_POLE = V((-0.90, -0.10, 1.45))

def combat_r(f, n=40):
    return COMBAT + V((0, 0, 0.012 * math.sin(2 * math.pi * f / n))), COMBAT_POLE

CLIPS = {
    'Combat': {'R': combat_r, 'hand_R': 'world', 'loop': True},
    'Attack': {   # THRUST at frame 6
        'R': [(0, COMBAT, COMBAT_POLE), (3, V((-0.50, 0.16, 1.62)), COMBAT_POLE), (6, THRUST, THRUST_POLE),
              (9, THRUST + V((0, -0.01, -0.01)), THRUST_POLE), (12, V((-0.40, -0.40, 1.50)), THRUST_POLE),
              (15, V((-0.44, -0.20, 1.53)), COMBAT_POLE), (18, V((-0.46, -0.02, 1.56)), COMBAT_POLE), (21, COMBAT, COMBAT_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
    'Ability': {   # War Cry: CLASH 11 and 19, ROAR 26
        'R': [(0, COMBAT, COMBAT_POLE), (3, V((-0.44, -0.08, 1.58)), RAISE_POLE), (7, RAISE, RAISE_POLE), (11, BEAT, BEAT_POLE),
              (15, RAISE, RAISE_POLE), (19, BEAT, BEAT_POLE), (22, V((-0.40, -0.25, 1.55)), RAISE_POLE), (26, HIGH, HIGH_POLE),
              (39, HIGH, HIGH_POLE), (42, HIGH + V((0, 0, -0.04)), HIGH_POLE), (45, V((-0.46, 0.0, 1.66)), COMBAT_POLE),
              (48, COMBAT, COMBAT_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.5,
    },
    'Cheer': {
        'R': [(0, COMBAT, COMBAT_POLE), (3, V((-0.50, -0.08, 1.80)), HIGH_POLE), (6, HIGH, HIGH_POLE), (33, HIGH, HIGH_POLE),
              (36, V((-0.50, -0.06, 1.84)), HIGH_POLE), (40, COMBAT, COMBAT_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.5,
    },
}
