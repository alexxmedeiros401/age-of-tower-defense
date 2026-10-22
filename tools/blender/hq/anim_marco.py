"""Marco's clips (keyed in frames; the game plays them at CLIP_FPS 24).

Idle    : standing easy, his left fist on his hip, the grenade in his right hand; twice a loop he tosses it up and catches
          it (his eyes follow it up and down), grinning; between the tosses he shifts his weight and looks about.
Combat  : side-on to the robots, his left foot forward and his left hand out at them, a grenade in his right hand cocked
          back beside his head, its fuse lit (the sparks fizz); he bounces on his knees.
Attack  : (33 frames: inside the 1.4 s cooldown) from the cocked stance he winds up and lobs the grenade overarm in a
          high arc; it leaves his hand at RELEASE (frame 10: game.gd launches its grenade from there; the one in his hand is
          hidden from the next frame); he follows through, reaches into the pouch on his right hip for the next one (FRESH:
          it appears in his hand), brings it up to the match on his chest and touches the fuse to it (LIGHT: the sparks
          start), and cocks it back again. (The lighting closes the loop: the clip starts and ends cocked with a lit fuse,
          as his Combat stance holds it.)
Ability : Powder Keg (72 frames): he tucks the lit grenade into his pouch, turns to the small keg standing by his right
          foot, squats and takes it in both hands, heaves it up onto his right shoulder, brings it down before his chest and
          lights its fuse at the match (K_LIGHT), swings it up over his head and heaves it out at the robots with both
          hands (K_RELEASE, frame 45: game.gd flies its keg from there and sets off the big blast after it; his keg is
          hidden from the next frame), follows through; then draws a fresh grenade, lights it and cocks it back.
Cheer   : (rank up) his left hand takes his cap off and raises it high, waving it, while he pumps his right fist (the
          grenade in it) and laughs, head back; he claps the cap back on.

Free bones: the grenade (kept in his right hand, tossed in the Idle), the cap (kept on his head, raised in the Cheer),
the keg (on the flagstones, lifted in the Ability); their sparks ride child bones whose scale shows them while lit."""
import math
from mathutils import Vector, Quaternion, Matrix
import marco as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

_wr, _f, _n, _t = cm.hand_frame("R")
WR_R = vec(_wr)
F_R, N_R, T_R = vec(_f), vec(_n), vec(_t)
G_OFF = vec(cm.grenade_center()) - WR_R                 # wrist -> the ball's middle (rest)
FUSE_REST = vec(cm.fuse_dir())
FUSE_REACH = cm.GREN_R + cm.FUSE_LEN                    # the ball's middle -> the fuse's tip
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
WR_L = vec(_wrL)
F_L, N_L, T_L = vec(_fL), vec(_nL), vec(_tL)
PALM_L = F_L * (0.08 * cm.HAND_S) + N_L * 0.045         # wrist -> the middle of the left palm's face (rest)
PALM_R = F_R * (0.08 * cm.HAND_S) + N_R * 0.045
MATCH_TIP = vec(cm.match_tip())
POUCH_MOUTH = vec(cm.POUCH_C) + V(0.0, 0.0, cm.POUCH_HALF[1] + 0.05) + vec(cm.POUCH_N) * 0.03
KEG_HEAD = vec(cm.KEG_C) + V(0, 0, 0.02)                # the keg bone's head (rest)
KEG_MID = vec(cm.KEG_C) + V(0, 0, cm.KEG_H / 2)
KEG_TIP = vec(cm.keg_tip())
G = 9.81

# clip frames (24 fps)
RELEASE = 10          # the grenade leaves his hand (game.gd ATTACK_FRAME)
FRESH = 19            # a fresh one in his hand at the pouch
LIGHT = 25            # its fuse touched to the match: lit
FR = 33               # the Attack's length (1.375 s at 24 fps, inside the 1.4 s cooldown)
TUCK = 6              # Ability: the lit grenade tucked away into the pouch
K_GRIP = 15           # his hands on the keg
K_SHOULDER = 25       # the keg up on his right shoulder
K_LIGHT = 33          # its fuse lit at the match
K_HIGH = 41           # swung up over his head
K_RELEASE = 45        # heaved out (game.gd: its keg flies from here, the blast follows)
A_FRESH = 57          # a fresh grenade from the pouch ...
A_LIGHT = 63          # ... lit at the match
A_FR = 72


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mixd(a, b, k):
    return a.normalized().lerp(b.normalized(), k).normalized()


def bez_p(a, b, c, k):
    return a.lerp(b, k).lerp(b.lerp(c, k), k)


def bez_d(a, b, c, k):
    return mixd(mixd(a, b, k), mixd(b, c, k), k)


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


# ---------------------------------------------------------------------------------------------- rest relations
class Rest:
    def __init__(self, arm):
        b = arm.data.bones
        self.m = {nm: b[nm].matrix_local.copy() for nm in ("hand.R", "hand.L", "head", "chest", "root", "grenade", "cap", "keg")}
        self.h2g = self.m["hand.R"].inverted() @ self.m["grenade"]
        self.h2c = self.m["head"].inverted() @ self.m["cap"]
        self.match_local = self.m["chest"].inverted() @ MATCH_TIP

    def match(self, P):
        return P["chest"] @ self.match_local


def grenade_in_hand(R):
    return lambda P, base: ("world", P["hand.R"] @ R.h2g)


def cap_on_head(R):
    return lambda P, base: ("world", P["head"] @ R.h2c)


def free_matrix(rest, pos, rot):
    """A free bone's whole pose: its rest orientation turned by `rot`, its head at `pos`."""
    M = rot.to_matrix().to_4x4() @ rest.to_3x3().to_4x4()
    M.translation = pos
    return M


# ---------------------------------------------------------------------------------------------- hands, feet, torso
def ball_grip(arm, center, fing, palm, pole):
    """Right hand round the grenade: the ball's middle at `center`, the fingers toward `fing`, the palm facing `palm`."""
    R = frame_map(F_R, Vector(fing), N_R, Vector(palm))
    aims = arm_aims(arm, "R", Vector(center) - R @ G_OFF, pole=pole)
    aims["hand.R"] = ("frame", F_R, Vector(fing), N_R, Vector(palm))
    return aims


def fuse_grip(arm, tip, fuse, fing, pole):
    """Right hand holding the grenade so its fuse's tip is at `tip`, the fuse pointing along `fuse`, the fingers toward
    `fing` (as near as can be)."""
    R = frame_map(FUSE_REST, Vector(fuse), F_R, Vector(fing))
    center = Vector(tip) - Vector(fuse).normalized() * FUSE_REACH
    aims = arm_aims(arm, "R", center - R @ G_OFF, pole=pole)
    aims["hand.R"] = ("frame", FUSE_REST, Vector(fuse), F_R, Vector(fing))
    return aims, center


def hand_on(arm, side, contact, fing, palm, pole):
    """A hand with the middle of its palm on `contact`, the fingers toward `fing`, the palm facing `palm`."""
    Fr, Nr, off = (F_L, N_L, PALM_L) if side == "L" else (F_R, N_R, PALM_R)
    R = frame_map(Fr, Vector(fing), Nr, Vector(palm))
    aims = arm_aims(arm, side, Vector(contact) - R @ off, pole=pole)
    aims["hand." + side] = ("frame", Fr, Vector(fing), Nr, Vector(palm))
    return aims


def hand_matrix(arm, side, M, pole):
    """A hand posed to the whole matrix M (its head at the wrist)."""
    Fr, Nr = (F_L, N_L) if side == "L" else (F_R, N_R)
    rest = arm.data.bones["hand." + side].matrix_local.to_3x3()
    Rf = M.to_3x3() @ rest.inverted()
    aims = arm_aims(arm, side, M.translation, pole=pole)
    aims["hand." + side] = ("frame", Fr, Rf @ Fr, Nr, Rf @ Nr)
    return aims


def feet(arm, yaw, lf=(0.2, -0.02), rf=(-0.2, 0.05), lift=(0.0, 0.0), turn=(8.0, -8.0)):
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


# ---------------------------------------------------------------------------------------------- idle
HIP_L = V(0.375, 0.085, 1.03)               # his left fist on his hip (behind the hanger's hilt)
HIP_L_PALM, HIP_L_FING = V(-1.0, 0.1, 0.05), V(0.1, 0.7, -0.7)
HOLD_C = V(-0.3, -0.27, 1.02)               # the grenade held before his right hip, in his upturned palm
HOLD_PALM, HOLD_FING = V(0.05, -0.05, 1.0), V(0.15, -1.0, 0.1)
TOSSES = ((10, 14, 26), (58, 62, 74))       # (dip, release, catch) frames of the Idle's two tosses
TOSS_T = 12                                 # its flight (frames)
I_FR = 96


def toss_state(f):
    """(hand offset (dip, throw, catch), ball in flight: (height above the hand's line, spin) or None, flight progress)."""
    for d0, rel, cat in TOSSES:
        if d0 <= f < rel:                                    # dip and throw
            k = (f - d0) / float(rel - d0)
            dip = -0.05 * math.sin(math.pi * min(1.0, k / 0.6)) if k < 0.6 else 0.07 * smooth01((k - 0.6) / 0.4)
            return dip, None, 0.0
        if rel <= f < cat:                                   # in the air
            tt = (f - rel) / float(FPS)
            T = TOSS_T / float(FPS)
            v0 = G * T / 2
            h = v0 * tt - 0.5 * G * tt * tt
            k = (f - rel) / float(cat - rel)
            hand = 0.07 - 0.07 * smooth01(k / 0.4) * (1 - smooth01((k - 0.55) / 0.45))     # (back up to meet it)
            return hand, (h, 2 * math.pi * k), k
        if cat <= f < cat + 6:                               # caught: the hand gives with it
            k = (f - cat) / 6.0
            return 0.07 * (1 - k) - 0.05 * math.sin(math.pi * k), None, 1.0
    return 0.0, None, 0.0


def idle_pose(arm, f, R):
    t = (f % I_FR) / float(I_FR)
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = 2.5 * sway
    ro = V(0.006 * sway, 0.0, -0.012 + 0.005 * br)
    aims = feet(arm, 0.0, lf=(0.21, -0.03), rf=(-0.2, 0.06), turn=(12.0, -10.0))
    dip, fly, k = toss_state(f % I_FR)
    look = (20.0 * math.sin(w + 0.4) + 5.0 * math.sin(w * 3)) * (0.3 if fly else 1.0)
    pitch = 0.04 + 0.02 * br
    if fly is not None:
        pitch += 0.35 * math.sin(math.pi * k) + 0.05                           # watching it go up and come down
        look = -18.0
    torso(aims, yaw, bend=-0.02, side=0.02 * sway, chest=2.0 * sway, look=look, pitch=pitch)
    c = body_pt(HOLD_C + V(0, 0, dip), ro, yaw)
    aims.update(ball_grip(arm, c, rz(yaw) @ HOLD_FING, rz(yaw) @ HOLD_PALM, pole=rz(yaw) @ V(-0.8, 0.6, -0.3)))
    aims.update(hand_on(arm, "L", body_pt(HIP_L, ro, yaw), rz(yaw) @ HIP_L_FING, rz(yaw) @ HIP_L_PALM, pole=rz(yaw) @ V(1.0, 0.25, 0.1)))
    aims["cap"] = cap_on_head(R)
    if fly is None:
        aims["grenade"] = grenade_in_hand(R)
    else:
        h, spin = fly
        rel_c = body_pt(HOLD_C + V(0, 0, 0.07), ro, yaw)
        q = Quaternion(rz(yaw) @ T_R, spin)
        def flying(P, base, rel_c=rel_c, h=h, q=q):
            M0 = P["hand.R"] @ R.h2g                                            # its orientation as it left his hand
            M = (q.to_matrix() @ M0.to_3x3()).to_4x4()
            M.translation = rel_c + V(0, 0, h)                                  # (the bone's head is the ball's middle)
            return ("world", M)
        aims["grenade"] = flying
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- combat (cocked)
C_YAW = -32.0
C_FEET = dict(lf=(0.21, -0.17), rf=(-0.17, 0.17), turn=(-4.0, -24.0))
COCK_C = V(-0.36, 0.17, 1.66)               # the grenade cocked back beside his head (body space)
COCK_FING, COCK_PALM = V(0.1, 0.35, 0.93), V(0.25, -0.9, 0.35)
COCK_POLE = V(-0.85, 0.35, -0.4)
AIM_L = V(0.2, -0.52, 1.4)                  # his left hand out at the robots (the robots' frame: yaw 0)
AIM_PALM, AIM_FING = V(0.0, 0.1, -1.0), V(-0.1, -1.0, 0.1)


def cocked(yaw, ro, bob=0.0):
    c = body_pt(COCK_C + V(0, 0, 0.012 * bob), ro, yaw)
    return c, rz(yaw) @ COCK_FING, rz(yaw) @ COCK_PALM, rz(yaw) @ COCK_POLE


def combat_pose(arm, t, R):
    w = 2 * math.pi * t
    bob = math.sin(w * 2)
    ro = V(0.0, 0.0, -0.065 + 0.014 * bob)
    aims = feet(arm, C_YAW, **C_FEET)
    torso(aims, C_YAW, bend=0.08, chest=-14.0, look=0.0, pitch=0.05)
    c, fg, pm, pole = cocked(C_YAW, ro, bob)
    aims.update(ball_grip(arm, c, fg, pm, pole))
    aims.update(hand_on(arm, "L", AIM_L + V(0, 0, 0.01 * bob) + ro, AIM_FING, AIM_PALM, pole=V(0.9, 0.2, -0.6)))
    aims["grenade"] = grenade_in_hand(R)
    aims["cap"] = cap_on_head(R)
    return aims, ro, rz(C_YAW)


# ---------------------------------------------------------------------------------------------- attack: the lob
WIND_C = V(-0.4, 0.33, 1.5)                 # wound back: low behind his shoulder (body space)
WIND_FING, WIND_PALM = V(0.2, 0.5, 0.85), V(0.1, -0.6, 0.8)
REL_C = V(-0.26, -0.3, 1.95)                # the release: high before him, out past his cap (the robots' frame)
REL_FING, REL_PALM = V(0.05, -0.55, 0.85), V(0.0, -0.85, -0.5)
FOL_C = V(-0.3, -0.36, 1.2)                 # the follow-through, down before his right hip (clear of his face)
FOL_FING, FOL_PALM = V(0.4, -0.5, -0.75), V(0.3, 0.6, -0.7)
LOB_L = V(0.32, -0.42, 1.7)                 # his left hand up at the sky before the throw (aiming the arc)
TUCK_L = V(0.36, -0.06, 1.06)               # ... and pulled down to his hip as he throws


def pouch_pose(yaw, ro):
    """The right hand's ball at the pouch's mouth (it rides his hips), fingers down into it."""
    c = body_pt(POUCH_MOUTH, ro, yaw)
    return c, rz(yaw) @ V(-0.1, 0.15, -1.0), rz(yaw) @ V(0.85, 0.1, 0.0), rz(yaw) @ V(-0.9, 0.5, 0.1)


def attack_state(f):
    """(yaw, chest, bend, crouch, ro_y, heel, left wrist (robots' frame, before ro), phase) at frame f."""
    if f <= 6:
        k = ease(f / 6.0)
        return lerp(C_YAW, C_YAW - 12.0, k), lerp(-14.0, -24.0, k), lerp(0.08, -0.04, k), lerp(0.065, 0.085, k), 0.035 * k, 0.0, \
            AIM_L.lerp(LOB_L, k), ("wind", k)
    if f <= RELEASE:
        k = ((f - 6) / float(RELEASE - 6)) ** 1.25
        return lerp(C_YAW - 12.0, -4.0, k), lerp(-24.0, 6.0, k), lerp(-0.04, 0.2, k), lerp(0.085, 0.07, k), lerp(0.035, -0.06, k), 0.05 * k, \
            LOB_L.lerp(TUCK_L, k), ("whip", k)
    if f <= 15:
        k = ease((f - RELEASE) / 5.0)
        return lerp(-4.0, 10.0, k), lerp(6.0, 12.0, k), lerp(0.2, 0.36, k), lerp(0.07, 0.11, k), lerp(-0.06, -0.07, k), 0.05, \
            TUCK_L, ("follow", k)
    if f <= FRESH:
        k = ease((f - 15) / float(FRESH - 15))
        return lerp(10.0, -10.0, k), lerp(12.0, 2.0, k), lerp(0.36, 0.22, k), lerp(0.11, 0.1, k), lerp(-0.07, -0.02, k), 0.05 * (1 - k), \
            TUCK_L.lerp(V(0.34, -0.3, 1.2), k), ("pouch", k)
    if f <= LIGHT:
        k = ease((f - FRESH) / float(LIGHT - FRESH))
        return lerp(-10.0, -18.0, k), lerp(2.0, -6.0, k), lerp(0.22, 0.12, k), lerp(0.1, 0.075, k), lerp(-0.02, 0.0, k), 0.0, \
            V(0.34, -0.3, 1.2).lerp(V(0.3, -0.46, 1.3), k), ("light", k)
    k = ease((f - LIGHT) / float(FR - LIGHT))
    return lerp(-18.0, C_YAW, k), lerp(-6.0, -14.0, k), lerp(0.12, 0.08, k), lerp(0.075, 0.065, k), 0.0, 0.0, \
        V(0.3, -0.46, 1.3).lerp(AIM_L, k), ("cock", k)


def light_pose(arm, P, R, yaw, k_from=None):
    """The grenade's fuse on the match (its sparks catch): the fuse pointing back and down into his chest."""
    m = R.match(P)
    fuse = rz(yaw) @ V(0.1, 0.65, -0.75)
    fing = rz(yaw) @ V(0.55, -0.2, 0.8)
    aims, center = fuse_grip(arm, m, fuse, fing, pole=rz(yaw) @ V(-0.8, -0.2, -0.6))
    return aims, center


def attack_pose(arm, f, R, P_prev=None):
    """The aims at frame f (two passes where the fuse must meet the match on his posed chest)."""
    yaw, chest, bend, crouch, ro_y, heel, wl, (phase, k) = attack_state(f)
    ro = rz(yaw) @ V(0.0, ro_y, 0.0) + V(0.0, 0.0, -crouch)
    aims = feet(arm, C_YAW, lift=(0.0, heel), **C_FEET)
    torso(aims, yaw, bend=bend, chest=chest, look=0.0, pitch=0.05 - 0.12 * bend)
    aims.update(hand_on(arm, "L", wl + ro, AIM_FING if phase not in ("whip", "follow") else V(0.1, 0.3, -1.0),
                        AIM_PALM if phase != "wind" else V(0.2, -0.3, -0.9), pole=V(0.9, 0.2, -0.6)))
    aims["cap"] = cap_on_head(R)
    aims["grenade"] = grenade_in_hand(R)
    return yaw, ro, aims, phase, k


def make_attack(arm, frames=FR):
    P0 = Poser(arm)
    R = Rest(arm)
    act = new_action(arm, "Attack")
    ro0 = V(0.0, 0.0, -0.065)
    c_c, c_f, c_p, c_pole = cocked(C_YAW, ro0)
    for f in range(frames + 1):
        yaw, ro, aims, phase, k = attack_pose(arm, f, R)
        # a first pass for where his chest (the match) and hips (the pouch) are
        base = dict(aims)
        base.update(ball_grip(arm, c_c, c_f, c_p, c_pole))
        _, P = P0.solve(base, ro, rz(yaw))
        if phase == "wind":
            c, fg, pm, pole = cocked(C_YAW, ro0)
            c2 = body_pt(WIND_C, ro, yaw)
            aims.update(ball_grip(arm, c.lerp(c2, k), mixd(fg, rz(yaw) @ WIND_FING, k), mixd(pm, rz(yaw) @ WIND_PALM, k),
                                  c_pole.lerp(rz(yaw) @ V(-0.8, 0.5, -0.3), k)))
        elif phase == "whip":
            s6 = attack_state(6)
            c1 = body_pt(WIND_C, rz(s6[0]) @ V(0.0, s6[4], 0.0) + V(0.0, 0.0, -s6[3]), s6[0])
            top = c1.lerp(REL_C + ro, 0.5) + V(-0.22, 0.06, 0.24)              # over the top, out beside his cap
            aims.update(ball_grip(arm, bez_p(c1, top, REL_C + ro, k), bez_d(rz(yaw) @ WIND_FING, V(-0.1, 0.2, 1.0), REL_FING, k),
                                  bez_d(rz(yaw) @ WIND_PALM, V(0.0, -0.5, 0.6), REL_PALM, k), V(-0.9, 0.3, -0.2)))
        elif phase == "follow":
            aims.update(ball_grip(arm, (REL_C + ro).lerp(FOL_C + ro, k) + V(-0.12, -0.08, 0.0) * math.sin(math.pi * k), mixd(REL_FING, FOL_FING, k), mixd(REL_PALM, FOL_PALM, k),
                                  V(-0.9, 0.3, -0.2).lerp(V(-0.6, 0.7, -0.4), k)))
        elif phase == "pouch":
            c, fg, pm, pole = pouch_pose(yaw, ro)
            arc = math.sin(math.pi * k)
            aims.update(ball_grip(arm, (FOL_C + ro).lerp(c, k) + V(-0.06, 0.0, 0.05) * arc, mixd(FOL_FING, fg, k), mixd(FOL_PALM, pm, k),
                                  V(-0.6, 0.7, -0.4).lerp(pole, k)))
        elif phase == "light":
            c, fg, pm, pole = pouch_pose(yaw, ro)
            la, lc = light_pose(arm, P, R, yaw)
            Rl = la["hand.R"]
            fg2 = frame_map(Rl[1], Rl[2], Rl[3], Rl[4]) @ F_R
            pm2 = frame_map(Rl[1], Rl[2], Rl[3], Rl[4]) @ N_R
            kk = smooth01(k / 0.85)
            aims.update(ball_grip(arm, c.lerp(lc, kk) + V(0.0, -0.06, 0.04) * math.sin(math.pi * kk), mixd(fg, fg2, kk), mixd(pm, pm2, kk),
                                  pole.lerp(rz(yaw) @ V(-0.8, -0.2, -0.6), kk)))
        else:                                                                    # cock it back again
            la, lc = light_pose(arm, P, R, attack_state(LIGHT)[0])
            Rl = la["hand.R"]
            fg2 = frame_map(Rl[1], Rl[2], Rl[3], Rl[4]) @ F_R
            pm2 = frame_map(Rl[1], Rl[2], Rl[3], Rl[4]) @ N_R
            c, fg, pm, pole = cocked(C_YAW, ro0)
            aims.update(ball_grip(arm, lc.lerp(c, k) + V(-0.08, 0.06, 0.1) * math.sin(math.pi * k), mixd(fg2, fg, k), mixd(pm2, pm, k),
                                  (rz(yaw) @ V(-0.8, -0.2, -0.6)).lerp(c_pole, k)))
        sc = {"grenade": 0.0 if RELEASE < f < FRESH else 1.0, "spark": 1.0 if (f <= RELEASE or f >= LIGHT) else 0.0}
        ch, _ = P0.solve(aims, ro, rz(yaw), scales=sc)
        P0.key(ch, f)
    key_constant(act, 'pose.bones["grenade"].scale')
    key_constant(act, 'pose.bones["spark"].scale')
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- ability: powder keg
KEG_TURN = -58.0                            # turned to the keg by his right foot
SQ_FEET = dict(lf=(0.27, 0.0), rf=(-0.25, 0.08), turn=(16.0, -16.0))
FRONT_FEET = dict(lf=(0.19, -0.1), rf=(-0.19, 0.1), turn=(6.0, -14.0))


def keg_matrix(R, mid, axis_q):
    """The keg bone's pose with the keg's middle at `mid`, turned by axis_q from upright."""
    rot = axis_q.to_matrix()
    M = rot.to_4x4() @ R.m["keg"].to_3x3().to_4x4()
    M.translation = Vector(mid) + rot @ (KEG_HEAD - KEG_MID)
    return M


def keg_point(R, M, p_rest):
    """Where a point of the keg (rest coordinates) is when its bone is at M."""
    return M @ (R.m["keg"].inverted() @ Vector(p_rest))


def ability_state(f):
    """(yaw, feet, chest, bend, crouch, pitch, keg mode, k)."""
    if f <= TUCK:
        k = ease(f / float(TUCK))
        return lerp(C_YAW, -46.0, k), "c", lerp(-14.0, -4.0, k), lerp(0.08, 0.2, k), lerp(0.065, 0.12, k), 0.0, "tuck", k
    if f <= K_GRIP:
        k = ease((f - TUCK) / float(K_GRIP - TUCK))
        return lerp(-46.0, KEG_TURN, k), "s", lerp(-4.0, 0.0, k), lerp(0.2, 0.82, k), lerp(0.12, 0.5, k), lerp(0.0, -0.3, k), "reach", k
    if f <= K_SHOULDER:
        k = ease((f - K_GRIP) / float(K_SHOULDER - K_GRIP))
        return lerp(KEG_TURN, -20.0, k), "f", lerp(0.0, -6.0, k), lerp(0.82, -0.04, k), lerp(0.5, 0.06, k), lerp(-0.3, 0.1, k), "lift", k
    if f <= K_LIGHT:
        k = ease((f - K_SHOULDER) / float(K_LIGHT - K_SHOULDER))
        return lerp(-20.0, -8.0, k), "f", lerp(-6.0, 0.0, k), lerp(-0.04, 0.14, k), lerp(0.06, 0.08, k), lerp(0.1, -0.15, k), "lower", k
    if f <= K_HIGH:
        k = ease((f - K_LIGHT) / float(K_HIGH - K_LIGHT))
        return lerp(-8.0, 0.0, k), "f", 0.0, lerp(0.14, -0.26, k), lerp(0.08, 0.04, k), lerp(-0.15, 0.3, k), "raise", k
    if f <= K_RELEASE:
        k = ((f - K_HIGH) / float(K_RELEASE - K_HIGH)) ** 1.3
        return 0.0, "f", 0.0, lerp(-0.26, 0.26, k), lerp(0.04, 0.1, k), lerp(0.3, 0.05, k), "heave", k
    if f <= 52:
        k = ease((f - K_RELEASE) / 7.0)
        return lerp(0.0, -6.0, k), "f", 0.0, lerp(0.26, 0.12, k), lerp(0.1, 0.07, k), lerp(0.05, 0.12, k), "watch", k
    if f <= A_FRESH:
        k = ease((f - 52) / float(A_FRESH - 52))
        return lerp(-6.0, -10.0, k), "f", lerp(0.0, 2.0, k), lerp(0.12, 0.2, k), lerp(0.07, 0.09, k), lerp(0.12, 0.0, k), "pouch", k
    if f <= A_LIGHT:
        k = ease((f - A_FRESH) / float(A_LIGHT - A_FRESH))
        return lerp(-10.0, -18.0, k), "f", lerp(2.0, -6.0, k), lerp(0.2, 0.12, k), lerp(0.09, 0.075, k), 0.0, "light", k
    k = ease((f - A_LIGHT) / float(A_FR - A_LIGHT))
    return lerp(-18.0, C_YAW, k), "c", lerp(-6.0, -14.0, k), lerp(0.12, 0.08, k), lerp(0.075, 0.065, k), lerp(0.0, 0.05, k), "cock", k


def make_ability(arm, frames=A_FR):
    P0 = Poser(arm)
    R = Rest(arm)
    act = new_action(arm, "Ability")
    ro0 = V(0.0, 0.0, -0.065)
    c_c, c_f, c_p, c_pole = cocked(C_YAW, ro0)
    keg_rest = R.m["keg"]
    up = Quaternion()
    feet_of = {"c": C_FEET, "s": SQ_FEET, "f": FRONT_FEET}
    # the keg's key poses (world): on his shoulder, before his chest (tilted to him), over his head, heaved out
    SH_MID, SH_Q = V(-0.37, 0.04, 1.66), Quaternion((1, 0, 0), math.radians(90)) @ Quaternion((0, 0, 1), math.radians(10))
    HI_MID, HI_Q = V(0.0, -0.31, 1.97), Quaternion((0, 1, 0), math.radians(90))          # (before his tall cap)
    OUT_MID, OUT_Q = V(0.0, -0.58, 1.8), Quaternion((0, 1, 0), math.radians(90)) @ Quaternion((1, 0, 0), math.radians(-25))
    prev_feet = None
    to_keg = (KEG_MID - ROOT)
    to_keg = V(to_keg.x, to_keg.y, 0.0).normalized()
    for f in range(frames + 1):
        yaw, fk, chest, bend, crouch, pitch, mode, k = ability_state(f)
        step = 0.17 * (smooth01((f - TUCK) / float(K_GRIP - TUCK)) - smooth01((f - K_GRIP) / float(K_SHOULDER - K_GRIP)))
        ro = V(0.0, 0.0, -crouch) + rz(yaw) @ V(0.0, -0.08 * bend, 0.0) + to_keg * step
        # feet: re-planted as he turns (a short step), from the stance to the squat to square on, and back
        fs = feet_of[fk]
        if mode == "tuck":
            aims = feet(arm, lerp(C_YAW, -46.0, k), **{kk: tuple(lerp(a, b, k) for a, b in zip(C_FEET[kk], SQ_FEET[kk])) for kk in ("lf", "rf", "turn")})
        elif mode == "reach":
            aims = feet(arm, lerp(-46.0, KEG_TURN, k), **SQ_FEET)
        elif mode == "lift":
            aims = feet(arm, lerp(KEG_TURN, -6.0, k), **{kk: tuple(lerp(a, b, k) for a, b in zip(SQ_FEET[kk], FRONT_FEET[kk])) for kk in ("lf", "rf", "turn")})
        elif mode == "cock":
            aims = feet(arm, lerp(-6.0, C_YAW, k), **{kk: tuple(lerp(a, b, k) for a, b in zip(FRONT_FEET[kk], C_FEET[kk])) for kk in ("lf", "rf", "turn")})
        else:
            aims = feet(arm, -6.0, **FRONT_FEET)
        torso(aims, yaw, bend=bend, chest=chest, look=yaw * 0.6 if mode in ("tuck", "reach", "lift") else 0.0, pitch=pitch)
        aims["cap"] = cap_on_head(R)
        aims["grenade"] = grenade_in_hand(R)
        sc = {"keg": 1.0, "keg_spark": 0.0, "grenade": 1.0, "spark": 1.0}
        keg_M = None
        # first pass (chest, hips) with the hands left where they rest
        base = dict(aims)
        base.update(ball_grip(arm, c_c, c_f, c_p, c_pole))
        _, P = P0.solve(base, ro, rz(yaw))
        q = rz(yaw)
        if mode in ("tuck", "pouch", "light", "cock"):
            # the grenade hand: to the pouch (tuck the lit one away / draw a fresh one), to the match, cocked
            pc, pfg, ppm, ppole = pouch_pose(yaw, ro)
            if mode == "tuck":
                aims.update(ball_grip(arm, c_c.lerp(pc, k) + (q @ V(-0.12, -0.24, 0.0)) * math.sin(math.pi * k), mixd(c_f, pfg, k),
                                      mixd(c_p, ppm, k), c_pole.lerp(ppole, k)))
                sc["grenade"] = 0.0 if f >= TUCK else 1.0
            elif mode == "pouch":
                start = q @ V(-0.3, -0.42, 1.36) + ROOT
                aims.update(ball_grip(arm, start.lerp(pc, k), mixd(q @ V(0.0, -0.6, 0.8), pfg, k), mixd(q @ V(0.0, -0.8, -0.5), ppm, k),
                                      (q @ V(-0.8, 0.4, -0.4)).lerp(ppole, k)))
                sc["grenade"] = 1.0 if f >= A_FRESH else 0.0
                sc["spark"] = 0.0
            elif mode == "light":
                la, lc = light_pose(arm, P, R, yaw)
                Rl = la["hand.R"]
                fg2 = frame_map(Rl[1], Rl[2], Rl[3], Rl[4]) @ F_R
                pm2 = frame_map(Rl[1], Rl[2], Rl[3], Rl[4]) @ N_R
                kk = smooth01(k / 0.85)
                aims.update(ball_grip(arm, pc.lerp(lc, kk) + V(0.0, -0.06, 0.04) * math.sin(math.pi * kk), mixd(pfg, fg2, kk),
                                      mixd(ppm, pm2, kk), ppole.lerp(q @ V(-0.8, -0.2, -0.6), kk)))
                sc["spark"] = 1.0 if f >= A_LIGHT else 0.0
            else:
                la, lc = light_pose(arm, P, R, ability_state(A_LIGHT)[0])
                Rl = la["hand.R"]
                fg2 = frame_map(Rl[1], Rl[2], Rl[3], Rl[4]) @ F_R
                pm2 = frame_map(Rl[1], Rl[2], Rl[3], Rl[4]) @ N_R
                c, fg, pm, pole = cocked(C_YAW, ro0)
                aims.update(ball_grip(arm, lc.lerp(c, k) + V(-0.08, 0.06, 0.1) * math.sin(math.pi * k), mixd(fg2, fg, k), mixd(pm2, pm, k),
                                      (q @ V(-0.8, -0.2, -0.6)).lerp(c_pole, k)))
            if mode == "tuck":
                aims.update(hand_on(arm, "L", (AIM_L + ro).lerp(body_pt(V(0.3, -0.3, 1.05), ro, yaw), k), mixd(AIM_FING, q @ V(0.0, -0.6, -0.8), k),
                                    mixd(AIM_PALM, q @ V(-0.8, 0.0, -0.5), k), pole=V(0.9, 0.2, -0.6)))
            else:
                wl = body_pt(V(0.32, -0.34, 1.2), ro, yaw)
                if mode == "cock":
                    wl = wl.lerp(AIM_L + ro, k)
                aims.update(hand_on(arm, "L", wl, AIM_FING, AIM_PALM, pole=V(0.9, 0.2, -0.6)))
            sc["keg"] = 0.0 if f > K_RELEASE else 1.0
            if mode in ("pouch", "light", "cock"):
                sc["keg"] = 0.0
            if f >= frames:
                sc["keg"] = 1.0                                                   # (the next keg is there again by his foot)
        else:
            sc["grenade"] = 0.0
            sc["spark"] = 0.0
            # the keg in his hands: its pose, then each hand on its sides
            if mode == "reach":
                keg_M = keg_rest.copy()
            elif mode == "lift":
                mid0 = KEG_MID
                kk = smooth01(k)
                mid = bez_p(mid0, V(-0.82, -0.24, 1.06), SH_MID, kk)              # (swung out at his side and up)
                keg_M = keg_matrix(R, mid, up.slerp(SH_Q, smooth01((k - 0.2) / 0.8)))
            elif mode == "lower":
                # before his chest, its top tipped to him, the fuse on the match
                m = R.match(P)
                tq = rz(yaw) @ Quaternion((1, 0, 0), math.radians(-82))
                Mtmp = keg_matrix(R, V(0, 0, 0), tq)
                tip_off = keg_point(R, Mtmp, KEG_TIP)
                mid_l = m - tip_off + V(0, 0, 0)
                kk = smooth01(k / 0.8)
                keg_M = keg_matrix(R, SH_MID.lerp(mid_l, kk) + V(0.0, -0.1, 0.06) * math.sin(math.pi * kk), SH_Q.slerp(tq, kk))
                sc["keg_spark"] = 1.0 if f >= K_LIGHT else 0.0
            elif mode == "raise":
                m = R.match(P)
                tq = rz(ability_state(K_LIGHT)[0]) @ Quaternion((1, 0, 0), math.radians(-82))
                mid_l = m - keg_point(R, keg_matrix(R, V(0, 0, 0), tq), KEG_TIP)
                keg_M = keg_matrix(R, bez_p(mid_l, V(0.0, -0.44, 1.72), HI_MID, k), tq.slerp(HI_Q, k))
                sc["keg_spark"] = 1.0
            elif mode == "heave":
                keg_M = keg_matrix(R, HI_MID.lerp(OUT_MID, k) + V(0, 0, 0.08) * math.sin(math.pi * k), HI_Q.slerp(OUT_Q, k))
                sc["keg_spark"] = 1.0
                sc["keg"] = 1.0
            else:                                                                 # watch it go
                keg_M = keg_matrix(R, OUT_MID, OUT_Q)
                sc["keg"] = 0.0 if f > K_RELEASE else 1.0
                sc["keg_spark"] = 1.0
            if mode != "watch":
                aims["keg"] = ("world", keg_M)
            # hands on the keg's sides (its middle, either side across his body), the fingers along it
            ax = (keg_M.to_3x3() @ (keg_rest.to_3x3().inverted() @ V(0, 0, 1))).normalized()
            mid = keg_point(R, keg_M, KEG_MID)
            across = (q @ V(1.0, 0.0, 0.0))
            across = (across - ax * across.dot(ax)).normalized()
            if mode == "watch":
                kk = smooth01(k)
                cr = (mid - across * 0.14).lerp(body_pt(V(-0.3, -0.42, 1.36), ro, yaw), kk)
                cl = (mid + across * 0.14).lerp(body_pt(V(0.3, -0.42, 1.36), ro, yaw), kk)
                aims.update(hand_on(arm, "R", cr, q @ V(0.0, -0.6, 0.8), q @ V(0.0, -0.8, -0.5), pole=q @ V(-0.8, 0.4, -0.4)))
                aims.update(hand_on(arm, "L", cl, q @ V(0.0, -0.6, 0.8), q @ V(0.0, -0.8, -0.5), pole=q @ V(0.8, 0.4, -0.4)))
            else:
                rk = cm.KEG_R1 + 0.012
                left = q @ V(1.0, 0.0, 0.0)
                ends = abs(ax.dot(left)) > 0.6                                   # lying across him: hold it by its heads
                if ends:
                    sx = 1.0 if ax.dot(left) > 0 else -1.0
                    cl = mid + ax * (sx * (cm.KEG_H / 2 + 0.012))
                    cr = mid - ax * (sx * (cm.KEG_H / 2 + 0.012))
                    upd = (V(0, 0, 1) - ax * ax.z).normalized()
                    aims.update(hand_on(arm, "R", cr, upd, ax * sx, pole=q @ V(-0.9, 0.2, -0.5)))
                    aims.update(hand_on(arm, "L", cl, upd, -ax * sx, pole=q @ V(0.9, 0.2, -0.5)))
                else:
                    rim = 0.1 if mode == "reach" else (0.1 * (1 - smooth01(k / 0.5)) if mode == "lift" else 0.0)
                    if mode == "lower":
                        rim = 0.06 * smooth01(k / 0.6)                               # (its near half, toward him)
                    cr = mid - across * rk + ax * rim                               # (low down: its upper sides, by the rim)
                    cl = mid + across * rk + ax * rim
                    if mode == "reach":
                        kk = smooth01(k)
                        st_r = body_pt(V(-0.3, -0.3, 1.0), ro, yaw)
                        st_l = body_pt(V(0.3, -0.3, 1.05), ro, yaw)
                        cr, cl = st_r.lerp(cr, kk), st_l.lerp(cl, kk)
                    aims.update(hand_on(arm, "R", cr, ax, across, pole=q @ V(-0.9, 0.2, -0.4)))
                    w = 0.0
                    if mode in ("lift", "lower"):
                        # while it rides his shoulder (his right hand on it) his left fist goes to his hip
                        w = smooth01((k - 0.45) / 0.45) if mode == "lift" else 1.0 - smooth01((k - 0.05) / 0.45)
                    hip = body_pt(HIP_L, ro, yaw)
                    if w > 0.0:
                        Ra = frame_map(F_L, ax, N_L, -across)
                        Rb = frame_map(F_L, q @ HIP_L_FING, N_L, q @ HIP_L_PALM)
                        qa, qb = Ra.to_quaternion(), Rb.to_quaternion()
                        Rm = qa.slerp(qb, w).to_matrix()
                        cl2 = cl.lerp(hip, w) + V(0.08, 0.0, 0.05) * math.sin(math.pi * w)
                        aims.update(hand_on(arm, "L", cl2, Rm @ F_L, Rm @ N_L, pole=(q @ V(0.9, 0.2, -0.4)).lerp(q @ V(1.0, 0.25, 0.1), w)))
                    else:
                        aims.update(hand_on(arm, "L", cl, ax, -across, pole=q @ V(0.9, 0.2, -0.4)))
        ch, _ = P0.solve(aims, ro, rz(yaw), scales=sc)
        P0.key(ch, f)
    for b in ("grenade", "spark", "keg", "keg_spark"):
        key_constant(act, 'pose.bones["%s"].scale' % b)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- cheer
CH_FR = 40
PALM_UP = V(0.47, -0.08, 1.96)                # his left palm with the cap held high, out past his head


def make_cheer(arm, frames=CH_FR):
    """Rank up: the cap off and raised high in his left hand, waved; his right fist (the grenade in it) pumped twice; a
    laugh, his head back, a hop; the cap back on."""
    P0 = Poser(arm)
    R = Rest(arm)
    act = new_action(arm, "Cheer")
    # the left hand's grip on the cap (its left side, at the band), in the cap's own frame
    cap_rest = R.m["cap"]
    grip_c = vec(cm.cap_root()) + V(0.215, 0.02, 0.0)
    rot = frame_map(F_L, V(0.0, 0.15, 1.0), N_L, V(-1.0, 0.0, 0.0))
    hand_rest = R.m["hand.L"].to_3x3()
    Mh = (rot @ hand_rest).to_4x4()
    Mh.translation = grip_c - rot @ PALM_L
    CAP2HAND = cap_rest.inverted() @ Mh
    for f in range(frames + 1):
        t = f / float(frames)
        up = smooth01((f - 6) / 8.0) * (1 - smooth01((f - 30) / 7.0))
        grab = smooth01(f / 6.0) * (1 - smooth01((f - 36) / 4.0))
        pump = max(0.0, math.sin((f - 10) / 20.0 * 2 * math.pi * 2)) * smooth01((f - 9) / 3.0) * (1 - smooth01((f - 29) / 3.0))
        laugh = math.sin(f * 1.3) * up
        hop = max(0.0, math.sin((f - 10) / 20.0 * 2 * math.pi * 2 - 0.5)) * 0.03 * up
        ro = V(0.0, 0.0, -0.015 + hop + 0.004 * laugh)
        aims = feet(arm, 0.0, lf=(0.21, -0.03), rf=(-0.2, 0.06), turn=(12.0, -10.0), lift=(hop * 0.5, hop * 0.5))
        torso(aims, 0.0, bend=-0.08 * up, side=0.04 * up, look=6.0 * math.sin(f * 0.4) * up, pitch=0.05 + 0.4 * up + 0.04 * laugh)
        # the right fist: from the idle hold, pumped up beside his head
        hold = body_pt(HOLD_C, ro, 0.0)
        top = V(-0.36, -0.12, 1.66 + 0.2 * pump)
        c = hold.lerp(top + ro, smooth01((f - 4) / 6.0) * (1 - smooth01((f - 33) / 6.0)))
        kk = smooth01((f - 4) / 6.0) * (1 - smooth01((f - 33) / 6.0))
        aims.update(ball_grip(arm, c, mixd(HOLD_FING, V(0.1, -0.2, 1.0), kk), mixd(HOLD_PALM, V(0.6, -0.8, 0.0), kk),
                              pole=V(-0.8, 0.6, -0.3).lerp(V(-1.0, 0.2, -0.4), kk)))
        # first pass: where is his head?
        base = dict(aims)
        base.update(hand_on(arm, "L", body_pt(HIP_L, ro, 0.0), HIP_L_FING, HIP_L_PALM, pole=V(1.0, 0.25, 0.1)))
        _, P = P0.solve(base, ro, Quaternion())
        on_head = P["head"] @ R.h2c
        if 6 <= f <= 37:
            wave = math.sin((f - 14) * 0.55) * smooth01((f - 13) / 3.0) * (1 - smooth01((f - 28) / 3.0))
            q_up = Quaternion((0, -1, 0), math.radians(18 + 14 * wave)) @ Quaternion((1, 0, 0), math.radians(-12))
            M_tmp = free_matrix(cap_rest, V(0, 0, 0), q_up)
            grip = (M_tmp @ CAP2HAND) @ (hand_rest.inverted().to_4x4() @ Vector(PALM_L))       # the palm, the cap's root at 0
            palm = PALM_UP + V(0.03 * wave, 0.0, 0.03 * pump) + ro
            M_up = free_matrix(cap_rest, palm - grip, q_up)
            k = up
            loc = on_head.translation.lerp(M_up.translation, k) + V(0.06, 0.0, 0.1) * math.sin(math.pi * k)
            qr = on_head.to_quaternion().slerp(M_up.to_quaternion(), k)
            M_cap = qr.to_matrix().to_4x4()
            M_cap.translation = loc
            aims["cap"] = ("world", M_cap)
            aims.update(hand_matrix(arm, "L", M_cap @ CAP2HAND, pole=V(1.0, 0.2, -0.3)))
        else:
            aims["cap"] = cap_on_head(R)
            k = smooth01(f / 6.0) if f < 6 else 1.0 - smooth01((f - 37) / 3.0)
            hip = body_pt(HIP_L, ro, 0.0)
            Mg = on_head @ CAP2HAND
            rot_h = frame_map(F_L, HIP_L_FING, N_L, HIP_L_PALM)
            Mhip = (rot_h @ hand_rest).to_4x4()
            Mhip.translation = hip - rot_h @ PALM_L
            loc = Mhip.translation.lerp(Mg.translation, k) + V(0.08, -0.05, 0.0) * math.sin(math.pi * k)
            qr = Mhip.to_quaternion().slerp(Mg.to_quaternion(), k)
            Mx = qr.to_matrix().to_4x4()
            Mx.translation = loc
            aims.update(hand_matrix(arm, "L", Mx, pole=V(1.0, 0.25, 0.0)))
        aims["grenade"] = grenade_in_hand(R)
        ch, _ = P0.solve(aims, ro, Quaternion(), scales={"spark": 0.0})
        P0.key(ch, f)
    key_constant(act, 'pose.bones["spark"].scale')
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- loops
def make_idle(arm, frames=I_FR):
    P = Poser(arm)
    R = Rest(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, f, R)
        ch, _ = P.solve(aims, ro, rr, scales={"spark": 0.0})
        P.key(ch, f)
    key_constant(act, 'pose.bones["spark"].scale')
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    P = Poser(arm)
    R = Rest(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr = combat_pose(arm, (f % frames) / frames, R)
        ch, _ = P.solve(aims, ro, rr)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def key_constant(act, path):
    """Make every key on the curve `path` constant (a thing popping into or out of sight)."""
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
