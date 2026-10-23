"""Missile Launcher clips (game: 24 fps).

Idle   : the launcher at rest, its pod a little elevated; he stands at ease beside it, his left hand resting on the
         control box, the fire-control tablet clipped to his chest; he breathes and looks about, and once lifts his right
         hand to his headset's ear cup and listens, his head cocked, then lets it drop.
Combat : the pod elevated toward the robots; he holds the tablet out before him by its grips, his thumb by the fire key,
         glancing from its screen to the field and back.
Attack : (52 frames, inside the 2.2 s cooldown) his thumb on the fire key and the missile leaves the near upper tube (SHOT,
         frame 3: the game's missile, flash and smoke leave the tube's mouth there): the pod jolts up on its trunnions, the
         pedestal shudders, the tube's blast cover is blown up off the pod's top and slaps back down. He clips the tablet
         back onto his chest; the pod tilts up to its loading angle (its back comes down) while he turns to the crate at
         his right, crouches and lifts out the next missile, carries it across his front round behind the pod, swings its
         nose up into the empty tube's back and shoves it home up the tube with his right palm on its tail (his left hand
         lets go and steadies the pod); he steps back, the pod comes down to its firing angle again and he unclips the
         tablet and holds it out.

The launcher's bones are posed directly: mount (the pedestal's shudder), pod (elevating about the trunnions, with its
kick), cover (on its hinge). The missile, the tablet and the crate are free bones posed in the world; the missile's
scale hides it from the shot until he takes the next one from the crate."""
import math
from mathutils import Vector, Quaternion, Matrix
import missile as mm
from rig import Poser, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease
from anim_cannon import rz, fwd, rgt, body_pt, wroot, smooth_keys, xform, perp, feet, torso, grip_r, grip_l
from anim_field_gun import fist_rot, palm_rot, hip_fist, body_matrix, blend_m, stance, palm_to_fist

FPS = 24
J = mm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
X_, Z_ = V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0)

TRUN = vec(mm.TRUN)
GD0, GU0, GX0 = vec(mm.GD), vec(mm.GU), V(1.0, 0.0, 0.0)
MOUNT_C = V(mm.MX, mm.BASE_Y, 0.0)
HINGE = vec(mm.hinge_pt(mm.FIRE))
TAIL0 = vec(mm.seated_tail(mm.FIRE))
MSL_L, MSL_R = mm.MSL_L, mm.MSL_R
MSL_MID = TAIL0 + GD0 * (MSL_L * 0.5)
_C, _X, _U, _N = mm.tablet_frame()
TB_C, TB_X, TB_U, TB_N = vec(_C), vec(_X), vec(_U), vec(_N)
CB_TOP = vec(mm.CB_C) + V(0.0, 0.05, mm.CB_HALF[2] + 0.004)       # (toward the box's back edge)
CRATE_TAIL = vec(mm.crate_tail(0))
CRATE_A = vec(mm.MSL_BOX_A)
POD_TOP = vec(mm.bpt(mm.POD_B + 0.08, 0.06, mm.POD_HH + 0.004))    # (rest) where his left palm steadies the pod
EL0 = math.degrees(mm.ELEV0)

# ---------------------------------------------------------------------------------------------- timing (24 fps)
PRESS = 2          # his thumb comes down on the fire key
SHOT = 3           # the missile leaves the tube (game: missile, flash, smoke at the mouth); the pod kicks
STOW0, STOW1 = 5, 10        # the tablet back onto his chest
LOWER0, LOWER1 = 6, 17      # the pod tilts up to its loading angle
GRAB = 15          # his hands on the missile in the crate
LIFT = 19          # lifted out (his right hand comes under it)
WALK = 24          # carried round behind the pod
AT_TUBE = 28       # its nose at the empty tube's back
LET_L = 30         # his left hand lets go and steadies the pod's top
HOME = 35          # pushed home (its tail flush with the pod's back)
OFF = 40           # both hands off: at his hips
RAISE0, RAISE1 = 38, 46     # the pod comes down to its firing angle
TAKE0, TAKE1 = 44, 50       # he unclips the tablet and holds it out
FR = 52            # = the 2.2 s cooldown (52.8 frames)

EL_IDLE = 10.0     # the pod's elevation (degrees): at rest ...
EL_C = 26.0        # ... in Combat and firing ...
EL_L = 38.0        # ... loading (tilted up: its back comes down to him)
KICK = 3.2         # the kick at the shot (degrees, nose up)


# ---------------------------------------------------------------------------------------------- the launcher
def kick(f):
    if f < SHOT:
        return 0.0
    t = f - SHOT
    if t <= 1.0:
        return KICK * t
    if t <= 5.0:
        return KICK * (1.0 - ease((t - 1.0) / 4.0))
    if t <= 8.0:
        return -0.5 * math.sin(math.pi * (t - 5.0) / 3.0)
    return 0.0


def shudder(f):
    """The pedestal's shudder at the shot: (shove back (m), rock (degrees))."""
    if f < SHOT:
        return 0.0, 0.0
    t = f - SHOT
    if t > 9:
        return 0.0, 0.0
    a = math.exp(-t / 2.5)
    return 0.012 * a * math.cos(t * 1.7), 0.7 * a * math.sin(t * 2.1 + 0.6)


def m_mount(f):
    sh, rk = shudder(f)
    pv = MOUNT_C + V(0.0, 0.25, 0.0)            # it rocks about the back edge of its base plate
    return (Matrix.Translation(V(0.0, sh, 0.0)) @ Matrix.Translation(pv) @ Matrix.Rotation(math.radians(rk), 4, "X")
            @ Matrix.Translation(-pv))


def m_pod(f, el):
    """The pod's rigid motion (rest -> posed) at elevation el (degrees) plus the kick at frame f."""
    d = math.radians(el + kick(f) - EL0)
    return m_mount(f) @ Matrix.Translation(TRUN) @ Matrix.Rotation(-d, 4, "X") @ Matrix.Translation(-TRUN)   # (nose up)


def m_cover(Mp, flap):
    """The firing tube's cover: `flap` degrees up off its rest (lying open on the pod's top), about its hinge."""
    return Mp @ Matrix.Translation(HINGE) @ Matrix.Rotation(math.radians(flap), 4, "X") @ Matrix.Translation(-HINGE)


class Rest:
    def __init__(self, arm):
        b = arm.data.bones
        self.m = {n: b[n].matrix_local.copy() for n in ("mount", "pod", "cover", "missile", "tablet", "props", "chest",
                                                        "hand.R", "hand.L")}
        self.inv = {n: m.inverted() for n, m in self.m.items()}


def launcher_aims(rest, f, el, flap=0.0):
    Mm, Mp = m_mount(f), m_pod(f, el)
    return {"mount": ("world", Mm @ rest.m["mount"]), "pod": ("world", Mp @ rest.m["pod"]),
            "cover": ("world", m_cover(Mp, flap) @ rest.m["cover"]), "props": ("world", rest.m["props"])}, Mp


# ---------------------------------------------------------------------------------------------- the tablet
def tablet_on_chest(rest):
    return lambda P, base: ("world", P["chest"] @ rest.inv["chest"] @ rest.m["tablet"])


def tablet_held(ro, yaw, br=0.0, look_down=0.0):
    """The tablet held out before his chest, its screen tilted up toward his face, its top edge away from him (rest ->
    posed): its +X side (the fire key) is then at his right."""
    q = rz(yaw)
    c = body_pt(V(0.0, -0.4, 1.1 + 0.004 * br), ro, yaw)
    a = math.radians(36.0 + 10.0 * look_down)          # the screen's tilt from facing straight up, toward his face
    N = q @ V(0.0, math.sin(a), math.cos(a))
    U = q @ V(0.0, -math.cos(a), math.sin(a))
    R = frame_map(TB_N, N, TB_U, U)
    M = R.to_4x4()
    M.translation = c - R @ TB_C
    return M


def tablet_grips(M, press=0.0):
    """His fists round the tablet's grip bars (placement M), knuckles out: {side: (fist, R)}; the right thumb comes down on
    the fire key (press)."""
    R3 = M.to_3x3()
    u, x, n = (R3 @ TB_U).normalized(), (R3 @ TB_X).normalized(), (R3 @ TB_N).normalized()
    gr = M @ (TB_C + TB_X * mm.TB_HANDLE) - n * 0.006 * press
    gl = M @ (TB_C - TB_X * mm.TB_HANDLE)
    return {"R": (gr, fist_rot("R", u, x * 0.8 - n * 0.6)), "L": (gl, fist_rot("L", u, -x * 0.8 - n * 0.6))}


def apply_hand(arm, aims, side, fist, R, pole):
    aims.update((grip_r if side == "R" else grip_l)(arm, fist, R, pole=pole))


def blend_hand(a, b, k, lift=0.0):
    (pa, Ra), (pb, Rb) = a, b
    p = pa.lerp(pb, k) + Z_ * (lift * math.sin(math.pi * k))
    return p, Ra.to_quaternion().slerp(Rb.to_quaternion(), k).to_matrix()


# ---------------------------------------------------------------------------------------------- stations
S_XY, S_YAW = (0.06, 0.12), 10.0             # Combat: behind and left of the pod, the tablet held out
I_XY, I_YAW = (0.19, -0.08), 34.0            # Idle: at ease by the control box
C_XY, C_YAW = (0.02, 0.1), -90.0             # at the crate (facing it: -X)
L0_XY, L1_XY, L_YAW = (0.64, 0.45), (0.63, 0.2), 4.0     # loading: behind the pod's near upper tube, facing forward
S_STANCE = (1.08, 0.08, -0.04)


def combat_body(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    yaw = S_YAW + 1.2 * math.sin(w)
    ro = wroot(S_XY[0], S_XY[1], ROOT.z - 0.03 + 0.004 * br)
    lf, rf = stance(S_XY, S_YAW, *S_STANCE)
    aims = feet(arm, lf, rf, S_YAW)
    up = 0.5 + 0.5 * math.sin(w - 0.8)               # glancing from the screen to the field and back
    look = yaw - 4.0 + 8.0 * math.sin(w * 2.0) * up
    torso(aims, yaw, bend=0.08, side=0.02, chest=2.0, look=look, pitch=-0.42 + 0.4 * up, br=br)
    return aims, ro, yaw, br, up


def combat_pose(arm, t, rest):
    aims, ro, yaw, br, up = combat_body(arm, t)
    g, Mp = launcher_aims(rest, 0, EL_C + 0.35 * math.sin(2 * math.pi * t))
    aims.update(g)
    M = tablet_held(ro, yaw, br, look_down=1.0 - up)
    aims["tablet"] = ("world", M @ rest.m["tablet"])
    q = rz(yaw)
    for side, (p, R) in tablet_grips(M).items():
        apply_hand(arm, aims, side, p, R, q @ V(-1.0 if side == "R" else 1.0, 0.5, -0.6))
    aims["missile"] = ("world", Mp @ rest.m["missile"])
    return aims, ro, yaw, {"missile": 1.0}


def idle_pose(arm, t, rest):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    radio = math.sin(math.pi * min(1.0, max(0.0, (t - 0.38) / 0.3))) ** 2 if 0.38 < t < 0.68 else 0.0
    yaw = I_YAW + 2.5 * math.sin(w)
    ro = wroot(I_XY[0] + 0.008 * math.sin(w), I_XY[1], ROOT.z - 0.012 + 0.005 * br)
    lf, rf = stance(I_XY, I_YAW, 1.06, 0.02, 0.02)
    aims = feet(arm, lf, rf, I_YAW)
    look = yaw - 10.0 + (1.0 - radio) * (26.0 * math.sin(w) + 8.0 * math.sin(w * 3)) + 10.0 * radio
    torso(aims, yaw, bend=0.03, side=0.03 * math.sin(w), chest=-4.0 + 2.0 * math.sin(w), look=look,
          pitch=0.04 + 0.03 * br - 0.14 * radio, br=br, tilt_head=-0.14 * radio)
    q = rz(yaw)
    g, Mp = launcher_aims(rest, 0, EL_IDLE)
    aims.update(g)
    aims["tablet"] = tablet_on_chest(rest)
    aims["missile"] = ("world", Mp @ rest.m["missile"])
    # his left hand resting on the control box's top
    top = CB_TOP + V(0.0, 0.0, 0.004 * br)
    Rl = palm_rot("L", V(0.0, 0.0, -1.0), q @ V(0.3, -1.0, 0.0))
    apply_hand(arm, aims, "L", palm_to_fist("L", top, Rl), Rl, q @ V(1.0, 0.6, -0.2))
    # his right fist on his hip; lifted to the headset's right cup now and then
    hip = hip_fist("R", ro, yaw)
    if radio > 0.0:
        cup = body_pt(mm.hp((-mm.CUP_C[0] - 0.06, mm.CUP_C[1] - 0.01, mm.CUP_C[2] - 0.005)), ro, yaw)
        Rc = palm_rot("R", q @ V(1.0, 0.0, 0.0), Z_ + q @ V(0.0, -0.4, 0.0))
        p, R = blend_hand(hip, (palm_to_fist("R", cup, Rc), Rc), radio)
        apply_hand(arm, aims, "R", p, R, q @ V(-1.0, 0.3, -0.7))
    else:
        apply_hand(arm, aims, "R", hip[0], hip[1], q @ V(-1.0, 0.5, 0.1))
    return aims, ro, yaw, {"missile": 1.0}


def _const(act):
    from anim_ugo import key_constant
    key_constant(act, 'pose.bones["missile"].scale')


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


# ---------------------------------------------------------------------------------------------- the attack: the pod
def elev(f):
    if f <= LOWER0:
        return EL_C
    if f <= LOWER1:
        return lerp(EL_C, EL_L, ease((f - LOWER0) / float(LOWER1 - LOWER0)))
    if f <= RAISE0:
        return EL_L
    if f <= RAISE1:
        return lerp(EL_L, EL_C, ease((f - RAISE0) / float(RAISE1 - RAISE0)))
    return EL_C


def flap(f):
    """The fired tube's cover: blown up off the pod's top by the launch (degrees), slapping back and bouncing."""
    if f < SHOT:
        return 0.0
    t = f - SHOT
    if t <= 2.0:
        return 78.0 * ease(t / 2.0)
    if t <= 6.0:
        return 78.0 * (1.0 - ((t - 2.0) / 4.0) ** 2)
    if t <= 13.0:
        return 14.0 * math.exp(-(t - 6.0) / 2.2) * abs(math.sin(math.pi * (t - 6.0) / 3.5))
    return 0.0


# ---------------------------------------------------------------------------------------------- the attack: body tracks
def _r(xy, z=0.0):
    return wroot(xy[0], xy[1], ROOT.z + z)


K_RO = [(0, _r(S_XY, -0.03)), (SHOT, _r((0.06, 0.135), -0.035)), (STOW1, _r((0.08, 0.07), -0.08)),
        (GRAB, _r(C_XY, -0.3)), (LIFT, _r((0.08, 0.12), -0.08)), (WALK, _r((0.42, 0.44), -0.06)), (AT_TUBE, _r(L0_XY, -0.14)),
        (HOME, _r(L1_XY, -0.06)), (OFF, _r((0.45, 0.28), -0.04)), (TAKE0, _r((0.2, 0.08), -0.03)), (FR, _r(S_XY, -0.03))]
K_YAW = [(0, S_YAW), (SHOT, S_YAW - 1.0), (STOW1, -40.0), (GRAB, C_YAW), (LIFT, C_YAW + 8.0), (WALK, -30.0),
         (AT_TUBE, L_YAW), (HOME, L_YAW + 2.0), (OFF, 10.0), (TAKE0, 16.0), (FR, S_YAW)]
K_BEND = [(0, 0.08), (SHOT, 0.06), (STOW1, 0.25), (GRAB, 0.75), (LIFT, 0.2), (WALK, 0.15), (AT_TUBE, 0.46),
          (HOME, 0.22), (OFF, 0.12), (TAKE0, 0.08), (FR, 0.08)]
K_CHEST = [(0, 2.0), (SHOT, 0.0), (STOW1, -6.0), (GRAB, 0.0), (LIFT, 0.0), (AT_TUBE, 0.0), (HOME, 4.0), (OFF, 0.0),
           (FR, 2.0)]
K_LOOK = [(0, S_YAW - 4.0), (SHOT, S_YAW - 2.0), (5, S_YAW + 6.0), (STOW1, -60.0), (GRAB, C_YAW), (LIFT, C_YAW + 20.0),
          (WALK, -20.0), (AT_TUBE, L_YAW + 6.0), (HOME, L_YAW + 4.0), (OFF, 20.0), (TAKE0, 14.0), (FR, S_YAW - 4.0)]
K_PITCH = [(0, -0.42), (SHOT, -0.36), (5, 0.1), (STOW1, -0.35), (GRAB, -0.5), (LIFT, -0.25), (WALK, -0.1),
           (AT_TUBE, -0.25), (HOME, -0.3), (OFF, 0.0), (TAKE0, -0.4), (FR, -0.42)]
_sS = stance(S_XY, S_YAW, *S_STANCE)
_sC = stance(C_XY, C_YAW, 1.2, 0.1, -0.06)
_sW = stance((0.42, 0.44), -30.0, 1.0, 0.06, -0.04)
_sL0 = stance(L0_XY, L_YAW, 1.12, 0.16, -0.14)
_sL1 = stance(L1_XY, L_YAW, 1.05, 0.14, -0.12)
_sB = stance((0.45, 0.3), 10.0, 1.05, 0.0, 0.0)
K_FEET = [(0, _sS[0], _sS[1]), (SHOT + 2, _sS[0], _sS[1]), (GRAB, _sC[0], _sC[1]), (LIFT, _sC[0], _sC[1]), (WALK, _sW[0], _sW[1]),
          (AT_TUBE, _sL0[0], _sL0[1]), (HOME, _sL1[0], _sL1[1]), (HOME + 2, _sL1[0], _sL1[1]), (OFF, _sB[0], _sB[1]),
          (FR, _sS[0], _sS[1])]
K_FYAW = [(0, S_YAW), (SHOT + 2, S_YAW), (GRAB, C_YAW), (LIFT, C_YAW), (WALK, -30.0), (AT_TUBE, L_YAW), (HOME + 2, L_YAW),
          (OFF, 10.0), (FR, S_YAW)]


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


# ---------------------------------------------------------------------------------------------- the attack: the missile
def in_tube(Mp, travel):
    """The missile on the fired tube's axis, `travel` short of seated (0 = home), rest -> posed."""
    return Mp @ Matrix.Translation(-GD0 * travel)


def crate_x():
    """The next missile in its cradle (rest -> posed)."""
    return xform(TAIL0, GD0, GU0, CRATE_TAIL, CRATE_A, Z_)


def carry_x(ro, yaw):
    """Carried level across his front at his belly, its nose to his left."""
    A = rz(yaw) @ V(1.0, 0.0, 0.0)
    mid = body_pt(V(0.04, -0.42, 0.97), ro, yaw)
    return xform(MSL_MID, GD0, GU0, mid, A, Z_)


def missile_track(f):
    """('tube', travel) in the pod, ('hidden',) or ('free', placement)."""
    if f < SHOT:
        return ("tube", 0.0)
    if f < GRAB:
        return ("hidden",)
    if f <= LIFT:
        k = ease((f - GRAB) / float(LIFT - GRAB))
        ro, yaw = body_at(f)
        return ("free", Matrix.Translation(Z_ * 0.06 * math.sin(math.pi * k)) @ blend_m(crate_x(), carry_x(ro, yaw), k, MSL_MID))
    if f <= WALK:
        ro, yaw = body_at(f)
        return ("free", carry_x(ro, yaw))
    if f <= AT_TUBE:
        k = ease((f - WALK) / float(AT_TUBE - WALK))
        ro, yaw = body_at(f)
        return ("free", blend_m(carry_x(ro, yaw), in_tube(m_pod(AT_TUBE, EL_L), MSL_L), k, MSL_MID))
    if f <= HOME:
        k = ease((f - AT_TUBE) / float(HOME - AT_TUBE))
        return ("tube", MSL_L * (1.0 - k))
    return ("tube", 0.0)


HOLD_T = 0.08          # his right hand on top near the tail (from the tail, along the missile) ...
HOLD_F = 0.33          # ... his left hand toward its nose: on top in the crate, under it once lifted


def missile_hand(X, side, under=0.0, yaw=0.0):
    """A hand on the missile (placement X) as a fist: (point, R). Right: on top near its tail, or (side 'push') flat on
    its tail's end; left: at HOLD_F, from on top (under 0) round its near side to under it (under 1)."""
    A = (X.to_3x3() @ GD0).normalized()
    tail = X @ TAIL0
    up = perp(Z_, A)
    near = perp(-fwd(yaw), A)
    if side == "push":
        c = tail - A * 0.018
        R = palm_rot("R", A, up - near * 0.3)
        return palm_to_fist("R", c, R), R
    if side == "R":
        c = tail + A * HOLD_T + up * (MSL_R + 0.014)
        R = palm_rot("R", -up, near + A * 0.3)
        return palm_to_fist("R", c, R), R
    phi = math.pi * under
    d = up * math.cos(phi) + near * math.sin(phi)
    c = tail + A * HOLD_F + d * (MSL_R + 0.014)
    R = palm_rot("L", -d, d.cross(A))
    return palm_to_fist("L", c, R), R


def missile_x(f):
    mt = missile_track(f)
    if mt[0] == "tube":
        return in_tube(m_pod(f, elev(f)), mt[1]), 1.0
    if mt[0] == "hidden":
        return m_pod(f, elev(f)), 0.0
    return mt[1], 1.0


# ---------------------------------------------------------------------------------------------- the attack: hands
def stowed_grips(f):
    """The tablet's grips while it rides his chest (near enough: his body's turn and shift)."""
    ro, yaw = body_at(f)
    return tablet_grips(body_matrix(ro, yaw))


def held_grips(f, press=0.0):
    ro, yaw = body_at(f)
    if f <= STOW0:
        ro, yaw = body_at(min(f, STOW0))
    return tablet_grips(tablet_held(ro, yaw, look_down=0.8), press)


def tablet_x(f):
    """The tablet (rest -> posed): held, on its way to his chest and back, or None while it rides his chest."""
    ro, yaw = body_at(f)
    if f <= STOW0:
        return tablet_held(ro, yaw, look_down=0.8)
    if f < STOW1:
        k = ease((f - STOW0) / float(STOW1 - STOW0))
        Mh = tablet_held(*body_at(STOW0), look_down=0.8)
        return Matrix.Translation(Z_ * 0.04 * math.sin(math.pi * k)) @ blend_m(Mh, body_matrix(ro, yaw), k, TB_C)
    if f < TAKE0:
        return None
    k = ease((f - TAKE0) / float(TAKE1 - TAKE0)) if f < TAKE1 else 1.0
    return Matrix.Translation(Z_ * 0.04 * math.sin(math.pi * k)) @ blend_m(body_matrix(ro, yaw), tablet_held(ro, yaw, look_down=0.6), k, TB_C)


def hand_at(side, f):
    """Where his fist is at frame f: (point, R)."""
    ro, yaw = body_at(f)
    hip = hip_fist(side, ro, yaw)
    if f <= STOW0 or f >= TAKE0:
        M = tablet_x(f)
        press = 1.0 if PRESS <= f <= SHOT + 1 else 0.0
        return tablet_grips(M, press)[side]
    if f < STOW1:
        return tablet_grips(tablet_x(f))[side]
    if f < GRAB:                                         # from the stowed tablet to the missile in the crate
        k = ease((f - STOW1) / float(GRAB - STOW1))
        a = stowed_grips(STOW1)[side]
        b = missile_hand(crate_x(), side, 0.0, body_at(GRAB)[1])
        b = (b[0] + Z_ * 0.03 * (1.0 - k), b[1])
        return blend_hand(a, b, k, 0.06)
    X, _ = missile_x(f)
    if side == "L":
        if f <= LET_L:
            under = ease(min(1.0, max(0.0, (f - GRAB) / float(LIFT + 1 - GRAB))))
            return missile_hand(X, "L", under, yaw)
        Mp = m_pod(f, elev(f))
        Rt = palm_rot("L", Mp.to_3x3() @ -GU0, rz(yaw) @ V(-0.2, -1.0, 0.0))
        on_pod = (palm_to_fist("L", Mp @ POD_TOP, Rt), Rt)
        if f <= LET_L + 3:
            k = ease((f - LET_L) / 3.0)
            X0, _ = missile_x(LET_L)
            return blend_hand(missile_hand(X0, "L", 1.0, body_at(LET_L)[1]), on_pod, k, 0.06)
        if f <= HOME + 1:
            return on_pod
        if f < OFF:
            k = ease((f - HOME - 1) / float(OFF - HOME - 1))
            Mp1 = m_pod(HOME + 1, elev(HOME + 1))
            Rt1 = palm_rot("L", Mp1.to_3x3() @ -GU0, rz(body_at(HOME + 1)[1]) @ V(-0.2, -1.0, 0.0))
            return blend_hand((palm_to_fist("L", Mp1 @ POD_TOP, Rt1), Rt1), hip, k, 0.05)
    else:
        if f <= AT_TUBE + 2:
            return missile_hand(X, "R", 0.0, yaw)
        if f <= AT_TUBE + 4:
            k = ease((f - AT_TUBE - 2) / 2.0)
            return blend_hand(missile_hand(X, "R", 0.0, yaw), missile_hand(X, "push", 0.0, yaw), k)
        if f <= HOME:
            return missile_hand(X, "push", 0.0, yaw)
        if f < OFF:
            k = ease((f - HOME) / float(OFF - HOME))
            Xh, _ = missile_x(HOME)
            return blend_hand(missile_hand(Xh, "push", 0.0, body_at(HOME)[1]), hip, k, 0.05)
    if f < TAKE0 - 4:
        return hip
    k = ease((f - (TAKE0 - 4)) / 4.0)                      # reaching for the tablet on his chest
    return blend_hand(hip, stowed_grips(TAKE0)[side], k)


# ---------------------------------------------------------------------------------------------- the attack: pose
def attack_pose(arm, f, rest):
    ro, yaw = body_at(f)
    lf, rf, ll, rl = feet_at(f)
    aims = feet(arm, lf, rf, smooth_keys(K_FYAW, f), lift_l=ll, lift_r=rl)
    torso(aims, yaw, bend=smooth_keys(K_BEND, f), side=0.03, chest=smooth_keys(K_CHEST, f), look=smooth_keys(K_LOOK, f),
          pitch=smooth_keys(K_PITCH, f))
    q = rz(yaw)
    g, Mp = launcher_aims(rest, f, elev(f), flap(f))
    aims.update(g)
    X, s = missile_x(f)
    aims["missile"] = ("world", X @ rest.m["missile"])
    Mt = tablet_x(f)
    aims["tablet"] = ("world", Mt @ rest.m["tablet"]) if Mt is not None else tablet_on_chest(rest)
    for side in ("R", "L"):
        p, R = hand_at(side, f)
        apply_hand(arm, aims, side, p, R, q @ V(-1.0 if side == "R" else 1.0, 0.35, -0.5))
    return aims, ro, yaw, {"missile": 1.0 if f >= FR else s}


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
