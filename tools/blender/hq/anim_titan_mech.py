"""Titan Mech clips (game: 24 fps):
- Idle (96 frames): a wide, heavy stance, the huge fists hanging by its knees; it sways its weight slowly from foot to
  foot (the hull rolling over its hips, the servos' bob, the fists swinging a beat behind), clenching and opening each
  fist once. The pilot looks about (left, ahead, right), the robot's head scanning slowly on its neck.
- Combat (40 frames): the guard: knees bent, both fists up before its belly and chest (thumbs up, knuckles to the
  robots), rocking from foot to foot with a bob; the pilot looking at the robots.
- Attack (24 frames, the 1.0 s cooldown): a sweeping right haymaker. From the guard it winds up, turning its hull to
  the right and drawing the right fist back and out at shoulder height (0-4); then it swings the fist round in a wide,
  falling arc, stepping in on its left foot and turning its hips and hull through, and the knuckle bar strikes across
  the front at BLOW (frame 9: the knuckles about 0.95 m before it, at a robot's chest height); the fist follows through
  to its left (9-12), recoils (12-14) and it comes back into the guard (14-24). The left fist stays up by its chest;
  the pilot's head jolts at the blow.

The arms are posed by their knuckles (as the Mech Brawler's, anim_mech_brawler.py): the upper arm and the forearm with
its rigid fist are a two-bone chain from the shoulder to the knuckle bar's front, both bones turned so the elbow works as
a hinge with the thumb where the clip puts it. The fingers (`fingers.*`) turn on their hinge across the knuckles; the
robot's head (`mhead`) turns on its neck."""
import math
from mathutils import Vector, Quaternion, Matrix
import titan_mech as cm
from rig import Poser, leg_aims, frame_map, two_bone, bone_len
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
A_REST, W_REST, H_REST, U_REST, OPEN_AX = {}, {}, {}, {}, {}
for _s in ("R", "L"):
    _wr, _A, _W, _M = cm.gframe(_s)
    A_REST[_s], W_REST[_s] = vec(_A), vec(_W)
    H_REST[_s] = vec(_A).cross(vec(_W)).normalized()
    U_REST[_s] = (vec(J["elbow_" + _s]) - vec(J["shoulder_" + _s])).normalized()
    OPEN_AX[_s] = vec(_A).cross(-vec(_M)).normalized()
KN_OFF = float((cm.knuckle_point("R") - J["wrist_R"]) @ cm.gframe("R")[1])      # wrist -> knuckles, along the forearm
BLOW = 9              # the knuckle bar strikes (game.gd ATTACK_FRAME)
FR = 24


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def _ortho(b, a):
    b = Vector(b) - Vector(a) * Vector(b).dot(Vector(a))
    return b.normalized() if b.length > 1e-5 else Vector(a).orthogonal().normalized()


def mixd(a, b, k):
    a, b = Vector(a).normalized(), Vector(b).normalized()
    if a.dot(b) > -0.98:
        return a.slerp(b, k).normalized()
    return a.lerp(b, k).normalized()


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


# ---------------------------------------------------------------------------------------------- arms (by the knuckles)
def fist_at(arm, side, T, tau, rest, open_=0.0, pole=None):
    """Aims putting the knuckles of `side` at T (armature space) with the thumb toward tau; the fingers opened by
    `open_` radians on their hinge; the elbow toward `pole` (default: away from the thumb)."""
    la = bone_len(arm, "upperarm." + side)
    lb = bone_len(arm, "forearm." + side)
    L2 = lb + KN_OFF
    T = Vector(T)
    tau = Vector(tau).normalized()
    pl = (-tau) if pole is None else Vector(pole)
    st = {}

    def upper(P, base):
        S = base.translation
        E = two_bone(S, T, la, L2, pl)
        d = (T - E).normalized()
        t2 = _ortho(tau, d)
        st["d"], st["t"] = d, t2
        U = (E - S).normalized()
        return ("frame", U_REST[side], U, H_REST[side], d.cross(t2))

    def fore(P, base):
        return ("frame", A_REST[side], st["d"], W_REST[side], st["t"])

    def fingers(P, base):
        Rh = P["hand." + side].to_3x3() @ rest["hand." + side].to_3x3().inverted()
        return ("rot", Quaternion(Rh @ OPEN_AX[side], open_))

    return {"upperarm." + side: upper, "forearm." + side: fore, "fingers." + side: fingers}


# ---------------------------------------------------------------------------------------------- body
def feet(arm, yaw, lf=(0.36, 0.06), rf=(-0.36, 0.06), lift=(0.0, 0.0), turn=(8.0, -8.0), step=(0.0, 0.0)):
    """Ankles at the body-frame (x, y) lf / rf turned by yaw (planted: the hips turn over them); `step` moves each foot
    forward (world -y); `lift` raises each foot."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by), up, tw, fw in (("L", lf, lift[0], turn[0], step[0]), ("R", rf, lift[1], turn[1], step[1])):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y - fw, float(J["ankle_" + side][2]) + up)
        pole = q @ V(0.1 if side == "L" else -0.1, -1.0, 0.0)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw + tw) @ (rest_foot + V(0, 0, -up * 0.3))
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0, shrug=(0.0, 0.0), reach=(0.0, 0.0),
          lean=0.0, mlook=0.0, mpitch=0.0):
    """The waist and hull bent forward by `bend` radians (to its left by `side`), the hull turned `chest` degrees more;
    the pilot's head to the world heading `look` (0 = the robots), pitched up by `pitch`, leaning forward by `lean`;
    `shrug` / `reach` move the shoulder actuators up / forward; the robot's head turned `mlook` degrees on its neck
    (to its left) and pitched down by `mpitch` radians."""
    q = rz(yaw)
    qc = rz(yaw + chest)

    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.4, side * 0.4), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    # (the pilot sits in the hull: his neck takes back most of its bend, so he keeps looking out)
    nb = -bend * 0.75 + lean
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(math.sin(roll) * 0.5, -0.13 - math.sin(nb) * 0.9 + 0.2 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.05 - math.sin(nb) * 0.4 + 0.55 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -reach[0], shrug[0])
    aims["clavicle.R"] = qc @ V(-1.0, -reach[1], shrug[1])

    def mh(P, base):
        up = base.col[1].xyz.normalized()
        fwd = base.col[2].xyz.normalized()
        return (up * math.cos(mpitch) + fwd * math.sin(mpitch), math.radians(mlook))
    aims["mhead"] = mh


def _solve_key(P, aims, ro, rr, f):
    ch, _ = P.solve(aims, ro, rr)
    P.key(ch, f)


def _bump(t, a, b, ramp):
    """0 outside [a, b], 1 inside, eased ramps `ramp` long."""
    if t <= a or t >= b:
        return 0.0
    return ease(min(1.0, (t - a) / ramp)) * ease(min(1.0, (b - t) / ramp))


# ---------------------------------------------------------------------------------------------- idle
I_FEET = dict(lf=(0.38, 0.06), rf=(-0.38, 0.06), turn=(10.0, -10.0))
HANG = {"R": V(-0.8, -0.14, 0.56), "L": V(0.8, -0.14, 0.56)}          # the knuckles, hanging by its knees


def idle_pose(arm, t, rest):
    w = 2 * math.pi * t
    sway = math.sin(w)                       # its weight, from foot to foot
    br = math.sin(w * 4)                     # the servos' bob
    yaw = 2.5 * math.sin(w - 0.4)
    ro = V(0.035 * sway, 0.0, -0.03 + 0.007 * br - 0.012 * abs(sway))
    aims = feet(arm, 0.0, lift=(0.012 * max(0.0, -sway) ** 2, 0.012 * max(0.0, sway) ** 2), **I_FEET)
    # the pilot: looks to his left, ahead, to his right, ahead (holding each a moment)
    look = 34.0 * math.sin(w * 2 + 0.3) ** 3
    pitch = 0.06 + 0.06 * math.sin(w * 3 + 1.0)
    torso(aims, yaw, bend=0.06 + 0.015 * br, side=-0.05 * sway, chest=-2.5 * sway, look=look, pitch=pitch,
          roll=0.04 * math.sin(w * 2), mlook=14.0 * math.sin(w + 1.6), mpitch=0.08 + 0.04 * math.sin(w * 2 + 0.5))
    lag = math.sin(w - 0.7)
    for side, sx in (("R", -1), ("L", 1)):
        k = _bump(t, 0.18, 0.42, 0.08) if side == "R" else _bump(t, 0.62, 0.86, 0.08)
        T = body_pt(HANG[side] + V(0.02 * lag, -0.035 * lag * sx, 0.012 * br), ro, yaw)
        tau = rz(yaw) @ V(sx * -0.2, -1.0, 0.25)
        op = 0.6 * k * max(0.0, math.sin((t - (0.18 if side == "R" else 0.62)) / 0.24 * math.pi * 2 - 0.5)) ** 1.2
        aims.update(fist_at(arm, side, T, tau, rest, open_=op, pole=rz(yaw) @ V(sx * 1.0, 0.7, -0.2)))
    return aims, ro, rz(yaw)


def make_idle(arm, frames=96):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames, P.rest)
        _solve_key(P, aims, ro, rr, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- combat: the guard
C_FEET = dict(lf=(0.38, -0.05), rf=(-0.36, 0.15), turn=(6.0, -14.0))
G_R = V(-0.44, -0.8, 1.28)              # the fists' knuckles (the robots are toward -Y)
G_L = V(0.46, -0.86, 1.22)
TAU_R = V(0.35, 0.2, 1.0)               # thumbs up, tipped in
TAU_L = V(-0.35, 0.2, 1.0)
POLE_R = V(-1.0, 0.5, -0.5)             # elbows out and down
POLE_L = V(1.0, 0.5, -0.5)
C_CROUCH = 0.08
C_BEND = 0.14


def guard_state(t):
    w = 2 * math.pi * t
    rock = math.sin(w)
    b = 0.5 - 0.5 * math.cos(2 * w)
    yaw = 4.0 * rock
    ro = V(0.03 * rock, 0.0, -C_CROUCH - 0.02 * b)
    return w, rock, b, yaw, ro


def _carried(p, ro, dyaw):
    r0 = V(0.0, 0.0, -C_CROUCH)
    return ROOT + ro + rz(dyaw) @ (Vector(p) - ROOT - r0)


def combat_pose(arm, t, rest):
    w, rock, b, yaw, ro = guard_state(t)
    aims = feet(arm, 0.0, lift=(0.025 * max(0.0, -rock), 0.025 * max(0.0, rock)), **C_FEET)
    torso(aims, yaw, bend=C_BEND + 0.02 * b, side=-0.05 * rock, chest=-3.0 * rock, look=0.0, pitch=0.1, lean=0.06,
          mlook=-yaw * 0.8, mpitch=0.12)
    bob = V(0.0, 0.0, -0.015 * b)
    aims.update(fist_at(arm, "R", _carried(G_R + bob, ro, yaw), rz(yaw) @ TAU_R, rest, pole=rz(yaw) @ POLE_R))
    aims.update(fist_at(arm, "L", _carried(G_L + bob + V(0.0, 0.015 * rock, 0.0), ro, yaw), rz(yaw) @ TAU_L, rest, pole=rz(yaw) @ POLE_L))
    return aims, ro, rz(yaw)


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr = combat_pose(arm, (f % frames) / frames, P.rest)
        _solve_key(P, aims, ro, rr, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- attack: the haymaker
LG = V(0.5, -0.58, 1.4)                 # the left fist pulled up by its chest while it swings (body frame)
#      frame, right knuckles (world),   right thumb,         right elbow pole,      yaw,  chest, bend, crouch, lunge
KEYS = [(0, G_R, TAU_R, POLE_R, 0.0, 0.0, C_BEND, C_CROUCH, 0.0),
        (4, V(-1.02, 0.22, 1.5), V(0.25, 0.35, 1.0), V(-0.6, 1.0, 0.3), -16.0, -22.0, 0.05, 0.1, -0.05),
        (7, V(-0.86, -0.62, 1.14), V(0.3, 0.1, 1.0), V(-0.8, 0.6, 0.5), -2.0, 0.0, 0.2, 0.15, 0.05),
        (BLOW, V(0.02, -0.95, 0.88), V(0.3, -0.05, 1.0), V(-0.9, 0.0, 0.5), 12.0, 18.0, 0.3, 0.19, 0.11),
        (12, V(0.52, -0.76, 0.96), V(0.1, -0.2, 1.0), V(-0.6, -0.6, 0.6), 22.0, 26.0, 0.27, 0.18, 0.1),
        (14, V(0.3, -0.84, 1.06), V(0.2, -0.1, 1.0), V(-0.8, -0.3, 0.4), 18.0, 18.0, 0.24, 0.17, 0.09),
        (FR, G_R, TAU_R, POLE_R, 0.0, 0.0, C_BEND, C_CROUCH, 0.0)]


def _catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def key_at(f):
    K = KEYS
    i = max(k for k in range(len(K) - 1) if K[k][0] <= f) if f < K[-1][0] else len(K) - 2
    a, b = K[i], K[i + 1]
    k = (f - a[0]) / float(b[0] - a[0])
    if a[0] == 0:
        k = ease(k)
    elif a[0] == 4:
        k = k * k * (1.6 - 0.6 * k)                      # the swing gathers speed ...
    elif a[0] == 7:
        k = k * (1.3 - 0.3 * k)                          # ... and drives through the blow
    elif a[0] == BLOW:
        k = 1 - (1 - k) ** 2                             # the follow-through slows
    else:
        k = ease(k)
    p0 = K[max(i - 1, 0)][1]
    p3 = K[min(i + 2, len(K) - 1)][1]
    T = _catmull(p0, a[1], b[1], p3, k) if a[0] != 0 else a[1].lerp(b[1], k)
    tau = mixd(a[2], b[2], k)
    pole = mixd(a[3], b[3], k)
    vals = [lerp(a[j], b[j], k) for j in range(4, 9)]
    return (T, tau, pole) + tuple(vals)


def attack_pose(arm, f, rest):
    T, tau, pole, yaw, chest, bend, crouch, lunge = key_at(f)
    ro = V(0.0, -lunge, -crouch)
    # the left foot steps in for the swing (3-8) and back to the guard (15-21); the right heel turns
    step = ease(min(1.0, max(0.0, (f - 3) / 5.0))) * (1.0 - ease(min(1.0, max(0.0, (f - 15) / 6.0))))
    lift = math.sin(math.pi * min(1.0, max(0.0, (f - 3) / 5.0))) * 0.06 if f < 8 else (
        math.sin(math.pi * min(1.0, max(0.0, (f - 15) / 6.0))) * 0.04 if 15 <= f < 21 else 0.0)
    aims = feet(arm, 0.0, lift=(lift, 0.0), step=(0.12 * step, 0.0), lf=C_FEET["lf"], rf=C_FEET["rf"],
                turn=(C_FEET["turn"][0], C_FEET["turn"][1] + 18.0 * step))
    jolt = math.exp(-((f - BLOW - 1.0) / 1.3) ** 2)
    torso(aims, yaw, bend=bend, side=0.04 * math.sin(math.pi * min(1.0, f / 14.0)), chest=chest, look=0.0,
          pitch=0.1 - 0.2 * jolt, lean=0.06 + 0.12 * jolt, roll=0.08 * jolt,
          shrug=(0.0, 0.12 * max(0.0, 1.0 - abs(f - 4) / 5.0)), reach=(0.0, 0.25 * max(0.0, 1.0 - abs(f - BLOW) / 4.0)),
          mlook=-0.6 * (yaw + chest) - 6.0 * jolt, mpitch=0.12 + 0.2 * jolt)
    aims.update(fist_at(arm, "R", T, tau, rest, pole=pole))
    ro_c = V(0.0, -lunge, -crouch)
    TL = ROOT + ro_c + rz(yaw) @ (LG - ROOT)
    k0 = ease(min(1.0, f / 4.0)) * (1.0 - ease(min(1.0, max(0.0, (f - 14) / 10.0))))
    TL = G_L.lerp(TL, k0)
    aims.update(fist_at(arm, "L", TL, rz(yaw) @ TAU_L, rest, pole=rz(yaw) @ POLE_L))
    return aims, ro, rz(yaw)


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, rr = attack_pose(arm, f, P.rest)
        _solve_key(P, aims, ro, rr, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
