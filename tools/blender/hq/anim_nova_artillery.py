"""Nova Artillery clips (game: 24 fps).

Idle   : the gun loaded and laid, its coils glowing; he stands at ease by the breech, his left hand resting on the firing
         grip's cap, his right fist on his hip; he breathes and looks about, and once reaches up and settles the goggles on
         his bandana, then lets his hand drop.
Combat : laid on the target: crouched beside the breech, leaning in, his left fist round the firing grip, his right fist on
         his hip, eyes on the field and now and then down at the breech.
Attack : (52 frames, inside the 2.2 s cooldown) the coils swell and he squeezes the grip: the gun fires (SHOT, frame 3: the
         game's star-hot shell leaves the muzzle there): the barrel slams back along its sled and runs out again, the gun
         rocking up on its spade, the coils going dark; as it runs out the breech opens by itself (the lever swings back,
         the block slides out) and the spent case flies out over the trail. He flinches back from the blast, lets go of the
         grip, turns to his ready rack, lifts a fresh glowing shell out of it with both hands, carries it to the breech and
         pushes it home with his palm, swings the lever shut (the block slides closed, the coils glow back up) and is back
         at the grip.

The gun's bones are posed directly ("world" aims): carriage (rocking about the spade at the shot), barrel (sliding back
along the sled), block (sliding out to open), lever (on the barrel, swinging up and back); coils (on the barrel) are scaled
in across the bore to go dark. The shell and the spent case are free bones posed in the world; their scales hide the shell
once it is home and the case outside the ejection."""
import math
from mathutils import Vector, Quaternion, Matrix
import nova_artillery as na
from rig import Poser, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease
from anim_cannon import rz, fwd, rgt, body_pt, wroot, smooth_keys, xform, perp, feet, torso, grip_r, grip_l
from anim_field_gun import (fist_rot, palm_rot, palm_at, hip_fist, hip_aims, body_matrix, blend_m, stance, palm_to_fist,
                            PALM_R, PALM_L, WR_R, WR_L, FIST_R, FIST_L)

FPS = 24
J = na.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
X_, Z_ = V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0)

GD, GU = vec(na.GD), vec(na.GU)
KP = vec(na.KICK_P)
LEV_P = vec(na.LEV_P)
LEV_TIP = vec(na.LEV_P + na.GD * na.LEV_L + na.GX_ * -0.01)
GRIP_C, GRIP_A = vec(na.GRIP_C), vec(na.GRIP_A)
GRIP_CAP = vec(na.GRIP_C + na.GRIP_A * 0.075)
SH_BASE0, SH_A0 = vec(na.SH_BASE0), vec(na.SH_A0)
CASE_B0 = vec(na.bore_pt(na.S_CASE))

# ---------------------------------------------------------------------------------------------- timing (24 fps)
PRESS = 2          # his fist squeezes the grip
SHOT = 3           # the gun fires (game: the shell leaves the muzzle), the barrel slams back
REC_PEAK = 6       # fully recoiled
RUN_OUT = 13       # run out again
OPEN0, OPEN1 = 10, 14       # the breech opens by itself as the barrel runs out (lever back, block out)
EJECT = 13         # the spent case leaves the breech
LET_GO = 7         # his hand off the grip
REACH0 = 11        # his hands go for the shell in the rack ...
GRAB = 17          # ... and hold it by its ends
LIFT = 20          # lifted out
SWING = 24         # (turning back to the gun with it)
AT_BREECH = 28     # its nose in the breech's mouth; his right hand lets go of the nose
HOME = 33          # his left palm pushes its base to the breech's face; it slides home (hidden from HOME + 1)
CLOSE0, CLOSE1 = 35, 38     # the lever swung shut (left hand), the block closing
CH0, CH1 = 37, 46  # the coils glow back up
BACK = 46          # his left fist back on the grip
FR = 52            # = the 2.2 s cooldown (52.8 frames)

REC = 0.3          # the recoil (m)
KICK = 2.6         # the gun rocking up about its spade (degrees)
LEV_OPEN = 120.0   # the lever's swing (degrees)
DIM = 0.82         # the coils' scale across the bore when dark (their bands below the grooves' bottoms)


# ---------------------------------------------------------------------------------------------- the gun
def recoil(f):
    if f <= SHOT:
        return 0.0
    if f <= REC_PEAK:
        k = (f - SHOT) / float(REC_PEAK - SHOT)
        return REC * (1.0 - (1.0 - k) ** 3)
    if f <= RUN_OUT:
        return REC * (1.0 - ease((f - REC_PEAK) / float(RUN_OUT - REC_PEAK)))
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
        return -0.4 * math.sin(math.pi * (t - 5) / 2.0)
    return 0.0


def carr(f):
    """The carriage's rigid motion at frame f (rest -> posed): rocking up about the spade, shoved back a little."""
    sh = 0.022 * math.sin(math.pi * min(1.0, max(0.0, (f - SHOT) / 6.0))) if f > SHOT else 0.0
    return (Matrix.Translation(KP + V(0.0, sh, 0.0)) @ Matrix.Rotation(-math.radians(kick(f)), 4, "X")
            @ Matrix.Translation(-KP))


def m_barrel(f, rec):
    return carr(f) @ Matrix.Translation(-GD * rec)


def m_lever(Mb, ang):
    return Mb @ Matrix.Translation(LEV_P) @ Matrix.Rotation(-math.radians(ang), 4, "X") @ Matrix.Translation(-LEV_P)


def coil_scale(f):
    """The coils' scale across the bore: swelling as they charge before the shot, dark after it, glowing back up once the
    breech is closed (a little past full, settling)."""
    if f <= SHOT:
        return 1.0 + 0.06 * ease(f / float(SHOT))
    if f < CH0:
        return DIM
    if f <= CH1:
        k = (f - CH0) / float(CH1 - CH0)
        if k < 0.7:
            return lerp(DIM, 1.04, ease(k / 0.7))
        return lerp(1.04, 1.0, ease((k - 0.7) / 0.3))
    return 1.0


def sc_across(s):
    return (s, 1.0, s)


class Rest:
    """Rest matrices of the bones the props ride on (from the armature)."""
    def __init__(self, arm):
        b = arm.data.bones
        self.m = {n: b[n].matrix_local.copy() for n in ("carriage", "barrel", "block", "lever", "shell", "case", "props",
                                                        "chest", "hand.R", "hand.L")}
        self.inv = {n: m.inverted() for n, m in self.m.items()}


def gun_aims(f, rest, rec=0.0, slide=0.0, lev=0.0):
    """The gun's bones at frame f: recoil rec (m), the block's slide (m), the lever's swing (deg). Returns aims and the
    barrel's matrix."""
    Mb = m_barrel(f, rec)
    aims = {"carriage": ("world", carr(f) @ rest.m["carriage"]),
            "barrel": ("world", Mb @ rest.m["barrel"]),
            "block": ("world", Mb @ Matrix.Translation(X_ * slide) @ rest.m["block"]),
            "lever": ("world", m_lever(Mb, lev) @ rest.m["lever"]),
            "props": ("world", rest.m["props"])}
    return aims, Mb


def lever_tip(Mb, ang):
    return m_lever(Mb, ang) @ LEV_TIP


def lever_rot(Mb, ang):
    return fist_rot("L", (m_lever(Mb, ang).to_3x3() @ X_) * -1.0, V(0.0, -0.4, 1.0))


# ---------------------------------------------------------------------------------------------- the grip
def grip_fist(f=0, press=0.0, yaw=22.0):
    """His left fist round the firing grip (riding the carriage), the thumb up it, the knuckles out to his left and
    forward."""
    M = carr(f)
    ax = (M.to_3x3() @ GRIP_A).normalized()
    p = M @ (GRIP_C - GRIP_A * (0.004 + 0.006 * press))
    return p, fist_rot("L", ax, rz(yaw) @ V(0.75, -0.6, 0.0))


def apply_hand(arm, aims, side, fist, R, pole):
    aims.update((grip_r if side == "R" else grip_l)(arm, fist, R, pole=pole))


def blend_hand(a, b, k, lift=0.0):
    (pa, Ra), (pb, Rb) = a, b
    p = pa.lerp(pb, k) + Z_ * (lift * math.sin(math.pi * k))
    return p, Ra.to_quaternion().slerp(Rb.to_quaternion(), k).to_matrix()


# ---------------------------------------------------------------------------------------------- stations
S_XY, S_YAW = (0.24, 0.02), 22.0               # Combat: crouched beside the breech, his left fist on the grip
I_XY, I_YAW = (0.22, 0.06), 26.0               # Idle: at ease by the grip
F_XY = (0.2, 0.09)                             # flinching back from the blast
C_XY, C_YAW = (0.25, 0.05), -84.0              # at the rack (facing -X)
W_XY = (0.32, 0.16)                            # swinging back to the gun with the shell
L0_XY, L1_XY, L_YAW = (0.4, 0.27), (0.41, 0.15), 90.0    # loading: side-on to the breech, facing the gun
K_XY = (0.36, 0.08)                            # closing the lever
S_STANCE = (1.12, 0.12, -0.06)


def combat_body(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    yaw = S_YAW + 1.0 * math.sin(w)
    ro = wroot(S_XY[0], S_XY[1], ROOT.z - 0.06 + 0.004 * br)
    lf, rf = stance(S_XY, S_YAW, *S_STANCE)
    aims = feet(arm, lf, rf, S_YAW)
    down = 0.5 + 0.5 * math.sin(w - 0.8)
    look = yaw - 8.0 + 8.0 * math.sin(w) * (1.0 - down) + 20.0 * down
    torso(aims, yaw, bend=0.18, side=0.05, chest=4.0, look=look, pitch=-0.05 - 0.3 * down, br=br)
    return aims, ro, yaw, br


def combat_pose(arm, t, rest):
    aims, ro, yaw, br = combat_body(arm, t)
    g, Mb = gun_aims(0, rest)
    aims.update(g)
    q = rz(yaw)
    p, R = grip_fist(0, 0.0, yaw)
    apply_hand(arm, aims, "L", p, R, q @ V(1.0, 0.5, -0.5))
    hp_, hR = hip_fist("R", ro, yaw)
    apply_hand(arm, aims, "R", hp_, hR, q @ V(-1.0, 0.5, 0.1))
    aims["shell"] = ("world", rest.m["shell"])
    aims["case"] = ("world", rest.m["case"])
    return aims, ro, yaw, {"shell": 1.0, "case": 0.0, "coils": sc_across(1.0)}


def idle_pose(arm, t, rest):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    gog = math.sin(math.pi * min(1.0, max(0.0, (t - 0.4) / 0.28))) ** 2 if 0.4 < t < 0.68 else 0.0
    yaw = I_YAW + 2.5 * math.sin(w)
    ro = wroot(I_XY[0] + 0.008 * math.sin(w), I_XY[1], ROOT.z - 0.012 + 0.005 * br)
    lf, rf = stance(I_XY, I_YAW, 1.06, 0.02, 0.02)
    aims = feet(arm, lf, rf, I_YAW)
    look = yaw - 10.0 + (1.0 - gog) * (26.0 * math.sin(w) + 8.0 * math.sin(w * 3)) - 6.0 * gog
    torso(aims, yaw, bend=0.03, side=0.03 * math.sin(w), chest=-4.0 + 2.0 * math.sin(w), look=look,
          pitch=0.04 + 0.03 * br + 0.06 * gog, br=br)
    q = rz(yaw)
    g, Mb = gun_aims(0, rest)
    aims.update(g)
    aims["shell"] = ("world", rest.m["shell"])
    aims["case"] = ("world", rest.m["case"])
    # his left hand resting on the grip's cap
    top = GRIP_CAP + V(0.0, 0.0, 0.022 + 0.003 * br)
    Rl = palm_rot("L", V(0.0, 0.0, -1.0), q @ V(0.4, -1.0, 0.0))
    apply_hand(arm, aims, "L", palm_to_fist("L", top, Rl), Rl, q @ V(1.0, 0.6, -0.2))
    # his right fist on his hip; lifted to settle the goggles on his bandana now and then
    hip = hip_fist("R", ro, yaw)
    if gog > 0.0:
        lens = body_pt(na.hp((-0.07, -0.29, 1.905)), ro, yaw)
        Rc = palm_rot("R", q @ V(0.15, 1.0, -0.3), Z_ + q @ V(0.3, 0.0, 0.0))
        p, R = blend_hand(hip, (palm_to_fist("R", lens, Rc), Rc), gog)
        apply_hand(arm, aims, "R", p, R, q @ V(-1.0, 0.2, -0.8))
    else:
        apply_hand(arm, aims, "R", hip[0], hip[1], q @ V(-1.0, 0.5, 0.1))
    return aims, ro, yaw, {"shell": 1.0, "case": 0.0, "coils": sc_across(1.0)}


def _const(act):
    from anim_ugo import key_constant
    key_constant(act, 'pose.bones["shell"].scale')
    key_constant(act, 'pose.bones["case"].scale')


def make_idle(arm, frames=120):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, yaw, sc = idle_pose(arm, (f % frames) / frames, rest)
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    _const(act)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=48):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, yaw, sc = combat_pose(arm, (f % frames) / frames, rest)
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    _const(act)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- the attack: body tracks
def _r(xy, z=0.0):
    return wroot(xy[0], xy[1], ROOT.z + z)


K_RO = [(0, _r(S_XY, -0.06)), (SHOT, _r(S_XY, -0.065)), (5, _r(F_XY, -0.04)), (LET_GO, _r(F_XY, -0.03)),
        (REACH0, _r((0.24, 0.07), -0.08)), (GRAB, _r(C_XY, -0.24)), (LIFT, _r(C_XY, -0.1)), (SWING, _r(W_XY, -0.06)),
        (AT_BREECH, _r(L0_XY, -0.1)), (HOME, _r(L1_XY, -0.12)), (CLOSE1, _r(K_XY, -0.1)), (BACK, _r(S_XY, -0.06)),
        (FR, _r(S_XY, -0.06))]
K_YAW = [(0, S_YAW), (SHOT, S_YAW - 2.0), (5, S_YAW - 8.0), (LET_GO, S_YAW - 6.0), (REACH0, -40.0), (GRAB, C_YAW),
         (LIFT, C_YAW + 4.0), (SWING, 24.0), (AT_BREECH, L_YAW), (HOME, L_YAW + 2.0), (CLOSE1, 62.0), (BACK, S_YAW),
         (FR, S_YAW)]
K_BEND = [(0, 0.18), (SHOT, 0.14), (5, -0.1), (LET_GO, -0.04), (REACH0, 0.3), (GRAB, 0.62), (LIFT, 0.22), (SWING, 0.15),
          (AT_BREECH, 0.4), (HOME, 0.46), (CLOSE1, 0.34), (BACK, 0.18), (FR, 0.18)]
K_CHEST = [(0, 4.0), (SHOT, 2.0), (5, -10.0), (LET_GO, -6.0), (REACH0, 0.0), (GRAB, 0.0), (LIFT, 0.0), (AT_BREECH, 0.0),
           (HOME, 6.0), (CLOSE1, 6.0), (BACK, 4.0), (FR, 4.0)]
K_LOOK = [(0, S_YAW - 8.0), (SHOT, S_YAW - 6.0), (5, S_YAW - 30.0), (LET_GO, S_YAW - 14.0), (REACH0, -60.0),
          (GRAB, C_YAW + 4.0), (LIFT, C_YAW + 12.0), (SWING, 50.0), (AT_BREECH, L_YAW + 8.0), (HOME, L_YAW + 10.0),
          (CLOSE1, L_YAW - 16.0), (BACK, S_YAW - 8.0), (FR, S_YAW - 8.0)]
K_PITCH = [(0, -0.05), (SHOT, 0.0), (5, 0.3), (LET_GO, 0.12), (REACH0, -0.25), (GRAB, -0.4), (LIFT, -0.2), (SWING, -0.1),
           (AT_BREECH, -0.35), (HOME, -0.35), (CLOSE1, -0.35), (BACK, -0.05), (FR, -0.05)]
_sS = stance(S_XY, S_YAW, *S_STANCE)
_sF = stance(F_XY, S_YAW - 6.0, 1.1, 0.04, -0.12)
_sC = stance(C_XY, C_YAW, 1.25, 0.1, -0.08)
_sW = stance(W_XY, 20.0, 1.05, 0.0, 0.0)
_sL0 = stance(L0_XY, L_YAW, 1.0, 0.06, -0.04)
_sL1 = stance(L1_XY, L_YAW, 1.05, 0.1, -0.08)
_sK = stance(K_XY, 62.0, 1.1, 0.1, -0.06)
K_FEET = [(0, _sS[0], _sS[1]), (SHOT + 1, _sS[0], _sS[1]), (LET_GO, _sF[0], _sF[1]), (LET_GO + 1, _sF[0], _sF[1]),
          (GRAB, _sC[0], _sC[1]), (LIFT, _sC[0], _sC[1]), (SWING, _sW[0], _sW[1]), (AT_BREECH, _sL0[0], _sL0[1]),
          (HOME, _sL1[0], _sL1[1]), (CLOSE0, _sL1[0], _sL1[1]), (CLOSE1 + 2, _sK[0], _sK[1]), (BACK, _sS[0], _sS[1]),
          (FR, _sS[0], _sS[1])]
K_FYAW = [(0, S_YAW), (SHOT + 1, S_YAW), (LET_GO, S_YAW - 6.0), (LET_GO + 1, S_YAW - 6.0), (GRAB, C_YAW), (LIFT, C_YAW),
          (SWING, 20.0), (AT_BREECH, L_YAW), (CLOSE0, L_YAW), (CLOSE1 + 2, 62.0), (BACK, S_YAW), (FR, S_YAW)]


def body_at(f):
    return smooth_keys(K_RO, f), smooth_keys(K_YAW, f)


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


# ---------------------------------------------------------------------------------------------- the attack: the breech
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
    return na.BLK_SLIDE * ease(min(1.0, max(0.0, (a - 0.25) / 0.75)))


# ---------------------------------------------------------------------------------------------- the attack: the shell
CARRY_BASE = V(0.22, -0.38, 0.99)       # (body, rest) the shell held across before him: its base at his left ...
CARRY_AX = V(-1.0, 0.0, 0.0)            # ... its nose to his right
S_NOSE_IN = na.S_BR - na.SHELL_L + 0.12  # the base's place along the bore when the nose is in the breech's mouth
SH_MID = SH_BASE0 + SH_A0 * (na.SHELL_L * 0.5)


def bore_x(Mb, s_base):
    """The shell on the bore's axis, its base at s_base along the bore (rest -> posed)."""
    return Mb @ xform(SH_BASE0, SH_A0, Z_, vec(na.bore_pt(s_base)), GD, GU)


def carry_x(ro, yaw):
    q = rz(yaw)
    return xform(SH_BASE0, SH_A0, Z_, body_pt(CARRY_BASE, ro, yaw), q @ CARRY_AX, Z_)


def shell_track(f):
    """The shell at frame f: (kind, placement) with kind 'rack', 'carry', 'breech' or 'home' (hidden)."""
    Mb = m_barrel(f, 0.0)
    if f < GRAB:
        return "rack", Matrix.Identity(4)
    if f > HOME:
        return "home", bore_x(Mb, na.S_CASE)
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
    return "breech", bore_x(Mb, lerp(S_NOSE_IN, na.S_BR, k))


def shell_hands(X, yaw):
    """His palms on the shell's ends (placement X): (contact, turn) for the left (on its base) and the right (cupping its
    nose), the fingers pointing away from him and a little down."""
    ax = (X.to_3x3() @ SH_A0).normalized()
    fing = rz(yaw) @ V(0.0, -1.0, 0.0) - Z_ * 0.45
    base = X @ SH_BASE0
    left = (base - ax * 0.018, palm_rot("L", ax, fing))
    right = (base + ax * (na.SHELL_L + 0.014), palm_rot("R", -ax, fing))
    return left, right


# ---------------------------------------------------------------------------------------------- the attack: the spent case
CASE_MID = CASE_B0 + GD * (na.CASE_L * 0.5)
CASE_OUT = 2                 # frames to slide out of the breech
CASE_V = V(0.3, 0.5, 0.95)   # m/s once clear: back over the trail, out to the gun's far side (away from him), and up
CASE_HIDE = 47


def case_track(f, Mb_now):
    """The spent case: in the chamber till EJECT; it shoots out of the breech, flies back over the trail tumbling, lands,
    hops and rolls a little; hidden from CASE_HIDE. Returns (rest -> posed, scale)."""
    if f < EJECT:
        return Mb_now, 0.0
    Mb_e = m_barrel(EJECT, 0.0)
    d_out = (Mb_e.to_3x3() @ GD) * -(na.CASE_L + 0.12)
    if f <= EJECT + CASE_OUT:
        k = (f - EJECT) / float(CASE_OUT)
        return Matrix.Translation(d_out * k) @ Mb_e, 1.0
    p0 = Mb_e @ CASE_MID + d_out
    tl = (CASE_V.z + math.sqrt(CASE_V.z ** 2 + 19.6 * max(0.0, p0.z - na.CASE_R - 0.004))) / 9.8
    t = (f - EJECT - CASE_OUT) / FPS
    R0 = Mb_e.to_quaternion()
    if t <= tl:
        p = p0 + CASE_V * t + V(0.0, 0.0, -4.9 * t * t)
        R = (Quaternion((1, 0, 0), 11.0 * t) @ R0).to_matrix()
    else:
        pl = p0 + CASE_V * tl + V(0.0, 0.0, -4.9 * tl * tl)
        k = min(1.0, (t - tl) * FPS / 9.0)
        lie = Quaternion((0, 0, 1), math.radians(18.0)) @ Quaternion((1, 0, 0), math.radians(-15.0)) @ R0
        roll = ease(k)
        hop = 0.035 * math.sin(math.pi * min(1.0, k * 2.5)) if k < 0.4 else 0.0
        p = V(pl.x + 0.07 * roll, pl.y + 0.02 * roll, na.CASE_R + 0.004 + hop)
        R = (Quaternion((1, 0, 0), 11.0 * tl) @ R0).slerp(lie, ease(min(1.0, k * 3.0))).to_matrix()
    M = R.to_4x4()
    M.translation = p - R @ CASE_MID
    return M, (1.0 if f < CASE_HIDE else 0.0)


# ---------------------------------------------------------------------------------------------- the attack: pose
def attack_pose(arm, f, rest):
    ro, yaw = body_at(f)
    lf, rf, ll, rl = feet_at(f)
    aims = feet(arm, lf, rf, smooth_keys(K_FYAW, f), lift_l=ll, lift_r=rl)
    torso(aims, yaw, bend=smooth_keys(K_BEND, f), side=0.05, chest=smooth_keys(K_CHEST, f), look=smooth_keys(K_LOOK, f),
          pitch=smooth_keys(K_PITCH, f))
    q = rz(yaw)
    sc = {}
    pole_r, pole_l = q @ V(-1.0, 0.3, -0.5), q @ V(1.0, 0.3, -0.5)
    # ---- the gun
    lev = lever_ang(f)
    g, Mb = gun_aims(f, rest, rec=recoil(f), slide=block_slide(f), lev=lev)
    aims.update(g)
    sc["coils"] = sc_across(coil_scale(f))
    # ---- the shell and the hands on it
    kind, X = shell_track(f)
    aims["shell"] = ("world", X @ rest.m["shell"])
    sc["shell"] = 0.0 if kind == "home" else 1.0
    (cl, Rl), (cr, Rr) = shell_hands(X, yaw)
    left = right = None
    if REACH0 <= f < GRAB:                                       # reaching for it in the rack
        k = ease((f - REACH0) / float(GRAB - REACH0))
        ro0, yaw0 = body_at(REACH0)
        hl, Rhl = hip_fist("L", ro0, yaw0)
        hl = hl + rz(yaw0) @ V(0.06, -0.12, 0.08)
        hr_, Rhr = hip_fist("R", ro, yaw)
        aims.update(grip_l(arm, hl.lerp(palm_to_fist("L", cl, Rl), k),
                           Rhl.to_quaternion().slerp(Rl.to_quaternion(), k).to_matrix(), pole=pole_l))
        aims.update(grip_r(arm, hr_.lerp(palm_to_fist("R", cr, Rr), k),
                           Rhr.to_quaternion().slerp(Rr.to_quaternion(), k).to_matrix(), pole=pole_r))
        left = right = "reach"
    elif GRAB <= f <= HOME:
        aims.update(palm_at(arm, "L", cl, Rl, pole=pole_l))
        left = "shell"
        if f < AT_BREECH:
            aims.update(palm_at(arm, "R", cr, Rr, pole=pole_r))
            right = "shell"
    # ---- his right hand between the jobs
    if right is None:
        if AT_BREECH <= f < BACK:
            k = ease((f - AT_BREECH) / float(BACK - 4 - AT_BREECH)) if f < BACK - 4 else 1.0
            _, Xa = shell_track(AT_BREECH - 1)
            (_, _), (c0, R0) = shell_hands(Xa, body_at(AT_BREECH - 1)[1])
            w0 = palm_to_fist("R", c0, R0)
            hp_, hR = hip_fist("R", ro, yaw)
            p = w0.lerp(hp_, k) + Z_ * 0.05 * math.sin(math.pi * k)
            R = R0.to_quaternion().slerp(hR.to_quaternion(), k).to_matrix()
            aims.update(grip_r(arm, p, R, pole=pole_r))
        else:
            aims.update(hip_aims(arm, "R", ro, yaw))
    # ---- his left hand: the grip, the lever
    if left is None:
        if f <= LET_GO:
            press = 1.0 if PRESS <= f <= SHOT + 1 else 0.0
            gp = grip_fist(f, press, S_YAW)
            if f <= SHOT:
                aims.update(grip_l(arm, gp[0], gp[1], pole=q @ V(1.0, 0.5, -0.5)))
            else:
                k = (f - SHOT) / float(LET_GO - SHOT)
                p, R = blend_hand(gp, (gp[0] + V(-0.03, 0.08, 0.04), gp[1]), ease(k))
                aims.update(grip_l(arm, p, R, pole=q @ V(1.0, 0.5, -0.5)))
        elif f < REACH0:
            k = ease((f - LET_GO) / float(REACH0 - LET_GO))
            g0 = grip_fist(LET_GO, 0.0, S_YAW)
            a0 = (g0[0] + V(-0.03, 0.08, 0.04), g0[1])
            ro0, yaw0 = body_at(REACH0)
            hl, Rhl = hip_fist("L", ro0, yaw0)
            p, R = blend_hand(a0, (hl + rz(yaw0) @ V(0.06, -0.12, 0.08), Rhl), k, 0.03)
            aims.update(grip_l(arm, p, R, pole=pole_l))
        elif HOME < f < CLOSE0:
            k = ease((f - HOME) / float(CLOSE0 - HOME))
            _, Xh = shell_track(HOME)
            (c0, R0), _ = shell_hands(Xh, body_at(HOME)[1])
            w0 = palm_to_fist("L", c0, R0)
            p = w0.lerp(lever_tip(Mb, LEV_OPEN), k) + Z_ * 0.04 * math.sin(math.pi * k)
            Rq = R0.to_quaternion().slerp(lever_rot(Mb, LEV_OPEN).to_quaternion(), k).to_matrix()
            aims.update(grip_l(arm, p, Rq, pole=pole_l))
        elif CLOSE0 <= f <= CLOSE1:
            aims.update(grip_l(arm, lever_tip(Mb, lev), lever_rot(Mb, lev), pole=pole_l))
        elif CLOSE1 < f < BACK:
            k = ease((f - CLOSE1) / float(BACK - CLOSE1))
            Mb2 = m_barrel(CLOSE1, 0.0)
            a2 = (lever_tip(Mb2, 0.0), lever_rot(Mb2, 0.0))
            p, R = blend_hand(a2, grip_fist(f, 0.0, S_YAW), k, 0.05)
            aims.update(grip_l(arm, p, R, pole=pole_l))
        else:
            gp = grip_fist(f, 0.0, S_YAW)
            aims.update(grip_l(arm, gp[0], gp[1], pole=q @ V(1.0, 0.5, -0.5)))
    # ---- the spent case
    Mc, s_case = case_track(f, Mb)
    aims["case"] = ("world", Mc @ rest.m["case"])
    sc["case"] = s_case
    if f >= FR:                                                  # the next shell lies ready in the rack again
        sc["shell"] = 1.0
        aims["shell"] = ("world", rest.m["shell"])
    return aims, ro, yaw, sc


def make_attack(arm, frames=FR):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, yaw, sc = attack_pose(arm, f, rest)
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    _const(act)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
