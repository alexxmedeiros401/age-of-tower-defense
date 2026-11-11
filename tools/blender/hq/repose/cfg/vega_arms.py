# Commander Vega (Data Center hero): the Idle and the Cheer held the pistol up "beside his right shoulder" right in front
# of his face (the muzzle across his eyes from the front), and the Ability's raised killswitch (24-32) came down past the
# left of his head (0-1 cm). Offsets on the shipped paths: the raised pistol 14 cm out and 8 cm back, the killswitch
# hand 12 cm out at his left. Fists keep their shipped orientation; the pistol and the switch keep their grip.
from mathutils import Vector as V
HERO = 'vega'
HOLD_PROPS = ['pistol', 'switch']
def ramp(f, pts):
    for (a, wa), (b, wb) in zip(pts, pts[1:]):
        if a <= f <= b:
            t = (f - a) / float(b - a); t = t * t * (3 - 2 * t); return wa + (wb - wa) * t
    return pts[-1][1] if f > pts[-1][0] else pts[0][1]
UPR = V((-0.14, 0.08, 0.0))
CLIPS = {
    'Idle': {'R': {'offset': UPR}, 'hand_R': 'world', 'loop': True},
    'Cheer': {'R': {'offset': lambda f: UPR * ramp(f, [(0, 0), (3, 0), (8, 1), (38, 1), (44, 0)])}, 'hand_R': 'world'},
    'Ability': {'L': {'offset': lambda f: V((0.12, 0.0, 0.0)) * ramp(f, [(0, 0), (16, 0), (22, 1), (32, 1), (36, 0)])}, 'hand_L': 'world', 'keep_roll': True},
}
