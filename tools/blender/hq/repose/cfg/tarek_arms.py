# Tarek (Bronze hero): the hammer arm kept its fist against the side of his head (Combat's cocked hammer), whipped
# across his face (Attack), raised the hammer straight up over his head with the forearm across his face (Ability,
# Cheer), and Idle's brow wipe drove his left forearm through his forehead. The hammer hand now cocks and rises OUT
# beside his head, the throw comes over at his right, the strikes come down at the anvil from the side, and the wipe
# is the back of his left hand at his left temple. The hammer keeps its shipped orientation in every frame ('world').
import math
from mathutils import Vector as V
HERO = 'tarek'
COCK = V((-0.50, 0.12, 1.70)); COCK_POLE = V((-0.95, 0.25, 1.45))
HIGH = V((-0.50, 0.05, 1.90)); HIGH_POLE = V((-0.95, 0.20, 1.65))
IDLE = V((-0.24, -0.18, 1.20)); IDLE_POLE = V((-0.75, -0.10, 1.00))
STRIKE = V((-0.18, -0.32, 1.28)); STRIKE_POLE = V((-0.80, -0.05, 1.20))

def combat_r(f, n=40):
    return COCK + V((0, 0, 0.012 * math.sin(2 * math.pi * f / n))), COCK_POLE
def idle_r(f, n=120):
    return IDLE + V((0, 0, 0.006 * math.sin(2 * math.pi * f / n))), IDLE_POLE

L_REST = V((0.34, 0.03, 1.00)); L_POLE = V((0.85, 0.30, 1.05))
CLIPS = {
    'Combat': {'R': combat_r, 'hand_R': 'world', 'loop': True, 'wrist_max': 180},
    'Attack': {   # release at frame 2 (game.gd RELEASE)
        'R': [(0, COCK, COCK_POLE), (2, V((-0.56, -0.20, 1.90)), V((-1.0, 0.10, 1.65))),
              (5, V((-0.44, -0.45, 1.36)), V((-0.90, -0.05, 1.30))), (8, V((-0.40, -0.36, 1.06)), V((-0.85, 0.05, 1.10))),
              (12, V((-0.46, -0.08, 0.98)), V((-0.85, 0.25, 1.05))), (15, V((-0.52, -0.02, 1.20)), V((-0.90, 0.30, 1.15))),
              (18, V((-0.54, 0.10, 1.50)), V((-0.95, 0.30, 1.35))), (22, COCK, COCK_POLE)],
        'hand_R': 'world', 'hand_smooth': 2.0,
    },
    'Ability': {   # Forge Fury: three strikes on the anvil in front, then the hammer raised and a roar
        'R': [(0, V((0.01, -0.19, 1.38)), STRIKE_POLE), (4, V((-0.42, -0.05, 1.62)), HIGH_POLE), (8, HIGH, HIGH_POLE),
              (12, STRIKE, STRIKE_POLE), (15, V((-0.48, 0.12, 1.64)), COCK_POLE), (18, V((-0.48, 0.12, 1.64)), COCK_POLE),
              (21, STRIKE, STRIKE_POLE), (24, STRIKE, STRIKE_POLE), (28, HIGH, HIGH_POLE), (32, HIGH + V((0, 0, 0.03)), HIGH_POLE),
              (36, STRIKE, STRIKE_POLE), (42, STRIKE, STRIKE_POLE), (47, V((-0.46, 0.10, 1.70)), HIGH_POLE),
              (51, HIGH + V((0.02, 0, 0.05)), HIGH_POLE), (57, HIGH + V((0.02, 0, 0.05)), HIGH_POLE), (62, V((-0.50, 0.08, 1.80)), HIGH_POLE),
              (66, COCK, COCK_POLE)],
        'hand_R': 'world', 'wrist_max': 180, 'blend_R': (3, 0),
    },
    'Cheer': {   # the hammer thrust up beside his head twice
        'R': [(0, IDLE, IDLE_POLE), (6, HIGH + V((0, 0, 0.04)), HIGH_POLE), (12, HIGH, HIGH_POLE), (18, HIGH + V((0, 0, 0.04)), HIGH_POLE),
              (24, HIGH + V((0, 0, 0.04)), HIGH_POLE), (30, HIGH, HIGH_POLE), (33, HIGH + V((0, 0, 0.03)), HIGH_POLE), (40, IDLE, IDLE_POLE)],
        'hand_R': 'world', 'wrist_max': 180,
    },
    'Idle': {
        'R': idle_r, 'hand_R': 'world', 'wrist_max': 180, 'loop': True,
        'L': [(0, L_REST, L_POLE), (66, L_REST, L_POLE), (71, V((0.36, -0.22, 1.50)), V((0.80, -0.10, 1.30))),
              (75, V((0.30, -0.33, 1.78)), V((0.75, -0.25, 1.55))), (81, V((0.24, -0.38, 1.80)), V((0.75, -0.30, 1.55))),
              (87, V((0.31, -0.33, 1.76)), V((0.75, -0.25, 1.55))), (92, V((0.36, -0.20, 1.45)), V((0.80, -0.10, 1.30))),
              (97, L_REST, L_POLE), (120, L_REST, L_POLE)],
        'hand_L': 'world', 'wrist_max_L': 180,
    },
}
