"""Glitch's clips (keyed in frames; the game plays them at CLIP_FPS 24).

Idle    : standing easy, blades drawn in, fists loose at his sides; he looks about; a third of the way through the loop he
          glitches (his head jerks and stutters, his shoulders hitch), then raises his right fist and taps the side of his
          head twice, head tilted, as if knocking himself back into tune, and looks about again.
Combat  : light on his feet: a fighter's stance (left foot forward, turned a little to his right), both fists up palm
          down, the blades out and level toward the robots, the left one leading; he bounces on the balls of his feet.
Attack  : (16 frames = 0.67 s, inside the 0.7 s cooldown) the cross slash: both blades flung up and out (0-2), then cut
          down and in together (2-5), crossing in an X before him at HIT (frame 5: game.gd's blow; the blades are at the
          robot from frame 4 to 6), on into a low cross (5-8), and back up into the guard (8-16).
Ability : System Freeze (66 frames): his blades draw in (0-8) and he drops to his right knee (8-18), his right fist
          cocked up beside his head, his left arm out behind him; he drives the fist down into the floor at SIGNAL (frame
          23: his eyes flash, `flash`, and game.gd's wave of glitch static goes out from the fist, `hand.R`), holds it there
          while the static spreads, head up (23-42), rises (42-58), his blades snapping out again (52-60), back to the guard.
Cheer   : (rank up) both blades thrust up in a V, pumped twice with a hop each time, his head rocking side to side.

The blades ride `blade.R` / `blade.L` (children of the forearms); scaled to BLADE_IN along their length they are drawn into
the housings. The arms are posed by their upper arms' and forearms' directions (the slashes) or by the wrist (two-bone IK:
the fist on the floor); each forearm is turned so its palm faces the given direction (the blade lies on the back of the
fist, its flat facing that way too), and the fist follows the forearm (the wrist stays straight)."""
import math
from mathutils import Vector, Quaternion, Matrix
import glitch as cm
from rig import Poser, leg_aims, frame_map, two_bone, bone_len
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

ARM = {}
for _s in "RL":
    _sh, _el, _wr = vec(J["shoulder_" + _s]), vec(J["elbow_" + _s]), vec(J["wrist_" + _s])
    _O, _a, _tt, _nn = cm.blade_axes(_s)
    _w, _f, _n, _t = cm.hand_frame(_s)
    _u0 = (_el - _sh).normalized()
    _a0 = (_wr - _el).normalized()
    ARM[_s] = dict(sh=_sh, el=_el, wr=_wr, u0=_u0, a0=_a0, c0=_u0.cross(_a0).normalized(), nn0=vec(_nn),
                   Lu=(_el - _sh).length, Lf=(_wr - _el).length,
                   knuck=vec(cm.fist_center(_s)) + vec(_f) * 0.062 - _wr,         # the front of the fist (its knuckles)
                   tip=vec(cm.blade_tip(_s)) - _wr)

HIT = 5               # Attack: the blades cross before him (the robot is cut 4-6)
FR = 16               # the Attack's length (0.67 s at 24 fps)
SIGNAL = 23           # Ability: the fist hits the floor, his eyes flash, the static goes out
AB_FR = 66
CH_FR = 48
I_FR = 96
C_FR = 40
BLADE_IN = 0.06       # a drawn-in blade's scale along its length


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mixd(a, b, k):
    a, b = Vector(a).normalized(), Vector(b).normalized()
    if a.dot(b) < -0.999:
        b = b + V(0.0, 0.0, 1e-3)
    return a.slerp(b, k) if hasattr(a, "slerp") else a.lerp(b, k).normalized()


def bez_p(a, b, c, k):
    return a.lerp(b, k).lerp(b.lerp(c, k), k)


def mirror(v):
    return V(-v.x, v.y, v.z)


def perp(v, d):
    """v with its component along d removed (normalized)."""
    d = Vector(d).normalized()
    w = Vector(v) - d * Vector(v).dot(d)
    return w.normalized() if w.length > 1e-5 else Vector(v).orthogonal().normalized()


# ---------------------------------------------------------------------------------------------- limbs
def arm_fk(side, u, d, palm):
    """The upper arm along u (its bend axis kept toward u x d, so the elbow hinges the right way), the forearm along d,
    turned so the palm faces `palm`."""
    A = ARM[side]
    u, d = Vector(u).normalized(), Vector(d).normalized()
    c = u.cross(d)
    if c.length > 0.15:
        up = ("frame", A["u0"], u, A["c0"], c)
    else:
        up = u
    return {"upperarm." + side: up, "forearm." + side: ("frame", A["a0"], d, A["nn0"], perp(palm, d))}


def arm_ik(arm, side, wrist, pole, palm, d_override=None):
    """The wrist at `wrist` (two-bone IK toward `pole`); the forearm along elbow -> wrist, its palm toward `palm`."""
    la, lb = bone_len(arm, "upperarm." + side), bone_len(arm, "forearm." + side)
    A = ARM[side]
    st = {}
    wrist = Vector(wrist)
    def upper(P, base):
        sh = base.translation
        e = two_bone(sh, wrist, la, lb, Vector(pole))
        st["el"] = e
        return e - sh
    def fore(P, base):
        d = (wrist - st["el"]).normalized() if d_override is None else Vector(d_override)
        return ("frame", A["a0"], d, A["nn0"], perp(palm, d))
    return {"upperarm." + side: upper, "forearm." + side: fore}


def fore_rot(side, d, palm):
    """The forearm's (and fist's) rotation from rest for a forearm along d with its palm toward `palm`."""
    A = ARM[side]
    return frame_map(A["a0"], Vector(d), A["nn0"], perp(palm, d))


def feet(arm, yaw, lf=(0.19, -0.03), rf=(-0.19, 0.05), lift=(0.0, 0.0), turn=(10.0, -10.0)):
    q = rz(yaw)
    aims = {}
    for side, (bx, by), up, tw in (("L", lf, lift[0], turn[0]), ("R", rf, lift[1], turn[1])):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + up)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw + tw) @ (rest_foot + V(0, 0, -up * 0.9))
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0):
    """Spine and chest bent forward by `bend` radians and to his left by `side`, the chest turned `chest` degrees more;
    the head turned to the world heading `look`, pitched up by `pitch` and rolled by `roll` (to his left)."""
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(math.sin(roll) * 0.5, -0.1 - 0.2 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.04 + 0.7 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.03, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.03, 0.02)


def blades(s_r, s_l=None, flash=0.0):
    s_l = s_r if s_l is None else s_l
    return {"blade.R": (1.0, s_r, 1.0), "blade.L": (1.0, s_l, 1.0), "flash": flash}


# ---------------------------------------------------------------------------------------------- the guard (Combat)
C_YAW = -18.0
C_FEET = dict(lf=(0.19, -0.15), rf=(-0.2, 0.15), turn=(4.0, -24.0))
DOWN = V(0.0, 0.0, -1.0)
# (upper arm, forearm, palm) in body space: fists up before his chest, palms down, blades level toward the robots
G_L = (V(0.42, -0.42, -0.8), V(-0.3, -0.92, 0.22), DOWN)
G_R = (V(-0.36, -0.18, -0.92), V(0.36, -0.86, 0.36), DOWN)


def guard_arms(yaw, bob=0.0, k=1.0, base=None):
    """Both arms in the guard (k = 1), or blended from `base` (dict side -> (u, d, palm), body space) toward it."""
    q = rz(yaw)
    aims = {}
    for side, g in (("L", G_L), ("R", G_R)):
        u, d, palm = g
        d = (d + V(0.0, 0.0, 0.05 * bob)).normalized()
        if base is not None and k < 1.0:
            u0, d0, p0 = base[side]
            u, d, palm = mixd(u0, u, k), mixd(d0, d, k), mixd(p0, palm, k)
        aims.update(arm_fk(side, q @ u, q @ d, q @ palm))
    return aims


def combat_pose(arm, t):
    w = 2 * math.pi * t
    hop = abs(math.sin(w * 2))                       # bouncing on the balls of his feet, twice a loop
    ro = V(0.0, 0.0, -0.075 + 0.028 * hop)
    yaw = C_YAW + 2.5 * math.sin(w)
    aims = feet(arm, C_YAW, lift=(0.02 * hop, 0.03 * hop), **C_FEET)
    torso(aims, yaw, bend=0.16, chest=-4.0, look=0.0, pitch=0.06 - 0.02 * hop)
    aims.update(guard_arms(yaw, math.sin(w * 2 + 0.6)))
    return aims, ro, rz(yaw), blades(1.0)


# ---------------------------------------------------------------------------------------------- attack: the cross slash
# keys (frame: (u, d, palm) for the right arm, body space; the left mirrors it, a little lower so the blades pass
# under the right one)
WIND_R = (V(-0.62, 0.08, 0.4), V(-0.2, 0.0, 1.0), V(0.95, 0.1, 0.1))          # flung up and out, the blade over his shoulder
HIT_R = (V(-0.22, -0.8, -0.5), V(0.72, -0.64, -0.1), V(0.25, 0.25, 0.94))     # cutting in across his front
LOW_R = (V(0.05, -0.7, -0.7), V(0.74, -0.3, -0.5), V(0.5, 0.5, 0.7))          # on through, into a low cross
BACK_R = (V(-0.32, -0.62, -0.72), V(0.1, -0.85, 0.5), V(-0.2, 0.3, -0.93))     # (back up: the right blade rising ...)
BACK_L = (V(0.34, -0.5, -0.8), V(-0.05, -0.85, -0.5), V(0.2, 0.4, -0.9))      # (... over the left one, still low)


def _mir(key, dz=0.0):
    u, d, p = key
    return (mirror(u), (mirror(d) + V(0.0, 0.0, dz)).normalized(), mirror(p))


def attack_keys(f):
    """(right (u, d, palm), left (u, d, palm), yaw, chest, bend, crouch, lunge) at frame f (the left arm mirrors the
    right one, a little lower, so its blade passes under the right one)."""
    gR, gL = G_R, G_L
    wR, wL = WIND_R, _mir(WIND_R)
    hR, hL = HIT_R, _mir(HIT_R, -0.16)
    lR, lL = LOW_R, _mir(LOW_R, -0.2)
    def blend(a, b, k):
        return tuple(mixd(x, y, k) for x, y in zip(a, b))
    if f <= 2:
        k = ease(f / 2.0)
        return blend(gR, wR, k), blend(gL, wL, k), lerp(C_YAW, -8.0, k), lerp(-4.0, 6.0, k), lerp(0.16, -0.06, k), lerp(0.075, 0.03, k), 0.0
    if f <= HIT:
        k = (f - 2) / float(HIT - 2)
        k = k ** 1.2
        return blend(wR, hR, k), blend(wL, hL, k), lerp(-8.0, 0.0, k), lerp(6.0, 0.0, k), lerp(-0.06, 0.26, k), lerp(0.03, 0.12, k), 0.07 * k
    if f <= 8:
        k = ease((f - HIT) / 3.0)
        return blend(hR, lR, k), blend(hL, lL, k), 0.0, 0.0, lerp(0.26, 0.34, k), lerp(0.12, 0.14, k), 0.07 + 0.02 * k
    if f <= 11:
        k = ease((f - 8) / 3.0)
        return (blend(lR, BACK_R, k), blend(lL, BACK_L, k), lerp(0.0, C_YAW * 0.4, k), lerp(0.0, -2.0, k), lerp(0.34, 0.24, k),
                lerp(0.14, 0.11, k), 0.09 - 0.03 * k)
    k = ease((f - 11) / float(FR - 11))
    return (blend(BACK_R, gR, k), blend(BACK_L, gL, k), lerp(C_YAW * 0.4, C_YAW, k), lerp(-2.0, -4.0, k), lerp(0.24, 0.16, k),
            lerp(0.11, 0.075, k), 0.06 * (1 - k))


def attack_pose(arm, f):
    r, l, yaw, chest, bend, crouch, lunge = attack_keys(f)
    q = rz(yaw)
    ro = V(0.0, 0.0, -crouch) + q @ V(0.0, -lunge, 0.0)
    aims = feet(arm, C_YAW, lift=(0.0, 0.03 * min(1.0, lunge / 0.07)), **C_FEET)
    torso(aims, yaw, bend=bend, chest=chest, look=0.0, pitch=0.06 - 0.25 * max(bend - 0.1, 0.0))
    aims.update(arm_fk("R", q @ r[0], q @ r[1], q @ r[2]))
    aims.update(arm_fk("L", q @ l[0], q @ l[1], q @ l[2]))
    return aims, ro, q, blades(1.0)


# ---------------------------------------------------------------------------------------------- ability: System Freeze
KNEE_Z = 0.1                 # the right knee's joint, kneeling (its cop on the floor)
ANKLE_R_Z = 0.22             # the right ankle behind it (the foot on its toes)
L_FOOT = (0.3, 0.04)         # the left foot planted ahead (forward, out)
KNEEL_RO = V(0.0, -0.04, -0.53)
PUNCH_PT = V(-0.42, -0.36, 0.012)      # the knuckles on the floor (body space; the floor = his soles' level)
PUNCH_D = V(0.04, -0.12, -1.0)         # the forearm driving down
COCK_R = (V(-0.75, 0.25, 0.42), V(0.1, 0.15, 1.0), V(0.9, -0.3, 0.0))       # the right fist cocked up beside his head
BAL_L = (V(0.7, 0.45, -0.3), V(0.6, 0.62, -0.1), V(0.0, 0.3, -1.0))          # the left arm out behind him


def kneel_legs(arm, yaw, ro, k):
    """Blend (k) from the standing feet (yaw 0) to the right knee down, the left foot planted ahead."""
    q = rz(yaw)
    fwd = q @ V(0, -1, 0)
    rgt = q @ V(-1, 0, 0)
    aims = {}
    hip = {s: ROOT + ro + q @ (vec(J["hip_" + s]) - ROOT) for s in ("R", "L")}
    lt, ls = bone_len(arm, "thigh.R"), bone_len(arm, "shin.R")
    stand = {"R": ROOT + q @ (V(-0.19, 0.05 - ROOT.y, 0.0)), "L": ROOT + q @ V(0.19, -0.03 - ROOT.y, 0.0)}
    # right: the knee down on the floor ahead of the hip, the shin back along it, the foot on its toes
    hz = hip["R"].z - KNEE_Z
    horiz = math.sqrt(max(lt * lt - hz * hz, 0.0004))
    knee = hip["R"] + (fwd * 0.97 + rgt * 0.08).normalized() * horiz
    knee.z = KNEE_Z
    back = (-fwd * 0.97 + rgt * 0.12).normalized()
    ank = knee + back * math.sqrt(max(ls * ls - (ANKLE_R_Z - KNEE_Z) ** 2, 1e-4))
    ank.z = ANKLE_R_Z
    a_st = V(stand["R"].x, stand["R"].y, float(J["ankle_R"][2]))
    a_r = a_st.lerp(ank, k)
    pole_r = (q @ V(-0.15, -1.0, 0.1)).lerp(knee - hip["R"], k)
    aims.update(leg_aims(arm, "R", a_r, pole=pole_r))
    rest_foot = vec(J["toe_R"]) - vec(J["ankle_R"])
    aims["foot.R"] = mixd(rz(yaw - 10) @ rest_foot, (fwd * 0.6 + V(0, 0, -1.0)), k)
    # left: the foot planted ahead, the knee up
    al = hip["L"] + fwd * L_FOOT[0] + q @ V(L_FOOT[1], 0, 0)
    al.z = float(J["ankle_L"][2])
    a_st = V(stand["L"].x, stand["L"].y, float(J["ankle_L"][2]))
    aims.update(leg_aims(arm, "L", a_st.lerp(al, k), pole=(q @ V(0.15, -1.0, 0.1)).lerp(fwd + V(0, 0, 0.5) - rgt * 0.3, k)))
    aims["foot.L"] = rz(yaw + 8) @ (vec(J["toe_L"]) - vec(J["ankle_L"]))
    return aims


def reach(S, K, pole, palm, d_guess, side="R"):
    """(upper arm, forearm) directions putting the fist's knuckles on K from the shoulder S (two-bone IK on the wrist,
    refined for the fist's offset from it)."""
    A = ARM[side]
    d = Vector(d_guess).normalized()
    for _ in range(4):
        W = K - fore_rot(side, d, palm) @ A["knuck"]
        E = two_bone(S, W, A["Lu"], A["Lf"], Vector(pole))
        d = (W - E).normalized()
    return (E - S).normalized(), d


def punch_point():
    """The knuckles' target on the floor (character space: he faces the base's front)."""
    return PUNCH_PT.copy()


def ability_state(f):
    """(phase, k)."""
    if f <= 8:
        return "draw", ease(f / 8.0)
    if f <= 18:
        return "kneel", ease((f - 8) / 10.0)
    if f <= SIGNAL:
        return "punch", ((f - 18) / float(SIGNAL - 18)) ** 1.6
    if f <= 42:
        return "hold", (f - SIGNAL) / float(42 - SIGNAL)
    if f <= 58:
        return "rise", ease((f - 42) / 16.0)
    return "guard", ease((f - 58) / float(AB_FR - 58))


def flash_scale(f):
    if f < SIGNAL:
        return 0.0
    x = f - SIGNAL
    if x == 0:
        return 1.0
    if x <= 2:
        return 1.25
    return max(0.0, 1.25 * (1.0 - (x - 2) / 9.0))


STATE = {}
PUNCH_POLE = V(-1.0, 0.7, 0.25)


def ability_pose(arm, f):
    """(aims, root offset, root rotation, scales, late): `late` = {side: fn(shoulder) -> (u, d, palm)} for arms that are
    placed from the posed shoulder (solved in a first pass)."""
    phase, k = ability_state(f)
    q0 = rz(C_YAW)
    late = {}
    if phase == "draw":
        yaw = lerp(C_YAW, 0.0, k)
        ro = V(0.0, 0.0, lerp(-0.075, -0.04, k))
        aims = feet(arm, lerp(C_YAW, 0.0, k), lf=tuple(lerp(a, b, k) for a, b in zip(C_FEET["lf"], (0.19, -0.03))),
                    rf=tuple(lerp(a, b, k) for a, b in zip(C_FEET["rf"], (-0.19, 0.05))), turn=(lerp(4.0, 10.0, k), lerp(-24.0, -10.0, k)))
        torso(aims, yaw, bend=lerp(0.16, 0.06, k), look=0.0, pitch=0.05)
        aims.update(arm_fk("R", mixd(q0 @ G_R[0], COCK_R[0], 0.4 * k), mixd(q0 @ G_R[1], COCK_R[1], 0.4 * k), mixd(q0 @ G_R[2], COCK_R[2], k)))
        aims.update(arm_fk("L", mixd(q0 @ G_L[0], BAL_L[0], 0.3 * k), mixd(q0 @ G_L[1], BAL_L[1], 0.3 * k), mixd(q0 @ G_L[2], BAL_L[2], k)))
        return aims, ro, rz(yaw), blades(lerp(1.0, BLADE_IN, k)), late
    if phase in ("kneel", "punch", "hold"):
        kk = k if phase == "kneel" else 1.0
        ro = V(0.0, 0.0, -0.04).lerp(KNEEL_RO, kk)
        tremor = 0.0
        if phase == "hold":
            tremor = math.sin(f * 2.3) * (1.0 - k) * 0.006
            ro = ro + V(tremor, 0.0, -0.006 * math.sin(math.pi * min(1.0, k * 3)))
        aims = kneel_legs(arm, 0.0, ro, kk)
        bend = {"kneel": lerp(0.06, 0.35, kk), "punch": lerp(0.35, 0.74, k), "hold": 0.74}[phase]
        side = {"kneel": lerp(0.0, -0.08, kk), "punch": lerp(-0.08, -0.3, k), "hold": -0.3}[phase]
        pitch = {"kneel": lerp(0.05, 0.2, kk), "punch": lerp(0.2, 0.62, k), "hold": 0.62}[phase]
        torso(aims, 0.0, bend=bend, side=side, look=0.0, pitch=pitch + tremor * 3)
        cock = (mixd(q0 @ G_R[0], COCK_R[0], 0.4), mixd(q0 @ G_R[1], COCK_R[1], 0.4), COCK_R[2])
        if phase == "kneel":
            aims.update(arm_fk("R", mixd(cock[0], COCK_R[0], kk), mixd(cock[1], COCK_R[1], kk), COCK_R[2]))
        else:
            K1 = punch_point()
            palm1 = V(1.0, 0.0, 0.0)
            def right(S, P0=None, phase=phase, k=k):
                A = ARM["R"]
                u0, d0 = COCK_R[0].normalized(), COCK_R[1].normalized()
                if phase == "punch":
                    # the knuckles from the cocked fist down onto the floor, on a curve
                    W0 = S + u0 * A["Lu"] + d0 * A["Lf"]
                    K0 = W0 + fore_rot("R", d0, COCK_R[2]) @ A["knuck"]
                    K = bez_p(K0, K0.lerp(K1, 0.5) + V(0.0, -0.12, 0.1), K1, k)
                    palm = mixd(COCK_R[2], palm1, k)
                    u, d = reach(S, K, PUNCH_POLE, palm, mixd(d0, PUNCH_D, k))
                    if k < 0.3:                      # (eased out of the cocked pose)
                        b = smooth01(k / 0.3)
                        u, d = mixd(u0, u, b), mixd(d0, d, b)
                    return u, d, palm
                u, d = reach(S, K1, PUNCH_POLE, palm1, PUNCH_D)
                STATE["hold"] = (u, d, palm1)
                return u, d, palm1
            late["R"] = right
        aims.update(arm_fk("L", mixd(mixd(q0 @ G_L[0], BAL_L[0], 0.3), BAL_L[0], kk), mixd(mixd(q0 @ G_L[1], BAL_L[1], 0.3), BAL_L[1], kk),
                           BAL_L[2]))
        return aims, ro, rz(0.0), blades(BLADE_IN, flash=flash_scale(f)), late
    if phase == "rise":
        ro = KNEEL_RO.lerp(V(0.0, 0.0, -0.075), k)
        yaw = lerp(0.0, C_YAW, k)
        aims = kneel_legs(arm, 0.0, ro, 1.0 - k)
        torso(aims, yaw, bend=lerp(0.74, 0.16, k), side=lerp(-0.3, 0.0, k), chest=lerp(0.0, -4.0, k), look=0.0, pitch=lerp(0.62, 0.06, k))
        q = rz(yaw)
        uh, dh, ph = STATE.get("hold", (V(-0.2, -0.3, -0.93), PUNCH_D, V(1.0, 0.0, 0.0)))
        kr = smooth01(k * 1.15)
        aims.update(arm_fk("R", mixd(uh, q @ G_R[0], kr), mixd(dh, q @ G_R[1], kr), mixd(ph, q @ G_R[2], kr)))
        aims.update(arm_fk("L", mixd(BAL_L[0], q @ G_L[0], k), mixd(BAL_L[1], q @ G_L[1], k), mixd(BAL_L[2], q @ G_L[2], k)))
        return aims, ro, q, blades(lerp(BLADE_IN, 1.0, smooth01((f - 52) / 8.0))), late
    # settle into the guard (the feet step into the stance)
    ro = V(0.0, 0.0, -0.075)
    yaw = C_YAW
    aims = feet(arm, lerp(0.0, C_YAW, k), lf=tuple(lerp(a, b, k) for a, b in zip((0.19, -0.03), C_FEET["lf"])),
                rf=tuple(lerp(a, b, k) for a, b in zip((-0.19, 0.05), C_FEET["rf"])), turn=(lerp(10.0, 4.0, k), lerp(-10.0, -24.0, k)),
                lift=(0.03 * math.sin(math.pi * k), 0.0))
    torso(aims, yaw, bend=0.16, chest=-4.0, look=0.0, pitch=0.06)
    aims.update(guard_arms(yaw))
    return aims, ro, rz(yaw), blades(lerp(BLADE_IN, 1.0, smooth01((f - 52) / 8.0))), late


# ---------------------------------------------------------------------------------------------- idle
REST_R = (V(-0.28, 0.06, -0.96), V(-0.1, -0.3, -0.95), V(0.95, 0.1, 0.0))     # hanging loose, palms in
REST_L = (mirror(REST_R[0]), mirror(REST_R[1]), mirror(REST_R[2]))
EAR_R = vec(cm.hp((-0.176, 0.036, 1.69)))                                     # his right ear disc (rest)
_HB = None
HEAD_REST_INV = None


def _head_rest(arm):
    global HEAD_REST_INV
    HEAD_REST_INV = arm.data.bones["head"].matrix_local.inverted()


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    gl = smooth01((t - 0.3) / 0.02) * (1.0 - smooth01((t - 0.4) / 0.03))           # the glitch
    jit = (1.0 if math.sin(t * 2 * math.pi * 21) > 0 else -1.0) * gl
    tap = smooth01((t - 0.44) / 0.07) * (1.0 - smooth01((t - 0.74) / 0.07))        # tapping his head back into tune
    knock = max(0.0, math.sin((t - 0.5) / 0.18 * 2 * math.pi * 2)) * smooth01((t - 0.49) / 0.02) * (1.0 - smooth01((t - 0.68) / 0.02))
    yaw = 2.5 * math.sin(w) + 3.0 * tap
    ro = V(0.0, 0.0, -0.018 + 0.004 * br + 0.006 * gl)
    aims = feet(arm, 0.0)
    look = (24.0 * math.sin(w + 0.4) + 6.0 * math.sin(w * 3)) * (1.0 - tap) * (1.0 - gl) + 9.0 * jit + 8.0 * tap
    roll = 0.22 * jit + 0.26 * tap + 0.05 * knock
    torso(aims, yaw, bend=0.03, side=0.02 * math.sin(w) - 0.04 * tap, look=look, pitch=0.03 * br - 0.06 * jit + 0.04 * tap, roll=roll)
    if gl > 0:
        aims["clavicle.L"] = rz(yaw) @ V(1.0, -0.03, 0.02 + 0.25 * gl * (0.5 + 0.5 * jit))
        aims["clavicle.R"] = rz(yaw) @ V(-1.0, -0.03, 0.02 + 0.25 * gl * (0.5 - 0.5 * jit))
    q = rz(yaw)
    sway = 0.04 * math.sin(w)
    aims.update(arm_fk("R", q @ (REST_R[0] + V(0, sway, 0)), q @ REST_R[1], q @ REST_R[2]))
    aims.update(arm_fk("L", q @ (REST_L[0] + V(0, -sway, 0)), q @ REST_L[1], q @ REST_L[2]))
    late = {}
    if tap > 0.0:
        def right(S, P0, tap=tap, knock=knock, q=q, sway=sway):
            # the fist's knuckles by his right ear (it taps twice), the palm toward his head
            H = P0["head"] @ HEAD_REST_INV
            ear = H @ EAR_R
            out = (H.to_3x3() @ V(-1.0, 0.1, 0.1)).normalized()
            K = ear + out * (0.085 - 0.04 * knock) + V(0.0, -0.02, 0.02)
            u1, d1 = reach(S, K, q @ V(-1.0, 0.4, -0.5), -out, q @ V(0.3, -0.2, 0.9))
            u0, d0 = q @ (REST_R[0] + V(0, sway, 0)), q @ REST_R[1]
            return mixd(u0, u1, tap), mixd(d0, d1, tap), mixd(q @ REST_R[2], -out, tap)
        late["R"] = right
    return aims, ro, q, blades(BLADE_IN), late


# ---------------------------------------------------------------------------------------------- cheer
UP_R = (V(-0.5, 0.0, 0.87), V(-0.28, -0.12, 1.0), V(0.95, 0.0, 0.2))          # thrust up in a V


def cheer_pose(arm, f):
    t = f / float(CH_FR)
    up = smooth01(t / 0.16) * (1.0 - smooth01((t - 0.84) / 0.16))
    pump = max(0.0, math.sin((t - 0.16) / 0.64 * 2 * math.pi * 2)) * smooth01((t - 0.14) / 0.05) * (1.0 - smooth01((t - 0.78) / 0.05))
    hop = 0.05 * pump
    yaw = lerp(C_YAW, 0.0, up)
    ro = V(0.0, 0.0, -0.03 + hop - 0.045 * (1.0 - up))
    aims = feet(arm, yaw * 0.0 + lerp(C_YAW, 0.0, up), lf=tuple(lerp(a, b, up) for a, b in zip(C_FEET["lf"], (0.19, -0.03))),
                rf=tuple(lerp(a, b, up) for a, b in zip(C_FEET["rf"], (-0.19, 0.05))), lift=(hop * 0.6, hop * 0.6),
                turn=(lerp(4.0, 10.0, up), lerp(-24.0, -10.0, up)))
    torso(aims, yaw, bend=lerp(0.16, -0.06, up), look=0.0, pitch=0.06 + 0.32 * up, roll=0.16 * math.sin(t * 2 * math.pi * 2.5) * up)
    q = rz(yaw)
    lift = V(0.0, 0.0, 0.25 * pump)
    for side, gk, uk in (("R", G_R, UP_R), ("L", G_L, (mirror(UP_R[0]), mirror(UP_R[1]), mirror(UP_R[2])))):
        u = mixd(rz(C_YAW) @ gk[0], uk[0] + lift, up)
        d = mixd(rz(C_YAW) @ gk[1], uk[1] + lift * 0.4, up)
        aims.update(arm_fk(side, u, d, mixd(rz(C_YAW) @ gk[2], uk[2], up)))
    return aims, ro, q, blades(1.0)


# ---------------------------------------------------------------------------------------------- clips
def solve_frame(P, arm, fn, x):
    """(`late` arms get the shoulder and the first pass's posed matrices.) Solve one frame: a first pass places the shoulders for arms placed from them (`late`), a second the whole pose."""
    if HEAD_REST_INV is None:
        _head_rest(arm)
    out = fn(arm, x)
    aims, ro, rr, sc = out[:4]
    late = out[4] if len(out) > 4 else {}
    if late:
        _, P0 = P.solve(aims, ro, rr, scales=sc)
        for side, g in late.items():
            u, d, palm = g(P0["upperarm." + side].translation.copy(), P0)
            aims.update(arm_fk(side, u, d, palm))
    ch, Pm = P.solve(aims, ro, rr, scales=sc)
    return ch, Pm


def _clip(arm, name, frames, fn, cyclic):
    P = Poser(arm)
    act = new_action(arm, name)
    STATE.clear()
    for f in range(frames + 1):
        x = (f % frames) / frames if cyclic else f
        ch, _ = solve_frame(P, arm, fn, x)
        P.key(ch, f)
    finish_action(arm, act, frames, cyclic)
    return act


def make_idle(arm):
    return _clip(arm, "Idle", I_FR, idle_pose, True)


def make_combat(arm):
    return _clip(arm, "Combat", C_FR, combat_pose, True)


def make_attack(arm):
    return _clip(arm, "Attack", FR, attack_pose, False)


def make_ability(arm):
    return _clip(arm, "Ability", AB_FR, ability_pose, False)


def make_cheer(arm):
    return _clip(arm, "Cheer", CH_FR, cheer_pose, False)


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
