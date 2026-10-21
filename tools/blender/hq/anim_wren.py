"""Wren's clips (keyed frame by frame; the .glb runs them at 24 fps, game.gd CLIP_FPS).

Idle    : the longbow upright at her left side, its lower tip just off the ground, her right thumb hooked in her belt;
          she shifts her weight and looks about.
Combat  : at full draw: side-on to the robots, the bow arm out, the string at the corner of her mouth, the yew bent deep.
Attack  : (FR = 18 frames = 0.75 s; her cooldown is 0.8 s and shortens as she ranks up) she looses at RELEASE (frame 1:
          the arrow leaves the string, game.gd spawns it there), her string hand flung back past her ear; down to the
          quiver at her hip, a fresh arrow in her fingers at GRAB, pulled up and swung over to the bow, nocked at NOCK,
          drawn to her jaw by the last frame (= Combat).
Ability : Arrow Rain: she lifts the drawn bow high and shoots three arrows into the sky as fast as she can draw (VOLLEY
          frames: game.gd sends the rain down after them), lowering the bow as she nocks a fourth, and is back at full
          draw by the end.
Cheer   : she faces the front, the bow thrust up overhead in her left fist, two fist pumps with her right, a hop.

The bow is rigid in her left fist ("frame" aims: along the fist's thumb axis, its back along the hand); each limb is two
bones (inner, outer) the clips turn about the bow's cross axis so it bends in an arc as the string is drawn: the bend is
solved each frame so the string keeps its braced length (bend_from). The string's halves are bones on the limbs' tips,
aimed at the nocking point and stretched to it; the arrow is its own bone in her string hand, its scale snapped 0/1."""
import math
from mathutils import Vector, Quaternion
import wren as cm
from rig import Poser, leg_aims, arm_aims, frame_map
from anim import new_action, finish_action, lerp, ease

J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))

_G, _A, _B, _S = cm.bow_frame()
G_REST, A_REST, B_REST = vec(_G), vec(_A), vec(_B)
S_REST = A_REST.cross(B_REST).normalized()
WR_L_REST = vec(cm.hand_frame("L")[0])
MID_REST = vec(cm.string_mid())
HALF_STRING = (MID_REST - vec(cm.bow_tips()[0])).length
_wr, _f, _n, _t = cm.hand_frame("R")
WR_R_REST, F_R, N_R = vec(_wr), vec(_f), vec(_n)
DRAW_REST = vec(cm.draw_point())
_p0, _ax = cm.arrow_axis()
AX_REST = vec(_ax)
_up = AX_REST.cross(N_R).normalized()
SIDE_REST = AX_REST.cross(_up).normalized()
Q_BOT, Q_TOP = vec(cm.Q_BOT), vec(cm.Q_TOP)
ROOT = vec(J["root"])
ANCHOR_LOCAL = vec(cm.hp((-0.13, -0.125, 1.555)))       # (rest pose) by her right jaw: the string hand's anchor

RELEASE = 1           # the frame the arrow leaves the string (game.gd spawns it then)
FR = 18
FOLLOW, GRAB, PULL, NOCK = 3, 7, 9, 12
VOLLEY = (9, 25, 41)  # Arrow Rain: the three shots into the sky
AB_FR = 62
E_UP = math.radians(52.0)


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def rest_len(arm, nm):
    b = arm.data.bones[nm]
    return (b.tail_local - b.head_local).length


def _dir_slerp(a, b, k):
    a, b = Vector(a).normalized(), Vector(b).normalized()
    return a.slerp(b, k) if a.dot(b) > -0.999 else a.lerp(b, k).normalized()


def _path(dirs, k):
    u = k * (len(dirs) - 1)
    i = min(int(u), len(dirs) - 2)
    return _dir_slerp(dirs[i], dirs[i + 1], u - i)


# ----------------------------------------------------------------------------------------------- body
def legs(arm, yaw, spread=1.0, open_feet=0.75, back=0.1):
    """Feet planted under the turned hips (left foot toward the target), toes turned with the body, knees soft."""
    q = rz(yaw)
    aims = {}
    for side, (bx, by) in (("L", (0.17 * spread, -0.02)), ("R", (-0.17 * spread, back))):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]))
        pole = q @ V(0.12 if side == "L" else -0.12, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw * open_feet) @ rest_foot
    return aims


def torso(aims, yaw_chest, lean=0.0, side=0.0, spine_tw=0.0, chest_tw=0.0, neck_tw=0.0, head_tw=0.0, head_tilt=0.0,
          head_up=0.0):
    """Lean / side bend are in the body's own frame (turned by yaw_chest); twists turn each bone about its axis."""
    q = rz(yaw_chest)
    aims["spine"] = (q @ V(side * 0.12, 0.02 - 0.2 * lean, 1.0), spine_tw)
    aims["chest"] = (q @ V(side * 0.16, 0.02 - 0.3 * lean, 1.0), chest_tw)
    aims["neck"] = (V(0.0, -0.16 + 0.3 * head_up, 1.0), neck_tw)
    aims["head"] = (V(head_tilt, -0.06 + 0.5 * head_up, 1.0), head_tw)


# ----------------------------------------------------------------------------------------------- the bow and the string
def bow_rot(A_t, B_t):
    """World rotation of the bow (and the left fist) taking its rest axes to A_t (along the bow) and B_t (its back)."""
    return frame_map(A_REST, A_t, B_REST, B_t)


def bow_hand(arm, G_t, A_t, B_t, pole):
    """Left arm aims putting the fist (the bow's grip) at G_t with the bow standing along A_t, its back toward B_t."""
    R = bow_rot(A_t, B_t)
    wrist = G_t - R @ (G_REST - WR_L_REST)
    aims = arm_aims(arm, "L", wrist, pole=pole)
    aims["hand.L"] = ("frame", A_REST, Vector(A_t), B_REST, Vector(B_t))
    return aims


def hand_q(f_t, n_t):
    return frame_map(F_R, f_t, N_R, n_t).to_quaternion()


def draw_hand_q(arm, D_t, q, pole):
    """Right arm aims putting the drawing fingers' hook (where the string sits) at D_t, the hand turned by q (world)."""
    R = q.to_matrix()
    wrist = D_t - R @ (DRAW_REST - WR_R_REST)
    aims = arm_aims(arm, "R", wrist, pole=pole)
    aims["hand.R"] = ("frame", F_R, R @ F_R, N_R, R @ N_R)
    return aims


def arrow_aim(aims, d_t, side_t):
    aims["arrow"] = ("frame", AX_REST, Vector(d_t).normalized(), SIDE_REST, Vector(side_t))


def bend_from(arm, P, nock):
    """How far each limb bends (radians; the outer bone turns twice as far as the inner) so the string, its middle at
    `nock`, keeps its braced length. P: a pose solved with the limbs straight."""
    out = {"top": 0.0, "bot": 0.0}
    if nock is None:
        return out, S_REST
    Rh = P["hand.L"].to_3x3() @ arm.data.bones["hand.L"].matrix_local.to_3x3().inverted()
    S = (Rh @ S_REST).normalized()
    for nm, sg, tb in (("top", -1.0, "string_top"), ("bot", 1.0, "string_bot")):
        p1 = P["limb_" + nm].translation
        p2 = P["limb_" + nm + "2"].translation
        tip = P[tb].translation
        def tip_at(th, p1=p1, p2=p2, tip=tip, sg=sg):
            q = Quaternion(S, sg * th)
            return p1 + q @ (p2 - p1) + (q @ q) @ (tip - p2)
        if (tip - nock).length <= HALF_STRING:
            continue
        lo, hi = 0.0, math.radians(36.0)
        for _ in range(26):
            m = 0.5 * (lo + hi)
            if (tip_at(m) - nock).length > HALF_STRING:
                lo = m
            else:
                hi = m
        out[nm] = 0.5 * (lo + hi)
    return out, S


def limb_aims(aims, S, bend):
    for nm, sg in (("top", -1.0), ("bot", 1.0)):
        q = Quaternion(S, sg * bend[nm])
        aims["limb_" + nm] = ("rot", q)
        aims["limb_" + nm + "2"] = ("rot", q)


def string_to(aims, scales, P, nock):
    """Aim the two string bones from their (posed) tips to the nocking point and stretch them to reach it."""
    n = Vector(nock)
    for nm in ("string_top", "string_bot"):
        head = P[nm].translation
        aims[nm] = (lambda n: (lambda PP, base: n - base.translation))(n)
        scales[nm] = (1.0, max(0.2, (n - head).length / HALF_STRING), 1.0)


def solve_bow(arm, P_, aims, ro, rr, sc, nock):
    """Solve with the limbs straight; bend them to the string's length; aim the string at the nock; solve again."""
    limb_aims(aims, S_REST, {"top": 0.0, "bot": 0.0})
    for nm in ("string_top", "string_bot"):
        aims.pop(nm, None)
        sc.pop(nm, None)
    ch, P = P_.solve(aims, ro, rr, scales=sc)
    if nock is None:
        return ch, P
    bend, S = bend_from(arm, P, nock)
    limb_aims(aims, S, bend)
    ch, P = P_.solve(aims, ro, rr, scales=sc)
    string_to(aims, sc, P, nock)
    return P_.solve(aims, ro, rr, scales=sc)


# ----------------------------------------------------------------------------------------------- the drawn pose
YAW_ROOT = -50.0
SPINE_TW, CHEST_TW = -6.0, -12.0
YAW_CHEST = YAW_ROOT + SPINE_TW + CHEST_TW       # the way her chest faces
NECK_TW, HEAD_TW = 27.0, 41.0                    # ... and her head turned back to the target (-Y)
A_AIM = V(-0.1, 0.0, 1.0).normalized()          # the bow nearly upright, its top canted a little to her right
F_AIM = V(0.42, -0.9, -0.05).normalized()       # string hand: knuckles toward the bow, thumb up,
N_AIM = V(0.9, 0.42, 0.0).normalized()          # palm toward her jaw
REST_UP, REST_SIDE = 0.045, 0.02                 # the arrow pass: above her fist, on the bow's left side
DRAW_POLE = V(-0.5, 1.0, 0.25)                   # drawing elbow: back along the arrow's line, out and up
BOW_POLE = V(0.6, 0.1, -1.0)
BOW_REACH = 0.96                                 # shoulder-to-wrist distance of the bow arm / its full length


def body_aims(arm, breathe=0.0, sway=0.0, lean=0.04, look_up=0.0):
    aims = legs(arm, YAW_ROOT, spread=1.2)
    ro = V(0.0, 0.0, -0.02 + 0.003 * breathe)
    rr = rz(YAW_ROOT + 1.2 * sway)
    torso(aims, YAW_CHEST, lean=lean, side=-0.05, spine_tw=math.radians(SPINE_TW), chest_tw=math.radians(CHEST_TW),
          neck_tw=math.radians(NECK_TW), head_tw=math.radians(HEAD_TW), head_tilt=-0.06, head_up=0.06 + look_up)
    q = rz(YAW_CHEST)
    aims["clavicle.L"] = q @ V(1.0, -0.1, 0.1 + 0.4 * look_up)
    aims["clavicle.R"] = q @ V(-1.0, 0.05, 0.22 + 0.3 * look_up)
    return aims, ro, rr


def elev_q(elev):
    return Quaternion((1, 0, 0), -elev)          # pitches -Y up toward +Z by `elev`


class Aim:
    """One full-draw geometry: the anchor (the nocking point at full draw, by her jaw), the grip and the bow's axes, the
    body's aims for it, and the string hand's turn at the anchor."""

    def __init__(self, arm, P_, breathe=0.0, sway=0.0, elev=0.0, lean=0.04, look_up=0.0):
        aims, ro, rr = body_aims(arm, breathe, sway, lean, look_up)
        _ch, P = P_.solve(aims, ro, rr)
        head_m = P["head"] @ arm.data.bones["head"].matrix_local.inverted()
        self.anchor = head_m @ ANCHOR_LOCAL
        self.chest_m = P["chest"] @ arm.data.bones["chest"].matrix_local.inverted()
        self.root_m = P["root"] @ arm.data.bones["root"].matrix_local.inverted()
        shoulder = P["upperarm.L"].translation
        qe = elev_q(elev)
        self.fwd = qe @ V(0.0, -1.0, 0.0)                         # the arrow's flight
        A = (qe @ A_AIM).normalized()
        B = self.fwd
        R = bow_rot(A, B)
        c = -(R @ (G_REST - WR_L_REST))
        L = BOW_REACH * (rest_len(arm, "upperarm.L") + rest_len(arm, "forearm.L"))
        g0 = self.anchor - A * REST_UP - V(1, 0, 0) * REST_SIDE
        w0 = g0 + c - shoulder
        b = w0.dot(self.fwd)
        s = -b + math.sqrt(max(b * b - w0.length_squared + L * L, 0.0))
        self.G, self.A, self.B = g0 + self.fwd * s, A, B
        self.rest_pt = self.G + A * REST_UP + V(1, 0, 0) * REST_SIDE
        self.aims, self.ro, self.rr = aims, ro, rr
        self.hq_draw = (qe @ hand_q(F_AIM, N_AIM))
        self.elev = elev

    def braced_mid(self):
        """Where the braced string's middle is, the bow held as at full draw."""
        R = bow_rot(self.A, self.B)
        return self.G + R @ (MID_REST - G_REST)

    def quiver(self):
        """The quiver's mouth and axis on her turned hips (it is rigid on the root bone)."""
        top = self.root_m @ Q_TOP
        bot = self.root_m @ Q_BOT
        return top, (top - bot).normalized()


def drawn_aims(arm, g):
    aims = dict(g.aims)
    aims.update(bow_hand(arm, g.G, g.A, g.B, pole=BOW_POLE))
    aims.update(draw_hand_q(arm, g.anchor, g.hq_draw, pole=DRAW_POLE))
    arrow_aim(aims, g.rest_pt - g.anchor, g.A)
    return aims


def shot_frame(arm, P_, g, t, T, body=None):
    """The pose t frames into one shot cycle at geometry g: drawn at 0, loosed at RELEASE, an arrow from the quiver
    at GRAB, pulled out (PULL), swung to the bow and nocked (NOCK), drawn again by T. Returns (channels, sc)."""
    body = body or g
    aims = dict(body.aims)
    ro, rr = body.ro, body.rr
    sc = {"arrow": 1.0}
    nock = None
    q_top, q_ax = g.quiver()
    out_dir = (g.root_m.to_3x3() @ V(-1.0, 0.0, 0.0)).normalized()    # her right hip's outward side
    D_follow = g.anchor + g.fwd * -0.12 + V(-0.07, 0.0, 0.03)
    hq_follow = (elev_q(g.elev) @ hand_q(V(0.25, -0.9, 0.2), V(0.6, 0.3, 0.75)))
    D_grab = q_top + q_ax * 0.22                                       # fingers on the nocks above the mouth
    D_pull = q_top + q_ax * 0.66 + out_dir * 0.04
    hq_grab = hand_q(-q_ax, -out_dir)
    hq_pull = hand_q(_dir_slerp(-q_ax, V(0, 0, 1), 0.35), _dir_slerp(-out_dir, -g.fwd, 0.3))
    # (the string at brace, the bow at arm's length, is out of her string hand's reach: she brings the bow in toward
    # her while she reloads and nocks, and pushes it out again as she draws)
    inn = g.fwd * -0.3 + V(0, 0, -0.05)
    R0 = bow_rot(g.A, g.B)
    D_nock = g.G + inn + R0 @ (MID_REST - G_REST)
    G_off = V(0, 0, 0)
    A_t = g.A
    adir = None
    pole = DRAW_POLE
    if t <= 0:
        D, hq = g.anchor, g.hq_draw
        nock = g.anchor
    elif t <= FOLLOW:                                                   # loosed: the hand flung back past her ear
        k = ease((t - RELEASE) / float(FOLLOW - RELEASE))
        D = g.anchor.lerp(D_follow, 0.6 + 0.4 * k)
        hq = g.hq_draw.slerp(hq_follow, 0.65 + 0.35 * k)
        sc["arrow"] = 0.0
        kick = math.sin(min(1.0, (t - 0.5) / 2.5) * math.pi)
        A_t = (g.A + g.fwd * 0.2 * kick).normalized()
        G_off = g.fwd * 0.015 * kick + V(0, 0, -0.015 * kick)
    elif t <= GRAB:                                                     # down to the quiver at her hip
        k = ease((t - FOLLOW) / float(GRAB - FOLLOW))
        D = D_follow.lerp(D_grab, k) + out_dir * (0.08 * math.sin(k * math.pi))
        hq = hq_follow.slerp(hq_grab, k)
        sc["arrow"] = 1.0 if t >= GRAB else 0.0
        adir = -q_ax
        pole = V(-1.0, 0.4, -0.2)
        G_off = inn * (0.6 * k)
    elif t <= PULL:                                                     # pulled up out of it
        k = ease((t - GRAB) / float(PULL - GRAB))
        D = D_grab.lerp(D_pull, k)
        hq = hq_grab.slerp(hq_pull, k)
        adir = _dir_slerp(-q_ax, (-q_ax).lerp(g.fwd, 0.4), k)
        pole = V(-1.0, 0.4, -0.2).lerp(DRAW_POLE, k)
        G_off = inn * (0.6 + 0.4 * k)
    elif t <= NOCK:                                                     # swung over to the bow, its tip forward, nocked
        k = ease((t - PULL) / float(NOCK - PULL))
        D = D_pull.lerp(D_nock, k) + V(0, 0, 0.06 * math.sin(k * math.pi))
        hq = hq_pull.slerp(g.hq_draw, k)
        G_off = inn
        down_fwd = (g.fwd * 0.75 + V(0, 0, -0.66)).normalized()
        adir = _path([(-q_ax).lerp(g.fwd, 0.4).normalized(), down_fwd, (g.rest_pt + inn - D_nock).normalized()], k)
        if t >= NOCK:
            nock = D_nock
            adir = None
    else:                                                               # drawn to her jaw as the bow goes out again
        k = ease((t - NOCK) / float(T - NOCK))
        G_off = inn * (1.0 - k)
        D = D_nock.lerp(g.anchor, k)
        hq = g.hq_draw
        nock = D
    aims.update(bow_hand(arm, g.G + G_off, A_t, g.B, pole=BOW_POLE))
    aims.update(draw_hand_q(arm, D, hq, pole=pole))
    if adir is None:
        arrow_aim(aims, g.rest_pt + G_off - (nock if nock is not None else D), g.A)
    else:
        side = Vector(adir).cross(V(1, 0, 0))
        arrow_aim(aims, adir, side.normalized() if side.length > 1e-3 else V(0, 0, 1))
    ch, _ = solve_bow(arm, P_, aims, ro, rr, sc, nock)
    return ch


# ----------------------------------------------------------------------------------------------- clips
def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    aims = legs(arm, -10.0, spread=0.95, open_feet=0.5, back=0.06)
    ro = V(0.0, 0.0, -0.008 + 0.005 * br)
    rr = rz(-10.0 + 3.0 * math.sin(w))
    look = 0.4 * math.sin(w) + 0.12 * math.sin(w * 3)
    torso(aims, -10.0, lean=0.0, side=0.02 * math.sin(w), spine_tw=0.03 * math.sin(w), chest_tw=0.05 * math.sin(w),
          neck_tw=0.3 * look, head_tw=0.7 * look, head_up=0.05 + 0.04 * br)
    q = rz(-10.0)
    aims["clavicle.L"] = q @ V(1.0, 0.0, 0.0)
    aims["clavicle.R"] = q @ V(-1.0, 0.0, 0.03)
    # the bow upright at her left side, its lower tip just off the ground, its back turned out
    G = V(0.37, -0.08, 0.9 + 0.01 * math.sin(w * 2 + 0.6))
    A = V(0.06, -0.18, 1.0).normalized()
    B = V(0.9, -0.42, 0.0)
    B = (B - A * B.dot(A)).normalized()
    aims.update(bow_hand(arm, G, A, B, pole=V(1.0, 0.4, -0.3)))
    # right thumb hooked in her belt, in front of the quiver
    aims.update(arm_aims(arm, "R", V(-0.17, -0.215, 0.955 + 0.003 * br), pole=V(-1.0, 0.3, 0.0), hand_dir=V(0.15, -0.25, -0.95)))
    return aims, ro, rr


def make_idle(arm, frames=120):
    P_ = Poser(arm)
    act = new_action(arm, "Idle")
    for f in range(frames + 1):
        aims, ro, rr = idle_pose(arm, (f % frames) / frames)
        sc = {"arrow": 0.0}
        ch, _ = solve_bow(arm, P_, aims, ro, rr, sc, None)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def combat_state(t):
    w = 2 * math.pi * t
    return math.sin(w * 2), 0.6 * math.sin(w)


def make_combat(arm, frames=40):
    P_ = Poser(arm)
    act = new_action(arm, "Combat")
    for f in range(frames + 1):
        br, sw = combat_state((f % frames) / frames)
        g = Aim(arm, P_, breathe=br, sway=sw)
        sc = {"arrow": 1.0}
        ch, _ = solve_bow(arm, P_, drawn_aims(arm, g), g.ro, g.rr, sc, g.anchor)
        P_.key(ch, f)
    finish_action(arm, act, frames, True)
    return act


def make_attack(arm, frames=FR):
    P_ = Poser(arm)
    act = new_action(arm, "Attack")
    br0, sw0 = combat_state(0.0)
    g = Aim(arm, P_, breathe=br0, sway=sw0)
    for f in range(frames + 1):
        P_.key(shot_frame(arm, P_, g, f, frames), f)
    _constant_scale(act, "arrow")
    finish_action(arm, act, frames, False)
    return act


def make_ability(arm, frames=AB_FR):
    """Arrow Rain: up to the sky (0-8, still drawn), three shots (VOLLEY), down again while nocking the fourth (41-56),
    held at full draw (56-62)."""
    P_ = Poser(arm)
    act = new_action(arm, "Ability")
    br0, sw0 = combat_state(0.0)
    level = Aim(arm, P_, breathe=br0, sway=sw0)
    up = Aim(arm, P_, elev=E_UP, lean=-0.1, look_up=0.32)
    cyc = VOLLEY[1] - VOLLEY[0]                                  # 16 frames a shot
    for f in range(frames + 1):
        if f <= VOLLEY[0] - 1:                                   # raise the drawn bow to the sky
            k = ease(f / float(VOLLEY[0] - 1))
            body_up = Aim(arm, P_, breathe=br0, sway=sw0 * (1 - k), elev=E_UP * k, lean=0.04 - 0.14 * k, look_up=0.32 * k)
            ch = shot_frame(arm, P_, body_up, 0, cyc)
        elif f < VOLLEY[2]:                                      # the first two shots and their reloads
            t = (f - VOLLEY[0] + 1) % cyc if f < VOLLEY[1] else f - VOLLEY[1] + 1
            ch = shot_frame(arm, P_, up, t, cyc)
        elif f <= VOLLEY[2] + cyc:                               # the third, then down to level while reloading
            t = f - VOLLEY[2] + 1
            k = ease(max(0.0, min(1.0, (f - VOLLEY[2] - 2) / float(cyc - 2))))
            body = Aim(arm, P_, breathe=br0, sway=sw0 * k, elev=E_UP * (1 - k), lean=-0.1 + 0.14 * k, look_up=0.32 * (1 - k))
            ch = shot_frame(arm, P_, body, min(t, cyc), cyc)
        else:                                                    # held at full draw (= Combat)
            ch = shot_frame(arm, P_, level, 0, cyc)
        P_.key(ch, f)
    _constant_scale(act, "arrow")
    finish_action(arm, act, frames, False)
    return act


def make_cheer(arm, frames=40):
    """She turns to the front; the bow thrust up overhead (level, its back to the sky) in her left fist; two fist pumps
    with her right, a hop between them; the bow brought down to her side again."""
    P_ = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        u = f / float(frames)
        up = ease(min(1.0, f / 7.0)) * (1.0 - ease(max(0.0, (f - 30) / 10.0)))
        hop = max(0.0, math.sin(math.pi * (f - 12) / 10.0)) if 12 <= f <= 22 else 0.0
        aims = legs(arm, -10.0 * (1 - up), spread=1.0, open_feet=0.5, back=0.03)
        ro = V(0.0, 0.0, -0.01 + 0.06 * hop - 0.02 * up * (1 - hop))
        rr = rz(-10.0 * (1 - up))
        torso(aims, -10.0 * (1 - up), lean=-0.06 * up, side=0.03 * up, head_up=0.05 + 0.25 * up)
        aims["clavicle.L"] = V(1.0, 0.0, 0.35 * up)
        aims["clavicle.R"] = V(-1.0, 0.0, 0.2 * up)
        # the bow: from her side up overhead, level, its back to the sky
        G0, A0 = V(0.37, -0.08, 0.9), V(0.06, -0.18, 1.0).normalized()
        B0 = V(0.9, -0.42, 0.0)
        B0 = (B0 - A0 * B0.dot(A0)).normalized()
        G1, A1, B1 = V(0.18, -0.06, 2.1), V(1.0, 0.0, 0.08).normalized(), V(0.0, -0.35, 1.0).normalized()
        G = G0.lerp(G1, up) + V(0, 0, 0.04 * hop)
        A = _dir_slerp(A0, A1, up)
        B = _dir_slerp(B0, B1, up)
        B = (B - A * B.dot(A)).normalized()
        aims.update(bow_hand(arm, G, A, B, pole=V(1.0, 0.2, -0.4).lerp(V(1.0, 0.4, 0.2), up)))
        # right fist: pumps up at 10 and 22, down between
        pump = 0.5 - 0.5 * math.cos(2 * math.pi * min(1.0, max(0.0, (f - 4) / 24.0)) * 2)
        lo_w = V(-0.17, -0.215, 0.955)
        hi_w = V(-0.42, -0.14, 1.7)
        mid_w = V(-0.36, -0.16, 1.42)
        wr = lo_w.lerp(mid_w, up).lerp(hi_w, pump * up) + V(0, 0, 0.04 * hop)
        aims.update(arm_aims(arm, "R", wr, pole=V(-1.0, 0.4, -0.3), hand_dir=V(0.05, -0.15, -1.0).lerp(V(0.05, 0.0, 1.0), up)))
        sc = {"arrow": 0.0}
        ch, _ = solve_bow(arm, P_, aims, ro, rr, sc, None)
        P_.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


def _constant_scale(act, bone):
    """The arrow appears / vanishes at once (constant interpolation on the bone's scale)."""
    path = 'pose.bones["%s"].scale' % bone
    fcs = []
    try:
        fcs = [fc for fc in act.fcurves]
    except Exception:
        pass
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                fcs += list(cb.fcurves)
    for fc in fcs:
        if fc.data_path == path:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
