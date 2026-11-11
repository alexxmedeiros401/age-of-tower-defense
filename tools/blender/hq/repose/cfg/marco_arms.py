# Marco (Gunpowder hero): the cocked grenade fist sat against the back of his head (Combat, and the ends of Attack and
# Ability: 3-4 cm in), the overarm lob wound up over the crown of his head (Attack 8), the lighting at the match on his
# chest came up past his chin into his face (Attack 22-32, Ability 60-70), the keg throw's follow-through drove his right
# fist into his face (Ability 46-48), and the left hand reached behind his neck for the keg on his shoulder (Ability
# 20-28). The cock is moved out beside his head, the wind-up out at his right, the lighting and the follow-through kept
# in front of his chest, the left hand on the keg's front. Each hand keeps its shipped orientation per frame; the
# grenade/keg (parentless props) keep their grip. Cheer: the cap is taken off/put back on by hand (intended contact),
# kept; the right fist pump passes kept.
from mathutils import Vector as V
HERO = 'marco'
HOLD_PROPS = ['grenade', 'keg']        # (the cap stays on his head: it is never in the right hand)
COCK = (-0.58, 0.16, 1.55)
PR = V((-0.95, 0.20, 1.25)); PRH = V((-1.00, 0.20, 1.65)); PL = V((0.90, 0.20, 1.20))
def path(keys, pole=PR, hi=None):
    return [(f, V(w), (hi if (hi is not None and w[2] > 1.62) else pole)) for f, w in keys]
CLIPS = {
    'Combat': {'R': lambda f: (V(COCK), PR), 'hand_R': 'world', 'loop': True},
    'Attack': {   # RELEASE 10, FRESH, LIGHT, cocked again by 33
        'R': path([(0, COCK), (3, (-0.60, 0.14, 1.48)), (6, (-0.64, 0.16, 1.40)), (9, (-0.56, 0.12, 1.84)), (12, (-0.58, -0.02, 1.72)),
                   (15, (-0.50, -0.08, 1.39)), (18, (-0.49, 0.05, 1.10)), (21, (-0.39, -0.10, 1.17)), (24, (-0.10, -0.52, 1.32)),
                   (27, (-0.18, -0.44, 1.36)), (30, (-0.48, 0.05, 1.50)), (33, COCK)], hi=PRH),
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
    'Ability': {   # Powder Keg: K_RELEASE 45
        'R': path([(0, COCK), (3, (-0.53, -0.27, 1.38)), (6, (-0.48, 0.03, 1.04)), (9, (-0.32, -0.37, 0.99)), (12, (-0.27, -0.42, 0.94)),
                   (15, (-0.22, -0.40, 0.96)), (18, (-0.31, -0.42, 1.02)), (21, (-0.60, -0.14, 1.60)), (24, (-0.62, -0.05, 1.74)),
                   (27, (-0.60, -0.10, 1.71)), (30, (-0.17, -0.52, 1.40)), (33, (-0.16, -0.53, 1.38)), (36, (-0.20, -0.45, 1.63)),
                   (39, (-0.22, -0.44, 1.74)), (42, (-0.25, -0.40, 1.84)), (45, (-0.24, -0.34, 1.90)), (48, (-0.26, -0.52, 1.56)),
                   (51, (-0.32, -0.30, 1.36)), (54, (-0.48, 0.10, 1.70)), (57, (-0.48, 0.08, 1.03)), (60, (-0.20, -0.48, 1.30)),
                   (63, (-0.10, -0.52, 1.32)), (66, (-0.22, -0.40, 1.40)), (69, (-0.48, 0.10, 1.52)), (72, COCK)], hi=PRH),
        'L': path([(0, (0.48, -0.06, 1.46)), (3, (0.43, -0.08, 1.33)), (6, (0.36, -0.19, 1.20)), (9, (0.31, -0.32, 1.02)),
                   (12, (0.16, -0.40, 0.96)), (15, (0.12, -0.39, 0.97)), (18, (0.05, -0.39, 1.03)), (21, (0.16, -0.24, 1.30)),
                   (24, (0.41, 0.07, 1.09)), (27, (0.38, -0.12, 1.20)), (29, (0.26, -0.40, 1.30)), (30, (0.17, -0.50, 1.40)), (33, (0.18, -0.53, 1.38)),
                   (36, (0.18, -0.48, 1.57)), (39, (0.24, -0.40, 1.76)), (42, (0.24, -0.38, 1.82)), (45, (0.20, -0.30, 1.90)),
                   (48, (0.26, -0.50, 1.56)), (51, (0.30, -0.25, 1.39)), (54, (0.31, -0.19, 1.30)), (60, (0.32, -0.17, 1.29)),
                   (66, (0.35, -0.16, 1.33)), (69, (0.43, -0.11, 1.42)), (72, (0.48, -0.06, 1.46))], pole=PL),
        'hand_R': 'world', 'hand_L': 'world', 'hand_smooth': 1.0,
    },
}
