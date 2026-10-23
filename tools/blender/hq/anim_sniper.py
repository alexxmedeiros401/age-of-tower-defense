"""Sniper clips (game: 24 fps). He kneels in his nest (right knee down on its pad, left foot forward), the rifle on its
bipod on the sandbags' top course (the ring round him: wherever the tower turns, the bipod's feet land on it).
- Idle (120 frames): his head up off the scope, looking out over it left and right; he settles his cheek on the stock
  and scans through the scope (the rifle sweeping slowly on its bipod), then lifts his head again.
- Combat (40 frames): on the scope, still: his cheek on the riser, a slow breath; the reticle barely moves.
- Attack (30 frames = 1.25 s, inside the 1.28 s cooldown): the shot at SHOT (frame 1: the muzzle has not moved yet:
  game.gd spawns the flash, the smoke and the bullet at the muzzle there); the recoil (2-4): the rifle slams back into
  his shoulder and its muzzle jumps, the bipod hops, his body rocks back and his head comes off the scope; it settles
  (5-8); his right hand leaves the grip for the bolt's knob (9-10), lifts it (11-12), draws it back (13-15: the empty
  case flies), runs it home (16-18), turns it down (19-20), goes back to the grip (21-23); his cheek finds the riser
  again (23-27) and he is on the scope by the last frame (= the Combat pose).

The rifle, its bolt and the bipod are bones without a parent, posed each frame by the whole matrix ("world" aims): the
rigid motion of their rest-pose placement (the bolt: the rifle's motion, then its own turn about the bore and its slide
along it; the bipod: the rifle's motion, then its legs swung about their pivot until the feet reach the ledge). The
right fist is put round the pistol grip by IK (its thumb axis up the grip), the cupped left hand under the butt; his
head is turned and tilted until his right eye sits behind the eyepiece."""
import math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
import sniper as cm
from rig import Poser, leg_aims, arm_aims, frame_map, bone_len, two_bone
from anim import new_action, finish_action

FPS = 24
TRACE = None              # (a list: per solved frame, the posed matrices and the targets, for checks)
SHOT = 1                  # the shot: the muzzle still on the aim (game.gd ATTACK_FRAME)
J = cm.J
V = lambda *a: Vector(a)
VV = lambda p: Vector((float(p[0]), float(p[1]), float(p[2])))
ROOT = VV(J["root"])
LEDGE_Z = cm.LEDGE_Z

# ---------------------------------------------------------------------------------------------- the rifle (rest pose)
_G, _A, _U, _S = cm.rifle_frame()
G_M, A_M, U_M, S_M = VV(_G), VV(_A), VV(_U), VV(_S)


def mloc(u, v=0.0, h=0.0):
    """A point of the rifle (rifle coordinates), where it is in the rest pose."""
    return G_M + A_M * u + S_M * v + U_M * h


MUZZLE = mloc(cm.MUZZLE_U, 0.0, cm.BORE_H)
BORE0 = mloc(0.0, 0.0, cm.BORE_H)
KNOB = mloc(*cm.KNOB)
_hb, _ht, _w = (float(x[0]) for x in cm.stock_profile(np.array([cm.BUTT_U], np.float32)))
BUTT = mloc(cm.BUTT_U, 0.0, _hb + 0.62 * (_ht - _hb))          # where the butt pad meets his shoulder
EYE = mloc(cm.SCOPE_U[0] - 0.072, 0.0, cm.SCOPE_H - 0.004)      # his eye behind the eyepiece
_lb = float(cm.stock_profile(np.array([-0.3], np.float32))[0][0])
CUP = mloc(-0.3, 0.0, _lb - 0.038)                             # the cupped left hand under the butt stock
_P0, _D, _BS, _BA = cm.bipod_frame()
BIPOD_P = VV(_P0)
FEET = [VV(p) for p in cm.bipod_feet()]
LIFT = math.radians(62)                    # the bolt's turn up (radians)
DRAW = 0.13                                # how far it slides back

HAND = {}
for _s in ("R", "L"):
    _wr, _f, _n, _t = cm.hand_frame(_s)
    HAND[_s] = {"wr": VV(_wr), "f": VV(_f), "n": VV(_n), "t": VV(_t), "off": VV(cm.fist_center(_s)) - VV(_wr)}
_EYE_REST = VV(cm.eye_c(-1))


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def rifle_at(point_rest, point_t, A_t, U_t):
    """The rifle's motion that lays it along A_t (its top toward U_t) with its rest-pose point `point_rest` at point_t."""
    R = frame_map(A_M, Vector(A_t).normalized(), U_M, Vector(U_t))
    return Matrix.Translation(Vector(point_t) - R @ Vector(point_rest)) @ R.to_4x4()


def rot_of(T):
    return T.to_3x3()


def bolt_motion(lift=0.0, draw=0.0):
    """The bolt's own motion (rest-pose rifle coordinates): turned up by `lift` about the bore, slid back `draw`."""
    q = Quaternion(A_M, -lift)
    return (Matrix.Translation(-A_M * draw) @ Matrix.Translation(BORE0) @ q.to_matrix().to_4x4()
            @ Matrix.Translation(-BORE0))


def bipod_motion(T_m):
    """The bipod's legs swung about their pivot (the gun's S axis) until the lower foot reaches the ledge; legs lean
    toward the muzzle. If the ledge is out of reach (the rifle hops), they hang straight down from the gun."""
    piv = T_m @ BIPOD_P
    axis = (rot_of(T_m) @ S_M).normalized()
    def feet_z(phi):
        R = Matrix.Translation(piv) @ Quaternion(axis, phi).to_matrix().to_4x4() @ Matrix.Translation(-piv)
        return min((R @ (T_m @ f)).z for f in FEET), R
    # phi > 0 swings the feet toward the muzzle (or back): pick the sign that does
    z0, _ = feet_z(0.0)
    zp, _ = feet_z(0.05)
    sgn = 1.0 if zp > z0 else -1.0                       # swinging this way lifts the feet: the legs lean forward
    lo, hi = 0.0, 1.2
    zlo, _ = feet_z(0.0)
    if zlo >= LEDGE_Z:
        # even hanging straight under the gun the feet clear the ledge: find the swing where they hang lowest
        best = min(((feet_z(sgn * a)[0], a) for a in np.linspace(-0.6, 0.6, 61)))
        z, R = feet_z(sgn * best[1])
        return R
    for _ in range(40):
        mid = (lo + hi) / 2
        z, _ = feet_z(sgn * mid)
        if z < LEDGE_Z:
            lo = mid
        else:
            hi = mid
    return feet_z(sgn * hi)[1]


# ---------------------------------------------------------------------------------------------- body
def kneel_legs(arm, yaw, ro, lift=0.0):
    """Right knee down on the floor (its pad), the shin back along it, the foot on its toes; left foot planted forward.
    `ro`: the root's offset (the hips' height follows from it)."""
    q = rz(yaw)
    fwd = q @ V(0, -1, 0)
    rgt = q @ V(-1, 0, 0)
    aims = {}
    hip = {s: ROOT + ro + q @ (VV(J["hip_" + s]) - ROOT) for s in ("R", "L")}
    lt, ls = bone_len(arm, "thigh.R"), bone_len(arm, "shin.R")
    # the right knee on the floor, a little ahead of the hip and out
    hz = hip["R"].z - KNEE_Z
    horiz = math.sqrt(max(lt * lt - hz * hz, 0.0004))
    k_dir = (fwd * 0.92 + rgt * 0.38).normalized()
    knee = hip["R"] + k_dir * horiz
    knee.z = KNEE_Z
    back = (-fwd * 0.95 + rgt * 0.15).normalized()
    ank = knee + back * math.sqrt(ls * ls - (ANKLE_R_Z - KNEE_Z) ** 2)
    ank.z = ANKLE_R_Z
    aims.update(leg_aims(arm, "R", ank, pole=knee - hip["R"]))
    aims["foot.R"] = (fwd * 0.45 + V(0, 0, -1.0) + rgt * 0.05).normalized()
    # the left foot planted ahead, its shin near upright, the knee up
    al = hip["L"] + fwd * L_FOOT[0] + q @ V(L_FOOT[1], 0, 0)
    al.z = float(J["ankle_L"][2]) + lift
    aims.update(leg_aims(arm, "L", al, pole=fwd * 1.0 + V(0, 0, 0.4) - rgt * 0.25))
    rest_foot = VV(J["toe_L"]) - VV(J["ankle_L"])
    aims["foot.L"] = rz(yaw + 8) @ rest_foot
    return aims


def torso(aims, yaw_chest, lean=0.0, side=0.0, spine_tw=0.0, chest_tw=0.0, neck_tw=0.0, head_tw=0.0, head_tilt=0.0,
          head_up=0.0, neck_side=0.0):
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.22 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.32 * lean, 1.0), chest_tw)
    aims["neck"] = (q @ V(neck_side, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (q @ V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


def grip(side, fist, along, fdir, palm=None):
    """The hand's "frame" aim and the wrist target that put the fist's grip centre at `fist`, its thumb axis along
    `along`, and its length (wrist to knuckles) as near `fdir` (the forearm) as the grip allows; `palm`: the palm's
    normal instead (the cupped left hand, palm up under the stock)."""
    H = HAND[side]
    t = Vector(along).normalized()
    if palm is not None:
        n = Vector(palm) - t * Vector(palm).dot(t)
        n.normalize()
    else:
        f = Vector(fdir) - t * Vector(fdir).dot(t)
        if f.length < 1e-6:
            f = t.orthogonal()
        f.normalize()
        n = t.cross(f) if side == "R" else f.cross(t)
    R = frame_map(H["t"], t, H["n"], n)
    return Vector(fist) - R @ H["off"], ("frame", H["t"], t, H["n"], n)


def hands_aims(arm, P, holds):
    """holds: {side: (fist, along, pole[, palm])}; P: a solved pose (for the shoulders)."""
    aims = {}
    for side, h in holds.items():
        fist, along, pole = h[:3]
        palm = h[3] if len(h) > 3 else None
        sh = P["upperarm." + side].translation.copy()
        la, lb = bone_len(arm, "upperarm." + side), bone_len(arm, "forearm." + side)
        wrist, fr = grip(side, fist, along, Vector(fist) - sh, palm)
        for it in range(3):
            el = two_bone(sh, wrist, la, lb, pole)
            wrist, fr = grip(side, fist, along, Vector(fist) - el, palm)
        aims.update(arm_aims(arm, side, wrist, pole=pole))
        aims["hand." + side] = fr
    return aims


def prop_world(P_, name, T):
    return ("world", T @ P_.rest[name])


def eye_of(P_, P):
    return P["head"] @ (P_.rest["head"].inverted() @ _EYE_REST)


def solve(P_, arm, aims, ro, rr, holds, props, extra=None):
    ch, P = P_.solve(aims, ro, rr)
    hs = {side: fn(P) for side, fn in holds.items()}
    aims = dict(aims)
    aims.update(hands_aims(arm, P, hs))
    if extra:
        aims.update(extra)
    for nm, fn in props.items():
        aims[nm] = (lambda f: (lambda PP, base: f(PP)))(fn)
    ch, P = P_.solve(aims, ro, rr)
    if TRACE is not None:
        TRACE.append({"P": {k: v.copy() for k, v in P.items()}, "holds": {s: Vector(h[0]) for s, h in hs.items()}})
    return ch, P


def on_rifle(T_m, p_rest, pole, along_rest, palm_rest=None):
    """A hold on the rifle at its (rest-pose) point p_rest, the thumb along along_rest (rest-pose direction)."""
    def fn(P):
        R = rot_of(T_m)
        out = (T_m @ p_rest, (R @ along_rest).normalized(), pole)
        if palm_rest is not None:
            out = out + ((R @ palm_rest).normalized(),)
        return out
    return fn


def rifle_props(P_, T_m, lift=0.0, draw=0.0):
    Bm = bipod_motion(T_m)
    return {"rifle": lambda P: prop_world(P_, "rifle", T_m),
            "bolt": lambda P: prop_world(P_, "bolt", T_m @ bolt_motion(lift, draw)),
            "bipod": lambda P: prop_world(P_, "bipod", Bm @ T_m)}


# ---------------------------------------------------------------------------------------------- the aim
YAW = -35.0                         # his body's turn (the rifle points straight ahead, -y)
KNEE_Z = 0.085                      # the right knee's height (its pad on the floor)
ANKLE_R_Z = 0.225                   # the right ankle (the foot on its toes behind)
L_FOOT = (0.36, 0.06)               # the left ankle: this far ahead of the left hip, this far out
RO = V(0.35, 0.1, -0.49)            # the root's offset on the aim (kneeling)
AIM_DOWN = math.radians(5.5)        # the barrel dips toward the street
POCKET = (0.04, 0.12, 0.04)        # the butt's place: ahead of his right shoulder joint, in toward his chest, up
R_POLE = V(-0.9, 0.35, -0.45)       # his right elbow out and down
L_POLE = V(0.35, -0.3, -1.0)        # his left elbow down under the stock
AIM_BODY = {"lean": 2.4, "side": -0.05, "head_tilt": -0.7, "head_up": -0.45, "neck_side": 0.2, "neck_tw": 0.12,
            "head_tw": 0.18}
GRIP_T = VV(cm.hand_frame("R")[3])   # (the pistol grip's axis = the right fist's thumb axis, rest pose)


def body(arm, br=0.0, sway=0.0, push=0.0, lean=0.0, yaw_off=0.0, ro_off=V(0, 0, 0), head=None):
    """The kneeling body on the aim; `push`: the recoil rocking him back (0..1); `lean`: added lean; `head`: overrides
    for the head aims (the eye solve)."""
    b = dict(AIM_BODY)
    if head:
        b.update(head)
    yaw = YAW + yaw_off
    ro = rz(yaw_off) @ (RO + V(0.0, 0.035 * push, 0.004 * br + 0.01 * push)) + ro_off
    aims = kneel_legs(arm, yaw, ro)
    yc = yaw + 2.0 * push + 0.6 * sway
    rr = rz(yaw)
    torso(aims, yc, lean=b["lean"] + lean - 0.25 * push, side=b["side"], spine_tw=math.radians(-4), chest_tw=math.radians(-8),
          neck_tw=b["neck_tw"], head_tw=b["head_tw"], head_tilt=b["head_tilt"], head_up=b["head_up"], neck_side=b["neck_side"])
    aims["clavicle.L"] = rz(yc) @ V(1.0, -0.35, 0.02)
    aims["clavicle.R"] = rz(yc) @ V(-1.0, 0.0, 0.12 + 0.05 * push)
    return aims, ro, rr


def aim_rifle(P, kick=0.0, back=0.0, sway=0.0, br=0.0, yaw_off=0.0):
    """The rifle on the aim: the butt in his right shoulder's pocket, the barrel toward the robots (-y, turned by
    `yaw_off`), dipping a little; `kick` turns the muzzle up (radians) and `back` shoves it back along the bore."""
    sh = P["upperarm.R"].translation
    C = P["chest"].to_3x3()
    fwd = C @ V(0, 0, 1)
    fwd.z = 0.0
    fwd.normalize()
    medial = C @ V(1, 0, 0)
    pocket = sh + fwd * POCKET[0] + medial * POCKET[1] + V(0, 0, POCKET[2])
    A_t = rz(yaw_off) @ V(0.006 * sway, -math.cos(AIM_DOWN), -math.sin(AIM_DOWN) + 0.002 * br)
    A_t.normalize()
    if kick:
        A_t = Quaternion(A_t.cross(V(0, 0, 1)).normalized(), kick) @ A_t
    U_t = V(0, 0, 1) - A_t * A_t.z
    return rifle_at(BUTT, pocket - A_t * back, A_t, U_t)


def aim_holds(T_m, r_hold=None):
    holds = {"L": on_rifle(T_m, CUP, L_POLE, A_M, U_M)}
    holds["R"] = r_hold or on_rifle(T_m, G_M, R_POLE, GRIP_T)
    return holds


HEAD_KEYS = ("neck_side", "head_tilt", "head_up")


def eye_solve(P_, arm, aims_fn, target_fn, guess, iters=6):
    """Adjust the head's aims (neck_side, head_tilt, head_up) until his right eye sits at target_fn(P) (Gauss-Newton
    with finite differences); returns the head overrides."""
    x = [guess[k] for k in HEAD_KEYS]
    def err(xv):
        aims, ro, rr = aims_fn(dict(zip(HEAD_KEYS, xv)))
        ch, P = P_.solve(aims, ro, rr)
        return eye_of(P_, P) - target_fn(P)
    for _ in range(iters):
        e0 = err(x)
        if e0.length < 0.002:
            break
        Jm = []
        for i in range(3):
            xd = list(x)
            xd[i] += 0.02
            Jm.append((err(xd) - e0) / 0.02)
        Jt = np.array([[Jm[i][r] for i in range(3)] for r in range(3)])
        dx = np.linalg.lstsq(Jt, -np.array(e0[:]), rcond=None)[0]
        dx = np.clip(dx, -0.25, 0.25)
        x = [x[i] + float(dx[i]) for i in range(3)]
    return dict(zip(HEAD_KEYS, x))


_HEAD = {}


def on_scope(arm, P_, br=0.0, sway=0.0, push=0.0, lean=0.0, kick=0.0, back=0.0, yaw_off=0.0, off=0.0, key=None):
    """Body, rifle and head on the aim; `off`: his eye this far up off the eyepiece (0 = on the scope)."""
    def aims_fn(hd):
        return body(arm, br, sway, push, lean, yaw_off, head=hd)
    aims, ro, rr = aims_fn(None)
    ch, P = P_.solve(aims, ro, rr)
    T_m = aim_rifle(P, kick, back, sway, br, yaw_off)
    tgt = lambda P, T_m=T_m: T_m @ EYE + V(0, 0, off) + (rot_of(T_m) @ A_M) * (-0.5 * off)
    g = _HEAD.get(key) or {k: AIM_BODY[k] for k in HEAD_KEYS}
    hd = eye_solve(P_, arm, aims_fn, tgt, g)
    if key is not None:
        _HEAD[key] = hd
    aims, ro, rr = aims_fn(hd)
    return aims, ro, rr, T_m


# ---------------------------------------------------------------------------------------------- Idle
def make_idle(arm, frames=120):
    """Head up off the scope looking about (0-30), down to the scope (30-44), scanning on it (44-96), up again (96-120)."""
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br = math.sin(w * 3)
        k = f % frames
        if k < 30:
            off = 1.0
        elif k < 44:
            off = 1.0 - _ease((k - 30) / 14.0)
        elif k < 96:
            off = 0.0
        else:
            off = _ease((k - 96) / 24.0)
        scan = math.sin(2 * math.pi * max(0.0, min(1.0, (k - 44) / 52.0))) if 44 <= k < 96 else 0.0
        yaw_off = 5.0 * scan
        aims, ro, rr, T_m = on_scope(arm, P_, br=br, lean=-0.18 * off, yaw_off=yaw_off, off=0.11 * off, key="idle%d" % int(off > 0.5))
        if off > 0:
            look = math.sin(2 * math.pi * min(1.0, k / 30.0)) if k < 30 else 0.0
            for nm in ("neck", "head"):
                d, tw = aims[nm]
                aims[nm] = (rz(16.0 * look * off) @ d, tw + 0.2 * look * off)
        ch, _ = solve(P_, arm, aims, ro, rr, aim_holds(T_m), rifle_props(P_, T_m))
        if f == 0:
            ch0 = ch
        P_.key(ch0 if f == frames else ch, f)                 # (the loop closes exactly)
    finish_action(arm, act, frames, True)
    return act


def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------------------------------------- Combat
def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        w = 2 * math.pi * (f % frames) / frames
        br, sw = math.sin(w), math.sin(w + 0.7)
        aims, ro, rr, T_m = on_scope(arm, P_, br=br, sway=sw, key="combat")
        ch, _ = solve(P_, arm, aims, ro, rr, aim_holds(T_m), rifle_props(P_, T_m))
        if f == 0:
            ch0 = ch
        P_.key(ch0 if f == frames else ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- Attack: the shot, the bolt
# per frame: (kick, back, push, eye off, bolt lift 0..1, bolt draw 0..1, right hand: "grip" | "knob" | blend 0..1)
ATTACK = {
    0: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "grip"),
    1: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "grip"),          # SHOT
    2: (0.15, 0.075, 1.0, 0.05, 0.0, 0.0, "grip"),      # the kick
    3: (0.12, 0.06, 0.9, 0.08, 0.0, 0.0, "grip"),
    4: (0.07, 0.035, 0.6, 0.08, 0.0, 0.0, "grip"),
    5: (0.03, 0.015, 0.35, 0.07, 0.0, 0.0, "grip"),
    6: (0.01, 0.005, 0.18, 0.06, 0.0, 0.0, "grip"),
    7: (0.0, 0.0, 0.08, 0.05, 0.0, 0.0, "grip"),
    8: (0.0, 0.0, 0.03, 0.05, 0.0, 0.0, 0.25),
    9: (0.0, 0.0, 0.0, 0.05, 0.0, 0.0, 0.65),
    10: (0.0, 0.0, 0.0, 0.05, 0.0, 0.0, "knob"),        # on the knob
    11: (0.0, 0.0, 0.0, 0.05, 0.55, 0.0, "knob"),
    12: (0.0, 0.0, 0.0, 0.05, 1.0, 0.0, "knob"),        # up
    13: (0.0, 0.0, 0.0, 0.05, 1.0, 0.35, "knob"),
    14: (0.0, 0.0, 0.0, 0.05, 1.0, 0.8, "knob"),
    15: (0.0, 0.0, 0.0, 0.05, 1.0, 1.0, "knob"),        # back (the case flies)
    16: (0.0, 0.0, 0.0, 0.05, 1.0, 0.7, "knob"),
    17: (0.0, 0.0, 0.0, 0.05, 1.0, 0.25, "knob"),
    18: (0.0, 0.0, 0.0, 0.05, 1.0, 0.0, "knob"),        # home
    19: (0.0, 0.0, 0.0, 0.05, 0.45, 0.0, "knob"),
    20: (0.0, 0.0, 0.0, 0.05, 0.0, 0.0, "knob"),        # down
    21: (0.0, 0.0, 0.0, 0.045, 0.0, 0.0, 0.6),
    22: (0.0, 0.0, 0.0, 0.04, 0.0, 0.0, 0.25),
    23: (0.0, 0.0, 0.0, 0.03, 0.0, 0.0, "grip"),        # back on the grip
    24: (0.0, 0.0, 0.0, 0.02, 0.0, 0.0, "grip"),
    25: (0.0, 0.0, 0.0, 0.01, 0.0, 0.0, "grip"),
    26: (0.0, 0.0, 0.0, 0.004, 0.0, 0.0, "grip"),
    27: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "grip"),
    28: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "grip"),
    29: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "grip"),
    30: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "grip"),
}
KNOB_OFF = (0.006, 0.022, 0.012)             # the fist's grip centre from the knob (rifle axes: along, right, up)
R_KNOB_POLE = V(-1.0, 0.1, -0.35)


def knob_hold(T_m, lift, draw):
    """The fist pinching the bolt's knob: just out to its right and over it, the thumb along the barrel."""
    M = T_m @ bolt_motion(lift, draw)
    R = rot_of(M)
    p = M @ KNOB + R @ (A_M * KNOB_OFF[0] + S_M * KNOB_OFF[1] + U_M * KNOB_OFF[2])
    return p, (rot_of(T_m) @ A_M).normalized()


def make_attack(arm, frames=30):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        kick, back, push, off, lift, draw, rh = ATTACK[f]
        aims, ro, rr, T_m = on_scope(arm, P_, push=push, kick=kick, back=back, off=off, key="combat" if off == 0 else None)
        li, dr = LIFT * lift, DRAW * draw
        grip_p = lambda P, T_m=T_m: (T_m @ G_M, (rot_of(T_m) @ GRIP_T).normalized(), R_POLE)
        if rh == "grip":
            r_hold = grip_p
        elif rh == "knob":
            def r_hold(P, T_m=T_m, li=li, dr=dr):
                p, al = knob_hold(T_m, li, dr)
                return (p, al, R_KNOB_POLE)
        else:
            def r_hold(P, T_m=T_m, li=li, dr=dr, k=float(rh)):
                p0, al0, _ = grip_p(P)
                p1, al1 = knob_hold(T_m, li, dr)
                return (p0.lerp(p1, k) + V(0, 0, 0.03) * math.sin(k * math.pi), al0.slerp(al1, k) if hasattr(al0, "slerp") else (al0 * (1 - k) + al1 * k).normalized(),
                        R_POLE.lerp(R_KNOB_POLE, k))
        ch, _ = solve(P_, arm, aims, ro, rr, aim_holds(T_m, r_hold), rifle_props(P_, T_m, li, dr))
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
