"""Boulder Catapult clips (30 fps).

Idle   : the catapult cocked and loaded; she rests her right hand on the trigger lever, left fist on her hip, looks round
         and now and then shades her eyes to look out over the field.
Combat : ready to shoot: crouched a little, gripping the lever, eyes on the target.
Attack : she yanks the lever, the arm whips up and slams into the padded stop bar (the boulder leaves the bucket at
         RELEASE); the windlass spins as its rope pays out; she cranks the arm back down in four pulls on the spokes,
         heaves the top boulder out of the basket by her left foot into the bucket, and takes the lever again.

The machine's bones are posed directly: beam (turns on the axle), cw (the counterweight net, hangs plumb and swings),
haul (the windlass rope: aimed at the arm and stretched to reach it), winch (the drum), lever, boulder and carry (the
boulder she lifts; a free bone moved by offsets)."""
import math
from mathutils import Vector, Quaternion, Matrix
import catapult as cm
from rig import Poser, leg_aims, arm_aims
from anim import new_action, finish_action, lerp, ease

FPS = 30
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
RELEASE = 2


def arm_aims_m(a, cw_swing=0.0, phi=0.35, lever=0.0):
    """Machine pose: arm angle a, counterweight swing (rad), drum turn phi, lever pull (rad)."""
    aims = {}
    aims["beam"] = vec(cm.arm_dir(a))
    aims["cw"] = V(0.0, math.sin(cw_swing), -math.cos(cw_swing))
    h0, h1 = vec(cm.haul_start()), vec(cm.haul_point(a))
    aims["haul"] = h1 - h0
    aims["winch"] = (V(1.0, 0.0, 0.0), phi - 0.35)
    lv = vec(cm.LEVER_T) - vec(cm.LEVER_P)
    aims["lever"] = Matrix.Rotation(lever, 3, "X") @ lv
    L0 = (vec(cm.haul_point(cm.COCK)) - h0).length
    return aims, {"haul": (1.0, (h1 - h0).length / L0, 1.0)}


def lever_top(lever):
    lv = vec(cm.LEVER_T) - vec(cm.LEVER_P)
    return vec(cm.LEVER_P) + Matrix.Rotation(lever, 3, "X") @ lv


def legs(arm, wide=1.0, crouch_fwd=0.0):
    aR = J["ankle_R"] + V(-0.03 * wide, 0.04, 0.0)
    aL = J["ankle_L"] + V(0.03 * wide, -0.03 - crouch_fwd, 0.0)
    aims = {}
    aims.update(leg_aims(arm, "R", aR, pole=V(-0.25, -1, 0.1)))
    aims.update(leg_aims(arm, "L", aL, pole=V(0.25, -1, 0.1)))
    return aims


def torso(aims, lean=0.0, twist=0.0, side=0.0, head_up=0.0, look=0.0):
    aims["spine"] = (V(side * 0.2, 0.04 - 0.3 * lean, 1.0), twist * 0.4)
    aims["chest"] = (V(side * 0.3, 0.02 - 0.4 * lean, 1.0), twist)
    aims["neck"] = V(side * 0.1, -0.3 + 0.4 * head_up + 0.25 * lean, 1.0)
    aims["head"] = (V(side * 0.05, -0.12 + 0.6 * head_up + 0.3 * lean, 1.0), look)


def hand_on_lever(arm, lever, pole=V(-0.6, 0.6, -0.6)):
    top = lever_top(lever)
    return arm_aims(arm, "R", top + V(0.0, 0.06, 0.03), pole=pole, hand_dir=V(0.1, -0.85, -0.5))


def fist_on_hip(arm, br=0.0):
    return arm_aims(arm, "L", V(0.27, 0.0, 0.84 + 0.005 * br), pole=V(1.0, 0.5, 0.1), hand_dir=V(-0.35, 0.25, -1.0))


def machine_ready(aims, sc):
    m, s = arm_aims_m(cm.COCK)
    aims.update(m)
    sc.update(s)


def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm)
    ro = V(0.0, 0.0, -0.01 + 0.006 * br)
    rr = Quaternion((0, 0, 1), math.radians(4 * math.sin(w)))
    shade = max(0.0, math.sin(w * 1.0 - 1.2)) ** 2                 # she shades her eyes and looks out, once a loop
    torso(aims, lean=0.02, twist=0.05 * math.sin(w), head_up=0.06 * br + 0.1 * shade, look=0.45 * math.sin(w) * (1 - shade) - 0.2 * shade)
    aims["clavicle.R"] = V(-1.0, 0.0, 0.05)
    aims["clavicle.L"] = V(1.0, 0.0, 0.05 + 0.2 * shade)
    aims.update(hand_on_lever(arm, 0.0))
    hip = V(0.27, 0.0, 0.84 + 0.005 * br)
    brow = V(0.12, -0.2, 1.62)
    wl = lerp(hip, brow, ease(shade))
    hd = lerp(V(-0.35, 0.25, -1.0), V(-1.0, -0.1, 0.2), ease(shade)).normalized()
    aims.update(arm_aims(arm, "L", wl, pole=lerp(V(1.0, 0.5, 0.1), V(1.0, 0.0, -0.4), shade), hand_dir=hd))
    sc = {"boulder": 1.0, "carry": 1.0}
    machine_ready(aims, sc)
    return aims, ro, rr, sc, {}


def combat_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm, wide=1.15, crouch_fwd=0.05)
    ro = V(0.0, -0.02, -0.05 + 0.008 * br)
    rr = Quaternion((0, 0, 1), math.radians(-8))
    torso(aims, lean=0.18, twist=-0.1, head_up=0.12, look=0.12)
    aims["clavicle.R"] = V(-1.0, -0.05, 0.0)
    aims["clavicle.L"] = V(1.0, -0.05, 0.05)
    aims.update(hand_on_lever(arm, 0.0, pole=V(-0.7, 0.5, -0.5)))
    aims.update(arm_aims(arm, "L", V(0.32, -0.14, 0.9 + 0.006 * br), pole=V(1.0, 0.3, -0.2), hand_dir=V(-0.3, -0.2, -1.0)))
    sc = {"boulder": 1.0, "carry": 1.0}
    machine_ready(aims, sc)
    return aims, ro, rr, sc, {}


# ---------------------------------------------------------------------------------------------- the attack
FR = 72
PULLS = [(14, 22), (22, 30), (30, 38), (38, 46)]      # cranking: four pulls on the spokes
LOAD = (46, 62)                                      # basket -> bucket
STEP = (cm.FIRED - cm.COCK) / len(PULLS)


def arm_angle(f):
    if f <= RELEASE:
        return cm.COCK - 0.04 * f                                          # the lever gives: a tiny dip
    if f <= 6:                                                             # whip up into the stop bar
        k = (f - RELEASE) / (6 - RELEASE)
        return lerp(cm.COCK - 0.08, cm.FIRED + 0.06, k * k)
    if f <= 12:                                                            # bounce off the pad and settle
        k = (f - 6) / 6
        return cm.FIRED - 0.12 * math.sin(k * math.pi) * (1 - k) + 0.06 * (1 - k)
    for i, (a, b) in enumerate(PULLS):                                     # wound down a step per pull
        if f <= b:
            k = (f - a) / (b - a)
            k = ease(min(1.0, k / 0.65))                                    # the drum turns while she pulls, then holds
            return cm.FIRED - STEP * (i + k)
    return cm.COCK


def drum_phi(f):
    """The drum spins back (rope paying out) while the arm flies, then each pull turns it a quarter forward."""
    base = 0.35
    if f <= RELEASE:
        return base
    if f <= 8:
        return base + 2 * math.pi * ease((f - RELEASE) / (8 - RELEASE))
    for i, (a, b) in enumerate(PULLS):
        if f <= b:
            k = ease(min(1.0, (f - a) / ((b - a) * 0.65)))
            return base + 2 * math.pi - (math.pi / 2) * (i + k)
    return base


def cw_swing(f):
    """The counterweight swings forward as it drops, then hangs again."""
    if f <= RELEASE:
        return 0.0
    if f <= 16:
        k = (f - RELEASE) / 14
        return 0.75 * math.sin(k * math.pi * 1.5) * (1 - k)
    for a, b in PULLS:
        if a <= f <= b:
            return 0.08 * math.sin((f - a) / (b - a) * math.pi)
    return 0.0


def make_attack(arm, frames=FR):
    P = Poser(arm)
    act = new_action(arm, "Attack")
    bucket0 = vec(cm.bucket_c(cm.COCK)) + vec(cm.arm_up(cm.COCK)) * 0.085
    carry0 = vec(cm.CARRY_C)
    for f in range(frames + 1):
        a = arm_angle(f)
        lever = -0.55 * ease(min(1.0, f / RELEASE)) if f <= 10 else -0.55 * (1 - ease(min(1.0, (f - 10) / 4)))
        if f >= 62:
            lever = 0.0
        aims = {}
        m, sc = arm_aims_m(a, cw_swing(f), drum_phi(f), lever)
        aims.update(m)
        offs = {}
        sc["boulder"] = 1.0 if (f < RELEASE or f >= LOAD[1] - 2) else 0.0
        sc["carry"] = 1.0
        # ---- her
        rr = Quaternion((0, 0, 1), math.radians(-8))
        ro = V(0.0, -0.02, -0.05)
        wl, wr = None, None
        if f <= 14:                                             # yank the lever, watch the shot fly
            k = min(1.0, f / RELEASE)
            lean = 0.18 - 0.25 * ease(k) if f <= 6 else lerp(-0.07, 0.25, ease((f - 6) / 8))
            look = 0.12
            head = 0.12 + 0.35 * math.sin(min(1.0, f / 10) * math.pi)
            torso(aims, lean=lean, twist=-0.1, head_up=head, look=look)
            aims.update(legs(arm, wide=1.15, crouch_fwd=0.05))
            if f <= 10:
                aims.update(hand_on_lever(arm, lever, pole=V(-0.7, 0.5, -0.5)))
            else:
                k2 = ease((f - 10) / 4)
                top = lever_top(lever) + V(0.0, 0.06, 0.03)
                spoke = vec(cm.spoke_end(drum_phi(f), 1)) + V(0.03, 0.0, 0.0)
                aims.update(arm_aims(arm, "R", lerp(top, spoke, k2), pole=V(-0.7, 0.6, -0.4), hand_dir=V(0.1, -0.85, -0.5)))
            wl = V(0.32, -0.14, 0.9)
            aims.update(arm_aims(arm, "L", wl, pole=V(1.0, 0.3, -0.2), hand_dir=V(-0.3, -0.2, -1.0)))
            ro = V(0.0, -0.02 - 0.04 * min(1.0, f / 3) * (1 if f < 8 else (1 - (f - 8) / 6)), -0.05 - 0.04 * min(1.0, max(0, f - 8) / 6))
        elif f < LOAD[0]:                                       # cranking: right hand on a spoke, left hand on her knee
            i = next(j for j, (aa, bb) in enumerate(PULLS) if f <= bb) if f <= PULLS[-1][1] else len(PULLS) - 1
            pa, pb = PULLS[i]
            u = (f - pa) / (pb - pa)
            phi = drum_phi(f)
            if u <= 0.65:                                       # pulling spoke k (the one starting up-front)
                hand = vec(cm.spoke_end(phi, 1))
            else:                                               # let go, reach for the next one coming up
                kk = ease((u - 0.65) / 0.35)
                hand = lerp(vec(cm.spoke_end(phi, 1)), vec(cm.spoke_end(phi, 2)), kk) + V(0.0, 0.0, 0.05 * math.sin(kk * math.pi))
            effort = math.sin(min(1.0, u / 0.65) * math.pi)
            torso(aims, lean=0.42 - 0.12 * effort, twist=-0.25, side=-0.15, head_up=0.05 - 0.1 * effort, look=-0.25)
            aims.update(legs(arm, wide=1.3, crouch_fwd=0.1))
            ro = V(-0.02, -0.01 + 0.03 * effort, -0.15)
            rr = Quaternion((0, 0, 1), math.radians(-18))
            aims.update(arm_aims(arm, "R", hand + V(0.035, 0.0, 0.0), pole=V(-0.6, 0.8, -0.3), hand_dir=V(0.2, -0.3, -1.0)))
            aims.update(arm_aims(arm, "L", V(0.24, -0.26, 0.6), pole=V(1.0, 0.3, 0.2), hand_dir=V(-0.4, -0.3, -1.0)))
        else:                                                   # heave the boulder from the basket into the bucket
            k = (f - LOAD[0]) / (LOAD[1] - LOAD[0])
            if f >= LOAD[1]:
                k = 1.0
            # the stone's path: up out of the basket, across her chest, down into the bucket
            lift = V(0.16, -0.18, 0.95)
            if k < 0.3:
                kk = ease(k / 0.3)
                c = lerp(carry0, carry0 + V(0, 0, 0.0), kk)            # bend and grip it (it stays in the basket)
                body_turn, lean, crouch = lerp(-18, 30, kk), lerp(0.3, 0.55, kk), lerp(0.15, 0.2, kk)
            elif k < 0.6:
                kk = ease((k - 0.3) / 0.3)
                c = lerp(carry0, lift, kk) + V(0, 0, 0.12 * math.sin(kk * math.pi))
                body_turn, lean, crouch = lerp(30, 0, kk), lerp(0.55, 0.15, kk), lerp(0.2, 0.08, kk)
            elif k < 0.9:
                kk = ease((k - 0.6) / 0.3)
                c = lerp(lift, bucket0 + V(0, 0, 0.1), kk)
                body_turn, lean, crouch = lerp(0, -40, kk), lerp(0.15, 0.6, kk), lerp(0.08, 0.2, kk)
            else:
                kk = ease((k - 0.9) / 0.1)
                c = lerp(bucket0 + V(0, 0, 0.1), bucket0, kk)
                body_turn, lean, crouch = -40, 0.6, 0.2
            if f >= LOAD[1] - 2:
                sc["carry"] = 0.0
            if f >= LOAD[1] + 1:
                sc["carry"] = 1.0                                       # a new top stone in the basket
                c = carry0
            offs["carry"] = c - carry0
            rr = Quaternion((0, 0, 1), math.radians(body_turn * 0.5))
            ro = V(0.0, -0.02, -crouch)
            torso(aims, lean=lean, twist=math.radians(body_turn * 0.6), side=0.2 * math.sin(math.radians(body_turn)), head_up=-0.1, look=math.radians(body_turn * 0.3))
            aims.update(legs(arm, wide=1.3, crouch_fwd=0.05))
            yaw = Quaternion((0, 0, 1), math.radians(body_turn))
            side = yaw @ V(0.11, 0.0, 0.0)
            if f < LOAD[1]:
                aims.update(arm_aims(arm, "R", c - side + V(0, 0.0, 0.02), pole=V(-1.0, 0.3, -0.3), hand_dir=(side + V(0, 0, -0.3)).normalized()))
                aims.update(arm_aims(arm, "L", c + side + V(0, 0.0, 0.02), pole=V(1.0, 0.3, -0.3), hand_dir=(-side + V(0, 0, -0.3)).normalized()))
            else:                                               # back to the lever
                k3 = ease((f - LOAD[1]) / (FR - LOAD[1]))
                top = lever_top(0.0) + V(0.0, 0.06, 0.03)
                aims.update(arm_aims(arm, "R", lerp(bucket0 - side, top, k3), pole=V(-0.7, 0.5, -0.5), hand_dir=V(0.1, -0.85, -0.5)))
                aims.update(arm_aims(arm, "L", lerp(bucket0 + side, V(0.32, -0.14, 0.9), k3), pole=V(1.0, 0.3, -0.2), hand_dir=V(-0.3, -0.2, -1.0)))
                rr = Quaternion((0, 0, 1), math.radians(lerp(body_turn * 0.5, -8, k3)))
                ro = V(0.0, -0.02, lerp(-crouch, -0.05, k3))
                torso(aims, lean=lerp(lean, 0.18, k3), twist=lerp(math.radians(body_turn * 0.6), -0.1, k3), head_up=lerp(-0.1, 0.12, k3), look=lerp(0, 0.12, k3))
        aims["clavicle.R"] = V(-1.0, -0.1, 0.0)
        aims["clavicle.L"] = V(1.0, -0.1, 0.05)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    from anim_ugo import key_constant
    key_constant(act, 'pose.bones["boulder"].scale')
    key_constant(act, 'pose.bones["carry"].scale')
    finish_action(arm, act, frames, False)
    return act


def make_idle(arm, frames=120):
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr, sc, offs = idle_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_combat(arm, frames=40):
    P = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        aims, ro, rr, sc, offs = combat_pose(arm, (f % frames) / frames)
        ch, _ = P.solve(aims, ro, rr, scales=sc, offsets=offs)
        P.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
