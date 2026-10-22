"""Halberdier clips (game: 24 fps):
- Idle: the halberd upright at his right side, its butt on the ground, his right fist round the shaft at his chest, his
  left fist on his hip; he breathes, looks about, sways a little on his feet.
- Combat: the halberd levelled in both hands, braced: left foot forward, knees bent, his right fist by his right hip near
  the butt, his left fist forward on the shaft, the top spike toward the robots, the axe blade out to his right; a slow
  bob.
- Attack (24 frames, the 1.0 s cooldown): he winds up (0-4), heaving the halberd up beside his right shoulder, its head
  high over him, the edge turned to the robots, his left hand sliding down the shaft to his right; then he brings the axe
  blade down and across in a great chop (4-9), the edge leading, his left foot stamping, the blade through the robots
  before him at HIT (frame 9: game.gd's cleave sits at the blade's middle); he follows through low on his left (9-13)
  and swings it back up into the guard (13-24).

The halberd rides its own bone (`halberd`, no parent): every frame it is posed in world space ("world" aim) and both
fists are closed on its shaft where the clip puts them (in the guard his right fist at the butt; through the chop his
hands slide up the shaft and back), each wrist kept straight (its fingers along the line from its shoulder)."""
import math
from mathutils import Vector, Quaternion, Matrix
import halberdier as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
_O, _A, _B, _W = cm.hb_frame()
O_REST, A_REST, B_REST = vec(_O), vec(_A), vec(_B)
T_REST, F_REST, FIST_OFF = {}, {}, {}
for _s in ("R", "L"):
    _wr, _f, _n, _t = cm.hand_frame(_s)
    T_REST[_s], F_REST[_s] = vec(_t), vec(_f)
    FIST_OFF[_s] = vec(cm.fist_center(_s) - _wr)
HIT = 9               # the blade through the robots (game.gd ATTACK_FRAME)
FR = 24
RIGHT_S = 0.095       # his right fist on the shaft, this far from the butt (Combat and Attack)
IDLE_S = 1.12         # ... in the Idle (the butt on the ground, his fist at his chest)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    """A rest-pose body point carried by the root offset and turn (no spine bend)."""
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def _ortho(b, a):
    b = Vector(b) - Vector(a) * Vector(b).dot(Vector(a))
    return b.normalized() if b.length > 1e-5 else Vector(a).orthogonal().normalized()


def mixd(a, b, k):
    a, b = Vector(a).normalized(), Vector(b).normalized()
    if a.dot(b) > -0.98:
        return a.slerp(b, k).normalized()
    return a.lerp(b, k).normalized()


# ---------------------------------------------------------------------------------------------- the halberd, the fists
class Halberd:
    """The halberd's pose: butt O, shaft direction A (butt -> head), the blade's side B (square to A)."""

    def __init__(self, O, A, B):
        self.A = Vector(A).normalized()
        self.B = _ortho(B, self.A)
        self.O = Vector(O)

    @classmethod
    def from_grip(cls, g, A, B, s=RIGHT_S):
        A = Vector(A).normalized()
        return cls(Vector(g) - A * s, A, B)

    def pt(self, s, b=0.0):
        return self.O + self.A * s + self.B * b

    def aim(self, rest_m):
        """The bone's armature-space matrix ("world" aim)."""
        R = frame_map(A_REST, self.A, B_REST, self.B)
        X = Matrix.Translation(self.O) @ R.to_4x4() @ Matrix.Translation(-O_REST)
        return ("world", X @ rest_m)


def fist_on(arm, side, g, ax, sh, pole):
    """Fist `side` closed on the shaft at g, its thumb toward the head (ax), its fingers' direction along the line from
    its shoulder sh to g, square to the shaft (a straight wrist)."""
    ax = Vector(ax).normalized()
    fl = _ortho(Vector(g) - Vector(sh), ax)
    R = frame_map(T_REST[side], ax, F_REST[side], fl)
    aims = arm_aims(arm, side, Vector(g) - R @ FIST_OFF[side], pole=pole)
    aims["hand." + side] = ("frame", T_REST[side], ax, F_REST[side], fl)
    return aims


def both_hands(arm, hb, s_l, ro, yaw, pole_r, pole_l, s_r=RIGHT_S):
    aims = fist_on(arm, "R", hb.pt(s_r), hb.A, body_pt(J["shoulder_R"], ro, yaw), pole_r)
    aims.update(fist_on(arm, "L", hb.pt(s_l), hb.A, body_pt(J["shoulder_L"], ro, yaw), pole_l))
    return aims


# ---------------------------------------------------------------------------------------------- body
def feet(arm, yaw, lf=(0.22, -0.04), rf=(-0.22, 0.06), lift=(0.0, 0.0), turn=(10.0, -10.0)):
    """Ankles at the body-frame (x, y) lf / rf, turned with the hips by yaw; `turn` opens the feet (degrees)."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by), up, tw in (("L", lf, lift[0], turn[0]), ("R", rf, lift[1], turn[1])):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + up)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw + tw) @ (rest_foot + V(0, 0, -up * 0.6))
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0, reach=(0.0, 0.0)):
    """Spine and chest bent forward by `bend` radians and to his left by `side`, the chest turned `chest` degrees more;
    the head to the world heading `look` (degrees, 0 = the robots), pitched up by `pitch`; `reach` (left, right) brings
    each shoulder forward (the clavicle swung toward the front)."""
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(math.sin(roll) * 0.5, -0.12 - 0.2 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.04 + 0.6 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.03 - reach[0], 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.03 - reach[1], 0.02)


# ---------------------------------------------------------------------------------------------- idle
IDLE_BUTT = V(-0.5, -0.25, 0.0)
IDLE_HIP = V(0.375, 0.035, 0.985)            # his left wrist on his hip (akimbo)


def idle_state(t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = 2.5 * sway
    ro = V(0.006 * sway, 0.0, -0.012 + 0.005 * br)
    A = V(-0.05 - 0.008 * sway, -0.025, 1.0).normalized()
    hb = Halberd(IDLE_BUTT, A, V(-1.0, -0.12, 0.0))
    return w, br, sway, yaw, ro, hb


def idle_pose(arm, t, rest_m):
    w, br, sway, yaw, ro, hb = idle_state(t)
    aims = feet(arm, 0.0, lf=(0.22, -0.02), rf=(-0.22, 0.05), turn=(14.0, -12.0))
    look = 26.0 * math.sin(w + 0.4) + 8.0 * math.sin(w * 3)
    torso(aims, yaw, bend=-0.03, side=0.012 * sway, chest=2.0 * sway, look=look, pitch=0.05 + 0.025 * br)
    aims["halberd"] = hb.aim(rest_m)
    aims.update(fist_on(arm, "R", hb.pt(IDLE_S), hb.A, body_pt(J["shoulder_R"], ro, yaw), rz(yaw) @ V(-0.7, 0.6, -0.5)))
    hip = body_pt(IDLE_HIP, ro, yaw)
    aims.update(arm_aims(arm, "L", hip + V(0, 0, 0.004 * br), pole=rz(yaw) @ V(1.0, 0.55, 0.15),
                         hand_dir=rz(yaw) @ V(-0.4, 0.2, -1.0)))
    return aims, ro, rz(yaw)


def make_idle(arm, frames=120):
    P = Poser(arm)
    rest_m = P.rest["halberd"]
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames, rest_m)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- combat: levelled, braced
# Poses below are in his body frame: turned with his hips by `yaw` (and carried by the root offset) into the robots'
# frame (body_pt / bdir), so his twist drives the swing.
C_YAW = -48.0
C_FEET = dict(lf=(0.2, -0.26), rf=(-0.2, 0.25), turn=(4.0, -26.0))
G_GUARD = V(-0.2, -0.34, 1.1)                # his right fist, by his right breast (body frame)
A_GUARD = V(0.7, -0.7, -0.07)                # down the shaft toward the robots
S_GUARD = 0.42                               # his left fist this far up the shaft from his right
POLE_R = V(-0.9, 0.5, -0.4)
POLE_L = V(0.5, 0.2, -1.0)


def bdir(d, yaw):
    return rz(yaw) @ Vector(d)


def right_side(A, down=0.4):
    """The blade's side when it is out to his right of the shaft (looking down it), tipped down by `down`."""
    A = Vector(A).normalized()
    b = A.cross(V(0.0, 0.0, 1.0))
    if b.length < 1e-4:
        b = V(-1.0, 0.0, 0.0)
    return _ortho(b.normalized() + V(0.0, 0.0, -down), A)


B_GUARD = right_side(A_GUARD, 0.35)


def guard_state(t):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    yaw = C_YAW + 1.2 * sw
    ro = rz(C_YAW) @ V(0.0, -0.03, 0.0) + V(0.0, 0.0, -0.075 + 0.008 * br)
    g = G_GUARD + V(0.004 * sw, 0.0, 0.008 * br)
    A = (A_GUARD + V(0.015 * sw, 0.0, 0.012 * br)).normalized()
    hb = Halberd.from_grip(body_pt(g, ro, yaw), bdir(A, yaw), bdir(right_side(A, 0.35), yaw))
    return br, sw, yaw, ro, hb


def combat_pose(arm, t, rest_m):
    br, sw, yaw, ro, hb = guard_state(t)
    aims = feet(arm, C_YAW, **C_FEET)
    torso(aims, yaw, bend=0.14, side=0.01 * sw, chest=-8.0, look=0.0, pitch=0.06 + 0.015 * br)
    aims["halberd"] = hb.aim(rest_m)
    aims.update(both_hands(arm, hb, RIGHT_S + S_GUARD, ro, yaw, rz(yaw) @ POLE_R, rz(yaw) @ POLE_L))
    return aims, ro, rz(yaw)


def make_combat(arm, frames=40):
    P = Poser(arm)
    rest_m = P.rest["halberd"]
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr = combat_pose(arm, (f % frames) / frames, rest_m)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- attack: the chop
def _toward(yaw):
    """The robots' direction in the body frame turned by yaw."""
    return rz(-yaw) @ V(0.0, -1.0, 0.0)


#      frame, right fist (body),    shaft dir (body),       blade side (body),      left at, yaw, chest, bend, crouch, lunge, right at
KEYS = [(0, G_GUARD, A_GUARD, B_GUARD, S_GUARD, C_YAW, -8.0, 0.14, 0.075, 0.0, RIGHT_S),
        (4, V(-0.27, -0.36, 1.28), V(-0.08, 0.16, 1.0), _toward(-66.0), 0.24, -66.0, -10.0, 0.02, 0.05, -0.06, 0.15),
        (6, V(-0.2, -0.44, 1.31), V(0.25, -0.55, 1.0), V(0.4, -0.85, -0.45), 0.25, -52.0, -8.0, 0.1, 0.07, 0.02, 0.13),
        (7, V(-0.14, -0.47, 1.2), V(0.4, -1.0, 0.4), V(0.25, -0.35, -1.0), 0.25, -40.0, -6.0, 0.2, 0.09, 0.1, 0.12),
        (HIT, V(-0.08, -0.46, 0.99), V(0.36, -0.88, -0.3), V(0.05, 0.35, -1.0), 0.25, -20.0, -4.0, 0.34, 0.14, 0.2, 0.11),
        (12, V(-0.06, -0.47, 0.95), V(0.84, -0.45, -0.24), V(-0.25, 0.5, -1.0), 0.25, -6.0, 2.0, 0.34, 0.14, 0.16, 0.1),
        (16, V(-0.14, -0.42, 1.06), V(0.72, -0.68, 0.06), V(-0.45, -0.5, -1.0), 0.32, -30.0, -6.0, 0.22, 0.1, 0.06, 0.1),
        (FR, G_GUARD, A_GUARD, B_GUARD, S_GUARD, C_YAW, -8.0, 0.14, 0.075, 0.0, RIGHT_S)]


def _catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def key_at(f):
    """(grip, shaft dir, blade side (body frame), left fist spacing, yaw, chest, bend, crouch, lunge, right fist along the
    shaft) at frame f."""
    i = max(k for k in range(len(KEYS) - 1) if KEYS[k][0] <= f) if f < KEYS[-1][0] else len(KEYS) - 2
    a, b = KEYS[i], KEYS[i + 1]
    k = (f - a[0]) / float(b[0] - a[0])
    if a[0] in (4, 6):
        k = k * k * (1.4 - 0.4 * k)                     # the chop gathers speed
    elif a[0] == 7:
        k = 1 - (1 - k) ** 1.6                          # ... and drives on through the hit
    else:
        k = ease(k)
    p0 = KEYS[max(i - 1, 0)][1]
    p3 = KEYS[min(i + 2, len(KEYS) - 1)][1]
    g = _catmull(p0, a[1], b[1], p3, k)
    A = mixd(a[2], b[2], k)
    B = mixd(_ortho(a[3], a[2].normalized()), _ortho(b[3], b[2].normalized()), k)
    vals = [lerp(a[j], b[j], k) for j in range(4, 11)]
    return (g, A, B) + tuple(vals)


def attack_state(f):
    g, A, B, sp, yaw, chest, bend, crouch, lunge, s_r = key_at(f)
    ro = rz(yaw) @ V(0.0, -0.03 - 0.12 * lunge, 0.0) + V(0.0, 0.0, -crouch)
    hb = Halberd.from_grip(body_pt(g, ro, yaw), bdir(A, yaw), bdir(B, yaw), s=s_r)
    return hb, s_r, s_r + sp, yaw, chest, bend, ro


def attack_pose(arm, f, rest_m):
    hb, s_r, s_l, yaw, chest, bend, ro = attack_state(f)
    stamp = math.sin(math.pi * min(1.0, max(0.0, (f - 3) / 5.0)))       # the left foot up and stamped down (3-8)
    aims = feet(arm, C_YAW, lift=(0.04 * stamp, 0.0), **C_FEET)
    lean = max(0.0, min(1.0, (bend - 0.14) / 0.2))                      # the left shoulder reaches into the blow
    torso(aims, yaw, bend=bend, chest=chest, look=0.0, pitch=0.06 - 0.1 * (bend - 0.14), reach=(0.3 * lean, 0.1 * lean))
    aims["halberd"] = hb.aim(rest_m)
    aims.update(both_hands(arm, hb, s_l, ro, yaw, rz(yaw) @ POLE_R, rz(yaw) @ POLE_L, s_r=s_r))
    return aims, ro, rz(yaw)


def make_attack(arm, frames=FR):
    P = Poser(arm)
    rest_m = P.rest["halberd"]
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, rr = attack_pose(arm, f, rest_m)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
