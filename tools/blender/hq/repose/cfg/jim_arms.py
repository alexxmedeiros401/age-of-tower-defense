# Big Jim (Industrial hero): after the valve slam (Ability 24-44) he "leans on the maul" with his right fist on top of
# its handle INSIDE his beard (16-22 cm, the fist at his chin); both fists (the maul is in his right, his left on the
# handle) are moved together forward and down so the fist rests in front of the beard and the left hand stays on the
# handle. The overhead raise (Ability 15-24, Cheer) is lifted forward off his cap with the same shared offset.
# Combat/Attack (the maul carried over his right shoulder, left fist at the front of his beard) kept: the left arm is at
# full reach across his body there, so the two-handed grip cannot move further out.
from mathutils import Vector as V
HERO = 'jim'

def ramp(f, pts):
    for (a, wa), (b, wb) in zip(pts, pts[1:]):
        if a <= f <= b:
            t = (f - a) / float(b - a); t = t * t * (3 - 2 * t); return wa + (wb - wa) * t
    return pts[-1][1] if f > pts[-1][0] else pts[0][1]
PR = V((-0.90, 0.10, 1.15)); PL = V((0.90, 0.10, 1.15)); PRH = V((-1.00, 0.10, 1.70)); PLH = V((1.00, 0.10, 1.70))
from mathutils import Matrix
def tilt(r, l, deg):
    # turn both fists about the maul's head (resting on the valve) so its handle leans forward, away from his face
    r = V(r); l = V(l); u = (l - r).normalized(); M = l + u * 0.6
    v = r - M; ax = v.cross(V((0, -1, 0))).normalized(); Rm = Matrix.Rotation(__import__('math').radians(deg), 3, ax)
    return M + Rm @ (r - M), M + Rm @ (l - M)
def both(keys, side):
    out = []
    for f, r, l, d in keys:
        if isinstance(d, (int, float)):
            r, l = tilt(r, l, d); d = (0, 0, 0)
        w = V(r if side == 'R' else l) + V(d)
        hi = w.z > 1.62
        out.append((f, w, (PRH if hi else PR) if side == 'R' else (PLH if hi else PL)))
    return out
Z = (0, 0, 0); LEAN = 14.0     # deg: the leaning maul tilted forward about its head
AB = [(0, (-0.10, -0.38, 1.12), (-0.09, -0.26, 1.38), Z), (9, (-0.10, -0.39, 1.08), (-0.09, -0.30, 1.35), Z),
      (12, (-0.11, -0.43, 1.22), (-0.08, -0.31, 1.47), Z), (15, (-0.12, -0.50, 1.41), (-0.05, -0.34, 1.62), (0, -0.04, 0)),
      (18, (-0.14, -0.51, 1.53), (-0.01, -0.33, 1.69), (0, -0.06, 0)), (21, (-0.13, -0.47, 1.62), (0.03, -0.30, 1.75), (0, -0.06, 0)),
      (24, (-0.08, -0.23, 1.63), (0.10, -0.47, 1.59), (0, -0.06, -0.03)), (27, (-0.03, -0.15, 1.49), (0.09, -0.35, 1.24), LEAN),
      (30, (-0.03, -0.16, 1.47), (0.09, -0.36, 1.23), LEAN), (36, (-0.03, -0.15, 1.48), (0.09, -0.35, 1.24), LEAN),
      (39, (-0.05, -0.17, 1.49), (0.10, -0.42, 1.34), LEAN), (42, (-0.09, -0.22, 1.45), (0.06, -0.45, 1.57), (-0.04, -0.14, -0.08)),
      (45, (-0.12, -0.30, 1.28), (-0.06, -0.38, 1.54), (0, -0.04, 0)), (48, (-0.11, -0.37, 1.09), (-0.09, -0.33, 1.37), Z),
      (54, (-0.10, -0.39, 1.06), (-0.09, -0.31, 1.33), Z), (60, (-0.10, -0.38, 1.10), (-0.09, -0.28, 1.36), Z),
      (66, (-0.10, -0.38, 1.12), (-0.09, -0.26, 1.38), Z)]
CLIPS = {
    'Ability': {'R': both(AB, 'R'), 'L': both(AB, 'L'), 'hand_R': 'world', 'hand_L': 'world', 'hand_smooth': 1.0},
}

# Pass 2 (p2H): a new carry stance. In Combat (and where Attack, Ability and Cheer start and end in it) his left hand
# held the handle up at his chin, the fist 5-7 cm into his beard. It now slides 13 cm down the handle toward the right
# fist (the handle line, chest-relative), so the left fist rides at his chest below the beard; the maul, the right fist
# and the swing are unchanged. Cheer: on the way up and down (3-6, 42-45) the raised maul crossed his face from the
# front-right, and the Attack's wind-up (1-6) brought the left forearm across his mouth: both fists go up 11 cm further out at his right and 3 cm further forward (the left arm is at full reach there).
SLIDE = V((0.0, -0.055, -0.118))          # 13 cm down the handle (left wrist -> right wrist direction in Combat)
def _ease(f, pts): return V(SLIDE) * ramp(f, pts)
OUT = V((-0.11, -0.03, 0.0))
def _cheer_out(f): return OUT * ramp(f, [(1, 0.0), (4, 1.0), (6, 1.0), (9, 0.0)]) if f < 20 else OUT * ramp(f, [(39, 0.0), (42, 1.0), (44, 1.0), (47, 0.0)])
CLIPS['Combat'] = {'L': {'offset': lambda f: V(SLIDE)}, 'hand_L': 'world', 'loop': True}
OUT2 = V((-0.12, -0.05, -0.12))
def _atk_out(f): return OUT2 * ramp(f, [(0, 0.0), (2, 1.0), (5, 1.0), (7, 0.0)])
CLIPS['Attack'] = {'L': {'offset': lambda f: _ease(f, [(0, 1.0), (5, 1.0), (8, 0.0), (11, 0.0), (14, 1.0)]) + _atk_out(f)},
                   'R': {'offset': _atk_out}, 'hand_L': 'world', 'hand_R': 'world'}
CLIPS['Cheer'] = {'L': {'offset': lambda f: _ease(f, [(0, 1.0), (3, 0.0), (45, 0.0), (48, 1.0)]) + _cheer_out(f)},
                  'R': {'offset': _cheer_out}, 'hand_L': 'world', 'hand_R': 'world'}
_ab = []
for f, r, l, d in AB:
    if f in (0, 9, 48, 54, 60, 66) or (f == 12):
        k = 1.0 if f != 12 else 0.5
        l = tuple(V(l) + V(SLIDE) * k)
    _ab.append((f, r, l, d))
CLIPS['Ability'] = {'R': both(_ab, 'R'), 'L': both(_ab, 'L'), 'hand_R': 'world', 'hand_L': 'world', 'hand_smooth': 1.0}
