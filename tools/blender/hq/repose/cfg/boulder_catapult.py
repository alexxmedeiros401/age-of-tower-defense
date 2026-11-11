# Boulder Catapult crew: the arms work the machine without clipping, except Idle frames ~30-75 where the left hand
# wiped her brow by sweeping across the face (into the chin/fringe). Re-authored that gesture only: the hand comes up
# the outside to the temple, wipes outward beside the head and returns to the hip. Rest of the motion: shipped.
# (The catapult beam swinging back past her face in Attack ~f20-28 is the machine, not her arms: left as is.)
from mathutils import Vector as V
HIP = V((0.27, -0.03, 0.853))
IDLE_L = [
    (24, V((0.263, -0.039, 0.854)), {}),
    (32, V((0.32, -0.12, 0.98)), {}),
    (40, V((0.38, -0.25, 1.28)), {}),
    (48, V((0.36, -0.20, 1.54)), {}),     # up at the temple, out beside the hair
    (56, V((0.41, -0.27, 1.50)), {}),     # wipe outward
    (62, V((0.42, -0.22, 1.36)), {}),
    (70, V((0.33, -0.08, 1.05)), {}),
    (78, V((0.272, 0.03, 0.85)), {}),
]
CLIPS = {'Idle': {'L': IDLE_L}}
WINDOW = {'Idle': {'L': (30, 74, 6)}}
