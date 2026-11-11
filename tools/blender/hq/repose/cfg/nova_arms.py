# Nova (Digital hero): Cheer thrust the pistol up from a fist in her hair (the right of her head, 2-3 cm in), the
# Ability's skyward signal raised the left fist against the left of her head, and the Idle held the pistol up in front of
# her right cheek. Offsets on the shipped paths (eased in/out) move these out to her side: the raised fists 15-20 cm
# further out, the Idle pistol 13 cm out and 8 cm back. Fists keep their shipped orientation; the pistol keeps its grip.
# Combat/Attack (the one-handed aim) clean, kept.
from mathutils import Vector as V
HERO = 'nova'
HOLD_PROPS = ['laser']
def ramp(f, pts):
    for (a, wa), (b, wb) in zip(pts, pts[1:]):
        if a <= f <= b:
            t = (f - a) / float(b - a); t = t * t * (3 - 2 * t); return wa + (wb - wa) * t
    return pts[-1][1] if f > pts[-1][0] else pts[0][1]
CLIPS = {
    'Cheer': {'R': {'offset': lambda f: V((-0.16, 0.0, 0.0)) * ramp(f, [(0, 0), (4, 0), (9, 1), (36, 1), (40, 0)])},
              'L': {'offset': lambda f: V((0.06, 0.0, 0.0)) * ramp(f, [(0, 0), (4, 0), (9, 1), (36, 1), (40, 0)])},
              'hand_R': 'world', 'hand_L': 'world'},
    'Ability': {'L': {'offset': lambda f: V((0.20, 0.0, -0.04)) * ramp(f, [(0, 0), (31, 0), (36, 1), (54, 1), (58, 0)])}, 'hand_L': 'world'},
    'Idle': {'R': {'offset': V((-0.13, 0.08, 0.0))}, 'hand_R': 'world', 'loop': True},
}
