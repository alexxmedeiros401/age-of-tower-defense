# Dr. Ken Ito (Modern hero): arming the EMP grenade (Ability 18-34) brought the gauntlet fist up to the tablet held
# before his face, the fist 16 cm into his chin/face; the cock-and-lob (34-46) went over the brim of his helmet; the
# Cheer's punches went up from a fist on the brim. Both arms are moved together (offsets on the shipped paths) for the
# arming, so the grenade still touches the tablet, now in front of his chest; the lob and the cheer go up out at his
# right. Fists keep their shipped orientation; the grenade keeps its grip. Combat/Attack/Idle kept.
from mathutils import Vector as V
HERO = 'ken'
HOLD_PROPS = ['grenade']
def ramp(f, pts):
    for (a, wa), (b, wb) in zip(pts, pts[1:]):
        if a <= f <= b:
            t = (f - a) / float(b - a); t = t * t * (3 - 2 * t); return wa + (wb - wa) * t
    return pts[-1][1] if f > pts[-1][0] else pts[0][1]
ARM = V((0.0, -0.12, -0.16)); OUT = V((-0.20, 0.02, 0.0))
def ab(f):
    return ARM * ramp(f, [(0, 0), (15, 0), (21, 1), (31, 1), (35, 0)]) + OUT * ramp(f, [(0, 0), (33, 0), (37, 1), (44, 1), (49, 0)]) + V((-0.04, -0.16, -0.30)) * ramp(f, [(0, 0), (29, 0), (33, 1), (37, 0)])
CLIPS = {
    'Ability': {'R': [(f, V(w), V((-0.90, 0.10, 1.20)) if w[2] < 1.5 else V((-1.0, 0.20, 1.60))) for f, w in [
                    (0, (-0.36, -0.01, 1.30)), (6, (-0.36, -0.03, 1.30)), (9, (-0.38, -0.12, 1.38)), (12, (-0.28, -0.14, 1.18)),
                    (15, (-0.20, -0.17, 1.12)), (18, (-0.12, -0.24, 1.18)), (21, (0.00, -0.30, 1.26)), (24, (0.08, -0.31, 1.30)),
                    (30, (0.08, -0.31, 1.30)), (33, (-0.18, -0.36, 1.22)), (37, (-0.50, 0.06, 1.52)), (40, (-0.54, 0.10, 1.56)),
                    (43, (-0.50, -0.18, 1.74)), (46, (-0.40, -0.32, 1.46)), (49, (-0.24, -0.32, 1.24)), (51, (-0.20, -0.34, 1.16)),
                    (54, (-0.23, -0.29, 1.17)), (57, (-0.27, -0.20, 1.20)), (60, (-0.32, -0.10, 1.25)), (63, (-0.35, -0.03, 1.29)),
                    (66, (-0.36, -0.01, 1.30))]], 'L': {'offset': lambda f: ARM * ramp(f, [(0, 0), (15, 0), (21, 1), (31, 1), (35, 0)])},
                'hand_R': 'world', 'hand_L': 'world', 'hand_smooth': 1.0},
    'Cheer': {'R': {'offset': lambda f: OUT * ramp(f, [(0, 0), (3, 0.5), (6, 1), (42, 1), (45, 0.5), (48, 0)])}, 'hand_R': 'world'},
}
