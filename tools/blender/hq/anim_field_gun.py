"""Field Gun clips (game: 24 fps).

Idle   : the gun loaded and laid; he stands at ease by the breech, fists on his hips, breathing and looking about; once he
         lifts his field glasses to his eyes with both hands, scans the field slowly and lets them drop back on his chest.
Combat : laying the gun: crouched beside the breech, his left hand on the elevating handwheel's knob turning it slowly to
         and fro (the barrel rises and dips with it), the lanyard's toggle in his right fist at his hip, the cord taut.
Attack : (52 frames, inside the 2.2 s cooldown) he yanks the lanyard and the gun fires (SHOT, frame 2: the game's flash,
         smoke and shell leave the muzzle there): the barrel slams back along its cylinder and runs out again, the gun
         rocking on its spade; he lets the toggle drop, swings the breech lever up and back with his left hand, the block
         slides open and the spent case flies out over the trail; he turns to the ammunition box, lifts a round out with
         both hands, carries it to the breech and pushes it home, swings the lever shut, picks up the toggle and is back
         laying the gun.

The gun's bones are posed directly: carriage (rocking about the spade), cradle (elevating about the trunnions), barrel
(sliding back along the cradle), block (sliding out to the gun's left), lever (on the barrel), handwheel (turning with the
elevation). The lanyard is stretched from its eye on the firing gear to the toggle; the toggle, the round, the spent
case and his field glasses are free bones posed in the world (their scales hide the round once it is home and the case
outside the ejection)."""
import math
from mathutils import Vector, Quaternion, Matrix
import field_gun as fg
from rig import Poser, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease
from anim_cannon import rz, fwd, rgt, body_pt, wroot, smooth_keys, xform, perp, feet, torso, grip_r, grip_l

FPS = 24
J = fg.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
X_, Z_ = V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0)

_wrR, _fR, _nR, _tR = fg.hand_frame("R")
WR_R, T_R, F_R, N_R = vec(_wrR), vec(_tR), vec(_fR), vec(_nR)
FIST_R = vec(fg.fist_center("R"))
PALM_R = vec(fg.palm_pt("R"))
_wrL, _fL, _nL, _tL = fg.hand_frame("L")
WR_L, T_L, F_L, N_L = vec(_wrL), vec(_tL), vec(_fL), vec(_nL)
FIST_L = vec(fg.fist_center("L"))
PALM_L = vec(fg.palm_pt("L"))

GD, GU = vec(fg.GD), vec(fg.GU)
TRUN = vec(fg.TRUN)
KP = vec(fg.KICK_P)
LEV_P = vec(fg.LEV_P)
LEV_TIP = vec(fg.LEV_P + fg.GD * fg.LEV_L + fg.GX_ * -0.01)
HW_C = vec(fg.HW_C)
KNOB0 = vec(fg.knob_pt(0.0) - fg.GX_ * fg.KNOB_OUT)          # (rest) the middle of the handwheel knob's grip
CORD_A = vec(fg.CORD_A)
TOG0 = vec(fg.TOG0)
SH_BASE0, SH_A0 = vec(fg.SH_BASE0), vec(fg.SH_A0)
CASE_B0 = vec(fg.bore_pt(fg.S_CASE))
_G, _X, _U, _N = fg.glasses_frame()
GL_G, GL_X, GL_U, GL_N = vec(_G), vec(_X), vec(_U), vec(_N)

# ---------------------------------------------------------------------------------------------- timing (24 fps)
SHOT = 2           # the lanyard yanked: the gun fires (game: flash, smoke and the shell at the muzzle)
REC_MAX = 5        # fully recoiled
RUN_OUT = 12       # run out again
LET_GO = 6         # he drops the toggle
ON_LEVER = 10      # his left hand on the lever's knob
OPEN0, OPEN1 = 10, 14       # the lever swung up and back, the block sliding open
EJECT = 13         # the spent case leaves the breech
REACH0 = 14        # his hands go for the round in the box ...
GRAB = 19          # ... and hold it by its ends
LIFT = 22          # lifted out
SWING = 26         # (turning back to the gun with it)
AT_BREECH = 29     # its nose in the breech's mouth; his right hand lets go of the nose
HOME = 34          # his left palm pushes its base to the breech's face; it slides home (hidden from HOME + 1)
CLOSE0, CLOSE1 = 36, 39     # the lever swung shut (left hand)
TAKE = 44          # the toggle back in his right fist
KNOB = 47          # his left hand back on the handwheel
FR = 52            # = the 2.2 s cooldown (52.8 frames)

REC = 0.28         # the recoil (m)
KICK = 2.2         # the gun rocking up about its spade (degrees)
LEV_OPEN = 128.0   # the lever's swing (degrees)
EL_COMBAT = 0.45   # Combat: the barrel's elevation swings +-this (degrees) ...
TURN_PER_DEG = 2 * math.pi / 1.2    # ... and the handwheel turns once for 1.2 degrees


# ---------------------------------------------------------------------------------------------- the gun
def recoil(f):
    if f <= SHOT:
        return 0.0
    if f <= REC_MAX:
        k = (f - SHOT) / float(REC_MAX - SHOT)
        return REC * (1.0 - (1.0 - k) ** 3)
    if f <= RUN_OUT:
        return REC * (1.0 - ease((f - REC_MAX) / float(RUN_OUT - REC_MAX)))
    return 0.0


def kick(f):
    if f <= SHOT:
        return 0.0
    t = f - SHOT
    if t <= 1.5:
        return KICK * t / 1.5
    if t <= 5:
        return KICK * (1.0 - ease((t - 1.5) / 3.5))
    if t <= 7:
        return -0.35 * math.sin(math.pi * (t - 5) / 2.0)
    return 0.0


def carr(f):
    """The carriage's rigid motion at frame f (rest -> posed): rocking up about the spade, shoved back a little."""
    sh = 0.018 * math.sin(math.pi * min(1.0, max(0.0, (f - SHOT) / 6.0))) if f > SHOT else 0.0
    return (Matrix.Translation(KP + V(0.0, sh, 0.0)) @ Matrix.Rotation(-math.radians(kick(f)), 4, "X")
            @ Matrix.Translation(-KP))


def m_cradle(f, el):
    return carr(f) @ Matrix.Translation(TRUN) @ Matrix.Rotation(-math.radians(el), 4, "X") @ Matrix.Translation(-TRUN)


def m_barrel(f, el, rec):
    return m_cradle(f, el) @ Matrix.Translation(-GD * rec)


def m_lever(Mb, ang):
    return Mb @ Matrix.Translation(LEV_P) @ Matrix.Rotation(-math.radians(ang), 4, "X") @ Matrix.Translation(-LEV_P)


def m_wheel(f, phi):
    return carr(f) @ Matrix.Translation(HW_C) @ Matrix.Rotation(phi, 4, "X") @ Matrix.Translation(-HW_C)


class Rest:
    """Rest matrices of the bones the props ride on (from the armature)."""
    def __init__(self, arm):
        b = arm.data.bones
        self.m = {n: b[n].matrix_local.copy() for n in ("barrel", "block", "lever", "handwheel", "lanyard", "toggle",
                                                        "shell", "case", "glasses", "chest", "hand.R", "hand.L")}
        self.inv = {n: m.inverted() for n, m in self.m.items()}


def gun_aims(f, rest, el=0.0, rec=0.0, slide=0.0, lev=0.0, phi=0.0):
    """The gun's bones at frame f: elevation el (deg), recoil rec (m), the block's slide (m), the lever's swing (deg), the
    handwheel's turn (rad). Returns aims, offsets and the barrel's matrix."""
    Mb = m_barrel(f, el, rec)
    aims = {"carriage": ("rot", Quaternion((1, 0, 0), -math.radians(kick(f)))),
            "cradle": ("rot", Quaternion((1, 0, 0), -math.radians(el))),
            "barrel": ("world", Mb @ rest.m["barrel"]),
            "block": ("world", Mb @ Matrix.Translation(X_ * slide) @ rest.m["block"]),
            "lever": ("world", m_lever(Mb, lev) @ rest.m["lever"]),
            "handwheel": ("world", m_wheel(f, phi) @ rest.m["handwheel"])}
    off = {"carriage": V(0.0, (carr(f) @ KP - KP).y, 0.0)}
    return aims, off, Mb


def knob_at(f, phi):
    return m_wheel(f, phi) @ KNOB0


def lever_tip(Mb, ang):
    return m_lever(Mb, ang) @ LEV_TIP


# ---------------------------------------------------------------------------------------------- lanyard and toggle
X_TOG = xform(TOG0, X_, Z_, FIST_R, T_R, F_R)        # (rest) the toggle placed in his right fist: the bar along the thumb axis


def toggle_in_hand(rest):
    def fn(P, base):
        return ("world", P["hand.R"] @ rest.inv["hand.R"] @ X_TOG @ rest.m["toggle"])
    return fn


def lanyard_aim(rest, A, held=None, T=None):
    """The cord from its eye A to the toggle (held in his fist, or at the world point T)."""
    def fn(P, base):
        end = (P["hand.R"] @ rest.inv["hand.R"] @ X_TOG) @ TOG0 if held else T
        d = end - A
        R = (TOG0 - CORD_A).normalized().rotation_difference(d.normalized()).to_matrix().to_4x4()
        M = Matrix.Translation(A) @ R @ Matrix.Translation(-CORD_A) @ rest.m["lanyard"]
        return ("world", M)
    return fn


def lanyard_len(rest, P, A, held, T):
    end = (P["hand.R"] @ rest.inv["hand.R"] @ X_TOG) @ TOG0 if held else T
    return (end - A).length / fg.LAN_L


def cord_eye(f):
    return carr(f) @ CORD_A


def hanging_toggle(f):
    A = cord_eye(f)
    return A, A - Z_ * fg.LAN_L


# ---------------------------------------------------------------------------------------------- hands
def fist_rot(side, axis, knuck):
    """A fist round a bar along `axis` (the thumb's way), its knuckles toward `knuck`."""
    axis = axis.normalized()
    if side == "R":
        return frame_map(T_R, axis, F_R, perp(knuck, axis))
    return frame_map(T_L, axis, F_L, perp(knuck, axis))


def palm_rot(side, palm, fingers):
    """An open hand: its palm facing `palm`, its fingers toward `fingers`."""
    palm = palm.normalized()
    if side == "R":
        return frame_map(N_R, palm, F_R, perp(fingers, palm))
    return frame_map(N_L, palm, F_L, perp(fingers, palm))


def palm_at(arm, side, contact, R, pole):
    """Aims putting the palm's grip point on `contact`, the hand turned by R."""
    if side == "R":
        aims = arm_aims(arm, "R", contact - R @ (PALM_R - WR_R), pole=pole)
        aims["hand.R"] = ("frame", T_R, R @ T_R, F_R, R @ F_R)
    else:
        aims = arm_aims(arm, "L", contact - R @ (PALM_L - WR_L), pole=pole)
        aims["hand.L"] = ("frame", T_L, R @ T_L, F_L, R @ F_L)
    return aims


def hip_fist(side, ro, yaw):
    """A fist resting on his hip: (where, turn)."""
    q = rz(yaw)
    s = -1.0 if side == "R" else 1.0
    return body_pt(V(s * 0.35, -0.02, 0.9), ro, yaw), fist_rot(side, q @ V(0.0, -1.0, 0.0), q @ V(-s * 0.35, 0.25, -1.0))


def hip_aims(arm, side, ro, yaw):
    p, R = hip_fist(side, ro, yaw)
    q = rz(yaw)
    if side == "R":
        return grip_r(arm, p, R, pole=q @ V(-1.0, 0.5, 0.1))
    return grip_l(arm, p, R, pole=q @ V(1.0, 0.5, 0.1))


def body_matrix(ro, yaw):
    """His body's rigid motion (rest -> posed) for the root offset ro and the turn yaw."""
    return Matrix.Translation(ROOT + ro) @ rz(yaw).to_matrix().to_4x4() @ Matrix.Translation(-ROOT)


def blend_m(A, B, k, pivot):
    R = A.to_quaternion().slerp(B.to_quaternion(), k).to_matrix()
    c = (A @ pivot).lerp(B @ pivot, k)
    M = R.to_4x4()
    M.translation = c - R @ pivot
    return M


# ---------------------------------------------------------------------------------------------- stations
S_XY, S_YAW = (0.27, -0.1), 22.0              # Combat: crouched beside the breech, turned a little toward the gun
I_XY, I_YAW = (0.24, 0.0), 12.0               # Idle: standing at ease by the breech
B_XY, B_YAW = (0.32, -0.04), 8.0              # at the breech lever
C_XY, C_YAW = (0.3, -0.02), -84.0             # at the box (facing -X)
L0_XY, L1_XY, L_YAW = (0.38, 0.02), (0.35, -0.12), 90.0   # loading: side-on to the breech, facing the gun
T_XY, T_YAW = (0.36, -0.08), 60.0             # picking up the toggle


def stance(xy, yaw, spread=1.0, lfwd=0.06, rfwd=-0.04):
    """His feet's places (ankles, x y) for standing at xy facing yaw."""
    q = rz(yaw)
    c = V(xy[0], xy[1], 0.0)
    lf = c + q @ V(0.2 * spread, -lfwd, 0.0)
    rf = c + q @ V(-0.2 * spread, -rfwd, 0.0)
    return (lf.x, lf.y), (rf.x, rf.y)


S_STANCE = (1.15, 0.16, -0.08)


def combat_body(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    yaw = S_YAW + 1.5 * math.sin(w)
    ro = wroot(S_XY[0], S_XY[1], ROOT.z - 0.13 + 0.004 * br)
    lf, rf = stance(S_XY, S_YAW, *S_STANCE)
    aims = feet(arm, lf, rf, S_YAW)
    torso(aims, yaw, bend=0.3, side=0.06, chest=8.0, look=S_YAW - 18.0, pitch=0.12, br=br)
    return aims, ro, yaw, br


def combat_el(t):
    return EL_COMBAT * math.sin(2 * math.pi * t)


def hold_toggle(ro, yaw, br=0.0, pull=0.0):
    """His right fist holding the toggle at his right hip, the bar upright, the knuckles toward the gun (pull: yanked back
    and out)."""
    q = rz(yaw)
    F0 = body_pt(V(-0.34, -0.12 + 0.2 * pull, 0.9 + 0.004 * br + 0.05 * pull), ro, yaw) + q @ V(-0.08 * pull, 0.0, 0.0)
    knuck = (CORD_A - F0)
    knuck.z = 0.0
    return F0, fist_rot("R", Z_, knuck)


def knob_rot():
    return fist_rot("L", V(-1.0, 0.0, 0.0), V(0.0, -1.0, -0.6))


def knob_hold(arm, f, phi, yaw):
    return grip_l(arm, knob_at(f, phi), knob_rot(), pole=rz(yaw) @ V(1.0, 0.4, -0.3))


def combat_pose(arm, t, rest, f_gun=0):
    aims, ro, yaw, br = combat_body(arm, t)
    el = combat_el(t)
    phi = el * TURN_PER_DEG
    g, off, Mb = gun_aims(f_gun, rest, el=el, phi=phi)
    aims.update(g)
    aims.update(knob_hold(arm, f_gun, phi, yaw))
    F0, R = hold_toggle(ro, yaw, br)
    aims.update(grip_r(arm, F0, R, pole=rz(yaw) @ V(-1.0, 0.4, -0.4)))
    aims["toggle"] = toggle_in_hand(rest)
    A = cord_eye(f_gun)
    aims["lanyard"] = lanyard_aim(rest, A, held=True)
    return aims, ro, yaw, {"shell": 1.0, "case": 0.0}, off, ("held", A, None)


def idle_body(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    look_t = min(1.0, max(0.0, (t - 0.3) / 0.12)) * (1.0 - min(1.0, max(0.0, (t - 0.72) / 0.12)))
    glass = ease(look_t)
    yaw = I_YAW + 3.0 * math.sin(w) + glass * 10.0 * math.sin(2 * math.pi * (t - 0.42) / 0.3)
    ro = wroot(I_XY[0], I_XY[1], ROOT.z - 0.01 + 0.005 * br)
    lf, rf = stance(I_XY, I_YAW, 1.05, 0.0, 0.0)
    aims = feet(arm, lf, rf, I_YAW)
    look = yaw - 6.0 + (1.0 - glass) * (24.0 * math.sin(w) + 8.0 * math.sin(w * 3))
    torso(aims, yaw, bend=0.02 - 0.06 * glass, side=0.02 * math.sin(w), chest=2.0 * math.sin(w), look=look,
          pitch=0.04 + 0.03 * br + 0.06 * glass, br=br)
    return aims, ro, yaw, br, glass


def glasses_at_eyes(ro, yaw, look):
    """The field glasses held up to his eyes (rest -> posed)."""
    hd = body_pt(fg.hp((0.0, -0.31, 1.672)), ro, yaw)
    q = rz(look)
    f = q @ V(0.0, -1.0, 0.0)
    left = q @ V(1.0, 0.0, 0.0)
    R = frame_map(GL_U, -f, GL_X, left)
    M = R.to_4x4()
    M.translation = hd + f * 0.03 - R @ GL_G
    return M


def idle_pose(arm, t, rest):
    aims, ro, yaw, br, glass = idle_body(arm, t)
    g, off, Mb = gun_aims(0, rest)
    aims.update(g)
    q = rz(yaw)
    if glass > 0.0:
        Me = glasses_at_eyes(ro, yaw, yaw - 6.0)
        Mc = body_matrix(ro, yaw)                          # (riding his chest, near enough)
        Mg = Matrix.Translation(Z_ * 0.05 * math.sin(math.pi * glass)) @ blend_m(Mc, Me, glass, GL_G)
        aims["glasses"] = ("world", Mg @ rest.m["glasses"])
        k = min(1.0, glass * 1.4)
        for side, s_ in (("R", -1), ("L", 1)):
            hp_, Rh = hip_fist(side, ro, yaw)
            gp = Mg @ (GL_G + GL_X * (s_ * (fg.GL_SEP + 0.012)) - GL_U * 0.012 - GL_N * 0.01)
            Rg = fist_rot(side, Mg.to_3x3() @ GL_U, Mg.to_3x3() @ (GL_N - GL_X * (s_ * 0.6)))
            R = Rh.to_quaternion().slerp(Rg.to_quaternion(), k).to_matrix()
            p = hp_.lerp(gp, k)
            if side == "R":
                aims.update(grip_r(arm, p, R, pole=q @ V(-1.0, 0.3, -0.6)))
            else:
                aims.update(grip_l(arm, p, R, pole=q @ V(1.0, 0.3, -0.6)))
    else:
        aims["glasses"] = lambda P, base: ("world", P["chest"] @ rest.inv["chest"] @ rest.m["glasses"])
        aims.update(hip_aims(arm, "R", ro, yaw))
        aims.update(hip_aims(arm, "L", ro, yaw))
    A, T = hanging_toggle(0)
    aims["toggle"] = ("world", Matrix.Translation(T - TOG0) @ rest.m["toggle"])
    aims["lanyard"] = lanyard_aim(rest, A, T=T)
    return aims, ro, yaw, {"shell": 1.0, "case": 0.0}, off, ("hang", A, T)


def _finish(P, aims, ro, yaw, sc, off, lan, rest, f):
    """Solve and key one frame (the lanyard's stretch needs the hand's pose: a second solve)."""
    sc = dict(sc)
    ch, Pm = P.solve(aims, ro, rz(yaw), scales=sc, offsets=off)
    kind, A, T = lan
    sc["lanyard"] = (1.0, lanyard_len(rest, Pm, A, kind == "held", T), 1.0)
    ch, Pm = P.solve(aims, ro, rz(yaw), scales=sc, offsets=off)
    P.key(ch, f)
    return Pm


def _rest_aims(rest, aims):
    aims.setdefault("shell", ("world", rest.m["shell"]))
    aims.setdefault("case", ("world", rest.m["case"]))
    aims.setdefault("glasses", lambda P, base: ("world", P["chest"] @ rest.inv["chest"] @ rest.m["glasses"]))


def _const(act):
    from anim_ugo import key_constant
    key_constant(act, 'pose.bones["shell"].scale')
    key_constant(act, 'pose.bones["case"].scale')


def make_idle(arm, frames=120):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, yaw, sc, off, lan = idle_pose(arm, (f % frames) / frames, rest)
        _rest_aims(rest, aims)
        _finish(P, aims, ro, yaw, sc, off, lan, rest, f)
    _const(act)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=48):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, yaw, sc, off, lan = combat_pose(arm, (f % frames) / frames, rest)
        _rest_aims(rest, aims)
        _finish(P, aims, ro, yaw, sc, off, lan, rest, f)
    _const(act)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- the attack: body tracks
def _r(xy, z=0.0):
    return wroot(xy[0], xy[1], ROOT.z + z)


K_RO = [(0, _r(S_XY, -0.13)), (SHOT, _r((0.26, -0.08), -0.12)), (4, _r((0.25, -0.05), -0.08)), (LET_GO, _r((0.28, -0.04), -0.07)),
        (ON_LEVER, _r(B_XY, -0.09)), (OPEN1, _r(B_XY, -0.06)), (GRAB, _r(C_XY, -0.24)), (LIFT, _r(C_XY, -0.1)),
        (SWING, _r((0.33, 0.0), -0.06)), (AT_BREECH, _r(L0_XY, -0.1)), (HOME, _r(L1_XY, -0.12)), (CLOSE1, _r((0.35, -0.14), -0.12)),
        (TAKE, _r(T_XY, -0.2)), (FR, _r(S_XY, -0.13))]
K_YAW = [(0, S_YAW), (SHOT, S_YAW - 2.0), (4, S_YAW + 2.0), (LET_GO, 14.0), (ON_LEVER, B_YAW), (OPEN1, 0.0), (GRAB, C_YAW),
         (LIFT, C_YAW + 4.0), (SWING, 20.0), (AT_BREECH, L_YAW), (HOME, L_YAW + 2.0), (CLOSE1, 70.0), (TAKE, T_YAW), (FR, S_YAW)]
K_BEND = [(0, 0.3), (SHOT, 0.22), (4, 0.06), (LET_GO, 0.12), (ON_LEVER, 0.32), (OPEN1, 0.2), (GRAB, 0.62), (LIFT, 0.22),
          (SWING, 0.15), (AT_BREECH, 0.38), (HOME, 0.45), (CLOSE1, 0.36), (TAKE, 0.5), (FR, 0.3)]
K_CHEST = [(0, 8.0), (SHOT, 4.0), (LET_GO, 4.0), (ON_LEVER, 12.0), (OPEN1, 4.0), (GRAB, 0.0), (LIFT, 0.0), (AT_BREECH, 0.0),
           (HOME, 6.0), (CLOSE1, 4.0), (TAKE, -4.0), (FR, 8.0)]
K_LOOK = [(0, S_YAW - 18.0), (SHOT, S_YAW - 22.0), (4, S_YAW - 8.0), (LET_GO, 20.0), (ON_LEVER, 30.0), (OPEN1, 30.0),
          (GRAB, C_YAW + 4.0), (LIFT, C_YAW + 12.0), (SWING, 50.0), (AT_BREECH, L_YAW + 8.0), (HOME, L_YAW + 10.0),
          (CLOSE1, L_YAW - 10.0), (TAKE, T_YAW + 6.0), (FR, S_YAW - 18.0)]
K_PITCH = [(0, 0.12), (SHOT, 0.2), (4, 0.25), (LET_GO, 0.0), (ON_LEVER, -0.35), (OPEN1, -0.3), (GRAB, -0.4), (LIFT, -0.2),
           (SWING, -0.1), (AT_BREECH, -0.35), (HOME, -0.35), (CLOSE1, -0.35), (TAKE, -0.45), (FR, 0.12)]
_sS = stance(S_XY, S_YAW, *S_STANCE)
_sB = stance(B_XY, B_YAW, 1.05, 0.1, -0.02)
_sC = stance(C_XY, C_YAW, 1.25, 0.1, -0.08)
_sW = stance((0.33, 0.0), 10.0, 1.05, 0.0, 0.0)
_sL0 = stance(L0_XY, L_YAW, 1.1, 0.06, -0.04)
_sL1 = stance(L1_XY, L_YAW, 1.15, 0.12, -0.08)
_sT = stance(T_XY, T_YAW, 1.15, 0.14, -0.06)
K_FEET = [(0, _sS[0], _sS[1]), (LET_GO, _sS[0], _sS[1]), (ON_LEVER, _sB[0], _sB[1]), (OPEN1, _sB[0], _sB[1]),
          (GRAB, _sC[0], _sC[1]), (LIFT, _sC[0], _sC[1]), (SWING, _sW[0], _sW[1]), (AT_BREECH, _sL0[0], _sL0[1]),
          (HOME, _sL1[0], _sL1[1]), (CLOSE1, _sL1[0], _sL1[1]), (TAKE, _sT[0], _sT[1]), (FR, _sS[0], _sS[1])]
K_FYAW = [(0, S_YAW), (LET_GO, S_YAW), (ON_LEVER, B_YAW), (OPEN1, B_YAW), (GRAB, C_YAW), (LIFT, C_YAW), (SWING, 10.0),
          (AT_BREECH, L_YAW), (CLOSE1, L_YAW), (TAKE, T_YAW), (FR, S_YAW)]


def feet_at(f):
    for (fa, la, ra), (fb, lb, rb) in zip(K_FEET, K_FEET[1:]):
        if fa <= f <= fb:
            k = (f - fa) / float(fb - fa) if fb > fa else 1.0
            kr = ease(min(1.0, k * 2.0))                     # one foot at a time: the right steps first, then the left
            kl = ease(max(0.0, k * 2.0 - 1.0))
            lf = (lerp(la[0], lb[0], kl), lerp(la[1], lb[1], kl))
            rf = (lerp(ra[0], rb[0], kr), lerp(ra[1], rb[1], kr))
            dl = math.hypot(lb[0] - la[0], lb[1] - la[1])
            dr = math.hypot(rb[0] - ra[0], rb[1] - ra[1])
            ll = min(0.08, dl * 0.45) * math.sin(math.pi * kl)
            rl = min(0.08, dr * 0.45) * math.sin(math.pi * kr)
            return lf, rf, ll, rl
    e = K_FEET[-1]
    return e[1], e[2], 0.0, 0.0


# ---------------------------------------------------------------------------------------------- the attack: the gun's moves
def lever_ang(f):
    if f <= OPEN0:
        return 0.0
    if f <= OPEN1:
        return LEV_OPEN * ease((f - OPEN0) / float(OPEN1 - OPEN0))
    if f <= CLOSE0:
        return LEV_OPEN
    if f <= CLOSE1:
        return LEV_OPEN * (1.0 - ease((f - CLOSE0) / float(CLOSE1 - CLOSE0)))
    return 0.0


def block_slide(f):
    a = lever_ang(f) / LEV_OPEN
    return fg.BLK_SLIDE * ease(min(1.0, max(0.0, (a - 0.25) / 0.75)))


# ---------------------------------------------------------------------------------------------- the attack: the round
CARRY_BASE = V(0.22, -0.38, 0.99)       # (body, rest) the round held across before him: its base at his left ...
CARRY_AX = V(-1.0, 0.0, 0.0)            # ... its nose to his right
S_NOSE_IN = fg.S_BR - fg.SHELL_L + 0.12  # the base's place along the bore when the nose is in the breech's mouth


def bore_x(Mb, s_base):
    """The round on the bore's axis, its base at s_base along the bore (rest -> posed)."""
    return Mb @ xform(SH_BASE0, SH_A0, Z_, vec(fg.bore_pt(s_base)), GD, GU)


def carry_x(ro, yaw):
    q = rz(yaw)
    return xform(SH_BASE0, SH_A0, Z_, body_pt(CARRY_BASE, ro, yaw), q @ CARRY_AX, Z_)


def body_at(f):
    return smooth_keys(K_RO, f), smooth_keys(K_YAW, f)


def round_track(f):
    """The round at frame f: (kind, placement) with kind 'box', 'carry', 'breech' or 'home' (hidden)."""
    Mb = m_barrel(f, 0.0, 0.0)
    if f < GRAB:
        return "box", Matrix.Identity(4)
    if f > HOME:
        return "home", bore_x(Mb, fg.S_CASE)
    ro, yaw = body_at(f)
    if f <= LIFT:
        k = ease((f - GRAB) / float(LIFT - GRAB))
        return "carry", Matrix.Translation(Z_ * 0.08 * math.sin(math.pi * k)) @ blend_m(Matrix.Identity(4), carry_x(ro, yaw), k, SH_MID)
    if f <= SWING:
        return "carry", carry_x(ro, yaw)
    if f <= AT_BREECH:
        k = ease((f - SWING) / float(AT_BREECH - SWING))
        return "carry", blend_m(carry_x(ro, yaw), bore_x(Mb, S_NOSE_IN), k, SH_MID)
    k = ease((f - AT_BREECH) / float(HOME - AT_BREECH))
    return "breech", bore_x(Mb, lerp(S_NOSE_IN, fg.S_BR, k))


SH_MID = SH_BASE0 + SH_A0 * (fg.SHELL_L * 0.5)


def round_hands(X, yaw):
    """His palms on the round's ends (placement X): (contact, turn) for the left (on its base) and the right (cupping its
    nose), the fingers pointing away from him and a little down."""
    ax = (X.to_3x3() @ SH_A0).normalized()
    fing = rz(yaw) @ V(0.0, -1.0, 0.0) - Z_ * 0.45
    base = X @ SH_BASE0
    left = (base - ax * 0.018, palm_rot("L", ax, fing))
    right = (base + ax * (fg.SHELL_L + 0.014), palm_rot("R", -ax, fing))
    return left, right


def palm_to_fist(side, c, R):
    """The fist's middle for a palm contact c with the hand turned by R (for blending into grips)."""
    if side == "R":
        return c - R @ (PALM_R - WR_R) + R @ (FIST_R - WR_R)
    return c - R @ (PALM_L - WR_L) + R @ (FIST_L - WR_L)


# ---------------------------------------------------------------------------------------------- the attack: the spent case
CASE_MID = CASE_B0 + GD * (fg.CASE_L * 0.5)
CASE_OUT = 2                # frames to slide out of the breech
CASE_V = V(0.5, 0.36, 0.9)   # m/s once clear: back, out to the gun's left (away from him), and up
CASE_HIDE = 47


def case_track(f, Mb_now):
    """The spent case: in the chamber till EJECT; it shoots out of the breech, flies back over the trail tumbling, lands,
    hops and rolls a little; hidden from CASE_HIDE. Returns (rest -> posed, scale)."""
    if f < EJECT:
        return Mb_now, 0.0
    Mb_e = m_barrel(EJECT, 0.0, 0.0)
    d_out = (Mb_e.to_3x3() @ GD) * -(fg.CASE_L + 0.12)
    if f <= EJECT + CASE_OUT:
        k = (f - EJECT) / float(CASE_OUT)
        return Matrix.Translation(d_out * k) @ Mb_e, 1.0
    p0 = Mb_e @ CASE_MID + d_out
    tl = (CASE_V.z + math.sqrt(CASE_V.z ** 2 + 19.6 * max(0.0, p0.z - fg.CASE_R - 0.004))) / 9.8
    t = (f - EJECT - CASE_OUT) / FPS
    R0 = Mb_e.to_quaternion()
    if t <= tl:
        p = p0 + CASE_V * t + V(0.0, 0.0, -4.9 * t * t)
        R = (Quaternion((1, 0, 0), 11.0 * t) @ R0).to_matrix()
    else:
        pl = p0 + CASE_V * tl + V(0.0, 0.0, -4.9 * tl * tl)
        k = min(1.0, (t - tl) * FPS / 9.0)
        lie = Quaternion((0, 0, 1), math.radians(18.0)) @ Quaternion((1, 0, 0), math.radians(-3.0)) @ R0
        roll = ease(k)
        hop = 0.035 * math.sin(math.pi * min(1.0, k * 2.5)) if k < 0.4 else 0.0
        p = V(pl.x + 0.07 * roll, pl.y + 0.02 * roll, fg.CASE_R + 0.004 + hop)
        R = (Quaternion((1, 0, 0), 11.0 * tl) @ R0).slerp(lie, ease(min(1.0, k * 3.0))).to_matrix()
    M = R.to_4x4()
    M.translation = p - R @ CASE_MID
    return M, (1.0 if f < CASE_HIDE else 0.0)


# ---------------------------------------------------------------------------------------------- the attack: pose
def toggle_free(f, q):
    """The dropped toggle (rest -> posed): falling from his fist and swinging back under its eye, then hanging."""
    _, Th = hanging_toggle(f)
    ro_l, yaw_l = body_at(LET_GO)
    F_let, R_let = hold_toggle(ro_l, yaw_l, pull=0.6)
    M_let = Matrix.Translation(F_let) @ (R_let @ X_TOG.to_3x3()).to_4x4() @ Matrix.Translation(-TOG0)
    k = ease(min(1.0, (f - LET_GO) / 6.0))
    u = min(1.0, (f - LET_GO) / 12.0)
    sw = 0.07 * math.sin(math.pi * u * 2.0) * (1.0 - u)
    return Matrix.Translation(q @ V(sw, 0.0, 0.0)) @ blend_m(M_let, Matrix.Translation(Th - TOG0), k, TOG0)


def attack_pose(arm, f, rest):
    ro, yaw = body_at(f)
    lf, rf, ll, rl = feet_at(f)
    aims = feet(arm, lf, rf, smooth_keys(K_FYAW, f), lift_l=ll, lift_r=rl)
    torso(aims, yaw, bend=smooth_keys(K_BEND, f), side=0.06, chest=smooth_keys(K_CHEST, f), look=smooth_keys(K_LOOK, f),
          pitch=smooth_keys(K_PITCH, f))
    q = rz(yaw)
    sc, off = {}, {}
    pole_r, pole_l = q @ V(-1.0, 0.3, -0.5), q @ V(1.0, 0.3, -0.5)
    # ---- the gun
    lev = lever_ang(f)
    g, go, Mb = gun_aims(f, rest, rec=recoil(f), slide=block_slide(f), lev=lev)
    aims.update(g)
    off.update(go)
    R_lev = fist_rot("L", (m_lever(Mb, lev).to_3x3() @ X_) * -1.0, V(0.0, -0.4, 1.0))
    # ---- the round and the hands on it
    kind, X = round_track(f)
    aims["shell"] = ("world", X @ rest.m["shell"])
    sc["shell"] = 0.0 if kind == "home" else 1.0
    (cl, Rl), (cr, Rr) = round_hands(X, yaw)
    left = right = None
    if REACH0 <= f < GRAB:                                       # reaching for it in the box
        k = ease((f - REACH0) / float(GRAB - REACH0))
        hl, Rhl = (lever_tip(Mb, LEV_OPEN), R_lev)
        hr_, Rhr = hip_fist("R", ro, yaw)
        aims.update(grip_l(arm, hl.lerp(palm_to_fist("L", cl, Rl), k),
                           Rhl.to_quaternion().slerp(Rl.to_quaternion(), k).to_matrix(), pole=pole_l))
        aims.update(grip_r(arm, hr_.lerp(palm_to_fist("R", cr, Rr), k),
                           Rhr.to_quaternion().slerp(Rr.to_quaternion(), k).to_matrix(), pole=pole_r))
        left = right = "reach"
    elif GRAB <= f <= HOME:
        if f <= HOME:
            # the left palm stays on the base; it stops at the breech's face while the round slides home
            aims.update(palm_at(arm, "L", cl, Rl, pole=pole_l))
            left = "round"
        if f < AT_BREECH:
            aims.update(palm_at(arm, "R", cr, Rr, pole=pole_r))
            right = "round"
    # ---- the toggle: held, dropped, picked up again
    A = cord_eye(f)
    if f <= LET_GO:
        pull = ease(min(1.0, f / float(SHOT))) if f <= SHOT else 1.0 - 0.4 * ease((f - SHOT) / float(LET_GO - SHOT))
        F, R = hold_toggle(ro, yaw, pull=pull)
        aims.update(grip_r(arm, F, R, pole=q @ V(-1.0, 0.4, -0.4)))
        aims["toggle"] = toggle_in_hand(rest)
        aims["lanyard"] = lanyard_aim(rest, A, held=True)
        lan = ("held", A, None)
        right = "toggle"
    elif f >= TAKE:
        k = ease((f - TAKE) / float(FR - TAKE))
        _, Th = hanging_toggle(f)
        F0, R0 = hold_toggle(ro, yaw)
        Rt = fist_rot("R", X_, V(0.3, -0.6, -1.0))
        F = Th.lerp(F0, k) + Z_ * 0.06 * math.sin(math.pi * k)
        R = Rt.to_quaternion().slerp(R0.to_quaternion(), k).to_matrix()
        aims.update(grip_r(arm, F, R, pole=q @ V(-1.0, 0.4, -0.4)))
        aims["toggle"] = toggle_in_hand(rest)
        aims["lanyard"] = lanyard_aim(rest, A, held=True)
        lan = ("held", A, None)
        right = "toggle"
    else:
        M = toggle_free(f, q)
        T = M @ TOG0
        aims["toggle"] = ("world", M @ rest.m["toggle"])
        aims["lanyard"] = lanyard_aim(rest, A, T=T)
        lan = ("hang", A, T)
    # ---- his right hand between the jobs
    if right is None:
        if LET_GO < f < REACH0:
            aims.update(hip_aims(arm, "R", ro, yaw))
        elif AT_BREECH <= f < TAKE:
            # from the round's nose down to the hanging toggle
            k = ease((f - AT_BREECH) / float(TAKE - AT_BREECH))
            _, Xa = round_track(AT_BREECH - 1)
            (_, _), (c0, R0) = round_hands(Xa, body_at(AT_BREECH - 1)[1])
            w0 = palm_to_fist("R", c0, R0)
            _, Th = hanging_toggle(f)
            Rt = fist_rot("R", X_, V(0.3, -0.6, -1.0))
            p = w0.lerp(Th, k) + Z_ * 0.12 * math.sin(math.pi * k)
            R = R0.to_quaternion().slerp(Rt.to_quaternion(), k).to_matrix()
            aims.update(grip_r(arm, p, R, pole=pole_r))
        else:
            aims.update(hip_aims(arm, "R", ro, yaw))
    # ---- his left hand: the handwheel, the lever
    if left is None:
        if f <= 4:
            aims.update(knob_hold(arm, f, 0.0, yaw))
        elif f < ON_LEVER:
            k = ease((f - 4) / float(ON_LEVER - 4))
            p = knob_at(f, 0.0).lerp(lever_tip(Mb, 0.0), k) + Z_ * 0.08 * math.sin(math.pi * k)
            Rq = knob_rot().to_quaternion().slerp(R_lev.to_quaternion(), k).to_matrix()
            aims.update(grip_l(arm, p, Rq, pole=pole_l))
        elif f < REACH0:
            aims.update(grip_l(arm, lever_tip(Mb, lev), R_lev, pole=pole_l))
        elif HOME < f < CLOSE0:
            k = ease((f - HOME) / float(CLOSE0 - HOME))
            _, Xh = round_track(HOME)
            (c0, R0), _ = round_hands(Xh, body_at(HOME)[1])
            w0 = palm_to_fist("L", c0, R0)
            p = w0.lerp(lever_tip(Mb, LEV_OPEN), k) + Z_ * 0.04 * math.sin(math.pi * k)
            Rq = R0.to_quaternion().slerp(R_lev.to_quaternion(), k).to_matrix()
            aims.update(grip_l(arm, p, Rq, pole=pole_l))
        elif CLOSE0 <= f <= CLOSE0 + 2:
            aims.update(grip_l(arm, lever_tip(Mb, lev), R_lev, pole=pole_l))
        elif CLOSE0 + 2 < f < KNOB:
            # he lets the lever fall shut and reaches for the handwheel
            k = ease((f - CLOSE0 - 2) / float(KNOB - CLOSE0 - 2))
            Mb2 = m_barrel(CLOSE0 + 2, 0.0, 0.0)
            a2 = lever_ang(CLOSE0 + 2)
            R2 = fist_rot("L", (m_lever(Mb2, a2).to_3x3() @ X_) * -1.0, V(0.0, -0.4, 1.0))
            p = lever_tip(Mb2, a2).lerp(knob_at(f, 0.0), k) + Z_ * 0.06 * math.sin(math.pi * k)
            Rq = R2.to_quaternion().slerp(knob_rot().to_quaternion(), k).to_matrix()
            aims.update(grip_l(arm, p, Rq, pole=pole_l))
        else:
            aims.update(knob_hold(arm, f, 0.0, yaw))
    # ---- the spent case, the glasses
    Mc, s_case = case_track(f, Mb)
    aims["case"] = ("world", Mc @ rest.m["case"])
    sc["case"] = s_case
    aims["glasses"] = lambda P, base: ("world", P["chest"] @ rest.inv["chest"] @ rest.m["glasses"])
    if f >= FR:                                                  # the next round lies ready in the box again
        sc["shell"] = 1.0
        aims["shell"] = ("world", rest.m["shell"])
    return aims, ro, yaw, sc, off, lan


def make_attack(arm, frames=FR):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, yaw, sc, off, lan = attack_pose(arm, f, rest)
        _finish(P, aims, ro, yaw, sc, off, lan, rest, f)
    _const(act)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
