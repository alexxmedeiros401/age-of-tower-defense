"""Mech Brawler clips (game: 24 fps):
- Idle (96 frames): a wide, easy stance, the big fists hanging by its knees, the servos' slow breathing bob. It raises
  its right fist before its chest and flexes it (opens and clenches it twice: the finger blocks swing open on their
  hinge), lowers it; then the left. The pilot watches each fist, then looks about.
- Combat (40 frames): the guard: knees bent, both fists up before its chest (thumbs up, knuckles to the robots), rocking
  from foot to foot with a bob; the pilot leans forward a little, looking at the robots.
- Attack (24 frames, the 1.0 s cooldown): the two-fisted ground slam. From the guard it rears up and swings both fists
  up over its head behind the roll bar (0-4), the left foot lifting; then it hammers them down in an arc before it,
  bending deep at the hips and knees, the left foot stamping forward, and drives the knuckles into the ground at BLOW
  (frame 8: the knuckle plates strike the floor about 0.95 m before it); the recoil bounces the fists up (8-11), it holds
  low a moment (11-13) and straightens back into the guard (13-24). The pilot's head jolts at the blow.

The arms are posed by their knuckles (as the Steam Brawler's, anim_steam_brawler.py): the upper arm and the forearm with
its rigid fist are a two-bone chain from the shoulder to the knuckle plates' front, both bones turned so the elbow works
as a hinge with the thumb where the clip puts it. The fingers (`fingers.*`) turn on their hinge across the knuckles."""
import math
from mathutils import Vector, Quaternion, Matrix
import mech_brawler as cm
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
    OPEN_AX[_s] = vec(_A).cross(-vec(_M)).normalized()            # turning about it swings the fingers away from the palm
KN_OFF = float((cm.knuckle_point("R") - J["wrist_R"]) @ cm.gframe("R")[1])      # wrist -> knuckles, along the forearm
BLOW = 8              # the knuckles strike the ground (game.gd ATTACK_FRAME)
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
def feet(arm, yaw, lf=(0.3, 0.05), rf=(-0.3, 0.05), lift=(0.0, 0.0), turn=(8.0, -8.0), step=(0.0, 0.0)):
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
          lean=0.0):
    """The waist and hull bent forward by `bend` radians (to its left by `side`), the hull turned `chest` degrees more;
    the pilot's head to the world heading `look` (0 = the robots), pitched up by `pitch`, leaning forward by `lean`
    (his neck); `shrug` / `reach` move the shoulder actuators up / forward."""
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
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(math.sin(roll) * 0.5, -0.1 - math.sin(nb) * 0.9 + 0.2 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.06 - math.sin(nb) * 0.4 + 0.55 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -reach[0], shrug[0])
    aims["clavicle.R"] = qc @ V(-1.0, -reach[1], shrug[1])


def _solve_key(P, aims, ro, rr, f):
    ch, _ = P.solve(aims, ro, rr)
    P.key(ch, f)


# ---------------------------------------------------------------------------------------------- idle
I_FEET = dict(lf=(0.31, 0.05), rf=(-0.31, 0.05), turn=(10.0, -10.0))
HANG = {"R": V(-0.74, -0.1, 0.5), "L": V(0.74, -0.1, 0.5)}          # the knuckles, hanging by its knees
FLEX = {"R": V(-0.42, -0.62, 1.2), "L": V(0.42, -0.62, 1.2)}        # ... raised before its chest to flex


def _bump(t, a, b, ramp):
    """0 outside [a, b], 1 inside, eased ramps `ramp` long."""
    if t <= a or t >= b:
        return 0.0
    return ease(min(1.0, (t - a) / ramp)) * ease(min(1.0, (b - t) / ramp))


def idle_pose(arm, t, rest):
    w = 2 * math.pi * t
    br = math.sin(w * 3)
    sway = math.sin(w)
    yaw = 2.0 * sway
    ro = V(0.008 * sway, 0.0, -0.025 + 0.008 * br)
    aims = feet(arm, 0.0, **I_FEET)
    flex = {"R": _bump(t, 0.08, 0.42, 0.09), "L": _bump(t, 0.56, 0.9, 0.09)}
    # the pilot: watches the right fist, then the left, looking about between
    lookR, lookL = -32.0, 30.0
    look = 14.0 * math.sin(w * 2 + 0.6)
    look = look * (1 - flex["R"] - flex["L"]) + lookR * flex["R"] + lookL * flex["L"]
    pitch = 0.1 - 0.25 * (flex["R"] + flex["L"]) + 0.03 * br
    torso(aims, yaw, bend=0.05 + 0.02 * br, side=0.02 * sway, chest=2.0 * sway - 6.0 * flex["R"] + 6.0 * flex["L"], look=look,
          pitch=pitch, shrug=(0.06 * flex["L"], 0.06 * flex["R"]))
    for side, sx in (("R", -1), ("L", 1)):
        k = flex[side]
        T = body_pt(HANG[side].lerp(FLEX[side], k), ro, yaw)
        tau = rz(yaw) @ mixd(V(0.0, -1.0, 0.25), V(sx * -0.5, 0.25, 1.0), k)
        # it opens and clenches the raised fist twice
        op = 0.0
        if k > 0.5:
            tt = (t - (0.08 if side == "R" else 0.56)) / 0.34
            op = 0.75 * max(0.0, math.sin(tt * 2 * math.pi * 2 - 0.9)) ** 1.5 * k
        aims.update(fist_at(arm, side, T, tau, rest, open_=op, pole=rz(yaw) @ V(sx * 1.0, 0.6, -0.3)))
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
C_FEET = dict(lf=(0.33, -0.04), rf=(-0.31, 0.13), turn=(6.0, -14.0))
G_R = V(-0.33, -0.66, 1.3)              # the fists' knuckles (the robots are toward -Y)
G_L = V(0.34, -0.74, 1.24)
TAU_R = V(0.35, 0.2, 1.0)               # thumbs up, tipped in
TAU_L = V(-0.35, 0.2, 1.0)
POLE_R = V(-1.0, 0.5, -0.6)             # elbows out and down
POLE_L = V(1.0, 0.5, -0.6)
C_CROUCH = 0.07
C_BEND = 0.14


def guard_state(t):
    w = 2 * math.pi * t
    rock = math.sin(w)
    b = 0.5 - 0.5 * math.cos(2 * w)                           # a bob each half rock
    yaw = 5.0 * rock
    ro = V(0.03 * rock, 0.0, -C_CROUCH - 0.02 * b)
    return w, rock, b, yaw, ro


def _carried(p, ro, dyaw):
    r0 = V(0.0, 0.0, -C_CROUCH)
    return ROOT + ro + rz(dyaw) @ (Vector(p) - ROOT - r0)


def combat_pose(arm, t, rest):
    w, rock, b, yaw, ro = guard_state(t)
    # the foot it rocks off rises a little
    aims = feet(arm, 0.0, lift=(0.025 * max(0.0, -rock), 0.025 * max(0.0, rock)), **C_FEET)
    torso(aims, yaw, bend=C_BEND + 0.02 * b, side=-0.05 * rock, chest=-3.0 * rock, look=0.0, pitch=0.12, lean=0.06)
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


# ---------------------------------------------------------------------------------------------- attack: the ground slam
SLAM_X, SLAM_Y, SLAM_Z = 0.3, -0.95, 0.07      # where the knuckles strike (each side's x), knuckle plates to the floor
#      frame, right knuckles,            right thumb,          bend,  crouch, lunge, rise, pitch, open
KEYS = [(0, G_R, TAU_R, C_BEND, C_CROUCH, 0.0, 0.0, 0.12, 0.0),
        (4, V(-0.3, 0.1, 2.55), V(0.8, 0.5, -0.1), -0.16, 0.0, -0.04, 0.05, 0.22, 0.25),
        (6, V(-0.34, -0.78, 1.95), V(0.9, 0.1, -0.3), 0.2, 0.08, 0.04, 0.0, 0.1, 0.0),
        (BLOW, V(-SLAM_X, SLAM_Y, SLAM_Z), V(0.85, 0.45, 0.0), 0.66, 0.27, 0.1, 0.0, 0.04, 0.0),
        (10, V(-SLAM_X - 0.01, SLAM_Y + 0.05, SLAM_Z + 0.15), V(0.85, 0.45, 0.0), 0.56, 0.22, 0.09, 0.0, 0.16, 0.0),
        (13, V(-0.31, -0.86, 0.3), V(0.7, 0.4, 0.4), 0.48, 0.19, 0.07, 0.0, 0.12, 0.0),
        (FR, G_R, TAU_R, C_BEND, C_CROUCH, 0.0, 0.0, 0.12, 0.0)]


def _catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def mirror(p):
    return V(-p.x, p.y, p.z)


def key_at(f):
    K = KEYS
    i = max(k for k in range(len(K) - 1) if K[k][0] <= f) if f < K[-1][0] else len(K) - 2
    a, b = K[i], K[i + 1]
    k = (f - a[0]) / float(b[0] - a[0])
    if a[0] == 4:
        k = k * k                                        # the swing gathers speed down into the blow ...
    elif a[0] == 6:
        k = k * (1.4 - 0.4 * k)
    elif a[0] == BLOW:
        k = 1 - (1 - k) ** 2                             # ... and the recoil snaps up
    else:
        k = ease(k)
    p0 = K[max(i - 1, 0)][1]
    p3 = K[min(i + 2, len(K) - 1)][1]
    T = _catmull(p0, a[1], b[1], p3, k) if a[0] not in (BLOW,) else a[1].lerp(b[1], k)
    tau = mixd(a[2], b[2], k)
    vals = [lerp(a[j], b[j], k) for j in range(3, 9)]
    return (T, tau) + tuple(vals)


def attack_pose(arm, f, rest):
    T, tau, bend, crouch, lunge, rise, pitch, op = key_at(f)
    ro = V(0.0, -lunge, -crouch + rise)
    # the left foot lifts in the wind-up (1-6) and stamps forward at the blow, back to the guard (14-22)
    lift = math.sin(math.pi * min(1.0, max(0.0, (f - 1) / 7.0))) * 0.07 if f < BLOW else 0.0
    stay = min(1.0, max(0.0, (f - 2) / 6.0)) * (1.0 - ease(min(1.0, max(0.0, (f - 14) / 8.0))))
    aims = feet(arm, 0.0, lift=(lift, 0.0), step=(0.1 * ease(stay), 0.0), **C_FEET)
    jolt = math.exp(-((f - BLOW - 1.0) / 1.2) ** 2)
    torso(aims, 0.0, bend=bend, look=0.0, pitch=pitch - 0.2 * jolt, lean=0.06 + 0.12 * jolt, shrug=(0.15 * max(0.0, -bend), 0.15 * max(0.0, -bend)),
          reach=(0.25 * max(0.0, bend - 0.3), 0.25 * max(0.0, bend - 0.3)))
    sp = abs(T.x)
    TR = T
    TL = mirror(T)
    tauR, tauL = tau, mirror(tau)
    poleR, poleL = V(-1.0, 0.6, -0.2), V(1.0, 0.6, -0.2)
    aims.update(fist_at(arm, "R", TR, tauR, rest, open_=op, pole=poleR))
    aims.update(fist_at(arm, "L", TL, tauL, rest, open_=op, pole=poleL))
    return aims, ro, rz(0.0)


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
