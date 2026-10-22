"""The War Drummer's clips (game: 24 fps).

Idle   : the sticks crossed and resting on the drumhead, his fists on its rim either side; he hums a tune, bobbing up on his
         toes and down onto his heels, his head swaying to it.
Combat : the sticks raised and ready over the drum, a little bounce to the beat he keeps in his head.
Attack : (33 frames, inside the 1.4 s cooldown) a quick roll building up (frames 1-4), both arms swing high (5-6) and come
         down in a great double beat (BEAT, frame 8, the sticks held on the head to frame 9: game.gd's shockwave leaves the
         drumhead there); the sticks bounce off, a flourish (the sticks raised before his face and crossed, clicked
         together at frame 17) and back to ready.

The sticks lie along the fists' thumb axes ("frame" aims on the hands; each stick rides its own bone, stick.R / stick.L,
child of the hand). The drum hangs on the root by its hook: its bone ("drum", head at the hook) tips it a little on the
hook at the beat; the drumhead bone carries the head's centre (the point the game's shockwave leaves from)."""
import math
from mathutils import Vector, Quaternion
import drummer as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
HOOK = vec(cm.hook_point()[0])
HEAD = vec(cm.DRUM_HEAD)
AX = vec(cm.DRUM_AX)
TIP = cm.STICK_TIP
CONTACT = 0.004 + 0.0165              # drumhead centre -> the acorn's centre when it rests on the head
SWING_AX = (HEAD - HOOK).cross(V(0, 0, 1)).normalized()     # tipping the drum about its hook: + dips the head

T_REST, F_REST, FIST_OFF = {}, {}, {}
for _s in ("R", "L"):
    _wr, _f, _n, _t = cm.hand_frame(_s)
    T_REST[_s], F_REST[_s] = vec(_t), vec(_f)
    FIST_OFF[_s] = vec(cm.fist_center(_s)) - vec(_wr)

BEAT = 8              # game.gd ATTACK_FRAME: both sticks come down on the head (held to frame 9)
FR = 33
POLE = {"R": V(-0.8, 0.5, -0.5), "L": V(0.8, 0.5, -0.5)}
POLE_UP = {"R": V(-1.0, 0.1, 0.3), "L": V(1.0, 0.1, 0.3)}
SHOULDER = {"R": vec(J["shoulder_R"]), "L": vec(J["shoulder_L"])}


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(ro, rr, p):
    """A point carried by the root (rest-pose position p) when the root is moved by ro and turned by rr."""
    return ROOT + ro + rr @ (vec(p) - ROOT)


def drum_pose(ro, rr, swing=0.0):
    """The posed drumhead: its centre, its axis and two directions in its plane (toward his right, toward him)."""
    q = Quaternion(rr @ SWING_AX, math.radians(swing))
    hook = body_pt(ro, rr, HOOK)
    H = hook + q @ (rr @ (HEAD - HOOK))
    a = (q @ (rr @ AX)).normalized()
    er = (rr @ V(-1, 0, 0))
    er = (er - a * er.dot(a)).normalized()
    eb = a.cross(er).normalized()
    if eb.dot(rr @ V(0, 1, 0)) < 0:
        eb = -eb
    return H, a, er, eb, q


def stick_grip(arm, side, fist, axis, finger=None, pole=None):
    """The fist (its grip centre) at `fist`, its stick along `axis`, the knuckles toward `finger` (by default the way the
    arm reaches, square to the stick; solve2 replaces that with the solved forearm's own direction)."""
    ax = Vector(axis).normalized()
    if finger is None or (Vector(finger) - ax * Vector(finger).dot(ax)).length < 0.15:
        reach = Vector(fist) - SHOULDER[side] + V(0, -0.15, -0.25)
        finger = reach - ax * reach.dot(ax)
    R = frame_map(T_REST[side], ax, F_REST[side], Vector(finger))
    aims = arm_aims(arm, side, Vector(fist) - R @ FIST_OFF[side], pole=pole or POLE[side])
    aims["hand." + side] = ("frame", T_REST[side], ax, F_REST[side], Vector(finger))
    return aims


def solve2(P_, arm, aims, ro, rr, sc, sticks, poles=None):
    """Solve with the sticks in the fists, twice: the second time each hand's knuckles follow its solved forearm (square
    to the stick), so the wrists bend as little as the stick allows."""
    fingers = {}
    for it in range(3):
        a2 = dict(aims)
        gR, dR, gL, dL = sticks
        a2.update(stick_grip(arm, "R", gR, dR, fingers.get("R"), (poles or {}).get("R")))
        a2.update(stick_grip(arm, "L", gL, dL, fingers.get("L"), (poles or {}).get("L")))
        ch, P = P_.solve(a2, ro, rr, scales=sc)
        for s, d in (("R", dR), ("L", dL)):
            fa = P["forearm." + s].col[1].xyz.normalized()
            ax = Vector(d).normalized()
            fingers[s] = fa - ax * fa.dot(ax)
    return ch, P


def tip_on(H, a, er, eb, dr, db, lift=0.0):
    """A point over the drumhead: dr toward his right, db toward him, lift off the head (the acorn's centre)."""
    return H + er * dr + eb * db + a * (CONTACT + lift)


def strike_dir(side, a, er, eb, phi, beta):
    """A stick coming down onto the head: phi turns it in the head's plane (0: straight across from his side, + toward
    the front), beta its angle down onto the plane."""
    s = -1.0 if side == "R" else 1.0
    inplane = er * (s * math.cos(math.radians(phi))) - eb * math.sin(math.radians(phi))
    return (inplane * math.cos(math.radians(beta)) - a * math.sin(math.radians(beta))).normalized()


def legs(arm, ro, rr, heel=0.0):
    """Feet planted (heel: rises onto the toes, 0..1)."""
    aims = {}
    th = math.radians(8.0) * heel
    for side in ("L", "R"):
        toe, an = vec(J["toe_" + side]), vec(J["ankle_" + side])
        rel = an - toe
        q = Quaternion(V(1, 0, 0), -th)                    # the heel lifts, the foot pivots on its ball
        a_t = toe + q @ rel
        pole = V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a_t, pole=pole))
        aims["foot." + side] = rz(-6 if side == "R" else 6) @ (toe - a_t)
    return aims


def heel_rise(heel):
    toe, an = vec(J["toe_L"]), vec(J["ankle_L"])
    rel = an - toe
    q = Quaternion(V(1, 0, 0), -math.radians(8.0) * heel)
    return (toe + q @ rel) - an


def torso(aims, rr, lean=0.0, side=0.0, chest_tw=0.0, look=0.0, nod=0.0, tilt=0.0):
    """lean: + forward; side: + to his left; look: head turned (+ to his left); nod: + chin up; tilt: + head to his left."""
    aims["spine"] = (rr @ V(side * 0.12, 0.02 - 0.22 * lean, 1.0), chest_tw * 0.4)
    aims["chest"] = (rr @ V(side * 0.16, 0.02 - 0.32 * lean, 1.0), chest_tw * 0.6)
    aims["neck"] = (rr @ V(tilt * 0.4, -0.16 - 0.2 * lean + 0.3 * nod, 1.0), look * 0.35)
    aims["head"] = (rr @ V(tilt, -0.06 + 0.5 * nod, 1.0), look * 0.65)
    aims["clavicle.L"] = rr @ V(1.0, -0.12, 0.0)
    aims["clavicle.R"] = rr @ V(-1.0, -0.12, 0.0)


def smooth_keys(keys, f, fn=ease):
    if f <= keys[0][0]:
        return keys[0][1]
    for (fa, a), (fb, b) in zip(keys, keys[1:]):
        if f <= fb:
            k = fn((f - fa) / float(fb - fa)) if fb > fa else 1.0
            if isinstance(a, Vector):
                return a.lerp(b, k)
            return a + (b - a) * k
    return keys[-1][1]


def dir_lerp(a, b, k):
    return Vector(a).normalized().slerp(Vector(b).normalized(), k)


# ----------------------------------------------------------------------------------------------- poses (drumhead frame)
# The sticks lie square across the fists, so they must cross the forearms: the strikes come down steeply onto the head
# with the forearms reaching forward; held up, the sticks stand upright before his chest (the drill's "recover").
def _seg_gap(p0, p1, q0, q1):
    """The closest approach of two segments (and the parameter along the first)."""
    best = (9.0, 0.0)
    for i in range(41):
        s = i / 40.0
        p = p0.lerp(p1, s)
        d = q1 - q0
        t = max(0.0, min(1.0, (p - q0).dot(d) / max(d.length_squared, 1e-9)))
        g = (p - (q0 + d * t)).length
        if g < best[0]:
            best = (g, s)
    return best


def rest_sticks(H, a, er, eb, rr):
    """The idle: the sticks crossed on the head from either side, the right one lying across it from over its low right
    rim, the left one coming down over it from the high side, its tip on the head beyond."""
    tR = tip_on(H, a, er, eb, -0.085, -0.04)
    dR = (rr @ V(0.99, -0.1, 0.0)).normalized()
    gR = tR - dR * TIP
    tL = tip_on(H, a, er, eb, 0.07, -0.075)
    gL0 = H - er * 0.21 - eb * 0.01 + a * 0.12
    for it in range(6):                                    # the left stick passes just over the right one where they cross
        dL = (tL - gL0).normalized()
        gL = tL - dL * TIP
        gap, s = _seg_gap(gR, gR + dR * (TIP + 0.02), gL, gL + dL * (TIP + 0.02))
        gL0 = gL0 + a * (0.028 - gap) * 1.4
    return gR, dR, gL, dL


def beat_sticks(H, a, er, eb, rr, lift=(0.0, 0.0)):
    """The sticks down on the head (lift: each tip held off it), steep, from either side."""
    dR = (rr @ V(0.5, -0.1, -0.86)).normalized()
    dL = (rr @ V(-0.44, -0.16, -0.88)).normalized()
    tR = tip_on(H, a, er, eb, 0.04, -0.02, lift[0])
    tL = tip_on(H, a, er, eb, -0.045, -0.03, lift[1])
    return tR - dR * TIP, dR, tL - dL * TIP, dL


def ready_sticks(H, a, er, eb, rr):
    """Ready: the fists over the drum, the sticks upright before his chest."""
    bR, _, bL, _ = beat_sticks(H, a, er, eb, rr)
    gR = bR + rr @ V(-0.03, 0.02, 0.0)
    gL = bL + rr @ V(0.02, 0.03, 0.0)
    return gR, (rr @ V(0.1, -0.14, 0.98)).normalized(), gL, (rr @ V(-0.08, -0.14, 0.98)).normalized()


def roll_sticks(H, a, er, eb, rr, kR, kL):
    """The roll: each stick at its strike angle, its fist raised (k: 0 down on the head, 1 a hand's breadth up), the
    raised stick tipped up a little."""
    gR, dR, gL, dL = beat_sticks(H, a, er, eb, rr)
    out = []
    for g, d, k, s in ((gR, dR, kR, 1.0), (gL, dL, kL, -1.0)):
        tilt = Quaternion(rr @ V(0.0, -1.0, 0.0), math.radians(-s * 22.0 * k))     # (the tip lifts outward)
        out += [g + rr @ V(0.0, 0.02 * k, 0.13 * k), tilt @ d]
    return tuple(out)


def high_sticks(H, a, er, eb, rr):
    """Wound up: both fists high, the sticks swung back over his shoulders."""
    gR = H + rr @ V(-0.4, 0.12, 0.6)
    gL = H + rr @ V(0.12, 0.16, 0.68)
    dR = (rr @ V(-0.35, 0.45, 0.82)).normalized()
    dL = (rr @ V(0.22, 0.5, 0.84)).normalized()
    return gR, dR, gL, dL


def lift_sticks(H, a, er, eb, rr):
    """On the way up: the fists rising, the sticks swinging up through the front (tips forward and up)."""
    gR = H + rr @ V(-0.3, 0.06, 0.42)
    gL = H + rr @ V(0.13, 0.1, 0.5)
    return gR, (rr @ V(0.3, -0.72, 0.62)).normalized(), gL, (rr @ V(-0.26, -0.72, 0.64)).normalized()


def swing_sticks(H, a, er, eb, rr):
    """On the way down: the fists dropping fast, the sticks swinging down through the front (tips forward and down)."""
    gR = H + rr @ V(-0.25, 0.07, 0.4)
    gL = H + rr @ V(0.17, 0.1, 0.44)
    return gR, (rr @ V(0.42, -0.74, -0.25)).normalized(), gL, (rr @ V(-0.38, -0.74, -0.3)).normalized()


def flourish_sticks(ro, rr, click=0.0):
    """The flourish: the fists up before his face, elbows out, the sticks crossed above them; click (0..1) brings the
    tips together."""
    gR = body_pt(ro, rr, V(-0.25, -0.44, 1.4))
    gL = body_pt(ro, rr, V(0.25, -0.42, 1.42))
    spread = 0.42 + 0.5 * click                                # (the fists either side of his face, the tips meeting over it)
    dR = (rr @ V(spread, -0.12, 0.9)).normalized()
    dL = (rr @ V(-spread, -0.12, 0.9)).normalized()
    return gR, dR, gL, dL


def mix_sticks(s0, s1, k):
    return (s0[0].lerp(s1[0], k), dir_lerp(s0[1], s1[1], k), s0[2].lerp(s1[2], k), dir_lerp(s0[3], s1[3], k))


# ----------------------------------------------------------------------------------------------- idle
def idle_pose(arm, t):
    w = 2 * math.pi * t
    bob = 0.5 - 0.5 * math.cos(w * 4)                      # four bobs a loop: up on his toes and down
    hum = math.sin(w * 2)
    rise = heel_rise(bob)
    rr = rz(4.0 * math.sin(w))
    ro = V(0.0, rise.y * 0.6, rise.z - 0.006)
    aims = legs(arm, ro, rr, bob)
    torso(aims, rr, lean=0.05, side=0.025 * hum, chest_tw=0.04 * math.sin(w), look=0.12 * math.sin(w + 0.6),
          nod=0.08 + 0.04 * bob, tilt=0.11 * hum)
    H, a, er, eb, q = drum_pose(ro, rr)
    return aims, ro, rr, {}, rest_sticks(H, a, er, eb, rr)


IDLE_POLES = {"R": V(-0.35, 1.0, -0.6), "L": V(0.8, 0.5, -0.5)}


def make_idle(arm, frames=96):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr, sc, sticks = idle_pose(arm, (f % frames) / frames)
        ch, _ = solve2(P, arm, aims, ro, rr, sc, sticks, IDLE_POLES)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- combat
def combat_pose(arm, t):
    w = 2 * math.pi * t
    beat = max(0.0, math.sin(w * 2)) ** 2                  # two little bounces a loop (the beat in his head)
    rr = rz(0.0)
    ro = V(0.0, 0.0, -0.022 - 0.014 * beat)
    aims = legs(arm, ro, rr)
    torso(aims, rr, lean=0.12 + 0.03 * beat, look=0.05 * math.sin(w), nod=-0.02 - 0.04 * beat)
    H, a, er, eb, q = drum_pose(ro, rr)
    gR, dR, gL, dL = ready_sticks(H, a, er, eb, rr)
    tw = 0.02 * math.sin(w * 2)
    return aims, ro, rr, {}, (gR + rr @ V(0, 0, tw), dR, gL - rr @ V(0, 0, tw), dL)


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr, sc, sticks = combat_pose(arm, (f % frames) / frames)
        ch, _ = solve2(P, arm, aims, ro, rr, sc, sticks)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- attack
K_RO = [(0, V(0, 0, -0.022)), (4, V(0, -0.005, -0.03)), (6, V(0, 0.01, -0.006)), (BEAT, V(0, -0.02, -0.055)),
        (9, V(0, -0.02, -0.058)), (12, V(0, 0, -0.03)), (15, V(0, 0.005, -0.01)), (22, V(0, 0.005, -0.012)), (FR, V(0, 0, -0.022))]
K_LEAN = [(0, 0.12), (4, 0.16), (6, -0.06), (BEAT, 0.32), (9, 0.32), (12, 0.12), (16, -0.08), (22, -0.04), (FR, 0.12)]
K_NOD = [(0, -0.02), (4, -0.06), (6, 0.12), (BEAT, -0.16), (9, -0.16), (13, 0.18), (17, 0.26), (22, 0.18), (FR, -0.02)]
K_SWING = [(0, 0.0), (7, 0.0), (BEAT, 4.5), (9, 4.5), (11, -1.5), (13, 0.8), (15, 0.0), (FR, 0.0)]
ROLL = [(1, "R", 0.4), (2, "L", 0.55), (3, "R", 0.75), (4, "L", 0.95)]     # (frame, the stick down on the head, how high the other is up)
K_UP = [(0, 0.0), (4, 0.0), (5, 0.7), (6, 1.0), (7, 0.4), (BEAT, 0.0), (11, 0.0), (14, 1.0), (22, 1.0), (28, 0.3), (FR, 0.0)]   # elbows out


def _poles(k):
    return {s: POLE[s].lerp(POLE_UP[s], max(0.0, min(1.0, k))) for s in ("R", "L")}


def attack_pose(arm, f):
    rr = rz(0.0)
    ro = smooth_keys(K_RO, f)
    aims = legs(arm, ro, rr)
    torso(aims, rr, lean=smooth_keys(K_LEAN, f), nod=smooth_keys(K_NOD, f),
          tilt=0.1 * math.sin(math.pi * max(0.0, min(1.0, (f - 13) / 9.0))), look=0.06 * math.sin(f * 0.4))
    swing = smooth_keys(K_SWING, f)
    H, a, er, eb, q = drum_pose(ro, rr, swing)
    ready = ready_sticks(H, a, er, eb, rr)
    beat = beat_sticks(H, a, er, eb, rr)
    up = smooth_keys(K_UP, f)
    if f == 0:
        sticks = ready
    elif f <= 4:                                                       # the roll, building: one stick down, the other up
        down, k = ROLL[f - 1][1], ROLL[f - 1][2]
        sticks = roll_sticks(H, a, er, eb, rr, *((0.0, k) if down == "R" else (k, 0.0)))
        if f == 1:
            sticks = mix_sticks(ready, sticks, 0.85)
    elif f <= 6:                                                       # wound up high (the sticks swing up through the front)
        sticks = lift_sticks(H, a, er, eb, rr) if f == 5 else high_sticks(H, a, er, eb, rr)
    elif f == 7:                                                       # coming down (through the front)
        sticks = swing_sticks(H, a, er, eb, rr)
    elif f <= 9:                                                       # the beat, held
        sticks = beat
    elif f <= 11:                                                      # the bounce off the head
        sticks = roll_sticks(H, a, er, eb, rr, *(((f - 9) / 2.0,) * 2))
    elif f <= 22:                                                      # the flourish: up before his face, crossed, clicked
        click = math.exp(-((f - 17) / 1.4) ** 2)
        k = smooth_keys([(11, 0.0), (12, 0.3), (13, 0.78), (15, 1.0)], f, fn=lambda x: x)
        sticks = mix_sticks(roll_sticks(H, a, er, eb, rr, 1.0, 1.0), flourish_sticks(ro, rr, click), k)
    else:                                                              # back to ready
        k = ease((f - 22) / float(FR - 22))
        sticks = mix_sticks(flourish_sticks(ro, rr, 0.0), ready, k)
    if abs(swing) > 1e-6:
        aims["drum"] = ("rot", q)
    return aims, ro, rr, {}, sticks, _poles(up)


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, rr, sc, sticks, poles = attack_pose(arm, f)
        ch, _ = solve2(P, arm, aims, ro, rr, sc, sticks, poles)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
