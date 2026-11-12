# Ada (Industrial hero): the spanner was thrust overhead from a gauntlet fist against her forehead (Ability 33-48) and
# twirled just under her chin (21-30); the Cheer swung the launcher up over her head with both fists at her hair line,
# passing it across her face on the way up and down. The spanner fist now goes up out at her right and twirls lower in
# front; the Cheer's launcher is held up and forward of her head (both hands moved together, so the two-handed grip
# holds) and comes up/down in front of her chest. Fists keep their shipped orientation; the props keep their grip.
from mathutils import Vector as V
HERO = 'ada'
HOLD_PROPS = ['wrench', 'launcher']
PR = V((-0.90, 0.20, 1.15)); PRH = V((-1.00, 0.15, 1.70)); PL = V((0.90, 0.20, 1.15)); PLH = V((1.00, 0.15, 1.70))
def path(keys, pole, hi):
    return [(f, V(w), hi if w[2] > 1.62 else pole) for f, w in keys]
def both(keys, side):
    # keys: (f, R wrist, L wrist, delta) -> one side's keys with the shared delta
    return [(f, V(r if side == 'R' else l) + V(d), (PRH if side == 'R' else PLH) if (r if side == 'R' else l)[2] > 1.62 else (PR if side == 'R' else PL))
            for f, r, l, d in keys]
UP = (0.0, 0.0, 0.0)
CH = [(0, (-0.10, -0.28, 1.11), (0.31, -0.38, 1.00), UP), (3, (-0.16, -0.43, 1.29), (0.21, -0.43, 1.34), (0, -0.06, -0.03)),
      (6, (-0.22, -0.35, 1.47), (0.21, -0.34, 1.59), (-0.22, -0.14, -0.22)),
      (7, (-0.22, -0.35, 1.47), (0.21, -0.34, 1.59), (-0.24, -0.18, -0.16)),
      (8, (-0.24, 0.04, 1.94), (0.26, -0.06, 1.92), (-0.16, 0.02, -0.08)), (9, (-0.24, 0.04, 1.94), (0.26, -0.06, 1.92), (-0.16, 0.02, -0.08)),
      (12, (-0.20, 0.08, 1.94), (0.26, -0.01, 1.93), (-0.16, 0.02, -0.08)), (21, (-0.20, 0.07, 1.94), (0.26, -0.02, 1.93), (-0.16, 0.02, -0.08)),
      (33, (-0.20, 0.09, 1.94), (0.26, -0.01, 1.93), (-0.16, 0.02, -0.08)), (34, (-0.20, 0.09, 1.94), (0.26, -0.01, 1.93), (-0.16, 0.02, -0.08)),
      (35, (-0.25, -0.25, 1.65), (0.23, -0.25, 1.73), (-0.24, -0.18, -0.30)),
      (36, (-0.25, -0.25, 1.65), (0.23, -0.25, 1.73), (-0.22, -0.14, -0.22)),
      (39, (-0.19, -0.46, 1.31), (0.18, -0.44, 1.44), (0, -0.06, -0.03)), (42, (-0.16, -0.36, 1.21), (0.33, -0.37, 1.30), UP),
      (45, (-0.10, -0.28, 1.11), (0.31, -0.38, 1.00), UP), (48, (-0.10, -0.28, 1.11), (0.31, -0.38, 1.00), UP)]
CLIPS = {
    'Ability': {   # Overdrive: SIGNAL 36-46 (the spanner high)
        'R': path([(0, (-0.10, -0.28, 1.11)), (3, (-0.11, -0.36, 1.02)), (6, (-0.10, -0.35, 1.08)), (9, (-0.28, -0.00, 0.95)),
                   (12, (-0.43, 0.06, 0.89)), (15, (-0.41, 0.08, 0.99)), (18, (-0.34, -0.10, 1.12)), (21, (-0.26, -0.42, 1.26)),
                   (24, (-0.27, -0.43, 1.29)), (27, (-0.27, -0.43, 1.29)), (30, (-0.26, -0.42, 1.26)), (33, (-0.46, -0.20, 1.72)),
                   (36, (-0.55, 0.00, 1.92)), (45, (-0.55, 0.00, 1.92)), (48, (-0.40, -0.32, 1.50)), (51, (-0.33, -0.04, 1.10)),
                   (54, (-0.42, 0.05, 0.94)), (57, (-0.32, 0.00, 0.93)), (60, (-0.13, -0.38, 1.03)), (63, (-0.16, -0.34, 1.02)),
                   (66, (-0.10, -0.28, 1.11)), (68, (-0.10, -0.28, 1.11))], PR, PRH),
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
    'Cheer': {'R': both(CH, 'R'), 'L': both(CH, 'L'), 'hand_R': 'world', 'hand_L': 'world', 'hand_smooth': 1.5},
}

# Pass 2 (p2H): on the way up and down (Cheer 6-7, 35-36) the launcher's barrel crossed her chin; both hands now swing
# it up and down 12 cm further out at her right and 4 cm further forward, past her right shoulder, and the swing
# between chest and overhead is a toss: below her chin at 7 and 35, overhead at 8 and 34 (the launcher never shows
# across her face).
