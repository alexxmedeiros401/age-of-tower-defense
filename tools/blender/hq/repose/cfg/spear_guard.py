# Spear Guard: overhand spear held by the ear with the butt running back through the long crest hair, the thrust
# drove the hand across in front of the face (hand at the chin centre) with the wrist bent ~180 deg (the spear sits in
# the fist pointing along the palm side, so a forearm pointing up aims it backwards). The shield rim pressed into the
# chest during the thrust. Re-authored as a hoplite overhand: elbow raised out at the side, forearm hanging from it,
# hand at shoulder height out beside the helmet (the shaft passes outside the hair), the thrust drives forward in front
# of the right shoulder (not the face); the shield braces forward (its facing kept).
import math
from mathutils import Vector as V
AXIS = {'R': V((-0.011, -0.985, 0.17)), 'L': V((0.554, -0.18, -0.813))}   # spear (to the tip), shield normal
AXIS2 = {'L': V((-0.706, -0.619, -0.344))}
SH = {'dir': V((0.516, -0.834, 0.195)), 'up': V((-0.718, -0.298, 0.629))}  # shipped shield facing (ready)
SH2 = {'dir': V((0.40, -0.89, 0.22)), 'up': V((-0.75, -0.15, 0.63))}
READY_R = V((-0.52, -0.08, 1.42)); EL_UP = V((-0.6, 0.2, 0.75)); EL_TH = V((-0.8, 0.4, 0.45)); SPEAR = V((0.14, -0.98, -0.10))
READY_L = V((0.36, -0.24, 1.16))
ATK_R = [
    (0,  READY_R,                  {'dir': SPEAR, 'pole': EL_UP}),
    (3,  V((-0.54, 0.02, 1.46)),   {'dir': V((0.12, -0.98, -0.06)), 'pole': EL_UP}),   # draw back
    (6,  V((-0.47, -0.40, 1.38)),  {'dir': V((0.18, -0.98, 0.02)), 'pole': EL_TH, 'aim': 0.8}),   # thrust (level), in front of the right shoulder
    (12, V((-0.47, -0.39, 1.38)),  {'dir': V((0.18, -0.98, 0.02)), 'pole': EL_TH, 'aim': 0.8}),
    (20, V((-0.52, -0.22, 1.41)),  {'dir': V((0.15, -0.98, -0.05)), 'pole': EL_UP, 'aim': 0.85}),
    (30, READY_R,                  {'dir': SPEAR, 'pole': EL_UP}),
]
ATK_L = [
    (0,  READY_L,                  SH),
    (6,  V((0.38, -0.30, 1.18)),   SH2),    # brace forward with the thrust
    (14, V((0.38, -0.29, 1.18)),   SH2),
    (30, READY_L,                  SH),
]
def loop(base, amp, n, o, ph=0.0):
    def k(f):
        a = 2 * math.pi * f / n + ph
        return base + V((0, amp[0] * math.sin(a), amp[1] * math.sin(a))), o
    return k
CLIPS = {
    'Attack': {'R': ATK_R, 'L': ATK_L},
    'Combat': {'R': loop(READY_R, (0.01, 0.015), 40, {'dir': SPEAR, 'pole': EL_UP}), 'L': loop(READY_L, (0.0, 0.012), 40, SH, 0.8)},
}
WFIT = 0.4

# Pass 2 (p2H): the thrust held the spear exactly level with the wrist bent 74-78 deg for frames 5-23 (above the ~65 deg
# guideline). The thrust keys now aim the spear at 0.8 (the recovery at 0.85): the wrist eases toward straight and the
# spear tilts ~15 deg up through the thrust; wrist <= 66 deg.
