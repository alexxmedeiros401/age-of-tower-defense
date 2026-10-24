"""Laser Turret clips (game: 24 fps).

Idle   : the turret at rest, its gun dipped a little, drifting slowly on its pedestal; he stands easy behind it, his left
         fist on the left grip, his right on his hip, breathing and scanning the field (a slow look from side to side);
         once he leans in and gives the power cell on the gun's right side two pats with his right palm, glancing at its
         charge window, then straightens again.
Combat : on the grips, aimed: leaning into the gun, both fists round its grips, elbows out, his eyes along the barrel;
         the gun tracks a little from side to side and rides up and down with his breathing.
Attack : (18 frames = 0.75 s, inside the 0.8 s cooldown) his thumbs come down on the violet bar (PRESS, frame 1) and the
         beam fires at SHOT (frame 2: the game's laser leaves the lens's centre along the `lens` bone; the lens flares,
         swelling on its bone, frames 1-5); the gun kicks back on its trunnions, its nose up (frames 3-8, a damped rebound)
         and he rocks back with it; the coil swells; the vent hatch on its top pops open to dump the heat (frames 4-6),
         stays open, and claps shut (frames 11-14); he re-settles on the grips and the aim (the clip ends in the Combat
         pose).

The turret's bones are posed directly ("world" aims): yoke (traversing about the pedestal's axis), gun (elevating about
the trunnions, with the kick), vent (on its hinge); lens and coil ride the gun and scale. His fists are placed on the posed
grips every frame (they follow the kick)."""
import math
from mathutils import Vector, Quaternion, Matrix
import laser as lz
from rig import Poser, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease
from anim_cannon import rz, fwd, rgt, body_pt, wroot, smooth_keys, xform, perp, feet, torso, grip_r, grip_l
from anim_field_gun import fist_rot, palm_rot, hip_fist, body_matrix, blend_m, stance, palm_to_fist

FPS = 24
J = lz.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])
X_, Z_ = V(1.0, 0.0, 0.0), V(0.0, 0.0, 1.0)

COL = V(0.0, lz.MY, 0.0)                       # the pedestal's axis (the yoke traverses about it)
TRUN = vec(lz.TRUN)
GD0, GU0, GX0 = vec(lz.GD), vec(lz.GU), vec(lz.GX_)
HINGE = vec(lz.hinge_pt())
GRIP = {"R": vec(lz.grip_pt(-1, 0.58)), "L": vec(lz.grip_pt(1, 0.58))}
CELL_TOUCH = vec(lz.cell_pt(-0.035, -lz.CELL_R * 0.62, lz.CELL_R * 0.8))     # (rest) where his palm pats the cell
CELL_N = V(-0.62, 0.0, 0.8).normalized()                                       # (rest) the cell's surface normal there

# ---------------------------------------------------------------------------------------------- timing (24 fps)
PRESS = 1          # his thumbs come down on the bar
SHOT = 2           # game.gd ATTACK_FRAME: the beam leaves the lens (its centre: the `lens` bone's head)
VENT0, VENT1 = 4, 6         # the hatch pops open ...
SHUT0, SHUT1 = 11, 14       # ... and claps shut
FR = 18            # 0.75 s (the 0.8 s cooldown is 19.2 frames)

EL_IDLE = -4.0     # the gun's elevation (degrees, + = nose up): at rest ...
EL_C = 1.5         # ... aimed
KICK = 3.6         # the kick at the shot (degrees, nose up; the gun bone can only turn about its trunnions)
REC = 0.0          # (a jolt back would need a translating gun bone: child bones only turn)
VENT_OPEN = 58.0   # the hatch's swing (degrees)


# ---------------------------------------------------------------------------------------------- the turret
def m_yoke(tr):
    return Matrix.Translation(COL) @ Matrix.Rotation(math.radians(tr), 4, "Z") @ Matrix.Translation(-COL)


def m_gun(tr, el, rec=0.0):
    """The gun's rigid motion (rest -> posed): traversed by tr, elevated to el (degrees, nose up), jolted back by rec."""
    return (m_yoke(tr) @ Matrix.Translation(TRUN) @ Matrix.Rotation(-math.radians(el), 4, "X") @ Matrix.Translation(-TRUN)
            @ Matrix.Translation(-GD0 * rec))


def m_vent(Mg, ang):
    """The hatch: its back edge lifted `ang` degrees about its hinge (along its front edge)."""
    return Mg @ Matrix.Translation(HINGE) @ Matrix.Rotation(math.radians(ang), 4, "X") @ Matrix.Translation(-HINGE)


class Rest:
    def __init__(self, arm):
        b = arm.data.bones
        self.m = {n: b[n].matrix_local.copy() for n in ("mount", "yoke", "gun", "vent", "lens", "coil")}


def turret_aims(rest, tr, el, rec=0.0, vent=0.0):
    Mg = m_gun(tr, el, rec)
    return {"yoke": ("world", m_yoke(tr) @ rest.m["yoke"]), "gun": ("world", Mg @ rest.m["gun"]),
            "vent": ("world", m_vent(Mg, vent) @ rest.m["vent"]), "lens": ("world", Mg @ rest.m["lens"]),
            "coil": ("world", Mg @ rest.m["coil"])}, Mg


# ---------------------------------------------------------------------------------------------- his hands
def grip_hand(side, Mg, press=0.0):
    """His fist round grip `side` of the gun placed by Mg: its axis up the grip (the thumb on top, on the bar), the
    knuckles out to his side and a little forward; `press` brings the thumb down (the fist dips)."""
    R3 = Mg.to_3x3()
    up, fw, ac = (R3 @ GU0).normalized(), (R3 @ GD0).normalized(), (R3 @ GX0).normalized()
    out = -ac if side == "R" else ac
    p = Mg @ GRIP[side] - up * (0.007 * press)
    return p, fist_rot(side, up, out * 0.75 + fw * 0.45 - up * 0.1)


def apply_hand(arm, aims, side, fist, R, pole):
    aims.update((grip_r if side == "R" else grip_l)(arm, fist, R, pole=pole))


def blend_hand(a, b, k, lift=0.0):
    (pa, Ra), (pb, Rb) = a, b
    p = pa.lerp(pb, k) + Z_ * (lift * math.sin(math.pi * k))
    return p, Ra.to_quaternion().slerp(Rb.to_quaternion(), k).to_matrix()


def elbow_pole(side, yaw):
    q = rz(yaw)
    return q @ V(-1.0 if side == "R" else 1.0, 0.25, -0.75)


# ---------------------------------------------------------------------------------------------- stations
S_XY, S_YAW = (0.0, 0.03), 0.0               # Combat: square behind the grips
S_STANCE = (1.12, 0.12, -0.1)                # (wide; left foot forward)
I_XY, I_YAW = (0.06, 0.1), -8.0              # Idle: standing easy a step back, a little to the left grip's side


def placed(xy, yaw, tr, z=0.0):
    """His root offset and yaw for standing at xy (turret at rest) facing yaw, carried round the pedestal by tr."""
    p = COL + rz(tr) @ (V(xy[0], xy[1], 0.0) - COL)
    return wroot(p.x, p.y, ROOT.z + z), yaw + tr


def combat_state(t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    tr = 1.6 * math.sin(w)
    el = EL_C + 0.5 * math.sin(w * 2 - 0.6)
    return w, br, tr, el


def combat_pose(arm, t, rest):
    w, br, tr, el = combat_state(t)
    ro, yaw = placed(S_XY, S_YAW, tr, -0.06 + 0.004 * br)
    lf, rf = stance(S_XY, S_YAW, *S_STANCE)
    aims = feet(arm, lf, rf, S_YAW)
    torso(aims, yaw, bend=0.2, side=0.0, chest=0.0, look=yaw + 0.5 * tr, pitch=-0.12 + 0.02 * br, br=br)
    g, Mg = turret_aims(rest, tr, el)
    aims.update(g)
    for side in ("R", "L"):
        p, R = grip_hand(side, Mg)
        apply_hand(arm, aims, side, p, R, elbow_pole(side, yaw))
    return aims, ro, yaw, {"lens": 1.0, "coil": 1.0}


def idle_pose(arm, t, rest):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    pat = 0.0
    if 0.42 < t < 0.74:
        pat = math.sin(math.pi * (t - 0.42) / 0.32) ** 2
    reach = min(1.0, pat * 1.6)
    tr = 1.8 * math.sin(w)
    el = EL_IDLE + 0.4 * math.sin(w * 2)
    ro, yaw = placed(I_XY, I_YAW, tr, -0.015 + 0.005 * br - 0.03 * reach)
    yaw += -12.0 * reach
    lf, rf = stance(I_XY, I_YAW, 1.04, 0.04, -0.04)
    aims = feet(arm, lf, rf, I_YAW)
    scan = (1.0 - reach) * (30.0 * math.sin(w) + 8.0 * math.sin(w * 3 + 0.4))
    look = yaw + 4.0 + scan - 22.0 * reach
    torso(aims, yaw, bend=0.06 + 0.28 * reach, side=0.03 * math.sin(w) - 0.05 * reach, chest=-3.0 + 2.0 * math.sin(w) - 6.0 * reach,
          look=look, pitch=0.02 + 0.02 * br - 0.4 * reach, br=br)
    g, Mg = turret_aims(rest, tr, el)
    aims.update(g)
    q = rz(yaw)
    p, R = grip_hand("L", Mg)
    apply_hand(arm, aims, "L", p, R, elbow_pole("L", yaw))
    hip = hip_fist("R", ro, yaw)
    if reach > 0.0:
        # two pats on the cell: the palm comes down on it, lifts a little and comes down again
        tt = (t - 0.42) / 0.32
        tap = 0.5 - 0.5 * math.cos(2 * math.pi * 2.0 * max(0.0, min(1.0, (tt - 0.3) / 0.4))) if 0.3 < tt < 0.7 else 0.0
        R3 = Mg.to_3x3()
        nrm = (R3 @ CELL_N).normalized()
        c = Mg @ CELL_TOUCH + nrm * (0.012 + 0.035 * tap)
        Rc = palm_rot("R", -nrm, (R3 @ GD0).normalized() * 0.8 + (R3 @ GX0) * 0.3)
        target = (palm_to_fist("R", c, Rc), Rc)
        p, R = blend_hand(hip, target, reach, 0.04)
        apply_hand(arm, aims, "R", p, R, q @ V(-1.0, 0.6, -0.4))
    else:
        apply_hand(arm, aims, "R", hip[0], hip[1], q @ V(-1.0, 0.5, 0.1))
    return aims, ro, yaw, {"lens": 1.0, "coil": 1.0}


def make_idle(arm, frames=120):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, yaw, sc = idle_pose(arm, (f % frames) / frames, rest)
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
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
    finish_action(arm, act, frames, True)
    return act


# ---------------------------------------------------------------------------------------------- the attack
def kick(f):
    """The gun's kick after the shot: (nose up (degrees), jolt back (m)), a damped rebound."""
    if f <= SHOT:
        return 0.0, 0.0
    t = f - SHOT
    if t <= 1.0:
        k = t
    elif t <= 5.0:
        k = 1.0 - ease((t - 1.0) / 4.0)
    elif t <= 9.0:
        k = -0.18 * math.sin(math.pi * (t - 5.0) / 4.0)
    else:
        k = 0.0
    return KICK * k, REC * max(k, 0.0)


def lens_scale(f):
    """The lens's flare: it swells to the shot and shrinks back."""
    return {0: 1.0, 1: 1.2, 2: 1.42, 3: 1.3, 4: 1.14, 5: 1.05}.get(f, 1.0)


def coil_scale(f):
    s = {0: 1.0, 1: 1.08, 2: 1.2, 3: 1.14, 4: 1.08}.get(f, 1.0)
    if VENT0 <= f <= SHUT1:                                    # it hums while the gun vents
        s = max(s, 1.0 + 0.05 * math.sin(math.pi * (f - VENT0) / float(SHUT1 - VENT0)))
    return s


def vent_angle(f):
    if f < VENT0:
        return 0.0
    if f <= VENT1:
        k = (f - VENT0) / float(VENT1 - VENT0)
        return VENT_OPEN * (1.0 - (1.0 - k) ** 2) * (1.08 if f == VENT1 else 1.0)
    if f < SHUT0:
        return VENT_OPEN * (1.0 + 0.04 * math.sin(math.pi * (f - VENT1) / 2.0))
    if f <= SHUT1:
        k = (f - SHUT0) / float(SHUT1 - SHUT0)
        return VENT_OPEN * (1.0 - k * k)
    if f == SHUT1 + 1:
        return 5.0                                              # a little bounce as it claps shut
    return 0.0


def attack_pose(arm, f, rest):
    t0 = f / float(FR)
    w, br, tr, el = combat_state(0.0)
    up, rec = kick(f)
    # his body rocks back with the kick and settles
    shove = 0.0
    if f > SHOT:
        tt = f - SHOT
        shove = 0.016 * math.sin(math.pi * min(1.0, tt / 6.0)) * math.exp(-max(0.0, tt - 3.0) / 4.0)
    ro, yaw = placed(S_XY, S_YAW, tr, -0.06)
    ro = ro + rz(yaw) @ V(0.0, shove, 0.006 * shove / 0.016)
    lf, rf = stance(S_XY, S_YAW, *S_STANCE)
    aims = feet(arm, lf, rf, S_YAW)
    flinch = 0.0
    if f > SHOT:
        flinch = math.sin(math.pi * min(1.0, (f - SHOT) / 5.0)) * math.exp(-max(0.0, f - SHOT - 2.0) / 3.0)
    vlook = 0.0
    if VENT0 <= f <= SHUT1 + 2:                                # a glance down at the venting hatch
        vlook = math.sin(math.pi * (f - VENT0) / float(SHUT1 + 2 - VENT0))
    torso(aims, yaw, bend=0.2 - 0.05 * flinch, chest=-1.5 * flinch, look=yaw + 0.5 * tr + 3.0 * vlook,
          pitch=-0.12 + 0.08 * flinch - 0.12 * vlook, br=0.0, tilt_head=0.03 * flinch)
    g, Mg = turret_aims(rest, tr, el + up, rec, vent_angle(f))
    aims.update(g)
    press = 1.0 if PRESS <= f <= SHOT + 1 else (0.5 if f == SHOT + 2 else 0.0)
    for side in ("R", "L"):
        p, R = grip_hand(side, Mg, press)
        apply_hand(arm, aims, side, p, R, elbow_pole(side, yaw))
    ls = lens_scale(f)
    return aims, ro, yaw, {"lens": (ls, 1.0 + 0.3 * (ls - 1.0), ls), "coil": coil_scale(f)}


def make_attack(arm, frames=FR):
    rest = Rest(arm)
    P = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        aims, ro, yaw, sc = attack_pose(arm, f, rest)
        ch, _ = P.solve(aims, ro, rz(yaw), scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm)]
