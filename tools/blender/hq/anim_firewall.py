"""Firewall clips (game: 24 fps).

Idle   : the rig idling (the node pulsing softly); he types at an easy pace, his eyes on the laptop's screen, stops to
         lift his head and scan the field from left to right, goes back to the keys with a small nod at what he reads,
         and glances up over his left shoulder at the emitter ring.
Combat : both hands on the keyboard, typing lightly, his head up, watching the robots over the laptop.
Attack : (33 frames, inside the 1.4 s cooldown) a burst of typing (frames 0-6: both hands hammering the keys, his head
         down to the screen, the node swelling and flickering, the mast humming); he lifts his right hand high and slams
         the Enter key: the pulse goes out at PULSE (frame 10, the hand held on the key to 13: the game draws the hack
         pulse from the node there); the node flares, a ring of amber light flashes out round the emitters (`flare`),
         the mast shudders and rings down; he lifts his head to watch it go, brings his right hand back to the keys and
         settles into the Combat pose.

The machine never moves (`machine`); the mast wobbles about its foot ("rot" aims), the node (`core`) and the flare ring
(`flare`) scale. His hands are placed with "frame" aims over the keys (palms down, the fingers toward the keyboard's far
edge, the thumbs toward each other)."""
import math
from mathutils import Vector, Quaternion, Matrix
import firewall as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease
from anim_emp import rz, body_pt, smooth_keys, perp, feet, torso

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

_wrR, _fR, _nR, _tR = cm.hand_frame("R")
WR_R, T_R, F_R, N_R = vec(_wrR), vec(_tR), vec(_fR), vec(_nR)
PALM_R = vec(cm.fist_center("R"))
_wrL, _fL, _nL, _tL = cm.hand_frame("L")
WR_L, T_L, F_L, N_L = vec(_wrL), vec(_tL), vec(_fL), vec(_nL)
PALM_L = vec(cm.fist_center("L"))

SW = vec(cm.SW)                               # across the keyboard (+ his left)
CU = vec(cm.CON_U)                            # toward him
KB = vec(cm.KB_C)
ENTER = vec(cm.ENTER_C)
UP = V(0.0, 0.0, 1.0)
SCREEN = vec(cm.lid_frame()[0] + cm.lid_frame()[1] * 0.1)
RING = vec(cm.CORE_C)

# ---------------------------------------------------------------------------------------------- timing (24 fps)
PULSE = 10         # game.gd ATTACK_FRAME: his hand hits Enter, the pulse goes out (held on the key to frame 13)
FR = 33            # <= 1.4 s
HIDE = 0.001       # the flare ring's scale when it is not flashing

HOVER = 0.036      # the palms' middle over the keys' tops
KEY_L = KB + SW * 0.075 - CU * 0.005 + UP * HOVER       # the hands' home on the keys
KEY_R = KB - SW * 0.07 - CU * 0.005 + UP * HOVER
ENTER_P = ENTER + UP * 0.03                              # his right palm on the Enter key (pressed)


def hand_aims(arm, side, palm, finger, pole):
    """A hand (its palm's middle) at `palm`, palm down, the fingers toward `finger`, the thumb toward the other hand."""
    T0, F0, W0, C0 = (T_R, F_R, WR_R, PALM_R) if side == "R" else (T_L, F_L, WR_L, PALM_L)
    t = SW if side == "R" else -SW
    t = perp(t, Vector(finger).normalized())
    R = frame_map(T0, t, F0, perp(finger, t))
    aims = arm_aims(arm, side, palm - R @ (C0 - W0), pole=pole)
    aims["hand." + side] = ("frame", T0, R @ T0, F0, R @ F0)
    return aims


FINGER = (-CU * 0.95 - UP * 0.22).normalized()          # the fingers' line over the keys


def hands(arm, yaw, tl=(0.0, 0.0, 0.0), tr=(0.0, 0.0, 0.0), right=None, rfinger=None):
    """Both hands on the keys; tl/tr: (up, across, toward the far edge) offsets for the typing; `right` overrides the
    right palm's place (the reach for Enter), `rfinger` its fingers' line."""
    q = rz(yaw)
    pl = KEY_L + UP * tl[0] + SW * tl[1] - CU * tl[2]
    pr = (KEY_R + UP * tr[0] + SW * tr[1] - CU * tr[2]) if right is None else right
    aims = {}
    aims.update(hand_aims(arm, "L", pl, (FINGER + SW * 0.12).normalized(), q @ V(1.0, 0.7, -0.35)))
    aims.update(hand_aims(arm, "R", pr, rfinger if rfinger is not None else (FINGER - SW * 0.12).normalized(), q @ V(-1.0, 0.7, -0.35)))
    return aims


def tap(f, rate, phase, amp):
    """A key-tapping bob: quick dips (the hand comes down on a key), resting high between them."""
    s = math.sin(2 * math.pi * (f * rate + phase))
    return amp * (0.5 + 0.5 * max(-1.0, min(1.0, s * 1.6)))


def typing(f, rate=0.11, amp=0.01, roam=0.012):
    """Both hands' offsets while typing: bobs out of step, a little drift across and over the keys."""
    tl = (tap(f, rate, 0.0, amp), roam * math.sin(f * 0.21), roam * 0.6 * math.sin(f * 0.13 + 1.0))
    tr = (tap(f, rate * 1.13, 0.45, amp), roam * math.sin(f * 0.17 + 2.0), roam * 0.6 * math.sin(f * 0.11 + 0.4))
    return tl, tr


# ---------------------------------------------------------------------------------------------- the machine
def machine_aims(aims, wobble=(0.0, 0.0)):
    q = Quaternion((1, 0, 0), math.radians(wobble[0])) @ Quaternion((0, 1, 0), math.radians(wobble[1]))
    aims["mast"] = ("rot", q)


def machine_scales(node=1.0, flare=HIDE):
    return {"core": node, "flare": max(HIDE, flare)}


# ---------------------------------------------------------------------------------------------- stance
YAW0 = math.degrees(math.atan2(-float(CU[0]), float(CU[1])))     # facing the keyboard (about -31 deg)
C_YAW = YAW0 + 3.0
C_RO = V(0.0, -0.012, -0.03)


def stance_feet(arm, yaw):
    q = rz(yaw)
    lf = q @ V(0.17, 0.05, 0.0)
    rf = q @ V(-0.19, 0.09, 0.0)
    return feet(arm, (lf.x, lf.y), (rf.x, rf.y), yaw)


def look_at(p, ro, yaw):
    """(heading in degrees, pitch) for his head to look at world point p."""
    eye = body_pt(cm.hp((0.0, -0.12, 1.68)), ro, yaw)
    d = vec(p) - eye
    head = math.degrees(math.atan2(-d.x, -d.y))
    pitch = math.atan2(d.z, math.hypot(d.x, d.y))
    return head, pitch


FIELD = V(-0.6, -3.0, 0.3)                    # where he watches the robots


# ---------------------------------------------------------------------------------------------- idle
def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br = math.sin(w * 3)
        scan = smooth_keys([(0.0, 0.0), (0.3, 0.0), (0.36, 1.0), (0.5, 1.0), (0.56, 0.0), (1.0, 0.0)], t)
        up = smooth_keys([(0.0, 0.0), (0.8, 0.0), (0.86, 1.0), (0.93, 1.0), (0.98, 0.0), (1.0, 0.0)], t)
        pause = max(scan, up)
        nod = 0.07 * math.sin(math.pi * min(1.0, max(0.0, (t - 0.64) / 0.07))) if 0.64 < t < 0.71 else 0.0
        yaw = YAW0 + 2.0 * math.sin(w) + 4.0 * up
        ro = C_RO + V(0.0, 0.0, 0.004 * br) + V(0.0, 0.01, 0.01) * pause
        aims = stance_feet(arm, YAW0)
        hs, ps = look_at(SCREEN, ro, yaw)
        hf, pf = look_at(FIELD, ro, yaw)
        hr_, pr_ = look_at(RING, ro, yaw)
        sweep = 22.0 * math.sin(math.pi * (t - 0.36) / 0.14) if 0.36 < t < 0.5 else 0.0
        look = hs + (hf + sweep - hs) * scan + (hr_ - hs) * up
        pitch = ps + (pf - ps) * scan + (min(pr_, 0.9) - ps) * up
        torso(aims, yaw, bend=0.2 - 0.08 * pause + 0.01 * br, side=-0.02, chest=-2.0 + 6.0 * up, look=look,
              pitch=pitch * 0.9 - nod + 0.015 * br, tilt=0.04 - 0.04 * up, shrug=0.02 * br + 0.04 * up)
        k = 1.0 - pause
        tl, tr = typing(f, rate=0.09, amp=0.009 * k, roam=0.01 * k)
        tl = (tl[0] + 0.02 * pause, tl[1], tl[2] - 0.015 * pause)
        tr = (tr[0] + 0.02 * pause, tr[1], tr[2] - 0.015 * pause)
        aims.update(hands(arm, yaw, tl, tr))
        machine_aims(aims)
        sc = machine_scales(node=1.0 + 0.04 * math.sin(w * 4))
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- combat
def combat_pose(arm, f, br=0.0, sw=0.0):
    yaw = C_YAW + 1.5 * sw
    ro = C_RO + V(0.0, 0.0, 0.005 * br)
    aims = stance_feet(arm, YAW0)
    hf, pf = look_at(FIELD, ro, yaw)
    torso(aims, yaw, bend=0.17 + 0.01 * br, side=-0.03, chest=-3.0, look=hf + 4.0 * sw, pitch=pf + 0.04, tilt=0.05)
    return aims, ro, yaw


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br, sw = math.sin(w * 2), math.sin(w)
        aims, ro, yaw = combat_pose(arm, f, br, sw)
        tl, tr = typing(f, rate=0.1, amp=0.006, roam=0.006)
        # (the loop must close: fade the typing's phase in and out over the loop)
        e = math.sin(math.pi * t)
        tl = tuple(x * e for x in tl)
        tr = tuple(x * e for x in tr)
        aims.update(hands(arm, yaw, tl, tr))
        machine_aims(aims)
        sc = machine_scales(node=1.0 + 0.05 * math.sin(w * 2))
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- attack
D = PULSE
# his right palm: typing (0-5), up high (8), down onto Enter (D), held (to D + 3), lifted off and back to the keys
K_RH = [(0, 0.0), (5, 0.0), (6, 0.14), (7, 0.34), (8, 0.4), (9, 0.24), (D, 0.0), (D + 3, 0.0), (D + 6, 0.1), (D + 11, 0.03), (FR, 0.0)]
K_RX = [(0, 0.0), (5, 0.0), (8, 1.0), (D + 3, 1.0), (D + 9, 0.4), (D + 14, 0.0), (FR, 0.0)]     # on its way to Enter
K_TYPE = [(0, 1.0), (5, 1.0), (7, 0.0), (D + 12, 0.0), (FR - 4, 0.3), (FR, 0.0)]                # the burst of typing
K_NODE = [(0, 1.0), (6, 1.22), (D - 1, 1.28), (D, 1.9), (D + 1, 1.7), (D + 3, 0.8), (D + 8, 0.85), (FR, 1.0)]
K_FLARE = [(0, 0.0), (D - 1, 0.0), (D, 1.0), (D + 2, 1.22), (D + 4, 1.38), (D + 6, 1.48), (D + 7, 0.0), (FR, 0.0)]
K_RO = [(0, C_RO), (5, C_RO + V(0.0, -0.012, -0.012)), (8, C_RO + V(0.006, 0.01, 0.02)), (D, C_RO + V(-0.012, -0.02, -0.035)),
        (D + 2, C_RO + V(-0.012, -0.018, -0.04)), (D + 7, C_RO + V(0.008, 0.016, -0.01)), (D + 13, C_RO), (FR, C_RO)]
K_YAW = [(0, C_YAW), (5, C_YAW - 2.0), (8, C_YAW + 4.0), (D, C_YAW - 5.0), (D + 5, C_YAW + 2.0), (24, C_YAW - 1.0), (FR, C_YAW)]
K_BEND = [(0, 0.17), (4, 0.26), (6, 0.2), (8, 0.06), (D, 0.32), (D + 2, 0.3), (D + 6, 0.13), (D + 12, 0.17), (FR, 0.17)]
K_SCREEN = [(0, 0.0), (2, 1.0), (6, 1.0), (8, 0.6), (D, 0.85), (D + 2, 0.7), (D + 6, 0.0), (FR, 0.0)]    # eyes on the screen
K_TILT = [(0, 0.05), (5, 0.0), (8, -0.04), (D + 1, 0.1), (D + 6, 0.02), (FR, 0.05)]
K_SHRUG = [(0, 0.0), (4, 0.06), (8, 0.14), (D, 0.0), (D + 2, 0.16), (D + 6, 0.04), (FR, 0.0)]
K_LIFT = [(0, 0.0), (D + 3, 0.0), (D + 6, 0.12), (D + 12, 0.04), (FR, 0.0)]      # his chin up, watching the pulse go


def hum(f):
    """The rig's hum while he types (a fine tremble growing to the pulse)."""
    if f >= D:
        return 0.0
    return (f / float(D)) ** 2 * math.sin(f * 2.9)


def ring(f):
    """The mast's ring-down after the pulse: a damped wobble."""
    if f < D:
        return 0.0
    t = f - D
    return math.exp(-t / 4.5) * math.sin(t * 1.9)


def attack_pose(arm, f):
    yaw = smooth_keys(K_YAW, f)
    ro = smooth_keys(K_RO, f)
    aims = stance_feet(arm, YAW0)
    hf, pf = look_at(FIELD, ro, yaw)
    hs, ps = look_at(SCREEN, ro, yaw)
    k = smooth_keys(K_SCREEN, f)
    torso(aims, yaw, bend=smooth_keys(K_BEND, f), side=-0.03 - 0.04 * ring(f), chest=-3.0 + 3.0 * ring(f + 0.5),
          look=hf + (hs - hf) * k, pitch=pf + 0.04 + (ps - pf - 0.04) * k + smooth_keys(K_LIFT, f),
          tilt=smooth_keys(K_TILT, f) + 0.05 * ring(f + 1), shrug=smooth_keys(K_SHRUG, f))
    ty = smooth_keys(K_TYPE, f)
    tl, tr = typing(f * 1.0, rate=0.24, amp=0.02 * ty, roam=0.014 * ty)
    # the right palm: from its place on the keys toward Enter, lifted by K_RH
    home = KEY_R + UP * tr[0] + SW * tr[1] - CU * tr[2]
    x = smooth_keys(K_RX, f)
    h = smooth_keys(K_RH, f)
    right = home.lerp(ENTER_P, x) + UP * h + CU * (0.12 * h) - SW * (0.2 * h)
    rfinger = (FINGER - SW * 0.12).normalized().lerp((FINGER - UP * 0.35).normalized(), x).normalized()
    aims.update(hands(arm, yaw, tl, tr, right=right, rfinger=rfinger))
    machine_aims(aims, wobble=(2.4 * ring(f) + 0.35 * hum(f), 1.3 * ring(f + 1.3) + 0.3 * hum(f + 1)))
    sc = machine_scales(node=smooth_keys(K_NODE, f) + 0.06 * hum(f + 0.5), flare=smooth_keys(K_FLARE, f, fn=lambda u: u))
    return aims, ro, yaw, sc


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, yaw, sc = attack_pose(arm, f)
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
