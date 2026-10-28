"""Unit Zero's clips (keyed in frames; the game plays them at CLIP_FPS 24).

Idle    : (96 frames) a gentle giant at ease: his weight sways slowly from foot to foot, the launcher and the big hand
          hanging; he tilts his head one way, then the other, as if curious, looks about, and blinks once (the `eye`
          bone squashed flat for a few frames).
Combat  : (40 frames) planted wide, knees bent, the launcher raised before him at the robots (its barrel tipped up for a
          lob), the big hand clenched by his hip; a slow heavy bob, his head up and a little tilted.
Attack  : (32 frames = 1.33 s, inside the 1.4 s cooldown) he leans in (0-2) and holds the aim (2-4): the shell leaves
          the muzzle at SHOT (frame 3: game.gd's shell leaves `barrel`'s tail, the muzzle; the held aim keeps the 30 Hz
          samples either side in agreement); from REC (frame 4) the barrel slams back into its jacket (`barrel` scaled
          short along its length, 4-5.5), the launcher kicks up and his body rocks back, his eye squints; the barrel runs
          out again (6-13) and he settles back into the Combat pose (frame 32 = Combat's first frame).
Ability : Overload (72 frames = 3 s): he steps his feet out wide and sinks (0-12), fists clenched low by his hips, elbows
          out, hunched over his core; the core's flare (`flare`) swells brighter and brighter while he trembles harder
          (12-40); he throws his arms wide and arches back (40-45), and at SIGNAL (frame 46: game.gd's blast goes out from
          his chest core, the flare bursts) holds there (45-52) while the flare dies away, then steps back into the Combat
          pose (52-72).
Cheer   : (48 frames = 2 s) his eye blinks into a happy arc (`smile`; `eye` scaled to 0), he waves the big hand high over
          his head twice, the launcher pumped up, a little stomping bounce, his head rocking side to side; back to Combat.

The arms are posed by the directions of their upper arms and forearms (FK, `arm_fk`) or by the wrist (two-bone IK,
`arm_ik`): the elbow works as a hinge, so the forearm's turn follows from the arm's bend (the launcher's top, its thumb
side, faces up when the forearm points forward). The hand and the launcher are rigid with the forearm (the wrist stays
straight); the big hand's fingers turn on their hinge (`fingers.L`: + opens, - clenches)."""
import math
from mathutils import Vector, Quaternion, Matrix
import zero as cm
from rig import Poser, leg_aims, frame_map, two_bone, bone_len
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

A_REST, W_REST, H_REST, U_REST, OPEN_AX, S0 = {}, {}, {}, {}, {}, {}
for _s in ("R", "L"):
    _wr, _A, _W, _M = cm.gframe(_s)
    A_REST[_s], W_REST[_s] = vec(_A), vec(_W)
    H_REST[_s] = vec(_A).cross(vec(_W)).normalized()
    U_REST[_s] = (vec(J["elbow_" + _s]) - vec(J["shoulder_" + _s])).normalized()
    OPEN_AX[_s] = vec(_A).cross(-vec(_M)).normalized()
    S0[_s] = 1.0 if U_REST[_s].cross(A_REST[_s]).dot(H_REST[_s]) > 0 else -1.0

SHOT = 3              # Attack: the shell leaves the muzzle (game.gd ATTACK_FRAME), inside the held aim (2-4)
REC = 4               # Attack: the recoil starts
FR = 32               # the Attack's length (1.33 s at 24 fps; the cooldown is 1.4 s)
SIGNAL = 46           # Ability: the blast goes out from the core
AB_FR = 72
CH_FR = 48
I_FR = 96
C_FR = 40


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mixd(a, b, k):
    a, b = Vector(a).normalized(), Vector(b).normalized()
    if a.dot(b) > -0.98:
        return a.slerp(b, k).normalized()
    return a.lerp(b, k).normalized()


def _ortho(b, a):
    b = Vector(b) - Vector(a) * Vector(b).dot(Vector(a))
    return b.normalized() if b.length > 1e-5 else Vector(a).orthogonal().normalized()


def mirror(v):
    return V(-v.x, v.y, v.z)


def bump(t, a, b, ramp):
    """0 outside [a, b], 1 inside, eased ramps `ramp` long."""
    if t <= a or t >= b:
        return 0.0
    return ease(min(1.0, (t - a) / ramp)) * ease(min(1.0, (b - t) / ramp))


# ---------------------------------------------------------------------------------------------- limbs
def arm_fk(side, u, d, tau=None):
    """The upper arm along u, the forearm along d; the elbow a hinge (the forearm's thumb side follows from the bend),
    or the thumb side toward `tau` when it is given (a nearly straight arm)."""
    u, d = Vector(u).normalized(), Vector(d).normalized()
    if tau is None:
        h = u.cross(d)
        if h.length < 1e-4:
            h = H_REST[side]
        h = h.normalized() * S0[side]
        t2 = h.cross(d).normalized()
    else:
        t2 = _ortho(tau, d)
    return {"upperarm." + side: ("frame", U_REST[side], u, H_REST[side], d.cross(t2)),
            "forearm." + side: ("frame", A_REST[side], d, W_REST[side], t2)}


def arm_ik(arm, side, wrist, pole, tau=None):
    """The wrist at `wrist` (two-bone IK, the elbow toward `pole`)."""
    la, lb = bone_len(arm, "upperarm." + side), bone_len(arm, "forearm." + side)
    st = {}
    wrist = Vector(wrist)

    def upper(P, base):
        S = base.translation
        E = two_bone(S, wrist, la, lb, Vector(pole))
        u, d = (E - S).normalized(), (wrist - E).normalized()
        a = arm_fk(side, u, d, tau)
        st["fore"] = a["forearm." + side]
        return a["upperarm." + side]

    def fore(P, base):
        return st["fore"]
    return {"upperarm." + side: upper, "forearm." + side: fore}


LEN = {}


def ik_ud(side, S, wrist, pole):
    """(upper arm, forearm) directions putting the wrist at `wrist` from the shoulder S (two-bone IK toward `pole`)."""
    E = two_bone(Vector(S), Vector(wrist), LEN["u" + side], LEN["f" + side], Vector(pole))
    return (E - Vector(S)).normalized(), (Vector(wrist) - E).normalized()


def fingers(rest, open_=0.0):
    def fn(P, base):
        Rh = P["hand.L"].to_3x3() @ rest["hand.L"].to_3x3().inverted()
        return ("rot", Quaternion(Rh @ OPEN_AX["L"], open_))
    return {"fingers.L": fn}


def feet(arm, yaw, lf=(0.3, 0.04), rf=(-0.3, 0.04), lift=(0.0, 0.0), turn=(8.0, -8.0)):
    """Ankles at the body-frame (x, y) lf / rf turned by yaw (planted: the hips turn over them); `lift` raises each."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by), up, tw in (("L", lf, lift[0], turn[0]), ("R", rf, lift[1], turn[1])):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + up)
        pole = q @ V(0.12 if side == "L" else -0.12, -1.0, 0.0)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw + tw) @ (rest_foot + V(0, 0, -up * 0.4))
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0, shrug=(0.0, 0.0), reach=(0.0, 0.0)):
    """Waist and hull bent forward by `bend` radians (to his left by `side`), the hull turned `chest` degrees more; the
    head turned to the world heading `look`, pitched up by `pitch`, tilted by `roll` (to his left); `shrug` / `reach`
    move the shoulder actuators up / forward."""
    q = rz(yaw)
    qc = rz(yaw + chest)

    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.4, side * 0.4), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(math.sin(roll) * 0.4 + math.sin(side) * 0.5,
                                                                     -0.36 - 0.5 * math.sin(bend) + 0.3 * pitch, 0.93), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.11 + 0.7 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -reach[0], shrug[0])
    aims["clavicle.R"] = qc @ V(-1.0, -reach[1], shrug[1])


def props(eye=1.0, smile=0.0, flare=0.0, barrel=1.0, blink=1.0):
    """The prop bones' scales: the eye (blink squashes it flat: bone z = up), the happy eye, the flare, the barrel
    (shortened along its length: the recoil)."""
    e = (eye, eye, eye * blink)
    return {"eye": e, "smile": smile, "flare": flare, "barrel": (1.0, barrel, 1.0)}


# ---------------------------------------------------------------------------------------------- idle
I_FEET = dict(lf=(0.31, 0.04), rf=(-0.31, 0.04), turn=(10.0, -10.0))
HANG_R = (V(-0.3, 0.06, -0.95), V(-0.08, -0.32, -0.94))       # (upper arm, forearm) hanging
HANG_L = (V(0.3, 0.06, -0.95), V(0.08, -0.3, -0.95))


def idle_pose(arm, t, rest):
    w = 2 * math.pi * t
    sway = math.sin(w)
    br = math.sin(w * 3)
    yaw = 3.0 * sway
    ro = V(0.022 * sway, 0.0, -0.02 + 0.006 * br - 0.008 * abs(sway))
    aims = feet(arm, 0.0, **I_FEET)
    # head tilts: to his left (t ~ 0.2), then to his right (t ~ 0.65), looking about between
    tiltL = bump(t, 0.1, 0.36, 0.08)
    tiltR = bump(t, 0.55, 0.8, 0.08)
    roll = 0.26 * tiltL - 0.24 * tiltR + 0.03 * sway
    look = 14.0 * math.sin(w + 0.9) * (1.0 - tiltL - tiltR) + 8.0 * tiltL - 10.0 * tiltR
    torso(aims, yaw, bend=0.06 + 0.01 * br, side=-0.04 * sway, chest=1.5 * sway, look=look, pitch=0.13 + 0.03 * br + 0.06 * (tiltL + tiltR),
          roll=roll, shrug=(0.03 * br, 0.03 * br))
    q = rz(yaw)
    sw = 0.05 * math.sin(w + 0.4)
    aims.update(arm_fk("R", q @ (HANG_R[0] + V(0, -sw, 0)), q @ (HANG_R[1] + V(0, -sw * 1.5, 0))))
    aims.update(arm_fk("L", q @ (HANG_L[0] + V(0, sw, 0)), q @ (HANG_L[1] + V(0, sw * 1.5, 0))))
    aims.update(fingers(rest, 0.1 + 0.15 * bump(t, 0.4, 0.9, 0.1)))
    # a blink a little after the first tilt
    b = 1.0 - 0.9 * bump(t, 0.42, 0.47, 0.02)
    return aims, ro, q, props(blink=b)


# ---------------------------------------------------------------------------------------------- combat
C_FEET = dict(lf=(0.33, -0.02), rf=(-0.33, 0.1), turn=(8.0, -14.0))
C_CROUCH = 0.05
AIM_U = V(-0.34, 0.26, -0.9)          # the launcher arm: the upper arm down and back ...
AIM_D = V(0.04, -0.9, 0.42)            # ... the forearm (and barrel) forward and up at the robots
GUARD_L = V(0.52, -0.36, 1.06)        # the big hand's wrist, clenched by his hip, forward
GUARD_POLE_L = V(1.0, 0.6, -0.3)


def combat_state(t):
    w = 2 * math.pi * t
    b = 0.5 - 0.5 * math.cos(w * 2)           # a heavy bob twice a loop
    yaw = -6.0 + 2.0 * math.sin(w)
    ro = V(0.0, 0.0, -C_CROUCH - 0.018 * b)
    return w, b, yaw, ro


def combat_arms(arm, yaw, ro, b, rest, lift=0.0, kick=0.0, back=0.0):
    """The launcher at the robots (raised `lift` + `kick` radians, its upper arm pulled `back`), the big hand by his hip."""
    q = rz(yaw)
    d = AIM_D.copy()
    ang = lift + kick
    d = Quaternion(V(1, 0, 0), -ang) @ d
    u = (AIM_U + V(0, 0.4 * back, 0)).normalized()
    aims = arm_fk("R", q @ u, q @ d)
    wl = ROOT + ro + q @ (GUARD_L - ROOT + V(0, 0, -0.012 * b))
    aims.update(arm_ik(arm, "L", wl, q @ GUARD_POLE_L))
    return aims


def combat_pose(arm, t, rest):
    w, b, yaw, ro = combat_state(t)
    aims = feet(arm, 0.0, **C_FEET)
    torso(aims, yaw, bend=0.12 + 0.015 * b, chest=-4.0, look=0.0, pitch=0.16 - 0.02 * b, roll=0.1 + 0.03 * math.sin(w))
    aims.update(combat_arms(arm, yaw, ro, b, rest, lift=0.02 * math.sin(w * 2 + 0.5)))
    aims.update(fingers(rest, -0.95))
    return aims, ro, rz(yaw), props()


# ---------------------------------------------------------------------------------------------- attack
def attack_pose(arm, f, rest):
    """0-2 lean in, held 2-4 (the shell leaves at SHOT, 3), recoil from REC (4), run out 6-13, back to Combat (t = 0) by FR."""
    w, b, yaw0, ro0 = combat_state(0.0)
    if f <= 2:
        lean = smooth01(f / 2.0)
    elif f <= REC:
        lean = 1.0
    else:
        lean = 1.0 - smooth01((f - REC) / 2.0)
    kick = rock = 0.0
    if f > REC:
        x = f - REC
        kick = 0.16 * math.exp(-((x - 1.4) / 1.6) ** 2) + 0.08 * math.exp(-((x - 6.0) / 5.0) ** 2)
        kick *= 1.0 - smooth01((f - 20) / (FR - 20))
        rock = math.exp(-((x - 2.2) / 2.6) ** 2)
    settle = smooth01((f - 12) / (FR - 12))
    # the barrel slams back (4 -> 5.5) and runs out (6 -> 13)
    if f <= REC:
        bar = 1.0
    elif f <= REC + 1.5:
        bar = 1.0 - 0.3 * smooth01((f - REC) / 1.5)
    else:
        bar = 0.7 + 0.3 * smooth01((f - REC - 2) / 7.0)
    yaw = yaw0
    ro = ro0 + V(0.0, -0.025 * lean + 0.035 * rock, -0.012 * lean - 0.02 * rock)
    aims = feet(arm, 0.0, **C_FEET)
    torso(aims, yaw, bend=0.12 + 0.06 * lean - 0.06 * rock, chest=-4.0 - 2.0 * rock, look=0.0, pitch=0.16 + 0.12 * rock,
          roll=0.1 - 0.05 * rock, shrug=(0.0, 0.1 * rock), reach=(0.0, 0.08 * lean - 0.06 * rock))
    aims.update(combat_arms(arm, yaw, ro, b, rest, lift=-0.05 * lean, kick=kick, back=0.08 * rock * (1 - settle)))
    aims.update(fingers(rest, -0.95))
    squint = 1.0 - 0.45 * math.exp(-((f - REC - 1.0) / 1.8) ** 2) if f >= REC - 1 else 1.0
    return aims, ro, rz(yaw), props(barrel=bar, blink=squint)


# ---------------------------------------------------------------------------------------------- ability: Overload
WIDE_FEET = dict(lf=(0.44, 0.02), rf=(-0.44, 0.06), turn=(14.0, -14.0))
CHARGE_L = V(0.4, -0.2, 0.86)         # the fists clenched low by his hips, elbows out
CHARGE_POLE_L = V(1.0, 0.7, 0.1)
CHARGE_R = (V(-0.55, 0.45, -0.7), V(0.35, -0.55, -0.76))     # the launcher arm: elbow out and back, the launcher down and in
WIDE_R = (V(-0.85, 0.12, 0.5), V(-0.55, -0.2, 0.81))         # arms thrown wide and up (a V), a little back
WIDE_L = (mirror(WIDE_R[0]), mirror(WIDE_R[1]))


def flare_scale(f):
    if f < 10:
        return 0.0
    if f < SIGNAL - 1:
        x = (f - 10) / float(SIGNAL - 1 - 10)
        return 0.25 + 0.8 * x ** 1.6
    if f <= SIGNAL + 1:
        return 1.6
    return max(0.0, 1.6 * (1.0 - (f - SIGNAL - 1) / 9.0))


def ability_pose(arm, f, rest):
    w0, b0, yaw0, ro0 = combat_state(0.0)
    q0 = rz(yaw0)
    sc = props(flare=flare_scale(f))
    if f <= 12:
        # step out wide and sink, the arms drawn down into the charge
        k = ease(f / 12.0)
        lf = tuple(lerp(a, c, k) for a, c in zip(C_FEET["lf"], WIDE_FEET["lf"]))
        rf = tuple(lerp(a, c, k) for a, c in zip(C_FEET["rf"], WIDE_FEET["rf"]))
        lift = (0.06 * math.sin(math.pi * min(1.0, f / 6.0)), 0.06 * math.sin(math.pi * max(0.0, min(1.0, (f - 6) / 6.0))))
        aims = feet(arm, 0.0, lf=lf, rf=rf, lift=lift, turn=(lerp(8.0, 14.0, k), lerp(-14.0, -14.0, k)))
        yaw = lerp(yaw0, 0.0, k)
        ro = ro0.lerp(V(0.0, 0.0, -0.12), k)
        torso(aims, yaw, bend=lerp(0.12, 0.22, k), chest=lerp(-4.0, 0.0, k), look=0.0, pitch=lerp(0.16, 0.0, k), roll=lerp(0.1, 0.0, k),
              shrug=(0.12 * k, 0.12 * k), reach=(0.06 * k, 0.06 * k))
        q = rz(yaw)
        cu, cd = AIM_U.normalized(), AIM_D.normalized()
        aims.update(arm_fk("R", mixd(q0 @ cu, CHARGE_R[0], k), mixd(q0 @ cd, CHARGE_R[1], k)))
        wl = (ROOT + ro0 + q0 @ (GUARD_L - ROOT)).lerp(ROOT + ro + (CHARGE_L - ROOT), k)
        aims.update(arm_ik(arm, "L", wl, (q0 @ GUARD_POLE_L).lerp(CHARGE_POLE_L, k)))
        aims.update(fingers(rest, -0.95))
        return aims, ro, rz(yaw), sc
    if f <= 40:
        # the charge: hunched over the swelling core, trembling harder and harder
        k = (f - 12) / 28.0
        amp = 0.003 + 0.012 * k ** 1.5
        jit = (1.0 if f % 2 else -1.0)
        ro = V(jit * amp, 0.0, -0.12 - 0.02 * k + 0.5 * amp * (1 if f % 3 == 0 else -1))
        aims = feet(arm, 0.0, **WIDE_FEET)
        torso(aims, jit * 1.5 * k, bend=0.22 + 0.06 * k, look=jit * 2.0 * k, pitch=-0.1 + 0.08 * k + jit * 0.02 * k, roll=jit * 0.03 * k,
              shrug=(0.12 + 0.05 * k, 0.12 + 0.05 * k), reach=(0.06, 0.06))
        aims.update(arm_fk("R", CHARGE_R[0], CHARGE_R[1]))
        aims.update(arm_ik(arm, "L", ROOT + ro + (CHARGE_L - ROOT), CHARGE_POLE_L))
        aims.update(fingers(rest, -0.95))
        sc = props(flare=flare_scale(f), blink=1.0 - 0.35 * k)
        return aims, ro, rz(0.0), sc
    if f <= 52:
        # the throw: arms flung wide, chest out, head back (40-45); held through the blast (45-52)
        k = smooth01((f - 40) / 5.0)
        hold = max(0.0, (f - 45) / 7.0)
        ro = V(0.0, 0.03 * k, lerp(-0.14, -0.08, k) - 0.01 * hold)
        aims = feet(arm, 0.0, **WIDE_FEET)
        torso(aims, 0.0, bend=lerp(0.28, -0.16, k), look=0.0, pitch=lerp(-0.02, 0.32, k), shrug=(lerp(0.17, 0.3, k),) * 2,
              reach=(lerp(0.06, -0.12, k),) * 2)
        aims.update(arm_fk("R", mixd(CHARGE_R[0], WIDE_R[0], k), mixd(CHARGE_R[1], WIDE_R[1], k)))
        wc = ROOT + V(0.0, 0.0, -0.14) + (CHARGE_L - ROOT)

        def left(S, k=k, wc=wc):
            u, d = ik_ud("L", S, wc, CHARGE_POLE_L)
            return mixd(u, WIDE_L[0], k), mixd(d, WIDE_L[1], k)
        aims.update(fingers(rest, lerp(-0.95, 0.55, k)))
        sc = props(flare=flare_scale(f), blink=lerp(0.65, 1.12, k))
        return aims, ro, rz(0.0), sc, {"L": left}
    # back into the Combat pose, the feet stepping in
    k = ease((f - 52) / float(AB_FR - 52))
    lf = tuple(lerp(a, c, k) for a, c in zip(WIDE_FEET["lf"], C_FEET["lf"]))
    rf = tuple(lerp(a, c, k) for a, c in zip(WIDE_FEET["rf"], C_FEET["rf"]))
    lift = (0.05 * math.sin(math.pi * min(1.0, max(0.0, (k - 0.1) / 0.4))), 0.05 * math.sin(math.pi * min(1.0, max(0.0, (k - 0.5) / 0.4))))
    aims = feet(arm, 0.0, lf=lf, rf=rf, lift=lift, turn=(lerp(14.0, 8.0, k), -14.0))
    yaw = lerp(0.0, yaw0, k)
    ro = V(0.0, 0.03, -0.09).lerp(ro0, k)
    torso(aims, yaw, bend=lerp(-0.16, 0.12, k), chest=lerp(0.0, -4.0, k), look=0.0, pitch=lerp(0.32, 0.16, k), roll=lerp(0.0, 0.1, k),
          shrug=(lerp(0.3, 0.0, k),) * 2, reach=(lerp(-0.12, 0.0, k),) * 2)
    q = rz(yaw)
    aims.update(arm_fk("R", mixd(WIDE_R[0], q @ AIM_U, k), mixd(WIDE_R[1], q @ AIM_D, k)))
    wl = ROOT + ro0 + rz(yaw0) @ (GUARD_L - ROOT)

    def left(S, k=k, wl=wl):
        u, d = ik_ud("L", S, wl, rz(yaw0) @ GUARD_POLE_L)
        return mixd(WIDE_L[0], u, k), mixd(WIDE_L[1], d, k)
    aims.update(fingers(rest, lerp(0.55, -0.95, k)))
    return aims, ro, rz(yaw), sc, {"L": left}


# ---------------------------------------------------------------------------------------------- cheer
WAVE_U = V(0.55, -0.1, 0.83)          # the big hand high over his head: the upper arm up and out ...
WAVE_D = V(0.2, -0.15, 1.0)           # ... the forearm up, swinging side to side
PUMP_U = V(-0.6, -0.05, 0.8)          # the launcher pumped up
PUMP_D = V(-0.15, -0.3, 1.0)


def cheer_pose(arm, f, rest):
    t = f / float(CH_FR)
    w0, b0, yaw0, ro0 = combat_state(0.0)
    up = smooth01(t / 0.18) * (1.0 - smooth01((t - 0.8) / 0.2))
    happy = smooth01((t - 0.07) / 0.06) * (1.0 - smooth01((t - 0.86) / 0.06))
    blink = 1.0 - 0.95 * (bump(t, 0.03, 0.13, 0.04) + bump(t, 0.83, 0.93, 0.04))
    wave = math.sin((t - 0.18) / 0.62 * 2 * math.pi * 2) * smooth01((t - 0.16) / 0.06) * (1.0 - smooth01((t - 0.76) / 0.06))
    bounce = max(0.0, math.sin((t - 0.18) / 0.6 * 2 * math.pi * 2)) * smooth01((t - 0.16) / 0.05) * (1.0 - smooth01((t - 0.76) / 0.05))
    yaw = lerp(yaw0, 0.0, up)
    ro = ro0.lerp(V(0.0, 0.0, -0.03), up) + V(0.0, 0.0, -0.05 * bounce)
    aims = feet(arm, 0.0, lift=(0.03 * bounce * (wave > 0), 0.03 * bounce * (wave <= 0)), **C_FEET)
    torso(aims, yaw, bend=lerp(0.12, -0.04, up), side=0.06 * wave * up, chest=lerp(-4.0, 0.0, up), look=0.0,
          pitch=lerp(0.16, 0.3, up), roll=lerp(0.1, 0.0, up) + 0.22 * wave * up, shrug=(0.32 * up, 0.28 * up))
    q0 = rz(yaw0)
    # the big hand waving high
    swing = Quaternion(V(0, -1, 0), 0.38 * wave)
    wl = ROOT + ro0 + q0 @ (GUARD_L - ROOT)

    def left(S, up=up, wl=wl, swing=swing):
        u, d = ik_ud("L", S, wl, q0 @ GUARD_POLE_L)
        return mixd(u, WAVE_U, up), mixd(d, swing @ WAVE_D, up)
    # the launcher pumped up
    aims.update(arm_fk("R", mixd(q0 @ AIM_U, PUMP_U + V(0, 0, 0.1 * bounce), up), mixd(q0 @ AIM_D, PUMP_D + V(0, -0.15 * bounce, 0), up)))
    aims.update(fingers(rest, lerp(-0.95, 0.5, up)))
    return aims, ro, rz(yaw), props(eye=1.0 - happy, smile=happy, blink=blink), {"L": left}


# ---------------------------------------------------------------------------------------------- clips
def _clip(arm, name, frames, fn, cyclic):
    P = Poser(arm)
    for s in ("R", "L"):
        LEN["u" + s], LEN["f" + s] = bone_len(arm, "upperarm." + s), bone_len(arm, "forearm." + s)
    act = new_action(arm, name)
    for f in range(frames + 1):
        x = (f % frames) / frames if cyclic else f
        out = fn(arm, x, P.rest)
        aims, ro, rr, sc = out[:4]
        late = out[4] if len(out) > 4 else {}
        if late:
            # arms placed from the posed shoulder (a first pass places it)
            _, P0 = P.solve(aims, ro, rr, scales=sc)
            for side, g in late.items():
                u, d = g(P0["upperarm." + side].translation.copy())
                aims.update(arm_fk(side, u, d))
        ch, _ = P.solve(aims, ro, rr, scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, cyclic)
    return act


def make_idle(arm):
    return _clip(arm, "Idle", I_FR, idle_pose, True)


def make_combat(arm):
    return _clip(arm, "Combat", C_FR, combat_pose, True)


def make_attack(arm):
    return _clip(arm, "Attack", FR, attack_pose, False)


def make_ability(arm):
    return _clip(arm, "Ability", AB_FR, ability_pose, False)


def make_cheer(arm):
    return _clip(arm, "Cheer", CH_FR, cheer_pose, False)


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
