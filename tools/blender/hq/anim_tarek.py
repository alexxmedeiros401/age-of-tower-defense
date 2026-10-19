"""Tarek's clips (keyed as 30 fps frames; the .glb runs them at 24, game.gd CLIP_FPS).

Idle    : the hammer resting on his right shoulder, his left fist on his hip; he rocks on his heels, looks about, and once
          a loop wipes the sweat off his brow with his forearm.
Combat  : side-on to the robots, his left foot forward and his left hand out at them, the hammer cocked back over his
          right shoulder ready to throw; he bounces on his knees.
Attack  : (22 frames, inside the 1.0 s cooldown) the throw: from the cocked stance his arm whips over and the hammer
          leaves his hand at RELEASE (frame 2: game.gd launches the flying hammer from there, the hammer in his hand
          vanishes), he follows through down across his body, reaches to his hip where a fresh one appears (FRESH) and
          cocks it back.
Ability : Forge Fury (game.gd turns him to his anvil, at ANVIL in front of him here): he lifts the hammer high and
          strikes the red-hot bar on the anvil three times, STRIKES (the sparks), the third the hardest (the fury goes
          out), then raises the hammer overhead and roars.
Cheer   : the hammer thrust overhead twice, his head thrown back laughing, his left hand slapping his belly.

The hammer is rigid on the `hammer` bone in his right fist ("frame" aims: its handle along the fist's thumb axis, its
red-hot face along the knuckles); the bone's scale hides it while the thrown one flies."""
import math
from mathutils import Vector, Quaternion
import tarek as cm
import tarek_base as tb
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
_G, _T, _F = cm.hammer_frame()
T_REST, F_REST = vec(_T), vec(_F)
_wr, _f, _n, _t = cm.hand_frame("R")
FIST_OFF = vec(_G - _wr)
HEAD_OFF = cm.HAMMER_L                      # grip -> the head's centre, along the handle
FACE_OFF = cm.HEAD_HALF[2] * 1.02            # the head's centre -> its striking face (tarek.hot_field)
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
RELEASE = 2         # the hammer leaves his hand (game.gd ATTACK_FRAME)
FRESH = 11          # a fresh hammer appears in his hand at his hip
FR = 22
STRIKES = (12, 22, 36)                      # the hammer on the anvil (game.gd: the sparks; the third sends out the fury)
AB_FR = 66
# the anvil, set in front of him (game.gd turns his yaw to it for the Ability): its face's middle, character space
ANVIL = V(0.02, -tb.ANVIL_R, tb.ANVIL_TOP + 0.019)     # (the top of the red-hot bar)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def dirz(deg):
    """Horizontal direction at `deg` counterclockwise from his front (-Y), seen from above."""
    a = math.radians(deg)
    return V(math.sin(a), -math.cos(a), 0.0)


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def hammer_grip(arm, grip, handle, face, pole):
    """Right fist (its grip centre) at `grip`, the handle along `handle`, the hot face toward `face`."""
    hd = Vector(handle).normalized()
    R = frame_map(T_REST, hd, F_REST, Vector(face))
    aims = arm_aims(arm, "R", Vector(grip) - R @ FIST_OFF, pole=pole)
    aims["hand.R"] = ("frame", T_REST, hd, F_REST, Vector(face))
    return aims


def strike_grip(head, handle):
    """The grip that puts the hammer's head centre at `head` with the handle along `handle`."""
    return Vector(head) - Vector(handle).normalized() * HEAD_OFF


def open_hand(arm, wrist, palm, fingers, pole):
    aims = arm_aims(arm, "L", wrist, pole=pole)
    aims["hand.L"] = ("frame", vec(_fL), Vector(fingers), vec(_nL), Vector(palm))
    return aims


def feet(arm, yaw, lf=(0.19, -0.02), rf=(-0.19, 0.04), lift=(0.0, 0.0), turn=(8.0, -8.0)):
    """Feet planted round the root (body space offsets, turned with `yaw`); `lift` raises each heel a little."""
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
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(0.0, -0.1 - 0.2 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.04 + 0.7 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.03, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.03, 0.02)


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mixv(a, b, k):
    return a.lerp(b, k)


def mixd(a, b, k):
    return a.normalized().lerp(b.normalized(), k).normalized()


# ---------------------------------------------------------------------------------------------- idle
SHOULDER_G = V(-0.27, -0.17, 1.2)          # the grip with the hammer resting on his shoulder
SHOULDER_HD = V(-0.03, 0.62, 0.78)         # the handle up and back over the shoulder
SHOULDER_FC = V(-1.0, 0.0, 0.0)            # its hot face turned out, away from his neck


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    rock = math.sin(w)
    yaw = 3.0 * rock
    ro = V(0.0, -0.008 * rock, -0.01 + 0.004 * br)
    aims = feet(arm, 0.0)
    # once a loop (t 0.55-0.8) he wipes his brow with his left forearm
    wipe = smooth01((t - 0.55) / 0.06) * (1.0 - smooth01((t - 0.74) / 0.07))
    sweep = smooth01((t - 0.6) / 0.12)
    look = (24.0 * math.sin(w + 0.6) + 5.0 * math.sin(w * 3)) * (1.0 - wipe)
    torso(aims, yaw, bend=0.0 + 0.06 * wipe, side=-0.03 * rock, look=look + yaw * 0.0, pitch=0.04 + 0.02 * br - 0.12 * wipe)
    g = body_pt(SHOULDER_G + V(0, 0, 0.006 * br), ro, yaw)
    aims.update(hammer_grip(arm, g, rz(yaw) @ SHOULDER_HD, rz(yaw) @ SHOULDER_FC, pole=rz(yaw) @ V(-0.6, -0.4, -1.0)))
    hip = V(0.34, 0.02, 1.0)
    brow = V(0.2, -0.27, 1.76).lerp(V(-0.06, -0.27, 1.78), sweep)
    wl = body_pt(hip.lerp(brow, wipe), ro, yaw)
    palm = V(-1.0, 0.15, 0.0).lerp(V(0.0, 0.3, -1.0), wipe)
    fing = V(0.05, -0.55, -0.83).lerp(V(-0.95, 0.1, 0.2), wipe)
    aims.update(open_hand(arm, wl, rz(yaw) @ palm, rz(yaw) @ fing, pole=rz(yaw) @ V(1.0, 0.3, -0.2).lerp(V(1.0, -0.2, -0.4), wipe)))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- combat (cocked)
C_YAW = -28.0          # turned side-on to the robots: his left shoulder toward them, his throwing arm back
COCK_G = V(-0.3, 0.08, 1.62)               # the grip up beside his head (body space, before the yaw)
COCK_HD = V(-0.06, 0.5, 0.86)              # the handle up and back
COCK_FC = V(0.0, 0.86, -0.5)               # the hot face back
AIM_L = V(0.18, -0.52, 1.36)               # his left hand out at the robots (the robots' frame: yaw 0)
C_FEET = dict(lf=(0.2, -0.18), rf=(-0.18, 0.16), turn=(-4.0, -20.0))


def cocked(yaw, ro, bob=0.0):
    g = body_pt(COCK_G + V(0, 0, 0.012 * bob), ro, yaw)
    return g, rz(yaw) @ COCK_HD, rz(yaw) @ COCK_FC


def combat_pose(arm, t):
    w = 2 * math.pi * t
    bob = math.sin(w * 2)
    ro = V(0.0, 0.0, -0.07 + 0.014 * bob)
    aims = feet(arm, C_YAW, **C_FEET)
    torso(aims, C_YAW, bend=0.1, chest=-12.0, look=0.0, pitch=0.02)
    g, hd, fc = cocked(C_YAW, ro, bob)
    aims.update(hammer_grip(arm, g, hd, fc, pole=rz(C_YAW) @ V(-0.8, 0.4, -0.4)))
    wl = body_pt(AIM_L + V(0, 0, 0.01 * bob), ro, 0.0)
    aims.update(open_hand(arm, wl, V(0.0, 0.1, -1.0), V(-0.1, -1.0, 0.1), pole=V(0.9, 0.2, -0.6)))
    return aims, ro, rz(C_YAW)


# ---------------------------------------------------------------------------------------------- attack: the throw
REL_G, REL_HD, REL_FC = V(-0.2, -0.36, 1.66), V(0.0, -0.62, 0.78), V(0.0, -0.78, -0.62)     # at the release (yaw 0 frame)
FOL_G = V(0.12, -0.38, 1.0)                                                                 # the follow-through
HIP_G, HIP_HD, HIP_FC = V(-0.42, -0.1, 0.96), V(-0.25, 0.1, -0.96), V(-0.1, -0.97, 0.1)     # a fresh one at his right hip
SWING_HD = V(-0.7, -0.6, 0.3)                                                               # pointing out as it comes up
HIP_L = V(0.42, 0.1, 1.08)                                                                  # his left hand pulled back


def bez_d(a, b, c, k):
    return mixd(mixd(a, b, k), mixd(b, c, k), k)


def throw_state(f, ro):
    """(body yaw, chest twist, bend, crouch, grip, handle, face, left wrist, heel lift) at frame f, in the robots' frame."""
    g_c, hd_c, fc_c = cocked(C_YAW, ro)
    if f <= RELEASE:                                         # the arm whips over the top
        k = (f / float(RELEASE)) ** 1.5
        g = g_c.lerp(REL_G + ro, k) + V(0, 0, 0.1 * math.sin(math.pi * k))
        return (lerp(C_YAW, -8.0, k), lerp(-12.0, 4.0, k), lerp(0.1, 0.16, k), 0.07, g, mixd(hd_c, REL_HD, k), mixd(fc_c, REL_FC, k),
                AIM_L.lerp(V(0.32, -0.24, 1.22), k) + ro, 0.0)
    if f <= 7:                                               # follow through, down across his body (the hammer is gone)
        k = ease((f - RELEASE) / float(7 - RELEASE))
        return (lerp(-8.0, 20.0, k), lerp(4.0, 12.0, k), lerp(0.16, 0.4, k), lerp(0.07, 0.13, k), (REL_G + ro).lerp(FOL_G + ro, k),
                REL_HD, REL_FC, V(0.32, -0.24, 1.22).lerp(HIP_L, k) + ro, 0.05 * k)
    if f <= FRESH:                                           # straighten, reach to his right hip
        k = ease((f - 7) / float(FRESH - 7))
        return (lerp(20.0, -6.0, k), lerp(12.0, -2.0, k), lerp(0.4, 0.18, k), lerp(0.13, 0.08, k), (FOL_G + ro).lerp(HIP_G + ro, k),
                HIP_HD, HIP_FC, HIP_L.lerp(V(0.36, -0.36, 1.26), k) + ro, 0.05 * (1 - k))
    k = ease((f - FRESH) / float(FR - FRESH))                # swing it up and cock it back
    arc = math.sin(math.pi * k)
    g = (HIP_G + ro).lerp(g_c, k) + V(-0.12 * arc, -0.1 * arc, 0.0)
    return (lerp(-6.0, C_YAW, k), lerp(-2.0, -12.0, k), lerp(0.18, 0.1, k), lerp(0.08, 0.07, k), g, bez_d(HIP_HD, SWING_HD, hd_c, k),
            bez_d(HIP_FC, V(0.0, -0.4, -0.9), fc_c, k), V(0.36, -0.36, 1.26).lerp(AIM_L, k) + ro, 0.0)


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        crouch = throw_state(f, V(0, 0, 0))[3]
        ro = V(0.0, -0.05 * smooth01(f / 5.0) * (1 - smooth01((f - 8) / 8.0)), -crouch)
        yaw, chest, bend, _c, g, hd, fc, wl, heel = throw_state(f, ro)
        aims = feet(arm, C_YAW, lift=(0.0, heel), **C_FEET)
        torso(aims, yaw, bend=bend, chest=chest, look=0.0, pitch=0.02 - 0.1 * bend)
        aims.update(hammer_grip(arm, g, hd, fc, pole=rz(yaw) @ V(-0.8, 0.3, -0.5)))
        aims.update(open_hand(arm, wl, V(0.0, 0.1, -1.0), V(-0.1, -1.0, 0.1), pole=V(0.9, 0.2, -0.6)))
        sc = {"hammer": 0.0 if RELEASE <= f < FRESH else 1.0}
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    key_constant(act, 'pose.bones["hammer"].scale')
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- ability: Forge Fury
STRIKE_HD = V(0.2, -0.9, -0.25)            # at the blow: from his right side, sloping down to the anvil's middle
HIGH_G, HIGH_HD, HIGH_FC = V(-0.2, 0.02, 1.86), V(-0.05, 0.45, 0.9), V(0.0, 0.9, -0.45)
ROAR_G, ROAR_HD, ROAR_FC = V(-0.22, -0.02, 2.02), V(-0.02, -0.1, 1.0), V(-0.9, -0.3, 0.0)
KNEE_L, ROAR_L = V(0.22, -0.2, 0.84), V(0.5, -0.12, 1.86)


def strike_pose(level, ro):
    """Grip, handle and face for the hammer `level` up from the anvil (0 = its face on the work, where the anvil is
    whatever his crouch; 1 = high overhead, with his body), swung through an arc in front of him."""
    head0 = ANVIL + V(0.0, 0.0, FACE_OFF)
    g0 = strike_grip(head0, STRIKE_HD)
    k = smooth01(level)
    g = g0.lerp(HIGH_G + ro, k) + V(-0.08, 0.04, 0.12) * math.sin(math.pi * k)
    hd = bez_d(STRIKE_HD, V(0.1, -0.5, 0.85), HIGH_HD, k)
    fc = bez_d(V(0.0, 0.0, -1.0), V(0.0, -0.9, -0.3), HIGH_FC, k)
    return g, hd, fc


def ability_state(f):
    """(hammer level above the anvil, bend, crouch, head pitch, roar) at frame f."""
    s1, s2, s3 = STRIKES
    if f <= 9:                                               # turn to it, lift high
        k = ease(f / 9.0)
        return lerp(0.3, 1.0, k), lerp(0.1, 0.05, k), lerp(0.07, 0.1, k), lerp(0.0, -0.1, k), 0.0
    if f <= s1:                                              # strike
        k = ((f - 9) / float(s1 - 9)) ** 1.6
        return lerp(1.0, 0.0, k), lerp(0.05, 0.34, k), lerp(0.1, 0.16, k), lerp(-0.1, -0.2, k), 0.0
    if f <= 16:                                              # rebound
        k = ease((f - s1) / float(16 - s1))
        return lerp(0.0, 0.62, k), lerp(0.34, 0.2, k), lerp(0.16, 0.12, k), -0.2, 0.0
    if f <= s2:
        k = ((f - 16) / float(s2 - 16)) ** 1.6
        return lerp(0.62, 0.0, k), lerp(0.2, 0.34, k), lerp(0.12, 0.16, k), -0.2, 0.0
    if f <= 30:                                              # the big wind-up, higher
        k = ease((f - s2) / float(30 - s2))
        return lerp(0.0, 1.15, k), lerp(0.34, -0.02, k), lerp(0.16, 0.06, k), lerp(-0.2, 0.05, k), 0.0
    if f <= s3:                                              # the hardest strike, deep
        k = ((f - 30) / float(s3 - 30)) ** 1.8
        return lerp(1.15, 0.0, k), lerp(-0.02, 0.44, k), lerp(0.06, 0.22, k), lerp(0.05, -0.25, k), 0.0
    if f <= 42:                                              # holds on it while the fury rolls out
        return 0.0, 0.44, 0.22, -0.25, 0.0
    if f <= 54:                                              # straighten and raise it overhead, roaring
        k = ease((f - 42) / 12.0)
        return lerp(0.0, 1.0, k), lerp(0.44, -0.12, k), lerp(0.22, 0.0, k), lerp(-0.25, 0.5, k), k
    return 1.0, -0.12, 0.0, 0.5, 1.0


def make_ability(arm, frames=AB_FR):
    P = Poser(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        level, bend, crouch, pitch, roar = ability_state(f)
        intro = smooth01(f / 9.0)
        settle = smooth01((f - 56) / float(frames - 56))
        mode = intro * (1 - settle)              # 0 = his combat stance, 1 = squared up to the anvil
        body_yaw = lerp(C_YAW, 0.0, mode)
        ro = V(0.0, -0.06 * bend, -lerp(0.07, crouch, mode) if f > 56 else -crouch)
        lf = (lerp(0.2, 0.22, mode), lerp(-0.18, -0.12, mode))
        rf = (lerp(-0.18, -0.25, mode), lerp(0.16, 0.06, mode))
        aims = feet(arm, body_yaw, lf=lf, rf=rf, turn=(lerp(-4.0, 6.0, mode), lerp(-20.0, -14.0, mode)))
        torso(aims, body_yaw, bend=lerp(0.1, bend, mode), chest=lerp(-12.0, -4.0, mode), look=0.0,
              pitch=lerp(0.02, pitch, mode if f > 56 else 1.0))
        g, hd, fc = strike_pose(min(level, 1.0), ro)
        if level > 1.0:                                       # the big wind-up: higher and further back
            g = g + V(0.02, 0.08, 0.1) * (level - 1.0) / 0.15
        g, hd, fc = g.lerp(ROAR_G + ro, roar), mixd(hd, ROAR_HD, roar), mixd(fc, ROAR_FC, roar)
        wl = (KNEE_L + V(0, 0, -crouch * 0.6)).lerp(ROAR_L, roar) + ro
        if f < 9:                                             # from the stance: the left hand comes in from aiming
            wl = (AIM_L + ro).lerp(wl, intro)
        palm = V(-0.3, 0.2, -0.93).lerp(V(-0.6, -0.6, 0.3), roar)
        fing = V(-0.1, -0.95, -0.3).lerp(V(0.1, 0.0, 1.0), roar)
        if settle > 0.0:                                      # back into the cocked stance
            cg, chd, cfc = cocked(C_YAW, V(0, 0, -0.07))
            g, hd, fc = g.lerp(cg, settle), mixd(hd, chd, settle), mixd(fc, cfc, settle)
            wl = wl.lerp(AIM_L + V(0, 0, -0.07), settle)
            palm, fing = palm.lerp(V(0.0, 0.1, -1.0), settle), fing.lerp(V(-0.1, -1.0, 0.1), settle)
        aims.update(hammer_grip(arm, g, hd, fc, pole=rz(body_yaw) @ V(-0.9, 0.4, -0.5)))
        aims.update(open_hand(arm, wl, palm, fing, pole=V(1.0, 0.3, -0.4)))
        ch, _ = P.solve(aims, ro, rz(body_yaw))
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- cheer
def make_cheer(arm, frames=40):
    """Rank up: the hammer thrust overhead twice, his head thrown back laughing, his left hand slapping his belly."""
    P = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        t = f / frames
        up = ease(min(1.0, t / 0.15)) * (1 - ease(max(0.0, (t - 0.82) / 0.18)))
        pump = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.4)) * (1 - max(0.0, (t - 0.8) / 0.2))
        laugh = math.sin(t * 2 * math.pi * 5) * up
        hop = max(0.0, math.sin(t * 2 * math.pi * 2 - 0.9)) * 0.03 * (1 - max(0.0, (t - 0.75) / 0.25))
        yaw = 0.0
        ro = V(0.0, 0.01 * up, -0.02 + hop + 0.006 * laugh)
        aims = feet(arm, yaw, lift=(hop * 0.5, hop * 0.5))
        torso(aims, yaw, bend=-0.1 * up, look=5.0 * math.sin(t * 9), pitch=0.05 + 0.45 * up + 0.05 * laugh)
        g_idle = body_pt(SHOULDER_G, ro, yaw)
        g_up = body_pt(V(-0.3, -0.04, 1.95) + V(0.0, 0.0, 0.1) * pump, ro, yaw)
        g = g_idle.lerp(g_up, up)
        hd = mixd(SHOULDER_HD, V(-0.1, -0.05, 1.0), up)
        fc = mixd(SHOULDER_FC, V(-0.6, -0.8, 0.0), up)
        aims.update(hammer_grip(arm, g, hd, fc, pole=V(-1.0, 0.3, -0.3)))
        belly = V(0.16, -0.3, 1.02) + V(0.0, -0.025, 0.0) * max(0.0, laugh)
        wl = V(0.34, 0.02, 1.0).lerp(belly, up) + ro
        aims.update(open_hand(arm, wl, V(-1.0, 0.15, 0.0).lerp(V(-0.4, 0.9, 0.0), up), V(0.05, -0.55, -0.83).lerp(V(-0.9, -0.1, -0.3), up),
                              pole=V(1.0, 0.2, -0.4)))
        ch, _ = P.solve(aims, ro, rz(yaw))
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_idle(arm, frames=120):
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


def key_constant(act, path):
    """Make every key on the curve `path` constant (the hammer pops out of / into his hand)."""
    fcs = []
    try:
        fcs = [fc for fc in act.fcurves]
    except Exception:
        pass
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                fcs += list(cb.fcurves)
    for fc in fcs:
        if fc.data_path == path:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
