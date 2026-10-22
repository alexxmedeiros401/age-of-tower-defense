"""Isla's clips (keyed frame by frame; the .glb runs them at 24 fps, game.gd CLIP_FPS).

Idle    : (120) one pistol resting on her right shoulder, her left hand on her cutlass's hilt, the other pistol tucked
          through her sash; she shifts her weight from hip to hip, looks about, taps the pistol on her shoulder.
Combat  : (40) the duellist's stance, right side to the robots, right foot forward: the right pistol raised and aimed at
          arm's length, the left one held up by her left shoulder, muzzle to the sky, ready.
Attack  : (FR = 19 frames, inside the 0.8 s cooldown) she fires the right pistol at SHOT (frame 1: the aim held over frames
          0-1, game.gd adds the flash, the smoke and the bullet at the muzzle), the kick throws it up and back, and she
          is back on aim by the end (= Combat).
Ability : Broadside (AB_FR = 64): she tucks the right pistol through her sash, draws the cutlass across her body, raises
          it high and sweeps it down to point at the robots at SIGNAL (frame 31: game.gd brings her ship's guns down on
          them), holds, sheathes it, draws the pistol again and is back on aim (= Combat).
Cheer   : (CH_FR = 50) the pistol tucked, the cutlass drawn and raised high overhead, her head thrown back (a whoop),
          two fist pumps with the left pistol, a hop; the cutlass sheathed again, the pistol drawn, back on aim.

Props are posed in world space (their bones are parentless, so every frame aims them): a pistol is in its fist (following
the hand) or tucked through the sash (following the spine); the cutlass is sheathed (following the root), sliding out along the scabbard as it is
drawn (the right hand gripping it), or in her right fist (blade along the fist's thumb axis, edge to the knuckles)."""
import math
from mathutils import Vector, Quaternion, Matrix
import isla as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

SHOT = 1               # game.gd ATTACK_FRAME: the right pistol fires (the aim held over frames 0-1)
FR = 19                # the Attack's length (0.79 s at 24 fps)
SIGNAL = 31            # Broadside: the cutlass swept down to point at the robots (the guns fire after it)
AB_FR = 64
CH_FR = 50

# ----------------------------------------------------------------------------------------------- rest-pose frames
_PF = {s: cm.pistol_frame(s) for s in ("R", "L")}
G0 = {s: vec(_PF[s][0]) for s in _PF}                   # a pistol's grip middle (the fist's), barrel direction, top
B0 = {s: vec(_PF[s][1]) for s in _PF}
U0 = {s: vec(_PF[s][2]) for s in _PF}
MZ0 = {s: vec(cm.pistol_muzzle(s)) for s in _PF}
WR0 = {s: vec(cm.hand_frame(s)[0]) for s in _PF}
_TK = {s: cm.pistol_tuck(s) for s in _PF}
_cg, _ca, _ce, _cw, _cth = cm.cutlass_rest()
CG0, CA0, CE0 = vec(_cg), vec(_ca), vec(_ce)
_wr, _f, _n, _t = cm.hand_frame("R")
FR0, TR0 = vec(_f), vec(_t)
FIST_R0 = vec(cm.fist_center("R"))
_wl, _fl, _nl, _tl = cm.hand_frame("L")
FL0, TL0 = vec(_fl), vec(_tl)
FIST_L0 = vec(cm.fist_center("L"))


def rigid(g0, a0, b0, g1, a1, b1):
    """The rigid transform taking point g0 to g1 and directions a0 -> a1, b0 -> b1 (as near as possible)."""
    R = frame_map(Vector(a0), Vector(a1), Vector(b0), Vector(b1)).to_4x4()
    return Matrix.Translation(Vector(g1)) @ R @ Matrix.Translation(-Vector(g0))


X_TUCK = {s: rigid(G0[s], B0[s], U0[s], vec(_TK[s][0]), vec(_TK[s][1]), vec(_TK[s][2])) for s in _PF}
X_CUT = rigid(CG0, CA0, CE0, FIST_R0, TR0, FR0)          # the sheathed cutlass -> in her right fist (rest pose)
X_CUT_L = rigid(CG0, CA0, CE0, FIST_L0, -CA0, CE0)        # (unused: a placeholder for a left-hand grip)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def seg(f, a, b):
    """0..1 eased progress of frame f through [a, b]."""
    return smooth01((f - a) / float(b - a))


def mixd(a, b, k):
    a, b = Vector(a).normalized(), Vector(b).normalized()
    return a.slerp(b, k) if a.dot(b) > -0.999 else a.lerp(b, k).normalized()


def mix_m(Ma, Mb, k):
    """Blend two rigid transforms (translation lerp, rotation slerp)."""
    la, ra, _ = Ma.decompose()
    lb, rb, _ = Mb.decompose()
    return Matrix.Translation(la.lerp(lb, k)) @ ra.slerp(rb, k).to_matrix().to_4x4()


def d_root(ro, rr):
    """The root bone's posed delta (armature space) from the root offset and rotation (as Poser.solve builds it)."""
    return Matrix.Translation(ROOT + ro) @ rr.to_matrix().to_4x4() @ Matrix.Translation(-ROOT)


def delta(P_, P, nm):
    return P[nm] @ P_.rest[nm].inverted()


# ----------------------------------------------------------------------------------------------- body
def legs(arm, yaw, lf=(0.18, -0.02), rf=(-0.18, 0.06), lift_l=0.0, lift_r=0.0, open_feet=0.6, turn_l=6.0, turn_r=-10.0):
    """Feet planted under the turned hips: lf / rf are the ankles in the body's own frame."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by), lift, tw in (("L", lf, lift_l, turn_l), ("R", rf, lift_r, turn_r)):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + lift)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * open_feet + tw) @ rest_foot
    return aims


def torso(aims, yaw_chest, lean=0.0, side=0.0, spine_tw=0.0, chest_tw=0.0, neck_tw=0.0, head_tw=0.0, head_tilt=0.0,
          head_up=0.0):
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.22 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.32 * lean, 1.0), chest_tw)
    aims["neck"] = (V(0.0, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


# ----------------------------------------------------------------------------------------------- hands and props
def hand_to(arm, side, H, pole):
    """Aims putting a hand where the rigid transform H (of its rest pose) takes it."""
    aims = arm_aims(arm, side, H @ WR0[side], pole=pole)
    R = H.to_3x3()
    f0, t0 = (FR0, TR0) if side == "R" else (FL0, TL0)
    aims["hand." + side] = ("frame", f0, R @ f0, t0, R @ t0)
    return aims


def pistol_H(side, G, B, U):
    """The hand's transform that puts its pistol's grip at G, its barrel along B, its top toward U."""
    R = frame_map(B0[side], Vector(B), U0[side], Vector(U)).to_4x4()
    return Matrix.Translation(Vector(G)) @ R @ Matrix.Translation(-G0[side])


def tuck_H(P_, P, side):
    """The hand's transform holding the pistol where it sits tucked through the sash (posed)."""
    return delta(P_, P, "spine") @ X_TUCK[side]


def cut_H_draw(Dr, d):
    """The right hand's transform gripping the cutlass slid `d` out of its scabbard (Dr: the root's delta)."""
    return Dr @ Matrix.Translation(-CA0 * d) @ X_CUT.inverted()


def cut_H(G, A, E):
    """The right hand's transform holding the cutlass with its grip's middle at G, blade along A, edge toward E."""
    return rigid(CG0, CA0, CE0, G, A, E) @ X_CUT.inverted()


def prop_aims(P_, P, props):
    """World aims for the props from a solved pose: pistols tucked (following the spine), the cutlass sheathed (the
    root), sliding out (the root), or in the right fist (the hand as posed)."""
    out = {}
    Dr = delta(P_, P, "root")
    for s in ("R", "L"):
        if props.get("pistol_" + s) == "tuck":
            out["pistol_" + s] = ("world", delta(P_, P, "spine") @ X_TUCK[s] @ P_.rest["pistol_" + s])
        else:
            out["pistol_" + s] = ("world", delta(P_, P, "hand." + s) @ P_.rest["pistol_" + s])
    c = props.get("cutlass", "sheath")
    if c == "sheath":
        out["cutlass"] = ("world", Dr @ P_.rest["cutlass"])
    elif c == "hand":
        out["cutlass"] = ("world", delta(P_, P, "hand.R") @ X_CUT @ P_.rest["cutlass"])
    return out


def solve(P_, body, ro, rr, arms_fn, props):
    """Solve the body, then the arms (arms_fn(P) may read the posed body: the sash, the shoulders), then the props."""
    _ch, P = P_.solve(body, ro, rr)
    aims = dict(body)
    aims.update(arms_fn(P))
    _ch, P = P_.solve(aims, ro, rr)
    aims.update(prop_aims(P_, P, props))
    return P_.solve(aims, ro, rr)


# ----------------------------------------------------------------------------------------------- the duellist's stance
YAW = 38.0                                    # right side to the robots
AIM_D = V(0.0, -1.0, -0.07).normalized()      # the right pistol's line (the robots straight ahead, below her)
AIM_POLE = V(-0.6, 0.3, -1.0)
READY_POLE = V(1.0, 0.4, -0.9)


def stance(arm, br=0.0, sway=0.0, lean=0.0, crouch=0.0, chest=0.0, head_up=0.0, lift_l=0.0, lift_r=0.0, yaw=YAW):
    q = rz(yaw)
    aims = legs(arm, yaw, lf=(0.2, 0.15), rf=(-0.19, -0.1), lift_l=lift_l, lift_r=lift_r, turn_l=8.0, turn_r=-30.0)
    ro = V(0.0, 0.0, -0.035 - 0.03 * crouch + 0.004 * br)
    rr = rz(yaw + 1.5 * sway)
    yc = yaw + chest
    torso(aims, yc, lean=0.03 + lean, side=0.03 * sway, spine_tw=math.radians(chest * 0.4), chest_tw=math.radians(chest * 0.6),
          neck_tw=math.radians(-0.42 * yc), head_tw=math.radians(-0.52 * yc), head_tilt=-0.04, head_up=0.04 + head_up)
    qc = rz(yc)
    aims["clavicle.L"] = qc @ V(1.0, 0.0, 0.0)
    aims["clavicle.R"] = qc @ V(-1.0, -0.12, 0.1)
    return aims, ro, rr


def aim_hand(P, kick=0.0, br=0.0, sway=0.0):
    """The right hand at arm's length along the aim; `kick` (0..1) throws the pistol up and back (the recoil)."""
    sh = P["upperarm.R"].translation
    reach = 0.94 * (0.3155 + 0.276)
    wr = sh + AIM_D * reach + V(0.0, 0.0, 0.004 * br) + V(0.006 * sway, 0, 0)
    wr = wr + V(0.0, 0.085, 0.07) * kick
    pitch = -math.radians(40.0) * kick
    B = (Quaternion(V(1, 0, 0), pitch) @ AIM_D).normalized()
    up = V(0.0, 0.0, 1.0)
    U = (up - B * up.dot(B)).normalized()
    Rw = frame_map(B0["R"], B, U0["R"], U).to_4x4()
    # the wrist where the hand's rest offset puts it: H maps the rest wrist to `wr`
    return Matrix.Translation(wr) @ Rw @ Matrix.Translation(-WR0["R"])


def ready_hand(P, yc, br=0.0, raise_=0.0):
    """The left pistol held up by her left shoulder, its muzzle to the sky, ready."""
    q = rz(yc)
    sh = P["upperarm.L"].translation
    G = sh + q @ V(0.14, -0.2, -0.06 + 0.12 * raise_) + V(0, 0, 0.004 * br)
    B = (q @ V(0.3, 0.1, 1.0)).normalized()
    U = (q @ V(0.0, -1.0, 0.0))
    U = (U - B * U.dot(B)).normalized()
    return pistol_H("L", G, B, U)


def combat_pose(arm, P_, t, kick=0.0):
    w = 2 * math.pi * t
    br, sw = math.sin(w * 2), math.sin(w)
    body, ro, rr = stance(arm, br, sw, lean=-0.06 * kick, head_up=0.03 * kick)
    yc = YAW
    def arms_fn(P):
        a = hand_to(arm, "R", aim_hand(P, kick, br, sw), AIM_POLE)
        a.update(hand_to(arm, "L", ready_hand(P, yc, br), READY_POLE))
        return a
    return solve(P_, body, ro, rr, arms_fn, {"cutlass": "sheath"})


def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        ch, _ = combat_pose(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def kick_curve(f):
    """The recoil: nothing until the shot has left (frame 1), up fast by 3.5, eased back down to the aim by 16."""
    if f <= SHOT:
        return 0.0
    if f <= 3.5:
        return smooth01((f - SHOT) / 2.5)
    return 1.0 - smooth01((f - 3.5) / 12.5)


def make_attack(arm, frames=FR):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    for f in range(frames + 1):
        ch, _ = combat_pose(arm, P_, 0.0, kick=kick_curve(f))
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ----------------------------------------------------------------------------------------------- idle
def idle_pose(arm, P_, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    hip = math.sin(w)                                  # her weight from hip to hip
    yaw = -6.0 + 3.0 * math.sin(w)
    aims = legs(arm, yaw, lf=(0.17 + 0.012 * hip, -0.03), rf=(-0.19 + 0.012 * hip, 0.05), open_feet=0.5, turn_l=10.0, turn_r=-16.0)
    ro = V(0.022 * hip, 0.0, -0.012 + 0.004 * br - 0.006 * abs(hip))
    rr = rz(yaw) @ Quaternion(V(0, 1, 0), math.radians(2.5 * hip))
    look = 0.42 * math.sin(w + 0.6) + 0.12 * math.sin(w * 3)
    torso(aims, yaw, lean=-0.02, side=-0.05 * hip, spine_tw=0.03 * math.sin(w), chest_tw=0.04 * math.sin(w),
          neck_tw=0.3 * look, head_tw=0.65 * look, head_tilt=0.04 * hip, head_up=0.06 + 0.03 * br)
    q = rz(yaw)
    aims["clavicle.L"] = q @ V(1.0, 0.0, -0.03)
    aims["clavicle.R"] = q @ V(-1.0, -0.05, 0.12)
    tap = max(0.0, math.sin(w * 4)) ** 4 * (1.0 if 0.25 < t < 0.75 else 0.0)        # two taps of the pistol on her shoulder
    def arms_fn(P):
        # the right pistol resting on her shoulder: the barrel back over it, the grip forward in her fist
        sh = P["upperarm.R"].translation
        qq = rz(yaw)
        B = (qq @ V(-0.13, 0.42 - 0.12 * tap, 1.0)).normalized()
        U = (qq @ V(0.0, 1.0, -0.42))
        U = (U - B * U.dot(B)).normalized()
        G = sh + qq @ V(0.035, -0.297 - 0.02 * tap, -0.14)
        a = hand_to(arm, "R", pistol_H("R", G, B, U), V(-0.7, 0.3, -1.0))
        # the left hand on the cutlass's hilt (sheathed: it rides her hips)
        Dr = delta(P_, P, "root")
        hilt = Dr @ (CG0 - CA0 * 0.012)
        A = (Dr.to_3x3() @ CA0).normalized()
        E = (Dr.to_3x3() @ CE0).normalized()
        R = frame_map(TL0, -A, FL0, E).to_4x4()
        H = Matrix.Translation(hilt) @ R @ Matrix.Translation(-FIST_L0)
        a.update(hand_to(arm, "L", H, V(1.0, 0.5, -0.4)))
        return a
    return solve(P_, aims, ro, rr, arms_fn, {"pistol_L": "tuck", "cutlass": "sheath"})


def make_idle(arm, frames=120):
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        ch, _ = idle_pose(arm, P_, (f % frames) / frames)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


# ----------------------------------------------------------------------------------------------- the cutlass's moves
HIGH = (V(-0.2, -0.02, 2.02), V(0.1, 0.32, 1.0), V(-0.3, -1.0, 0.1))        # raised high (grip, blade dir, edge dir)
POINT = (V(-0.2, -0.7, 1.3), V(0.0, -1.0, -0.12), V(0.0, -0.12, -1.0))     # swept down to point at the robots
OVER = (V(-0.14, -0.05, 2.06), V(-0.05, 0.12, 1.0), V(0.0, -1.0, 0.0))     # the cheer: straight up overhead
LOWER = (V(0.06, -0.42, 1.02), V(0.45, -0.35, -0.82), V(0.2, -0.9, 0.3))   # on the way back: low before her, point down
SALUTE = (V(0.0, -0.48, 1.3), V(0.05, -0.35, 1.0), V(0.0, -1.0, -0.3))   # on the way up: before her face, point up
FRONT_UP = (V(-0.06, -0.52, 1.48), V(0.0, -0.75, 0.66), V(0.0, -0.66, -0.75))  # the cheer's way down: before her, point up-out


def path(f, keys):
    """Piecewise eased blend through [(frame, H), ...]."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (fa, Ha), (fb, Hb) in zip(keys, keys[1:]):
        if f <= fb:
            return mix_m(Ha, Hb, seg(f, fa, fb))
    return keys[-1][1]


def above(H, dz=0.22, dy=-0.07):
    """H lifted up (and a little out): the pistol held over its place in the sash, barrel down."""
    return Matrix.Translation(V(0.0, dy, dz)) @ H


def out_front(H):
    """The pistol held out before her, barrel still down: where it turns between pointing down and pointing ahead."""
    return Matrix.Translation(V(0.0, -0.3, 0.26)) @ H


def cut_frame(spec, Dr):
    """A cutlass target (grip, blade, edge) given in the body's frame (yaw only) -> world, via the root's delta."""
    g, a, e = spec
    R = Dr.to_3x3()
    G = Dr @ g
    A = (R @ a).normalized()
    E = (R @ e)
    E = (E - A * E.dot(A)).normalized()
    return G, A, E


def draw_sequence(arm, P_, P, f, k):
    """The right hand through the cutlass's draw/sheathe: k = keys {name: frame}; returns (aims, cutlass state)."""
    Dr = delta(P_, P, "root")
    pole = V(-0.8, 0.2, -1.0)
    if f < k["grab"]:
        # to the hilt: from the tuck (after the pistol is put away), across her body
        u = seg(f, k["free"], k["grab"])
        H0 = tuck_H(P_, P, "R")
        H1 = cut_H_draw(Dr, 0.0)
        return hand_to(arm, "R", mix_m(H0, H1, u), pole.lerp(V(0.4, 0.6, -1.0), u)), "sheath"
    if f < k["out"]:
        u = seg(f, k["grab"], k["out"])
        return hand_to(arm, "R", cut_H_draw(Dr, 0.62 * u), V(0.4, 0.6, -1.0).lerp(V(-1.0, 0.2, -0.6), u)), ("draw", 0.62 * u)
    return None, "hand"


def make_ability(arm, frames=AB_FR):
    """Broadside: tuck (0-6), to the hilt (6-11), draw (11-17), raise high (17-25), hold (25-28), sweep down to point at
    SIGNAL (28-31), hold (31-40), back to the hip and sheathe (40-50), the pistol drawn (50-56), back on aim (56-64)."""
    P_ = Poser(arm)
    act = new_action(arm, "Ability")
    k = {"tuck": 6, "free": 6, "grab": 11, "out": 17, "high": 25, "hold": 28, "point": SIGNAL, "back": 40, "home": 46, "in": 50,
         "pgrab": 54, "aim": 60}
    for f in range(frames + 1):
        front = seg(f, 0, 12) * (1.0 - seg(f, 54, 62))           # turned to the front while she signals
        yaw = YAW + (8.0 - YAW) * front
        up = seg(f, k["out"], k["high"]) * (1.0 - seg(f, k["hold"], k["point"]))
        lunge = seg(f, k["hold"], k["point"]) * (1.0 - seg(f, k["back"], k["in"]))
        reach = seg(f, k["free"] - 2, k["grab"]) * (1.0 - seg(f, k["grab"] + 2, k["out"] + 2)) + \
            seg(f, k["back"] + 2, k["home"]) * (1.0 - seg(f, k["in"], k["pgrab"]))
        body, ro, rr = stance(arm, 0.0, 0.0, lean=-0.12 * up + 0.16 * lunge + 0.22 * reach, head_up=0.3 * up - 0.02 * lunge - 0.08 * reach,
                              crouch=0.35 * lunge + 0.45 * reach, chest=32.0 * reach, yaw=yaw)
        props = {"cutlass": "sheath"}
        if k["tuck"] <= f < k["pgrab"]:
            props["pistol_R"] = "tuck"
        state = {}
        def arms_fn(P, f=f, yaw=yaw):
            a = hand_to(arm, "L", ready_hand(P, yaw, 0.0, raise_=0.6 * up), READY_POLE)
            Dr = delta(P_, P, "root")
            if f <= k["tuck"]:                                   # the pistol from the aim up over the sash, then in
                u = seg(f, 0, k["tuck"])
                Ht = tuck_H(P_, P, "R")
                a.update(hand_to(arm, "R", path(f, [(0, aim_hand(P)), (k["tuck"] * 0.4, out_front(Ht)), (k["tuck"] * 0.7, above(Ht)), (k["tuck"], Ht)]),
                                 AIM_POLE.lerp(V(-0.8, 0.2, -1.0), u)))
                state["c"] = "sheath"
            elif f < k["out"]:
                aa, c = draw_sequence(arm, P_, P, f, k)
                a.update(aa)
                state["c"] = c
            elif f <= k["back"]:                                  # high, then down to point
                if f <= k["high"]:
                    mid = k["out"] + 0.45 * (k["high"] - k["out"])
                    H = path(f, [(k["out"], cut_H_draw(Dr, 0.62)), (mid, cut_H(*cut_frame(SALUTE, Dr))), (k["high"], cut_H(*cut_frame(HIGH, Dr)))])
                elif f <= k["hold"]:
                    sh = 0.012 * math.sin((f - k["high"]) * 2.4)
                    G, A, E = cut_frame(HIGH, Dr)
                    H = cut_H(G + V(0, 0, sh), A, E)
                elif f <= k["point"]:
                    u = (f - k["hold"]) / float(k["point"] - k["hold"])
                    u = u * u * (3 - 2 * u) if u < 1 else 1.0
                    H = mix_m(cut_H(*cut_frame(HIGH, Dr)), cut_H(*cut_frame(POINT, Dr)), u)
                else:
                    o = 0.02 * math.sin((f - k["point"]) * 0.9) * (1.0 - (f - k["point"]) / 9.0)
                    G, A, E = cut_frame(POINT, Dr)
                    H = cut_H(G + V(0, 0, o), A, E)
                a.update(hand_to(arm, "R", H, V(-1.0, 0.3, -0.6)))
                state["c"] = "hand"
            elif f <= k["in"]:                                    # back to the hip and in
                if f <= k["home"]:
                    u = (f - k["back"]) / float(k["home"] - k["back"])
                    if u < 0.5:
                        H = mix_m(cut_H(*cut_frame(POINT, Dr)), cut_H(*cut_frame(LOWER, Dr)), smooth01(u * 2))
                    else:
                        H = mix_m(cut_H(*cut_frame(LOWER, Dr)), cut_H_draw(Dr, 0.62), smooth01(u * 2 - 1))
                    state["c"] = "hand"
                else:
                    u = seg(f, k["home"], k["in"])
                    H = cut_H_draw(Dr, 0.62 * (1.0 - u))
                    state["c"] = ("draw", 0.62 * (1.0 - u))
                a.update(hand_to(arm, "R", H, V(0.4, 0.6, -1.0)))
            elif f <= k["pgrab"]:                                 # the hand to the pistol in the sash
                u = seg(f, k["in"], k["pgrab"])
                a.update(hand_to(arm, "R", mix_m(cut_H_draw(Dr, 0.0), tuck_H(P_, P, "R"), u), V(-0.8, 0.2, -1.0)))
                state["c"] = "sheath"
            else:                                                 # drawn up out of the sash and back on aim
                u = seg(f, k["pgrab"], k["aim"])
                Ht = tuck_H(P_, P, "R")
                n = k["aim"] - k["pgrab"]
                a.update(hand_to(arm, "R", path(f, [(k["pgrab"], Ht), (k["pgrab"] + 0.3 * n, above(Ht)), (k["pgrab"] + 0.6 * n, out_front(Ht)),
                                                    (k["aim"], aim_hand(P))]),
                                 V(-0.8, 0.2, -1.0).lerp(AIM_POLE, u)))
                state["c"] = "sheath"
            return a
        # the cutlass state is decided by arms_fn (a first call to learn it)
        _c, P0 = P_.solve(body, ro, rr)
        arms_fn(P0)
        props["cutlass"] = "hand" if state.get("c") in ("hand",) or isinstance(state.get("c"), tuple) else "sheath"
        ch, P = solve(P_, body, ro, rr, arms_fn, props)
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_cheer(arm, frames=CH_FR):
    """Tuck (0-5), to the hilt (5-9), draw (9-13), up overhead (13-18), two pumps of her left fist with a hop (18-34),
    the cutlass down and sheathed (34-42), the pistol drawn and back on aim (42-50)."""
    P_ = Poser(arm)
    act = new_action(arm, "Cheer")
    k = {"tuck": 5, "free": 5, "grab": 9, "out": 13, "high": 18, "down": 34, "home": 38, "in": 42, "pgrab": 45, "aim": 50}
    for f in range(frames + 1):
        front = seg(f, 0, 10) * (1.0 - seg(f, 43, 50))
        yaw = YAW + (0.0 - YAW) * front
        up = seg(f, k["out"], k["high"]) * (1.0 - seg(f, k["down"], k["home"]))
        pump = max(0.0, math.sin(math.pi * (f - 18) / 8.0)) if 18 <= f <= 34 else 0.0
        hop = max(0.0, math.sin(math.pi * (f - 19) / 6.0)) * 0.045 if 19 <= f <= 25 else 0.0
        whoop = math.sin(math.pi * min(1.0, max(0.0, (f - 14) / 12.0)))
        reach = seg(f, k["free"] - 2, k["grab"]) * (1.0 - seg(f, k["grab"] + 2, k["out"] + 2)) + \
            seg(f, k["down"] + 2, k["home"]) * (1.0 - seg(f, k["in"], k["pgrab"]))
        body, ro, rr = stance(arm, 0.0, 0.0, lean=-0.14 * up - 0.1 * whoop + 0.22 * reach, head_up=0.45 * up + 0.45 * whoop - 0.08 * reach,
                              crouch=-0.3 * up + 0.45 * reach, chest=32.0 * reach, yaw=yaw)
        ro = ro + V(0.0, 0.0, hop)
        props = {}
        if k["tuck"] <= f < k["pgrab"]:
            props["pistol_R"] = "tuck"
        state = {}
        def arms_fn(P, f=f, yaw=yaw, up=up, pump=pump):
            q = rz(yaw)
            sh = P["upperarm.L"].translation
            # the left fist (with its pistol): from the ready pose up into two pumps
            Hr = ready_hand(P, yaw, 0.0)
            Gp = sh + q @ V(0.1, -0.08, 0.08 + 0.42 * pump)
            Bp = (q @ V(0.2, -0.1, 1.0)).normalized()
            Up = (q @ V(0.0, -1.0, 0.0))
            Up = (Up - Bp * Up.dot(Bp)).normalized()
            a = hand_to(arm, "L", mix_m(Hr, pistol_H("L", Gp, Bp, Up), up), READY_POLE.lerp(V(1.0, 0.2, -0.6), up))
            Dr = delta(P_, P, "root")
            if f <= k["tuck"]:
                u = seg(f, 0, k["tuck"])
                Ht = tuck_H(P_, P, "R")
                a.update(hand_to(arm, "R", path(f, [(0, aim_hand(P)), (k["tuck"] * 0.4, out_front(Ht)), (k["tuck"] * 0.7, above(Ht)), (k["tuck"], Ht)]),
                                 AIM_POLE.lerp(V(-0.8, 0.2, -1.0), u)))
                state["c"] = "sheath"
            elif f < k["out"]:
                aa, c = draw_sequence(arm, P_, P, f, k)
                a.update(aa)
                state["c"] = c
            elif f <= k["down"]:
                G, A, E = cut_frame(OVER, Dr)
                shake = V(0.015 * math.sin(f * 1.3), 0.0, 0.025 * pump)
                mid = k["out"] + 0.45 * (k["high"] - k["out"])
                H = path(f, [(k["out"], cut_H_draw(Dr, 0.62)), (mid, cut_H(*cut_frame(SALUTE, Dr))), (k["high"], cut_H(G + shake, A, E))])
                a.update(hand_to(arm, "R", H, V(-1.0, 0.3, -0.5)))
                state["c"] = "hand"
            elif f <= k["in"]:
                if f <= k["home"]:
                    n = k["home"] - k["down"]
                    H = path(f, [(k["down"], cut_H(*cut_frame(OVER, Dr))), (k["down"] + 0.35 * n, cut_H(*cut_frame(FRONT_UP, Dr))),
                                 (k["down"] + 0.7 * n, cut_H(*cut_frame(LOWER, Dr))), (k["home"], cut_H_draw(Dr, 0.62))])
                    state["c"] = "hand"
                else:
                    u = seg(f, k["home"], k["in"])
                    H = cut_H_draw(Dr, 0.62 * (1.0 - u))
                    state["c"] = ("draw", 0.62 * (1.0 - u))
                a.update(hand_to(arm, "R", H, V(0.4, 0.6, -1.0)))
            elif f <= k["pgrab"]:
                u = seg(f, k["in"], k["pgrab"])
                a.update(hand_to(arm, "R", mix_m(cut_H_draw(Dr, 0.0), tuck_H(P_, P, "R"), u), V(-0.8, 0.2, -1.0)))
                state["c"] = "sheath"
            else:
                u = seg(f, k["pgrab"], k["aim"])
                Ht = tuck_H(P_, P, "R")
                n = k["aim"] - k["pgrab"]
                a.update(hand_to(arm, "R", path(f, [(k["pgrab"], Ht), (k["pgrab"] + 0.3 * n, above(Ht)), (k["pgrab"] + 0.6 * n, out_front(Ht)),
                                                    (k["aim"], aim_hand(P))]),
                                 V(-0.8, 0.2, -1.0).lerp(AIM_POLE, u)))
                state["c"] = "sheath"
            return a
        _c, P0 = P_.solve(body, ro, rr)
        arms_fn(P0)
        props["cutlass"] = "hand" if state.get("c") in ("hand",) or isinstance(state.get("c"), tuple) else "sheath"
        ch, P = solve(P_, body, ro, rr, arms_fn, props)
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
