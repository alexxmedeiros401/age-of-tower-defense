"""Steam Brawler clips (game: 24 fps):
- Idle (96 frames): a wide, easy stance, the huge fists hanging before his thighs; he rolls his shoulders one after the
  other (the boiler heaves with his chest at PUFF, frame 44: a good moment for a puff of steam from the vent), breathes,
  looks about.
- Combat (40 frames): a boxer's guard, bladed (left foot forward), the left fist out before him, the right by his chin;
  he bounces twice on the balls of his feet and weaves a little.
- Attack (24 frames, the 1.0 s cooldown): from the guard he cocks the right fist back beside his head, turning away
  (0-5); then steps in on his left foot, turns his hips and shoulders through and drives a straight right (5-10), the
  fist turning over (palm down); at BLOW (frame 10) the pistons fire and the fist rams out along his forearm (RAM_MAX)
  into the robot, its knuckles about 1.4 m in front of him; he holds it a moment (10-13), the ram slides back (13-17)
  and he comes back to the guard (13-24).

The arms are posed by their knuckles: the upper arm and the forearm-with-fist (rigid: the wrist stays straight) are a
two-bone chain from the shoulder to the knuckle-plate, its elbow away from the thumb; both bones are turned so the elbow
works as a hinge with the thumb where the clip puts it. The fist rides its free `ram.*` bone: every frame it is put on
its forearm ("world" aim from the solved forearm) and pushed out along it by the ram's travel."""
import math
from mathutils import Vector, Quaternion, Matrix
import steam_brawler as cm
from rig import Poser, leg_aims, frame_map, two_bone, bone_len
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
A_REST, W_REST, H_REST, U_REST = {}, {}, {}, {}
for _s in ("R", "L"):
    _wr, _A, _W, _M = cm.gframe(_s)
    A_REST[_s], W_REST[_s] = vec(_A), vec(_W)
    H_REST[_s] = vec(_A).cross(vec(_W)).normalized()
    U_REST[_s] = (vec(J["elbow_" + _s]) - vec(J["shoulder_" + _s])).normalized()
KN_OFF = float((cm.knuckle_point("R") - J["wrist_R"]) @ cm.gframe("R")[1])      # wrist -> knuckles, along the forearm
BLOW = 10             # the blow lands (game.gd ATTACK_FRAME): the ram fully out
FR = 24
PUFF = 44             # (Idle) the chest heaves: a puff from the vent would sit well here


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


def world_to_body(p, ro, yaw):
    return ROOT + rz(-yaw) @ (vec(p) - ROOT - ro)


# ---------------------------------------------------------------------------------------------- arms (by the knuckles)
def fist_at(arm, side, T, tau, ext, rest):
    """Aims putting the knuckles of `side` at T (armature space) with the thumb toward tau, the ram out by ext."""
    la = bone_len(arm, "upperarm." + side)
    lb = bone_len(arm, "forearm." + side)
    L2 = lb + KN_OFF + ext
    T = Vector(T)
    tau = Vector(tau).normalized()
    st = {}

    def upper(P, base):
        S = base.translation
        E = two_bone(S, T, la, L2, -tau)
        d = (T - E).normalized()
        t2 = _ortho(tau, d)
        st["d"], st["t"] = d, t2
        U = (E - S).normalized()
        return ("frame", U_REST[side], U, H_REST[side], d.cross(t2))

    def fore(P, base):
        return ("frame", A_REST[side], st["d"], W_REST[side], st["t"])

    rel = rest["forearm." + side].inverted() @ rest["ram." + side]

    def ram(P, base):
        Mf = P["forearm." + side]
        d = Mf.col[1].xyz.normalized()
        return ("world", Matrix.Translation(d * ext) @ Mf @ rel)

    return {"upperarm." + side: upper, "forearm." + side: fore, "ram." + side: ram}


# ---------------------------------------------------------------------------------------------- body
def feet(arm, yaw, lf=(0.22, -0.04), rf=(-0.22, 0.06), lift=(0.0, 0.0), turn=(10.0, -10.0), step=(0.0, 0.0)):
    """Ankles at the body-frame (x, y) lf / rf turned by yaw (planted: the hips turn over them); `step` moves each foot
    forward (world -y); `lift` raises each heel."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by), up, tw, fw in (("L", lf, lift[0], turn[0], step[0]), ("R", rf, lift[1], turn[1], step[1])):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y - fw, float(J["ankle_" + side][2]) + up)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw + tw) @ (rest_foot + V(0, 0, -up * 0.6))
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0, shrug=(0.0, 0.0), reach=(0.0, 0.0)):
    """Spine and chest bent forward by `bend` radians and to his left by `side`, the chest turned `chest` degrees more;
    the head to the world heading `look` (degrees, 0 = the robots), pitched up by `pitch`; `shrug` (left, right) lifts
    each shoulder, `reach` brings it forward."""
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
    aims["clavicle.L"] = qc @ V(1.0, -0.03 - reach[0], 0.02 + shrug[0])
    aims["clavicle.R"] = qc @ V(-1.0, -0.03 - reach[1], 0.02 + shrug[1])


def _solve_key(P, aims, ro, rr, f):
    ch, _ = P.solve(aims, ro, rr)
    P.key(ch, f)


# ---------------------------------------------------------------------------------------------- idle
I_FEET = dict(lf=(0.25, -0.03), rf=(-0.25, 0.04), turn=(16.0, -16.0))


def idle_pose(arm, t, rest):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = 3.0 * sway
    # the shoulder roll: each shoulder up, back, down and forward in turn (the right first)
    def roll(ph):
        a = w * 2 - ph
        k = max(0.0, math.sin(a * 0.5)) ** 2                 # (one roll each per half loop, a rest between)
        return 0.16 * k * math.sin(a), 0.12 * k * math.cos(a)
    upR, fwR = roll(0.0)
    upL, fwL = roll(math.pi * 0.9)
    heave = math.exp(-((t * 96 - PUFF) / 7.0) ** 2)           # the chest heaves (a deep breath) at PUFF
    ro = V(0.006 * sway, 0.0, -0.03 + 0.005 * br + 0.01 * heave)
    aims = feet(arm, 0.0, **I_FEET)
    look = 24.0 * math.sin(w + 0.5) + 6.0 * math.sin(w * 3)
    torso(aims, yaw, bend=0.06 - 0.06 * heave, side=0.015 * sway, chest=2.0 * sway, look=look, pitch=0.02 + 0.02 * br + 0.05 * heave,
          shrug=(upL + 0.04 * heave, upR + 0.04 * heave), reach=(fwL, fwR))
    for side, sx, up, fw in (("R", -1, upR, fwR), ("L", 1, upL, fwL)):
        T = body_pt(V(sx * 0.66, -0.2 - 0.06 * fw, 0.56 + 0.25 * up), ro, yaw)
        tau = rz(yaw) @ V(-sx * 0.25, -1.0, 0.35)
        aims.update(fist_at(arm, side, T, tau, 0.0, rest))
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
# (fists and thumbs in the robots' frame: the robots are toward -Y)
C_YAW = -18.0
C_FEET = dict(lf=(0.15, -0.21), rf=(-0.2, 0.17), turn=(6.0, -22.0))
G_L = V(0.21, -0.86, 1.2)             # the lead (left) fist's knuckles, out before him
G_R = V(-0.3, -0.74, 1.27)            # the right by his chin
TAU_L = V(-0.2, 0.35, 1.0)            # thumbs up (palms in), tipped back toward him
TAU_R = V(0.45, 0.35, 1.0)
C_CROUCH = 0.075


def guard_state(t):
    w = 2 * math.pi * t
    b = 0.5 - 0.5 * math.cos(2 * w)                           # two bounces a loop
    weave = math.sin(w)
    yaw = C_YAW + 3.0 * weave
    ro = V(0.012 * weave, 0.0, -C_CROUCH + 0.028 * b)
    return w, b, weave, yaw, ro


def _carried(p, ro, dyaw):
    """A guard point carried by the body's bounce (ro) and its weave (turned dyaw degrees about the hips)."""
    r0 = V(0.0, 0.0, -C_CROUCH)
    return ROOT + ro + rz(dyaw) @ (Vector(p) - ROOT - r0)


def combat_pose(arm, t, rest):
    w, b, weave, yaw, ro = guard_state(t)
    aims = feet(arm, C_YAW, lift=(0.022 * b, 0.026 * b), **C_FEET)
    torso(aims, yaw, bend=0.12 + 0.02 * b, side=0.03 * weave, chest=-2.0 * weave, look=0.0, pitch=0.07)
    bob = V(0.0, 0.0, -0.012 * b)
    dy = yaw - C_YAW
    aims.update(fist_at(arm, "L", _carried(G_L + bob + V(0.0, -0.012 * weave, 0.0), ro, dy), rz(dy) @ TAU_L, 0.0, rest))
    aims.update(fist_at(arm, "R", _carried(G_R + bob, ro, dy), rz(dy) @ TAU_R, 0.0, rest))
    return aims, ro, rz(yaw)


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr = combat_pose(arm, (f % frames) / frames, P.rest)
        _solve_key(P, aims, ro, rr, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- attack: the piston punch
BLOW_AT = V(0.02, -1.46, 1.22)        # where the knuckles land at BLOW


def _ro(lunge, crouch):
    return V(0.0, -lunge, -crouch)


#      frame, right knuckles,               its thumb,             left knuckles,          yaw,   chest, bend, crouch, lunge
KEYS = [(0, G_R, TAU_R, G_L, C_YAW, 0.0, 0.12, C_CROUCH, 0.0),
        (5, V(-0.52, -0.46, 1.33), V(0.9, -0.1, 1.0), V(0.22, -0.88, 1.22), -40.0, -10.0, 0.05, 0.1, -0.04),
        (8, V(-0.22, -1.06, 1.28), V(1.0, 0.1, 0.5), V(0.32, -0.88, 1.22), -12.0, 8.0, 0.22, 0.12, 0.1),
        (BLOW, BLOW_AT, V(1.0, 0.0, -0.08), V(0.42, -0.84, 1.2), 14.0, 12.0, 0.3, 0.14, 0.17),
        (13, BLOW_AT + V(0.0, 0.06, 0.01), V(1.0, 0.0, -0.05), V(0.42, -0.85, 1.2), 12.0, 10.0, 0.28, 0.135, 0.16),
        (17, V(-0.25, -0.98, 1.3), V(0.6, 0.2, 1.0), V(0.3, -0.88, 1.2), -6.0, 4.0, 0.2, 0.11, 0.09),
        (FR, G_R, TAU_R, G_L, C_YAW, 0.0, 0.12, C_CROUCH, 0.0)]


def _catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def ram_at(f):
    """The ram's travel: it fires over the two frames before the blow, holds, slides back 13-17."""
    if f < 7:
        return 0.0
    if f <= BLOW - 2:
        return cm.RAM_MAX * 0.18 * (f - 7)
    if f <= BLOW:
        return cm.RAM_MAX * (0.18 + 0.82 * ((f - (BLOW - 2)) / 2.0) ** 0.7)
    if f <= 13:
        return cm.RAM_MAX
    if f <= 17:
        return cm.RAM_MAX * (1.0 - ease((f - 13) / 4.0))
    return 0.0


def key_at(f):
    K = KEYS
    i = max(k for k in range(len(K) - 1) if K[k][0] <= f) if f < K[-1][0] else len(K) - 2
    a, b = K[i], K[i + 1]
    k = (f - a[0]) / float(b[0] - a[0])
    if a[0] == 5:
        k = k * k * (1.6 - 0.6 * k)                      # the drive gathers speed into the blow
    elif a[0] == 8:
        k = 1 - (1 - k) ** 2
    else:
        k = ease(k)
    p0 = K[max(i - 1, 0)][1]
    p3 = K[min(i + 2, len(K) - 1)][1]
    T = _catmull(p0, a[1], b[1], p3, k) if a[0] != BLOW else a[1].lerp(b[1], k)
    tau = mixd(a[2], b[2], k)
    TL = a[3].lerp(b[3], k)
    vals = [lerp(a[j], b[j], k) for j in range(4, 9)]
    return (T, tau, TL) + tuple(vals) + (ram_at(f),)


def attack_pose(arm, f, rest):
    T, tau, TL, yaw, chest, bend, crouch, lunge, ram = key_at(f)
    ro = _ro(lunge, crouch)
    st = math.sin(math.pi * min(1.0, max(0.0, (f - 5) / 4.0)))        # the left foot steps in (5-9) ...
    stay = min(1.0, max(0.0, (f - 5) / 4.0)) * (1.0 - ease(min(1.0, max(0.0, (f - 15) / 7.0))))   # ... and back (15-22)
    heel = max(0.0, min(1.0, (f - 6) / 3.0)) * (1 - ease(min(1.0, max(0.0, (f - 14) / 6.0))))     # the rear heel up
    aims = feet(arm, C_YAW, lift=(0.05 * st, 0.03 * heel), step=(0.12 * ease(stay), 0.0), **C_FEET)
    lean = max(0.0, min(1.0, (bend - 0.12) / 0.18))
    torso(aims, yaw, bend=bend, chest=chest, look=0.0, pitch=0.07 - 0.1 * (bend - 0.12), reach=(0.0, 0.35 * lean))
    aims.update(fist_at(arm, "R", T, tau, ram, rest))
    aims.update(fist_at(arm, "L", TL, TAU_L + V(-0.9 * lean, 0.0, 0.0), 0.0, rest))     # (the left elbow out as he turns)
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
