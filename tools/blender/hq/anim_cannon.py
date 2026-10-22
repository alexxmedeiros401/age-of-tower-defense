"""Cannon clips (game: 24 fps).

Idle   : the gun loaded and run out; he stands by the breech beside the near wheel, the linstock grounded at his right
         side, his left hand resting on the wheel's tyre; he breathes, looks out over the gun and about, and once lifts
         the linstock to his face and blows on the match.
Combat : ready to fire: turned to the vent, the linstock held out low in his right fist, the match a hand's breadth over
         the touch hole, his left fist on his hip.
Attack : (52 frames, inside the 2.2 s cooldown) he puts the match to the vent and the gun fires (SHOT, frame 2: the
         game's flash, smoke and ball leave the muzzle there): gun and carriage leap back, the muzzle kicking up and the
         wheels rolling back, and he flinches away. He stabs the linstock into the deck at his side, grabs the
         rammer-and-sponge from the front of the wheel, swabs the bore, takes a round from his cartridge bag and pushes it
         into the muzzle, turns the staff about and rams the round home, leans the staff back against the wheel, hauls the
         wheel round to run the gun out again, plucks up the linstock and holds the match over the vent again.

The gun's bones are posed directly: carriage (rolled back by its offset, rocked about the trail's end), the wheels
(turning about the axle as it rolls). His three props are free bones posed in the world: the linstock rides his right
fist (sliding through it) or stands planted in the deck; the rammer rides the carriage while it leans on the wheel, or his
hands; the round rides his left hand, then the bore (its scale hides it in the bag and once it is rammed home)."""
import math
from mathutils import Vector, Quaternion, Matrix
import cannon as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

_wrR, _fR, _nR, _tR = cm.hand_frame("R")
WR_R, T_R, F_R, N_R = vec(_wrR), vec(_tR), vec(_fR), vec(_nR)
FIST_R = vec(cm.fist_center("R"))
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
WR_L, T_L, F_L, N_L = vec(_wrL), vec(_tL), vec(_fL), vec(_nL)
FIST_L = vec(cm.fist_center("L"))

_G, _T, _Fv, _B, _f0 = cm.linstock_frame()
LS_T, LS_FV, LS_B, LS_F0 = vec(_T), vec(_Fv), vec(_B), vec(_f0)
EMB = vec(cm.ember_pt())
LS_GRIP = cm.LS_GRIP

RAM_F0, RAM_AX = vec(cm.R_FOOT), vec(cm.R_AX)
RAM_SD = RAM_AX.cross(V(1.0, 0.0, 0.0)).normalized()
RAM_LEN = cm.RAM_LEN
_C, _A = cm.round_frame()
RD_C, RD_A = vec(_C), vec(_A)
RD_SD = RD_A.cross(V(0.0, 0.0, 1.0)).normalized()

GD, GU = vec(cm.GD), vec(cm.GU)
MUZ, VENT = vec(cm.MUZZLE), vec(cm.VENT)
KP = vec(cm.KICK_P)
SAT = vec(cm.sat_mouth())

# ---------------------------------------------------------------------------------------------- timing (24 fps)
SHOT = 2           # the match on the vent: the gun fires (game: flash, smoke and the ball at the muzzle)
REC_END = 7        # fully recoiled
FLINCH = 4
PLANT = 10         # the linstock's point in the deck; he lets go after it
GRAB = 13          # his hands on the rammer
AT_L = 16          # at the muzzle, the sponge at its mouth
SW_IN = 19         # the sponge pushed home
SW_TW = 20         # ...given a turn
SW_OUT = 22        # pulled out
UPRIGHT = 24       # the staff upright in his right fist
BAG = 25           # his left hand in the cartridge bag: the round appears in it
RD_IN = 28         # the round pushed into the muzzle's mouth
RAM_AT = 30        # the rammer's face at the mouth
RAM_IN = 33        # rammed home (the round hidden in the bore)
RAM_OUT = 35       # the rammer out
LEAN = 38          # the staff back against the wheel
HEAVE0, HEAVE1 = 41, 47     # hauling the wheel round: the gun runs out
TAKE = 49          # the linstock in his fist
FR = 52            # = the 2.2 s cooldown (52.8 frames)

REC = 0.26         # the recoil (m)
KICK = 7.0         # the muzzle's kick (degrees, about the trail's end)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def fwd(yaw):
    return rz(yaw) @ V(0.0, -1.0, 0.0)


def rgt(yaw):
    return rz(yaw) @ V(-1.0, 0.0, 0.0)


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def wroot(x, y, z=None):
    return V(x, y, ROOT.z if z is None else z) - ROOT


def smooth_keys(keys, f, fn=ease):
    if f <= keys[0][0]:
        return keys[0][1]
    for (fa, a), (fb, b) in zip(keys, keys[1:]):
        if f <= fb:
            k = fn((f - fa) / float(fb - fa)) if fb > fa else 1.0
            return a.lerp(b, k) if isinstance(a, Vector) else a + (b - a) * k
    return keys[-1][1]


def xform(o0, a0, b0, o1, a1, b1):
    """The rigid motion taking the point o0 to o1, the direction a0 to a1 and the plane (a0, b0) to (a1, b1)."""
    R = frame_map(a0, a1, b0, b1)
    M = R.to_4x4()
    M.translation = o1 - R @ o0
    return M


def perp(v, ax):
    v = Vector(v) - ax * Vector(v).dot(ax)
    return v.normalized() if v.length > 1e-6 else (ax.orthogonal().normalized())


# ---------------------------------------------------------------------------------------------- the gun
def recoil(f):
    if f <= SHOT:
        return 0.0
    if f <= REC_END:
        k = (f - SHOT) / float(REC_END - SHOT)
        return REC * (1.0 - (1.0 - k) ** 3)
    if f <= HEAVE0:
        return REC
    if f <= HEAVE1:
        return REC * (1.0 - ease((f - HEAVE0) / float(HEAVE1 - HEAVE0)))
    return 0.0


def kick(f):
    """The muzzle's kick (degrees): the carriage rocks back about the trail's end, the wheels leave the deck, and it
    drops back with a little bounce."""
    if f <= SHOT:
        return 0.0
    t = f - SHOT
    if t <= 2:
        return KICK * t / 2.0
    if t <= 6:
        return KICK * (1.0 - ease((t - 2) / 4.0))
    if t <= 8:
        return -1.0 * math.sin(math.pi * (t - 6) / 2.0)
    return 0.0


def carr(f):
    """The carriage's motion at frame f (rest -> posed, for anything rigid with it)."""
    return (Matrix.Translation(KP + V(0.0, recoil(f), 0.0)) @ Matrix.Rotation(-math.radians(kick(f)), 4, "X")
            @ Matrix.Translation(-KP))


def muzzle_at(f):
    M = carr(f)
    return M @ MUZ, (M.to_3x3() @ GD).normalized()


def gun_aims(f):
    aims = {"carriage": ("rot", Quaternion((1, 0, 0), -math.radians(kick(f))))}
    roll = recoil(f) / cm.WR
    aims["wheel_a"] = (V(-1.0, 0.0, 0.0), roll)
    aims["wheel_b"] = (V(1.0, 0.0, 0.0), -roll)
    return aims, {"carriage": V(0.0, recoil(f), 0.0)}


# ---------------------------------------------------------------------------------------------- props
class Rest:
    """Rest matrices of the bones the props ride on (from the armature)."""
    def __init__(self, arm):
        b = arm.data.bones
        self.hand_r_inv = b["hand.R"].matrix_local.inverted()
        self.hand_l_inv = b["hand.L"].matrix_local.inverted()
        self.ls = b["linstock"].matrix_local.copy()
        self.ram = b["rammer"].matrix_local.copy()
        self.rd = b["round"].matrix_local.copy()


def ls_rot(hd, face):
    """The linstock's turn (rest -> world): its staff along hd, the fist's fingers toward face."""
    return frame_map(LS_T, hd, LS_FV, perp(face, hd))


def ls_fist_for_ember(E, hd, face, g):
    """Where his fist must be (holding the staff g from its point) for the match's end to be at E."""
    R = ls_rot(hd, face)
    f0 = E - R @ (EMB - LS_F0)
    return f0 + hd * g, R


def ls_planted(Q, hd, face):
    """The linstock standing with its point at Q."""
    R = ls_rot(hd, face)
    M = R.to_4x4()
    M.translation = Q - R @ LS_F0
    return M, R


def held_ls(rest, g):
    """The linstock riding his right fist, held g from its point (it slides through his fist)."""
    S = Matrix.Translation(LS_T * (LS_GRIP - g))
    def fn(P, base):
        return ("world", P["hand.R"] @ rest.hand_r_inv @ S @ rest.ls)
    return fn


def grip_r(arm, fist, R, pole):
    """His right fist at `fist`, the hand turned by R (rest -> world)."""
    aims = arm_aims(arm, "R", fist - R @ (FIST_R - WR_R), pole=pole)
    aims["hand.R"] = ("frame", T_R, R @ T_R, F_R, R @ F_R)
    return aims


def grip_l(arm, fist, R, pole):
    aims = arm_aims(arm, "L", fist - R @ (FIST_L - WR_L), pole=pole)
    aims["hand.L"] = ("frame", T_L, R @ T_L, F_L, R @ F_L)
    return aims


def ram_x(foot, ax, sd=None):
    """The rammer's placement: its rammer face at `foot`, the staff toward the sponge along ax."""
    ax = ax.normalized()
    sd = perp(sd if sd is not None else V(1.0, 0.0, 0.0), ax)
    return xform(RAM_F0, RAM_AX, RAM_SD, foot, ax, sd)


def ram_pt(X, s):
    return X @ (RAM_F0 + RAM_AX * s)


def ram_axis(X):
    return (X.to_3x3() @ RAM_AX).normalized()


def staff_hand_rot(side, ax, face, flip=False):
    """A fist's turn round a staff along ax: the thumb along the staff (toward ax's end unless flip), the knuckles toward
    face."""
    t = -ax if flip else ax
    if side == "R":
        return frame_map(T_R, t, F_R, perp(face, t))
    return frame_map(T_L, t, F_L, perp(face, t))


def round_hand(C, A, face):
    """His left hand holding the round: the ball at C, the cartridge along A; returns the wrist and the hand's turn."""
    R = frame_map(N_L, A.normalized(), F_L, perp(face, A.normalized()))
    return C - R @ (RD_C - WR_L), R


def round_x(C, A):
    A = A.normalized()
    return xform(RD_C, RD_A, RD_SD, C, A, perp(V(0.0, 0.0, 1.0), A))


# ---------------------------------------------------------------------------------------------- body
def feet(arm, lf, rf, yaw, lift_l=0.0, lift_r=0.0, foot_yaw=None):
    q = rz(yaw)
    fy = yaw if foot_yaw is None else foot_yaw
    aims = {}
    for side, p, lift in (("L", lf, lift_l), ("R", rf, lift_r)):
        z = float(J["ankle_" + side][2]) + lift
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims.update(leg_aims(arm, side, V(p[0], p[1], z), pole=pole))
        aims["foot." + side] = rz(fy + (-10 if side == "R" else 10)) @ rest_foot
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, br=0.0, tilt_head=0.0):
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend + 0.01 * br, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(0.0, -0.16 - 0.25 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(tilt_head), -0.06 + 0.55 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.04, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.04, 0.02)


# ---------------------------------------------------------------------------------------------- stations
S_XY, S_YAW = (0.1, -0.62), 122.0              # Combat: beside the near wheel, turned to the vent
I_XY, I_YAW = (0.2, -0.38), 40.0               # Idle: by the breech, looking out over the gun
Q_LS = V(-0.12, -0.9, -0.03)                   # where he plants the linstock (behind him, out of his way)
G_XY, G_YAW = (0.3, -0.9), 128.0              # grabbing the rammer at the front of the wheel
L_XY, L_YAW = (0.6, -1.22), 60.0               # loading: by the muzzle (run back), turned toward the bore
H0_XY, H1_XY, H_YAW = (0.24, -0.38), (0.24, -0.68), 90.0     # hauling the wheel round
G_COMBAT = 0.5                                 # where his fist holds the linstock to fire
G_STAND = 0.86                                 # ...to stand it on the deck
E_COMBAT = VENT + V(0.0, 0.0, 0.07)            # the match's end over the vent


def combat_ls(br=0.0, dip=0.0):
    """The linstock held out low toward the vent: (fist, R, g)."""
    E = E_COMBAT + V(0.0, 0.0, 0.004 * br - dip)
    root = V(S_XY[0], S_XY[1], 0.0)
    F0 = root + fwd(S_YAW) * 0.37 + rgt(S_YAW) * 0.25 + V(0.0, 0.0, 0.92 + 0.006 * br - dip * 0.6)
    hd = (E - F0).normalized()
    F, R = ls_fist_for_ember(E, hd, V(0.0, 0.0, -1.0), G_COMBAT)
    return F, R


def combat_core(arm, br=0.0, sw=0.0):
    yaw = S_YAW + 1.0 * sw
    ro = wroot(S_XY[0], S_XY[1], ROOT.z - 0.015 + 0.004 * br)
    aims = feet(arm, (0.24, -0.5), (0.08, -0.78), S_YAW - 8.0)
    torso(aims, yaw, bend=0.12, side=0.05, chest=-6.0, look=S_YAW - 2.0, pitch=-0.42, br=br)
    hip = body_pt(V(0.27, -0.04, 0.95), ro, yaw)
    aims.update(arm_aims(arm, "L", hip, pole=rz(yaw) @ V(1.0, 0.5, 0.1), hand_dir=rz(yaw) @ V(-0.35, 0.25, -1.0)))
    return aims, ro, yaw


def combat_pose(arm, t, rest):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    aims, ro, yaw = combat_core(arm, br, sw)
    F, R = combat_ls(br)
    aims.update(grip_r(arm, F, R, pole=rz(yaw) @ V(-1.0, 0.35, -0.5)))
    aims["linstock"] = held_ls(rest, G_COMBAT)
    return aims, ro, rz(yaw), {"round": 0.0}, {}


def idle_pose(arm, t, rest):
    """t in [0, 1): breathing, looking about; around t = 0.45 he lifts the linstock to his face and blows on the match."""
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    sway = math.sin(w)
    yaw = I_YAW + 3.0 * sway
    blow = math.sin(math.pi * min(1.0, max(0.0, (t - 0.33) / 0.26))) ** 2 if 0.33 < t < 0.59 else 0.0
    ro = wroot(I_XY[0] + 0.01 * sway, I_XY[1], ROOT.z - 0.01 + 0.005 * br)
    aims = feet(arm, (0.34, -0.26), (0.06, -0.48), I_YAW)
    look = yaw - 8.0 + 30.0 * math.sin(w) * (1.0 - blow) + 10.0 * math.sin(w * 3) * (1.0 - blow) + 22.0 * blow
    torso(aims, yaw, bend=0.04 + 0.1 * blow, side=0.03 * sway, chest=2.0 * sway + 8.0 * blow, look=look,
          pitch=0.05 + 0.03 * br - 0.25 * blow, br=br)
    q = rz(yaw)
    # the linstock grounded at his right side; raised to his mouth to blow on the match
    Qi = body_pt(V(-0.35, -0.08, 0.0), ro, I_YAW)
    Qi.z = -0.03
    face = fwd(yaw)
    hd_g = V(-0.06, 0.0, 1.0).normalized()
    _, R = ls_planted(Qi, rz(I_YAW) @ hd_g, face)
    Fg = Qi + (rz(I_YAW) @ hd_g) * G_STAND
    mouth = body_pt(cm.hp((0.0, -0.3, 1.56)), ro, yaw) + V(0.0, 0.0, -0.01)
    hd_b = (rz(yaw) @ V(0.1, 0.25, 1.0)).normalized()
    Fb, Rb = ls_fist_for_ember(mouth + fwd(yaw) * 0.05, hd_b, face, G_STAND)
    if blow > 0.0:
        F = Fg.lerp(Fb, blow)
        hd = (rz(I_YAW) @ hd_g).lerp(hd_b, blow).normalized()
        R = ls_rot(hd, face)
    else:
        F, hd = Fg, rz(I_YAW) @ hd_g
    aims.update(grip_r(arm, F, R, pole=q @ V(-1.0, 0.6, -0.3)))
    aims["linstock"] = held_ls(rest, G_STAND)
    # his left hand on the near wheel's tyre
    top = V(cm.MX - cm.WX - 0.012, cm.AY + 0.06, 2 * cm.WR + 0.04 + 0.004 * br)
    Rl = frame_map(N_L, V(0.0, 0.0, -1.0), F_L, perp(fwd(yaw) + rgt(yaw) * -0.6, V(0.0, 0.0, -1.0)))
    wrist = top - Rl @ (FIST_L - WR_L) + V(0.0, 0.0, 0.03)
    aims.update(arm_aims(arm, "L", wrist, pole=q @ V(1.0, 0.6, -0.1)))
    aims["hand.L"] = ("frame", N_L, V(0.0, 0.0, -1.0), F_L, Rl @ F_L)
    return aims, ro, rz(yaw), {"round": 0.0}, {}


def make_idle(arm, frames=120):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr, sc, offs = idle_pose(arm, (f % frames) / frames, rest)
        g, go = gun_aims(0)
        aims.update(g)
        offs.update(go)
        aims["rammer"] = ("world", ram_x(RAM_F0, RAM_AX) @ rest.ram)
        aims["round"] = ("world", round_x(SAT, V(0.0, 0.0, -1.0)) @ rest.rd)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    from anim_ugo import key_constant
    key_constant(act, 'pose.bones["round"].scale')
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr, sc, offs = combat_pose(arm, (f % frames) / frames, rest)
        g, go = gun_aims(0)
        aims.update(g)
        offs.update(go)
        aims["rammer"] = ("world", ram_x(RAM_F0, RAM_AX) @ rest.ram)
        aims["round"] = ("world", round_x(SAT, V(0.0, 0.0, -1.0)) @ rest.rd)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    from anim_ugo import key_constant
    key_constant(act, 'pose.bones["round"].scale')
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- the attack: body tracks
def _r(xy, z=0.0):
    return wroot(xy[0], xy[1], ROOT.z + z)


K_RO = [(0, _r(S_XY, -0.015)), (SHOT, _r((0.09, -0.63), -0.04)), (FLINCH, _r((0.0, -0.66), -0.01)), (7, _r((-0.02, -0.68), -0.03)),
        (PLANT, _r((0.04, -0.72), -0.1)), (GRAB, _r(G_XY, -0.14)), (AT_L, _r((0.6, -1.25), -0.1)), (SW_IN, _r((0.62, -1.18), -0.14)),
        (SW_OUT, _r((0.6, -1.25), -0.1)), (UPRIGHT, _r(L_XY, -0.06)), (RD_IN, _r((0.57, -1.24), -0.12)),
        (RAM_AT, _r((0.6, -1.25), -0.1)), (RAM_IN, _r((0.62, -1.18), -0.14)), (RAM_OUT, _r((0.6, -1.25), -0.1)),
        (LEAN, _r((0.35, -0.96), -0.1)), (HEAVE0, _r(H0_XY, -0.07)), (44, _r((0.24, -0.52), -0.1)), (HEAVE1, _r(H1_XY, -0.12)),
        (TAKE, _r((0.05, -0.74), -0.05)), (FR, _r(S_XY, -0.015))]
K_YAW = [(0, S_YAW), (SHOT, S_YAW + 2.0), (FLINCH, S_YAW + 6.0), (7, 95.0), (PLANT, 40.0), (GRAB, G_YAW), (AT_L, L_YAW),
         (RAM_OUT, L_YAW), (LEAN, 125.0), (HEAVE0, H_YAW), (HEAVE1, H_YAW), (TAKE, 30.0), (FR, S_YAW)]
K_BEND = [(0, 0.12), (SHOT, 0.18), (FLINCH, -0.12), (7, 0.0), (PLANT, 0.28), (GRAB, 0.55), (AT_L, 0.38), (SW_IN, 0.46),
          (SW_OUT, 0.38), (UPRIGHT, 0.15), (RD_IN, 0.35), (RAM_AT, 0.38), (RAM_IN, 0.46), (RAM_OUT, 0.38), (LEAN, 0.32),
          (HEAVE0, 0.3), (44, 0.4), (HEAVE1, 0.45), (TAKE, 0.25), (FR, 0.12)]
K_CHEST = [(0, -6.0), (FLINCH, -18.0), (7, -6.0), (PLANT, 8.0), (GRAB, 0.0), (AT_L, 0.0), (RAM_OUT, 0.0), (LEAN, 0.0),
           (HEAVE0, 0.0), (TAKE, 10.0), (FR, -6.0)]
K_LOOK = [(0, S_YAW - 2.0), (SHOT, S_YAW + 6.0), (FLINCH, S_YAW + 50.0), (7, 20.0), (PLANT, 30.0), (GRAB, 150.0),
          (AT_L, 40.0), (RAM_OUT, 40.0), (LEAN, 120.0), (HEAVE0, 80.0), (HEAVE1, 70.0), (TAKE, 50.0), (FR, S_YAW - 2.0)]
K_PITCH = [(0, -0.42), (SHOT, -0.5), (FLINCH, 0.1), (7, 0.05), (PLANT, -0.3), (GRAB, -0.45), (AT_L, -0.3), (RAM_OUT, -0.3),
           (LEAN, -0.35), (HEAVE0, -0.3), (HEAVE1, -0.35), (TAKE, -0.35), (FR, -0.42)]
# feet: (frame, left (x, y), right (x, y))
K_FEET = [(0, (0.24, -0.5), (0.08, -0.78)), (SHOT, (0.24, -0.5), (0.08, -0.78)), (FLINCH, (0.12, -0.5), (0.08, -0.78)),
          (7, (0.12, -0.5), (-0.06, -0.78)), (PLANT, (0.2, -0.66), (-0.02, -0.82)), (GRAB, (0.48, -0.8), (0.28, -1.0)),
          (AT_L, (0.72, -1.04), (0.46, -1.42)), (RAM_OUT, (0.72, -1.04), (0.46, -1.42)), (LEAN, (0.42, -0.84), (0.42, -1.1)),
          (HEAVE0, (0.27, -0.24), (0.24, -0.52)), (44, (0.27, -0.24), (0.22, -0.68)), (HEAVE1, (0.26, -0.55), (0.22, -0.82)),
          (TAKE, (0.18, -0.6), (-0.02, -0.82)), (FR, (0.24, -0.5), (0.08, -0.78))]


def feet_at(f):
    for (fa, la, ra), (fb, lb, rb) in zip(K_FEET, K_FEET[1:]):
        if fa <= f <= fb:
            k = ease((f - fa) / float(fb - fa)) if fb > fa else 1.0
            lf = (lerp(la[0], lb[0], k), lerp(la[1], lb[1], k))
            rf = (lerp(ra[0], rb[0], k), lerp(ra[1], rb[1], k))
            # one foot at a time: the right foot steps in the first half, the left in the second
            kr = min(1.0, k * 2.0)
            kl = max(0.0, k * 2.0 - 1.0)
            lf = (lerp(la[0], lb[0], ease(kl)), lerp(la[1], lb[1], ease(kl)))
            rf = (lerp(ra[0], rb[0], ease(kr)), lerp(ra[1], rb[1], ease(kr)))
            dl = math.hypot(lb[0] - la[0], lb[1] - la[1])
            dr = math.hypot(rb[0] - ra[0], rb[1] - ra[1])
            ll = min(0.08, dl * 0.4) * math.sin(math.pi * kl)
            rl = min(0.08, dr * 0.4) * math.sin(math.pi * kr)
            return lf, rf, ll, rl
    e = K_FEET[-1]
    return e[1], e[2], 0.0, 0.0


# ---------------------------------------------------------------------------------------------- the attack: props
def ls_track(f):
    """The linstock at frame f: ('held', fist, R, g) or ('planted', M, R)."""
    if f <= SHOT:
        F0, R0 = combat_ls()
        hd = (R0 @ LS_T)
        F1, R1 = ls_fist_for_ember(VENT + V(0.0, 0.0, 0.006), hd, V(0.0, 0.0, -1.0), G_COMBAT)
        k = ease(f / float(SHOT))
        return "held", F0.lerp(F1, k), ls_rot(hd, V(0.0, 0.0, -1.0)), G_COMBAT
    _, F_s, R_s, _ = ls_track(SHOT)
    hd_s = R_s @ LS_T
    # the flinch: jerked up and back toward him
    root = V(0.0, -0.66, 0.0)
    F_f = root + fwd(S_YAW + 6.0) * 0.26 + rgt(S_YAW + 6.0) * 0.3 + V(0.0, 0.0, 1.05)
    hd_f = (hd_s + V(0.0, 0.0, 0.85)).normalized()
    # planted: upright at Q_LS
    face_p = fwd(40.0)
    hd_p = V(0.0, 0.0, 1.0)
    F_p = Q_LS + hd_p * G_STAND
    if f <= FLINCH:
        k = ease((f - SHOT) / float(FLINCH - SHOT))
        hd = hd_s.lerp(hd_f, k).normalized()
        return "held", F_s.lerp(F_f, k), ls_rot(hd, V(0.0, 0.0, -1.0)), G_COMBAT + 0.05 * k
    if f < PLANT:
        k = ease((f - FLINCH) / float(PLANT - FLINCH))
        hd = hd_f.lerp(hd_p, k).normalized()
        face = V(0.0, 0.0, -1.0).lerp(face_p, k)
        F = F_f.lerp(F_p, k) + V(0.0, 0.0, 0.12 * math.sin(math.pi * k))
        return "held", F, ls_rot(hd, face), lerp(G_COMBAT + 0.05, G_STAND, k)
    if f < TAKE:
        M, R = ls_planted(Q_LS, hd_p, face_p)
        return "planted", M, R
    # plucked up and held out over the vent again
    F_c, R_c = combat_ls()
    hd_c = R_c @ LS_T
    k = ease((f - TAKE) / float(FR - TAKE))
    hd = hd_p.lerp(hd_c, k).normalized()
    face = face_p.lerp(V(0.0, 0.0, -1.0), k)
    F = F_p.lerp(F_c, k) + V(0.0, 0.0, 0.1 * math.sin(math.pi * k))
    return "held", F, ls_rot(hd, face), lerp(G_STAND, G_COMBAT, k)


ENTRY_TILT = math.radians(20.0)
SW_DEPTH, RAM_DEPTH = 0.18, 0.26                # how far the sponge and the rammer go in
S_R_SW, S_L_SW = 0.16, 0.34                    # where his fists hold the staff to swab (from the rammer's face)...
S_R_RAM, S_L_RAM = 0.52, 0.4                   # ...and to ram (the staff turned about)


def bore_placement(f, depth, which, tilt=0.0, spin=0.0):
    """The rammer in the bore at frame f: 'sponge' (the sponge's end `depth` inside the mouth) or 'ram' (the rammer's face
    `depth` inside); tilted up by `tilt` about the mouth (entering and leaving)."""
    m, d = muzzle_at(f)
    side = d.cross(V(0.0, 0.0, 1.0)).normalized()
    up = side.cross(d).normalized()
    out = (d * math.cos(tilt) + up * math.sin(tilt)).normalized()      # from the mouth out along the staff
    tip = m - d * depth
    if which == "sponge":
        ax = -out                                                        # rammer face -> sponge: into the bore
        foot = tip - ax * RAM_LEN
    else:
        ax = out
        foot = tip
    sd = Quaternion(ax, spin) @ perp(V(1.0, 0.0, 0.0), ax)
    return ram_x(foot, ax, sd)


RAM_MID = RAM_F0 + RAM_AX * (RAM_LEN * 0.5)


def lerp_x(A, B, k, pivot=None):
    """Blend two rigid placements: the pivot (a rest point, the staff's middle by default) moves straight from one to the
    other while the turn slerps about it."""
    pv = RAM_MID if pivot is None else pivot
    R = A.to_quaternion().slerp(B.to_quaternion(), k).to_matrix()
    c = (A @ pv).lerp(B @ pv, k)
    M = R.to_4x4()
    M.translation = c - R @ pv
    return M


def ram_track(f):
    """The rammer at frame f: ('carriage',) or ('hands', X, s_r, s_l) (where his fists hold it along the staff)."""
    if f <= GRAB or f >= LEAN:
        return ("carriage",)
    X_g = carr(GRAB) @ ram_x(RAM_F0, RAM_AX)
    if f <= AT_L:
        k = ease((f - GRAB) / float(AT_L - GRAB))
        # lifted from the wheel and swung over to the muzzle, the sponge end coming down into its mouth
        X_e = bore_placement(AT_L, -0.02, "sponge", ENTRY_TILT)
        X = lerp_x(X_g, X_e, k)
        X.translation += V(0.0, 0.0, 0.12 * math.sin(math.pi * k))
        return ("hands", X, lerp(0.3, S_R_SW, k), lerp(0.5, S_L_SW, k))
    if f <= SW_IN:
        k = ease((f - AT_L) / float(SW_IN - AT_L))
        return ("hands", bore_placement(f, lerp(-0.02, SW_DEPTH, k), "sponge", ENTRY_TILT * (1.0 - min(1.0, k * 1.6))), S_R_SW, S_L_SW)
    if f <= SW_TW:
        k = ease((f - SW_IN) / float(SW_TW - SW_IN))
        return ("hands", bore_placement(f, SW_DEPTH, "sponge", 0.0, spin=1.6 * k), S_R_SW, S_L_SW)
    if f <= SW_OUT:
        k = ease((f - SW_TW) / float(SW_OUT - SW_TW))
        return ("hands", bore_placement(f, lerp(SW_DEPTH, 0.0, k), "sponge", ENTRY_TILT * max(0.0, k * 1.6 - 0.6), spin=1.6), S_R_SW, S_L_SW)
    # upright in his right fist (the sponge up) while his left hand loads the round
    up_foot = V(L_XY[0], L_XY[1], 0.36) + fwd(L_YAW) * 0.25 + rgt(L_YAW) * 0.26
    X_up = ram_x(up_foot, V(0.05, -0.08, 1.0))
    if f <= UPRIGHT:
        k = ease((f - SW_OUT) / float(UPRIGHT - SW_OUT))
        return ("hands", lerp_x(bore_placement(SW_OUT, 0.0, "sponge", ENTRY_TILT * 0.6, spin=1.6), X_up, k), lerp(S_R_SW, 0.3, k), S_L_SW)
    if f <= RD_IN:
        return ("hands", X_up, 0.3, None)
    if f <= RAM_AT:
        # turned about: the rammer's face swings up to the mouth
        k = ease((f - RD_IN) / float(RAM_AT - RD_IN))
        X_e = bore_placement(RAM_AT, -0.02, "ram", ENTRY_TILT * 1.4)
        return ("hands", lerp_x(X_up, X_e, k), lerp(0.3, S_R_RAM, k), lerp(0.45, S_L_RAM, k))
    if f <= RAM_IN:
        k = ease((f - RAM_AT) / float(RAM_IN - RAM_AT))
        return ("hands", bore_placement(f, lerp(-0.02, RAM_DEPTH, k), "ram", ENTRY_TILT * 1.4 * (1.0 - min(1.0, k * 1.5))), S_R_RAM, S_L_RAM)
    if f <= RAM_OUT:
        k = ease((f - RAM_IN) / float(RAM_OUT - RAM_IN))
        return ("hands", bore_placement(f, lerp(RAM_DEPTH, 0.02, k), "ram", ENTRY_TILT * max(0.0, k * 1.6 - 0.6)), S_R_RAM, S_L_RAM)
    # back to the wheel
    k = ease((f - RAM_OUT) / float(LEAN - RAM_OUT))
    X_o = bore_placement(RAM_OUT, 0.02, "ram", ENTRY_TILT)
    X_l = carr(LEAN) @ ram_x(RAM_F0, RAM_AX)
    X_mid = ram_x(V(0.4, -1.2, 0.5), V(0.4, 0.5, 0.75).normalized())
    X = lerp_x(X_o, X_mid, ease(min(1.0, k * 2.0))) if k < 0.5 else lerp_x(X_mid, X_l, ease((k - 0.5) * 2.0))
    return ("hands", X, lerp(S_R_RAM, 0.32, k), lerp(S_L_RAM, 0.55, k))


def round_track(f):
    """The round: ('bag',) hidden; ('hand', C, A) in his left hand; ('bore', depth) in the muzzle."""
    if f < BAG or f >= RAM_IN:
        return ("bag",)
    m, d = muzzle_at(f)
    if f < RD_IN:
        k = ease((f - BAG) / float(RD_IN - BAG))
        C0 = SAT + V(0.0, 0.0, 0.02)
        C1 = m - d * (cm.ROUND_R + 0.012)
        C = C0.lerp(C1, k) + V(0.0, 0.0, 0.18 * math.sin(math.pi * k))
        A = V(0.0, 0.0, -1.0).lerp(-d, k).normalized()
        return ("hand", C, A)
    if f < RAM_AT:
        return ("bore", cm.ROUND_R + 0.012)
    k = ease((f - RAM_AT) / float(RAM_IN - RAM_AT))
    return ("bore", cm.ROUND_R + 0.012 + lerp(0.0, RAM_DEPTH, k))


# ---------------------------------------------------------------------------------------------- the attack: pose
def attack_pose(arm, f, rest):
    ro = smooth_keys(K_RO, f)
    yaw = smooth_keys(K_YAW, f)
    bend = smooth_keys(K_BEND, f)
    lf, rf, ll, rl = feet_at(f)
    aims = feet(arm, lf, rf, yaw, lift_l=ll, lift_r=rl)
    torso(aims, yaw, bend=bend, side=0.0, chest=smooth_keys(K_CHEST, f), look=smooth_keys(K_LOOK, f), pitch=smooth_keys(K_PITCH, f))
    q = rz(yaw)
    sc, offs = {}, {}
    # ---- the gun
    g, go = gun_aims(f)
    aims.update(g)
    offs.update(go)
    # ---- the linstock (and his right hand while it holds it)
    st = ls_track(f)
    right_busy = False
    if st[0] == "held":
        _, F, R, gg = st
        aims.update(grip_r(arm, F, R, pole=q @ V(-1.0, 0.35, -0.5)))
        aims["linstock"] = held_ls(rest, gg)
        right_busy = True
    else:
        aims["linstock"] = ("world", st[1] @ rest.ls)
    # ---- the rammer
    rt = ram_track(f)
    if rt[0] == "carriage":
        aims["rammer"] = ("world", carr(f) @ ram_x(RAM_F0, RAM_AX) @ rest.ram)
    else:
        _, X, s_r, s_l = rt
        aims["rammer"] = ("world", X @ rest.ram)
        ax = ram_axis(X)
        if not right_busy:
            Rr = staff_hand_rot("R", ax, -q @ V(0.0, 0.0, 1.0) + fwd(yaw) * 0.3)
            aims.update(grip_r(arm, ram_pt(X, s_r), Rr, pole=q @ V(-1.0, -0.2, -0.6)))
            right_busy = True
        if s_l is not None:
            Rl = staff_hand_rot("L", ax, -q @ V(0.0, 0.0, 1.0) + fwd(yaw) * 0.3)
            aims.update(grip_l(arm, ram_pt(X, s_l), Rl, pole=q @ V(0.35, 0.25, -1.0)))
    # ---- the round (and his left hand while it holds it)
    rd = round_track(f)
    if rd[0] == "hand":
        _, C, A = rd
        wrist, Rl = round_hand(C, A, fwd(yaw))
        aims.update(arm_aims(arm, "L", wrist, pole=q @ V(1.0, 0.3, -0.5)))
        aims["hand.L"] = ("frame", N_L, A.normalized(), F_L, Rl @ F_L)
        aims["round"] = (lambda P, base: ("world", P["hand.L"] @ rest.hand_l_inv @ rest.rd))
        sc["round"] = 1.0
    elif rd[0] == "bore":
        m, d = muzzle_at(f)
        aims["round"] = ("world", round_x(m - d * rd[1], -d) @ rest.rd)
        sc["round"] = 1.0 if rd[1] < 0.3 else 0.0
    else:
        aims["round"] = ("world", round_x(SAT, V(0.0, 0.0, -1.0)) @ rest.rd)
        sc["round"] = 0.0
    # ---- the hands' other jobs: hauling the wheel round, else on his hips
    left_busy = rd[0] == "hand" or (rt[0] == "hands" and rt[3] is not None)
    if HEAVE0 - 2 <= f <= HEAVE1 and not right_busy and not left_busy:
        roll = (REC - recoil(f)) / cm.WR
        hub = carr(f) @ vec(cm.hub_c(-1))
        for side, dphi in (("L", 0.0), ("R", 0.36)):
            a = math.radians(104.0) + dphi + roll
            rad = V(0.0, math.cos(a), math.sin(a))
            tan = V(0.0, -math.sin(a), math.cos(a))
            p = hub + rad * (cm.WR - 0.012) + V(-0.045, 0.0, 0.0)
            face = (V(1.0, 0.0, 0.0) * 0.55 - rad * 0.85).normalized()
            if side == "L":
                aims.update(grip_l(arm, p, frame_map(T_L, tan, F_L, perp(face, tan)), pole=q @ V(1.0, 0.3, -0.6)))
            else:
                aims.update(grip_r(arm, p, frame_map(T_R, tan, F_R, perp(face, tan)), pole=q @ V(-1.0, 0.3, -0.6)))
        right_busy = left_busy = True
    if not right_busy:
        hip = body_pt(V(-0.27, -0.04, 0.95), ro, yaw)
        aims.update(arm_aims(arm, "R", hip, pole=q @ V(-1.0, 0.5, 0.1), hand_dir=q @ V(0.35, 0.25, -1.0)))
    if not left_busy:
        lhip = body_pt(V(0.27, -0.04, 0.95), ro, yaw)
        aims.update(arm_aims(arm, "L", lhip, pole=q @ V(1.0, 0.5, 0.1), hand_dir=q @ V(-0.35, 0.25, -1.0)))
    return aims, ro, rz(yaw), sc, offs


def make_attack(arm, frames=FR):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, rr, sc, offs = attack_pose(arm, f, rest)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    from anim_ugo import key_constant
    key_constant(act, 'pose.bones["round"].scale')
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
