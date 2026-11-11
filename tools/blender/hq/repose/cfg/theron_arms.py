# Theron (Classical hero): the sun-staff was held with its sun beside/in front of his face in Combat and Attack (the sun
# at head height 3 cm off his cheek, over his face from the front), raised from a fist in front of his face (Ability's
# vision, Cheer), and levelled from a fist in front of his chin (Ability's flare). The staff fist is moved out to his
# right along the same paths (the shipped wrist path shifted out 18-26 cm, the raises out beside his head); the staff
# keeps its shipped orientation per frame. Idle and the left arm: clean, kept.
from mathutils import Vector as V
HERO = 'theron'

def ramp(f, pts):
    for (a, wa), (b, wb) in zip(pts, pts[1:]):
        if a <= f <= b:
            t = (f - a) / float(b - a); t = t * t * (3 - 2 * t); return wa + (wb - wa) * t
    return pts[-1][1] if f > pts[-1][0] else pts[0][1]
POLE = V((-0.95, 0.15, 1.15)); HIGH_POLE = V((-1.00, 0.15, 1.65))
def shift(keys, dx=-0.20, dy=0.03, pole=POLE):
    return [(f, V(w) + V((dx, dy, 0)), pole) for f, w in keys]
STANCE = (-0.35, -0.19, 1.07)
CLIPS = {
    'Combat': {'R': shift([(0, STANCE), (40, STANCE)]), 'hand_R': 'world', 'loop': True},
    'Attack': {   # lift 0-6, HIT 9 (the staff foot struck down before him), hold, settle
        'R': shift([(0, STANCE), (3, (-0.37, -0.15, 1.15)), (6, (-0.39, -0.12, 1.24)), (9, (-0.36, -0.34, 1.22)),
                    (12, (-0.35, -0.35, 1.18)), (18, (-0.35, -0.35, 1.15)), (24, (-0.34, -0.28, 1.12)), (32, STANCE)], dx=-0.24),
        'hand_R': 'world',
        # the strike leans him over the staff: its sun tilted out to his right (25 deg) so it stays off his face
        'world_rot': lambda f: ((0, 1, 0), -25 * ramp(f, [(0, 0), (6, 0), (9, 1), (21, 1), (30, 0)])),
    },
    'Ability': {   # Prophecy: staff raised high beside his head (VISION 20), levelled at the robots (FLARE 34), settle
        'R': shift([(0, STANCE), (3, (-0.34, -0.18, 1.14)), (6, (-0.36, -0.14, 1.33))]) +
             [(9, V((-0.46, -0.10, 1.58)), HIGH_POLE), (12, V((-0.52, -0.08, 1.80)), HIGH_POLE), (15, V((-0.55, -0.08, 1.90)), HIGH_POLE),
              (27, V((-0.55, -0.08, 1.90)), HIGH_POLE), (30, V((-0.50, -0.12, 1.82)), HIGH_POLE),
              (33, V((-0.33, -0.40, 1.46)), POLE), (36, V((-0.30, -0.46, 1.39)), POLE), (42, V((-0.30, -0.46, 1.38)), POLE),
              (45, V((-0.31, -0.46, 1.33)), POLE), (48, V((-0.30, -0.41, 1.29)), POLE)] +
             shift([(51, (-0.28, -0.25, 1.24)), (54, (-0.33, -0.22, 1.13)), (58, STANCE)]),
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
    'Cheer': {   # two thumps of the staff, then lifted high beside his head
        'R': shift([(0, STANCE), (3, (-0.35, -0.19, 1.14)), (6, (-0.35, -0.19, 1.12)), (9, STANCE), (15, STANCE), (18, (-0.34, -0.16, 1.20))]) +
             [(21, V((-0.48, -0.06, 1.60)), HIGH_POLE), (24, V((-0.56, -0.02, 1.88)), HIGH_POLE), (33, V((-0.56, -0.02, 1.88)), HIGH_POLE),
              (36, V((-0.50, -0.06, 1.66)), HIGH_POLE)] + shift([(39, (-0.34, -0.18, 1.13)), (40, STANCE)]),
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
    'Idle': {'R': shift([(0, (-0.42, 0.09, 1.05)), (120, (-0.42, 0.09, 1.05))], dx=-0.14, dy=0.0), 'hand_R': 'world', 'loop': True},
}
