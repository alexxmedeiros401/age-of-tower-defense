"""Plasma Mortar clips (game: 24 fps).

Idle   : the mortar charged and humming; he stands at ease beside it, his left hand resting on the firing grip's cap, his
         right fist on his hip; he breathes and looks about, and once lifts his right hand to his ear piece and listens,
         his head cocked, then lets it drop.
Combat : laid on the target: he leans in, his left fist round the firing grip, his right fist on his hip, eyes on the
         field and now and then down at the mortar.
Attack : (52 frames, inside the 2.2 s cooldown) the coils charge (their bands swell, frames 0-3) and he squeezes the
         trigger: the plasma ball leaves the bore (SHOT, frame 3: the game's plasma ball leaves the muzzle there), the tube
         slams back down through its gimbal ring and runs out again, the ring rocks; the coils go dark and the spent cell
         pops out of the breech's port, tumbling away (hidden once it is clear). He flinches back, grinning, lets go of the
         grip and steps back behind the breech, turning to the charging rack; takes a fresh cell from it, swings it over and
         slots it into the port; the coils glow back up (bands swelling a little past full and settling) while he steps
         back to the grip and lays the mortar again.

The mortar's bones are posed directly: cradle (the gimbal ring, rocking about the trunnions), tube (sliding back along
its axis), coils (scaled in across the tube's axis to go dark: their bands sink below the grooves). The cell is a free
bone posed in the world: seated in the port, ejected, hidden, taken from the rack and slotted in; its core (cellcore) is
scaled in to go dark when it is spent."""
import math
from mathutils import Vector, Quaternion, Matrix
import plasma_mortar as pm
from rig import Poser, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease
from anim_cannon import rz, fwd, rgt, body_pt, wroot, smooth_keys, xform, perp, feet, torso, grip_r, grip_l
from anim_field_gun import fist_rot, palm_rot, hip_fist, body_matrix, blend_m, stance, palm_to_fist

FPS = 24
J = pm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
X_, Z_ = V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0)

TRUN = vec(pm.TRUN_W)
GD0, GU0 = vec(pm.GD), vec(pm.GU)
_mid, _ax = pm.seated_cell()
CELL_MID0, CELL_AX0 = vec(_mid), vec(_ax)            # (rest) the seated cell
CELL_SIDE0 = X_
_pt, _pa = pm.port_top()
PORT0 = vec(_pt)
GRIP_C, GRIP_A = vec(pm.GRIP_W), vec(pm.GRIP_A)
GRIP_CAP = vec(pm.GRIP_CAP_W)
_rm, _ra = pm.rack_slot(pm.HIS_SLOT)
RACK_MID = vec(_rm)
HOLD = 0.075                    # his fist round the cell: this far up its axis from its middle

# ---------------------------------------------------------------------------------------------- timing (24 fps)
PRESS = 2          # his fist squeezes the trigger
SHOT = 3           # the plasma ball leaves the bore (game); the tube slams back
EJECT = 4          # the spent cell pops out of the port
HIDE = 12          # ... hidden once it is clear
LET_GO = 7         # his hand off the grip
GRAB = 15          # his right fist round the fresh cell in the rack
LIFT = 19          # lifted clear of its socket
AT_PORT = 26       # its foot at the port's mouth
SEAT = 31          # slotted home
CH0, CH1 = 32, 42  # the coils glow back up
OFF = 35           # his hand off the cell
BACK = 45          # back at the grip
FR = 52            # = the 2.2 s cooldown (52.8 frames)

REC = 0.09        # the tube's slam back (m)
DIM = 0.86         # the coils' scale across the tube when dark (their bands below the grooves' bottoms)
CORE_DIM = 0.7     # a spent cell's core


# ---------------------------------------------------------------------------------------------- the mortar
def recoil(f):
    if f < SHOT:
        return 0.0
    t = f - SHOT
    if t <= 1.0:
        return REC * (0.93 + 0.07 * t)
    if t <= 8.0:
        return REC * (1.0 - ease((t - 1.0) / 7.0))
    return 0.0


def rock(f):
    """The gimbal ring's rock at the shot (degrees, nose up +)."""
    if f < SHOT:
        return 0.0
    t = f - SHOT
    if t > 10:
        return 0.0
    return -2.2 * math.exp(-t / 2.4) * math.cos(t * 1.25)


def coil_scale(f):
    """The coils' scale across the tube: charging (swelling) before the shot, dark after it, glowing back up."""
    if f <= SHOT:
        return 1.0 + 0.075 * ease(f / float(SHOT))
    if f < CH0:
        return DIM
    if f <= CH1:
        k = (f - CH0) / float(CH1 - CH0)
        if k < 0.7:
            return lerp(DIM, 1.05, ease(k / 0.7))
        return lerp(1.05, 1.0, ease((k - 0.7) / 0.3))
    return 1.0


def m_cradle(f):
    return Matrix.Translation(TRUN) @ Matrix.Rotation(-math.radians(rock(f)), 4, "X") @ Matrix.Translation(-TRUN)


def m_tube(f):
    return m_cradle(f) @ Matrix.Translation(-GD0 * recoil(f))


class Rest:
    def __init__(self, arm):
        b = arm.data.bones
        self.m = {n: b[n].matrix_local.copy() for n in ("mount", "cradle", "tube", "cell", "chest", "hand.R", "hand.L")}
        self.inv = {n: m.inverted() for n, m in self.m.items()}


def mortar_aims(rest, f):
    return {"mount": ("world", rest.m["mount"]), "cradle": ("world", m_cradle(f) @ rest.m["cradle"]),
            "tube": ("world", m_tube(f) @ rest.m["tube"])}


def sc_across(s):
    return (s, 1.0, s)


# ---------------------------------------------------------------------------------------------- the cell
def cell_x(mid, ax, side=None):
    """The cell placed with its middle at `mid`, its axis along `ax` (rest -> posed)."""
    side = perp(side if side is not None else X_, ax.normalized())
    return xform(CELL_MID0, CELL_AX0, CELL_SIDE0, mid, ax.normalized(), side)


def seated_x(f, out=0.0):
    """The cell in the port, `out` short of home along its axis (rest -> posed)."""
    Mt = m_tube(f)
    return Mt @ Matrix.Translation(CELL_AX0 * out)


def rack_x():
    return cell_x(RACK_MID, Z_, V(0.0, -1.0, 0.0))


EJ_V = V(0.55, 0.75, 1.9)        # the spent cell's flight (m/s): out to the mortar's side, back and up


def eject_x(f):
    t = (f - EJECT) / float(FPS)
    M0 = seated_x(EJECT, 0.06)
    c0 = M0 @ CELL_MID0
    c = c0 + EJ_V * t + V(0.0, 0.0, -4.9 * t * t)
    R = Quaternion(V(1.0, 0.3, 0.0).normalized(), 9.0 * t).to_matrix() @ M0.to_3x3()
    M = R.to_4x4()
    M.translation = c - R @ CELL_MID0
    return M


def cell_track(f):
    """(placement, cell scale, core scale)."""
    if f < EJECT:
        return seated_x(f), 1.0, (1.0 if f < SHOT + 1 else CORE_DIM)
    if f < HIDE:
        if f == EJECT:
            return seated_x(f, 0.06), 1.0, CORE_DIM
        return eject_x(f), 1.0, CORE_DIM
    if f < GRAB:
        return rack_x(), 0.0, 1.0
    if f <= LIFT:
        k = ease((f - GRAB) / float(LIFT - GRAB))
        return Matrix.Translation(Z_ * 0.17 * k) @ rack_x(), 1.0, 1.0
    if f <= AT_PORT:
        k = ease((f - LIFT) / float(AT_PORT - LIFT))
        a = Matrix.Translation(Z_ * 0.17) @ rack_x()
        b = seated_x(f, 0.13)
        M = blend_m(a, b, k, CELL_MID0)
        return Matrix.Translation(Z_ * 0.08 * math.sin(math.pi * k)) @ M, 1.0, 1.0
    if f <= SEAT:
        k = ease((f - AT_PORT) / float(SEAT - AT_PORT))
        return seated_x(f, 0.13 * (1.0 - k)), 1.0, 1.0
    return seated_x(f), 1.0, 1.0


def cell_fist(M, yaw):
    """His right fist round the cell (placement M) near its top: (point, R)."""
    ax = (M.to_3x3() @ CELL_AX0).normalized()
    c = M @ (CELL_MID0 + CELL_AX0 * HOLD)
    return c, fist_rot("R", ax, perp(fwd(yaw) + rgt(yaw) * 0.4, ax))


# ---------------------------------------------------------------------------------------------- stations
S_XY, S_YAW = (-0.06, 0.22), 16.0              # Combat: beside the breech, his left fist on the grip
I_XY, I_YAW = (-0.04, 0.25), 22.0             # Idle: at ease by the grip
L_XY = (0.28, 0.43)                          # loading: behind the breech, between the rack and the port
R_YAW, P_YAW = 110.0, 58.0                    # ... facing the rack, facing the port
S_STANCE = (1.12, 0.12, -0.06)


def grip_fist(press=0.0, yaw=S_YAW):
    """His left fist round the firing grip, the thumb up it, the knuckles out to his left and forward."""
    q = rz(yaw)
    return GRIP_C - GRIP_A * (0.004 + 0.006 * press), fist_rot("L", GRIP_A, q @ V(0.75, -0.6, 0.0))


def apply_hand(arm, aims, side, fist, R, pole):
    aims.update((grip_r if side == "R" else grip_l)(arm, fist, R, pole=pole))


def blend_hand(a, b, k, lift=0.0):
    (pa, Ra), (pb, Rb) = a, b
    p = pa.lerp(pb, k) + Z_ * (lift * math.sin(math.pi * k))
    return p, Ra.to_quaternion().slerp(Rb.to_quaternion(), k).to_matrix()


def combat_body(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    yaw = S_YAW + 1.0 * math.sin(w)
    ro = wroot(S_XY[0], S_XY[1], ROOT.z - 0.045 + 0.004 * br)
    lf, rf = stance(S_XY, S_YAW, *S_STANCE)
    aims = feet(arm, lf, rf, S_YAW)
    down = 0.5 + 0.5 * math.sin(w - 0.8)               # now and then a glance down at the mortar
    look = yaw - 6.0 + 10.0 * math.sin(w) * (1.0 - down) + 18.0 * down
    torso(aims, yaw, bend=0.14, side=0.05, chest=4.0, look=look, pitch=-0.1 - 0.3 * down, br=br)
    return aims, ro, yaw, br


def combat_pose(arm, t, rest):
    aims, ro, yaw, br = combat_body(arm, t)
    aims.update(mortar_aims(rest, 0))
    q = rz(yaw)
    p, R = grip_fist(0.0, yaw)
    apply_hand(arm, aims, "L", p, R, q @ V(1.0, 0.5, -0.5))
    hp_, hR = hip_fist("R", ro, yaw)
    apply_hand(arm, aims, "R", hp_, hR, q @ V(-1.0, 0.5, 0.1))
    aims["cell"] = ("world", seated_x(0) @ rest.m["cell"])
    return aims, ro, yaw, {"cell": 1.0, "cellcore": sc_across(1.0), "coils": sc_across(1.0)}


def idle_pose(arm, t, rest):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    radio = math.sin(math.pi * min(1.0, max(0.0, (t - 0.38) / 0.3))) ** 2 if 0.38 < t < 0.68 else 0.0
    yaw = I_YAW + 2.5 * math.sin(w)
    ro = wroot(I_XY[0] + 0.008 * math.sin(w), I_XY[1], ROOT.z - 0.012 + 0.005 * br)
    lf, rf = stance(I_XY, I_YAW, 1.06, 0.02, 0.02)
    aims = feet(arm, lf, rf, I_YAW)
    look = yaw - 10.0 + (1.0 - radio) * (26.0 * math.sin(w) + 8.0 * math.sin(w * 3)) - 10.0 * radio
    torso(aims, yaw, bend=0.03, side=0.03 * math.sin(w), chest=-4.0 + 2.0 * math.sin(w), look=look,
          pitch=0.04 + 0.03 * br - 0.12 * radio, br=br, tilt_head=0.14 * radio)
    q = rz(yaw)
    aims.update(mortar_aims(rest, 0))
    aims["cell"] = ("world", seated_x(0) @ rest.m["cell"])
    # his left hand resting on the grip's cap
    top = GRIP_CAP + V(0.0, 0.0, 0.022 + 0.003 * br)
    Rl = palm_rot("L", V(0.0, 0.0, -1.0), q @ V(0.4, -1.0, 0.0))
    apply_hand(arm, aims, "L", palm_to_fist("L", top, Rl), Rl, q @ V(1.0, 0.6, -0.2))
    # his right fist on his hip; lifted to his right ear piece now and then
    hip = hip_fist("R", ro, yaw)
    if radio > 0.0:
        cup = body_pt(pm.hp((-0.27, 0.02, 1.66)), ro, yaw)
        Rc = palm_rot("R", q @ V(1.0, 0.0, 0.0), Z_ + q @ V(0.0, -0.4, 0.0))
        p, R = blend_hand(hip, (palm_to_fist("R", cup, Rc), Rc), radio)
        apply_hand(arm, aims, "R", p, R, q @ V(-1.0, 0.3, -0.7))
    else:
        apply_hand(arm, aims, "R", hip[0], hip[1], q @ V(-1.0, 0.5, 0.1))
    return aims, ro, yaw, {"cell": 1.0, "cellcore": sc_across(1.0), "coils": sc_across(1.0)}


def _const(act):
    from anim_ugo import key_constant
    key_constant(act, 'pose.bones["cell"].scale')
    key_constant(act, 'pose.bones["cellcore"].scale')


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


K_RO = [(0, _r(S_XY, -0.045)), (SHOT, _r(S_XY, -0.05)), (6, _r((-0.07, 0.27), -0.03)), (LET_GO, _r((-0.06, 0.28), -0.03)),
        (13, _r(L_XY, -0.07)), (GRAB, _r(L_XY, -0.12)), (LIFT, _r(L_XY, -0.07)), (AT_PORT, _r((0.33, 0.37), -0.13)),
        (SEAT, _r((0.35, 0.35), -0.17)), (OFF, _r((0.33, 0.37), -0.11)), (40, _r((0.15, 0.3), -0.05)),
        (BACK, _r(S_XY, -0.045)), (FR, _r(S_XY, -0.045))]
K_YAW = [(0, S_YAW), (SHOT, S_YAW - 2.0), (6, S_YAW - 6.0), (LET_GO, S_YAW), (13, R_YAW - 8.0), (GRAB, R_YAW),
         (LIFT, R_YAW - 6.0), (AT_PORT, P_YAW), (SEAT, P_YAW), (OFF, P_YAW + 4.0), (40, 24.0), (BACK, S_YAW), (FR, S_YAW)]
K_BEND = [(0, 0.14), (SHOT, 0.1), (6, -0.08), (LET_GO, -0.04), (13, 0.2), (GRAB, 0.42), (LIFT, 0.24), (AT_PORT, 0.42),
          (SEAT, 0.52), (OFF, 0.36), (40, 0.12), (BACK, 0.14), (FR, 0.14)]
K_CHEST = [(0, 4.0), (SHOT, 2.0), (6, -8.0), (LET_GO, -4.0), (GRAB, 0.0), (LIFT, 0.0), (AT_PORT, 0.0), (SEAT, 2.0),
           (OFF, 0.0), (BACK, 4.0), (FR, 4.0)]
K_LOOK = [(0, S_YAW - 6.0), (SHOT, S_YAW - 4.0), (5, S_YAW - 26.0), (LET_GO, S_YAW - 10.0), (13, R_YAW), (GRAB, R_YAW + 4.0),
          (LIFT, R_YAW - 10.0), (AT_PORT, P_YAW + 4.0), (SEAT, P_YAW + 2.0), (OFF, P_YAW - 4.0), (40, 0.0), (BACK, S_YAW - 6.0),
          (FR, S_YAW - 6.0)]
K_PITCH = [(0, -0.1), (SHOT, -0.05), (5, 0.25), (LET_GO, 0.1), (13, -0.3), (GRAB, -0.5), (LIFT, -0.35), (AT_PORT, -0.45),
           (SEAT, -0.5), (OFF, -0.3), (40, -0.05), (BACK, -0.1), (FR, -0.1)]
_sS = stance(S_XY, S_YAW, *S_STANCE)
_sF = stance((-0.07, 0.27), S_YAW - 4.0, 1.1, 0.06, -0.12)
_sR = stance(L_XY, R_YAW - 10.0, 1.12, 0.08, -0.06)
_sP = stance((0.33, 0.38), P_YAW + 4.0, 1.16, 0.14, -0.12)
_sB = stance((0.15, 0.3), 24.0, 1.05, 0.04, -0.02)
K_FEET = [(0, _sS[0], _sS[1]), (SHOT + 1, _sS[0], _sS[1]), (6, _sF[0], _sF[1]), (LET_GO + 1, _sF[0], _sF[1]),
          (GRAB - 1, _sR[0], _sR[1]), (LIFT, _sR[0], _sR[1]), (AT_PORT, _sP[0], _sP[1]), (OFF + 2, _sP[0], _sP[1]),
          (40, _sB[0], _sB[1]), (BACK, _sS[0], _sS[1]), (FR, _sS[0], _sS[1])]
K_FYAW = [(0, S_YAW), (SHOT + 1, S_YAW), (6, S_YAW - 4.0), (LET_GO + 1, S_YAW - 4.0), (GRAB - 1, R_YAW - 10.0),
          (LIFT, R_YAW - 10.0), (AT_PORT, P_YAW + 4.0), (OFF + 2, P_YAW + 4.0), (40, 24.0), (BACK, S_YAW), (FR, S_YAW)]


def body_at(f):
    return smooth_keys(K_RO, f), smooth_keys(K_YAW, f)


def feet_at(f):
    for (fa, la, ra), (fb, lb, rb) in zip(K_FEET, K_FEET[1:]):
        if fa <= f <= fb:
            k = (f - fa) / float(fb - fa) if fb > fa else 1.0
            kr = ease(min(1.0, k * 2.0))
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


# ---------------------------------------------------------------------------------------------- the attack: hands
def hand_at(side, f):
    """Where his fist is at frame f: (point, R)."""
    ro, yaw = body_at(f)
    hip = hip_fist(side, ro, yaw)
    if side == "L":
        if f <= LET_GO:
            press = 1.0 if PRESS <= f <= SHOT + 1 else 0.0
            g = grip_fist(press, S_YAW)
            if f <= SHOT:
                return g
            # the slam jolts his fist off the grip a little; then he lets go
            k = (f - SHOT) / float(LET_GO - SHOT)
            return blend_hand(g, (g[0] + V(-0.02, 0.05, 0.03), g[1]), ease(k))
        if f < 13:
            k = ease((f - LET_GO) / float(13 - LET_GO))
            g = grip_fist(0.0, S_YAW)
            return blend_hand((g[0] + V(-0.02, 0.05, 0.03), g[1]), hip, k, 0.03)
        if f < BACK - 5:
            return hip
        if f < BACK:
            k = ease((f - (BACK - 5)) / 5.0)
            return blend_hand(hip, grip_fist(0.0, yaw), k, 0.04)
        return grip_fist(0.0, yaw)
    # right hand
    if f <= LET_GO:
        return hip
    M, s, _c = cell_track(max(f, GRAB))
    if f < GRAB:
        k = ease((f - LET_GO) / float(GRAB - LET_GO))
        tgt = cell_fist(rack_x(), body_at(GRAB)[1])
        tgt = (tgt[0] + Z_ * 0.04 * (1.0 - k), tgt[1])
        return blend_hand(hip, tgt, k, 0.06)
    if f <= SEAT + 2:
        return cell_fist(M, yaw if f > LIFT else body_at(GRAB)[1])
    if f < 41:
        k = ease((f - SEAT - 2) / float(41 - SEAT - 2))
        a = cell_fist(seated_x(SEAT + 2), body_at(SEAT + 2)[1])
        return blend_hand(a, hip, k, 0.05)
    return hip


# ---------------------------------------------------------------------------------------------- the attack: pose
def attack_pose(arm, f, rest):
    ro, yaw = body_at(f)
    lf, rf, ll, rl = feet_at(f)
    aims = feet(arm, lf, rf, smooth_keys(K_FYAW, f), lift_l=ll, lift_r=rl)
    torso(aims, yaw, bend=smooth_keys(K_BEND, f), side=0.04, chest=smooth_keys(K_CHEST, f), look=smooth_keys(K_LOOK, f),
          pitch=smooth_keys(K_PITCH, f))
    q = rz(yaw)
    aims.update(mortar_aims(rest, f))
    M, s, c = cell_track(f)
    aims["cell"] = ("world", M @ rest.m["cell"])
    for side in ("R", "L"):
        p, R = hand_at(side, f)
        apply_hand(arm, aims, side, p, R, q @ V(-1.0 if side == "R" else 1.0, 0.35, -0.5))
    if f >= FR:
        s, c = 1.0, 1.0
    return aims, ro, yaw, {"cell": s, "cellcore": sc_across(c), "coils": sc_across(coil_scale(f))}


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
