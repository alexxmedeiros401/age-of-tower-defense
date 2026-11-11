# Wren (Medieval hero): the longbow's string hand was drawn to the middle of her chin (Combat, the end of the Attack,
# the Ability's three draws: the fist and the arrow's nock 10 cm into her face), and the Cheer's raised bow went up from a
# fist over her crown with the left forearm across her face. The draw now comes to beside and in front of her right jaw
# (the arrow under her eye, 6+ cm off the face), the string (both halves) and the arrow follow the drawing hand, and
# the Cheer raises the bow out at her left.
import math
from mathutils import Vector as V
HERO = 'wren'
import os
WRL = float(os.environ.get('WRL', '-60'))   # the raised bow turned upright beside her head
AXIS_R = (-0.002, -0.984, 0.18)          # the arrow, nock -> tip (rest)
DRAW = V((-0.20, -0.30, 1.42)); DRAW_POLE = V((-0.65, 0.05, 1.60))
REST_R = V((-0.12, -0.24, 0.98)); REST_POLE = V((-0.70, 0.20, 1.05))
ARROW = {'axis': AXIS_R, 'at': 'hand.L', 'offset': (0, 0.06, 0), 'w': 'auto'}
STRING = {'string_top': 'R', 'string_bot': 'R'}
def shifted(keys):
    # the shipped wrist path, its drawn end moved from the chin to DRAW (by how near it was to the chin)
    chin = V((-0.03, -0.15, 1.51)); out = []
    for f, w in keys:
        w = V(w); k = max(0.0, 1.0 - (w - chin).length / 0.25)
        w = w + (DRAW - chin) * k
        k2 = max(0.0, min(1.0, (w.x + 0.12) / 0.2))      # crossing over to the bow: in front of her chest, not her face
        out.append((f, w + V((0, -0.16, -0.28)) * k2, DRAW_POLE))
    return out
CLIPS = {
    'Combat': {'R': lambda f: (DRAW + V((0, 0, 0.006 * math.sin(2 * math.pi * f / 40))), DRAW_POLE), 'hand_R': 'world', 'loop': True,
               'aim_fix_R': ARROW, 'follow_tail': STRING},
    'Attack': {   # RELEASE 1, the string hand flung back past her ear, down to the quiver, GRAB, NOCK, drawn by 18
        'R': shifted([(0, (-0.03, -0.15, 1.51)), (3, (-0.16, -0.14, 1.49)), (6, (-0.26, -0.36, 1.34)), (9, (-0.17, -0.49, 1.50)),
                      (12, (0.20, -0.25, 1.42)), (15, (0.11, -0.22, 1.47)), (18, (-0.03, -0.15, 1.51))]),
        'hand_R': 'world', 'hand_smooth': 1.0, 'aim_fix_R': ARROW, 'follow_tail': STRING,
    },
    'Ability': {   # Arrow Rain: three draws to the jaw with the bow raised
        'R': shifted([(0, (-0.03, -0.15, 1.51)), (3, (-0.03, -0.15, 1.49)), (6, (-0.01, -0.16, 1.44)), (9, (-0.03, -0.19, 1.37)),
                      (12, (-0.18, -0.22, 1.31)), (15, (-0.21, -0.41, 1.25)), (18, (-0.09, -0.48, 1.50)), (21, (0.09, -0.22, 1.47)),
                      (24, (-0.01, -0.17, 1.43)), (27, (-0.05, -0.19, 1.33)), (30, (-0.27, -0.37, 1.31)), (33, (-0.17, -0.50, 1.49)),
                      (36, (0.11, -0.23, 1.48)), (39, (0.01, -0.18, 1.44)), (42, (-0.04, -0.19, 1.35)), (45, (-0.33, -0.29, 1.34)),
                      (48, (-0.17, -0.51, 1.40)), (51, (0.10, -0.37, 1.47)), (54, (0.10, -0.21, 1.47)), (57, (-0.03, -0.15, 1.51)),
                      (62, (-0.03, -0.15, 1.51))]),
        'hand_R': 'world', 'hand_smooth': 1.0, 'aim_fix_R': ARROW, 'follow_tail': STRING,
        # the raised bow out to her left (its grip was in front of her brow)
        'L': [(f, V(w) + V((0.14, 0.04, -0.02)) * k, V((0.95, 0.10, 1.55))) for f, w, k in [
              (0, (0.70, -0.34, 1.47), 0), (3, (0.65, -0.31, 1.64), 0.3), (6, (0.48, -0.24, 1.84), 1), (9, (0.41, -0.22, 1.88), 1),
              (12, (0.40, -0.22, 1.85), 1), (15, (0.31, -0.18, 1.71), 1), (18, (0.24, -0.16, 1.59), 1), (21, (0.27, -0.17, 1.64), 1),
              (24, (0.42, -0.22, 1.88), 1), (27, (0.42, -0.22, 1.88), 1), (30, (0.33, -0.19, 1.73), 1), (33, (0.24, -0.16, 1.59), 1),
              (36, (0.24, -0.16, 1.59), 1), (39, (0.39, -0.21, 1.83), 1), (42, (0.41, -0.22, 1.89), 1), (45, (0.38, -0.21, 1.78), 1),
              (48, (0.35, -0.19, 1.62), 1), (51, (0.37, -0.20, 1.52), 0.7), (54, (0.55, -0.28, 1.49), 0.3), (57, (0.70, -0.34, 1.47), 0),
              (62, (0.70, -0.34, 1.47), 0)]],
        'hand_L': 'world', 'blend_L': (2, 2),
    },
    'Cheer': {   # the bow thrust up out at her left (it went up over her crown)
        'L': [(0, V((0.30, 0.04, 0.93)), V((0.80, 0.30, 1.05))), (3, V((0.40, 0.04, 1.42)), V((0.90, 0.20, 1.40))),
              (6, V((0.52, -0.02, 1.92)), V((0.95, 0.15, 1.65))), (33, V((0.52, -0.02, 1.92)), V((0.95, 0.15, 1.65))),
              (36, V((0.40, 0.05, 1.40)), V((0.90, 0.20, 1.40))), (40, V((0.30, 0.04, 0.93)), V((0.80, 0.30, 1.05)))],
        'hand_L': 'world', 'world_rot_L': lambda f: ((0, 1, 0), WRL * min(1.0, max(0.0, min(f - 2, 36 - f) / 4.0))),
    },
}
