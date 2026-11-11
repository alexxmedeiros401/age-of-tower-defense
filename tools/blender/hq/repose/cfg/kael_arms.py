# Kael (Iron hero): the javelin arm released the throw from a fist in front of his face (Attack frame 3, Ability's
# skyward hurl), reached for the case on his back with the elbow up across his head, and Cheer's raised javelin went up
# over his crown. The fist now comes over OUT beside his head, follows through at his right, reaches back for the case
# with the elbow out to the side, and is raised out at his right; the javelin keeps its shipped orientation per frame.
import math
from mathutils import Vector as V
HERO = 'kael'
POISE = V((-0.51, 0.05, 1.49)); POISE_POLE = V((-0.95, 0.10, 1.30))
CASE = V((-0.44, 0.46, 1.78)); CASE_POLE = V((-1.00, 0.35, 1.90))
HIGH = V((-0.52, 0.02, 1.95)); HIGH_POLE = V((-1.00, 0.20, 1.70))
IDLE = V((-0.38, -0.05, 0.99)); IDLE_POLE = V((-0.80, 0.30, 1.10))

CLIPS = {
    'Attack': {   # RELEASE 3, FRESH 14
        'R': [(0, POISE, POISE_POLE), (3, V((-0.52, -0.20, 1.86)), V((-1.0, 0.0, 1.70))), (6, V((-0.48, -0.42, 1.45)), V((-0.95, -0.05, 1.35))),
              (9, V((-0.42, -0.40, 1.22)), V((-0.90, 0.05, 1.15))), (12, V((-0.55, 0.15, 1.50)), V((-1.0, 0.30, 1.55))),
              (15, CASE + V((0, -0.03, -0.10)), CASE_POLE), (18, CASE, CASE_POLE), (21, V((-0.50, 0.18, 1.72)), V((-1.0, 0.25, 1.65))),
              (24, POISE, POISE_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
    'Ability': {   # Javelin Storm: the hurl straight up at frame ~15 (A_RELEASE), fresh javelin from the case 42-48
        'R': [(0, POISE, POISE_POLE), (6, V((-0.50, -0.10, 1.44)), POISE_POLE), (12, V((-0.48, -0.20, 1.40)), POISE_POLE),
              (15, V((-0.50, -0.12, 2.00)), HIGH_POLE), (18, V((-0.48, -0.25, 1.75)), HIGH_POLE), (21, V((-0.40, -0.32, 1.53)), POISE_POLE),
              (27, V((-0.30, -0.32, 1.27)), V((-0.80, -0.05, 1.20))), (30, V((-0.30, -0.31, 1.17)), V((-0.80, -0.05, 1.15))),
              (36, V((-0.22, -0.35, 1.24)), V((-0.80, -0.05, 1.20))), (39, V((-0.45, -0.07, 1.48)), POISE_POLE),
              (42, CASE + V((0.02, -0.06, -0.18)), CASE_POLE), (45, CASE, CASE_POLE), (48, CASE + V((-0.02, -0.10, 0.03)), CASE_POLE),
              (51, V((-0.47, 0.10, 1.66)), POISE_POLE), (54, POISE, POISE_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
    'Cheer': {
        'R': [(0, IDLE, IDLE_POLE), (3, V((-0.46, 0.0, 1.40)), POISE_POLE), (6, HIGH + V((0, 0, -0.04)), HIGH_POLE), (9, HIGH, HIGH_POLE),
              (32, HIGH, HIGH_POLE), (35, V((-0.58, 0.04, 1.74)), POISE_POLE), (37, V((-0.52, 0.0, 1.40)), POISE_POLE), (40, IDLE, IDLE_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.0,
    },
    'Idle': {   # hefts the javelin and sights along it (63-96): the fist out at his shoulder, the shaft beside his head
        'R': [(0, IDLE, IDLE_POLE), (60, IDLE, IDLE_POLE), (63, V((-0.45, 0.02, 1.20)), V((-0.90, 0.30, 1.20))),
              (67, V((-0.52, 0.10, 1.42)), V((-0.95, 0.25, 1.30))), (70, V((-0.52, 0.14, 1.46)), V((-0.95, 0.25, 1.30))),
              (90, V((-0.52, 0.13, 1.46)), V((-0.95, 0.25, 1.30))), (93, V((-0.48, 0.02, 1.30)), V((-0.90, 0.30, 1.20))),
              (96, V((-0.42, 0.0, 1.10)), IDLE_POLE), (99, IDLE, IDLE_POLE), (120, IDLE, IDLE_POLE)],
        'hand_R': 'world', 'hand_smooth': 1.0, 'loop': True,
    },
}
