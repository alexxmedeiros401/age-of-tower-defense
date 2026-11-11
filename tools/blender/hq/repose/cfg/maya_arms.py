# Maya (Modern hero): on the aim (Combat, the Attack's burst, and the ends of Ability/Cheer that meet it) the rifle ran
# through her lower face: the scope at her mouth, the stock 7-11 cm into her jaw. Both hands (and the rifle, a parentless
# prop that keeps its grip) are moved together 7 cm to her right and 3 cm down, so the stock sits against her right
# cheek and the sight line passes beside her face. The Cheer's raised rifle is held further out at her right. The
# shipped wrist paths are kept otherwise (offsets only); fists keep their shipped orientation.
from mathutils import Vector as V
HERO = 'maya'
HOLD_PROPS = ['rifle']
AIM = V((-0.13, 0.02, -0.01))
def ramp(f, pts):
    for (a, wa), (b, wb) in zip(pts, pts[1:]):
        if a <= f <= b:
            t = (f - a) / float(b - a); t = t * t * (3 - 2 * t); return wa + (wb - wa) * t
    return pts[-1][1] if f > pts[-1][0] else pts[0][1]
CLIPS = {
    'Combat': {'R': {'offset': AIM}, 'L': {'offset': AIM}, 'hand_R': 'world', 'hand_L': 'world', 'loop': True},
    'Attack': {'R': {'offset': AIM}, 'L': {'offset': AIM}, 'hand_R': 'world', 'hand_L': 'world'},
    'Ability': {'R': {'offset': lambda f: AIM * ramp(f, [(0, 1), (6, 0), (63, 0), (70, 1)]) + V((-0.10, 0.04, 0)) * ramp(f, [(0, 0), (4, 0), (8, 1), (60, 1), (64, 0)])},
                'L': {'offset': lambda f: AIM * ramp(f, [(0, 1), (6, 0), (63, 0), (70, 1)])}, 'hand_R': 'world', 'hand_L': 'world'},
    'Cheer': {'R': {'offset': lambda f: AIM * ramp(f, [(0, 1), (5, 0), (42, 0), (48, 1)]) + V((-0.14, 0.06, 0)) * ramp(f, [(0, 0), (6, 0), (10, 1), (34, 1), (39, 0)])},
              'L': {'offset': lambda f: AIM * ramp(f, [(0, 1), (5, 0), (42, 0), (48, 1)])}, 'hand_R': 'world', 'hand_L': 'world'},
}
