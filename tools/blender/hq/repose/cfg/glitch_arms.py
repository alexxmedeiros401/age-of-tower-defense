# Glitch (Digital hero): the Attack's fling (frames 0-4: both blades thrown up and out before the cross slash) brought the
# right blade up past the front of his face (from the side it crosses his visor), and the Cheer's V held both blades close
# beside his head. Offsets on the shipped paths widen these: the flung fists 15 cm further out to each side, the Cheer's
# raised fists 10 cm out. The blades ride the forearms, so the arms keep their shipped upper-arm roll and forearm twist
# ('keep_roll': only where the arm points changes) and the hands their shipped wrist. HIT 5 unchanged.
from mathutils import Vector as V
HERO = 'glitch'
def ramp(f, pts):
    for (a, wa), (b, wb) in zip(pts, pts[1:]):
        if a <= f <= b:
            t = (f - a) / float(b - a); t = t * t * (3 - 2 * t); return wa + (wb - wa) * t
    return pts[-1][1] if f > pts[-1][0] else pts[0][1]
FL = [(0, 0), (2, 1), (4, 0.6), (6, 0)]
CH = [(0, 0), (4, 0), (8, 1), (40, 1), (44, 0)]
CLIPS = {
    'Attack': {'R': {'offset': lambda f: V((-0.15, 0.03, 0)) * ramp(f, FL)}, 'L': {'offset': lambda f: V((0.15, 0.03, 0)) * ramp(f, FL)},
               'hand_R': 'keep', 'hand_L': 'keep', 'keep_roll': True},
    'Cheer': {'R': {'offset': lambda f: V((-0.10, 0.02, 0)) * ramp(f, CH)}, 'L': {'offset': lambda f: V((0.10, 0.02, 0)) * ramp(f, CH)},
              'hand_R': 'keep', 'hand_L': 'keep', 'keep_roll': True},
}
