"""EMP Tower clips (game: 24 fps).

Idle   : the guard closed over the trigger, the bank idling (its bars a quarter lit, the head pulsing softly); he stands at
         his case, his right fist resting on its near edge, raises his left forearm and checks the readout on his
         control pad (head bowed to it, a small nod), lowers it, glances up at the emitter head and back out at the field.
Combat : the guard open; he leans in over the case, his right fist poised over the trigger, his left hand pressing the
         headset's left cup to his ear (listening), watching the robots.
Attack : (33 frames, inside the 1.4 s cooldown) the capacitor bank charges (frames 0-8: the bars fill up their windows,
         the head swells and flickers, the mast hums) while he draws his fist up high (anticipation); he slams it down on
         the trigger: the pulse goes off at DISCHARGE (frame 10, the trigger held down to 12: the game draws the EMP rings
         from the emitter head there); the head flashes, the bank empties, the mast shudders and rings down (a damped
         wobble about its foot), he flinches from the blast; then the bars creep back, he lifts his fist back over the
         trigger and settles into the Combat pose.

The machine never moves (`machine`); the mast wobbles about its foot ("rot" aims), the head (`emitter`) and the bars
(`charge`, along its length) scale, the guard turns about its hinge (SW), the trigger's cap squashes (`button`, along its
axis). His right fist is placed with a "frame" aim (the thumb up the trigger's axis: a hammer fist), the knuckles
following the solved forearm; his left fist is placed on the posed headset cup (a second solve once the head is known)."""
import math
from mathutils import Vector, Quaternion, Matrix
import emp as cm
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
SHOULDER_R = vec(J["shoulder_R"])
SHOULDER_L = vec(J["shoulder_L"])

SN, SU, SW = vec(cm.SN), vec(cm.SU), vec(cm.SW)
BTN_TOP = vec(cm.BTN_TOP)
CONTACT = 0.04                  # the fist's centre above the trigger's rest top at the slam (its cap pressed down)
PRESS = 0.55                    # the trigger's cap squashed to this (its bone's length)
OPEN = cm.GUARD_OPEN
EMIT = vec(cm.EMIT_C)
_pc, _pax, _pout, _pacr = cm.pad_frame()
PAD_C, PAD_OUT = vec(_pc), vec(_pout)
CUP_OUT_L = vec(cm._cup_out(1))
CUP_AX_L = vec(cm._cup_axis(1))

# ---------------------------------------------------------------------------------------------- timing (24 fps)
DISCHARGE = 10     # game.gd ATTACK_FRAME: the fist hits the trigger, the pulse goes off (held to frame 12)
FR = 33            # <= 1.4 s


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def fwd(yaw):
    return rz(yaw) @ V(0.0, -1.0, 0.0)


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def smooth_keys(keys, f, fn=ease):
    if f <= keys[0][0]:
        return keys[0][1]
    for (fa, a), (fb, b) in zip(keys, keys[1:]):
        if f <= fb:
            k = fn((f - fa) / float(fb - fa)) if fb > fa else 1.0
            return a.lerp(b, k) if isinstance(a, Vector) else a + (b - a) * k
    return keys[-1][1]


def perp(v, ax):
    v = Vector(v) - ax * Vector(v).dot(ax)
    return v.normalized() if v.length > 1e-6 else ax.orthogonal().normalized()


# ---------------------------------------------------------------------------------------------- the machine
def machine_aims(aims, guard=0.0, wobble=(0.0, 0.0)):
    """guard: the guard's opening (deg); wobble: the mast's tilt (deg) about two horizontal axes."""
    aims["guard"] = ("rot", Quaternion(SW, math.radians(guard)))
    q = Quaternion((1, 0, 0), math.radians(wobble[0])) @ Quaternion((0, 1, 0), math.radians(wobble[1]))
    aims["mast"] = ("rot", q)


def machine_scales(charge=0.25, emitter=1.0, button=1.0):
    return {"charge": (1.0, max(0.06, charge), 1.0), "emitter": emitter, "button": (1.0, button, 1.0)}


# ---------------------------------------------------------------------------------------------- body
def feet(arm, lf, rf, yaw, lift_l=0.0, lift_r=0.0):
    aims = {}
    q = rz(yaw)
    for side, p, lift in (("L", lf, lift_l), ("R", rf, lift_r)):
        z = float(J["ankle_" + side][2]) + lift
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims.update(leg_aims(arm, side, V(p[0], p[1], z), pole=pole))
        aims["foot." + side] = rz(yaw + (-10 if side == "R" else 10)) @ rest_foot
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, tilt=0.0, shrug=0.0):
    """bend: + forward; side: + to his left; chest: the chest's extra turn (deg); look: the head's heading (deg, world);
    pitch: + chin up; tilt: + head to his left; shrug: + shoulders up."""
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tl(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tl(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tl(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(tilt * 0.3, -0.16 - 0.25 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(tilt, -0.06 + 0.55 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.04, 0.02 + shrug)
    aims["clavicle.R"] = qc @ V(-1.0, -0.04, 0.02 + shrug)


def grip(arm, side, fist, thumb, finger, pole):
    """A fist (its middle) at `fist`, the thumb along `thumb`, the knuckles toward `finger`."""
    T0, F0, W0, C0 = (T_R, F_R, WR_R, FIST_R) if side == "R" else (T_L, F_L, WR_L, FIST_L)
    t = Vector(thumb).normalized()
    R = frame_map(T0, t, F0, perp(finger, t))
    aims = arm_aims(arm, side, fist - R @ (C0 - W0), pole=pole)
    aims["hand." + side] = ("frame", T0, R @ T0, F0, R @ F0)
    return aims


def hip_l(arm, ro, yaw):
    """His left fist on his hip, the elbow out."""
    wrist = body_pt(V(0.3, -0.005, 1.0), ro, yaw)
    return arm_aims(arm, "L", wrist, pole=rz(yaw) @ V(1.0, 0.45, 0.1), hand_dir=rz(yaw) @ V(-0.4, 0.25, -1.0))


def cup_target(Pm):
    """The posed headset cup's outer centre and axis (from the posed head)."""
    M = Pm["head"]
    R0 = arm_rest["head"]
    Mw = M @ R0.inverted()
    return Mw @ CUP_OUT_L, (Mw.to_3x3() @ CUP_AX_L).normalized(), (Mw.to_3x3() @ V(0, 0, 1)).normalized(), (Mw.to_3x3() @ V(0, -1, 0)).normalized()


arm_rest = {}


def ear_l(arm, Pm):
    """His left fist pressed to the headset's left cup (from the head's posed matrix)."""
    c, ax, up, fw = cup_target(Pm)
    fist = c + ax * 0.038 + up * 0.012
    return grip(arm, "L", fist, up, fw, ax * 1.0 + V(0.0, 0.4, -0.8))


def pad_twist_aims(arm, aims, want):
    """Turn the left forearm about its own axis so the control pad's face looks along `want`."""
    orig = aims["forearm.L"]
    rest = arm.data.bones["forearm.L"].matrix_local.to_3x3()
    out_local = rest.inverted() @ PAD_OUT
    def fa(P, base):
        d = Vector(orig(P, base)).normalized()
        y0 = base.col[1].xyz.normalized()
        R = y0.rotation_difference(d).to_matrix() @ base.to_3x3()
        o = (R @ out_local)
        o = (o - d * o.dot(d)).normalized()
        w = Vector(want)
        w = (w - d * w.dot(d)).normalized()
        ang = math.atan2(d.dot(o.cross(w)), o.dot(w))
        return (d, ang)
    aims["forearm.L"] = fa


def solve_r(P, arm, aims, ro, rr, sc, fist, thumb, pole, finger0, left=None):
    """Solve with his right fist at `fist` (the thumb along `thumb`), three passes: the knuckles follow the solved
    forearm; `left`(Pm) -> aims for the left arm from the posed head (solved in the same passes)."""
    t = Vector(thumb).normalized()
    finger = perp(finger0, t)
    Pm = None
    for it in range(3):
        a2 = dict(aims)
        a2.update(grip(arm, "R", fist, t, finger, pole))
        if left is not None and Pm is not None:
            a2.update(left(Pm))
        ch, Pm = P.solve(a2, ro, rr, scales=sc)
        fa = Pm["forearm.R"].col[1].xyz.normalized()
        finger = perp(fa, t)
    if left is not None:
        a2 = dict(aims)
        a2.update(grip(arm, "R", fist, t, finger, pole))
        a2.update(left(Pm))
        ch, Pm = P.solve(a2, ro, rr, scales=sc)
    return ch


# ---------------------------------------------------------------------------------------------- idle
I_FEET = ((0.17, 0.07), (-0.2, 0.0))
I_YAW = -18.0
I_RO = V(0.0, 0.0, -0.01)
REST_R = cm.slab_pt(-0.13, cm.SLAB_HALF[1] - 0.01, 0.045)     # his right fist resting on the case's near edge


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br = math.sin(w * 3)
        read = smooth_keys([(0.0, 0.0), (0.12, 0.0), (0.24, 1.0), (0.56, 1.0), (0.66, 0.0), (1.0, 0.0)], t)
        up = smooth_keys([(0.0, 0.0), (0.68, 0.0), (0.76, 1.0), (0.86, 1.0), (0.94, 0.0), (1.0, 0.0)], t)
        nod = 0.07 * math.sin(math.pi * min(1.0, max(0.0, (t - 0.42) / 0.08))) if 0.42 < t < 0.5 else 0.0
        yaw = I_YAW + 4.0 * up + 1.5 * math.sin(w)
        ro = I_RO + V(0.0, 0.0, 0.004 * br) + V(0.01, 0.0, 0.0) * read
        aims = feet(arm, I_FEET[0], I_FEET[1], I_YAW)
        look = I_YAW - 6.0 + 4.0 * math.sin(w * 2) * (1 - read) + 22.0 * read + 48.0 * up
        torso(aims, yaw, bend=0.06 + 0.12 * read, side=0.02 * read, chest=4.0 * read + 6.0 * up, look=look,
              pitch=0.0 - 0.5 * read - nod + 0.36 * up + 0.015 * br, tilt=-0.05 * read + 0.08 * up, shrug=0.02 * br)
        # his left arm: at his side, raised to read the pad (the forearm across his chest, the pad's face up to his eyes)
        if read < 1e-4:
            aims.update(arm_aims(arm, "L", body_pt(V(0.4, 0.0, 0.9), ro, yaw), pole=rz(yaw) @ V(1.0, 0.6, -0.2),
                                 hand_dir=rz(yaw) @ V(0.3, -0.1, -1.0)))
        else:
            hang = body_pt(V(0.4, 0.0, 0.9), ro, yaw)
            held = body_pt(V(0.06, -0.36, 1.2), ro, yaw)
            wr = hang.lerp(held, read) + V(0, 0, 0.05 * math.sin(math.pi * read))
            aims.update(arm_aims(arm, "L", wr, pole=(rz(yaw) @ V(1.0, 0.6, -0.2)).lerp(rz(yaw) @ V(1.0, 0.2, -0.7), read),
                                 hand_dir=(rz(yaw) @ V(0.3, -0.1, -1.0)).lerp(rz(yaw) @ V(-0.9, -0.3, 0.1), read)))
            eye = body_pt(cm.hp((0.0, -0.1, 1.68)), ro, yaw)
            pad_twist_aims(arm, aims, (eye - held).normalized())
        machine_aims(aims, guard=0.0)
        sc = machine_scales(charge=0.25 + 0.03 * math.sin(w * 6), emitter=1.0 + 0.035 * math.sin(w * 4))
        thumb = (SN * 0.4 + V(0, 0, 1) * 0.6).normalized()
        ch = solve_r(P, arm, aims, ro, rz(yaw), sc, vec(REST_R), thumb, rz(yaw) @ V(-1.0, 0.4, -0.6), -SU)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- combat
C_FEET = ((0.16, 0.08), (-0.25, -0.08))
C_YAW = -30.0
C_RO = V(0.0, -0.01, -0.035)
POLE_R = V(-1.0, 0.5, -0.6)
HOVER = 0.075                  # the fist above the trigger in the Combat pose


def combat_core(arm, br=0.0, sw=0.0):
    ro = C_RO + V(0.0, 0.0, 0.006 * br)
    aims = feet(arm, C_FEET[0], C_FEET[1], C_YAW)
    torso(aims, C_YAW + 1.5 * sw, bend=0.2 + 0.01 * br, side=-0.05, chest=-8.0, look=-12.0 + 5.0 * sw, pitch=0.04, tilt=0.1)
    return aims, ro


def fist_at(h):
    """The fist's centre over the trigger, h above contact."""
    return BTN_TOP + SN * (CONTACT + h)


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        t = (f % frames) / frames
        w = 2 * math.pi * t
        br, sw = math.sin(w * 2), math.sin(w)
        aims, ro = combat_core(arm, br, sw)
        machine_aims(aims, guard=OPEN)
        sc = machine_scales(charge=0.25 + 0.03 * math.sin(w * 3), emitter=1.0 + 0.04 * math.sin(w * 2))
        ch = solve_r(P, arm, aims, ro, rz(C_YAW + 1.5 * sw), sc, fist_at(HOVER + 0.006 * br), SN, rz(C_YAW) @ POLE_R,
                     -SU, left=lambda Pm: ear_l(arm, Pm))
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- attack
D = DISCHARGE
K_H = [(0, HOVER), (3, HOVER + 0.08), (7, 0.26), (8, 0.25), (9, 0.1), (D, 0.0), (D + 2, 0.0), (D + 5, 0.06), (D + 9, 0.05),
       (22, HOVER + 0.02), (FR, HOVER)]
K_BTN = [(0, 1.0), (D - 1, 1.0), (D, PRESS), (D + 2, PRESS), (D + 4, 1.0), (FR, 1.0)]
K_CHARGE = [(0, 0.25), (2, 0.32), (8, 1.0), (D, 1.0), (D + 1, 0.06), (D + 6, 0.08), (FR, 0.25)]
K_EMIT = [(0, 1.0), (8, 1.16), (D - 1, 1.2), (D, 1.55), (D + 1, 1.45), (D + 3, 0.8), (D + 8, 0.82), (FR, 1.0)]
K_RO = [(0, C_RO), (4, C_RO + V(0.01, 0.015, 0.02)), (7, C_RO + V(0.012, 0.02, 0.026)), (D, C_RO + V(-0.02, -0.02, -0.035)),
        (D + 2, C_RO + V(-0.018, -0.016, -0.04)), (D + 6, C_RO + V(0.02, 0.03, -0.02)), (D + 12, C_RO + V(0.0, 0.0, -0.01)), (FR, C_RO)]
K_YAW = [(0, C_YAW), (6, C_YAW + 5.0), (D, C_YAW - 4.0), (D + 5, C_YAW + 3.0), (24, C_YAW - 1.0), (FR, C_YAW)]
K_BEND = [(0, 0.2), (6, 0.08), (8, 0.1), (D, 0.32), (D + 2, 0.3), (D + 5, 0.12), (D + 10, 0.16), (FR, 0.2)]
K_PITCH = [(0, 0.04), (5, -0.12), (8, -0.16), (D, -0.1), (D + 2, -0.22), (D + 6, 0.1), (D + 12, 0.06), (FR, 0.04)]
K_LOOK = [(0, -12.0), (5, -30.0), (D, -26.0), (D + 4, -2.0), (D + 12, -8.0), (FR, -12.0)]
K_TILT = [(0, 0.1), (5, 0.06), (D + 1, 0.18), (D + 5, 0.02), (FR, 0.1)]
K_SHRUG = [(0, 0.0), (6, 0.1), (D, 0.0), (D + 2, 0.22), (D + 6, 0.06), (FR, 0.0)]


def hum(f):
    """The bank's hum while it charges (a fine tremble growing to the discharge)."""
    if f >= D:
        return 0.0
    return (f / float(D)) ** 2 * math.sin(f * 2.9)


def ring(f):
    """The mast's ring-down after the discharge: a damped wobble."""
    if f < D:
        return 0.0
    t = f - D
    return math.exp(-t / 4.5) * math.sin(t * 1.9)


def attack_pose(arm, f):
    yaw = smooth_keys(K_YAW, f)
    ro = smooth_keys(K_RO, f)
    aims = feet(arm, C_FEET[0], C_FEET[1], C_YAW)
    torso(aims, yaw, bend=smooth_keys(K_BEND, f), side=-0.05 - 0.04 * ring(f), chest=-8.0 + 3.0 * ring(f + 0.5),
          look=smooth_keys(K_LOOK, f), pitch=smooth_keys(K_PITCH, f), tilt=smooth_keys(K_TILT, f) + 0.05 * ring(f + 1),
          shrug=smooth_keys(K_SHRUG, f))
    machine_aims(aims, guard=OPEN, wobble=(2.6 * ring(f) + 0.35 * hum(f), 1.4 * ring(f + 1.3) + 0.3 * hum(f + 1)))
    em = smooth_keys(K_EMIT, f) + 0.05 * hum(f + 0.5)
    sc = machine_scales(charge=smooth_keys(K_CHARGE, f), emitter=em, button=smooth_keys(K_BTN, f))
    return aims, ro, yaw, sc


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, yaw, sc = attack_pose(arm, f)
        h = smooth_keys(K_H, f)
        ch = solve_r(P, arm, aims, ro, rz(yaw), sc, fist_at(h), SN, rz(yaw) @ POLE_R, -SU, left=lambda Pm: ear_l(arm, Pm))
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    for b in arm.data.bones:
        arm_rest[b.name] = b.matrix_local.copy()
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
