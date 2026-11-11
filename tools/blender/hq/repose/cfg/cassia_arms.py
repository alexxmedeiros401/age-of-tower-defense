# Cassia (Classical hero): the gladius raised for the charge order (Ability 6-21) and for the Cheer (3-36) went up from a
# fist in front of her face, the forearm across her face and the blade over her helmet. The fist now rises out at her
# right (x 0.55), beside the helmet; the gladius keeps its shipped orientation per frame. Combat, Attack, Idle, the
# shield arm: clean, kept.
from mathutils import Vector as V
HERO = 'cassia'

def ramp(f, pts):
    for (a, wa), (b, wb) in zip(pts, pts[1:]):
        if a <= f <= b:
            t = (f - a) / float(b - a); t = t * t * (3 - 2 * t); return wa + (wb - wa) * t
    return pts[-1][1] if f > pts[-1][0] else pts[0][1]
STANCE = V((-0.26, -0.27, 1.19)); STANCE_POLE = V((-0.80, 0.00, 1.10))
ORDER = V((-0.55, -0.18, 1.88)); ORDER_POLE = V((-1.00, 0.10, 1.65))
HIGH = V((-0.56, -0.02, 1.92)); HIGH_POLE = V((-1.00, 0.20, 1.65))
CLIPS = {
    'Ability': {   # ORDER at frame 12, SLAM 31
        'R': [(0, STANCE, STANCE_POLE), (3, V((-0.34, -0.26, 1.34)), STANCE_POLE), (6, V((-0.46, -0.24, 1.60)), ORDER_POLE),
              (9, ORDER + V((0, 0, -0.03)), ORDER_POLE), (12, ORDER, ORDER_POLE), (18, ORDER, ORDER_POLE),
              (21, V((-0.40, -0.18, 1.46)), STANCE_POLE), (24, V((-0.26, -0.16, 1.16)), STANCE_POLE)] +
             [(f, None, None) for f in ()],
        'hand_R': 'world', 'hand_smooth': 1.0,
        # the order: the blade's point swung out to her right (it pointed forward across her face from the front)
        'world_rot': lambda f: ((0, 0, 1), -45 * ramp(f, [(0, 0), (6, 1), (18, 1), (24, 0)])),
    },
    'Cheer': {
        'R': [(0, STANCE, STANCE_POLE), (3, V((-0.42, -0.14, 1.60)), ORDER_POLE), (6, HIGH, HIGH_POLE), (33, HIGH, HIGH_POLE),
              (36, V((-0.42, -0.12, 1.64)), ORDER_POLE), (40, STANCE, STANCE_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
}
# Ability after frame 24: the shipped arm (the charge behind the shield, sword low at her hip) is kept by easing back
CLIPS['Ability']['R'] = [k for k in CLIPS['Ability']['R'] if k[1] is not None] + [
    (30, V((-0.26, -0.08, 1.17)), STANCE_POLE), (39, V((-0.26, -0.07, 1.17)), STANCE_POLE), (45, V((-0.25, -0.17, 1.19)), STANCE_POLE),
    (52, STANCE, STANCE_POLE)]
