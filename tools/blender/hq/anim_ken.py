"""Dr. Ken Ito's clips (keyed in frames; the game plays them at CLIP_FPS 24).

Idle    : standing easy, reading the tablet on his left forearm (raised across his chest, the screen turned up to his
          face), his gauntlet fist hanging at his side; halfway through the loop he lowers the tablet, looks up and about
          with a grin and brings the gauntlet up before his chest, turning it to check it, then goes back to the tablet.
Combat  : the ready stance: feet wide, knees bent, turned a little to his right; his left forearm raised before him (the
          tablet up), the gauntlet fist at his right hip, the plate's face to the robots; he bobs on his knees.
Attack  : (22 frames = 0.92 s, inside 1.1 s) the ground pound: he rises and heaves the gauntlet up over his right shoulder
          (0-4), drops into a deep lunge and slams the plate into the ground before him (4-9): HIT (frame 9, held to 11:
          the game's pulse leaves `plate`'s tail, on the ground), then rises back to the ready stance (11-22).
Ability : EMP Grenade (66 frames): he squares up to the robots, raises the tablet and reaches to the pouch on the right
          of his belly; at GRAB (14) the grenade is in his fist (the `grenade` bone is shown from here); he brings it up
          and touches it to the tablet's screen: ARM (26, held to 31: its glowing band swells, `core`); he cocks it back
          beside his head and lobs it overarm a short way in front of him: RELEASE (43: the game flies its grenade from the
          `grenade` bone's head to the ground about 1.8 m before him; his is hidden from the next frame), follows through
          and comes back to the ready stance.
Cheer   : (rank up) the gauntlet punched up at the sky and pumped twice, his left fist on his hip, a little hop, grinning.

The arms are posed by their fists ("frame" aims for the hands, the forearms turned with them so the wrists only bend):
the right fist by the seismic plate's face (PF_OFF), the left by the wrist."""
import math
from mathutils import Vector, Quaternion, Matrix
import ken as cm
from rig import Poser, leg_aims, frame_map, two_bone, bone_len
from anim import new_action, finish_action, lerp, ease

FPS = 24
J = cm.J
V = lambda *a: Vector(a)
vec = lambda a: Vector((float(a[0]), float(a[1]), float(a[2])))
ROOT = vec(J["root"])

HAND = {}
for _s in "RL":
    _wr, _f, _n, _t = cm.hand_frame(_s)
    _el = vec(J["elbow_" + _s])
    _fa = (vec(_wr) - _el).normalized()
    _nn = vec(_n)
    HAND[_s] = dict(wr=vec(_wr), f=vec(_f), n=_nn, t=vec(_t), fa=_fa, np=(_nn - _fa * _nn.dot(_fa)).normalized(),
                    fist=vec(cm.fist_center(_s)) - vec(_wr))
PF_OFF = vec(cm.plate_face()) - HAND["R"]["wr"]           # wrist -> the plate's face (rest)
_G, _A, _C = cm.grenade_frame()
GC_OFF = vec(_C) - HAND["R"]["wr"]                         # wrist -> the grenade's middle (rest)
G_AX = vec(_A)                                             # the grip's axis (rest) = the thumb axis
_tc, _tR = cm.tablet_frame()
SCREEN_REST = vec(_tc) + vec(_tR[:, 2]) * (cm.TAB_HALF[2] + 0.002)
SCREEN_N_REST = vec(_tR[:, 2])

HIT = 9               # Attack: the plate on the ground (held to 11)
FR = 22               # the Attack's length (0.92 s at 24 fps)
GRAB = 14             # Ability: the grenade in his fist
ARM = 26              # ... touched to the tablet: armed (held to 31)
RELEASE = 43          # ... lobbed: it leaves his hand
AB_FR = 66
CH_FR = 48
I_FR = 96
C_FR = 40


def rz(deg):
    return Quaternion((0, 0, 1), math.radians(deg))


def body_pt(p, ro, yaw):
    return ROOT + ro + rz(yaw) @ (vec(p) - ROOT)


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mixd(a, b, k):
    return a.normalized().lerp(b.normalized(), k).normalized()


def mixv(a, b, k):
    return a.lerp(b, k)


def bez_p(a, b, c, k):
    return a.lerp(b, k).lerp(b.lerp(c, k), k)


# ---------------------------------------------------------------------------------------------- limbs
def arm_aims(arm, side, wrist, pole, hf, hn):
    """The arm to `wrist` (two-bone IK toward `pole`), the hand's fingers along hf, its palm toward hn; the forearm turned
    with the hand (its palm side toward hn), so the wrist only bends."""
    la, lb = bone_len(arm, "upperarm." + side), bone_len(arm, "forearm." + side)
    H = HAND[side]
    st = {}
    wrist = Vector(wrist)
    hf, hn = Vector(hf).normalized(), Vector(hn).normalized()
    def upper(P, base):
        sh = base.translation
        e = two_bone(sh, wrist, la, lb, Vector(pole))
        st["el"] = e
        return e - sh
    def fore(P, base):
        d = wrist - st["el"]
        dn = d.normalized()
        nd = hn - dn * hn.dot(dn)
        if nd.length < 1e-3:
            return d
        return ("frame", H["fa"], d, H["np"], nd)
    return {"upperarm." + side: upper, "forearm." + side: fore, "hand." + side: ("frame", H["f"], hf, H["n"], hn)}


def hand_rot(side, hf, hn):
    return frame_map(HAND[side]["f"], Vector(hf), HAND[side]["n"], Vector(hn))


def fist_at(arm, side, center, hf, hn, pole):
    R = hand_rot(side, hf, hn)
    return arm_aims(arm, side, Vector(center) - R @ HAND[side]["fist"], pole, hf, hn)


def plate_at(arm, face, hf, hn, pole):
    """The right fist placed by the seismic plate's face."""
    R = hand_rot("R", hf, hn)
    return arm_aims(arm, "R", Vector(face) - R @ PF_OFF, pole, hf, hn)


def grenade_at(arm, center, axis, hf_hint, pole):
    """The right fist holding the grenade with its middle at `center`, its grip's axis (toward the canister) along `axis`,
    the fingers as near `hf_hint` as can be."""
    R = frame_map(G_AX, Vector(axis), HAND["R"]["f"], Vector(hf_hint))
    hf, hn = R @ HAND["R"]["f"], R @ HAND["R"]["n"]
    return arm_aims(arm, "R", Vector(center) - R @ GC_OFF, pole, hf, hn)


def feet(arm, yaw, lf=(0.2, -0.03), rf=(-0.2, 0.04), lift=(0.0, 0.0), turn=(10.0, -10.0)):
    q = rz(yaw)
    aims = {}
    for side, (bx, by), up, tw in (("L", lf, lift[0], turn[0]), ("R", rf, lift[1], turn[1])):
        off = q @ V(bx, by - ROOT.y, 0.0)
        a = V(ROOT.x + off.x, ROOT.y + off.y, float(J["ankle_" + side][2]) + up)
        pole = q @ V(0.15 if side == "L" else -0.15, -1.0, 0.1)
        aims.update(leg_aims(arm, side, a, pole=pole))
        rest_foot = vec(J["toe_" + side]) - vec(J["ankle_" + side])
        aims["foot." + side] = rz(yaw + tw) @ (rest_foot + V(0, 0, -up * 0.6))
    return aims


def torso(aims, yaw, bend=0.0, side=0.0, chest=0.0, look=None, pitch=0.0, roll=0.0):
    q = rz(yaw)
    qc = rz(yaw + chest)
    def tilt(fb, fs):
        return V(math.sin(fs), -math.sin(fb), math.cos(fb) * math.cos(fs))
    aims["spine"] = (q @ tilt(bend * 0.45, side * 0.45), math.radians(chest * 0.4))
    aims["chest"] = (qc @ tilt(bend, side), math.radians(chest * 0.6))
    look = yaw + chest if look is None else look
    tw = math.radians(look - yaw - chest)
    aims["neck"] = (rz(yaw + chest + (look - yaw - chest) * 0.4) @ V(math.sin(roll) * 0.5, -0.1 - 0.2 * min(bend, 0.9) + 0.25 * pitch, 1.0), tw * 0.4)
    aims["head"] = (rz(look) @ V(math.sin(roll), -0.04 + 0.7 * pitch, 1.0), tw * 0.6)
    aims["clavicle.L"] = qc @ V(1.0, -0.03, 0.02)
    aims["clavicle.R"] = qc @ V(-1.0, -0.03, 0.02)


# ---------------------------------------------------------------------------------------------- the tablet arm
READ_WR = V(0.1, -0.31, 1.18)                  # the left wrist, reading (body space)
READ_F = V(-0.82, -0.52, 0.18).normalized()    # the hand along the forearm, across his chest
READ_N = V(0.25, -0.12, -0.96).normalized()    # the palm down: the screen up, toward his face
READ_POLE = V(1.0, 0.15, -0.55)


def tablet_params(ro, yaw, lift=0.0, fwd=0.0, out=0.0, turn=0.0):
    """(wrist, pole, fingers, palm) of the left arm raised across his chest, the tablet's screen turned up to his face
    (`turn` rolls it toward the robots, radians)."""
    q = rz(yaw)
    w = body_pt(READ_WR + V(out, -fwd, lift), ro, yaw)
    hn = Quaternion(READ_F, turn) @ READ_N
    return w, q @ READ_POLE, q @ READ_F, q @ hn


def tablet_arm(arm, ro, yaw, **kw):
    return arm_aims(arm, "L", *tablet_params(ro, yaw, **kw))


# ---------------------------------------------------------------------------------------------- idle
def idle_pose(arm, t):
    w = 2 * math.pi * t
    br = math.sin(w * 2)
    up = smooth01((t - 0.42) / 0.08) * (1.0 - smooth01((t - 0.8) / 0.08))     # looking up, checking the gauntlet
    yaw = 2.0 * math.sin(w) + 6.0 * up
    ro = V(0.0, 0.0, -0.02 + 0.005 * br)
    aims = feet(arm, 0.0, lf=(0.2, -0.03), rf=(-0.2, 0.05), turn=(12.0, -12.0))
    look = 4.0 * math.sin(w * 1.5) * (1 - up) + (-14.0 + 28.0 * smooth01((t - 0.5) / 0.22)) * up
    torso(aims, yaw, bend=0.06 - 0.04 * up, side=0.02 * math.sin(w), look=look, pitch=-0.42 * (1 - up) + 0.06 * up + 0.02 * br)
    aims.update(tablet_arm(arm, ro, yaw, lift=-0.18 * up, fwd=-0.04 * up, out=0.06 * up))
    q = rz(yaw)
    # the gauntlet: hanging at his side; brought up before his chest and turned while he checks it
    spin = math.sin((t - 0.5) / 0.3 * 2 * math.pi) * up
    hang_c, hang_f, hang_n = V(-0.43, 0.0, 0.84), V(-0.08, -0.05, -1.0), V(1.0, 0.12, 0.0)
    chk_c, chk_f, chk_n = V(-0.2, -0.36, 1.18), V(0.25, -0.55, 0.8), V(0.95, 0.2, -0.1)
    c = hang_c.lerp(chk_c, up)
    hf = mixd(hang_f, chk_f, up)
    hn = mixd(hang_n, chk_n, up)
    hn = Quaternion(hf, 0.7 * spin) @ hn
    aims.update(fist_at(arm, "R", body_pt(c, ro, yaw), q @ hf, q @ hn, q @ mixd(V(-0.4, 1.0, 0.0), V(-1.0, 0.3, -0.6), up)))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- combat: ready
C_YAW = -22.0
C_FEET = dict(lf=(0.25, -0.12), rf=(-0.24, 0.14), turn=(-2.0, -26.0))
C_FACE = V(-0.34, -0.3, 1.3)                 # the gauntlet cocked by his right shoulder, the plate to the robots (body space)
C_HF, C_HN = V(0.08, -1.0, 0.12), V(0.3, 0.0, -1.0)
C_POLE = V(-1.0, 0.6, -0.7)


def combat_state(t):
    bob = math.sin(2 * math.pi * t * 2)
    return V(0.0, 0.0, -0.1 + 0.012 * bob), C_YAW + 2.0 * math.sin(2 * math.pi * t), bob


def combat_pose(arm, t):
    ro, yaw, bob = combat_state(t)
    aims = feet(arm, C_YAW, **C_FEET)
    torso(aims, yaw, bend=0.14, chest=-4.0, look=0.0, pitch=0.04)
    q = rz(yaw)
    aims.update(tablet_arm(arm, ro, yaw, lift=-0.02 + 0.01 * bob, fwd=0.1, out=0.12, turn=0.35))
    aims.update(plate_at(arm, body_pt(C_FACE + V(0, 0, 0.01 * bob), ro, yaw), q @ C_HF, q @ C_HN, q @ C_POLE))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- attack: the ground pound
A_FEET = dict(lf=(0.25, -0.2), rf=(-0.25, 0.28), turn=(-2.0, -22.0))
UP_FACE = V(-0.36, 0.04, 1.86)                # heaved up over his right shoulder (body space, before the crouch)
HIT_FACE = V(-0.22, -0.42, 0.012)
DEEP = 0.42                                   # the lunge's depth             # on the ground before him (character space: the soles at z = 0)


def swing_dirs(phi):
    """The fist's fingers and palm at swing angle phi (degrees: 0 = knuckles up, 180 = knuckles down), in the plane of
    his front: the palm to the robots at the top, toward him at the bottom."""
    p = math.radians(phi)
    return V(0.0, -math.sin(p), math.cos(p)), V(0.0, -math.cos(p), -math.sin(p))


def attack_state(f):
    """(yaw, crouch, bend, plate face (armature space, or None: from the combat stance), phi or None, heel lift R)."""
    if f <= 4:
        k = ease(f / 4.0)
        return lerp(C_YAW, C_YAW - 4.0, k), lerp(0.1, 0.02, k), lerp(0.14, -0.06, k), k, "up"
    if f <= HIT:
        k = ((f - 4) / float(HIT - 4)) ** 1.5
        return lerp(C_YAW - 4.0, -8.0, k), lerp(0.02, DEEP, k), lerp(-0.06, 0.92, k), k, "slam"
    if f <= 11:
        k = (f - HIT) / 2.0
        return -8.0, DEEP + 0.012 * math.sin(math.pi * k), 0.92, k, "hold"
    k = ease((f - 11) / float(FR - 11))
    return lerp(-8.0, C_YAW, k), lerp(DEEP, 0.1, k), lerp(0.92, 0.14, k), k, "back"


def attack_pose(arm, f):
    yaw, crouch, bend, k, phase = attack_state(f)
    dk = max(0.0, min(1.0, (crouch - 0.1) / (DEEP - 0.1)))
    ro = V(0.0, 0.0, -crouch) + rz(yaw) @ V(0.0, -0.06 * dk, 0.0)
    aims = feet(arm, C_YAW * 0.6, **A_FEET)
    torso(aims, yaw, bend=bend, chest=-4.0 * (1 - dk), look=0.0, pitch=0.04 - 0.35 * max(bend - 0.3, 0.0))
    aims["clavicle.R"] = rz(yaw) @ V(-1.0, -0.25 * dk, 0.02 - 0.45 * dk)          # (the shoulder dropped into the blow)
    q = rz(yaw)
    tl = {"up": 0.06 * k, "slam": 0.06 * (1 - k) - 0.1 * k, "hold": -0.1, "back": -0.1 * (1 - k) + 0.02 * k}[phase]
    aims.update(tablet_arm(arm, ro, yaw, lift=tl, fwd=0.08, out=0.08 * (k if phase == "slam" else (1.0 if phase == "hold" else 0.0)), turn=0.25))
    c_face = body_pt(C_FACE, V(0, 0, -0.1), C_YAW)
    up_face = body_pt(UP_FACE, V(0, 0, -0.02), C_YAW - 4.0)
    hit_face = body_pt(HIT_FACE, V(0, 0, 0), -8.0)
    if phase == "up":
        face = c_face.lerp(up_face, k)
        hf, hn = mixd(q @ C_HF, q @ swing_dirs(0.0)[0], k), mixd(q @ C_HN, q @ swing_dirs(0.0)[1], k)
        pole = q @ mixd(C_POLE, V(-1.0, 0.4, 0.2), k)
    elif phase == "slam":
        face = bez_p(up_face, body_pt(V(-0.3, -0.5, 1.3), V(0, 0, -0.2), -8.0), hit_face, k)
        a, b = swing_dirs(lerp(0.0, 180.0, k))
        hf, hn = q @ a, q @ b
        pole = q @ V(-1.0, 0.4, 0.2)
    elif phase == "hold":
        face = hit_face
        a, b = swing_dirs(180.0)
        hf, hn = q @ a, q @ b
        pole = q @ V(-1.0, 0.4, 0.2)
    else:
        face = hit_face.lerp(c_face, k) + V(0, 0, 0.12 * math.sin(math.pi * k))
        a, b = swing_dirs(180.0)
        hf, hn = mixd(q @ a, q @ C_HF, k), mixd(q @ b, q @ C_HN, k)
        pole = q @ mixd(V(-1.0, 0.4, 0.2), C_POLE, k)
    aims.update(plate_at(arm, face, hf, hn, pole))
    return aims, ro, rz(yaw)


# ---------------------------------------------------------------------------------------------- ability: EMP grenade
class Rest:
    def __init__(self, arm):
        b = arm.data.bones
        self.m = {nm: b[nm].matrix_local.copy() for nm in ("hand.R", "forearm.L", "grenade")}
        self.h2g = self.m["hand.R"].inverted() @ self.m["grenade"]
        self.screen = self.m["forearm.L"].inverted() @ SCREEN_REST
        self.screen_n = self.m["forearm.L"].to_3x3().inverted() @ SCREEN_N_REST


def pouch_grab():
    """(the grenade's middle as he draws it, its axis) in body space: just above the pouch on the right of his belly."""
    c, R, half = cm.pouch_frame("grenades")
    u, n, s = vec(R[:, 1]), vec(R[:, 2]), vec(R[:, 0])
    return vec(c) + u * (half[1] + 0.07) + n * 0.03 + s * 0.02, (u + n * 0.3).normalized()


WIND_C, WIND_AX, WIND_F = V(-0.3, 0.14, 1.66), V(-0.2, 0.6, 0.8), V(0.0, 0.2, 1.0)        # cocked back beside his head
REL_C, REL_AX, REL_F = V(-0.2, -0.46, 1.66), V(-0.1, -0.4, 0.9), V(0.0, -1.0, 0.6)        # the lob: out before him, rising
FOL_C, FOL_AX, FOL_F = V(-0.12, -0.48, 1.08), V(0.2, -0.3, 0.9), V(0.1, -0.6, -0.8)


def ability_state(f):
    """(yaw, crouch, bend, phase, k)."""
    if f <= 8:
        return lerp(C_YAW, 0.0, ease(f / 8.0)), lerp(0.1, 0.03, ease(f / 8.0)), lerp(0.14, 0.05, ease(f / 8.0)), "square", ease(f / 8.0)
    if f <= GRAB:
        return 0.0, 0.03 + 0.03 * ease((f - 8) / 6.0), 0.05 + 0.12 * ease((f - 8) / 6.0), "reach", ease((f - 8) / 6.0)
    if f <= ARM:
        return 0.0, lerp(0.06, 0.02, ease((f - GRAB) / float(ARM - GRAB))), lerp(0.17, 0.08, ease((f - GRAB) / float(ARM - GRAB))), "bring", ease((f - GRAB) / float(ARM - GRAB))
    if f <= 31:
        return 0.0, 0.02, 0.08, "arm", (f - ARM) / 5.0
    if f <= 38:
        k = ease((f - 31) / 7.0)
        return lerp(0.0, -16.0, k), lerp(0.02, 0.08, k), lerp(0.08, -0.08, k), "wind", k
    if f <= RELEASE:
        k = ((f - 38) / float(RELEASE - 38)) ** 1.3
        return lerp(-16.0, 6.0, k), lerp(0.08, 0.05, k), lerp(-0.08, 0.2, k), "throw", k
    if f <= 50:
        k = ease((f - RELEASE) / 7.0)
        return lerp(6.0, 4.0, k), lerp(0.05, 0.1, k), lerp(0.2, 0.3, k), "follow", k
    k = ease((f - 50) / float(AB_FR - 50))
    return lerp(4.0, C_YAW, k), 0.1, lerp(0.3, 0.14, k), "back", k


def ability_pose(arm, f, R):
    """Returns (aims, ro, root rotation, scales); the hand that arms the grenade at the tablet needs the left forearm's
    pose, so this pose is solved twice (make_ability)."""
    yaw, crouch, bend, phase, k = ability_state(f)
    ro = V(0.0, 0.0, -crouch)
    q = rz(yaw)
    if phase == "square":
        fy = lerp(C_YAW, 0.0, k)
    elif phase == "back":
        fy = lerp(0.0, C_YAW, k)
    else:
        fy = 0.0
    fe = {kk: tuple(lerp(a, b, 0.5) for a, b in zip(C_FEET[kk], (0.22, -0.06) if kk == "lf" else ((-0.22, 0.1) if kk == "rf" else (8.0, -14.0)))) for kk in ("lf", "rf", "turn")}
    aims = feet(arm, fy, lift=(0.0, 0.03 * k if phase == "throw" else 0.0), **fe)
    look = {"square": 0.0, "reach": -8.0 * k, "bring": -8.0 + 8.0 * k, "arm": 0.0, "wind": 0.0, "throw": 0.0, "follow": 0.0, "back": 0.0}[phase]
    pitch = {"reach": -0.3 * k, "bring": -0.3 - 0.15 * k, "arm": -0.45, "wind": -0.45 * (1 - k) + 0.1 * k, "throw": 0.1, "follow": 0.05}.get(phase, 0.0)
    torso(aims, yaw, bend=bend, look=yaw + look, pitch=pitch)
    # the left forearm: up with the tablet; out of the way for the throw, pointing at the robots
    if phase in ("square", "reach", "bring", "arm"):
        aims.update(tablet_arm(arm, ro, yaw, lift=0.02, fwd=0.04))
    elif phase in ("wind", "throw"):
        kk = k if phase == "wind" else 1.0
        aims.update(tablet_arm(arm, ro, yaw, lift=0.02 + 0.12 * kk, fwd=0.04 + 0.12 * kk, out=0.1 * kk, turn=0.6 * kk))
    elif phase == "follow":
        aims.update(tablet_arm(arm, ro, yaw, lift=0.14 - 0.1 * k, fwd=0.16 - 0.06 * k, out=0.1, turn=0.6 - 0.35 * k))
    else:
        aims.update(tablet_arm(arm, ro, yaw, lift=0.04, fwd=0.1 - 0.02 * k, out=0.1 * (1 - k), turn=0.25))
    sc = {"grenade": 1.0 if GRAB <= f <= RELEASE else 0.0, "core": 1.0}
    if phase == "arm":
        sc["core"] = 1.0 + 0.45 * math.sin(math.pi * min(1.0, k * 1.2))
    return aims, ro, q, sc, phase, k


def right_hand(arm, f, phase, k, ro, yaw, screen=None, screen_n=None):
    q = rz(yaw)
    pole_lo = q @ V(-0.6, 1.0, -0.4)
    if phase == "square":
        return plate_at(arm, body_pt(C_FACE, ro, yaw), q @ C_HF, q @ C_HN, q @ C_POLE)
    gc, gax = pouch_grab()
    if phase == "reach":
        c0 = body_pt(C_FACE, ro, yaw)
        R0 = hand_rot("R", q @ C_HF, q @ C_HN)
        g0 = c0 - R0 @ PF_OFF + R0 @ GC_OFF                                # (where the grenade's middle would be at the hip)
        c = bez_p(g0, body_pt((g0 + gc) * 0.5 + V(-0.06, -0.08, 0.06), ro, yaw), body_pt(gc, ro, yaw), k)
        return grenade_at(arm, c, mixd(R0 @ G_AX, q @ gax, k), q @ V(0.3, -0.5, -0.8), pole_lo)
    if phase in ("bring", "arm"):
        tgt = screen + screen_n * (cm.GREN_H * 0.5 + 0.012) if screen is not None else body_pt(V(0.1, -0.3, 1.3), ro, yaw)
        ax = -screen_n if screen_n is not None else V(0, 0, -1)
        if phase == "bring":
            c = bez_p(body_pt(gc, ro, yaw), body_pt(V(-0.12, -0.42, 1.32), ro, yaw), tgt + V(0, 0, 0.03 * (1 - k)), k)
            axis = mixd(q @ gax, ax, k)
        else:
            c = tgt - screen_n * (0.004 * math.sin(math.pi * k))
            axis = ax
        return grenade_at(arm, c, axis, q @ V(0.6, -0.6, -0.2), pole_lo)
    if phase == "wind":
        a = screen + screen_n * (cm.GREN_H * 0.5 + 0.012) if screen is not None else body_pt(V(0.1, -0.3, 1.3), ro, yaw)
        c = bez_p(a, body_pt(V(-0.24, -0.2, 1.62), ro, yaw), body_pt(WIND_C, ro, yaw), k)
        axis = mixd(-screen_n if screen_n is not None else V(0, 0, -1), q @ WIND_AX, k)
        return grenade_at(arm, c, axis, q @ mixd(V(0.6, -0.6, -0.2), WIND_F, k), q @ V(-1.0, 0.3, -0.3))
    if phase == "throw":
        c = bez_p(body_pt(WIND_C, ro, yaw), body_pt(V(-0.3, -0.1, 1.86), ro, yaw), body_pt(REL_C, ro, yaw), k)
        return grenade_at(arm, c, q @ mixd(WIND_AX, REL_AX, k), q @ mixd(WIND_F, REL_F, k), q @ V(-1.0, 0.2, -0.4))
    if phase == "follow":
        c = body_pt(REL_C, ro, yaw).lerp(body_pt(FOL_C, ro, yaw), k)
        return grenade_at(arm, c, q @ mixd(REL_AX, FOL_AX, k), q @ mixd(REL_F, FOL_F, k), q @ V(-1.0, 0.2, -0.6))
    # back to the ready stance
    R1 = frame_map(G_AX, q @ FOL_AX, HAND["R"]["f"], q @ FOL_F)
    f1 = body_pt(FOL_C, ro, yaw) - R1 @ GC_OFF + R1 @ PF_OFF
    face = f1.lerp(body_pt(C_FACE, ro, yaw), k)
    return plate_at(arm, face, mixd(R1 @ HAND["R"]["f"], q @ C_HF, k), mixd(R1 @ HAND["R"]["n"], q @ C_HN, k),
                    q @ mixd(V(-1.0, 0.2, -0.6), C_POLE, k))


def make_ability(arm, frames=AB_FR):
    P = Poser(arm)
    R = Rest(arm)
    act = new_action(arm, "Ability")
    for f in range(frames + 1):
        aims, ro, rr, sc, phase, k = ability_pose(arm, f, R)
        yaw = ability_state(f)[0]
        screen = screen_n = None
        if phase in ("bring", "arm", "wind"):
            a0 = dict(aims)
            a0.update(right_hand(arm, f, "square", 0.0, ro, yaw))
            _, P0 = P.solve(a0, ro, rr)
            M = P0["forearm.L"]
            screen = M @ R.screen
            screen_n = (M.to_3x3() @ R.screen_n).normalized()
        aims.update(right_hand(arm, f, phase, k, ro, yaw, screen, screen_n))
        aims["grenade"] = lambda P_, base: ("world", P_["hand.R"] @ R.h2g)
        ch, _ = P.solve(aims, ro, rr, scales=sc)
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- cheer
def make_cheer(arm, frames=CH_FR):
    """Rank up: the gauntlet punched up at the sky and pumped twice, his left fist on his hip, a little hop."""
    P = Poser(arm)
    act = new_action(arm, "Cheer")
    for f in range(frames + 1):
        t = f / float(frames)
        up = smooth01(t / 0.18) * (1 - smooth01((t - 0.82) / 0.18))
        pump = max(0.0, math.sin((t - 0.2) / 0.6 * 2 * math.pi * 2)) * smooth01((t - 0.18) / 0.06) * (1 - smooth01((t - 0.76) / 0.06))
        hop = 0.03 * pump
        yaw = lerp(C_YAW, 0.0, up)
        ro = V(0.0, 0.0, -0.03 + hop - 0.06 * (1 - up))
        aims = feet(arm, 0.0, lf=(0.2, -0.03), rf=(-0.2, 0.05), turn=(12.0, -12.0), lift=(hop * 0.5, hop * 0.5))
        torso(aims, yaw, bend=-0.08 * up + 0.12 * (1 - up), side=0.06 * up, look=6.0 * math.sin(f * 0.3) * up, pitch=0.04 + 0.42 * up)
        q = rz(yaw)
        top = V(-0.24, -0.04, 2.18 + 0.07 * pump)
        face = body_pt(C_FACE, ro, yaw).lerp(body_pt(top, ro, yaw), smooth01(up * 1.3))
        hf = mixd(q @ C_HF, V(0.05, 0.0, 1.0), smooth01(up * 1.3))
        hn = mixd(q @ C_HN, V(1.0, -0.1, 0.0), smooth01(up * 1.3))
        aims.update(plate_at(arm, face, hf, hn, q @ mixd(C_POLE, V(-1.0, 0.0, -0.2), up)))
        w0, p0, f0, n0 = tablet_params(ro, yaw, lift=0.02, fwd=0.08, turn=0.25)
        s = smooth01(up * 1.4)
        w1, p1, f1, n1 = body_pt(V(0.34, 0.0, 1.0), ro, yaw), q @ V(1.0, 0.3, 0.1), q @ V(-0.55, 0.15, -0.82), q @ V(-0.75, -0.1, 0.5)
        aims.update(arm_aims(arm, "L", w0.lerp(w1, s), mixd(p0, p1, s), mixd(f0, f1, s), mixd(n0, n1, s)))
        ch, _ = P.solve(aims, ro, rz(yaw), scales={"grenade": 0.0})
        P.key(ch, f)
    finish_action(arm, act, frames, False)
    return act


# ---------------------------------------------------------------------------------------------- loops
def _loop(arm, name, frames, fn, cyclic=True, scales=None):
    P = Poser(arm)
    act = new_action(arm, name)
    for f in range(frames + 1):
        aims, ro, rr = fn(arm, (f % frames) / frames if cyclic else f)
        ch, _ = P.solve(aims, ro, rr, scales=scales or {"grenade": 0.0})
        P.key(ch, f)
    finish_action(arm, act, frames, cyclic)
    return act


def make_idle(arm):
    return _loop(arm, "Idle", I_FR, idle_pose)


def make_combat(arm):
    return _loop(arm, "Combat", C_FR, combat_pose)


def make_attack(arm):
    return _loop(arm, "Attack", FR, attack_pose, cyclic=False)


def make_all(arm):
    return [make_idle(arm), make_combat(arm), make_attack(arm), make_ability(arm), make_cheer(arm)]
