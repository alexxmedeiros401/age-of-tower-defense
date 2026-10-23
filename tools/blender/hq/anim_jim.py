"""Big Jim's clips (keyed in frames; the game plays them at CLIP_FPS 24).

Idle    : leaning on his maul: its head on the ballast before his toes, his fists stacked on the end of its handle; he
          breathes and looks about, and once a loop throws his head back in a booming laugh, his shoulders shaking.
Combat  : the maul ready: feet wide, knees bent, turned a little to his right, the maul raised over his right shoulder
          in both fists, its head up behind him; he bobs with its weight.
Attack  : (16 frames, inside the 0.7 s cooldown) a short, heavy overhead blow: he heaves it a little further back
          (0-3), brings it over and down in front of him (3-7), the head landing about 1.3 m out at HIT (frame 7, held
          to 9: game.gd's blow), and hauls it back up over his shoulder into the ready stance (9-16).
Ability : Steam Blast (66 frames; game.gd turns his yaw to the base's front first, as Tarek's anvil): he turns to the
          valve standpipe at the front-left of the track (jim_base.VALVE), swings the maul high overhead and slams it
          down on the red striker cap at SLAM (frame 25: the valve bursts open, game.gd's blast goes off from
          VALVE_POINT), leans on it while the steam roars, then straightens with the maul on his shoulder, laughing,
          and turns back to the ready stance.
Cheer   : (rank up) the maul heaved up over his head in both fists, across, pumped twice, his head thrown back laughing.

The maul is rigid on the `maul` bone in his right fist (his lower hand, at the butt); his left fist closes on the handle
LEFT_ON further up, placed every frame from the maul's pose. The maul's pose is given by its grip, its handle's
direction and its striking face's direction (the face that leads the swing)."""
import math
from mathutils import Vector, Quaternion
import jim as cm
import jim_base as jb
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
_G, _A, _B = cm.maul_frame()
A_REST, B_REST = vec(_A), vec(_B)
_wr, _f, _n, _t = cm.hand_frame("R")
FIST_OFF_R = vec(_G - _wr)
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
TL_REST, FL_REST = vec(_tL), vec(_fL)
FIST_OFF_L = vec(cm.fist_center("L") - _wrL)
MAUL_L = cm.MAUL_L
HEAD_HALF = cm.HEAD_HALF
LEFT_ON = 0.24          # his left fist this far up the handle from his right

HIT = 7                 # the Attack's blow (held to 9)
FR = 16                 # the Attack's length (0.67 s at 24 fps)
SLAM = 25               # the Ability: the maul on the valve
AB_FR = 66
CH_FR = 48
I_FR = 96
# the valve's striker cap in character space (the base's front = his front, his feet at z = 0)
VALVE_CS = V(jb.VALVE[0], jb.VALVE[1], jb.VALVE_TOP - jb.TOP_Z + 0.004)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mixd(a, b, k):
    return a.normalized().lerp(b.normalized(), k).normalized()


def bez_p(a, b, c, k):
    return a.lerp(b, k).lerp(b.lerp(c, k), k)


def swing_axes(dirn, tilt=0.0):
    """The swing's plane: U up (tilted toward his right by `tilt` radians), W forward along `dirn` (horizontal)."""
    W = V(dirn.x, dirn.y, 0.0).normalized()
    right = W.cross(V(0, 0, 1))                 # (his right, looking along W)
    U = (V(0, 0, 1) * math.cos(tilt) + right * math.sin(tilt)).normalized()
    W = (W - U * W.dot(U)).normalized()
    return U, W


def swing_dirs(phi, U, W):
    """Handle direction and striking-face direction at swing angle phi (degrees from straight up, toward the front)."""
    p = math.radians(phi)
    haft = U * math.cos(p) + W * math.sin(p)
    face = -U * math.sin(p) + W * math.cos(p)
    return haft.normalized(), face.normalized()


def two_hands(arm, grip, haft, face, ro, yaw, left_on=LEFT_ON):
    """Both fists on the handle: the right at `grip` (the handle along `haft`, the striking face toward `face`), the left
    `left_on` along the handle from it, its wrist straight (its fingers along the line from its shoulder)."""
    hd = Vector(haft).normalized()
    aims = arm_aims(arm, "R", Vector(grip) - frame_map(A_REST, hd, B_REST, Vector(face)) @ FIST_OFF_R,
                    pole=rz(yaw) @ V(-0.9, 0.2, -0.6))
    aims["hand.R"] = ("frame", A_REST, hd, B_REST, Vector(face))
    gl = Vector(grip) + hd * left_on
    sh_l = body_pt(J["shoulder_L"], ro, yaw)
    fl = gl - sh_l
    fl = fl - hd * fl.dot(hd)
    if fl.length < 1e-4:
        fl = rz(yaw) @ V(0.0, -1.0, 0.0)
    RL = frame_map(TL_REST, hd, FL_REST, fl)
    aims.update(arm_aims(arm, "L", gl - RL @ FIST_OFF_L, pole=rz(yaw) @ V(0.9, 0.2, -0.6)))
    aims["hand.L"] = ("frame", TL_REST, hd, FL_REST, fl)
    return aims


def feet(arm, yaw, lf=(0.22, -0.04), rf=(-0.22, 0.05), lift=(0.0, 0.0), turn=(10.0, -10.0)):
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


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0):
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


# ---------------------------------------------------------------------------------------------- idle: leaning on it
IDLE_HEAD = V(-0.03, -0.47, 0.058)        # the maul's head on the ballast before his toes (the robots' frame)
IDLE_HAFT = V(0.0, 0.08, 1.0).normalized()
IDLE_G = IDLE_HEAD + IDLE_HAFT * MAUL_L   # (the grip, up the handle from the head)
IDLE_FACE = V(1.0, 0.0, 0.0)              # the head lying across in front of him


def laugh_k(t, t0, t1):
    return smooth01((t - t0) / 0.05) * (1.0 - smooth01((t - t1) / 0.06))


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    lk = laugh_k(t, 0.5, 0.74)                                  # the booming laugh
    shake = math.sin(t * 2 * math.pi * 22) * lk
    yaw = 3.0 * sway * (1 - lk)
    ro = V(0.0, -0.02, -0.025 + 0.006 * br + 0.01 * shake + 0.012 * lk)
    aims = feet(arm, 0.0, lf=(0.23, -0.02), rf=(-0.23, 0.04), turn=(14.0, -14.0))
    look = (22.0 * math.sin(w + 0.5) + 6.0 * math.sin(w * 3)) * (1.0 - lk)
    torso(aims, yaw, bend=0.12 - 0.1 * lk, side=-0.02 * sway, look=look, pitch=0.02 * br + 0.42 * lk + 0.03 * shake)
    aims.update(two_hands(arm, IDLE_G, -IDLE_HAFT, IDLE_FACE, ro, yaw, left_on=-0.115))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- combat: ready
C_YAW = -32.0
C_FEET = dict(lf=(0.25, -0.16), rf=(-0.24, 0.17), turn=(-4.0, -24.0))
C_TILT = 0.42                             # the swing's plane leans out to his right (the handle clear of his head)
COCK_G = V(-0.2, -0.13, 1.25)             # the grip at the ready (the robots' frame, before the crouch)
COCK_PHI = -40.0                          # the handle up and back over his right shoulder


def cock_state(yaw=C_YAW):
    U, W = swing_axes(rz(yaw) @ V(0, -1, 0), C_TILT)
    haft, face = swing_dirs(COCK_PHI, U, W)
    return COCK_G, haft, face


def combat_pose(arm, t):
    w = 2 * math.pi * t
    bob = math.sin(w * 2)
    sway = math.sin(w)
    ro = V(0.0, 0.0, -0.085 + 0.012 * bob)
    aims = feet(arm, C_YAW, **C_FEET)
    torso(aims, C_YAW + 2.0 * sway, bend=0.12, chest=-6.0, look=0.0, pitch=0.05)
    g, haft, face = cock_state()
    U, W = swing_axes(rz(C_YAW) @ V(0, -1, 0), C_TILT)
    haft, face = swing_dirs(COCK_PHI + 3.0 * bob, U, W)
    aims.update(two_hands(arm, g + ro + V(0.006 * sway, 0.0, 0.008 * bob), haft, face, ro, C_YAW + 2.0 * sway))
    return aims, ro, rz(C_YAW + 2.0 * sway)


# ---------------------------------------------------------------------------------------------- attack: the blow
WIND_G, WIND_PHI = V(-0.22, -0.06, 1.38), -62.0       # heaved further back, the grip up by his ear
TOP_G = V(-0.16, -0.32, 1.42)                         # (over the top)
HIT_G, HIT_PHI = V(-0.06, -0.46, 1.08), 120.0         # the blow: the head about 1.3 m out, at a robot's middle
HIT_TILT = 0.12


def attack_state(f):
    """(yaw, chest, bend, crouch, lunge, grip, phi, tilt, heel lift R) at frame f (the robots' frame)."""
    if f <= 3:
        k = ease(f / 3.0)
        return (lerp(C_YAW, C_YAW - 6.0, k), lerp(-6.0, -12.0, k), lerp(0.12, 0.0, k), lerp(0.085, 0.07, k), 0.0,
                COCK_G.lerp(WIND_G, k), lerp(COCK_PHI, WIND_PHI, k), C_TILT, 0.0)
    if f <= HIT:
        k = ((f - 3) / float(HIT - 3)) ** 1.35
        return (lerp(C_YAW - 6.0, -4.0, k), lerp(-12.0, 4.0, k), lerp(0.0, 0.42, k), lerp(0.07, 0.16, k), 0.09 * k,
                bez_p(WIND_G, TOP_G, HIT_G, k), lerp(WIND_PHI, HIT_PHI, k), lerp(C_TILT, HIT_TILT, k), 0.05 * k)
    if f <= 9:                                                    # the weight of it: held on the blow, a little give
        k = (f - HIT) / 2.0
        return (-4.0, 4.0, 0.42 + 0.02 * math.sin(math.pi * k), 0.16 + 0.01 * math.sin(math.pi * k), 0.09,
                HIT_G + V(0.0, 0.0, -0.006 * math.sin(math.pi * k)), HIT_PHI + 2.0 * math.sin(math.pi * k), HIT_TILT, 0.05)
    k = ease((f - 9) / float(FR - 9))                             # hauled back up over his shoulder
    return (lerp(-4.0, C_YAW, k), lerp(4.0, -6.0, k), lerp(0.42, 0.12, k), lerp(0.16, 0.085, k), 0.09 * (1 - k),
            bez_p(HIT_G, V(-0.18, -0.3, 1.3), COCK_G, k), lerp(HIT_PHI, COCK_PHI, k), lerp(HIT_TILT, C_TILT, k), 0.05 * (1 - k))


def attack_pose(arm, f):
    yaw, chest, bend, crouch, lunge, g, phi, tilt, heel = attack_state(f)
    ro = rz(yaw) @ V(0.0, -lunge, 0.0) + V(0.0, 0.0, -crouch)
    aims = feet(arm, C_YAW, lift=(0.0, heel), **C_FEET)
    torso(aims, yaw, bend=bend, chest=chest, look=0.0, pitch=0.05 - 0.15 * bend)
    U, W = swing_axes(rz(yaw) @ V(0, -1, 0), tilt)
    haft, face = swing_dirs(phi, U, W)
    aims.update(two_hands(arm, g + ro, haft, face, ro, yaw))
    return aims, ro, rz(yaw)


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, rr = attack_pose(arm, f)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- ability: Steam Blast
def valve_strike():
    """(grip, handle, face, body yaw) with the maul's face on the valve's striker cap: the handle 45 degrees down toward
    it, the face leading down onto it."""
    to = V(VALVE_CS.x - ROOT.x, VALVE_CS.y - ROOT.y, 0.0)
    yaw = math.degrees(math.atan2(to.x, -to.y))            # rz(yaw) @ (0, -1, 0) points at it
    U, W = swing_axes(to, 0.0)
    haft, face = swing_dirs(135.0, U, W)
    head = VALVE_CS - face * HEAD_HALF
    g = head - haft * MAUL_L
    return g, haft, face, yaw


V_YAW = valve_strike()[3]                 # turned to the valve


def ability_state(f):
    """(yaw, mode blend 0 combat .. 1 valve, crouch, bend, lunge, grip, phi, tilt, pitch, laugh, roll)."""
    gv, hv, fv, _ = valve_strike()
    if f <= 8:                                                   # turn to the valve, the maul still ready
        k = ease(f / 8.0)
        return lerp(C_YAW, V_YAW, k), k, lerp(0.085, 0.06, k), lerp(0.12, 0.0, k), 0.0, "ready", k
    if f <= 19:                                                  # heave it high overhead, up on his toes
        k = ease((f - 8) / 11.0)
        return V_YAW, 1.0, lerp(0.06, 0.0, k), lerp(0.0, -0.12, k), 0.0, "raise", k
    if f <= SLAM:                                                # the slam
        k = ((f - 19) / float(SLAM - 19)) ** 1.6
        return V_YAW, 1.0, lerp(0.0, 0.2, k), lerp(-0.12, 0.5, k), 0.1 * k, "slam", k
    if f <= 36:                                                  # leaning on it while the steam roars
        k = (f - SLAM) / float(36 - SLAM)
        return V_YAW, 1.0, 0.2 + 0.01 * math.sin(k * 9), 0.5, 0.1, "hold", k
    if f <= 50:                                                  # up, the maul onto his shoulder, laughing
        k = ease((f - 36) / 14.0)
        return lerp(V_YAW, V_YAW * 0.5, k), 1.0, lerp(0.2, 0.0, k), lerp(0.5, -0.08, k), 0.1 * (1 - k), "shoulder", k
    k = ease((f - 50) / float(AB_FR - 50))                       # back to the ready stance
    return lerp(V_YAW * 0.5, C_YAW, k), 1.0 - k, lerp(0.0, 0.085, k), lerp(-0.08, 0.12, k), 0.0, "back", k


RAISE_G, RAISE_PHI = V(-0.2, -0.16, 1.86), -45.0         # high overhead (body space of the turned stance)
RAISE_TILT = 0.38
SHOULDER_G, SHOULDER_PHI = V(-0.22, -0.2, 1.3), -38.0    # on his shoulder
V_FEET = dict(lf=(0.22, -0.2), rf=(-0.25, 0.14), turn=(2.0, -18.0))


def ability_pose(arm, f):
    yaw, mode_k, crouch, bend, lunge, phase, k = ability_state(f)
    gv, hv, fv, _ = valve_strike()
    ro = rz(yaw) @ V(0.0, -lunge, 0.0) + V(0.0, 0.0, -crouch)
    fy = lerp(C_YAW, V_YAW, mode_k)
    fs = {kk: tuple(lerp(a, b, mode_k) for a, b in zip(C_FEET[kk], V_FEET[kk])) for kk in ("lf", "rf", "turn")}
    heel = 0.04 * k if phase == "raise" else (0.04 * (1 - k) if phase == "slam" else 0.0)
    aims = feet(arm, fy, lift=(heel, heel), **fs)
    laugh = 0.0
    if phase == "shoulder":
        laugh = smooth01(k / 0.5)
    elif phase == "back":
        laugh = 1.0 - smooth01(k / 0.4)
    shake = math.sin(f * 2.1) * laugh
    look = yaw if phase not in ("back",) else lerp(yaw, 0.0, k)
    torso(aims, yaw, bend=bend, chest=0.0, look=look, pitch=0.05 - 0.2 * max(bend, 0.0) + 0.45 * laugh + 0.04 * shake)
    ro = ro + V(0.0, 0.0, 0.008 * shake)
    Uv, Wv = swing_axes(rz(V_YAW) @ V(0, -1, 0), 0.0)
    Uc, Wc = swing_axes(rz(yaw) @ V(0, -1, 0), C_TILT)
    if phase == "ready":
        g0, h0, f0 = cock_state(C_YAW)
        g1 = body_pt(SHOULDER_G, V(0, 0, 0), V_YAW)
        g = g0.lerp(g1, k) + ro
        haft, face = swing_dirs(lerp(COCK_PHI, SHOULDER_PHI, k), *swing_axes(rz(yaw) @ V(0, -1, 0), lerp(C_TILT, 0.2, k)))
    elif phase == "raise":
        g = body_pt(SHOULDER_G, V(0, 0, 0), V_YAW).lerp(body_pt(RAISE_G, V(0, 0, 0), V_YAW), k) + ro
        haft, face = swing_dirs(lerp(SHOULDER_PHI, RAISE_PHI, k), *swing_axes(rz(V_YAW) @ V(0, -1, 0), lerp(0.2, RAISE_TILT, k)))
    elif phase == "slam":
        top = body_pt(V(-0.1, -0.42, 1.62), V(0, 0, 0), V_YAW)
        g = bez_p(body_pt(RAISE_G, V(0, 0, 0), V_YAW) + ro, top + ro, gv, k)
        haft, face = swing_dirs(lerp(RAISE_PHI, 135.0, k), *swing_axes(rz(V_YAW) @ V(0, -1, 0), lerp(RAISE_TILT, 0.0, k)))
    elif phase == "hold":
        g, haft, face = gv, hv, fv
    elif phase == "shoulder":
        g = gv.lerp(body_pt(SHOULDER_G, V(0, 0, 0), yaw) + ro, k) + V(0, 0, 0.12 * math.sin(math.pi * k))
        haft, face = swing_dirs(lerp(135.0, SHOULDER_PHI, k), *swing_axes(rz(lerp(V_YAW, yaw, k)) @ V(0, -1, 0), lerp(0.0, 0.2, k)))
    else:
        g0, h0, f0 = cock_state(C_YAW)
        g = body_pt(SHOULDER_G, V(0, 0, 0), yaw).lerp(g0, k) + ro
        haft, face = swing_dirs(lerp(SHOULDER_PHI, COCK_PHI, k), *swing_axes(rz(yaw) @ V(0, -1, 0), lerp(0.2, C_TILT, k)))
    aims.update(two_hands(arm, g, haft, face, ro, yaw))
    return aims, ro, rz(yaw)


def make_ability(arm, frames=AB_FR):
    P = Poser(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        aims, ro, rr = ability_pose(arm, f)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- cheer
def make_cheer(arm, frames=CH_FR):
    """Rank up: the maul heaved up over his head, held across in both fists, pumped twice; a booming laugh."""
    P = Poser(arm)
    act = new_action(arm, "Cheer")
    up_g, up_h, up_f = V(-0.3, -0.06, 2.02), V(1.0, 0.0, 0.08).normalized(), V(0.0, 0.0, 1.0)
    for f in range(frames + 1):
        t = f / float(frames)
        up = smooth01(t / 0.2) * (1 - smooth01((t - 0.8) / 0.2))
        pump = max(0.0, math.sin((t - 0.2) / 0.6 * 2 * math.pi * 2)) * smooth01((t - 0.18) / 0.06) * (1 - smooth01((t - 0.76) / 0.06))
        laugh = math.sin(f * 1.9) * up
        hop = 0.025 * pump
        ro = V(0.0, 0.0, -0.03 + hop + 0.006 * laugh - 0.03 * (1 - up))
        aims = feet(arm, 0.0, lf=(0.23, -0.02), rf=(-0.23, 0.04), turn=(14.0, -14.0), lift=(hop * 0.4, hop * 0.4))
        torso(aims, 0.0, bend=-0.1 * up, look=4.0 * math.sin(f * 0.3) * up, pitch=0.05 + 0.4 * up + 0.04 * laugh)
        g = (SHOULDER_G + ro).lerp(up_g + V(0.0, 0.0, 0.1 * pump) + ro, up)
        U, W = swing_axes(V(0, -1, 0), 0.3)
        haft, face = swing_dirs(SHOULDER_PHI, U, W)
        haft, face = mixd(haft, up_h, up), mixd(face, up_f, up)
        aims.update(two_hands(arm, g, haft, face, ro, 0.0, left_on=lerp(LEFT_ON, 0.56, up)))
        ch, _ = P.solve(aims, ro, Quaternion())
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- loops
def make_idle(arm, frames=I_FR):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr = combat_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
