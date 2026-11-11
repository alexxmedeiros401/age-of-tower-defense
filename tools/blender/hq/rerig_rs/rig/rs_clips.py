"""Rock Slinger re-rig: the clips. Idle (90 frames, loop), Whirl (24, loop), Throw (24, the stone leaves on RELEASE).

All at 24 fps (game.gd CLIP_FPS). The game starts Throw the moment the sim fires and spawns its rock then, so Throw
opens cocked and lets go two frames in; it ends cocked again, so shot after shot chains, and Whirl starts from that pose.
"""
import numpy as np
import rs_core, rs_anim
from rs_core import J, unit
from rs_anim import Clip

V = lambda *a: np.array(a, float)
RELEASE = 2          # Throw: the stone leaves the pouch on this frame
RELOAD = 11          # Throw: a new stone is in the pouch from this frame

# ---- combat stance (left foot toward the target, right foot back and turned out) -------------------------------------
FOOT_L = dict(ball=V(-0.055, -0.08, 0.0), yaw=8.0)
FOOT_R = dict(ball=V(-0.06, 0.18, 0.0), yaw=-35.0)

# ---- the whirl: a tilted circle beside his head, rising over it and dipping on the outside ---------------------------
GRIP_C = V(-0.50, 0.24, 1.80)            # where the fist holds the cords while whirling (armature space)
TILT = 38.0
_rise = unit(V(0.0, 0.03, 0.0) - V(GRIP_C[0], GRIP_C[1], 0.0))                       # toward his head
E2 = V(_rise[0] * np.cos(np.radians(TILT)), _rise[1] * np.cos(np.radians(TILT)), np.sin(np.radians(TILT)))
E1 = V(_rise[1], -_rise[0], 0.0)
WHIRL_N = np.cross(E1, E2)
HAND_LEN = float(np.linalg.norm(J['hand_end.R'] - J['wrist.R']))


def whirl_dir(alpha_deg):
    """Unit direction grip -> pouch on the whirl circle; alpha grows with time (anticlockwise seen from above):
    0 front, 90 over his head (high), 180 back, 270 outside (low)."""
    a = np.radians(alpha_deg)
    return np.cos(a) * E1 + np.sin(a) * E2


def whirl_hand(alpha_deg, stir=0.45, lead=25.0, r=0.028):
    """Fist aim (it stirs after the pouch) and wrist position for a pouch angle."""
    d = whirl_dir(alpha_deg + lead)
    aim = unit(V(0.0, 0.0, 1.0) + d * stir)
    grip = GRIP_C + whirl_dir(alpha_deg + lead) * r
    return grip - aim * HAND_LEN, aim


def stance(c, period_keys=None):
    c.key('ball.L', {0: FOOT_L['ball']}); c.key('foot_yaw.L', {0: FOOT_L['yaw']})
    c.key('ball.R', {0: FOOT_R['ball']}); c.key('foot_yaw.R', {0: FOOT_R['yaw']})


ALPHA0 = 170.0       # the pouch's angle in the cocked pose (Throw 0 / 24, Whirl 0)
REV = 12.0           # Whirl: frames per turn


def whirl():
    c = Clip('Whirl', 24, True)
    stance(c)
    w = lambda f: 2 * np.pi * f / 24.0
    c.key('pelvis', {f: V(-0.02 + 0.006 * np.sin(2 * w(f)), 0.035 + 0.006 * np.cos(2 * w(f)), -0.065 + 0.008 * np.sin(w(f))) for f in range(0, 24, 2)})
    c.key('pelvis_ypr', {f: V(-14 + 1.5 * np.sin(2 * w(f)), -2, 0) for f in range(0, 24, 2)})
    c.key('chest_ypr', {f: V(-30 + 2.5 * np.sin(2 * w(f) + 0.6), -5 + 1.0 * np.sin(w(f)), -3) for f in range(0, 24, 2)})
    c.key('head_ypr', {0: V(-4, 1, 0), 12: V(-2, 0, 0)})
    c.key('wrist.L', {0: V(0.30, -0.50, 1.33), 6: V(0.31, -0.51, 1.345), 12: V(0.30, -0.50, 1.33), 18: V(0.29, -0.50, 1.32)})
    c.key('pole.L', {0: V(0.7, 0.2, -0.6)})
    c.key('pole.R', {0: V(-0.8, 0.5, -0.45)})
    alpha = lambda f: ALPHA0 + 360.0 * f / REV

    def arm(f, ctl):
        wr, aim = whirl_hand(alpha(f))
        ctl['arm.R']['wrist'] = wr; ctl['arm.R']['aim'] = aim
    c.extra.append(arm)
    c.sling = dict(drive=lambda f: (1.0, whirl_dir(alpha(f))), loops=1)
    return c



def _slerp_dir(a, b, k):
    a, b = unit(a), unit(b)
    w = np.arccos(np.clip(a @ b, -1, 1))
    if w < 1e-6: return a
    return (np.sin((1 - k) * w) * a + np.sin(k * w) * b) / np.sin(w)


def _ease(x):
    x = float(np.clip(x, 0, 1)); return x * x * (3 - 2 * x)


def throw():
    """24 frames. 0 cocked -> RELEASE (2): the stone leaves -> follow-through across the body -> the hand comes back to the
    hip bag and the pouch dips at it (a new stone from RELOAD) -> swung up in front and whirled a turn and a third round
    his head, faster and faster -> 24 cocked again (= frame 0), so shot after shot chains."""
    c = Clip('Throw', 24, True)                     # cyclic in pose: frame 24 is frame 0
    T = 24
    # ---- feet: planted; the back heel comes up as the hips drive through, and settles again
    c.key('ball.L', {0: FOOT_L['ball']}); c.key('foot_yaw.L', {0: FOOT_L['yaw']})
    c.key('ball.R', {0: FOOT_R['ball'], 4: FOOT_R['ball'] + V(0.0, -0.01, 0.0), 7: FOOT_R['ball'] + V(0.0, -0.01, 0.0), 11: FOOT_R['ball']})
    c.key('foot_yaw.R', {0: FOOT_R['yaw'], 4: -20.0, 7: -20.0, 11: FOOT_R['yaw']})
    c.key('foot_lift.R', {0: 0.0, 2: 10.0, 4: 32.0, 6: 30.0, 9: 8.0, 11: 0.0}, flat=(0, 11))
    # ---- hips: back over the right leg when cocked, driven forward and round through the release, then home
    # (the cocked pose is held flat: the trunk sinks a touch deeper into the coil over the last frames, then lets go)
    c.key('pelvis', {0: V(-0.035, 0.060, -0.075), 2: V(-0.005, -0.005, -0.060), 4: V(0.028, -0.052, -0.085), 6: V(0.030, -0.050, -0.095),
                     9: V(0.000, -0.012, -0.075), 13: V(-0.020, 0.030, -0.060), 18: V(-0.030, 0.050, -0.066), 22: V(-0.036, 0.062, -0.078)}, flat=(0, 6))
    c.key('pelvis_ypr', {0: V(-20, -3, 0), 2: V(-2, 2, 0), 4: V(12, 6, 0), 6: V(13, 7, 0), 9: V(2, 4, 0), 13: V(-10, 0, 0), 18: V(-18, -2, 0),
                         22: V(-21, -3, 0)}, flat=(0, 6))
    c.key('chest_ypr', {0: V(-42, -9, -5), 1: V(-27, -3, -3), 2: V(-4, 6, 0), 3: V(14, 14, 2), 4: V(27, 20, 3), 6: V(30, 21, 4),
                        8: V(14, 13, 2), 10: V(-4, 7, 0), 12: V(-16, 2, -2), 15: V(-28, -3, -3), 19: V(-38, -7, -4), 22: V(-44, -10, -5)}, flat=(0, 6))
    c.key('head_ypr', {0: V(-8, 0, 0), 2: V(-2, 3, 0), 4: V(5, 9, 0), 6: V(6, 9, 0), 9: V(-2, 6, 0), 13: V(-5, 1, 0), 18: V(-7, 0, 0)}, flat=(0, 6))

    def chest_pt(f, pt):
        P, _ = rs_core.solve(c.controls(float(f)))
        return P['chest'](np.asarray(pt, float))

    def chest_dir(f, d):
        P, _ = rs_core.solve(c.controls(float(f)))
        return P['chest'].R @ np.asarray(d, float)
    # ---- left arm: aims at the target, pulls in to the ribs as he throws, swings back behind the hip, comes out to aim
    AIM_L = V(0.30, -0.50, 1.33)
    c.key('wrist.L', {0: AIM_L, 2: chest_pt(2, (0.52, -0.30, 1.16)), 4: chest_pt(4, (0.64, -0.06, 1.02)), 6: chest_pt(6, (0.66, 0.10, 0.99)),
                      8: chest_pt(8, (0.60, -0.12, 1.05)), 10: chest_pt(10, (0.46, -0.36, 1.18)), 13: V(0.31, -0.49, 1.31), 16: AIM_L}, flat=(0, 16))
    c.key('pole.L', {0: V(0.7, 0.2, -0.6), 4: chest_dir(4, (0.6, 0.8, -0.2)), 7: chest_dir(7, (0.6, 0.8, -0.2)), 10: V(0.7, 0.3, -0.5), 13: V(0.7, 0.2, -0.6)})
    # ---- the pouch's angle round the whirl circle: on the circle from frame 14, a turn and a third, then the whip
    al = rs_anim.Track({13.5: -10.0, 14: 15.0, 16: 100.0, 18: 195.0, 20: 295.0, 22: 405.0, 24: ALPHA0 + 360.0, 25: 590.0, 26: 645.0}, None)
    ON = 14.0                                        # from here the fist is at its whirl place
    # ---- right arm: the sling hand
    W0, A0 = whirl_hand(ALPHA0)
    HIP = V(-0.47, -0.35, 1.21)                      # the fist over the hip bag: the pouch hangs just in front of it
    # (the whip stays close to him: the base's tusks stand 0.95 m from his axis and the base does not turn with him)
    # (the follow-through passes in front of the beard's tip and ends clear of his belly: he is leaning well forward by then)
    c.key('wrist.R', {0: W0, 1: V(-0.53, 0.03, 1.74), 2: V(-0.46, -0.34, 1.70), 3: V(-0.38, -0.49, 1.49), 4: V(-0.26, -0.57, 1.24), 5: V(-0.12, -0.62, 1.03),
                      6: V(-0.03, -0.64, 0.94), 8: V(-0.22, -0.53, 1.00), 10: HIP, 11: HIP + V(-0.02, 0.0, 0.03), 12.5: V(-0.56, -0.18, 1.46), ON: whirl_hand(al(ON))[0]},
          flat=(0,))
    c.key('pole.R', {0: V(-0.8, 0.5, -0.45), 2: V(-0.9, 0.4, -0.2), 4: V(-1.0, 0.0, 0.1), 6: V(-1.0, -0.25, 0.15), 8: V(-1.0, 0.0, 0.0), 10: V(-0.8, 0.6, -0.1),
                     13: V(-0.8, 0.5, -0.45)})
    c.key('stone', {0: 1.0, RELEASE: 0.0, RELOAD: 1.0, T: 1.0}, mode='step', periodic=False)
    D_REL = unit(V(-0.20, -0.50, 0.84))              # the cords' direction as the stone leaves: up, forward, a little to his right
    D_OUT = whirl_dir(252.0)                         # the whip's pass on his outside: low, under the tusks' tips
    D_DOWN = V(0.0, 0.0, -1.0)

    def pouch_dir(f):
        """Unit direction grip -> pouch while the stone is in it (frames RELOAD .. 24 and 0 .. RELEASE)."""
        f = f % T
        if f <= 1.0:
            return _slerp_dir(whirl_dir(ALPHA0), D_OUT, f)
        if f <= RELEASE:
            return _slerp_dir(D_OUT, D_REL, (f - 1.0) / (RELEASE - 1.0))
        if f < ON:
            return _slerp_dir(D_DOWN, whirl_dir(al(ON)), _ease((f - RELOAD) / (ON - RELOAD)))
        return whirl_dir(al(f))

    def drive(f):
        f = f % T
        if f <= RELEASE: return 1.0, pouch_dir(f)
        if f < 8.0: return 0.0, None
        if f < RELOAD: return _ease((f - 8.0) / (RELOAD - 8.0)) ** 2, D_DOWN      # gathered back to hang by the bag
        return 1.0, pouch_dir(f)

    def arm(f, ctl):
        f = f % T
        a = ctl['arm.R']
        down = V(0.0, -0.25, -1.0)
        if f >= ON:
            wr, aim = whirl_hand(al(f)); a['wrist'] = wr; a['aim'] = aim
        elif f >= RELOAD:
            a['aim'] = _slerp_dir(down, whirl_hand(al(ON))[1], _ease((f - RELOAD) / (ON - RELOAD)))
        elif f >= 8.0:
            fore = unit(a['wrist'] - V(-0.35, -0.10, 1.25))
            a['aim'] = _slerp_dir(fore, down, _ease((f - 8.0) / (RELOAD - 8.0)))
        elif f <= RELEASE:
            a['aim'] = _slerp_dir(A0, unit(V(-0.25, -0.75, 0.6)), _ease(f / RELEASE))
        else:
            a['aim'] = None
    c.extra.append(arm)
    c.sling = dict(drive=drive, loops=3, drag=4.5)
    return c


def idle():
    """90 frames. Relaxed: weight shifting from foot to foot, breathing, the head scanning the valley, the loaded sling
    swaying from his fist; once a loop he gives the sling a little bounce."""
    T = 90
    c = Clip('Idle', T, True)
    w = lambda f: 2 * np.pi * f / T
    fr = range(0, T, 6)
    c.key('ball.L', {0: V(-0.05, 0.0, 0.0)}); c.key('foot_yaw.L', {0: 7.0})
    c.key('ball.R', {0: V(0.045, 0.0, 0.0)}); c.key('foot_yaw.R', {0: -7.0})
    c.key('pelvis', {f: V(0.014 * np.sin(w(f)), 0.004 * np.sin(w(f) + 1.0), -0.022 + 0.005 * np.sin(2 * w(f))) for f in fr})
    c.key('pelvis_ypr', {f: V(1.5 * np.sin(w(f) - 0.3), 0.6 * np.sin(2 * w(f)), -1.6 * np.sin(w(f))) for f in fr})
    c.key('chest_ypr', {f: V(3.0 * np.sin(w(f) - 0.6), 1.0 - 1.6 * np.sin(2 * w(f) + 0.4), 1.2 * np.sin(w(f))) for f in fr})
    c.key('head_ypr', {0: V(0, 1, 0), 10: V(14, 2, 0), 20: V(24, 0, 1), 34: V(22, 1, 1), 46: V(-6, 3, 0), 56: V(-22, 1, -1), 70: V(-20, 2, -1), 82: V(-4, 2, 0)},
          flat=(20, 34, 56, 70))
    sway = lambda f, s: V(s * 0.006 * np.sin(w(f) + 0.8), 0.010 * np.sin(w(f) - 0.5), -0.020 + 0.004 * np.sin(2 * w(f) + 0.5))
    c.key('wrist.L', {f: J['wrist.L'] + V(-0.02, 0.0, 0.0) + sway(f, 1.0) for f in fr})
    # the sling hand: at his side; a small lift and drop (frames 52..66) sets the pouch swinging
    bounce = rs_anim.Track({0: 0.0, 50: 0.0, 56: 1.0, 61: -0.25, 67: 0.0, 90: 0.0}, None, flat=(0, 50, 67, 90))
    c.key('wrist.R', {f: J['wrist.R'] + V(0.02, 0.0, 0.0) + sway(f, -1.0) + V(0.0, -0.02, 0.045) * bounce(f) for f in range(0, T, 3)})
    c.sling = dict(drive=lambda f: (0.0, None), loops=5, drag=2.2)
    return c


CLIPS = {'Idle': idle, 'Whirl': whirl, 'Throw': throw}
